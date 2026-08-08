"""ACCEPTANCE GATE for the per-item hero asset campaign.

    /opt/blender-5.2.0-linux-x64/blender -b <item_module.blend> --factory-startup \
        -P tools/item_gate.py -- --item kerb_hero_t4 --out render/items/<id>/gate.json

WHY
---
    "1 agent per ITEM in every scene to build each item a trash can a water
     bottl the tire of the truck the haul etc. to extreme realesim and
     perfeciton etc."

435 items, one agent each, none of whom can see the others' work. Every one of
them will finish by reporting success. Without a gate that MEASURES the thing
they were asked for, the campaign produces 435 claims and no evidence.

WHAT WAVE 1 PROVED ABOUT THE OLD VERSION OF THIS FILE
-----------------------------------------------------
Wave 1 built 28 items. **All 28 passed this gate. All 15 that were then
adversarially pixel-peeped came back REWORK. Zero survived.** A gate with a 0 %
agreement rate against the bar it exists to protect is not a weak gate, it is a
measurement of something else. Specifically:

  * `material_depth` counted procedural texture NODES. `crew_fireproof_overall`
    has 28 and `spectator_seated` 51; both PASS; both render as vinyl. Node
    count is a property of the SHADER GRAPH. What the brief asks for is a
    property of the PIXELS. Those are different things and one does not imply
    the other -- the whole of `WAVE1-PEEP-SYNTHESIS.md` PATTERN 3 is the gap
    between them: "the mechanism is in the code and its amplitude is 3-5x too
    small to survive to pixels."

  * Nothing looked at a rendered image at all, so no check could see any defect
    that only exists in the image: a fabric with no weave, a trouser leg that
    is a machined cone, a pocket that is a printed rectangle rather than an
    object with a sunward lip and a lee shadow.

So this gate now RENDERS. Three of its checks are measured on pixels.

THE WITNESS FRAME, AND WHY THE GATE BUILDS IT ITSELF
----------------------------------------------------
Two ways to get an image were available: accept a PNG path from the agent, or
render one. **The gate renders one, from staging it builds itself.** The
tradeoff, stated plainly:

  Taking a PNG costs nothing and is fast. It also puts the single most
  load-bearing input to three checks under the control of the party being
  judged -- lens, distance, exposure, light, denoiser and framing all chosen by
  the agent whose work is on trial. Wave 1 is the argument against it: the peep
  found the item test scenes were being judged under light nobody had checked,
  and the whole synthesis document opens by throwing out every appearance-based
  conclusion drawn under it. A gate that inherits the subject's staging inherits
  the subject's staging bugs.

  Rendering costs a GPU job (~1-4 min on the 5090 via ~/vast-render/rq, a few
  cents). In exchange every number below is measured under staging this file
  wrote: this file's sun at the contract's 12.5 deg, this file's camera at the
  MANIFEST's `nearest_camera_m` and `lens_at_closest_mm`, this file's exposure,
  Standard view transform (not AgX -- a tone curve that compresses highlights
  is not something to measure contrast through), and this file's two reference
  primitives. Reproducible, comparable across all 435 items, and not
  negotiable by the agent.

  `--from-png` exists for re-analysis, and it REQUIRES the witness spec sidecar
  that staging wrote. A PNG with no sidecar is refused, because without it the
  gate cannot say which pixels are the control.

THE CONTROL IN THE FRAME
------------------------
Every render-based check is a COMPARISON AGAINST KNOWN-SMOOTH PRIMITIVES
RENDERED IN THE SAME FRAME -- a plain UV sphere, a plain plane, and a six-step
neutral wedge, all plain Principled, all under the same sun, the same sampling,
the same denoiser and the same 16-bit quantisation. This is not decoration.
From the peep of `crew_fireproof_overall`:

    maroon back panel   r1 0.89  r2 0.34  r4 0.49  r8 0.96  r16 1.33
    maroon thigh        r1 1.01  r2 0.50  r4 0.70  r8 0.85  r16 0.90
    STANDIN head (a smooth featureless ovoid) 1.52 / 0.86 / 1.06 / 1.34 / 1.66
    flat ground plane                         0.34 / 0.20 / 0.47 / 1.10 / 1.95

The fireproof fabric measured FLATTER THAN THE PLACEHOLDER BLOB HEAD. No
absolute threshold produces that finding; the comparison does. And an absolute
threshold is exactly what a denoiser change, a sample-count change or a view
transform change would silently invalidate -- the control moves with them.

A control only controls at the SUBJECT'S OWN BRIGHTNESS, because band contrast
is reported as a percentage of the patch mean and a small divisor flatters a
dark surface. A single-albedo sphere cannot do that job on its own: its dark
region is a rim a couple of pixels wide, which is exactly the rim every
band-pass has to erode away. Hence the wedge. Whichever controls are large
enough AND at the subject's brightness participate, and the bar is the
strictest of them; which ones spoke is recorded in every report.

ONE HONEST CAVEAT, MEASURED, NOT GUESSED
----------------------------------------
With OpenImageDenoise on at 512 samples, a genuinely plain smooth surface in
this rig reports a fine-band contrast of about 0.04 % of mean -- the denoiser
removes essentially all of it. So `surface_microstructure` is a comparison
against a floor near zero, and almost any surface clears it by two orders of
magnitude. It still catches a flat-shaded or untextured surface, which is worth
having, but it is NOT the discriminator the wave-1 numbers imply, and the reason
is that the peep's "STANDIN head" was not a clean primitive -- at 1.52 % it was
carrying something. `relief_reads_as_lip_and_shade` is the check that does the
discriminating work here. Said plainly rather than tuned around.

THE EIGHT CHECKS
----------------
  1. no_external_assets              binary, unchanged
 1b. relief_wiring_reaches_the_shader
                                     R2-072. Reads the BLEND, not the source:
                                     fails when a Bump / Normal Map / Bevel
                                     output lands on a shading node's
                                     non-normal input (on 5.2 the `Normal`
                                     off-by-one puts it on `Thin Wall`), when a
                                     relief node's output goes nowhere, when a
                                     Bump's Height is a constant or its Filter
                                     Width is driven. Rules shared with
                                     `tools/socket_index_audit.py --blend` via
                                     `tools/socket_blend_scan.py`; the
                                     edge-wear idiom is a NOTE, not a failure.
                                     Scoped to the WHOLE blend including
                                     context materials -- see `relief_wiring`.
                                     Pre-render, so a miswired item costs no
                                     GPU job and check 6 never gets to measure
                                     a flat surface without saying why.
  2. material_depth                  procedural texture nodes, unchanged.
                                     KEPT as a free pre-render floor: it can
                                     only ever add rejections, and a failure
                                     here saves a GPU job. It is no longer
                                     claimed to measure appearance.
  3. geometry_resolves_at_distance   10th-percentile edge in screen px, unchanged
  4. per_instance_variation          realized-instance walk, unchanged, PLUS
                                     `distinct_shapes`, which catches 420 source
                                     datablocks holding 6 actual poses
  5. surface_microstructure          RENDER. Two clauses, both referenced to
                                     the brightness-matched smooth control:
                                     AMPLITUDE (r1-r2 contrast at least twice
                                     the control's) and SPECTRAL BALANCE (the
                                     subject's fine/coarse ratio at least the
                                     control's). The second is what bites --
                                     it is "the mechanism is in the code and its
                                     amplitude is 3-5x too small to survive to
                                     pixels" written as a number. See the caveat
                                     above for why the first clause is weak.
  6. relief_reads_as_lip_and_shade   TWO RENDERS. Under a 12.5 deg raking sun a
                                     raised feature makes a bright sunward lip
                                     AND a dark lee shadow -- a dipole along the
                                     light. Measured as the depth of the
                                     along-light anticorrelation MINUS the
                                     across-light one, so a merely directional
                                     surface cannot fake it.
                                     THAT DIP IS NO LONGER THE WHOLE CHECK, and
                                     R2-060 is why: a flat quad -- four
                                     vertices, z identically zero, no modifier,
                                     no normal map -- painted with stripes
                                     ALIGNED to the light scores 0.63 against
                                     real 2 mm ribs' 1.01. After the band-pass a
                                     sharp albedo STEP and a lip-and-shadow are
                                     the same bipolar pair at the same spacing,
                                     and this statistic reads only the spacing.
                                     So the frame is now staged and rendered on
                                     BOTH candidate sun sides -- the side the
                                     picker chose and the one it rejected -- and
                                     the fine band is split into the half that
                                     MOVED with the light and the half that did
                                     not. Relief is in the first, paint is in
                                     the second, and the half that moved has to
                                     clear the same x2.00 over the same
                                     in-frame smooth control that check 5 uses.
                                     Measured: 0.02x on all four painted decoys
                                     including a HIGH-CONTRAST one and a
                                     roughness-only one, 1.00x on a plain plate
                                     and a plain cylinder, 2.16-2.61x on real
                                     ribs. See LIGHT_OVER_CONTROL.
  7. silhouette_departs_from_analytic  RENDER, flexible items only. Cloth is
                                     not a machined cone.

Plus `witness_frame_valid`, which is the gate checking its OWN instrument
before it reports anything measured with it -- subject and control populations,
clipping, and whether the control sphere's highlights are actually WARM, which
is the SYSTEMIC 1 signature the wave-1 peep opened with.

NOTHING HERE FALLS THROUGH TO A WEAKER STATISTIC
------------------------------------------------
R2-018 and R2-019 are both the same bug: a check that could not be evaluated
was reported as passed, once by saying so out loud and passing anyway, once by
quietly falling through to the chunk statistics one layer down. Every path in
this file that cannot measure its check sets it to `null`, writes a
`reason_unmeasurable` string saying what would make it measurable, and the item
is REJECTED. `all(checks)` is not used anywhere; the verdict requires every
gated check to be exactly `True`.

Every number reported is a physical quantity in real units, per R2-017.

The witness spec records `rig_version`. Any table of results across items should
be checked for having come out of ONE rig rather than assumed to have -- three
staging faults were found by rendering, looking, and measuring, and each one
invalidated every frame taken before it.
"""

import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

R2 = "/home/zany/f1-round2"
# The provenance stamp lives beside this file. Imported by path rather than by
# package, because item_gate runs inside Blender's interpreter with whatever
# cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as _prov                                       # noqa: E402
import gate_exit                                                 # noqa: E402
import socket_blend_scan as _sockets                             # noqa: E402

RQ = "/home/zany/vast-render/rq"
# The broker resolves symlinks and `..` and then requires the scene to sit
# inside one of its roots -- a client-supplied scene path becomes a filesystem
# path on the rented instance too, so it is a traversal vector and is checked
# as one. The witness .blend therefore always lands here, whatever --out or
# --witness-dir say, and the PNG and spec follow --out as usual.
WITNESS_BLEND_ROOT = os.path.join(R2, "render/gate_witness")

PROCEDURAL_TEX = {
    "TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MAGIC", "TEX_BRICK",
    "TEX_CHECKER", "TEX_GRADIENT", "TEX_MUSGRAVE", "TEX_WHITE_NOISE",
    "BUMP", "DISPLACEMENT", "VECT_DISPLACEMENT", "NEW_GEOMETRY",
    "BEVEL", "AMBIENT_OCCLUSION", "LAYER_WEIGHT", "FRESNEL",
}
# Nodes that carry actual surface history rather than just plumbing. A shader
# can have 40 Mix nodes and still be a flat colour.
TEXTURE_ONLY = {n for n in PROCEDURAL_TEX if n.startswith("TEX_")} | {
    "BUMP", "DISPLACEMENT", "VECT_DISPLACEMENT"}

SENSOR_MM = 36.0
RES_X_4K = 3840
RES_Y_4K = 2160

# ---------------------------------------------------------------------------
# WITNESS FRAME CONSTANTS -- the staging this gate builds for itself.
# ---------------------------------------------------------------------------
# The contract's sun. `ITEM-CAMPAIGN-BRIEF` and every item test scene built to
# it use 12.5 deg; the real solar disc is 0.53 deg across, which is what makes
# a shadow edge crisp enough for a 4 mm lip to read.
SUN_ELEV_DEG = 12.5
SUN_ANGLE_DEG = 0.526
# Sun 80 deg off the camera azimuth, camera 35 deg up, view 40 deg past
# perpendicular to the subject's long axis. Those three together, and not one of
# them for its own sake, because check 6 needs THE LIGHT TO RUN ACROSS THE
# SUBJECT'S FEATURES IN SCREEN SPACE and a 12.5 deg sun projects nearly
# horizontally in any level view. Measured on a rendered witness frame of
# `armco_w_beam`: the beam's corrugations ran within 15 deg of the projected
# light, so the light raked along the ridges instead of across them and the
# dipole the check looks for could not form in that view whatever the surface
# was like.
#
# Screen angle between the projected light and the projected long axis, which is
# the direction a guardrail's corrugation, a deck's boards, a kerb's arris and an
# extrusion's ribs all run:
#
#   cam 18 deg, view +30 past perpendicular, sun 65 off  ->  15.2 deg  (was this)
#   cam 30 deg, view +40 past perpendicular, sun 80 off  ->  28.9 deg
#   cam 35 deg, view +40 past perpendicular, sun 80 off  ->  30.5 deg  (is this)
#
# The sun's own 12.5 deg elevation is fixed by the contract and is not touched.
SUN_AZ_OFF_CAM_DEG = 70.0
# Irradiance, W/m^2. Calibrated so the reference sphere (Principled default,
# base colour 0.8) peaks near 0.68 linear = 0.85 sRGB: bright, unclipped, and
# leaving headroom for a specular lobe. See `calibration` in the report -- the
# gate measures the clipped fraction on the control every run and fails the
# frame if the exposure has drifted.
SUN_ENERGY = 2.5
# A 12.5 deg sun is warm, and `witness_frame_valid` relies on that: it measures
# R-B on the control sphere's brightest decile and refuses the frame if blue
# meets or beats red, which is the no-direct-sun signature WAVE1-PEEP SYSTEMIC 1
# opened with.
SUN_COLOR = (1.0, 0.94, 0.86)
SKY_COLOR = (0.30, 0.44, 0.70)
# THE FILL IS DELIBERATELY VERY LOW, AND THAT IS THE CONTROL'S DYNAMIC RANGE.
#
# The sphere is only a control for a given subject if some part of it is at the
# subject's brightness. Its bright end is fixed by the sun; its DARK end is set
# entirely by the sky fill, because a sphere's shadow side is lit by nothing
# else. Measured, on the first real item:
#
#   SKY 0.12 -> sphere floor 0.043 linear; timber deck measured 0.026 ->    0 px matched
#   SKY 0.07 -> sphere floor 0.025 linear; same deck at 0.034      -> 1350 px matched
#   SKY 0.025-> sphere floor 0.009 linear; range 0.009..0.64, a 70x span
#
# At 0.025 the sphere brackets everything from a black tyre in the light to a
# white panel facing the sun, which is what a universal control has to do. It
# also sharpens the lee shadows check 6 looks for. It is not a photometrically
# plausible sky, and it is not meant to be one -- this frame exists to be
# measured, not to be looked at, and the control moves with the lighting by
# construction.
SKY_STRENGTH = 0.025
CAM_ELEV_DEG = 35.0
# 512 samples with OpenImageDenoise, which is the project's own render setting,
# so the frame this gate judges is the frame a human peeper would be shown. The
# sample count is not load-bearing precisely BECAUSE the control is in the frame:
# more samples lower the control's floor and the subject's noise together. 512 at
# 3840x2160 renders in 6-7 s on the 5090; the wall time is queue and upload.
WITNESS_SAMPLES = 512
WITNESS_DENOISER = "OPENIMAGEDENOISE"

# Reference primitives: normalised device coords of their centres and their
# on-screen radius in pixels. Top of frame, because for a ground-plane item the
# top of frame is sky and the controls hang against nothing; for a tall item
# they cost about 2 % of the subject's pixels.
REF_SPHERE_NDC = (0.115, 0.845)
REF_PLANE_NDC = (0.885, 0.845)
# 240 px radius, not 150. The controls are measured only on pixels whose
# LUMINANCE MATCHES the subject's, which on a sphere is an annulus rather than a
# disc; at 150 px that annulus fell close to the minimum population for a
# standard deviation to mean anything. 480 px across costs 2.8 % of the frame
# each and leaves the matched band comfortably large.
REF_RADIUS_PX = 240.0
# The step wedge: NDC (x0, y0, x1, y1) of the strip, and its reflectance steps.
# Six steps ~2.4x apart against a 2.8x-wide matching window, so every subject
# brightness in 0.004..0.55 linear lands on one.
WEDGE_NDC = (0.28, 0.885, 0.72, 0.975)
WEDGE_ALBEDOS = (0.02, 0.05, 0.12, 0.28, 0.55, 0.95)
# Bumped whenever the staging geometry changes, and written into every witness
# spec, so a table of results can be checked for having come out of one rig
# rather than assumed to have.
RIG_VERSION = 6

# Band radii, in pixels, at which contrast is measured. All five are reported.
#
# WHICH ONES THE CHECK IS BUILT ON IS A COMPUTED CHOICE, NOT A PREFERENCE. The
# failure to detect is "all the energy at r8-r16 (2-4 cm) and none at r1-r4
# (3-11 mm)", so the fine aggregate must be blind to the coarse scale, or a soft
# AO mask gets credited with fabric it does not have. Measured response of the
# band-pass to a sinusoid, normalised at each band's own peak:
#
#     period      r1      r2      r4      r8     r16
#      3 px    0.466   0.111   0.000   0.000   0.000
#      6 px    0.261   0.466   0.111   0.000   0.000
#     12 px    0.040   0.261   0.466   0.111   0.000
#     25 px    0.003   0.035   0.241   0.471   0.132
#     50 px    0.000   0.003   0.035   0.241   0.471
#
# mean(r1,r2)     rejects a 25 px feature 19:1 against its 4-6 px peak
# mean(r1,r2,r4)  rejects the same feature only 3:1
#
# 19:1 is a discriminator. 3:1 is a leak, and the leak points the wrong way --
# it would let the exact wave-1 defect through. So r4 is reported and r1-r2
# decide. At 373 px/m that is 2.7 and 5.4 mm: weave, stitch, saw kerb, chip.
BANDS = (1, 2, 4, 8, 16)
FINE_BANDS = (1, 2)
COARSE_BANDS = (8, 16)

# A SUBJECT-SIZE FLOOR MUST NOT BE AN INVENTED ABSOLUTE. 200,000 px was the
# first value and it rejected `spectator_seated` outright: one seated figure at
# its own 14.7 m on a 28 mm lens is 254 px tall and covers 16,715 px, which is
# a fact about the manifest's framing, not a defect in the asset. Rejecting an
# item because the gate framed it small is the gate measuring itself.
#
# So this floor only asks "is there a subject in the frame at all". Whether any
# GIVEN band can be measured is decided per band, by population, after erosion
# (MIN_BAND_PX), and each band that cannot be measured says so with its own
# reason. 12,000 px is a hair above what survives erosion at r2 for a subject
# that small: it is the point below which no band can be measured either way.
MIN_SUBJECT_PX = 12_000
MIN_CONTROL_PX = 10_000
# A standard deviation over 8,000 samples has a relative error of about
# 1/sqrt(2n) = 0.8 %, which is far below any difference this gate rules on. The
# floor is here to reject slivers, not to chase precision.
MIN_BAND_PX = 8_000

# ---------------------------------------------------------------------------
# THRESHOLDS, AND WHICH OF THEM DEPEND ON HOW BIG THE THING ACTUALLY IS
# ---------------------------------------------------------------------------
# The manifest's `nearest_camera_m` is measured ABEAM -- 90 deg off travel,
# which at 35 mm is 63 deg outside the frame -- and beats 2-5 have no camera
# rig at all, so it is not yet known how big most of these items really are on
# screen. `docs/PLAN-scope-optimisation.md` puts the median correction at
# 373 -> 164 px. A gate whose thresholds are absolute pixel amplitudes would
# have to be re-tuned the day that number is re-derived, and re-tuning a gate
# is how a gate stops meaning anything.
#
# So every threshold below is one of two kinds, and the report says which:
#
#   SCALE-INVARIANT   a ratio against a control rendered in the SAME frame, at
#                     the SAME density, through the SAME denoiser. Changing the
#                     filmed distance moves subject and control together and
#                     the ratio survives. All three contrast/relief thresholds
#                     are of this kind.
#
#   PHYSICAL          a quantity in millimetres, which is a fact about cloth
#                     rather than about framing, and equally survives.
#
# There is exactly ONE size-dependent decision left -- whether the silhouette
# check is measurable at all at this item's density -- and it is a scoping test
# with the measured density printed beside it, not a threshold.
#
# `--filmed-distance-m` and `--onscreen-px-4k` let the caller supply the real
# numbers when task #61 re-derives them, without touching this file.

