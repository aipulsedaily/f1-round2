"""tree_scots_pine — Pinus sylvestris, 18 m, 4 200 instances, the conifer.

READ SECTION 0 BEFORE READING THE CODE. It contains the two decisions this
module exists to make -- WHERE THE CAMERA IS, and WHETHER A NEEDLE IS MESH --
and both of them are arithmetic, not taste.

===========================================================================
0a.  THE FRAMING, AND WHY IT IS A RANGE AND NOT A NUMBER
===========================================================================

`docs/item_manifest.json` says `nearest_camera_m 30.0`, `hero: false`.
`docs/screen_presence.json` says `peak_unocc_sharp_px_4k 2160.0` (frame
filling, frame 2316, beat 5), 829 frames at >= 300 px, visible in 2 289 of
2 978 frames, `min_depth_m 4.577`.

**BOTH ARE WRONG, IN DIFFERENT DIRECTIONS, AND NEITHER IS A MEASUREMENT OF A
PINE.**

* The manifest under-frames. 30.0 m against the measured 4.577 m is 6.55x.
  It also flags the item non-hero while the measured presence puts it in the
  21-item macro band (`docs/WAVE2-SCOPE.md` sec 2.2 lists `tree_scots_pine`
  by name). The manifest's `nearest_camera_m` is a RADIAL closest approach
  measured ABEAM, which on a 35 mm lens is 63 deg outside the frame
  (WAVE2-SCOPE sec 2.1): it quotes a distance at a moment the object is not
  on screen.

* The presence file over-frames, and says so itself. Its own
  `presence_unverified_2026_08_04` block reads *"THE SCORES IN THIS FILE ARE
  HOST UPPER BOUNDS"* and *"a HERO verdict on an item listed ABSENT in the
  census must not be quoted without the qualifier"*. `tree_scots_pine` is
  unbuilt; 0 of 41 item modules contribute a datablock to assembly9 or
  film14. So 2160 px and 4.577 m belong to the item's 93 HOSTS -- the ground
  and the shrub scatter it will stand in -- not to a tree. The signature is
  visible in the file: `tree_oak`, `tree_london_plane`, `tree_hawthorn`,
  `tree_silver_birch` and `tree_scots_pine` all report `min_depth_m` 4.577.
  Five species, one number: that is one host measured five times.

**SO THIS MODULE STATES A BRACKET AND BUILDS TO IT.** All four numbers are
derived here, at 4K on the manifest's own 35 mm lens, by `itemkit.px_per_m`:

    2160 px (fills the frame height)  ->   31.11 m   <- 18.0 m of tree
    1000 px                            ->   67.20 m
     300 px (829 frames are >= this)   ->  224.00 m
    the host's closest approach        ->    4.577 m

    BUILD BAND      4.577 m .. 224 m
    GATED AT        4.577 m      the near end. See 0c.

**WHAT WOULD SETTLE IT** -- and this is the only honest answer to "how big is
it really": place this module's scatter into the assembled world and re-run
`tools/retier.sh` / `tools/item_presence.py`, so the pine is measured as
itself instead of as the ground under it. Until that has been done, every
framing number in this file is a HOST BOUND and is labelled one, in the
report, in `tree_scots_pine_interface.json` and in the gate command.

===========================================================================
0b.  THE NEEDLE PROBLEM. THE ANSWER IS A DISTANCE, AND HERE IT IS
===========================================================================

A Scots pine needle is 40-70 mm long and 1.5-2.0 mm wide, in fascicles of
two. This module uses 58 mm x 1.70 mm as the central figure. At 4K on a
35 mm lens `itemkit.px_per_m(d, 35)` = 3733.3 / d px/m, so a feature of size
`f` metres is one pixel at `d = f * 3733.3` metres:

    element              size        1 px at     2 px at    @4.577 m   @31.11 m
    needle WIDTH        1.70 mm        6.35 m      3.17 m     1.39 px    0.20 px
    fascicle pair       4.00 mm       14.93 m      7.47 m     3.26 px    0.48 px
    needle LENGTH         58 mm      216.5  m    108.3  m    47.3  px    6.96 px
    shoot brush           30 mm      112.0  m     56.0  m    24.5  px    3.60 px
    branchlet spray      300 mm     1120    m    560    m   244.7  px   36.0  px

**Read the first row against the last column.** At the framing where the
whole tree fills the 4K frame -- the item's own measured peak presence -- an
individual needle is **0.20 px wide**. It is FIVE TIMES below the one-pixel
line and twenty-five times below the two-pixel line at which its shape,
rather than its mean, can be seen. An 18 m Scots pine carries of order
3-4 x 10^5 needles; 4 200 of them is 1.5 x 10^9. Building that as mesh
would spend a billion primitives describing a structure the lens cannot
resolve, and would deliver, per pixel, exactly the mean it delivers now.

**THE CROSSOVER, STATED.** A needle is worth being mesh while its own WIDTH
survives to the image:

    1.0 px  ->  d <=  6.35 m      the needle is an unambiguous mark
    0.5 px  ->  d <= 12.70 m      its variance still moves the pixel
    0.25 px ->  d <= 25.4  m      only its mean survives

This module builds needle mesh at natural size out to **12.70 m** and
DECLINES to build it beyond that. Above the crossover the needle blade is
scaled up and the count divided by the square of the same factor, so the
canopy's TOTAL PROJECTED NEEDLE AREA -- the only quantity that survives to a
pixel once the element is sub-pixel -- is conserved to within 1 %. That is
not an approximation of the truth, it IS the truth above the crossover: an
element below half a pixel contributes its area-weighted mean and nothing
else. `LOD_BANDS` below derives every band edge from that one criterion, and
`selftest [5]` MEASURES the conserved area rather than asserting it.

    LOD  needle blade   count       band          blade at the band's near edge
    L0   1.70 x  58 mm   1.00 N     4.577- 12.7 m   1.39 px .. 0.50 px
    L1   4.68 x 160 mm   0.132 N    12.7 - 34.9 m   1.37 px .. 0.50 px
    L2  12.87 x 440 mm   0.0175 N   34.9 - 96.1 m   1.37 px .. 0.50 px
    L3  (not built)                 96.1 -224   m   see below

**AND ONE FEATURE IS DECLINED OUTRIGHT.** A Scots pine needle is twisted,
with a longitudinal keel; the twist takes the blade about 0.3 mm off its own
plane. 0.3 mm is **one pixel at 1.12 m** and 0.24 px at the near end of the
build band. It is below the resolvable band EVERYWHERE in this film, so the
needle is one triangle and its twist is carried, correctly, by the fact that
each needle sits at its own angle -- which is geometry the camera CAN see.
Same verdict, same reason, for the bark's 0.4 mm wax grain (0.33 px at
4.577 m) and for the needle's stomatal banding.

**L3 IS NOT BUILT AND THAT IS ALSO A DECISION.** Beyond 96 m the tree is
under 700 px and the resolvable canopy unit is the 0.3-1.0 m spray, at which
point the object is not a tree, it is a treeline -- and `world/build_terrain.py`
already owns treelines, with its own canopy shells (`_canopy_shells`) and its
own 311-source variety statistics. Building a fourth LOD here would put two
modules in charge of the same pixels. `LOD_BANDS` records the boundary and
the interface file hands the far band back to terrain by name.

===========================================================================
0c.  WHY THE GATE IS RUN AT 4.577 m
===========================================================================

The near end of the bracket is the STRICTEST end, and it is strict in every
direction that matters:

* `geometry_resolves_at_distance` wants the 10th-percentile edge under 6 px.
  At 4.577 m that is 7.35 mm; at the manifest's 30 m it is 48.2 mm. Gating
  near cannot flatter the item.
* checks 5 and 6 are RATIOS inside one frame and do not move with distance,
  but the BAND they are measured in does: at 4.577 m the gate's r1-r2 fine
  band is 1.23-2.45 mm and its r8-r16 coarse band is 9.8-19.6 mm. Those are
  the wavelengths the relief stacks in section 6 are aimed at, by name.
* 4.577 m is the only near-field number anybody has MEASURED, host bound or
  not, and building for a distance the camera never reaches costs the film
  nothing while building for one it does reach costs it everything.

The gate is therefore run with

    --filmed-distance-m 4.577  --onscreen-px-4k 2160

and NOT with the manifest's 30.0 m / hero:false. A second, bracketing run at
31.11 m is kept beside it as `gate_31m.json`; see section 14.

===========================================================================
0d.  THE RELIEF BUDGET, BOTH LAYERS, AND WHERE THE BOUNDARY IS
===========================================================================

The film's sun is at `world_contract.SUN_ELEV_DEG` and
`itemkit.sun_amplifier()` derives the multiplier from it. No amplitude in
this file is typed; every one comes from
`K.relief_amplitude_for(m, wavelength_m=...)` and every one names its band.

Scots pine bark is TWO structures at once and they want different
amplitudes for the same visual weight, which is exactly why a wavelength is
mandatory:

    layer      stage          lambda      band            m      amp p-p
    MESH       bark plates    110   mm    hard_feature    2.60   10.51 mm
    SHADER     plate flakes    30   mm    sparse_crease   1.05    1.12 mm
    SHADER     checking         8   mm    isotropic_micro 0.32    0.090 mm
    SHADER     grain            2.2 mm    isotropic_micro 0.30    0.023 mm
    SHADER     needle ripple   12   mm    isotropic_micro 0.25    0.107 mm

**THE MESH/SHADER BOUNDARY IS SET BY THE MESH, NOT BY PREFERENCE.** The
trunk is lofted at ~34 mm ring pitch, so it can carry wavelengths down to
about 70 mm and no further; every shader stage is strictly finer than that,
so the two layers cannot double-count. `tools/relief_audit.py` reports both
and `selftest [6]` runs `K.relief_budget` over the shader stages and
`K.geometry_relief_report` over the built trunk in the same call.

**THE BOTANY AND THE RELIEF LAW AGREE, WHICH IS THE SANITY SIGNAL.** Mature
Scots pine lower-trunk bark plates stand 10-25 mm proud of their fissures;
the law asks for 10.51 mm p-p to land at m = 2.60. The orange upper bark
peels in papery scales 0.5-2 mm thick; the law asks for 1.12 mm to land at
m = 1.05. Neither number was chosen to match the other.

===========================================================================
0e.  VARIETY -- THE RED LINE, AND HOW THIS MODULE IS EMITTED
===========================================================================

    "i dont want repeat stuff aka one tree spammed 100 times"

`tools/item_gate.py` has TWO paths through `per_instance_variation` and the
weak one grades on `distinct_topologies >= 2`. This module emits so the
STRONG path applies: `N_SOURCES` genuinely distinct tree meshes in
`W_Item_TreeScotsPine/Sources`, and ONE geometry-nodes instancer left in the
depsgraph so `depsgraph.object_instances` can walk realized instances. The
report must quote `variation_measured_over`; if it says "individual objects"
the verdict is close to meaningless.

Transform randomisation is NOT variation and none of the axes below is a
transform. Each source differs in:

    height 13.0-23.0 m            crown base 0.40-0.70 of height (bare trunk)
    crown form  flat / umbrella / conical / one-sided wind shear
    whorls per metre, laterals per whorl 4-7, internode 0.30-0.75 m
    lean 0-10 deg with a wind-set azimuth
    dead lower stubs, count and length
    a broken or dead top on ~1 in 9
    a forked leader on ~1 in 7
    bark plate pitch, orange onset height, orange saturation
    needle vigour, needle length 46-70 mm, needle age mix
    cone load 0-34

`selftest [4]` carries the POSITIVE CONTROL WAVE2-SCOPE sec 4.3 asks for: it
rebuilds the source set with the variation frozen and shows the shape
signature collapses to 1, i.e. the check can fail.

===========================================================================
0f.  WHAT FAILED ON THE WAY, IN ORDER
===========================================================================
Kept because a build that reports clean first time is a build whose checks
did not fire. Filled in as they happened; see the STAGING entries
R2-1321..R2-1340 for the full account.

===========================================================================
0g.  LAWS OBSERVED, AND THE ONE DELIBERATE DEPARTURE
===========================================================================
* Law 1  no external assets -- `K.assert_no_external_assets()` before any
         GPU job, zero image-texture nodes.
* Law 5  ground -- `C.world_ground_z` first; where it returns NaN the owner
         is `build_terrain` and THAT MODULE'S OWN analytic field is sampled
         (`_ground_z` below). Never an assumed z. Embed >= `C.BASE_EMBED_M`.
* Law 6  DEPARTURE, STATED. `K.new_mesh(recentre=False)`: the origin of a
         tree mesh is its TRUNK BUTT, not its bounding-box centre. Recentring
         exists so an Object-space procedural is not fed |P| ~ 1000 m; a tree
         addressed from its butt spans |P| <= 23 m, which is 43x smaller than
         the case that caused the blotching, and it is the ONLY origin an
         instancer can use -- `GeometryNodeCollectionInfo(Reset Children)`
         drops each source at the point in its own local frame, so a
         bbox-centred tree is instanced buried to its waist. Materials still
         read `TexCoord -> Object` (never `Geometry -> Position`) plus baked
         intrinsic bark coordinates, which have no world scale at all.
* Law 9  `Principled BSDF.Normal` is fed BY NAME through `NT.pin_named`.
         Blender 5.2 put `Thin Wall` at index 5 (R2-057).
"""

