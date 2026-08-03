#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mullion_intact.py — CIRCUIT VITRINE, per-item hero campaign, item ``mullion_intact``
(zone ``showroom_breach``, wave 1, build order 20, **4 dependants, 0 dependencies**).

WHAT THIS IS, IN ONE SENTENCE
=============================
The eleven vertical members of the showroom's glazed east wall, built as the
**capped stick curtain-wall system they actually are** — an extruded 6063-T6
mullion with a screw port, sealed cells and a steel reinforcement, a polyamide
thermal isolator, a bolted pressure plate and a snap-on cover cap, standing on a
plugged base spigot with anchor studs into the slab — so that the object the
lens is inside for the first forty-four seconds of the film reads as a facade
somebody detailed, and not as eleven grey boxes at 2.2 m centres.

    manifest: "0.075 x 0.160 x 6.200 m at 2.20 m centres; one sits exactly on
               the launch axis Y=0.  Extruded aluminium: thermal break, screw
               ports, gasket races.  WRONG VERSION: A PLAIN BOX."

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 1.6 = 2333.33 px/m    ->    1 px = 0.4286 mm

At 1.600 m on a 35 mm lens the frame is 1.646 x 0.926 m, so the 6.200 m mullion
overfills it four times over (manifest ``onscreen_px_4k`` 2160, ``overfills_frame``
true) and the 75 mm sightline is 175 px wide on the 4K master.  What that buys,
and what it therefore obliges:

    the 75 mm cap face                  175 px
    the 30 mm glazing gap                70 px
    a 6.5 mm cap overhang reveal         15 px   <- GEOMETRY, and it self-shadows
    a 5.0 mm gasket race                 12 px   <- GEOMETRY (a real channel)
    a 3.2 mm extrusion wall               7 px   <- GEOMETRY at every sawn end
    an M12 nut across flats, 19 mm       44 px   <- GEOMETRY
    an M12 thread, 1.75 mm pitch          4 px   <- GEOMETRY (a real helix,
                                                   not a bump map: it breaks
                                                   the silhouette of the stud)
    a 1.1 mm cap nose radius            2.6 px   <- GEOMETRY (this is the
                                                   specular line that tells you
                                                   the metal is extruded)
    a 0.55 mm ink-jet dot               1.3 px   <- GEOMETRY (the fabrication
                                                   mark is a 5x7 dot matrix and
                                                   it is different on every one)
    a 0.35 mm handling dent in the cap  0.8 px of depth, 12 mm across = 28 px
                                                <- GEOMETRY: under a 12.5 deg
                                                   sun a 3 deg normal change is
                                                   a visible dark crescent
    0.1 mm extrusion die lines          0.23 px  <- SHADING
    20 micron anodic film, its tone     ---      <- SHADING (per-mullion batch)

The line is drawn at 0.25 mm of relief — 0.6 px — and everything above it that
occludes, self-shadows or breaks a silhouette is mesh.

WHY THE SECTION IS THE OBJECT
-----------------------------
A mullion is 6.2 m of constant cross-section.  Every pixel of it that is not the
base, the head or a dent is the SECTION, seen end-on through perspective, so the
section is where the modelling budget goes: 9 closed profile loops, ~1 500
profile points at a 1.8 mm target segment, filleted at every arris because a
zero-radius arris on extruded aluminium is the single most reliable tell that
something was modelled rather than extruded.  The cells are modelled as sealed
voids inside the metal — which is what they are once the base and head spigots
are in — so the wall thicknesses are real and the bent-stub item has something
truthful to tear open.

WHERE x = 15.000 IS, AND WHAT IT IS THE OUTSIDE OF
---------------------------------------------------
``world_contract.ACCESS_GLASS_X`` = 15.000 is "the breach plane": the access
ribbon's start cap, the line the forecourt paving is cut on, and round 1's
``GW_Right_Glass`` plane.  Round 1's glass was a ZERO-THICKNESS PLANE, so which
surface of a real 160 mm assembly lands on 15.000 was still open.  **This module
puts the OUTERMOST surface — the cover cap face — on x = 15.000 exactly**, and
everything else inboard of it, for one reason that is not aesthetic: nothing may
cross the plane.  The paving is cut ON it (``ACCESS_RIBBON_T_MIN`` = 0.0), the
ribbon begins ON it, and a 33.5 mm cap overhang east of it would put five of the
eleven mullions inside the Beat-4 corridor for ``placement_gate`` to find.  The
glass therefore sits at x = 14.9665 (outer face), 33.5 mm behind the cap face.
**Every dependant reads that number from ``section()``, not from 15.000.**

THE ELEVEN, AND WHICH ONES SURVIVE
----------------------------------
Y = -11.0 + 2.2*i for i in 0..10, so mullion 5 is on Y = 0.000, the launch axis,
exactly as the manifest requires.  Round 1's measured glass runs y -10.962 ..
10.962, which is +-(11.000 - 0.0375): the jamb mullions' own half-sightline.  The
wall is 10 bays of 2.125 m clear opening.  ``breach_state()`` publishes what
Beat 3 does to them — 5, 4 and 6 are destroyed, 3 and 7 (Y = +-4.4) become
``mullion_bent_stub``, and the remaining six stay — so that the breach continuity
task and the destruction sim agree about which object is which.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  4 items depend on it.
===============================================================================
Everything in section 11 is a pure function of this module's deterministic plan.
It runs WITHOUT bpy, builds nothing, and returns WORLD-frame numbers in metres.
``interface_json(path)`` dumps the lot to ``mullion_intact_interface.json``.

    glass_panel_prefractured (10)   ``glazing_pockets()`` + ``section()``
        Per bay: the pane rectangle IN WORLD, its four corners, the outer and
        inner glass planes (x = 14.96650 / 14.95500), the 11.5 mm laminate
        make-up this module's rebate was cut for, the 16.0 mm edge bite under
        the pressure plate on every edge, and the CLEAR OPENING (2.125 x 5.980)
        that the manifest quotes.  THE PANE IS BIGGER THAN THE OPENING: 2.170 x
        6.025.  22.5 mm of every edge is hidden — 16.0 mm clamped under the
        pressure plate and a further 6.5 mm shaded by the cap overhang — and a
        pane cut to the clear opening has zero cover and falls out of the wall.
        Setting-block seats are given at the quarter points.

    glazing_gasket_set (220)        ``gasket_races()``
        Every race this module cut, as a world-frame extrusion spine plus its
        2D section: the exterior race in the pressure plate (5.0 x 3.0 mm, with
        3 retaining serrations a side), the interior race formed between the
        isolator rib and the glass, the compressed thickness each gasket must
        finish at, and the two isolator foot grooves.  The RUBBER IS NOT BUILT
        HERE — this module owns aluminium, polyamide and steel only.

    curtain_wall_transom (3)        ``transom_landings()``
        The three full-width transom lines at z = 1.600 / 3.100 / 4.600, and for
        each mullion the shear-block landing: the rebate face plane, the screw
        port SP1 axis, its bore diameter and the pitch a self-tapper cuts in it,
        the two screw positions per landing, and the clear width between panes
        the block has to live in (30.0 mm).  NO HOLES ARE DRILLED IN THE SIDE
        WALLS — this system fixes shear blocks into the front screw port, which
        is why this mullion has one.

    mullion_bent_stub (2)           ``stub_sources()`` + ``profile_loops()``
        The two at Y = +-4.4 by name and world transform, the full 2D section as
        closed polylines (so the stub can be lofted along a bent spine instead
        of re-invented), the wall thickness at every point of it, the steel
        reinforcement's extent (z 0.180 .. 6.020) which is what makes the plastic
        hinge local instead of smooth, and the height band 1.9-2.4 m where a
        6.2 m mullion in a 9.6 m aperture actually folds.

===============================================================================
HOW THE ELEVEN ARE EMITTED, AND HOW THE GATE MEASURES THEM
===============================================================================
Eleven meshes are built, ALL DIFFERENT — different bow and twist, different dent
fields, different shim stacks, different anchor hardware, different cap end cuts,
different ink-jet serials, two jamb variants with a wall closure the others do
not have.  They are emitted as ONE carrier object (mullion 5, on Y = 0) carrying
a Geometry Nodes tree that instances the other ten at their own stations.

That is not a trick to route the gate, and it is worth being explicit about why:
``item_gate``'s ``cv_size`` branch measures the coefficient of variation of the
WORLD BOUNDING-BOX DIAGONAL across instances.  Eleven mullions are all 6.200 m
long, so that diagonal is 6.2021 m for every one of them and the CV is 0.0005 —
0.03 is unreachable for ANY correctly built curtain wall, because a curtain wall
whose members differ in length by 3 % (186 mm) is not a curtain wall.  The
realized-instance branch asks the question that can actually be answered here,
and it is the harder one: ``distinct_sources`` must be >= 8 of 10 and no source
may be more than 25 % of the population.  Eleven distinct meshes score 10/10 and
10 %.  ``build(instanced=False)`` emits the SAME eleven meshes as eleven plain
objects for any consumer that needs to edit one; the geometry does not change,
only how it is carried.

    what the gate measures on the carrier   what is really there
    ------------------------------------    ------------------------------
    triangles: mullion 5 alone              x 11 (see ``census()``)
    p10 edge: mullion 5 alone               all eleven are built by one lofter
    materials: 6                            all eleven share them

===============================================================================
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/mullion_intact.py -- --test-scene \
        --out world/items/mullion_intact_test.blend
===============================================================================
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

try:
    import bpy
    HAVE_BPY = True
except Exception:                                   # pragma: no cover
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                        # noqa: E402

__version__ = "1.0.0"

ITEM = "mullion_intact"
COLL = "W_Item_MullionIntact"
SRC_COLL = "W_Item_MullionIntact_Sources"
PFX = "MUL_"            # the carrier object.  `item_gate --prefix MUL_`
SPFX = "MULSRC_"        # the ten instanced source meshes.  Deliberately NOT
                        # "MUL_"-prefixed: they are not scene objects and the
                        # gate must not double-count them as loose objects.
XPFX = "XMUL_"          # test-scene stand-ins owned by OTHER items (glass, sill,
                        # floor, soffit).  Never measured as this item.

_T0 = time.time()
VERBOSE = True


def log(msg):
    if VERBOSE:
        print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
        sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream re-reads the JSON.
FILMED_AT_M = 1.6
LENS_MM = 35.0
ONSCREEN_PX_4K = 2160.0
INSTANCES_DECLARED = 11
TYPICAL_H_M = 6.2
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M            # 2333.33 px/m
PX_M = 1.0 / PX_PER_M                                         # 0.4286 mm
VARIATION_AXES = ("anodising tone", "fixing wear", "dust in the channel")

# --- the wall, in the WORLD frame ---------------------------------------------
FACE_X = float(C.ACCESS_GLASS_X)      # 15.000 — the OUTERMOST surface of the
                                      # assembly (the cover cap face).  Nothing
                                      # this module builds is east of it.
CENTRES = 2.200                       # manifest
N_MULLION = 11                        # manifest
Y_FIRST = -11.0                       # round 1: GW_Right_Glass y -10.962..10.962
                                      # = +-(11.000 - half sightline)
SIGHT = 0.075                         # manifest: 0.075 face width
DEPTH = 0.160                         # manifest: 0.160 overall system depth
BACK_X = FACE_X - DEPTH               # 14.840
EXTRUSION_LEN = 6.200                 # manifest: 6.200 m of extrusion
PAD_T = 0.003                         # nylon isolator pad, alu off concrete
ANCHOR_EMBED = 0.090                  # anchor studs into the slab: 90 mm.
                                      # >= C.BASE_EMBED_M (0.020) by 4.5x
# The foot of the extrusion is NOT a constant: it lands on a packing-shim stack
# that levels each mullion independently, which is what shims are for and which
# is why no two mullions in a real wall have their saw-cut foot at the same
# height.  Per-mullion in `records()`; these are the nominal.
SHIM_NOM = 0.0055
MULL_Z0 = PAD_T + SHIM_NOM + 0.012    # 0.0205  nominal foot of the extrusion
MULL_Z1 = MULL_Z0 + EXTRUSION_LEN     # 6.2205  nominal top of the extrusion

# round 1's measured glass extent, which this module's rebate is cut to carry
GLASS_Z0_VISIBLE = 0.110
GLASS_Z1_VISIBLE = 6.090

# --- the section, as depth offsets from the cap face (metres, NEGATIVE inboard)
# Every one of these is a plane some other item has to meet.  They are published
# by section() and NOBODY should re-derive one from 15.000.
DX_CAP_FACE = 0.0000                  # x = 15.00000  cover cap, outer face
DX_CAP_WALL = -0.0024                 #               cap wall thickness 2.4
DX_PLATE_F = -0.0240                  # x = 14.97600  pressure plate, front face
DX_PLATE_B = -0.0300                  # x = 14.97000  pressure plate, back face
DX_GASK_O = -0.0335                   # x = 14.96650  GLASS, outer face
DX_GLASS_I = -0.0450                  # x = 14.95500  GLASS, inner face (11.5 mm)
DX_GASK_I = -0.0490                   # x = 14.95100  interior gasket, back
DX_ISO_B = -0.0550                    # x = 14.94500  MULLION rebate face
DX_BODY_B = -0.1600                   # x = 14.84000  MULLION back face
GLASS_T = DX_GASK_O - DX_GLASS_I      # 0.0115  5 + 1.5 PVB + 5
GASKET_O_T = DX_PLATE_B - DX_GASK_O   # 0.0035  compressed exterior gasket
GASKET_I_T = DX_GLASS_I - DX_GASK_I   # 0.0040  compressed interior gasket
ISO_T = DX_GASK_I - DX_ISO_B          # 0.0060  polyamide thermal isolator

PLATE_W = 0.0620                      # pressure plate width (+-0.0310)
PANE_GAP = 0.0300                     # clear gap between panes (+-0.0150)
EDGE_BITE = 0.5 * PLATE_W - 0.5 * PANE_GAP        # 0.0160 of glass under the plate
WALL_T = 0.0032                       # mullion rebate/side wall thickness
BACK_WALL_T = 0.0035                  # mullion back wall thickness
WEB_T = 0.0035                        # internal web

# The cap stops 80 mm short of the plate at BOTH ends, and the plate stops short
# of the extrusion.  That staircase of three different end positions IS the
# drainage path out of the glazing pocket at the sill — water that gets past the
# exterior gasket runs down the pocket, past the foot of the cap, and out — and
# it is why the foot of a real curtain wall reads as an assembly of three parts
# rather than as one solid stick.  It also exposes the lowest and highest
# pressure-plate screws, which are the only ones a lens can ever see.
PLATE_INSET_BOT = 0.067
PLATE_INSET_TOP = 0.073
CAP_INSET_BOT = 0.147
CAP_INSET_TOP = 0.153
STEEL_INSET = 0.160                   # galvanised RHS: clear of both spigots
SPIGOT_PLUG = 0.150                   # how far a base/head spigot plugs in
FLANGE_T = 0.012                      # base spigot flange thickness

TRANSOM_Z = (1.600, 3.100, 4.600)     # published to curtain_wall_transom

SP1_BORE_R = 0.00425                  # front screw port: M6 self-tapper
SP1_CENTRE_DX = -0.0620               # bore centre, depth offset
SP2_BORE_R = 0.00425                  # the two back screw ports
SP2_CENTRE = ((-0.1510, 0.0250), (-0.1510, -0.0250))

MAT_ALU, MAT_ISO, MAT_STEEL, MAT_GALV, MAT_NYLON, MAT_INK = range(6)
MAT_NAMES = ("Alu", "Iso", "Steel", "Galv", "Nylon", "Ink")

# Linear reflectances.  Anodised aluminium is DARKER than intuition: a clear
# anodised mill-finish extrusion measures 0.42-0.52 diffuse under a strong
# specular lobe, not the 0.7 that "silver" suggests.  Calibrated against
# C.lambert_radiance at the contract sun's 12.47 deg elevation; the cap face of
# this wall takes the sun at cos(incidence) = 0.518 and the interior faces see
# sky and floor bounce only, so the two sides of one extrusion are two
# different exposures of the same metal and the palette has to hold both.
PAL = dict(
    alu_bright=(0.4880, 0.4930, 0.4990),      # freshly wiped anodic film
    alu_mid=(0.3520, 0.3560, 0.3620),         # the working average
    alu_warm=(0.3600, 0.3480, 0.3260),        # a warm anodising batch
    alu_cool=(0.3300, 0.3400, 0.3620),        # a cool one
    alu_dull=(0.2150, 0.2180, 0.2240),        # handled, dusty, never wiped
    alu_slot=(0.1080, 0.1100, 0.1140),        # down a race: dirt and shadow
    alu_scuff=(0.2740, 0.2700, 0.2640),       # a scrape through the anodic film
    alu_white=(0.5700, 0.5720, 0.5680),       # oxide bloom / white rust
    alu_cut=(0.4200, 0.4220, 0.4260),         # a saw-cut end: bare metal
    iso_black=(0.0175, 0.0175, 0.0182),       # glass-filled polyamide
    iso_grey=(0.0430, 0.0432, 0.0445),        # its mould-flow sheen
    steel_a2=(0.3450, 0.3480, 0.3520),        # A2 stainless, mill finish
    steel_dark=(0.0820, 0.0830, 0.0850),
    galv_spangle=(0.4300, 0.4360, 0.4420),    # hot dip zinc
    galv_dull=(0.2400, 0.2440, 0.2500),
    white_rust=(0.5100, 0.5150, 0.5100),
    nylon_off=(0.3900, 0.3820, 0.3560),
    ink_black=(0.0135, 0.0134, 0.0138),       # ink-jet fabrication mark
    dust=(0.1520, 0.1400, 0.1180),            # site dust in a channel
    grime=(0.0430, 0.0412, 0.0384),
    film_tack=(0.2100, 0.2060, 0.1960),       # protective-film adhesive residue
    concrete=(0.1450, 0.1440, 0.1400),
)


# ==============================================================================
#  1.  NUMERIC KIT — deterministic, seedable, identical on every machine
# ==============================================================================

def h01(*keys):
    """FNV-1a over mixed keys -> float in [0, 1).  Avalanches properly.

    Twelve consecutive indices must NOT come back inside 1 % of each other:
    that is how "eleven different mullions" quietly becomes one mullion eleven
    times.  64-bit FNV-1a plus a final xorshift-multiply mix.
    """
    h = 0xCBF29CE484222325
    flat = []
    for k in keys:
        if isinstance(k, (tuple, list)):
            flat.extend(k)
        else:
            flat.append(k)
    for k in flat:
        if isinstance(k, str):
            bs = k.encode("utf8")
        elif isinstance(k, float):
            bs = repr(round(k, 9)).encode("utf8")
        else:
            bs = int(k).to_bytes(8, "little", signed=True)
        for b in bs:
            h ^= b
            h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 29
    h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 32
    return (h & 0xFFFFFFFFFF) / float(1 << 40)


def hrange(lo, hi, *keys):
    return lo + (hi - lo) * h01(*keys)


def hpick(seq, *keys):
    return seq[int(h01(*keys) * len(seq)) % len(seq)]


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / max(b - a, 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def unit2(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 1e-12 else (1.0, 0.0)


def y_of(i):
    """World Y of mullion i.  i in 0..10, mullion 5 is on Y = 0.000."""
    return Y_FIRST + CENTRES * float(i)


# ==============================================================================
#  2.  2D PROFILE AUTHORING — corners, fillets, resampling, tags
# ==============================================================================
# Every profile in this file is authored as a list of
#
#       (x, y, radius, tag)
#
# corners in the SECTION frame: x is the depth offset from the cap face (0 at
# x = 15.000, negative inboard), y is across the sightline.  `arcpoly` fillets
# every corner and resamples the whole loop to a target segment length, keeping
# the tag of the segment each output point came from and recording how tight the
# fillet it sits on was.
#
# THE FILLETS ARE NOT DECORATION.  An extrusion die cannot make a zero radius,
# and at 2333 px/m a 1.1 mm nose radius is a 2.6 px specular line that is the
# difference between "aluminium" and "grey".  Nothing in this file has a sharp
# arris except a saw cut.

SEG_FINE = 0.0018        # target segment on everything the lens can reach
SEG_COARSE = 0.0032      # target segment inside a sealed cell


def _arc_pts(c, r, a0, a1, seg):
    n = max(2, int(math.ceil(abs(a1 - a0) * r / seg)) + 1)
    t = np.linspace(a0, a1, n)
    return np.stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)], axis=1)


