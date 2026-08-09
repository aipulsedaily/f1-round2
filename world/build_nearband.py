#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_nearband.py — THE BAND `wood` EVACUATES.  Round 2, CIRCUIT VITRINE.

WHAT IS WRONG, MEASURED (R2-1156, and this module does not re-litigate it)
--------------------------------------------------------------------------
`build_terrain.habitat()` computes the woodland probability as

    wood  = smoothstep(-0.22, 0.34, fbm(x/165, y/165, 4, seed=401))
    wood *= smoothstep(52.0, 150.0, D)                       # <-- THE EMPTIER
    wood *= (1 - 0.88*plateau) * (1 - 0.94*built) * (1 - 0.80*ez)

`D` is distance to the nearest centreline, so woodland probability is EXACTLY ZERO
for D <= 52 m and 0.5 at D = 101 m.  `wood` then gates FIVE consumers — woodland
(`pw = h["wood"]*0.44*q`), hedgerows, shrubs (`edge`/`inner`), saplings and ferns.
Every woody thing in the world is switched off within 52 m of the racing line.

Weighted by exact screen-area-time over film17's 2 978 frames:

    18.0 %  of ground screen-area-time has woodland probability EXACTLY ZERO
    35.7 %  is partially gated (52 < D < 150, mean gate 0.52)
    46.3 %  is ungated (D >= 150)
    44.9 %  of ground screen-area-time is > 10 m from ANY woody instance
    ground at 25-50 m depth is a median 78.9 m from the nearest tree;
    ground beyond 250 m is 9.6 m from one.  Inverse correlation, 8.2x.

The client: "anything 5 feet away from the main road and buildings have blank grass
no detail nothing" / "i want to fill the WHOLE map with trees and detail no blank
green spots period".

WHAT THIS MODULE IS
-------------------
A NEW TIER that fills exactly the complement.  It does not edit `build_terrain.py`
and it does not change one number in it: it imports it, reads the same fields, and
plants where the gate has switched the old tiers off.

    nb_density = (1 - smoothstep(52, 150, D))    # the EXACT complement of the gate
               * smoothstep(2.0, 14.0, f)        # f = metres OUTBOARD OF THE RIM
               * habitat modulation

Because the D term is the exact complement of the gate, near-band + woodland is
roughly constant in D BY CONSTRUCTION.  That is the no-cliff requirement, and this
module VERIFIES it rather than asserting it: `density_vs_D()` walks every woody
instance actually in the scene, bins it by measured D in 10 m bins across 0-300 m
against Monte-Carlo annulus areas, and prints the table.  R2-1661 caught tiers that
would have laid visible density rings at 200 m and 520 m.  A ring at 52 m would be
the same defect at the exact radius the client already complained about.

THE HEIGHT CEILING RAMPS WITH `f`, AND THAT IS WHAT KEEPS IT HONEST
-------------------------------------------------------------------
This is a race circuit.  There is a debris fence and a runoff programme outboard of
every metre of racing surface, and a tree in either of them is a worse defect than
bare grass.  So the placeable unit's height is bounded by a monotone continuous ramp
in `f` (metres outboard of the corridor rim, NOT distance from the centreline — the
rim is 12.1 m out at s = 0 and 87.9 m out at T10, and one number cannot serve both):

    f  2-8 m    tussock, weed stands, low scrub only          < 0.62 m
    f  8-20 m   gorse / bramble / juniper / broom scrub        0.62 - 2.50 m
    f 20-52 m   hazel scrub, saplings, and only the SHORT
                tree species — hawthorn (h 2.8-6.2), rowan
                (7.0-13.0), birch (8.0-16.5), weighted toward
                hawthorn BY THE RAMP ITSELF                    2.50 - 16.5 m
    f > 52 m    ceiling saturates; the woodland tier's own D gate is ramping up

`height_ceiling(f)` is that ramp, it is monotone and continuous, and NOTHING is
emitted whose declared height exceeds it.  `selftest` proves the check REJECTS a
scrub taller than the ceiling and REJECTS an oak offered at f = 25 m.

WHY THE PLACEABLE UNIT IS A CLUMP AND NOT A SHRUB
--------------------------------------------------
At D 26-52 m the ground is typically seen at 100-250 m depth, so 1 px = 20-50 mm and
individual leaves are sub-pixel.  This is the same argument that made R2-1661's sward
fix a "drift" and not a "clump", and it drops the instance count with the SQUARE of
the pitch: the verge band is 0.39 km2, and at a single-shrub pitch that is nine
figures of instance.  So the unit here is a SCRUB CLUMP of 1.5-4.5 m, COMPOSED from
the shipping generators (`gen_shrub`, `gen_weed`, `gen_grass`, `gen_tree("sapling")`,
`gen_stone`) — no new plant geometry is authored anywhere in this file.

THE MECHANISM IS SHADOW, NOT GEOMETRY
--------------------------------------
The sun is at 12.47 deg (`C.SUN_ELEV_DEG`).  A 1.0 m scrub lays 4.52 m of shadow.  In
R2-1661 35 % plan cover read as 72 % screen cover for exactly this reason.
`shadow_cover()` measures it here — plan cover and plan+shadow cover, rasterised at
0.25 m over a real patch of the built band — so the claim is a number and not a hope.

RUN IT
------
    B=/opt/blender-5.2.0-linux-x64/blender
    $B -b --factory-startup -noaudio -P build_nearband.py -- --selftest
    $B -b --factory-startup -noaudio -P build_nearband.py -- --full \\
        --save /home/zany/f1-round2/world/nearband.blend --stats nb.json

`--full` runs `build_terrain.build()` first so the no-cliff evidence is measured
against the REAL woodland tier and not against a model of it.  `--terrain-only`
builds the ground + library and this tier alone (fast, for iteration).

BLENDER EXITS 0 ON AN UNCAUGHT EXCEPTION.  Judge only on the printed
`>> STAGE RESULT:` lines.  Every one of them carries ok=1 or ok=0.
"""

import bpy, math, json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_terrain as T            # IMPORTED, NEVER EDITED
import world_contract as C           # the datum, the corridor, the sun
import itemkit as K                  # relief_amplitude_for / detail_for -- the laws


# ==================================================================================
# 0.  CONFIGURATION
# ==================================================================================

SUB = "NearBand"                     # sub-collection under WORLD_TERRAIN
NAME = "nb_"                         # every datablock is VEG_nb_*, so T.purge() eats it
SEED = 20260807

QUAL = float(os.environ.get("NEARBAND_QUALITY", os.environ.get("TERRAIN_QUALITY",
                                                               "1.0")))

# --- THE GATE THIS TIER COMPLEMENTS ------------------------------------------------
# These are `build_terrain.habitat()`'s own numbers.  They are re-stated here because
# they are literals inside that function and there is nothing to import; `selftest`
# therefore MEASURES them off the live `habitat()` and fails if they have moved.  A
# constant copied without an instrument watching it is how two modules drift.
WOOD_GATE_D = (52.0, 150.0)
WOOD_GATE_TOL_M = 3.0                # how far the measured edge may sit from 52.0

# --- THE OUTBOARD RAMP -------------------------------------------------------------
# `f` is metres outboard of the corridor rim.  Nothing at all inside f = 2.0 (the
# drainage swale invert is at f = 9.0 and its shoulder starts at 1.2; 2.0 m keeps the
# lowest tier off the rim weld), full weight by f = 14.0.
NB_F0, NB_F1 = 2.0, 14.0

# --- THE HEIGHT CEILING ------------------------------------------------------------
# (f metres, ceiling metres).  Monotone, continuous, piecewise linear, saturating.
# The knots are the tier boundaries in the brief; the top knot is silver birch's own
# maximum (SPECIES["birch"]["h"][1] = 16.5), so the ramp hands over to the woodland
# tier at the tallest thing the woodland tier's SHORT species can be.
F_RAMP = ((0.0, 0.00), (2.0, 0.30), (8.0, 0.62), (20.0, 2.50), (52.0, 16.5))

# --- KEEP-OUTS, all from the contract ----------------------------------------------
NB_PAVE_STANDOFF_M = 1.2      # low tiers: metres outside C.platform_field
NB_PAVE_STANDOFF_TREE_M = 4.0  # a small tree's crown may not overhang the concrete
NB_TRANSIT_CLEAR_M = (C.ACCESS_HALF_W + C.TRANSIT_DRIVE_CLEAR_M + 2.0)   # 8.6 m
NB_FORECOURT_CLEAR_M = 3.0    # outside FORECOURT_WORLD's declared box

# --- THE TIERS ---------------------------------------------------------------------
# `pitch` is the placement pitch in metres; the clump is DRAWN over 1.45 x pitch (the
# anti-tiling law, build_terrain.gen_sward) so neighbours overlap 2.1x in area and no
# seam survives.  `dens` is the peak probability a candidate at full nb weight is
# taken -- the ground density is dens / pitch^2 clumps per m2.
#
# `nshrub`/`nweed`/`ngrass`/`nstone` are the COMPOSITION of one clump: how many of the
# shipping generators' outputs are merged into it.  `hnom` is the clump's nominal
# tallest element; `gn_kind` normalises every library mesh by it, so the target height
# this module passes IS the tallest plant in the placed clump, exactly, which is what
# makes the ceiling test exact.
#
# `shrub_lod` IS A TRIANGLE DIAL AND IT IS THE BIG ONE.  `gen_shrub` at LOD 0 dresses
# 420-760 leaves x2.6; at LOD 1 it is 190-320 x2.6.  Measured on the first standalone
# build, an N2 clump built from LOD-0 shrubs came out at 40 076 triangles -- a hero
# tree's worth of geometry for a 2.9 m gorse bush seen at 100-250 m, where its leaves
# are sub-pixel.  LOD 1 everywhere in N1/N2, and a 25 % minority of LOD 0 in N3 (which
# is the closest TALL thing to the lens, 20-52 m outboard of a rim the camera flies
# along).
NB_TIERS = (
    dict(tag="N1", label="verge tussock and weed stand",
         fw=(None, 5.0, 9.0),         # weight: 1 - smoothstep(5, 9, f)
         pitch=1.45, dens=1.00, hnom=0.62, nlib=44,
         shrubs=(("bramble", 1.0),), nshrub=(0, 1), shrub_lod=1, lod0_p=0.0,
         weeds=("plantain", "yarrow", "dock", "nettle"), nweed=(1, 4),
         wfrac=(0.40, 1.00),
         grass=("tussock", "meadow", "dry"), ngrass=(3, 6), grass_lod=1,
         gfrac=(0.34, 0.88), gblades=(8, 14), nstone=(0, 1), sapling=0.0),
    dict(tag="N2", label="gorse / bramble / juniper / broom scrub",
         # THE N1/N2 CROSSFADE WAS MOVED INBOARD, 6-11 m -> 5-9 m, AND IT IS THE ONLY
         # THING THAT MOVES THE 40-50 m COVER BIN.  Measured on the first full build:
         # woody plan cover ran 0.001 / 0.003 / 0.073 / 0.198 across D 20-30 / 30-40 /
         # 40-50 / 50-60 m against a far field of 0.170, i.e. flat and correct from
         # 50 m out but an order down inside it.  The cause is not density: cover for
         # a tier whose clump is drawn at 1.45 x its own pitch is `0.554 * dens`
         # INDEPENDENT OF PITCH, so the only levers are `dens` (already near 1) and
         # WHICH TIER OWNS THE GROUND -- and N1's clump has a 0.61 m plan radius
         # against N2's 1.22, a 4x difference in footprint.  Handing 5-9 m of `f` to
         # N2 puts the bigger footprint where the ground is.  It does NOT put taller
         # plants there: `height_ceiling(f)` still clips an N2 clump at f = 7 m to
         # 0.55 m, so what stands there is a gorse sheared to knee height, which is
         # what stands beside a debris fence.
         fw=(5.0, 9.0, 17.0, 24.0),   # smoothstep(5,9,f) * (1 - smoothstep(17,24,f))
         pitch=2.90, dens=0.98, hnom=1.75, nlib=44,
         # THE MIX IS ALSO A TRIANGLE DIAL.  Measured at LOD 1: bramble 3 213 tris,
         # hazel 4 824, juniper 12 492, gorse 13 435, broom 14 082 -- a 4.4x spread,
         # because `brushfine`/`scale` leaf templates are many triangles each.  The
         # weights below keep gorse as the signature verge scrub while letting the
         # cheap species carry the bulk, which is what a real verge looks like anyway.
         shrubs=(("bramble", 1.3), ("gorse", 1.0), ("juniper", 0.5), ("broom", 0.4)),
         nshrub=(1, 2), shrub_lod=None, lod0_p=0.0,
         weeds=("dock", "thistle", "ragwort", "nettle"), nweed=(1, 3),
         wfrac=(0.26, 0.62),
         grass=("tussock", "meadow"), ngrass=(2, 4), grass_lod=1,
         gfrac=(0.16, 0.40), gblades=(6, 11), nstone=(0, 2), sapling=0.10),
    dict(tag="N3", label="hazel scrub thicket",
         fw=(17.0, 24.0, None, None),  # smoothstep(17, 24, f)
         pitch=4.10, dens=0.70, hnom=3.40, nlib=44,
         shrubs=(("hazel", 1.3), ("bramble", 0.9), ("gorse", 0.4)),
         nshrub=(1, 2), shrub_lod=None, lod0_p=0.25,
         weeds=("dock", "nettle", "thistle"), nweed=(1, 3),
         wfrac=(0.13, 0.34),
         grass=("tussock", "meadow"), ngrass=(1, 3), grass_lod=1,
         gfrac=(0.08, 0.21), gblades=(5, 9), nstone=(0, 2), sapling=0.55),
)

# --- THE SHORT-TREE SUB-TIER -------------------------------------------------------
# Only these three, and the ramp does the weighting for free: a target height is drawn
# uniformly in [2.6, ceiling(f)], and the species whose h-range brackets it is taken.
# hawthorn is 2.8-6.2, so it is the ONLY candidate until ceiling(f) passes 7.0 m,
# which happens at f = 30.3 m.  Nothing is hand-weighted toward hawthorn; the physics
# of the ramp weights it.
NB_TREES = ("hawthorn", "rowan", "birch")
NB_TREE_PITCH = 11.5          # metres; short trees are an EMERGENT layer over scrub
NB_TREE_DENS = 0.55
NB_TREE_HMIN = 2.6
NB_TREE_LIB_TARGET = 22       # unique base meshes wanted per (species, LOD)
NB_TREE_LIB_EXTRA_LODS = (0, 1, 2)   # build_terrain ships 8/12/16 -- all three are
#                             short of the item gate's `min(40, sqrt(realized))` once
#                             the near band adds its own instances to the count.

# --- AMENITY (the second half of the defect) ---------------------------------------
# `(1 - 0.94*built)` suppresses woody cover by 94 % near the paddock and the showroom,
# which is where beats 1-4 live and exactly what the client meant by "...and
# buildings".  This tier does not fight that term; it plants a DIFFERENT thing there,
# driven FROM the declared paving rather than suppressed by a hand-drawn district.
AM_EDGE_BAND = (1.2, 7.5)     # metres outside C.platform_field where amenity sits
AM_HEDGE_PITCH = 1.85         # hedge segments are drawn 2.0 m long and placed at 1.85
AM_HEDGE_LEN = 2.00
AM_HEDGE_H = (0.85, 1.45)
AM_HEDGE_W = (0.55, 0.85)
AM_HEDGE_LIB = 32
AM_TREE_PITCH = 12.0
AM_TREE_H = (3.2, 6.0)
AM_PLANTER_PITCH = 17.0
AM_PLANTER_LIB = 18

# --- MEASUREMENT -------------------------------------------------------------------
DENS_BINS = np.arange(0.0, 310.0, 10.0)
DENS_MC = 900000              # Monte-Carlo samples for the annulus areas

LOG_T0 = time.time()


def log(msg):
    print("[nearband %7.1fs] %s" % (time.time() - LOG_T0, msg), flush=True)


_STAGES = []


def stage(name, ok, **kw):
    """THE ONLY THING A GATE MAY READ.  Blender exits 0 on an uncaught exception."""
    _STAGES.append((name, bool(ok), kw))
    print(">> STAGE RESULT: %s ok=%d %s"
          % (name, 1 if ok else 0, json.dumps(kw, sort_keys=True, default=float)),
          flush=True)
    return bool(ok)


# ==================================================================================
# 1.  THE LAW: the complement, the outboard ramp, the ceiling
# ==================================================================================

def wood_gate(D):
    """`build_terrain.habitat()`'s own D gate.  Verified against it in `selftest`."""
    return T.smoothstep(WOOD_GATE_D[0], WOOD_GATE_D[1], np.asarray(D, float))


