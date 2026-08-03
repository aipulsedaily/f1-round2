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

THE SEVEN CHECKS
----------------
  1. no_external_assets              binary, unchanged
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
  6. relief_reads_as_lip_and_shade   RENDER. Under a 12.5 deg raking sun a
                                     raised feature makes a bright sunward lip
                                     AND a dark lee shadow -- a dipole along the
                                     light. A printed one makes a single-value
                                     mark. Measured as the depth of the
                                     along-light anticorrelation MINUS the
                                     across-light one, so a merely directional
                                     surface cannot fake it.
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
    p.add_argument("--item", required=True)
    p.add_argument("--out", required=True)
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
    """
    dims, vols, tris = [], [], []
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
        oe.to_mesh_clear()
    if len(dims) < 2:
        return {"n": len(dims), "cv_size": None, "cv_volume": None,
                "distinct_topologies": len(set(tris))}, boxes

    def cv(xs):
        mu = statistics.mean(xs)
        return (statistics.pstdev(xs) / mu) if mu > 1e-9 else 0.0

    return {"n": len(dims), "cv_size": round(cv(dims), 5),
            "cv_volume": round(cv(vols), 5),
            "distinct_topologies": len(set(tris))}, boxes


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


def relief_anisotropy(L, mask, sun_rc, r=2):
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
    """
    m = _erode(mask, int(math.ceil(3 * r)))
    if int(m.sum()) < MIN_BAND_PX:
        return None, {"reason": "too few pixels after erosion"}
    B = _dog(L, r)
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


def analyse(png, spec):
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
    lit_all = sub_m & unclipped
    if lit_all.any():
        sm = _blur(L, 8.0)
        cut = float(np.quantile(sm[lit_all], 0.60))
        sub_ok = lit_all & (sm >= cut)
        if int(sub_ok.sum()) < MIN_BAND_PX * 3:
            sub_ok = lit_all                    # too small to subdivide
            cut = None
    else:
        sub_ok = lit_all
        cut = None
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

def main():
    a = parse_args()
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

    if declared <= 1:
        var_ok = True
    elif real:
        # `distinct_sources` catches "one tree spammed 100 times".
        # `distinct_shapes` catches its sequel: 420 datablocks holding 6 poses,
        # which is what the rebuilt spectator crowd actually is.
        need_sources = max(8, min(40, int(math.sqrt(real["realized"]))))
        var_ok = (real["distinct_sources"] >= need_sources
                  and real["distinct_shapes"] >= need_sources
                  and real["top_source_share"] <= 0.25
                  and real["top_shape_share"] <= 0.25)
        real["distinct_sources_required"] = need_sources
        real["distinct_shapes_required"] = need_sources
        real["top_source_share_limit"] = 0.25
    elif gn_instanced:
        # UNPROVEN IS NOT A PASS (R2-019). No fallthrough to chunk statistics.
        var_ok = False
    else:
        var_ok = (var["cv_size"] is not None and var["cv_size"] >= 0.03
                  and var["distinct_topologies"] >= 2)

    pre = {"no_external_assets": ext_ok, "material_depth": mat_ok,
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
                render_info = render_witness(wblend, wpng, a.samples, a)
            img, notes = analyse(wpng, wspec)
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
            ok_bal = (foc is None or focc is None or foc >= focc)
            micro_ok = bool(ok_amp and ok_bal)
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
                         + ("" if ok_bal else
                            " -- MORE COARSE-WEIGHTED THAN A FEATURELESS SMOOTH "
                            "SURFACE: there is a mechanism at centimetre scale "
                            "and nothing at millimetre scale, which is a "
                            "3-5x amplitude shortfall, not an absence"))

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
            "silhouette_rms_mm_required": SIL_RMS_MM,
            "silhouette_rms_over_control_required": SIL_OVER_CONTROL,
            "silhouette_min_px_for_5mm": SIL_MIN_PX_FOR_5MM,
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
        },
        "measured": {
            "external_image_files": ext_imgs,
            "image_texture_nodes": mat["image_texture_nodes"],
            "materials": mat["materials"],
            "procedural_texture_nodes": mat["procedural_texture_nodes"],
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
        "result": "ITEM_ACCEPTED" if passed else "ITEM_REJECTED",
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
    print(f">> {px_per_m:.0f} px/m at the filmed distance = "
          f"{1000.0/px_per_m:.3f} mm per pixel. Band radii in world units: "
          + ", ".join(f"r{r}={1000.0*r/px_per_m:.1f}mm" for r in BANDS))
    if declared > 1:
        print(f">> instances {var['n']} found vs {declared} declared, "
              f"size CV {var['cv_size']}, {var['distinct_topologies']} distinct topologies")
        if real:
            print(f">> REALIZED instances: {real['realized']} from "
                  f"{real['distinct_sources']} distinct source meshes and "
                  f"{real['distinct_shapes']} distinct SHAPES "
                  f"(need {real['distinct_sources_required']} of each); "
                  f"commonest source {real['top_source_share']*100:.1f} %, "
                  f"commonest shape {real['top_shape_share']*100:.1f} % (limit 25 %)")
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
    if report["result"] == "ITEM_REJECTED" and unmeasurable and \
            not any(v is False for v in checks.values()):
        print(">> REFUSING TO REPORT A VERDICT: nothing FAILED, but %d check(s) "
              "could not be measured at all. That is not a rejection, it is a "
              "gate that could not look." % len(unmeasurable))
        return gate_exit.verdict("ITEM_UNMEASURABLE")
    return gate_exit.verdict(report["result"])


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="item_gate")