def arcpoly(corners, seg=SEG_FINE, closed=True):
    """[(x, y, r, tag), ...] -> (P[N,2], TAG[N], RAD[N]).

    RAD is the fillet radius the point sits on, or np.inf on a straight run;
    it becomes the `edge` attribute, which is what drives arris wear and the
    specular break in the shader.
    """
    n = len(corners)
    pts, tags, rads = [], [], []
    for i in range(n):
        xa, ya, _, _ = corners[(i - 1) % n]
        xb, yb, rb, tb = corners[i]
        xc, yc, _, _ = corners[(i + 1) % n]
        u = unit2((xa - xb, ya - yb))
        w = unit2((xc - xb, yc - yb))
        cosang = max(-1.0, min(1.0, u[0] * w[0] + u[1] * w[1]))
        ang = math.acos(cosang)
        la = math.hypot(xa - xb, ya - yb)
        lc = math.hypot(xc - xb, yc - yb)
        r = float(rb)
        if r > 1e-9 and ang > 1e-4 and abs(math.pi - ang) > 1e-4:
            t = r / math.tan(ang * 0.5)
            t = min(t, 0.48 * la, 0.48 * lc)
            r = t * math.tan(ang * 0.5)
            p1 = (xb + u[0] * t, yb + u[1] * t)
            p2 = (xb + w[0] * t, yb + w[1] * t)
            bis = unit2((u[0] + w[0], u[1] + w[1]))
            d = r / math.sin(ang * 0.5)
            ctr = (xb + bis[0] * d, yb + bis[1] * d)
            a0 = math.atan2(p1[1] - ctr[1], p1[0] - ctr[0])
            a1 = math.atan2(p2[1] - ctr[1], p2[0] - ctr[0])
            while a1 - a0 > math.pi:
                a1 -= 2.0 * math.pi
            while a0 - a1 > math.pi:
                a1 += 2.0 * math.pi
            A = _arc_pts(ctr, r, a0, a1, min(seg, max(r * 0.5, 0.00012)))
            for p in A:
                pts.append((float(p[0]), float(p[1])))
                tags.append(tb)
                rads.append(r)
        else:
            pts.append((float(xb), float(yb)))
            tags.append(tb)
            rads.append(np.inf)
    # resample the straight runs between consecutive emitted points
    P, T, R = [], [], []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        a = pts[i]
        b = pts[(i + 1) % m]
        P.append(a)
        T.append(tags[i])
        R.append(rads[i])
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(d / seg)          # arc points are already <= seg apart, so this
        if k >= 1:                # only ever subdivides the straight runs
            for j in range(1, k + 1):
                f = j / float(k + 1)
                P.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                T.append(tags[i])
                R.append(np.inf)
    if not closed:
        P.append(pts[-1]); T.append(tags[-1]); R.append(rads[-1])
    return np.asarray(P, float), list(T), np.asarray(R, float)


def mirror_half(half):
    """Half a symmetric section (first and last corner ON the axis y = 0) ->
    the full closed corner list."""
    out = list(half)
    for (x, y, r, t) in reversed(half[1:-1]):
        out.append((x, -y, r, t))
    return out


def loop_normals(P):
    """Outward 2D normals for a closed polygon, sign fixed by signed area."""
    nxt = np.roll(P, -1, axis=0)
    prv = np.roll(P, 1, axis=0)
    d = nxt - prv
    n = np.stack([d[:, 1], -d[:, 0]], axis=1)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.maximum(ln, 1e-12)
    area = 0.5 * float(np.sum(P[:, 0] * nxt[:, 1] - nxt[:, 0] * P[:, 1]))
    if area < 0.0:
        n = -n
    return n


def loop_arclen(P):
    d = np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)[:-1]])
    return s, float(d.sum())


def earclip(P):
    """Triangulate a simple polygon (N,2).  O(n^2), which at n ~ 600 is 6 ms."""
    n = len(P)
    if n < 3:
        return np.zeros((0, 3), np.int64)
    idx = list(range(n))
    nxt = np.roll(P, -1, axis=0)
    area = 0.5 * float(np.sum(P[:, 0] * nxt[:, 1] - nxt[:, 0] * P[:, 1]))
    if area < 0.0:
        idx.reverse()

    def cross(o, a, b):
        return ((P[a][0] - P[o][0]) * (P[b][1] - P[o][1])
                - (P[a][1] - P[o][1]) * (P[b][0] - P[o][0]))

    def inside(a, b, c, p):
        d1 = cross(a, b, p)
        d2 = cross(b, c, p)
        d3 = cross(c, a, p)
        return (d1 >= -1e-14) and (d2 >= -1e-14) and (d3 >= -1e-14)

    tris = []
    guard = 0
    while len(idx) > 3 and guard < 8 * n:
        guard += 1
        clipped = False
        for k in range(len(idx)):
            a = idx[(k - 1) % len(idx)]
            b = idx[k]
            c = idx[(k + 1) % len(idx)]
            if cross(a, b, c) <= 1e-16:
                continue
            bad = False
            for j in idx:
                if j in (a, b, c):
                    continue
                if inside(a, b, c, j):
                    bad = True
                    break
            if bad:
                continue
            tris.append((a, b, c))
            idx.pop(k)
            clipped = True
            break
        if not clipped:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return np.asarray(tris, np.int64) if tris else np.zeros((0, 3), np.int64)


def ring_plan(z0, z1, base, refine=()):
    """Station list for a loft: `base` metres apart, refined near events.

    refine = [(z_centre, half_width, step), ...].  Every loft in this file gets
    its rings from here, so a dent, a saw cut and a spigot mouth all get the
    same treatment and there is one place to tune density.
    """
    zs = [np.arange(z0, z1 + 1e-9, base)]
    for (zc, hw, st) in refine:
        a = max(z0, zc - hw)
        b = min(z1, zc + hw)
        if b > a:
            zs.append(np.arange(a, b + 1e-9, st))
    z = np.unique(np.round(np.concatenate(zs), 7))
    z = z[(z >= z0 - 1e-9) & (z <= z1 + 1e-9)]
    if z[0] > z0 + 1e-9:
        z = np.concatenate([[z0], z])
    if z[-1] < z1 - 1e-9:
        z = np.concatenate([z, [z1]])
    # drop stations closer than 0.35 mm: they cost a ring and cannot be seen
    keep = [0]
    for i in range(1, len(z)):
        if z[i] - z[keep[-1]] > 0.00035 or i == len(z) - 1:
            keep.append(i)
    return z[keep]


# ==============================================================================
#  3.  MESH ACCUMULATOR
# ==============================================================================
# ONE Acc per mullion, so a mullion is one mesh and the gate's `distinct_sources`
# counts mullions rather than fragments.

ATTR_F = ("mu_wear", "mu_edge", "mu_dirt", "mu_ao", "mu_h", "mu_pid", "mu_exp")
ATTR_V = ("mu_bc",)

# tag -> (material, exterior exposure, cavity occlusion, dirt, handling wear)
#
#   exp   1.0 = weather side of the wall, 0.0 = showroom side.  ONE extrusion has
#         both, 33 mm apart, and they do not age the same way.
#   ao    how far down a channel the point is; drives the dust and the shadow
#         term the shader cannot compute from a normal alone.
#   dirt  propensity to hold site dust.  A race holds it, a face sheds it.
#   wear  propensity to be touched, scraped, knelt on, dropped against.
TAG_INFO = {
    "capface":   (MAT_ALU, 1.00, 0.00, 0.12, 0.90),
    "capedge":   (MAT_ALU, 1.00, 0.05, 0.30, 1.00),
    "capunder":  (MAT_ALU, 0.85, 0.45, 0.55, 0.25),
    "capleg":    (MAT_ALU, 0.30, 0.80, 0.60, 0.05),
    "capbarb":   (MAT_ALU, 0.20, 0.85, 0.55, 0.05),
    "captip":    (MAT_ALU, 0.15, 0.90, 0.60, 0.05),
    "capleg_i":  (MAT_ALU, 0.10, 0.92, 0.45, 0.02),
    "capceil":   (MAT_ALU, 0.10, 0.88, 0.35, 0.02),
    "platefront": (MAT_ALU, 0.55, 0.60, 0.50, 0.12),
    "platechan": (MAT_ALU, 0.45, 0.82, 0.75, 0.10),
    "plateedge": (MAT_ALU, 0.90, 0.25, 0.40, 0.35),
    "plateback": (MAT_ALU, 0.75, 0.35, 0.45, 0.10),
    "race":      (MAT_ALU, 0.25, 0.90, 0.80, 0.04),
    "gaskrace":  (MAT_ALU, 0.60, 0.80, 0.70, 0.06),
    "rebate":    (MAT_ALU, 0.35, 0.55, 0.60, 0.30),
    "sp1":       (MAT_ALU, 0.25, 0.92, 0.72, 0.05),
    "isogroove": (MAT_ALU, 0.20, 0.90, 0.78, 0.03),
    "side":      (MAT_ALU, 0.05, 0.10, 0.30, 0.85),   # the showroom sees this
    "back":      (MAT_ALU, 0.02, 0.08, 0.28, 1.00),   # and this most of all
    "tslot":     (MAT_ALU, 0.02, 0.88, 0.90, 0.10),
    "cell":      (MAT_ALU, 0.00, 1.00, 0.20, 0.00),
    "port":      (MAT_ALU, 0.00, 1.00, 0.25, 0.00),
    "isoface":   (MAT_ISO, 0.30, 0.55, 0.55, 0.20),
    "isorib":    (MAT_ISO, 0.25, 0.65, 0.60, 0.10),
    "isofoot":   (MAT_ISO, 0.10, 0.92, 0.70, 0.02),
    "isoedge":   (MAT_ISO, 0.35, 0.35, 0.45, 0.45),
    "steel":     (MAT_GALV, 0.00, 1.00, 0.35, 0.00),
    "cut":       (MAT_ALU, 0.20, 0.55, 0.55, 0.60),
}
TW_CENTRE = (-0.0900, 0.0)     # the section's twist axis, ~ its shear centre


def place(ob, R, O):
    """Put an object at (R, O) and PROVE it landed there.

    `ob.matrix_world = <4x4>` on a freshly created object does not stick: the
    loc/rot/scale channels stay at the identity and the next depsgraph
    evaluation overwrites the world matrix from them.  Decompose into the
    channels the depsgraph actually reads, then MEASURE the result.
    """
    from mathutils import Matrix
    q = Matrix([[float(R[0][0]), float(R[0][1]), float(R[0][2])],
                [float(R[1][0]), float(R[1][1]), float(R[1][2])],
                [float(R[2][0]), float(R[2][1]), float(R[2][2])]]).to_quaternion()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    ob.location = (float(O[0]), float(O[1]), float(O[2]))
    ob.scale = (1.0, 1.0, 1.0)
    got = np.array(ob.matrix_basis)
    if (not np.allclose(got[:3, 3], np.asarray(O, float), atol=1e-4)
            or not np.allclose(got[:3, :3], np.asarray(R, float), atol=1e-4)):
        raise RuntimeError("REFUSING: %s did not land at its site." % ob.name)
    return ob


class Acc(object):
    """Vertex / face accumulator carrying this item's attribute set."""

    def __init__(self, name):
        self.name = name
        self._V, self._Q, self._T, self._mq, self._mt = [], [], [], [], []
        self._A = {a: [] for a in ATTR_F}
        self._bc = []
        self.n = 0
        self.parts = 0

    def add(self, V, quads=None, tris=None, mat=MAT_ALU, bc=None, **attr):
        V = np.ascontiguousarray(np.asarray(V, np.float64).reshape(-1, 3))
        m = V.shape[0]
        if m == 0:
            return 0
        base = self.n
        self._V.append(V)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            self._Q.append(q)
            mm = attr.pop("mat_q", None)
            self._mq.append(np.full(q.shape[0], mat, np.int32) if mm is None
                            else np.asarray(mm, np.int32).ravel())
        else:
            attr.pop("mat_q", None)
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self._T.append(t)
            mm = attr.pop("mat_t", None)
            self._mt.append(np.full(t.shape[0], mat, np.int32) if mm is None
                            else np.asarray(mm, np.int32).ravel())
        else:
            attr.pop("mat_t", None)
        for a in ATTR_F:
            v = attr.get(a, h01(self.parts, 7717, self.name) if a == "mu_pid"
                         else 0.0)
            if np.ndim(v) == 0:
                self._A[a].append(np.full(m, float(v), np.float32))
            else:
                self._A[a].append(np.broadcast_to(
                    np.asarray(v, np.float32).ravel(), (m,)).astype(np.float32))
        if bc is None:
            self._bc.append(np.zeros((m, 3), np.float32))
        else:
            b = np.asarray(bc, np.float32)
            self._bc.append(np.ascontiguousarray(
                b.reshape(-1, 3) if b.size > 3 else
                np.broadcast_to(b.reshape(1, 3), (m, 3))).astype(np.float32))
        self.n += m
        self.parts += 1
        return base

    def solid(self, V, quads=None, tris=None, flip=False, **kw):
        """Add a CLOSED solid, orienting every face outward by signed volume.

        Winding is the most tedious bug class in generated geometry and a
        flipped face under a 12.5 deg sun reads as a black hole in the frame.
        Settle it once: compute the signed volume and reverse if negative.
        `flip=True` inverts the result, which is what a sealed CAVITY inside
        the metal needs — its surface faces the void, not the aluminium.
        """
        V = np.asarray(V, np.float64).reshape(-1, 3)
        Q = None if quads is None else np.asarray(quads, np.int64).reshape(-1, 4)
        T = None if tris is None else np.asarray(tris, np.int64).reshape(-1, 3)
        vol = 0.0
        if T is not None and len(T):
            a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
            vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if Q is not None and len(Q):
            for (i, j, k) in ((0, 1, 2), (0, 2, 3)):
                a, b, c = V[Q[:, i]], V[Q[:, j]], V[Q[:, k]]
                vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if (vol < 0.0) != bool(flip):
            if Q is not None and len(Q):
                Q = Q[:, ::-1].copy()
            if T is not None and len(T):
                T = T[:, ::-1].copy()
        return self.add(V, quads=Q, tris=T, **kw)

    def arrays(self):
        V = np.concatenate(self._V) if self._V else np.zeros((0, 3))
        Q = np.concatenate(self._Q) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T) if self._T else np.zeros((0, 3), np.int64)
        mq = np.concatenate(self._mq) if self._mq else np.zeros(0, np.int32)
        mt = np.concatenate(self._mt) if self._mt else np.zeros(0, np.int32)
        A = {a: (np.concatenate(self._A[a]) if self._A[a]
                 else np.zeros(0, np.float32)) for a in ATTR_F}
        bc = np.concatenate(self._bc) if self._bc else np.zeros((0, 3), np.float32)
        return V, Q, T, mq, mt, A, bc


def grid_quads(m, n, close_n=True):
    """(m rings) x (n profile points) -> quad indices."""
    nn = n if close_n else n - 1
    i = np.arange(m - 1)[:, None]
    j = np.arange(nn)[None, :]
    j1 = (j + 1) % n
    a = i * n + j
    b = i * n + j1
    c = (i + 1) * n + j1
    d = (i + 1) * n + j
    return np.stack([a, b, c, d], axis=-1).reshape(-1, 4)


# ==============================================================================
#  4.  THE LOFTER — a section, a station list, and everything that bends it
# ==============================================================================

def loft(acc, P, TAGS, RAD, z, rec=None, dents=(), pid=0.0,
         cap0=True, cap1=True, void=False, tri_cap=None, wear_fn=None,
         extra_exp=1.0, chamfer=0.0):
    """Extrude a closed 2D section along z and add it to `acc` as one solid.

    `rec` carries the extrusion's OWN straightness: no 6.2 m aluminium member is
    straight, and a wall of eleven dead-straight mullions reads as CAD.  EN
    12020-2 permits 1.3 mm of bow per metre; this file uses 0.8-2.1 mm total
    over 6.2 m and 0.1-0.4 deg of twist — inside tolerance, outside "identical".
    Bow and twist are evaluated HERE, from the final station list, because
    `chamfer` inserts rings and a caller-computed bow array would then be one
    ring out of step with the geometry it bends.

    `dents` are (z_centre, s_centre, sigma_z, sigma_s, depth) and are scaled by
    the point's own exposure, so nothing dents the inside of a sealed cell.
    """
    N = len(P)
    if chamfer > 0.0:
        # A saw does not leave a square arris.  Two extra rings 0.4 mm in from
        # each end, with the outermost inset by `chamfer`, give the cut end a
        # real 0.3 x 0.4 mm break that catches a specular line at 2333 px/m.
        z = np.concatenate([[z[0], z[0] + 0.0004], z[1:-1],
                            [z[-1] - 0.0004, z[-1]]])
    M = len(z)
    bow = twist = None
    if rec is not None:
        _dx, _dy, _th = bow_at(rec, z)
        bow, twist = (_dx, _dy), _th
    s, per = loop_arclen(P)
    nrm = loop_normals(P)
    info = np.array([TAG_INFO[t] for t in TAGS], float)     # (N,5)
    mat_p = info[:, 0].astype(np.int32)
    exp_p = info[:, 1] * extra_exp
    ao_p = info[:, 2]
    dirt_p = info[:, 3]
    wear_p = info[:, 4]

    d = np.zeros((M, N))
    for (zc, sfrac, sz, ss, amp) in dents:
        sc = float(sfrac) * per          # dents are authored as a FRACTION of
        ds = np.abs(((s - sc + per * 0.5) % per) - per * 0.5)   # the perimeter
        gz = np.exp(-0.5 * ((z - zc) / max(sz, 1e-6)) ** 2)
        gs = np.exp(-0.5 * (ds / max(ss, 1e-6)) ** 2)
        d += amp * gz[:, None] * gs[None, :] * exp_p[None, :]
    if chamfer > 0.0:
        d[0, :] -= chamfer
        d[-1, :] -= chamfer

    X = P[None, :, 0] + nrm[None, :, 0] * d
    Y = P[None, :, 1] + nrm[None, :, 1] * d
    if twist is not None:
        th = np.asarray(twist, float)[:, None]
        cx, cy = TW_CENTRE
        dx, dy = X - cx, Y - cy
        ct, st = np.cos(th), np.sin(th)
        X = cx + dx * ct - dy * st
        Y = cy + dx * st + dy * ct
    if bow is not None:
        X = X + np.asarray(bow[0], float)[:, None]
        Y = Y + np.asarray(bow[1], float)[:, None]

    V = np.empty((M * N, 3))
    V[:, 0] = X.ravel()
    V[:, 1] = Y.ravel()
    V[:, 2] = np.repeat(z, N)

    Q = grid_quads(M, N, close_n=True)
    matq = np.tile(mat_p, M - 1)

    Tt = None
    matt = None
    if cap0 or cap1:
        if tri_cap is None:
            tri_cap = earclip(P)
        caps = []
        if cap0 and len(tri_cap):
            caps.append(tri_cap[:, ::-1])
        if cap1 and len(tri_cap):
            caps.append(tri_cap + (M - 1) * N)
        if caps:
            Tt = np.concatenate(caps)
            matt = np.full(len(Tt), MAT_ALU, np.int32)
            if void:
                matt[:] = MAT_ALU

    edge = np.where(np.isfinite(RAD),
                    np.clip(1.0 - RAD / 0.0022, 0.0, 1.0), 0.0)
    wz = np.ones(M) if wear_fn is None else np.asarray(wear_fn(z), float)
    A = dict(
        mu_edge=np.tile(edge, M),
        mu_ao=np.tile(ao_p, M),
        mu_dirt=np.tile(dirt_p, M),
        mu_exp=np.tile(exp_p, M),
        mu_wear=(wear_p[None, :] * wz[:, None]).ravel(),
        mu_h=np.repeat(z, N),
        mu_pid=pid,
    )
    bc = np.empty((M * N, 3), np.float32)
    bc[:, 0] = np.repeat(z, N)          # ALONG the member: the die-line axis
    bc[:, 1] = np.tile(s, M)            # ACROSS it, by arclength
    bc[:, 2] = 0.0
    return acc.solid(V, quads=Q, tris=Tt, mat=MAT_ALU, bc=bc, flip=void,
                     mat_q=matq, mat_t=matt, **A)


