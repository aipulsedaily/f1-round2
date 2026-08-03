#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sky.py — procedural sky, sun and atmosphere for CIRCUIT VITRINE.

ONE CONTINUOUS SHOT.  The camera starts inside a darkened showroom, breaches a glass
wall, crosses a paddock and flies a 3675 m lap, ending 140 m up looking 600 m back at
the wounded building.  There is exactly ONE physical light in that world and this
module owns it: a late-afternoon sun at the circuit spec's measured angle, the sky it
belongs to, and the air between the camera and everything it can see.

WHAT THIS MODULE OWNS
  * SKY_Sun          — the single SUN lamp.  Direction, colour and irradiance are
                       MEASURED against Blender's own spectral sky model, not dialled.
  * SKY_World        — the world shader: Blender 5.2 MULTIPLE_SCATTERING sky
                       (Garcia Linan spectral model) + three procedurally-projected
                       cloud decks + a camera-ray-only solar disc with limb darkening.
                       No image texture of any kind: nothing to lose on a render farm,
                       nothing to band, infinite angular resolution at 4K.
  * SKY_Atmosphere   — a homogeneous Rayleigh + Mie slab that gives every distant
                       object real aerial perspective (extinction AND airlight).
  * SKY_HazeStrata   — a thin, structured low-level haze so the near/mid air is not a
                       uniform grey wash.