# 2.00: the subject's fine-band contrast must be at least twice that of the
# strictest smooth control in the same frame at the same brightness.
#
# This is a DETECTION THRESHOLD against a measured floor, not a taste threshold.
# A smooth control at the subject's brightness reports what this pipeline puts
# on a surface that has nothing on it -- residual noise after OpenImageDenoise,
# plus 16-bit quantisation. Twice that in standard deviation is four times in
# variance, so structure variance >= 3x noise variance, an amplitude SNR of 1.7.
# It is the weakest statement that means "there is something here".
#
# 1.0 was the first choice and is too weak: a vinyl surface sits AT the floor,
# so a coin-flip's worth of noise would carry it. SCALE-INVARIANT -- both terms
# are measured in the same frame at the same density through the same denoiser.
FINE_OVER_CONTROL = 2.00
# Margin over the control's own directional anisotropy. Set from the observed
# spread of that control across the wave-1 witness frames -- see
# `calibration_note` in each report.  SCALE-INVARIANT.
RELIEF_MARGIN = 0.030
# ... and an absolute floor, because a perfectly flat denoised control has almost
# no band energy at all and the correlation of near-zero noise is unstable in
# either direction, so `control + margin` alone can be satisfied by a control
# that happened to read slightly negative. 0.05 is over ten times what the
# index measures on structureless input in synthetic validation (pure noise
# +0.0013, isotropic printed marks -0.0041) and an eighth of what a genuine
# lip-and-shadow field measures (+0.445). Cross-checked against the smooth
# controls' own dip in every wave-1 witness frame.  SCALE-INVARIANT.
RELIEF_DIP_FLOOR = 0.05
# A control's dip is only a reference if the control has enough band energy for a
# correlation to mean anything, and a perfectly flat denoised patch sometimes does
# not. Measured across 23 witness frames the participating controls report dips of
# -0.223 .. +1.668 with a median of -0.075: 21 of the 23 sit inside +/-0.30 and
# the two outside it are the correlation of near-zero noise with itself.
# `gravel_bed_surface` was rejected by one such reading -- control +1.668 put the
# bar at +1.698, which nothing can clear -- so a control outside this band is
# discarded as degenerate and the absolute floor decides alone. Recorded in the
# report when it happens, because it is a weakening of the check and has to be
# visible.
RELIEF_CONTROL_SANE = 0.30
# ---------------------------------------------------------------------------
# R2-060. THE TWO-LIGHT SEPARATOR -- the clause that makes check 6 mean what it
# says. `relief_anisotropy` alone cannot tell a painted step from a lip and a
# shadow: a flat quad (4 verts, z identically 0, no modifier, no normal map)
# with 30 mm stripes ALIGNED to the light scores dip 0.6311 against 0.6082 for
# real 2 mm ribs. Both leave a bipolar pair at the same ~2r spacing after the
# band-pass, and the statistic reads only the spacing.
#
# The physical fact that separates them: a lip-and-shadow belongs to the LIGHT
# and an albedo step belongs to the SURFACE. Stage the sun on its OTHER
# candidate side -- the runner-up `sun_side_chosen` already rejects -- and the
# relief pattern inverts while the paint does not move.
#
# TWO THRESHOLDS, and each catches a case the other cannot:
#
#   LIGHT_OVER_CONTROL   the ANTISYMMETRIC half of the band -- the part that
#                        moved when the sun moved -- must be at least twice the
#                        smooth control's, exactly as `fine_over_control`
#                        demands of the total band. Without it the FLAT GREY
#                        PLATE passes: on a structureless surface the only thing
#                        in the band is its own directional shading, which
#                        inverts too, so rho reads -0.98 on nothing whatsoever.
#                        This clause is also what closes the amplitude hole --
#                        rho is a correlation and therefore blind to how much
#                        energy it is correlating, so a handful of sharp painted
#                        edges gives a near-perfect coefficient on almost no
#                        band. An AMPLITUDE referenced to the in-frame control
#                        cannot be satisfied by sparseness, and a HIGHER-contrast
#                        painted pattern adds its energy entirely to the
#                        symmetric half, so it does not help.
#                        Same 2.00 as FINE_OVER_CONTROL and for the same reason:
#                        twice the noise floor in sd is four times in variance.
#
#                        MEASURED on the extended control ladder, chosen sun
#                        against its runner-up, every ratio against a smooth
#                        control OF THE SAME SHAPE:
#
#                          real relief   b_rib_0p5mm     x2.37   RELIEF
#                                        c_rib_2mm       x2.61   RELIEF
#                                        d_rib_8mm       x2.16   RELIEF
#                                        l_cyl_rib_2mm   x7.94   RELIEF
#                          smooth        a_flat_0mm      x1.00   reject
#                                        j_cyl_flat      x1.00   reject
#                                        m_sph_flat      x1.00   reject
#                          paint         f_printed       x0.02   reject
#                                        g_aligned       x0.02   reject
#                                        h_hi_contrast   x0.03   reject
#                                        i_roughness     x0.02   reject
#                                        k_cyl_printed   x1.40   reject
#                                        n_sph_printed   x1.04   reject
#
#                        The two rows to read are the last two. THE CURVED
#                        PAINTED SPHERE has a dip of 0.6252 -- it defeats the
#                        statistic this check used to be -- and a fine-band
#                        contrast 25.45x the control, so it defeats check 5 by a
#                        factor of twelve as well. This is the only clause that
#                        rejects it. And it is curvature that makes it hard: on
#                        a curved surface the same paint renders as albedo times
#                        cos(i), and cos(i) is NOT the same under the two suns,
#                        so in linear luminance the paint's amplitude changes
#                        with the light and lands in the half reserved for
#                        relief. Hence the log; see LOG_FLOOR_FRAC.
#
#                        THE MARGIN AGAINST CURVED PAINT IS THE THIN PART OF
#                        THIS AND IT IS NOT HIDDEN. The log removes the SMOOTH
#                        part of log cos(i); near a shadow terminator cos(i) is
#                        small and changing fast, and what is left there is
#                        genuinely light-driven fine structure made by paint.
#                        The painted cylinder measures x1.40 at the gate's own
#                        runner-up geometry and x2.05 at a true 180 deg
#                        reversal -- i.e. it CROSSES this bar when the two suns
#                        are nearly opposed. That is measured, not feared; see
#                        `truth_table_A_vs_C.json`. It is the one case on the
#                        ladder where paint still passes, it is a smooth convex
#                        body (the worst shape for this test, because the two
#                        suns leave only a grazing band lit in common), and
#                        closing it needs either a shape-aware control or a
#                        third render. The bar is NOT raised to chase it: 3.00
#                        would reject real 8 mm ribs at x2.83 in the same
#                        column, which is a worse trade.
#
#                        A NULL, PROVEN RATHER THAN ASSUMED. Uncorrelated
#                        Monte-Carlo residual lands entirely in the light half,
#                        so "the band that moved" could in principle be nothing
#                        but noise. Rendering sun A TWICE at different seeds --
#                        the light does not move at all -- collapses it:
#                        real relief 11.6-16.2x smaller, the smooth controls
#                        4.6-23.4x smaller, and the flat painted decoys not at
#                        all (x0.7-1.8), i.e. their entire light-half was noise
#                        to begin with and their noise-subtracted signal is
#                        0.0000. The band this clause reads is the sun's.
LIGHT_OVER_CONTROL = 2.00
#   rho                  MEASURED AND REPORTED, DELIBERATELY NOT GATED, and
#                        this is a correction to the proposal rather than a
#                        detail. corr(chosen, flip) over the fine band is the
#                        obvious separator -- a lip and its shadow swap ends, a
#                        painted step does not -- and on the first ladder it
#                        looked total: ribs -0.4248 and -0.1833, both painted
#                        decoys +1.0000. It does not survive its own controls.
#
#                        Measured on the extended ladder, A vs B:
#
#                          b_rib_0p5mm   relief   rho -0.4897
#                          c_rib_2mm     relief   rho -0.0833
#                          d_rib_8mm     relief   rho -0.1014
#                          e_bolts_3mm   relief   rho +0.1003   <- POSITIVE
#                          a_flat_0mm    smooth   rho -0.8608   <- "relief"
#                          j_cyl_flat    smooth   rho +0.9193   <- "paint"
#                          paints        paint    rho +0.86 .. +0.9992
#
#                        `rho <= 0` would REJECT 3 mm chamfered bolt heads --
#                        the exact feature marshal_post_deck was failed for --
#                        and would pass a plain grey plate. The reason is
#                        physical and not fixable by moving the number: real
#                        relief carries a LIGHT-INVARIANT component too. A rib's
#                        flat top is bright under both suns, so a fixed
#                        geometric pattern sits in the band behaving exactly
#                        like paint, and rho is the ratio of that to the part
#                        that moves. Sparse relief is mostly flat top.
#                        Kept in the report because it reads well beside the
#                        amplitude -- +0.99 says "this surface's fine band is
#                        the same picture under both suns" -- but a number that
#                        puts a smooth cylinder and a painted one in the same
#                        bin cannot be the thing that decides.
# The band-pass is taken in LOG luminance for the two-light pair, and that is
# load-bearing rather than cosmetic. On a CURVED painted surface the same paint
# renders as albedo*cos(i), and cos(i) differs between the two sun sides -- so in
# linear luminance the painted pattern's AMPLITUDE changes with the light even
# though the pattern itself does not move, and the antisymmetric half picks up
# a scaled copy of the paint. In log luminance that contamination is an ADDITIVE
# slowly-varying term, log cos(i), which a fine band-pass removes outright. What
# is left is log(albedo), identical under both suns. Measured on a painted
# cylinder and a painted sphere; see `tools/relief_control_measure.py --measure2`.
# The floor keeps log() away from zero and is a fraction of the frame's own
# subject mean, so it is scale-invariant like everything else here.
LOG_FLOOR_FRAC = 0.02
# Real cloth at the stated LAMBDA_HANG of 112 mm should perturb a silhouette by
# 5-10 mm; crew_fireproof_overall measured 1.6 mm. 5.0 is the BOTTOM of the
# stated physical range, so it is the most permissive reading of the evidence
# that still rejects a machined cone.  PHYSICAL, in millimetres.
SIL_RMS_MM = 5.0
# ... and it must also beat the instrument. The control sphere's own outline is
# an exact analytic curve, so whatever the sub-pixel edge estimator reports on IT
# -- measured with the identical 100-row local refit -- is this frame's noise
# floor. 3x that floor.  SCALE-INVARIANT.
SIL_OVER_CONTROL = 3.0
# Below this the 5 mm bar is under one pixel at the item's own closest framing,
# so fold language cannot be seen at any point in the film and the check is
# out of scope rather than failed. The density is printed with the verdict.
SIL_MIN_PX_FOR_5MM = 1.0


# ---------------------------------------------------------------------------
# FLEXIBLE ITEMS
# ---------------------------------------------------------------------------
# Check 7 asks whether a silhouette departs from its analytic form. That is the
# right question for cloth and the WRONG question for a precast kerb, whose
# silhouette had better be a straight line. So the check needs a classification,
# and the classification is the reviewable artefact: token rules over the
# manifest's own `id` and `name`, printed in every report, with the compounds
# that break them listed explicitly.
#
# It is deliberately NOT a command-line switch that can turn the check OFF. A
# knob an agent can use to make a failing check inapplicable is not a gate.
# `--flexible` can only force it ON.
# Things that ARE cloth, or hang like it.
CLOTH_TOKENS = (
    "overall", "overalls", "race suit", "racesuit", "garment", "clothing",
    "cloth", "fabric", "scrim", "banner", "blanket", "tarp", "tarpaulin",
    "awning", "canopy", "drape", "draped", "flag", "glove", "gloves",
    "balaclava", "hose", "loom", "strap", "webbing", "windsock", "coat",
    "cushion", "upholstery", "towel", "rag", "curtain", "belt facing",
)
# A HUMAN wearing clothes is a flexible subject -- "the garments are inflated
# balloons wearing a moulded plastic bib" is a wave-1 verdict. But the token
# `marshal` alone also matches `marshal_water_cooler`, and a water cooler's
# outline had better be analytic. So a person family token only counts WITH a
# token that says the item is the person rather than their equipment.
PERSON_TOKENS = ("crew", "marshal", "spectator", "driver", "crowd",
                 "paddock personnel", "team principal", "photographer",
                 "steward")
FIGURE_TOKENS = ("figure", "seated", "standing", "kneeling", "leaning",
                 "operator", "mechanic", "gunner", "carrier", "technician",
                 "engineer", "adjuster", "cleaner", "principal",
                 "photographer", "steward", "child", "personnel",
                 "stabiliser", "flagging", "general admission")
# Compounds where a cloth-sounding token names a rigid thing. Checked first.
RIGID_COMPOUNDS = (
    "curtain wall", "manhole cover", "duct cover", "flagpole", "flag rack",
    "flag pole", "seat bracket", "cable ramp", "cable duct", "junction box",
    "hose reel", "reel drum", "cover plate", "tool chest", "belt pack",
    "beltpack", "row letter", "number plate", "sill extrusion",
    "head extrusion", "roof sheet", "profiled metal", "light panel",
    "overhead canopy", "handrail", "helmet",
)
FLEX_FORCE = {            # named because token rules cannot see them
    "tyre_blanket", "crew_fireproof_overall", "spectator_seated",
    "spectator_seated_leaning", "spectator_clothing", "driver_race_suit",
    "driver_figure", "marshal_overall", "garage_spare_car_covered",
    "crowd_banner_draped", "spectator_bag_and_coat", "litter_paper_scrap",
    "garage_curtain_divider", "tv_camera_cable", "wheel_gun_hose",
    "spectator_umbrella",
}
RIGID_FORCE = {           # named because token rules over-reach on them
    "mullion_intact", "hospitality_deck", "grandstand_seat",
    "timing_stand_seat", "truck_side_skirt", "grandstand_skirt",
    "track_manhole_cover", "paddock_manhole_cover", "paddock_duct_cover",
    "grandstand_riser_unit", "marshal_post_deck", "marshal_post_column",
    "marshal_flag_rack", "flagpole", "tool_chest", "cable_reel_drum",
    "air_hose_reel", "crew_radio_beltpack", "grandstand_row_letter",
    "info_gate_sign", "apron_wall_coping", "crew_helmet_visor",
    "driver_helmet", "grandstand_roof_sheet", "marshal_light_panel",
    "garage_door_overhead", "spectator_ear_defenders", "spectator_headwear",
    "grandstand_litter_bin", "spectator_entrance_gate",
    "spectator_folding_stool", "spectator_backpack_coolbox",
    "crew_kneeling_pad", "crew_headset", "crew_headset_full",
    "marshal_access_gate", "leaf_litter", "grass_clipping_drift",
    "timing_stand_canopy", "awning_leg", "tyre_blanket_controller",
    "driver_boots_and_feet", "driver_gloves", "crew_gloves_and_boots",
    "photographer_rig", "glass_panel_prefractured",
}


def classify_flexible(rec, forced):
    """(is_flexible, why). Deterministic, printed, and never weakened by a flag.

    The list above IS the artefact to review; there is no CLI switch that turns
    this check off, because a switch an agent can use to make a failing check
    inapplicable is not a gate. Verified by running it over all 435 manifest
    entries and reading the output -- 56 flexible, 379 rigid. It will be wrong
    on some of the 407 items nobody has built yet; a wrong classification shows
    up in the report as a named reason, which is a thing a reader can correct,
    not a silent pass.
    """
    ident = rec["id"]
    text = re.sub(r"[_\-/]+", " ", (ident + " " + rec.get("name", "")).lower())
    if forced:
        return True, "forced ON by --flexible (can only strengthen)"
    if ident in RIGID_FORCE:
        return False, f"'{ident}' is in RIGID_FORCE"
    if ident in FLEX_FORCE:
        return True, f"'{ident}' is in FLEX_FORCE"
    for c in RIGID_COMPOUNDS:
        if c in text:
            return False, f"rigid compound '{c}' in id/name"
    for t in CLOTH_TOKENS:
        if re.search(r"\b" + re.escape(t) + r"\b", text):
            return True, f"cloth token '{t}' in id/name"
    p = next((t for t in PERSON_TOKENS
              if re.search(r"\b" + re.escape(t) + r"\b", text)), None)
    if p:
        f = next((t for t in FIGURE_TOKENS
                  if re.search(r"\b" + re.escape(t) + r"\b", text)), None)
        if f:
            return True, f"a clothed human: '{p}' + '{f}' in id/name"
        return False, (f"'{p}' names the family, not a person wearing cloth "
                       f"(no figure token in id/name)")
    return False, "no cloth token and no clothed-human pattern in id/name"


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    # R2-060: `--stage-flip` retrofits the other-sun-side blend onto a witness
    # that was staged before the two-light clause existed. It needs no item and
    # no report, so it does not demand them.
    need = "--stage-flip" not in argv
    p.add_argument("--stage-flip", default=None,
                   help="mirror the sun of an EXISTING witness .blend onto its "
                        "other candidate side, write `<stem>_flip.blend` beside "
                        "it, and stop. For witnesses staged before R2-060.")
    p.add_argument("--item", required=need)
    p.add_argument("--out", required=need)
    p.add_argument("--manifest", default=os.path.join(R2, "docs/item_manifest.json"))
    p.add_argument("--prefix", default=None,
                   help="object-name prefix identifying this item")
    p.add_argument("--collection", default=None,
                   help="collection holding this item; beats auto-detection")
    p.add_argument("--subject", default=None,
                   help="name the object to frame in the witness render. "
                        "Default is the MEDIAN-triangle-count object of the "
                        "item, i.e. the typical instance, not the best one. "
                        "Recorded in the report when overridden.")
    p.add_argument("--flexible", action="store_true",
                   help="force the silhouette check ON. There is deliberately "
                        "no switch to force it off.")
    p.add_argument("--samples", type=int, default=WITNESS_SAMPLES)
    p.add_argument("--witness-dir", default=None,
                   help="where the witness .png and spec go. Default is "
                        "render/gate_witness/<item>/, on real disk -- a 4K "
                        "16-bit RGBA frame is ~60 MB and the scratch tmpfs is "
                        "RAM. The witness .blend always goes there regardless, "
                        "because the broker only accepts scenes inside its "
                        "permitted roots.")
    p.add_argument("--from-png", default=None,
                   help="skip rendering and analyse this PNG. REQUIRES the "
                        "witness spec sidecar written by a previous staging "
                        "run; without it the control regions are unknown and "
                        "the gate refuses rather than guessing.")
    p.add_argument("--from-png-flip", default=None,
                   help="R2-060. The same frame rendered on the OTHER candidate "
                        "sun side, for the paint-vs-geometry clause of the "
                        "relief check. Defaults to `<from-png stem>_flip.png` "
                        "beside it. Without it the relief check reports NOT "
                        "MEASURED, because the dip on its own cannot tell a "
                        "painted step from a lip and a shadow.")
    p.add_argument("--stage-only", action="store_true",
                   help="write the witness blend + spec and stop. The "
                        "render-based checks are then unevaluated, so the "
                        "result is REJECTED -- this is for debugging staging.")
    p.add_argument("--local-render", action="store_true",
                   help="render the witness frame with THIS Blender instead of "
                        "the 5090 broker. Slow, and recorded in the report.")
    p.add_argument("--always-render", action="store_true",
                   help="render even when a pre-render check already failed. "
                        "Adds measurements; never removes a rejection.")
    p.add_argument("--rq", default=RQ)
    p.add_argument("--timeout", type=int, default=5400)
    # The manifest's framing numbers are known to be wrong for most items --
    # measured abeam, from a camera corridor that does not exist for beats 2-5.
    # These let a corrected figure be supplied without editing this file or the
    # manifest. Whichever was used is recorded in every report.
    p.add_argument("--filmed-distance-m", type=float, default=None,
                   help="override the manifest's nearest_camera_m for the "
                        "witness framing")
    p.add_argument("--onscreen-px-4k", type=float, default=None,
                   help="override the manifest's onscreen_px_4k (reported, and "
                        "used for triangles-per-onscreen-pixel)")
    return p.parse_args(argv)


def item_record(manifest, item_id):
    for it in manifest["items"]:
        if it["id"] == item_id:
            return it
    raise SystemExit(f"REFUSING: '{item_id}' is not in the item manifest. "
                     "The manifest is the single source of truth for what "
                     "exists; an item that is not in it should not be built.")


# ===========================================================================
# PART 1 -- THE MESH-SIDE CHECKS. Unchanged from the version that shipped
# wave 1, except that per-object triangle counts are now captured on the way
# past (the witness render needs them to pick the median instance) and
# `distinct_shapes` is added to the realized-instance walk.
# ===========================================================================

