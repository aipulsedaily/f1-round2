#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tyre_blanket.py — CIRCUIT VITRINE, per-item hero campaign, item ``tyre_blanket``
(zone ``pit_lane``, wave 1, build order 136, **5 dependants, 0 dependencies**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Fifty-six electrically heated tyre blankets on fifty-six mounted F1 wheels,
built as what a blanket physically IS — a quilted, insulated, silicone-glass
sheet that is *larger than the thing it wraps*, so it bulges between its straps,
pleats where its elastic hem gathers, gapes along its hook-and-loop closure, and
hangs off the tyre entirely wherever a mechanic has pulled it back — and never
as a smooth cylinder with a fabric shader on it.

    manifest, verbatim:  "User-named class.  A blanket that is a smooth cylinder
                          is wrong - it must bulge over the tyre and gape at the
                          seam."

THE TWO SENTENCES THAT DECIDED THE WHOLE MODEL
----------------------------------------------
A blanket is not a surface offset.  It is a *sheet of finite area* forced onto a
torus whose developable area is smaller, and every visible feature is that
mismatch resolving itself:

  * the fabric is **longer around** than the tyre, so it buckles between the
    straps — that is the bulge;
  * the fabric is **wider across** than the sidewall it has to cover, and the
    excess is gathered by an elastic hem — that is the radial pleat fan, which
    is the single most recognisable thing about a real blanket and which no
    offset surface can produce;
  * the closure **overlaps**, so there are two thicknesses of quilted cloth over
    90 mm of arc, a 14 mm step, a shadow line down the whole section, and a
    triangular gape at the free edge where the hook tape has not caught.

Everything else — quilt channels, scorch, cable, buckles, handles — is dressing
on top of those three facts.

AND IT IS A DRUM, NOT A SHRINK-WRAP.  The section is a cylindrical tread band
with a hard bound corner at each shoulder and two flat-ish annular side panels
that **bridge** the tyre's shoulder radius rather than following it — a 6–11 mm
air gap under the corner.  That bridge is what gives the object its square
silhouette and its single crisp horizontal welt.  The first build offset the
tyre's own section by 2 mm the whole way round and produced a smooth torus,
which is the manifest's forbidden "smooth cylinder" wearing a different hat.

===============================================================================
THE PIXEL BUDGET THIS WAS BUILT TO
===============================================================================
    manifest:  nearest_camera_m 13.0,  lens_at_closest_mm 35,  onscreen_px_4k 195
    px_per_m = (3840 x 35 / 36) / 13.0 = 287.2 px/m      ->    1 px = 3.482 mm

BUT THAT IS NOT THE TIGHTEST LENS THIS OBJECT IS JUDGED BY, and building to it
would have been the mistake.  ``tyre_blanket_controller`` — which is MY cable
gland, MY cable, and the box on the end of it — is filmed at the same 13.0 m on
a **58 mm** lens:

    px_per_m = (3840 x 58 / 36) / 13.0 = 475.9 px/m      ->    1 px = 2.101 mm

and ``crew_tyre_carrier_on/off`` carry one of these at 10.0 m on 35 mm
(373.3 px/m).  So the governing number is **2.101 mm per pixel**, and the line
this module draws is:

    ANYTHING WITH >= 1.0 mm OF RELIEF OR SILHOUETTE IS MESH.  Below that, and
    only below that, it is shading.

What that buys, measured against 2.101 mm/px:

    the blanketed wheel, 0.755 m OD               359 px (58 mm) / 217 px (35 mm)
    the hem opening, 0.474 m across               226 px      <- the wheel shows
    a quilt channel, 74-96 mm pitch                35-46 px   <- MESH
    a quilt stitch valley, 5 mm deep, 9 mm wide     4 x 2 px  <- MESH
    the closure overlap step, 14 mm                 6.7 px    <- MESH
    the gape at the free edge, 6-34 mm              3-16 px   <- MESH
    a radial hem pleat, 4-11 mm amplitude           2-5 px    <- MESH
    the bound seam welt at the shoulder, 3.2 mm     1.5 px    <- MESH
    38 mm webbing strap                            18 px      <- MESH
    a side-release buckle, 46 x 26 x 12 mm         22 x 12 px <- MESH
    the buckle's 2.5 mm rib pitch                   1.2 px    <- MESH
    the cable gland, 26 mm dia, 5 relief ribs      12 px, ribs 2 px <- MESH
    8.5 mm cable                                    4 px      <- MESH
    a carry-handle bar tack, 38 x 25 mm            18 x 12 px <- MESH
    a stitched brand patch, 1.6 mm proud            0.8 px    <- MESH (silhouette)
    a burn-through to the batting, 25-60 mm        12-29 px   <- MESH
    the char lip round it, 2 mm                     1 px      <- MESH
    a sewing stitch, 0.4 mm thread, 3 mm pitch      0.2 px    <- SHADING
    the 0.34 mm silicone-glass weave                0.16 px   <- SHADING
    screen-printed brand ink, 0.2 mm proud          0.1 px    <- SHADING (SDF)
    tyre sidewall lettering, 0.9 mm proud           0.43 px   <- MESH anyway,
                                                       because it is the only
                                                       thing on the sidewall
                                                       and it reads by gloss

WHY THE PRINT IS AN SDF AND NOT A PAINTED VERTEX COLOUR.  Brand artwork on the
side panel is 40-70 mm of cap height on a mesh whose cells are 2-6 mm.  A
per-vertex *colour* would be mush at that ratio.  A per-vertex signed *distance*
interpolates linearly and can be thresholded in the shader, which is how signed
distance fields render type at any magnification — so ``tb_print`` is baked in
metres and the shader takes a 0.4 mm smoothstep across zero.  The letterforms
stay razor-edged at 58 mm and would stay razor-edged at 200 mm.

===============================================================================
THE LIGHT DECIDES WHICH RELIEF IS WORTH HAVING
===============================================================================
``world_contract``: SUN_DIR (0.5179, -0.8278, 0.2159), elevation 12.47 deg,
bearing -57.97 deg.  These blankets stand in the pit lane, whose garage front
faces circuit +y = world bearing 130 deg, so the sun rakes ALONG the row at
about 8 deg of incidence to the garage face and 12.5 deg above the deck.

    * A 5 mm quilt valley throws 5 x 4.52 = 22.6 mm of shadow = 11 px.  The
      quilt is therefore the loudest signal on the object and it is worth every
      row of mesh it costs.
    * Vertical relief on a blanket standing upright — the closure step, the
      free edge — is nearly edge-on to the sun.  It reads by its own occlusion
      and by the dark cavity behind it, not by a cast shadow, which is why the
      gape is modelled as a real opening with a real inner surface and a real
      fabric thickness rather than as a crease.
    * At 12.47 deg the TOP of a standing blanket takes sin(12.47) = 0.216 of
      normal irradiance while its sunward flank takes 0.95.  A 4.4x tonal split
      across one object; the quilt pillows straddle it and that is the read.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Nothing below needs bpy.  Everything is a pure function of the deterministic
plan, returns world-frame numbers, and is dumped in full by
``interface_json(path)`` to ``world/items/tyre_blanket_interface.json``.

  tyre_blanket_controller   ``cable_exit(uid)`` -> the gland's world position,
     (56, 13 m, 58 mm)      its outward axis, the cable diameter (0.0085 m),
                            AND ``cable_tail(uid)`` -> the polyline of the
                            0.35-0.95 m of cable THIS module already built,
                            ending in ``tail_end``/``tail_dir``.
                            THE BOUNDARY: I own the gland and the tail up to
                            ``tail_end``.  You own everything from that point —
                            the run to the floor, the coil, the controller box,
                            the plug and the LED.  Start your first cable vertex
                            AT ``tail_end`` with tangent ``tail_dir`` and the
                            joint is invisible.  Do not re-model the gland.

  tyre_trolley              ``cradle_footprint(uid)`` -> for every instance, the
     (28, 13 m, 35 mm)      blanketed OD, the axial width over the hems, the
                            contact-patch half-length, and the local frame.
                            ``pose_of(uid)`` tells you which of the 56 are
                            already standing on the floor (do not put a trolley
                            under those) and which are laid flat.
                            ``stack_seat(uid)`` -> the plane a second wheel
                            seats on when these are stacked flat, including the
                            17 mm the blanket squashes.

  garage_tyre_allocation    ``bare_wheel_uids()`` and ``blanketed_uids()``; the
     (28, 22 m, 35 mm)      "blanketed vs bare" axis is already resolved here.
                            ``wheel_profile(corner)`` -> the (x, r) section of
                            the tyre and the rim so a stack you build yourself
                            is the same object.  ``compound_of(uid)`` -> the
                            compound index and its band colour, so an allocation
                            stack reads as a real allocation.

  crew_tyre_carrier_on      ``carry_grip(uid)`` -> the two handle loops as world
  crew_tyre_carrier_off     arcs with their tangents, the assembly mass
     (4 + 4, 10 m, 35 mm)   (11.2-13.6 kg), the centre of mass, and the axial
                            width, which is what decides where a forearm goes.
                            ``hand_pads(uid)`` -> the two 120 x 90 mm patches of
                            tread a carrier's palms actually land on.

  Anyone at all             ``plan()`` -> all 56 records.  ``build(...)`` emits
                            into collection ``W_Item_TyreBlanket`` as ONE joined
                            mesh object per instance, named ``TBK_i##_<pose>``,
                            recentred on its own centroid with the placement in
                            the object matrix (law 6).

WHERE THEY ARE.  56 = 14 pit boxes x 4 wheels, which is not a coincidence and is
not a choice: the manifest's 56 and the spec's 14 garages are the same fact.
Bay pitch is 320 m / 14 = 22.857 m over circuit x -245..+75, garage front at
circuit y = +23.5, and every set stands in the working half of the 12 m pit lane
between y = +20.6 and y = +22.9 — 8 m clear of the fast lane, never on it.
Ground comes from ``C.world_ground_z`` (which answers z = 0.000,
``build_architecture:paving``, over the whole run) and never from an assumed z.

DEVIATION FROM THE MANIFEST, DECLARED
-------------------------------------
The manifest gives ``typical_height_m`` 0.68.  The round-1 car this film is
about carries 0.720 m tyres — measured, ``round2_inventory.md`` line 84, the
``wheel_tyre_`` module bounding box is 4.32 x 2.01 x **0.72** — and law 3 says
scale against the measured car.  A blanket that fits a 0.68 m wheel does not fit
this car's wheel, and the crew carry these to that car.  So the tyre is 0.720 m
OD (18 in rim, 305 mm front / 405 mm rear section) and the blanketed assembly is
**0.748 m** OD, standing 0.728 m proud of the deck after the 20 mm bed-in.  That
is +7.1 % on the manifest's height and therefore ~209 px rather than 195 px on
the 4K master.  The camera specification — 13.0 m, 35 mm — is honoured exactly;
it is only the descriptive height that moves, and it moves toward the car.

WHAT IS SHADING AND WHAT IS MESH, STATED ONCE
---------------------------------------------
MESH: every quilt channel and stitch valley, the closure overlap and its gape,
every hem pleat, the bound welts, all straps, all buckles, both handles and
their bar tacks, the gland, the cable, the stitched patches, the burn-throughs
and their char lips, the tyre section including its contact-patch flattening,
its moulding vent spues, its wear-indicator holes, its raised sidewall
lettering, the rim barrel, both flanges, all ten spokes, the hub, the centre-lock
nut, the six drive pegs and the valve stem.
SHADING: the 0.34 mm weave, the silicone sheen, thread gloss, printed ink,
scorch discolouration, brake dust, rubber pickup, marbles under 2 mm, oil, and
the aluminised inner face.

Contract: world_contract 1.0.1.  Blender 5.2 LTS.  No image textures, no
external anything: verified by the gate, and by ``--selftest``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                       # noqa: E402

try:
    import bpy                                                   # noqa: E402
    from mathutils import Vector                                 # noqa: E402
except ImportError:                     # importable from a bare shell
    bpy = None
    Vector = None


# ==============================================================================
#  1.  IDENTITY, AND THE NUMBERS THE MANIFEST DECIDED
# ==============================================================================

ITEM = "tyre_blanket"
COLL = "W_Item_TyreBlanket"
PFX = "TBK_"

FILMED_AT_M = 13.0          # manifest nearest_camera_m — the acceptance shot
LENS_MM = 35.0              # manifest lens_at_closest_mm
ONSCREEN_PX_4K = 195.0      # manifest, on the 0.68 m it assumed
DEP_LENS_MM = 58.0          # tyre_blanket_controller, same 13.0 m — the TIGHT one
CARRY_DIST_M = 10.0         # crew_tyre_carrier_on/off

PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M          # 287.18
PX_PER_M_TIGHT = (3840.0 * DEP_LENS_MM / 36.0) / FILMED_AT_M  # 475.93
MM_PER_PX = 1000.0 / PX_PER_M_TIGHT                          # 2.101
MESH_FLOOR_M = 0.0010       # "half a pixel at the tightest lens" -> the mesh line

_T0 = time.time()
_QUIET = False


def log(msg):
    if not _QUIET:
        print("[%7.2fs] %s%s" % (time.time() - _T0, PFX, msg), flush=True)


# ------------------------------------------------------------------ the wheel
# 2022-spec 18 in F1 wheel, scaled against the measured car (OD 0.720 m).
TYRE_OD = 0.7200
TYRE_R = TYRE_OD * 0.5                      # 0.3600
RIM_D = 0.4572                              # 18.00 in
RIM_R = RIM_D * 0.5                         # 0.2286
BEAD_SEAT_R = RIM_R + 0.0050                # 0.2336
FLANGE_R = RIM_R + 0.0134                   # 0.2420  rim flange lip
W_FRONT = 0.3050
W_REAR = 0.4050
RIM_W_FRAC = 0.900                          # rim width as a fraction of section
CROWN_DROP = 0.0022                         # tread crown, centre to tread edge
SHOULDER_R = 0.0320

# ---------------------------------------------------------------- the blanket
BLK_SHELL_T = 0.00070       # one face of silicone-coated glass cloth
BLK_BATT_T = 0.01180        # needled silica batting, uncompressed
BLK_T = 2 * BLK_SHELL_T + BLK_BATT_T        # 0.01320 nominal
BLK_T_STITCH = 0.00380      # thickness at a quilt stitch line (crushed)
BLK_GAP = 0.0020            # mean standoff of the inner face from the tyre
HEM_R = 0.2372              # the elastic hem circle.  NOT a free parameter:
                            # it is where the tyre's own lower sidewall sits
                            # after the elastic has pulled the edge 2.2 mm
                            # inboard over the rim flange (FLANGE_R 0.2420), and
                            # it is derived from the tyre section in
                            # `conform_profile`, not asserted.  Published because
                            # garage_tyre_allocation stacks on it.
HEM_ROLL = 0.0060           # rolled-and-bound hem bead radius
OVERLAP_M = 0.0900          # closure overlap, arc length at the tread radius
BINDING_W = 0.0180          # bound seam tape width
BINDING_H = 0.0032          # and how proud the welt stands

STRAP_W = 0.0380
STRAP_T = 0.0025
BUCKLE_L = 0.0460
BUCKLE_W = 0.0260
BUCKLE_H = 0.0120
HANDLE_L = 0.2000
HANDLE_RISE = 0.0450
GLAND_D = 0.0260
CABLE_D = 0.0085

BASE_EMBED = C.BASE_EMBED_M                 # 0.020, law 5

# ---------------------------------------------------------------- the world
GARAGE_X0 = -245.0          # circuit frame, spec paddock.garages_design.x
GARAGE_X1 = 75.0
GARAGE_FRONT_Y = 23.5       # spec pit_lane_design_y[1]
PIT_LANE_Y0 = 11.5
N_BAYS = 14
BAY_PITCH = (GARAGE_X1 - GARAGE_X0) / N_BAYS        # 22.857 m

# The five compounds.  Names invented; the colour code is the real convention
# because a colour code that does not read as one is not a colour code.
# LINEAR reflectances, and they are half what "red", "yellow" and "white" want
# to be.  This is a 14 mm stripe of paint on black rubber standing in a 12.5 deg
# raking key under a -3.048 EV AgX exposure that already puts a 0.20 albedo
# surface 2.25 stops above middle grey.  The first pass used 0.42/0.50/0.62 and
# the "HARD" band rendered as a glaring cream ring wider and brighter than the
# garage front behind it -- measured 0.723 sRGB against the wall's 0.740.
COMPOUNDS = [
    # key, band linear rgb, tread pattern, name printed on the sidewall
    ("SOFT",  (0.1900, 0.0170, 0.0140), "slick", "C4"),
    ("MED",   (0.2400, 0.1550, 0.0120), "slick", "C3"),
    ("HARD",  (0.3000, 0.2950, 0.2850), "slick", "C2"),
    ("INTER", (0.0220, 0.1150, 0.0280), "inter", "CI"),
    ("WET",   (0.0160, 0.0450, 0.1650), "wet",   "CW"),
]

CORNERS = ["FL", "FR", "RL", "RR"]


def corner_width(corner):
    return W_FRONT if corner in ("FL", "FR") else W_REAR


# ==============================================================================
#  2.  DETERMINISM
# ==============================================================================
# Every number in the plan comes from here.  Nothing uses `random`, nothing
# depends on dict ordering, and a rebuild six months from now produces the same
# 56 objects down to the last pleat.

_M64 = (1 << 64) - 1


def rnd(*keys):
    """splitmix64 over the keys -> float in [0, 1).  Scalar, exact, portable."""
    x = 0x9E3779B97F4A7C15
    for k in keys:
        if isinstance(k, str):
            v = 0
            for ch in k:
                v = (v * 131 + ord(ch)) & _M64
        else:
            v = int(round(float(k) * 4096.0)) & _M64
        x = (x ^ v) & _M64
        x = (x * 0xBF58476D1CE4E5B9) & _M64
        x ^= (x >> 31)
        x = (x * 0x94D049BB133111EB) & _M64
        x ^= (x >> 29)
    return ((x >> 12) & ((1 << 40) - 1)) / float(1 << 40)


def rr(lo, hi, *keys):
    return lo + (hi - lo) * rnd(*keys)


def rpick(seq, *keys):
    return seq[min(int(rnd(*keys) * len(seq)), len(seq) - 1)]


def rbool(p, *keys):
    return rnd(*keys) < p


def _hash2(ix, iy, seed):
    ix = np.asarray(ix).astype(np.int64)
    iy = np.asarray(iy).astype(np.int64)
    h = (ix * 374761393 + iy * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h.astype(np.float64) / 4294967295.0


def vnoise2(x, y, seed=0):
    """Cubic-smoothed 2D value noise in [0, 1).  Vectorised, deterministic."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    a = _hash2(ix, iy, seed); b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed); d = _hash2(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def fbm2(x, y, seed=0, octaves=4, lac=2.07, gain=0.52):
    tot = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(octaves):
        tot = tot + amp * vnoise2(np.asarray(x) * frq, np.asarray(y) * frq,
                                  seed * 977 + o * 31)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def sstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / max(1e-12, (e1 - e0)), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bump01(x):
    """A C1 hump: 0 at x=0 and x=1, 1 at x=0.5."""
    t = np.clip(np.asarray(x, float), 0.0, 1.0)
    return np.sin(math.pi * t) ** 2


def unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


# ==============================================================================
#  3.  A HAND-CUT STROKE FACE, AND SIGNED DISTANCE FROM IT
# ==============================================================================
# The brief forbids downloaded assets and I am not going to argue about whether a
# bundled font datablock counts, so the artwork on these blankets is set in a
# face cut here, by hand, as polylines in a 0..1 em box.  Rasterised as a signed
# distance field with a round join, a stroke face at 0.19 em weight reads as a
# heavy geometric sans -- which is what a screen-printed blanket carries anyway,
# because thin strokes do not survive a silicone-glass weave.
#
# The SDF is baked to a vertex attribute in metres and thresholded in the
# shader, so the type is resolution-independent: it is as sharp at 200 mm from
# the lens as it is at 13 m.

GLYPH = {
    "A": [[(.06, 0), (.5, 1), (.94, 0)], [(.235, .40), (.765, .40)]],
    "B": [[(.14, 0), (.14, 1), (.62, 1), (.84, .84), (.66, .55), (.14, .55)],
          [(.66, .55), (.88, .30), (.66, 0), (.14, 0)]],
    "C": [[(.90, .84), (.66, 1), (.30, .98), (.10, .70), (.10, .30),
           (.30, .02), (.66, 0), (.90, .16)]],
    "D": [[(.14, 0), (.14, 1), (.58, 1), (.86, .70), (.86, .30), (.58, 0),
           (.14, 0)]],
    "E": [[(.88, 1), (.14, 1), (.14, 0), (.88, 0)], [(.14, .50), (.70, .50)]],
    "F": [[(.14, 0), (.14, 1), (.88, 1)], [(.14, .52), (.70, .52)]],
    "G": [[(.90, .86), (.62, 1), (.28, .96), (.10, .68), (.10, .30),
           (.30, .02), (.66, 0), (.90, .20), (.90, .44), (.58, .44)]],
    "H": [[(.14, 0), (.14, 1)], [(.86, 0), (.86, 1)], [(.14, .52), (.86, .52)]],
    "I": [[(.50, 0), (.50, 1)]],
    "J": [[(.80, 1), (.80, .24), (.60, .02), (.30, .02), (.14, .22)]],
    "K": [[(.16, 0), (.16, 1)], [(.86, 1), (.20, .46)], [(.42, .62), (.90, 0)]],
    "L": [[(.18, 1), (.18, 0), (.88, 0)]],
    "M": [[(.10, 0), (.10, 1), (.50, .34), (.90, 1), (.90, 0)]],
    "N": [[(.14, 0), (.14, 1), (.86, 0), (.86, 1)]],
    "O": [[(.10, .30), (.30, 1), (.70, 1), (.90, .30), (.70, 0), (.30, 0),
           (.10, .30)]],
    "P": [[(.14, 0), (.14, 1), (.66, 1), (.88, .78), (.66, .54), (.14, .54)]],
    "Q": [[(.10, .30), (.30, 1), (.70, 1), (.90, .30), (.70, 0), (.30, 0),
           (.10, .30)], [(.60, .26), (.94, -.06)]],
    "R": [[(.14, 0), (.14, 1), (.66, 1), (.88, .78), (.66, .56), (.14, .56)],
          [(.50, .56), (.90, 0)]],
    "S": [[(.90, .82), (.60, 1), (.24, .96), (.12, .72), (.34, .54),
           (.70, .48), (.88, .28), (.74, .06), (.36, 0), (.10, .18)]],
    "T": [[(.06, 1), (.94, 1)], [(.50, 1), (.50, 0)]],
    "U": [[(.14, 1), (.14, .26), (.34, .02), (.66, .02), (.86, .26), (.86, 1)]],
    "V": [[(.06, 1), (.50, 0), (.94, 1)]],
    "W": [[(.03, 1), (.26, 0), (.50, .64), (.74, 0), (.97, 1)]],
    "X": [[(.10, 1), (.90, 0)], [(.90, 1), (.10, 0)]],
    "Y": [[(.08, 1), (.50, .48), (.92, 1)], [(.50, .48), (.50, 0)]],
    "Z": [[(.10, 1), (.90, 1), (.10, 0), (.90, 0)]],
    "0": [[(.12, .30), (.30, 1), (.70, 1), (.88, .30), (.70, 0), (.30, 0),
           (.12, .30)], [(.28, .22), (.72, .78)]],
    "1": [[(.24, .76), (.52, 1), (.52, 0)], [(.20, 0), (.84, 0)]],
    "2": [[(.10, .78), (.30, 1), (.70, 1), (.90, .74), (.90, .58), (.10, 0),
           (.92, 0)]],
    "3": [[(.10, 1), (.88, 1), (.44, .56), (.88, .46), (.88, .18), (.66, 0),
           (.26, 0), (.10, .20)]],
    "4": [[(.70, 0), (.70, 1), (.08, .28), (.94, .28)]],
    "5": [[(.88, 1), (.16, 1), (.13, .56), (.60, .60), (.90, .44), (.90, .18),
           (.68, 0), (.20, 0)]],
    "6": [[(.84, .88), (.50, 1), (.16, .76), (.10, .28), (.30, 0), (.68, 0),
           (.88, .26), (.72, .50), (.28, .54), (.12, .38)]],
    "7": [[(.08, 1), (.92, 1), (.38, 0)]],
    "8": [[(.50, .52), (.20, .64), (.20, .86), (.40, 1), (.60, 1), (.80, .86),
           (.80, .64), (.50, .52), (.16, .38), (.14, .18), (.34, 0), (.66, 0),
           (.86, .18), (.84, .38), (.50, .52)]],
    "9": [[(.16, .16), (.50, .04), (.84, .28), (.90, .74), (.70, 1), (.32, 1),
           (.12, .74), (.28, .50), (.72, .46), (.88, .60)]],
    "-": [[(.14, .48), (.86, .48)]],
    ".": [[(.44, .04), (.56, .04)]],
    "/": [[(.14, -.06), (.86, 1.02)]],
    "'": [[(.50, 1.02), (.50, .74)]],
    " ": [],
}
GLYPH_ADV = 0.76


def text_segments(text, cap_h, tracking=0.14, weight=0.19):
    """-> (segs (n,2,2) in metres, advance width, stroke half-width)."""
    segs, x = [], 0.0
    for ch in str(text).upper():
        g = GLYPH.get(ch, GLYPH[" "])
        for pl in g:
            for i in range(len(pl) - 1):
                segs.append(((x + pl[i][0] * cap_h * GLYPH_ADV,
                              pl[i][1] * cap_h),
                             (x + pl[i + 1][0] * cap_h * GLYPH_ADV,
                              pl[i + 1][1] * cap_h)))
        x += cap_h * (GLYPH_ADV + tracking)
    w = max(x - cap_h * tracking, 0.0)
    return (np.asarray(segs, float) if segs else np.zeros((0, 2, 2))), w, \
        weight * cap_h * 0.5


def seg_sdf(px, py, segs, halfw):
    """Signed distance to a stroked polyline set.  Negative INSIDE the stroke."""
    px = np.asarray(px, float); py = np.asarray(py, float)
    if len(segs) == 0:
        return np.full(px.shape, 1e6)
    best = np.full(px.shape, 1e6)
    for (ax, ay), (bx, by) in segs:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-14:
            d = np.hypot(px - ax, py - ay)
        else:
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
            d = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
        best = np.minimum(best, d)
    return best - halfw


def rrect_sdf(px, py, hw, hh, r):
    """Signed distance to a rounded rectangle centred on the origin."""
    qx = np.abs(np.asarray(px, float)) - (hw - r)
    qy = np.abs(np.asarray(py, float)) - (hh - r)
    outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return outside + inside - r


# ==============================================================================
#  4.  CURVES
# ==============================================================================

def catmull(P, per_seg=18, closed=False, alpha=0.5):
    """Centripetal Catmull-Rom through P (m,d) -> a dense polyline."""
    P = np.asarray(P, float)
    n = len(P)
    if n < 3:
        return P.copy()
    idx = list(range(n))
    if closed:
        seq = [(idx[(i - 1) % n], idx[i], idx[(i + 1) % n], idx[(i + 2) % n])
               for i in range(n)]
    else:
        seq = [(idx[max(i - 1, 0)], idx[i], idx[min(i + 1, n - 1)],
                idx[min(i + 2, n - 1)]) for i in range(n - 1)]
    out = []
    for (i0, i1, i2, i3) in seq:
        p0, p1, p2, p3 = P[i0], P[i1], P[i2], P[i3]
        def tj(ti, pa, pb):
            return ti + max(np.linalg.norm(pb - pa), 1e-9) ** alpha
        t0 = 0.0
        t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        t = np.linspace(t1, t2, per_seg, endpoint=False)[:, None]
        A1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        A2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        A3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
        B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
        out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
    Q = np.concatenate(out, axis=0)
    if not closed:
        Q = np.concatenate([Q, P[-1][None, :]], axis=0)
    return Q


def arclen(P, closed=False):
    P = np.asarray(P, float)
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    if closed:
        d = np.concatenate([d, [np.linalg.norm(P[0] - P[-1])]])
    return np.concatenate([[0.0], np.cumsum(d)])


def resample_at(P, s_want, closed=False, s=None):
    """Sample the polyline P at the given arc-length positions.

    `s` MUST be passed whenever P is not itself the curve whose arc length
    parameterises it.  Leaving it out for a NORMAL field -- which is what the
    first version of this module did -- reparameterises the normals by the arc
    length of the unit-normal hodograph instead of by the arc length of the
    curve, which silently rotates the normal field by up to 130 degrees at the
    hem and puts 125 mm of blanket inside the tyre.  Measured, not guessed:
    cp["N"][-1] was (+0.785, -0.619) and the resample returned (-0.990, -0.144).
    """
    P = np.asarray(P, float)
    s = arclen(P, closed) if s is None else np.asarray(s, float)
    if closed:
        P = np.concatenate([P, P[:1]], axis=0)
    out = np.empty((len(s_want), P.shape[1]))
    for d in range(P.shape[1]):
        out[:, d] = np.interp(np.clip(s_want, 0, s[-1]), s, P[:, d])
    return out


# ==============================================================================
#  5.  A GEOMETRY ACCUMULATOR
# ==============================================================================
# One instance is one joined mesh with ten material slots.  Everything below
# appends into an `Acc`, which keeps vertices, faces, per-face material ids and
# per-vertex attributes in numpy the whole way and only ever touches bpy once,
# through the foreach_set fast path.  Building 56 of these with `from_pydata`
# and python lists took 41 minutes; this takes 3.

# Per-vertex float attributes the shaders read.  Every one is a PHYSICAL
# quantity or a normalised mask, and every one is baked here rather than
# derived in the shader from a position -- law 6.
ATTR_DEFAULT = {
    "tb_print": 1.0,      # signed distance to printed artwork, m (neg = ink)
    "tb_region": 0.0,     # which part of the object this is (see REGION_*)
    "tb_quilt": 1.0,      # 0 in a stitch valley, 1 at a pillow crown
    "tb_scorch": 0.0,     # 0..1 heat damage
    "tb_wear": 0.0,       # 0..1 abrasion / handling polish
    "tb_grime": 0.0,      # 0..1 settled dirt, brake dust, rubber
    "tb_cav": 0.0,        # 0..1 cheap baked cavity (concavity of the sheet)
    "tb_seam": 1.0,       # distance to the nearest sewn seam, m
    "tb_face": 1.0,       # 1 = outer face of the shell, 0 = inner (aluminised)
    "tb_letter": 1.0,     # signed distance to raised tyre lettering, m
    "tb_band": 0.0,       # 0..1 compound colour band on the sidewall
    "tb_dust": 0.0,       # 0..1 brake dust load on the rim
    "tb_u": 0.0,          # fabric material coordinate, m
    "tb_v": 0.0,
}

REGION_SHELL = 0.0
REGION_SIDEPANEL = 1.0
REGION_HEM = 2.0
REGION_BINDING = 3.0
REGION_STRAP = 4.0
REGION_BUCKLE = 5.0
REGION_CABLE = 6.0
REGION_TYRE_TREAD = 7.0
REGION_TYRE_WALL = 8.0
REGION_RIM = 9.0
REGION_PATCH = 10.0
REGION_BATT = 11.0

# material slot order, fixed, so a dependant can rely on it
MATS = ["Shell", "Webbing", "Buckle", "Cable", "Batting", "Label",
        "Rubber", "Rim", "Velcro", "Binding"]
MAT_INDEX = {n: i for i, n in enumerate(MATS)}


class Acc(object):
    """Vertices, faces, material ids and attributes, all numpy, all appended."""

    def __init__(self):
        self._V = []
        self._Q = []          # (m,4)
        self._T = []          # (m,3)
        self._QM = []
        self._TM = []
        self._A = {k: [] for k in ATTR_DEFAULT}
        self.n = 0

    def add(self, V, quads=None, tris=None, mat="Shell", qmat=None, tmat=None,
            **attrs):
        V = np.ascontiguousarray(np.asarray(V, float).reshape(-1, 3))
        nv = len(V)
        if nv == 0:
            return 0
        base = self.n
        self._V.append(V)
        self.n += nv
        mi = MAT_INDEX[mat] if isinstance(mat, str) else int(mat)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            self._Q.append(q)
            self._QM.append(np.full(len(q), mi, np.int32) if qmat is None
                            else np.asarray(qmat, np.int32).reshape(-1))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self._T.append(t)
            self._TM.append(np.full(len(t), mi, np.int32) if tmat is None
                            else np.asarray(tmat, np.int32).reshape(-1))
        for k, dflt in ATTR_DEFAULT.items():
            a = attrs.get(k, None)
            if a is None:
                self._A[k].append(np.full(nv, dflt))
            else:
                a = np.asarray(a, float)
                self._A[k].append(np.broadcast_to(a, (nv,)).astype(float).copy())
        return base

    def merge(self, other, xform=None):
        """Append another Acc, optionally through a 4x4 transform."""
        if other.n == 0:
            return
        V = np.concatenate(other._V, axis=0)
        if xform is not None:
            V = V @ xform[:3, :3].T + xform[:3, 3]
        base = self.n
        self._V.append(V)
        self.n += len(V)
        for q, m in zip(other._Q, other._QM):
            self._Q.append(q + base); self._QM.append(m)
        for t, m in zip(other._T, other._TM):
            self._T.append(t + base); self._TM.append(m)
        for k in ATTR_DEFAULT:
            self._A[k].append(np.concatenate(other._A[k]) if other._A[k]
                              else np.full(len(V), ATTR_DEFAULT[k]))

    # -- read-back ---------------------------------------------------------
    def verts(self):
        return np.concatenate(self._V, axis=0) if self._V else np.zeros((0, 3))

    def faces(self):
        Q = np.concatenate(self._Q, axis=0) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T, axis=0) if self._T else np.zeros((0, 3), np.int64)
        QM = np.concatenate(self._QM) if self._QM else np.zeros(0, np.int32)
        TM = np.concatenate(self._TM) if self._TM else np.zeros(0, np.int32)
        return Q, T, QM, TM

    def attr(self, k):
        return np.concatenate(self._A[k]) if self._A[k] else np.zeros(0)

    def tris(self):
        Q, T, _, _ = self.faces()
        return 2 * len(Q) + len(T)

    def transform(self, M):
        self._V = [v @ M[:3, :3].T + M[:3, 3] for v in self._V]

    def map_verts(self, fn):
        self._V = [fn(v) for v in self._V]

    def bounds(self):
        V = self.verts()
        return V.min(axis=0), V.max(axis=0)


# ------------------------------------------------------------------ primitives

def grid_quads(nr, nc, wrap_c=False, wrap_r=False):
    """Quad indices for an (nr x nc) vertex grid, row-major."""
    r = np.arange(nr if wrap_r else nr - 1)
    c = np.arange(nc if wrap_c else nc - 1)
    R, Cc = np.meshgrid(r, c, indexing="ij")
    r1 = (R + 1) % nr if wrap_r else R + 1
    c1 = (Cc + 1) % nc if wrap_c else Cc + 1
    a = R * nc + Cc
    b = R * nc + c1
    d = r1 * nc + Cc
    e = r1 * nc + c1
    return np.stack([a.ravel(), b.ravel(), e.ravel(), d.ravel()], axis=1)


def fan_tris(n, centre_idx, ring_idx, flip=False):
    a = np.full(n, centre_idx)
    b = ring_idx
    c = np.roll(ring_idx, -1)
    return np.stack([a, c, b] if flip else [a, b, c], axis=1)


def revolve(loop_xr, thetas, closed_loop=True, flip=False):
    """Revolve a 2D cross-section (x, r) about the local X axis.

    thetas is the angular sample list (radians, need not be uniform); the result
    always wraps.  -> (verts, quads)
    """
    L = np.asarray(loop_xr, float)
    nl, nt = len(L), len(thetas)
    ct = np.cos(thetas)[:, None]
    st = np.sin(thetas)[:, None]
    X = np.broadcast_to(L[None, :, 0], (nt, nl))
    R = np.broadcast_to(L[None, :, 1], (nt, nl))
    V = np.stack([X, R * ct, R * st], axis=-1).reshape(-1, 3)
    Q = grid_quads(nt, nl, wrap_c=closed_loop, wrap_r=True)
    if flip:
        Q = Q[:, ::-1]
    return V, Q


def adaptive_axis(s0, s1, base, refines=(), hard=()):
    """Sample [s0, s1] at `base` spacing, finer inside each (a, b, step) refine.

    This is how a 5 mm quilt valley gets 2 mm rows without the whole 0.55 m
    section carrying 2 mm rows: 4x the mesh where the light does something and
    the base step everywhere else.
    """
    xs = [float(s0)]
    s = float(s0)
    guard = 0
    while s < s1 - 1e-9:
        step = base
        for (a, b, st) in refines:
            if (a - 2.0 * st) <= s <= (b + 2.0 * st):
                step = min(step, st)
        s = min(s + step, s1)
        xs.append(s)
        guard += 1
        if guard > 400000:
            break
    xs = np.array(xs)
    for h in hard:
        if s0 < h < s1:
            xs = np.concatenate([xs, [h]])
    xs = np.unique(np.round(xs, 9))
    return xs


def sweep_ribbon(path, up, half_w, thick, close=False, taper=None):
    """Sweep a rectangular section along a 3D path with a given up vector field.

    -> (verts, quads).  A strap, a handle, a binding welt and a label edge are
    all this function; the difference is the path and the section.
    """
    P = np.asarray(path, float)
    n = len(P)
    T = np.gradient(P, axis=0)
    T = unit(T)
    U = unit(np.asarray(up, float).reshape(-1, 3) * np.ones((n, 1)))
    S = unit(np.cross(T, U))
    U = unit(np.cross(S, T))
    hw = np.asarray(half_w, float) * np.ones(n)
    th = np.asarray(thick, float) * np.ones(n)
    if taper is not None:
        hw = hw * taper
    # rounded section: 8 points round a stadium so the strap edge is not a knife
    ang = np.linspace(0, 2 * math.pi, 12, endpoint=False)
    ex = np.where(np.cos(ang) >= 0, 1.0, -1.0)
    ez = np.sin(ang)
    cx = np.cos(ang)
    pts = []
    for k in range(12):
        off = (S * (hw[:, None] * np.clip(cx[k] * 1.35, -1, 1))
               + U * (th[:, None] * 0.5 * ez[k]))
        pts.append(P + off)
    V = np.stack(pts, axis=1).reshape(-1, 3)
    Q = grid_quads(n, 12, wrap_c=True, wrap_r=close)
    return V, Q


def sweep_tube(path, radius, nside=12, close_ends=True, ref_up=(0, 0, 1)):
    """Parallel-transport swept tube -> (verts, quads, tris)."""
    P = np.asarray(path, float)
    n = len(P)
    T = unit(np.gradient(P, axis=0))
    U = np.zeros((n, 3))
    u = np.asarray(ref_up, float)
    u = unit(u - T[0] * np.dot(u, T[0]))
    if np.linalg.norm(u) < 1e-6:
        u = unit(np.cross(T[0], (1.0, 0.0, 0.0)))
    U[0] = u
    for i in range(1, n):
        v = U[i - 1] - T[i] * np.dot(U[i - 1], T[i])
        nv = np.linalg.norm(v)
        U[i] = v / nv if nv > 1e-9 else U[i - 1]
    S = unit(np.cross(T, U))
    ang = np.linspace(0, 2 * math.pi, nside, endpoint=False)
    r = np.asarray(radius, float) * np.ones(n)
    pts = [P + (S * np.cos(a) + U * np.sin(a)) * r[:, None] for a in ang]
    V = np.stack(pts, axis=1).reshape(-1, 3)
    Q = grid_quads(n, nside, wrap_c=True)
    tris = []
    if close_ends:
        c0 = len(V)
        V = np.concatenate([V, P[:1], P[-1:]], axis=0)
        ring0 = np.arange(nside)
        ring1 = (n - 1) * nside + np.arange(nside)
        tris.append(fan_tris(nside, c0, ring0, flip=True))
        tris.append(fan_tris(nside, c0 + 1, ring1))
    Tr = np.concatenate(tris, axis=0) if tris else np.zeros((0, 3), np.int64)
    return V, Q, Tr


def rounded_box(size, radius=0.0015, seg=14, centre=(0, 0, 0)):
    """A box with genuinely rounded arrises -> (verts, quads).

    A 46 mm buckle is 22 px wide at the tight lens and its 1.5 mm arris is
    0.7 px of highlight.  A square corner there is a black line -- which is why
    every hard part in this module is built through here rather than as a cube.

    The construction is the offset-surface one: take the unit sphere's normal
    field, clamp the CENTRE point to the inner box (the box shrunk by r), and
    add r * n.  That is exactly the Minkowski sum of a box and a ball, so every
    face is flat, every edge is a quarter-cylinder of radius r and every corner
    is an eighth-sphere -- and it has no seams.
    """
    sx, sy, sz = [s * 0.5 for s in size]
    r = float(min(radius, 0.49 * min(size)))
    m = int(seg)
    th = np.linspace(0.0, math.pi, m)
    ph = np.linspace(0.0, 2 * math.pi, 2 * m, endpoint=False)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    nx = np.sin(TH) * np.cos(PH)
    ny = np.sin(TH) * np.sin(PH)
    nz = np.cos(TH)
    ax = np.maximum(np.array([sx - r, sy - r, sz - r]), 1e-6)
    big = 1e6
    kx = np.clip(nx * big, -ax[0], ax[0])
    ky = np.clip(ny * big, -ax[1], ax[1])
    kz = np.clip(nz * big, -ax[2], ax[2])
    V = np.stack([kx + r * nx, ky + r * ny, kz + r * nz], axis=-1)
    V = V.reshape(-1, 3) + np.asarray(centre, float)
    return V, grid_quads(m, 2 * m, wrap_c=True)


def disc(radius0, radius1, thetas, x, flip=False):
    """An annular ring in the plane x = const (local Y-Z plane)."""
    ct, st = np.cos(thetas), np.sin(thetas)
    V0 = np.stack([np.full(len(thetas), x), radius0 * ct, radius0 * st], axis=1)
    V1 = np.stack([np.full(len(thetas), x), radius1 * ct, radius1 * st], axis=1)
    V = np.concatenate([V0, V1], axis=0)
    Q = grid_quads(2, len(thetas), wrap_c=True)
    if flip:
        Q = Q[:, ::-1]
    return V, Q


def lay_on_floor(P, zf, wander=0.35, phase=0.0):
    """Continue a dangling path ALONG the deck instead of through it.

    A 0.34 m strap tail hanging off a buckle 0.18 m above the ground does not
    stop at the ground and it does not go through it: it lands, and the rest of
    its length lies there.  Arc length is preserved -- the tail is the same
    length before and after -- which is the only version of this that does not
    make the strap change size when the wheel is laid flat.
    """
    P = np.asarray(P, float).copy()
    out = [P[0].copy()]
    for i in range(1, len(P)):
        d = P[i] - P[i - 1]
        L = float(np.linalg.norm(d))
        p = out[-1] + d
        if p[2] < zf:
            h = np.array([d[0], d[1], 0.0])
            nh = float(np.linalg.norm(h))
            h = h / nh if nh > 1e-9 else np.array([1.0, 0.0, 0.0])
            if wander:
                h = unit(h + np.cross(h, np.array([0.0, 0.0, 1.0]))
                         * wander * math.sin(2.6 * i + phase))
            p = np.array([out[-1][0], out[-1][1], max(out[-1][2], zf)]) + h * L
            p[2] = zf + 0.0014 * abs(math.sin(2.1 * i + phase))
        out.append(p)
    return np.asarray(out)


def cavity_from_height(H):
    """A cheap ambient-occlusion proxy: local concavity of a height field.

    Real AO on 25 M triangles of quilted cloth is not affordable per rebuild and
    the shader's own AO node cannot see the sheet's own folds at the right
    scale.  The discrete Laplacian of the displacement does: positive where the
    sheet dishes in (a stitch valley, a crease), zero on a flat, negative on a
    pillow crown.  It costs one convolution and it is what makes the quilting
    read as quilting rather than as ribbing.
    """
    L = (np.roll(H, 1, 0) + np.roll(H, -1, 0)
         + np.roll(H, 1, 1) + np.roll(H, -1, 1) - 4.0 * H)
    L[0, :] = L[1, :]; L[-1, :] = L[-2, :]
    s = np.percentile(np.abs(L), 97.0) + 1e-9
    return np.clip(L / s, 0.0, 1.0)


# ==============================================================================
#  6.  THE WHEEL:  an 18 in F1 rim and the slick on it
# ==============================================================================
# The tyre is not scenery here.  It is the FORM the blanket is stretched over,
# so its section decides where the fabric bulges, where the hem can grip and how
# wide the gape opens; and on the eleven instances whose blanket is off or
# peeled it is the object itself.
#
# Section, outboard half, in metres, from the measured car's 0.720 m OD:
#     crown            r 0.3600, flat to +-0.86 of the half width, 2.2 mm crown
#     shoulder         r 0.3510 at 0.955 hw, 32 mm radius
#     max section      r 0.2880 at 1.010 hw   <- the sidewall bulges PROUD of the
#                                                tread, which is what stops the
#                                                blanket's hem sliding off
#     bead             r 0.2336 on the rim seat


def tyre_section(width, wear=0.0, squash=0.0):
    """-> (P (n,2) = (x, r), N (n,2) outward normal, s arc length, tag).

    Traversed INBOARD bead -> crown -> OUTBOARD bead, so +x is outboard.
    `tag`: 0 bead, 1 sidewall, 2 shoulder, 3 tread.
    """
    hw = width * 0.5
    rimhw = width * RIM_W_FRAC * 0.5
    bx = rimhw - 0.0100
    Ro = TYRE_R - wear * 0.0045
    cp = [
        (0.000 * hw, Ro),
        (0.420 * hw, Ro - CROWN_DROP * 0.18),
        (0.720 * hw, Ro - CROWN_DROP * 0.62),
        (0.860 * hw, Ro - CROWN_DROP * 1.00),
        (0.930 * hw, Ro - 0.0042 - wear * 0.0020),
        (0.980 * hw, Ro - 0.0140 - wear * 0.0035),
        (1.008 * hw, Ro - 0.0300),
        (1.018 * hw, 0.3080 + squash * 0.004),
        (1.010 * hw, 0.2880 + squash * 0.006),
        (0.975 * hw, 0.2660 + squash * 0.004),
        (0.918 * hw, 0.2478),
        (bx + 0.0075, 0.2402),
        (bx, BEAD_SEAT_R),
    ]
    half = catmull(np.array(cp), per_seg=14)
    mirror = half[::-1].copy()
    mirror[:, 0] *= -1.0
    P = np.concatenate([mirror[:-1], half], axis=0)
    s = arclen(P)
    d = np.gradient(P, axis=0)
    N = unit(np.stack([-d[:, 1], d[:, 0]], axis=1))
    r = P[:, 1]
    ax = np.abs(P[:, 0])
    tag = np.where(r > Ro - CROWN_DROP - 0.0015, 3.0,
                   np.where(r > 0.3200, 2.0,
                            np.where(r > 0.2450, 1.0, 0.0)))
    return P, N, s, tag


def tyre_radius_at(width, x, wear=0.0):
    """r(x) on the tyre's outer surface — used for the fabric collision clamp."""
    P, _, _, _ = tyre_section(width, wear)
    xs, rs = P[:, 0], P[:, 1]
    o = np.argsort(xs)
    return np.interp(np.asarray(x, float), xs[o], rs[o],
                     left=rs[o][0], right=rs[o][-1])


def raised_lettering(acc, text, width, r_base, phi0, cap_h, x_sign,
                     wear=0.0, mat="Rubber", relief=0.0009, stroke=0.0060,
                     tag=1.0, arc_dir=1.0):
    """Raised sidewall lettering as REAL SWEPT GEOMETRY, not a bump map.

    A 0.9 mm letter at 2.101 mm/px is 0.43 px of relief, which by this module's
    own rule is shading -- except that on an F1 sidewall the lettering is the
    ONLY thing there, it is the difference between glossy moulded rubber and the
    matt sidewall around it, and at a grazing 12.5 deg sun it self-shadows along
    its whole length.  It also has a silhouette against the sky on the top of
    the wheel.  So it is built: each stroke of each glyph is swept as a rounded
    ribbon lying on the sidewall surface, which costs 2,800 quads for a wordmark
    and needs no refinement of the sidewall mesh at all.  A 1.5 mm sidewall grid
    carrying a displacement would have cost 168,000.
    """
    segs, adv, halfw = text_segments(text, cap_h, tracking=0.16,
                                     weight=stroke / cap_h * 2.0)
    if len(segs) == 0:
        return
    # letters run around the sidewall: glyph x -> arc, glyph y -> radius
    circ = 2.0 * math.pi * r_base
    for (ax, ay), (bx, by) in segs:
        n = max(3, int(np.hypot(bx - ax, by - ay) / 0.0035) + 2)
        t = np.linspace(0, 1, n)
        gx = ax + (bx - ax) * t
        gy = ay + (by - ay) * t
        phi = phi0 + arc_dir * (gx - adv * 0.5) / r_base
        rr_ = r_base + gy - cap_h * 0.5
        xw = x_sign * (tyre_wall_x(width, rr_) + relief * 0.5)
        P = np.stack([xw, rr_ * np.cos(phi), rr_ * np.sin(phi)], axis=1)
        up = np.stack([np.full(n, float(x_sign)), np.zeros(n), np.zeros(n)],
                      axis=1)
        V, Q = sweep_ribbon(P, up, stroke * 0.5, relief * 2.0)
        acc.add(V, quads=Q, mat=mat, tb_region=REGION_TYRE_WALL,
                tb_letter=-1.0, tb_wear=wear, tb_band=0.0)


def tyre_wall_x(width, r):
    """x of the OUTBOARD sidewall surface at radius r (the lettering plane)."""
    P, _, _, _ = tyre_section(width, 0.0)
    half = P[len(P) // 2:]                       # outboard half, x increasing
    rs = half[:, 1]
    o = np.argsort(rs)
    return np.interp(np.asarray(r, float), rs[o], half[o, 0])


def tyre_mesh(acc, rec, fine=True):
    """The slick.  Section, tread, vent spues, wear indicators and lettering."""
    W = rec["width"]
    wear = rec["wear"]
    comp = COMPOUNDS[rec["compound"]]
    P2, N2, s2, tag = tyre_section(W, wear)
    Ltot = s2[-1]

    base_r = 0.0045 if fine else 0.0090
    base_c = 0.0045 if fine else 0.0090
    # rows: fine at the shoulders and across the colour band; the crown is flat
    sh = s2[np.argmax(tag >= 2.0)]
    refines = [(0.0, 0.030, base_r * 0.7),
               (Ltot - 0.030, Ltot, base_r * 0.7)]
    if fine:
        refines += [(sh - 0.02, sh + 0.05, 0.0030),
                    (Ltot - sh - 0.05, Ltot - sh + 0.02, 0.0030)]
    rows_s = adaptive_axis(0.0, Ltot, base_r, refines)
    prof = resample_at(P2, rows_s, s=s2)
    pn = unit(resample_at(N2, rows_s, s=s2))
    ptag = np.interp(rows_s, s2, tag)

    circ = 2.0 * math.pi * TYRE_R
    grooved = comp[2] in ("inter", "wet")
    cref = []
    if fine and grooved:
        cref.append((0.0, circ, 0.0030))
    cols_s = adaptive_axis(0.0, circ, base_c, cref)[:-1]
    th = cols_s / TYRE_R
    nr, nc = len(rows_s), len(th)

    X = np.broadcast_to(prof[:, 0][:, None], (nr, nc)).copy()
    R = np.broadcast_to(prof[:, 1][:, None], (nr, nc)).copy()
    TT = np.broadcast_to(th[None, :], (nr, nc))
    NX = np.broadcast_to(pn[:, 0][:, None], (nr, nc))
    NR = np.broadcast_to(pn[:, 1][:, None], (nr, nc))
    is_tread = (ptag >= 2.6)[:, None] * np.ones((1, nc))
    is_wall = (ptag < 1.6)[:, None] * np.ones((1, nc))
    R0 = R.copy()

    # --- THE SIDEWALL IS NOT A TURNED DISC ---------------------------------
    # It came back from the first render as a flat cream plate 240 px across
    # with nothing on it but the wordmark, and that was the single most CG
    # thing in the frame.  A moulded F1 sidewall carries a rim-protector ring,
    # a shoulder ridge, the mould's own parting flash at the shoulder, and a
    # radial draw texture.  Everything >= 0.8 mm is here as GEOMETRY, displaced
    # along the SECTION NORMAL (which on a sidewall is axial, so a "ridge"
    # there is a change in x, not in r -- displacing r would have flattened it).
    dn = np.zeros((nr, nc))
    for r_c, amp, wid in ((0.2735, 0.0019, 0.0042),      # rim protector ring
                          (0.3025, 0.0011, 0.0055),      # mid-wall rib
                          (0.3255, 0.0014, 0.0038)):     # shoulder ridge
        dn += amp * np.exp(-((R0 - r_c) / wid) ** 2) * is_wall
    # the two-part mould's parting flash, 0.9 mm, at the shoulder tangent
    sh_r = TYRE_R - 0.0140
    dn += 0.0009 * np.exp(-((R0 - sh_r) / 0.0021) ** 2) * \
        (0.6 + 0.4 * np.sin(TT * 37.0 + 1.1))
    # radial draw texture.  0.35 mm over 90 flutes read as KNURLING on a
    # slick's sidewall -- the fix for a flat plate is not a machined one.
    # 0.12 mm over 64 breaks the specular sheet without inventing a tread.
    dn += 0.00012 * np.sin(TT * 64.0 + R0 * 21.0) * is_wall * \
        np.clip((R0 - 0.2450) / 0.05, 0, 1)

    # --- moulded relief on the crown ------------------------------------
    # A slick is not smooth.  It carries the mould's own 0.3 mm orange-peel, a
    # 1.1 mm circumferential graining once it has run, and picked-up marbles on
    # the shoulder.  Only the >= 1 mm terms are here; the rest is the shader.
    u = X / max(W * 0.5, 1e-6)
    grain = (fbm2(TT * TYRE_R / 0.055, X / 0.20, seed=int(rec["uid"]) * 7 + 3,
                  octaves=3) - 0.5)
    R += is_tread * grain * (0.0011 * (0.25 + 0.75 * wear))
    marb = np.clip(fbm2(TT * TYRE_R / 0.018, X / 0.020,
                        seed=int(rec["uid"]) * 11 + 5, octaves=2) - 0.62, 0, 1)
    shoulder = np.clip((np.abs(u) - 0.70) / 0.28, 0, 1) * is_tread
    R += marb * shoulder * 0.0026 * wear

    if grooved:
        # intermediate/wet: four swept channels, 6.5 mm deep, real geometry
        ng = 4 if comp[2] == "inter" else 5
        for g in range(ng):
            xc = W * (-0.36 + 0.72 * g / max(ng - 1, 1))
            sweep = 0.34 * np.sin(TT * (2 if comp[2] == "inter" else 3)
                                  + g * 0.7)
            d = np.abs(X - (xc + sweep * 0.05)) / 0.0085
            R -= np.clip(1.0 - d * d, 0, 1) * 0.0065 * is_tread

    if fine:
        # four tread-depth indicator holes, 4.2 mm dia x 2.6 mm
        for k in range(4):
            phk = (k * 0.5 + 0.13) * math.pi
            xk = W * (0.30 if k % 2 else -0.30)
            dphi = np.abs(((TT - phk + math.pi) % (2 * math.pi)) - math.pi)
            d = np.hypot(dphi * TYRE_R / 0.0021, (X - xk) / 0.0021)
            R -= np.clip(1.0 - d * d, 0, 1) * 0.0026

    X = X + NX * dn
    R = R + NR * dn
    V = np.stack([X, R * np.cos(TT), R * np.sin(TT)], axis=-1).reshape(-1, 3)
    Q = grid_quads(nr, nc, wrap_c=True)
    RR = R0.ravel()
    band = (sstep(0.2678, 0.2698, RR) * (1.0 - sstep(0.2822, 0.2842, RR)))
    acc.add(V, quads=Q, mat="Rubber",
            tb_region=np.where(is_tread.ravel() > 0.5, REGION_TYRE_TREAD,
                               REGION_TYRE_WALL),
            tb_wear=np.full(nr * nc, wear),
            tb_band=band,
            tb_grime=np.clip(0.25 + 0.6 * rec["dirt"], 0, 1),
            tb_u=(TT * TYRE_R).ravel(), tb_v=X.ravel())

    # --- vent spues: the whiskers a tyre keeps until it has been scrubbed ---
    if fine and wear < 0.55:
        nsp = int(90 * (1.0 - wear / 0.55))
        for k in range(nsp):
            a = rnd(rec["uid"], "spue", k) * 2 * math.pi
            xx = (rnd(rec["uid"], "spuex", k) - 0.5) * W * 1.86
            xx = float(np.clip(xx, -W * 0.52, W * 0.52))
            r0 = float(np.interp(abs(xx), np.abs(prof[:, 0]), prof[:, 1])) \
                if abs(xx) <= abs(prof[:, 0]).max() else TYRE_R
            r0 = float(tyre_radius_at(W, xx, wear))
            L = rr(0.0028, 0.0055, rec["uid"], "spuel", k)
            n = 5
            t = np.linspace(0, 1, n)
            bend = rr(-0.5, 0.5, rec["uid"], "spueb", k)
            rr_ = r0 - 0.0004 + L * t
            ph = a + bend * 0.010 * t * t / TYRE_R
            xs = xx + bend * 0.004 * t * t
            Pp = np.stack([xs, rr_ * np.cos(ph), rr_ * np.sin(ph)], axis=1)
            Vv, Qq, Tt = sweep_tube(Pp, np.linspace(0.00075, 0.00042, n),
                                    nside=6)
            acc.add(Vv, quads=Qq, tris=Tt, mat="Rubber",
                    tb_region=REGION_TYRE_TREAD, tb_wear=0.0)

    # --- sidewall lettering, both sides -----------------------------------
    if fine:
        brand = rec["tyre_brand"]
        # arc_dir = -1 on the OUTBOARD side: +X is outboard, so a viewer there
        # sees increasing theta running clockwise, and type laid along +theta
        # reads backwards.  Measured in the first render: "MERIDIAN" came out
        # as "NAIDIREM".  The inboard side takes +1 for the same reason.
        raised_lettering(acc, brand, W, 0.3050, rec["letter_phi"], 0.0340,
                         +1.0, wear=wear, relief=0.0011, stroke=0.0062,
                         arc_dir=-1.0)
        raised_lettering(acc, "%d/720-R18" % int(round(W * 1000)), W, 0.2760,
                         rec["letter_phi"] + 2.30, 0.0160, +1.0, wear=wear,
                         relief=0.0008, stroke=0.0032, arc_dir=-1.0)
        raised_lettering(acc, comp[3], W, 0.2760, rec["letter_phi"] - 2.10,
                         0.0210, +1.0, wear=wear, relief=0.0009, stroke=0.0040,
                         arc_dir=-1.0)
        raised_lettering(acc, brand, W, 0.3050, rec["letter_phi"] + math.pi,
                         0.0340, -1.0, wear=wear, relief=0.0011, stroke=0.0062,
                         arc_dir=+1.0)


def rim_mesh(acc, rec, fine=True):
    """The wheel: barrel, both flanges, ten spokes, hub, centre nut, valve.

    Everything inside the blanket's 0.504 m hem opening is visible on EVERY
    fitted instance -- 240 px across at the tight lens -- so this is not a
    stand-in disc.  Brake dust is baked as an attribute (`tb_dust`) with a
    gravity bias and a radial gradient, because a wheel that has done a stint
    is filthy in a pattern, not uniformly.
    """
    W = rec["width"]
    rimhw = W * RIM_W_FRAC * 0.5
    xf = rimhw - 0.0300 - (0.006 if rec["corner"] in ("RL", "RR") else 0.0)
    nt = 128 if fine else 72
    th = np.linspace(0, 2 * math.pi, nt, endpoint=False)
    dust = rec["dust"]

    # ---- barrel: a closed section, so the flange has a real edge ----------
    t_wall = 0.0058
    outer = [
        (-rimhw, FLANGE_R), (-rimhw + 0.0035, FLANGE_R + 0.0008),
        (-rimhw + 0.0090, BEAD_SEAT_R + 0.0012), (-rimhw + 0.0290, BEAD_SEAT_R),
        (-rimhw + 0.0430, 0.2090), (-rimhw + 0.0620, 0.2035),
        (0.0, 0.2020), (rimhw - 0.0620, 0.2035), (rimhw - 0.0430, 0.2090),
        (rimhw - 0.0290, BEAD_SEAT_R), (rimhw - 0.0090, BEAD_SEAT_R + 0.0012),
        (rimhw - 0.0035, FLANGE_R + 0.0008), (rimhw, FLANGE_R),
    ]
    outer = catmull(np.array(outer), per_seg=6)
    inner = outer[::-1].copy()
    inner[:, 1] -= t_wall
    inner[:, 0] *= 0.998
    loop = np.concatenate([outer, inner], axis=0)
    V, Q = revolve(loop, th, closed_loop=True)
    rr_ = np.linalg.norm(V[:, 1:], axis=1)
    zz = V[:, 2]
    acc.add(V, quads=Q, mat="Rim", tb_region=REGION_RIM,
            tb_dust=np.clip(dust * (0.45 + 0.55 * (1.0 - sstep(0.20, 0.24, rr_)))
                            * (0.6 + 0.4 * (1.0 - sstep(-0.2, 0.2, zz))), 0, 1))

    # ---- outer ring of the spider ----------------------------------------
    ring = catmull(np.array([
        (xf - 0.0060, 0.1960), (xf - 0.0075, 0.2010), (xf - 0.0060, 0.2065),
        (xf + 0.0055, 0.2065), (xf + 0.0072, 0.2010), (xf + 0.0055, 0.1960),
    ]), per_seg=5, closed=True)
    V, Q = revolve(ring, th, closed_loop=True)
    acc.add(V, quads=Q, mat="Rim", tb_region=REGION_RIM, tb_dust=dust * 0.8)

    # ---- ten spokes -------------------------------------------------------
    nsp = 10
    for k in range(nsp):
        ph0 = 2 * math.pi * k / nsp + rec["rim_phase"]
        n = 22
        t = np.linspace(0, 1, n)
        rr_ = 0.0960 + t * 0.1090
        ph = ph0 + 0.155 * (t ** 1.6)
        xx = xf - 0.0110 * np.sin(math.pi * t) ** 1.3
        Pp = np.stack([xx, rr_ * np.cos(ph), rr_ * np.sin(ph)], axis=1)
        up = np.stack([np.ones(n), np.zeros(n), np.zeros(n)], axis=1)
        hwid = 0.0175 - 0.0065 * t + 0.0030 * np.sin(math.pi * t)
        V, Q = sweep_ribbon(Pp, up, hwid, 0.0125 - 0.0035 * t)
        rrv = np.linalg.norm(V[:, 1:], axis=1)
        acc.add(V, quads=Q, mat="Rim", tb_region=REGION_RIM,
                tb_dust=np.clip(dust * (1.10 - 1.5 * (rrv - 0.10)), 0, 1))

    # ---- hub, centre-lock nut, retention clip ------------------------------
    hub = catmull(np.array([
        (xf - 0.0140, 0.0460), (xf - 0.0150, 0.1010), (xf + 0.0180, 0.1005),
        (xf + 0.0250, 0.0760), (xf + 0.0255, 0.0500), (xf + 0.0300, 0.0480),
        (xf + 0.0300, 0.0330), (xf - 0.0140, 0.0330),
    ]), per_seg=5, closed=True)
    V, Q = revolve(hub, th, closed_loop=True)
    acc.add(V, quads=Q, mat="Rim", tb_region=REGION_RIM, tb_dust=dust * 1.0)

    # the nut: a 12-point socket, so it has flats and it is not a cylinder
    npt = 12
    nutth = np.linspace(0, 2 * math.pi, npt * 6, endpoint=False)
    # 12-point drive.  0.055 of scallop read as a FLOWER at 240 px across in
    # the first render; a real 12-point socket is 1.4 % off round.
    flat = 1.0 - 0.016 * np.abs(np.cos(nutth * npt * 0.5)) ** 2.2
    nut_prof = np.array([
        (xf + 0.0300, 0.0340), (xf + 0.0300, 0.0472), (xf + 0.0348, 0.0472),
        (xf + 0.0505, 0.0455), (xf + 0.0520, 0.0400), (xf + 0.0520, 0.0250),
        (xf + 0.0470, 0.0215), (xf + 0.0300, 0.0215),
    ])
    nut_prof = catmull(nut_prof, per_seg=4, closed=True)
    ct, st = np.cos(nutth), np.sin(nutth)
    Xn = np.broadcast_to(nut_prof[None, :, 0], (len(nutth), len(nut_prof)))
    Rn = nut_prof[None, :, 1] * flat[:, None]
    Vn = np.stack([Xn, Rn * ct[:, None], Rn * st[:, None]],
                  axis=-1).reshape(-1, 3)
    Qn = grid_quads(len(nutth), len(nut_prof), wrap_c=True, wrap_r=True)
    acc.add(Vn, quads=Qn, mat="Rim", tb_region=REGION_RIM,
            tb_dust=dust * 0.55, tb_wear=0.45)

    # the spring retention clip: a 2.2 mm wire ring with a gap
    gap = 0.45
    cth = np.linspace(gap, 2 * math.pi - gap, 40)
    rc = 0.0510
    Pc = np.stack([np.full(40, xf + 0.0455), rc * np.cos(cth),
                   rc * np.sin(cth)], axis=1)
    Vc, Qc, Tc = sweep_tube(Pc, 0.0011, nside=8)
    acc.add(Vc, quads=Qc, tris=Tc, mat="Rim", tb_region=REGION_RIM,
            tb_dust=dust * 0.3, tb_wear=0.7)

    # ---- six drive pegs on the inboard face --------------------------------
    for k in range(6):
        ph = 2 * math.pi * k / 6 + 0.2
        rp = 0.0720
        n = 6
        t = np.linspace(0, 1, n)
        xx = -rimhw + 0.0330 - 0.0190 * t
        Pp = np.stack([xx, np.full(n, rp * math.cos(ph)),
                       np.full(n, rp * math.sin(ph))], axis=1)
        Vp, Qp, Tp = sweep_tube(Pp, 0.0060 - 0.0006 * t, nside=10)
        acc.add(Vp, quads=Qp, tris=Tp, mat="Rim", tb_region=REGION_RIM,
                tb_dust=dust * 0.9)

    # ---- valve stem --------------------------------------------------------
    phv = rec["rim_phase"] + 0.62
    rv = 0.1780
    n = 8
    t = np.linspace(0, 1, n)
    xx = xf + 0.0060 + 0.0230 * t
    rrv = rv + 0.0055 * t
    Pv = np.stack([xx, rrv * np.cos(phv), rrv * np.sin(phv)], axis=1)
    Vv, Qv, Tv = sweep_tube(Pv, np.linspace(0.0042, 0.0034, n), nside=10)
    acc.add(Vv, quads=Qv, tris=Tv, mat="Rim", tb_region=REGION_RIM,
            tb_dust=dust * 0.5)

    # ---- 2022-spec aero cover, on some wheels only -------------------------
    if rec["aero_cover"]:
        cov = catmull(np.array([
            (xf + 0.0180, 0.0500), (xf + 0.0225, 0.1100), (xf + 0.0232, 0.1700),
            (xf + 0.0195, 0.2020), (xf + 0.0120, 0.2085), (xf + 0.0085, 0.2060),
            (xf + 0.0140, 0.1700), (xf + 0.0150, 0.1100), (xf + 0.0110, 0.0520),
        ]), per_seg=5, closed=True)
        thc = np.linspace(0, 2 * math.pi, 160, endpoint=False)
        Vc, Qc = revolve(cov, thc, closed_loop=True)
        # a moulded fan of 14 shallow ribs, 1.6 mm proud: real geometry
        rrv = np.linalg.norm(Vc[:, 1:], axis=1)
        phv2 = np.arctan2(Vc[:, 2], Vc[:, 1])
        # 7 shallow scallops, 0.9 mm.  The first version ran 14 ribs at 1.6 mm
        # and the cover read as a turbine wheel at 240 px.
        rib = np.sin(7.0 * (phv2 + 0.9 * rrv)) * 0.5 + 0.5
        m = (Vc[:, 0] > xf + 0.016) & (rrv > 0.06) & (rrv < 0.198)
        Vc[m, 0] += (rib[m] ** 2) * 0.0009
        acc.add(Vc, quads=Qc, mat="Rim", tb_region=REGION_RIM,
                tb_dust=dust * 0.35, tb_wear=0.2)
        # its retaining ring and five quarter-turn fasteners: without them the
        # cover reads as a moulded hubcap, which is what the first render gave
        ring2 = catmull(np.array([
            (xf + 0.0170, 0.2010), (xf + 0.0205, 0.2062), (xf + 0.0175, 0.2098),
            (xf + 0.0125, 0.2092), (xf + 0.0108, 0.2040),
        ]), per_seg=4, closed=True)
        Vr, Qr = revolve(ring2, thc, closed_loop=True)
        acc.add(Vr, quads=Qr, mat="Rim", tb_region=REGION_RIM,
                tb_dust=dust * 0.5, tb_wear=0.45)
        for k in range(5):
            ph = 2 * math.pi * k / 5 + rec["rim_phase"] * 1.7
            rp = 0.1560
            t5 = np.linspace(0, 1, 5)
            Pp = np.stack([xf + 0.0215 + 0.0060 * t5,
                           np.full(5, rp * math.cos(ph)),
                           np.full(5, rp * math.sin(ph))], axis=1)
            Vp, Qp, Tp = sweep_tube(Pp, np.linspace(0.0070, 0.0055, 5),
                                    nside=10)
            acc.add(Vp, quads=Qp, tris=Tp, mat="Rim", tb_region=REGION_RIM,
                    tb_dust=dust * 0.4, tb_wear=0.6)


# ==============================================================================
#  7.  THE BLANKET
# ==============================================================================
# The whole object in one paragraph.  A quilted sheet of finite area is forced
# onto a torus of smaller developable area.  `conform_profile` is the surface it
# would take if it fitted, which it does not; every function after that is one
# of the ways the mismatch shows.  The mid-surface of the sheet is
#
#     mid(a, b) = conform(a, b) + N(a, b) * [ gap + T(a,b)/2 + quilt + slack
#                                             + pleat + crumple + gape - pull ]
#
# and the two shells are mid +- T/2, with T crushed to 3.8 mm at every stitch
# line and 13.2 mm between them.
#
# EVERYTHING IS BUILT IN THE WORLD-ORIENTED FRAME (origin at the wheel hub, axes
# parallel to world).  That is not a detail: gravity, the hanging branches and
# the floor are all defined there, so ONE model covers a wheel standing against
# the garage front, a wheel lying flat on the deck, and a blanket a mechanic has
# pulled half off.  If the fabric were draped in the wheel's own frame, a wheel
# lying flat would have its blanket hanging sideways.


def conform_profile(rec):
    """The surface the fabric would lie on if it fitted: tyre + 2 mm, closed off
    at both ends by the elastic hem where it tucks over the rim flange.

    -> dict(P (n,2) x,r | N (n,2) | s | reg | s_total | a_band0 | a_band1)
    """
    W = rec["width"]
    hw = W * 0.5
    Wb = hw + 0.0100                       # the band overhangs the tread
    tr = TYRE_R + BLK_GAP                  # 0.3620, the inner face on the crown
    P2, N2, s2, tag = tyre_section(W, rec["wear"])
    Pg = P2 + N2 * BLK_GAP

    # A BLANKET IS A DRUM, NOT A SHRINK-WRAP.  The first version offset the
    # tyre's own section by 2 mm all the way round, which produced a smooth
    # torus -- and a smooth torus is the "smooth cylinder" the manifest
    # forbids wearing a different hat.  A real blanket has a CYLINDRICAL tread
    # band, a hard bound corner at the shoulder, and flat-ish annular side
    # panels that BRIDGE the tyre's shoulder radius instead of following it.
    # That bridge is a 6-11 mm air gap and it is what gives the object its
    # square silhouette and its one crisp horizontal welt line.
    #
    # THE HEM IS STILL DERIVED FROM THE TYRE, not asserted at a radius: the
    # elastic pulls the last 3 mm of edge inboard over the rim flange, where it
    # grips, and everything below r = 0.300 follows the sidewall.
    half = Pg[len(Pg) // 2:]                                # x increasing
    low = half[(half[:, 1] <= 0.3000) & (half[:, 1] >= 0.2400)]
    if len(low) < 4:
        low = half[-8:]
    hem = low[-1] + np.array([-0.0022, -0.0028])
    top = np.array([
        [0.0000, tr + 0.0015],                              # a 1.5 mm crown
        [Wb * 0.55, tr + 0.0008],
        [Wb * 0.93, tr],
        [Wb, tr - 0.0020],                                  # the corner starts
        [Wb + 0.0035, tr - 0.0058],
        [Wb + 0.0030, tr - 0.0130],
        [Wb - 0.0010, tr - 0.0330],                         # off the shoulder
    ])
    ctrl_out = np.concatenate([top, low[::3], hem[None, :]], axis=0)
    mirr = ctrl_out[::-1].copy()
    mirr[:, 0] *= -1.0
    ctrl = np.concatenate([mirr[:-1], ctrl_out], axis=0)
    P = catmull(ctrl, per_seg=9)
    s = arclen(P)
    d = np.gradient(P, axis=0)
    N = unit(np.stack([-d[:, 1], d[:, 0]], axis=1))
    r = P[:, 1]
    reg = np.where(r < 0.2640, 0.0, np.where(r < 0.3350, 1.0,
                   np.where(r < tr - 0.0050, 2.0, 3.0)))
    band = np.where(reg >= 2.5)[0]
    return dict(P=P, N=N, s=s, reg=reg, s_total=float(s[-1]),
                a_band0=float(s[band[0]]), a_band1=float(s[band[-1]]))


def quilt_plan(rec, cp):
    """Where the stitching runs.  Three generations of blanket, three patterns.

    Pitch is 74-96 mm because that is what holds 12 mm of needled silica batting
    without it migrating, and it is also -- at 2.101 mm/px -- 35 to 46 px, which
    makes the quilt the loudest geometric rhythm on the object.
    """
    A = cp["s_total"]
    pitch = rr(0.074, 0.096, rec["uid"], "qp")
    n = max(4, int(round((A - 0.055) / pitch)))
    pitch = (A - 0.055) / n
    lines = 0.0275 + pitch * np.arange(n + 1)
    lines = lines + np.array([rr(-0.004, 0.004, rec["uid"], "qj", k)
                              for k in range(n + 1)])
    lines = np.clip(lines, 0.020, A - 0.020)
    cross = []
    if rec["gen"] == 1:
        cross = [dict(kind="side", n=12, phase=rr(0, 0.5, rec["uid"], "qx"))]
    elif rec["gen"] == 2:
        m = int(round(2 * math.pi * TYRE_R / rr(0.135, 0.175, rec["uid"], "qd")))
        cross = [dict(kind="all", n=m, phase=rr(0, 1.0, rec["uid"], "qx"))]
    return dict(lines=lines, pitch=pitch, cross=cross, gen=rec["gen"])


def blanket_rows(rec, cp, qp, lod):
    """Row positions across the section: ~2 mm at every stitch valley, hem and
    welt, 5.5-7 mm on the flats.  This is where the mesh budget is SPENT."""
    A = cp["s_total"]
    base = (0.0055, 0.0080, 0.0125)[lod]
    fine = (0.0019, 0.0027, 0.0044)[lod]
    ref = [(float(x) - 0.008, float(x) + 0.008, fine) for x in qp["lines"]]
    ref += [(0.0, 0.048, fine * 1.25), (A - 0.048, A, fine * 1.25)]
    ref += [(cp["a_band0"] - 0.014, cp["a_band0"] + 0.014, fine),
            (cp["a_band1"] - 0.014, cp["a_band1"] + 0.014, fine)]
    return adaptive_axis(0.0, A, base, ref)


def blanket_cols(rec, qp, lod):
    """Column positions round the wrap, in metres of arc at the tread radius.

    b in [0, L] is the layer that goes on first; b in [L, L + 0.09] is the flap
    that closes over it.  Two thicknesses of cloth, a 14 mm step, a shadow line
    all the way down the section, and the gape at b = L + 0.09.
    """
    R = TYRE_R + BLK_GAP + BLK_T * 0.5
    L = 2.0 * math.pi * R
    tot = L + OVERLAP_M
    base = (0.0055, 0.0082, 0.0135)[lod]
    fine = (0.0020, 0.0029, 0.0047)[lod]
    ref = [(0.0, 0.038, fine), (L - 0.022, tot, fine)]
    for st in rec["straps"]:
        ref.append((st["b_buckle"] - 0.075, st["b_buckle"] + 0.075, fine * 1.2))
    if qp["cross"]:
        cx = qp["cross"][0]
        for k in range(cx["n"]):
            b = tot * ((k + cx["phase"]) / cx["n"])
            ref.append((b - 0.008, b + 0.008, fine))
    return adaptive_axis(0.0, tot, base, ref), L, tot, R


def pleat_field(rec, th, key, n_pleats, width, amp):
    """Irregular radial gathers -- the signature of an elasticated hem.

    A gathered hem does not produce a sine wave.  It produces n discrete tucks
    at irregular spacing with irregular amplitude, and the irregularity is the
    whole read: an evenly-pleated hem looks turned on a lathe.
    """
    out = np.zeros_like(th)
    for j in range(n_pleats):
        c = 2 * math.pi * (j + rr(-0.34, 0.34, rec["uid"], key, j)) / n_pleats
        a = amp * rr(0.45, 1.35, rec["uid"], key, "a", j)
        w = width * rr(0.70, 1.45, rec["uid"], key, "w", j)
        d = ((th - c + math.pi) % (2 * math.pi)) - math.pi
        out = out + a * np.exp(-(d * TYRE_R / w) ** 2)
    return out


def hang_branch(rec, rows_s, b_vals, b0, prof_xr, R, theta0, Rot, axis_w,
                sense=+1.0, z_floor=None):
    """Where the sheet has left the tyre.

    It leaves tangentially, bends toward the ground at a rate set by the quilt's
    own stiffness (a 13 mm silica sandwich does not fall like a bedsheet: it
    holds a 0.28-0.48 m radius), flattens as it goes because nothing is holding
    it round the tyre any more, and when it reaches the floor it lies on it and
    wanders.

    ARC LENGTH IS CONSERVED IN BOTH DIRECTIONS.  The flattening is done by
    scaling the section's turning angle and re-integrating it, not by scaling
    the section -- so the hanging part is the same piece of cloth as the wrapped
    part, carries the same quilt at the same pitch, and meets it without a step.

    Everything here is in the WORLD-ORIENTED frame.  -> (P, N) each (nr, nb, 3).
    """
    nr, nb = len(rows_s), len(b_vals)
    sigma = np.abs(b_vals - b0)
    imid = int(np.argmin(np.abs(rows_s - rows_s[-1] * 0.5)))
    x0, r0 = prof_xr[imid]
    th0 = b0 / R + theta0
    p0 = Rot @ np.array([x0, r0 * math.cos(th0), r0 * math.sin(th0)])
    t0 = Rot @ (np.array([0.0, -math.sin(th0), math.cos(th0)]) * sense)
    dn = np.array([0.0, 0.0, -1.0])
    stiff = rec["hang_stiff"]
    P = np.zeros((nb, 3)); T = np.zeros((nb, 3))
    p, t = p0.copy(), t0.copy()
    for j in range(nb):
        if j:
            ds = float(sigma[j] - sigma[j - 1])
            perp = dn - t * float(np.dot(dn, t))
            npn = np.linalg.norm(perp)
            if npn > 1e-9:
                t = t + (perp / npn) * (ds / max(stiff, 1e-3))
                t = t / np.linalg.norm(t)
            p = p + t * ds
            if z_floor is not None and p[2] < z_floor:
                p[2] = z_floor
                if t[2] < 0.0:
                    t[2] = 0.0
                    nn = np.linalg.norm(t)
                    t = t / nn if nn > 1e-9 else np.array([0.0, 1.0, 0.0])
                    w = math.sin(5.5 * sigma[j] + rec["pool_phase"])
                    t = t + np.cross(t, np.array([0.0, 0.0, 1.0])) * w * 0.12
                    t = t / np.linalg.norm(t)
        P[j] = p; T[j] = t
    d = np.gradient(prof_xr, axis=0)
    psi = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    psi = psi - psi[imid]
    da = np.gradient(rows_s)
    k = np.exp(-sigma / max(rec["hang_flat"], 1e-3))[None, :]
    ps = psi[:, None] * k
    ex = np.cumsum(np.cos(ps) * da[:, None], axis=0)
    ey = np.cumsum(np.sin(ps) * da[:, None], axis=0)
    ex = ex - ex[imid][None, :]
    ey = ey - ey[imid][None, :]
    U = np.zeros((nb, 3)); S = np.zeros((nb, 3))
    radial0 = p0 - axis_w * float(np.dot(p0, axis_w))
    radial0 = radial0 / max(np.linalg.norm(radial0), 1e-9)
    for j in range(nb):
        s_ = axis_w - T[j] * float(np.dot(axis_w, T[j]))
        ns = np.linalg.norm(s_)
        S[j] = s_ / ns if ns > 1e-9 else axis_w
        U[j] = np.cross(T[j], S[j])
        if float(np.dot(U[j], radial0)) < 0.0:
            U[j] = -U[j]; S[j] = -S[j]
    Pg = (P[None, :, :] + S[None, :, :] * ex[:, :, None]
          + U[None, :, :] * ey[:, :, None])
    drop = (np.abs(ex) ** 1.7) * (1.0 - np.exp(-sigma[None, :] / 0.22)) * 0.62
    Pg[:, :, 2] -= drop
    if z_floor is not None:
        below = Pg[:, :, 2] < z_floor
        Pg[:, :, 2] = np.where(below, z_floor - 0.0016 * np.abs(
            np.sin(ex * 34.0 + sigma[None, :] * 11.0)), Pg[:, :, 2])
    Ng = unit(np.cross(np.gradient(Pg, axis=1), np.gradient(Pg, axis=0)))
    ref = U[None, :, :] * np.ones((nr, 1, 1))
    flip = np.sum(Ng * ref, axis=2) < 0
    Ng[flip] *= -1.0
    return Pg, Ng


def blanket_surface(rec, lod, Rot, z_floor_hint=None):
    """Mid-surface, both shells, and every field baked onto them.  (nr, nb)."""
    cp = conform_profile(rec)
    qp = quilt_plan(rec, cp)
    rows_s = blanket_rows(rec, cp, qp, lod)
    cols_b, L, tot, R = blanket_cols(rec, qp, lod)
    nr, nb = len(rows_s), len(cols_b)
    # BOTH resampled against the POSITION curve's arc length.  See resample_at.
    prof = resample_at(cp["P"], rows_s, s=cp["s"])
    profN = unit(resample_at(cp["N"], rows_s, s=cp["s"]))
    reg = np.interp(rows_s, cp["s"], cp["reg"])
    A = cp["s_total"]
    theta0 = rec["theta0"]

    AA = np.broadcast_to(rows_s[:, None], (nr, nb)).copy()
    BB = np.broadcast_to(cols_b[None, :], (nr, nb)).copy()
    TH = BB / R + theta0

    # ------------------------------------------------------------------ quilt
    dl = np.min(np.abs(AA[:, :, None] - qp["lines"][None, None, :]), axis=2)
    if qp["cross"]:
        cx = qp["cross"][0]
        per = tot / cx["n"]
        db = np.abs(((BB / per + cx["phase"] + 0.5) % 1.0) - 0.5) * per
        if cx["kind"] == "side":
            db = np.where(reg[:, None] <= 1.5, db, 1e3)
        dl = np.minimum(dl, db)
    puff = sstep(0.0, 0.0235, dl) ** 0.72
    Tth = BLK_T_STITCH + (BLK_T - BLK_T_STITCH) * puff
    quilt_rise = 0.0026 * puff + 0.0009 * puff ** 3

    # ------------------------------------------------------- straps and pull
    pull = np.zeros((nr, nb))
    for st in rec["straps"]:
        pull += 0.0052 * np.exp(-((AA - st["a"]) / 0.030) ** 2)

    # ------------------------------------------------- slack: the actual bulge
    band_m = (sstep(cp["a_band0"] - 0.02, cp["a_band0"] + 0.03, AA)
              * (1.0 - sstep(cp["a_band1"] - 0.03, cp["a_band1"] + 0.02, AA)))
    slack = rec["slack"] * band_m * (1.0 - np.clip(pull / 0.0052, 0, 1)) * 0.0125
    lobes = np.zeros((nr, nb))
    for m in range(2, 7):
        lobes += (rr(0.4, 1.0, rec["uid"], "lob", m) / m) * \
            np.sin(m * TH + rr(0.0, 6.283, rec["uid"], "lop", m))
    slack = slack + lobes * rec["slack"] * 0.0042 * (0.35 + 0.65 * band_m)

    # ----------------------------------------------- the gathered hem pleats
    ple = np.zeros((nr, nb))
    for side, key in ((0, "hemA"), (1, "hemB")):
        n_pl = int(rr(22, 34, rec["uid"], key, "n"))
        f = pleat_field(rec, TH[0], key, n_pl, 0.0135, 1.0)
        dist = np.abs(AA if side == 0 else (A - AA))
        ple += f[None, :] * np.exp(-(dist / 0.062) ** 1.5) * rec["hem_amp"]
    ripple = (pleat_field(rec, TH[0], "ripple", 16, 0.030, 1.0)[None, :]
              * np.clip(1.0 - np.abs(reg[:, None] - 1.0) / 0.9, 0, 1) * 0.0030)

    # -------------------------------------------------------------- crumple
    crum = (fbm2(BB / 0.085, AA / 0.045, seed=int(rec["uid"]) * 13 + 1,
                 octaves=4) - 0.5) * 0.0052 * rec["crumple"]
    crum = crum + (fbm2(BB / 0.021, AA / 0.016, seed=int(rec["uid"]) * 29 + 7,
                        octaves=2) - 0.5) * 0.0021
    # a 13 mm quilted sandwich creases where it has been folded and stacked:
    # long, shallow, sharp-bottomed, and NOT the same statistic as the crumple
    crease = np.abs(fbm2(BB / 0.190 + 3.1, AA / 0.075,
                         seed=int(rec["uid"]) * 41 + 9, octaves=2) - 0.5)
    crum = crum - np.clip(1.0 - crease / 0.10, 0.0, 1.0) ** 2 * 0.0031

    # -------------------------------------------------- the closure and gape
    over = sstep(L - 0.006, L + 0.006, BB)
    lift = over * (BLK_T + 0.0016)
    # THE GAPE IS A TREAD-BAND EVENT.  It opens where the closure is only held
    # by hook tape; on the side panels the ELASTIC HEM is still round the rim
    # flange and holds the free edge down whatever the closure is doing.  The
    # first version let the gape act on the whole section, which flared the
    # free edge 70 mm outboard on both side panels and took the measured axial
    # width of a 305 mm front from 0.372 m to 0.460 m -- a blanket 55 mm wider
    # at the seam than anywhere else, which is not a thing.
    gape = (rec["gape"] * sstep(L + OVERLAP_M * 0.30, tot, BB) ** 1.6
            * (0.22 + 0.78 * band_m))
    press = -0.0016 * (1.0 - sstep(0.0, 0.030, BB))

    hmid = (BLK_GAP + Tth * 0.5 + quilt_rise + slack + ple + ripple + crum
            + lift + gape + press - pull)

    # ---------------------------------------------------------- burn-through
    scorch = np.zeros((nr, nb))
    burn = np.zeros((nr, nb))
    for k, s in enumerate(rec["scorch"]):
        db_ = np.abs(((BB - s["b"] + tot * 0.5) % tot) - tot * 0.5)
        d = np.hypot(db_, AA - s["a"])
        edge = s["r"] * (1.0 + 0.28 * (fbm2(BB / 0.02 + k * 9.0, AA / 0.02,
                                            seed=int(rec["uid"]) * 3 + k,
                                            octaves=2) - 0.5) * 2.0)
        scorch = np.maximum(scorch,
                            np.clip(1.0 - d / (edge * 2.3), 0, 1) ** 1.4
                            * s["deep"])
        if s["through"]:
            burn = np.maximum(burn, sstep(0.0, 0.25,
                                          np.clip(1.0 - d / edge, 0, 1)))
            hmid = hmid + np.exp(-((d - edge) / 0.0045) ** 2) * 0.0021

    # -------------------------------------- the conform surface, world-oriented
    ct, st_ = np.cos(TH), np.sin(TH)
    Pl = np.stack([np.broadcast_to(prof[:, 0][:, None], (nr, nb)),
                   prof[:, 1][:, None] * ct,
                   prof[:, 1][:, None] * st_], axis=-1)
    Nl = np.stack([np.broadcast_to(profN[:, 0][:, None], (nr, nb)),
                   profN[:, 1][:, None] * ct,
                   profN[:, 1][:, None] * st_], axis=-1)
    Pc = Pl @ Rot.T
    Nc = unit(Nl @ Rot.T)

    # the floor, in this frame: the deepest point of the attached shell, plus
    # the 20 mm every object on the ground owes world_contract (law 5).
    PO_att = Pc + Nc * (hmid + Tth * 0.5)[:, :, None]
    z_low = float(PO_att[:, :, 2].min())
    z_floor = z_low + BASE_EMBED if z_floor_hint is None else z_floor_hint

    # ------------------------------------------------- detachment / hanging
    axis_w = Rot @ np.array([1.0, 0.0, 0.0])
    det = np.zeros(nb, bool)
    if rec["peel_hi"] is not None:
        j = int(np.searchsorted(cols_b, rec["peel_hi"]))
        if j < nb - 1:
            det[j:] = True
            Ph, Nh = hang_branch(rec, rows_s, cols_b[j:], cols_b[j], prof, R,
                                 theta0, Rot, axis_w, +1.0, z_floor)
            Pc[:, j:, :] = Ph
            Nc[:, j:, :] = Nh
    if rec["peel_lo"] is not None:
        j = int(np.searchsorted(cols_b, rec["peel_lo"]))
        if j > 1:
            det[:j] = True
            Pl2, Nl2 = hang_branch(rec, rows_s, cols_b[:j][::-1], cols_b[j],
                                   prof, R, theta0, Rot, axis_w, -1.0, z_floor)
            Pc[:, :j, :] = Pl2[:, ::-1, :]
            Nc[:, :j, :] = Nl2[:, ::-1, :]

    dm = det[None, :].astype(float)
    hmid = hmid * (1.0 - dm) + (Tth * 0.5 + quilt_rise + crum * 1.7) * dm

    PO = Pc + Nc * (hmid + Tth * 0.5)[:, :, None]
    inner_h = np.where(det[None, :], hmid - Tth * 0.5,
                       np.maximum(hmid - Tth * 0.5, 0.0006))
    PI = Pc + Nc * inner_h[:, :, None]
    if burn.max() > 0.0:
        f = burn[:, :, None]
        PO = PO * (1.0 - f) + (PI + Nc * 0.0022) * f

    # the bottom of a blanket is CRUSHED between the tyre and the deck, and it
    # splays sideways as it goes; without this it reads as a tangent circle
    dep = np.clip(z_floor - PO[:, :, 2], 0.0, 1.0)
    spread = np.clip(np.abs((PO - 0.0) @ axis_w) / (rec["width"] * 0.5), 0, 1)
    if abs(float(axis_w[2])) < 0.55:
        PO = PO + axis_w[None, None, :] * (
            np.sign((PO @ axis_w))[:, :, None] * (dep * spread * 0.85)[:, :, None])
        PI = PI + axis_w[None, None, :] * (
            np.sign((PI @ axis_w))[:, :, None] * (dep * spread * 0.60)[:, :, None])

    return dict(cp=cp, qp=qp, rows=rows_s, cols=cols_b, L=L, tot=tot, R=R,
                PO=PO, PI=PI, N=Nc, hmid=hmid, T=Tth, puff=puff, dl=dl,
                reg=reg, AA=AA, BB=BB, TH=TH, det=det, scorch=scorch,
                burn=burn, prof=prof, profN=profN, band_m=band_m,
                z_floor=z_floor, theta0=theta0)


def print_sdf(rec, srf):
    """Signed distance, in metres, to everything printed on this blanket.

    Two charts, both in the fabric's OWN material coordinates so the artwork
    rides the wrinkles instead of sliding over them: (arc, axial) on the tread
    band and (arc, radius) on the side panels.
    """
    AA, BB = srf["AA"], srf["BB"]
    cp = srf["cp"]
    A = cp["s_total"]
    tot = srf["tot"]
    out = np.full(AA.shape, 1.0)
    name = rec["brand"][0]
    strap = rec["brand"][6]
    ab = (cp["a_band0"] + cp["a_band1"]) * 0.5
    cap = 0.055
    segs, w, hwid = text_segments(name, cap, tracking=rec["brand"][5],
                                  weight=0.20)
    segs2, w2, hw2 = text_segments(strap, 0.020, tracking=0.24, weight=0.22)
    for k in range(rec["print_n"]):
        b0 = tot * (k + rec["print_phase"]) / rec["print_n"]
        ba = ((BB - b0 + tot * 0.5) % tot) - tot * 0.5
        out = np.minimum(out, seg_sdf(ba + w * 0.5, AA - (ab - cap * 0.5),
                                      segs, hwid))
        out = np.minimum(out, seg_sdf(ba + w2 * 0.5, AA - (ab + cap * 0.62),
                                      segs2, hw2))
    segs3, w3, hw3 = text_segments(name, 0.034, tracking=rec["brand"][5],
                                   weight=0.21)
    segs4, w4, hw4 = text_segments(rec["corner"], 0.030, tracking=0.20,
                                   weight=0.24)
    # THE RADIUS THE FABRIC IS ACTUALLY AT, per row, straight off the conform
    # profile.  The first version used a linear guess (HEM_R + a * 0.88) which
    # was 20 mm out by the top of the side panel and put the wordmark on a
    # sloping baseline.
    r_chart = np.broadcast_to(srf["prof"][:, 1][:, None], AA.shape)
    reg = np.broadcast_to(srf["reg"][:, None], AA.shape)
    for side in (0, 1):
        # +X is OUTBOARD, so a viewer on the outboard side sees +Y on his LEFT
        # and increasing theta running left -> up -> right, i.e. CLOCKWISE.
        # Type set along increasing theta therefore reads BACKWARDS from the
        # only side the lens ever looks at.  Measured in the first render:
        # "CIRRUS" came out as "SURRIC".  The arc direction is flipped per side.
        sgn = +1.0 if side == 0 else -1.0
        near_hem = (AA if side == 0 else (A - AA))
        m = (reg > 0.5) & (reg < 1.5) & (near_hem < A * 0.5)
        arc = (((sgn * (srf["TH"] - rec["side_phi"]) + math.pi)
                % (2 * math.pi)) - math.pi) * 0.30
        d = seg_sdf(arc + w3 * 0.5, r_chart - 0.2810, segs3, hw3)
        out = np.where(m, np.minimum(out, d), out)
        arc2 = (((sgn * (srf["TH"] - rec["side_phi"] - 2.4) + math.pi)
                 % (2 * math.pi)) - math.pi) * 0.28
        d2 = seg_sdf(arc2 + w4 * 0.5, r_chart - 0.3130, segs4, hw4)
        out = np.where(m, np.minimum(out, d2), out)
    return out


def blanket_mesh(acc, rec, srf):
    """Turn the two shells into a closed, bound, quilted piece of cloth."""
    PO, PI, N = srf["PO"], srf["PI"], srf["N"]
    nr, nb = PO.shape[0], PO.shape[1]

    def bead(e, f, d, nseg=3):
        mid = 0.5 * (e + f)
        rad = (0.5 * np.linalg.norm(e - f, axis=-1))[:, None]
        arm = e - mid
        return [mid + arm * math.cos(math.pi * k / (nseg + 1))
                + d * (rad * math.sin(math.pi * k / (nseg + 1)))
                for k in range(1, nseg + 1)]

    dA = unit(PO[-1] - PO[-2])
    d0 = unit(PO[0] - PO[1])
    parts = ([PO[i] for i in range(nr)] + bead(PO[-1], PI[-1], dA)
             + [PI[i] for i in range(nr - 1, -1, -1)] + bead(PI[0], PO[0], d0))
    Lp = len(parts)
    Ring = np.stack(parts, axis=1)                        # (nb, Lp, 3)

    # ---- THE TWO FREE EDGES OF THE WRAP ARE BOUND, NOT CAPPED -------------
    # First version closed b = 0 and b = tot with a triangle fan to the ring's
    # centroid.  That is a LID: a flat plate spanning the whole 0.54 m section,
    # 34 mm inside the tyre, right at the closure -- exactly where the gape is
    # supposed to show the tyre through.  It was found by the "no fabric inside
    # the tyre" check and it would have been found by the eye a render later.
    #
    # What a real blanket has there is a bound edge: the two shells fold to meet
    # and the tape wraps round them.  So the cross-section ring is swept a
    # quarter turn about its own mid-surface line, with a bead radius equal to
    # the LOCAL half-thickness, and closes onto that line.  Watertight, 4 mm of
    # rolled edge, and nothing spans the opening.
    mid_seq = ([0.5 * (PO[i] + PI[i]) for i in range(nr)]
               + [0.5 * (PO[-1] + PI[-1])] * 3
               + [0.5 * (PO[i] + PI[i]) for i in range(nr - 1, -1, -1)]
               + [0.5 * (PO[0] + PI[0])] * 3)
    Mid = np.stack(mid_seq, axis=1)                       # (nb, Lp, 3)
    Arm = Ring - Mid
    Amag = np.linalg.norm(Arm, axis=2, keepdims=True)
    NCAP = 4
    ang = np.linspace(0.0, math.pi * 0.5, NCAP + 1)[1:]
    capS, capE = [], []
    dB0 = unit(Ring[0] - Ring[1])
    dB1 = unit(Ring[-1] - Ring[-2])
    for th in ang:
        capS.append(Mid[0] + Arm[0] * math.cos(th)
                    + dB0 * (Amag[0] * math.sin(th)))
        capE.append(Mid[-1] + Arm[-1] * math.cos(th)
                    + dB1 * (Amag[-1] * math.sin(th)))
    V3 = np.concatenate([np.stack(capS[::-1], axis=0), Ring,
                         np.stack(capE, axis=0)], axis=0)
    nbf = V3.shape[0]
    V = V3.reshape(-1, 3)
    Q = grid_quads(nbf, Lp, wrap_c=True, wrap_r=False)

    def col(field):
        f = np.asarray(field)
        if f.ndim == 1:
            f = np.broadcast_to(f[:, None], (nr, nb))
        a, z = f[-1], f[0]
        seq = ([f[i] for i in range(nr)] + [a, a, a]
               + [f[i] for i in range(nr - 1, -1, -1)] + [z, z, z])
        g = np.stack(seq, axis=1)                          # (nb, Lp)
        return np.concatenate([np.repeat(g[:1], NCAP, axis=0), g,
                               np.repeat(g[-1:], NCAP, axis=0)],
                              axis=0).ravel()

    prt = print_sdf(rec, srf)
    face = np.concatenate([np.ones(nr), np.full(3, 0.5), np.zeros(nr),
                           np.full(3, 0.5)])
    face = np.broadcast_to(face[None, :], (nbf, Lp)).ravel()
    cav = cavity_from_height(srf["hmid"])
    reg2 = np.where(srf["reg"] < 0.5, REGION_HEM,
                    np.where(srf["reg"] < 1.5, REGION_SIDEPANEL, REGION_SHELL))
    wear = np.clip(rec["age"] * (0.35 + 0.85 * cav)
                   + 0.5 * srf["puff"] * rec["age"], 0, 1)
    grime = np.clip(rec["dirt"] * (0.30 + 0.9 * cav) + 0.25 * rec["dirt"], 0, 1)

    qm = np.full(len(Q), MAT_INDEX["Shell"], np.int32)
    if srf["burn"].max() > 0.5:
        # face centres in the SAME order grid_quads emits: rows are the wrap
        # columns (open), cols are the section loop (closed), row-major.
        bf = col(srf["burn"]).reshape(nbf, Lp)
        bfr = np.roll(bf, -1, axis=1)
        cen = 0.25 * (bf[:-1] + bfr[:-1] + bf[1:] + bfr[1:])
        qm = np.where(cen.ravel() > 0.55, MAT_INDEX["Batting"], qm)

    acc.add(V, quads=Q, qmat=qm,
            tb_print=col(prt), tb_region=col(reg2), tb_quilt=col(srf["puff"]),
            tb_scorch=col(srf["scorch"]), tb_wear=col(wear),
            tb_grime=col(grime), tb_cav=col(cav),
            tb_seam=col(np.minimum(srf["dl"], 0.25)), tb_face=face,
            tb_u=col(srf["BB"]), tb_v=col(srf["AA"]))


def binding_and_closure(acc, rec, srf):
    """Bound edges, the hook-and-loop closure, and the two shoulder welts.

    A blanket's edges are BOUND -- 18 mm tape folded over and twice stitched.
    3.2 mm proud is 1.5 px, and it is the line that separates one panel from the
    next all the way round the object.
    """
    PO, PI, N = srf["PO"], srf["PI"], srf["N"]
    nr, nb = PO.shape[0], PO.shape[1]
    cols = srf["cols"]

    for i in (0, nr - 1):
        P = 0.5 * (PO[i] + PI[i]) + N[i] * 0.0006
        V, Q = sweep_ribbon(P, N[i], BINDING_W * 0.45, BINDING_H)
        acc.add(V, quads=Q, mat="Binding", tb_region=REGION_BINDING,
                tb_wear=float(np.clip(rec["age"] * 1.25, 0, 1)),
                tb_grime=float(np.clip(rec["dirt"] * 1.1, 0, 1)), tb_seam=0.0)

    for a_seam in (srf["cp"]["a_band0"], srf["cp"]["a_band1"]):
        i = int(np.argmin(np.abs(srf["rows"] - a_seam)))
        V, Q = sweep_ribbon(PO[i] + N[i] * 0.0009, N[i], 0.0075, 0.0026)
        acc.add(V, quads=Q, mat="Binding", tb_region=REGION_BINDING,
                tb_wear=float(np.clip(rec["age"] * 0.9, 0, 1)),
                tb_grime=float(rec["dirt"]), tb_seam=0.0)

    step = max(1, (nr - 6) // 70)
    rows = np.arange(3, nr - 3, step)
    j1 = int(np.searchsorted(cols, OVERLAP_M * 0.92))
    if j1 > 3:
        Pl = PO[rows][:, :j1] + N[rows][:, :j1] * 0.0011
        acc.add(Pl.reshape(-1, 3), quads=grid_quads(len(rows), j1),
                mat="Velcro", tb_region=REGION_BINDING, tb_face=1.0,
                tb_wear=float(np.clip(rec["age"] * 1.4, 0, 1)))
    k0 = int(np.searchsorted(cols, srf["L"] + 0.004))
    if k0 < nb - 3:
        Ph = PI[rows][:, k0:] - N[rows][:, k0:] * 0.0011
        acc.add(Ph.reshape(-1, 3),
                quads=grid_quads(len(rows), nb - k0)[:, ::-1], mat="Velcro",
                tb_region=REGION_BINDING, tb_face=0.0,
                tb_wear=float(np.clip(rec["age"] * 1.4, 0, 1)))


def surf_at(srf, a, b, use="PO"):
    """Bilinear sample of the finished shell at fabric coordinates (a, b)."""
    rows, cols = srf["rows"], srf["cols"]
    G, Ng = srf[use], srf["N"]
    a = np.asarray(a, float); b = np.asarray(b, float)
    ia = np.clip(np.searchsorted(rows, a) - 1, 0, len(rows) - 2)
    fa = ((a - rows[ia]) / (rows[ia + 1] - rows[ia]))[..., None]
    ib = np.clip(np.searchsorted(cols, b) - 1, 0, len(cols) - 2)
    fb = ((b - cols[ib]) / (cols[ib + 1] - cols[ib]))[..., None]

    def bl(M):
        return ((M[ia, ib] * (1 - fa) + M[ia + 1, ib] * fa) * (1 - fb)
                + (M[ia, ib + 1] * (1 - fa) + M[ia + 1, ib + 1] * fa) * fb)
    return bl(G), unit(bl(Ng))


# ------------------------------------------------------------------- straps

def strap_and_buckle(acc, rec, srf):
    """38 mm webbing round the band, a moulded side-release buckle on each, and
    a tail that is either dressed under the keeper or hanging.

    The strap is what makes the bulge legible: it pins the fabric at three
    stations so the cloth between them has somewhere to go.  Its own geometry
    is the buckle -- 46 x 26 x 12 mm, 22 x 12 px at the tight lens, so its
    ribs, its window and its release arms are all mesh.
    """
    tot = srf["tot"]
    for si, st in enumerate(rec["straps"]):
        b0, b1 = 0.030, tot - 0.030
        n = max(60, int((b1 - b0) / 0.010))
        bb = np.linspace(b0, b1, n)
        aa = np.full(n, st["a"])
        P, N = surf_at(srf, aa, bb)
        # the buckle sits proud of the surface and the strap ramps up to it
        db = np.abs(bb - st["b_buckle"])
        raise_ = np.exp(-(db / 0.055) ** 2) * 0.0115
        P = P + N * (STRAP_T * 0.5 + 0.0007 + raise_[:, None])
        keep = db > 0.026
        V, Q = sweep_ribbon(P[keep], N[keep], STRAP_W * 0.5, STRAP_T)
        acc.add(V, quads=Q, mat="Webbing", tb_region=REGION_STRAP,
                tb_wear=np.clip(rec["age"] * 1.15 + 0.15, 0, 1),
                tb_grime=np.clip(rec["dirt"] * 1.2, 0, 1), tb_seam=0.0)

        # ---- the buckle ---------------------------------------------------
        i = int(np.argmin(db))
        o = P[i]
        t = unit(P[min(i + 2, n - 1)] - P[max(i - 2, 0)])
        u = N[i]
        s = unit(np.cross(t, u))
        u = unit(np.cross(s, t))
        M = np.stack([t, s, u], axis=1)

        def place(Vl):
            return Vl @ M.T + o

        body, bq = rounded_box((BUCKLE_L, BUCKLE_W, BUCKLE_H), radius=0.0018,
                               centre=(0, 0, 0))
        acc.add(place(body), quads=bq, mat="Buckle", tb_region=REGION_BUCKLE,
                tb_wear=np.clip(0.25 + rec["age"], 0, 1), tb_grime=rec["dirt"])
        # the window the male prong shows through
        win, wq = rounded_box((0.0150, 0.0130, 0.0030), radius=0.0009,
                              centre=(-0.0055, 0.0, BUCKLE_H * 0.42))
        acc.add(place(win), quads=wq, mat="Buckle", tb_region=REGION_BUCKLE,
                tb_wear=0.5)
        # the two release arms
        for sgn in (-1.0, 1.0):
            arm, aq = rounded_box((0.0180, 0.0035, 0.0085), radius=0.0012,
                                  centre=(0.0075, sgn * (BUCKLE_W * 0.5 + 0.0011),
                                          0.0))
            acc.add(place(arm), quads=aq, mat="Buckle",
                    tb_region=REGION_BUCKLE, tb_wear=0.6)
        # the grip ribs -- 2.5 mm pitch, 1.2 px, and they catch the low sun
        for k in range(6):
            rib, rq = rounded_box((0.0016, 0.0180, 0.0016), radius=0.0006,
                                  centre=(0.0130 + k * 0.0026, 0.0,
                                          BUCKLE_H * 0.5 - 0.0004))
            acc.add(place(rib), quads=rq, mat="Buckle",
                    tb_region=REGION_BUCKLE, tb_wear=0.75)
        # the webbing bar at the fixed end
        bar, brq = rounded_box((0.0032, 0.0210, 0.0032), radius=0.0014,
                               centre=(-BUCKLE_L * 0.5 + 0.0030, 0.0, 0.0))
        acc.add(place(bar), quads=brq, mat="Buckle", tb_region=REGION_BUCKLE)

        # ---- the tail -----------------------------------------------------
        Ltail = st["tail"]
        m = max(10, int(Ltail / 0.010))
        tt = np.linspace(0, 1, m)
        if st["dangle"]:
            # it hangs, and a 38 mm webbing tail curls as it goes
            down = np.asarray(rec["_down"], float)
            dirv = unit(t * 0.35 + down * 1.0)
            curl = np.sin(tt * 3.4 + st["phase"]) * 0.030 * tt
            Pt = (o + u * 0.0090)[None, :] + dirv[None, :] * (tt * Ltail)[:, None] \
                + s[None, :] * curl[:, None] \
                + t[None, :] * (0.045 * np.sin(tt * 2.1) * tt)[:, None]
            Pt = lay_on_floor(Pt, rec["_zfloor"] + 0.0015, 0.30, st["phase"])
            up = np.broadcast_to(s, (m, 3))
        else:
            bt = st["b_buckle"] + 0.030 + tt * Ltail
            bt = np.clip(bt, 0.031, tot - 0.031)
            Pt0, Nt = surf_at(srf, np.full(m, st["a"]), bt)
            Pt = Pt0 + Nt * (STRAP_T * 1.7 + 0.0010)
            up = Nt
        V, Q = sweep_ribbon(Pt, up, STRAP_W * 0.5, STRAP_T * 0.85)
        acc.add(V, quads=Q, mat="Webbing", tb_region=REGION_STRAP,
                tb_wear=np.clip(rec["age"] * 1.3 + 0.25, 0, 1),
                tb_grime=rec["dirt"] * 1.3)


def handles(acc, rec, srf):
    """Two carry loops.  ``carry_grip`` publishes them; the crew items use it."""
    cp = srf["cp"]
    ab0 = cp["a_band0"]; ab1 = cp["a_band1"]
    out = []
    for k, h in enumerate(rec["handles"]):
        a0 = ab0 + 0.045
        a1 = ab1 - 0.045
        n = 34
        t = np.linspace(0, 1, n)
        aa = a0 + (a1 - a0) * t
        bb = np.full(n, h["b"])
        P, N = surf_at(srf, aa, bb)
        arch = np.sin(math.pi * np.clip((t - 0.06) / 0.88, 0, 1)) ** 0.75
        P = P + N * ((0.0016 + HANDLE_RISE * h["rise"] * arch)[:, None])
        V, Q = sweep_ribbon(P, N, 0.0135, 0.0030)
        acc.add(V, quads=Q, mat="Webbing", tb_region=REGION_STRAP,
                tb_wear=np.clip(0.45 + rec["age"], 0, 1),
                tb_grime=np.clip(rec["dirt"] * 1.5, 0, 1), tb_seam=0.0)
        # bar tacks: a 38 x 25 mm block of dense stitching at each end
        for e in (0, n - 1):
            o = P[e]
            tg = unit(P[min(e + 2, n - 1)] - P[max(e - 2, 0)])
            u = N[e]
            s_ = unit(np.cross(tg, u))
            u = unit(np.cross(s_, tg))
            M = np.stack([tg, s_, u], axis=1)
            blk, bq = rounded_box((0.0250, 0.0300, 0.0022), radius=0.0008,
                                  centre=(0.0, 0.0, -0.0006))
            acc.add(blk @ M.T + o, quads=bq, mat="Webbing",
                    tb_region=REGION_STRAP, tb_seam=0.0, tb_wear=0.8)
        out.append(dict(P=P.copy(), N=N.copy()))
    return out


def gland_and_cable(acc, rec, srf):
    """The strain-relief gland and the tail of cable this module owns.

    THE INTERFACE BOUNDARY WITH ``tyre_blanket_controller`` LIVES HERE.  I build
    the gland, its ribs and 0.35-0.95 m of 8.5 mm cable.  ``cable_exit`` and
    ``cable_tail`` publish where that ends and which way it is pointing.
    """
    a_g, b_g = rec["gland_a"], rec["gland_b"]
    Pg, Ng = surf_at(srf, np.array([a_g]), np.array([b_g]))
    o = Pg[0]; nv = Ng[0]
    # a frame with +Z along the surface normal
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, nv))) > 0.9:
        ref = np.array([0.0, 0.0, 1.0])
    ex = unit(np.cross(ref, nv)); ey = unit(np.cross(nv, ex))
    M = np.stack([ex, ey, nv], axis=1)

    # a moulded rubber gland: flange, body, five relief ribs, a taper
    prof = [(0.0000, GLAND_D * 0.5 + 0.0035), (0.0022, GLAND_D * 0.5 + 0.0035),
            (0.0040, GLAND_D * 0.5), (0.0140, GLAND_D * 0.5 - 0.0010)]
    for k in range(5):
        z = 0.0175 + k * 0.0062
        rb = 0.0092 - k * 0.0012
        prof += [(z - 0.0016, rb - 0.0014), (z, rb), (z + 0.0016, rb - 0.0014)]
    prof += [(0.0500, CABLE_D * 0.5 + 0.0009)]
    prof = np.array(prof)
    # solid of revolution about local Z: built as (x = distance along, r)
    lath = np.stack([prof[:, 0], prof[:, 1]], axis=1)
    lath = np.concatenate([np.array([[0.0, 0.0]]), lath,
                           np.array([[0.0500, 0.0]])], axis=0)
    th = np.linspace(0, 2 * math.pi, 32, endpoint=False)
    Vg, Qg = revolve(lath, th, closed_loop=True)
    Vg = np.stack([Vg[:, 1], Vg[:, 2], Vg[:, 0]], axis=1)   # local x->z
    acc.add(Vg @ M.T + o, quads=Qg, mat="Cable", tb_region=REGION_CABLE,
            tb_grime=rec["dirt"], tb_wear=0.35)

    # ---- the cable tail ---------------------------------------------------
    down = np.asarray(rec["_down"], float)
    Ltail = rec["cable_len"]
    n = max(24, int(Ltail / 0.012))
    t = np.linspace(0, 1, n)
    route = rec["cable_route"]
    d0 = nv
    if route == "coil":
        # three loose turns hanging off the gland
        turns = 2.6
        ang = t * turns * 2 * math.pi
        rad = 0.052 + 0.010 * np.sin(ang * 0.7)
        Pt = (o + nv * 0.055)[None, :] \
            + ex[None, :] * (rad * np.cos(ang))[:, None] \
            + ey[None, :] * (rad * np.sin(ang))[:, None] \
            + down[None, :] * (t * 0.10)[:, None] \
            + nv[None, :] * (0.02 * np.sin(ang))[:, None]
    else:
        # 8.5 mm 3-core rubber cable holds a 0.10-0.16 m radius, not 0.24-0.40:
        # the first render put a stiff wire hoop over the wheel.
        bend = 0.105 if route == "drop" else 0.155
        dirv = np.zeros((n, 3))
        p = o + nv * 0.050
        cur = d0.copy()
        pts = [p.copy()]
        ds = Ltail / (n - 1)
        for j in range(1, n):
            perp = down - cur * float(np.dot(down, cur))
            npn = np.linalg.norm(perp)
            if npn > 1e-9:
                cur = cur + (perp / npn) * (ds / bend)
                cur = cur / np.linalg.norm(cur)
            p = p + cur * ds
            zf = rec["_zfloor"] + 0.006
            if p[2] < zf:
                p[2] = zf
                if cur[2] < 0:
                    cur[2] = 0.0
                    cur = cur / max(np.linalg.norm(cur), 1e-9)
                    cur = unit(cur + np.cross(cur, np.array([0.0, 0.0, 1.0]))
                               * 0.55 * math.sin(4.0 * j * ds + rec["pool_phase"]))
            pts.append(p.copy())
        Pt = np.array(pts)
    V, Q, T = sweep_tube(Pt, CABLE_D * 0.5, nside=12)
    acc.add(V, quads=Q, tris=T, mat="Cable", tb_region=REGION_CABLE,
            tb_grime=np.clip(rec["dirt"] * 1.4, 0, 1), tb_wear=0.4)
    return dict(origin=o, axis=nv, tail=Pt)


def sewn_patches(acc, rec, srf):
    """The stitched brand patch, the woven care label and the compound tab.

    Screen-printed ink has no relief and is handled by ``tb_print``.  These are
    the things that are SEWN ON, which do: 1.6 mm of patch, a 3 mm stitched
    border that puckers the cloth under it, and a label that is caught on one
    edge only and has curled.
    """
    cp = srf["cp"]
    # ---- the brand patch on the outboard side panel -----------------------
    a_c = rec["patch_a"]
    b_c = rec["patch_b"]
    pw, ph = rec["patch_w"], rec["patch_h"]
    nu, nv_ = 26, 14
    uu = np.linspace(-pw * 0.5, pw * 0.5, nu)
    vv = np.linspace(-ph * 0.5, ph * 0.5, nv_)
    U, Vv = np.meshgrid(uu, vv, indexing="ij")
    P, N = surf_at(srf, np.clip(a_c + Vv, 0.006, cp["s_total"] - 0.006),
                   np.clip(b_c + U, 0.004, srf["tot"] - 0.004))
    d = rrect_sdf(U, Vv, pw * 0.5, ph * 0.5, 0.008)
    puck = np.clip(1.0 + d / 0.006, 0, 1)
    thick = 0.0016 * np.clip(-d / 0.004, 0, 1) ** 0.5
    Ptop = P + N * (0.0004 + thick)[:, :, None]
    Pbot = P + N * 0.0003
    Vt = np.concatenate([Ptop.reshape(-1, 3), Pbot.reshape(-1, 3)], axis=0)
    Qt = grid_quads(nu, nv_)
    Qb = grid_quads(nu, nv_)[:, ::-1] + nu * nv_
    # U runs along +b, which on the OUTBOARD panel the lens reads right-to-left
    # (see print_sdf): the patch is set against -U so it is not mirrored.
    segs, w, hw = text_segments(rec["brand"][0], 0.026,
                                tracking=rec["brand"][5], weight=0.22)
    prt = seg_sdf(-U.ravel() + w * 0.5, Vv.ravel() + 0.004, segs, hw)
    acc.add(Vt, quads=np.concatenate([Qt, Qb], axis=0), mat="Label",
            tb_region=REGION_PATCH,
            tb_print=np.concatenate([prt, np.full(nu * nv_, 1.0)]),
            tb_wear=np.clip(rec["age"] * 0.9, 0, 1),
            tb_grime=rec["dirt"] * 0.8, tb_seam=0.0)
    # its stitched border, as a real bead
    bd = []
    m = 90
    tt = np.linspace(0, 2 * math.pi, m, endpoint=False)
    ex_ = (pw * 0.5 - 0.004) * np.sign(np.cos(tt)) * np.minimum(
        np.abs(np.cos(tt)) * 1.6, 1.0)
    ey_ = (ph * 0.5 - 0.004) * np.sign(np.sin(tt)) * np.minimum(
        np.abs(np.sin(tt)) * 1.6, 1.0)
    Pb, Nb = surf_at(srf, np.clip(a_c + ey_, 0.006, cp["s_total"] - 0.006),
                     np.clip(b_c + ex_, 0.004, srf["tot"] - 0.004))
    Pb = Pb + Nb * 0.0021
    V, Q = sweep_ribbon(Pb, Nb, 0.0016, 0.0014, close=True)
    acc.add(V, quads=Q, mat="Binding", tb_region=REGION_PATCH, tb_seam=0.0,
            tb_wear=0.6)

    # ---- the care label, caught on one edge and curled --------------------
    a_l, b_l = rec["label_a"], rec["label_b"]
    P0, N0 = surf_at(srf, np.array([a_l]), np.array([b_l]))
    o = P0[0]; nv2 = N0[0]
    P1, _ = surf_at(srf, np.array([a_l + 0.01]), np.array([b_l]))
    tg = unit(P1[0] - o)
    s_ = unit(np.cross(tg, nv2)); u_ = unit(np.cross(s_, tg))
    lw, ll = 0.042, 0.026
    nu2, nv3 = 16, 10
    uu = np.linspace(0, ll, nu2)
    vv = np.linspace(-lw * 0.5, lw * 0.5, nv3)
    U, Vv = np.meshgrid(uu, vv, indexing="ij")
    curl = rec["label_curl"]
    lift = (U / ll) ** 1.7 * curl
    Pl = (o[None, None, :] + tg[None, None, :] * U[:, :, None]
          + s_[None, None, :] * Vv[:, :, None]
          + u_[None, None, :] * (lift + 0.0009)[:, :, None]
          + tg[None, None, :] * (-(lift ** 2) * 3.0)[:, :, None])
    Pl = Pl + s_[None, None, :] * (np.sin(Vv * 60.0) * lift * 0.25)[:, :, None]
    Vt2 = np.concatenate([Pl.reshape(-1, 3),
                          (Pl - u_ * 0.0006).reshape(-1, 3)], axis=0)
    Q2 = np.concatenate([grid_quads(nu2, nv3),
                         grid_quads(nu2, nv3)[:, ::-1] + nu2 * nv3], axis=0)
    acc.add(Vt2, quads=Q2, mat="Label", tb_region=REGION_PATCH,
            tb_wear=np.clip(rec["age"] * 1.2, 0, 1), tb_grime=rec["dirt"] * 0.5)

    # ---- the compound colour tab ------------------------------------------
    a_t, b_t = rec["tab_a"], rec["tab_b"]
    nu3, nv4 = 12, 6
    uu = np.linspace(-0.030, 0.030, nu3)
    vv = np.linspace(-0.011, 0.011, nv4)
    U, Vv = np.meshgrid(uu, vv, indexing="ij")
    P, N = surf_at(srf, np.clip(a_t + Vv, 0.006, cp["s_total"] - 0.006),
                   np.clip(b_t + U, 0.004, srf["tot"] - 0.004))
    Pt2 = P + N * 0.0012
    acc.add(np.concatenate([Pt2.reshape(-1, 3), (P + N * 0.0002).reshape(-1, 3)]),
            quads=np.concatenate([grid_quads(nu3, nv4),
                                  grid_quads(nu3, nv4)[:, ::-1] + nu3 * nv4]),
            mat="Label", tb_region=REGION_PATCH, tb_band=1.0,
            tb_wear=np.clip(rec["age"], 0, 1))


# ==============================================================================
#  8.  THE BRAND BOOK  —  reused, not reinvented
# ==============================================================================
# Law 2: "No real sponsor names.  31 invented brands already exist in
# build_dressing's brand book and 12 are shared with build_architecture - reuse
# them."  So this module READS that table out of build_dressing.py rather than
# copying it, because a copy is a thing that goes stale and a 32nd brand
# fragments the world's identity.  build_dressing imports bpy at module scope
# and this module has to work from a bare shell, so the literal is lifted with
# ast instead of by importing.

_BRANDS = None


def brands():
    global _BRANDS
    if _BRANDS is not None:
        return _BRANDS
    import ast
    p = os.path.join(_WORLD, "build_dressing.py")
    txt = open(p, "r").read()
    i = txt.index("\nBRANDS = [")
    j = txt.index("\n]", i)
    _BRANDS = ast.literal_eval(txt[i + len("\nBRANDS = "):j + 2])
    return _BRANDS


def srgb_lin(hexs):
    v = [int(hexs[k:k + 2], 16) / 255.0 for k in (1, 3, 5)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                 for c in v)


def _relum(c, lo, hi):
    """Keep the hue, move the luminance into [lo, hi]."""
    c = np.asarray(c, float)
    y = float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
    if y < 1e-6:
        return (lo, lo, lo)
    t = lo + (hi - lo) * (y ** 0.45)
    return tuple(float(v) for v in np.clip(c * (t / y), 0.0, 1.0))


def blanket_colours(br):
    """The colour a blanket is actually MADE in, not the colour of the hoarding.

    A brand's board colour is picked to be legible at 80 m on an advertising
    panel.  A blanket made in it would be the brightest object in the pit lane:
    CIRRUS's #4aa3d8 is 0.687 linear in blue, and the first render measured the
    side panel at 0.700 sRGB -- brighter than the sunlit garage front behind it
    (0.740) and 2.3x the deck.  Silicone-coated glass cloth in a team colour
    measures 0.018-0.052 linear; screen-printed ink on it measures 0.055-0.26,
    not the 0.9 that "white" wants.  Hue kept, luminance moved.
    """
    return _relum(srgb_lin(br[1]), 0.018, 0.052), \
        _relum(srgb_lin(br[2]), 0.055, 0.260)


# ==============================================================================
#  9.  THE PLAN:  56 blankets = 14 pit boxes x 4 wheels
# ==============================================================================
# The manifest's 56 and the spec's 14 garages are the same fact, not a
# coincidence, so the plan is built from the garage list and lands on 56 exactly.
#
# Every axis the manifest names is resolved as GEOMETRY here, never as a
# material variant:
#
#   wrapped/open   six box states, from four blankets on and closed to two
#                  wheels stripped bare with a blanket pooled on the deck.  A
#                  peeled blanket is a genuinely different surface -- it is
#                  re-integrated as a hanging sheet, not rotated.
#   velcro flap    the overlap is a real second layer of cloth with a real
#                  14 mm step; the gape at its free edge runs 4 mm (dressed) to
#                  38 mm (thrown on in a hurry).
#   scorch marks   0-4 sites per blanket, and on the old ones the shell has
#                  burned THROUGH: the outer face collapses onto the batting and
#                  a 2 mm melt lip beads up round the hole.
#   cable dangling four routes -- coiled on the gland, dropped to the deck,
#                  running away to a socket, pooled -- and the tail length runs
#                  0.35 to 0.95 m.
#   branded face   one of the 31 invented brands per box (14 teams, 14 brands),
#                  set in this module's own stroke face and baked as an SDF.
#
# and four more the manifest did not have to ask for, because they are what
# makes 56 of something look like 56 things: front vs rear section (305 vs
# 405 mm, a REAL 100 mm of geometry), five compounds including two with moulded
# rain grooves, three quilt generations with different pitch and pattern, and
# the wheel itself either bare-faced or under a 2022 aero cover.

BOX_STATES = {
    "ready":    ["fitted", "fitted", "fitted", "fitted"],
    "warming":  ["fitted", "gaping", "fitted", "fitted"],
    "opening":  ["fitted", "flap_open", "gaping", "fitted"],
    "stripped": ["bare", "fitted", "off", "fitted"],
    "swap":     ["bare", "bare", "fitted", "flap_open"],
    "mixed":    ["gaping", "flap_open", "fitted", "bare"],
}
BOX_KINDS = (["ready"] * 3 + ["warming"] * 3 + ["opening"] * 3
             + ["stripped"] * 2 + ["swap"] * 1 + ["mixed"] * 2)

BOX_ARR = {
    "row4":        ["upright", "upright", "upright", "upright"],
    "row3_flat1":  ["upright", "upright", "upright", "flat"],
    "row2_stack2": ["upright", "upright", "flat", "flat_stack"],
}
ARR_KINDS = ["row4"] * 6 + ["row3_flat1"] * 4 + ["row2_stack2"] * 4

_PLAN = None


def plan():
    """56 deterministic records.  Pure python + numpy; no bpy, no side effects."""
    global _PLAN
    if _PLAN is not None:
        return _PLAN
    B = brands()
    ordr = sorted(range(len(B)), key=lambda i: rnd("teamorder", i))
    kinds = [BOX_KINDS[i] for i in sorted(range(N_BAYS),
                                          key=lambda i: rnd("boxkind", i))]
    arrs = [ARR_KINDS[i] for i in sorted(range(N_BAYS),
                                         key=lambda i: rnd("boxarr", i))]
    recs = []
    for box in range(N_BAYS):
        bx = GARAGE_X0 + BAY_PITCH * (box + 0.5)
        kind = kinds[box]
        arr = arrs[box]
        states = BOX_STATES[kind]
        poses = BOX_ARR[arr]
        br = B[ordr[box % len(ordr)]]
        base_comp = int(rnd("comp", box) * 3)          # dry compounds mostly
        if rnd("wetbox", box) < 0.18:
            base_comp = 3 + int(rnd("wetc", box) * 2)
        # the four corners of a set, in a deterministic but non-obvious order
        cs = [CORNERS[i] for i in sorted(range(4),
                                         key=lambda i: rnd("corner", box, i))]
        for slot in range(4):
            uid = box * 4 + slot
            state = states[slot]
            pose = poses[slot]
            corner = cs[slot]
            W = corner_width(corner)
            comp = base_comp
            if rnd("compmix", uid) < 0.22:
                comp = int(rnd("compmix2", uid) * 5)
            wear = (rr(0.0, 0.22, uid, "wear") if rnd("scrub", uid) < 0.55
                    else rr(0.35, 0.92, uid, "wear2"))
            age = rr(0.05, 0.95, uid, "age")
            dirt = float(np.clip(age * rr(0.5, 1.25, uid, "dirt"), 0.03, 1.0))

            # ---- straps: two or three, and where their buckles sit --------
            cpq = conform_profile(dict(width=W, wear=wear))
            a0, a1 = cpq["a_band0"], cpq["a_band1"]
            nstr = 2 if rnd("nstrap", uid) < 0.45 else 3
            Rr = TYRE_R + BLK_GAP + BLK_T * 0.5
            tot = 2.0 * math.pi * Rr + OVERLAP_M
            straps = []
            for k in range(nstr):
                f = (k + 1.0) / (nstr + 1.0)
                straps.append(dict(
                    a=a0 + (a1 - a0) * (f + rr(-0.06, 0.06, uid, "sa", k)),
                    b_buckle=tot * rr(0.05, 0.95, uid, "sb", k),
                    tail=rr(0.10, 0.34, uid, "st", k),
                    dangle=rnd("sd", uid, k) < 0.42,
                    phase=rr(0, 6.283, uid, "sp", k)))

            # ---- scorch and burn-through ----------------------------------
            nsc = int(rnd("nsc", uid) * 4.4 * (0.35 + age))
            scorch = []
            for k in range(nsc):
                deep = rr(0.35, 1.0, uid, "scd", k)
                scorch.append(dict(
                    a=rr(0.02, cpq["s_total"] - 0.02, uid, "sca", k),
                    b=rr(0.02, tot - 0.02, uid, "scb", k),
                    r=rr(0.014, 0.048, uid, "scr", k),
                    deep=deep,
                    through=bool(age > 0.62 and deep > 0.80
                                 and rnd("sct", uid, k) < 0.55)))

            has_blanket = state != "bare"
            # ---- the peel: where the sheet leaves the tyre ------------------
            peel_lo = peel_hi = None
            theta0 = rr(0.0, 6.283, uid, "th0")
            if state == "flap_open":
                peel_hi = tot - rr(0.26, 0.62, uid, "peel")
                theta0 = rr(1.2, 2.6, uid, "th0f")
            elif state == "off":
                L = tot - OVERLAP_M
                half = rr(0.26, 0.42, uid, "peeloff")
                peel_lo = L * 0.5 - half
                peel_hi = L * 0.5 + half
                theta0 = math.pi * 0.5 - (L * 0.5) / Rr

            gape = {"fitted": rr(0.004, 0.013, uid, "gp"),
                    "gaping": rr(0.020, 0.038, uid, "gp"),
                    "flap_open": 0.004, "off": 0.0, "bare": 0.0}[state]

            # ---- placement, circuit frame ----------------------------------
            if pose in ("flat", "flat_stack"):
                cxo = 1.35 + rr(-0.25, 0.25, uid, "px")
                cyo = 21.15 + rr(-0.30, 0.30, uid, "py")
            else:
                cxo = (-0.90 + 0.60 * slot) + rr(-0.07, 0.07, uid, "px")
                cyo = 22.84 + rr(-0.06, 0.06, uid, "py")
            if pose == "flat_stack":
                # sits on the one below: same footprint, deterministic offset
                cxo = 1.35 + rr(-0.25, 0.25, uid - 1, "px") \
                    + rr(-0.045, 0.045, uid, "stx")
                cyo = 21.15 + rr(-0.30, 0.30, uid - 1, "py") \
                    + rr(-0.045, 0.045, uid, "sty")
            cx, cy = bx + cxo, cyo
            wx, wy = C.circuit_to_world(cx, cy)
            zg, owner = C.world_ground_z(float(wx), float(wy))

            rec = dict(
                uid=uid, box=box, slot=slot, kind=kind, arr=arr,
                corner=corner, width=W, compound=comp, wear=wear,
                state=state, pose=pose, has_blanket=has_blanket,
                gen=int(rnd("gen", uid) * 3),
                brand=br, brand_bg=blanket_colours(br)[0],
                brand_fg=blanket_colours(br)[1],
                tyre_brand=brands()[[b[0] for b in brands()].index("MERIDIAN")][0],
                age=age, dirt=dirt, dust=rr(0.15, 1.0, uid, "dust"),
                slack=rr(0.55, 1.45, uid, "slack"),
                hem_amp=rr(0.0038, 0.0105, uid, "hem"),
                crumple=rr(0.55, 1.75, uid, "crum"),
                gape=gape, theta0=theta0, peel_lo=peel_lo, peel_hi=peel_hi,
                hang_stiff=rr(0.28, 0.48, uid, "hs"),
                hang_flat=rr(0.10, 0.24, uid, "hf"),
                pool_phase=rr(0, 6.283, uid, "pool"),
                straps=straps, scorch=scorch,
                handles=[dict(b=tot * rr(0.10, 0.42, uid, "h0"),
                              rise=rr(0.6, 1.25, uid, "hr0")),
                         dict(b=tot * rr(0.56, 0.92, uid, "h1"),
                              rise=rr(0.6, 1.25, uid, "hr1"))],
                gland_a_f=rr(0.06, 0.30, uid, "ga"),
                gland_b=float(np.clip(
                    (((math.pi * 0.5 + rr(-1.25, 1.25, uid, "gth") - theta0)
                      * Rr) % (2.0 * math.pi * Rr)), 0.03, tot - 0.03)),
                cable_len=rr(0.35, 0.95, uid, "cl"),
                cable_route=rpick(["coil", "drop", "run", "drop"], uid, "cr"),
                patch_a_f=rr(0.30, 0.62, uid, "pa"),
                patch_b=tot * rr(0.03, 0.97, uid, "pb"),
                patch_w=rr(0.150, 0.215, uid, "pw"),
                patch_h=rr(0.055, 0.082, uid, "ph"),
                label_a_f=rr(0.14, 0.34, uid, "la"),
                label_b=tot * rr(0.03, 0.97, uid, "lb"),
                label_curl=rr(0.004, 0.028, uid, "lc"),
                tab_a_f=rr(0.40, 0.78, uid, "ta"),
                tab_b=tot * rr(0.03, 0.97, uid, "tb"),
                print_n=2 if rnd("pn", uid) < 0.6 else 3,
                print_phase=rr(0, 1, uid, "pp"),
                side_phi=rr(0, 6.283, uid, "sph"),
                letter_phi=rr(0, 6.283, uid, "lph"),
                rim_phase=rr(0, 0.628, uid, "rph"),
                aero_cover=bool(rnd("aero", uid) < 0.34),
                yaw=rr(-0.24, 0.24, uid, "yaw"),
                lean=rr(0.030, 0.165, uid, "lean"),
                spin=rr(0, 6.283, uid, "spin"),
                face_up=bool(rnd("fup", uid) < 0.6),
                cx=float(cx), cy=float(cy),
                wx=float(wx), wy=float(wy), zg=float(zg), owner=owner,
                stack_on=(uid - 1 if pose == "flat_stack" else None),
                a_band0=cpq["a_band0"], a_band1=cpq["a_band1"],
                s_total=cpq["s_total"], wrap_total=tot,
            )
            recs.append(rec)
    _PLAN = recs
    return recs


# ==============================================================================
# 10.  POSE, PLACEMENT AND ONE INSTANCE
# ==============================================================================

def cdir(vx, vy):
    """A direction in the circuit frame -> the same direction in world."""
    cr, sr = math.cos(math.radians(C.ROT_DEG)), math.sin(math.radians(C.ROT_DEG))
    return np.array([vx * cr - vy * sr, vx * sr + vy * cr, 0.0])


def rot_about(axis, ang):
    a = unit(np.asarray(axis, float))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def pose_frame(rec):
    """local (X = wheel axis outboard, Z = up when standing) -> world axes.

    The garage front is on circuit y = +23.5 and faces the pit lane, so a wheel
    stood against it has its axis along circuit -y and its OUTBOARD face -- the
    one with the brand on it and the wheel showing through the hem -- turned
    toward the lens.  That is not a styling choice; it is where a mechanic puts
    a wheel down so he can read the compound tab.
    """
    if rec["pose"] in ("flat", "flat_stack"):
        ex = np.array([0.0, 0.0, 1.0 if rec["face_up"] else -1.0])
        ez = np.array([math.cos(rec["spin"]), math.sin(rec["spin"]), 0.0])
    else:
        n = cdir(0.0, -1.0)
        c, s = math.cos(rec["yaw"]), math.sin(rec["yaw"])
        ex = np.array([n[0] * c - n[1] * s, n[0] * s + n[1] * c, 0.0])
        ex = unit(ex)
        ez = rot_about(ex, rec["lean"]) @ np.array([0.0, 0.0, 1.0])
    ez = unit(ez - ex * float(np.dot(ez, ex)))
    ey = np.cross(ez, ex)
    return np.stack([ex, ey, ez], axis=1)


def lowest_z(profile_xr, R):
    """Exact minimum world-oriented z of a body of revolution about local X."""
    P = np.asarray(profile_xr, float)
    k = math.hypot(R[2, 1], R[2, 2])
    return float(np.min(R[2, 0] * P[:, 0] - P[:, 1] * k))


def build_instance(rec, lod=0, fine=None):
    """One blanketed (or bare) wheel, in the world-oriented frame, hub at 0.

    -> (Acc, info) where info carries everything the interface publishes.
    """
    Rot = pose_frame(rec)
    if fine is None:
        fine = (lod == 0)
    W = rec["width"]
    P2, _, _, _ = tyre_section(W, rec["wear"])
    z_tyre = lowest_z(P2, Rot)

    srf = None
    if rec["has_blanket"]:
        srf = blanket_surface(rec, lod, Rot)
        z_floor = min(srf["z_floor"], z_tyre + BASE_EMBED)
    else:
        z_floor = z_tyre + BASE_EMBED
    rec["_zfloor"] = z_floor
    rec["_down"] = (0.0, 0.0, -1.0)

    acc = Acc()
    # ---- the wheel, built in its own frame then carried into this one -----
    tacc = Acc()
    tyre_mesh(tacc, rec, fine=fine)
    rim_mesh(tacc, rec, fine=fine)
    M = np.eye(4); M[:3, :3] = Rot
    acc.merge(tacc, M)

    # a loaded tyre bulges where it meets the deck.  Applied once, here, to
    # everything already below the floor, and only when the wheel is standing.
    axis_w = Rot @ np.array([1.0, 0.0, 0.0])
    if abs(float(axis_w[2])) < 0.55:
        hw = W * 0.5

        def bulge(V):
            dep = np.clip(z_floor - V[:, 2], 0.0, 0.20)
            if dep.max() <= 0.0:
                return V
            lx = V @ axis_w
            f = np.clip(np.abs(lx) / hw, 0, 1)
            return V + axis_w[None, :] * (np.sign(lx) * f * dep * 0.85)[:, None]
        acc.map_verts(bulge)

    info = dict(uid=rec["uid"])
    if srf is not None:
        cp = srf["cp"]
        A = cp["s_total"]
        # a = 0 is the INBOARD hem and a = A is the OUTBOARD hem (the section
        # is traversed inboard bead -> crown -> outboard bead).  The branded
        # face, the compound tab and the cable gland all belong on the OUTBOARD
        # panel, because that is the side a mechanic leaves facing him and the
        # side the lens sees off the pit lane -- and on a wheel laid flat with
        # its outboard face DOWN, the gland goes to the other panel, because a
        # 50 mm gland under 12 kg of wheel is 50 mm of gland underground.
        up_out = (not rec["pose"].startswith("flat")) or rec["face_up"]
        rec["patch_a"] = A - cp["a_band0"] * rec["patch_a_f"]
        rec["tab_a"] = A - cp["a_band0"] * rec["tab_a_f"]
        rec["label_a"] = cp["a_band0"] * rec["label_a_f"]
        # THE GLAND BELONGS ON THE SHOULDER, not in the middle of the branded
        # face.  On the side panel its outward normal is AXIAL, so the cable
        # left the blanket straight at the lens and then draped across the
        # wheel -- which is where the first render put a bare wire over the
        # spokes.  On the shoulder the normal is radial and the cable falls
        # down the outside of the tyre, which is where it falls in life.
        sh = cp["a_band1"] + (A - cp["a_band1"]) * rec["gland_a_f"]
        rec["gland_a"] = sh if up_out else (cp["a_band0"]
                                            * (1.0 - rec["gland_a_f"]))
        blanket_mesh(acc, rec, srf)
        binding_and_closure(acc, rec, srf)
        strap_and_buckle(acc, rec, srf)
        hh = handles(acc, rec, srf)
        gi = gland_and_cable(acc, rec, srf)
        sewn_patches(acc, rec, srf)
        info["handles"] = [dict(path=h["P"].tolist()[::4],
                                normal=h["N"].tolist()[::4]) for h in hh]
        info["cable"] = dict(origin=gi["origin"].tolist(),
                             axis=gi["axis"].tolist(),
                             tail=gi["tail"].tolist()[::3],
                             tail_end=gi["tail"][-1].tolist(),
                             tail_dir=unit(gi["tail"][-1]
                                           - gi["tail"][-2]).tolist(),
                             diameter=CABLE_D)
        # MEASURED OVER THE ATTACHED WRAP ONLY.  On the instances whose blanket
        # is peeled off, the sheet is lying on the deck two metres from the
        # axis, and a "blanketed OD" that includes it reported 1.741 m -- a
        # number no trolley cradle can use.  det marks the columns that have
        # left the tyre; they are the pooled cloth, not the object's envelope.
        att = ~srf["det"]
        PW = srf["PO"][:, att, :].reshape(-1, 3) if att.any() \
            else srf["PO"].reshape(-1, 3)
        aw = PW @ axis_w
        rw = np.linalg.norm(PW - axis_w[None, :] * aw[:, None], axis=1)
        # TWO numbers, because a cradle and a clearance envelope are different
        # questions: p98 is the body of the blanket (what a trolley seats on),
        # max also contains the one free edge that is standing 40 mm off it.
        info["blanket_od"] = float(2.0 * np.percentile(rw, 98.0))
        info["blanket_od_envelope"] = float(2.0 * rw.max())
        info["axial_width"] = float(np.percentile(aw, 99.0)
                                    - np.percentile(aw, 1.0))
        info["axial_envelope"] = float(np.ptp(aw))

    lo, hi = acc.bounds()
    # LAW 5 IS MEASURED, NOT ASSUMED.  z_floor was predicted from the analytic
    # section before the mesh existed; resampling that section to rows can miss
    # its extremum by a few tenths of a millimetre, and over 56 instances the
    # worst embed came out at 19.7 mm against a 20.0 mm obligation.  So the
    # floor is RE-DERIVED from the geometry that actually got built, and it can
    # only ever move the object DOWN.
    z_floor = max(z_floor, float(lo[2]) + BASE_EMBED)
    info["z_floor"] = z_floor
    info["z_hub"] = rec["zg"] - z_floor
    info["embed_m"] = float(z_floor - lo[2])
    info["local_bounds"] = [lo.tolist(), hi.tolist()]
    info["triangles"] = acc.tris()
    return acc, info


# ==============================================================================
# 11.  MATERIALS
# ==============================================================================
# Ten shaders.  All procedural, all driven by TexCoord->Object or by an
# attribute this module baked -- `Geometry->Position` appears nowhere, per law 6,
# because these objects sit up to 480 m from the world origin and a
# position-driven procedural at |P| ~ 500 m is the blotching the first pass was
# rejected for.
#
# CALIBRATION.  Exposure is C.REFERENCE_EXPOSURE_EXTERIOR = -3.048 EV under AgX,
# with the sun 12.47 deg up.  These objects stand in the shade of the garage
# front for most of the day and take a raking key at the end of it, so their
# linear reflectances are set LOW: silicone-coated glass cloth in a team colour
# measures 0.03-0.10, not the 0.25 that "blue" wants to be; a used F1 slick
# measures 0.014-0.022, which is darker than almost any other object in the
# film; and magnesium under three stints of brake dust is 0.09-0.16 and warm.

class NT(object):
    """Node DSL.  Same shape as pit_wall_unit's and kerb_precast_unit's."""

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
        nd.location = ((self.x % 13) * 230, -(self.x // 13) * 320)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, idx, src):
        if src is None:
            return
        if isinstance(src, tuple) and len(src) == 2 and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (tuple(src) + (1.0,)
                                            if len(src) == 3 else tuple(src))
        else:
            nd.inputs[idx].default_value = float(src)

    def pinname(self, nd, name, src):
        """Wire a socket BY NAME, and RAISE if that name is gone.

        R2-057.  This used to `if name in ...: pin(...)` and otherwise do
        nothing at all.  A by-name helper that shrugs when the name is missing
        buys nothing over an index: the failure it is supposed to prevent --
        relief computed in full and delivered nowhere -- happens just the same,
        still with no error and still with a plausible render.  The whole value
        of addressing by name is that the name is checkable, so check it.
        """
        if src is None:
            return
        for i in nd.inputs:
            if i.name == name:
                return self.pin(nd, name, src)
        raise RuntimeError(
            "%s has no input named %r; it has %s"
            % (nd.bl_idname, name, [i.name for i in nd.inputs]))

    def cmix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, 0, fac); self.pin(nd, 6, a); self.pin(nd, 7, b)
        return (nd, 2)

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, 0, fac); self.pin(nd, 2, a); self.pin(nd, 3, b)
        return (nd, 0)

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        return (nd, 0)

    def vmath(self, op, a=None, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        if scale is not None:
            self.pin(nd, 3, scale)
        return (nd, 0)

    # SOCKET INDICES ARE VERIFIED AGAINST BLENDER 5.2, NOT REMEMBERED.  Three
    # of them moved and every one failed SILENTLY, which is the worst way for a
    # shader to be wrong -- it renders, it just renders a different material:
    #   TexNoise   input 6 is "Offset", not "Distortion" (that is 8).
    #   Bump       inputs are (Strength, Distance, Filter Width, Height,
    #              Normal) -- so the old (0,1,2) put HEIGHT into FILTER WIDTH
    #              and left Height unconnected.  Every bump in this module was
    #              dead, which is exactly why the first render came back
    #              plastic: no weave, no nap, no grain, no cast-in relief.
    #   TexVoronoi output 0 is "Distance", which for F1 in 3D lives in roughly
    #              0.0-0.6 with a mean near 0.25.  Thresholding it at 0.72-0.98
    #              -- as the first version did for marbles, chips, scuffs, fray
    #              and pickup -- clamps to zero everywhere, so five separate
    #              weathering layers were switched off.
    def noise(self, vec, scale, detail=8.0, rough=0.55, lac=2.0, out=0,
              dist=0.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 3, detail)
        self.pin(nd, 4, rough); self.pin(nd, 5, lac); self.pin(nd, 8, dist)
        return (nd, out)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 8, rand)
        return (nd, out)

    def spots(self, vec, scale, near=0.035, far=0.130, rand=1.0):
        """A sparse 0..1 mask that is 1 AT the Voronoi feature points.

        `near`/`far` are distances in Voronoi cell units, so `far` sets how big
        each spot is and `near` how hard its edge is.  This is the correct way
        to get marbles, chips, spalls and pickup out of a Distance output.
        """
        return self.maprange(self.vor(vec, scale, rand=rand), far, near,
                             0.0, 1.0)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, direction="X",
             out=1):
        nd = self.n("ShaderNodeTexWave", wave_type="BANDS",
                    bands_direction=direction)
        self.pin(nd, 0, vec); self.pin(nd, 1, scale)
        self.pin(nd, 2, distortion); self.pin(nd, 3, detail)
        return (nd, out)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, 0, src)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = tuple(stops[0][1]) + (1.0,)
        for pos, colr in stops[1:]:
            e = el.new(pos)
            e.color = tuple(colr) + (1.0,)
        return (nd, 0)

    def attr(self, name, out=2, typ="GEOMETRY"):
        nd = self.n("ShaderNodeAttribute", attribute_type=typ)
        nd.attribute_name = name
        return (nd, out)

    def maprange(self, v, f0, f1, t0, t1, clamp=True):
        nd = self.n("ShaderNodeMapRange")
        nd.clamp = clamp
        self.pin(nd, 0, v); self.pin(nd, 1, f0); self.pin(nd, 2, f1)
        self.pin(nd, 3, t0); self.pin(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance, normal=None):
        # R2-038/R2-057: BY NAME.  The indices this used (0/1/3/4, with a
        # comment noting that 2 is "Filter Width") were correct on 5.2 -- but
        # they were correct because someone had already been bitten once and
        # come back to fix them.  `Filter Width` was inserted at 2 in 5.2 and
        # silently ate the height of every bump in the kit; a name cannot be
        # inserted in front of.
        nd = self.n("ShaderNodeBump")
        self.pinname(nd, "Strength", strength)
        self.pinname(nd, "Distance", distance)
        self.pinname(nd, "Height", height)
        if normal is not None:
            self.pinname(nd, "Normal", normal)
        return (nd, 0)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def obj_coord(self):
        """Object space + a per-object offset, so 56 blankets are 56 shaders."""
        co = self.n("ShaderNodeTexCoord")
        ofs = self.comb(self.attr("tb_ofs_x", 2, "OBJECT"),
                        self.attr("tb_ofs_y", 2, "OBJECT"),
                        self.attr("tb_ofs_z", 2, "OBJECT"))
        return self.vmath("ADD", (co, 3), ofs)

    def uv_coord(self, sx=1.0, sy=1.0):
        """The FABRIC's own material coordinates, in metres, baked at build."""
        return self.comb(self.math("MULTIPLY", self.attr("tb_u"), sx),
                         self.math("MULTIPLY", self.attr("tb_v"), sy),
                         0.0)

    def out(self, bsdf, disp=None):
        o = self.n("ShaderNodeOutputMaterial")
        self.t.links.new(bsdf.outputs[0], o.inputs["Surface"])
        return o

    def prin(self, **kw):
        nd = self.n("ShaderNodeBsdfPrincipled")
        names = {i.name for i in nd.inputs}
        alias = {"base": "Base Color", "rough": "Roughness",
                 "metal": "Metallic", "normal": "Normal", "ior": "IOR",
                 "sheen": "Sheen Weight", "sheen_r": "Sheen Roughness",
                 "sheen_t": "Sheen Tint", "coat": "Coat Weight",
                 "coat_r": "Coat Roughness", "spec": "Specular IOR Level",
                 "aniso": "Anisotropic", "aniso_r": "Anisotropic Rotation",
                 "trans": "Transmission Weight", "emis": "Emission Color",
                 "emis_s": "Emission Strength"}
        for k, v in kw.items():
            nm = alias.get(k, k)
            if nm in names:
                self.pin(nd, nm, v)
        return nd