WHAT IT DOES NOT OWN
  * exposure.  Nothing here touches scene.view_settings.  The light is physically
    absolute; the animated camera exposes it.  build() reports the reference stop.
  * the interior practicals (round 1's 23 lamps), the breach dust column, cloud
    shadows (see build_sky.md 6.3 for why there are none).

HARD CONSTRAINTS HONOURED
  * PROCEDURAL ONLY.  No HDRI, no photo, no downloaded stock.  Round 1's city.exr is
    a photograph and is not referenced here (see DEFECT-LOG-R2 R2-013).
  * The sun serves Beat 1 (interior) and Beats 4-6 (circuit) as one light, because
    the camera crosses between them without a cut.

Run headless:
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P build_sky.py
    ...                                  -P build_sky.py -- --render all
    ...                                  -P build_sky.py -- --calibrate
Idempotent: re-running purges and rebuilds only the datablocks this module owns.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy
import bmesh
from mathutils import Vector

# ----------------------------------------------------------------------------------
# 0.  PATHS AND IDENTITY
# ----------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC_JSON = os.path.join(ROOT, "docs", "circuit_spec.json")
BEAT_JSON = os.path.join(ROOT, "docs", "beat_sheet.json")
RENDER_DIR = os.path.join(ROOT, "render", "world", "sky")

COLL = "WORLD_SKY"
PFX = "SKY_"                      # every datablock this module owns starts with this


def log(*a):
    print("[sky]", *a, flush=True)


# ----------------------------------------------------------------------------------
# 1.  THE SUN — GEOMETRY, MEASURED FROM THE SPEC
# ----------------------------------------------------------------------------------
# circuit_spec.json:sun.direction_to_sun is published to 3 decimals and is therefore
# not quite unit length (|d| = 1.00043).  Normalising changes the elevation by 0.03 deg
# and the bearing by 0.03 deg — under the pixel, but the whole point of this module is
# that the number is exact everywhere it is used, so it is normalised once, here, and
# every consumer reads SUN_DIR.

_RAW_SUN = (0.518, -0.828, 0.216)
SUN_DIR = Vector(_RAW_SUN).normalized()                    # (.517854, -.827767, .215939)
SUN_ELEV = math.asin(SUN_DIR.z)                            # 0.217654 rad = 12.4706 deg
SUN_BEARING = math.atan2(SUN_DIR.y, SUN_DIR.x)             # -1.011766 rad = -57.9697 deg
SHADOW_RATIO = 1.0 / math.tan(SUN_ELEV)                    # 4.5222  (spec publishes 4.51)
_h = math.hypot(SUN_DIR.x, SUN_DIR.y)
SUN_HORIZ = (SUN_DIR.x / _h, SUN_DIR.y / _h)               # unit horizontal, toward sun

# Blender 5.2's MULTIPLE_SCATTERING sky is world-space locked: its Vector input is
# DISABLED for the scattering models, so the deck cannot be rotated with a Mapping node
# and sun_rotation is the only handle.  Its convention was MEASURED (see build_sky.md
# 3.1): an emissive marker was placed at SUN_DIR and sun_rotation swept until the sky's
# own disc landed on it.  Result: bearing = 90 deg - sun_rotation, i.e.
SKY_SUN_ROTATION = math.radians(90.0) - SUN_BEARING        # 2.582247 rad = 147.9697 deg

# Angular diameter.  0.545 deg is Blender's sky-model disc; the geometric solar disc is
# 0.533 deg and refraction/scattering broaden it at 4.5 air masses.  The lamp and the
# drawn disc use the same number so shadows, specular highlights and the visible sun
# cannot disagree.
SUN_ANGULAR_DIAM = math.radians(0.545)
SUN_HALF_ANGLE = SUN_ANGULAR_DIAM * 0.5
SUN_SOLID_ANGLE = math.pi * SUN_HALF_ANGLE ** 2            # 7.1053e-5 sr
SUN_LIMB_U = 0.60                                          # visible-band limb darkening

# ----------------------------------------------------------------------------------
# 2.  SKY MODEL PARAMETERS
# ----------------------------------------------------------------------------------
# air 1.0            standard sea-level molecular column.
# aerosol 0.45       DELIBERATELY below Blender's "urban" 1.0.  The bottom ~1.1 km of
#                    aerosol is modelled explicitly by SKY_Atmosphere so that distant
#                    GEOMETRY hazes, which a background shader can never do.  Leaving
#                    the sky at 1.0 as well would count that air twice.
# ozone 1.30         mid-latitude summer column.  Ozone's Chappuis band eats 550-650 nm
#                    and is the reason a clean afternoon sky is blue rather than white;
#                    at 12.5 deg elevation it is what keeps the anti-solar half of the
#                    sky saturated instead of washing to grey.
# altitude 0.0       the datum: z = 0 is the showroom floor AND the pit-straight surface.
SKY_AIR = 1.0
SKY_AEROSOL = 0.45
SKY_OZONE = 1.30
SKY_ALTITUDE = 0.0

# ----------------------------------------------------------------------------------
# 3.  MEASURED PHOTOMETRY  (see calibrate(); reproduce with  -- --calibrate)
# ----------------------------------------------------------------------------------
# Measured two independent ways at the sky parameters above and agreeing to 4 s.f.:
#   (a) a white Lambertian plane rendered with the sky's own sun disc on and off;
#       E_normal = (A - B) * pi / sin(elevation)
#   (b) direct solid-angle integration of a 512x512 / 1.03 deg render of the disc
#   (a) -> (115.754, 82.917, 44.811)      (b) -> (115.764, 82.914, 44.787)
# These are Blender-sky-model radiometric units, not SI solar watts: what matters is
# that sun and sky are on ONE scale, and they are, because the sun was measured
# against the sky.
SUN_IRRADIANCE = (115.754, 82.917, 44.811)                 # W/m^2 normal to the sun
SUN_ENERGY = 115.754                                       # = max channel
SUN_COLOR = (1.00000, 0.71632, 0.38712)                    # = SUN_IRRADIANCE / max

# Sky-only (no disc) downward irradiance on a horizontal surface, and its normalised
# tint.  This is the fill light that fills every shadow in the film, and the colour a
# cloud's shaded side and the haze's back-scatter must be tinted with.
SKY_IRRADIANCE = (4.228, 7.577, 13.573)
SKY_TINT = (0.3115, 0.5582, 1.0000)
DIRECT_TO_DIFFUSE = 2.072                                  # on a horizontal surface

# Reference exposure for the camera rig.  An albedo-0.18 horizontal surface in full sun
# renders at 1.4888 linear, so placing it on AgX mid-grey needs -3.048 stops.  This is
# a HAND-OFF, not a setting: this module never writes view_settings.
REFERENCE_EXPOSURE_EXTERIOR = -3.048

# Solar disc centre radiance, derived from the measured irradiance and the limb law
# I(r)/I(0) = 1 - u(1 - sqrt(1 - r^2)), whose disc mean is (1 - u/3) x I(0).
# Cross-checked against the rendered disc centre (2.036e6, 1.458e6, 7.877e5): 0.1% .
# The per-channel slab compensation in SLAB_T_TO_SUN (section 4) is applied to it —
# see DISC_RADIANCE below, and gate G5 for why.
DISC_CENTRE_RADIANCE = SUN_ENERGY / SUN_SOLID_ANGLE / (1.0 - SUN_LIMB_U / 3.0)

# ----------------------------------------------------------------------------------
# 4.  ATMOSPHERE
# ----------------------------------------------------------------------------------
# Meteorological visual range (Koschmieder, 2% contrast): sigma_ext = 3.912 / V.
# V = 23 km is a clean-but-not-arctic summer afternoon.  What it buys, measured:
#     600 m (the Beat-6 showroom)   91% transmitted
#       3 km                        60%
#      10 km                        18%
# — a readable depth ramp rather than either a crisp matte painting or grey mush.
VISUAL_RANGE_M = 23000.0
SIGMA_EXT_550 = 3.912 / VISUAL_RANGE_M                     # 1.7009e-4 /m

# Rayleigh at sea level, 550 nm, and the lambda^-4 split across Rec.709 primaries
# (dominant wavelengths 612 / 549 / 465 nm).  This term is why distant hills go BLUE
# and not merely pale — the single most recognisable cue in aerial perspective.
SIGMA_RAYLEIGH_550 = 1.16e-5                               # /m
RAYLEIGH_RGB = (0.6493, 1.0000, 1.9490)

# Whatever is left is aerosol.  Angstrom exponent 1.1 gives its (much milder) colour.
SIGMA_AEROSOL_550 = SIGMA_EXT_550 - SIGMA_RAYLEIGH_550     # 1.5849e-4 /m
AEROSOL_RGB = (0.8873, 1.0000, 1.2003)
# Phase function.  Chosen by MEASUREMENT, not by preference: the mean airlight was
# rendered in annuli around the sun (48 spp, 90 deg lens) for six candidates.  Radiance
# at 0.6-1.5 deg / 6-12 deg / 12-20 deg from the sun, and the 1 deg -> 20 deg fall:
#
#     HG  g = 0.60           47    42    22     2x   flat: no aureole at all
#     HG  g = 0.78 (v1)     ~300  ~120   ~30     -   a 40 deg featureless white blob
#     HG  g = 0.85          280   105    30      9x  still too broad
#     2-lobe HG .93+.45     386    50    18.5   21x  good, but TWO volume closures
#     Mie  d = 0.6 um       170    93    32      5x  too flat
#     Mie  d = 2.0 um       498    77    24     21x  <-- same shape, ONE closure
#     Mie  d = 8.0 um      2578    55    23    112x  fog, not haze
#
# Cycles counts every volume closure as MAX_VOLUME_STACK_SIZE = 32 against a kernel
# limit of 64, so a material may hold at most TWO.  Mie at 2 um reproduces the two-lobe
# fit in one node and leaves the second slot for Rayleigh.  2 um is also the right
# number physically for continental haze / thin mist droplets.
AEROSOL_MIE_DIAMETER = 2.0        # micrometres

# Single-scattering albedo is taken as 1.0 (non-absorbing haze) because absorption
# would need a third volume closure and there is no room.  Real tropospheric aerosol
# runs 0.90-0.98.  The consequence is bounded and known: the EXTINCTION is unchanged
# (the coefficient is set to the target either way, so the distance ramp and the
# visual range are exact); only the AIRLIGHT is up to 8% brighter than a ssa = 0.92
# haze would be, i.e. the far distance sits a twelfth of a stop lighter.
AEROSOL_SSA = 1.0

# TWO NESTED HOMOGENEOUS SLABS — a two-step staircase approximation of the real
# exponential aerosol profile sigma(z) = sigma0 * exp(-z / 1120 m).
#
#   AirColumn    z -220 .. 1500 m   0.62 x sigma0 aerosol + ALL the Rayleigh
#   AirBoundary  z -220 ..  240 m   0.38 x sigma0 aerosol      (overlaps, so it ADDS)
#
# so ground level sees 1.00 x sigma0 and anything above the boundary layer sees 0.62.
# They deliberately OVERLAP rather than abut: coincident volume faces are a precision
# hazard and a gap would punch a hole in the column.
#
# Why homogeneous, MEASURED (build_sky.md 5.2): Cycles integrates a homogeneous volume
# analytically and ray-marches a textured one.  At 512x256/64spp on the GTX 1070 the
# same frame costs 8.8 s with the homogeneous slab, 8.1 s with a second homogeneous
# slab nested inside it, and 22-48 s the moment either becomes texture-driven.  Across
# 2978 frames that is the difference between free and a multi-day tax, so the global
# air is analytic and the textured layer is opt-in (STRATA_ENABLED).
#
# What it costs to be homogeneous: no patchiness.  What it does NOT cost, because these
# are properties of the phase function and the scene and not of a density texture:
#   * the air GLOWS toward the sun and goes blue-grey away from it (Mie, g = 0.78)
#   * haze darkens inside the shadow of a grandstand or the pit building, because
#     shadow rays out of the volume are still occluded by real geometry
#   * the distance ramp, which is the whole point
SLAB_TOP = 1500.0
SLAB_BOTTOM = -220.0
SLAB_HALF = 40000.0                                        # +-40 km: past total opacity
BOUNDARY_TOP = 240.0
BOUNDARY_FRACTION = 0.38                                   # of sigma0, added below 240 m
COLUMN_FRACTION = 0.62                                     # of sigma0, whole column

# --- the slab's own transmittance along the sun ray, and why the disc needs it -----
# The lamp is NOT attenuated by the slabs (visible_shadow = False, section 10.1): its
# measured value is already the ground-level beam.  The DRAWN disc, however, is part of
# the background, so a camera ray to it crosses the whole slab and IS attenuated.  Left
# alone the visible sun ends up half as bright and visibly redder than the light it
# casts, which is the bottom kilometre of reddening counted twice — exactly the error
# the lamp was spared.  So the drawn disc carries the inverse.
#
# Verified against the render before it was applied: gate G5 measured the disc arriving
# at (0.489, 0.437, 0.349) of the lamp; the closed form below gives (0.4880, 0.4360,
# 0.3476).  Three decimal places, so the compensation is exact rather than fitted.
_P_COL = SLAB_TOP / math.sin(SUN_ELEV)             # 6946.4 m of column layer
_P_BND = BOUNDARY_TOP / math.sin(SUN_ELEV)         # 1111.4 m more of boundary layer
_TAU_A = SIGMA_AEROSOL_550 * (COLUMN_FRACTION * _P_COL + BOUNDARY_FRACTION * _P_BND)
_TAU_R = SIGMA_RAYLEIGH_550 * _P_COL
SLAB_TAU_TO_SUN = tuple(_TAU_A * AEROSOL_RGB[i] + _TAU_R * RAYLEIGH_RGB[i]
                        for i in range(3))
SLAB_T_TO_SUN = tuple(math.exp(-t) for t in SLAB_TAU_TO_SUN)
DISC_RADIANCE = tuple(SUN_IRRADIANCE[i] / SUN_SOLID_ANGLE / (1.0 - SUN_LIMB_U / 3.0)
                      / SLAB_T_TO_SUN[i] for i in range(3))
DISC_PEAK = max(DISC_RADIANCE)
DISC_TINT = tuple(v / DISC_PEAK for v in DISC_RADIANCE)

# Opt-in textured low haze (see build_sky.md 5.2 for the cost).  Off by default.
STRATA_ENABLED = os.environ.get("SKY_STRATA", "0") == "1"
STRATA_TOP = 70.0
STRATA_HALF = 2200.0
STRATA_CENTRE = (-40.0, 360.0)                             # circuit centroid, world XY
STRATA_GAIN = 0.45                                         # x sigma0

# ----------------------------------------------------------------------------------
# 5.  CLOUD DECKS
# ----------------------------------------------------------------------------------
# Three decks, each a spherical shell intersected by the view ray (see 6.1) and sampled
# with non-tiling gradient noise, so there is no repeat anywhere and no resolution
# limit.  Every number below is a meteorological decision, written down:
#
#   * wind VEERS with height (Ekman spiral).  Surface flow is backed ~30-50 deg from
#     the gradient wind, so the three decks run at three different bearings.  That one
#     detail is most of what makes a sky read as a place rather than a backdrop.
#   * coverage is COMPOSED, not uniform: the sunward sky is thinned so the low sun has
#     something to read against, the anti-solar west is thickened because that is where
#     the Beat-6 closing wide points and where the lit faces of the clouds turn toward
#     the lens.
#   * each deck evolves on its own timescale (4D noise) and drifts at its own speed.
#     A cumulus deck that shape-shifted as fast as cirrus is a tell.
CLOUD = {
    "cirrus": dict(
        altitude=9000.0, scale=9000.0, aniso=5.0, shear_deg=18.0,
        detail=7.0, roughness=0.52, lacunarity=2.10,
        warp_scale=0.0, warp_amt=0.0,
        cover=0.560, soft=0.230, sun_clear=-0.075,       # NEGATIVE: more cirrus sunward
        march_taps=0, march_step=0.0, march_k=0.0,
        wind_ms=34.0, wind_deg=18.0, evolve=0.0035,
        seed=11.37,
    ),
    "altocumulus": dict(
        altitude=4600.0, scale=2100.0, aniso=1.70, shear_deg=-12.0,
        detail=6.0, roughness=0.480, lacunarity=2.00,
        warp_scale=9000.0, warp_amt=700.0,
        cover=0.535, soft=0.100, sun_clear=0.085,
        march_taps=2, march_step=2400.0, march_k=1.35,
        wind_ms=14.0, wind_deg=-12.0, evolve=0.0090,
        seed=53.09,
    ),
    "cumulus": dict(
        altitude=1550.0, scale=1250.0, aniso=1.25, shear_deg=-34.0,
        detail=6.0, roughness=0.520, lacunarity=2.05,
        warp_scale=5200.0, warp_amt=460.0,
        cover=0.620, soft=0.070, sun_clear=0.115,
        march_taps=4, march_step=1100.0, march_k=1.10,
        wind_ms=8.0, wind_deg=-34.0, evolve=0.0140,
        seed=97.61,
    ),
}

EARTH_R = 6371000.0

# Cloud radiometry, derived from the measured sun and sky rather than picked.
#   lit flank      = albedo * E_normal * <cos> / pi
#   shaded side    = albedo * (sky irradiance + ground bounce) / pi
CLOUD_ALBEDO = 0.75
CUMULUS_LIT = CLOUD_ALBEDO * SUN_ENERGY * 0.75 / math.pi           # 20.7
CUMULUS_SHADE = CLOUD_ALBEDO * (sum(SKY_IRRADIANCE) / 3.0 * 1.35) / math.pi   # 2.6
ALTOCU_LIT = CUMULUS_LIT * 0.80
ALTOCU_SHADE = CUMULUS_SHADE * 1.15
# Cirrus is optically THIN: its radiance is single-scattered sunlight through tau ~ 0.4,
# so away from the sun it is DIMMER than the blue sky (a grey veil) and within a few
# degrees of it, brighter than anything but the disc.  That asymmetry is the whole look
# of high cloud at a low sun and it falls out of the phase function, not out of a tint.
CIRRUS_TAU = 0.40
CIRRUS_BASE = CIRRUS_TAU * SUN_ENERGY / (4.0 * math.pi)            # 3.68

SEED = 20260728

# Anti-banding: real sky has ~1% aerosol mottle at a few degrees' scale.  Adding it is
# both true and the structural fix for gradient banding — it decorrelates quantisation
# without adding grain that would average away under 1000+ samples.
MOTTLE_AMPLITUDE = 0.010
MOTTLE_SCALE = 18.0


# ==================================================================================
# 6.  NODE PLUMBING
# ==================================================================================

class NB(object):
    """Tiny node-graph builder: auto-layout, terse constructors, no bookkeeping."""

    def __init__(self, tree):
        self.t = tree
        self.col = 0
        self.row = 0

    def _place(self, n, col, row):
        n.location = (col * 210.0, -row * 165.0)

    def new(self, idname, col, row, label=None, **kw):
        n = self.t.nodes.new(idname)
        self._place(n, col, row)
        if label:
            n.label = label
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        return self.t.links.new(a, b)

    # -- scalar maths ---------------------------------------------------------------
    def math(self, op, a, b=None, c=None, col=0, row=0, label=None, clamp=False):
        n = self.new("ShaderNodeMath", col, row, label or op)
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if hasattr(v, "is_output"):
                self.link(v, n.inputs[i])
            else:
                n.inputs[i].default_value = float(v)
        return n.outputs[0]

    def vmath(self, op, a, b=None, c=None, scale=None, col=0, row=0, label=None):
        n = self.new("ShaderNodeVectorMath", col, row, label or op)
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if hasattr(v, "is_output"):
                self.link(v, n.inputs[i])
            else:
                n.inputs[i].default_value = tuple(v)
        if scale is not None:
            if hasattr(scale, "is_output"):
                self.link(scale, n.inputs["Scale"])
            else:
                n.inputs["Scale"].default_value = float(scale)
        return n.outputs[0] if op not in ("DOT_PRODUCT", "DISTANCE", "LENGTH") \
            else n.outputs["Value"]

    def smoothstep(self, v, lo, hi, col=0, row=0, label=None):
        n = self.new("ShaderNodeMapRange", col, row, label or "smoothstep")
        n.interpolation_type = "SMOOTHSTEP"
        n.clamp = True
        self.link(v, n.inputs["Value"])
        n.inputs[1].default_value = float(lo)
        n.inputs[2].default_value = float(hi)
        n.inputs[3].default_value = 0.0
        n.inputs[4].default_value = 1.0
        return n.outputs["Result"]

    def sep(self, v, col=0, row=0):
        n = self.new("ShaderNodeSeparateXYZ", col, row, "split")
        self.link(v, n.inputs[0])
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def comb(self, x, y, z, col=0, row=0):
        n = self.new("ShaderNodeCombineXYZ", col, row, "join")
        for i, v in enumerate((x, y, z)):
            if hasattr(v, "is_output"):
                self.link(v, n.inputs[i])
            else:
                n.inputs[i].default_value = float(v)
        return n.outputs[0]

    @staticmethod
    def _sock(node, name, kind):
        """Pick the socket by (name, socket type).

        The Mix node carries one A/B/Result triple per data_type and hides the rest,
        so indexing by name alone silently lands on the ROTATION sockets and Blender
        then rejects a 4-tuple with a message about dimension 0.  Ask for the type.
        """
        for s in (node.inputs if kind != 'OUT' else node.outputs):
            if s.name == name and s.type == 'RGBA':
                return s
        raise KeyError("%s.%s (RGBA) not found" % (node.name, name))

    def mixrgb(self, fac, a, b, col=0, row=0, label=None):
        n = self.new("ShaderNodeMix", col, row, label or "mix")
        n.data_type = "RGBA"
        ff = [s for s in n.inputs if s.name == "Factor" and s.type == 'VALUE'][0]
        if hasattr(fac, "is_output"):
            self.link(fac, ff)
        else:
            ff.default_value = float(fac)
        ia = self._sock(n, "A", 'IN')
        ib = self._sock(n, "B", 'IN')
        for sock, v in ((ia, a), (ib, b)):
            if hasattr(v, "is_output"):
                self.link(v, sock)
            else:
                sock.default_value = (v[0], v[1], v[2], 1.0)
        return self._sock(n, "Result", 'OUT')

    def rgb(self, c, col=0, row=0, label=None):
        n = self.new("ShaderNodeRGB", col, row, label or "colour")
        n.outputs[0].default_value = (c[0], c[1], c[2], 1.0)
        return n.outputs[0]

    def scale_rgb(self, color, k, col=0, row=0, label=None):
        """colour * scalar, keeping it a colour.  k may be a socket or a float."""
        n = self.new("ShaderNodeMix", col, row, label or "x")
        n.data_type = "RGBA"
        n.blend_type = "MULTIPLY"
        [s for s in n.inputs if s.name == "Factor"
         and s.type == 'VALUE'][0].default_value = 1.0
        ia = self._sock(n, "A", 'IN')
        ib = self._sock(n, "B", 'IN')
        if hasattr(color, "is_output"):
            self.link(color, ia)
        else:
            ia.default_value = (color[0], color[1], color[2], 1.0)
        if hasattr(k, "is_output"):
            self.link(self.comb(k, k, k, col, row + 1), ib)
        else:
            ib.default_value = (k, k, k, 1.0)
        return self._sock(n, "Result", 'OUT')

    def add_rgb(self, a, b, col=0, row=0, label=None):
        n = self.new("ShaderNodeMix", col, row, label or "+")
        n.data_type = "RGBA"
        n.blend_type = "ADD"
        [s for s in n.inputs if s.name == "Factor"
         and s.type == 'VALUE'][0].default_value = 1.0
        ia = self._sock(n, "A", 'IN')
        ib = self._sock(n, "B", 'IN')
        for sock, v in ((ia, a), (ib, b)):
            if hasattr(v, "is_output"):
                self.link(v, sock)
            else:
                sock.default_value = (v[0], v[1], v[2], 1.0)
        return self._sock(n, "Result", 'OUT')


def _driven_value(tree, name, expression, targets=None, col=0, row=0):
    """A Value node whose output is driven.

    `expression` is evaluated by Blender's SIMPLE expression evaluator, so it must not
    need script auto-execution — that matters because these blends are shipped to a
    render farm which does not, and must not, run arbitrary python on load.
    `targets` maps variable name -> (object, transform_channel).
    """
    n = tree.nodes.new("ShaderNodeValue")
    n.name = name
    n.label = name
    n.location = (col * 210.0, -row * 165.0)
    fc = n.outputs[0].driver_add("default_value")
    drv = fc.driver
    drv.type = 'SCRIPTED'
    for v in list(drv.variables):
        drv.variables.remove(v)
    for vname, (ob, chan) in (targets or {}).items():
        var = drv.variables.new()
        var.name = vname
        var.type = 'TRANSFORMS'
        var.targets[0].id = ob
        var.targets[0].transform_type = chan
        var.targets[0].transform_space = 'WORLD_SPACE'
    drv.expression = expression
    return n


# ==================================================================================
# 7.  THE CLOUD DECK
# ==================================================================================

def _cloud_deck(nb, key, D, Dz, camXY, T, cos_psi, sun_h, col0):
    """Emit one cloud deck and return (alpha, colour) sockets.

    6.1  PROJECTION.  A deck is a spherical shell of radius R+H about the Earth centre.
    For an observer on the surface looking along unit D, the shell is hit at

        t = -R*Dz + sqrt((R*Dz)^2 + 2*R*H + H^2)

    The discriminant is positive for every direction, so there is always exactly one
    outward hit and the maths never needs a branch.  Using the SPHERE and not a flat
    plane is what makes the deck stop at the true horizon (a 9 km cirrus deck reaches
    338 km and quits) and what compresses the cells correctly as they recede — the flat
    -plane version runs to infinity and reads as a painted dome.

    The observer's height is taken as 0.  The camera never exceeds 140 m, which is 1.5%
    of the lowest deck: below the pixel, and it removes a dependency on a shader-side
    camera Z that Cycles does not reliably expose to the world.  The observer's XY IS
    tracked (see bind_camera) because the camera travels 3.6 km, and at 1550 m a
    stationary deck over that baseline is the classic skybox tell.
    """
    p = CLOUD[key]
    H = p["altitude"]
    c = col0

    # ---- shell intersection ------------------------------------------------------
    b = nb.math("MULTIPLY", Dz, EARTH_R, col=c, row=0, label="b = R*Dz")
    b2 = nb.math("MULTIPLY", b, b, col=c + 1, row=0, label="b^2")
    disc = nb.math("ADD", b2, 2.0 * EARTH_R * H + H * H, col=c + 2, row=0, label="disc")
    rt = nb.math("SQRT", disc, col=c + 3, row=0, label="sqrt")
    t = nb.math("SUBTRACT", rt, b, col=c + 4, row=0, label="t (m to deck)")

    # ---- hit point in world XY ---------------------------------------------------
    tD = nb.vmath("SCALE", D, scale=t, col=c + 5, row=0, label="t*D")
    Px, Py, _ = nb.sep(tD, col=c + 6, row=0)
    cx, cy, _ = nb.sep(camXY, col=c + 6, row=1)
    hx = nb.math("ADD", Px, cx, col=c + 7, row=0, label="hit x")
    hy = nb.math("ADD", Py, cy, col=c + 7, row=1, label="hit y")

    # ---- wind drift (deck-specific bearing AND speed: the wind veers with height) --
    wdx = math.cos(math.radians(p["wind_deg"])) * p["wind_ms"]
    wdy = math.sin(math.radians(p["wind_deg"])) * p["wind_ms"]
    dx = nb.math("MULTIPLY_ADD", T, -wdx, hx, col=c + 8, row=0, label="drift x")
    dy = nb.math("MULTIPLY_ADD", T, -wdy, hy, col=c + 8, row=1, label="drift y")
    P = nb.comb(dx, dy, p["seed"] * 1000.0, col=c + 9, row=0)

    # ---- domain warp -------------------------------------------------------------
    # A raw fbm field lays its cells out on a statistically uniform lattice; warping the
    # domain with a lower-frequency field is what turns that into streets and clusters.
    if p["warp_amt"] > 0.0:
        wm = nb.new("ShaderNodeMapping", c + 10, 2, "warp map")
        wm.vector_type = 'POINT'
        nb.link(P, wm.inputs["Vector"])
        wm.inputs["Scale"].default_value = (1.0 / p["warp_scale"],) * 3
        wn = nb.new("ShaderNodeTexNoise", c + 11, 2, "warp noise",
                    noise_dimensions='3D', normalize=True)
        nb.link(wm.outputs["Vector"], wn.inputs["Vector"])
        wn.inputs["Scale"].default_value = 1.0
        wn.inputs["Detail"].default_value = 2.0
        wn.inputs["Roughness"].default_value = 0.5
        # Colour output = three decorrelated noise fields; use it as a vector offset.
        off = nb.vmath("SUBTRACT", wn.outputs["Color"], (0.5, 0.5, 0.5),
                       col=c + 12, row=2, label="centre")
        off = nb.vmath("SCALE", off, scale=p["warp_amt"] * 2.0, col=c + 13, row=2)
        P = nb.vmath("ADD", P, off, col=c + 14, row=0, label="warped")
        c += 5

    # ---- anisotropic sampling frame (wind shear stretches cells along the flow) ----
    mp = nb.new("ShaderNodeMapping", c + 10, 0, "%s frame" % key)
    mp.vector_type = 'POINT'
    nb.link(P, mp.inputs["Vector"])
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(p["shear_deg"]))
    mp.inputs["Scale"].default_value = (1.0 / (p["scale"] * p["aniso"]),
                                        1.0 / p["scale"], 1.0 / p["scale"])
    Pm = mp.outputs["Vector"]

    # ---- evolution: 4D noise, W = time ------------------------------------------
    Wt = nb.math("MULTIPLY_ADD", T, p["evolve"], p["seed"], col=c + 11, row=3, label="W")

    def _noise(vec, cc, rr, tag):
        n = nb.new("ShaderNodeTexNoise", cc, rr, tag,
                   noise_dimensions='4D', noise_type='FBM', normalize=True)
        nb.link(vec, n.inputs["Vector"])
        nb.link(Wt, n.inputs["W"])
        n.inputs["Scale"].default_value = 1.0
        n.inputs["Detail"].default_value = p["detail"]
        n.inputs["Roughness"].default_value = p["roughness"]
        n.inputs["Lacunarity"].default_value = p["lacunarity"]
        return n.outputs["Factor"]

    dens = _noise(Pm, c + 12, 0, "%s density" % key)

    # ---- coverage: COMPOSED across the sky --------------------------------------
    # cos_h is +1 looking straight at the sun's bearing, -1 anti-solar.  Raising the
    # threshold removes cloud.  sun_clear > 0 thins the sunward sky (so the low sun has
    # something to read against); cirrus uses a NEGATIVE value because high ice cloud is
    # exactly what you want between the lens and a low sun.
    clear = nb.math("MULTIPLY_ADD", sun_h, 0.5, 0.5, col=c + 12, row=4, label="sunward")
    # ...plus a very large-scale patchiness so coverage is never uniform anywhere.
    bigm = nb.new("ShaderNodeMapping", c + 12, 5, "coverage patch")
    bigm.vector_type = 'POINT'
    nb.link(P, bigm.inputs["Vector"])
    bigm.inputs["Scale"].default_value = (1.0 / 26000.0,) * 3
    bign = nb.new("ShaderNodeTexNoise", c + 13, 5, "coverage noise",
                  noise_dimensions='3D', normalize=True)
    nb.link(bigm.outputs["Vector"], bign.inputs["Vector"])
    bign.inputs["Scale"].default_value = 1.0
    bign.inputs["Detail"].default_value = 2.0
    patch = nb.math("MULTIPLY_ADD", bign.outputs["Factor"], 0.18, -0.09,
                    col=c + 14, row=5, label="+-0.09")
    cov = nb.math("MULTIPLY_ADD", clear, p["sun_clear"], p["cover"],
                  col=c + 15, row=4, label="cover")
    cov = nb.math("ADD", cov, patch, col=c + 16, row=4, label="cover eff")
    cov_hi = nb.math("ADD", cov, p["soft"], col=c + 17, row=4, label="cover+soft")

    mr = nb.new("ShaderNodeMapRange", c + 18, 0, "%s alpha" % key)
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.clamp = True
    nb.link(dens, mr.inputs["Value"])
    nb.link(cov, mr.inputs[1])
    nb.link(cov_hi, mr.inputs[2])
    alpha = mr.outputs["Result"]

    # ---- horizon fade ------------------------------------------------------------
    # The deck is only valid above the true horizon.  From 140 m that is -0.38 deg, so
    # the ramp runs from -0.010 to +0.004 in Dz: below it the deck is gone, and by then
    # SKY_Atmosphere has already taken it to near-total opacity anyway.
    hz = nb.smoothstep(Dz, -0.010, 0.004, col=c + 18, row=6, label="horizon fade")
    alpha = nb.math("MULTIPLY", alpha, hz, col=c + 19, row=0, label="alpha")

    # ---- self-shadowing march ----------------------------------------------------
    # At 12.5 deg elevation a sun ray crosses 4.52 m of deck horizontally per metre of
    # depth, so the sun enters a cumulus almost through its FLANK.  Marching in the
    # projected plane toward the sun's bearing is therefore not an approximation of the
    # 3D march, it is very nearly the same ray.  The result is the correct late-
    # afternoon look: one bright flank, a long dark body behind it.
    if p["march_taps"] > 0:
        acc = None
        for k in range(1, p["march_taps"] + 1):
            step = p["march_step"] * k
            sm = nb.new("ShaderNodeMapping", c + 12, 7 + k, "march %d" % k)
            sm.vector_type = 'POINT'
            nb.link(P, sm.inputs["Vector"])
            sm.inputs["Location"].default_value = (SUN_HORIZ[0] * step,
                                                   SUN_HORIZ[1] * step, 0.0)
            sm.inputs["Rotation"].default_value = (0.0, 0.0,
                                                   math.radians(p["shear_deg"]))
            sm.inputs["Scale"].default_value = (1.0 / (p["scale"] * p["aniso"]),
                                                1.0 / p["scale"], 1.0 / p["scale"])
            dk = _noise(sm.outputs["Vector"], c + 13, 7 + k, "march dens %d" % k)
            # only what is above the coverage threshold occludes
            ok = nb.math("SUBTRACT", dk, cov, col=c + 14, row=7 + k)
            ok = nb.math("MAXIMUM", ok, 0.0, col=c + 15, row=7 + k)
            acc = ok if acc is None else nb.math("ADD", acc, ok,
                                                 col=c + 16, row=7 + k)
        tau = nb.math("MULTIPLY", acc, p["march_k"] * 6.0, col=c + 17, row=8,
                      label="tau")
        neg = nb.math("MULTIPLY", tau, -1.0, col=c + 18, row=8)
        sun_t = nb.math("EXPONENT", neg, col=c + 19, row=8, label="T_sun")
    else:
        sun_t = None

    # ---- radiometry --------------------------------------------------------------
    fwd_t = nb.math("MULTIPLY_ADD", cos_psi, 0.5, 0.5, col=c + 12, row=13,
                    label="fwd base")
    tight = nb.math("POWER", fwd_t, 42.0, col=c + 13, row=13, label="tight lobe")
    broad = nb.math("POWER", fwd_t, 5.0, col=c + 13, row=14, label="broad lobe")

    if key == "cirrus":
        # Optically-thin single scatter: L = tau * E/(4pi) * P(theta)
        ph = nb.math("MULTIPLY_ADD", tight, 46.0, 0.30, col=c + 14, row=13, label="P")
        ph = nb.math("MULTIPLY_ADD", broad, 3.0, ph, col=c + 15, row=13)
        lev = nb.math("MULTIPLY", ph, CIRRUS_BASE, col=c + 16, row=13, label="L")
        colour = nb.scale_rgb(SUN_COLOR, lev, col=c + 17, row=13, label="cirrus L")
        # the veil also transmits some sky, which keeps it from reading as a decal
        colour = nb.add_rgb(colour, nb.scale_rgb(SKY_TINT, 0.9, col=c + 17, row=14),
                            col=c + 18, row=13)
    else:
        lit = CUMULUS_LIT if key == "cumulus" else ALTOCU_LIT
        shade = CUMULUS_SHADE if key == "cumulus" else ALTOCU_SHADE
        litc = nb.scale_rgb(SUN_COLOR, lit, col=c + 14, row=13, label="lit flank")
        shac = nb.scale_rgb(SKY_TINT, shade, col=c + 14, row=14, label="shaded side")
        base = nb.mixrgb(sun_t, shac, litc, col=c + 16, row=13, label="shade mix")
        # forward-scatter rim ("silver lining") — strongest where the deck is thin and
        # the sun is behind it; scaled by (1 - T_sun) so it lives on the edges.
        rimf = nb.math("MULTIPLY_ADD", tight, 9.0, 0.0, col=c + 15, row=15)
        rimf = nb.math("MULTIPLY_ADD", broad, 1.2, rimf, col=c + 16, row=15)
        rimf = nb.math("MULTIPLY", rimf, lit * 0.55, col=c + 17, row=15, label="rim")
        rim = nb.scale_rgb(SUN_COLOR, rimf, col=c + 18, row=15)
        colour = nb.add_rgb(base, rim, col=c + 19, row=13)
        if key == "cumulus":
            # Flat bases: looking steeply up you see the shaded underside, looking
            # shallow you see the sunlit flank.  Three nodes, and it is the difference
            # between cumulus and cotton wool.
            look = nb.smoothstep(Dz, 0.45, 0.10, col=c + 18, row=16, label="flank view")
            basec = nb.scale_rgb(SKY_TINT, shade * 0.62, col=c + 18, row=17,
                                 label="cloud base")
            colour = nb.mixrgb(look, basec, colour, col=c + 20, row=13,
                               label="base/flank")
    return alpha, colour