def nb_gate(D):
    """THE EXACT COMPLEMENT.  1 - wood_gate(D).  This is the whole no-cliff argument:
    a smoothstep plus its own complement is identically 1, so whatever shape the
    handover has, the two tiers sum to a constant in D."""
    return 1.0 - wood_gate(D)


def outboard_ramp(f):
    """0 at the rim, 1 by NB_F1.  Nothing may stand in the runoff."""
    return T.smoothstep(NB_F0, NB_F1, np.asarray(f, float))


def height_ceiling(f):
    """Metres.  Monotone, continuous, saturating.  THE PHYSICAL RULE.

    Nothing this module emits may declare a height above this at its own `f`.  It is
    piecewise linear through F_RAMP and flat beyond the last knot, so it has no step
    anywhere and a candidate one metre further out is never allowed a metre more of
    plant than its neighbour.
    """
    f = np.asarray(f, float)
    fs = np.array([k[0] for k in F_RAMP])
    hs = np.array([k[1] for k in F_RAMP])
    return np.interp(np.clip(f, fs[0], fs[-1]), fs, hs)


def tier_weight(tier, f):
    """Crossfaded membership in `f`.  The three weights sum to 1 for every f.

    THEY CROSSFADE, THEY DO NOT BUTT — the same rule R2-1661 wrote for the sward
    tiers, for the same reason: a hard cut at f = 6 or f = 17 would lay a density
    line parallel to the track down the whole lap, which is a worse artefact than
    the bare ground it replaces.
    """
    f = np.asarray(f, float)
    a0, a1, b0, b1 = (list(tier["fw"]) + [None, None])[:4]
    w = np.ones_like(f)
    if a0 is not None:
        w = w * T.smoothstep(a0, a1, f)
    elif a1 is not None:                       # first tier: 1 - smoothstep(a1, b0, f)
        w = w * (1.0 - T.smoothstep(a1, b0, f))
        return np.clip(w, 0, 1)
    if b0 is not None:
        w = w * (1.0 - T.smoothstep(b0, b1, f))
    return np.clip(w, 0, 1)


def nb_density(h, tier=None):
    """The placement field.  `h` is a `build_terrain.habitat()` dict.

    THE ONLY D TERM IS THE COMPLEMENT.  There is deliberately no second distance
    term anywhere in this function: every additional D-dependent factor is another
    chance to put a ring in the picture, and the whole point of the complement is
    that it cannot.
    """
    d = nb_gate(h["D"]) * outboard_ramp(h["f"])
    # habitat modulation.  These are all f- and terrain-driven, never D-driven.
    d = d * (1.0 - 0.55 * h["plateau"])        # the plateau is managed grass
    d = d * (1.0 - 0.85 * h["ez"])             # declared event zones stay clear
    d = d * (1.0 - 0.80 * h["built"])          # the paddock gets AMENITY instead
    d = d * (0.72 + 0.55 * T.smoothstep(0.02, 0.20, h["slope"]))   # banks hold scrub
    # patchiness at 44 m and 11 m so the band is scrub-and-gaps and not a hedge wall.
    # Both are >= 0.42 at their floor, so no combination of them can make a hole the
    # size of the defect this module exists to fix.
    d = d * np.clip(0.62 + 0.52 * (0.5 + 0.5 * T.fbm(h["cx"] / 44.0, h["cy"] / 44.0,
                                                     3, seed=6301)), 0.42, 1.25)
    d = d * np.clip(0.70 + 0.44 * (0.5 + 0.5 * T.fbm(h["cx"] / 11.0, h["cy"] / 11.0,
                                                     2, seed=6303)), 0.48, 1.20)
    if tier is not None:
        d = d * tier_weight(tier, h["f"]) * tier["dens"]
    return np.clip(d, 0.0, 1.0)


# ==================================================================================
# 2.  THE EXACT TESTS.  Every one of these is proven to REJECT in `selftest`.
# ==================================================================================

def test_outside_corridor(x, y, clear):
    """`build_terrain.outside_corridor` — the EXACT corridor field, not the raster.

    The raster is a 14 m lattice and interpolating `f` across it is worth a metre near
    a tight rim, so every final position gets this.
    """
    return T.outside_corridor(x, y, clear)


def test_off_paving(x, y, standoff):
    """Metres outside the contract's DECLARED z = 0.000 platform.

    `C.platform_field` is the same field `build_terrain.cut_field` cuts the ground
    mesh with, so a plant that passes this always has ground under it.
    """
    return np.asarray(C.platform_field(np.asarray(x, float),
                                       np.asarray(y, float)), float) > standoff


_RT = np.linspace(0.0, C.ACCESS_TOTAL, 2001)
_RX, _RY, _RH = C.access_route_arrays(_RT)


def test_transit_clear(x, y, clear=None):
    """Distance to the DECLARED beat-3/4 transit route centreline.

    A SECOND, INDEPENDENT test.  `corridor_field` already contains the access ribbon,
    but the amenity tier plants nearer to it than anything else in the world does, and
    a keep-out that exists only as a side effect of another module's field is a
    keep-out that disappears the day that field is re-scoped.
    """
    clear = NB_TRANSIT_CLEAR_M if clear is None else clear
    x = np.atleast_1d(np.asarray(x, float)); y = np.atleast_1d(np.asarray(y, float))
    d = np.full(x.shape, np.inf)
    for a in range(0, len(_RT), 256):
        b = min(len(_RT), a + 256)
        d = np.minimum(d, np.min(np.hypot(x[:, None] - _RX[None, a:b],
                                          y[:, None] - _RY[None, a:b]), axis=1))
    return d > clear


def test_forecourt_clear(x, y, clear=None):
    """Outside build_architecture's declared showroom forecourt box + clearance."""
    clear = NB_FORECOURT_CLEAR_M if clear is None else clear
    f = C.FORECOURT_WORLD
    return (np.abs(np.asarray(x, float) - f["cx"]) > f["hx"] + clear) | \
           (np.abs(np.asarray(y, float) - f["cy"]) > f["hy"] + clear)


def test_height_ok(target_h, f, tol=1e-6):
    """THE CEILING.  Nothing may be emitted taller than `height_ceiling(f)`."""
    return np.asarray(target_h, float) <= height_ceiling(f) + tol


def clip_height(target_h, f):
    return np.minimum(np.asarray(target_h, float), height_ceiling(f))


def test_species_fits(key, f):
    """A species may stand at `f` only if its SHORTEST specimen fits the ceiling.

    This is what refuses an oak at f = 25 m: SPECIES["oak"]["h"][0] = 12.0 against a
    ceiling of 4.99 m there.  Scaling an oak down to 5 m is not a small oak, it is a
    5 m tree with an oak's 21 m branching order, and it reads as one.
    """
    return float(T.SPECIES[key]["h"][0]) <= float(height_ceiling(f))


# ==================================================================================
# 3.  MESH COMPOSITION — merge the SHIPPING generators, author no new plant
# ==================================================================================

def _read_mesh(me):
    nv, nl, npo = len(me.vertices), len(me.loops), len(me.polygons)
    V = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", V)
    LV = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", LV)
    LS = np.empty(npo, np.int32); me.polygons.foreach_get("loop_start", LS)
    LT = np.empty(npo, np.int32); me.polygons.foreach_get("loop_total", LT)
    MI = np.empty(npo, np.int32); me.polygons.foreach_get("material_index", MI)

    def at(nm):
        a = me.attributes.get(nm)
        if a is None:
            return np.zeros(nv, np.float32)
        o = np.empty(nv, np.float32); a.data.foreach_get("value", o)
        return o
    # Loops are contiguous in polygon order for everything `new_mesh_arrays` built,
    # which is every mesh in this world -- but the merge does not ASSUME it, because
    # a merge that silently scrambles a polygon when the assumption fails is exactly
    # the class of defect this project keeps finding.  The check is two array ops.
    if npo:
        want = np.concatenate([[0], np.cumsum(LT)[:-1]]).astype(np.int32)
        if not np.array_equal(LS, want):
            LV = LV[np.concatenate([np.arange(s, s + t)
                                    for s, t in zip(LS, LT)]).astype(np.int64)]
    return dict(V=V.reshape(-1, 3).astype(np.float64), LV=LV,
                LT=LT, MI=MI, pid=at("pid"), pgrad=at("pgrad"),
                mats=[m.name if m is not None else None for m in me.materials])


def _new_mesh_loops(name, V, LV, LT, MI, pid, pgrad, matnames):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", np.asarray(V, np.float32).ravel())
    if len(LT):
        starts = np.concatenate([[0], np.cumsum(LT)[:-1]]).astype(np.int32)
        me.loops.add(len(LV)); me.loops.foreach_set("vertex_index",
                                                    np.asarray(LV, np.int32))
        me.polygons.add(len(LT)); me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    if len(LT):
        me.polygons.foreach_set("material_index", np.asarray(MI, np.int32))
    a = me.attributes.new("pid", "FLOAT", "POINT")
    a.data.foreach_set("value", np.asarray(pid, np.float32))
    g = me.attributes.new("pgrad", "FLOAT", "POINT")
    g.data.foreach_set("value", np.asarray(pgrad, np.float32))
    for mn in matnames:
        me.materials.append(bpy.data.materials[mn])
    me.update()
    return me


def merge_parts(name, parts, drop=True):
    """Merge (mesh, offset, scale_xyz, spin_z) parts into ONE clump mesh.

    Material slots are unioned BY NAME and every part's polygon indices are remapped,
    so a clump can carry hazel bark, gorse leaf, dock flower and a flint pebble at
    once without any of the shipping generators being told about the others.
    `drop=True` removes the component datablock afterwards: the clump owns the
    geometry now, and 44 clumps x 8 parts of orphan meshes is 350 datablocks of
    nothing.
    """
    Vs, LVs, LTs, MIs, PIs, PGs = [], [], [], [], [], []
    names = []
    vo = 0
    used = []
    for me, off, scl, spin in parts:
        d = _read_mesh(me)
        used.append(me)
        remap = np.zeros(max(1, len(d["mats"])), np.int32)
        for i, mn in enumerate(d["mats"]):
            mn = mn or (T.VPFX + "bark_hawthorn")
            if mn not in names:
                names.append(mn)
            remap[i] = names.index(mn)
        c, s = math.cos(spin), math.sin(spin)
        P = d["V"] * np.asarray(scl, float)[None, :]
        Vp = np.empty_like(P)
        Vp[:, 0] = P[:, 0] * c - P[:, 1] * s + off[0]
        Vp[:, 1] = P[:, 0] * s + P[:, 1] * c + off[1]
        Vp[:, 2] = P[:, 2] + off[2]
        Vs.append(Vp)
        LVs.append(d["LV"].astype(np.int64) + vo)
        LTs.append(d["LT"])
        MIs.append(remap[np.clip(d["MI"], 0, len(remap) - 1)])
        PIs.append(d["pid"]); PGs.append(d["pgrad"])
        vo += len(Vp)
    V = np.concatenate(Vs) if Vs else np.zeros((0, 3))
    me = _new_mesh_loops(name, V,
                         np.concatenate(LVs) if LVs else np.zeros(0, np.int32),
                         np.concatenate(LTs) if LTs else np.zeros(0, np.int32),
                         np.concatenate(MIs) if MIs else np.zeros(0, np.int32),
                         np.concatenate(PIs) if PIs else np.zeros(0),
                         np.concatenate(PGs) if PGs else np.zeros(0),
                         names)
    if drop:
        for m in used:
            try:
                bpy.data.meshes.remove(m)
            except Exception:
                pass
    hmax = float(V[:, 2].max()) if len(V) else 0.0
    half = float(np.abs(V[:, :2]).max()) if len(V) else 0.0
    return me, hmax, half


def _tris(me):
    return T._mesh_tris(me)


def _top_z(me):
    """The mesh's ACTUAL top, not the height its generator declared.

    They are not the same and the difference is not small.  `gen_weed` returns the
    drawn habit height but `_weed_head` then puts a flowering head on top of the
    stem, so a "0.9 m" dock is 1.1 m of geometry; `gen_grass` returns the longest
    BLADE LENGTH, but the blade leans, so a "0.6 m" tussock is 0.45 m tall.  Scaling
    a clump's parts by the declared numbers therefore leaves the clump's real height
    somewhere either side of what was asked for -- which is exactly what selftest
    check 8b caught, twice.
    """
    n = len(me.vertices)
    if not n:
        return 1e-3
    V = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", V)
    return float(max(V.reshape(-1, 3)[:, 2].max(), 1e-3))


# ==================================================================================
# 4.  THE CLUMP.  Composed from build_terrain's own generators, nothing new.
# ==================================================================================