# Linear reflectances.  Every one is a measured-plausible surface, not a
# "colour": a black silicone blanket in sun is 0.035, not 0.05, and the
# difference is what stops it clipping to a grey slab under AgX.
PAL = dict(
    shell_dark=(0.0300, 0.0296, 0.0292),   # black silicone-glass, as new
    shell_grey=(0.0430, 0.0426, 0.0421),   # the paler weave under it
    glass_fibre=(0.0960, 0.0938, 0.0880),  # where the silicone has rubbed off
    thread=(0.0900, 0.0880, 0.0840),       # bonded polyester stitching
    scorch_warm=(0.0290, 0.0195, 0.0130),  # heat-browned silicone
    char=(0.0092, 0.0088, 0.0086),         # burnt through
    batt_gold=(0.1400, 0.1175, 0.0720),    # needled silica batting
    batt_white=(0.2350, 0.2320, 0.2225),
    alu_face=(0.1750, 0.1790, 0.1845),     # the aluminised inner face
    webbing=(0.0470, 0.0455, 0.0440),
    webbing_worn=(0.0910, 0.0880, 0.0830),
    buckle=(0.0330, 0.0330, 0.0345),
    buckle_scuff=(0.0760, 0.0760, 0.0780),
    cable=(0.0245, 0.0243, 0.0245),
    label=(0.1750, 0.1735, 0.1670),        # a woven label, sunlit, not paper
    rubber_new=(0.0205, 0.0203, 0.0206),   # unscrubbed slick, mould sheen
    rubber_run=(0.0142, 0.0140, 0.0142),   # after a stint
    rubber_blue=(0.0180, 0.0186, 0.0215),  # overheated: the blue bloom
    rubber_grain=(0.0260, 0.0250, 0.0244),
    marble=(0.0330, 0.0316, 0.0300),
    mag_paint=(0.0335, 0.0330, 0.0328),    # satin black-anodised magnesium
    mag_bare=(0.0760, 0.0750, 0.0725),     # where it has been rubbed back
    brake_dust=(0.0620, 0.0478, 0.0372),
    heat_tint=(0.1050, 0.0720, 0.0430),
    grime=(0.0330, 0.0300, 0.0258),
    velcro_hook=(0.0400, 0.0396, 0.0392),
    velcro_loop=(0.0620, 0.0612, 0.0600),
)