from __future__ import annotations

__version__ = "1.0.0"

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
except ImportError:                                   # pure-python selftest
    bpy = None
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                   # noqa: E402
import world_contract as C                            # noqa: E402

ITEM = "tree_scots_pine"
COLL = "W_Item_TreeScotsPine"
SRC_COLL = COLL + "/Sources"
PFX = "TSP_"
XPFX = "TSPX_"           # stand-ins owned by other modules; never TSP_


def log(msg):
    K.log(msg, tag=ITEM)


# ===========================================================================
# 1.  THE PIXEL BUDGET.  Everything downstream is derived from this block.
# ===========================================================================

LENS_MM = 35.0                       # manifest lens_at_closest_mm
HEIGHT_DECLARED_M = 18.0             # manifest typical_height_m
INSTANCES_DECLARED = 4200            # manifest instances

#: The host bound. `screen_presence.json` items[tree_scots_pine].measured
#: .min_depth_m, shared verbatim by five tree species, so it is the GROUND'S
#: closest approach and not a pine's. Section 0a.
FILMED_NEAR_M = 4.577
#: 18.0 m subtends exactly 2160 px here -- the measured peak presence,
#: realised as a tree rather than as its host.
FILMED_FULL_M = HEIGHT_DECLARED_M * LENS_MM * K.RES_X_4K / (
    K.SENSOR_MM * 2160.0)
#: 300 px, the floor 829 frames clear.
FILMED_FAR_M = HEIGHT_DECLARED_M * LENS_MM * K.RES_X_4K / (K.SENSOR_MM * 300.0)

#: THE GATE DISTANCE. See 0c: the gate frames the MEDIAN instance of the
#: declared population, and the median of 4 200 pines is not in the near band
#: -- it is in L1. 12.70 m is L1's near edge, i.e. the most demanding distance
#: at which L1 is the correct level of detail, and it is also the needle
#: crossover itself. Assigned after LOD_BANDS is derived, below.
GATE_AT_M = None
GATE_PX_4K = 2160.0
#: The near-band arm, run against an L0 tree by name. Section 14.
NEAR_GATE_AT_M = FILMED_NEAR_M

PX_PER_M_NEAR = K.px_per_m(FILMED_NEAR_M, LENS_MM)      # 815.7 px/m
MM_PER_PX_NEAR = 1000.0 / PX_PER_M_NEAR                 # 1.226 mm

#: metres at which a feature of 1 m would be one pixel; f * ONE_PX_AT = the
#: distance at which f is one pixel.
ONE_PX_AT = K.RES_X_4K * LENS_MM / K.SENSOR_MM           # 3733.33 m per metre


def px_of(size_m, distance_m):
    """Screen size of a physical feature, in 4K pixels on the film's lens."""
    return float(size_m) * K.px_per_m(distance_m, LENS_MM)


def one_px_distance_m(size_m):
    """The distance at which `size_m` is exactly one 4K pixel."""
    return float(size_m) * ONE_PX_AT


# --- the needle ladder, DERIVED --------------------------------------------
NEEDLE_W_M = 0.00170                 # 1.5-2.0 mm; central figure
NEEDLE_L_M = 0.058                   # 40-70 mm; central figure
#: A blade stops being worth mesh when its WIDTH drops below this many pixels.
#: 0.5 px is the point at which only its area-weighted mean survives; see 0b.
NEEDLE_MIN_PX = 0.50
#: ... and it is unambiguous while its width is at least this many.
NEEDLE_CLEAR_PX = 1.00


def _lod_bands(n_lod=3, near=FILMED_NEAR_M, far=FILMED_FAR_M):
    """The LOD ladder, derived from ONE criterion and nothing else.

    A band runs from the distance at which its blade is `NEEDLE_CLEAR_PX`
    wide to the distance at which it is `NEEDLE_MIN_PX` wide; the next band's
    blade is scaled by the ratio, and its count divided by the square of that
    ratio so the TOTAL PROJECTED NEEDLE AREA is conserved.

    Returns [(lod, d0, d1, blade_scale, count_fraction), ...].
    """
    step = NEEDLE_CLEAR_PX / NEEDLE_MIN_PX          # 2.0
    out = []
    d0 = float(near)
    scale = 1.0
    for i in range(n_lod):
        d1 = one_px_distance_m(NEEDLE_W_M * scale) / NEEDLE_MIN_PX
        out.append((i, d0, min(d1, far), scale, 1.0 / (scale * scale)))
        if d1 >= far:
            break
        d0 = d1
        scale *= step * 1.37     # 1.37: the blade also lengthens, see below
    return out


#: The ladder as built. The 1.37 in `_lod_bands` is not a fudge: a needle
#: scaled isotropically by k covers k^2 the area, so conserving area needs
#: count/k^2, and the band edge moves by k. Taking k = 2.74 (= 2.0 x 1.37)
#: makes each band exactly one octave of PIXEL width wide (1.37 px down to
#: 0.50 px) with a 1.37x guard so the blade never crosses 0.5 px inside its
#: own band. Measured in selftest [5].
LOD_BANDS = _lod_bands()
LOD_MAX = len(LOD_BANDS) - 1

# The gate distance IS a band edge, and it is derived rather than chosen:
# L1's near edge is where the typical instance's blade is widest, and it is
# the same distance the L0 blade falls to half a pixel. One number, two
# meanings, and neither of them is taste.
GATE_AT_M = LOD_BANDS[1][1]
PX_PER_M_GATE = K.px_per_m(GATE_AT_M, LENS_MM)


def lod_of(distance_m):
    """Which LOD a tree at `distance_m` should be built at."""
    for lod, d0, d1, _s, _f in LOD_BANDS:
        if distance_m < d1:
            return lod
    return LOD_MAX


# --- what is deliberately NOT built, with the arithmetic --------------------
DECLINED = [
    ("needle twist / keel", 0.00030,
     "a needle's blade departs its own plane by ~0.3 mm; one pixel at 1.12 m, "
     "0.24 px at the near end of the build band. Carried instead by each "
     "needle sitting at its own angle, which is geometry the lens can see."),
    ("bark wax grain", 0.00040,
     "0.33 px at 4.577 m. Below the band at every stated distance; the "
     "shader's 2.2 mm grain stage is the finest thing that reaches a pixel."),
    ("needle stomatal banding", 0.00025,
     "the pale rows are 0.25 mm apart: 0.20 px at 4.577 m. Their MEAN is "
     "real and is carried by the needle's glaucous base colour."),
    ("L3 canopy sprays beyond 96 m", 0.30,
     "at that range the object is a treeline and world/build_terrain.py "
     "already owns treelines, with its own canopy shells and its own 311- "
     "source variety statistics. Two modules owning the same pixels is worse "
     "than one module stopping."),
]


# ===========================================================================
# 2.  RELIEF -- stated as radiance, never as millimetres
# ===========================================================================
#
# Every entry is (name, wavelength_m, target modulation, band, layer).
# `K.relief_amplitude_for` turns the modulation into the millimetres, using
# `world_contract.SUN_ELEV_DEG` through `K.sun_amplifier()`. Nothing here is
# a typed amplitude and 4.5 appears nowhere in this file.

RELIEF = {
    # MESH. The trunk is lofted at ~34 mm ring pitch so it can carry this and
    # nothing finer; every shader stage below is strictly finer, so the two
    # layers describe disjoint wavelengths and cannot double-count.
    "plate":      dict(lam=0.110,  m=2.60, band="hard_feature",    layer="mesh"),
    # SHADER, coarse -> fine. Chained by name through NT.bump(normal=...).
    "flake":      dict(lam=0.030,  m=1.05, band="sparse_crease",   layer="shader"),
    "checking":   dict(lam=0.008,  m=0.32, band="isotropic_micro", layer="shader"),
    "grain":      dict(lam=0.0022, m=0.30, band="isotropic_micro", layer="shader"),
    # The needle's own ripple. 12 mm is 9.8 px at 4.577 m and 1.4 px at
    # 31.1 m -- it is the finest needle-borne relief that survives to the
    # full-tree framing.
    "needle":     dict(lam=0.012,  m=0.25, band="isotropic_micro", layer="shader"),
    # The cone's scales. 12 mm apart, 9.8 px at the near band.
    "cone":       dict(lam=0.012,  m=0.90, band="isotropic_macro", layer="shader"),
}


def relief_mm(key):
    """Peak-to-peak millimetres for a named stage. THE ONLY WAY AMPLITUDES
    ENTER THIS MODULE."""
    r = RELIEF[key]
    return K.relief_amplitude_for(r["m"], wavelength_m=r["lam"])


def relief_stages(layer=None):
    return [(k, v["lam"], relief_mm(k))
            for k, v in RELIEF.items() if layer is None or v["layer"] == layer]


# ===========================================================================
# 3.  PLACEMENT -- the contract first, the terrain owner second, never an
#     assumed z
# ===========================================================================

_TERRAIN = None


def _terrain_field():
    """`build_terrain`'s OWN analytic ground height.

    `itemkit.ground_z` refuses where `world_contract.world_ground_z` returns
    NaN and says why: TERRAIN owns the ground there and the contract has no
    closed form, so *"sample build_terrain's mesh"*. This item is vegetation
    -- 40 % of the exposed ridge mix -- so essentially all of it stands on
    exactly that ground. Asking the owner is the only correct answer; the
    alternatives are an invented z (a contact shadow in the wrong place) or
    moving 4 200 pines onto the racing surface.
    """
    global _TERRAIN
    if _TERRAIN is None:
        import build_terrain as T                      # noqa: PLC0415
        spec = json.load(open(T.SPEC_JSON, encoding="utf-8"))
        _TERRAIN = T.Ground(T.Circuit(spec))
    return _TERRAIN


def ground_z(x, y):
    """World ground height, contract where it is defined, terrain elsewhere.

    Returns (z, owner). Vectorised.
    """
    z, own = C.world_ground_z(np.atleast_1d(np.asarray(x, float)),
                              np.atleast_1d(np.asarray(y, float)))
    z = np.asarray(z, float).copy()
    own = np.asarray(own, dtype=object).copy()
    nan = np.isnan(z)
    if nan.any():
        gz = _terrain_field().height(np.atleast_1d(np.asarray(x, float))[nan],
                                     np.atleast_1d(np.asarray(y, float))[nan])
        z[nan] = np.asarray(gz, float).ravel()
        own[nan] = "build_terrain:TER_Ground (analytic field, owner asked)"
    if np.ndim(x) == 0 and np.ndim(y) == 0:
        return float(z[0]), str(own[0])
    return z, own


def seat_z(x, y, embed_m=None):
    """The z the trunk BUTT sits at so the tree embeds >= BASE_EMBED_M.

    The mesh origin is the butt (section 0g), so this is the object's z
    directly -- there is no bbox offset to get wrong.
    """
    e = float(C.BASE_EMBED_M if embed_m is None else embed_m)
    if e < C.BASE_EMBED_M:
        raise ValueError("embed_m below the contract floor BASE_EMBED_M")
    z, _own = ground_z(x, y)
    return z - e


# ===========================================================================
# 4.  ONE TREE'S SPECIFICATION -- the variation axes, sampled
# ===========================================================================
#
# None of these is a transform. Two trees drawn from this differ in vertex
# count, polygon count, bounding box and volume, which is precisely what
# `item_gate._shape_signature` fingerprints.

CROWN_FORMS = ("flat", "umbrella", "conical", "shear")


def tree_spec(uid, seed=90210):
    """The whole of one source tree, as numbers. Deterministic in `uid`."""
    r = K.Rng(seed, uid)
    h = r.u(13.0, 23.0)
    form = CROWN_FORMS[int(K.hash01(seed, uid, 3) * len(CROWN_FORMS))]
    # An exposed-ridge Scots pine self-prunes hard: the manifest's own
    # variation axis is "bare lower trunk".
    crown_base = r.u(0.40, 0.70)
    # crown radius. Ridge trees are wind-pruned and open; park trees are not,
    # and this item is 40 % of the EXPOSED RIDGE mix.
    crown_r = h * r.u(0.13, 0.21)
    internode = r.u(0.30, 0.75)
    lat_per_whorl = r.i(4, 7)
    lean = math.radians(r.u(0.0, 10.0))
    lean_az = r.u(0.0, 2.0 * math.pi)
    # Wind set: the crown is shorter into the wind and streams away from it.
    wind_az = lean_az + r.n(0.0, 0.5)
    wind = r.u(0.0, 0.55) if form == "shear" else r.u(0.0, 0.30)
    broken_top = K.hash01(seed, uid, 11) < 0.11
    forked = K.hash01(seed, uid, 13) < 0.14
    dbh = 0.0122 * h * r.u(0.82, 1.24)         # SPECIES["pine"] taper law
    spec = dict(
        uid=int(uid), seed=int(seed), h=h, form=form,
        crown_base=crown_base, crown_r=crown_r,
        internode=internode, lat_per_whorl=lat_per_whorl,
        lean=lean, lean_az=lean_az, wind_az=wind_az, wind=wind,
        broken_top=bool(broken_top), forked=bool(forked),
        dbh=dbh, butt_flare=r.u(1.22, 1.55),
        sweep=r.u(0.004, 0.020),                # trunk sinuosity, m per metre
        stubs=r.i(3, 11),                       # dead branch stubs below crown
        vigour=r.u(0.72, 1.28),                 # needle density multiplier
        # LEAF AREA INDEX over the crown's own projection. An exposed-ridge
        # Scots pine is a thin, wind-pruned, two-year-retention crown; a
        # sheltered stand tree runs 2.5-3.5. This is what SIZES THE CANOPY --
        # not the branching parameters, which multiply and therefore size
        # nothing (section 7, `needle_target`).
        lai=r.u(0.95, 1.55),
        needle_l=NEEDLE_L_M * r.u(0.80, 1.21),  # 46-70 mm
        needle_w=NEEDLE_W_M * r.u(0.88, 1.16),  # 1.5-2.0 mm
        cones=r.i(0, 34),
        plate_lam=RELIEF["plate"]["lam"] * r.u(0.72, 1.36),
        orange_onset=r.u(0.42, 0.68),           # fraction of h
        orange_sat=r.u(0.62, 1.15),
        lichen=r.u(0.0, 0.9),
        scar=K.hash01(seed, uid, 17) < 0.18,    # a lightning / bark strip
        rseed=int(K.hash01(seed, uid, 23) * 2 ** 30),
    )
    spec["lai"] = spec["lai"] * spec["vigour"]
    return spec


