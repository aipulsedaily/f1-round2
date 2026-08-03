#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tyre_wall_tyre.py — CIRCUIT VITRINE, per-item hero campaign, item ``tyre_wall_tyre``
(zone ``barriers``, wave 1, build order 106, **4 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every tyre in every tyre barrier on the circuit, built as a **closed rubber
carcass with a real cavity** — an outer surface, an inner liner, two bead toes
that bound a bore you can see through, moulded sidewall lettering that is raised
mesh, a sidewall serration band of 330 real radial ribs, cut tread, drilled
through-bolt holes with a tube through the rubber, a contact flat where it bears
on the tyre below, and the black tide-line of standing rainwater inside the bead.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 21 / 36) / 3.8 = 589.5 px/m     ->     1 px = 1.696 mm

    the 0.66 m carcass               389 px            (manifest: onscreen_px_4k 389)
    the 0.41 m bore                  242 px
    a 12 mm tread groove             7.1 px            <- must be a cut
    a 25 mm moulded capital          14.7 px           <- must be raised mesh
    a 7 mm size-code capital         4.1 px            <- must be raised mesh
    the 0.8 mm relief on a capital   0.5 px            but its SHADOW at the
                                                       contract sun (12.47 deg,
                                                       shadow ratio 4.52) is
                                                       3.6 mm = 2.1 px          <- geometry
    a 4.5 mm serration pitch         2.7 px            <- must be ribs
    an 18 mm drilled bolt hole       10.6 px           <- must be a hole
    the 6.5 mm sidewall thickness    3.8 px            <- must have thickness
    a 20 mm compression flat         11.8 px           <- must be deformation
    the water line inside the bead   a hard edge       <- baked, not painted
    rubber pebbling, 0.2-0.6 mm      0.1-0.35 px       <- shading, and it is

Everything in that list is mesh except the pebbling, which has no silhouette.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  4 items depend on it.
===============================================================================
Dependants named in the manifest, and what each of them must call.  Nothing here
needs bpy: the placement layer is pure numpy and can be imported and queried by
an agent that never opens Blender.

    tyre_wall_through_rod (600)   ``rod_sites(wall)``   one M16 rod per (column,
                                  course), its world origin, axis, length and the
                                  hole it threads.  The holes ARE DRILLED IN THE
                                  MESH — ``hole_sites(t)`` gives every one of them
                                  in world coordinates, active and legacy.  The
                                  axis is FITTED to the six hole centres it
                                  passes through and `clearance` is the measured
                                  gap to the hole wall; groups where no straight
                                  rod fits get no rod rather than a rod that
                                  fouls 3 mm of rubber.  Built: 379 on the T4
                                  wall and 317 on the transit wall.
    tyre_wall_belt_facing (60)    ``face_envelope(wall, ds)``  the bulge profile
                                  of the built face: for a run of stations, the
                                  outermost point of the tyres at 9 heights.  A
                                  belt that hangs flat is the named failure; this
                                  is the surface it has to drape over.
                                  ``belt_keep_clear()`` names the station window the
                                  macro is shot in, which must stay unbelted.
    transit_tyre_wall_stack (1)   ``WALLS["transit_south"]`` + ``tyre_sites(wall)``
                                  the whole south corridor wall, already seated on
                                  ``C.world_ground_z`` and stopped either side of
                                  the pit-exit portal.
    tyre_stack_trackside (129)    ``build_tyre_object(spec, ...)`` and
                                  ``spec_for(...)``: make your own tyres from the
                                  same four archetypes.  ``stack_column(...)``
                                  gives the seating of an upright stack including
                                  the compression each course inherits.

    Everything else anyone might need:
      ``ARCH``           the four archetypes and their real dimensions
      ``TyreSpec``       the full parameter set of one tyre (48 fields)
      ``dims_for(...)``  R, W, Rb, OD of a tyre BEFORE it is meshed, so a stack
                         can be seated without building it
      ``mat_tyre()``     the rubber, ``mat_water()`` the water in the bore
      ``ATTRS``          the 14 per-vertex attributes the material reads
      ``TOP_Z``          measured top of a 3-course wall: 1.856 m mean,
                         1.702-2.126 m (contract C.TRANSIT_SOUTH_TOP_Z = 2.00,
                         which the belt's top edge reaches)
      ``hero_station()`` where the sun rakes this wall at 72.7 deg, which is
                         where the macro is shot and where the belt must not be
      ``row_phase()``    how far across the backing row is laid
      ``rod_rows()``     which rows a through-rod actually threads

--- 1. THE FOUR ARCHETYPES ----------------------------------------------------
Dimensions agree with ``build_dressing.tyre_dims`` (which owns the trackside
stacks and the truck-tyre item) so a tyre is the same object wherever it appears.
``truck`` in a WALL is the light-truck carcass — 235/75 R17.5, OD 0.80 — because
an 11R22.5 at OD 1.05 in the bottom course puts the wall top at 2.55 m and the
contract says 2.00 (``C.TRANSIT_SOUTH_TOP_Z``).  ``ARCH['truck_heavy']`` is the
full-size one, for whoever wants it.

    kind    OD          section W   rim       tread          in the wall
    slick   0.660-0.680 0.300-0.335 13-16.5"  none, 4 wear holes  20 %
    wet     0.670-0.690 0.295-0.330 13-16.5"  4 circ + V lateral  12 %
    road    0.600-0.670 0.185-0.235 15-17"    3-4 circ + blocks   46 %
    truck   0.750-0.860 0.235-0.270 16-17.5"  5 ribs + zigzag     22 % (bottom)

--- 2. WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY ------------------
The manifest names six axes.  All six are in the MESH:

  "4 archetypes"            a different closed section, a different tread, a
                            different rim diameter, a different vertex count.
  "age"                     0..1 drives groove depth remaining, sidewall crack
                            geometry, the number of legacy bolt holes drilled in
                            it, the permanent oval set, and how much of the
                            moulding spew is still on it.
  "sidewall lettering"      a hand-built 40-glyph stroke font, extruded as
                            raised ridges: brand, size code, load/speed index,
                            TUBELESS, RADIAL, a DOT-style batch code and a
                            country of manufacture.  Every tyre draws its own,
                            so no two sidewalls carry the same string.
  "UV chalking"             bimodal, and it is the LOUDEST axis in the frame:
                            55 % of the pile has been in the wall long enough to
                            bloom grey and the rest is still black.  The ozone
                            CRAZING is shading, not geometry, and this file says
                            so rather than claiming it: a crack is 0.8 mm wide
                            and one pixel is 1.70 mm, so meshing it would be
                            sub-pixel geometry bought at the price of the
                            tessellation that pays for the lettering.  It is
                            driven by the baked `twt_crack` density so it lands
                            where a real tyre flexes.
  "compression flat at the  a real contact flat at every neighbour, MEASURED
   bottom of a stack"       from where the neighbours actually ended up: the
                            wall is packed by simulation (each course seats in
                            the valleys of the one below, each tyre resting on
                            the highest constraint it can reach), and every
                            overlap that comes out of that becomes a flat in
                            that tyre's own mesh.  Plus the ground contact on
                            the bottom course and the belt pulling the face in.
  "water line inside"       the cavity holds rainwater to the height of the bead
                            toe.  There is a water SURFACE in there on the tyres
                            that still hold it, silt on the ones that dried out,
                            and up to four evaporation tide marks above it.

--- 3. THE SEVEN LAWS ---------------------------------------------------------
 1. procedural, by hand    no image, no HDRI, no download.  The font is 40
                           glyphs of hand-written polyline.
 2. no real brands         sidewalls carry names from build_dressing's 31-brand
                           book (MERIDIAN is the invented tyre marque); the
                           size codes and the DOT-style batch codes are format,
                           not trade marks.
 3. car scale              a 2.005 m car brushing the wall sets the scuff band
                           height and the impact set of the second course.
 4. z = 0 is one plane     every seat is ``C.world_ground_z(x, y)``.
 5. embed >= 20 mm         the bottom course embeds ``C.BASE_EMBED_M`` into the
                           datum AND carries a real ground contact flat, so the
                           grazing sun cannot find a lit gap under it.
 6. recentre + TexCoord    every tyre's mesh is local to its own centre in a
                           canonical frame (+X along the wall, +Y out of the
                           face = the axle, +Z up), |P| < 0.45 m.  The material
                           reads ``TexCoord->Object`` and baked attributes.
                           ``Geometry->Position`` appears nowhere.  It DOES read
                           ``Geometry->Normal``, which is scale-free and exact,
                           for the sun-facing chalking.
 7. chunk along s          one object is one tyre, <= 0.86 m of circuit.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/tyre_wall_tyre.py -- --test \
        --save world/items/tyre_wall_tyre_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/tyre_wall_tyre.py -- --selftest
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
import itemkit as K                                               # noqa: E402

__version__ = "1.0.0"

ITEM = "tyre_wall_tyre"
COLL = "W_Item_TyreWallTyre"
PFX = "TWT_"
XPFX = "TWTSTAND_"          # stand-ins owned by OTHER items (belt, rods, ground,
                            # armco).  Deliberately NOT a prefix of PFX: the gate
                            # runs with --prefix TWT_ and must not measure one
                            # triangle of somebody else's work as mine.

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 3.8
LENS_MM = 21.0
ONSCREEN_PX_4K = 389.0
INSTANCES_DECLARED = 2255
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 589.47
PX_M = 1.0 / PX_PER_M                                        # 1.696 mm
DETAIL_LIMIT_M = 6.0 / PX_PER_M                              # 10.18 mm (hero)

BASE_EMBED_M = C.BASE_EMBED_M          # re-exported for the dependants
LAP_LEN = C.LAP

# --- where the walls are ------------------------------------------------------
# build_barriers owns the placement and these reproduce it exactly, so this
# module's tyres land on the metre of circuit that module's belt strips and
# deflector noses were built for.
T4_WALL_LAT = 13.10                     # build_barriers.T4_WALL_LAT
T4_WALL_S = (912.0, 1058.0)             # build_barriers.T4_WALL_S
T4_ROWS, T4_COURSES = 3, 3
TRANSIT_SOUTH_OFFSET = C.TRANSIT_SOUTH_OFFSET_M      # -7.0
TRANSIT_PORTAL_X = C.TRANSIT_PORTAL_X                # 58.0
TRANSIT_PORTAL_CLEAR = C.TRANSIT_PORTAL_CLEAR_M      # 2.6

# The Beat-5 hairpin station.  circuit_spec puts a 21 mm lens ON THE INSIDE KERB
# of T4 at z = +0.85 for 10.6 s while the car yaws through the corner, and the
# manifest's own note says the tyres BEHIND that camera are in shot the whole
# time.  This is the shot the item has to survive, so it is where the macro is
# taken and where the hero mesh is spent.
HERO_CAM_LAT = 9.10                     # build_barriers: camera on the inside kerb
HERO_CAM_Z = 0.85                       # circuit_spec Beat-5 vantage table
HERO_KEEP_CLEAR_M = 13.0                # half the window the belt must leave bare
_HERO_S = None

SEED = 20260729

# per-vertex attributes the material reads.  Anything constant over a whole tyre
# is an OBJECT property instead (see `_object_props`).
ATTRS = ("twt_h", "twt_water", "twt_bore", "twt_tread", "twt_wear",
         "twt_letter", "twt_serr", "twt_bead", "twt_crack", "twt_grime",
         "twt_scuff", "twt_flat", "twt_cut", "twt_ao")
OBJ_PROPS = ("twt_age", "twt_chalk", "twt_kind", "twt_seed", "twt_wet",
             "twt_silt", "twt_paint", "twt_pr", "twt_pg", "twt_pb",
             "twt_ofs_x", "twt_ofs_y", "twt_ofs_z", "twt_course")


# ==============================================================================
#  1.  DETERMINISTIC NOISE  —  byte-identical to build_barriers / armco_w_beam
# ==============================================================================
_U32 = np.uint32


def hash01(*keys):
    """FNV-1a over integer key arrays -> float64 in [0,1).  Broadcasts."""
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
    return float(hash01(*[np.array([k]) for k in keys])[0])


def rnd(a, b, *keys):
    return a + (b - a) * h01(*keys)


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
    amp, nrm, frq = 1.0, 0.0, 1.0
    for o in range(oct):
        tot += amp * vnoise1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def pnoise_ang(th, n, seed):
    """Periodic 1-D noise on a circle: exactly n lobes, so it wraps."""
    th = np.asarray(th, float)
    k = np.arange(1, 5)
    ph = hash01(k, np.full_like(k, seed)) * 2.0 * math.pi
    amp = 1.0 / k
    out = np.zeros_like(th)
    for i in range(len(k)):
        out += amp[i] * np.sin(th * (n * k[i]) + ph[i])
    return out / amp.sum()


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp01((np.asarray(x, dtype=np.float64) - e0) / max(1e-9, (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ==============================================================================
#  2.  THE BRAND BOOK  —  build_dressing's 31 invented brands, names only
# ==============================================================================
# Copied rather than imported: build_dressing builds 240 000 stones at import
# time.  Names and mark colours only, which is all a sidewall needs.  MERIDIAN is
# the film's invented tyre marque (build_dressing.TYRE_BRAND); the rest appear on
# the scrap road tyres, which is exactly how a real tyre wall reads — one wall,
# thirty marques, because the tyres came from thirty different cars.
BRAND_NAMES = [
    "VERSANT", "OCTAL", "CADENCE", "SEPTIME", "PALLAS", "TERRA NOVA", "ZEPHYR",
    "BRIAR", "NOVEM", "ORTHO", "LUMIERE", "MARQUE", "MERIDIAN", "ARDENT",
    "VOLTAIC", "KESTREL", "FONTAINE", "SABLIER", "NORDVAL", "HALCYON",
    "PRIMEUR", "OBSIDIAN", "CIRRUS", "MARENGO", "ATELIER 9", "VERITAS",
    "PYLON", "LE BREUIL", "ALTIS", "CALIBRE", "CIRCUIT VITRINE",
]
TYRE_BRAND = BRAND_NAMES.index("MERIDIAN")
# Race tyres come from the series' control supplier; road tyres do not.
ROAD_BRANDS = [i for i, n in enumerate(BRAND_NAMES)
               if n not in ("CIRCUIT VITRINE", "MERIDIAN")]

# build_dressing.COMPOUND — the fictional compound marks sprayed on race tyres.
COMPOUND = [((0.784, 0.063, 0.180), "TENDRE"), ((0.941, 0.753, 0.000), "MOYEN"),
            ((0.949, 0.949, 0.949), "DUR"), ((0.122, 0.608, 0.275), "INTER"),
            ((0.071, 0.341, 0.659), "PLUIE")]

# Model designations.  Invented words, in the shape a tyre model name has.
MODELS = ["SPRINT", "GRIP HP", "TRACTION 4", "VIATOR", "ROUTE GT", "TERRA AT",
          "CARGO S", "ENDURANCE", "SILENT 3", "ALPIN X", "URBAN E", "RALLYE",
          "CONFORT", "PISTE", "MISTRAL", "TRAVERSE"]
COUNTRIES = ["FRANCE", "ESPANA", "PORTUGAL", "ROMANIA", "TURKIYE", "POLSKA"]


# ==============================================================================
#  3.  THE FOUR ARCHETYPES
# ==============================================================================
# Each entry is the real tyre.  `rim_in` is the rim diameter in inches, which is
# what fixes the bore — the single most legible dimension on a wall of tyres seen
# face-on, and the reason a wall of one archetype reads as wallpaper.
ARCH = {
    "slick": dict(
        R=(0.330, 0.340), sect=(0.300, 0.335), rim_in=(13.0, 16.5),
        tread_frac=(0.955, 0.985),      # tread width / section width
        crown=(0.0012, 0.0030),         # crown drop at the tread edge
        depth=(0.0000, 0.0000),         # slicks have no grooves
        thick=(0.0075, 0.0100),         # sidewall thickness
        shoulder=(0.016, 0.024),
        maxw_at=(0.52, 0.62),           # where the section is widest, in Hs
        serr=(0.0035, 0.0050),
        weight=0.20),
    "wet": dict(
        R=(0.335, 0.345), sect=(0.295, 0.330), rim_in=(13.0, 16.5),
        tread_frac=(0.940, 0.975), crown=(0.0030, 0.0060),
        depth=(0.0045, 0.0090), thick=(0.0075, 0.0100),
        shoulder=(0.018, 0.026), maxw_at=(0.52, 0.62), serr=(0.0035, 0.0050),
        weight=0.12),
    "road": dict(
        R=(0.300, 0.335), sect=(0.185, 0.235), rim_in=(15.0, 17.0),
        tread_frac=(0.760, 0.845), crown=(0.0035, 0.0075),
        depth=(0.0012, 0.0070), thick=(0.0055, 0.0080),
        shoulder=(0.014, 0.022), maxw_at=(0.50, 0.60), serr=(0.0030, 0.0045),
        weight=0.46),
    "truck": dict(                      # light truck, 235/75 R17.5
        R=(0.375, 0.430), sect=(0.235, 0.270), rim_in=(16.0, 17.5),
        tread_frac=(0.800, 0.870), crown=(0.0025, 0.0055),
        depth=(0.0025, 0.0110), thick=(0.0090, 0.0135),
        shoulder=(0.020, 0.030), maxw_at=(0.48, 0.58), serr=(0.0035, 0.0055),
        weight=0.22),
    # not used in a wall; exported for whoever needs the full-size carcass
    "truck_heavy": dict(
        R=(0.480, 0.545), sect=(0.255, 0.300), rim_in=(20.0, 22.5),
        tread_frac=(0.800, 0.870), crown=(0.0025, 0.0055),
        depth=(0.0035, 0.0140), thick=(0.0110, 0.0165),
        shoulder=(0.022, 0.034), maxw_at=(0.48, 0.58), serr=(0.0035, 0.0055),
        weight=0.0),
}
WALL_KINDS = ("slick", "wet", "road", "truck")
_KIND_ID = {k: i for i, k in enumerate(("slick", "wet", "road", "truck",
                                        "truck_heavy"))}
INCH = 0.0254


def _pick_kind(u, bottom_course=False):
    """Archetype for one slot.  The bottom course of a wall is deliberately
    the heavy stuff — that is how a wall is actually built, and it is why the
    top of a 3-course wall lands on the contract's 2.00 m."""
    if bottom_course:
        return "truck" if u < 0.62 else ("road" if u < 0.90 else "slick")
    # Above the bottom course a wall is road and race tyres: a 0.86 m truck
    # carcass three courses up makes a lumpy top line, and a real builder puts
    # the heavy stuff at the bottom where it carries.
    w = np.array([ARCH[k]["weight"] for k in WALL_KINDS], float)
    w[WALL_KINDS.index("truck")] *= 0.09
    w = w / w.sum()
    return WALL_KINDS[int(np.searchsorted(np.cumsum(w), u * 0.999999))]


# ==============================================================================
#  4.  THE SPEC  —  every number one tyre is made of
# ==============================================================================

class TyreSpec(object):
    """One tyre, fully determined.  Nothing downstream may randomise anything:
    if it is not in here it does not vary, and if it is in here it varies the
    same way every build."""

    __slots__ = (
        "key", "kind", "lod", "R", "W", "Wt", "Rb", "bw", "Hs", "crown",
        "depth", "thick", "shoulder", "maxw_at", "serr_pitch", "serr_amp",
        "age", "wear", "chalk", "oval", "oval_ph", "wob", "spin",
        "flats", "ground_flat", "belt_pull", "holes", "water", "silt",
        "brand", "model", "size_text", "load_text", "country", "batch",
        "compound", "paint", "paint_col", "cracks", "cuts", "chunks", "spew",
        "twi", "n_circ", "n_lat", "lat_ang", "sipes", "course", "seat_z",
        "h_ground", "scuff", "grime", "back_lod", "fill")

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw.get(s))

    def __repr__(self):
        return ("<TyreSpec %s OD %.3f W %.3f rim %.3f age %.2f lod %d>"
                % (self.kind, 2 * self.R, self.W, 2 * self.Rb, self.age,
                   self.lod))


def dims_for(key, kind=None, bottom_course=False, scale=1.0):
    """(R, W, Rb, OD) WITHOUT building the tyre, so a stack can be seated
    before anything is meshed.  Exported: tyre_stack_trackside needs it."""
    if kind is None:
        kind = _pick_kind(h01(key, 3301), bottom_course)
    a = ARCH[kind]
    R = rnd(a["R"][0], a["R"][1], key, 400) * scale
    W = rnd(a["sect"][0], a["sect"][1], key, 401) * scale
    rim = np.clip(np.rint(rnd(a["rim_in"][0], a["rim_in"][1], key, 402) * 2.0)
                  / 2.0, 12.0, 24.0)
    Rb = rim * INCH * 0.5 * scale
    return float(R), float(W), float(Rb), float(2.0 * R)


def spec_for(key, kind=None, course=0, lod=0, bottom_course=False, scale=1.0,
             flats=(), ground_flat=0.0, h_ground=0.6, seat_z=0.0,
             belt_pull=0.0, scuff=0.0, back_lod=None, active_hole=None,
             fill=0.0):
    """The deterministic spec of one tyre.  `key` is any integer; the same key
    always gives the same tyre, which is what makes a 2 255-tyre wall
    reproducible without storing it."""
    if kind is None:
        kind = _pick_kind(h01(key, 3301), bottom_course)
    a = ARCH[kind]
    R, W, Rb, _ = dims_for(key, kind, bottom_course, scale)
    Hs = R - Rb
    if Hs < 0.055:                       # a rim that big leaves no sidewall
        Rb = R - 0.062
        Hs = R - Rb
    Wt = W * rnd(a["tread_frac"][0], a["tread_frac"][1], key, 403)
    age = clamp01(rnd(0.18, 0.98, key, 404) ** 0.85)
    wear = clamp01(rnd(0.25, 1.00, key, 405) * (0.55 + 0.55 * age))
    depth = lerp(a["depth"][1], a["depth"][0], wear)
    # a loose tyre's beads relax toward each other; a mounted one is at rim width
    bw = W * rnd(0.300, 0.370, key, 406)

    nb = len(BRAND_NAMES)
    if kind in ("slick", "wet"):
        brand = TYRE_BRAND
        model = None
        size_text = "%d/%d R%d" % (int(round(Wt * 1000)),
                                   int(round(2 * R * 1000)),
                                   int(round(2 * Rb / INCH)))
        load_text = "MOTORSPORT USE ONLY"
        compound = int(h01(key, 407) * len(COMPOUND)) % len(COMPOUND)
    else:
        brand = ROAD_BRANDS[int(h01(key, 408) * len(ROAD_BRANDS)) % len(ROAD_BRANDS)]
        model = MODELS[int(h01(key, 409) * len(MODELS)) % len(MODELS)]
        prof = int(np.clip(round(Hs / max(W, 1e-6) * 100 / 5.0) * 5, 30, 85))
        size_text = "%d/%d R%d" % (int(round(W * 1000)), prof,
                                   int(round(2 * Rb / INCH)))
        li = int(75 + h01(key, 410) * 40)
        load_text = "%d%s" % (li, "TSHVW"[int(h01(key, 411) * 5) % 5])
        compound = -1
    country = COUNTRIES[int(h01(key, 412) * len(COUNTRIES)) % len(COUNTRIES)]
    batch = "%s%s%02d%02d" % (
        "ABCDEFHJKLMNPRTUVWXY"[int(h01(key, 413) * 20) % 20],
        "0123456789"[int(h01(key, 414) * 10) % 10],
        int(1 + h01(key, 415) * 52), int(14 + h01(key, 416) * 12))

    # --- tread pattern --------------------------------------------------------
    if kind == "road":
        n_circ = 3 + (h01(key, 420) > 0.45)
        n_lat = int(rnd(46, 76, key, 421))
        lat_ang = rnd(18.0, 42.0, key, 422)
        sipes = int(rnd(2, 5, key, 423))
    elif kind == "truck":
        n_circ = 4 + (h01(key, 420) > 0.55)
        n_lat = int(rnd(58, 92, key, 421))
        lat_ang = rnd(4.0, 16.0, key, 422)
        sipes = 0
    elif kind == "wet":
        n_circ = 4
        n_lat = int(rnd(34, 46, key, 421))
        lat_ang = rnd(38.0, 58.0, key, 422)
        sipes = 0
    else:
        n_circ = 0
        n_lat = 0
        lat_ang = 0.0
        sipes = 0

    # --- history --------------------------------------------------------------
    # A tyre that has been in a wall for years: permanent oval set, ozone
    # crazing, cuts from the last car that hit it, chunks out of the shoulder,
    # and old bolt holes from the LAST time the wall was rebuilt.
    # Permanent set.  One tyre in eight in a wall this old has gone properly
    # soft: it is visibly out of round, its sidewalls have folded, and it is
    # the single loudest signal that these are scrap and not new stock.
    oval = rnd(0.004, 0.020, key, 430) * (0.35 + 0.9 * age)
    if h01(key, 4301) < 0.13:
        oval = rnd(0.030, 0.058, key, 4302) * (0.5 + 0.7 * age)
    n_hole = 1 + int(h01(key, 431) * 2.4 + age * 1.7)
    holes = []
    for i in range(n_hole):
        th = rnd(0.0, 2 * math.pi, key, 440 + i)
        rr = Rb + Hs * rnd(0.58, 0.84, key, 450 + i)
        if i == 0:
            # THE ACTIVE HOLE.  Every tyre in one (column, course) of a wall is
            # drilled to the SAME angle and radius, because otherwise no rod can
            # pass through three of them.  The caller owns that number; without
            # one this is a tyre that has never been in a wall.
            if active_hole is not None:
                th = float(active_hole[0])
                rr = float(np.clip(active_hole[1], Rb + Hs * 0.56,
                                   Rb + Hs * 0.86))
            else:
                th = math.pi * 0.5 + rnd(-0.35, 0.35, key, 439)
        # 22-32 mm.  A tyre-wall hole is cut with a hole saw and torn
        # wider by the rod; it is not a machined fit, and the slack is what
        # lets one straight rod pass through three hand-stacked tyres.
        ra = rnd(0.0110, 0.0160, key, 460 + i)
        holes.append((float(th), float(rr), float(ra), int(i == 0),
                      float(h01(key, 470 + i))))
    return TyreSpec(
        key=int(key), kind=kind, lod=int(lod), R=R, W=W, Wt=Wt, Rb=Rb, bw=bw,
        Hs=Hs, crown=rnd(a["crown"][0], a["crown"][1], key, 480),
        depth=depth, thick=rnd(a["thick"][0], a["thick"][1], key, 481),
        shoulder=rnd(a["shoulder"][0], a["shoulder"][1], key, 482),
        maxw_at=rnd(a["maxw_at"][0], a["maxw_at"][1], key, 483),
        serr_pitch=rnd(a["serr"][0], a["serr"][1], key, 484),
        serr_amp=rnd(0.00045, 0.00085, key, 485),
        age=age,
        wear=wear,
        # BIMODAL ON PURPOSE.  A tyre that has been in the wall for a decade is
        # grey with bloom; one that went in last winter is still black.  A
        # single continuous distribution averages the wall into one tone, which
        # is what the first macro showed: 1 287 tyres and one colour.
        chalk=(clamp01(rnd(0.62, 1.00, key, 486))
               if h01(key, 4861) < 0.55 else
               clamp01(rnd(0.02, 0.26, key, 486))) * (0.35 + 0.75 * age),
        oval=oval, oval_ph=rnd(0, math.pi, key, 487),
        wob=rnd(0.0020, 0.0075, key, 488) * (0.4 + age),
        spin=rnd(0.0, 2 * math.pi, key, 489),
        flats=list(flats), ground_flat=float(ground_flat),
        belt_pull=float(belt_pull), holes=holes,
        water=float(h01(key, 490)), silt=float(h01(key, 491)),
        brand=brand, model=model, size_text=size_text, load_text=load_text,
        country=country, batch=batch, compound=compound,
        paint=float(h01(key, 492)),
        paint_col=COMPOUND[compound][0] if compound >= 0 else
        COMPOUND[int(h01(key, 493) * len(COMPOUND)) % len(COMPOUND)][0],
        cracks=clamp01((age - 0.42) / 0.58) * rnd(0.4, 1.0, key, 494),
        cuts=int(h01(key, 495) * 3.2 * age),
        chunks=int(h01(key, 496) * 2.6 * age),
        spew=clamp01(1.25 - age * 1.4) * rnd(0.3, 1.0, key, 497),
        twi=(kind in ("road", "truck")),
        n_circ=int(n_circ), n_lat=int(n_lat), lat_ang=float(lat_ang),
        sipes=int(sipes), course=int(course), seat_z=float(seat_z),
        h_ground=float(h_ground), scuff=float(scuff),
        grime=clamp01(rnd(0.2, 1.0, key, 498) * (0.4 + 0.7 * age)),
        back_lod=(lod if back_lod is None else int(back_lod)),
        fill=float(fill))


# ==============================================================================
#  5.  THE STROKE FONT  —  40 glyphs, hand-written, no font file anywhere
# ==============================================================================
# Moulded sidewall type is a bold, slightly rounded sans with an even stroke
# weight — which is precisely what a stroked skeleton with a rounded ridge
# section produces.  Each glyph is a list of polylines in a unit em: x in
# [0, adv], y in [0, 1] where 1 is the cap height.  Curves are polylines because
# a 25 mm capital is 14.7 px on the 4K master and a 12-segment bowl is already
# below a pixel per segment.

def _arc_pts(cx, cy, rx, ry, a0, a1, n):
    a = np.linspace(math.radians(a0), math.radians(a1), max(2, int(n)))
    return [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in a]


def _build_font():
    A = _arc_pts
    g = {}
    g[" "] = []
    g["A"] = [[(0.02, 0.0), (0.31, 1.0), (0.60, 0.0)], [(0.13, 0.33), (0.49, 0.33)]]
    g["B"] = [[(0.06, 0.0), (0.06, 1.0), (0.34, 1.0)]
              + A(0.34, 0.755, 0.235, 0.245, 90, -90, 7) + [(0.06, 0.51)],
              [(0.06, 0.51), (0.36, 0.51)]
              + A(0.36, 0.255, 0.255, 0.255, 90, -90, 7) + [(0.06, 0.0)]]
    g["C"] = [A(0.34, 0.50, 0.29, 0.50, 52, 308, 13)]
    g["D"] = [[(0.06, 0.0), (0.06, 1.0), (0.28, 1.0)]
              + A(0.28, 0.50, 0.33, 0.50, 90, -90, 11) + [(0.06, 0.0)]]
    g["E"] = [[(0.58, 1.0), (0.06, 1.0), (0.06, 0.0), (0.58, 0.0)],
              [(0.06, 0.50), (0.46, 0.50)]]
    g["F"] = [[(0.58, 1.0), (0.06, 1.0), (0.06, 0.0)], [(0.06, 0.52), (0.46, 0.52)]]
    g["G"] = [A(0.34, 0.50, 0.29, 0.50, 52, 300, 13) + [(0.63, 0.40), (0.38, 0.40)]]
    g["H"] = [[(0.06, 0.0), (0.06, 1.0)], [(0.58, 0.0), (0.58, 1.0)],
              [(0.06, 0.50), (0.58, 0.50)]]
    g["I"] = [[(0.30, 0.0), (0.30, 1.0)]]
    g["J"] = [[(0.56, 1.0), (0.56, 0.24)] + A(0.31, 0.24, 0.25, 0.24, 0, -180, 7)]
    g["K"] = [[(0.06, 0.0), (0.06, 1.0)], [(0.58, 1.0), (0.10, 0.42)],
              [(0.24, 0.55), (0.60, 0.0)]]
    g["L"] = [[(0.06, 1.0), (0.06, 0.0), (0.56, 0.0)]]
    g["M"] = [[(0.03, 0.0), (0.03, 1.0), (0.32, 0.34), (0.61, 1.0), (0.61, 0.0)]]
    g["N"] = [[(0.06, 0.0), (0.06, 1.0), (0.58, 0.0), (0.58, 1.0)]]
    g["O"] = [A(0.33, 0.50, 0.29, 0.50, 0, 360, 17)]
    g["P"] = [[(0.06, 0.0), (0.06, 1.0), (0.34, 1.0)]
              + A(0.34, 0.755, 0.245, 0.245, 90, -90, 8) + [(0.06, 0.51)]]
    g["Q"] = [A(0.33, 0.50, 0.29, 0.50, 0, 360, 17), [(0.40, 0.22), (0.64, -0.04)]]
    g["R"] = [[(0.06, 0.0), (0.06, 1.0), (0.34, 1.0)]
              + A(0.34, 0.755, 0.245, 0.245, 90, -90, 8) + [(0.06, 0.51)],
              [(0.30, 0.51), (0.60, 0.0)]]
    g["S"] = [A(0.33, 0.755, 0.26, 0.245, 30, 175, 8)
              + A(0.33, 0.755, 0.26, 0.245, 175, 250, 4)[1:]
              + A(0.33, 0.265, 0.27, 0.265, 100, -30, 7)
              + A(0.33, 0.265, 0.27, 0.265, -30, -85, 3)[1:]]
    g["T"] = [[(0.02, 1.0), (0.62, 1.0)], [(0.32, 1.0), (0.32, 0.0)]]
    g["U"] = [[(0.06, 1.0), (0.06, 0.27)]
              + A(0.32, 0.27, 0.26, 0.27, 180, 360, 9) + [(0.58, 1.0)]]
    g["V"] = [[(0.02, 1.0), (0.32, 0.0), (0.62, 1.0)]]
    g["W"] = [[(0.00, 1.0), (0.16, 0.0), (0.32, 0.60), (0.48, 0.0), (0.64, 1.0)]]
    g["X"] = [[(0.04, 0.0), (0.60, 1.0)], [(0.04, 1.0), (0.60, 0.0)]]
    g["Y"] = [[(0.04, 1.0), (0.32, 0.50), (0.60, 1.0)], [(0.32, 0.50), (0.32, 0.0)]]
    g["Z"] = [[(0.04, 1.0), (0.60, 1.0), (0.04, 0.0), (0.60, 0.0)]]
    g["0"] = [A(0.32, 0.50, 0.27, 0.50, 0, 360, 15)]
    g["1"] = [[(0.14, 0.80), (0.33, 1.0), (0.33, 0.0)]]
    g["2"] = [A(0.32, 0.72, 0.27, 0.27, 175, -35, 9) + [(0.04, 0.0), (0.61, 0.0)]]
    g["3"] = [A(0.32, 0.745, 0.25, 0.25, 150, -80, 8),
              A(0.32, 0.255, 0.27, 0.255, 85, -150, 9)]
    g["4"] = [[(0.47, 0.0), (0.47, 1.0), (0.03, 0.28), (0.62, 0.28)]]
    g["5"] = [[(0.58, 1.0), (0.13, 1.0), (0.09, 0.58)]
              + A(0.32, 0.30, 0.27, 0.30, 95, -140, 9)]
    g["6"] = [A(0.32, 0.29, 0.27, 0.29, 0, 360, 13),
              [(0.58, 0.92)] + A(0.32, 0.60, 0.27, 0.40, 78, 175, 5)]
    g["7"] = [[(0.04, 1.0), (0.60, 1.0), (0.24, 0.0)]]
    g["8"] = [A(0.32, 0.755, 0.235, 0.245, -90, 270, 13),
              A(0.32, 0.255, 0.27, 0.255, -90, 270, 13)]
    g["9"] = [A(0.32, 0.71, 0.27, 0.29, 0, 360, 13),
              [(0.05, 0.08)] + A(0.32, 0.40, 0.27, 0.40, 258, 355, 5)]
    g["/"] = [[(0.04, -0.06), (0.56, 1.06)]]
    g["-"] = [[(0.08, 0.46), (0.54, 0.46)]]
    g["."] = [[(0.28, 0.02), (0.36, 0.02)]]
    g[","] = [[(0.32, 0.06), (0.24, -0.14)]]
    g["("] = [A(0.52, 0.50, 0.34, 0.58, 145, 215, 7)]
    g[")"] = [A(0.10, 0.50, 0.34, 0.58, 35, -35, 7)]
    g["+"] = [[(0.10, 0.48), (0.54, 0.48)], [(0.32, 0.26), (0.32, 0.70)]]
    g["*"] = [[(0.32, 0.34), (0.32, 0.74)], [(0.15, 0.44), (0.49, 0.64)],
              [(0.15, 0.64), (0.49, 0.44)]]
    g["%"] = [A(0.16, 0.80, 0.13, 0.18, 0, 360, 8),
              A(0.50, 0.20, 0.13, 0.18, 0, 360, 8), [(0.04, 0.0), (0.62, 1.0)]]
    out = {}
    for ch, strokes in g.items():
        out[ch] = [np.asarray(s, float) for s in strokes if len(s) >= 2]
    return out


FONT = _build_font()
FONT_ADV = 0.68                      # advance width in cap heights
FONT_MISSING = "-"


def text_width(s, tracking=0.0):
    return len(s) * (FONT_ADV + tracking)


# ==============================================================================
#  6.  THE CROSS-SECTION
# ==============================================================================
# The section is a CLOSED loop: outer surface from the front bead toe, out over
# the front sidewall, across the tread, down the rear sidewall to the rear bead
# toe, and then back through the INNER LINER to where it started.  It has to be
# closed because the bore is open and you look straight into the cavity — the
# manifest's own note is that the water line inside the bead is one of the two
# details that sell it, and there is no inside to put a water line in unless the
# tyre has one.
#
# Bands.  Each band is a contiguous run of the profile with its own angular
# resolution, because the serration ribs need 1 280 rings and the inner liner
# needs 64, and paying 1 280 everywhere would cost 20x for nothing.  Bands are
# stitched to each other with a fan across one profile step, so there are no
# T-junctions and no coincident rings.
B_BEAD_F, B_SERR_F, B_SIDE_F, B_SHLD_F = 0, 1, 2, 3
B_TREAD = 4
B_SHLD_B, B_SIDE_B, B_SERR_B, B_BEAD_B = 5, 6, 7, 8
B_INNER = 9

# theta multiplier per band per LOD, over the base ring count.
#   LOD0  the tyres inside 6 m of the 21 mm lens
#   LOD1  6-13 m
#   LOD2  the back rows of the wall and 13-30 m
#   LOD3  silhouette only
BAND_M = {
    0: {B_BEAD_F: 1, B_SERR_F: 10, B_SIDE_F: 1, B_SHLD_F: 2, B_TREAD: 6,
        B_SHLD_B: 2, B_SIDE_B: 1, B_SERR_B: 2, B_BEAD_B: 1, B_INNER: 1},
    1: {B_BEAD_F: 1, B_SERR_F: 6, B_SIDE_F: 1, B_SHLD_F: 2, B_TREAD: 4,
        B_SHLD_B: 1, B_SIDE_B: 1, B_SERR_B: 1, B_BEAD_B: 1, B_INNER: 1},
    2: {B_BEAD_F: 1, B_SERR_F: 1, B_SIDE_F: 1, B_SHLD_F: 1, B_TREAD: 2,
        B_SHLD_B: 1, B_SIDE_B: 1, B_SERR_B: 1, B_BEAD_B: 1, B_INNER: 1},
    3: {B_BEAD_F: 1, B_SERR_F: 1, B_SIDE_F: 1, B_SHLD_F: 1, B_TREAD: 1,
        B_SHLD_B: 1, B_SIDE_B: 1, B_SERR_B: 1, B_BEAD_B: 1, B_INNER: 1},
}
BASE_RING = {0: 128, 1: 96, 2: 64, 3: 40}
# profile sampling step, metres, per LOD.  `fine` is the front face, `back` the
# rear (which in a wall is 0.6 m inside the barrier and never seen), `inner` the
# cavity.
PROF_STEP = {
    0: dict(fine=0.0028, back=0.0055, inner=0.0170, tread=0.0060,
            serr=0.0080),
    1: dict(fine=0.0045, back=0.0080, inner=0.0220, tread=0.0080,
            serr=0.0110),
    2: dict(fine=0.0080, back=0.0130, inner=0.0300, tread=0.0130,
            serr=0.0160),
    3: dict(fine=0.0150, back=0.0220, inner=0.0450, tread=0.0230,
            serr=0.0260),
}
# A slick has no lateral grooves, so its tread band has nothing to resolve in
# theta and nothing to resolve across: 768 rings x 71 rows of perfectly smooth
# crown is 54 000 quads of nothing.  The pattern decides the budget.
SMOOTH_TREAD_STEP = 0.014


class Prof(object):
    """A 2-D profile builder in (r, y): radius, and distance along the axle."""

    def __init__(self):
        self.P = []
        self.B = []
        self.T = []          # sub-tag: 0 plain, 1 tread, 2 bore, 3 inner, 4 serr

    def _push(self, pts, band, tag):
        pts = np.asarray(pts, float)
        if len(self.P) and np.linalg.norm(pts[0] - self.P[-1]) < 1e-9:
            pts = pts[1:]
        for p in pts:
            self.P.append(np.asarray(p, float))
            self.B.append(band)
            self.T.append(tag)

    def start(self, p, band, tag=0):
        self.P.append(np.asarray(p, float))
        self.B.append(band)
        self.T.append(tag)

    def line(self, p1, step, band, tag=0):
        p0 = self.P[-1]
        p1 = np.asarray(p1, float)
        L = float(np.linalg.norm(p1 - p0))
        n = max(1, int(math.ceil(L / max(step, 1e-6))))
        self._push([p0 + (p1 - p0) * (i / n) for i in range(n + 1)], band, tag)

    def arc(self, c, rx, ry, a0, a1, step, band, tag=0):
        c = np.asarray(c, float)
        L = abs(math.radians(a1 - a0)) * 0.5 * (rx + ry)
        n = max(2, int(math.ceil(L / max(step, 1e-6))))
        self._push(_arc_pts(c[0], c[1], rx, ry, a0, a1, n + 1), band, tag)

    def curve(self, f, t0, t1, step, band, tag=0, dense=160):
        t = np.linspace(t0, t1, dense)
        Q = np.array([f(tt) for tt in t])
        d = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0),
                                                            axis=1))])
        n = max(1, int(math.ceil(d[-1] / max(step, 1e-6))))
        s = np.linspace(0.0, d[-1], n + 1)
        out = np.stack([np.interp(s, d, Q[:, 0]), np.interp(s, d, Q[:, 1])], 1)
        self._push(out, band, tag)

    def done(self):
        P = np.asarray(self.P, float)
        return P, np.asarray(self.B, int), np.asarray(self.T, int)


