#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cockpit_surface.py — R2-881: the seat the client complained about.

    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim_driver.blend \
        --factory-startup -noaudio -P tools/cockpit_surface.py -- \
        --out world/car_anim_driver_R2881_seat.blend --json work/r2881/seat.json

THE FRAMING EVERY NUMBER HERE IS QUOTED AT
------------------------------------------
Frame 2635, `CAM_DRV_F2635`, 32 mm on a 36 mm sensor at 3840x2160, camera 2.34 m
from the cockpit aperture and 80.4 deg above its plane.  That is **1458.9 px/m**
at the aperture and a measured **1416.4 px/m** at the centre of `CI_seat`
(f = 3413.3 px, d = 2.410 m).  A "resolvable" feature below is one whose period
clears ~2.5 px there; a feature at 2.4 px is at Nyquist and is not a feature, it
is a flat tone with noise on it.

WHAT WAS WRONG, MEASURED
------------------------
1.  THE CARBON WEAVE WAS AT NYQUIST AND THEREFORE INVISIBLE.  `CarbonMatte`
    inherits round 1's `carbon_fibre()` / `_weave(nt, scale=190.0)`.  The three
    triplanar `Mapping` nodes carry Scale 190 and each `Wave BANDS` behind them
    is at Scale 1.0 — and Blender's Wave node multiplies its coordinate by 20
    internally, so the emitted period is `2*pi/20 / 190 = 1.6535 mm`, i.e.
    604.8 periods/m, i.e. **2.41 px**.  Averaged over a pixel that is a constant.
    The exterior already got this fix: `world/car_paint.py`'s `WEAVE_PITCH_M =
    0.0050` documents the identical bug on `LiveryPaint` — and `car_paint.py`
    only ever targets `LiveryPaint` (`TARGET_MATERIAL`, line 124), which is
    exactly why `CarbonMatte` never received it.

2.  `SuedeGrip` HAD NO COLOUR OR ROUGHNESS TEXTURE AT ALL.  One `TexNoise` at
    Scale 1400 — a 1.143 mm feature, **1.62 px**, fully sub-pixel — feeding only
    a Bump.  Base Color and Roughness were constants.  `imperfections.py` then
    modulated those constants, but a soiling layer on a flat value is still a
    flat value with dirt on it.

3.  `Coat Weight = 0.42` WITH `Coat Normal` UNCONNECTED.  42 % of the response
    was a gloss layer reflecting off the *unbumped* shading normal, which washes
    out whatever weave survives.  (`imperfections.py` wires `Coat Normal` under
    `coat=True`; `AMOUNTS["CarbonMatte"]` sets `coat=False`, so it never did.)

4.  THE FACETS ARE REAL.  Round 1's `_emit` calls `shade_auto_smooth(ob, 36 deg)`,
    which writes hard `sharp_edge` booleans and nothing else — no bevel, no
    custom normals.  On a 0.53 m shell at 15,778 polys (median edge 4.91 mm =
    7.2 px) that turns the loft's rolled-edge and bolster-crest rings — which
    are continuous curvature — into printed creases.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT
-------------------------------------------------
MATERIAL AND SHADING ATTRIBUTES ONLY.  Not one vertex moves, no topology
changes, no object transform and no keyframe is touched.  That is not modesty,
it is the reason this scope was chosen: 32 of these objects carry beat 1's
explode path, and a shared action datablock previously rewrote the car's own
assembly flight when something upstream of it was edited.  `sharp_edge` is a
mesh ATTRIBUTE — a per-edge boolean — so clearing it changes shading and cannot
change geometry.  `--assert-static` re-hashes every CI_* vertex buffer and every
CI_* fcurve before and after and fails if either moved.

THE IMPERFECTION LAYER IS PRESERVED BY REMOVING IT AND PUTTING IT BACK
---------------------------------------------------------------------
`tools/imperfections.py` owns `Base Color`, `Roughness`, `Normal` (and on
`SuedeGrip` also `Sheen Weight` and `Specular IOR Level`) on both of these
materials through its `R2IMP_*` layer, and records the originals in
`material["r2imp"]`.  Editing underneath a live injection means guessing which
`R2IMP_*` input used to be the base value.  Instead this imports
`imperfections` and calls its own `strip(mat)` before the rewrite and
`inject(mat, AMOUNTS[name], strength)` after it — the documented round trip —
so the soiling ends up sitting on the new base exactly as it sat on the old one,
at the same strength the blend already recorded (`*_imp.json`, strength 1.0).

FEED SOCKETS BY NAME.  Blender 5.2 moved `Principled BSDF.Normal` from index 5
to 6 and inserted `Filter Width` at index 2 of `ShaderNodeBump`; index feeding
shipped 14 dead bump stacks on this project.  Every socket this file writes goes
through `feed(...)`, which resolves by name and raises if the name is absent.

STATE THE RADIANCE MODULATION, NOT THE MILLIMETRES.  Every relief amplitude here
comes from `itemkit.relief_amplitude_for(modulation_pp, wavelength_m)` and every
texture frequency from `itemkit.noise_scale_for` / the Wave factor.  Amplitudes
chosen in raw millimetres have been rendered and rejected three times on this
project; `--relief-budget` prints both layers against
`itemkit.RELIEF_BANDS["isotropic_micro"]` before anything is written.

Blender exits 0 on an uncaught exception.  Judge only on the final
`>> STAGE RESULT: <TOKEN>` line.
"""

import argparse
import hashlib
import json
import math
import os
import sys

import bpy
from mathutils import Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "world"), os.path.join(R2, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

VERSION = 1
PFX = "R2CS_"
REC_KEY = "r2cs"
RESULT = "R2881_COCKPIT_SURFACE"

TARGET_MATERIALS = ("CarbonMatte", "SuedeGrip")
OBJECT_PREFIX = "CI_"
#: the six the client is looking at; reported separately from the CI_* sweep
SEAT_OBJECTS = ("CI_seat", "CI_seatpad", "CI_headrest",
                "CI_sidehead", "CI_liner", "CI_harness_web")

# --------------------------------------------------------------------------- #
# TUNABLES.  Each one is a number somebody has to be able to argue with, so each
# says what it is, where it came from, and what it costs in pixels at the shot.
# --------------------------------------------------------------------------- #

#: px/m on the seat at frame 2635, MEASURED off the look scene (not assumed):
#: f = lens/sensor * W = 32/36 * 3840 = 3413.3 px, seat centre at d = 2.410 m.
PX_PER_M = 1416.4

# ---- the weave ------------------------------------------------------------
# 5.0 mm tow pitch, THE SAME NUMBER `car_paint.py` SHIPPED on the bodywork
# (`WEAVE_PITCH_M`), for the same reason and now on the same car: real 2x2 twill
# is about 5 mm, and 5.0 mm is 7.29 px here where 1.6535 mm was 2.41 px.  The
# twill DESIGN is untouched — same triplanar projection, same two perpendicular
# SIN bands overlaid, same object-space coordinate.  Only the pitch moves.
WEAVE_PITCH_M = 0.0050
#: Blender's Wave BANDS multiplies its coordinate by 20, so a Mapping Scale of S
#: in front of a Wave at Scale 1.0 emits a period of (2*pi/20)/S metres.  This is
#: `itemkit.WAVE_WAVELENGTH_FACTOR` and it is the whole bug in one line.
WAVE_FACTOR = 2.0 * math.pi / 20.0                     # 0.3141593
MAPPING_SCALE = WAVE_FACTOR / WEAVE_PITCH_M            # 62.832

# The relief has to be RE-DERIVED, not carried over, and this is the trap in
# re-pitching a weave.  Slope goes as amplitude/wavelength, so tripling the pitch
# at a fixed amplitude divides the modulation by three.  Round 1's 0.0005 m x
# 0.095 = 47.5 um read m = 0.813 pp at 1.6535 mm (far above the band, but
# sub-pixel, so it only ever delivered noise) and would read m = 0.270 at 5.0 mm.
# Stated as a modulation instead: 0.32 pp, upper-middle of
# `itemkit.RELIEF_BANDS["isotropic_micro"]` = (0.12, 0.45), which is the band
# whose ends were set by looking at renders — 0.28 accepted as cloth, 0.79
# rejected as machined.  Upper-middle and not the centre because the relief law
# is calibrated on the contract sun's 12.47 deg directional key and this shot is
# a shaded cockpit interior lit mostly by sky and bounce, which under-delivers
# modulation for the same slope.
WEAVE_MOD_PP = 0.32

# The grazing fade is a stand-in for the mip filtering a procedural never gets:
# where the surface turns edge-on, many weave cells fall inside one pixel and the
# twill aliases into a comb.  Round 1 set the band at |N.I| 0.10..0.42 FOR A
# 1.6535 mm WEAVE.  Aliasing starts where the projected period crosses a pixel,
# and the projected period scales with the pitch, so a 5.0 mm weave survives
# 3.023x further into grazing: 0.10/3.02 = 0.033 and 0.42/3.02 = 0.139.  Leaving
# the old band in place after re-pitching would have thrown away the weave over
# the whole of a bowl-shaped seat seen from 80 deg above — the bolsters and the
# seat back are exactly the parts at |N.I| ~ 0.2-0.4.  Rounded outward from the
# arithmetic for margin.
WEAVE_FADE_LO, WEAVE_FADE_HI = 0.045, 0.200

# ---- the suede ------------------------------------------------------------
# THE RESOLVABLE BAND IS 2-6 px, i.e. 1.4-4.2 mm at 1416 px/m.  Everything below
# is inside it by construction; the printed report checks it rather than trusting
# it.  Round 1's single feature was 1.143 mm = 1.62 px and could not be there.
#
# Suede is not isotropic.  It has a NAP — a pile combed one way — and the whole
# reason a real seat pad does not read as felt is that you can see which way the
# pile lies.  So the fine field is stretched: 2.2 mm across the nap (3.11 px) and
# 11.0 mm along it (15.6 px), a 5:1 streak.
NAP_ACROSS_M = 0.0022
NAP_ALONG_M = 0.0110
#: the nap direction in OBJECT space.  Fore-aft (car X) — a moulded seat's
#: alcantara is laid along the driver, and every CI_* shares the car's frame.
NAP_DIR_OBJ = (1.0, 0.0, 0.0)
#: isotropic patchiness one octave coarser, so the streaks sit in fields rather
#: than covering the pad at one density.  3.8 mm = 5.38 px, top of the band.
MOTTLE_M = 0.0038
#: and a broad drift well above the band, which is not texture but FORM: on a
#: real pad the pile lies in large domains and that is most of what you see
#: first.  24 mm = 34 px.
SWEEP_M = 0.0240

# Blender's fBm Factor is not uniform on 0..1 — measured over three clusters at
# mean 0.500, p5/p95 0.40/0.60 (`imperfections.NOISE_LO/HI`).  Feeding it raw
# into an amplitude means getting a fifth of the amplitude asked for, so every
# field here is normalised through this window first and the weights below are
# then true peak-to-peak fractions.
NOISE_LO, NOISE_HI = 0.385, 0.615

# Base colour.  Round 1's constant is (0.017, 0.017, 0.019) and THE MEAN IS
# PRESERVED: these are 0.55x and 1.45x it, and the height that drives the ramp
# has mean 0.5, so the pad's overall value against the rest of the cockpit does
# not move and only its structure appears.
#
# STATE THE REALISED SPREAD, NOT THE RAMP ENDS.  The ends are 1.40 stops apart
# (log2 1.45/0.55) and quoting that would overstate this by a factor of seven:
# the height is a weighted sum of three independent normalised noises, so it
# concentrates hard on its mean.  With weights (0.50, 0.30, 0.20) and a per-field
# sigma of ~0.22 the height's sigma is ~0.136, which the ramp turns into ~0.20
# stops of albedo at 1 sigma and ~0.6 stops at 3 sigma.  That is a real tonal
# texture through AgX at -3.628 and it is not a pattern.  The ramp ends are only
# reached where all three fields agree, which is where a real pile has a genuine
# whorl — and a nap you can write on with a fingertip swings that far, which is
# precisely what makes suede read as suede and not as flat felt.
SUEDE_BASE = (0.017, 0.017, 0.019)
SUEDE_LO_K, SUEDE_HI_K = 0.55, 1.45

# Roughness.  Round 1's constant is 0.86.  Where the pile lies flat and coherent
# it scatters a little more directionally; where it stands up it is rougher.
# Anti-correlated with the albedo on purpose — the bright streaks are the lying
# pile — because a roughness field that agrees with the colour field just doubles
# the colour and reads as a printed pattern.
SUEDE_ROUGH_BASE = 0.86
SUEDE_ROUGH_LO, SUEDE_ROUGH_HI = 0.780, 0.925

# Sheen — the OTHER half of the nap, and the directional half.  D027 is the
# governing lesson: sheen is a broad grazing-angle WHITE lobe, and at 0.32 it
# turned a 1.7 % albedo grip into a light grey pillow, exactly as it turned the
# tyres grey.  Round 1 settled on a flat 0.06.  This keeps the MEAN at ~0.065 and
# spends the variation on direction: strongest looking ACROSS the pile (you see
# the fibre sides), weakest looking along it.  And it is faded out head-on,
# because a sheen lobe that acts at normal incidence is not a sheen lobe.
SHEEN_ACROSS, SHEEN_ALONG = 0.100, 0.035
SHEEN_BASE = 0.060
#: |N.I| window over which the directional term is crossfaded in.  1.0 is head-on.
SHEEN_GRAZE_HI, SHEEN_GRAZE_LO = 0.85, 0.25
#: how much of the albedo the nap direction carries, peak-to-peak, on top of the
#: fine fields.  This is the broad "which way is the pile lying" lightness, the
#: single most recognisable thing about a suede surface.
NAP_DIR_ALBEDO_PP = 0.28

#: field weights into the albedo height.  They sum to 1.0 before the directional
#: term, so the height is a genuine 0..1 and the ramp stops mean what they say.
W_NAP, W_MOTTLE, W_SWEEP = 0.50, 0.30, 0.20

# Suede relief.  Same law, same band, same reasoning as the weave, stated at the
# FINEST wavelength present because the finest direction is what sets the slope
# (`itemkit._vector_gain`'s lesson).  Round 1's bump was 0.0003 m x 0.28 = 84 um
# at 1.143 mm, which is m = 2.03 pp — 4.5x the top of the band — and it did not
# read as relief because the wavelength was sub-pixel; it read as grain noise
# that the renderer then averaged into a slightly darker flat.
SUEDE_MOD_PP = 0.35

# ---- the creases ----------------------------------------------------------
# Round 1 wrote `sharp_edge` at 36 deg.  A 36 deg dihedral on a 4.91 mm edge is
# not a design feature, it is a loft's own curvature sampled at 15,778 polys: the
# rolled edge of the seat pan and the crest of each bolster are continuous, and
# printing a crease along them is what the client is seeing.  60 deg is the
# threshold that keeps the genuine ones — the pan-to-back junction, the harness
# slots, the shell's cut edges — and drops the false band.  NOTHING IS ADDED:
# an edge above the threshold keeps its flag, an edge below it loses it, and the
# mesh itself is not touched.
SHARP_KEEP_DEG = 60.0
#: what counts as "up-facing" for the census — an adjacent face whose WORLD
#: normal has n.z above this.  The camera is 80.4 deg above the aperture plane,
#: so world +Z is within 10 deg of the view axis and up-facing is what the client
#: can see.  cos(70 deg) = 0.342.
UPFACE_NZ = 0.342


def log(*a):
    print("[cockpit]", *a)
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
# socket plumbing.  BY NAME, ALWAYS.
# --------------------------------------------------------------------------- #

def find_bsdf(mat):
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            return n
    return None


def out_by_name(node, name):
    """Output socket index by name — and it must be ENABLED.

    `ShaderNodeMix` carries three outputs all named "Result" and only the one
    matching `data_type` is enabled; a bare name lookup returns the float one.
    `car_paint.py` shipped that exact fault once (R2-534) and the panel rendered
    flat white with the chain fully connected.
    """
    for i, o in enumerate(node.outputs):
        if o.name == name and o.enabled:
            return i
    raise RuntimeError("%s has no enabled output named %r; it has %s"
                       % (node.bl_idname, name,
                          [(o.name, o.enabled) for o in node.outputs]))


def feed(nt, bsdf, name, src):
    """Write a Principled socket BY NAME.  `src` is (node, out_index) or a value.

    THE WHOLE POINT OF THIS FUNCTION.  Blender 5.2 moved `Principled BSDF.Normal`
    from index 5 to 6; index feeding shipped 14 dead bump stacks on this project
    and every one of them built, rendered and passed a node-count check.
    """
    sock = bsdf.inputs.get(name)
    if sock is None:
        raise RuntimeError("Principled BSDF has no input named %r; it has %s"
                           % (name, [s.name for s in bsdf.inputs]))
    if isinstance(src, tuple) and src and hasattr(src[0], "outputs"):
        node, idx = src
        o = node.outputs[idx]
        if not o.enabled:
            raise RuntimeError("refusing to link %s.%s -> BSDF.%s: that output "
                               "is DISABLED" % (node.bl_idname, o.name, name))
        for l in list(sock.links):
            nt.links.remove(l)
        nt.links.new(o, sock)
        return
    for l in list(sock.links):
        nt.links.remove(l)
    if hasattr(sock.default_value, "__len__"):
        v = tuple(src)
        sock.default_value = v if len(v) == 4 else (v + (1.0,))
    else:
        sock.default_value = float(src)


def set_vec(node, idx, v):
    """Set a 3-component Vector input to a constant.

    `itemkit.NT.pin` CANNOT DO THIS and fails loudly if asked:
    `(x, y, z)` is turned into `(x, y, z, 1.0)` on its way in — correct for a
    Color socket, and a `ValueError: sequences of dimension 0 should contain 3
    items, not 4` on a Vector one.  Verified against 5.2 rather than assumed;
    the `_vector_gain` docstring's `vmath('MULTIPLY', obj, (110.0,)*3)` example
    is illustrative and does not run.
    """
    node.inputs[idx].default_value = tuple(float(x) for x in v)[:3]


def nt_on(mat):
    """An `itemkit.NT` bound to an EXISTING tree, without clearing it.

    `NT.__init__` calls `nodes.clear()`, which is right when a module owns a
    whole material and wrong here: `imperfections.py` owns a layer in both of
    these and round 1 owns the weave in one of them.  Everything else on NT —
    `noise(wavelength_m=)`, `wave(wavelength_m=)`, `bump(modulation_pp=)`,
    `pin_named` — is the relief and frequency law this project is required to
    build through, so the class is reused and only the constructor is not.
    """
    import itemkit as K
    g = K.NT.__new__(K.NT)
    g.m = mat
    g.t = mat.node_tree
    g.x = 0
    return g


def tag_new(nt, before, y_shift=-2400.0):
    """Name every node created since `before` with the module prefix and move it
    clear of the graph it was added to, so a human opening the blend can see
    which nodes are this pass and which are round 1's."""
    made = [n for n in nt.nodes if n.name not in before]
    made.sort(key=lambda n: n.name)
    for i, n in enumerate(made):
        n.location = (n.location.x, n.location.y + y_shift)
        n.name = "%s%03d" % (PFX, i)
    return made


# --------------------------------------------------------------------------- #
# 1 + 3.  CarbonMatte: re-pitch the weave, re-derive its relief, wire the coat.
# --------------------------------------------------------------------------- #

def fix_carbon_matte(mat, report):
    """Three edits and no new design.

    The triplanar twill, the ramps that read albedo and roughness off it, the
    normal-blended projection weights and the grazing fade are all round 1's and
    all stay.  What changes is the PITCH those nodes run at, the AMPLITUDE of the
    relief that pitch implies, the ANGLE at which the fade gives up, and the fact
    that the clearcoat now sees the same normal as the base.
    """
    nt = mat.node_tree
    bsdf = find_bsdf(mat)
    if bsdf is None:
        raise RuntimeError("%s has no Principled BSDF" % mat.name)

    # -- the pitch ----------------------------------------------------------
    maps = [n for n in nt.nodes if n.bl_idname == "ShaderNodeMapping"]
    if len(maps) != 3:
        raise RuntimeError("%s: expected round 1's three triplanar Mapping "
                           "nodes, found %d" % (mat.name, len(maps)))
    before_scales = []
    for m in maps:
        s = m.inputs["Scale"]
        if s.is_linked:
            raise RuntimeError("%s: %s.Scale is LINKED; this pass assumes round "
                               "1's constant" % (mat.name, m.name))
        before_scales.append(float(s.default_value[0]))
        s.default_value = (MAPPING_SCALE,) * 3
    # every Wave behind them must still be at Scale 1.0, or the pitch arithmetic
    # above is not the pitch the material emits
    waves = [n for n in nt.nodes if n.bl_idname == "ShaderNodeTexWave"]
    bad = [(n.name, float(n.inputs["Scale"].default_value)) for n in waves
           if abs(float(n.inputs["Scale"].default_value) - 1.0) > 1e-6]
    if bad:
        raise RuntimeError("%s: Wave nodes not at Scale 1.0: %s — the emitted "
                           "pitch is not (2*pi/20)/MappingScale" % (mat.name, bad))
    pitch_before = WAVE_FACTOR / before_scales[0]
    pitch_after = WAVE_FACTOR / MAPPING_SCALE

    # -- the relief ---------------------------------------------------------
    import itemkit as K
    bumps = [n for n in nt.nodes if n.bl_idname == "ShaderNodeBump"]
    if len(bumps) != 1:
        raise RuntimeError("%s: expected exactly one round-1 Bump after strip(), "
                           "found %d" % (mat.name, len(bumps)))
    b = bumps[0]
    if not b.inputs["Height"].is_linked:
        raise RuntimeError("%s: the weave Bump has an UNLINKED Height — a "
                           "constant has zero gradient and no relief"
                           % mat.name)
    amp_before_mm = (float(b.inputs["Distance"].default_value)
                     * float(b.inputs["Strength"].default_value) * 1000.0)
    amp_mm = K.relief_amplitude_for(WEAVE_MOD_PP, WEAVE_PITCH_M)
    b.inputs["Strength"].default_value = 1.0
    b.inputs["Distance"].default_value = amp_mm * 1e-3

    # -- the grazing fade ---------------------------------------------------
    mrs = [n for n in nt.nodes if n.bl_idname == "ShaderNodeMapRange"]
    fade = None
    for n in mrs:
        f0 = float(n.inputs["From Min"].default_value)
        f1 = float(n.inputs["From Max"].default_value)
        if abs(f0 - 0.10) < 1e-6 and abs(f1 - 0.42) < 1e-6:
            fade = n
            break
    if fade is None:
        raise RuntimeError("%s: could not find round 1's weave grazing fade "
                           "(MapRange 0.10..0.42); found %s"
                           % (mat.name, [(n.name,
                                          float(n.inputs['From Min'].default_value),
                                          float(n.inputs['From Max'].default_value))
                                         for n in mrs]))
    fade.inputs["From Min"].default_value = WEAVE_FADE_LO
    fade.inputs["From Max"].default_value = WEAVE_FADE_HI

    report[mat.name] = dict(
        pitch_before_mm=pitch_before * 1000.0,
        pitch_after_mm=pitch_after * 1000.0,
        px_before=pitch_before * PX_PER_M,
        px_after=pitch_after * PX_PER_M,
        mapping_scale_before=before_scales, mapping_scale_after=MAPPING_SCALE,
        bump_amp_before_mm=amp_before_mm, bump_amp_after_mm=amp_mm,
        mod_before_at_old_pitch=K.modulation_for_amplitude(amp_before_mm,
                                                           pitch_before),
        mod_before_at_new_pitch=K.modulation_for_amplitude(amp_before_mm,
                                                           pitch_after),
        mod_after=K.modulation_for_amplitude(amp_mm, pitch_after),
        fade_before=[0.10, 0.42], fade_after=[WEAVE_FADE_LO, WEAVE_FADE_HI],
    )
    log("%s: weave pitch %.4f -> %.4f mm  (%.2f -> %.2f px at %.0f px/m)"
        % (mat.name, pitch_before * 1000, pitch_after * 1000,
           pitch_before * PX_PER_M, pitch_after * PX_PER_M, PX_PER_M))
    log("%s: weave relief %.4f -> %.4f mm p-p  (m %.3f -> %.3f pp at the new "
        "pitch; band isotropic_micro = 0.12..0.45)"
        % (mat.name, amp_before_mm, amp_mm,
           K.modulation_for_amplitude(amp_before_mm, pitch_after),
           K.modulation_for_amplitude(amp_mm, pitch_after)))
    log("%s: grazing fade |N.I| 0.100..0.420 -> %.3f..%.3f"
        % (mat.name, WEAVE_FADE_LO, WEAVE_FADE_HI))
    return report[mat.name]


def wire_coat_normal(mat):
    """`Coat Normal` <- whatever now feeds `Normal`.

    Called AFTER `imperfections.inject`, so the coat sees the full stack — round
    1's weave bump and round 2's micro bump — and not just the part of it that
    existed when this module ran.  Doing it before inject would have left the
    coat on the weave alone and the base on weave+micro, which is a different
    surface under the clearcoat than on top of it.
    """
    nt = mat.node_tree
    b = find_bsdf(mat)
    n = b.inputs.get("Normal")
    c = b.inputs.get("Coat Normal")
    if n is None or c is None:
        raise RuntimeError("%s: Principled has no Normal/Coat Normal" % mat.name)
    if not n.is_linked:
        raise RuntimeError("%s: Normal is not linked, so there is no relief to "
                           "give the coat" % mat.name)
    src = n.links[0].from_socket
    for l in list(c.links):
        nt.links.remove(l)
    nt.links.new(src, c)
    log("%s: Coat Normal <- %s.%s (Coat Weight %.3f, Coat Roughness %.3f)"
        % (mat.name, n.links[0].from_node.name, src.name,
           float(b.inputs["Coat Weight"].default_value)
           if not b.inputs["Coat Weight"].is_linked else float("nan"),
           float(b.inputs["Coat Roughness"].default_value)
           if not b.inputs["Coat Roughness"].is_linked else float("nan")))
    return dict(coat_normal_from=n.links[0].from_node.name)


# --------------------------------------------------------------------------- #
# 2.  SuedeGrip: give it a surface.
# --------------------------------------------------------------------------- #

def build_suede_grip(mat, report):
    """A nap, in four fields and one direction.

    Round 1's whole material was TexCoord -> Noise(1400) -> Bump -> Normal, with
    Base Color and Roughness as constants.  This replaces it with:

      NAP     an ANISOTROPIC noise, 2.2 mm across and 11.0 mm along the pile.
              The stretch is done on the COORDINATE, not on the Scale socket:
              multiplying object space by (across/along, 1, 1) before a noise
              asked for `wavelength_m = across` gives features `across` wide and
              `along` long, and both numbers stay legible in metres.
      MOTTLE  isotropic, 3.8 mm, so the streaks vary in density instead of
              covering the pad uniformly.
      SWEEP   isotropic, 24 mm — above the texture band on purpose.  This is the
              domain structure of a real pile, and it is what the eye reads
              first from 2.4 m.
      NAP DIRECTION  the view direction PROJECTED INTO THE SURFACE, dotted with
              the pile direction, faded in with grazing angle.  This is the term
              that makes suede look like suede rather than like dark felt: it is
              a broad lightness that swings as the surface curves away, and it
              cannot be faked with any amount of isotropic noise.

    Albedo, roughness, sheen and relief are all read off those same fields, so
    the surface cannot disagree with itself.  Roughness is ANTI-correlated with
    albedo — the bright streaks are pile lying flat, which is the smoother state
    — because a roughness field that agrees with the colour field just prints the
    colour twice.
    """
    import itemkit as K
    nt = mat.node_tree
    bsdf = find_bsdf(mat)
    if bsdf is None:
        raise RuntimeError("%s has no Principled BSDF" % mat.name)

    # Round 1's base graph goes; the BSDF and the output stay.  (strip() has
    # already removed the R2IMP_* layer, and inject() puts it back afterwards.)
    keep = {"ShaderNodeBsdfPrincipled", "ShaderNodeOutputMaterial"}
    removed = [n.name for n in list(nt.nodes) if n.bl_idname not in keep]
    for n in list(nt.nodes):
        if n.bl_idname not in keep:
            nt.nodes.remove(n)
    before = {n.name for n in nt.nodes}

    g = nt_on(mat)
    P = g.object_coords()

    def norm01(fac):
        """Blender's fBm Factor -> a true 0..1, through the measured window."""
        return g.maprange(fac, NOISE_LO, NOISE_HI, 0.0, 1.0)

    # --- the three scalar fields ------------------------------------------
    kx = NAP_ACROSS_M / NAP_ALONG_M
    _sq = g.n("ShaderNodeVectorMath", operation="MULTIPLY")
    g.pin(_sq, 0, P)
    set_vec(_sq, 1, (kx, 1.0, 1.0))
    P_nap = (_sq, 0)
    nap = norm01(g.noise(P_nap, wavelength_m=NAP_ACROSS_M, detail=3.0, rough=0.50))
    mottle = norm01(g.noise(P, wavelength_m=MOTTLE_M, detail=2.0, rough=0.50))
    sweep = norm01(g.noise(P, wavelength_m=SWEEP_M, detail=2.0, rough=0.50))

    # --- the nap direction -------------------------------------------------
    # d_world = the pile direction carried out of object space.  VECTOR, not
    # NORMAL: it is a direction glued to the part, and the parts rotate.
    vt = g.n("ShaderNodeVectorTransform", vector_type="VECTOR",
             convert_from="OBJECT", convert_to="WORLD")
    set_vec(vt, 0, NAP_DIR_OBJ)
    d = (vt, 0)
    geo = g.n("ShaderNodeNewGeometry")
    N = (geo, out_by_name(geo, "Normal"))
    I = (geo, out_by_name(geo, "Incoming"))

    def dot(a, b):
        nd = g.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        g.pin(nd, 0, a)
        g.pin(nd, 1, b)
        return (nd, out_by_name(nd, "Value"))

    def project_out_normal(v):
        """v - N (v.N): the part of v lying IN the surface."""
        s = g.n("ShaderNodeVectorMath", operation="SCALE")
        g.pin(s, 0, N)
        g.pin(s, 3, dot(v, N))
        r = g.n("ShaderNodeVectorMath", operation="SUBTRACT")
        g.pin(r, 0, v)
        g.pin(r, 1, (s, 0))
        nz = g.n("ShaderNodeVectorMath", operation="NORMALIZE")
        g.pin(nz, 0, (r, 0))
        return (nz, 0)

    NdotI = g.math("ABSOLUTE", dot(N, I))
    # 1 at grazing, 0 head-on.  The directional term is a SHEEN-class effect and
    # it does not exist at normal incidence; forcing it there would print a
    # gradient across the pad that no lighting could justify.
    graze = g.maprange(NdotI, SHEEN_GRAZE_LO, SHEEN_GRAZE_HI, 1.0, 0.0)
    along = g.math("ABSOLUTE", dot(project_out_normal(I),
                                   project_out_normal(d)))

    # --- albedo -------------------------------------------------------------
    # h = W_NAP*nap + W_MOTTLE*mottle + W_SWEEP*sweep + NAP_DIR_ALBEDO_PP*(along-0.5)*graze
    h = g.math("MULTIPLY", nap, W_NAP)
    h = g.math("ADD", h, g.math("MULTIPLY", mottle, W_MOTTLE))
    h = g.math("ADD", h, g.math("MULTIPLY", sweep, W_SWEEP))
    dir_term = g.math("MULTIPLY",
                      g.math("MULTIPLY", g.math("SUBTRACT", along, 0.5), graze),
                      NAP_DIR_ALBEDO_PP)
    h = g.math("ADD", h, dir_term, clamp=True)

    lo = tuple(c * SUEDE_LO_K for c in SUEDE_BASE)
    hi = tuple(c * SUEDE_HI_K for c in SUEDE_BASE)
    col = g.ramp(h, [(0.10, lo), (0.90, hi)])

    # --- roughness ----------------------------------------------------------
    hr = g.math("ADD",
                g.math("MULTIPLY", nap, 0.65),
                g.math("MULTIPLY", mottle, 0.35))
    rough = g.maprange(hr, 0.0, 1.0, SUEDE_ROUGH_HI, SUEDE_ROUGH_LO)

    # --- sheen --------------------------------------------------------------
    sheen_dir = g.maprange(along, 0.0, 1.0, SHEEN_ACROSS, SHEEN_ALONG)
    sheen = g.fmix(graze, SHEEN_BASE, sheen_dir)

    # --- relief -------------------------------------------------------------
    # Stated at the FINEST wavelength present, which is what sets the slope.
    hb = g.math("ADD",
                g.math("MULTIPLY", nap, 0.72),
                g.math("MULTIPLY", mottle, 0.28))
    nrm = g.bump(hb, 1.0, modulation_pp=SUEDE_MOD_PP,
                 wavelength_m=NAP_ACROSS_M, height_pp=1.0)

    # --- the BSDF, every socket BY NAME -------------------------------------
    feed(nt, bsdf, "Base Color", col)
    feed(nt, bsdf, "Roughness", rough)
    feed(nt, bsdf, "Sheen Weight", sheen)
    feed(nt, bsdf, "Normal", nrm)
    feed(nt, bsdf, "Metallic", 0.0)
    feed(nt, bsdf, "IOR", 1.5)
    feed(nt, bsdf, "Specular IOR Level", 0.22)
    feed(nt, bsdf, "Sheen Roughness", 0.62)
    feed(nt, bsdf, "Coat Weight", 0.0)

    made = tag_new(nt, before)
    amp_mm = K.relief_amplitude_for(SUEDE_MOD_PP, NAP_ACROSS_M)
    report[mat.name] = dict(
        removed_round1_nodes=removed, nodes_built=len(made),
        nap_across_mm=NAP_ACROSS_M * 1000.0,
        nap_along_mm=NAP_ALONG_M * 1000.0,
        mottle_mm=MOTTLE_M * 1000.0, sweep_mm=SWEEP_M * 1000.0,
        px_nap_across=NAP_ACROSS_M * PX_PER_M,
        px_nap_along=NAP_ALONG_M * PX_PER_M,
        px_mottle=MOTTLE_M * PX_PER_M, px_sweep=SWEEP_M * PX_PER_M,
        px_round1_only_feature=(1.6 / 1400.0) * PX_PER_M,
        albedo_lo=lo, albedo_hi=hi,
        albedo_pp_stops=math.log2(SUEDE_HI_K / SUEDE_LO_K),
        rough_lo=SUEDE_ROUGH_LO, rough_hi=SUEDE_ROUGH_HI,
        sheen_across=SHEEN_ACROSS, sheen_along=SHEEN_ALONG,
        bump_amp_mm=amp_mm, bump_mod_pp=SUEDE_MOD_PP,
        bump_amp_before_mm=0.0003 * 0.28 * 1000.0,
        mod_before=K.modulation_for_amplitude(0.084, 1.6 / 1400.0),
    )
    log("%s: rebuilt.  removed %d round-1 nodes, built %d"
        % (mat.name, len(removed), len(made)))
    log("%s: fields  nap %.2f mm across (%.2f px) x %.1f mm along (%.1f px) | "
        "mottle %.2f mm (%.2f px) | sweep %.1f mm (%.1f px) | round 1 had ONE "
        "field at %.3f mm (%.2f px)"
        % (mat.name, NAP_ACROSS_M * 1000, NAP_ACROSS_M * PX_PER_M,
           NAP_ALONG_M * 1000, NAP_ALONG_M * PX_PER_M,
           MOTTLE_M * 1000, MOTTLE_M * PX_PER_M,
           SWEEP_M * 1000, SWEEP_M * PX_PER_M,
           1.6 / 1400.0 * 1000, 1.6 / 1400.0 * PX_PER_M))
    log("%s: albedo %.5f..%.5f (%.2f stops p-p, mean preserved at %.5f) | "
        "roughness %.3f..%.3f | sheen %.3f..%.3f directional | relief %.4f mm "
        "= m %.3f pp at %.2f mm"
        % (mat.name, lo[0], hi[0], math.log2(SUEDE_HI_K / SUEDE_LO_K),
           SUEDE_BASE[0], SUEDE_ROUGH_LO, SUEDE_ROUGH_HI,
           SHEEN_ALONG, SHEEN_ACROSS, amp_mm, SUEDE_MOD_PP,
           NAP_ACROSS_M * 1000))
    return report[mat.name]


# --------------------------------------------------------------------------- #
# 4.  the creases
# --------------------------------------------------------------------------- #

_DIH_CACHE = {}


def edge_dihedrals(me):
    """{edge_index: (angle_deg, (n_a, n_b))} for every 2-face edge.

    Object-space face normals, so the caller rotates them once instead of per
    edge.  Cached per mesh: the census runs before and after and the clear runs
    between them, and clearing an ATTRIBUTE cannot change a dihedral — if it
    could, this pass would not be attribute-only.
    """
    key = me.name
    if key in _DIH_CACHE:
        return _DIH_CACHE[key]
    face_n = [tuple(p.normal) for p in me.polygons]
    edge_faces = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    key_to_idx = {}
    for e in me.edges:
        key_to_idx[tuple(sorted(e.vertices))] = e.index
    out = {}
    for ek, fs in edge_faces.items():
        if len(fs) != 2:
            continue
        i = key_to_idx.get(tuple(sorted(ek)))
        if i is None:
            continue
        a, b = face_n[fs[0]], face_n[fs[1]]
        d = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
        out[i] = (math.degrees(math.acos(d)), (a, b))
    _DIH_CACHE[key] = out
    return out


def sharp_census(ob, keep_deg):
    """Count the flags this object carries, split by the band they sit in and by
    whether the camera can see them.

    The bands are the argument: 36-60 deg is a loft's own curvature at this poly
    density and printing a crease there is the defect; >= 60 deg is a designed
    junction and printing a crease there is correct.
    """
    me = ob.data
    att = me.attributes.get("sharp_edge")
    if att is None:
        return dict(total=0, sharp=0, sharp_false_band=0, sharp_keep=0,
                    sharp_up=0, sharp_up_false_band=0, sharp_up_keep=0,
                    sharp_boundary=0)
    M = ob.matrix_world.to_3x3()
    dih = edge_dihedrals(me)
    n = dict(total=len(me.edges), sharp=0, sharp_false_band=0, sharp_keep=0,
             sharp_up=0, sharp_up_false_band=0, sharp_up_keep=0,
             sharp_boundary=0)
    for e in me.edges:
        if not att.data[e.index].value:
            continue
        n["sharp"] += 1
        d = dih.get(e.index)
        if d is None:
            n["sharp_boundary"] += 1
            continue
        ang, (na, nb) = d
        up = max((M @ Vector(na)).normalized().z,
                 (M @ Vector(nb)).normalized().z) > UPFACE_NZ
        if ang < keep_deg:
            n["sharp_false_band"] += 1
            if up:
                n["sharp_up_false_band"] += 1
        else:
            n["sharp_keep"] += 1
            if up:
                n["sharp_up_keep"] += 1
        if up:
            n["sharp_up"] += 1
    return n


def raise_sharp_threshold(ob, keep_deg):
    """Clear `sharp_edge` wherever the dihedral is below `keep_deg`.

    ATTRIBUTE ONLY.  No vertex, no face, no edge is created, removed or moved;
    the loop that follows writes exactly one boolean per edge and touches nothing
    else.  Boundary and non-manifold edges are LEFT ALONE — a hole's rim has no
    dihedral to judge and its flag is the shell's own cut edge.
    """
    me = ob.data
    att = me.attributes.get("sharp_edge")
    if att is None:
        return 0
    dih = edge_dihedrals(me)
    cleared = 0
    for e in me.edges:
        if not att.data[e.index].value:
            continue
        d = dih.get(e.index)
        if d is None:
            continue
        if d[0] < keep_deg:
            att.data[e.index].value = False
            cleared += 1
    me.update()
    return cleared


# --------------------------------------------------------------------------- #
# the static guarantee
# --------------------------------------------------------------------------- #

#: frames the flight is re-sampled at.  Beat 1's explode path is the thing that
#: must not move, so the sample straddles it as well as the shot itself.
ANIM_SAMPLE_FRAMES = (1, 200, 400, 700, 1000, 1400, 1800, 2200, 2635, 2900)


def static_fingerprint(objs, scene=None):
    """A hash of every vertex coordinate, and of the flight, EVALUATED.

    THIS IS THE WHOLE REASON THE SCOPE IS WHAT IT IS.  32 of these objects carry
    beat 1's explode path and a shared action datablock has already rewritten the
    car's assembly flight once on this project.  A material-and-attribute pass
    cannot move geometry or animation — so prove it, rather than saying it.

    THE FLIGHT IS SAMPLED, NOT READ OFF THE CURVES.  Blender 5.x actions are
    slotted: `Action.fcurves` no longer exists, the curves live in
    `action.layers[].strips[].channelbags[].fcurves`, and a fingerprint taken
    from the curves would still miss a constraint, a driver, a parent or a
    delta transform.  Sampling `matrix_world` at ten frames across the whole film
    catches every one of those and is what "the car flies the same path" actually
    means.
    """
    sc = scene or bpy.context.scene
    keep = sc.frame_current
    hv = hashlib.sha256()
    ha = hashlib.sha256()
    ordered = sorted(objs, key=lambda o: o.name)
    for ob in ordered:
        hv.update(ob.name.encode())
        me = ob.data
        buf = [0.0] * (3 * len(me.vertices))
        me.vertices.foreach_get("co", buf)
        hv.update(("%d|%d|%d" % (len(me.vertices), len(me.edges),
                                 len(me.polygons))).encode())
        hv.update(b"".join(b"%.7f" % v for v in buf))
    for f in ANIM_SAMPLE_FRAMES:
        sc.frame_set(int(f))
        ha.update(b"f%d" % f)
        for ob in ordered:
            ha.update(ob.name.encode())
            for row in ob.matrix_world:
                ha.update(b"".join(b"%.6f" % v for v in row))
    sc.frame_set(keep)
    return hv.hexdigest(), ha.hexdigest()


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #

def verify(mat, want_coat_normal):
    """Refuse to save a material whose chain is connected to the wrong thing.

    A node count cannot see a dead bump stack and did not see fourteen of them.
    These are the four questions that would have.
    """
    bad = []
    nt = mat.node_tree
    b = find_bsdf(mat)
    if b is None:
        return ["%s: no Principled BSDF" % mat.name]
    for nm in ("Base Color", "Roughness", "Normal"):
        s = b.inputs.get(nm)
        if s is None or not s.is_linked:
            bad.append("%s: %s is not linked" % (mat.name, nm))
            continue
        o = s.links[0].from_socket
        if not o.enabled:
            bad.append("%s: %s is fed by a DISABLED output %s.%s"
                       % (mat.name, nm, s.links[0].from_node.bl_idname, o.name))
    if want_coat_normal:
        s = b.inputs.get("Coat Normal")
        if s is None or not s.is_linked:
            bad.append("%s: Coat Normal is not linked" % mat.name)
        elif b.inputs["Normal"].is_linked:
            # BY (node name, socket identifier), NOT BY `is`.  Two reads of the
            # same socket return two different Python wrappers, so an identity
            # test on bpy_struct is always False and this check would have
            # failed on a correctly wired material.
            def sig(sock):
                l = sock.links[0]
                return (l.from_node.name, l.from_socket.identifier)
            if sig(s) != sig(b.inputs["Normal"]):
                bad.append("%s: Coat Normal and Normal are fed by DIFFERENT "
                           "sources (%s vs %s)"
                           % (mat.name, sig(s), sig(b.inputs["Normal"])))
    # every Bump in the tree must have a LINKED Height; a constant has no gradient
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeBump" and not n.inputs["Height"].is_linked:
            bad.append("%s: Bump %s has an unlinked Height — zero gradient, no "
                       "relief" % (mat.name, n.name))
    return bad


def relief_budget(report):
    import itemkit as K
    stages = []
    cm = report.get("materials", {}).get("CarbonMatte")
    sg = report.get("materials", {}).get("SuedeGrip")
    if cm:
        stages.append(("weave BEFORE (old pitch)", cm["pitch_before_mm"] / 1000.0,
                       cm["bump_amp_before_mm"]))
        stages.append(("weave AFTER", WEAVE_PITCH_M, cm["bump_amp_after_mm"]))
    if sg:
        stages.append(("suede BEFORE", 1.6 / 1400.0, sg["bump_amp_before_mm"]))
        stages.append(("suede AFTER", NAP_ACROSS_M, sg["bump_amp_mm"]))
    return K.relief_budget(stages, band="isotropic_micro")


# --------------------------------------------------------------------------- #

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="NEW blend path; this never "
                    "overwrites its input")
    ap.add_argument("--json", default=None)
    ap.add_argument("--sharp-deg", type=float, default=SHARP_KEEP_DEG)
    ap.add_argument("--strength", type=float, default=1.0,
                    help="imperfections.py re-injection strength; must match "
                         "what the blend was built with (world/*_imp.json)")
    ap.add_argument("--frame", type=int, default=2635,
                    help="frame at which world normals are evaluated for the "
                         "up-facing census")
    ap.add_argument("--no-imp", action="store_true",
                    help="do not strip/re-inject the imperfection layer "
                         "(diagnostic only — ships a car with no soiling)")
    ap.add_argument("--measure-only", action="store_true")
    a = ap.parse_args(argv)

    src = bpy.data.filepath
    outp = os.path.abspath(a.out)
    if os.path.abspath(src) == outp:
        print(">> STAGE RESULT: FAIL_WOULD_OVERWRITE_INPUT")
        return 1
    log("in  %s" % src)
    log("out %s" % outp)

    bpy.context.scene.frame_set(a.frame)
    objs = [o for o in bpy.data.objects
            if o.name.startswith(OBJECT_PREFIX) and o.type == 'MESH']
    if not objs:
        print(">> STAGE RESULT: FAIL_NO_CI_OBJECTS")
        return 1
    log("%d %s* meshes at frame %d" % (len(objs), OBJECT_PREFIX, a.frame))

    rep = {"version": VERSION, "frame": a.frame, "px_per_m": PX_PER_M,
           "sharp_keep_deg": a.sharp_deg, "in": src, "out": outp,
           "materials": {}, "sharp": {"before": {}, "after": {}}}

    # ---- census BEFORE -----------------------------------------------------
    tot_b = dict(sharp=0, sharp_false_band=0, sharp_keep=0, sharp_up=0,
                 sharp_up_false_band=0, sharp_up_keep=0)
    for ob in objs:
        c = sharp_census(ob, a.sharp_deg)
        rep["sharp"]["before"][ob.name] = c
        for k in tot_b:
            tot_b[k] += c.get(k, 0)
    rep["sharp"]["before_total"] = tot_b
    log("SHARP BEFORE  all CI_*: %d flagged, %d in the %.0f-%.0f deg false band, "
        "%d up-facing (%d of those false-band)"
        % (tot_b["sharp"], tot_b["sharp_false_band"], 36.0, a.sharp_deg,
           tot_b["sharp_up"], tot_b["sharp_up_false_band"]))
    for nm in SEAT_OBJECTS:
        c = rep["sharp"]["before"].get(nm)
        if c:
            log("   %-16s sharp %5d  false-band %5d  up-facing %5d  "
                "up+false %5d" % (nm, c["sharp"], c["sharp_false_band"],
                                  c["sharp_up"], c["sharp_up_false_band"]))

    vh0, ah0 = static_fingerprint(objs)
    log("static fingerprint BEFORE: verts %s  anim %s" % (vh0[:16], ah0[:16]))

    if a.measure_only:
        if a.json:
            os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
            json.dump(rep, open(a.json, "w"), indent=1)
        print(">> STAGE RESULT: %s_MEASURE_ONLY" % RESULT)
        return 0

    # ---- materials ---------------------------------------------------------
    import imperfections as IMP
    mats = {}
    for nm in TARGET_MATERIALS:
        m = bpy.data.materials.get(nm)
        if m is None:
            log("MISSING material %s" % nm)
            print(">> STAGE RESULT: FAIL_MISSING_MATERIAL_%s" % nm)
            return 1
        mats[nm] = m

    # NOT IDEMPOTENT, AND IT SAYS SO RATHER THAN HALF-APPLYING.  Re-running this
    # on an already-fixed blend would re-pitch an already-re-pitched Mapping and
    # then fail to find round 1's 0.10..0.42 grazing fade, i.e. it would raise
    # somewhere in the middle with the materials partly rewritten.  Blender exits
    # 0 on an uncaught exception, so that failure would be silent to `$?` and the
    # blend would already have been touched.  Refuse up front instead.
    already = [nm for nm, m in mats.items() if REC_KEY in m.keys()]
    if already:
        for nm in already:
            log("%s already carries %s: %s" % (nm, REC_KEY, m.get(REC_KEY)))
        log("run this on a round-1 blend, not on one this pass has already "
            "written")
        print(">> STAGE RESULT: FAIL_ALREADY_APPLIED")
        return 1

    stripped = {}
    if not a.no_imp:
        for nm, m in mats.items():
            stripped[nm] = bool(IMP.strip(m))
            log("%s: imperfections layer stripped=%s" % (nm, stripped[nm]))

    fix_carbon_matte(mats["CarbonMatte"], rep["materials"])
    build_suede_grip(mats["SuedeGrip"], rep["materials"])

    if not a.no_imp:
        for nm, m in mats.items():
            if not stripped.get(nm):
                continue
            touched = IMP.inject(m, IMP.AMOUNTS[nm], a.strength)
            log("%s: imperfections re-injected at strength %.2f; sockets %s"
                % (nm, a.strength, sorted(touched or [])))
            rep["materials"].setdefault(nm, {})["imp_sockets"] = sorted(touched or [])

    # AFTER inject, so the coat sees the whole stack.
    rep["materials"]["CarbonMatte"].update(
        wire_coat_normal(mats["CarbonMatte"]))

    rep["relief_budget"] = relief_budget(rep)

    bad = []
    bad += verify(mats["CarbonMatte"], want_coat_normal=True)
    bad += verify(mats["SuedeGrip"], want_coat_normal=False)
    if bad:
        for b in bad:
            log("WIRING FAIL: %s" % b)
        print(">> STAGE RESULT: FAIL_WIRING")
        return 1
    log("wiring verified: Base Color / Roughness / Normal linked and enabled on "
        "both, Coat Normal == Normal on CarbonMatte, no Bump with a constant "
        "Height")

    for nm, m in mats.items():
        m[REC_KEY] = json.dumps({"version": VERSION,
                                 "weave_pitch_m": WEAVE_PITCH_M,
                                 "nap_across_m": NAP_ACROSS_M,
                                 "sharp_keep_deg": a.sharp_deg})

    # ---- the creases -------------------------------------------------------
    cleared_total = 0
    for ob in objs:
        cleared_total += raise_sharp_threshold(ob, a.sharp_deg)

    bpy.context.scene.frame_set(a.frame)
    tot_a = dict(sharp=0, sharp_false_band=0, sharp_keep=0, sharp_up=0,
                 sharp_up_false_band=0, sharp_up_keep=0)
    for ob in objs:
        c = sharp_census(ob, a.sharp_deg)
        rep["sharp"]["after"][ob.name] = c
        for k in tot_a:
            tot_a[k] += c.get(k, 0)
    rep["sharp"]["after_total"] = tot_a
    rep["sharp"]["cleared"] = cleared_total
    log("SHARP AFTER   all CI_*: %d flagged (was %d), %d in the false band "
        "(was %d), %d up-facing (was %d)"
        % (tot_a["sharp"], tot_b["sharp"], tot_a["sharp_false_band"],
           tot_b["sharp_false_band"], tot_a["sharp_up"], tot_b["sharp_up"]))
    for nm in SEAT_OBJECTS:
        cb = rep["sharp"]["before"].get(nm)
        ca = rep["sharp"]["after"].get(nm)
        if cb and ca:
            log("   %-16s sharp %5d -> %5d   up-facing %5d -> %5d"
                % (nm, cb["sharp"], ca["sharp"], cb["sharp_up"], ca["sharp_up"]))
    if tot_a["sharp_false_band"] != 0:
        log("a sharp edge remains inside the false band — the clear did not take")
        print(">> STAGE RESULT: FAIL_SHARP_NOT_CLEARED")
        return 1

    # ---- the static guarantee ---------------------------------------------
    vh1, ah1 = static_fingerprint(objs)
    rep["static"] = {"verts_before": vh0, "verts_after": vh1,
                     "anim_before": ah0, "anim_after": ah1,
                     "unchanged": (vh0 == vh1 and ah0 == ah1)}
    if vh0 != vh1:
        log("VERTEX BUFFER CHANGED: %s -> %s" % (vh0[:16], vh1[:16]))
        print(">> STAGE RESULT: FAIL_GEOMETRY_MOVED")
        return 1
    if ah0 != ah1:
        log("ANIMATION CHANGED: %s -> %s" % (ah0[:16], ah1[:16]))
        print(">> STAGE RESULT: FAIL_ANIMATION_MOVED")
        return 1
    log("static guarantee HELD: every CI_* vertex and every CI_* fcurve is "
        "byte-identical (verts %s, anim %s)" % (vh1[:16], ah1[:16]))

    os.makedirs(os.path.dirname(outp), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=outp, compress=False, copy=False)
    log("wrote %s (%.1f MB)" % (outp, os.path.getsize(outp) / 1e6))

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(rep, open(a.json, "w"), indent=1)
        log("wrote %s" % a.json)

    print(">> STAGE RESULT: %s_OK" % RESULT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