# ==================================================================================
# 8.  THE WORLD
# ==================================================================================

def build_world(camera=None):
    w = bpy.data.worlds.new(PFX + "World")
    w.use_fake_user = True
    tree = w.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_WORLD':
            tree.nodes.remove(n)
    out = [n for n in tree.nodes if n.type == 'OUTPUT_WORLD'][0]
    out.location = (5200, 0)
    nb = NB(tree)

    fps = bpy.context.scene.render.fps or 24
    T = _driven_value(tree, PFX + "Time", "frame / %.6f" % float(fps),
                      col=0, row=8).outputs[0]
    camx_n = _driven_value(tree, PFX + "CamX", "0.0", col=0, row=9)
    camy_n = _driven_value(tree, PFX + "CamY", "0.0", col=0, row=10)
    camXY = nb.comb(camx_n.outputs[0], camy_n.outputs[0], 0.0, col=1, row=9)

    # ---- ray direction -----------------------------------------------------------
    # MEASURED (build_sky.md 3.2): for a world shader Texture Coordinate > Generated is
    # the unit RAY direction in world space, while Geometry > Incoming is its negation.
    # Getting that backwards mirrors the entire sky through the origin and is invisible
    # in a clear-sky test — which is exactly why it was measured and not assumed.
    tc = nb.new("ShaderNodeTexCoord", 0, 0, "ray dir")
    D = tc.outputs["Generated"]
    _, _, Dz = nb.sep(D, col=1, row=0)

    cos_psi = nb.vmath("DOT_PRODUCT", D, tuple(SUN_DIR), col=1, row=1, label="cos psi")

    # horizontal-only sun alignment, for the coverage composition
    dxy = nb.vmath("MULTIPLY", D, (1.0, 1.0, 0.0), col=1, row=2, label="D.xy")
    dxy = nb.vmath("NORMALIZE", dxy, col=2, row=2)
    sun_h = nb.vmath("DOT_PRODUCT", dxy, (SUN_HORIZ[0], SUN_HORIZ[1], 0.0),
                     col=3, row=2, label="cos bearing")

    # ---- base sky ----------------------------------------------------------------
    sky = nb.new("ShaderNodeTexSky", 2, 4, "MS sky")
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False              # the SUN lamp is the light; see 8.2
    sky.sun_size = SUN_ANGULAR_DIAM
    sky.sun_intensity = 1.0
    sky.sun_elevation = SUN_ELEV
    sky.sun_rotation = SKY_SUN_ROTATION
    sky.altitude = SKY_ALTITUDE
    sky.air_density = SKY_AIR
    sky.aerosol_density = SKY_AEROSOL
    sky.ozone_density = SKY_OZONE
    sky_col = sky.outputs["Color"]

    # ---- aerosol mottle (and the anti-banding term) -------------------------------
    mm = nb.new("ShaderNodeMapping", 2, 6, "mottle frame")
    mm.vector_type = 'POINT'
    nb.link(D, mm.inputs["Vector"])
    mm.inputs["Scale"].default_value = (MOTTLE_SCALE,) * 3
    mn = nb.new("ShaderNodeTexNoise", 3, 6, "mottle", noise_dimensions='4D',
                normalize=True)
    nb.link(mm.outputs["Vector"], mn.inputs["Vector"])
    nb.link(nb.math("MULTIPLY", T, 0.02, col=2, row=7), mn.inputs["W"])
    mn.inputs["Scale"].default_value = 1.0
    mn.inputs["Detail"].default_value = 4.0
    mn.inputs["Roughness"].default_value = 0.55
    mgain = nb.math("MULTIPLY_ADD", mn.outputs["Factor"], 2.0 * MOTTLE_AMPLITUDE,
                    1.0 - MOTTLE_AMPLITUDE, col=4, row=6, label="1 +- 1%")
    sky_col = nb.scale_rgb(sky_col, mgain, col=5, row=4, label="mottled sky")

    # ---- cloud decks, composited far to near -------------------------------------
    acc = sky_col
    col = 7
    for key in ("cirrus", "altocumulus", "cumulus"):
        a, c = _cloud_deck(nb, key, D, Dz, camXY, T, cos_psi, sun_h, col)
        acc = nb.mixrgb(a, acc, c, col=col + 34, row=0, label="over %s" % key)
        col += 36

    # ---- the solar disc, camera rays only ----------------------------------------
    # 8.2  Why the disc is drawn here and not by the sky node or the lamp:
    #   * sky_disc ON would light the scene a second time on top of the lamp, and the
    #     lamp is what gives clean shadows and a controllable penumbra.
    #   * a SUN lamp visible to camera draws a FLAT disc: no limb darkening, wrong at
    #     4K in a shot that looks into the sun.
    #   * so: lamp.visible_camera = False, sky.sun_disc = False, and the disc is a
    #     camera-ray-only emission term with the real limb law, at the radiance derived
    #     from the SAME measured irradiance the lamp uses.  One sun, three consumers,
    #     no possibility of disagreement.
    psi = nb.math("ARCCOSINE", nb.math("MINIMUM", cos_psi, 1.0, col=col, row=0),
                  col=col + 1, row=0, label="psi")
    r = nb.math("DIVIDE", psi, SUN_HALF_ANGLE, col=col + 2, row=0, label="r = psi/psi0")
    r2 = nb.math("MULTIPLY", r, r, col=col + 3, row=0)
    om = nb.math("SUBTRACT", 1.0, r2, col=col + 4, row=0)
    om = nb.math("MAXIMUM", om, 0.0, col=col + 5, row=0)
    mu = nb.math("SQRT", om, col=col + 6, row=0, label="mu")
    limb = nb.math("MULTIPLY_ADD", mu, SUN_LIMB_U, 1.0 - SUN_LIMB_U,
                   col=col + 7, row=0, label="limb")
    # A hard step at r = 1 aliases at 4K; 4.5 air masses of scattering blur the limb by
    # roughly 1.5% of the radius anyway, so the edge is a smoothstep, not a step.
    edge = nb.smoothstep(r, 1.015, 0.985, col=col + 7, row=1, label="limb edge")
    discf = nb.math("MULTIPLY", limb, edge, col=col + 8, row=0)
    discf = nb.math("MULTIPLY", discf, DISC_PEAK, col=col + 9, row=0, label="L_disc")
    # DISC_TINT, not SUN_COLOR: the drawn disc is pre-divided by the slab it will be
    # seen through, so that after SKY_Atmosphere attenuates it the visible sun is the
    # same beam the lamp casts.  See SLAB_T_TO_SUN and gate G5.
    disc = nb.scale_rgb(DISC_TINT, discf, col=col + 10, row=0, label="disc")

    lp = nb.new("ShaderNodeLightPath", col + 8, 2, "camera only")
    disc = nb.scale_rgb(disc, lp.outputs["Is Camera Ray"], col=col + 11, row=0,
                        label="x is-camera")
    final = nb.add_rgb(acc, disc, col=col + 13, row=0, label="sky + disc")

    bg = nb.new("ShaderNodeBackground", col + 15, 0, "background")
    nb.link(final, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    nb.link(bg.outputs["Background"], out.inputs["Surface"])
    out.location = ((col + 17) * 210.0, 0)

    # Importance-sample the sky: with the disc gone the map is smooth, but the cloud
    # decks are 10x the blue sky and worth sampling toward.
    w.cycles.sampling_method = 'MANUAL'
    w.cycles.sample_map_resolution = 1024
    w.cycles.max_bounces = 1024

    if camera is not None:
        bind_camera(camera, world=w)
    return w


def bind_camera(cam, world=None):
    """Point the cloud decks' observer at `cam` so they parallax over the lap.

    The camera rig owns the camera; this module owns the sky.  Call this once the rig
    exists.  Without it the decks sit at world XY (0,0) and behave as a skybox, which
    is a graceful degradation, not a crash.
    """
    world = world or bpy.data.worlds.get(PFX + "World")
    if world is None:
        return False
    tree = world.node_tree
    ok = 0
    for name, chan in ((PFX + "CamX", 'LOC_X'), (PFX + "CamY", 'LOC_Y')):
        n = tree.nodes.get(name)
        if n is None:
            continue
        n.outputs[0].driver_remove('default_value')
        fc = n.outputs[0].driver_add('default_value')
        drv = fc.driver
        drv.type = 'SCRIPTED'
        var = drv.variables.new()
        var.name = "v"
        var.type = 'TRANSFORMS'
        var.targets[0].id = cam
        var.targets[0].transform_type = chan
        var.targets[0].transform_space = 'WORLD_SPACE'
        drv.expression = "v"
        ok += 1
    log("bind_camera: %s -> %d cloud-parallax drivers" % (cam.name, ok))
    return ok == 2


# ==================================================================================
# 9.  THE SUN LAMP
# ==================================================================================

def build_sun(coll):
    lt = bpy.data.lights.new(PFX + "Sun", 'SUN')
    lt.energy = SUN_ENERGY
    lt.color = SUN_COLOR
    lt.angle = SUN_ANGULAR_DIAM
    lt.use_shadow = True
    lt.cycles.use_multiple_importance_sampling = True
    lt.cycles.max_bounces = 1024

    ob = bpy.data.objects.new(PFX + "Sun", lt)
    # A Blender SUN emits along its own -Z, so local +Z must be the direction TO the
    # sun.  Inverting this puts the sun underground and every frame comes back flat.
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = SUN_DIR.to_track_quat('Z', 'Y')
    # Parked high and well clear of the circuit so it is never selected by accident in
    # the viewport; a SUN's position is irrelevant to the light it casts.
    ob.location = (SUN_DIR.x * 2000.0, SUN_DIR.y * 2000.0, SUN_DIR.z * 2000.0)
    # The world shader draws the disc with the real limb law; a lamp visible to camera
    # would draw a second, flat one on top of it.
    ob.visible_camera = False
    coll.objects.link(ob)
    return ob


# ==================================================================================
# 10.  THE ATMOSPHERE
# ==================================================================================

def _box(name, cx, cy, z0, z1, half, coll):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(2.0 * half, 2.0 * half, z1 - z0),
                    verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, 0.5 * (z0 + z1)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _atmosphere_material(name, sigma_scale, structured, rayleigh=1.0):
    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    out = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    out.location = (1400, 0)
    nb = NB(tree)

    sig_a_s = SIGMA_AEROSOL_550 * AEROSOL_SSA * sigma_scale
    # Rayleigh has an 8.5 km scale height, so over the 1.7 km these slabs span it is
    # uniform: all of it goes in the column layer and none in the boundary layer.
    sig_r = SIGMA_RAYLEIGH_550 * rayleigh

    dens_a = None
    if structured:
        # z-falloff x large-scale patchiness.  Real low haze pools in hollows and thins
        # over ridges; a uniform slab is correct physics and a dead image, so the bulk
        # extinction stays in the homogeneous slab and only this thin layer is textured.
        geo = nb.new("ShaderNodeNewGeometry", 0, 0, "P")
        _, _, pz = nb.sep(geo.outputs["Position"], col=1, row=0)
        fall = nb.smoothstep(pz, STRATA_TOP, -6.0, col=2, row=0, label="z falloff")
        fall = nb.math("POWER", fall, 1.6, col=3, row=0)
        mp = nb.new("ShaderNodeMapping", 1, 2, "haze frame")
        mp.vector_type = 'POINT'
        nb.link(geo.outputs["Position"], mp.inputs["Vector"])
        mp.inputs["Scale"].default_value = (1.0 / 620.0, 1.0 / 620.0, 1.0 / 160.0)
        nz = nb.new("ShaderNodeTexNoise", 2, 2, "haze patches",
                    noise_dimensions='3D', normalize=True)
        nb.link(mp.outputs["Vector"], nz.inputs["Vector"])
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 3.0
        nz.inputs["Roughness"].default_value = 0.55
        patch = nb.math("MULTIPLY_ADD", nz.outputs["Factor"], 1.30, 0.42,
                        col=3, row=2, label="0.42..1.72")
        dens_a = nb.math("MULTIPLY", fall, patch, col=4, row=0, label="profile")

    def _scatter(col_rgb, sigma, phase, row, tag, **kw):
        n = nb.new("ShaderNodeVolumeScatter", 6, row, tag)
        n.phase = phase
        n.inputs["Color"].default_value = (col_rgb[0], col_rgb[1], col_rgb[2], 1.0)
        if dens_a is None:
            n.inputs["Density"].default_value = sigma
        else:
            nb.link(nb.math("MULTIPLY", dens_a, sigma, col=5, row=row),
                    n.inputs["Density"])
        for k, v in kw.items():
            n.inputs[k].default_value = v
        return n.outputs["Volume"]

    # The aerosol.  ONE Mie closure (see AEROSOL_MIE_DIAMETER for the measurement that
    # picked it).  This is why the air GLOWS when the camera looks toward the low sun
    # and goes quietly blue-grey when it looks away — the same medium, opposite
    # behaviour, no per-shot cheat anywhere.
    acc = _scatter(AEROSOL_RGB, sig_a_s, 'MIE', 0, "Mie aerosol",
                   Diameter=AEROSOL_MIE_DIAMETER)
    if sig_r > 0.0:
        # Rayleigh: the air itself.  Symmetric phase, lambda^-4 colour.  Tiny in
        # magnitude and entirely responsible for distant terrain reading BLUE rather
        # than merely pale — the most recognisable cue in aerial perspective there is.
        ray = _scatter(RAYLEIGH_RGB, sig_r, 'RAYLEIGH', 3, "Rayleigh air")
        a2 = nb.new("ShaderNodeAddShader", 8, 0, "+")
        nb.link(acc, a2.inputs[0])
        nb.link(ray, a2.inputs[1])
        acc = a2.outputs[0]
    nb.link(acc, out.inputs["Volume"])
    # Closure budget: Cycles charges MAX_VOLUME_STACK_SIZE (32) per volume closure
    # against a kernel limit of 64, so this material must never hold more than two.
    # Exceeding it logs "Maximum number of closures exceeded" and silently clamps.
    n_closures = len([n for n in tree.nodes
                      if n.bl_idname in ('ShaderNodeVolumeScatter',
                                         'ShaderNodeVolumeAbsorption',
                                         'ShaderNodeVolumePrincipled')])
    assert n_closures <= 2, ("volume closure budget blown in %s: %d closures x 32 > 64"
                             % (name, n_closures))

    mat.cycles.volume_sampling = 'MULTIPLE_IMPORTANCE'
    mat.cycles.volume_interpolation = 'LINEAR'
    if structured:
        mat.cycles.volume_step_rate = 6.0
    return mat


def build_atmosphere(coll):
    """The air.  Invisible, analytic, and — measured — free."""
    obs = []

    col = _box(PFX + "AirColumn", 0.0, 0.0, SLAB_BOTTOM, SLAB_TOP, SLAB_HALF, coll)
    col.data.materials.append(
        _atmosphere_material(PFX + "Air", COLUMN_FRACTION, False, rayleigh=1.0))
    bnd = _box(PFX + "AirBoundary", 0.0, 0.0, SLAB_BOTTOM, BOUNDARY_TOP, SLAB_HALF, coll)
    bnd.data.materials.append(
        _atmosphere_material(PFX + "AirLow", BOUNDARY_FRACTION, False, rayleigh=0.0))
    obs += [col, bnd]

    if STRATA_ENABLED:
        st = _box(PFX + "HazeStrata", STRATA_CENTRE[0], STRATA_CENTRE[1],
                  -8.0, STRATA_TOP, STRATA_HALF, coll)
        st.data.materials.append(
            _atmosphere_material(PFX + "AirStrata", STRATA_GAIN, True))
        obs.append(st)

    for ob in obs:
        # 10.1  visible_shadow = False, deliberately.
        # The measured SUN_IRRADIANCE is already the value AT THE GROUND: all 4.5 air
        # masses of reddening are baked into SUN_COLOR.  If these slabs also attenuated
        # shadow rays they would apply the bottom kilometre of that path a SECOND time
        # (tau = 0.70 over the 4.1 km slant path — half the key light), and every
        # shadow ray in the film would become a volume ray.
        # Cost of the choice: the global haze casts no god rays.  A clear sky has no
        # occluders, so there is nothing to lose here; the breach dust column is a
        # separate, local volume and may cast whatever it likes.
        ob.visible_shadow = False
        ob.visible_volume_scatter = True
        ob.hide_select = True
    return obs


# ==================================================================================
# 11.  BUILD
# ==================================================================================

def purge():
    """Idempotence: remove everything this module owns, and nothing else."""
    n = 0
    c = bpy.data.collections.get(COLL)
    if c is not None:
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
            n += 1
        for sc in bpy.data.scenes:
            if c.name in sc.collection.children:
                sc.collection.children.unlink(c)
        bpy.data.collections.remove(c)
    for coll_ in (bpy.data.objects, bpy.data.lights, bpy.data.meshes,
                  bpy.data.materials, bpy.data.worlds, bpy.data.node_groups):
        for d in list(coll_):
            if d.name.startswith(PFX):
                try:
                    coll_.remove(d)
                    n += 1
                except Exception:
                    pass
    return n


def build(scene=None, camera=None):
    t0 = time.time()
    scene = scene or bpy.context.scene
    purged = purge()

    coll = bpy.data.collections.new(COLL)
    scene.collection.children.link(coll)

    log("sun: elev %.4f deg  bearing %.4f deg  shadows %.3f x height"
        % (math.degrees(SUN_ELEV), math.degrees(SUN_BEARING), SHADOW_RATIO))
    sun = build_sun(coll)
    log("sun: E_normal %s   lamp energy %.3f colour %s   disc %.3f deg"
        % (tuple(round(v, 3) for v in SUN_IRRADIANCE), SUN_ENERGY,
           tuple(round(v, 5) for v in SUN_COLOR), math.degrees(SUN_ANGULAR_DIAM)))

    if camera is None:
        camera = scene.camera
    world = build_world(camera)
    scene.world = world
    log("world: MS sky air=%.2f aerosol=%.2f ozone=%.2f, %d nodes, 3 cloud decks"
        % (SKY_AIR, SKY_AEROSOL, SKY_OZONE, len(world.node_tree.nodes)))

    atmo = build_atmosphere(coll)
    log("atmosphere: V=%.0f m, sigma_ext(550)=%.4e /m  (600 m -> %.0f%%, 3 km -> %.0f%%,"
        " 10 km -> %.0f%%)"
        % (VISUAL_RANGE_M, SIGMA_EXT_550,
           100 * math.exp(-SIGMA_EXT_550 * 600),
           100 * math.exp(-SIGMA_EXT_550 * 3000),
           100 * math.exp(-SIGMA_EXT_550 * 10000)))

    # 11.1  Two integrator settings are part of the LIGHT, not of the render recipe,
    # and are therefore set here rather than left to whoever renders:
    #   * volume_bounces 0 (Blender's default) makes an optically-thick horizon haze
    #     too dark, because at tau > 1 multiple scattering is most of the airlight.
    #   * volume_max_steps only bites on the thin structured layer.
    scene.cycles.volume_bounces = max(scene.cycles.volume_bounces, 2)
    scene.cycles.volume_max_steps = max(scene.cycles.volume_max_steps, 1024)
    # 11.2  Indirect clamping, and why this module has an opinion about it.
    # Cycles ships sample_clamp_indirect = 10.0, which assumes a scene referenced near
    # 1.0.  This world is referenced near 100: a sunlit white surface renders at 38 and
    # a sunlit cloud flank at ~50, so the default would silently crush the film's whole
    # indirect budget.  That is a direct consequence of the absolute-scale decision
    # (build_sky.md 6.1), so it is fixed here — but ONLY if it is still at the default,
    # because a deliberate value set by whoever owns the render recipe must survive.
    if abs(scene.cycles.sample_clamp_indirect - 10.0) < 1e-6:
        scene.cycles.sample_clamp_indirect = 200.0
        log("raised sample_clamp_indirect 10.0 -> 200.0 (this world is referenced "
            "near 100, not near 1; 200 still catches fireflies)")

    others = [o for o in scene.objects
              if o.type == 'LIGHT' and o.data.type == 'SUN'
              and not o.name.startswith(PFX)]
    if others:
        log("WARNING: %d other SUN lamp(s) in the scene (%s). This module owns THE sun;"
            " a second one breaks the one-light law." % (len(others),
                                                         [o.name for o in others]))

    tris = sum(len(o.data.polygons) * 2 for o in coll.objects if o.type == 'MESH')
    summary = dict(
        module="build_sky",
        collection=COLL,
        purged=purged,
        objects=len(coll.objects),
        triangles=tris,
        world=world.name,
        sun=dict(direction=tuple(round(v, 6) for v in SUN_DIR),
                 elevation_deg=round(math.degrees(SUN_ELEV), 4),
                 bearing_deg=round(math.degrees(SUN_BEARING), 4),
                 shadow_ratio=round(SHADOW_RATIO, 4),
                 energy=SUN_ENERGY, color=SUN_COLOR,
                 angular_diameter_deg=round(math.degrees(SUN_ANGULAR_DIAM), 4),
                 irradiance=SUN_IRRADIANCE),
        sky=dict(model="MULTIPLE_SCATTERING", air=SKY_AIR, aerosol=SKY_AEROSOL,
                 ozone=SKY_OZONE, sun_rotation_deg=round(
                     math.degrees(SKY_SUN_ROTATION), 4),
                 nodes=len(world.node_tree.nodes),
                 decks=list(CLOUD.keys())),
        atmosphere=dict(visual_range_m=VISUAL_RANGE_M,
                        sigma_ext_550=SIGMA_EXT_550,
                        sigma_rayleigh_550=SIGMA_RAYLEIGH_550,
                        sigma_aerosol_550=SIGMA_AEROSOL_550,
                        column_z=(SLAB_BOTTOM, SLAB_TOP), half_m=SLAB_HALF,
                        boundary_top=BOUNDARY_TOP,
                        homogeneous=True, strata_enabled=STRATA_ENABLED,
                        transmittance=dict(
                            m600=round(math.exp(-SIGMA_EXT_550 * 600), 4),
                            km3=round(math.exp(-SIGMA_EXT_550 * 3000), 4),
                            km10=round(math.exp(-SIGMA_EXT_550 * 10000), 4))),
        handoff=dict(
            camera_clip_end_min=50000.0,
            reference_exposure_exterior=REFERENCE_EXPOSURE_EXTERIOR,
            sky_irradiance=SKY_IRRADIANCE,
            direct_to_diffuse=DIRECT_TO_DIFFUSE,
            bind_camera="call build_sky.bind_camera(cam) once the rig exists",
            note="this module never writes scene.view_settings; exposure is the "
                 "camera's"),
        seconds=round(time.time() - t0, 2),
    )
    log("built in %.2f s: %d objects, %d tris, world '%s'"
        % (summary["seconds"], summary["objects"], tris, world.name))
    log("HAND-OFF: camera clip_end >= 50 km; reference exterior exposure %.3f stops"
        % REFERENCE_EXPOSURE_EXTERIOR)
    return summary


# ==================================================================================
# 12.  CALIBRATION  (the measurement that produced section 3's constants)
# ==================================================================================

def calibrate(samples=3000):
    """Re-derive SUN_IRRADIANCE from the sky model and check the baked constants.

    Kept in the module rather than in a scratch script because the constants in
    section 3 are only trustworthy for as long as the sky parameters in section 2 hold.
    Change an aerosol value and this is the thing that tells you the sun moved.
    """
    import numpy as np
    scene = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.sample_clamp_indirect = 0.0
    scene.render.resolution_x = scene.render.resolution_y = 48
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    scene.view_settings.view_transform = 'Standard'

    me = bpy.data.meshes.new("CAL_plane")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400.0)
    bm.to_mesh(me)
    bm.free()
    po = bpy.data.objects.new("CAL_plane", me)
    scene.collection.objects.link(po)
    mat = bpy.data.materials.new("CAL_white")
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.0
    me.materials.append(mat)
    cd = bpy.data.cameras.new("CAL_cam")
    cd.lens = 50.0
    cd.clip_end = 1e7
    co = bpy.data.objects.new("CAL_cam", cd)
    scene.collection.objects.link(co)
    co.location = (0, 0, 40)
    scene.camera = co

    w = bpy.data.worlds.new("CAL_world")
    scene.world = w
    tree = w.node_tree
    bg = [n for n in tree.nodes if n.type == 'BACKGROUND'][0]
    sky = tree.nodes.new("ShaderNodeTexSky")
    tree.links.new(sky.outputs["Color"], bg.inputs[0])
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_size = SUN_ANGULAR_DIAM
    sky.sun_elevation = SUN_ELEV
    sky.sun_rotation = SKY_SUN_ROTATION
    sky.altitude = SKY_ALTITUDE
    sky.air_density = SKY_AIR
    sky.aerosol_density = SKY_AEROSOL
    sky.ozone_density = SKY_OZONE

    tmp = os.path.join(RENDER_DIR, "_calib.exr")
    os.makedirs(RENDER_DIR, exist_ok=True)

    def shoot():
        scene.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        import OpenImageIO as oiio
        i = oiio.ImageInput.open(tmp)
        s = i.spec()
        a = np.array(i.read_image(format='float')).reshape(
            s.height, s.width, s.nchannels)[:, :, :3]
        i.close()
        return a[6:-6, 6:-6].reshape(-1, 3).mean(0)

    sky.sun_disc = True
    A = shoot()
    sky.sun_disc = False
    B = shoot()
    En = (A - B) * math.pi / math.sin(SUN_ELEV)
    log("calibrate: E_normal = %s   (baked %s)"
        % (np.round(En, 3), tuple(round(v, 3) for v in SUN_IRRADIANCE)))
    log("calibrate: sky irradiance = %s   (baked %s)"
        % (np.round(B * math.pi, 3), tuple(round(v, 3) for v in SKY_IRRADIANCE)))
    drift = max(abs(En[i] - SUN_IRRADIANCE[i]) / SUN_IRRADIANCE[i] for i in range(3))
    log("calibrate: worst-channel drift %.3f %%  -> %s"
        % (100 * drift, "OK" if drift < 0.02 else "RE-BAKE SECTION 3"))
    return dict(E_normal=[float(v) for v in En],
                sky_irradiance=[float(v) for v in (B * math.pi)],
                drift=float(drift))


