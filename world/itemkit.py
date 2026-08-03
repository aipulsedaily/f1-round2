"""itemkit — the scaffold every per-item module was re-typing.

WHY
---
Wave 1 built 28 item modules totalling **102,554 lines**, and a mechanical AST
census of all 28 found **30,653 of them (29.9 %) in functions whose name recurs
in three or more modules**. Every agent re-derived the same conventions from the
same briefs and then re-typed the same scaffold: the sun rig, the macro camera,
the test scene, the collection plumbing, the node-graph DSL, the hash and noise
helpers, the interface JSON, the CLI. At ~372 agents for the remaining campaign
that is the single largest recoverable block of agent time left.

But saving typing is the *smaller* half. Six of these functions carry a fact that
one agent measured, wrote into its own copy, and could not transmit to the other
27. Those are the reason this file exists:

1. `hash01` — 15 modules define it, in at least **10 different implementations**.
   `pit_wall_unit`'s docstring records that the common idiom returns the low 30
   bits of an FNV hash, which does not avalanche: `hash01(seed,3)`,
   `hash01(seed,5)` and `hash01(seed,7)` all returned 0.33955 for the same unit
   — seven degrees of freedom collapsed to one, on a built blend. It added a
   murmur3 finaliser. **That fix was never propagated; the other 14 modules ship
   the bug.** The finaliser version is the one here, and `selftest()` measures
   the avalanche rather than asserting it.

2. `macro_rig` — 17 of 28 modules set `resolution_x = 1920` while
   `tools/item_gate.py` computes every pixel figure against `RES_X_4K = 3840`.
   That is R2-020: 11 of 28 wave-1 heroes were judged at twice their real
   resolution. Here the render resolution is not an argument an agent can get
   wrong; a non-gate resolution has to be asked for by name.

3. `contract_sun` — 2 of 28 test scenes built no sun at all, and the first
   adversarial peep pass was conducted entirely under sky-only light
   (WAVE1-PEEP-SYNTHESIS systemic 1). Worse, R2-021 records the same author
   writing a sun that pointed **upward** twice in one session. Here the emitted
   direction is measured and the function REFUSES if the sun does not light the
   ground.

4. `object_coords` — Law 6. `TexCoord -> Object`, never `Geometry -> Position`:
   at |P| ~ 1000 m a position-driven procedural loses precision and blotches.
   The census found zero violations across 28 modules, which is worth keeping;
   this file makes the wrong node unavailable rather than merely discouraged.

5. `purge` — `armco_post.contract_light`'s docstring explains, at length, why it
   is a copy of `armco_w_beam`'s: the beam's helper names its datablocks `AWB_`
   and the beam's `purge()` deletes everything starting `AWB_`, so calling one
   module's light helper and then another's builder **deletes the light and the
   render comes back black**. Every function here that creates a datablock takes
   the caller's prefix. A shared kit that ignored prefixes would reintroduce
   exactly that bug 372 times.

6. `brands` — the 31 invented brands exist once, in `build_dressing.BRANDS`.
   Wave 1 re-declared six different partial copies under six different names
   (`BRAND_BOOK` twice, with *different* 12-entry subsets; `BRANDS`; `BRAND`;
   `BRAND_NAMES`; `SPONSORS`), one of which pre-converted the colours to linear
   and one of which read the source file as text. Law 2 says reuse them; this
   reads the one book.

WHAT IS DELIBERATELY *NOT* HERE
-------------------------------
The item. `build()`, the geometry, the materials, the variation model — those
are the work, and they are different for a trash can and a guardrail. The census
found `build` in 28 of 28 modules and **no two implementations alike**, which is
correct. This file exists so that an agent's whole budget goes there.

Also not here: a chunking helper. The brief's Law 7 (chunk along s, 80-260 m)
is real, but the census looked for a shared implementation and found that `s0`/
`s1` name four unrelated quantities across eight modules. There is nothing to
factor yet, and inventing one would be a guess wearing a measurement's clothes.
`chunk_spans()` below is the one honest piece: the arithmetic, with the contract
number, and nothing about geometry.

USE
---
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import itemkit as K

    ITEM, COLL, PFX = "kerb_hero_t4", "W_Item_KerbHeroT4", "KHT_"
    ...
    root = K.coll(COLL)
    K.purge(PFX, COLL)                 # prefix-scoped; cannot touch another item
    K.contract_sun(PFX, coll=root)     # refuses to point at the sky
    K.macro_rig(PFX + "CAM_MACRO", loc, aim, lens, cams)   # 3840x2160, always

Read `world/items/REFERENCE.md` for one item worked end to end.

SELF-TEST
---------
    python3 world/itemkit.py --selftest          # the pure-python half
    blender -b --factory-startup -P world/itemkit.py -- --selftest   # all of it
"""

import json
import math
import os
import sys
import time

import numpy as np

try:
    import bpy
    HAVE_BPY = True
except ImportError:                                     # pure-python selftest
    bpy = None
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import world_contract as C                              # noqa: E402

# ---------------------------------------------------------------------------
# THE NUMBERS THE GATE SCORES AGAINST.
# These are not preferences. tools/item_gate.py:195 computes px_per_m from
# RES_X_4K = 3840 and stages its witness frame at that width; a deliverable at
# any other width is measured against a frame that was never rendered (R2-020).
# ---------------------------------------------------------------------------
RES_X_4K = 3840
RES_Y_4K = 2160
SENSOR_MM = 36.0

# ---------------------------------------------------------------------------
# WHAT A TEXTURE NODE ACTUALLY EMITS FOR A GIVEN `Scale`.
#
# `Scale` is NOT one over the feature size. Measured by rendering each node
# alone as an emission shader on a 1.000 m plane through an orthographic camera
# at 1024 px (1 px = 0.9766 mm) and taking the radially-averaged power spectrum:
#
#     Noise      emits 1.60x the wavelength implied by 1/Scale
#     Voronoi    emits 2.17x
#
# The measurement carries its own control: Blender's Wave has a closed form, and
# the probe returned 0.3136 and 0.3528 against 2*pi/20 = 0.31416 and a sine's
# sd = 0.35355 — so it measures the node rather than itself.
#
# WHY THIS MATTERS MORE THAN IT LOOKS. item_gate's decisive r1/r2 bands peak at
# 3 px and 6 px, which at 373.3 px/m is 8.04 and 16.07 mm. A module that asks for
# an 8.63 mm crumple by writing `scale = 1/0.00863` gets 13.8 mm and lands
# OUTSIDE the band that judges it. That is the "amplitude never reaches the
# image" failure which sank 21 of 28 wave-1 items, arriving through the front
# door as a units mistake.
#
# PROVENANCE — NO LONGER SINGLE-SOURCED. The original note here said these came
# from ONE agent's measurement and that an independent confirmation was still
# owed. That confirmation has now been done twice, by two agents, with two
# independent probes: `world/build_dressing.py`'s (8192 px row, zero-crossing
# count) and `work/wavefix/measure_emitted_wavelength.py` +
# `work/wavefix/measure2d.py` (8192 px row least-squares sinusoid fit, and a
# 2048x2048 radially-averaged 2-D power spectrum). Both probes carry a
# CALIBRATION CASE that shares no assumption with the thing measured — a
# closed-form sin(2*pi*x/lam) built out of Math nodes, recovered to 0.04 %.
#
#   Noise    peak 1.56-1.99, centroid 1.53-1.86, row fit 1.90-2.12
#   Voronoi  centroid 2.30-2.53, row fit 2.34-2.39   (peak DISQUALIFIED: it
#            drifts 5.1 -> 47.2 with Scale, so it is not measuring a factor)
#
# 1.60 and 2.17 sit inside that envelope and are LEFT ALONE. They are good to
# about +-20 %, which is the width at which three defensible estimators of "the
# feature size of a fractal" disagree with each other; the factor also moves
# with `detail` (measured: peak-mean 1.90 at detail 0, 1.80 at detail 8).
# A fractal has no single wavelength, and a fourth significant figure here would
# be a guess wearing a measurement's clothes. Every module's declared wavelength
# is written as `K.NOISE_WAVELENGTH_FACTOR / scale`, so refining these would
# move 28 modules' declared numbers for no gain in what they emit.
NOISE_WAVELENGTH_FACTOR = 1.60
VORONOI_WAVELENGTH_FACTOR = 2.17

# ---------------------------------------------------------------------------
# WAVE IS NOT AN ESTIMATE. IT IS A CLOSED FORM, AND THIS FILE HAD IT WRONG.
#
# R2-058. `_tex_wavelength_m()` returned `1.0 / Scale` for ShaderNodeTexWave,
# which is 3.183x too COARSE — and the correct value was already written in this
# same header, a few lines up: the NOISE/VORONOI paragraph uses Blender's Wave
# as its CONTROL precisely because it has a closed form, and quotes
# "2*pi/20 = 0.31416" while doing so. The constant was right in the comment and
# wrong in the code. Nothing caught it because the one selftest that exercised
# it round-tripped `1.0/230.0` against itself, and an algebraic identity cannot
# fail for any value of the constant, including a wrong one.
#
# Blender computes, for BANDS:   n = 20 * (P * Scale)[axis]
# and the SIN profile is 0.5 + 0.5*sin(n - pi/2), so the spatial period is
# 2*pi / (20 * Scale). MEASURED, not assumed — an orthographic 1-sample emission
# render of the node alone on a 2.000 m plane, denoiser off, Standard view
# transform, sub-bin least-squares sinusoid fit:
#
#     Scale        5      10      20      40      80     160     230
#     factor    0.31416 0.31416 0.31416 0.31416 0.31416 0.31416 0.31416
#
# — flat to six digits over a 46x sweep, against 2*pi/20 = 0.3141593. Confirmed
# again by a 2048x2048 radially-averaged 2-D spectrum (0.31422 +- 0.00015 over
# BANDS X, Y and Z) and by build_dressing's independent zero-crossing probe
# (0.3125/0.3150/0.3137/0.3143). See work/wavefix/emitted_wavelength{,_2d}.json.
#
# WHAT THIS COST. `bump_relief_report()` audits with `_tex_wavelength_m`, so
# every Wave-driven relief stage it has ever reported was audited at 3.183x the
# true wavelength — and since m goes as amplitude/wavelength, every one of those
# stages is really 3.183x the modulation the report printed. Relief law #86 and
# the 14-module rebuild #98 were judged on those numbers.
WAVE_WAVELENGTH_FACTOR = 2.0 * math.pi / 20.0            # 0.3141593

# DIAGONAL IS THE EXCEPTION, AND IT IS NOT 1/2 OR 2 OF THE OTHERS. Blender sums
# the components and multiplies by TEN, not twenty: n = 10 * (x+y+z) * Scale.
# The gradient is 10*Scale*(1,1,1), |grad| = 10*Scale*sqrt(3), so the period
# NORMAL TO THE BANDS is 2*pi/(10*sqrt(3)*Scale) = 0.36276/Scale — and along any
# single axis it is 2*pi/(10*Scale) = 0.62832/Scale. MEASURED both ways: the row
# fit reads 0.62832 (along x) and the 2-D radial peak reads 0.4424 (the
# band-normal on a z = 0 plane, where only x and y vary: 2*pi/(10*sqrt(2)) =
# 0.44429). The band-normal figure is the one reported, on the same principle as
# `_vector_gain`: THE FINEST DIRECTION IS THE ONE THAT SETS THE SLOPE.
# Seven built modules use one of these: DIAGONAL in driver_figure (4 nodes) and
# spectator_seated (1); RINGS/X in access_road_slab, forecourt_paving_bay (3),
# marshal_post_deck, pont_deck_slab and pont_girder.
WAVE_DIAGONAL_FACTOR = 2.0 * math.pi / (10.0 * math.sqrt(3.0))   # 0.3627599
# RINGS: n = 20 * |P*Scale| along the ring normal, so the RADIAL period is the
# same 2*pi/20. Measured 0.3127 / 0.3136 by 2-D peak, 0.3143 by row fit.


def noise_scale_for(wavelength_m):
    """`Scale` that makes ShaderNodeTexNoise emit features of `wavelength_m`.

    Use this instead of `1.0 / wavelength_m`, which is 1.6x wrong.
    """
    return NOISE_WAVELENGTH_FACTOR / float(wavelength_m)


def voronoi_scale_for(wavelength_m):
    """`Scale` that makes ShaderNodeTexVoronoi emit cells of `wavelength_m`."""
    return VORONOI_WAVELENGTH_FACTOR / float(wavelength_m)


def wave_scale_for(wavelength_m, direction="X"):
    """`Scale` that makes ShaderNodeTexWave emit bands of `wavelength_m`.

    `1.0 / wavelength_m` is 3.183x wrong and was the shape of R2-058. There is
    now ONE source for this number: `build_dressing`'s local
    `WAVE_WAVELENGTH_FACTOR` was a correct workaround for a broken itemkit and
    should be deleted in favour of this.
    """
    f = (WAVE_DIAGONAL_FACTOR if str(direction).upper() == "DIAGONAL"
         else WAVE_WAVELENGTH_FACTOR)
    return f / float(wavelength_m)

__all__ = [
    "RES_X_4K", "RES_Y_4K", "SENSOR_MM", "C",
    "px_per_m", "mm_per_px", "resolvable_mm", "chunk_spans",
    "hash01", "Rng", "clamp01", "smoothstep", "vnoise1", "vnoise2",
    "fbm1", "fbm2",
    "coll", "purge", "new_mesh", "shade_by_angle", "bake_attributes",
    "winding_audit", "orient_outward", "mesh_winding_report",
    "object_winding_report", "inside_out_fraction",
    "sun_elev_deg", "sun_amplifier", "slope_for_modulation",
    "modulation_for_slope", "relief_amplitude_for", "modulation_for_amplitude",
    "relief_budget", "RELIEF_BANDS", "bump_relief_report",
    "NOISE_WAVELENGTH_FACTOR", "VORONOI_WAVELENGTH_FACTOR",
    "WAVE_WAVELENGTH_FACTOR", "WAVE_DIAGONAL_FACTOR",
    "noise_scale_for", "voronoi_scale_for", "wave_scale_for",
    "geometry_relief_report", "emitted_wavelength_m",
    "NT", "object_coords", "srgb_linear",
    "contract_sun", "add_camera", "macro_rig", "ground_plane",
    "ground_z", "ground_owner", "seat_on_ground", "brands", "brand", "pick_brand",
    "interface_json", "assert_no_external_assets", "log", "cli", "selftest",
]

_T0 = time.time()


def log(msg, tag="itemkit"):
    sys.stdout.write("[%7.1fs] %s: %s\n" % (time.time() - _T0, tag, msg))
    sys.stdout.flush()


# ===========================================================================
# 1.  THE PIXEL BUDGET — the arithmetic the brief tells every agent to do
# ===========================================================================

def px_per_m(distance_m, lens_mm, res_x=RES_X_4K):
    """Screen resolution on a surface at `distance_m`, in pixels per metre.

    This is ITEM-CAMPAIGN-BRIEF sec 3's formula, with the gate's own numerator.
    Calling it instead of retyping it is the difference between a budget and a
    coincidence: the brief prints 3840 in the formula, the wave-1 harness asked
    the renderer for 1920, and nothing compared the two.
    """
    return (float(res_x) * float(lens_mm) / SENSOR_MM) / max(float(distance_m), 1e-6)


def mm_per_px(distance_m, lens_mm, res_x=RES_X_4K):
    return 1000.0 / px_per_m(distance_m, lens_mm, res_x)


def resolvable_mm(distance_m, lens_mm, px=1.0, res_x=RES_X_4K):
    """The smallest feature worth building, in mm. Below this it is a material."""
    return px * mm_per_px(distance_m, lens_mm, res_x)


def chunk_spans(s0, s1, target_m=170.0, min_m=80.0, max_m=260.0):
    """Split [s0, s1] along the circuit into spans inside Law 7's 80-260 m.

    Only the arithmetic: equal spans, count chosen so every span lands in the
    band, and it REFUSES rather than silently emitting a 30 m tail. What the
    caller does with the spans is the item's business.
    """
    total = float(s1) - float(s0)
    if total <= 0:
        raise ValueError("chunk_spans: s1 must exceed s0")
    if total <= max_m:
        return [(float(s0), float(s1))]
    n = max(1, int(round(total / float(target_m))))
    while n > 1 and total / n < min_m:
        n -= 1
    while total / n > max_m:
        n += 1
    span = total / n
    if not (min_m <= span <= max_m):
        raise ValueError(
            "chunk_spans: %.1f m cannot be split into spans inside "
            "[%.0f, %.0f] m; the range is shorter than the minimum chunk. "
            "Say what the item actually needs instead of forcing it."
            % (total, min_m, max_m))
    return [(float(s0) + i * span, float(s0) + (i + 1) * span) for i in range(n)]


# ===========================================================================
# 2.  DETERMINISTIC NOISE — one implementation, and it avalanches
# ===========================================================================

def hash01(*keys):
    """FNV-1a with a murmur3 finaliser. Returns [0,1).

    THE FINALISER IS THE WHOLE POINT, and it is here because one wave-1 agent
    found the bug on a built blend and the other fourteen never heard.

    Without it this returns the low 30 bits of an FNV-1a hash. FNV's multiply
    only propagates change UPWARD, so small keys differing in their low bits
    land in the same low-30-bit bucket: `hash01(seed,3)`, `hash01(seed,5)` and
    `hash01(seed,7)` all came back **0.33955** for the same unit. Seven
    per-object properties, one degree of freedom, and every object identical in
    exactly the way the user names as the project's headline failure.

    `selftest()` MEASURES the avalanche (mean output bit-flip probability for a
    one-bit input change) rather than asserting the code looks right.
    """
    h = 1469598103934665603
    for k in keys:
        h ^= int(k) & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    return float(h % (1 << 30)) / float(1 << 30)


class Rng(object):
    """Deterministic per-object stream. Same keys -> same object, always."""

    def __init__(self, *keys):
        s = 0
        for k in keys:
            s = (s * 1000003 + int(k)) & 0x7FFFFFFF
        self.seed = s
        self.r = np.random.default_rng(s)

    def u(self, a=0.0, b=1.0):
        return float(self.r.uniform(a, b))

    def n(self, mu=0.0, sd=1.0):
        return float(self.r.normal(mu, sd))

    def clipn(self, sd, clip):
        """A normal draw that cannot produce an impossible part."""
        return float(np.clip(self.r.normal(0.0, sd), -clip, clip))

    def i(self, a, b):
        return int(self.r.integers(a, b + 1))

    def pick(self, seq):
        return seq[int(self.r.integers(0, len(seq)))]

    def arr(self, n):
        return self.r.random(n)


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def _sstep(t):
    return t * t * (3.0 - 2.0 * t)


def smoothstep(e0, e1, x):
    return _sstep(clamp01((np.asarray(x, float) - e0) / max(e1 - e0, 1e-12)))


def _h2(ix, iy, seed):
    """Vectorised 2D integer hash -> [0,1]. numpy, so it runs on whole meshes."""
    with np.errstate(over="ignore"):
        h = (np.asarray(ix, np.uint32) * np.uint32(374761393)
             + np.asarray(iy, np.uint32) * np.uint32(668265263)
             + np.uint32(int(seed) & 0xFFFFFFFF) * np.uint32(2246822519))
        h = h ^ (h >> np.uint32(13))
        h = h * np.uint32(1274126177)
        h = h ^ (h >> np.uint32(16))
    return h.astype(np.float64) / 4294967295.0


def vnoise2(x, y, seed=0):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx = _sstep(x - ix)
    fy = _sstep(y - iy)
    a = _h2(ix, iy, seed)
    b = _h2(ix + 1, iy, seed)
    c = _h2(ix, iy + 1, seed)
    d = _h2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy)
            + c * (1 - fx) * fy + d * fx * fy)


def vnoise1(x, seed=0):
    x = np.asarray(x, float)
    ix = np.floor(x).astype(np.int64)
    fx = _sstep(x - ix)
    a = _h2(ix, np.zeros_like(ix), seed)
    b = _h2(ix + 1, np.zeros_like(ix), seed)
    return a * (1 - fx) + b * fx