def _weave(t, uv, pitch=0.00034, ang=0.0):
    """A silicone-coated glass cloth weave: two crossed bands plus fibre noise.

    0.34 mm at 2.101 mm/px is 0.16 px, so this is shading and nothing else --
    but it is the difference between cloth and vinyl at every angle where the
    sheen catches, and the sheen on silicone-coated glass is the whole material.
    """
    w1 = t.wave(uv, 1.0 / pitch, distortion=1.4, detail=2.0, direction="X")
    w2 = t.wave(uv, 1.0 / pitch, distortion=1.4, detail=2.0, direction="Y")
    fib = t.noise(uv, 900.0, detail=4.0, rough=0.7)
    a = t.math("MULTIPLY", w1, w2)
    return t.math("ADD", t.math("MULTIPLY", a, 0.75),
                  t.math("MULTIPLY", fib, 0.25))


def mat_shell():
    """Silicone-coated glass cloth: the blanket itself.

    Eleven layers, and the order matters because it is the order they happened
    in: the cloth is woven, coated, printed, quilted, then it spends two seasons
    being dragged over kerbs, cooked at 100 C, dropped in brake dust, scorched
    by an exhaust and finally burnt through by a hot disc.
    """
    t = NT(PFX + "Shell")
    P = t.obj_coord()
    uv = t.uv_coord(1.0, 1.0)
    face = t.attr("tb_face")
    quilt = t.attr("tb_quilt")
    cav = t.attr("tb_cav")
    wear = t.attr("tb_wear")
    grime = t.attr("tb_grime")
    scorch = t.attr("tb_scorch")
    prt = t.attr("tb_print")
    seam = t.attr("tb_seam")
    reg = t.attr("tb_region")
    bg = t.comb(t.attr("tb_bg_r", 2, "OBJECT"), t.attr("tb_bg_g", 2, "OBJECT"),
                t.attr("tb_bg_b", 2, "OBJECT"))
    fg = t.comb(t.attr("tb_fg_r", 2, "OBJECT"), t.attr("tb_fg_g", 2, "OBJECT"),
                t.attr("tb_fg_b", 2, "OBJECT"))

    # 1. the cloth: the team colour, knocked back into a real reflectance, with
    #    a dye-lot drift across the panel that no two blankets share
    lot = t.noise(P, 3.2, detail=3.0, rough=0.55)
    base = t.cmix(0.68, PAL["shell_dark"], bg)
    base = t.cmix(t.maprange(lot, 0.35, 0.72, 0.0, 0.28), base,
                  t.cmix(0.5, base, PAL["shell_grey"]))

    # 2. the weave, and the silicone that fills it
    wv = _weave(t, uv)
    base = t.cmix(t.maprange(wv, 0.25, 0.85, 0.0, 0.16), base,
                  t.cmix(0.5, base, PAL["shell_grey"]))

    # 3. print: an SDF threshold, so the type is sharp at any magnification
    ink = t.maprange(prt, 0.00042, -0.00042, 0.0, 1.0)
    base = t.cmix(ink, base, fg)

    # 4. the quilt: the valleys hold dirt and the crowns lose their coating
    base = t.cmix(t.math("MULTIPLY", cav, 0.55), base,
                  t.cmix(0.35, base, PAL["grime"]))
    rub = t.math("MULTIPLY", t.math("MULTIPLY", quilt, quilt), wear)
    base = t.cmix(t.math("MULTIPLY", rub, 0.75), base, PAL["glass_fibre"])

    # 5. stitching: 0.4 mm thread, 0.2 px -- colour and gloss only
    stitch = t.maprange(seam, 0.0018, 0.0006, 0.0, 1.0)
    stline = t.math("MULTIPLY", stitch,
                    t.maprange(t.wave(uv, 330.0, distortion=0.4,
                                      direction="Y"), 0.35, 0.65, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", stline, 0.8), base, PAL["thread"])

    # 6. handling: dirt collects where hands and the deck touch it
    dirtn = t.noise(P, 14.0, detail=6.0, rough=0.62)
    gm = t.math("MULTIPLY", grime,
                t.maprange(dirtn, 0.30, 0.80, 0.35, 1.25))
    base = t.cmix(t.math("MULTIPLY", gm, 0.85, clamp=True), base, PAL["grime"])

    # 7. rubber pickup: this thing lives against a hot tyre
    pick = t.spots(P, 46.0, near=0.030, far=0.115, rand=0.9)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", pick, 0.55),
                         t.attr("tb_dirtg", 2, "OBJECT")), base,
                  PAL["rubber_run"])

    # 8. scorch: silicone browns, then blackens, then goes to char
    sc = t.math("MULTIPLY", scorch,
                t.maprange(t.noise(P, 30.0, detail=5.0), 0.25, 0.85, 0.6, 1.3))
    base = t.cmix(t.maprange(sc, 0.05, 0.55, 0.0, 1.0), base, PAL["scorch_warm"])
    base = t.cmix(t.maprange(sc, 0.55, 0.95, 0.0, 1.0), base, PAL["char"])

    # 9. the inner face is aluminised and it is a different material entirely
    base = t.cmix(t.maprange(face, 0.55, 0.15, 0.0, 1.0), base, PAL["alu_face"])

    # ---- roughness: silicone is glossy, glass fibre is not, char is dead ----
    # SILICONE-COATED GLASS IS NOT PATENT LEATHER.  It is a rubbery, matt,
    # slightly waxy surface with a broad low-grazing sheen and no highlight you
    # could see a window in.  The first pass ran 0.42 base roughness at 0.42
    # specular and the blankets rendered as inflated vinyl.
    rough = t.fmix(t.maprange(wv, 0.2, 0.9, 0.0, 1.0), 0.62, 0.80)
    rough = t.fmix(t.math("MULTIPLY", rub, 0.9), rough, 0.93)
    rough = t.fmix(t.maprange(sc, 0.1, 0.9, 0.0, 1.0), rough, 0.96)
    rough = t.fmix(t.math("MULTIPLY", gm, 0.7, clamp=True), rough, 0.90)
    rough = t.fmix(ink, rough, 0.72)
    rough = t.fmix(t.maprange(face, 0.55, 0.15, 0.0, 1.0), rough, 0.42)

    # ---- bump: weave + stitch pucker + the fibre nap ------------------------
    h = t.math("ADD", t.math("MULTIPLY", wv, 0.55),
               t.math("MULTIPLY", stitch, -0.9))
    h = t.math("ADD", h, t.math("MULTIPLY",
                                t.noise(P, 260.0, detail=5.0, rough=0.7), 0.35))
    # the mid-scale rumple the mesh cannot afford: 6-14 mm of soft relief that
    # breaks the pillow crowns up so they do not read as extruded tubes
    h = t.math("ADD", h, t.math("MULTIPLY",
                                t.noise(P, 42.0, detail=6.0, rough=0.62), 0.55))
    nrm = t.bump(h, 0.70, 0.0026)

    b = t.prin(base=base, rough=rough, metal=t.fmix(
        t.maprange(face, 0.55, 0.15, 0.0, 1.0), 0.0, 0.35),
        normal=nrm, sheen=0.55, sheen_r=0.32, sheen_t=(0.55, 0.55, 0.58),
        spec=0.22, ior=1.42)
    t.out(b)
    return t.m