def gen_nb_clump(rng, tier):
    """ONE near-band scrub clump, authored at TRUE WORLD SIZE over `pitch` metres.

    DRAWN OVER 1.45 x THE PITCH IT IS PLACED AT (`gen_sward`'s anti-tiling law): a
    patch drawn at exactly the placement pitch tiles, and a tiling ground cover along
    a 3 675 m verge is a picket fence.

    Every element is a call into `build_terrain`.  The clump's returned height is its
    TALLEST ELEMENT, because `gn_kind` normalises each library mesh by that number and
    rescales the lot by one target -- so the target this module passes IS the height of
    the tallest plant in the placed clump, exactly, and the ceiling test is exact.
    """
    half = tier["pitch"] * 1.45 * 0.5
    hn = tier["hnom"]
    parts = []
    stems = 0

    def spot(r=1.0):
        a = rng.uniform(0, 2 * math.pi)
        rr = half * r * math.sqrt(rng.random())
        return np.array([math.cos(a) * rr, math.sin(a) * rr, 0.0])

    def add(me, _declared, lo, hi, r, breadth=(0.86, 1.30)):
        """Scale a generator's output to a TARGET HEIGHT relative to the tier's hnom.

        NOT to the generator's own habit height.  A dock is 0.40-1.15 m and a broom is
        0.50-1.40 m; dropped into a tier whose whole ceiling is 0.62 m at their natural
        size, the clump's tallest element is whatever the dice said and the tier's
        nominal height means nothing.  Since `gn_kind` normalises by the clump's
        tallest element, that would have made the placed size a function of which weed
        was drawn -- the exact failure `gen_sward`'s docstring records for returning
        the plant height instead of the plan half-extent.
        """
        t = hn * rng.uniform(lo, hi)
        sc = float(t / _top_z(me))          # MEASURED extent, not the declared one
        w = float(rng.uniform(*breadth))
        parts.append((me, spot(r), (sc * w, sc * float(rng.uniform(*breadth)), sc),
                      rng.uniform(0, 2 * math.pi)))

    # --- the woody core --------------------------------------------------------
    # ONE ELEMENT IS THE LEADER and is drawn at 0.90-1.04 x hnom.  Without it the
    # clump's tallest element is the maximum of a handful of independent uniforms and
    # a clump that happened to draw a short weed and a short tussock declares 0.38 m
    # where the tier says 0.62 -- so `gn_kind` scales it up 1.6x and the placed size
    # is a function of the dice rather than of the tier.  (The selftest caught exactly
    # that on its first run; the check is check 8b.)
    ns = int(rng.integers(tier["nshrub"][0], tier["nshrub"][1] + 1))
    keys = [k for k, w in tier["shrubs"]]
    wts = np.array([w for k, w in tier["shrubs"]], float)
    wts /= wts.sum()
    lead = ns >= 1                          # a shrub leads if there is one
    for i in range(ns):
        key = keys[int((rng.random() > np.cumsum(wts)).sum())]
        lod = tier["shrub_lod"]
        if lod is None:
            lod = 0 if rng.random() < tier["lod0_p"] else 1
        me, h0 = T.gen_shrub(key, np.random.default_rng(int(rng.integers(1 << 31))),
                             lod)
        if i == 0:
            add(me, h0, 0.90, 1.04, 0.55)
        else:
            add(me, h0, 0.40, 0.92, 0.62)
        stems += 1

    # --- a sapling coming up through it ---------------------------------------
    if rng.random() < tier["sapling"]:
        me, h0 = T.gen_tree("sapling",
                            np.random.default_rng(int(rng.integers(1 << 31))),
                            1 if rng.random() < 0.5 else 0)
        if lead:
            add(me, h0, 0.70, 0.98, 0.45, breadth=(0.90, 1.10))
        else:
            add(me, h0, 0.90, 1.04, 0.45, breadth=(0.90, 1.10))
            lead = True
        stems += 1

    # --- the weed stand.  A verge is not grass; it is grass AND dock AND thistle.
    nw = int(rng.integers(tier["nweed"][0], tier["nweed"][1] + 1))
    for i in range(nw):
        key = tier["weeds"][int(rng.integers(0, len(tier["weeds"])))]
        me, h0 = T.gen_weed(key, np.random.default_rng(int(rng.integers(1 << 31))))
        if lead:
            add(me, h0, tier["wfrac"][0], tier["wfrac"][1], 0.95)
        else:
            add(me, h0, 0.90, 1.04, 0.75)   # the weed stand leads a tier with no shrub
            lead = True
        stems += 1

    # --- the skirt.  Tussocks at the base, or the clump floats. -----------------
    ng = int(rng.integers(tier["ngrass"][0], tier["ngrass"][1] + 1))
    for i in range(ng):
        kd = tier["grass"][int(rng.integers(0, len(tier["grass"])))]
        nb = int(rng.integers(tier["gblades"][0], tier["gblades"][1] + 1))
        me, gh = T.gen_grass(np.random.default_rng(int(rng.integers(1 << 31))),
                             kind=kd, blades=nb, segs=2, lod=tier["grass_lod"])
        add(me, gh, tier["gfrac"][0], tier["gfrac"][1], 1.00)

    # --- stones.  Bare ground is made of the 10-95 mm fraction, not of a bump map.
    nst = int(rng.integers(tier["nstone"][0], tier["nstone"][1] + 1))
    for i in range(nst):
        key = "cobble" if rng.random() < 0.5 else "pebble"
        me, h0 = T.gen_stone(key, np.random.default_rng(int(rng.integers(1 << 31))))
        # STONES KEEP THEIR OWN SIZE -- a cobble is 0.10-0.34 m whatever is growing
        # over it -- so they are scaled to an ABSOLUTE target, not to hnom.  And they
        # are scaled off the MEASURED extent: `gen_stone` returns a mesh about 1.5 m
        # across whatever size class was asked for (it is normalised by `gn_kind`
        # downstream, which is where `STONES[key]["h"]` is actually applied), so
        # multiplying its own return by anything near 1.0 puts a 1.5 m boulder in a
        # 0.62 m verge clump.  It did: selftest check 8b reported an N1 clump
        # declaring 1.333 m against an hnom of 0.62.
        tgt = float(rng.uniform(*T.STONES[key]["h"]))
        sc = tgt / _top_z(me)
        # bedded 15-40 % into the ground: a stone lying ON a plane is a stone lying
        # on a plane, and at a grazing sun the difference is the shadow's shape
        p = spot(1.0); p[2] = -tgt * rng.uniform(0.15, 0.40)
        parts.append((me, p, (sc * 1.2, sc, sc), rng.uniform(0, 2 * math.pi)))

    me, hmax, hh = merge_parts(
        T.VPFX + NAME + "clump_%s_%04d" % (tier["tag"], rng.integers(0, 1 << 30) % 9999),
        parts)
    return me, max(hmax, 1e-3), stems


def gen_nb_hedge(rng, lod=1):
    """ONE clipped-hedge segment: AM_HEDGE_LEN of trimmed run, drawn along +x.

    Composed from `gen_shrub` squeezed into the trimmed box.  A clipped hedge IS a
    shrub that has been sheared; the shearing is a non-uniform scale plus a top
    plane, not a different plant, and pretending otherwise would mean authoring a
    plant this project already has.

    RETURNED AT UNIT HEIGHT AND TRUE LENGTH, and that is not cosmetic -- it is
    `gen_sward`'s law in the other axis.  `nb_gn` normalises every library mesh by the
    height it is handed and then rescales the lot, so whatever this returns becomes
    the thing every segment is made equal in.  Normalising a 2.00 m segment
    UNIFORMLY by its own 0.85-1.45 m height would have made its LENGTH 1.38-2.35 m --
    a run laid at a 1.85 m pitch would then gap in some places and pile up in others,
    driven by a dice roll about how tall that segment happened to be drawn.  So the
    shear normalises Z ONLY: length and thickness survive at the metres they were
    drawn at, and the placement scale carries height in metres directly.
    """
    L = AM_HEDGE_LEN
    W = rng.uniform(*AM_HEDGE_W)
    H = rng.uniform(*AM_HEDGE_H)
    parts = []
    n = int(rng.integers(3, 6))
    for i in range(n):
        key = "hazel" if rng.random() < 0.62 else "juniper"
        me, h0 = T.gen_shrub(key, np.random.default_rng(int(rng.integers(1 << 31))),
                             lod)
        sx = (L / n) * rng.uniform(1.35, 1.85) / max(h0, 0.05)
        sy = (W * 0.62) * rng.uniform(0.9, 1.25) / max(h0, 0.05)
        sz = H * rng.uniform(0.92, 1.08) / max(h0, 0.05)
        off = np.array([(i + 0.5) / n * L - L * 0.5 + rng.normal(0, 0.05),
                        rng.normal(0, 0.035), -H * rng.uniform(0.02, 0.10)])
        parts.append((me, off, (sx, sy, sz), rng.uniform(-0.25, 0.25)))
    me, hmax, hh = merge_parts(
        T.VPFX + NAME + "hedge_%04d" % (rng.integers(0, 1 << 30) % 9999), parts)
    # THE SHEAR.  Everything above the trim line is cut off, which is what makes it a
    # hedge and not a row of bushes.  Done on the merged mesh by clamping z, so no
    # generator had to know it was going to be clipped.
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    P = V.reshape(-1, 3)
    top = H * rng.uniform(0.96, 1.02)
    P[:, 2] = np.minimum(P[:, 2], top)
    P[:, 1] = np.clip(P[:, 1], -W * 0.5, W * 0.5)
    P[:, 2] /= max(top, 1e-3)              # Z ONLY -- see the docstring
    me.vertices.foreach_set("co", P.ravel())
    me.update()
    # the sheared faces are a plane of cut twig ends, not a shrub's silhouette, and
    # they get the material authored for that (see `mat_nb_clipped`)
    cm = bpy.data.materials.get(T.VPFX + NAME + "clipped")
    if cm is not None:
        for i, m in enumerate(me.materials):
            if m is not None and m.name.startswith(T.VPFX + "leaf_shrub_"):
                me.materials[i] = cm
    return me, 1.0                         # unit height by construction


def gen_nb_planter(rng):
    """A kerbed planting bed: a ring of field stone with shrubs standing in it.

    The stone ring is `gen_stone("cobble")` laid on a rectangle -- the same generator
    the scree and the grit use.  No new primitive; a planter on a real forecourt is a
    kerb and some plants, and this is a kerb and some plants.
    """
    parts = []
    hx = rng.uniform(0.85, 1.45)
    hy = rng.uniform(0.70, 1.10)
    n = int(rng.integers(10, 17))
    for i in range(n):
        t = (i + 0.5) / n * 4.0
        k = int(t)
        u = t - k
        px, py = ((-hx + 2 * hx * u, -hy), (hx, -hy + 2 * hy * u),
                  (hx - 2 * hx * u, hy), (-hx, hy - 2 * hy * u))[k % 4]
        me, h0 = T.gen_stone("cobble",
                             np.random.default_rng(int(rng.integers(1 << 31))))
        sc = rng.uniform(0.55, 0.95) / max(h0, 0.02) * 0.28
        parts.append((me, np.array([px, py, -0.02]), (sc, sc, sc * 1.15),
                      rng.uniform(0, 2 * math.pi)))
    for i in range(int(rng.integers(2, 5))):
        key = "juniper" if rng.random() < 0.5 else "broom"
        me, h0 = T.gen_shrub(key, np.random.default_rng(int(rng.integers(1 << 31))),
                             1)
        sc = rng.uniform(0.55, 0.95) / max(h0, 0.05)
        parts.append((me, np.array([rng.uniform(-hx * 0.6, hx * 0.6),
                                    rng.uniform(-hy * 0.6, hy * 0.6), 0.08]),
                      (sc, sc, sc), rng.uniform(0, 2 * math.pi)))
    me, hmax, hh = merge_parts(
        T.VPFX + NAME + "planter_%04d" % (rng.integers(0, 1 << 30) % 9999), parts)
    # normalised to unit height UNIFORMLY (a planter is not sheared, so its plan size
    # is allowed to follow its height), so the placement scale is metres of height
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    P = V.reshape(-1, 3) / max(hmax, 1e-3)
    me.vertices.foreach_set("co", P.ravel())
    me.update()
    return me, 1.0


# ==================================================================================
# 5.  THE CLIPPED-SURFACE MATERIAL -- the one shader this module authors
# ==================================================================================
# A sheared hedge face is not a shrub's silhouette: it is a plane of cut twig ends, and
# at a 12.47 deg sun that plane is the brightest thing in the paddock unless it carries
# relief.  ONE material, and both of its numbers come from itemkit rather than from a
# keyboard.

NB_HEDGE_LAM_M = 0.045          # the sheared twig-end scale: 45 mm
NB_HEDGE_MOD_PP = 0.26          # what we want that surface to DO to the light
NB_HEDGE_SHOT = dict(distance_m=26.0, lens_mm=35.0)   # beats 1-4 see it from here


def mat_nb_clipped():
    name = T.VPFX + NAME + "clipped"
    t = T.NT(name)
    detail = K.detail_for(NB_HEDGE_LAM_M, **NB_HEDGE_SHOT)
    amp_mm = K.relief_amplitude_for(NB_HEDGE_MOD_PP, wavelength_m=NB_HEDGE_LAM_M)
    pg = t.attr("pgrad")
    oi = t.n("ShaderNodeObjectInfo")
    dark = (0.021, 0.038, 0.016)
    lit = (0.058, 0.086, 0.034)
    base = t.mix((pg, 2), dark, lit)
    hs = t.n("ShaderNodeHueSaturation")
    t.link(base, 2, hs, "Color")
    vv = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", vv, 0)
    t.set(vv, "To Min", 0.78); t.set(vv, "To Max", 1.24)
    t.link(vv, 0, hs, "Value")
    # `Scale` is cycles per unit of the generated coordinate; the wavelength is the
    # reciprocal, and it is the wavelength `detail_for` was asked about.
    nse = t.noise(1.0 / NB_HEDGE_LAM_M, detail=detail, rough=0.52)
    bump = t.n("ShaderNodeBump")
    t.set(bump, "Strength", 1.0)
    t.set(bump, "Distance", amp_mm * 1e-3)
    t.link(nse, "Fac", bump, "Height")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    # BLENDER 5.2 MOVED Principled BSDF.Normal FROM SOCKET 5 TO 6.  By name, always.
    t.link(bump, "Normal", p, "Normal")
    t.set(p, "Roughness", 0.62); t.set(p, "Specular IOR Level", 0.28)
    tr = t.n("ShaderNodeBsdfTranslucent")
    t.link(hs, 0, tr, "Color")
    sh = t.n("ShaderNodeMixShader")
    sh.inputs[0].default_value = 0.22
    t.link(p, 0, sh, 1); t.link(tr, 0, sh, 2)
    t.out(sh)
    return dict(material=name, wavelength_m=NB_HEDGE_LAM_M, detail=float(detail),
                amplitude_mm=round(float(amp_mm), 4),
                finest_octave_mm=round(
                    K.finest_octave_for(NB_HEDGE_LAM_M, detail,
                                        **NB_HEDGE_SHOT)["finest_mm"], 4))


# ==================================================================================
# 6.  THE EMITTER.  Geometry-nodes instances the depsgraph can walk.
# ==================================================================================