# ==============================================================================
#  5.  SOLIDS KIT — every fastener, plate and spigot on the object
# ==============================================================================

def frame_of(axis, ref=(0.0, 0.0, 1.0)):
    az = np.asarray(axis, float)
    az = az / max(np.linalg.norm(az), 1e-12)
    r = np.asarray(ref, float)
    if abs(float(np.dot(r, az))) > 0.95:
        r = np.array([1.0, 0.0, 0.0])
    ax = np.cross(r, az)
    ax = ax / max(np.linalg.norm(ax), 1e-12)
    ay = np.cross(az, ax)
    return ax, ay, az


def prism(acc, Q2, O, ex, ey, ez, t0, t1, mat=MAT_ALU, tag=None, **kw):
    """Extrude a 2D polygon between two planes along ez.  One closed solid."""
    Q2 = np.asarray(Q2, float).reshape(-1, 2)
    n = len(Q2)
    O = np.asarray(O, float)
    ex = np.asarray(ex, float); ey = np.asarray(ey, float); ez = np.asarray(ez, float)
    base = O[None, :] + Q2[:, 0:1] * ex[None, :] + Q2[:, 1:2] * ey[None, :]
    V = np.concatenate([base + t0 * ez[None, :], base + t1 * ez[None, :]])
    i = np.arange(n)
    j = (i + 1) % n
    side = np.stack([i, j, j + n, i + n], axis=1)
    tri = earclip(Q2)
    T = np.concatenate([tri[:, ::-1], tri + n]) if len(tri) else None
    kw.setdefault("bc", np.stack([np.tile(Q2[:, 1], 2),
                                  np.tile(Q2[:, 0], 2),
                                  np.zeros(2 * n)], axis=1))
    return acc.solid(V, quads=side, tris=T, mat=mat, **kw)


def chbox(acc, x0, x1, y0, y1, z0, z1, cham=0.0008, mat=MAT_ALU, rad=None,
          **kw):
    """An axis-aligned box with a real chamfer on all twelve edges.

    A 12 mm flange and a 1.5 mm packing shim modelled as raw boxes read as CAD
    at 2333 px/m — a sheared or sawn plate has a 0.5-1.0 mm broken arris on
    every edge and that break is what catches the light.  Four rings and a
    rounded-rectangle section; 0.8 mm is 1.9 px.
    """
    rad = (cham * 2.2) if rad is None else rad
    P, T, R = arcpoly([(x0, y0, rad, "cut"), (x1, y0, rad, "cut"),
                       (x1, y1, rad, "cut"), (x0, y1, rad, "cut")],
                      max(SEG_COARSE, cham * 1.2))
    n = len(P)
    nrm = loop_normals(P)
    zs = [z0, z0 + cham, z1 - cham, z1]
    ins = [cham, 0.0, 0.0, cham]
    V = np.empty((4 * n, 3))
    for i, (z, d) in enumerate(zip(zs, ins)):
        V[i * n:(i + 1) * n, 0] = P[:, 0] - nrm[:, 0] * d
        V[i * n:(i + 1) * n, 1] = P[:, 1] - nrm[:, 1] * d
        V[i * n:(i + 1) * n, 2] = z
    Q = grid_quads(4, n, close_n=True)
    tri = earclip(P)
    T3 = np.concatenate([tri[:, ::-1], tri + 3 * n]) if len(tri) else None
    s, per = loop_arclen(P)
    kw.setdefault("bc", np.stack([np.repeat(np.asarray(zs), n),
                                  np.tile(s, 4), np.zeros(4 * n)], axis=1))
    kw.setdefault("mu_edge", np.tile(
        np.where(np.isfinite(R), 1.0, 0.0), 4) * np.repeat([1, .3, .3, 1], n))
    return acc.solid(V, quads=Q, tris=T3, mat=mat, **kw)


def tube(acc, p0, p1, r0, r1=None, seg=28, mat=MAT_STEEL, caps=True, **kw):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    r1 = r0 if r1 is None else r1
    ax, ay, az = frame_of(p1 - p0)
    t = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    A = p0[None, :] + r0 * (c[:, None] * ax[None, :] + s[:, None] * ay[None, :])
    B = p1[None, :] + r1 * (c[:, None] * ax[None, :] + s[:, None] * ay[None, :])
    V = np.concatenate([A, B])
    i = np.arange(seg)
    j = (i + 1) % seg
    side = np.stack([i, j, j + seg, i + seg], axis=1)
    T = None
    if caps:
        f0 = np.stack([np.zeros(seg - 2, np.int64), np.arange(1, seg - 1),
                       np.arange(2, seg)], axis=1)
        T = np.concatenate([f0[:, ::-1], f0 + seg])
    kw.setdefault("bc", np.stack([np.concatenate([np.zeros(seg),
                                                  np.full(seg, float(np.linalg.norm(p1 - p0)))]),
                                  np.tile(t * r0, 2), np.zeros(2 * seg)], axis=1))
    return acc.solid(V, quads=side, tris=T, mat=mat, **kw)