def mat_webbing():
    """Polyester webbing: a twill you can count the picks of at 18 px."""
    t = NT(PFX + "Webbing")
    P = t.obj_coord()
    wear = t.attr("tb_wear")
    grime = t.attr("tb_grime")
    tw = t.wave(P, 1400.0, distortion=1.8, detail=3.0, direction="Y")
    tw2 = t.wave(P, 190.0, distortion=0.6, detail=2.0, direction="X")
    weave = t.math("ADD", t.math("MULTIPLY", tw, 0.6),
                   t.math("MULTIPLY", tw2, 0.4))
    base = t.cmix(t.maprange(weave, 0.2, 0.85, 0.0, 0.35), PAL["webbing"],
                  t.cmix(0.5, PAL["webbing"], PAL["webbing_worn"]))
    base = t.cmix(t.math("MULTIPLY", wear, 0.7), base, PAL["webbing_worn"])
    dn = t.noise(P, 40.0, detail=6.0)
    base = t.cmix(t.math("MULTIPLY", grime,
                         t.maprange(dn, 0.3, 0.8, 0.4, 1.2)), base,
                  PAL["grime"])
    fuzz = t.vor(P, 2600.0, feature="F1", rand=1.0)
    rough = t.fmix(t.maprange(weave, 0.2, 0.9, 0, 1), 0.66, 0.82)
    rough = t.fmix(t.math("MULTIPLY", wear, 0.8), rough, 0.93)
    h = t.math("ADD", t.math("MULTIPLY", weave, 0.8),
               t.math("MULTIPLY", fuzz, 0.2))
    b = t.prin(base=base, rough=rough, normal=t.bump(h, 0.7, 0.0009),
               sheen=0.55, sheen_r=0.35, spec=0.32)
    t.out(b)
    return t.m