def nb_gn(name, meshes, P, rot, scl, parent):
    """`build_terrain.gn_kind` with the rotation and scale supplied by the caller.

    `gn_kind` is used verbatim for every scattered tier -- it already varies height,
    breadth, mirroring, lean, spin, colour, season and canopy density per instance,
    and re-deriving that here would be a second implementation of a solved problem.
    This variant exists ONLY for the amenity runs, where the instance must be aligned
    to a paving edge and a random spin is precisely wrong.  Same node graph, same
    unit-height normalisation, same named-attribute wiring.
    """
    n = len(P)
    if n == 0 or not meshes:
        return 0
    lib = bpy.data.collections.new(T.VPFX + name + "_lib")
    for me, h0 in meshes:
        m2 = me.copy(); m2.name = me.name + "_u"
        if h0 > 1e-4:
            V = np.empty(len(m2.vertices) * 3, np.float32)
            m2.vertices.foreach_get("co", V)
            m2.vertices.foreach_set("co", (V.reshape(-1, 3) / h0).ravel())
            m2.update()
        lib.objects.link(bpy.data.objects.new(m2.name, m2))
    # DETERMINISTIC.  `hash(str)` is salted per process (PYTHONHASHSEED), and a build
    # that is not reproducible cannot be A/B'd against the frame that rejected it.
    seed = (sum(ord(c) * (i + 7) for i, c in enumerate(name)) + SEED) % (1 << 31)
    idx = np.random.default_rng(seed).integers(0, len(meshes), n)
    me = T.new_mesh_arrays(T.VPFX + name, P, None, None)
    for nm, data in (("inst_rot", rot), ("inst_scl", scl)):
        a = me.attributes.new(nm, "FLOAT_VECTOR", "POINT")
        a.data.foreach_set("vector", np.asarray(data, np.float32).ravel())
    a = me.attributes.new("inst_idx", "INT", "POINT")
    a.data.foreach_set("value", np.asarray(idx, np.int32))
    ob = bpy.data.objects.new(T.VPFX + name, me)
    parent.objects.link(ob)
    ng = bpy.data.node_groups.new(T.VPFX + "gn_" + name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    N = ng.nodes
    gi = N.new("NodeGroupInput"); gi.location = (-700, 0)
    go = N.new("NodeGroupOutput"); go.location = (400, 0)
    iop = N.new("GeometryNodeInstanceOnPoints"); iop.location = (100, 0)
    ci = N.new("GeometryNodeCollectionInfo"); ci.location = (-300, -260)
    ci.inputs[0].default_value = lib
    ci.inputs[1].default_value = True
    ci.inputs[2].default_value = True
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
    m = ob.modifiers.new(T.VPFX + "gn", "NODES")
    m.node_group = ng
    return n


# ==================================================================================
# 7.  PLACEMENT
# ==================================================================================

_PLACED = []            # every emission: for the density table and the gate


def _record(tier, kind, P, stems, tris_each, sources, top_share):
    _PLACED.append(dict(tier=tier, kind=kind, n=int(len(P)),
                        stems=int(stems), tris=int(len(P) * tris_each),
                        sources=int(sources), top_share=float(top_share),
                        P=np.asarray(P, float)))


def candidate_domain(dom):
    """The bbox this tier can possibly place in, intersected with build()'s domain.

    Everything here lives within `WOOD_GATE_D[1]` of the centreline, so scattering
    candidates over build_terrain's full 2 960 x 2 960 m square is 3.5x wasted work --
    at N1's 1.45 m pitch that is 4.2 M points and ~700 MB of raster samples on a box
    with 11 GB and three other Blenders running.  `_corridor_bbox()` is already padded
    by the widest platform_edge, so + WOOD_GATE_D[1] covers every candidate.
    """
    bx0, bx1, by0, by1 = T._corridor_bbox()
    pad = WOOD_GATE_D[1] + 30.0
    X0, X1, Y0, Y1 = dom
    return (max(X0, bx0 - pad), min(X1, bx1 + pad),
            max(Y0, by0 - pad), min(Y1, by1 + pad))


def build_scatter(gr, gz, cam, ras, lib, rng, q, coll, dom):
    """The three scrub tiers plus the short-tree emergent layer."""
    X0, X1, Y0, Y1 = candidate_domain(dom)
    log("  candidate domain %.0f..%.0f x %.0f..%.0f m (%.2f km2)"
        % (X0, X1, Y0, Y1, (X1 - X0) * (Y1 - Y0) / 1e6))
    out = {}
    tot_tris = 0

    for tier in NB_TIERS:
        t0 = time.time()
        nl = max(8, int(round(tier["nlib"] * (0.35 + 0.65 * q))))
        clumps = []
        for i in range(nl):
            clumps.append(gen_nb_clump(
                np.random.default_rng(int(rng.integers(1 << 31))), tier))
        mt = int(np.mean([_tris(m) for m, h, s in clumps]))
        mstem = float(np.mean([s for m, h, s in clumps]))
        log("  %s library: %d clumps, %d tris each (mean), %.1f woody stems each, %.0fs"
            % (tier["tag"], nl, mt, mstem, time.time() - t0))

        sx, sy, sr = T.jitter_grid(X0, X1, Y0, Y1, tier["pitch"], 4400 + ord(tier["tag"][-1]))
        r0 = ras.sample(sx, sy)
        # cheap pre-filter on the raster BEFORE the expensive habitat sweep
        keep = (r0["D"] < WOOD_GATE_D[1] + 20.0) & (r0["f"] > NB_F0 - 2.0)
        sx, sy, sr = sx[keep], sy[keep], sr[keep]
        if not len(sx):
            continue
        h = T.habitat(gr, gz, cam, sx, sy, ras)
        dens = nb_density(h, tier) * q
        take = np.where(sr < dens)[0]
        if not len(take):
            continue
        # --- THE EXACT TESTS, on the FINAL positions ---------------------------
        px, py = sx[take], sy[take]
        ok = test_outside_corridor(px, py, NB_F0)
        ok &= test_off_paving(px, py, NB_PAVE_STANDOFF_M)
        take = take[ok]
        if not len(take):
            continue
        px, py = sx[take], sy[take]
        hf = h["f"][take]
        # --- THE CEILING -------------------------------------------------------
        # target height is the clump's own habit, CLIPPED to the ramp.  Clipping and
        # not rejecting, because rejecting would thin the tier exactly at the rim,
        # which is where the defect is.
        want = tier["hnom"] * rng.uniform(0.72, 1.28, len(take))
        th = clip_height(want, hf)
        bad = ~test_height_ok(th, hf)
        if bad.any():                       # cannot happen; if it does, drop them
            take = take[~bad]; px, py = sx[take], sy[take]
            th = th[~bad]; hf = hf[~bad]
        # `xy` widens the footprint INDEPENDENTLY of height (gn_kind's own argument):
        # a clump scaled down to a 0.35 m ceiling would otherwise also shrink its plan
        # extent to 0.20 of the pitch and leave 96 % bare ground between clumps, which
        # is the flat wash again.
        ex = np.clip((tier["hnom"] / np.maximum(th, 1e-3)) ** 0.62, 0.72, 1.90)
        P = np.stack([px, py, gz(px, py) - 0.035], 1)
        got = T.gn_kind(NAME + "clump_" + tier["tag"],
                        [(m, hh) for m, hh, s in clumps], P, th, rng, coll,
                        lean=0.9, wide=0.11, xy=ex)
        tot_tris += got * mt
        _record(tier["tag"], "scrub_clump", P, int(round(got * mstem)), mt,
                len(clumps), 1.0 / max(1, len(clumps)))
        out["nb_%s_clumps" % tier["tag"]] = int(got)
        out["nb_%s_stems" % tier["tag"]] = int(round(got * mstem))
        log("  %s: %d clumps placed (pitch %.2f m, %d tris each)"
            % (tier["tag"], got, tier["pitch"], mt))

    # ---- THE SHORT-TREE EMERGENT LAYER -------------------------------------------
    tot_tris += _build_short_trees(gr, gz, cam, ras, lib, rng, q, coll, dom, out)
    out["nb_scatter_tris"] = int(tot_tris)
    return out


def _build_short_trees(gr, gz, cam, ras, lib, rng, q, coll, dom, out):
    """hawthorn / rowan / birch, and NOTHING taller, standing over the scrub.

    The species mix is not hand-weighted.  A target height is drawn in
    [NB_TREE_HMIN, ceiling(f)] and the species whose habit brackets it is taken; since
    ceiling(f) only reaches rowan's 7.0 m minimum at f = 30.3 m and birch's 8.0 m at
    f = 32.6 m, hawthorn takes the whole f 20-30 m band on its own.  That IS the
    "weighted toward hawthorn" the brief asks for, arrived at from the ramp.
    """
    X0, X1, Y0, Y1 = candidate_domain(dom)
    tx, ty, tr = T.jitter_grid(X0, X1, Y0, Y1, NB_TREE_PITCH, 5511)
    r0 = ras.sample(tx, ty)
    keep = (r0["D"] < WOOD_GATE_D[1] + 20.0) & (r0["f"] > 18.0)
    tx, ty, tr = tx[keep], ty[keep], tr[keep]
    if not len(tx):
        return 0
    h = T.habitat(gr, gz, cam, tx, ty, ras)
    dens = nb_density(h) * NB_TREE_DENS * q
    # a tree needs room the low tiers do not: the ceiling must clear NB_TREE_HMIN
    dens = dens * (height_ceiling(h["f"]) >= NB_TREE_HMIN)
    take = np.where(tr < dens)[0]
    if not len(take):
        return 0
    px, py = tx[take], ty[take]
    ok = test_outside_corridor(px, py, 8.0)
    ok &= test_off_paving(px, py, NB_PAVE_STANDOFF_TREE_M)
    take = take[ok]
    if not len(take):
        return 0
    px, py = tx[take], ty[take]
    hf = h["f"][take]
    ceil = height_ceiling(hf)
    th = NB_TREE_HMIN + (ceil - NB_TREE_HMIN) * rng.random(len(take)) ** 0.85
    th = clip_height(th, hf)
    dcam = h["dcam"][take]
    lod = np.where(dcam < 95.0, 0, np.where(dcam < 380.0, 1, 2))

    # species: the shortest habit that brackets the target, else the tallest that fits
    spec = np.full(len(take), 0, int)
    for i, key in enumerate(NB_TREES):
        lo, hi = T.SPECIES[key]["h"]
        spec = np.where((th >= lo) & (th <= hi), i, spec)
    fits = np.ones(len(take), bool)
    for i, key in enumerate(NB_TREES):
        lo, hi = T.SPECIES[key]["h"]
        m = spec == i
        fits &= ~(m & (th > hi + 1e-6))
        # the species gate: its SHORTEST specimen must fit the ceiling here
        fits &= ~(m & (lo > ceil + 1e-6))
    px, py, th, hf, lod, spec = (px[fits], py[fits], th[fits], hf[fits],
                                 lod[fits], spec[fits])
    if not len(px):
        return 0

    nb_lib = _short_tree_library(lib, rng, q)
    tris = 0
    n_all = 0
    for i, key in enumerate(NB_TREES):
        for l in (0, 1, 2):
            m = (spec == i) & (lod == l)
            if not m.any():
                continue
            ms = nb_lib[(key, l)]
            P = np.stack([px[m], py[m], gz(px[m], py[m]) - 0.05], 1)
            mt = int(np.mean([_tris(me) for me, hh in ms]))
            got = T.gn_kind(NAME + "tree_%s_L%d" % (key, l), ms, P, th[m], rng,
                            coll, lean=1.5, wide=0.10)
            tris += got * mt
            n_all += got
            _record("NT", "%s_L%d" % (key, l), P, got, mt, len(ms),
                    1.0 / max(1, len(ms)))
    out["nb_short_trees"] = int(n_all)
    out["nb_short_tree_tris"] = int(tris)
    log("  short trees: %d (%s), %d instanced tris" % (n_all, ",".join(NB_TREES), tris))
    return tris


_NB_TREE_LIB = {}


def _short_tree_library(lib, rng, q):
    """The existing library PLUS enough extra unique meshes to satisfy the gate.

    `tools/item_gate.py` demands `distinct_sources >= max(8, min(40, sqrt(realized)))`
    and `top_source_share <= 0.25` on the geometry-nodes path.  build_terrain's L0
    library is 8 unique meshes per species (`nlod[0]`), which passes the >= 8 floor but
    leaves a 12.5 % top share and no headroom.  So this tier tops each (species, L0)
    group up to NB_TREE_LIB_TARGET with meshes generated HERE, from the same
    `gen_tree`, seeded independently.  L1 (12) and L2 (16) are already fine.
    """
    if _NB_TREE_LIB:
        return _NB_TREE_LIB
    want = max(8, int(round(NB_TREE_LIB_TARGET * (0.4 + 0.6 * q))))
    for key in NB_TREES:
        for l in (0, 1, 2):
            ms = list(lib[(key, l)])
            if l in NB_TREE_LIB_EXTRA_LODS:
                while len(ms) < want:
                    me, hh = T.gen_tree(
                        key, np.random.default_rng(int(rng.integers(1 << 31))), l)
                    me.name = T.VPFX + NAME + "tree_%s_L%d_%02d" % (key, l, len(ms))
                    ms.append((me, hh))
            _NB_TREE_LIB[(key, l)] = ms
        log("  short-tree library %-9s L0 x%d  L1 x%d  L2 x%d"
            % (key, len(_NB_TREE_LIB[(key, 0)]), len(_NB_TREE_LIB[(key, 1)]),
               len(_NB_TREE_LIB[(key, 2)])))
    return _NB_TREE_LIB


# ---------------------------------------------------------------------------------
# 7b.  AMENITY.  Driven FROM `built`, not suppressed by it.
# ---------------------------------------------------------------------------------

def paving_edge_polylines(step=1.0):
    """The outline of the DECLARED paving, as world polylines.

    `C.APRON_REGIONS_CIRCUIT` (pit lane, garages, paddock, apron) + the showroom
    forecourt box, walked at `step` metres and transformed to world.  Stated once by
    the contract, so a hedge run cannot drift away from the pavement it edges the way
    `built`'s hand-drawn district drifted away from the architecture (R2-1821).
    """
    segs = []
    for name, (x0, x1, y0, y1) in C.APRON_REGIONS_CIRCUIT.items():
        for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1),
                                 (x1, y1, x0, y1), (x0, y1, x0, y0)):
            L = math.hypot(bx - ax, by - ay)
            n = max(2, int(L / step))
            t = np.linspace(0, 1, n)
            cx = ax + (bx - ax) * t
            cy = ay + (by - ay) * t
            wx, wy = T.circuit_to_world(cx, cy)
            segs.append((name, wx, wy))
    f = C.FORECOURT_WORLD
    for (ax, ay, bx, by) in ((-f["hx"], -f["hy"], f["hx"], -f["hy"]),
                             (f["hx"], -f["hy"], f["hx"], f["hy"]),
                             (f["hx"], f["hy"], -f["hx"], f["hy"]),
                             (-f["hx"], f["hy"], -f["hx"], -f["hy"])):
        L = math.hypot(bx - ax, by - ay)
        n = max(2, int(L / step))
        t = np.linspace(0, 1, n)
        segs.append(("forecourt", f["cx"] + ax + (bx - ax) * t,
                     f["cy"] + ay + (by - ay) * t))
    return segs


def _edge_offsets(wx, wy, off):
    """Offset a polyline OUTWARD, and return (x, y, heading).

    Outward is decided by `C.platform_field`: the side whose field is larger is the
    side that is not paved.  Measured, not assumed -- the circuit rectangles are not
    all wound the same way and half of them would otherwise have grown a hedge in the
    middle of the pit lane.
    """
    dx = np.gradient(wx); dy = np.gradient(wy)
    L = np.maximum(np.hypot(dx, dy), 1e-9)
    nx, ny = -dy / L, dx / L
    pa = np.asarray(C.platform_field(wx + nx * off, wy + ny * off), float)
    pb = np.asarray(C.platform_field(wx - nx * off, wy - ny * off), float)
    sgn = np.where(pa >= pb, 1.0, -1.0)
    return (wx + nx * off * sgn, wy + ny * off * sgn,
            np.arctan2(dy, dx))