# ==================================================================================
# 13.  TEST RENDER HARNESS
# ==================================================================================
# Scaffolding only.  Everything it makes is prefixed SKYTEST_ and build() creates none
# of it.  The point of these frames is to check the four things that can actually be
# wrong with a sky: the sun is in the right place, the shadow is the right length and
# direction, the air has depth, and nothing bands.

TEST_PFX = "SKYTEST_"


def _clear_test():
    """Clear the stage.

    This removes EVERY object that is neither this module's nor this harness's — and
    it has to, because `blender -b --factory-startup` opens with a 2 m Cube at the
    origin and a 1000 W point light 6 m above it.  Both were silently present in the
    first round of test frames: the Cube swallowed the 1 m shadow gnomon (which is why
    a "cube" appeared to have a black top face), its own shadow was measured as the
    gnomon's and came out 30% long, and the point light polluted every ambient reading.
    The harness now owns the stage explicitly.  build() does NOT do this — it is meant
    to be called into the assembled world and touches nothing but its own datablocks.
    """
    for ob in list(bpy.context.scene.objects):
        if not (ob.name.startswith(TEST_PFX) or ob.name.startswith(PFX)):
            bpy.data.objects.remove(ob, do_unlink=True)
    for coll_ in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        for d in list(coll_):
            if d.name.startswith(TEST_PFX) or (d.users == 0
                                               and not d.name.startswith(PFX)):
                try:
                    coll_.remove(d)
                except Exception:
                    pass
    stray = [o.name for o in bpy.context.scene.objects
             if o.type == 'LIGHT' and not o.name.startswith(PFX)]
    assert not stray, "stage not clear: stray lights %s" % stray