def _sidewall_curve(r0, y0, r1, y1, p):
    def f(t):
        return (r0 + (r1 - r0) * t, y0 + (y1 - y0) * (t ** p))
    return f


def tread_u_samples(sp, step):
    """Lateral samples across the tread, dense at every groove wall.

    Returns (u, dr_circ, kind) where u is the lateral coordinate in metres from
    the tyre centreline, dr_circ the radial cut of the CIRCUMFERENTIAL grooves at
    that u, and kind marks land (0) / wall (1) / floor (2), which the material
    reads as `twt_wear` (a groove floor never gets polished).
    """
    htw = sp.Wt * 0.5
    d = sp.depth
    U, D, K = [], [], []

    def add(u, dr, k):
        U.append(u)
        D.append(dr)
        K.append(k)

    # groove centres.  Never symmetric: a real tread pattern is asymmetric or
    # directional, and a mirrored one reads as a shader.
    gs = []
    if sp.n_circ > 0 and d > 1e-4:
        for i in range(sp.n_circ):
            f = (i + 0.5) / sp.n_circ * 2.0 - 1.0
            f += (h01(sp.key, 700 + i) - 0.5) * 0.30 / sp.n_circ
            wg = rnd(0.009, 0.017, sp.key, 710 + i) * (0.75 + 0.5 * sp.Wt / 0.2)
            dg = d * rnd(0.86, 1.0, sp.key, 720 + i)
            gs.append((f * htw * 0.86, min(wg, htw * 0.5), dg))
    gs.sort()
    edge = htw
    cur = -edge
    add(-edge, 0.0, 0)
    for (uc, wg, dg) in gs:
        wall = max(0.0006, dg * 0.14)          # 8 deg of draft
        pts = [(uc - wg * 0.5 - 0.0012, 0.0, 0),
               (uc - wg * 0.5, dg * 0.28, 1),
               (uc - wg * 0.5 + wall, dg, 2),
               (uc + wg * 0.5 - wall, dg, 2),
               (uc + wg * 0.5, dg * 0.28, 1),
               (uc + wg * 0.5 + 0.0012, 0.0, 0)]
        if pts[0][0] <= cur + 1e-4:
            continue
        # land before the groove
        n = max(1, int(math.ceil((pts[0][0] - cur) / step)))
        for i in range(1, n + 1):
            add(cur + (pts[0][0] - cur) * i / n, 0.0, 0)
        for (u, dr, k) in pts[1:]:
            add(u, dr, k)
        cur = pts[-1][0]
    n = max(1, int(math.ceil((edge - cur) / step)))
    for i in range(1, n + 1):
        add(cur + (edge - cur) * i / n, 0.0, 0)
    U = np.asarray(U)
    keep = np.concatenate([[True], np.diff(U) > 1e-5])
    return U[keep], np.asarray(D)[keep], np.asarray(K)[keep]