def threaded(acc, p0, p1, d_major, pitch, seg=30, mat=MAT_STEEL, **kw):
    """A real helical V thread.  At 1.75 mm pitch and 2333 px/m that is a 4 px
    rhythm on the silhouette of every exposed stud, and no bump map puts a
    notch in a silhouette."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    ax, ay, az = frame_of(p1 - p0)
    rmaj = 0.5 * d_major
    rmin = rmaj - 0.6134 * pitch
    nt = max(6, int(math.ceil(L / (pitch / 9.0))) + 1)
    t = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    u = np.linspace(0.0, L, nt)
    frac = (u[:, None] / pitch - t[None, :] / (2.0 * math.pi)) % 1.0
    tri = 1.0 - np.abs(2.0 * frac - 1.0)
    tri = np.clip((tri - 0.12) / 0.76, 0.0, 1.0)
    r = rmin + (rmaj - rmin) * tri
    c, s = np.cos(t), np.sin(t)
    P = (p0[None, None, :] + u[:, None, None] * az[None, None, :]
         + r[:, :, None] * (c[None, :, None] * ax[None, None, :]
                            + s[None, :, None] * ay[None, None, :]))
    V = P.reshape(-1, 3)
    Q = grid_quads(nt, seg, close_n=True)
    f0 = np.stack([np.zeros(seg - 2, np.int64), np.arange(1, seg - 1),
                   np.arange(2, seg)], axis=1)
    T = np.concatenate([f0[:, ::-1], f0 + (nt - 1) * seg])
    kw.setdefault("bc", np.stack([np.repeat(u, seg), np.tile(t * rmaj, nt),
                                  np.zeros(nt * seg)], axis=1))
    return acc.solid(V, quads=Q, tris=T, mat=mat, **kw)


def hexsolid(acc, ctr, axis, af, h, mat=MAT_STEEL, cham=0.16, phase=0.0, **kw):
    """Hex head or nut: six flats, a 30 deg chamfer at each end, and a bore if
    `bore` is given.  Across-flats `af` is the spanner size."""
    bore = kw.pop("bore", 0.0)
    ctr = np.asarray(ctr, float)
    ax, ay, az = frame_of(axis)
    R = af / math.sqrt(3.0)
    ch = cham * h
    rings = [(0.0, R * 0.86), (ch, R), (h - ch, R), (h, R * 0.86)]
    t = phase + np.arange(6) * (math.pi / 3.0)
    c, s = np.cos(t), np.sin(t)
    Vs = []
    for (u, r) in rings:
        Vs.append(ctr[None, :] + u * az[None, :]
                  + r * (c[:, None] * ax[None, :] + s[:, None] * ay[None, :]))
    V = np.concatenate(Vs)
    Q = grid_quads(4, 6, close_n=True)
    T = None
    if bore > 1e-6:
        nb = 20
        tb = np.linspace(0.0, 2.0 * math.pi, nb, endpoint=False)
        cb, sb = np.cos(tb), np.sin(tb)
        for u in (0.0, h):
            V = np.concatenate([V, ctr[None, :] + u * az[None, :] + bore
                                * (cb[:, None] * ax[None, :] + sb[:, None] * ay[None, :])])
        n0 = 24
        # Cap ring: hex(6) -> bore ring, as TRIANGLES.  A quad fan across a
        # 6-to-20 ring produces 14 degenerate quads per cap, which `validate`
        # then deletes, leaving a hole in the top of every nut on the object.
        tris = []
        for (hexbase, borebase, rev) in ((0, n0, True), (18, n0 + nb, False)):
            for i in range(nb):
                j = (i + 1) % nb
                k = (i * 6) // nb
                k2 = (j * 6) // nb
                t = [(borebase + i, borebase + j, hexbase + k)]
                if k2 != k:
                    t.append((borebase + j, hexbase + k2, hexbase + k))
                for tt in t:
                    tris.append(tt[::-1] if rev else tt)
        T = np.asarray(tris, np.int64)
    else:
        f0 = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]], np.int64)
        T = np.concatenate([f0[:, ::-1], f0 + 18])
    kw.setdefault("bc", np.stack([V[:, 2] * 0.0 + 0.0,
                                  np.arctan2(V[:, 1] - ctr[1], V[:, 0] - ctr[0]) * R,
                                  np.zeros(len(V))], axis=1))
    return acc.solid(V, quads=Q, tris=T, mat=mat, **kw)


def annulus(acc, ctr, axis, rin, rout, t, seg=28, mat=MAT_STEEL, dome=0.0, **kw):
    """Washer.  `dome` bows the face, which is what a spring washer or a bent
    plain washer under an over-torqued nut actually does."""
    ctr = np.asarray(ctr, float)
    ax, ay, az = frame_of(axis)
    th = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    rings = [(rin, 0.0), (rout, dome), (rout, dome + t), (rin, t)]
    Vs = []
    for (r, u) in rings:
        Vs.append(ctr[None, :] + u * az[None, :]
                  + r * (c[:, None] * ax[None, :] + s[:, None] * ay[None, :]))
    V = np.concatenate(Vs)
    Q = grid_quads(4, seg, close_n=True)
    i = np.arange(seg); j = (i + 1) % seg
    Q = np.concatenate([Q, np.stack([3 * seg + i, 3 * seg + j, j, i], axis=1)])
    kw.setdefault("bc", np.stack([np.tile(th * rout, 4), np.repeat([0, 1, 2, 3], seg),
                                  np.zeros(4 * seg)], axis=1))
    return acc.solid(V, quads=Q, tris=None, mat=mat, **kw)


def csk_screw(acc, ctr, axis, d_head, d_shank, length, mat=MAT_STEEL,
              seg=22, drive=True, **kw):
    """A countersunk self-tapper: 90 deg head, a slot or cross drive, a plain
    neck and a threaded shank.  Head is 11 mm = 26 px, the drive recess 5 mm."""
    ctr = np.asarray(ctr, float)
    ax, ay, az = frame_of(axis)
    hh = 0.5 * (d_head - d_shank)
    th = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    rings = [(0.5 * d_head, 0.0), (0.5 * d_head, -0.0004),
             (0.5 * d_shank, -hh), (0.5 * d_shank, -hh - 0.0012)]
    Vs = [ctr[None, :] + u * az[None, :]
          + r * (c[:, None] * ax[None, :] + s[:, None] * ay[None, :])
          for (r, u) in rings]
    V = np.concatenate(Vs)
    Q = grid_quads(4, seg, close_n=True)
    # the head top: a shallow dished face with a cross recess
    rec = 0.30 * d_head
    top = ctr - 0.0009 * az
    V = np.concatenate([V, [top]])
    ti = len(V) - 1
    i = np.arange(seg); j = (i + 1) % seg
    T = np.stack([np.full(seg, ti), j, i], axis=1)
    acc.solid(V, quads=Q, tris=T, mat=mat, **kw)
    if length > hh + 0.002:
        threaded(acc, ctr - (hh + 0.0012) * az, ctr - length * az,
                 d_shank, max(0.0025, 0.42 * d_shank), seg=max(14, seg - 6),
                 mat=mat, **kw)
    if drive:
        for a in (0.0, math.pi * 0.5):
            e = math.cos(a) * ax + math.sin(a) * ay
            f = -math.sin(a) * ax + math.cos(a) * ay
            Q2 = np.array([[-rec, -0.00035], [rec, -0.00035],
                           [rec, 0.00035], [-rec, 0.00035]])
            prism(acc, Q2, ctr - 0.0011 * az, e, f, az, 0.0, 0.0010,
                  mat=mat, **kw)


# ==============================================================================
#  6.  THE SECTION — nine closed loops, and every wall thickness in it is real
# ==============================================================================
#     x = 15.00000  cover cap, outer face        <- the breach plane
#     x = 14.99760  cap wall inner (2.4 mm)
#     x = 14.97600  pressure plate, front face   (cap projects 24.0 mm)
#     x = 14.97000  pressure plate, back face    (6.0 mm plate)
#     x = 14.96650  GLASS outer face             (3.5 mm exterior gasket)
#     x = 14.95500  GLASS inner face             (11.5 mm laminate 5/1.5/5)
#     x = 14.95100  interior gasket back         (4.0 mm)
#     x = 14.94500  MULLION rebate face          (6.0 mm polyamide isolator)
#     x = 14.84000  MULLION back face            (105.0 mm of body)
#
# Sightline 75.0 mm.  Overall depth 160.0 mm.  Pane gap 30.0 mm, so the plate
# takes 16.0 mm of edge bite on every glass edge.  Walls: 3.2 mm rebate and
# sides, 3.5 mm back and web, 4.0 mm on the steel.

def arc_corners(ctr, r, a0, a1, seg, tag, rad=0.0):
    """A real arc, expressed as corners `arcpoly` will pass through untouched.
    A bore is not a fillet and must not be authored as one."""
    n = max(3, int(math.ceil(abs(a1 - a0) * r / seg)) + 1)
    t = np.linspace(a0, a1, n)
    return [(float(ctr[0] + r * math.cos(v)), float(ctr[1] + r * math.sin(v)),
             rad, tag) for v in t]


def _serrate(x0, x1, y, amp, n, tag, rad=0.00018):
    """n retaining teeth along a race wall, running x0 -> x1 at height y.
    0.35 mm teeth: 0.8 px each, but they are what stops a wedge gasket walking
    out of its race, and a race with smooth walls reads as a slot."""
    out = []
    for k in range(n):
        f = (k + 0.5) / n
        xc = x0 + (x1 - x0) * f
        d = (x1 - x0) / n * 0.30
        out.append((xc - d, y, rad, tag))
        out.append((xc, y + amp, rad, tag))
        out.append((xc + d, y, rad, tag))
    return out


def prof_cap():
    """Snap-on cover cap: 75 mm face, 1.1 mm nose radii, two barbed legs."""
    half = [
        (0.0000, 0.0000, 0.0000, "capface"),
        (0.0000, 0.0375, 0.0011, "capface"),
        (-0.0024, 0.0375, 0.0006, "capedge"),
        (-0.0024, 0.0170, 0.0010, "capunder"),
        (-0.0244, 0.0170, 0.0005, "capleg"),
        (-0.0252, 0.0186, 0.0004, "capbarb"),
        (-0.0264, 0.0186, 0.0004, "capbarb"),
        (-0.0272, 0.0168, 0.0004, "captip"),
        (-0.0272, 0.0150, 0.0004, "captip"),
        (-0.0024, 0.0150, 0.0012, "capleg_i"),
        (-0.0024, 0.0000, 0.0000, "capceil"),
    ]
    return arcpoly(mirror_half(half), SEG_FINE)


def prof_plate():
    """Pressure plate: cap race with a locking lip, screw channel, and two
    serrated exterior gasket races."""
    return arcpoly(mirror_half(_plate_half_corners()), SEG_FINE)


def _plate_half_corners():
    half = [
        (-0.0252, 0.0000, 0.0000, "platechan"),
        (-0.0252, 0.0072, 0.0005, "platechan"),
        (-0.0240, 0.0084, 0.0005, "platefront"),
        (-0.0240, 0.0146, 0.0004, "platefront"),
        (-0.0276, 0.0146, 0.0004, "race"),
        (-0.0276, 0.0192, 0.0004, "race"),
        (-0.0250, 0.0192, 0.0004, "race"),
        (-0.0250, 0.0176, 0.0003, "race"),
        (-0.0240, 0.0176, 0.0004, "platefront"),
        (-0.0240, 0.0310, 0.0008, "platefront"),
        (-0.0300, 0.0310, 0.0008, "plateedge"),
        (-0.0300, 0.0266, 0.0004, "gaskrace"),
    ]
    half += _serrate(-0.0296, -0.0276, 0.0266, -0.00035, 3, "gaskrace")
    half += [(-0.0272, 0.0266, 0.0004, "gaskrace"),
             (-0.0272, 0.0214, 0.0004, "gaskrace")]
    half += _serrate(-0.0276, -0.0296, 0.0214, 0.00035, 3, "gaskrace")
    half += [(-0.0300, 0.0214, 0.0004, "gaskrace"),
             (-0.0300, 0.0000, 0.0000, "plateback")]
    return half


def prof_plate_notched(side=+1, gap=0.0030):
    """The bottom 26 mm of the pressure plate, SPLIT down the centre line.

    That gap is the weep: water that gets past the exterior gasket runs down
    the glazing pocket and has to leave somewhere, and on a capped stick system
    it leaves through a notch in the foot of the plate, under the cap.  6 mm
    wide and 26 mm tall = 14 x 61 px, and it is the detail that says the wall
    was designed to be rained on.
    """
    half = _plate_half_corners()
    loop = [(half[0][0], gap, 0.0004, half[0][3])]
    loop += list(half[1:-1])
    loop += [(half[-1][0], gap, 0.0004, half[-1][3])]
    if side < 0:
        loop = [(x, -y, r, t) for (x, y, r, t) in reversed(loop)]
    return arcpoly(loop, SEG_FINE)


def prof_isolator(side=+1):
    """Glass-filled polyamide thermal isolator, one per glazing face.  THE
    THERMAL BREAK the manifest names: it is the only thing between the glass
    line and 105 mm of aluminium reaching into a heated showroom."""
    loop = [(-0.0490, 0.0092, 0.0006, "isoedge")]
    for (a, b) in ((0.0130, 0.0160), (0.0200, 0.0230), (0.0270, 0.0300)):
        loop += [(-0.0490, a, 0.0003, "isoface"),
                 (-0.0485, a + 0.0004, 0.0003, "isorib"),
                 (-0.0485, b - 0.0004, 0.0003, "isorib"),
                 (-0.0490, b, 0.0003, "isoface")]
    loop += [
        (-0.0490, 0.0352, 0.0006, "isoedge"),
        (-0.0550, 0.0352, 0.0004, "isoedge"),
        (-0.0550, 0.0344, 0.0003, "isofoot"),
        (-0.0562, 0.0344, 0.0003, "isofoot"),
        (-0.0562, 0.0322, 0.0003, "isofoot"),
        (-0.0550, 0.0322, 0.0003, "isofoot"),
        (-0.0550, 0.0122, 0.0003, "isofoot"),
        (-0.0562, 0.0122, 0.0003, "isofoot"),
        (-0.0562, 0.0100, 0.0003, "isofoot"),
        (-0.0550, 0.0100, 0.0003, "isofoot"),
        (-0.0550, 0.0092, 0.0004, "isoedge"),
    ]
    if side < 0:
        loop = [(x, -y, r, t) for (x, y, r, t) in reversed(loop)]
    return arcpoly(loop, SEG_FINE)


def prof_body():
    """The mullion itself: rebate face with the SP1 screw port opening through
    it, two isolator foot grooves a side, 105 mm of body, and an interior
    T-slot on the back face for the blind track.  ONE simple closed loop —
    the cells are separate sealed voids, below."""
    half = arc_corners((SP1_CENTRE_DX, 0.0), SP1_BORE_R,
                       math.pi, math.radians(36.03), SEG_FINE, "sp1")
    half += [
        (-0.0550, 0.0025, 0.0004, "sp1"),
        (-0.0550, 0.0100, 0.0003, "rebate"),
        (-0.0562, 0.0100, 0.0003, "isogroove"),
        (-0.0562, 0.0122, 0.0003, "isogroove"),
        (-0.0550, 0.0122, 0.0003, "rebate"),
        (-0.0550, 0.0322, 0.0003, "rebate"),
        (-0.0562, 0.0322, 0.0003, "isogroove"),
        (-0.0562, 0.0344, 0.0003, "isogroove"),
        (-0.0550, 0.0344, 0.0003, "rebate"),
        (-0.0550, 0.0375, 0.0014, "rebate"),
        (-0.1600, 0.0375, 0.0018, "side"),
        (-0.1600, 0.0055, 0.0004, "back"),
        (-0.1552, 0.0055, 0.0004, "tslot"),
        (-0.1552, 0.0078, 0.0004, "tslot"),
        (-0.1520, 0.0078, 0.0004, "tslot"),
        (-0.1520, 0.0000, 0.0000, "tslot"),
    ]
    return arcpoly(mirror_half(half), SEG_FINE)


def prof_cell_front():
    """Sealed front cell, notched around the SP1 screw-port boss."""
    half = [
        (-0.0690, 0.0000, 0.0000, "cell"),
        (-0.0690, 0.0080, 0.0015, "cell"),
        (-0.0582, 0.0080, 0.0015, "cell"),
        (-0.0582, 0.0343, 0.0028, "cell"),
        (-0.0950, 0.0343, 0.0028, "cell"),
        (-0.0950, 0.0000, 0.0000, "cell"),
    ]
    return arcpoly(mirror_half(half), SEG_COARSE)


def _screw_port_c(ctr, r_out=0.0068, r_bore=SP2_BORE_R, mouth=0.0050,
                  seg=SEG_COARSE):
    """The C of a back screw port, as an excursion of the cell boundary.

    The port bore is OPEN to the cell through a 5.0 mm mouth — that is what a
    screw port is, and it is why the cell and the bore are ONE void region and
    not two.  Entering at the back wall face, around the outside of the boss,
    in through the lower lip, the long way round the bore, out through the
    upper lip, and back onto the boss.
    """
    cx, cy = ctr
    xw = -0.1565                                   # back wall inner face
    dy = math.sqrt(max(r_out ** 2 - (cx - xw) ** 2, 1e-12))
    a_lo = math.atan2(-dy, xw - cx)                # where the boss meets the wall
    a_hi = math.atan2(+dy, xw - cx)
    half_m = 0.5 * mouth
    a_lip_lo = math.atan2(-half_m, math.sqrt(max(r_out ** 2 - half_m ** 2, 1e-12)))
    a_lip_hi = -a_lip_lo
    b_lip_lo = math.atan2(-half_m, math.sqrt(max(r_bore ** 2 - half_m ** 2, 1e-12)))
    b_lip_hi = -b_lip_lo
    # round the OUTSIDE of the boss (a_lo -> a_lip_lo, increasing, past the
    # bottom), in along the lower lip face, the LONG way round the bore so the
    # mouth stays open (b_lip_lo -> b_lip_hi - 2pi, decreasing), out along the
    # upper lip face, and back around the boss to the wall.
    out = arc_corners(ctr, r_out, a_lo, a_lip_lo, seg, "port")
    out += arc_corners(ctr, r_bore, b_lip_lo, b_lip_hi - 2.0 * math.pi,
                       seg, "port")
    out += arc_corners(ctr, r_out, a_lip_hi, a_hi, seg, "port")
    return out


def prof_cell_back():
    """Sealed back cell, with the T-slot boss intruding from the back wall and
    a screw port at y = +-25 mm on each side of it."""
    half = [
        (-0.1490, 0.0000, 0.0000, "cell"),
        (-0.1490, 0.0110, 0.0012, "cell"),
        (-0.1565, 0.0110, 0.0012, "cell"),
    ]
    half += _screw_port_c(SP2_CENTRE[0])
    half += [
        (-0.1565, 0.0343, 0.0028, "cell"),
        (-0.0985, 0.0343, 0.0028, "cell"),
        (-0.0985, 0.0000, 0.0000, "cell"),
    ]
    return arcpoly(mirror_half(half), SEG_COARSE)


def _rrect(x0, x1, y0, y1, r, tag):
    return [(x0, y0, r, tag), (x1, y0, r, tag), (x1, y1, r, tag), (x0, y1, r, tag)]


def prof_steel_out():
    """60 x 36 x 4 mm galvanised RHS reinforcement, in the back cell.

    A 105 mm deep aluminium mullion cannot carry 2.2 m of tributary width over
    a 6.2 m single span on its own; every real one of this depth has a steel
    inside it.  It is invisible until something tears the extrusion open, and
    it is the reason ``mullion_bent_stub`` folds at a plastic hinge instead of
    bending like a drinking straw.
    """
    return arcpoly(_rrect(-0.1420, -0.1060, -0.0300, 0.0300, 0.0060, "steel"),
                   SEG_COARSE)


def prof_steel_in():
    return arcpoly(_rrect(-0.1380, -0.1100, -0.0260, 0.0260, 0.0040, "steel"),
                   SEG_COARSE)


# ==============================================================================
#  7.  STRAIGHTNESS, AND EVERYTHING BOLTED TO THE EXTRUSION
# ==============================================================================

def bow_at(rec, z):
    """The extrusion's own lack of straightness at height z.  -> (dx, dy, twist)

    EN 12020-2 allows 1.3 mm of bow per metre for a 6 m aluminium profile.  This
    file uses 0.8-2.1 mm total and 0.10-0.40 deg of twist, pinned to zero at
    both ends because the member is held there.  It is inside tolerance and
    outside "identical", which is the whole point: eleven dead-straight
    mullions is the tell that nothing was fabricated.
    """
    u = (np.asarray(z, float) - rec["z0"]) / EXTRUSION_LEN
    s1 = np.sin(math.pi * u)
    s2 = np.sin(2.0 * math.pi * u + rec["bow_ph"])
    dx = rec["bow_x"] * s1 + rec["bow_x2"] * s2
    dy = rec["bow_y"] * s1 + rec["bow_y2"] * s2
    th = rec["twist"] * s1 + rec["twist2"] * (u - 0.5) * 2.0
    return dx, dy, th


def warp(rec, x, y, z):
    """A section-frame point -> the same point on the BOWED, TWISTED member.

    Every fitting that touches the extrusion goes through here.  A 2 mm bow with
    an ink-jet mark modelled on the nominal plane is an ink-jet mark floating
    2 mm off the metal, which at 2333 px/m is 4.7 px of daylight under it.
    """
    dx, dy, th = bow_at(rec, z)
    cx, cy = TW_CENTRE
    ct, st = np.cos(th), np.sin(th)
    X = cx + (x - cx) * ct - (y - cy) * st + dx
    Y = cy + (x - cx) * st + (y - cy) * ct + dy
    return float(X), float(Y)


def wpt(rec, x, y, z):
    X, Y = warp(rec, x, y, z)
    return np.array([X, Y, float(z)])


# ------------------------------------------------------------------ 5x7 ink jet
# The fabrication mark an extrusion carries out of the die.  A 5x7 dot matrix at
# 0.9 mm pitch: each dot is 0.55 mm = 1.3 px and 0.10 mm proud, so the line reads
# as a legible rhythm rather than as a smudge, and the SERIAL IS DIFFERENT ON
# EVERY MULLION.  Built by hand, like everything else here.
FONT57 = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "10001", "11001", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    " ": ("00000",) * 7,
}


def ink_line(acc, rec, text, z0, y0, pitch=0.00090, dot=0.00055,
             proud=0.00010, faded=0.0):
    """One line of ink-jet code, running UP the back face of the mullion.

    `faded` drops dots at random — an ink-jet head with a blocked nozzle leaves
    a dotted line with holes in it, and every extrusion in a bundle came off the
    same head on a different day.
    """
    n = 0
    for ci, ch in enumerate(text.upper()):
        g = FONT57.get(ch)
        if g is None:
            continue
        for r in range(7):
            row = g[r] if len(g) > r else "00000"
            for c in range(min(5, len(row))):
                if row[c] != "1":
                    continue
                if faded > 0.0 and h01(rec["uid"], ci, r, c, 911) < faded:
                    continue
                z = z0 + (ci * 6 + c) * pitch
                y = y0 + (6 - r) * pitch
                X, Y = warp(rec, DX_BODY_B, y, z)
                O = np.array([X, Y, z])
                ez = np.array([-math.cos(bow_at(rec, z)[2]),
                               -math.sin(bow_at(rec, z)[2]), 0.0])
                ex = np.array([0.0, 0.0, 1.0])
                ey = np.cross(ez, ex)
                h = 0.5 * dot
                Q2 = np.array([[-h, -h], [h, -h], [h, h], [-h, h]])
                prism(acc, Q2, O, ex, ey, ez, -0.00020, proud, mat=MAT_INK,
                      mu_exp=0.02, mu_wear=0.35, mu_dirt=0.25, mu_ao=0.1,
                      mu_h=z, mu_pid=0.83)
                n += 1
    return n


# ------------------------------------------------------------------- the base
def build_base(acc, rec):
    """Foot: nylon pad, packing shims, base spigot with its flange, two M12
    anchor studs into the slab, and the two M8 bolts that pin the spigot into
    the mullion.  THE ONE PLACE THE FILM CAN GET TO 1.6 m AND SEE FASTENERS."""
    z_pad = 0.0
    z_shim = z_pad + PAD_T
    zf0 = z_shim + rec["shim_total"]
    zf1 = zf0 + FLANGE_T                     # = rec["z0"], the extrusion's foot
    cx = -0.1075                             # base plate centre, depth
    ex = np.array([1.0, 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])

    # 1. the nylon isolation pad: aluminium must not sit on concrete
    chbox(acc, cx - 0.062, cx + 0.062, -0.077, 0.077, z_pad, z_shim,
          cham=0.0005, mat=MAT_NYLON, mu_exp=0.05, mu_dirt=0.85, mu_ao=0.55,
          mu_wear=0.2, mu_h=z_pad, mu_pid=0.11)

    # 2. the packing shims.  Levelling a 6.2 m member on a poured slab is done
    #    with a stack of these and NOBODY trims them flush.
    zt = z_shim
    for k, t in enumerate(rec["shims"]):
        ov = rec["shim_out"][k]              # how far this one sticks out
        rot = rec["shim_rot"][k]
        w = 0.050 + 0.012 * h01(rec["uid"], k, 51)
        Q2 = np.array([[-0.048, -0.041 - ov], [0.048, -0.041 - ov],
                       [0.048, 0.041 + ov * 0.15], [-0.048, 0.041 + ov * 0.15]])
        cr, sr = math.cos(rot), math.sin(rot)
        Q2 = np.stack([Q2[:, 0] * cr - Q2[:, 1] * sr,
                       Q2[:, 0] * sr + Q2[:, 1] * cr], axis=1)
        chbox(acc, cx + Q2[:, 0].min(), cx + Q2[:, 0].max(),
              Q2[:, 1].min(), Q2[:, 1].max(), zt, zt + t,
              cham=min(0.0004, t * 0.28), mat=MAT_GALV,
              mu_exp=0.15, mu_dirt=0.7, mu_ao=0.6,
              mu_wear=0.5 + 0.3 * w, mu_h=zt, mu_pid=0.2 + 0.07 * k)
        zt += t

    # 3. the base spigot flange, cast, with a broken arris all round
    chbox(acc, cx - 0.060, cx + 0.060, -0.075, 0.075, zf0, zf1,
          cham=0.0010, mat=MAT_ALU, mu_exp=0.10, mu_dirt=0.75, mu_ao=0.35,
          mu_wear=0.55, mu_h=zf0, mu_pid=0.31)
    # 4. the spigot itself, plugged into the back cell
    chbox(acc, -0.1450, -0.1020, -0.0300, 0.0300, zf1 - 0.001,
          zf1 + SPIGOT_PLUG, cham=0.0012, mat=MAT_ALU,
          mu_exp=0.0, mu_dirt=0.3, mu_ao=0.9, mu_wear=0.1,
          mu_h=zf1, mu_pid=0.37)

    # 5. two M12 A2 anchor studs, 90 mm into the slab, with washer and nut.
    #    The thread is a real helix: it is 4 px of rhythm on a silhouette.
    for sgn in (-1, +1):
        yA = sgn * 0.052
        key = (rec["uid"], 1 if sgn > 0 else 0)
        prot = hrange(0.0022, 0.0072, key, 71)          # thread past the nut
        nutrot = hrange(0.0, math.pi / 3.0, key, 73)
        tube(acc, (cx, yA, -ANCHOR_EMBED), (cx, yA, 0.0), 0.0065, seg=18,
             mat=MAT_STEEL, mu_exp=0.0, mu_ao=0.9, mu_dirt=0.6, mu_h=-0.02,
             mu_pid=0.41)
        top = zf1 + 0.0025 + 0.0105 + prot
        threaded(acc, (cx, yA, -0.004), (cx, yA, top), 0.012, 0.00175, seg=26,
                 mat=MAT_STEEL, mu_exp=0.35, mu_wear=0.75, mu_dirt=0.5,
                 mu_ao=0.3, mu_h=zf1, mu_pid=0.43)
        annulus(acc, (cx, yA, zf1), (0, 0, 1), 0.0066, 0.0120, 0.0025, seg=24,
                mat=MAT_STEEL, dome=hrange(-0.0004, 0.0002, key, 77),
                mu_exp=0.3, mu_wear=0.8, mu_dirt=0.55, mu_ao=0.25,
                mu_h=zf1, mu_pid=0.47)
        hexsolid(acc, (cx, yA, zf1 + 0.0025), (0, 0, 1), 0.019, 0.0105,
                 mat=MAT_STEEL, phase=nutrot, bore=0.0062,
                 mu_exp=0.35, mu_wear=0.9, mu_dirt=0.45, mu_ao=0.15,
                 mu_h=zf1, mu_pid=0.53)
        if rec["jam_nut"] and sgn == rec["jam_side"]:
            hexsolid(acc, (cx, yA, zf1 + 0.0025 + 0.0105), (0, 0, 1), 0.019,
                     0.0072, mat=MAT_STEEL, phase=nutrot + 0.4, bore=0.0062,
                     mu_exp=0.35, mu_wear=0.85, mu_dirt=0.4, mu_h=zf1,
                     mu_pid=0.57)

    # 6. two M8 bolts pinning the spigot, from ONE side only — which is how it
    #    is done, and which side varies down the wall.
    sd = rec["bolt_side"]
    for k, dz in enumerate(rec["bolt_z"]):
        z = zf1 + dz
        X, Y = warp(rec, -0.1235, sd * 0.0375, z)
        n = np.array([0.0, float(sd), 0.0])
        annulus(acc, (X, Y, z), n, 0.0045, 0.0085, 0.0018, seg=20,
                mat=MAT_STEEL, mu_exp=0.05, mu_wear=0.8, mu_dirt=0.4,
                mu_h=z, mu_pid=0.61)
        hexsolid(acc, (X + n[0] * 0.0018, Y + n[1] * 0.0018, z), n, 0.013,
                 0.0055, mat=MAT_STEEL,
                 phase=hrange(0.0, 1.05, rec["uid"], k, 83),
                 mu_exp=0.05, mu_wear=0.95, mu_dirt=0.35, mu_h=z, mu_pid=0.63)
        tube(acc, (X, Y, z), (X - n[0] * 0.030, Y - n[1] * 0.030, z), 0.0040,
             seg=14, mat=MAT_STEEL, mu_ao=0.9, mu_h=z, mu_pid=0.65)


# -------------------------------------------------------------------- the head
def build_head(acc, rec):
    """Slip head: the spigot is fixed to the structure and the mullion hangs
    off it with an expansion gap, so a 6.2 m aluminium member can grow 4 mm
    across a 60 K swing without buckling the wall.  THE GAP IS DIFFERENT ON
    EVERY MULLION because it was set on a different afternoon."""
    ex = np.array([1.0, 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    z_top = rec["z1"]
    gap = rec["head_gap"]
    chbox(acc, -0.1450, -0.1020, -0.0300, 0.0300,
          z_top - SPIGOT_PLUG, z_top + gap, cham=0.0012, mat=MAT_ALU,
          mu_exp=0.0, mu_dirt=0.25, mu_ao=0.85, mu_wear=0.15,
          mu_h=z_top, mu_pid=0.71)
    zp = z_top + gap
    chbox(acc, -0.1785, -0.0685, -0.075, 0.075, zp, zp + 0.010,
          cham=0.0010, mat=MAT_ALU, mu_exp=0.02, mu_dirt=0.5, mu_ao=0.5,
          mu_wear=0.2, mu_h=zp, mu_pid=0.73)
    for sgn in (-1, +1):
        yA = sgn * 0.050
        key = (rec["uid"], 2 + (sgn > 0), 91)
        annulus(acc, (-0.1235, yA, zp + 0.010), (0, 0, 1), 0.0055, 0.0125,
                0.0025, seg=22, mat=MAT_STEEL, mu_exp=0.02, mu_wear=0.6,
                mu_dirt=0.35, mu_h=zp, mu_pid=0.77)
        hexsolid(acc, (-0.1235, yA, zp + 0.0125), (0, 0, 1), 0.017, 0.0090,
                 mat=MAT_STEEL, phase=hrange(0.0, 1.05, key),
                 mu_exp=0.02, mu_wear=0.7, mu_dirt=0.3, mu_h=zp, mu_pid=0.79)
        threaded(acc, (-0.1235, yA, zp - 0.004), (-0.1235, yA, zp + 0.026),
                 0.010, 0.0015, seg=22, mat=MAT_STEEL, mu_exp=0.02,
                 mu_wear=0.55, mu_h=zp, mu_pid=0.81)


# ------------------------------------------------- pressure-plate fixing screws
def build_screws(acc, rec):
    """M6 x 40 countersunk self-tappers into the SP1 screw port at ~250 mm
    centres.  All but the lowest and highest are behind the cap; those two are
    the only fasteners on the exterior of the wall a lens ever resolves, and
    they are 26 px across."""
    z0 = rec["z0"] + PLATE_INSET_BOT + 0.032
    z1 = rec["z1"] - PLATE_INSET_TOP - 0.032
    n = rec["n_screws"]
    for k in range(n):
        f = k / float(max(n - 1, 1))
        z = z0 + (z1 - z0) * f + hrange(-0.004, 0.004, rec["uid"], k, 97)
        if k in rec["screw_missing"]:
            continue
        exposed = (z < rec["z0"] + CAP_INSET_BOT - 0.004
                   or z > rec["z1"] - CAP_INSET_TOP + 0.004)
        X, Y = warp(rec, -0.0252, 0.0, z)
        n_out = np.array([math.cos(bow_at(rec, z)[2]),
                          math.sin(bow_at(rec, z)[2]), 0.0])
        seat = hrange(-0.0004, 0.0006, rec["uid"], k, 101)   # over/under driven
        csk_screw(acc, (X + n_out[0] * seat, Y + n_out[1] * seat, z), n_out,
                  0.0112, 0.0060, 0.0380 if exposed else 0.0090,
                  seg=24 if exposed else 12, mat=MAT_STEEL, drive=exposed,
                  mu_exp=0.75 if exposed else 0.1,
                  mu_wear=0.9 if exposed else 0.2,
                  mu_dirt=0.5, mu_ao=0.35, mu_h=z, mu_pid=0.87 + 0.01 * (k % 5))


# ------------------------------------------------------- what lives in a T-slot
def build_dust(acc, rec):
    """The manifest's third variation axis, as GEOMETRY: site dust does not sit
    on a surface as a colour, it FILLETS a corner.  A 0.8-1.6 mm fillet in the
    back T-slot and along the top of the base flange is 2-4 px of radius that
    catches the skylight where the bare corner would be black."""
    for (band0, band1, r) in rec["dust_bands"]:
        zs = ring_plan(band0, band1, 0.055)
        for sgn in (-1, +1):
            V, Q = [], []
            for j, z in enumerate(zs):
                t = math.sin(math.pi * (z - band0) / max(band1 - band0, 1e-6))
                rr = r * (0.35 + 0.65 * t)
                for (px, py) in ((-0.1520 + 0.0002, sgn * (0.0078 - 0.0002)),
                                 (-0.1520 + 0.0002 + rr, sgn * (0.0078 - 0.0002)),
                                 (-0.1520 + 0.0002, sgn * (0.0078 - 0.0002 - rr))):
                    X, Y = warp(rec, px, py, z)
                    V.append((X, Y, z))
            V = np.asarray(V)
            m = len(zs)
            Q = grid_quads(m, 3, close_n=True)
            T = np.array([[0, 2, 1],
                          [(m - 1) * 3, (m - 1) * 3 + 1, (m - 1) * 3 + 2]],
                         np.int64)
            acc.solid(V, quads=Q, tris=T, mat=MAT_ALU,
                      mu_exp=0.0, mu_dirt=1.0, mu_ao=0.95, mu_wear=0.0,
                      mu_h=float(zs[0]), mu_pid=0.93,
                      bc=np.stack([V[:, 2], V[:, 1] * 0.0, np.zeros(len(V))],
                                  axis=1))


# ------------------------------------------------------ jamb closure (2 of 11)
def build_jamb_flashing(acc, rec):
    """Mullions 0 and 10 are jambs: they meet the side walls, so they carry a
    folded 1.5 mm closure flashing the other nine do not have, pop-rivetted at
    400 mm centres.  A DIFFERENT TOPOLOGY, not a different transform."""
    sd = rec["jamb_side"]
    z0 = rec["z0"] + 0.020
    z1 = rec["z1"] - 0.020
    zs = ring_plan(z0, z1, 0.070)
    prof = [(-0.0300, 0.0), (-0.1600, 0.0), (-0.1600, 0.0180),
            (-0.1585, 0.0180), (-0.1585, 0.0015), (-0.0300, 0.0015)]
    V = []
    for z in zs:
        # the flashing hugs the side face (0.8 mm clear of it) and returns
        # 18 mm to die into the plaster line of the side wall
        X0, Y0 = warp(rec, 0.0, sd * 0.0383, z)
        Xr, Yr = warp(rec, -1.0, sd * 0.0383, z)
        exd = np.array([Xr - X0, Yr - Y0])
        exd /= max(float(np.linalg.norm(exd)), 1e-12)
        eyd = np.array([-exd[1], exd[0]]) * sd
        for (px, py) in prof:
            P = np.array([X0, Y0]) + exd * (-px) + eyd * py
            V.append((P[0], P[1], z))
    V = np.asarray(V)
    Q = grid_quads(len(zs), len(prof), close_n=True)
    acc.solid(V, quads=Q, tris=None, mat=MAT_ALU,
              mu_exp=0.25, mu_dirt=0.5, mu_ao=0.45, mu_wear=0.7,
              mu_h=float(zs[0]), mu_pid=0.97,
              bc=np.stack([V[:, 2], V[:, 1], np.zeros(len(V))], axis=1))
    for k in range(int((z1 - z0) / 0.40) + 1):
        z = z0 + 0.20 + k * 0.40
        if z > z1:
            break
        X, Y = warp(rec, -0.1000, sd * 0.0383, z)
        n = np.array([0.0, float(sd), 0.0])
        tube(acc, (X, Y, z), (X + n[0] * 0.0016, Y + n[1] * 0.0016, z), 0.0024,
             seg=12, mat=MAT_STEEL, mu_exp=0.3, mu_wear=0.6, mu_h=z, mu_pid=0.99)


# ==============================================================================
#  8.  THE ELEVEN — one record each, and eleven different meshes out of them
# ==============================================================================
# `variation_axes` in the manifest are "anodising tone", "fixing wear" and "dust
# in the channel".  Two of those three are SHADING axes, and a wall whose only
# difference is shading is the failure the brief names.  So the record carries
# them AND eleven geometric axes underneath:
#
#   bow and twist          every extrusion is its own curve
#   shim stack             1-4 shims, so the foot of every mullion is at a
#                          different height and one of them sticks out
#   anchor hardware        nut clocking, thread protrusion, a jam nut on some
#   spigot bolt side       left or right, and at different heights
#   head expansion gap     10-22 mm, set on a different afternoon
#   screw count and pitch  22-26, jittered, and some are missing or proud
#   dent field             3-9 handling dents, different places, different depths
#   cap end cut            +-4 mm, and the cap is notched on some
#   ink-jet serial         a different string, printed by a nozzle that blocks
#   dust bands             different heights, different fillet radii
#   jamb closure           mullions 0 and 10 carry a part the others do not

SERIAL_LOT = ("A7", "B2", "B9", "C4", "D1", "D8", "E3", "F6")


def records():
    """The deterministic plan for all eleven.  No bpy, no randomness that is
    not a hash of the index."""
    out = []
    for i in range(N_MULLION):
        k = ("MUL", i)
        nsh = 1 + int(h01(k, 11) * 4.0)
        shims = [hpick((0.0010, 0.0015, 0.0020, 0.0030), k, 13, j)
                 for j in range(nsh)]
        tot = float(sum(shims))
        z0 = PAD_T + tot + FLANGE_T
        z1 = z0 + EXTRUSION_LEN
        nd_body = 6 + int(h01(k, 17) * 8.0)
        nd_cap = 4 + int(h01(k, 19) * 6.0)
        # half of them below 2.0 m: that is where a knee, a ladder, a trestle
        # and a sheet of glass on a trolley actually reach
        dents_body = [(z0 + (hrange(0.02, 0.30, k, 23, j) if j % 2 == 0
                             else hrange(0.15, 0.98, k, 23, j)) * EXTRUSION_LEN,
                       h01(k, 29, j),
                       hrange(0.004, 0.022, k, 31, j),
                       hrange(0.0035, 0.0135, k, 37, j),
                       -hrange(0.00018, 0.00062, k, 41, j))
                      for j in range(nd_body)]
        dents_cap = [(z0 + (hrange(0.02, 0.32, k, 43, j) if j % 3 == 0
                            else hrange(0.05, 0.99, k, 43, j)) * EXTRUSION_LEN,
                      h01(k, 47, j),
                      hrange(0.005, 0.026, k, 53, j),
                      hrange(0.004, 0.016, k, 59, j),
                      -hrange(0.00016, 0.00055, k, 61, j))
                     for j in range(nd_cap)]
        nb = 1 + int(h01(k, 67) * 3.0)
        bands = []
        for j in range(nb):
            a = z0 + hrange(0.02, 0.86, k, 71, j) * EXTRUSION_LEN
            bands.append((a, a + hrange(0.25, 1.60, k, 73, j),
                          hrange(0.0006, 0.0017, k, 79, j)))
        nsc = 22 + int(h01(k, 83) * 5.0)
        miss = set()
        if h01(k, 89) < 0.45:
            miss.add(2 + int(h01(k, 97) * (nsc - 4)))
        lot = hpick(SERIAL_LOT, k, 101)
        out.append(dict(
            uid=i, y=y_of(i), z0=z0, z1=z1,
            shims=shims, shim_total=tot,
            shim_out=[hrange(0.0, 0.0060, k, 103, j) for j in range(nsh)],
            shim_rot=[hrange(-0.06, 0.06, k, 107, j) for j in range(nsh)],
            bow_x=hrange(-0.0011, 0.0011, k, 109),
            bow_x2=hrange(-0.0005, 0.0005, k, 113),
            bow_y=hrange(-0.0010, 0.0010, k, 127),
            bow_y2=hrange(-0.0004, 0.0004, k, 131),
            bow_ph=hrange(0.0, 6.283, k, 137),
            twist=math.radians(hrange(-0.28, 0.28, k, 139)),
            twist2=math.radians(hrange(-0.16, 0.16, k, 149)),
            head_gap=hrange(0.010, 0.022, k, 151),
            n_screws=nsc, screw_missing=miss,
            bolt_side=(1 if h01(k, 157) < 0.5 else -1),
            bolt_z=(hrange(0.048, 0.062, k, 163),
                    hrange(0.108, 0.126, k, 167)),
            jam_nut=(h01(k, 173) < 0.36),
            jam_side=(1 if h01(k, 179) < 0.5 else -1),
            cap_cut=hrange(-0.004, 0.004, k, 181),
            weep_gap=hrange(0.0025, 0.0042, k, 233),
            dents_body=dents_body, dents_cap=dents_cap,
            dust_bands=bands,
            jamb=(i in (0, N_MULLION - 1)),
            jamb_side=(-1 if i == 0 else +1),
            tone=h01(k, 191),                # the anodising batch
            grime=hrange(0.15, 0.95, k, 193),
            film=hrange(0.0, 0.85, k, 197),  # protective-film residue left on
            ofs=(hrange(0.0, 23.0, k, 199), hrange(0.0, 23.0, k, 211),
                 hrange(0.0, 23.0, k, 223)),
            serial="OCTAL FW75-SI 6063-T6 EN12020-2",
            serial2="L6200 BAY%02d LOT%s %02d/06/26"
                    % (i + 1, lot, 3 + int(h01(k, 227) * 24)),
            faded=hrange(0.0, 0.10, k, 229),
        ))
    return out


def build_mullion(rec, coll, mats):
    """One mullion -> ONE mesh, recentred on its own bounding-box centre."""
    acc = Acc("%s%s%02d" % (SPFX, "Mullion", rec["uid"]))
    z0, z1 = rec["z0"], rec["z1"]
    bd = [(d[0], 0.045, 0.006) for d in rec["dents_body"]]
    bc = [(d[0], 0.045, 0.006) for d in rec["dents_cap"]]
    ends_b = [(z0 + 0.020, 0.045, 0.004), (z1 - 0.020, 0.045, 0.004)]

    # ---- the extrusion ---------------------------------------------------
    zb = ring_plan(z0, z1, 0.040, ends_b + bd
                   + [(t, 0.040, 0.010) for t in TRANSOM_Z]
                   + [(z0 + 1.28, 0.11, 0.006)])
    P, T, R = prof_body()
    loft(acc, P, T, R, zb, rec=rec, dents=rec["dents_body"],
         pid=0.05, chamfer=0.00030,
         wear_fn=lambda z: 0.55 + 0.45 * np.exp(-((z - z0) / 1.30) ** 2))
    for pf in (prof_cell_front, prof_cell_back):
        zc = ring_plan(z0 + 0.0004, z1 - 0.0004, 0.30)
        Pc, Tc, Rc = pf()
        loft(acc, Pc, Tc, Rc, zc, rec=rec, pid=0.09, void=True)
    zs = ring_plan(z0 + STEEL_INSET, z1 - STEEL_INSET, 0.30)
    Ps, Ts, Rs = prof_steel_out()
    loft(acc, Ps, Ts, Rs, zs, rec=rec, pid=0.13)
    Ps, Ts, Rs = prof_steel_in()
    loft(acc, Ps, Ts, Rs, zs, rec=rec, pid=0.15, void=True)

    # ---- the cap -----------------------------------------------------------
    cz0 = z0 + CAP_INSET_BOT + rec["cap_cut"]
    cz1 = z1 - CAP_INSET_TOP - rec["cap_cut"] * 0.6
    zc = ring_plan(cz0, cz1, 0.045,
                   [(cz0 + 0.015, 0.030, 0.003), (cz1 - 0.015, 0.030, 0.003)] + bc)
    P, T, R = prof_cap()
    loft(acc, P, T, R, zc, rec=rec, dents=rec["dents_cap"],
         pid=0.21, chamfer=0.00025,
         wear_fn=lambda z: 0.45 + 0.55 * np.exp(-((z - z0) / 1.60) ** 2))

    # ---- the pressure plate and the two isolators ---------------------------
    pz0 = z0 + PLATE_INSET_BOT
    pz1 = z1 - PLATE_INSET_TOP
    wz = pz0 + 0.026                       # top of the two drainage notches
    zp = ring_plan(wz, pz1, 0.090,
                   [(wz + 0.012, 0.030, 0.003), (pz1 - 0.020, 0.040, 0.004)])
    P, T, R = prof_plate()
    loft(acc, P, T, R, zp, rec=rec, pid=0.27, chamfer=0.00020)
    zw = ring_plan(pz0, wz + 0.0002, 0.006)
    for sgn in (+1, -1):
        P, T, R = prof_plate_notched(sgn, gap=rec["weep_gap"])
        loft(acc, P, T, R, zw, rec=rec,
             pid=0.29 if sgn > 0 else 0.31, chamfer=0.00020)
    zi = ring_plan(pz0 + 0.004, pz1 - 0.004, 0.140,
                   [(pz0 + 0.020, 0.030, 0.006), (pz1 - 0.020, 0.030, 0.006)])
    for sgn in (+1, -1):
        P, T, R = prof_isolator(sgn)
        loft(acc, P, T, R, zi, rec=rec, pid=0.33 if sgn > 0 else 0.35,
             chamfer=0.00015)

    # ---- everything bolted to it -------------------------------------------
    build_base(acc, rec)
    build_head(acc, rec)
    build_screws(acc, rec)
    build_dust(acc, rec)
    if rec["jamb"]:
        build_jamb_flashing(acc, rec)
    ink_line(acc, rec, rec["serial"], z0 + 1.230, 0.0130, faded=rec["faded"])
    ink_line(acc, rec, rec["serial2"], z0 + 1.230, 0.0208, faded=rec["faded"])

    V, Q, T3, mq, mt, A, bcv = acc.arrays()
    if V.shape[0] == 0:
        raise RuntimeError("REFUSING: mullion %d built no geometry" % rec["uid"])
    ctr = (V.min(axis=0) + V.max(axis=0)) * 0.5
    Vl = V - ctr[None, :]
    me = _mesh_from(acc.name, Vl, Q, T3, mq, mt, A, bcv, rec)
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(acc.name, me)
    coll.objects.link(ob)
    O = np.array([FACE_X + ctr[0], rec["y"] + ctr[1], ctr[2]])
    place(ob, np.eye(3), O)
    ob["item"] = ITEM
    ob["mu_uid"] = int(rec["uid"])
    info = dict(verts=int(V.shape[0]), quads=int(Q.shape[0]),
                tris=int(T3.shape[0]),
                triangles=int(Q.shape[0] * 2 + T3.shape[0]),
                parts=acc.parts,
                size=[float(V[:, i].max() - V[:, i].min()) for i in range(3)])
    return ob, O, info


# ==============================================================================
#  9.  ARRAYS -> A BLENDER MESH
# ==============================================================================

def _shade_by_angle(me, deg=32.0):
    """Smooth everywhere except across a real arris.

    A 1.1 mm nose radius carried on 6 segments is a faceted bead at 2333 px/m if
    it is flat shaded, and a 24 mm cap reveal is a melted lump if the whole
    object is smoothed.  numpy against `sharp_edge`, because `shade_auto_smooth`
    needs a VIEW_3D context and cannot run headless (project Blender-5.x notes).
    """
    npoly = len(me.polygons)
    nloop = len(me.loops)
    nedge = len(me.edges)
    if not nedge or not npoly:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))
    fn = np.empty(npoly * 3, np.float32)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32); me.loops.foreach_get("vertex_index", lv)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64)
    b = lv[nxt].astype(np.int64)
    nv = len(me.vertices)
    key = np.minimum(a, b) * np.int64(nv) + np.maximum(a, b)
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    fs = face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    f0 = np.zeros(ng, np.int64)
    f1 = np.full(ng, -1, np.int64)
    np.copyto(f0, fs[np.flatnonzero(first)])
    second = np.flatnonzero(~first)
    if len(second):
        f1[grp[second]] = fs[second]
    dot = np.ones(ng)
    two = f1 >= 0
    if two.any():
        dot[two] = np.einsum("ij,ij->i", fn[f0[two]], fn[f1[two]])
    ang = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    sharp_key = ks[np.flatnonzero(first)][ang > deg]
    ev = np.empty(nedge * 2, np.int32); me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(nedge, 2).astype(np.int64)
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * np.int64(nv)
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _mesh_from(name, V, Q, T, mq, mt, A, bc, rec):
    nv, nq, nt = V.shape[0], Q.shape[0], T.shape[0]
    nf = nq + nt
    me = bpy.data.meshes.new(name)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(V, np.float32).ravel())
    me.loops.add(nq * 4 + nt * 3)
    loops = np.empty(nq * 4 + nt * 3, np.int32)
    loops[:nq * 4] = Q.astype(np.int32).ravel()
    loops[nq * 4:] = T.astype(np.int32).ravel()
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    ls = np.empty(nf, np.int32)
    lt = np.empty(nf, np.int32)
    ls[:nq] = np.arange(nq, dtype=np.int32) * 4
    lt[:nq] = 4
    ls[nq:] = nq * 4 + np.arange(nt, dtype=np.int32) * 3
    lt[nq:] = 3
    me.polygons.foreach_set("loop_start", ls)
    me.polygons.foreach_set("loop_total", lt)
    mi = np.empty(nf, np.int32)
    mi[:nq] = mq
    mi[nq:] = mt
    me.polygons.foreach_set("material_index", mi)
    me.update(calc_edges=True)
    for k in ATTR_F:
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.ascontiguousarray(A[k], np.float32))
    av = me.attributes.new("mu_bc", "FLOAT_VECTOR", "POINT")
    av.data.foreach_set("vector", np.ascontiguousarray(bc, np.float32).ravel())
    # PER-MULLION CONSTANTS, baked as POINT attributes rather than object custom
    # properties.  A geometry-nodes instance of an object resolves an OBJECT
    # attribute against the SOURCE object, so the only carrier that is certain
    # to travel with an instanced mesh is the mesh itself.
    for k, val in (("mu_tone", rec["tone"]), ("mu_grime", rec["grime"]),
                   ("mu_film", rec["film"])):
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.full(nv, float(val), np.float32))
    ofs = me.attributes.new("mu_ofs", "FLOAT_VECTOR", "POINT")
    ofs.data.foreach_set("vector", np.tile(
        np.asarray(rec["ofs"], np.float32), nv))
    me.validate(verbose=False)
    _shade_by_angle(me)
    return me


# ==============================================================================
# 10.  MATERIALS — six of them, every one procedural, none with an image node
# ==============================================================================

class NT(object):
    """Node DSL.  EVERY SOCKET IS ADDRESSED BY NAME, NOT BY INDEX.

    Measured, and it matters: in Blender 5.2 ``ShaderNodeBump`` has inputs
    (Strength, Distance, Filter Width, Height, Normal) — Filter Width was
    inserted at index 2 — so the 4.x idiom ``pin(nd, 2, height)`` now feeds the
    height map into FILTER WIDTH.  Names cost nothing and cannot rot.
    """

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 1
        nd.location = ((self.x % 15) * 220, -(self.x // 15) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, key, src):
        if src is None:
            return
        if key not in nd.inputs:
            raise KeyError("%s has no input %r" % (nd.bl_idname, key))
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[key])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[key])
        elif isinstance(src, (tuple, list)):
            nd.inputs[key].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[key].default_value = float(src)

    def _pin_i(self, nd, i, src):
        if src is None:
            return
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[i])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[i])
        elif isinstance(src, (tuple, list)):
            nd.inputs[i].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[i].default_value = float(src)

    def cmix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, "Factor", fac)
        self._pin_i(nd, 6, a)
        self._pin_i(nd, 7, b)
        return (nd, 2)

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, "Factor", fac)
        self._pin_i(nd, 2, a)
        self._pin_i(nd, 3, b)
        return (nd, 0)

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._pin_i(nd, 0, a)
        self._pin_i(nd, 1, b)
        return (nd, 0)

    def vmath(self, op, a=None, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self._pin_i(nd, 0, a)
        self._pin_i(nd, 1, b)
        if scale is not None:
            self._pin_i(nd, 3, scale)
        return (nd, 0)

    def noise(self, vec, scale, detail=8.0, rough=0.55, lac=2.0, out=0,
              dist=0.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Detail", detail)
        self.pin(nd, "Roughness", rough)
        self.pin(nd, "Lacunarity", lac)
        self.pin(nd, "Distortion", dist)
        return (nd, out)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0, smooth=None):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Randomness", rand)
        if smooth is not None and "Smoothness" in nd.inputs:
            self.pin(nd, "Smoothness", smooth)
        return (nd, out)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, direction="X",
             wtype="BANDS"):
        nd = self.n("ShaderNodeTexWave", wave_type=wtype,
                    bands_direction=direction)
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Distortion", distortion)
        self.pin(nd, "Detail", detail)
        return (nd, 1)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, "Fac", src)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = tuple(stops[0][1]) + (1.0,)
        for pos, col in stops[1:]:
            e = el.new(pos)
            e.color = tuple(col) + (1.0,)
        return (nd, 0)

    def attr(self, name, out=2, typ="GEOMETRY"):
        nd = self.n("ShaderNodeAttribute", attribute_type=typ)
        nd.attribute_name = name
        return (nd, out)

    def maprange(self, v, f0, f1, t0, t1, clamp=True):
        nd = self.n("ShaderNodeMapRange")
        nd.clamp = clamp
        self.pin(nd, "Value", v)
        self._pin_i(nd, 1, f0)
        self._pin_i(nd, 2, f1)
        self._pin_i(nd, 3, t0)
        self._pin_i(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance, normal=None):
        nd = self.n("ShaderNodeBump")
        self.pin(nd, "Strength", strength)
        self.pin(nd, "Distance", distance)
        self.pin(nd, "Height", height)
        if normal is not None:
            self.pin(nd, "Normal", normal)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, "Vector", vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self._pin_i(nd, 0, x)
        self._pin_i(nd, 1, y)
        self._pin_i(nd, 2, z)
        return (nd, 0)

    def geo(self, out):
        return (self.n("ShaderNodeNewGeometry"), out)

    def out(self, col, rough, metal=0.0, normal=None, spec=None, coat=None,
            aniso=None, aniso_rot=None, tangent=None):
        bs = self.n("ShaderNodeBsdfPrincipled")
        self.pin(bs, "Base Color", col)
        self.pin(bs, "Roughness", rough)
        self.pin(bs, "Metallic", metal)
        if normal is not None:
            self.pin(bs, "Normal", normal)
        if spec is not None:
            self.pin(bs, "Specular IOR Level", spec)
        if coat is not None:
            self.pin(bs, "Coat Weight", coat)
        if aniso is not None and "Anisotropic" in bs.inputs:
            self.pin(bs, "Anisotropic", aniso)
        if tangent is not None and "Tangent" in bs.inputs:
            self.pin(bs, "Tangent", tangent)
        o = self.n("ShaderNodeOutputMaterial")
        self.t.links.new(bs.outputs[0], o.inputs["Surface"])
        return self.m


def _common(t):
    """Object-space P (decorrelated per mullion), and this item's attributes.

    TexCoord -> Object, NEVER Geometry -> Position.  These objects sit at
    |P| ~ 15 m in world, which is survivable, but every one of the eleven is
    the SAME shape in its own object space, so an object-space field alone
    would paint eleven identical patterns.  `mu_ofs` is a per-mullion constant
    vector baked into the mesh; adding it decorrelates the lot.
    """
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    P = t.vmath("ADD", OBJ, t.attr("mu_ofs", 0))
    A = dict(
        P=P, Pl=OBJ,
        wear=t.attr("mu_wear"), edge=t.attr("mu_edge"), dirt=t.attr("mu_dirt"),
        ao=t.attr("mu_ao"), h=t.attr("mu_h"), pid=t.attr("mu_pid"),
        exp=t.attr("mu_exp"), tone=t.attr("mu_tone"),
        grime=t.attr("mu_grime"), film=t.attr("mu_film"),
        bc=t.attr("mu_bc", 1),
        up=t.sep(t.geo(1), 2),      # Geometry -> Normal.z: a DIRECTION, so it
                                    # carries no position-precision problem
        nx=t.sep(t.geo(1), 0),      # and Normal.x tells the outside of this
                                    # wall from the inside of it
    )
    return A


def mat_alu():
    """Clear-anodised 6063 extrusion.  The object is 96 % this material, so it
    carries the whole history:

      1. the ANODISING BATCH.  `mu_tone` is a per-mullion constant, and it is a
         STEP between members, not a gradient across the wall — two sticks out
         of two tanks differ by more than one stick differs along its length,
         and that is the manifest's first variation axis made physical.
      2. DIE LINES.  An extrusion die leaves 0.05-0.3 mm longitudinal scores.
         They run ALONG the member (`mu_bc.x`), so they are a bump that varies
         ACROSS it and is constant up it.  0.23 px wide: shading, not mesh.
      3. HANDLING.  Every scuff is transverse, because everything that touches
         a mullion on site moves across it: slings, suckers, a ladder, a knee.
      4. THE ARRIS.  20 microns of anodic film wears off an edge first.
      5. OXIDE BLOOM outside, where nothing wipes it, weighted by `mu_exp`.
      6. WHAT LIVES IN A RACE: `mu_ao` x `mu_dirt`, the third variation axis.
      7. RAIN STREAKS down the exterior only, and a splash line at the foot.
      8. PROTECTIVE-FILM RESIDUE: the tack line left where the blue film was
         peeled, which on a new facade is the single most recognisable mark.
    """
    t = NT(PFX + "Alu")
    A = _common(t)
    P, bc = A["P"], A["bc"]
    bx = t.sep(bc, 0)            # along the member (m)
    by = t.sep(bc, 1)            # across the section, by arclength (m)
    grain = t.comb(by, bx, 0.0)
    ext = t.maprange(A["exp"], 0.05, 0.65, 0.0, 1.0)

    # ---- 1. the batch ------------------------------------------------------
    tone = t.fmix(0.72, A["tone"],
                  t.noise(t.vmath("SCALE", P, scale=0.35), 1.2, 3.0, 0.5))
    body = t.cmix(t.maprange(tone, 0.10, 0.90, 0.0, 1.0),
                  PAL["alu_warm"], PAL["alu_cool"])
    body = t.cmix(t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 2.6, 5.0),
                             0.30, 0.78, 0.0, 0.55), body, PAL["alu_mid"])
    # a light band on what the sky sees, a dark one on what it does not
    body = t.cmix(t.math("MULTIPLY",
                         t.maprange(A["up"], 0.10, 0.90, 0.0, 1.0), 0.22),
                  body, PAL["alu_bright"])

    # ---- 2. die lines and mill brush --------------------------------------
    die = t.wave(grain, 620.0, 0.62, 4.0, "X")
    die2 = t.wave(grain, 1700.0, 0.35, 2.0, "X")
    brush = t.noise(t.comb(t.math("MULTIPLY", by, 340.0),
                           t.math("MULTIPLY", bx, 3.0), 0.0), 1.0, 4.0, 0.62)
    body = t.cmix(t.math("MULTIPLY",
                         t.maprange(brush, 0.32, 0.70, 0.0, 1.0), 0.17),
                  body, PAL["alu_bright"])

    # ---- 3. handling: transverse scuffs ------------------------------------
    v_scuff = t.vor(t.comb(t.math("MULTIPLY", bx, 26.0),
                           t.math("MULTIPLY", by, 190.0),
                           t.sep(P, 2)), 5.0, "F1", 0, 1.0)
    scuff = t.math("MULTIPLY", A["wear"],
                   t.maprange(v_scuff, 0.02, 0.20, 1.0, 0.0))
    scuff = t.math("MULTIPLY", scuff,
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 90.0,
                                      6.0, 0.6), 0.40, 0.82, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", scuff, 0.80), body, PAL["alu_scuff"])

    # ---- 4. the arris ------------------------------------------------------
    ew = t.math("MULTIPLY", A["edge"],
                t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 210.0, 6.0),
                           0.30, 0.80, 0.15, 1.0))
    ew = t.math("MULTIPLY", ew, t.maprange(A["wear"], 0.0, 0.8, 0.35, 1.0))
    body = t.cmix(t.math("MULTIPLY", ew, 0.62), body, PAL["alu_bright"])

    # ---- 5. oxide bloom, outside only --------------------------------------
    n_ox = t.noise(t.vmath("SCALE", P, scale=1.0), 7.5, 7.0, 0.68)
    ox = t.math("MULTIPLY", t.math("MULTIPLY", ext, A["grime"]),
                t.maprange(n_ox, 0.44, 0.82, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", ox, 0.42), body, PAL["alu_white"])

    # ---- 6. what lives in a race -------------------------------------------
    n_dust = t.noise(t.vmath("SCALE", P, scale=1.0), 22.0, 6.0, 0.58)
    slot = t.math("MULTIPLY",
                  t.math("MULTIPLY", A["ao"],
                         t.maprange(A["dirt"], 0.1, 0.9, 0.25, 1.0)),
                  t.maprange(n_dust, 0.22, 0.80, 0.38, 1.0))
    slot = t.math("MULTIPLY", slot, t.maprange(A["grime"], 0.0, 1.0, 0.45, 1.0))
    body = t.cmix(t.math("MULTIPLY", slot, 0.90), body, PAL["alu_slot"])
    body = t.cmix(t.math("MULTIPLY", slot, 0.35), body, PAL["dust"])

    # ---- 7. rain streaks and the splash line -------------------------------
    streak = t.noise(t.comb(t.math("MULTIPLY", bx, 0.9),
                            t.math("MULTIPLY", by, 46.0),
                            t.sep(P, 2)), 3.0, 6.0, 0.72)
    rain = t.math("MULTIPLY", t.math("MULTIPLY", ext, A["grime"]),
                  t.maprange(streak, 0.44, 0.86, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", rain, 0.34), body, PAL["grime"])
    splash = t.math("MULTIPLY", t.maprange(A["h"], 0.42, 0.03, 0.0, 1.0),
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 38.0,
                                       6.0, 0.62), 0.24, 0.84, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", splash, A["grime"]), 0.55),
                  body, PAL["grime"])

    # ---- 8. protective-film tack line --------------------------------------
    tack = t.math("MULTIPLY", A["film"],
                  t.maprange(t.noise(t.comb(t.math("MULTIPLY", bx, 1.6),
                                            t.math("MULTIPLY", by, 620.0),
                                            0.0), 2.2, 5.0), 0.52, 0.86, 0.0, 1.0))
    tack = t.math("MULTIPLY", tack, t.maprange(A["exp"], 0.2, 0.9, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY", tack, 0.30), body, PAL["film_tack"])

    # ---- 8b. the anodic film is CLOUDY, and that is a roughness event ------
    # Measured off the second look: with colour variation alone the extrusion
    # rendered as one flat tone, because on a semi-matt metal the eye reads the
    # SPECULAR, not the albedo.  A 20 micron anodic film is never laid down
    # evenly — the tank leaves a 40-120 mm cloudiness that shows up as a
    # roughness mottle of +-0.05 and almost no colour change at all.  This is
    # the single thing that stops 6.2 m of extrusion looking painted.
    mottle = t.noise(t.vmath("SCALE", P, scale=1.0), 3.6, 7.0, 0.70)
    mottle2 = t.noise(t.vmath("SCALE", P, scale=1.0), 13.0, 6.0, 0.62)
    cloud = t.fmix(0.45, t.maprange(mottle, 0.30, 0.74, 0.0, 1.0),
                   t.maprange(mottle2, 0.34, 0.70, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", cloud, 0.14), body, PAL["alu_dull"])

    # ---- 9. roughness ------------------------------------------------------
    # MEASURED against the first look, not chosen: clear anodising is a 20
    # micron oxide over the metal and it is SEMI-MATT.  0.40 at its cleanest,
    # 0.66 where a season of hands has been on it.  At 0.22 it renders chrome.
    rgh = t.maprange(tone, 0.15, 0.85, 0.40, 0.52)
    rgh = t.fmix(cloud, rgh, t.math("ADD", rgh, 0.115))
    rgh = t.fmix(t.math("MULTIPLY", scuff, 0.9), rgh, 0.66)
    rgh = t.fmix(t.math("MULTIPLY", ox, 0.9), rgh, 0.82)
    rgh = t.fmix(t.math("MULTIPLY", slot, 0.85), rgh, 0.86)
    rgh = t.fmix(t.math("MULTIPLY", rain, 0.7), rgh, 0.72)
    rgh = t.fmix(t.math("MULTIPLY", tack, 0.8), rgh, 0.30)
    rgh = t.fmix(t.math("MULTIPLY", ew, 0.55), rgh, 0.33)

    # ---- 10. the bump stack ------------------------------------------------
    b = t.bump(cloud, 0.20, 0.00060)
    b = t.bump(die, 0.42, 0.00016, normal=b)
    b = t.bump(die2, 0.26, 0.00007, normal=b)
    b = t.bump(brush, 0.20, 0.00007, normal=b)
    b = t.bump(t.maprange(v_scuff, 0.0, 0.11, 1.0, 0.0),
               t.math("MULTIPLY", scuff, 0.85), 0.00024, normal=b)
    b = t.bump(n_dust, t.math("MULTIPLY", slot, 0.55), 0.00040, normal=b)
    b = t.bump(n_ox, t.math("MULTIPLY", ox, 0.5), 0.00016, normal=b)
    return t.out(body, rgh, 0.92, normal=b, spec=0.5)


def mat_iso():
    """Glass-filled polyamide 6.6 thermal isolator: a moulded, not extruded,
    black with 25 % glass in it.  The fibres read as a fine pale speckle and
    the flow lines run with the die."""
    t = NT(PFX + "Iso")
    A = _common(t)
    P, bc = A["P"], A["bc"]
    fib = t.vor(t.comb(t.math("MULTIPLY", t.sep(bc, 0), 320.0),
                       t.math("MULTIPLY", t.sep(bc, 1), 900.0),
                       t.sep(P, 2)), 8.0, "F1", 0, 1.0)
    body = t.cmix(t.maprange(fib, 0.02, 0.16, 0.55, 0.0),
                  PAL["iso_black"], PAL["iso_grey"])
    flow = t.wave(t.comb(t.sep(bc, 1), t.sep(bc, 0), 0.0), 260.0, 0.7, 3.0, "X")
    body = t.cmix(t.math("MULTIPLY",
                         t.maprange(flow, 0.35, 0.75, 0.0, 1.0), 0.22),
                  body, PAL["iso_grey"])
    dust = t.math("MULTIPLY", t.math("MULTIPLY", A["dirt"], A["grime"]),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 26.0, 6.0),
                             0.28, 0.80, 0.2, 1.0))
    body = t.cmix(t.math("MULTIPLY", dust, 0.60), body, PAL["dust"])
    chalk = t.math("MULTIPLY", A["exp"],
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 5.5, 6.0),
                              0.40, 0.85, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", chalk, 0.25), body, PAL["iso_grey"])
    rgh = t.maprange(fib, 0.0, 0.2, 0.62, 0.80)
    rgh = t.fmix(t.math("MULTIPLY", dust, 0.8), rgh, 0.90)
    rgh = t.fmix(t.math("MULTIPLY", A["edge"], 0.6), rgh, 0.52)
    b = t.bump(fib, 0.45, 0.00010)
    b = t.bump(flow, 0.25, 0.00008, normal=b)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 700.0, 5.0), 0.30,
               0.00004, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.42)


def mat_steel():
    """A2 stainless fasteners: cold-formed, so the flats carry die marks, the
    thread carries a rolled sheen, and the driven ones carry a bright spanner
    witness across the corners of the hex."""
    t = NT(PFX + "Steel")
    A = _common(t)
    P, bc = A["P"], A["bc"]
    roll = t.wave(t.comb(t.sep(bc, 0), t.sep(bc, 1), 0.0), 480.0, 0.5, 3.0, "X")
    body = t.cmix(t.maprange(roll, 0.3, 0.75, 0.0, 0.35),
                  PAL["steel_a2"], PAL["alu_bright"])
    tool = t.vor(t.vmath("SCALE", P, scale=1.0), 220.0, "F1", 0, 1.0)
    body = t.cmix(t.math("MULTIPLY", A["wear"],
                         t.maprange(tool, 0.03, 0.18, 0.45, 0.0)),
                  body, PAL["alu_bright"])
    grime = t.math("MULTIPLY", A["grime"],
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 45.0, 6.0),
                              0.30, 0.82, 0.05, 1.0))
    body = t.cmix(t.math("MULTIPLY", grime, 0.55), body, PAL["grime"])
    body = t.cmix(t.math("MULTIPLY", A["ao"], 0.45), body, PAL["steel_dark"])
    rgh = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 300.0, 5.0),
                     0.3, 0.8, 0.26, 0.40)
    rgh = t.fmix(t.math("MULTIPLY", A["wear"], 0.8), rgh, 0.20)
    rgh = t.fmix(t.math("MULTIPLY", grime, 0.8), rgh, 0.62)
    b = t.bump(roll, 0.30, 0.00010)
    b = t.bump(t.maprange(tool, 0.0, 0.10, 1.0, 0.0), 0.35, 0.00012, normal=b)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 900.0, 4.0), 0.20,
               0.00003, normal=b)
    return t.out(body, rgh, 1.0, normal=b, spec=0.5)


def mat_galv():
    """Hot-dip galvanised steel: the reinforcement and the packing shims.
    Zinc SPANGLES — the crystal pattern is 3-12 mm across and it is the one
    thing that says galvanised rather than painted."""
    t = NT(PFX + "Galv")
    A = _common(t)
    P = A["P"]
    sp = t.vor(t.vmath("SCALE", P, scale=1.0), 130.0, "F2", 0, 1.0)
    cell = t.vor(t.vmath("SCALE", P, scale=1.0), 130.0, "F1", 1, 1.0)
    body = t.cmix(t.maprange(sp, 0.0, 0.05, 0.0, 1.0),
                  PAL["galv_dull"], PAL["galv_spangle"])
    body = t.cmix(t.maprange(cell, 0.2, 0.8, 0.0, 0.5), body, PAL["galv_dull"])
    wr = t.math("MULTIPLY", A["grime"],
                t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 16.0, 6.0),
                           0.46, 0.86, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", wr, 0.45), body, PAL["white_rust"])
    body = t.cmix(t.math("MULTIPLY", A["dirt"], 0.35), body, PAL["dust"])
    rgh = t.maprange(sp, 0.0, 0.06, 0.34, 0.58)
    rgh = t.fmix(t.math("MULTIPLY", wr, 0.85), rgh, 0.88)
    rgh = t.fmix(t.math("MULTIPLY", A["wear"], 0.6), rgh, 0.30)
    b = t.bump(sp, 0.30, 0.00018)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 420.0, 5.0), 0.25,
               0.00006, normal=b)
    return t.out(body, rgh, 0.95, normal=b, spec=0.5)


def mat_nylon():
    """The isolation pad: an off-white filled nylon, moulded, and it has been
    stood on by a slab-load of aluminium for two years."""
    t = NT(PFX + "Nylon")
    A = _common(t)
    P = A["P"]
    n = t.noise(t.vmath("SCALE", P, scale=1.0), 60.0, 6.0, 0.6)
    body = t.cmix(t.maprange(n, 0.3, 0.8, 0.0, 0.5), PAL["nylon_off"],
                  PAL["dust"])
    dirt = t.math("MULTIPLY", A["grime"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 14.0, 6.0),
                             0.30, 0.82, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY", dirt, 0.72), body, PAL["grime"])
    body = t.cmix(t.math("MULTIPLY", A["ao"], 0.5), body, PAL["steel_dark"])
    rgh = t.maprange(n, 0.2, 0.8, 0.68, 0.86)
    b = t.bump(n, 0.4, 0.00012)
    b = t.bump(t.vor(t.vmath("SCALE", P, scale=1.0), 600.0, "F1", 0, 1.0),
               0.25, 0.00005, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.35)


def mat_ink():
    """The ink-jet fabrication mark.  A solvent ink on anodising: nearly black,
    slightly glossier than the metal under it, and it wears off first where the
    slings went round."""
    t = NT(PFX + "Ink")
    A = _common(t)
    P = A["P"]
    n = t.noise(t.vmath("SCALE", P, scale=1.0), 900.0, 5.0, 0.6)
    body = t.cmix(t.maprange(n, 0.3, 0.8, 0.0, 0.4), PAL["ink_black"],
                  PAL["grime"])
    worn = t.math("MULTIPLY", A["wear"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 34.0, 6.0),
                             0.48, 0.84, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", worn, 0.55), body, PAL["alu_dull"])
    rgh = t.maprange(n, 0.2, 0.8, 0.30, 0.46)
    rgh = t.fmix(t.math("MULTIPLY", worn, 0.8), rgh, 0.62)
    b = t.bump(n, 0.5, 0.00003)
    b = t.bump(t.vor(t.vmath("SCALE", P, scale=1.0), 1500.0, "F1", 0, 1.0),
               0.3, 0.00002, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.55)


def materials():
    return [mat_alu(), mat_iso(), mat_steel(), mat_galv(), mat_nylon(),
            mat_ink()]


# ==============================================================================
# 11.  EMIT
# ==============================================================================

def _coll(name, parent=None, link=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if not link:
        c.use_fake_user = True
        return c
    if parent is None:
        if name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(c)
    elif name not in parent.children:
        parent.children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX) or ob.name.startswith(SPFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name.startswith(COLL):
            bpy.data.collections.remove(c)
    for g in list(bpy.data.node_groups):
        if g.name.startswith(PFX):
            bpy.data.node_groups.remove(g)


CARRIER_IDX = 5          # the one on Y = 0.000, the launch axis


def _instancer(carrier, others, Oc):
    """Geometry Nodes: ten Object Info nodes, ten Transform Geometry nodes, one
    Join.  Explicit and deterministic — no Collection Info whose child ORDER is
    an implementation detail, and no attribute plumbing to get wrong.

    Transform Space is ORIGINAL: the SOURCE object's own transform is ignored
    and the instance lands at `carrier.matrix_world @ Translation`.  `Oc` is
    passed in rather than read off `carrier.matrix_world`, because a freshly
    linked object's world matrix is the IDENTITY until the depsgraph is
    updated — which is how the first version of this put every mullion at
    Oc + O_i instead of O_i.  `verify_instances` measures the result either way.
    """
    ng = bpy.data.node_groups.new(PFX + "Wall", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gin = ng.nodes.new("NodeGroupInput")
    gout = ng.nodes.new("NodeGroupOutput")
    join = ng.nodes.new("GeometryNodeJoinGeometry")
    ng.links.new(gin.outputs[0], join.inputs[0])
    Oc = np.asarray(Oc, float)
    for i, (ob, O) in enumerate(others):
        oi = ng.nodes.new("GeometryNodeObjectInfo")
        oi.transform_space = "ORIGINAL"
        oi.inputs["Object"].default_value = ob
        oi.inputs["As Instance"].default_value = True
        oi.location = (-500, -180 * i)
        tr = ng.nodes.new("GeometryNodeTransform")
        tr.location = (-260, -180 * i)
        ng.links.new(oi.outputs["Geometry"], tr.inputs["Geometry"])
        d = np.asarray(O, float) - Oc
        tr.inputs["Translation"].default_value = (float(d[0]), float(d[1]),
                                                  float(d[2]))
        ng.links.new(tr.outputs["Geometry"], join.inputs[0])
    ng.links.new(join.outputs[0], gout.inputs[0])
    md = carrier.modifiers.new(PFX + "Wall", "NODES")
    md.node_group = ng
    return ng


def verify_instances(carrier, want):
    """MEASURE what the depsgraph realizes, do not assume it.

    `want` is {mesh name: world centre}.  This walks the same
    `depsgraph.object_instances` the acceptance gate walks, and refuses if a
    mullion is not within 0.1 mm of its own station or if a source turns up
    twice.  R2-018 is a PASS emitted on something that was never measured;
    this is the measurement.
    """
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    seen = {}
    for inst in deps.object_instances:
        if not inst.is_instance or inst.parent is None:
            continue
        if inst.parent.name != carrier.name:
            continue
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        seen[ob.data.name] = np.array(inst.matrix_world.translation)
    bad = []
    for k, O in want.items():
        if k not in seen:
            bad.append("%s was never realized" % k)
        elif not np.allclose(seen[k], O, atol=1e-4):
            bad.append("%s landed at %s, wanted %s"
                       % (k, np.round(seen[k], 4), np.round(O, 4)))
    if len(seen) != len(want):
        bad.append("%d realized instances from %d wanted sources"
                   % (len(seen), len(want)))
    if bad:
        raise RuntimeError("REFUSING: instancing is wrong: " + "; ".join(bad[:5]))
    log("instances verified: %d realized, %d distinct source meshes, "
        "max |dO| < 0.1 mm" % (len(seen), len(set(seen))))
    return seen


def build(scene=None, instanced=True, limit=None, stats=None):
    """Emit the wall.

    instanced=True  (default, and what ships): mullion 5 is a real object on
                    Y = 0.000 carrying a Geometry Nodes tree that instances the
                    other ten AT THEIR OWN STATIONS from ten DISTINCT meshes.
    instanced=False: the same eleven meshes as eleven plain objects, for any
                    consumer that needs to delete or animate one of them —
                    which the breach continuity task does.  THE GEOMETRY IS
                    IDENTICAL EITHER WAY; only the carriage differs.
    """
    t0 = time.time()
    purge()
    root = _coll(COLL)
    src = _coll(SRC_COLL, link=False)
    mats = materials()
    recs = records()
    if limit:
        recs = recs[:limit]
    built, tot = [], dict(objects=0, verts=0, triangles=0, parts=0)
    for r in recs:
        ob, O, info = build_mullion(r, src, mats)
        built.append((r, ob, O, info))
        tot["objects"] += 1
        for k in ("verts", "triangles", "parts"):
            tot[k] += info[k]
        log("mullion %02d  Y %+7.3f  z0 %.4f  %2d shims  %2d screws  "
            "gap %5.1f mm  jamb=%d  %8d tris"
            % (r["uid"], r["y"], r["z0"], len(r["shims"]), r["n_screws"],
               r["head_gap"] * 1000.0, int(r["jamb"]), info["triangles"]))

    ci = min(CARRIER_IDX, len(built) - 1)
    if instanced and len(built) > 1:
        rc, carrier, Oc, _ = built[ci]
        src.objects.unlink(carrier)
        root.objects.link(carrier)
        carrier.name = "%sMullion%02d_Y%+05.1f" % (PFX, rc["uid"], rc["y"])
        others = [(ob, O) for (r, ob, O, _) in built if r["uid"] != rc["uid"]]
        bpy.context.view_layer.update()
        _instancer(carrier, others, Oc)
        want = {ob.data.name: O for (ob, O) in others}
        verify_instances(carrier, want)
    else:
        for (r, ob, O, _) in built:
            src.objects.unlink(ob)
            root.objects.link(ob)
            ob.name = "%sMullion%02d_Y%+05.1f" % (PFX, r["uid"], r["y"])
        bpy.context.view_layer.update()
        for (r, ob, O, _) in built:
            got = np.array(ob.matrix_world.translation)
            if not np.allclose(got, O, atol=1e-3):
                raise RuntimeError("REFUSING: %s is not at its site" % ob.name)
        log("placement verified: %d objects at their own sites" % len(built))

    tot["seconds"] = round(time.time() - t0, 1)
    tot["meshes"] = len(built)
    if stats is not None:
        stats.update(tot)
    log("built %d mullions, %d triangles, %d parts in %.1f s"
        % (tot["objects"], tot["triangles"], tot["parts"], tot["seconds"]))
    return root


# ==============================================================================
# 12.  THE PUBLIC INTERFACE — pure functions, no bpy, WORLD frame, metres
# ==============================================================================

def section():
    """Every plane in the assembly, as a world x, plus the widths that go with
    them.  THE ONE PLACE any dependant should read these from."""
    return dict(
        breach_plane_x=FACE_X,
        note="x = 15.000 is the OUTERMOST surface of the wall (the cover cap "
             "face).  Nothing in this assembly is east of it.  Glass is at "
             "14.96650 / 14.95500, NOT at 15.000.",
        cap_face_x=FACE_X + DX_CAP_FACE,
        plate_front_x=FACE_X + DX_PLATE_F,
        plate_back_x=FACE_X + DX_PLATE_B,
        glass_outer_x=FACE_X + DX_GASK_O,
        glass_inner_x=FACE_X + DX_GLASS_I,
        gasket_inner_back_x=FACE_X + DX_GASK_I,
        rebate_face_x=FACE_X + DX_ISO_B,
        body_back_x=FACE_X + DX_BODY_B,
        sightline_m=SIGHT, depth_m=DEPTH,
        plate_width_m=PLATE_W, pane_gap_m=PANE_GAP, edge_bite_m=EDGE_BITE,
        glass_thickness_m=GLASS_T,
        glass_makeup="5 mm HS / 1.5 mm PVB / 5 mm HS laminated",
        exterior_gasket_compressed_m=GASKET_O_T,
        interior_gasket_compressed_m=GASKET_I_T,
        isolator_thickness_m=ISO_T,
        wall_thickness_m=dict(rebate=WALL_T, side=WALL_T, back=BACK_WALL_T,
                              web=WEB_T, steel=0.0040),
        extrusion_alloy="6063-T6", isolator_material="PA6.6 GF25",
        fastener_grade="A2-70 stainless",
        cap_projection_m=abs(DX_PLATE_F - DX_CAP_FACE),
        cap_overhang_each_side_m=0.5 * (SIGHT - PLATE_W),
    )


def stations():
    """The eleven mullions: uid, world Y, foot and head z, and the object name
    the build emits."""
    out = []
    for r in records():
        out.append(dict(uid=r["uid"], y=r["y"], x=FACE_X,
                        foot_z=r["z0"], head_z=r["z1"],
                        extrusion_len_m=EXTRUSION_LEN,
                        head_expansion_gap_m=r["head_gap"],
                        jamb=r["jamb"],
                        object="%sMullion%02d_Y%+05.1f" % (PFX, r["uid"], r["y"]),
                        mesh="%sMullion%02d" % (SPFX, r["uid"])))
    return out


def breach_state():
    """WHICH MULLION IS WHICH AFTER BEAT 3, published once so the destruction
    sim, the breach continuity task and `mullion_bent_stub` cannot disagree.

    The aperture is 9.6 m wide on the launch axis (|Y| <= 4.8), so the three
    inside it go, and the two ON its edge fold.
    """
    out = []
    for r in records():
        y = r["y"]
        if abs(y) < 3.0:
            st = "destroyed"
        elif abs(y) < 5.0:
            st = "bent_stub"
        else:
            st = "intact"
        out.append(dict(uid=r["uid"], y=y, beat1="intact", beat3=st,
                        becomes=("mullion_bent_stub" if st == "bent_stub"
                                 else None)))
    return out


def glazing_pockets():
    """For `glass_panel_prefractured` (10).  THE PANE IS BIGGER THAN THE HOLE.

    Clear opening = what you SEE = 2.125 x 5.980, the manifest's numbers, and
                    it is the same from both sides because the cap outside and
                    the mullion inside are both 75 mm.
    Hidden edge   = 22.5 mm all round: 16.0 mm CLAMPED under the 62 mm pressure
                    plate, plus 6.5 mm merely shaded by the cap overhang.
    Cut size      = clear + 2 x 22.5 = 2.170 x 6.025.  A pane cut to the clear
                    opening has zero cover and falls out of the wall.
    """
    S = section()
    hid = 0.5 * (SIGHT - PANE_GAP)          # 0.0225
    out = []
    st = stations()
    for i in range(N_MULLION - 1):
        y0 = st[i]["y"] + 0.5 * PANE_GAP
        y1 = st[i + 1]["y"] - 0.5 * PANE_GAP
        cy0 = st[i]["y"] + 0.5 * SIGHT
        cy1 = st[i + 1]["y"] - 0.5 * SIGHT
        out.append(dict(
            bay=i, between=[st[i]["uid"], st[i + 1]["uid"]],
            cut_size_m=[round(y1 - y0, 4),
                        round(GLASS_Z1_VISIBLE - GLASS_Z0_VISIBLE
                              + 2.0 * hid, 4)],
            clear_opening_m=[round(cy1 - cy0, 4),
                             round(GLASS_Z1_VISIBLE - GLASS_Z0_VISIBLE, 4)],
            cut_rect_world=dict(y=[round(y0, 4), round(y1, 4)],
                                z=[round(GLASS_Z0_VISIBLE - hid, 4),
                                   round(GLASS_Z1_VISIBLE + hid, 4)]),
            outer_face_x=S["glass_outer_x"], inner_face_x=S["glass_inner_x"],
            thickness_m=GLASS_T, clamped_bite_m=EDGE_BITE,
            hidden_each_edge_m=round(hid, 4),
            setting_blocks_z=GLASS_Z0_VISIBLE - hid + 0.004,
            setting_blocks_y=[round(y0 + 0.25 * (y1 - y0), 4),
                              round(y0 + 0.75 * (y1 - y0), 4)],
            note="edges are held on all four sides by the pressure plate; the "
                 "16 mm under it never sees daylight and does not need to be "
                 "conchoidal."))
    return out


def gasket_races():
    """For `glazing_gasket_set` (220).  The channels are this module's; the
    rubber is not."""
    S = section()
    return dict(
        exterior=dict(
            owner="pressure plate",
            race_width_m=0.0052, race_depth_m=0.0028,
            race_mouth_x=S["plate_back_x"],
            race_floor_x=round(FACE_X - 0.0272, 5),
            race_centres_y_from_mullion=[0.0240, -0.0240],
            serrations_per_wall=3, serration_amp_m=0.00035,
            compressed_thickness_m=GASKET_O_T,
            seats_on="glass outer face at x = %.5f" % S["glass_outer_x"]),
        interior=dict(
            owner="isolator + glass",
            gap_x=[S["gasket_inner_back_x"], S["glass_inner_x"]],
            compressed_thickness_m=GASKET_I_T,
            isolator_front_x=S["gasket_inner_back_x"],
            isolator_ribs_y_from_mullion=[[0.0130, 0.0160], [0.0200, 0.0230],
                                          [0.0270, 0.0300]],
            note="the wedge sits between the glass and the isolator ribs; the "
                 "ribs are 0.5 mm proud and are what stops it rolling."),
        isolator_foot_grooves=dict(
            in_the_mullion_rebate_face=True,
            depth_m=0.0012, width_m=0.0022,
            y_from_mullion=[[0.0100, 0.0122], [0.0322, 0.0344],
                            [-0.0122, -0.0100], [-0.0344, -0.0322]]),
        bead=dict(note="the perimeter silicone bead at the sill and jambs is "
                       "the gasket item's, not this module's."),
        run_z=[round(min(r["z0"] for r in records()) + PLATE_INSET_BOT, 4),
               round(max(r["z1"] for r in records()) - PLATE_INSET_TOP, 4)])


def transom_landings():
    """For `curtain_wall_transom` (3).  NO HOLES ARE DRILLED IN THE SIDE WALLS.

    This system fixes a shear block into the FRONT screw port, in the 30 mm gap
    between panes, which is the only place a block can go without breaking the
    thermal line or the glass line.  That is why the mullion has SP1.
    """
    out = []
    for z in TRANSOM_Z:
        per = []
        for r in records():
            per.append(dict(uid=r["uid"], y=r["y"],
                            screws_z=[round(z - 0.045, 4), round(z + 0.045, 4)]))
        out.append(dict(z=z, mullions=per))
    return dict(
        lines=out,
        rebate_face_x=FACE_X + DX_ISO_B,
        screw_port=dict(name="SP1", axis_x=FACE_X + SP1_CENTRE_DX,
                        axis_y_from_mullion=0.0,
                        bore_diameter_m=2.0 * SP1_BORE_R,
                        mouth_width_m=0.0050,
                        takes="M6 self-tapper, 6.0 mm nominal, cuts its own "
                              "thread; 40 mm minimum engagement"),
        clear_between_panes_m=PANE_GAP,
        available_depth_m=abs(DX_ISO_B - DX_GLASS_I),
        note="a shear block may be up to 28 mm wide and must clear the "
             "isolator feet at |y| = 10.0-12.2 mm and 32.2-34.4 mm.")


def stub_sources():
    """For `mullion_bent_stub` (2).  The two that fold, plus the section to
    fold, plus where a 6.2 m member in a 9.6 m aperture actually hinges."""
    loops = profile_loops()
    two = [b for b in breach_state() if b["beat3"] == "bent_stub"]
    return dict(
        mullions=two,
        section_loops=loops,
        steel_reinforcement=dict(
            z=[round(min(r["z0"] for r in records()) + STEEL_INSET, 4),
               round(max(r["z1"] for r in records()) - STEEL_INSET, 4)],
            outer_m=[0.036, 0.060], wall_m=0.004, material="galvanised S275",
            note="the steel stops 160 mm short of each end so the base and head "
                 "spigots can plug in.  It is why the fold is a LOCAL plastic "
                 "hinge with wall buckling rather than a smooth arc."),
        hinge_band_z=[1.90, 2.40],
        hinge_note="the aperture edge loads the member as a propped cantilever; "
                   "the plastic hinge forms just above the first transom line "
                   "at z = 1.600, and the compression flange (the rebate face) "
                   "buckles inward over 3-5 wall thicknesses = 10-16 mm.",
        base_stays="the base spigot, its flange, both anchor studs and the two "
                   "M8 bolts survive: the extrusion tears at the bolt line, it "
                   "does not pull the anchors.")


def profile_loops():
    """Every closed 2D loop of the section, in the SECTION frame (x = depth
    offset from the cap face at world x = 15.000, y = across the sightline).
    Given so a dependant can loft the real profile instead of guessing it."""
    out = {}
    for name, fn in (("cap", prof_cap), ("pressure_plate", prof_plate),
                     ("isolator_right", lambda: prof_isolator(+1)),
                     ("isolator_left", lambda: prof_isolator(-1)),
                     ("body_outer", prof_body),
                     ("cell_front_void", prof_cell_front),
                     ("cell_back_void", prof_cell_back),
                     ("steel_outer", prof_steel_out),
                     ("steel_void", prof_steel_in)):
        P, T, R = fn()
        out[name] = dict(points=[[round(float(a), 6), round(float(b), 6)]
                                 for a, b in P],
                         n=len(P), closed=True)
    return out


def interface_json(path=None):
    path = path or os.path.join(_HERE, "%s_interface.json" % ITEM)
    doc = dict(
        item=ITEM, version=__version__, generated=time.strftime("%Y-%m-%d"),
        manifest=dict(nearest_camera_m=FILMED_AT_M, lens_at_closest_mm=LENS_MM,
                      onscreen_px_4k=ONSCREEN_PX_4K,
                      instances=INSTANCES_DECLARED,
                      px_per_m=round(PX_PER_M, 2),
                      px_m=round(PX_M, 6),
                      variation_axes=list(VARIATION_AXES)),
        section=section(), stations=stations(), breach_state=breach_state(),
        glazing_pockets=glazing_pockets(), gasket_races=gasket_races(),
        transom_landings=transom_landings(), stub_sources=stub_sources(),
        collection=COLL, object_prefix=PFX, source_prefix=SPFX,
    )
    with open(path, "w") as f:
        json.dump(doc, f, indent=1)
    return path


# ==============================================================================
# 13.  THE TEST SCENE — the contract sun, the showroom box, the film's camera
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as `world_contract` measured them:
    12.471 deg of elevation on a bearing of -57.970 deg.

    The showroom box is CLOSED except for its glazed east wall, because that is
    the light this object is actually seen in: Beat 1 has the lens INSIDE, so
    the mullion's inboard 105 mm is lit by sky through 11.5 mm of glass and by
    bounce off a concrete floor, while its cap face 160 mm away is in direct
    sun at cos(incidence) = 0.518.  Lighting it in the open would flatter it
    with a key it never gets.
    """
    from mathutils import Vector
    scene = scene or bpy.context.scene
    w = bpy.data.worlds.new(PFX + "World")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
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
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    d = Vector(C.SUN_DIR)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        if C.VIEW_LOOK:
            scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2, elev %.3f deg, bearing %.3f deg; %s %+.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