def _mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(TEST_PFX + name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0
    return m


def _mesh_obj(name, bm, mat, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(TEST_PFX + name)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(TEST_PFX + name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_test_scene(kind="depth"):
    """A stand-in world with known dimensions, so the sky can be judged against maths.

    'depth'  : ground + 3 m posts at 100/300/1000/3000/10000/25000 m along the
               anti-solar axis (the Beat-6 look direction) + the 4.51x shadow gnomon.
    'bare'   : nothing but ground, for dome and banding frames.
    """
    _clear_test()
    sc = bpy.context.scene
    ground = _mat("ground", (0.115, 0.125, 0.105), 0.95)   # dry summer grass, linear
    conc = _mat("conc", (0.34, 0.335, 0.325), 0.80)
    white = _mat("white", (0.80, 0.80, 0.80), 0.90)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60000.0)
    _mesh_obj("ground", bm, ground)

    if kind == "bare":
        return

    # the gnomon: a 1.000 m cube whose shadow must run 4.522 m toward (-0.518, +0.828)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
    _mesh_obj("gnomon", bm, white, loc=(0, 0, 0))

    # Depth ladder.  Pairs of slabs — one concrete, one white — at six ranges along the
    # anti-solar axis, each scaled so it subtends the SAME angle from the camera and
    # each offset laterally by an angle that grows with range, so they form a receding
    # staircase instead of hiding behind one another (the first version put them on one
    # radial line and the far five were invisible).  Equal angular size is the point:
    # any difference between them in a frame is aerial perspective and nothing else.
    for i, d in enumerate((100, 300, 1000, 3000, 10000, 25000)):
        s = d / 100.0                      # keeps angular size constant
        lat = math.radians(2.6 * i)        # fan them out to the left
        ux, uy = -math.cos(math.radians(15.0) + lat), math.sin(math.radians(15.0) + lat)
        for tag, mat, side in (("A", conc, 0.0), ("B", white, 2.2 * s)):
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(3.0 * s, 3.0 * s, 12.0 * s), verts=bm.verts)
            bmesh.ops.translate(bm, vec=(0, 0, 6.0 * s), verts=bm.verts)
            _mesh_obj("post%s%d" % (tag, d), bm, mat,
                      loc=(d * ux - uy * side, d * uy + ux * side, 0))


TEST_VIEWS = {
    # name: (loc, look_at | None, lens, panorama, res_scale, samples, note)
    "dome": ((0, 0, 4.0), None, None, True, 1.0, 220,
             "full 360 equirect: every deck, the disc, the horizon, in one image"),
    "into_sun": ((0, 0, 2.4), (SUN_DIR.x * 900, SUN_DIR.y * 900, SUN_DIR.z * 900),
                 24.0, False, 1.0, 260,
                 "straight into the 12.5 deg sun: disc, aureole, haze glow"),
    "beat6": ((594.19, 16.05, 140.0), (-40.0, 200.0, 40.0), 18.75, False, 1.0, 300,
              "the Beat-6 hold station and lens, looking back down the world"),
    "away": ((0, 0, 2.0), (-950.0, 254.0, 60.0), 35.0, False, 1.0, 260,
             "anti-solar: the depth ladder and the blue end of aerial perspective"),
    "shadow": ((7.5, 7.0, 3.2), (0, 1.6, 0.4), 35.0, False, 1.0, 200,
               "the 1 m gnomon: shadow length and bearing against the spec"),
    "banding": ((0, 0, 2.0), (-260.0, 420.0, 190.0), 50.0, False, 1.0, 400,
                "clean gradient, 4K, for the banding gate"),
}


def render_test(name, out_dir=RENDER_DIR, res=(1920, 1080), samples=None,
                denoise=True, device="GPU"):
    sc = bpy.context.scene
    loc, look, lens, pano, rs, smp, note = TEST_VIEWS[name]
    build_test_scene("bare" if name in ("dome", "banding") else "depth")

    cd = bpy.data.cameras.new(TEST_PFX + "cam_" + name)
    cd.clip_start = 0.05
    cd.clip_end = 200000.0        # the haze slab is 80 km across; clipping it truncates
    if pano:                      # the airlight and the horizon goes hard-edged
        cd.type = 'PANO'
        cd.panorama_type = 'EQUIRECTANGULAR'
    else:
        cd.lens = lens
    co = bpy.data.objects.new(TEST_PFX + "cam_" + name, cd)
    sc.collection.objects.link(co)
    co.location = loc
    if look is not None:
        d = (Vector(look) - Vector(loc)).normalized()
        co.rotation_mode = 'QUATERNION'
        co.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    else:
        co.rotation_euler = (math.radians(90), 0, math.radians(180.0))
    sc.camera = co
    bind_camera(co)

    sc.render.engine = 'CYCLES'
    _gpu()
    sc.cycles.device = device
    sc.cycles.samples = samples or smp
    sc.cycles.use_denoising = denoise
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.008
    sc.cycles.sample_clamp_indirect = 0.0
    sc.cycles.volume_bounces = max(sc.cycles.volume_bounces, 2)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.dither_intensity = 1.0
    # The exposure this module publishes, applied HERE only so the test frames are
    # legible.  build() never writes it.
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = REFERENCE_EXPOSURE_EXTERIOR

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sky_%s.png" % name)
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    log("rendered %-9s %4dx%-4d %4d spp  %6.1f s  -> %s   (%s)"
        % (name, res[0], res[1], sc.cycles.samples, time.time() - t0, path, note))
    return path


# ==================================================================================
# 13b.  VERIFICATION GATES
# ==================================================================================
# Four things can be wrong with a sky and none of them is visible by eye at 1080p, so
# each one gets a number and a tolerance.  Run with  -- --verify.

def _tempdir():
    """Keep Cycles' tile cache off /tmp.

    On this box /tmp is a 5.9 GB tmpfs already at 92% full, and a 3840x2160 Cycles
    render spills tiles to Blender's temporary directory, which defaults there.  The
    4K banding frame died with "Error writing tile to file" until this existed.
    """
    d = os.path.join(RENDER_DIR, "_tmp")
    os.makedirs(d, exist_ok=True)
    bpy.context.preferences.filepaths.temporary_directory = d
    return d


def _gpu():
    _tempdir()
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == "CUDA")
        return "GPU"
    except Exception:
        return "CPU"