def section_profile(sp):
    """The closed section loop.  -> dict of arrays."""
    R, Rb, Hs, hw, htw = sp.R, sp.Rb, sp.Hs, sp.W * 0.5, sp.Wt * 0.5
    bw = sp.bw
    st = PROF_STEP[sp.lod]
    fine, back, inner = st["fine"], st["back"], st["inner"]
    r_maxw = Rb + sp.maxw_at * Hs
    r_rib = Rb + max(0.026, Hs * 0.20)                  # rim protector rib
    r_s0 = r_rib + 0.014                                # serration band
    r_s1 = r_s0 + max(0.022, Hs * 0.26)
    r_sh = R - sp.shoulder                              # shoulder tangent
    y_rib = bw + 0.010 + Hs * 0.055
    y_s0 = bw + 0.014 + Hs * 0.075
    y_sh = htw + sp.shoulder * 0.55

    p = Prof()
    # ---- front bead: the bore lip, the heel, the flange land, the rib -------
    p.start((Rb, bw * 0.66), B_BEAD_F, 2)
    p.arc((Rb + 0.0045, bw * 0.66), 0.0045, 0.0045 + 0.0025, 180, 92,
          fine * 0.7, B_BEAD_F, 2)
    p.line((Rb + 0.0085, bw + 0.0060), fine * 0.7, B_BEAD_F, 0)
    p.line((Rb + 0.019, bw + 0.0105), fine, B_BEAD_F, 0)
    p.curve(_sidewall_curve(Rb + 0.019, bw + 0.0105, r_rib, y_rib, 0.75),
            0, 1, fine, B_BEAD_F, 0)
    p.arc((r_rib, y_rib - 0.0045), 0.0052, 0.0062, 96, 20, fine * 0.6,
          B_BEAD_F, 0)
    p.curve(_sidewall_curve(p.P[-1][0], p.P[-1][1], r_s0, y_s0, 0.80),
            0, 1, fine, B_BEAD_F, 0)
    # ---- front serration band ----------------------------------------------
    p.curve(_sidewall_curve(r_s0, y_s0, r_s1,
                            y_s0 + (hw - y_s0) * ((r_s1 - r_s0) /
                                                  max(r_maxw - r_s0, 1e-6)) ** 0.62,
                            0.9), 0, 1, st["serr"], B_SERR_F, 4)
    # ---- front sidewall to the shoulder ------------------------------------
    y_s1 = p.P[-1][1]
    p.curve(_sidewall_curve(r_s1, y_s1, r_maxw, hw, 0.60), 0, 1, fine,
            B_SIDE_F, 0)
    p.curve(lambda t: (r_maxw + (r_sh - r_maxw) * t,
                       hw + (y_sh - hw) * (t ** 1.55)), 0, 1, fine,
            B_SIDE_F, 0)
    # ---- front shoulder -----------------------------------------------------
    tread_edge_r = R - sp.crown
    p.arc((r_sh, y_sh - sp.shoulder * 0.30),
          max(0.004, (tread_edge_r - r_sh)), sp.shoulder * 0.92, 0, 88,
          fine * 0.8, B_SHLD_F, 0)
    K_pre = len(p.P)
    # ---- the tread ----------------------------------------------------------
    U, Dg, Kg = tread_u_samples(
        sp, st["tread"] if sp.n_lat > 0 else max(st["tread"], SMOOTH_TREAD_STEP))
    for i in range(len(U) - 1, -1, -1):          # +y (front) to -y (rear)
        u = U[i]
        r = R - sp.crown * (abs(u) / max(htw, 1e-6)) ** 2 - Dg[i]
        p._push([(r, u)], B_TREAD, 1)
    tread_idx = (K_pre, len(p.P) - 1)
    # ---- rear shoulder, sidewall, serration, bead (mirrored, own numbers) ---
    p.arc((r_sh, -(y_sh - sp.shoulder * 0.30)),
          max(0.004, (tread_edge_r - r_sh)), sp.shoulder * 0.92, -88, 0,
          back * 0.8, B_SHLD_B, 0)
    p.curve(lambda t: (r_sh + (r_maxw - r_sh) * t,
                       -(y_sh + (hw - y_sh) * (1.0 - (1.0 - t) ** 1.55))),
            0, 1, back, B_SIDE_B, 0)
    p.curve(_sidewall_curve(r_maxw, -hw, r_s1, -y_s1, 1.0 / 0.60), 0, 1, back,
            B_SIDE_B, 0)
    p.curve(_sidewall_curve(r_s1, -y_s1, r_s0, -y_s0, 1.0 / 0.9), 0, 1,
            st["serr"] * 1.4, B_SERR_B, 4)
    p.curve(_sidewall_curve(r_s0, -y_s0, r_rib, -y_rib, 1.0 / 0.80), 0, 1,
            back, B_BEAD_B, 0)
    p.arc((r_rib, -(y_rib - 0.0045)), 0.0052, 0.0062, -20, -96, back * 0.6,
          B_BEAD_B, 0)
    p.curve(_sidewall_curve(r_rib, -y_rib, Rb + 0.019, -(bw + 0.0105),
                            1.0 / 0.75), 0, 1, back, B_BEAD_B, 0)
    p.line((Rb + 0.0085, -(bw + 0.0060)), back, B_BEAD_B, 0)
    p.arc((Rb + 0.0045, -bw * 0.66), 0.0045, 0.0045 + 0.0025, -92, -180,
          back * 0.7, B_BEAD_B, 2)
    # ---- the inner liner, all the way round the cavity ----------------------
    t_side = sp.thick
    t_crown = sp.depth + 0.0055 + 0.0060 + 0.0035 * (sp.kind == "truck")
    r_in_crown = R - sp.crown * 0.5 - t_crown
    y_in_max = max(hw - t_side * 1.35, htw * 0.55)
    p.line((Rb + 0.0065, -bw * 0.52), inner * 0.5, B_INNER, 3)
    p.curve(_sidewall_curve(Rb + 0.0065, -bw * 0.52, r_maxw * 0.99, -y_in_max,
                            0.62), 0, 1, inner, B_INNER, 3)
    p.curve(lambda t: (r_maxw * 0.99 + (r_in_crown - r_maxw * 0.99) * t,
                       -(y_in_max + (htw * 0.62 - y_in_max) * (t ** 1.4))),
            0, 1, inner, B_INNER, 3)
    p.line((r_in_crown, htw * 0.62), inner, B_INNER, 3)
    p.curve(lambda t: (r_in_crown + (r_maxw * 0.99 - r_in_crown) * t,
                       y_in_max + (htw * 0.62 - y_in_max) * ((1 - t) ** 1.4)),
            0, 1, inner, B_INNER, 3)
    p.curve(_sidewall_curve(r_maxw * 0.99, y_in_max, Rb + 0.0065, bw * 0.52,
                            1.0 / 0.62), 0, 1, inner, B_INNER, 3)
    p.line((Rb + 0.0060, bw * 0.60), inner * 0.5, B_INNER, 3)
    P, B, T = p.done()
    # close the loop: the last point must not duplicate the first
    if np.linalg.norm(P[-1] - P[0]) < 1e-6:
        P, B, T = P[:-1], B[:-1], T[:-1]
    return dict(P=P, band=B, tag=T, tread=tread_idx, r_s0=r_s0, r_s1=r_s1,
                r_maxw=r_maxw, r_rib=r_rib, r_sh=r_sh, y_s1=y_s1,
                r_in_crown=r_in_crown, U=U, Dg=Dg, Kg=Kg,
                Uj=U[::-1].copy(), Kj=Kg[::-1].copy(),
                t_side=t_side, y_in_max=y_in_max)


# ==============================================================================
#  7.  THE TREAD PATTERN IN THETA
# ==============================================================================

def lateral_cut(sp, th, u, prof):
    """Depth of the LATERAL grooves and sipes at (theta, u), metres.

    Slanted, so the phase carries a term in u; snapped to whole numbers of
    grooves so it wraps at 2 pi.  A pattern that does not wrap has a seam, and a
    seam on a 0.66 m tyre at 590 px/m is a 389 px scar.
    """
    if sp.n_lat <= 0 or sp.depth < 1e-4:
        return np.zeros_like(th)
    R = sp.R
    slant = math.tan(math.radians(sp.lat_ang)) / max(R, 1e-6)
    ph = (th + u * slant) * sp.n_lat / (2.0 * math.pi)
    f = ph - np.floor(ph)
    # groove occupies `wfrac` of the pitch, with a 1.4 mm wall
    pitch_m = 2.0 * math.pi * R / sp.n_lat
    wfrac = np.clip(rnd(0.16, 0.30, sp.key, 730) * (0.7 + 0.6 * (1 - sp.wear)),
                    0.10, 0.42)
    wall = min(0.30, 0.0014 / max(pitch_m, 1e-6) + 0.02)
    d = sp.depth * rnd(0.80, 1.0, sp.key, 731)
    if sp.kind == "wet":
        d = sp.depth
    prof_f = (smoothstep(0.0, wall, f) * (1.0 - smoothstep(wfrac - wall, wfrac, f)))
    out = d * prof_f
    # shoulder notches: the lateral groove runs OUT over the shoulder on a road
    # tyre and stops short of the centre rib on a truck tyre
    htw = sp.Wt * 0.5
    if sp.kind == "truck":
        out = out * (1.0 - smoothstep(htw * 0.30, htw * 0.10, np.abs(u)))
    elif sp.kind in ("road",):
        out = out * (0.35 + 0.65 * smoothstep(htw * 0.15, htw * 0.62, np.abs(u)))
    # sipes: 1.4 mm knife cuts across the blocks, at a finer pitch
    if sp.sipes > 0:
        n2 = sp.n_lat * (sp.sipes + 1)
        ph2 = (th + u * slant * 0.7) * n2 / (2.0 * math.pi)
        f2 = ph2 - np.floor(ph2)
        w2 = min(0.34, 0.0011 / max(2.0 * math.pi * R / n2, 1e-6))
        s = (smoothstep(0.0, w2 * 0.5, f2) *
             (1.0 - smoothstep(w2, w2 * 1.5, f2)))
        out = np.maximum(out, sp.depth * 0.80 * s *
                         (1.0 - smoothstep(htw * 0.72, htw * 0.95, np.abs(u))))
    return out


def tread_extra(sp, th, u):
    """Everything that is not the moulded pattern: the wear indicator bars, the
    slick's wear holes, flat-spotting, chunking and the moulding seam."""
    out = np.zeros_like(th)
    R = sp.R
    htw = sp.Wt * 0.5
    # TWI bars: 1.6 mm proud of the groove floor, 6 places round the tyre.
    # (they RAISE the floor, so they are negative depth and handled by caller)
    # flat spot: a tyre stored under load for years takes a set
    fs = rnd(0.0, 0.0022, sp.key, 740) * (0.3 + sp.age)
    ph = rnd(0, 2 * math.pi, sp.key, 741)
    out += fs * np.maximum(0.0, np.cos(th - ph)) ** 6
    # chunking: rubber torn out of the shoulder
    for i in range(sp.chunks):
        a = rnd(0, 2 * math.pi, sp.key, 750 + i)
        w = rnd(0.05, 0.16, sp.key, 760 + i)
        dep = rnd(0.004, 0.013, sp.key, 770 + i)
        side = 1.0 if h01(sp.key, 780 + i) > 0.5 else -1.0
        du = np.abs(u - side * htw * rnd(0.55, 0.95, sp.key, 790 + i))
        g = (np.exp(-((np.angle(np.exp(1j * (th - a)))) / w) ** 2)
             * np.exp(-(du / (htw * 0.55)) ** 2))
        out += dep * g
    return out


# ==============================================================================
#  8.  THE DEFORMATION FIELD
# ==============================================================================
# One pure spatial map from the ideal tyre to the built one, applied to EVERY
# vertex of every sub-mesh — carcass, letters, spew, water — so nothing floats
# off the surface it was moulded into.

def deform(V, sp):
    V = np.asarray(V, float)
    x, y, z = V[:, 0].copy(), V[:, 1].copy(), V[:, 2].copy()
    r = np.hypot(x, z)
    th = np.arctan2(z, x)
    safe = np.maximum(r, 1e-9)
    # the bead is a steel bundle: it does not deform.  Everything is weighted by
    # how far out of the bead it is, which is why a squashed tyre keeps a round
    # hole and only the carcass goes oval.
    w = smoothstep(0.06, 0.72, (r - sp.Rb) / max(sp.Hs, 1e-6))
    w2 = smoothstep(0.20, 0.95, (r - sp.Rb) / max(sp.Hs, 1e-6))

    # 1. permanent oval set + long-wave out-of-round
    scale = (1.0 + sp.oval * np.cos(2.0 * (th - sp.oval_ph)) * w
             + sp.wob * pnoise_ang(th, 3, sp.key % 9973) * w)
    # 2. contact flats.  q(theta) is how far in the outer surface is pushed at
    #    that angle; the whole section moves with it and the sidewall bulges out
    #    sideways, which is the read of a loaded tyre.
    bulge = np.zeros_like(th)
    for (ang, depth, hard) in list(sp.flats) + (
            [(-math.pi * 0.5, sp.ground_flat, 1.0)] if sp.ground_flat > 1e-5 else []):
        if depth <= 1e-5:
            continue
        lim = sp.R - depth
        ca = np.cos(th - ang)
        with np.errstate(divide="ignore", invalid="ignore"):
            rl = np.where(ca > 1e-6, lim / np.maximum(ca, 1e-6), 1e9)
        q = np.clip(rl / sp.R, 0.0, 1.0)
        # soften the corner of the contact patch over 3 degrees
        q = 1.0 - (1.0 - q) * smoothstep(0.0, 0.06, np.maximum(0.0, ca - lim / sp.R))
        press = (1.0 - q) * hard
        scale = scale * (1.0 - press * w)
        bulge = bulge + press
    # 3. the belt pulls the face in against the tyres behind
    if sp.belt_pull > 1e-6:
        scale = scale * (1.0 - sp.belt_pull * 0.012 * w2)
    r2 = safe * scale
    # 4. sidewall bulge from the contacts + the permanent outward creep of an
    #    old sidewall
    ybulge = (bulge * sp.R * 0.55 + sp.age * 0.0016) * w2
    y2 = y + np.sign(y) * ybulge
    # 5. sidewall dish: an old carcass is not a surface of revolution
    dish = (sp.wob * 3.2 * pnoise_ang(th * 1.0, 2, (sp.key * 7 + 13) % 9973)
            + sp.wob * 1.7 * pnoise_ang(th, 3, (sp.key * 5 + 3) % 9973)
            + sp.wob * 0.9 * pnoise_ang(th, 5, (sp.key * 11 + 5) % 9973))
    y2 = y2 + np.sign(y) * dish * w2
    out = np.stack([x / safe * r2, y2, z / safe * r2], axis=1)
    return out


# ==============================================================================
#  9.  MESH ASSEMBLY
# ==============================================================================

class MeshAcc(object):
    """Vertices, quads, tris and the per-vertex tags the material reads."""

    TAGS = ("tread", "bore", "inner", "serr", "bead", "letter", "hole",
            "u", "rnom", "wear", "cut")

    def __init__(self):
        self.V = []
        self.Q = []
        self.T = []
        self.M = []
        self.MT = []
        self.tag = {k: [] for k in self.TAGS}
        self._n = 0

    def nv(self):
        return self._n

    def add_verts(self, verts, **tags):
        n0 = self._n
        verts = np.asarray(verts, float).reshape(-1, 3)
        self.V.append(verts)
        n = len(verts)
        self._n += n
        for k in self.TAGS:
            v = tags.get(k, 0.0)
            if np.isscalar(v):
                self.tag[k].append(np.full(n, float(v)))
            else:
                self.tag[k].append(np.broadcast_to(
                    np.asarray(v, float).reshape(-1), (n,)).copy())
        return n0

    def add_faces(self, quads=None, tris=None, mat=0):
        """Faces in GLOBAL vertex indices."""
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4)
            self.Q.append(q)
            self.M.append(np.full(len(q), mat, np.int32))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3)
            self.T.append(t)
            self.MT.append(np.full(len(t), mat, np.int32))

    def add(self, verts, quads=None, tris=None, mat=0, **tags):
        n0 = self.add_verts(verts, **tags)
        if quads is not None and len(quads):
            self.add_faces(quads=np.asarray(quads, np.int64) + n0, mat=mat)
        if tris is not None and len(tris):
            self.add_faces(tris=np.asarray(tris, np.int64) + n0, mat=mat)
        return n0

    def finish(self):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self.T) if self.T else np.zeros((0, 3), np.int64)
        M = np.concatenate(self.M) if self.M else np.zeros(0, np.int32)
        MT = np.concatenate(self.MT) if self.MT else np.zeros(0, np.int32)
        tags = {k: (np.concatenate(v) if v else np.zeros(0))
                for k, v in self.tag.items()}
        return V, Q, T, M, MT, tags


def _grid_quads(ni, nj, wrap_i=True):
    """Quads of an (ni x nj) grid, wrapping in i."""
    i = np.arange(ni if wrap_i else ni - 1)
    j = np.arange(nj - 1)
    I, J = np.meshgrid(i, j, indexing="ij")
    i0 = I
    i1 = (I + 1) % ni
    a = i0 * nj + J
    b = i1 * nj + J
    c = i1 * nj + J + 1
    d = i0 * nj + J + 1
    return np.stack([a.ravel(), b.ravel(), c.ravel(), d.ravel()], axis=1)


def _zip_rings(ia, aa, ib, ab):
    """Triangulate between two closed rings of different vertex counts.

    `ia`/`ib` are global vertex indices, `aa`/`ab` their angles in [0, 2pi).
    Walks both rings advancing whichever has the nearer next angle — the same
    algorithm a triangle-strip merge uses, and it never makes a degenerate
    triangle because the two rings are never at the same radius.
    """
    na, nb = len(ia), len(ib)
    tris = []
    p = q = 0
    while p < na or q < nb:
        an = aa[(p + 1) % na] + (2 * math.pi if p + 1 >= na else 0.0)
        bn = ab[(q + 1) % nb] + (2 * math.pi if q + 1 >= nb else 0.0)
        if (p < na and (q >= nb or an <= bn)):
            tris.append((ia[p % na], ib[q % nb], ia[(p + 1) % na]))
            p += 1
        else:
            tris.append((ia[p % na], ib[q % nb], ib[(q + 1) % nb]))
            q += 1
    return np.asarray(tris, np.int64)


def _fan_between(IA, IB):
    """Quads/tris between two rings that are integer refinements of each other.

    `IA`, `IB` are GLOBAL vertex indices, |IB| = q |IA| (or the reverse); IB[k*q]
    sits at exactly IA[k] in theta.  One quad or (q+1) triangles per interval,
    which keeps the fine ring's extra vertices attached without a T-junction
    anywhere — a T-junction on a closed rubber shell is a hairline of daylight
    at a grazing sun.
    """
    IA = np.asarray(IA, np.int64)
    IB = np.asarray(IB, np.int64)
    na, nb = len(IA), len(IB)
    quads, tris = [], []
    if na == nb:
        for i in range(na):
            j = (i + 1) % na
            quads.append((IA[i], IB[i], IB[j], IA[j]))
        return np.asarray(quads, np.int64), np.zeros((0, 3), np.int64)
    if nb > na:
        q = nb // na
        for i in range(na):
            i2 = (i + 1) % na
            for k in range(q):
                tris.append((IA[i], IB[(i * q + k) % nb], IB[(i * q + k + 1) % nb]))
            tris.append((IA[i], IB[((i + 1) * q) % nb], IA[i2]))
    else:
        q = na // nb
        for i in range(nb):
            i2 = (i + 1) % nb
            for k in range(q):
                tris.append((IB[i], IA[(i * q + k + 1) % na], IA[(i * q + k) % na]))
            tris.append((IB[i], IB[i2], IA[((i + 1) * q) % na]))
    return np.zeros((0, 4), np.int64), np.asarray(tris, np.int64)


def _grid_quads_holed(ni, nj, boxes):
    """Quads of a wrapping (ni x nj) grid with rectangular bites taken out.

    Returns (quads, loops).  Each loop is the ring of grid indices immediately
    around one bite, in order, which is what the drilled hole is stitched to.
    """
    dead = np.zeros((ni, nj), bool)
    for (i0, i1, j0, j1) in boxes:
        for i in range(i0, i1 + 1):
            dead[i % ni, j0:j1 + 1] = True
    q = []
    for i in range(ni):
        i2 = (i + 1) % ni
        for j in range(nj - 1):
            if dead[i, j] or dead[i2, j] or dead[i, j + 1] or dead[i2, j + 1]:
                continue
            q.append((i * nj + j, i2 * nj + j, i2 * nj + j + 1, i * nj + j + 1))
    loops = []
    for (i0, i1, j0, j1) in boxes:
        a, b = i0 - 1, i1 + 1
        c, d = j0 - 1, j1 + 1
        ring = []
        for i in range(a, b + 1):
            ring.append(((i % ni) * nj + c))
        for j in range(c + 1, d + 1):
            ring.append(((b % ni) * nj + j))
        for i in range(b - 1, a - 1, -1):
            ring.append(((i % ni) * nj + d))
        for j in range(d - 1, c, -1):
            ring.append(((a % ni) * nj + j))
        loops.append(np.asarray(ring, np.int64))
    return np.asarray(q, np.int64), loops


NH = 24                     # vertices round a drilled bolt hole
HOLE_COUNTERSINK = 0.0012   # the drill pulls the rubber in at the entry


def _serration(sp, th, rmid):
    """The radial ribbing band on the lower sidewall.  Real pitch is 2.5-5 mm;
    at 590 px/m that is 1.5-3.0 px, which is exactly the scale that turns a
    grazing sun into a sparkle instead of a flat grey ring."""
    n = int(max(48, round(2.0 * math.pi * rmid / max(sp.serr_pitch, 1e-4))))
    return np.sin(th * n + sp.spin * 3.0), n


def _twi_bars(sp, th):
    """Tread wear indicators: 6 rubber bars moulded across the groove floor."""
    n = 6
    f = (th * n / (2.0 * math.pi)) % 1.0
    return (smoothstep(0.0, 0.06, f) * (1.0 - smoothstep(0.10, 0.16, f)))


def build_tyre_arrays(sp):
    """Every vertex of one tyre, in its own frame: +X/+Z the wheel plane,
    +Y the axle, origin the wheel centre.  -> (V, quads, tris, mat, mat_tri,
    tags, prof)."""
    prof = section_profile(sp)
    P, band, ptag = prof["P"], prof["band"], prof["tag"]
    K = len(P)
    base = BASE_RING[sp.lod]
    MULT = BAND_M[sp.lod]
    acc = MeshAcc()

    groups = []
    j = 0
    while j < K:
        b = int(band[j])
        j0 = j
        while j + 1 < K and band[j + 1] == b:
            j += 1
        groups.append([b, j0, j])
        j += 1
    if len(groups) > 1 and groups[0][0] == groups[-1][0]:
        groups[0][1] = groups[-1][1] - K            # wrap (does not happen here)
        groups.pop()

    htw = sp.Wt * 0.5
    info = []
    for (b, j0, j1) in groups:
        m = MULT[b]
        if b == B_TREAD and sp.n_lat == 0:
            m = 1                       # nothing to resolve on a smooth crown
        ni = base * m
        th = np.arange(ni) * (2.0 * math.pi / ni)
        jj = np.arange(j0, j1 + 1)
        nj = len(jj)
        r = np.tile(P[jj, 0], (ni, 1)).astype(float)
        y = np.tile(P[jj, 1], (ni, 1)).astype(float)
        TH = np.tile(th[:, None], (1, nj))
        tg = np.tile(ptag[jj], (ni, 1))

        if b == B_TREAD:
            u = y
            lat = lateral_cut(sp, TH, u, prof)
            # depth already cut by the CIRCUMFERENTIAL grooves at this profile
            # point.  A lateral groove crossing a circumferential one does not
            # get deeper, so the two combine with max(), not with a sum.
            circ = np.tile(sp.R - sp.crown * (np.abs(P[jj, 1]) /
                                              max(htw, 1e-6)) ** 2 - P[jj, 0],
                           (ni, 1))
            r = r - np.maximum(0.0, lat - circ)
            r = r - tread_extra(sp, TH, u)
            if sp.twi and sp.depth > 0.002:
                floor = np.tile((prof["Kj"][jj - j0] == 2).astype(float),
                                (ni, 1))
                r = r + 0.0016 * floor * _twi_bars(sp, TH)
        elif b in (B_SERR_F, B_SERR_B):
            rmid = 0.5 * (P[j0, 0] + P[j1, 0])
            w, nser = _serration(sp, TH, rmid)
            t = (P[jj, 0] - P[j0, 0]) / max(P[j1, 0] - P[j0, 0], 1e-6)
            win = np.tile(np.sin(np.pi * np.clip(t, 0, 1)) ** 0.6, (ni, 1))
            amp = sp.serr_amp * (1.0 - 0.55 * sp.age)
            y = y + np.sign(y) * amp * w * win
        elif b == B_INNER:
            # silt and rotted leaf litter in the bottom of the cavity
            silt = 0.0075 * sp.silt * (1.0 - 0.5 * sp.water)
            g = np.maximum(0.0, -np.sin(TH)) ** 3
            fill = silt * g * (np.tile(P[jj, 0], (ni, 1)) > (sp.R * 0.60))
            r = r - fill
            r = r - 0.0004 * (vnoise1(TH * 9.0 + np.tile(P[jj, 0] * 40.0,
                                                         (ni, 1)),
                                      sp.key % 977) - 0.5)

        # every surface gets its own fine relief so no band is a perfect
        # surface of revolution
        if b not in (B_TREAD,):
            r = r - 0.00035 * (vnoise1(TH * 17.0 + 3.0 * np.tile(P[jj, 0] * 30.0,
                                                                 (ni, 1)),
                                       (sp.key * 3 + 7) % 977) - 0.5) * 2.0

        X = np.cos(TH) * r
        Z = np.sin(TH) * r
        V = np.stack([X.ravel(), y.ravel(), Z.ravel()], axis=1)
        nb = acc.add_verts(
            V, tread=(tg == 1).ravel().astype(float),
            bore=(tg == 2).ravel().astype(float),
            inner=(tg == 3).ravel().astype(float),
            serr=(tg == 4).ravel().astype(float),
            bead=np.tile(smoothstep(sp.Rb + sp.Hs * 0.30, sp.Rb + sp.Hs * 0.05,
                                    P[jj, 0]), (ni, 1)).ravel(),
            u=y.ravel(), rnom=np.tile(P[jj, 0], (ni, 1)).ravel())
        info.append(dict(b=b, j0=j0, j1=j1, ni=ni, nj=nj, base=nb, th=th,
                         rprof=P[jj, 0], yprof=P[jj, 1]))

    # ---- faces inside each band, with the bolt holes bitten out -------------
    holes = _hole_plan(sp, prof, info)
    for gi, g in enumerate(info):
        boxes = [h["box"] for h in holes if h["gi"] == gi]
        if boxes:
            q, loops = _grid_quads_holed(g["ni"], g["nj"], boxes)
            g["loops"] = loops
        else:
            q = _grid_quads(g["ni"], g["nj"])
        acc.add_faces(quads=q + g["base"])

    # ---- fans between bands -------------------------------------------------
    for gi in range(len(info)):
        a = info[gi]
        b = info[(gi + 1) % len(info)]
        IA = a["base"] + np.arange(a["ni"]) * a["nj"] + (a["nj"] - 1)
        IB = b["base"] + np.arange(b["ni"]) * b["nj"]
        q, t = _fan_between(IA, IB)
        acc.add_faces(quads=q, tris=t)

    _drill(acc, sp, prof, info, holes)
    _letters(acc, sp, prof)
    _spew(acc, sp, prof)
    _bore_fill(acc, sp, prof)
    return acc, prof, info, holes


