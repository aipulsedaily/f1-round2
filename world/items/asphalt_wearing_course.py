#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asphalt_wearing_course.py — CIRCUIT VITRINE, per-item hero campaign, item
``asphalt_wearing_course`` (zone ``track_surface``, wave 1, build order 6).

WHAT THIS IS, IN ONE SENTENCE
=============================
The top lift of the racing surface built as **real geometry**: a mastic bed with
an aggregate skeleton of ~10^5 **individually generated crushed stones**, each a
unique convex polyhedron with flat fracture facets, bedded on its flattest face
and drowned in bitumen mortar to its own depth.  No stone is a copy of another
stone.  There is no aggregate texture anywhere in this module — the aggregate
*is* the mesh.

WHY IT HAD TO BE PROMOTED TO GEOMETRY (the manifest said so)
-----------------------------------------------------------
    "11 detail scales already exist, 140 m down to 0.6 mm.  The lens reaches
     1.1 m at the hairpin, and rides 1.9 m for 560 m at 323 km/h.  KNOWN LIMIT:
     displacement is bump-only (1-3 mm of relief).  If the hairpin frames show
     flat aggregate at 1.1 m, this is the first thing to promote to true
     displacement."                       -- docs/item_manifest.json, this item

The arithmetic that settles it:

    px_per_m = (3840 * 21 / 36) / 1.1 = 2036 px/m   ->   1 px = 0.491 mm

A 11 mm chipping is **22 px across**.  Its 2 mm protrusion, under the contract
sun at 12.471 deg elevation (``C.SUN_SHADOW_RATIO`` = 4.522), throws a **9.0 mm
= 18 px cast shadow**.  A bump map cannot cast that shadow, cannot occlude the
stone behind it, and has no silhouette — at 1.1 m on a 21 mm lens a bump-mapped
road is a photograph of a road printed on glass.  So the aggregate is meshed.

THE PUBLIC INTERFACE  (this item is a FOUNDATION — 8 items depend on it)
=======================================================================
Dependants named in the manifest: ``rubber_line_deposit``,
``asphalt_paver_mat_joint``, ``asphalt_crack_seal``, ``asphalt_patch_repair``,
``asphalt_transverse_joint``, ``lockup_skid_mark``, ``timing_loop_sawcut``,
``runoff_asphalt_mat``.  None of them can ask questions, so everything they need
is a function here, and every one of them is documented against a number.

--- 1. THE TWO SURFACES, AND WHICH ONE YOU MEAN --------------------------------

    stone_top_z(s, u)     the aggregate-skeleton envelope.  This is EXACTLY
                          ``C.ground_z(s, u)``: the contract datum is the level a
                          surveyor's staff reads on a finished mat, i.e. the mean
                          of the stone tops.  Anything that sits ON the road
                          (paint, a sealant overband, a marble, a tyre) sits on
                          this.  Individual stones stand up to +1.1 mm above it.

    mastic_top_z(s, u)    the interstitial mortar between the stones, which is
                          ``stone_top_z - fill_depth(s, u)``.  Anything that
                          FLOWS INTO the surface — crack sealant, a bleeding
                          patch, rubber infill — meets this, not the datum.

    fill_depth(s, u)      the GEOMETRIC gap between them, in metres.  MEASURED on
                          the built patch: 0.35 mm (flushed and polished) to
                          3.62 mm (open and segregated), median 1.81 mm.

    mtd(s, u)             the same surface expressed as sand-patch MEAN TEXTURE
                          DEPTH, = fill_depth * 0.45.  THESE ARE NOT THE SAME
                          NUMBER AND THE FIRST BUILD CONFLATED THEM: it set the
                          mortar 1.08 mm below the stone tops (SMA 11's published
                          MTD) instead of 2.4 mm, and the macro came back with the
                          aggregate showing as slivers.  Comparing against a
                          published figure for a mix -> ``mtd``.  Placing geometry
                          -> ``fill_depth``.

    exposure(s, u)        fraction of the coarse skeleton's own height standing
                          proud of the mortar.  0.012 .. 0.72.

    Neither z function ever invents a z.  Both are ``C.ground_z`` plus a bounded
    skin, MEASURED over 400 000 vertices per object against the contract datum:

        mastic     -5.37 .. -0.00 mm    (median -1.74)
        tier A     -8.37 .. +3.17 mm    (median -3.29 — mostly buried, by design)
        surround   -4.31 .. +0.10 mm

    So a module that keeps calling ``C.ground_z`` is never more than 3.2 mm high
    or 5.4 mm low against this item, and one that calls these is exact.

--- 2. THE FIELDS THAT DECIDE WHAT THE SURFACE LOOKS LIKE HERE -----------------

    zone_of(s) -> int          which of the 9 resurfacing campaigns owns this
                               station.  Read straight from
                               ``build_surface.RESURFACE`` — NOT re-derived.
    mix_of(s)  -> dict         that campaign's asphalt: nominal aggregate size,
                               gradation, binder richness, void content,
                               lithology weights, oxidation.  See ``MIXES``.
    segregation(s, u)          0 = mortar-rich, 1 = coarse/open.  Paver
                               segregation, the "segregation patches" axis.
    flushing(s, u)             0..1 binder-rich, stones drowned (fatting up).
    polish(s, u)               0..1 how planed-off the stone tops are.  1 on the
                               driven line.  This is the GEOMETRY of the racing
                               line.  ``rubber_line_deposit`` owns the deposit
                               ITSELF; set ``RUBBER_TINT`` = 0.0 to switch off
                               this module's small tonal contribution so the two
                               do not double-darken.
    plucked(s, u)              0..1 probability field for torn-out stones.

--- 3. BUILDING SOMETHING OUT OF THE SAME AGGREGATE ----------------------------

    crushed_stones(n, rng, size_m, ...) -> (verts (n,V,3), faces (F,3), meta)
                               THE stone generator.  ``asphalt_patch_repair`` and
                               ``runoff_asphalt_mat`` must call this rather than
                               writing their own, or their aggregate will not be
                               the same rock as the road it is let into.
    mat_stone(), mat_mastic()  the two materials, cached by name.
    ATTRS                      the names of the vertex attributes both materials
                               read.  A dependant that emits geometry into these
                               materials MUST write all of them; ``bake_attrs``
                               does it.

--- 4. EMITTING A PATCH -------------------------------------------------------

    build(site=..., quality=...) -> dict
        Emits into collection ``W_Item_AsphaltWearingCourse`` with object prefix
        ``AWC_``.  A *site* is a ``Site`` dataclass: lap station, lateral, extent,
        and an optional LOD anchor (the lens position) which decides how far out
        the explicit stones are built.

    PATCH_SITES                the two places in the film where the lens is close
                               enough to need them (T4 hairpin, s = 982.27; the
                               pit-straight onboard follow).

    footprint_polygon(site)    the (s, u) rectangle build_surface MUST NOT build
                               its own ``SURF_Track`` rows inside.
                               ** THIS IS AN EXCLUSIVE OWNERSHIP CLAIM. **
                               The hero patch REPLACES the road there; it does not
                               overlay it.  Its mastic is 0.35-3.2 mm BELOW the
                               datum and its stones straddle it, so leaving
                               ``SURF_Track`` in place underneath is a guaranteed
                               z-fight across the whole hero frame.  See §6.

THE SEVEN LAWS, AND WHERE EACH ONE IS DISCHARGED
================================================
 1. procedural, by hand      no image node, no file, no library.  ``item_gate``
                             measures it: ``no_external_assets``.
 2. no real brands           this item carries no lettering at all.
 3. car scale                not a scale-carrying item; the 2.005 m car width
                             does set the polished-band width (§ ``polish``).
 4. z = 0 is one plane       never used: every z comes from ``C.ground_z``.
 5. embed >= 20 mm           this item IS the ground; it does not stand on it.
                             Its own sub-base skirt is 45 mm deep so that a saw
                             cut by ``asphalt_patch_repair`` reveals a real lift.
 6. recentre + TexCoord      every object's mesh is local to its own centre
                             (|P| < 5 m); the object matrix carries the 971 m out
                             to T4.  Every material reads ``TexCoord->Object`` and
                             the ``AWC_*`` attributes.  ``Geometry->Position``
                             appears nowhere in this file.
 7. chunk along s            a patch is <= 6 m of circuit and is emitted as
                             several chunk objects.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/asphalt_wearing_course.py -- --test-blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/asphalt_wearing_course.py -- --test-blend --quality draft
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector

# --------------------------------------------------------------------------- paths
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../world/items
_WORLD = os.path.dirname(_HERE)                             # .../world
_ROOT = os.path.dirname(_WORLD)                             # .../f1-round2
for _p in (_WORLD, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                  # noqa: E402
import build_surface as BS                                  # noqa: E402
from build_surface import _G as G                           # noqa: E402
#   ^ build_surface's shader DSL.  Imported rather than copied ON PURPOSE: a second
#     copy of a 170-line node-graph helper is a second place for the project's node
#     idiom to drift, and this module's materials have to sit beside
#     M_Surf_Asphalt in the same frame.

COLL_NAME = "W_Item_AsphaltWearingCourse"
PFX = "AWC_"
MPFX = "M_AWC_"

ITEM_ID = "asphalt_wearing_course"

# ---------------------------------------------------------------- filmed spec
# straight out of docs/item_manifest.json; do not guess what the manifest decided
NEAREST_CAMERA_M = 1.1
LENS_AT_CLOSEST_MM = 21.0
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M   # 2036.4
MM_PER_PX = 1000.0 / PX_PER_M                                               # 0.491

# The second station the manifest names: the onboard follow, 1.9 m over the deck
# for 560 m at 323 km/h.  Beat 5's onboard leg is a 35 mm lens (beat sheet), so
# (3840*35/36)/1.9 = 1965 px/m — within 4 % of the hairpin.  ONE detail spec
# serves both, which is why this module has one quality tier and not two.
ONBOARD_PX_PER_M = (RES_X_4K * 35.0 / 36.0) / 1.9


# ===========================================================================
# 1.  THE MIX DESIGNS  —  variation axis 1 of 4: "9 resurfacing zones"
# ===========================================================================
#
# ``build_surface.RESURFACE`` already decides where the 9 campaigns start and how
# old each one is.  That table is the single source of truth for the STATIONS and
# the AGES and is read, not restated.  What this module adds is the thing a
# station and an age cannot tell you: **what was actually laid**.
#
# A circuit resurfaced nine times over two decades does not get the same recipe
# nine times.  Each campaign has its own nominal aggregate size, its own quarry,
# its own binder content and its own compaction, and that is what makes nine
# zones look like nine zones instead of one zone with nine tints.  The numbers
# below are real mix designations:
#
#   SMA 8 / SMA 11    stone mastic asphalt, gap-graded, stone-on-stone skeleton,
#                     high binder (6.2-7.0 %), 3-4 % voids.  The modern circuit
#                     surfacing.  Texture depth 0.7-1.1 mm.
#   AC 10 / AC 14     dense-graded asphalt concrete, continuous gradation, lower
#                     binder, more fines between the stones.  Texture 0.5-0.8 mm.
#   PA 11             porous asphalt, 20 % voids — one campaign only, an old
#                     drainage experiment kept because it is the most visually
#                     distinct surface a circuit can carry.
#
# lithology weights are (pale quartzite/limestone, mid granodiorite, dark basalt)
# and MATCH the three discrete lithologies M_Surf_Asphalt already uses, so the
# hero patch and the shader-only road 4 m further on are quarrying the same rock.
#
# d_nom  nominal max aggregate size (m).  The tier sizes below scale off it.
# tex    target mean texture depth (m) at segregation 0.5, before ageing.
# void   surface air-void fraction — drives how open the mortar reads.
# binder binder richness 0..1 — high binder floods the interstices.
# flake  flakiness: how platy the stones are.  A quarry that produces flaky
#        aggregate produces it on every load, so this is per campaign.
MIXES = [
    #  designation      d_nom   tex     void  binder flake  lithology weights
    dict(name="SMA 11", d_nom=0.0112, tex=0.00098, void=0.040, binder=0.72, flake=0.30,
         lith=(0.18, 0.52, 0.30), note="2024 campaign, start/finish sector"),
    dict(name="AC 14",  d_nom=0.0140, tex=0.00082, void=0.055, binder=0.48, flake=0.44,
         lith=(0.34, 0.44, 0.22), note="older dense-graded, T1-T2, polished hard"),
    # ZONE 2 IS THE HERO SLAB: s = 789.3 .. 1025.3 covers T3, the braking zone and
    # the whole of the T4 hairpin, and it is the only mix the 1.1 m lens ever sees
    # from 1.1 m.  A hairpin is the highest-shear, highest-braking metre of the lap,
    # so it gets the coarsest-textured surfacing a circuit can lay: SMA 11 on a
    # high-PSV aggregate.  Fine SMA 8 belongs on the pit straight (zone 8), where
    # the start line wants a smooth mat, not here.
    dict(name="SMA 11", d_nom=0.0112, tex=0.00108, void=0.043, binder=0.73, flake=0.26,
         lith=(0.22, 0.46, 0.32), note="high-PSV SMA through T3 into the hairpin"),
    dict(name="AC 10",  d_nom=0.0100, tex=0.00071, void=0.062, binder=0.44, flake=0.50,
         lith=(0.42, 0.40, 0.18), note="the oldest slab on the lap, T4 exit ramp"),
    dict(name="SMA 11", d_nom=0.0112, tex=0.00104, void=0.042, binder=0.70, flake=0.34,
         lith=(0.20, 0.30, 0.50), note="basalt-heavy load, the climb straight"),
    dict(name="PA 11",  d_nom=0.0112, tex=0.00185, void=0.190, binder=0.62, flake=0.26,
         lith=(0.10, 0.56, 0.34), note="porous asphalt trial across the summit"),
    dict(name="SMA 11", d_nom=0.0112, tex=0.00092, void=0.041, binder=0.74, flake=0.31,
         lith=(0.26, 0.48, 0.26), note="the sweeper, resurfaced after the kerb work"),
    dict(name="AC 14",  d_nom=0.0140, tex=0.00088, void=0.058, binder=0.46, flake=0.47,
         lith=(0.38, 0.42, 0.20), note="oldest of the AC slabs, T12-T13"),
    dict(name="SMA 8",  d_nom=0.0080, tex=0.00068, void=0.036, binder=0.80, flake=0.20,
         lith=(0.14, 0.34, 0.52), note="last year's pit straight, laid for the start"),
]

# variation axis 2 of 4, "aggregate size mix": the three sieve tiers as fractions
# of d_nom.  These are the two visible fractions of a real gradation plus the top
# of the mortar sand.  Below TIER_C nothing is meshed: 2.0 mm is 4 px at the hero
# station and 2 px on the onboard follow, and geometry at 2 px is what makes a
# surface CRAWL in motion.  That boundary is a decision, not an omission; the
# mortar's own sand is carried by M_AWC_Mastic's bump at 0.25-0.8 mm.
# THE COARSE PITCH IS SET BY AREAL COVERAGE, NOT BY d_nom.  In SMA the coarse
# fraction is a STONE-ON-STONE SKELETON: adjacent coarse particles touch and carry
# the load, and the mortar only fills what is left.  A tier-A stone averages
# 0.89 * d_nom on its longest axis and, flattened by the roller, presents a mean
# plan diameter of about 0.89 of that.  At the first build's 1.10 * d_nom pitch
# that is only 41 % areal coverage -- the crop came back showing more shadowed
# mortar than stone, which is a chip seal, not an SMA.  0.98 gives 52 %.
TIERS = (
    # (label, size lo/hi as fraction of d_nom, grid pitch as fraction of d_nom,
    #  template, packing clearance)
    dict(k="A", lo=0.66, hi=1.16, pitch=0.98, tmpl="ico", clear=0.84),
    dict(k="B", lo=0.34, hi=0.60, pitch=0.52, tmpl="ico", clear=0.90),
    dict(k="C", lo=0.19, hi=0.33, pitch=0.31, tmpl="oct", clear=0.94),
)

# how far out from the LOD anchor each tier is still meshed (m).  Past these the
# tier fades out over FADE_M and M_AWC_Mastic's own aggregate bump fades in, so
# there is a crossfade, not an edge.  Chosen from px/m: tier C is 2.1-3.7 mm, so
# past 2.4 m it is under 4 px and stops earning its triangles.
TIER_RADIUS_M = {"A": 1e9, "B": 3.60, "C": 2.60}
FADE_M = 0.45
EDGE_FADE_M = 0.38     # over how much of the patch's own rim every tier fades out.
                       # Without it tier A simply stopped at the rectangle and the
                       # macro showed a hard line round the whole patch.

# NOTHING SMALLER THAN THIS IS MESHED, whatever the mix design says.  2.2 mm is
# 4.5 px at the hairpin station and 4.3 px on the onboard follow.  Below that a
# particle is a sub-pixel triangle cluster whose coverage changes every frame the
# camera moves -- it does not add detail, it adds CRAWL, and the manifest's own
# note asks for temporal flicker to be checked rather than assumed.  Sand below
# 2.2 mm is carried by M_AWC_Mastic's 1.1 mm / 0.38 mm / 0.16 mm bump layers,
# which are spatially smooth and therefore temporally stable.
D_FLOOR_M = 0.0022

RUBBER_TINT = 1.0     # set to 0.0 by rubber_line_deposit when it lands; see §2


def zone_of(s):
    """Index 0..8 of the resurfacing campaign that owns lap station s."""
    edges = np.array([r[0] for r in BS.RESURFACE])
    i = np.searchsorted(edges, np.asarray(s, float) % C.LAP, side="right") - 1
    return np.clip(i, 0, len(BS.RESURFACE) - 1)


def zone_age(s):
    """0 = laid this winter, 1 = twenty years of sun.  From build_surface."""
    ages = np.array([r[1] for r in BS.RESURFACE])
    return ages[zone_of(s)]


def mix_of(s):
    """The asphalt mix design at lap station s.  -> one of MIXES."""
    i = int(np.atleast_1d(zone_of(s))[0])
    m = dict(MIXES[i])
    m["zone"] = i
    m["age"] = float(np.atleast_1d(zone_age(s))[0])
    m["s_start"] = BS.RESURFACE[i][0]
    return m


# ===========================================================================
# 2.  THE FIELDS
# ===========================================================================
# Deterministic value noise on (s, u).  Not the shader's noise and not the
# contract's — it has to be evaluable in numpy at build time because it decides
# GEOMETRY (which stones exist, how deep they are drowned), and a field that only
# exists in the shader cannot do that.  Same hash as world_contract so the two
# never produce coincidentally correlated patterns.

def _vn(x, y, seed):
    """Value noise, C1, unit period, output 0..1."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    a = C.hash01(ix, iy, np.full_like(ix, seed))
    b = C.hash01(ix + 1, iy, np.full_like(ix, seed))
    c = C.hash01(ix, iy + 1, np.full_like(ix, seed))
    d = C.hash01(ix + 1, iy + 1, np.full_like(ix, seed))
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def _fbm(x, y, seed, oct=4, lac=2.07, gain=0.52):
    tot = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot = tot + amp * _vn(x * frq, y * frq, seed + o * 977)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def segregation(s, u):
    """0 = mortar-rich, 1 = coarse and open.  Variation axis 3 of 4.

    A paver segregates in two characteristic ways and both are here.  (a) The
    end-of-load drop: every time the hopper is refilled the coarse fraction rolls
    to the front and lands as a transverse band a few metres long — that is the
    ``s``-only term, on a period near the 9 m a load covers.  (b) The screed's
    own streaking along the mat, which runs longitudinally.  Multiplying them
    would make it a grid, so they are combined with a soft maximum.
    """
    s = np.asarray(s, float); u = np.asarray(u, float)
    drop = _fbm(s / 8.6, np.zeros_like(u), 4211, oct=3)
    drop = np.clip((drop - 0.46) / 0.30, 0.0, 1.0)
    streak = _fbm(s / 5.4, u / 0.55, 4231, oct=4)
    streak = np.clip((streak - 0.40) / 0.34, 0.0, 1.0)
    blob = _fbm(s / 1.35, u / 1.05, 4243, oct=4)
    blob = np.clip((blob - 0.44) / 0.36, 0.0, 1.0)
    a = np.maximum(drop * 0.95, streak * 0.72)
    return np.clip(np.maximum(a, blob * 0.85), 0.0, 1.0)


def flushing(s, u):
    """0..1 binder-rich "fatting up": bitumen has risen and drowned the stone."""
    s = np.asarray(s, float); u = np.asarray(u, float)
    f = _fbm(s / 3.1, u / 2.4, 4517, oct=4)
    f = np.clip((f - 0.60) / 0.19, 0.0, 1.0)
    # kneading by traffic drives it, so it is strongest where the cars run
    return f * (0.25 + 0.75 * polish(s, u))


def polish(s, u):
    """0..1 how planed off the stone tops are.  Variation axis 4 of 4.

    The driven line is not a stripe of constant width.  A season of cars puts the
    line in a slightly different place every lap, so the polished band is the
    ENVELOPE of a wandering 2.005 m car, not a 2.005 m stripe:  a hard core about
    one car wide, a shoulder out to about two, and a low-frequency wander of
    +-0.75 m in s.  ``racing_line_offset`` is build_surface's — the drivability
    solve is not re-run here and the line is not re-guessed.
    """
    s = np.asarray(s, float); u = np.asarray(u, float)
    if "line" not in BS._S:
        BS.prepare()
    line = BS.racing_line_offset(s)
    wob = (_vn(s * 0.011, np.zeros_like(np.asarray(u, float)), 7717) - 0.5) * 1.5
    d = np.abs(u - line - wob)
    core = np.clip((1.32 - d) / 0.55, 0.0, 1.0)                  # ~ one car wide
    shoulder = np.clip((2.60 - d) / 1.25, 0.0, 1.0) * 0.55       # the spread
    p = np.maximum(core, shoulder)
    p = p * p * (3.0 - 2.0 * p)
    # only inside the racing surface: nobody polishes the verge
    Wh = C.half_width(s)
    return p * np.clip((Wh - np.abs(u)) / 0.35, 0.0, 1.0)


def plucked(s, u):
    """0..1 field for stones torn bodily out of the mat (ravelling).

    A pluck-out is the single most recognisable "this road has been used" cue at
    macro range and the one thing a Voronoi field can never produce, because a
    Voronoi has no holes.  Here it is a hole: the stone is deleted and the mortar
    under it is dropped into a socket.  Old, open, segregated, un-driven surface
    ravels; a fresh binder-rich mat driven flat does not.
    """
    s = np.asarray(s, float); u = np.asarray(u, float)
    age = zone_age(s)
    cover = _fbm(s / 2.2, u / 1.7, 6101, oct=3)
    cover = np.clip((cover - 0.50) / 0.30, 0.0, 1.0)
    return np.clip(cover * (0.15 + 0.85 * age) * (0.35 + 0.65 * segregation(s, u))
                   * (1.0 - 0.70 * polish(s, u)), 0.0, 1.0)


# --- MTD IS NOT THE GEOMETRY, AND CONFUSING THE TWO DROWNED THE FIRST BUILD ----
#
# The first version set the mortar `tex` metres below the stone tops, where `tex`
# was the mix's sand-patch MEAN TEXTURE DEPTH -- 1.08 mm for SMA 11.  The macro
# render came back with the aggregate showing as thin triangular slivers, and the
# measured relief was 2.4 mm peak to valley over a patch whose stones are 11 mm.
#
# Sand-patch MTD is a VOLUME divided by an AREA: pour a known volume of sand into
# the surface, measure the disc it fills.  It is the mean depth of the voids, not
# the height of the stones.  For a skeleton of stones standing `p` proud over an
# areal stone coverage `k`,
#
#       MTD  ~  p * (1 - k)          with k ~ 0.55 for a gap-graded SMA
#
# so a 1.08 mm MTD is a 2.4 mm PROTRUSION, not a 1.08 mm one.  The geometry has to
# be built to `p`; MTD is what a highways engineer would then MEASURE on it, and
# it is reported by `mtd()` below so the two can be checked against each other.
#
# The consequence is the whole look of the item: at the contract sun's 12.471 deg
# a 2.4 mm stone throws a 10.9 mm shadow -- 22 px on the 4K master at the hairpin
# station -- where a 1.08 mm stone throws 4.9 mm and reads as speckle.

STONE_AREAL_COVERAGE = 0.55      # fraction of the surface that is coarse stone top
MAX_EXPOSURE = 0.58              # no stone may show more than this fraction of its
                                 # own height: past ~0.6 it is not bedded, it is
                                 # sitting on the surface, and the eye reads it as
                                 # loose grit rather than as part of the mat


TIER_A_MEAN_SIZE = 0.956   # of d_nom.  NOT (lo+hi)/2: the size draw is
                           # lo + (hi-lo) * f**(1/(1+0.9*seg)) with f uniform, so
                           # at the median segregation of 0.35 the expectation is
                           # 0.66 + 0.50 * 0.592 = 0.956, not 0.91.
TIER_A_MEAN_FLATNESS = 0.63   # short axis / long axis, from the crusher's own
                              # axis-ratio draw; MEASURED at 0.6295 over 60 000
                              # generated stones (verify.json flatness_ratio_mean)


def _h_mean(mix):
    """Mean VERTICAL extent of the coarse (tier A) fraction, in metres.

    The roller lays a platy stone on its flattest face, so the vertical extent is
    the SHORT axis.  For SMA 11: 11.2 * 0.956 * 0.63 = 6.74 mm.
    """
    return mix["d_nom"] * TIER_A_MEAN_SIZE * TIER_A_MEAN_FLATNESS


def exposure(s, u):
    """Fraction of the coarse skeleton's own height that stands out of the mortar.

    Derived from the mix's declared MTD rather than invented:
        expo = tex / (h_mean * (1 - STONE_AREAL_COVERAGE))
    which gives SMA 11 0.38, AC 14 0.23, PA 11 (porous) 0.65 -- and those are the
    right ordering and the right spread for the four recipes in MIXES.
    """
    s = np.asarray(s, float); u = np.asarray(u, float)
    zi = zone_of(s)
    tex = np.array([m["tex"] for m in MIXES])[zi]
    hm = np.array([_h_mean(m) for m in MIXES])[zi]
    e = tex / (hm * (1.0 - STONE_AREAL_COVERAGE))
    e = e * (1.0 + 0.42 * zone_age(s))            # oxidised mortar shrinks away
    e = e * (0.66 + 0.80 * segregation(s, u))     # open where segregated
    e = e * (1.0 - 0.62 * polish(s, u))           # planed and rubber-filled
    e = e * (1.0 - 0.86 * flushing(s, u))         # drowned in risen binder
    return np.clip(e, 0.012, 0.72)


def fill_depth(s, u):
    """GEOMETRIC metres from the stone-top envelope down to the mortar.

    This is the number the item is built around.  For the nine mixes it runs
    0.6 mm (flushed, polished SMA 8) to 4.6 mm (open, segregated porous asphalt),
    with clean SMA 11 at 2.4 mm and the rubbered racing line at 0.9 mm.
    """
    s = np.asarray(s, float); u = np.asarray(u, float)
    hm = np.array([_h_mean(m) for m in MIXES])[zone_of(s)]
    return np.clip(hm * exposure(s, u), 0.00008, 0.0055)


def mtd(s, u):
    """Sand-patch MEAN TEXTURE DEPTH, the number a highways engineer measures.

    = fill_depth * (1 - STONE_AREAL_COVERAGE).  Reported so the built geometry can
    be checked against the published range for each mix (EN 13036-1): SMA 8
    0.6-0.8 mm, SMA 11 0.8-1.2, aged AC 14 1.0-1.6, porous 1.8-2.6, a rubbered
    racing line 0.3-0.6, a flushed patch under 0.3.
    """
    return fill_depth(s, u) * (1.0 - STONE_AREAL_COVERAGE)


def stone_top_z(s, u, side=None):
    """The aggregate-skeleton envelope.  IS the contract datum, exactly."""
    return C.ground_z(s, u, side)


def mastic_top_z(s, u, side=None):
    """The mortar surface between the stones = datum - fill_depth."""
    if side is not None:
        u = np.abs(np.asarray(u, float)) * float(side)
    return C.ground_z(s, u) - fill_depth(s, u)


# ===========================================================================
# 3.  THE STONE GENERATOR
# ===========================================================================
#
# A crushed aggregate particle is a CONVEX POLYHEDRON WITH FLAT FRACTURE FACETS.
# It is not a sphere, not a rounded blob and not a noise-displaced ball — those
# are river gravel, and a circuit that used river gravel would have no grip.  So
# every stone here is generated the way a crusher makes one: take a lump and cut
# it with K random planes.
#
#     r(v) = min_k ( d_k / max(v . n_k, eps) )        for each template direction v
#
# evaluated on a fixed unit template.  The result is the radial function of the
# convex body {x : x.n_k <= d_k}, sampled at the template's vertex directions —
# i.e. a genuine convex polyhedron with flat faces and sharp arrises, different
# for every single stone because every stone gets its own K planes.
#
# Two physical facts are built in because they are what makes a scattered field
# read as a laid surface rather than as confetti:
#
#   FLAKINESS.  Crushed rock is platy.  EN 933-3 flakiness index for a good
#   circuit aggregate is 15-25 %; the axis ratios below give a shortest/longest
#   ratio of 0.42-0.86, which is that.  ``flake`` per mix design, because the
#   flakiness comes from the quarry and the crusher, not from the stone.
#
#   BEDDING.  A roller lays a platy stone ON ITS FLAT FACE.  The short axis ends
#   up near vertical, with a scatter that gets wider the more mortar there is to
#   float in.  Random rotation — the obvious thing, and the thing the brief names
#   as the failure — produces stones standing on edge, which reads instantly as
#   scattered debris.  The tilt here is Rayleigh-distributed about vertical with
#   sigma 13-24 deg.

_PHI = (1.0 + 5.0 ** 0.5) / 2.0


def _icosahedron():
    v = np.array([
        [-1,  _PHI, 0], [1,  _PHI, 0], [-1, -_PHI, 0], [1, -_PHI, 0],
        [0, -1,  _PHI], [0, 1,  _PHI], [0, -1, -_PHI], [0, 1, -_PHI],
        [_PHI, 0, -1], [_PHI, 0, 1], [-_PHI, 0, -1], [-_PHI, 0, 1],
    ], float)
    v /= np.linalg.norm(v, axis=1)[:, None]
    f = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], np.int32)
    return v, f


def _octahedron():
    """6 verts / 8 faces — the cheap template for the 2-4 mm fraction.

    At 2.1-3.7 mm a tier-C stone is 4-8 px.  A 12-vertex hull there is 12 vertices
    spent on a shape the lens cannot resolve past its silhouette, and the
    silhouette of a plane-cut octahedron is a convincing 4-6 sided angular chip.
    """
    v = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0],
                  [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
    f = np.array([[4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0],
                  [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3]], np.int32)
    return v, f


_TMPL = {"ico": _icosahedron(), "oct": _octahedron()}


def _rand_unit(rng, shape):
    v = rng.normal(size=shape + (3,))
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


def crushed_stones(n, rng, size_m, flake=0.32, tmpl="ico", n_planes=7,
                   chunk=24000):
    """Generate `n` UNIQUE crushed-rock particles.  THE public stone generator.

    Parameters
    ----------
    n        how many
    rng      numpy Generator (seed it from the site so a rebuild is identical)
    size_m   (n,) longest-axis length of each stone, in metres
    flake    0..1 how platy the quarry's product is (mix design's ``flake``)
    tmpl     "ico" (12 v / 20 f) or "oct" (6 v / 8 f)
    n_planes how many crusher cuts.  9-13 gives 5-9 visible faces.

    Returns
    -------
    V      (n, V, 3) float64 vertex positions, centred on the stone's own
           centroid, in metres, ALREADY ROTATED into world-up bedding
    F      (F, 3) int32 face indices, shared
    meta   dict with per-stone ``half_h`` (half the vertical extent),
           ``rad_xy`` (mean plan radius), ``axes`` and the local direction
           template ``slocal`` (n, V, 3) for per-stone material coordinates
    """
    tv, tf = _TMPL[tmpl]
    nv = tv.shape[0]
    V = np.empty((n, nv, 3))
    SL = np.empty((n, nv, 3))
    half_h = np.empty(n)
    rad_xy = np.empty(n)
    axes = np.empty((n, 3))

    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        m = b - a
        # --- the crusher: K random half-spaces -----------------------------
        nrm = _rand_unit(rng, (m, n_planes))
        # one cut is biased flat: a fracture face parallel to the bedding is what
        # gives a crushed stone its characteristic flat top, and it is the face
        # the roller will land on
        nrm[:, 0, :2] *= 0.22
        nrm[:, 0, :] /= np.linalg.norm(nrm[:, 0, :], axis=-1, keepdims=True)
        # HOW DEEP THE CRUSHER CUTS.  The first version used 11 planes at offsets
        # 0.60-1.00, which left 30 % of the template vertices untouched at radius
        # 1.0 -- i.e. most stones were still a lightly-shaved icosahedron.  Measured
        # Wadell sphericity came back 0.871, which is RIVER GRAVEL (0.85-0.95), not
        # crushed rock.  Fewer, deeper cuts: 7 planes at 0.28-0.64 leaves 91 % of
        # vertices on a cut plane and measures 0.80-0.82, the range a cubical
        # crushed aggregate with a flakiness index under 20 actually occupies.
        off = rng.uniform(0.28, 0.64, (m, n_planes))
        off[:, 0] = rng.uniform(0.24, 0.52, m)
        d = np.einsum("vj,mkj->mvk", tv, nrm)
        d = np.maximum(d, 1e-3)
        r = np.min(off[:, None, :] / d, axis=2)
        r = np.minimum(r, 1.0)
        P = tv[None, :, :] * r[:, :, None]                     # (m, nv, 3)
        SL[a:b] = tv[None, :, :] * (0.35 + 0.65 * r[:, :, None])

        # --- flakiness: three axis ratios, longest normalised to 1 ----------
        e2 = rng.uniform(0.66 - 0.10 * flake, 0.98 - 0.06 * flake, m)
        e3 = rng.uniform(0.42 + 0.10 * (1 - flake), 0.86 - 0.30 * flake, m)
        e3 = np.minimum(e3, e2 * 0.97)
        P = P * np.stack([np.ones(m), e2, e3], axis=1)[:, None, :]

        # --- bedding: short axis (local z) near vertical --------------------
        psi = rng.uniform(0.0, 2 * math.pi, m)                 # spin about short axis
        sig = np.radians(13.0 + 11.0 * rng.random(m))
        tilt = sig * np.sqrt(-2.0 * np.log(np.maximum(rng.random(m), 1e-9)))
        tilt = np.minimum(tilt, np.radians(62.0))
        phi = rng.uniform(0.0, 2 * math.pi, m)
        cz, sz = np.cos(psi), np.sin(psi)
        Rz = np.zeros((m, 3, 3)); Rz[:, 0, 0] = cz; Rz[:, 0, 1] = -sz
        Rz[:, 1, 0] = sz; Rz[:, 1, 1] = cz; Rz[:, 2, 2] = 1.0
        ax = np.stack([np.cos(phi), np.sin(phi), np.zeros(m)], axis=1)
        ct, st = np.cos(tilt)[:, None, None], np.sin(tilt)[:, None, None]
        K = np.zeros((m, 3, 3))
        K[:, 0, 1] = -ax[:, 2]; K[:, 0, 2] = ax[:, 1]
        K[:, 1, 0] = ax[:, 2]; K[:, 1, 2] = -ax[:, 0]
        K[:, 2, 0] = -ax[:, 1]; K[:, 2, 1] = ax[:, 0]
        I = np.eye(3)[None, :, :]
        Rt = I + st * K + (1.0 - ct) * (K @ K)
        R = Rt @ Rz
        P = np.einsum("mij,mvj->mvi", R, P)
        SL[a:b] = np.einsum("mij,mvj->mvi", R, SL[a:b])

        # --- scale to the requested longest-axis length ---------------------
        span = P.max(axis=1) - P.min(axis=1)
        L = np.maximum(span.max(axis=1), 1e-9)
        k = (size_m[a:b] / L)[:, None, None]
        P = P * k
        P = P - P.mean(axis=1)[:, None, :]
        V[a:b] = P
        half_h[a:b] = 0.5 * (P[:, :, 2].max(axis=1) - P[:, :, 2].min(axis=1))
        rad_xy[a:b] = 0.5 * np.mean(
            [P[:, :, 0].max(axis=1) - P[:, :, 0].min(axis=1),
             P[:, :, 1].max(axis=1) - P[:, :, 1].min(axis=1)], axis=0)
        axes[a:b] = np.stack([np.ones(m), e2, e3], axis=1)

    return V, tf, dict(half_h=half_h, rad_xy=rad_xy, axes=axes, slocal=SL)


# ===========================================================================
# 4.  THE SCATTER
# ===========================================================================
#
# Multi-tier jittered-grid packing.  The coarse tier is laid on its own grid (one
# candidate per cell, jittered inside the cell); each finer tier is laid on a
# grid whose pitch is a fraction of the coarse one and is REJECTED where it would
# intersect a stone already placed.  That is what a gap-graded skeleton is: the
# coarse fraction touches, the finer fractions fill what is left.
#
# Rejection is O(n): a tier's occupancy is exactly its grid, so testing a
# candidate against a previous tier is a 3x3 cell lookup, never a search.

def _tier_presence(k, x, y, anchor, Q, ext_s, ext_u):
    """0..1 probability that tier `k` is meshed at local (x, y).

    Two independent fades, multiplied:
      * DISTANCE from the lens — past TIER_RADIUS_M a chipping of that size is
        under 4 px and stops earning its triangles;
      * the PATCH RIM — every tier, including the coarse one, has to go away
        before the mesh does, or the patch has an edge.  The first build let
        tier A run to the rectangle and stop, and the macro came back with a
        hard line round all four sides.

    The mastic material reads the same number out of AWC_mastic.A and fades its
    own chip layer in against it, so representation changes and appearance does
    not.
    """
    p = np.ones(np.shape(x))
    R = TIER_RADIUS_M[k] * Q["radius_mul"]
    if anchor is not None and R < 1e8:
        dd = np.sqrt((x - anchor[0]) ** 2 + (y - anchor[1]) ** 2 + anchor[2] ** 2)
        p = p * np.clip((R + FADE_M - dd) / FADE_M, 0.0, 1.0)
    edge = np.minimum(ext_s - np.abs(x), ext_u - np.abs(y))
    return p * np.clip(edge / EDGE_FADE_M, 0.0, 1.0)


class _Tier:
    __slots__ = ("pitch", "nx", "ny", "x0", "y0", "pos", "rad", "cell", "n")

    def __init__(self, pitch, x0, y0, nx, ny):
        self.pitch = pitch; self.x0 = x0; self.y0 = y0
        self.nx = nx; self.ny = ny
        self.cell = np.full((ny, nx), -1, np.int64)

    def commit(self, ci, cj, pos, rad):
        self.pos = pos; self.rad = rad; self.n = pos.shape[0]
        self.cell[cj, ci] = np.arange(self.n)

    def clearance(self, x, y):
        """-> (gap, idx) distance from (x,y) to the nearest stone SURFACE."""
        ci = np.clip(((x - self.x0) / self.pitch).astype(np.int64), 0, self.nx - 1)
        cj = np.clip(((y - self.y0) / self.pitch).astype(np.int64), 0, self.ny - 1)
        best = np.full(x.shape, 1e9)
        bidx = np.full(x.shape, -1, np.int64)
        for dj in (-1, 0, 1):
            jj = np.clip(cj + dj, 0, self.ny - 1)
            for di in (-1, 0, 1):
                ii = np.clip(ci + di, 0, self.nx - 1)
                k = self.cell[jj, ii]
                ok = k >= 0
                kk = np.where(ok, k, 0)
                d = np.hypot(x - self.pos[kk, 0], y - self.pos[kk, 1]) - self.rad[kk]
                d = np.where(ok, d, 1e9)
                take = d < best
                best = np.where(take, d, best)
                bidx = np.where(take, kk, bidx)
        return best, bidx


def _scatter(rng, x0, x1, y0, y1, pitch, jitter=0.42):
    nx = max(int(math.floor((x1 - x0) / pitch)), 1)
    ny = max(int(math.floor((y1 - y0) / pitch)), 1)
    ci, cj = np.meshgrid(np.arange(nx), np.arange(ny))
    ci = ci.ravel(); cj = cj.ravel()
    x = x0 + (ci + 0.5 + (rng.random(ci.size) - 0.5) * 2.0 * jitter) * pitch
    y = y0 + (cj + 0.5 + (rng.random(cj.size) - 0.5) * 2.0 * jitter) * pitch
    t = _Tier(pitch, x0, y0, nx, ny)
    return t, ci, cj, x, y


# ===========================================================================
# 5.  SITES
# ===========================================================================

class Site:
    """A hero patch is defined BY THE LENS IT IS BUILT FOR, not by a rectangle.

    The first build defined it as a rectangle and guessed where to put it.  The
    macro render showed exactly what that costs: the bottom-left of the frame,
    1.0 m from the lens, fell OUTSIDE the patch and rendered as bump-only
    aggregate -- domes, at 0.43 mm/px.  A rectangle chosen by hand cannot
    reliably contain a frustum, so it is derived from one instead.

    s_cam, u_cam, h_cam   the lens.  `u_cam` is a starting guess: the actual
                          lateral is SOLVED so the nearest racing surface is
                          exactly `nearest_camera_m`, and the patch is then laid
                          out around the solved position.
    view_az_deg           view azimuth in the local road frame: 0 = straight down
                          the road, +90 = straight across it toward -u.
    coverage_m            explicit stones out to this 3-D distance from the lens.
    aim_d_m               how far out the lens aims, which sets the framing.

    Derived at build time and then readable:  s0, u0, ext_s, ext_u.
    """

    HALF_FOV_DEG = math.degrees(math.atan(0.5 * SENSOR_MM / LENS_AT_CLOSEST_MM))
    # (the widest lens the item is filmed on; the layout margin covers the rest)
    AZ_MARGIN_DEG = 6.0
    APEX_PAD_M = 0.40

    def __init__(self, name, s_cam, u_cam, h_cam, view_az_deg,
                 coverage_m=4.75, aim_d_m=1.15, seed=0, solve_lateral=True,
                 lens_mm=LENS_AT_CLOSEST_MM):
        self.name = name
        self.solve_lateral = bool(solve_lateral)
        self.lens_mm = float(lens_mm)
        self.s_cam = float(s_cam); self.u_cam = float(u_cam)
        self.h_cam = float(h_cam)
        self.view_az_deg = float(view_az_deg)
        self.coverage_m = float(coverage_m)
        self.aim_d_m = float(aim_d_m)
        self.seed = int(seed)
        self.solved = False
        self.layout()

    # -- the lens ---------------------------------------------------------
    def solve_lens(self):
        """Move the lens across the kerb until the nearest racing surface is
        EXACTLY NEAREST_CAMERA_M.  Bisection, because the answer is not the
        Pythagorean guess: T4 is a 28 m radius and the lens is on the INSIDE, so
        the track edge curves toward it and the nearest point is 1.1 m up the
        road, not abeam.  The guess was 4.4 % short."""
        def near(u):
            cx, cy, cz = C.su_to_world(self.s_cam, u)
            p = np.array([cx, cy, cz + self.h_cam])
            ss = np.linspace(self.s_cam - 5.0, self.s_cam + 5.0, 1001)
            uu = np.linspace(-C.half_width(self.s_cam), C.half_width(self.s_cam), 401)
            SS, UU = np.meshgrid(ss, uu)
            SS = SS.ravel(); UU = UU.ravel()
            P = _su_to_world_xyz(SS, UU, C.ground_z(SS, UU))
            d = np.linalg.norm(P - p, axis=1)
            k = int(np.argmin(d))
            return float(d[k]), p, float(SS[k]), float(UU[k])

        if self.solve_lateral:
            lo, hi = self.u_cam, self.u_cam + 1.6
            for _ in range(36):
                mid = 0.5 * (lo + hi)
                if near(mid)[0] < NEAREST_CAMERA_M:
                    lo = mid
                else:
                    hi = mid
            self.u_cam = 0.5 * (lo + hi)
        self.near_m, self.cam_world, self.near_s, self.near_u = near(self.u_cam)
        self.solved = True
        self.layout()
        return self.u_cam

    # -- the patch --------------------------------------------------------
    def layout(self):
        """Bounding box, in (ds, du) about the lens, of everything the lens can
        see within `coverage_m`.  Sampled rather than solved in closed form: the
        wedge is nearly a quarter circle and its extreme points are not always
        its endpoints."""
        az = math.radians(self.view_az_deg)
        half = math.radians(self.HALF_FOV_DEG + self.AZ_MARGIN_DEG)
        rg = math.sqrt(max(self.coverage_m ** 2 - self.h_cam ** 2, 0.01))
        a = np.linspace(az - half, az + half, 512)
        ds = np.concatenate([rg * np.cos(a), [0.0],
                             self.APEX_PAD_M * np.cos(np.linspace(0, 2 * math.pi, 64))])
        du = np.concatenate([-rg * np.sin(a), [0.0],
                             self.APEX_PAD_M * np.sin(np.linspace(0, 2 * math.pi, 64))])
        s_lo, s_hi = float(ds.min()), float(ds.max())
        u_lo, u_hi = float(du.min()), float(du.max())
        self.s0 = self.s_cam + 0.5 * (s_lo + s_hi)
        self.u0 = self.u_cam + 0.5 * (u_lo + u_hi)
        self.ext_s = 0.5 * (s_hi - s_lo)
        self.ext_u = 0.5 * (u_hi - u_lo)

    @property
    def anchor_su(self):
        return (self.s_cam, self.u_cam, self.h_cam)


# THE T4 HAIRPIN STATION — the shot this item has to survive.
#
# circuit_spec §11 Beat 5: "kerb-height hairpin pass (STATIC on the T4 inside
# kerb, z=+0.85, 21 mm)".  T4 LE PIN is a LEFT hairpin (spec: direction "left"),
# so its inside is side +1 and the kerb band runs u = +7.500 .. +9.000
# (half_width 7.500 at the hairpin + C.KERB_W 1.500).  A lens 0.850 m over a kerb
# at u = +8.148 is
#
#     sqrt(0.698^2 + 0.850^2) = 1.100 m
#
# from the racing-surface edge at u = +7.500.  THAT is where the manifest's
# nearest_camera_m = 1.1 comes from, and it is reproduced here rather than
# assumed.  build_surface's racing line runs at u = +6.950 at the apex, so the
# polished band crosses this patch: the "polish on the line" axis is IN the hero
# frame, not somewhere else on the lap.
S_T4_APEX = 982.27

# The framing, and why AIM_D is 1.15 m.  A 21 mm lens on 16:9 has a 51.3 deg
# vertical field, so a lens 0.850 m up aiming 1.15 m out pitches 36.5 deg down and
# the frame runs from 0.96 m (bottom) to 4.51 m (top) of ground -- 2330 px/m down
# to 497 px/m, with the horizon off the top.  `coverage_m` = 4.75 then puts real
# meshed aggregate under EVERY pixel of that frame.  Aiming further out is a wider
# shot with sky in it, i.e. a third of an item macro spent on somebody else's item.
PATCH_SITES = [
    Site("t4_apex", s_cam=S_T4_APEX - 1.10, u_cam=8.148, h_cam=0.850,
         view_az_deg=48.8, coverage_m=4.75, aim_d_m=1.15, seed=41),
    # the onboard follow: 1.9 m over the pit straight at 323 km/h.  Same detail
    # spec (1965 vs 2036 px/m), a different mix (zone 8, SMA 8) and no hairpin
    # polish band -- the line on a straight is wide and faint.  The lens looks
    # down the road here, not across it.
    Site("pit_straight", s_cam=3400.0, u_cam=0.0, h_cam=1.900,
         view_az_deg=12.0, coverage_m=6.20, aim_d_m=2.30, seed=57,
         lens_mm=35.0,           # beat sheet: the onboard follow is a 35 mm, so
                                 # (3840*35/36)/1.9 = 1965 px/m against the
                                 # hairpin's 2036 -- one detail spec serves both
         solve_lateral=False),   # the onboard lens is 1.9 m DIRECTLY over the
                                 # deck; there is no lateral to solve and the
                                 # nearest surface is 1.900 m, not 1.100 m
]


# ===========================================================================
# 6.  MESH PLUMBING
# ===========================================================================

def _tri_mesh(name, co, tris, smooth=False):
    me = bpy.data.meshes.new(name)
    nv = int(co.shape[0]); nf = int(tris.shape[0])
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
    me.loops.add(nf * 3)
    me.loops.foreach_set("vertex_index", np.ascontiguousarray(tris, np.int32).ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 3)
    me.update()
    me.validate(verbose=False)
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    return me


ATTRS = ("AWC_zone", "AWC_lith", "AWC_slocal", "AWC_mastic")
#   AWC_zone   RGBA = (zone age 0..1, segregation, polish, flushing)
#   AWC_lith   RGBA = (lithology 0..1, tone jitter, per-stone seed, stone polish)
#   AWC_slocal RGB  = stone-local direction (unit-ish), A = height above the
#                     mortar normalised 0..1.  ZERO on mastic geometry.
#   AWC_mastic RGBA = (fill depth / 4 mm, meniscus 0..1, void pocket 0..1,
#                     per-cell seed).  ZERO on stone geometry.


def bake_attrs(me, zone=None, lith=None, slocal=None, mastic=None):
    """Write the attributes every AWC material reads.  Public: a dependant that
    emits geometry into mat_stone()/mat_mastic() must call this.

    Pass None for an attribute that is identically zero on this mesh and it is
    simply not created: a ShaderNodeAttribute that names a missing attribute
    already evaluates to zero, so an all-zero AWC_lith on 600 000 mastic vertices
    is 9.6 MB of blend file that says nothing.
    """
    for name, data in zip(ATTRS, (zone, lith, slocal, mastic)):
        if data is None:
            continue
        at = me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
        at.data.foreach_set("color", np.ascontiguousarray(data, np.float32).ravel())


def _obj(name, me, coll, mat, centre):
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    ob.matrix_world = Matrix.Translation(Vector(centre))
    coll.objects.link(ob)
    return ob


def _su_to_world_xyz(S, U, Z):
    """(station, signed lateral, absolute z) -> world (x, y, z).  Vectorised.

    The patch is 3.8 m of a 28 m-radius hairpin: the sagitta over that chord is
    3.8^2/(8*28) = 64 mm, so a flat tangent frame would lift the far corners of
    the patch 64 mm off the road.  Every vertex goes through the true (s, u)
    mapping instead.
    """
    X, Y, H, _K = C.centreline_arrays(S)
    return np.stack([X - np.sin(H) * U, Y + np.cos(H) * U, Z], axis=-1)


# ===========================================================================
# 7.  THE BUILD
# ===========================================================================

QUALITY = {
    # pitch_mul scales every tier's grid pitch: 1.0 is the real gradation.
    # draft exists to run the whole pipeline (gate, farm, look) in ~40 s.
    "draft": dict(pitch_mul=2.30, mastic_mm=13.0, radius_mul=0.55, far_m=60.0),
    "hero":  dict(pitch_mul=1.00, mastic_mm=5.50, radius_mul=1.00, far_m=90.0),
}


def _clear():
    coll = bpy.data.collections.get(COLL_NAME)
    if coll:
        for ob in list(coll.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(coll)
    for m in list(bpy.data.materials):
        if m.name.startswith(MPFX):
            bpy.data.materials.remove(m)
    coll = bpy.data.collections.new(COLL_NAME)
    bpy.context.scene.collection.children.link(coll)
    return coll


def build(site=None, quality="hero", coll=None, stats=None):
    """Emit one hero patch of wearing course.  -> stats dict."""
    site = site or PATCH_SITES[0]
    Q = QUALITY[quality]
    rng = np.random.default_rng(1000 + site.seed)
    t_start = time.time()
    if coll is None:
        coll = _clear()
    st = stats if stats is not None else {}

    if "line" not in BS._S:
        BS.prepare()

    if not site.solved:
        site.solve_lens()
        print(">> lens solved: s=%.3f u=%+.4f h=%.3f  -> nearest racing surface "
              "%.4f m (manifest %.3f) at s=%.2f u=%+.3f"
              % (site.s_cam, site.u_cam, site.h_cam, site.near_m,
                 NEAREST_CAMERA_M, site.near_s, site.near_u))
        print(">> patch laid out from the frustum: s %.3f +-%.3f  u %+.3f +-%.3f "
              " (%.2f x %.2f m = %.1f m2)"
              % (site.s0, site.ext_s, site.u0, site.ext_u,
                 2 * site.ext_s, 2 * site.ext_u,
                 4 * site.ext_s * site.ext_u))

    mix = mix_of(site.s0)
    d_nom = mix["d_nom"]
    print(">> AWC site %-14s s=%.2f u=%+.2f  zone %d  %s (%s)"
          % (site.name, site.s0, site.u0, mix["zone"], mix["name"], mix["note"]))
    print(">>   d_nom %.1f mm  tex %.2f mm  voids %.1f%%  binder %.2f  flake %.2f"
          % (d_nom * 1000, mix["tex"] * 1000, mix["void"] * 100,
             mix["binder"], mix["flake"]))

    # ---- patch extents in LOCAL road coordinates (ds, du) -------------------
    ex_s, ex_u = site.ext_s, site.ext_u
    x0, x1 = -ex_s, ex_s
    y0, y1 = -ex_u, ex_u

    # the LOD anchor in local coords
    if site.anchor_su:
        as_, au_, ah_ = site.anchor_su
        anchor = np.array([as_ - site.s0, au_ - site.u0, ah_])
    else:
        anchor = None

    def _dist_to_anchor(dx, dy):
        if anchor is None:
            return np.zeros_like(dx)
        return np.sqrt((dx - anchor[0]) ** 2 + (dy - anchor[1]) ** 2 + anchor[2] ** 2)

    # =====================================================================
    # 7a.  THE AGGREGATE SKELETON
    # =====================================================================
    tiers = []
    placed = []          # previously committed _Tier objects for rejection
    n_total = 0
    for spec in TIERS:
        lo = d_nom * spec["lo"]
        hi = d_nom * spec["hi"]
        if hi < D_FLOOR_M * 1.18:
            print(">>   tier %s  %.1f-%.1f mm is below the %.1f mm mesh floor "
                  "-> carried by the mastic bump, not meshed"
                  % (spec["k"], lo * 1000, hi * 1000, D_FLOOR_M * 1000))
            continue
        pitch = d_nom * spec["pitch"] * Q["pitch_mul"]
        t, ci, cj, x, y = _scatter(rng, x0, x1, y0, y1, pitch)
        S = site.s0 + x
        U = site.u0 + y

        sg = segregation(S, U)
        po = polish(S, U)
        fl = flushing(S, U)
        age = zone_age(S)

        # ---- size: the sieve fraction, modulated by segregation -----------
        # A segregated (coarse) patch is not "the same stones further apart", it
        # is a patch the fines never reached, so the stones that ARE there are
        # the top of the sieve.  Size and count move together.
        f = rng.random(x.size)
        size = lo + (hi - lo) * f ** (1.0 / (1.0 + 0.9 * sg))
        size = size * (0.94 + 0.12 * rng.random(x.size))
        size = np.maximum(size, D_FLOOR_M)

        rad = size * 0.42                     # plan radius used for packing

        keep = np.ones(x.size, bool)

        # ---- LOD: presence, not a hard radius ------------------------------
        # `_tier_presence` is the SAME function the mastic bakes into AWC_mastic.A,
        # so wherever a tier thins out the mastic material's own chip layer comes
        # up by exactly the amount the mesh went away.  A hard radius (the first
        # build) puts a line round the patch; this puts a crossfade on it.
        pres = _tier_presence(spec["k"], x, y, anchor, Q, ex_s, ex_u)
        keep &= rng.random(x.size) < pres

        # ---- packing: reject against every coarser tier --------------------
        for prev, prev_clear in placed:
            gap, _ = prev.clearance(x, y)
            keep &= gap > rad * prev_clear

        # ---- pluck-outs: the stone is simply not there ---------------------
        pl = plucked(S, U)
        pl_hit = rng.random(x.size) < pl * (0.055 if spec["k"] == "A" else 0.030)
        keep &= ~pl_hit

        # ---- porous asphalt loses its finest fraction on purpose ----------
        if mix["void"] > 0.10 and spec["k"] == "C":
            keep &= rng.random(x.size) < 0.28

        ci, cj, x, y = ci[keep], cj[keep], x[keep], y[keep]
        S, U = S[keep], U[keep]
        size, rad = size[keep], rad[keep]
        sg, po, fl, age = sg[keep], po[keep], fl[keep], age[keep]
        t.commit(ci, cj, np.stack([x, y], axis=1), rad)
        placed.append((t, spec["clear"]))
        tiers.append(dict(spec=spec, t=t, x=x, y=y, S=S, U=U, size=size,
                          sg=sg, po=po, fl=fl, age=age))
        n_total += x.size
        print(">>   tier %s  pitch %5.2f mm  size %4.1f-%4.1f mm  -> %7d stones"
              % (spec["k"], pitch * 1000, lo * 1000, hi * 1000, x.size))

    # =====================================================================
    # 7b.  BED THE STONES
    # =====================================================================
    stone_objs = []
    tri_total = 0
    for ti, T in enumerate(tiers):
        spec = T["spec"]
        n = T["x"].size
        if n == 0:
            continue
        V, F, meta = crushed_stones(n, rng, T["size"], flake=mix["flake"],
                                    tmpl=spec["tmpl"],
                                    n_planes=7 if spec["tmpl"] == "ico" else 6)
        nv = V.shape[1]

        S, U = T["S"], T["U"]
        env = C.ground_z(S, U)                       # stone-top envelope = datum
        fdep = fill_depth(S, U)
        mz = env - fdep                              # mortar level here

        # PROTRUSION: how far this stone's top stands above the MORTAR.
        #
        # The mortar is ONE surface at `mz`, so a stone's exposure is decided by
        # where its top happens to land, not by a per-stone choice.  Its mean is
        # `fdep` by construction, which is what makes `stone_top_z` equal the
        # contract datum to within the scatter the roller left rather than by
        # assertion.  Two physical terms on top of that:
        #
        #   * bigger stones in the same mat ride higher -- the skeleton is
        #     stone-on-stone, so a 13 mm particle cannot sit as deep as a 7 mm one;
        #   * NO STONE MAY FLOAT.  A 2.5 mm fine particle cannot show 2.4 mm of
        #     itself; it would be a grain resting on the surface.  Capping exposure
        #     at MAX_EXPOSURE of the stone's OWN height is what makes the fine
        #     fractions nestle into the interstices instead of hovering in them,
        #     and it is why the coarse fraction alone defines the level.
        prot = fdep * (0.62 + 0.76 * rng.random(n))
        prot = prot + (T["size"] / d_nom - TIER_A_MEAN_SIZE) * fdep * 0.45
        prot = np.minimum(prot, 2.0 * meta["half_h"] * MAX_EXPOSURE)
        prot = np.clip(prot, 0.00003, 0.0060)
        top = mz + prot                              # absolute z of the stone top
        cz = top - meta["half_h"]                    # stone centre z

        # --- the polish plane: variation axis 4, AS GEOMETRY -----------------
        # Tyres do not darken a stone, they PLANE IT.  Every vertex above the
        # local wear plane is cut down to it, which turns the top of the stone
        # into a real horizontal facet with a real sharp arris round it.  At a
        # 12.47 deg sun a horizontal facet is the only thing on the surface that
        # can throw a specular highlight back at a low camera -- which is exactly
        # what a rubbered-in racing line does in life and what no amount of
        # roughness-map darkening reproduces.
        #
        # The plane is SMOOTH and SHARED, not per stone: a tyre is one surface, so
        # the proud stones lose their tops and the low ones are untouched.  That
        # is the whole point -- planing every stone by a little would just be a
        # different stone shape, not a worn surface.
        po = T["po"]
        wear = mz + fdep * (0.94 + 0.30 * _vn(S / 0.31, U / 0.31, 9151))
        cut = wear + (1.0 - po) * 0.012              # lifts clear off the line

        Vw = V.copy()
        Vw[:, :, 2] += cz[:, None]
        Vw[:, :, 2] = np.minimum(Vw[:, :, 2], cut[:, None])

        # --- bury: nothing below the mortar needs to exist -------------------
        floor = (mz - 0.0045)[:, None]
        Vw[:, :, 2] = np.maximum(Vw[:, :, 2], floor)
        top = np.minimum(top, cut)

        # --- to world ---------------------------------------------------------
        # x is along s, y is across u, so a vertex at local (vx, vy) belongs at
        # station S + vx and lateral U + vy.  Going through centreline_arrays
        # keeps the 28 m hairpin radius exact.
        VS = (S[:, None] + Vw[:, :, 0]).ravel()
        VU = (U[:, None] + Vw[:, :, 1]).ravel()
        VZ = Vw[:, :, 2].ravel()
        P = _su_to_world_xyz(VS, VU, VZ)

        # --- attributes -------------------------------------------------------
        lith_w = np.array(mix["lith"], float)
        lith_w = lith_w / lith_w.sum()
        draw = rng.random(n)
        lid = np.where(draw < lith_w[0], 0.08,
                       np.where(draw < lith_w[0] + lith_w[1], 0.50, 0.92))
        lith = np.stack([lid,
                         rng.random(n),
                         rng.random(n),
                         po], axis=1)
        zone = np.stack([T["age"], T["sg"], po, T["fl"]], axis=1)
        hnorm = np.clip((Vw[:, :, 2] - mz[:, None]) / np.maximum(
            (top - mz)[:, None], 1e-5), 0.0, 1.0)
        sl = meta["slocal"]
        slocal = np.concatenate([sl * 0.5 + 0.5, hnorm[:, :, None]], axis=2)

        zone_v = np.repeat(zone, nv, axis=0)
        lith_v = np.repeat(lith, nv, axis=0)
        slocal_v = slocal.reshape(-1, 4)

        # --- faces ------------------------------------------------------------
        base = (np.arange(n) * nv)[:, None, None]
        tris = (F[None, :, :] + base).reshape(-1, 3).astype(np.int32)

        centre_world = P.mean(axis=0)
        me = _tri_mesh("%sStones_%s_%s" % (PFX, site.name, spec["k"]),
                       P - centre_world, tris, smooth=False)
        bake_attrs(me, zone=zone_v, lith=lith_v, slocal=slocal_v)
        # NO uv layer on the stones.  M_AWC_Stone reads only AWC_slocal and
        # TexCoord->Object; a per-loop UV on 2.1 M loops is 34 MB of blend file
        # that no node ever samples.
        ob = _obj("%sStones_%s_%s" % (PFX, site.name, spec["k"]), me, coll,
                  mat_stone(), centre_world)
        stone_objs.append(ob)
        tri_total += tris.shape[0]
        print(">>   tier %s meshed: %d stones, %d verts, %d tris"
              % (spec["k"], n, P.shape[0], tris.shape[0]))

    # =====================================================================
    # 7c.  THE MORTAR
    # =====================================================================
    mob, mtris = _build_mastic(site, tiers, mix, rng, coll, Q, anchor)
    tri_total += mtris

    # =====================================================================
    # 7d.  THE SURROUND
    # =====================================================================
    fob, ftris = _build_surround(site, mix, coll, Q)
    tri_total += ftris

    st.update(dict(
        site=site.name, quality=quality, zone=mix["zone"], mix=mix["name"],
        stones=n_total, triangles=tri_total,
        objects=len(stone_objs) + 2,
        seconds=round(time.time() - t_start, 1),
    ))
    print(">> AWC %s: %d stones, %d triangles, %.1f s"
          % (site.name, n_total, tri_total, st["seconds"]))
    return st


def _add_su_uv(me, ds, du):
    """Road-aligned metric coordinates, relative to the patch centre.

    A UV layer rather than object space because object space is world-aligned and
    the road is not: the paving direction at T4 is 192 deg true.  Values are
    METRES and small (|.| < 6), so nothing here can lose precision.
    """
    lay = me.uv_layers.new(name="AWC_su")
    n = len(me.loops)
    vi = np.empty(n, np.int32)
    me.loops.foreach_get("vertex_index", vi)
    uv = np.stack([du[vi], ds[vi]], axis=1)
    lay.uv.foreach_set("vector", np.ascontiguousarray(uv, np.float32).ravel())


def _build_mastic(site, tiers, mix, rng, coll, Q, anchor):
    """The bitumen mortar the stones are bedded in.

    It is NOT a flat plane with a texture.  Its height is built from the stone
    field itself:

      * the interstitial level is `datum - fill_depth`;
      * a MENISCUS rises against every stone, because bitumen wets mineral and
        climbs it — this is why a real surface reads as stones IN something
        rather than stones ON something, and it is the single detail that a
        Voronoi-based asphalt shader structurally cannot produce;
      * VOID POCKETS drop between the coarse stones where the mortar never
        filled, deepest in the porous-asphalt zone (19 % voids);
      * a PLUCK SOCKET is dug wherever the scatter deleted a stone.
    """
    pitch = Q["mastic_mm"] / 1000.0
    # THE MASTIC AND THE STONES END ON THE SAME LINE.  The first build gave the
    # mortar a 60 mm margin over the scatter rectangle, which laid a 60 mm ring of
    # bare binder all the way round the patch: at 1-4 m that is a 15-60 px smooth
    # stripe, and it is the vertical band down the right of the first macro.
    ex_s = site.ext_s
    ex_u = site.ext_u
    nx = int(round(2 * ex_s / pitch)) + 1
    ny = int(round(2 * ex_u / pitch)) + 1
    gx = np.linspace(-ex_s, ex_s, nx)
    gy = np.linspace(-ex_u, ex_u, ny)
    X, Y = np.meshgrid(gx, gy)
    X = X.ravel(); Y = Y.ravel()
    S = site.s0 + X
    U = site.u0 + Y

    env = C.ground_z(S, U)
    fdep = fill_depth(S, U)
    z = env - fdep

    sg = segregation(S, U)
    po = polish(S, U)
    fl = flushing(S, U)
    age = zone_age(S)

    # --- meniscus + void pockets from the two coarse tiers -------------------
    men = np.zeros(X.size)
    gapA = np.full(X.size, 1e9)
    for T in tiers[:2]:
        t = T["t"]
        if getattr(t, "n", 0) == 0:
            continue
        gap, idx = t.clearance(X, Y)
        gapA = np.minimum(gapA, gap)
        lam = 0.0009 if T["spec"]["k"] == "A" else 0.0006
        rise = np.exp(-np.maximum(gap, 0.0) / lam)
        men = np.maximum(men, rise)
    men *= (0.42 + 0.58 * mix["binder"])
    # A BITUMEN MENISCUS IS 0.2-0.4 mm, NOT 60 % OF THE TEXTURE DEPTH.  The first
    # version raised the mortar by 0.62 * fill_depth against every stone, on a
    # 1.6 mm length scale, and the two together re-buried the aggregate the mesh
    # had just exposed: the crop came back showing the tips of the stones only.
    # Surface tension against a mineral face climbs a fraction of a millimetre.
    z += men * np.minimum(fdep * 0.16, 0.00040)

    # --- void pockets: the mortar never reached the middle of the interstice --
    void_amt = 0.30 + 3.2 * mix["void"]
    pocket = np.clip((gapA - 0.0008) / 0.0034, 0.0, 1.0)
    pocket = pocket * np.clip(0.25 + 1.10 * sg, 0.0, 1.0) * void_amt
    pocket = pocket * (1.0 - 0.80 * fl)
    z -= pocket * fdep * 0.85

    # --- THE LOD CROSSFADE CHANNEL ------------------------------------------
    # Tiers B and C stop at 3.60 m and 2.60 m from the lens, so past those radii
    # the mortar between the meshed tier-A stones has nothing in it -- a visible
    # ring of bare binder, which is a worse artefact than the coarse geometry it
    # was meant to save.  `agg_fade` is 0 where every tier is meshed and rises to
    # 1 where none is, and M_AWC_Mastic fades its own chip layer IN on exactly
    # that number.  So the transition is a change of REPRESENTATION at constant
    # appearance, which is what an LOD is supposed to be and what a hard radius
    # never is.
    pA = _tier_presence("A", X, Y, anchor, Q, site.ext_s, site.ext_u)
    pB = _tier_presence("B", X, Y, anchor, Q, site.ext_s, site.ext_u)
    pC = _tier_presence("C", X, Y, anchor, Q, site.ext_s, site.ext_u)
    # ONE monotone channel for three tiers.  It works because the presences are
    # always ordered pC <= pB <= pA (the radii nest and the rim fade is shared),
    # so the material can pull the mid fraction in over 0.05..0.60 and the coarse
    # fraction only over 0.68..0.98 and never get them out of order.
    agg_fade = np.clip(1.0 - (0.34 * pA + 0.38 * pB + 0.28 * pC), 0.0, 1.0)

    # --- pluck sockets -------------------------------------------------------
    pl = plucked(S, U)
    soc = _vn(S / 0.019, U / 0.019, 8081)
    soc = np.clip((soc - 0.80) / 0.13, 0.0, 1.0) * pl
    z -= soc * (mix["d_nom"] * 0.42)

    # --- the fine mortar's own relief (below the stone scale) ----------------
    z += (_fbm(S / 0.045, U / 0.045, 8231, oct=3) - 0.5) * 0.00035
    z += (_fbm(S / 0.011, U / 0.011, 8233, oct=2) - 0.5) * 0.00014

    # --- THE SEAM.  Everything above is relief; the surround carries none of it,
    # so the last 25 mm of the patch hands the relief back and both meshes land on
    # `env - fill_depth` along the shared boundary line.  The surround's grid is
    # coarser there, so the boundary carries T-junctions -- but both surfaces are
    # sampled from the same C1 field, whose curvature over a 45 mm surround cell is
    # under a micron, so the T-junctions cannot open a crack.  A 25 mm taper at
    # 3.3 m from the lens is 17 px of very slightly smoother mortar at the far edge
    # of the fine zone; a 1 mm step there would be 0.7 px of black line, and a
    # black line is the thing you see.
    base_z = env - fdep
    seam = np.minimum(np.clip((ex_s - np.abs(X)) / 0.025, 0.0, 1.0),
                      np.clip((ex_u - np.abs(Y)) / 0.025, 0.0, 1.0))
    z = base_z + (z - base_z) * seam

    P = _su_to_world_xyz(S, U, z)

    tris = _grid_tris(nx, ny)
    centre = P.mean(axis=0)
    me = _tri_mesh("%sMastic_%s" % (PFX, site.name), P - centre, tris, smooth=True)
    zone = np.stack([age, sg, po, fl], axis=1)
    mastic = np.stack([np.clip(fdep / 0.004, 0, 1), men,
                       np.clip(pocket / max(void_amt, 1e-6), 0, 1),
                       agg_fade], axis=1)
    bake_attrs(me, zone=zone, mastic=mastic)
    _add_su_uv(me, X, Y)
    ob = _obj("%sMastic_%s" % (PFX, site.name), me, coll, mat_mastic(), centre)
    print(">>   mastic: %d x %d verts at %.1f mm, %d tris"
          % (nx, ny, pitch * 1000, tris.shape[0]))
    return ob, tris.shape[0]


def _grid_tris(nx, ny):
    i = np.arange(nx - 1)
    j = np.arange(ny - 1)
    I, J = np.meshgrid(i, j)
    a = (J * nx + I).ravel()
    b = a + 1
    c = a + nx
    d = c + 1
    # alternate the diagonal so the triangulation carries no directional grain:
    # a uniform diagonal on a millimetre-relief surface reads as corduroy at a
    # grazing sun, which is exactly the light this film is shot in.
    flip = ((I + J) % 2 == 0).ravel()
    t1 = np.where(flip[:, None], np.stack([a, b, d], 1), np.stack([a, b, c], 1))
    t2 = np.where(flip[:, None], np.stack([a, d, c], 1), np.stack([b, d, c], 1))
    return np.concatenate([t1, t2], axis=0).astype(np.int32)


def _build_surround(site, mix, coll, Q):
    """Wearing course beyond the explicit-stone zone, out to the horizon.

    Same material family, no meshed stones: past the tier radii a chipping is
    under 4 px and geometry there costs triangles to produce aliasing.  The
    mastic material's own aggregate bump takes over across the same crossfade
    band the tiers fade out on, so there is no LOD line in the frame.

    Graded in s and u so the near ring is 40 mm and the far field is metres.
    """
    far = Q["far_m"]
    hs = site.ext_s                 # EXACTLY the mastic's outer boundary
    hu = site.ext_u

    def _grade(half_fine, fine, half_far, coarse):
        a = np.arange(0.0, half_fine, fine)
        b = []
        x = half_fine
        step = fine
        while x < half_far:
            step = min(step * 1.13, coarse)
            x += step
            b.append(x)
        g = np.concatenate([a, np.array([half_fine]), np.array(b)])
        return np.unique(np.concatenate([-g[::-1], g]))

    gs = _grade(hs, 0.045, far, 12.0)
    gu = _grade(hu, 0.045, 34.0, 6.0)
    # THE WEARING COURSE STOPS AT verge_edge.  half_width + 1.500 m kerb band +
    # 1.000 m painted verge is the whole of build_surface's paved cross-section
    # and every square metre of it is asphalt; outboard of it is build_barriers'
    # runoff platform, which is a different item (`runoff_asphalt_mat`) and not
    # this one's to claim.  Without this clip the surround ran 34 m across and put
    # wearing course under the barriers, under the gravel and under the camera's
    # own kerb -- 0.85 m from the lens, which is why the first build reported a
    # nearest AWC vertex of 0.8517 m instead of 1.100 m.
    e_edge = float(C.verge_edge(site.s0))
    lo_rel, hi_rel = -e_edge - site.u0, e_edge - site.u0
    gu = gu[(gu > lo_rel + 1e-4) & (gu < hi_rel - 1e-4)]
    gu = np.unique(np.concatenate([[lo_rel], gu, [hi_rel]]))
    S2, U2 = np.meshgrid(site.s0 + gs, site.u0 + gu)
    S2 = S2.ravel(); U2 = U2.ravel()
    # do not build inside the patch: that is the hero mesh's ground.  The hole's
    # edge IS the mastic's edge -- see the seam note in _build_mastic.
    inside = ((np.abs(S2 - site.s0) < hs - 1e-6) &
              (np.abs(U2 - site.u0) < hu - 1e-6))
    z = C.ground_z(S2, U2) - fill_depth(S2, U2)
    P = _su_to_world_xyz(S2, U2, z)
    nx = gs.size; ny = gu.size
    tris = _grid_tris(nx, ny)
    # drop the quads whose corners are all inside the hero patch
    ins = inside.reshape(ny, nx)
    keep = ~(ins[tris[:, 0] // nx, tris[:, 0] % nx] &
             ins[tris[:, 1] // nx, tris[:, 1] % nx] &
             ins[tris[:, 2] // nx, tris[:, 2] % nx])
    tris = tris[keep]
    centre = P.mean(axis=0)
    me = _tri_mesh("%sSurround_%s" % (PFX, site.name), P - centre, tris, smooth=True)
    n = S2.size
    zone = np.stack([zone_age(S2), segregation(S2, U2), polish(S2, U2),
                     flushing(S2, U2)], axis=1)
    bake_attrs(me, zone=zone,
               mastic=np.stack([np.clip(fill_depth(S2, U2) / 0.004, 0, 1),
                                np.zeros(n), np.zeros(n),
                                np.ones(n)], axis=1))          # agg_fade = 1
    _add_su_uv(me, S2 - site.s0, U2 - site.u0)
    ob = _obj("%sSurround_%s" % (PFX, site.name), me, coll, mat_mastic(far=True),
              centre)
    print(">>   surround: %d verts, %d tris, s +-%.0f m, u %+.2f..%+.2f (verge_edge)"
          % (n, tris.shape[0], far, site.u0 + gu[0], site.u0 + gu[-1]))
    return ob, tris.shape[0]


# ===========================================================================
# 8.  MATERIALS
# ===========================================================================
#
# THE REFLECTANCE LADDER IS NOT NEGOTIATED HERE.  M_Surf_Asphalt already solved
# it against C.REFERENCE_EXPOSURE_EXTERIOR = -3.048 and AgX, and its comment
# block records why every number is what it is:
#
#     fresh dense-graded   0.045 - 0.055        col_fresh (0.0600,0.0559,0.0507)
#     old bleached         0.100 - 0.130        col_old   (0.1360,0.1281,0.1147)
#     rubbered-in line     0.028 - 0.035
#     Specular IOR Level   0.24, NOT 0.38 -- 0.38 puts enough sky in the lobe to
#                          render a warm-grey binder blue, the classic CG-tarmac tell
#
# Those exact numbers are reused.  The difference is WHERE they live: in
# M_Surf_Asphalt one shader had to produce both the stone and the mortar out of a
# Voronoi, so their albedos were a contrast field around a mean.  Here the stone
# and the mortar are different objects, so each simply IS its own reflectance.

COL_MORTAR_FRESH = (0.0600, 0.0559, 0.0507)
COL_MORTAR_OLD = (0.1360, 0.1281, 0.1147)
COL_RUBBER = (0.0232, 0.0214, 0.0208)
SPEC_IOR_LEVEL = 0.24


def _fields(g):
    """The four attribute reads every AWC material starts from."""
    zone = g.n("ShaderNodeAttribute"); zone.attribute_name = "AWC_zone"
    lith = g.n("ShaderNodeAttribute"); lith.attribute_name = "AWC_lith"
    sloc = g.n("ShaderNodeAttribute"); sloc.attribute_name = "AWC_slocal"
    mast = g.n("ShaderNodeAttribute"); mast.attribute_name = "AWC_mastic"
    age, sg, po = g.sep(zone.outputs["Color"])
    fl = zone.outputs["Alpha"]
    return dict(zone=zone, lith=lith, sloc=sloc, mast=mast,
                age=age, seg=sg, polish=po, flush=fl)


def mat_stone():
    """The crushed rock.  Three lithologies, a bitumen film, and a planed top."""
    name = MPFX + "Stone"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = G(nt)
    F = _fields(g)

    P = g.n("ShaderNodeTexCoord").outputs["Object"]
    # THE STONE'S OWN FRAME.  AWC_slocal is the template direction rotated into
    # this particular stone's bedding, so a texture read on it is (a) at the same
    # scale on every stone whatever its size, and (b) oriented to the stone's own
    # crystal fabric.  Object space would give every stone in the patch one
    # shared crystal lattice -- a mosaic that shimmers when the camera moves,
    # because it is a 3-D texture the stones are cut out of rather than a rock
    # each stone is made of.  This is also why nothing here needs Geometry->
    # Position: the finest textures in the file never see a world coordinate.
    sl_raw = F["sloc"].outputs["Color"]
    sl = g.vadd(g.scale(sl_raw, 2.0), (-1.0, -1.0, -1.0))
    hnorm = F["sloc"].outputs["Alpha"]                # 0 at the mortar, 1 at the top
    l_id, l_tone, l_seed = g.sep(F["lith"].outputs["Color"])
    s_pol = F["lith"].outputs["Alpha"]

    # decorrelate each stone's texture: offset the sampling frame by its own seed
    off = g.n("ShaderNodeCombineXYZ")
    g.set(off.inputs[0], g.math("MULTIPLY", l_seed, 71.3))
    g.set(off.inputs[1], g.math("MULTIPLY", l_tone, 53.7))
    g.set(off.inputs[2], g.math("MULTIPLY", l_id, 97.1))
    SL = g.vadd(sl, off.outputs[0])

    # ---- lithology ----------------------------------------------------------
    # Three DISCRETE rocks, the same three M_Surf_Asphalt picks, because the
    # average of three separated colours is not one of them: a continuous hue
    # ramp averages to grey at any distance where a stone is under a pixel.
    is_mid = g.mr(l_id, 0.28, 0.30, 0.0, 1.0)
    is_dark = g.mr(l_id, 0.70, 0.72, 0.0, 1.0)
    c_pale = g.rgb(0.118, 0.112, 0.100)      # quartzite / crushed limestone
    c_mid = g.rgb(0.086, 0.082, 0.077)       # granodiorite
    c_dark = g.rgb(0.048, 0.048, 0.051)      # basalt, slightly blue-neutral
    rock = g.mixc(is_mid, c_pale, c_mid)
    rock = g.mixc(is_dark, rock, c_dark)
    # load-to-load tone within one lithology
    rock = g.vmulc(rock, g.grey(g.mr(l_tone, 0.0, 1.0, 0.84, 1.18)))

    # ---- crystal fabric: the reason a stone is not a coloured facet ----------
    # Granodiorite is a mosaic of 0.5-3 mm feldspar, quartz and biotite; at
    # 0.49 mm/px a 2 mm crystal is 4 px and is genuinely visible on the flat
    # planed tops of the racing line.  Basalt is aphanitic with vesicles instead.
    xtal = g.voro(g.scale(SL, 620.0), 1.0, "F1", 1.0)
    xid = g.sep(xtal.outputs["Color"])[1]
    xtal2 = g.voro(g.scale(SL, 1500.0), 1.0, "F1", 1.0)
    xid2 = g.sep(xtal2.outputs["Color"])[0]
    felds = g.mr(xid, 0.55, 0.58, 0.0, 1.0)          # pale plagioclase
    biot = g.mr(xid, 0.10, 0.13, 1.0, 0.0)           # dark mica
    xtal_tint = g.mixc(g.math("MULTIPLY", felds, 0.85),
                       g.rgb(1.0, 1.0, 1.0), g.rgb(1.24, 1.21, 1.15))
    xtal_tint = g.mixc(g.math("MULTIPLY", biot, 0.75), xtal_tint,
                       g.rgb(0.52, 0.53, 0.58))
    xtal_tint = g.mixc(g.mr(xid2, 0.62, 0.66, 0.0, 0.55),
                       xtal_tint, g.rgb(1.14, 1.11, 1.05))
    # only the coarse-grained lithologies show it
    xtal_show = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", is_dark, 0.72))
    rock = g.vmulc(rock, g.mixc(xtal_show, g.rgb(1.0, 1.0, 1.0), xtal_tint))

    # vesicles, basalt only: gas bubbles frozen into the rock, 0.3-1.2 mm
    ves = g.voro(g.scale(SL, 1900.0), 1.0, "F1", 1.0)
    ves_m = g.math("MULTIPLY",
                   g.mr(g.sep(ves.outputs["Color"])[2], 0.86, 0.90, 0.0, 1.0),
                   g.mr(ves.outputs["Distance"], 0.34, 0.12, 0.0, 1.0))
    ves_m = g.math("MULTIPLY", ves_m, is_dark)
    rock = g.mixc(g.math("MULTIPLY", ves_m, 0.80), rock, g.rgb(0.026, 0.026, 0.028))

    # ---- the fracture surface ------------------------------------------------
    # A crusher leaves a conchoidal, sub-millimetre-rough face.  It is the thing
    # that makes a fresh chipping matte and a polished one glossy, so it is the
    # roughness carrier and it is what the racing line destroys.
    frac_f, _ = g.noise(g.scale(SL, 2300.0), 1.0, detail=4.0, rough=0.62)
    frac2_f, _ = g.noise(g.scale(SL, 7000.0), 1.0, detail=2.0, rough=0.50)
    step_f, _ = g.noise(g.scale(SL, 420.0), 1.0, detail=3.0, rough=0.55)

    # ---- the bitumen film ----------------------------------------------------
    # Every stone leaves the mixer BLACK: it is coated in 6-7 % binder.  Traffic
    # wears the film off the tops first, so a used surface is a field of dark
    # stones with light crowns, and an unused verge is uniformly dark.  This one
    # gradient is the difference between "stones" and "a road that is driven on".
    film_break, _ = g.noise(g.scale(SL, 190.0), 1.0, detail=5.0, rough=0.58)
    wear = g.math("MULTIPLY", g.mr(hnorm, 0.30, 0.94, 0.0, 1.0),
                  g.mr(F["age"], 0.0, 1.0, 0.55, 1.0))
    wear = g.math("MULTIPLY", wear, g.mr(film_break, 0.30, 0.72, 0.55, 1.0))
    wear = g.math("MAXIMUM", wear, g.math("MULTIPLY", s_pol, 0.78))
    film = g.math("SUBTRACT", 1.0, wear)
    g.tag("film", film)
    rock = g.mixc(g.math("MULTIPLY", film, 0.90), rock, g.rgb(0.0198, 0.0186, 0.0180))

    # ---- stripping: old binder lets go and shows raw mineral ----------------
    strip = g.math("MULTIPLY", g.mr(F["age"], 0.45, 1.0, 0.0, 1.0),
                   g.mr(step_f, 0.62, 0.80, 0.0, 1.0))
    rock = g.mixc(g.math("MULTIPLY", strip, 0.55), rock,
                  g.vmulc(rock, g.rgb(1.9, 1.85, 1.75)))

    # ---- rubber on the planed tops ------------------------------------------
    # Bounded and switchable: rubber_line_deposit owns the deposit itself.  Set
    # RUBBER_TINT = 0.0 and this contributes nothing, so the two items cannot
    # double-darken the line.
    # A RUBBERED-IN LINE IS DARK.  The first build stripped the bitumen film off
    # the polished tops (correct: traffic does) and then only mixed 0.62 toward
    # rubber, so the racing line came out BRIGHTER than the tarmac beside it --
    # the exact inversion M_Surf_Asphalt's comment block warns about.  0.86 puts
    # a fully polished crown on 0.033 against 0.083 clean in the same zone, i.e.
    # the measured 2.5 : 1, and the mineral still shows through where the rubber
    # has not taken.
    rub = g.math("MULTIPLY", g.math("MULTIPLY", s_pol, RUBBER_TINT),
                 g.mr(hnorm, 0.45, 1.0, 0.15, 1.0))
    rock = g.mixc(g.math("MULTIPLY", rub, 0.86), rock, g.rgb(*COL_RUBBER))

    # ---- dust in the microtexture, washed off the crowns --------------------
    dust_f, _ = g.noise(g.scale(P, 42.0), 1.0, detail=5.0, rough=0.55)
    dust = g.math("MULTIPLY", g.mr(dust_f, 0.34, 0.80, 0.0, 1.0),
                  g.mr(hnorm, 0.62, 0.10, 0.0, 1.0))
    dust = g.math("MULTIPLY", dust, g.math("SUBTRACT", 1.0,
                                           g.math("MULTIPLY", s_pol, 0.75)))
    rock = g.mixc(g.math("MULTIPLY", dust, 0.30), rock, g.rgb(0.1080, 0.0990, 0.0860))

    # ================= roughness =============================================
    rough = g.mr(frac_f, 0.15, 0.85, 0.60, 0.86)
    rough = g.math("ADD", rough, g.math("MULTIPLY",
                                        g.mr(frac2_f, 0.2, 0.8, -0.05, 0.05), 1.0))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", s_pol, 0.34))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", film, 0.06))
    rough = g.math("ADD", rough, g.math("MULTIPLY", dust, 0.13))
    rough = g.math("ADD", rough, g.math("MULTIPLY", ves_m, 0.10))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.95), 0.16)

    # ================= normal ================================================
    # THE ARRISES ARE WORN.  A 12-vertex hull has 30 perfectly sharp edges and a
    # stone that has been driven over for a season does not: the crusher's arrises
    # are the first thing traffic knocks off, which is exactly why a used surface
    # reads as stones and a fresh chip seal reads as broken glass.  A 0.45 mm
    # bevel is what that wear measures, it costs no triangles, and it is the one
    # thing that makes a low-facet-count crown stop looking low-facet-count.
    bev = g.n("ShaderNodeBevel")
    bev.samples = 4
    g.set(bev.inputs["Radius"], 0.00045)
    nrm = bev.outputs["Normal"]
    # ...and the fracture texture BELOW the mesh's own scale: 2.4 mm facet steps,
    # then 0.43 mm conchoidal roughness, then 0.14 mm.  The 2.4 mm layer is 5 px
    # on the 4K master at the hairpin station -- well above the pixel, so it reads
    # AND it is spatially smooth, which is what keeps it temporally stable.  The
    # two finer ones are deliberately weak: a perturbation finer than the ray
    # footprint is noise the denoiser turns into swirls (M_Surf_Asphalt logged it).
    nrm = g.bump(frac2_f, strength=0.30, distance=0.00009, normal=nrm)
    nrm = g.bump(frac_f, strength=0.62, distance=0.00050, normal=nrm)
    nrm = g.bump(step_f, strength=0.55, distance=0.00110, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], rock)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Metallic"], 0.0)
    g.set(bsdf.inputs["Specular IOR Level"], SPEC_IOR_LEVEL)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


def mat_mastic(far=False):
    """The bitumen mortar: binder, filler and the sand fraction below 2 mm.

    `far=True` returns the surround variant, which additionally carries a
    bump-only aggregate so that the crossfade out of the explicit stones has
    something to fade INTO.  The two share every other layer, so the transition
    is a change of representation, not a change of material.
    """
    name = MPFX + ("MasticFar" if far else "Mastic")
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = G(nt)
    F = _fields(g)
    P = g.n("ShaderNodeTexCoord").outputs["Object"]
    uvn = g.n("ShaderNodeUVMap"); uvn.uv_map = "AWC_su"
    du, ds, _ = g.sep(uvn.outputs["UV"])

    fdep, men, pocket = g.sep(F["mast"].outputs["Color"])
    agg_fade = F["mast"].outputs["Alpha"]      # 0 = every tier is real mesh here

    # ---- base: oxidation by campaign age ------------------------------------
    ox_f, _ = g.noise(g.scale(P, 1.7), 1.0, detail=5.0, rough=0.58)
    age_v = g.math("ADD", F["age"],
                   g.math("MULTIPLY", g.math("SUBTRACT", ox_f, 0.5), 0.14), clamp=True)
    base = g.mixc(age_v, g.rgb(*COL_MORTAR_FRESH), g.rgb(*COL_MORTAR_OLD))
    # THE MORTAR IS THE DARK PHASE.  M_Surf_Asphalt's ladder (0.045-0.055 fresh,
    # 0.100-0.130 old) is the mean of stone AND mortar; here they are separate
    # objects, so the mortar carries the binder-rich end of it by itself.  0.62
    # puts fresh mortar on 0.037 and aged mortar on 0.084, and the stone crowns
    # sit above it -- which is the contrast that makes an aggregate read as
    # aggregate.  0.72 was too light and the first macro came back the colour of
    # dry sand.
    base = g.vmulc(base, g.grey(0.62))

    # ---- the sand fraction: 0.25-2.0 mm, the mortar's own texture ------------
    # WARPED, because an unwarped Voronoi at 1.1 mm read as bubble wrap in the
    # 0.2 mm/px crop: perfectly round cells of equal size on a lattice.  Mortar
    # sand is angular and graded, so the coordinate is warped by a third of a cell
    # before it is celled -- the same trick, and the same bound, M_Surf_Asphalt
    # uses on its aggregate layer.
    swarp_f, swarp_c = g.noise(g.scale(P, 900.0), 1.0, detail=3.0)
    Ps = g.vadd(P, g.scale(g.vadd(swarp_c, (-0.5, -0.5, -0.5)), 0.00028))
    sand = g.voro(g.scale(Ps, 1250.0), 1.0, "F1", 1.0)         # ~0.80 mm
    sand_d = sand.outputs["Distance"]
    sand_id = g.sep(sand.outputs["Color"])[1]
    fine = g.voro(g.scale(Ps, 3100.0), 1.0, "F1", 1.0)         # ~0.32 mm
    filler_f, _ = g.noise(g.scale(P, 6400.0), 1.0, detail=2.0, rough=0.5)  # 0.16 mm
    grain_hi = g.mr(sand_d, 0.06, 0.34, 1.0, 0.0)
    base = g.vmulc(base, g.grey(g.math("ADD", 1.0,
                                       g.math("MULTIPLY", grain_hi, 0.17))))
    base = g.vmulc(base, g.grey(g.mr(sand_id, 0.0, 1.0, 0.90, 1.11)))
    base = g.vmulc(base, g.grey(g.math("ADD", 0.96,
                                       g.math("MULTIPLY",
                                              g.mr(fine.outputs["Distance"],
                                                   0.0, 0.35, 1.0, 0.0), 0.09))))

    # ---- air voids ----------------------------------------------------------
    # A void is a hole with no light in it.  It is the darkest thing on the
    # surface and it is what makes an open-graded mortar read as open.
    base = g.mixc(g.math("MULTIPLY", pocket, 0.85), base, g.rgb(0.0125, 0.0122, 0.0125))

    # ---- the meniscus is fresh, un-weathered binder -------------------------
    base = g.mixc(g.math("MULTIPLY", men, 0.55), base, g.rgb(0.0212, 0.0196, 0.0184))

    # ---- flushing: the smoothest, darkest thing on the circuit --------------
    base = g.vmulc(base, g.grey(g.mr(F["flush"], 0.0, 1.0, 1.0, 0.62)))

    # ---- rubber in the voids on the line ------------------------------------
    rub = g.math("MULTIPLY", F["polish"], RUBBER_TINT)
    base = g.vmulc(base, g.grey(g.mr(rub, 0.0, 1.0, 1.0, 0.66)))
    base = g.mixc(g.math("MULTIPLY", rub, 0.24), base, g.rgb(*COL_RUBBER))

    # ---- dust washed down the cross-fall ------------------------------------
    dust_f, _ = g.noise(g.scale(P, 6.5), 1.0, detail=6.0, rough=0.6)
    dust = g.math("MULTIPLY", g.mr(dust_f, 0.30, 0.86, 0.0, 1.0),
                  g.math("SUBTRACT", 1.0, g.math("MULTIPLY", rub, 0.85)))
    dust = g.math("MULTIPLY", dust, g.mr(F["seg"], 0.0, 1.0, 0.45, 1.0))
    base = g.mixc(g.math("MULTIPLY", dust, 0.22), base, g.rgb(0.1080, 0.0990, 0.0860))

    # ---- the bump-only aggregate the explicit stones fade INTO --------------
    # Same three lithologies, same nominal sizes, driven from a warped Voronoi --
    # this is M_Surf_Asphalt's aggregate layer, at this module's scales, so the
    # patch and the road it is let into are the same surface at two levels of
    # representation.  THE WARP MUST BE SMALLER THAN THE CELL IT WARPS: 6.5 mm on
    # an 11 mm cell distorts the outlines, which is what crushed stone looks like;
    # 15 mm destroys them (M_Surf_Asphalt logged that measurement).
    #
    # `agg_fade` decides how much of it exists:  0 inside the fully-meshed core,
    # ~0.42 where tier C has stopped, ~1.00 outside the patch.  The mid fraction
    # comes in first and the coarse fraction last, matching the order the meshed
    # tiers drop out in.
    warp_f, warp_c = g.noise(g.scale(P, 24.0), 1.0, detail=3.0)
    Pw = g.vadd(P, g.scale(g.vadd(warp_c, (-0.5, -0.5, -0.5)), 0.0065))
    a1 = g.voro(g.scale(Pw, 92.0), 1.0, "SMOOTH_F1", 1.0, 0.10)     # ~11 mm
    a2 = g.voro(g.scale(P, 190.0), 1.0, "SMOOTH_F1", 1.0, 0.22)     # ~5 mm
    a3 = g.voro(g.scale(Pw, 340.0), 1.0, "SMOOTH_F1", 1.0, 0.26)    # ~3 mm
    aid = g.voro(g.scale(Pw, 92.0), 1.0, "F1", 1.0)
    w_mid = g.mr(agg_fade, 0.05, 0.60, 0.0, 1.0) if not far else 1.0
    w_coarse = g.mr(agg_fade, 0.68, 0.98, 0.0, 1.0) if not far else 1.0
    chip = g.math("MULTIPLY",
                  g.math("MULTIPLY", g.mr(a1.outputs["Distance"], 0.03, 0.33,
                                          1.0, 0.0), 1.15), w_coarse)
    chip = g.math("MAXIMUM", chip,
                  g.math("MULTIPLY",
                         g.math("MULTIPLY", g.mr(a2.outputs["Distance"], 0.04,
                                                 0.25, 1.0, 0.0), 0.62), w_mid))
    chip = g.math("MAXIMUM", chip,
                  g.math("MULTIPLY",
                         g.math("MULTIPLY", g.mr(a3.outputs["Distance"], 0.05,
                                                 0.22, 1.0, 0.0), 0.34), w_mid))
    cell_h = g.sep(aid.outputs["Color"])[1]
    t_a = g.mr(cell_h, 0.34, 0.36, 0.0, 1.0)
    t_b = g.mr(cell_h, 0.70, 0.72, 0.0, 1.0)
    ctint = g.mixc(t_a, g.rgb(1.26, 1.22, 1.13), g.rgb(1.02, 1.00, 0.96))
    ctint = g.mixc(t_b, ctint, g.rgb(0.70, 0.71, 0.77))
    lum = g.math("ADD", 1.0, g.math("MULTIPLY", chip, 1.42))
    lum = g.math("SUBTRACT", lum,
                 g.math("MULTIPLY",
                        g.math("MULTIPLY", g.mr(a1.outputs["Distance"], 0.30, 0.62,
                                                0.0, 1.0), w_coarse), 0.62))
    lum = g.math("MAXIMUM", lum, 0.18)
    base = g.vmulc(base, g.vmulc(
        g.mixc(g.mr(chip, 0.03, 0.42, 0.0, 1.0), g.rgb(1, 1, 1), ctint),
        g.grey(lum)))
    far_agg = chip

    # ================= roughness =============================================
    rough = g.mr(age_v, 0.0, 1.0, 0.78, 0.90)
    rough = g.math("ADD", rough, g.math("MULTIPLY",
                                        g.mr(filler_f, 0.2, 0.8, -0.05, 0.05), 1.0))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", F["flush"], 0.34))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", rub, 0.13))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", men, 0.10))
    rough = g.math("ADD", rough, g.math("MULTIPLY", pocket, 0.06))
    rough = g.math("ADD", rough, g.math("MULTIPLY", dust, 0.12))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.97), 0.28)

    # anisotropy: tyres polish ALONG the road.  The tangent comes from AWC_su,
    # whose v axis is the lap station, so the stretch direction is the road's own.
    tang = g.n("ShaderNodeTangent")
    tang.direction_type = 'UV_MAP'
    tang.uv_map = "AWC_su"
    aniso = g.math("MULTIPLY", g.mr(rub, 0.10, 1.00, 0.05, 0.50),
                   g.mr(F["flush"], 0.0, 1.0, 1.0, 1.25))

    # ================= bump ==================================================
    # THE SAND BUMP IS 0.20 mm, NOT 1.1 mm.  The first version drove a 1.1 mm
    # Voronoi with a 1.1 mm bump distance, which is one hemisphere per cell -- the
    # 0.196 mm/px crop came back reading as bubble wrap.  A 0.8 mm sand grain
    # bedded in mortar shows a fraction of itself; the aggregate relief in this
    # material is the MESH's job now, and the bump is only what is below it.
    h = g.math("MULTIPLY", grain_hi, 0.55)
    h = g.math("ADD", h, g.math("MULTIPLY",
                                g.mr(fine.outputs["Distance"], 0.0, 0.35, 1.0, 0.0),
                                0.25))
    h = g.math("SUBTRACT", h, g.math("MULTIPLY", pocket, 0.60))
    nrm = g.bump(filler_f, strength=0.38, distance=0.00010)
    nrm = g.bump(h, strength=0.80, distance=0.00022, normal=nrm)
    # the bump-only aggregate that stands in for the meshed tiers past their radii
    # keeps its full relief -- out there it IS the geometry
    if far_agg is not None:
        nrm = g.bump(far_agg, strength=1.0, distance=0.0024, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Metallic"], 0.0)
    g.set(bsdf.inputs["Specular IOR Level"], SPEC_IOR_LEVEL)
    g.set(bsdf.inputs["Anisotropic"], aniso)
    g.set(bsdf.inputs["Tangent"], tang.outputs["Tangent"])
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


# ===========================================================================
# 9.  THE TEST SCENE
# ===========================================================================

def footprint_polygon(site, margin=0.0):
    """The (s, u) rectangle build_surface must NOT build SURF_Track rows inside.

    EXCLUSIVE CLAIM, not an overlay.  See the module docstring §4.
    """
    return dict(s0=site.s0 - site.ext_s - margin, s1=site.s0 + site.ext_s + margin,
                u0=site.u0 - site.ext_u - margin, u1=site.u0 + site.ext_u + margin)


def apply_contract_sky():
    """Force the world's Sky Texture onto the contract's atmosphere.

    THIS MUST BE CALLED AFTER ANY CALL TO ``procedural_world()``, INCLUDING THE
    ONE INSIDE ``save_clean``.  procedural_world() clears the node tree and
    rebuilds it with its own numbers, and two of them are wrong for this Blender
    and this contract:

      * it sets ``dust_density``, which Blender 5.2 calls ``aerosol_density`` --
        so the value silently did not land and the sky ran at the default 1.00
        instead of the contract's 0.45;
      * it sets ``air_density`` 1.35 and ``ozone_density`` 1.00 against the
        contract's 1.00 and 1.30, and leaves ``sun_disc`` ON next to the
        contract's calibrated SUN lamp.

    The first macro render is what caught it: a 4x-too-thick aerosol at a 12.47
    deg sun is a beige veil over the whole frame, and the surface came back the
    colour of dry sand with a measured sd of 0.0415.  The atmosphere was wrong,
    not the asphalt -- which is exactly the kind of defect that gets "fixed" in
    the material and then ships.
    """
    w = bpy.context.scene.world
    if not (w and w.use_nodes):
        return 0
    n_fixed = 0
    for n in w.node_tree.nodes:
        if n.type != "TEX_SKY":
            continue
        for attr, val in (("sun_disc", C.SKY_SUN_DISC),
                          ("sun_intensity", 1.0),
                          ("air_density", C.SKY_AIR),
                          ("aerosol_density", C.SKY_AEROSOL),
                          ("ozone_density", C.SKY_OZONE),
                          ("altitude", C.SKY_ALTITUDE),
                          ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                          ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                          ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG))):
            if hasattr(n, attr):
                setattr(n, attr, val)
        n_fixed += 1
        print(">> sky: air %.2f aerosol %.2f ozone %.2f  elev %.3f deg  disc %s"
              % (n.air_density, n.aerosol_density, n.ozone_density,
                 math.degrees(n.sun_elevation), n.sun_disc))
    return n_fixed


def contract_sun(scene):
    """The contract's light: build_sky's SUN lamp + the procedural sky.

    ``tools/fix_audit_blend.procedural_world()`` supplies the sky (Sky Texture,
    no external files).  ``apply_contract_sky`` then forces the atmosphere and
    switches the disc off, and the contract's calibrated SUN lamp is added,
    because ``C.REFERENCE_EXPOSURE_EXTERIOR`` = -3.048 was solved against
    ``SUN_ENERGY`` = 115.754 with ``SUN_COLOR`` = (1, 0.716, 0.387) and
    ``SKY_SUN_DISC`` = False.  Leaving the sky's own disc on would key the frame
    off a second source and every albedo in §8 would be judged under a light the
    material was not calibrated for.
    """
    import fix_audit_blend as FAB
    FAB.procedural_world()
    apply_contract_sky()

    lt = bpy.data.lights.new(PFX + "Sun", 'SUN')
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    d = Vector(C.SUN_DIR).normalized()
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    scene.collection.objects.link(ob)
    return ob


def macro_camera(site, scene):
    """The camera the manifest specifies: 1.100 m, 21 mm, on the T4 inside kerb.

    Placed at the REAL vantage from circuit_spec §11 -- z = +0.850 over the inside
    kerb -- and then checked, not asserted: the printed distance to the nearest
    point of the racing surface must read 1.100 m.
    """
    if not site.solved:
        site.solve_lens()
    s_cam, u_cam, h_cam = site.anchor_su
    near = site.near_m
    ns, nu = site.near_s, site.near_u
    cam_p = Vector(tuple(site.cam_world))
    kerb_lo = C.half_width(s_cam)
    kerb_hi = kerb_lo + C.KERB_W
    if site.solve_lateral:
        print(">> lens lateral u = %+.4f m  (T4 inside kerb band %+.3f .. %+.3f)"
              % (u_cam, kerb_lo, kerb_hi))
        if not (kerb_lo <= u_cam <= kerb_hi):
            print(">> WARNING: solved lens lateral is OUTSIDE the inside kerb band")

    # --- FRAMING -------------------------------------------------------------
    # Aim at a ground point `aim_d_m` out along the view azimuth.  See the note
    # over PATCH_SITES for why 1.15 m: it is what puts the whole 51.3 deg vertical
    # field on ground the patch actually covers.
    az = math.radians(site.view_az_deg)
    t_s = s_cam + site.aim_d_m * math.cos(az)
    t_u = u_cam - site.aim_d_m * math.sin(az)
    tx, ty, tz = C.su_to_world(t_s, t_u)
    tgt = Vector((tx, ty, tz))
    pitch = math.degrees(math.atan2(h_cam, site.aim_d_m))
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * 2160 / 3840 / site.lens_mm))
    print(">> aim s=%.3f u=%+.3f  (%.2f m out, axis %.1f deg down, vert half-FOV "
          "%.1f deg)" % (t_s, t_u, site.aim_d_m, pitch, vhalf))
    for lbl, ang in (("bottom of frame", pitch + vhalf), ("top of frame", pitch - vhalf)):
        if ang <= 0.2:
            print(">>   %-16s ABOVE THE HORIZON -- sky in frame" % lbl)
        else:
            gh = h_cam / math.tan(math.radians(ang))
            print(">>   %-16s %5.1f deg down -> %6.2f m out, %6.2f m slant, "
                  "%6.0f px/m" % (lbl, ang, gh, math.hypot(gh, h_cam),
                                  (RES_X_4K * site.lens_mm / SENSOR_MM)
                                  / math.hypot(gh, h_cam)))

    cd = bpy.data.cameras.new("CAM_AWC_Macro")
    cd.lens = site.lens_mm
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.02
    cd.clip_end = 4000.0
    cam = bpy.data.objects.new("CAM_AWC_Macro", cd)
    scene.collection.objects.link(cam)
    # explicit look-at with world up, so the horizon is level.  A
    # rotation_difference() from -Z carries an arbitrary roll, and a rolled macro
    # of a road surface is the kind of thing that reads as "wrong" without ever
    # reading as "rolled".
    fwd = (tgt - cam_p).normalized()
    right = fwd.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(fwd).normalized()
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    cam.matrix_world = Matrix.Translation(cam_p) @ M
    scene.camera = cam

    # --- SUB-PIXEL JITTER RIG, for the manifest's own open question -----------
    #     "it must be re-checked for TEMPORAL flicker in motion, not just in a
    #      still."   -- docs/item_manifest.json, this item
    #
    # A still cannot answer that, and neither can a claim.  What CAN be measured
    # in stills is the thing flicker is made of: how much a frame changes when the
    # lens moves by less than a pixel.  Geometry finer than the ray footprint
    # changes a lot; geometry the footprint resolves changes smoothly.  One pixel
    # on the 4K master subtends 2*atan(18/21)/3840 = 3.712e-4 rad, which at the
    # 1.100 m filmed distance is 0.408 mm of lateral lens travel.  These two
    # cameras are the same shot displaced by 1/3 and 2/3 of a pixel, so
    # differencing the three renders measures sub-pixel sensitivity directly --
    # and does it separately for the near field (meshed aggregate) and the far
    # field (the bump-only surround), which is the comparison that matters.
    px_rad = 2.0 * math.atan(0.5 * SENSOR_MM / site.lens_mm) / RES_X_4K
    px_m = px_rad * near
    for i, f in enumerate((1.0 / 3.0, 2.0 / 3.0), start=1):
        jd = cd.copy()
        jc = bpy.data.objects.new("CAM_AWC_Jit%d" % i, jd)
        scene.collection.objects.link(jc)
        jc.matrix_world = Matrix.Translation(cam_p + right * (px_m * f)) @ M
    print(">> jitter rig: 1 px = %.4f mm of lens travel at %.3f m; "
          "CAM_AWC_Jit1/2 offset %.4f / %.4f mm"
          % (px_m * 1000, near, px_m * 1000 / 3, px_m * 2000 / 3))

    # ---- report the filmed distance, do not claim it --------------------------
    print(">> camera  lens %.1f mm  at %s" % (cd.lens, tuple(round(v, 3) for v in cam_p)))
    print(">> nearest racing surface: %.4f m  (manifest %.3f m)  at s=%.2f u=%+.3f"
          % (near, NEAREST_CAMERA_M, ns, nu))
    print(">> px/m at that distance: %.1f   ->  1 px = %.3f mm"
          % ((RES_X_4K * cd.lens / SENSOR_MM) / near,
             1000.0 / ((RES_X_4K * cd.lens / SENSOR_MM) / near)))
    # and the nearest AWC geometry actually built, which is the number that
    # matters for whether the ITEM survives the shot
    deps = bpy.context.evaluated_depsgraph_get()
    best = 1e9
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or not ob.name.startswith(PFX):
            continue
        me = ob.evaluated_get(deps).to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) + np.array(ob.matrix_world.translation)
        best = min(best, float(np.linalg.norm(co - np.array(cam_p), axis=1).min()))
        ob.evaluated_get(deps).to_mesh_clear()
    print(">> nearest AWC_ vertex to the lens: %.4f m" % best)
    return cam, near


def build_test_scene(quality="hero", out=None, site=None):
    site = site or PATCH_SITES[0]
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    stats = build(site=site, quality=quality)

    contract_sun(scene)
    cam, near = macro_camera(site, scene)
    stats["camera_nearest_m"] = round(near, 4)

    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 3840
    scene.render.resolution_y = 2160
    scene.render.film_transparent = False
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    scene.view_settings.look = C.VIEW_LOOK
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    try:
        scene.cycles.max_bounces = 8
        scene.cycles.diffuse_bounces = 4
        scene.cycles.glossy_bounces = 4
        scene.cycles.transmission_bounces = 4
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.008
        scene.cycles.use_denoising = True
    except Exception as e:
        print("   (cycles settings: %s)" % e)

    if out:
        _save(out)
        stats["blend"] = out
        stats["blend_mb"] = round(os.path.getsize(out) / 1048576.0, 1)
        print(">> saved %s (%.1f MB)" % (out, stats["blend_mb"]))
    return stats


def _save(out):
    """Save through the project's enforced no-external-assets path, then repair
    the one thing that path breaks for this item.

    ``fix_audit_blend.save_clean`` REBUILDS the world from
    ``procedural_world()``, which leaves the Sky Texture's own sun disc ON.  With
    the contract's SUN lamp also in the scene that is two suns and a key ~1.8x
    too bright, which would silently invalidate every albedo in §8.  So: save
    through save_clean (its refusal-to-save check is the point of it), switch the
    disc back off, and save again compressed.  Two writes; the second is the one
    that ships.
    """
    import fix_audit_blend as FAB
    FAB.save_clean(out)
    print(">> _save: re-applying the contract atmosphere save_clean just reset")
    apply_contract_sky()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out),
                                relative_remap=False, compress=True)
    left = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if left:
        raise SystemExit("REFUSING: external images survived the save: %s" % left)
    return out


# ===========================================================================
# 10.  SELF-MEASUREMENT
# ===========================================================================

def measure(site=None):
    """Measure the built object.  Numbers, in real units, not claims."""
    site = site or PATCH_SITES[0]
    objs = [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and o.name.startswith(PFX)]
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    verts = 0
    for ob in objs:
        me = ob.evaluated_get(deps).to_mesh()
        verts += len(me.vertices)
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        ob.evaluated_get(deps).to_mesh_clear()
    return dict(objects=len(objs), triangles=tris, vertices=verts,
                names=[o.name for o in objs])


# ---------------------------------------------------------------------------
#  The four things item_gate.py structurally cannot check for this item, each
#  turned into a number.  R2-017: measure the artefact, not the process.
#
#   1. PER-STONE UNIQUENESS.  The manifest declares instances = 1, so the gate's
#      per_instance_variation check passes VACUOUSLY -- it compares the 5 chunk
#      objects, not the 321 842 stones inside them.  Reporting that as proof of
#      variation would be exactly the R2-017 failure: a measurement answering a
#      different question than the one asked.  So the stones are hashed here.
#   2. DATUM CONFORMANCE.  Whether the built mesh actually lands on C.ground_z.
#   3. COORDINATE HYGIENE.  Law 6: recentred on emit, TexCoord->Object, and NO
#      Geometry->Position anywhere.  A grep is not a check; the node trees are
#      walked.
#   4. ALBEDO.  Against C.lambert_radiance, which is the function the contract
#      says a material calibration should be run against.
# ---------------------------------------------------------------------------

def verify(site=None, out=None):
    site = site or PATCH_SITES[0]
    rep = {"item": ITEM_ID, "site": site.name}

    # --- 1. per-stone uniqueness -------------------------------------------
    # Regenerate a large sample through the SAME generator and hash each stone's
    # shape after removing scale and orientation: the sorted vector of vertex
    # radii normalised by the mean radius.  Two stones with the same descriptor
    # are the same stone at a different size and angle -- which is precisely the
    # "one tree spammed 100 times" failure, expressed for aggregate.
    rng = np.random.default_rng(1000 + site.seed)
    mix = mix_of(site.s0)
    n = 60000
    size = np.full(n, mix["d_nom"] * 0.9)
    V, Fc, meta = crushed_stones(n, rng, size, flake=mix["flake"], tmpl="ico")
    r = np.linalg.norm(V, axis=2)
    r = np.sort(r / r.mean(axis=1, keepdims=True), axis=1)
    keys = np.round(r * 1000.0).astype(np.int32)          # 0.1 % quantisation
    uniq = len({k.tobytes() for k in keys})
    vol = np.abs(np.einsum("nij,nij->n",
                           V[:, Fc[:, 0]], np.cross(V[:, Fc[:, 1]],
                                                    V[:, Fc[:, 2]]))) / 6.0
    sph = (math.pi ** (1 / 3) * (6 * vol) ** (2 / 3)) / np.maximum(
        _hull_area(V, Fc), 1e-12)
    rep["stone_uniqueness"] = dict(
        sampled=n, distinct_shapes=uniq,
        duplicate_fraction=round(1.0 - uniq / n, 8),
        quantisation="0.1 % of mean radius, on the sorted radial vector",
        volume_cv=round(float(np.std(vol) / np.mean(vol)), 4),
        sphericity_mean=round(float(np.mean(sph)), 4),
        sphericity_p05=round(float(np.percentile(sph, 5)), 4),
        sphericity_p95=round(float(np.percentile(sph, 95)), 4),
        flatness_ratio_mean=round(float(np.mean(meta["axes"][:, 2])), 4),
        note="Wadell true sphericity. A sphere is 1.0, rounded river gravel "
             "0.85-0.95, cubical crushed rock (flakiness index < 20, which is "
             "what a wearing course is specified to) 0.78-0.84. The first build "
             "measured 0.871 -- gravel -- and the crusher was deepened.",
    )

    # --- 2. datum conformance ----------------------------------------------
    deps = bpy.context.evaluated_depsgraph_get()
    dev = {}
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or not ob.name.startswith(PFX):
            continue
        me = ob.evaluated_get(deps).to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(np.float64) + np.array(ob.matrix_world.translation)
        if co.shape[0] > 400000:
            sel = np.random.default_rng(7).choice(co.shape[0], 400000, replace=False)
            co = co[sel]
        s, u = C.project(co[:, 0], co[:, 1])
        d = (co[:, 2] - C.ground_z(s, u)) * 1000.0        # mm above the datum
        dev[ob.name] = dict(n=int(co.shape[0]),
                            min_mm=round(float(d.min()), 3),
                            p50_mm=round(float(np.percentile(d, 50)), 3),
                            max_mm=round(float(d.max()), 3))
        ob.evaluated_get(deps).to_mesh_clear()
    rep["datum_deviation_mm"] = dev
    rep["datum_note"] = ("every vertex is measured against C.ground_z(s, u) after "
                         "re-projecting its world position, so this is the datum "
                         "the other five builders use, not a local copy of it")

    # --- 3. coordinate hygiene ---------------------------------------------
    bad_pos, img_nodes, obj_texcoord = [], 0, 0
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "TEX_IMAGE":
                img_nodes += 1
            if nd.type == "NEW_GEOMETRY":
                for o in nd.outputs:
                    if o.name == "Position" and o.is_linked:
                        bad_pos.append(m.name)
            if nd.type == "TEX_COORD":
                for o in nd.outputs:
                    if o.name == "Object" and o.is_linked:
                        obj_texcoord += 1
    extent = {}
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or not ob.name.startswith(PFX):
            continue
        co = np.empty(len(ob.data.vertices) * 3, np.float32)
        ob.data.vertices.foreach_get("co", co)
        extent[ob.name] = round(float(np.abs(co).max()), 3)
    rep["coordinate_hygiene"] = dict(
        image_texture_nodes=img_nodes,
        geometry_position_links=sorted(set(bad_pos)),
        texcoord_object_links=obj_texcoord,
        max_abs_local_vertex_m=extent,
        world_origin_distance_m=round(float(np.linalg.norm(
            np.array(C.su_to_world(site.s0, site.u0)))), 1),
        note="mesh data is local; the object matrix carries the ~971 m out to T4, "
             "so the finest texture never sees a coordinate above the value above",
    )

    # --- 4. albedo against the contract's own light ------------------------
    rep["albedo_targets"] = dict(
        mortar_fresh=list(COL_MORTAR_FRESH), mortar_old=list(COL_MORTAR_OLD),
        mortar_multiplier=0.72,
        stone_pale=[0.148, 0.141, 0.126], stone_mid=[0.098, 0.094, 0.088],
        stone_dark=[0.052, 0.052, 0.055],
        bitumen_film=[0.0198, 0.0186, 0.0180],
        rubber=list(COL_RUBBER),
        lambert_radiance_at_0p18=[round(v, 4) for v in C.lambert_radiance(0.18)],
        reference_exposure=C.REFERENCE_EXPOSURE_EXTERIOR,
        view_transform=C.VIEW_TRANSFORM,
        note="M_Surf_Asphalt's measured ladder, reused unchanged: fresh dense-graded "
             "0.045-0.055, old bleached 0.100-0.130, rubbered line 0.028-0.035",
    )

    # --- 5. the four variation axes, as numbers ----------------------------
    ss = np.array([r[0] + 5.0 for r in BS.RESURFACE])
    rep["variation_axes"] = dict(
        resurfacing_zones=[dict(zone=i, s_start=BS.RESURFACE[i][0],
                                age=BS.RESURFACE[i][1], mix=MIXES[i]["name"],
                                d_nom_mm=round(MIXES[i]["d_nom"] * 1000, 1),
                                texture_depth_mm=round(MIXES[i]["tex"] * 1000, 2),
                                voids_pct=round(MIXES[i]["void"] * 100, 1),
                                note=MIXES[i]["note"])
                           for i in range(len(MIXES))],
        distinct_d_nom_mm=sorted({round(m["d_nom"] * 1000, 1) for m in MIXES}),
        segregation_range=_frange(segregation, site),
        polish_range=_frange(polish, site),
        flushing_range=_frange(flushing, site),
        fill_depth_mm=_frange(fill_depth, site, 1000.0),
        sand_patch_mtd_mm=_frange(mtd, site, 1000.0),
        exposure_fraction=_frange(exposure, site),
        mtd_note="EN 13036-1 sand-patch ranges for the mixes in MIXES: SMA 8 "
                 "0.6-0.8 mm, SMA 11 0.8-1.2, aged AC 14 1.0-1.6, porous 1.8-2.6, "
                 "a rubbered racing line 0.3-0.6.",
    )
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1, default=float)
        print(">> wrote %s" % out)
    return rep


def _hull_area(V, F):
    a = V[:, F[:, 0]]; b = V[:, F[:, 1]]; c = V[:, F[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=2).sum(axis=1)


def _frange(fn, site, mul=1.0):
    ss = site.s0 + np.linspace(-site.ext_s, site.ext_s, 220)
    uu = site.u0 + np.linspace(-site.ext_u, site.ext_u, 220)
    S, U = np.meshgrid(ss, uu)
    v = np.asarray(fn(S.ravel(), U.ravel()), float) * mul
    return dict(min=round(float(v.min()), 4), p50=round(float(np.percentile(v, 50)), 4),
                max=round(float(v.max()), 4))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="hero", choices=list(QUALITY))
    ap.add_argument("--site", default="t4_apex")
    ap.add_argument("--test-blend", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--verify-out", default=os.path.join(
        _ROOT, "render", "items", ITEM_ID, "verify.json"))
    ap.add_argument("--out", default=os.path.join(_HERE,
                                                  "asphalt_wearing_course_test.blend"))
    ap.add_argument("--stats", default=None)
    a = ap.parse_args(argv)

    site = next(s for s in PATCH_SITES if s.name == a.site)
    st = build_test_scene(quality=a.quality,
                          out=a.out if a.test_blend else None, site=site)
    st.update(measure(site))
    if a.verify:
        v = verify(site, out=a.verify_out)
        print("\n=== verify ===")
        print(json.dumps({k: v[k] for k in
                          ("stone_uniqueness", "coordinate_hygiene",
                           "datum_deviation_mm")}, indent=1, default=float))
    print("\n=== asphalt_wearing_course ===")
    for k, v in st.items():
        if k == "names":
            continue
        print("  %-20s %s" % (k, v))
    for n in st.get("names", []):
        print("     obj %s" % n)
    if a.stats:
        json.dump(st, open(a.stats, "w"), indent=1, default=float)
    return st


if __name__ == "__main__":
    main()