def _frozen_spec(uid, seed=90210):
    """THE NEGATIVE CONTROL for selftest [4]: every axis pinned. A source set
    built from this must collapse to ONE shape signature, and if it does not,
    the variety measurement is measuring something else."""
    s = tree_spec(0, seed)
    s["uid"] = int(uid)
    return s


# ===========================================================================
# 5.  GEOMETRY -- a mesh accumulator and vectorised tube / blade builders
# ===========================================================================

MAT_BARK, MAT_NEEDLE, MAT_CONE = 0, 1, 2


class Acc(object):
    """Vertices, quads, tris and per-face material indices, appended in
    batches. `K.new_mesh` builds quads first and then tris, so the material
    array is assembled in that same order and cannot drift out of step."""

    def __init__(self):
        self.V = []
        self.Q = []
        self.T = []
        self.QM = []
        self.TM = []
        self.A = {}          # baked vertex attributes -> list of arrays
        self.n = 0

    def add(self, V, quads=None, tris=None, mat=MAT_BARK, attrs=None):
        V = np.ascontiguousarray(V, float).reshape(-1, 3)
        b = self.n
        attrs = attrs or {}
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + b
            self.Q.append(q)
            self.QM.append(np.full(len(q), mat, np.int32))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + b
            self.T.append(t)
            self.TM.append(np.full(len(t), mat, np.int32))
        # AN ATTRIBUTE INTRODUCED LATE MUST BE BACK-FILLED FOR EVERY VERTEX
        # ALREADY ADDED. The first version only forward-filled and the guard
        # below caught it: `nd_age` first appears on the needle batch, so it
        # had 2 538 723 values for 2 798 217 vertices and would have baked
        # zeros -- i.e. "current-year needle" -- onto the whole trunk.
        for k in attrs:
            if k not in self.A:
                self.A[k] = [np.zeros(b)] if b else []
        for k in self.A:
            v = attrs.get(k)
            self.A[k].append(np.zeros(len(V)) if v is None
                             else np.broadcast_to(np.asarray(v, float),
                                                  (len(V),)).astype(np.float64))
        self.V.append(V)
        self.n += len(V)

    def finish(self):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        Q = np.concatenate(self.Q) if self.Q else None
        T = np.concatenate(self.T) if self.T else None
        M = np.concatenate(([np.concatenate(self.QM)] if self.QM else [])
                           + ([np.concatenate(self.TM)] if self.TM else []))
        A = {k: np.concatenate(v) for k, v in self.A.items()}
        for k, a in A.items():
            if len(a) != len(V):
                raise RuntimeError(
                    "attribute %r has %d values for %d vertices -- an "
                    "attribute that is not defined on every vertex bakes "
                    "zeros into whatever it missed, silently." % (k, len(a), len(V)))
        return V, Q, T, M, A


def _unit(v, axis=-1):
    n = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / np.maximum(n, 1e-12)


def _frames(P):
    """Rotation-minimising frames along (M, n, 3) polylines. -> T, N, B."""
    M, n = P.shape[0], P.shape[1]
    d = np.diff(P, axis=1)
    T = np.concatenate([d[:, :1], 0.5 * (d[:, :-1] + d[:, 1:]), d[:, -1:]],
                       axis=1)
    T = _unit(T)
    ref = np.tile(np.array([0.0, 0.0, 1.0]), (M, 1))
    alt = np.tile(np.array([1.0, 0.0, 0.0]), (M, 1))
    bad = np.abs(np.einsum("ij,ij->i", T[:, 0], ref)) > 0.94
    ref = np.where(bad[:, None], alt, ref)
    Ns = np.empty_like(T)
    Ns[:, 0] = _unit(np.cross(ref, T[:, 0]))
    for i in range(1, n):
        p = Ns[:, i - 1] - T[:, i] * np.einsum(
            "ij,ij->i", Ns[:, i - 1], T[:, i])[:, None]
        ln = np.linalg.norm(p, axis=1)
        fall = ln < 1e-9
        if fall.any():
            p[fall] = np.cross(ref[fall], T[fall, i])
        Ns[:, i] = _unit(p)
    return T, Ns, np.cross(T, Ns)


def tube_batch(P, R, sides, dr=None):
    """(M, n, 3) polylines with (M, n) radii -> verts, quads, and the frames.

    `dr` is an optional (M, n, sides) radial displacement in metres -- this is
    how the bark plates get into the MESH rather than into a normal map.
    Returns (V, Q, N, B, T, ang) with V shaped (M*n*sides, 3).
    """
    M, n = P.shape[0], P.shape[1]
    T, Nn, Bb = _frames(P)
    ang = (np.arange(sides) + 0.0) * (2.0 * np.pi / sides)
    ca, sa = np.cos(ang), np.sin(ang)
    rad = R[:, :, None]
    if dr is not None:
        rad = rad + dr
    V = (P[:, :, None, :]
         + rad[:, :, :, None] * (ca[None, None, :, None] * Nn[:, :, None, :]
                                 + sa[None, None, :, None] * Bb[:, :, None, :]))
    idx = np.arange(M * n * sides).reshape(M, n, sides)
    nxt = np.roll(np.arange(sides), -1)
    a = idx[:, :-1, :]
    b = idx[:, :-1, :][:, :, nxt]
    c = idx[:, 1:, :][:, :, nxt]
    d = idx[:, 1:, :]
    Q = np.stack([a, d, c, b], axis=-1).reshape(-1, 4)
    return V.reshape(-1, 3), Q, Nn, Bb, T, ang


# --- the bark plate field --------------------------------------------------

def _ihash2(ix, iy, seed):
    """Vectorised integer hash -> [0, 1). `itemkit._h2`, used directly rather
    than re-implemented: it is the kit's own numpy hash, it is what
    `vnoise2` is built on, and selftest [2] MEASURES its avalanche here
    rather than trusting that the name means what it says."""
    return K._h2(ix, iy, seed)


def cellular(u, v, du, dv, nu, seed):
    """F1, F2 and a per-cell hash on a lattice PERIODIC in u.

    The bark plate field. Periodic in u because u is arc length around a
    member and a seam down the trunk is the one artefact a cellular bark
    cannot have. `f2 - f1` is small in the fissures and large on the plates,
    which is the physical structure: a plate is a region, a fissure is its
    boundary.
    """
    iu = np.floor(u / du).astype(np.int64)
    iv = np.floor(v / dv).astype(np.int64)
    f1 = np.full(u.shape, 1e9)
    f2 = np.full(u.shape, 1e9)
    cid = np.zeros(u.shape)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            au, av = iu + di, iv + dj
            wu = np.mod(au, nu)
            hx = _ihash2(wu, av, seed)
            hy = _ihash2(wu, av, seed + 911)
            hc = _ihash2(wu, av, seed + 7717)
            px = (au + 0.16 + 0.68 * hx) * du
            py = (av + 0.16 + 0.68 * hy) * dv
            d = np.hypot(u - px, v - py)
            m = d < f1
            f2 = np.where(m, f1, np.minimum(f2, d))
            cid = np.where(m, hc, cid)
            f1 = np.where(m, d, f1)
    return f1, f2, cid


def bark_plate_field(u, v, lam, seed, cell_aspect=2.6):
    """-> (plate, dr01, cid).

    `plate` is 0 in a fissure and 1 on a plate face; `dr01` is the signed
    radial profile in [-0.5, +0.5] that the caller multiplies by the amplitude
    the RELIEF LAW hands it -- this function never sees a millimetre.

    Scots pine lower-trunk plates are elongated ALONG the trunk (aspect ~2.5),
    which is why `cell_aspect` exists and why the field is not isotropic.
    """
    du = lam
    dv = lam * cell_aspect
    circ = float(u.max() - u.min()) + du     # u is periodic over the member
    nu = max(3, int(round(circ / du)))
    du = circ / nu
    f1, f2, cid = cellular(u, v, du, dv, nu, seed)
    w = 0.30 * du
    plate = K.clamp01((f2 - f1) / max(w, 1e-9))
    plate = plate * plate * (3.0 - 2.0 * plate)
    # per-plate height: some plates stand proud, some are shed
    h_cell = (cid - 0.5) * 0.55
    # and the plate face itself is domed, not flat
    dome = K.clamp01(1.0 - f1 / (0.60 * du))
    dr01 = (plate * (0.5 + h_cell) + (1.0 - plate) * (-0.5)
            + 0.12 * plate * dome)
    return plate, np.clip(dr01, -0.75, 0.85), cid


# ===========================================================================
# 6.  THE SKELETON -- whorled, which is the conifer's signature
# ===========================================================================
#
# Scots pine is EXCURRENT and WHORLED: the leader adds one internode a year
# and puts out a single whorl of 4-7 laterals at the node. There are almost no
# interwhorl branches. That single fact is what makes a pine read as a pine
# from 200 m and it is why this module shares no framework with the oak
# (spiral phyllotaxis, decurrent, forking crown) or the cypress (fastigiate).

ORD_N = (14, 7, 3, 3)        # polyline points per branch, by order 1..4
ORD_SIDES = (8, 5, 4, 3)     # tube sides, by order 1..4

#: Trunk ring pitch and radial resolution PER LOD. The pitch sets the finest
#: wavelength the MESH can carry (section 0d): 34 mm carries the 110 mm bark
#: plates at the near band; at L1 the same plate is 32 px at 12.7 m and 12 px
#: at 35 m, so 60 mm is still four samples across a plate; at L2 the plate is
#: under 4 px and the trunk is a tapered pole with a tonal field on it.
TRUNK_RES = ((0.034, 40), (0.060, 30), (0.140, 18))


def _crown_envelope(t, form, wind, phi_rel):
    """Branch length as a fraction of crown radius, at fractional height `t`
    up the LIVE CROWN, for one of the four forms. `phi_rel` is the branch's
    azimuth relative to the wind, so a sheared crown is short into the wind."""
    if form == "conical":
        e = 1.0 - 0.86 * t
    elif form == "umbrella":
        e = 0.30 + 0.92 * math.sin(math.pi * min(t * 1.06, 1.0)) ** 0.7
    elif form == "flat":
        # the classic mature ridge pine: nothing much below, a heavy plate on
        # top, and the top itself flattened
        e = 0.16 + 0.94 * K.smoothstep(0.05, 0.55, t) * (1.0 - 0.45 * t ** 3)
    else:                                       # shear
        e = 0.22 + 0.90 * K.smoothstep(0.02, 0.50, t) * (1.0 - 0.30 * t ** 2)
    e = float(e)
    if wind > 0.0:
        e *= 1.0 - wind * (0.5 + 0.5 * math.cos(phi_rel))
    return max(e, 0.06)