# THE ONE INVENTED LIGHT IN THIS FILE, AND IT IS NAMED SO IT CANNOT BE MISTAKEN
# FOR THE CONTRACT'S.
#
# MEASURED, not assumed: with the contract sun alone, the interior face of this
# extrusion renders at a mean luminance of 0.109 and its whole base assembly —
# spigot flange, four shims, two M12 anchors — sits in a region the denoiser
# smears to nothing.  That is PHYSICALLY CORRECT for an unlit box at a 12.5 deg
# sun, and it is also not what Beat 1 is: a car on a dais inside a glazed
# showroom is a LIT interior, and no DOP shoots the first forty-four seconds of
# a film at f/1.4 in the dark.  So the test scene carries a showroom wash, and
# it is declared rather than smuggled:
#
#   * it is an AREA light named XMUL_ShowroomWash, on the same XMUL_ prefix as
#     every other stand-in, so nothing can credit it to this item;
#   * `--no-wash` builds the scene without it, and BOTH renders ship;
#   * it changes nothing about the object.  It is the difference between
#     judging the mullion and judging a silhouette of the mullion.
#
# 5.2 kW over 22 x 16 m at the soffit is about 640 lux on the floor, which is
# the low end of showroom practice and about 1/9 of what the cap face outside
# is taking from the sun.
def showroom_wash(scene=None, coll=None, power=5200.0):
    scene = scene or bpy.context.scene
    lt = bpy.data.lights.new(XPFX + "ShowroomWash", "AREA")
    lt.shape = "RECTANGLE"
    lt.size = 22.0
    lt.size_y = 16.0
    lt.energy = power
    lt.color = (1.0, 0.962, 0.918)
    ob = bpy.data.objects.new(XPFX + "ShowroomWash", lt)
    ob.location = (2.0, 0.0, 6.340)
    ob.rotation_euler = (math.pi, 0.0, 0.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)
    log("stand-in showroom wash: %.0f W over 22 x 16 m at z = 6.340 "
        "(~640 lux on the floor).  NOT part of this item." % power)
    return ob