def mat_buckle():
    """Glass-filled nylon: matte, with mould flow and a lifetime of scuffs."""
    t = NT(PFX + "Buckle")
    P = t.obj_coord()
    wear = t.attr("tb_wear")
    flow = t.noise(P, 55.0, detail=4.0, rough=0.4, dist=1.2)
    base = t.cmix(t.maprange(flow, 0.35, 0.7, 0.0, 0.22), PAL["buckle"],
                  PAL["buckle_scuff"])
    scuff = t.spots(P, 320.0, near=0.040, far=0.150, rand=0.85)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", scuff, 0.7),
                         t.math("ADD", 0.25, wear)), base, PAL["buckle_scuff"])
    gl = t.noise(P, 900.0, detail=3.0)
    rough = t.fmix(t.maprange(gl, 0.3, 0.8, 0, 1), 0.44, 0.62)
    rough = t.fmix(t.math("MULTIPLY", wear, 0.8), rough, 0.72)
    b = t.prin(base=base, rough=rough,
               normal=t.bump(t.math("ADD", t.math("MULTIPLY", flow, 0.4),
                                    t.math("MULTIPLY", gl, 0.6)),
                             0.35, 0.0006), spec=0.5, ior=1.53)
    t.out(b)
    return t.m


def mat_cable():
    """Rubber cable jacket and the moulded gland: matt, dusty, scuffed."""
    t = NT(PFX + "Cable")
    P = t.obj_coord()
    grime = t.attr("tb_grime")
    n1 = t.noise(P, 700.0, detail=5.0, rough=0.65)
    n2 = t.noise(P, 90.0, detail=4.0)
    base = t.cmix(t.maprange(n2, 0.3, 0.75, 0.0, 0.25), PAL["cable"],
                  t.cmix(0.5, PAL["cable"], PAL["grime"]))
    base = t.cmix(t.math("MULTIPLY", grime, 0.8), base, PAL["grime"])
    scuff = t.spots(P, 420.0, near=0.035, far=0.140)
    base = t.cmix(t.math("MULTIPLY", scuff, 0.35), base,
                  PAL["buckle_scuff"])
    rough = t.fmix(t.maprange(n1, 0.25, 0.8, 0, 1), 0.62, 0.80)
    b = t.prin(base=base, rough=rough,
               normal=t.bump(t.math("ADD", t.math("MULTIPLY", n1, 0.7),
                                    t.math("MULTIPLY", n2, 0.3)),
                             0.4, 0.0007), spec=0.44)
    t.out(b)
    return t.m