def fbm2(x, y, seed=0, oct=4, lac=2.07, gain=0.5):
    s = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    a, f, norm = 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * vnoise2(np.asarray(x) * f, np.asarray(y) * f, seed + i * 71)
        norm += a
        a *= gain
        f *= lac
    return s / norm


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    s = np.zeros(np.asarray(x).shape)
    a, f, norm = 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * vnoise1(np.asarray(x) * f, seed + i * 37)
        norm += a
        a *= gain
        f *= lac
    return s / norm


def srgb_linear(hexcode):
    """'#12385e' -> linear RGB triple. The brand book stores sRGB hex."""
    h = hexcode.lstrip("#")
    out = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# ===========================================================================
# 3.  SCENE PLUMBING — every datablock carries the caller's prefix
# ===========================================================================

def _require_bpy(fn):
    if not HAVE_BPY:
        raise RuntimeError(
            "itemkit.%s needs Blender. Run under "
            "/opt/blender-5.2.0-linux-x64/blender -b ... -P <module>." % fn)


def coll(name, parent=None):
    """Get-or-make a collection, linked under `parent` (default: the scene)."""
    _require_bpy("coll")
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge(prefix, coll_name=None):
    """Remove THIS item's objects, meshes, materials, lights and collections.

    `prefix` is REQUIRED and there is no default.

    `armco_post.contract_light` carries a long docstring about why it is a
    verbatim copy of `armco_w_beam`'s: the beam's helper names its world
    `AWB_World` and its sun `AWB_Sun`, and the beam's `purge()` deletes every
    datablock starting `AWB_`. Call the beam's light and then the beam's builder
    and the light is gone; the acceptance render comes back BLACK. That is one
    module's prefix colliding with one other module's. A SHARED kit with a fixed
    prefix would make it 372 modules colliding with each other, so nothing here
    creates a datablock the caller has not named.
    """
    _require_bpy("purge")
    if not prefix or not isinstance(prefix, str):
        raise ValueError(
            "itemkit.purge(prefix): the prefix is mandatory. A purge with no "
            "prefix deletes another item's datablocks, and a deleted sun "
            "renders black rather than failing.")
    removed = {"objects": 0, "meshes": 0, "materials": 0, "lights": 0,
               "worlds": 0, "collections": 0}
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefix):
            bpy.data.objects.remove(ob, do_unlink=True)
            removed["objects"] += 1
    for coll_ in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                  bpy.data.worlds):
        key = {bpy.data.meshes: "meshes", bpy.data.materials: "materials",
               bpy.data.lights: "lights", bpy.data.worlds: "worlds"}[coll_]
        for d in list(coll_):
            if d.name.startswith(prefix) and d.users == 0:
                coll_.remove(d)
                removed[key] += 1
    if coll_name:
        root = bpy.data.collections.get(coll_name)
        if root:
            stack, seen = [root], []
            while stack:
                c = stack.pop()
                seen.append(c)
                stack.extend(list(c.children))
            for c in seen:
                for ob in list(c.objects):
                    bpy.data.objects.remove(ob, do_unlink=True)
                    removed["objects"] += 1
            for c in reversed(seen):
                bpy.data.collections.remove(c)
                removed["collections"] += 1
    return removed


# ===========================================================================
# 3b. WINDING — WHICH SIDE OF THE SURFACE THE RENDERER GETS
#
# THIS EXISTS BECAUSE 54 OF 318 PIECES OF THE HUMAN FIGURE FACED INWARD AND
# EVERY CHECK IN THE PROJECT PASSED. The head shell (normal.radial -0.966), both
# ears, the hair mass (-0.97), both shoe uppers (-0.717), both soles and all 22
# tread bars.
#
# BUT READ THIS BEFORE YOU BUDGET ANY TIME FOR IT. The mechanism that was
# ATTRIBUTED to it -- "Cycles flips a back-facing normal, so it rendered with
# every bump INVERTED, a brow ridge lit as a groove" -- IS NOT WHAT CYCLES DOES,
# and that was measured, on the 5090, with a control that proves the fault
# reached the renderer:
#
#   tools/winding_probe.py builds ONE sphere, in ONE place, under the contract
#   sun with a 12 mm ridge at m = 2.2, and renders it correct and reversed.
#
#     Geometry > Backfacing         correct BLACK, reversed WHITE everywhere
#                                   -- Cycles knows the surface is reversed
#     the lit render, Principled    mean |difference| 0.00011, rms 0.00039,
#     + Bump, 1600x900              HIGH-PASS CORRELATION +0.9997
#     the same with true            mean |difference| 0.0117, rms 0.0315,
#     DISPLACEMENT                  high-pass correlation +0.9553
#
#   Cycles flips the shading normal for a back-facing hit AND the bump
#   perturbation follows it consistently, so for an OPAQUE Principled surface
#   with a bump -- which is what every item module in this campaign is -- an
#   inside-out shell renders THE SAME PICTURE. Not black, and not inverted.
#
# SO WHAT IS THIS SECTION FOR. Winding still decides the picture wherever the
# renderer needs to know which side is IN rather than merely which side the ray
# came from:
#   * TRUE DISPLACEMENT -- measured above, and it moves geometry the wrong way;
#   * REFRACTION AND TRANSMISSION -- a reversed glass shell refracts as if the
#     camera were inside the glass. `showroom_facade_panel` and `mullion_intact`
#     are glass items;
#   * SUBSURFACE SCATTERING -- the scattering side is the inside;
#   * any shader reading `Geometry > Backfacing`;
#   * every consumer that is not Cycles -- the viewport, exporters, and any
#     future engine.
# It is also free: `new_mesh` orients on emit, and the cost is one bincount.
#
# WHAT IT IS NOT FOR is a campaign of repairs and re-gates on 28 built modules.
# The measurement above says that would move ~0.01 % of the pixels. THE
# INSTRUCTION THAT CAME WITH THIS WORK SAID IT IN ADVANCE -- "a similar repair
# was predicted to move every built vertex and on measurement moved almost
# nothing" -- and this is the same shape. Measure before you claim.
#
# WHY IT IS STILL NOT A HUMANKIT PROBLEM. The idioms that produce it -- lofting
# rings, sweeping a profile, capping a boundary loop, and above all MIRRORING
# ACROSS AN AXIS, which reverses winding BY CONSTRUCTION -- are the idioms every
# item module is built from, and the sweep found inward pieces in 20 of 30 built
# item blends. Nothing measured it, because every check measured the MODEL and
# none measured the SIDE.
#
# THE METHOD IS humankit.Mesh.orient_outward's, PORTED, NOT REINVENTED: every
# piece decided by EXACT SIGNED VOLUME, with open pieces closed first by capping
# their boundary loops. No heuristic and no deadband. Two differences, both
# forced by the setting:
#
#   * humankit knows its pieces because it built them (`Mesh.BLK`, one entry per
#     `add()`). An item module hands over a finished vertex/face array and there
#     is no such record, so a piece here is a CONNECTED COMPONENT of the polygon
#     graph -- which is what "a piece" means to the renderer anyway.
#   * it is vectorised. humankit's version is a Python loop over ~300 pieces;
#     this has to run over a 20 M-triangle test scene, so components, boundary
#     loops, capping and volume are all bincount/reduceat.
#
# THREE STATISTICS, INDEPENDENTLY WRITTEN, AND THEY MUST AGREE:
#   1. exact signed volume of the closed (capped) piece      -- decides
#   2. area-weighted mean(unit normal . unit radial)         -- confirms
#   3. `inside_out_fraction` -- cast rays, take the first hit, count back-faces
#      -- the only one that measures what a VIEWER gets, and the only one that
#      can be wrong about the model and right about the picture.
# A fourth, `inconsistent_edge_pairs`, catches the other winding defect that
# signed volume cannot see: a piece wound INCONSISTENTLY WITHIN ITSELF, whose
# volume can come out near zero or plain wrong. Both sides of the fault are
# bounded, because both sides are wrong.
#
# THE TWO PRIMARY STATISTICS HAVE OPPOSITE BLIND SPOTS, AND THAT IS MEASURED,
# not reasoned. `tools/winding_audit.py --plant-fault` reverses the largest
# piece of a real module in place and re-audits:
#
#   armco_w_beam   956 of 2,868 faces reversed -> signed volume still says
#                  0 inward, the RAY says 0.000 -> 0.378. The w-beam is an open
#                  pressed rail: it encloses too little to have an inside, so it
#                  is `undecidable` by design and volume cannot see it.
#   crew_figure    3,816 of 26,991 reversed -> volume says 1 inward -> 2, the
#                  RAY does not move at all. The reversed piece is a body part
#                  UNDER a garment: no first hit ever reaches it.
#
# So: volume is blind to reversed SHEETS, the ray is blind to BURIED pieces.
# Run both, and never quote one alone.
# ===========================================================================

def _components(nv, ea, eb):
    """Connected-component label per vertex. Vectorised pointer jumping.

    scipy is not available in this Blender, and a Python union-find over the
    60 M edges of a wave-1 test scene is not a real option, so this is
    label-propagation by `reduceat` plus pointer-doubling: O(log n) rounds, each
    one a sort-free scatter-min over the (already sorted) adjacency.
    """
    lab = np.arange(nv, dtype=np.int64)
    if nv == 0 or len(ea) == 0:
        return lab
    a = np.concatenate([np.asarray(ea, np.int64), np.asarray(eb, np.int64)])
    b = np.concatenate([np.asarray(eb, np.int64), np.asarray(ea, np.int64)])
    order = np.argsort(a, kind="stable")
    a = a[order]
    b = b[order]
    cnt = np.bincount(a, minlength=nv)
    starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    ne = np.flatnonzero(cnt > 0)
    idx = starts[ne]
    for _ in range(256):
        m = np.minimum.reduceat(lab[b], idx)
        new = lab.copy()
        new[ne] = np.minimum(lab[ne], m)
        while True:
            nn = new[new]
            if np.array_equal(nn, new):
                break
            new = nn
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def _csr_from_faces(quads=None, tris=None):
    """(starts, counts, corners) for a quad array and/or a tri array."""
    starts, counts, corners = [], [], []
    n = 0
    if quads is not None and len(quads):
        q = np.asarray(quads, np.int64).reshape(-1, 4)
        counts.append(np.full(len(q), 4, np.int64))
        starts.append(np.arange(len(q), dtype=np.int64) * 4)
        corners.append(q.ravel())
        n = 4 * len(q)
    if tris is not None and len(tris):
        t = np.asarray(tris, np.int64).reshape(-1, 3)
        counts.append(np.full(len(t), 3, np.int64))
        starts.append(np.arange(len(t), dtype=np.int64) * 3 + n)
        corners.append(t.ravel())
    if not counts:
        z = np.zeros(0, np.int64)
        return z, z, z
    return (np.concatenate(starts), np.concatenate(counts),
            np.concatenate(corners))


def _within_face_index(counts):
    """0,1,2,...  restarting at every face. Vectorised `repeat`+`arange`."""
    tot = int(counts.sum())
    if tot == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    fid = np.repeat(np.arange(len(counts), dtype=np.int64), counts)
    off = np.arange(tot, dtype=np.int64) - np.repeat(
        np.cumsum(counts) - counts, counts)
    return fid, off


def winding_audit(verts, quads=None, tris=None, starts=None, counts=None,
                  corners=None, apply=False, eps_rel=1e-9, with_tri_piece=False,
                  q_min=0.005):
    """Per-piece winding, by exact signed volume. Pure numpy; no bpy.

    Give it `quads`/`tris`, or a polygon CSR (`starts`, `counts`, `corners`) for
    a mesh with n-gons. With `apply=True` the inward pieces are REVERSED IN
    PLACE in the arrays you passed, and the report says how many.

    Returns a dict. The fields that matter:

        pieces                    connected components of the polygon graph
        inward                    how many of them face the wrong way
        inward_faces              how many POLYGONS that is (the number that
                                  says whether it matters)
        vol / nrad                the two statistics, per piece
        statistics_agree          they must; if they do not, say so loudly
        flat                      pieces enclosing no volume (a plate, a decal,
                                  a fingernail) -- decided by the weaker rule of
                                  which way they face, and RECORDED as such
                                  rather than passed over in silence
        inconsistent_edge_pairs   interior edges traversed the SAME way by both
                                  their faces: a piece wound inconsistently
                                  within itself, which no volume can fix
    """
    V = np.ascontiguousarray(verts, float).reshape(-1, 3)
    nv = len(V)
    given_csr = corners is not None
    if not given_csr:
        starts, counts, corners = _csr_from_faces(quads, tris)
    starts = np.asarray(starts, np.int64)
    counts = np.asarray(counts, np.int64)
    corners = np.asarray(corners, np.int64)
    nf = len(counts)
    if nf == 0 or nv == 0:
        return {"pieces": 0, "faces": 0, "inward": 0, "inward_faces": 0,
                "flipped": 0, "flat": 0, "statistics_agree": True,
                "inconsistent_edge_pairs": 0, "boundary_edges": 0,
                "vol": np.zeros(0), "nrad": np.zeros(0),
                "inward_mask": np.zeros(0, bool), "piece_of_face":
                np.zeros(0, np.int64), "inward_area_frac": 0.0}

    # ---- directed polygon edges ----------------------------------------
    fid, off = _within_face_index(counts)
    nxt = np.arange(len(corners), dtype=np.int64) + 1
    nxt[starts + counts - 1] = starts
    ea = corners
    eb = corners[nxt]

    # ---- pieces ---------------------------------------------------------
    vlab = _components(nv, ea, eb)
    froot = vlab[corners[starts]]
    uroot, piece = np.unique(froot, return_inverse=True)
    npc = int(len(uroot))

    # ---- fan triangulation ----------------------------------------------
    ntp = counts - 2
    tfid, toff = _within_face_index(ntp)
    ts = starts[tfid]
    TR = np.stack([corners[ts], corners[ts + toff + 1],
                   corners[ts + toff + 2]], axis=1)
    TP = piece[tfid]

    # ---- boundary edges (used once) and winding consistency -------------
    lo = np.minimum(ea, eb)
    hi = np.maximum(ea, eb)
    key = lo.astype(np.int64) * np.int64(nv) + hi
    order = np.argsort(key, kind="stable")
    ks = key[order]
    firstk = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(firstk) - 1
    use = np.bincount(grp)
    per_edge_use = use[grp]                       # in SORTED order
    bsel = order[per_edge_use == 1]
    ba, bb = ea[bsel], eb[bsel]
    manifold = order[per_edge_use == 2]
    incons = 0
    if len(manifold):
        dk = np.sort(ea[manifold].astype(np.int64) * np.int64(nv) + eb[manifold])
        incons = int(np.count_nonzero(dk[1:] == dk[:-1]))

    # ---- cap every boundary loop to its own centroid --------------------
    VV = V
    cap_tris = np.zeros((0, 3), np.int64)
    cap_piece = np.zeros(0, np.int64)
    if len(ba):
        llab = _components(nv, ba, bb)
        bverts = np.unique(np.concatenate([ba, bb]))
        _, lidx = np.unique(llab[bverts], return_inverse=True)
        nl = int(lidx.max()) + 1
        cw = np.bincount(lidx, minlength=nl).astype(float)
        ctr = np.stack([np.bincount(lidx, weights=V[bverts, k], minlength=nl) / cw
                        for k in range(3)], axis=1)
        VV = np.concatenate([V, ctr])
        lof = lidx[np.searchsorted(bverts, ba)]
        # wound to OPPOSE the boundary edge's direction in the face that owns it
        cap_tris = np.stack([bb, ba, len(V) + lof], axis=1)
        cap_piece = np.searchsorted(uroot, vlab[ba])

    # ---- statistic 1: exact signed volume, per piece ---------------------
    allt = np.concatenate([TR, cap_tris])
    allp = np.concatenate([TP, cap_piece])
    det = np.einsum("ij,ij->i", VV[allt[:, 0]],
                    np.cross(VV[allt[:, 1]], VV[allt[:, 2]]))
    vol = np.bincount(allp, weights=det, minlength=npc) / 6.0

    # ---- statistic 2: area-weighted mean(unit normal . unit radial) ------
    fn = np.cross(V[TR[:, 1]] - V[TR[:, 0]], V[TR[:, 2]] - V[TR[:, 0]])
    nn = np.linalg.norm(fn, axis=1)
    area = 0.5 * nn
    cen = (V[TR[:, 0]] + V[TR[:, 1]] + V[TR[:, 2]]) / 3.0
    pn = np.bincount(TP, minlength=npc).astype(float)
    pcen = np.stack([np.bincount(TP, weights=cen[:, k], minlength=npc)
                     / np.maximum(pn, 1.0) for k in range(3)], axis=1)
    rad = cen - pcen[TP]
    rn = np.linalg.norm(rad, axis=1)
    ok = (rn > 1e-12) & (nn > 1e-12)
    dot = np.zeros(len(TR))
    dot[ok] = np.einsum("ij,ij->i", fn[ok], rad[ok]) / (nn[ok] * rn[ok])
    parea = np.bincount(TP, weights=area, minlength=npc)
    nrad = (np.bincount(TP, weights=dot * area, minlength=npc)
            / np.maximum(parea, 1e-30))

    # ---- the decision ----------------------------------------------------
    # A FLAT PLATE HAS NO INSIDE. Neither has a road slab, a paving bay or an
    # asphalt course, and THAT IS NOT A CORNER CASE HERE -- it is a third of the
    # campaign. Volume cannot decide them and no amount of arithmetic will make
    # it: the first version of this decided `asphalt_wearing_course` "100 %
    # inward" off a capped volume of essentially nothing, which is a coin toss
    # wearing an exact method's clothes.
    #
    # So the decision is scoped by HOW ENCLOSING THE PIECE ACTUALLY IS. Q =
    # |vol| / area^1.5 is 0.094 for a sphere, 0.071 for a capped tube and ~0 for
    # a sheet; above `q_min` the sign of the volume means something and decides,
    # below it the piece is recorded as UNDECIDABLE and LEFT ALONE.
    #
    # Leaving it alone is the deliberate half. "A fallback that decides nothing
    # is R2-019's defect in a new hat" -- but a fallback that decides WRONGLY
    # reverses a correct road surface across the whole film, and this repair
    # changes the rendered result. Undecidable pieces are counted, named, and
    # handed to `inside_out_fraction`, which measures the only thing that can
    # settle them: which side a viewer gets.
    tol = eps_rel * np.maximum(parea, 1e-30) ** 1.5
    qual = np.abs(vol) / np.maximum(parea, 1e-30) ** 1.5
    flat = np.abs(vol) <= tol
    sheet = qual < float(q_min)
    inward = (vol < -tol) & ~sheet
    # A piece that encloses too little to speak for itself, but sits OFF the
    # body's centre and belongs to a multi-piece mesh, still has one usable
    # fact: which way it faces relative to the body. That is humankit's rule for
    # a fingernail or a belt buckle, and it is applied only where it is
    # meaningful -- never to a lone sheet, which has nothing to be off-centre
    # from.
    undecidable = sheet.copy()
    if sheet.any() and npc > 1:
        gc = V.mean(axis=0)
        nsum = np.stack([np.bincount(TP, weights=fn[:, k], minlength=npc)
                         for k in range(3)], axis=1)
        aw = pcen - gc
        prad = np.sqrt(np.maximum(parea, 1e-30) / math.pi)
        usable = sheet & (np.linalg.norm(aw, axis=1) > 0.25 * prad)
        d_away = np.einsum("ij,ij->i", nsum, aw)
        inward = np.where(usable, d_away < 0.0, inward)
        undecidable = sheet & ~usable

    # the two statistics must agree wherever volume is decisive
    dec = ~sheet
    agree = bool(np.all(np.sign(vol[dec]) == np.sign(nrad[dec]))
                 if dec.any() else True)
    fpp = np.bincount(piece, minlength=npc)
    rep = {
        "pieces": npc,
        "faces": int(nf),
        "triangles": int(len(TR)),
        "inward": int(inward.sum()),
        "inward_faces": int(fpp[inward].sum()),
        "inward_area_frac": float(parea[inward].sum()
                                  / max(float(parea.sum()), 1e-30)),
        "closed_pieces": int(dec.sum()),
        "sheet_pieces": int(sheet.sum()),
        "undecidable": int(undecidable.sum()),
        "undecidable_area_frac": float(parea[undecidable].sum()
                                       / max(float(parea.sum()), 1e-30)),
        "enclosure_q": qual,
        "flat": int(flat.sum()),
        "boundary_edges": int(len(ba)),
        "inconsistent_edge_pairs": incons,
        "statistics_agree": agree,
        "vol": vol,
        "nrad": nrad,
        "area": parea,
        "inward_mask": inward,
        "piece_of_face": piece,
        "flipped": 0,
    }
    if with_tri_piece:
        # WHICH PIECES A VIEWER ACTUALLY GETS. An inward piece BURIED inside
        # solid geometry costs nothing and must not be counted as a defect
        # alongside a reversed head shell -- and worse, a cavity liner emitted
        # as its own closed shell is LEGITIMATELY inward-facing and flipping it
        # would be the defect. `tri_piece` lets a ray cast attribute every
        # back-facing first hit to the piece it came from, which is the only way
        # to tell those three cases apart.
        rep["tri_piece"] = TP.astype(np.int32)
        rep["tri_index"] = TR.astype(np.int32)
    if apply and inward.any():
        fl = inward[piece]
        sel = np.flatnonzero(fl)
        cc = counts[sel]
        ss = starts[sel]
        sf, k = _within_face_index(cc)
        src = ss[sf] + (cc[sf] - 1 - k)
        dst = ss[sf] + k
        newc = corners.copy()
        newc[dst] = corners[src]
        if given_csr:
            corners[:] = newc
        else:
            nq = 0
            if quads is not None and len(quads):
                nq = len(quads)
                np.asarray(quads).reshape(-1, 4)[:] = newc[:4 * nq].reshape(-1, 4)
            if tris is not None and len(tris):
                np.asarray(tris).reshape(-1, 3)[:] = newc[4 * nq:].reshape(-1, 3)
        rep["flipped"] = int(inward.sum())
    return rep