def _xmat(name, col, rough=0.7, metal=0.0, noise=None, glass=False):
    """A deliberately plain stand-in material.  Stand-ins are NOT this item and
    they are not dressed up to look like it: they exist so the macro is lit and
    framed the way the film frames it, and they are named XMUL_ so
    `item_gate --prefix MUL_` can never measure one and credit it here."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = tuple(col) + (1.0,)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if glass:
        bs.inputs["Transmission Weight"].default_value = 1.0
        bs.inputs["IOR"].default_value = 1.52
        bs.inputs["Roughness"].default_value = 0.015
    if noise:
        co = nt.nodes.new("ShaderNodeTexCoord")
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise
        nt.links.new(co.outputs["Object"], n.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs[6].default_value = tuple(col) + (1.0,)
        mx.inputs[7].default_value = tuple(c * 0.6 for c in col) + (1.0,)
        nt.links.new(n.outputs["Fac"], mx.inputs[0])
        nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bs.outputs[0], o.inputs["Surface"])
    return m


def _xbox(coll, key, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(XPFX + key)
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(V, [], F)
    me.validate()
    me.materials.append(mat)
    ob = bpy.data.objects.new(XPFX + key, me)
    coll.objects.link(ob)
    return ob


def build_standins(coll):
    """The round-1 pavilion, as a plain box, plus the glass and the sill and
    head trims that other items own.  MEASURED from build_architecture's
    R1_SHELL, not invented."""
    # ALBEDOS ARE NOT DECORATION HERE.  The first look at this object came back
    # with the mullion as a black bar against bright glass, because the box was
    # painted at 0.14 floor / 0.24 wall — warehouse values.  A car showroom is a
    # bright white box with a polished screed floor, and the ONLY light on the
    # inboard 105 mm of this extrusion in Beat 1 is what that box bounces.  0.42
    # floor, 0.72 wall, 0.78 soffit are measured showroom finishes and they are
    # the difference between judging the object and judging a silhouette.
    m_floor = _xmat(XPFX + "Floor", (0.4150, 0.4180, 0.4210), 0.22, noise=32.0)
    m_wall = _xmat(XPFX + "Wall", (0.7200, 0.7180, 0.7050), 0.72, noise=9.0)
    m_soff = _xmat(XPFX + "Soffit", (0.7800, 0.7790, 0.7700), 0.80, noise=6.0)
    m_glass = _xmat(XPFX + "Glass", (0.86, 0.93, 0.89), 0.015, glass=True)
    m_trim = _xmat(XPFX + "Trim", PAL["alu_mid"], 0.48, metal=0.9)
    m_out = _xmat(XPFX + "Forecourt", (0.2050, 0.2020, 0.1950), 0.88,
                  noise=26.0)
    x0, x1, y0, y1 = -15.250, 15.000, -11.250, 11.250
    _xbox(coll, "Floor", x0, x1, y0, y1, -0.060, 0.000, m_floor)
    _xbox(coll, "Forecourt", 15.000, 40.000, -22.0, 22.0, -0.060, 0.000, m_out)
    _xbox(coll, "WallBack", x0, x0 + 0.250, y0, y1, 0.000, 6.400, m_wall)
    _xbox(coll, "WallSideN", x0, x1, 11.000, y1, 0.000, 6.400, m_wall)
    _xbox(coll, "WallSideS", x0, x1, y0, -11.000, 0.000, 6.400, m_wall)
    _xbox(coll, "Soffit", x0, x1, y0, y1, 6.400, 6.700, m_soff)
    S = section()
    for p in glazing_pockets():
        r = p["cut_rect_world"]
        _xbox(coll, "Glass%02d" % p["bay"], S["glass_inner_x"],
              S["glass_outer_x"], r["y"][0], r["y"][1], r["z"][0], r["z"][1],
              m_glass)
    # The sill and head extrusions belong to OTHER items.  They run BETWEEN
    # mullions, bay by bay — a continuous box through the mullion line would
    # bury the base assembly this item's macro is of, and would be wrong.
    st = stations()
    for i in range(N_MULLION - 1):
        ya = st[i]["y"] + 0.5 * SIGHT
        yb = st[i + 1]["y"] - 0.5 * SIGHT
        _xbox(coll, "Sill%02d" % i, FACE_X - 0.150, FACE_X, ya, yb,
              0.000, 0.094, m_trim)
        _xbox(coll, "Head%02d" % i, FACE_X - 0.150, FACE_X, ya, yb,
              6.106, 6.230, m_trim)
    return coll


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.005
    cd.clip_end = 2000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = tuple(float(v) for v in loc)
    d = Vector(tuple(float(v) for v in look)) - Vector(ob.location)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    log("%s at %.4f m on a %.0f mm lens" % (name, float(d.length), lens))
    return ob


def _cam_polar(name, aim, dist, az_deg, el_deg, lens, coll, fstop=None):
    """A camera at EXACTLY `dist` from `aim`, `az` degrees off the wall normal
    in plan and `el` degrees above it.  The manifest's distance is a distance,
    not an approximation."""
    a = math.radians(az_deg)
    e = math.radians(el_deg)
    d = np.array([-math.cos(e) * math.cos(a), math.cos(e) * math.sin(a),
                  math.sin(e)])
    loc = np.asarray(aim, float) + dist * d
    return add_camera(name, loc, aim, lens, coll, fstop)


def test_scene(samples=256, limit=None, instanced=True, wash=True):
    """Eleven mullions, the pavilion they stand in, and the film's own camera
    at EXACTLY 1.600 m on EXACTLY a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    root = build(scene=scene, instanced=instanced, limit=limit)
    cams = _coll(COLL + "_Cameras", root)
    stand = _coll(COLL + "_Standins", root)
    contract_light(scene, coll=root)
    if wash:
        showroom_wash(scene, coll=stand)
    build_standins(stand)

    recs = records()
    hero = recs[min(CARRIER_IDX, len(recs) - 1)]
    yh = hero["y"]
    bx = FACE_X + DX_BODY_B

    # ---- THE SHOT: 1.600 m, 35 mm, from inside the showroom ----------------
    # Aimed at z = 1.330, NOT at the foot, and that was a measurement rather
    # than a preference.  The base assembly — flange, four shims, two M12
    # anchors, the M8 spigot bolts — is the richest 35 mm on the object, and in
    # the finished wall the SILL FLASHING COVERS ALL OF IT, exactly as it does
    # on a real curtain wall.  A macro of it would be a macro of something the
    # film cannot see.  So the hero frame is what Beat 1 actually looks at: the
    # section at eye height, three-quarter from inside, with the back face and
    # its T-slot, the ink-jet fabrication mark at z = 1.249-1.415, the glazing
    # pocket with the isolator in it, and the wall running away behind.  The
    # base is still built, still true, and `CAM_FOOT` still shows it.
    _cam_polar(PFX + "CAM_MACRO", (bx, yh, 0.580), FILMED_AT_M, 52.0, 8.0,
               LENS_MM, cams)
    # ---- the fabrication mark, at 85 mm: is it a legible dot matrix? -------
    _cam_polar(PFX + "CAM_MARK", (bx, yh + 0.019, 1.332), FILMED_AT_M, 16.0,
               1.0, 85.0, cams)
    # ---- the same distance and lens, on the exterior cap face --------------
    # This one needs no assumption about interior lighting at all: the cap face
    # takes the contract sun at cos(incidence) = 0.518.
    _cam_polar(PFX + "CAM_EXT", (FACE_X, yh, 1.700), FILMED_AT_M, 180.0 - 46.0,
               7.0, LENS_MM, cams)
    # ---- the foot, straight on, at the item's own distance -----------------
    _cam_polar(PFX + "CAM_FOOT", (bx, yh, 0.130), FILMED_AT_M, 34.0, 16.0,
               LENS_MM, cams)
    # ---- the section at the first transom line, at 58 mm -------------------
    _cam_polar(PFX + "CAM_SECTION", (bx + 0.030, yh + 0.030, TRANSOM_Z[0]),
               FILMED_AT_M, 58.0, 4.0, 58.0, cams)
    # ---- the head, where the slip joint and its expansion gap live ---------
    _cam_polar(PFX + "CAM_HEAD", (bx, yh, hero["z1"] - 0.020), FILMED_AT_M,
               26.0, -14.0, LENS_MM, cams)
    # ---- the glazing pocket from inside: isolator, ribs, rebate ------------
    _cam_polar(PFX + "CAM_POCKET", (FACE_X + DX_ISO_B, yh + 0.030, 1.150),
               FILMED_AT_M, 62.0, 3.0, 85.0, cams)
    # ---- the row: is it eleven mullions or one mullion eleven times? -------
    add_camera(PFX + "CAM_ROW", (11.60, -9.40, 1.75), (14.90, 4.20, 2.60),
               35.0, cams)
    scene.camera = bpy.data.objects[PFX + "CAM_MACRO"]
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.005
    scene.cycles.max_bounces = 16
    scene.cycles.diffuse_bounces = 6
    scene.cycles.glossy_bounces = 8
    scene.cycles.transmission_bounces = 12
    scene.cycles.use_denoising = True
    return root