def edge_stats_m(objs, deps):
    """Edge-length distribution over the EVALUATED meshes, in metres.

    Evaluated because SUBSURF and BEVEL are exactly the modifiers that turn a
    coarse cage into resolved geometry; judging the base mesh would fail every
    correctly-built object.

    THE MEDIAN IS THE WRONG STATISTIC and the first version of this gate used
    it. Most of a guardrail is smooth beam whose edges are legitimately long;
    demanding a 4 mm median would demand millions of triangles of flat panel.
    What the check is actually asking is "does this object carry detail at the
    scale the lens resolves" -- an existence question, not an average.

    So the deciding number is the 10th percentile: the fine end of the
    distribution. If even the finest decile of edges is coarser than a screen
    pixel, the object has no resolvable detail ANYWHERE and no amount of
    smooth panel can excuse it. The median is still reported, as advice.
    """
    lens = []
    for ob in objs:
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        sx, sy, sz = ob.matrix_world.to_scale()
        s = (abs(sx) + abs(sy) + abs(sz)) / 3.0
        for e in me.edges:
            a = me.vertices[e.vertices[0]].co
            b = me.vertices[e.vertices[1]].co
            lens.append((a - b).length * s)
        oe.to_mesh_clear()
    if not lens:
        return None
    lens.sort()
    return {"p10": lens[len(lens) // 10], "median": lens[len(lens) // 2],
            "p90": lens[min(len(lens) * 9 // 10, len(lens) - 1)],
            "n_edges": len(lens)}


def tri_count(objs, deps):
    """Total triangles, and the per-object counts the subject picker needs."""
    n = 0
    per = {}
    for ob in objs:
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        k = 0
        for p in me.polygons:
            k += max(len(p.vertices) - 2, 1)
        per[ob.name] = k
        n += k
        oe.to_mesh_clear()
    return n, per


def material_depth(objs):
    """Procedural texture nodes actually reachable from each material's output.

    Counting every node in the tree would reward an agent for leaving orphaned
    nodes lying around. Only what feeds the surface counts.

    THIS NUMBER DOES NOT MEASURE APPEARANCE and wave 1 proved it: 28 nodes on
    `crew_fireproof_overall`, 51 on `spectator_seated`, both vinyl. It is kept
    only as a free floor -- it can add a rejection, never remove one, and a
    failure here saves the GPU job that checks 5-7 need.
    """
    seen_mats, tex_nodes, all_nodes, img_nodes = set(), 0, 0, 0
    for ob in objs:
        for slot in ob.material_slots:
            m = slot.material
            if not m or m.name in seen_mats or not m.use_nodes:
                continue
            seen_mats.add(m.name)
            nt = m.node_tree
            out = next((n for n in nt.nodes
                        if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
            if out is None:
                continue
            stack, reached = [out], set()
            while stack:
                n = stack.pop()
                if n.name in reached:
                    continue
                reached.add(n.name)
                for inp in n.inputs:
                    for lk in inp.links:
                        stack.append(lk.from_node)
            for name in reached:
                n = nt.nodes[name]
                all_nodes += 1
                if n.type == "TEX_IMAGE":
                    img_nodes += 1
                if n.type in TEXTURE_ONLY:
                    tex_nodes += 1
    return {"materials": len(seen_mats), "reachable_nodes": all_nodes,
            "procedural_texture_nodes": tex_nodes, "image_texture_nodes": img_nodes}


def relief_wiring(objs):
    """CHECK 1b -- R2-072. Does the relief actually REACH the shader?

    WHY THIS CHECK IS HERE AND NOT SOMEWHERE ELSE
    ---------------------------------------------
    R2-057 and R2-070 are the same defect twice: a bump chain built in full and
    then wired to a socket that is not `Normal`, because Blender 5.2 moved
    `Normal` from index 5 to 6 and put `Thin Wall` where it used to be. No
    error, no black frame, a completely plausible render, and the relief
    repair it was meant to deliver moves 0.00 % of the pixels.

    `tools/socket_index_audit.py` catches it two ways -- an AST arm over source
    and an artefact arm over a built blend. The artefact arm was the one that
    mattered, and R2-071 recorded why: a source fix is not landed until the
    artefact downstream of it has been rebuilt AND RE-READ. Four blends sat on
    disk carrying a defect whose source fix was months old.

    So the artefact arm needed a gate that runs it. The two candidates were
    `campaign_preflight` and this file, and this file wins on three counts:

      * PREFLIGHT IS PER-ITEM AND PRE-BUILD. It checks a module before its
        agent starts. There is no artefact at that point -- the whole content
        of R2-071 is that source and artefact disagree, so a check that can
        only see source cannot close it.
      * THIS GATE ALREADY HAS THE BLEND OPEN. It is invoked as
        `blender -b <item>.blend -P item_gate.py`, so the scan costs a few
        milliseconds of graph walk. Running the same arm from preflight would
        mean spawning a second Blender to reopen a file up to 2.4 GB.
      * A VERDICT ALREADY DEPENDS ON THE ANSWER. Check 6 asks whether the
        surface reads as lip and shade. If the bump never reached the shader,
        check 6 is measuring a flat surface and will say so without ever
        saying WHY. This check names the cause, and it fails BEFORE the GPU
        job, so a miswired item costs no render.

    WHOSE MATERIALS COUNT
    ---------------------
    Every node tree in the blend, and the report says which are the item's own
    and which are not. That is deliberate. In R2-070 the miswired materials
    were `CTX_*` CONTEXT materials -- the ground and abutments an item module
    builds to light and site itself -- and `gantry_truss` and `pont_girder`
    were ACCEPTED with them broken. Scoping this check to the item's own
    material slots would have passed both. The blend an item is judged from is
    the item's artefact, context included.

    That is not an argument, it is the measurement. Run against the shipped
    `gantry_truss` test scene rebuilt with the R2-070 wiring deliberately
    restored, this check reports `0 on this item's own materials, 1 elsewhere
    in the blend` and FAILS -- and an item-scoped version of it would have
    said PASS to the very defect it exists for.

    AND THE COST OF THAT SCOPE WAS MEASURED TOO, because a check that fails
    most of the corpus is a check somebody switches off. All 32 item test
    blends on disk were scanned with these rules on 2026-08-03: 32 PASS,
    0 fail. Two carry NOTE-level findings and both of them are
    `armco_w_beam`'s Bevel-dotted-with-geometry-normal edge-wear mask, which
    is the idiom this must never fail. Whole-blend scope costs zero false
    rejections across the entire item campaign.
    """
    data = _sockets.scan_open_blend()
    findings = data["findings"]
    fails = _sockets.failing(findings)
    notes = [f for f in findings if f.get("severity") == "NOTE"]

    mine = set()
    for ob in objs:
        for slot in ob.material_slots:
            if slot.material:
                mine.add(slot.material.name)

    def bucket(f):
        return "item" if (f["kind"] == "material" and f["owner"] in mine) \
            else "other"

    rows = []
    for f in sorted(fails, key=lambda x: (x["rule"], x["owner"], x["node"])):
        shell = f.get("shell") or []
        carries = any((s.get("Transmission Weight") or {}).get("value")
                      or (s.get("Transmission Weight") or {}).get("linked")
                      or (s.get("Subsurface Weight") or {}).get("value")
                      or (s.get("Subsurface Weight") or {}).get("linked")
                      for s in shell)
        rows.append({
            "rule": f["rule"], "scope": bucket(f), "kind": f["kind"],
            "owner": f["owner"], "node": f["node"],
            "to_socket": f.get("to_socket"),
            "detail": f["detail"],
            # A stray relief link is merely FLAT on an opaque material and a
            # per-pixel shell flip on one that carries transmission or
            # subsurface. Measured here, never assumed.
            "shell_carries_transmission_or_subsurface": bool(carries),
        })
    return {
        "ok": not fails,
        "trees_scanned": data["scanned_trees"],
        "item_materials": sorted(mine),
        "failing": rows,
        "failing_on_item_materials": len([r for r in rows if r["scope"] == "item"]),
        "failing_elsewhere_in_blend": len([r for r in rows if r["scope"] == "other"]),
        # The edge-wear idiom -- a Bevel normal dotted with the geometry
        # normal -- looks exactly like the defect and is correct. Recorded, not
        # failed. See socket_blend_scan's docstring.
        "computation_notes": [
            {"owner": f["owner"], "node": f["node"],
             "to_node": f.get("to_node"), "to_socket": f.get("to_socket")}
            for f in notes],
    }


def _shape_signature(me):
    """A quantised fingerprint of one source mesh's SHAPE.

    Coarse on purpose: bbox to 10 mm and volume to 1 %, so a millimetre of
    vertex jitter does not read as a new shape, while a genuinely different
    pose does. Vertex and triangle counts are exact because two poses of one
    body rarely share both.
    """
    if not me.vertices:
        return None
    xs = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", xs)
    xs = xs.reshape(-1, 3)
    d = xs.max(axis=0) - xs.min(axis=0)
    vol = float(max(d[0], 1e-6) * max(d[1], 1e-6) * max(d[2], 1e-6))
    return (len(me.vertices), len(me.polygons),
            int(round(d[0] * 100)), int(round(d[1] * 100)), int(round(d[2] * 100)),
            int(round(math.log(max(vol, 1e-12)) * 100)))


def _scale_invariant_key(sig):
    """`_shape_signature` with UNIFORM SCALE divided out.

    RECORDED, NOT GATED (R2-1381).  A builder that bakes a per-copy scale into
    the vertex data rather than the object matrix produces N signatures from
    one body: the bounding box is quantised in metres, so 4,500 sizes of one
    tree are 4,500 "shapes" to the fingerprint and one tree to the eye. Divided
    by its own largest side, that family collapses back to a single key.

    It is not a check because it cannot distinguish that failure from a
    legitimate library whose bodies share a topology and an aspect ratio --
    jittered copies of one generator differ by millimetres, which is under the
    quantisation, and gating on this would reject them. So the number is put in
    the report where a reader can see it, and the rule stays on what it can
    prove. The residual is named in `docs/STAGING-R2-2941-to-R2-3000.md`.
    """
    if sig is None:
        return None
    nv, npoly, bx, by, bz = sig[0], sig[1], sig[2], sig[3], sig[4]
    m = max(bx, by, bz, 1)
    return (nv, npoly, round(bx / m, 2), round(by / m, 2), round(bz / m, 2))


# THE VARIETY LAW LIVES HERE, ONCE.  (R2-1381.)
#
# It used to live in two places with two different strengths: realized
# geometry-nodes instances were held to 8-40 distinct sources, 8-40 distinct
# SHAPES and no shape over 25 % of the population, while anything emitting
# PLAIN OBJECTS was asked for a size CV of 0.03 and two distinct triangle
# counts. The second is satisfied by 4,500 copies of two meshes at slightly
# different scales -- which is, verbatim, the failure the check exists to
# catch: "i dont want repeat stuff aka one tree spammed 100 times".
#
# Nineteen of the 32 wave-1 items took the weak path, four of them declaring
# 900-3,641 instances. It had not yet produced a false accept. Nothing
# prevented one, and the tree tier -- 11 of the top 11 items by screen time --
# was about to be built straight through it (`docs/WAVE2-RANKING.md` §5).
TOP_SHARE_LIMIT = 0.25
CV_SIZE_FLOOR = 0.03


def need_distinct_shapes(n):
    """How many distinct shapes a population of `n` must show.

    `max(8, min(40, sqrt(n)))` is the number the realized-instance path has
    always used: eight at the small end, forty at 1,600 instances and above.

    THE `min(n, ...)` IS NOT A RELAXATION. Without it a population of seven
    objects is asked for eight distinct shapes, which no population of seven
    can ever contain: that is an arithmetically impossible requirement, not a
    strict one, and it would fail `pont_girder` (7 objects, 7 different bodies,
    ACCEPTED) for being small rather than for being repetitive. Where it binds,
    `top_share_limit` still does the work. Verified not to move any shipped
    verdict: every realized-instance population on disk is 10 or larger, where
    `min(n, ...)` is a no-op.
    """
    return min(n, max(8, min(40, int(math.sqrt(n)))))


def top_share_limit(n):
    """No single shape may be more than a quarter of the population.

    Same reasoning as the `min(n, ...)` above: at n < 4 a 25 % share is
    unreachable even when every single object is unique, so the limit relaxes
    to exactly "not two of the same". At n >= 4 this returns 0.25 and is the
    rule as it has always been.
    """
    return max(TOP_SHARE_LIMIT, 1.0 / max(n, 1))


def variation_verdict(declared, var, real, gn_instanced):
    """THE ONE PLACE `per_instance_variation` IS DECIDED.

    Extracted from `main()` so that the false accept can be run against it
    directly -- `tools/r2_1381_variety_control.py` builds 4,500 plain objects
    from two meshes and watches this function refuse them, and builds 4,500
    from forty bodies and watches it accept them. A rule that is only ever
    exercised through a 40-minute item gate is a rule nobody tests.

    Annotates `var` and `real` in place with the thresholds actually applied,
    so the report says what was required and not merely what was found.
    """
    if declared <= 1:
        return True

    if real:
        # `distinct_sources` catches "one tree spammed 100 times".
        # `distinct_shapes` catches its sequel: 420 datablocks holding 6 poses,
        # which is what the rebuilt spectator crowd actually is.
        n = real["realized"]
        need, limit = need_distinct_shapes(n), top_share_limit(n)
        real["distinct_sources_required"] = need
        real["distinct_shapes_required"] = need
        real["top_source_share_limit"] = limit
        real["top_shape_share_limit"] = limit
        return (real["distinct_sources"] >= need
                and real["distinct_shapes"] >= need
                and real["top_source_share"] <= limit
                and real["top_shape_share"] <= limit)

    if gn_instanced:
        # UNPROVEN IS NOT A PASS (R2-019). No fallthrough to chunk statistics.
        return False

    # ---- PLAIN OBJECTS: the same law, on the same terms ------------------
    # `distinct_topologies` is `len(set(triangle_count))`, and a triangle count
    # is a weak proxy for a shape: two entirely different bodies with the same
    # count collide, and the old floor of 2 was clearable by any pair of
    # meshes at any population. The population is now fingerprinted with
    # `_shape_signature` -- the SAME function the realized-instance path uses,
    # not a second one -- and held to the same count and the same 25 % ceiling.
    # `cv_size` and the topology floor are kept as well: this is strictly
    # additive, nothing that failed before passes now.
    n = var["n"]
    need, limit = need_distinct_shapes(n), top_share_limit(n)
    var["distinct_shapes_required"] = need
    var["top_shape_share_limit"] = round(limit, 4)
    return (var["cv_size"] is not None and var["cv_size"] >= CV_SIZE_FLOOR
            and var["distinct_topologies"] >= 2
            and var.get("distinct_shapes") is not None
            and var["distinct_shapes"] >= need
            and var.get("top_shape_share") is not None
            and var["top_shape_share"] <= limit)


def realized_instances(deps, want_names):
    """Measure the instances GEOMETRY NODES ACTUALLY EMITS, not the chunks.

    The first version of this gate could only see the 260 chunk objects that
    carry 7,800 spectators. It said so honestly in the report -- and then set
    `per_instance_variation: true` anyway, passing a check it had just declared
    itself unable to evaluate. That is R2-018 with a different label: a PASS
    emitted on something that was never measured. It let through the grandstand
    crowd the user rejected as mannequins.

    `depsgraph.object_instances` walks the REALIZED instances, each with the
    source geometry it references and its own world matrix, which is exactly
    the data the named failure lives in:

        "i dont want repeat stuff aka one tree spammed 100 times"

    DISTINCT SOURCES IS NOT ENOUGH ON ITS OWN, and wave 1 showed why. The
    rebuilt `spectator_seated` reports 420 distinct source datablocks over
    7,420 realized instances -- comfortably over the required 40 -- and the
    peep still says "~6 poses". 420 datablocks holding 6 shapes satisfies a
    datablock count and satisfies nothing else. So the shapes are fingerprinted
    too, and BOTH have to clear the bar.
    """
    from collections import Counter
    srcs = Counter()
    shapes = Counter()
    sig_cache = {}
    scales, rots, n = [], [], 0
    for inst in deps.object_instances:
        if not inst.is_instance:
            continue
        parent = inst.parent
        if parent is not None and want_names and parent.name not in want_names:
            continue
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        n += 1
        key = ob.data.name if ob.data else ob.name
        srcs[key] += 1
        if key not in sig_cache:
            try:
                sig_cache[key] = _shape_signature(ob.data)
            except Exception:
                sig_cache[key] = ("UNREADABLE", key)
        shapes[sig_cache[key]] += 1
        m = inst.matrix_world
        s = m.to_scale()
        scales.append((abs(s.x) + abs(s.y) + abs(s.z)) / 3.0)
        e = m.to_euler()
        rots.append((e.x, e.y, e.z))
    if not n:
        return None

    def cv(xs):
        mu = statistics.mean(xs)
        return (statistics.pstdev(xs) / mu) if abs(mu) > 1e-9 else 0.0

    rot_sd = [round(math.degrees(statistics.pstdev([r[i] for r in rots])), 2)
              for i in range(3)] if len(rots) > 1 else [0.0, 0.0, 0.0]
    return {"realized": n, "distinct_sources": len(srcs),
            "distinct_shapes": len(shapes),
            "top_source_share": round(srcs.most_common(1)[0][1] / n, 4),
            "top_shape_share": round(shapes.most_common(1)[0][1] / n, 4),
            "cv_scale": round(cv(scales), 5) if len(scales) > 1 else 0.0,
            "rot_sd_deg": rot_sd}


def instance_variation(objs, deps, per_tris):
    """Spread across instances. Identical copies score 0.0 and fail.

    Measures the SHAPE of each instance, not just its transform: rotating one
    mesh randomly is the exact failure the user named, and a transform-only
    metric would pass it.

    THE SHAPES ARE FINGERPRINTED HERE TOO (R2-1381). This function used to
    report `distinct_topologies` -- `len(set(triangle_count))` -- as its only
    account of how many different bodies were on screen, and `variation_verdict`
    had nothing better to gate on. It now runs `_shape_signature`, the same
    fingerprint the realized-instance path uses, over each object's evaluated
    mesh. It costs nothing: the evaluated mesh is already in hand for the
    bounding box.

    The signature is taken in the object's LOCAL space on purpose, exactly as
    it is for a geometry-nodes source. A per-object scale in the matrix is a
    transform, not a shape, and a hundred sizes of one tree must read as one
    shape or the check is back where it started.
    """
    from collections import Counter
    dims, vols, tris = [], [], []
    shapes, srcs, families = Counter(), Counter(), Counter()
    boxes = {}
    for ob in objs:
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None or not me.vertices:
            continue
        mw = ob.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        d = hi - lo
        boxes[ob.name] = (lo.copy(), hi.copy())
        dims.append(d.length)
        vols.append(max(d.x, 1e-6) * max(d.y, 1e-6) * max(d.z, 1e-6))
        tris.append(per_tris.get(ob.name, 0))
        try:
            sig = _shape_signature(me)
        except Exception:
            sig = ("UNREADABLE", ob.name)
        shapes[sig] += 1
        families[_scale_invariant_key(sig)] += 1
        srcs[ob.data.name if ob.data else ob.name] += 1
        oe.to_mesh_clear()

    def shape_stats(total):
        if not total:
            return {"distinct_shapes": None, "top_shape_share": None,
                    "distinct_source_meshes": None,
                    "distinct_shapes_scale_invariant": None}
        return {"distinct_shapes": len(shapes),
                "top_shape_share": round(shapes.most_common(1)[0][1] / total, 4),
                "distinct_source_meshes": len(srcs),
                # recorded, not gated -- see `_scale_invariant_key`
                "distinct_shapes_scale_invariant": len(families)}

    if len(dims) < 2:
        return dict({"n": len(dims), "cv_size": None, "cv_volume": None,
                     "distinct_topologies": len(set(tris))},
                    **shape_stats(len(dims))), boxes

    def cv(xs):
        mu = statistics.mean(xs)
        return (statistics.pstdev(xs) / mu) if mu > 1e-9 else 0.0

    return dict({"n": len(dims), "cv_size": round(cv(dims), 5),
                 "cv_volume": round(cv(vols), 5),
                 "distinct_topologies": len(set(tris))},
                **shape_stats(len(dims))), boxes


# ===========================================================================
# PART 2 -- SUBJECT SELECTION
# ===========================================================================

CONTEXT_PAT = re.compile(
    r"(?:^|_)(?:ctx|standin|stand_in|context|proxy|placeholder|helper|"
    r"backdrop|dummy)(?:_|\d|$)", re.I)
CONTEXT_COLL_PAT = re.compile(
    r"(standin|context|camera|ctx|proxy|helper|backdrop|ref)s?$", re.I)


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _collection_meshes(coll):
    """Meshes in a collection, descending into children but NOT into a child
    named like a standin/context/camera group.

    `all_objects` descends into everything, which is how the first run of this
    picked `CTX_Column_14` -- a context column parked inside
    `ITEM_MARSHAL_POST_DECK` -- as the subject to frame and judge. A placeholder
    measured as the item is the same class of error as a placeholder used as the
    control, and wave 1 managed both.
    """
    out, skipped = [], []
    stack = [coll]
    seen = set()
    while stack:
        c = stack.pop()
        if c.name in seen:
            continue
        seen.add(c.name)
        out.extend(o for o in c.objects if o.type == "MESH")
        for ch in c.children:
            if CONTEXT_COLL_PAT.search(ch.name):
                skipped.append(ch.name)
            else:
                stack.append(ch)
    return out, skipped


def select_objects(scene, rec, prefix, coll_name):
    """Which meshes ARE the item.

    The old default -- every mesh in the scene -- was wrong in a way wave 1
    made visible. `crew_fireproof_overall`'s test scene contains STANDIN bodies
    with smooth ovoid heads; `armco_w_beam`'s contains 1,076 AWBSTAND_ bolts;
    `marshal_post_deck`'s contains 50 CTX_Column objects. Measuring a
    placeholder as part of the item is measuring the wrong thing, and it is how
    a reviewer ended up using one of the item's own objects as the control.

    Order: explicit --prefix, explicit --collection, a collection whose name
    matches the manifest id, then every mesh MINUS anything named like a
    standin. The selection used is always reported.
    """
    in_scene = {o.name for o in scene.objects}
    meshes = [o for o in scene.objects if o.type == "MESH"]

    def clean(objs, tag, drop_standins):
        # The name filter runs on AUTO-DETECTED selections only. An explicit
        # --prefix or --collection is a statement about what the item is, and a
        # gate that quietly drops objects the caller named is a gate that
        # measured something other than what was asked for.
        objs = [o for o in objs if o.name in in_scene]
        if not drop_standins:
            return objs, tag
        kept = [o for o in objs if not CONTEXT_PAT.search(o.name)]
        if len(kept) < len(objs):
            tag += f", minus {len(objs) - len(kept)} named like standins"
        return (kept or objs), tag

    if prefix:
        return clean([o for o in meshes if o.name.startswith(prefix)],
                     f"--prefix {prefix} (taken as given)", False)
    if coll_name:
        c = bpy.data.collections.get(coll_name)
        if c is None:
            raise SystemExit(f"REFUSING: no collection named '{coll_name}'.")
        objs, skipped = _collection_meshes(c)
        tag = f"--collection {coll_name}"
        if skipped:
            tag += f" (skipped sub-collections {skipped})"
        return clean(objs, tag, False)

    target = _norm(rec["id"])
    cands = []
    for c in bpy.data.collections:
        if CONTEXT_COLL_PAT.search(c.name):
            continue
        n = _norm(c.name)
        if target and (target in n or n in target) and len(n) >= 6:
            objs, skipped = _collection_meshes(c)
            objs = [o for o in objs if o.name in in_scene]
            if objs:
                cands.append((c.name, objs, skipped))
    if cands:
        cands.sort(key=lambda kv: (-len(kv[1]), kv[0]))
        name, objs, skipped = cands[0]
        tag = f"collection '{name}' (auto-detected from item id)"
        if skipped:
            tag += f", skipping sub-collections {skipped}"
        if len(cands) > 1:
            tag += (f"; {len(cands)} collections matched, took the largest -- "
                    "pass --collection to be explicit")
        return clean(objs, tag, True)

    kept = [o for o in meshes if not CONTEXT_PAT.search(o.name)]
    if kept and len(kept) < len(meshes):
        return kept, (f"every mesh MINUS {len(meshes) - len(kept)} named like a "
                      f"standin/context object (no collection matched '{rec['id']}' "
                      f"-- pass --prefix or --collection to be explicit)")
    return meshes, ("every mesh in the scene (no collection matched "
                    f"'{rec['id']}' -- pass --prefix or --collection)")


def prefix_integrity(scene, rec, prefix, chosen):
    """`--prefix` may NAME the item. It may not carve a piece out of it.

    Added 2026-08-02. This measures the selection; it does not change any
    check, threshold or measurement, and it is a no-op for every run that does
    not pass `--prefix`.

    WHY. `--prefix` is the one selector `select_objects` takes "as given": it
    applies no standin filter and consults no collection, so whatever the caller
    types is what gets measured. It was introduced so `marshal_post_deck` could
    exclude the 50 `CTX_Column` stand-ins parked in its test scene. The gate now
    does that itself -- measured on the actual blend: 75 meshes in the file, 50
    of them `CTX_`, carrying 16.8 % of the face count, and auto-detection
    selects 25 objects by skipping the `_Context` sub-collection with no
    `--prefix` at all. Every one of the 28 wave-1 items re-gates by
    auto-detection or `--collection`; not one needs the flag.

    What survives is the escape hatch: a prefix that also drops REAL objects
    narrows the gate onto the part of the item the author likes best, and
    nothing said so. So the flag now has to be honest. If the objects it drops
    are stand-ins the gate would have dropped anyway, fine. If they are the
    item, this refuses and points at `--collection`, which is filtered,
    reported, and descends into children while skipping standin sub-collections.
    """
    if not prefix:
        return None
    auto, auto_why = select_objects(scene, rec, None, None)
    chosen_names = {o.name for o in chosen}
    dropped = [o.name for o in auto
               if o.name not in chosen_names and not CONTEXT_PAT.search(o.name)]
    if dropped:
        raise SystemExit(
            f"REFUSING: --prefix {prefix} selects {len(chosen)} meshes but "
            f"excludes {len(dropped)} that are part of this item and are NOT "
            f"named like stand-ins: {sorted(dropped)[:12]}"
            f"{' ...' if len(dropped) > 12 else ''}.\n"
            f"Without --prefix the gate selects {len(auto)} objects via "
            f"{auto_why}.\n"
            "--prefix is taken as given and filters nothing, so a prefix that "
            "drops real objects narrows the measurement onto the part of the "
            "item its author chose -- which is the same class of error as "
            "measuring a placeholder as the item. Use --collection: it is "
            "filtered, it is reported, and it skips standin/context "
            "sub-collections on its own.")
    return {"prefix_selected": len(chosen), "auto_would_select": len(auto),
            "auto_selection": auto_why,
            "standins_prefix_also_dropped":
                len([o for o in auto if o.name not in chosen_names])}


def pick_subject(objs, per_tris, override, declared, boxes):
    """Which single object the witness camera frames.

    TWO RULES, because "typical" only means something when there is a population.

    MANY INSTANCES -> the MEDIAN by triangle count. An item is accepted on the
    strength of its typical instance; moving the median requires improving half
    the population, whereas a hero instance can be built once and pointed at.
    When the agent's own macro camera is aimed at its best bay, this deliberately
    looks somewhere else.

    ONE INSTANCE -> the LARGEST object by bounding-box diagonal. With no
    population there is nothing to be typical of, and the median by complexity
    picks whatever sub-part happens to sit in the middle of the list. On
    `access_road_slab` -- one declared instance, ten objects -- that was an
    object measuring 0.01 x 3.29 x 0.01 m: a sealant strip. The gate framed a
    10 mm sliver at 1.7 m, measured it 84 % crushed, and reported on the road
    slab. The item's principal body is what the item is.
    """
    if override:
        ob = bpy.data.objects.get(override)
        if ob is None:
            raise SystemExit(f"REFUSING: --subject '{override}' is not in this blend.")
        return ob, f"--subject {override} (OVERRIDDEN)"
    # Objects that evaluate to nothing are not candidates. `paddock_paving_bay`'s
    # median-by-triangles object was `PPB_Field_2_3_0`, which emits no geometry
    # at all, and staging died on it -- a gate that cannot report is worse than
    # one that reports a rejection.
    live = [o for o in objs if per_tris.get(o.name, 0) > 0]
    if live:
        objs = live
    if declared > 1:
        ranked = sorted(objs, key=lambda o: (per_tris.get(o.name, 0), o.name))
        ob = ranked[len(ranked) // 2]
        return ob, (f"median-triangle instance of {len(ranked)} objects "
                    f"({per_tris.get(ob.name, 0)} tris) -- the TYPICAL instance "
                    f"of a population of {declared}, not the best one")

    def diag(o):
        b = boxes.get(o.name)
        if not b:
            return 0.0
        d = b[1] - b[0]
        return float(d.length)

    ranked = sorted(objs, key=lambda o: (-diag(o), o.name))
    ob = ranked[0]
    return ob, (f"largest of {len(ranked)} objects by bbox diagonal "
                f"({diag(ob):.2f} m) -- one declared instance, so there is no "
                f"population to be typical of and the item's principal body is "
                f"what it is")


# ===========================================================================
# PART 3 -- STAGING THE WITNESS FRAME
# ===========================================================================

def _look_at(obj, target):
    d = (target - obj.location)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def flip_path(p):
    """`.../witness.blend` -> `.../witness_flip.blend`, and the same for .png.

    One function, so the writer and every reader agree by construction.
    """
    root, ext = os.path.splitext(os.path.abspath(p))
    return root + "_flip" + ext


def sun_screen_rowcol(cam, light_dir):
    """Where the light travels, in image array coordinates (row, col).

    Lifted out of `stage_witness` so the flip frame's direction is computed by
    the SAME three lines as the chosen frame's. Two copies of this arithmetic
    that disagree by a sign is exactly the class of fault that has cost this
    project three instruments.
    """
    vc = cam.matrix_world.to_3x3().transposed() @ light_dir
    sx, sy = float(vc.x), float(vc.y)
    n = math.hypot(sx, sy)
    if n <= 1e-6:
        return [1.0, 0.0]
    return [-sy / n, sx / n]


def mirror_sun_about_camera(sun, cam):
    """Swing the sun to the OTHER candidate side. R2-060.

    `sun_side_chosen` is already a choice between two: the sun sits at
    cam_az +/- SUN_AZ_OFF_CAM_DEG and the side that better lights the subject's
    dominant visible normal wins. The two-light separator needs the RUNNER-UP,
    and the runner-up is the winner MIRRORED ABOUT THE CAMERA AZIMUTH -- not its
    opposite. Mirroring is what this does, so the flip frame is a frame the gate
    would have been entitled to stage anyway, at the same elevation, at the same
    energy, with the same cos(incidence) budget on a surface facing the camera.

    A true 180 deg reversal would separate paint from geometry MORE cleanly --
    the lip and the shadow would swap exactly. It is not available: the reversed
    sun is the one the side-picker rejected as putting the subject in its own
    shadow, and four wave-1 items were rejected by the rig rather than by
    anything about the asset for precisely that reason. So the repair is
    measured on the mirror, which is what the gate can actually afford, and the
    180 deg case is rendered on the control ladder only, to bound what the
    mirror costs.

    Returns (detail, light_dir). Refuses rather than returning an identity.
    """
    emit = (sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    sun_from = -emit
    el = math.asin(max(-1.0, min(1.0, float(sun_from.z))))
    sun_az = math.atan2(float(sun_from.y), float(sun_from.x))
    fwd = cam.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    cam_az = math.atan2(float(fwd.y), float(fwd.x))
    off = math.atan2(math.sin(sun_az - cam_az), math.cos(sun_az - cam_az))
    if abs(math.degrees(off)) < 5.0:
        raise RuntimeError(
            f"REFUSING to stage a flip frame: the sun is only "
            f"{math.degrees(off):+.2f} deg off the camera azimuth, so its "
            "mirror is the same light. There are not two sides here.")
    new_az = cam_az - off
    new_from = Vector((math.cos(el) * math.cos(new_az),
                       math.cos(el) * math.sin(new_az), math.sin(el)))
    sun.rotation_euler = new_from.to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.update()
    got = (sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    # The three things that make this a mirror and not a mistake, asserted
    # rather than assumed: it still points DOWN, it is at the SAME elevation,
    # and it is the same angle off the camera on the other side.
    if got.z >= 0.0:
        raise RuntimeError(f"flip sun emits upward ({got.z:+.4f})")
    if abs(math.degrees(math.asin(max(-1.0, min(1.0, float(-got.z)))))
           - math.degrees(el)) > 0.05:
        raise RuntimeError("flip sun changed elevation")
    sep = math.degrees(math.acos(max(-1.0, min(1.0, float(
        Vector((emit.x, emit.y, 0.0)).normalized().dot(
            Vector((got.x, got.y, 0.0)).normalized()))))))
    if sep < 60.0:
        raise RuntimeError(
            f"flip sun is only {sep:.1f} deg round from the chosen one; a lip "
            "and its shadow do not swap ends over that little")
    return ({"chosen_sun_az_deg": round(math.degrees(sun_az), 4),
             "flip_sun_az_deg": round(math.degrees(new_az), 4),
             "camera_az_deg": round(math.degrees(cam_az), 4),
             "off_camera_deg": round(math.degrees(off), 4),
             "ground_separation_deg": round(sep, 3),
             "elevation_deg": round(math.degrees(el), 4),
             "emit": [round(float(v), 6) for v in got]},
            -new_from)


def stage_witness(subject, rec, dist, lens, blend_path, spec_path):
    """Rebuild this blend as a controlled measurement frame and save a copy.

    DESTRUCTIVE to the in-memory scene, so every mesh-side check has already
    run by the time this is called. `save_as_mainfile(copy=True)` never touches
    the file the gate was pointed at.

    Everything but the subject is deleted -- every other instance of the item,
    every standin, every camera and light the agent authored, the whole
    context. That is not tidiness: it makes the witness .blend small enough to
    upload in seconds (a 1.4 GB item test scene becomes a few MB), it removes
    the placeholder geometry that would otherwise be measured as subject, and
    it means the light in the frame is this file's light and nobody else's.
    """
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    oe = subject.evaluated_get(deps)
    me = oe.to_mesh()
    if me is None or not me.vertices:
        raise SystemExit(f"REFUSING: subject '{subject.name}' evaluates to no geometry.")
    mw = subject.matrix_world
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(mw.to_4x4())
    pts = co @ M[:3, :3].T + M[:3, 3]
    # Polygon normals and areas, kept for orienting the flat control card to the
    # subject's own dominant visible surface.
    npoly = len(me.polygons)
    pn = np.empty(npoly * 3, dtype=np.float64)
    pa = np.empty(npoly, dtype=np.float64)
    me.polygons.foreach_get("normal", pn)
    me.polygons.foreach_get("area", pa)
    pn = (pn.reshape(-1, 3) @ M[:3, :3].T)
    ln = np.linalg.norm(pn, axis=1)
    pn = pn / np.maximum(ln, 1e-12)[:, None]
    oe.to_mesh_clear()
    lo = pts.min(axis=0)
    hi = pts.max(axis=0)
    ctr = (lo + hi) / 2.0
    dims = hi - lo

    # --- camera azimuth: look at the broad face -----------------------------
    # An elongated object viewed end-on shows almost nothing. Perpendicular to
    # the longest horizontal axis shows the face the film sees.
    long_az = 0.0 if dims[0] >= dims[1] else math.radians(90.0)
    # Perpendicular to the long axis PLUS 40 degrees. Dead-on perpendicular is
    # what a plan drawing looks like and it lays the subject's dominant feature
    # direction along a screen axis, which is where check 6 loses its power --
    # see the note on SUN_AZ_OFF_CAM_DEG for the measured numbers.
    cam_az = long_az + math.radians(90.0 + 40.0)

    th = math.radians(CAM_ELEV_DEG)
    cdir = Vector((math.cos(th) * math.cos(cam_az),
                   math.cos(th) * math.sin(cam_az),
                   math.sin(th)))
    # AIM AT THE SURFACE, NOT AT THE BOUNDING BOX'S CENTRE.
    #
    # The bbox centre of an extended or irregular mesh is not on the mesh. On
    # `terrain_ground` -- one object 81 m across the diagonal -- the centre sits
    # metres above the ground, so a camera 2.4 m from it at 35 deg looked down at
    # a point in mid-air and the terrain appeared as a triangle in the bottom
    # corner of the frame: 80,309 of 8,294,400 pixels, 1 %. Every number measured
    # in that frame was measured on a grazing sliver, and the item was ACCEPTED
    # on the strength of it.
    #
    # The per-axis median vertex position is on or in the surface for a terrain
    # patch, a guardrail bay, a deck, a figure and a hollow box alike, and it
    # costs one numpy call. Bounding-box extents are still what choose the view
    # AZIMUTH, which is what they are good for.
    med = np.median(pts, axis=0)
    aim = Vector((float(med[0]), float(med[1]), float(med[2])))
    # A tall thin thing (a 6 m post at 2.6 m) cannot be aimed at its centre and
    # still show its interesting end, but centring is the only choice that is
    # the same for every item, so centre it is -- and `onscreen_px_4k` in the
    # report says how much of it lands in frame.
    cam_loc = aim + cdir * dist

    # nearest subject surface, conservatively from the bbox corners
    d_near = 1e18
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                c = Vector((lo[0] if i else hi[0], lo[1] if j else hi[1],
                            lo[2] if k else hi[2]))
                d_near = min(d_near, (c - cam_loc).length)
    d_ref = max(0.10, min(0.45 * d_near, 0.60 * dist))

    keep = {subject.name}
    for o in list(bpy.data.objects):
        if o.name not in keep:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass

    # --- world --------------------------------------------------------------
    w = bpy.data.worlds.new("GATE_WITNESS_WORLD")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (*SKY_COLOR, 1.0)
    bg.inputs[1].default_value = SKY_STRENGTH
    nt.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w

    # --- camera -------------------------------------------------------------
    cd = bpy.data.cameras.new("GATE_CAM")
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.sensor_fit = "HORIZONTAL"     # so px/m is exactly 3840*lens/36/d
    cd.clip_start = 0.005
    cd.clip_end = max(2000.0, dist * 50.0)
    cd.dof.use_dof = False
    cam = bpy.data.objects.new("GATE_CAM", cd)
    scene.collection.objects.link(cam)
    cam.location = cam_loc
    _look_at(cam, aim)
    scene.camera = cam
    bpy.context.view_layer.update()
    R = cam.matrix_world.to_3x3()

    # --- the subject's dominant VISIBLE surface -----------------------------
    # Camera-facing faces only, area-weighted. R2-011 is the reason for that
    # qualifier: an area-weighted mean normal over a CLOSED mesh is exactly zero,
    # and a fix built on one is how the steering wheel got audited from behind.
    # Restricting to faces the camera can see cannot cancel.
    view_dir = (aim - cam.location).normalized()
    vd = np.array([view_dir.x, view_dir.y, view_dir.z])
    facing = (pn @ (-vd)) > 0.1
    vis_n = None
    if facing.any():
        acc = (pn[facing] * pa[facing][:, None]).sum(axis=0)
        if np.linalg.norm(acc) > 1e-12:
            acc = acc / np.linalg.norm(acc)
            vis_n = Vector((float(acc[0]), float(acc[1]), float(acc[2])))
    if vis_n is None or vis_n.length < 1e-6:
        vis_n = (cam.location - aim).normalized()
        vis_why = "camera-facing (subject normals cancelled)"
    else:
        vis_why = (f"area-weighted normal of the camera-facing faces "
                   f"({vis_n.x:+.3f},{vis_n.y:+.3f},{vis_n.z:+.3f})")

    # --- sun: on whichever side actually LIGHTS that surface ----------------
    #
    # The sun has to be off to one side for check 6 to have a light direction to
    # work along, but "one side" is two choices and only one of them lights the
    # face the camera is looking at. Putting it on the wrong side is not a dim
    # frame, it is a BLACK one: rendered and measured, `armco_w_beam` came back
    # with 98 % of the subject crushed and a single lit pixel-wide lip along the
    # top edge, and `access_road_slab`, `catch_fence_post` and
    # `forecourt_paving_bay` did the same -- 4 of 11 items rejected by the rig
    # rather than by anything about the asset.
    #
    # So the side is chosen, not assumed: whichever of +/- the azimuth offset
    # gives the larger cos(incidence) on the subject's own dominant visible
    # normal. Deterministic, one dot product, and recorded in the spec.
    el = math.radians(SUN_ELEV_DEG)
    best_side, best_cos, sun_az = None, None, None
    for side in (+1.0, -1.0):
        az = cam_az + side * math.radians(SUN_AZ_OFF_CAM_DEG)
        sf = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                     math.sin(el)))
        c = vis_n.dot(sf)
        if best_cos is None or c > best_cos:
            best_side, best_cos, sun_az = side, c, az
    sun_from = Vector((math.cos(el) * math.cos(sun_az),
                       math.cos(el) * math.sin(sun_az),
                       math.sin(el)))          # scene -> sun
    light_dir = -sun_from                       # direction light travels
    sun_why = (f"{'+' if best_side > 0 else '-'}{SUN_AZ_OFF_CAM_DEG:.0f} deg off "
               f"the camera azimuth, chosen because it gives cos(incidence) "
               f"{best_cos:+.3f} on the subject's dominant visible normal")

    ld = bpy.data.lights.new("GATE_SUN", "SUN")
    ld.energy = SUN_ENERGY
    ld.angle = math.radians(SUN_ANGLE_DEG)
    ld.color = SUN_COLOR
    sun = bpy.data.objects.new("GATE_SUN", ld)
    scene.collection.objects.link(sun)
    sun.rotation_euler = sun_from.to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.update()

    # --- reference primitives ----------------------------------------------
    hw = (SENSOR_MM / 2.0) / lens                       # half width at depth 1
    hh = hw * (RES_Y_4K / float(RES_X_4K))
    ref_radius = REF_RADIUS_PX * 2.0 * hw * d_ref / RES_X_4K

    refmat = bpy.data.materials.new("GATE_REF_DEFAULT")
    refmat.use_nodes = True            # untouched Principled: base 0.8, rough 0.5

    def ndc_to_world(nx, ny, depth):
        v = Vector(((nx * 2 - 1) * hw, (ny * 2 - 1) * hh, -1.0))
        return cam.location + (R @ v) * depth

    # sphere: dense enough that a facet is under a pixel at 300 px across, and
    # smooth-shaded, so the control is a control and not a low-poly ball.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=512, ring_count=256,
                                         radius=ref_radius)
    sph = bpy.context.object
    sph.name = "GATE_REF_SPHERE"
    for p in sph.data.polygons:
        p.use_smooth = True
    sph.location = ndc_to_world(*REF_SPHERE_NDC, d_ref)
    sph.data.materials.append(refmat)

    # plane: a flat card, normal bisecting camera and sun so it is brightly and
    # squarely lit. It is the noise floor -- what the pipeline puts on a surface
    # that has nothing on it.
    bpy.ops.mesh.primitive_plane_add(size=ref_radius * 1.6)
    pln = bpy.context.object
    pln.name = "GATE_REF_PLANE"
    pln.location = ndc_to_world(*REF_PLANE_NDC, d_ref)
    # Oriented to the SUBJECT'S OWN dominant visible surface, so it is lit at the
    # same incidence the subject's main face is -- a flat control under the same
    # light rather than merely a flat control.
    card_why = vis_why
    pln.rotation_euler = vis_n.to_track_quat("Z", "Y").to_euler()
    pln.data.materials.append(refmat)

    # --- the step wedge, and why a sphere alone is not enough ---------------
    #
    # A control only controls if some of it is AT THE SUBJECT'S BRIGHTNESS: the
    # band contrast is reported as a percentage of the patch mean, so a dark
    # patch divides by a small number and scores high on arithmetic alone. Two
    # real measurements, both on the same timber deck at mean 0.033 linear:
    #
    #   sphere floor 0.043 (sky 0.12)  ->     0 sphere px in the subject's window
    #   sphere floor 0.009 (sky 0.025) ->  1939 sphere px, still under the minimum
    #
    # and the reason is geometric, not a tuning failure. On a sphere L is
    # proportional to cos(incidence), so the region at 5 % of peak brightness is
    # the outer 0.7 % of the radius -- a rim a couple of pixels wide, which is
    # exactly the rim every band-pass has to erode away to avoid measuring the
    # silhouette. A single-albedo sphere can therefore only ever be a control
    # for BRIGHT subjects, whatever the sky is set to.
    #
    # So the frame also carries a six-step neutral wedge: one flat quad per step,
    # camera-facing, plain default Principled differing only in base colour,
    # spanning 2 % to 95 % reflectance. Steps are ~2.4x apart and the matching
    # window is 2.8x wide, so EVERY subject brightness from 0.004 to 0.55 linear
    # has a large, flat, smooth, identically-rendered patch at its own
    # brightness. It is the grey card of a photographic set-up, for the same
    # reason a photographer carries one.
    wedge = []
    wsize_x = (WEDGE_NDC[2] - WEDGE_NDC[0]) / len(WEDGE_ALBEDOS)
    for i, alb in enumerate(WEDGE_ALBEDOS):
        cxn = WEDGE_NDC[0] + wsize_x * (i + 0.5)
        cyn = (WEDGE_NDC[1] + WEDGE_NDC[3]) / 2.0
        wid_px = wsize_x * RES_X_4K
        hei_px = (WEDGE_NDC[3] - WEDGE_NDC[1]) * RES_Y_4K
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        q = bpy.context.object
        q.name = f"GATE_REF_WEDGE_{i}"
        q.location = ndc_to_world(cxn, cyn, d_ref)
        # EXACTLY PARALLEL TO THE IMAGE PLANE, not merely aimed at the camera.
        #
        # Aiming each quad at the camera from its own position gives each one a
        # slightly different normal -- the strip spans 24 deg of the 54 deg
        # horizontal field -- and at the grazing incidence a 12.5 deg sun makes
        # with a camera-facing surface, cos(i) is near zero and 8 deg of tilt
        # halves it. Measured on a real witness frame, that turned the ladder
        # into this:
        #
        #     albedo  0.02   0.05   0.12   0.28   0.55   0.95
        #     lin L  0.0105 0.0165 0.0280 0.0463 0.0592 0.0518
        #
        # -- saturating, then going BACKWARDS at the bright end, and spanning
        # only 5.6x instead of the intended 47x. The whole point of the wedge is
        # its brightness range, so the range cannot be at the mercy of where in
        # the frame each step happens to sit. Sharing the camera's own rotation
        # gives every step one normal, one cos(i), and a ladder that is purely
        # albedo.
        q.rotation_euler = cam.rotation_euler
        sx_w = wid_px * 2.0 * hw * d_ref / RES_X_4K
        sy_w = hei_px * 2.0 * hw * d_ref / RES_X_4K
        q.scale = (sx_w, sy_w, 1.0)
        mm = bpy.data.materials.new(f"GATE_REF_WEDGE_{i}")
        mm.use_nodes = True
        bsdf = next((n for n in mm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"),
                    None)
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (alb, alb, alb, 1.0)
        q.data.materials.append(mm)
        wedge.append((q, alb, [cxn * RES_X_4K, (1.0 - cyn) * RES_Y_4K,
                               wid_px, hei_px]))

    for o in [sph, pln] + [w[0] for w in wedge]:
        # They must not throw shade on the subject, or bounce light into it. A
        # control that changes the thing it is controlling for is not a control.
        o.visible_shadow = False
        o.visible_diffuse = False
        o.visible_glossy = False

    # --- render settings ----------------------------------------------------
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = RES_X_4K
    scene.render.resolution_y = RES_Y_4K
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True          # gives a free geometry matte
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    # STANDARD, not AgX. AgX compresses highlights and desaturates them, which
    # is a tone curve applied on top of the quantity being measured; it is also
    # the most likely explanation for the peep's "blue exceeds red in every
    # band" finding, since these scenes DO have a 12.5 deg sun lamp in them.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.display_settings.display_device = "sRGB"
    scene.frame_set(scene.frame_current)

    for _ in range(8):
        try:
            if not bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
                                          do_recursive=True):
                break
        except Exception:
            break

    os.makedirs(os.path.dirname(os.path.abspath(blend_path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True, compress=True)

    # --- R2-060. THE SAME FRAME ON THE OTHER CANDIDATE SUN SIDE ------------
    # Written every time, unconditionally, because a check that is only
    # sometimes measurable is a check that is sometimes a pass by default. Same
    # scene, same camera, same subject, same controls, same energy: the ONLY
    # difference in this file is which of the two sides the side-picker chose.
    flip_blend = flip_path(blend_path)
    flip_detail, flip_light_dir = mirror_sun_about_camera(sun, cam)
    bpy.ops.wm.save_as_mainfile(filepath=flip_blend, copy=True, compress=True)
    flip_rowcol = sun_screen_rowcol(cam, flip_light_dir)
    sun.rotation_euler = sun_from.to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.update()
    back = (sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    if (back - light_dir).length > 1e-5:
        raise RuntimeError(
            "the chosen sun did not come back to where it was after the flip "
            f"blend was written ({tuple(round(float(v), 6) for v in back)} vs "
            f"{tuple(round(float(v), 6) for v in light_dir)}); the witness "
            "frame and the flip frame would not be the same staging")

    # --- what the analyser needs to find the control ------------------------
    vc = R.transposed() @ light_dir       # light travel in camera space
    sx, sy = float(vc.x), float(vc.y)
    n = math.hypot(sx, sy)
    # image array coords: +row is DOWN the picture, so the y component flips
    sun_uv = [sx / n, -sy / n] if n > 1e-6 else [1.0, 0.0]

    px_per_m = (RES_X_4K * lens / SENSOR_MM) / max(dist, 1e-6)

    def ndc_px(nx, ny):
        return [nx * RES_X_4K, (1.0 - ny) * RES_Y_4K]

    spec = {
        "item": rec["id"],
        "rig_version": RIG_VERSION,
        "subject_object": subject.name,
        "resolution": [RES_X_4K, RES_Y_4K],
        "lens_mm": lens,
        "camera_distance_m": dist,
        "px_per_m": px_per_m,
        "mm_per_px": 1000.0 / px_per_m,
        "sun_elevation_deg": SUN_ELEV_DEG,
        "sun_azimuth_off_camera_deg": SUN_AZ_OFF_CAM_DEG,
        "sun_screen_direction_rowcol": [sun_uv[1], sun_uv[0]],
        "sun_energy_w_m2": SUN_ENERGY,
        "sky_strength": SKY_STRENGTH,
        "view_transform": "Standard",
        "ref_depth_m": d_ref,
        "ref_radius_m": ref_radius,
        "ref_sphere_centre_px": ndc_px(*REF_SPHERE_NDC),
        "ref_plane_centre_px": ndc_px(*REF_PLANE_NDC),
        "ref_radius_px": REF_RADIUS_PX,
        "ref_card_normal_from": card_why,
        "sun_side_chosen": sun_why,
        # R2-060. The runner-up side, staged and recorded so the relief check
        # can ask whether the pattern belongs to the light or to the surface.
        "sun_screen_direction_rowcol_flip": flip_rowcol,
        "witness_blend_flip": os.path.abspath(flip_blend),
        "flip_sun": flip_detail,
        "subject_visible_normal": [float(vis_n.x), float(vis_n.y), float(vis_n.z)],
        "sun_cos_incidence_on_visible_normal": round(float(best_cos), 5),
        "wedge_boxes_px": [w[2] for w in wedge],
        "wedge_albedos": [w[1] for w in wedge],
        "band_radii_px": list(BANDS),
        "band_radii_mm": {str(r): round(1000.0 * r / px_per_m, 3) for r in BANDS},
        "aim_point_m": [float(med[0]), float(med[1]), float(med[2])],
        "aim_from": "per-axis median vertex position (NOT the bbox centre)",
        "camera_location_m": [float(cam_loc.x), float(cam_loc.y), float(cam_loc.z)],
        "subject_bbox_m": [list(map(float, lo)), list(map(float, hi))],
        "subject_dims_m": list(map(float, dims)),
        "witness_blend": os.path.abspath(blend_path),
    }
    with open(spec_path, "w") as fh:
        json.dump(spec, fh, indent=1)
    return spec


# ===========================================================================
# PART 4 -- GETTING THE PIXELS
# ===========================================================================

def render_witness_pair(blend_path, png_path, samples, args):
    """Both sun sides, submitted back to back. R2-060.

    Two jobs against two ~5 MB scenes. That is deliberately NOT consolidated
    into one scene with light linking: the five-arm study was worth merging
    because its scenes were 1.4 GB and the broker was spending 940 s loading
    them, and neither is true here -- the measured witness blends run 3-11 MB,
    so a merge would buy back nothing and would put a light-linking rig between
    the two frames whose ONLY permitted difference is the sun's azimuth.
    """
    info = render_witness(blend_path, png_path, samples, args)
    fb, fp = flip_path(blend_path), flip_path(png_path)
    if not os.path.exists(fb):
        info["flip"] = {"rendered": False,
                        "why": f"no flip blend at {fb} -- this witness was "
                               "staged before R2-060; re-stage it"}
        return info
    try:
        info["flip"] = render_witness(fb, fp, samples, args)
        info["flip"]["png"] = fp
    except Exception as exc:                                   # noqa: BLE001
        # A FAILED FLIP RENDER MUST NOT COST THE OTHER SIX CHECKS. It costs the
        # relief check, which then reports NOT MEASURED -- and NOT MEASURED is
        # not a pass (R2-019), so nothing is smuggled through here.
        info["flip"] = {"rendered": False,
                        "why": f"{type(exc).__name__}: {exc}"}
    return info


def render_witness(blend_path, png_path, samples, args):
    """Submit the witness frame to the 5090 broker and wait for the PNG.

    Failure here is a FAILURE, never a skip. If the frame does not arrive, three
    checks were not measured, and R2-018 is the whole reason that cannot be
    allowed to read as a pass.
    """
    os.makedirs(os.path.dirname(os.path.abspath(png_path)), exist_ok=True)
    if args.local_render:
        scene = bpy.context.scene
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.render.filepath = png_path
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        return {"backend": "local", "seconds": round(time.time() - t0, 1),
                "samples": samples, "denoiser": "OPENIMAGEDENOISE"}
    cmd = [args.rq, "render",
           "--scene", os.path.abspath(blend_path),
           "--cam", "GATE_CAM",
           "--res", str(RES_X_4K), str(RES_Y_4K),
           "--samples", str(samples),
           "--engine", "CYCLES",
           "--denoiser", WITNESS_DENOISER,
           "--film-transparent",
           "--dof", "off",
           "--agent", "itemgate",
           "--timeout", str(args.timeout),
           "--wait", "-o", os.path.abspath(png_path)]
    print(">> witness render: " + " ".join(cmd))
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout + 600)
    tail = (p.stdout or "")[-1500:] + (p.stderr or "")[-1500:]
    if p.returncode != 0 or not os.path.exists(png_path):
        raise RuntimeError(f"witness render failed (rc={p.returncode}). "
                           f"rq said:\n{tail}")
    return {"backend": "vast-5090 via rq", "seconds": round(time.time() - t0, 1),
            "samples": samples, "denoiser": WITNESS_DENOISER,
            "rq_tail": tail[-400:]}


def load_linear_rgba(path):
    """(H,W,4) float32, scene-linear RGB, straight alpha, row 0 at the TOP.

    Read through Blender rather than a PNG library because this script runs in
    Blender's Python, which has no PIL -- and because Blender's own colour
    management is what wrote the file, so it is what should undo it.
    CHANNEL_PACKED keeps RGB and alpha independent: no premultiply round-trip.
    """
    img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    img.colorspace_settings.name = "sRGB"
    img.alpha_mode = "CHANNEL_PACKED"
    img.reload()
    w, h = img.size
    if w == 0 or h == 0:
        raise RuntimeError(f"{path} loaded with size {w}x{h}")
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    arr = buf.reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(img)
    return arr


# ===========================================================================
# PART 5 -- THE IMAGE MEASUREMENTS
# ===========================================================================

def _box_sum(a, r):
    """Sum over a (2r+1)^2 window, edge-clamped. Integral image, O(N)."""
    if r <= 0:
        return a.copy()
    pad = np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge")
    c = pad.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]


def _gauss_kernel(sigma):
    rad = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-rad, rad + 1, dtype=np.float64)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def _sep_conv(a, k):
    """Separable convolution, edge-clamped."""
    rad = (len(k) - 1) // 2
    pad = np.pad(a, ((rad, rad), (0, 0)), mode="edge")
    out = np.zeros_like(a)
    for i, w in enumerate(k):
        out += w * pad[i:i + a.shape[0], :]
    pad = np.pad(out, ((0, 0), (rad, rad)), mode="edge")
    res = np.zeros_like(a)
    for i, w in enumerate(k):
        res += w * pad[:, i:i + a.shape[1]]
    return res


# Below this, an exact separable Gaussian; above it, three box passes, which are
# O(N) regardless of width.
#
# THE SMALL CASE HAS TO BE EXACT AND THE FIRST VERSION OF THIS WAS NOT. Three
# box passes cannot make a sigma under 1.41 at all (b rounds to 1), so
# `_dog(L, 1)` was blur(1.41) minus blur(1.41) -- IDENTICALLY ZERO. The r1 band
# reported 0.0000 for every surface in every test, subject and control alike,
# which is a check that cannot fail. Worse, a box of radius 1 averages exactly
# three samples and therefore annihilates a 3-px-period signal outright: the
# validation case built from a 3 px pattern measured bit-identical to pure
# noise. r1-r4 is the band the whole wave-1 finding lives in.
GAUSS_EXACT_BELOW = 3.2


def _blur(a, sigma):
    if sigma < 0.2:
        return a
    if sigma < GAUSS_EXACT_BELOW:
        return _sep_conv(a, _gauss_kernel(sigma))
    b = int(round((-1.0 + math.sqrt(1.0 + 4.0 * sigma * sigma)) / 2.0))
    b = max(b, 1)
    area = float((2 * b + 1) ** 2)
    out = a
    for _ in range(3):
        out = _box_sum(out, b) / area
    return out


def _dog(L, r):
    """Band-pass centred on r px.

    A plain difference of Gaussians rolls off only as omega^2 below its
    passband, which leaks a lot: a 40-px-period sine -- pure r16 content --
    put 0.40 into the r2 band and 1.09 into r4 during validation. That leak is
    precisely the false-accept path this gate exists to close, because "all the
    energy at r8-r16 and none at r1-r4" IS the wave-1 failure signature, and a
    leaky fine band would credit a soft AO mask with fabric it does not have.

    So the DoG output is high-passed once more at 2r, which strips its residual
    low-frequency tail and takes the rolloff to omega^4. Measured effect: the
    same 40-px sine drops to 0.03 in r2.
    """
    b = _blur(L, 0.5 * r) - _blur(L, 1.0 * r)
    return b - _blur(b, 2.0 * r)


def _erode(mask, r):
    """True only where the whole (2r+1)^2 window is inside the mask.

    Needed because a band-pass across a silhouette edge is enormous and has
    nothing to do with the surface. Every band erodes by 3x its own radius,
    which is where the wider Gaussian's support runs out.
    """
    if r <= 0:
        return mask
    k = float((2 * r + 1) ** 2)
    return _box_sum(mask.astype(np.float64), r) >= k - 0.5


def _shift(a, di, dj):
    """a[i+di, j+dj] with a validity mask, no wraparound."""
    H, W = a.shape
    out = np.zeros_like(a)
    ok = np.zeros((H, W), dtype=bool)
    si0, si1 = max(0, -di), min(H, H - di)
    sj0, sj1 = max(0, -dj), min(W, W - dj)
    if si1 <= si0 or sj1 <= sj0:
        return out, ok
    out[si0:si1, sj0:sj1] = a[si0 + di:si1 + di, sj0 + dj:sj1 + dj]
    ok[si0:si1, sj0:sj1] = True
    return out, ok


def contrast_bands(L, mask, mean_ref=None):
    """Band-passed contrast as % of the patch mean, per band radius.

    The peep's instrument, reimplemented. `% of mean` rather than absolute so a
    dark material and a light one are on the same scale -- and because that is
    the form the wave-1 numbers are quoted in.

    THE `% OF MEAN` IS ALSO A FALSE-ACCEPT PATH IF THE CONTROL IS NOT MATCHED
    TO IT, and it took a second pass to see. Divide by a small mean and the
    quotient grows: a tyre at mean 0.02 and a sphere at mean 0.50 differ 25x in
    the divisor while their absolute noise differs only ~5x, so a black rubber
    surface with nothing on it would out-score the control on arithmetic alone.
    That is why the control patches are restricted to pixels whose LUMINANCE
    MATCHES the subject's before they are measured (see `matched`). No model, no
    correction factor -- the same brightness, therefore the same divisor and the
    same noise, measured on a surface known to be smooth.
    """
    npix = int(mask.sum())
    if npix < MIN_BAND_PX:
        return None, npix, None
    mu = float(L[mask].mean()) if mean_ref is None else mean_ref
    if mu <= 1e-6:
        return None, npix, mu
    out = {}
    for r in BANDS:
        m = _erode(mask, int(math.ceil(3 * r)))
        n = int(m.sum())
        if n < MIN_BAND_PX:
            out[str(r)] = None
            continue
        out[str(r)] = round(100.0 * float(_dog(L, r)[m].std()) / mu, 4)
    return out, npix, mu


def _agg(bands, which):
    vals = [bands[str(r)] for r in which if bands.get(str(r)) is not None]
    return (sum(vals) / len(vals)) if vals else None


def _agg_max(bands, which):
    vals = [bands[str(r)] for r in which if bands.get(str(r)) is not None]
    return max(vals) if vals else None


def relief_anisotropy(L, mask, sun_rc, r=2, band=None):
    """Does the surface carry LIGHT-AND-SHADE PAIRS, or single-value marks?

    Under a 12.5 deg sun a raised feature makes a bright sunward lip and a dark
    lee shadow: a DIPOLE, and its two halves sit side by side ALONG THE LIGHT.
    So in the band-passed image the surface must be ANTICORRELATED WITH ITSELF
    at a lag along the light, at the lip-to-shadow spacing. A printed mark has no
    such lobe -- its autocorrelation is isotropic and decays without going
    usefully negative -- and a printed decal is exactly what every failed wave-1
    feature behaves like.

    THE STATISTIC IS THE DEPTH OF THAT NEGATIVE LOBE, `dip = max(-rho_along)`,
    and it took a rewrite to get there. The first version used
    `rho_across - rho_along`, which conflates relief with any DIRECTIONAL
    surface: a deck of parallel boards running along the light measured -0.133,
    i.e. strongly "anti-relief", purely because a board correlates with itself
    along its own length and that term was being subtracted. The negative lobe on
    its own does not have that failure -- boards running along the light give a
    positive rho_along and a dip of zero, which is the correct answer for a
    direction the light cannot rake across.

    `rho_across` at the same lag is reported beside it, because real relief is
    usually correlated across the light while anticorrelated along it, and the
    pair is far more readable than either number alone.

    Returns (dip, detail). Compared against the same statistic measured on the
    smooth controls in the same frame.

    `band` supplies an ALREADY BAND-PASSED image in place of `_dog(L, r)`, which
    is how R2-060 re-derives a shipped dip on the LIGHT-DRIVEN half of the band
    alone. Nothing else about the statistic changes, so the re-derived number is
    on the same scale as the shipped one and the two can be subtracted.
    """
    m = _erode(mask, int(math.ceil(3 * r)))
    if int(m.sum()) < MIN_BAND_PX:
        return None, {"reason": "too few pixels after erosion"}
    B = _dog(L, r) if band is None else band
    u = np.array(sun_rc, dtype=np.float64)
    nu = math.hypot(u[0], u[1])
    if nu < 1e-6:
        return None, {"reason": "degenerate sun screen direction"}
    u = u / nu
    v = np.array([-u[1], u[0]])

    def rho(lag, d):
        di, dj = int(round(lag * d[0])), int(round(lag * d[1]))
        if di == 0 and dj == 0:
            return None
        Bs, ok = _shift(B, di, dj)
        ms, _ = _shift(m.astype(np.float64), di, dj)
        val = m & ok & (ms > 0.5)
        if int(val.sum()) < MIN_BAND_PX:
            return None
        x = B[val]
        y = Bs[val]
        sx, sy = x.std(), y.std()
        if sx < 1e-12 or sy < 1e-12:
            return None
        return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))

    dip_a = dip_c = None
    detail = {}
    for lag in (2 * r, 3 * r, 4 * r, 5 * r, 6 * r, 8 * r):
        rp = rho(lag, u)
        rq_ = rho(lag, v)
        if rp is None and rq_ is None:
            continue
        detail[f"lag{lag}"] = {"along_light": (round(rp, 5) if rp is not None
                                              else None),
                               "across_light": (round(rq_, 5) if rq_ is not None
                                                else None)}
        if rp is not None and (dip_a is None or -rp > dip_a):
            dip_a, detail["best_lag_px"] = -rp, lag
        if rq_ is not None and (dip_c is None or -rq_ > dip_c):
            dip_c = -rq_
    if dip_a is None or dip_c is None:
        return None, {"reason": "no usable lag in both directions"}
    # A BAND-PASS IMPOSES ITS OWN NEGATIVE LOBE, so the dip is never zero even on
    # structureless input: synthetic validation measures 0.120 on pure noise and
    # 0.198 on a field of isotropic printed marks, against 0.579 on a field of
    # lip-and-shadow dipoles. The baseline is a property of the filter, identical
    # in both directions -- so the ACROSS-light dip cancels it, and what is left
    # is the part of the anticorrelation that only a directional light falling on
    # real relief can produce. On the synthetic cases: dipoles +0.42, isotropic
    # marks +0.00, pure noise +0.00.
    detail["dip_along"] = round(dip_a, 5)
    detail["dip_across"] = round(dip_c, 5)
    return round(dip_a - dip_c, 5), detail


def two_light_bands(LA, LB, mask, floor, bands=FINE_BANDS, cache=None):
    """Split the fine band of a two-sun pair into what MOVED and what STAYED.

    THE R2-060 SEPARATOR. Write the two band-passed log-luminance images as

        a = dP + dS_A            b = dP + dS_B

    where `dP` is whatever the SURFACE carries (albedo, and in log luminance
    that is all it carries) and `dS` is what the LIGHT carries. A lip and its
    shadow swap ends when the sun changes side, so dS_B ~ -dS_A; a painted step
    does not move at all, so dP is common. The two halves are then just

        D = (a - b) / 2  ->  dS_A        THE LIGHT-DRIVEN BAND
        S = (a + b) / 2  ->  dP          THE SURFACE-DRIVEN BAND

    and `rho = corr(a, b)` says which of the two dominates: -1 for pure relief,
    +1 for pure paint.

    WHY LOG. On a curved surface the same paint renders as albedo*cos(i) and
    cos(i) is not the same under the two suns, so in LINEAR luminance
    D = dP*(cA - cB)/2 -- a scaled copy of the paint, arriving in the half that
    is supposed to contain only light. In log luminance the irradiance is an
    additive term log cos(i) that varies over the whole object rather than over
    a 1-2 px band, and the band-pass removes it. Measured, not argued: a painted
    cylinder and a painted sphere both return their paint to the S half.

    WHY IT IS NOT SUFFICIENT ALONE, stated here because the number is seductive.
    A FLAT GREY PLATE with nothing on it returns rho = -0.98. That is the
    physics and not a bug: with no structure the only thing in the band is the
    plate's own directional shading, which inverts with the sun like anything
    else. rho is a correlation, so it is blind to the fact that it is
    correlating almost nothing. The amplitude clause is what closes that, and
    the amplitude is referenced to the smooth control in the same frame exactly
    as `fine_over_control` is.

    Returns (stats, detail). `light` and `still` are in percent, being 100x the
    sd of a log, i.e. percent contrast -- no `% of mean` divisor, so the divisor
    hazard `contrast_bands` documents does not arise here at all.
    """
    if LA.shape != LB.shape:
        return None, {"reason": f"frame shapes differ: {LA.shape} vs {LB.shape}"}
    # THE BAND-PASSES DO NOT DEPEND ON THE MASK, only on the frame pair and the
    # log floor, and this function is called once for the subject and once for
    # EVERY smooth control in the frame -- eight or nine times on a witness with
    # a sphere, a card and six wedge steps. Recomputing five Gaussian blurs of
    # an 8.3-megapixel array each time made a single item take tens of minutes;
    # over the ~407-item wave-2 campaign that is hours of CPU spent computing
    # the same arrays. `cache` is a plain dict owned by the caller for the life
    # of one frame pair. It changes no number: the arrays are identical, which
    # is exactly why they can be shared.
    if cache is None:
        cache = {}
    key = round(float(floor), 12)
    if cache.get("floor") != key:
        cache.clear()
        cache["floor"] = key
        cache["lA"] = np.log(np.maximum(LA, floor))
        cache["lB"] = np.log(np.maximum(LB, floor))
    lA, lB = cache["lA"], cache["lB"]
    sxx = syy = sxy = 0.0
    per = {}
    light, still, dband = [], [], {}
    for r in bands:
        m = _erode(mask, int(math.ceil(3 * r)))
        n = int(m.sum())
        if n < MIN_BAND_PX:
            per[str(r)] = {"px": n, "skipped": f"{n} px after erosion"}
            continue
        if ("a", r) not in cache:
            cache[("a", r)], cache[("b", r)] = _dog(lA, r), _dog(lB, r)
        a, b = cache[("a", r)], cache[("b", r)]
        D, S = 0.5 * (a - b), 0.5 * (a + b)
        dband[r] = D
        x, y = a[m], b[m]
        x = x - x.mean()
        y = y - y.mean()
        sxx += float((x * x).sum())
        syy += float((y * y).sum())
        sxy += float((x * y).sum())
        lv, sv = 100.0 * float(D[m].std()), 100.0 * float(S[m].std())
        light.append(lv)
        still.append(sv)
        per[str(r)] = {"px": n, "light_pct": round(lv, 5),
                       "still_pct": round(sv, 5),
                       "rho": (round(float((x * y).mean()
                                           / max(x.std() * y.std(), 1e-30)), 5)
                               if x.std() > 1e-12 and y.std() > 1e-12 else None)}
    if not light:
        return None, {"reason": "no band had enough pixels after erosion",
                      "per_band": per}
    rho = (sxy / math.sqrt(sxx * syy)) if sxx > 1e-30 and syy > 1e-30 else None
    return ({"rho": (round(rho, 5) if rho is not None else None),
             "light_pct": round(sum(light) / len(light), 5),
             "still_pct": round(sum(still) / len(still), 5),
             "px": int(_erode(mask, int(math.ceil(3 * max(bands)))).sum()),
             "log_floor": round(float(floor), 8)},
            {"per_band": per, "D": dband})


def silhouette_departure(alpha, px_per_m, min_rows=100, want_max=True):
    """How far the outline wanders off the analytic curve it is fitted to.

    `crew_fireproof_overall`'s trouser silhouette fitted a quadratic taper to
    0.61 px RMS -- 1.6 mm at 373 px/m -- with a 1.23 px maximum. That is a
    machined cone, not Nomex over a knee. The reviewer's proposed test is
    implemented here directly: fit a quadratic, measure the residual.

    Sub-pixel, from the antialiasing coverage in the alpha channel, so the
    floor is around 0.1 px rather than the 0.5 px a binary mask would give.
    Only row-bands where the outline is a single unbroken run are used -- a row
    that crosses two figures has two outlines and no single profile.
    """
    H, W = alpha.shape
    solid = alpha > 0.5
    rows = []
    for y in range(H):
        idx = np.flatnonzero(solid[y])
        if idx.size < 20:
            continue
        if idx[-1] - idx[0] + 1 != idx.size:      # more than one run
            continue
        j0, j1 = int(idx[0]), int(idx[-1])
        a_l = float(alpha[y, j0 - 1]) if j0 > 0 else 0.0
        a_r = float(alpha[y, j1 + 1]) if j1 + 1 < W else 0.0
        rows.append((y, j0 - 0.5 - a_l, j1 + 0.5 + a_r))
    if len(rows) < min_rows:
        return None, {"reason": f"only {len(rows)} rows carry a single unbroken "
                                f"outline; need {min_rows}"}

    bands, cur = [], [rows[0]]
    for prev, nxt in zip(rows, rows[1:]):
        if nxt[0] == prev[0] + 1:
            cur.append(nxt)
        else:
            bands.append(cur)
            cur = [nxt]
    bands.append(cur)
    bands = [b for b in bands if len(b) >= min_rows]
    if not bands:
        return None, {"reason": "no contiguous run of "
                                f"{min_rows}+ single-outline rows"}

    best = None
    detail = []
    for b in bands:
        ys = np.array([r[0] for r in b], dtype=np.float64)
        for side, prof in (("left", np.array([r[1] for r in b])),
                           ("right", np.array([r[2] for r in b]))):
            c = np.polyfit(ys, prof, 2)
            res = prof - np.polyval(c, ys)
            rms = float(np.sqrt((res ** 2).mean()))
            # THE LOCAL REFIT IS THE STATISTIC, and the global one is advice.
            #
            # Fitting ONE quadratic to a whole outline measures the outline's
            # SHAPE, not its wander: on `crew_fireproof_overall` the
            # worst-fitting 136-row stretch came out at 3.94 px, and it was a
            # shoulder -- a shoulder is not a quadratic and no amount of cloth
            # is involved. The same fit on the control sphere gave 2.98 px,
            # because a 478-row circular arc is not a quadratic either. Both
            # numbers were about conic sections.
            #
            # Refitting inside each 100-row window removes any smooth
            # large-scale shape -- limb, taper, arc -- and leaves the
            # high-frequency departure, which is what a fold IS. At the stated
            # LAMBDA_HANG of 112 mm a fold is 42 px at 373 px/m, comfortably
            # inside a 100-row window, so the thing being looked for survives
            # while the limb it sits on does not.
            locs, lrms = [], []
            for s in range(0, len(ys) - min_rows + 1, min_rows // 2):
                yy = ys[s:s + min_rows]
                pp = prof[s:s + min_rows]
                cc = np.polyfit(yy, pp, 2)
                r_ = pp - np.polyval(cc, yy)
                locs.append(float(np.abs(r_).max()))
                lrms.append(float(np.sqrt((r_ ** 2).mean())))
            loc = float(np.median(locs)) if locs else 0.0
            lr = float(np.median(lrms)) if lrms else 0.0
            rec = {"side": side, "rows": len(ys),
                   "y0": int(ys[0]), "y1": int(ys[-1]),
                   "global_rms_px": round(rms, 3),
                   "global_rms_mm": round(1000.0 * rms / px_per_m, 3),
                   "rms_px": round(lr, 3),
                   "rms_mm": round(1000.0 * lr / px_per_m, 3),
                   "local_max_px": round(loc, 3),
                   "local_max_mm": round(1000.0 * loc / px_per_m, 3),
                   "windows": len(lrms)}
            detail.append(rec)
    if not detail:
        return None, {"reason": "no profile could be fitted"}
    # THE MEDIAN PROFILE, not the most extreme one. An outline has many stretches
    # and the question is what this item's fold language IS, not whether one
    # elbow somewhere departs from a curve.
    detail.sort(key=lambda d: d["rms_px"])
    best = detail[0] if not want_max else detail[len(detail) // 2]
    return best, {"profiles": detail[:8], "n_profiles": len(detail),
                  "statistic": "median over 100-row windows of the residual RMS "
                               "after refitting a quadratic inside each window"}


def disc_mask(H, W, cx, cy, rad):
    yy, xx = np.ogrid[:H, :W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad


def _two_light_block(flip_png, spec, rgba, L, solid, sub_m, sub_ok, unclippedA,
                     controls, part, mu_sub, sun_rc):
    """Measure the chosen frame against its flip. R2-060. Returns (block, why).

    THE MASK IS "LIT IN BOTH FRAMES", and it is NOT the intersection of the two
    frames' `lit_core`s. That was the first version and it was wrong, measured:
    `lit_core` keeps the brightest 40 % of a blurred copy OF ITS OWN FRAME, and
    the two frames are lit from opposite sides, so their brightest 40 %s are
    nearly disjoint BY CONSTRUCTION. On `pont_girder` that left 24,765 pixels in
    common out of 1,708,028 and 1,160,212 -- 1.4 % -- and the clause reported
    NOT MEASURED on an item that has plenty of surface lit in both. The cut
    exists to keep a band-pass out of a subject's own shadows; requiring the
    pixel to be un-crushed and un-clipped in BOTH frames already does that, and
    does it better, because a pixel in shadow under either sun is excluded by
    the frame that shadows it.

    It is still conservative in the right direction. A shadow edge that MOVES
    when the sun moves is relief -- the best evidence there is -- and this mask
    still throws those pixels away wherever one side crushes them. That can only
    cost the subject relief it really has; it can never manufacture any. An item
    that passes on this mask passes a fortiori.

    The geometry is asserted identical between the two frames before anything is
    measured. If the alpha mattes disagree the flip blend is not the same
    staging, and every number below would be the subject compared with a
    different subject.
    """
    if not os.path.exists(flip_png):
        return None, f"the flip frame {flip_png} has not been rendered"
    B = load_linear_rgba(flip_png)
    if B.shape != rgba.shape:
        return None, (f"the flip frame is {B.shape[1]}x{B.shape[0]}, the chosen "
                      f"frame {rgba.shape[1]}x{rgba.shape[0]}")
    LB = (0.2126 * B[:, :, 0] + 0.7152 * B[:, :, 1]
          + 0.0722 * B[:, :, 2]).astype(np.float64)
    solidB = B[:, :, 3].astype(np.float64) >= 0.995
    agree = float((solid == solidB).mean())
    if agree < 0.999:
        return None, (f"the two frames' alpha mattes agree on only {agree:.4%} "
                      "of pixels. Only the sun's azimuth may differ between "
                      "them; a different silhouette means a different scene, "
                      "and nothing measured across the pair would be about the "
                      "same object.")
    unclippedB = (LB > 0.0015) & (LB < 0.90)
    sub_okB = sub_m & unclippedB
    both = (sub_m & unclippedA & unclippedB)
    floor = LOG_FLOOR_FRAC * max(mu_sub, 1e-6)
    cache = {}
    st, det = two_light_bands(L, LB, both, floor, cache=cache)
    if st is None:
        return None, ("the two frames are lit in common on too little to "
                      f"measure: {det.get('reason')}. {int(both.sum())} px lit "
                      f"and unclipped in BOTH, of {int((sub_m & unclippedA).sum())} "
                      f"and {int(sub_okB.sum())}.")
    out = dict(st)
    out["px_lit_in_both"] = int(both.sum())
    out["px_chosen_lit"] = int((sub_m & unclippedA).sum())
    out["px_flip_lit"] = int(sub_okB.sum())
    out["px_chosen_lit_core"] = int(sub_ok.sum())
    out["alpha_agreement"] = round(agree, 6)
    out["flip_png"] = os.path.abspath(flip_png)
    out["sun_screen_direction_rowcol_flip"] = spec.get(
        "sun_screen_direction_rowcol_flip")
    # The dip RE-DERIVED on the light-driven half alone -- the shipped statistic,
    # unchanged, run on the part of the band that moved when the sun moved. Not
    # gated; it is what makes an inflated shipped number legible.
    d2 = (det.get("D") or {}).get(2)
    if d2 is not None:
        out["dip_light_driven"], out["dip_light_driven_detail"] = \
            relief_anisotropy(L, both, sun_rc, r=2, band=d2)
    # ... and every smooth control in the frame measured the same way, so the
    # amplitude has a floor from THIS frame rather than from a constant.
    cl = {}
    for name, msk, _full in controls:
        mk = msk & unclippedB
        if int(mk.sum()) < MIN_BAND_PX:
            continue
        cst, _ = two_light_bands(L, LB, mk, floor, cache=cache)
        if cst is not None:
            cl[name] = {"light_pct": cst["light_pct"], "rho": cst["rho"],
                        "still_pct": cst["still_pct"]}
    out["controls"] = cl
    names = [k for k, _ in part if k in cl]
    if names:
        strict = max(names, key=lambda k: cl[k]["light_pct"])
        out["light_control"] = cl[strict]["light_pct"]
        out["light_control_from"] = strict
        out["light_over_control"] = round(
            out["light_pct"] / max(cl[strict]["light_pct"], 1e-9), 4)
    else:
        out["light_control"] = out["light_over_control"] = None
        return out, ("no smooth control in this frame is both large enough and "
                     "at the subject's brightness, so the light-driven band has "
                     "no floor to be compared with. The comparison this clause "
                     "is made of does not exist in this frame.")
    return out, None


def lit_core(L, lit_all):
    """The brightest 40 % of the lit subject, as one contiguous region.

    Factored out of `analyse` for R2-060 and for one reason only: the flip frame
    has to be reduced to its lit core by the SAME rule as the chosen frame, and
    the way this project has repeatedly gone wrong is two copies of a rule that
    drift apart. One function, called twice.
    """
    if not lit_all.any():
        return lit_all, None
    sm = _blur(L, 8.0)
    cut = float(np.quantile(sm[lit_all], 0.60))
    ok = lit_all & (sm >= cut)
    if int(ok.sum()) < MIN_BAND_PX * 3:
        return lit_all, None                    # too small to subdivide
    return ok, cut


def analyse(png, spec, flip_png=None):
    """Every render-side number, plus the frame's own fitness to be measured."""
    rgba = load_linear_rgba(png)
    H, W, _ = rgba.shape
    exp_w, exp_h = spec["resolution"]
    notes = []
    if (W, H) != (exp_w, exp_h):
        return None, [f"witness PNG is {W}x{H}, staged for {exp_w}x{exp_h}"]

    rgb = rgba[:, :, :3].astype(np.float64)
    alpha = rgba[:, :, 3].astype(np.float64)
    L = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]

    scx, scy = spec["ref_sphere_centre_px"]
    pcx, pcy = spec["ref_plane_centre_px"]
    rr = spec["ref_radius_px"]
    solid = alpha >= 0.995
    # inside the sphere's own projection with room to spare, so every pixel is
    # certainly sphere: the controls are the frontmost objects in the frame
    sph_m = disc_mask(H, W, scx, scy, rr * 0.80) & solid
    pln_m = disc_mask(H, W, pcx, pcy, rr * 0.62) & solid
    # exclusion discs sized from each primitive's own projected extent plus a
    # margin, so no control edge leaks into the subject statistics
    excl = disc_mask(H, W, scx, scy, rr * 1.25) | disc_mask(H, W, pcx, pcy, rr * 1.30)
    # AND THE WEDGE. Leaving it out of this cost one whole run: the six wedge
    # patches are opaque geometry, so `solid` picked them up as subject, adding
    # 330,000 perfectly flat bright pixels to the very statistic they exist to
    # be compared against. The subject's mean went 0.033 -> 0.082 and every
    # number in that report was of the subject blended with its own control.
    _yy, _xx = np.ogrid[:H, :W]
    for _cx, _cy, _w, _h in (spec.get("wedge_boxes_px") or []):
        excl |= ((np.abs(_xx - _cx) <= _w * 0.62) & (np.abs(_yy - _cy) <= _h * 0.85))
    sub_m = solid & ~excl
    # 16-bit PNG, so the shadow end is worth keeping: 0.0015 linear is sRGB code
    # ~2800 of 65535, decades above quantisation. An 8-bit file could not be
    # measured this far down, which is why the witness frame is written 16-bit.
    unclipped = (L > 0.0015) & (L < 0.90)

    stat = {
        "subject_px": int(sub_m.sum()),
        "sphere_px": int(sph_m.sum()),
        "plane_px": int(pln_m.sum()),
        "subject_mean_linear": round(float(L[sub_m].mean()), 6) if sub_m.any() else None,
        "sphere_mean_linear": round(float(L[sph_m].mean()), 6) if sph_m.any() else None,
        "plane_mean_linear": round(float(L[pln_m].mean()), 6) if pln_m.any() else None,
        "subject_clipped_frac": round(float((L[sub_m] >= 0.90).mean()), 4) if sub_m.any() else None,
        "subject_crushed_frac": round(float((L[sub_m] <= 0.004).mean()), 4) if sub_m.any() else None,
        "sphere_clipped_frac": round(float((L[sph_m] >= 0.90).mean()), 4) if sph_m.any() else None,
    }

    # --- IS THIS FRAME FIT TO BE MEASURED? ---------------------------------
    # Ask of the CONTROL, whose answer is known in advance. If the sphere is not
    # lit by a warm sun from the side, the render did not come out of the rig
    # this file staged, and nothing measured in it means what it says.
    if stat["subject_px"] < MIN_SUBJECT_PX:
        notes.append(f"only {stat['subject_px']} subject pixels "
                     f"(need {MIN_SUBJECT_PX}) -- the subject does not fill "
                     f"enough of the witness frame to measure")
    if stat["sphere_px"] < MIN_CONTROL_PX:
        notes.append(f"reference SPHERE covers {stat['sphere_px']} px "
                     f"(need {MIN_CONTROL_PX}) -- no control, no comparison")
    if stat["plane_px"] < MIN_CONTROL_PX:
        notes.append(f"reference PLANE covers {stat['plane_px']} px "
                     f"(need {MIN_CONTROL_PX}) -- no control, no comparison")
    if stat["sphere_px"] >= MIN_CONTROL_PX:
        lit = L[sph_m]
        cut = np.quantile(lit, 0.90)
        hi = sph_m & (L >= cut)
        rb = float((rgb[:, :, 0][hi] - rgb[:, :, 2][hi]).mean())
        stat["sphere_highlight_R_minus_B"] = round(rb, 5)
        stat["sphere_dynamic_range"] = round(float(lit.max() / max(lit.min(), 1e-6)), 2)
        if rb <= 0.002:
            notes.append(
                f"the control sphere's brightest decile has R-B = {rb:+.4f}. A "
                "12.5 deg sun is warm; blue at or above red means the frame has "
                "no direct solar component -- the same signature WAVE1-PEEP "
                "SYSTEMIC 1 found. Nothing measured under this light counts.")
        if stat["sphere_clipped_frac"] > 0.25:
            notes.append(f"{stat['sphere_clipped_frac']:.0%} of the control "
                         "sphere is clipped; contrast cannot be measured "
                         "through a blown highlight (lower SUN_ENERGY)")
    if stat["subject_px"] >= MIN_SUBJECT_PX:
        if stat["subject_clipped_frac"] > 0.40:
            notes.append(f"{stat['subject_clipped_frac']:.0%} of the subject is "
                         "clipped -- measure contrast on a surface that has "
                         "tonal range left")
        if stat["subject_crushed_frac"] > 0.60:
            notes.append(f"{stat['subject_crushed_frac']:.0%} of the subject is "
                         "crushed to black -- the subject is in its own shadow, "
                         "reframe or relight")

    # `notes` are FRAME-VALIDITY problems only: reasons the whole witness frame
    # is unfit to be measured. They are kept separate from a single measurement
    # failing, so a report can say which check was not measured instead of
    # blaming everything on the frame.
    m = {"frame": stat, "why": {}}
    if notes:
        return m, notes

    # --- band-passed contrast, subject vs the two controls -----------------
    # MEASURE THE SURFACE WHERE THERE IS LIGHT TO SEE IT BY. The peep measured
    # "flat, fully-lit panels" and was right to: a band-pass over a subject's own
    # shadows reports the shadows. Including them here gave r1 = 6.4 % of mean on
    # a timber deck against the peep's ~1 % on fabric, which is a measurement of
    # shading, not of surface. The cut is taken on a BLURRED copy so the retained
    # region is spatially contiguous -- a percentile cut on raw luminance
    # shatters the mask into slivers that erosion then deletes.
    sub_ok, cut = lit_core(L, sub_m & unclipped)
    m["lit_cut_linear"] = round(cut, 6) if cut is not None else None
    m["frame"]["subject_px_lit"] = int(sub_ok.sum())
    mu_sub = float(L[sub_ok].mean()) if sub_ok.any() else 0.0
    # LUMINANCE-MATCHED CONTROLS. Same divisor, same photon count, same denoiser
    # behaviour -- so what is left of the difference is structure.
    lo_w, hi_w = 0.60 * mu_sub, 1.70 * mu_sub
    matched = (L >= lo_w) & (L <= hi_w)
    sph_ok = sph_m & unclipped & matched
    pln_ok = pln_m & unclipped & matched
    m["luminance_window"] = [round(lo_w, 6), round(hi_w, 6)]
    m["frame"]["subject_mean_measured"] = round(mu_sub, 6)
    sun_rc = spec["sun_screen_direction_rowcol"]

    # ---- EVERY SMOOTH CONTROL IN THE FRAME, EACH MEASURED SEPARATELY -------
    # A control participates in the verdict only if it is BOTH big enough for a
    # standard deviation to mean something AND at the subject's brightness. Then
    # the bar is the STRICTEST participant. That is the whole point of putting
    # several in: no single primitive can be at every brightness, so the frame
    # carries a range and the one that matches is the one that speaks.
    controls = [("sphere", sph_m & unclipped & matched, sph_m),
                ("card", pln_m & unclipped & matched, pln_m)]
    for i, box in enumerate(spec.get("wedge_boxes_px") or []):
        cx, cy, wpx, hpx = box
        yy, xx = np.ogrid[:H, :W]
        # 0.80 of the nominal box, so projection slop cannot walk off the patch
        inb = ((np.abs(xx - cx) <= wpx * 0.40) & (np.abs(yy - cy) <= hpx * 0.40))
        alb = (spec.get("wedge_albedos") or [None] * 9)[i]
        controls.append((f"wedge{i}(alb {alb})", inb & solid & unclipped & matched,
                         inb & solid))
    ctl = {}
    for name, msk, full in controls:
        n = int(msk.sum())
        rec = {"px_matched": n, "px_total": int(full.sum()),
               "mean_linear": (round(float(L[full].mean()), 6)
                              if full.any() else None)}
        if n >= MIN_BAND_PX:
            b, _, _ = contrast_bands(L, msk)
            rec["bands"] = b
            rec["fine"] = _agg(b or {}, FINE_BANDS)
            rec["relief"], _ = relief_anisotropy(L, msk, sun_rc)
        else:
            rec["bands"] = rec["fine"] = rec["relief"] = None
            rec["skipped"] = (f"{n} px in the subject's luminance window "
                              f"{m['luminance_window']}; need {MIN_BAND_PX}")
        ctl[name] = rec
    m["controls"] = ctl
    part = [(k, v) for k, v in ctl.items() if v.get("fine") is not None]
    m["controls_participating"] = [k for k, _ in part]

    m["bands_subject"], _, _ = contrast_bands(L, sub_ok)
    m["fine_subject"] = _agg(m["bands_subject"] or {}, FINE_BANDS)
    m["coarse_subject"] = _agg(m["bands_subject"] or {}, COARSE_BANDS)
    m["fine_control"] = (round(max(v["fine"] for _, v in part), 4)
                         if part else None)
    m["fine_control_from"] = (max(part, key=lambda kv: kv[1]["fine"])[0]
                              if part else None)
    m["fine_over_control"] = None
    if m["fine_subject"] is None:
        m["why"]["microstructure"] = (
            f"the SUBJECT has no measurable band in {FINE_BANDS} px: "
            f"{int(sub_ok.sum())} usable pixels, and every band erodes its patch "
            f"by 3x its own radius, which leaves nothing. THIS IS A STATEMENT "
            f"ABOUT THE FRAMING, NOT ABOUT THE ASSET, and it is still not a "
            f"pass. At this item's manifest framing the subject is simply too "
            f"small on the 4K master to carry a measurable surface. Either the "
            f"manifest's nearest_camera_m is wrong for this item -- which "
            f"docs/PLAN-scope-optimisation.md says it is for most of them, "
            f"because it is measured abeam -- in which case re-run with "
            f"--filmed-distance-m set to the real figure; or the item genuinely "
            f"is never seen close enough for its surface to matter, in which "
            f"case say so and have the check scoped out deliberately rather "
            f"than silently.")
    elif m["fine_control"] is None:
        m["why"]["microstructure"] = (
            f"NO smooth control in the frame is both large enough and at the "
            f"subject's brightness (subject mean {mu_sub:.5f}, window "
            f"{m['luminance_window']}). Per-control reasons are in "
            f"`controls`. Nothing here is a pass -- the comparison this check "
            f"is made of does not exist in this frame.")
    else:
        m["fine_over_control"] = round(m["fine_subject"] / max(m["fine_control"], 1e-9), 4)
    m["fine_over_coarse"] = (round(m["fine_subject"] / m["coarse_subject"], 4)
                             if m["fine_subject"] and m["coarse_subject"] else None)
    # SPECTRAL BALANCE, against the control's own spectral balance.
    #
    # This is the wave-1 signature stated as a number: "all the energy sat at
    # r8-r16 (2-4 cm) and none at r1-r4 (3-11 mm) -- the signature of a soft
    # AO/dirt mask with no fabric under it". Measured on `armco_w_beam`, at
    # 1436 px/m where r1 is 0.7 mm, i.e. zinc-spangle scale:
    #
    #     subject   r1 0.172  r2 0.299  r4 0.512  r8 0.765     fine/coarse 0.308
    #     control   r1 0.048  r2 0.034  r4 0.033  r8 0.058     fine/coarse 0.71
    #
    # The barrier's energy is MORE coarse-weighted than a featureless smooth
    # surface's is. It has a mechanism at centimetre scale and nothing at
    # millimetre scale -- which is the peep's "zero crystal boundaries, zero
    # polygonal facets, zero dendrite" in one ratio. Referenced to the control,
    # so a denoiser or sample-count change moves both terms together.
    cf = [v["bands"] for _, v in part if v.get("bands")]
    ctl_foc = []
    for b_ in cf:
        f_, c_ = _agg(b_, FINE_BANDS), _agg(b_, COARSE_BANDS)
        if f_ and c_:
            ctl_foc.append(f_ / c_)
    m["fine_over_coarse_control"] = (round(min(ctl_foc), 4) if ctl_foc else None)
    # Reported alongside, because the mean over r1-r2 demands structure at BOTH
    # scales while the max asks only that it exists at one. A borderline item is
    # a different conversation depending on which of the two is carrying it.
    m["fine_max_subject"] = _agg_max(m["bands_subject"] or {}, FINE_BANDS)

    # --- COLOUR DIVERSITY. Reported, deliberately NOT gated. ----------------
    #
    # "stones are untextured low-poly blobs of a single colour -- six sampled
    # stones cluster at one hue, one value, one material" is a wave-1 verdict,
    # and `terrain_ground` passes every check in this file while being exactly
    # that. The reason is that every check here is luminance-based, and one hue
    # is not a luminance fault.
    #
    # It is NOT gated, for the same reason triangles-per-instance is not: the
    # controls are neutral grey by construction, so they give no floor to
    # compare against, and an absolute bar on chromatic spread invented without
    # calibration would be a guess wearing a measurement's clothes. What it is
    # instead is the number put in front of whoever reads the report. A surface
    # whose `single_hue_fraction` is near 1.0 has one colour, whatever else is
    # true of it.
    tot = rgb.sum(axis=2)
    ok_c = sub_ok & (tot > 1e-5)
    if int(ok_c.sum()) >= MIN_BAND_PX:
        cu = rgb[:, :, 0][ok_c] / tot[ok_c]
        cv = rgb[:, :, 1][ok_c] / tot[ok_c]
        mu_u, mu_v = float(np.median(cu)), float(np.median(cv))
        d = np.sqrt((cu - mu_u) ** 2 + (cv - mu_v) ** 2)
        m["colour"] = {
            "px": int(ok_c.sum()),
            "median_chromaticity": [round(mu_u, 5), round(mu_v, 5)],
            "chroma_sd_u": round(float(cu.std()), 5),
            "chroma_sd_v": round(float(cv.std()), 5),
            # fraction of the surface inside a tight ball around its own median
            # hue. 1.00 means one colour; a real weathered surface spreads.
            "single_hue_fraction_r010": round(float((d <= 0.010).mean()), 4),
            "single_hue_fraction_r005": round(float((d <= 0.005).mean()), 4),
            "chroma_p95_radius": round(float(np.quantile(d, 0.95)), 5),
            "gated": False,
            "note": "NOT GATED -- the smooth controls are neutral by "
                    "construction so there is no in-frame floor for chroma, "
                    "and an absolute bar here would be uncalibrated. Read it.",
        }
    else:
        m["colour"] = {"px": int(ok_c.sum()), "gated": False,
                       "note": "too few pixels to characterise colour"}

    # --- relief -------------------------------------------------------------
    m["relief_subject"], m["relief_subject_detail"] = relief_anisotropy(L, sub_ok, sun_rc)
    rel_all = [v["relief"] for _, v in part if v.get("relief") is not None]
    rel = [v for v in rel_all if abs(v) <= RELIEF_CONTROL_SANE]
    m["relief_control_all"] = [round(v, 5) for v in rel_all]
    m["relief_control"] = round(max(rel), 5) if rel else None
    m["relief_control_degenerate"] = (
        None if not rel_all or len(rel) == len(rel_all) else
        f"{len(rel_all) - len(rel)} of {len(rel_all)} control dips fell outside "
        f"+/-{RELIEF_CONTROL_SANE} ({[round(v, 3) for v in rel_all]}) and were "
        f"discarded as the correlation of near-zero noise with itself"
        + ("; NO sane control remains, so the absolute floor decides alone"
           if not rel else ""))
    if m["relief_subject"] is None:
        m["why"]["relief"] = ("subject: "
                              + str(m["relief_subject_detail"].get("reason")))
    elif m["relief_control"] is None:
        m["why"]["relief"] = ("no participating smooth control yielded a "
                              "directional autocorrelation, so the subject's "
                              "number has nothing to be compared with")

    # --- R2-060. THE SAME SURFACE UNDER THE OTHER CANDIDATE SUN ------------
    m["two_light"] = None
    if flip_png is None:
        m["why"]["two_light"] = (
            "no flip frame was supplied. The dip ALONE cannot tell a painted "
            "step from a lip and a shadow -- measured, on a flat quad with four "
            "vertices and z identically zero, which outscores real 2 mm ribs "
            "0.6311 to 0.6082. Stage and render `witness_flip.png`.")
    else:
        m["two_light"], m["why"]["two_light"] = _two_light_block(
            flip_png, spec, rgba, L, solid, sub_m, sub_ok, unclipped, controls,
            part, mu_sub, sun_rc)

    # --- silhouette, and the instrument floor measured on the control -------
    # The control sphere's outline is an exact analytic curve, so the RMS the
    # sub-pixel edge estimator reports on IT is this frame's own noise floor --
    # measured, per frame, rather than assumed.
    sph_alpha = np.zeros_like(alpha)
    ring = disc_mask(H, W, scx, scy, rr * 1.03)
    sph_alpha[ring] = alpha[ring]
    # If subject geometry happens to sit right beside the sphere, its pixels join
    # the sphere's run and the "control outline" stops being the sphere's. The
    # sphere's chord width at each row is known in closed form, so any row whose
    # run is not that width to within 6 % is thrown away -- the control has to be
    # verifiable as the control, or it is not one.
    yy = np.arange(H, dtype=np.float64)
    dy = np.abs(yy - scy)
    chord = 2.0 * np.sqrt(np.maximum(rr * rr - dy * dy, 0.0))
    keep = chord > 40.0
    for y in range(H):
        if not keep[y]:
            sph_alpha[y, :] = 0.0
            continue
        w_meas = float((sph_alpha[y] > 0.5).sum())
        if abs(w_meas - chord[y]) > 0.06 * chord[y] + 3.0:
            sph_alpha[y, :] = 0.0
    ctl_sil, ctl_det = silhouette_departure(sph_alpha, spec["px_per_m"],
                                            want_max=False)
    m["silhouette_control"] = ctl_sil
    m["silhouette_control_rows"] = int((sph_alpha > 0.5).any(axis=1).sum())
    if ctl_sil is None:
        m["silhouette_control_why"] = str(ctl_det.get("reason"))

    sil_alpha = alpha.copy()
    sil_alpha[excl] = 0.0
    best, sil_detail = silhouette_departure(sil_alpha, spec["px_per_m"])
    m["silhouette"] = best
    m["silhouette_detail"] = sil_detail
    if best is None:
        m["why"]["silhouette"] = str(sil_detail.get("reason"))
    elif ctl_sil is None:
        m["why"]["silhouette"] = ("the control sphere's own outline could not be "
                                  "fitted, so this frame's sub-pixel edge noise "
                                  "floor is unknown and the subject's RMS cannot "
                                  "be judged against it")
    return m, notes


# ===========================================================================
# MAIN
# ===========================================================================

def stage_flip_existing(src):
    """Retrofit the other-sun-side blend onto an already-staged witness.

    Opens the witness, mirrors GATE_SUN about GATE_CAM's azimuth, and saves.
    NOTHING ELSE IS TOUCHED -- same camera, same subject, same controls, same
    energy, same sampler. The flip frame differs from the chosen frame in one
    scalar, and it is asserted to differ in exactly that (see
    `mirror_sun_about_camera`) before the file is written.

    Also re-derives the flip sun's screen direction into the witness spec beside
    it, if one is there, so a later `--from-png` run has it.
    """
    src = os.path.abspath(src)
    bpy.ops.wm.open_mainfile(filepath=src)
    scn = bpy.context.scene
    sun = bpy.data.objects.get("GATE_SUN")
    cam = bpy.data.objects.get("GATE_CAM")
    if sun is None or cam is None:
        raise SystemExit(f"REFUSING: {src} has no GATE_SUN/GATE_CAM; it was not "
                         "staged by this gate and cannot be flipped by it")
    scn.camera = cam
    bpy.context.view_layer.update()
    detail, light_dir = mirror_sun_about_camera(sun, cam)
    dst = flip_path(src)
    bpy.ops.wm.save_as_mainfile(filepath=dst, copy=True, compress=True)
    rowcol = sun_screen_rowcol(cam, light_dir)
    print(f">> {os.path.basename(src)}: sun {detail['chosen_sun_az_deg']:+.2f} "
          f"-> {detail['flip_sun_az_deg']:+.2f} deg "
          f"({detail['ground_separation_deg']:.1f} deg round, elevation "
          f"{detail['elevation_deg']:+.2f} unchanged, camera at "
          f"{detail['camera_az_deg']:+.2f})")
    print(f">> wrote {dst}")
    for cand in (os.path.join(os.path.dirname(src), "witness_spec.json"),):
        if os.path.exists(cand):
            sp = json.load(open(cand))
            sp["sun_screen_direction_rowcol_flip"] = rowcol
            sp["witness_blend_flip"] = dst
            sp["flip_sun"] = detail
            json.dump(sp, open(cand, "w"), indent=1)
            print(f">> updated {cand}")
    return 0


def main():
    a = parse_args()
    if a.stage_flip:
        return stage_flip_existing(a.stage_flip)
    manifest = json.load(open(a.manifest))
    rec = item_record(manifest, a.item)
    deps = bpy.context.evaluated_depsgraph_get()

    objs, sel_why = select_objects(bpy.context.scene, rec, a.prefix, a.collection)
    if not objs:
        raise SystemExit(
            f"REFUSING: no mesh objects selected for '{a.item}' via {sel_why}. "
            "There is nothing to accept. An empty test set is a failure to "
            "test, not a successful test (R2-018).")
    prefix_note = prefix_integrity(bpy.context.scene, rec, a.prefix, objs)

    hero = bool(rec.get("hero"))
    dist = float(rec.get("nearest_camera_m", 25.0))
    px = float(rec.get("onscreen_px_4k", 0) or 0)
    framing_src = "item_manifest.json"
    if a.filmed_distance_m is not None:
        dist = float(a.filmed_distance_m)
        framing_src = "--filmed-distance-m (caller override of the manifest)"
    if a.onscreen_px_4k is not None:
        px = float(a.onscreen_px_4k)
        framing_src += " + --onscreen-px-4k"
    lens = float(rec.get("lens_at_closest_mm", 35.0) or 35.0)
    declared = int(rec.get("instances", 1) or 1)
    flexible, flex_why = classify_flexible(rec, a.flexible)

    wbdir = os.path.join(WITNESS_BLEND_ROOT, a.item)
    wdir = os.path.abspath(a.witness_dir) if a.witness_dir else wbdir
    os.makedirs(wbdir, exist_ok=True)
    os.makedirs(wdir, exist_ok=True)
    wblend = os.path.join(wbdir, "witness.blend")
    wspec_path = os.path.join(wdir, "witness_spec.json")
    wpng = os.path.join(wdir, "witness.png")

    # ---- 1. EXTERNAL ASSETS ---------------------------------------------
    ext_imgs = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    mat = material_depth(objs)
    ext_ok = not ext_imgs and mat["image_texture_nodes"] == 0

    # ---- 1b. RELIEF WIRING (R2-072) --------------------------------------
    # Runs before the GPU job on purpose: if the bump never reached the shader,
    # check 6 would measure a flat surface and never say why, and the render
    # would be paid for to learn nothing.
    wiring = relief_wiring(objs)
    wiring_ok = wiring["ok"]

    # ---- 2. MATERIAL DEPTH (node floor; NOT an appearance measurement) ----
    need_tex = 6 if hero else 3
    mat_ok = mat["procedural_texture_nodes"] >= need_tex

    # ---- 3. DETAIL AT THE DISTANCE IT IS SEEN ----------------------------
    px_per_m = (RES_X_4K * lens / SENSOR_MM) / max(dist, 0.01)
    es = edge_stats_m(objs, deps)
    p10_px = es["p10"] * px_per_m if es else None
    med_px = es["median"] * px_per_m if es else None
    tris, per_tris = tri_count(objs, deps)
    detail_limit_px = 6.0 if hero else 16.0
    geo_ok = p10_px is not None and p10_px <= detail_limit_px

    # ---- 4. PER-INSTANCE VARIATION ---------------------------------------
    var, boxes = instance_variation(objs, deps, per_tris)
    gn_instanced = declared > 1 and var["n"] < declared * 0.5
    real = realized_instances(deps, {o.name for o in objs}) if gn_instanced else None

    # ONE RULE, ONE PLACE, TESTABLE WITHOUT A GATE RUN. See
    # `variation_verdict` for what changed in R2-1381 and why.
    var_ok = variation_verdict(declared, var, real, gn_instanced)

    pre = {"no_external_assets": ext_ok, "material_depth": mat_ok,
           "relief_wiring_reaches_the_shader": wiring_ok,
           "geometry_resolves_at_distance": geo_ok,
           "per_instance_variation": var_ok}
    pre_ok = all(pre.values())

    # ---- 5/6/7. THE WITNESS FRAME ----------------------------------------
    subject_why = render_info = wspec = img = None
    render_err = None
    subject_name = None
    unmeasurable = []
    if not pre_ok and not a.always_render:
        unmeasurable.append(
            "witness frame not rendered: " +
            ", ".join(k for k, v in pre.items() if not v) +
            " already failed, so the GPU job was skipped. Fix those, re-run, "
            "and the rendered checks will be measured. (--always-render "
            "measures them anyway.)")
    else:
        try:
            subject, subject_why = pick_subject(objs, per_tris, a.subject,
                                               declared, boxes)
            subject_name = subject.name
            if a.from_png:
                if not os.path.exists(wspec_path):
                    raise RuntimeError(
                        f"--from-png needs the witness spec at {wspec_path}, "
                        "written by a staging run. Without it the gate does not "
                        "know which pixels are the control, and a control it "
                        "has to guess at is not a control.")
                wspec = json.load(open(wspec_path))
                wpng = os.path.abspath(a.from_png)
                render_info = {"backend": "supplied PNG (--from-png)",
                               "png": wpng}
            else:
                wspec = stage_witness(subject, rec, dist, lens, wblend, wspec_path)
                if a.stage_only:
                    raise RuntimeError(
                        "--stage-only: witness blend written, nothing rendered, "
                        "so checks 5-7 were not measured.")
                render_info = render_witness_pair(wblend, wpng, a.samples, a)
            # R2-060. The flip frame defaults to sitting beside the chosen one
            # under one naming rule (`flip_path`) that the writer and the reader
            # share, so there is no path for the two to disagree.
            wflip = os.path.abspath(a.from_png_flip) if a.from_png_flip \
                else flip_path(wpng)
            if not os.path.exists(wflip):
                wflip = None
            render_info["flip_png_used"] = wflip
            img, notes = analyse(wpng, wspec, flip_png=wflip)
            unmeasurable.extend(notes)
        except Exception as exc:                       # noqa: BLE001
            render_err = f"{type(exc).__name__}: {exc}"
            unmeasurable.append("witness frame unusable -- " + render_err)

    # ----- the three rendered checks --------------------------------------
    micro_ok = relief_ok = sil_ok = None
    frame_ok = False
    micro_why = relief_why = sil_why = None

    if img and not unmeasurable:
        frame_ok = True
        why = img.get("why", {})

        # 5. SURFACE MICROSTRUCTURE.
        # Two clauses, and the first is the one wave 1 needed. A surface that
        # carries less 1-4 px structure than a featureless primitive in the same
        # frame is not a surface, whatever its node graph says. The second is a
        # backstop for the case where the sphere reads anomalously low: the flat
        # card is the pipeline's noise floor, and doubling the noise floor is the
        # least that "has any structure at all" can mean. Both are RATIOS in the
        # same frame, so neither moves if the filmed distance turns out to be
        # wrong.
        if img.get("fine_over_control") is None:
            micro_ok = None
            micro_why = "NOT MEASURED -- " + why.get("microstructure", "unknown")
            unmeasurable.append("surface_microstructure: " + micro_why)
        else:
            foc, focc = img.get("fine_over_coarse"), img.get("fine_over_coarse_control")
            ok_amp = img["fine_over_control"] >= FINE_OVER_CONTROL
            # R2-635. THE SPECTRAL-BALANCE CLAUSE COULD NOT FIRE ON ITS OWN
            # WORST CASE, AND IT SAID NOTHING WHILE FAILING TO.
            #
            # This was:
            #
            #     ok_bal = (foc is None or focc is None or foc >= focc)
            #
            # -- an unmeasurable balance PASSED.
            #
            # MEASURED CAUSE, and it is not the one that looks obvious. Across
            # ALL ELEVEN wave-1 items reporting `spectral balance None`, it is
            # the COARSE band that is missing and never the fine one:
            #
            #   crew_fireproof_overall  bands r1,r2,r4,r8,r16 = 9.86,16.82,40.89,null,null
            #   spectator_seated                               8.71,13.48,null,null,null
            #   tyre_wall_tyre                                 1.41, 1.83,null,null,null
            #
            # So `fine_over_coarse` is None because r8/r16 COULD NOT BE MEASURED
            # at this subject's pixel size -- the lit patch is too small to
            # survive a radius-8 or radius-16 band-pass and its erosion -- NOT
            # because the surface carries no energy there. This is an INSTRUMENT
            # LIMIT, not a property of the item, which is exactly why the answer
            # is VACUOUS and not FAIL.
            #
            # And it is systematic in the worst place: the clause exists to
            # catch "all the energy sat at r8-r16 and none at r1-r4", which
            # REQUIRES a measurable coarse band. On 11 of 30 measured wave-1
            # items there never is one, so on a third of the campaign the clause
            # could not fire at all -- and said nothing, because it passed.
            # Among those eleven: `crew_fireproof_overall`, a MUST-REJECT the
            # wave-1 peep found renders as vinyl and measured FLATTER THAN THE
            # PLACEHOLDER BLOB HEAD, and `driver_figure`.
            #
            # VACUOUS, NOT PASS -- and not FAIL either. This project already
            # has a verdict for an arm that cannot decide on an empty set, and
            # it is the one `gate_exit` calls VACUOUS: NOT a pass, and
            # deliberately distinguishable from a failure so a caller can tell
            # "your item is flat" from "the instrument could not see". Silently
            # passing is the one option that is definitely wrong.
            #
            # ORDER MATTERS. A definite amplitude failure is still a FAILURE --
            # vacuity only applies when the undecidable clause is the DECIDING
            # one. An item that already fails `fine_over_control` does not get
            # upgraded to "could not measure" by a second clause going blind.
            if not ok_amp:
                ok_bal = None
                micro_ok = False
            elif foc is None or focc is None:
                ok_bal = None
                micro_ok = None
            else:
                ok_bal = foc >= focc
                micro_ok = bool(ok_bal)
            micro_why = (f"fine(r{FINE_BANDS[0]}-r{FINE_BANDS[-1]}) "
                         f"{img['fine_subject']:.3f} % of mean vs the strictest "
                         f"brightness-matched smooth control "
                         f"{img['fine_control']:.3f} "
                         f"[{img['fine_control_from']}] = "
                         f"x{img['fine_over_control']:.2f}, need "
                         f"x{FINE_OVER_CONTROL:.2f}"
                         + ("" if ok_amp else
                            " -- AT OR NEAR THE PIPELINE'S SMOOTH-SURFACE FLOOR")
                         + f"; controls in play {img.get('controls_participating')}"
                         f"; spectral balance fine/coarse "
                         f"{img.get('fine_over_coarse')} vs control "
                         f"{img.get('fine_over_coarse_control')}"
                         + ("" if ok_bal is True or ok_bal is None else
                            " -- MORE COARSE-WEIGHTED THAN A FEATURELESS SMOOTH "
                            "SURFACE: there is a mechanism at centimetre scale "
                            "and nothing at millimetre scale, which is a "
                            "3-5x amplitude shortfall, not an absence")
                         + ("" if not (ok_amp and ok_bal is None) else
                            " -- SPECTRAL BALANCE NOT MEASURABLE: "
                            f"fine_over_coarse={foc!r}, control={focc!r}. "
                            "The COARSE band could not be measured at this "
                            "subject's pixel size, so there is nothing to "
                            "compare the fine band against. VACUOUS: NOT a "
                            "pass, and NOT a failure of the item -- it is an "
                            "instrument limit. See R2-635."))
            if micro_ok is None:
                unmeasurable.append("surface_microstructure: " + micro_why)

        # 6. RELIEF.
        if img.get("relief_subject") is None:
            relief_ok = None
            relief_why = "NOT MEASURED -- " + why.get("relief", "unknown")
            unmeasurable.append("relief_reads_as_lip_and_shade: " + relief_why)
        elif img.get("relief_control") is None:
            # Every control's dip was degenerate. The absolute floor still
            # applies, and the report says the margin clause was dropped.
            relief_ok = bool(img["relief_subject"] >= RELIEF_DIP_FLOOR)
            relief_why = (f"lip-and-shadow dip {img['relief_subject']:+.4f} vs the "
                          f"absolute floor {RELIEF_DIP_FLOOR:.3f} ALONE -- "
                          + str(img.get("relief_control_degenerate")))
        else:
            relief_ok = bool(img["relief_subject"]
                             >= img["relief_control"] + RELIEF_MARGIN
                             and img["relief_subject"] >= RELIEF_DIP_FLOOR)
            relief_why = (
                f"lip-and-shadow dip {img['relief_subject']:+.4f} along the "
                f"light vs the strictest smooth control "
                f"{img['relief_control']:+.4f} (need control + "
                f"{RELIEF_MARGIN:.3f} AND >= {RELIEF_DIP_FLOOR:.3f} absolute). "
                + (str(img.get("relief_control_degenerate")) + " "
                   if img.get("relief_control_degenerate") else "")
                + ("" if relief_ok else
                   "The features on this surface are single-value marks: they "
                   "have no sunward lip and no lee shadow, which is how a "
                   "printed decal behaves and not how a physical object does."))

        # 6b. ... AND THE PATTERN MUST BELONG TO THE LIGHT. R2-060.
        #
        # The dip above cannot tell a painted step from a lip and a shadow --
        # measured, on a four-vertex quad with z identically zero, which
        # outscores real 2 mm ribs. So the dip is now the FIRST of three
        # clauses, never the whole check, and this is the other two.
        #
        # THREE CLAUSES, each with a control that fails it:
        #   dip                  0.12 on a flat plate; DEFEATED outright by
        #                        aligned paint, which scores 0.63 against real
        #                        2 mm ribs' 1.01 -- so it can no longer decide
        #                        alone, and it is kept because a surface with no
        #                        dipole at the lip spacing has no relief either
        #   fine_over_control    the same bar check 5 applies, restated here so
        #                        this check means something read on its own
        #   light_over_control   THE SEPARATOR. 1.00 on the flat plate and on
        #                        the flat cylinder (they ARE the floor), 0.02
        #                        on all four painted decoys including the
        #                        HIGH-CONTRAST one and the roughness-only one,
        #                        1.40 on the painted CYLINDER, against 2.16 to
        #                        2.61 on real ribs.
        tl = img.get("two_light")
        if relief_ok is None:
            pass                     # the dip itself was not measurable; said
        elif tl is None or tl.get("light_over_control") is None:
            relief_ok = None
            relief_why = ("NOT MEASURED -- the dip alone cannot separate paint "
                          "from geometry, and the two-light clause that can was "
                          "not measurable: "
                          + str(why.get("two_light", "unknown"))
                          + f" (dip was {img.get('relief_subject')})")
            unmeasurable.append("relief_reads_as_lip_and_shade: " + relief_why)
        else:
            amp_ok = tl["light_over_control"] >= LIGHT_OVER_CONTROL
            foc = img.get("fine_over_control")
            fine_ok = foc is not None and foc >= FINE_OVER_CONTROL
            was = relief_ok
            relief_ok = bool(relief_ok and amp_ok and fine_ok)
            relief_why += (
                f" | TWO-LIGHT: the band that MOVED when the sun crossed to its "
                f"other candidate side is {tl['light_pct']:.4f} % contrast, "
                f"x{tl['light_over_control']:.2f} the strictest smooth control's "
                f"({tl.get('light_control_from')}, need "
                f"x{LIGHT_OVER_CONTROL:.2f}) -- {'PASS' if amp_ok else 'FAIL'}. "
                f"The band that did NOT move is {tl['still_pct']:.4f} %, and "
                f"corr(chosen, flip) = {tl['rho']:+.4f} (REPORTED, NOT GATED -- "
                f"see LIGHT_OVER_CONTROL). Fine-band contrast "
                f"x{foc if foc is not None else float('nan'):.2f} the control "
                f"(need x{FINE_OVER_CONTROL:.2f}) -- "
                f"{'PASS' if fine_ok else 'FAIL'}."
                + ("" if relief_ok else
                   (" The dip was clear but the surface's fine band barely "
                    "moved when the light did: on this evidence the pattern "
                    "belongs to the paint, not to the shape."
                    if was and not amp_ok else "")))
            if tl.get("dip_light_driven") is not None:
                relief_why += (f" [dip re-derived on the light-driven half "
                               f"alone: {tl['dip_light_driven']:+.4f}]")

        # 7. SILHOUETTE -- flexible items only, and only where 5 mm is a pixel.
        wpm = (wspec or {}).get("px_per_m", px_per_m)
        mm5_px = SIL_RMS_MM * wpm / 1000.0
        if not flexible:
            sil_ok = "not_applicable"
            sil_why = f"rigid item ({flex_why}); an analytic outline is correct here"
        elif mm5_px < SIL_MIN_PX_FOR_5MM:
            # Scoping, not a fallback: at this item's OWN closest framing the
            # physical bar is under a pixel, so no fold this check could demand
            # would ever be visible in the film. The density is printed so the
            # decision is auditable rather than assumed.
            sil_ok = "not_applicable"
            sil_why = (f"flexible, but {wpm:.0f} px/m puts the {SIL_RMS_MM:.0f} mm "
                       f"physical bar at {mm5_px:.2f} px -- under the "
                       f"{SIL_MIN_PX_FOR_5MM:.1f} px the sub-pixel edge estimator "
                       "needs. Fold language cannot be seen at this item's "
                       "closest framing, so it is out of scope here, NOT passed.")
        elif img.get("silhouette") is None or img.get("silhouette_control") is None:
            sil_ok = None
            sil_why = "NOT MEASURED -- " + why.get("silhouette", "unknown")
            unmeasurable.append("silhouette_departs_from_analytic: " + sil_why)
        else:
            s = img["silhouette"]
            c = img["silhouette_control"]
            floor_px = SIL_OVER_CONTROL * c["rms_px"]
            sil_ok = bool(s["rms_mm"] >= SIL_RMS_MM and s["rms_px"] >= floor_px)
            sil_why = (f"typical outline wander {s['rms_px']:.2f} px = "
                       f"{s['rms_mm']:.1f} mm (median over {s['windows']} "
                       f"100-row windows, quadratic refitted in each, "
                       f"{s['rows']}-row band); needs >= {SIL_RMS_MM:.1f} mm "
                       f"(physical: real cloth at LAMBDA_HANG 112 mm should "
                       f"perturb it 5-10 mm) AND >= {floor_px:.2f} px = "
                       f"{SIL_OVER_CONTROL:.0f}x the control sphere's own "
                       f"{c['rms_px']:.2f} px floor measured the same way. "
                       f"Whole-outline fit for reference: "
                       f"{s['global_rms_mm']:.1f} mm.")

    checks = dict(pre)
    checks["witness_frame_valid"] = frame_ok
    checks["surface_microstructure"] = micro_ok
    checks["relief_reads_as_lip_and_shade"] = relief_ok
    checks["silhouette_departs_from_analytic"] = sil_ok

    # A pass requires every gated check to be exactly True. `not_applicable` is
    # neither a pass nor a failure and is excluded from the vote; `None` means
    # NOT MEASURED and is a failure, which is the whole of R2-018/R2-019.
    gated = [v for k, v in checks.items() if v != "not_applicable"]
    passed = all(v is True for v in gated)

    # R2-637. A TRANSPORT FAILURE IS NOT A VERDICT ABOUT A MODULE.
    #
    # `witness_frame_valid` is the ONE check in this file that is not about the
    # item at all -- it is the gate checking its own instrument (subject and
    # control populations, clipping, whether the control sphere's highlights are
    # warm). When it is False the gate has no picture, so `surface_microstructure`,
    # `relief_reads_as_lip_and_shade` and `silhouette_departs_from_analytic` are
    # all None and the item has been told nothing about itself.
    #
    # It nonetheless produced ITEM_REJECTED, because the ITEM_UNMEASURABLE branch
    # at the bottom of `main` requires `not any(v is False ...)` and
    # `witness_frame_valid: False` is itself a False. The one condition that
    # should have forced "I could not look" was the one blocking it.
    #
    # MEASURED, and this is how it was found rather than reasoned: job
    # 707c2a92ba76 QUEUED FINE at depth 15 and the client's poll died on
    # `http.client.RemoteDisconnected` -- which is what a broker closing a
    # keep-alive looks like and what a broker restart produces by construction.
    # The gate reported `ITEM_REJECTED` on `driver_figure`. Nothing in the
    # printed verdict distinguished that from a real rejection; it took reading
    # `checks.witness_frame_valid` in the JSON to tell them apart.
    #
    # THIS GATE DECIDES WHETHER ~113 MODULES GET AUTHORED. A false rejection here
    # costs a rework round on an item that was fine, and teaches whoever does the
    # rework to build toward a defect that was never there.
    #
    # A REAL failure elsewhere still REJECTS. `no_external_assets` is true or
    # false about the blend whether or not a picture exists, so an item carrying
    # an image texture is rejected on that evidence and not excused by a dead
    # socket. Only the render-based checks are forfeited with the witness.
    WITNESS_CHECK = "witness_frame_valid"
    substantive_fail = sorted(k for k, v in checks.items()
                              if v is False and k != WITNESS_CHECK)
    witness_unusable = checks.get(WITNESS_CHECK) is False
    verdict_is_vacuous = bool(
        (witness_unusable or (unmeasurable and not substantive_fail))
        and not substantive_fail and not passed)

    report = {
        "item": a.item, "hero": hero,
        "filmed_at_m": dist, "lens_mm": lens, "onscreen_px_4k": px,
        "flexible": flexible, "flexible_because": flex_why,
        "subject_selection": sel_why,
        "prefix_integrity": prefix_note,
        "witness_subject": subject_name,
        "witness_subject_because": subject_why,
        "checks": checks,
        "check_notes": {
            "surface_microstructure": micro_why,
            "relief_reads_as_lip_and_shade": relief_why,
            "silhouette_departs_from_analytic": sil_why,
        },
        "unmeasurable": unmeasurable,
        "framing_source": framing_src,
        "thresholds": {
            "procedural_texture_nodes_required": need_tex,
            "detail_limit_px": detail_limit_px,
            "fine_over_control_required": FINE_OVER_CONTROL,
            "fine_over_coarse_at_least_control": True,
            "relief_margin_over_control": RELIEF_MARGIN,
            "relief_dip_absolute_floor": RELIEF_DIP_FLOOR,
            "relief_control_sane_band": RELIEF_CONTROL_SANE,
            "relief_light_over_control_required": LIGHT_OVER_CONTROL,
            "relief_two_light_rho": "REPORTED, NOT GATED -- see LIGHT_OVER_CONTROL",
            "silhouette_rms_mm_required": SIL_RMS_MM,
            "silhouette_rms_over_control_required": SIL_OVER_CONTROL,
            "silhouette_min_px_for_5mm": SIL_MIN_PX_FOR_5MM,
            # R2-1381. A PASS AWARDED BY A WEAKER INSTRUMENT MUST BE
            # IDENTIFIABLE AS ONE. `mark_gate_version_stale.py` finds stale
            # reports by COUNTING checks, which cannot see a check that was
            # strengthened rather than added -- the 33 reports on disk all say
            # "8 checks" and 19 of them hold a `per_instance_variation` decided
            # on two triangle counts. A report WITHOUT this key was written by
            # the pre-R2-1381 gate, whatever its check count says.
            "variation_shape_law":
                "R2-1381: distinct SHAPES via _shape_signature on BOTH the "
                "realized-instance and the plain-object path; "
                "min(n, max(8, min(40, sqrt(n)))) required, "
                "commonest <= max(0.25, 1/n)",
            "variation_cv_size_floor": CV_SIZE_FLOOR,
        },
        "threshold_kinds": {
            "fine_over_control_required": "SCALE-INVARIANT (ratio to in-frame control)",
            "fine_over_coarse_at_least_control": "SCALE-INVARIANT (spectral shape vs in-frame control)",
            "relief_margin_over_control": "SCALE-INVARIANT (margin over in-frame control)",
            "relief_dip_absolute_floor": "SCALE-INVARIANT (calibrated from control spread)",
            "silhouette_rms_mm_required": "PHYSICAL (millimetres of cloth)",
            "silhouette_rms_over_control_required": "SCALE-INVARIANT (ratio to in-frame control)",
            "silhouette_min_px_for_5mm": "SIZE-DEPENDENT SCOPING TEST, not a bar",
            "detail_limit_px": "SIZE-DEPENDENT (screen px at the filmed distance)",
            "procedural_texture_nodes_required": "size-independent node floor",
            "variation_shape_law":
                "POPULATION-SCALED (sqrt of the instance count, floor 8, "
                "ceiling 40, each capped at the population itself)",
        },
        "measured": {
            "external_image_files": ext_imgs,
            "image_texture_nodes": mat["image_texture_nodes"],
            "materials": mat["materials"],
            "procedural_texture_nodes": mat["procedural_texture_nodes"],
            "relief_wiring": wiring,
            "objects": len(objs),
            "triangles": tris,
            # Reported, deliberately NOT gated. A trash can and a human need
            # wildly different budgets and I will not invent one threshold for
            # 435 item classes. But 390 triangles for a person is a mannequin in
            # any reading, so the number belongs in front of whoever reads this.
            "triangles_per_declared_instance": round(tris / max(declared, 1), 1),
            "triangles_per_found_object": round(tris / max(len(objs), 1), 1),
            "triangles_per_onscreen_px": (round(tris / px, 2) if px else None),
            "edges": es["n_edges"] if es else 0,
            "p10_edge_m": round(es["p10"], 6) if es else None,
            "median_edge_m": round(es["median"], 6) if es else None,
            "p90_edge_m": round(es["p90"], 6) if es else None,
            "p10_edge_px_at_filmed_distance": round(p10_px, 2) if p10_px else None,
            "median_edge_px_at_filmed_distance": round(med_px, 2) if med_px else None,
            "px_per_m_at_filmed_distance": round(px_per_m, 1),
            "mm_per_px_at_filmed_distance": round(1000.0 / px_per_m, 4),
            # Closes the resolution alibi in the report itself: these are the
            # world sizes of the bands the gate measures. "Too small to resolve"
            # is checkable against this line, not assertable over it.
            "band_radii_mm_at_filmed_distance": {
                str(r): round(1000.0 * r / px_per_m, 3) for r in BANDS},
            "instances_declared": declared,
            "instances_found": var["n"],
            "cv_size": var["cv_size"],
            "cv_volume": var["cv_volume"],
            "distinct_topologies": var["distinct_topologies"],
            # R2-1381. `distinct_topologies` is a triangle-count proxy and is
            # kept for continuity with the 32 wave-1 reports; the SHAPES below
            # are what the plain-object path is now gated on.
            "distinct_shapes": var.get("distinct_shapes"),
            "top_shape_share": var.get("top_shape_share"),
            "distinct_shapes_required": var.get("distinct_shapes_required"),
            "top_shape_share_limit": var.get("top_shape_share_limit"),
            "distinct_source_meshes": var.get("distinct_source_meshes"),
            "distinct_shapes_scale_invariant":
                var.get("distinct_shapes_scale_invariant"),
            "variation_measured_over": (
                "REALIZED geometry-nodes instances via depsgraph.object_instances"
                if real else
                ("geometry-nodes CHUNKS and the realized instances could NOT be "
                 "walked -- per_instance_variation is UNPROVEN and therefore FAILS"
                 if gn_instanced else "individual objects")),
            "realized_instances": real,
        },
        "witness": {
            "blend": wblend if not a.from_png else None,
            "png": wpng,
            "spec": wspec_path,
            "render": render_info,
            "render_error": render_err,
            "image": img,
        },
        # THE REPORT SAYS WHAT THE RUN SAYS. R2-637 and R2-116/R2-117 together:
        # the exit path below used to convert a rejection into ITEM_UNMEASURABLE
        # while the JSON on disk still read ITEM_REJECTED, which is precisely the
        # "the verdict on disk is not the verdict of the run" defect this project
        # has already been bitten by once. One string, computed once, used twice.
        "result": ("ITEM_ACCEPTED" if passed else
                   "ITEM_UNMEASURABLE" if verdict_is_vacuous else
                   "ITEM_REJECTED"),
        "verdict_is_vacuous_because": (
            None if not verdict_is_vacuous else
            ("the witness frame is unusable, so every render-based check was "
             "forfeited and nothing was measured about this module -- a "
             "transport or staging failure is the ABSENCE of a verdict, not a "
             "verdict. See witness.render_error."
             if witness_unusable else
             "no check FAILED, but %d could not be measured at all"
             % len(unmeasurable))),
    }

    # ---------------- WHAT THIS REPORT MEASURED -------------------------
    # A verdict that cannot name the blend it read is a verdict nobody can
    # check. On 2026-08-02 fourteen rebuilt gate reports sat in a work
    # directory while `render/items/<item>/gate.json` still served 29-30 July
    # files; `crew_fireproof_overall` read ITEM_ACCEPTED canonically and was in
    # fact ITEM_REJECTED, and there was no way to tell from the file itself.
    # `describes` carries the witness artefacts so a fresh verdict shipped
    # beside a stale picture is caught too -- that is the trap that follows
    # fixing the first one. See tools/provenance.py.
    report[_prov.STAMP_KEY] = _prov.stamp(
        tool_file=__file__,
        tool_version="item_gate RIG_VERSION %d, %d checks"
                     % (RIG_VERSION, len(report.get("checks") or {})),
        inputs=[("blend", bpy.data.filepath or None),
                ("manifest", a.manifest),
                ("from_png", a.from_png)],
        describes=[("witness_blend", wblend if not a.from_png else None),
                   ("witness_png", wpng),
                   ("witness_spec", wspec_path)],
    )

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=1)

    # ---------------- console -------------------------------------------
    print(f">> item {a.item}  hero={hero}  filmed at {dist} m on a {lens:.0f} mm lens")
    print(f">> subject set: {sel_why}")
    print(f">> {len(objs)} objects, {tris} triangles, {mat['materials']} materials")
    if es:
        print(f">> edges  p10 {es['p10']*1000:7.2f} mm = {p10_px:8.2f} px   "
              f"(limit {detail_limit_px} px -- this is the check)")
        print(f">>        med {es['median']*1000:7.2f} mm = {med_px:8.2f} px   (advisory)")
    print(f">> procedural texture nodes {mat['procedural_texture_nodes']} "
          f"(need {need_tex}) -- a node floor, NOT an appearance measurement")
    print(f">> relief wiring: {wiring['trees_scanned']} node tree(s) read from "
          f"the BLEND, {len(wiring['failing'])} miswired "
          f"({wiring['failing_on_item_materials']} on this item's own "
          f"materials, {wiring['failing_elsewhere_in_blend']} elsewhere in the "
          f"blend), {len(wiring['computation_notes'])} relief output(s) feeding "
          f"a computation (the edge-wear idiom -- noted, not failed)")
    for r in wiring["failing"]:
        print(f">>   MISWIRED [{r['scope']}] {r['kind']} {r['owner']!r} "
              f"{r['node']}: {r['detail']}")
        if r["shell_carries_transmission_or_subsurface"]:
            print(">>     ** this material CARRIES TRANSMISSION OR SUBSURFACE: "
                  "a stray relief link here is not merely flat, it switches "
                  "the shell interpretation per pixel.")
    print(f">> {px_per_m:.0f} px/m at the filmed distance = "
          f"{1000.0/px_per_m:.3f} mm per pixel. Band radii in world units: "
          + ", ".join(f"r{r}={1000.0*r/px_per_m:.1f}mm" for r in BANDS))
    if declared > 1:
        print(f">> instances {var['n']} found vs {declared} declared, "
              f"size CV {var['cv_size']}, {var['distinct_topologies']} distinct topologies")
        if not real and not gn_instanced:
            print(f">> PLAIN OBJECTS: {var['distinct_shapes']} distinct SHAPES "
                  f"over {var['n']} objects "
                  f"(need {var['distinct_shapes_required']}), commonest shape "
                  f"{(var['top_shape_share'] or 0)*100:.1f} % "
                  f"(limit {(var['top_shape_share_limit'] or 0)*100:.1f} %); "
                  f"{var['distinct_source_meshes']} source mesh datablocks")
            if (var["distinct_shapes_scale_invariant"] is not None
                    and var["distinct_shapes"]
                    and var["distinct_shapes_scale_invariant"]
                    < var["distinct_shapes"] / 2):
                print(">>   ** RECORDED, NOT FAILED: those shapes collapse to "
                      f"{var['distinct_shapes_scale_invariant']} once uniform "
                      "scale is divided out -- much of this population may be "
                      "one body at many sizes with the scale baked into the "
                      "vertices.")
        if real:
            print(f">> REALIZED instances: {real['realized']} from "
                  f"{real['distinct_sources']} distinct source meshes and "
                  f"{real['distinct_shapes']} distinct SHAPES "
                  f"(need {real['distinct_sources_required']} of each); "
                  f"commonest source {real['top_source_share']*100:.1f} %, "
                  f"commonest shape {real['top_shape_share']*100:.1f} % "
                  f"(limit {real['top_shape_share_limit']*100:.1f} %)")
            if real["distinct_shapes"] < real["distinct_sources"] / 2:
                print(">>   ** the source meshes are largely COPIES of each other: "
                      f"{real['distinct_sources']} datablocks carrying only "
                      f"{real['distinct_shapes']} shapes.")
        elif gn_instanced:
            print(f">> UNPROVEN: {declared} instances declared, {var['n']} objects "
                  "visible, and walking depsgraph.object_instances found none. "
                  "Per-instance variation was NOT measured, so it does not pass.")
        print(f">> triangles: {tris} total, {tris/max(declared,1):.0f}/declared "
              f"instance, {tris/max(len(objs),1):.0f}/object")
    if render_info:
        print(f">> witness frame: subject '{subject_name}' -- {subject_why}")
        print(f">>   {render_info}")
    if img and img.get("frame"):
        f = img["frame"]
        print(f">>   subject {f['subject_px']} px, sphere {f['sphere_px']} px, "
              f"plane {f['plane_px']} px; sphere highlight R-B "
              f"{f.get('sphere_highlight_R_minus_B')}")
    if img and img.get("frame", {}).get("subject_px_lit"):
        f = img["frame"]
        print(f">>   measured on the lit {f['subject_px_lit']} px of the subject "
              f"(mean {f.get('subject_mean_measured')}); brightness window "
              f"{img.get('luminance_window')}")
    if img and img.get("colour", {}).get("single_hue_fraction_r010") is not None:
        c = img["colour"]
        print(f">>   COLOUR (reported, not gated): "
              f"{c['single_hue_fraction_r010']*100:.1f} % of the lit surface sits "
              f"within 0.010 of its own median chromaticity "
              f"{c['median_chromaticity']}; chroma sd "
              f"({c['chroma_sd_u']}, {c['chroma_sd_v']}), p95 radius "
              f"{c['chroma_p95_radius']}. Near 100 % means ONE COLOUR.")
    if img and img.get("bands_subject"):
        b = img["bands_subject"]
        print(">>   band-pass % of mean [SUBJECT] " +
              "  ".join(f"r{r} {b[str(r)]}" for r in BANDS
                        if b.get(str(r)) is not None))
        for name, rec in (img.get("controls") or {}).items():
            if rec.get("bands"):
                bb = rec["bands"]
                print(f">>   band-pass % of mean [{name:16s}] mean "
                      f"{rec['mean_linear']}  " +
                      "  ".join(f"r{r} {bb[str(r)]}" for r in BANDS
                                if bb.get(str(r)) is not None) +
                      f"   relief {rec.get('relief')}")
            else:
                print(f">>   control [{name:16s}] mean {rec['mean_linear']} "
                      f"NOT USED: {rec.get('skipped')}")
    for k, v in checks.items():
        tag = {True: "PASS", False: "FAIL", None: "NOT MEASURED",
               "not_applicable": "n/a "}.get(v, str(v))
        print(f"     {tag:12s}  {k}")
    for k, v in report["check_notes"].items():
        if v:
            print(f"       - {k}: {v}")
    for u in unmeasurable:
        print(f"     !! {u}")

    # THE VERDICT AND THE EXIT STATUS COME FROM THE SAME STRING.
    #
    # This printed `STAGE RESULT: ITEM_REJECTED` and exited 0. `sweep2.sh`
    # already logs `rc=$?` beside the verdict line, so for 28 items it recorded
    # rc=0 next to REJECTED and nobody could have branched on it. Now:
    #   ITEM_ACCEPTED    -> 0
    #   ITEM_REJECTED    -> 1
    #   ITEM_UNMEASURABLE-> 3  (checks that could not be run at all)
    #
    # A gate whose checks did not RUN is not a rejection either: it is a
    # refusal, and callers deciding whether to rebuild an item need to tell
    # "your item is wrong" from "I could not look at your item".
    # ONE STRING, DECIDED WHERE THE REPORT WAS BUILT. This used to re-derive the
    # vacuity test here, which is how the JSON and the exit status came to
    # disagree -- see `verdict_is_vacuous` and the note on "result".
    if report["result"] == "ITEM_UNMEASURABLE":
        print(">> REFUSING TO REPORT A VERDICT: %s"
              % report.get("verdict_is_vacuous_because"))
    return gate_exit.verdict(report["result"])


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="item_gate")