def orient_outward(verts, quads=None, tris=None, report=False):
    """Reverse the winding of every piece that faces INWARD. In place.

    The one-line form of `winding_audit(..., apply=True)`; this is the call an
    item module makes just before `new_mesh`, and it is what `new_mesh` does for
    you unless you say `orient=False`.
    """
    rep = winding_audit(verts, quads=quads, tris=tris, apply=True)
    return rep if report else (quads, tris)


def mesh_winding_report(me, apply=False, with_tri_piece=False):
    """`winding_audit` on a live Blender mesh datablock (n-gons included).

    With `apply=True` the mesh's own loops are rewritten, so this repairs a mesh
    that is already built -- which is how the 28 wave-1 modules get audited
    without re-running 28 builders.
    """
    _require_bpy("mesh_winding_report")
    nv, nl, nf = len(me.vertices), len(me.loops), len(me.polygons)
    if not nf or not nv:
        return {"pieces": 0, "inward": 0, "inward_faces": 0, "faces": 0,
                "flipped": 0, "flat": 0, "statistics_agree": True,
                "inconsistent_edge_pairs": 0, "inward_area_frac": 0.0,
                "boundary_edges": 0, "triangles": 0}
    co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    corners = lv.astype(np.int64)
    rep = winding_audit(co.reshape(-1, 3).astype(np.float64),
                        starts=ls.astype(np.int64), counts=lt.astype(np.int64),
                        corners=corners, apply=apply,
                        with_tri_piece=with_tri_piece)
    if with_tri_piece:
        rep["verts"] = co.reshape(-1, 3).astype(np.float64)
    if apply and rep.get("flipped"):
        me.loops.foreach_set("vertex_index", corners.astype(np.int32))
        me.update()
        # AND TELL THE DEPSGRAPH. Without `update_tag` the evaluated copy keeps
        # the old winding, so a ray-cast taken after the repair reports the
        # geometry as it was -- which is how this instrument nearly reported a
        # repaired control as still 5 % inside-out and was very nearly believed.
        me.update_tag()
    return rep


def object_winding_report(ob, apply=False):
    """`mesh_winding_report` plus the OBJECT-level way to get this wrong.

    A negative-determinant object matrix -- any odd number of mirrored axes --
    reverses the effective winding of a mesh that is perfectly wound in its own
    space. Cycles compensates for it, but Blender's viewport and several
    exporters do not, and a module that mirrors by scaling -1 and ALSO mirrors
    its vertex array has done it twice. Reported, never silently "fixed".
    """
    _require_bpy("object_winding_report")
    rep = (mesh_winding_report(ob.data, apply=apply)
           if getattr(ob, "type", None) == "MESH" and ob.data else
           {"pieces": 0, "inward": 0, "inward_faces": 0, "faces": 0,
            "flipped": 0, "flat": 0, "statistics_agree": True,
            "inconsistent_edge_pairs": 0, "inward_area_frac": 0.0,
            "boundary_edges": 0, "triangles": 0})
    rep["name"] = ob.name
    rep["matrix_det"] = float(np.linalg.det(
        np.array(ob.matrix_world.to_3x3())))
    rep["mirrored_by_matrix"] = rep["matrix_det"] < 0.0
    return rep


def _world_triangles(objects, max_tris=6000000):
    """World-space triangles of `objects`, read from the DATABLOCKS."""
    _require_bpy("_world_triangles")
    VS, FS, n = [], [], 0
    for ob in objects:
        me = getattr(ob, "data", None)
        if getattr(ob, "type", None) != "MESH" or me is None or not len(me.polygons):
            continue
        nv, nl, nf = len(me.vertices), len(me.loops), len(me.polygons)
        co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co)
        lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
        ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
        lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
        P = co.reshape(-1, 3).astype(np.float64)
        M = np.array(ob.matrix_world)
        P = P @ M[:3, :3].T + M[:3, 3]
        starts = ls.astype(np.int64); counts = lt.astype(np.int64)
        corners = lv.astype(np.int64)
        fid, off = _within_face_index(counts - 2)
        s = starts[fid]
        T = np.stack([corners[s], corners[s + off + 1],
                      corners[s + off + 2]], axis=1)
        # A NEGATIVE-DETERMINANT MATRIX REVERSES WINDING, AND CYCLES ALREADY
        # KNOWS. An odd number of mirrored axes turns every face inside out in
        # world space -- but Cycles carries a negative-scale flag and flips the
        # normal back, so the RENDER is correct and only a naive transform sees
        # a defect. Not compensating here read `grandstand_riser_unit` as 96.3 %
        # back-facing on geometry that renders perfectly. This statistic exists
        # to measure what the renderer gets, so it has to model the renderer.
        if float(np.linalg.det(M[:3, :3])) < 0.0:
            T = T[:, ::-1].copy()
        VS.append(P)
        FS.append(T + n)
        n += len(P)
        if sum(len(f) for f in FS) > max_tris:
            raise MemoryError(
                "inside_out_fraction over %d triangles. Audit per object, or "
                "raise max_tris deliberately -- a silent subsample would make "
                "'first hit' mean nothing." % sum(len(f) for f in FS))
    if not VS:
        return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
    return np.concatenate(VS), np.concatenate(FS)


def inside_out_fraction(objects=None, n_rays=1500, seed=7, verts=None,
                        tris=None, return_hits=False):
    """THE ONE THAT MEASURES THE PICTURE: cast rays, take the FIRST hit, count
    the ones that land on a back face.

    Signed volume measures the model. This measures what a viewer standing
    outside gets, which is the thing that was actually wrong. humankit's version
    is the reason "open boundary loop area" and "height above the acromion" were
    both abandoned as instruments -- they were the wrong layer, and this is not.

    IT CASTS AGAINST GEOMETRY IT READ ITSELF, and that is not fastidiousness.
    The first version used `scene.ray_cast` and reported a control that the
    datablock proved was 6144/6144 outward as 5.2 % back-facing, because the
    DEPSGRAPH'S EVALUATED COPY had not caught up with the repair. Two sources of
    geometry, one answer each. This one builds a BVH from the same arrays every
    other statistic in this section uses, so "which copy did I measure" is not a
    question that can be asked.
    """
    _require_bpy("inside_out_fraction")
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    if verts is None:
        obs = [o for o in (objects if objects is not None
                           else bpy.context.scene.objects)
               if getattr(o, "type", None) == "MESH"]
        verts, tris = _world_triangles(obs)
    verts = np.asarray(verts, float).reshape(-1, 3)
    tris = np.asarray(tris, np.int64).reshape(-1, 3)
    if not len(tris):
        return {"rays": 0, "hits": 0, "back": 0, "fraction": 0.0,
                "triangles": 0}
    lo, hi = verts.min(axis=0), verts.max(axis=0)
    ctr = 0.5 * (lo + hi)
    rad = float(np.linalg.norm(hi - lo)) * 0.5 + 1e-6
    # AIM AT THE SURFACE, NOT AT THE MIDDLE OF THE BOX. Aiming at points near
    # the bbox centre sends rays down the hub of a tyre and into the cavity of
    # every hollow thing, where the inner wall IS a back face and is supposed to
    # be: `tyre_wall_tyre` read 77 % back-facing with 0.27 % of its area inward.
    # Sampling target points on the surface, weighted by area, asks the question
    # that matters -- CAN A CAMERA SEE A BACK FACE -- and weights it the way the
    # eye does, by how much of the visible surface it is.
    A = verts[tris[:, 0]]
    ab = verts[tris[:, 1]] - A
    ac = verts[tris[:, 2]] - A
    area = 0.5 * np.linalg.norm(np.cross(ab, ac), axis=1)
    tot = float(area.sum())
    if tot <= 0.0:
        return {"rays": 0, "hits": 0, "back": 0, "fraction": 0.0,
                "triangles": int(len(tris))}
    cdf = np.cumsum(area) / tot
    # `.tolist()` is a C conversion; the list comprehension it replaces spent
    # minutes on a 2 M-triangle deck slab and was the reason a witness audit
    # looked hung.
    bvh = BVHTree.FromPolygons(verts.tolist(), tris.tolist(),
                               all_triangles=True, epsilon=0.0)
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(n_rays, 3))
    d /= np.linalg.norm(d, axis=1)[:, None]
    # NOT A FULL SPHERE OF ORIGINS. Half of a full sphere is UNDERGROUND, and
    # for a road slab or a paving bay -- a third of this campaign -- that reads
    # 50 % back-facing on geometry that is perfectly correct, because the
    # underside of a one-sided sheet is supposed to be a back face. No camera in
    # this film is below the tarmac. This keeps the ray origins in the
    # hemisphere a camera can occupy, which is what "which side does the
    # renderer get" means.
    d[:, 2] = np.abs(d[:, 2]) * 0.9 + 0.05
    d /= np.linalg.norm(d, axis=1)[:, None]
    pick = np.searchsorted(cdf, rng.random(n_rays))
    u = rng.random(n_rays)
    v = rng.random(n_rays)
    flip = u + v > 1.0
    u = np.where(flip, 1.0 - u, u)
    v = np.where(flip, 1.0 - v, v)
    tgt = A[pick] + ab[pick] * u[:, None] + ac[pick] * v[:, None]
    hits = back = 0
    hit_tri, hit_back = [], []
    for i in range(n_rays):
        org = Vector(tgt[i] + d[i] * rad * 3.0)
        dirv = Vector(tgt[i]) - org
        if dirv.length < 1e-9:
            continue
        dirv.normalize()
        loc, nrm, idx, dist = bvh.ray_cast(org, dirv, rad * 9.0)
        if loc is None:
            continue
        hits += 1
        b = nrm.dot(dirv) > 0.0
        back += 1 if b else 0
        if return_hits:
            hit_tri.append(int(idx))
            hit_back.append(bool(b))
    out = {"rays": int(n_rays), "hits": int(hits), "back": int(back),
           "fraction": (back / hits) if hits else 0.0,
           "triangles": int(len(tris))}
    if return_hits:
        out["hit_tri"] = hit_tri
        out["hit_back"] = hit_back
    return out


# --- CONTROL GEOMETRY, built here so the checks own their own faults --------
# A negative control that depends on ANOTHER MODULE STAYING BROKEN is not a
# control: humankit's `every_bump_drives_height_not_filter_width` went green
# this week because the bug it needed was fixed upstream. These build the
# inside-out surface themselves, from scratch, so they fail on their own terms
# forever.

def _ctl_sphere(nu=24, nv=16, r=1.0, centre=(0.0, 0.0, 0.0), reverse=False):
    """A closed lat/long sphere, wound OUTWARD unless `reverse`."""
    th = np.linspace(0.0, np.pi, nv + 1)
    ph = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    P, T = np.meshgrid(ph, th)
    V = np.stack([r * np.sin(T) * np.cos(P), r * np.sin(T) * np.sin(P),
                  r * np.cos(T)], axis=-1).reshape(-1, 3)
    V = V + np.asarray(centre, float)
    idx = np.arange((nv + 1) * nu).reshape(nv + 1, nu)
    i2 = np.roll(idx, -1, axis=1)
    Q = np.stack([idx[1:], i2[1:], i2[:-1], idx[:-1]], axis=-1).reshape(-1, 4)
    return V, (Q[:, ::-1].copy() if reverse else Q.astype(np.int64))


def _ctl_tube(nu=20, nz=6, r=0.5, h=2.0, centre=(0.0, 0.0, 0.0), reverse=False):
    """An OPEN tube -- the case a closed-volume method cannot decide unless it
    caps the boundary loops first, which is why humankit's first version
    abstained on every trouser head."""
    ph = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    z = np.linspace(0.0, h, nz + 1)
    P, Z = np.meshgrid(ph, z)
    V = np.stack([r * np.cos(P), r * np.sin(P), Z], axis=-1).reshape(-1, 3)
    V = V + np.asarray(centre, float)
    idx = np.arange((nz + 1) * nu).reshape(nz + 1, nu)
    i2 = np.roll(idx, -1, axis=1)
    Q = np.stack([idx[:-1], i2[:-1], i2[1:], idx[1:]], axis=-1).reshape(-1, 4)
    return V, (Q[:, ::-1].copy() if reverse else Q.astype(np.int64))


def _ctl_sin_grid(n=64, span=1.0, lam=0.125, amp_mm=2.0, z=0.0):
    """A flat grid displaced by a sinusoid of known wavelength and amplitude --
    the physical ladder `geometry_relief_report` is calibrated against."""
    x = np.linspace(-0.5 * span, 0.5 * span, n)
    X, Y = np.meshgrid(x, x)
    Z = 0.5 * (amp_mm * 1e-3) * np.sin(2.0 * np.pi * X / lam) + z
    V = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    idx = np.arange(n * n).reshape(n, n)
    Q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                 axis=-1).reshape(-1, 4).astype(np.int64)
    return V, Q


def new_mesh(name, verts, quads=None, tris=None, smooth_deg=33.0,
             recentre=True, orient=True):
    """Mesh from numpy arrays, RECENTRED ON EMIT (Law 6), shaded by angle.

    `orient=True` (the default) runs `orient_outward` first, so a piece that was
    lofted the wrong way round or mirrored across an axis cannot reach the
    renderer inside-out. See section 3b: 54 of 318 pieces of the human figure
    did, every check passed, and it rendered with every bump inverted. Pass
    `orient=False` only for a surface that is DELIBERATELY one-sided and knows
    which side it wants -- and say why in a comment.

    `recentre` returns the offset that was subtracted so the caller can set
    `ob.location` to it. It defaults ON because that is the law, and because
    "recentre on emit" was one of the two conventions every wave-1 agent
    re-derived by hand: the census found 28 independent inline `V - centre`
    implementations and exactly one named helper.

    Recentring is not tidiness. `TexCoord -> Object` addresses the material in
    the object's own local frame, so an object whose vertices sit at |P| ~ 1000 m
    feeds its procedural coordinates that lose float precision — which is the
    measured cause of the first pass's blotching.
    """
    _require_bpy("new_mesh")
    verts = np.ascontiguousarray(verts, dtype=np.float64)
    wind = None
    if orient and len(verts):
        quads = None if quads is None else np.ascontiguousarray(quads, np.int64)
        tris = None if tris is None else np.ascontiguousarray(tris, np.int64)
        wind = winding_audit(verts, quads=quads, tris=tris, apply=True)
    offset = np.zeros(3)
    if recentre and len(verts):
        offset = 0.5 * (verts.min(axis=0) + verts.max(axis=0))
        verts = verts - offset
    verts = np.ascontiguousarray(verts, dtype=np.float32)
    me = bpy.data.meshes.new(name)
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
    if smooth_deg is not None and len(me.polygons):
        shade_by_angle(me, smooth_deg)
    return me, tuple(float(v) for v in offset)


def shade_by_angle(me, deg=33.0):
    """Smooth everywhere except across a real arris. Pure numpy.

    `bpy.ops.object.shade_auto_smooth` needs a VIEW_3D context and cannot run
    headless — a Blender 5.x gotcha that cost time on this project before. This
    marks `sharp_edge` directly from the face-normal angle, so it works in `-b`.

    Flat-shading a cast or rolled surface turns its continuous curvature into
    visible facets at a few pixels; the chamfers, ends and fracture faces are
    genuinely sharp and must stay sharp. One threshold separates them.
    """
    _require_bpy("shade_by_angle")
    npoly, nloop, nedge = len(me.polygons), len(me.loops), len(me.edges)
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
    nxt[(ls + lt - 1).astype(np.int64)] = ls.astype(np.int64)
    a = lv.astype(np.int64); b = lv[nxt].astype(np.int64)
    nv = np.int64(len(me.vertices))
    key = np.minimum(a, b) * nv + np.maximum(a, b)
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)
    order = np.argsort(key, kind="stable")
    ks, fs = key[order], face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    f0 = np.zeros(ng, np.int64); f1 = np.full(ng, -1, np.int64)
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
    ekey = np.minimum(ev[:, 0], ev[:, 1]) * nv + np.maximum(ev[:, 0], ev[:, 1])
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def bake_attributes(me, attrs):
    """Per-vertex FLOAT attributes, for materials to read via ShaderNodeAttribute."""
    _require_bpy("bake_attributes")
    for name, vals in attrs.items():
        a = me.attributes.get(name) or me.attributes.new(name, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(vals, np.float32))


# ===========================================================================
# 4.  THE NODE DSL — 14 modules wrote this class, no two alike
# ===========================================================================