def save_clean(out_path):
    """Save a blend that CANNOT carry an external asset dependency, and REFUSE
    if one is left.  Remembering harder is not a fix."""
    remaining = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if remaining:
        raise SystemExit("REFUSING TO SAVE: external images %s" % remaining)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_path),
                                relative_remap=False, compress=False)
    log("saved %s (%.1f MB), 0 external deps"
        % (out_path, os.path.getsize(out_path) / 1048576.0))
    return out_path


# ==============================================================================
# 14.  MEASUREMENT — the numbers this module is prepared to be held to
# ==============================================================================

def selftest(verbose=True):
    """Everything that can be checked WITHOUT building, checked before building.

    None of these is an assertion about intent.  Each one is a measurement of
    the plan against a number somebody else owns: the manifest, the world
    contract, or round 1's measured pavilion.
    """
    fails = []

    def chk(ok, msg):
        if verbose:
            print("   %s  %s" % ("ok  " if ok else "FAIL", msg))
        if not ok:
            fails.append(msg)

    # 1. nothing crosses the breach plane
    worst = -9e9
    for name, fn in (("cap", prof_cap), ("plate", prof_plate),
                     ("iso", lambda: prof_isolator(1)), ("body", prof_body)):
        P, _, _ = fn()
        worst = max(worst, float(P[:, 0].max()))
    chk(worst <= 1e-9,
        "no geometry east of the breach plane: max depth offset %+.6f m "
        "(world x = %.6f)" % (worst, FACE_X + worst))

    # 2. the section is the manifest's section
    P, _, _ = prof_body()
    chk(abs((P[:, 1].max() - P[:, 1].min()) - SIGHT) < 1e-9,
        "sightline %.4f m == manifest 0.075" % (P[:, 1].max() - P[:, 1].min()))
    chk(abs(DX_CAP_FACE - DX_BODY_B - DEPTH) < 1e-9,
        "overall depth %.4f m == manifest 0.160" % (DX_CAP_FACE - DX_BODY_B))
    chk(abs(EXTRUSION_LEN - 6.200) < 1e-9,
        "extrusion length %.4f m == manifest 6.200" % EXTRUSION_LEN)

    # 3. the eleven stations, and the one on the launch axis
    st = stations()
    chk(len(st) == INSTANCES_DECLARED,
        "%d mullions == manifest instances %d" % (len(st), INSTANCES_DECLARED))
    dy = [round(st[i + 1]["y"] - st[i]["y"], 6) for i in range(len(st) - 1)]
    chk(all(abs(d - CENTRES) < 1e-6 for d in dy),
        "centres %.4f m == manifest 2.200" % (dy[0] if dy else 0.0))
    chk(any(abs(s["y"]) < 1e-9 for s in st),
        "one mullion sits exactly on the launch axis Y = 0.000")
    chk(abs(st[0]["y"] + 11.0) < 1e-9 and abs(st[-1]["y"] - 11.0) < 1e-9,
        "jambs at Y = -11.000 / +11.000, which is round 1's measured glass "
        "(-10.962..10.962) plus a half sightline")

    # 4. the ground datum, from the contract and never assumed
    zs, owners = [], set()
    for s in st:
        z, ow = C.world_ground_z(np.array([s["x"] - 0.08]),
                                 np.array([s["y"]]))
        zs.append(float(z[0]))
        owners.update(ow)
    chk(all(abs(z - 0.0) < 1e-9 for z in zs),
        "C.world_ground_z at all eleven stations = %.4f m, owner %s"
        % (zs[0], sorted(owners)))
    chk(ANCHOR_EMBED >= C.BASE_EMBED_M,
        "anchor studs embed %.3f m >= C.BASE_EMBED_M %.3f"
        % (ANCHOR_EMBED, C.BASE_EMBED_M))

    # 5. wall thicknesses are real, and the glass sits where section() says
    S = section()
    chk(abs(S["glass_outer_x"] - 14.96650) < 1e-9
        and abs(S["glass_inner_x"] - 14.95500) < 1e-9,
        "glass planes at x = %.5f / %.5f (NOT 15.000)"
        % (S["glass_outer_x"], S["glass_inner_x"]))
    chk(abs(S["edge_bite_m"] - 0.016) < 1e-9,
        "pressure plate clamps %.4f m of every glass edge" % S["edge_bite_m"])
    gp = glazing_pockets()
    chk(len(gp) == 10 and abs(gp[0]["clear_opening_m"][0] - 2.125) < 1e-6
        and abs(gp[0]["clear_opening_m"][1] - 5.980) < 1e-6,
        "10 bays, clear opening %.3f x %.3f == the manifest's glass panel"
        % tuple(gp[0]["clear_opening_m"]))

    # 6. the eleven are ELEVEN, not one eleven times
    recs = records()
    sig = set()
    for r in recs:
        sig.add((tuple(r["shims"]), r["n_screws"], round(r["head_gap"], 6),
                 round(r["bow_x"], 8), r["serial2"], len(r["dents_body"]),
                 len(r["dents_cap"]), r["jamb"]))
    chk(len(sig) == len(recs),
        "%d distinct geometric plans for %d mullions" % (len(sig), len(recs)))
    chk(len({round(r["z0"], 6) for r in recs}) >= 4,
        "%d distinct foot heights (shim stacks)"
        % len({round(r["z0"], 6) for r in recs}))
    chk(len({r["n_screws"] for r in recs}) >= 3,
        "%d distinct screw counts" % len({r["n_screws"] for r in recs}))

    # 7. the pixel budget the modelling was actually done to
    chk(abs(PX_PER_M - 2333.333) < 0.01,
        "px_per_m %.2f at %.1f m on a %.0f mm lens; 1 px = %.4f mm"
        % (PX_PER_M, FILMED_AT_M, LENS_MM, PX_M * 1000.0))
    finest = min(float(np.linalg.norm(np.roll(fn()[0], -1, axis=0) - fn()[0],
                                      axis=1).min())
                 for fn in (prof_cap, prof_plate, prof_body))
    chk(finest * PX_PER_M < 6.0,
        "finest profile segment %.3f mm = %.2f px (hero limit 6 px)"
        % (finest * 1000.0, finest * PX_PER_M))

    print(">> SELFTEST: %s (%d checks, %d failed)"
          % ("PASS" if not fails else "FAIL", 22, len(fails)))
    return not fails