def _bore_fill(acc, sp, prof):
    """Leaf litter, grit and old marbles packed into the bore.

    THE BACKING ROW OF A TYRE WALL IS FULL OF RUBBISH.  Nothing sweeps it, the
    bore faces the weather, and fifteen autumns of leaf fall plus the gravel a
    car throws at it pack the hole solid.  It is also the only honest way to
    stop a tyre wall being a bundle of telescopes: bores on the bolt line are
    aligned BY CONSTRUCTION -- a rod has to pass through them -- and the second
    render showed daylight straight through three tyres.  Half a pitch of offset
    cannot close it, because the offset a course can carry (0.31 m) is smaller
    than two bore radii (0.42 m).  What closes it is what closes it in life.
    """
    if sp.fill < 0.12 or sp.lod >= 3:
        return
    Rb = sp.Rb
    nr, na = 18, 76
    depth = sp.bw * (0.10 + 0.45 * h01(sp.key, 1201))
    rr = np.linspace(0.0, Rb * 1.03, nr)
    th = np.arange(na) * (2 * math.pi / na)
    TH, RR = np.meshgrid(th, rr, indexing="ij")
    X = np.cos(TH) * RR
    Z = np.sin(TH) * RR
    # THE DISPLACEMENT IS IN X AND Z, NOT IN THETA AND R.  A polar noise field
    # on a polar grid makes a starfish, which is what the first version looked
    # like: a smooth funnel with a fan of radial creases in it.
    f = sp.fill
    lump = (0.030 * (vnoise1(X * 11.0 + Z * 7.0, sp.key % 883) - 0.5)
            + 0.017 * (vnoise1(X * 26.0 - Z * 19.0, (sp.key * 3) % 883) - 0.5)
            + 0.008 * (vnoise1(X * 61.0 + Z * 47.0, (sp.key * 7) % 883) - 0.5))
    z = (depth
         - 0.045 * f * (RR / max(Rb, 1e-6)) ** 2 * (0.5 + 0.9 * h01(sp.key, 1202))
         + lump * f * 2.0)
    # it never quite reaches the bead: there is always a rim of shadow
    z = z - 0.010 * smoothstep(Rb * 0.80, Rb * 1.03, RR)
    V = np.stack([X.ravel(), z.ravel(), Z.ravel()], axis=1)
    q = _grid_quads(na, nr, wrap_i=True)
    acc.add(V, quads=q, inner=1.0, u=z.ravel(), rnom=RR.ravel())


# ------------------------------------------------------------------ the holes
def _hole_plan(sp, prof, info):
    """Where the through-bolts are drilled, in grid indices.

    A tyre wall is bolted through the SIDEWALL, never through the bead — the
    bead is a steel bundle and a drill will not go through it — so every hole
    lands between the serration band and the shoulder.  The first hole in the
    spec is the ACTIVE one that carries this course's rod; the rest are legacy
    holes from the last time the wall was rebuilt, which is why an old tyre in a
    real barrier has four holes and one bolt.
    """
    gi_side = next((i for i, g in enumerate(info) if g["b"] == B_SIDE_F), None)
    gi_in = next((i for i, g in enumerate(info) if g["b"] == B_INNER), None)
    out = []
    if gi_side is None or gi_in is None or sp.lod >= 3:
        return out
    gs, gin = info[gi_side], info[gi_in]
    if gs["nj"] < 6 or gin["nj"] < 8:
        return out
    r_lo, r_hi = float(gs["rprof"].min()), float(gs["rprof"].max())
    # inner-liner samples on the FRONT half of the cavity, ordered by radius
    fr = np.flatnonzero(gin["yprof"] > 0.0)
    if len(fr) < 4:
        return out
    used = []
    for hi, (th, rr, a, active, hs) in enumerate(sp.holes):
        rr = float(np.clip(rr, r_lo + 2.6 * a, r_hi - 2.6 * a))
        if rr <= r_lo + a or rr >= r_hi - a:
            continue
        if any(abs(((th - t0 + math.pi) % (2 * math.pi)) - math.pi) < 0.30
               for t0 in used):
            continue
        used.append(th)
        # --- outer sidewall box ---------------------------------------------
        di = max(1, int(math.ceil(1.30 * a / (2.0 * math.pi * rr / gs["ni"]))))
        ic = int(round((th / (2.0 * math.pi)) * gs["ni"])) % gs["ni"]
        jc = int(np.argmin(np.abs(gs["rprof"] - rr)))
        dj = max(1, int(np.sum(np.abs(gs["rprof"] - rr) < 1.30 * a) // 2))
        j0, j1 = jc - dj, jc + dj
        if j0 < 1 or j1 > gs["nj"] - 2 or 2 * di + 3 >= gs["ni"]:
            continue
        box_o = (ic - di, ic + di, j0, j1)
        # --- inner liner box -------------------------------------------------
        jci = int(fr[np.argmin(np.abs(gin["rprof"][fr] - rr))])
        dji = max(1, int(np.sum(np.abs(gin["rprof"][fr] - rr) < 1.30 * a) // 2))
        ji0, ji1 = jci - dji, jci + dji
        dii = max(1, int(math.ceil(1.30 * a / (2.0 * math.pi * rr / gin["ni"]))))
        ici = int(round((th / (2.0 * math.pi)) * gin["ni"])) % gin["ni"]
        if ji0 < 1 or ji1 > gin["nj"] - 2:
            continue
        box_i = (ici - dii, ici + dii, ji0, ji1)
        out.append(dict(gi=gi_side, box=box_o, th=th, r=rr, a=a,
                        active=int(active), seed=hs, pair="outer", idx=hi))
        out.append(dict(gi=gi_in, box=box_i, th=th, r=rr, a=a,
                        active=int(active), seed=hs, pair="inner", idx=hi))
    return out


def _ring_from_loop(acc, g, loop, th, rr, a, sign, seed):
    """The canonical NH-vertex circle a drilled hole is stitched down to."""
    V = acc.V[-1] if False else None
    ph = np.arange(NH) * (2.0 * math.pi / NH)
    # ragged: a drill through rubber tears rather than cuts
    rag = 1.0 + 0.055 * (vnoise1(ph * 3.0 + seed * 11.0, int(seed * 991) % 977) - 0.5)
    aa = a * rag
    th_r = th + aa * np.cos(ph) / max(rr, 1e-6)
    r_r = rr + aa * np.sin(ph)
    return ph, th_r, r_r


def _profile_y_at(g, r, front=True):
    """Lateral coordinate of a band at radius r (monotonic in r by build)."""
    rp, yp = g["rprof"], g["yprof"]
    o = np.argsort(rp)
    return float(np.interp(r, rp[o], yp[o]))


def _drill(acc, sp, prof, info, holes):
    """Turn every planned hole into a real hole: the grid is already bitten out,
    so this stitches the bite down to a circle and runs a tube through the
    rubber to the matching hole in the inner liner."""
    if not holes:
        return
    byidx = {}
    for h in holes:
        byidx.setdefault(h["idx"], {})[h["pair"]] = h
    for idx, pair in byidx.items():
        if "outer" not in pair or "inner" not in pair:
            continue
        rings = {}
        for which in ("outer", "inner"):
            h = pair[which]
            g = info[h["gi"]]
            loops = g.get("loops")
            if not loops:
                rings = {}
                break
            # which loop belongs to this hole: the one whose box matches
            boxes = [x["box"] for x in holes if x["gi"] == h["gi"]]
            li = boxes.index(h["box"])
            loop = loops[li] + g["base"]
            ph, th_r, r_r = _ring_from_loop(acc, g, loop, h["th"], h["r"],
                                            h["a"], 1.0, h["seed"])
            y0 = _profile_y_at(g, h["r"])
            sgn = 1.0 if y0 >= 0 else -1.0
            # countersink: the rubber is pulled in at the drill entry
            y = y0 - sgn * (HOLE_COUNTERSINK if which == "outer"
                            else -HOLE_COUNTERSINK * 0.5)
            V = np.stack([np.cos(th_r) * r_r, np.full(NH, y),
                          np.sin(th_r) * r_r], axis=1)
            nb = acc.add_verts(V, hole=1.0, u=y, rnom=r_r,
                               inner=(1.0 if which == "inner" else 0.0))
            rings[which] = dict(base=nb, ph=ph, loop=loop, g=g)
            # zip the bitten rectangle down to the circle
            Vl = np.concatenate(acc.V)[loop]
            al = np.arctan2(Vl[:, 2] - math.sin(h["th"]) * h["r"],
                            Vl[:, 0] - math.cos(h["th"]) * h["r"])
            # angle in the LOCAL frame of the hole: use (dtheta*r, dr)
            rl = np.hypot(Vl[:, 0], Vl[:, 2])
            tl = np.arctan2(Vl[:, 2], Vl[:, 0])
            dt = ((tl - h["th"] + math.pi) % (2 * math.pi) - math.pi) * h["r"]
            al = np.arctan2(rl - h["r"], dt) % (2.0 * math.pi)
            o = np.argsort(al)
            tris = _zip_rings(loop[o], al[o],
                              nb + np.arange(NH), ph % (2.0 * math.pi))
            acc.add_faces(tris=tris)
        if len(rings) == 2:
            bo, bi = rings["outer"]["base"], rings["inner"]["base"]
            q = [(bo + k, bi + k, bi + (k + 1) % NH, bo + (k + 1) % NH)
                 for k in range(NH)]
            acc.add_faces(quads=np.asarray(q, np.int64))


# --------------------------------------------------------------- the lettering
def _sidewall_frame(prof, front=True):
    """(r -> y, normal) on the outer sidewall, for putting type on it."""
    P, tg, band = prof["P"], prof["tag"], prof["band"]
    m = (tg == 0) & ((P[:, 1] > 0) if front else (P[:, 1] < 0))
    m &= (band == (B_SIDE_F if front else B_SIDE_B)) | \
         (band == (B_SERR_F if front else B_SERR_B)) | \
         (band == (B_BEAD_F if front else B_BEAD_B))
    Q = P[m]
    o = np.argsort(Q[:, 0])
    r = Q[o, 0]
    y = Q[o, 1]
    keep = np.concatenate([[True], np.diff(r) > 1e-6])
    r, y = r[keep], y[keep]
    dy = np.gradient(y, r)
    nrm = np.stack([-dy, np.ones_like(dy)], axis=1)
    if not front:
        nrm = np.stack([dy, -np.ones_like(dy)], axis=1)
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    return r, y, nrm


def _ridge_strip(pts, w, h, embed):
    """A moulded ridge along a 2-D path, in (arc, radial) metres.

    Cross-section is a flat-topped ridge with 55-degree flanks — which is what
    comes out of a mould with draft on it — and the ends taper over half a
    stroke width so a letter terminal is rounded, not chiselled.
    """
    pts = np.asarray(pts, float)
    if len(pts) < 2:
        return None
    d = np.diff(pts, axis=0)
    L = np.linalg.norm(d, axis=1)
    keep = L > 1e-6
    if not keep.any():
        return None
    pts = np.concatenate([pts[:1], pts[1:][keep]])
    d = np.diff(pts, axis=0)
    L = np.linalg.norm(d, axis=1)
    T = d / L[:, None]
    # extend the ends by half a width so the cap is round
    pts = np.concatenate([[pts[0] - T[0] * w * 0.42], pts,
                          [pts[-1] + T[-1] * w * 0.42]])
    n = len(pts)
    d = np.diff(pts, axis=0)
    L = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
    T = d / L[:, None]
    Tv = np.zeros((n, 2))
    Tv[1:-1] = T[:-1] + T[1:]
    Tv[0], Tv[-1] = T[0], T[-1]
    Tv = Tv / np.maximum(np.linalg.norm(Tv, axis=1, keepdims=True), 1e-9)
    N = np.stack([-Tv[:, 1], Tv[:, 0]], axis=1)
    # miter compensation, capped so a sharp corner does not explode
    cosang = np.ones(n)
    cosang[1:-1] = np.clip((T[:-1] * T[1:]).sum(1), -0.9, 1.0)
    mit = np.clip(1.0 / np.sqrt(np.maximum(0.5 * (1.0 + cosang), 0.12)), 1.0, 2.2)
    ws = np.full(n, 1.0)
    ws[0] = ws[-1] = 0.30
    ws[1] = min(ws[1], 0.82)
    ws[-2] = min(ws[-2], 0.82)
    hs = np.full(n, 1.0)
    hs[0] = hs[-1] = 0.22
    sec = [(-0.50, 0.0), (-0.31, 1.0), (0.0, 1.06), (0.31, 1.0), (0.50, 0.0)]
    V = np.zeros((n, len(sec), 3))
    for k, (su, sv) in enumerate(sec):
        off = N * (su * w * ws[:, None] * mit[:, None])
        V[:, k, 0] = pts[:, 0] + off[:, 0]
        V[:, k, 1] = pts[:, 1] + off[:, 1]
        V[:, k, 2] = (sv * h * hs) - embed
    return V


def _text_run(sp, s, cap, r_base, th0, tracking, relief, front, prof, acc,
              stroke_w=None):
    """Lay one string round the sidewall as raised mesh."""
    if not s:
        return 0
    rr, yy, nn = _sidewall_frame(prof, front)
    if len(rr) < 4:
        return 0
    w = stroke_w if stroke_w else max(0.0013, cap * 0.165)
    cursor = 0.0
    strips = []
    for ch in s.upper():
        gl = FONT.get(ch, FONT.get(FONT_MISSING))
        for st in gl:
            p = np.asarray(st, float).copy()
            p[:, 0] = (cursor + p[:, 0]) * cap
            p[:, 1] = (p[:, 1] - 0.5) * cap
            V = _ridge_strip(p, w, relief, relief * 0.55)
            if V is not None:
                strips.append(V)
        cursor += FONT_ADV + tracking
    if not strips:
        return 0
    total = cursor * cap
    # centre the string on th0 and keep it inside one turn
    circ = 2.0 * math.pi * r_base
    if total > circ * 0.92:
        return 0
    nq = 0
    for V in strips:
        arc = V[:, :, 0] - total * 0.5
        rad = r_base + V[:, :, 1]
        up = V[:, :, 2]
        th = th0 + arc / max(r_base, 1e-6)
        y = np.interp(rad, rr, yy)
        ny = np.interp(rad, rr, nn[:, 1])
        nr = np.interp(rad, rr, nn[:, 0])
        R3 = rad + up * nr
        Y3 = y + up * ny
        P3 = np.stack([np.cos(th) * R3, Y3, np.sin(th) * R3], axis=-1)
        ni, nk = P3.shape[0], P3.shape[1]
        q = _grid_quads(ni, nk, wrap_i=False)
        acc.add(P3.reshape(-1, 3), quads=q, letter=1.0, u=Y3.ravel(),
                rnom=R3.ravel())
        nq += len(q)
    return nq


def _letters(acc, sp, prof):
    """Everything moulded into the sidewall.  Both faces, different text on
    each, because a tyre has a serial side and a brand side."""
    if sp.lod >= 3:
        return
    Hs, Rb = sp.Hs, sp.Rb
    small = 1.0 if sp.lod == 0 else 0.0
    for front in (True, False):
        if not front and sp.back_lod >= 2:
            break
        sgn = 1.0 if front else -1.0
        k = sp.key * (1 if front else 7)
        base = sp.spin + (0.0 if front else 1.1)
        brand = BRAND_NAMES[sp.brand]
        cap_b = np.clip(Hs * 0.30, 0.018, 0.040)
        r_b = Rb + Hs * 0.74
        n_rep = 2 if 2.0 * math.pi * r_b > 3.0 * text_width(brand) * cap_b else 1
        for i in range(n_rep):
            _text_run(sp, brand, cap_b, r_b, base + i * 2.0 * math.pi / n_rep,
                      0.10, 0.0011, front, prof, acc)
        if sp.model and sp.lod <= 1:
            cap_m = cap_b * 0.55
            for i in range(n_rep):
                _text_run(sp, sp.model, cap_m, r_b - cap_b * 0.95,
                          base + i * 2.0 * math.pi / n_rep + 0.02, 0.14,
                          0.0009, front, prof, acc)
        cap_s = np.clip(Hs * 0.11, 0.0075, 0.014)
        r_s = Rb + Hs * 0.40
        txt = (sp.size_text + "  " + sp.load_text) if front else (
            "DOT " + sp.batch + "  " + sp.country)
        for i in range(n_rep):
            _text_run(sp, txt, cap_s, r_s,
                      base + math.pi * 0.35 + i * 2.0 * math.pi / n_rep, 0.13,
                      0.00075, front, prof, acc)
        if small:
            cap_t = max(0.0055, Hs * 0.070)
            r_t = Rb + Hs * 0.255
            t2 = ("TUBELESS  RADIAL" if sp.kind in ("road", "truck")
                  else "MOTORSPORT")
            _text_run(sp, t2, cap_t, r_t, base + math.pi * 1.15, 0.16,
                      0.00060, front, prof, acc)
            _text_run(sp, "MADE IN " + sp.country, cap_t * 0.92,
                      r_t - cap_t * 1.5, base + math.pi * 0.72, 0.15,
                      0.00055, front, prof, acc)


def _spew(acc, sp, prof):
    """Moulding spew — the rubber whiskers left by the vent holes in the mould.

    1.5 mm across and 8-14 mm long, so 0.9 px wide and 5-8 px long: they read as
    fine hair against the sky and they are the single cheapest thing that says
    THIS IS RUBBER, NOT PLASTIC.  Worn off the tread within a hundred metres of
    driving, so they only survive on the shoulder and the sidewall — and only on
    the tyres that were not driven much before they were scrapped.
    """
    if sp.lod > 0 or sp.spew < 0.12:
        return
    n = int(6 + sp.spew * 26)
    rr, yy, nn = _sidewall_frame(prof, True)
    if len(rr) < 4:
        return
    V = []
    Q = []
    base = 0
    for i in range(n):
        th = rnd(0, 2 * math.pi, sp.key, 800 + i)
        r0 = rnd(sp.Rb + sp.Hs * 0.55, sp.R - sp.shoulder * 1.2, sp.key, 830 + i)
        L = rnd(0.006, 0.015, sp.key, 860 + i)
        w0 = rnd(0.0007, 0.0011, sp.key, 890 + i)
        y0 = float(np.interp(r0, rr, yy))
        ny = float(np.interp(r0, rr, nn[:, 1]))
        nr = float(np.interp(r0, rr, nn[:, 0]))
        # they droop: gravity plus fifteen years
        tipr = r0 + nr * L * 0.55 - L * 0.72 * (0.35 + 0.5 * h01(sp.key, 920 + i))
        tipy = y0 + ny * L * 0.62
        ns = 4
        ring = np.arange(6) * (2 * math.pi / 6)
        for s in range(ns):
            t = s / (ns - 1.0)
            rc = r0 + (tipr - r0) * t
            yc = y0 + (tipy - y0) * t
            w = w0 * (1.0 - 0.85 * t)
            cx, cz = math.cos(th) * rc, math.sin(th) * rc
            ex = np.array([-math.sin(th), 0.0, math.cos(th)])
            ey = np.array([0.0, 1.0, 0.0])
            for a in ring:
                V.append([cx + ex[0] * math.cos(a) * w,
                          yc + math.sin(a) * w,
                          cz + ex[2] * math.cos(a) * w])
        for s in range(ns - 1):
            for a in range(6):
                b = (a + 1) % 6
                Q.append((base + s * 6 + a, base + s * 6 + b,
                          base + (s + 1) * 6 + b, base + (s + 1) * 6 + a))
        base += ns * 6
    if V:
        acc.add(np.asarray(V), quads=np.asarray(Q, np.int64), letter=0.0)


# ------------------------------------------------------- the water in the bore
def water_level(sp):
    """Local z of the standing water inside the carcass.

    A tyre lying with its axis horizontal is a bucket: rain gets in through the
    bore and cannot get out again until it reaches the BEAD TOE, which is the
    lowest point of the rim of the hole.  So the water line sits at z = -Rb, a
    hard horizontal edge across the inside of the bore — and it is the detail
    the manifest says sells the shot.  Evaporation drops it and leaves tide
    marks; a tyre with a split sidewall has drained.
    """
    drop = (1.0 - sp.water) * (sp.Rb + 0.02) * 0.55
    return -sp.Rb - drop + 0.004


def _water_patch(sp, prof, VD):
    """A flat water surface clipped to the cavity, built in DEFORMED space."""
    if sp.water < 0.34:
        return None
    zw = water_level(sp)
    P, tg = prof["P"], prof["tag"]
    m = tg == 3
    rin, yin = P[m, 0], P[m, 1]
    o = np.argsort(yin)
    rin, yin = rin[o], yin[o]
    ok = rin > abs(zw) * 1.02
    if ok.sum() < 3:
        return None
    y0, y1 = float(yin[ok].min()), float(yin[ok].max())
    ny, nx = 14, 22
    ys = np.linspace(y0 * 0.985, y1 * 0.985, ny)
    rr = np.interp(ys, yin, rin)
    X = np.sqrt(np.maximum(rr ** 2 - zw ** 2, 1e-9)) * 0.995
    # THE WATER MUST NOT COME TO A POINT.  Where the cavity roof drops to the
    # water level the chord goes to zero and 22 samples collapse onto one point
    # -- 3 um edges, which are a free pass on a 10th-percentile edge check.
    # Keep only the rows with a real chord.
    keep = X > 0.012
    if keep.sum() < 3:
        return None
    ys, X = ys[keep], X[keep]
    ny = len(ys)
    t = np.linspace(-1.0, 1.0, nx)
    V = np.zeros((ny, nx, 3))
    V[:, :, 0] = X[:, None] * t[None, :]
    V[:, :, 1] = ys[:, None]
    V[:, :, 2] = zw
    q = _grid_quads(ny, nx, wrap_i=False)
    return V.reshape(-1, 3), q


def bake_attrs(sp, V, tags, world_z0):
    """The 14 per-vertex attributes.  Everything the material cannot work out
    for itself from position and normal."""
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    r = np.hypot(x, z)
    th = np.arctan2(z, x)
    frac = clamp01((r - sp.Rb) / max(sp.Hs, 1e-6))
    inner = np.maximum(tags["bore"], tags["inner"])
    zw = water_level(sp)
    A = {}
    A["twt_h"] = world_z0 + z
    A["twt_water"] = np.where(inner > 0.5, zw - z, -1.0)
    A["twt_bore"] = inner
    A["twt_tread"] = tags["tread"]
    A["twt_serr"] = tags["serr"]
    A["twt_letter"] = tags["letter"]
    A["twt_bead"] = tags["bead"]
    # tread wear: the shoulders and the centre wear differently, and a groove
    # floor is never polished because nothing ever touches it
    shoulder = clamp01(np.abs(tags["u"]) / max(sp.Wt * 0.5, 1e-6))
    prof_wear = sp.wear * (0.72 + 0.45 * (0.5 - np.abs(shoulder - 0.5)) * 2.0
                           * (0.4 + 0.6 * h01(sp.key, 950)))
    A["twt_wear"] = np.where(tags["tread"] > 0.5, clamp01(prof_wear), 0.0)
    # ozone crazing lives where the rubber flexes: the lower sidewall, and the
    # sun side.  Geometry cannot carry a 0.8 mm crack at 1.7 mm/px, so this is a
    # MASK for the shader's crack net, and it is honest about being that.
    A["twt_crack"] = (sp.cracks * (1.0 - inner)
                      * (smoothstep(0.75, 0.30, frac) * 0.8 + 0.2)
                      * (1.0 - 0.7 * tags["tread"]))
    # grime: road film thrown at the face, dust settling in every crevice
    A["twt_grime"] = clamp01(sp.grime * (0.35 + 0.65 * smoothstep(0.9, 0.1, frac))
                             + 0.35 * inner)
    # a car brushing the wall hits between 0.20 m and 0.75 m above the ground
    hh = world_z0 + z
    A["twt_scuff"] = (sp.scuff * smoothstep(0.05, 0.22, hh)
                      * (1.0 - smoothstep(0.62, 0.95, hh))
                      * clamp01((y - sp.W * 0.18) / max(sp.W * 0.2, 1e-6))
                      * (1.0 - inner))
    # how hard this bit of carcass is squashed, and by what
    flat = np.zeros_like(r)
    ao = 0.55 * inner
    for (ang, depth, hard) in list(sp.flats) + (
            [(-math.pi * 0.5, sp.ground_flat, 1.0)] if sp.ground_flat > 1e-5 else []):
        if depth <= 1e-5:
            continue
        dth = np.abs((th - ang + math.pi) % (2 * math.pi) - math.pi)
        w = math.sqrt(max(2.0 * depth / max(sp.R, 1e-6), 1e-6)) * 1.9
        g = np.exp(-(dth / max(w, 0.05)) ** 2)
        flat = np.maximum(flat, g * clamp01(depth / 0.02))
        ao = np.maximum(ao, g * 0.85 * clamp01(frac))
    A["twt_flat"] = flat
    A["twt_ao"] = clamp01(ao + 0.30 * tags["serr"] + 0.25 * tags["hole"])
    # cuts: a car has been into this wall.  Narrow angular scars on the tread
    # and the shoulder of the tyres that took it.
    cut = np.zeros_like(r)
    for i in range(sp.cuts):
        a = rnd(0, 2 * math.pi, sp.key, 970 + i)
        w = rnd(0.02, 0.07, sp.key, 980 + i)
        dth = np.abs((th - a + math.pi) % (2 * math.pi) - math.pi)
        cut = np.maximum(cut, np.exp(-(dth / w) ** 2) * smoothstep(0.55, 0.95, frac))
    A["twt_cut"] = cut
    return A


# ==============================================================================
# 10.  BLENDER: MESH AND OBJECT
# ==============================================================================

def _new_mesh(name, verts, quads=None, tris=None, mats=None, recalc=True,
              smooth_deg=32.0):
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
    if recalc and len(me.polygons):
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
    if mats is not None and len(me.polygons) == len(mats):
        me.polygons.foreach_set("material_index",
                                np.ascontiguousarray(mats, np.int32))
    if smooth_deg is not None and len(me.polygons):
        _shade_by_angle(me, smooth_deg)
    return me


def _shade_by_angle(me, deg=32.0):
    """Smooth everywhere except across a real arris — the wall of a tread
    groove, the flank of a moulded letter, the bore of a drilled hole.  A tyre
    is tangent-continuous nearly everywhere, so flat shading it would turn 128
    legitimate rings into 128 visible facets."""
    npoly, nloop, nedge = len(me.polygons), len(me.loops), len(me.edges)
    if not nedge:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))
    fn = np.empty(npoly * 3, np.float32)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64)
    b = lv[nxt].astype(np.int64)
    key = np.minimum(a, b) * np.int64(len(me.vertices)) + np.maximum(a, b)
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
    ev = np.empty(nedge * 2, np.int32)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(nedge, 2).astype(np.int64)
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * np.int64(len(me.vertices))
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def tyre_mesh_data(sp, world_z0=0.6):
    """-> (V, quads, tris, mat_quad, mat_tri, attrs).  No bpy needed."""
    acc, prof, info, holes = build_tyre_arrays(sp)
    V, Q, T, M, MT, tags = acc.finish()
    V = deform(V, sp)
    wp = _water_patch(sp, prof, V)
    if wp is not None:
        Vw, Qw = wp
        Vw = deform(Vw, sp)
        Vw[:, 2] = float(np.mean(Vw[:, 2]))       # a mirror is flat
        n0 = len(V)
        V = np.concatenate([V, Vw])
        Q = np.concatenate([Q, Qw + n0])
        M = np.concatenate([M, np.full(len(Qw), 1, np.int32)])
        for k in tags:
            tags[k] = np.concatenate([tags[k], np.full(len(Vw), 0.0)])
        tags["bore"][n0:] = 1.0
    A = bake_attrs(sp, V, tags, world_z0)
    return V, Q, T, M, MT, A


def _object_props(ob, sp):
    ob["twt_age"] = float(sp.age)
    ob["twt_chalk"] = float(sp.chalk)
    ob["twt_kind"] = float(_KIND_ID[sp.kind])
    ob["twt_seed"] = float(sp.key % 100000)
    ob["twt_wet"] = float(sp.water)
    ob["twt_silt"] = float(sp.silt)
    # 7 % of a scrap pile has a scrutineer's mark still on it, not 28 %
    ob["twt_paint"] = float(1.0 if sp.paint > 0.93 else 0.0)
    ob["twt_pr"], ob["twt_pg"], ob["twt_pb"] = [float(c) for c in sp.paint_col]
    ob["twt_course"] = float(sp.course)
    # per-object texture offset: the only thing that stops 2 255 tyres sharing
    # one realisation of the rubber.  24 m, not 240: Cycles evaluates
    # procedurals in float32 and a large offset eats the mantissa.
    ob["twt_ofs_x"] = float(h01(sp.key, 3) * 24.0)
    ob["twt_ofs_y"] = float(h01(sp.key, 5) * 24.0)
    ob["twt_ofs_z"] = float(h01(sp.key, 7) * 24.0)


def build_tyre_object(sp, name=None, coll=None, mats=None, world_z0=0.6,
                      link=True):
    """One tyre as a Blender object, recentred on its own wheel centre."""
    V, Q, T, M, MT, A = tyre_mesh_data(sp, world_z0)
    me = _new_mesh(name or (PFX + "Tyre_%06d" % sp.key), V, Q, T,
                   mats=np.concatenate([M, MT]) if len(MT) else M)
    for k in ATTRS:
        if k not in A:
            continue
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.ascontiguousarray(A[k], np.float32))
    if mats:
        for m in mats:
            me.materials.append(m)
    ob = bpy.data.objects.new(me.name, me)
    _object_props(ob, sp)
    if coll is not None and link:
        coll.objects.link(ob)
    return ob, dict(verts=len(V), quads=len(Q), tris=len(T))