def build_amenity(gr, gz, cam, ras, lib, rng, q, coll):
    """Clipped hedge runs, kerbed planters and ornamental small trees on the paving
    edges -- the thing that fills the band `(1 - 0.94*built)` empties."""
    out = {}
    mat = mat_nb_clipped()
    out["nb_clipped_material"] = mat
    log("  clipped-surface material: lam %.3f m, detail %.1f (finest %.2f mm), "
        "bump %.3f mm p-p" % (mat["wavelength_m"], mat["detail"],
                              mat["finest_octave_mm"], mat["amplitude_mm"]))

    nl = max(6, int(round(AM_HEDGE_LIB * (0.4 + 0.6 * q))))
    hedges = [gen_nb_hedge(np.random.default_rng(int(rng.integers(1 << 31))))
              for _ in range(nl)]
    planters = [gen_nb_planter(np.random.default_rng(int(rng.integers(1 << 31))))
                for _ in range(max(5, int(round(AM_PLANTER_LIB * (0.4 + 0.6 * q)))))]
    hmt = int(np.mean([_tris(m) for m, h in hedges]))
    pmt = int(np.mean([_tris(m) for m, h in planters]))
    log("  amenity library: %d hedge segments (%d tris), %d planters (%d tris)"
        % (len(hedges), hmt, len(planters), pmt))

    HX, HY, HR, HS = [], [], [], []
    TX, TY, TH = [], [], []
    PX, PY, PR = [], [], []
    tris = 0
    for ei, (name, wx, wy) in enumerate(paving_edge_polylines(0.7)):
        off = rng.uniform(AM_EDGE_BAND[0], AM_EDGE_BAND[1] * 0.55)
        ex, ey, eh = _edge_offsets(wx, wy, off)
        # walk the run at the hedge pitch, with real GAPS -- an unbroken 600 m hedge
        # round a paddock is as much of a lie as bare grass
        L = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(ex), np.diff(ey)))])
        if L[-1] < 6.0:
            continue
        run = np.arange(0.0, L[-1], AM_HEDGE_PITCH)
        gap = (0.5 + 0.5 * T.fbm(run / 26.0, np.full(len(run), ei * 3.7),
                                 2, seed=7717)) > 0.30
        run = run[gap]
        if not len(run):
            continue
        jx = np.interp(run, L, ex) + rng.normal(0, 0.06, len(run))
        jy = np.interp(run, L, ey) + rng.normal(0, 0.06, len(run))
        jh = np.interp(run, L, np.unwrap(eh))
        ok = test_outside_corridor(jx, jy, 1.0)
        ok &= test_off_paving(jx, jy, AM_EDGE_BAND[0])
        ok &= (np.asarray(C.platform_field(jx, jy), float) < AM_EDGE_BAND[1])
        ok &= test_transit_clear(jx, jy)
        ok &= test_forecourt_clear(jx, jy, 1.0)
        if not ok.any():
            continue
        jx, jy, jh, run = jx[ok], jy[ok], jh[ok], run[ok]
        # THE THREE AMENITY KINDS SHARE ONE LINE AND MUST NOT SHARE A STATION.  A
        # tree and a planter drawn at the same `run` as a hedge segment stand INSIDE
        # it -- three sets of geometry interpenetrating at the exact spot the beat-1
        # to beat-4 lens is pointed.  So the stations are partitioned: a tree takes
        # its station, a planter takes its station, and the hedge takes what is left.
        # A specimen tree standing in a gap in a hedge run is what a real forecourt
        # looks like anyway.
        tsel = (np.floor(run / AM_TREE_PITCH).astype(int) !=
                np.floor((run - AM_HEDGE_PITCH) / AM_TREE_PITCH).astype(int))
        psel = (np.floor(run / AM_PLANTER_PITCH).astype(int) !=
                np.floor((run - AM_HEDGE_PITCH) / AM_PLANTER_PITCH).astype(int))
        psel &= ~tsel
        hsel = ~(tsel | psel)
        if hsel.any():
            HX.append(jx[hsel]); HY.append(jy[hsel]); HR.append(jh[hsel])
            # height in METRES (the library is unit-height), CLIPPED to the f-ramp:
            # the pit-lane paving abuts the corridor, so a hedge run there can sit at
            # a small `f` and the same ceiling that governs the open band governs it
            hh_t = rng.uniform(AM_HEDGE_H[0], AM_HEDGE_H[1], int(hsel.sum()))
            HS.append(clip_height(hh_t, T.corridor_field(jx[hsel], jy[hsel])))
        if tsel.any():
            TX.append(jx[tsel]); TY.append(jy[tsel])
            TH.append(rng.uniform(AM_TREE_H[0], AM_TREE_H[1], int(tsel.sum())))
        if psel.any():
            PX.append(jx[psel]); PY.append(jy[psel]); PR.append(jh[psel])

    if HX:
        jx = np.concatenate(HX); jy = np.concatenate(HY)
        jh = np.concatenate(HR); js = np.concatenate(HS)
        P = np.stack([jx, jy, gz(jx, jy) - 0.03], 1)
        # ORIENTED, not spun: a hedge segment is aligned to the run it edges.  This is
        # the ONLY reason `nb_gn` exists instead of `gn_kind`.
        rot = np.stack([np.zeros(len(jx)), np.zeros(len(jx)), jh], 1)
        # x = 1.0 keeps the segment at the AM_HEDGE_LEN it was drawn at so the run
        # abuts at AM_HEDGE_PITCH; y varies the thickness; z IS the height in metres
        scl = np.stack([np.ones(len(jx)), rng.uniform(0.85, 1.20, len(jx)), js], 1)
        got = nb_gn(NAME + "hedge", hedges, P, rot, scl, coll)
        tris += got * hmt
        _record("AM", "clipped_hedge", P, got, hmt, len(hedges),
                1.0 / max(1, len(hedges)))
        out["nb_amenity_hedge_segments"] = int(got)
        out["nb_amenity_hedge_run_m"] = round(float(got * AM_HEDGE_LEN), 1)
    if PX:
        jx = np.concatenate(PX); jy = np.concatenate(PY); jh = np.concatenate(PR)
        P = np.stack([jx, jy, gz(jx, jy) - 0.02], 1)
        s = clip_height(rng.uniform(0.75, 1.15, len(jx)), T.corridor_field(jx, jy))
        rot = np.stack([np.zeros(len(jx)), np.zeros(len(jx)), jh], 1)
        scl = np.stack([s, s, s], 1)
        got = nb_gn(NAME + "planter", planters, P, rot, scl, coll)
        tris += got * pmt
        _record("AM", "planter", P, got, pmt, len(planters),
                1.0 / max(1, len(planters)))
        out["nb_amenity_planters"] = int(got)
    if TX:
        jx = np.concatenate(TX); jy = np.concatenate(TY); th = np.concatenate(TH)
        # a forecourt tree stands on the paved side of nothing: the ceiling still
        # applies, measured at its own f
        fz = T.corridor_field(jx, jy)
        th = clip_height(th, fz)
        keep = th >= 2.2
        jx, jy, th = jx[keep], jy[keep], th[keep]
        if len(jx):
            nb_lib = _short_tree_library(lib, rng, q)
            P = np.stack([jx, jy, gz(jx, jy) - 0.04], 1)
            ms = nb_lib[("hawthorn", 0)] + nb_lib[("rowan", 0)]
            mt = int(np.mean([_tris(me) for me, hh in ms]))
            got = T.gn_kind(NAME + "amenity_tree", ms, P, th, rng, coll,
                            lean=0.30, wide=0.07)
            tris += got * mt
            _record("AM", "ornamental_tree", P, got, mt, len(ms),
                    1.0 / max(1, len(ms)))
            out["nb_amenity_trees"] = int(got)
    out["nb_amenity_tris"] = int(tris)
    return out


# ==================================================================================
# 8.  THE ENTRY POINT
# ==================================================================================

class capture_terrain:
    """Run `build_terrain.build()` and keep the objects it made, without editing it.

    build() constructs a `Ground`, a `GridZ` off the BUILT mesh, a `CameraPath`, a
    `Raster` and a library, uses them, and drops them on the floor.  This tier needs
    exactly those five things and needs them to be THE SAME ONES -- a second `GridZ`
    sampled off `Ground.height` on a coarser grid is a different height field, and
    plants placed against it would sit at a different z from the woodland they are
    meant to blend into.

    So the five constructors are wrapped for the duration of the call and the
    instances recorded.  `build_terrain.py` is not touched: Python resolves module
    globals at call time, so setting the attribute back restores it exactly.
    """

    NAMES = ("Ground", "GridZ", "CameraPath", "Raster", "build_library")

    def __enter__(self):
        self.saved = {n: getattr(T, n) for n in self.NAMES}
        self.got = {}
        for n in self.NAMES:
            def mk(nm, orig):
                def f(*a, **k):
                    o = orig(*a, **k)
                    self.got[nm] = o
                    return o
                return f
            setattr(T, n, mk(n, self.saved[n]))
        return self

    def __exit__(self, *exc):
        for n, v in self.saved.items():
            setattr(T, n, v)
        return False


def terrain_context(q, ground=True, library=True):
    """Ground + library + camera path + raster, WITHOUT the rest of build_terrain.

    Used by `--terrain-only` and by `--selftest`.  A full `build_terrain.build()`
    is 982 s on this box and most of it is grass; iterating on a scrub tier does not
    need the grass.
    """
    spec = json.load(open(T.SPEC_JSON))
    beats = json.load(open(T.BEAT_JSON))
    cir = T.Circuit(spec)
    gr = T.Ground(cir)
    rng = np.random.default_rng(T.SEED)
    root = bpy.data.collections.get(T.COLL)
    if root is None:
        root = bpy.data.collections.new(T.COLL)
        bpy.context.scene.collection.children.link(root)
    T.build_materials()
    if ground:
        gob, attrs, (gxs, gys, gZ) = T.build_ground(gr, T._sub(root, "Ground"))
        gz = T.GridZ(gxs, gys, gZ)
    else:
        gz = T._probe_gz(gr, -1560, 1480, -1160, 1880, 40.0)
    cam = T.CameraPath(cir, beats)
    lib = None
    if library:
        nlod = [max(2, int(round(v * (0.45 + 0.55 * q)))) for v in (8, 12, 16, 7, 7, 9)]
        lib = T.build_library(rng, nlod)
    X0, X1, Y0, Y1 = -1520.0, 1440.0, -1120.0, 1840.0
    ras = T.Raster(gr, cam, X0 - 40, X1 + 40, Y0 - 40, Y1 + 40, 14.0, gz=gz)
    return dict(cir=cir, gr=gr, gz=gz, cam=cam, ras=ras, lib=lib, rng=rng,
                root=root, dom=(X0, X1, Y0, Y1))


_CTX = None


def build(ctx=None, quality=None, coll=None):
    """THE ENTRY.  Call with a context from `build_terrain.build()`, or with nothing.

    ctx keys: cir, gr, gz, cam, ras, lib, rng, root, dom.  Everything this tier needs
    is something build_terrain already made; nothing is recomputed.
    """
    global _CTX
    q = QUAL if quality is None else float(quality)
    t0 = time.time()
    if ctx is None:
        ctx = terrain_context(q)
    _CTX = ctx
    root = ctx.get("root") or bpy.data.collections.get(T.COLL)
    if coll is None:
        coll = bpy.data.collections.get(T.COLL + "/" + SUB)
        if coll is None:
            coll = T._sub(root, SUB)
    rng = ctx.get("rng") or np.random.default_rng(SEED)
    dom = ctx.get("dom", (-1520.0, 1440.0, -1120.0, 1840.0))

    log("near-band: the complement of smoothstep(%.0f, %.0f, D)" % WOOD_GATE_D)
    stats = {}
    stats.update(build_scatter(ctx["gr"], ctx["gz"], ctx["cam"], ctx["ras"],
                               ctx["lib"], rng, q, coll, dom))
    stats.update(build_amenity(ctx["gr"], ctx["gz"], ctx["cam"], ctx["ras"],
                               ctx["lib"], rng, q, coll))

    # BASE LIBRARY, COUNTED ONCE.  `gn_kind` links a unit-height COPY of every library
    # mesh into its own collection, named `<mesh>_u`.  Those copies are the same
    # geometry a second time; counting them doubled the figure on the first build.
    base = 0
    nbase = 0
    for me in bpy.data.meshes:
        if me.name.startswith(T.VPFX + NAME) and not me.name.endswith("_u"):
            base += _tris(me)
            nbase += 1
    stats["nb_base_library_tris"] = int(base)
    stats["nb_base_library_meshes"] = int(nbase)
    stats["nb_instanced_tris"] = int(sum(p["tris"] for p in _PLACED))
    stats["nb_instances"] = int(sum(p["n"] for p in _PLACED))
    stats["nb_woody_stems"] = int(sum(p["stems"] for p in _PLACED))
    stats["nb_build_s"] = round(time.time() - t0, 1)
    log("near-band done in %.1f s: %d instances, %d woody stems, %d instanced tris"
        % (time.time() - t0, stats["nb_instances"], stats["nb_woody_stems"],
           stats["nb_instanced_tris"]))
    return stats


# ==================================================================================
# 9.  MEASUREMENT.  The evidence, not the assertion.
# ==================================================================================

def _instance_positions():
    """Every woody instance in the scene, by tier, as world XY.

    Plain objects (build_terrain's woodland, hedgerow and avenue) come from
    `object.location`; geometry-nodes point clouds come from the point cloud itself.
    A tier that emitted GN instances and a tier that emitted objects are counted the
    same way, which is the only way the two curves can be compared.
    """
    out = {}
    root = bpy.data.collections.get(T.COLL)
    if root is None:
        return out
    stack = [root]
    colls = []
    while stack:
        c = stack.pop()
        colls.append(c)
        stack.extend(list(c.children))
    for c in colls:
        short = c.name.split("/")[-1]
        for o in c.objects:
            if o.type != 'MESH':
                continue
            # CLASSIFY BEFORE READING.  The grit tier alone is millions of points and
            # none of them are woody; pulling every point cloud into numpy and then
            # throwing most of it away is how an 11 GB box runs out of memory during
            # its own measurement.
            key = _classify(short, o.name)
            if key is None:
                continue
            if any(m.type == 'NODES' for m in o.modifiers):
                n = len(o.data.vertices)
                if not n:
                    continue
                V = np.empty(n * 3, np.float32)
                o.data.vertices.foreach_get("co", V)
                P = V.reshape(-1, 3)[:, :2].astype(float)
                P = P + np.array([o.location.x, o.location.y])[None, :]
            else:
                P = np.array([[o.location.x, o.location.y]])
            r = _radius_for(key, o.name)
            out.setdefault(key, []).append(
                np.concatenate([P, np.full((len(P), 1), r)], 1))
    return {k: np.concatenate(v) for k, v in out.items()}


# NOMINAL PLAN FOOTPRINT RADIUS, metres, per class.  DECLARED, not measured off the
# geometry -- an instance's true crown is a function of the mesh the GN node picked
# and its per-instance scale, and walking 4.7 M realized instances to get it is not a
# measurement anyone will re-run.  These are the numbers the placement itself was
# sized with: a clump's is `pitch * 0.42` (the drawn half-extent less the 1.45x
# anti-tiling overlap), a woodland tree's is 0.32 x the mean habit height of MIX_BASE.
#
# WHY THIS COLUMN EXISTS AT ALL.  The instance-COUNT table treats a three-stem gorse
# clump and a 21 m oak as one unit each, and they are not remotely the same amount of
# "not a blank green spot".  Counts are still printed, because they are what was
# actually placed and they cannot be argued with; cover is what the no-cliff verdict
# is taken on, because cover is the thing the client is looking at.
FOOT_R = {
    "woodland_tree": 4.5,
    "woodland_undergrowth": 0.55,
    "nearband_tree": 1.8,
    "nearband_scrub_N1": 0.61,      # NB_TIERS pitch 1.45 * 0.42
    "nearband_scrub_N2": 1.22,      # 2.90 * 0.42
    "nearband_scrub_N3": 1.72,      # 4.10 * 0.42
    "nearband_amenity_hedge": 0.67,  # a 2.00 x 0.70 m segment, equal-area radius
    "nearband_amenity_planter": 1.05,
    "nearband_amenity_tree": 1.60,
}


