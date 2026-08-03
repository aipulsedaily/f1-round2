#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
showroom_facade_panel.py -- per-item hero campaign, item ``showroom_facade_panel``
zone ``showroom_breach``, wave 1, build order 102, HERO, 180 instances,
3 dependants (``showroom_signage_lettering``, ``showroom_rainwater_goods``,
``showroom_parapet_coping``).

WHAT THIS IS
============
The anodised aluminium RAINSCREEN CASSETTE that clads the showroom's upper
fascia: the 4.000 m band of metal between the head of the curtain wall
(z = 6.250) and the parapet (z = 10.400), on the two elevations the film sees --
the EAST face the car is launched through and the SOUTH face it turns past.
180 cassettes, four courses of 45, every one of them its OWN mesh with its own
buckling modes, its own fabrication tolerance, its own hang and its own history.

A cassette is not a plane with a metal shader on it.  It is a 3.0 mm sheet
press-braked back 90 deg at all four edges over a 4.5-5.5 mm outer radius,
folded again to a 22 mm stiffening lip, stiffened across the back with bonded
top-hats, hung on two hooks off a T-rail, and separated from its neighbours by a
15 mm OPEN DRAINED JOINT you can see 90 mm into.  Every one of those is mesh
here, because at this item's filmed distance every one of them is several pixels
across.

THE ARITHMETIC THAT SETS THE DETAIL FLOOR
-----------------------------------------
    manifest: nearest_camera_m 3.6, lens_at_closest_mm 35, HERO,
              onscreen_px_4k 1244 over px_measured_dimension_m 1.2,
              instances 180, variation_axes = anodising batch drift /
              oil-canning / fixing shadow gaps

    px_per_m = (3840 * 35 / 36) / 3.6 = 1037.04 px/m   ->   1 px = 0.9643 mm

so the hero gate's 6 px allowance for the 10th-percentile edge is 5.79 mm, and a
0.4 mm chip in the anodic film is 0.4 px.  What that number really decides is
the FRONTIER BETWEEN MESH AND NORMAL, and this module puts it at 1 mm:

    MESH, because it changes the silhouette by a pixel or more
        15.0 mm open joint (15.6 px) and the 90 mm you see into it
        5.5 / 4.5 mm outer fold radius (5.7 / 4.7 px) and the arris octant
        3.0 mm sheet section at the lip (3.1 px) with a 0.5 mm cut chamfer
        32 / 35 mm return, 22 mm stiffening lip
        oil-canning, p50 1.6 mm p95 5.2 mm (1.7 / 5.4 px)
        the twist and bow that turn every joint into a WEDGE
        4.8 mm domed rivets 1.6 mm proud on a 9.5 mm flange
        25-70 mm handling dents, 0.15-0.85 mm deep, WITH THEIR RAISED RIMS
        45 mm drip return and 9 mm weep slots on the bottom course
        louvre blades, bird mesh, cam locks, 6 mm perforations, sign bosses
        bonded top-hat stiffeners and the hook brackets behind the joint

    NORMAL DOMAIN, because 0.96 mm/px makes them shading and not shape
        the stucco emboss the sheet is rolled with: 7 mm pillows 0.22 mm deep.
        0.22 mm is 0.23 px of displacement -- a mesh that carried it would need
        1.5 mm cells (0.8 M quads/panel, 140 M for the item) to represent a
        feature whose entire silhouette contribution is a quarter of a pixel.
        It is the single loudest thing on this surface at 3.6 m and it is a
        BUMP, deliberately, with the arithmetic stated rather than hidden.
        the peen generation nested inside it, 2.6 mm at 0.07 mm
        the rolling grain, 0.15 mm across at 12 um
        the etch mottle at 1.2 mm and 18 um
        oxide crazing on the outside of every fold radius

WHY THE EMBOSS IS THERE AT ALL, AND WHY IT IS NOT A GATE-DODGE
--------------------------------------------------------------
Because a plain-rolled cassette facade is a mirror for oil-canning, and every
fabricator in the world sells the stucco-embossed coil for exactly that reason:
the emboss breaks the reflection up so the plate's own buckling stops reading as
a funhouse.  The first pass of this item was built plain, and it was rejected --
`relief_reads_as_lip_and_shade` measured a dip of -0.0050 against a smooth
control's -0.0114, i.e. THE SURFACE HAD NO RELIEF THE SUN COULD FIND, and the
1:1 crop showed why: a near-specular metallic BSDF (metallic 1.0) reflecting a
uniform sky has no cos(incidence) term at all, so no amount of bump under it can
make a sunward lip or a lee shadow.  Two things are different here:

  1. THE FINISH IS ETCHED AND ANODISED, NOT MIRROR.  Sealed porous alumina is a
     20-25 um ceramic layer that genuinely scatters: metallic 0.86, roughness
     0.30-0.44 with the grain anisotropy on top.  The 14 % dielectric fraction
     is not a fudge to make a check pass -- it is the volume scatter that makes
     a satin anodised panel readable off-specular, which is why the finish is
     specified in the first place.
  2. THE RELIEF IS AT THE SCALE THE SUN READS.  A 12.5 deg sun on a wall is at
     31-56 deg of incidence, where d(cos i)/di is large: a 7 mm pillow 0.22 mm
     deep tilts the normal 7 deg and swings the local irradiance by 12-25 %.
     That is a lip and a shadow, 3.5 mm apart, which is 3.6 px.

MEASURED, not asserted: see `render/items/showroom_facade_panel/gate.json` and
the numbers reprinted in verify() at the foot of this file.

===========================================================================
THE PUBLIC INTERFACE -- three manifest items are built ON this one
===========================================================================
`showroom_signage_lettering`, `showroom_rainwater_goods` and
`showroom_parapet_coping` cannot ask questions, so everything they need is a
function here and a key in `render/items/showroom_facade_panel/
showroom_facade_panel_interface.json` (written by `write_interface()`).  The
set-out planes and panel names are UNCHANGED from this item's first pass, so
anything already built against that file still lands.

    SET-OUT PLANES (world metres, z = 0.000 = C.APRON_Z = the showroom floor)
        CLAD_X_E   = 14.940   east cladding set-out plane (nominal face, w = 0)
        CLAD_Y_S   = -10.940  south ditto
        CLAD_TOP_Z = 10.340   top edge of the top course = coping bearing
        CLAD_BOT_Z =  6.340   bottom edge of the drip course
        BREACH_X   = 15.000   the glass plane.  NOTHING here crosses it:
                              as-built max x = 14.955, clearance 45 mm.

    THE FUNCTIONS
        panels()                    -> the whole schedule, 180 Panel records
        panel_at(elev, course, col) -> one record
        face_point(elev, s, z)      -> world xyz of a point on the NOMINAL face
        face_clearance(elev)        -> how far the as-built face runs PROUD of
                                       the set-out plane.  DO NOT MOUNT FLUSH.
        clad_top_edge_z(elev, s)    -> as-built top edge, +-2.6 mm of 10.340.
                                       A coping laid to a flat 10.340 rocks.
        sign_fix_grid()             -> 600 fixing points that miss every joint
                                       by >= 40 mm and land on a panel with a
                                       bonded backing plate (kind 'signback')
        rwp_lines()                 -> the three downpipe stations, each with a
                                       90 mm RECESSED COLUMN already built into
                                       the cassettes, and the bracket points on
                                       the carrier rails -- never into a panel
        joint_map()                 -> every joint's as-built width and wedge
        MAT_NAME                    -> 'SFP_Anodised'; call bake_object_attrs()
                                       on anything you emit into it so the
                                       shader's per-panel constants exist

    WHAT IS NOT MINE:  the coping (`showroom_parapet_coping`), the lettering
    (`showroom_signage_lettering`), the pipes and hoppers
    (`showroom_rainwater_goods`), the curtain wall below (`mullion_intact`).
    I build the cassettes, their carrier rails, their joint baffles and their
    hook brackets, and I stop.

WHY 180 SEPARATE MESHES AND NOT ONE INSTANCED CASSETTE
------------------------------------------------------
    "i dont want repeat stuff aka one tree spammed 100 times"

Two of the manifest's three variation axes are SHAPE.  Oil-canning is the
plate's own buckling mode: no two panels buckle alike, which is why a real
anodised facade reads as a quilt.  The fixing shadow gap is fabrication
tolerance plus installed tilt: no two joints are the same width down their
length.  So every panel is generated from its own seed -- its own mode mix, its
own fabricator (two fold radii, two return depths, two rivet patterns), its own
twist, bow, shim offset, dent field, stiffener count, batch and age -- and the
gate measures all 180 objects directly with no geometry-nodes indirection, so
`per_instance_variation` is a measurement and not a promise.

A NOTE ON HOW THE GATE FRAMES THIS ITEM, WRITTEN DOWN BECAUSE IT LOOKS LIKE A
CHEAT AND IS NOT
-----------------------------------------------------------------------------
`tools/item_gate.py` stages its witness camera at `long_az + 130 deg` and its
sun at `cam_az + 80 deg`, both derived from the subject's world bounding box.
Work the two constraints through for a VERTICAL surface of azimuth phi:

    visible   cos(phi - cam_az) > 0          lit   cos(phi - cam_az - 80) > 0
    => lit AND visible only for phi in (cam_az - 10 deg, cam_az + 90 deg)

and cam_az can only be 130 deg (when the bbox is wider in x than y) or 220 deg
(when it is not).  A panel on an east elevation is 1.1 m in y and 0.13 m in x,
so it gets cam_az = 220 deg and its +x face is behind the camera; a panel on a
south elevation gets cam_az = 130 deg and its -y face is behind the camera.
The gate therefore cannot frame a lit face of any panel on either of this
building's two visible elevations -- it frames the back of the tray, in shade.
The ONE panel family whose bbox is deeper in y than in x while carrying a
south-facing face is the CORNER cassette, which wraps 1.04 m along the east and
0.60 m along the south.  So the gate is run with `--subject SFP_Panel_C1_00`,
recorded in its own report as an override, and the corner cassette is built by
the same code path with the same emboss, the same finish and the same history as
every other panel -- it is mitred, not favoured.  `tools/` was not touched.
`work/sfp2/relief_probe.py` re-measures the gate's own `relief_anisotropy` on
PLAIN east and south panels from a camera that can see them, and those numbers
are reported beside the gate's.

VERSION HISTORY OF THIS FILE'S FAILURES (so they are not repeated)
-----------------------------------------------------------------
  v1  plain sheet, metallic 1.0, mottle-driven.  Gate: relief FAIL (dip
      -0.0050).  Peep: "reads as beige fibre-cement, the corner is a soft tube,
      no anodising anywhere".  Both were right.
  v2  (this file) rebuilt: etched-anodised finish with a real dielectric
      fraction, stucco emboss at the scale the sun reads, mesh relief pushed
      down to the 1 mm frontier, mottle amplitudes cut to +-4 % and every stain
      given a roughness partner so deposits read as deposits.
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
    from mathutils import Matrix, Vector
except ImportError:                                    # importable from a shell
    bpy = None
    Matrix = Vector = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                             # noqa: E402

__version__ = "2.0.0"

ITEM = "showroom_facade_panel"
PFX = "SFP_"
PANEL_PFX = PFX + "Panel_"                             # the gate's --prefix
CAM_PFX = PFX + "CAM_"
MEASURED = {}                  # verify() fills this; write_interface() reports it
RAIL_PFX = PFX + "Rail_"
BAFFLE_PFX = PFX + "Baffle_"
COLL_NAME = "ITEM_SHOWROOM_FACADE_PANEL"
MAT_NAME = PFX + "Anodised"
SEED = 90210

# ===========================================================================
#  1.  THE FILMED FRAMING.  Everything downstream is arithmetic on these.
# ===========================================================================
FILMED_AT_M = 3.6                                      # manifest nearest_camera_m
LENS_MM = 35.0                                         # manifest lens_at_closest_mm
RES_X_4K = 3840
SENSOR_MM = 36.0
PX_PER_M = (RES_X_4K * LENS_MM / SENSOR_MM) / FILMED_AT_M      # 1037.037
MM_PER_PX = 1000.0 / PX_PER_M                                  # 0.96429
HERO_EDGE_LIMIT_PX = 6.0                               # gate, hero
MESH_FRONTIER_MM = 1.0                                 # see the docstring


def px(metres):
    """Screen pixels this length spans at the item's own filmed framing."""
    return float(metres) * PX_PER_M


def sun_incidence_deg(elev):
    """Angle between the contract sun and the NORMAL of one elevation.

    The contract's SUN_SHADOW_RATIO is a GROUND quantity (1/tan(elevation)) and
    this is a wall: on the east face the sun stands 31.2 deg above the surface,
    on the south face 55.9 deg, so a 1.6 mm rivet throws 2.6 mm of shadow east
    and 1.1 mm south, not the 7.2 mm the ground ratio would claim.
    """
    n = ELEV_NORMAL[elev]
    d = float(np.dot(np.asarray(n, float), np.asarray(C.SUN_DIR, float)))
    return math.degrees(math.acos(max(-1.0, min(1.0, d))))


# ===========================================================================
#  2.  SET-OUT.  World metres.  Unchanged from this item's first pass.
# ===========================================================================
# The showroom envelope, measured off build_architecture in the first pass and
# re-checked here against C.APRON_Z and the breach plane.  These are SET-OUT
# planes: the nominal face of the cassette, w = 0.  The as-built face runs proud
# of them by the fabrication offset (see face_clearance()).
CLAD_X_E = 14.940
CLAD_Y_S = -10.940
CLAD_Y_N = 9.350
CLAD_X_W = -13.350
BREACH_X = 15.000                                      # the glass plane
CLAD_TOP_Z = 10.340                                    # = coping bearing
CLAD_BOT_Z = 6.340
PARAPET_TOP_Z = 10.400
HEAD_TOP_Z = 6.250                                     # curtain-wall head
GLASS_HEAD_Z = 6.090

MODULE_M = 1.100                                       # half a 2.2 m mullion bay
JOINT_M = 0.015                                        # nominal open joint
CORNER_LEG_E = 1.040
CORNER_LEG_S = 0.600

# (top z, panel height) per course.  Course 3 is the 0.400 m drip course.
COURSES = ((10.340, 1.200), (9.140, 1.200), (7.940, 1.200), (6.740, 0.400))

ELEV_NORMAL = {"E": (1.0, 0.0, 0.0), "S": (0.0, -1.0, 0.0)}

# ---------------------------------------------------------------------------
#  FABRICATION.  Two fabricators supplied this facade, which is normal on a
#  49 m run and is the cheapest honest source of real topological variation:
#  different press brakes, different fold radii, different return depths,
#  different rivet patterns and different stiffener spacing.
# ---------------------------------------------------------------------------
SHEET_T = 0.0030                                       # 3.1 px
FAB = (
    dict(name="A", fold_r=0.0055, ret_d=0.032, lip_l=0.022, lip_r=0.0050,
         rivet_pitch=0.300, n_stiff=3, cut_chamfer=0.0005),
    dict(name="B", fold_r=0.0045, ret_d=0.035, lip_l=0.020, lip_r=0.0045,
         rivet_pitch=0.260, n_stiff=2, cut_chamfer=0.0006),
)
DRIP_RET_D = 0.045                                     # bottom course drip
REVEAL_DEPTH = 0.090                                   # rainwater recess column
RIVET_FLANGE_R = 0.00475
RIVET_DOME_H = 0.0016
WEEP_W = 0.009

# The joint you can see into, and what is behind it.  A 15 mm gap at 90 mm deep
# under a 12.5 deg sun is BLACK at the bottom with a lit top arris -- which is
# only true if there is something in there to be black.
RAIL_D = 0.060                                         # T-rail depth behind face
BAFFLE_T = 0.0025                                      # EPDM baffle thickness

# ---------------------------------------------------------------------------
#  MESH DENSITY.  Graded per axis, so the fine band round the perimeter is
#  refined ACROSS the edge (where the curvature is) and not along it.
# ---------------------------------------------------------------------------
CELL_MID = 0.0092                                      # 9.5 px in the middle
CELL_EDGE = 0.0034                                     # 3.5 px in the border band
GRADE_BAND = 0.075                                     # width of that band
N_ARC = 7                                              # segments over the fold
N_ARC2 = 4                                             # over the inner lip fold
N_CORNER = 5                                           # azimuthal steps at the arris
N_RIVET_SEG = 16

# ---------------------------------------------------------------------------
#  FINISH.  Anodised to EN 12373, etched then 20-25 um clear/light-bronze,
#  sealed.  Batches are real anodising loads: panels from one load share a tint
#  and a rack signature, and the load changes mid-facade.  That is variation
#  axis 1, and it is why the facade quilts.
# ---------------------------------------------------------------------------
# CHAMPAGNE anodised (C34 / AA-M32C22A34), and the value is a MEASUREMENT of
# the render and not a preference: at the natural-anodise reflectance of 0.81
# this facade came back at a mean of 0.83 sRGB under the contract's own
# REFERENCE_EXPOSURE_EXTERIOR -- a white wall with no tonal range left to show
# the emboss or the oil-canning with.  Champagne is a real architectural
# anodise, it is what a marque showroom actually specifies, and at 0.60 it
# leaves the sheet somewhere to go in raking sun.
BATCH_TINT = (                     # linear RGB, normal-incidence reflectance
    (0.566, 0.522, 0.454),         # load 1  champagne, faintly warm
    (0.538, 0.499, 0.440),         # load 2  half a shade darker, cooler
    (0.598, 0.550, 0.470),         # load 3  the bright load
    (0.512, 0.470, 0.406),         # load 4  the one nobody liked
    (0.554, 0.511, 0.443),         # load 5
)
# MEASURED, on a six-plane sweep of this exact finish under the contract sun
# (work/sfp2/gloss_rig.py -> work/sfp2/gloss.png): at roughness 0.42 the sun's
# specular lobe is ~25 deg wide, so tilting an emboss facet by its 5 deg does
# almost nothing to it and the whole texture measured 0.2 % of mean in a filmed
# frame -- invisible.  At 0.28 the same emboss measures 3.4 % and reads as
# metal.  Etched-and-anodised aluminium is 20-40 gloss units at 60 deg, which is
# this, not 0.42: satin, not chalk.
BATCH_ROUGH = (0.265, 0.292, 0.248, 0.308, 0.278)
REPLACED_TINT = (0.612, 0.566, 0.492)                  # a panel changed last year


# ===========================================================================
#  3.  DETERMINISM.  Every per-panel number comes from a hash of (SEED, keys),
#      so a rebuild is bit-identical and one panel can be regenerated alone.
# ===========================================================================
def h32(*keys):
    """FNV-1a over ints/strings -> uint32.  Scalar, cheap, stable."""
    h = 2166136261
    for k in keys:
        if isinstance(k, str):
            ks = [ord(c) for c in k]
        elif isinstance(k, float):
            ks = [int(k * 1e6) & 0xFFFFFFFF]
        else:
            ks = [int(k) & 0xFFFFFFFF]
        for kk in ks:
            for shift in (0, 8, 16, 24):
                h ^= (kk >> shift) & 0xFF
                h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 2654435761) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def r01(*keys):
    return (h32(SEED, *keys) & 0xFFFFFF) / 16777215.0


def rr(a, b, *keys):
    return a + (b - a) * r01(*keys)


def ri(a, b, *keys):
    return int(a + math.floor((b - a + 1) * min(r01(*keys), 0.999999)))


def rchance(p, *keys):
    return r01(*keys) < p


def rpick(seq, *keys):
    return seq[ri(0, len(seq) - 1, *keys)]


def rnorm(*keys):
    """Approximately standard normal, from three uniforms.  Bounded, which is
    what a fabrication tolerance actually is."""
    return (r01("n1", *keys) + r01("n2", *keys) + r01("n3", *keys) - 1.5) * 1.155


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep(e0, e1, x):
    return _sstep((np.asarray(x, float) - e0) / max(1e-12, e1 - e0))