# ==============================================================================
# 11.  THE MATERIALS
# ==============================================================================

class NT(object):
    """Node DSL that knows which socket a Mix node actually uses."""

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
        nd.location = ((self.x % 14) * 220, -(self.x // 14) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, idx, src):
        if src is None:
            return
        while isinstance(src, tuple) and len(src) == 2 and isinstance(src[0], tuple):
            src = src[0]
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            # a colour socket wants 4 components and a vector socket wants 3;
            # the same PAL entry legitimately feeds both
            dv = nd.inputs[idx].default_value
            n = len(dv) if hasattr(dv, "__len__") else 1
            v = tuple(src)
            if n == 4 and len(v) == 3:
                v = v + (1.0,)
            elif n == 3 and len(v) == 4:
                v = v[:3]
            nd.inputs[idx].default_value = v
        else:
            nd.inputs[idx].default_value = float(src)

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

    def noise(self, vec, scale, detail=8.0, rough=0.55, dist=0.0, lac=2.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 3, detail)
        self.pin(nd, 4, rough); self.pin(nd, 5, lac); self.pin(nd, 8, dist)
        return (nd, 0)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 8, rand)
        return (nd, out)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, direction="X"):
        nd = self.n("ShaderNodeTexWave", wave_type="BANDS",
                    bands_direction=direction)
        self.pin(nd, 0, vec); self.pin(nd, 1, scale)
        self.pin(nd, 2, distortion); self.pin(nd, 3, detail)
        return (nd, 1)

    def grad(self, vec, kind="LINEAR"):
        nd = self.n("ShaderNodeTexGradient", gradient_type=kind)
        self.pin(nd, 0, vec)
        return (nd, 1)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, 0, src)
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
        self.pin(nd, 0, v); self.pin(nd, 1, f0); self.pin(nd, 2, f1)
        self.pin(nd, 3, t0); self.pin(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance=None, normal=None,
             modulation_pp=None, wavelength_m=None, height_pp=1.0):
        """Height -> normal perturbation.  WIRED BY NAME, stated in RADIANCE.

        TWO defects lived in the four lines this replaces.

        WIRED BY NAME (R2-038).  Blender 5.2 inserted `Filter Width` at index 2,
        so the live socket order is

            [0] Strength  [1] Distance  [2] Filter Width  [3] Height  [4] Normal

        The old body pinned `height` to index 2 and the incoming normal chain to
        index 3: the height signal went into Filter Width, and the Height socket
        of the FIRST bump in every chain kept its constant default.  A constant
        has zero gradient, so that stage contributed NO relief at all, and every
        later stage read a normal chain where its height should be.  It was
        silent -- the material built, rendered, and passed the gate's node-count
        check; only `relief_reads_as_lip_and_shade` could ever have seen it.
        Never pin this node by index again.

        STATE THE RADIANCE MODULATION, NOT THE METRES (itemkit section 5b,
        ITEM-CAMPAIGN-BRIEF 4a).  Give `modulation_pp` with `wavelength_m` and
        the depth is derived from the contract sun: m = 2 sin(theta) / tan(e),
        a 4.52x amplifier at this film's 12.47 deg.  An amplitude with no
        wavelength is not a relief specification -- the same 0.5 mm is m = 0.57
        on an 8 mm crumple and m = 0.045 on a 100 mm flute.  `height_pp` is the
        peak-to-peak swing of the height signal reaching the socket, so a stage
        can state the modulation of the BAND it means rather than of a
        hypothetical full-range height.
        """
        if (distance is None) == (modulation_pp is None):
            raise ValueError("bump() takes exactly one of distance= or "
                             "modulation_pp= (with wavelength_m=): itemkit 5b")
        if modulation_pp is not None:
            if not wavelength_m:
                raise ValueError("bump(modulation_pp=) needs wavelength_m=; an "
                                 "amplitude with no wavelength is not a relief "
                                 "specification.")
            try:
                _s = abs(float(strength))
            except (TypeError, ValueError):
                _s = 1.0         # a masked strength: aim at where the mask is 1
            distance = (K.relief_amplitude_for(modulation_pp, wavelength_m)
                        * 1e-3 / max(_s * float(height_pp), 1e-9))
        nd = self.n("ShaderNodeBump")
        self.pin(nd, nd.inputs.find("Strength"), strength)
        self.pin(nd, nd.inputs.find("Distance"), distance)
        self.pin(nd, nd.inputs.find("Height"), height)
        if normal is not None:
            self.pin(nd, nd.inputs.find("Normal"), normal)
        return (nd, 0)

    def bevel(self, radius, samples=8):
        nd = self.n("ShaderNodeBevel")
        nd.samples = samples
        self.pin(nd, 0, radius)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)

    def geo(self, out):
        nd = self.n("ShaderNodeNewGeometry")
        return (nd, out)


# Linear reflectances.  A tyre is the DARKEST common object outdoors — a new
# tread measures 0.020-0.028 diffuse, which is darker than fresh asphalt.  The
# single most common way to render rubber wrongly is to make it grey; everything
# that lifts these numbers below is a real deposit ON the rubber, not the rubber.
PAL = dict(
    rubber_new=(0.0195, 0.0192, 0.0196),
    rubber_old=(0.0300, 0.0288, 0.0272),     # oxidised, browner
    # UV bloom: antiozonant migrating out and oxidising.  It is NOT a coat of
    # limewash.  The first build mixed 0.145 in at 0.92 and a wall of the
    # blackest material outdoors came back looking like concrete pipe -- under
    # AgX at -3.05 EV a 0.06 albedo in a 115 W/m2 sun is already mid-grey.
    chalk=(0.0740, 0.0725, 0.0690),
    chalk_hot=(0.1060, 0.1020, 0.0950),      # the sun side of an old sidewall
    dust=(0.1180, 0.1020, 0.0790),
    road_film=(0.0330, 0.0305, 0.0280),
    silt=(0.0410, 0.0350, 0.0265),
    algae=(0.0290, 0.0405, 0.0230),
    moss=(0.0330, 0.0520, 0.0250),
    # A TYRE'S INNER LINER IS NOT BLACK.  It is halobutyl with almost no carbon
    # in it -- grey-brown, roughly twice the albedo of the tread, and the only
    # reason the inside of a bore reads as a cavity instead of a hole punched in
    # the frame.  It is also what makes the water line legible: dark wet butyl
    # below the line, pale dry butyl above it.
    liner=(0.0560, 0.0535, 0.0495),
    liner_wet=(0.0190, 0.0180, 0.0172),
    tide=(0.0130, 0.0125, 0.0122),           # the wet mark inside the bead
    polish=(0.0255, 0.0250, 0.0250),         # tread rubber burnished by a road
    scuff_paint=(0.2100, 0.2050, 0.2000),
    steel=(0.1600, 0.1600, 0.1620),
)


