#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-372..R2-376.  BUILD A REAL ROOF ON THE SHOWROOM, INTO A FILM BLEND.

    /opt/blender-5.2.0-linux-x64/blender -b render/film14_breach_r6.blend \
        --factory-startup -P tools/r2366_roof_build.py -- \
        --out render/r2366_roof_after.blend --report work/r2366/build.json

    # measure only, no build -- the BEFORE reading on the same instrument
    ... -P tools/r2366_roof_build.py -- --no-build --report work/r2366/before.json

    # re-open a saved file and re-measure it
    ... -b render/r2366_roof_after.blend -P tools/r2366_roof_build.py -- --verify


WHY THIS IS A POST-APPEND TOOL AND NOT A FIX AT SOURCE
======================================================
The roof is NOT round-2 geometry. `Ceiling` is a literal cuboid emitted by
`~/opus5-car-render/build/s02_showroom.py:490` `build_shell()` --
8 vertices, 6 quads, top face ONE QUAD OF 686 m^2 -- carrying `CeilingMat`,
a two-node flat Principled from `build/s03_materials.py:207`. It reaches the
film through `tools/build_film_scene.py`'s append of `world/car_anim.blend`'s
SHOWROOM collection, at identity.

`~/opus5-car-render` IS READ-ONLY (project law 1), so the source
cannot be corrected. `tools/add_dais_ramp.py` established the shape of the
answer for exactly this situation and its argument is repeated here: open the
film blend that already exists, build into it, ASSERT the datum it is landing
against rather than trusting it, and save somewhere new.

`CeilingMat` IS NOT TOUCHED, AND THAT IS DELIBERATE. It is also on
`Cove_Coffer_0/1` and `WallLine_*Fin_0/1` -- the INTERIOR. The `Ceiling`
cuboid's UNDERSIDE at z = 6.200 is the showroom's interior ceiling, visible in
beat 5, and putting roof treatment on it would create a new defect. The roof
built here sits ENTIRELY ABOVE z = 6.500 as a separate warm-roof buildup, in
its own collection, with its own materials. Nothing round-1 is edited.


WHAT THE ROOF HAS TO DO, MEASURED RATHER THAN ASSUMED
=====================================================
`tools/r2366_surface_visibility.py` projected the roof rectangle through all
2,978 camera poses. The roof top is visible on 151 frames, ALL in beat 6, all
at 594-610 m. It is NEVER near-field. At f2978 the four corners land at

    (-15.25,-11.25) -> u 1788 v 949      (+15.25,-11.25) -> u 1771 v 1036
    (-15.25,+11.25) -> u 2073 v 951      (+15.25,+11.25) -> u 2069 v 1038

so the whole 686 m^2 roof is a 302 x 89 px quadrilateral, and THE SCALE IS
STRONGLY ANISOTROPIC -- a fact the single number "352 mm/px" hides:

    along y (across the frame)   22.5 m over 285 px  ->   79 mm / px
    along x (into the frame)     30.5 m over  88 px  ->  347 mm / px

347 mm/px is the foreshortened axis and is the one that limits: a feature that
varies along x needs to be >= 0.7 m to occupy 2 px. A feature that varies along
y is resolved to 0.16 m. So the read is designed to come from FORM AND OBJECTS
at 0.7-10 m, with the finer stages running in y where they are resolved:

  * A 1.100 m PARAPET with an oversailing coping. At a 12.47 deg sun this is
    the single strongest cue available: the -y parapet throws a 4.12 m shadow
    band ACROSS the roof (52 px of the 285), the coping catches a highlight the
    membrane cannot, and the near parapet occludes 4.94 m of deck -- three
    different, unmistakable signals from one 1.1 m upstand.
  * FALLS. Four valley gutters at y = -10.20 / -3.55 / +3.55 / +10.20 with
    1:40 cross-falls to ridges between them, and a 1:100 fall along x to eight
    outlets. Six alternating tonal bands, each ~45 px wide, differing by 19 %.
  * ROOF PLANT, which is where most of the read is. A 1.4 m tall unit is 18 px
    of screen and throws a 6.3 m shadow -- up to 80 px of unmistakable, moving,
    correctly-directed dark. 36 objects, every one a unique mesh.
  * MEMBRANE BAYS at 2.00 m, laps running in y so the pitch lands at 5.8 px --
    above the 4 px where a repeating pattern starts to alias across a 151-frame
    move, and BUILT AS REAL VERTICES, not as a bump.

SUB-PIXEL DETAIL EXISTS UNDERNEATH (emboss grain at 25 mm, roller ripple at
300 mm) BUT IS EXPLICITLY NOT WHAT CARRIES THE FRAME. It is there so the
surface is a material rather than a plane, and it is declared as such in the
relief table below.


THE RELIEF LAW, AND THE TRAP
============================
Amplitudes are DERIVED from `world/itemkit.py`'s law
(`relief_amplitude_for(m, wavelength_m)`), never chosen in millimetres --
section 5b, and three rendered-and-rejected amplitude sets.

Defect R2-060 is the trap: a flat 4-vertex quad painted with stripes aligned to
the light scored dip 0.6308 against 0.6082 for real 2 mm ribs. ALBEDO VARIATION
IS NOT RELIEF, and passing a relief check is not the same as passing it for the
right reason. So every stage that has to carry the frame here is REAL GEOMETRY
(falls, bay camber, cross-lap welts, ponding, parapet, coping, plant) and only
the two sub-pixel stages are bump. `tools/r2366_roof_pvg.py` then runs the
`relief_paint_vs_geometry.py` separation -- same scene, same camera, same
pixel mask, paint forced constant -- and the `truegeo` arm answers it off the
evaluated mesh alone.

Blender 5.2 EXITS 0 ON AN UNCAUGHT SCRIPT EXCEPTION. Judge on `STAGE RESULT`.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy                                                       # noqa: E402
import gate_exit                                                 # noqa: E402
import itemkit as K                                              # noqa: E402
import world_contract as C                                       # noqa: E402
import film_exposure as FX                                       # noqa: E402


# ===========================================================================
# 0.  THE DATUM.  Asserted against the file, never trusted.
# ===========================================================================
DECK_Z = 6.500                 # top of the round-1 structural slab
SOFFIT_Z = 6.200               # its underside -- the INTERIOR ceiling. Untouched.
OUT_X, OUT_Y = 15.25, 11.25    # slab edge = outer face of the walls below
WALL_T = 0.25                  # OUT_* minus the inner face measured in the blend
IN_X, IN_Y = OUT_X - WALL_T, OUT_Y - WALL_T          # 15.00 / 11.00
TOL = 1e-4

PFX = "RRF_"                   # one family, so tools/mesh_reuse.py groups it
COLL = "R2_ShowroomRoof"

# ---- parapet -------------------------------------------------------------
# 1.100 m over the deck. NOT a styling choice: below 1.100 m a roof carrying
# plant needs a separate guardrail, and a 48 mm guardrail tube is 0.14 px at
# this range -- thin geometry that would shimmer across 151 frames for no read.
# The parapet does the same job as form the camera can actually resolve.
PARA_H = 1.040                 # upstand, deck datum -> underside of coping
COPE_T = 0.060                 # coping thickness at its outer edge
COPE_OVER = 0.045              # oversail each side -> the drip shadow line
COPE_FALL = 1.0 / 12.0         # coping falls INWARD, so it drains to the roof
DRIP_H = 0.030                 # downstand under the oversail

PARA_TOP = DECK_Z + PARA_H                      # 7.540
COPE_TOP_OUT = PARA_TOP + COPE_T                # 7.600

# ---- falls ---------------------------------------------------------------
BASE_BUILDUP = 0.075           # membrane + minimum tapered insulation at an outlet
VALLEY_Y = (-10.20, -3.55, 3.55, 10.20)
OUTLET_X = (-7.5, 7.5)
YFALL = 1.0 / 40.0             # cross-fall, the steep end of BS 6229 practice
XFALL = 1.0 / 100.0            # fall along the valleys to the outlets

# ---- membrane ------------------------------------------------------------
BAY_W = 2.00                   # single-ply roll width; laps run in y, WITH the fall
WELT_SIG = 0.18                # cross-lap welt, gaussian sigma
SETTLE_LAM = 5.0               # deck deflection / settlement wavelength

# grid. dx is the tight one: the bay camber varies in x and needs >= 8 samples
# per 2.00 m bay for `geometry_relief_report` to see a slope rather than a step.
DX, DY = 0.100, 0.100


# ===========================================================================
# 1.  THE RELIEF TABLE.  Every amplitude derived, none typed.
# ===========================================================================
def _slope_rad(m_pp):
    return math.radians(K.slope_for_modulation(m_pp))


_SUN_H = np.array(C.SUN_DIR[:2], float)
_SUN_H = _SUN_H / np.linalg.norm(_SUN_H)


def axis_gain(axis):
    """How much of the relief law a stage gets, given WHICH WAY IT RUNS.

    `m = 2 sin(theta) / tan(e)` is derived for a normal tilted in the VERTICAL
    PLANE THROUGH THE SUN. A stage whose gradient runs along a fixed world axis
    only tilts that far toward the sun in azimuth, and delivers

        m_real = m_law * |axis . sun_horizontal|

    At this film's bearing of -57.97 deg that is 0.530 for a gradient in x and
    0.848 for one in y -- a factor of 1.6 between two stages of IDENTICAL
    amplitude and wavelength, purely from which way they were laid. Measured
    the hard way first: the 2.00 m bay camber was cut to the law's 35.3 mm for
    m = 0.50 and `stage_slope_audit` differentiated the built field and
    returned 0.322. The law was not wrong; it was being asked the wrong
    question.
    """
    e = np.array((1.0, 0.0) if axis == "x" else (0.0, 1.0))
    return float(abs(e @ _SUN_H))


def _sin_amp_mm(slope_rad, lam):
    """The peak-to-peak a SINUSOID of wavelength `lam` needs for this slope.

    The law is written for a sinusoid (max slope = pi A / lam). A triangular
    fall and a gaussian welt have the same maximum slope at different
    amplitudes, so each stage is converted to its sinusoid-equivalent amplitude
    before it is handed to `relief_budget` -- otherwise the audit column and the
    built surface would be describing two different things.
    """
    return math.tan(slope_rad) * float(lam) / math.pi * 1000.0


# --- targets, stated as RADIANCE MODULATION -------------------------------
M_BAY = 0.50        # isotropic_macro  (0.35 .. 0.95)
M_WELT = 0.50       # isotropic_macro
M_RIPPLE = 0.50     # isotropic_macro  -- BUMP, sub-pixel, declared as such
M_GRAIN = 0.28      # isotropic_micro  (0.12 .. 0.45) -- BUMP, sub-pixel