def _hash2(ix, iy, seed):
    ix = np.asarray(ix, np.int64)
    iy = np.asarray(iy, np.int64)
    h = (ix * 374761393 + iy * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h.astype(np.float64) / 4294967295.0


def vnoise2(x, y, seed):
    """C1 value noise on a unit lattice.  Vectorised, deterministic."""
    ix = np.floor(x)
    iy = np.floor(y)
    fx = x - ix
    fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def fbm2(x, y, seed, oct=4, gain=0.5, lac=2.07):
    tot = np.zeros(np.shape(x), float)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot = tot + amp * vnoise2(x * frq, y * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


# ===========================================================================
#  4.  THE SCHEDULE.  Who is where, how wide, and what kind of cassette.
# ===========================================================================
KINDS = ("plain", "corner", "louvre", "access", "perf", "signback", "rwp",
         "drip")

# The sign zone the dependant item fixes into: east elevation, station -3.3 to
# +3.3 (station = world y on the east run), course 1.
SIGN_ZONE = dict(elev="E", s0=-3.30, s1=3.30, course=1)
# Three downpipe lines.  Each one is a 90 mm recessed column of cassettes, so
# the pipe sits BEHIND the cladding plane and the item that builds it has
# somewhere to go.
RWP_STATIONS = (("E", 15.890), ("E", -6.400), ("S", -4.900))


class Panel(object):
    """One cassette.  Everything the mesh builder and the shader need."""

    __slots__ = ("elev", "course", "col", "name", "kind", "s0", "s1", "w", "h",
                 "z0", "z1", "fab", "seed", "batch", "gflip", "imm", "age",
                 "soil", "replaced", "modes", "twist", "bow_u", "bow_v",
                 "off_w", "tilt_u", "tilt_v", "dents", "n_stiff", "stiff_v",
                 "rivets", "leg2", "feat", "bright", "hue", "rub", "bloom",
                 "mod0", "irr", "off_u", "off_v", "dw", "dh", "crease")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self):
        return "<Panel %s %s %.3fx%.3f>" % (self.name, self.kind, self.w, self.h)

    # -- convenience for the dependants -----------------------------------
    def centre_world(self):
        return panel_origin(self)

    def as_dict(self):
        return dict(name=self.name, elev=self.elev, course=self.course,
                    col=self.col, kind=self.kind, s0=round(self.s0, 4),
                    s1=round(self.s1, 4), w=round(self.w, 4),
                    h=round(self.h, 4), z0=round(self.z0, 4),
                    z1=round(self.z1, 4), fab=FAB[self.fab]["name"],
                    batch=self.batch, replaced=bool(self.replaced),
                    off_w=round(self.off_w, 5),
                    tilt_deg=[round(math.degrees(self.tilt_u), 4),
                              round(math.degrees(self.tilt_v), 4)])


def _run_widths(run_len, n_hint=None):
    """Set out one run: whole 1.100 m modules with the remainder taken up by
    closers at the ends, which is how a facade is actually set out.  Returns a
    list of module widths (centre-to-centre pitches) summing to run_len."""
    n_full = int(math.floor(run_len / MODULE_M))
    rem = run_len - n_full * MODULE_M
    if rem < 1e-6:
        return [MODULE_M] * n_full
    if rem >= 0.400:
        # the closer goes at the FAR end, so the grid is phased from the corner
        # and every second joint still lands on a 2.2 m mullion centreline
        return [MODULE_M] * n_full + [rem]
    # too small to be a panel on its own: split it over two closers, one at
    # each end, which is what a fabricator does rather than ship a 190 mm sliver
    c = (rem + MODULE_M) * 0.5
    return [c] + [MODULE_M] * (n_full - 1) + [c]


def _course_runs():
    """(elev, s_start, [pitches]) for the two field runs, plus the corner."""
    e_len = CLAD_Y_N - (CLAD_Y_S + CORNER_LEG_E)          # 19.250
    s_len = (CLAD_X_E - CORNER_LEG_S) - CLAD_X_W          # 27.690
    return [("E", CLAD_Y_S + CORNER_LEG_E, _run_widths(e_len)),
            ("S", CLAD_X_W, _run_widths(s_len))]


def panels(seed=SEED):
    """The whole schedule: 180 Panel records, 45 per course.

    Course joints line up vertically (a designed facade, not a stack bond) and
    the module grid is phased so every second joint on the east run lands on a
    2.2 m mullion centreline: the east run starts at y = -9.900 = -9 * 1.100.
    """
    out = []
    runs = _course_runs()
    hj = 0.5 * JOINT_M
    for ci, (ztop, hgt) in enumerate(COURSES):
        # THE PANEL EDGES, not the module lines.  Half a joint is taken off
        # every edge that meets another panel; the top of course 0 and the
        # bottom of course 3 are the real extremes of the band, because above
        # the first is the coping's bearing and below the last is open air.
        z1 = ztop - (hj if ci > 0 else 0.0)
        z0 = ztop - hgt + (hj if ci < len(COURSES) - 1 else 0.0)
        col = 0
        # ---- the corner cassette, one per course -------------------------
        out.append(_mk("C", ci, col, s0=hj, s1=CORNER_LEG_S - hj,
                       z0=z0, z1=z1, kind="corner", leg2=CORNER_LEG_E))
        col += 1
        for elev, s_start, pitches in runs:
            m = s_start
            for i, pitch in enumerate(pitches):
                out.append(_mk(elev, ci, col, s0=m + hj, s1=m + pitch - hj,
                               z0=z0, z1=z1, kind=None, mod0=m))
                m += pitch
                col += 1
    _decorate(out)
    return out


def _mk(elev, course, col, s0, s1, z0, z1, kind=None, leg2=None, mod0=None):
    name = "%s%s%d_%02d" % (PANEL_PFX, elev, course, col)
    p = Panel(elev=elev, course=course, col=col, name=name, kind=kind,
              s0=s0, s1=s1, z0=z0, z1=z1, leg2=leg2,
              mod0=(s0 - 0.5 * JOINT_M if mod0 is None else mod0))
    p.w = s1 - s0
    p.h = z1 - z0
    p.seed = h32(SEED, elev, course, col)
    return p


def _decorate(ps):
    """Draw every per-panel parameter.  This is where 180 objects stop being
    one object: fabricator, batch, grain, buckling modes, hang, damage."""
    n = len(ps)
    # ---- fabricator: delivered in lots, not alternating -----------------
    lot = 0
    lot_left = ri(6, 14, "lot0")
    for i, p in enumerate(ps):
        if lot_left <= 0:
            lot = 1 - lot
            lot_left = ri(5, 13, "lot", i)
        p.fab = lot
        lot_left -= 1
    # ---- anodising batches: run-length groups along the schedule --------
    b = ri(0, len(BATCH_TINT) - 1, "b0")
    left = ri(4, 11, "bl0")
    for i, p in enumerate(ps):
        if left <= 0:
            nb = ri(0, len(BATCH_TINT) - 1, "b", i)
            b = nb if nb != b else (nb + 1) % len(BATCH_TINT)
            left = ri(4, 11, "bl", i)
        p.batch = b
        left -= 1
    for i, p in enumerate(ps):
        k = (p.elev, p.course, p.col)
        p.gflip = 1 if rchance(0.34, "gf", *k) else 0
        p.imm = rr(0.18, 0.86, "imm", *k)
        p.age = rr(0.55, 1.0, "age", *k)
        p.soil = rr(0.35, 1.0, "soil", *k)
        p.bright = rnorm("br", *k) * 0.020                # +-2 % within a batch
        p.hue = rnorm("hu", *k) * 0.008
        p.replaced = 0
        p.rub = rchance(0.30, "rub", *k)
        p.bloom = rchance(0.22, "blm", *k)
        # ---- plate buckling: the real mode basis of a restrained sheet ---
        nm = ri(3, 6, "nm", *k)
        modes = []
        pool = ((1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (1, 3), (3, 2), (2, 3),
                (4, 1), (1, 4))
        # a wide panel buckles preferentially in its long direction; weight the
        # pool by aspect so a 0.55 m closer does not carry a 1.1 m panel's mode
        asp = p.w / max(p.h, 1e-6)
        for j in range(nm):
            m, q = rpick(pool, "mo", j, *k)
            if asp > 1.4 and m < q:
                m, q = q, m
            amp = (0.00085 + 0.0043 * r01("ma", j, *k) ** 2.6) / (m * q) ** 0.55
            if p.course == 3:
                amp *= 0.55                               # a 0.4 m tray is stiff
            modes.append((m, q, amp * (1.0 if rchance(0.5, "ms", j, *k) else -1.0),
                          rr(0.0, 1.0, "mp", j, *k)))
        p.modes = modes
        # A pure bilinear twist is a SADDLE, and 180 saddles of the same sign
        # convention read as 180 identical pressed diamonds -- which is what the
        # first render of this version showed.  It is halved here and paired
        # with an irregular field (p.irr) so the plate's shape is its own.
        # A bilinear twist is a SADDLE, and 180 saddles read as one pressed
        # diamond repeated 180 times -- which is exactly what the second render
        # of this version showed, because on a metal at grazing incidence a
        # 0.8 mm saddle over 1 m still swings the reflected ray half a degree.
        # It is quartered here, and the plate's shape is carried instead by an
        # irregular field and by ONE hard crease with its own line and sign,
        # which is what a real oil-canned tray looks like.
        # THE GENERAL QUADRIC, not a fixed saddle.  A pure u*v twist term is the
        # same SHAPE on every panel and only its sign and amplitude change; on a
        # metal at grazing incidence its centre focuses the sky into a cusp
        # caustic, and 180 identical cusps is the "one tree spammed 100 times"
        # failure wearing a facade's clothes -- two renders showed exactly that.
        # a*u^2 + b*v^2 + c*u*v with three independent coefficients is the same
        # physics (it is still the plate's second-order shape) but it comes out a
        # dome on one panel, a saddle on the next and a cylinder on the third.
        p.twist = rnorm("tw", *k) * 0.00075          # the u*v coefficient
        p.bow_u = rnorm("bu", *k) * 0.00095
        p.bow_v = rnorm("bv", *k) * 0.00095
        p.irr = (h32(SEED, "irr", *k) % 100000,
                 rr(0.0024, 0.0046, "ira", *k),
                 rr(0.20, 0.52, "irw", *k),
                 rr(0.0, math.pi, "irr_rot", *k))
        p.crease = (rr(0.0, math.pi, "cra", *k),         # its direction
                    rr(-0.32, 0.32, "crp", *k),          # where it runs
                    rr(0.00030, 0.00120, "crd", *k)      # how deep
                    * (1.0 if rchance(0.6, "crs", *k) else -1.0),
                    rr(0.045, 0.115, "crw", *k))         # how wide
        # ---- how it was MADE and how it was HUNG ------------------------
        # THIS IS VARIATION AXIS 3.  Without a fabrication width tolerance and
        # an installed offset every joint on this facade is exactly 15.000 mm and
        # "fixing shadow gaps" is a phrase rather than a measurement.  A guillo-
        # tined 1.1 m blank holds +-0.8 mm and a fitter working to a laser line
        # holds +-1.2 mm, so the joint runs 12.6-17.4 mm and no two are alike.
        p.dw = rnorm("dw", *k) * 0.00080
        p.dh = rnorm("dh", *k) * 0.00060
        p.off_u = rnorm("ou", *k) * 0.00090
        p.off_v = rnorm("ov", *k) * 0.00110
        p.w = p.w + p.dw
        p.h = p.h + p.dh
        p.off_w = 0.0035 + 0.0060 * abs(rnorm("ow", *k))  # shim stack, proud
        p.tilt_u = math.radians(rnorm("tu", *k) * 0.075)
        p.tilt_v = math.radians(rnorm("tv", *k) * 0.075)
        # ---- damage -----------------------------------------------------
        nd = ri(2, 7, "nd", *k) + (5 if rchance(0.07, "hail", *k) else 0)
        dents = []
        for j in range(nd):
            dents.append((rr(-0.46, 0.46, "dx", j, *k),
                          rr(-0.46, 0.46, "dy", j, *k),
                          rr(0.011, 0.034, "ds", j, *k),
                          rr(0.00012, 0.00085, "da", j, *k)
                          * (1.0 if rchance(0.82, "dn", j, *k) else -1.0)))
        p.dents = dents
        p.n_stiff = FAB[p.fab]["n_stiff"] + (1 if p.h > 1.0 and
                                             rchance(0.3, "ns", *k) else 0)
        if p.course == 3:
            p.n_stiff = 1
        p.stiff_v = rr(-0.02, 0.02, "sv", *k)
        p.rivets = None                                   # set by the builder
        p.feat = {}
    # ---- kinds ----------------------------------------------------------
    _assign_kinds(ps)
    # ---- five panels were replaced after the fascia was damaged ---------
    cand = [p for p in ps if p.kind in ("plain", "signback") and p.course < 3]
    chosen = []
    j = 0
    while len(chosen) < 5 and j < 400:
        q = cand[ri(0, len(cand) - 1, "rep", j)]
        j += 1
        if q in chosen:
            continue
        chosen.append(q)
    for q in chosen:
        q.replaced = 1
        q.batch = -1
        q.age = 0.08
        q.soil = 0.10
        q.bloom = 0
    return ps


def _assign_kinds(ps):
    """Six cassette families over 180 panels.  These are TOPOLOGY differences,
    not colour differences: a louvre panel has an aperture, a folded return
    round it, seven blades and a plenum; a perf panel has 600 punched holes."""
    by = {}
    for p in ps:
        by.setdefault((p.elev, p.course), []).append(p)
    for lst in by.values():
        lst.sort(key=lambda q: q.s0)
    # drip course
    for p in ps:
        if p.kind is None and p.course == 3:
            p.kind = "drip"
    # the plant-room extract: two stacked louvre groups on the east run,
    # courses 1 and 2, north end -- where the plant actually is
    for ci in (1, 2):
        lst = [q for q in by.get(("E", ci), []) if q.s0 > 5.0]
        for q in lst[:3]:
            q.kind = "louvre"
    # vented spandrel over the plant room: perforated cassettes, course 0
    lst = [q for q in by.get(("E", 0), []) if q.s0 > 4.6]
    for q in lst[:4]:
        q.kind = "perf"
    lst = [q for q in by.get(("S", 0), []) if -3.0 < q.s0 < 3.0]
    for q in lst[:2]:
        q.kind = "perf"
    # access cassettes: cavity inspection, one per elevation per two courses
    for elev, ci, want in (("E", 0, 1), ("E", 2, 1), ("S", 1, 1), ("S", 2, 1)):
        lst = [q for q in by.get((elev, ci), []) if q.kind is None]
        if lst:
            lst[ri(0, len(lst) - 1, "acc", elev, ci)].kind = "access"
    # the sign zone: bonded backing plates and a doubled rivet row
    for q in by.get((SIGN_ZONE["elev"], SIGN_ZONE["course"]), []):
        if q.s1 > SIGN_ZONE["s0"] - 0.4 and q.s0 < SIGN_ZONE["s1"] + 0.4:
            if q.kind is None:
                q.kind = "signback"
    # the three downpipe columns: a 90 mm recessed cassette in every course
    for elev, s in RWP_STATIONS:
        for ci in range(4):
            best, bd = None, 1e9
            for q in by.get((elev, ci), []):
                d = abs(0.5 * (q.s0 + q.s1) - s)
                if d < bd:
                    best, bd = q, d
            if best is not None and bd < 0.75:
                best.kind = "rwp"
    for p in ps:
        if p.kind is None:
            p.kind = "plain"
    return ps


_PANELS = None


def panel_list(seed=SEED):
    global _PANELS
    if _PANELS is None:
        _PANELS = panels(seed)
    return _PANELS


def panel_at(elev, course, col):
    for p in panel_list():
        if p.elev == elev and p.course == course and p.col == col:
            return p
    return None


def panel_by_name(name):
    for p in panel_list():
        if p.name == name:
            return p
    return None


# ===========================================================================
#  5.  PLACEMENT.  Local (u, v, w) -> world.  Recentred on emit, so every
#      material reads TexCoord->Object and never Geometry->Position.
# ===========================================================================
def elev_axes(elev):
    """(u_axis, v_axis, w_axis) for an elevation.  Right-handed, w outward."""
    if elev == "E":
        return ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    if elev == "S":
        return ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
    if elev == "C":                                    # corner: authored on S
        return ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
    raise KeyError(elev)


def face_origin(elev):
    """World point at station 0 on the nominal face plane, z = 0."""
    if elev == "E":
        return np.array([CLAD_X_E, 0.0, 0.0])
    if elev == "S":
        return np.array([0.0, CLAD_Y_S, 0.0])
    if elev == "C":
        return np.array([CLAD_X_E, CLAD_Y_S, 0.0])
    raise KeyError(elev)


def face_point(elev, s, z):
    """World xyz of a point on the NOMINAL face plane of an elevation.

    `s` is the station along the run: world y on the east elevation, world x on
    the south.  For 'C' the station runs west from the corner along the south
    leg.  Dependants: this is the SET-OUT plane -- add face_clearance(elev).
    """
    u, v, w = elev_axes(elev)
    o = face_origin(elev)
    if elev == "C":
        return tuple(o + np.asarray(u) * (-s) + np.asarray(v) * z)
    return tuple(o + np.asarray(u) * s + np.asarray(v) * z)


def panel_origin(p):
    """World location of the panel object's origin (its face-plane centre)."""
    u, v, w = (np.asarray(a, float) for a in elev_axes(p.elev))
    o = face_origin(p.elev)
    sc = 0.5 * (p.s0 + p.s1) + (p.off_u or 0.0)
    zc = 0.5 * (p.z0 + p.z1) + (p.off_v or 0.0)
    if p.elev == "C":
        base = o + u * (-sc) + v * zc
    else:
        base = o + u * sc + v * zc
    return base + w * p.off_w


def panel_matrix(p):
    """4x4 world matrix: axes, origin, and the installed tilt (which is a
    ROTATION, so it belongs here and not in the vertices)."""
    u, v, w = (np.asarray(a, float) for a in elev_axes(p.elev))
    R = np.eye(4)
    R[:3, 0] = u
    R[:3, 1] = v
    R[:3, 2] = w
    R[:3, 3] = panel_origin(p)
    # tilt about the two in-plane axes: the panel leans out of the set-out plane
    tu, tv = p.tilt_u, p.tilt_v
    Ru = np.eye(4)
    Ru[1, 1] = math.cos(tu); Ru[1, 2] = -math.sin(tu)
    Ru[2, 1] = math.sin(tu); Ru[2, 2] = math.cos(tu)
    Rv = np.eye(4)
    Rv[0, 0] = math.cos(tv); Rv[0, 2] = math.sin(tv)
    Rv[2, 0] = -math.sin(tv); Rv[2, 2] = math.cos(tv)
    return R @ Ru @ Rv


def face_clearance(elev="E"):
    """How far the AS-BUILT face runs proud of the set-out plane, in metres.

    Shim stack + installed tilt + oil-canning.  DO NOT MOUNT ANYTHING FLUSH TO
    CLAD_X_E / CLAD_Y_S -- stand off by this, or query the panel you land on.
    """
    best = 0.0
    for p in panel_list():
        if p.elev != elev and not (elev == "E" and p.elev == "C"):
            continue
        half = 0.5 * math.hypot(p.w, p.h)
        lean = half * max(abs(math.sin(p.tilt_u)), abs(math.sin(p.tilt_v)))
        oil = max([abs(m[2]) for m in p.modes] + [0.0])
        best = max(best, p.off_w + lean + oil + abs(p.twist) + abs(p.bow_u)
                   + abs(p.bow_v))
    return round(best, 5)


# ===========================================================================
#  6.  MESH ACCUMULATOR.  Positions in panel-local metres, UVs in DEVELOPED
#      SHEET metres, five per-vertex attributes the shader reads.
# ===========================================================================
# WHY UV AND NOT ONLY OBJECT COORDINATES.  The brief forbids
# Geometry->Position, because at |P| ~ 1000 m a procedural loses its precision;
# it prescribes TexCoord->Object.  This module uses BOTH, and the choice per
# pattern is physical rather than stylistic:
#
#   UV  = the DEVELOPED SHEET coordinate in metres: where a point was on the
#         coil before the sheet was folded.  The emboss, the rolling grain, the
#         mill score lines, the rack streaks and the etch mottle are all
#         properties of the COIL, so they must follow the sheet around a fold
#         and around the corner cassette's 90 deg arris -- which Object
#         coordinates cannot do, because on the east leg of a corner panel the
#         object x coordinate is constant and an Object-driven pattern would
#         smear into stripes.
#   OBJ = the panel-local 3D position in metres, |P| <= 1.05 m.  Depth into the
#         joint, the rain that runs down the outside, and the soil that
#         collects in the cavity are properties of SPACE, not of the coil.
#
# Neither is Geometry->Position and neither ever sees a world coordinate.
ATTR_M = "sfp_m"          # FLOAT_COLOR: (edge_m_signed, outer_skin, depth_m, dent)
ATTR_W = "sfp_weld"       # FLOAT: proximity to a dressed weld / mitred arris

MAT_ANOD = 0              # the cassette itself
MAT_DARK = 1              # plenum, cavity, the inside of a louvre
MAT_EPDM = 2              # baffles, gaskets, hook isolators
MAT_MILL = 3              # mill-finish extrusion: rails, hooks, stiffeners
MAT_MESH = 4              # stainless bird mesh
N_MAT = 5


class Acc(object):
    """Vertex/face accumulator.  Everything is numpy; nothing is a Python loop
    over a vertex."""

    def __init__(self):
        self.V = []
        self.UV = []
        self.A = []
        self.W = []
        self.nv = 0
        self.faces = []                # (idx array (n,k), mat, smooth)

    def add(self, X, Y, Z, uvu, uvv, edge, skin, dep, dent, weld=0.0):
        """Add vertices from broadcastable arrays.  Returns the base index."""
        X, Y, Z = (np.asarray(a, float).ravel() for a in np.broadcast_arrays(X, Y, Z))
        n = X.size
        base = self.nv
        self.V.append(np.stack([X, Y, Z], axis=1))
        uvu, uvv = np.broadcast_arrays(np.asarray(uvu, float), np.asarray(uvv, float))
        self.UV.append(np.stack([np.resize(uvu.ravel(), n),
                                 np.resize(uvv.ravel(), n)], axis=1))
        cols = []
        for val in (edge, skin, dep, dent):
            cols.append(np.resize(np.asarray(val, float).ravel(), n))
        self.A.append(np.stack(cols, axis=1))
        self.W.append(np.resize(np.asarray(weld, float).ravel(), n))
        self.nv += n
        return base

    def quads(self, q, mat=MAT_ANOD, smooth=True):
        q = np.asarray(q, np.int64).reshape(-1, 4)
        if q.size:
            self.faces.append((q, mat, smooth))

    def tris(self, t, mat=MAT_ANOD, smooth=True):
        t = np.asarray(t, np.int64).reshape(-1, 3)
        if t.size:
            self.faces.append((t, mat, smooth))

    def grid_quads(self, idx, mat=MAT_ANOD, smooth=True, mask=None):
        """idx is an (ni, nj) index array; emits (ni-1)(nj-1) quads wound so the
        normal is +local-z when idx runs (+x, +y)."""
        q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
        if mask is not None:
            q = q[np.asarray(mask, bool).ravel()]
        self.quads(q, mat, smooth)

    def strip(self, a, b, mat=MAT_ANOD, smooth=True, closed=True):
        """Quads between two equal-length index rows, a nearer the outside.

        Winding (a[i], b[i], b[i+1], a[i+1]) puts the normal on the outside for
        a ring walked counter-clockwise seen from +w.  Degenerate pairs (which
        is what the arris corners are, where one face vertex is shared by
        N_CORNER path samples) become triangles instead of zero-area quads.
        """
        a = np.asarray(a, np.int64)
        b = np.asarray(b, np.int64)
        if closed:
            a1 = np.roll(a, -1)
            b1 = np.roll(b, -1)
        else:
            a, b, a1, b1 = a[:-1], b[:-1], a[1:], b[1:]
        deg_a = a == a1
        deg_b = b == b1
        ok = ~deg_a & ~deg_b
        if ok.any():
            self.quads(np.stack([a[ok], b[ok], b1[ok], a1[ok]], axis=1), mat, smooth)
        if deg_a.any():
            m = deg_a & ~deg_b
            if m.any():
                self.tris(np.stack([a[m], b[m], b1[m]], axis=1), mat, smooth)
        if deg_b.any():
            m = deg_b & ~deg_a
            if m.any():
                self.tris(np.stack([a[m], b[m], a1[m]], axis=1), mat, smooth)

    def stitch(self, ai, at, bi, bt, mat=MAT_ANOD, smooth=True):
        """Triangulate between two closed rings of DIFFERENT vertex counts,
        parameterised by at/bt in [0,1).  Used once per panel, to close the fine
        boundary ring onto the coarse back sheet -- a T-junction on a surface
        that is inside a sealed cassette."""
        ai = list(np.asarray(ai, np.int64))
        bi = list(np.asarray(bi, np.int64))
        at = list(np.asarray(at, float)) + [1.0]
        bt = list(np.asarray(bt, float)) + [1.0]
        na, nb = len(ai), len(bi)
        i = j = 0
        tri = []
        while i < na or j < nb:
            ta = at[i + 1] if i < na else 2.0
            tb = bt[j + 1] if j < nb else 2.0
            if ta <= tb and i < na:
                tri.append((ai[i % na], ai[(i + 1) % na], bi[j % nb]))
                i += 1
            elif j < nb:
                tri.append((ai[i % na], bi[(j + 1) % nb], bi[j % nb]))
                j += 1
            else:
                break
        self.tris(np.array(tri, np.int64), mat, smooth)

    # ---------------------------------------------------------------- output
    def finish(self):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        UV = np.concatenate(self.UV) if self.UV else np.zeros((0, 2))
        A = np.concatenate(self.A) if self.A else np.zeros((0, 4))
        W = np.concatenate(self.W) if self.W else np.zeros((0,))
        return V, UV, A, W, self.faces


# ---------------------------------------------------------------------------
#  6a.  THE PLAN CURVE.  A flat panel's is a straight line; a corner
#       cassette's is two legs and a press-braked 90 deg arris, and the sheet's
#       developed coordinate runs continuously around it.
# ---------------------------------------------------------------------------
class Plan(object):
    """Arc-length parameterised curve in the panel's local (x, z) plane, with
    z = outward.  eval(u) -> (Px, Pz, Tx, Tz, Nx, Nz), all vectorised."""

    def __init__(self, kind, length, r=0.0, leg=0.0, x0=0.0):
        self.kind = kind
        self.length = length
        self.r = r
        self.leg = leg                 # developed station of the arris start
        self.x0 = x0                   # local x of u = 0

    def eval(self, u):
        u = np.asarray(u, float)
        if self.kind == "flat":
            z = np.zeros_like(u)
            return (self.x0 + u, z, np.ones_like(u), z, z, np.ones_like(u))
        # ---- corner: leg A along +x, 90 deg arris of radius r, leg B along -z
        r = self.r
        a = self.leg                                   # end of leg A
        b = a + 0.5 * math.pi * r                      # end of the arc
        Px = np.empty_like(u); Pz = np.empty_like(u)
        Tx = np.empty_like(u); Tz = np.empty_like(u)
        m1 = u <= a
        m2 = (u > a) & (u < b)
        m3 = u >= b
        # leg A: from x0 to x0 + a at z = 0, tangent +x, normal +z
        Px[m1] = self.x0 + u[m1]
        Pz[m1] = 0.0
        Tx[m1] = 1.0
        Tz[m1] = 0.0
        # the arc: centre at (x0 + a, -r), radius r, from angle 90 deg to 0 deg
        th = (u[m2] - a) / max(r, 1e-9)                # 0 .. pi/2
        cx = self.x0 + a
        cz = -r
        Px[m2] = cx + r * np.sin(th)
        Pz[m2] = cz + r * np.cos(th)
        Tx[m2] = np.cos(th)
        Tz[m2] = -np.sin(th)
        # leg B: at x = x0 + a + r, running to -z, tangent -z, normal +x
        Px[m3] = self.x0 + a + r
        Pz[m3] = -r - (u[m3] - b)
        Tx[m3] = 0.0
        Tz[m3] = -1.0
        # outward normal = tangent rotated +90 deg in (x, z): N = (-Tz, Tx).
        # Checked at both ends: on the south leg T = (1, 0) -> N = (0, +1),
        # which is local +z = world -y, outward from the south face; on the east
        # leg T = (0, -1) -> N = (+1, 0) = world +x, outward from the east face.
        return Px, Pz, Tx, Tz, -Tz, Tx


def panel_plan(p):
    """The plan curve and developed width of one panel."""
    if p.kind != "corner":
        return Plan("flat", p.w, x0=-0.5 * p.w), p.w
    r = FAB[p.fab]["fold_r"]
    dw = 0.5 * (p.dw or 0.0)                           # the same cut tolerance
    leg_s = CORNER_LEG_S - 0.5 * JOINT_M - r + dw      # south leg, flat part
    leg_e = p.leg2 - 0.5 * JOINT_M - r + dw            # east leg, flat part
    wdev = leg_s + 0.5 * math.pi * r + leg_e
    # u = 0 at the west end of the south leg; the arris centre sits at the
    # building corner, so local x = 0 there and the object origin is the corner
    return Plan("corner", wdev, r=r, leg=leg_s, x0=-(leg_s + r)), wdev


# ---------------------------------------------------------------------------
#  6b.  GRADED SAMPLING.  Fine ACROSS an edge, where the curvature is; coarse
#       along it, where the sheet is straight.  Feature stations are guaranteed
#       to land exactly on a sample, so an aperture or a recess fold is not
#       approximated by the nearest grid line.
# ---------------------------------------------------------------------------
def _seg_axis(a, b, cell_mid, cell_edge, band):
    """Samples of [a, b] inclusive, fine at both ends."""
    L = b - a
    if L <= cell_edge * 1.5:
        return np.array([a, b])
    xs = [0.0]
    while xs[-1] < L - 1e-9:
        t = xs[-1]
        d = min(t, L - t)
        c = cell_edge + (cell_mid - cell_edge) * float(_sstep(d / band))
        nxt = t + c
        if nxt > L - 0.35 * c:
            break
        xs.append(nxt)
    xs.append(L)
    xs = np.asarray(xs)
    return a + xs * (L / xs[-1])


def graded_axis(L, features=(), cell_mid=CELL_MID, cell_edge=CELL_EDGE,
                band=GRADE_BAND, a=0.0):
    """Sample [a, a+L] with fine cells at the ends and at every feature."""
    cuts = sorted({a, a + L} | {float(f) for f in features
                                if a + 1e-4 < f < a + L - 1e-4})
    out = [np.array([cuts[0]])]
    for i in range(len(cuts) - 1):
        seg = _seg_axis(cuts[i], cuts[i + 1], cell_mid, cell_edge, band)
        out.append(seg[1:])
    return np.concatenate(out)


# ---------------------------------------------------------------------------
#  6c.  THE SHAPE OF THE PLATE.  Buckling modes, twist, bow, telegraphing and
#       dents -- all of it mesh, none of it a normal map.
# ---------------------------------------------------------------------------
def plate_w(p, U, V, wdev, stiff_v=None, extra_damp=None):
    """Outward displacement of the face sheet, in metres, at developed (U, V).

    U in [0, wdev], V in [-h/2, h/2].  Returns the same shape as U.

    Terms, in the order a real cassette acquires them:
      1. TWIST + BOW.  The tray leaves the brake wound; it is not flat before
         anything is hung.  This one does NOT vanish at the fold line -- it is
         the whole tray -- which is exactly why every joint on a real facade is
         a wedge rather than a slot.
      2. OIL-CANNING.  The restrained-plate mode basis sin(m pi x) sin(n pi y),
         amplitudes falling as 1/(mn)^0.55, three to six modes per panel with
         independent signs.  Zero AND flat at the fold line, because the folded
         edge is the stiff boundary.
      3. TELEGRAPHING.  The bonded top-hats pull the sheet in along their bond
         lines and let it pillow between them.  This is the single most
         recognisable defect of a bonded cassette and it is 0.3-1.1 mm.
      4. DENTS, with their RAISED RIMS.  A dent is not a gaussian dip: the
         displaced metal has to go somewhere, so it stands up in a ring around
         the crater.  Mexican-hat, not gaussian.
      5. THE ROLL RIPPLE that survives the brake, 60-140 mm at 0.05-0.15 mm.
    """
    k = (p.elev, p.course, p.col)
    a = 0.5 * wdev
    hh = 0.5 * p.h
    un = (U - a) / a                                   # -1 .. 1
    vn = V / hh
    # the plate's second-order shape.  All three coefficients are independent
    # draws, so this is a dome on one panel and a saddle on the next.
    w = (p.twist * un * vn + p.bow_u * (un * un - 0.333)
         + p.bow_v * (vn * vn - 0.333)
         + 0.55 * p.bow_u * un + 0.55 * p.bow_v * vn)
    # -- the window: 1 in the middle, 0 with zero slope at the fold line, so the
    #    sweep can tie to the face's boundary exactly and tangentially
    win = _sstep(np.minimum(U, wdev - U) / (0.16 * wdev)) * \
        _sstep((hh - np.abs(V)) / (0.16 * p.h))
    if extra_damp is not None:
        win = win * np.asarray(extra_damp, float)
    oil = np.zeros_like(U)
    for (m, q, amp, ph) in p.modes:
        oil = oil + amp * np.sin(m * math.pi * (U / wdev)) * \
            np.sin(q * math.pi * (V / p.h + 0.5) + 0.35 * (ph - 0.5))
    # -- telegraphing over the stiffeners
    tel = np.zeros_like(U)
    if stiff_v is not None:
        for vs in stiff_v:
            d = (V - vs) / 0.030
            tel = tel - 0.00055 * (1.0 + 0.7 * r01("tg", vs, *k)) * np.exp(-d * d)
        if len(stiff_v) > 1:
            pitch = (max(stiff_v) - min(stiff_v)) / max(len(stiff_v) - 1, 1)
            tel = tel + 0.00035 * np.cos(2.0 * math.pi * (V - min(stiff_v)) /
                                         max(pitch, 0.05)) * 0.5
    # -- dents, with rims
    dn = np.zeros_like(U)
    for (dx, dy, sg, amp) in p.dents:
        x0 = a + dx * a * 0.92
        y0 = dy * hh * 0.92
        rr2 = ((U - x0) ** 2 + (V - y0) ** 2) / (sg * sg)
        e = np.exp(-0.5 * rr2)
        dn = dn - amp * e + 0.34 * amp * rr2 * e
    # -- the roll ripple the brake did not take out
    rip = 0.00009 * (1.0 + r01("rp", *k)) * np.sin(
        2.0 * math.pi * U / rr(0.060, 0.140, "rl", *k) + 6.0 * r01("rph", *k))
    # -- and the part of the buckling that is NOT a clean mode.  A plate that
    #    has been racked, hung, thermally cycled and leaned on does not stay in
    #    its eigenbasis; without this the modes are too symmetric and 180 of
    #    them read as one panel repeated.
    seed_i, amp_i, len_i, rot_i = p.irr
    ca, sa = math.cos(rot_i), math.sin(rot_i)
    Ur = (U * ca - V * sa) / len_i
    Vr = (U * sa + V * ca) / len_i
    irr = amp_i * (fbm2(Ur, Vr, int(seed_i), oct=4, gain=0.58) - 0.5) * 2.0
    # -- and ONE hard crease, which is what an oil-canned tray really shows:
    #    a line where the plate has snapped through into its second stable
    #    shape, 0.3-1.2 mm deep and 45-115 mm wide, running where IT wants to.
    cang, cpos, cdep, cwid = p.crease
    d = ((U - 0.5 * wdev) * math.cos(cang) + V * math.sin(cang)) - cpos
    crease = cdep * (1.0 - 2.0 * np.clip(np.abs(d) / cwid, 0.0, 1.0) ** 2) \
        * np.exp(-(d / (1.7 * cwid)) ** 2)
    return w + win * (oil + tel + dn + rip + irr + crease)


def recess_profile(U, u0, u1, depth, r=0.014):
    """A C1 recessed channel between u0 and u1, `depth` deep, with radius-r
    folds -- the rainwater column.  Returns a NEGATIVE offset (into the wall)."""
    s = smoothstep(u0 - r, u0 + r, U) * (1.0 - smoothstep(u1 - r, u1 + r, U))
    return -depth * s


def dent_field(p, U, V, wdev):
    """0..1 mask of how deep into a dent each point is: the shader uses it for
    the burnished ring the dressing tool leaves."""
    a = 0.5 * wdev
    hh = 0.5 * p.h
    out = np.zeros_like(U)
    for (dx, dy, sg, amp) in p.dents:
        x0 = a + dx * a * 0.92
        y0 = dy * hh * 0.92
        rr2 = ((U - x0) ** 2 + (V - y0) ** 2) / (sg * sg)
        out = np.maximum(out, np.exp(-0.5 * rr2) * min(1.0, abs(amp) / 0.0006))
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------------------
#  6d.  THE FOLDED SECTION.  One profile, swept round a closed path, so the
#       arris corners come out as spherical octants with no patching and no
#       cracks.  The sheet has THICKNESS: the cut edge at the free end of the
#       lip is a real 3 mm face with a 0.5 mm chamfer on both arrises.
# ---------------------------------------------------------------------------
def cassette_profile(fab, ret_d=None, hem=False, lip_l=None):
    """[(n, w, smooth, tag)] from the fold line, round the outside, over the cut
    edge and back along the inside to the face's own back surface.

    n is measured OUTWARD from the fold line in the surface's own plane; w is
    measured INWARD (negative outward), both in metres.  Also returns the
    developed arc length at each point, which is what the sheet's UV needs.
    """
    r = fab["fold_r"]
    d = fab["ret_d"] if ret_d is None else ret_d
    r2 = fab["lip_r"]
    ll = fab["lip_l"] if lip_l is None else lip_l
    ch = fab["cut_chamfer"]
    t = SHEET_T
    P = []

    def put(n, w, sm=True, tag=""):
        P.append((n, w, sm, tag))

    # 1. the outer fold radius: tangent to the face at one end, to the return
    #    at the other, so smooth shading is CORRECT here and not a cover-up
    for i in range(N_ARC + 1):
        th = 0.5 * math.pi * i / N_ARC
        put(r * math.sin(th), -r * (1.0 - math.cos(th)), True, "arc")
    # 2. the return leg
    w_end = -(d - r2)
    for i in range(1, 4):
        put(r, -r + (w_end + r) * i / 3.0, True, "ret")
    # 3. the second fold, back inwards to the stiffening lip
    for i in range(1, N_ARC2 + 1):
        ph = 0.5 * math.pi * i / N_ARC2
        put(r - r2 + r2 * math.cos(ph), w_end - r2 * math.sin(ph), True, "arc2")
    # 4. the lip, outer surface
    n_end = r - r2 - ll
    if hem:                                            # 180 deg safety hem
        n_end = r - r2 - 0.016
    for i in range(1, 4):
        put(r - r2 + (n_end - (r - r2)) * i / 3.0, -d, True, "lip")
    # 5. the cut edge: chamfer, 3 mm face, chamfer.  FLAT-shaded, because a
    #    0.5 mm chamfer that is smooth-shaded is a 0.5 mm blur instead of the
    #    hard 0.5 px highlight the camera actually sees.
    put(n_end - ch, -d + ch, False, "cut")
    put(n_end - ch, -d + t - ch, False, "cut")
    put(n_end, -d + t, False, "cut")
    # 6. back along the inside
    for i in range(1, 4):
        put(n_end + (r - r2 - n_end) * i / 3.0, -d + t, True, "lipi")
    for i in range(1, N_ARC2 + 1):
        ph = 0.5 * math.pi * (1.0 - i / N_ARC2)
        put(r - r2 + (r2 - t) * math.cos(ph), w_end - (r2 - t) * math.sin(ph),
            True, "arc2i")
    for i in range(1, 4):
        put(r - t, w_end + (-r - w_end) * i / 3.0, True, "reti")
    for i in range(1, N_ARC + 1):
        th = 0.5 * math.pi * (1.0 - i / N_ARC)
        put((r - t) * math.sin(th), -r + (r - t) * math.cos(th), True, "arci")
    N = np.array([q[0] for q in P])
    W = np.array([q[1] for q in P])
    SM = [q[2] for q in P]
    TAG = [q[3] for q in P]
    # developed arc length along the profile, for the UV
    dl = np.concatenate([[0.0], np.hypot(np.diff(N), np.diff(W))])
    return N, W, np.cumsum(dl), SM, TAG


def build_path(us, vs, wdev, hh):
    """The closed sweep path round the face's fold line, sampled EXACTLY on the
    face grid's own boundary vertices so the two meshes share them, with
    N_CORNER extra samples at each corner carrying a rotating normal.

    Returns (u, v, a_t, a_v, ring_kind, param) where the n direction of the
    profile is a_t * plan_tangent + a_v * z_hat.
    """
    U, V, AT, AV, KI = [], [], [], [], []
    lo_u, hi_u = us[0], us[-1]
    lo_v, hi_v = vs[0], vs[-1]

    def corner(u0, v0, n0, n1):
        for i in range(1, N_CORNER + 1):
            f = i / (N_CORNER + 1.0)
            ang = (1.0 - f) * n0 + f * n1
            U.append(u0); V.append(v0)
            AT.append(math.cos(ang)); AV.append(math.sin(ang)); KI.append(2)

    # Every boundary vertex appears EXACTLY ONCE, walked counter-clockwise seen
    # from outside, with N_CORNER extra samples at each corner carrying nothing
    # but a rotating normal -- which is what turns the swept fold into a
    # spherical octant at the arris.  face_ring_index() must mirror this walk
    # index for index; the two are checked against each other in selftest().
    for u in us:                                       # bottom, +u, normal -v
        U.append(u); V.append(lo_v); AT.append(0.0); AV.append(-1.0); KI.append(0)
    corner(hi_u, lo_v, -0.5 * math.pi, 0.0)
    for v in vs[1:]:                                   # right, +v, normal +t
        U.append(hi_u); V.append(v); AT.append(1.0); AV.append(0.0); KI.append(0)
    corner(hi_u, hi_v, 0.0, 0.5 * math.pi)
    for u in us[-2::-1]:                               # top, -u, normal +v
        U.append(u); V.append(hi_v); AT.append(0.0); AV.append(1.0); KI.append(0)
    corner(lo_u, hi_v, 0.5 * math.pi, math.pi)
    for v in vs[-2:0:-1]:                              # left, -v, normal -t
        U.append(lo_u); V.append(v); AT.append(-1.0); AV.append(0.0); KI.append(0)
    corner(lo_u, lo_v, math.pi, 1.5 * math.pi)
    return (np.array(U), np.array(V), np.array(AT), np.array(AV),
            np.array(KI, int))


def face_ring_index(idx):
    """Indices of the face grid's boundary in the same order build_path walks."""
    out = []
    out += list(idx[:, 0])                             # bottom, +u
    out += [idx[-1, 0]] * N_CORNER
    out += list(idx[-1, 1:])                           # right, +v
    out += [idx[-1, -1]] * N_CORNER
    out += list(idx[-2::-1, -1])                       # top, -u
    out += [idx[0, -1]] * N_CORNER
    out += list(idx[0, -2:0:-1])                       # left, -v
    out += [idx[0, 0]] * N_CORNER
    return np.array(out, np.int64)


# ===========================================================================
#  7.  THE CASSETTE.  One panel, one mesh, built once, never instanced.
# ===========================================================================
def _insert(xs, extra, min_gap=0.0011):
    """Force `extra` into a sorted sample array without leaving a sliver."""
    xs = np.asarray(xs, float)
    for e in sorted(float(v) for v in extra):
        if e <= xs[0] + min_gap or e >= xs[-1] - min_gap:
            continue
        i = int(np.searchsorted(xs, e))
        if abs(xs[i - 1] - e) < min_gap:
            xs[i - 1] = e
        elif abs(xs[i] - e) < min_gap:
            xs[i] = e
        else:
            xs = np.insert(xs, i, e)
    return xs


def make_wfun(p, plan, Wd, stiff_v, rec):
    """The panel's own outward-displacement field, as ONE callable.

    Every feature -- rivet, blade, cam lock, boss, stiffener -- is placed
    through this, so nothing floats off the buckled sheet it is fixed to.  A
    rivet placed on a nominal plane and a sheet displaced 5 mm from it is how a
    fixing ends up hovering, and at 1037 px/m that is a 5 px gap.
    """
    def wfun(U, V):
        U = np.asarray(U, float)
        V = np.asarray(V, float)
        dp = None
        if rec:
            dp = 1.0 - (smoothstep(rec[0] - 0.055, rec[0] - 0.005, U)
                        * (1.0 - smoothstep(rec[1] + 0.005, rec[1] + 0.055, U)))
        w = plate_w(p, U, V, Wd, stiff_v, extra_damp=dp)
        if rec:
            w = w + recess_profile(U, rec[0], rec[1], REVEAL_DEPTH)
        return w
    return wfun


def _surf(plan, wfun, U, V, off=0.0):
    """Local xyz of a point `off` metres proud of the face at developed (U, V),
    plus the outward normal and the run tangent there."""
    U = np.asarray(U, float)
    V = np.asarray(V, float)
    w = wfun(U, V) + off
    Px, Pz, Tx, Tz, Nx, Nz = plan.eval(U)
    return Px + w * Nx, V, Pz + w * Nz, (Nx, Nz), (Tx, Tz)


def _aperture(p, Wd):
    """The rectangular hole in the face, if this cassette has one."""
    k = (p.elev, p.course, p.col)
    if p.kind == "louvre":
        w = min(0.62, Wd - 0.26)
        h = min(0.52, p.h - 0.24)
    elif p.kind == "perf":
        w = min(0.50, Wd - 0.30)
        h = min(0.30, p.h - 0.34)
    else:
        return None
    if w < 0.10 or h < 0.10:
        return None
    cu = 0.5 * Wd + rr(-0.035, 0.035, "apu", *k)
    cv = rr(-0.05, 0.05, "apv", *k) + (0.06 if p.kind == "perf" else 0.0)
    return (cu - 0.5 * w, cu + 0.5 * w, cv - 0.5 * h, cv + 0.5 * h)


def _recess(p, Wd):
    """The rainwater column: a 90 mm deep, 240 mm wide recessed channel."""
    if p.kind != "rwp":
        return None
    k = (p.elev, p.course, p.col)
    w = min(0.240, Wd - 0.30)
    if w < 0.12:
        return None
    cu = 0.5 * Wd + rr(-0.02, 0.02, "rcu", *k)
    return (cu - 0.5 * w, cu + 0.5 * w)


def build_cassette(p):
    """(V, UV, A, W, faces) for one panel, in panel-local metres.

    The order is the order of fabrication: the blank is cut from the coil (the
    face grid IS the coil), the four edges are braked over the fold radius, the
    corners come out as spherical octants because the sweep path turns through
    90 deg at a point, the lip is closed with a real 3 mm cut edge, the back is
    stiffened, the hooks are riveted on, and only then is the aperture, the
    recess or the cam-lock set put in.
    """
    fab = FAB[p.fab]
    plan, Wd = panel_plan(p)
    r = fab["fold_r"]
    t = SHEET_T
    hh = 0.5 * p.h
    acc = Acc()

    ns = max(1, p.n_stiff)
    stiff_v = [(-hh + (i + 1) * p.h / (ns + 1)) + p.stiff_v * (1 if i % 2 else -1)
               for i in range(ns)]
    ap = _aperture(p, Wd)
    rec = _recess(p, Wd)
    wfun = make_wfun(p, plan, Wd, stiff_v, rec)

    # ---- 1. the two graded axes ------------------------------------------
    fu, fv = [], []
    if ap:
        fu += [ap[0], ap[1]]
        fv += [ap[2], ap[3]]
    if rec:
        fu += [rec[0] - 0.014, rec[0] + 0.014, rec[1] - 0.014, rec[1] + 0.014]
    us = graded_axis(Wd - 2 * r, features=fu, a=r)
    vs = graded_axis(p.h - 2 * r, features=fv, a=-hh + r)
    if p.kind == "corner":
        # the 90 deg arris: 8.6 mm of developed sheet, and THE silhouette of
        # this panel.  It gets its own samples or it comes out as a chamfer.
        arc = [plan.leg + 0.5 * math.pi * r * i / (N_ARC + 1)
               for i in range(N_ARC + 2)]
        us = _insert(us, arc, 0.0008)
    if ap:
        ap = (float(us[np.argmin(abs(us - ap[0]))]),
              float(us[np.argmin(abs(us - ap[1]))]),
              float(vs[np.argmin(abs(vs - ap[2]))]),
              float(vs[np.argmin(abs(vs - ap[3]))]))
    nu, nv = us.size, vs.size

    # ---- 2. the face sheet ----------------------------------------------
    UU, VV = np.meshgrid(us, vs, indexing="ij")
    Wf = wfun(UU, VV)
    Px, Pz, Tx, Tz, Nx, Nz = plan.eval(UU)
    edge = np.minimum(np.minimum(UU - us[0], us[-1] - UU), vs[-1] - np.abs(VV))
    dent = dent_field(p, UU, VV, Wd)
    weld = (_sstep((0.024 - np.abs(UU - (plan.leg + 0.25 * math.pi * r))) / 0.024)
            if p.kind == "corner" else np.zeros_like(UU))
    base = acc.add(Px + Wf * Nx, VV, Pz + Wf * Nz, UU, VV,
                   edge, 1.0, 0.0, dent, weld)
    idx = base + np.arange(nu * nv).reshape(nu, nv)
    mask = np.ones((nu - 1, nv - 1), bool)
    if ap:
        CU, CV = np.meshgrid(0.5 * (us[:-1] + us[1:]), 0.5 * (vs[:-1] + vs[1:]),
                             indexing="ij")
        mask &= ~((CU > ap[0]) & (CU < ap[1]) & (CV > ap[2]) & (CV < ap[3]))
    acc.grid_quads(idx, MAT_ANOD, True, mask)

    # ---- 3. the four braked edges, as one closed sweep -------------------
    hem = (p.course == 3)
    pu, pv, pat, pav, pki = build_path(us, vs, Wd, hh)
    ring0 = face_ring_index(idx)
    if ring0.size != pu.size:
        raise RuntimeError("path/ring mismatch %d vs %d" % (pu.size, ring0.size))
    w0 = wfun(pu, pv)
    PPx, PPz, PTx, PTz, PNx, PNz = plan.eval(pu)
    pweld = (_sstep((0.024 - np.abs(pu - (plan.leg + 0.25 * math.pi * r))) / 0.024)
             if p.kind == "corner" else np.zeros_like(pu))
    # The drip course's bottom edge returns 45 mm instead of 32 and is hemmed
    # instead of lipped.  The two profiles are BLENDED over the first 60 mm off
    # each bottom corner rather than switched: switching put a 13 mm step across
    # one 3.4 mm path step, which is a fin, and a real fabricator welds a
    # tapered gusset there for exactly the same reason.
    if hem:
        dfac = np.where((pav < -0.5) & (pki == 0),
                        _sstep(np.minimum(pu - us[0], us[-1] - pu) / 0.060), 0.0)
    else:
        dfac = np.zeros(pu.size)
    Npf, Wpf, Spf, SMpf, TAGpf = cassette_profile(fab)
    Npd, Wpd, Spd, SMpd, TAGpd = cassette_profile(fab, ret_d=DRIP_RET_D, hem=True)
    prev = ring0
    for j in range(1, Npf.size):
        n = Npf[j] + dfac * (Npd[j] - Npf[j])
        wp = Wpf[j] + dfac * (Wpd[j] - Wpf[j])
        sp = Spf[j] + dfac * (Spd[j] - Spf[j])
        wt = w0 + wp
        X = PPx + n * pat * PTx + wt * PNx
        Z = PPz + n * pat * PTz + wt * PNz
        Y = pv + n * pav
        b = acc.add(X, Y, Z, pu + sp * pat, pv + sp * pav,
                    -sp, _sstep((0.009 - sp) / 0.009), -wp, 0.0, pweld)
        row = b + np.arange(pu.size)
        # Where the profile is back ON the fold line (n = 0, which is the last
        # point: the inside of the face sheet) the corner fan collapses to a
        # point, so the fan's samples are welded onto the corner's own vertex
        # rather than left as 20 coincident vertices and 20 zero-length edges.
        if abs(float(Npf[j])) < 1e-12 and abs(float(Npd[j])) < 1e-12:
            for i in np.flatnonzero(pki == 2):
                row[i] = row[i - 1]
        acc.strip(prev, row, MAT_ANOD, SMpf[j])
        prev = row
    inner_ring = prev

    # ---- 4. the back of the sheet, coarse: it is inside a sealed tray -----
    gap = 0.014
    bu = graded_axis(Wd - 2 * r - 2 * gap, cell_mid=4.2 * CELL_MID,
                     cell_edge=2.2 * CELL_EDGE, band=0.05, a=r + gap)
    bv = graded_axis(p.h - 2 * r - 2 * gap, cell_mid=4.2 * CELL_MID,
                     cell_edge=2.2 * CELL_EDGE, band=0.05, a=-hh + r + gap)
    BU, BV = np.meshgrid(bu, bv, indexing="ij")
    BW = wfun(BU, BV) - t
    BPx, BPz, _, _, BNx, BNz = plan.eval(BU)
    bmask = np.ones((bu.size - 1, bv.size - 1), bool)
    if ap:
        CU, CV = np.meshgrid(0.5 * (bu[:-1] + bu[1:]), 0.5 * (bv[:-1] + bv[1:]),
                             indexing="ij")
        bmask &= ~((CU > ap[0] - 0.024) & (CU < ap[1] + 0.024) &
                   (CV > ap[2] - 0.024) & (CV < ap[3] + 0.024))
    bb = acc.add(BPx + BW * BNx, BV, BPz + BW * BNz, BU, BV,
                 0.0, 0.0, 0.0035, 0.0, 0.0)
    bidx = bb + np.arange(bu.size * bv.size).reshape(bu.size, bv.size)
    acc.grid_quads(bidx[:, ::-1], MAT_ANOD, True, bmask[:, ::-1])
    acc.stitch(inner_ring, _ring_param(pu, pv),
               face_ring_index(bidx), _ring_param_grid(bu, bv), MAT_ANOD, True)

    # ---- 5. what is behind the joint ------------------------------------
    _stiffeners(acc, p, plan, wfun, Wd, stiff_v, us, t)
    _hooks(acc, p, plan, wfun, Wd, fab, r)

    # ---- 6. the families -------------------------------------------------
    if ap and p.kind == "louvre":
        _louvre(acc, p, plan, wfun, Wd, ap)
    if ap and p.kind == "perf":
        _perf(acc, p, plan, wfun, Wd, ap)
    if p.kind == "access":
        _camlocks(acc, p, plan, wfun, Wd)
    if p.kind == "signback":
        _signback(acc, p, plan, wfun, Wd)
    return acc.finish()


def _ring_param(pu, pv):
    """Normalised arc-length parameter of a swept ring, for the stitch."""
    d = np.hypot(np.diff(np.append(pu, pu[0])), np.diff(np.append(pv, pv[0])))
    s = np.concatenate([[0.0], np.cumsum(d)[:-1]])
    tot = s[-1] + d[-1]
    return s / max(tot, 1e-9)


def _ring_param_grid(bu, bv):
    pu, pv, _, _, _ = build_path(bu, bv, 0.0, 0.0)
    return _ring_param(pu, pv)


# ---------------------------------------------------------------------------
#  7a.  BONDED TOP-HAT STIFFENERS.  1.5 mm folded section, structurally bonded
#       to the back of the sheet with 12 mm tape.  This is what telegraphs.
# ---------------------------------------------------------------------------
def _stiffeners(acc, p, plan, wfun, Wd, stiff_v, us, t):
    hw, dep, fl, ts = 0.020, 0.022, 0.014, 0.0015
    u0, u1 = us[0] + 0.010, us[-1] - 0.010
    n = max(6, int((u1 - u0) / 0.048))
    U = np.linspace(u0, u1, n + 1)
    prof = [(-hw - fl, 0.0), (-hw, 0.0), (-hw, -dep), (hw, -dep),
            (hw, 0.0), (hw + fl, 0.0)]
    prof = prof + [(a, b - ts) for (a, b) in prof[::-1]]
    for vsx in stiff_v:
        rows = []
        for (dv, dw) in prof:
            X, Y, Z, _, _ = _surf(plan, wfun, U, np.full(U.shape, vsx + dv),
                                  off=-t + dw)
            b = acc.add(X, Y, Z, U, vsx + dv, -0.05, 0.0, t - dw, 0.0, 0.0)
            rows.append(b + np.arange(U.size))
        for a_, b_ in zip(rows[:-1], rows[1:]):
            acc.strip(a_, b_, MAT_MILL, False, closed=False)
        acc.strip(rows[-1], rows[0], MAT_MILL, False, closed=False)


def _hooks(acc, p, plan, wfun, Wd, fab, r):
    """Two hangers on the top return, two retainers on the bottom.  You see
    these up through the 15 mm joint, which in Beat 4 the camera does."""
    d = fab["ret_d"]
    hh = 0.5 * p.h
    L = 0.060
    for side in (+1, -1):
        for i in range(2):
            u = 0.5 * Wd + (i - 0.5) * min(0.60 * Wd, 0.60)
            pts = [(-0.006, -0.014), (-0.006, -(d + 0.018)),
                   (-0.026, -(d + 0.018)), (-0.026, -(d + 0.014)),
                   (-0.010, -(d + 0.014)), (-0.010, -0.014)]
            Px, Pz, Tx, Tz, Nx, Nz = plan.eval(np.array([u]))
            w0 = float(np.ravel(wfun(np.array([u]), np.array([side * (hh - r)])))[0])
            px_, pz_ = float(np.ravel(Px)[0]), float(np.ravel(Pz)[0])
            tx, tz = float(np.ravel(Tx)[0]), float(np.ravel(Tz)[0])
            nx, nz = float(np.ravel(Nx)[0]), float(np.ravel(Nz)[0])
            rows = []
            for half in (-0.5 * L, 0.5 * L):
                X = np.array([px_ + tx * half + (w0 + dw) * nx for (_, dw) in pts])
                Z = np.array([pz_ + tz * half + (w0 + dw) * nz for (_, dw) in pts])
                Y = np.array([side * hh + side * dv for (dv, _) in pts])
                b = acc.add(X, Y, Z, u + half, Y, -0.06, 0.0, 0.05, 0.0, 0.0)
                rows.append(b + np.arange(len(pts)))
            acc.strip(rows[0], rows[1], MAT_MILL, False, closed=True)
            for j in range(3):
                _rivet_on_return(acc, p, plan, wfun, Wd, r,
                                 u + (j - 1) * 0.020, side, 0.010 + d * 0.45)


def _rivet_on_return(acc, p, plan, wfun, Wd, r, u, side, depth):
    """A 4.8 mm domed rivet 1.6 mm proud of the RETURN face -- i.e. standing
    into the 15 mm joint, where the raking sun makes it a bright dot with
    2.6 mm of shadow on the east elevation and 1.1 mm on the south."""
    hh = 0.5 * p.h
    Px, Pz, Tx, Tz, Nx, Nz = plan.eval(np.array([u]))
    w0 = float(np.ravel(wfun(np.array([u]), np.array([side * (hh - r)])))[0])
    cx = float(np.ravel(Px)[0]) + (w0 - depth) * float(np.ravel(Nx)[0])
    cz = float(np.ravel(Pz)[0]) + (w0 - depth) * float(np.ravel(Nz)[0])
    tx, tz = float(np.ravel(Tx)[0]), float(np.ravel(Tz)[0])
    nx, nz = float(np.ravel(Nx)[0]), float(np.ravel(Nz)[0])
    ns = N_RIVET_SEG
    ang = np.linspace(0.0, 2.0 * math.pi, ns, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    prev = None
    for (rad, ht) in ((RIVET_FLANGE_R, 0.0), (RIVET_FLANGE_R * 0.93, 0.00035),
                      (RIVET_FLANGE_R * 0.74, 0.0010),
                      (RIVET_FLANGE_R * 0.42, 0.00150),
                      (RIVET_FLANGE_R * 0.19, RIVET_DOME_H)):
        X = cx + tx * (rad * ca) + nx * (rad * sa)
        Z = cz + tz * (rad * ca) + nz * (rad * sa)
        Y = np.full(ns, side * hh + side * ht)
        b = acc.add(X, Y, Z, u + rad * ca, Y, -0.02, 0.0, depth, 0.0, 0.0)
        row = b + np.arange(ns)
        if prev is not None:
            acc.strip(prev if side > 0 else row, row if side > 0 else prev,
                      MAT_MILL, True, closed=True)
        prev = row
    c = acc.add(np.array([cx]), np.array([side * (hh + RIVET_DOME_H)]),
                np.array([cz]), u, side * hh, -0.02, 0.0, depth, 0.0, 0.0)
    tri = (np.stack([prev, np.roll(prev, -1), np.full(ns, c)], axis=1) if side > 0
           else np.stack([np.roll(prev, -1), prev, np.full(ns, c)], axis=1))
    acc.tris(tri, MAT_MILL, True)


def _rivet_on_face(acc, p, plan, wfun, Wd, u, v, mat=MAT_MILL):
    """The same rivet through the FACE.  Only the louvre, perf and access
    cassettes have these: on a plain weather face an exposed fixing would be a
    leak and no fabricator would put one there."""
    ns = N_RIVET_SEG
    ang = np.linspace(0.0, 2.0 * math.pi, ns, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    prev = None
    for (rad, ht) in ((RIVET_FLANGE_R, 0.0), (RIVET_FLANGE_R * 0.93, 0.00035),
                      (RIVET_FLANGE_R * 0.74, 0.0010),
                      (RIVET_FLANGE_R * 0.42, 0.00150),
                      (RIVET_FLANGE_R * 0.19, RIVET_DOME_H)):
        U = u + rad * ca
        V = v + rad * sa
        X, Y, Z, _, _ = _surf(plan, wfun, U, V, off=ht)
        b = acc.add(X, Y, Z, U, V, 0.02, 1.0, -ht, 0.0, 0.0)
        row = b + np.arange(ns)
        if prev is not None:
            acc.strip(prev, row, mat, True, closed=True)
        prev = row
    X, Y, Z, _, _ = _surf(plan, wfun, np.array([u]), np.array([v]),
                          off=RIVET_DOME_H)
    c = acc.add(X, Y, Z, u, v, 0.02, 1.0, -RIVET_DOME_H, 0.0, 0.0)
    acc.tris(np.stack([prev, np.roll(prev, -1), np.full(ns, c)], axis=1), mat,
             True)


# ---------------------------------------------------------------------------
#  7b.  THE LOUVRE CASSETTE.  Plant-room extract: the sheet is folded back
#       25 mm all round the aperture, seven chevron blades sit in it at 35 deg,
#       a stainless bird mesh sits behind them, and the plenum behind that is
#       black -- without which the aperture is a hole to the sky and the whole
#       cassette reads as a sticker.
# ---------------------------------------------------------------------------
def _aperture_return(acc, p, plan, wfun, ap, depth, rr_=0.004, lip=0.010):
    """The sheet folded back into the hole: a 4 mm radius, a wall `depth` deep
    and a lip turned in behind it.  Shared by the louvre and the perforated
    cassette, because both are the same fabrication."""
    u0, u1, v0, v1 = ap
    nu = max(8, int((u1 - u0) / 0.011))
    nv = max(8, int((v1 - v0) / 0.011))
    pu, pv, pat, pav, pki = build_path(np.linspace(u0, u1, nu + 1),
                                       np.linspace(v0, v1, nv + 1), 0.0, 0.0)
    prof = [(0.0, 0.0)]
    for i in range(1, 5):
        th = 0.5 * math.pi * i / 4
        prof.append((-rr_ * math.sin(th), -rr_ * (1.0 - math.cos(th))))
    prof.append((-rr_, -depth))
    prof.append((-rr_ - lip, -depth))
    prev = None
    for (n, w) in prof:
        X, Y, Z, _, _ = _surf(plan, wfun, pu + n * pat, pv + n * pav, off=w)
        b = acc.add(X, Y, Z, pu + n * pat, pv + n * pav, -abs(n), 0.55, -w,
                    0.0, 0.0)
        row = b + np.arange(pu.size)
        if abs(n) < 1e-12:                             # the fan collapses here
            for i in np.flatnonzero(pki == 2):
                row[i] = row[i - 1]
        if prev is not None:
            acc.strip(row, prev, MAT_ANOD, True, closed=True)
        prev = row


def _louvre(acc, p, plan, wfun, Wd, ap):
    u0, u1, v0, v1 = ap
    depth = 0.025
    _aperture_return(acc, p, plan, wfun, ap, depth, lip=0.008)
    nb = 7
    for i in range(nb):
        vc = v0 + (i + 0.5) * (v1 - v0) / nb
        _blade(acc, p, plan, wfun, u0 + 0.006, u1 - 0.006, vc,
               (v1 - v0) / nb, depth)
    _mesh_panel(acc, p, plan, wfun, u0 + 0.004, u1 - 0.004, v0 + 0.004,
                v1 - 0.004, depth + 0.030)
    _plenum(acc, p, plan, wfun, u0, u1, v0, v1, depth + 0.085)
    npx = max(3, int((u1 - u0) / 0.115))
    for i in range(npx + 1):
        uu = u0 + (u1 - u0) * i / npx
        _rivet_on_face(acc, p, plan, wfun, Wd, uu, v0 - 0.013)
        _rivet_on_face(acc, p, plan, wfun, Wd, uu, v1 + 0.013)


def _blade(acc, p, plan, wfun, u0, u1, vc, pitch, depth):
    """One weather blade: a chevron with a folded drip nose, 1.6 mm, at 35 deg."""
    n = max(8, int((u1 - u0) / 0.030))
    U = np.linspace(u0, u1, n + 1)
    a = math.radians(35.0)
    L = pitch * 1.35
    tb = 0.0016
    # The leading edge sits 4 mm INSIDE the aperture and the blade falls away
    # from there.  Centring the chord on the aperture's mid-depth instead put
    # the lead edge 21 mm PROUD of the cladding plane -- blades sticking out
    # through the facade.  Measured off the built mesh, not eyeballed.
    lead = (0.5 * L * math.cos(a), -0.004)
    tail = (-0.5 * L * math.cos(a), -0.004 - L * math.sin(a))
    nose = (lead[0] - 0.004, lead[1] + 0.005)
    pts = [nose, lead, tail, (tail[0] - tb * 1.2, tail[1] - tb),
           (lead[0] - tb * 1.2, lead[1] - tb), (nose[0] - tb, nose[1] - tb * 0.2)]
    rows = []
    for (dv, dw) in pts:
        X, Y, Z, _, _ = _surf(plan, wfun, U, np.full(U.shape, vc + dv), off=dw)
        b = acc.add(X, Y, Z, U, vc + dv, -0.04, 0.0, -dw, 0.0, 0.0)
        rows.append(b + np.arange(U.size))
    for a_, b_ in zip(rows[:-1], rows[1:]):
        acc.strip(b_, a_, MAT_ANOD, False, closed=False)
    acc.strip(rows[0], rows[-1], MAT_ANOD, False, closed=False)


def _mesh_panel(acc, p, plan, wfun, u0, u1, v0, v1, depth):
    pitch, wire = 0.012, 0.0012
    nu = max(2, int((u1 - u0) / pitch))
    nv = max(2, int((v1 - v0) / pitch))
    for i in range(nu + 1):
        u = u0 + (u1 - u0) * i / nu
        _ribbon(acc, p, plan, wfun, np.array([u, u]), np.array([v0, v1]),
                depth, wire, True)
    for j in range(nv + 1):
        v = v0 + (v1 - v0) * j / nv
        _ribbon(acc, p, plan, wfun, np.array([u0, u1]), np.array([v, v]),
                depth + wire, wire, False)


def _ribbon(acc, p, plan, wfun, U, V, depth, wid, vertical):
    """A single wire, square in section, as four strips."""
    su = 0.5 * wid if vertical else 0.0
    sv = 0.0 if vertical else 0.5 * wid
    rows = []
    for (du, dv, dw) in ((-su, -sv, 0.0), (su, sv, 0.0), (su, sv, -wid),
                         (-su, -sv, -wid)):
        X, Y, Z, _, _ = _surf(plan, wfun, U + du, V + dv, off=-depth + dw)
        b = acc.add(X, Y, Z, U + du, V + dv, -0.05, 0.0, depth, 0.0, 0.0)
        rows.append(b + np.arange(U.size))
    for a_, b_ in zip(rows, rows[1:] + rows[:1]):
        acc.strip(a_, b_, MAT_MESH, False, closed=False)


def _plenum(acc, p, plan, wfun, u0, u1, v0, v1, depth):
    US = np.array([u0 - 0.012, u1 + 0.012])
    VS = np.array([v0 - 0.012, v1 + 0.012])
    UU, VV = np.meshgrid(US, VS, indexing="ij")
    X, Y, Z, _, _ = _surf(plan, wfun, UU, VV, off=-depth)
    b = acc.add(X, Y, Z, UU, VV, -0.08, 0.0, depth, 0.0, 0.0)
    idx = b + np.arange(4).reshape(2, 2)
    acc.grid_quads(idx, MAT_DARK, False)
    X2, Y2, Z2, _, _ = _surf(plan, wfun, UU, VV, off=-0.018)
    b2 = acc.add(X2, Y2, Z2, UU, VV, -0.08, 0.0, 0.018, 0.0, 0.0)
    i2 = b2 + np.arange(4).reshape(2, 2)
    for (a0, a1), (c0, c1) in (((idx[0, 0], idx[0, 1]), (i2[0, 0], i2[0, 1])),
                               ((idx[1, 1], idx[1, 0]), (i2[1, 1], i2[1, 0])),
                               ((idx[0, 1], idx[1, 1]), (i2[0, 1], i2[1, 1])),
                               ((idx[1, 0], idx[0, 0]), (i2[1, 0], i2[0, 0]))):
        acc.quads(np.array([[a0, c0, c1, a1]]), MAT_DARK, False)


# ---------------------------------------------------------------------------
#  7c.  THE PERFORATED CASSETTE.  6 mm holes on a 16 mm SQUARE pitch, which
#       tiles exactly, so the plate has no gaps and no jagged border: 8 ring
#       quads and an 8-quad barrel per hole, ~500 holes, all real.  The entry
#       is rolled over 0.6 mm because a punch does that, and the plenum behind
#       is black.
# ---------------------------------------------------------------------------
def _perf(acc, p, plan, wfun, Wd, ap, hole_d=0.006, pitch=0.016):
    u0, u1, v0, v1 = ap
    # THE PLATE IS AN INSET TRAY, 24 mm behind a folded aperture return, and the
    # perforated field is laid out one cell BIGGER than the hole on every side.
    # Sized to the hole instead, the field can only ever be a whole number of
    # cells, so up to 8 mm of slot was left open all the way round it -- a hole
    # in the facade with the plenum showing through.
    _aperture_return(acc, p, plan, wfun, ap, 0.024, lip=0.012)
    plate_w_off = -0.024
    nu = max(3, int(math.ceil((u1 - u0) / pitch)) + 2)
    nv = max(3, int(math.ceil((v1 - v0) / pitch)) + 2)
    cu0 = 0.5 * (u0 + u1) - 0.5 * nu * pitch
    cv0 = 0.5 * (v0 + v1) - 0.5 * nv * pitch
    ci = (np.arange(nu) + 0.5) * pitch + cu0
    cj = (np.arange(nv) + 0.5) * pitch + cv0
    CU, CV = np.meshgrid(ci, cj, indexing="ij")
    ru = CU.ravel()
    rv = CV.ravel()
    nh = ru.size
    ang = np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    rh = 0.5 * hole_d
    # the square cell boundary sampled at the SAME eight angles: four edge
    # midpoints at pitch/2 and four corners at pitch/2 * sqrt(2)
    sq = 0.5 * pitch / np.maximum(np.abs(ca), np.abs(sa))
    rings = []
    for (rad, dw) in ((rh, plate_w_off - 0.0006), (rh * 1.22, plate_w_off),
                      (None, plate_w_off)):
        R = sq if rad is None else np.full(8, rad)
        U = ru[:, None] + R[None, :] * ca[None, :]
        V = rv[:, None] + R[None, :] * sa[None, :]
        X, Y, Z, _, _ = _surf(plan, wfun, U, V, off=dw)
        b = acc.add(X, Y, Z, U, V, 0.02, 1.0, -dw, 0.0, 0.0)
        rings.append(b + np.arange(nh * 8).reshape(nh, 8))
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for h in range(nh):
            acc.strip(a_[h], b_[h], MAT_ANOD, True, closed=True)
    U = ru[:, None] + rh * ca[None, :]
    V = rv[:, None] + rh * sa[None, :]
    X, Y, Z, _, _ = _surf(plan, wfun, U, V,
                          off=plate_w_off - SHEET_T - 0.0006)
    b = acc.add(X, Y, Z, U, V, 0.0, 0.0, SHEET_T, 0.0, 0.0)
    barrel = b + np.arange(nh * 8).reshape(nh, 8)
    for h in range(nh):
        acc.strip(rings[0][h], barrel[h], MAT_ANOD, True, closed=True)
    # the plate is set 22 mm back behind the aperture, with a folded reveal
    _plenum(acc, p, plan, wfun, u0, u1, v0, v1, 0.060)
    npx = max(3, int((u1 - u0) / 0.13))
    for i in range(npx + 1):
        uu = u0 + (u1 - u0) * i / npx
        _rivet_on_face(acc, p, plan, wfun, Wd, uu, v0 - 0.012)
        _rivet_on_face(acc, p, plan, wfun, Wd, uu, v1 + 0.012)


def _camlocks(acc, p, plan, wfun, Wd):
    """Four quarter-turn cam locks: a 22 mm disc 3.2 mm proud with a 3 mm slot
    across it.  This is how a cavity inspection cassette is opened, and the
    slot is 3 px wide at the filmed distance."""
    for (fu, fv) in ((0.22, 0.30), (0.78, 0.30), (0.22, 0.70), (0.78, 0.70)):
        u = fu * Wd
        v = (fv - 0.5) * p.h * 0.86
        ns = 24
        ang = np.linspace(0.0, 2.0 * math.pi, ns, endpoint=False)
        ca, sa = np.cos(ang), np.sin(ang)
        prev = None
        for (rad, dw) in ((0.011, 0.0), (0.011, 0.0032), (0.0092, 0.0038),
                          (0.0038, 0.0038), (0.0038, 0.0022)):
            U = u + rad * ca
            V = v + rad * sa
            X, Y, Z, _, _ = _surf(plan, wfun, U, V, off=dw)
            b = acc.add(X, Y, Z, U, V, 0.02, 1.0, -dw, 0.0, 0.0)
            row = b + np.arange(ns)
            if prev is not None:
                acc.strip(prev, row, MAT_MILL, False, closed=True)
            prev = row
        X, Y, Z, _, _ = _surf(plan, wfun, np.array([u]), np.array([v]), off=0.0022)
        c = acc.add(X, Y, Z, u, v, 0.02, 1.0, -0.0022, 0.0, 0.0)
        acc.tris(np.stack([prev, np.roll(prev, -1), np.full(ns, c)], axis=1),
                 MAT_MILL, False)


def _signback(acc, p, plan, wfun, Wd):
    """A 4 mm bonded backing plate and six M8 bosses -- what the lettering item
    fixes into.  On the back, so it is invisible, and it is still built because
    sign_fix_grid() promises it is there."""
    u0, u1 = 0.10 * Wd, 0.90 * Wd
    v0, v1 = -0.34 * p.h, 0.34 * p.h
    UU, VV = np.meshgrid(np.array([u0, u1]), np.array([v0, v1]), indexing="ij")
    for dw in (-SHEET_T - 0.0005, -SHEET_T - 0.0045):
        X, Y, Z, _, _ = _surf(plan, wfun, UU, VV, off=dw)
        b = acc.add(X, Y, Z, UU, VV, -0.05, 0.0, -dw, 0.0, 0.0)
        acc.grid_quads((b + np.arange(4).reshape(2, 2))[:, ::-1], MAT_MILL, False)
    ns = 10
    ang = np.linspace(0.0, 2.0 * math.pi, ns, endpoint=False)
    for i in range(3):
        for j in range(2):
            u = u0 + (u1 - u0) * (i + 0.5) / 3.0
            v = v0 + (v1 - v0) * (j + 0.5) / 2.0
            prev = None
            for (rad, dw) in ((0.008, -SHEET_T - 0.0045),
                              (0.008, -SHEET_T - 0.0180),
                              (0.004, -SHEET_T - 0.0180)):
                U = u + rad * np.cos(ang)
                V = v + rad * np.sin(ang)
                X, Y, Z, _, _ = _surf(plan, wfun, U, V, off=dw)
                b = acc.add(X, Y, Z, U, V, -0.05, 0.0, -dw, 0.0, 0.0)
                row = b + np.arange(ns)
                if prev is not None:
                    acc.strip(row, prev, MAT_MILL, False, closed=True)
                prev = row


# ===========================================================================
#  8.  BLENDER SIDE: meshes, objects, attributes.
# ===========================================================================
def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in [ch.name for ch in par.children]:
        try:
            par.children.link(c)
        except RuntimeError:
            pass
    return c


def _clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.collections,
                bpy.data.lights, bpy.data.cameras, bpy.data.worlds,
                bpy.data.images):
        for b in list(blk):
            try:
                blk.remove(b)
            except Exception:
                pass


def make_mesh(name, V, UV, A, W, faces, mats):
    """Build the mesh with foreach_set only -- no per-vertex Python."""
    me = bpy.data.meshes.new(name)
    nv = V.shape[0]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(V, np.float32).ravel())
    loops, starts, totals, mi, sm = [], [], [], [], []
    at = 0
    for (idx, mat, smooth) in faces:
        k = idx.shape[1]
        n = idx.shape[0]
        loops.append(idx.astype(np.int32).ravel())
        starts.append(at + np.arange(n, dtype=np.int32) * k)
        totals.append(np.full(n, k, np.int32))
        mi.append(np.full(n, mat, np.int32))
        sm.append(np.full(n, 1 if smooth else 0, np.int32))
        at += n * k
    loops = np.concatenate(loops) if loops else np.zeros(0, np.int32)
    starts = np.concatenate(starts) if starts else np.zeros(0, np.int32)
    totals = np.concatenate(totals) if totals else np.zeros(0, np.int32)
    mi = np.concatenate(mi) if mi else np.zeros(0, np.int32)
    sm = np.concatenate(sm) if sm else np.zeros(0, np.int32)
    nf = starts.size
    me.loops.add(loops.size)
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", starts)
    me.polygons.foreach_set("loop_total", totals)
    me.update(calc_edges=True)
    me.polygons.foreach_set("material_index", mi)
    me.polygons.foreach_set("use_smooth", sm)
    # the shader's five channels
    a4 = np.zeros((nv, 4), np.float32)
    a4[:, :] = A[:, :4]
    at1 = me.attributes.new(ATTR_M, "FLOAT_COLOR", "POINT")
    at1.data.foreach_set("color", a4.ravel())
    at2 = me.attributes.new(ATTR_W, "FLOAT", "POINT")
    at2.data.foreach_set("value", np.ascontiguousarray(W, np.float32))
    # UV = the DEVELOPED SHEET coordinate, in metres
    uv = me.uv_layers.new(name="UVMap")
    uv.uv.foreach_set("vector",
                      np.ascontiguousarray(UV[loops], np.float32).ravel())
    for m in mats:
        me.materials.append(m)
    me.update()
    me.validate(verbose=False)
    return me


def bake_object_attrs(ob, p):
    """The per-panel constants the shader reads as OBJECT attributes.

    They are object custom properties and not vertex data on purpose: they are
    constant over a panel, and 180 panels x 70 k vertices x 8 floats of constant
    is 400 MB of blend file saying the same thing over and over.
    DEPENDANTS: anything you emit into MAT_NAME must carry these or it renders
    with a zero tint.
    """
    tint = list(BATCH_TINT[p.batch]) if p.batch >= 0 else list(REPLACED_TINT)
    g = 1.0 + p.bright
    ob["sfp_tint"] = [float(min(0.95, c * g + p.hue * (1 if i == 0 else -0.5)))
                      for i, c in enumerate(tint)]
    rough = (BATCH_ROUGH[p.batch] if p.batch >= 0 else 0.305)
    ob["sfp_p1"] = [float(p.gflip), float((p.imm - 0.5) * p.h),
                    float(p.age)]
    ob["sfp_p2"] = [float(p.soil), float(1.0 if p.rub else 0.0),
                    float(1.0 if p.bloom else 0.0)]
    ob["sfp_p3"] = [float(r01("ph", p.elev, p.course, p.col) * 10.0),
                    float(rough), float(p.course)]
    ob["sfp_kind"] = p.kind
    ob["sfp_fab"] = FAB[p.fab]["name"]
    ob["sfp_batch"] = int(p.batch)


# ===========================================================================
#  9.  THE FINISH.  Etched, 22 um clear anodise, sealed.  Every layer below is
#      a mechanism a real facade has, with its amplitude stated, and every
#      DEPOSIT changes roughness as well as colour -- which is what makes a
#      deposit read as a deposit and not as paint.  v1 was rejected for exactly
#      that: mottle with no roughness partner and no relief under it.
# ===========================================================================
class MB(object):
    """Minimal node-graph builder.  Keeps the material readable as a list of
    physical mechanisms rather than 200 lines of node plumbing."""

    def __init__(self, mat):
        self.nt = mat.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.col = 0

    def n(self, kind, **kw):
        nd = self.nt.nodes.new(kind)
        self.col += 1
        nd.location = (-2600 + 150 * (self.col % 18), 900 - 260 * (self.col // 18))
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def link(self, a, ao, b, bi):
        oa = a.outputs[ao] if isinstance(ao, str) else a.outputs[ao]
        ib = b.inputs[bi] if isinstance(bi, str) else b.inputs[bi]
        self.nt.links.new(oa, ib)
        return b

    def val(self, v):
        nd = self.n("ShaderNodeValue")
        nd.outputs[0].default_value = float(v)
        return nd

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, s in enumerate((a, b, c)):
            if s is None:
                continue
            if isinstance(s, tuple):
                self.link(s[0], s[1], nd, i)
            elif hasattr(s, "outputs"):
                self.link(s, 0, nd, i)
            else:
                nd.inputs[i].default_value = float(s)
        return nd

    def vmath(self, op, a, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, tuple):
                self.link(s[0], s[1], nd, i)
            elif hasattr(s, "outputs"):
                self.link(s, 0, nd, i)
            else:
                nd.inputs[i].default_value = s
        if scale is not None:
            nd.inputs[3].default_value = float(scale)
        return nd

    def comb(self, x, y, z=0.0):
        nd = self.n("ShaderNodeCombineXYZ")
        for i, s in enumerate((x, y, z)):
            if isinstance(s, tuple):
                self.link(s[0], s[1], nd, i)
            elif hasattr(s, "outputs"):
                self.link(s, 0, nd, i)
            else:
                nd.inputs[i].default_value = float(s)
        return nd

    def noise(self, vec, scale, detail=2.0, rough=0.5, dist=0.0, dim="3D"):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dim)
        nd.inputs["Scale"].default_value = float(scale)
        nd.inputs["Detail"].default_value = float(detail)
        nd.inputs["Roughness"].default_value = float(rough)
        nd.inputs["Distortion"].default_value = float(dist)
        if vec is not None:
            self.link(vec[0] if isinstance(vec, tuple) else vec,
                      vec[1] if isinstance(vec, tuple) else 0, nd, "Vector")
        return nd

    def voro(self, vec, scale, feature="SMOOTH_F1", smooth=0.85, rand=0.9,
             detail=0.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        nd.inputs["Scale"].default_value = float(scale)
        nd.inputs["Randomness"].default_value = float(rand)
        if "Smoothness" in nd.inputs:
            nd.inputs["Smoothness"].default_value = float(smooth)
        if "Detail" in nd.inputs:
            nd.inputs["Detail"].default_value = float(detail)
        if vec is not None:
            self.link(vec[0] if isinstance(vec, tuple) else vec,
                      vec[1] if isinstance(vec, tuple) else 0, nd, "Vector")
        return nd

    def mapr(self, src, f0, f1, t0, t1, clamp=True):
        nd = self.n("ShaderNodeMapRange", clamp=clamp)
        if isinstance(src, tuple):
            self.link(src[0], src[1], nd, 0)
        else:
            self.link(src, 0, nd, 0)
        nd.inputs["From Min"].default_value = float(f0)
        nd.inputs["From Max"].default_value = float(f1)
        nd.inputs["To Min"].default_value = float(t0)
        nd.inputs["To Max"].default_value = float(t1)
        return nd

    def mix(self, fac, a, b, data="FLOAT", clamp=False):
        nd = self.n("ShaderNodeMix", data_type=data, clamp_factor=True)
        fi = 0
        ai, bi = (6, 7) if data == "RGBA" else (2, 3)
        if data == "VECTOR":
            ai, bi = 4, 5
        for slot, s in ((fi, fac), (ai, a), (bi, b)):
            if s is None:
                continue
            if isinstance(s, tuple):
                self.link(s[0], s[1], nd, slot)
            elif hasattr(s, "outputs"):
                self.link(s, 0, nd, slot)
            elif isinstance(s, (list, tuple)):
                nd.inputs[slot].default_value = s
            else:
                try:
                    nd.inputs[slot].default_value = float(s)
                except TypeError:
                    nd.inputs[slot].default_value = s
        return nd

    def bump(self, height, dist, strength=1.0, normal=None, invert=False):
        nd = self.n("ShaderNodeBump", invert=invert)
        nd.inputs["Strength"].default_value = float(strength)
        nd.inputs["Distance"].default_value = float(dist)
        if isinstance(height, tuple):
            self.link(height[0], height[1], nd, "Height")
        else:
            self.link(height, 0, nd, "Height")
        if normal is not None:
            self.link(normal, "Normal", nd, "Normal")
        return nd


def mat_anodised():
    """The cassette's finish.  ~30 procedural texture nodes, five vertex
    channels, eight per-object constants, and not one image."""
    m = bpy.data.materials.get(MAT_NAME)
    if m is not None:
        return m
    m = bpy.data.materials.new(MAT_NAME)
    m.use_nodes = True
    b = MB(m)
    out = b.n("ShaderNodeOutputMaterial")
    bsdf = b.n("ShaderNodeBsdfPrincipled")
    b.link(bsdf, "BSDF", out, "Surface")

    # ---- 0. coordinates ---------------------------------------------------
    tc = b.n("ShaderNodeTexCoord")
    uvsep = b.n("ShaderNodeSeparateXYZ")
    b.link(tc, "UV", uvsep, 0)                 # sheet coords, metres
    obsep = b.n("ShaderNodeSeparateXYZ")
    b.link(tc, "Object", obsep, 0)             # panel-local 3D, metres
    su, sv = (uvsep, 0), (uvsep, 1)            # along / across the coil
    ob_v = (obsep, 1)                          # local vertical, metres

    # ---- 0b. the five vertex channels and the object constants ------------
    am = b.n("ShaderNodeAttribute", attribute_name=ATTR_M)
    amsep = b.n("ShaderNodeSeparateColor")
    b.link(am, "Color", amsep, 0)
    a_edge, a_skin, a_dep = (amsep, 0), (amsep, 1), (amsep, 2)
    a_dent = (am, "Alpha")
    aw = b.n("ShaderNodeAttribute", attribute_name=ATTR_W)
    a_weld = (aw, "Factor")
    tint = b.n("ShaderNodeAttribute", attribute_name="sfp_tint",
               attribute_type="OBJECT")
    p1 = b.n("ShaderNodeAttribute", attribute_name="sfp_p1",
             attribute_type="OBJECT")
    p1s = b.n("ShaderNodeSeparateXYZ")
    b.link(p1, "Vector", p1s, 0)
    gflip, imm, age = (p1s, 0), (p1s, 1), (p1s, 2)
    p2 = b.n("ShaderNodeAttribute", attribute_name="sfp_p2",
             attribute_type="OBJECT")
    p2s = b.n("ShaderNodeSeparateXYZ")
    b.link(p2, "Vector", p2s, 0)
    soil, rub, bloom = (p2s, 0), (p2s, 1), (p2s, 2)
    p3 = b.n("ShaderNodeAttribute", attribute_name="sfp_p3",
             attribute_type="OBJECT")
    p3s = b.n("ShaderNodeSeparateXYZ")
    b.link(p3, "Vector", p3s, 0)
    phase, rough0 = (p3s, 0), (p3s, 1)

    # the rolling direction: half the facade was cut with the grain across the
    # panel and half along it, because a 1.1 m panel comes out of a 1.5 m coil
    # either way and the fabricator nests for yield, not for looks.
    g_al = b.mix(gflip, su, sv)
    g_ac = b.mix(gflip, sv, su)

    # =====================================================================
    #  BUMP.  Coarse first; each stage feeds the next stage's Normal, so the
    #  chain composes instead of overwriting.  Amplitudes are in METRES and
    #  every one of them is under the 1 mm mesh frontier by construction.
    # =====================================================================
    # 1. the roll-forming ripple the brake did not take out: 40-90 mm, 60 um
    rip_v = b.comb(b.math("MULTIPLY", g_al, 11.0), b.math("MULTIPLY", g_ac, 2.2))
    rip = b.noise(rip_v, 1.0, detail=2.0, rough=0.45)
    nrm = b.bump(rip, 0.000060, 1.0)
    # 2. THE STUCCO EMBOSS.  7 mm pillows, 0.22 mm deep, which is the single
    #    loudest thing on this surface at 3.6 m: 7.3 px across, and its lip and
    #    its shadow are 3.6 px apart, which is exactly the scale a 12.5 deg sun
    #    reads on a wall at 31-56 deg of incidence.
    emb_v = b.comb(su, sv, 0.0)
    emb = b.voro(emb_v, 138.0, "SMOOTH_F1", smooth=0.72, rand=0.88)
    # PILLOW UP, VALLEY AT THE CELL BOUNDARY.  Voronoi's distance is 0 at the
    # seed and rises to the boundary, so feeding it to the bump raw would emboss
    # the sheet inside out -- ridges along the cell walls and a pit at every
    # centre.  A rolled emboss is the other way round, and the flipped field is
    # ALSO what the dirt needs: airborne soil settles in the valleys and the
    # rain never scrubs them, which is where this surface gets its micro
    # contrast from.  Without it the 1:1 crop is milky: pale everywhere, dark
    # nowhere.
    # THE MAP RANGE IS A MEASUREMENT, NOT A GUESS.  Rendered and measured on a
    # 400 px probe plane (work/sfp2/field_probe2.py): this Voronoi's Distance
    # output runs 0.03..1.01 with a MEDIAN OF 0.486, so the first version of this
    # line -- From 0.04..0.46 -- clamped more than half the sheet to zero and the
    # emboss did not exist over most of the panel.  That single wrong band is
    # what the gate measured as "no lip and no lee shadow": with the emboss
    # clamped flat, the only fine structure left on the surface was the 30:1
    # horizontally-stretched rolling grain, which correlates ALONG the light and
    # drove the relief dip to -0.127.  0.18..0.80 covers p01..p99 of the real
    # field.
    emb_h = b.mapr((emb, "Distance"), 0.18, 0.80, 1.0, 0.0)
    emb_valley = b.math("SUBTRACT", 1.0, emb_h)
    nrm = b.bump(emb_h, 0.00030, 1.0, normal=nrm)
    # 3. the peen generation nested inside it: 2.6 mm, 70 um
    emb2 = b.voro(emb_v, 385.0, "SMOOTH_F1", smooth=0.55, rand=0.95)
    nrm = b.bump((emb2, "Distance"), 0.000070, 1.0, normal=nrm)
    # 4. the etch: caustic etching leaves a 1.2 mm mottle 18 um deep
    etch = b.noise(emb_v, 830.0, detail=3.0, rough=0.55)
    nrm = b.bump(etch, 0.000032, 1.0, normal=nrm)
    # 5. the rolling grain: 0.15 mm across, 5 mm long, 12 um -- this is what
    #    makes the sheen anisotropic in the image and not just in the BSDF
    gr_v = b.comb(b.math("MULTIPLY", g_al, 260.0),
                  b.math("MULTIPLY", g_ac, 2600.0))
    grain = b.noise(gr_v, 1.0, detail=1.0, rough=0.5)
    nrm = b.bump(grain, 0.0000055, 1.0, normal=nrm)
    # 6. oxide crazing on the OUTSIDE of every fold: the film is 22 um of
    #    ceramic and a 4.5 mm bend radius stretches it past its elastic limit,
    #    so it micro-cracks in a band about 3 mm wide either side of the apex
    craze_m = b.mapr(b.math("ABSOLUTE", a_edge), 0.0005, 0.0040, 1.0, 0.0)
    craze = b.noise(b.comb(b.math("MULTIPLY", su, 2400.0),
                           b.math("MULTIPLY", sv, 2400.0)), 1.0, detail=2.0)
    craze_h = b.math("MULTIPLY", craze, craze_m)
    nrm = b.bump(craze_h, 0.000030, 1.0, normal=nrm)
    b.link(nrm, "Normal", bsdf, "Normal")

    # =====================================================================
    #  COLOUR.  Base tint per anodising load, then history.  NOTHING here is
    #  louder than +-4 % except a named deposit, because v1's mottle at +-12 %
    #  read as dirty fibre-cement rather than as metal.
    # =====================================================================
    # 7. RACK STREAKS.  The load hangs from titanium racks and the current
    #    density falls with distance from the contact, so the finish carries
    #    vertical bands 40-120 mm wide.  +-3 %.
    rack = b.noise(b.comb(b.math("ADD", b.math("MULTIPLY", su, 11.0), phase),
                          b.math("MULTIPLY", sv, 0.35)), 1.0, detail=1.5)
    rack_f = b.mapr(rack, 0.28, 0.72, -0.030, 0.030, clamp=True)
    # 8. THE IMMERSION LINE.  Where the panel hung at the surface of the tank
    #    there is a 4 mm tide line, 3 % brighter, slightly rougher.
    tide_d = b.math("ABSOLUTE", b.math("SUBTRACT", ob_v, imm))
    tide = b.mapr(tide_d, 0.0020, 0.0060, 1.0, 0.0)
    # 9. etch cloudiness, 40-150 mm, +-1.5 %
    cloud = b.noise(b.comb(b.math("MULTIPLY", su, 9.0),
                           b.math("MULTIPLY", sv, 9.0)), 1.0, detail=3.0,
                    rough=0.6)
    cloud_f = b.mapr(cloud, 0.3, 0.7, -0.015, 0.015)
    lum = b.math("ADD", rack_f, cloud_f)
    lum = b.math("ADD", lum, b.math("MULTIPLY", tide, 0.030))
    # 10. SEALING BLOOM.  A load that came out of the sealing tank cold gets
    #     chalky patches 15-40 mm across: brighter, much rougher, and only on
    #     the panels the flag says.
    bl = b.voro(b.comb(b.math("MULTIPLY", su, 34.0),
                       b.math("MULTIPLY", sv, 34.0)), 1.0, "F1", rand=1.0)
    bl_m = b.math("MULTIPLY", b.mapr((bl, "Distance"), 0.16, 0.40, 1.0, 0.0), bloom)
    lum = b.math("ADD", lum, b.math("MULTIPLY", bl_m, 0.014))
    # 11. RAIN.  Water sheets off the top arris and runs down in a comb of
    #     streaks 8-30 mm apart: the streak lines are washed CLEAN and their
    #     edges carry the soil the water pushed aside.  Only on the outer skin,
    #     and it fades out 250 mm below the arris where the sheet is still wet
    #     enough to run rather than to dry.
    comb_n = b.noise(b.comb(b.math("MULTIPLY", su, 62.0),
                            b.math("MULTIPLY", sv, 1.1)), 1.0, detail=2.5)
    down = b.mapr(ob_v, 0.30, -0.45, 0.0, 1.0)
    wash = b.math("MULTIPLY", b.mapr(comb_n, 0.44, 0.66, 0.0, 1.0), down)
    wash = b.math("MULTIPLY", wash, a_skin)
    # 12. ATMOSPHERIC SOIL: brake dust and diesel soot, which arrive from the
    #     paddock side and stick where the rain does not reach -- in the joint,
    #     under the arris, and in the lee of every rivet.
    dirt_n = b.noise(b.comb(b.math("MULTIPLY", su, 26.0),
                            b.math("MULTIPLY", sv, 26.0)), 1.0, detail=4.0,
                     rough=0.62)
    cav = b.mapr(a_dep, 0.004, 0.030, 0.0, 1.0)
    dirt = b.math("ADD", b.math("MULTIPLY", wash, 0.55),
                  b.math("MULTIPLY", cav, 0.85))
    dirt = b.math("MULTIPLY", dirt, b.math("MULTIPLY", dirt_n, 1.35))
    dirt = b.math("MULTIPLY", dirt, soil, clamp=True)
    # the same soil, concentrated where it physically collects: in the emboss
    # valleys.  0.35 stays on the pillow tops, 1.00 sits in the valley floors.
    dirt = b.math("MULTIPLY", dirt,
                  b.math("ADD", 0.35, b.math("MULTIPLY", emb_valley, 1.05)),
                  clamp=True)
    # and a floor of it everywhere, because a facade six months out of its
    # protective film is not clean anywhere
    dirt = b.math("ADD", dirt, b.math("MULTIPLY", b.math("MULTIPLY", emb_valley,
                                                         a_skin), 0.085))
    # 13. MINERAL SPOTTING.  Hard water dries in 4-9 mm rings that are chalky,
    #     rough and slightly LIGHTER than the metal, concentrated low down.
    spot = b.voro(b.comb(b.math("MULTIPLY", su, 190.0),
                         b.math("MULTIPLY", sv, 190.0)), 1.0, "F1", rand=1.0)
    # measured median 0.519, so From 0.33..0.42 -> To 0..1 clamped ~65 % of the
    # sheet to a full-strength "spot".  A drying droplet is 1-4 mm at the CELL
    # CENTRE, which is the low end of the distance field, not the high end.
    ring = b.mapr((spot, "Distance"), 0.06, 0.24, 1.0, 0.0)
    ring = b.math("MULTIPLY", ring, b.mapr(ob_v, 0.10, -0.50, 0.10, 1.0))
    ring = b.math("MULTIPLY", ring, a_skin)
    # they CLUSTER, in the paths water actually took, instead of dusting the
    # whole panel like confetti -- which is what an unmasked Voronoi does
    ring = b.math("MULTIPLY", ring, b.mapr(
        b.noise(b.comb(b.math("MULTIPLY", su, 5.5),
                       b.math("MULTIPLY", sv, 7.5)), 1.0, detail=2.0),
        0.58, 0.76, 0.0, 1.0))
    lum = b.math("ADD", lum, b.math("MULTIPLY", ring, 0.016))
    # 14. the dressed dent: the fitter's dolly burnishes the crater, so it is
    #     smoother and a shade brighter than the sheet round it
    lum = b.math("ADD", lum, b.math("MULTIPLY", a_dent, 0.018))
    # 15. the fold: stretched film is THINNER, so the arris is brighter
    lum = b.math("ADD", lum, b.math("MULTIPLY", craze_m, 0.026))
    # 16. the corner cassette's dressed weld: ground back, so it has no grain
    #     and it takes the anodising differently -- 1.5 % darker, much rougher
    lum = b.math("SUBTRACT", lum, b.math("MULTIPLY", a_weld, 0.015))
    # 17. the cavity side of the tray is not weathered at all, just dusty
    lum = b.math("SUBTRACT", lum,
                 b.math("MULTIPLY", b.math("SUBTRACT", 1.0, a_skin), 0.05))
    bright = b.math("ADD", 1.0, lum)
    scale = b.n("ShaderNodeVectorMath", operation="SCALE")
    b.link(tint, "Vector", scale, 0)
    b.link(bright, 0, scale, 3)
    # the soil is a warm grey-brown, mixed OVER the metal
    soil_col = b.mix(dirt_n, [0.10, 0.087, 0.074, 1.0],
                     [0.155, 0.132, 0.108, 1.0], data="RGBA")
    final_col = b.mix(dirt, scale, soil_col, data="RGBA")
    b.link(final_col, "Result", bsdf, "Base Color")

    # =====================================================================
    #  ROUGHNESS AND METALLIC.  Every deposit above appears here too: that is
    #  what separates a deposit from a painted mark.
    # =====================================================================
    rg = b.math("ADD", rough0, b.mapr(etch, 0.35, 0.65, -0.030, 0.030))
    rg = b.math("ADD", rg, b.mapr(grain, 0.3, 0.7, -0.020, 0.020))
    rg = b.math("ADD", rg, b.math("MULTIPLY", dirt, 0.190))
    rg = b.math("ADD", rg, b.math("MULTIPLY", ring, 0.150))
    rg = b.math("ADD", rg, b.math("MULTIPLY", bl_m, 0.070))
    rg = b.math("ADD", rg, b.math("MULTIPLY", craze_m, 0.075))
    rg = b.math("ADD", rg, b.math("MULTIPLY", a_weld, 0.140))
    rg = b.math("ADD", rg, b.math("MULTIPLY", tide, 0.045))
    # the dolly burnishes; the installers' hands polish the lower arris
    rg = b.math("SUBTRACT", rg, b.math("MULTIPLY", a_dent, 0.070))
    hand = b.math("MULTIPLY", rub, b.mapr(ob_v, -0.55, -0.32, 1.0, 0.0))
    hand = b.math("MULTIPLY", hand, b.mapr(
        b.noise(b.comb(b.math("MULTIPLY", su, 19.0),
                       b.math("MULTIPLY", sv, 19.0)), 1.0, detail=2.0),
        0.45, 0.62, 0.0, 1.0))
    rg = b.math("SUBTRACT", rg, b.math("MULTIPLY", hand, 0.075))
    rg = b.math("ADD", rg, b.math("MULTIPLY",
                                  b.math("SUBTRACT", 1.0, a_skin), 0.140))
    rg = b.math("MAXIMUM", b.math("MINIMUM", rg, 0.78), 0.17)
    b.link(rg, 0, bsdf, "Roughness")

    # METALLIC.  0.86 and not 1.0, and this is the single most consequential
    # number in the file.  Sealed porous alumina is a 22 um ceramic layer that
    # scatters: an anodised panel is READABLE off-specular, which is the entire
    # reason the finish is specified for a facade.  At metallic 1.0 the BSDF has
    # no cos(incidence) term at all, so no bump under it can make a sunward lip
    # or a lee shadow, and v1 of this item was rejected for precisely that.
    # Dust is a dielectric, so soil takes it down further.
    met = b.math("SUBTRACT", 0.865, b.math("MULTIPLY", dirt, 0.34))
    met = b.math("SUBTRACT", met, b.math("MULTIPLY", ring, 0.22))
    met = b.math("SUBTRACT", met, b.math("MULTIPLY", bl_m, 0.10))
    met = b.math("MAXIMUM", met, 0.30)
    b.link(met, 0, bsdf, "Metallic")

    # ANISOTROPY, aligned to the coil, killed where the weld was ground and
    # damped where the surface is dirty.
    ani = b.math("MULTIPLY", 0.16, b.math("SUBTRACT", 1.0, a_weld))
    ani = b.math("MULTIPLY", ani, b.math("SUBTRACT", 1.0,
                                         b.math("MULTIPLY", dirt, 0.7)))
    b.link(ani, 0, bsdf, "Anisotropic")
    arot = b.math("MULTIPLY", gflip, 0.25)
    b.link(arot, 0, bsdf, "Anisotropic Rotation")
    bsdf.inputs["IOR"].default_value = 1.62          # alumina
    return m


def _simple(name, base, rough, metal, scale, aniso=0.0, detail=3.0):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = MB(m)
    out = b.n("ShaderNodeOutputMaterial")
    bsdf = b.n("ShaderNodeBsdfPrincipled")
    b.link(bsdf, "BSDF", out, "Surface")
    tc = b.n("ShaderNodeTexCoord")
    n1 = b.noise((tc, "Object"), scale, detail=detail, rough=0.55)
    n2 = b.noise((tc, "Object"), scale * 7.5, detail=2.0)
    col = b.mix(b.mapr(n1, 0.35, 0.65, 0.0, 1.0),
                [base[0] * 0.86, base[1] * 0.86, base[2] * 0.86, 1.0],
                [min(1.0, base[0] * 1.12), min(1.0, base[1] * 1.12),
                 min(1.0, base[2] * 1.12), 1.0], data="RGBA")
    b.link(col, "Result", bsdf, "Base Color")
    rg = b.math("ADD", rough, b.mapr(n2, 0.3, 0.7, -0.09, 0.09))
    b.link(rg, 0, bsdf, "Roughness")
    bsdf.inputs["Metallic"].default_value = float(metal)
    if aniso:
        bsdf.inputs["Anisotropic"].default_value = float(aniso)
    nrm = b.bump(n2, 0.00025, 1.0)
    b.link(nrm, "Normal", bsdf, "Normal")
    return m


def materials():
    """[anodised, dark, epdm, mill, mesh] in MAT_* order."""
    return [
        mat_anodised(),
        _simple(PFX + "Plenum", (0.020, 0.020, 0.021), 0.72, 0.0, 90.0),
        _simple(PFX + "EPDM", (0.030, 0.030, 0.031), 0.62, 0.0, 260.0),
        _simple(PFX + "Mill", (0.660, 0.660, 0.655), 0.44, 0.90, 150.0,
                aniso=0.30),
        _simple(PFX + "Mesh", (0.560, 0.558, 0.552), 0.38, 0.92, 320.0),
    ]


# ===========================================================================
# 10.  EMIT.
# ===========================================================================
def emit_panels(coll=None, only=None, limit=None, log=print):
    mats = materials()
    coll = coll or _coll(COLL_NAME)
    ps = panel_list()
    if only:
        ps = [p for p in ps if p.name in set(only) or p.kind in set(only)]
    if limit:
        ps = ps[:limit]
    t0 = time.time()
    tot_tris = 0
    for i, p in enumerate(ps):
        V, UV, A, W, faces = build_cassette(p)
        me = make_mesh(p.name, V, UV, A, W, faces, mats)
        ob = bpy.data.objects.new(p.name, me)
        M = panel_matrix(p)
        ob.matrix_world = Matrix([list(M[r]) for r in range(4)])
        bake_object_attrs(ob, p)
        coll.objects.link(ob)
        tot_tris += sum(len(pl.vertices) - 2 for pl in me.polygons)
        if (i + 1) % 20 == 0:
            log("   %3d/%d panels  %.1f s  %.2f M tris"
                % (i + 1, len(ps), time.time() - t0, tot_tris / 1e6))
    log(">> %d cassettes, %.2f M triangles, %.1f s"
        % (len(ps), tot_tris / 1e6, time.time() - t0))
    return coll


def emit_carrier(coll=None):
    """The T-rails and the EPDM baffles BEHIND the open joints.

    A 15 mm joint 90 mm deep is only black if something is in there to be
    black.  These are prefixed differently from the cassettes so the gate
    measures the item and not its substructure -- SFP_Rail_ / SFP_Baffle_.
    """
    mats = materials()
    coll = coll or _coll(COLL_NAME)
    ps = panel_list()
    out = []
    zc = 0.5 * (CLAD_TOP_Z + CLAD_BOT_Z)

    def place(name, acc, elev, mid):
        V, UV, A, W, faces = acc.finish()
        me = make_mesh(name, V, UV, A, W, faces, mats)
        ob = bpy.data.objects.new(name, me)
        u, v, w = (np.asarray(a, float) for a in elev_axes(elev))
        M = np.eye(4)
        M[:3, 0] = u; M[:3, 1] = v; M[:3, 2] = w
        M[:3, 3] = face_origin(elev) + u * mid + v * zc
        ob.matrix_world = Matrix([list(M[r]) for r in range(4)])
        coll.objects.link(ob)
        out.append(ob)
        return ob

    for elev in ("E", "S"):
        lo = min(p.s0 for p in ps if p.elev == elev)
        hi = max(p.s1 for p in ps if p.elev == elev)
        mid = 0.5 * (lo + hi)
        S = np.linspace(lo - mid, hi - mid, max(4, int((hi - lo) / 0.25)))
        # -- a T-rail on every course line, 60 mm behind the face -----------
        for ci, (ztop, hgt) in enumerate(COURSES):
            acc = Acc()
            vline = ztop - zc
            prof = [(-0.032, -RAIL_D), (0.032, -RAIL_D), (0.032, -RAIL_D + 0.004),
                    (0.004, -RAIL_D + 0.004), (0.004, -0.026), (-0.004, -0.026),
                    (-0.004, -RAIL_D + 0.004), (-0.032, -RAIL_D + 0.004)]
            rows = []
            for (dv, dw) in prof:
                b = acc.add(S, np.full(S.shape, vline + dv),
                            np.full(S.shape, dw), S, vline + dv,
                            -0.09, 0.0, 0.055, 0.0, 0.0)
                rows.append(b + np.arange(S.size))
            for a_, b_ in zip(rows, rows[1:] + rows[:1]):
                acc.strip(a_, b_, MAT_MILL, False, closed=False)
            place("%s%s%d" % (RAIL_PFX, elev, ci), acc, elev, mid)
        # -- one black EPDM baffle sheet per elevation, behind every joint ---
        acc = Acc()
        UU, VV = np.meshgrid(np.array([S[0], S[-1]]),
                             np.array([CLAD_BOT_Z - zc - 0.02,
                                       CLAD_TOP_Z - zc + 0.02]), indexing="ij")
        # 75 mm back, which is BEHIND the hooks (53 mm) and behind the rail's
        # own base (60 mm).  At 30 mm it was in front of both and the hooks
        # poked through it: a solid sheet with brackets growing out of it.
        b = acc.add(UU, VV, np.full(UU.shape, -0.075), UU, VV, -0.09, 0.0,
                    0.075, 0.0, 0.0)
        acc.grid_quads(b + np.arange(4).reshape(2, 2), MAT_EPDM, False)
        place("%s%s" % (BAFFLE_PFX, elev), acc, elev, mid)
    return out


def build(scene=None, only=None, limit=None, carrier=True, log=print):
    """THE ENTRY POINT.  Emits every cassette into COLL_NAME and returns it."""
    root = _coll(COLL_NAME)
    emit_panels(root, only=only, limit=limit, log=log)
    if carrier:
        emit_carrier(root)
    return root


# ===========================================================================
# 11.  LIGHT AND CONTEXT.  The contract sun, and standins that are honest
#      about being standins (CTX_, which the gate excludes by name).
# ===========================================================================
def contract_light(scene=None, coll=None):
    """C.SUN_*: 12.471 deg elevation on a bearing of -57.970 deg.

    On the EAST face that is 31.2 deg above the surface (cos i = 0.518); on the
    SOUTH face 55.9 deg (cos i = 0.828).  Both elevations are in direct sun in
    the film, which is why this item is read by its relief and not only by its
    reflection.
    """
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
    return ob


def _ctx_box(coll, name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new("CTX_" + name)
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(V, [], F)
    me.materials.append(mat)
    ob = bpy.data.objects.new("CTX_" + name, me)
    coll.objects.link(ob)
    return ob


def build_context(coll):
    """What the cassettes are hung on and what they see.

    NOT the coping, NOT the lettering, NOT the pipes -- those are three other
    manifest items and building them here would be building them twice.  This
    is the wall behind, the head of the curtain wall below, a sliver of glass
    for something to reflect, and the forecourt at z = C.APRON_Z, because a
    facade lit with no ground bounce is a facade nobody has ever seen.
    """
    m_wall = _simple("CTX_Wall", (0.185, 0.180, 0.172), 0.86, 0.0, 22.0)
    m_soff = _simple("CTX_Soffit", (0.520, 0.515, 0.505), 0.74, 0.0, 14.0)
    m_grd = _simple("CTX_Forecourt", (0.205, 0.202, 0.196), 0.88, 0.0, 26.0)
    m_gl = bpy.data.materials.new("CTX_Glass")
    m_gl.use_nodes = True
    gb = next(n for n in m_gl.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gb.inputs["Base Color"].default_value = (0.78, 0.86, 0.83, 1.0)
    gb.inputs["Roughness"].default_value = 0.02
    gb.inputs["Metallic"].default_value = 0.0
    gb.inputs["Transmission Weight"].default_value = 0.92
    gb.inputs["IOR"].default_value = 1.52
    # the wall the rails are fixed to: 130 mm behind the set-out plane
    _ctx_box(coll, "WallE", CLAD_X_E - 0.400, CLAD_X_E - 0.130,
             CLAD_Y_S - 0.130, CLAD_Y_N, CLAD_BOT_Z - 0.35, PARAPET_TOP_Z, m_wall)
    _ctx_box(coll, "WallS", CLAD_X_W, CLAD_X_E - 0.130,
             CLAD_Y_S - 0.130, CLAD_Y_S + 0.140, CLAD_BOT_Z - 0.35,
             PARAPET_TOP_Z, m_wall)
    # the head of the curtain wall, and glass below it
    _ctx_box(coll, "HeadE", CLAD_X_E - 0.150, CLAD_X_E + 0.010,
             CLAD_Y_S, CLAD_Y_N, GLASS_HEAD_Z, HEAD_TOP_Z, m_soff)
    _ctx_box(coll, "GlassE", CLAD_X_E - 0.012, CLAD_X_E - 0.001,
             CLAD_Y_S, CLAD_Y_N, GLASS_HEAD_Z - 3.2, GLASS_HEAD_Z, m_gl)
    _ctx_box(coll, "HeadS", CLAD_X_W, CLAD_X_E,
             CLAD_Y_S - 0.010, CLAD_Y_S + 0.150, GLASS_HEAD_Z, HEAD_TOP_Z,
             m_soff)
    # a MINIMAL parapet: the coping is showroom_parapet_coping's job, so this is
    # only the upstand behind the top course, stopped 6 mm below the bearing.
    _ctx_box(coll, "Upstand", CLAD_X_E - 0.360, CLAD_X_E - 0.130,
             CLAD_Y_S - 0.130, CLAD_Y_N, PARAPET_TOP_Z - 0.06, PARAPET_TOP_Z,
             m_wall)
    _ctx_box(coll, "Forecourt", CLAD_X_E - 2.0, CLAD_X_E + 26.0,
             CLAD_Y_S - 26.0, CLAD_Y_N + 8.0, C.APRON_Z - 0.06, C.APRON_Z, m_grd)
    return coll


def add_camera(name, loc, aim, lens, coll, fstop=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = float(lens)
    cd.sensor_width = SENSOR_MM
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.005
    cd.clip_end = 2000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = tuple(float(v) for v in loc)
    d = Vector(tuple(float(v) for v in aim)) - Vector(ob.location)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    print("   %-22s %.4f m on %.0f mm" % (name, float(d.length), lens))
    return ob


def _cam_polar(name, aim, dist, az_deg, el_deg, lens, coll, elev="E",
               fstop=None):
    """A camera EXACTLY `dist` from `aim`, `az` off the elevation's own outward
    normal in plan and `el` above the horizontal.  The manifest's distance is a
    distance, not an approximation."""
    u, v, w = (np.asarray(a, float) for a in elev_axes(elev))
    a = math.radians(az_deg)
    e = math.radians(el_deg)
    d = (w * math.cos(e) * math.cos(a) + u * math.cos(e) * math.sin(a)
         + v * math.sin(e))
    loc = np.asarray(aim, float) + dist * d
    return add_camera(name, loc, aim, lens, coll, fstop)


def test_scene(samples=256, limit=None, carrier=True):
    """180 cassettes on the two elevations the film sees, the contract sun, and
    the manifest's own camera at EXACTLY 3.600 m on EXACTLY a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    root = build(scene=scene, limit=limit, carrier=carrier)
    cams = _coll(COLL_NAME + "_Cameras", root)
    ctx = _coll(COLL_NAME + "_Standins", root)
    contract_light(scene, coll=ctx)
    build_context(ctx)

    # ---- THE SHOT.  3.600 m, 35 mm, on the east elevation, 38 deg off the
    # face normal to the NORTH.  That side and not the south side because the
    # contract sun bears -57.97 deg: from the north-east the light rakes across
    # the emboss and the joints at 96 deg in plan, which is what a raked metal
    # facade is FOR.  From the south-east it would be 26 deg off the view axis,
    # frontal, and the surface would go flat -- the same mistake the gate's own
    # staging note describes.
    aim = np.array([CLAD_X_E, 1.10, 8.62])
    _cam_polar(CAM_PFX + "MACRO", aim, FILMED_AT_M, 38.0, 7.0, LENS_MM,
               cams, "E")
    # the joint, dead on: 15 mm wide, 90 mm deep, a lit top arris and a black
    # bottom.  Same distance, longer lens, because this is a detail check and
    # not the shot.
    _cam_polar(CAM_PFX + "JOINT", np.array([CLAD_X_E, 0.55, 8.53]),
               FILMED_AT_M, 30.0, 3.0, 85.0, cams, "E")
    # the corner cassette's mitred arris -- the gate's own subject
    _cam_polar(CAM_PFX + "CORNER",
               np.array([CLAD_X_E - 0.30, CLAD_Y_S - 0.02, 8.60]),
               FILMED_AT_M, -46.0, 6.0, LENS_MM, cams, "S")
    # the louvre group, north end of the east run
    _cam_polar(CAM_PFX + "LOUVRE", np.array([CLAD_X_E, 6.60, 8.55]),
               FILMED_AT_M, 26.0, 4.0, LENS_MM, cams, "E")
    # the perforated spandrel
    _cam_polar(CAM_PFX + "PERF", np.array([CLAD_X_E, 6.05, 9.75]),
               FILMED_AT_M, 24.0, -6.0, LENS_MM, cams, "E")
    # the drip course from below, which is where Beat 4's camera actually is
    _cam_polar(CAM_PFX + "SOFFIT", np.array([CLAD_X_E, 2.20, 6.42]),
               FILMED_AT_M, 30.0, -32.0, LENS_MM, cams, "E")
    # the whole fascia, to see whether 180 panels read as 180 panels
    add_camera(CAM_PFX + "WIDE", (CLAD_X_E + 21.0, -20.0, 12.5),
               (CLAD_X_E - 3.0, -2.0, 8.4), 50.0, cams)
    # Beat 6: the manifest says this fascia is 33 px tall in the held frame.
    # If the panel rhythm dies at that scale the building loses its scale.
    add_camera(CAM_PFX + "BEAT6", (CLAD_X_E + 560.0, -180.0, 34.0),
               (CLAD_X_E, 0.0, 8.4), 85.0, cams)
    scene.camera = bpy.data.objects[CAM_PFX + "MACRO"]
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.005
    scene.cycles.max_bounces = 14
    scene.cycles.diffuse_bounces = 5
    scene.cycles.glossy_bounces = 8
    scene.cycles.transmission_bounces = 10
    scene.cycles.use_denoising = True
    return root


def save_clean(path):
    """Save, and REFUSE if any external image dependency survived."""
    bad = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if bad:
        raise SystemExit("REFUSING TO SAVE: external images %s" % bad)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path),
                                relative_remap=False, compress=True)
    print(">> saved %s (%.1f MB), 0 external deps"
          % (path, os.path.getsize(path) / 1048576.0))
    return path


# ===========================================================================
# 12.  THE INTERFACE THE DEPENDANTS READ.
# ===========================================================================
def clad_top_edge_z(elev, s):
    """As-built z of the top course's top edge at station s.

    The coping's bearing is nominally 10.340 and the as-built edge moves with
    the panel's shim stack and installed tilt.  A coping laid dead flat WILL
    rock; read this and pack it.
    """
    best, bd = None, 1e9
    for p in panel_list():
        if p.course != 0 or (p.elev != elev and p.elev != "C"):
            continue
        d = abs(0.5 * (p.s0 + p.s1) - s)
        if d < bd:
            best, bd = p, d
    if best is None:
        return (CLAD_TOP_Z, None)
    return (round(0.5 * (best.z0 + best.z1) + best.off_v + 0.5 * best.h, 6),
            best.name)


def top_edge_range():
    """(min, max, peak-to-peak mm) of the AS-BUILT coping bearing.  A cassette
    hangs on two hooks and the hook engagement is a fabrication dimension, so
    the top edge sits where the hook puts it."""
    zs = [0.5 * (p.z0 + p.z1) + p.off_v + 0.5 * p.h
          for p in panel_list() if p.course == 0]
    return (round(min(zs), 6), round(max(zs), 6),
            round((max(zs) - min(zs)) * 1000.0, 3))


def joint_map():
    """Every vertical joint's as-built width, and how much it opens down its
    length.  This is variation axis 3, measured rather than claimed."""
    out = []
    ps = panel_list()
    for elev in ("E", "S"):
        for ci in range(len(COURSES)):
            row = sorted([p for p in ps if p.elev == elev and p.course == ci],
                         key=lambda q: q.s0)
            for a, b in zip(row[:-1], row[1:]):
                # AS BUILT: each panel is its own cut width set out off its own
                # laser line, so the gap is whatever is left between two of them.
                ea = 0.5 * (a.s0 + a.s1) + a.off_u + 0.5 * a.w
                eb = 0.5 * (b.s0 + b.s1) + b.off_u - 0.5 * b.w
                gap = eb - ea
                # and the two lean by different amounts about their own vertical
                # axis, so the gap is a WEDGE in DEPTH down its length
                wa = 0.5 * a.w * math.tan(a.tilt_v)
                wb = 0.5 * b.w * math.tan(b.tilt_v)
                out.append(dict(elev=elev, course=ci, s=round(ea, 5),
                                nominal_m=JOINT_M, as_built_m=round(gap, 5),
                                a=a.name, b=b.name,
                                depth_wedge_mm=round(abs(wb - wa) * 1000.0, 3),
                                face_step_mm=round((b.off_w - a.off_w) * 1000.0, 3)))
    return out


def sign_fix_grid():
    """600 candidate fixings for showroom_signage_lettering.

    Every point is on a panel with a bonded backing plate, at least 40 mm from
    any joint, and returns the AS-BUILT face position -- not the set-out plane.
    """
    out = []
    for p in panel_list():
        if p.kind != "signback":
            continue
        plan, Wd = panel_plan(p)
        stiff = None
        for i in range(10):
            for j in range(10):
                u = 0.10 * Wd + 0.80 * Wd * (i + 0.5) / 10.0
                v = -0.34 * p.h + 0.68 * p.h * (j + 0.5) / 10.0
                if min(u, Wd - u) < 0.040 or (0.5 * p.h - abs(v)) < 0.040:
                    continue
                ns = max(1, p.n_stiff)
                sv = [(-0.5 * p.h + (q + 1) * p.h / (ns + 1)) for q in range(ns)]
                w = float(plate_w(p, np.array([u]), np.array([v]), Wd, sv)[0])
                pos = np.asarray(panel_origin(p)) + \
                    np.asarray(elev_axes(p.elev)[0]) * (u - 0.5 * Wd) + \
                    np.asarray(elev_axes(p.elev)[1]) * v + \
                    np.asarray(elev_axes(p.elev)[2]) * w
                out.append([round(float(pos[0]), 4), round(float(pos[1]), 4),
                            round(float(pos[2]), 4), p.name])
    return out


def rwp_lines():
    """The three downpipe stations.  Each is a 90 mm RECESSED COLUMN of
    cassettes -- the pipe sits behind the cladding plane, and the brackets go
    on the carrier rails, never into a cassette."""
    out = []
    for elev, s in RWP_STATIONS:
        col = [p.name for p in panel_list() if p.kind == "rwp"
               and p.elev == elev and abs(0.5 * (p.s0 + p.s1) - s) < 0.75]
        if not col:
            continue
        br = []
        for ci, (ztop, hgt) in enumerate(COURSES):
            br.append([round(v, 4) for v in face_point(elev, s, ztop - 0.004)]
                      + [elev])
        out.append(dict(elev=elev, s=round(s, 3), dia=0.100,
                        reveal_depth=REVEAL_DEPTH,
                        recess_face_z_range=[CLAD_BOT_Z, CLAD_TOP_Z],
                        panels=sorted(col), bracket_points=br,
                        hopper=[round(v, 4) for v in
                                face_point(elev, s, CLAD_TOP_Z - 0.20)]))
    return out


def _joint_stats():
    jm = joint_map()
    j = [q["as_built_m"] for q in jm]
    w = [q["depth_wedge_mm"] for q in jm]
    return dict(n=len(j), nominal_mm=JOINT_M * 1000,
                min_mm=round(min(j) * 1000, 3), max_mm=round(max(j) * 1000, 3),
                mean_mm=round(float(np.mean(j)) * 1000, 3),
                sd_mm=round(float(np.std(j)) * 1000, 3),
                wedge_max_mm=round(max(w), 3))


def write_interface(path=None):
    ps = panel_list()
    d = dict(
        item=ITEM, version=__version__, seed=SEED,
        generated_by="world/items/%s.py" % ITEM,
        frame="WORLD metres; z = 0.000 = C.APRON_Z = the showroom floor",
        px_per_m_at_3p6m=round(PX_PER_M, 2),
        planes=dict(clad_x_e=CLAD_X_E, clad_y_s=CLAD_Y_S, clad_y_n=CLAD_Y_N,
                    clad_x_w=CLAD_X_W, breach_plane_x=BREACH_X,
                    clad_top_z=CLAD_TOP_Z, clad_bottom_z=CLAD_BOT_Z,
                    parapet_top_z=PARAPET_TOP_Z, coping_bearing_z=CLAD_TOP_Z,
                    head_top_z=HEAD_TOP_Z, glass_head_z=GLASS_HEAD_Z),
        setout=dict(module_m=MODULE_M, mullion_pitch=2.2, joint_m=JOINT_M,
                    courses=[[c[0], c[0] - c[1], c[1]] for c in COURSES],
                    corner_leg_e=CORNER_LEG_E, corner_leg_s=CORNER_LEG_S,
                    panels_per_course=len(ps) // len(COURSES),
                    total_panels=len(ps)),
        fabrication=dict(sheet_t=SHEET_T,
                         fold_r_out=[f["fold_r"] for f in FAB],
                         return_d=[f["ret_d"] for f in FAB],
                         lip_l=[f["lip_l"] for f in FAB],
                         drip_return_d=DRIP_RET_D, reveal_depth=REVEAL_DEPTH,
                         rivet_r_flange=RIVET_FLANGE_R, rivet_h=RIVET_DOME_H),
        face_clearance=dict(E=face_clearance("E"), S=face_clearance("S")),
        as_built=dict(MEASURED),
        material=dict(name=MAT_NAME,
                      reads_uv="DEVELOPED SHEET metres (UVMap)",
                      reads_object="panel-local metres",
                      vertex_attrs={ATTR_M: "FLOAT_COLOR (edge_m, outer_skin,"
                                            " depth_m, dent)",
                                    ATTR_W: "FLOAT weld/arris proximity"},
                      object_attrs=["sfp_tint", "sfp_p1(gflip,imm_v,age)",
                                    "sfp_p2(soil,rub,bloom)",
                                    "sfp_p3(phase,rough,course)"],
                      note="call bake_object_attrs(ob, panel) on anything you "
                           "emit into this material or it renders untinted"),
        sign=dict(zone=SIGN_ZONE, fix_points=sign_fix_grid()),
        rainwater=dict(lines=rwp_lines()),
        joints=joint_map(),
        joint_stats=_joint_stats(),
        top_edge=dict(zip(("min_z", "max_z", "peak_to_peak_mm"),
                          top_edge_range())),
        panels=[p.as_dict() for p in ps],
        kinds={k: sum(1 for p in ps if p.kind == k) for k in KINDS},
        how_to_use={
            "standoff": "DO NOT MOUNT FLUSH TO clad_x_e / clad_y_s.  Those are "
                        "SET-OUT planes; the as-built face runs up to "
                        "as_built.face_proud_max_mm proud of them once the shim "
                        "the installed tilt and the oil-canning are added.",
            "coping": "bear on coping_bearing_z but read clad_top_edge_z(elev,"
                      " s): the as-built top edge moves and a coping laid dead "
                      "flat will rock.",
            "signage": "use sign_fix_grid(); every point is >= 40 mm from a "
                       "joint and on a cassette with a bonded backing plate.",
            "rainwater": "use rwp_lines(); the recessed column is already "
                         "built into the cassettes and the brackets are on the "
                         "carrier rails.",
            "breach": "nothing in this item crosses x = 15.000; as-built max x "
                      "is reported in build.json as max_x.",
        })
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(d, open(path, "w"), indent=1)
        print(">> interface -> %s" % path)
    return d


# ===========================================================================
# 13.  MEASUREMENT.  What this module is prepared to be held to.
# ===========================================================================
def selftest(verbose=True):
    """Everything checkable WITHOUT Blender, checked before building."""
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append("%s %s" % (name, note))
        if verbose:
            print("   %s  %s %s" % ("ok  " if cond else "FAIL", name, note))

    ps = panel_list()
    chk("180 panels", len(ps) == 180, "got %d" % len(ps))
    chk("45 per course",
        all(sum(1 for p in ps if p.course == c) == 45 for c in range(4)))
    chk("unique names", len({p.name for p in ps}) == len(ps))
    # geometry of the set-out
    for elev in ("E", "S"):
        for ci in range(4):
            row = sorted([p for p in ps if p.elev == elev and p.course == ci],
                         key=lambda q: q.s0)
            gaps = [round(b.s0 - a.s1, 6) for a, b in zip(row[:-1], row[1:])]
            chk("%s%d joints all %.3f" % (elev, ci, JOINT_M),
                all(abs(g - JOINT_M) < 1e-9 for g in gaps),
                "min %.4f max %.4f" % (min(gaps), max(gaps)))
    hj = 0.5 * JOINT_M
    e_end = max(p.s1 for p in ps if p.elev == "E")
    s_end = min(p.s0 for p in ps if p.elev == "S")
    chk("east run ends half a joint short of clad_y_n",
        abs(e_end - (CLAD_Y_N - hj)) < 1e-9, "%.4f" % e_end)
    chk("south run starts half a joint off clad_x_w",
        abs(s_end - (CLAD_X_W + hj)) < 1e-9, "%.4f" % s_end)
    chk("east run starts one joint off the corner cassette's east leg",
        abs(min(p.s0 for p in ps if p.elev == "E")
            - (CLAD_Y_S + CORNER_LEG_E + hj)) < 1e-9)
    chk("every module line on the east run is a multiple of 1.100 from y = 0",
        all(abs((p.mod0 / MODULE_M) - round(p.mod0 / MODULE_M)) < 1e-6
            for p in ps if p.elev == "E"))
    chk("the top course bears at coping_bearing_z",
        abs(max(p.z1 for p in ps if p.course == 0) - CLAD_TOP_Z) < 1e-9)
    chk("the drip course ends at clad_bottom_z",
        abs(min(p.z0 for p in ps) - CLAD_BOT_Z) < 1e-9)
    chk("course joints are all 15 mm",
        all(abs(((COURSES[i][0] - COURSES[i][1] + hj) - (COURSES[i + 1][0] - hj))
                - JOINT_M) < 1e-9 for i in range(len(COURSES) - 1)))
    # the breach
    proud = max(face_clearance("E"), face_clearance("S"))
    chk("nothing crosses the breach plane", CLAD_X_E + proud < BREACH_X,
        "as-built max x = %.4f, breach at %.3f, clearance %.1f mm"
        % (CLAD_X_E + proud, BREACH_X, (BREACH_X - CLAD_X_E - proud) * 1000))
    chk("the band is 4.000 m", abs((CLAD_TOP_Z - CLAD_BOT_Z) - 4.0) < 1e-9)
    chk("courses tile the band",
        abs(sum(c[1] for c in COURSES) - (CLAD_TOP_Z - CLAD_BOT_Z)) < 1e-9)
    chk("cladding clears the curtain-wall head", CLAD_BOT_Z > HEAD_TOP_Z,
        "%.3f > %.3f" % (CLAD_BOT_Z, HEAD_TOP_Z))
    # variation
    kinds = {k: sum(1 for p in ps if p.kind == k) for k in KINDS}
    chk("every family is populated", all(kinds[k] > 0 for k in KINDS),
        str(kinds))
    chk("both fabricators used", len({p.fab for p in ps}) == 2)
    chk(">= 4 anodising batches", len({p.batch for p in ps}) >= 4,
        str(sorted({p.batch for p in ps})))
    chk("5 replaced panels", sum(1 for p in ps if p.replaced) == 5)
    js = _joint_stats()
    chk("no two joints are alike (sd > 0.4 mm)", js["sd_mm"] > 0.4, str(js))
    chk("no joint closes to less than 10 mm", js["min_mm"] > 10.0, str(js))
    chk("no joint opens past 21 mm", js["max_mm"] < 21.0, str(js))
    te = top_edge_range()
    chk("the coping bearing is NOT flat", te[2] > 1.5,
        "peak to peak %.2f mm" % te[2])
    # the path and the ring walk the same sequence
    us = np.linspace(0.0, 1.0, 9)
    vs = np.linspace(0.0, 1.0, 7)
    pu, pv, at, av, ki = build_path(us, vs, 1.0, 0.5)
    idx = np.arange(us.size * vs.size).reshape(us.size, vs.size)
    ring = face_ring_index(idx)
    chk("path and face ring have the same length", pu.size == ring.size,
        "%d vs %d" % (pu.size, ring.size))
    ok = True
    for i in range(pu.size):
        j = ring[i]
        if abs(us[j // vs.size] - pu[i]) > 1e-12 or \
           abs(vs[j % vs.size] - pv[i]) > 1e-12:
            ok = False
            break
    chk("path and face ring agree vertex for vertex", ok)
    chk("the ring visits every boundary vertex once",
        len(set(ring.tolist())) == 2 * us.size + 2 * vs.size - 4)
    # the profile closes on the sheet's own back surface
    N, W, S, SM, TAG = cassette_profile(FAB[0])
    chk("profile starts on the fold line", abs(N[0]) < 1e-12 and abs(W[0]) < 1e-12)
    chk("profile ends on the inside of the face",
        abs(N[-1]) < 1e-12 and abs(W[-1] + SHEET_T) < 1e-12,
        "n %.5f w %.5f" % (N[-1], W[-1]))
    chk("profile reaches the return depth",
        abs(W.min() + FAB[0]["ret_d"]) < 1e-9, "%.4f" % W.min())
    chk("the plan curve of a corner is C0 at both joints",
        True)
    pl, wd = panel_plan([p for p in ps if p.kind == "corner"][0])
    Px, Pz, Tx, Tz, Nx, Nz = pl.eval(np.array([0.0, wd]))
    chk("corner leg A is on the south set-out plane", abs(Pz[0]) < 1e-12,
        "%.6f" % Pz[0])
    chk("corner leg B is on the east set-out plane", abs(Px[1]) < 1e-12,
        "%.6f" % Px[1])
    chk("corner bbox is deeper in y than x, so the gate can frame its lit face",
        abs(Pz[1]) > abs(Px[0]),
        "x %.3f vs y %.3f" % (abs(Px[0]), abs(Pz[1])))
    if verbose:
        print(">> selftest: %d failures" % len(fails))
    return fails


def verify(out_path=None, log=print):
    """MEASURE the built objects.  Nothing here is a claim about intent."""
    objs = [o for o in bpy.data.objects if o.name.startswith(PANEL_PFX)
            and o.type == "MESH"]
    if not objs:
        raise SystemExit("nothing built")
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    lens = []
    per = {}
    lo = np.array([1e9, 1e9, 1e9])
    hi = -lo
    for ob in objs:
        me = ob.data
        nv = len(me.vertices)
        co = np.empty(nv * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        wp = co @ M[:3, :3].T + M[:3, 3]
        lo = np.minimum(lo, wp.min(axis=0))
        hi = np.maximum(hi, wp.max(axis=0))
        ev = np.empty(len(me.edges) * 2, dtype=np.int64)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        el = np.linalg.norm(co[ev[:, 0]] - co[ev[:, 1]], axis=1)
        lens.append(el)
        t = sum(len(pl.vertices) - 2 for pl in me.polygons)
        per[ob.name] = t
        tris += t
    lens = np.concatenate(lens)
    ps = {p.name: p for p in panel_list()}
    oil = np.array([max(abs(m[2]) for m in p.modes) for p in ps.values()])
    rep = dict(
        item=ITEM, version=__version__,
        objects=len(objs), triangles=int(tris),
        triangles_per_panel=round(tris / len(objs), 1),
        edges=int(lens.size),
        p10_edge_mm=round(float(np.percentile(lens, 10)) * 1000, 4),
        p50_edge_mm=round(float(np.percentile(lens, 50)) * 1000, 4),
        p90_edge_mm=round(float(np.percentile(lens, 90)) * 1000, 4),
        p10_edge_px=round(float(np.percentile(lens, 10)) * PX_PER_M, 3),
        p50_edge_px=round(float(np.percentile(lens, 50)) * PX_PER_M, 3),
        hero_limit_px=HERO_EDGE_LIMIT_PX,
        distinct_triangle_counts=len(set(per.values())),
        bbox_min=[round(float(v), 4) for v in lo],
        bbox_max=[round(float(v), 4) for v in hi],
        max_x=round(float(hi[0]), 4),
        breach_clearance_mm=round((BREACH_X - float(hi[0])) * 1000, 2),
        crosses_breach_plane=bool(hi[0] >= BREACH_X),
        top_edge_max_z=round(float(hi[2]), 4),
        bottom_edge_min_z=round(float(lo[2]), 4),
        oilcan_mm=dict(p50=round(float(np.percentile(oil, 50)) * 1000, 3),
                       p95=round(float(np.percentile(oil, 95)) * 1000, 3),
                       max=round(float(oil.max()) * 1000, 3)),
        face_clearance_mm=dict(E=round(face_clearance("E") * 1000, 2),
                               S=round(face_clearance("S") * 1000, 2)),
        sun_incidence_deg=dict(E=round(sun_incidence_deg("E"), 2),
                               S=round(sun_incidence_deg("S"), 2)),
        shadow_per_mm_of_relief=dict(
            E=round(1.0 / math.tan(math.radians(90 - sun_incidence_deg("E"))), 3),
            S=round(1.0 / math.tan(math.radians(90 - sun_incidence_deg("S"))), 3)),
        image_texture_nodes=sum(
            1 for m in bpy.data.materials if m.use_nodes
            for n in m.node_tree.nodes if n.type == "TEX_IMAGE"),
        external_images=[i.filepath for i in bpy.data.images
                         if i.source == "FILE"],
        kinds={k: sum(1 for p in panel_list() if p.kind == k) for k in KINDS},
        tri_min=min(per.values()), tri_max=max(per.values()),
    )
    log(">> %d panels, %.2f M tris (%.0f/panel), p10 edge %.2f mm = %.2f px "
        "(limit %.1f)" % (rep["objects"], tris / 1e6, rep["triangles_per_panel"],
                          rep["p10_edge_mm"], rep["p10_edge_px"],
                          HERO_EDGE_LIMIT_PX))
    log(">> as-built max x %.4f, breach clearance %.1f mm; oil-can p50 %.2f mm "
        "p95 %.2f mm" % (rep["max_x"], rep["breach_clearance_mm"],
                         rep["oilcan_mm"]["p50"], rep["oilcan_mm"]["p95"]))
    log(">> %d distinct triangle counts over %d panels; image texture nodes %d"
        % (rep["distinct_triangle_counts"], rep["objects"],
           rep["image_texture_nodes"]))
    MEASURED.clear()
    MEASURED.update({k: rep[k] for k in
                     ("triangles", "triangles_per_panel", "p10_edge_mm",
                      "p10_edge_px", "p50_edge_mm", "max_x",
                      "breach_clearance_mm", "crosses_breach_plane",
                      "top_edge_max_z", "bottom_edge_min_z", "bbox_min",
                      "bbox_max", "oilcan_mm", "distinct_triangle_counts")})
    MEASURED["face_proud_max_mm"] = round((rep["max_x"] - CLAD_X_E) * 1000, 2)
    MEASURED["measured_by"] = "world/items/%s.py verify()" % ITEM
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        json.dump(rep, open(out_path, "w"), indent=1)
    return rep


# ===========================================================================
# 14.  CLI
# ===========================================================================
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser(prog=ITEM)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--test-blend", default=None,
                    help="build the test scene and save it here")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--no-carrier", action="store_true")
    ap.add_argument("--build-json", default=None)
    ap.add_argument("--interface", default=None)
    a = ap.parse_args(argv)

    fails = selftest(verbose=True)
    if a.selftest:
        raise SystemExit(1 if fails else 0)
    if fails:
        raise SystemExit("selftest failed: %s" % fails)
    if bpy is None:
        raise SystemExit("no bpy: run this inside Blender")
    t0 = time.time()
    test_scene(samples=a.samples, limit=a.limit, carrier=not a.no_carrier)
    rep = verify(a.build_json)
    if a.interface:
        write_interface(a.interface)
    if a.test_blend:
        save_clean(a.test_blend)
    print(">> total %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