def _radius_for(key, obj_name):
    if key == "nearband_scrub":
        for t in NB_TIERS:
            if obj_name.endswith(t["tag"]):
                return FOOT_R["nearband_scrub_" + t["tag"]]
        return FOOT_R["nearband_scrub_N2"]
    if key == "nearband_amenity":
        if "planter" in obj_name:
            return FOOT_R["nearband_amenity_planter"]
        if "amenity_tree" in obj_name:
            return FOOT_R["nearband_amenity_tree"]
        return FOOT_R["nearband_amenity_hedge"]
    return FOOT_R.get(key, 1.0)


def _classify(coll_name, obj_name):
    n = obj_name
    if n.startswith(T.VPFX + NAME + "clump"):
        return "nearband_scrub"
    if n.startswith(T.VPFX + NAME + "tree"):
        return "nearband_tree"
    if n.startswith(T.VPFX + NAME + "hedge") or \
       n.startswith(T.VPFX + NAME + "planter") or \
       n.startswith(T.VPFX + NAME + "amenity"):
        return "nearband_amenity"
    if n.startswith(T.VPFX + "sward") or n.startswith(T.VPFX + "grass") or \
       n.startswith(T.VPFX + "weed") or n.startswith(T.VPFX + "stone") or \
       n.startswith(T.VPFX + "clod") or n.startswith(T.VPFX + "gritstone"):
        return None                       # ground cover, not woody
    if coll_name == "Trees" or n.startswith(T.VPFX + "tree_") or \
       n.startswith(T.VPFX + "hedge_") or n.startswith(T.VPFX + "avenue"):
        return "woodland_tree"
    if n.startswith(T.VPFX + "shrub_") or n.startswith(T.VPFX + "sapling") or \
       n.startswith(T.VPFX + "fern"):
        return "woodland_undergrowth"
    return None


def _D_of(x, y, chunk=200000):
    """Distance to the nearest centreline, the same `D` `habitat` uses."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    out = np.empty(len(x))
    for a in range(0, len(x), chunk):
        b = min(len(x), a + chunk)
        s, u = C.project(x[a:b], y[a:b])
        out[a:b] = np.abs(u)
    return out


BUILT_SPLIT = 0.30      # `habitat()["built"]` above this is the paddock/showroom
#                       district -- where woody cover is suppressed 94 % on purpose
#                       and the amenity tier, not the scrub tier, does the filling.


def annulus_areas(ctx, n=DENS_MC, seed=99):
    """Monte-Carlo m2 of PLANTABLE ground per 10 m D bin, split open / built.

    Plantable = outside the corridor (f > 0) and off the declared paving.  `f` and `D`
    come from the same 14 m raster the placement used, so the areas and the counts are
    measured against the same field; the +-1 m the raster costs near a tight rim is a
    tenth of a 10 m bin.  `built` comes from `build_terrain.habitat()` itself, not from
    a copy of its expression.
    """
    ras, dom = ctx["ras"], ctx["dom"]
    X0, X1, Y0, Y1 = candidate_domain(dom)
    rg = np.random.default_rng(seed)
    x = rg.uniform(X0, X1, n); y = rg.uniform(Y0, Y1, n)
    r = ras.sample(x, y)
    ok = (r["f"] > 0.0) & (r["D"] < DENS_BINS[-1] + 40.0)
    idx = np.where(ok)[0]
    pf = np.asarray(C.platform_field(x[idx], y[idx]), float)
    idx = idx[pf > 0.0]
    h = T.habitat(ctx["gr"], ctx["gz"], ctx["cam"], x[idx], y[idx], ras)
    cell = (X1 - X0) * (Y1 - Y0) / n
    op = h["built"] < BUILT_SPLIT
    a_open, _ = np.histogram(h["D"][op], bins=DENS_BINS)
    a_built, _ = np.histogram(h["D"][~op], bins=DENS_BINS)
    return a_open * cell, a_built * cell


def density_vs_D(ctx):
    """THE NO-CLIFF EVIDENCE.  Woody instance density per hectare, per 10 m D bin.

    The claim under test is that near-band + woodland is roughly constant in D and in
    particular has no step at 52 m (where the woodland gate switches on) or at 150 m
    (where it saturates).  This does not model either tier: it counts what is actually
    in the built scene.

    THE TABLE IS SPLIT BY `built`, AND THAT IS NOT A CONVENIENCE.  The amenity tier
    follows the outline of the declared paving, so it is a LINE, not a field, and a
    line lands in one or two D bins wherever the paddock happens to sit -- on the
    first standalone build it put 68 instances/ha in the 110-120 m bin and 3 in the
    next one.  That is not a ring in the picture (a hedge along a paddock edge is
    supposed to be a line); it is a D-histogram conflating "distance from the track"
    with "where the architecture is".  Mixing it into the open-country series would
    make the no-cliff statistic measure the paddock's position.  So the no-cliff
    figures are computed over OPEN COUNTRY (`built < 0.30`), where both the woodland
    gate and this tier are genuinely areal fields, and the built district is reported
    beside it with its own numbers.
    """
    a_open, a_built = annulus_areas(ctx)
    pos = _instance_positions()
    nb = len(DENS_BINS) - 1
    cnt = {}
    fpa = {}
    for k, P in pos.items():
        D = _D_of(P[:, 0], P[:, 1])
        h = T.habitat(ctx["gr"], ctx["gz"], ctx["cam"], P[:, 0], P[:, 1], ctx["ras"])
        op = h["built"] < BUILT_SPLIT
        a = math.pi * P[:, 2] ** 2                    # plan footprint, m2
        for zone, m in (("open", op), ("built", ~op)):
            cnt[(k, zone)] = np.histogram(D[m], bins=DENS_BINS)[0]
            fpa[(k, zone)] = np.histogram(D[m], bins=DENS_BINS, weights=a[m])[0]

    def series(src, zone, pred):
        s = np.zeros(nb)
        for (k, z), v in src.items():
            if z == zone and pred(k):
                s = s + v
        return s

    nbp = lambda k: k.startswith("nearband")          # noqa: E731
    old = series(cnt, "open", lambda k: not nbp(k))
    new = series(cnt, "open", nbp)
    bold = series(cnt, "built", lambda k: not nbp(k))
    bnew = series(cnt, "built", nbp)
    aold = series(fpa, "open", lambda k: not nbp(k))
    anew = series(fpa, "open", nbp)
    tot = old + new
    ha = np.maximum(a_open, 1.0) / 1e4
    hb = np.maximum(a_built, 1.0) / 1e4

    # RANDOM-DISC COVERAGE, not naive area/area.  Summed footprint over ground area
    # exceeds 1 as soon as crowns overlap, and a woodland at 150 trees/ha of 4.5 m
    # crown sums to 0.95 while a closed wood is nearer 0.80 of actual cover.  For
    # centres scattered at intensity lambda with footprint a, the fraction of ground
    # covered by at least one is 1 - exp(-lambda a) -- the same law the sward fix used
    # backwards to solve for its tuft count.
    cov_old = 1.0 - np.exp(-aold / np.maximum(a_open, 1.0))
    cov_tot = 1.0 - np.exp(-(aold + anew) / np.maximum(a_open, 1.0))

    table = []
    for i in range(nb):
        table.append(dict(d0=float(DENS_BINS[i]), d1=float(DENS_BINS[i + 1]),
                          area_ha=round(float(ha[i]), 3),
                          woodland_per_ha=round(float(old[i] / ha[i]), 2),
                          nearband_per_ha=round(float(new[i] / ha[i]), 2),
                          total_per_ha=round(float(tot[i] / ha[i]), 2),
                          woody_cover_before=round(float(cov_old[i]), 4),
                          woody_cover_after=round(float(cov_tot[i]), 4),
                          built_area_ha=round(float(hb[i]), 3),
                          built_woodland_per_ha=round(float(bold[i] / hb[i]), 2),
                          built_nearband_per_ha=round(float(bnew[i] / hb[i]), 2)))

    tps = tot / ha
    ops = old / ha
    # BINS WITH ALMOST NO GROUND IN THEM ARE NOT EVIDENCE.  D < ~15 m is the racing
    # surface: there is no plantable ground there at all, so its "density" is 0/0 and
    # including it would let the statistic be dominated by the one place the answer is
    # meaningless.  Every figure below is computed over bins carrying >= AREA_FLOOR
    # hectares of plantable ground, and the mask is reported so the choice is visible.
    AREA_FLOOR = 0.5
    valid = ha >= AREA_FLOOR
    vi = np.where(valid)[0]

    def step_at(edge, series):
        """Relative jump across a bin boundary, |a-b| / mean(a,b)."""
        j = int(edge // 10.0)
        if j < 1 or j >= len(series) or not (valid[j] and valid[j - 1]):
            return None
        a, b = series[j - 1], series[j]
        m = 0.5 * (a + b)
        return None if m <= 0 else round(float(abs(a - b) / m), 4)

    def max_step(series, lo=20.0, hi=200.0):
        js = [j for j in vi if lo <= DENS_BINS[j] < hi]
        best = 0.0
        worst = None
        for a, b in zip(js, js[1:]):
            if b != a + 1:
                continue
            m = 0.5 * (series[a] + series[b])
            if m <= 0:
                continue
            v = abs(series[a] - series[b]) / m
            if v > best:
                best, worst = v, (float(DENS_BINS[b]))
        return round(float(best), 4), worst

    msb, msb_at = max_step(ops)
    msa, msa_at = max_step(tps)
    cvb, cvb_at = max_step(cov_old)
    cva, cva_at = max_step(cov_tot)
    ev = dict(
        table=table,
        # THE VERDICT IS TAKEN ON COVER.  See FOOT_R for why the count series cannot
        # carry it: it treats a three-stem gorse clump and a 21 m oak as one unit.
        cover_step_at_52m_before=step_at(50.0, cov_old),
        cover_step_at_52m_after=step_at(50.0, cov_tot),
        cover_step_at_150m_before=step_at(150.0, cov_old),
        cover_step_at_150m_after=step_at(150.0, cov_tot),
        cover_max_step_20_200m_before=cvb, cover_max_step_before_at_m=cvb_at,
        cover_max_step_20_200m_after=cva, cover_max_step_after_at_m=cva_at,
        cover_zero_bins_before=int(((cov_old <= 0.002) & valid
                                    & (DENS_BINS[:-1] < 160)).sum()),
        cover_zero_bins_after=int(((cov_tot <= 0.002) & valid
                                   & (DENS_BINS[:-1] < 160)).sum()),
        mean_cover_0_52_before=round(float(
            cov_old[valid & (DENS_BINS[:-1] < 52)].mean()
            if (valid & (DENS_BINS[:-1] < 52)).any() else 0.0), 4),
        mean_cover_0_52_after=round(float(
            cov_tot[valid & (DENS_BINS[:-1] < 52)].mean()
            if (valid & (DENS_BINS[:-1] < 52)).any() else 0.0), 4),
        mean_cover_150_300=round(float(
            cov_tot[valid & (DENS_BINS[:-1] >= 150)].mean()), 4),
        area_floor_ha=AREA_FLOOR,
        bins_measured=int(valid.sum()),
        first_measured_bin_m=float(DENS_BINS[vi[0]]) if len(vi) else None,
        step_at_52m_before=step_at(50.0, ops), step_at_52m_after=step_at(50.0, tps),
        step_at_150m_before=step_at(150.0, ops), step_at_150m_after=step_at(150.0, tps),
        max_step_20_200m_before=msb, max_step_20_200m_before_at_m=msb_at,
        max_step_20_200m_after=msa, max_step_20_200m_after_at_m=msa_at,
        zero_bins_before=int(((ops <= 0.0) & valid & (DENS_BINS[:-1] < 160)).sum()),
        zero_bins_after=int(((tps <= 0.0) & valid & (DENS_BINS[:-1] < 160)).sum()),
        mean_total_per_ha_0_52=round(float(
            (tot[valid & (DENS_BINS[:-1] < 52)].sum()
             / max(ha[valid & (DENS_BINS[:-1] < 52)].sum(), 1e-9))), 2),
        mean_total_per_ha_150_300=round(float(
            (tot[valid & (DENS_BINS[:-1] >= 150)].sum()
             / max(ha[valid & (DENS_BINS[:-1] >= 150)].sum(), 1e-9))), 2),
        mean_woodland_per_ha_0_52=round(float(
            (old[valid & (DENS_BINS[:-1] < 52)].sum()
             / max(ha[valid & (DENS_BINS[:-1] < 52)].sum(), 1e-9))), 2),
        built_district=dict(
            woodland_per_ha=round(float(bold.sum() / max(hb.sum(), 1e-9)), 2),
            nearband_per_ha=round(float(bnew.sum() / max(hb.sum(), 1e-9)), 2),
            area_ha=round(float(hb.sum()), 1)),
    )
    return ev


def shadow_cover(patch=None, cell=0.25):
    """Plan cover vs plan+shadow cover over a real patch of the near band.

    THE MECHANISM IS SHADOW.  The sun sits at C.SUN_ELEV_DEG = 12.47 deg, so a 1.0 m
    scrub lays 4.52 m of shadow.  Every instance is stamped as its plan footprint and
    then as that footprint swept along the sun's ground bearing by h / tan(elev); the
    union of the stamps is the cover.  This is a geometric measurement of the same
    thing R2-1661 measured off a render (35 % plan -> 72 % screen).
    """
    if not _PLACED:
        return None
    if patch is None:
        # centre on the SCATTER tiers, not on the amenity runs: the question is what
        # the open near band does to the light, and a patch centred on the paddock
        # would answer a different one
        tags = {t["tag"] for t in NB_TIERS} | {"NT"}
        src = [p["P"][:, :2] for p in _PLACED if p["n"] and p["tier"] in tags]
        if not src:
            return None
        allP = np.concatenate(src)
        c = allP[np.random.default_rng(3).integers(0, len(allP))]
        patch = (c[0] - 90.0, c[0] + 90.0, c[1] - 90.0, c[1] + 90.0)
    x0, x1, y0, y1 = patch
    nx = int((x1 - x0) / cell); ny = int((y1 - y0) / cell)
    plan = np.zeros((nx, ny), bool)
    shad = np.zeros((nx, ny), bool)
    sd = np.array(C.SUN_DIR[:2], float)
    sd = -sd / max(np.linalg.norm(sd), 1e-9)          # ground direction of the shadow
    cot = 1.0 / math.tan(math.radians(C.SUN_ELEV_DEG))
    n_used = 0

    def stamp(A, cx, cy, r):
        """Union a disc into A, touching only the cells the disc can reach.

        Stamping into the whole 720 x 720 grid per disc is 10^10 operations for a
        real patch; this is 10^6.  Same answer.
        """
        i0 = max(0, int((cx - r - x0) / cell)); i1 = min(nx, int((cx + r - x0) / cell) + 2)
        j0 = max(0, int((cy - r - y0) / cell)); j1 = min(ny, int((cy + r - y0) / cell) + 2)
        if i1 <= i0 or j1 <= j0:
            return
        gx = x0 + (np.arange(i0, i1) + 0.5) * cell - cx
        gy = y0 + (np.arange(j0, j1) + 0.5) * cell - cy
        A[i0:i1, j0:j1] |= (gx[:, None] ** 2 + gy[None, :] ** 2) < r * r

    for p in _PLACED:
        if not p["n"]:
            continue
        P = p["P"]
        m = (P[:, 0] > x0 - 40) & (P[:, 0] < x1 + 40) & \
            (P[:, 1] > y0 - 40) & (P[:, 1] < y1 + 40)
        if not m.any():
            continue
        tier = next((t for t in NB_TIERS if t["tag"] == p["tier"]), None)
        if tier is not None:
            r = tier["pitch"] * 0.42
            hgt = tier["hnom"] * 0.85
        elif p["tier"] == "NT":
            r = 1.5; hgt = 4.5
        else:
            r = 0.9; hgt = 1.1
        Q = P[m]
        n_used += len(Q)
        L = hgt * cot
        k = max(1, int(L / (r * 0.8)))
        for q in Q:
            stamp(plan, q[0], q[1], r)
            for j in range(k + 1):
                o = q[:2] + sd * (L * j / k)
                stamp(shad, o[0], o[1], r)
    tot = plan | shad
    return dict(patch=[round(float(v), 1) for v in patch],
                instances=int(n_used),
                sun_elev_deg=C.SUN_ELEV_DEG,
                shadow_ratio=round(cot, 3),
                plan_cover=round(float(plan.mean()), 4),
                plan_plus_shadow_cover=round(float(tot.mean()), 4),
                amplification=round(float(tot.mean() / max(plan.mean(), 1e-9)), 3))


def library_diversity():
    """`tools/item_gate.py`'s geometry-nodes rule, applied to every emission here."""
    rows = []
    ok = True
    for p in _PLACED:
        need = max(8, min(40, int(math.sqrt(max(1, p["n"])))))
        good = (p["sources"] >= need) and (p["top_share"] <= 0.25)
        ok &= good
        rows.append(dict(tier=p["tier"], kind=p["kind"], instances=p["n"],
                         distinct_sources=p["sources"],
                         required=need, top_source_share=round(p["top_share"], 4),
                         pass_=bool(good)))
    return ok, rows