# ...corrected for the fact that the laps run in y, so the camber's gradient is
# in x and only 0.530 of the law's tilt is toward the sun; and then CAPPED,
# because a membrane is not free to be any shape that makes a number. 45 mm of
# ballooning over a 2.00 m bay is 2.2 % and is the top of what a mechanically
# fastened single-ply actually does between fastener rows. Asking the law for
# m = 0.50 through a gain of 0.530 wants 66.8 mm, which is not a roof.
BAY_AMP_PHYS_MAX = 0.045
BAY_AMP = min(K.relief_amplitude_for(M_BAY / axis_gain("x"), BAY_W) * 1e-3,
              BAY_AMP_PHYS_MAX)
WELT_LAM = 4.0 * WELT_SIG                                        # 0.72 m
WELT_AMP = math.tan(_slope_rad(M_WELT)) * WELT_SIG * math.sqrt(math.e)
RIPPLE_LAM = 0.30
GRAIN_LAM = 0.025

# form-scale stages: OUTSIDE the texture bands ON PURPOSE, and here is why.
# A roof fall is limited to 1:40 by what water and a squeegee will do; asking
# `relief_budget` to put it in `geometry_fold` (0.60-1.40) would mean a 1:9
# roof, which is not a flat roof. These are FORM, they are reported with their
# real modulation, and the band column says NONE rather than LOW.
RIDGE_HALF = 0.5 * (VALLEY_Y[2] - VALLEY_Y[1])       # 3.55 m, y=0 ridge
FALL_LAM = 2.0 * 3.325                               # 6.65 m, the outer bays
XFALL_LAM = 2.0 * 7.5                                # 15.0 m
SETTLE_M = 0.12                                      # deliberately sub-band
SETTLE_AMP = K.relief_amplitude_for(SETTLE_M, SETTLE_LAM) * 1e-3


def relief_stages():
    """(name, layer, wavelength_m, sinusoid-equivalent amp_mm, band-or-None)."""
    return [
        ("falls_1in40", "GEOM", FALL_LAM,
         _sin_amp_mm(math.atan(YFALL), FALL_LAM), None),
        ("valley_1in100", "GEOM", XFALL_LAM,
         _sin_amp_mm(math.atan(XFALL), XFALL_LAM), None),
        ("bay_camber", "GEOM", BAY_W, BAY_AMP * 1000.0, "isotropic_macro"),
        ("crosslap_welt", "GEOM", WELT_LAM,
         _sin_amp_mm(_slope_rad(M_WELT), WELT_LAM), "isotropic_macro"),
        ("deck_settlement", "GEOM", SETTLE_LAM, SETTLE_AMP * 1000.0, None),
        ("membrane_ripple", "BUMP", RIPPLE_LAM,
         K.relief_amplitude_for(M_RIPPLE, RIPPLE_LAM), "isotropic_macro"),
        ("membrane_grain", "BUMP", GRAIN_LAM,
         K.relief_amplitude_for(M_GRAIN, GRAIN_LAM), "isotropic_micro"),
    ]


# ===========================================================================
# 2.  THE HEIGHT FIELD.  One definition; the deck AND the parapet base use it.
# ===========================================================================
def _bay_index(x):
    return np.floor((np.asarray(x, float) + IN_X) / BAY_W)


def _bay_hash(k, salt):
    """`itemkit.hash01` per BAY, not per sample point.

    There are 15 bays and up to a couple of million sample points; hashing per
    point would call a python-level FNV once per point and make the audit grid
    unaffordable. The values are identical -- the hash is keyed on the integer
    bay index either way -- this only stops it being recomputed 100,000 times
    per bay.
    """
    k = np.asarray(k)
    u = np.unique(k)
    lut = {int(v): K.hash01(int(v), salt) for v in u}
    return np.vectorize(lut.__getitem__, otypes=[float])(k)


def _bay_amp(k):
    """Per-bay camber amplitude. Bays are not identical rolls on a real roof."""
    return BAY_AMP * (0.72 + 0.56 * _bay_hash(k, 9271))


def _welt_x(x):
    """Where the cross-lap sits, as a function of x. WANDERS, NOT STEPS.

    This was `hash01(bay_index)`, which staggered the lap PER BAY -- and a
    per-bay constant is a step function, so the welt jumped up to 1.6 m at every
    2.00 m lap and the membrane acquired a 16 mm vertical cliff. It was
    invisible in the relief table and `stage_slope_audit` caught it outright:
    the welt stage returned slope_max 22.3 deg against a design maximum of 3.2.
    A roll laid by hand wanders; it does not teleport.
    """
    return (K.fbm1(np.asarray(x, float) / 6.0, seed=4457, oct=3) - 0.5) * 1.7


PONDS = [   # (cx, cy, radius_m, depth_m) -- where water actually stands
    (-7.5, -3.55, 2.6, 0.026), (7.5, 3.55, 2.2, 0.021),
    (-7.5, 10.20, 1.7, 0.018), (7.5, -10.20, 1.9, 0.023),
    (-2.6, -6.9, 2.9, 0.015), (10.4, 6.6, 2.4, 0.019),
    (-12.1, 0.4, 1.6, 0.012),
]

# plinths get a back-fall CRICKET on their upslope side so water is shed round
# them rather than dammed behind them. (cx, cy, half_x, half_y, rise)
CRICKETS = [
    (-8.0, 4.75, 2.55, 1.05, 0.048), (-8.0, 0.25, 2.55, 1.05, 0.048),
    (3.5, 10.05, 1.05, 0.90, 0.036), (3.5, 5.95, 1.05, 0.90, 0.036),
    (-2.0, -4.55, 1.45, 0.80, 0.030), (7.4, 7.55, 1.25, 0.80, 0.028),
]


STAGE_NAMES = ("valley_1in100", "falls_1in40", "bay_camber", "crosslap_welt",
               "deck_settlement", "ponding", "crickets")