class NT(object):
    """Shader node-tree builder. `pin` takes a node, a (node, socket) pair, a
    colour/vector tuple or a scalar, so a graph reads as expressions."""

    def __init__(self, name):
        _require_bpy("NT")
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

    def pin(self, nd, idx, src, expect=None):
        """Wire or set an input socket.

        `expect` names the socket the caller BELIEVES sits at `idx`. Pass it and
        a version change that moves the socket raises instead of silently
        wiring the wrong thing.

        THIS ARGUMENT EXISTS BECAUSE INDEX PINNING FAILED SILENTLY AND COST THE
        WHOLE FOUNDATION. Blender 5.2 inserted `Filter Width` at index 2 of
        ShaderNodeBump, so `bump()` wired height into the filter, the normal
        chain into Height, and left the Height socket of the FIRST bump in every
        chain at its constant default of 1.0. A constant has zero gradient, so
        it produced NO RELIEF AT ALL — in the shared kit every wave-2 item is
        built on, and in the reference item every agent is told to copy. It
        passed the gate, because a node count cannot see it.
        """
        if src is None:
            return
        if expect is not None:
            got = nd.inputs[idx].name if idx < len(nd.inputs) else "<out of range>"
            if got != expect:
                raise RuntimeError(
                    f"{nd.bl_idname} input [{idx}] is {got!r}, not {expect!r}. "
                    "Blender has moved this socket. Wire it by NAME and re-check "
                    "every other index in this file — see itemkit.socket_audit()."
                )
        if isinstance(src, tuple) and src and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[idx].default_value = float(src)

    def pin_named(self, nd, name, src):
        """Wire or set an input socket BY NAME. Prefer this to `pin`."""
        if src is None:
            return
        for i, s in enumerate(nd.inputs):
            if s.name == name:
                return self.pin(nd, i, src)
        raise RuntimeError(
            f"{nd.bl_idname} has no input named {name!r}; it has "
            f"{[s.name for s in nd.inputs]}")

    # --- the addressing law, enforced ------------------------------------
    def object_coords(self):
        """`TexCoord -> Object`. Law 6, and the ONLY coordinate source here.

        There is deliberately no `position()` on this class. `Geometry ->
        Position` is world-space: at |P| ~ 1000 m the float coordinate feeding a
        procedural has ~0.06 mm of resolution left and the texture blotches.
        That is not a style preference, it is the measured cause of the first
        pass's rejection. The census found zero violations across 28 modules;
        an absent node keeps it that way for the next 372.
        """
        return (self.n("ShaderNodeTexCoord"), 3)      # socket 3 = Object

    def uv(self):
        return (self.n("ShaderNodeTexCoord"), 2)

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

    def noise(self, vec, scale=None, detail=8.0, rough=0.55, lac=2.0, out=0,
              wavelength_m=None):
        """Noise. Give `wavelength_m` to state the FEATURE SIZE YOU WANT.

        `scale` is Blender's own parameter and is NOT one over the feature size:
        the node emits 1.60x the wavelength that 1/scale implies. Writing
        `scale=1/0.00863` for an 8.63 mm crumple gets 13.8 mm, which lands
        outside item_gate's decisive r1/r2 bands (8.04 and 16.07 mm at
        373.3 px/m). See NOISE_WAVELENGTH_FACTOR.
        """
        if (scale is None) == (wavelength_m is None):
            raise ValueError("noise() takes exactly one of scale= or wavelength_m=")
        if wavelength_m is not None:
            scale = noise_scale_for(wavelength_m)
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec, expect="Vector")
        self.pin(nd, 2, scale, expect="Scale")
        self.pin(nd, 3, detail, expect="Detail")
        self.pin(nd, 4, rough, expect="Roughness")
        self.pin(nd, 5, lac, expect="Lacunarity")
        return (nd, out)

    def vor(self, vec, scale=None, feature="F1", out=0, rand=1.0,
            wavelength_m=None):
        """Voronoi. Give `wavelength_m` to state the CELL SIZE YOU WANT.

        The node emits 2.17x the wavelength that 1/scale implies. See
        VORONOI_WAVELENGTH_FACTOR.
        """
        if (scale is None) == (wavelength_m is None):
            raise ValueError("vor() takes exactly one of scale= or wavelength_m=")
        if wavelength_m is not None:
            scale = voronoi_scale_for(wavelength_m)
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, 0, vec, expect="Vector")
        self.pin(nd, 2, scale, expect="Scale")
        self.pin(nd, 8, rand, expect="Randomness")
        return (nd, out)

    def wave(self, vec, scale=None, distortion=0.0, detail=2.0, direction="X",
             wavelength_m=None):
        """Wave BANDS. Give `wavelength_m` to state the BAND PITCH YOU WANT.

        `scale` is Blender's own parameter and is NOT one over the pitch: the
        node emits 2*pi/20 = 0.31416 times the wavelength that 1/scale implies,
        so it is 3.183x FINER than a raw `scale=1/lam` asks for. That was
        R2-058; see WAVE_WAVELENGTH_FACTOR. `mat_fabric`'s weave, documented as
        a 1.15 mm pitch, was emitting 0.361 mm — a tenth of a pixel at the
        film's distances, a weave that cannot reach the image.
        """
        if (scale is None) == (wavelength_m is None):
            raise ValueError("wave() takes exactly one of scale= or wavelength_m=")
        if wavelength_m is not None:
            scale = wave_scale_for(wavelength_m, direction)
        nd = self.n("ShaderNodeTexWave", wave_type="BANDS",
                    bands_direction=direction)
        self.pin(nd, 0, vec); self.pin(nd, 1, scale)
        self.pin(nd, 2, distortion); self.pin(nd, 3, detail)
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
        """Height -> normal perturbation. WIRED BY NAME, and here is why.

        STATE THE RADIANCE MODULATION, NOT THE METRES. Give `modulation_pp` and
        `wavelength_m` instead of `distance` and the depth is derived from the
        contract sun (section 5b):

            nt.bump(h, 1.0, modulation_pp=0.28, wavelength_m=0.008)

        `distance` is Blender's own parameter and says nothing about how the
        surface will read: at this film's 12.47 deg sun the same 0.5 mm is
        m = 0.57 on an 8 mm crumple and m = 0.045 on a 100 mm flute. Three
        amplitude sets were rendered and rejected on the human figures and every
        one of them had been chosen in millimetres. Same fix shape as
        `noise(wavelength_m=)` replacing a raw `scale=`.

        `height_pp` is the peak-to-peak swing of what you feed Height (1.0 for a
        full-range ramp, ~0.6 for a raw Noise); the depth is divided by it and
        by `strength`, because those multiply the displacement too.


        This was pinned by index and Blender 5.2 inserted `Filter Width` at
        index 2, so the live order is:

            [0] Strength   [1] Distance   [2] Filter Width   [3] Height   [4] Normal

        The old code put `height` into Filter Width and the incoming normal
        chain into Height, which left the Height socket of the FIRST bump in
        every chain at its constant default of 1.0. A constant has zero
        gradient, so that bump contributed NO RELIEF AT ALL.

        It was silent. The material built, rendered, and passed the gate's
        node-count check; only `relief_reads_as_lip_and_shade` could see it, and
        that is the check 21 of 28 wave-1 items already failed. Measured on
        three spheres under the contract sun at 10 m / 35 mm, fine-band contrast
        against a smooth control of identical colour and roughness:

            shipped (miswired)                     0.257x
            frequency-corrected, still miswired    0.972x
            wired by name                          2.438x     (gate bar 2.0)

        Never pin this node by index again. `pin_named` costs one dict lookup.
        """
        if (distance is None) == (modulation_pp is None):
            raise ValueError(
                "bump() takes exactly one of distance= or modulation_pp= "
                "(with wavelength_m=). Prefer modulation_pp: see itemkit "
                "section 5b -- millimetres alone do not say how a surface will "
                "read, and three amplitude sets were rejected for it.")
        if modulation_pp is not None:
            if not wavelength_m:
                raise ValueError(
                    "bump(modulation_pp=...) needs wavelength_m=. The same "
                    "amplitude is m = 0.57 at 8 mm and m = 0.045 at 100 mm; "
                    "an amplitude with no wavelength is not a relief spec.")
            s = float(strength) if not isinstance(strength, tuple) else 1.0
            amp_mm = relief_amplitude_for(modulation_pp, wavelength_m)
            distance = amp_mm * 1e-3 / max(abs(s) * float(height_pp), 1e-9)
        nd = self.n("ShaderNodeBump")
        self.pin_named(nd, "Strength", strength)
        self.pin_named(nd, "Distance", distance)
        self.pin_named(nd, "Height", height)
        if normal is not None:
            self.pin_named(nd, "Normal", normal)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)

    def principled_out(self, **kw):
        """BSDF + Material Output, wired. kw are socket names -> pin sources."""
        bsdf = self.n("ShaderNodeBsdfPrincipled")
        for k, v in kw.items():
            key = k.replace("_", " ").title()
            for cand in (k, key, key.replace(" ", "")):
                if cand in bsdf.inputs:
                    self.pin(bsdf, bsdf.inputs.find(cand), v)
                    break
        out = self.n("ShaderNodeOutputMaterial")
        self.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
        return bsdf

    def texture_node_count(self):
        """What the gate's `material_depth` floor counts. Check before shipping."""
        return sum(1 for nd in self.t.nodes
                   if nd.bl_idname.startswith("ShaderNodeTex")
                   and nd.bl_idname != "ShaderNodeTexImage")


def object_coords(nt):
    """Free-function form of `NT.object_coords`, for graphs built by hand."""
    return nt.object_coords()


# ===========================================================================
# 5.  LIGHT — a sun that cannot point at the sky
# ===========================================================================

def contract_sun(prefix, scene=None, coll_=None, sky=True):
    """The film's sun and sky, exactly as `world_contract` measured them.

    Two things wave 1 got wrong are made unrepresentable here rather than
    remembered:

    NO SUN AT ALL. Two of 28 test scenes built a Sky Texture background and no
    SUN lamp. A Sky Texture is not a sun: the whole first adversarial peep pass
    was conducted under sky-only light, R minus B negative in every luminance
    band and increasingly so toward the highlights, and every appearance-based
    conclusion in it had to be thrown away. This function always creates the
    lamp, and returns it so the caller can assert on it.

    A SUN POINTING UP. R2-021: the author of the gate's own positive control
    wrote `(-d).to_track_quat('Z','Y')` and shipped a sun emitting at z = +0.216
    — straight at the sky — twice in one session, having disproven the same bug
    earlier the same day. The emitted direction is computed and checked below;
    if it does not go downward this REFUSES.

    `prefix` names the world and the lamp so another module's `purge()` cannot
    delete them (see `purge`).
    """
    _require_bpy("contract_sun")
    from mathutils import Vector
    if not prefix:
        raise ValueError("contract_sun(prefix): name your datablocks.")
    scene = scene or bpy.context.scene

    if sky:
        w = bpy.data.worlds.new(prefix + "World")
        w.use_nodes = True
        nt = w.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputWorld")
        bg = nt.nodes.new("ShaderNodeBackground")
        sk = nt.nodes.new("ShaderNodeTexSky")
        avail = {e.identifier for e in sk.bl_rna.properties["sky_type"].enum_items}
        for want in (C.SKY_MODEL, "MULTIPLE_SCATTERING", "SINGLE_SCATTERING",
                     "HOSEK_WILKIE"):
            if want in avail:
                sk.sky_type = want
                break
        for attr, val in (("sun_disc", C.SKY_SUN_DISC),
                          ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG)),
                          ("sun_intensity", 1.0),
                          ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                          ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                          ("altitude", C.SKY_ALTITUDE),
                          ("air_density", C.SKY_AIR),
                          ("aerosol_density", C.SKY_AEROSOL),
                          ("ozone_density", C.SKY_OZONE)):
            if hasattr(sk, attr):
                setattr(sk, attr, val)
        bg.inputs["Strength"].default_value = C.SKY_STRENGTH
        nt.links.new(sk.outputs["Color"], bg.inputs["Color"])
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
        scene.world = w

    lt = bpy.data.lights.new(prefix + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(prefix + "Sun", lt)
    d = Vector(C.SUN_DIR)                      # points FROM the ground TO the sun
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
    ob.visible_camera = False
    (coll_ or scene.collection).objects.link(ob)

    # --- THE REFUSAL. A SUN lamp emits along its local -Z. -----------------
    emit = (ob.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0)))
    if emit.z > -0.05:
        raise RuntimeError(
            "REFUSING: this sun emits toward (%.4f, %.4f, %.4f) -- z is not "
            "negative, so it is lighting the sky, not the ground. This is "
            "R2-021 exactly: the same bug was written twice in one session and "
            "the measurement that followed could not see it, because a "
            "measurement cannot tell you its input was black."
            % (emit.x, emit.y, emit.z))
    if C.SUN_ENERGY <= 0.0:
        raise RuntimeError("REFUSING: world_contract.SUN_ENERGY is %r"
                           % (C.SUN_ENERGY,))

    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:                                   # noqa: BLE001
        pass

    # --- THE GRADE. R2-059. THIS SET `C.REFERENCE_EXPOSURE_EXTERIOR`. --------
    #
    # -3.048 is the contract's DERIVED exposure and it is REFUTED. The measured
    # value is `world/film_exposure.py`'s FILM_EXPOSURE = -3.628, correct to
    # 0.006 stops against an 18 % card with two view transforms agreeing to
    # 0.0141 stops. The difference is 0.580 stops, and it went OVER: every item
    # test frame ever judged through this helper was 0.58 stops bright,
    # including the crew macro that passed 8/8 and the frames the human-figure
    # brief was written from.
    #
    # THIS FUNCTION IS WHY IT WAS SO EXPENSIVE. `contract_sun` exists precisely
    # so that no item agent quotes the light independently — it is the one place
    # the lamp, the sky and the grade come from. A wrong number here is not one
    # module's mistake, it is every module's, and none of them can see it,
    # because the helper's whole promise is that you do not have to check.
    #
    # It stayed invisible because the ONE caller that checked was accidentally
    # immune: the beat-3 sim's `witness.py` overwrites the exposure AFTER
    # calling this, so its saved scenes really are at -3.628.
    #
    # IMPORTED, NEVER SPELLED. Writing -3.628 here would make a second copy of a
    # measured number and this defect is what a second copy costs. And it is now
    # ASSERTED rather than merely set, the way tools/build_verify_scene.py
    # asserts its grade: a helper that silently sets a value the caller then
    # overwrites is how the sim agent's scenes came out right while everyone
    # else's came out 0.58 stops over, with nothing on either side saying so.
    import film_exposure as FX                          # noqa: E402
    scene.view_settings.exposure = FX.FILM_EXPOSURE
    got = float(scene.view_settings.exposure)
    if abs(got - FX.FILM_EXPOSURE) > 1e-4:
        raise RuntimeError(
            "REFUSING: view exposure read back %+.4f after being set to "
            "film_exposure.FILM_EXPOSURE %+.4f. The grade is the film's, "
            "measured; it is not this scene's to choose." % (got, FX.FILM_EXPOSURE))
    if abs(FX.FILM_EXPOSURE - C.REFERENCE_EXPOSURE_EXTERIOR) < 1e-6:
        raise RuntimeError(
            "REFUSING: film_exposure.FILM_EXPOSURE has become equal to "
            "world_contract.REFERENCE_EXPOSURE_EXTERIOR (%+.4f). The measured "
            "value and the refuted derived one must not be the same number; if "
            "the contract has genuinely been re-measured, delete this check "
            "deliberately rather than let R2-059 land again unnoticed."
            % (FX.FILM_EXPOSURE,))
    log("sun %.3f W/m2, elev %.2f deg, bearing %.2f deg, emitting z %+.4f; "
        "%s look=%s exposure %+.3f EV (film_exposure.FILM_EXPOSURE, MEASURED; "
        "the contract's derived %+.3f is refuted and is %+.3f stops over)"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, emit.z,
           C.VIEW_TRANSFORM, C.VIEW_LOOK, FX.FILM_EXPOSURE,
           C.REFERENCE_EXPOSURE_EXTERIOR,
           C.REFERENCE_EXPOSURE_EXTERIOR - FX.FILM_EXPOSURE))
    return ob


# ===========================================================================
# 5b. RELIEF AMPLITUDE — THE SUN IS THE AMPLIFIER, AND IT IS NOT 1
#
# WHAT THE EYE JUDGES IS NOT THE HEIGHT OF A BUMP. It is the radiance
# modulation the bump produces. A Lambertian surface lit at elevation `e` has
# radiance proportional to sin(e); tilt its normal by a small angle theta
# towards or away from the sun and that becomes sin(e +- theta) ~ sin e +-
# theta cos e, so the RELATIVE peak-to-peak modulation is
#
#         m = 2 theta / tan(e)
#
# THIS FILM'S SUN IS AT 12.47 deg, WHERE tan(e) = 0.2213. The same crumple that
# is a soft grain at noon is a saturated crust here: relative to a 45 deg
# midday reference the divisor amplifies by 1/0.2213 = 4.52x. `sun_amplifier()`
# DERIVES that from `world_contract.SUN_ELEV_DEG`; it is not written down
# anywhere as 4.5, because if the sun moves the amplifier moves with it and a
# hardcoded 4.5 would then be a lie that renders.
#
# THIS COST THREE RENDERED-AND-REJECTED AMPLITUDE SETS ON THE HUMAN FIGURES,
# and every one of them had been reasoned about in MILLIMETRES OF CLOTH:
#
#     shipped      5.0 deg  -> m = 0.79   a machined cone
#     first fix   22.6 deg  -> m = 3.76   coarse stucco
#     second fix  10.4 deg  -> m = 1.66   thick felt / towelling
#     accepted     1.8 deg  -> m = 0.28   cloth; creases carry the rest
#
# AND IT REPEATS ONE LAYER DOWN. After the fabric SHADER was corrected to
# 0.28 pp the same misconception turned out to be in the fold-field GEOMETRY --
# 8.2 mm of radial displacement at a 100 mm flute is a 14.4 deg surface, m =
# 2.32 -- and became the dominant defect. It was corrected 2.09-4.16 -> 0.93-
# 1.29 pp. CHECK BOTH LAYERS. Correcting one and not the other is exactly what
# happened, twice, and the second time it was invisible because the first fix
# had worked.
#
# THE FIX SHAPE IS `noise(wavelength_m=...)`'s: make the caller state the
# PHYSICAL QUANTITY IT ACTUALLY MEANS. A module asks for a radiance modulation
# and is handed the millimetres, rather than choosing millimetres and finding
# out what they look like from a render.
# ===========================================================================

MIDDAY_REFERENCE_ELEV_DEG = 45.0    # tan = 1.0; the "amplifier" is against this


def sun_elev_deg():
    """The contract's sun elevation. READ, not copied (see selftest [8])."""
    return float(C.SUN_ELEV_DEG)


def sun_amplifier(elev_deg=None):
    """How much more a given slope modulates radiance here than at midday.

    tan(45 deg) / tan(e). At this film's 12.47 deg that is 4.52x. Derived, so
    a change of sun changes it; never write the number down.
    """
    e = math.radians(sun_elev_deg() if elev_deg is None else float(elev_deg))
    return math.tan(math.radians(MIDDAY_REFERENCE_ELEV_DEG)) / math.tan(e)


def slope_for_modulation(mod_pp, elev_deg=None):
    """Surface slope in DEGREES that modulates radiance by `mod_pp` p-p.

    Exact inverse of `modulation_for_slope`: theta = asin(m tan(e) / 2), and it
    REFUSES a modulation the sun cannot deliver at any slope (m > 2/tan(e) =
    9.04 here) instead of returning a NaN that would silently become a NaN
    vertex.
    """
    e = math.radians(sun_elev_deg() if elev_deg is None else float(elev_deg))
    s = 0.5 * float(mod_pp) * math.tan(e)
    if not -1.0 <= s <= 1.0:
        raise ValueError(
            "no slope produces m = %.3f at a sun elevation of %.4f deg; the "
            "ceiling is %.3f (a normal tilted to the terminator). Asking for "
            "more is asking for a shadow, which is geometry, not relief."
            % (mod_pp, math.degrees(e), 2.0 / math.tan(e)))
    return math.degrees(math.asin(s))


def modulation_for_slope(slope_deg, elev_deg=None):
    """The radiance modulation a slope of `slope_deg` produces. The forward law.

    Use this to ASK WHAT YOU ALREADY BUILT. Feeding a module's shipped
    amplitudes through it is how the felt was found, and it takes no render.

    WHICH FORM, AND WHY IT DOES NOT MATTER WHERE IT MATTERS. Radiance on a
    Lambertian surface goes as n.L; flat ground under a sun at elevation e gives
    sin(e), and tilting the normal by theta gives sin(e +- theta), so exactly

        m = [sin(e+th) - sin(e-th)] / sin(e) = 2 sin(theta) / tan(e)

    The brief writes the small-angle form `m = 2 theta / tan(e)` and the human
    figures' record was tabulated with `2 tan(theta) / tan(e)`. All three agree
    to 0.05 % at the ACCEPTED 0.28 pp and to 1.6 % at the rejected 1.66; they
    only separate above m ~ 3, where every set on record was rejected anyway.
    This uses the exact one because there is no reason not to, and the selftest
    reproduces the recorded ladder to show the choice changes no verdict.
    """
    e = math.radians(sun_elev_deg() if elev_deg is None else float(elev_deg))
    return 2.0 * math.sin(math.radians(float(slope_deg))) / math.tan(e)