# ==================================================================================
# 10.  SELFTEST.  Every check is shown to REJECT known-bad input.
# ==================================================================================
# THE COMMONEST DEFECT ACROSS 840 LOG ENTRIES IS A BROKEN INSTRUMENT, NOT A BAD
# RENDER.  A check that has never been shown to fail is not a check, so every gate in
# this module is exercised twice: once on input it must accept, once on input it must
# refuse, and the refusal is reported by name.

def selftest(gr=None, gz=None, cam=None, ras=None):
    res = []
    fired = []

    def chk(name, ok, why=""):
        res.append(dict(check=name, ok=bool(ok), why=why))
        return bool(ok)

    def neg(name, refused, why=""):
        res.append(dict(check="NEG " + name, ok=bool(refused), why=why,
                        negative_control=True))
        if refused:
            fired.append(name)
        return bool(refused)

    # ---- 1. THE GATE THIS TIER COMPLEMENTS IS STILL WHERE WE THINK IT IS -------
    # `52.0` and `150.0` are literals inside build_terrain.habitat().  They are
    # re-stated in this module and there is nothing to import, so they are MEASURED
    # off the live function.  If that module's author moves the gate, this fires.
    if gz is None:
        ctx = terrain_context(0.05, ground=False, library=False)
        gr, gz, cam, ras = ctx["gr"], ctx["gz"], ctx["cam"], ctx["ras"]
    rg = np.random.default_rng(11)
    sx = rg.uniform(-900, 900, 60000); sy = rg.uniform(-500, 1100, 60000)
    h = T.habitat(gr, gz, cam, sx, sy, ras)
    nz = h["wood"] > 1e-9
    dmax_zero = float(h["D"][~nz].max()) if (~nz).any() else -1.0
    dmin_nz = float(h["D"][nz].min()) if nz.any() else -1.0
    chk("wood gate lower edge is at D = %.1f m" % WOOD_GATE_D[0],
        abs(dmin_nz - WOOD_GATE_D[0]) < WOOD_GATE_TOL_M + 6.0 and dmin_nz > 0,
        "min D with wood>0 = %.2f m (expected just above %.1f)"
        % (dmin_nz, WOOD_GATE_D[0]))
    chk("wood is EXACTLY zero for every sample with D <= %.1f" % WOOD_GATE_D[0],
        bool((h["wood"][h["D"] <= WOOD_GATE_D[0]] == 0.0).all()),
        "%d samples inside" % int((h["D"] <= WOOD_GATE_D[0]).sum()))
    chk("nb_gate is the exact complement of wood_gate",
        float(np.abs(nb_gate(h["D"]) + wood_gate(h["D"]) - 1.0).max()) < 1e-12,
        "max |nb+wood-1| = %.3e"
        % float(np.abs(nb_gate(h["D"]) + wood_gate(h["D"]) - 1.0).max()))
    # NEGATIVE CONTROL for the drift detector itself: the "wood is exactly zero
    # inside the gate" instrument must FAIL when handed a gate edge that is wrong.
    # If it passed for 80 m as well as for 52 m it would be measuring nothing.
    neg("gate_detector_rejects_a_wrong_gate_edge",
        not bool((h["wood"][h["D"] <= 80.0] == 0.0).all()),
        "the same test asserted at D <= 80 m must FAIL (%d of %d samples in "
        "52-80 m carry wood > 0)"
        % (int((h["wood"][(h["D"] > 52.0) & (h["D"] <= 80.0)] > 0).sum()),
           int(((h["D"] > 52.0) & (h["D"] <= 80.0)).sum())))
    chk("dmax with wood == 0 is not an artefact of an empty sample",
        int((h["D"] <= WOOD_GATE_D[0]).sum()) > 100 and dmax_zero > 0,
        "%d samples inside the gate, dmax_zero %.1f m"
        % (int((h["D"] <= WOOD_GATE_D[0]).sum()), dmax_zero))

    # ---- 2. THE CEILING -------------------------------------------------------
    ff = np.linspace(0.0, 90.0, 4001)
    cc = height_ceiling(ff)
    chk("height_ceiling is monotone non-decreasing",
        bool((np.diff(cc) >= -1e-12).all()))
    chk("height_ceiling is continuous (no step > 0.02 m per 0.0225 m of f)",
        float(np.abs(np.diff(cc)).max()) < 0.02,
        "max step %.5f m" % float(np.abs(np.diff(cc)).max()))
    chk("ceiling at f = 2 m is < 0.6 m (tussock band)",
        float(height_ceiling(2.0)) < 0.6, "%.3f m" % float(height_ceiling(2.0)))
    chk("ceiling at f = 8 m is 0.60-0.65 m",
        0.60 <= float(height_ceiling(8.0)) <= 0.65,
        "%.3f m" % float(height_ceiling(8.0)))
    chk("ceiling at f = 20 m is 2.50 m", abs(float(height_ceiling(20.0)) - 2.5) < 1e-9)
    chk("ceiling at f = 52 m is 16.5 m (birch max)",
        abs(float(height_ceiling(52.0)) - 16.5) < 1e-9)
    # NEGATIVE CONTROL: a scrub taller than the ramp must be REFUSED
    neg("scrub_above_ceiling_refused",
        not bool(test_height_ok(2.40, 5.0)),
        "a 2.40 m scrub offered at f = 5.0 m (ceiling %.3f m) must be refused"
        % float(height_ceiling(5.0)))
    neg("scrub_above_ceiling_refused_at_tier2_floor",
        not bool(test_height_ok(2.50, 8.0)),
        "a 2.50 m gorse at f = 8.0 m (ceiling %.3f m) must be refused"
        % float(height_ceiling(8.0)))
    chk("a 0.45 m tussock at f = 5.0 m is ACCEPTED",
        bool(test_height_ok(0.45, 5.0)))
    chk("a 2.30 m gorse at f = 19.0 m is ACCEPTED (ceiling %.3f m)"
        % float(height_ceiling(19.0)),
        bool(test_height_ok(2.30, 19.0)))

    # ---- 3. THE SPECIES GATE --------------------------------------------------
    neg("tall_species_refused_in_the_band",
        not test_species_fits("oak", 25.0),
        "oak (h_min %.1f m) at f = 25 m, ceiling %.2f m"
        % (T.SPECIES["oak"]["h"][0], float(height_ceiling(25.0))))
    neg("poplar_refused_at_f40",
        not test_species_fits("poplar", 40.0),
        "poplar (h_min %.1f m) at f = 40 m, ceiling %.2f m"
        % (T.SPECIES["poplar"]["h"][0], float(height_ceiling(40.0))))
    chk("hawthorn (h_min 2.8 m) is ACCEPTED at f = 25 m",
        test_species_fits("hawthorn", 25.0))
    neg("hawthorn_refused_at_f21",
        not test_species_fits("hawthorn", 20.5),
        "hawthorn h_min 2.8 m against a %.2f m ceiling at f = 20.5 m"
        % float(height_ceiling(20.5)))
    chk("rowan only becomes legal beyond f = 30 m",
        (not test_species_fits("rowan", 28.0)) and test_species_fits("rowan", 33.0))

    # ---- 4. THE CORRIDOR ------------------------------------------------------
    # NEGATIVE CONTROL: a candidate on the racing line must be REFUSED.
    s = np.linspace(0.0, C.LAP, 400)[:-1]
    cxx, cyy, _, _ = C.centreline_arrays(s)
    ref = test_outside_corridor(cxx, cyy, 0.0)
    neg("centreline_candidates_refused",
        not bool(ref.any()),
        "%d of %d points ON the centreline passed outside_corridor"
        % (int(ref.sum()), len(cxx)))
    # ... and one just inside the rim.  The rim comes from `C.platform_edge(s, +1)`
    # DIRECTLY and not from `corridor_fz`'s `lim`: at u = 0 the sign of u is a coin
    # flip, and `lim` then returns the RIGHT rim (up to 87.9 m at T10) for a point
    # being offset to the LEFT -- which lands 76 m outside the corridor and makes the
    # control pass for the wrong reason.  (It did.  That is why this comment exists.)
    hd = C.centreline_arrays(s[:40])[2]
    lim = C.platform_edge(s[:40], +1)
    inx = cxx[:40] - np.sin(hd) * (lim - 1.0)
    iny = cyy[:40] + np.cos(hd) * (lim - 1.0)
    ref2 = test_outside_corridor(inx, iny, 0.0)
    neg("inside_rim_candidates_refused",
        not bool(ref2.any()),
        "%d of 40 points 1.0 m INSIDE the left rim passed" % int(ref2.sum()))
    outx = cxx[:40] - np.sin(hd) * (lim + 12.0)
    outy = cyy[:40] + np.cos(hd) * (lim + 12.0)
    chk("points 12 m OUTBOARD of the rim are accepted",
        bool(test_outside_corridor(outx, outy, 2.0).mean() > 0.9),
        "%.2f accepted" % float(test_outside_corridor(outx, outy, 2.0).mean()))

    # ---- 5. THE PAVING AND THE TRANSIT ROUTE ----------------------------------
    f = C.FORECOURT_WORLD
    neg("candidate_on_the_forecourt_refused",
        not bool(test_off_paving(np.array([f["cx"]]), np.array([f["cy"]]),
                                 NB_PAVE_STANDOFF_M)[0]),
        "the middle of the declared forecourt must not be plantable")
    # t = 20 m is on the STRAIGHT run out of the glass, heading +x, so the
    # perpendicular really is y and the boundary can be probed on both sides of it.
    px, py, _ = C.access_route_arrays(np.array([20.0]))
    neg("candidate_on_the_transit_route_refused",
        not bool(test_transit_clear(px, py)[0]),
        "a point ON the beat-3/4 route centreline (t = 20 m) must be refused")
    neg("candidate_inside_the_transit_clearance_refused",
        not bool(test_transit_clear(px, py - (NB_TRANSIT_CLEAR_M - 2.0))[0]),
        "%.1f m off the route, inside the %.1f m clearance"
        % (NB_TRANSIT_CLEAR_M - 2.0, NB_TRANSIT_CLEAR_M))
    chk("a point %.1f m off the transit route is accepted"
        % (NB_TRANSIT_CLEAR_M + 4),
        bool(test_transit_clear(px, py - (NB_TRANSIT_CLEAR_M + 4.0))[0]))
    neg("candidate_inside_the_forecourt_box_refused",
        not bool(test_forecourt_clear(np.array([f["cx"] + 5.0]),
                                      np.array([f["cy"]]))[0]))

    # ---- 6. THE DENSITY FIELD -------------------------------------------------
    hh = dict(D=np.array([0.0, 30.0, 52.0, 101.0, 150.0, 300.0]),
              f=np.full(6, 30.0), plateau=np.zeros(6), ez=np.zeros(6),
              built=np.zeros(6), slope=np.full(6, 0.05),
              cx=np.zeros(6), cy=np.zeros(6))
    d = nb_density(hh)
    chk("near-band density is > 0 where wood is exactly 0 (D <= 52 m)",
        bool((d[:3] > 0.05).all()), "%s" % np.round(d[:3], 3).tolist())
    neg("nearband_refuses_the_far_field",
        float(d[5]) == 0.0,
        "density at D = 300 m must be exactly 0 (the complement has closed); got %.6f"
        % float(d[5]))
    neg("nearband_refuses_the_rim",
        float(nb_density(dict(hh, f=np.full(6, 1.0)))[1]) == 0.0,
        "density at f = 1.0 m (inboard of NB_F0 = %.1f) must be exactly 0" % NB_F0)
    ws = sum(tier_weight(t, np.linspace(0, 80, 801)) for t in NB_TIERS)
    chk("the three f-tier weights sum to 1 everywhere",
        float(np.abs(ws - 1.0).max()) < 1e-9,
        "max |sum-1| = %.3e" % float(np.abs(ws - 1.0).max()))

    # ---- 7. THE LIBRARY DIVERSITY INSTRUMENT ----------------------------------
    # NEGATIVE CONTROL: the check that catches "one mesh spammed a hundred times"
    # must itself be shown to catch it.
    save = list(_PLACED)
    try:
        _PLACED[:] = [dict(tier="X", kind="one_mesh_spammed", n=5000, stems=5000,
                           tris=0, sources=1, top_share=1.0,
                           P=np.zeros((0, 3)))]
        bad_ok, rows = library_diversity()
        neg("one_mesh_spammed_refused", not bad_ok,
            "a 5 000-instance emission from 1 source mesh must fail "
            "(required %d sources)" % rows[0]["required"])
        _PLACED[:] = [dict(tier="X", kind="diverse", n=5000, stems=5000, tris=0,
                           sources=44, top_share=1 / 44.0, P=np.zeros((0, 3)))]
        good_ok, rows = library_diversity()
        chk("a 5 000-instance emission from 44 source meshes passes", good_ok)
    finally:
        _PLACED[:] = save

    # ---- 8. THE MESH MERGE ----------------------------------------------------
    me_a, ha = T.gen_shrub("gorse", np.random.default_rng(1), 1)
    me_b, hb = T.gen_weed("dock", np.random.default_rng(2))
    ta, tb = _tris(me_a), _tris(me_b)
    na, nb_ = len(me_a.vertices), len(me_b.vertices)
    mg, hm, hh2 = merge_parts(T.VPFX + NAME + "selftest_merge",
                              [(me_a, np.zeros(3), (1, 1, 1), 0.0),
                               (me_b, np.array([1.0, 0.0, 0.0]), (1, 1, 1), 0.3)])
    chk("merge_parts conserves triangles", _tris(mg) == ta + tb,
        "%d + %d -> %d" % (ta, tb, _tris(mg)))
    chk("merge_parts conserves vertices", len(mg.vertices) == na + nb_,
        "%d + %d -> %d" % (na, nb_, len(mg.vertices)))
    chk("merge_parts unions the material slots by name",
        len(mg.materials) == 5, "%s" % [m.name for m in mg.materials])
    chk("merge_parts keeps the pid/pgrad attributes",
        ("pid" in mg.attributes) and ("pgrad" in mg.attributes))
    V = np.empty(len(mg.vertices) * 3, np.float32)
    mg.vertices.foreach_get("co", V)
    chk("merge_parts applies the part offset",
        abs(float(V.reshape(-1, 3)[na:, 0].mean()) - 1.0) < 0.6,
        "second part mean x = %.3f, offset was 1.0"
        % float(V.reshape(-1, 3)[na:, 0].mean()))
    try:
        bpy.data.meshes.remove(mg)
    except Exception:
        pass

    # ---- 8b. THE CLUMP IS THE SIZE IT SAYS IT IS ------------------------------
    # This is the check that would have caught the sizing defect this module shipped
    # with for one afternoon: the parts were scaled by their generators' own habit
    # heights, so an N1 clump whose weed happened to be a 1.15 m dock declared 1.15 m
    # and was then scaled to 0.62/1.15 by `gn_kind` -- a clump whose placed size was a
    # function of which weed the dice drew.  The ceiling was never violated, which is
    # exactly why nothing else would have caught it.
    for tier in NB_TIERS:
        me, h0, stems = gen_nb_clump(np.random.default_rng(int(ord(tier["tag"][-1]))),
                                     tier)
        hn = tier["hnom"]
        chk("%s clump declares a height within 35 %% of hnom" % tier["tag"],
            0.65 * hn <= h0 <= 1.35 * hn,
            "declared %.3f m against hnom %.3f m" % (h0, hn))
        chk("%s clump carries at least one woody stem" % tier["tag"], stems >= 1,
            "%d stems" % stems)
        # hnom must fit the ceiling where the tier carries full weight ...
        f_lo, f_hi = {"N1": (2.0, 8.0), "N2": (8.0, 20.0),
                      "N3": (20.0, 52.0)}[tier["tag"]]
        chk("%s hnom fits the ceiling at the top of its band (f = %.0f m)"
            % (tier["tag"], f_hi), bool(test_height_ok(hn, f_hi)),
            "hnom %.2f m against ceiling %.2f m" % (hn, float(height_ceiling(f_hi))))
        # ... and where it does not, THE CLIP MUST BITE, not the emission be dropped
        chk("%s hnom is CLIPPED (not refused) at the bottom of its band (f = %.0f m)"
            % (tier["tag"], f_lo),
            abs(float(clip_height(hn, f_lo)) - float(height_ceiling(f_lo))) < 1e-9
            or hn <= float(height_ceiling(f_lo)),
            "clip(%.2f, f=%.0f) = %.3f, ceiling %.3f"
            % (hn, f_lo, float(clip_height(hn, f_lo)), float(height_ceiling(f_lo))))
        try:
            bpy.data.meshes.remove(me)
        except Exception:
            pass

    # ---- 8c. THE AMENITY LIBRARY IS UNIT-HEIGHT AND TRUE-LENGTH ---------------
    # `nb_gn` normalises by the declared height, so a hedge segment that declares
    # anything but 1.0 has its LENGTH divided by that number too -- and a run laid at
    # AM_HEDGE_PITCH then gaps or piles up according to how tall the segment happened
    # to be drawn.  These two checks are the whole contract between `gen_nb_hedge` and
    # the placement scale.
    mat_nb_clipped()                       # the hedge picks it up by name
    hme, hh = gen_nb_hedge(np.random.default_rng(4))
    HV = np.empty(len(hme.vertices) * 3, np.float32)
    hme.vertices.foreach_get("co", HV)
    HP = HV.reshape(-1, 3)
    chk("hedge segment declares unit height", abs(hh - 1.0) < 1e-9, "%.4f" % hh)
    chk("hedge segment IS unit height", abs(float(HP[:, 2].max()) - 1.0) < 0.02,
        "top %.4f" % float(HP[:, 2].max()))
    chk("hedge segment keeps its drawn length (%.2f m)" % AM_HEDGE_LEN,
        abs(float(HP[:, 0].max() - HP[:, 0].min()) - AM_HEDGE_LEN) < 0.55,
        "length %.3f m" % float(HP[:, 0].max() - HP[:, 0].min()))
    chk("hedge segment is thinner than it is long",
        float(HP[:, 1].max() - HP[:, 1].min()) < AM_HEDGE_W[1] + 0.05,
        "width %.3f m against W max %.2f"
        % (float(HP[:, 1].max() - HP[:, 1].min()), AM_HEDGE_W[1]))
    chk("hedge segment carries the clipped material",
        any(m is not None and m.name == T.VPFX + NAME + "clipped"
            for m in hme.materials),
        "%s" % [m.name for m in hme.materials if m])
    pme, ph = gen_nb_planter(np.random.default_rng(4))
    chk("planter declares unit height", abs(ph - 1.0) < 1e-9, "%.4f" % ph)
    for m in (hme, pme):
        try:
            bpy.data.meshes.remove(m)
        except Exception:
            pass

    # ---- 9. THE MATERIAL LAWS -------------------------------------------------
    mi = mat_nb_clipped()
    chk("the clipped material's detail comes from K.detail_for",
        abs(mi["detail"] - K.detail_for(NB_HEDGE_LAM_M, **NB_HEDGE_SHOT)) < 1e-9,
        "detail = %.1f at lam %.3f m" % (mi["detail"], mi["wavelength_m"]))
    chk("no octave is emitted below the resolvable floor",
        not K.finest_octave_for(NB_HEDGE_LAM_M, mi["detail"],
                                **NB_HEDGE_SHOT)["below_floor"],
        "finest %.2f mm" % mi["finest_octave_mm"])
    neg("house_default_detail_8_would_be_refused",
        K.finest_octave_for(NB_HEDGE_LAM_M, 8.0, **NB_HEDGE_SHOT)["below_floor"],
        "detail=8 at lam %.3f m emits %.3f mm, below the floor -- %d wasted octaves"
        % (NB_HEDGE_LAM_M,
           K.finest_octave_for(NB_HEDGE_LAM_M, 8.0, **NB_HEDGE_SHOT)["finest_mm"],
           K.finest_octave_for(NB_HEDGE_LAM_M, 8.0,
                               **NB_HEDGE_SHOT)["wasted_octaves"]))
    m = bpy.data.materials[mi["material"]]
    p = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    chk("Principled BSDF.Normal is fed BY NAME and is connected",
        p.inputs["Normal"].is_linked,
        "Blender 5.2 moved it from socket 5 to 6")

    # ---- 10. NO EXTERNAL ASSETS ----------------------------------------------
    imgs = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    chk("no external image assets", not imgs, "%s" % imgs)

    npass = sum(1 for r in res if r["ok"])
    ok = npass == len(res)
    return dict(ok=ok, passed=npass, total=len(res),
                negative_controls_fired=fired, checks=res)