def mat_batting():
    """Needled silica batting, seen only where the shell has burnt through.

    It is the brightest thing on the object -- 0.20-0.34 against the shell's
    0.03 -- which is exactly why a burn-through reads from 13 m.
    """
    t = NT(PFX + "Batting")
    P = t.obj_coord()
    scorch = t.attr("tb_scorch")
    fib = t.vor(P, 1800.0, feature="F1", rand=1.0)
    fib2 = t.noise(P, 420.0, detail=7.0, rough=0.75)
    base = t.cmix(t.maprange(fib2, 0.25, 0.8, 0, 1), PAL["batt_gold"],
                  PAL["batt_white"])
    base = t.cmix(t.maprange(fib, 0.06, 0.26, 0.0, 0.5), base,
                  PAL["batt_gold"])
    base = t.cmix(t.maprange(scorch, 0.4, 1.0, 0.0, 0.85), base, PAL["char"])
    b = t.prin(base=base, rough=0.94,
               normal=t.bump(t.math("ADD", t.math("MULTIPLY", fib, 0.5),
                                    t.math("MULTIPLY", fib2, 0.5)),
                             0.9, 0.0012),
               sheen=0.7, sheen_r=0.6)
    t.out(b)
    return t.m


def mat_label():
    """The sewn patch and the woven care label: the only pale cloth on it."""
    t = NT(PFX + "Label")
    P = t.obj_coord()
    prt = t.attr("tb_print")
    band = t.attr("tb_band")
    wear = t.attr("tb_wear")
    grime = t.attr("tb_grime")
    bg = t.comb(t.attr("tb_bg_r", 2, "OBJECT"), t.attr("tb_bg_g", 2, "OBJECT"),
                t.attr("tb_bg_b", 2, "OBJECT"))
    fg = t.comb(t.attr("tb_fg_r", 2, "OBJECT"), t.attr("tb_fg_g", 2, "OBJECT"),
                t.attr("tb_fg_b", 2, "OBJECT"))
    cmp_ = t.comb(t.attr("tb_cmp_r", 2, "OBJECT"),
                  t.attr("tb_cmp_g", 2, "OBJECT"),
                  t.attr("tb_cmp_b", 2, "OBJECT"))
    wv = t.wave(P, 2400.0, distortion=1.5, detail=2.0, direction="Y")
    base = t.cmix(0.55, PAL["label"], bg)
    base = t.cmix(t.maprange(wv, 0.25, 0.8, 0.0, 0.20), base, PAL["label"])
    base = t.cmix(t.maprange(prt, 0.0004, -0.0004, 0.0, 1.0), base, fg)
    base = t.cmix(band, base, cmp_)
    dn = t.noise(P, 60.0, detail=5.0)
    base = t.cmix(t.math("MULTIPLY", grime,
                         t.maprange(dn, 0.3, 0.8, 0.3, 1.1)), base, PAL["grime"])
    base = t.cmix(t.math("MULTIPLY", wear, 0.35), base, PAL["grime"])
    b = t.prin(base=base, rough=t.fmix(t.maprange(wv, 0.2, 0.9, 0, 1),
                                       0.60, 0.80),
               normal=t.bump(wv, 0.5, 0.0006), sheen=0.5, spec=0.35)
    t.out(b)
    return t.m