def relief_amplitude_for(mod_pp, wavelength_m, elev_deg=None):
    """PEAK-TO-PEAK MILLIMETRES for a target radiance modulation. THE HELPER.

    State what you want the surface to DO to the light, and get the millimetres
    that do it, at the wavelength you are building at.

        amp_mm = K.relief_amplitude_for(0.28, wavelength_m=0.008)

    A sinusoid of peak-to-peak amplitude A and wavelength lam has maximum slope
    atan(pi A / lam), so A = lam tan(theta) / pi. WAVELENGTH IS NOT OPTIONAL and
    that is the whole point of stating it: the same 0.5 mm is a 3.6 deg slope on
    an 8 mm crumple and a 0.29 deg slope on a 100 mm flute -- m = 0.57 against
    m = 0.045, a factor of thirteen. Amplitude alone means nothing.

    BOUND IT BOTH WAYS. This returns a target, not a ceiling. Too little relief
    is as wrong as too much: 5.0 deg / m = 0.79 rendered as a machined cone and
    was rejected just as 22.6 deg / m = 3.76 was. `relief_budget` prints both
    ends.
    """
    th = math.radians(slope_for_modulation(mod_pp, elev_deg))
    return math.tan(th) * float(wavelength_m) / math.pi * 1000.0


def modulation_for_amplitude(amp_mm, wavelength_m, elev_deg=None):
    """What a relief stage you ALREADY have actually does to the light.

    The audit direction. Point it at every stage of an existing module before
    changing anything: `relief_budget`.
    """
    th = math.degrees(math.atan(math.pi * float(amp_mm) * 1e-3
                                / max(float(wavelength_m), 1e-12)))
    return modulation_for_slope(th, elev_deg)


#: What the rendered-and-looked-at record supports, peak-to-peak modulation.
#: These are BANDS, not bars, and they came off renders that were judged by eye
#: -- 0.28 accepted as cloth, 1.66 rejected as felt, 0.79 rejected as machined.
RELIEF_BANDS = {
    "isotropic_micro": (0.12, 0.45),   # weave, grain, cast skin, blasted metal
    "isotropic_macro": (0.35, 0.95),   # crumple, aggregate, hand-laid texture
    "sparse_crease":   (0.80, 1.60),   # acts on a fraction of the area only
    "geometry_fold":   (0.60, 1.40),   # real folds carried by real geometry
    "hard_feature":    (1.50, 6.00),   # an arris, a lip, a joint -- an EDGE
}


def relief_budget(stages, elev_deg=None, band=None, verbose=True):
    """Feed it (name, wavelength_m, amp_mm) and it prints slope and m for each.

    THE INSTRUMENT FOR "CHECK BOTH LAYERS". Run it on the shader's bump stages
    AND on the geometry that carries them, in the same call if you like, and the
    two columns are directly comparable because both are radiance.

    Returns a list of dicts and, if `band` names a `RELIEF_BANDS` entry, marks
    every stage that is outside it -- on EITHER side.
    """
    lo, hi = RELIEF_BANDS.get(band, (None, None))
    rows = []
    for name, lam, amp in stages:
        m = modulation_for_amplitude(amp, lam, elev_deg)
        th = math.degrees(math.atan(math.pi * float(amp) * 1e-3
                                    / max(float(lam), 1e-12)))
        verdict = ""
        if lo is not None:
            verdict = ("LOW" if m < lo else "HIGH" if m > hi else "ok")
        rows.append({"name": name, "wavelength_m": float(lam),
                     "amp_mm": float(amp), "slope_deg": th, "m": m,
                     "verdict": verdict})
        if verbose:
            log("relief %-16s lam %7.2f mm  amp %6.3f mm  slope %6.2f deg  "
                "m %6.3f pp %s" % (name, lam * 1000.0, amp, th, m, verdict))
    return rows


def _vector_gain(sock, depth=0):
    """How much the coordinate reaching this texture has ALREADY been scaled.

    THE SCALE SOCKET IS NOT THE WHOLE SCALE, AND THAT WAS WORTH A FACTOR OF 110.
    Half the item modules never touch `Scale` at all; they multiply the object
    coordinate first and leave the texture at 1.0:

        g.noise(g.vmath('MULTIPLY', obj, (110.0, 110.0, 110.0)), scale=1.0)

    Reading only the Scale socket calls that a 1.6 m feature when it is a 14.5 mm
    one. Measured consequence: `pont_deck_slab`, `gantry_truss` and `pont_girder`
    were all put on record at m_median 0.002 -- "essentially no shader relief in
    either layer" -- and every one of them is really between 0.18 and 0.88.
    Nothing was flat; the instrument was pointed at the wrong socket. This is the
    same class of mistake as reading `scale=` for a wavelength in the first
    place, one level up.

    Returns the largest absolute component of the accumulated multiply, because
    the FINEST direction is the one that sets the slope. A non-uniform scale has
    no single wavelength, and the caller is told the gain rather than being
    handed an average that is true in no direction.
    """
    if depth > 12:
        return 1.0
    for lk in sock.links:
        n2 = lk.from_node
        if n2.bl_idname != "ShaderNodeVectorMath":
            # a Mapping node carries its own scale; anything else is a
            # coordinate source and the walk stops there
            if n2.bl_idname == "ShaderNodeMapping":
                try:
                    v = n2.inputs["Scale"].default_value
                    g = max(abs(float(x)) for x in v)
                except Exception:                            # noqa: BLE001
                    g = 1.0
                return g * _vector_gain(n2.inputs["Vector"], depth + 1)
            return 1.0
        op = n2.operation
        if op == "SCALE":
            try:
                g = abs(float(n2.inputs["Scale"].default_value))
            except Exception:                                # noqa: BLE001
                g = 1.0
        elif op == "MULTIPLY":
            try:
                v = n2.inputs[1].default_value
                g = max(abs(float(x)) for x in v)
            except Exception:                                # noqa: BLE001
                g = 1.0
        else:
            # ADD/SUBTRACT translate, they do not scale; anything else is not
            # something this can reason about, so it contributes 1.0 and says so
            g = 1.0
        return g * _vector_gain(n2.inputs[0], depth + 1)
    return 1.0


def _tex_wavelength_m(nd):
    """Feature wavelength a texture node emits.

    `Scale` TIMES whatever the coordinate was already multiplied by on its way
    in -- see `_vector_gain`, and do not go back to reading one of the two.
    """
    try:
        s = float(nd.inputs["Scale"].default_value)
    except Exception:                                       # noqa: BLE001
        return None
    try:
        s *= _vector_gain(nd.inputs["Vector"])
    except Exception:                                       # noqa: BLE001
        pass
    if abs(s) < 1e-12:
        return None
    if nd.bl_idname == "ShaderNodeTexNoise":
        return NOISE_WAVELENGTH_FACTOR / s
    if nd.bl_idname == "ShaderNodeTexVoronoi":
        return VORONOI_WAVELENGTH_FACTOR / s
    if nd.bl_idname == "ShaderNodeTexWave":
        # R2-058. This said `1.0 / s` and was 3.183x too coarse, which made
        # every Wave-driven stage this function has ever audited report 1/3.183
        # of its real modulation. See WAVE_WAVELENGTH_FACTOR.
        diag = (getattr(nd, "wave_type", "BANDS") == "BANDS"
                and getattr(nd, "bands_direction", "X") == "DIAGONAL")
        return (WAVE_DIAGONAL_FACTOR if diag else WAVE_WAVELENGTH_FACTOR) / s
    return None


def emitted_wavelength_m(make_fac, span=2.0, px=4096, keep=False):
    """RENDER a texture alone and MEASURE the wavelength it emits, in metres.

    THE ONLY HONEST CHECK ON A WAVELENGTH CONSTANT, and the reason R2-058 lived
    for as long as it did. A selftest that computes `scale = F / lam` and then
    asserts `lam == F / scale` is an ALGEBRAIC IDENTITY: it uses the constant on
    both sides and cannot fail for any value of F, including a wrong one.
    `pit_wall_unit_itemkit`'s relief round-trip is exactly that shape and passed
    every time while its ply-veneer stage was 3.18x off. This function goes
    outside the arithmetic and asks Cycles.

    `make_fac(nt)` is a callback handed a fresh `NT` and returning the
    (node, socket) whose value should be emitted. Everything else is fixed:

      * ITS OWN SCENE DATABLOCK. It never touches the caller's scene, and it
        REFUSES unless that scene contains exactly its own plane and camera.
        `--factory-startup` is not an empty scene: the default Cube once sat
        between an ortho camera and a measurement plane and returned one
        identical number for fourteen different stages.
      * Cycles, 1 sample, max_bounces 0, DENOISER OFF. A denoiser is a low-pass
        filter aimed at precisely the quantity being measured.
      * view_transform 'Standard'. A tone curve is monotone but not linear and
        feeds harmonics into the spectrum.
      * A least-squares sinusoid fit refined by golden section, not a bin index:
        zero-crossing and FFT-peak estimators quantise to span/(k/2) and read
        0.03125 where the answer is 0.031416.

    Returns metres per cycle along the plane's local X. NaN if the row is
    constant, which is the correct answer for e.g. BANDS Z on a plane (a plane's
    object coordinates are (x, y, 0) at any orientation, so local z never
    varies) and is why this returns NaN rather than a number.
    """
    _require_bpy("emitted_wavelength_m")
    import tempfile
    sc = bpy.data.scenes.new("IKT_WAVEPROBE")
    old = bpy.context.window.scene if bpy.context.window else None
    tmp = tempfile.mkdtemp(prefix="ikt_wave_")
    try:
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = 1
        sc.cycles.use_denoising = False
        sc.cycles.max_bounces = 0
        sc.render.resolution_x, sc.render.resolution_y = int(px), 4
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = 'OPEN_EXR'
        sc.render.image_settings.color_depth = '32'
        sc.render.film_transparent = False
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0.0
        wd = bpy.data.worlds.new("IKT_WAVEPROBE_W")
        sc.world = wd
        wd.use_nodes = True
        for nname in ("Background",):
            bn = wd.node_tree.nodes.get(nname)
            if bn:
                bn.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
                bn.inputs[1].default_value = 0.0

        me = bpy.data.meshes.new("IKT_WAVEPROBE_M")
        h = span * 0.5
        me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)],
                       [], [(0, 1, 2, 3)])
        me.update()
        pl = bpy.data.objects.new("IKT_WAVEPROBE_PLANE", me)
        sc.collection.objects.link(pl)
        cd = bpy.data.cameras.new("IKT_WAVEPROBE_CAM")
        cd.type = 'ORTHO'
        cd.ortho_scale = span
        cam = bpy.data.objects.new("IKT_WAVEPROBE_CAM", cd)
        sc.collection.objects.link(cam)
        cam.location = (0.0, 0.0, 5.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        sc.camera = cam
        names = sorted(o.name for o in sc.collection.all_objects)
        if names != ["IKT_WAVEPROBE_CAM", "IKT_WAVEPROBE_PLANE"]:
            raise RuntimeError("wavelength probe REFUSES: its scene holds %r, "
                               "not just its own plane and camera" % (names,))

        nt = NT("IKT_WAVEPROBE_MAT")
        src = make_fac(nt)
        em = nt.n("ShaderNodeEmission")
        nt.pin_named(em, "Strength", 1.0)
        nt.pin_named(em, "Color", src)
        out = nt.n("ShaderNodeOutputMaterial")
        nt.t.links.new(em.outputs[0], out.inputs["Surface"])
        me.materials.append(nt.m)

        sc.render.filepath = os.path.join(tmp, "probe")
        if old is not None:
            bpy.context.window.scene = sc
        bpy.ops.render.render(write_still=True, scene=sc.name)
        path = os.path.join(tmp, "probe.exr")
        img = bpy.data.images.load(path, check_existing=False)
        a = np.array(img.pixels[:], dtype=np.float64).reshape(4, int(px), 4)
        bpy.data.images.remove(img)
        row = a[2, :, 0]
    finally:
        if old is not None:
            bpy.context.window.scene = old
        for d in (bpy.data.objects, bpy.data.meshes, bpy.data.cameras,
                  bpy.data.materials, bpy.data.worlds, bpy.data.scenes):
            for db in list(d):
                if db.name.startswith("IKT_WAVEPROBE"):
                    try:
                        d.remove(db)
                    except Exception:                       # noqa: BLE001
                        pass
        if not keep:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    n = len(row)
    x = np.arange(n, dtype=np.float64)
    s = row - np.polyval(np.polyfit(x, row, 1), x)
    if float(np.std(s)) < 1e-7:
        return float('nan')                     # constant row: no wavelength
    F = np.abs(np.fft.rfft(s * np.hanning(n)))
    F[0] = 0.0
    k0 = int(np.argmax(F))
    if k0 == 0:
        return float('nan')
    xm = np.linspace(-0.5, 0.5, n, endpoint=False) * span

    def _resid(f):
        A = np.column_stack([np.sin(2 * math.pi * f * xm),
                             np.cos(2 * math.pi * f * xm), np.ones_like(xm)])
        c, *_ = np.linalg.lstsq(A, s, rcond=None)
        return float(np.sum((s - A @ c) ** 2))

    lo, hi = (k0 - 1.0) / span, (k0 + 1.0) / span
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    for _ in range(70):
        c1 = hi - gr * (hi - lo)
        c2 = lo + gr * (hi - lo)
        if _resid(c1) < _resid(c2):
            hi = c2
        else:
            lo = c1
    f = 0.5 * (lo + hi)
    return 1.0 / f if f > 0 else float('nan')


def bump_relief_report(node_tree, elev_deg=None, height_pp=1.0):
    """Every ShaderNodeBump in a graph, as SLOPE AND RADIANCE MODULATION.

    THE SHADER HALF of "check both layers", on a graph that already exists --
    which is what lets the 28 wave-1 modules be audited from their built blends
    without re-running a single builder.

    It walks back from each bump's Height socket to the nearest procedural
    texture node, reads that node's live `Scale`, converts it to a wavelength
    with the factor this file already measured, and reports

        amplitude_mm = Distance * Strength * height_pp * 1000

    `height_pp` is the peak-to-peak swing of the height signal reaching the
    node and defaults to 1.0, which is the CONSERVATIVE assumption -- a raw
    Noise output swings about 0.6 of that, a ramped one can swing the full 1.0.
    A stage this reports at m = 2.3 is therefore at least 1.4, never less.
    Where no driving texture can be found the row says so instead of guessing;
    an unknown wavelength is not a wavelength of 1 m.
    """
    _require_bpy("bump_relief_report")
    rows = []
    for nd in node_tree.nodes:
        if nd.bl_idname != "ShaderNodeBump":
            continue
        dist = float(nd.inputs["Distance"].default_value)
        stg = float(nd.inputs["Strength"].default_value)
        lam, src, seen = None, None, set()
        chained = any(lk.from_node.bl_idname == "ShaderNodeBump"
                      for lk in nd.inputs["Height"].links)
        stack = [nd.inputs["Height"]]
        while stack and lam is None:
            sock = stack.pop()
            for lk in sock.links:
                n2 = lk.from_node
                if n2.name in seen:
                    continue
                seen.add(n2.name)
                w = _tex_wavelength_m(n2)
                if w:
                    lam, src = w, n2.bl_idname
                    break
                # NEVER WALK A BUMP'S `Normal` SOCKET. That is the normal chain,
                # not the height signal, and following it makes every stage in a
                # chain report whichever texture the FIRST one happened to use.
                # It also makes R2-038 invisible: when Height and Normal were
                # swapped, walking through Normal still found a texture and the
                # graph looked healthy.
                stack.extend([s for s in n2.inputs
                              if not (n2.bl_idname == "ShaderNodeBump"
                                      and s.name == "Normal")])
        amp = dist * stg * float(height_pp) * 1000.0
        row = {"node": nd.name, "distance_m": dist, "strength": stg,
               "amp_mm": amp, "wavelength_m": lam, "driver": src,
               "height_driven_by_a_bump": bool(chained),
               "height_unlinked": not nd.inputs["Height"].links}
        if lam:
            row["slope_deg"] = math.degrees(math.atan(
                math.pi * amp * 1e-3 / lam))
            row["m"] = modulation_for_amplitude(amp, lam, elev_deg)
        else:
            row["slope_deg"] = None
            row["m"] = None
            row["why"] = "no procedural texture found upstream of Height"
        rows.append(row)
    return rows


def geometry_relief_report(me, bands=((0.004, 0.012), (0.012, 0.040),
                                      (0.040, 0.150)), elev_deg=None):
    """THE GEOMETRY HALF: what the built surface itself does to the light.

    For every interior edge, the dihedral angle between its two faces IS the
    surface slope change at that edge's own length scale. Grouped into
    wavelength bands by edge length and reported as an area-weighted RMS slope
    and its radiance modulation.

    THIS IS THE LAYER THE HUMAN FIGURES' SECOND MISS WAS IN. The fabric shader
    was corrected and the FOLD FIELD, made of real triangles, still carried
    m = 2.32. Nothing that reads materials could ever have seen it.

    A dihedral is a slope CHANGE across one edge, so this is not identical to
    `modulation_for_amplitude` on a smooth sinusoid -- for a sinusoid resolved
    by n samples per wavelength the per-edge dihedral is about 2 pi / n of the
    full peak-to-peak swing. It is reported as `rms_dihedral_deg` and converted
    with the SAME law, and the selftest calibrates it against a sinusoid of
    known amplitude so the two are known to agree to a stated factor rather
    than assumed to.
    """
    _require_bpy("geometry_relief_report")
    nv, nl, nf = len(me.vertices), len(me.loops), len(me.polygons)
    if not nf:
        return []
    co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co)
    V = co.reshape(-1, 3).astype(np.float64)
    fn = np.empty(nf * 3, np.float32); me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(nf, 3).astype(np.float64)
    ar = np.empty(nf, np.float32); me.polygons.foreach_get("area", ar)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    corners = lv.astype(np.int64)
    starts = ls.astype(np.int64); counts = lt.astype(np.int64)
    nxt = np.arange(nl, dtype=np.int64) + 1
    nxt[starts + counts - 1] = starts
    a, b = corners, corners[nxt]
    face = np.repeat(np.arange(nf, dtype=np.int64), counts)
    key = np.minimum(a, b).astype(np.int64) * nv + np.maximum(a, b)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    use = np.bincount(grp)
    two = np.flatnonzero(use == 2)
    if not len(two):
        return []
    pos = np.searchsorted(np.flatnonzero(first), two)
    i0 = np.flatnonzero(first)[pos]
    f0 = face[order][i0]
    f1 = face[order][i0 + 1]
    ea = a[order][i0]; eb = b[order][i0]
    L = np.linalg.norm(V[ea] - V[eb], axis=1)
    dot = np.clip(np.einsum("ij,ij->i", fn[f0], fn[f1]), -1.0, 1.0)
    ang = np.degrees(np.arccos(dot))
    w = 0.5 * (ar[f0] + ar[f1])
    out = []
    for lo, hi in bands:
        sel = (L >= lo) & (L < hi)
        if not sel.any():
            out.append({"band_m": (lo, hi), "edges": 0})
            continue
        rms = float(np.sqrt(np.average(ang[sel] ** 2, weights=w[sel])))
        out.append({"band_m": (lo, hi), "edges": int(sel.sum()),
                    "median_edge_m": float(np.median(L[sel])),
                    "rms_dihedral_deg": rms,
                    "m": modulation_for_slope(rms, elev_deg)})
    return out


# ===========================================================================
# 6.  CAMERA — the resolution is not something an agent can get wrong
# ===========================================================================

def add_camera(name, loc, look, lens_mm, coll_, fstop=None, sensor_mm=SENSOR_MM):
    """A camera at `loc` aimed at `look`. Returns (object, measured_distance_m)."""
    _require_bpy("add_camera")
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = float(lens_mm)
    cd.sensor_width = float(sensor_mm)
    cd.clip_start = 0.005
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = tuple(float(v) for v in loc)
    d = Vector(tuple(float(v) for v in look)) - Vector(ob.location)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll_.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    return ob, float(d.length)