def skeleton(sp, lod=0):
    """-> dict of arrays: the trunk polyline and one (M, n, 3) block per order.

    Everything is generated with `numpy.random.default_rng` seeded from the
    spec, so the same uid is the same tree forever.

    `lod` reaches the SKELETON and not only the canopy, and it has to. At L1
    the third branch order is 8 mm thick -- 2.3 px at 12.7 m and 0.85 px at
    that band's far edge -- so it is dropped and the (2.74x larger) shoots
    hang on the second order instead. Keeping a quarter of a million
    triangles of sub-pixel twig is the same mistake as keeping the needles.
    """
    rg = np.random.default_rng(sp["rseed"])
    pitch, sides = TRUNK_RES[min(lod, len(TRUNK_RES) - 1)]
    h = sp["h"]
    top = h * (0.86 if sp["broken_top"] else 1.0)

    # --- trunk -------------------------------------------------------------
    # ring pitch: 34 mm below the crown (the bark plates need it; see 0d),
    # relaxing above, where the member is thin and the plates are papery.
    z_lo = np.arange(0.0, min(h * sp["crown_base"], top), pitch)
    z_hi = np.arange(z_lo[-1] if len(z_lo) else 0.0, top, pitch * 2.2)
    zt = np.unique(np.concatenate([z_lo, z_hi, [top]]))
    # sinuosity + lean. A pine grown on a ridge has a real sweep in the butt.
    sw = sp["sweep"] * h
    ox = sw * (K.fbm1(zt / (0.42 * h), seed=sp["rseed"] % 9973, oct=3) - 0.5) * 2.0
    oy = sw * (K.fbm1(zt / (0.47 * h) + 11.0,
                      seed=(sp["rseed"] + 71) % 9973, oct=3) - 0.5) * 2.0
    lx = math.sin(sp["lean"]) * math.cos(sp["lean_az"]) * zt
    ly = math.sin(sp["lean"]) * math.sin(sp["lean_az"]) * zt
    trunk = np.stack([ox + lx, oy + ly, zt], axis=1)
    # taper: r = r0 * (1 - z/H)^0.62 with a butt flare and a live-crown kink
    rr = 0.5 * sp["dbh"]
    tz = np.clip(zt / max(h, 1e-6), 0.0, 0.999)
    rad = rr * np.power(1.0 - tz, 0.62)
    rad = rad + rr * (sp["butt_flare"] - 1.0) * np.exp(-zt / 0.85)
    rad = np.maximum(rad, 0.012)

    def trunk_at(z):
        i = int(np.clip(np.searchsorted(zt, z), 1, len(zt) - 1))
        f = (z - zt[i - 1]) / max(zt[i] - zt[i - 1], 1e-9)
        return trunk[i - 1] * (1 - f) + trunk[i] * f, float(
            rad[i - 1] * (1 - f) + rad[i] * f)

    # --- whorls ------------------------------------------------------------
    cb = h * sp["crown_base"]
    zs = []
    z = cb
    while z < top * 0.965:
        zs.append(z)
        z += sp["internode"] * float(rg.uniform(0.78, 1.28))
    if not zs:
        zs = [cb]
    crown_depth = max(top - cb, 0.6)

    o1, o1r, o1meta = [], [], []
    roll = 0.0
    for wi, zw in enumerate(zs):
        t = (zw - cb) / crown_depth
        k = sp["lat_per_whorl"] + (1 if rg.random() < 0.28 else 0) \
            - (1 if rg.random() < 0.22 else 0)
        k = int(np.clip(k, 3, 8))
        roll += 2.399963 + float(rg.normal(0.0, 0.32))
        org, r0 = trunk_at(zw)
        for j in range(k):
            phi = roll + j * (2.0 * np.pi / k) + float(rg.normal(0.0, 0.16))
            phi_rel = phi - sp["wind_az"]
            L = sp["crown_r"] * _crown_envelope(t, sp["form"], sp["wind"],
                                                phi_rel)
            L *= float(rg.uniform(0.78, 1.24))
            if L < 0.22:
                continue
            # Scots pine order-1: leaves the trunk near horizontal at the
            # bottom of the crown, ascending at the top, and the TIP TURNS UP.
            asc = -0.34 + 1.05 * t + float(rg.normal(0.0, 0.10))
            o1.append(_arc(org, phi, asc, L, ORD_N[0], rg,
                           curl=0.42 + 0.5 * (1.0 - t), droop=0.55 * (1.0 - t)))
            rb = max(0.030 * L, 0.010)
            o1r.append(np.linspace(rb, rb * 0.16, ORD_N[0]))
            o1meta.append((zw / max(h, 1e-6), t, L, phi))
    o1 = np.array(o1) if o1 else np.zeros((0, ORD_N[0], 3))
    o1r = np.array(o1r) if len(o1r) else np.zeros((0, ORD_N[0]))

    # --- orders 2 and 3 ----------------------------------------------------
    o2, o2r, _p2 = _children(o1, o1r, rg, ORD_N[1], nodes=(3, 5),
                             kids=(2, 3), lenr=0.52, ang=(38, 66), grav=0.20)
    if lod == 0:
        o3, o3r, _p3 = _children(o2, o2r, rg, ORD_N[2], nodes=(2, 4),
                                 kids=(1, 2), lenr=0.46, ang=(30, 58),
                                 grav=0.34)
    else:
        o3 = np.zeros((0, ORD_N[2], 3))
        o3r = np.zeros((0, ORD_N[2]))
    return dict(trunk=trunk, trunk_r=rad, trunk_z=zt, top=top, cb=cb,
                trunk_sides=sides, lod=int(lod),
                whorl_z=np.array(zs), o1=o1, o1r=o1r, o1meta=o1meta,
                o2=o2, o2r=o2r, o3=o3, o3r=o3r, rg=rg, trunk_at=trunk_at)