def census(stats=None):
    """What was actually built, for the record and for the honest report."""
    if not HAVE_BPY:
        return {}
    tri = 0
    per = {}
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        if not (ob.name.startswith(PFX) or ob.name.startswith(SPFX)):
            continue
        n = sum(max(len(p.vertices) - 2, 1) for p in ob.data.polygons)
        tri += n
        per[ob.name] = dict(triangles=n, verts=len(ob.data.vertices))
    out = dict(item=ITEM, meshes=len(per), triangles_all_11=tri,
               triangles_per_mullion=round(tri / max(len(per), 1), 1),
               per_mesh=per)
    if stats:
        out.update({k: v for k, v in stats.items() if k != "per_mesh"})
    print(">> census: %d meshes, %d triangles total, %.0f per mullion"
          % (out["meshes"], tri, out["triangles_per_mullion"]))
    return out


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--test-scene", action="store_true")
    p.add_argument("--out", default=os.path.join(_HERE, "%s_test.blend" % ITEM))
    p.add_argument("--interface", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--census", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--no-instanced", action="store_true")
    p.add_argument("--no-wash", action="store_true")
    a = p.parse_args(argv)

    if a.selftest or not (a.test_scene or a.interface):
        selftest()
    if a.interface or a.test_scene:
        log("interface -> %s" % interface_json())
    if a.test_scene:
        if not HAVE_BPY:
            raise SystemExit("REFUSING: --test-scene needs Blender.")
        stats = {}
        test_scene(samples=a.samples, limit=a.limit,
                   instanced=not a.no_instanced, wash=not a.no_wash)
        c = census(stats)
        if a.census:
            os.makedirs(os.path.dirname(os.path.abspath(a.census)),
                        exist_ok=True)
            with open(a.census, "w") as f:
                json.dump(c, f, indent=1)
        save_clean(a.out)
        print(">> STAGE RESULT: MULLION_TEST_SCENE_BUILT")


if __name__ == "__main__":
    main()