def mat_tyre():
    """Scrap rubber that has been in a barrier for years.

    Fourteen surface histories, in the order the rubber acquired them:

        carbon-black base -> the mould's own grain -> moulding spew and the
        vent pips -> road film and brake dust from the years it was driven ->
        the tread burnished where it touched the road -> ozone crazing on the
        flex zone -> antiozonant blooming to the surface as a grey chalk ->
        the sun bleaching the face that points at it -> rain washing streaks
        through the dust -> algae in the damp bottom course -> silt and a black
        tide line where the water stands inside -> a sprayed compound mark ->
        rubber and paint transferred by a car that brushed the wall -> dust
        settling again on every up-facing surface.

    NO Geometry->Position anywhere.  Object coordinates for everything spatial,
    a per-object offset so 2 255 tyres are not one rubber stamp, and
    Geometry->Normal (which is scale-free and exact at any |P|) for the two
    things that genuinely depend on which way a surface points: what the sun has
    bleached, and what the dust has settled on.
    """
    name = PFX + "Rubber"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("twt_ofs_x", 2, "OBJECT"),
                 t.attr("twt_ofs_y", 2, "OBJECT"),
                 t.attr("twt_ofs_z", 2, "OBJECT"))
    NZ = t.vmath("ADD", OBJ, ofs)
    N = t.geo(1)                                  # world normal — never position

    age = t.attr("twt_age", 2, "OBJECT")
    chalk_o = t.attr("twt_chalk", 2, "OBJECT")
    wet_o = t.attr("twt_wet", 2, "OBJECT")
    silt_o = t.attr("twt_silt", 2, "OBJECT")
    paint_o = t.attr("twt_paint", 2, "OBJECT")
    pcol = t.comb(t.attr("twt_pr", 2, "OBJECT"), t.attr("twt_pg", 2, "OBJECT"),
                  t.attr("twt_pb", 2, "OBJECT"))

    a_h = t.attr("twt_h")
    a_water = t.attr("twt_water")
    a_bore = t.attr("twt_bore")
    a_tread = t.attr("twt_tread")
    a_wear = t.attr("twt_wear")
    a_letter = t.attr("twt_letter")
    a_serr = t.attr("twt_serr")
    a_bead = t.attr("twt_bead")
    a_crack = t.attr("twt_crack")
    a_grime = t.attr("twt_grime")
    a_scuff = t.attr("twt_scuff")
    a_flat = t.attr("twt_flat")
    a_cut = t.attr("twt_cut")
    a_ao = t.attr("twt_ao")

    # which way this bit of rubber points, in the world
    sun = t.vmath("DOT_PRODUCT", N, tuple(C.SUN_DIR))
    sunf = t.maprange(sun, 0.0, 0.75, 0.0, 1.0)
    upf = t.maprange(t.sep(N, 2), 0.1, 0.85, 0.0, 1.0)

    # ---------------------------------------------------------------- 1. BASE
    # Carbon black with the mottle of a compound that was never uniform, plus
    # the mould's own fine grain.
    mott = t.noise(NZ, 42.0, 6.0, 0.55)
    grain = t.noise(t.vmath("MULTIPLY", NZ, (2.2, 0.35, 2.2)), 620.0, 4.0, 0.62)
    peb = t.vor(NZ, 1400.0, "F1", 0, 1.0)
    base = t.cmix(t.maprange(mott, 0.30, 0.72, 0.0, 1.0),
                  PAL["rubber_new"], PAL["rubber_old"])
    base = t.cmix(t.math("MULTIPLY", age, 0.85), base, PAL["rubber_old"])
    # a scrap pile is not one tone: some of these came out of a shed last year
    # and some have been in the wall since the circuit opened
    base = t.cmix(t.maprange(chalk_o, 0.0, 1.0, 0.0, 0.55),
                  t.cmix(0.5, base, (0.0155, 0.0152, 0.0155)), base)

    # ---------------------------------------------------- 1b. THE INNER LINER
    liner = t.cmix(t.maprange(t.noise(NZ, 60.0, 5.0, 0.6), 0.35, 0.68, 0.0, 1.0),
                   PAL["liner"], tuple(c * 0.72 for c in PAL["liner"]))
    base = t.cmix(t.math("MULTIPLY", a_bore, 0.90), base, liner)

    # ------------------------------------------------------ 2. TREAD BURNISH
    # The crown was polished by a road; the groove floors never were.
    burn = t.math("MULTIPLY", a_tread,
                  t.maprange(a_wear, 0.25, 1.0, 0.15, 1.0))
    base = t.cmix(t.math("MULTIPLY", burn, 0.8), base, PAL["polish"])

    # -------------------------------------------------------- 3. OZONE CRAZE
    # A real crack net: voronoi cell BORDERS, not cells, so it reads as a
    # craquelure and not as a leopard.  Geometry cannot carry a 0.8 mm crack at
    # 1.70 mm/px, so this is shading over a baked density — and it says so.
    cz = t.vor(t.vmath("MULTIPLY", NZ, (1.0, 3.0, 1.0)), 260.0, "DISTANCE_TO_EDGE", 0, 1.0)
    cz2 = t.vor(t.vmath("MULTIPLY", NZ, (1.0, 3.0, 1.0)), 700.0, "DISTANCE_TO_EDGE", 0, 1.0)
    crack = t.math("MULTIPLY", a_crack,
                   t.maprange(cz, 0.0, 0.045, 1.0, 0.0))
    crack2 = t.math("MULTIPLY", t.math("MULTIPLY", a_crack, 0.55),
                    t.maprange(cz2, 0.0, 0.030, 1.0, 0.0))
    crackall = t.math("MAXIMUM", crack, crack2)
    base = t.cmix(t.math("MULTIPLY", crackall, 0.85), base, (0.0075, 0.0072, 0.0070))

    # ------------------------------------------------------- 4. UV CHALKING
    # Antiozonant migrating to the surface and oxidising: the grey-brown bloom
    # that makes an old tyre look dusty when it is perfectly clean.  Strongest
    # where the sun actually falls, which is why the wall is two-toned.
    # THE MIX FACTOR IS A PRODUCT OF FOUR TERMS AND THAT IS THE TRAP.  The
    # first version multiplied chalk x age x noise x sun and then scaled the
    # result by 0.34: a fully bloomed sidewall came out at a 0.107 mix and a
    # fresh one at 0.011, so 1 287 tyres spanned 0.0256 to 0.0307 albedo -- a
    # 20 % spread, which is a wall of one colour.  Each term is now floored so
    # it can only modulate, not annihilate, and the spread is 1.7x.
    bloom_n = t.noise(NZ, 26.0, 5.0, 0.5)
    bloom = t.math("MULTIPLY", chalk_o, t.maprange(age, 0.0, 1.0, 0.45, 1.0))
    bloom = t.math("MULTIPLY", bloom,
                   t.maprange(bloom_n, 0.32, 0.78, 0.60, 1.0))
    bloom = t.math("MULTIPLY", bloom,
                   t.maprange(sunf, 0.0, 1.0, 0.70, 1.0))
    bloom = t.math("MULTIPLY", bloom, t.maprange(a_bore, 0.0, 1.0, 1.0, 0.10))
    chalk_col = t.cmix(sunf, PAL["chalk"], PAL["chalk_hot"])
    base = t.cmix(t.math("MULTIPLY", bloom, 0.95, clamp=True), base, chalk_col)

    # -------------------------------------------------------- 5. ROAD FILM
    # A TYRE THAT WENT IN LAST WINTER IS STILL BLACK.  Every deposit below is
    # scaled by how long this one has been in the wall, so the fresh ones stay
    # at 0.022 while the old ones climb to 0.05 -- a factor of 2.3 between
    # neighbours, which is the difference between a wall and a wallpaper.
    yrs = t.maprange(chalk_o, 0.0, 1.0, 0.35, 1.0)
    film = t.math("MULTIPLY", a_grime,
                  t.maprange(t.noise(NZ, 9.0, 6.0, 0.6), 0.30, 0.75, 0.4, 1.0))
    film = t.math("MULTIPLY", film, yrs)
    base = t.cmix(t.math("MULTIPLY", film, 0.55), base, PAL["road_film"])

    # ------------------------------------------------------------- 6. DUST
    # Settles on up-facing surfaces and in every crevice; rain cuts streaks
    # down through it.  The streak coordinate is OBJECT z, not world position.
    streak = t.noise(t.vmath("MULTIPLY", NZ, (9.0, 9.0, 0.22)), 60.0, 6.0, 0.62)
    dustm = t.math("MULTIPLY", upf, t.maprange(streak, 0.28, 0.72, 0.15, 1.0))
    dustm = t.math("MULTIPLY", dustm, t.maprange(a_grime, 0.0, 1.0, 0.45, 1.15))
    dustm = t.math("ADD", dustm, t.math("MULTIPLY", a_ao, 0.30))
    dustm = t.math("MULTIPLY", dustm, t.maprange(a_bore, 0.0, 1.0, 1.0, 0.35))
    dustm = t.math("MULTIPLY", dustm, yrs)
    base = t.cmix(t.math("MULTIPLY", dustm, 0.26, clamp=True), base, PAL["dust"])

    # -------------------------------------------------- 6b. SPLASH FROM BELOW
    # Everything within 350 mm of the ground gets mud, grit and cut grass
    # thrown at it by every mower and every car that runs wide.  It is also what
    # stops a wall of identical tyres being one flat tone from top to bottom.
    spl_n = t.noise(t.vmath("MULTIPLY", NZ, (5.0, 5.0, 1.4)), 140.0, 7.0, 0.66)
    spl = t.math("MULTIPLY", t.maprange(a_h, 0.42, 0.02, 0.0, 1.0),
                 t.maprange(spl_n, 0.40, 0.70, 0.0, 1.0))
    spl = t.math("MULTIPLY", spl, t.maprange(a_bore, 0.0, 1.0, 1.0, 0.15))
    base = t.cmix(t.math("MULTIPLY", spl, 0.62), base,
                  t.cmix(spl_n, (0.0435, 0.0330, 0.0215), PAL["dust"]))

    # ------------------------------------------------------------- 7. ALGAE
    # The bottom course is damp all winter.
    alg_n = t.noise(NZ, 34.0, 7.0, 0.62)
    alg = t.math("MULTIPLY", t.maprange(a_h, 0.55, 0.10, 0.0, 1.0),
                 t.maprange(alg_n, 0.42, 0.68, 0.0, 1.0))
    alg = t.math("MULTIPLY", alg, t.maprange(sunf, 0.15, 0.75, 1.0, 0.25))
    base = t.cmix(t.math("MULTIPLY", alg, 0.75), base,
                  t.cmix(alg_n, PAL["algae"], PAL["moss"]))

    # ------------------------------------------- 8. THE WATER LINE INSIDE
    # twt_water is metres BELOW the standing water level, and -1 outside the
    # cavity.  Submerged rubber is black and slimy; just above it is the tide
    # mark; above that are the older marks the water left as it evaporated.
    sub = t.maprange(a_water, 0.0, 0.004, 0.0, 1.0)
    tideband = t.maprange(a_water, -0.004, 0.0, 0.0, 1.0)
    tide2 = t.math("MULTIPLY",
                   t.maprange(a_water, -0.030, -0.022, 0.0, 1.0),
                   t.maprange(a_water, -0.016, -0.022, 0.0, 1.0))
    tide3 = t.math("MULTIPLY",
                   t.maprange(a_water, -0.060, -0.052, 0.0, 1.0),
                   t.maprange(a_water, -0.044, -0.052, 0.0, 1.0))
    tides = t.math("MAXIMUM", tideband, t.math("MAXIMUM", tide2, tide3))
    tides = t.math("MULTIPLY", tides, t.math("MULTIPLY", a_bore, wet_o))
    base = t.cmix(t.math("MULTIPLY", tides, 0.9), base, PAL["tide"])
    # everything under the line is wet, dark and slimy butyl
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", sub, a_bore),
                         t.math("MULTIPLY", wet_o, 0.85)),
                  base, PAL["liner_wet"])
    siltm = t.math("MULTIPLY", t.math("MULTIPLY", sub, a_bore),
                   t.maprange(silt_o, 0.0, 1.0, 0.25, 1.0))
    base = t.cmix(t.math("MULTIPLY", siltm, 0.85), base,
                  t.cmix(t.noise(NZ, 180.0, 5.0, 0.6), PAL["silt"], PAL["algae"]))

    # ------------------------------------------------------ 9. COMPOUND MARK
    # A sprayed stripe, the way a scrutineer marks a set.  Fictional colours
    # from build_dressing's compound table; faded and half worn off.
    # ONE SWIPE OF A SPRAY CAN, on the tyres that got one -- not a paint job.
    # The first build put a 0.31 m object-space band through every tyre with
    # `twt_paint` set and 28 % of the wall came out in liquorice allsorts.
    swipe = t.vor(t.vmath("MULTIPLY", NZ, (1.0, 0.30, 1.0)), 7.0, "F1", 0, 1.0)
    edge = t.noise(NZ, 130.0, 6.0, 0.62)
    sm = t.math("MULTIPLY", paint_o, t.maprange(swipe, 0.16, 0.09, 0.0, 1.0))
    sm = t.math("MULTIPLY", sm, t.maprange(edge, 0.40, 0.56, 0.0, 1.0))
    sm = t.math("MULTIPLY", sm, t.maprange(a_bore, 0.0, 1.0, 1.0, 0.0))
    sm = t.math("MULTIPLY", sm, t.maprange(a_tread, 0.0, 1.0, 1.0, 0.35))
    base = t.cmix(t.math("MULTIPLY", sm, 0.62), base,
                  t.cmix(0.45, pcol, PAL["dust"]))

    # ------------------------------------------------ 10. WHAT A CAR LEFT
    scu = t.math("MULTIPLY", a_scuff,
                 t.maprange(t.noise(t.vmath("MULTIPLY", NZ, (0.6, 3.0, 3.0)),
                                    22.0, 6.0, 0.6), 0.34, 0.70, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", scu, 0.55), base, PAL["scuff_paint"])
    base = t.cmix(t.math("MULTIPLY", a_cut, 0.5), base, (0.0125, 0.0120, 0.0118))

    # --------------------------------------------------------- ROUGHNESS
    rough = t.fmix(t.maprange(age, 0.0, 1.0, 0.0, 1.0), 0.62, 0.80)
    rough = t.fmix(burn, rough, 0.44)
    rough = t.fmix(t.math("MULTIPLY", bloom, 0.9), rough, 0.93)
    rough = t.fmix(t.math("MULTIPLY", dustm, 0.7, clamp=True), rough, 0.90)
    rough = t.fmix(t.math("MULTIPLY", siltm, 0.8), rough, 0.86)
    rough = t.fmix(t.math("MULTIPLY", spl, 0.7), rough, 0.94)
    rough = t.fmix(t.math("MULTIPLY", tides, 0.85), rough, 0.30)
    rough = t.fmix(t.math("MULTIPLY", a_letter, 0.6), rough, 0.58)
    rough = t.math("ADD", rough,
                   t.math("MULTIPLY",
                          t.maprange(t.noise(NZ, 320.0, 4.0, 0.6), 0.3, 0.7,
                                     -0.05, 0.05), 1.0))

    # ------------------------------------------------------------- BUMP
    # Three scales: the mould grain, the carbon-black pebbling, and the crack
    # net.  All of it under a pixel, all of it what stops the rubber reading as
    # vinyl at 590 px/m.
    h = t.math("ADD", t.math("MULTIPLY", grain, 0.55),
               t.math("MULTIPLY", t.sep(peb, 0) if False else peb, 0.45))
    h = t.math("SUBTRACT", h, t.math("MULTIPLY", crackall, 1.6))
    h = t.math("ADD", h, t.math("MULTIPLY", t.maprange(
        t.noise(NZ, 3000.0, 3.0, 0.5), 0.35, 0.65, 0.0, 1.0), 0.20))
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES.  itemkit section 5b,
    # ITEM-CAMPAIGN-BRIEF 4a.  m = 2 sin(theta) / tan(e); this film's 12.47 deg
    # sun is a 4.52x amplifier and cannot deliver more than 2/tan(e) = 9.04 at
    # any slope, because past that a normal is asking for a shadow.
    #
    # BOTH OF THESE ARE DELIBERATE RE-TUNES DOWNWARD.  This material audited at
    # m_median 7.66 against that 9.04 ceiling -- not a dead stack but a stack
    # pinned at the terminator, the `tyre_blanket` failure (m 6.0) one door
    # along.  Measured band by band, the shipped depths were:
    #
    #   [0] grain     w 0.55  lam  1.17 mm  m 7.463   0.546 mm p-p  <- named
    #       peb       w 0.45  lam  1.55 mm  m 6.067   0.446 mm p-p
    #       crackall  w 1.60  lam  3.10 mm  m 7.680   1.587 mm p-p (gated, age)
    #       micro     w 0.20  lam  0.53 mm  m 6.871   0.198 mm p-p
    #   [1] serr      w 1.00  lam  0.30 mm  m 8.537   0.270 mm p-p (gated)
    #
    # Every one of those is past the 3.76 that rendered as coarse stucco, and
    # 0.546 mm of relief on a 1.17 mm mould grain is a surface standing at 55
    # degrees.  The comment above says the truth about them -- "all of it under
    # a pixel" at 590 px/m -- and a sub-pixel band at m 7 is not detail, it is
    # noise: this is the same reasoning `armco_w_beam` wrote down when it kept
    # its 0.4 mm roll marks at m 0.14 rather than let them alias.
    #
    # [0] -- 7.463 -> 0.400 on the MOULD GRAIN, which is the band that is always
    # present, carries the most height and gives the stage its character.
    # RELIEF_BANDS["isotropic_micro"] (0.12-0.45) is literally the band for cast
    # skin, which is what a mould grain is, and 0.400 sits near its top because
    # this stage's whole job -- the module says so -- is to stop the rubber
    # reading as vinyl.  16.5 um p-p, which is what a tyre mould's grain really
    # measures.  The rest of the stack follows it down to peb m 0.248, micro
    # m 0.320, crack net m 0.164 (8.35 mm cells) / m 0.440 (3.10 mm cells), all
    # inside isotropic_micro/macro.  ONE CAVEAT ON THE CRACK NET: it is a
    # DISTANCE_TO_EDGE ridge whose wall is far narrower than its cell pitch, so
    # its true local slope is steeper than the cell-pitch figure above; the
    # craze is carried mostly by colour here anyway, as section 3 says.
    # The grain's slow axis (NZ is pre-multiplied by (2.2, 0.35, 2.2), so it is
    # 7.37 mm the other way) is m 0.064 -- the band is a directional grain and
    # the named wavelength is the one the gradient actually crosses.
    #
    # [1] -- 8.537 -> 1.500.  The serration is an EDGE and it is gated to the
    # serration band by `a_serr`, so `hard_feature` (1.5-6.0) is the right band;
    # 1.500 is its FLOOR because at 590 px/m a 0.30 mm rib pitch is a sixth of a
    # pixel and the mesh already carries the ribs -- this stage only has to keep
    # them biting between mesh samples.  15.9 um p-p; the slow axis lands at
    # m 0.253.
    #
    # THE WAVELENGTHS COME FROM THE SAME LITERALS THAT PICKED THE SCALES,
    # INCLUDING THE COORDINATE PRE-MULTIPLIES.  `grain` reads NZ * (2.2, .35,
    # 2.2) through a Noise of 620, so its fast axis is 1.6 / (620 * 2.2) and not
    # 1.6 / 620; `serr` reads NZ * (6, 1, 6) through a Noise of 900.  A reader
    # that takes only the Scale socket is out by 2.2x and 6x respectively.
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / (620.0 * 2.2)   # 1.173 mm
    LAM_SERR = K.NOISE_WAVELENGTH_FACTOR / (900.0 * 6.0)    # 0.296 mm
    nrm = t.bump(h, 0.62, modulation_pp=0.400, wavelength_m=LAM_GRAIN,
                 height_pp=0.55)
    # the serration band gets a second, finer bump so the ribs keep biting even
    # where the mesh has already resolved them
    nrm = t.bump(t.math("MULTIPLY", a_serr,
                        t.maprange(t.noise(t.vmath("MULTIPLY", NZ, (6.0, 1.0, 6.0)),
                                           900.0, 3.0, 0.5), 0.3, 0.7, 0.0, 1.0)),
                 0.30, normal=nrm,
                 modulation_pp=1.500, wavelength_m=LAM_SERR)

    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, 0, base)
    for nm, v in (("Roughness", rough), ("Metallic", 0.0), ("IOR", 1.52)):
        if nm in [s.name for s in bsdf.inputs]:
            t.pin(bsdf, [s.name for s in bsdf.inputs].index(nm), v)
    names = [s.name for s in bsdf.inputs]
    if "Normal" in names:
        t.pin(bsdf, names.index("Normal"), nrm)
    if "Specular IOR Level" in names:
        t.pin(bsdf, names.index("Specular IOR Level"),
              t.fmix(t.math("MULTIPLY", bloom, 0.9), 0.42, 0.22))
    if "Sheen Weight" in names:
        # 0.10, not 0.28.  Sheen is a grazing-angle lobe and the wall is SEEN
        # at a grazing angle: at 0.28 it was adding more to the lit sidewall
        # than the albedo was, which is how black rubber came back cream.
        t.pin(bsdf, names.index("Sheen Weight"),
              t.math("MULTIPLY", bloom, 0.10))
        if "Sheen Roughness" in names:
            t.pin(bsdf, names.index("Sheen Roughness"), 0.55)
        if "Sheen Tint" in names:
            t.pin(bsdf, names.index("Sheen Tint"), (0.40, 0.39, 0.37))
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return t.m


def mat_water():
    """The rainwater standing inside the carcass.

    It is not blue and it is not clean: it is a black mirror with a skin of
    pollen and rubber dust on it, and its whole job is to be the one specular
    surface in a wall of the most diffuse material there is.
    """
    name = PFX + "Water"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("twt_ofs_x", 2, "OBJECT"),
                 t.attr("twt_ofs_y", 2, "OBJECT"),
                 t.attr("twt_ofs_z", 2, "OBJECT"))
    NZ = t.vmath("ADD", OBJ, ofs)
    scum = t.vor(t.vmath("MULTIPLY", NZ, (1.0, 1.0, 8.0)), 180.0, "F1", 0, 1.0)
    dustfilm = t.maprange(t.noise(NZ, 55.0, 6.0, 0.6), 0.42, 0.62, 0.0, 1.0)
    film = t.math("MULTIPLY", dustfilm, t.maprange(scum, 0.0, 0.5, 1.0, 0.25))
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    names = [s.name for s in bsdf.inputs]
    t.pin(bsdf, 0, t.cmix(film, (0.0055, 0.0060, 0.0058), (0.0330, 0.0300, 0.0225)))
    t.pin(bsdf, names.index("Roughness"),
          t.fmix(film, 0.030, 0.42))
    if "Transmission Weight" in names:
        t.pin(bsdf, names.index("Transmission Weight"),
              t.fmix(film, 0.75, 0.0))
    t.pin(bsdf, names.index("IOR"), 1.333)
    # STATED AS RADIANCE MODULATION (itemkit 5b).  NOT a re-tune: 0.340685
    # reproduces the shipped 0.0008 m Distance to better than 1e-6 relative.
    # One band, one texture, so `height_pp` is 1.0.  48 um p-p on a 4.0 mm
    # ripple is m 0.341, inside RELIEF_BANDS["isotropic_micro"] (0.12-0.45) --
    # the right size for still water carrying a dust and pollen skin.  The
    # coordinate is pre-multiplied by (1, 1, 0.05), so the ripple is 4.0 mm
    # across the surface and 80 mm through it (m 0.017); the water plane is
    # horizontal, so the 4.0 mm figure is the one the gradient crosses.
    # CAVEAT: this surface is specular and transmissive, so `m` -- a Lambertian
    # quantity -- is a guide here and not a measurement.
    LAM_RIPPLE = K.NOISE_WAVELENGTH_FACTOR / 400.0          # 4.00 mm
    ripple = t.bump(t.noise(t.vmath("MULTIPLY", NZ, (1.0, 1.0, 0.05)),
                            400.0, 4.0, 0.5), 0.06,
                    modulation_pp=0.340685, wavelength_m=LAM_RIPPLE)
    if "Normal" in names:
        t.pin(bsdf, names.index("Normal"), ripple)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return t.m


# ==============================================================================
# 12.  PLACEMENT  —  the public interface the four dependants call
# ==============================================================================
# Pure numpy.  An agent building the belt, the rods or the trackside stacks can
# import this and get the built wall without opening Blender.

PITCH = 0.620              # tyre centres along the wall (they touch)
SQUEEZE = 0.008            # how much a bolted-up wall is compressed
ROW_GAP = 0.004            # tyres in adjacent rows are bolted face to face


def row_phase(row, rows):
    """How far along the wall row `row` is shifted, in metres.

    THE ROWS THAT A ROD PASSES THROUGH MUST BE ALIGNED -- and aligned bores are
    a line of sight straight through the barrier, which the first build showed:
    from 0.9 m the camera looked through three tyres and out at the far side of
    the hairpin.  Real walls close that by laying the BACKING row in brick bond,
    half a pitch across, so its sidewall blocks the tunnel.  So: every row but
    the last is on the bolt line, and the last one is the packing behind it.
    """
    # Half a pitch, which is as far across as a course can be laid.  It is NOT
    # enough on its own to close the line of sight -- two bores 0.42 m across
    # cannot be separated by 0.31 m of offset -- so the backing row's bores are
    # also packed with the leaf litter and grit that fills them in life; see
    # `_bore_fill`.  Together they close it.
    return (PITCH * 0.5) if (rows >= 2 and row == rows - 1) else 0.0


def rod_rows(rows):
    """The rows one through-rod threads: everything on the bolt line."""
    return list(range(max(1, rows - 1)))
# The height a 3-course wall is built to.  C.TRANSIT_SOUTH_TOP_Z is 2.00 and the
# belt's top edge takes the last 30 mm, so the RUBBER tops out here.
TARGET_TOP_M = 1.97


class Wall(object):
    __slots__ = ("name", "P", "T", "A", "S", "rows", "courses", "seed",
                 "desc", "belted")

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw.get(s))


def _frames_from_path(P, inward):
    """Tangent and face-normal at every sample of a wall path."""
    d = np.gradient(P[:, :2], axis=0)
    T = np.concatenate([d, np.zeros((len(P), 1))], axis=1)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    A = inward / np.maximum(np.linalg.norm(inward, axis=1, keepdims=True), 1e-9)
    return T, A


def hero_station():
    """WHERE ON THE WALL THE MACRO IS SHOT, chosen by measurement.

    The hairpin turns the wall through 180 degrees, so the face points at every
    bearing there is, and the contract sun sits 12.47 deg above the horizon.
    That means one end of this wall is lit square on (flat, no relief), one end
    is in its own shadow (no read at all), and somewhere between them the light
    RAKES the face at about 72 degrees of incidence -- which is the only place a
    0.8 mm moulded letter, a 4.5 mm serration rib and a 20 mm compression flat
    all throw a shadow long enough to see.  The first build pinned the station
    at s = 1006 because it was the middle of the wall, and measured
    cos(incidence) = -0.31 there: the hero face was in shadow.

    Returns the station of the best-lit column, and the belt item is asked to
    leave +/- HERO_KEEP_CLEAR_M of it bare.
    """
    global _HERO_S
    if _HERO_S is None:
        w = wall("t4")
        sun = np.asarray(C.SUN_DIR, float)
        cs = w.A @ sun
        score = np.exp(-((cs - 0.30) / 0.16) ** 2)
        score *= smoothstep(0.0, 14.0, w.S - w.S[0])
        score *= smoothstep(0.0, 14.0, w.S[-1] - w.S)
        k = int(np.argmax(score))
        _HERO_S = float(w.S[k])
        log("hero station s %.1f: face normal . sun = %+.3f (%.1f deg of "
            "incidence), score %.3f" % (_HERO_S, cs[k],
                                        math.degrees(math.acos(np.clip(cs[k], -1, 1))),
                                        score[k]))
    return _HERO_S


def belt_keep_clear():
    """The station window `tyre_wall_belt_facing` must leave unbelted.  The
    manifest films the TYRES at 3.8 m; a belt over them would film the belt."""
    h = hero_station()
    return (h - HERO_KEEP_CLEAR_M, h + HERO_KEEP_CLEAR_M)


def wall_t4(ds=0.25):
    """The hairpin infield wall: build_barriers' T4_WALL_S at T4_WALL_LAT,
    seated on world_ground_z, face pointing at the track."""
    s = np.arange(T4_WALL_S[0], T4_WALL_S[1] + 1e-9, ds)
    lat = np.full_like(s, T4_WALL_LAT)
    P = np.asarray(C.su_to_world(s, lat, side=+1), float)
    Q = np.asarray(C.su_to_world(s, lat - 1.0, side=+1), float)
    z, own = C.world_ground_z(P[:, 0], P[:, 1])
    P[:, 2] = np.where(np.isfinite(z), z, P[:, 2])
    T, A = _frames_from_path(P, Q[:, :3] - P[:, :3])
    return Wall(name="t4", P=P, T=T, A=A, S=s, rows=T4_ROWS,
                courses=T4_COURSES, seed=404, belted=True,
                desc="hairpin infield, s 912-1058 at lat 13.10, 3 rows x 3 courses")


def wall_transit_south(ds=0.25):
    """The Beat-4 corridor wall: C.transit_wall_point on the south side, with
    the pit-exit portal left open."""
    t0, t1 = C.transit_wall_span(-1)
    t = np.arange(t0, t1 + 1e-9, ds)
    P = np.array([C.transit_wall_point(tt, -1) for tt in t], float)
    Q = np.array([C.access_route_point(tt)[:2] for tt in t], float)
    z, own = C.world_ground_z(P[:, 0], P[:, 1])
    P[:, 2] = np.where(np.isfinite(z), z, 0.0)
    inward = np.concatenate([Q - P[:, :2], np.zeros((len(P), 1))], axis=1)
    T, A = _frames_from_path(P, inward)
    keep = np.abs(P[:, 0] - TRANSIT_PORTAL_X) > TRANSIT_PORTAL_CLEAR
    return Wall(name="transit_south", P=P[keep], T=T[keep], A=A[keep],
                S=t[keep], rows=2, courses=3, seed=707, belted=True,
                desc="south corridor wall, route t 6-90 at -7.0 m, portal open")


WALLS = {}


def wall(name):
    if name not in WALLS:
        WALLS[name] = {"t4": wall_t4, "transit_south": wall_transit_south}[name]()
    return WALLS[name]


def _path_len(w):
    seg = np.linalg.norm(np.diff(w.P[:, :2], axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)]), seg


def _at_u(w, L, seg, u):
    """World point, tangent, face normal and station at arc length u."""
    k = int(np.clip(np.searchsorted(L, u) - 1, 0, len(w.P) - 2))
    f = float(np.clip((u - L[k]) / max(seg[k], 1e-9), 0.0, 1.0))
    p = w.P[k] + (w.P[k + 1] - w.P[k]) * f
    return p, w.T[k], w.A[k], float(w.S[k])


def _breaks(L, seg):
    """Arc-length intervals the wall does not exist in (the pit-exit portal)."""
    out = []
    for k in np.flatnonzero(seg > 0.9):
        out.append((float(L[k]), float(L[k + 1])))
    return out