# ==================================================================================
# 11.  MAIN
# ==================================================================================

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    q = QUAL
    if "--quality" in argv:
        q = float(argv[argv.index("--quality") + 1])
    out = {"quality": q}

    if "--selftest" in argv and "--full" not in argv and "--terrain-only" not in argv:
        T.purge()
        st = selftest()
        out["selftest"] = st
        stage("nearband_selftest", st["ok"], passed=st["passed"], total=st["total"],
              negative_controls_fired=len(st["negative_controls_fired"]),
              fired=st["negative_controls_fired"],
              failed=[c["check"] for c in st["checks"] if not c["ok"]])
        _dump(out, argv)
        return

    if "--measure" in argv:
        # RE-MEASURE A BUILT BLEND.  The build is 20 minutes and the measurement is
        # two; a defect in the instrument must not cost the build again.  Only
        # Ground / CameraPath / Raster are rebuilt (off `_probe_gz`, not off the
        # ground mesh, which is already in the file) -- none of them is used to place
        # anything here, only to bin what is already placed.
        p = argv[argv.index("--measure") + 1]
        bpy.ops.wm.open_mainfile(filepath=p)
        log("measuring %s" % p)
        spec = json.load(open(T.SPEC_JSON)); beats = json.load(open(T.BEAT_JSON))
        cir = T.Circuit(spec); gr = T.Ground(cir)
        gz = T._probe_gz(gr, -1000, 900, -560, 1290, 20.0)
        cam = T.CameraPath(cir, beats)
        X0, X1, Y0, Y1 = -1520.0, 1440.0, -1120.0, 1840.0
        ras = T.Raster(gr, cam, X0 - 40, X1 + 40, Y0 - 40, Y1 + 40, 14.0, gz=gz)
        ctx = dict(gr=gr, gz=gz, cam=cam, ras=ras, dom=(X0, X1, Y0, Y1))
        _report_density(ctx, out)
        _dump(out, argv)
        return

    ctx = None
    if "--full" in argv:
        log("full build_terrain.build() first, so the no-cliff evidence is measured "
            "against the REAL woodland tier and not against a model of it")
        t0 = time.time()
        with capture_terrain() as cap:
            tstats = T.build(quality=q)
        out["terrain"] = tstats
        stage("terrain_build", tstats.get("evaluated_tris", 0) > 0,
              build_s=round(time.time() - t0, 1),
              objects=tstats.get("objects"),
              unique_meshes=tstats.get("unique_meshes"),
              base_library_tris=tstats.get("base_library_tris"),
              evaluated_tris=tstats.get("evaluated_tris"),
              woodland_trees=tstats.get("woodland_trees"),
              shrubs=tstats.get("shrubs"))
        missing = [n for n in capture_terrain.NAMES if n not in cap.got]
        if missing:
            stage("terrain_context_captured", False, missing=missing)
            _dump(out, argv)
            return
        stage("terrain_context_captured", True, captured=sorted(cap.got))
        ctx = dict(gr=cap.got["Ground"], gz=cap.got["GridZ"],
                   cam=cap.got["CameraPath"], ras=cap.got["Raster"],
                   lib=cap.got["build_library"],
                   rng=np.random.default_rng(SEED),
                   root=bpy.data.collections.get(T.COLL),
                   dom=(-1520.0, 1440.0, -1120.0, 1840.0))
    elif "--terrain-only" in argv:
        T.purge()
        ctx = terrain_context(q)

    st = build(ctx=ctx, quality=q)
    ctx = _CTX
    out["nearband"] = st
    stage("nearband_build", st["nb_instances"] > 0,
          instances=st["nb_instances"], woody_stems=st["nb_woody_stems"],
          base_library_tris=st["nb_base_library_tris"],
          instanced_tris=st["nb_instanced_tris"],
          build_s=st["nb_build_s"])

    # SAVE BEFORE MEASURING.  The build is 20-40 minutes and the measurement is two;
    # losing the first to a defect in the second is a bad trade, and the .blend is
    # what `tools/instance_variety.py` needs anyway.
    if "--save" in argv:
        p = argv[argv.index("--save") + 1]
        bpy.ops.wm.save_as_mainfile(filepath=p)
        stage("nearband_saved", os.path.exists(p), path=p,
              mb=round(os.path.getsize(p) / 1e6, 1) if os.path.exists(p) else 0)

    div_ok, div = library_diversity()
    out["library_diversity"] = div
    stage("nearband_instance_diversity", div_ok,
          emissions=len(div), failed=[r["kind"] for r in div if not r["pass_"]])

    _report_density(ctx, out)

    sc = shadow_cover()
    out["shadow_cover"] = sc
    if sc:
        stage("nearband_shadow_cover", sc["plan_plus_shadow_cover"] > sc["plan_cover"],
              **sc)

    if "--selftest" in argv:
        stt = selftest(ctx["gr"], ctx["gz"], ctx["cam"], ctx["ras"])
        out["selftest"] = stt
        stage("nearband_selftest", stt["ok"], passed=stt["passed"],
              total=stt["total"],
              negative_controls_fired=len(stt["negative_controls_fired"]),
              fired=stt["negative_controls_fired"],
              failed=[c["check"] for c in stt["checks"] if not c["ok"]])

    _dump(out, argv)


def _report_density(ctx, out):
    ev = density_vs_D(ctx)
    out["density_vs_D"] = ev
    no_cliff = (ev["cover_max_step_20_200m_after"] <= 0.55
                and ev["cover_zero_bins_after"] == 0
                and (ev["cover_step_at_52m_after"] or 0.0) <= 0.35
                and ev["cover_max_step_20_200m_after"]
                <= ev["cover_max_step_20_200m_before"] + 1e-9)
    stage("nearband_no_cliff", no_cliff,
          cover_step_at_52m_before=ev["cover_step_at_52m_before"],
          cover_step_at_52m_after=ev["cover_step_at_52m_after"],
          cover_step_at_150m_before=ev["cover_step_at_150m_before"],
          cover_step_at_150m_after=ev["cover_step_at_150m_after"],
          cover_max_step_before=ev["cover_max_step_20_200m_before"],
          cover_max_step_before_at_m=ev["cover_max_step_before_at_m"],
          cover_max_step_after=ev["cover_max_step_20_200m_after"],
          cover_max_step_after_at_m=ev["cover_max_step_after_at_m"],
          cover_zero_bins_before=ev["cover_zero_bins_before"],
          cover_zero_bins_after=ev["cover_zero_bins_after"],
          mean_cover_0_52_before=ev["mean_cover_0_52_before"],
          mean_cover_0_52_after=ev["mean_cover_0_52_after"],
          mean_cover_150_300=ev["mean_cover_150_300"],
          count_max_step_after=ev["max_step_20_200m_after"],
          count_max_step_after_at_m=ev["max_step_20_200m_after_at_m"],
          built_district=ev["built_district"])
    print("  OPEN COUNTRY (built < %.2f)                                    "
          "  |  BUILT DISTRICT" % BUILT_SPLIT, flush=True)
    print("D bin      area ha  wood/ha    nb/ha  total/ha   cover_b  cover_a "
          "|  area ha  wood/ha    nb/ha", flush=True)
    for r in ev["table"]:
        print("  %4.0f-%4.0f %8.3f %8.2f %8.2f %9.2f %9.3f %8.3f | %8.3f %8.2f %8.2f"
              % (r["d0"], r["d1"], r["area_ha"], r["woodland_per_ha"],
                 r["nearband_per_ha"], r["total_per_ha"],
                 r["woody_cover_before"], r["woody_cover_after"],
                 r["built_area_ha"], r["built_woodland_per_ha"],
                 r["built_nearband_per_ha"]), flush=True)
    return ev


def _dump(out, argv):
    if "--stats" in argv:
        p = argv[argv.index("--stats") + 1]
        json.dump(out, open(p, "w"), indent=1, default=float)
        log("stats -> %s" % p)
    print(json.dumps({k: v for k, v in out.items() if k != "selftest"},
                     indent=1, default=float)[:6000], flush=True)


if __name__ == "__main__":
    main()