def macro_rig(name, loc, look, lens_mm, coll_, scene=None, samples=256,
              want_distance_m=None, tolerance_m=0.02, fstop=None,
              resolution=None, i_know_this_is_not_the_gate_resolution=False):
    """The deliverable macro camera and its render settings. 3840 x 2160.

    R2-020 IS THIS FUNCTION'S REASON TO EXIST. `tools/item_gate.py` computes
    `px_per_m` from `RES_X_4K = 3840`; ITEM-CAMPAIGN-BRIEF sec 3 prints 3840 in
    the formula it tells every agent to build to; the wave-1 harness asked the
    renderer for 1920x1080, and **17 of 28 wave-1 modules also set
    `resolution_x = 1920` in their own test scenes**. 11 of 28 delivered heroes
    were therefore judged at twice their real resolution: a feature the gate
    called 6 px was 3 px in the frame the reviewer actually looked at.

    So the resolution is not a parameter with a sensible default here. Asking
    for another one requires naming the keyword
    `i_know_this_is_not_the_gate_resolution`, which is long on purpose: a draft
    pass at 1080p is legitimate, and it must not be possible to do it by
    accident and then ship the result.

    `want_distance_m` closes the other half. The manifest's distance is the
    specification; a camera placed by arithmetic that drifted is a macro of the
    wrong shot. Pass it and the MEASURED camera-to-aim distance is checked
    against it and reported. Not asserting this is how wave 1 shipped peeps
    framed at distances the camera never reaches.
    """
    _require_bpy("macro_rig")
    scene = scene or bpy.context.scene
    if resolution is None:
        res_x, res_y = RES_X_4K, RES_Y_4K
    else:
        res_x, res_y = int(resolution[0]), int(resolution[1])
        if (res_x, res_y) != (RES_X_4K, RES_Y_4K) and \
                not i_know_this_is_not_the_gate_resolution:
            raise ValueError(
                "REFUSING to render the deliverable at %dx%d. The gate scores "
                "every pixel figure against %dx%d (item_gate.py RES_X_4K) and "
                "never opened the image, which is R2-020: 11 of 28 wave-1 "
                "heroes shipped at half resolution and were scored as 4K, every "
                "pixel judgement on them out by exactly 2x. If this really is a "
                "draft pass, pass "
                "i_know_this_is_not_the_gate_resolution=True and do not ship "
                "the result as macro.png."
                % (res_x, res_y, RES_X_4K, RES_Y_4K))

    cam, dist = add_camera(name, loc, look, lens_mm, coll_, fstop=fstop)
    if want_distance_m is not None:
        err = abs(dist - float(want_distance_m))
        if err > float(tolerance_m):
            raise RuntimeError(
                "REFUSING: %s stands %.4f m from its aim point, but the "
                "specification is %.4f m (out by %.0f mm, tolerance %.0f mm). "
                "The manifest's distance IS the shot; a macro at another "
                "distance is a picture of a different item."
                % (name, dist, float(want_distance_m), err * 1000.0,
                   float(tolerance_m) * 1000.0))

    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.cycles.samples = int(samples)
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.use_denoising = True
    ppm = px_per_m(dist, lens_mm, res_x)
    log("%s: %.4f m on a %.0f mm lens at %dx%d -> %.1f px/m, %.3f mm/px; "
        "a 1 px feature is %.2f mm"
        % (name, dist, lens_mm, res_x, res_y, ppm, 1000.0 / ppm, 1000.0 / ppm))
    return cam, dist, ppm


# ===========================================================================
# 7.  PLACEMENT — the contract, never an assumed z
# ===========================================================================

def ground_z(x, y, allow_terrain=False):
    """The world's ground height. Law 5: never an assumed z.

    TWO THINGS `world_contract.world_ground_z` DOES THAT ARE EASY TO GET WRONG,
    and I got both wrong writing this file before a smoke test caught them:

    It returns **`(z, owner)`**, not `z`. `float()` on the pair raises; worse, an
    agent who indexes `[0]` without reading the docstring gets the right answer
    for the wrong reason and never learns the second thing.

    **`z` is NaN wherever TERRAIN owns the ground.** The contract is analytic for
    the racing surface, the access ribbon, the runoff platform and the declared
    apron; outside those, the height lives in `build_terrain`'s mesh and there is
    no closed form. NaN is the contract saying "ask the terrain", and it is not a
    number you may seat an object on: `nan - 0.020` is `nan`, an object at z=nan
    vanishes from the render, and nothing downstream would say why. So this
    refuses by default and tells you whose mesh to ask.

    Scalar in, scalar out; arrays in, arrays out.
    """
    z, own = C.world_ground_z(x, y)
    if np.ndim(z) == 0:
        if np.isnan(z) and not allow_terrain:
            raise ValueError(
                "world_ground_z(%.3f, %.3f) is NaN: TERRAIN owns the ground "
                "there (owner %r), so the contract has no closed form and this "
                "refuses to invent one. Sample build_terrain's mesh, or move "
                "the item onto surface/apron/platform, or pass "
                "allow_terrain=True and handle the NaN yourself."
                % (float(x), float(y), own))
        return float(z)
    z = np.asarray(z, float)
    if not allow_terrain and np.isnan(z).any():
        n = int(np.isnan(z).sum())
        raise ValueError(
            "%d of %d sample points are NaN: TERRAIN owns the ground there and "
            "the contract has no closed form. Owners present: %s."
            % (n, z.size, sorted(set(np.asarray(own).ravel().tolist()))))
    return z


def ground_owner(x, y):
    """Which module's mesh is actually the ground at (x, y)."""
    return C.world_ground_z(x, y)[1]


def seat_on_ground(x, y, base_local_z=0.0, embed_m=None):
    """The z an object's ORIGIN needs so its base embeds >= BASE_EMBED_M.

    `base_local_z` is the object's own lowest point in its local frame — which,
    after `new_mesh(recentre=True)`, is negative. Law 5 in one call, with the
    contract's number, so no module has to re-type 0.020 and none of them can
    quietly disagree with it. (One wave-1 module does: `timing_stand` uses
    0.022, documented and deliberately stricter. That is fine — `embed_m`
    exists for it — but it should be a stated choice, not a stray literal.)
    """
    e = float(C.BASE_EMBED_M if embed_m is None else embed_m)
    if e < C.BASE_EMBED_M:
        raise ValueError(
            "seat_on_ground: embed_m=%.4f is below the contract's floor "
            "BASE_EMBED_M=%.4f. Deeper is a choice; shallower is a floating "
            "object at a 12.5 deg sun." % (e, C.BASE_EMBED_M))
    return ground_z(x, y) - float(base_local_z) - e


def ground_plane(prefix, coll_, centre=(0.0, 0.0), span=60.0, res=200,
                 material=None, fill_z=None):
    """A contract-height ground for the item to stand on in its test scene.

    Named with the caller's prefix, and named *Standin* so `item_gate.py`'s
    context filter excludes it from the item's own statistics. That matters: the
    gate's `CONTEXT_PAT` / `CONTEXT_COLL_PAT` drop `standin`/`context`/`ctx`
    objects and sub-collections, and wave 1 had a `CTX_Column` picked as the
    subject to frame and judge.
    """
    _require_bpy("ground_plane")
    n = int(res)
    xs = np.linspace(centre[0] - span * 0.5, centre[0] + span * 0.5, n)
    ys = np.linspace(centre[1] - span * 0.5, centre[1] + span * 0.5, n)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    # `world_ground_z` is already vectorised. It returns NaN where terrain owns
    # the ground; a standin plane may legitimately reach out that far, so this
    # takes an explicit `fill_z` rather than inventing one -- and refuses if the
    # caller has not said what to do.
    Z = ground_z(X.ravel(), Y.ravel(), allow_terrain=True).reshape(X.shape)
    nan = np.isnan(Z)
    if nan.any():
        if fill_z is None:
            raise ValueError(
                "ground_plane: %d of %d sample points (%.1f %%) fall where "
                "TERRAIN owns the ground, so world_contract has no height for "
                "them. Shrink `span`, move `centre`, or pass fill_z=<metres> "
                "as a deliberate stated choice. A standin ground at an invented "
                "height is a contact shadow in the wrong place."
                % (int(nan.sum()), Z.size, 100.0 * nan.mean()))
        Z = np.where(nan, float(fill_z), Z)
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    idx = np.arange(n * n).reshape(n, n)
    q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], axis=1)
    me, off = new_mesh(prefix + "Standin_Ground", V, quads=q, smooth_deg=None,
                       recentre=True)
    ob = bpy.data.objects.new(prefix + "Standin_Ground", me)
    ob.location = off
    if material is not None:
        ob.data.materials.append(material)
    coll_.objects.link(ob)
    return ob


# ===========================================================================
# 8.  THE BRAND BOOK — one book, 31 brands, Law 2
# ===========================================================================

_BRANDS_CACHE = None


def brands():
    """`build_dressing.BRANDS`: (name, bg_hex, fg_hex, mark, tier, tracking,
    strapline) x 31. Imported if bpy is available, otherwise read from source.

    Law 2 says reuse these and never invent a 32nd. Wave 1 obeyed the spirit and
    broke the letter six times over: two modules each declared a `BRAND_BOOK` of
    12 entries and the two subsets DIFFER, one declared a dict, one pre-converted
    the colours to linear, one kept only the names, one kept 17 names as
    `SPONSORS`, and one read `build_dressing.py` as text to dodge the bpy import.
    Six partial copies of a 31-row table is how a world's identity fragments.
    """
    global _BRANDS_CACHE
    if _BRANDS_CACHE is not None:
        return _BRANDS_CACHE
    try:
        import build_dressing as D                       # needs bpy
        _BRANDS_CACHE = list(D.BRANDS)
        return _BRANDS_CACHE
    except Exception:                                    # noqa: BLE001
        pass
    # Source read, no import: `build_dressing` pulls in bpy and numpy at module
    # scope and this must stay usable from a plain python3 selftest.
    src = open(os.path.join(_HERE, "build_dressing.py"), "r",
               encoding="utf-8").read()
    i = src.index("\nBRANDS = [")
    j = src.index("\n]", i)
    ns = {}
    exec(compile(src[i + 1:j + 2], "build_dressing.BRANDS", "exec"), ns)  # noqa: S102
    _BRANDS_CACHE = list(ns["BRANDS"])
    return _BRANDS_CACHE


def brand(name):
    for b in brands():
        if b[0] == name:
            return b
    raise KeyError(
        "'%s' is not one of the %d invented brands. Law 2: inventing a 32nd "
        "fragments the world's identity. Pick from: %s"
        % (name, len(brands()), ", ".join(b[0] for b in brands())))


def pick_brand(*keys):
    """A brand chosen deterministically from `keys`, weighted by commercial tier.

    Tier is how much board space a brand buys, and weighting by it is what makes
    the distribution read as a sales sheet rather than as uniform noise.
    """
    bs = brands()
    w = np.array([{1: 0.6, 2: 1.0, 3: 1.7, 4: 2.6, 5: 1.2}[b[4]] for b in bs])
    cdf = np.cumsum(w) / w.sum()
    return bs[int(np.searchsorted(cdf, hash01(*keys)))]


# ===========================================================================
# 9.  HANDBACK — the interface file, and the cheap law-1 check
# ===========================================================================

def assert_no_external_assets():
    """Law 1, checked locally and for free before a GPU job is ever queued.

    The gate checks this too. Running it here means the answer arrives in
    milliseconds instead of after a render, and the failure names the node.
    """
    _require_bpy("assert_no_external_assets")
    bad_imgs = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    bad_nodes = []
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.bl_idname == "ShaderNodeTexImage":
                bad_nodes.append("%s/%s" % (m.name, nd.name))
    for w in bpy.data.worlds:
        if w.use_nodes and w.node_tree:
            for nd in w.node_tree.nodes:
                if nd.bl_idname == "ShaderNodeTexImage":
                    bad_nodes.append("%s/%s" % (w.name, nd.name))
    if bad_imgs or bad_nodes:
        raise RuntimeError(
            "REFUSING: Law 1 -- everything is built by hand. Image files: %s. "
            "Image-texture nodes: %s." % (bad_imgs, bad_nodes))
    return {"external_image_files": 0, "image_texture_nodes": 0}


def interface_json(item, path=None, **fields):
    """What DEPENDANT items are allowed to rely on.

    An item's dependants cannot ask it questions. Whatever profile, material
    name, seating function or station list they build against has to be written
    down or they will re-derive it and drift.
    """
    doc = {"item": item, "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "contract": {"ground_z": "world_contract.world_ground_z(x, y)",
                        "base_embed_m": C.BASE_EMBED_M,
                        "view_transform": C.VIEW_TRANSFORM},
           **fields}
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        json.dump(doc, open(path, "w"), indent=1, default=float)
        log("interface -> %s" % path)
    return doc


def gate_command(item, blend, prefix=None, collection=None, out=None,
                 filmed_distance_m=None, onscreen_px_4k=None):
    """The exact acceptance command for this item. Prints `--collection`.

    Deliberately NOT `--prefix`. The gate takes a prefix "as given" and applies
    no standin filter to it, so it is the one selector that can quietly narrow
    the measurement to the objects the author likes. `--collection` is filtered,
    reported, and descends into children while skipping standin/context
    sub-collections. All 28 wave-1 items were re-gated by auto-detection or
    collection with no `--prefix` at all.
    """
    out = out or os.path.join(_ROOT, "render/items", item, "gate.json")
    cmd = ["/opt/blender-5.2.0-linux-x64/blender", "-b", blend,
           "--factory-startup", "-P", os.path.join(_ROOT, "tools/item_gate.py"),
           "--", "--item", item, "--out", out]
    if collection:
        cmd += ["--collection", collection]
    elif prefix:
        cmd += ["--prefix", prefix]
    if filmed_distance_m is not None:
        cmd += ["--filmed-distance-m", "%.4f" % filmed_distance_m]
    if onscreen_px_4k is not None:
        cmd += ["--onscreen-px-4k", "%.1f" % onscreen_px_4k]
    return cmd


def cli(build_fn, item, coll_name, prefix, blend_path=None):
    """The `if __name__ == "__main__"` block, once. 23 of 28 modules wrote one.

    --build       build into the current scene
    --test-scene  build + sun + macro camera + save the test blend
    --selftest    whatever the module's own `selftest` asserts
    """
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=item)
    p.add_argument("--build", action="store_true")
    p.add_argument("--test-scene", action="store_true")
    p.add_argument("--save", default=blend_path)
    p.add_argument("--samples", type=int, default=256)
    a = p.parse_args(argv)
    _require_bpy("cli")
    root = build_fn(scene=bpy.context.scene, test_scene=a.test_scene,
                    samples=a.samples)
    assert_no_external_assets()
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save, compress=True)
        log("saved %s" % a.save)
    log("gate:  " + " ".join(gate_command(item, a.save or "<blend>",
                                          collection=coll_name)))
    return root


# ===========================================================================
# 10.  SELFTEST — measured, not asserted
# ===========================================================================

def CONTEXT_LIKE(name):
    """Would `item_gate.CONTEXT_PAT` treat this name as a standin? Kept in step
    with the gate by reading the gate's own pattern rather than restating it."""
    import re
    src = open(os.path.join(_ROOT, "tools/item_gate.py"), encoding="utf-8").read()
    i = src.index("CONTEXT_PAT = re.compile(")
    j = src.index(")", src.index("re.I", i))
    ns = {"re": re}
    exec(compile(src[i:j + 1], "item_gate.CONTEXT_PAT", "exec"), ns)  # noqa: S102
    return bool(ns["CONTEXT_PAT"].search(name))