def mat_rubber():
    """An F1 slick.  Darker than anything else in the frame, and not uniform.

    Tread and sidewall are different surfaces and the shader knows which is
    which from `tb_region`: the sidewall keeps its mould gloss, the tread has
    been scrubbed matt and grained, and the compound band and the raised
    lettering are the two things on it that are not black.
    """
    t = NT(PFX + "Rubber")
    P = t.obj_coord()
    reg = t.attr("tb_region")
    wear = t.attr("tb_wear")
    band = t.attr("tb_band")
    letter = t.attr("tb_letter")
    grime = t.attr("tb_grime")
    cmp_ = t.comb(t.attr("tb_cmp_r", 2, "OBJECT"),
                  t.attr("tb_cmp_g", 2, "OBJECT"),
                  t.attr("tb_cmp_b", 2, "OBJECT"))
    tread = t.maprange(reg, 7.4, 7.0, 0.0, 1.0)     # 7 = tread, 8 = sidewall

    mould = t.noise(P, 260.0, detail=6.0, rough=0.6)
    base = t.cmix(t.maprange(mould, 0.3, 0.8, 0.0, 0.35), PAL["rubber_new"],
                  PAL["rubber_run"])
    base = t.cmix(t.math("MULTIPLY", wear, 0.85), base, PAL["rubber_run"])
    grain = t.wave(P, 620.0, distortion=2.6, detail=4.0, direction="X")
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", tread, wear),
                         t.maprange(grain, 0.35, 0.8, 0.0, 0.8)), base,
                  PAL["rubber_grain"])
    blue = t.noise(P, 8.0, detail=4.0)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", tread, wear),
                         t.maprange(blue, 0.55, 0.85, 0.0, 0.55)), base,
                  PAL["rubber_blue"])
    marb = t.spots(P, 340.0, near=0.030, far=0.110)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", marb, 0.65),
                         wear), base, PAL["marble"])
    base = t.cmix(band, base, cmp_)
    lt = t.maprange(letter, 0.5, -0.5, 0.0, 1.0)
    base = t.cmix(t.math("MULTIPLY", lt, 0.35), base, PAL["rubber_new"])
    # the sidewall's own history: radial draw streaks off the mould, and the
    # dull ring where a wheel gun sleeve and a hundred hands have rubbed it
    wall = t.math("SUBTRACT", 1.0, tread)
    draw = t.wave(P, 130.0, distortion=3.4, detail=5.0, direction="Y")
    base = t.cmix(t.math("MULTIPLY", wall,
                         t.maprange(draw, 0.30, 0.85, 0.0, 0.12)), base,
                  PAL["rubber_grain"])
    dn = t.noise(P, 26.0, detail=5.0)
    base = t.cmix(t.math("MULTIPLY", grime,
                         t.maprange(dn, 0.30, 0.85, 0.35, 1.05)), base,
                  PAL["grime"])
    # brake dust off the disc lands on the inboard sidewall and the bead
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", grime, 0.55),
                         t.maprange(t.noise(P, 9.0, detail=4.0),
                                    0.35, 0.8, 0.0, 1.0)), base,
                  PAL["brake_dust"])

    rough = t.fmix(tread, 0.44, 0.70)
    rough = t.fmix(t.math("MULTIPLY", tread, wear), rough, 0.86)
    rough = t.fmix(t.math("MULTIPLY", lt, 0.8), rough, 0.30)
    rough = t.fmix(t.math("MULTIPLY", band, 0.9), rough, 0.44)
    h = t.math("ADD", t.math("MULTIPLY", mould, 0.45),
               t.math("MULTIPLY", grain, t.math("MULTIPLY", tread, 0.55)))
    h = t.math("ADD", h, t.math("MULTIPLY", draw,
                                t.math("MULTIPLY", wall, 0.16)))
    b = t.prin(base=base, rough=rough, normal=t.bump(h, 0.55, 0.0011),
               spec=0.26, ior=1.52, coat=t.math("MULTIPLY", lt, 0.22),
               coat_r=0.38)
    t.out(b)
    return t.m


def mat_rim():
    """Magnesium under three stints of brake dust, which is not grey.

    Brake dust is warm, it is 0.06-0.09, it sits in the corners and it runs
    down.  `tb_dust` carries the pattern (radial gradient + gravity bias, baked
    per vertex); this shader carries what it is made of.
    """
    t = NT(PFX + "Rim")
    P = t.obj_coord()
    dust = t.attr("tb_dust")
    wear = t.attr("tb_wear")
    mach = t.wave(P, 900.0, distortion=0.5, detail=2.0, direction="X")
    base = t.cmix(t.maprange(mach, 0.3, 0.8, 0.0, 0.18), PAL["mag_paint"],
                  PAL["mag_bare"])
    grit = t.noise(P, 130.0, detail=6.0, rough=0.62)
    dm = t.math("MULTIPLY", dust, t.maprange(grit, 0.25, 0.85, 0.55, 1.55))
    base = t.cmix(t.math("MULTIPLY", dm, 0.92, clamp=True), base,
                  PAL["brake_dust"])
    heat = t.noise(P, 5.0, detail=3.0)
    base = t.cmix(t.math("MULTIPLY", t.maprange(heat, 0.5, 0.85, 0.0, 0.45),
                         dust), base, PAL["heat_tint"])
    chip = t.spots(P, 520.0, near=0.022, far=0.085, rand=0.9)
    base = t.cmix(t.math("MULTIPLY", chip, t.math("ADD", 0.15, wear)), base,
                  PAL["mag_bare"])
    # An F1 wheel is SATIN BLACK ANODISED MAGNESIUM, not polished alloy.  At
    # 0.72 metallic and 0.34 roughness the first render made the spider a bright
    # chrome fan that read as the brightest object in the frame.
    rough = t.fmix(t.maprange(mach, 0.25, 0.85, 0, 1), 0.52, 0.68)
    rough = t.fmix(t.math("MULTIPLY", dm, 0.95, clamp=True), rough, 0.92)
    # MEASURED, twice.  At 0.30 metallic the wheel face was the brightest area
    # in the frame at 0.58 sRGB against a 0.42 blanket and a 0.33 deck: an F1
    # wheel is a matt black composite-and-magnesium object and it must sit
    # BELOW the blanket, not above it.
    metal = t.fmix(t.math("MULTIPLY", dm, 0.9, clamp=True), 0.10, 0.02)
    h = t.math("ADD", t.math("MULTIPLY", mach, 0.35),
               t.math("ADD", t.math("MULTIPLY", grit, 0.45),
                      t.math("MULTIPLY", chip, 0.2)))
    b = t.prin(base=base, rough=rough, metal=metal,
               normal=t.bump(h, 0.5, 0.0009), spec=0.5)
    t.out(b)
    return t.m


def mat_velcro():
    """Hook and loop.  Two surfaces, told apart by which face they are on."""
    t = NT(PFX + "Velcro")
    P = t.obj_coord()
    face = t.attr("tb_face")
    wear = t.attr("tb_wear")
    hook = t.vor(P, 3200.0, feature="F1", rand=1.0)
    loop = t.noise(P, 2200.0, detail=7.0, rough=0.8)
    isloop = t.maprange(face, 0.4, 0.8, 0.0, 1.0)
    base = t.cmix(isloop, PAL["velcro_hook"], PAL["velcro_loop"])
    base = t.cmix(t.math("MULTIPLY", t.maprange(hook, 0.28, 0.06, 0, 1), 0.35),
                  base, PAL["webbing_worn"])
    base = t.cmix(t.math("MULTIPLY", wear, 0.5), base, PAL["grime"])
    rough = t.fmix(isloop, 0.48, 0.86)
    h = t.fmix(isloop, hook, loop)
    b = t.prin(base=base, rough=rough, normal=t.bump(h, 0.85, 0.0011),
               sheen=t.fmix(isloop, 0.2, 0.8), sheen_r=0.5, spec=0.4)
    t.out(b)
    return t.m


def mat_binding():
    """Bound edge tape: the same yarn as the webbing, a tighter weave, and it
    is the first thing on a blanket to go."""
    t = NT(PFX + "Binding")
    P = t.obj_coord()
    wear = t.attr("tb_wear")
    grime = t.attr("tb_grime")
    wv = t.wave(P, 2000.0, distortion=1.2, detail=3.0, direction="Y")
    base = t.cmix(t.maprange(wv, 0.25, 0.8, 0.0, 0.28), PAL["webbing"],
                  PAL["webbing_worn"])
    fray = t.spots(P, 1500.0, near=0.045, far=0.170)
    base = t.cmix(t.math("MULTIPLY", fray, t.math("MULTIPLY", wear, 1.1)),
                  base, PAL["glass_fibre"])
    dn = t.noise(P, 55.0, detail=5.0)
    base = t.cmix(t.math("MULTIPLY", grime, t.maprange(dn, 0.3, 0.8, 0.4, 1.2)),
                  base, PAL["grime"])
    rough = t.fmix(t.math("MULTIPLY", wear, 0.9), 0.68, 0.90)
    h = t.math("ADD", t.math("MULTIPLY", wv, 0.65),
               t.math("MULTIPLY", fray, 0.35))
    b = t.prin(base=base, rough=rough, normal=t.bump(h, 0.75, 0.0010),
               sheen=0.6, sheen_r=0.4, spec=0.34)
    t.out(b)
    return t.m


_MAT_FN = {"Shell": mat_shell, "Webbing": mat_webbing, "Buckle": mat_buckle,
           "Cable": mat_cable, "Batting": mat_batting, "Label": mat_label,
           "Rubber": mat_rubber, "Rim": mat_rim, "Velcro": mat_velcro,
           "Binding": mat_binding}


def materials():
    return [_MAT_FN[n]() for n in MATS]


# ==============================================================================
# 12.  EMIT
# ==============================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children:
        p.children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
    c = bpy.data.collections.get(COLL)
    if c:
        bpy.data.collections.remove(c)