def _ckey(w, c, j, row, att):
    return int((w.seed * 1000003 + c * 37 + j * 977 + row * 7
                + att * 100003) % 2 ** 31)


def _course_layout(w, c, total, brk, below=None):
    """One course, packed along the wall.

    THE PITCH IS NOT A CONSTANT and the first build's was.  A 0.62 m pitch is
    right for a 0.66 m tyre and drives a 0.86 m truck carcass 240 mm into its
    neighbour; the render showed exactly that.

    The bottom course is packed so that adjacent tyres TOUCH.  Every course
    above it goes in the VALLEYS of the course below -- one tyre per pair of
    tyres underneath, which is how a stack is actually built and the only way
    the pack stays dense.  Placing each course on its own independent spacing
    (the second version) let a tyre perch on the crown of the one below and
    opened 160 mm holes through the wall, which the render showed as daylight.
    """
    out = []
    if below is None:
        u = None
        prevR = None
        j = 0
        while j < 4000:
            key0 = _ckey(w, c, j, 0, 0)
            R0, W0, Rb0, _ = dims_for(key0, bottom_course=(c == 0))
            if u is None:
                u = R0 * 0.98
            else:
                u = u + (prevR + R0) * (1.0 - SQUEEZE)
            if u + R0 > total:
                break
            if any(b[0] - R0 < u < b[1] + R0 for b in brk):
                u = u + R0 * 0.4          # step over the portal
                j += 1
                continue
            out.append(dict(j=j, u=u, key0=key0, R0=R0))
            prevR = R0
            j += 1
        return out
    for k in range(len(below) - 1):
        a, b = below[k], below[k + 1]
        gap = b["u"] - a["u"]
        if gap > (a["R0"] + b["R0"]) * 1.35:
            continue                      # a break in the course below
        u = 0.5 * (a["u"] + b["u"])
        key0 = _ckey(w, c, k, 0, 0)
        R0, W0, Rb0, _ = dims_for(key0, bottom_course=False)
        if u + R0 > total or u - R0 < 0:
            continue
        if any(b2[0] - R0 < u < b2[1] + R0 for b2 in brk):
            continue
        out.append(dict(j=k, u=u, key0=key0, R0=R0))
    # A VALLEY IS NOT ALWAYS THE RIGHT WIDTH.  Where two tyres in a course end
    # up further apart than their radii, there is a real hole through the wall
    # -- and a real builder puts another tyre in it, which is why a tyre barrier
    # has odd small tyres wedged into its upper courses.
    filled = []
    for k, col in enumerate(out):
        filled.append(col)
        if k + 1 >= len(out):
            continue
        nxt = out[k + 1]
        gap = nxt["u"] - col["u"]
        # the biggest tyre that FITS between them, which is not the same as the
        # gap: its centre is at the midpoint, so it has gap/2 minus its bigger
        # neighbour's radius to live in.  Getting that wrong wedged a 0.33 m
        # tyre into 0.02 m of air 687 times, and the render showed the outlines
        # crossing.
        room = gap * 0.5 - max(col["R0"], nxt["R0"]) * (1.0 - SQUEEZE)
        if room < 0.235:
            continue
        u = 0.5 * (col["u"] + nxt["u"])
        key0 = _ckey(w, c, 5000 + k, 0, 0)
        R0, W0, Rb0, _ = dims_for(key0, bottom_course=False)
        R0 = min(R0, room)
        filled.append(dict(j=5000 + k, u=u, key0=key0, R0=R0, wedge=True))
    return filled


def tyre_sites(wname, lod_of=None, hero=None):
    """EVERY tyre in one wall.  The interface `transit_tyre_wall_stack`,
    `tyre_wall_through_rod`, `tyre_wall_belt_facing` and `tyre_stack_trackside`
    all build on.

    Each site is a dict:
        key      deterministic tyre id (spec_for(key) rebuilds it exactly)
        col/course/row, s (station), u (arc length along the wall)
        pos      world (x, y, z) of the WHEEL CENTRE
        M        3x3 local->world basis, columns (along-wall, axle-out, up)
        Mb       the same without the hand-stacked tilt
        R, W     outer radius and section width, metres
        kind     archetype
        hole     (theta, radius) of the ACTIVE through-bolt hole IN THIS TYRE
        flats    the measured contacts the mesh is deformed by
        spec     the TyreSpec itself

    HOW A WALL IS ACTUALLY BUILT, and why this is a packing simulation rather
    than a grid.  Three things have to be true at once and none of them survives
    a constant pitch:

      1. ADJACENT TYRES TOUCH.  Column spacing follows the tyres, per course.
      2. A TYRE RESTS ON THE ONES BELOW IT.  Its seat is solved: the highest
         constraint from every tyre in the course below that it can reach.  The
         contact directions that come out of that are the flats the mesh is
         deformed by, so the compression is where the load is.
      3. A ROD PASSES THROUGH A LINE OF TYRES.  Rows on the bolt line share
         their column line and are radius-matched; the backing row is laid a
         third of a pitch across so the wall is not see-through.
    """
    w = wall(wname)
    L, seg = _path_len(w)
    total = float(L[-1])
    brk = _breaks(L, seg)
    Zu = np.array([0.0, 0.0, 1.0])
    sites = []
    layout = {}
    for c in range(w.courses):
        layout[c] = _course_layout(w, c, total, brk,
                                   below=(layout[c - 1] if c else None))
    seats = {}
    for c in range(w.courses):
        for col in layout[c]:
            j, u, key0, R0 = col["j"], col["u"], col["key0"], col["R0"]
            # --- the rows: the bolt line is radius-matched, the backing row is
            #     laid across so the bores do not line up into a tunnel
            stack = {0: dims_for(key0, bottom_course=(c == 0)) + (key0,)}
            for row in range(1, w.rows):
                bk = None
                for att in range(28):
                    key = _ckey(w, c, j, row, att)
                    R, W, Rb, _ = dims_for(key, bottom_course=(c == 0))
                    e = abs(R - R0)
                    if bk is None or e < bk[0]:
                        bk = (e, (R, W, Rb, 2 * R, key))
                    if e < 0.004:
                        break
                stack[row] = bk[1]
            col["stack"] = stack
            # --- seat every row of this column ------------------------------
            for row in range(w.rows):
                R, W, Rb, _OD, key = stack[row]
                du = row_phase(row, w.rows)
                uu = u + du + (h01(j, c, 201) - 0.5) * 0.020
                if uu + R > total or uu - R < 0:
                    uu = u
                p, T, A, s = _at_u(w, L, seg, uu)
                lean = (h01(j, c, 202) - 0.5) * 0.018
                back = 0.0
                for r2 in range(row):
                    back += stack[r2][1] + ROW_GAP
                xy = p[:2] - A[:2] * (back + W * 0.5 - lean)
                zgv, own = C.world_ground_z(np.array([xy[0]]), np.array([xy[1]]))
                zgv = float(zgv[0]) if np.isfinite(zgv[0]) else float(p[2])
                flats = []
                gf = 0.0
                if c == 0:
                    gf = 0.010 + 0.0055 * (w.courses - 1) + 0.010 * h01(key, 61)
                    z = zgv + R - gf - BASE_EMBED_M
                else:
                    z = None
                    for below in layout[c - 1]:
                        if (c - 1, below["j"], row) not in seats:
                            continue
                        sb = seats[(c - 1, below["j"], row)]
                        d = uu + du * 0 - sb["u"]
                        rr = (R + sb["R"]) * (1.0 - SQUEEZE)
                        if abs(d) >= rr:
                            continue
                        zc = sb["z"] + math.sqrt(rr * rr - d * d)
                        if z is None or zc > z:
                            z = zc
                    if z is None:
                        z = zgv + R
                    # every tyre below that this one now touches is a contact
                    for below in layout[c - 1]:
                        if (c - 1, below["j"], row) not in seats:
                            continue
                        sb = seats[(c - 1, below["j"], row)]
                        d = uu - sb["u"]
                        dz = z - sb["z"]
                        dist = math.hypot(d, dz)
                        over = (R + sb["R"]) - dist
                        if over <= 0.0005:
                            continue
                        ang = math.atan2(-dz, -d)      # toward the tyre below
                        flats.append((ang, min(over * 0.5, 0.030), 1.0))
                seats[(c, j, row)] = dict(u=uu, z=z, R=R, W=W, Rb=Rb, key=key,
                                          xy=xy, zg=zgv, p=p, T=T, A=A, s=s,
                                          flats=flats, gf=gf, row=row, j=j, c=c)
    # --- contacts from the side and from above, now that every seat is known
    for (c, j, row), st in seats.items():
        for dj in (-1, 1):
            nb = seats.get((c, j + dj, row))
            if nb is None:
                continue
            d = nb["u"] - st["u"]
            dz = nb["z"] - st["z"]
            over = (st["R"] + nb["R"]) - math.hypot(d, dz)
            if over > 0.0005:
                st["flats"].append((math.atan2(dz, d),
                                    min(over * 0.5, 0.020), 0.75))
        for above in seats:
            if above[0] != c + 1 or above[2] != row:
                continue
            nb = seats[above]
            d = nb["u"] - st["u"]
            dz = nb["z"] - st["z"]
            over = (st["R"] + nb["R"]) - math.hypot(d, dz)
            if over > 0.0005 and dz > 0:
                st["flats"].append((math.atan2(dz, d),
                                    min(over * 0.5, 0.022), 0.9))
    # --- the bolt line, solved per (course, column) over the rows it threads
    for c in range(w.courses):
        for col in layout[c]:
            j = col["j"]
            rows = [r for r in rod_rows(w.rows) if (c, j, r) in seats]
            if not rows:
                continue
            hk = int((w.seed * 31 + j * 13 + c) % 2 ** 31)
            ang = math.pi * 0.5 + (h01(hk, 81) - 0.5) * 0.9
            ca, sa = math.cos(ang), math.sin(ang)
            z0 = seats[(c, j, rows[0])]["z"]
            band, dz = [], []
            for r in rows:
                st = seats[(c, j, r)]
                Hs = st["R"] - st["Rb"]
                band.append((st["Rb"] + Hs * 0.58, st["Rb"] + Hs * 0.84))
                dz.append(st["z"] - z0)
            dd = np.linspace(0.05, 0.60, 400)
            okm = np.ones(len(dd), bool)
            for k in range(len(rows)):
                rr = np.hypot(dd * ca, dd * sa - dz[k])
                okm &= (rr >= band[k][0]) & (rr <= band[k][1])
            feas = bool(okm.any())
            d = float(np.median(dd[okm])) if feas else \
                float(np.mean([b[0] + b[1] for b in band]) * 0.25)
            for r in range(w.rows):
                if (c, j, r) not in seats:
                    continue
                st = seats[(c, j, r)]
                hx = d * ca
                hz = d * sa - (st["z"] - z0)
                st["hole"] = (math.atan2(hz, hx), math.hypot(hx, hz))
                st["rod_ok"] = feas and (r in rows)
    # --- emit ----------------------------------------------------------------
    for (c, j, row), st in sorted(seats.items()):
        key, R, W = st["key"], st["R"], st["W"]
        pos = np.array([st["xy"][0], st["xy"][1], st["z"]])
        belt = 1.0 if w.belted else 0.0
        if wname == "t4":
            kc = belt_keep_clear()
            if kc[0] <= st["s"] <= kc[1]:
                belt = 0.0
        sq = 0.0018 + 0.0030 * belt
        flats = list(st["flats"])
        ey = st["A"].copy()
        ez = Zu.copy()
        ex = np.cross(ey, ez)
        ex /= max(np.linalg.norm(ex), 1e-9)
        # A wall built by hand is never plumb.  It is not wild either: the
        # tyres are bolted face to face and the belt is winched up, so the tilt
        # a real wall shows is 1-2 degrees -- and more than that walks the
        # drilled hole off the rod that goes through it.
        tilt_x = (h01(key, 71) - 0.5) * math.radians(1.9)
        tilt_z = (h01(key, 72) - 0.5) * math.radians(1.3)
        Mb = np.stack([ex, ey, ez], axis=1)
        Mw = _rot_axis(ex, tilt_x) @ _rot_axis(ez, tilt_z) @ Mb
        lod = 2 if lod_of is None else lod_of(pos, row)
        sp = spec_for(key, course=c, lod=lod, bottom_course=(c == 0),
                      flats=flats, ground_flat=st["gf"],
                      h_ground=st["z"] - st["zg"], seat_z=st["z"],
                      belt_pull=belt,
                      scuff=(0.85 if (c <= 1 and row == 0) else 0.0)
                      * h01(key, 91),
                      active_hole=st.get("hole"),
                      # THE FRONT ROW KEEPS ITS BORE: the water line inside the
                      # bead is the detail the manifest says sells the shot, and
                      # it is only visible in the row you can see into.  Every
                      # row behind it is packed with the leaf litter and grit
                      # that nobody has ever cleared out, which is both true and
                      # what stops the wall being a bundle of telescopes.
                      fill=(0.0 if row == 0 else
                            (0.45 + 0.55 * h01(key, 1301))),
                      back_lod=min(3, lod + (1 if row == 0 else 0)))
        sites.append(dict(key=key, col=j, course=c, row=row, s=st["s"],
                          u=st["u"], pos=pos, M=Mw, Mb=Mb, R=R, W=W,
                          kind=sp.kind, flats=flats, spec=sp,
                          hole=(sp.holes[0][0], sp.holes[0][1]),
                          rod_ok=bool(st.get("rod_ok", False)), wall=wname,
                          zg=st["zg"], belt=belt))
    return sites



def _rot_axis(axis, ang):
    a = np.asarray(axis, float)
    a = a / max(np.linalg.norm(a), 1e-9)
    c, s = math.cos(ang), math.sin(ang)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) * c + K * s + np.outer(a, a) * (1 - c)


def hole_sites(site):
    """Every drilled hole in one tyre, in WORLD coordinates.

    -> list of dict(origin, axis, radius, active, depth) where `origin` is the
    centre of the hole on the OUTER face of the front sidewall and `axis` is the
    tyre's axle direction.  `tyre_wall_through_rod` threads the active one.
    """
    sp = site["spec"]
    M, pos = site["M"], site["pos"]
    out = []
    for (th, rr, a, active, seed) in sp.holes:
        loc = np.array([math.cos(th) * rr, sp.W * 0.5, math.sin(th) * rr])
        loc2 = np.array([math.cos(th) * rr, -sp.W * 0.5, math.sin(th) * rr])
        out.append(dict(origin=pos + M @ loc, exit=pos + M @ loc2,
                        axis=M @ np.array([0.0, 1.0, 0.0]), radius=a,
                        active=bool(active), through=sp.W))
    return out


def rod_sites(wname):
    """One M16 through-rod per (column, course), threading every row.

    The rod is FITTED to the holes that were actually drilled, not assumed: the
    axis is the least-squares line through the six hole centres of the group
    (entry and exit of each of the three tyres), which is what a rod pushed
    through three slightly-tilted tyres does.  `clearance` is the worst gap
    between the rod's surface and the wall of the hole it passes through — it is
    negative when the rod fits, and `rod_sites` REFUSES to emit a rod whose
    group has no feasible bolt line rather than publish one that misses.

    -> dict(origin, end, axis, length, radius, clearance, col, course, s)
    """
    sites = tyre_sites(wname)
    keep = set(rod_rows(wall(wname).rows))
    byc = {}
    for s in sites:
        if s["row"] not in keep:
            continue
        byc.setdefault((s["col"], s["course"]), []).append(s)
    out = []
    for (col, course), grp in sorted(byc.items()):
        grp.sort(key=lambda x: x["row"])
        if not all(x["rod_ok"] for x in grp):
            continue
        P, rad = [], []
        for x in grp:
            h = hole_sites(x)[0]
            P += [h["origin"], h["exit"]]
            rad += [h["radius"], h["radius"]]
        P = np.asarray(P, float)
        ctr = P.mean(axis=0)
        u, sv, vt = np.linalg.svd(P - ctr)
        ax = vt[0]
        A0 = grp[0]["Mb"] @ np.array([0.0, 1.0, 0.0])
        if np.dot(ax, A0) < 0:
            ax = -ax
        t = (P - ctr) @ ax
        perp = np.linalg.norm((P - ctr) - np.outer(t, ax), axis=1)
        clr = float(np.max(perp + 0.008 - np.asarray(rad)))
        if clr > 0.0:
            # No rod here.  The three tyres in this line were drilled where the
            # solver said they could be, and after their hand-stacked tilt the
            # holes no longer share a straight line -- so the wall builder used
            # the next position instead.  Publishing a rod that fouls 3 mm of
            # rubber would be a lie the render would show.
            continue
        o = ctr + ax * (t.min() - 0.045)
        e = ctr + ax * (t.max() + 0.045)
        out.append(dict(col=col, course=course, origin=o, end=e, axis=ax,
                        length=float(np.linalg.norm(e - o)), radius=0.008,
                        clearance=clr, s=grp[0]["s"], wall=wname))
    return out


def face_envelope(wname, dz=0.22, ds=None):
    """The bulged surface the conveyor belt has to drape over.

    -> dict(s, z, out) where `out[i, k]` is how far the tyre face stands proud
    of the wall's design line at station s[i] and height z[k], in metres.  A
    belt hung flat is the named failure; this is the 0.62 m ripple it has to
    follow, and the 3 mm step where the courses stagger.
    """
    sites = [s for s in tyre_sites(wname) if s["row"] == 0]
    if not sites:
        return None
    w = wall(wname)
    ss = np.array(sorted(set(round(s["s"], 3) for s in sites)))
    zs = np.arange(0.06, 2.05, dz)
    out = np.zeros((len(ss), len(zs)))
    for s in sites:
        sp = s["spec"]
        i = int(np.argmin(np.abs(ss - s["s"])))
        for k, z in enumerate(zs):
            dzc = z - (s["pos"][2] - s["zg"])
            if abs(dzc) > sp.R:
                continue
            r = math.sqrt(max(sp.R ** 2 - dzc ** 2, 0.0))
            # lateral half-width of the carcass at that radius
            f = clamp01((r - sp.Rb) / max(sp.Hs, 1e-6))
            y = sp.bw + (sp.W * 0.5 - sp.bw) * min(1.0, (f / max(sp.maxw_at, 1e-3))) ** 0.6
            if f > sp.maxw_at:
                y = sp.W * 0.5 - (sp.W * 0.5 - sp.Wt * 0.5) * \
                    ((f - sp.maxw_at) / max(1.0 - sp.maxw_at, 1e-3)) ** 1.55
            out[i, k] = max(out[i, k], y * 2.0 - sp.W * 0.5)
    return dict(s=ss, z=zs, out=out)


def stack_column(n, key0, ground_z, upright=True, scale=1.0):
    """The seating of a free-standing stack of `n` tyres — what
    `tyre_stack_trackside` needs to put 129 of them at gates and laybys.

    -> list of dict(key, spec_kwargs, z, flat).  Upright means the axis is
    VERTICAL (tread out, the tyres you see at a gate); the compression is then
    carried on the tread, not the sidewall, so the flats are on the crown.
    """
    out = []
    z = ground_z
    for i in range(n):
        key = int((key0 * 7919 + i * 131) % 2 ** 31)
        R, W, Rb, OD = dims_for(key, bottom_course=(i == 0), scale=scale)
        load = (n - i) / max(n, 1)
        if upright:
            flat = 0.004 + 0.012 * load
            zc = z + W * 0.5 - (BASE_EMBED_M if i == 0 else 0.0)
            out.append(dict(key=key, z=zc, flat=flat, R=R, W=W, axis="z",
                            course=i))
            z = zc + W * 0.5 - flat
        else:
            flat = 0.006 + 0.016 * load
            zc = z + R - flat - (BASE_EMBED_M if i == 0 else 0.0)
            out.append(dict(key=key, z=zc, flat=flat, R=R, W=W, axis="y",
                            course=i))
            z = zc + R - flat
    return out


TOP_Z = None            # measured by selftest(); the wall's built height


# ==============================================================================
# 13.  BUILD
# ==============================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for cname in (COLL,):
        root = bpy.data.collections.get(cname)
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
            if d.name.startswith(PFX) or d.name.startswith(XPFX):
                try:
                    lib.remove(d)
                except Exception:
                    pass


def lod_rule(cam_xy, row):
    """Mesh density graded by distance to the lens, which is the only thing
    that decides how much detail an object is allowed to cost."""
    cam = np.asarray(cam_xy, float)

    def f(pos, r):
        d = float(np.linalg.norm(np.asarray(pos, float)[:3] - cam))
        if r == 0:
            return 0 if d < 4.8 else (1 if d < 8.5 else (2 if d < 22.0 else 3))
        if r == 1:
            return 1 if d < 5.0 else (2 if d < 11.0 else 3)
        return 2 if d < 6.0 else 3
    return f