def selftest(verbose=True):
    """Every claim in this file, checked. Pure-python parts run without bpy."""
    out, fails = [], []

    def chk(name, ok, detail):
        out.append((name, bool(ok), detail))
        if not ok:
            fails.append(name)
        if verbose:
            print("  %-34s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))

    # [0] EVERY INDEX THIS FILE PINS, CHECKED AGAINST THE LIVE SOCKET.
    #
    #     Blender 5.2 inserted `Filter Width` at index 2 of ShaderNodeBump and
    #     nothing noticed: `bump()` wired height into the filter, the normal
    #     chain into Height, and left the first bump of every chain on a
    #     constant with zero gradient — no relief, in the kit every wave-2 item
    #     is built on. It rendered, and it passed the gate, because a node count
    #     cannot see a dead socket.
    #
    #     A version bump must now FAIL HERE rather than quietly flatten 407
    #     items. Costs milliseconds and needs no render.
    try:
        import bpy as _bpy
        _m = _bpy.data.materials.new("_itemkit_socket_audit")
        _m.use_nodes = True
        _T = _m.node_tree
        # (node type, kwargs, {index: the socket name this file assumes})
        _ASSUME = [
            ("ShaderNodeMix", {"data_type": "RGBA"}, {0: "Factor", 6: "A", 7: "B"}),
            ("ShaderNodeMix", {"data_type": "FLOAT"}, {0: "Factor", 2: "A", 3: "B"}),
            ("ShaderNodeMath", {}, {0: "Value", 1: "Value"}),
            ("ShaderNodeVectorMath", {}, {0: "Vector", 1: "Vector", 3: "Scale"}),
            ("ShaderNodeTexNoise", {}, {0: "Vector", 2: "Scale", 3: "Detail",
                                        4: "Roughness", 5: "Lacunarity"}),
            ("ShaderNodeTexVoronoi", {}, {0: "Vector", 2: "Scale", 8: "Randomness"}),
            ("ShaderNodeTexWave", {}, {0: "Vector", 1: "Scale",
                                       2: "Distortion", 3: "Detail"}),
            ("ShaderNodeMapRange", {}, {0: "Value", 1: "From Min", 2: "From Max",
                                        3: "To Min", 4: "To Max"}),
            ("ShaderNodeSeparateXYZ", {}, {0: "Vector"}),
            ("ShaderNodeCombineXYZ", {}, {0: "X", 1: "Y", 2: "Z"}),
        ]
        _bad = []
        for _typ, _kw, _exp in _ASSUME:
            _nd = _T.nodes.new(_typ)
            for _k, _v in _kw.items():
                setattr(_nd, _k, _v)
            for _i, _want in sorted(_exp.items()):
                _got = (_nd.inputs[_i].name if _i < len(_nd.inputs)
                        else "<out of range>")
                if _got != _want:
                    _bad.append("%s[%d] is %r not %r" % (_typ, _i, _got, _want))
            _T.nodes.remove(_nd)
        # Bump is wired BY NAME now, so assert the names exist rather than
        # their positions — that is the whole point of the fix.
        _nd = _T.nodes.new("ShaderNodeBump")
        _names = [s.name for s in _nd.inputs]
        for _want in ("Strength", "Distance", "Height", "Normal"):
            if _want not in _names:
                _bad.append("ShaderNodeBump has no %r socket" % _want)
        if _names[2] == "Height":
            _bad.append("ShaderNodeBump[2] is 'Height' again — this Blender "
                        "predates the 5.2 Filter Width insert; re-check bump()")
        _T.nodes.remove(_nd)
        _bpy.data.materials.remove(_m)
        chk("socket_indices_match_live_blender", not _bad,
            "all %d index assumptions hold" % sum(len(e) for _, _, e in _ASSUME)
            if not _bad else "; ".join(_bad))
    except ImportError:
        pass

    # [1] hash01 AVALANCHE. The bug this replaces produced identical outputs for
    #     keys differing in their low bits; measure the bit-flip rate.
    flips = []
    for seed in range(64):
        for bit in range(20):
            a = int(hash01(seed, 1234) * (1 << 30))
            b = int(hash01(seed, 1234 ^ (1 << bit)) * (1 << 30))
            flips.append(bin(a ^ b).count("1") / 30.0)
    av = float(np.mean(flips))
    chk("hash01_avalanche", 0.40 <= av <= 0.60,
        "mean output bit-flip for a 1-bit key change = %.4f (want ~0.5)" % av)

    # [2] the EXACT collision the docstring records.
    vals = [hash01(9001, k) for k in (3, 5, 7)]
    chk("hash01_no_low_bit_collision", len(set(vals)) == 3,
        "hash01(9001, 3/5/7) = %s" % ["%.5f" % v for v in vals])

    # [3] the naive form, for contrast -- proves the test can fail.
    def naive(*keys):
        h = 1469598103934665603
        for k in keys:
            h ^= int(k) & 0xFFFFFFFFFFFFFFFF
            h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return float(h % (1 << 30)) / float(1 << 30)
    nf = []
    for seed in range(64):
        for bit in range(20):
            a = int(naive(seed, 1234) * (1 << 30))
            b = int(naive(seed, 1234 ^ (1 << bit)) * (1 << 30))
            nf.append(bin(a ^ b).count("1") / 30.0)
    nav = float(np.mean(nf))
    chk("hash01_control_naive_is_worse", nav < av - 0.05,
        "the unfinalised FNV form flips %.4f of output bits vs %.4f -- the "
        "test discriminates" % (nav, av))

    # [4] the pixel budget reproduces the brief's worked examples.
    a1 = px_per_m(0.8, 21.0)
    a2 = px_per_m(2.6, 35.0)
    chk("px_per_m_matches_brief", abs(a1 - 2800.0) < 1.0 and abs(a2 - 1436.0) < 1.0,
        "kerb_hero_t4 0.8 m/21 mm = %.1f px/m (brief: 2800); armco 2.6 m/35 mm "
        "= %.1f (brief: 1436)" % (a1, a2))

    # [5] the resolution this kit renders at is the resolution the gate scores.
    gsrc = open(os.path.join(_ROOT, "tools/item_gate.py"), encoding="utf-8").read()
    gx = int([l for l in gsrc.splitlines()
              if l.startswith("RES_X_4K")][0].split("=")[1])
    chk("resolution_matches_gate", gx == RES_X_4K,
        "item_gate.RES_X_4K = %d, itemkit.RES_X_4K = %d" % (gx, RES_X_4K))

    # [6] chunk_spans respects Law 7 for every length in the campaign's range.
    bad = []
    for total in range(60, 3000, 7):
        try:
            sp = chunk_spans(0.0, float(total))
        except ValueError:
            if total > 260:
                bad.append(("refused", total))
            continue
        for s0, s1 in sp:
            if total > 260 and not (80.0 - 1e-9 <= s1 - s0 <= 260.0 + 1e-9):
                bad.append((total, s1 - s0))
    chk("chunk_spans_inside_law7", not bad,
        "every length 60-3000 m splits into 80-260 m spans; %d violations" % len(bad))

    # [7] the brand book is the one book, with all 31.
    bs = brands()
    chk("brand_book_31", len(bs) == 31 and brand("MERIDIAN")[4] == 4,
        "%d brands, MERIDIAN tier %d" % (len(bs), brand("MERIDIAN")[4]))

    # [8] contract numbers are READ, not copied.
    chk("contract_is_live", C.BASE_EMBED_M == 0.020 and abs(C.SUN_ELEV_DEG - 12.47061) < 1e-6,
        "BASE_EMBED_M %.4f, SUN_ELEV_DEG %.5f, SUN_ENERGY %.3f"
        % (C.BASE_EMBED_M, C.SUN_ELEV_DEG, C.SUN_ENERGY))

    # [9] seat_on_ground refuses a shallower embed than the contract's floor.
    try:
        seat_on_ground(0.0, 0.0, -0.5, embed_m=0.001)
        ok = False
    except ValueError:
        ok = True
    chk("seat_refuses_shallow_embed", ok,
        "embed_m=0.001 below BASE_EMBED_M=%.3f is refused" % C.BASE_EMBED_M)

    # [10] ground_z unpacks (z, owner) and the seat arithmetic is right.
    #      This exists because writing it wrong is easy and silent: the first
    #      version of `ground_z` in this file did `float(C.world_ground_z(...))`
    #      on a PAIR, and no test caught it until a smoke test tried to build a
    #      ground plane.
    z_track = ground_z(100.0, 0.0)
    own = ground_owner(100.0, 0.0)
    seat = seat_on_ground(100.0, 0.0, base_local_z=-0.5)
    embed = z_track - (seat - 0.5)
    chk("ground_z_and_seat", abs(embed - C.BASE_EMBED_M) < 1e-9,
        "ground %.5f m (owner %s); an object whose base sits 0.500 below its "
        "origin seats at %.5f, embedding %.4f m" % (z_track, own, seat, embed))

    # [11] and it REFUSES where terrain owns the ground, instead of returning
    #      NaN. nan - 0.020 is nan, and an object at z=nan vanishes silently.
    raw = C.world_ground_z(0.0, 300.0)
    try:
        ground_z(0.0, 300.0)
        ok = False
    except ValueError:
        ok = True
    chk("ground_z_refuses_nan", ok and math.isnan(raw[0]),
        "world_ground_z(0, 300) = (nan, %r) and ground_z refuses it; "
        "allow_terrain=True returns the NaN for a caller who handles it" % raw[1])

    # [12] WINDING. The positive control is an inside-out surface built HERE,
    #      and the negative control is the same surface built correctly. BOTH
    #      SIDES ARE BOUND: a check that flips everything it is shown would pass
    #      a positive control and destroy every module it touched. That is the
    #      100 mm of sunken paving lesson -- a bound that catches "too proud"
    #      and never "too sunken" saw nothing.
    Vg, Qg = _ctl_sphere()
    r_out = winding_audit(Vg, quads=Qg.copy())
    Qr = Qg[:, ::-1].copy()
    r_in = winding_audit(Vg, quads=Qr.copy())
    Qfix = Qr.copy()
    r_fix = winding_audit(Vg, quads=Qfix, apply=True)
    r_after = winding_audit(Vg, quads=Qfix)
    chk("winding_catches_inside_out",
        r_out["inward"] == 0 and r_in["inward"] == 1
        and r_fix["flipped"] == 1 and r_after["inward"] == 0,
        "outward sphere vol %+.4f n.r %+.3f -> %d inward (want 0); the SAME "
        "sphere reversed vol %+.4f n.r %+.3f -> %d inward (want 1), repaired "
        "to %d" % (r_out["vol"][0], r_out["nrad"][0], r_out["inward"],
                   r_in["vol"][0], r_in["nrad"][0], r_in["inward"],
                   r_after["inward"]))

    # [13] and it does NOT touch a correct one. The other side of the bound.
    Qkeep = Qg.copy()
    r_keep = winding_audit(Vg, quads=Qkeep, apply=True)
    chk("winding_leaves_outward_alone",
        r_keep["flipped"] == 0 and np.array_equal(Qkeep, Qg),
        "a correctly wound sphere is returned bit-identical: %d flipped, "
        "%d/%d faces unchanged" % (r_keep["flipped"],
                                   int((Qkeep == Qg).all(axis=1).sum()), len(Qg)))

    # [14] AN OPEN PIECE IS DECIDED, NOT ABSTAINED ON. This is the case that
    #      broke the first version of the method in humankit: mean(n.radial)
    #      with a deadband abstained on 13 pieces over 8 figures, including
    #      every trouser head, and "a fallback that decides nothing" is R2-019's
    #      defect in a new hat. Capping the boundary loops removes the choice.
    Vt, Qt = _ctl_tube()
    t_out = winding_audit(Vt, quads=Qt.copy())
    t_in = winding_audit(Vt, quads=Qt[:, ::-1].copy())
    chk("winding_decides_open_pieces",
        t_out["boundary_edges"] == 40 and t_out["inward"] == 0
        and t_in["inward"] == 1,
        "an OPEN tube (%d boundary edges, 2 loops) is decided by capping: "
        "outward vol %+.4f -> %d inward, reversed vol %+.4f -> %d inward"
        % (t_out["boundary_edges"], t_out["vol"][0], t_out["inward"],
           t_in["vol"][0], t_in["inward"]))

    # [15] TWO INDEPENDENT STATISTICS, and they agree on every piece. Signed
    #      volume decides; area-weighted mean(unit normal . unit radial) is
    #      written from different arithmetic and must never disagree.
    V1, Q1 = _ctl_sphere(centre=(0.0, 0.0, 0.0))
    V2, Q2 = _ctl_sphere(centre=(4.0, 0.0, 0.0), reverse=True)
    V3, Q3 = _ctl_tube(centre=(-4.0, 0.0, 0.0), reverse=True)
    Vm = np.concatenate([V1, V2, V3])
    Qm = np.concatenate([Q1, Q2 + len(V1), Q3 + len(V1) + len(V2)])
    rm = winding_audit(Vm, quads=Qm.copy())
    chk("winding_two_statistics_agree",
        rm["pieces"] == 3 and rm["inward"] == 2 and rm["statistics_agree"]
        and list(np.sign(rm["vol"])) == list(np.sign(rm["nrad"])),
        "3 pieces (closed, closed-reversed, open-reversed): vol %s, "
        "n.radial %s -- signs identical, %d inward"
        % ([round(v, 3) for v in rm["vol"]],
           [round(v, 3) for v in rm["nrad"]], rm["inward"]))

    # [16] A MIRRORED PIECE IS REVERSED BY CONSTRUCTION. This is the idiom the
    #      whole audit exists for: `V[:, 0] *= -1` on a correct piece produces a
    #      correct-looking model that renders inside-out, and nothing else in
    #      this file would notice.
    Vmir = V1.copy(); Vmir[:, 0] *= -1.0
    r_mir = winding_audit(Vmir, quads=Q1.copy())
    chk("winding_catches_axis_mirror", r_mir["inward"] == 1,
        "mirroring x on a correctly wound sphere reverses it: vol %+.4f, "
        "n.radial %+.3f, %d inward -- the defect arrives through the front door"
        % (r_mir["vol"][0], r_mir["nrad"][0], r_mir["inward"]))

    # [17] A SHEET HAS NO INSIDE. A lone one is reported UNDECIDABLE and left
    #      alone; one that belongs to a body is decided by which way it faces.
    #      This is the case that made the first version of the audit call
    #      `asphalt_wearing_course` "100 % inward" off a capped volume of
    #      essentially nothing -- an exact method applied where its input means
    #      nothing.
    Vp = np.array([[0.0, 0.0, 2.0], [1.0, 0.0, 2.0],
                   [1.0, 1.0, 2.0], [0.0, 1.0, 2.0]])
    Qp = np.array([[0, 1, 2, 3]], np.int64)
    r_lone = winding_audit(Vp, quads=Qp.copy(), apply=True)
    Vf = np.concatenate([V1, Vp]); Qf = np.concatenate([Q1, Qp + len(V1)])
    rf = winding_audit(Vf, quads=Qf.copy())
    Vsheet, Qsheet = _ctl_sin_grid(n=48, span=60.0, lam=8.0, amp_mm=60.0)
    r_slab = winding_audit(Vsheet, quads=Qsheet.copy(), apply=True)
    chk("winding_leaves_undecidable_sheets_alone",
        r_lone["undecidable"] == 1 and r_lone["flipped"] == 0
        and rf["pieces"] == 2 and rf["sheet_pieces"] == 1
        and rf["undecidable"] == 0
        and r_slab["undecidable"] == 1 and r_slab["flipped"] == 0,
        "a lone 1 m plate: Q %.2e -> undecidable, %d flipped; the SAME plate "
        "beside a sphere is decided by facing-away (%d undecidable); a 60 m "
        "road-slab sheet: Q %.2e -> undecidable, %d flipped (a closed shell is "
        "Q ~ 0.094)" % (r_lone["enclosure_q"][0], r_lone["flipped"],
                        rf["undecidable"], r_slab["enclosure_q"][0],
                        r_slab["flipped"]))

    # [18] INCONSISTENT WINDING WITHIN ONE PIECE -- the fault signed volume
    #      cannot see, because reversing half a shell can leave the sum near
    #      anything. Bounded separately, because both faults are wrong.
    Qbad = Qg.copy(); Qbad[::2] = Qbad[::2][:, ::-1]
    rb = winding_audit(Vg, quads=Qbad)
    chk("winding_detects_inconsistent_piece",
        rb["inconsistent_edge_pairs"] > 0 and r_out["inconsistent_edge_pairs"] == 0,
        "half the sphere's quads reversed: %d interior edges traversed the same "
        "way by both faces (a consistent sphere has %d)"
        % (rb["inconsistent_edge_pairs"], r_out["inconsistent_edge_pairs"]))

    # [19] THE RELIEF LAW, AND THE AMPLIFIER IS DERIVED. If the sun moves the
    #      amplifier moves with it; 4.5x is a consequence of 12.47 deg, not a
    #      constant. Checked by asking the same question at a different sun.
    amp_film = sun_amplifier()
    amp_noon = sun_amplifier(45.0)
    m_at_10deg = modulation_for_slope(10.4)
    round_trip = modulation_for_amplitude(
        relief_amplitude_for(0.28, 0.008), 0.008)
    chk("relief_law_derives_the_amplifier",
        abs(amp_film - 4.52) < 0.02 and abs(amp_noon - 1.0) < 1e-9
        and abs(m_at_10deg - 1.66) < 0.04 and abs(round_trip - 0.28) < 1e-6,
        "sun %.4f deg -> amplifier %.3fx (45 deg would be %.3fx); the rejected "
        "10.4 deg set = m %.3f (recorded 1.66); 0.28 pp -> %.4f mm at 8 mm -> "
        "%.4f pp round trip" % (sun_elev_deg(), amp_film, amp_noon, m_at_10deg,
                                relief_amplitude_for(0.28, 0.008), round_trip))

    # [20] and the law REPRODUCES THE HUMAN-FIGURE RECORD, which is the only
    #      ladder it has that was JUDGED BY EYE. Positive control: the sets that
    #      were rejected must come out where the record says they did.
    #      The record was tabulated with 2 tan(th)/tan(e) and this file uses the
    #      exact 2 sin(th)/tan(e); the check requires the two to agree to 2 % in
    #      the whole accepted/near-accepted range and states the divergence at
    #      the far end rather than hiding it in a loose tolerance.
    ladder = [("shipped", 5.0, 0.79), ("second fix", 10.4, 1.66),
              ("accepted", 1.8, 0.28), ("fold field", 14.4, 2.32)]
    rel = [(n, modulation_for_slope(s) / m - 1.0) for n, s, m in ladder]
    far = modulation_for_slope(22.6) / 3.76 - 1.0        # the stucco set
    fold = modulation_for_amplitude(8.2, 0.100)          # geometry, second layer
    chk("relief_law_matches_the_rejected_ladder",
        all(abs(d) < 0.032 for _, d in rel) and abs(fold - 2.25) < 0.03,
        "every judged set reproduces within %.1f %% (%s); the far end, the "
        "22.6 deg stucco, differs by %+.1f %% because the record used tan and "
        "this uses sin -- both are 'rejected'. The fold field's 8.2 mm at a "
        "100 mm flute = m %.3f, the SECOND layer, recorded 2.32"
        % (100 * max(abs(d) for _, d in rel),
           ", ".join("%s %+.1f%%" % (n, 100 * d) for n, d in rel),
           100 * far, fold))

    # [21] AMPLITUDE ALONE MEANS NOTHING, which is why the helper demands a
    #      wavelength. The negative control for the whole idea.
    m8 = modulation_for_amplitude(0.5, 0.008)
    m100 = modulation_for_amplitude(0.5, 0.100)
    chk("relief_needs_a_wavelength", m8 / m100 > 10.0,
        "the SAME 0.5 mm is m %.3f at an 8 mm wavelength and m %.3f at a "
        "100 mm one -- a factor of %.1f, which is why millimetres are not a "
        "relief spec" % (m8, m100, m8 / m100))

    # [22] and the band table catches BOTH ends. A bound that only catches
    #      "too much" is how 100 mm of sunken paving went unseen.
    rows = relief_budget([("too_flat", 0.008, 0.02),
                          ("right", 0.008, relief_amplitude_for(0.28, 0.008)),
                          ("felt", 0.008, relief_amplitude_for(1.66, 0.008))],
                         band="isotropic_micro", verbose=False)
    chk("relief_budget_bounds_both_sides",
        [r["verdict"] for r in rows] == ["LOW", "ok", "HIGH"],
        "0.02 mm -> m %.3f LOW, %.3f mm -> m %.3f ok, %.3f mm -> m %.3f HIGH"
        % (rows[0]["m"], rows[1]["amp_mm"], rows[1]["m"],
           rows[2]["amp_mm"], rows[2]["m"]))

    # ---- the bpy half ---------------------------------------------------
    if not HAVE_BPY:
        chk("bpy_half", True, "skipped -- not running inside Blender")
    else:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        sc = bpy.context.scene

        # [10] the sun emits DOWNWARD (R2-021).
        from mathutils import Vector
        sun = contract_sun("IKT_", scene=sc, coll_=sc.collection)
        e = sun.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        chk("sun_emits_downward", e.z < -0.05,
            "emit (%.4f, %.4f, %.4f); lamp energy %.3f"
            % (e.x, e.y, e.z, sun.data.energy))

        # [10b] R2-059. THE GRADE contract_sun LEAVES ON THE SCENE IS THE
        #       FILM'S MEASURED ONE, NOT THE CONTRACT'S DERIVED ONE.
        #       This helper set C.REFERENCE_EXPOSURE_EXTERIOR = -3.048 for the
        #       whole item campaign, which is 0.580 stops OVER the measured
        #       -3.628, so every frame judged through it was bright by that
        #       much. The check reads the live scene rather than the constant,
        #       and it names the refuted number so a regression is legible
        #       rather than a bare number mismatch.
        import film_exposure as FX
        got_ev = float(sc.view_settings.exposure)
        over = C.REFERENCE_EXPOSURE_EXTERIOR - FX.FILM_EXPOSURE
        chk("contract_sun_grades_at_the_measured_exposure",
            abs(got_ev - FX.FILM_EXPOSURE) < 1e-4
            and abs(got_ev - C.REFERENCE_EXPOSURE_EXTERIOR) > 0.5
            and sc.view_settings.view_transform == C.VIEW_TRANSFORM,
            "the live scene reads %+.4f EV = film_exposure.FILM_EXPOSURE "
            "(MEASURED, 0.006 stops against an 18 %% card); the contract's "
            "DERIVED and refuted REFERENCE_EXPOSURE_EXTERIOR is %+.4f, which "
            "is %+.3f stops over and is what this helper used to set; "
            "view transform %s look %s"
            % (got_ev, C.REFERENCE_EXPOSURE_EXTERIOR, over,
               sc.view_settings.view_transform, C.VIEW_LOOK))

        # [11] and the refusal is REACHABLE -- flip it and confirm it fires.
        sun.rotation_quaternion = Vector(C.SUN_DIR).to_track_quat("-Z", "Y")
        bpy.context.view_layer.update()
        e2 = sun.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        chk("upward_sun_is_detectable", e2.z > -0.05,
            "the exact R2-021 form (-d).to_track_quat('Z','Y') emits z %+.4f, "
            "which the guard rejects" % e2.z)
        bpy.data.objects.remove(sun, do_unlink=True)

        # [12] macro_rig REFUSES 1080p unless named (R2-020).
        cams = coll("IKT_Cams")
        try:
            macro_rig("IKT_bad", (0, -3, 1), (0, 0, 1), 35.0, cams,
                      resolution=(1920, 1080))
            ok = False
            why = "it accepted 1920x1080 for the deliverable"
        except ValueError as exc:
            ok = "R2-020" in str(exc)
            why = "refused: " + str(exc).split(".")[0]
        chk("macro_rig_refuses_1080p", ok, why)

        # [13] and delivers 4K by default.
        cam, dist, ppm = macro_rig("IKT_good", (0, -3, 1), (0, 0, 1), 35.0, cams)
        chk("macro_rig_delivers_4k",
            (sc.render.resolution_x, sc.render.resolution_y) == (RES_X_4K, RES_Y_4K),
            "scene renders %dx%d, camera %.4f m -> %.1f px/m"
            % (sc.render.resolution_x, sc.render.resolution_y, dist, ppm))

        # [14] and refuses a camera at the wrong distance.
        try:
            macro_rig("IKT_far", (0, -9, 1), (0, 0, 1), 35.0, cams,
                      want_distance_m=3.0)
            ok = False
        except RuntimeError:
            ok = True
        chk("macro_rig_checks_distance", ok,
            "a camera 9 m out declared as 3.0 m is refused")

        # [15] new_mesh recentres, so TexCoord->Object stays near the origin.
        far = np.array([[1000.0, 1000.0, 0.0], [1001.0, 1000.0, 0.0],
                        [1001.0, 1001.0, 0.0], [1000.0, 1001.0, 0.0]])
        me, off = new_mesh("IKT_far_mesh", far, quads=[[0, 1, 2, 3]])
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        chk("new_mesh_recentres", float(np.abs(co).max()) < 1.0,
            "vertices at |P| ~ 1414 m emit at |P| max %.4f m, origin offset %s"
            % (float(np.abs(co).max()), tuple(round(v, 1) for v in off)))

        # [16] the node DSL offers Object coords and NOT world Position.
        nt = NT("IKT_mat")
        nd, sock = nt.object_coords()
        chk("node_dsl_object_addressing",
            nd.bl_idname == "ShaderNodeTexCoord" and sock == 3
            and not hasattr(NT, "position"),
            "object_coords() -> %s socket %d ('%s'); NT has no position()"
            % (nd.bl_idname, sock, nd.outputs[sock].name))

        # [17] bake_attributes round-trips (materials read these).
        me2, _ = new_mesh("IKT_attr", [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
                          quads=[[0, 1, 2, 3]])
        bake_attributes(me2, {"ikt_w": np.array([0.1, 0.2, 0.3, 0.4])})
        buf = np.empty(4, np.float32)
        me2.attributes["ikt_w"].data.foreach_get("value", buf)
        chk("bake_attributes_round_trip", np.allclose(buf, [0.1, 0.2, 0.3, 0.4]),
            "wrote [0.1 0.2 0.3 0.4], read back %s" % buf.round(3))

        # [18] a full graph wires to the surface output and counts as the gate does.
        n1 = nt.noise(nt.object_coords(), 40.0)
        n2 = nt.vor(nt.object_coords(), 12.0)
        n3 = nt.wave(nt.object_coords(), 8.0)
        nt.principled_out(
            base_color=nt.ramp(n1, [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.6, 0.6, 0.6))]),
            roughness=n2, normal=nt.bump(n3, 0.4, 0.002))
        wired = any(l.to_node.bl_idname == "ShaderNodeOutputMaterial"
                    for l in nt.t.links)
        chk("principled_out_wired", wired and nt.texture_node_count() >= 3,
            "%d nodes, %d links, %d procedural texture nodes (gate floor 6 hero)"
            % (len(nt.t.nodes), len(nt.t.links), nt.texture_node_count()))

        # [19] ground_plane sits at the contract height and is named so the gate
        #      excludes it -- and REFUSES rather than inventing a height where
        #      terrain owns the ground.
        gp = ground_plane("IKT_", coll("IKT_Stand"), centre=(100.0, 0.0),
                          span=20.0, res=30)
        zz = np.empty(len(gp.data.vertices) * 3, np.float32)
        gp.data.vertices.foreach_get("co", zz)
        zw = zz.reshape(-1, 3)[:, 2] + gp.location.z
        near = abs(float(zw.mean()) - ground_z(100.0, 0.0)) < 0.10
        try:
            ground_plane("IKT2_", coll("IKT_Stand"), centre=(0.0, 300.0), span=20.0)
            refused = False
        except ValueError:
            refused = True
        chk("ground_plane_contract_height_and_refusal",
            near and refused and CONTEXT_LIKE(gp.name),
            "mean world z %.4f vs contract %.4f; name %r reads as a standin; "
            "refuses over terrain" % (zw.mean(), ground_z(100.0, 0.0), gp.name))

        # [20] the law-1 check fires on a planted image-texture node.
        nt.n("ShaderNodeTexImage")
        try:
            assert_no_external_assets()
            ok = False
        except RuntimeError:
            ok = True
        chk("law1_catches_image_node", ok,
            "a planted ShaderNodeTexImage is caught before any render")

        # [21] new_mesh ORIENTS BY DEFAULT, and the proof is the built mesh's
        #      own polygon normals, not the array that went in.
        Vs, Qs = _ctl_sphere(reverse=True)
        me3, _ = new_mesh("IKT_wind_on", Vs.copy(), quads=Qs.copy())
        nrm = np.empty(len(me3.polygons) * 3, np.float32)
        me3.polygons.foreach_get("normal", nrm)
        cen = np.empty(len(me3.polygons) * 3, np.float32)
        me3.polygons.foreach_get("center", cen)
        out_frac = float(np.mean(np.einsum(
            "ij,ij->i", nrm.reshape(-1, 3), cen.reshape(-1, 3)) > 0.0))
        me4, _ = new_mesh("IKT_wind_off", Vs.copy(), quads=Qs.copy(),
                          orient=False)
        nrm2 = np.empty(len(me4.polygons) * 3, np.float32)
        me4.polygons.foreach_get("normal", nrm2)
        cen2 = np.empty(len(me4.polygons) * 3, np.float32)
        me4.polygons.foreach_get("center", cen2)
        off_frac = float(np.mean(np.einsum(
            "ij,ij->i", nrm2.reshape(-1, 3), cen2.reshape(-1, 3)) > 0.0))
        chk("new_mesh_orients_outward_by_default",
            out_frac > 0.999 and off_frac < 0.001,
            "an inside-out sphere through new_mesh() emits %.1f %% outward-"
            "facing polygons; the SAME array with orient=False emits %.1f %% -- "
            "the default is doing the work, and the escape hatch still exists"
            % (100 * out_frac, 100 * off_frac))

        # [22] and a mesh that is ALREADY BUILT can be audited and repaired,
        #      which is how 28 wave-1 modules get checked without re-running 28
        #      builders. The control is the same self-built fault.
        r_be = mesh_winding_report(me4)
        r_ap = mesh_winding_report(me4, apply=True)
        r_af = mesh_winding_report(me4)
        chk("mesh_winding_report_repairs_a_built_mesh",
            r_be["inward"] == 1 and r_ap["flipped"] == 1 and r_af["inward"] == 0,
            "the un-oriented datablock reports %d inward piece (vol %+.4f, "
            "n.radial %+.3f), repairs in place, and re-reports %d"
            % (r_be["inward"], r_be["vol"][0], r_be["nrad"][0], r_af["inward"]))

        # [23] THE RENDER-FACING STATISTIC. Signed volume measures the model;
        #      this casts rays and counts back faces, which is what a viewer
        #      gets. Both directions bound: the broken sphere must read ~100 %
        #      back-facing and the repaired one ~0 %.
        for o in list(bpy.data.objects):
            if o.name.startswith("IKT_io"):
                bpy.data.objects.remove(o, do_unlink=True)
        # SIXTEENTH TIME THE INSTRUMENT WAS THE BROKEN THING. This check first
        # read 6.4 % on a control the datablock proved was 6144/6144 outward,
        # and the tempting explanation -- "a coarse polyhedron has a
        # silhouette-facet floor" -- was PLAUSIBLE, WRONG, and would have been
        # written into the bar as a tolerance. Refining the control 16x moved it
        # to 5.2 %, which is what killed the theory: a facet floor would have
        # fallen. It was `scene.ray_cast` reading the depsgraph's stale
        # evaluated copy. Casting against the arrays this file reads itself
        # gives 0.0 %, and the bar is set where a real floor would still show.
        Vb, Qb = _ctl_sphere(nu=96, nv=64, reverse=True)
        meb, offb = new_mesh("IKT_io_bad", Vb.copy(), quads=Qb.copy(),
                             orient=False)
        obb = bpy.data.objects.new("IKT_io_bad", meb)
        obb.location = offb
        bpy.context.scene.collection.objects.link(obb)
        f_bad = inside_out_fraction([obb], n_rays=400, seed=11)
        mesh_winding_report(meb, apply=True)
        bpy.context.view_layer.update()
        f_good = inside_out_fraction([obb], n_rays=400, seed=11)
        bpy.data.objects.remove(obb, do_unlink=True)
        chk("inside_out_fraction_sees_the_picture",
            f_bad["hits"] > 100 and f_bad["fraction"] > 0.95
            and f_good["fraction"] < 0.04
            and f_good["fraction"] < 0.10 * f_bad["fraction"],
            "%d rays hit the inside-out sphere and %.1f %% landed on a back "
            "face; after repair %.1f %% -- the statistic that measures what "
            "Cycles is handed, not what the array says"
            % (f_bad["hits"], 100 * f_bad["fraction"], 100 * f_good["fraction"]))

        # [24] THE GEOMETRY HALF OF THE AMPLITUDE LAW, CALIBRATED AGAINST A
        #      PHYSICAL LADDER rather than asserted. A sinusoid of known
        #      wavelength and amplitude has a known slope, so the dihedral
        #      estimator can be given a stated conversion instead of a hoped-for
        #      one -- and it must be MONOTONIC in amplitude and near zero on a
        #      flat plate, which is the negative control.
        lam = 0.125
        got = []
        for a_mm in (0.0, 0.5, 2.0, 8.0):
            Vsg, Qsg = _ctl_sin_grid(n=64, span=1.0, lam=lam, amp_mm=a_mm)
            mesg, _ = new_mesh("IKT_sin_%.1f" % a_mm, Vsg, quads=Qsg,
                               smooth_deg=None)
            rr = geometry_relief_report(mesg, bands=((0.010, 0.030),))[0]
            want = modulation_for_amplitude(a_mm, lam)
            got.append((a_mm, rr.get("rms_dihedral_deg", 0.0),
                        rr.get("m", 0.0), want))
        ratios = [g[2] / g[3] for g in got if g[3] > 1e-6]
        mono = all(got[i][2] < got[i + 1][2] for i in range(len(got) - 1))
        spread = (max(ratios) / min(ratios)) if ratios else 99.0
        chk("geometry_relief_calibrated_on_a_ladder",
            got[0][2] < 0.01 and mono and spread < 1.10,
            "0/0.5/2/8 mm at a 125 mm wavelength -> dihedral RMS %s deg, "
            "m %s against the closed form %s; flat reads %.4f, monotonic, and "
            "the estimator/closed-form ratio is %.3f +- %.1f %% across the "
            "ladder (it reads a per-edge slope CHANGE, so it is a fixed "
            "fraction of the peak-to-peak swing, and that fraction is measured "
            "here rather than assumed)"
            % ([round(g[1], 3) for g in got], [round(g[2], 4) for g in got],
               [round(g[3], 4) for g in got], got[0][2],
               float(np.mean(ratios)) if ratios else 0.0,
               100 * (spread - 1.0)))

        # [25] bump(modulation_pp=) puts the DERIVED depth on the live socket,
        #      and refuses an amplitude with no wavelength.
        nt2 = NT("IKT_relief")
        h = nt2.noise(nt2.object_coords(), wavelength_m=0.008)
        nd_b = nt2.bump(h, 1.0, modulation_pp=0.28, wavelength_m=0.008)[0]
        dist = float(nd_b.inputs["Distance"].default_value)
        want_mm = relief_amplitude_for(0.28, 0.008)
        try:
            nt2.bump(h, 1.0, modulation_pp=0.28)
            refused = False
        except ValueError:
            refused = True
        try:
            nt2.bump(h, 1.0, 0.001, modulation_pp=0.28, wavelength_m=0.008)
            both = False
        except ValueError:
            both = True
        rows = bump_relief_report(nt2.t)
        # [25a] R2-038's SIGNATURE, DETECTED, with the fault built here. Pinning
        #       a bump by index on Blender 5.2 puts the height into Filter Width
        #       and the previous stage's NORMAL into Height, so the first bump
        #       of every chain sits on a constant -- zero gradient, no relief --
        #       and the sweep found this pattern in the built blends of 14 of 28
        #       wave-1 modules, 122 stages. The control reproduces the miswiring
        #       verbatim rather than depending on any module staying broken.
        nt3 = NT("IKT_r2038")
        h3 = nt3.noise(nt3.object_coords(), wavelength_m=0.008)
        b1 = nt3.n("ShaderNodeBump")
        b2 = nt3.n("ShaderNodeBump")
        # R2-070: these two MUST stay by index -- they ARE the fault this
        # check detects, reproduced verbatim.  Naming them would turn the
        # positive control into a second negative control.
        nt3.pin(b1, 2, h3)                       # Filter Width  <- the height  # socket-index-audit: waive(R2-038 positive control, must stay by index)
        nt3.pin(b2, 3, (b1, 0))                  # Height        <- the normal  # socket-index-audit: waive(R2-038 positive control, must stay by index)
        bad = bump_relief_report(nt3.t)
        good = bump_relief_report(nt2.t)
        chk("bump_report_detects_the_r2038_miswiring",
            sum(r["height_unlinked"] for r in bad) == 1
            and sum(r["height_driven_by_a_bump"] for r in bad) == 1
            and not any(r["height_unlinked"] or r["height_driven_by_a_bump"]
                        for r in good),
            "the index-pinned pair reports %d unlinked Height and %d Height fed "
            "by a Bump; the correctly wired graph reports 0 and 0"
            % (sum(r["height_unlinked"] for r in bad),
               sum(r["height_driven_by_a_bump"] for r in bad)))

        # [26] R2-058. THE WAVELENGTH CONSTANTS, MEASURED OFF A RENDER.
        #      Every other check in this file that touches a wavelength asks the
        #      arithmetic whether the arithmetic agrees with itself. This one
        #      renders the node and counts the bands, so it can disagree.
        #
        #      A CALIBRATION CASE FIRST, with a known answer that shares nothing
        #      with the thing under test: a closed-form sin(2*pi*x/lam) out of
        #      Math nodes, no texture node anywhere in it. If the probe cannot
        #      recover a wavelength it was told in metres, nothing below counts.
        def _cal(lam):
            def build(ntx):
                sep = ntx.n("ShaderNodeSeparateXYZ")
                ntx.pin_named(sep, "Vector", ntx.object_coords())
                mul = ntx.n("ShaderNodeMath", operation='MULTIPLY')
                ntx.t.links.new(sep.outputs["X"], mul.inputs[0])
                mul.inputs[1].default_value = 2.0 * math.pi / lam
                sn = ntx.n("ShaderNodeMath", operation='SINE')
                ntx.t.links.new(mul.outputs[0], sn.inputs[0])
                mad = ntx.n("ShaderNodeMath", operation='MULTIPLY_ADD')
                ntx.t.links.new(sn.outputs[0], mad.inputs[0])
                mad.inputs[1].default_value = 0.5
                mad.inputs[2].default_value = 0.5
                return (mad, 0)
            return build

        cal = [(lam, emitted_wavelength_m(_cal(lam)))
               for lam in (0.05, 0.01)]
        cal_err = max(abs(g - w) / w for w, g in cal)

        #      THE MEASUREMENT: ask for a pitch by name and count what arrives.
        askw = [(lam, emitted_wavelength_m(
                    lambda ntx, L=lam: ntx.wave(ntx.object_coords(),
                                                wavelength_m=L)))
                for lam in (0.02, 0.004)]
        ask_err = max(abs(g - w) / w for w, g in askw)

        #      THE POSITIVE CONTROL THAT MUST FAIL. `scale = 1/lam` is the
        #      pre-R2-058 idiom and the value `_tex_wavelength_m` used to
        #      report. It must come back 3.183x FINER than asked, and it does.
        #      If anyone sets WAVE_WAVELENGTH_FACTOR back to 1.0, the row above
        #      breaks and this one starts passing — the two move in opposite
        #      directions, which is what a control is for.
        old_way = emitted_wavelength_m(
            lambda ntx: ntx.wave(ntx.object_coords(), scale=1.0 / 0.02))
        old_ratio = 0.02 / old_way

        #      AND THE AUDIT PATH ITSELF: `_tex_wavelength_m` is what
        #      `bump_relief_report` reads. Point it at a live node and compare
        #      against the rendered answer for the SAME node.
        nt_w = NT("IKT_waveaudit")
        wnd = nt_w.wave(nt_w.object_coords(), wavelength_m=0.004)[0]
        audit_lam = _tex_wavelength_m(wnd)
        audit_err = abs(audit_lam - askw[1][1]) / askw[1][1]

        #      AND THE DIAGONAL BRANCH, which is the one that is NOT 2*pi/20.
        #      Blender sums the components and multiplies by TEN, so along a
        #      single axis the period is 2*pi/(10*Scale) and normal to the bands
        #      in 3-D it is that over sqrt(3). The probe's row runs along local
        #      x, so what it measures is the along-axis figure, and the audit
        #      function reports the band-normal one: the two must differ by
        #      exactly sqrt(3), and if the branch were missing they would differ
        #      by 2 instead. A relation, not a repeated constant.
        S_D = 40.0
        nt_d = NT("IKT_wavediag")
        dnd = nt_d.wave(nt_d.object_coords(), S_D, direction="DIAGONAL")[0]
        diag_audit = _tex_wavelength_m(dnd)
        diag_row = emitted_wavelength_m(
            lambda ntx: ntx.wave(ntx.object_coords(), S_D,
                                 direction="DIAGONAL"))
        diag_ratio = diag_row / diag_audit
        chk("wave_diagonal_is_not_the_bands_factor",
            abs(diag_ratio - math.sqrt(3.0)) < 0.03
            and abs(diag_row - 2 * math.pi / (10.0 * S_D)) / diag_row < 0.03,
            "BANDS DIAGONAL at Scale %g renders a %.4f mm period along x "
            "(closed form 2*pi/(10*S) = %.4f mm) and _tex_wavelength_m reports "
            "the band-normal %.4f mm; the ratio is %.4f against sqrt(3) = "
            "%.4f — a BANDS-X reading would have made it %.4f"
            % (S_D, 1000 * diag_row, 1000 * 2 * math.pi / (10.0 * S_D),
               1000 * diag_audit, diag_ratio, math.sqrt(3.0),
               diag_row / (WAVE_WAVELENGTH_FACTOR / S_D)))

        chk("wavelength_constants_measured_off_a_render",
            cal_err < 0.02 and ask_err < 0.03
            and 3.0 < old_ratio < 3.4 and audit_err < 0.03,
            "calibration sine recovered to %.2f %%; wave(wavelength_m=20 mm) "
            "emits %.4f mm and (4 mm) emits %.4f mm, worst error %.2f %%; the "
            "OLD idiom scale=1/lam emits %.4f mm for a 20 mm ask, %.3fx too "
            "fine (2*pi/20 = %.5f predicts %.3fx); and _tex_wavelength_m — the "
            "function bump_relief_report audits with — reads %.4f mm off the "
            "live node against %.4f mm measured, %.2f %% apart"
            % (100 * cal_err, 1000 * askw[0][1], 1000 * askw[1][1],
               100 * ask_err, 1000 * old_way, old_ratio,
               WAVE_WAVELENGTH_FACTOR, 1.0 / WAVE_WAVELENGTH_FACTOR,
               1000 * audit_lam, 1000 * askw[1][1], 100 * audit_err))

        chk("bump_takes_a_modulation_not_a_depth",
            abs(dist * 1000.0 - want_mm) < 1e-6 and refused and both
            and len(rows) == 1 and abs(rows[0]["m"] - 0.28) < 0.02
            and abs(rows[0]["wavelength_m"] - 0.008) < 1e-9,
            "modulation_pp=0.28 at an 8 mm wavelength -> Distance %.6f m "
            "(%.4f mm); read back off the live graph the same node measures "
            "m %.3f at lam %.1f mm; a modulation with no wavelength and a "
            "double spec are both refused"
            % (dist, dist * 1000.0, rows[0]["m"],
               1000.0 * rows[0]["wavelength_m"]))

    print("\n  itemkit selftest: %d checks, %d FAILED %s"
          % (len(out), len(fails), fails or ""))
    return not fails


if __name__ == "__main__":
    # BLENDER RETURNS 0 FOR A SCRIPT THAT RAISED. `blender -b -P itemkit.py --
    # --selftest` printed a traceback and exited 0, MEASURED on this box while
    # landing R2-059: the positive control for the new exposure assertion made
    # `contract_sun` raise, the selftest never reached its own verdict, and the
    # shell saw success. A selftest whose crash is indistinguishable from a pass
    # is not a selftest. `gate_exit.guard` maps an uncaught exception to 2 and
    # passes a real verdict through unchanged (0 pass, 1 fail, 3 vacuous).
    _TOOLS = os.path.join(_ROOT, "tools")
    if _TOOLS not in sys.path:
        sys.path.insert(0, _TOOLS)
    import gate_exit                                             # noqa: E402

    def _cli():
        argv = sys.argv
        argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
        if "--selftest" in argv or not argv:
            return 0 if selftest() else 1
        return 0

    gate_exit.guard(_cli, tool="itemkit")