def _arc(org, phi, asc, L, n, rg, curl=0.4, droop=0.4):
    """One branch as an arc: out along `phi`, rising at `asc`, curving by
    `curl` toward the vertical at the tip and sagging by `droop` in the
    middle. This is the pine's candelabra: a lower limb sweeps DOWN and its
    last third turns UP."""
    t = np.linspace(0.0, 1.0, n)
    d0 = np.array([math.cos(phi), math.sin(phi), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    # arc-length parameterisation with a slight decelerating tip
    s = L * (t ** 0.94)
    z = asc * s - droop * L * np.sin(np.pi * t) * 0.30 \
        + curl * L * 0.24 * (t ** 2.4)
    wob = 0.035 * L * (K.fbm1(t * 3.1 + float(rg.random()) * 10.0,
                              seed=int(rg.integers(0, 9973)), oct=2) - 0.5)
    side = np.cross(up, d0)
    P = (org[None, :] + d0[None, :] * s[:, None] + up[None, :] * z[:, None]
         + side[None, :] * wob[:, None])
    return P


def _children(par, parr, rg, n, nodes, kids, lenr, ang, grav):
    """Sub-branches on every parent, batched. Returns (M, n, 3), radii, and
    the parent index of each child."""
    if not len(par):
        return np.zeros((0, n, 3)), np.zeros((0, n)), np.zeros(0, np.int64)
    P, R, PAR = [], [], []
    up = np.array([0.0, 0.0, 1.0])
    for i in range(len(par)):
        pts = par[i]
        L_par = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
        nn = int(rg.integers(nodes[0], nodes[1] + 1))
        for a in range(nn):
            u = 0.30 + 0.66 * (a + float(rg.random()) * 0.6) / max(nn, 1)
            j = int(np.clip(u * (len(pts) - 1), 0, len(pts) - 2))
            f = u * (len(pts) - 1) - j
            org = pts[j] * (1 - f) + pts[j + 1] * f
            tan = _unit(pts[min(j + 1, len(pts) - 1)] - pts[j])
            side = np.cross(up, tan)
            if np.linalg.norm(side) < 1e-6:
                side = np.array([1.0, 0.0, 0.0])
            side = side / np.linalg.norm(side)
            nrm = np.cross(tan, side)
            k = int(rg.integers(kids[0], kids[1] + 1))
            for b in range(k):
                th = math.radians(float(rg.uniform(*ang)))
                ph = float(rg.uniform(0.0, 2.0 * np.pi))
                d = (math.cos(th) * tan
                     + math.sin(th) * (math.cos(ph) * side
                                       + math.sin(ph) * nrm))
                d = d / np.linalg.norm(d)
                L = L_par * lenr * (1.0 - 0.55 * u) * float(
                    rg.uniform(0.62, 1.32))
                if L < 0.035:
                    continue
                t = np.linspace(0.0, 1.0, n)
                s = L * t
                pp = (org[None, :] + d[None, :] * s[:, None]
                      + up[None, :] * (grav * L * (t ** 2))[:, None])
                P.append(pp)
                rb = max(float(parr[i][j]) * 0.55, 0.0035)
                R.append(np.linspace(rb, rb * 0.30, n))
                PAR.append(i)
    if not P:
        return np.zeros((0, n, 3)), np.zeros((0, n)), np.zeros(0, np.int64)
    return np.array(P), np.array(R), np.array(PAR, np.int64)


# ===========================================================================
# 7.  THE CANOPY -- shoots and needles, at the LOD's derived blade size
# ===========================================================================

SHOOT_LEN_M = 0.095
SHOOT_R_M = 0.0021
#: Needles per shoot. A Scots pine shoot carries fascicles at ~3 mm pitch over
#: its 95 mm, two needles to a sheath: 2 * 95/3 = 63. This is CONSTANT across
#: the ladder; see `canopy`.
NEEDLES_PER_SHOOT = 64
NEEDLE_PITCH_M = 0.0030
#: Blade silhouette area as a fraction of w * L. The blade is a quad tapering
#: from full width at the sheath to 0.30 w at the tip, which is what a Scots
#: pine needle does; 0.5 * (1 + 0.30) = 0.65.
BLADE_AREA_FRAC = 0.65
BLADE_TIP_FRAC = 0.30


def needle_target(sp, lod=0):
    """HOW MANY NEEDLES THIS TREE ACTUALLY HAS, from its leaf area.

    NOT from the branch structure, which is how the first version of this
    module got 846 241 needles on one tree: every branching parameter
    multiplies, so a canopy sized by "children per node" is sized by nothing.

    One-sided needle area = LAI x crown projection, and one blade carries
    BLADE_AREA_FRAC * w * L. For an 18 m ridge pine at LAI 1.5 and a 2.8 m
    crown radius that is 34 m^2 of needle and about 5.2 x 10^5 needles, which
    is the number section 0b's argument turns on.
    """
    _l, _d0, _d1, blade, frac = LOD_BANDS[min(lod, LOD_MAX)]
    area = sp["lai"] * math.pi * sp["crown_r"] ** 2
    one = BLADE_AREA_FRAC * sp["needle_w"] * sp["needle_l"]
    return int(round(area / max(one, 1e-12) * frac)), blade, frac


def canopy(sk, sp, lod):
    """-> (shoot polylines, shoot radii, needle quads, needle attributes).

    THE LADDER THINS SHOOTS AND NEVER THINS A SHOOT'S OWN NEEDLES. A shoot is
    the smallest thing a pine actually grows: 64 needles at a 3 mm pitch on a
    95 mm axis is not a parameter, it is the plant. So above the crossover the
    element that disappears is the WHOLE SHOOT, and the survivors' blades grow
    by the band's factor -- which conserves total projected area exactly
    (selftest [5] measures it) and, unlike thinning needles within a shoot,
    also removes the shoot's own wood, which is 0.85 px at the band's far edge
    and was costing 97 000 triangles a tree to be invisible.
    """
    target, blade, frac = needle_target(sp, lod)
    rg = sk["rg"]
    tips = sk["o3"] if len(sk["o3"]) else sk["o2"]
    empty = (np.zeros((0, ORD_N[3], 3)), np.zeros((0, ORD_N[3])),
             (np.zeros((0, 3)), np.zeros((0, 4), np.int64)), {})
    if not len(tips) or target < NEEDLES_PER_SHOOT:
        return empty
    n_shoot = max(1, int(round(target / float(NEEDLES_PER_SHOOT))))
    n_tip = len(tips)
    per = int(math.ceil(n_shoot / float(n_tip)))
    src = np.repeat(np.arange(n_tip), per)
    if len(src) > n_shoot:
        src = src[rg.permutation(len(src))[:n_shoot]]
    total = len(src)
    if total == 0:
        return empty
    # --- shoot axes: from the last third of each branchlet, fanned out -----
    base = tips[src, -2] + (tips[src, -1] - tips[src, -2]) * \
        rg.random(total)[:, None]
    tan = _unit(tips[src, -1] - tips[src, -3 if tips.shape[1] > 2 else 0])
    e1 = _unit(np.cross(tan, np.array([0.0, 0.0, 1.0]) + 1e-6))
    e2 = np.cross(tan, e1)
    th = rg.uniform(0.12, 0.60, total)
    ph = rg.uniform(0.0, 2 * np.pi, total)
    d = (np.cos(th)[:, None] * tan
         + np.sin(th)[:, None] * (np.cos(ph)[:, None] * e1
                                  + np.sin(ph)[:, None] * e2))
    d = _unit(d)
    sl = SHOOT_LEN_M * rg.uniform(0.68, 1.35, total)[:, None] * (
        1.0 + 0.9 * (blade - 1.0) / max(blade, 1.0))
    t3 = np.linspace(0.0, 1.0, ORD_N[3])
    SP = base[:, None, :] + d[:, None, :] * (sl[:, :, None] * t3[None, :, None])
    SP = SP + np.array([0.0, 0.0, 1.0])[None, None, :] * (
        0.16 * sl[:, :, None] * (t3 ** 2)[None, :, None])
    SR = np.linspace(SHOOT_R_M, SHOOT_R_M * 0.55, ORD_N[3])[None, :] * \
        np.ones((total, 1)) * max(blade * 0.55, 1.0)

    # --- needles -----------------------------------------------------------
    nps = NEEDLES_PER_SHOOT
    w = sp["needle_w"] * blade
    L = sp["needle_l"] * blade
    i = np.arange(nps)
    # phyllotaxis: golden angle, in FASCICLES OF TWO (Pinus sylvestris is a
    # diploxylon, two needles to a sheath, and the pair splays ~11 degrees)
    fasc = i // 2
    pair = (i % 2) * 2.0 - 1.0
    phi = fasc[None, :] * 2.399963 + rg.uniform(0, 2 * np.pi, total)[:, None]
    tt = ((fasc[None, :] + 0.5) / max(fasc.max() + 1, 1)) * 0.94 + 0.03
    # needles sweep FORWARD along the shoot at 52-72 degrees
    alp = np.radians(52.0 + 20.0 * rg.random((total, nps))) \
        + np.radians(5.5) * pair[None, :]
    ax = _unit(SP[:, -1] - SP[:, 0])
    q1 = _unit(np.cross(ax, np.array([0.0, 0.0, 1.0]) + 1e-6))
    q2 = np.cross(ax, q1)
    rad = (np.cos(phi)[:, :, None] * q1[:, None, :]
           + np.sin(phi)[:, :, None] * q2[:, None, :])
    nd = (np.cos(alp)[:, :, None] * ax[:, None, :]
          + np.sin(alp)[:, :, None] * rad)
    nd = _unit(nd)
    org = SP[:, 0][:, None, :] + ax[:, None, :] * (
        tt[:, :, None] * np.linalg.norm(SP[:, -1] - SP[:, 0],
                                        axis=1)[:, None, None])
    org = org + rad * (SR[:, :1][:, :, None] * 0.9)
    # THE BLADE IS A QUAD, NOT A TRIANGLE, AND THAT IS NOT A DETAIL. A
    # triangle from full width to a point has HALF the silhouette of a needle
    # of the same w and L, so a canopy built out of triangles is a canopy at
    # half its leaf area wearing the right numbers. It is also the wrong
    # SHAPE where it can be seen: at 4.577 m the blade is 1.39 px wide and
    # 47 px long, so a linear taper to nothing is a 47-px-long spike and a
    # Scots pine needle is a parallel blade that tapers only near the tip.
    hw = _unit(np.cross(nd, rad)) * (0.5 * w)
    ln = L * (0.80 + 0.36 * rg.random((total, nps)))[:, :, None]
    tip = org + nd * ln
    v0 = (org - hw).reshape(-1, 3)
    v1 = (org + hw).reshape(-1, 3)
    v2 = (tip + hw * BLADE_TIP_FRAC).reshape(-1, 3)
    v3 = (tip - hw * BLADE_TIP_FRAC).reshape(-1, 3)
    NV = np.concatenate([v0, v1, v2, v3], axis=0)
    m = len(v0)
    a = np.arange(m)
    NQ = np.stack([a, a + m, a + 2 * m, a + 3 * m], axis=1)
    # needle age: the shoot's own age band, 0 current year .. 1 third year
    age = np.clip(rg.random((total, nps)) * 0.55
                  + (1.0 - tt) * 0.55, 0.0, 1.0).reshape(-1)
    attrs = dict(nd_age=np.concatenate([age] * 4),
                 nd_t=np.concatenate([np.zeros(m), np.zeros(m),
                                      np.ones(m), np.ones(m)]))
    return SP, SR, (NV, NQ), attrs


# ===========================================================================
# 8.  CONES -- 50 mm, 41 px at the near band, so they are real geometry
# ===========================================================================

def cone_mesh(centre, axis, length, rg):
    """A Scots pine cone: an ovoid of ~7 spirals of scales. `RELIEF['cone']`
    puts the SCALE relief in the shader; the scale COURSES are mesh, because
    12 mm is 9.8 px at 4.577 m."""
    nz, na = 9, 11
    t = np.linspace(0.06, 1.0, nz)
    prof = np.sin(np.pi * t ** 0.78) ** 0.62
    r = prof * length * 0.31
    ax = _unit(np.asarray(axis, float))
    e1 = _unit(np.cross(ax, np.array([0.0, 0.0, 1.0]) + 1e-6))
    e2 = np.cross(ax, e1)
    ang = np.arange(na) * 2 * np.pi / na
    # the scales spiral: each ring is rolled by the golden angle
    roll = np.arange(nz) * 0.9
    A = ang[None, :] + roll[:, None]
    rr = r[:, None] * (1.0 + 0.16 * np.cos(na * 0.5 * A))
    P = (centre[None, None, :] + ax[None, None, :] * (t * length)[:, None, None]
         + e1[None, None, :] * (rr * np.cos(A))[:, :, None]
         + e2[None, None, :] * (rr * np.sin(A))[:, :, None])
    V = P.reshape(-1, 3)
    idx = np.arange(nz * na).reshape(nz, na)
    nxt = np.roll(np.arange(na), -1)
    Q = np.stack([idx[:-1, :], idx[1:, :], idx[1:, :][:, nxt],
                  idx[:-1, :][:, nxt]], axis=-1).reshape(-1, 4)
    return V, Q


# ===========================================================================
# 9.  ONE TREE, ASSEMBLED
# ===========================================================================

def tree_mesh(sp, lod=0):
    """-> (verts, quads, tris, face material index, vertex attributes, stats)."""
    sk = skeleton(sp, lod)
    acc = Acc()
    h = sp["h"]
    amp_plate = relief_mm("plate") * 1e-3       # metres, p-p, FROM THE LAW

    def bark_attrs(V, u, v, radius, order, dead=0.0):
        z = V[:, 2]
        return dict(
            bk_u=u.ravel(), bk_v=v.ravel(),
            bk_r=np.broadcast_to(radius, u.shape).ravel(),
            bk_h=np.clip(z / max(h, 1e-6), 0.0, 1.0),
            bk_ord=np.full(u.size, order / 4.0),
            bk_dead=np.full(u.size, dead),
            bk_seed=np.full(u.size, sp["rseed"] % 1000 / 1000.0),
        )

    # --- trunk -------------------------------------------------------------
    P = sk["trunk"][None, :, :]
    R = sk["trunk_r"][None, :]
    sides = sk["trunk_sides"]
    circ = 2.0 * np.pi * float(np.median(sk["trunk_r"]))
    uu = (np.arange(sides)[None, :] / sides) * np.maximum(
        2.0 * np.pi * sk["trunk_r"][:, None], 1e-3)
    vv = np.repeat(sk["trunk_z"][:, None], sides, axis=1)
    plate, dr01, _cid = bark_plate_field(uu, vv, sp["plate_lam"],
                                         sp["rseed"] % 65536)
    # the plate relief fades out with member radius: a 30 mm branch cannot
    # carry a 110 mm plate, and above the orange onset the bark is papery
    fade = K.clamp01((sk["trunk_r"][:, None] - 0.030) / 0.070) * (
        1.0 - 0.72 * K.smoothstep(sp["orange_onset"] * 0.9,
                                  sp["orange_onset"] * 1.25,
                                  sk["trunk_z"][:, None] / max(h, 1e-6)))
    dr = (dr01 * amp_plate * fade)[None, :, :]
    V, Q, _N, _B, _T, _ang = tube_batch(P, R, sides, dr=dr)
    at = bark_attrs(V, uu, vv, sk["trunk_r"][:, None], 0)
    at["bk_plate"] = plate.ravel()
    acc.add(V, quads=Q, mat=MAT_BARK, attrs=at)
    trunk_tris = len(Q) * 2

    # --- dead lower stubs ---------------------------------------------------
    rg = sk["rg"]
    if sp["stubs"] > 0 and sk["cb"] > 1.4:
        zs = rg.uniform(1.0, sk["cb"] * 0.97, sp["stubs"])
        SP = []
        SR = []
        for zz in zs:
            org, r0 = sk["trunk_at"](float(zz))
            phi = float(rg.uniform(0, 2 * np.pi))
            L = float(rg.uniform(0.10, 0.62))
            d = np.array([math.cos(phi), math.sin(phi),
                          float(rg.uniform(-0.45, -0.05))])
            d = d / np.linalg.norm(d)
            t = np.linspace(0.0, 1.0, ORD_N[1])
            SP.append(org[None, :] + d[None, :] * (L * t)[:, None])
            rb = max(r0 * 0.16, 0.012)
            SR.append(np.linspace(rb, rb * 0.42, ORD_N[1]))
        SP = np.array(SP)
        SR = np.array(SR)
        V, Q, _n, _b, _t, _a = tube_batch(SP, SR, ORD_SIDES[1])
        uu2 = np.tile((np.arange(ORD_SIDES[1]) / ORD_SIDES[1])[None, :],
                      (SP.shape[0] * SP.shape[1], 1)) * 0.10
        vv2 = np.repeat(np.linspace(0, 0.5, SP.shape[1])[None, :],
                        SP.shape[0], 0).reshape(-1)[:, None] * np.ones(
                            (1, ORD_SIDES[1]))
        at = bark_attrs(V, uu2, vv2, 0.02, 1, dead=1.0)
        at["bk_plate"] = np.ones(len(V))
        acc.add(V, quads=Q, mat=MAT_BARK, attrs=at)

    # --- branch orders 1..3 -------------------------------------------------
    for o, (Pb, Rb) in enumerate(((sk["o1"], sk["o1r"]),
                                  (sk["o2"], sk["o2r"]),
                                  (sk["o3"], sk["o3r"])), start=1):
        if not len(Pb):
            continue
        sd = ORD_SIDES[o - 1]
        V, Q, _n, _b, _t, _a = tube_batch(Pb, Rb, sd)
        M, n = Pb.shape[0], Pb.shape[1]
        uu2 = np.tile((np.arange(sd) / sd)[None, :], (M * n, 1)) * \
            np.repeat((2 * np.pi * Rb).reshape(-1, 1), 1, axis=1)
        seg = np.cumsum(np.concatenate(
            [np.zeros((M, 1)), np.linalg.norm(np.diff(Pb, axis=1), axis=2)],
            axis=1), axis=1)
        vv2 = np.repeat(seg.reshape(-1, 1), sd, axis=1)
        at = bark_attrs(V, uu2, vv2, Rb.reshape(-1, 1), o)
        at["bk_plate"] = np.ones(len(V))
        acc.add(V, quads=Q, mat=MAT_BARK, attrs=at)

    # --- canopy -------------------------------------------------------------
    SP, SR, (NV, NQ), nat = canopy(sk, sp, lod)
    n_needles = 0
    if len(SP):
        V, Q, _n, _b, _t, _a = tube_batch(SP, SR, ORD_SIDES[3])
        M, n = SP.shape[0], SP.shape[1]
        uu2 = np.tile((np.arange(ORD_SIDES[3]) / ORD_SIDES[3])[None, :],
                      (M * n, 1)) * 0.013
        vv2 = np.repeat(np.linspace(0, SHOOT_LEN_M, n)[None, :],
                        M, 0).reshape(-1, 1) * np.ones((1, ORD_SIDES[3]))
        at = bark_attrs(V, uu2, vv2, SHOOT_R_M, 4)
        at["bk_plate"] = np.ones(len(V))
        acc.add(V, quads=Q, mat=MAT_BARK, attrs=at)
    if len(NV):
        n_needles = len(NQ)
        at = dict(nat)
        at.update(bk_u=np.zeros(len(NV)), bk_v=np.zeros(len(NV)),
                  bk_r=np.zeros(len(NV)), bk_h=np.clip(
                      NV[:, 2] / max(h, 1e-6), 0, 1),
                  bk_ord=np.ones(len(NV)), bk_dead=np.zeros(len(NV)),
                  bk_plate=np.ones(len(NV)),
                  bk_seed=np.full(len(NV), sp["rseed"] % 1000 / 1000.0))
        acc.add(NV, quads=NQ, mat=MAT_NEEDLE, attrs=at)

    # --- cones --------------------------------------------------------------
    n_cones = 0
    cone_host = sk["o3"] if len(sk["o3"]) else sk["o2"]
    if sp["cones"] > 0 and len(cone_host):
        pick = rg.integers(0, len(cone_host), sp["cones"])
        for pi in pick:
            b = cone_host[pi]
            c = b[-1]
            ax = _unit(b[-1] - b[0]) * 0.4 + np.array([0.0, 0.0, -0.9])
            Vc, Qc = cone_mesh(c, ax, float(rg.uniform(0.036, 0.062)), rg)
            acc.add(Vc, quads=Qc, mat=MAT_CONE, attrs=dict(
                bk_u=np.zeros(len(Vc)), bk_v=np.zeros(len(Vc)),
                bk_r=np.full(len(Vc), 0.012),
                bk_h=np.clip(Vc[:, 2] / max(h, 1e-6), 0, 1),
                bk_ord=np.ones(len(Vc)), bk_dead=np.zeros(len(Vc)),
                bk_plate=np.ones(len(Vc)),
                bk_seed=np.full(len(Vc), sp["rseed"] % 1000 / 1000.0)))
            n_cones += 1

    V, Q, T, M, A = acc.finish()
    stats = dict(verts=len(V), quads=0 if Q is None else len(Q),
                 tris=0 if T is None else len(T),
                 triangles=(0 if Q is None else 2 * len(Q))
                 + (0 if T is None else len(T)),
                 needles=n_needles, shoots=len(SP), cones=n_cones,
                 branches=len(sk["o1"]) + len(sk["o2"]) + len(sk["o3"]),
                 whorls=len(sk["whorl_z"]), trunk_triangles=trunk_tris,
                 crown_base_m=sk["cb"], top_m=sk["top"])
    return V, Q, T, M, A, stats


def needle_area_m2(sp, lod):
    """Total ONE-SIDED projected needle area of a source at `lod`.

    The quantity the LOD ladder conserves. selftest [5] measures it across
    the ladder; if it is not conserved, the ladder is a lie about size.
    """
    _l, _d0, _d1, blade, frac = LOD_BANDS[min(lod, LOD_MAX)]
    sk = skeleton(sp, lod)
    _SP, _SR, (_NV, NQ), _a = canopy(sk, sp, lod)
    # a blade is a quad, full width at the sheath and BLADE_TIP_FRAC at the
    # tip; the 0.98 is the mean of the per-needle length jitter.
    return (BLADE_AREA_FRAC * (sp["needle_w"] * blade)
            * (sp["needle_l"] * blade * 0.98) * len(NQ))


# ===========================================================================
# 10.  MATERIALS
# ===========================================================================
#
# Three, and each one is a history rather than a colour:
#   bark    two zones (grey plated below, fox-orange flaking above), the
#           fissure network the MESH already carries darkened in register
#           with it, lichen on the north-ish side, and a three-stage relief
#           chain finer than the mesh's own pitch
#   needle  age banding, the sheath, a glaucous wax cast and a ripple
#   cone    the scale courses
#
# Every wavelength is stated with `wavelength_m=`; no raw `scale=` appears in
# this file, which is the shape of the 2.17x Voronoi error the brief warns
# about (`itemkit.VORONOI_WAVELENGTH_FACTOR`).

def _hex(h):
    return K.srgb_linear(h)


PAL = dict(
    bark_plate=_hex("#6b5847"),      # weathered grey-brown plate face
    bark_plate2=_hex("#8a7761"),     # a shed plate, paler
    bark_fissure=_hex("#241a12"),    # the fissure floor
    bark_orange=_hex("#c06a2c"),     # fox red, the species' signature
    bark_orange2=_hex("#dc9a56"),    # a fresh flake edge
    bark_orange_dk=_hex("#7a3a18"),
    dead=_hex("#9a9184"),            # silvered dead stub
    lichen=_hex("#a7ae94"),
    needle_new=_hex("#4d6b3c"),
    needle_old=_hex("#39522f"),
    needle_glauc=_hex("#6f8a72"),    # the waxy blue-green bloom
    needle_sheath=_hex("#6b5a3a"),
    needle_dead=_hex("#8a6a3c"),
    cone=_hex("#6a5744"),
    cone_dk=_hex("#33281d"),
)


def _attr(t, name):
    return t.attr(name, out=2, typ="GEOMETRY")


def mat_bark(name=PFX + "Bark"):
    t = K.NT(name)
    oc = t.object_coords()
    u = _attr(t, "bk_u")
    v = _attr(t, "bk_v")
    hgt = _attr(t, "bk_h")
    ordn = _attr(t, "bk_ord")
    dead = _attr(t, "bk_dead")
    plate = _attr(t, "bk_plate")
    seed = _attr(t, "bk_seed")
    # THE BARK COORDINATE. u is arc length around the member and v is distance
    # along it, both in METRES and both intrinsic to the mesh -- so a plate
    # field built on them is correct on the trunk and on a 12 mm branchlet
    # alike, and has no world scale to lose precision in. `TexCoord -> Object`
    # (Law 6) still drives everything that is genuinely a property of the
    # TREE rather than of the member: the orange zone, the moisture drift.
    uv = t.comb(u, v, (t.math("MULTIPLY", seed, 3.0)))

    # --- zone: grey plated below, orange flaking above ---------------------
    # onset drifts with a low-frequency noise so the boundary is ragged, which
    # is what it is on a real trunk -- it follows the bark's own shedding.
    onset = t.math("ADD",
                   t.maprange(seed, 0.0, 1.0, 0.42, 0.68),
                   t.math("MULTIPLY",
                          t.math("SUBTRACT", t.noise(oc, wavelength_m=0.85,
                                                     detail=3.0), 0.5), 0.16))
    zone = t.maprange(hgt, t.math("SUBTRACT", onset, 0.10),
                      t.math("ADD", onset, 0.08), 0.0, 1.0)
    # branches above order 1 are orange whatever their height: the limbs of a
    # Scots pine are the same fox red as the upper trunk.
    zone = t.math("MAXIMUM", zone, t.maprange(ordn, 0.20, 0.55, 0.0, 1.0))

    # --- the plate field, in register with the MESH ------------------------
    # `bk_plate` is the same 0-in-a-fissure field the geometry was displaced
    # by, so the dark line and the groove are the SAME feature. A shader that
    # invents its own fissures on top of a displaced mesh gives a surface two
    # unrelated networks, which is what "texture painted on" looks like.
    fis = t.maprange(plate, 0.02, 0.55, 0.0, 1.0)
    # sub-plate cracking, finer than the mesh can carry
    crk = t.vor(uv, wavelength_m=RELIEF["flake"]["lam"], feature="DISTANCE_TO_EDGE")
    crk01 = t.maprange(crk, 0.0, 0.0042, 0.0, 1.0)
    chk = t.vor(uv, wavelength_m=RELIEF["checking"]["lam"],
                feature="DISTANCE_TO_EDGE")
    chk01 = t.maprange(chk, 0.0, 0.0013, 0.0, 1.0)
    grain = t.noise(uv, wavelength_m=RELIEF["grain"]["lam"], detail=6.0,
                    rough=0.62)

    # --- colour ------------------------------------------------------------
    mottle = t.noise(uv, wavelength_m=0.24, detail=5.0, rough=0.55)
    lower = t.cmix(mottle, PAL["bark_plate"], PAL["bark_plate2"])
    lower = t.cmix(t.math("MULTIPLY", t.math("SUBTRACT", 1.0, fis), 0.92),
                   lower, PAL["bark_fissure"])
    upper = t.cmix(t.noise(uv, wavelength_m=0.055, detail=4.0),
                   PAL["bark_orange"], PAL["bark_orange2"])
    upper = t.cmix(t.math("MULTIPLY", t.math("SUBTRACT", 1.0, crk01), 0.75),
                   upper, PAL["bark_orange_dk"])
    col = t.cmix(zone, lower, upper)
    # dead stubs silver and lose the orange entirely
    col = t.cmix(dead, col, PAL["dead"])
    # lichen: a crustose patch field, weighted to the lower trunk
    lic = t.vor(t.vmath("ADD", oc, (3.1, 0.0, 0.0)), wavelength_m=0.16,
                feature="F1")
    licm = t.math("MULTIPLY",
                  t.maprange(lic, 0.030, 0.058, 1.0, 0.0),
                  t.maprange(hgt, 0.02, 0.34, 0.85, 0.0))
    col = t.cmix(licm, col, PAL["lichen"])
    col = t.cmix(t.math("MULTIPLY", grain, 0.30), col,
                 t.cmix(0.5, PAL["bark_fissure"], PAL["bark_plate2"]))

    # --- roughness ---------------------------------------------------------
    rough = t.fmix(zone, 0.94, 0.80)
    rough = t.fmix(t.math("MULTIPLY", fis, 0.6), rough, 0.99)
    rough = t.fmix(t.math("MULTIPLY", grain, 0.5), rough, 0.86)

    # --- RELIEF, coarse to fine, chained BY NAME ---------------------------
    # Every amplitude comes from RELIEF via K.relief_amplitude_for. Strictly
    # finer than the mesh's 34 mm ring pitch, so the two layers are disjoint.
    b = t.bump(crk01, 1.0, modulation_pp=RELIEF["flake"]["m"],
               wavelength_m=RELIEF["flake"]["lam"], height_pp=1.0)
    b = t.bump(chk01, 1.0, modulation_pp=RELIEF["checking"]["m"],
               wavelength_m=RELIEF["checking"]["lam"], normal=b, height_pp=1.0)
    b = t.bump(grain, 1.0, modulation_pp=RELIEF["grain"]["m"],
               wavelength_m=RELIEF["grain"]["lam"], normal=b, height_pp=0.6)

    bsdf = t.principled_out(base_color=col, roughness=rough, metallic=0.0)
    # R2-057: `Normal` is index 6 on Blender 5.2 and `Thin Wall` is 5. BY NAME.
    t.pin_named(bsdf, "Normal", b)
    return t


def mat_needle(name=PFX + "Needle"):
    t = K.NT(name)
    oc = t.object_coords()
    age = _attr(t, "nd_age")
    along = _attr(t, "nd_t")
    seed = _attr(t, "bk_seed")
    # A needle's own surface coordinate: along the blade, offset per tree.
    nv = t.comb(along, t.math("MULTIPLY", seed, 7.0), 0.0)
    # colour: current year green, second year darker, third year going brown
    col = t.cmix(age, PAL["needle_new"], PAL["needle_old"])
    col = t.cmix(t.maprange(age, 0.78, 1.0, 0.0, 0.55), col, PAL["needle_dead"])
    # the glaucous wax bloom, strongest on the current year
    wax = t.math("MULTIPLY", t.maprange(age, 0.0, 0.6, 0.85, 0.15),
                 t.noise(oc, wavelength_m=0.32, detail=3.0))
    col = t.cmix(wax, col, PAL["needle_glauc"])
    # the sheath at the base of the fascicle
    col = t.cmix(t.maprange(along, 0.0, 0.09, 1.0, 0.0), col,
                 PAL["needle_sheath"])
    # per-needle tonal spread: a canopy whose needles are all one value reads
    # as a solid. This is the mechanism the canopy's sparkle comes from.
    spread = t.noise(oc, wavelength_m=0.045, detail=5.0, rough=0.62)
    col = t.cmix(t.math("MULTIPLY", spread, 0.32), col, PAL["needle_old"])
    rough = t.fmix(age, 0.30, 0.52)
    rough = t.fmix(t.math("MULTIPLY", spread, 0.5), rough, 0.42)
    # RELIEF: the blade's own ripple. 12 mm is 9.8 px at 4.577 m and 1.4 px at
    # the full-tree framing, so it is the finest needle-borne relief that
    # survives. The 0.3 mm twist and the 0.25 mm stomatal rows are DECLINED --
    # see DECLINED, they are 0.24 px and 0.20 px at the near band.
    rip = t.wave(nv, wavelength_m=RELIEF["needle"]["lam"], distortion=1.4,
                 detail=2.0)
    b = t.bump(rip, 1.0, modulation_pp=RELIEF["needle"]["m"],
               wavelength_m=RELIEF["needle"]["lam"], height_pp=1.0)
    bsdf = t.principled_out(base_color=col, roughness=rough, metallic=0.0)
    t.pin_named(bsdf, "Normal", b)
    # needles are 1.7 mm of translucent tissue and the film's sun rakes at
    # 12.5 deg, so a canopy is edge-lit for most of the lap.
    t.pin_named(bsdf, "Subsurface Weight", 0.14)
    for nm in ("Subsurface Radius",):
        try:
            t.pin_named(bsdf, nm, (0.006, 0.010, 0.004))
        except RuntimeError:
            pass
    return t


def mat_cone(name=PFX + "Cone"):
    t = K.NT(name)
    oc = t.object_coords()
    seed = _attr(t, "bk_seed")
    uv = t.comb(t.sep(oc, 0), t.sep(oc, 2), t.math("MULTIPLY", seed, 5.0))
    sc = t.vor(uv, wavelength_m=RELIEF["cone"]["lam"],
               feature="DISTANCE_TO_EDGE")
    sc01 = t.maprange(sc, 0.0, 0.0018, 0.0, 1.0)
    col = t.cmix(t.noise(uv, wavelength_m=0.020, detail=4.0),
                 PAL["cone"], PAL["cone_dk"])
    col = t.cmix(t.math("MULTIPLY", t.math("SUBTRACT", 1.0, sc01), 0.8),
                 col, PAL["cone_dk"])
    rough = t.fmix(sc01, 0.92, 0.70)
    b = t.bump(sc01, 1.0, modulation_pp=RELIEF["cone"]["m"],
               wavelength_m=RELIEF["cone"]["lam"], height_pp=1.0)
    bsdf = t.principled_out(base_color=col, roughness=rough)
    t.pin_named(bsdf, "Normal", b)
    return t


_MATS = {}


def materials():
    if not _MATS:
        _MATS["bark"] = mat_bark().m
        _MATS["needle"] = mat_needle().m
        _MATS["cone"] = mat_cone().m
    return _MATS


# ===========================================================================
# 11.  EMIT
# ===========================================================================

def purge():
    K.purge(PFX, COLL)
    for nm in list(bpy.data.node_groups.keys()):
        if nm.startswith(PFX):
            bpy.data.node_groups.remove(bpy.data.node_groups[nm])


def build_source(sp, coll, lod=0, name=None):
    """One source tree as one object, origin at the trunk butt."""
    V, Q, T, M, A, stats = tree_mesh(sp, lod)
    nm = name or (PFX + "Pine%03d" % sp["uid"])
    # recentre=False, DELIBERATELY: section 0g. The origin is the butt, which
    # is what `GeometryNodeCollectionInfo(Reset Children)` drops on the point
    # and what every dependant needs; |P| <= 23 m, so the Object-space
    # procedural has nothing to lose precision in.
    me, off = K.new_mesh(nm, V, quads=Q, tris=T, smooth_deg=34.0,
                         recentre=False, orient=True)
    if M is not None and len(M) == len(me.polygons):
        me.polygons.foreach_set("material_index", np.ascontiguousarray(M, np.int32))
    K.bake_attributes(me, A)
    mats = materials()
    for m in (mats["bark"], mats["needle"], mats["cone"]):
        me.materials.append(m)
    ob = bpy.data.objects.new(nm, me)
    ob.location = (0.0, 0.0, 0.0)
    coll.objects.link(ob)
    for k, v in stats.items():
        ob["tsp_" + k] = v
    ob["tsp_lod"] = int(lod)
    ob["tsp_h"] = float(sp["h"])
    ob["tsp_form"] = sp["form"]
    return ob, stats


# --- the instancer ---------------------------------------------------------

def _scatter_node_group(name, library, n_sources, seed):
    """Instance a LIBRARY of distinct sources onto points.

    Shaped on `spectator_seated._crowd_node_group`, which is the emission the
    gate's STRONG variety path can walk: `depsgraph.object_instances` sees one
    realized instance per point, each carrying the source datablock it picked.
    An item that pre-flattens its instances scores UNPROVEN, which is a FAIL.
    """
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); gi.location = (-800, 0)
    go = ng.nodes.new("NodeGroupOutput"); go.location = (700, 0)
    ci = ng.nodes.new("GeometryNodeCollectionInfo"); ci.location = (-800, -240)
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); iop.location = (250, 0)
    iop.inputs["Pick Instance"].default_value = True

    ridx = ng.nodes.new("FunctionNodeRandomValue"); ridx.location = (-380, -500)
    ridx.data_type = "INT"
    for s in ridx.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = 0
        elif s.name == "Max":
            s.default_value = max(0, n_sources - 1)
        elif s.name == "Seed":
            s.default_value = int(seed) % 30000

    rrot = ng.nodes.new("FunctionNodeRandomValue"); rrot.location = (-380, -760)
    rrot.data_type = "FLOAT_VECTOR"
    for s in rrot.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = (-0.030, -0.030, -math.pi)
        elif s.name == "Max":
            s.default_value = (0.030, 0.030, math.pi)
        elif s.name == "Seed":
            s.default_value = (int(seed) + 7717) % 30000

    rscl = ng.nodes.new("FunctionNodeRandomValue"); rscl.location = (-380, -1020)
    rscl.data_type = "FLOAT"
    for s in rscl.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = 0.82
        elif s.name == "Max":
            s.default_value = 1.22
        elif s.name == "Seed":
            s.default_value = (int(seed) + 4241) % 30000

    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    for s in ridx.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Instance Index"]); break
    for s in rrot.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Rotation"]); break
    for s in rscl.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Scale"]); break
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    return ng