def _lambert(name, size, loc, albedo=0.8):
    me = bpy.data.meshes.new(TEST_PFX + name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, size[2] * 0.5), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new(TEST_PFX + name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1.0)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.0
    me.materials.append(m)
    ob = bpy.data.objects.new(TEST_PFX + name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def verify(samples=128, quiet=False):
    import numpy as np
    import OpenImageIO as oiio
    sc = bpy.context.scene
    out = {}
    build()
    build_test_scene("bare")
    sc.render.engine = 'CYCLES'
    sc.cycles.device = _gpu()
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.volume_bounces = 2
    sc.cycles.sample_clamp_indirect = 0.0
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Standard'
    os.makedirs(RENDER_DIR, exist_ok=True)
    tmp = os.path.join(RENDER_DIR, "_verify.exr")

    def shoot():
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        i = oiio.ImageInput.open(tmp)
        sp = i.spec()
        a = np.array(i.read_image(format='float')).reshape(
            sp.height, sp.width, sp.nchannels)[:, :, :3]
        i.close()
        return a

    cd = bpy.data.cameras.new(TEST_PFX + "vcam")
    cd.clip_end = 200000.0
    co = bpy.data.objects.new(TEST_PFX + "vcam", cd)
    sc.collection.objects.link(co)
    sc.camera = co

    def aim(pos, tgt):
        co.location = pos
        d = (Vector(tgt) - Vector(pos)).normalized()
        co.rotation_mode = 'QUATERNION'
        co.rotation_quaternion = (-d).to_track_quat('Z', 'Y')

    # --- G1  face radiances against the Lambert prediction -------------------------
    # If the sun's energy, colour or direction were wrong this is where it shows, in
    # absolute numbers, before anything subjective is looked at.  Each face is shot
    # ON AXIS so the sample is one face and not the vertical corner between two — the
    # first version framed the corner and the "error" was in the prediction, not the
    # render.  Predicted direct radiance of a Lambert face is
    #     L = albedo/pi * E_normal * max(0, n . s)
    # and everything above that is ambient: sky + haze airlight + ground bounce.
    cube = _lambert("vcube", (2.0, 2.0, 2.0), (0, 0, 0))
    alb = 0.8
    FACES = (("top",   (0, 0, 1), (0.0, 0.0, 16.0)),
             ("east",  (1, 0, 0), (11.0, 0.0, 1.0)),
             ("south", (0, -1, 0), (0.0, -11.0, 1.0)),
             ("north", (0, 1, 0), (0.0, 11.0, 1.0)))
    cd.type = 'PERSP'
    cd.lens = 85.0
    sc.render.resolution_x = sc.render.resolution_y = 320
    out["faces"] = {}
    if not quiet:
        log("G1 face radiance, 2 m Lambert cube albedo 0.8 (units: Blender sky model):")
        log("   face    n.s      measured RGB              direct-only pred   ambient")
    for tag, n_, pos in FACES:
        aim(pos, (0, 0, 1.0))
        a = shoot()
        m = a[150:170, 150:170].reshape(-1, 3).mean(0)
        ns = max(0.0, Vector(n_).dot(SUN_DIR))
        pred = np.array(SUN_IRRADIANCE) * (alb / math.pi) * ns
        amb = m - pred
        out["faces"][tag] = dict(n_dot_s=round(ns, 4),
                                 measured=[round(float(v), 3) for v in m],
                                 direct_prediction=[round(float(v), 3) for v in pred],
                                 ambient=[round(float(v), 3) for v in amb])
        if not quiet:
            log("   %-6s %6.4f   %-24s  %-18s %s"
                % (tag, ns, np.round(m, 2), np.round(pred, 2), np.round(amb, 2)))
    bpy.data.objects.remove(cube, do_unlink=True)

    # The single most useful number that falls out of G1: the diffuse-to-direct ratio
    # on a horizontal surface, WITH the haze in place.  It is the one quantity for
    # which real measured values at a 12.5 deg solar elevation are common knowledge —
    # DNI ~ 500 W/m^2, DHI ~ 90-120 W/m^2, so diffuse / (DNI sin h) lands at 0.8-1.2 for
    # clear-to-hazy air.  It is also the number that would expose double counting
    # between the sky model's own aerosol column and SKY_Atmosphere's.
    amb_top = np.array(out["faces"]["top"]["ambient"])
    diffuse = amb_top * math.pi / alb
    direct_h = np.array(SUN_IRRADIANCE) * math.sin(SUN_ELEV)
    ratio = float(diffuse.mean() / direct_h.mean())
    out["diffuse_over_direct_horizontal"] = round(ratio, 3)
    out["diffuse_irradiance_with_haze"] = [round(float(v), 3) for v in diffuse]
    if not quiet:
        log("   diffuse irradiance with haze %s  vs direct-horizontal %s"
            % (np.round(diffuse, 2), np.round(direct_h, 2)))
        log("   diffuse/direct-horizontal = %.2f  (real sky at 12.5 deg: 0.8-1.2)"
            "  -> %s" % (ratio, "PASS" if 0.7 < ratio < 1.4 else "FAIL"))

    # --- G2  shadow length and bearing ---------------------------------------------
    # A 1.000 m post, shot orthographically from straight above so a pixel is a metre
    # scaled, then PROFILED along the expected shadow ray.  A global dark-pixel
    # threshold does not work: the shadow of a thin post is 0.1% of the frame, so any
    # percentile-based threshold lands inside the render noise of the lit ground and
    # returns a frame corner.  Walk the ray instead.
    gn = _lambert("vgnomon", (0.10, 0.10, 1.0), (0, 0, 0))
    cd.type = 'ORTHO'
    cd.ortho_scale = 13.0
    co.rotation_mode = 'XYZ'
    co.rotation_euler = (0, 0, 0)
    co.location = (0, 0, 90)
    sc.render.resolution_x = sc.render.resolution_y = 1400
    a = shoot()
    L = a.mean(2)
    mpp = 13.0 / 1400.0

    def at(wx_, wy_):
        ix = (wx_ + 6.5) / mpp - 0.5
        iy = (6.5 - wy_) / mpp - 0.5        # OIIO row 0 is the TOP row = +Y
        i0, j0 = int(np.clip(ix, 0, 1398)), int(np.clip(iy, 0, 1398))
        fx, fy = ix - i0, iy - j0
        return float((L[j0, i0] * (1 - fx) + L[j0, i0 + 1] * fx) * (1 - fy) +
                     (L[j0 + 1, i0] * (1 - fx) + L[j0 + 1, i0 + 1] * fx) * fy)

    exp_bearing = math.degrees(math.atan2(-SUN_DIR.y, -SUN_DIR.x))

    def ray(bear_deg, s):
        t = math.radians(bear_deg)
        return at(math.cos(t) * s, math.sin(t) * s)

    yy, xx = np.mgrid[0:1400, 0:1400]
    far = np.hypot((xx + 0.5) * mpp - 6.5, 6.5 - (yy + 0.5) * mpp) > 8.0
    lit = float(np.median(L[far]))
    floor = float(np.median([ray(exp_bearing, s)
                             for s in np.linspace(0.4, 2.4, 60)]))
    thr = 0.5 * (lit + floor)
    # bearing: the darkest direction in a +-8 deg fan at half the expected length
    fan = np.arange(exp_bearing - 8.0, exp_bearing + 8.0, 0.02)
    prof = np.array([ray(b, SHADOW_RATIO * 0.5) for b in fan])
    dark = fan[prof < thr]
    bearing = float(dark.mean()) if len(dark) else float(fan[int(np.argmin(prof))])
    # Length: walk out and stop at the FIRST crossing, confirmed by 40 mm of samples
    # staying above the threshold.  Taking the last sub-threshold sample instead reads
    # a single dark pixel somewhere out near the frame edge and doubles the answer.
    # The walk is also clamped inside the frame, because at() clamps its indices and
    # would otherwise keep resampling the edge pixel forever.
    tb = math.radians(bearing)
    lim = 6.3 / max(abs(math.cos(tb)), abs(math.sin(tb)))
    ss = np.arange(0.4, min(1.8 * SHADOW_RATIO, lim), 0.002)
    vals = np.array([ray(bearing, s) for s in ss])
    length, run = float(ss[-1]), 0
    for idx, v in enumerate(vals):
        if v >= thr:
            run += 1
            if run >= 20:
                length = float(ss[idx - 19])
                break
        else:
            run = 0
    r = np.array([length])
    k = 0
    out["shadow"] = dict(length_m=round(float(r[k]), 4),
                         expected_m=round(SHADOW_RATIO, 4),
                         length_err_pct=round(100 * (r[k] / SHADOW_RATIO - 1), 3),
                         bearing_deg=round(bearing, 3),
                         expected_bearing_deg=round(exp_bearing, 3),
                         bearing_err_deg=round(bearing - exp_bearing, 3))
    if not quiet:
        log("G2 shadow: %.3f m vs %.3f m (%+.2f%%), bearing %.2f deg vs %.2f deg "
            "(%+.2f deg)  -> %s"
            % (r[k], SHADOW_RATIO, out["shadow"]["length_err_pct"], bearing,
               exp_bearing, out["shadow"]["bearing_err_deg"],
               "PASS" if abs(out["shadow"]["length_err_pct"]) < 3.0
               and abs(out["shadow"]["bearing_err_deg"]) < 1.5 else "FAIL"))
    bpy.data.objects.remove(gn, do_unlink=True)

    # --- G3  aerial perspective ladder ---------------------------------------------
    # Identical albedo-0.8 cards, each scaled to subtend the same angle, at five ranges
    # along the anti-solar axis.  Measured radiance is checked against
    #     L(d) = L(0) * exp(-sigma d)  +  airlight(d)
    # by solving for the airlight and confirming it rises monotonically to a plateau.
    cd.type = 'PERSP'
    cd.lens = 50.0
    co.rotation_mode = 'QUATERNION'
    sc.render.resolution_x = sc.render.resolution_y = 320
    ladder = []
    for d in (50, 500, 2000, 8000, 25000):
        w = max(4.0, d * 0.05)
        c = _lambert("vcard%d" % d, (w * 0.04, w, w),
                     (-d * 0.9659, d * 0.2588, 0))
        aim((0, 0, w * 0.5), (-d * 0.9659, d * 0.2588, w * 0.5))
        a = shoot()
        card = a[150:170, 150:170].reshape(-1, 3).mean(0)
        ladder.append((d, [round(float(v), 3) for v in card],
                       round(math.exp(-SIGMA_EXT_550 * d), 4)))
        bpy.data.objects.remove(c, do_unlink=True)
    L0 = np.array(ladder[0][1])
    out["ladder"] = []
    if not quiet:
        log("G3 aerial perspective (identical albedo-0.8 cards, equal angular size):")
        log("      range      measured RGB              T(d)    implied airlight")
    for d, rgbv, T in ladder:
        air = np.array(rgbv) - L0 * T
        out["ladder"].append(dict(range_m=d, rgb=rgbv, transmittance=T,
                                  airlight=[round(float(v), 3) for v in air]))
        if not quiet:
            log("   %7d m   %-24s  %.4f  %s"
                % (d, np.round(rgbv, 2), T, np.round(air, 2)))

    # --- G5  the drawn disc must BE the lamp ----------------------------------------
    # The world shader draws the sun and the lamp lights the scene.  If those two ever
    # disagree the film has a sun that is the wrong brightness for its own shadows, and
    # nothing else in the pipeline would catch it.  So: point a 2000 mm lens (1.03 deg
    # of frame) straight up the sun vector and integrate the drawn disc over solid
    # angle.  It must return SUN_IRRADIANCE.
    for o in list(bpy.data.objects):
        if o.name.startswith(TEST_PFX) and o.type == 'MESH':
            o.hide_render = True
    cd.type = 'PERSP'
    cd.lens = 2000.0
    co.location = (0.0, 0.0, 2.0)
    co.rotation_mode = 'QUATERNION'
    co.rotation_quaternion = SUN_DIR.to_track_quat('-Z', 'Y')
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.cycles.samples = 64
    a = shoot()
    hfov = 2.0 * math.atan(18.0 / 2000.0)
    sr_px = (hfov / 512.0) ** 2
    bg = np.median(np.concatenate([a[:24].reshape(-1, 3), a[-24:].reshape(-1, 3)]), 0)
    integ = (a - bg).reshape(-1, 3).sum(0) * sr_px
    err = float(np.max(np.abs(integ - np.array(SUN_IRRADIANCE))
                       / np.array(SUN_IRRADIANCE)))
    out["disc"] = dict(integrated=[round(float(v), 3) for v in integ],
                       lamp=list(SUN_IRRADIANCE), worst_err_pct=round(100 * err, 2))
    if not quiet:
        log("G5 drawn disc integrated over solid angle: %s"
            % np.round(integ, 3))
        log("   lamp irradiance                       : %s"
            % np.round(SUN_IRRADIANCE, 3))
        log("   worst-channel disagreement %.2f %%  -> %s"
            % (100 * err, "PASS" if err < 0.05 else "FAIL"))
    sc.cycles.samples = samples

    # --- G4  banding at 4K ----------------------------------------------------------
    # The gate that matters is the 8-bit delivery, so the linear frame is put through
    # the shipping view transform and the resulting column is measured two ways:
    # the longest run of identical codes (a visible band is a long run) and the
    # residual sigma after a smooth fit (noise/mottle above ~0.5 LSB destroys banding).
    for o in list(bpy.data.objects):
        if o.name.startswith(TEST_PFX) and o.type == 'MESH':
            o.hide_render = True
    cd.lens = 50.0
    aim((0, 0, 2.0), (-260.0, 420.0, 190.0))
    sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    sc.render.dither_intensity = 1.0
    # Denoised, because that is the worst case: the denoiser removes exactly the render
    # noise that would otherwise hide banding, so an un-denoised gate passes for the
    # wrong reason.  The film ships denoised, so the gate ships denoised.
    sc.cycles.use_denoising = True
    sc.cycles.samples = max(64, samples)
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = REFERENCE_EXPOSURE_EXTERIOR
    path = os.path.join(RENDER_DIR, "sky_banding.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    i = oiio.ImageInput.open(path)
    sp = i.spec()
    img = np.array(i.read_image(format='uint8')).reshape(
        sp.height, sp.width, sp.nchannels)[:, :, :3]
    i.close()
    # The gate is measured on a SINGLE-PIXEL column, not on an averaged strip.  The
    # first version averaged 240 columns, which cancels the dither — the very thing
    # that hides the staircase — and then reported the staircase as a failure.  What a
    # viewer sees is the displayed pixels, so that is what gets measured; the averaged
    # figure is kept as a diagnostic because it reports the underlying gradient slope.
    k = 41

    def stats(v):
        best, cur = 1, 1
        q = v.round().astype(int)
        for j in range(1, len(q)):
            cur = cur + 1 if q[j] == q[j - 1] else 1
            best = max(best, cur)
        sm = np.convolve(v.astype(float), np.ones(k) / k, mode='valid')
        return best, float((v[k // 2:len(v) - k // 2] - sm).std())

    col = img[:, 1900, 1].astype(np.float64)
    avg = img[:, 1800:2040, 1].astype(np.float64).mean(1)
    run_px, sigma = stats(col)
    run_avg, sigma_avg = stats(avg)
    span = int(col.max() - col.min())
    ok = (sigma > 0.40) and (run_px < 24)
    out["banding"] = dict(
        png=path, codes_spanned=span,
        px_per_code=round(len(col) / max(1, span), 2),
        longest_flat_run_px=int(run_px), residual_sigma_lsb=round(sigma, 3),
        averaged_diag=dict(longest_flat_run_px=int(run_avg),
                           residual_sigma_lsb=round(sigma_avg, 3)),
        passed=bool(ok))
    # Visual evidence, not just a number: a 26x contrast stretch of a smooth patch.
    # If there are contours in the gradient, this is where they become undeniable.
    crop = img[300:700, 1700:2500].astype(np.float64)
    st = np.clip((crop - crop.mean()) * 26.0 + 128.0, 0, 255).astype(np.uint8)
    cpath = os.path.join(RENDER_DIR, "sky_banding_crop26x.png")
    o = oiio.ImageOutput.create(cpath)
    o.open(cpath, oiio.ImageSpec(800, 400, 3, 'uint8'))
    o.write_image(st)
    o.close()
    out["banding"]["stretch_png"] = cpath
    if not quiet:
        log("G4 banding, 3840x2160, AgX, 8-bit, dither 1.0:")
        log("   gradient spans %d codes over %d px (%.1f px/code)"
            % (span, len(col), out["banding"]["px_per_code"]))
        log("   single-pixel column : longest flat run %d px, residual sigma %.3f LSB"
            % (run_px, sigma))
        log("   240-column average  : longest flat run %d px, residual sigma %.3f LSB"
            "   (diagnostic: this cancels the dither)" % (run_avg, sigma_avg))
        log("   -> %s   evidence: %s" % ("PASS" if ok else "FAIL", cpath))
    sc.render.image_settings.color_depth = '16'
    return out


# ==================================================================================
# 14.  ENTRY POINT
# ==================================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", default=None,
                    help="comma list of %s, or 'all'" % list(TEST_VIEWS))
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--device", default="GPU")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    if a.calibrate:
        r = calibrate()
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
        return
    if a.verify:
        r = verify(samples=a.samples or 128)
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
        return

    s = build()
    # idempotence gate: building twice must be a no-op, and it is cheap to prove
    s2 = build()
    assert s2["objects"] == s["objects"], "not idempotent"
    log("idempotence: second build purged %d datablocks, same %d objects"
        % (s2["purged"], s2["objects"]))
    if a.json:
        json.dump(s, open(a.json, "w"), indent=1)

    if a.render:
        names = list(TEST_VIEWS) if a.render == "all" else a.render.split(",")
        for n in names:
            render_test(n.strip(), res=tuple(a.res), samples=a.samples,
                        device=a.device)
    print(">> STAGE RESULT: BUILD_SKY_OK")


if __name__ == "__main__":
    main()