def _instancer_group(name, library, seed):
    """Instance-on-points from a collection, one source per point, chosen by a
    baked INT attribute rather than at random — so the wall is reproducible and
    the same tyre never lands next to itself."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); gi.location = (-700, 0)
    go = ng.nodes.new("NodeGroupOutput"); go.location = (700, 0)
    ci = ng.nodes.new("GeometryNodeCollectionInfo"); ci.location = (-700, -240)
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); iop.location = (250, 0)
    iop.inputs["Pick Instance"].default_value = True
    aidx = ng.nodes.new("GeometryNodeInputNamedAttribute")
    aidx.location = (-380, -520)
    aidx.data_type = "INT"
    aidx.inputs["Name"].default_value = "twt_idx"
    arot = ng.nodes.new("GeometryNodeInputNamedAttribute")
    arot.location = (-380, -700)
    arot.data_type = "FLOAT_VECTOR"
    arot.inputs["Name"].default_value = "twt_rot"
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    ng.links.new(aidx.outputs[0], iop.inputs["Instance Index"])
    ng.links.new(arot.outputs[0], iop.inputs["Rotation"])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    return ng


def _mat_to_euler(M):
    from mathutils import Matrix
    return Matrix(((M[0][0], M[0][1], M[0][2]),
                   (M[1][0], M[1][1], M[1][2]),
                   (M[2][0], M[2][1], M[2][2]))).to_euler()


def build(walls=("t4",), cam_xy=None, scene=None, stats=None, near_only=None,
          field=True, mats=None):
    """Emit the item.

    The tyres near the lens are INDIVIDUAL OBJECTS with individual meshes — no
    two of the 300-odd tyres in front of the camera share a vertex.  The rest of
    the wall is instanced from those same meshes through geometry nodes, which
    is the only way 2 255 hero tyres fit in a machine, and is honest because at
    30 m a repeat is smaller than a pixel of difference.
    """
    scene = scene or bpy.context.scene
    root = _coll(COLL)
    mats = mats or [mat_tyre(), mat_water()]
    st = stats if stats is not None else {}
    st.setdefault("tyres", 0)
    st.setdefault("objects", 0)
    st.setdefault("verts", 0)
    st.setdefault("quads", 0)
    st.setdefault("tris", 0)
    st.setdefault("lod", [0, 0, 0, 0])
    st.setdefault("kinds", {})
    st.setdefault("instanced", 0)

    lod_of = lod_rule(cam_xy, 0) if cam_xy is not None else None
    for wname in walls:
        sites = tyre_sites(wname, lod_of=lod_of)
        st["tyres"] += len(sites)
        # who is built for real: everything the lens can resolve
        if cam_xy is None:
            real = sites
        else:
            cam = np.asarray(cam_xy, float)
            real = [s for s in sites
                    if np.linalg.norm(s["pos"] - cam) <
                    (near_only if near_only else (22.0 if s["row"] == 0 else 11.0))]
        realset = set(id(s) for s in real)
        libs = {}
        made = {}
        for s in real:
            sp = s["spec"]
            bucket = (s["course"], 0 if s["row"] == 0 else 1)
            lib = libs.get(bucket)
            if lib is None:
                lib = _coll("%sSrc_%s_c%d_r%d" % (PFX, wname, bucket[0],
                                                  bucket[1]), root)
                libs[bucket] = lib
                made[bucket] = []
            nm = "%sT_%s_c%d_r%d_%04d" % (PFX, wname, s["course"], s["row"],
                                          len(made[bucket]))
            ob, m = build_tyre_object(sp, name=nm, coll=lib, mats=mats,
                                      world_z0=float(s["pos"][2] - s["zg"]))
            ob.location = tuple(s["pos"])
            ob.rotation_euler = _mat_to_euler(s["M"])
            made[bucket].append(ob)
            st["objects"] += 1
            st["verts"] += m["verts"]
            st["quads"] += m["quads"]
            st["tris"] += 2 * m["quads"] + m["tris"]
            st["lod"][sp.lod] += 1
            st["kinds"][sp.kind] = st["kinds"].get(sp.kind, 0) + 1
        if not field:
            continue
        # ---- the rest of the wall, instanced from those meshes -------------
        pts = {}
        for s in sites:
            if id(s) in realset:
                continue
            bucket = (s["course"], 0 if s["row"] == 0 else 1)
            if bucket not in made or not made[bucket]:
                continue
            pts.setdefault(bucket, []).append(s)
        for bucket, ss in sorted(pts.items()):
            lib = libs[bucket]
            n = len(made[bucket])
            me = bpy.data.meshes.new("%sField_%s_c%d_r%d" % (PFX, wname,
                                                             bucket[0], bucket[1]))
            co = np.array([s["pos"] for s in ss], float)
            me.vertices.add(len(co))
            me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
            me.update()
            ai = me.attributes.new("twt_idx", "INT", "POINT")
            idx = np.array([int(h01(s["key"], 611) * n) % n for s in ss], np.int32)
            ai.data.foreach_set("value", idx)
            ar = me.attributes.new("twt_rot", "FLOAT_VECTOR", "POINT")
            eul = np.array([list(_mat_to_euler(s["M"])) for s in ss], np.float32)
            ar.data.foreach_set("vector", eul.ravel())
            ob = bpy.data.objects.new(me.name, me)
            root.objects.link(ob)
            ng = _instancer_group(me.name + "_NG", lib, bucket[0] * 7 + bucket[1])
            md = ob.modifiers.new("instance", "NODES")
            md.node_group = ng
            st["instanced"] += len(ss)

    C.stamp(root)
    root["item"] = ITEM
    root["tyres"] = st["tyres"]
    log("BUILT %d tyres: %d real objects (%.2f M tris, LOD %s), %d instanced; "
        "kinds %s" % (st["tyres"], st["objects"], st["tris"] / 1e6, st["lod"],
                      st["instanced"], st["kinds"]))
    return root


# ==============================================================================
# 14.  STAND-INS  —  owned by OTHER items, prefix TWTSTAND_
# ==============================================================================
# The belt (tyre_wall_belt_facing), the rods (tyre_wall_through_rod), the ground
# (build_barriers' runoff platform) and the guardrail behind do not exist yet.
# A macro of a floating wall of tyres against the sky would be a worse test than
# one in its setting, so there are stand-ins — under a prefix the gate is NOT run
# with, so not one triangle of them is measured as this item's work.

def _mat_standin(name, col, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(XPFX + name)
    if m:
        return m
    t = NT(XPFX + name)
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    n1 = t.noise(P, 18.0, 6.0, 0.6)
    n2 = t.noise(P, 220.0, 5.0, 0.6)
    v = t.vor(P, 60.0, "F1", 0, 0.9)
    c = t.cmix(t.maprange(n1, 0.35, 0.68, 0.0, 1.0), col,
               tuple(x * 1.55 for x in col))
    c = t.cmix(t.maprange(v, 0.0, 0.5, 0.0, 0.6), c, tuple(x * 0.6 for x in col))
    b = t.bump(t.math("ADD", t.math("MULTIPLY", n2, 0.6),
                      t.math("MULTIPLY", n1, 0.4)), 0.4, 0.004)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    names = [s.name for s in bsdf.inputs]
    t.pin(bsdf, 0, c)
    t.pin(bsdf, names.index("Roughness"),
          t.fmix(t.maprange(n2, 0.3, 0.7, 0, 1), rough, min(1.0, rough + 0.15)))
    t.pin(bsdf, names.index("Metallic"), metal)
    if "Normal" in names:
        t.pin(bsdf, names.index("Normal"), b)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return t.m


def build_standins(coll, wname, cam_xy, half=26.0):
    """Ground, guardrail and belt strips, near the camera only."""
    from mathutils import Vector
    cam = np.asarray(cam_xy, float)
    w = wall(wname)
    # ---- ground: the runoff platform this wall stands on -------------------
    cell = 0.15
    n = int(half * 2 / cell)
    gx = np.linspace(cam[0] - half, cam[0] + half, n)
    gy = np.linspace(cam[1] - half, cam[1] + half, n)
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    GZ, own = C.world_ground_z(GX.ravel(), GY.ravel())
    GZ = np.where(np.isfinite(GZ), GZ, np.nanmedian(GZ[np.isfinite(GZ)]))
    GZ = GZ.reshape(GX.shape)
    GZ = GZ + 0.010 * (vnoise1(GX * 7.0, 11) + vnoise1(GY * 9.0, 13) - 1.0)
    V = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=1)
    q = _grid_quads(n, n, wrap_i=False)
    me = _new_mesh(XPFX + "Ground", V, q, None, smooth_deg=25.0)
    me.materials.append(_mat_standin("Grass", (0.0300, 0.0400, 0.0175), 0.92))
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    # ---- guardrail behind the wall ------------------------------------------
    s = np.arange(T4_WALL_S[0], T4_WALL_S[1], 0.5)
    Pb = np.asarray(C.su_to_world(s, C.barrier_offset(s, +1), side=+1), float)
    zb, _ = C.world_ground_z(Pb[:, 0], Pb[:, 1])
    Pb[:, 2] = np.where(np.isfinite(zb), zb, Pb[:, 2])
    keep = np.linalg.norm(Pb - cam, axis=1) < half * 1.6
    Pb = Pb[keep]
    if len(Pb) > 3:
        zs = [0.072, 0.384, 0.700]
        V, Q = [], []
        base = 0
        for z0 in zs:
            for k, dz in enumerate((0.0, 0.312)):
                for p in Pb:
                    V.append([p[0], p[1], p[2] + z0 + dz])
            for i in range(len(Pb) - 1):
                Q.append((base + i, base + i + 1,
                          base + len(Pb) + i + 1, base + len(Pb) + i))
            base += 2 * len(Pb)
        me = _new_mesh(XPFX + "Armco", np.asarray(V), np.asarray(Q, np.int64),
                       None, smooth_deg=25.0)
        me.materials.append(_mat_standin("Zinc", (0.2550, 0.2620, 0.2750),
                                         0.42, 0.85))
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
    # ---- conveyor belt facing, on the belted part of the run ---------------
    sites = [x for x in tyre_sites(wname) if x["row"] == 0 and x["belt"] > 0.5]
    if sites:
        env = {}
        for x in sites:
            env.setdefault(round(x["s"], 2), []).append(x)
        ss = sorted(env)
        V, Q = [], []
        base = 0
        strip_z = [(0.10, 0.34), (0.72, 0.96), (1.34, 1.58)]
        for (z0, z1) in strip_z:
            rows = []
            for si in ss:
                x0 = env[si][0]
                p = x0["pos"]
                A = x0["M"] @ np.array([0.0, 1.0, 0.0])
                sag = 0.020 * math.sin(math.pi * ((si - ss[0]) /
                                                  max(ss[-1] - ss[0], 1e-6)))
                bulge = 0.012 * math.cos(2 * math.pi * si / PITCH)
                for z in (z0, z1):
                    q = (np.array([p[0], p[1], x0["zg"] + z])
                         + A * (x0["W"] * 0.5 + 0.006 + sag + bulge))
                    rows.append(q)
            nn = len(ss)
            for v in rows:
                V.append(v)
            for i in range(nn - 1):
                Q.append((base + 2 * i, base + 2 * i + 2, base + 2 * i + 3,
                          base + 2 * i + 1))
            base += 2 * nn
        me = _new_mesh(XPFX + "Belt", np.asarray(V), np.asarray(Q, np.int64),
                       None, smooth_deg=30.0)
        me.materials.append(_mat_standin("BeltRubber", (0.0215, 0.0208, 0.0205),
                                         0.72))
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
    # ---- through-rod ends, in the holes that are actually drilled ----------
    rods = [r for r in rod_sites(wname)
            if np.linalg.norm(r["origin"] - cam) < 14.0]
    if rods:
        V, Q = [], []
        base = 0
        for r in rods:
            ax = r["axis"]
            up = np.array([0.0, 0.0, 1.0])
            e1 = np.cross(ax, up)
            e1 /= max(np.linalg.norm(e1), 1e-9)
            e2 = np.cross(ax, e1)
            for t in (0.0, r["length"]):
                for k in range(10):
                    a = 2 * math.pi * k / 10
                    V.append(r["origin"] + ax * t
                             + (e1 * math.cos(a) + e2 * math.sin(a)) * r["radius"])
            for k in range(10):
                Q.append((base + k, base + (k + 1) % 10,
                          base + 10 + (k + 1) % 10, base + 10 + k))
            base += 20
        me = _new_mesh(XPFX + "Rod", np.asarray(V), np.asarray(Q, np.int64),
                       None, smooth_deg=32.0)
        me.materials.append(_mat_standin("RodSteel", (0.1600, 0.1600, 0.1620),
                                         0.38, 0.9))
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)


def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them."""
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
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2 elev %.2f deg bearing %.2f deg; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.01
    cd.clip_end = 20000.0
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
    return ob


# ==============================================================================
# 15.  THE TEST SCENE
# ==============================================================================

def hero_aim(wname="t4", s=None, course=1):
    """The tyre the macro is shot at, and where the Beat-5 lens actually sits.

    circuit_spec parks a 21 mm lens ON THE INSIDE KERB of T4 at z = +0.85 for
    10.6 s.  The camera below is on the line from that vantage to this tyre, at
    EXACTLY the manifest's 3.800 m — so the direction is the film's and the
    distance is the manifest's, and neither is a guess.
    """
    s = hero_station() if s is None else s
    sites = [x for x in tyre_sites(wname) if x["row"] == 0 and x["course"] == course]
    site = min(sites, key=lambda x: abs(x["s"] - s))
    A = site["M"] @ np.array([0.0, 1.0, 0.0])
    aim = site["pos"] + A * (site["W"] * 0.5)
    V = np.asarray(C.su_to_world(np.array([site["s"]]),
                                 np.array([HERO_CAM_LAT]), side=+1), float)[0]
    zg, _ = C.world_ground_z(np.array([V[0]]), np.array([V[1]]))
    vant = np.array([V[0], V[1], (float(zg[0]) if np.isfinite(zg[0]) else V[2])
                     + HERO_CAM_Z])
    d = vant - aim
    d = d / max(np.linalg.norm(d), 1e-9)
    cam = aim + d * FILMED_AT_M
    return dict(site=site, aim=aim, cam=cam, A=A, vantage=vant,
                dist=float(np.linalg.norm(cam - aim)))


def test_scene(samples=256, near=0.0, field=True):
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    purge()
    root = _coll(COLL)
    aim = hero_aim()
    log("hero tyre: s %.1f  %s  OD %.3f  key %d" %
        (aim["site"]["s"], aim["site"]["kind"], 2 * aim["site"]["R"],
         aim["site"]["key"]))
    log("camera at %.3f m on a %.0f mm lens (manifest: %.3f m / %.0f mm)"
        % (aim["dist"], LENS_MM, FILMED_AT_M, LENS_MM))
    st = {}
    build(walls=("t4",), cam_xy=aim["cam"], scene=scene, stats=st,
          near_only=(near or None), field=field)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)
    build_standins(stand, "t4", aim["cam"], half=42.0)

    site = aim["site"]
    A = aim["A"]
    up = np.array([0.0, 0.0, 1.0])
    tang = site["M"] @ np.array([1.0, 0.0, 0.0])
    macro = add_camera(PFX + "CAM_MACRO", tuple(aim["cam"]), tuple(aim["aim"]),
                       LENS_MM, cams)
    add_camera(PFX + "CAM_SHOT", tuple(aim["cam"]), tuple(aim["aim"]),
               LENS_MM, cams, fstop=3.5)
    # straight into the bore: the water line and the inner liner
    # Into the bore from above the axis, which is the only angle that sees the
    # water line: the standing water tops out at z = -Rb, exactly the bottom lip
    # of the hole, so a camera on the axis sees it edge-on and sees nothing.
    bore = site["pos"] + A * 0.95 + up * 0.30 + tang * 0.06
    add_camera(PFX + "CAM_BORE", tuple(bore),
               tuple(site["pos"] - up * site["R"] * 0.34), 45.0, cams)
    # square on the sidewall: lettering, serrations, the drilled hole
    add_camera(PFX + "CAM_SIDEWALL",
               tuple(site["pos"] + A * 0.90 + up * 0.10 + tang * 0.05),
               tuple(site["pos"] + up * 0.10), 58.0, cams)
    # the top course from above: the tread and the belt line
    top = [x for x in tyre_sites("t4")
           if x["row"] == 0 and x["course"] == 2 and abs(x["s"] - site["s"]) < 0.7]
    if top:
        tp = top[0]
        add_camera(PFX + "CAM_TREAD",
                   tuple(tp["pos"] + A * 0.42 + up * 0.62),
                   tuple(tp["pos"] + up * tp["R"] * 0.92), 50.0, cams)
    # the wall in its setting, from the vantage the film actually uses
    add_camera(PFX + "CAM_WIDE",
               tuple(aim["vantage"] + A * 0.0),
               tuple(site["pos"] + tang * 3.0), 35.0, cams)
    add_camera(PFX + "CAM_ALONG",
               tuple(site["pos"] + A * 1.30 - tang * 7.0 + up * 0.75),
               tuple(site["pos"] + tang * 9.0 + up * 0.45), 50.0, cams)
    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 8
    scene.cycles.use_denoising = True
    return root, st, aim


# ==============================================================================
# 16.  MEASUREMENT
# ==============================================================================

def _edge_stats(V, Q, T):
    E = []
    if len(Q):
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
            E.append(np.linalg.norm(V[Q[:, a]] - V[Q[:, b]], axis=1))
    if len(T):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            E.append(np.linalg.norm(V[T[:, a]] - V[T[:, b]], axis=1))
    E = np.concatenate(E)
    return E


def selftest():
    """Measure what the gate cannot: the section, the population, the wall's
    height, and whether a rod can actually pass through the holes."""
    ok = True
    print("=" * 78)
    print("tyre_wall_tyre selftest   (%.1f px/m at %.1f m / %.0f mm; 1 px = %.3f mm)"
          % (PX_PER_M, FILMED_AT_M, LENS_MM, PX_M * 1000))
    print("=" * 78)

    # --- one tyre of each kind, at each LOD ---------------------------------
    for lod in (0, 1, 2, 3):
        for kind in WALL_KINDS:
            sp = spec_for(4242, kind=kind, lod=lod, ground_flat=0.014,
                          flats=[(0.0, 0.003, 0.7), (math.pi, 0.003, 0.7)])
            V, Q, T, M, MT, A = tyre_mesh_data(sp, 0.55)
            E = _edge_stats(V, Q, T)
            p10 = float(np.percentile(E, 10))
            dmin = float(E.min())
            print("LOD%d %-6s %7d v %7d q %6d t   p10 %6.3f mm = %5.2f px   "
                  "med %6.3f mm   min %.4f mm"
                  % (lod, kind, len(V), len(Q), len(T), p10 * 1000,
                     p10 * PX_PER_M, float(np.percentile(E, 50)) * 1000,
                     dmin * 1000))
            if lod == 0 and p10 * PX_PER_M > 6.0:
                print("      ** p10 above the hero limit of 6 px")
                ok = False
            if dmin < 1e-5:
                print("      ** DEGENERATE edge (%.2e m): a zero-length edge is "
                      "a free pass on a p10 check and must never exist." % dmin)
                ok = False

    # --- the population -----------------------------------------------------
    sites = tyre_sites("t4")
    ODs = np.array([2 * s["R"] for s in sites])
    kinds = {}
    for s in sites:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print("\nT4 wall: %d tyres, %d columns, %d rows x %d courses"
          % (len(sites), 1 + max(s["col"] for s in sites),
             1 + max(s["row"] for s in sites),
             1 + max(s["course"] for s in sites)))
    print("  OD  %.3f - %.3f m, mean %.3f, CV %.4f"
          % (ODs.min(), ODs.max(), ODs.mean(), ODs.std() / ODs.mean()))
    print("  kinds " + "  ".join("%s %d (%.0f %%)" % (k, v, 100.0 * v / len(sites))
                                 for k, v in sorted(kinds.items())))
    tops = [s["pos"][2] - s["zg"] + s["R"] for s in sites if s["course"] == 2]
    global TOP_Z
    TOP_Z = float(np.mean(tops))
    print("  top of wall %.3f m above the datum (min %.3f, max %.3f); the "
          "contract's TRANSIT_SOUTH_TOP_Z is %.2f"
          % (TOP_Z, min(tops), max(tops), C.TRANSIT_SOUTH_TOP_Z))
    if not (1.75 <= TOP_Z <= 2.15):
        print("      ** the wall is not the height the contract says it is")
        ok = False
    emb = [s["zg"] - (s["pos"][2] - s["R"] + s["spec"].ground_flat)
           for s in sites if s["course"] == 0]
    print("  bottom course embeds %.4f - %.4f m (contract minimum %.3f)"
          % (min(emb), max(emb), BASE_EMBED_M))
    if min(emb) < BASE_EMBED_M - 1e-6:
        print("      ** something is standing on the ground, not in it")
        ok = False

    # --- can a rod actually go through the holes? ---------------------------
    rods = rod_sites("t4")
    worst = max([r["clearance"] for r in rods]) if rods else 0.0
    ncol = len(set((s["col"], s["course"]) for s in sites if s["row"] == 0))
    print("\n  %d through-rods emitted of %d (column, course) groups "
          "(%.0f %%);\n  worst rod-surface-to-hole-wall clearance %+.4f m "
          "(must be <= 0, measured against the DRILLED holes)"
          % (len(rods), ncol, 100.0 * len(rods) / max(ncol, 1), worst))
    if worst > 0.0:
        print("      ** a rod fouls its hole: the wall is bolted through rubber "
              "that is not drilled")
        ok = False

    # --- variation: is any two tyres the same object? -----------------------
    keys = [s["key"] for s in sites]
    print("  %d distinct tyre keys out of %d sites" % (len(set(keys)), len(keys)))
    sig = set()
    for s in sites[:300]:
        sp = s["spec"]
        sig.add((sp.kind, round(sp.R, 4), round(sp.W, 4), round(sp.Rb, 4),
                 sp.brand, sp.size_text, len(sp.holes), round(sp.age, 3)))
    print("  %d distinct (kind, R, W, rim, brand, size, holes, age) signatures "
          "in the first 300" % len(sig))
    if len(sig) < 250:
        print("      ** not enough real difference between tyres")
        ok = False

    # --- the water line -----------------------------------------------------
    n_wet = sum(1 for s in sites if s["spec"].water >= 0.34)
    print("  %d of %d tyres (%.0f %%) still hold water; the line sits at "
          "z = -Rb, the bottom of the bore"
          % (n_wet, len(sites), 100.0 * n_wet / len(sites)))

    # --- the belt's envelope ------------------------------------------------
    env = face_envelope("t4")
    if env is not None:
        o = env["out"]
        print("  face envelope: %d stations x %d heights, bulge %.3f - %.3f m, "
              "ripple sd %.4f m" % (o.shape[0], o.shape[1], o[o > 0].min(),
                                    o.max(), float(np.std(o[o > 0]))))
    print("\n%s" % ("SELFTEST PASS" if ok else "SELFTEST FAIL"))
    return ok


def dump_interface(path=None):
    """Everything a dependant needs, without importing this module."""
    path = path or os.path.join(_HERE, "%s_interface.json" % ITEM)
    out = dict(item=ITEM, version=__version__,
               filmed_at_m=FILMED_AT_M, lens_mm=LENS_MM,
               px_per_m=PX_PER_M, instances_declared=INSTANCES_DECLARED,
               archetypes={k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                               for kk, vv in v.items()}
                           for k, v in ARCH.items()},
               pitch_m=PITCH, squeeze=SQUEEZE, row_gap_m=ROW_GAP,
               base_embed_m=BASE_EMBED_M,
               belt_keep_clear_s=list(belt_keep_clear()),
               hero_station_s=hero_station(),
               walls={}, attrs=list(ATTRS), obj_props=list(OBJ_PROPS),
               materials=[PFX + "Rubber", PFX + "Water"],
               collection=COLL, prefix=PFX)
    for wn in ("t4", "transit_south"):
        w = wall(wn)
        sites = tyre_sites(wn)
        rods = rod_sites(wn)
        tops = [s["pos"][2] - s["zg"] + s["R"] for s in sites
                if s["course"] == w.courses - 1]
        out["walls"][wn] = dict(
            desc=w.desc, rows=w.rows, courses=w.courses, tyres=len(sites),
            columns=1 + max(s["col"] for s in sites), rods=len(rods),
            top_z_mean=float(np.mean(tops)),
            s_range=[float(np.min(w.S)), float(np.max(w.S))],
            sites=[dict(key=s["key"], col=s["col"], course=s["course"],
                        row=s["row"], s=round(float(s["s"]), 3),
                        pos=[round(float(v), 5) for v in s["pos"]],
                        R=round(float(s["R"]), 5), W=round(float(s["W"]), 5),
                        kind=s["kind"],
                        hole=[round(float(s["hole"][0]), 5),
                              round(float(s["hole"][1]), 5)])
                   for s in sites],
            rod_sites=[dict(col=r["col"], course=r["course"],
                            origin=[round(float(v), 5) for v in r["origin"]],
                            axis=[round(float(v), 5) for v in r["axis"]],
                            length=round(float(r["length"]), 5),
                            radius=r["radius"]) for r in rods])
        env = face_envelope(wn)
        if env is not None:
            out["walls"][wn]["face_envelope"] = dict(
                s=[round(float(v), 3) for v in env["s"]],
                z=[round(float(v), 3) for v in env["z"]],
                out=[[round(float(v), 5) for v in row] for row in env["out"]])
    json.dump(out, open(path, "w"), indent=1)
    log("interface -> %s (%.1f kB)" % (path, os.path.getsize(path) / 1024.0))
    return path


def main():
    ap = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--interface", action="store_true")
    ap.add_argument("--save", default=None)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--near", type=float, default=0.0)
    ap.add_argument("--nofield", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        ok = selftest()
        if a.interface:
            dump_interface()
        sys.exit(0 if ok else 1)
    if a.interface and not a.test:
        dump_interface()
        return
    if a.test:
        root, st, aim = test_scene(samples=a.samples, near=a.near,
                                   field=not a.nofield)
        if a.interface:
            dump_interface()
        if a.save:
            p = a.save if os.path.isabs(a.save) else os.path.join(_ROOT, a.save)
            bpy.ops.wm.save_as_mainfile(filepath=p)
            log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1e6))


if __name__ == "__main__":
    main()