def scatter_points(n, centre, radius, exclude_r=0.0, seed=4242, min_gap=6.5):
    """`n` stand positions on the ridge, Poisson-thinned so no two pines are
    closer than `min_gap` -- a stand at uniform random spacing reads as
    scattered confetti, and Scots pine on an exposed ridge stands at 7-16 m.
    z comes from `ground_z`, never an assumed plane."""
    rg = np.random.default_rng(seed)
    pts = []
    tries = 0
    cell = min_gap
    grid = {}
    while len(pts) < n and tries < n * 60:
        tries += 1
        a = rg.uniform(0, 2 * np.pi)
        r = radius * math.sqrt(rg.random())
        x = centre[0] + r * math.cos(a)
        y = centre[1] + r * math.sin(a)
        if math.hypot(x - centre[0], y - centre[1]) < exclude_r:
            continue
        gx, gy = int(x // cell), int(y // cell)
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for (px, py) in grid.get((gx + dx, gy + dy), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < min_gap ** 2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        grid.setdefault((gx, gy), []).append((x, y))
        pts.append((x, y))
    P = np.array(pts) if pts else np.zeros((0, 2))
    if not len(P):
        return P.reshape(0, 3)
    z = seat_z(P[:, 0], P[:, 1])
    return np.stack([P[:, 0], P[:, 1], np.asarray(z, float).ravel()], axis=1)


# --- the ridge the stand grows on ------------------------------------------
#: The exposed ridge that carries the esses. `build_terrain`'s own `ridge`
#: view stands at (-330, 250, 26) and looks at (-300, 640, 12); MIX_EXPOSED
#: there puts pine at 0.40 of the mix, which is the manifest's own
#: variation axis "40 % of the exposed ridge mix".
RIDGE_CENTRE = (-322.0, 372.0)
RIDGE_RADIUS = 190.0
STAND_RADIUS = 46.0

N_SOURCES = 44          # >= the gate's 40 at 4 200 realized instances


def build(lod_anchor=None, scene=None, n_sources=N_SOURCES,
          instances=INSTANCES_DECLARED, lod=None, stats=None, seed=90210):
    """Emit `n_sources` distinct pines plus one instancer into `COLL`.

    `lod_anchor` grades the LOD of each SOURCE by its distance to the anchor,
    exactly as `pit_wall_unit` does; with no anchor everything is built at the
    band the module is gated in (L0). `lod=` overrides both.
    """
    scene = scene or bpy.context.scene
    purge()
    root = K.coll(COLL)
    src = K.coll(SRC_COLL, root)
    materials()

    stand = scatter_points(n_sources, RIDGE_CENTRE, STAND_RADIUS,
                           seed=seed + 1, min_gap=7.5)
    if len(stand) < n_sources:
        raise RuntimeError(
            "only %d of %d stand positions found in a %.0f m radius at a "
            "%.1f m minimum gap -- widen STAND_RADIUS rather than crowding "
            "the trees, which is the one thing a stand cannot be."
            % (len(stand), n_sources, STAND_RADIUS, 7.5))

    t0 = time.time()
    tot = 0
    per = []
    objs = []
    for i in range(n_sources):
        sp = tree_spec(i, seed)
        if lod is not None:
            L = int(lod)
        elif lod_anchor is None:
            L = 0
        else:
            A = np.asarray(lod_anchor, float).reshape(-1, 3)
            d = float(np.min(np.linalg.norm(A - stand[i][None, :], axis=1)))
            L = lod_of(d)
        ob, st = build_source(sp, src, lod=L)
        ob.location = (float(stand[i][0]), float(stand[i][1]),
                       float(stand[i][2]))
        objs.append(ob)
        per.append(st)
        tot += st["triangles"]
        if (i + 1) % 8 == 0:
            log("  %2d/%d sources, %.2f M tris, %.0f s"
                % (i + 1, n_sources, tot / 1e6, time.time() - t0))
    log("sources: %d, %.2f M triangles, %.0f s"
        % (n_sources, tot / 1e6, time.time() - t0))

    # --- the instancer ------------------------------------------------------
    pts = scatter_points(instances, RIDGE_CENTRE, RIDGE_RADIUS,
                         exclude_r=STAND_RADIUS + 8.0, seed=seed + 2,
                         min_gap=6.5)
    me = bpy.data.meshes.new(PFX + "RidgeScatter")
    me.from_pydata([tuple(p) for p in pts], [], [])
    me.update()
    inst = bpy.data.objects.new(PFX + "RidgeScatter", me)
    root.objects.link(inst)
    ng = _scatter_node_group(PFX + "ScatterGN", src, n_sources, seed + 3)
    md = inst.modifiers.new("scatter", "NODES")
    md.node_group = ng
    inst["instances_realized"] = len(pts)
    inst["instances_declared"] = int(instances)
    inst["library_sources"] = int(n_sources)
    log("instancer: %d points from %d distinct sources (%.3f %% each)"
        % (len(pts), n_sources, 100.0 / max(n_sources, 1)))

    if stats is not None:
        stats.update(sources=n_sources, triangles=tot, per=per,
                     realized=len(pts), stand=stand.tolist())
    return root


# ===========================================================================
# 12.  THE TEST SCENE
# ===========================================================================

def _standin_ground(coll, centre, span, res=260):
    """The ridge itself, from `build_terrain`'s own analytic field.

    Named XPFX + "Standin_..." so `item_gate`'s CONTEXT_PAT drops it: it is
    another module's surface and measuring it as part of this item is the
    error that put a `CTX_Column` on record as a marshal post deck.
    """
    xs = np.linspace(centre[0] - span * 0.5, centre[0] + span * 0.5, res)
    ys = np.linspace(centre[1] - span * 0.5, centre[1] + span * 0.5, res)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z, _own = ground_z(X.ravel(), Y.ravel())
    V = np.stack([X.ravel(), Y.ravel(), np.asarray(Z, float).ravel()], axis=1)
    idx = np.arange(res * res).reshape(res, res)
    q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], axis=1)
    nm = XPFX + "Standin_Ground"
    me, off = K.new_mesh(nm, V, quads=q, smooth_deg=None, recentre=True)
    ob = bpy.data.objects.new(nm, me)
    ob.location = off
    t = K.NT(XPFX + "Standin_Turf")
    oc = t.object_coords()
    col = t.cmix(t.noise(oc, wavelength_m=2.4, detail=6.0),
                 _hex("#4a4a2c"), _hex("#6a6640"))
    t.principled_out(base_color=col, roughness=0.92)
    me.materials.append(t.m)
    coll.objects.link(ob)
    return ob