def new_mesh(name, acc, smooth_deg=36.0):
    """The foreach_set fast path.  from_pydata on 25 M triangles took 41 min."""
    V = acc.verts()
    Q, T, QM, TM = acc.faces()
    centre = 0.5 * (V.min(axis=0) + V.max(axis=0))
    V = np.ascontiguousarray(V - centre[None, :])

    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    nq, nt = len(Q), len(T)
    nloops = 4 * nq + 3 * nt
    loops = np.empty(nloops, np.int64)
    if nq:
        loops[:4 * nq] = Q.ravel()
    if nt:
        loops[4 * nq:] = T.ravel()
    starts = np.empty(nq + nt, np.int64)
    if nq:
        starts[:nq] = np.arange(nq) * 4
    if nt:
        starts[nq:] = 4 * nq + np.arange(nt) * 3
    me.loops.add(nloops)
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nq + nt)
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.polygons.foreach_set("material_index",
                            np.concatenate([QM, TM]).astype(np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(nq + nt, np.int32))

    for k in ATTR_DEFAULT:
        if k in ("tb_u", "tb_v"):
            continue
        a = me.attributes.new(k, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(acc.attr(k)))
    uvs = np.stack([acc.attr("tb_u"), acc.attr("tb_v")], axis=1)
    uva = me.attributes.new("UVMap", "FLOAT2", "CORNER")
    uva.data.foreach_set("vector", np.ascontiguousarray(uvs[loops]).ravel())
    # tb_u / tb_v as plain floats too, so a shader can read them without a UV
    for k, col in (("tb_u", 0), ("tb_v", 1)):
        a = me.attributes.new(k, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(uvs[:, col]))

    me.validate(verbose=False)
    try:
        me.set_sharp_from_angle(angle=math.radians(smooth_deg))
    except Exception:
        pass
    return me, centre


def emit(rec, acc, mats, coll, info):
    me, centre = new_mesh(PFX + "i%02d" % rec["uid"], acc)
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(
        PFX + "i%02d_%s_%s" % (rec["uid"], rec["pose"][:4], rec["state"][:4]), me)
    ob.location = (rec["wx"] + centre[0], rec["wy"] + centre[1],
                   info["z_hub"] + centre[2])
    coll.objects.link(ob)
    # per-object decorrelation: 56 realisations of one shader, not 56 copies
    ob["tb_ofs_x"] = rr(-40.0, 40.0, rec["uid"], "ox")
    ob["tb_ofs_y"] = rr(-40.0, 40.0, rec["uid"], "oy")
    ob["tb_ofs_z"] = rr(-40.0, 40.0, rec["uid"], "oz")
    bg, fg = rec["brand_bg"], rec["brand_fg"]
    cmpc = COMPOUNDS[rec["compound"]][1]
    for k, v in (("tb_bg_r", bg[0]), ("tb_bg_g", bg[1]), ("tb_bg_b", bg[2]),
                 ("tb_fg_r", fg[0]), ("tb_fg_g", fg[1]), ("tb_fg_b", fg[2]),
                 ("tb_cmp_r", cmpc[0]), ("tb_cmp_g", cmpc[1]),
                 ("tb_cmp_b", cmpc[2]),
                 ("tb_dirtg", rec["dirt"]), ("tb_ageg", rec["age"]),
                 ("tb_wearg", rec["wear"])):
        ob[k] = float(v)
    ob["tb_item"] = ITEM
    ob["tb_uid"] = rec["uid"]
    ob["tb_state"] = rec["state"]
    ob["tb_pose"] = rec["pose"]
    ob["tb_corner"] = rec["corner"]
    ob["tb_compound"] = COMPOUNDS[rec["compound"]][0]
    ob["tb_brand"] = rec["brand"][0]
    return ob


def grade_lod(recs, anchor):
    """LOD by distance from where the lens actually is.

    Nothing here is coarser than 12.5 mm of section row and 13.5 mm of wrap
    column, which at the item's own 287 px/m is 3.6 px and 3.9 px -- so even the
    far end of a 320 m row of garages still resolves its quilt.  The near set is
    at 2.0 mm, 0.6 px.
    """
    if not anchor:
        return {r["uid"]: 0 for r in recs}
    A = np.asarray(anchor, float).reshape(-1, 3)
    out = {}
    for r in recs:
        p = np.array([r["wx"], r["wy"], r["zg"] + 0.37])
        d = float(np.min(np.linalg.norm(A - p[None, :], axis=1)))
        out[r["uid"]] = 0 if d < 24.0 else (1 if d < 70.0 else 2)
    return out


def build(lod_anchor=None, scene=None, stats=None, limit=None, uids=None,
          coll=None):
    """Emit all 56 into ``W_Item_TyreBlanket``.  One joined object per instance."""
    purge()
    root = coll or _coll(COLL)
    mats = materials()
    recs = plan()
    if uids is not None:
        recs = [r for r in recs if r["uid"] in set(uids)]
    if limit:
        recs = recs[:limit]
    lods = grade_lod(recs, lod_anchor)
    tot_tri = 0
    for r in recs:
        lod = lods[r["uid"]]
        acc, info = build_instance(r, lod=lod)
        info = stack_adjust(r, info)
        ob = emit(r, acc, mats, root, info)
        _MEASURED[r["uid"]] = info
        tot_tri += info["triangles"]
        if stats is not None:
            stats.setdefault("objects", []).append(
                dict(name=ob.name, uid=r["uid"], lod=lod,
                     tris=info["triangles"], state=r["state"], pose=r["pose"],
                     corner=r["corner"], compound=COMPOUNDS[r["compound"]][0],
                     brand=r["brand"][0], embed_m=info["embed_m"],
                     owner=r["owner"]))
        log("i%02d %-9s %-5s %-2s %-5s lod%d  %7d tris  embed %.4f m"
            % (r["uid"], r["state"], r["pose"], r["corner"],
               COMPOUNDS[r["compound"]][0], lod, info["triangles"],
               info["embed_m"]))
    log("built %d instances, %d triangles" % (len(recs), tot_tri))
    if stats is not None:
        stats["triangles"] = tot_tri
        stats["instances"] = len(recs)
    return root


# ==============================================================================
# 13.  THE PUBLIC INTERFACE
# ==============================================================================

_MEASURED = {}


def stack_adjust(rec, info):
    """A wheel laid on another wheel seats on IT, not on the deck.

    Pitch is the mean of the two axial extents measured on the built shells,
    less the 17 mm the two blankets squash between them.  Published by
    ``stack_seat`` so garage_tyre_allocation stacks the same way.
    """
    if rec.get("stack_on") is None:
        return info
    below = _MEASURED.get(rec["stack_on"])
    if not below:
        return info
    rb = plan()[rec["stack_on"]]
    ha = 0.5 * info.get("axial_width", rec["width"] * RIM_W_FRAC + 0.030)
    hb = 0.5 * below.get("axial_width", rb["width"] * RIM_W_FRAC + 0.030)
    info["z_hub"] = below["z_hub"] + ha + hb - 0.0170
    info["seated_on"] = rec["stack_on"]
    return info


def _ensure_measured(lod=2):
    """Run the geometry plan without bpy so the interface works from a shell."""
    recs = plan()
    for r in recs:
        if r["uid"] not in _MEASURED:
            _, info = build_instance(r, lod=lod, fine=False)
            _MEASURED[r["uid"]] = stack_adjust(r, info)
    return _MEASURED


def _world(uid, p):
    """local (world-oriented, hub at origin) -> world."""
    r = plan()[uid]
    i = _ensure_measured()[uid]
    return [float(p[0]) + r["wx"], float(p[1]) + r["wy"],
            float(p[2]) + i["z_hub"]]


def pose_of(uid):
    r = plan()[uid]
    return dict(uid=uid, pose=r["pose"], state=r["state"], box=r["box"],
                slot=r["slot"], corner=r["corner"], width_m=r["width"],
                has_blanket=r["has_blanket"],
                world=[r["wx"], r["wy"], _ensure_measured()[uid]["z_hub"]],
                axis=(pose_frame(r) @ np.array([1.0, 0, 0])).tolist(),
                up=(pose_frame(r) @ np.array([0, 0, 1.0])).tolist(),
                ground_z=r["zg"], ground_owner=r["owner"])


def cable_exit(uid):
    """THE GLAND.  ``tyre_blanket_controller`` starts here and not before.

    -> world position of the gland's mouth, the outward axis, the cable
    diameter, and the free end of the tail this module has already built.
    """
    i = _ensure_measured()[uid]
    if "cable" not in i:
        return None
    c = i["cable"]
    return dict(uid=uid, origin=_world(uid, c["origin"]), axis=c["axis"],
                diameter=c["diameter"],
                tail_end=_world(uid, c["tail_end"]), tail_dir=c["tail_dir"],
                route=plan()[uid]["cable_route"],
                note="I own the gland and this tail.  Start your run at "
                     "tail_end with tangent tail_dir; do not remodel the gland.")


def cable_tail(uid):
    i = _ensure_measured()[uid]
    if "cable" not in i:
        return None
    return [_world(uid, p) for p in i["cable"]["tail"]]


def cradle_footprint(uid):
    """What ``tyre_trolley`` needs to put a cradle under one of these."""
    r = plan()[uid]
    i = _ensure_measured()[uid]
    Rot = pose_frame(r)
    return dict(uid=uid, pose=r["pose"],
                blanketed_od=i.get("blanket_od", TYRE_OD),
                blanketed_od_envelope=i.get("blanket_od_envelope",
                                            i.get("blanket_od", TYRE_OD)),
                axial_width=i.get("axial_width", r["width"] + 0.030),
                axial_envelope=i.get("axial_envelope",
                                     i.get("axial_width", r["width"] + 0.03)),
                tyre_od=TYRE_OD, section_width=r["width"],
                axis=(Rot @ np.array([1.0, 0, 0])).tolist(),
                up=(Rot @ np.array([0, 0, 1.0])).tolist(),
                hub_world=[r["wx"], r["wy"], i["z_hub"]],
                ground_z=r["zg"], embed_m=i["embed_m"],
                contact_half_len=float(math.sqrt(max(
                    2.0 * TYRE_R * BASE_EMBED, 1e-9))),
                on_floor=r["pose"] in ("upright", "flat"))


def stack_seat(uid):
    """The plane a second wheel seats on when these are stacked flat."""
    r = plan()[uid]
    i = _ensure_measured()[uid]
    half = 0.5 * i.get("axial_width", r["width"] * RIM_W_FRAC + 0.030)
    squash = 0.0170 if r["has_blanket"] else 0.0
    return dict(uid=uid, half_extent_axial=half, squash=squash,
                pitch=2.0 * half - squash,
                seat_z=i["z_hub"] + (half - squash) if r["pose"].startswith("flat")
                else None)


def bare_wheel_uids():
    return [r["uid"] for r in plan() if not r["has_blanket"]]


def blanketed_uids():
    return [r["uid"] for r in plan() if r["has_blanket"]]


def compound_of(uid):
    r = plan()[uid]
    c = COMPOUNDS[r["compound"]]
    return dict(uid=uid, index=r["compound"], key=c[0], band_linear_rgb=c[1],
                tread=c[2], sidewall_code=c[3], wear=r["wear"])


def wheel_profile(corner="FL", n=120):
    """The tyre section and the rim's key radii, so a dependant that builds its
    own stack builds the SAME wheel."""
    W = corner_width(corner)
    P, N, s, tag = tyre_section(W, 0.0)
    step = max(1, len(P) // n)
    return dict(corner=corner, section_width=W, od=TYRE_OD,
                rim_diameter=RIM_D, bead_seat_r=BEAD_SEAT_R,
                flange_r=FLANGE_R, rim_half_width=W * RIM_W_FRAC * 0.5,
                hem_r=HEM_R, blanket_thickness=BLK_T,
                profile_xr=P[::step].tolist())


def carry_grip(uid):
    """The two handle loops, for ``crew_tyre_carrier_on`` / ``_off``.

    Mass is computed, not guessed: a 305/720-R18 slick on an 18 in magnesium
    wheel is 9.5 kg (front) or 11.5 kg (rear) and the blanket adds 1.7 kg.
    """
    r = plan()[uid]
    i = _ensure_measured()[uid]
    m_wheel = 9.5 if r["corner"] in ("FL", "FR") else 11.5
    out = dict(uid=uid, mass_kg=m_wheel + (1.7 if r["has_blanket"] else 0.0),
               axial_width=i.get("axial_width", r["width"] + 0.03),
               grip_diameter=i.get("blanket_od", TYRE_OD),
               handles=[])
    for h in i.get("handles", []):
        out["handles"].append(dict(path=[_world(uid, p) for p in h["path"]],
                                   normal=h["normal"]))
    return out


def hand_pads(uid, n=2):
    """The two 120 x 90 mm patches of tread a carrier's palms actually land on:
    diametrically opposite, on the band, clear of both handles."""
    r = plan()[uid]
    i = _ensure_measured()[uid]
    Rot = pose_frame(r)
    R = TYRE_R + (BLK_GAP + BLK_T if r["has_blanket"] else 0.0)
    out = []
    for k in range(n):
        th = r["theta0"] + math.pi * (0.35 + k)
        p = Rot @ np.array([0.0, R * math.cos(th), R * math.sin(th)])
        nrm = Rot @ np.array([0.0, math.cos(th), math.sin(th)])
        out.append(dict(centre=_world(uid, p), normal=nrm.tolist(),
                        size=[0.120, 0.090]))
    return out


def interface_json(path=None):
    _ensure_measured()
    recs = plan()
    d = dict(
        item=ITEM, version=1,
        contract=dict(world_contract=C.__version__,
                      filmed_at_m=FILMED_AT_M, lens_mm=LENS_MM,
                      tightest_dependant_lens_mm=DEP_LENS_MM,
                      px_per_m=PX_PER_M, px_per_m_tight=PX_PER_M_TIGHT,
                      mm_per_px_tight=MM_PER_PX, mesh_floor_m=MESH_FLOOR_M),
        geometry=dict(tyre_od=TYRE_OD, rim_diameter=RIM_D,
                      front_width=W_FRONT, rear_width=W_REAR,
                      blanket_thickness=BLK_T, hem_r=HEM_R,
                      overlap_m=OVERLAP_M, cable_diameter=CABLE_D,
                      base_embed_m=BASE_EMBED),
        profiles={c: wheel_profile(c, 60) for c in ("FL", "RL")},
        instances=[])
    for r in recs:
        e = dict(uid=r["uid"], box=r["box"], slot=r["slot"],
                 state=r["state"], pose=r["pose"], corner=r["corner"],
                 width=r["width"], compound=COMPOUNDS[r["compound"]][0],
                 brand=r["brand"][0], gen=r["gen"],
                 world=[r["wx"], r["wy"], _MEASURED[r["uid"]]["z_hub"]],
                 circuit=[r["cx"], r["cy"]], ground_z=r["zg"],
                 ground_owner=r["owner"], embed_m=_MEASURED[r["uid"]]["embed_m"],
                 pose_info=pose_of(r["uid"]),
                 cradle=cradle_footprint(r["uid"]),
                 stack=stack_seat(r["uid"]),
                 compound_info=compound_of(r["uid"]),
                 carry=carry_grip(r["uid"]),
                 hand_pads=hand_pads(r["uid"]),
                 cable=cable_exit(r["uid"]))
        d["instances"].append(e)
    d["bare_wheel_uids"] = bare_wheel_uids()
    d["blanketed_uids"] = blanketed_uids()
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(d, open(path, "w"), indent=1)
    return d


# ==============================================================================
# 14.  LIGHT, STAND-INS AND THE CAMERA THE MANIFEST SPECIFIED
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them."""
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
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2, elev %.2f deg, bearing %.2f deg; %s %+.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def _mat_stand(name, base, rough, scale, bumpy=0.4):
    """A stand-in surface.  Procedural, so the test blend has no external deps,
    and named STAND_ so the gate never mistakes it for the item."""
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    n1 = t.noise(P, scale, detail=8.0, rough=0.62)
    n2 = t.vor(P, scale * 6.0, feature="F1")
    c = t.cmix(t.maprange(n1, 0.3, 0.8, 0.0, 0.35), base,
               tuple(v * 1.5 for v in base))
    c = t.cmix(t.maprange(n2, 0.30, 0.06, 0.0, 0.25), c,
               tuple(v * 0.6 for v in base))
    r = t.fmix(t.maprange(n1, 0.25, 0.85, 0, 1), rough, min(rough + 0.18, 1.0))
    b = t.prin(base=c, rough=r, spec=0.22,
               normal=t.bump(t.math("ADD", t.math("MULTIPLY", n1, 0.6),
                                    t.math("MULTIPLY", n2, 0.4)),
                             bumpy, 0.0018))
    t.out(b)
    return t.m


def build_standins(coll, centre, span=200.0):
    """The pit-lane deck and the garage front these things stand against.

    NOT part of the item and not measured as part of it -- but the blanket is a
    matt black object in the shade of a wall taking a 12.5 deg raking key, and
    judging its material without the wall that bounces into it would be judging
    a different object.
    """
    cx, cy = C.world_to_circuit(centre[0], centre[1])
    cx = float(cx); cy = float(cy)
    n = 120
    u = np.linspace(-span, span, n)
    v = np.linspace(-span * 0.35, span * 0.35, n)
    U, V = np.meshgrid(u, v, indexing="ij")
    CX = cx + U
    CY = cy + V
    WX, WY = C.circuit_to_world(CX.ravel(), CY.ravel())
    Z = np.zeros(WX.shape)
    Vg = np.stack([WX - centre[0], WY - centre[1], Z], axis=1)
    me = bpy.data.meshes.new("STAND_Deck")
    me.from_pydata(Vg.tolist(), [], grid_quads(n, n).tolist())
    me.update()
    ob = bpy.data.objects.new("STAND_Deck", me)
    ob.location = (centre[0], centre[1], 0.0)
    ob.data.materials.append(_mat_stand("STAND_Deck",
                                        (0.0395, 0.0388, 0.0378), 0.66, 26.0))
    coll.objects.link(ob)

    # the garage front: a wall on circuit y = 23.5 with a door reveal
    wx0, wy0 = C.circuit_to_world(cx - span, GARAGE_FRONT_Y)
    ex = cdir(1.0, 0.0)
    ey = cdir(0.0, 1.0)
    pts = []
    quads = []
    L = 2.0 * span
    nx, nz = 160, 14
    zz = np.linspace(0.0, 4.6, nz)
    xx = np.linspace(0.0, L, nx)
    XX, ZZ = np.meshgrid(xx, zz, indexing="ij")
    door = (np.abs(((XX / 11.4) % 1.0) - 0.5) < 0.34) & (ZZ < 4.0)
    off = np.where(door, 0.22, 0.0)
    Pw = (np.array([wx0, wy0, 0.0])[None, None, :]
          + ex[None, None, :] * XX[:, :, None]
          + np.array([0, 0, 1.0])[None, None, :] * ZZ[:, :, None]
          + ey[None, None, :] * off[:, :, None])
    Pw = Pw.reshape(-1, 3) - np.array([centre[0], centre[1], 0.0])
    me2 = bpy.data.meshes.new("STAND_GarageFront")
    me2.from_pydata(Pw.tolist(), [], grid_quads(nx, nz)[:, ::-1].tolist())
    me2.update()
    ob2 = bpy.data.objects.new("STAND_GarageFront", me2)
    ob2.location = (centre[0], centre[1], 0.0)
    # An F1 garage front is dark composite panelling and a roller shutter, not
    # bare concrete.  At 0.105 it measured 0.740 sRGB in the first render -- the
    # brightest thing in frame, bouncing into every blanket and making the whole
    # judgement about the wall.  0.052 is dark grey panel.
    ob2.data.materials.append(_mat_stand("STAND_Wall",
                                         (0.0335, 0.0330, 0.0322), 0.86, 9.0))
    coll.objects.link(ob2)
    return ob, ob2


def add_camera(name, loc, look, lens, coll, fstop=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.010
    cd.clip_end = 4000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    log("%s: %.4f m on a %.0f mm lens" % (name, d.length, lens))
    return ob


def hero_uid():
    """WHERE THE MACRO IS SHOT, by score and not by convenience.

    The manifest says the blanket must bulge and gape, so the hero has to be one
    that does both, with a strap tail loose, a scorch on it and a cable that is
    doing something.  It also has to be a wheel standing up in the front rank,
    because that is the only one the lens can see at 13 m.
    """
    best, bs = 0, -1e9
    for r in plan():
        if r["pose"] != "upright" or not r["has_blanket"]:
            continue
        sc = (2.6 * r["gape"] * 100.0
              + 1.4 * r["slack"] + 1.1 * r["hem_amp"] * 100.0
              + 0.9 * len(r["scorch"])
              + 0.8 * sum(1 for s in r["straps"] if s["dangle"])
              + 0.6 * (1.0 if r["state"] == "gaping" else 0.0)
              + 0.5 * r["age"] + 0.4 * r["crumple"]
              + 0.5 * (1.0 if r["cable_route"] == "coil" else 0.0)
              + 0.3 * (1.0 if any(s["through"] for s in r["scorch"]) else 0.0))
        if sc > bs:
            best, bs = r["uid"], sc
    return best


def _aim(uid):
    r = plan()[uid]
    i = _ensure_measured()[uid]
    return np.array([r["wx"], r["wy"], i["z_hub"]])


def macro_rig(coll, uid, name, lens=LENS_MM, dist=FILMED_AT_M, az_deg=34.0,
              height=1.55, aim_off=(0.0, 0.0, 0.0), fstop=None):
    """A camera at EXACTLY the manifest's distance and lens.

    `az_deg` is measured from the garage front's own outward normal: 0 is square
    on, 90 is straight down the row.  34 deg is the default because the sun is
    only 8 deg off that normal, so standing square on puts the key behind the
    lens and flattens every fold; 34 deg turns the quilt's shadow side toward
    the camera and the closure's step into a hard edge.
    """
    aim = _aim(uid) + np.asarray(aim_off, float)
    n = cdir(0.0, -1.0)
    a = math.radians(az_deg)
    d = np.array([n[0] * math.cos(a) - n[1] * math.sin(a),
                  n[0] * math.sin(a) + n[1] * math.cos(a), 0.0])
    dz = height - aim[2]
    horiz = math.sqrt(max(dist * dist - dz * dz, 0.04))
    loc = aim + d * horiz + np.array([0.0, 0.0, dz])
    return add_camera(name, tuple(float(v) for v in loc),
                      tuple(float(v) for v in aim), lens, coll, fstop)


def test_scene(samples=256, limit=None, lod0_only=False):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 13.000 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    uid = hero_uid()
    hero = plan()[uid]
    log("hero i%02d  box %d slot %d  %s/%s  %s %s  gape %.4f slack %.2f "
        "scorch %d  cable %s"
        % (uid, hero["box"], hero["slot"], hero["state"], hero["pose"],
           hero["corner"], COMPOUNDS[hero["compound"]][0], hero["gape"],
           hero["slack"], len(hero["scorch"]), hero["cable_route"]))

    _ensure_measured()
    aim = _aim(uid)
    anchor = [(aim[0], aim[1], aim[2])]
    if lod0_only:
        anchor = None
    # build() purges first, INCLUDING the item collection, so it must be the
    # one that creates it -- handing it a collection made beforehand hands it a
    # dangling StructRNA.
    root = build(lod_anchor=anchor, limit=limit)

    stand = _coll("STAND_Standins")
    cams = _coll(PFX + "Cameras")
    contract_light(scene, coll=stand)
    build_standins(stand, aim)

    # THE ACCEPTANCE SHOT: manifest nearest_camera_m and lens_at_closest_mm.
    macro = macro_rig(cams, uid, PFX + "CAM_MACRO", LENS_MM, FILMED_AT_M,
                      az_deg=34.0, height=1.55)
    # the dependant's lens at the same distance -- the tightest this item is
    # ever judged by, and the one the gland and cable have to survive
    macro_rig(cams, uid, PFX + "CAM_TIGHT", DEP_LENS_MM, FILMED_AT_M,
              az_deg=26.0, height=1.20)
    # square on: the branded face, the hem gather and the wheel in the opening
    macro_rig(cams, uid, PFX + "CAM_FACE", LENS_MM, FILMED_AT_M,
              az_deg=4.0, height=0.95)
    # down the row: 14 boxes of them, and the repetition has to survive it
    macro_rig(cams, uid, PFX + "CAM_ROW", LENS_MM, FILMED_AT_M,
              az_deg=76.0, height=1.35)
    # what a tyre carrier sees, at his own 10 m
    macro_rig(cams, uid, PFX + "CAM_CARRY", 35.0, CARRY_DIST_M,
              az_deg=40.0, height=1.62)
    # MY OWN EYES ONLY -- not an acceptance shot.  0.85 m on 58 mm is
    # 4,545 px/m: one quilt stitch is 41 px and one weave pick is 1.5 px.
    macro_rig(cams, uid, PFX + "CAM_PEEP", 58.0, 0.85, az_deg=38.0,
              height=0.62, aim_off=(0.0, 0.0, 0.10), fstop=5.6)

    off = [r["uid"] for r in plan() if r["state"] == "off"]
    if off:
        macro_rig(cams, off[0], PFX + "CAM_OFF", LENS_MM, FILMED_AT_M,
                  az_deg=44.0, height=1.30)
    flat = [r["uid"] for r in plan() if r["pose"] == "flat_stack"]
    if flat:
        macro_rig(cams, flat[0], PFX + "CAM_STACK", LENS_MM, FILMED_AT_M,
                  az_deg=58.0, height=1.10)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 3840
    scene.render.resolution_y = 2160
    scene.render.resolution_percentage = 100
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.006
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 4
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 15.  MEASUREMENT
# ==============================================================================

def selftest(verbose=True):
    """Measure the artefact, not the process.  Every number is a real quantity."""
    ok = True

    def chk(name, cond, msg=""):
        nonlocal ok
        if not cond:
            ok = False
        if verbose:
            print("   %-4s %-42s %s" % ("PASS" if cond else "FAIL", name, msg))
        return cond

    recs = plan()
    chk("instance count == manifest", len(recs) == 56, "%d" % len(recs))
    chk("14 boxes x 4 wheels", len({r["box"] for r in recs}) == N_BAYS)

    # ---- placement: ground from the contract, never assumed -----------------
    zbad = [r["uid"] for r in recs
            if abs(r["zg"] - C.world_ground_z(r["wx"], r["wy"])[0]) > 1e-9]
    chk("ground z from world_ground_z", not zbad, str(zbad[:5]))
    owners = sorted({r["owner"] for r in recs})
    chk("ground owned by a real surface",
        all(o and not o.startswith("build_terrain") for o in owners),
        ", ".join(owners))

    # ---- the pit lane: 12 m wide, y 11.5..23.5.  Nothing on the fast lane ---
    ys = [r["cy"] for r in recs]
    chk("inside the pit lane working strip",
        min(ys) > PIT_LANE_Y0 + 8.0 and max(ys) < GARAGE_FRONT_Y - 0.3,
        "circuit y %.3f .. %.3f" % (min(ys), max(ys)))
    xs = [r["cx"] for r in recs]
    chk("along the garage frontage",
        min(xs) > GARAGE_X0 - 2.0 and max(xs) < GARAGE_X1 + 3.0,
        "circuit x %.1f .. %.1f" % (min(xs), max(xs)))

    # ---- variation is GEOMETRY -------------------------------------------
    st = {}
    for r in recs:
        st[r["state"]] = st.get(r["state"], 0) + 1
    chk("all five blanket states present", len(st) >= 5, str(st))
    chk("both sections built",
        len({r["width"] for r in recs}) == 2,
        "front %d, rear %d" % (sum(1 for r in recs if r["width"] == W_FRONT),
                               sum(1 for r in recs if r["width"] == W_REAR)))
    chk("three quilt generations", len({r["gen"] for r in recs}) == 3)
    chk(">= 4 compounds", len({r["compound"] for r in recs}) >= 4)
    chk("14 brands, all from the brand book",
        len({r["brand"][0] for r in recs}) == N_BAYS
        and all(r["brand"] in brands() for r in recs))

    # ---- the built geometry ------------------------------------------------
    sample = [0, 1, 2, 3, hero_uid()]
    sample += [r["uid"] for r in recs if r["state"] == "off"][:1]
    sample += [r["uid"] for r in recs if r["pose"] == "flat"][:1]
    sample += [r["uid"] for r in recs if not r["has_blanket"]][:1]
    sample = sorted(set(sample))
    tris, p10s, embeds, pens = [], [], [], []
    for uid in sample:
        r = recs[uid]
        acc, info = build_instance(r, lod=0)
        V = acc.verts()
        Q, T, _, _ = acc.faces()
        tris.append(acc.tris())
        embeds.append(info["embed_m"])
        e = []
        if len(Q):
            for k in range(4):
                e.append(np.linalg.norm(V[Q[:, k]] - V[Q[:, (k + 1) % 4]],
                                        axis=1))
        el = np.concatenate(e) if e else np.zeros(1)
        p10s.append(float(np.percentile(el, 10)))
        # THE FABRIC MUST NOT BE INSIDE THE TYRE.  Measured on the SHELL
        # vertices only -- selected by the baked `tb_region`, because the acc
        # also holds the rim, whose spokes are legitimately at r = 0.10 and
        # would make this check meaningless (and did, first time round).  Only
        # the states whose blanket is still fully wrapped are eligible: a sheet
        # a mechanic has pulled off is under no obligation to clear anything.
        if r["state"] in ("fitted", "gaping"):
            Rot = pose_frame(r)
            Vl = V @ Rot
            ax = Vl[:, 0]
            rad = np.hypot(Vl[:, 1], Vl[:, 2])
            regv = acc.attr("tb_region")
            fabric = (regv < 3.5)                       # shell/side/hem/binding
            m = fabric & (np.abs(ax) < r["width"] * 0.42)
            if m.any():
                rt = tyre_radius_at(r["width"], ax[m], r["wear"])
                pens.append(float(np.min(rad[m] - rt)))
    chk("every sampled instance embeds >= %.3f m" % BASE_EMBED,
        min(embeds) >= BASE_EMBED - 1e-6,
        "min %.4f m over %d sampled" % (min(embeds), len(embeds)))
    chk("p10 edge resolves at the filmed distance",
        max(p10s) * PX_PER_M <= 6.0,
        "worst %.3f mm = %.2f px (limit 6 px)"
        % (max(p10s) * 1000.0, max(p10s) * PX_PER_M))
    chk("p10 edge resolves at the DEPENDANT's 58 mm lens too",
        max(p10s) * PX_PER_M_TIGHT <= 6.0,
        "worst %.2f px" % (max(p10s) * PX_PER_M_TIGHT))
    if pens:
        chk("no fabric inside the tyre", min(pens) > -0.0035,
            "worst clearance %+.4f m over %d wrapped instances"
            % (min(pens), len(pens)))
    chk("triangles per instance are not a placeholder",
        min(tris) > 60000, "min %d, max %d" % (min(tris), max(tris)))

    # ---- the letterforms actually produce artwork ---------------------------
    segs, w, hw = text_segments("MERIDIAN", 0.055)
    chk("stroke face rasterises", len(segs) > 20 and w > 0.2,
        "%d segments, %.3f m wide" % (len(segs), w))

    if bpy is not None:
        chk("no external images", not [i for i in bpy.data.images
                                       if i.source == "FILE"])
    if verbose:
        print("   sampled uids %s" % sample)
        print("   triangles/instance %d..%d" % (min(tris), max(tris)))
    return ok


def census(stats=None):
    recs = plan()
    def tally(key):
        d = {}
        for r in recs:
            k = key(r)
            d[k] = d.get(k, 0) + 1
        return dict(sorted(d.items()))
    print(">> tyre_blanket census, %d instances" % len(recs))
    print("   state    %s" % tally(lambda r: r["state"]))
    print("   pose     %s" % tally(lambda r: r["pose"]))
    print("   corner   %s" % tally(lambda r: r["corner"]))
    print("   compound %s" % tally(lambda r: COMPOUNDS[r["compound"]][0]))
    print("   quilt gen%s" % tally(lambda r: r["gen"]))
    print("   cable    %s" % tally(lambda r: r["cable_route"]))
    print("   straps   %s" % tally(lambda r: len(r["straps"])))
    print("   aero cvr %s" % tally(lambda r: r["aero_cover"]))
    print("   burnthru %s" % tally(lambda r: any(s["through"]
                                                 for s in r["scorch"])))
    print("   brands   %d distinct" % len({r["brand"][0] for r in recs}))
    if stats and "objects" in stats:
        t = [o["tris"] for o in stats["objects"]]
        print("   triangles %d total, %d..%d per instance, %d mean"
              % (sum(t), min(t), max(t), sum(t) // len(t)))
        print("   embed %.4f .. %.4f m"
              % (min(o["embed_m"] for o in stats["objects"]),
                 max(o["embed_m"] for o in stats["objects"])))


# ==============================================================================
# 16.  CLI
# ==============================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--interface", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[3840, 2160])
    ap.add_argument("--lod0", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        okk = selftest()
        print(">> STAGE RESULT: %s" % ("SELFTEST_PASS" if okk
                                       else "SELFTEST_FAIL"))
        if not (a.test or a.build or a.save or a.render or a.interface
                or a.census):
            sys.exit(0 if okk else 1)
    if a.census:
        census()
    if a.interface:
        interface_json(os.path.abspath(a.interface))
        log("interface -> %s" % a.interface)
    if a.test or a.save or a.render:
        test_scene(samples=a.samples, limit=a.limit, lod0_only=a.lod0)
    elif a.build:
        st = {}
        build(stats=st, limit=a.limit)
        census(st)
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True,
                                    relative_remap=False)
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


if __name__ == "__main__":
    main()