def buildup(x, y, only=None):
    """Metres of roof buildup above the structural deck at (x, y). Vectorised.

    z_membrane = DECK_Z + buildup(x, y).  Everything is ADDITIVE above the
    round-1 slab, so nothing can z-fight with it and nothing round-1 moves.

    `only` names a subset of `STAGE_NAMES`. That is not a build option -- the
    roof is always built with all of them -- it is what lets `stage_slope_audit`
    differentiate ONE STAGE AT A TIME off the same function the mesh is cut
    from, so the audit cannot drift from the surface the way a second,
    hand-written description of the same field would.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    on = (lambda n: True) if only is None else (lambda n: n in only)
    b = np.full(np.broadcast(x, y).shape, BASE_BUILDUP, float)

    # fall along x: a shallow V to each of the two outlet lines
    if on("valley_1in100"):
        dxo = np.minimum(np.abs(x - OUTLET_X[0]), np.abs(x - OUTLET_X[1]))
        b = b + np.minimum(dxo, 7.5) * XFALL

    # cross-fall: distance from the nearest valley line
    if on("falls_1in40"):
        dv = np.min(np.stack([np.abs(y - v) for v in VALLEY_Y]), axis=0)
        b = b + dv * YFALL

    # membrane bay camber -- REAL GEOMETRY, 2.00 m laps running in y
    k = _bay_index(x)
    if on("bay_camber"):
        u = (x + IN_X) / BAY_W - k
        b = b + 0.5 * _bay_amp(k) * (1.0 - np.cos(2.0 * math.pi * u))

    # cross-lap welts, staggered per bay
    if on("crosslap_welt"):
        yw = _welt_x(x)
        for y0 in (-7.0, 0.0, 7.0):
            b = b + WELT_AMP * np.exp(-((y - (y0 + yw)) / WELT_SIG) ** 2)

    # deck deflection between the structural bays
    if on("deck_settlement"):
        b = b + SETTLE_AMP * (K.fbm2(x / SETTLE_LAM, y / SETTLE_LAM, seed=6311,
                                     oct=3) - 0.5)

    # ponding -- shallow dishes where the falls leave water standing
    if on("ponding"):
        for cx, cy, r, d in PONDS:
            t = np.hypot(x - cx, y - cy) / r
            b = b - d * np.clip(1.0 - t * t, 0.0, 1.0) ** 1.5

    # crickets: back-falls shedding water around the plant plinths
    if not on("crickets"):
        return b
    for cx, cy, hx, hy, rise in CRICKETS:
        t = np.clip(1.0 - np.maximum(np.abs(x - cx) / hx,
                                     np.abs(y - cy) / hy), 0.0, 1.0)
        b = b + rise * t * t
    return b


def stage_slope_audit(step=0.02, half=None):
    """WHAT THE BUILT SURFACE ACTUALLY DOES TO THE LIGHT, stage by stage.

    `relief_budget` answers for an equivalent SINUSOID. A 1:40 triangular fall
    and a gaussian welt are not sinusoids, so the table above is a translation
    and a translation can be wrong. This does not translate: it differentiates
    the SAME height field the deck mesh is cut from, builds the true surface
    normal, and evaluates Lambert against `world_contract.SUN_DIR` directly:

        rel = max(0, n . L) / (n_flat . L)

    and reports the peak-to-peak spread of `rel` -- which IS the radiance
    modulation the relief law is a shortcut for. The two columns are printed
    side by side so the shortcut can be checked rather than trusted.

    Sampled on a 20 mm grid, which resolves the finest GEOMETRIC stage
    (the 0.72 m welt) 36x over and the 2.00 m bay camber 100x over.
    """
    L = np.array(C.SUN_DIR, float)
    L = L / np.linalg.norm(L)
    flat = L[2]
    hx = IN_X if half is None else half
    hy = IN_Y if half is None else half
    xs = np.arange(-hx, hx + 1e-9, step)
    ys = np.arange(-hy, hy + 1e-9, step)
    X, Y = np.meshgrid(xs, ys, indexing="ij")

    def one(only):
        Z = buildup(X, Y, only=only)
        gx, gy = np.gradient(Z, step, step)
        nz = 1.0 / np.sqrt(1.0 + gx * gx + gy * gy)
        rel = np.clip(-gx * nz * L[0] - gy * nz * L[1] + nz * L[2], 0.0,
                      None) / flat
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        return dict(
            slope_max_deg=float(slope.max()),
            slope_rms_deg=float(np.sqrt((slope ** 2).mean())),
            m_pp=float(np.percentile(rel, 99.5) - np.percentile(rel, 0.5)),
            m_rms=float(rel.std() * 2.0 * math.sqrt(2.0)),
            rel_min=float(rel.min()), rel_max=float(rel.max()))

    out = {}
    for s in STAGE_NAMES:
        out[s] = one({s})
    out["ALL"] = one(None)
    return out


# ===========================================================================
# 3.  MATERIALS.  Nine, all procedural, none shared with anything already built.
# ===========================================================================
def _pout(nt, specular=None, **kw):
    """`NT.principled_out` PLUS the socket its kwarg mapping cannot reach.

    `principled_out` maps a kwarg to a socket with `k.replace("_", " ").title()`,
    which turns `specular_ior_level` into `"Specular Ior Level"`. The live socket
    is `"Specular IOR Level"` -- IOR is an initialism and `.title()` lower-cases
    its last two letters -- so the candidate list
    (`specular_ior_level`, `Specular Ior Level`, `SpecularIorLevel`) matches
    nothing and the loop falls through **silently**, leaving the socket at its
    default. Verified against a live 5.2 Principled BSDF, not inferred.

    Ten materials in this file asked for a specular level and ten got 0.5. Same
    family as R2-038: a socket addressed by a name that is one transformation
    away from the real one, with no error. Everything else here goes through
    `pin_named`, which raises.
    """
    b = nt.principled_out(**kw)
    if specular is not None:
        nt.pin_named(b, "Specular IOR Level", specular)
    return b


def _mat_membrane():
    """Weathered light-grey single-ply membrane. The roof field.

    Two BUMP stages only, both sub-pixel at 347 mm/px and declared as such in
    `relief_stages()`. Everything that has to READ is in the mesh.

    Both bumps are driven through a clamped MapRange so the height signal
    genuinely swings 0..1 -- which makes `bump_relief_report`'s conservative
    `height_pp = 1.0` EXACT rather than an over-estimate. A raw Noise swings
    about 0.6 and would make every audited number 1.67x high.
    """
    nt = K.NT(PFX + "Membrane")
    oc = nt.object_coords()
    sep = nt.n("ShaderNodeSeparateXYZ")
    nt.pin(sep, 0, oc)

    # per-bay tone: rolls come off different batches and weather differently
    bay = nt.math("FLOOR", nt.math("DIVIDE", (sep, 0), BAY_W))
    wn = nt.n("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
    nt.pin_named(wn, "W", bay)
    tone = nt.ramp((wn, 1), [(0.0, (0.196, 0.199, 0.196)),
                             (0.35, (0.232, 0.234, 0.228)),
                             (0.70, (0.211, 0.214, 0.210)),
                             (1.0, (0.248, 0.249, 0.240))])

    # soiling: airborne dirt collects in the low ground. `rrf_low` is BAKED
    # FROM THE HEIGHT FIELD, so the paint follows the geometry instead of
    # being an independent invention -- and it is still paint, which is why it
    # is taken away in the `geo` arm.
    low = nt.attr("rrf_low", out=2)
    grime = nt.noise(oc, wavelength_m=2.6, detail=6.0, rough=0.62)
    grime2 = nt.noise(oc, wavelength_m=0.62, detail=4.0, rough=0.50)
    gmix = nt.math("ADD", nt.math("MULTIPLY", grime, 0.70),
                   nt.math("MULTIPLY", grime2, 0.30))
    dirt = nt.maprange(nt.math("ADD", nt.math("MULTIPLY", low, 0.55),
                               nt.math("MULTIPLY", gmix, 0.75)),
                       0.22, 0.92, 0.0, 1.0)
    soiled = nt.cmix(dirt, tone, (0.108, 0.109, 0.101))

    # biological growth in the sheltered gutter runs
    algae = nt.maprange(nt.math("MULTIPLY", low,
                                nt.noise(oc, wavelength_m=1.35, detail=5.0)),
                        0.34, 0.78, 0.0, 0.85)
    base = nt.cmix(algae, soiled, (0.062, 0.076, 0.056))

    # standing water leaves a hard-edged mineral tide line
    pond = nt.attr("rrf_pond", out=2)
    tide = nt.maprange(pond, 0.05, 0.30, 0.0, 1.0)
    base = nt.cmix(nt.math("MULTIPLY", tide, 0.55), base,
                   (0.145, 0.147, 0.140))

    # --- relief. BUMP, sub-pixel, chained fine-onto-coarse ------------------
    rip_h = nt.maprange(nt.noise(oc, wavelength_m=RIPPLE_LAM, detail=3.0,
                                 rough=0.45), 0.30, 0.70, 0.0, 1.0)
    b1 = nt.bump(rip_h, 1.0, modulation_pp=M_RIPPLE, wavelength_m=RIPPLE_LAM,
                 height_pp=1.0)
    grn_h = nt.maprange(nt.vor(oc, wavelength_m=GRAIN_LAM, rand=0.92),
                        0.10, 0.90, 0.0, 1.0)
    b2 = nt.bump(grn_h, 1.0, modulation_pp=M_GRAIN, wavelength_m=GRAIN_LAM,
                 normal=b1, height_pp=1.0)

    rough = nt.maprange(nt.math("SUBTRACT", dirt, nt.math("MULTIPLY", tide, 0.6)),
                        0.0, 1.0, 0.52, 0.83)
    _pout(nt, base_color=base, roughness=rough, metallic=0.0,
                      specular=0.42, normal=b2)
    return nt.m


def _mat_upstand():
    """The membrane turned up the parapet's inner face. Its own weathering:
    a vertical face sheds, so it is cleaner high and streaked low."""
    nt = K.NT(PFX + "Upstand")
    oc = nt.object_coords()
    sep = nt.n("ShaderNodeSeparateXYZ")
    nt.pin(sep, 0, oc)
    h = nt.maprange((sep, 2), -0.45, 0.45, 1.0, 0.0)
    mp = nt.n("ShaderNodeMapping")
    nt.pin_named(mp, "Vector", oc)
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.16)   # a 3-vector, not a colour
    streak = nt.noise((mp, 0), wavelength_m=0.55, detail=6.0, rough=0.60)
    dirt = nt.maprange(nt.math("ADD", nt.math("MULTIPLY", h, 0.7),
                               nt.math("MULTIPLY", streak, 0.6)),
                       0.24, 0.86, 0.0, 1.0)
    base = nt.cmix(dirt, (0.222, 0.224, 0.218), (0.094, 0.095, 0.088))
    hh = nt.maprange(nt.noise(oc, wavelength_m=RIPPLE_LAM * 0.8, detail=3.0),
                     0.30, 0.70, 0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=M_RIPPLE, wavelength_m=RIPPLE_LAM * 0.8,
                 height_pp=1.0)
    _pout(nt, base_color=base, roughness=nt.maprange(dirt, 0, 1, 0.55, 0.80),
                      metallic=0.0, specular=0.42, normal=bp)
    return nt.m


def _mat_coping():
    """PPC aluminium coping. THE LIP THAT CATCHES THE LIGHT.

    Light enough and smooth enough to sit clearly above the membrane's 0.21,
    but only 0.25 metallic -- a mirror coping under a Sky Texture blows out at
    grazing incidence and would be a new defect rather than a fix.
    """
    nt = K.NT(PFX + "Coping")
    oc = nt.object_coords()
    mp = nt.n("ShaderNodeMapping")
    nt.pin_named(mp, "Vector", oc)
    mp.inputs["Scale"].default_value = (0.09, 1.0, 1.0)   # streaks run along the run
    run = nt.noise((mp, 0), wavelength_m=0.42, detail=5.0, rough=0.55)
    base = nt.ramp(run, [(0.30, (0.318, 0.320, 0.316)),
                         (0.55, (0.362, 0.364, 0.358)),
                         (0.82, (0.296, 0.299, 0.300))])
    hh = nt.maprange(nt.noise(oc, wavelength_m=0.085, detail=4.0), 0.32, 0.68,
                     0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.30, wavelength_m=0.085, height_pp=1.0)
    # metallic 0.12, not 0.25: at 0.25 the coping mirrored the Sky Texture at
    # grazing incidence and read as a chrome strip round the building.
    _pout(nt, base_color=base, roughness=nt.maprange(run, 0, 1, 0.38, 0.50),
                      metallic=0.12, specular=0.52, normal=bp)
    return nt.m


def _mat_fascia():
    """The parapet's OUTER face: dark cassette cladding continuing the round-1
    slab edge. Deliberately close to CeilingMat's 0.076 so the joint at
    z = 6.500 reads as a panel line and not as a different building -- but not
    equal to it, because a seamless continuation would hide the parapet."""
    nt = K.NT(PFX + "Fascia")
    oc = nt.object_coords()
    sep = nt.n("ShaderNodeSeparateXYZ")
    nt.pin(sep, 0, oc)
    grain = nt.noise(oc, wavelength_m=0.30, detail=5.0, rough=0.55)
    base = nt.ramp(grain, [(0.32, (0.0705, 0.0712, 0.0748)),
                           (0.60, (0.0902, 0.0910, 0.0946)),
                           (0.86, (0.0788, 0.0796, 0.0830))])
    hh = nt.maprange(grain, 0.32, 0.68, 0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.26, wavelength_m=0.30, height_pp=1.0)
    _pout(nt, base_color=base, roughness=0.52, metallic=0.10,
                      specular=0.5, normal=bp)
    return nt.m


def _mat_plantcase():
    """Powder-coated plant casing. Per-UNIT tone from Object Info -> Random, so
    a bank of condensers is a bank of DIFFERENT condensers without a texture."""
    nt = K.NT(PFX + "PlantCase")
    oc = nt.object_coords()
    oi = nt.n("ShaderNodeObjectInfo")
    tone = nt.ramp((oi, 5), [(0.0, (0.208, 0.214, 0.212)),
                             (0.34, (0.246, 0.250, 0.245)),
                             (0.62, (0.188, 0.196, 0.198)),
                             (1.0, (0.268, 0.268, 0.258))])
    weather = nt.noise(oc, wavelength_m=0.34, detail=6.0, rough=0.58)
    base = nt.cmix(nt.maprange(weather, 0.36, 0.86, 0.0, 0.55), tone,
                   (0.112, 0.110, 0.098))
    hh = nt.maprange(nt.noise(oc, wavelength_m=0.055, detail=4.0), 0.30, 0.70,
                     0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.30, wavelength_m=0.055, height_pp=1.0)
    _pout(nt, base_color=base, roughness=nt.maprange(weather, 0, 1, 0.40, 0.62),
                      metallic=0.20, specular=0.5, normal=bp)
    return nt.m


def _mat_alu():
    """Mill aluminium: cowls, louvre blades, fan guards."""
    nt = K.NT(PFX + "Alu")
    oc = nt.object_coords()
    n = nt.noise(oc, wavelength_m=0.14, detail=6.0, rough=0.55)
    base = nt.ramp(n, [(0.30, (0.402, 0.406, 0.410)), (0.70, (0.472, 0.474, 0.476))])
    hh = nt.maprange(nt.noise(oc, wavelength_m=0.030, detail=4.0), 0.30, 0.70,
                     0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.24, wavelength_m=0.030, height_pp=1.0)
    _pout(nt, base_color=base, roughness=nt.maprange(n, 0, 1, 0.28, 0.44),
                      metallic=0.82, specular=0.5, normal=bp)
    return nt.m


def _mat_galv():
    """Hot-dip galvanised: frames, legs, sleeper brackets, hatch ironmongery."""
    nt = K.NT(PFX + "Galv")
    oc = nt.object_coords()
    sp = nt.vor(oc, wavelength_m=0.075, feature="F1", out=0, rand=0.95)
    base = nt.ramp(sp, [(0.10, (0.284, 0.292, 0.300)), (0.55, (0.336, 0.342, 0.348)),
                        (0.90, (0.252, 0.262, 0.272))])
    hh = nt.maprange(sp, 0.10, 0.90, 0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.34, wavelength_m=0.075, height_pp=1.0)
    _pout(nt, base_color=base, roughness=0.46, metallic=0.62,
                      specular=0.5, normal=bp)
    return nt.m


def _mat_rooflight():
    """Triple-skin opal polycarbonate. The brightest thing on the roof, and the
    only translucent one -- which is exactly why it is here: a highlight the
    membrane cannot produce at any roughness."""
    nt = K.NT(PFX + "Rooflight")
    oc = nt.object_coords()
    n = nt.noise(oc, wavelength_m=0.11, detail=4.0)
    base = nt.ramp(n, [(0.35, (0.560, 0.572, 0.560)), (0.75, (0.660, 0.668, 0.652))])
    hh = nt.maprange(nt.noise(oc, wavelength_m=0.020, detail=3.0), 0.32, 0.68,
                     0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.20, wavelength_m=0.020, height_pp=1.0)
    b = _pout(nt, base_color=base, roughness=0.20, metallic=0.0,
                          specular=0.62, normal=bp)
    nt.pin_named(b, "Transmission Weight", 0.28)
    nt.pin_named(b, "IOR", 1.49)
    return nt.m


def _mat_walkway():
    """Recycled-rubber walkway tiles: the darkest thing up here, which is what
    makes a 0.9 m wide walkway legible as a LINE at 79 mm/px across the y axis."""
    nt = K.NT(PFX + "Walkway")
    oc = nt.object_coords()
    n = nt.noise(oc, wavelength_m=0.24, detail=6.0, rough=0.60)
    # 0.075..0.105, not 0.035..0.055. A recycled-rubber pad is dark, but at
    # 0.04 it renders as a HOLE in the roof rather than as a walkway, and 0.9 m
    # of hole is 11 px of the roof's 285.
    base = nt.ramp(n, [(0.28, (0.0742, 0.0755, 0.0760)),
                       (0.72, (0.1045, 0.1052, 0.1040))])
    stud = nt.vor(oc, wavelength_m=0.052, rand=0.15)
    hh = nt.maprange(stud, 0.15, 0.85, 0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.38, wavelength_m=0.052, height_pp=1.0)
    _pout(nt, base_color=base, roughness=nt.maprange(n, 0, 1, 0.62, 0.80),
                      metallic=0.0, specular=0.4, normal=bp)
    return nt.m


def _mat_plinth():
    """GRP / precast plant plinths and sleepers."""
    nt = K.NT(PFX + "Plinth")
    oc = nt.object_coords()
    n = nt.noise(oc, wavelength_m=0.19, detail=6.0, rough=0.58)
    base = nt.ramp(n, [(0.25, (0.152, 0.150, 0.144)), (0.70, (0.196, 0.194, 0.186))])
    hh = nt.maprange(nt.noise(oc, wavelength_m=0.042, detail=5.0), 0.28, 0.72,
                     0.0, 1.0)
    bp = nt.bump(hh, 1.0, modulation_pp=0.32, wavelength_m=0.042, height_pp=1.0)
    _pout(nt, base_color=base, roughness=0.72, metallic=0.0,
                      specular=0.45, normal=bp)
    return nt.m


MATFN = {
    "Membrane": _mat_membrane, "Upstand": _mat_upstand, "Coping": _mat_coping,
    "Fascia": _mat_fascia, "PlantCase": _mat_plantcase, "Alu": _mat_alu,
    "Galv": _mat_galv, "Rooflight": _mat_rooflight, "Walkway": _mat_walkway,
    "Plinth": _mat_plinth,
}


def materials(rebuild=True):
    out = {}
    for k, fn in MATFN.items():
        name = PFX + k
        m = bpy.data.materials.get(name)
        if m is None or rebuild:
            m = fn()
        out[k] = m
    return out


# ===========================================================================
# 4.  MESH PRIMITIVES.  Every emit is a NEW datablock -- nothing is reused.
# ===========================================================================
def reverse_faces(me):
    """Reverse every polygon's winding in place.

    An OPEN lofted strip has no inside, so `orient_outward` cannot decide it and
    `new_mesh(orient=True)` must not be asked to. The four parapet runs and the
    four coping runs are swept in a fixed profile order around a rectangle, so
    two of each four come out with their sweep frame mirrored and their normals
    reversed. This is the repair, and `_face_up` below is the TEST that decides
    when to apply it -- measured off a named strip of the built mesh rather than
    reasoned about per side, because reasoning about it per side is how 54 of
    318 pieces of the human figure shipped inside-out with every bump inverted
    (itemkit section 3b).
    """
    nl, nf = len(me.loops), len(me.polygons)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    out = lv.copy()
    for st, ct in zip(ls, lt):
        out[st:st + ct] = lv[st:st + ct][::-1]
    me.loops.foreach_set("vertex_index", out)
    me.update()
    me.update_tag()


def face_up(ob, lo, hi):
    """Area-weighted mean +z of polygons [lo, hi). The orientation TEST."""
    me = ob.data
    nf = len(me.polygons)
    n = np.empty(nf * 3, np.float32); me.polygons.foreach_get("normal", n)
    a = np.empty(nf, np.float32); me.polygons.foreach_get("area", a)
    n = n.reshape(nf, 3)[lo:hi]
    a = a[lo:hi]
    return float(np.average(n[:, 2], weights=np.maximum(a, 1e-12)))


class Build(object):
    def __init__(self, mats, coll):
        self.mats = mats
        self.coll = coll
        self.objs = []
        self.tris = 0

    def emit(self, name, verts, quads=None, tris=None, mat="Membrane",
             smooth=33.0, orient=True, attrs=None, loc=None):
        me, off = K.new_mesh(PFX + name, verts, quads=quads, tris=tris,
                             smooth_deg=smooth, recentre=True, orient=orient)
        if orient:
            # SECOND PASS ON THE LIVE MESH. `new_mesh(orient=True)` audits the
            # raw vertex ARRAY; this audits the DATABLOCK, which is what the
            # renderer and `object_winding_report` see. On the first build one
            # piece -- a wide, short truncated cone -- came out of the array
            # pass clean and reported inward_area 1.000 as a mesh. One of the
            # two is the artefact; the artefact is the one that renders.
            K.mesh_winding_report(me, apply=True)
        if attrs:
            K.bake_attributes(me, attrs)
        me.materials.append(self.mats[mat] if isinstance(mat, str) else mat)
        ob = bpy.data.objects.new(PFX + name, me)
        ob.location = off if loc is None else loc
        self.coll.objects.link(ob)
        self.objs.append(ob)
        self.tris += sum(len(p.vertices) - 2 for p in me.polygons)
        return ob

    # --- generic solids ---------------------------------------------------
    def box(self, name, c, h, mat, **kw):
        """Axis-aligned box, centre `c`, half-extents `h`."""
        cx, cy, cz = c
        hx, hy, hz = h
        V = np.array([(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
                      (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
                      (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
                      (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)])
        Q = np.array([(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
                      (2, 6, 7, 3), (3, 7, 4, 0)])
        return self.emit(name, V, quads=Q, mat=mat, smooth=None, **kw)

    def prism(self, name, poly, z0, z1, mat, cap=True, smooth=33.0, **kw):
        """Extrude a closed 2D polygon between two z. `poly` is (n, 2)."""
        p = np.asarray(poly, float)
        n = len(p)
        V = np.concatenate([np.column_stack([p, np.full(n, z0)]),
                            np.column_stack([p, np.full(n, z1)])])
        Q = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        T = []
        if cap:
            for i in range(1, n - 1):
                T.append((0, i, i + 1))
                T.append((n, n + i + 1, n + i))
        return self.emit(name, V, quads=np.array(Q),
                         tris=np.array(T) if T else None, mat=mat,
                         smooth=smooth, **kw)

    def tube(self, name, c, r0, r1, z0, z1, mat, seg=24, cap=True, **kw):
        """Cone/cylinder. r0 at z0, r1 at z1."""
        a = np.linspace(0, 2 * math.pi, seg, endpoint=False)
        lo = np.column_stack([c[0] + r0 * np.cos(a), c[1] + r0 * np.sin(a),
                              np.full(seg, z0)])
        hi = np.column_stack([c[0] + r1 * np.cos(a), c[1] + r1 * np.sin(a),
                              np.full(seg, z1)])
        V = np.concatenate([lo, hi])
        Q = np.array([(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i)
                      for i in range(seg)])
        T = []
        if cap:
            for i in range(1, seg - 1):
                T.append((0, i, i + 1))
                T.append((seg, seg + i + 1, seg + i))
        return self.emit(name, V, quads=Q, tris=np.array(T) if T else None,
                         mat=mat, **kw)

    def loft(self, name, rings, mat, closed=False, cap_ends=False, **kw):
        """Loft a list of equal-length rings of 3D points."""
        R = [np.asarray(r, float) for r in rings]
        n = len(R[0])
        V = np.concatenate(R)
        Q = []
        lim = n if closed else n - 1
        for s in range(len(R) - 1):
            for i in range(lim):
                j = (i + 1) % n
                Q.append((s * n + i, s * n + j, (s + 1) * n + j, (s + 1) * n + i))
        T = []
        if cap_ends and closed:
            for i in range(1, n - 1):
                T.append((0, i + 1, i))
                b = (len(R) - 1) * n
                T.append((b, b + i, b + i + 1))
        return self.emit(name, V, quads=np.array(Q),
                         tris=np.array(T) if T else None, mat=mat, **kw)


# ===========================================================================
# 5.  THE DECK
# ===========================================================================
def build_deck(B):
    nx = int(round(2 * IN_X / DX)) + 1
    ny = int(round(2 * IN_Y / DY)) + 1
    xs = np.linspace(-IN_X, IN_X, nx)
    ys = np.linspace(-IN_Y, IN_Y, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z = DECK_Z + buildup(X, Y)

    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    ii = np.arange(nx * ny).reshape(nx, ny)
    # CCW seen from +z, so the emitted normal is up. `orient=False` below:
    # this is a DELIBERATELY ONE-SIDED surface -- it is a membrane laid on a
    # slab whose underside is the interior ceiling and is never seen -- so the
    # winding is asserted here rather than being guessed by orient_outward,
    # which has no inside to reason about on an open sheet.
    Q = np.stack([ii[:-1, :-1].ravel(), ii[1:, :-1].ravel(),
                  ii[1:, 1:].ravel(), ii[:-1, 1:].ravel()], axis=1)

    # attributes the membrane shader reads. `rrf_low` = how far this point is
    # BELOW the local ridge, normalised -- the dirt map follows the falls.
    dv = np.min(np.stack([np.abs(Y - v) for v in VALLEY_Y]), axis=0)
    low = 1.0 - np.clip(dv / 3.4, 0.0, 1.0)
    pond = np.zeros_like(X)
    for cx, cy, r, d in PONDS:
        t = np.hypot(X - cx, Y - cy) / r
        pond = np.maximum(pond, d * np.clip(1.0 - t * t, 0.0, 1.0) ** 1.5)

    ob = B.emit("Deck", V, quads=Q, mat="Membrane", smooth=28.0, orient=False,
                attrs={"rrf_low": low.ravel(),
                       "rrf_pond": (pond / max(pond.max(), 1e-9)).ravel()})
    return ob


# ===========================================================================
# 6.  THE PARAPET AND ITS COPING
# ===========================================================================
def _para_run(B, name, axis, sign):
    """One of the four parapet runs, as a lofted profile whose INNER FOOT
    follows the deck height field. Four runs, four different meshes -- and the
    two long runs are longer than the two short ones, so nothing here is a
    duplicate of anything else.
    """
    if axis == "y":                              # runs along x, full length
        s = np.arange(-OUT_X, OUT_X + 1e-9, 0.25)
        outer, inner = sign * OUT_Y, sign * IN_Y
        fillet = sign * (IN_Y - 0.10)

        def pt(t, off, z):
            return (t, off, z)
        deck_at = lambda t: DECK_Z + buildup(np.clip(t, -IN_X, IN_X),
                                             sign * (IN_Y - 0.05))
    else:                                        # runs along y, cut back
        s = np.arange(-IN_Y, IN_Y + 1e-9, 0.25)
        outer, inner = sign * OUT_X, sign * IN_X
        fillet = sign * (IN_X - 0.10)

        def pt(t, off, z):
            return (off, t, z)
        deck_at = lambda t: DECK_Z + buildup(sign * (IN_X - 0.05),
                                             np.clip(t, -IN_Y, IN_Y))

    d = deck_at(s)
    # A CLOSED SECTION, and that is not tidiness. The first version swept an
    # OPEN five-point profile, so each run's two ENDS were open cross-sections
    # -- and the two runs that stop at y = +-11.00 put those open ends where
    # the camera can see straight through them. It rendered as a hard black
    # notch at each near corner of the roof, 6 px of pure black on a 302 px
    # roof, in the first preview. Closing the section back along the slab makes
    # each run a manifold solid, which caps the ends, lets `orient_outward`
    # decide the winding instead of a hand-written per-side rule, and buries
    # the closing edge under the deck membrane where nothing can see it.
    rings = []
    for i, t in enumerate(s):
        rings.append([pt(t, fillet, d[i] + 0.002),      # 0 fillet toe
                      pt(t, inner, d[i] + 0.100),       # 1 fillet top
                      pt(t, inner, PARA_TOP),           # 2 inner face
                      pt(t, outer, PARA_TOP),           # 3 top (under coping)
                      pt(t, outer, DECK_Z),             # 4 outer face
                      pt(t, fillet, DECK_Z)])           # 5 back under the deck
    ob = B.loft(name, rings, "Upstand", closed=True, cap_ends=True,
                smooth=33.0)
    ob.data.materials.append(B.mats["Fascia"])
    nseg, npt = len(s) - 1, 6
    mi = np.zeros(len(ob.data.polygons), np.int32)
    # profile edge 3->4 is the OUTER face; everything else is the membrane
    # upstand, the coping seating or the hidden underside.
    mi[:nseg * npt].reshape(nseg, npt)[:, 3] = 1
    ob.data.polygons.foreach_set("material_index", mi)
    return ob


def _cope_run(B, name, axis, sign):
    """Coping: oversails 45 mm each side over a 30 mm drip, falls INWARD at
    1:12 so it drains to the roof. The oversail + drip is the hard arris that
    catches the highlight; the inward fall is why the +y coping reads bright
    and the -y coping dark under a bearing of -58 deg."""
    if axis == "y":
        s = np.array([-OUT_X - COPE_OVER, OUT_X + COPE_OVER])
        o_out, o_in = sign * (OUT_Y + COPE_OVER), sign * (IN_Y - COPE_OVER)

        def pt(t, off, z):
            return (t, off, z)
    else:
        s = np.array([-(IN_Y - COPE_OVER), IN_Y - COPE_OVER])
        o_out, o_in = sign * (OUT_X + COPE_OVER), sign * (IN_X - COPE_OVER)

        def pt(t, off, z):
            return (off, t, z)

    w = abs(o_out - o_in)
    z_in = COPE_TOP_OUT - w * COPE_FALL
    rings = [[pt(t, o_out, COPE_TOP_OUT - DRIP_H),   # 0 bottom of the drip
              pt(t, o_out, COPE_TOP_OUT),            # 1 outer arris
              pt(t, o_in, z_in),                     # 2 inner arris
              pt(t, o_in, z_in - COPE_T)]            # 3 underside inner
             for t in s]
    return B.loft(name, rings, "Coping", closed=True, cap_ends=True,
                  smooth=20.0)


def build_parapet(B):
    out = []
    for axis, sign, tag in (("y", -1, "S"), ("y", +1, "N"),
                            ("x", -1, "W"), ("x", +1, "E")):
        out.append(_para_run(B, "Parapet_" + tag, axis, sign))
        out.append(_cope_run(B, "Coping_" + tag, axis, sign))
    return out


# ===========================================================================
# 7.  ROOF PLANT.  36 objects, 36 distinct meshes, no two alike.
# ===========================================================================
def _z(x, y):
    return float(DECK_Z + buildup(np.array([x]), np.array([y]))[0])


def _plinth(B, name, cx, cy, hx, hy, h):
    B.box(name, (cx, cy, _z(cx, cy) + 0.5 * h), (hx, hy, 0.5 * h), "Plinth")


def _ahu(B, tag, cx, cy, L, W, H, along, seed):
    """An air handling unit: ribbed casing, an access door, a discharge cowl and
    a flexible connection down through the roof. Two are built and they differ
    in size, orientation, cowl form and door side -- both meshes are unique."""
    r = K.Rng(seed)
    hx, hy = (0.5 * L, 0.5 * W) if along == "x" else (0.5 * W, 0.5 * L)
    pl = 0.30
    _plinth(B, "AhuPlinth_" + tag, cx, cy, hx + 0.16, hy + 0.16, pl)
    z0 = _z(cx, cy) + pl

    # casing with real cross ribs -- a rib every 0.60 m, 0.030 m proud
    n = max(2, int(round((L if along == "x" else L) / 0.60)))
    prof = []
    for i in range(n + 1):
        prof.append(i / n)
    rings = []
    axis_h = hx if along == "x" else hy
    for i, t in enumerate(prof):
        d = 0.030 if i % 2 == 0 else 0.0
        u = -axis_h + 2 * axis_h * t
        if along == "x":
            box = [(cx + u, cy - hy - d, z0), (cx + u, cy + hy + d, z0),
                   (cx + u, cy + hy + d, z0 + H), (cx + u, cy - hy - d, z0 + H)]
        else:
            box = [(cx - hx - d, cy + u, z0), (cx + hx + d, cy + u, z0),
                   (cx + hx + d, cy + u, z0 + H), (cx - hx - d, cy + u, z0 + H)]
        rings.append(box)
    B.loft("AhuCase_" + tag, rings, "PlantCase", closed=True, cap_ends=True,
           smooth=25.0)

    # discharge cowl on top: a tapered hood, unique per unit
    ch = r.u(0.45, 0.75)
    cw = r.u(0.55, 0.85)
    B.prism("AhuCowl_" + tag,
            [(cx - cw, cy - cw), (cx + cw, cy - cw),
             (cx + cw, cy + cw), (cx - cw, cy + cw)],
            z0 + H, z0 + H + 0.06, "Alu", smooth=None)
    B.tube("AhuStack_" + tag, (cx, cy), cw * 0.62, cw * 0.44,
           z0 + H + 0.06, z0 + H + 0.06 + ch, "Alu", seg=20)
    B.tube("AhuHood_" + tag, (cx, cy), cw * 0.80, cw * 0.80,
           z0 + H + 0.06 + ch, z0 + H + 0.12 + ch, "Alu", seg=20)

    # access door, standing 0.025 proud on the sunward face
    if along == "x":
        B.box("AhuDoor_" + tag, (cx - 0.28 * L, cy - hy - 0.045,
                                 z0 + 0.52 * H),
              (0.30, 0.030, 0.34 * H), "PlantCase")
    else:
        B.box("AhuDoor_" + tag, (cx + hx + 0.045, cy - 0.28 * L,
                                 z0 + 0.52 * H),
              (0.030, 0.30, 0.34 * H), "PlantCase")


def _condenser(B, tag, cx, cy, L, W, H, fans, leg, seed):
    """A condenser. Fan count, footprint, height and leg height all vary, so the
    five in this bank are five different machines rather than one mesh placed
    five times -- which is the project's `no repeated assets` law, measured by
    tools/mesh_reuse.py."""
    r = K.Rng(seed)
    z0 = _z(cx, cy)
    hx, hy = 0.5 * L, 0.5 * W
    # rail feet
    B.box("CondRailA_" + tag, (cx, cy - hy * 0.72, z0 + 0.5 * leg),
          (hx * 0.94, 0.055, 0.5 * leg), "Galv")
    B.box("CondRailB_" + tag, (cx, cy + hy * 0.72, z0 + 0.5 * leg),
          (hx * 0.94, 0.055, 0.5 * leg), "Galv")
    zc = z0 + leg
    # coil casing with louvred long faces: real blades, 0.10 m pitch
    nb = max(3, int(round(L / 0.10)))
    rings = []
    for i in range(nb + 1):
        u = -hx + 2 * hx * i / nb
        d = 0.018 if i % 2 else 0.0
        rings.append([(cx + u, cy - hy - d, zc), (cx + u, cy + hy + d, zc),
                      (cx + u, cy + hy + d, zc + H),
                      (cx + u, cy - hy - d, zc + H)])
    B.loft("CondCase_" + tag, rings, "PlantCase", closed=True, cap_ends=True,
           smooth=25.0)
    # fan guards on top
    fr = min(hy * 0.86, (L / fans) * 0.42)
    for f in range(fans):
        fx = cx - hx + L * (f + 0.5) / fans
        B.tube("CondFanRing_%s%d" % (tag, f), (fx, cy), fr, fr * 0.96,
               zc + H, zc + H + 0.075 + r.u(0.0, 0.03), "Alu", seg=22)
        B.tube("CondFanHub_%s%d" % (tag, f), (fx, cy), fr * 0.20, fr * 0.16,
               zc + H + 0.02, zc + H + 0.10, "Galv", seg=12)


def _duct(B, tag, pts, w, h, seed):
    """A rectangular duct run on sleepers, with a flange every 1.2 m standing
    0.025 proud. One mesh; the sleepers under it are separate and all differ."""
    r = K.Rng(seed)
    rings = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(2, int(round(L / 0.30)))
        for j in range(n + (1 if i == len(pts) - 2 else 0)):
            t = j / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            nx_, ny_ = -uy, ux
            d = 0.025 if (j % 4 == 0) else 0.0
            zb = _z(x, y) + 0.32
            hw = 0.5 * w + d
            hh = 0.5 * h + d
            rings.append([(x + nx_ * hw, y + ny_ * hw, zb - hh),
                          (x - nx_ * hw, y - ny_ * hw, zb - hh),
                          (x - nx_ * hw, y - ny_ * hw, zb + hh),
                          (x + nx_ * hw, y + ny_ * hw, zb + hh)])
    B.loft("Duct_" + tag, rings, "Alu", closed=True, cap_ends=True,
           smooth=25.0)
    # sleepers, one per ~2.4 m, every one a different block
    k = 0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        for j in range(max(1, int(L / 2.4))):
            t = (j + 0.5) / max(1, int(L / 2.4))
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            hgt = 0.16 + r.u(0.0, 0.05)
            B.box("DuctSleeper_%s%d" % (tag, k),
                  (x, y, _z(x, y) + 0.5 * hgt),
                  (0.22 + r.u(0, 0.06), 0.42 + r.u(0, 0.10), 0.5 * hgt),
                  "Plinth")
            k += 1


def _flue(B, tag, cx, cy, dia, h, terminal, seed):
    z0 = _z(cx, cy)
    B.tube("FlueKerb_" + tag, (cx, cy), dia * 0.95, dia * 0.85, z0,
           z0 + 0.16, "Membrane", seg=18)
    B.tube("FlueBody_" + tag, (cx, cy), dia * 0.5, dia * 0.5, z0 + 0.10,
           z0 + h, "Galv", seg=18)
    if terminal == "cowl":
        B.tube("FlueTerm_" + tag, (cx, cy), dia * 0.90, dia * 0.30,
               z0 + h, z0 + h + dia * 0.9, "Alu", seg=18)
    elif terminal == "mushroom":
        B.tube("FlueTerm_" + tag, (cx, cy), dia * 0.30, dia * 1.15,
               z0 + h, z0 + h + dia * 0.55, "Alu", seg=18)
    else:
        B.tube("FlueTerm_" + tag, (cx, cy), dia * 0.62, dia * 0.62,
               z0 + h - 0.06, z0 + h + 0.10, "Alu", seg=18)


def _hatch(B, cx, cy):
    """Roof access hatch with the lid propped open. An unmistakable shape and
    a 2.4 m shadow, both of which say `this is a roof` at 600 m."""
    z0 = _z(cx, cy)
    B.box("HatchKerb", (cx, cy, z0 + 0.175), (0.78, 0.78, 0.175), "Membrane")
    B.box("HatchFrame", (cx, cy, z0 + 0.375), (0.72, 0.72, 0.030), "Galv")
    a = math.radians(52.0)
    L = 1.32
    hy0 = cy + 0.70
    V = np.array([
        (cx - 0.70, hy0, z0 + 0.40), (cx + 0.70, hy0, z0 + 0.40),
        (cx + 0.70, hy0 + L * math.cos(a), z0 + 0.40 + L * math.sin(a)),
        (cx - 0.70, hy0 + L * math.cos(a), z0 + 0.40 + L * math.sin(a)),
        (cx - 0.70, hy0 - 0.05, z0 + 0.44), (cx + 0.70, hy0 - 0.05, z0 + 0.44),
        (cx + 0.70, hy0 + L * math.cos(a) - 0.05,
         z0 + 0.44 + L * math.sin(a)),
        (cx - 0.70, hy0 + L * math.cos(a) - 0.05,
         z0 + 0.44 + L * math.sin(a))])
    Q = np.array([(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
                  (2, 6, 7, 3), (3, 7, 4, 0)])
    B.emit("HatchLid", V, quads=Q, mat="PlantCase", smooth=None)
    B.tube("HatchStay", (cx + 0.60, hy0 + 0.42), 0.022, 0.022,
           z0 + 0.42, z0 + 0.42 + 0.78, "Galv", seg=8)


def _rooflight(B, tag, cx, cy, L, W, rise):
    z0 = _z(cx, cy)
    hx, hy = 0.5 * L, 0.5 * W
    B.box("RlKerb_" + tag, (cx, cy, z0 + 0.225), (hx + 0.09, hy + 0.09, 0.225),
          "Membrane")
    # a ridged dome light: a closed six-vertex solid, ridge along the long axis
    zb = z0 + 0.45
    zt = zb + rise
    V = np.array([(cx - hx, cy - hy, zb), (cx + hx, cy - hy, zb),
                  (cx + hx, cy + hy, zb), (cx - hx, cy + hy, zb),
                  (cx - hx * 0.34, cy, zt), (cx + hx * 0.34, cy, zt)])
    Q = np.array([(0, 1, 5, 4), (2, 3, 4, 5), (0, 3, 2, 1)])
    T = np.array([(1, 2, 5), (3, 0, 4)])
    B.emit("RlDome_" + tag, V, quads=Q, tris=T, mat="Rooflight", smooth=None)


def _walkway(B, pts, w):
    """ONE mesh for the whole walkway. A run of pads is inherently repetitive;
    building it as N copies of one pad mesh would be exactly the repetition the
    law forbids, so the per-pad variation (height, gap, yaw) is baked into a
    single datablock instead."""
    r = K.Rng(97531)
    V, Q = [], []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(round(L / 0.62)))
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx_, ny_ = -uy, ux
        for j in range(n):
            # 30 mm between pads, not 230. The first preview read as a black
            # dashed line -- a railway track laid across the roof -- because a
            # 0.62 m pad with a 6 % gap at each end leaves a 75 mm shadow slot
            # that is 1 px wide and, at this albedo, pure black.
            t0 = (j + 0.024) / n
            t1 = (j + 0.976) / n
            th = 0.022 + r.u(0.0, 0.008)
            hw = 0.5 * w * (0.97 + r.u(0.0, 0.06))
            for tt in (t0, t1):
                pass
            ax, ay = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
            bx, by = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
            base = len(V)
            for (px, py) in ((ax, ay), (bx, by)):
                zb = _z(px, py)
                V += [(px + nx_ * hw, py + ny_ * hw, zb),
                      (px - nx_ * hw, py - ny_ * hw, zb),
                      (px - nx_ * hw, py - ny_ * hw, zb + th),
                      (px + nx_ * hw, py + ny_ * hw, zb + th)]
            Q += [(base + 4, base + 7, base + 6, base + 5),   # top
                  (base + 2, base + 6, base + 7, base + 3),   # far edge
                  (base + 3, base + 7, base + 4, base + 0),   # side
                  (base + 1, base + 5, base + 6, base + 2),   # side
                  (base + 0, base + 4, base + 5, base + 1),   # near edge
                  (base + 0, base + 1, base + 2, base + 3)]   # bottom -> closed
    B.emit("Walkway", np.array(V), quads=np.array(Q), mat="Walkway",
           smooth=None)


def _outlet(B, tag, cx, cy):
    z0 = _z(cx, cy)
    B.tube("OutletSump_" + tag, (cx, cy), 0.30, 0.22, z0 - 0.020, z0 + 0.004,
           "Membrane", seg=16)
    B.tube("OutletGuard_" + tag, (cx, cy), 0.16, 0.05, z0 + 0.004, z0 + 0.11,
           "Galv", seg=12)


def _penetration(B, tag, cx, cy, dia, h):
    z0 = _z(cx, cy)
    B.tube("PenColl_" + tag, (cx, cy), dia * 1.9, dia * 1.1, z0, z0 + 0.09,
           "Membrane", seg=14)
    B.tube("PenPipe_" + tag, (cx, cy), dia * 0.5, dia * 0.5, z0 + 0.05,
           z0 + h, "Galv", seg=14)


def _dish(B, cx, cy, r_dish, h):
    z0 = _z(cx, cy)
    B.box("DishBase", (cx, cy, z0 + 0.09), (0.55, 0.55, 0.09), "Plinth")
    B.tube("DishMast", (cx, cy), 0.045, 0.040, z0 + 0.18, z0 + h, "Galv", seg=10)
    a = np.linspace(0, 2 * math.pi, 20, endpoint=False)
    rim = np.column_stack([cx + r_dish * np.cos(a) * 0.35 + 0.30,
                           cy + r_dish * np.sin(a),
                           z0 + h - 0.10 + r_dish * np.sin(a) * 0.0
                           + r_dish * np.cos(a) * 0.62])
    cen = np.array([[cx + 0.18, cy, z0 + h - 0.10]])
    V = np.concatenate([cen, rim])
    T = np.array([(0, i + 1, 1 + (i + 1) % 20) for i in range(20)])
    ob = B.emit("DishFace", V, tris=T, mat="Alu", smooth=None, orient=False)
    if face_up(ob, 0, len(ob.data.polygons)) < 0.0:   # the bowl looks up-sun
        reverse_faces(ob.data)


def _acoustic_screen(B, tag, pts, h, blades, seed):
    """A louvred acoustic screen: what actually stands round a condenser bank.

    Real, and legible: 1.9 m of vertical louvre is 24 px of screen and throws
    an 8.6 m shadow. Two are built, on different runs, with different blade
    counts and heights -- two meshes, not one placed twice."""
    r = K.Rng(seed)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx_, ny_ = -uy, ux
        z0 = _z(0.5 * (x0 + x1), 0.5 * (y0 + y1))
        # posts
        for e, (px, py) in enumerate(((x0, y0), (x1, y1))):
            B.box("AcPost_%s%d%d" % (tag, i, e), (px, py, z0 + 0.5 * h),
                  (0.055, 0.055, 0.5 * h), "Galv")
        # blades, as ONE lofted mesh per run: a rank of louvres is repetitive by
        # construction, so the repetition lives inside one datablock.
        V, Q = [], []
        for b in range(blades):
            zb = z0 + 0.10 + (h - 0.20) * (b + 0.5) / blades
            t = 0.5 * (h - 0.20) / blades
            d = 0.055 + r.u(0.0, 0.012)
            base = len(V)
            for sgn in (0.0, 1.0):
                px, py = x0 + (x1 - x0) * sgn, y0 + (y1 - y0) * sgn
                V += [(px + nx_ * d, py + ny_ * d, zb - t),
                      (px - nx_ * d, py - ny_ * d, zb + t * 0.2),
                      (px - nx_ * d, py - ny_ * d, zb + t),
                      (px + nx_ * d, py + ny_ * d, zb + t * 1.8 - t)]
            Q += [(base + 4, base + 7, base + 6, base + 5),
                  (base + 0, base + 1, base + 2, base + 3),
                  (base + 0, base + 4, base + 5, base + 1),
                  (base + 1, base + 5, base + 6, base + 2),
                  (base + 2, base + 6, base + 7, base + 3),
                  (base + 3, base + 7, base + 4, base + 0)]
        B.emit("AcBlades_%s%d" % (tag, i), np.array(V), quads=np.array(Q),
               mat="Alu", smooth=None)


def _anchor(B, tag, cx, cy, h):
    """A fall-arrest anchor post: three on the roof, three heights."""
    z0 = _z(cx, cy)
    B.tube("AnchorPlate_" + tag, (cx, cy), 0.19, 0.17, z0, z0 + 0.035,
           "Membrane", seg=12)
    B.tube("AnchorPost_" + tag, (cx, cy), 0.032, 0.028, z0 + 0.02, z0 + h,
           "Galv", seg=10)
    B.tube("AnchorEye_" + tag, (cx, cy), 0.065, 0.065, z0 + h - 0.03, z0 + h,
           "Galv", seg=10)


def _pad_stack(B, cx, cy, n):
    """A short stack of spare ballast pads left beside the hatch. Roofs have
    things left on them, and a 0.6 x 0.6 m stack is 8 px of `somebody works
    up here`."""
    r = K.Rng(2468)
    V, Q = [], []
    z = _z(cx, cy)
    for i in range(n):
        t = 0.045
        hx = 0.30 + r.u(0.0, 0.03)
        hy = 0.30 + r.u(0.0, 0.03)
        ox, oy = r.u(-0.04, 0.04), r.u(-0.04, 0.04)
        b = len(V)
        for zz in (z, z + t):
            V += [(cx + ox - hx, cy + oy - hy, zz), (cx + ox + hx, cy + oy - hy, zz),
                  (cx + ox + hx, cy + oy + hy, zz), (cx + ox - hx, cy + oy + hy, zz)]
        Q += [(b, b + 1, b + 2, b + 3), (b + 4, b + 7, b + 6, b + 5),
              (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
              (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)]
        z += t
    B.emit("PadStack", np.array(V), quads=np.array(Q), mat="Walkway",
           smooth=None)


def build_plant(B):
    # --- the two air handling units --------------------------------------
    _ahu(B, "A", -8.0, 2.5, 4.6, 2.2, 2.00, "x", 1201)
    _ahu(B, "B", 3.5, 8.0, 3.2, 1.7, 1.60, "y", 1202)
    # --- the condenser bank: five machines, five sizes --------------------
    _condenser(B, "1", -2.0, -3.1, 2.30, 1.05, 1.35, 2, 0.22, 3311)
    _condenser(B, "2", -2.0, -1.3, 2.05, 0.95, 1.20, 2, 0.26, 3312)
    _condenser(B, "3", -2.0, 0.6, 2.60, 1.15, 1.55, 3, 0.20, 3313)
    _condenser(B, "4", 7.4, 4.1, 1.75, 0.90, 1.10, 1, 0.30, 3314)
    _condenser(B, "5", 7.4, 6.2, 2.20, 1.00, 1.30, 2, 0.24, 3315)
    # --- the duct run -----------------------------------------------------
    _duct(B, "A", [(-5.6, 2.5), (2.0, 2.5), (2.0, 6.6)], 0.90, 0.62, 5501)
    # --- flues and vents: four, all different ------------------------------
    _flue(B, "1", -12.4, -5.0, 0.40, 2.40, "cowl", 7701)
    _flue(B, "2", 9.0, -4.0, 0.25, 1.50, "mushroom", 7702)
    _flue(B, "3", -6.0, -8.6, 0.15, 0.90, "open", 7703)
    _flue(B, "4", 8.6, 9.0, 0.30, 1.90, "cowl", 7704)
    # --- access and light --------------------------------------------------
    _hatch(B, 8.0, -8.0)
    _rooflight(B, "A", -11.0, 7.4, 2.60, 1.30, 0.42)
    _rooflight(B, "B", 5.4, -7.0, 1.90, 1.90, 0.36)
    # --- walkway: hatch -> AHU A, with a spur to the condenser bank ---------
    _walkway(B, [(7.6, -8.0), (-9.0, -8.0), (-9.0, 2.5), (-5.9, 2.5)], 0.90)
    # --- drainage ----------------------------------------------------------
    n = 0
    for vx in OUTLET_X:
        for vy in VALLEY_Y:
            _outlet(B, str(n), vx, vy)
            n += 1
    # --- small penetrations -------------------------------------------------
    _penetration(B, "1", -13.4, 3.0, 0.11, 0.85)
    _penetration(B, "2", 11.6, -2.0, 0.08, 0.55)
    _penetration(B, "3", 0.5, 9.4, 0.13, 1.10)
    # --- comms dish ---------------------------------------------------------
    _dish(B, 12.2, 5.6, 0.72, 1.70)
    # --- acoustic screening round the two condenser groups ------------------
    _acoustic_screen(B, "A", [(-3.6, -4.4), (-3.6, 1.9), (-0.4, 1.9)], 1.90,
                     9, 8801)
    _acoustic_screen(B, "B", [(6.0, 3.1), (6.0, 7.3)], 1.55, 7, 8802)
    # --- fall-arrest anchors, three heights ---------------------------------
    _anchor(B, "1", -13.0, -8.2, 1.05)
    _anchor(B, "2", 1.2, -9.4, 0.62)
    _anchor(B, "3", 12.9, 1.2, 0.88)
    # --- somebody works up here --------------------------------------------
    _pad_stack(B, 6.2, -9.6, 6)


# ===========================================================================
# 8.  THE BUILD
# ===========================================================================
def assert_datum():
    """The roof this was designed against must be the roof in this file."""
    ob = bpy.data.objects.get("Ceiling")
    if ob is None or ob.type != "MESH":
        return None, ("REFUSING: no `Ceiling` mesh. This roof is scribed to the "
                      "round-1 showroom slab; run it on a blend carrying the "
                      "SHOWROOM collection.")
    M = ob.matrix_world
    V = np.array([tuple(M @ v.co) for v in ob.data.vertices])
    got = dict(verts=len(V), polys=len(ob.data.polygons),
               x=[float(V[:, 0].min()), float(V[:, 0].max())],
               y=[float(V[:, 1].min()), float(V[:, 1].max())],
               z=[float(V[:, 2].min()), float(V[:, 2].max())])
    for name, val, want in (("top z", got["z"][1], DECK_Z),
                            ("soffit z", got["z"][0], SOFFIT_Z),
                            ("x min", got["x"][0], -OUT_X),
                            ("x max", got["x"][1], OUT_X),
                            ("y min", got["y"][0], -OUT_Y),
                            ("y max", got["y"][1], OUT_Y)):
        if abs(val - want) > TOL:
            return None, ("REFUSING: Ceiling %s is %.5f, not the %.5f this roof "
                          "was cut to. Re-measure before rebuilding."
                          % (name, val, want))
    if len(ob.data.polygons) != 6 or len(V) != 8:
        return None, ("REFUSING: Ceiling is %d verts / %d polys, not the 8/6 "
                      "cuboid this tool was written against -- something has "
                      "already been done to it and this would double up."
                      % (len(V), len(ob.data.polygons)))
    return got, None


def clearance_report(max_report=12):
    """Nothing may already occupy the roof volume. MEASURED ON VERTICES.

    THE FIRST VERSION OF THIS ASKED BOUNDING BOXES AND WAS USELESS. Run on the
    film blend it refused the build with "47 objects already reach into
    z > 6.500 inside the parapet line", and the list was `TER_Ground`
    (z -12.8 .. 364.5, x -10907 .. 10827), `SURF_Track`, `ARCH_Ground_Fences`
    and forty-four other world-scale meshes whose AABB of course contains a
    30 x 22 m box at the origin. Not one of them has a single vertex up there.

    A bounding box is a cheap FILTER and nothing else, so it is used as one:
    AABB overlap to shortlist, then the EVALUATED mesh's vertices in world
    space, which is the only thing that can answer the question.
    """
    from mathutils import Vector
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = np.array([-OUT_X - COPE_OVER, -OUT_Y - COPE_OVER, DECK_Z + 0.001])
    hi = np.array([OUT_X + COPE_OVER, OUT_Y + COPE_OVER, COPE_TOP_OUT + 4.0])
    shortlist, hits, scanned = 0, [], 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.data is None or not len(o.data.vertices):
            continue
        if o.name.startswith(PFX):
            continue
        bb = np.array([tuple(o.matrix_world @ Vector(c)) for c in o.bound_box])
        if not ((bb.max(axis=0) > lo).all() and (bb.min(axis=0) < hi).all()):
            continue
        shortlist += 1
        try:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
        except Exception:                                       # noqa: BLE001
            me = o.data
            ev = None
        n = len(me.vertices)
        if n:
            co = np.empty(n * 3, np.float32)
            me.vertices.foreach_get("co", co)
            V = co.reshape(-1, 3).astype(np.float64)
            M = np.array(o.matrix_world)
            V = V @ M[:3, :3].T + M[:3, 3]
            inside = ((V > lo).all(axis=1) & (V < hi).all(axis=1))
            scanned += n
            if inside.any():
                W = V[inside]
                hits.append(dict(name=o.name, n_verts=int(inside.sum()),
                                 z=[float(W[:, 2].min()), float(W[:, 2].max())]))
        if ev is not None:
            try:
                ev.to_mesh_clear()
            except Exception:                                   # noqa: BLE001
                pass
    print(">> clearance: %d object(s) shortlisted by AABB, %d vertices tested, "
          "%d object(s) with real geometry in the roof volume"
          % (shortlist, scanned, len(hits)))
    for h in hits[:max_report]:
        print("     %-30s %d vert(s), z %.3f..%.3f"
              % (h["name"], h["n_verts"], h["z"][0], h["z"][1]))
    return hits


def recess_report():
    """Every groove this roof cuts, against `world_contract`'s black-line law.

    Defect #48 was 3,390 pure-black pixels from 35 mm joints. Nothing here may
    repeat it, so each recess is declared with its width, its depth and the
    bearing it RUNS along, and compared with `max_recess_depth`.
    """
    out = []
    for name, w, d, bearing in (
            ("coping_drip_shadow", COPE_OVER, DRIP_H, 0.0),
            ("coping_drip_shadow_y", COPE_OVER, DRIP_H, 90.0),
            ("ahu_rib_reveal", 0.60, 0.030, 0.0),
            ("condenser_louvre", 0.10, 0.018, 90.0),
            ("outlet_sump", 0.60, 0.020, 0.0),
            ("valley_gutter", 6.65, 0.083, 0.0),
            ("pond_dish", 5.20, 0.026, 0.0)):
        r = float(C.recess_relative_radiance(w, d, bearing))
        out.append(dict(name=name, width_m=w, depth_m=d, bearing_deg=bearing,
                        radiance=r, max_depth_m=float(C.max_recess_depth(w, bearing)),
                        ok=bool(r >= C.TOL_RECESS_RADIANCE)))
    return out


def build(scene=None):
    scene = scene or bpy.context.scene
    c = K.coll(COLL)
    mats = materials(rebuild=True)
    B = Build(mats, c)
    build_deck(B)
    build_parapet(B)
    build_plant(B)
    return B


# ===========================================================================
# 9.  MEASUREMENT.  Both layers, before and after, same instrument.
# ===========================================================================
GEO_BANDS = ((0.05, 0.16), (0.16, 0.45), (0.45, 1.40), (1.40, 4.50),
             (4.50, 40.0))


def measure(tag):
    rep = {"tag": tag, "sun_elev_deg": K.sun_elev_deg(),
           "amplifier": K.sun_amplifier(),
           "bands": {k: list(v) for k, v in K.RELIEF_BANDS.items()}}

    # --- the declared relief table, through the law ------------------------
    stages = relief_stages()
    print("\n>> RELIEF TABLE  (sun %.4f deg, amplifier %.3fx)"
          % (K.sun_elev_deg(), K.sun_amplifier()))
    print("   %-17s %-5s %10s %10s %8s %8s  %s"
          % ("stage", "layer", "lambda_m", "amp_mm", "slope", "m", "band"))
    rows = []
    for name, layer, lam, amp, band in stages:
        m = K.modulation_for_amplitude(amp, lam)
        th = math.degrees(math.atan(math.pi * amp * 1e-3 / lam))
        v = ""
        if band:
            lo, hi = K.RELIEF_BANDS[band]
            v = "LOW" if m < lo else "HIGH" if m > hi else "ok"
        rows.append(dict(stage=name, layer=layer, wavelength_m=lam, amp_mm=amp,
                         slope_deg=th, m=m, band=band, verdict=v or "FORM"))
        print("   %-17s %-5s %10.3f %10.3f %7.3f%s %8.3f  %s %s"
              % (name, layer, lam, amp, th, "d", m, band or "(form)", v))
    rep["stages"] = rows

    # --- the same stages, DIFFERENTIATED off the real height field ---------
    if tag != "before":
        sa = stage_slope_audit()
        rep["stage_slope_audit"] = sa
        print("\n>> STAGE SLOPE AUDIT  (the height field differentiated, "
              "Lambert against world_contract.SUN_DIR -- NOT the sinusoid "
              "translation above)")
        print("   %-17s %10s %10s %9s %9s"
              % ("stage", "slope_max", "slope_rms", "m_pp", "m_rms"))
        for k2 in list(STAGE_NAMES) + ["ALL"]:
            v = sa[k2]
            print("   %-17s %9.3fd %9.3fd %9.3f %9.3f"
                  % (k2, v["slope_max_deg"], v["slope_rms_deg"], v["m_pp"],
                     v["m_rms"]))

    # --- the SHADER half ---------------------------------------------------
    rep["bumps"] = {}
    print("\n>> BUMP RELIEF REPORT  (itemkit.bump_relief_report, height_pp=1.0)")
    for mname in sorted(m.name for m in bpy.data.materials
                        if m.name.startswith(PFX) or m.name == "CeilingMat"):
        mat = bpy.data.materials[mname]
        if not mat.node_tree:
            continue
        rr = K.bump_relief_report(mat.node_tree, height_pp=1.0)
        rep["bumps"][mname] = rr
        if not rr:
            print("   %-20s NO ShaderNodeBump AT ALL -- zero shader relief"
                  % mname)
        for r in rr:
            if r["m"] is None:
                print("   %-20s %-10s amp %6.3f mm  lam ?   %s"
                      % (mname, r["node"], r["amp_mm"], r.get("why", "")))
            else:
                print("   %-20s %-10s amp %6.3f mm  lam %8.2f mm  slope %5.2f  "
                      "m %6.3f" % (mname, r["node"], r["amp_mm"],
                                   r["wavelength_m"] * 1000.0, r["slope_deg"],
                                   r["m"]))

    # --- the GEOMETRY half -------------------------------------------------
    rep["geometry"] = {}
    print("\n>> GEOMETRY RELIEF REPORT  (itemkit.geometry_relief_report)")
    print("   %-22s %10s %8s %11s %8s %8s"
          % ("mesh", "band_lo_m", "band_hi", "edges", "rms_deg", "m"))
    subjects = [o for o in bpy.context.scene.objects
                if o.type == "MESH" and (o.name.startswith(PFX)
                                         or o.name == "Ceiling")]
    subjects.sort(key=lambda o: -len(o.data.polygons))
    for o in subjects[:14]:
        rr = K.geometry_relief_report(o.data, bands=GEO_BANDS)
        rep["geometry"][o.name] = rr
        for r in rr:
            if r.get("edges"):
                print("   %-22s %10.3f %8.3f %11d %8.3f %8.3f"
                      % (o.name, r["band_m"][0], r["band_m"][1], r["edges"],
                         r["rms_dihedral_deg"], r["m"]))
            else:
                print("   %-22s %10.3f %8.3f %11d %8s %8s"
                      % (o.name, r["band_m"][0], r["band_m"][1], 0, "-", "-"))

    # --- winding. 54 of 318 pieces of the human figure shipped inside-out ---
    rep["winding"] = {}
    worst = []
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or not o.name.startswith(PFX):
            continue
        w = K.object_winding_report(o)
        rep["winding"][o.name] = {k2: w[k2] for k2 in
                                  ("inward_area_frac", "boundary_edges",
                                   "faces", "mirrored_by_matrix")}
        if w["inward_area_frac"] > 1e-6 or w["mirrored_by_matrix"]:
            worst.append((o.name, w["inward_area_frac"],
                          w["mirrored_by_matrix"]))
    print("\n>> WINDING: %d of %d roof meshes report any inward-facing area"
          % (len(worst), len(rep["winding"])))
    for n2, f2, mir in sorted(worst, key=lambda t: -t[1])[:10]:
        print("     %-26s inward_area %.4f  mirrored=%s" % (n2, f2, mir))
    return rep


def inventory():
    # THE DEPSGRAPH FIRST. A freshly created object's `matrix_world` is identity
    # until the view layer updates, and `new_mesh(recentre=True)` puts every
    # piece of this roof metres from its own origin -- so reading it early
    # reported the roof at z -1.15..1.15 and this function's own datum check
    # REFUSED a correct build. Same trap as add_dais_ramp.py's deck radius.
    bpy.context.view_layer.update()
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name.startswith(PFX)]
    meshes = {o.data.name for o in objs}
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    verts = sum(len(o.data.vertices) for o in objs)
    from mathutils import Vector
    if objs:
        bb = np.array([tuple(o.matrix_world @ Vector(c))
                       for o in objs for c in o.bound_box])
        ext = dict(x=[float(bb[:, 0].min()), float(bb[:, 0].max())],
                   y=[float(bb[:, 1].min()), float(bb[:, 1].max())],
                   z=[float(bb[:, 2].min()), float(bb[:, 2].max())])
    else:
        ext = None
    return dict(objects=len(objs), meshes=len(meshes), tris=tris, verts=verts,
                objs_per_mesh=(len(objs) / max(len(meshes), 1)),
                extent=ext,
                materials=sorted(m.name for m in bpy.data.materials
                                 if m.name.startswith(PFX)))


# ===========================================================================
# 10.  CLI
# ===========================================================================
def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--report", default=None)
    p.add_argument("--no-build", action="store_true",
                   help="measure ONLY: the BEFORE reading, on this instrument")
    p.add_argument("--verify", action="store_true",
                   help="the file is already built; re-measure it")
    return p.parse_args(argv)


def main():
    a = parse_args()
    t0 = time.time()
    src = bpy.data.filepath
    print(">> source %s (%.2f GB)"
          % (src, os.path.getsize(src) / 2 ** 30 if src else 0.0))
    print(">> itemkit sun %.5f deg   film exposure %.3f stops"
          % (K.sun_elev_deg(), FX.FILM_EXPOSURE))

    already = [o for o in bpy.context.scene.objects if o.name.startswith(PFX)]
    got, why = None, None
    if a.verify or already:
        print(">> %d %s* object(s) already present" % (len(already), PFX))
    if not already:
        got, why = assert_datum()
        if why:
            print(why)
            return gate_exit.verdict("ROOF_NO_DATUM_REFUSED", " " + why)
        print(">> DATUM OK: %s" % json.dumps(got))

    rep = {"source": src, "datum": got}

    clear = clearance_report()
    rep["clearance"] = clear
    if clear and not a.verify and not already:
        return gate_exit.verdict("ROOF_VOLUME_OCCUPIED_VIOLATION",
                                 " %d object(s) have vertices above z = %.3f "
                                 "inside the parapet line: %s"
                                 % (len(clear), DECK_Z,
                                    [h["name"] for h in clear[:6]]))
    if not clear:
        print(">> roof volume clear: no object outside %s* has a single vertex "
              "above z = %.3f inside the parapet line" % (PFX, DECK_Z))

    rep["recess"] = recess_report()
    print("\n>> RECESS LAW  (world_contract, TOL %.2f)" % C.TOL_RECESS_RADIANCE)
    bad = []
    for r in rep["recess"]:
        print("   %-22s w %6.3f d %6.3f bearing %5.0f -> radiance %6.3f "
              "(max depth %6.3f m)  %s"
              % (r["name"], r["width_m"], r["depth_m"], r["bearing_deg"],
                 r["radiance"], r["max_depth_m"], "ok" if r["ok"] else "BLACK"))
        if not r["ok"]:
            bad.append(r["name"])
    if bad:
        return gate_exit.verdict("ROOF_RECESS_BLACK_VIOLATION", " %s" % bad)

    if a.no_build:
        print("\n>> --no-build: MEASURING ONLY. This is the BEFORE reading, "
              "taken with this instrument on this file lineage.")
        rep["measure"] = measure("before")
        rep["inventory"] = inventory()
    else:
        if not already:
            B = build()
            print("\n>> built %d objects, %d triangles into collection %s"
                  % (len(B.objs), B.tris, COLL))
        rep["measure"] = measure("after")
        rep["inventory"] = inventory()
        inv = rep["inventory"]
        print("\n>> INVENTORY  %d objects  %d distinct meshes  %.3f obj/mesh  "
              "%d tris" % (inv["objects"], inv["meshes"], inv["objs_per_mesh"],
                           inv["tris"]))
        print(">>   extent %s" % json.dumps(inv["extent"]))
        print(">>   materials %s" % inv["materials"])
        if inv["objects"] and inv["objs_per_mesh"] > 1.0 + 1e-9:
            return gate_exit.verdict(
                "ROOF_REPEATED_ASSET_VIOLATION",
                " %d objects share %d meshes" % (inv["objects"], inv["meshes"]))
        if inv["extent"] and inv["extent"]["z"][0] < DECK_Z - 0.031:
            return gate_exit.verdict(
                "ROOF_BELOW_DATUM_VIOLATION",
                " roof reaches z %.4f, below the slab top %.3f -- it would "
                "intersect the interior ceiling"
                % (inv["extent"]["z"][0], DECK_Z))

    ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if ext:
        why = "REFUSING TO SAVE: external images %s (Law 2)" % ext
        print(why)
        return gate_exit.verdict("ROOF_EXTERNAL_ASSETS_REJECT", " " + why)

    if a.out:
        out = os.path.abspath(a.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
        rep["out"] = out
        print("\n>> saved %s (%.2f GB) in %.0f s"
              % (out, os.path.getsize(out) / 2 ** 30, time.time() - t0))

    if a.report:
        p = os.path.abspath(a.report)
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        json.dump(rep, open(p, "w"), indent=1, default=float)
        print(">> report -> %s" % p)

    if a.no_build:
        return gate_exit.verdict("ROOF_BEFORE_MEASURED_OK",
                                 " flat slab, no roof present")
    return gate_exit.verdict("ROOF_BUILT_OK", " %d objects, %d meshes, %d tris"
                             % (rep["inventory"]["objects"],
                                rep["inventory"]["meshes"],
                                rep["inventory"]["tris"]))


if __name__ == "__main__":
    gate_exit.guard(main, tool="r2366_roof_build")