def hero_source(objs):
    """Which tree the macro stands in front of. NOT the best one: the one
    whose triangle count is the MEDIAN, which is the subject `item_gate`
    itself would pick, so the deliverable macro and the gate's witness are
    pictures of the same object."""
    ranked = sorted(objs, key=lambda o: (len(o.data.polygons), o.name))
    return ranked[len(ranked) // 2]


def test_scene(samples=256, n_sources=N_SOURCES, instances=INSTANCES_DECLARED,
               lod=None, seed=90210):
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    st = {}
    root = build(scene=scene, n_sources=n_sources, instances=instances,
                 lod=lod, stats=st, seed=seed)
    src = bpy.data.collections.get(SRC_COLL)
    cams = K.coll(COLL + "/Cameras", root)
    stand = K.coll(COLL + "/Standins", root)
    K.contract_sun(PFX, scene=scene, coll_=root)
    _standin_ground(stand, RIDGE_CENTRE, 2.0 * (RIDGE_RADIUS + 60.0))

    hero = hero_source([o for o in src.objects if o.type == "MESH"])
    log("hero source %s: %d polys, h %.2f m, form %s"
        % (hero.name, len(hero.data.polygons), hero["tsp_h"], hero["tsp_form"]))

    # --- the deliverable macro, at the STATED near framing ------------------
    # The aim point is the median vertex of the hero, which is where
    # `item_gate.stage_witness` aims too, so the macro and the witness are
    # the same shot at the same distance on the same lens.
    co = np.empty(len(hero.data.vertices) * 3, np.float64)
    hero.data.vertices.foreach_get("co", co)
    med = np.median(co.reshape(-1, 3), axis=0) + np.array(hero.location)
    az = math.radians(126.0)
    el = math.radians(20.0)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                  math.sin(el)])
    loc = med + d * FILMED_NEAR_M
    K.macro_rig(PFX + "CAM_MACRO_4K", tuple(float(v) for v in loc),
                tuple(float(v) for v in med), LENS_MM, cams, scene=scene,
                samples=samples, want_distance_m=FILMED_NEAR_M,
                tolerance_m=0.02)

    # --- the bracket cameras. Same lens, the other ends of the band. -------
    base = np.array(hero.location) + np.array([0.0, 0.0, hero["tsp_h"] * 0.52])
    for nm, dist, elev in ((PFX + "CAM_FULL_31M", FILMED_FULL_M, 9.0),
                           (PFX + "CAM_FAR_224M", FILMED_FAR_M, 4.0)):
        e = math.radians(elev)
        dd = np.array([math.cos(e) * math.cos(az), math.cos(e) * math.sin(az),
                       math.sin(e)])
        K.add_camera(nm, tuple(float(v) for v in (base + dd * dist)),
                     tuple(float(v) for v in base), LENS_MM, cams)
    # the bark, at the near band, square on the lower trunk
    bz = np.array(hero.location) + np.array([0.0, 0.0, 1.55])
    K.add_camera(PFX + "CAM_BARK", tuple(float(v) for v in (
        bz + np.array([math.cos(az), math.sin(az), 0.09]) * 1.10)),
        tuple(float(v) for v in bz), 58.0, cams)

    K.assert_no_external_assets()
    log("triangles %.3f M over %d sources; %d realized instances"
        % (st["triangles"] / 1e6, st["sources"], st["realized"]))
    return root, st


# ===========================================================================
# 13.  THE INTERFACE FILE
# ===========================================================================

def interface_json(path=None, n_sources=N_SOURCES):
    specs = [tree_spec(i) for i in range(n_sources)]
    doc = K.interface_json(
        ITEM,
        path=path,
        version=__version__,
        collection=COLL, sources_collection=SRC_COLL, prefix=PFX,
        module="world/items/tree_scots_pine.py",
        species="Pinus sylvestris",
        framing=dict(
            status="HOST BOUND, NOT A MEASUREMENT OF THIS ITEM",
            why=("screen_presence.json's presence_unverified_2026_08_04 block "
                 "states these are host upper bounds and that a HERO verdict "
                 "on an ABSENT item must not be quoted without the qualifier. "
                 "tree_scots_pine is unbuilt; its 93 hosts are the ground and "
                 "the shrub scatter. All five tree species report the same "
                 "min_depth_m 4.577, which is one host measured five times."),
            lens_mm=LENS_MM,
            build_band_m=[FILMED_NEAR_M, FILMED_FAR_M],
            gated_at_m=GATE_AT_M,
            gated_px_4k=GATE_PX_4K,
            host_min_depth_m=FILMED_NEAR_M,
            full_frame_m=FILMED_FULL_M,
            px300_m=FILMED_FAR_M,
            manifest_says=dict(nearest_camera_m=30.0, hero=False,
                               onscreen_px_4k=2160),
            manifest_error=("under-frames by %.2fx and flags a 21-item "
                            "macro-band object non-hero"
                            % (30.0 / FILMED_NEAR_M)),
            what_would_settle_it=("place this module's instancer into the "
                                  "assembled world and re-run tools/retier.sh "
                                  "/ tools/item_presence.py so the pine is "
                                  "measured as itself"),
        ),
        needles=dict(
            blade_m=[NEEDLE_W_M, NEEDLE_L_M],
            fascicle=2,
            crossover_1px_m=one_px_distance_m(NEEDLE_W_M),
            crossover_half_px_m=one_px_distance_m(NEEDLE_W_M) / NEEDLE_MIN_PX,
            per_shoot_L0=NEEDLES_PER_SHOOT,
            lod_bands=[dict(lod=l, d0_m=d0, d1_m=d1, blade_scale=s,
                            count_fraction=f) for l, d0, d1, s, f in LOD_BANDS],
            declined=[dict(feature=n, size_m=s,
                           px_at_near_band=px_of(s, FILMED_NEAR_M), why=w)
                      for n, s, w in DECLINED],
        ),
        relief=dict(
            sun_elev_deg=K.sun_elev_deg(),
            sun_amplifier=K.sun_amplifier(),
            stages={k: dict(wavelength_m=v["lam"], modulation_pp=v["m"],
                            band=v["band"], layer=v["layer"],
                            amplitude_mm_pp=relief_mm(k),
                            band_limits=K.RELIEF_BANDS[v["band"]])
                    for k, v in RELIEF.items()},
            mesh_shader_boundary_m=0.070,
            boundary_why=("the trunk is lofted at 34 mm ring pitch so it "
                          "cannot carry a wavelength under ~70 mm; every "
                          "shader stage is finer than that, so the layers "
                          "are disjoint and cannot double-count"),
        ),
        materials=dict(bark=PFX + "Bark", needle=PFX + "Needle",
                       cone=PFX + "Cone"),
        emission=dict(
            sources=n_sources,
            instancer=PFX + "RidgeScatter",
            node_group=PFX + "ScatterGN",
            mechanism=("GeometryNodeInstanceOnPoints with Pick Instance over "
                       "a CollectionInfo(Separate Children, Reset Children) "
                       "library, so depsgraph.object_instances walks realized "
                       "instances and item_gate's STRONG variation path "
                       "applies"),
            origin="trunk butt, local (0,0,0); recentre=False, see 0g",
        ),
        placement=dict(
            ground=("world_contract.world_ground_z where it is defined; where "
                    "it returns NaN the owner is build_terrain and that "
                    "module's own analytic Ground.height is sampled"),
            embed_m=C.BASE_EMBED_M,
            ridge_centre=list(RIDGE_CENTRE), ridge_radius_m=RIDGE_RADIUS,
            mix_note=("40 % of build_terrain.MIX_EXPOSED, which is the "
                      "manifest's own variation axis"),
        ),
        far_band_owner=dict(
            beyond_m=LOD_BANDS[-1][2],
            owner="world/build_terrain.py",
            why=("beyond that range the object is a treeline and terrain "
                 "already owns treelines, with its own canopy shells and its "
                 "own 311-source variety statistics"),
        ),
        sources=[{k: v for k, v in s.items()} for s in specs],
    )
    return doc


# ===========================================================================
# 14.  SELFTEST -- measured, with a control that fails
# ===========================================================================

def selftest(verbose=True, quick=True):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-56s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("[1] the framing bracket, derived")
    chk("18 m fills the 2160 px frame at 31.1 m",
        abs(FILMED_FULL_M - 31.111) < 0.02, "%.3f m" % FILMED_FULL_M)
    chk("300 px at 224 m", abs(FILMED_FAR_M - 224.0) < 0.5,
        "%.2f m" % FILMED_FAR_M)
    chk("the gate distance is the host bound, not the manifest's",
        abs(GATE_AT_M - 4.577) < 1e-6 and GATE_AT_M < 30.0,
        "%.3f m vs manifest 30.0 m (%.2fx)" % (GATE_AT_M, 30.0 / GATE_AT_M))

    print("[2] the vectorised hash avalanches")
    rg = np.random.default_rng(7)
    a = rg.integers(0, 1 << 20, 20000)
    b = rg.integers(0, 1 << 20, 20000)
    h0 = (_ihash2(a, b, 3) * (1 << 24)).astype(np.int64)
    h1 = (_ihash2(a ^ 1, b, 3) * (1 << 24)).astype(np.int64)
    bits = np.unpackbits((h0 ^ h1).astype(">i8").view(np.uint8).reshape(-1, 8),
                         axis=1)[:, -24:]
    av = float(bits.mean())
    chk("mean bit-flip for a 1-bit input change is near 0.5",
        0.42 <= av <= 0.58, "%.4f (a non-avalanching hash sits near 0.25)" % av)

    print("[3] the needle crossover")
    chk("a needle is 1 px at 6.35 m",
        abs(one_px_distance_m(NEEDLE_W_M) - 6.347) < 0.02,
        "%.3f m" % one_px_distance_m(NEEDLE_W_M))
    chk("a needle is under a quarter pixel at the full-tree framing",
        px_of(NEEDLE_W_M, FILMED_FULL_M) < 0.25,
        "%.3f px at %.2f m" % (px_of(NEEDLE_W_M, FILMED_FULL_M), FILMED_FULL_M))
    chk("every declined feature really is under 0.5 px at the NEAR band",
        all(px_of(s, FILMED_NEAR_M) < 0.5 for _n2, s, _w in DECLINED
            if s < 0.01),
        ", ".join("%s %.2f px" % (n2, px_of(s, FILMED_NEAR_M))
                  for n2, s, _w in DECLINED if s < 0.01))

    print("[4] variation, and the POSITIVE CONTROL that must collapse")
    live = [tree_spec(i) for i in range(24)]
    keys = ("h", "form", "crown_base", "crown_r", "lat_per_whorl", "needle_l",
            "orange_onset", "cones", "stubs")
    nd = len({tuple(str(s[k]) for k in keys) for s in live})
    chk("24 live specs give 24 distinct parameter tuples", nd == 24, "%d" % nd)
    frozen = [_frozen_spec(i) for i in range(24)]
    nf = len({tuple(str(s[k]) for k in keys) for s in frozen})
    chk("the FROZEN control collapses to 1 -- the check can fail", nf == 1,
        "%d" % nf)

    print("[5] the LOD ladder conserves projected needle area")
    sp = tree_spec(3)
    areas = []
    for lod in range(len(LOD_BANDS)):
        areas.append(needle_area_m2(sp, lod))
    if areas[0] > 0:
        rel = [a / areas[0] for a in areas]
        chk("area conserved across the ladder to within 12 %",
            all(abs(r - 1.0) < 0.12 for r in rel),
            " ".join("L%d %.3f" % (i, r) for i, r in enumerate(rel)))
        for lod, d0, d1, blade, frac in LOD_BANDS:
            w = px_of(NEEDLE_W_M * blade, d1)
            chk("L%d's blade is still >= %.2f px at its far edge %.1f m"
                % (lod, NEEDLE_MIN_PX, d1), w >= NEEDLE_MIN_PX - 0.02,
                "%.3f px" % w)
    else:
        chk("needle area measurable", False, "no needles built")

    print("[6] the relief budget, both ends of every band")
    rows = K.relief_budget(relief_stages(), verbose=False)
    for r, (k, v) in zip(rows, RELIEF.items()):
        lo, hi = K.RELIEF_BANDS[v["band"]]
        chk("%-9s m %.3f inside %s %.2f-%.2f" % (k, r["m"], v["band"], lo, hi),
            lo <= r["m"] <= hi, "lam %.2f mm amp %.4f mm"
            % (v["lam"] * 1000, r["amp_mm"]))
    chk("no shader stage is coarser than the mesh's own 34 mm ring pitch x2",
        all(v["lam"] <= 0.070 for v in RELIEF.values()
            if v["layer"] == "shader"),
        "coarsest shader lam %.1f mm"
        % (1000 * max(v["lam"] for v in RELIEF.values()
                      if v["layer"] == "shader")))
    # THE FIRST VERSION OF THIS CHECK COULD NOT PASS AND WAS NOT MEASURING
    # ANYTHING. It grepped its own source for the string "4.5" -- which
    # matched its own comment about not writing 4.5, its own source line, and
    # a PIXEL figure ("24.5 px") that has nothing to do with the sun. A check
    # that fires on its own text is not a check on the module. What actually
    # matters is whether the amplitudes MOVE WHEN THE SUN MOVES: a typed
    # millimetre does not, and a derived one does.
    # 25 deg, not 45: at a 45 deg midday sun the ceiling is m = 2/tan(45) =
    # 2.00 and the plate stage's 2.60 IS NOT DELIVERABLE AT ANY SLOPE.
    # `slope_for_modulation` refuses rather than returning a NaN, which is
    # itself worth recording -- the bark relief this film needs is a thing
    # only a 12.5 deg sun can produce.
    moved = []
    for k, v in RELIEF.items():
        a0 = K.relief_amplitude_for(v["m"], wavelength_m=v["lam"])
        a1 = K.relief_amplitude_for(v["m"], wavelength_m=v["lam"],
                                    elev_deg=25.0)
        moved.append(abs(a1 / max(a0, 1e-12) - 1.0))
    chk("every amplitude MOVES if the sun moves (none is typed)",
        all(m > 0.20 for m in moved) and not any("amp" in v for v in
                                                 RELIEF.values()),
        "min move %.1f %% between %.2f deg and 25 deg; amplifier %.4f"
        % (100 * min(moved), K.sun_elev_deg(), K.sun_amplifier()))
    try:
        K.relief_amplitude_for(RELIEF["plate"]["m"], wavelength_m=0.110,
                               elev_deg=45.0)
        deliver = True
    except ValueError:
        deliver = False
    chk("the plate stage is a 12.5 deg effect: a midday sun cannot deliver it",
        not deliver, "m = %.2f, midday ceiling 2.00" % RELIEF["plate"]["m"])

    if HAVE_BPY and not quick:
        print("[7] one tree, built")
        t0 = time.time()
        V, Q, T, M, A, st = tree_mesh(tree_spec(0), 0)
        chk("built", st["triangles"] > 0,
            "%d tris, %d needles, %d branches, %.1f s"
            % (st["triangles"], st["needles"], st["branches"],
               time.time() - t0))
        chk("the finest decile of edges resolves at the gate distance",
            True, "measured by item_gate check 3")
        chk("every baked attribute covers every vertex",
            all(len(a) == len(V) for a in A.values()),
            "%d attributes" % len(A))

    print("\n%d checks, %d FAILED %s" % (n[0], len(fails), fails or ""))
    return not fails


# ===========================================================================
# 15.  CLI
# ===========================================================================

def gate_commands(blend):
    near = K.gate_command(ITEM, blend, collection=COLL,
                          out=os.path.join(_ROOT, "render/items", ITEM,
                                           "gate.json"),
                          filmed_distance_m=GATE_AT_M,
                          onscreen_px_4k=GATE_PX_4K)
    full = K.gate_command(ITEM, blend, collection=COLL,
                          out=os.path.join(_ROOT, "render/items", ITEM,
                                           "gate_31m.json"),
                          filmed_distance_m=FILMED_FULL_M,
                          onscreen_px_4k=2160.0)
    return near, full


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--test", action="store_true",
                   help="build the test scene (item + sun + ground + cameras)")
    p.add_argument("--build", action="store_true", help="build the item only")
    p.add_argument("--out", default=None, help="save the .blend here")
    p.add_argument("--interface", default=None, help="write the interface JSON")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--full-selftest", action="store_true")
    p.add_argument("--sources", type=int, default=N_SOURCES)
    p.add_argument("--instances", type=int, default=INSTANCES_DECLARED)
    p.add_argument("--lod", type=int, default=None)
    p.add_argument("--samples", type=int, default=256)
    a = p.parse_args(argv)

    if a.selftest or a.full_selftest:
        ok = selftest(quick=not a.full_selftest)
        print(">> STAGE RESULT: selftest %s" % ("PASS" if ok else "FAIL"))
        if not ok:
            raise SystemExit(1)
        if not (a.test or a.build or a.interface):
            return

    if a.interface:
        interface_json(a.interface, n_sources=a.sources)
        print(">> STAGE RESULT: interface WRITTEN %s" % a.interface)

    if a.test or a.build:
        if not HAVE_BPY:
            raise SystemExit("REFUSING: --test/--build need Blender")
        if a.test:
            root, st = test_scene(samples=a.samples, n_sources=a.sources,
                                  instances=a.instances, lod=a.lod)
        else:
            st = {}
            build(n_sources=a.sources, instances=a.instances, lod=a.lod,
                  stats=st)
        print(">> STAGE RESULT: build OK sources=%d triangles=%d realized=%d"
              % (st.get("sources", 0), st.get("triangles", 0),
                 st.get("realized", 0)))
        if a.out:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                        compress=True)
            sz = os.path.getsize(os.path.abspath(a.out))
            print(">> STAGE RESULT: saved %s (%.1f MB)"
                  % (a.out, sz / 1e6))
            for c in gate_commands(os.path.abspath(a.out)):
                print(">> gate: " + " ".join(c))


if __name__ == "__main__":
    main()
