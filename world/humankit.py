"""humankit -- the shared procedural human foundation.

Everything about people in this film is built on this file: a 7,800-seat seated
crowd, 3,500 standing on the GA banking, 260 paddock personnel, 160 marshals,
120 crew, one driver. It is built ONCE and imported, exactly as `itemkit` is,
and it imports `itemkit` rather than re-typing any of it.

WHY IT EXISTS -- the measured defect list it replaces
-----------------------------------------------------
From pixel-peeping the current 4K grandstand render (docs/HUMAN-FIGURE-BRIEF.md):
heads are featureless ovoids; ~6 poses across ~600 figures; zero props; clothing
is flat colour fill; one body type; hands are stumps; nobody standing; occupancy
random-uniform; no shared attention; contact with the seat unsolved. Measured:
**390 triangles per person**. The rebuilt attempt reached 1,196 tris across 420
source meshes -- but `cv_scale` was 0.0 and yaw varied 3.99 deg, i.e. every
figure identically scaled and nearly identically oriented.

WHAT SCREEN PRESENCE ACTUALLY DEMANDS -- docs/screen_presence.json, all 2,978 frames
-----------------------------------------------------------------------------------
    marshal / crew / paddock       551.8 sharp px   106 frames >= 300 px   min depth 7.602 m
    spectator_standing_ga  x3500   278.7 sharp px     0 frames >= 300 px   min depth 10.756 m
    spectator_seated       x7800   199.1 sharp px     0 frames >= 300 px   min depth 10.756 m

**THE NUMBERS ABOVE WERE 767.2 / 363.4 / 259.6 UNTIL 2026-08-03 AND ALL THREE
WERE WRONG.** They were carried in from a pre-shutter-fix run of
`tools/screen_presence.py` -- a RAMPED shutter, before R2-037 -- and survived
into this docstring, into sec 12c below, into `crew_figure.PEEP_PX`,
`paddock_personnel_figure.PEEP_PX` and `human_bench --px`'s default, and into
the LOD reasoning in every one of them. **767.2 overstates the covered tier's
real macro resolve by 39.0 %** (767.2 / 551.8), and it is the number the
`CAM_SPECSEAT_MACRO` render was framed at. There is no `peak_sharp_px` field in
`screen_presence.json` at all -- only **`peak_sharp_px_4k`** -- so any figure
quoted as "peak SHARP px" without the `_4k` suffix was read off something else.
Re-read the file before quoting it; it is regenerated whenever the camera path
or the world assembly moves, and it moved again on 2026-08-03 03:58.

552 px is a figure filling a quarter of the frame height, held for 106 frames.
That number is still an UPPER BOUND: `marshal_figure_standing`, `crew_figure`,
`paddock_personnel_figure` and `marshal_overall` all report the identical
785.7 / 551.8 / 106 / 148 / 7.602 tuple because they share one 28-host set and
inherit its best moment. `LOD.for_px()` is therefore driven by the figure's OWN
projected height, and the tiers are stated in px, not in metres.

THE HASH TRAP -- read before writing any variation code
-------------------------------------------------------
`hash01` appears in 15 of 28 wave-1 modules in at least 10 implementations. One
did not avalanche and collapsed 7 independent properties onto 1 -- measured
bit-flip rate 0.2458 against a correct 0.5032. A crowd whose height, build,
garment and pose all derive from a collapsed hash is ranks of clones however
many source meshes it emits. **This file has no `hash01` of its own.** It calls
`itemkit.hash01`, and `measure_variation()` below then measures the realised
parameter matrix -- correlation, PCA participation ratio, nearest-neighbour
distance -- because an avalanching hash is necessary and not sufficient: seven
independent draws can still be fed through one archetype table and come out
rank-1.

WHERE THE NUMBERS COME FROM, STATED PLAINLY
-------------------------------------------
The anthropometry below is standard published material recalled from memory, not
looked up from a source document in this session, and it is written here so it
can be checked rather than trusted:

  * SEGMENT RATIOS are the Drillis & Contini fractions of stature (acromion
    0.818 H, trochanter 0.530 H, knee 0.285 H, upper arm 0.186 H, forearm
    0.146 H, hand 0.108 H, foot 0.152 H, head height 0.130 H, biacromial
    0.259 H, bi-iliac 0.191 H). These are textbook figures and I am confident in
    them to ~1 % of stature.
  * STATURE MOMENTS (adult male 1.756 +/- 0.072 m, adult female 1.618 +/-
    0.066 m) are NHANES-era Western adult figures. Confident to ~10 mm in the
    mean and ~5 mm in the sd.
  * BMI MOMENTS (male 25.4 +/- 4.3, female 25.8 +/- 5.5, lognormal-skewed) are
    the shakiest numbers here -- population BMI has moved and depends entirely
    on which population. They are used only to drive girth, and the girth model
    itself (girth ~ sqrt(mass / stature)) is a modelling choice, not a citation.
  * CHILD STATURE follows a linear growth segment I fitted by eye to the usual
    50th-centile curve, not a published table.

None of this is load-bearing on a citation. What it is load-bearing on is that
the RATIOS VARY INDEPENDENTLY PER PERSON, which is what makes 600 figures 600
bodies, and that is measured in `measure_variation()`.

USE
---
    import sys, os
    sys.path.insert(0, "/home/zany/f1-round2/world")
    import itemkit as K
    import humankit as HK

    b = HK.sample_body(HK.rng_for(seed, 0))         # anthropometry
    p = HK.sample_pose(HK.rng_for(seed, 1), b, "stand_watch")
    fig = HK.build_figure(b, p, HK.LOD.for_px(653), seed=seed)
    ob  = HK.emit_figure(fig, "PPF_F000", coll, mats)

SELF-TEST
---------
    python3 world/humankit.py --selftest        # geometry + variation, no bpy
    blender -b --factory-startup -P world/humankit.py -- --selftest
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
except ImportError:
    bpy = None
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import itemkit as K                                          # noqa: E402

hash01 = K.hash01           # ONE implementation, and it avalanches. Never redefine.
Rng = K.Rng

TAU = 2.0 * math.pi
_T0 = time.time()


def log(msg):
    sys.stdout.write("[%7.1fs] humankit: %s\n" % (time.time() - _T0, msg))
    sys.stdout.flush()


def film_exposure(scene):
    """Move a scene off `itemkit.contract_sun`'s exposure and onto the film's.

    EVERY ITEM FRAME EVER JUDGED ON THIS PROJECT IS 0.580 STOPS OVER.
    `itemkit.contract_sun` sets `scene.view_settings.exposure =
    world_contract.REFERENCE_EXPOSURE_EXTERIOR = -3.048`. The film renders at
    `film_exposure.FILM_EXPOSURE = -3.628`, which is a MEASUREMENT -- an 18 %
    lambertian card rendered under the contract sun and read back, good to
    0.006 stops -- and `tools/build_verify_scene.py` calls -3.048 *"the refuted
    contract value"* in terms. 0.58 stops is not a rounding error on a face: it
    is most of the shading range a brow ridge has to work in, and defect 1 is
    "the face is a featureless oval".

    `contract_sun` belongs to `itemkit` and another agent owns it, so this is
    the correction applied loudly at every figure item's own scene setup rather
    than quietly at the source. Call it AFTER `contract_sun`.

    It RAISES rather than falling back. A figure item that cannot read the
    film's exposure must not render: shipping a frame at an exposure nobody has
    checked is R2-020 with a different constant, and this project has now spent
    five passes judging faces under a light the film does not use.
    """
    import film_exposure as FX                                # noqa: E402
    was = float(scene.view_settings.exposure)
    scene.view_settings.exposure = float(FX.FILM_EXPOSURE)
    log("EXPOSURE: %+.3f EV -> film_exposure.FILM_EXPOSURE %+.3f (a %.3f stop "
        "correction; frames judged before 2026-08-03 are that much over)"
        % (was, FX.FILM_EXPOSURE, was - FX.FILM_EXPOSURE))
    return float(FX.FILM_EXPOSURE)


def rng_for(*keys):
    """A stream keyed by (figure seed, channel). Channels must be DISTINCT ints.

    Every property draws from its own channel so that changing the wardrobe
    model does not change anybody's height -- and so that the parameter vector
    `measure_variation` inspects really is a set of independent draws rather
    than one draw reused, which is the collapsed-hash failure in a different
    costume.
    """
    return Rng(*[int(k) for k in keys])


def _hash01(*vals):
    """A deterministic float in [0, 1) from floats, drawing no randomness.

    For deriving a per-person property from numbers that person already has,
    where taking another draw off a live `Rng` would shift every subsequent
    draw and silently change the whole population. Uses the fractional part of a
    large irrational multiple, which decorrelates inputs that differ in the
    fourth decimal (two statures 1 mm apart give unrelated outputs).
    """
    a = 0.0
    for i, x in enumerate(vals):
        a += (float(x) + 1.0) * (12.9898 + 7.233 * i) * 1e4
    return float(math.sin(a) * 43758.5453 % 1.0)


# ===========================================================================
# 1.  LOD -- budgeted against the MEASURED screen presence, not against ambition
# ===========================================================================

class LOD(object):
    """Resolution tier. `for_px()` maps a figure's projected HEIGHT IN PIXELS on
    the 4K master to a tier, because that is the quantity the eye actually has.

    Do not build one 100 k-triangle human and instance it 7,800 times: that is
    780 M triangles for the seated crowd alone, against a whole world that
    currently traces 13.2 B. The tiers below, applied to the measured
    populations, come to ~112 M triangles for all 11,300 crowd figures -- 0.85 %
    of the world -- and are what makes the hero tier affordable.

        tier   px range      measured population it serves               tris
        L0     >= 300 px     marshal/crew/paddock 767 px, GA front 363   60-95 k
        L1     150-300 px    spectator_seated 260 px, GA mid             18-26 k
        L2      60-150 px    the bulk of both stands                      6-9 k
        L3     <  60 px      far stands, horizon crowd                    2-3 k
    """

    __slots__ = ("name", "px", "ring", "station", "head_u", "head_v", "ears",
                 "fingers", "nails", "hair_strands", "hair_cap_res",
                 "shoe_detail", "seams", "wrinkle_oct", "eyes", "props")

    def __init__(self, name, px, ring, station, head_u, head_v, ears, fingers,
                 nails, hair_strands, hair_cap_res, shoe_detail, seams,
                 wrinkle_oct, eyes, props):
        self.name = name
        self.px = px
        self.ring = ring                  # cross-section points on a limb
        self.station = station            # stations per limb segment
        self.head_u = head_u              # head azimuth divisions
        self.head_v = head_v              # head elevation divisions
        self.ears = ears
        self.fingers = fingers            # 5 = separate, 3 = grouped, 1 = mitten
        self.nails = nails
        self.hair_strands = hair_strands
        self.hair_cap_res = hair_cap_res
        self.shoe_detail = shoe_detail    # 2 laces+tread, 1 sole+tread, 0 sole
        self.seams = seams
        self.wrinkle_oct = wrinkle_oct
        self.eyes = eyes
        self.props = props

    def __repr__(self):
        return "<LOD %s ring=%d head=%dx%d fingers=%d hair=%d>" % (
            self.name, self.ring, self.head_u, self.head_v, self.fingers,
            self.hair_strands)

    def derive(self, name=None, **over):
        """A copy of this tier with named fields replaced.

        WHY THIS EXISTS -- defect 6, "the hands are mittens", measured in
        `render/items/spectator_crowd/crops/feet_c.png`. `LOD_L1.fingers = 3`
        means `_finger_groups` returns two FUSED PAIRS at 1.9x radius, which is
        a flat paddle with a thumb, and 85 % of a grandstand is built at L1
        because a 1.25 m seated figure projects 254 px.
        `for_px` is right about the FIGURE and wrong about the HAND: a raised
        hand in that same crop is 90-120 px across, which is four separate
        fingers' worth of pixels. A tier is a budget for a whole body and the
        body does not shrink uniformly -- a hand held above the head is nearer
        the camera and unoccluded, and it is the single most mannequin-making
        part of a person when it is wrong.
        The alternative was to build the entire seated library at L0, which is
        62 M library triangles against 34 M for one body part. Measured cost of
        doing it this way instead: see `spectator_crowd`'s HANDS_L0 note.
        """
        vals = {k: getattr(self, k) for k in LOD.__slots__}
        bad = set(over) - set(LOD.__slots__)
        if bad:
            raise KeyError("LOD has no field(s) %s" % sorted(bad))
        vals.update(over)
        vals["name"] = name or (self.name + "+" + ",".join(
            "%s=%s" % (k, over[k]) for k in sorted(over) if k != "name"))
        return LOD(**vals)

    @staticmethod
    def for_px(px_height):
        """Tier from the figure's projected height in pixels on the 4K master."""
        p = float(px_height)
        if p >= 300.0:
            return LOD_L0
        if p >= 150.0:
            return LOD_L1
        if p >= 60.0:
            return LOD_L2
        return LOD_L3

    @staticmethod
    def for_distance(dist_m, lens_mm=35.0, height_m=1.75):
        """Tier from a filmed distance. Uses itemkit's own px_per_m."""
        return LOD.for_px(K.px_per_m(dist_m, lens_mm) * height_m)


# `hair_strands` WAS 620/190/48 AND THE HAIR WAS MORE THAN HALF THE FIGURE.
# Measured on this file's own builder before the strand rewrite: 12,324 hair
# triangles on a 24,287-triangle L1 person -- **51 %** -- and 11,400 of those
# 12,324 were strand tubes. What the frames show for that spend is a regular
# lattice of dark commas (see `_hair_strands`). The outline break is now the
# MESH's lock ridges, which cost a tenth as much and also move the silhouette,
# and the strands are back to being what their own docstring always said they
# were: a fringe on the edge, not a coat over the whole dome. L2 keeps a token
# 28 because a 60-150 px head still has an edge; L3 has none and never did.
#                name  px   ring stn  hu  hv  ear fing nail hair cap shoe seam oct eye prop
LOD_L0 = LOD("L0", 300, 26, 7, 72, 52, 2, 5, 1, 260, 5, 2, 1, 5, 1, 1)
LOD_L1 = LOD("L1", 150, 18, 5, 44, 32, 1, 3, 0, 96, 4, 1, 1, 4, 1, 1)
LOD_L2 = LOD("L2", 60, 12, 4, 26, 20, 0, 2, 0, 28, 3, 1, 0, 3, 0, 1)
LOD_L3 = LOD("L3", 0, 8, 3, 16, 12, 0, 1, 0, 0, 2, 0, 0, 2, 0, 0)
LOD_TIERS = (LOD_L0, LOD_L1, LOD_L2, LOD_L3)


# ===========================================================================
# 2.  ANTHROPOMETRY -- genuinely different BODIES, not one mesh scaled
# ===========================================================================
#
# `cv_scale = 0.0` is the failure this section exists to make impossible. A
# figure is not a stature multiplied through a template: every segment carries
# its OWN residual, so two people of identical height have different leg-to-
# torso ratios, different shoulder-to-hip ratios and different girths.
#
# The residual sd of 0.030 on each ratio is a modelling choice. Real segment
# ratios have residual CVs in the 2-4 % band once stature is regressed out, so
# 3 % is inside the plausible range; it is stated as a choice rather than
# presented as a citation.

SEG_RATIO = {                       # fraction of stature H, Drillis & Contini
    "acromion_h":   0.8180,         # shoulder joint height
    "trochanter_h": 0.5300,         # hip joint height
    "knee_h":       0.2850,
    "ankle_h":      0.0390,
    "upper_arm":    0.1860,
    "forearm":      0.1460,
    "hand_len":     0.1080,
    "foot_len":     0.1520,
    "head_h":       0.1300,         # chin to vertex
    "biacromial":   0.2590,         # shoulder breadth
    "biiliac":      0.1910,         # hip breadth
    # Chest depth is the one ratio I could not recall with confidence. Drillis &
    # Contini's table is quoted with 0.174 H, which puts a 1.75 m male at a
    # 305 mm front-to-back chest -- too deep by eye against a ~230 mm reality.
    # 0.130 H = 228 mm is used instead and is a MODELLING CHOICE, flagged here
    # rather than presented as the citation.
    "chest_depth":  0.1300,
    # Acromion to the OCCIPITAL CONDYLE (the head's pivot), not to the chin.
    # Derived, not recalled: the vertical chain has to close on stature, and
    # 0.818 (acromion) + n + 0.66 x 0.130 (pivot to vertex) = 1.000 gives
    # n = 0.0962. The visible neck is shorter than this because the lower third
    # of the head mass hangs below the pivot.
    "neck_len":     0.0962,
}
# Which ratios get an independent per-person residual. Stature is drawn first;
# these then move relative to it, which is what makes limb PROPORTION vary.
SEG_JITTER = ("acromion_h", "trochanter_h", "knee_h", "upper_arm", "forearm",
              "hand_len", "foot_len", "head_h", "biacromial", "biiliac",
              "chest_depth", "neck_len")
SEG_JITTER_SD = 0.030

# Adult stature and BMI moments. See the docstring: recalled, not cited.
STATURE = {"M": (1.756, 0.072), "F": (1.618, 0.066)}
BMI = {"M": (25.4, 4.3), "F": (25.8, 5.5)}

# Age composition of a race-weekend crowd. A stand with no children and no
# elderly is one of the ten measured defects; 8 % children is the manifest's own
# figure for `spectator_seated`.
AGE_MIX = (("child", 0.055), ("teen", 0.055), ("adult", 0.740),
           ("elder", 0.150))

# Melanin index -> base skin colour. Two-parameter (melanin, haemoglobin) model
# evaluated at build time; these are the endpoints in LINEAR RGB, chosen so the
# ladder is monotonic in luminance and keeps a real red component at the dark
# end (a dark skin that goes neutral grey is the commonest procedural tell).
SKIN_LIGHT = (0.640, 0.446, 0.371)
SKIN_DARK = (0.078, 0.038, 0.026)
SKIN_MID = (0.330, 0.184, 0.124)

HAIR_COLOURS = (          # linear RGB, name, frequency weight
    ((0.0120, 0.0085, 0.0062), "black", 0.30),
    ((0.0290, 0.0175, 0.0098), "dark_brown", 0.26),
    ((0.0630, 0.0360, 0.0175), "brown", 0.17),
    ((0.1180, 0.0740, 0.0330), "light_brown", 0.09),
    ((0.2250, 0.1620, 0.0700), "blonde", 0.07),
    ((0.0900, 0.0300, 0.0130), "auburn", 0.035),
    ((0.3600, 0.3400, 0.3200), "grey", 0.045),
    ((0.6200, 0.6050, 0.5800), "white", 0.020),
)

HAIR_STYLES = (           # name, length_m, volume, part_frac, weight_M, weight_F
    ("crop", 0.020, 0.35, 0.00, 0.30, 0.030),
    ("short", 0.055, 0.55, 0.30, 0.34, 0.120),
    ("medium", 0.115, 0.80, 0.35, 0.14, 0.230),
    ("long", 0.290, 1.00, 0.40, 0.02, 0.300),
    ("ponytail", 0.230, 0.70, 0.30, 0.01, 0.160),
    ("bun", 0.075, 0.85, 0.25, 0.005, 0.100),
    ("bald", 0.000, 0.00, 0.00, 0.13, 0.005),
    ("curly", 0.090, 1.25, 0.10, 0.06, 0.055),
)


class Body(object):
    """One person's measurements. Every field is metres unless named otherwise.

    Constructed only by `sample_body`. Nothing downstream may invent a
    dimension: if a builder needs a number that is not here, it belongs here.
    """

    __slots__ = (
        "seed", "sex", "age_band", "age_years", "stature", "bmi", "mass",
        "ratio", "acromion_h", "trochanter_h", "knee_h", "ankle_h",
        "upper_arm", "forearm", "hand_len", "foot_len", "head_h", "neck_len",
        "shoulder_half", "hip_half", "chest_depth", "waist_half",
        "waist_depth", "chest_half", "neck_r", "head_w", "head_d",
        "girth", "arm_r", "thigh_r", "calf_r", "wrist_r", "ankle_r",
        "belly", "bust", "melanin", "haemo", "skin_rgb", "hair_rgb",
        "hair_name", "hair_style", "hair_len", "hair_vol", "hair_part",
        "hair_part_az", "beard",
        "params",
    )

    def __repr__(self):
        return ("<Body %s/%s %.3f m %.1f kg BMI %.1f>"
                % (self.sex, self.age_band, self.stature, self.mass, self.bmi))

    def as_vector(self):
        """The independent parameter vector, for `measure_variation`."""
        return self.params


def _pick_weighted(u, pairs):
    """pairs = ((value, weight), ...). `u` in [0,1)."""
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w / tot
        if u < acc:
            return v
    return pairs[-1][0]


def _child_stature(age, sex_f):
    """50th-centile stature, metres, for age 4..17. Fitted by eye, not cited."""
    a = float(np.clip(age, 4.0, 17.0))
    if a <= 12.0:
        h = 1.020 + 0.0620 * (a - 4.0)          # 1.02 m at 4 -> 1.52 m at 12
    else:
        h = 1.520 + 0.0430 * (a - 12.0)         # -> 1.735 m at 17
    if sex_f:
        h *= 0.988 if a < 11 else (0.960 if a < 14 else 0.930)
    return h


def sample_body(rng, sex=None, age_band=None, adult_only=False):
    """Draw one anthropometrically plausible body.

    Independent channels, deliberately: sex, age, stature residual, BMI
    residual, twelve segment residuals, skin, hair colour, hair style. Eighteen
    numbers with no shared source, which is what `measure_variation` then
    checks is still true after the archetype tables have had their say.
    """
    b = Body()
    b.seed = rng.seed
    b.sex = sex or ("F" if rng.u() < 0.42 else "M")
    if age_band is None:
        age_band = "adult" if adult_only else _pick_weighted(rng.u(), AGE_MIX)
    b.age_band = age_band
    sex_f = (b.sex == "F")

    if age_band == "child":
        b.age_years = rng.u(5.0, 12.99)
        h0 = _child_stature(b.age_years, sex_f)
        b.stature = h0 * (1.0 + rng.clipn(0.042, 0.12))
    elif age_band == "teen":
        b.age_years = rng.u(13.0, 17.99)
        h0 = _child_stature(b.age_years, sex_f)
        b.stature = h0 * (1.0 + rng.clipn(0.038, 0.11))
    else:
        mu, sd = STATURE[b.sex]
        if age_band == "elder":
            b.age_years = rng.u(65.0, 84.0)
            mu -= 0.030 + 0.0018 * (b.age_years - 65.0)   # vertebral shrinkage
        else:
            b.age_years = rng.u(18.0, 64.0)
        b.stature = float(np.clip(rng.n(mu, sd), mu - 3.2 * sd, mu + 3.4 * sd))

    # --- BMI, hence mass, hence girth ------------------------------------
    mu_b, sd_b = BMI[b.sex]
    if age_band == "child":
        mu_b, sd_b = 17.0 + 0.42 * (b.age_years - 5.0), 2.6
    elif age_band == "teen":
        mu_b, sd_b = 20.4 + 0.30 * (b.age_years - 13.0), 3.4
    elif age_band == "elder":
        mu_b, sd_b = mu_b + 0.9, sd_b * 0.92
    # Right-skewed: real BMI has a long upper tail and a hard lower wall.
    z = rng.n(0.0, 1.0)
    b.bmi = float(np.clip(mu_b + sd_b * (z + 0.28 * max(z, 0.0) ** 2), 14.0, 46.0))
    b.mass = b.bmi * b.stature ** 2

    # --- segment lengths, each with its OWN residual ----------------------
    H = b.stature
    b.ratio = {}
    for k, v in SEG_RATIO.items():
        j = (1.0 + rng.clipn(SEG_JITTER_SD, 2.6 * SEG_JITTER_SD)) \
            if k in SEG_JITTER else 1.0
        b.ratio[k] = v * j
    # Children are proportioned differently: a big head and short legs, and
    # nothing about a crowd reads as fake faster than a scaled-down adult.
    if age_band in ("child", "teen"):
        t = float(np.clip((b.age_years - 4.0) / 14.0, 0.0, 1.0))
        b.ratio["head_h"] *= 1.0 + 0.36 * (1.0 - t) ** 1.4
        b.ratio["trochanter_h"] *= 1.0 - 0.085 * (1.0 - t) ** 1.2
        b.ratio["knee_h"] *= 1.0 - 0.060 * (1.0 - t) ** 1.2
        b.ratio["biacromial"] *= 1.0 - 0.045 * (1.0 - t)
        b.ratio["upper_arm"] *= 1.0 - 0.035 * (1.0 - t)

    b.acromion_h = H * b.ratio["acromion_h"]
    b.trochanter_h = H * b.ratio["trochanter_h"]
    b.knee_h = H * b.ratio["knee_h"]
    b.ankle_h = H * b.ratio["ankle_h"]
    b.upper_arm = H * b.ratio["upper_arm"]
    b.forearm = H * b.ratio["forearm"]
    b.hand_len = H * b.ratio["hand_len"]
    b.foot_len = H * b.ratio["foot_len"]
    b.head_h = H * b.ratio["head_h"]
    b.neck_len = H * b.ratio["neck_len"]
    # STATURE IS THE MEASUREMENT, so the vertical chain must close on it. Twelve
    # independent ratio residuals do not sum to 1.0 by construction, and the
    # first version of this left every figure 20-50 mm short of its own declared
    # height -- which would have made `stature` a label rather than a dimension
    # and quietly broken every seat, doorway and eyeline that reads off it. The
    # three vertical segments above the hip are rescaled together, so their
    # residuals survive as PROPORTION while the total is exact.
    kv = H / max(b.acromion_h + b.neck_len + 0.66 * b.head_h, 1e-6)
    b.acromion_h *= kv
    b.neck_len *= kv
    b.head_h *= kv

    # --- breadths, with sex dimorphism ------------------------------------
    sh = H * b.ratio["biacromial"] * (0.930 if sex_f else 1.0)
    hp = H * b.ratio["biiliac"] * (1.055 if sex_f else 1.0)
    b.shoulder_half = 0.5 * sh
    b.hip_half = 0.5 * hp

    # Girth scales as sqrt(mass / stature): mass ~ H * girth^2 for a body of
    # roughly constant density and roughly self-similar section. A MODEL, not a
    # citation, and it is the only place BMI enters the geometry.
    g = math.sqrt(max(b.mass, 8.0) / max(H, 0.6)) / math.sqrt(70.0 / 1.75)
    b.girth = g
    b.chest_depth = H * b.ratio["chest_depth"] * (0.5 + 0.5 * g) \
        * (0.965 if sex_f else 1.0)
    b.chest_half = b.shoulder_half * (0.760 + 0.130 * (g - 1.0))
    # Waist: the single most BMI-sensitive dimension, and the one that carries
    # "larger build" to the silhouette. Sex changes the shape of the taper.
    wf = 0.780 if sex_f else 0.845
    b.waist_half = b.hip_half * wf * (0.72 + 0.36 * g ** 1.55)
    b.waist_depth = b.chest_depth * (0.80 + 0.40 * (g - 1.0)) * (0.92 if sex_f else 1.0)
    b.belly = float(np.clip((b.bmi - 22.0) / 16.0, -0.15, 1.25))
    b.bust = (0.55 + 0.55 * rng.u()) * (0.35 + 0.45 * g) if sex_f else 0.0
    if age_band == "child":
        b.bust = 0.0

    b.neck_r = 0.0345 * H * (0.86 if sex_f else 1.0) * (0.80 + 0.30 * g)
    b.head_w = b.head_h * 0.680 * (0.965 if sex_f else 1.0)
    b.head_d = b.head_h * 0.855

    b.arm_r = 0.0290 * H * (0.72 + 0.36 * g) * (0.93 if sex_f else 1.0)
    b.wrist_r = 0.0162 * H * (0.80 + 0.24 * g) * (0.90 if sex_f else 1.0)
    b.thigh_r = 0.0480 * H * (0.68 + 0.40 * g) * (1.055 if sex_f else 1.0)
    b.calf_r = 0.0338 * H * (0.72 + 0.34 * g) * (1.00 if sex_f else 1.0)
    b.ankle_r = 0.0195 * H * (0.82 + 0.22 * g)

    # --- surface appearance -----------------------------------------------
    b.melanin = float(np.clip(rng.u() ** 1.35, 0.0, 1.0))
    b.haemo = float(np.clip(rng.n(0.50, 0.17), 0.05, 0.95))
    b.skin_rgb = skin_colour(b.melanin, b.haemo)
    hc = _pick_weighted(rng.u(), [(c, w) for c, _, w in HAIR_COLOURS])
    b.hair_rgb = hc
    b.hair_name = next(n for c, n, _ in HAIR_COLOURS if c == hc)
    if age_band == "elder" and rng.u() < 0.78:
        grey = 0.35 + 0.60 * rng.u()
        tgt = (0.36, 0.345, 0.325)
        b.hair_rgb = tuple(hc[i] * (1 - grey) + tgt[i] * grey for i in range(3))
        b.hair_name = "greying_" + b.hair_name
    idx = 5 if sex_f else 4
    st = _pick_weighted(rng.u(), [(s, s[idx]) for s in HAIR_STYLES])
    b.hair_style, b.hair_len, b.hair_vol = st[0], st[1], st[2]
    # `part_frac` -- column 3 of HAIR_STYLES -- had been declared since the
    # table was written and READ NOWHERE. Eight styles that reach the mesh only
    # as a length and a volume are three styles, which is a quiet contributor to
    # "16 visible identical twins": two people with the same length and volume
    # were the same hair. It is now a real per-person parting.
    b.hair_part = float(st[3])
    # DELIBERATELY NOT A DRAW. Taking one more number off `rng` here shifts
    # every subsequent draw in `sample_body`, so every body in the library
    # changes and the hair A/B stops being an A/B -- two frames that differ in
    # the hair AND in who is standing there answer nothing. This is a hash of
    # numbers already drawn, so the stream is untouched and the old library
    # rebuilds identically.
    # +-0.12 turns = +-43 deg of azimuth off the centre line, which spans a
    # centre parting to a deep side parting and no further; a parting behind the
    # ear is not a parting.
    b.hair_part_az = float(_hash01(b.stature, b.age_years, b.melanin) - 0.5) * 0.24
    if age_band == "child" and b.hair_style == "bald":
        b.hair_style, b.hair_len, b.hair_vol = "short", 0.050, 0.55
        b.hair_part = 0.25
    b.beard = 0.0
    if not sex_f and age_band in ("adult", "elder"):
        b.beard = 0.0 if rng.u() < 0.62 else rng.u(0.25, 1.0)

    # --- the independent parameter vector, for measurement -----------------
    b.params = {
        "stature": b.stature, "bmi": b.bmi, "sex_f": 1.0 if sex_f else 0.0,
        "age_years": b.age_years, "melanin": b.melanin, "haemo": b.haemo,
        "hair_len": b.hair_len, "hair_vol": b.hair_vol,
        "hair_lum": 0.2126 * b.hair_rgb[0] + 0.7152 * b.hair_rgb[1]
                    + 0.0722 * b.hair_rgb[2],
        "beard": b.beard, "bust": b.bust,
        # `belly` is DELIBERATELY NOT HERE. It is a deterministic function of
        # bmi (r = 0.985 measured), so putting it in the independent-parameter
        # vector would flatter every rank statistic below with a copy of a
        # column that is already in it. Derived quantities do not belong in a
        # measurement of independence.
    }
    for k in SEG_JITTER:
        b.params["r_" + k] = b.ratio[k] / SEG_RATIO[k]
    return b


def skin_colour(melanin, haemo):
    """Linear-RGB base colour from a melanin/haemoglobin pair.

    Two segments through (light, mid, dark) rather than one lerp, because a
    straight line from pale to dark passes through a grey-brown that no real
    skin occupies. Haemoglobin then rotates it toward red without changing
    luminance much, which is what makes cheeks, ears and knuckles read.
    """
    m = float(np.clip(melanin, 0.0, 1.0))
    if m < 0.55:
        t = m / 0.55
        c = [SKIN_LIGHT[i] * (1 - t) + SKIN_MID[i] * t for i in range(3)]
    else:
        t = (m - 0.55) / 0.45
        c = [SKIN_MID[i] * (1 - t) + SKIN_DARK[i] * t for i in range(3)]
    h = (float(np.clip(haemo, 0.0, 1.0)) - 0.5) * 0.22
    c[0] *= 1.0 + h
    c[1] *= 1.0 - 0.35 * h
    c[2] *= 1.0 - 0.55 * h
    return tuple(float(max(v, 0.004)) for v in c)


# ===========================================================================
# 3.  SKELETON -- real joints, real anatomical limits
# ===========================================================================
#
# Convention: X right, Y forward (the direction the figure faces), Z up.
# Every bone has a REST basis expressed in its parent's basis and a local pose
# rotation applied after it, so a pose is a set of DEVIATIONS FROM REST and the
# limits below are limits on those deviations -- which is what an anatomical
# range of motion actually is.

def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == 0:
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)
    if axis == 1:
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def _euler(x, y, z):
    """Intrinsic X then Y then Z, in degrees."""
    return _rot(2, z) @ _rot(1, y) @ _rot(0, x)


# name -> (parent, limits (xlo,xhi, ylo,yhi, zlo,zhi) in degrees)
#
# Ranges are clinical ranges of motion, rounded, and applied about the bone's
# own rest frame. They exist so that a random pose is a POSSIBLE pose: the
# measured defect "arms crossed in an X on the lap, dozens of times" is what a
# tiny pose vocabulary looks like, and an unlimited random one produces
# dislocated shoulders instead, which is worse.
JOINT_LIMITS = {
    "lumbar":   (-25, 40, -22, 22, -35, 35),
    "thorax":   (-18, 28, -16, 16, -32, 32),
    "neck":     (-42, 32, -38, 38, -55, 55),
    "head":     (-14, 12, -12, 12, -18, 18),
    "clav_L":   (-12, 16, -10, 22, -14, 14),
    "clav_R":   (-12, 16, -22, 10, -14, 14),
    "arm_L":    (-62, 165, -95, 42, -92, 55),
    "arm_R":    (-62, 165, -42, 95, -55, 92),
    "fore_L":   (0, 148, 0, 0, -78, 82),
    "fore_R":   (0, 148, 0, 0, -82, 78),
    "hand_L":   (-72, 68, -20, 32, -12, 12),
    "hand_R":   (-72, 68, -32, 20, -12, 12),
    "hip_L":    (-25, 128, -45, 30, -40, 42),
    "hip_R":    (-25, 128, -30, 45, -42, 40),
    "knee_L":   (-140, 3, 0, 0, -8, 8),
    "knee_R":   (-140, 3, 0, 0, -8, 8),
    "foot_L":   (-45, 22, -14, 18, -20, 20),
    "foot_R":   (-45, 22, -18, 14, -20, 20),
}


class Skeleton(object):
    """Bones with world origins and bases, solved once from a Body and a pose."""

    __slots__ = ("body", "origin", "basis", "length", "order", "parent")

    def __init__(self, body):
        self.body = body
        self.origin = {}
        self.basis = {}
        self.length = {}
        self.parent = {}
        self.order = []

    def head_top(self):
        return self.origin["head"] + self.basis["head"] @ np.array(
            [0.0, 0.0, self.length["head"]])

    def joint(self, name):
        return self.origin[name]

    def tip(self, name):
        return self.origin[name] + self.basis[name] @ np.array(
            [0.0, 0.0, self.length[name]])

    def dirn(self, name):
        return self.basis[name] @ np.array([0.0, 0.0, 1.0])


def clamp_pose(pose):
    """Clamp every joint into its anatomical range. Returns a NEW dict.

    Silently clamping is deliberate: a pose sampler that has to know every limit
    is a pose sampler nobody will extend, and an out-of-range shoulder is a
    dislocation, which is a worse artefact than a slightly flattened pose.
    `pose_violations()` reports what was clamped so it is visible.
    """
    out = {}
    for k, v in pose.items():
        lim = JOINT_LIMITS.get(k)
        if lim is None:
            out[k] = tuple(float(a) for a in v)
            continue
        out[k] = (float(np.clip(v[0], lim[0], lim[1])),
                  float(np.clip(v[1], lim[2], lim[3])),
                  float(np.clip(v[2], lim[4], lim[5])))
    return out


def pose_violations(pose):
    """(joint, axis, value, limit) for everything outside its range."""
    bad = []
    for k, v in pose.items():
        lim = JOINT_LIMITS.get(k)
        if lim is None:
            continue
        for i, ax in enumerate("xyz"):
            lo, hi = lim[2 * i], lim[2 * i + 1]
            if not (lo - 1e-9 <= v[i] <= hi + 1e-9):
                bad.append((k, ax, float(v[i]), (lo, hi)))
    return bad


def solve_skeleton(body, pose):
    """Forward kinematics. Returns a Skeleton with world origins and bases.

    The pelvis is placed with its origin at the trochanter height of a figure
    standing on z = 0; `ground_contact()` then measures where the feet and seat
    actually ended up and the caller drops the whole figure onto its contact.
    Solving contact AFTER the pose rather than assuming it is what fixes defect
    10, "some intersect the seat back, some float".
    """
    b = body
    p = clamp_pose(pose)
    sk = Skeleton(b)

    torso = b.acromion_h - b.trochanter_h            # hip joint to shoulder line
    lumbar_len = torso * 0.46
    thorax_len = torso * 0.54

    # REST BASES ARE DECLARED IN WORLD AXES, and the local rest rotation is
    # solved from them. Composing them by hand from Euler triples is how the
    # first version of this function ended up with an elbow that flexed
    # backwards on one side and an arm that pointed out sideways: the algebra is
    # easy to get wrong and impossible to read afterwards. Declaring the answer
    # and solving for the rotation cannot be got wrong silently.
    #
    # Every limb bone gets X=(1,0,0), Y=(0,-1,0), Z=along the bone, so that a
    # POSITIVE local x-rotation is FLEXION on both sides of the body and the
    # joint limits below can be read as anatomy instead of as sign conventions.
    E = np.eye(3)

    def wb(x, y, z):
        return np.stack([np.asarray(x, float), np.asarray(y, float),
                         np.asarray(z, float)], axis=1)

    DOWN = wb((1, 0, 0), (0, -1, 0), (0, 0, -1))     # limb hanging down
    rest_world = {"pelvis": E, "lumbar": E, "thorax": E, "neck": E, "head": E}
    for s, sg in (("R", +1.0), ("L", -1.0)):
        rest_world["clav_" + s] = wb((0, 0, -sg), (0, 1, 0), (sg, 0, 0))
        rest_world["arm_" + s] = DOWN
        rest_world["fore_" + s] = DOWN
        rest_world["hand_" + s] = DOWN
        rest_world["hip_" + s] = DOWN
        rest_world["knee_" + s] = DOWN
        rest_world["foot_" + s] = wb((1, 0, 0), (0, 0, -1), (0, 1, 0))

    def place(name, parent, offset, length):
        pb_rest = E if parent is None else sk_rest[parent]
        rest = pb_rest.T @ rest_world[name]
        if parent is None:
            po, pb = np.zeros(3), E
        else:
            po, pb = sk.origin[parent], sk.basis[parent]
        sk.origin[name] = po + pb @ np.asarray(offset, float)
        e = p.get(name, (0.0, 0.0, 0.0))
        sk.basis[name] = pb @ rest @ _euler(*e)
        sk_rest[name] = rest_world[name]
        sk.length[name] = float(length)
        sk.parent[name] = parent
        sk.order.append(name)

    sk_rest = {}
    place("pelvis", None, (0.0, 0.0, b.trochanter_h), 0.02)
    place("lumbar", "pelvis", (0.0, 0.0, 0.0), lumbar_len)
    place("thorax", "lumbar", (0.0, 0.0, lumbar_len), thorax_len)
    place("neck", "thorax", (0.0, 0.010, thorax_len), b.neck_len)
    # The head bone's ORIGIN is the occipital condyle and its LENGTH is the
    # distance from there to the vertex, which is 0.66 of head height. The chin
    # hangs 0.34 head-heights BELOW the bone origin -- so `sk.tip("head")` is
    # the top of the skull and nothing downstream has to guess where the chin is.
    place("head", "neck", (0.0, -0.012, b.neck_len), 0.66 * b.head_h)

    clav_len = b.shoulder_half * 0.86
    for s in ("R", "L"):
        place("clav_" + s, "thorax", (0.0, 0.014, thorax_len * 0.945), clav_len)
        place("arm_" + s, "clav_" + s, (0.0, 0.0, clav_len), b.upper_arm)
        place("fore_" + s, "arm_" + s, (0.0, 0.0, b.upper_arm), b.forearm)
        place("hand_" + s, "fore_" + s, (0.0, 0.0, b.forearm), b.hand_len)

    thigh = b.trochanter_h - b.knee_h
    shank = b.knee_h - b.ankle_h
    for s, sg in (("R", +1.0), ("L", -1.0)):
        place("hip_" + s, "pelvis", (sg * b.hip_half * 0.60, 0.0, 0.0), thigh)
        place("knee_" + s, "hip_" + s, (0.0, 0.0, thigh), shank)
        place("foot_" + s, "knee_" + s, (0.0, 0.0, shank), b.foot_len)
    return sk


def ground_contact(sk):
    """The z of the lowest foot contact, and the seat contact if seated.

    WEIGHT MUST LAND ON THE SEAT OR THE FEET. Returns a dict; the caller
    subtracts `drop` from the whole figure so the supporting surface is exactly
    touched. Measured afterwards by `contact_error()` on the emitted mesh,
    because a solver that is only asserted is the project's named failure.
    """
    out = {}
    lo = 1e9
    for s in ("L", "R"):
        heel = sk.origin["foot_" + s]
        toe = sk.tip("foot_" + s)
        lo = min(lo, float(heel[2]), float(toe[2]))
        out["foot_" + s] = (float(heel[2]), float(toe[2]))
    out["foot_min_z"] = lo
    out["ischium_z"] = float(sk.origin["pelvis"][2]
                             - sk.body.trochanter_h * 0.145)
    return out


# ===========================================================================
# 4.  MESH MACHINERY -- pure numpy, so it runs and is testable without Blender
# ===========================================================================
#
# Everything is built DIRECTLY IN THE POSED CONFIGURATION. There is no skinning
# and no bind pose: a limb's cross-sections are swept along the centreline the
# solved skeleton already put in world space. That removes the entire class of
# candy-wrapper and collapsed-elbow artefacts, and it means a pose costs nothing
# but a re-sweep.

MAT_SKIN, MAT_TOP, MAT_LEG, MAT_HAIR = 0, 1, 2, 3
MAT_SHOE, MAT_SOLE, MAT_EYE, MAT_ACC, MAT_NAIL = 4, 5, 6, 7, 8
# Two slots the COVERED tier needs and that no soft material can stand in for:
# a helmet shell is clear-coated paint over composite -- glossy, hard-edged
# specular, no sheen -- and a visor is a dark tinted plate with a mirror
# highlight. Rendering either through the fabric shader is what makes a helmet
# read as a felt hat.
MAT_HELM, MAT_VISOR = 9, 10
MAT_NAMES = ("skin", "top", "leg", "hair", "shoe", "sole", "eye", "acc",
             "nail", "helm", "visor")
N_MAT = len(MAT_NAMES)


class Mesh(object):
    """A growing quad/tri soup with a material index per face.

    Deliberately not welded across parts. A garment shell, an arm and a shoe are
    separate closed surfaces that interpenetrate, which is what real clothing
    does and what makes a garment's hem readable as an edge instead of as a
    crease in one continuous skin.
    """

    # Per-vertex channels every material reads. `zone` is what lets ONE skin
    # shader put a lip colour on the lips, a nail on the nail and a darker
    # brow on the brow without a texture image and without a separate material
    # slot per feature; `u`/`v` are the garment's own surface parameterisation,
    # which is what a weave and a seam have to be aligned to. Attributes were
    # retro-fitted once and it was painful, so they are here from the start.
    # ONE MATERIAL SET FOR THE WHOLE POPULATION, and the per-figure differences
    # travel as vertex data. 260 figures x 9 slots would be 2,340 material
    # datablocks, every one of them a copy of the same graph with a different
    # base colour -- which is both wasteful and the thing that makes a crowd
    # impossible to re-grade later. `hk_col` carries the garment colour,
    # `hk_id` a per-figure constant that de-phases every procedural in the
    # shader so two people in the same shirt do not have the same creases.
    # `hk_zone` is a DISCRETE code and a discrete code has a hard boundary.
    # On the face that boundary is a grid edge, and the first Cycles render
    # showed it as a stair-step running down the cheek and along the jaw
    # wherever the lip or brow tint started. So the three masks that carry
    # COLOUR are continuous channels of their own, and `hk_zone` is left to the
    # things whose boundaries are already geometric edges (nail, scalp, palm).
    CHANNELS = ("hk_u", "hk_v", "hk_zone", "hk_wear", "hk_ao", "hk_id",
                "hk_lip", "hk_brow", "hk_dark")

    __slots__ = ("V", "Q", "T", "QM", "TM", "AT", "CV", "_n", "BLK", "LOCK")

    def __init__(self):
        self.V = []
        self.Q = []
        self.T = []
        self.QM = []
        self.TM = []
        self.AT = {c: [] for c in Mesh.CHANNELS}
        self.CV = []
        self._n = 0
        self.BLK = []          # one (qi, ti) per add() -- see orient_outward
        # Pieces added with an EXPLICIT colour, which `colour_by_material` must
        # not repaint. A livery panel and the overall under it are the same
        # material -- the same cloth -- in two colours, so colour cannot be
        # derived from the material slot for them.
        self.LOCK = []

    def add(self, verts, quads=None, tris=None, mat=0, attrs=None, col=None):
        v = np.ascontiguousarray(verts, float).reshape(-1, 3)
        base = self._n
        self.V.append(v)
        self._n += len(v)
        c = np.zeros((len(v), 3)) if col is None else np.broadcast_to(
            np.asarray(col, float).reshape(-1, 3), (len(v), 3)).copy()
        self.CV.append(c)
        self.LOCK.append(col is not None)
        attrs = attrs or {}
        for c in Mesh.CHANNELS:
            a = attrs.get(c)
            if a is None:
                self.AT[c].append(np.zeros(len(v)))
            else:
                self.AT[c].append(np.broadcast_to(
                    np.asarray(a, float).ravel(), (len(v),)).copy())
        qi = ti = -1
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            qi = len(self.Q)
            self.Q.append(q)
            self.QM.append(np.full(len(q), mat, np.int32))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            ti = len(self.T)
            self.T.append(t)
            self.TM.append(np.full(len(t), mat, np.int32))
        self.BLK.append((qi, ti))
        return base

    def merge(self, other):
        base = self._n
        qb, tb = len(self.Q), len(self.T)
        for v in other.V:
            self.V.append(v)
            self._n += len(v)
        for c in Mesh.CHANNELS:
            self.AT[c].extend(other.AT[c])
        self.CV.extend(other.CV)
        self.LOCK.extend(other.LOCK)
        for q, m in zip(other.Q, other.QM):
            self.Q.append(q + base)
            self.QM.append(m)
        for t, m in zip(other.T, other.TM):
            self.T.append(t + base)
            self.TM.append(m)
        for qi, ti in other.BLK:
            self.BLK.append((qi + qb if qi >= 0 else -1,
                             ti + tb if ti >= 0 else -1))

    def orient_outward(self, report=False):
        """Reverse the winding of any emitted piece that faces INWARD.

        WHY THIS EXISTS, MEASURED RATHER THAN SUSPECTED. An orientation audit of
        a finished L1 figure -- signed volume and mean(normal . radial) per
        emitted piece, two independent statistics that agreed on every piece --
        found 55 of 318 pieces inside-out, and they were not obscure ones:

            the HEAD SHELL      2,816 tris   normal . radial  -0.966
            both EARS                                         -0.065
            the HAIR MASS and its hanging fall                -0.97
            both SHOE UPPERS                                  -0.717
            both SOLES                                        -0.450
            all 22 SOLE TREAD BARS                            -0.733

        Cycles shades a back-face by flipping the geometric normal, so these did
        not render black -- they rendered with every BUMP INVERTED, which is
        what turns a brow ridge into a groove and a hair clump into a gutter. It
        is the mechanism behind three of the six defects the 767 px peep was
        rejected for: "faces are not resolving at 100 px of head", "hair reads
        as a straw cone", "shoes read closer to slippers". None of them were
        visible to any check in the file, because every check measured the
        model and none measured the surface's SIDE.

        The decision is per piece and is not a heuristic where it does not have
        to be:

        THERE IS NO HEURISTIC AND NO DEADBAND. Every piece is decided by SIGNED
        VOLUME, which is exact. An OPEN piece -- a sleeve tube, a collar band, a
        strand with one cap -- is closed first: its boundary loops are found
        (edges used exactly once), each is capped by a fan to its own centroid
        with the triangles wound to oppose the boundary edge's direction in the
        face that owns it, and the volume of the resulting closed surface is
        taken. The first version of this used mean(normal . radial) with a
        0.045 deadband for open pieces and ABSTAINED on 13 pieces over 8
        figures, including every trouser head -- a fallback that decides
        nothing is R2-019's defect wearing a different hat.
        """
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        flipped, abstained, flat, closed_n = 0, [], [], 0
        for bi, (qi, ti) in enumerate(self.BLK):
            faces = []
            if qi >= 0:
                faces += [tuple(int(x) for x in f) for f in self.Q[qi]]
            if ti >= 0:
                faces += [tuple(int(x) for x in f) for f in self.T[ti]]
            if len(faces) < 2:
                continue
            tri = []
            for f in faces:
                tri.append((f[0], f[1], f[2]))
                if len(f) == 4:
                    tri.append((f[0], f[2], f[3]))
            tri = np.asarray(tri, np.int64)
            sc = V[tri].mean(axis=1).mean(axis=0)
            use = {}
            for f in faces:
                n = len(f)
                for i in range(n):
                    a, c = f[i], f[(i + 1) % n]
                    k = (a, c) if a < c else (c, a)
                    use.setdefault(k, []).append((a, c))
            bnd = [v[0] for k, v in use.items() if len(v) == 1]
            cap, VV = [], V
            if bnd:
                adj = {}
                for a, c in bnd:
                    adj.setdefault(a, []).append(c)
                    adj.setdefault(c, []).append(a)
                seen, loops = set(), []
                for st in adj:
                    if st in seen:
                        continue
                    comp, stack = [], [st]
                    seen.add(st)
                    while stack:
                        vtx = stack.pop()
                        comp.append(vtx)
                        for w in adj[vtx]:
                            if w not in seen:
                                seen.add(w)
                                stack.append(w)
                    loops.append(set(comp))
                ctrs = [V[np.asarray(sorted(L), int)].mean(axis=0) for L in loops]
                base_c = len(V)
                VV = np.concatenate([V, np.asarray(ctrs)]) if ctrs else V
                for a, c in bnd:
                    for li, L in enumerate(loops):
                        if a in L:
                            cap.append((c, a, base_c + li))
                            break
            allt = np.concatenate([tri, np.asarray(cap, np.int64).reshape(-1, 3)]) \
                if cap else tri
            closed_n += 0 if bnd else 1
            A = VV[allt[:, 0]] - sc
            B = VV[allt[:, 1]] - sc
            Cc = VV[allt[:, 2]] - sc
            vol = float(np.einsum("ij,ij->i", A, np.cross(B, Cc)).sum())
            if abs(vol) < 1e-14:
                # A FLAT PLATE HAS NO INSIDE. A cap peak, a fingernail and a
                # belt buckle enclose no volume, so volume cannot decide them
                # and no amount of arithmetic will make it. Decided instead by
                # the only thing that is defined for them -- which side faces
                # away from the figure -- and RECORDED as `flat`, so the report
                # says which pieces were decided by a weaker rule instead of
                # letting them pass unmentioned.
                nn = np.cross(VV[allt[:, 1]] - VV[allt[:, 0]],
                              VV[allt[:, 2]] - VV[allt[:, 0]])
                aw = sc - V.mean(axis=0)
                d = float(np.einsum("ij,j->i", nn, aw).sum())
                flat.append((bi, len(faces), round(d, 9)))
                inward = d < 0.0
            else:
                inward = vol < 0.0
            if inward:
                flipped += 1
                if qi >= 0:
                    self.Q[qi] = self.Q[qi][:, ::-1].copy()
                if ti >= 0:
                    self.T[ti] = self.T[ti][:, ::-1].copy()
        rep = {"pieces": len(self.BLK), "closed": closed_n,
               "flipped": flipped, "abstained": abstained,
               "flat_decided_by_facing_away": flat}
        return rep if report else self

    def finish(self):
        V = (np.concatenate(self.V) if self.V else np.zeros((0, 3)))
        Q = (np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64))
        T = (np.concatenate(self.T) if self.T else np.zeros((0, 3), np.int64))
        QM = (np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32))
        TM = (np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32))
        A = {c: (np.concatenate(self.AT[c]) if self.AT[c] else np.zeros(0))
             for c in Mesh.CHANNELS}
        A["hk_col"] = (np.concatenate(self.CV) if self.CV else np.zeros((0, 3)))
        return V, Q, T, QM, TM, A

    def n_tris(self):
        return 2 * sum(len(q) for q in self.Q) + sum(len(t) for t in self.T)

    def translate(self, d):
        d = np.asarray(d, float)
        self.V = [v + d for v in self.V]

    def bounds(self):
        if not self.V:
            return None
        lo = np.min([v.min(axis=0) for v in self.V], axis=0)
        hi = np.max([v.max(axis=0) for v in self.V], axis=0)
        return lo, hi

    def vertex_materials(self):
        """The material slot of each vertex (the lowest, at a shared cap)."""
        V, Q, T, QM, TM, _ = self.finish()
        vm = np.full(len(V), 255, np.int32)
        for faces, mats in ((Q, QM), (T, TM)):
            if len(faces):
                for k in range(faces.shape[1]):
                    np.minimum.at(vm, faces[:, k], mats)
        return V, np.where(vm == 255, 0, vm)

    def colour_by_material(self, table):
        """Paint `hk_col` from a per-material-slot colour table.

        Done once at the end rather than threaded through twenty builders: the
        material index already says what each face IS, so a vertex's colour is
        derivable and does not need to be carried. A vertex shared by two
        materials takes the lower slot, which only happens at a cap fan.
        """
        V, vm = self.vertex_materials()
        tab = np.asarray(table, float).reshape(-1, 3)
        C = tab[np.clip(vm, 0, len(tab) - 1)]
        out, i = [], 0
        for k, v in enumerate(self.V):
            out.append(self.CV[k] if (k < len(self.LOCK) and self.LOCK[k])
                       else C[i:i + len(v)].copy())
            i += len(v)
        self.CV = out

    def set_all(self, **channels):
        """Set a scalar channel on every vertex added so far (figure constants)."""
        n = [len(v) for v in self.V]
        for k, val in channels.items():
            self.AT[k] = [np.full(m, float(val)) for m in n]


def _norm(v, axis=-1):
    n = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / np.maximum(n, 1e-12)


def resample_polyline(pts, n):
    """n points equally spaced along a polyline, by arc length."""
    P = np.asarray(pts, float)
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    if s[-1] <= 1e-9:
        return np.repeat(P[:1], n, axis=0), np.zeros(n)
    t = np.linspace(0.0, s[-1], n)
    out = np.empty((n, 3))
    for k in range(3):
        out[:, k] = np.interp(t, s, P[:, k])
    return out, t / s[-1]


def smooth_polyline(P, passes, weight=0.5):
    """Laplacian smoothing with the ends pinned -- this is what rounds a joint.

    A polyline through shoulder, elbow and wrist has a crease at the elbow, and
    a tube swept along it creases too. Smoothing the centreline over a window
    proportional to the limb's own radius rounds the bend the way an elbow
    actually rounds, without any of the machinery of a skin deformer.
    """
    P = np.array(P, float)
    if len(P) < 3:
        return P
    for _ in range(int(passes)):
        Q = P.copy()
        Q[1:-1] = (1.0 - weight) * P[1:-1] + weight * 0.5 * (P[:-2] + P[2:])
        P = Q
    return P


def parallel_frames(P, up_hint=(0.0, 1.0, 0.0)):
    """Rotation-minimising frames along a centreline.

    Columns of each 3x3 are (X, Y, Z) with Z along the curve. Parallel transport
    rather than a fixed up-vector, because a fixed up flips 180 deg when the
    tangent passes through it and the tube turns inside out at exactly the place
    a limb bends most.
    """
    P = np.asarray(P, float)
    n = len(P)
    T = np.empty((n, 3))
    T[:-1] = P[1:] - P[:-1]
    T[-1] = T[-2]
    T = _norm(T)
    ref = np.asarray(up_hint, float)
    if abs(float(np.dot(ref, T[0]))) > 0.94:
        ref = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(ref, T[0]))) > 0.94:
            ref = np.array([1.0, 0.0, 0.0])
    X = _norm(np.cross(ref, T[0]))
    B = np.empty((n, 3, 3))
    for i in range(n):
        if i:
            # rotate the previous X into the new tangent's plane
            v = T[i] - T[i - 1]
            X = X - T[i] * float(np.dot(X, T[i]))
            ln = np.linalg.norm(X)
            if ln < 1e-9:
                X = np.cross(T[i], np.array([0.0, 0.0, 1.0]))
                ln = np.linalg.norm(X)
                if ln < 1e-9:
                    X = np.cross(T[i], np.array([1.0, 0.0, 0.0]))
                    ln = np.linalg.norm(X)
            X = X / max(ln, 1e-12)
            _ = v
        Y = np.cross(T[i], X)
        B[i, :, 0] = X
        B[i, :, 1] = Y
        B[i, :, 2] = T[i]
    return B


def _parab_pass(f, pos, roll, k, period, mode):
    """One grayscale morphological pass along axis 0 with a PARABOLIC element.

    `mode="max"` is the dilation, `mode="min"` the erosion.  The element is
    `g(d) = -d^2 / (2*roll)`, so the pair together is a ball of radius `roll`
    rolled along the outside of `f` -- an operation with one physical
    parameter and no window shape to tune.  `pos` is the sample position in
    the SAME units as `roll` (metres of surface distance here), which is what
    lets the element stay physical on a non-uniformly sampled ring.
    """
    n = f.shape[0]
    ar = np.arange(n)
    shape = [1] * f.ndim
    shape[0] = n
    acc = None
    for j in range(-k, k + 1):
        if period is not None:
            idx = (ar + j) % n
            d = pos[idx] - pos
            d = (d + 0.5 * period) % period - 0.5 * period
        else:
            idx = np.clip(ar + j, 0, n - 1)
            d = pos[idx] - pos
        pen = ((d * d) / (2.0 * roll)).reshape(shape)
        cand = f[idx] - pen if mode == "max" else f[idx] + pen
        if acc is None:
            acc = cand
        else:
            acc = np.maximum(acc, cand) if mode == "max" else np.minimum(acc,
                                                                        cand)
    return acc


def roll_close(f, pos, roll, axis=0, periodic=False, morph="close"):
    """Roll a ball of radius `roll` along the outside of `f`.

    `morph="close"` is dilation-then-erosion -- the IDENTITY on anything the
    ball can touch (a ramp, a bulge, a plateau) and a bridge across anything
    it cannot (a hollow narrower than the ball).  `morph="dilate"` is the
    dilation alone, which is what "cloth bridges concavities" naively becomes
    and which lifts a straight taper by the full element height; it is kept
    because it is the control that is KNOWN to inflate.
    """
    f = np.asarray(f, float)
    pos = np.asarray(pos, float)
    if not roll > 0.0 or f.shape[axis] < 3:
        return f.copy()
    g = np.moveaxis(f, axis, 0)
    n = g.shape[0]
    rng = float(g.max() - g.min())
    if not rng > 1e-9:
        return f.copy()
    sp = float(np.mean(np.abs(np.diff(pos)))) if n > 1 else 1.0
    # the ball can only reach as far as the profile's own range lifts it
    k = int(math.ceil(math.sqrt(2.0 * roll * rng) / max(sp, 1e-9)))
    k = max(1, min(k, 32, (n // 2) if periodic else n))
    if periodic:
        out = _parab_pass(g, pos, roll, k, float(n) * sp, "max")
        if morph != "dilate":
            out = _parab_pass(out, pos, roll, k, float(n) * sp, "min")
            out = np.maximum(out, g)
        return np.moveaxis(out, 0, axis)
    # AN OPEN PROFILE MUST BE PADDED BY EXTRAPOLATION, NOT BY REPLICATION.
    # Replication turns each end into a plateau, and a plateau is a feature:
    # the dilation cannot reach past it and the erosion therefore cannot pull
    # the lift back off, so the closing stops being the identity on a ramp
    # exactly where a garment has its HEM. Measured with replicate padding, a
    # closing deviated from a straight taper by the same 3.6 mm as the plain
    # dilation -- i.e. the control that is supposed to separate the two
    # operators could not, which is the failure mode this project keeps
    # hitting. A linear extrapolation of the end slope makes both passes exact
    # on a ramp and leaves the hem where the pattern cut it.
    m = min(3, n - 1)
    s_lo = (g[m] - g[0]) / max(pos[m] - pos[0], 1e-12)
    s_hi = (g[-1] - g[-1 - m]) / max(pos[-1] - pos[-1 - m], 1e-12)
    d_lo = pos[0] - pos[1] if n > 1 else -sp
    d_hi = pos[-1] - pos[-2] if n > 1 else sp
    j = np.arange(1, k + 1, dtype=float)
    p_lo = pos[0] + j[::-1] * d_lo
    p_hi = pos[-1] + j * d_hi
    sh = [1] * g.ndim
    lo = g[0] + (p_lo - pos[0]).reshape([k] + sh[1:]) * s_lo
    hi = g[-1] + (p_hi - pos[-1]).reshape([k] + sh[1:]) * s_hi
    gp = np.concatenate([lo, g, hi], axis=0)
    pp = np.concatenate([p_lo, pos, p_hi])
    out = _parab_pass(gp, pp, roll, k, None, "max")
    if morph != "dilate":
        out = _parab_pass(out, pp, roll, k, None, "min")
        out = np.maximum(out, gp)
    return np.moveaxis(out[k:k + n], 0, axis)


class Sweep(object):
    """A swept surface, kept as its generating rings so a GARMENT can be built
    from the same rings rather than from a mesh.

    This is the whole reason clothing here is geometry with fit rather than a
    scaled copy of the body: `offset()` returns a NEW Sweep whose radii are the
    body's plus a thickness, a slack field and a wrinkle field, so a shirt over
    a heavy torso and the same shirt over a thin one are different surfaces,
    not the same surface at two scales.
    """

    __slots__ = ("C", "B", "LX", "LY", "closed", "BX", "BY")

    def __init__(self, C, B, LX, LY, closed=True, base=None):
        self.C = np.asarray(C, float)          # (S,3) ring centres
        self.B = np.asarray(B, float)          # (S,3,3) ring bases, cols X Y Z
        self.LX = np.asarray(LX, float)        # (S,R) local x of each ring point
        self.LY = np.asarray(LY, float)        # (S,R)
        self.closed = closed
        # THE RELIEF-FREE RINGS -- the same surface with the body's own muscle /
        # skin noise term left OUT. A garment is lofted from THESE, never from
        # LX/LY. See `relaxed()` for the measurement and the reason.
        self.BX = None if base is None else np.asarray(base[0], float)
        self.BY = None if base is None else np.asarray(base[1], float)

    @property
    def S(self):
        return self.LX.shape[0]

    @property
    def R(self):
        return self.LX.shape[1]

    def verts(self):
        L = np.stack([self.LX, self.LY, np.zeros_like(self.LX)], axis=-1)
        return self.C[:, None, :] + np.einsum("sij,srj->sri", self.B, L)

    def normals2d(self):
        """Outward 2D normal of each ring point, in the ring's own plane."""
        P = np.stack([self.LX, self.LY], axis=-1)                 # (S,R,2)
        nxt = np.roll(P, -1, axis=1)
        prv = np.roll(P, +1, axis=1)
        t = nxt - prv
        nrm = np.stack([t[..., 1], -t[..., 0]], axis=-1)
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-12)
        # orient outward: away from the ring centroid
        ctr = P.mean(axis=1, keepdims=True)
        sgn = np.sign(np.sum(nrm * (P - ctr), axis=-1, keepdims=True))
        sgn[sgn == 0] = 1.0
        return nrm * sgn

    def offset(self, d):
        """A new Sweep displaced by `d` (scalar or (S,R)) along the 2D normal."""
        n = self.normals2d()
        d = np.asarray(d, float)
        if d.ndim == 0:
            d = np.full((self.S, self.R), float(d))
        return Sweep(self.C, self.B, self.LX + n[..., 0] * d,
                     self.LY + n[..., 1] * d, self.closed)

    def extend_start(self, n, dist):
        """Prepend `n` rings extrapolated backwards along the sweep.

        This is what buries a sleeve head inside the shirt. Without it the
        sleeve's first ring sits at the shoulder JOINT, outside the trunk shell,
        and the render shows an open cylinder end stuck on each shoulder like a
        pauldron -- which is exactly what the first clay preview showed.
        """
        if n <= 0:
            return self
        d = self.C[0] - self.C[1]
        nrm = np.linalg.norm(d)
        d = d / max(nrm, 1e-9) * float(dist) / max(n, 1)
        Cs = np.stack([self.C[0] + d * (n - i) for i in range(n)])
        Bs = np.repeat(self.B[:1], n, axis=0)
        k = np.linspace(0.86, 0.99, n)[:, None]
        return Sweep(np.concatenate([Cs, self.C]),
                     np.concatenate([Bs, self.B]),
                     np.concatenate([self.LX[:1] * k, self.LX]),
                     np.concatenate([self.LY[:1] * k, self.LY]), self.closed)

    def slice(self, s0, s1):
        base = None if self.BX is None else (self.BX[s0:s1], self.BY[s0:s1])
        return Sweep(self.C[s0:s1], self.B[s0:s1], self.LX[s0:s1],
                     self.LY[s0:s1], self.closed, base=base)

    # -- THE GARMENT BASE ---------------------------------------------------
    #
    # DEFECT: THE OVERALL WAS WEARING THE BODY'S MUSCLES. `garment_from_sweep`
    # sliced the BODY's Sweep and offset it, so every garment shell inherited,
    # one-for-one, `build_torso`'s `surface_noise x 0.010 x chest_depth` and
    # `build_arm`'s `noise_amp = 0.055 x r`. Found by LOOKING at the B2 bench
    # render at 767 px: the light overall carries large soft blobs that follow
    # the limb like anatomy instead of hanging like cloth.
    #
    # AND IT IS NOT A SMALL TERM. The arm's noise is +-0.055 r = +-2.5 mm at an
    # emitted wavelength of 2.59/9.0 = 0.288 of the arm's length, i.e. ~158 mm,
    # which is a 5.6 deg surface -- and under the contract sun's 12.47 deg
    # elevation that is
    #
    #       m = 2 tan(5.6) / tan(12.47) = 0.89 peak-to-peak
    #
    # a bigger radiance swing than the ENTIRE intended fold language
    # (`fold_field` targets 0.90 hang + 0.60 crumple) and about three times the
    # shader's isotropic crumple (0.28). See section 0.5 of HUMAN-REFERENCE.md:
    # what the eye judges is radiance modulation, not millimetres.
    #
    # THE SECOND TERM IS ALIASED ANATOMY. `build_torso`'s spinal groove is
    # `exp(-(azimuth/0.11)^2)` -- a 0.11 rad Gaussian on a ring that carries a
    # sample every 2 pi / 32 = 0.196 rad. It is NARROWER THAN ONE COLUMN, so it
    # lands on a single line of vertices and displaces it by the full 0.030
    # chest_depth (6.6 mm). That is the same defect class as the one-column
    # seam welt of section 0.4, and a garment must not carry it at all: real
    # cloth BRIDGES a groove that narrow.
    #
    # So the garment base is (a) the relief-free rings and (b) low-passed at a
    # physical bridging length. `sigma_m = 0.017` attenuates a 50 mm surface
    # feature to 0.10 and passes a 250 mm one at 0.91 -- so the spinal groove,
    # the sub-mammary crease and the profile-table kinks go, and the deltoid,
    # the belly, the chest and the buttocks stay, which is what cloth does.

    def relaxed(self, sigma_m=0.017, use_base=True, roll_m=0.0,
                roll_u=0.0, morph="close"):
        """A smoothed, relief-free copy of these rings: the GARMENT BASE.

        `sigma_m` is a Gaussian width in METRES OF SURFACE DISTANCE, applied
        separably: circularly around the ring, clamped along the sweep. The
        ring's mean radius is restored afterwards, because smoothing a polygon
        in Cartesian coordinates shrinks it by the chord-versus-arc error
        (1.5 % on a 26-point ring) and a shrinking garment base is a garment
        that creeps inside the body.

        `roll_m` then does the thing a low-pass CANNOT: it BRIDGES.  See
        `roll_close` -- a rolling ball of that radius run over the radial
        profile along the sweep, which is what stops a garment wrapping into
        the under-bust hollow, the waist, the elbow and the popliteal fossa.
        A low-pass only averages a concavity out against its own walls; it
        moves the shell IN over the bulges by as much as it moves it OUT over
        the hollow, and the result is the skin-tight bodysuit that the B5
        render shows.  `morph="dilate"` is the naive max, kept as the control
        that is KNOWN to inflate.
        """
        LX = self.BX if (use_base and self.BX is not None) else self.LX
        LY = self.BY if (use_base and self.BY is not None) else self.LY
        s = float(sigma_m)
        if not s > 0.0:
            return Sweep(self.C, self.B, LX.copy(), LY.copy(), self.closed)
        P = np.stack([LX, LY], axis=-1)                       # (S,R,2)
        ctr = P.mean(axis=1, keepdims=True)
        rad0 = np.linalg.norm(P - ctr, axis=-1).mean(axis=1)  # (S,)
        # sample spacing, in metres, in each direction
        du = float(np.linalg.norm(np.roll(P, -1, axis=1) - P, axis=-1).mean())
        dv = (float(np.linalg.norm(np.diff(self.C, axis=0), axis=1).mean())
              if self.S > 1 else 1.0)
        Q = P
        for axis, dd in ((1, du), (0, dv)):
            sig = s / max(dd, 1e-9)
            if sig < 0.12:                      # finer than the mesh: no-op
                continue
            rad = int(min(8, max(1, round(2.5 * sig))))
            k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sig) ** 2)
            k = k / k.sum()
            acc = np.zeros_like(Q)
            for j, w in zip(range(-rad, rad + 1), k):
                if axis == 1:
                    acc = acc + w * np.roll(Q, -j, axis=1)
                else:
                    idx = np.clip(np.arange(Q.shape[0]) + j, 0, Q.shape[0] - 1)
                    acc = acc + w * Q[idx]
            Q = acc
        c2 = Q.mean(axis=1, keepdims=True)
        r2 = np.linalg.norm(Q - c2, axis=-1).mean(axis=1)
        Q = c2 + (Q - c2) * (rad0 / np.maximum(r2, 1e-9))[:, None, None]
        Q = self._bridge(Q, roll_m, roll_u, morph)
        return Sweep(self.C, self.B, Q[..., 0], Q[..., 1], self.closed)

    # -- THE BRIDGE ---------------------------------------------------------
    #
    # DEFECT: THE OVERALL STILL READ AS A SKIN-TIGHT BODYSUIT.  Removing the
    # body's muscle relief (above) killed the anatomy blobs and did NOT make
    # the suit hang, because a garment that follows the body exactly is a paint
    # job whatever its surface carries.  A low-pass is the wrong operator for
    # this and the reason is one line: it is SIGN-SYMMETRIC.  It pulls the
    # shell out of a hollow and equally far into a bulge, so the shell keeps
    # the body's every feature at reduced contrast.  Cloth is not symmetric --
    # it is a membrane in TENSION over the high points, so it spans a hollow
    # completely and touches a bulge exactly.
    #
    # The operator for that is a grayscale morphological CLOSING of the radial
    # profile: dilate, then erode, with the same structuring element.  A plain
    # dilation is what "cloth bridges concavities" sounds like and it is wrong
    # in a way that shows immediately in a render -- a dilation is EXTENSIVE
    # everywhere, so it lifts a straight taper (an upper arm, a shin) by the
    # full element height and everybody comes out inflated and armoured.  A
    # closing is the identity on any profile the element can touch: exact on a
    # ramp, exact on a bulge, and it fills only what is genuinely concave.
    # `_bridge_controls` in the selftest is that pair, on synthetic profiles
    # with a closed-form answer.
    #
    # The element is a PARABOLA, not a flat window, which makes the operation a
    # rolling ball of radius `roll_m` run along the outside of the profile --
    # the physical picture, and one parameter with a physical meaning: the
    # tightest external curvature a stiff panel of this cloth will take.  A
    # ball of radius R spanning a hollow of width W dips into it by W^2/8R, so
    # R = 0.16 m leaves 8 mm of a 100 mm-wide hollow -- it does not erase the
    # waist, it stops the garment tracking it.

    def _bridge(self, Q, roll_m, roll_u, morph):
        if not (roll_m > 0.0 or roll_u > 0.0) or self.S < 3:
            return Q
        ctr = Q.mean(axis=1, keepdims=True)
        D = Q - ctr
        rad = np.linalg.norm(D, axis=-1)                        # (S,R)
        unit = D / np.maximum(rad[..., None], 1e-12)
        out = rad
        if roll_m > 0.0:
            arc = np.concatenate(
                [[0.0], np.cumsum(np.linalg.norm(np.diff(self.C, axis=0),
                                                 axis=1))])
            out = roll_close(out, arc, roll_m, axis=0, periodic=False,
                             morph=morph)
        if roll_u > 0.0:
            # metres AROUND the ring: mean chord x index, which is what the
            # circumference of a 26-gon divides into.
            du = float(np.linalg.norm(np.roll(Q, -1, axis=1) - Q,
                                      axis=-1).mean())
            pos = np.arange(self.R, dtype=float) * du
            out = roll_close(out, pos, roll_u, axis=1,
                             periodic=self.closed, morph=morph)
        return ctr + unit * out[..., None]

    def emit(self, mesh, mat, cap_start=False, cap_end=False, flip=False,
             zone=0.0, wear=0.0, u0=0.0, u1=1.0, v0=0.0, v1=1.0, col=None):
        """Quads between consecutive rings, plus optional fan caps.

        Indices are built LOCAL to this sweep and handed to `Mesh.add` once, so
        the cap fans cannot be offset twice -- which they were in the first
        version of this method, and the symptom was caps stitched to whatever
        part happened to be emitted before them.
        """
        if not self.closed:
            raise ValueError("Sweep.emit: only closed rings are supported")
        S, R = self.S, self.R
        V = [self.verts().reshape(-1, 3)]
        nv = S * R
        idx = np.arange(nv).reshape(S, R)
        nxt = (np.arange(R) + 1) % R
        q = np.stack([idx[:-1, :].ravel(), idx[:-1, nxt].ravel(),
                      idx[1:, nxt].ravel(), idx[1:, :].ravel()], axis=1)
        if flip:
            q = q[:, ::-1]
        tris = []
        if cap_start:
            ctr = self.C[0] + self.B[0] @ np.array(
                [self.LX[0].mean(), self.LY[0].mean(), 0.0])
            V.append(ctr.reshape(1, 3))
            ci = nv
            nv += 1
            for r in range(R):
                tris.append([ci, idx[0, (r + 1) % R], idx[0, r]])
        if cap_end:
            ctr = self.C[-1] + self.B[-1] @ np.array(
                [self.LX[-1].mean(), self.LY[-1].mean(), 0.0])
            V.append(ctr.reshape(1, 3))
            ci = nv
            nv += 1
            for r in range(R):
                tris.append([ci, idx[-1, r], idx[-1, (r + 1) % R]])
        T = np.asarray(tris, np.int64).reshape(-1, 3) if tris else None
        if flip and T is not None:
            T = T[:, ::-1]
        VV = np.concatenate(V)
        uu = np.tile(np.linspace(u0, u1, R, endpoint=False), S)
        vv = np.repeat(np.linspace(v0, v1, S), R)
        pad = len(VV) - S * R
        if pad > 0:
            uu = np.concatenate([uu, np.zeros(pad)])
            vv = np.concatenate([vv, np.zeros(pad)])
            if col is not None and np.ndim(col) == 2 and len(col) == S * R:
                col = np.concatenate([col, np.repeat(col[-1:], pad, axis=0)])
        return mesh.add(VV, quads=q, tris=T, mat=mat, col=col,
                        attrs={"hk_u": uu, "hk_v": vv,
                               "hk_zone": zone, "hk_wear": wear})


def ring_theta(R):
    return np.linspace(0.0, TAU, R, endpoint=False)


def superellipse(theta, ax, ay, n=2.4):
    """A cross-section between a circle (n=2) and a rounded rectangle.

    Real limbs are not circular: a thigh is wider than deep and flattens
    medially, a forearm is an ellipse that rotates through pronation, a torso is
    close to a rounded rectangle. One exponent covers the family.
    """
    c, s = np.cos(theta), np.sin(theta)
    k = (np.abs(c) ** n + np.abs(s) ** n) ** (-1.0 / n)
    return ax * k * c, ay * k * s


def profile_at(table, t):
    """Piecewise-linear anatomical radius profile. `table` = ((t, mult), ...)."""
    ts = np.array([p[0] for p in table])
    vs = np.array([p[1] for p in table])
    return np.interp(t, ts, vs)


# THE SAME TRAP AS THE SHADER'S, IN THE GEOMETRY. `itemkit.fbm2` is value noise
# on a unit lattice, and "one lattice cell" is NOT one wavelength: the field has
# to cross zero twice per cycle, and it does so far less often than once a cell.
# MEASURED, with a zero-crossing estimator calibrated on sinusoids of known
# wavelength (it returned 1.008 and 1.002 x the truth), six seeds per cell, on a
# 262,144-sample record:
#
#     octaves    emitted wavelength, in lattice cells
#        1                3.99 +- 0.35
#        2                2.95 +- 0.23
#        3                2.59 +- 0.20
#        4                2.24 +- 0.14
#
# More octaves means MORE zero crossings, hence a shorter apparent fundamental;
# the numbers are for the finished fbm, which is what callers actually get.
# `fold_field` below used `scale = 1/lambda`, so its declared 60-140 mm flutes
# were emitting at 155-360 mm.
FBM_LAMBDA_CELLS = {1: 3.99, 2: 2.95, 3: 2.59, 4: 2.24}


def fbm_scale(lam_units, oct=4):
    """The `scale` that makes `surface_noise` emit features `lam_units` long,
    where the unit is whatever u or v is normalised over."""
    return FBM_LAMBDA_CELLS[int(np.clip(oct, 1, 4))] / max(float(lam_units), 1e-9)


def surface_noise(seed, u, v, scale_u, scale_v, oct=4, gain=0.5):
    """Correlated noise on a (u, v) parameterisation, in [-1, 1].

    `scale_u`/`scale_v` are LATTICE CELLS per unit, not wavelengths. Use
    `fbm_scale()` to convert, and read the note above it for why they differ by
    2.2-4.0x.
    """
    return 2.0 * K.fbm2(np.asarray(u) * scale_u, np.asarray(v) * scale_v,
                        seed=int(seed) & 0x7FFFFFFF, oct=int(oct),
                        gain=gain) - 1.0


def smooth_centerline(pts, sigma_m, n_out):
    """Resample, Gaussian-smooth by a PHYSICAL width, resample again.

    `sigma_m` is a length in metres, normally the limb's own radius: a joint
    rounds over the scale of the thing that is bending, so an elbow on a thin
    arm is a sharper corner than the same angle on a heavy one. Endpoints are
    clamped, so the wrist and the shoulder stay where the skeleton put them.
    """
    dense, _ = resample_polyline(pts, 241)
    L = float(np.sum(np.linalg.norm(np.diff(dense, axis=0), axis=1)))
    ds = L / 240.0
    sig = max(float(sigma_m) / max(ds, 1e-9), 0.35)
    rad = int(min(60, max(1, round(3.0 * sig))))
    x = np.arange(-rad, rad + 1, dtype=float)
    k = np.exp(-0.5 * (x / sig) ** 2)
    k /= k.sum()
    pad = np.concatenate([np.repeat(dense[:1], rad, 0), dense,
                          np.repeat(dense[-1:], rad, 0)])
    sm = np.empty_like(dense)
    for c in range(3):
        sm[:, c] = np.convolve(pad[:, c], k, mode="valid")
    sm[0] = dense[0]
    sm[-1] = dense[-1]
    out, t = resample_polyline(sm, int(n_out))
    return out, t


def tube_from_chain(pts, radii_t, radii_r, ring, seed, aspect=1.0, expo=2.3,
                    smooth_r=None, noise_amp=0.0, noise_su=3.0, noise_sv=7.0,
                    twist=0.0):
    """A limb: a superellipse swept along a smoothed joint chain.

    `radii_t` / `radii_r` are the anatomical radius profile -- arc-length
    fraction against radius in METRES. It is not a taper. A cone from shoulder
    to wrist is exactly the `silhouette_departs_from_analytic` failure the gate
    was written to catch (`crew_fireproof_overall`'s trouser fitted a quadratic
    to 0.61 px RMS), so the deltoid, the biceps belly, the olecranon narrowing
    and the forearm belly are all in the table and all of them show up in the
    outline.
    """
    S = len(radii_t) if radii_t is None else None
    n_st = int(S or 0)
    return _tube_impl(pts, radii_t, radii_r, ring, seed, aspect, expo,
                      smooth_r, noise_amp, noise_su, noise_sv, twist, n_st)


def _tube_impl(pts, prof_t, prof_r, ring, seed, aspect, expo, smooth_r,
               noise_amp, noise_su, noise_sv, twist, n_st):
    S = int(n_st) if n_st else max(8, len(prof_t))
    sr = smooth_r if smooth_r is not None else float(np.mean(prof_r))
    C, t = smooth_centerline(pts, sr, S)
    B = parallel_frames(C)
    th = ring_theta(ring)
    r = np.interp(t, prof_t, prof_r)
    asp = np.interp(t, prof_t, np.broadcast_to(np.asarray(aspect, float),
                                               np.shape(prof_r)))
    ex = np.interp(t, prof_t, np.broadcast_to(np.asarray(expo, float),
                                              np.shape(prof_r)))
    LX = np.empty((S, ring))
    LY = np.empty((S, ring))
    for s in range(S):
        tw = twist * t[s]
        cx, cy = superellipse(th + tw, r[s], r[s] * asp[s], ex[s])
        LX[s] = cx
        LY[s] = cy
    if noise_amp > 0.0:
        n = surface_noise(seed, th[None, :] / TAU, t[:, None],
                          noise_su, noise_sv, oct=3)
        d = n * (noise_amp * r[:, None])
        sw = Sweep(C, B, LX, LY)
        nm = sw.normals2d()
        # THE RELIEF-FREE RINGS ARE KEPT. This term is SKIN -- it is what stops
        # a bare limb reading as an extruded superellipse -- and it must not
        # travel through a garment shell. See Sweep.relaxed.
        return Sweep(C, B, LX + nm[..., 0] * d, LY + nm[..., 1] * d,
                     base=(LX, LY))
    return Sweep(C, B, LX, LY)


# ===========================================================================
# 5.  THE BODY -- torso, limbs, neck. Anatomical profiles, not tapers.
# ===========================================================================

def arm_profile(b):
    """(t, radius_m) from the shoulder joint to the wrist joint."""
    a, w = b.arm_r, b.wrist_r
    t = np.array([0.00, 0.06, 0.14, 0.26, 0.40, 0.50, 0.56, 0.63, 0.70,
                  0.82, 0.92, 1.00])
    r = np.array([a * 1.22, a * 1.30, a * 1.16, a * 1.04, a * 0.93,
                  a * 0.88, a * 0.92, a * 0.94, a * 0.88, a * 0.76,
                  w * 1.16, w])
    return t, r


def leg_profile(b):
    """(t, radius_m) from the hip joint to the ankle joint."""
    th, ca, an = b.thigh_r, b.calf_r, b.ankle_r
    t = np.array([0.00, 0.07, 0.18, 0.32, 0.44, 0.50, 0.55, 0.62, 0.70,
                  0.80, 0.90, 1.00])
    r = np.array([th * 0.90, th * 1.00, th * 1.02, th * 0.92, th * 0.80,
                  th * 0.74, ca * 1.02, ca * 1.16, ca * 1.06, ca * 0.84,
                  an * 1.22, an])
    return t, r


def build_arm(sk, side, b, lod, seed):
    pts = [sk.origin["arm_" + side], sk.origin["fore_" + side],
           sk.origin["hand_" + side]]
    t, r = arm_profile(b)
    S = 3 * lod.station + 4
    asp = np.full_like(t, 0.92)
    asp[t > 0.55] = 0.80                       # forearm is flattened, not round
    ex = np.where(t < 0.30, 2.5, 2.2)
    return _tube_impl(pts, t, r, lod.ring, seed + 11, asp, ex,
                      smooth_r=b.arm_r * 1.15, noise_amp=0.055,
                      noise_su=2.5, noise_sv=9.0, twist=0.0, n_st=S)


def build_leg(sk, side, b, lod, seed):
    pts = [sk.origin["hip_" + side], sk.origin["knee_" + side],
           sk.origin["foot_" + side]]
    t, r = leg_profile(b)
    S = 3 * lod.station + 5
    asp = np.full_like(t, 0.93)
    asp[t < 0.40] = 0.86                       # thigh wider than deep
    asp[t > 0.60] = 1.05                       # calf deeper than wide
    ex = np.full_like(t, 2.4)
    return _tube_impl(pts, t, r, lod.ring, seed + 13, asp, ex,
                      smooth_r=b.thigh_r * 0.95, noise_amp=0.045,
                      noise_su=2.5, noise_sv=8.0, twist=0.0, n_st=S)


def _blend_basis(B0, B1, w):
    """Blend two orthonormal frames and re-orthonormalise (Gram-Schmidt)."""
    M = B0 * (1.0 - w) + B1 * w
    z = M[:, 2] / max(np.linalg.norm(M[:, 2]), 1e-12)
    x = M[:, 0] - z * float(np.dot(M[:, 0], z))
    nx = np.linalg.norm(x)
    if nx < 1e-9:
        x = np.cross(np.array([0.0, 1.0, 0.0]), z)
        nx = np.linalg.norm(x)
    x = x / max(nx, 1e-12)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)


def build_torso(sk, b, lod, seed):
    """The trunk, as horizontal cross-sections swept up a bending spine.

    Returns (Sweep, t) so garments can be cut at a parameter rather than at a
    height: a hem at t = 0.30 is at the same place on the body of a 1.45 m
    twelve-year-old and a 1.92 m adult, which a z cut is not.
    """
    # t = 0 is the HIP JOINT and t = 1 the acromion, but the trunk continues
    # below the hip joints: the buttocks and the perineum are ~0.11 m lower and
    # the legs emerge from inside that mass. Stopping the trunk at t = 0 left a
    # flat disc where the crotch should be.
    T0 = -0.24
    S = max(14, 4 * lod.station + 8)
    R = max(12, lod.ring + 6)
    t = np.linspace(T0, 1.0, S)
    th = ring_theta(R)
    pel = sk.origin["pelvis"]
    tho = sk.origin["thorax"]
    top = sk.tip("thorax")
    torso_len = float(np.linalg.norm(top - pel))
    below = pel + sk.basis["pelvis"] @ np.array([0.0, 0.0, T0 * torso_len])
    C, _ = smooth_centerline([below, pel, tho, top], b.waist_half * 0.55, S)
    Bl = sk.basis["lumbar"]
    Bt = sk.basis["thorax"]
    B = np.empty((S, 3, 3))
    for s in range(S):
        w = float(np.clip((t[s] - 0.30) / 0.40, 0.0, 1.0))
        B[s] = _blend_basis(Bl, Bt, w * w * (3 - 2 * w))

    # --- half-breadth and half-depth up the trunk -------------------------
    hw = np.interp(t, [T0, -0.16, -0.06, 0.00, 0.10, 0.30, 0.44, 0.62, 0.80,
                       0.93, 1.00],
                   [b.hip_half * 0.50, b.hip_half * 0.82, b.hip_half * 0.98,
                    b.hip_half * 1.00, b.hip_half * 1.04, b.waist_half * 1.05,
                    b.waist_half, b.chest_half * 0.93, b.chest_half,
                    b.shoulder_half * 0.90, b.shoulder_half * 0.84])
    cd = b.chest_depth * 0.5
    wd = b.waist_depth * 0.5
    hd = np.interp(t, [T0, -0.16, -0.06, 0.00, 0.12, 0.30, 0.44, 0.62, 0.80,
                       0.93, 1.00],
                   [wd * 0.62, wd * 0.94, wd * 1.10, wd * 1.12, wd * 1.10,
                    wd * 1.00, wd * 0.96, cd * 0.94, cd, cd * 0.92, cd * 0.84])

    c, s_ = np.cos(th), np.sin(th)
    n = 2.55
    k = (np.abs(c) ** n + np.abs(s_) ** n) ** (-1.0 / n)
    LX = hw[:, None] * (k * c)[None, :]
    LY = hd[:, None] * (k * s_)[None, :]

    front = np.maximum(s_, 0.0)[None, :]
    back = np.maximum(-s_, 0.0)[None, :]

    def gz(mu, sd):
        return np.exp(-0.5 * ((t - mu) / sd) ** 2)[:, None]

    # belly, and it is FORWARD and LOW, not a uniform inflation
    LY = LY + (b.belly * b.waist_depth * 0.30) * gz(0.30, 0.15) * front ** 1.6
    LX = LX + (b.belly * b.waist_half * 0.16) * gz(0.30, 0.18) \
        * np.abs(c)[None, :] ** 2.0
    # pectoral / bust
    if b.bust > 0.0:
        for sgn in (+1.0, -1.0):
            ang = np.arctan2(s_, c) - sgn * 0.62
            ang = (ang + math.pi) % TAU - math.pi
            lobe = np.exp(-0.5 * (ang / 0.42) ** 2)[None, :]
            LY = LY + (b.bust * b.chest_depth * 0.36) * gz(0.755, 0.075) * lobe
    else:
        LY = LY + (b.chest_depth * 0.045) * gz(0.78, 0.075) * front ** 2.2
    # the pectoral / sub-mammary shelf line -- a real crease under the chest
    LY = LY - (b.chest_depth * 0.022) * gz(0.685, 0.028) * front ** 2.0
    # spinal groove down the back, and the scapulae either side of it
    LY = LY + (b.chest_depth * 0.030) * gz(0.55, 0.30) \
        * (np.exp(-0.5 * ((np.arctan2(s_, c) + math.pi / 2) / 0.11) ** 2))[None, :]
    for sgn in (+1.0, -1.0):
        ang = np.arctan2(s_, c) + math.pi / 2 - sgn * 0.46
        ang = (ang + math.pi) % TAU - math.pi
        LY = LY - (b.chest_depth * 0.040) * gz(0.795, 0.055) \
            * np.exp(-0.5 * (ang / 0.30) ** 2)[None, :]
    # iliac crest, and the latissimus flare above the waist
    LX = LX + (b.hip_half * 0.045) * gz(0.115, 0.045) * np.abs(c)[None, :] ** 3
    LX = LX + (b.chest_half * 0.055) * gz(0.62, 0.10) * np.abs(c)[None, :] ** 2
    # the buttocks -- a real backward mass below the hip joint, and the gluteal
    # fold under it. Without this a seated figure has nothing to sit ON.
    glute = (0.22 + 0.30 * b.belly + (0.16 if b.sex == "F" else 0.0))
    LY = LY - (glute * b.hip_half) * gz(-0.055, 0.115) * back ** 1.5
    LY = LY + (0.055 * b.hip_half) * gz(-0.185, 0.045) * back ** 2.0

    # muscle / skin relief -- small, but it is what stops the trunk reading as
    # an extruded superellipse in the outline
    nz = surface_noise(seed + 31, th[None, :] / TAU, t[:, None], 3.0, 5.0, oct=3)
    sw = Sweep(C, B, LX, LY)
    nm = sw.normals2d()
    d = nz * (0.010 * b.chest_depth)
    return Sweep(C, B, LX + nm[..., 0] * d, LY + nm[..., 1] * d,
                 base=(LX, LY)), t


def build_neck(sk, b, lod, seed):
    pts = [sk.origin["neck"] + sk.basis["neck"] @ np.array([0, 0, -b.neck_len * 0.55]),
           sk.origin["head"]]
    t = np.array([0.0, 0.35, 0.75, 1.0])
    r = np.array([b.neck_r * 1.30, b.neck_r * 1.05, b.neck_r * 0.95,
                  b.neck_r * 0.92])
    return _tube_impl(pts, t, r, max(10, lod.ring - 6), seed + 17,
                      np.array([1.10, 1.05, 1.00, 1.00]), 2.2,
                      smooth_r=b.neck_r, noise_amp=0.03, noise_su=2.0,
                      noise_sv=4.0, twist=0.0, n_st=max(5, lod.station + 2))


def emit_grid(mesh, P, mat, closed_u=True, cap_lo=None, cap_hi=None,
              zone=0.0, wear=0.0, uu=None, vv=None, flip=False, col=None,
              extra=None):
    """Emit an (S, R, 3) grid of points as quads, with optional pole fans.

    One entry point for every gridded surface here -- head, ear, hair cap, shoe
    -- because index bookkeeping written five times is index bookkeeping wrong
    at least once, and a mis-stitched cap is a hole that only shows up as a
    black pixel in a render nobody looked at.
    """
    P = np.asarray(P, float)
    S, R, _ = P.shape
    V = [P.reshape(-1, 3)]
    nv = S * R
    idx = np.arange(nv).reshape(S, R)
    nx = (np.arange(R) + 1) % R if closed_u else np.arange(1, R)
    if closed_u:
        q = np.stack([idx[:-1, :].ravel(), idx[:-1, nx].ravel(),
                      idx[1:, nx].ravel(), idx[1:, :].ravel()], axis=1)
    else:
        q = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(),
                      idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], axis=1)
    tris = []
    caps = []
    if cap_lo is not None:
        V.append(np.asarray(cap_lo, float).reshape(1, 3))
        ci = nv
        nv += 1
        caps.append(ci)
        for r in range(R if closed_u else R - 1):
            tris.append([ci, idx[0, (r + 1) % R], idx[0, r]])
    if cap_hi is not None:
        V.append(np.asarray(cap_hi, float).reshape(1, 3))
        ci = nv
        nv += 1
        caps.append(ci)
        for r in range(R if closed_u else R - 1):
            tris.append([ci, idx[-1, r], idx[-1, (r + 1) % R]])
    T = np.asarray(tris, np.int64).reshape(-1, 3) if tris else None
    if flip:
        q = q[:, ::-1]
        if T is not None:
            T = T[:, ::-1]
    if uu is None:
        uu = np.tile(np.linspace(0.0, 1.0, R, endpoint=closed_u is False), S)
    else:
        uu = np.asarray(uu, float).ravel()
    if vv is None:
        vv = np.repeat(np.linspace(0.0, 1.0, S), R)
    else:
        vv = np.asarray(vv, float).ravel()
    z = np.broadcast_to(np.asarray(zone, float).ravel(), (S * R,)) \
        if np.ndim(zone) else np.full(S * R, float(zone))
    w = np.broadcast_to(np.asarray(wear, float).ravel(), (S * R,)) \
        if np.ndim(wear) else np.full(S * R, float(wear))
    if caps:
        uu = np.concatenate([uu, np.zeros(len(caps))])
        vv = np.concatenate([vv, np.zeros(len(caps))])
        z = np.concatenate([z, np.zeros(len(caps))])
        w = np.concatenate([w, np.zeros(len(caps))])
    at = {"hk_u": uu, "hk_v": vv, "hk_zone": z, "hk_wear": w}
    for k, a in (extra or {}).items():
        a = np.asarray(a, float).ravel()
        pad = len(uu) - len(a)
        if pad > 0:
            a = np.concatenate([a, np.zeros(pad)])
        elif pad < 0:
            a = a[:len(uu)]
        at[k] = a
    return mesh.add(np.concatenate(V), quads=q, tris=T, mat=mat, col=col,
                    attrs=at)


# ===========================================================================
# 6.  THE HEAD -- skull structure, brow, nose, jaw, ears, eyes, neck transition
# ===========================================================================
#
# Defect 1: "heads are featureless ovoids -- no face, ears, jaw, brow, no hair
# geometry. At macro distance a head reads as an egg."
#
# The construction is an ellipsoid warped by a SHAPE stage (jaw taper, face
# plane, occiput, cranial vault) and then displaced by ~30 anatomical LOBES --
# anisotropic Gaussians at named landmarks, applied along the surface normal.
# It is not a sculpt and it is not trying to be a portrait: at the measured
# 767 px the head is 176 px tall and an eye is 11 px, so what has to be right is
# the ARRANGEMENT OF LIGHT AND SHADOW -- brow shadow, nose shadow, eye sockets,
# the lip line, the shadow under the jaw. Those are what the lobe list is.
#
# Coordinates are the UNIT SPHERE the ellipsoid is built from: fx along the
# head's width, fy forward, fz up, all in [-1, 1]. Amplitudes are fractions of
# HEAD HEIGHT, so a small head gets a proportionally small nose.

#            name              fx     fy     fz     sx    sy    sz    amp     key
HEAD_LOBES = (
    ("brow_ridge_L",         -0.34,  0.86,  0.31, 0.30, 0.60, 0.105, +0.030, "brow"),
    ("brow_ridge_R",         +0.34,  0.86,  0.31, 0.30, 0.60, 0.105, +0.030, "brow"),
    ("glabella",              0.00,  0.92,  0.30, 0.11, 0.60, 0.090, +0.013, "brow"),
    ("nasal_root",            0.00,  0.90,  0.215, 0.13, 0.60, 0.055, -0.021, None),
    ("nose_bridge",           0.00,  0.95,  0.075, 0.090, 0.60, 0.185, +0.058, "nose"),
    ("nose_tip",              0.00,  1.00, -0.095, 0.105, 0.60, 0.078, +0.082, "nose"),
    ("ala_L",                -0.115, 0.92, -0.115, 0.075, 0.50, 0.060, +0.038, "nose"),
    ("ala_R",                +0.115, 0.92, -0.115, 0.075, 0.50, 0.060, +0.038, "nose"),
    ("nostril_L",            -0.082, 0.93, -0.170, 0.042, 0.45, 0.033, -0.030, None),
    ("nostril_R",            +0.082, 0.93, -0.170, 0.042, 0.45, 0.033, -0.030, None),
    ("subnasale",             0.00,  0.95, -0.180, 0.150, 0.50, 0.030, -0.021, None),
    ("philtrum",              0.00,  0.93, -0.255, 0.044, 0.50, 0.055, -0.012, None),
    ("upper_lip",             0.00,  0.93, -0.310, 0.200, 0.50, 0.046, +0.023, "lip"),
    ("lip_line",              0.00,  0.95, -0.352, 0.215, 0.50, 0.016, -0.020, "lip"),
    ("lower_lip",             0.00,  0.93, -0.400, 0.180, 0.50, 0.050, +0.025, "lip"),
    ("mentolabial",           0.00,  0.90, -0.500, 0.200, 0.50, 0.055, -0.023, None),
    ("chin",                  0.00,  0.80, -0.640, 0.300, 0.55, 0.175, +0.038, "chin"),
    ("zygomatic_L",          -0.62,  0.62, -0.020, 0.240, 0.55, 0.165, +0.023, None),
    ("zygomatic_R",          +0.62,  0.62, -0.020, 0.240, 0.55, 0.165, +0.023, None),
    ("cheek_L",              -0.520, 0.70, -0.250, 0.300, 0.55, 0.230, +0.016, None),
    ("cheek_R",              +0.520, 0.70, -0.250, 0.300, 0.55, 0.230, +0.016, None),
    ("nasolabial_L",         -0.300, 0.86, -0.300, 0.070, 0.45, 0.130, -0.014, None),
    ("nasolabial_R",         +0.300, 0.86, -0.300, 0.070, 0.45, 0.130, -0.014, None),
    ("orbit_L",              -0.360, 0.82,  0.130, 0.190, 0.55, 0.115, -0.048, "eye"),
    ("orbit_R",              +0.360, 0.82,  0.130, 0.190, 0.55, 0.115, -0.048, "eye"),
    ("lid_upper_L",          -0.360, 0.88,  0.186, 0.165, 0.45, 0.042, +0.030, "eye"),
    ("lid_upper_R",          +0.360, 0.88,  0.186, 0.165, 0.45, 0.042, +0.030, "eye"),
    ("lid_lower_L",          -0.360, 0.88,  0.048, 0.165, 0.45, 0.036, +0.024, "eye"),
    ("lid_lower_R",          +0.360, 0.88,  0.048, 0.165, 0.45, 0.036, +0.024, "eye"),
    ("temporal_L",           -0.800, 0.50,  0.360, 0.230, 0.55, 0.200, -0.011, None),
    ("temporal_R",           +0.800, 0.50,  0.360, 0.230, 0.55, 0.200, -0.011, None),
    ("gonial_L",             -0.680, 0.16, -0.560, 0.290, 0.55, 0.190, +0.034, "jaw"),
    ("gonial_R",             +0.680, 0.16, -0.560, 0.290, 0.55, 0.190, +0.034, "jaw"),
    ("occiput",               0.00, -0.90,  0.120, 0.520, 0.35, 0.300, +0.011, None),
    ("nuchal",                0.00, -0.85, -0.330, 0.400, 0.35, 0.140, -0.016, None),
)

# Zone codes baked into `hk_zone` so ONE skin shader can put a lip colour on the
# lips and a brow on the brow without an image texture and without a material
# slot per feature.
ZONE_SKIN, ZONE_LIP, ZONE_BROW, ZONE_EYE, ZONE_NAIL = 0.0, 1.0, 2.0, 3.0, 4.0
ZONE_JAW, ZONE_CHIN, ZONE_NOSE, ZONE_SCALP, ZONE_PALM = 5.0, 6.0, 7.0, 8.0, 9.0
ZONE_BELT = 10.0
ZONE_KEY = {"lip": ZONE_LIP, "brow": ZONE_BROW, "eye": ZONE_EYE,
            "jaw": ZONE_JAW, "chin": ZONE_CHIN, "nose": ZONE_NOSE}


FACE_GRID_WARP = 1.0
FACE_LOBE_FLOOR = 1.0
"""DEFECT 1 -- "the face is a blank egg" -- AND ITS MECHANISM, WHICH IS SAMPLING.

The fifth pass measured `HEAD_LOBES` at **m = 2.22**, more relief than anything
on the garment, and concluded correctly that the face is not flat and that the
tint does 0.05 % of the work. What it measured was the ANALYTIC LOBE FIELD. A
renderer shades the SAMPLED MESH, and on the head grid most of that field does
not survive being sampled.

Measured on this file's own `head_points`, over the face (fy > 0.45):

    tier   face row spacing   face col spacing   lobes with sigma < spacing
    L0          6.8 mm             6.6 mm             17 of 32
    L1         11.0 mm            10.7 mm             **20 of 32**

and the twenty at L1 are not a random twenty. They are **every lobe that
carries a sharp shading step**, and the twelve that survive are **every lobe
that is broad**:

    lobe          sigma_z   its own slope   sigma / grid spacing   realised peak
    lip_line       1.83 mm      56.6 deg          **0.17**            **29.7 %**
    nostril        3.78         47.8              0.31                26.2
    subnasale      3.44         40.3              0.31                --
    philtrum       6.31         14.8              0.32                93.7
    lid_upper      4.82         40.9              0.44                55.4
    nasolabial    14.91          7.4              0.51                86.6
    ---- the survivors ----
    brow_ridge    12.04         19.1              1.10                97.2
    orbit         13.19         26.9              1.20                94.9
    chin          20.07         14.8              1.83                99.3
    cheek         26.38          4.8              2.18                97.5

**THE MOUTH REALISES 29.7 % OF ITS OWN DEPTH AND IS RECONSTRUCTED BY LINEAR
INTERPOLATION ACROSS AN 11 mm CELL.** A 4.59 mm groove at sigma 1.83 mm is a
56.6 deg wall; the same groove sampled at 1.36 mm deep and spread over one cell
is a **7.0 deg ramp** -- m = 1.10 instead of 8.9. The eyelid crease goes the
same way, and so do the nostril, the subnasale and the philtrum.

**AND IT IS THE SAME TWELVE SURVIVORS THAT THE FIFTH PASS'S OWN FRAMES SHOW.**
Its finding was *"the face reads in PROFILE as silhouette, not front-on as
shade"*: brow, nose, chin, cheek and orbit are exactly the broad lobes, and
broad lobes are what a silhouette is made of. The sharp ones -- the lip line,
the lid crease, the nasolabial, the alar crease -- are what a FRONTAL face is
made of, and none of them reaches the mesh. That is why turning the tint off
changed 0.05 % of pixels (the masks are sub-grid too), why turning the relief
off left an egg (the survivors ARE the head shape), and why adding shader
contrast cannot help: **there is no geometry there to shade.**

The realised fraction has a standard deviation of **0.000 across 40 bodies**,
because `th` and `ph` are fixed linspaces and the lobe centres are in
unit-sphere coordinates. This is not sampling noise that averages out over a
crowd. Every person in the grandstand has the same 30 % of a mouth.

**TWO FIXES, AND THEY ARE THE SAME FIX AT TWO SCALES.**

`FACE_GRID_WARP` puts the samples where the features are. The head grid spends
its rows and columns uniformly over a sphere, so the occiput -- which is smooth
-- gets the same density as the mouth. A monotone reparameterisation
concentrates both on the face; it costs no vertices and changes no silhouette.

`FACE_LOBE_FLOOR` stops a lobe being narrower than the mesh it is built on. Any
sigma below one grid cell is floored to it, AT UNCHANGED DEPTH, so the feature
arrives as the steepest thing the grid can carry instead of as a fraction of
itself. This is section 00.3's welt argument in the geometry: *"a colour edge
inside a quad is a soft edge; the welt is the line the eye reads."* The floor
is TIER-DEPENDENT by construction, which is what a LOD is for -- L0 is seen at
400 px and gets a fine mouth, L1 is seen at 63 px and gets the mouth its own
mesh can represent.

Both default to 1.0 and both are gains, so `0.0` on either is the control that
rebuilds the shipped face. `human_bench --face-warp 0 --face-floor 0`."""


def _warp_param(t, centre, width, gain, periodic=False):
    """Reparameterise [0,1) so samples bunch around `centre`.

    A density `1 + gain * exp(-((t-c)/w)^2)` is integrated to a CDF and
    inverted, which is monotone by construction -- so no sample can cross
    another and no quad can invert, which a naive `t + a sin(...)` warp can do
    for large `a`. `periodic` wraps the distance, so the azimuth stays a circle.
    """
    if gain <= 0.0:
        return np.asarray(t, float)
    g = np.linspace(0.0, 1.0, 2049)
    d = np.abs(g - centre)
    if periodic:
        d = np.minimum(d, 1.0 - d)
    dens = 1.0 + float(gain) * np.exp(-(d / float(width)) ** 2)
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]))])
    cdf = cdf / cdf[-1]
    return np.interp(np.asarray(t, float), cdf, g)


def head_points(b, lod, seed, rows=None, cols=None):
    """The head surface as an (S, R, 3) grid in the HEAD BONE's local frame,
    plus the per-vertex zone code and the unit-sphere coordinates.

    Returned rather than emitted so the hair cap can be built from the same
    surface: hair that is offset from the actual skull sits on the skull, and
    hair generated from its own sphere floats or clips, which is what a painted
    cap looks like in three dimensions.

    THE GRID IS NOT UNIFORM AND THAT IS THE POINT -- see `FACE_GRID_WARP`.
    """
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    V = int(rows or lod.head_v)
    R = int(cols or lod.head_u)
    zc, ax, ay, az = 0.16 * hh, 0.5 * hw, 0.5 * hd, 0.50 * hh
    yc = -0.06 * hd

    # `th` runs crown (0) to chin (pi); the face occupies about 0.34..0.86 of
    # it, centred on the nose. `ph` runs from the occiput and reaches the face
    # at parameter 0.5, by construction of the -pi/2 offset below.
    tv = np.linspace(0.0, math.pi, V + 2)[1:-1] / math.pi
    tu = np.linspace(0.0, 1.0, R, endpoint=False)
    th = math.pi * _warp_param(tv, 0.60, 0.26, 1.45 * FACE_GRID_WARP)
    ph = TAU * _warp_param(tu, 0.50, 0.19, 1.70 * FACE_GRID_WARP,
                           periodic=True) - math.pi / 2.0   # col 0 = occiput
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    fx = np.sin(TH) * np.cos(PH - math.pi / 2.0) * 0.0 + np.sin(TH) * np.sin(PH - math.pi / 2.0) * 0.0
    # unit-sphere direction with fy = +1 straight ahead
    fx = np.sin(TH) * np.cos(PH)
    fy = np.sin(TH) * np.sin(PH)
    fz = np.cos(TH)

    # --- SHAPE stage: a head is not an ellipsoid ---------------------------
    sex_f = (b.sex == "F")
    child = 1.0 if b.age_band == "child" else 0.0
    lower = np.clip(-fz, 0.0, 1.0)                       # 0 at the equator, 1 low
    # jaw taper: the mandible is narrower than the cranium, and much more so on
    # a female or a child skull
    taper = 1.0 - (0.22 + 0.05 * sex_f - 0.04 * child) * lower ** 1.75
    gx = fx * taper
    gy = fy * (1.0 - 0.14 * lower ** 1.6)
    gz = fz
    # the face is a PLANE, not a sphere: flatten everything in front of fy 0.55
    over = np.clip(fy - 0.50, 0.0, None)
    gy = gy - 0.20 * over ** 1.7
    # cranial vault narrows toward the crown
    up = np.clip(fz, 0.0, 1.0)
    gx = gx * (1.0 - 0.055 * up ** 2.4)
    # the back of the head is fuller than the front
    gy = gy - 0.06 * np.clip(-fy, 0.0, 1.0) ** 2

    P = np.stack([gx * ax, yc + gy * ay, zc + gz * az], axis=-1)

    # --- LOBE stage --------------------------------------------------------
    # normals of the (already warped) surface, from the grid itself
    N = _grid_normals(P, closed_u=True)
    zone = np.zeros(P.shape[:2])
    rr = rng_for(seed, 91)
    brow_k = (0.42 if sex_f else 1.0) * (0.35 if child else 1.0)
    jaw_k = (0.55 if sex_f else 1.0) * (0.4 if child else 1.0)
    nose_k = (0.86 if sex_f else 1.0) * (0.62 if child else 1.0)
    lip_k = (1.22 if sex_f else 1.0)
    chin_k = (0.70 if sex_f else 1.0)
    age_k = float(np.clip((b.age_years - 25.0) / 55.0, 0.0, 1.4))
    keyk = {"brow": brow_k, "jaw": jaw_k, "nose": nose_k, "lip": lip_k,
            "chin": chin_k}
    disp = np.zeros(P.shape[:2])
    soft = {"hk_lip": np.zeros(P.shape[:2]), "hk_brow": np.zeros(P.shape[:2]),
            "hk_dark": np.zeros(P.shape[:2])}
    # --- THE LOBE FLOOR. See `FACE_LOBE_FLOOR`. The grid's OWN spacing on the
    # face, measured off the shaped surface rather than assumed, converted back
    # into the unit-sphere units the lobe table is written in. Measured here so
    # it follows the tier, the warp and the body -- a constant would be the
    # frequency trap in a third costume.
    face_m = fy > 0.45
    if face_m.sum() >= 8:
        d_v = float(np.median(np.linalg.norm(P[1:] - P[:-1], axis=-1)
                              [face_m[1:] & face_m[:-1]]))
        d_u = float(np.median(np.linalg.norm(np.roll(P, -1, axis=1) - P,
                                             axis=-1)[face_m]))
    else:                                                  # pragma: no cover
        d_v = d_u = 0.011
    # a Gaussian of sigma = one cell is about the sharpest thing a grid can
    # reconstruct; 1.15 buys a little margin against the phase of the samples
    floor_z = FACE_LOBE_FLOOR * 1.15 * d_v / max(az, 1e-6)
    floor_x = FACE_LOBE_FLOOR * 1.15 * d_u / max(ax, 1e-6)
    floor_y = FACE_LOBE_FLOOR * 1.15 * d_v / max(ay, 1e-6)
    for (nm, cx, cy, cz2, sx, sy, sz, amp, key) in HEAD_LOBES:
        k = keyk.get(key, 1.0)
        if nm.startswith("nasolabial"):
            k = 0.35 + age_k
        jit = 1.0 + rr.clipn(0.16, 0.42)
        # WIDENED AT UNCHANGED DEPTH, only where the mesh could not hold it.
        # Widening at unchanged depth REDUCES the analytic slope and RAISES the
        # realised one, because what arrives stops being a fraction of the
        # lobe -- the lip line goes from a 56.6 deg wall that realises 30 % of
        # 4.59 mm to a 14-27 deg wall that realises all of it. The steepness
        # the grid loses was never in the render.
        sx = max(sx, floor_x)
        sy = max(sy, floor_y)
        sz = max(sz, floor_z)
        g = np.exp(-0.5 * (((fx - cx) / sx) ** 2 + ((fy - cy) / sy) ** 2
                           + ((fz - cz2) / sz) ** 2))
        # FACE_RELIEF is the geometry half of the defect-1 ladder. It gains the
        # LOBES only -- the grain noise below is deliberately left alone, so a
        # `FACE_RELIEF = 0` frame is a head with skin texture and no features
        # rather than a polished egg, which is the comparison that separates
        # "the features are not there" from "the features are not lit".
        disp = disp + (FACE_RELIEF * amp * k * jit * hh) * g
        z = ZONE_KEY.get(key)
        if z is not None:
            zone = np.where(g > 0.45, z, zone)
        # CONTINUOUS masks, accumulated from the same Gaussians, so the tint
        # fades exactly as the anatomy does instead of stepping on a grid edge
        if key == "lip":
            soft["hk_lip"] = np.maximum(soft["hk_lip"], g)
        elif key == "brow" or nm.startswith("lid_upper"):
            soft["hk_brow"] = np.maximum(soft["hk_brow"], g)
        elif nm.startswith("orbit") or nm.startswith("nasolabial") \
                or nm in ("mentolabial", "nasal_root", "subnasale"):
            soft["hk_dark"] = np.maximum(soft["hk_dark"], g)
    # skin grain: small, but a perfectly smooth head is the measured defect
    disp = disp + (0.0022 * hh) * wrap_noise(seed + 7, ((PH + math.pi / 2.0)
                                                        / TAU) % 1.0,
                                             TH / math.pi, 7.0, 5.0, oct=4)
    P = P + N * disp[..., None]
    # the scalp zone, for the hairline
    zone = np.where((fz > 0.25) | ((fy < -0.1) & (fz > -0.15)), ZONE_SCALP, zone)
    return P, zone, (fx, fy, fz), (TH, PH), soft


def _grid_normals(P, closed_u=True):
    """Per-vertex normals of an (S,R,3) grid, by central differences."""
    du = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    dv = np.empty_like(P)
    dv[1:-1] = P[2:] - P[:-2]
    dv[0] = P[1] - P[0]
    dv[-1] = P[-1] - P[-2]
    N = np.cross(dv, du)
    n = np.linalg.norm(N, axis=-1, keepdims=True)
    return N / np.maximum(n, 1e-12)


def build_head(mesh, sk, b, lod, seed, covered=False):
    """Head, ears and eyes, emitted into `mesh` in WORLD space.

    `covered` is for a figure in a helmet or balaclava: the face lobes are still
    built (the covering deforms over them) but the eyes and the hair are not.
    """
    O = sk.origin["head"]
    B = sk.basis["head"]
    P, zone, (fx, fy, fz), (TH, PH), soft = head_points(b, lod, seed)
    W = O + np.einsum("ij,srj->sri", B, P)
    vertex = O + B @ np.array([0.0, -0.06 * b.head_d, 0.66 * b.head_h])
    chin = O + B @ np.array([0.0, -0.06 * b.head_d, -0.34 * b.head_h])
    emit_grid(mesh, W, MAT_SKIN, closed_u=True, cap_lo=vertex, cap_hi=chin,
              zone=zone.ravel(), uu=(PH / TAU).ravel(), vv=(TH / math.pi).ravel(),
              extra={k: v.ravel() for k, v in soft.items()})
    if lod.ears:
        for sgn in (-1.0, +1.0):
            build_ear(mesh, O, B, b, lod, seed, sgn)
    if lod.eyes and not covered:
        for sgn in (-1.0, +1.0):
            build_eye(mesh, O, B, b, lod, seed, sgn, surf=P)
    return {"vertex": vertex, "chin": chin}


def build_ear(mesh, O, B, b, lod, seed, sgn):
    """A real ear: helix rim, concha bowl, lobe, set back and out from the skull.

    At 767 px an ear is 27 px and it is the single most reliable silhouette cue
    that a head is a head. `spectator_seated`'s own comment records its ears
    falling between two samples and rendering as horns -- this one is a separate
    shell attached to the skull, not a displacement of it, so it cannot alias.
    """
    hh, hw = b.head_h, b.head_w
    n = 14 if lod.ears >= 2 else 9
    m = 9 if lod.ears >= 2 else 6
    t = np.linspace(0.0, 1.0, m)
    a = np.linspace(0.0, TAU, n, endpoint=False)
    T, A = np.meshgrid(t, a, indexing="ij")
    # An adult ear is ~62 mm tall on a ~228 mm head: 0.27 head-heights, so the
    # half-height is 0.135. The first build used 0.230 and produced a 105 mm ear
    # -- which in a clay render reads as a handle, and is exactly the class of
    # error only looking at the picture finds.
    ry = 0.086 * hh * (1.0 + 0.10 * np.cos(A))
    rz = 0.150 * hh
    ey = ry * np.cos(A) * (1.0 - 0.22 * np.clip(-np.sin(A), 0, 1))
    ez = rz * np.sin(A) * (1.0 + 0.10 * np.clip(np.sin(A), 0, 1))
    # T sweeps from the skull attachment (0) out to the helix rim (1). Row 0
    # must be NEARLY A POINT or the ear is an annulus with a hole through it.
    scale = 0.12 + 0.88 * T
    bulge = np.sin(math.pi * np.clip(T, 0, 1)) ** 0.8
    ex = sgn * (0.5 * hw * 0.80 + 0.030 * hh * bulge)
    # concha: a bowl pressed into the middle of the ear
    conc = np.exp(-0.5 * ((ey / (0.040 * hh)) ** 2 + ((ez + 0.02 * hh)
                                                      / (0.050 * hh)) ** 2))
    ex = ex - sgn * 0.030 * hh * conc * T
    # helix: the rim rolls over
    rim = np.clip((T - 0.72) / 0.28, 0.0, 1.0)
    scale = scale * (1.0 - 0.08 * rim)
    P = np.stack([ex, -0.045 * b.head_d + ey * scale,
                  0.085 * hh + ez * scale], axis=-1)
    W = O + np.einsum("ij,srj->sri", B, P)
    tip = O + B @ np.array([sgn * (0.5 * hw * 0.86), -0.10 * b.head_d,
                            -0.02 * hh])
    emit_grid(mesh, W, MAT_SKIN, closed_u=True, cap_lo=tip,
              zone=ZONE_SKIN, flip=(sgn < 0))


def build_eye(mesh, O, B, b, lod, seed, sgn, surf):
    """The visible CAP of an eyeball, set flush into the orbit.

    A FULL SPHERE IS WRONG HERE and the first build proved it in one render:
    placed at the depth the anatomy wants, a whole sphere pokes out through the
    lids at the sides and the figure has two googly eyes stuck on its face. Only
    the aperture is ever seen, so only the aperture is built -- a 70 deg cap,
    closed with a rim fan, sitting at the socket floor. The iris and pupil are
    placed by the SHADER from `hk_u`/`hk_v` on this cap, so a dark pupil costs no
    geometry at all, and at 11 px the dark pupil IS the read.
    """
    hh, hw = b.head_h, b.head_w
    r = 0.047 * hh
    ex, ez = sgn * 0.200 * hw, 0.140 * hh
    # WHERE THE SOCKET ACTUALLY IS, MEASURED off the built head rather than
    # predicted from the lobe table. Predicting it put the eyeball 12.3 mm
    # BEHIND the skin -- an invisible eye -- because the lid lobes push the
    # surface forward by more than the orbit lobe pushes it back, and no amount
    # of reading the table would have told me that. The apex is then set 1 mm
    # proud of the aperture so the sclera catches the light the lids do not.
    Q = surf.reshape(-1, 3)
    Q = Q[Q[:, 1] > 0.02 * hh]          # THE FRONT of the head only: an (x, z)
    d = np.hypot(Q[:, 0] - ex, Q[:, 2] - ez)   # projection matches the occiput
    k = np.argsort(d)[:8]                      # just as well as the face
    y_surf = float(np.mean(Q[k, 1]))
    ctr = np.array([ex, y_surf + 0.0006 - r * 1.07, ez])
    n, m = 14, 6
    ph = np.linspace(0.0, TAU, n, endpoint=False)
    al = np.linspace(0.06, 1.22, m)              # polar angle from +Y
    AL, PH = np.meshgrid(al, ph, indexing="ij")
    d = np.stack([np.sin(AL) * np.cos(PH), np.cos(AL),
                  np.sin(AL) * np.sin(PH)], axis=-1)
    rr = r * (1.0 + 0.07 * np.clip((0.55 - AL) / 0.55, 0.0, 1.0) ** 1.4)
    P = ctr + d * rr[..., None]
    W = O + np.einsum("ij,srj->sri", B, P)
    apex = O + B @ (ctr + np.array([0.0, r * 1.07, 0.0]))
    rim = O + B @ (ctr - np.array([0.0, r * 0.30, 0.0]))
    emit_grid(mesh, W, MAT_EYE, closed_u=True, cap_lo=apex, cap_hi=rim,
              zone=ZONE_EYE, uu=(PH / TAU).ravel(), vv=(AL / 1.22).ravel())


# ===========================================================================
# 7.  HANDS -- separated, posed fingers that grip what they hold
# ===========================================================================
#
# Defect 6: "hands are stumps. No fingers. Nothing reads as a mannequin faster."
#
# FINGER_SPEC is (fraction of hand length, lateral position, base radius factor,
# splay). Phalanx lengths are the usual 0.42 / 0.32 / 0.26 split. A grip is
# solved, not authored: given a grip radius the phalanges wrap a circle, so a
# hand on a flag pole, a bottle or a camera body closes on the actual object.

FINGER_SPEC = (        # name        len    lateral  radius  splay_deg
    ("index",  0.410, -0.300, 1.00, -5.0),
    ("middle", 0.455, -0.100, 1.02, -1.0),
    ("ring",   0.425, +0.105, 0.95, +3.0),
    ("little", 0.335, +0.300, 0.82, +8.0),
)
PHALANX = (0.42, 0.32, 0.26)


def build_hand(mesh, sk, side, b, lod, seed, grip=0.15, grip_r=None,
               mat=MAT_SKIN, thick=0.0):
    """Palm plus five fingers, in world space. `grip` 0 = open, 1 = closed fist.

    `grip_r` (metres) solves the curl against a real object instead: each
    phalanx is placed on a circle of that radius, advancing by 2 asin(l / 2R),
    which is what makes a hand on a 22 mm flag pole and a hand on a 90 mm bottle
    different hands rather than the same hand at two scales.
    """
    hl = b.hand_len
    O = sk.origin["hand_" + side]
    B = sk.basis["hand_" + side]
    sgn = +1.0 if side == "R" else -1.0
    rr = rng_for(seed, 55 + (0 if side == "R" else 1))
    pw = 0.44 * hl * (1.0 + 0.10 * (b.girth - 1.0))          # palm width
    pt = 0.155 * hl * (1.0 + 0.14 * (b.girth - 1.0))          # palm thickness
    pl = 0.545 * hl                                           # palm length
    ring = max(8, lod.ring - 8)

    # --- the palm: a rounded slab that thickens at the thenar eminence ----
    S = 6
    tt = np.linspace(0.0, 1.0, S)
    th = ring_theta(ring)
    wid = pw * np.interp(tt, [0, 0.25, 0.7, 1.0], [0.80, 0.96, 1.02, 1.00])
    thk = pt * np.interp(tt, [0, 0.3, 0.75, 1.0], [1.06, 1.00, 0.92, 0.86])
    c, s_ = np.cos(th), np.sin(th)
    n = 3.1
    k = (np.abs(c) ** n + np.abs(s_) ** n) ** (-1.0 / n)
    LX = (wid[:, None] * 0.5) * (k * c)[None, :]
    LY = (thk[:, None] * 0.5) * (k * s_)[None, :]
    # thenar (thumb) mass on the radial side, hypothenar on the ulnar
    LY = LY - (0.28 * pt) * np.exp(-0.5 * ((tt - 0.35) / 0.30) ** 2)[:, None] \
        * np.exp(-0.5 * (((th - (math.pi * 1.5 + sgn * 0.9) + math.pi) % TAU
                          - math.pi) / 0.85) ** 2)[None, :]
    C = np.stack([O + B @ np.array([0.0, 0.0, pl * u]) for u in tt])
    BB = np.repeat(B[None, :, :], S, axis=0)
    palm = Sweep(C, BB, LX, LY)
    if thick > 0.0:
        palm = palm.offset(thick)
    palm.emit(mesh, mat, cap_start=True, zone=ZONE_PALM)

    # --- fingers ----------------------------------------------------------
    groups = _finger_groups(lod.fingers)
    for gi, grp in enumerate(groups):
        flen = float(np.mean([FINGER_SPEC[i][1] for i in grp])) * hl
        lat = float(np.mean([FINGER_SPEC[i][2] for i in grp]))
        frad = float(np.mean([FINGER_SPEC[i][3] for i in grp])) * 0.055 * hl \
            * (1.0 + 0.16 * (b.girth - 1.0))
        splay = float(np.mean([FINGER_SPEC[i][4] for i in grp]))
        wide = len(grp) > 1
        base = O + B @ np.array([sgn * lat * pw, -0.10 * pt, pl])
        curl = grip + 0.10 * rr.u()
        _finger(mesh, base, B, flen, frad * (1.9 if wide else 1.0),
                curl, grip_r, splay * sgn, ring, lod, mat, thick,
                rr, flat=wide)
    # --- thumb ------------------------------------------------------------
    tbase = O + B @ np.array([sgn * 0.46 * pw, -0.16 * pt, 0.30 * pl])
    tb = B @ _euler(-18.0, sgn * -46.0, sgn * 26.0)
    _finger(mesh, tbase, tb, 0.36 * hl, 0.066 * hl * (1.0 + 0.16 * (b.girth - 1.0)),
            0.35 + 0.5 * grip, None, 0.0, ring, lod, mat, thick, rr,
            phal=(0.52, 0.48), flat=False)


def _finger_groups(nf):
    if nf >= 5:
        return [(0,), (1,), (2,), (3,)]
    if nf == 3:
        return [(0, 1), (2, 3)]
    if nf == 2:
        return [(0, 1, 2, 3)]
    return [(0, 1, 2, 3)]


def _finger(mesh, base, B, length, rad, curl, grip_r, splay, ring, lod, mat,
            thick, rr, phal=PHALANX, flat=False):
    """One finger (or a fused pair) as a chain of tapered phalanges.

    When `grip_r` is given the curl is SOLVED against that radius: each bone
    subtends 2 asin(l / 2R) on the circle, so the finger lies on the object
    instead of near it. Otherwise `curl` drives the usual 55/75/55 deg fist.
    """
    segs = max(2, min(len(phal), 3 if lod.fingers >= 3 else 2))
    ph = np.array(phal[:segs], float)
    ph = ph / ph.sum()
    ang = np.array([55.0, 75.0, 55.0])[:segs] * float(np.clip(curl, 0.0, 1.2))
    if grip_r:
        for i in range(segs):
            l = float(length * ph[i])
            ang[i] = math.degrees(2.0 * math.asin(
                min(0.999, l / (2.0 * max(grip_r + rad, l * 0.51)))))
    pts = [np.asarray(base, float)]
    Bc = B @ _euler(0.0, splay, 0.0)
    for i in range(segs):
        Bc = Bc @ _euler(ang[i] + rr.clipn(4.0, 9.0), 0.0, 0.0)
        pts.append(pts[-1] + Bc @ np.array([0.0, 0.0, length * ph[i]]))
    pts = np.array(pts)
    t = np.array([0.0, 0.16, 0.34, 0.40, 0.62, 0.68, 0.86, 1.00])
    r = rad * np.array([1.08, 0.98, 1.06, 0.94, 1.03, 0.92, 0.95, 0.62])
    if segs == 2:
        t = np.array([0.0, 0.25, 0.50, 0.58, 0.85, 1.0])
        r = rad * np.array([1.08, 0.96, 1.06, 0.93, 0.95, 0.66])
    asp = np.full_like(t, 1.10 if not flat else 0.55)
    S = max(6, 2 * lod.station + 2)
    sw = _tube_impl(pts, t, r, ring, int(rr.u() * 1e6), asp, 2.4,
                    smooth_r=rad * 0.85, noise_amp=0.03, noise_su=2.0,
                    noise_sv=6.0, twist=0.0, n_st=S)
    if thick > 0.0:
        sw = sw.offset(thick)
    sw.emit(mesh, mat, cap_end=True, zone=ZONE_SKIN)
    if lod.nails and not flat:
        _nail(mesh, sw, rad, mat)


def _nail(mesh, sw, rad, mat):
    """A nail plate on the back of the last phalanx. 40 triangles, and it is
    what stops a fingertip reading as the end of a pipe."""
    s0 = int(sw.S * 0.80)
    s1 = sw.S - 1
    if s1 - s0 < 2:
        return
    R = sw.R
    j0 = int(round(R * 0.25))
    span = max(3, int(round(R * 0.20)))
    cols = [(j0 + k - span // 2) % R for k in range(span)]
    V = sw.verts()
    nm = sw.normals2d()
    P = np.empty((s1 - s0 + 1, span, 3))
    for i, s in enumerate(range(s0, s1 + 1)):
        for j, cidx in enumerate(cols):
            d = 0.10 * rad * (1.0 - abs(j - (span - 1) / 2.0) / (span / 2.0))
            P[i, j] = V[s, cidx] + (sw.B[s] @ np.array(
                [nm[s, cidx, 0], nm[s, cidx, 1], 0.0])) * d
    emit_grid(mesh, P, mat, closed_u=False, zone=ZONE_NAIL)


# ===========================================================================
# 8.  FEET AND FOOTWEAR -- actual shoes with soles
# ===========================================================================

def build_shoe(mesh, sk, side, b, lod, seed, style, mats):
    """A shoe with an upper, a midsole, an outsole lip and a heel.

    Returns the world z of the LOWEST sole point, which is what `ground_contact`
    needs to put weight on the floor rather than near it. Defect 10 is contact
    not being solved; solving it means measuring the sole, not the ankle.
    """
    O = sk.origin["foot_" + side]
    B = sk.basis["foot_" + side]
    fl = b.foot_len
    fw = 0.385 * fl * (1.0 + 0.10 * (b.girth - 1.0))
    sole_t = style.get("sole", 0.026) * fl / 0.26
    toe_spring = style.get("toe_spring", 0.075) * fl
    collar = style.get("collar", 0.34)          # top of the upper, x foot length
    ring = max(10, lod.ring - 6)
    S = max(9, 2 * lod.station + 5)
    t = np.linspace(0.0, 1.0, S)

    # HEIGHTS ARE MEASURED FROM THE FLOOR, not from the ankle joint. The first
    # version measured them from the bone origin and every shoe floated
    # 18.5 mm -- which `ground_contact` would then have "solved" by dropping the
    # whole figure 18.5 mm into the concrete. The ankle joint stands
    # `b.ankle_h` above the floor by definition, so the floor is at local
    # -ankle_h and everything else is built up from there.
    floor = -b.ankle_h
    lift = toe_spring * np.clip((t - 0.70) / 0.30, 0.0, 1.0) ** 2 \
        + 0.35 * toe_spring * np.clip((0.10 - t) / 0.10, 0.0, 1.0) ** 2
    sole_bot = floor + lift
    top_h = fl * np.interp(t, [0.0, 0.08, 0.26, 0.45, 0.62, 0.82, 1.0],
                           [collar * 0.86, collar, collar * 0.97, collar * 0.80,
                            collar * 0.60, collar * 0.40, collar * 0.20])
    upper_top = sole_bot + top_h
    wid = fw * np.interp(t, [0.0, 0.10, 0.28, 0.55, 0.74, 0.90, 1.0],
                         [0.60, 0.76, 0.78, 0.98, 1.00, 0.86, 0.44])

    th = ring_theta(ring)
    c, s_ = np.cos(th), np.sin(th)
    n = 3.4
    k = (np.abs(c) ** n + np.abs(s_) ** n) ** (-1.0 / n)
    zc = 0.5 * (sole_bot + upper_top)
    hz = 0.5 * (upper_top - sole_bot)
    LX = (wid[:, None] * 0.5) * (k * c)[None, :]
    LZ = zc[:, None] + hz[:, None] * np.clip(k * s_, -1.0, 1.0)[None, :]
    # flatten the underside onto the sole plane -- a shoe does not have a round
    # bottom, and a round bottom renders as a 1 px bright line under every figure
    LZ = np.maximum(LZ, sole_bot[:, None])
    # instep swell over the arch, and the vamp's own creases
    LZ = LZ + (0.035 * fl) * np.exp(-0.5 * ((t - 0.42) / 0.15) ** 2)[:, None] \
        * np.clip(s_, 0, 1)[None, :] ** 1.5
    LZ = LZ + (0.0075 * fl) * np.sin(t[:, None] * 34.0 + 1.1) \
        * np.exp(-0.5 * ((t[:, None] - 0.60) / 0.15) ** 2) \
        * np.clip(s_, 0, 1)[None, :] ** 2

    C = np.stack([O + B @ np.array([0.0, 0.0, fl * u]) for u in t])
    BB = np.repeat(B[None, :, :], S, axis=0)
    # the foot bone's local frame is X across, Y DOWN, Z along the sole, so the
    # ring's local y is the NEGATIVE of a height
    upper = Sweep(C, BB, LX, -LZ)
    upper.emit(mesh, mats["shoe"], cap_start=True, cap_end=True, zone=0.0)

    # --- the sole: a separate shell so it can be a different material -----
    sole_top = sole_bot + sole_t
    LZ2 = np.minimum(LZ, sole_top[:, None])
    LX2 = LX * 1.05                       # the outsole stands proud: a welt line
    sole = Sweep(C, BB, LX2, -LZ2)
    sole.emit(mesh, mats["sole"], cap_start=True, cap_end=True, zone=0.0)
    if lod.shoe_detail >= 1:
        _sole_tread(mesh, C, BB, LX2, sole_bot, t, fl, mats["sole"], seed)
    if lod.shoe_detail >= 2:
        _laces(mesh, O, B, fl, fw, t, top_h, sole_bot, mats["shoe"], seed, style)

    W = np.concatenate([upper.verts().reshape(-1, 3),
                        sole.verts().reshape(-1, 3)])
    return float(W[:, 2].min())


def _sole_tread(mesh, C, BB, LX, base_z, t, fl, mat, seed):
    """Transverse tread bars on the visible SIDE of the sole.

    Deliberately on the side wall and not the underside: the underside is never
    seen, and the check that decides these items measures a lip and a shadow
    along a raking light on the surfaces that ARE seen.
    """
    nb = 11
    for i in range(nb):
        u = 0.10 + 0.80 * i / (nb - 1.0)
        j = int(np.clip(np.searchsorted(t, u), 1, len(t) - 1))
        for sgn in (-1.0, +1.0):
            w = float(np.abs(LX[j]).max()) * sgn
            z0 = float(base_z[j]) + 0.004
            z1 = float(base_z[j]) + 0.014
            y = float(C[j][1])
            _ = y
            c0 = C[j] + BB[j] @ np.array([w, -z0, -0.006 * fl])
            c1 = C[j] + BB[j] @ np.array([w, -z0, +0.006 * fl])
            c2 = C[j] + BB[j] @ np.array([w, -z1, +0.006 * fl])
            c3 = C[j] + BB[j] @ np.array([w, -z1, -0.006 * fl])
            out = BB[j] @ np.array([sgn * 0.0022, 0.0, 0.0])
            V = np.array([c0, c1, c2, c3, c0 + out, c1 + out, c2 + out, c3 + out])
            q = np.array([[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1],
                          [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]])
            if sgn < 0:
                q = q[:, ::-1]
            mesh.add(V, quads=q, mat=mat)


def _laces(mesh, O, B, fl, fw, t, top_h, sole_bot, mat, seed, style):
    """Four crossed laces over the vamp. ~600 triangles, and at 767 px they are
    the difference between a shoe and a moulded clog."""
    rr = rng_for(seed, 77)
    npair = 4
    for i in range(npair):
        u = 0.40 + 0.095 * i
        h = float(np.interp(u, t, sole_bot + top_h * 0.82))
        for sgn in (-1.0, +1.0):
            a = O + B @ np.array([sgn * 0.26 * fw, -h, u * fl])
            c = O + B @ np.array([-sgn * 0.26 * fw, -h, (u + 0.075) * fl])
            mid = 0.5 * (a + c) + B @ np.array([0.0, -0.010 * fl, 0.0])
            pts = np.array([a, mid, c])
            r = np.array([0.0075 * fl] * 3) * (1.0 + 0.2 * rr.u())
            sw = _tube_impl(pts, np.array([0.0, 0.5, 1.0]), r, 6,
                            int(rr.u() * 1e6), 0.55, 2.0,
                            smooth_r=0.01 * fl, noise_amp=0.0, noise_su=1,
                            noise_sv=1, twist=0.0, n_st=7)
            sw.emit(mesh, mat, cap_start=True, cap_end=True)


# ===========================================================================
# 9.  EMIT -- one Mesh becomes ONE Blender object
# ===========================================================================
#
# ONE OBJECT PER FIGURE, deliberately. `tools/item_gate.py:994 pick_subject`
# frames the MEDIAN-TRIANGLE object of a population, so a figure split into
# eleven objects would put the gate's camera on a shoe and report on the person.
# It also means an instanced crowd instances a whole human, not eleven parts.

def purge_factory_scene():
    """Remove Blender's factory Cube, Camera and 1000 W point Light.

    `--factory-startup` ships all three and no item module was removing them,
    so every figure test blend has carried a 2 m white cube at the WORLD ORIGIN,
    a spare camera (which `rq`'s worker PREWARMS, ~4 s each -- a blend with 19
    cameras once destroyed a healthy instance), and a 1000 W point lamp that is
    not the contract sun.

    On the paddock item the contamination was arithmetically negligible -- the
    figures sit 65 m from the origin, where that lamp delivers 0.019 W/m^2
    against the sun's 115.754, i.e. 0.016 % -- so nothing already judged needs
    re-judging on those grounds. It was NOT negligible on the first bench
    render, where the figures were at the origin: the cube occluded the middle
    figure and the lamp lit all five. Same defect, and whether it mattered was
    an accident of where the item happened to be placed.
    """
    if not HAVE_BPY:
        return []
    gone = []
    for ob in list(bpy.data.objects):
        if ob.name in ("Cube", "Camera", "Light") and not ob.users_collection[0]\
                .name.startswith("W_"):
            gone.append((ob.name, ob.type))
            bpy.data.objects.remove(ob, do_unlink=True)
    return gone


def emit_mesh(name, mesh, coll_, materials, smooth_deg=38.0):
    """Emit into Blender. Returns the object, recentred per itemkit's Law 6."""
    if not HAVE_BPY:
        raise RuntimeError("emit_mesh needs Blender")
    V, Q, T, QM, TM, A = mesh.finish()
    if not len(V):
        raise ValueError("emit_mesh: %s has no geometry" % name)
    me, off = K.new_mesh(name, V, quads=Q, tris=T, smooth_deg=smooth_deg)
    for m in materials:
        me.materials.append(m)
    if len(Q) + len(T):
        mi = np.concatenate([QM, TM]).astype(np.int32)
        mi = np.clip(mi, 0, max(len(materials) - 1, 0))
        me.polygons.foreach_set("material_index", mi)
    A = dict(A)
    col = A.pop("hk_col", None)
    K.bake_attributes(me, A)
    if col is not None and len(col):
        # A FLOAT_COLOR point attribute, not three floats: this is what carries
        # every per-figure colour, so ONE material set serves the whole
        # population instead of nine material datablocks per person.
        at = me.attributes.get("hk_col") or me.attributes.new(
            "hk_col", "FLOAT_COLOR", "POINT")
        rgba = np.concatenate([np.asarray(col, np.float32),
                               np.ones((len(col), 1), np.float32)], axis=1)
        at.data.foreach_set("color", rgba.ravel())
    ob = bpy.data.objects.new(name, me)
    ob.location = off
    coll_.objects.link(ob)
    return ob


# ===========================================================================
# 10.  POSE -- a library big enough that nothing repeats visibly in 600 figures
# ===========================================================================
#
# Defect 2: "roughly six poses across ~600 figures. The 'arms crossed in an X on
# the lap' pose repeats dozens of times, visibly."
#
# The answer is NOT a longer table. A table of 30 poses across 600 figures still
# shows each pose 20 times. An archetype here is a MEAN and a per-joint spread,
# so the realised pose is drawn from a continuous distribution around it and no
# two figures share one. `measure_pose_spread()` measures what that is actually
# worth: nearest-neighbour distance in joint-angle space over the whole
# population, against the same statistic computed for a 6-pose table.
#
# Angles are degrees, in the joint's own rest frame, and every one of them is
# clamped into `JOINT_LIMITS` afterwards, so an archetype cannot dislocate a
# shoulder however wide its spread.

def _P(kind, weight, **joints):
    return {"kind": kind, "weight": weight, "j": joints}


POSE_SD = {                     # per-joint spread, degrees, x/y/z
    "lumbar": (5.0, 3.5, 5.0), "thorax": (3.5, 3.0, 4.5),
    "neck": (6.0, 4.5, 7.0), "head": (3.5, 3.0, 4.5),
    "clav": (2.5, 3.0, 2.5), "arm": (8.0, 7.0, 8.0), "fore": (9.0, 0.0, 8.0),
    "hand": (7.0, 6.0, 4.0), "hip": (5.5, 4.0, 4.5), "knee": (7.0, 0.0, 2.0),
    "foot": (4.5, 3.0, 3.5),
}

POSES = {
    # ---- standing ------------------------------------------------------
    "stand_relaxed": _P("stand", 1.00,
                        arm=(4, -7, 3), fore=(11, 0, 6), hand=(-6, 0, 0),
                        hip=(-2, 1, 0), knee=(-6, 0, 0), lumbar=(2, 0, 0)),
    "stand_weight_side": _P("stand", 0.95,
                            arm=(3, -8, 2), fore=(9, 0, 5), hip=(-3, 3, 0),
                            knee=(-13, 0, 0), lumbar=(1, -5, 2),
                            thorax=(0, 4, -2)),
    "arms_folded": _P("stand", 0.72,
                      arm=(24, -22, 34), fore=(112, 0, 42), hand=(-14, 18, 0),
                      lumbar=(4, 0, 0), knee=(-5, 0, 0)),
    "hands_on_hips": _P("stand", 0.42,
                        arm=(-6, -46, 46), fore=(88, 0, 26), hand=(-20, 0, 0),
                        thorax=(-3, 0, 0), knee=(-6, 0, 0)),
    "hands_pockets": _P("stand", 0.55,
                        arm=(-9, -12, 8), fore=(30, 0, 16), hand=(-24, 8, 0),
                        lumbar=(4, 0, 0), knee=(-7, 0, 0)),
    "hands_behind_back": _P("stand", 0.30,
                            arm=(-24, -9, -6), fore=(62, 0, -30),
                            hand=(-12, 0, 0), thorax=(-4, 0, 0)),
    "clasped_front": _P("stand", 0.38,
                        arm=(16, -12, 14), fore=(78, 0, 30), hand=(-16, 0, 0),
                        lumbar=(3, 0, 0), knee=(-5, 0, 0)),
    "talking_turned": _P("stand", 0.85,
                         arm=(20, -16, 16), fore=(74, 0, 24), hand=(-10, 12, 0),
                         thorax=(0, 0, 17), lumbar=(1, 0, 9),
                         neck=(-4, 0, 21), head=(0, 0, 8), knee=(-7, 0, 0)),
    "pointing": _P("stand", 0.22,
                   arm=(66, -20, 10), fore=(22, 0, 8), hand=(-4, 0, 0),
                   thorax=(0, 0, 8), neck=(-6, 0, 10)),
    "phone_to_ear": _P("stand", 0.34,
                       arm=(28, -30, 62), fore=(126, 0, 44), hand=(-22, 0, 0),
                       neck=(2, 6, 12), lumbar=(3, 0, 0), knee=(-6, 0, 0)),
    "phone_held_up": _P("stand", 0.44,
                        arm=(58, -18, 22), fore=(84, 0, 24), hand=(-14, 0, 0),
                        neck=(-10, 0, 0), thorax=(-3, 0, 0)),
    "clipboard": _P("stand", 0.26,
                    arm=(12, -14, 22), fore=(96, 0, 28), hand=(-24, 0, 0),
                    neck=(16, 0, 0), thorax=(4, 0, 0)),
    "radio_talk": _P("stand", 0.24,
                     arm=(34, -26, 54), fore=(118, 0, 40), hand=(-18, 6, 0),
                     neck=(0, 0, 9), lumbar=(2, 0, 0)),
    "carry_bag": _P("stand", 0.30,
                    arm=(2, -5, 0), fore=(7, 0, 3), hand=(-4, 0, 0),
                    clav=(0, 0, -6), thorax=(0, 5, 0), lumbar=(2, -4, 0),
                    knee=(-6, 0, 0)),
    "lean_on_rail": _P("stand", 0.36,
                       arm=(40, -20, 16), fore=(38, 0, 12), hand=(-18, 0, 0),
                       lumbar=(16, 0, 0), thorax=(7, 0, 0), neck=(-14, 0, 0),
                       hip=(12, 2, 0), knee=(-11, 0, 0)),
    "adjust_cap": _P("stand", 0.16,
                     arm=(74, -28, 50), fore=(128, 0, 30), hand=(-26, 0, 0),
                     neck=(-6, 0, 0)),
    "watching_up": _P("stand", 0.40,
                      arm=(3, -8, 3), fore=(13, 0, 6), neck=(-24, 0, 0),
                      head=(-8, 0, 0), thorax=(-4, 0, 0), knee=(-6, 0, 0)),
    "walk_stride": _P("walk", 0.62,
                      arm=(-22, -8, 2), fore=(26, 0, 6), hip=(26, 2, 0),
                      knee=(-9, 0, 0), foot=(-6, 0, 0), lumbar=(2, 0, 4)),
    "walk_contact": _P("walk", 0.55,
                       arm=(-14, -8, 2), fore=(20, 0, 6), hip=(14, 2, 0),
                       knee=(-26, 0, 0), foot=(4, 0, 0), lumbar=(3, 0, 3)),
    "arms_akimbo_watch": _P("stand", 0.30,
                            arm=(-4, -40, 40), fore=(80, 0, 24),
                            hand=(-18, 0, 0), neck=(-8, 0, 14), knee=(-6, 0, 0)),
    # ---- seated --------------------------------------------------------
    "sit_upright": _P("sit", 0.90,
                      hip=(84, 5, 0), knee=(-86, 0, 0), foot=(4, 0, 0),
                      arm=(6, -7, 4), fore=(30, 0, 10), lumbar=(4, 0, 0)),
    "sit_forward": _P("sit", 0.80,
                      hip=(96, 6, 0), knee=(-92, 0, 0), foot=(8, 0, 0),
                      arm=(38, -14, 12), fore=(88, 0, 20), lumbar=(22, 0, 0),
                      thorax=(10, 0, 0), neck=(-10, 0, 0)),
    "sit_back_folded": _P("sit", 0.62,
                          hip=(78, 8, 0), knee=(-72, 0, 0), foot=(-2, 0, 0),
                          arm=(22, -22, 34), fore=(114, 0, 42),
                          lumbar=(-10, 0, 0), thorax=(-6, 0, 0)),
    "sit_arms_spread": _P("sit", 0.42,
                          hip=(76, 9, 0), knee=(-70, 0, 0),
                          arm=(-26, -52, 8), fore=(52, 0, 12),
                          lumbar=(-12, 0, 0), thorax=(-5, 0, 0)),
    "sit_legs_crossed": _P("sit", 0.40,
                           hip=(80, -14, 22), knee=(-92, 0, 0),
                           arm=(10, -9, 6), fore=(46, 0, 14), lumbar=(2, 0, 5)),
    "sit_phone": _P("sit", 0.50,
                    hip=(88, 5, 0), knee=(-88, 0, 0),
                    arm=(30, -12, 14), fore=(96, 0, 26), neck=(22, 0, 4),
                    lumbar=(12, 0, 0), thorax=(6, 0, 0)),
    "sit_cheer": _P("sit", 0.30,
                    hip=(80, 7, 0), knee=(-80, 0, 0),
                    arm=(146, -18, 12), fore=(24, 0, 6), neck=(-16, 0, 0),
                    thorax=(-6, 0, 0)),
    "sit_turn_neighbour": _P("sit", 0.55,
                             hip=(82, 6, 0), knee=(-84, 0, 0),
                             arm=(14, -10, 8), fore=(56, 0, 18),
                             thorax=(0, 0, 21), lumbar=(2, 0, 11),
                             neck=(-2, 0, 24), head=(0, 0, 9)),
    "sit_hands_lap": _P("sit", 0.70,
                        hip=(84, 5, 0), knee=(-86, 0, 0),
                        arm=(12, -10, 12), fore=(70, 0, 26), hand=(-16, 0, 0),
                        lumbar=(6, 0, 0)),
    "sit_elbow_knee": _P("sit", 0.45,
                         hip=(94, 8, 0), knee=(-94, 0, 0),
                         arm=(46, -16, 18), fore=(104, 0, 26),
                         lumbar=(20, 0, 0), thorax=(8, 0, 0), neck=(-6, 0, 8)),
    "sit_slouch": _P("sit", 0.50,
                     hip=(66, 10, 0), knee=(-58, 0, 0), foot=(-8, 0, 0),
                     arm=(4, -8, 4), fore=(26, 0, 8), lumbar=(-16, 0, 0),
                     thorax=(-9, 0, 0), neck=(14, 0, 0)),
}
POSE_NAMES = tuple(sorted(POSES))
_LIMB_KEY = {"arm": "arm", "fore": "fore", "hand": "hand", "hip": "hip",
             "knee": "knee", "foot": "foot", "clav": "clav"}


def sample_pose(rng, body, archetype=None, kind=None, gaze=None,
                asym=1.0):
    """One realised pose. Continuous, per-joint, mirrored, clamped.

    THE TWO SIDES MOVE INDEPENDENTLY. `spectator_seated`'s jitter dict does this
    too and it is the single cheapest thing that stops a crowd reading as a row
    of dolls: a symmetric figure is a mannequin even when its pose is unusual.
    """
    if archetype is None:
        cands = [(k, v["weight"]) for k, v in POSES.items()
                 if kind is None or v["kind"] == kind]
        archetype = _pick_weighted(rng.u(), cands)
    A = POSES[archetype]
    mirror = rng.u() < 0.5
    pose = {}
    for j, key in (("lumbar", "lumbar"), ("thorax", "thorax"),
                   ("neck", "neck"), ("head", "head")):
        m = A["j"].get(key, (0.0, 0.0, 0.0))
        sd = POSE_SD[key]
        s = -1.0 if mirror else 1.0
        pose[j] = (m[0] + rng.n(0, sd[0]) * asym,
                   s * m[1] + rng.n(0, sd[1]) * asym,
                   s * m[2] + rng.n(0, sd[2]) * asym)
    for base in ("clav", "arm", "fore", "hand", "hip", "knee", "foot"):
        m = A["j"].get(base, (0.0, 0.0, 0.0))
        sd = POSE_SD[base]
        for side in ("L", "R"):
            # sign of the y (abduction) and z (axial) axes flips between sides
            sg = +1.0 if side == "R" else -1.0
            if mirror:
                sg = -sg
            pose[base + "_" + side] = (
                m[0] + rng.n(0, sd[0]) * asym,
                sg * m[1] + rng.n(0, sd[1]) * asym,
                sg * m[2] + rng.n(0, sd[2]) * asym)
    # an individual's own standing habit, applied on top of any archetype
    pose["lumbar"] = tuple(np.add(pose["lumbar"],
                                  (rng.n(0, 3.0), rng.n(0, 2.0), rng.n(0, 2.5))))
    if gaze is not None:
        pose = apply_gaze(pose, gaze)
    return archetype, clamp_pose(pose)


def apply_gaze(pose, gaze):
    """Point the head at something. `gaze` = (yaw_deg, pitch_deg) in the
    figure's own frame, split between neck and head the way a real neck does.

    Defect 9: "no attention -- nobody is looking at anything in particular. In a
    real grandstand almost every head is turned toward the same moving object."
    """
    yaw, pitch = float(gaze[0]), float(gaze[1])
    p = dict(pose)
    n = list(p.get("neck", (0.0, 0.0, 0.0)))
    h = list(p.get("head", (0.0, 0.0, 0.0)))
    n[2] += 0.68 * yaw
    h[2] += 0.32 * yaw
    n[0] += 0.72 * pitch
    h[0] += 0.28 * pitch
    p["neck"] = tuple(n)
    p["head"] = tuple(h)
    return p


def gaze_to(sk_or_pos, target, facing_deg=0.0):
    """(yaw, pitch) degrees to look at a world point from the head's position."""
    if hasattr(sk_or_pos, "origin"):
        p = sk_or_pos.origin["head"]
    else:
        p = np.asarray(sk_or_pos, float)
    d = np.asarray(target, float) - p
    yaw = math.degrees(math.atan2(-d[0], d[1])) - facing_deg
    yaw = (yaw + 180.0) % 360.0 - 180.0
    pitch = -math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    return (float(np.clip(yaw, -95.0, 95.0)), float(np.clip(pitch, -45.0, 45.0)))


def pose_vector(pose):
    """A flat vector of every joint angle, for measuring how far apart poses are."""
    keys = sorted(pose)
    return np.array([v for k in keys for v in pose[k]], float)


# ===========================================================================
# 11.  CLOTHING -- geometry shells with fit, folds, collars, cuffs, hems, seams
# ===========================================================================
#
# Defect 4: "clothing is flat colour fill -- no folds, collars, cuffs, hems,
# seams; no shoe geometry. Shirts are a solid RGB value."
#
# HOW THE BUDGET IS SPLIT BETWEEN MESH AND SHADER, and why -- this is the one
# decision in the file that a reader should be able to check:
#
#   The gate measures band-passed contrast at r1-r2 px and a lip-and-shadow
#   dipole at 4-16 px lags. At `paddock_personnel_figure`'s 10 m / 35 mm that is
#   373 px/m, so r1 peaks on an 8 mm feature and r2 on a 16 mm one, and the
#   relief lags span 11-43 mm. It also measures a SILHOUETTE wander of >= 5 mm.
#
#   Silhouette wander is a GEOMETRY problem and nothing else can produce it, so
#   the fold field is real mesh at 25-120 mm wavelength and 4-12 mm amplitude.
#   Representing an 8 mm crumple in mesh would need 3 mm edges: 78,000 quads on
#   the torso alone, for a feature that only ever changes the SHADING. So the
#   8-16 mm band is carried by a bump in the fabric shader, which perturbs the
#   normal and therefore does make a real sunward lip and lee shadow -- the
#   R2-021 ladder shows PAINT scoring as flat (0.169 against a flat plate's
#   0.142) while 0.5 mm of actual relief scores 0.361, and a bump is relief in
#   the shading integral, not paint.
#   Seams, hems, cuffs, plackets and waistbands ARE mesh, because they are
#   one-dimensional and cost almost nothing: a 2 mm welt along a seam line is
#   the strongest dipole on the whole garment.

TOPS = {
    #  name:           sleeve  hem   ease   collar     stiff  fold_lam  weight M/F
    "tee":            dict(sleeve=0.22, hem=0.16, ease=0.013, collar="crew",
                           stiff=0.55, lam=0.085, w=(0.26, 0.20)),
    "polo":           dict(sleeve=0.26, hem=0.14, ease=0.012, collar="polo",
                           stiff=0.70, lam=0.080, w=(0.18, 0.10)),
    "buttoned_shirt": dict(sleeve=0.94, hem=0.10, ease=0.018, collar="shirt",
                           stiff=0.85, lam=0.095, w=(0.14, 0.10)),
    "shirt_rolled":   dict(sleeve=0.55, hem=0.11, ease=0.018, collar="shirt",
                           stiff=0.85, lam=0.095, w=(0.08, 0.06)),
    "longsleeve":     dict(sleeve=0.92, hem=0.15, ease=0.015, collar="crew",
                           stiff=0.58, lam=0.088, w=(0.09, 0.10)),
    "sweatshirt":     dict(sleeve=0.95, hem=0.12, ease=0.024, collar="crew",
                           stiff=0.40, lam=0.115, w=(0.10, 0.12)),
    "hoodie":         dict(sleeve=0.95, hem=0.11, ease=0.029, collar="hood",
                           stiff=0.38, lam=0.125, w=(0.09, 0.13)),
    "softshell":      dict(sleeve=0.96, hem=0.09, ease=0.033, collar="stand",
                           stiff=1.00, lam=0.100, w=(0.10, 0.09)),
    "gilet":          dict(sleeve=0.02, hem=0.10, ease=0.036, collar="stand",
                           stiff=0.95, lam=0.105, w=(0.05, 0.03)),
    "team_jersey":    dict(sleeve=0.30, hem=0.14, ease=0.016, collar="polo",
                           stiff=0.62, lam=0.082, w=(0.09, 0.05)),
    "blouse":         dict(sleeve=0.42, hem=0.13, ease=0.020, collar="shirt",
                           stiff=0.50, lam=0.090, w=(0.00, 0.12)),
}
BOTTOMS = {
    "jeans":     dict(leg=0.99, rise=0.34, ease=0.013, stiff=0.95, lam=0.105,
                      cuff=0.030, w=(0.30, 0.30)),
    "chinos":    dict(leg=0.97, rise=0.33, ease=0.015, stiff=0.72, lam=0.100,
                      cuff=0.026, w=(0.20, 0.14)),
    "cargo":     dict(leg=0.98, rise=0.35, ease=0.021, stiff=0.80, lam=0.110,
                      cuff=0.030, w=(0.11, 0.05)),
    "shorts":    dict(leg=0.46, rise=0.33, ease=0.019, stiff=0.70, lam=0.095,
                      cuff=0.024, w=(0.16, 0.12)),
    "track":     dict(leg=0.98, rise=0.32, ease=0.024, stiff=0.42, lam=0.120,
                      cuff=0.034, w=(0.11, 0.10)),
    "tech_trou": dict(leg=0.99, rise=0.34, ease=0.019, stiff=0.88, lam=0.105,
                      cuff=0.028, w=(0.12, 0.09)),
    "skirt":     dict(leg=0.00, rise=0.34, ease=0.035, stiff=0.45, lam=0.130,
                      cuff=0.000, w=(0.00, 0.20)),
}
HEADWEAR = {"none": 0.58, "cap": 0.30, "beanie": 0.06, "bucket": 0.03,
            "visor": 0.03}


def wrap_noise(seed, u, v, su, sv, oct=4):
    """Noise on a cylinder: periodic in u by construction.

    A plain fbm in u has a discontinuity at u = 0, which on a garment is a
    visible seam running the full height of the figure at whatever azimuth the
    parameterisation happened to start at. The blend below costs one extra
    evaluation and removes it: f(u) = a(u)(1-u) + a(u-1)u, which satisfies
    f(0) = f(1) exactly.
    """
    u = np.asarray(u, float)
    a = surface_noise(seed, u, v, su, sv, oct=oct)
    b = surface_noise(seed, u - 1.0, v, su, sv, oct=oct)
    return a * (1.0 - u) + b * u


FOLD_MODE = "cloth"
"""`"isotropic"` is the superseded fold language, kept as the POSITIVE CONTROL
for `folds_are_sparse_and_oriented`. See `_fold_cloth`."""

# The three families, as (target radiance modulation, wavelength in metres).
# Read at call time so the bench can sweep them.
FOLD_DRAPE_M = (0.40, 0.42)
FOLD_CREASE_M = (1.55, 0.130)
FOLD_CRUMPLE_M = (0.18, 0.060)
FOLD_ACTIVE = 0.32
"""The fraction of the garment a crease is allowed to touch. THE WHOLE POINT:
the superseded field spent m = 0.93 uniformly over every square millimetre of
every garment, which is neither smooth cloth nor a fold, and at 767 px it
rendered as plaster. Cloth is smooth over most of a panel and 15-25 deg in a
few narrow lines."""


def _quantile_gate(g, active, soft=0.55):
    """A 0..1 gate that is ON over exactly `active` of the samples.

    Thresholding a noise at a fixed VALUE makes the active fraction a property
    of the noise's realised histogram, which is not the same on two garments;
    thresholding at a QUANTILE makes it a stated number that the selftest can
    check on the artefact.
    """
    g = np.asarray(g, float)
    hi = float(np.quantile(g, 1.0 - active * (1.0 - 0.5 * soft)))
    lo = float(np.quantile(g, 1.0 - active * (1.0 + 0.5 * soft)))
    w = np.clip((g - lo) / max(hi - lo, 1e-9), 0.0, 1.0)
    return w * w * (3.0 - 2.0 * w)


def _ridge_field(seed, u, vn, su, sv, oct=3):
    """A ridged noise: 1 on the source noise's zero set, 0 away from it.

    `1 - |n|` concentrates the range of a noise into NARROW LINES, which is
    what a crease is. An fbm of the same amplitude spreads the same range over
    the whole surface, which is what stucco is. The two are indistinguishable
    in a variance statistic and completely different in a picture.
    """
    n = wrap_noise(seed, u, vn, su, sv, oct=oct)
    s = float(np.percentile(np.abs(n), 92.0))
    r = 1.0 - np.clip(np.abs(n) / max(s, 1e-9), 0.0, 1.0)
    return r


def _fold_cloth(seed, u, vn, spec, flex, drape, circ_m, span_m, lam, stiff):
    """The fold language, rebuilt after LOOKING at the B5/C3 bench at 767 px.

    WHAT THE PICTURE SHOWED. The white overall's outline is a clean analytic
    curve from shoulder to wrist and from hip to ankle -- not one fold breaks
    it anywhere -- while its SURFACE carries a uniform granular crust at about
    20 px. That is the signature of an isotropic field: all of the fold budget
    spent as texture and none of it as form. The superseded field is exactly
    that, two fbm octave-sets at m = 0.93 and 0.54 with a total of 4.9 mm
    peak-to-peak, and no term anywhere longer than 140 mm.

    Real cloth spends its budget the other way round. Three families:

      DRAPE    panel scale, 420 mm, 5.9 mm p-p -- 2.5 deg of slope, so it is
               invisible AS SHADING and is worth 2.6 px of silhouette wander at
               the crew tier's 438 px/m. This is the term that stops the shell
               being a parallel surface of the body.
      CREASE   the sparse one. A RIDGED noise (narrow lines, not a field),
               strongly elongated along the body -- hanging cloth flutes
               vertically -- gated so it touches FOLD_ACTIVE of the surface,
               and steep where it acts: 1.55 modulation at 130 mm, which the
               ridging roughly doubles in the valley itself. Everywhere else
               the garment is left alone.
      CRUMPLE  what is left of the old isotropic term, cut from m = 0.54 to
               0.18 -- enough that a panel is not glass, far under what reads
               as texture.

    plus the two SITED families, which are where a real garment's most
    recognisable creases actually are and which no noise will ever put in the
    right place:

      FLEX     transverse compression at a bent joint (already here).
      STACK    the trouser breaking over the boot and the sleeve stacking at
               the cuff -- a short train of transverse creases in the last
               ~12 % of the run, which is the single most recognisable cloth
               event on a standing figure and was entirely absent.

    THE MESH IS THE CEILING AND IT IS WHY THE CREASE IS AT 130 mm. A garment
    ring carries `lod.ring` columns -- 26 at L0, i.e. 40 mm on a 1 m torso --
    so a feature needs ~3 columns to survive. Asking for a 40 mm crease in
    geometry produces aliasing; that band belongs to the shader.
    """
    m_d, lam_d = FOLD_DRAPE_M
    m_c, lam_c = FOLD_CREASE_M
    m_x, lam_x = FOLD_CRUMPLE_M
    soft = 1.0 / max(0.35, stiff)             # a soft cloth folds more
    # --- drape: long both ways ------------------------------------------
    a_d = amp_mm_for_modulation(m_d * drape, lam_d) * 1e-3
    su = float(np.clip(fbm_scale(lam_d / max(circ_m, 0.05), 3), 1.2, 26.0))
    sv = float(np.clip(fbm_scale(lam_d / max(span_m, 0.05), 3), 1.0, 14.0))
    d = a_d * wrap_noise(seed + 1, u, vn, su, sv, oct=3)
    # --- crease: narrow lines, elongated ALONG the body, gated -----------
    a_c = amp_mm_for_modulation(m_c * soft * drape, lam_c) * 1e-3
    su_c = float(np.clip(fbm_scale(lam_c / max(circ_m, 0.05), 3), 2.0, 26.0))
    sv_c = float(np.clip(fbm_scale(lam_c * 3.6 / max(span_m, 0.05), 3),
                         1.0, 14.0))
    ridge = _ridge_field(seed + 5, u, vn, su_c, sv_c, oct=3)
    gate = _quantile_gate(wrap_noise(seed + 6, u, vn,
                                     max(su_c * 0.30, 1.2),
                                     max(sv_c * 0.55, 1.0), oct=2),
                          FOLD_ACTIVE)
    cre = ridge * gate
    d = d - a_c * (cre - float(cre.mean()))
    # --- crumple: the isotropic remainder, small on purpose --------------
    a_x = amp_mm_for_modulation(m_x, lam_x) * 1e-3
    su_x = float(np.clip(fbm_scale(lam_x / max(circ_m, 0.05), 4), 3.0, 26.0))
    sv_x = float(np.clip(fbm_scale(lam_x / max(span_m, 0.05), 4), 2.0, 14.0))
    d = d + a_x * wrap_noise(seed + 2, u, vn, su_x, sv_x, oct=4)
    # --- flex: transverse creases where a joint is genuinely bent --------
    if flex is not None:
        f = np.clip(np.asarray(flex, float) / 90.0, 0.0, 1.6)
        ph = wrap_noise(seed + 3, u, vn, 2.2, 3.0, oct=2)
        lam_fl = 0.045 * (0.9 + 0.7 * stiff)
        creases = np.sin(vn * (2.0 * math.pi * span_m / lam_fl) + 2.2 * ph)
        d = d + (0.0075 * f) * creases * (0.7 + 0.5 * stiff)
    # --- stack: the break over the boot / the cuff -----------------------
    # A trouser leg is cut longer than the leg and the surplus PILES UP on the
    # shoe. Nothing in a noise field puts a crease there, and it is the first
    # thing a viewer reads as cloth on a standing figure.
    lam_s = 0.055 * (0.85 + 0.5 * stiff)
    env = np.exp(-0.5 * ((1.0 - vn) / 0.075) ** 2)
    if env.max() > 1e-3:
        phs = wrap_noise(seed + 7, u, vn, 3.0, 1.2, oct=2)
        a_s = amp_mm_for_modulation(1.9 * soft, lam_s) * 1e-3
        d = d + a_s * env * np.sin(
            (1.0 - vn) * (2.0 * math.pi * span_m / lam_s) + 3.0 * phs)
    return d


def fold_field(seed, u, v, spec, flex=None, drape=1.0,
               circ_m=1.0, span_m=0.8):
    """The garment's fold language, in METRES of radial displacement.

    Three superposed families, and the amplitudes are chosen against the gate's
    silhouette bar (>= 5 mm RMS after a local quadratic is refitted in each
    100-row window), not against taste:

      HANG    long flutes 60-140 mm apart that a hanging cloth makes under its
              own weight. Amplitude scales with looseness.
      CRUMPLE general 25-60 mm creasing from wear and movement.
      FLEX    transverse compression creases, concentrated where a joint is
              actually bent -- a straight arm has none, a 110 deg elbow has a
              stack. `flex` is the local flexion in degrees.

    THE FREQUENCIES ARE PHYSICAL. `u` is one full turn and `v` one full run of
    the sweep, so a wavelength in metres has to be converted with the garment's
    OWN circumference and span. The first version treated them as if u and v
    were metres and put three lobes around a one-metre torso -- a 330 mm fold
    where the spec said 95 mm. It rendered SMOOTH, which is exactly how a
    frequency error hides from every check that reads the code.
    """
    lam = float(spec.get("lam", 0.10))
    stiff = float(np.clip(spec.get("stiff", 0.7), 0.15, 1.2))
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    vr = float(v.max() - v.min()) if v.size else 1.0
    vn = (v - v.min()) / max(vr, 1e-9)                  # 0..1 along the sweep
    # EMITTED wavelengths, via the measured fbm response -- see `fbm_scale`.
    # The previous form was `circ_m / lam`, which is the `1/lambda` idiom, and
    # it emitted 2.59x coarser than it declared: a 100 mm flute came out at
    # 259 mm and was then largely absorbed by the local quadratic that
    # item_gate check 8 refits every 100 rows.
    #
    # THE CEILING IS THE MESH, NOT THE MODEL, and that is why it stays at 26.
    # A garment ring carries `lod.ring` points -- 26 at L0 -- so the finest fold
    # the geometry can represent around the body is about one per 2.6 points,
    # i.e. 10 per turn, i.e. ~96 mm on a 1 m torso. Asking for finer does not
    # produce finer folds, it produces aliasing, and finer than that is the
    # SHADER's job: `fabric_material` covers 1.3 mm to 120 mm.
    su_h = float(np.clip(fbm_scale(max(lam, 0.02) / circ_m, 3), 3.0, 26.0))
    sv_h = float(np.clip(fbm_scale(max(lam * 3.2, 0.03) / span_m, 3), 1.5, 14.0))
    if FOLD_MODE == "cloth":
        return _fold_cloth(seed, u, vn, spec, flex, drape, circ_m, span_m,
                           lam, stiff) * FOLD_GAIN
    hang = wrap_noise(seed + 1, u, vn, su_h, sv_h, oct=3)
    crum = wrap_noise(seed + 2, u, vn, min(su_h * 1.9, 26.0),
                      min(sv_h * 2.6, 14.0), oct=4)
    # AMPLITUDES SET AGAINST THE SUN, exactly as `fabric_stages` now is -- see
    # `slope_for_modulation`. This is the SAME error one layer down, and after
    # the shader was corrected it became the dominant one: 8.2 mm of radial
    # displacement at a 100 mm flute is a 14.4 deg surface, which under the
    # contract sun's 12.47 deg elevation modulates the rendered radiance by
    # 2 tan(14.4) / tan(12.47) = 2.32 peak-to-peak. That is what makes the
    # coveralls in the crew bench render read as carved foam even with the
    # shader's own crumple down at 0.28. Geometry folds should carry MORE than
    # the shader, because they are the real folds -- but ~0.9, not 2.3.
    a_hang = amp_mm_for_modulation(0.90 * drape / stiff,
                                   max(lam, 0.02)) * 1e-3
    a_crum = amp_mm_for_modulation(0.60 * drape / (0.6 + 0.5 * stiff),
                                   max(lam, 0.02) / 1.9) * 1e-3
    d = a_hang * hang + a_crum * crum
    if flex is not None:
        f = np.clip(np.asarray(flex, float) / 90.0, 0.0, 1.6)
        ph = wrap_noise(seed + 3, u, vn, 2.2, 3.0, oct=2)
        lam_c = 0.045 * (0.9 + 0.7 * stiff)             # 50-75 mm, physical
        creases = np.sin(vn * (2.0 * math.pi * span_m / lam_c) + 2.2 * ph)
        d = d + (0.0075 * f) * creases * (0.7 + 0.5 * stiff)
    return d * FOLD_GAIN


def _flex_along(sk, chain, t):
    """Local flexion in degrees at parameter t along a two-bone chain."""
    a = sk.dirn(chain[0])
    b = sk.dirn(chain[1])
    ang = math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))
    return ang * np.exp(-0.5 * ((np.asarray(t, float) - 0.50) / 0.13) ** 2)


CLOTH_BRIDGE_M = 0.017
"""The Gaussian width, in metres of surface distance, at which a garment stops
following the body. See `Sweep.relaxed`: it attenuates a 50 mm feature to 0.10
and passes a 250 mm one at 0.91."""

CLOTH_ROLL_M = 0.80
"""The radius of the ball rolled along the outside of the garment's radial
profile -- the tightest EXTERNAL curvature a panel of this cloth will take.
See `Sweep._bridge`. It bridges a hollow of width W down to W^2/8R of its
depth.

THE VALUE IS A MEASUREMENT AND SO IS THE DISAPPOINTMENT. The physically
tempting radius -- the tightest curvature a Nomex panel will take, ~0.2 m --
does essentially nothing on a real body, because anatomical hollows along a
limb are extremely WIDE AND SHALLOW: the elbow dip is 2.4 mm deep over 130 mm,
which needs R = W^2/8d = 0.88 m before a ball will bridge it at all, and the
waist is 22 mm over 290 mm, which needs 0.48 m. Measured on the torso, the
lift of the shell is 0.26 mm mean at R = 0.26, 0.70 at 0.50, 2.48 at 0.80 and
4.93 at 1.20, while the waist indent falls 21.9 -> 20.6 -> 19.8 -> 16.6 ->
11.9 mm. 0.80 m is the largest radius that still leaves three quarters of the
waist, and it is worth +9.3 mm of p95 clearance on the trunk, +2.2 on the leg
and +0.2 on the SLEEVE -- i.e. on an arm this operator does nothing at any
radius, and the sleeve's departure from the body has to come from the fold
field instead. That is the honest size of this lever."""

GARMENT_RELAX = "cloth"
"""The default `relax` for every garment shell. A module global, read at CALL
time, so a bench can render the ladder without threading a keyword through six
call sites -- and so a superseded stage stays reachable as a control."""

FOLD_GAIN = 1.0
"""Gain on the GEOMETRY fold field. `0.0` is the control that answers "who owns
the granular crust in the render, the mesh or the shader?" -- a question no
amount of reading either can settle. See `fold_field`."""

FACE_RELIEF = 1.0
FACE_TINT = 1.0
"""THE FACE LADDER -- defect 1, "the face is a blank egg".

`render/items/spectator_crowd/HANDS.png` shows a 180 px head with no eye
socket, no brow shadow and no mouth. HUMAN-REFERENCE sec 0000.5 calls that
"geometry at essentially zero contrast" and names the skin shader's zone
channels as the suspect. **Both halves of that were measured before either was
believed, and the geometry half is FALSE:**

    HEAD_LOBES alone, grain noise excluded, on the face (fy > 0.45)
      L1   displacement -4.5 .. +35.9 mm      slope RMS 14.07 deg   m = 2.22
      L0   displacement -5.7 .. +40.0 mm      slope RMS 14.52 deg   m = 2.29

`m = 2 theta / tan(12.47 deg)` is sec 0.5's radiance modulation under this
film's own sun, and 2.2 is HIGHER than the fold field's 0.9 target. The face is
not flat. The attributes are not missing either -- `hk_lip`, `hk_brow` and
`hk_dark` reach 0.95, 0.97 and 1.00 on the finished mesh.

What IS measurable and small is how much of the face carries them. At L1 the
face is 304 vertices on a 44 x 32 grid, 10.7 mm apart -- 8.4 px at a 180 px
head -- and after the shader's own `maprange` thresholds:

    hk_lip    6 vertices above 0.5   (1.97 % of the face)   <- the mouth
    hk_brow  14                       (4.61 %)
    hk_dark  26                       (8.55 %)

A mouth that is six vertices is two quads, and a colour edge inside a quad is
the soft edge sec 00.3 already had to answer with a geometry welt.

So the cause is NOT settled by any of this, and these two gains exist so it can
be settled by a picture instead of by an argument: `FACE_RELIEF = 0` removes
the lobes' displacement and leaves the tint; `FACE_TINT = 0` removes the tint
and leaves the displacement. Render the four corners. Whichever frame stops
looking like the shipped one is the layer that owns the read -- and if NEITHER
does, the answer is the light, which is where this project's fifth systemic
error lives."""

HAIR_LEGACY = False
"""THE SHIPPED HAIR, KEPT REACHABLE AS THE POSITIVE CONTROL.

`FOLD_MODE = "isotropic"` and `plan_block(legacy_gaze=True)` are the same idea
and are in this repository for the same reason: a control has to REPRODUCE THE
FAULT or it proves nothing. Sixteen times on this project the instrument was
the broken thing, and the specific way it broke most recently was a control
reconstructed from the new code's own residual -- which returned a clean result
for both arms, i.e. could not fail.

`HAIR_LEGACY = True` restores, exactly: the 1.2 mm / 8.0 mm bump pair at m 3.38
and 3.69, the 1.1 mm colour noise, the untangented Anisotropic 0.60, the
0.75 x head_u grid, the isotropic thickness lump with no locks and no parting,
the taper that goes to zero at every azimuth, the lattice-rooted strands and
the 620/190/48 strand counts. Everything the fifth pass's frames were shot
with. It is what `work/hairab/hair_old.blend` is built from, and the pair of
frames is the whole of the hair argument.

It covers the GEOMETRY as well as the shader on purpose: rendering only the new
mesh under the old shader would have said which layer changed, and the question
the frames have to answer is whether the thing a viewer sees is better."""

HAIR_RELIEF = 1.0
HAIR_LUMP = 1.0
HAIR_STRAND_GAIN = 1.0
"""THE HAIR LADDER -- defect 3, "the hair is a granular crust at every distance".

Same instrument as `FOLD_GAIN`/`SHADER_RELIEF` one layer up, and it exists for
the same reason: the crust could be the SHADER's bumps or the MESH's thickness
field or the strand tubes, and no amount of reading the three settles it.

    HAIR_RELIEF        gain on every bump amplitude in `hair_material`
    HAIR_LUMP          gain on the geometric thickness modulation in `build_hair`
    HAIR_STRAND_GAIN   gain on the strand COUNT; 0.0 emits no strand tubes

Read at call time, so `human_bench --hair-relief 0` builds the control.

**WHAT THE ARITHMETIC ALREADY SAYS, before any render.** The shipped hair
shader was never given the discipline `fabric_stages` was given after the crew
bench was rejected as stucco. Its two stages, through this file's own
`max_slope_deg` and `slope_for_modulation`:

    stage                  lambda   amp pp   slope     m = 2 theta / tan(12.47)
    fibre (Wave)           1.20 mm   0.150    21.44 deg     3.384
    clump (Noise d4)       8.00 mm   1.100    23.36 deg     3.688

against `fabric_stages`' own targets of **m 0.21-0.30 fine, 0.28-0.42 mid** and
0.90-1.30 for a stage that is SPARSE. The garment shader that was rejected by
eye as "coarse stucco, a uniform crawl over shirt and trouser alike" was
carrying **m = 1.57**. The hair carries **2.2x that**, isotropically, over the
whole mass.

**AND THE FINE STAGE IS A TENTH OF THE NYQUIST FLOOR.** `fabric_stages` drops
any stage below `2 / px_per_m` -- 5.36 mm at this item's 373.3 px/m -- with the
reason stated in its docstring: *"Cycles does not filter a bump by the pixel
footprint, so a 1.3 mm weave at 373 px/m -- 0.49 px -- does not render as a
fine weave, it renders as per-pixel noise."* The hair's 1.2 mm fibre is 0.53 px
at the 400 px face framing and **0.33 px at the crowd's 63 px head**. It is
per-pixel noise at m = 3.4. That is a granular crust, it is a crust at EVERY
distance because it is pinned to the pixel rather than to the surface, and it
is on every uncovered head -- which is exactly what the frames show.

The colour layer does the same thing: `strand` was a Noise at **1.1 mm**
driving a 0.74-1.28 value multiplier, i.e. sub-pixel COLOUR speckle on top of
the sub-pixel bump.

So the hair now goes through `hair_stages()`, which is `fabric_stages()`'s
discipline applied to hair: wavelengths EMITTED via `tex_scale`, amplitudes set
from a target RADIANCE MODULATION rather than from millimetres, and everything
below the Nyquist floor DROPPED rather than shrunk. What a sub-pixel fibre
actually does to light is give the mass an anisotropic sheen, and that is
where it went -- see `hair_material`."""

CLOTH_ROLL_U_M = 0.0
"""OFF, and the reason is a measurement, not a preference. The same ball run
AROUND the ring operates on radius-versus-COLUMN-INDEX, and the polar radius of
an ellipse has minima at the ends of its minor axis that are not concavities of
the SURFACE at all -- so closing it inflates a perfectly convex cross-section
toward a circle. Measured: on the torso it lifted the p95 clearance 20.7 -> 25.2
mm while the honest v-axis bridge moved it to 21.5, i.e. four fifths of what it
appeared to buy was a parameterisation artefact and would have rendered as a
barrel chest. Doing it properly needs a planar closing of the cross-section
CURVE, and the concavities it would find (the scapular pair, the sub-mammary
shelf) are already spanned by the v-axis pass. Kept reachable, set to zero."""


def relax_spec(relax):
    """(sigma_m, roll_m, roll_u, morph) for a `relax` name, or None for the
    body's own rings. Read at CALL time so a bench can sweep the constants."""
    if relax == "none":
        return None
    if relax == "base":                       # relief-free, nothing else
        return (0.0, 0.0, 0.0, "close")
    if relax == "lowpass":                    # what shipped before the bridge
        return (CLOTH_BRIDGE_M, 0.0, 0.0, "close")
    if relax == "dilate":                     # the control known to inflate
        return (CLOTH_BRIDGE_M, CLOTH_ROLL_M, CLOTH_ROLL_U_M, "dilate")
    if relax == "cloth_v":                    # along the body only
        return (CLOTH_BRIDGE_M, CLOTH_ROLL_M, 0.0, "close")
    if relax == "cloth":
        return (CLOTH_BRIDGE_M, CLOTH_ROLL_M, CLOTH_ROLL_U_M, "close")
    raise ValueError("unknown relax %r" % (relax,))


def garment_from_sweep(sw, t, seed, spec, t0, t1, flex=None, drape=1.0,
                       extra=0.0, relax=None):
    """Offset a body Sweep into a garment shell over the parameter range.

    `relax` selects what the shell is lofted FROM, and every superseded stage
    is kept so each check below has a case it is known to fail:

        "none"     the body's own rings, muscle relief and all -- DEFECT 1,
                   retained as a POSITIVE CONTROL
        "base"     the relief-free rings only
        "lowpass"  relief-free and low-passed at CLOTH_BRIDGE_M -- DEFECT 2,
                   the skin-tight bodysuit, retained as a POSITIVE CONTROL
        "cloth_v"  ... and bridged along the body
        "cloth"    ... and around the ring as well  (default)
        "dilate"   bridged with a plain dilation -- the inflation control
    """
    relax = GARMENT_RELAX if relax is None else relax
    i0 = int(np.searchsorted(t, t0))
    i1 = int(np.searchsorted(t, t1))
    i0 = int(np.clip(i0, 0, len(t) - 3))
    i1 = int(np.clip(max(i1, i0 + 3), i0 + 3, len(t)))
    sub = sw.slice(i0, i1)
    rs = relax_spec(relax)
    if rs is not None:
        sub = sub.relaxed(rs[0], roll_m=rs[1], roll_u=rs[2], morph=rs[3])
    tt = t[i0:i1]
    R = sub.R
    u = np.tile(np.linspace(0.0, 1.0, R, endpoint=False), (len(tt), 1))
    vv = np.repeat(tt[:, None], R, axis=1)
    fl = None if flex is None else np.repeat(
        np.asarray(flex)[i0:i1, None], R, axis=1)
    W = sub.verts()
    circ = float(np.linalg.norm(np.roll(W, -1, axis=1) - W,
                                axis=2).sum(axis=1).mean())
    span = float(np.linalg.norm(np.diff(sub.C, axis=0), axis=1).sum())
    # A HEM IS A FINISHED EDGE. The fold field is a radial displacement of a few
    # millimetres, and applied at full amplitude on the boundary RING it makes
    # the garment's outline wobble by +-8 mm -- 3.5 px at the 767 px framing --
    # so the shirt hem in the bench render reads as torn rather than sewn. Real
    # hems are the stiffest part of a garment: two or three thicknesses of cloth
    # turned and stitched, which is exactly why they hang straight. The window
    # tapers the field to 25 % over the first and last ring and back to full by
    # the third, which costs no vertices and turns a ragged edge into an edge.
    S = len(tt)
    ii = np.arange(S, dtype=float)
    edge = np.minimum(ii, (S - 1) - ii)
    win = (0.25 + 0.75 * np.clip(edge / 2.0, 0.0, 1.0))[:, None]
    d = spec.get("ease", 0.025) + extra + win * fold_field(
        seed, u, vv, spec, fl, drape, circ_m=circ, span_m=max(span, 0.05))
    # AND THE SKIN MUST STAY UNDER THE CLOTH. Lofting from a relaxed base moves
    # the shell INWARD wherever the body bulged, so if the ease no longer covers
    # the worst positive residual the limb pokes through the sleeve -- a defect
    # that would only ever be found by looking, on one figure in fifty. Measured
    # here and the whole shell loosened by whatever it is short, which costs a
    # millimetre of fit and cannot produce a hole.
    if rs is not None:
        raw = sw.slice(i0, i1)
        nm = sub.normals2d()
        nw = np.einsum("sij,srj->sri", sub.B,
                       np.stack([nm[..., 0], nm[..., 1],
                                 np.zeros_like(nm[..., 0])], axis=-1))
        resid = np.einsum("sri,sri->sr", raw.verts() - W, nw)
        short = float(np.max(resid + 0.0015 - d))
        if short > 0.0:
            d = d + short
    return sub.offset(d), tt


def _ridge(sw, tt, u_centre, width_u, height, along="v"):
    """A raised welt along a parameter line: the seam, hem and cuff primitive.

    2 mm of welt is the strongest lip-and-shadow dipole on a garment and costs
    no extra vertices -- it is a displacement of the ones already there. The
    R2-021 physical ladder puts 0.5 mm of rib at dip 0.361 against a flat
    plate's 0.142, so 2 mm is comfortably in the regime the check can see.
    """
    R = sw.R
    u = np.linspace(0.0, 1.0, R, endpoint=False)
    du = np.abs((u - u_centre + 0.5) % 1.0 - 0.5)
    # A WELT NARROWER THAN THE VERTEX SPACING IS NOT A WELT, IT IS A SPIKE.
    # Every caller asked for 0.006-0.010 of a turn; a garment ring carries
    # `lod.ring` points, 26 at L0, so one column is 0.038 of a turn. A Gaussian
    # of sigma 0.006 therefore lands entirely inside ONE column and displaces a
    # single line of vertices by the full height -- which is what the crew bench
    # render shows as a hard 3 mm ledge running the whole length of the overall
    # where the zip should be. Clamped to 0.62 of a column spacing, the welt
    # spans about three columns and reads as a seam.
    width_u = max(float(width_u), 0.62 / float(R))
    prof = np.exp(-0.5 * (du / max(width_u, 1e-4)) ** 2)
    return np.broadcast_to(prof[None, :] * height, (sw.S, R))


def sleeve_head(mesh, slv, sk, side, b, lod, mat, wear=0.0, bulge=0.13,
                toward=None, depth=None):
    """Close a sleeve's armhole with a real SET-IN SLEEVE HEAD.

    THE DEFECT THIS REPLACES, and it was the worst single thing in the 767 px
    peep: `build_top` used `Sweep.extend_start(2, upper_arm * 0.30)` and then
    emitted the sleeve with `cap_start=False`. `extend_start` walks BACKWARDS
    ALONG THE ARM'S OWN AXIS at 86-99 % of full sleeve radius, so on a figure
    with its arms hanging the sleeve's open end travelled ~90 mm STRAIGHT UP
    from the glenohumeral joint -- clear of the trunk shell, whose top ring is
    at the acromion -- and stopped there, open. The render shows two dark
    ellipses on the shoulders that you can see down into. It was never buried;
    it was a chimney.

    A set-in sleeve is not a tube that stops. Its head is a DOME that turns
    inboard off the arm axis and disappears under the shoulder seam, so:

      * the rings turn from the arm axis toward the thorax, not along it;
      * their radius falls as `1 - sin(pi/2 * w)`, so the surface converges;
      * the last ring is closed with a pole fan at a target point INSIDE the
        chest, which is what makes the sleeve a closed shell;
      * a small `bulge` keeps the first third proud of the arm, because a real
        sleeve head is eased into the armscye and stands slightly off the
        deltoid rather than shrink-wrapping it.

    `sleeve_head_protrusion_mm` measures the result against the trunk shell,
    and the old path is available as a positive control (`--sleeve-control`).
    """
    P0 = slv.verts()[0]                                # (R,3) armhole ring
    ctr = P0.mean(axis=0)
    aim = np.asarray(sk.tip("thorax") if toward is None else toward, float)
    inb = aim - ctr
    inb[2] *= 0.35                                     # mostly horizontal
    inb = inb / max(float(np.linalg.norm(inb)), 1e-9)
    depth = max(0.42 * b.shoulder_half, 0.050) if depth is None else float(depth)
    tgt = ctr + inb * depth
    rows = max(3, int(rows_for_head(lod)))
    out = [P0]
    for i in range(1, rows + 1):
        w = i / float(rows + 1)
        s = math.sin(0.5 * math.pi * w)
        k = (1.0 - s) * (1.0 + bulge * math.sin(math.pi * w))
        out.append((ctr + (tgt - ctr) * w)[None, :] + (P0 - ctr[None, :]) * k)
    G = np.stack(out)
    # WINDING IS DECIDED AGAINST THE TUBE IT IS STITCHED TO, not assumed. The
    # dome runs proximally where the sleeve runs distally, so "flip it" is the
    # obvious answer and it is wrong on some poses: `Mesh.orient_outward`'s
    # audit caught one shoulder at -0.056 and the other at +0.151 from the SAME
    # code. So take the sleeve's own outward normal at the armhole ring -- which
    # `Sweep.normals2d` orients away from the ring centroid, and which the
    # figure's own signed volume confirms is correct -- and orient the dome's
    # first quad row to agree with it.
    nm2 = slv.normals2d()[0]                                   # (R,2) local
    B0 = slv.B[0]
    outw = (nm2[:, 0:1] * B0[:, 0][None, :] + nm2[:, 1:2] * B0[:, 1][None, :])
    e_u = np.roll(G[0], -1, axis=0) - G[0]
    e_v = G[1] - G[0]
    n0 = np.cross(e_u, e_v)
    flip = float(np.einsum("rj,rj->r", n0, outw).sum()) < 0.0
    return emit_grid(mesh, G, mat, closed_u=True, cap_hi=tgt, wear=wear,
                     flip=flip,
                     vv=np.repeat(np.linspace(0.0, -0.25, G.shape[0]),
                                  G.shape[1]))


def rows_for_head(lod):
    return max(3, min(6, lod.station + 1))


def open_boundary_loops(m, mat):
    """Every open boundary loop of one material, as (centroid, area_m2, n).

    A boundary edge is an edge used by exactly one face. The loops they form are
    where a shell is OPEN -- a hem, a cuff, a neck opening, and any hole that
    should not be there. Area is Newell's, which is the true planar area for a
    flat loop and a good proxy for a nearly flat one; a sleeve armhole is
    nearly flat by construction.
    """
    V, Q, T, QM, TM, _A = m.finish()
    faces = []
    if len(Q):
        faces += [q for q, mm in zip(Q, QM) if mm == mat]
    if len(T):
        faces += [t for t, mm in zip(T, TM) if mm == mat]
    use = {}
    for f in faces:
        n = len(f)
        for i in range(n):
            a, c = int(f[i]), int(f[(i + 1) % n])
            k = (a, c) if a < c else (c, a)
            use[k] = use.get(k, 0) + 1
    bnd = [k for k, v in use.items() if v == 1]
    if not bnd:
        return []
    adj = {}
    for a, c in bnd:
        adj.setdefault(a, []).append(c)
        adj.setdefault(c, []).append(a)
    seen = set()
    out = []
    for start in adj:
        if start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        P = V[np.asarray(comp, int)]
        ctr = P.mean(axis=0)
        D = P - ctr[None, :]
        # Newell on the fan around the centroid, in the loop's own best plane
        nrm = np.zeros(3)
        for i in range(len(D)):
            nrm = nrm + np.cross(D[i], D[(i + 1) % len(D)])
        out.append((ctr, 0.5 * float(np.linalg.norm(nrm)), len(comp)))
    return out


def _mesh_triangles(m, mats=None):
    """Every face of the mesh as triangles, with the material of each."""
    V, Q, T, QM, TM, _A = m.finish()
    tri, mt = [], []
    if len(Q):
        Q = np.asarray(Q, int)
        tri.append(Q[:, [0, 1, 2]])
        tri.append(Q[:, [0, 2, 3]])
        mt.append(np.asarray(QM, int))
        mt.append(np.asarray(QM, int))
    if len(T):
        tri.append(np.asarray(T, int))
        mt.append(np.asarray(TM, int))
    F = np.concatenate(tri) if tri else np.zeros((0, 3), int)
    M = np.concatenate(mt) if mt else np.zeros((0,), int)
    if mats is not None and len(F):
        keep = np.isin(M, np.asarray(mats, int))
        F, M = F[keep], M[keep]
    return V, F, M


def _first_hit(V, F, org, dirn, chunk=20000):
    """Batched Moller-Trumbore. Returns (t, face_index) of the nearest hit."""
    P0 = V[F[:, 0]]
    E1 = V[F[:, 1]] - P0
    E2 = V[F[:, 2]] - P0
    N = len(org)
    best_t = np.full(N, np.inf)
    best_f = np.full(N, -1, int)
    for a in range(0, len(F), chunk):
        p0 = P0[a:a + chunk]
        e1 = E1[a:a + chunk]
        e2 = E2[a:a + chunk]
        pv = np.cross(dirn[:, None, :], e2[None, :, :])
        det = np.einsum("fj,rfj->rf", e1, pv)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = org[:, None, :] - p0[None, :, :]
        u = np.einsum("rfj,rfj->rf", tv, pv) * inv
        qv = np.cross(tv, e1[None, :, :])
        v = np.einsum("rj,rfj->rf", dirn, qv) * inv
        t = np.einsum("fj,rfj->rf", e2, qv) * inv
        good = ok & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > 1e-6)
        t = np.where(good, t, np.inf)
        j = np.argmin(t, axis=1)
        tt = t[np.arange(N), j]
        upd = tt < best_t
        best_t[upd] = tt[upd]
        best_f[upd] = j[upd] + a
    return best_t, best_f


def headwear_clearance_mm(seed, kind="cap", lod=None, body=None,
                          legacy=False):
    """Vertical clearance between a cap's lowest FORWARD point and the eyes, mm.

    A cap peak is in front of the face and above the eyes. If it is not above
    them it is across them, which is what every capped figure in the first bench
    render had -- the peak root was pinned at z = 0.075 * head_h against eyes at
    0.140 * head_h, so it crossed the brow and its tip hung below the chin.
    Nothing in the module could see it; a 767 px crop showed it immediately.

    Positive is clearance. Negative means the hat is on the face.
    """
    lod = lod or LOD_L0
    b = body or sample_body(rng_for(int(seed), 1), adult_only=True)
    sk = solve_skeleton(b, {})
    m = Mesh()
    build_headwear(m, sk, b, lod, int(seed), kind, MAT_ACC, legacy=legacy)
    V, vm = m.vertex_materials()
    if not len(V):
        return float("inf")
    O = np.asarray(sk.origin["head"], float)
    B = np.asarray(sk.basis["head"], float)
    L = (V - O[None, :]) @ B                       # into the head's own frame
    # IN FRONT OF THE EYES, not merely in front of the head. A cap peak's OUTER
    # CORNERS legitimately dip to brow level at the temples; what must never
    # happen is brim over pupil. The eyes sit at +-0.200 * head_w, so the
    # question is asked over |x| < 0.30 * head_w.
    fwd = (L[:, 1] > 0.30 * b.head_d) & (np.abs(L[:, 0]) < 0.30 * b.head_w)
    if not fwd.any():
        return float("inf")
    eye_z = 0.140 * b.head_h
    return float((L[fwd, 2].min() - eye_z) * 1000.0)


def visible_material_fraction(fig, mat, n_rays=1200, seed=7):
    """Fraction of the figure's VISIBLE surface carried by one material slot.

    The manifest's claim for `crew_figure` is "completely covered -- helmet,
    visor, balaclava, fireproofs, gloves -- **zero exposed skin**", and a claim
    is not a measurement. This casts rays inward from a sphere around the
    figure, takes the first hit, and reports what share of them landed on the
    given slot -- so "zero exposed skin" becomes a number with a control (the
    same bodies built as paddock personnel, who are supposed to show face,
    neck and forearms).
    """
    m = fig["mesh"]
    V, F, M = _mesh_triangles(m)
    if not len(F):
        return 0.0
    lo, hi = V.min(axis=0), V.max(axis=0)
    ctr = 0.5 * (lo + hi)
    rad = float(np.linalg.norm(hi - lo)) * 0.75 + 0.3
    rr = rng_for(int(seed), 613)
    u = np.array([rr.u() for _ in range(n_rays)])
    v = np.array([rr.u() for _ in range(n_rays)])
    z = 2.0 * u - 1.0
    ph = TAU * v
    s = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    D = np.stack([s * np.cos(ph), s * np.sin(ph), z], axis=1)
    a = np.stack([np.array([rr.u() for _ in range(n_rays)])
                  for _ in range(3)], axis=1)
    aim = ctr[None, :] + (a - 0.5) * (hi - lo)[None, :] * 0.92
    _t, fi = _first_hit(V, F, aim + D * rad, -D)
    hit = fi >= 0
    if hit.sum() < 50:
        return 0.0
    return float(np.mean(M[fi[hit]] == int(mat)))


def _signed_volume(m):
    """Six times the enclosed volume of a Mesh, about its own centroid."""
    V, F, _M = _mesh_triangles(m)
    if not len(F):
        return 0.0
    c = V.mean(axis=0)
    A = V[F[:, 0]] - c
    B = V[F[:, 1]] - c
    C = V[F[:, 2]] - c
    return float(np.einsum("ij,ij->i", A, np.cross(B, C)).sum() / 6.0)


def inside_out_fraction(fig, n_rays=1400, seed=7, mats=None):
    """Fraction of the figure's visible surface that shows its own INSIDE.

    THE DEFECT, MEASURED THE WAY THE EYE SEES IT. This mesh is deliberately a
    stack of open, interpenetrating shells -- a shirt shell, a shoulder cap, two
    sleeves, a collar -- so counting open boundary loops measures the
    construction, not the defect: the first version of this check returned
    0.49 m^2 of "hole" on a figure with no visible hole at all, because a trunk
    shell's top ring is legitimately open under a shoulder cap. An exact
    measurement of the wrong layer.

    What a viewer actually sees is a BACK FACE. A closed shell presents its
    outside to every ray that reaches it from outside; a hole presents the
    inside of the shell behind it, which is the dark ellipse on each shoulder in
    the 767 px peep. So: cast rays inward from a sphere around the figure, take
    the first hit, and report the fraction whose normal points AWAY from the
    viewer. Scale-free, pose-free, and it cannot pass by construction.
    """
    m = fig["mesh"]
    V, F, _M = _mesh_triangles(m, mats=mats)
    if not len(F):
        return 0.0
    lo, hi = V.min(axis=0), V.max(axis=0)
    ctr = 0.5 * (lo + hi)
    rad = float(np.linalg.norm(hi - lo)) * 0.75 + 0.3
    rr = rng_for(int(seed), 991)
    u = np.array([rr.u() for _ in range(n_rays)])
    v = np.array([rr.u() for _ in range(n_rays)])
    # directions on the sphere, and an aim point inside the body's bounding box
    z = 2.0 * u - 1.0
    ph = TAU * v
    s = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    D = np.stack([s * np.cos(ph), s * np.sin(ph), z], axis=1)
    a1 = np.array([rr.u() for _ in range(n_rays)])
    a2 = np.array([rr.u() for _ in range(n_rays)])
    a3 = np.array([rr.u() for _ in range(n_rays)])
    aim = ctr[None, :] + (np.stack([a1, a2, a3], axis=1) - 0.5) \
        * (hi - lo)[None, :] * 0.92
    org = aim + D * rad
    dirn = -D
    t, fi = _first_hit(V, F, org, dirn)
    hit = fi >= 0
    if hit.sum() < 50:
        return 0.0
    f = F[fi[hit]]
    n = np.cross(V[f[:, 1]] - V[f[:, 0]], V[f[:, 2]] - V[f[:, 0]])
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    facing = np.einsum("rj,rj->r", n, dirn[hit])
    return float(np.mean(facing > 0.0))


def sleeve_head_protrusion_mm(fig):
    """How far the sleeve head sticks out past the trunk garment, in mm.

    THE MEASUREMENT, not the intent. The trunk shell's top ring is the shoulder
    seam; anything on the sleeve above it is a pauldron. Reported as the max
    height of any MAT_TOP vertex above the trunk's own top ring plane, minus the
    same figure's shoulder-cap height, so a correctly domed sleeve scores ~0 and
    the old `extend_start` path scores ~90.

    Positive control: `build_figure(..., sleeve_control=True)` restores the old
    path in the same run, so this reports "0.3 mm here, 88.1 mm there" instead
    of a claim.

    IT IS RESTRICTED TO THE OUTBOARD THIRD, and that restriction is the whole
    reason the number means anything. Plenty of legitimate garment sits above
    the acromion -- the shoulder cap's trapezius rise and every collar ring --
    but all of it is INBOARD, near the neck. A pauldron is over the deltoid. So
    the filter is `|lateral| > 0.60 * shoulder_half`, which keeps the collar and
    the cap out of the statistic and keeps the defect in it.
    """
    m = fig["mesh"]
    sk = fig["skeleton"]
    b = fig["body"]
    V, vmat = m.vertex_materials()
    top = V[vmat == MAT_TOP]
    if not len(top):
        return 0.0
    up = sk.basis["thorax"][:, 2]
    lat = sk.basis["thorax"][:, 0]
    acr = np.asarray(sk.tip("thorax"), float)
    d = top - acr[None, :]
    sel = np.abs(d @ lat) > 0.60 * b.shoulder_half
    if not sel.any():
        return 0.0
    return float(max(0.0, float((d[sel] @ up).max())) * 1000.0)


def _sweep_face_normals(sw):
    """Unit normal of every quad of a closed Sweep, as (S-1, R, 3)."""
    V = sw.verts()
    a = np.roll(V, -1, axis=1) - V
    b = np.roll(V, -1, axis=0) - V
    n = np.cross(a, b)[:-1]
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)


def _probe_part(seed, lod, body, part):
    """The (Sweep, t, t0, t1, drape) a garment probe is run on. Shared, so two
    instruments cannot disagree about which body they measured."""
    lod = lod or LOD_L0
    b = body or sample_body(rng_for(seed, 1), adult_only=True)
    _a, pose = sample_pose(rng_for(seed, 3), b, archetype="stand_relaxed")
    sk = solve_skeleton(b, pose)
    if part == "arm":
        sw = build_arm(sk, "L", b, lod, seed)
        return sw, np.linspace(0.0, 1.0, sw.S), 0.0, 0.985, 1.05, b
    if part == "leg":
        sw = build_leg(sk, "L", b, lod, seed)
        return sw, np.linspace(0.0, 1.0, sw.S), 0.0, 0.97, 1.00, b
    sw, t = build_torso(sk, b, lod, seed)
    return sw, t, -0.2399, 1.0001, 0.95, b


def garment_hangs_off_the_body(seed, lod=None, body=None, part="torso",
                               relax="cloth", ctl="lowpass", spec=None,
                               elev_deg=None):
    """Does the garment SPAN the body's hollows, or paint them? Measured.

    The statistic is the CLEARANCE between the garment shell and the body's own
    relief-free base, along the base's outward normal, over every ring point:

      `contact_mm`  the 5th percentile -- where the cloth is actually touching.
                    Cloth is a membrane in tension: it must still touch. A
                    garment whose contact clearance has risen is not hanging,
                    it is INFLATED, which is exactly what `relax="dilate"` does
                    and why that path is kept.
      `span_mm`     p95 - p05, the depth of cloth that is bridging something.
                    A paint job scores whatever the fold field alone is worth;
                    a garment scores that plus the hollows it spans.

    and, because this film's sun is at 12.47 deg where tan(e) = 0.221, the
    `m` the change is worth: 2 tan(theta) / tan(e) on the RMS angle between
    corresponding faces of the control shell and this one.
    """
    sw, t, t0, t1, drape, b = _probe_part(seed, lod, body, part)
    spec = spec or dict(OVERALL)
    if sw.BX is None:
        raise RuntimeError("the body sweep carries no relief-free base")
    kw = dict(seed=seed + 101, spec=spec, t0=t0, t1=t1, drape=drape)
    g_ctl, _ = garment_from_sweep(sw, t, relax=ctl, **kw)
    g_new, _ = garment_from_sweep(sw, t, relax=relax, **kw)
    i0 = int(np.clip(int(np.searchsorted(t, t0)), 0, len(t) - 3))
    i1 = int(np.clip(max(int(np.searchsorted(t, t1)), i0 + 3), i0 + 3, len(t)))
    base = sw.slice(i0, i1).relaxed(0.0)
    nm = base.normals2d()
    nw = np.einsum("sij,srj->sri", base.B,
                   np.stack([nm[..., 0], nm[..., 1],
                             np.zeros_like(nm[..., 0])], axis=-1))
    Vb = base.verts()
    out = {"part": part, "relax": relax, "ctl": ctl}
    for tag, g in ((("ctl_" + ctl), g_ctl), ("this", g_new)):
        cl = 1000.0 * np.einsum("sri,sri->sr", g.verts() - Vb, nw)
        out[tag + "_contact_mm"] = float(np.percentile(cl, 5.0))
        out[tag + "_median_mm"] = float(np.percentile(cl, 50.0))
        out[tag + "_p95_mm"] = float(np.percentile(cl, 95.0))
        out[tag + "_span_mm"] = float(np.percentile(cl, 95.0)
                                      - np.percentile(cl, 5.0))
    out["inflation_mm"] = (out["this_contact_mm"]
                           - out["ctl_" + ctl + "_contact_mm"])
    out["span_gain_mm"] = (out["this_span_mm"]
                           - out["ctl_" + ctl + "_span_mm"])
    e = math.radians(SUN_ELEV_DEG if elev_deg is None else float(elev_deg))
    dot = np.clip(np.einsum("sri,sri->sr", _sweep_face_normals(g_ctl),
                            _sweep_face_normals(g_new)), -1.0, 1.0)
    th = float(np.sqrt(np.mean(np.arccos(dot) ** 2)))
    out["normal_rms_deg"] = math.degrees(th)
    out["m_changed"] = 2.0 * math.tan(th) / math.tan(e)
    return out


def fold_relief_profile(seed, lod=None, body=None, part="torso", spec=None,
                        mode=None, elev_deg=None):
    """Is the fold field a few CREASES or a uniform crust? Measured on the mesh.

    The distinction cannot be made by amplitude or by variance -- an fbm and a
    ridged noise of the same RMS are the same number and completely different
    pictures. What separates them is the SHAPE OF THE SLOPE DISTRIBUTION:

      `p50` / `p99`  the median and 99th-percentile angle between the garment
                     shell's face normals and the smooth base's. An isotropic
                     Gaussian field has p99/p50 ~ 2.6 by construction; a field
                     that is flat over most of the surface and steep in narrow
                     lines runs 5-10.
      `active`       the fraction of faces steeper than 4 deg, i.e. the share
                     of the garment that is actually creased.
      `aniso`        RMS of the residual's gradient across the body divided by
                     the same along it. Hanging cloth flutes VERTICALLY, so a
                     fold's gradient is in u and this is > 1. Isotropic noise
                     scores ~1 and is why the superseded field read as plaster
                     rather than as drape.

    and the median and 99th slopes are reported as `m` under the contract sun,
    because that is the number this project argues in.
    """
    global FOLD_MODE
    keep = FOLD_MODE
    if mode is not None:
        FOLD_MODE = mode
    try:
        sw, t, t0, t1, drape, b = _probe_part(seed, lod, body, part)
        spec = spec or dict(OVERALL)
        kw = dict(seed=seed + 101, spec=spec, t0=t0, t1=t1, drape=drape)
        g, tt = garment_from_sweep(sw, t, **kw)
    finally:
        FOLD_MODE = keep
    i0 = int(np.clip(int(np.searchsorted(t, t0)), 0, len(t) - 3))
    i1 = int(np.clip(max(int(np.searchsorted(t, t1)), i0 + 3), i0 + 3, len(t)))
    rs = relax_spec(GARMENT_RELAX)
    base = sw.slice(i0, i1).relaxed(rs[0], roll_m=rs[1], roll_u=rs[2],
                                    morph=rs[3])
    nb = _sweep_face_normals(base.offset(spec.get("ease", 0.025)))
    ng = _sweep_face_normals(g)
    ang = np.degrees(np.arccos(np.clip(np.einsum("sri,sri->sr", nb, ng),
                                       -1.0, 1.0)))
    # the radial residual, and its gradient in each direction
    nm = base.normals2d()
    nw = np.einsum("sij,srj->sri", base.B,
                   np.stack([nm[..., 0], nm[..., 1],
                             np.zeros_like(nm[..., 0])], axis=-1))
    res = np.einsum("sri,sri->sr", g.verts() - base.verts(), nw)
    du = float(np.linalg.norm(np.roll(base.verts(), -1, axis=1)
                              - base.verts(), axis=-1).mean())
    dv = float(np.linalg.norm(np.diff(base.C, axis=0), axis=1).mean())
    gu = np.abs(np.roll(res, -1, axis=1) - res) / max(du, 1e-9)
    gv = np.abs(np.diff(res, axis=0)) / max(dv, 1e-9)
    e = math.radians(SUN_ELEV_DEG if elev_deg is None else float(elev_deg))
    out = {"part": part, "mode": mode or keep,
           "p50_deg": float(np.percentile(ang, 50.0)),
           "p90_deg": float(np.percentile(ang, 90.0)),
           "p99_deg": float(np.percentile(ang, 99.0)),
           "active_frac": float(np.mean(ang > 4.0)),
           "pp_mm": float(1000.0 * (res.max() - res.min())),
           "aniso": float(np.sqrt(np.mean(gu ** 2))
                          / max(float(np.sqrt(np.mean(gv ** 2))), 1e-9))}
    out["peak_over_median"] = out["p99_deg"] / max(out["p50_deg"], 1e-6)
    for k in ("p50", "p90", "p99"):
        out["m_" + k] = 2.0 * math.tan(math.radians(out[k + "_deg"])) \
            / math.tan(e)
    return out


def _bridge_controls(roll=0.26, n=61, span=0.60):
    """The two synthetic profiles that decide whether the operator is right.

    A RAMP is the case a closing must leave ALONE and a plain dilation must
    fail -- it is the whole reason the shipped bridge is a closing. A V-GROOVE
    is the case both must fill, to a depth this function computes in closed
    form (a ball of radius R spanning a gap of width W dips W^2/8R into it), so
    the check has an answer it did not get from the code under test.
    """
    x = np.linspace(0.0, span, n)
    ramp = 0.20 - 0.10 * (x / span)
    W = 0.16
    groove = np.where(np.abs(x - span * 0.5) < W * 0.5, 0.20 - 0.030, 0.20)
    cl_ramp = roll_close(ramp, x, roll)
    di_ramp = roll_close(ramp, x, roll, morph="dilate")
    cl_gro = roll_close(groove, x, roll)
    mid = n // 2
    return {
        "ramp_close_max_mm": float(1000.0 * np.max(np.abs(cl_ramp - ramp))),
        "ramp_dilate_max_mm": float(1000.0 * np.max(np.abs(di_ramp - ramp))),
        "groove_filled_mm": float(1000.0 * (cl_gro[mid] - groove[mid])),
        "groove_depth_mm": 30.0,
        "predicted_residual_mm": float(1000.0 * W * W / (8.0 * roll)),
        "groove_residual_mm": float(1000.0 * (0.20 - cl_gro[mid])),
    }


def garment_inherits_body_relief(seed, lod=None, body=None, part="arm",
                                 relax="cloth", spec=None, elev_deg=None):
    """Does the garment shell carry the BODY's own muscle relief? Measured.

    Two numbers, on the artefact, with the shipped path in the same run as a
    positive control:

      `gain`  the noise-ATTRIBUTABLE part of the shell, isolated by building
              the whole garment TWICE off the same body -- once off the real
              sweep and once off a twin whose rings are the relief-free ones --
              and projecting the difference onto the body's own noise field.
              The shipped path offsets the noisy rings, so it carries that
              field one-for-one and must score ~1.0; a garment lofted from the
              relief-free base must score ~0.0.

              THE EARLIER FORM OF THIS PROJECTED THE SHELL'S WHOLE RESIDUAL and
              it broke the moment a second term was added to the pipeline: the
              rolling-ball bridge lifts the shell by 1-3 mm at roughly the same
              spatial scale as the muscle noise, so a chance overlap between
              two unrelated fields of similar RMS put the arm at 0.141 and the
              torso at 0.356 and the check went red on a garment that provably
              carries no noise at all. A statistic that cannot separate the
              term it is about from the rest of the pipeline is not measuring
              the term it is about. The twin build has no such coupling: the
              two shells differ ONLY by the noise.
      `gain_total` the old statistic, kept for continuity, and it is the one to
              distrust.
      `m`     the radiance modulation the difference is worth under the contract
              sun -- 2 tan(theta) / tan(elev), where theta is the RMS angle
              between corresponding face normals of the two shells. This is the
              number section 0.5 of HUMAN-REFERENCE.md says to reason in, and it
              is measured off the two meshes rather than predicted from an
              amplitude and a wavelength.
    """
    sw, t, t0, t1, drape, b = _probe_part(seed, lod, body, part)
    spec = spec or dict(OVERALL)
    if sw.BX is None:
        raise RuntimeError("the body sweep carries no relief-free base; "
                           "_tube_impl / build_torso must record one")
    kw = dict(seed=seed + 101, spec=spec, t0=t0, t1=t1, drape=drape)
    # THE TWIN: the same body with its muscle relief never applied. Everything
    # downstream -- the low-pass, the bridge, the fold field, the ease and the
    # cover correction -- is identical, so the difference between the two
    # shells is the noise and nothing else.
    twin = Sweep(sw.C, sw.B, sw.BX.copy(), sw.BY.copy(), sw.closed,
                 base=(sw.BX, sw.BY))
    g_ctl, _ = garment_from_sweep(sw, t, relax="none", **kw)
    g_ctl_tw, _ = garment_from_sweep(twin, t, relax="none", **kw)
    g_new, _ = garment_from_sweep(sw, t, relax=relax, **kw)
    g_new_tw, _ = garment_from_sweep(twin, t, relax=relax, **kw)
    # the body's own noise field, along the base's outward normal
    i0 = int(np.clip(int(np.searchsorted(t, t0)), 0, len(t) - 3))
    i1 = int(np.clip(max(int(np.searchsorted(t, t1)), i0 + 3), i0 + 3, len(t)))
    raw = sw.slice(i0, i1)
    base = raw.relaxed(0.0)
    nm = base.normals2d()
    nw = np.einsum("sij,srj->sri", base.B,
                   np.stack([nm[..., 0], nm[..., 1],
                             np.zeros_like(nm[..., 0])], axis=-1))
    Vb = base.verts()
    noise = np.einsum("sri,sri->sr", raw.verts() - Vb, nw)
    noise = noise - noise.mean()
    den = float(np.sum(noise * noise))
    out = {"part": part, "relax": relax,
           "body_noise_pp_mm": float(1000.0 * (noise.max() - noise.min()))}
    for tag, g, gt in (("shipped", g_ctl, g_ctl_tw), ("this", g_new, g_new_tw)):
        res = np.einsum("sri,sri->sr", g.verts() - Vb, nw)
        out["gain_total_" + tag] = float(
            np.sum((res - res.mean()) * noise) / max(den, 1e-18))
        dif = np.einsum("sri,sri->sr", g.verts() - gt.verts(), nw)
        dif = dif - dif.mean()
        out["gain_" + tag] = float(np.sum(dif * noise) / max(den, 1e-18))
    e = math.radians(SUN_ELEV_DEG if elev_deg is None else float(elev_deg))
    dot = np.clip(np.einsum("sri,sri->sr", _sweep_face_normals(g_ctl),
                            _sweep_face_normals(g_new)), -1.0, 1.0)
    ang = np.arccos(dot)
    th = float(np.sqrt(np.mean(ang ** 2)))
    p99 = float(np.percentile(ang, 99.0))
    out["normal_rms_deg"] = math.degrees(th)
    out["normal_p99_deg"] = math.degrees(p99)
    out["m_removed"] = 2.0 * math.tan(th) / math.tan(e)
    out["m_removed_p99"] = 2.0 * math.tan(p99) / math.tan(e)
    return out


def shoulder_cap(sw, sk, b, rows=5, r_neck=None, rise=1.0, extra=0.0):
    """Close a trunk shell over the shoulders and down to a neck ring.

    The naive closure -- a fan to the centroid of the top ring -- puts a flat
    lid at acromion height, which is what the first build of this had, and the
    silhouette of a person with a flat top is unmistakable. The real shape is a
    SHELF: the deltoid line stays out at nearly full width until close to the
    neck, then drops fast, while the sagittal direction necks in early. That is
    the exponent below -- `f ** (0.8 + 1.4 cos(theta)^2)` -- and it is the whole
    trick.
    """
    R = sw.R
    Ptop = sw.verts()[-1]                                    # (R,3) world
    nb = sk.origin["head"]
    Bn = sk.basis["neck"]
    rn = float(r_neck if r_neck is not None else b.neck_r * 1.06) + extra
    th = ring_theta(R)
    Pneck = nb[None, :] + (np.cos(th)[:, None] * (Bn[:, 0] * rn)[None, :]
                           + np.sin(th)[:, None] * (Bn[:, 1] * rn * 1.16)[None, :])
    Pneck = Pneck - Bn[None, :, 2] * (b.neck_len * 0.42)
    c2 = np.cos(th) ** 2
    up = sk.basis["thorax"][:, 2]
    out = []
    for i in range(1, rows + 1):
        f = i / float(rows)
        w = f ** (0.8 + 1.4 * c2)
        P = Ptop * (1.0 - w[:, None]) + Pneck * w[:, None]
        # trapezius: the ridge between the neck and the point of the shoulder
        P = P + up[None, :] * (rise * b.chest_depth * 0.085
                               * np.sin(math.pi * f) * (1.0 - c2))[:, None]
        out.append(P)
    return np.stack([Ptop] + out)


def build_top(mesh, sw_t, t_t, arms, sk, b, lod, seed, spec, mat, wear=0.0,
              sleeve_control=False):
    """Shirt / jacket / jersey: trunk shell, shoulder cap, sleeves, collar."""
    hem = spec.get("hem", 0.14)
    ease = spec.get("ease", 0.025)
    shell, tt = garment_from_sweep(sw_t, t_t, seed + 101, spec, hem, 1.0001,
                                   drape=1.0)
    # hem: the bottom two rings roll outward and thicken -- a real folded edge
    d = np.zeros((shell.S, shell.R))
    hemw = np.exp(-0.5 * ((np.arange(shell.S)) / 1.1) ** 2)[:, None]
    d = d + 0.0026 * hemw
    # side seams and a front placket, as raised welts
    if lod.seams:
        d = d + _ridge(shell, tt, 0.00, 0.006, 0.0016)
        d = d + _ridge(shell, tt, 0.50, 0.006, 0.0016)
        if spec.get("collar") in ("shirt", "polo"):
            d = d + _ridge(shell, tt, 0.25, 0.010, 0.0022)
    shell = shell.offset(d)
    shell.emit(mesh, mat, cap_start=True, wear=wear, v0=float(tt[0]),
               v1=float(tt[-1]))
    cap = shoulder_cap(shell, sk, b, rows=max(3, lod.station),
                       r_neck=b.neck_r * 1.04 + 0.24 * ease, extra=0.0)
    emit_grid(mesh, cap, mat, closed_u=True, wear=wear,
              vv=np.repeat(np.linspace(1.0, 1.25, cap.shape[0]), cap.shape[1]))

    # --- sleeves ----------------------------------------------------------
    sl = spec.get("sleeve", 0.25)
    if sl > 0.05:
        for side in ("L", "R"):
            sw_a, t_a = arms[side]
            flex = _flex_along(sk, ("arm_" + side, "fore_" + side), t_a)
            slv, ta = garment_from_sweep(sw_a, t_a, seed + 211 + ord(side),
                                         spec, 0.0, min(sl, 0.999), flex=flex,
                                         drape=1.15)
            # A CUFF IS GATHERED IN AND THEN BANDED OUT -- see `_cuff_profile`.
            # The single outward Gaussian this replaces rendered as a hard
            # cylindrical flange standing off the end of the sleeve like a cast,
            # on every short-sleeved figure in the 767 px bench frame.
            dd = _cuff_profile(slv, gather=(0.0026 if sl > 0.6 else 0.0018),
                               band=(0.0030 if sl > 0.6 else 0.0022), rows=3)
            if lod.seams:
                dd = dd + _ridge(slv, ta, 0.50, 0.007, 0.0015)
            slv = slv.offset(dd)
            if sleeve_control:
                # THE POSITIVE CONTROL -- the shipped path, kept verbatim so the
                # protrusion check has a case it is known to fail.
                slv = slv.extend_start(2, b.upper_arm * 0.30)
                slv.emit(mesh, mat, cap_end=(sl < 0.90), wear=wear,
                         v0=float(ta[0]), v1=float(ta[-1]))
            else:
                slv.emit(mesh, mat, cap_end=(sl < 0.90), wear=wear,
                         v0=float(ta[0]), v1=float(ta[-1]))
                sleeve_head(mesh, slv, sk, side, b, lod, mat, wear=wear)
    build_collar(mesh, sk, b, lod, seed, spec, mat, ease, wear)


def build_collar(mesh, sk, b, lod, seed, spec, mat, ease, wear=0.0,
                 col=None):
    """crew / polo / shirt / stand / hood, as four rings of real geometry."""
    kind = spec.get("collar", "crew")
    R = max(14, lod.ring)
    th = ring_theta(R)
    nb = sk.origin["head"]
    Bn = sk.basis["neck"]
    r0 = b.neck_r * 1.04 + 0.24 * ease
    z0 = -b.neck_len * 0.42
    if kind == "crew":
        prof = [(z0, r0 * 1.02, 0.0), (z0 + 0.016, r0 * 1.00, 0.0),
                (z0 + 0.024, r0 * 1.05, 0.0), (z0 + 0.012, r0 * 1.09, 0.0)]
    elif kind == "stand":
        prof = [(z0, r0 * 1.02, 0.0), (z0 + 0.030, r0 * 1.02, 0.0),
                (z0 + 0.052, r0 * 1.06, 0.0), (z0 + 0.048, r0 * 1.12, 0.0)]
    elif kind == "hood":
        prof = [(z0, r0 * 1.05, 0.0), (z0 + 0.030, r0 * 1.30, -0.055),
                (z0 + 0.060, r0 * 1.55, -0.105), (z0 + 0.045, r0 * 1.45, -0.135)]
    else:                                    # shirt / polo: a folded-over band
        h = 0.034 if kind == "shirt" else 0.026
        prof = [(z0, r0 * 1.01, 0.0), (z0 + h * 0.55, r0 * 1.02, 0.0),
                (z0 + h, r0 * 1.07, -0.005), (z0 + h * 0.45, r0 * 1.15, -0.010)]
    rings = []
    for (zz, rr, yy) in prof:
        P = nb[None, :] + (np.cos(th)[:, None] * (Bn[:, 0] * rr)[None, :]
                           + np.sin(th)[:, None] * (Bn[:, 1] * rr * 1.16)[None, :]
                           + Bn[None, :, 2] * zz + Bn[None, :, 1] * yy)
        rings.append(P)
    G = np.stack(rings)
    if kind in ("shirt", "polo"):
        # the collar OPENS at the front: pull the front points down and apart
        u = th / TAU
        front = np.exp(-0.5 * (((u - 0.25 + 0.5) % 1.0 - 0.5) / 0.085) ** 2)
        G[2:] = G[2:] - Bn[None, None, :, 2] * (front[None, :, None] * 0.016)
        G[3] = G[3] + Bn[None, :, 1] * (front[:, None] * 0.007)
    emit_grid(mesh, G, mat, closed_u=True, wear=wear, col=col)


def build_bottom(mesh, sw_t, t_t, legs, sk, b, lod, seed, spec, mat, wear=0.0):
    """Trousers / shorts / skirt: a seat shell plus two leg tubes."""
    rise = spec.get("rise", 0.34)
    ease = spec.get("ease", 0.024)
    seat, ts = garment_from_sweep(sw_t, t_t, seed + 301, spec, -0.2399, rise,
                                  drape=0.85)
    d = np.zeros((seat.S, seat.R))
    # waistband: a stiff band that stands proud, at the top of the seat shell
    wb = np.exp(-0.5 * ((np.arange(seat.S) - (seat.S - 1)) / 1.3) ** 2)[:, None]
    d = d + 0.0042 * wb
    if lod.seams:
        d = d + _ridge(seat, ts, 0.50, 0.006, 0.0020)      # back rise seam
        d = d + _ridge(seat, ts, 0.25, 0.006, 0.0018)      # fly
    seat = seat.offset(d)
    seat.emit(mesh, mat, cap_start=True, wear=wear, v0=float(ts[0]),
              v1=float(ts[-1]))
    if spec.get("belt", True) and lod.seams:
        _belt(mesh, seat, ts, b, lod, seed)
    lg = spec.get("leg", 0.98)
    if lg > 0.05:
        for side in ("L", "R"):
            sw_l, t_l = legs[side]
            flex = _flex_along(sk, ("hip_" + side, "knee_" + side), t_l)
            trs, tl = garment_from_sweep(sw_l, t_l, seed + 401 + ord(side),
                                         spec, 0.0, min(lg, 0.999), flex=flex,
                                         drape=1.25)
            dd = _cuff_profile(trs, gather=0.0022,
                               band=spec.get("cuff", 0.028) * 0.11, rows=3)
            if lod.seams:
                dd = dd + _ridge(trs, tl, 0.00, 0.006, 0.0016)
                dd = dd + _ridge(trs, tl, 0.50, 0.006, 0.0016)
            trs = trs.offset(dd)
            trs.emit(mesh, mat, cap_end=(lg < 0.90), wear=wear,
                     v0=float(tl[0]), v1=float(tl[-1]))
            # The trouser leg gets the same closed head as the sleeve, aimed at
            # the pelvis so it converges inside the seat shell. The old
            # `extend_start` left it open; it happened to be buried on a
            # standing figure and was not on a seated or a striding one.
            sleeve_head(mesh, trs, sk, side, b, lod, mat, wear=wear, bulge=0.06,
                        toward=sk.origin["pelvis"],
                        depth=max(0.30 * b.hip_half, 0.045))
    elif spec.get("leg", 1.0) == 0.0:
        _skirt(mesh, sw_t, t_t, sk, b, lod, seed, spec, mat, wear)


def _belt(mesh, seat, ts, b, lod, seed):
    """A leather belt at the waistband, on the SHOE material.

    Four rings, 30 mm deep, standing 5 mm proud, with a buckle plate at the
    front. It is here because the waist is the one place on a clothed figure
    where two garments meet, and without a belt the join reads as a seam in a
    single suit -- which is what the first Cycles look showed.
    """
    S = seat.S
    i1 = S - 1
    i0 = max(0, i1 - 2)
    band = seat.slice(i0, S)
    band = band.offset(0.0048)
    band.emit(mesh, MAT_SHOE, zone=ZONE_BELT)
    # buckle: a small plate at the front (u = 0.25 is +Y on these rings)
    R = band.R
    j = int(round(0.25 * R)) % R
    V = band.verts()
    nm = band.normals2d()
    cols = [(j + k - 2) % R for k in range(5)]
    P = np.empty((2, len(cols), 3))
    for a, s_ in enumerate((i1 - i0 - 1, i1 - i0)):
        s_ = min(max(s_, 0), band.S - 1)
        for c, cidx in enumerate(cols):
            P[a, c] = V[s_, cidx] + band.B[s_] @ np.array(
                [nm[s_, cidx, 0], nm[s_, cidx, 1], 0.0]) * 0.0035
    emit_grid(mesh, P, MAT_SHOE, closed_u=False, zone=ZONE_BELT)


def _skirt(mesh, sw_t, t_t, sk, b, lod, seed, spec, mat, wear):
    """A skirt: a flared cone of rings that hangs from the hip, with flutes."""
    R = max(20, lod.ring + 10)
    S = max(8, 2 * lod.station + 4)
    i = int(np.searchsorted(t_t, spec.get("rise", 0.34)))
    C0 = sw_t.C[i]
    B0 = sw_t.B[i]
    th = ring_theta(R)
    rr = rng_for(seed, 313)
    L = b.trochanter_h * (0.42 + 0.42 * rr.u())
    out = []
    for s in range(S):
        f = s / (S - 1.0)
        r = b.hip_half * (1.02 + 0.55 * f ** 1.3)
        u = th / TAU
        flut = wrap_noise(seed + 5, u, np.full(R, f), 7.0, 1.2, oct=3)
        r = r + (0.016 * f ** 1.4) * flut
        # NEVER EXECUTED UNTIL THE CROWD ASKED FOR A SKIRT. `r` is a radius PER
        # COLUMN, (R,), and `B0[:, 0]` is a 3-vector; the shipped form wrote
        # `B0[:, 0] * r`, which numpy refuses the moment R != 3. Every bench
        # and every item so far has been crew, marshal or paddock -- trousers
        # to a man -- so the first figure ever to wear a skirt was spectator
        # number 40-odd of a 402-source library, and it took the whole build
        # down. An outer product is what was meant.
        P = (C0[None, :]
             + (np.cos(th) * r)[:, None] * B0[None, :, 0]
             + (np.sin(th) * r * 0.86)[:, None] * B0[None, :, 1]
             - B0[None, :, 2] * (L * f))
        out.append(P)
    emit_grid(mesh, np.stack(out), mat, closed_u=True, wear=wear)


# ===========================================================================
# 12.  HAIR -- geometry with a real silhouette, not a painted cap
# ===========================================================================

def build_hair(mesh, sk, b, lod, seed, mat, squash=1.0):
    """A hair mass built on its OWN polar grid, cut at a per-column hairline.

    The obvious construction -- take the head grid, offset it by a thickness
    field, and drop the rows that are empty -- cannot work, and the clay render
    showed why: a grid can only be cut on WHOLE ROWS, so the hairline came out
    as a hard horizontal plate edge across the forehead. Here row i of column j
    sits at polar angle `th_max(j) * i / (m-1)`, so the last row IS the
    hairline, exactly, at whatever azimuth-dependent height the style says --
    and the thickness tapers to zero there, so the hair meets the skin instead
    of ending in a cliff.

    The strands on top are what break the OUTLINE, which is what makes hair read
    as hair rather than as a moulded cap, and what supplies the head's share of
    `silhouette_departs_from_analytic`.

    THE MASS IS LOCKED, IN THE MESH, AND THAT IS WHY THIS GRID IS DENSER THAN
    THE HEAD'S. Defect 3 was "a granular crust ... the ugliest thing in both
    frames". Half of it was the shader (see `HAIR_RELIEF`); the other half is
    that the mass had no structure of its own at all -- one smooth ellipsoid
    carrying an ISOTROPIC thickness noise, so every hair-like signal in the
    picture came from a bump map, and a bump map cannot move a silhouette. A
    lock of hair is 10-20 mm across at the scalp, which is 4 px at the crowd's
    63 px head and 26 px at the 400 px face framing -- resolvable at both, so it
    has to be geometry at both.

    A ridge needs about three columns to read, so `n` is now 2x `head_u`
    rather than 0.75x: 144 columns at L0 gives 36 locks at 15 mm, 88 at L1
    gives 22 at 25 mm. Measured cost on a seated L1 figure: +2.2 k triangles on
    29.8 k, **+7.2 %**, all of it in the one part of the figure the frames say
    is worst. The shader's own `lock` stage sits at 7.2 mm, i.e. BELOW what this
    grid can carry, so the two do not fight: the mesh owns the lock and its
    outline, the shader owns the texture between locks.
    """
    if b.hair_style == "bald" or b.hair_len <= 0.001:
        return 0
    O = sk.origin["head"]
    B = sk.basis["head"]
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    rr = rng_for(seed, 131)
    zc, ax, ay, az = 0.16 * hh, 0.5 * hw, 0.5 * hd, 0.50 * hh
    yc = -0.06 * hd
    n = (max(24, 3 * lod.head_u // 4) if HAIR_LEGACY else max(36, 2 * lod.head_u))
    m = (max(6, lod.head_v // 3) if HAIR_LEGACY else max(8, lod.head_v // 2))
    ph = np.linspace(0.0, TAU, n, endpoint=False) - math.pi / 2.0
    u = ((ph + math.pi / 2.0) / TAU) % 1.0
    recede = 0.0
    if b.sex == "M" and b.age_band in ("adult", "elder"):
        recede = float(np.clip(rr.n(0.10, 0.16) + 0.006 * (b.age_years - 25.0),
                               0.0, 0.55))
    front = np.clip(np.sin(ph), 0.0, 1.0)
    jag = 0.075 * wrap_noise(seed + 9, u, np.zeros(n), 11.0, 1.0, oct=3)
    fz_b = np.clip((0.06 - 0.62 * recede) + 0.78 * front ** 2.0 + jag,
                   -0.94, 0.94)
    th_max = np.arccos(fz_b)
    i = np.arange(m)[:, None]
    # THE CROWN WAS A NEEDLE, NOT A DOME. `TH = th_max * i / (m - 1)` puts the
    # WHOLE of ring 0 at theta = 0, i.e. every one of its 33 vertices on the
    # polar axis -- and because `grow` carries `lump`, which is a function of
    # PH, they do not coincide there: measured on a real figure, ring 0 spans
    # 2.2 mm in xy and **10.8 mm in z**. So the top of every uncovered head was
    # a 10.8 mm vertical spike of 33 vertices, ringed by 33 sliver quads at
    # 55 mm^2 against a typical 307, with `cap_lo` then fanning 33 exactly
    # ZERO-AREA triangles to an apex above it. A zero-area face has no defined
    # normal; Cycles will shade it with whatever the interpolation gives.
    #
    # Ring 0 now starts one row IN from the pole and `cap_lo` closes a real
    # dome over it. The hairline (i = m-1, TH = th_max) does not move.
    # Found by a full-parameter-space sweep of the composer: 2,293 of 2,360
    # figures carried exactly this, median 33 degenerate triangles each.
    TH = th_max[None, :] * ((i + 1.0) / float(m))
    PH = np.broadcast_to(ph[None, :], TH.shape)
    fx = np.sin(TH) * np.cos(PH)
    fy = np.sin(TH) * np.sin(PH)
    fz = np.cos(TH)
    # A HAT FLATTENS HAIR, and until this was here it did not. The mass is up
    # to 39 mm thick and `build_headwear`'s clearance was a flat 6 mm, so every
    # capped figure wore its cap INSIDE its hair: the A3 face render shows a
    # bare red band and peak with a granular brown dome above them and no cap
    # crown anywhere. `squash` is what a hat does to hair, and the residual
    # thickness is handed to `build_headwear` so the dome clears it.
    thick = (0.008 + 0.030 * b.hair_vol) * hh / 0.23 * float(squash)
    uu2 = ((PH + math.pi / 2.0) / TAU) % 1.0
    # THE MASS MUST NOT TAPER TO ZERO WHERE IT CARRIES ON. The taper exists so
    # hair MEETS SKIN at the forehead instead of ending in a cliff, and that is
    # right at the face -- but it was applied at every azimuth, so at the sides
    # and nape the hanging mass left the hairline at zero thickness and the
    # frames show it: a hard cut-out edge round the ear with no volume behind
    # it. The taper now ends at a per-column value that is 0 at the face and
    # 0.72 where the fall hangs, which is the same `back` weight `_hair_fall`
    # uses for its length -- one quantity, used twice, instead of two that can
    # disagree.
    back = np.clip(0.55 - fz_b, 0.0, 1.6) / 1.6                     # (n,)
    edge = 0.72 * back * (1.0 if b.hair_len > 0.055 else 0.0)
    tap0 = np.sin(math.pi * 0.5 * np.clip(1.0 - i / (m - 1.0), 0.0, 1.0)) ** 0.7
    taper = tap0 if HAIR_LEGACY else (edge[None, :]
                                      + (1.0 - edge[None, :]) * tap0)
    # --- the thickness field. Three terms, and each is a different scale of the
    # same object. `HAIR_LUMP` gains all three so the control exists.
    #
    # 1. VOLUME -- how the mass sits on the skull. Coarse (~200 mm), and this is
    #    what the shipped `lump` was, at 0.42 amplitude and nothing else.
    vol = 0.22 * wrap_noise(seed + 10, uu2, TH / math.pi,
                            fbm_scale(0.55, oct=3), fbm_scale(0.42, oct=3),
                            oct=3)
    # 2. LOCKS -- gutters that RUN DOWN THE HEAD, at the grid's own resolvable
    #    wavelength, NOT at a millimetre constant. A ridge and its valley need
    #    four columns to be a shape rather than an alias, so the lock count is
    #    `n // 4` and follows the tier: 36 locks at 15.4 mm at L0, 22 at 25 mm
    #    at L1. Asking for 7 mm locks on a 33-column grid is the frequency trap
    #    in the MESH, and it is how the crown became a needle once already.
    #
    #    The carrier is `|cos|` rather than a noise, for a reason that is not
    #    taste: a ridged noise puts its gutters wherever its zero crossings
    #    happen to fall -- about two per wavelength, but only on average -- so
    #    setting the wavelength does not set the spacing and half the locks come
    #    out at half the pitch, i.e. aliased. `|cos(pi N u)|` puts exactly N
    #    gutters around for any integer N, and is periodic in u whether N is
    #    odd or even because the absolute value kills the sign flip. The
    #    irregularity real hair has then comes from a phase JITTER and a
    #    strength modulation, both from `wrap_noise`, which is periodic too.
    #
    #    AND THEY MUST NOT REACH THE POLE. The first build of this ran the
    #    ridges the whole way from hairline to crown, and because they are
    #    MERIDIANS of a polar grid they all converge there: the render of a
    #    short blonde came back as a **fluted melon** -- a segmented gourd, or
    #    a ribbed swim cap -- which is the beanie's own `sin(PH * 9)` defect in
    #    a new costume. A real crown has a WHORL, not 36 ribs meeting at a
    #    point. `conv` fades them out over the top 30 deg, and `brk` breaks
    #    each lock along its own length so a lock starts and stops instead of
    #    running unbroken from the parting to the nape.
    n_lock = max(6, int(n // 4))
    jit = (0.34 / n_lock) * wrap_noise(
        seed + 14, uu2, TH / math.pi, fbm_scale(0.22, oct=2),
        fbm_scale(0.60, oct=2), oct=2)
    lock = 1.0 - 2.0 * np.abs(np.cos(math.pi * n_lock * (uu2 + jit)))
    brk = (0.12 + 0.88 * (0.5 + 0.5 * wrap_noise(
        seed + 15, uu2, TH / math.pi, fbm_scale(0.16, oct=2),
        fbm_scale(0.13, oct=2), oct=2))) ** 1.6
    conv = np.clip(TH / 0.62, 0.0, 1.0) ** 1.20
    lock = lock * brk * conv
    # AND A LOCK IS A PROPERTY OF LENGTH, NOT ONLY OF VOLUME. Scaling the
    # ridge depth off `thick` alone gave a 1.5 mm gutter on a 15 mm pitch to a
    # 20 mm crop, and the render of a short blonde came back as a **ribbed
    # gourd** -- v1 and v2 both. Hair that is 20 mm long cannot form a lock; it
    # is a close pelt with a parting and almost no relief. `lk_len` takes the
    # crop to a quarter depth and leaves anything past a bob at full.
    lk_len = float(np.clip(b.hair_len / 0.090, 0.22, 1.0))
    lock_amp = min(0.16 * thick, 0.0018) * lk_len
    # 3. THE PARTING. `HAIR_STYLES` has carried `part_frac` since it was written
    #    and nothing read it (see `sample_body`). A parting is a gutter along
    #    ONE meridian, deepest at the hairline and closing over the crown, and
    #    it is the single most identity-carrying thing about a head of hair.
    d_az = np.abs(((uu2 - (0.25 + b.hair_part_az)) + 0.5) % 1.0 - 0.5)
    part = np.exp(-(d_az / 0.028) ** 2) * np.clip(TH / (0.30 + 1e-9), 0.0, 1.0)
    part = part * float(b.hair_part) * 1.00
    if HAIR_LEGACY:
        # the shipped field: one ISOTROPIC noise at 0.42, no locks, no parting
        lock = lock * 0.0
        lock_amp = 0.0
        field = 1.0 + 0.42 * wrap_noise(seed + 10, uu2, TH / math.pi,
                                        7.0, 4.0, oct=3) * float(HAIR_LUMP)
    else:
        field = (1.0 + (vol + lock_amp / max(thick, 1e-6) * lock - part)
                 * float(HAIR_LUMP))
    grow = 1.0 + (thick * taper * np.clip(field, 0.05, 3.0)) \
        / max(0.5 * hw, 1e-6)
    P = np.stack([fx * ax * grow,
                  yc + fy * ay * grow * (1.0 - 0.10 * np.clip(-fz, 0, 1) ** 1.6),
                  zc + fz * az * grow], axis=-1)
    apex = np.array([0.0, yc, zc + az * (1.0 + thick / max(0.5 * hw, 1e-6))])
    W = O + np.einsum("ij,srj->sri", B, P)
    # `hk_v` RUNS CROWN -> TIP ACROSS BOTH PIECES. `emit_grid`'s default gives
    # each grid its own 0..1, so the cap ran 0..1 and the hanging mass ran 0..1
    # again -- and `hair_material`'s root-to-tip value ramp therefore restarted
    # at the hairline, putting the brightest hair on the crown AND on the
    # hairline with a step between them. The cap owns 0..0.5, the fall 0.5..1.
    emit_grid(mesh, W, mat, closed_u=True, cap_lo=O + B @ apex, zone=ZONE_SCALP,
              vv=(None if HAIR_LEGACY
                  else np.repeat(np.linspace(0.0, 0.5, m), n)))
    # THE LENGTH LIVES IN A HANGING MASS, NOT IN THE STRANDS. Giving 700 tubes
    # the full hair length produced a straw wig -- every hair individually
    # visible and none of them touching. Real hair at 176 px is a solid mass
    # whose EDGE is broken; so the mass is a surface that hangs from the
    # hairline, and the strands are a fringe on top of it a few millimetres wide.
    if b.hair_len > 0.055:
        P = np.concatenate([P, _hair_fall(P[-1], fz_b, b, lod, seed, ph,
                                          lock, lock_amp)])
        W2 = O + np.einsum("ij,srj->sri", B, P[m - 1:])
        nf = P.shape[0] - (m - 1)
        emit_grid(mesh, W2, mat, closed_u=True, zone=ZONE_SCALP,
                  vv=(None if HAIR_LEGACY
                      else np.repeat(np.linspace(0.5, 1.0, nf), n)))
    n_str = int(_hair_strand_budget(lod) * (0.5 + 0.9 * b.hair_vol)
                * (0.35 + 0.65 * float(squash)) * float(HAIR_STRAND_GAIN))
    if n_str <= 0:
        return thick
    N = _grid_normals(P, closed_u=True)
    amt = np.zeros(P.shape[:2])
    amt[:m] = taper
    amt[m:] = 1.0
    _hair_strands(mesh, O, B, P, N, amt, m, b, lod, seed, mat, n_str)
    return thick


#: `LOD.hair_strands` before the strand rewrite. `HAIR_LEGACY` restores it, so
#: the control frame carries the count the shipped frames were made with.
LEGACY_HAIR_STRANDS = {"L0": 620, "L1": 190, "L2": 48, "L3": 0}


def _hair_strand_budget(lod):
    if HAIR_LEGACY:
        return LEGACY_HAIR_STRANDS.get(lod.name.split("+")[0],
                                       lod.hair_strands)
    return lod.hair_strands


def _hair_fall(ring, fz_b, b, lod, seed, ph, lock=None, lock_amp=0.0):
    """The hanging mass below the hairline: long at the back and sides, ~0 at
    the face. Flares slightly and is broken by noise so its outline is not an arc.

    THE LOCKS CARRY ON DOWN IT, AND THEY SEPARATE. `ring` is the cap's last row
    and already has the lock relief in it, so the fall inherits the ridges for
    free -- but real hair does not hang in parallel columns, it separates into
    heavier locks that drift apart as they fall, and that separation is most of
    what breaks the outline of long hair. `sep` grows with depth, so the ridges
    that leave the hairline 15 mm apart are 40 % deeper and displaced by the
    time they reach the tips.
    """
    n = ring.shape[0]
    rows = max(4, lod.head_v // 6) if HAIR_LEGACY else max(5, lod.head_v // 4)
    u = ((ph + math.pi / 2.0) / TAU) % 1.0
    back = np.clip(0.55 - fz_b, 0.0, 1.6) / 1.6
    Lj = b.hair_len * (0.25 + 1.15 * back ** 1.2)
    Lj = Lj * (1.0 + 0.30 * wrap_noise(
        seed + 11, u, np.zeros(n),
        6.0 if HAIR_LEGACY else fbm_scale(0.16, oct=3), 1.0, oct=3))
    rad = np.hypot(ring[:, 0], ring[:, 1])
    rad = np.where(rad > 1e-6, rad, 1e-6)
    lk = None if lock is None else np.asarray(lock, float)[-1]
    out = []
    for i in range(1, rows + 1):
        f = i / float(rows)
        P = ring.copy()
        P[:, 2] -= Lj * f
        flare = 1.0 + 0.10 * f + 0.05 * wrap_noise(
            seed + 12, u, np.full(n, f),
            8.0 if HAIR_LEGACY else fbm_scale(0.12, oct=3), 2.0, oct=3)
        if lk is not None and not HAIR_LEGACY:
            # deepen the inherited gutters with depth, radially, so the locks
            # part rather than staying a fluted tube
            sep = 1.0 + (0.40 * f) * lock_amp * lk / rad
            flare = flare * sep
        P[:, 0] *= flare
        P[:, 1] = P[:, 1] * flare
        out.append(P)
    return np.stack(out)


def _hair_strands_legacy(mesh, O, B, P, N, amt, b, lod, seed, mat, n):
    """The SHIPPED strand layer, verbatim, as the positive control -- roots on
    grid vertices, 0.7-1.9 mm tubes, gravity from the first segment. This is
    what `render/faceab/face_base.png` shows as a lattice of dark commas across
    the dome. `HAIR_LEGACY`. Do not tune it."""
    rr = rng_for(seed, 137)
    S, R = amt.shape
    ii, jj = np.nonzero(amt > 0.02)
    if not len(ii):
        return
    wgt = (ii / max(S - 1.0, 1.0)) ** 1.6 + 0.06
    pick = rr.r.choice(len(ii), size=n, p=wgt / wgt.sum())
    hh = b.head_h
    L0 = max(b.hair_len, 0.012)
    style = b.hair_style
    down = np.array([0.0, 0.0, -1.0])
    back = np.array([0.0, -1.0, 0.0])
    segs = 4 if _hair_strand_budget(lod) >= 80 else 3
    for k in pick:
        i, j = int(ii[k]), int(jj[k])
        nrm = N[i, j]
        L = L0 * (0.08 + 0.17 * rr.u()) * (1.0 + 0.15 * rr.clipn(0.4, 1.0))
        wid = (0.0006 + 0.0013 * b.hair_vol) * (0.55 + rr.u()) * hh / 0.23
        p0 = P[i, j] + nrm * (wid * 0.4)
        flow = down * 0.62 + back * 0.38
        tang = flow - nrm * float(np.dot(flow, nrm))
        if np.linalg.norm(tang) < 1e-6:
            tang = back - nrm * float(np.dot(back, nrm))
        tang = tang / max(np.linalg.norm(tang), 1e-9)
        pts = [p0]
        d = tang * 0.965 + nrm * 0.035
        d = d / np.linalg.norm(d)
        for s in range(segs):
            g = (s + 1.0) / segs
            grav = down * (0.80 if style in ("long", "medium", "ponytail")
                           else 0.45) + back * 0.15
            curl = (0.55 if style == "curly" else 0.13)
            wob = np.array([rr.n(0, curl), rr.n(0, curl), rr.n(0, curl * 0.6)])
            d = d * (1.0 - 0.26 * g) + grav * (0.34 * g) + wob * 0.20
            d = d / max(np.linalg.norm(d), 1e-9)
            pts.append(pts[-1] + d * (L / segs))
        pts = np.array(pts)
        t = np.linspace(0.0, 1.0, 5)
        r = wid * np.array([1.0, 0.92, 0.74, 0.48, 0.16])
        sw = _tube_impl(pts, t, r, 5, int(rr.u() * 1e6), 0.80, 2.0,
                        smooth_r=wid * 1.5, noise_amp=0.0, noise_su=1,
                        noise_sv=1, twist=0.0, n_st=segs + 3)
        W = Sweep(O + np.einsum("ij,sj->si", B, sw.C),
                  np.einsum("ij,sjk->sik", B, sw.B), sw.LX, sw.LY)
        W.emit(mesh, mat, cap_end=True, zone=ZONE_SCALP)


def _bilerp_grid(A, fi, fj):
    """Bilinear sample of an (S, R, 3) grid at float (fi, fj), wrapping in j."""
    S, R = A.shape[0], A.shape[1]
    i0 = int(np.clip(math.floor(fi), 0, S - 1))
    i1 = min(i0 + 1, S - 1)
    ti = float(np.clip(fi - i0, 0.0, 1.0))
    j0 = int(math.floor(fj)) % R
    j1 = (j0 + 1) % R
    tj = float(fj - math.floor(fj))
    return ((A[i0, j0] * (1 - tj) + A[i0, j1] * tj) * (1 - ti)
            + (A[i1, j0] * (1 - tj) + A[i1, j1] * tj) * ti)


def _hair_strands(mesh, O, B, P, N, amt, m_cap, b, lod, seed, mat, n):
    """The broken EDGE of the mass -- wisps that lie along it, not pins in it.

    WHAT THE RENDER SHOWED, and it is why this was rewritten rather than tuned.
    In `render/faceab/face_base.png` at a 400 px head the strand layer is a
    REGULAR LATTICE OF DARK COMMAS across the whole dome -- rows and columns of
    them, evenly spaced, reading as a pin cushion or a scattering of flies.
    Three separate causes, all of them structural:

    * **The lattice.** Roots were `np.nonzero(amt > 0.02)`, i.e. GRID VERTICES,
      and 190 strands on a 33 x 14 grid is one on every other vertex. A random
      choice from a lattice is still on the lattice. Roots are now sampled at
      continuous (fi, fj) and the surface is bilinearly interpolated, so the
      grid is no longer visible in the distribution.

    * **The pin cushion.** Each tube left along the tangent and was immediately
      taken by gravity, so it stood clear of the mass along its whole length
      with sky behind it -- an isolated 3 px object, lit on one side, over a
      lit surface. Real flyaways HUG the mass for most of their length and only
      the last few millimetres leave it. `hug` keeps the first 60 % of the
      strand within a hair's breadth of the surface it grew from.

    * **The scatter.** They were independent draws, so no two agreed. Hair
      leaves in WISPS. Roots are now drawn as `clusters` of `per` neighbours
      sharing a direction and a length, which is also what makes them read at
      63 px, where an individual strand is 0.2 px and a wisp of six is 1.5.

    And they are moved OFF the dome and ONTO the boundary: `w_row` puts them at
    the hairline and at the tips of the fall, which are the only two places a
    strand can break an outline. A strand in the middle of a lit mass costs
    triangles and contributes nothing but noise.
    """
    rr = rng_for(seed, 137)
    S, R = amt.shape
    if S < 2 or n <= 0:
        return
    if HAIR_LEGACY:
        return _hair_strands_legacy(mesh, O, B, P, N, amt, b, lod, seed, mat, n)
    m_cap = int(m_cap if m_cap else S)
    # WHERE, in rows: a bump at the hairline (the cap's last row) and a ramp to
    # the tips, with a small floor everywhere so the dome is not bald of them.
    rows = np.arange(S, dtype=float)
    w_row = (0.05
             + 0.85 * np.exp(-((rows - (m_cap - 1)) / 1.4) ** 2)
             + 1.00 * np.clip((rows - (m_cap - 1))
                              / max(S - m_cap, 1.0), 0.0, 1.0) ** 2.0)
    w_row = w_row * (amt.mean(axis=1) > 0.02)
    if w_row.sum() <= 0:
        return
    w_row = w_row / w_row.sum()
    hh = b.head_h
    L0 = max(b.hair_len, 0.012)
    style = b.hair_style
    down = np.array([0.0, 0.0, -1.0])
    back = np.array([0.0, -1.0, 0.0])
    segs = 4 if _hair_strand_budget(lod) >= 80 else 3
    per = 6 if n >= 42 else 3
    clusters = max(1, int(n // per))
    for _c in range(clusters):
        ci = float(rr.r.choice(S, p=w_row)) + rr.u() - 0.5
        cj = rr.u() * R
        # ONE direction and ONE length for the whole wisp
        c_len = L0 * (0.10 + 0.26 * rr.u()) * (1.0 + 0.15 * rr.clipn(0.4, 1.0))
        c_wob = np.array([rr.n(0, 0.10), rr.n(0, 0.10), rr.n(0, 0.06)])
        for _s in range(per):
            fi = float(np.clip(ci + rr.n(0.0, 0.55), 0.0, S - 1.0))
            fj = cj + rr.n(0.0, 1.1)
            nrm = _bilerp_grid(N, fi, fj)
            nn = float(np.linalg.norm(nrm))
            if nn < 1e-9:
                continue
            nrm = nrm / nn
            base = _bilerp_grid(P, fi, fj)
            L = c_len * (0.75 + 0.50 * rr.u())
            # THINNER. A wisp is not a rod: 0.35-0.9 mm against the 0.7-1.9 mm
            # the shipped tubes carried, which at a 400 px head is 0.6-1.6 px
            # rather than 1.2-3.4 -- a soft fringe instead of a hard comma.
            wid = (0.00035 + 0.00055 * b.hair_vol) * (0.6 + 0.8 * rr.u()) \
                * hh / 0.23
            p0 = base + nrm * (wid * 0.5)
            flow = down * 0.62 + back * 0.38
            tang = flow - nrm * float(np.dot(flow, nrm))
            if np.linalg.norm(tang) < 1e-6:
                tang = back - nrm * float(np.dot(back, nrm))
            tang = tang / max(np.linalg.norm(tang), 1e-9)
            pts = [p0]
            d = tang * 0.99 + nrm * 0.01
            d = d / np.linalg.norm(d)
            for s in range(segs):
                g = (s + 1.0) / segs
                # HUG, THEN LEAVE. Gravity and wobble are gated by g^2, so the
                # root half of the strand stays along the surface and only the
                # tip departs from it.
                grav = down * (0.80 if style in ("long", "medium", "ponytail")
                               else 0.45) + back * 0.15
                curl = (0.55 if style == "curly" else 0.13)
                wob = c_wob + np.array([rr.n(0, curl * 0.35),
                                        rr.n(0, curl * 0.35),
                                        rr.n(0, curl * 0.20)])
                hug = g * g
                d = d * (1.0 - 0.30 * hug) + grav * (0.40 * hug) \
                    + wob * (0.30 * hug)
                d = d / max(np.linalg.norm(d), 1e-9)
                pts.append(pts[-1] + d * (L / segs))
            pts = np.array(pts)
            t = np.linspace(0.0, 1.0, 5)
            r = wid * np.array([1.0, 0.88, 0.66, 0.38, 0.10])
            sw = _tube_impl(pts, t, r, 4, int(rr.u() * 1e6), 0.80, 2.0,
                            smooth_r=wid * 1.5, noise_amp=0.0, noise_su=1,
                            noise_sv=1, twist=0.0, n_st=segs + 3)
            W = Sweep(O + np.einsum("ij,sj->si", B, sw.C),
                      np.einsum("ij,sjk->sik", B, sw.B), sw.LX, sw.LY)
            # A STRAND'S `hk_u` IS THE AZIMUTH IT GREW AT, NOT ITS OWN RING.
            # `Sweep.emit`'s default runs u 0..1 AROUND the tube, and
            # `hair_material` reads `hk_u` as the head's azimuth to place 61
            # lock bands on it -- so a 0.5 mm tube would carry all 61 of them
            # across its own diameter, which is per-pixel noise on a 1 px
            # object and is how the black commas got their contrast. Held
            # constant, a wisp takes the shade of the lock it came out of.
            uc = (fj % R) / float(R)
            if fi <= m_cap - 1:
                vr = 0.5 * fi / max(m_cap - 1.0, 1.0)
            else:
                vr = 0.5 + 0.5 * (fi - (m_cap - 1)) / max(S - m_cap, 1.0)
            W.emit(mesh, mat, cap_end=True, zone=ZONE_SCALP,
                   u0=uc, u1=uc, v0=float(np.clip(vr, 0.0, 1.0)),
                   v1=float(np.clip(vr + 0.12, 0.0, 1.0)))


# ===========================================================================
# 12b.  HELD PROPS -- defect 3, the half that headwear does not cover
# ===========================================================================
#
# "Zero props. No phones held up, no caps, no bags, no flags, no drinks, no
# cameras, no umbrellas, no scarves, no programmes. A real grandstand is dense
# with objects and HALF OF THEM ARE HELD IN HANDS."
#
# `build_headwear` covers what is WORN. Until this section existed nothing
# covered what is HELD -- and the pose table already had `phone_to_ear`,
# `phone_held_up`, `clipboard`, `radio_talk`, `carry_bag` and `sit_phone` in it,
# so six archetypes were posing a hand around thin air. At 767 px a hand curled
# around nothing is worse than a hand at rest, because the brain reads the
# intent and then finds the object missing.
#
# THE GRIP IS SOLVED, NOT STYLED. Each prop declares `grip_r`, the radius the
# fingers actually close on, and `build_hand(grip_r=...)` places every phalanx
# on a circle of that radius advancing by 2 asin(l / 2R). A hand on an 8 mm
# phone edge and a hand on a 33 mm bottle are then different hands rather than
# one hand at two scales.
#
# Dimensions are real objects measured in mm, because at 438 px/m (the 767 px
# peep) a phone is 64 x 32 px and its screen bezel is 1.3 px -- above the
# resolve threshold, so it has to be right rather than suggestive.

PROPS = {
    # name        w      h      d     grip_r  hand  weight  where
    "phone":     dict(dims=(0.0715, 0.1465, 0.0079), grip_r=0.011, w=0.34),
    "bottle":    dict(dims=(0.0655, 0.2100, 0.0655), grip_r=0.0330, w=0.20),
    "clipboard": dict(dims=(0.2300, 0.3200, 0.0060), grip_r=0.010, w=0.14),
    "radio":     dict(dims=(0.0560, 0.1120, 0.0330), grip_r=0.024, w=0.12),
    "programme": dict(dims=(0.1480, 0.2100, 0.0070), grip_r=0.010, w=0.10),
    # --- THE GRANDSTAND SET. The brief's defect 3 is "zero props ... a real
    # grandstand is dense with objects and half of them are held in hands",
    # and the five above are a PADDOCK's objects, not a crowd's. Every one of
    # these is measured off the real article.
    "flag":      dict(dims=(0.4600, 0.3000, 0.0090), grip_r=0.0105, w=0.10),
    "camera":    dict(dims=(0.1320, 0.0930, 0.0700), grip_r=0.0300, w=0.10),
    "binocular": dict(dims=(0.1250, 0.1400, 0.0560), grip_r=0.0250, w=0.06),
    "cup":       dict(dims=(0.0880, 0.1550, 0.0880), grip_r=0.0360, w=0.14),
    "none":      dict(dims=None, grip_r=None, w=0.10),
}
# Which archetypes REQUIRE something in the hand, and what.
POSE_PROP = {"phone_to_ear": "phone", "phone_held_up": "phone",
             "sit_phone": "phone", "clipboard": "clipboard",
             "radio_talk": "radio", "carry_bag": "bottle"}
PROP_ROLE_W = {
    "paddock":   (("phone", 0.30), ("clipboard", 0.16), ("radio", 0.16),
                  ("bottle", 0.14), ("programme", 0.04), ("none", 0.20)),
    "crew":      (("radio", 0.30), ("clipboard", 0.14), ("bottle", 0.16),
                  ("phone", 0.10), ("none", 0.30)),
    "marshal":   (("radio", 0.34), ("bottle", 0.10), ("none", 0.56)),
    # A GRANDSTAND IS NOT A PADDOCK. Frequencies from what a stand actually
    # holds: phones everywhere, a programme in every other lap, team flags in
    # the enthusiast blocks, a long lens here and there, drinks all afternoon.
    # Only 26 % of a stand is holding nothing.
    "spectator": (("phone", 0.28), ("programme", 0.15), ("flag", 0.09),
                  ("cup", 0.09), ("bottle", 0.07), ("camera", 0.04),
                  ("binocular", 0.02), ("none", 0.26)),
}


def _slab(mesh, O, B, w, h, d, mat, seed, r=0.004, rows=9, ring=16,
          zone=ZONE_SKIN, col=None):
    """A rounded rectangular solid in the hand's frame. Phones, boards, passes.

    The corner radius is what makes it an object rather than a cuboid: at 438
    px/m a 4 mm radius is 1.8 px of shading roll-off, which is the difference
    between a phone and a domino.
    """
    tt = np.linspace(-0.5, 0.5, rows)
    th = ring_theta(ring)
    # superellipse cross-section: exponent from the corner radius
    n = float(np.clip(2.0 * (0.5 * min(w, d) / max(r, 1e-4)) ** 0.5, 2.2, 9.0))
    c, s_ = np.cos(th), np.sin(th)
    k = (np.abs(c) ** n + np.abs(s_) ** n) ** (-1.0 / n)
    # taper the ends so the short edges round over too
    ta = np.sqrt(np.clip(1.0 - (2.0 * tt) ** 2 * (r / max(h, 1e-4)) * 4.0,
                         0.55, 1.0))
    LX = (0.5 * w * ta)[:, None] * (k * c)[None, :]
    LY = (0.5 * d * ta)[:, None] * (k * s_)[None, :]
    C = np.stack([O + B @ np.array([0.0, 0.0, h * u]) for u in tt])
    BB = np.repeat(B[None, :, :], rows, axis=0)
    Sweep(C, BB, LX, LY).emit(mesh, mat, cap_start=True, cap_end=True,
                              zone=zone, col=col)


#: WHAT A PROP IS MADE OF, and it is not what the person's HAT is made of.
#:
#: Defect 5, *"the flat props are conspicuous and samey: `phone` (28 %) and
#: `programme` (15 %) are both a pale flat slab, so 43 % of the block is
#: holding a bright rectangle against dark clothing"*, has a cause and it is
#: not the modelling. Every prop is emitted into `MAT_ACC`, and `hk_col` for
#: `MAT_ACC` is set once at the end of `build_figure` from
#: `w["headwear_rgb"]` -- so **a phone is the colour of that person's cap**.
#: With `#f2f0eb` (0.87 linear) in the headwear book, a phone in one hand and
#: a programme in the other are two white slabs, at the brightest value on the
#: figure, held out in front of dark clothing. Nothing was ever going to fix
#: that by adding geometry to the programme.
#:
#: These are LOCKED colours (`Mesh.add(col=...)`), which is the same mechanism
#: a livery panel uses to keep its own colour on a garment that shares its
#: material, so `colour_by_material` cannot repaint them.
PROP_COLS = {
    "phone":     ((0.012, 0.013, 0.016), 0.42),      # graphite
    "phone2":    ((0.055, 0.056, 0.060), 0.24),      # silver
    "phone3":    ((0.140, 0.130, 0.120), 0.20),      # champagne / rose
    "phone4":    ((0.020, 0.038, 0.075), 0.14),      # deep blue
    "programme": ((0.320, 0.075, 0.055), 0.30),      # printed cover
    "programme2": ((0.055, 0.090, 0.230), 0.26),
    "programme3": ((0.480, 0.400, 0.130), 0.22),
    "programme4": ((0.520, 0.520, 0.500), 0.22),     # newsprint
    "clipboard": ((0.190, 0.120, 0.060), 0.70),      # hardboard
    "clipboard2": ((0.030, 0.032, 0.036), 0.30),
    "radio":     ((0.014, 0.014, 0.016), 1.00),
    "bottle":    ((0.300, 0.330, 0.310), 0.55),      # pale PET
    "bottle2":   ((0.090, 0.110, 0.190), 0.25),
    "bottle3":   ((0.055, 0.048, 0.040), 0.20),
    "cup":       ((0.520, 0.500, 0.470), 0.55),
    "cup2":      ((0.230, 0.060, 0.045), 0.45),
    "camera":    ((0.011, 0.011, 0.013), 1.00),
    "binocular": ((0.013, 0.014, 0.016), 1.00),
    "flag":      ((0.330, 0.060, 0.050), 0.34),
    "flag2":     ((0.050, 0.110, 0.290), 0.33),
    "flag3":     ((0.520, 0.470, 0.100), 0.33),
}


def _prop_colour(kind, rr):
    """Pick from `PROP_COLS`' variants for `kind`. None if it has none."""
    cands = [(v[0], v[1]) for k, v in PROP_COLS.items()
             if k.rstrip("0123456789") == kind]
    if not cands:
        return None
    c = _pick_weighted(rr.u(), tuple(cands))
    j = 1.0 + rr.clipn(0.10, 0.26)
    return tuple(float(np.clip(x * j, 0.004, 0.72)) for x in c)


def _programme(mesh, O, B, w, h, d, mat, lod, rr, col):
    """A folded programme, not a slab: two leaves meeting at a spine, curled.

    Defect 5's other half. A race programme held in a hand is never flat -- it
    is a saddle-stitched booklet that has been rolled, so the free edge stands
    off the spine and the cover takes a cylindrical curl. That curl is the
    whole read: it puts a lit face and a shaded face on an object that as a
    slab has exactly one value, which is why 15 % of the block was holding an
    identical bright rectangle.
    """
    nu = max(7, lod.station + 3)
    nv = max(5, lod.station + 1)
    uu, vv = np.meshgrid(np.linspace(-1.0, 1.0, nu),
                         np.linspace(0.0, 1.0, nv), indexing="ij")
    curl = 0.30 + 0.55 * rr.u()
    open_a = 0.10 + 0.30 * rr.u()               # how far the leaves part
    # each leaf sweeps an arc away from the spine at u = 0
    a = np.abs(uu) * curl
    x = 0.5 * w * np.sign(uu) * np.sin(a) / np.maximum(a, 1e-6) * np.abs(uu)
    y = -0.5 * w * open_a * (1.0 - np.cos(a)) - 0.5 * d * np.sign(uu) * 0.0
    # the pages sag along the height, more toward the free edge
    z = h * (vv - 0.5) + 0.010 * (uu ** 2) * (vv - 0.35)
    P = np.stack([x, y, z], axis=-1)
    Pw = O[None, None, :] + np.einsum("ij,uvj->uvi", B, P)
    emit_grid(mesh, Pw, mat, closed_u=False, col=col)
    # the spine, so the two leaves are one object and not two loose sheets
    _slab(mesh, O, B, 0.006, h * 0.99, max(d, 0.004), mat, 0, r=0.0018,
          rows=4, ring=8, col=col)


def build_prop(mesh, sk, side, b, lod, seed, kind, mats):
    """Place `kind` in the `side` hand. Returns the grip radius to pose it on.

    Returns None for "none", so the caller can tell "no prop" from "a prop of
    radius zero" -- which matters because `build_hand(grip_r=0)` would collapse
    every finger onto the palm.
    """
    spec = PROPS.get(kind)
    if not spec or spec["dims"] is None:
        return None
    if not lod.props:
        return None                      # L3: below 60 px a phone is 1.7 px
    w, h, d = spec["dims"]
    O = sk.origin["hand_" + side]
    B = sk.basis["hand_" + side]
    sgn = +1.0 if side == "R" else -1.0
    rr = rng_for(seed, 91 + (0 if side == "R" else 1))
    pt = 0.155 * b.hand_len * (1.0 + 0.14 * (b.girth - 1.0))
    pl = 0.545 * b.hand_len
    # against the palm (-Y is the palm side; see build_hand's thenar offset),
    # centred a little past mid-palm where the fingers actually close
    off = np.array([sgn * 0.02 * b.hand_len,
                    -(0.5 * pt + 0.5 * d + 0.0015),
                    0.62 * pl])
    tilt = _euler(rr.n(0.0, 5.0), sgn * rr.n(0.0, 4.0), rr.n(0.0, 6.0))
    Bp = B @ tilt
    Op = O + B @ off
    ac, sc = mats.get("acc", MAT_ACC), mats.get("shoe", MAT_SHOE)
    pcol = _prop_colour(kind, rr)

    if kind in ("phone", "programme", "clipboard"):
        if kind == "programme":
            _programme(mesh, Op, Bp, w, h, d, ac, lod, rr, pcol)
        else:
            _slab(mesh, Op, Bp, w, h, d, ac, seed,
                  r=0.006 if kind != "clipboard" else 0.003,
                  rows=9 if kind != "clipboard" else 7,
                  ring=max(12, lod.ring - 10), col=pcol)
        if kind == "phone":
            # the screen, inset 1.2 mm -- a black slab with no screen reads as
            # a bar of soap at any distance where the phone reads at all
            _slab(mesh, Op + Bp @ np.array([0.0, -0.5 * d - 0.0003, 0.0]), Bp,
                  w - 0.0062, h - 0.0125, 0.0012, mats.get("eye", MAT_EYE),
                  seed, r=0.0035, rows=5, ring=12, col=(0.008, 0.009, 0.012))
        if kind == "clipboard":
            # the sheet stack, then the spring clip across the head
            _slab(mesh, Op + Bp @ np.array([0.0, -0.5 * d - 0.0009, -0.004]),
                  Bp, w - 0.012, h - 0.020, 0.0016, ac, seed, r=0.001,
                  rows=5, ring=10, col=(0.560, 0.550, 0.525))
            _slab(mesh, Op + Bp @ np.array([0.0, -0.5 * d - 0.0035,
                                            0.5 * h - 0.021]),
                  Bp, 0.062, 0.030, 0.0075, sc, seed, r=0.003, rows=4,
                  ring=12, col=(0.115, 0.120, 0.128))
    elif kind == "bottle":
        # a revolved profile: base, body, shoulder, neck, cap -- 7 stations, so
        # the shoulder is a curve and not a chamfer
        prof_t = np.array([0.00, 0.05, 0.62, 0.74, 0.82, 0.88, 1.00])
        prof_r = np.array([0.72, 1.00, 1.00, 0.86, 0.46, 0.44, 0.50])
        rows = max(9, lod.station + 4)
        tt = np.linspace(0.0, 1.0, rows)
        rad = np.interp(tt, prof_t, prof_r) * 0.5 * w
        # neck rings, 0.9 mm proud -- 0.4 px at the peep, and they catch the sun
        rad = rad + 0.0009 * (np.sin(tt * 62.0) > 0.6) * (tt > 0.84)
        th = ring_theta(max(14, lod.ring - 6))
        LX = rad[:, None] * np.cos(th)[None, :]
        LY = rad[:, None] * np.sin(th)[None, :]
        C = np.stack([Op + Bp @ np.array([0.0, 0.0, h * (u - 0.42)])
                      for u in tt])
        BB = np.repeat(Bp[None, :, :], rows, axis=0)
        Sweep(C, BB, LX, LY).emit(mesh, ac, cap_start=True, cap_end=True,
                                  col=pcol)
    elif kind == "radio":
        _slab(mesh, Op, Bp, w, h, d, sc, seed, r=0.005, rows=7,
              ring=max(12, lod.ring - 10), col=pcol)
        # antenna: a 118 mm stub, 5 mm at the root and 3 at the tip
        rows = 5
        tt = np.linspace(0.0, 1.0, rows)
        rad = 0.0025 - 0.0010 * tt
        th = ring_theta(8)
        LX = rad[:, None] * np.cos(th)[None, :]
        LY = rad[:, None] * np.sin(th)[None, :]
        base = Op + Bp @ np.array([0.30 * w, 0.0, 0.5 * h])
        C = np.stack([base + Bp @ np.array([0.0, 0.0, 0.118 * u]) for u in tt])
        BB = np.repeat(Bp[None, :, :], rows, axis=0)
        Sweep(C, BB, LX, LY).emit(mesh, sc, cap_start=True, cap_end=True,
                                  col=(0.020, 0.020, 0.022))
        # speaker grille: three proud bars, 1.5 mm, on the front face
        for i in range(3):
            _slab(mesh, Op + Bp @ np.array([0.0, -0.5 * d - 0.0006,
                                            0.24 * h + 0.010 * i]),
                  Bp, w * 0.60, 0.0042, 0.0015, sc, seed, r=0.0008,
                  rows=3, ring=8, col=(0.020, 0.020, 0.022))
    elif kind == "flag":
        # A STAFF AND A CLOTH THAT IS NOT FLAT. A flag rendered as a rectangle
        # is a signboard; what makes it read is that the free edge is longer
        # than the luff, so the panel takes a travelling wave. Emitted as a
        # grid, with the amplitude ramped from 0 at the staff to full at the
        # fly, which is exactly how a real flag behaves and costs nothing.
        _prop_rod(mesh, Op, Bp, np.array([0.0, 0.0, 1.0]), 0.560, 0.0045,
                  sc, lod, lift=-0.16, col=(0.170, 0.130, 0.080))
        nu = max(9, 2 * lod.station + 3)
        nv = max(6, lod.station + 2)
        uu, vv = np.meshgrid(np.linspace(0.0, 1.0, nu),
                             np.linspace(0.0, 1.0, nv), indexing="ij")
        ph = rr.u(0.0, TAU)
        amp = 0.055 * uu ** 1.5
        yv = amp * np.sin(uu * 7.4 + vv * 2.1 + ph)
        # the fly edge sags: a hanging flag is not a plane
        sag = -0.030 * uu ** 2 * (1.0 - 0.35 * vv)
        P = np.stack([w * uu, yv, 0.24 + h * (vv - 0.5) + sag], axis=-1)
        Pw = Op[None, None, :] + np.einsum("ij,uvj->uvi", Bp, P)
        emit_grid(mesh, Pw, ac, closed_u=False, col=pcol)
    elif kind == "camera":
        # body, then a lens barrel with a hood -- the barrel is the whole read
        # at any distance where a camera reads at all
        _slab(mesh, Op, Bp, w, h, d, sc, seed, r=0.008, rows=7,
              ring=max(12, lod.ring - 10), col=pcol)
        _slab(mesh, Op + Bp @ np.array([0.0, 0.0, 0.5 * h + 0.008]), Bp,
              0.036, 0.016, 0.030, sc, seed, r=0.004, rows=4, ring=10,
              col=pcol)
        _prop_rod(mesh, Op + Bp @ np.array([0.0, -0.5 * d, -0.004]), Bp,
                  np.array([0.0, -1.0, 0.0]), 0.098, 0.0355, sc, lod,
                  taper=1.10, lift=0.0, col=(0.014, 0.014, 0.016))
        _prop_rod(mesh, Op + Bp @ np.array([0.0, -0.5 * d - 0.098, -0.004]),
                  Bp, np.array([0.0, -1.0, 0.0]), 0.020, 0.0385, ac, lod,
                  taper=1.0, lift=0.0, col=(0.009, 0.009, 0.010))
    elif kind == "binocular":
        for sx in (-1.0, +1.0):
            _prop_rod(mesh, Op + Bp @ np.array([sx * 0.032, 0.0, 0.0]), Bp,
                      np.array([0.0, -1.0, 0.0]), h, 0.0245, sc, lod,
                      taper=1.14, lift=-0.5 * h, col=pcol)
        _slab(mesh, Op, Bp, 0.064, 0.030, 0.026, sc, seed, r=0.004,
              rows=4, ring=10, col=pcol)
    elif kind == "cup":
        # a tapered cup with a rolled rim -- the rim is 1.4 mm proud and is
        # the only thing that separates a cup from a cone at 260 px
        rows = max(6, lod.station + 2)
        tt = np.linspace(0.0, 1.0, rows)
        rad = 0.5 * w * (0.62 + 0.38 * tt)
        rad = rad + 0.0014 * (tt > 0.93)
        th = ring_theta(max(12, lod.ring - 8))
        LX = rad[:, None] * np.cos(th)[None, :]
        LY = rad[:, None] * np.sin(th)[None, :]
        C = np.stack([Op + Bp @ np.array([0.0, 0.0, h * (u - 0.40)])
                      for u in tt])
        Sweep(C, np.repeat(Bp[None, :, :], rows, axis=0), LX, LY).emit(
            mesh, ac, cap_start=True, cap_end=True, col=pcol)
    return float(spec["grip_r"])


def _prop_rod(mesh, O, B, axis, length, rad, mat, lod, taper=1.0, lift=0.0,
              col=None):
    """A capped cylinder in a hand frame: flag staff, lens barrel, binocular."""
    rows = max(4, lod.station)
    tt = np.linspace(0.0, 1.0, rows)
    r = rad * (1.0 + (taper - 1.0) * tt)
    th = ring_theta(max(8, lod.ring - 12))
    a = np.asarray(axis, float)
    a = a / max(np.linalg.norm(a), 1e-12)
    C = np.stack([O + B @ (a * (lift + length * u)) for u in tt])
    Sweep(C, np.repeat(B[None, :, :], rows, axis=0),
          r[:, None] * np.cos(th)[None, :],
          r[:, None] * np.sin(th)[None, :]).emit(
              mesh, mat, cap_start=True, cap_end=True, col=col)


def build_headwear(mesh, sk, b, lod, seed, kind, mat, legacy=False,
                   hair_thick=0.0, wear=0.0):
    """cap / beanie / bucket / visor as a clean dome of revolution over the skull.

    NOT a row-slice of the head grid. The first build cut the head's own (u, v)
    grid at a per-column contour, and because a grid can only be cut on whole
    rows the brim came out as a stepped, torn edge with loose triangles hanging
    off it -- clearly visible in a clay render and invisible to every number.
    A dome built on its own polar grid has an exact circular hem by construction.
    """
    if kind in (None, "none"):
        return
    O = sk.origin["head"]
    B = sk.basis["head"]
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    rr = rng_for(seed, 149)
    zc, ax, ay, az = 0.16 * hh, 0.5 * hw, 0.5 * hd, 0.50 * hh
    yc = -0.06 * hd
    # THE CLEARANCE HAS TO CLEAR THE HAIR UNDER IT. See `build_hair`: the mass
    # is (8 + 30 x hair_vol) mm, up to 39 mm, and a flat 6 mm gap buried the cap
    # crown inside it on every capped figure in the A3 face render.
    gap = ((0.010 if kind == "beanie" else 0.006) * hh / 0.23
           + 1.06 * float(hair_thick))
    # THE HEM IS NOT A LATITUDE. A hat sits above the brow at the FRONT and
    # comes down over the occiput and the ears at the BACK -- a cap band is
    # level with the brow and its back edge is 40 mm lower, a beanie covers the
    # ears entirely. The first version used one latitude all the way round, so
    # a beanie's front edge sat 37 mm BELOW the eyes: measured by
    # `headwear_clearance_mm`, and visible in the bench render as a blindfold.
    #                 front   back
    if legacy:
        # THE POSITIVE CONTROL, kept verbatim: one latitude all the way round
        # and a peak pinned at z = 0.075 * head_h. `headwear_clearance_mm`
        # must report this on the face.
        HEM = {"cap": (0.30, 0.30), "beanie": (-0.26, -0.26),
               "bucket": (0.14, 0.14), "visor": (0.40, 0.40)}[kind]
    else:
        HEM = {"cap":    (0.290, 0.060),
               "beanie": (0.150, -0.340),
               "bucket": (0.245, 0.020),
               "visor":  (0.320, 0.320)}[kind]
    # THE GRID HAS TO BE ABLE TO HOLD A SEAM. It was `2 * head_u // 3` -- 48
    # columns at L0, 10 mm apart on a 478 mm crown -- and defect 4 is "no
    # six-panel seams, no button, no crown break", i.e. exactly the features
    # that live at 3-8 mm. Putting a 3 mm ridge on a 10 mm grid is the sampling
    # failure `FACE_LOBE_FLOOR` documents, one object along. 96 columns at L0
    # is 5.0 mm and 58 at L1 is 8.2 mm, and the seam width is floored to the
    # spacing below rather than declared in millimetres.
    n = max(28, 4 * lod.head_u // 3)
    m = max(8, lod.head_v // 3)
    ph = np.linspace(0.0, TAU, n, endpoint=False)
    frontness = 0.5 + 0.5 * np.sin(ph)                   # 1 at the face, 0 aft
    hem_col = HEM[1] + (HEM[0] - HEM[1]) * frontness
    hem_fz = float(HEM[0])
    th_hi_col = np.arccos(np.clip(hem_col, -0.98, 0.98))
    th_hi = float(np.arccos(np.clip(hem_fz, -0.98, 0.98)))
    # SAME POLE TRAP AS `build_hair`, one line different. The floor was a
    # FRACTION of the front column's th_hi, so a column whose own hem sits
    # higher (`beanie` aft, HEM[1] = -0.34 against +0.15) started at a
    # proportionally smaller theta, and on a `visor` -- HEM (0.40, 0.40),
    # th_hi 1.16 rad -- ring 0 landed inside 3.6 mm of the pole where the
    # crown's own relief is larger than the ring radius. Measured: 4 exactly
    # zero-area triangles on 9 of 20 hatted figures. The floor is now an
    # ABSOLUTE theta, so every column's ring 0 has a real radius whatever its
    # own hem does.
    th_lo = 0.13                                   # rad; ~12 mm on a crown
    i_ = np.linspace(1.0, float(m), m)[:, None] / float(m)
    TH = th_lo + (th_hi_col[None, :] - th_lo) * i_
    TH = np.clip(TH, 0.0, th_hi_col[None, :])
    PH = np.broadcast_to(ph[None, :], TH.shape)
    fx = np.sin(TH) * np.cos(PH)
    fy = np.sin(TH) * np.sin(PH)
    fz = np.cos(TH)
    grow0 = 1.0 + gap / max(0.5 * hw, 1e-6)
    grow = grow0
    if kind == "beanie":
        # RIBBING, at a wavelength the grid can hold and an amplitude that is
        # knitwear rather than corrugation. `sin(PH * 9)` was 9 ribs round a
        # 478 mm crown -- a 53 mm rib, which is a pumpkin, not a hat -- and the
        # turn-up, which is the one thing that says "beanie" at any distance,
        # did not exist at all. 26 ribs is 18 mm, 5.6 px at the film's biggest
        # head, and the turn-up is a doubled band at the hem.
        rib = 0.0022 * np.cos(PH * 26.0) * np.clip(np.sin(TH), 0.0, 1.0)
        turn = np.clip((TH - (th_hi_col[None, :] - 0.30)) / 0.30, 0.0, 1.0)
        grow = grow + (rib + 0.0060 * turn ** 1.5) / max(0.5 * hw, 1e-6)
    elif kind in ("cap", "bucket"):
        # SIX PANELS, A CROWN BREAK AND A BUTTON -- defect 4, "the caps still
        # read as hard hats: a smooth dome, no six-panel seam, no button".
        #
        # A cap is six wedges of twill joined by a topstitched seam, and the
        # seams are the whole read: they run from the button to the hem, they
        # catch the sun as six bright lines on a dome that would otherwise
        # have one highlight, and each panel bulges slightly between them so
        # the crown is a hexagonal dome rather than a sphere. The front seam
        # sits on the centre line (`ph = pi/2` is the face here) so a cap seen
        # head-on shows a seam down the middle, which is what a cap does.
        s6 = 3.0 * (PH - math.pi / 2.0)
        # angular distance to the nearest seam meridian, as an ARC in metres,
        # so the ridge is a constant physical width up the dome instead of
        # pinching to nothing at the crown
        d_ang = np.abs(((s6 + math.pi / 2.0) % math.pi) - math.pi / 2.0) / 3.0
        r_loc = np.maximum(ax * np.sin(TH), 1e-4)
        seam_w = max(1.15 * TAU * ax / n, 0.0035)
        seam = np.exp(-((d_ang * r_loc) / seam_w) ** 2)
        panel = np.sin(s6) ** 2
        # both fade out at the pole, where six seams are one point
        fade = np.clip(np.sin(TH) / math.sin(0.45), 0.0, 1.0)
        crown = (0.0016 * seam + 0.0014 * panel) * fade
        # THE CROWN BREAK: a structured cap stands up at the front and slopes
        # away to the back. A hemisphere is a hard hat, and that is the word
        # the defect report uses.
        crown = crown + (0.0075 if kind == "cap" else 0.0030) \
            * np.clip(np.sin(PH), 0.0, 1.0) ** 1.4 * np.clip(
                1.0 - TH / max(float(th_hi), 1e-6), 0.0, 1.0) ** 0.8
        grow = grow + crown / max(0.5 * hw, 1e-6)
    px = fx * ax * grow
    py = yc + fy * ay * grow * (1.0 - 0.14 * np.clip(-fz, 0, 1) ** 1.6)
    pz = zc + fz * az * grow
    P = np.stack([px, py, pz], axis=-1)
    # a real hem: the last two rows roll outward and back up, so the brim has a
    # sunward lip and a lee shadow instead of being a zero-thickness edge
    roll = np.clip((np.arange(m) - (m - 3)) / 2.0, 0.0, 1.0)[:, None]
    P[..., 0] += fx * (0.0035 * roll)
    P[..., 1] += fy * (0.0035 * roll)
    P[..., 2] -= 0.0030 * roll
    apex = np.array([0.0, yc, zc + az * grow if np.isscalar(grow) else zc + az])
    W = O + np.einsum("ij,srj->sri", B, P)
    emit_grid(mesh, W, mat, closed_u=True, cap_lo=O + B @ apex,
              wear=float(wear))
    if kind == "cap":
        # THE BUTTON. 12 mm across and 5 mm proud, which is 3.7 x 1.6 px at the
        # film's biggest head -- small, and the one detail that is unambiguous
        # about what the object is. It is where the six panels meet, so it has
        # to sit exactly on the apex the dome was closed at.
        _button(mesh, O, B, apex, ax, az, grow0, lod, mat)
    if kind in ("cap", "visor", "bucket"):
        # THE PEAK ATTACHES TO THE HEM THIS DOME ACTUALLY HAS. It used to be
        # placed at hard-coded head-frame coordinates and the 767 px bench
        # render showed why that cannot work: the root sat at z = 0.075 h_h,
        # which is BELOW the eyes at 0.140 h_h, and the droop took the tip to
        # -0.030 m -- under the chin. Every capped figure had a coloured wedge
        # across its mouth and a band over its eyes. Found by looking, not by
        # any number in the file.
        z_hem = zc + hem_fz * az * grow0
        y_hem = yc + ay * float(np.sin(th_hi)) * grow0
        if legacy:
            y_hem, z_hem = 0.5 * hd * 0.30 + 0.012, 0.075 * hh
        _peak(mesh, O, B, b, lod, kind, rr, mat, y_hem, z_hem,
              droop=(0.24 if legacy else None))


def _button(mesh, O, B, apex, ax, az, grow0, lod, mat):
    """The fabric-covered button at the crown of a six-panel cap.

    A squashed hemisphere sitting on the apex, closed with a pole fan, built on
    its own grid for the same reason `build_headwear` is: cutting one out of
    the dome's grid means cutting on whole rows.
    """
    n = max(10, lod.head_u // 4)
    m = max(3, lod.head_v // 10)
    r = 0.0060
    h = 0.0050
    ph = np.linspace(0.0, TAU, n, endpoint=False)
    th = np.linspace(math.pi * 0.5, 0.0, m + 1)[:-1]      # rim -> pole
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    P = np.stack([r * np.sin(TH) * np.cos(PH),
                  r * np.sin(TH) * np.sin(PH),
                  h * np.cos(TH)], axis=-1)
    P = P + np.asarray(apex, float)[None, None, :]
    top = np.asarray(apex, float) + np.array([0.0, 0.0, h])
    emit_grid(mesh, O + np.einsum("ij,srj->sri", B, P), mat, closed_u=True,
              cap_hi=O + B @ top)


def _peak(mesh, O, B, b, lod, kind, rr, mat, y_hem, z_hem, droop=None):
    """A cap peak: a curved plate 3.5 mm thick with a closed edge all round.

    A cap peak projects ~70 mm on a 197 mm-deep head. The first build reached
    165 mm and rendered as a duck bill; it was also an open sheet, so its rim
    was a zero-thickness line that a raking sun turns into an aliasing artefact.

    `y_hem` / `z_hem` are the front of the crown's own hem ring, so the peak
    starts where the band ends instead of at an invented height.
    """
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    n = max(11, lod.ring - 6)
    m = 5
    a = np.linspace(-1.0, 1.0, n)
    t = np.linspace(0.0, 1.0, m)
    A, T = np.meshgrid(a, t, indexing="ij")
    reach = (0.36 if kind != "bucket" else 0.26) * hd
    wid = 0.46 * hw
    # A peak drops ~25 mm over a 70 mm reach -- about 20 deg, not 50. The old
    # 0.24 * head_depth was 47 mm of droop on a 71 mm reach.
    droop = droop if droop is not None else (0.115 if kind != "visor"
                                            else 0.150)
    x = A * wid * (1.0 - 0.30 * T ** 2)
    y = y_hem - 0.012 + T * reach
    z = z_hem - droop * hd * T ** 1.7 - 0.032 * hd * A ** 2 * T
    top = np.stack([x, y, z], axis=-1)
    bot = top - np.array([0.0, 0.0, 0.0035])
    # one closed strip: down one side, back along the other, so the rim exists
    G = np.concatenate([top[::-1], bot], axis=0)
    W = O + np.einsum("ij,srj->sri", B, G)
    emit_grid(mesh, W, mat, closed_u=False)
    # Rim band closing the two sheets along the outer edge. It used to be a
    # CLOSED strip of (loop, loop-with-the-halves-swapped), which is the same
    # pair of points in both rows at the two joins -- two exactly zero-area
    # quads, i.e. FOUR degenerate triangles on the peak of every capped figure,
    # and the wrap quad on top of that. A strip from the top edge to the bottom
    # edge is what a 3.5 mm plate rim actually is.
    edge = np.stack([top[:, -1], bot[:, -1]])
    emit_grid(mesh, O + np.einsum("ij,srj->sri", B, edge), mat, closed_u=False)


# ===========================================================================
# 12c.  THE COVERED TIER -- pit crew: helmet, visor, balaclava, gloves, boots
# ===========================================================================
#
# The manifest calls `crew_figure` "completely covered -- helmet, visor,
# balaclava, fireproofs, gloves -- zero exposed skin", 120 of them, and
# `screen_presence.json` measures the family at a peak SHARP **551.8 px**
# (`peak_sharp_px_4k`, frame 956) with a minimum depth of **7.602 m**. This
# comment said 767.2 px / 7.537 m until 2026-08-03; the depth was close but the
# pixel figure was a pre-shutter-fix RAMPED number that survived R2-037 and
# overstates the covered tier's macro resolve by 39 %. See the file header.
# The brief is blunt about what that means:
#
#   "Covered does not mean easy: it means fabric, seams, folds, equipment and
#    posture carry the entire read."
#
# So there is no face to hide behind and nothing to spend the budget on except
# the things a covered figure IS. Concretely, and each one is a thing the
# rejected build did not have:
#
#   * a ONE-PIECE overall, not a shirt tucked into trousers. The waist of a
#     race suit is a seam and a belt loop tape, not a hem over a waistband, and
#     the difference is obvious in a silhouette;
#   * a full-length front ZIP with a real welt, a mandarin collar, a yoke seam
#     across the shoulders, elbow and knee panels with their own seams, and
#     elasticated cuffs at both wrist and ankle;
#   * a HELMET with a recessed visor aperture, so the aperture has a lip and a
#     lee shadow instead of being a painted band, and a separate visor plate in
#     that recess on a glossy tinted material;
#   * GLOVES, which are the hand geometry inflated by a real 2.4 mm of Nomex
#     with a gauntlet cuff over the sleeve -- not the sleeve stopping at a
#     stump;
#   * BOOTS with a shaft above the ankle, so the trouser cuff has something to
#     sit on instead of ending in mid-air above a slipper.

OVERALL = dict(sleeve=0.985, hem=-0.2399, ease=0.019, collar="stand",
               stiff=0.92, lam=0.115, leg=0.985, cuff=0.030, rise=0.34)
GLOVE_MM = 2.4                 # Nomex + suede palm, measured on a real glove


def _livery_welts(shell, tt, livery, part, height=0.0022):
    """Raised seams on the VERTICAL colour boundaries of a livery pattern.

    A colour edge inside a quad is a soft edge -- a garment ring carries only
    `lod.ring` columns, so one column is 40 mm on the chest, 17 px at the crew
    tier's framing. A real panelled suit has a SEAM at every colour change, and
    a 2.2 mm welt under a 12.47 deg sun is the strongest line on the garment.
    So the geometry supplies the edge the colour interpolation cannot.
    """
    if livery is None:
        return np.zeros((shell.S, shell.R))
    pat = livery["pattern"]
    d = np.zeros((shell.S, shell.R))
    if part == "trunk" and pat == "sides":
        for u in (0.25 - 0.215, 0.25 - 0.115, 0.25 + 0.115, 0.25 + 0.215):
            d = d + _ridge(shell, tt, u % 1.0, 0.006, height)
    elif part in ("sleeve", "leg") and pat in ("sides", "chevron"):
        for u in (0.15, 0.35):
            d = d + _ridge(shell, tt, u, 0.006, height)
    return d


def build_overall(mesh, sw_t, t_t, arms, legs, sk, b, lod, seed, spec, mat,
                  wear=0.0, livery=None):
    """A one-piece fireproof overall: trunk, sleeves, legs, collar, zip.

    ONE SHELL from below the seat to the acromion, so there is no hem at the
    waist. What marks the waist instead is what marks it on a real suit: a
    seam, slightly cinched, with the fabric blousing a little above it.
    """
    ease = spec.get("ease", 0.030)
    shell, tt = garment_from_sweep(sw_t, t_t, seed + 101, spec, -0.2399, 1.0001,
                                   drape=0.95)
    S = shell.S
    d = np.zeros((S, shell.R))
    iv = np.asarray(tt, float)

    def band(centre, width):
        return np.exp(-0.5 * ((iv - centre) / width) ** 2)[:, None]

    # the waist: a seam that stands proud with the cloth cinched under it
    d = d - 0.0055 * band(0.315, 0.030)
    d = d + 0.0030 * band(0.345, 0.014)
    # the yoke seam across the shoulders, and a chest panel edge
    d = d + 0.0022 * band(0.845, 0.013)
    if lod.seams:
        d = d + _ridge(shell, tt, 0.00, 0.006, 0.0018)      # side seams
        d = d + _ridge(shell, tt, 0.50, 0.006, 0.0018)
        # THE ZIP. A full-length welt up the front, wider and taller than a
        # placket because a zip has a tape either side of it and a slider on it.
        d = d + _ridge(shell, tt, 0.25, 0.0075, 0.0032)
        d = d + _ridge(shell, tt, 0.2365, 0.0030, 0.0016)
        d = d + _ridge(shell, tt, 0.2635, 0.0030, 0.0016)
        d = d + _livery_welts(shell, tt, livery, "trunk")
    shell = shell.offset(d)
    _emit_livery_sweep(mesh, shell, tt, mat, wear, livery, "trunk")
    cap_col = None
    if livery is not None:
        bands = _livery_bands(livery, "trunk")
        cap_col = (livery["accent"] if bands[-1][2] else livery["base"])
    emit_grid(mesh, shoulder_cap(shell, sk, b, rows=max(3, lod.station),
                                 r_neck=b.neck_r * 1.10 + 0.24 * ease),
              mat, closed_u=True, wear=wear, col=cap_col,
              vv=np.repeat(np.linspace(1.0, 1.25, max(3, lod.station) + 1),
                           shell.R))
    build_collar(mesh, sk, b, lod, seed, dict(spec, collar="stand"), mat,
                 ease, wear, col=cap_col)
    # SPONSOR PANELS. Raised patches -- a real 1.4 mm of stitched-on cloth with
    # the team's own mark on it -- on the chest, the back and the right thigh,
    # which is where a race suit actually carries them.
    if livery is not None and lod.seams:
        for (u, v, w_, h_, ms) in ((0.25, 0.700, 0.060, 0.038, 0.052),
                                   (0.75, 0.655, 0.072, 0.046, 0.062),
                                   (0.25, 0.130, 0.044, 0.030, 0.040)):
            P0, N, T1, T2 = _garment_frame(shell, tt, u, v)
            _helm_pad(mesh, _O3, _I3, P0, N, T1, T2, w_, h_, 0.0016, mat,
                      col=livery["trim"], cols=20, expo=8.0, rows=2,
                      foot=0.0003)
            _mark_geometry(mesh, _O3, _I3, P0 + N * 0.0014, N, T1, T2,
                           livery["mark"], ms, mat, livery["trim"],
                           accent=_contrasting(livery, livery["trim"]),
                           lift=0.0013)

    for side in ("L", "R"):
        sw_a, t_a = arms[side]
        flex = _flex_along(sk, ("arm_" + side, "fore_" + side), t_a)
        slv, ta = garment_from_sweep(sw_a, t_a, seed + 211 + ord(side), spec,
                                     0.0, 0.985, flex=flex, drape=1.05)
        dd = _cuff_profile(slv, gather=0.0030, band=0.0026, rows=3)
        if lod.seams:
            dd = dd + _ridge(slv, ta, 0.50, 0.007, 0.0016)
            # elbow panel: a seam ring either side of the joint
            ep = np.asarray(ta, float)
            dd = dd + 0.0016 * np.exp(
                -0.5 * ((ep - 0.42) / 0.022) ** 2)[:, None]
            dd = dd + 0.0016 * np.exp(
                -0.5 * ((ep - 0.60) / 0.022) ** 2)[:, None]
            dd = dd + _livery_welts(slv, ta, livery, "sleeve", 0.0018)
        slv = slv.offset(dd)
        # CAP THE CUFF. The overall's sleeve was emitted as an OPEN TUBE at the
        # wrist, and the 767 px bench render shows a pink sliver of forearm
        # skin inside it, above the gauntlet, on every crew figure -- 0.24 % of
        # the visible surface, all of it at hip height, which is exactly where
        # the eye is. A real elasticated cuff closes on the wrist.
        _emit_livery_sweep(mesh, slv, ta, mat, wear, livery, "sleeve")
        sleeve_head(mesh, slv, sk, side, b, lod, mat, wear=wear)

        sw_l, t_l = legs[side]
        flexl = _flex_along(sk, ("hip_" + side, "knee_" + side), t_l)
        trs, tl = garment_from_sweep(sw_l, t_l, seed + 401 + ord(side), spec,
                                     0.0, 0.985, flex=flexl, drape=1.10)
        dl = _cuff_profile(trs, gather=0.0035, band=0.0030, rows=3)
        if lod.seams:
            dl = dl + _ridge(trs, tl, 0.00, 0.006, 0.0018)
            dl = dl + _ridge(trs, tl, 0.50, 0.006, 0.0018)
            # KNEE PANEL -- a padded rectangle over the front of the knee, the
            # one piece of a race suit that is unmistakably a race suit.
            kp = np.asarray(tl, float)
            along = np.exp(-0.5 * ((kp - 0.505) / 0.055) ** 2)[:, None]
            uu = np.linspace(0.0, 1.0, trs.R, endpoint=False)
            front = np.exp(-0.5 * ((((uu - 0.25) + 0.5) % 1.0 - 0.5)
                                   / 0.155) ** 2)[None, :]
            dl = dl + 0.0042 * along * front
            for kc in (0.455, 0.555):
                dl = dl + 0.0018 * np.exp(
                    -0.5 * ((kp - kc) / 0.012) ** 2)[:, None] * front
            dl = dl + _livery_welts(trs, tl, livery, "leg", 0.0018)
        trs = trs.offset(dl)
        _emit_livery_sweep(mesh, trs, tl, mat, wear, livery, "leg")
        sleeve_head(mesh, trs, sk, side, b, lod, mat, wear=wear, bulge=0.06,
                    toward=sk.origin["pelvis"],
                    depth=max(0.30 * b.hip_half, 0.045))


def _cuff_profile(sw, gather=0.003, band=0.0026, rows=3):
    """A cuff that reads as a cuff: gathered IN, then a band standing OUT.

    The shipped profile was a single outward Gaussian on the last two rings,
    and the 767 px bench render showed what that is -- a hard cylindrical
    flange standing off the end of the sleeve like a cast. A real elasticated
    cuff pulls the cloth IN over ~30 mm and then the band itself stands a
    couple of millimetres proud of that, so there are two edges and the light
    finds both.
    """
    S = sw.S
    i = np.arange(S)[:, None]
    gat = np.exp(-0.5 * ((i - (S - 1 - rows)) / max(rows * 0.55, 0.6)) ** 2)
    bnd = np.exp(-0.5 * ((i - (S - 1)) / 1.05) ** 2)
    return -float(gather) * gat + float(band) * bnd


def build_glove(mesh, sk, side, b, lod, seed, mat, cuff_mat=None, grip=0.15,
                grip_r=None):
    """The hand, inflated by real glove thickness, with a gauntlet cuff.

    A glove is not a mitten and it is not a bare hand tinted black: it is the
    same hand 2.4 mm bigger everywhere, with the fingers slightly fatter and
    less separated, and a stiff cuff that sits OVER the sleeve rather than
    under it -- which is the detail that says "fireproof" at 767 px.
    """
    t = GLOVE_MM * 1e-3 * (0.85 + 0.30 * (b.hand_len / 0.190))
    build_hand(mesh, sk, side, b, lod, seed, grip=grip, grip_r=grip_r,
               mat=mat, thick=t)
    # the gauntlet: a short flared tube up the forearm from the wrist
    O = sk.origin["hand_" + side]
    B = sk.basis["hand_" + side]
    ring = max(10, lod.ring - 6)
    th = ring_theta(ring)
    rows = 4
    L = 0.052 * (b.forearm / 0.255)
    r0 = b.wrist_r * 1.16 + t
    out = []
    for i in range(rows):
        f = i / (rows - 1.0)
        r = r0 * (1.0 + 0.30 * f ** 1.4)
        LX = r * np.cos(th)
        LY = r * 0.86 * np.sin(th)
        C = O + B @ np.array([0.0, 0.0, -L * f])
        out.append(C[None, :] + (np.cos(th)[:, None] * (B[:, 0] * r)[None, :]
                                 + np.sin(th)[:, None]
                                 * (B[:, 1] * r * 0.86)[None, :]))
        _ = (LX, LY)
    emit_grid(mesh, np.stack(out), cuff_mat if cuff_mat is not None else mat,
              closed_u=True, zone=ZONE_BELT)


# ---------------------------------------------------------------------------
# THE HELMET. Rebuilt because the first one was an EGG.
#
# The shipped version was an ellipsoid plus six Gaussian lobes of 2.3-6.8 mm
# amplitude, with the eyeport as an 8 mm dent. At the crew tier's 767 px --
# 438 px/m, 2.28 mm per pixel -- a 2.3 mm crown "spine" is ONE pixel and a
# 6.8 mm "chin bar" is three: nothing in that table could have made a helmet
# shape, and the B2 bench render shows exactly what it made, a smooth white egg
# with a dark band. A pit-crew helmet at 10-30 m is a hero silhouette and the
# features that say "helmet" rather than "head" are large:
#
#     chin bar projecting past the face        35-45 mm    15-20 px
#     rear aero spoiler                        18-24 mm     8-11 px
#     eyeport recess + its rim bead            9 mm + 4 mm  4 + 2 px
#     crown intake scoops                      8 mm proud, 34 x 26 mm footprint
#     visor pivot bosses                       6 mm proud, 34 mm across
#
# and the shell itself is BIGGER than a head: 237 mm across the ears against a
# 161 mm skull, which is most of why a helmeted figure reads as helmeted at a
# distance where no vent is resolvable.
#
# Everything below is a displacement of a direction field, so it is evaluable
# at an ARBITRARY direction, which is what lets the vents and the pivots be
# placed on the finished surface instead of guessed at on the ellipsoid.

HELM_SHAPE = {
    "shell_x": 0.038,      # added to the half-head width, metres
    "shell_y": 0.030,
    # THE CROWN IS A SPHERE, NOT AN EGG. One ellipsoid centred low on the head
    # gives a vertical semi-axis 23 % longer than the horizontal one, and B4
    # shows exactly that: a helmet that comes to a rounded POINT at the top.
    # The centre is raised into the cranium and the semi-axis is split above and
    # below it, so the crown is spherical (ratio 0.99) while the shell still
    # closes 35 mm below the chin.
    "shell_zc": 0.280,     # x head_h, above the occipital condyle
    "shell_up": 0.026,     # clearance over the vertex
    "shell_dn": 0.035,     # clearance under the chin
    "chin": 0.042,         # forward projection of the chin bar
    "brow": 0.013,
    "spoiler": 0.021,      # rearward projection of the aero lip
    "jaw": 0.013,          # how much the shell narrows below the ear
    "nape": 0.012,
    "port_e0": 0.10,       # eyeport centre, in fz
    "port_he": 0.27,       # eyeport half-height, in fz
    "port_ha": 1.28,       # eyeport half-width, in radians of azimuth
    "port_depth": 0.0090,
    "port_bead": 0.0040,
}


def _helm_dir(TH, PH):
    return (np.sin(TH) * np.cos(PH), np.sin(TH) * np.sin(PH), np.cos(TH))


def _helm_P(TH, PH, b, s=HELM_SHAPE, port=True):
    """The helmet surface at (polar, azimuth), in HEAD-LOCAL coordinates.

    +y is forward, +z up, azimuth pi/2 is dead ahead. Written as a function of
    direction rather than as a grid so `_helm_frame` can evaluate it -- and its
    tangents -- wherever a vent or a pivot has to sit.
    """
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    fx, fy, fz = _helm_dir(TH, PH)
    ax = 0.5 * hw + s["shell_x"]
    ay = 0.5 * hd + s["shell_y"]
    zc, yc = s["shell_zc"] * hh, -0.040 * hd
    az_up = (0.665 * hh - zc) + s["shell_up"]     # clears the vertex
    az_dn = (zc + 0.345 * hh) + s["shell_dn"]     # closes below the chin
    w = np.clip((fz + 0.28) / 0.56, 0.0, 1.0)
    w = w * w * (3.0 - 2.0 * w)
    az = az_dn + (az_up - az_dn) * w
    P = np.stack([fx * ax, yc + fy * ay, zc + fz * az], axis=-1)
    N = np.stack([fx / ax, fy / ay, fz / az], axis=-1)
    N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-12)
    fwd = np.clip(fy, 0.0, 1.0)
    bak = np.clip(-fy, 0.0, 1.0)
    lat = np.exp(-0.5 * (fx / 1.02) ** 2)
    # THE CHIN BAR -- the single feature that makes a full-face helmet read as
    # one. A forward wall below the eyeport that wraps under the jaw.
    chin = (np.exp(-0.5 * ((fz + 0.54) / 0.32) ** 2) * fwd ** 0.55 * lat
            / (1.0 + np.exp((fz + 0.16) * 14.0)))
    P[..., 1] += s["chin"] * chin
    # the brow band above the port, and a shallow centre spine over the crown
    P[..., 1] += s["brow"] * np.exp(-0.5 * ((fz - 0.44) / 0.20) ** 2) \
        * fwd ** 1.1 * lat
    P[..., 2] += 0.006 * np.exp(-0.5 * (fx / 0.16) ** 2) \
        * np.clip(fz, 0.0, 1.0) ** 1.4
    # THE REAR SPOILER -- an aero lip across the occiput with a hard lower edge
    sp = (np.exp(-0.5 * ((fz - 0.02) / 0.24) ** 2) * bak ** 1.1
          * np.exp(-0.5 * (fx / 1.25) ** 2)
          / (1.0 + np.exp(-(fz + 0.34) * 16.0)))
    P[..., 1] -= s["spoiler"] * sp
    # the shell narrows below the ear, and the neck roll swells at the nape
    P[..., 0] -= (s["jaw"] * np.sign(fx) * np.abs(fx) ** 1.4
                  * np.clip(-fz - 0.10, 0.0, 1.0) ** 0.8)
    P[..., 1] -= s["nape"] * bak ** 1.6 \
        * np.exp(-0.5 * ((fz + 0.72) / 0.26) ** 2)
    if not port:
        return P
    # THE EYEPORT. A letterbox in (azimuth, elevation), recessed, with a raised
    # bead round its rim: two real edges across the widest part of the helmet,
    # which under a 12.47 deg sun is the strongest shading event on the figure.
    ang = np.arctan2(fx, np.maximum(fy, 1e-6))
    ang = np.where(fy > 0.0, ang, np.sign(ang) * math.pi)
    q = np.sqrt(((fz - s["port_e0"]) / s["port_he"]) ** 2
                + (ang / s["port_ha"]) ** 2)
    rec = 1.0 / (1.0 + np.exp((q - 0.92) * 22.0))
    bead = np.exp(-0.5 * ((q - 1.10) / 0.09) ** 2)
    P += N * (s["port_bead"] * bead - s["port_depth"] * rec)[..., None]
    return P


def _helm_frame(TH, PH, b, s=HELM_SHAPE):
    """Surface point and an orthonormal (normal, along-azimuth, along-polar)."""
    e = 2e-3
    P = _helm_P(TH, PH, b, s)
    T1 = (_helm_P(TH, PH + e, b, s) - P) / e
    T2 = (_helm_P(TH + e, PH, b, s) - P) / e
    N = np.cross(T1, T2)
    N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-12)
    T1 = T1 / np.maximum(np.linalg.norm(T1, axis=-1, keepdims=True), 1e-12)
    T2 = np.cross(N, T1)
    return P, N, T1, T2


def _helm_pad(mesh, O, B, P0, N, T1, T2, hw_, hh_, lift, mat, col=None,
              rows=3, cols=20, expo=3.0, tilt=0.0, zone=0.0, foot=0.0004):
    """A rounded-rect pad standing off the shell: vent, boss, patch or panel.

    A polar grid on a superellipse footprint, so it is ONE closed piece with a
    pole at its centre and a flat top with a steep wall over the outer fifth.
    `lift` negative makes it a recess -- a vent mouth, an exhaust slot.
    `foot` keeps the rim a few tenths of a millimetre off the shell so the two
    surfaces are never coplanar, which is what z-fights in a render.
    """
    th = ring_theta(cols)
    c, sn = np.cos(th), np.sin(th)
    k = (np.abs(c) ** expo + np.abs(sn) ** expo) ** (-1.0 / expo)
    out = []
    for i in range(rows + 1):
        r = (i + 1) / float(rows + 1)
        z = float(lift) * min(1.0, (1.0 - r) / 0.30) + foot
        loc = (P0[None, :] + T1[None, :] * (hw_ * r * k * c)[:, None]
               + T2[None, :] * (hh_ * r * k * sn)[:, None]
               + N[None, :] * z
               + T2[None, :] * (tilt * z))
        out.append(loc)
    G = np.stack(out[::-1])                       # outer ring first
    ctr = P0 + N * (float(lift) + foot) + T2 * (tilt * (lift + foot))
    emit_grid(mesh, O + np.einsum("ij,srj->sri", B, G), mat, closed_u=True,
              cap_hi=O + B @ ctr, col=col, zone=zone)


# ---------------------------------------------------------------------------
# BRAND MARKS AS GEOMETRY. Law 2: the world already has 31 invented brands, and
# `build_dressing` draws their marks -- chevron, ring, bars, delta, hex, wing,
# bolt, diamond -- as flat artwork on the trackside boards. The SAME vocabulary
# is used here so a team's crew, its truck and its board carry one identity.
#
# They are geometry, not a texture: each part is a closed pad standing 1.5-2 mm
# off the cloth, which is what `item_gate` check 7 is asking for -- a sunward
# lip and a lee shadow rather than "a single-value mark ... how a printed decal
# behaves and not how a physical object does". A printed logo is also exactly
# what the brief forbids: no downloaded logos, no photo textures.
#
# Each part is (dx, dy, hw, hh, rot_deg, expo, cols, use_accent), in units of
# the mark's own size. `expo` is the superellipse exponent -- 4 is a rectangle,
# 2 an ellipse, and 3 columns at any exponent is a triangle.
_MK_RECT, _MK_TRI, _MK_DISC = 4.0, 3.0, 2.0
MARK_PARTS = {
    "chevron": [(-0.20, +0.16, 0.07, 0.26, -34, _MK_RECT, 8, 1),
                (-0.20, -0.16, 0.07, 0.26, +34, _MK_RECT, 8, 1),
                (+0.16, +0.16, 0.07, 0.26, -34, _MK_RECT, 8, 1),
                (+0.16, -0.16, 0.07, 0.26, +34, _MK_RECT, 8, 1)],
    "delta":   [(0.0, -0.06, 0.46, 0.44, 0, _MK_TRI, 3, 1)],
    "hex":     [(0.0, 0.0, 0.46, 0.46, 30, _MK_DISC, 6, 1)],
    "diamond": [(0.0, 0.0, 0.40, 0.52, 0, _MK_TRI, 4, 1),
                (0.0, 0.0, 0.17, 0.23, 0, _MK_TRI, 4, 0)],
    "ring":    [(0.0, 0.0, 0.46, 0.46, 0, _MK_DISC, 16, 1),
                (0.0, 0.0, 0.27, 0.27, 0, _MK_DISC, 14, 0),
                (0.0, 0.0, 0.06, 0.58, 0, _MK_RECT, 6, 1)],
    "mono":    [(0.0, 0.0, 0.48, 0.48, 0, _MK_DISC, 16, 1),
                (0.0, 0.0, 0.34, 0.34, 0, _MK_DISC, 14, 0)],
    "bars":    [(-0.26, 0.0, 0.09, 0.42, 12, _MK_RECT, 8, 1),
                (0.00, 0.0, 0.09, 0.42, 12, _MK_RECT, 8, 1),
                (+0.26, 0.0, 0.09, 0.42, 12, _MK_RECT, 8, 1)],
    "wing":    [(-0.06, +0.22, 0.42, 0.07, 0, _MK_RECT, 8, 1),
                (+0.02, +0.02, 0.34, 0.07, 0, _MK_RECT, 8, 1),
                (+0.10, -0.18, 0.26, 0.07, 0, _MK_RECT, 8, 1)],
    "bolt":    [(-0.10, +0.20, 0.10, 0.28, +26, _MK_RECT, 8, 1),
                (+0.10, -0.20, 0.10, 0.28, +26, _MK_RECT, 8, 1)],
    "shield":  [(0.0, +0.12, 0.40, 0.30, 0, _MK_RECT, 8, 1),
                (0.0, -0.24, 0.40, 0.26, 180, _MK_TRI, 3, 1)],
    "grid":    [(-0.20, +0.20, 0.16, 0.16, 0, _MK_RECT, 6, 1),
                (+0.20, +0.20, 0.16, 0.16, 0, _MK_RECT, 6, 1),
                (-0.20, -0.20, 0.16, 0.16, 0, _MK_RECT, 6, 1),
                (+0.20, -0.20, 0.16, 0.16, 0, _MK_RECT, 6, 1)],
    "wave":    [(0.0, +0.20, 0.46, 0.07, 8, _MK_RECT, 8, 1),
                (0.0, 0.00, 0.46, 0.07, -8, _MK_RECT, 8, 1),
                (0.0, -0.20, 0.46, 0.07, 8, _MK_RECT, 8, 1)],
    "arcs":    [(-0.10, -0.16, 0.50, 0.10, 22, _MK_RECT, 8, 1),
                (0.02, +0.02, 0.40, 0.10, 22, _MK_RECT, 8, 1),
                (0.14, +0.20, 0.30, 0.10, 22, _MK_RECT, 8, 1)],
    "drop":    [(0.0, -0.14, 0.34, 0.34, 0, _MK_DISC, 14, 1),
                (0.0, +0.24, 0.24, 0.30, 0, _MK_TRI, 3, 1)],
    "mount":   [(0.0, -0.10, 0.50, 0.42, 0, _MK_TRI, 3, 1)],
    "arch":    [(0.0, +0.10, 0.46, 0.36, 0, _MK_DISC, 14, 1),
                (0.0, -0.26, 0.46, 0.16, 0, _MK_RECT, 6, 1)],
    "crest":   [(0.0, +0.14, 0.36, 0.32, 0, _MK_RECT, 8, 1),
                (0.0, -0.26, 0.36, 0.26, 180, _MK_TRI, 3, 1),
                (0.0, +0.04, 0.20, 0.07, 0, _MK_RECT, 6, 0)],
}


def _rot2(T1, T2, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return T1 * c + T2 * s, -T1 * s + T2 * c


def _mark_geometry(mesh, O, B, P0, N, T1, T2, kind, size, mat, back_col,
                   accent=None, lift=0.0016, zone=0.0):
    """A brand mark, as a stack of closed pads standing off a surface."""
    parts = MARK_PARTS.get(kind) or MARK_PARTS["delta"]
    acc = back_col if accent is None else accent
    for (dx, dy, hw_, hh_, rot, expo, cols, use_acc) in parts:
        A, Bt = _rot2(T1, T2, rot)
        c = acc if use_acc else back_col
        z = lift * (1.0 if use_acc else 1.55)
        _helm_pad(mesh, O, B, P0 + T1 * (dx * size) + T2 * (dy * size), N,
                  A, Bt, hw_ * size, hh_ * size, z, mat, col=c,
                  cols=int(cols), expo=float(expo), rows=2, zone=zone,
                  foot=0.0002)


# ---------------------------------------------------------------------------
# TEAM LIVERY. Defect: "overalls are flat single colours -- no team graphics,
# sponsor panels or contrasting shoulders."
#
# A race suit is PANELLED: separate pieces of Nomex in different colours, sewn
# together, with the seam standing proud at every colour change. So the livery
# here is not a texture painted on one shell. The horizontal bands -- yoke,
# waist, sleeve, cuff -- are emitted as their OWN ring sections of the same
# sweep, which means the colour boundary falls exactly on a ring and is zero
# pixels wide. The vertical zones -- side panels, the flanks of the zip -- are
# per-vertex colour with a raised welt on the boundary, because a ring carries
# only `lod.ring` columns and a colour edge inside a quad is a soft edge; the
# welt is a real 2 mm seam and it is what the eye reads as the line.
LIVERY_PATTERNS = ("yoke", "shoulders", "sash", "sides", "blocks", "chevron")


def livery_for_team(brand, seed=0):
    """One team's identity, from itemkit's ONE brand book (Law 2)."""
    if brand is None:
        return None
    name, bg, fg = brand[0], brand[1], brand[2]
    base = K.srgb_linear(bg)
    accent = K.srgb_linear(fg)
    # A POLYNOMIAL HASH OF THE WHOLE NAME, not sum(ord(c)). The sum collides
    # freely -- 11 of the 31 brands landed on the same pattern with it, which is
    # this project's own "one tree spammed 100 times" in a new costume.
    key = 0
    for ch in name:
        key = (key * 131 + ord(ch)) & 0x0FFFFFFF
    h = hash01(int(seed), 7717, key)
    pat = LIVERY_PATTERNS[int(h * len(LIVERY_PATTERNS)) % len(LIVERY_PATTERNS)]
    lum = 0.2126 * base[0] + 0.7152 * base[1] + 0.0722 * base[2]
    trim = (0.86, 0.855, 0.83) if lum < 0.22 else (0.045, 0.045, 0.05)
    return {"team": name, "base": base, "accent": accent, "trim": trim,
            "mark": brand[3], "pattern": pat, "tier": brand[4]}


def _contrasting(livery, on):
    """Whichever of the team's two colours reads against `on`.

    A mark drawn in the team accent on a near-white sponsor patch is yellow on
    white -- 2 % contrast, and B4 shows it as a blank blob. Pick by luminance.
    """
    def lum(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    a, bs, o = livery["accent"], livery["base"], lum(on)
    return a if abs(lum(a) - o) > abs(lum(bs) - o) else bs


def _livery_zone_cols(livery, uu, vv, part):
    """Per-vertex colour for the VERTICAL zones of one garment piece.

    Returns (N,3) or None. `uu` is the turn around the body (0.25 is dead
    ahead, where the zip is) and `vv` the parameter along the sweep.
    """
    if livery is None:
        return None
    base = np.broadcast_to(np.asarray(livery["base"], float),
                           (len(uu), 3)).copy()
    acc = np.asarray(livery["accent"], float)
    pat = livery["pattern"]
    du = np.abs((uu - 0.25 + 0.5) % 1.0 - 0.5)          # distance from front
    if part == "trunk":
        if pat == "sides":
            base[(du > 0.115) & (du < 0.215)] = acc
        elif pat == "sash":
            base[np.abs(0.72 * (du - 0.10) + (vv - 0.62)) < 0.075] = acc
        elif pat == "chevron":
            base[np.abs(du * 1.35 - (0.86 - vv)) < 0.070] = acc
        elif pat == "blocks":
            base[(vv > 0.36) & (vv < 0.60) & (du < 0.20)] = acc
    elif part in ("sleeve", "leg") and pat in ("sides", "chevron"):
        base[du < 0.10] = acc
    return base


def _livery_bands(livery, part):
    """(t0, t1, use_accent) sections a garment sweep is emitted in.

    A band is its OWN ring section, so the colour edge is exactly a ring and is
    ZERO pixels wide. The bounds are in the sweep's OWN parameter -- for the
    trunk that runs -0.24 (below the seat) to 1.00 (the acromion), so a yoke is
    t > 0.82 and a waist block is 0.10..0.36. B4 was built with these read as a
    0..1 fraction of the sweep and put the "shoulder" band across the lower
    ribs, which is what the render showed.
    """
    if livery is None:
        return None
    pat = livery["pattern"]
    if part == "trunk":
        if pat == "yoke":
            return ((-0.24, 0.82, 0), (0.82, 1.01, 1))
        if pat == "shoulders":
            return ((-0.24, 0.70, 0), (0.70, 0.93, 1), (0.93, 1.01, 0))
        if pat == "blocks":
            return ((-0.24, 0.10, 0), (0.10, 0.36, 1), (0.36, 1.01, 0))
        return ((-0.24, 1.01, 0),)
    if part == "sleeve":
        return ((0.0, 0.30, 1), (0.30, 1.01, 0)) if pat in (
            "yoke", "shoulders", "blocks") else ((0.0, 0.70, 0),
                                                 (0.70, 0.84, 1),
                                                 (0.84, 1.01, 0))
    if part == "leg":
        return ((0.0, 1.01, 0),) if pat != "blocks" else ((0.0, 0.60, 0),
                                                          (0.60, 0.72, 1),
                                                          (0.72, 1.01, 0))
    return ((0.0, 1.01, 0),)


def _emit_livery_sweep(mesh, sw, tt, mat, wear, livery, part, uu=None):
    """Emit a garment sweep in its livery bands, with per-vertex zone colour."""
    S, R = sw.S, sw.R
    u1d = np.linspace(0.0, 1.0, R, endpoint=False)
    bands = _livery_bands(livery, part) or ((-1e9, 1e9, 0),)
    v = np.asarray(tt, float)
    for (v0, v1, acc) in bands:
        i0 = int(np.clip(np.searchsorted(v, v0), 0, S - 2))
        i1 = int(np.clip(np.searchsorted(v, v1) + 1, i0 + 2, S))
        sub = sw.slice(i0, i1)
        n = (i1 - i0) * R
        uuf = np.tile(u1d, i1 - i0)
        vvf = np.repeat(v[i0:i1], R)
        if livery is None:
            col = None
        elif acc:
            col = np.broadcast_to(np.asarray(livery["accent"], float),
                                  (n, 3)).copy()
        else:
            col = _livery_zone_cols(livery, uuf, vvf, part)
        sub.emit(mesh, mat, cap_start=(i0 == 0 and part == "trunk"),
                 cap_end=(i1 == S and part in ("sleeve", "leg")),
                 wear=wear, v0=float(tt[i0]), v1=float(tt[i1 - 1]), col=col)


_I3 = np.eye(3)
_O3 = np.zeros(3)


def _garment_frame(sw, tt, u, v):
    """Point and tangent frame on a garment shell at (turn u, parameter v)."""
    t = np.asarray(tt, float)
    i = int(np.clip(np.searchsorted(t, v), 1, sw.S - 2))
    j = int(round(float(u) * sw.R)) % sw.R
    V = sw.verts()
    P0 = V[i, j]
    T1 = V[i, (j + 1) % sw.R] - V[i, (j - 1) % sw.R]
    T2 = V[i + 1, j] - V[i - 1, j]
    N = np.cross(T1, T2)
    nn = float(np.linalg.norm(N))
    nm = sw.normals2d()[i, j]
    out = sw.B[i] @ np.array([nm[0], nm[1], 0.0])
    N = (N / nn) if nn > 1e-12 else out
    if float(np.dot(N, out)) < 0.0:
        N = -N
    T1 = T1 / max(float(np.linalg.norm(T1)), 1e-12)
    T2 = np.cross(N, T1)
    return P0, N, T1, T2


def build_helmet(mesh, sk, b, lod, seed, shell_mat, visor_mat, trim_mat,
                 open_visor=False, livery=None):
    """A full-face helmet: shell, chin bar, spoiler, eyeport, visor, vents.

    THE APERTURE IS A RECESS, not a painted band. `item_gate` check 7 asks
    whether a feature has a sunward lip and a lee shadow or is "a single-value
    mark ... how a printed decal behaves and not how a physical object does",
    and 21 of 28 wave-1 items failed it.
    """
    O = sk.origin["head"]
    B = sk.basis["head"]
    s = HELM_SHAPE
    # The grid has to resolve the eyeport rim: 64 columns is 5.6 deg, 12 mm at
    # the shell radius, so the bead spans two samples and the recess wall one.
    n = int(np.clip(lod.head_u, 20, 64))
    m = int(np.clip(lod.head_v * 3 // 4, 12, 38))
    th = np.linspace(0.028, math.pi - 0.028, m)
    ph = np.linspace(0.0, TAU, n, endpoint=False)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    P = _helm_P(TH, PH, b, s)
    W = O + np.einsum("ij,srj->sri", B, P)
    top = O + B @ _helm_P(np.array(0.0), np.array(0.0), b, s, port=False)
    bot = O + B @ _helm_P(np.array(math.pi), np.array(0.0), b, s, port=False)
    emit_grid(mesh, W, shell_mat, closed_u=True, cap_lo=top, cap_hi=bot,
              uu=(PH / TAU).ravel(), vv=(TH / math.pi).ravel())

    # ---- the visor plate, filling the recess -----------------------------
    fx, fy, fz = _helm_dir(TH, PH)
    ang = np.arctan2(fx, np.maximum(fy, 1e-6))
    ang = np.where(fy > 0.0, ang, np.sign(ang) * math.pi)
    q = np.sqrt(((fz - s["port_e0"]) / s["port_he"]) ** 2
                + (ang / s["port_ha"]) ** 2)
    sel = (q < 0.94) & (fy > 0.0)
    rows_ = np.where(sel.any(axis=1))[0]
    if len(rows_) >= 2:
        cols_ = np.where(sel.any(axis=0))[0]
        roll = (-int(cols_.min()) if (cols_.max() - cols_.min()) < n - 1
                else -int(np.where(~sel.any(axis=0))[0][0]))
        selr = np.roll(sel, roll, axis=1)
        cr = np.where(selr.any(axis=0))[0]
        r0, r1 = int(rows_.min()), int(rows_.max()) + 1
        c0, c1 = int(cr.min()), int(cr.max()) + 1
        THr = np.roll(TH, roll, axis=1)[r0:r1, c0:c1]
        PHr = np.roll(PH, roll, axis=1)[r0:r1, c0:c1]
        Pv = _helm_P(THr, PHr, b, s, port=False)
        Nv = _helm_P(THr, PHr + 2e-3, b, s, port=False) - Pv
        Nv = np.cross(Nv, _helm_P(THr + 2e-3, PHr, b, s, port=False) - Pv)
        Nv = Nv / np.maximum(np.linalg.norm(Nv, axis=-1, keepdims=True), 1e-12)
        # closed, the visor sits 3.5 mm inside the shell line; flipped up it
        # stands 25 mm proud of it and the recess is open underneath
        lift = (-0.0035) if not open_visor else (+0.0250)
        Vp = Pv + Nv * lift
        emit_grid(mesh, O + np.einsum("ij,srj->sri", B, Vp), visor_mat,
                  closed_u=False)

    # ---- vents, pivots, trim ---------------------------------------------
    # A vent is a raised scoop with a DARK RECESSED MOUTH in front of it, in two
    # pieces, because a scoop with no hole in it is a blister.
    def at(ang_deg, ele):
        """Frame at an azimuth measured from dead ahead and an elevation fz."""
        a = math.radians(ang_deg)
        t = math.acos(float(np.clip(ele, -1.0, 1.0)))
        p = math.pi / 2.0 - a
        return _helm_frame(np.array(t), np.array(p), b, s)

    if lod.seams:
        for sgn in (-1.0, +1.0):
            P0, N, T1, T2 = at(sgn * 26.0, 0.70)             # crown intakes
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.017, 0.014, 0.0085,
                      shell_mat, cols=16, expo=2.6, tilt=0.55)
            P0, N, T1, T2 = at(sgn * 26.0, 0.585)
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.015, 0.006, -0.0060,
                      trim_mat, cols=14, expo=4.0, zone=ZONE_BELT)
            P0, N, T1, T2 = at(sgn * 172.0, 0.10)            # rear exhausts
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.010, 0.019, -0.0055,
                      trim_mat, cols=14, expo=4.0, zone=ZONE_BELT)
            # THE VISOR PIVOT: the boss the visor turns on, at the port's end
            P0, N, T1, T2 = at(sgn * 74.0, s["port_e0"])
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.019, 0.019, 0.0055,
                      trim_mat, cols=16, expo=2.0, zone=ZONE_BELT)
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.008, 0.008, 0.0085,
                      shell_mat, cols=12, expo=2.0)
        # the chin vent: a recessed mouth with three bars across it
        P0, N, T1, T2 = at(0.0, -0.60)
        _helm_pad(mesh, O, B, P0, N, T1, T2, 0.026, 0.011, -0.0060,
                  trim_mat, cols=16, expo=4.0, zone=ZONE_BELT)
        for k in (-1, 0, 1):
            Pb = P0 + T1 * (k * 0.0125)
            _helm_pad(mesh, O, B, Pb, N, T1, T2, 0.0026, 0.0100, -0.0018,
                      shell_mat, cols=8, expo=4.0, rows=2)

    # ---- team livery ------------------------------------------------------
    if livery is not None:
        acc = livery["accent"]
        # a centre stripe fore-and-aft over the crown, in the accent colour
        for j, ele in enumerate(np.linspace(0.30, 0.99, 5)):
            P0, N, T1, T2 = at(0.0, float(ele))
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.020, 0.026, 0.0009,
                      shell_mat, col=acc, cols=12, expo=4.0, rows=2)
        for sgn in (-1.0, +1.0):
            P0, N, T1, T2 = at(sgn * 118.0, 0.30)
            _helm_pad(mesh, O, B, P0, N, T1, T2, 0.030, 0.020, 0.0009,
                      shell_mat, col=acc, cols=14, expo=3.0, rows=2)
            _mark_geometry(mesh, O, B, P0 + N * 0.0016, N, T1, T2,
                           livery["mark"], 0.024, shell_mat, livery["base"])

    # ---- the bottom trim: a rolled neck edge, not a hem -------------------
    thb = np.array([math.pi - 0.028, math.pi - 0.090, math.pi - 0.150])
    THb, PHb = np.meshgrid(thb, ph, indexing="ij")
    Pb = _helm_P(THb, PHb, b, s, port=False)
    Nb = Pb - np.array([0.0, Pb[..., 1].mean(), Pb[..., 2].mean()])[None, None, :]
    Nb = Nb / np.maximum(np.linalg.norm(Nb, axis=-1, keepdims=True), 1e-12)
    roll_ = np.array([0.0, 0.0035, 0.0060])[:, None, None]
    emit_grid(mesh, O + np.einsum("ij,srj->sri", B, Pb + Nb * roll_),
              trim_mat, closed_u=True, zone=ZONE_BELT)


def build_balaclava(mesh, sk, b, lod, seed, mat):
    """A Nomex balaclava: the head, offset 1.6 mm, closed under the chin.

    It is under the helmet and mostly invisible, and it is built anyway,
    because the 15-20 mm of it that shows at the neck and the eye aperture is
    exactly where a helmet meets a person, and a helmet floating on bare skin
    is the tell.
    """
    P, _zone, _f, (TH, PH), _soft = head_points(b, lod, seed)
    O = sk.origin["head"]
    B = sk.basis["head"]
    ctr = np.array([0.0, -0.05 * b.head_d, 0.14 * b.head_h])
    D = P - ctr[None, None, :]
    D = D / np.maximum(np.linalg.norm(D, axis=-1, keepdims=True), 1e-12)
    Q = P + D * 0.0016
    W = O + np.einsum("ij,srj->sri", B, Q)
    top = O + B @ np.array([0.0, -0.06 * b.head_d, 0.665 * b.head_h])
    chin = O + B @ np.array([0.0, -0.06 * b.head_d, -0.345 * b.head_h])
    emit_grid(mesh, W, mat, closed_u=True, cap_lo=top, cap_hi=chin,
              uu=(PH / TAU).ravel(), vv=(TH / math.pi).ravel())
    # the neck skirt: a short tube down from the jawline, tucked into the collar
    ring = max(12, lod.ring - 4)
    th = ring_theta(ring)
    Bn = sk.basis["neck"]
    nb = sk.origin["head"]
    out = []
    for i in range(4):
        f = i / 3.0
        r = b.neck_r * (1.05 + 0.10 * f)
        z = -b.neck_len * (0.10 + 0.62 * f)
        out.append(nb[None, :]
                   + np.cos(th)[:, None] * (Bn[:, 0] * r)[None, :]
                   + np.sin(th)[:, None] * (Bn[:, 1] * r * 1.14)[None, :]
                   + Bn[None, :, 2] * z)
    emit_grid(mesh, np.stack(out), mat, closed_u=True)


def build_headset(mesh, sk, b, lod, seed, shell_mat, pad_mat):
    """Ear defenders with a headband and a boom mic. Garage crew, not helmets."""
    O = sk.origin["head"]
    B = sk.basis["head"]
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    ring = max(10, lod.ring - 8)
    th = ring_theta(ring)
    for sgn in (-1.0, +1.0):
        cx = sgn * (0.5 * hw + 0.004)
        cz = 0.10 * hh
        cy = -0.06 * hd
        rows = 4
        out = []
        for i in range(rows):
            f = i / (rows - 1.0)
            r = 0.030 * (1.0 - 0.22 * f ** 2)
            x = cx + sgn * 0.030 * f
            out.append(np.stack([np.full(ring, x),
                                 cy + r * np.cos(th) * 1.10,
                                 cz + r * np.sin(th)], axis=1))
        G = np.stack(out)
        emit_grid(mesh, O + np.einsum("ij,srj->sri", B, G), shell_mat,
                  closed_u=True,
                  cap_hi=O + B @ np.array([cx + sgn * 0.032, cy, cz]))
        _ = pad_mat
    # the headband: a strip over the crown between the two cups
    m = 9
    a = np.linspace(-1.0, 1.0, m)
    pts = np.stack([a * (0.5 * hw + 0.020),
                    np.full(m, -0.055 * hd),
                    0.10 * hh + (1.0 - a ** 2) * 0.62 * hh], axis=1)
    r = np.array([0.0062] * m)
    sw = _tube_impl(pts, np.linspace(0, 1, m), r, 7, seed + 61, 0.65, 2.2,
                    smooth_r=0.02, noise_amp=0.0, noise_su=1, noise_sv=1,
                    twist=0.0, n_st=m + 2)
    Sweep(O + np.einsum("ij,sj->si", B, sw.C),
          np.einsum("ij,sjk->sik", B, sw.B), sw.LX,
          sw.LY).emit(mesh, shell_mat, cap_start=True, cap_end=True)
    # the boom mic
    mp = np.stack([np.linspace(-(0.5 * hw + 0.028), -0.030 * hw, 6),
                   np.linspace(-0.02 * hd, 0.42 * hd, 6),
                   np.linspace(0.09 * hh, -0.14 * hh, 6)], axis=1)
    sw2 = _tube_impl(mp, np.linspace(0, 1, 6), np.full(6, 0.0032), 6,
                     seed + 62, 1.0, 2.0, smooth_r=0.01, noise_amp=0.0,
                     noise_su=1, noise_sv=1, twist=0.0, n_st=8)
    Sweep(O + np.einsum("ij,sj->si", B, sw2.C),
          np.einsum("ij,sjk->sik", B, sw2.B), sw2.LX,
          sw2.LY).emit(mesh, shell_mat, cap_start=True, cap_end=True)


def build_boot_shaft(mesh, sk, side, b, lod, seed, mat):
    """The Nomex shaft above a race boot, so the ankle is not a bare cylinder.

    The 767 px peep of the shipped build shows a white cylinder of ankle
    between the trouser hem and the shoe on every figure. On a crew figure that
    gap is where the boot goes.
    """
    O = sk.origin["foot_" + side]
    B = sk.basis["foot_" + side]
    ring = max(10, lod.ring - 6)
    th = ring_theta(ring)
    rows = 5
    out = []
    for i in range(rows):
        f = i / (rows - 1.0)
        r = b.ankle_r * (1.14 + 0.20 * f)
        z = b.ankle_h * (0.10 + 0.86 * f)
        C = O + B @ np.array([0.0, -z, 0.030 * b.foot_len * f])
        out.append(C[None, :]
                   + np.cos(th)[:, None] * (B[:, 0] * r)[None, :]
                   + np.sin(th)[:, None] * (B[:, 2] * r * 0.94)[None, :])
    emit_grid(mesh, np.stack(out), mat, closed_u=True)


# ===========================================================================
# 13.  WARDROBE -- garment TYPES, and a colour distribution with structure
# ===========================================================================
#
# "COLOUR DISTRIBUTION IS THE CROWD'S TEXTURE. Uniform random hue reads as
# television static; real crowds clump into team-colour blocks against a
# neutral field." -- the manifest's own note on `spectator_clothing`.
#
# So the sampler takes a `team` (a brand from itemkit's ONE brand book, Law 2)
# and a `team_frac`, and the rest of the population draws from a neutral field
# that is deliberately desaturated and dominated by dark blue, grey, white and
# denim -- which is what a real crowd wears.

NEUTRALS = (           # sRGB hex, weight
    ("#1c1f26", 0.11), ("#2b3240", 0.09), ("#3d4450", 0.07), ("#6b7280", 0.07),
    ("#9aa1aa", 0.06), ("#d6d8da", 0.09), ("#f2f0eb", 0.06), ("#7d1f1f", 0.03),
    ("#26456e", 0.08), ("#3f6fa3", 0.05), ("#2f5b3a", 0.04), ("#7a6a4f", 0.04),
    ("#b5651d", 0.025), ("#5a3f6b", 0.02), ("#0f3b3b", 0.03), ("#8c8f7a", 0.03),
    ("#c9b28a", 0.025), ("#4a4a4a", 0.05), ("#1d2b1d", 0.03), ("#a03c2e", 0.025),
)
DENIMS = (("#2c3f5c", 0.4), ("#3f5a7d", 0.3), ("#1d2a3d", 0.2), ("#6b7f99", 0.1))
SHOE_COLS = (("#171719", 0.30), ("#2e2a26", 0.14), ("#f0eee9", 0.18),
             ("#5a4632", 0.12), ("#8f9296", 0.10), ("#25355c", 0.08),
             ("#7a2727", 0.04), ("#d8d2c4", 0.04))
SOLE_COLS = (("#e8e5de", 0.42), ("#1a1a1c", 0.34), ("#b9b4a8", 0.14),
             ("#c9713a", 0.10))
SHOE_STYLES = {
    "trainer": dict(sole=0.030, toe_spring=0.085, collar=0.36, w=0.46),
    "runner":  dict(sole=0.034, toe_spring=0.095, collar=0.34, w=0.18),
    "boot":    dict(sole=0.038, toe_spring=0.070, collar=0.56, w=0.12),
    # A RACE BOOT, for the covered tier: a taller shaft so the overall's leg
    # cuff sits ON something. The separate `build_boot_shaft` tube this
    # replaces rendered as a bright sock pulled over the shoe.
    "race_boot": dict(sole=0.030, toe_spring=0.060, collar=0.74, w=0.00),
    "loafer":  dict(sole=0.020, toe_spring=0.060, collar=0.26, w=0.12),
    "flat":    dict(sole=0.016, toe_spring=0.055, collar=0.24, w=0.12),
}


def _hexw(rng, table):
    return K.srgb_linear(_pick_weighted(rng.u(), table))


def sample_wardrobe(rng, b, team=None, team_frac=0.30, role=None):
    """One person's clothes. Garment TYPES, not colour swaps.

    `role` overrides the sampler for a working figure -- `paddock`, `marshal`,
    `crew` -- because a paddock in random leisurewear is as wrong as a crowd in
    uniform.
    """
    fem = 1 if b.sex == "F" else 0
    w = {}
    if role in ("paddock", "crew", "marshal"):
        cands = [("polo", 0.34), ("buttoned_shirt", 0.18), ("shirt_rolled", 0.14),
                 ("softshell", 0.16), ("team_jersey", 0.10), ("gilet", 0.05),
                 ("tee", 0.03)]
        bcands = [("chinos", 0.42), ("tech_trou", 0.30), ("jeans", 0.16),
                  ("cargo", 0.08), ("shorts", 0.04)]
    else:
        cands = [(k, v["w"][fem]) for k, v in TOPS.items() if v["w"][fem] > 0]
        bcands = [(k, v["w"][fem]) for k, v in BOTTOMS.items() if v["w"][fem] > 0]
    w["top"] = _pick_weighted(rng.u(), cands)
    w["bottom"] = _pick_weighted(rng.u(), bcands)
    if b.age_band == "child":
        w["top"] = _pick_weighted(rng.u(), [("tee", 0.5), ("longsleeve", 0.2),
                                            ("hoodie", 0.2), ("sweatshirt", 0.1)])
        w["bottom"] = _pick_weighted(rng.u(), [("shorts", 0.4), ("jeans", 0.3),
                                               ("track", 0.3)])
    tspec = dict(TOPS[w["top"]])
    bspec = dict(BOTTOMS[w["bottom"]])
    # FIT VARIES WITH THE BODY UNDERNEATH -- the brief's requirement, and the
    # reason `ease` is a per-person draw and not a table constant. A garment on
    # a heavy frame is tighter (less ease per unit girth), on a slight frame
    # looser, and everyone has their own preference on top of that.
    fit = float(np.clip(rng.n(1.0, 0.22), 0.55, 1.75))
    slack = 1.0 + 0.55 * float(np.clip(1.25 - b.girth, -0.35, 0.55))
    tspec["ease"] = tspec["ease"] * fit * slack
    bspec["ease"] = bspec["ease"] * float(np.clip(rng.n(1.0, 0.18), 0.6, 1.6)) \
        * slack
    tspec["hem"] = tspec["hem"] * float(np.clip(rng.n(1.0, 0.20), 0.5, 1.6))
    tspec["sleeve"] = float(np.clip(tspec["sleeve"]
                                    * np.clip(rng.n(1.0, 0.10), 0.7, 1.3),
                                    0.0, 0.985))
    tspec["lam"] = tspec["lam"] * float(np.clip(rng.n(1.0, 0.15), 0.6, 1.5))
    bspec["lam"] = bspec["lam"] * float(np.clip(rng.n(1.0, 0.15), 0.6, 1.5))
    w["top_spec"] = tspec
    w["bottom_spec"] = bspec

    on_team = (team is not None) and (rng.u() < team_frac)
    if on_team:
        bg = K.srgb_linear(team[1])
        fg = K.srgb_linear(team[2])
        w["top_rgb"] = bg if rng.u() < 0.72 else fg
        w["team"] = team[0]
    else:
        w["top_rgb"] = _hexw(rng, NEUTRALS)
        w["team"] = None
    if w["bottom"] in ("jeans",):
        w["bottom_rgb"] = _hexw(rng, DENIMS)
    elif role in ("paddock", "crew", "marshal"):
        w["bottom_rgb"] = _hexw(rng, (("#1c1f26", 0.4), ("#2b3240", 0.2),
                                      ("#3f4148", 0.2), ("#d6d8da", 0.1),
                                      ("#5a4632", 0.1)))
    else:
        w["bottom_rgb"] = _hexw(rng, NEUTRALS)
    # dye lot: two people in "the same" shirt are never the same shirt
    j = 1.0 + rng.clipn(0.075, 0.20)
    w["top_rgb"] = tuple(float(np.clip(c * j, 0.002, 0.95)) for c in w["top_rgb"])
    j2 = 1.0 + rng.clipn(0.065, 0.18)
    w["bottom_rgb"] = tuple(float(np.clip(c * j2, 0.002, 0.95))
                            for c in w["bottom_rgb"])

    # ---- THE COVERED TIER ------------------------------------------------
    # A pit crew is a UNIFORM, so the variation is not "what did you choose to
    # wear" but build, fit, wear, role kit, and which team. Everything that
    # would normally be a garment draw is replaced by one overall whose EASE,
    # LENGTH and WEAR still vary per person -- a suit issued in five sizes to a
    # hundred different bodies fits a hundred different ways.
    if role == "crew":
        osp = dict(OVERALL)
        osp["ease"] = osp["ease"] * float(np.clip(rng.n(1.0, 0.13), 0.72, 1.35)) \
            * (0.5 + 0.5 * slack)
        osp["lam"] = osp["lam"] * float(np.clip(rng.n(1.0, 0.14), 0.65, 1.45))
        osp["sleeve"] = float(np.clip(rng.n(0.985, 0.010), 0.94, 0.995))
        osp["leg"] = float(np.clip(rng.n(0.985, 0.010), 0.94, 0.995))
        w["top"] = w["bottom"] = "overall"
        w["overall_spec"] = osp
        w["top_spec"] = osp
        w["bottom_spec"] = osp
        # HEAD KIT BY JOB. Over-the-wall crew are helmeted; garage and
        # pit-wall crew are in a balaclava and ear defenders. Both are built.
        w["head_kit"] = _pick_weighted(rng.u(), (("helmet", 0.56),
                                                 ("headset", 0.34),
                                                 ("cap_headset", 0.10)))
        w["visor_open"] = rng.u() < 0.22
        # THE TEAM LIVERY. Defect: "overalls are flat single colours -- no team
        # graphics, sponsor panels or contrasting shoulders." A crew is a
        # uniform, so the livery is a property of the TEAM and every member
        # wears the same pattern, the same panel colours and the same mark.
        w["livery"] = livery_for_team(team)
        if team is not None:
            w["top_rgb"] = K.srgb_linear(team[1])
            w["helm_rgb"] = K.srgb_linear(team[2] if rng.u() < 0.55 else team[1])
            w["team"] = team[0]
        else:
            w["top_rgb"] = _hexw(rng, NEUTRALS)
            w["helm_rgb"] = _hexw(rng, NEUTRALS)
        j3 = 1.0 + rng.clipn(0.045, 0.12)
        w["top_rgb"] = tuple(float(np.clip(c * j3, 0.002, 0.95))
                             for c in w["top_rgb"])
        w["bottom_rgb"] = w["top_rgb"]
        # the dye lot travels through the livery too: a team's suits are the
        # same suit, issued at different times, and no two are the same white
        if w["livery"] is not None:
            for k in ("base", "accent", "trim"):
                w["livery"][k] = tuple(
                    float(np.clip(c * j3, 0.002, 0.95)) for c in w["livery"][k])
            w["top_rgb"] = w["bottom_rgb"] = w["livery"]["base"]
        w["glove_rgb"] = _hexw(rng, (("#141416", 0.42), ("#2a2b30", 0.22),
                                     ("#7d1f1f", 0.10), ("#1b2a44", 0.14),
                                     ("#d8d4cc", 0.12)))
        w["balaclava_rgb"] = _hexw(rng, (("#101012", 0.50), ("#e8e6e0", 0.30),
                                         ("#2a2b30", 0.20)))
        w["headwear"] = "none"
        w["headwear_rgb"] = w["helm_rgb"]

    st = _pick_weighted(rng.u(), [(k, v["w"]) for k, v in SHOE_STYLES.items()])
    if role == "crew":
        st = "race_boot"
    w["shoe"] = st
    w["shoe_spec"] = dict(SHOE_STYLES[st])
    w["shoe_rgb"] = _hexw(rng, SHOE_COLS)
    w["sole_rgb"] = _hexw(rng, SOLE_COLS)
    if role == "crew":
        w["shoe_rgb"] = _hexw(rng, (("#141416", 0.52), ("#2a2b30", 0.26),
                                    ("#d8d4cc", 0.22)))
        w["sole_rgb"] = _hexw(rng, (("#1a1a1c", 0.68), ("#3a352e", 0.32)))
    hw = _pick_weighted(rng.u(), tuple(HEADWEAR.items()))
    if role in ("paddock", "crew", "marshal") and rng.u() < 0.55:
        hw = "cap"
    if b.hair_style == "bald" and hw == "none" and rng.u() < 0.45:
        hw = "cap"
    w["headwear"] = hw
    w["headwear_rgb"] = (w["top_rgb"] if (on_team and rng.u() < 0.5)
                         else _hexw(rng, NEUTRALS))
    # A WHITE CAP IS NOT A WHITE CARD. Defect 4's second half: *"the white ones
    # are the brightest objects in the frame"*, and they were -- `#f2f0eb` is
    # 0.87 linear, which under a 12.47 deg sun on the TOP of a head (the one
    # surface pointed at the sky) out-reads the sky itself. New cotton twill is
    # about 0.72 and a cap that has been worn outdoors is well below that,
    # because the crown is the part that sits in the sun and the band is the
    # part that soaks up sweat. Headwear is therefore capped and then
    # weathered, not left at whatever the shared neutral book says. The book is
    # shared with shirts, where 0.87 is a fine white shirt in shadow.
    #
    # DERIVED, NOT DRAWN, for the reason `sample_body.hair_part_az` is: two
    # more `rng` calls here shift every later draw in this function, so the
    # prop, the shoe and the grip of every person in the library change and a
    # headwear A/B stops being an A/B. `_hash01` of numbers already drawn.
    _h = _hash01(w["headwear_rgb"][0], w["headwear_rgb"][2], b.stature)
    _cap_lin = 0.62 + 0.10 * _h
    _mx = max(w["headwear_rgb"])
    if _mx > _cap_lin:
        w["headwear_rgb"] = tuple(c * (_cap_lin / _mx)
                                  for c in w["headwear_rgb"])
    w["headwear_wear"] = float(np.clip(
        0.16 + 0.74 * _hash01(b.stature, w["headwear_rgb"][1], b.age_years),
        0.10, 1.0))
    w["wear"] = float(np.clip(rng.n(0.35, 0.22), 0.0, 1.0))
    w["grip"] = float(np.clip(rng.n(0.18, 0.14), 0.0, 0.7))
    # HELD PROPS -- defect 3. Drawn by plausible frequency per role, and the
    # ARCHETYPE overrides the draw: a figure posed `phone_to_ear` holds a phone
    # whatever the frequency table says, because the alternative is a hand
    # cupped around nothing beside an ear.
    tbl = PROP_ROLE_W.get(role or "spectator", PROP_ROLE_W["spectator"])
    w["prop"] = _pick_weighted(rng.u(), tbl)
    w["prop_hand"] = "R" if rng.u() < 0.82 else "L"      # handedness
    return w


# ===========================================================================
# 14.  THE FIGURE -- every layer, one object, contact solved and MEASURED
# ===========================================================================

def build_figure(seed, lod=None, kind=None, archetype=None, gaze=None,
                 sex=None, age_band=None, adult_only=False, role=None,
                 team=None, team_frac=0.30, covered=False, seat_z=None,
                 body=None, pose=None, wardrobe=None, sleeve_control=False):
    """One complete person. Returns a dict; `["mesh"]` is a single Mesh.

    CONTACT IS SOLVED AND THEN MEASURED. The figure is built with the hip joint
    at its anthropometric height, the actual lowest sole vertex is found in the
    finished mesh, and the whole mesh is translated so that vertex sits exactly
    on z = 0 (or on the seat). `["contact"]` reports what the residual is, and
    `["lowest_non_contact_z"]` reports whether anything ELSE is below the
    contact plane -- which is how a floating figure and a figure buried to the
    ankle both show up as numbers instead of as something to notice in a render.
    """
    lod = lod or LOD_L0
    rb = rng_for(seed, 1)
    b = body or sample_body(rb, sex=sex, age_band=age_band,
                            adult_only=adult_only)
    rw = rng_for(seed, 2)
    w = wardrobe or sample_wardrobe(rw, b, team=team, team_frac=team_frac,
                                    role=role)
    crew = (role == "crew")
    if crew:
        covered = True
    rp = rng_for(seed, 3)
    if kind is None:
        kind = "sit" if seat_z is not None else None
    if pose is None:
        arche, pose = sample_pose(rp, b, archetype=archetype, kind=kind,
                                  gaze=gaze)
    else:
        arche = archetype or "given"
        pose = clamp_pose(pose)
    sk = solve_skeleton(b, pose)

    m = Mesh()
    tor, t_t = build_torso(sk, b, lod, seed)
    arms, legs = {}, {}
    for s in ("L", "R"):
        sa = build_arm(sk, s, b, lod, seed)
        arms[s] = (sa, np.linspace(0.0, 1.0, sa.S))
        sl = build_leg(sk, s, b, lod, seed)
        legs[s] = (sl, np.linspace(0.0, 1.0, sl.S))

    # ---- skin ------------------------------------------------------------
    tor.emit(m, MAT_SKIN, cap_start=True, v0=float(t_t[0]), v1=float(t_t[-1]))
    emit_grid(m, shoulder_cap(tor, sk, b, rows=max(3, lod.station)), MAT_SKIN)
    # ---- held prop, BEFORE the hands, because it sets their grip -----------
    prop = POSE_PROP.get(arche, w.get("prop", "none"))
    prop_hand = w.get("prop_hand", "R")
    grip_r = build_prop(m, sk, prop_hand, b, lod, seed, prop,
                        {"acc": MAT_ACC, "shoe": MAT_SHOE, "eye": MAT_EYE})
    if grip_r is None:
        prop = "none"
    for s in ("L", "R"):
        arms[s][0].emit(m, MAT_SKIN, cap_start=True)
        legs[s][0].emit(m, MAT_SKIN, cap_start=True)
        if crew:
            build_glove(m, sk, s, b, lod, seed, MAT_NAIL, cuff_mat=MAT_TOP,
                        grip=w["grip"],
                        grip_r=(grip_r if s == prop_hand else None))
        else:
            build_hand(m, sk, s, b, lod, seed, grip=w["grip"],
                       grip_r=(grip_r if s == prop_hand else None))
    build_neck(sk, b, lod, seed).emit(m, MAT_SKIN, cap_start=True, cap_end=True)
    head_info = build_head(m, sk, b, lod, seed, covered=covered)

    # ---- clothing --------------------------------------------------------
    if crew:
        build_overall(m, tor, t_t, arms, legs, sk, b, lod, seed,
                      w["overall_spec"], MAT_TOP, wear=w["wear"],
                      livery=w.get("livery"))
    else:
        build_top(m, tor, t_t, arms, sk, b, lod, seed, w["top_spec"], MAT_TOP,
                  wear=w["wear"], sleeve_control=sleeve_control)
        build_bottom(m, tor, t_t, legs, sk, b, lod, seed, w["bottom_spec"],
                     MAT_LEG, wear=w["wear"])
    soles = []
    for s in ("L", "R"):
        soles.append(build_shoe(m, sk, s, b, lod, seed, w["shoe_spec"],
                                {"shoe": MAT_SHOE, "sole": MAT_SOLE}))
    if crew:
        build_balaclava(m, sk, b, lod, seed, MAT_HAIR)
        kit = w.get("head_kit", "helmet")
        if kit == "helmet":
            build_helmet(m, sk, b, lod, seed, MAT_HELM, MAT_VISOR, MAT_ACC,
                         open_visor=w.get("visor_open", False),
                         livery=w.get("livery"))
        else:
            if kit == "cap_headset":
                build_headwear(m, sk, b, lod, seed, "cap", MAT_ACC)
            build_headset(m, sk, b, lod, seed, MAT_HELM, MAT_ACC)
    elif not covered:
        # A HAT IS WORN OVER HAIR, and both halves of that have to be true:
        # the hair is squashed and thinned under the crown, and the crown is
        # then given the clearance the squashed hair actually needs.
        hat = w["headwear"] in ("cap", "beanie", "bucket")
        ht = build_hair(m, sk, b, lod, seed, MAT_HAIR,
                        squash=(0.40 if hat else 1.0))
        build_headwear(m, sk, b, lod, seed, w["headwear"], MAT_ACC,
                       hair_thick=(ht if hat else 0.0),
                       wear=w.get("headwear_wear", 0.0))

    # ---- surface SIDE ----------------------------------------------------
    # Every piece is checked to be facing outward, and reversed if it is not.
    # See Mesh.orient_outward: 55 of 318 pieces on the shipped build were
    # inside-out, including the head, the hair and both shoes.
    orient = m.orient_outward(report=True)

    # ---- contact ---------------------------------------------------------
    # MEASURE THE MESH, NOT THE BUILDER'S RETURN VALUE. `build_shoe` reports the
    # minimum of the two shells it lofts, and that missed the cap fans and the
    # tread bars: the selftest found figures whose real lowest vertex sat 5.1 mm
    # below the height the solver had "solved" to. A contact solver that trusts
    # a number it was handed is the same class of error as a gate that never
    # opens the image.
    Vall, vmat = m.vertex_materials()
    shoe_v = (vmat == MAT_SHOE) | (vmat == MAT_SOLE)
    sole_z = (float(Vall[shoe_v][:, 2].min()) if shoe_v.any()
              else float(min(soles)))
    if seat_z is None:
        drop = -sole_z
    else:
        lo, _hi = m.bounds()
        seat_contact = _seat_contact_z(m, sk, b)
        drop = float(seat_z) - seat_contact
    m.translate((0.0, 0.0, drop))
    lo, hi = m.bounds()
    contact_plane = 0.0 if seat_z is None else float(seat_z)
    m.set_all(hk_id=hash01(int(seed), 8191))
    m.colour_by_material([
        b.skin_rgb,
        w["top_rgb"], w["bottom_rgb"],
        w["balaclava_rgb"] if crew else b.hair_rgb,
        w["shoe_rgb"], w["sole_rgb"], (0.55, 0.55, 0.56),
        w["headwear_rgb"],
        w["glove_rgb"] if crew else b.skin_rgb,
        w.get("helm_rgb", (0.30, 0.30, 0.32)),
        (0.02, 0.02, 0.024)])

    return {
        "mesh": m, "body": b, "pose": pose, "archetype": arche,
        "wardrobe": w, "skeleton": sk, "lod": lod, "seed": int(seed),
        "prop": prop, "prop_hand": prop_hand, "prop_grip_r": grip_r,
        "head": head_info, "kind": kind or "stand", "orient": orient,
        "drop": drop, "bbox": (lo, hi),
        "height_m": float(hi[2] - lo[2]),
        "contact": {
            "plane_z": contact_plane,
            "sole_z_after": float(sole_z + drop),
            "residual_mm": float(abs((sole_z + drop) - (0.0 if seat_z is None
                                                        else 0.0)) * 1000.0),
            "lowest_vertex_z": float(lo[2]),
            "below_plane_mm": float(max(0.0, contact_plane - lo[2]) * 1000.0),
        },
        "tris": m.n_tris(),
    }


def _seat_contact_z(m, sk, b):
    """The z of the ischial contact -- the lowest point of the buttock mass."""
    V, _Q, _T, _QM, _TM, _A = m.finish()
    pel = sk.origin["pelvis"]
    fwd = sk.basis["pelvis"][:, 1]
    d = V - pel[None, :]
    back = (d @ fwd) < 0.02
    near = np.abs(d[:, 2]) < b.trochanter_h * 0.45
    sel = back & near & (d[:, 2] < 0.0)
    if not sel.any():
        return float(V[:, 2].min())
    return float(V[sel][:, 2].min())


def figure_stats(fig):
    """Everything a report needs about one figure, in real units."""
    b = fig["body"]
    m = fig["mesh"]
    V, Q, T, _QM, _TM, _A = m.finish()
    return {
        "seed": fig["seed"], "sex": b.sex, "age_band": b.age_band,
        "age_years": round(b.age_years, 1),
        "stature_m": round(b.stature, 4), "bmi": round(b.bmi, 2),
        "mass_kg": round(b.mass, 1),
        "archetype": fig["archetype"], "lod": fig["lod"].name,
        "top": fig["wardrobe"]["top"], "bottom": fig["wardrobe"]["bottom"],
        "hair": b.hair_style, "hair_colour": b.hair_name,
        "headwear": fig["wardrobe"]["headwear"],
        "prop": fig.get("prop", "none"),
        "verts": int(len(V)), "quads": int(len(Q)), "tris": int(m.n_tris()),
        "height_m": round(fig["height_m"], 4),
        "contact": fig["contact"],
    }


# ===========================================================================
# 15.  MATERIALS -- ONE set for the whole population
# ===========================================================================
#
# WHAT THE SHADER IS FOR AND WHAT IT IS NOT FOR. The gate measures band-passed
# contrast at r1-r2 px and a lip-and-shadow dipole at 4-16 px lags. At
# `paddock_personnel_figure`'s 10 m / 35 mm that is 373 px/m: r1 peaks on an
# 8 mm feature and r2 on a 16 mm one. Representing an 8 mm crumple as MESH needs
# 3 mm edges -- 78,000 quads on the torso alone -- for a feature that only ever
# changes the shading. So the 3-16 mm band is a BUMP here, and the >= 25 mm
# fold language is real geometry in section 11. A bump is not paint: it
# perturbs the normal, so it makes a genuine sunward lip and lee shadow, which
# is what R2-021's physical ladder distinguishes (painted stripes score 0.169
# against a flat plate's 0.142; 0.5 mm of real relief scores 0.361).
#
# Every graph addresses itself with `TexCoord -> Object` (itemkit Law 6) and
# reads the per-figure data from vertex attributes, never from an image.

# ---------------------------------------------------------------------------
# NODE RESPONSE -- MEASURED, and the fix for the defect that outlived wave 1.
# ---------------------------------------------------------------------------
#
# HOW IT WAS MEASURED. Each node was rendered alone, as an emission shader, on a
# 1.000 x 1.000 m plane whose vertices sit at +-0.5 in its OWN object space,
# under an orthographic camera of ortho_scale 1.0 at 1024 x 1024 with the
# reconstruction filter at 0.01 px. One pixel is therefore exactly 0.9766 mm and
# the rendered image IS the node's output on a known metric grid. Radially
# averaged 2-D power spectrum -> the wavelength carrying the most energy.
#
#     node                        emitted wavelength      output sd    p01..p99
#                                 / declared (1/scale)                  range
#     Noise, any detail                   1.60          0.059-0.116   0.27-0.51
#     Voronoi F1                          2.17          0.168         0.750
#     Wave BANDS, one axis                0.314         0.353         1.000
#     Wave BANDS, diagonal    0.363 (3-D) / 0.444 (planar)
#
# THE WAVE ROW IS THE CONTROL AND IT IS WHY THE OTHER ROWS CAN BE BELIEVED.
# Blender's wave texture multiplies the coordinate by 20 before the sine (by 10
# along the diagonal), so its wavelength has a closed form: 2*pi/20 = 0.31416,
# and 2*pi/(10*sqrt3) = 0.36276 on a surface where all three axes vary. The
# measurement returned 0.3136 and 0.3628, and the sine's standard deviation came
# back 0.3528 against an exact 1/(2*sqrt2) = 0.35355. An instrument that
# reproduces two closed forms to 0.2 % is measuring the node, not itself.
#
# TWO CONSEQUENCES. BOTH WERE SHIPPED, AND THE SECOND IS THE BIGGER.
#
# 1. FREQUENCY. `scale = 1/L` reads as "features of L metres" and is not: a
#    Noise emits 1.60 L and a Voronoi 2.17 L, while a Wave emits 0.31 L. The
#    first version of this shader declared an 8.6 mm crumple and emitted
#    13.8 mm, and declared 17.7 mm and emitted 28.3 mm -- 1.60x coarse in both,
#    which walks them out of `item_gate`'s decisive r1/r2 bands (whose measured
#    response peaks on 3 px and 6 px periods = 8.04 and 16.07 mm at this item's
#    373.3 px/m) and into r4/r8, the exact place wave 1's cloth was found to
#    have all of its energy. The same factor is in the module this file is
#    replacing: `crew_fireproof_overall`'s crumple declares 1/(52*2) = 9.6 mm
#    and emits 15.4 mm.
#
# 2. AMPLITUDE -- WAVE1-PEEP-SYNTHESIS's "the wavelength model may well be
#    right; the AMPLITUDE is effectively zero". A Bump node's `Distance`
#    multiplies the height SIGNAL, and that signal's range is a property of the
#    node that nobody measured. A Wave swings the full 0..1. A Noise at detail 5
#    has sd 0.059 and a 1st-99th percentile range of 0.269. So
#    `bump(noise, 0.62, 0.0022)` does not emit 2.2 mm of relief; it emits
#    0.62 * 2.2 * 0.269 = 0.37 mm -- while the identical call on a Wave emits
#    1.37 mm, 3.7x more, with nothing in the source saying so. Worked through
#    every stage of the previous fabric shader, the steepest surface slope
#    anywhere in the 3-16 px band was 5.0 deg. Cloth is 20-30 deg. The shader
#    was asking the renderer to shade a machined surface.
#
# `tex_scale()` and `relief()` make both unrepresentable. A wavelength is asked
# for in METRES and arrives; a bump amplitude is asked for in MILLIMETRES
# PEAK-TO-PEAK and arrives, because the height is renormalised to 0..1 first.
# `max_slope_deg()` turns the pair into the number that can be argued about.

NODE_K = {           # emitted wavelength = NODE_K / scale
    "noise": 1.60,
    "voronoi": 2.17,
    "wave_x": 0.31416,          # 2*pi/20, closed form; measured 0.3136
    "wave_diag": 0.36276,       # 2*pi/(10*sqrt 3) on a general 3-D surface
}
NODE_PP = {          # 1st-99th percentile range of the node's own output
    "noise_d0": 0.512, "noise_d3": 0.328, "noise_d4": 0.300, "noise_d5": 0.275,
    "voronoi": 0.750, "wave": 1.000,
}


def tex_scale(kind, lam_m):
    """The `Scale` that makes a node emit features of `lam_m` METRES."""
    if kind not in NODE_K:
        raise KeyError("tex_scale: %r is not a measured node kind; known: %s"
                       % (kind, sorted(NODE_K)))
    if not lam_m > 0:
        raise ValueError("tex_scale: wavelength must be positive, got %r" % lam_m)
    return NODE_K[kind] / float(lam_m)


def max_slope_deg(amp_mm, lam_m):
    """The steepest slope a sinusoid of this peak-to-peak amplitude and this
    wavelength reaches: d/dx of (A/2) sin(2 pi x / L) is pi A / L.

    This is the number to argue about. A shader stage is not "1 mm of relief",
    it is "1 mm of relief at 8 mm, which is a 21 degree surface". Cloth crumple
    is 20-30 deg, leather creasing 15-20, skin 3-6, a machined cone 0.
    """
    return math.degrees(math.atan(math.pi * float(amp_mm) * 1e-3 / float(lam_m)))


def bump_by_name(nt, height, strength, distance, normal=None):
    """A Bump node wired BY SOCKET NAME. Do not use `itemkit.NT.bump` in 5.2.

    ============================ READ THIS ==============================
    THE AMPLITUDE TRAP, FOUND. `itemkit.NT.bump` pins by INDEX:

        pin(nd, 0, strength); pin(nd, 1, distance); pin(nd, 2, height)
        if normal is not None: pin(nd, 3, normal)

    In Blender 5.2 a Bump node has FIVE inputs, not four, because **Filter
    Width was inserted at index 2**:

        [0] Strength   [1] Distance   [2] Filter Width   [3] Height   [4] Normal

    So on this Blender, for EVERY module that calls `NT.bump`:

      * the height signal is wired into **Filter Width**, where it does nothing
        but widen the derivative filter of a bump that has no height;
      * the normal chain is wired into **Height**, so each stage takes the
        previous stage's NORMAL VECTOR as its height scalar;
      * and the FIRST bump of any chain passes `normal=None`, which `pin`
        returns early on -- so its Height stays at the socket default, a
        CONSTANT 1.0. A constant has zero gradient. **That stage emits exactly
        zero relief, and it is the stage every chain starts with.**

    This is WAVE1-PEEP-SYNTHESIS's central finding with a mechanism under it:
    "the wavelength model may well be right; the AMPLITUDE is effectively zero,
    so nothing the model computes ever reaches the image", and fabric measuring
    FLATTER than a featureless placeholder ovoid. It is also why this file's
    corrected wavelengths and 5x amplitudes measured, on a lit flat plate,
    only 1.14x the shader they replaced: BOTH were emitting almost nothing,
    because in neither did the height ever reach the Height socket.

    It was found by dumping the built material's node values instead of reading
    the code -- the code is correct for the 4-input Bump of earlier Blenders,
    and no amount of reading it would have shown this.

    THE REST OF THE DSL IS FINE, and that was checked rather than assumed: every
    index `itemkit.NT` pins was compared against the live socket names in
    Blender 5.2 --

        TexNoise    0 Vector  2 Scale  3 Detail  4 Roughness  5 Lacunarity  OK
        TexWave     0 Vector  1 Scale  2 Distortion  3 Detail              OK
        TexVoronoi  0 Vector  2 Scale  8 Randomness                        OK
        MapRange    0 Value  1 From Min  2 From Max  3 To Min  4 To Max    OK
        Mix (RGBA)  0 Factor  6 A  7 B      Mix (FLOAT) 2 A  3 B           OK
        Math / VectorMath / CombineXYZ / ValToRGB                          OK
        Bump        2 -> Filter Width, 3 -> Height              *** BROKEN

    -- so `Bump` is the ONLY node type affected, and it is the one that carries
    every millimetre of relief in every material in the project.

    `itemkit.py` is read-only for this task, so the fix lives here. IT IS NOT
    ONLY THIS MODULE'S PROBLEM: `world/items/pit_wall_unit_itemkit.py`, the
    project's worked reference item, and every wave-2 module written against
    `itemkit` are affected. `selftest` below asserts the wiring on a BUILT
    material so a future socket insertion cannot do this again quietly.
    """
    nd = nt.n("ShaderNodeBump")
    nd.inputs["Strength"].default_value = float(strength)
    nd.inputs["Distance"].default_value = float(distance)
    nt.pin(nd, nd.inputs.find("Height"), height)
    if normal is not None:
        nt.pin(nd, nd.inputs.find("Normal"), normal)
    return (nd, 0)


def relief(nt, src, node_pp, lam_m, amp_mm, normal=None):
    """One bump stage, in real units.

    `src`      the height signal (a node/socket pair)
    `node_pp`  that node's own output range, from NODE_PP -- renormalised away
    `lam_m`    the wavelength it was built at, for the log line only
    `amp_mm`   PEAK-TO-PEAK relief in millimetres, which is what arrives
    """
    h = nt.maprange(src, 0.5 - 0.5 * node_pp, 0.5 + 0.5 * node_pp, 0.0, 1.0)
    return bump_by_name(nt, h, 1.0, float(amp_mm) * 1e-3, normal=normal)


def relief_budget(stages):
    """`[(name, lam_m, amp_mm)]` -> what the surface actually asks for.

    Reported by `selftest`, so the amplitudes are a stated claim in degrees
    rather than an array of millimetre constants nobody can check.
    """
    return [{"stage": n, "lambda_mm": round(1000.0 * l, 3),
             "amp_pp_mm": round(a, 4),
             "max_slope_deg": round(max_slope_deg(a, l), 2),
             "lambda_px_at_373": round(1000.0 * l / 2.6786, 2)}
            for n, l, a in stages]


def _attr_col(nt, name="hk_col"):
    nd = nt.n("ShaderNodeAttribute", attribute_type="GEOMETRY")
    nd.attribute_name = name
    return (nd, 0)


def _attr_f(nt, name):
    nd = nt.n("ShaderNodeAttribute", attribute_type="GEOMETRY")
    nd.attribute_name = name
    return (nd, 2)


def _zone_is(nt, zone, code, width=0.45):
    """1.0 inside a zone code, 0 outside. `hk_zone` is baked per vertex, so this
    is how one skin shader puts a lip on the lips and a nail on the nail."""
    d = nt.math("SUBTRACT", zone, float(code))
    a = nt.math("ABSOLUTE", d)
    return nt.maprange(a, 0.0, width, 1.0, 0.0)


def skin_material(prefix, name="Skin"):
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    col = _attr_col(nt)
    zone = _attr_f(nt, "hk_zone")
    fid = _attr_f(nt, "hk_id")
    # de-phase every procedural per figure so two people never share a mole
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 31.7),
                                    nt.math("MULTIPLY", fid, 17.3),
                                    nt.math("MULTIPLY", fid, 43.1)))
    # --- tone: large-scale mottle, then the vascular red in the thin places
    mottle = nt.noise(Pj, tex_scale("noise", 0.180), detail=4.0, rough=0.55)
    base = nt.cmix(nt.maprange(mottle, 0.30, 0.70, 0.0, 1.0),
                   nt.cmix(0.28, col, (0.35, 0.20, 0.14), "MULTIPLY"),
                   nt.cmix(0.22, col, (1.30, 1.10, 1.02), "MULTIPLY"))
    # CONTINUOUS masks, not the discrete zone code: a hard threshold on a grid
    # is a stair-step in the render, and it was one.
    lip = nt.maprange(_attr_f(nt, "hk_lip"), 0.25, 0.80, 0.0, 1.0)
    brow = nt.maprange(_attr_f(nt, "hk_brow"), 0.42, 0.92, 0.0, 1.0)
    dark = nt.maprange(_attr_f(nt, "hk_dark"), 0.20, 0.85, 0.0, 1.0)
    nail = _zone_is(nt, zone, ZONE_NAIL)
    # FACE_TINT is the shader half of the defect-1 ladder (see its docstring).
    # It gains the MIX FACTOR of each of the three face masks, so 0.0 leaves
    # exactly the mottle and the vascular red -- a face with no lip, no brow
    # shadow and no orbital darkening -- while every other skin term is
    # untouched. Read at call time, so a bench sets it before building.
    base = nt.cmix(nt.math("MULTIPLY", lip, FACE_TINT), base,
                   nt.cmix(0.55, col, (0.78, 0.26, 0.24), "MULTIPLY"))
    base = nt.cmix(nt.math("MULTIPLY", brow, 0.85 * FACE_TINT), base,
                   nt.cmix(0.85, col, (0.14, 0.10, 0.075), "MULTIPLY"))
    base = nt.cmix(nt.math("MULTIPLY", dark, 0.45 * FACE_TINT), base,
                   nt.cmix(0.5, col, (0.62, 0.50, 0.46), "MULTIPLY"))
    base = nt.cmix(nail, base, nt.cmix(0.45, col, (1.25, 1.02, 1.00), "MULTIPLY"))
    # --- relief. Wavelengths EMITTED, amplitudes peak-to-peak in mm.
    # Skin is genuinely shallow -- 3-6 deg of slope at the grain scale -- and
    # saying so is the point. The stages are separate bumps rather than one
    # summed height, because summing two nodes of different output ranges is
    # exactly the arithmetic the NODE RESPONSE block exists to stop.
    SKIN_STAGES = [("grain", 0.0050, 0.10),      # 3.6 deg
                   ("pore", 0.00035, 0.030),     # 15.3 deg, 0.13 px at 373 px/m
                   ("crease", 0.020, 0.50)]      # 4.5 deg
    grain = nt.noise(Pj, tex_scale("noise", 0.0050), detail=5.0, rough=0.62)
    pore = nt.vor(Pj, tex_scale("voronoi", 0.00035), feature="F1")
    nrm = relief(nt, grain, NODE_PP["noise_d5"], 0.0050, 0.10)
    nrm = relief(nt, pore, NODE_PP["voronoi"], 0.00035, 0.030, normal=nrm)
    creases = nt.wave(Pj, tex_scale("wave_x", 0.020), distortion=8.0, detail=3.0)
    nrm = relief(nt, creases, NODE_PP["wave"], 0.020, 0.50, normal=nrm)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.021), detail=3.0),
                        0.30, 0.70, 0.44, 0.62)
    rough = nt.fmix(lip, rough, 0.34)
    b = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                          subsurface_weight=0.16,
                          subsurface_scale=0.010,
                          metallic=0.0)
    for nm, v in (("Subsurface Radius", (0.036, 0.011, 0.006)),
                  ("Specular IOR Level", 0.42)):
        if nm in b.inputs:
            b.inputs[nm].default_value = v
    return nt.m


FABRIC_STAGES_MM = None          # filled by the first fabric_material() call

SHADER_RELIEF = 1.0
"""Gain on every fabric bump amplitude. The other half of the `FOLD_GAIN`
control pair: render the figure once with the geometry folds off and once with
the shader relief off, and whichever frame loses the granular crust is the one
that owns it. Neither can be settled by reading the code -- both live at about
23 px at the 767 px framing."""


FIGURE_PX_PER_M = 373.3      # 10.0 m on a 35 mm lens at 3840 -- the figure items


SUN_ELEV_DEG = 12.47061          # world_contract.SUN_ELEV_DEG -- see below


def slope_for_modulation(mod_pp, elev_deg=SUN_ELEV_DEG):
    """The surface slope, in degrees, that a bump needs to modulate the
    rendered radiance by `mod_pp` peak-to-peak under a sun at `elev_deg`.

    THE NUMBER THAT WAS MISSING, AND IT IS WHY EVERY GARMENT RENDERED AS FELT.
    A Lambertian surface lit at elevation e has radiance proportional to
    sin(e); tilt its normal by theta towards or away from the sun and that
    becomes sin(e +- theta) ~ sin e +- theta cos e. So the RELATIVE peak-to-peak
    modulation is

        m = 2 theta / tan(e)

    and the film's sun is at 12.47 deg, where tan(e) = 0.2213. That divisor is
    the whole story: the same crumple that is a soft grain at noon is a
    saturated crust at this sun. `fabric_stages` had been tuned to 9.9-10.8 deg
    of slope, which is

        m = 2 x 0.174 / 0.2213 = 1.57

    -- a 157 % peak-to-peak swing on a 3 px feature, over the entire garment,
    with no smooth cloth anywhere. That is exactly what the bench render shows:
    coveralls that read as thick felt and a polo that reads as towelling. The
    two rejected renders this replaces bracket the SAME error from both sides
    (4.97 deg read as a machined cone, 22.6 deg as stucco) because both were
    reasoned about as millimetres of cloth and neither was reasoned about as
    light.

    Cloth genuinely does crumple at 20-30 deg -- but locally, at creases, over a
    small fraction of the area, not as an isotropic field everywhere. So the
    isotropic stages are set from this function and a SPARSE crease stage
    carries the steep part.
    """
    e = math.radians(float(elev_deg))
    return math.degrees(0.5 * float(mod_pp) * math.tan(e))


def amp_mm_for_modulation(mod_pp, lam_m, elev_deg=SUN_ELEV_DEG):
    """Peak-to-peak millimetres that give `mod_pp` modulation at `lam_m`."""
    th = math.radians(slope_for_modulation(mod_pp, elev_deg))
    return math.tan(th) * float(lam_m) / math.pi * 1000.0


def fabric_stages(stiff, weave_mm, px_per_m=FIGURE_PX_PER_M):
    """The five relief stages of the garment shader, as (name, lambda_m, amp_mm).

    TUNED AGAINST A RENDER, AFTER THE FIRST SET WAS LOOKED AT AND REJECTED.
    The first amplitudes here put 22.6 and 23.6 degrees of slope at 3 px and
    6 px. That cleared `item_gate`'s microstructure bar by a factor of 179 --
    12.232 % fine contrast against a 0.034 % flat card -- and at 767 px the
    garments read as COARSE STUCCO, a uniform crawl over shirt and trouser
    alike. 24 degrees is the top of cloth's range and it belongs to heavy
    knitwear; a poplin shirt at an 8 mm crumple is nearer 0.4 mm deep, which is
    10 degrees. Overshooting a bar is not passing it.

    AND ANYTHING BELOW 2 px IS DROPPED, NOT SHRUNK. Cycles does not filter a
    bump by the pixel footprint, so a 1.3 mm weave at 373 px/m -- 0.49 px --
    does not render as a fine weave, it renders as per-pixel noise that inflates
    the r1 band and destroys the sunward-lip coherence that check 7 measures.
    That is the likeliest cause of this build's `relief_reads_as_lip_and_shade`
    dip coming back NEGATIVE (-0.1003 against a control of +0.0421): the
    surface had plenty of fine energy and none of it was lit like relief.
    A driver at 2 m gets the weave; a spectator at 15 m does not.

    WAVELENGTHS. `item_gate`'s decisive fine bands have a MEASURED response that
    peaks on periods of 3 px and 6 px (item_gate.py:295). At the figure items'
    373.3 px/m -- 10.0 m on a 35 mm lens at 3840 wide -- that is 8.04 mm and
    16.07 mm, and those two are built explicitly, EMITTED, via `tex_scale`.
    `stiff` moves them +-6 %: a heavy denim crumples marginally longer than a
    jersey. It is deliberately a small spread, because a stage that wanders out
    of the band it was built for stops doing the job it exists for.
    Anything coarser than ~25 mm is GEOMETRY, in section 11's fold field.

    AMPLITUDES, peak-to-peak in mm, and `relief_budget()` prints the slope they
    imply. The version before the amplitude cut reached 22-24 deg and rendered
    as stucco; the version before THAT reached 5.0 deg and rendered, correctly,
    as a machined cone. Cloth is between them and this is 9-11 deg.
    """
    s = float(stiff)
    band = 0.88 + 0.24 * s                     # 1.03 at jersey, 1.09 at denim
    nyq_m = 2.0 / max(float(px_per_m), 1e-6)   # 5.36 mm at 373.3 px/m
    # TARGET RADIANCE MODULATION, not target millimetres. See
    # `slope_for_modulation`. A soft jersey crumples more than a stiff Nomex, so
    # the target falls with stiffness; the CREASE stage is sparse (its height
    # signal is gated so it only acts on ~1/4 of the area) and is allowed to be
    # four times steeper, which is where the 20-30 deg of real cloth lives.
    #
    # AND THE COARSE END OF THIS LADDER WAS THE PLASTER, MEASURED BY RENDERING
    # THE TWO HALVES SEPARATELY. The C1/C2 control pair on the crew bench --
    # one frame with the GEOMETRY fold field zeroed and the shader untouched,
    # one with every shader bump zeroed and the geometry untouched -- settles
    # an argument that neither reading the code nor any variance statistic can:
    #
    #   C1, no geometry folds ....... the granular crust is entirely still
    #                                 there, unchanged.
    #   C2, no shader relief ........ a smooth plastic mannequin with visible
    #                                 flat facets on the sleeve.
    #
    # So the crust is the SHADER's, and the geometry fold field was contributing
    # nothing a viewer could see. The two offenders are the two coarsest stages,
    # and they are coarse enough that they were doing the GEOMETRY's job as a
    # normal map: `drape` was an isotropic noise at 120 mm -- 53 px at the crew
    # framing -- carrying m = 0.55, i.e. a 55 % peak-to-peak radiance swing over
    # a 53 px blob, over the whole garment, which is a definition of popcorn;
    # and `crease` sat at 42-55 mm with m = 0.94. This file's own rule says
    # "anything coarser than ~25 mm is GEOMETRY" and the shader was breaking it
    # by a factor of five.
    #
    # `drape` is deleted -- `_fold_cloth`'s 420 mm drape term is the real one,
    # in the mesh, where it also moves the silhouette. `crease` stays, because
    # a sparse ridge is not popcorn, but it comes down to m = 0.55 and stays
    # below the 40 mm the mesh cannot represent.
    m_fine = 0.30 - 0.10 * s                   # 0.24 jersey ... 0.21 Nomex
    m_mid = 0.42 - 0.14 * s
    m_crease = 1.30 - 0.40 * s
    lam_f = 0.00804 * band
    lam_m_ = 0.01607 * band
    lam_c = 0.034 * (0.85 + 0.5 * s)
    all_stages = [
        ("weave",   float(weave_mm) * 1e-3,   0.085 * float(weave_mm)),
        ("slub",    0.0024,                   0.10),
        ("crumple_fine", lam_f,               amp_mm_for_modulation(m_fine, lam_f)),
        ("crumple_mid",  lam_m_,              amp_mm_for_modulation(m_mid, lam_m_)),
        ("crease",  lam_c,                    amp_mm_for_modulation(m_crease, lam_c)),
    ]
    return [(n_, l_, a_ * SHADER_RELIEF)
            for (n_, l_, a_) in all_stages if l_ >= nyq_m]


def fabric_material(prefix, name, stiff=0.7, sheen=0.42, weave_mm=1.3,
                    px_per_m=FIGURE_PX_PER_M):
    """The garment shader. `stiff` picks the crumple wavelength and depth.

    THE CRUMPLE IS THE POINT. `crew_fireproof_overall` has 28 procedural texture
    nodes and `spectator_seated` 51, and both measured FLATTER than a
    featureless placeholder ovoid in the same frame -- all their energy sat at
    r8-r16 (2-4 cm) with none at r1-r4 (3-11 mm). Nodes were never the problem.
    The wavelengths and the amplitudes were, and both are now stated in real
    units and MEASURED out of the node rather than assumed -- see the NODE
    RESPONSE block above and `fabric_stages` below.
    """
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    col = _attr_col(nt)
    wear = _attr_f(nt, "hk_wear")
    fid = _attr_f(nt, "hk_id")
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 23.9),
                                    nt.math("MULTIPLY", fid, 51.7),
                                    nt.math("MULTIPLY", fid, 11.3)))
    # dye lot and sun fade: low-frequency, small amplitude, always present
    dye = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.290), detail=3.0),
                      0.30, 0.70, 0.93, 1.07)
    base = nt.cmix(0.5, col, nt.cmix(dye, nt.cmix(1.0, col, (0.86, 0.86, 0.90),
                                                  "MULTIPLY"),
                                     nt.cmix(1.0, col, (1.10, 1.08, 1.02),
                                             "MULTIPLY")))
    # wear: knees, elbows and seats go lighter and rougher
    grime = nt.noise(Pj, tex_scale("noise", 0.073), detail=4.0, rough=0.6)
    dirt = nt.math("MULTIPLY", wear, nt.maprange(grime, 0.42, 0.78, 0.0, 1.0))
    base = nt.cmix(nt.math("MULTIPLY", dirt, 0.55), base,
                   nt.cmix(0.6, base, (0.62, 0.58, 0.52), "MULTIPLY"))
    # --- FIVE relief stages. Wavelength EMITTED, amplitude PEAK-TO-PEAK. ----
    global FABRIC_STAGES_MM
    stages = fabric_stages(stiff, weave_mm, px_per_m)
    FABRIC_STAGES_MM = relief_budget(stages)
    nrm = None
    for name, lam, amp in stages:
        if name == "weave":
            src = nt.wave(Pj, tex_scale("wave_diag", lam), distortion=1.5,
                          detail=2.0, direction="DIAGONAL")
            pp = NODE_PP["wave"]
        elif name == "slub":
            src = nt.vor(Pj, tex_scale("voronoi", lam), feature="F1")
            pp = NODE_PP["voronoi"]
        elif name == "drape":
            src = nt.noise(Pj, tex_scale("noise", lam), detail=4.0, rough=0.55)
            pp = NODE_PP["noise_d4"]
        elif name == "crease":
            # SPARSE, so the steep part of cloth is where cloth is actually
            # steep. A crease is a line, not a field: the height signal is a
            # ridged noise (|n - 0.5| inverted) which concentrates its range
            # into narrow valleys and leaves most of the surface flat, and it
            # is then gated by a second, coarser noise so whole regions of the
            # garment have no creasing at all. An isotropic fbm at this
            # amplitude is the felt the bench render showed.
            n1 = nt.noise(Pj, tex_scale("noise", lam), detail=3.0, rough=0.42)
            ridge = nt.maprange(nt.math("ABSOLUTE",
                                        nt.math("SUBTRACT", n1, 0.5)),
                                0.0, 0.22, 1.0, 0.0)
            gate = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.185),
                                        detail=3.0), 0.46, 0.66, 0.0, 1.0)
            src = nt.math("MULTIPLY", ridge, gate)
            pp = 0.62
        else:
            src = nt.noise(Pj, tex_scale("noise", lam), detail=5.0,
                           rough=0.66 if name == "crumple_fine" else 0.62)
            pp = NODE_PP["noise_d5"]
        nrm = relief(nt, src, pp, lam, amp, normal=nrm)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.019), detail=3.0),
                        0.25, 0.75, 0.66 + 0.10 * stiff, 0.90)
    rough = nt.fmix(nt.math("MULTIPLY", dirt, 0.8), rough, 0.95)
    b = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                          metallic=0.0, sheen_weight=sheen,
                          sheen_roughness=0.32)
    for nm, v in (("Sheen Tint", (0.85, 0.85, 0.88, 1.0)),
                  ("Specular IOR Level", 0.32)):
        if nm in b.inputs:
            b.inputs[nm].default_value = v
    return nt.m


HAIR_STAGES_MM = None            # filled by the first hair_material() call

#: The head circumference the hair's angular texture frequencies are set from.
#: `head_w` and `head_d` average ~0.152/0.190 m over the population and the
#: scalp's own ring sits at roughly half of each, so this is the arc a lock
#: actually has to fit into. It is a CONSTANT on purpose: the material is one
#: datablock for the whole population (Mesh.CHANNELS' note), so it cannot be a
#: function of the body, and a lock is 7 mm on a big head and a small one.
HAIR_HEAD_CIRC_M = math.pi * 0.176

#: Value bands around the head in `hair_material`'s colour layer. Coarser than
#: the relief locks: real hair varies in tone over groups of locks, not lock by
#: lock, and lock-by-lock colour at this wavelength is speckle again.
HAIR_TONE_LOCKS = 26.0


def hair_stages(px_per_m=FIGURE_PX_PER_M):
    """The relief stages of the hair shader, as (name, lambda_m, amp_mm).

    `fabric_stages`' discipline, applied to the one surface that never got it.
    Read `HAIR_RELIEF`'s docstring for what the shipped numbers were and why
    they are a crust; this is what replaces them, and the three decisions in it
    are decisions rather than taste:

    **1. THE SUB-PIXEL FIBRE IS DROPPED, NOT SHRUNK.** A 1.2 mm ridge is 0.53 px
    at the 400 px face framing and 0.33 px at the crowd's 63 px head. Cycles
    does not filter a bump by the pixel footprint, so it renders as per-pixel
    noise at whatever amplitude it is given, and it does so IDENTICALLY at every
    distance -- which is why the defect is "a granular crust at every distance"
    rather than a texture that softens as the figure recedes. The floor is
    `2 / px_per_m`, the same one `fabric_stages` uses.

    **2. WHAT A SUB-PIXEL FIBRE ACTUALLY DOES TO LIGHT IS NOT A BUMP.** A hair
    is 0.07 mm; there is no framing in this film where one is a pixel. A bundle
    of parallel cylinders does not scatter like a rough surface, it scatters
    into a CONE about the fibre axis -- which is a highlight stretched
    perpendicular to the flow, i.e. the band around the head that reads as
    gloss. So the fibre moved out of the bump chain and into anisotropy with a
    real meridional tangent. See `hair_material`.

    **3. THE CLUMP MOVED TO THE MESH.** A lock of hair genuinely stands 1-2 mm
    proud of its neighbours over 8 mm, which is 20-30 deg, which is m = 3-5 --
    saturated. That is not a reason to render it saturated; it is a reason it
    cannot be a bump map at all, because a real lock also BREAKS THE
    SILHOUETTE and a normal perturbation never can. `build_hair`'s thickness
    field carries it now, directionally, and this shader is left with the
    sub-clump texture between locks. Same conclusion `fabric_stages` reached
    when it deleted `drape` -- "anything coarser than ~25 mm is GEOMETRY", and
    on hair the crossover is lower because the mesh is denser there.

    Targets are RADIANCE MODULATION under the film's 12.47 deg sun, not
    millimetres. Hair is allowed to run hotter than cloth -- it is a broken
    fibrous mass, not a woven sheet -- but 0.75 is a 75 % peak-to-peak swing and
    3.4 is a black-and-white stipple.
    """
    if HAIR_LEGACY:
        # THE SHIPPED PAIR, with no Nyquist floor -- which is the defect.
        return [("fibre", 0.0012, 0.15 * HAIR_RELIEF),
                ("clump", 0.0080, 1.10 * HAIR_RELIEF)]
    nyq_m = 2.0 / max(float(px_per_m), 1e-6)
    # THE TWO STAGES STRADDLE WHAT THE MESH CAN CARRY AND NEITHER SITS ON IT.
    # `build_hair` builds `n // 4` lock ridges, which is 15.4 mm at L0 and
    # 25 mm at L1, and its volume term is ~200 mm. A shader stage inside the
    # 15-25 mm band would be a normal map arguing with a shape -- which is what
    # `fabric_stages` deleted `drape` for. So the fine stage sits BELOW
    # everything the mesh can represent at any tier and the coarse one sits
    # between the locks and the volume.
    lam_lock, lam_swell = 0.0090, 0.0340
    all_stages = [
        # between-lock shading: the finest thing hair may still carry as a bump
        ("lock", lam_lock, amp_mm_for_modulation(0.78, lam_lock)),
        # groups of locks catching the light together, below the volume term
        ("swell", lam_swell, amp_mm_for_modulation(0.30, lam_swell)),
    ]
    return [(n_, l_, a_ * HAIR_RELIEF)
            for (n_, l_, a_) in all_stages if l_ >= nyq_m]


def _hair_ring_coord(nt, u, v, n_around, v_cells, phase):
    """A texture coordinate in the HAIR GRID's own parameterisation that is
    exactly periodic around the head, so a band texture on it has no seam.

    TWO TRAPS ARE CLOSED HERE AND BOTH HAVE BITTEN THIS PROJECT ALREADY.

    **The seam.** `hk_u` runs 0 .. (R-1)/R and then wraps to 0, so any noise
    evaluated on `u` directly jumps across that wrap and draws a line down the
    head at whatever azimuth the grid happened to start at. `wrap_noise` exists
    thirty lines up in the GEOMETRY for exactly this reason and there is no
    shader equivalent, so the coordinate is put on a CIRCLE instead:
    `(r cos 2 pi u, r sin 2 pi u, ...)` is periodic by construction, for any r.

    **The 1.60x.** With the coordinate on a circle of radius r, an angular
    period of 2 pi / N is an arc of `2 pi r / N` texture units -- and a Noise
    emits features of `NODE_K["noise"] / scale`, i.e. 1.60 units at scale 1. So
    `N` features around the head needs `r = N * 1.60 / (2 pi)`, and writing
    `r = N / (2 pi)` gets 1.60x too few. That factor is HUMAN-REFERENCE sec 3b's
    frequency trap and it is the same 1.60 that put a declared 8.6 mm crumple on
    the garment at 13.8 mm.
    """
    r = float(n_around) * NODE_K["noise"] / TAU
    th = nt.math("MULTIPLY", u, TAU)
    return nt.comb(nt.math("MULTIPLY", nt.math("COSINE", th), r),
                   nt.math("MULTIPLY", nt.math("SINE", th), r),
                   nt.math("ADD", nt.math("MULTIPLY", v,
                                          float(v_cells) * NODE_K["noise"]),
                           phase))


def _meridional_tangent(nt):
    """The surface tangent pointing along the head's meridians -- the direction
    hair falls -- built from the shading normal and world up, with no attribute.

        a = normalise(up x N)      the azimuthal direction (a horizontal ring)
        t = normalise(N x a)       the meridional direction (crown -> nape)

    Degenerate only where N is parallel to up, i.e. exactly at the crown, where
    the tangent is undefined for the same reason a pole is; the normalise leaves
    a bounded vector there and the anisotropy simply loses its axis on a few
    quads at the top of the head.

    WHY NOT `ShaderNodeTangent`: its RADIAL mode about Z returns `a`, not `t` --
    the ring, not the fall -- which stretches the highlight vertically down the
    head. That is the mirror image of the hair highlight and it would have
    looked deliberate.
    """
    N = nt.n("ShaderNodeNewGeometry")
    # `comb`, not a literal 3-tuple: `NT.pin` appends alpha to any length-3
    # sequence (it is written for colour sockets) and a VectorMath input takes
    # three floats, so a literal raises. One more socket-shape trap of exactly
    # the kind `pin`'s `expect=` was added for.
    up = nt.comb(0.0, 0.0, 1.0)
    a = nt.vmath("CROSS_PRODUCT", up, (N, 1))
    a = nt.vmath("NORMALIZE", a)
    t = nt.vmath("CROSS_PRODUCT", (N, 1), a)
    return nt.vmath("NORMALIZE", t)


def _hair_material_legacy(nt, col, v, Pj):
    """The SHIPPED hair shader, verbatim, as the positive control. `HAIR_LEGACY`.

    Do not tune this. Its whole value is that it is the graph the frames in
    `render/items/spectator_crowd/p5/` and `render/faceab/` were made with, so
    a new frame beside an old one differs in the hair and in nothing else.
    """
    global HAIR_STAGES_MM
    strand = nt.noise(Pj, tex_scale("noise", 0.0011), detail=3.0, rough=0.5)
    tone = nt.maprange(strand, 0.30, 0.70, 0.74, 1.28)
    base = nt.cmix(0.85, col, nt.cmix(tone, nt.cmix(1.0, col, (0.55, 0.52, 0.50),
                                                    "MULTIPLY"),
                                      nt.cmix(1.0, col, (1.55, 1.45, 1.35),
                                              "MULTIPLY")))
    base = nt.cmix(nt.maprange(v, 0.0, 1.0, 0.0, 0.35), base,
                   nt.cmix(0.5, base, (1.35, 1.28, 1.20), "MULTIPLY"))
    stages = hair_stages()
    HAIR_STAGES_MM = relief_budget(stages)
    fibre = nt.wave(Pj, tex_scale("wave_x", 0.0012), distortion=6.0, detail=3.0)
    nrm = relief(nt, fibre, NODE_PP["wave"], 0.0012, stages[0][2])
    clump = nt.noise(Pj, tex_scale("noise", 0.0080), detail=4.0)
    nrm = relief(nt, clump, NODE_PP["noise_d4"], 0.0080, stages[1][2],
                 normal=nrm)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.008)), 0.3, 0.7,
                        0.24, 0.46)
    b = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                          metallic=0.0)
    for nm, v2 in (("Specular IOR Level", 0.62), ("Anisotropic", 0.60),
                   ("Sheen Weight", 0.25)):
        if nm in b.inputs:
            b.inputs[nm].default_value = v2
    return nt.m


def hair_material(prefix, name="Hair"):
    """The hair shader. See `HAIR_RELIEF` for what this replaces and why.

    THE READ OF HAIR IS THREE THINGS AND ONLY ONE OF THEM IS A BUMP: a mass
    whose OUTLINE is broken (geometry -- `build_hair`), a highlight band that
    runs the wrong way round the head from every other highlight on the figure
    (anisotropy, below), and value variation from lock to lock (colour, below).
    The shipped version tried to get all three out of two isotropic bumps at
    1.2 mm and 8 mm, and got a crust.
    """
    global HAIR_STAGES_MM
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    col = _attr_col(nt)
    v = _attr_f(nt, "hk_v")
    u = _attr_f(nt, "hk_u")
    fid = _attr_f(nt, "hk_id")
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 71.3), 0.0, 0.0))
    if HAIR_LEGACY:
        return _hair_material_legacy(nt, col, v, Pj)
    # --- colour. LOCK-scale, not strand-scale.
    # The shipped value noise was a Noise at 1.1 mm -- 0.48 px at this item's
    # own 373.3 px/m -- driving a 0.74..1.28 multiplier, which is sub-pixel
    # colour speckle and is half of what the frames show. Hair is never one
    # colour, but the unit it varies over is a LOCK, and a lock is a band that
    # runs down the head rather than a blob. `hk_u` is the hair grid's own
    # azimuth and it is periodic by construction, so an integer number of bands
    # in u has no seam -- which a 3-D noise in object space cannot promise.
    band_n = nt.noise(_hair_ring_coord(nt, u, v, HAIR_TONE_LOCKS, 2.6,
                                       nt.math("MULTIPLY", fid, 19.7)),
                      1.0, detail=2.0, rough=0.5)
    tone = nt.maprange(band_n, 0.32, 0.68, 0.82, 1.20)
    base = nt.cmix(0.85, col, nt.cmix(tone, nt.cmix(1.0, col, (0.66, 0.63, 0.60),
                                                    "MULTIPLY"),
                                      nt.cmix(1.0, col, (1.42, 1.34, 1.26),
                                              "MULTIPLY")))
    # a slow drift over the whole head so the mass is not one flat value
    drift = nt.noise(Pj, tex_scale("noise", 0.075), detail=3.0, rough=0.5)
    base = nt.cmix(nt.maprange(drift, 0.30, 0.70, 0.0, 0.30), base,
                   nt.cmix(0.6, base, (1.22, 1.18, 1.12), "MULTIPLY"))
    # roots darker than ends
    base = nt.cmix(nt.maprange(v, 0.0, 1.0, 0.0, 0.30), base,
                   nt.cmix(0.5, base, (1.30, 1.24, 1.17), "MULTIPLY"))
    # --- relief, through the same budget the garment goes through -----------
    stages = hair_stages()
    HAIR_STAGES_MM = relief_budget(stages)
    nrm = None
    for nm_, lam, amp in stages:
        if nm_ == "lock":
            # DIRECTIONAL. A lock runs down the head, so its shading signal is
            # a function of azimuth that varies only slowly along the fall --
            # in the hair's OWN parameterisation, which is the only place that
            # direction exists. An isotropic 3-D noise at this wavelength is a
            # field of blobs and it is what the shipped shader had. 2.2 cells
            # along v against `n_lock` around is a 30:1 anisotropy, i.e. a lock
            # rather than a blob.
            n_lock = max(4.0, round(HAIR_HEAD_CIRC_M / lam))
            src = nt.noise(_hair_ring_coord(nt, u, v, n_lock, 2.2,
                                            nt.math("MULTIPLY", fid, 7.3)),
                           1.0, detail=3.0, rough=0.55)
            pp = NODE_PP["noise_d3"]
        else:
            src = nt.noise(Pj, tex_scale("noise", lam), detail=4.0, rough=0.55)
            pp = NODE_PP["noise_d4"]
        nrm = relief(nt, src, pp, lam, amp, normal=nrm)
    # --- gloss. Roughness falls from root to tip; the anisotropy is what makes
    # the highlight a BAND rather than a spot, and it needs a tangent that is
    # not the Principled default.
    # 0.26 at the tips was too low and the first render shows it: the crown
    # came back as moulded plastic with one hard highlight. Hair is glossy but
    # it is a bundle of rough fibres, not a lacquer; 0.34-0.50 with the
    # anisotropy doing the shaping is the read, and `Anisotropic` came down
    # from 0.72 with it.
    rough = nt.maprange(v, 0.0, 1.0, 0.50, 0.34)
    rough = nt.fmix(nt.maprange(drift, 0.3, 0.7, 0.0, 1.0), rough,
                    nt.math("ADD", rough, 0.09))
    b = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                          metallic=0.0)
    if "Tangent" in b.inputs:
        nt.pin(b, b.inputs.find("Tangent"), _meridional_tangent(nt))
    else:                                                  # pragma: no cover
        raise RuntimeError(
            "Principled BSDF has no `Tangent` input on this Blender; the hair "
            "anisotropy would silently use the default tangent, which runs "
            "round the head instead of down it. Sockets: %s"
            % sorted(i.name for i in b.inputs))
    for nm, v2 in (("Specular IOR Level", 0.48), ("Anisotropic", 0.55),
                   ("Anisotropic Rotation", 0.0), ("Sheen Weight", 0.18)):
        if nm in b.inputs:
            b.inputs[nm].default_value = v2
    return nt.m


def shoe_material(prefix, name="Shoe", sole=False):
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    col = _attr_col(nt)
    wear = _attr_f(nt, "hk_wear")
    fid = _attr_f(nt, "hk_id")
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 13.7),
                                    nt.math("MULTIPLY", fid, 29.1), 0.0))
    zone = _attr_f(nt, "hk_zone")
    scuff = nt.noise(Pj, tex_scale("noise", 0.023), detail=5.0, rough=0.62)
    base = nt.cmix(nt.math("MULTIPLY", wear,
                           nt.maprange(scuff, 0.45, 0.80, 0.0, 0.75)),
                   col, nt.cmix(0.6, col, (0.68, 0.66, 0.62), "MULTIPLY"))
    # A BELT IS LEATHER. It shares this material with the shoes so the figure
    # keeps one leather look, but a white trainer does not make a white belt.
    base = nt.cmix(_zone_is(nt, zone, ZONE_BELT, 0.45), base,
                   nt.cmix(0.88, col, (0.16, 0.12, 0.10), "MULTIPLY"))
    # Leather grain, then the two creases every worn shoe has across the vamp.
    # 13-18 deg: shallower than cloth, which is what separates them by eye.
    l_g = 0.0008 if not sole else 0.0019
    grain = nt.vor(Pj, tex_scale("voronoi", l_g), feature="F1")
    fine = nt.noise(Pj, tex_scale("noise", 0.0030), detail=5.0, rough=0.6)
    nrm = relief(nt, grain, NODE_PP["voronoi"], l_g, 0.090)
    nrm = relief(nt, fine, NODE_PP["noise_d5"], 0.0030, 0.22, normal=nrm)
    crease = nt.wave(Pj, tex_scale("wave_x", 0.0090), distortion=9.0, detail=3.0)
    nrm = relief(nt, crease, NODE_PP["wave"], 0.0090, 0.95, normal=nrm)
    crease2 = nt.noise(Pj, tex_scale("noise", 0.016), detail=4.0, rough=0.6)
    nrm = relief(nt, crease2, NODE_PP["noise_d4"], 0.016, 1.50, normal=nrm)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.011)), 0.3, 0.7,
                        0.72 if sole else 0.38, 0.94 if sole else 0.62)
    nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                      metallic=0.0)
    return nt.m


def eye_material(prefix, name="Eye"):
    """Sclera, iris and pupil placed from the eye cap's own `hk_v`.

    The cap is parameterised with v = 0 at the corneal apex and 1 at the rim, so
    an iris is a band in v and costs no geometry. At 11 px the dark pupil is the
    whole read: a white sphere in a socket looks blind.
    """
    nt = K.NT(prefix + name)
    v = _attr_f(nt, "hk_v")
    fid = _attr_f(nt, "hk_id")
    P = nt.object_coords()
    iris_hue = nt.ramp(fid, [(0.00, (0.055, 0.030, 0.016)),
                             (0.34, (0.115, 0.070, 0.030)),
                             (0.58, (0.090, 0.088, 0.052)),
                             (0.78, (0.055, 0.085, 0.090)),
                             (1.00, (0.070, 0.100, 0.135))])
    fib = nt.noise(nt.vmath("SCALE", P, None, 60.0), 120.0, detail=5.0)
    iris = nt.cmix(nt.maprange(fib, 0.35, 0.65, 0.0, 0.55), iris_hue,
                   nt.cmix(1.0, iris_hue, (1.8, 1.7, 1.6), "MULTIPLY"))
    sclera = nt.cmix(nt.maprange(nt.noise(P, 260.0), 0.4, 0.7, 0.0, 0.35),
                     (0.72, 0.70, 0.68), (0.62, 0.45, 0.42))
    col = nt.cmix(nt.maprange(v, 0.30, 0.42, 1.0, 0.0), sclera, iris)
    col = nt.cmix(nt.maprange(v, 0.13, 0.19, 1.0, 0.0), col, (0.004, 0.004, 0.005))
    rough = nt.fmix(nt.maprange(v, 0.42, 0.52, 1.0, 0.0), 0.30, 0.06)
    nt.principled_out(base_color=col, roughness=rough, metallic=0.0)
    return nt.m


def helmet_material(prefix, name="Helm"):
    """Clear-coated paint over composite: glossy, hard specular, no sheen.

    A helmet is the only hard, wet-looking surface on a covered figure and it
    is the whole reason the covered tier needs its own material slot. Run
    through the fabric shader -- 0.66 roughness with sheen -- it reads as a
    felt hat, which is what makes a helmeted figure look like a doll.

    The relief is deliberately tiny: 0.05 mm of orange peel at 1.6 mm and a
    2 mm swage line. A painted shell is SMOOTH, and its read comes from the
    specular lobe and the recessed aperture geometry, not from a bump.
    """
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    col = _attr_col(nt)
    fid = _attr_f(nt, "hk_id")
    zone = _attr_f(nt, "hk_zone")
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 17.3),
                                    nt.math("MULTIPLY", fid, 41.9),
                                    nt.math("MULTIPLY", fid, 7.7)))
    fleck = nt.noise(Pj, tex_scale("noise", 0.0016), detail=4.0, rough=0.5)
    base = nt.cmix(nt.maprange(fleck, 0.35, 0.65, 0.0, 0.16), col,
                   nt.cmix(1.0, col, (1.22, 1.20, 1.18), "MULTIPLY"))
    # scuffs and fingerprints where a helmet is actually handled
    hand = nt.noise(Pj, tex_scale("noise", 0.055), detail=5.0, rough=0.62)
    base = nt.cmix(nt.maprange(hand, 0.58, 0.82, 0.0, 0.22), base,
                   nt.cmix(0.5, base, (0.74, 0.73, 0.72), "MULTIPLY"))
    base = nt.cmix(_zone_is(nt, zone, ZONE_BELT, 0.45), base,
                   nt.cmix(0.9, base, (0.10, 0.10, 0.11), "MULTIPLY"))
    peel = nt.noise(Pj, tex_scale("noise", 0.0016), detail=3.0, rough=0.5)
    nrm = relief(nt, peel, NODE_PP["noise_d4"], 0.0016, 0.050)
    swage = nt.noise(Pj, tex_scale("noise", 0.019), detail=3.0, rough=0.4)
    nrm = relief(nt, swage, NODE_PP["noise_d4"], 0.019, 0.22, normal=nrm)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.030), detail=3.0),
                        0.3, 0.7, 0.085, 0.185)
    rough = nt.fmix(_zone_is(nt, zone, ZONE_BELT, 0.45), rough, 0.62)
    bsdf = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                             metallic=0.0)
    for nm, v in (("Specular IOR Level", 0.62), ("Coat Weight", 0.85),
                  ("Coat Roughness", 0.035)):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = v
    return nt.m


def visor_material(prefix, name="Visor"):
    """A dark tinted visor: near-black tint, mirror-smooth, a strong highlight.

    Deliberately opaque rather than transmissive. A transmissive visor at 767 px
    shows a balaclava through it and costs light paths for something that reads
    as a dark plate anyway; what carries the read is the SPECULAR streak of the
    sky across it, and that is the same either way.
    """
    nt = K.NT(prefix + name)
    P = nt.object_coords()
    fid = _attr_f(nt, "hk_id")
    Pj = nt.vmath("ADD", P, nt.comb(nt.math("MULTIPLY", fid, 9.1), 0.0, 0.0))
    tint = nt.ramp(fid, [(0.00, (0.010, 0.009, 0.008)),
                         (0.45, (0.014, 0.013, 0.016)),
                         (0.75, (0.022, 0.018, 0.010)),
                         (1.00, (0.008, 0.012, 0.016))])
    dust = nt.noise(Pj, tex_scale("noise", 0.0045), detail=5.0, rough=0.6)
    base = nt.cmix(nt.maprange(dust, 0.66, 0.88, 0.0, 0.20), tint,
                   (0.055, 0.053, 0.050))
    micro = nt.noise(Pj, tex_scale("noise", 0.0022), detail=3.0)
    nrm = relief(nt, micro, NODE_PP["noise_d4"], 0.0022, 0.014)
    rough = nt.maprange(nt.noise(Pj, tex_scale("noise", 0.012), detail=3.0),
                        0.35, 0.65, 0.025, 0.060)
    bsdf = nt.principled_out(base_color=base, roughness=rough, normal=nrm,
                             metallic=0.0)
    for nm, v in (("Specular IOR Level", 0.80), ("Coat Weight", 0.60),
                  ("Coat Roughness", 0.020)):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = v
    return nt.m


def figure_materials(prefix, crew=False):
    """The eleven slots, in MAT_* order. Shared by a whole population.

    `crew` swaps the soft slots for the covered tier: the overall is a stiffer,
    flatter, matte Nomex rather than a cotton polo, the hair slot carries the
    balaclava, and the shoe slots carry boot leather. The two hard slots --
    helmet shell and visor -- are always built, because a population is one
    material set and 120 crew figures cannot each own a helmet shader.
    """
    if not HAVE_BPY:
        raise RuntimeError("figure_materials needs Blender")
    if crew:
        soft = [
            fabric_material(prefix, "Top", stiff=0.95, sheen=0.18,
                            weave_mm=1.1),
            fabric_material(prefix, "Leg", stiff=0.95, sheen=0.18,
                            weave_mm=1.1),
            fabric_material(prefix, "Hair", stiff=0.60, sheen=0.22,
                            weave_mm=0.9),
        ]
    else:
        soft = [
            fabric_material(prefix, "Top", stiff=0.62, sheen=0.45,
                            weave_mm=1.3),
            fabric_material(prefix, "Leg", stiff=0.88, sheen=0.30,
                            weave_mm=1.8),
            hair_material(prefix),
        ]
    return [
        skin_material(prefix),
        soft[0], soft[1], soft[2],
        shoe_material(prefix, "Shoe", sole=False),
        shoe_material(prefix, "Sole", sole=True),
        eye_material(prefix),
        fabric_material(prefix, "Acc", stiff=0.80, sheen=0.35, weave_mm=1.5),
        skin_material(prefix, "Nail"),
        helmet_material(prefix),
        visor_material(prefix),
    ]


def material_node_census(mats):
    """What the gate's `material_depth` floor will count, before any render."""
    tot = 0
    per = {}
    for m in mats:
        n = sum(1 for nd in m.node_tree.nodes
                if nd.bl_idname.startswith("ShaderNodeTex")
                and nd.bl_idname != "ShaderNodeTexImage")
        n += sum(1 for nd in m.node_tree.nodes
                 if nd.bl_idname in ("ShaderNodeBump", "ShaderNodeDisplacement"))
        per[m.name] = n
        tot += n
    return tot, per


# ===========================================================================
# 16.  CROWD COMPOSITION -- grouping, occupancy, standing fraction, gaze
# ===========================================================================
#
# Defect 8: "occupancy is random-uniform. Real crowds cluster into groups --
# families, friends, pairs -- leaving irregular gaps, denser at the centre and
# front."  Defect 9: "no attention -- nobody is looking at anything."
# Defect 7: "nobody is standing, walking, or moving."
#
# `spectator_seated`'s own comment claims "people arrive in twos and threes" and
# the code under it is one Bernoulli draw per seat. This is the version that
# does what the comment says, and `occupancy_clumpiness()` measures it.

GROUP_SIZES = ((1, 0.24), (2, 0.30), (3, 0.21), (4, 0.13), (5, 0.08), (6, 0.04))


def compose_crowd(seed, n, extent, focus=None, walk_frac=0.20,
                  focus_frac=0.45, spacing=0.95, density=None):
    """Place `n` standing/walking figures in CONVERSATION GROUPS, with gaze.

    `extent` = (x0, y0, x1, y1). `density(x, y) -> [0,1]` biases where groups
    land; the default is a soft centre bias, because a paddock is busy at the
    garages and empty at the fence.

    Returns one dict per figure: position, facing, pose kind, gaze target and
    group id. It does NOT build geometry -- an item module decides what a
    "figure" is, and the crowd logic is the same whether they are marshals or
    spectators.
    """
    rr = rng_for(seed, 501)
    x0, y0, x1, y1 = [float(v) for v in extent]
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    rx, ry = max(0.5 * (x1 - x0), 1e-3), max(0.5 * (y1 - y0), 1e-3)
    if density is None:
        def density(x, y):
            d = math.hypot((x - cx) / rx, (y - cy) / ry)
            return float(np.clip(1.15 - 0.85 * d ** 1.6, 0.05, 1.0))
    out, placed, gid = [], [], 0
    guard = 0
    while len(out) < n and guard < 200 * n:
        guard += 1
        gx = rr.u(x0, x1)
        gy = rr.u(y0, y1)
        if rr.u() > density(gx, gy):
            continue
        if any((gx - px) ** 2 + (gy - py) ** 2 < (spacing * 2.2) ** 2
               for px, py in placed[-40:]):
            continue
        size = min(_pick_weighted(rr.u(), GROUP_SIZES), n - len(out))
        walking = rr.u() < walk_frac and size <= 3
        heading = rr.u(0.0, 360.0)
        gid += 1
        # a conversation group stands on an arc facing its own centre; the arc
        # is open, because a closed ring of people is a seance, not a chat
        span = math.radians(rr.u(150.0, 290.0))
        a0 = math.radians(rr.u(0.0, 360.0))
        rad = spacing * (0.45 + 0.20 * size) * (0.85 + 0.4 * rr.u())
        for k in range(size):
            f = 0.0 if size == 1 else k / (size - 1.0)
            a = a0 + span * f
            px = gx + (0.0 if size == 1 else rad * math.cos(a)) + rr.n(0, 0.10)
            py = gy + (0.0 if size == 1 else rad * math.sin(a)) + rr.n(0, 0.10)
            if walking:
                yaw = heading + rr.n(0, 8.0)
                kind, arche = "walk", None
            else:
                yaw = math.degrees(math.atan2(gy - py, gx - px)) - 90.0 \
                    + rr.n(0, 22.0)
                kind, arche = "stand", None
            look = None
            if focus is not None and rr.u() < focus_frac:
                look = tuple(focus)
            elif size > 1:
                j = (k + 1 + int(rr.u() * (size - 1))) % size
                aj = a0 + span * (0.0 if size == 1 else j / (size - 1.0))
                look = (gx + rad * math.cos(aj), gy + rad * math.sin(aj), 1.55)
            out.append({"pos": (px, py), "yaw_deg": float(yaw % 360.0),
                        "kind": kind, "archetype": arche, "look_at": look,
                        "group": gid, "walking": walking,
                        "group_size": size})
            placed.append((px, py))
            if len(out) >= n:
                break
    return out


def compose_seated(seed, seats, occupancy=0.82, aisle_cols=(), front_bonus=0.10,
                   edge_falloff=0.45, stand_frac=0.06):
    """Which seats are occupied, in CLUMPS, and who is standing up.

    `seats` = array of (row, col, x, y, z). Returns one record per OCCUPIED seat.

    A per-seat Bernoulli draw at 82 % gives a uniform speckle that reads as
    static; real occupancy is groups of 2-6 with whole empty patches between,
    the good rows full and the corners thin. The clump field below is a
    thresholded low-frequency noise plus a friend-group pass, and
    `occupancy_clumpiness()` measures the difference against the Bernoulli
    control rather than asserting it.
    """
    rr = rng_for(seed, 601)
    S = np.asarray(seats, float).reshape(-1, 5)
    row, col = S[:, 0], S[:, 1]
    nr = max(row.max(), 1.0)
    nc = max(col.max(), 1.0)
    r01, c01 = row / nr, col / nc
    # the expensive rows fill first; the corners of a block go last
    want = occupancy * (1.0 + front_bonus * (1.0 - r01)
                        - edge_falloff * (np.abs(c01 - 0.5) * 2.0) ** 2.4
                        - 0.22 * r01 ** 2.2)
    clump = K.fbm2(c01 * 7.0, r01 * 4.0, seed=int(seed) & 0x7FFFFFFF, oct=4)
    clump = (clump - clump.mean()) / max(clump.std(), 1e-6)
    p = np.clip(want + 0.30 * clump, 0.02, 0.995)
    take = rr.arr(len(S)) < p
    for c in aisle_cols:
        take &= col != c
    idx = np.flatnonzero(take)
    out = []
    for i in idx:
        out.append({"row": int(row[i]), "col": int(col[i]),
                    "pos": (float(S[i, 2]), float(S[i, 3])),
                    "z": float(S[i, 4]),
                    "kind": "stand" if rr.u() < stand_frac else "sit",
                    "look_at": None})
    return out


STAND_ROLES = ("sit", "stand", "lean_rail", "aisle", "steps", "turned")
"""What a person in a grandstand is DOING. The brief's defect 7 is "nobody
stands, walks or moves -- real stands always have people on their feet, in
aisles, climbing steps, turned around talking to the row behind", and the
superseded `compose_seated` had exactly two: `sit` and a 6 % `stand`."""

# Per-role pose archetypes, drawn from POSES. Every one of these is a
# distribution, not a pose -- see `sample_pose`.
STAND_POSES = {
    "sit": (("sit_upright", 0.15), ("sit_forward", 0.13),
            ("sit_back_folded", 0.12), ("sit_arms_spread", 0.08),
            ("sit_legs_crossed", 0.10), ("sit_phone", 0.11),
            ("sit_cheer", 0.05), ("sit_hands_lap", 0.09),
            ("sit_elbow_knee", 0.09), ("sit_slouch", 0.08)),
    "turned": (("sit_turn_neighbour", 1.00),),
    "stand": (("stand_relaxed", 0.22), ("stand_weight_side", 0.18),
              ("arms_folded", 0.12), ("hands_on_hips", 0.09),
              ("phone_held_up", 0.13), ("pointing", 0.07),
              ("watching_up", 0.09), ("arms_akimbo_watch", 0.10)),
    "lean_rail": (("lean_on_rail", 1.00),),
    "aisle": (("walk_stride", 0.55), ("walk_contact", 0.45)),
    "steps": (("walk_stride", 0.60), ("walk_contact", 0.40)),
}


def compose_stand(seed, seats, focus=None, occupancy=0.82, aisle_cols=(),
                  front_bonus=0.10, edge_falloff=0.45, stand_frac=0.09,
                  turned_frac=0.05, aisle_frac=0.020, steps_frac=0.014,
                  attention=0.80, group_mean=3.0):
    """A whole grandstand block: who is in it, what they are doing, and where
    they are looking. Supersedes `compose_seated`, which is kept below.

    `seats` = (row, col, x, y, z) per seat. `focus` = the thing everyone is
    watching, in world coordinates -- read it out of `telemetry/telemetry.csv`
    at the frame being rendered, because a crowd looking at a car that is not
    there is worse than a crowd looking nowhere.

    THE FOUR CROWD DEFECTS, and where each is answered:

      7  nobody stands or moves ... `STAND_ROLES`: a real block is ~9 % on
         their feet in the rows, 5 % turned round to the row behind, 2 % in
         the aisle and 1.4 % on the steps, and each role draws from its own
         archetype table rather than from one pose.
      8  occupancy is random-uniform ... the clump field below, measured by
         `occupancy_clumpiness` against a Bernoulli control at the same mean.
      9  no attention ... `attention` of the block gazes at `focus`, and the
         REST is not random either: a person who is not watching the car is
         looking at whoever they came with. `attention_spread` measures it.
      10 figures do not interact with the seats ... this function returns the
         seat's own z and the row behind's z; `build_figure(seat_z=)` solves
         the ischial contact on the FINISHED mesh.

    A GROUP IS THE UNIT, NOT A SEAT. People arrive together, sit together,
    stand up together and look at each other -- so occupancy, role and
    attention are all drawn per GROUP and only jittered per person. Drawing
    them per seat is what makes a crowd read as static: 7,800 independent
    coin flips have no structure at any scale a viewer can see.
    """
    rr = rng_for(seed, 601)
    S = np.asarray(seats, float).reshape(-1, 5)
    if not len(S):
        return []
    row, col = S[:, 0], S[:, 1]
    nr = max(row.max(), 1.0)
    nc = max(col.max(), 1.0)
    r01, c01 = row / nr, col / nc
    want = occupancy * (1.0 + front_bonus * (1.0 - r01)
                        - edge_falloff * (np.abs(c01 - 0.5) * 2.0) ** 2.4
                        - 0.22 * r01 ** 2.2)
    clump = K.fbm2(c01 * 7.0, r01 * 4.0, seed=int(seed) & 0x7FFFFFFF, oct=4)
    clump = (clump - clump.mean()) / max(clump.std(), 1e-6)
    p = np.clip(want + 0.30 * clump, 0.02, 0.995)
    take = rr.arr(len(S)) < p
    for c in aisle_cols:
        take &= col != c
    idx = np.flatnonzero(take)
    if not len(idx):
        return []
    # --- groups: runs of adjacent occupied seats in the same row ----------
    order = np.lexsort((col[idx], row[idx]))
    idx = idx[order]
    gid = np.zeros(len(idx), int)
    g, run = 0, 0
    target = max(1, int(round(rr.n(group_mean, 1.4))))
    for k in range(len(idx)):
        newrow = k and row[idx[k]] != row[idx[k - 1]]
        gap = k and not newrow and (col[idx[k]] - col[idx[k - 1]]) > 1
        if k == 0 or newrow or gap or run >= target:
            g += 1
            run = 0
            target = max(1, int(round(rr.n(group_mean, 1.4))))
        gid[k] = g
        run += 1
    ng = g + 1
    # THE BLOCK'S OWN FORWARD DIRECTION, taken out of the seat array rather
    # than guessed: rows climb AWAY from the track, so the bearing from the
    # back row's centroid to the front row's is where a seat faces. A guessed
    # forward is how a whole stand ends up facing the car park.
    lo_r = S[row <= row.min() + 0.5][:, 2:4].mean(axis=0)
    hi_r = S[row >= row.max() - 0.5][:, 2:4].mean(axis=0)
    fwd_deg = math.degrees(math.atan2(lo_r[1] - hi_r[1], lo_r[0] - hi_r[0]))
    # and the along-row direction, for aisle traffic
    lo_c = S[col <= col.min() + 0.5][:, 2:4].mean(axis=0)
    hi_c = S[col >= col.max() - 0.5][:, 2:4].mean(axis=0)
    row_deg = math.degrees(math.atan2(hi_c[1] - lo_c[1], hi_c[0] - lo_c[0]))
    # per-GROUP draws
    gr_stand = rr.arr(ng) < stand_frac
    gr_turn = rr.arr(ng) < turned_frac
    gr_att = rr.arr(ng)
    out = []
    grp_seats = {}
    for k, i in enumerate(idx):
        grp_seats.setdefault(int(gid[k]), []).append(
            (float(S[i, 2]), float(S[i, 3])))
    for k, i in enumerate(idx):
        gg = int(gid[k])
        u = rr.u()
        if gr_stand[gg]:
            role = "stand" if u < 0.90 else "lean_rail"
        elif gr_turn[gg] and u < 0.75:
            role = "turned"
        else:
            role = "sit"
        # attention is a GROUP property with a per-person defection
        looks = bool(focus is not None
                     and ((gr_att[gg] < attention) != (rr.u() < 0.12)))
        px, py = float(S[i, 2]), float(S[i, 3])
        jit = float(rr.n(0.0, 7.0))
        if looks:
            yaw = math.degrees(math.atan2(focus[1] - py, focus[0] - px)) + jit
            look = tuple(focus)
        else:
            # NOT WATCHING IS NOT RANDOM EITHER. Someone who is not looking at
            # the car is looking at whoever they came with; a person on their
            # own faces the way their seat does. Both are stated here so the
            # measurement downstream has a real yaw to measure and is not
            # reading a placeholder invented by the instrument.
            peers = [q for q in grp_seats[gg] if abs(q[0] - px) + abs(q[1] - py)
                     > 1e-6]
            if role == "turned":
                yaw = fwd_deg + 180.0 + rr.n(0.0, 26.0)
                look = None
            elif peers:
                q = peers[int(rr.u() * len(peers)) % len(peers)]
                yaw = math.degrees(math.atan2(q[1] - py, q[0] - px)) + jit
                look = (q[0], q[1], float(S[i, 4]) + 1.15)
            else:
                yaw = fwd_deg + rr.n(0.0, 34.0)
                look = None
        out.append({
            "row": int(row[i]), "col": int(col[i]),
            "pos": (px, py), "z": float(S[i, 4]),
            "role": role, "kind": "sit" if role in ("sit", "turned") else "stand",
            "archetype": _pick_weighted(rr.u(), STAND_POSES[role]),
            "group": gg, "group_size": len(grp_seats[gg]),
            "attends": looks, "look_at": look,
            "yaw_deg": float(yaw % 360.0),
        })
    # --- and the people who are not in a seat at all ----------------------
    # An aisle walker or someone on the steps is placed at a seat's x/y and
    # pushed sideways to the aisle, so they inherit the block's own geometry
    # rather than a guessed coordinate.
    n_seat = len(out)
    for role, frac in (("aisle", aisle_frac), ("steps", steps_frac)):
        for _ in range(int(round(n_seat * frac))):
            j = int(rr.u() * len(idx)) % len(idx)
            i = idx[j]
            side = 1.0 if rr.u() < 0.5 else -1.0
            px, py = float(S[i, 2]), float(S[i, 3])
            looks = bool(focus is not None and rr.u() < attention * 0.6)
            if looks:
                yaw = math.degrees(math.atan2(focus[1] - py, focus[0] - px))
                yaw += rr.n(0.0, 12.0)
            elif role == "steps":
                # someone on the steps is walking up or down them, i.e. along
                # the rows' rise, not along a row
                yaw = fwd_deg + (0.0 if rr.u() < 0.5 else 180.0) + rr.n(0, 12.0)
            else:
                yaw = row_deg + (0.0 if side > 0 else 180.0) + rr.n(0.0, 14.0)
            out.append({
                "row": int(row[i]), "col": -1,
                "pos": (px, py),
                "z": float(S[i, 4]), "role": role, "kind": "stand",
                "archetype": _pick_weighted(rr.u(), STAND_POSES[role]),
                "group": 0, "group_size": 1,
                "aisle_side": float(side),
                "attends": looks,
                "look_at": (tuple(focus) if looks else None),
                "yaw_deg": float(yaw % 360.0),
            })
    return out


def attention_spread(plan, focus, deg=20.0):
    """Is the crowd WATCHING something? Measured on the plan, with a control.

    Measured on the REALISED `yaw_deg` of every record, which `compose_stand`
    computes for watchers and non-watchers alike -- the first version of this
    function invented a yaw for the non-watchers and then measured its own
    invention, which is the failure this project has hit sixteen times.

    `frac_on` is the share whose facing is within `deg` of the bearing to
    `focus`; `circ_sd_deg` is the circular standard deviation of the bearing
    error over the whole block. The brief's defect 9 -- "a crowd all facing
    slightly different directions reads as dead" -- is a uniform distribution,
    which scores `frac_on = 2*deg/360` (0.111 at 20 deg) and a circular sd of
    about 104 deg. `compose_stand(attention=0.0)` is that control and it can be
    run in the same pass.
    """
    fx, fy = float(focus[0]), float(focus[1])
    err = []
    for r in plan:
        px, py = r["pos"]
        want = math.degrees(math.atan2(fy - py, fx - px))
        err.append(((float(r["yaw_deg"]) - want + 180.0) % 360.0) - 180.0)
    e = np.radians(np.asarray(err, float))
    if not e.size:
        return {"frac_on": 0.0, "circ_sd_deg": 0.0, "n": 0}
    Rlen = float(np.hypot(np.cos(e).mean(), np.sin(e).mean()))
    return {"frac_on": float(np.mean(np.abs(np.degrees(e)) <= deg)),
            "circ_sd_deg": math.degrees(math.sqrt(
                max(-2.0 * math.log(max(Rlen, 1e-9)), 0.0))),
            "n": len(err)}


def role_mix(plan):
    """The share of a block in each `STAND_ROLES` state, as a dict."""
    n = max(len(plan), 1)
    return {r: sum(1 for p in plan if p["role"] == r) / float(n)
            for r in STAND_ROLES}


def occupancy_clumpiness(taken, rows, cols):
    """Join-count clumpiness: P(neighbour occupied | occupied) minus the mean.

    0 for a uniform Bernoulli field by construction, positive for a clumped one.
    Reported against a Bernoulli control drawn at the same mean, so the number
    has something to be compared with -- which is the whole lesson of R2-018.
    """
    G = np.zeros((int(rows) + 1, int(cols) + 1), bool)
    for r, c in taken:
        G[int(r), int(c)] = True
    occ = G.mean()
    if occ <= 0 or occ >= 1:
        return 0.0, occ
    nb = np.zeros_like(G, float)
    nb[:, :-1] += G[:, 1:]
    nb[:, 1:] += G[:, :-1]
    nb[:-1, :] += G[1:, :]
    nb[1:, :] += G[:-1, :]
    cnt = np.zeros_like(G, float)
    cnt[:, :-1] += 1
    cnt[:, 1:] += 1
    cnt[:-1, :] += 1
    cnt[1:, :] += 1
    frac = float((nb[G] / cnt[G]).mean())
    return frac - occ, occ


# ===========================================================================
# 17.  MEASURING THE VARIATION -- because a hash that avalanches is NOT enough
# ===========================================================================

def measure_variation(figs, verbose=True):
    """Is this population rank-1 wearing 400 datablocks?

    THE TRAP THIS EXISTS FOR: `hash01` appears in 15 of 28 wave-1 modules in at
    least 10 implementations, one of which did not avalanche and collapsed seven
    independent properties onto one -- measured bit-flip rate 0.2458 against a
    correct 0.5032. Using itemkit's hash fixes the SOURCE. It does not prove the
    OUTCOME: eighteen independent draws can still be funnelled through one
    archetype table and come out a straight line in parameter space.

    So this measures the realised matrix:
      * the correlation matrix of the standardised per-figure parameters,
      * its eigenvalues, the PC1 share, and the PARTICIPATION RATIO
        (sum(l)^2 / sum(l^2)) -- the effective number of independent axes,
      * the nearest-neighbour distance distribution in that space,
      * and the same statistics for a RANK-1 CONTROL built from the same
        figures, so the test is shown to be able to fail.

    SOME CORRELATION IS CORRECT AND MUST NOT BE ENGINEERED AWAY. `bust` against
    `sex_f` measures 0.95 and `hair_len` against `sex_f` 0.67 -- those are sex
    dimorphism and a real grooming distribution, not a collapsed hash. What
    would indicate a collapse is a HIGH PARTICIPATION-RATIO DEFICIT: many axes
    all loading on one factor. That is the number to read, and the rank-1
    control is what it is read against.
    """
    keys = sorted(figs[0]["body"].params)
    X = np.array([[f["body"].params[k] for k in keys] for f in figs], float)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    live = sd > 1e-9
    Z = (X[:, live] - mu[live]) / sd[live]
    kl = [k for k, l in zip(keys, live) if l]
    C = np.corrcoef(Z, rowvar=False)
    ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    pr = float(ev.sum() ** 2 / max((ev ** 2).sum(), 1e-12))
    # nearest-neighbour distance, normalised by dimension
    D = np.sqrt(np.maximum(
        ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(axis=2), 0.0))
    np.fill_diagonal(D, np.inf)
    nn = D.min(axis=1) / math.sqrt(Z.shape[1])
    # RANK-1 CONTROL: one latent variable driving every parameter. If the
    # statistic cannot tell this from the real population it is not a statistic.
    g = np.random.default_rng(7).normal(size=len(figs))
    load = np.random.default_rng(11).normal(size=Z.shape[1])
    Zc = np.outer(g, load) + 0.02 * np.random.default_rng(13).normal(size=Z.shape)
    Cc = np.corrcoef(Zc, rowvar=False)
    evc = np.sort(np.linalg.eigvalsh(Cc))[::-1]
    prc = float(evc.sum() ** 2 / max((evc ** 2).sum(), 1e-12))
    off = np.abs(C - np.eye(len(C)))
    rep = {
        "n_figures": len(figs), "n_parameters": int(Z.shape[1]),
        "parameters": kl,
        "cv_stature": float(sd[keys.index("stature")] / mu[keys.index("stature")]),
        "pc1_share": float(ev[0] / ev.sum()),
        "participation_ratio": pr,
        "participation_ratio_of_rank1_control": prc,
        "max_abs_offdiag_correlation": float(off.max()),
        "mean_abs_offdiag_correlation": float(off.sum() / (len(C) * (len(C) - 1))),
        "nn_distance_min": float(nn.min()),
        "nn_distance_median": float(np.median(nn)),
        "eigenvalues": [round(float(v), 4) for v in ev],
    }
    if verbose:
        print("  parameters %d over %d figures" % (Z.shape[1], len(figs)))
        print("  PC1 carries %.1f %% of the variance; participation ratio "
              "%.2f of %d axes  (rank-1 control: %.2f)"
              % (100 * rep["pc1_share"], pr, Z.shape[1], prc))
        print("  worst |correlation| between any two parameters %.3f, mean %.3f"
              % (rep["max_abs_offdiag_correlation"],
                 rep["mean_abs_offdiag_correlation"]))
        print("  nearest-neighbour distance in parameter space: min %.4f, "
              "median %.4f (sigma units)" % (rep["nn_distance_min"],
                                             rep["nn_distance_median"]))
    return rep


def measure_pose_spread(figs, verbose=True):
    """How close is the closest pair of POSES, against a 6-pose control?

    The measured defect is "roughly six poses across ~600 figures", so the
    control is exactly that: the same population re-posed from six archetypes
    with no jitter. If the nearest-neighbour distance for the real population is
    not far above the control's, the pose library has not done anything.
    """
    V = np.array([pose_vector(f["pose"]) for f in figs], float)
    D = np.sqrt(np.maximum(((V[:, None, :] - V[None, :, :]) ** 2).sum(2), 0.0))
    np.fill_diagonal(D, np.inf)
    nn = D.min(axis=1)
    six = list(POSE_NAMES)[:6]
    ctrl = []
    for i in range(len(figs)):
        p = clamp_pose(dict(POSES[six[i % 6]]["j"]))
        full = {}
        for k in ("lumbar", "thorax", "neck", "head"):
            full[k] = p.get(k, (0.0, 0.0, 0.0))
        for base in ("clav", "arm", "fore", "hand", "hip", "knee", "foot"):
            for side in ("L", "R"):
                full[base + "_" + side] = p.get(base, (0.0, 0.0, 0.0))
        ctrl.append(pose_vector(full))
    Vc = np.array(ctrl)
    Dc = np.sqrt(np.maximum(((Vc[:, None, :] - Vc[None, :, :]) ** 2).sum(2), 0.0))
    np.fill_diagonal(Dc, np.inf)
    nnc = Dc.min(axis=1)
    rep = {"n": len(figs),
           "distinct_archetypes": len({f["archetype"] for f in figs}),
           "nn_pose_distance_deg_min": float(nn.min()),
           "nn_pose_distance_deg_median": float(np.median(nn)),
           "nn_pose_distance_deg_p05": float(np.quantile(nn, 0.05)),
           "control_6_pose_table_nn_min": float(nnc.min()),
           "control_6_pose_table_nn_median": float(np.median(nnc))}
    if verbose:
        print("  %d archetypes realised; nearest pose pair %.1f deg "
              "(median %.1f deg).  6-pose control: nearest pair %.1f deg, "
              "median %.1f deg"
              % (rep["distinct_archetypes"], rep["nn_pose_distance_deg_min"],
                 rep["nn_pose_distance_deg_median"],
                 rep["control_6_pose_table_nn_min"],
                 rep["control_6_pose_table_nn_median"]))
    return rep


# ===========================================================================
# 18.  SELFTEST -- measured, with controls, and every check able to fail
# ===========================================================================

def head_departs_from_ovoid(b, lod, seed):
    """How far the head is from being an ovoid, in mm. Returns a dict.

    Defect 1 is "heads are featureless ovoids". This measures exactly that:
    fit the general quadric a x^2 + b y^2 + c z^2 + d x + e y + f z = 1 to the
    head's own vertices and report the residual distance.

    THE WHOLE-SURFACE RMS IS THE WRONG STATISTIC and it took a failing check to
    see it: a head is mostly cranium, the cranium IS an ellipsoid, and averaging
    a 20 mm nose over 3,700 vertices of smooth skull gives 2 mm. The question is
    not "is the average vertex off the ellipsoid" but "does the FACE have
    features", so the face region is measured separately and the tail of the
    whole distribution is reported beside it. The control -- a plain ellipsoid
    on the same grid -- scores 0.000 on all three.
    """
    P, zone, f, _t, _s = head_points(b, lod, seed)
    V = P.reshape(-1, 3)
    fy = f[1].reshape(-1)

    def resid(X):
        A = np.column_stack([X[:, 0] ** 2, X[:, 1] ** 2, X[:, 2] ** 2,
                             X[:, 0], X[:, 1], X[:, 2]])
        c, *_ = np.linalg.lstsq(A, np.ones(len(X)), rcond=None)
        r = A @ c - 1.0
        g = np.column_stack([2 * c[0] * X[:, 0] + c[3],
                             2 * c[1] * X[:, 1] + c[4],
                             2 * c[2] * X[:, 2] + c[5]])
        return np.abs(r) / np.maximum(np.linalg.norm(g, axis=1), 1e-9) * 1000.0

    r = resid(V)
    face = fy > 0.45
    hh, hw, hd = b.head_h, b.head_w, b.head_d
    th = np.linspace(0.05, math.pi - 0.05, lod.head_v)
    ph = np.linspace(0.0, TAU, lod.head_u, endpoint=False)
    T, H = np.meshgrid(th, ph, indexing="ij")
    E = np.stack([np.sin(T) * np.cos(H) * 0.5 * hw,
                  np.sin(T) * np.sin(H) * 0.5 * hd,
                  np.cos(T) * 0.50 * hh], axis=-1).reshape(-1, 3)
    rc = resid(E)
    return {"rms_mm": float(np.sqrt((r ** 2).mean())),
            "face_rms_mm": float(np.sqrt((r[face] ** 2).mean())),
            "p99_mm": float(np.quantile(r, 0.99)),
            "max_mm": float(r.max()),
            "control_rms_mm": float(np.sqrt((rc ** 2).mean())),
            "control_p99_mm": float(np.quantile(rc, 0.99))}


def mesh_components(V, Q, T):
    """Connected components of a face soup, by union-find over the faces."""
    parent = np.arange(len(V))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, bq):
        ra, rb = find(a), find(bq)
        if ra != rb:
            parent[rb] = ra

    for faces in (Q, T):
        for fc in faces:
            for k in range(1, len(fc)):
                union(int(fc[0]), int(fc[k]))
    roots = np.array([find(i) for i in range(len(V))])
    return roots


def hand_finger_separation(b, lod, seed):
    """How many SEPARATE shells the hand is made of, and how far apart the
    fingertips are, in mm.

    Defect 6 is "hands are stumps. No fingers." A stump is one shell with one
    tip. This counts connected components of the emitted mesh and measures the
    gap between the tips of the finger-shaped ones -- so the answer comes from
    the artefact, not from the fact that `_finger` was called five times.

    The first version of this check clustered tip vertices at a 12 mm link
    distance and reported ONE cluster on a hand that plainly has five fingers:
    adjacent fingertips are 17 mm apart on a 190 mm hand and single-link
    clustering happily chains through them. A check that cannot tell a hand from
    a stump is R2-018 in miniature, so it was replaced rather than re-tuned.
    """
    sk = solve_skeleton(b, {})
    m = Mesh()
    build_hand(m, sk, "R", b, lod, seed, grip=0.10)
    V, Q, T, _QM, _TM, _A = m.finish()
    roots = mesh_components(V, Q, T)
    O = sk.origin["hand_R"]
    shells = []
    for r in np.unique(roots):
        P = V[roots == r]
        d = np.linalg.norm(P - O, axis=1)
        lo, hi = P.min(axis=0), P.max(axis=0)
        diag = float(np.linalg.norm(hi - lo))
        shells.append({"n": len(P), "reach": float(d.max()),
                       "diag": diag, "tip": P[int(np.argmax(d))]})
    shells.sort(key=lambda z: -z["reach"])
    digits = [z for z in shells if z["reach"] > 0.55 * shells[0]["reach"]
              and z["n"] > 12]
    if len(digits) < 2:
        return {"shells": len(shells), "digits": len(digits),
                "min_tip_gap_mm": 0.0}
    tips = np.array([z["tip"] for z in digits])
    D = np.linalg.norm(tips[:, None, :] - tips[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    return {"shells": len(shells), "digits": len(digits),
            "min_tip_gap_mm": float(D.min() * 1000.0),
            "max_reach_mm": float(shells[0]["reach"] * 1000.0)}


def selftest(verbose=True, n=96):
    out, fails = [], []

    def chk(name, ok, detail):
        out.append((name, bool(ok), detail))
        if not ok:
            fails.append(name)
        if verbose:
            print("  %-34s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))

    # [1] ONE hash, and it is itemkit's -- not a fifteenth implementation.
    flips = []
    for seed in range(48):
        for bit in range(20):
            a = int(hash01(seed, 1234) * (1 << 30))
            c = int(hash01(seed, 1234 ^ (1 << bit)) * (1 << 30))
            flips.append(bin(a ^ c).count("1") / 30.0)
    av = float(np.mean(flips))
    chk("hash_is_itemkits_and_avalanches",
        hash01 is K.hash01 and 0.40 <= av <= 0.60,
        "humankit.hash01 IS itemkit.hash01 (%s); measured bit-flip %.4f"
        % (hash01 is K.hash01, av))

    bodies = [sample_body(rng_for(9000 + i * 13, 1)) for i in range(400)]

    # [2] the vertical chain closes on stature
    err = []
    for b in bodies[:120]:
        sk = solve_skeleton(b, {})
        err.append(abs(float(sk.head_top()[2]) - b.stature))
    chk("stature_is_a_dimension", max(err) < 1e-4,
        "worst |head vertex - declared stature| over 120 bodies = %.5f mm"
        % (max(err) * 1000.0))

    # [3] segment ratios move INDEPENDENTLY of stature and of each other
    # ADULTS ONLY. A child's head IS relatively bigger and its legs ARE
    # relatively shorter, so over a mixed-age population `head_h` correlates
    # with stature at -0.70 BY DESIGN -- that is anthropometry, not a collapsed
    # hash, and suppressing it would make every child a scaled-down adult, which
    # is defect 5. The independence claim is about the RESIDUALS within an age
    # band, so that is what is measured.
    ad = [b for b in bodies if b.age_band in ("adult", "elder")]
    R = np.array([[b.ratio[k] / SEG_RATIO[k] for k in SEG_JITTER] for b in ad])
    H = np.array([b.stature for b in ad])
    cs = [abs(float(np.corrcoef(R[:, i], H)[0, 1])) for i in range(R.shape[1])]
    C = np.corrcoef(R, rowvar=False)
    off = np.abs(C - np.eye(len(C)))
    chk("segment_ratios_are_independent",
        max(cs) < 0.45 and off.max() < 0.35 and R.std(axis=0).min() > 0.015,
        "worst |corr(ratio, stature)| %.3f, worst |corr(ratio_i, ratio_j)| "
        "%.3f, smallest ratio sd %.4f" % (max(cs), off.max(), R.std(axis=0).min()))

    # [4] no pose leaves its anatomical range
    bad = 0
    for i in range(400):
        b = bodies[i % len(bodies)]
        _a, p = sample_pose(rng_for(7000 + i, 3), b)
        bad += len(pose_violations(p))
    chk("poses_are_anatomically_possible", bad == 0,
        "%d joint-axis violations over 400 sampled poses" % bad)

    # [5] the head is NOT an ovoid -- measured against a plain ellipsoid
    hd_ = head_departs_from_ovoid(bodies[3], LOD_L0, 4242)
    chk("head_departs_from_ellipsoid",
        hd_["face_rms_mm"] > 3.0 and hd_["p99_mm"] > 6.0
        and hd_["p99_mm"] > 20.0 * max(hd_["control_p99_mm"], 1e-6),
        "FACE departs from the head's own best-fit ellipsoid by %.2f mm RMS "
        "(whole head %.2f, p99 %.2f, max %.2f); a plain ellipsoid on the same "
        "grid measures %.3f / p99 %.3f"
        % (hd_["face_rms_mm"], hd_["rms_mm"], hd_["p99_mm"], hd_["max_mm"],
           hd_["control_rms_mm"], hd_["control_p99_mm"]))

    # [6] hands have separated fingers
    hf = hand_finger_separation(bodies[3], LOD_L0, 4242)
    chk("hand_has_separated_fingers",
        hf["digits"] >= 4 and hf["min_tip_gap_mm"] > 5.0,
        "%d separate shells in the hand, %d of them digit-length; closest two "
        "fingertips %.1f mm apart (a stump is 1 shell, 1 tip)"
        % (hf["shells"], hf["digits"], hf["min_tip_gap_mm"]))

    # [7] LOD tiers are ordered, and each is budgeted against its own distance
    figs = {}
    for tier in LOD_TIERS:
        f = build_figure(seed=4242, lod=tier, role="paddock", kind="stand",
                         archetype="stand_relaxed")
        figs[tier.name] = f["tris"]
    ordered = all(figs[a] > figs[b] for a, b in
                  (("L0", "L1"), ("L1", "L2"), ("L2", "L3")))
    chk("lod_tiers_are_ordered_and_budgeted",
        ordered and figs["L3"] > 390,
        "L0 %d, L1 %d, L2 %d, L3 %d tris/person (the rejected crowd was 390)"
        % (figs["L0"], figs["L1"], figs["L2"], figs["L3"]))

    # [8] variation, against a rank-1 control
    pop = [build_figure(seed=3000 + i * 17, lod=LOD_L3, role="paddock",
                        kind="stand") for i in range(n)]
    var = measure_variation(pop, verbose=False)
    chk("population_is_not_rank1",
        var["participation_ratio"] > 6.0
        and var["participation_ratio"] > 4.0
        * var["participation_ratio_of_rank1_control"],
        "participation ratio %.2f of %d parameters; the rank-1 control measures "
        "%.2f, and PC1 carries %.1f %%"
        % (var["participation_ratio"], var["n_parameters"],
           var["participation_ratio_of_rank1_control"],
           100 * var["pc1_share"]))

    # [9] poses do not repeat, against the 6-pose table this replaces
    ps = measure_pose_spread(pop, verbose=False)
    chk("poses_do_not_repeat",
        ps["nn_pose_distance_deg_min"] > 8.0
        and ps["control_6_pose_table_nn_min"] < 1.0,
        "closest pose pair %.1f deg over %d figures; the 6-pose table measures "
        "%.1f deg" % (ps["nn_pose_distance_deg_min"], n,
                      ps["control_6_pose_table_nn_min"]))

    # [10] contact is solved on the MESH
    below = max(f["contact"]["below_plane_mm"] for f in pop)
    chk("contact_is_solved", below < 0.05,
        "worst geometry below the contact plane %.4f mm over %d figures"
        % (below, n))

    # [11] crowd occupancy is CLUMPED, against a Bernoulli control
    rows, cols = 26, 90
    seats = np.array([[r, c, c * 0.5, r * 0.8, r * 0.42]
                      for r in range(rows) for c in range(cols)], float)
    occ = compose_seated(5150, seats, occupancy=0.82)
    cl, frac = occupancy_clumpiness([(o["row"], o["col"]) for o in occ],
                                    rows, cols)
    rr = np.random.default_rng(3)
    ctrl_take = [(r, c) for r in range(rows) for c in range(cols)
                 if rr.random() < frac]
    clc, _ = occupancy_clumpiness(ctrl_take, rows, cols)
    chk("occupancy_is_clumped", cl > 0.05 and cl > 3.0 * abs(clc),
        "join-count clumpiness %+.4f at %.0f %% occupancy; a uniform Bernoulli "
        "field at the same mean measures %+.4f" % (cl, 100 * frac, clc))

    # [11a] AND A GRANDSTAND IS NOT A SEATING PLAN. Defect 7 of the brief:
    #       "nobody stands, walks or moves ... real stands always have people
    #       on their feet, in aisles, climbing steps, turned around talking to
    #       the row behind." `compose_seated`, which this replaces, is run in
    #       the same pass as the POSITIVE CONTROL: it emits two states and its
    #       standing share is a per-seat 6 % coin flip with no aisle, no steps
    #       and nobody facing backwards.
    _cs = compose_seated(5150, seats, occupancy=0.82)
    _old_mix = len({("stand" if o["kind"] == "stand" else "sit") for o in _cs})
    _st = compose_stand(5150, seats, focus=(20.0, 6.0, 0.6), occupancy=0.82)
    mix = role_mix(_st)
    _upright = sum(v for k, v in mix.items() if k != "sit")
    chk("crowd_has_people_on_their_feet",
        _upright > 0.10 and mix["sit"] > 0.70
        and sum(1 for v in mix.values() if v > 0.005) >= 5
        and mix["aisle"] > 0.005 and mix["steps"] > 0.005
        and mix["turned"] > 0.01 and _old_mix == 2,
        "role mix over %d people: %s -- %.1f %% are not plainly seated. The "
        "superseded `compose_seated`, run here as the control, emits %d states "
        "(sit / a per-seat 6 %% stand) with no aisle, no steps and nobody "
        "turned to the row behind"
        % (len(_st), {k: round(v, 4) for k, v in mix.items()},
           100 * _upright, _old_mix))

    # [11b] AND THEY ARE ALL LOOKING AT THE SAME THING. Defect 9. Measured on
    #       the REALISED yaw of every record -- see `attention_spread`, whose
    #       first version invented a yaw for the non-watchers and measured its
    #       own invention. The control is the same composer at attention = 0,
    #       which must land on the uniform values (0.111 and ~104 deg).
    _fc = (20.0, 6.0, 0.6)
    _at = attention_spread(_st, _fc)
    _a0 = attention_spread(
        compose_stand(5150, seats, focus=_fc, occupancy=0.82, attention=0.0),
        _fc)
    chk("crowd_watches_the_car",
        _at["frac_on"] > 0.60 and _at["circ_sd_deg"] < 60.0
        and _a0["frac_on"] < 0.28 and _a0["circ_sd_deg"] > 85.0,
        "%.1f %% of the block faces the focus within 20 deg, circular sd "
        "%.1f deg; the same composer with attention = 0 -- the brief's "
        "\"crowd all facing slightly different directions\" -- measures "
        "%.1f %% and %.1f deg against the uniform distribution's 11.1 %% and "
        "104 deg"
        % (100 * _at["frac_on"], _at["circ_sd_deg"],
           100 * _a0["frac_on"], _a0["circ_sd_deg"]))

    # [12] THE AMPLITUDE TRAP, checked rather than remembered.
    #
    # WAVE1-PEEP-SYNTHESIS: "the wavelength model may well be right; the
    # AMPLITUDE is effectively zero, so nothing the model computes ever reaches
    # the image." Fabric measured FLATTER than a featureless placeholder ovoid.
    # A relief stage is not "2.2 mm of bump distance"; it is a SURFACE SLOPE,
    # and the slope is what the renderer shades. So this asserts the slope, in
    # degrees, and it carries the shipped-and-rejected numbers as its control.
    #
    # The control is the previous version of `fabric_material`, worked through
    # its own node responses: a bump Distance of 2.2 mm at strength 0.62 driving
    # a Noise whose 1st-99th percentile range is 0.269 emits 0.37 mm of relief,
    # at 13.8 mm rather than the declared 8.6 mm, which is 4.97 deg of slope.
    st = fabric_stages(0.62, 1.3)
    bud = relief_budget(st)
    fine = [r for r in bud if r["stage"].startswith("crumple")]
    slopes = [r["max_slope_deg"] for r in fine]
    px = [r["lambda_px_at_373"] for r in fine]
    old_slopes = [max_slope_deg(0.382, 0.0138), max_slope_deg(0.582, 0.0283)]
    # THE BAR IS A RADIANCE MODULATION UNDER THE FILM'S OWN SUN, not a slope.
    # Three amplitude sets have now been rendered and looked at, and reasoning
    # in millimetres of cloth got all three wrong in the same way -- because
    # what the eye judges is 2 theta / tan(elevation), and this film's sun is at
    # 12.47 deg where tan(e) = 0.221, a 4.5x amplifier:
    #
    #     shipped     5.0 deg -> m = 0.79   read as a machined cone
    #     first fix  22.6 deg -> m = 3.76   read as coarse stucco
    #     second fix 10.4 deg -> m = 1.66   read as THICK FELT (the crew bench)
    #     this       ~1.8 deg -> m = 0.28   isotropic; creases carry the rest
    #
    # The isotropic crumple must stay well under 1 -- a 100 % peak-to-peak swing
    # on a 4 px feature over an entire garment is felt, whatever it is called --
    # and the steep part of real cloth is delivered by the SPARSE `crease`
    # stage, which is ridged and gated so it acts on about a quarter of the
    # surface. Both facts are asserted here.
    mods = [2.0 * math.tan(math.radians(s))
            / math.tan(math.radians(SUN_ELEV_DEG)) for s in slopes]
    cr = [r for r in bud if r["stage"] == "crease"]
    cr_mod = (2.0 * math.tan(math.radians(cr[0]["max_slope_deg"]))
              / math.tan(math.radians(SUN_ELEV_DEG))) if cr else 0.0
    old_mods = [2.0 * math.tan(math.radians(s))
                / math.tan(math.radians(SUN_ELEV_DEG)) for s in old_slopes]
    # AND NOTHING IN THE SHADER MAY BE COARSER THAN 40 mm. That band belongs to
    # the mesh, and the C1/C2 control pair measured what happens when the
    # shader takes it anyway: with the geometry fold field switched off the
    # granular crust on the crew bench did not move at all, because a 120 mm
    # isotropic noise at m = 0.55 was painting popcorn over every garment. A
    # normal map cannot move a silhouette, so relief at form scale is spent
    # entirely on the wrong thing.
    coarse = [r for r in bud if r["lambda_mm"] > 40.0]
    chk("relief_modulation_is_cloth_not_felt",
        max(mods) < 0.55 and min(mods) > 0.10 and cr_mod > 1.5 * max(mods)
        and not coarse and 2.4 < min(px) < 4.2 and 5.2 < max(px) < 8.2,
        "isotropic crumple modulates the rendered radiance by %s peak-to-peak "
        "under the contract sun at %.2f deg (slopes %s deg at %s px); the "
        "sparse crease stage reaches %.2f, %.1fx deeper. %d shader stages are "
        "coarser than 40 mm (the mesh's band -- the deleted `drape` stage was "
        "120 mm at m = 0.55 and the C1 control frame proved it owned the "
        "crust). The shipped shader measured %s and the felt render 1.66"
        % ([round(m, 2) for m in mods], SUN_ELEV_DEG,
           [round(s, 2) for s in slopes], px, cr_mod,
           cr_mod / max(max(mods), 1e-6), len(coarse),
           [round(m, 2) for m in old_mods]))

    # [12a2] AND THE STEEP PART OF CLOTH IS NOW THE GEOMETRY'S JOB, so it is
    #        asserted where it lives. The superseded field is run in the same
    #        pass as the POSITIVE CONTROL: two fbm octave-sets have a slope
    #        distribution with p99/p50 ~ 3.3, which is what a Gaussian field
    #        gives and what plaster looks like; a ridged, gated field must run
    #        far above that while leaving the median flat.
    fp = [fold_relief_profile(9300 + 11 * i, part=p, mode="cloth")
          for i, p in enumerate(("torso", "arm", "leg"))]
    fo = [fold_relief_profile(9300 + 11 * i, part=p, mode="isotropic")
          for i, p in enumerate(("torso", "arm", "leg"))]
    chk("folds_are_sparse_and_oriented",
        all(f["m_p50"] < 0.55 for f in fp)
        and all(f["m_p99"] > 2.0 for f in fp)
        and all(f["peak_over_median"] > 5.0 for f in fp)
        and all(o["peak_over_median"] < 4.2 for o in fo)
        and all(0.15 < f["active_frac"] < 0.50 for f in fp),
        "garment shell slope against its own smooth base, on torso/arm/leg: "
        "median %s deg (m %s -- most of a panel is SMOOTH), 99th %s deg "
        "(m %s -- a real crease), peak/median %s against the superseded "
        "isotropic field's %s measured in this run, %s of the surface steeper "
        "than 4 deg, %s mm peak-to-peak against the old %s"
        % ([round(f["p50_deg"], 2) for f in fp],
           [round(f["m_p50"], 2) for f in fp],
           [round(f["p99_deg"], 1) for f in fp],
           [round(f["m_p99"], 2) for f in fp],
           [round(f["peak_over_median"], 2) for f in fp],
           [round(o["peak_over_median"], 2) for o in fo],
           [round(f["active_frac"], 2) for f in fp],
           [round(f["pp_mm"], 1) for f in fp],
           [round(o["pp_mm"], 1) for o in fo]))

    # [12a3] THE BRIDGE. `Sweep._bridge` rolls a ball along the outside of the
    #        garment's radial profile so the shell spans a hollow instead of
    #        wrapping into it. The operator is a morphological CLOSING and the
    #        two synthetic profiles below are why: a closing is the identity on
    #        a ramp and a plain dilation is not, which is the difference between
    #        cloth and armour. The groove residual is checked against the closed
    #        form W^2/8R, computed here and not by the code under test.
    bc = _bridge_controls(roll=CLOTH_ROLL_M)
    hg = [garment_hangs_off_the_body(9400 + 13 * i, part=p, relax="cloth")
          for i, p in enumerate(("torso", "arm", "leg"))]
    hd = [garment_hangs_off_the_body(9400 + 13 * i, part=p, relax="dilate")
          for i, p in enumerate(("torso", "arm", "leg"))]
    chk("cloth_bridges_hollows_without_inflating",
        bc["ramp_close_max_mm"] < 0.01 and bc["ramp_dilate_max_mm"] > 1.0
        and abs(bc["groove_residual_mm"] - bc["predicted_residual_mm"]) < 0.05
        # the TRUNK and the LEG are where the hollows are; the sleeve is not
        # bridgeable at any radius and saying so is part of the result.
        and all(h["inflation_mm"] < 2.0 for h in hg)
        and hg[0]["span_gain_mm"] > 4.0 and hg[2]["span_gain_mm"] > 1.0
        and all(d["inflation_mm"] > 1.4 * h["inflation_mm"] + 0.5
                for d, h in zip(hd, hg)),
        "a ball of R = %.2f m rolled along a straight taper moves it %.4f mm "
        "(a plain dilation moves the same taper %.2f mm) and bridges a 160 mm "
        "x 30 mm groove to a residual of %.2f mm against the closed form "
        "%.2f. On torso/arm/leg it lifts the p95 clearance by %s mm while the "
        "CONTACT clearance moves %s mm; the dilation control inflates contact "
        "by %s mm, which is the armoured figure this operator was chosen to "
        "avoid"
        % (CLOTH_ROLL_M, bc["ramp_close_max_mm"], bc["ramp_dilate_max_mm"],
           bc["groove_residual_mm"], bc["predicted_residual_mm"],
           [round(h["span_gain_mm"], 2) for h in hg],
           [round(h["inflation_mm"], 2) for h in hg],
           [round(d["inflation_mm"], 2) for d in hd]))

    # [12b] A GARMENT MUST NOT WEAR THE BODY'S MUSCLES. `garment_from_sweep`
    #       used to slice the BODY's Sweep and offset it, so the shell inherited
    #       `build_arm`'s 0.055 r noise and `build_torso`'s 0.010 chest_depth
    #       one-for-one -- large soft blobs that follow the limb like anatomy
    #       rather than hanging like cloth. Found by LOOKING at the B2 bench
    #       render, not by any check. The shipped path is kept as `relax="none"`
    #       and run here as the POSITIVE CONTROL: it must score a gain of ~1
    #       against the body's own noise field while the delivered path scores
    #       ~0, on the same body, the same seed and the same fold field.
    gi = [garment_inherits_body_relief(9100 + 7 * i, part=p)
          for i, p in enumerate(("arm", "torso"))]
    chk("garments_do_not_inherit_muscle_relief",
        all(g["gain_shipped"] > 0.85 for g in gi)
        and all(abs(g["gain_this"]) < 0.02 for g in gi)
        and all(g["m_removed"] > 0.15 for g in gi),
        "the noise-attributable part of the garment shell, isolated by building "
        "it twice off the same body (once off the real sweep, once off a "
        "relief-free twin) and projected onto the body's own noise field: "
        "shipped %s, this %s (arm, torso). The whole-residual form of the same "
        "statistic, which the rolling-ball bridge contaminates, reads %s. "
        "Removing the relief changes the shell normals by %s deg RMS, worth "
        "m = %s peak-to-peak radiance under the %.2f deg sun -- against the "
        "fold field's own 0.90 target and the shader's 0.28"
        % ([round(g["gain_shipped"], 3) for g in gi],
           [round(g["gain_this"], 4) for g in gi],
           [round(g["gain_total_this"], 3) for g in gi],
           [round(g["normal_rms_deg"], 2) for g in gi],
           [round(g["m_removed"], 3) for g in gi], SUN_ELEV_DEG))

    # [12c] ... and no skin came through the cloth as a result. Lofting from a
    #       relaxed base moves the shell INWARD wherever the body bulged, so the
    #       ease guard in `garment_from_sweep` is measured on the finished mesh:
    #       rays are cast at the figure and the share of first hits that land on
    #       MAT_SKIN is compared against the same bodies built as PADDOCK
    #       personnel, whose face, neck and forearms are exposed by design.
    _cf = [build_figure(seed=9200 + 31 * i, lod=LOD_L1, role="crew")
           for i in range(4)]
    _cs = [visible_material_fraction(f, MAT_SKIN, n_rays=600, seed=41 + i)
           for i, f in enumerate(_cf)]
    _ps = [visible_material_fraction(
        build_figure(seed=9200 + 31 * i, lod=LOD_L1, role="paddock",
                     body=_cf[i]["body"]), MAT_SKIN, n_rays=600, seed=41 + i)
        for i in range(4)]
    chk("relaxed_garments_still_cover_the_skin",
        # A RATIO, NOT AN ABSOLUTE ON THE CONTROL. This is a ray-cast estimate
        # -- 600 rays on each of 4 figures -- so the paddock control's own
        # value carries about half a point of sampling noise, and it sat at
        # 10.6 % against a bar of 10.0. It went red at 9.9 % on a build whose
        # covered figures had got BETTER (1.85 -> 1.75 %), i.e. the check would
        # have been reporting on its own binomial error. The fact being
        # asserted is that a covered figure shows far less skin than an
        # exposed one, and a ratio says that without depending on where the
        # control happens to land.
        float(np.mean(_cs)) < 0.030
        and float(np.mean(_ps)) > 4.0 * float(np.mean(_cs))
        and float(np.mean(_ps)) > 0.07,
        "%.2f %% of a covered figure's visible surface is bare skin; the same "
        "bodies built as paddock personnel measure %.1f %%, a factor of %.1f"
        % (100 * float(np.mean(_cs)), 100 * float(np.mean(_ps)),
           float(np.mean(_ps)) / max(float(np.mean(_cs)), 1e-9)))

    # [13] and the wavelength really is what was asked for. `tex_scale` must
    #      invert the MEASURED node response, not the 1/L that reads right.
    chk("tex_scale_inverts_the_measured_response",
        abs(NODE_K["noise"] / tex_scale("noise", 0.00804) - 0.00804) < 1e-9
        and abs(tex_scale("noise", 0.00804) - 199.0) < 1.0
        and abs(tex_scale("wave_x", 0.020) - 15.708) < 0.01,
        "an 8.04 mm noise needs Scale %.1f (the 1/L idiom gives %.1f, which "
        "emits %.2f mm); a 20 mm wave needs %.3f (1/L gives %.1f, emitting "
        "%.2f mm)"
        % (tex_scale("noise", 0.00804), 1.0 / 0.00804,
           1000.0 * NODE_K["noise"] * 0.00804,
           tex_scale("wave_x", 0.020), 1.0 / 0.020,
           1000.0 * NODE_K["wave_x"] * 0.020))

    # [14] DEFECT 3: things are actually HELD, and the grip is solved on them.
    #      The control is the same figure with the prop suppressed: if the
    #      triangle count does not move, nothing was built, and if the grip
    #      radius does not move the hand is not closing on anything.
    fp = build_figure(seed=5001, lod=LOD_L0, role="paddock",
                      archetype="phone_to_ear")
    fn = build_figure(seed=5001, lod=LOD_L3, role="paddock",
                      archetype="phone_to_ear")
    kinds = {}
    for i in range(64):
        kinds[build_figure(seed=6000 + i * 13, lod=LOD_L2,
                           role="paddock")["prop"]] = 1
    held = 1.0 - sum(1 for i in range(64)
                     if build_figure(seed=6000 + i * 13, lod=LOD_L2,
                                     role="paddock")["prop"] == "none") / 64.0
    chk("hands_hold_real_objects",
        fp["prop"] == "phone" and fp["prop_grip_r"] == PROPS["phone"]["grip_r"]
        and fn["prop"] == "none" and len(kinds) >= 4 and 0.5 < held < 0.95,
        "a `phone_to_ear` figure holds a phone and closes its fingers on an "
        "%.0f mm radius; %d prop kinds realised over 64 paddock figures, %.0f %% "
        "carrying something; at L3 (<60 px, a phone is 1.7 px) it is correctly "
        "dropped" % (1000 * fp["prop_grip_r"], len(kinds), 100 * held))

    # [15] LOD selection is driven by MEASURED screen presence
    # The three headline numbers are `peak_sharp_px_4k` READ OUT OF THE FILE,
    # not the 767.2 / 363.4 / 259.6 this check asserted until 2026-08-03. Those
    # were pre-shutter-fix ramped figures and 767.2 is 39 % high. The tier
    # boundaries did not move, so the seated crowd still lands on L1 by its own
    # projected height -- and that is exactly what defect 6 (mitten hands) is:
    # the presence number says L1 and the picture says the hand needs L0.
    chk("lod_maps_the_measured_presence",
        LOD.for_px(551.8) is LOD_L0 and LOD.for_px(278.7) is LOD_L1
        and LOD.for_px(199.1) is LOD_L1 and LOD.for_px(40.0) is LOD_L3
        and LOD.for_px(300.0) is LOD_L0 and LOD.for_px(299.9) is LOD_L1,
        "552 px (marshal/crew/paddock) -> L0, 279 px (GA standing) -> L1, "
        "199 px (seated crowd) -> L1, 40 px -> L3; the 300 px boundary is "
        "inclusive-below")

    # [16] EVERY EMITTED SURFACE FACES OUTWARD, and it is checked on the mesh.
    #
    # This check exists because 54 of 318 pieces on the shipped build were
    # inside-out -- the head shell, both ears, the hair mass, both shoe uppers,
    # both soles and all 22 tread bars -- and NOTHING in the module could see
    # it, because every check measured the model and none measured which SIDE
    # of the surface the renderer would get. Cycles flips a back-facing normal
    # for diffuse, so it renders, and it renders with every bump INVERTED: a
    # brow ridge lit as a groove, a hair clump as a gutter.
    #
    # The controls are built in the same run and are a PAIR, so the check is
    # shown to be able to move in both directions rather than merely to pass:
    # a polar grid emitted the ordinary way (which is INWARD -- that is the
    # defect) must be flipped, and the same grid emitted reversed must be left
    # alone.
    def _ctl(rev):
        mm = Mesh()
        S_, R_ = 10, 14
        th_ = np.linspace(0.06 * math.pi, 0.94 * math.pi, S_)
        ph_ = np.linspace(0.0, TAU, R_, endpoint=False)
        Pc = np.stack([np.stack([np.sin(t) * np.cos(ph_), np.sin(t) * np.sin(ph_),
                                 np.full(R_, np.cos(t))], axis=1) for t in th_])
        emit_grid(mm, Pc, 0, closed_u=True, cap_lo=(0, 0, 1.0),
                  cap_hi=(0, 0, -1.0), flip=rev)
        v0 = _signed_volume(mm)
        r_ = mm.orient_outward(report=True)
        return v0, _signed_volume(mm), r_["flipped"]

    # [17] A HAT IS ON THE HEAD, NOT ON THE FACE.
    hw_new, hw_old = {}, {}
    for k in ("cap", "visor", "bucket", "beanie"):
        hw_new[k] = min(headwear_clearance_mm(7000 + i * 97, k)
                        for i in range(8))
        hw_old[k] = min(headwear_clearance_mm(7000 + i * 97, k, legacy=True)
                        for i in range(8))
    chk("headwear_clears_the_eyes",
        min(hw_new.values()) > 0.0 and max(hw_old.values()) < 0.0,
        "worst clearance over the pupils %+.1f mm (cap %+.1f, visor %+.1f, "
        "bucket %+.1f, beanie %+.1f); the shipped constants measure %+.1f mm "
        "-- a peak at chin height and a band across the brow, which is what "
        "the 767 px bench render showed on every capped figure"
        % (min(hw_new.values()), hw_new["cap"], hw_new["visor"],
           hw_new["bucket"], hw_new["beanie"], max(hw_old.values())))

    a0, a1, af = _ctl(False)
    b0, b1, bf = _ctl(True)
    figs_o = [build_figure(seed=9700 + i * 131, lod=LOD_L2, role="paddock",
                           adult_only=True) for i in range(6)]
    worst = max(inside_out_fraction(f, n_rays=500, seed=17 + i)
                for i, f in enumerate(figs_o))
    ab = sum(len(f["orient"]["abstained"]) for f in figs_o)
    chk("every_surface_faces_outward",
        af == 1 and a1 > 0 and bf == 0 and b1 > 0 and ab == 0 and worst < 0.06,
        "controls: an inward grid (vol %+.3f) is flipped to %+.3f, an outward "
        "one (%+.3f) is left at %+.3f; on 6 figures 0 pieces undecided and at "
        "most %.1f %% of the visible surface is inside-out (the shipped build "
        "measured 10.5 %%, incl. the head at -0.966 and the hair at -0.97)"
        % (a0, a1, b0, b1, 100 * worst))

    # ---- NO FACE MAY HAVE ZERO AREA ---------------------------------------
    # A zero-area triangle has no cross product, hence no normal, and Cycles
    # shades it with whatever the interpolation happens to give. Found by
    # sweeping the composer over its whole parameter space rather than over a
    # sample: 2,293 of 2,360 figures carried a median of 33 of them, ALL of
    # them on the head, and nothing in this file could see it -- every check
    # here measures a distribution, a clearance or a slope, and a face of zero
    # area is none of those. Two independent causes, both a collapsed pole:
    #
    #   * `build_hair` put the whole of ring 0 at theta = 0, so its 33 vertices
    #     were a 10.8 mm NEEDLE on the polar axis (they do not coincide, because
    #     `grow` carries an azimuthal `lump`), ringed by 55 mm^2 sliver quads
    #     against a typical 307, with `cap_lo` fanning 33 zero-area triangles
    #     over the top;
    #   * `_peak`'s rim band was a closed strip of (loop, loop-with-its-halves-
    #     swapped): the same two points in both rows at each join.
    #
    # POSITIVE CONTROLS, both reproduced here rather than reached for by a
    # flag, so they fail on their own terms whatever the builders are rewritten
    # to do next.
    def _degen(fig):
        V, Q, T, _QM, _TM, _A = fig["mesh"].finish()
        F = [Q[:, (0, 1, 2)], Q[:, (0, 2, 3)]] if len(Q) else []
        if len(T):
            F.append(T)
        F = np.concatenate(F)
        e1, e2 = V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]
        return int((0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
                    < 1e-12).sum())

    figs_d = [build_figure(seed=8800 + i * 907, lod=LOD_L1, role="spectator",
                           adult_only=False) for i in range(24)]
    n_deg = sum(_degen(f) for f in figs_d)
    # control A: a fan to a point whose ring is already AT that point
    ring = np.stack([np.zeros(16), np.zeros(16), np.linspace(0, 0.01, 16)], 1)
    e1 = ring[1:] - ring[0]
    ctlA = int((0.5 * np.linalg.norm(np.cross(
        np.broadcast_to(np.array([0.0, 0.0, 0.011]) - ring[0], e1.shape),
        e1), axis=1) < 1e-12).sum())
    # control B: `_peak`'s superseded rim band, reproduced verbatim -- two rows
    # made of the same two edges concatenated in opposite orders, so the quad
    # that straddles each join has its four corners in two coincident pairs.
    tp = np.stack([np.linspace(-1, 1, 9), np.zeros(9), np.zeros(9)], 1)
    bt = tp - np.array([0.0, 0.0, 0.0035])
    r0 = np.concatenate([tp, bt[::-1]])
    r1 = np.concatenate([bt, tp[::-1]])
    ctlB = 0
    for k in range(len(r0)):                      # closed_u=True wraps
        j = (k + 1) % len(r0)
        for a, b_, c in ((r0[k], r0[j], r1[j]), (r0[k], r1[j], r1[k])):
            if 0.5 * np.linalg.norm(np.cross(b_ - a, c - a)) < 1e-12:
                ctlB += 1
    chk("no_face_has_zero_area",
        n_deg == 0 and ctlA > 0 and ctlB > 0,
        "%d zero-area faces over 24 mixed-age, mixed-sex figures; the two "
        "constructions that produced them measure %d and %d degeneracies as "
        "controls. A face with no area has no normal."
        % (n_deg, ctlA, ctlB))

    # [26] THE HAIR IS NOT A CRUST -- defect 3, in the same arithmetic the
    # garment was rescued with. Two claims, one check: every hair relief stage
    # must sit inside a plausible radiance modulation AND above the pixel
    # floor. The POSITIVE CONTROL is `HAIR_LEGACY`, which re-runs the SHIPPED
    # `hair_stages` -- not a reconstruction of it -- and must fail both.
    def _hair_m(stages):
        te = math.tan(math.radians(SUN_ELEV_DEG))
        return [2.0 * math.radians(max_slope_deg(a, l)) / te
                for _n, l, a in stages], [l for _n, l, _a in stages]

    global HAIR_LEGACY
    _was = HAIR_LEGACY
    HAIR_LEGACY = False
    m_new, lam_new = _hair_m(hair_stages())
    HAIR_LEGACY = True
    m_old, lam_old = _hair_m(hair_stages())
    HAIR_LEGACY = _was
    nyq = 2.0 / FIGURE_PX_PER_M
    ok_new = (max(m_new) <= 1.30 and min(lam_new) >= nyq)
    ok_old = (max(m_old) > 2.0 and min(lam_old) < nyq)
    chk("hair_relief_is_not_a_crust", ok_new and ok_old,
        "hair shader stages modulate the rendered radiance by %s peak-to-peak "
        "at wavelengths %s mm, all of them above the %.2f mm pixel floor at "
        "%.1f px/m. The SHIPPED stages, re-run here as the control via "
        "HAIR_LEGACY, measure %s at %s mm -- %.1fx the modulation, with the "
        "fine stage at %.2f of the floor, i.e. per-pixel noise at every "
        "distance. Cloth was rejected by eye as stucco at 1.57."
        % ([round(x, 2) for x in m_new], [round(1000 * l, 1) for l in lam_new],
           1000 * nyq, FIGURE_PX_PER_M, [round(x, 2) for x in m_old],
           [round(1000 * l, 1) for l in lam_old],
           max(m_old) / max(max(m_new), 1e-9), min(lam_old) / nyq))

    # [27] THE FACE'S SHARP LOBES REACH THE MESH -- defect 1, and its mechanism.
    # The fifth pass measured the ANALYTIC lobe field at m = 2.22 and concluded
    # the face was not flat. It is not; but on the L1 grid most of the sharp
    # half of it was never sampled. Measured the only way that cannot be argued
    # with: build the head twice off one body, once with a lobe and once with
    # its amplitude zeroed, and take the largest vertex displacement between
    # the twins. That IS the realised depth.
    #
    # THE CONTROLS ARE BOTH REQUIRED AND THEY PULL OPPOSITE WAYS:
    #   * FACE_LOBE_FLOOR = 0 (the shipped build) must FAIL on the sharp lobes;
    #   * the BROAD lobes -- chin, cheek -- must be unmoved by the fix in both
    #     builds, or the statistic is measuring the change and not the feature.
    global FACE_GRID_WARP, FACE_LOBE_FLOOR
    _w0, _f0 = FACE_GRID_WARP, FACE_LOBE_FLOOR

    def _realised(lod_, name, seeds_):
        full = HEAD_LOBES
        row = next(r for r in full if r[0] == name)
        frac = []
        try:
            for sd in seeds_:
                bb = sample_body(rng_for(sd, 1), adult_only=True)
                P1 = head_points(bb, lod_, sd)[0]
                globals()["HEAD_LOBES"] = tuple(
                    r if r[0] != name else r[:7] + (0.0,) + r[8:] for r in full)
                P0 = head_points(bb, lod_, sd)[0]
                globals()["HEAD_LOBES"] = full
                got = float(np.linalg.norm(P1 - P0, axis=-1).max())
                frac.append(got / max(abs(row[7]) * bb.head_h, 1e-9))
        finally:
            globals()["HEAD_LOBES"] = full
        return float(np.mean(frac))

    _sds = [4000 + i * 7919 for i in range(8)]
    SHARP = ("lip_line", "lid_upper_L", "nostril_L", "subnasale")
    BROAD = ("chin", "cheek_L", "brow_ridge_L")
    FACE_GRID_WARP, FACE_LOBE_FLOOR = 0.0, 0.0
    sharp_old = {k: _realised(LOD_L1, k, _sds) for k in SHARP}
    broad_old = {k: _realised(LOD_L1, k, _sds) for k in BROAD}
    FACE_GRID_WARP, FACE_LOBE_FLOOR = 1.0, 1.0
    sharp_new = {k: _realised(LOD_L1, k, _sds) for k in SHARP}
    broad_new = {k: _realised(LOD_L1, k, _sds) for k in BROAD}
    FACE_GRID_WARP, FACE_LOBE_FLOOR = _w0, _f0
    ok_sharp = min(sharp_new.values()) >= 0.80
    ok_ctl = max(sharp_old.values()) < 0.65
    ok_broad = all(abs(broad_new[k] - broad_old[k]) < 0.05 for k in BROAD)
    chk("face_lobes_survive_the_head_grid",
        ok_sharp and ok_ctl and ok_broad,
        "at L1 -- 85 %% of a grandstand -- the sharp face lobes now realise %s "
        "of their own depth on the MESH. The shipped grid, re-run here as the "
        "control, realises %s: the mouth arrives at %.0f %% and is "
        "reconstructed across an 11 mm cell, which is a 7 deg ramp where the "
        "lobe asks for a 57 deg wall. NEGATIVE CONTROL, the lobes that were "
        "never sub-grid: %s shipped vs %s now, unmoved."
        % ({k: round(v, 2) for k, v in sharp_new.items()},
           {k: round(v, 2) for k, v in sharp_old.items()},
           100 * sharp_old["lip_line"],
           {k: round(v, 2) for k, v in broad_old.items()},
           {k: round(v, 2) for k, v in broad_new.items()}))

    if HAVE_BPY:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        mats = figure_materials("HKSELF_")
        tot, per = material_node_census(mats)
        wired = all(any(l.to_node.bl_idname == "ShaderNodeOutputMaterial"
                        for l in m.node_tree.links) for m in mats)
        chk("materials_wired_and_deep", wired and tot >= 6 * len(mats),
            "%d procedural texture/bump nodes over %d materials (gate hero "
            "floor is 6 reachable nodes): %s" % (tot, len(mats), per))
        # THE HAIR'S ANISOTROPY HAS A TANGENT, AND IT IS THE RIGHT SOCKET.
        # `Tangent` is input **18** of the Blender 5.2 Principled BSDF, so this
        # is exactly the shape of the trap `bump_by_name` documents: an
        # index-pinned write would land on something else entirely, and an
        # anisotropy with no tangent silently uses the default, which runs
        # ROUND the head instead of down it -- the mirror image of a hair
        # highlight, which would have looked deliberate.
        hm = bpy.data.materials.get("HKSELF_Hair")
        hb = next((n for n in hm.node_tree.nodes
                   if n.bl_idname == "ShaderNodeBsdfPrincipled"), None) \
            if hm else None
        tg = hb.inputs["Tangent"] if (hb and "Tangent" in hb.inputs) else None
        aniso = float(hb.inputs["Anisotropic"].default_value) if hb else 0.0
        chk("hair_anisotropy_has_a_tangent",
            tg is not None and tg.is_linked and aniso > 0.2,
            "Principled `Tangent` is input [%s] on this Blender and is wired "
            "from %s; Anisotropic = %.2f. Wired BY NAME -- an index write "
            "would land on socket 18 of something else, and an unwired "
            "Tangent is the default one, which circles the head instead of "
            "running down it."
            % (hb.inputs.find("Tangent") if hb else "?",
               tg.links[0].from_node.bl_idname if (tg and tg.is_linked)
               else None, aniso))
        # EVERY BUMP'S HEIGHT MUST BE LINKED, AND FILTER WIDTH MUST NOT BE.
        # This is the check that would have caught the defect described at
        # length in `bump_by_name`: on Blender 5.2 the Bump node grew a
        # `Filter Width` input at index 2, so `itemkit.NT.bump`'s index-based
        # pinning puts the height into Filter Width, the normal chain into
        # Height, and leaves the FIRST bump of every chain driven by a constant
        # -- which has zero gradient and therefore emits no relief at all.
        #
        # The NEGATIVE CONTROL is built right here: one material wired the
        # itemkit way, so the check is shown to reject the thing it exists for
        # rather than merely to pass the thing it was written against.
        bad = []
        nbump = 0
        for m_ in mats:
            for nd in m_.node_tree.nodes:
                if nd.bl_idname != "ShaderNodeBump":
                    continue
                nbump += 1
                # `l.to_node is nd` is FALSE for bpy wrappers even when they
                # address the same node -- RNA hands out a fresh Python object
                # per access. The first version of this check used `is` and
                # reported all 31 stages as faults, i.e. it was a broken
                # instrument accusing working code, which is R2-017's whole
                # family. Compare by name.
                lk = {l.to_socket.name for l in m_.node_tree.links
                      if l.to_node.name == nd.name}
                if "Height" not in lk:
                    bad.append("%s: Height unlinked (default %.3f)"
                               % (m_.name, nd.inputs["Height"].default_value))
                if "Filter Width" in lk:
                    bad.append("%s: a signal is wired into Filter Width" % m_.name)
        # THE CONTROL BUILDS THE DEFECT ITSELF, and it did not always. It used
        # to call `itemkit.NT.bump`, which WAS index-pinned and therefore
        # miswired 2 of 2. `itemkit` has since been corrected -- so the control
        # stopped failing, and this check went red reporting "miswires 0 of 2"
        # while the 31 real stages were all correct. A negative control that
        # depends on another module staying broken is not a control. The old
        # index pinning is reproduced here verbatim instead, so this check can
        # always fail and always for the reason it names.
        ctl = K.NT("HKSELF_BumpControl")
        cn = ctl.noise(ctl.object_coords(), 100.0)
        prev = None
        for _k in range(2):
            nd = ctl.n("ShaderNodeBump")
            ctl.pin(nd, 0, 1.0)                          # Strength
            ctl.pin(nd, 1, 0.001)                        # Distance
            ctl.pin(nd, 2, cn)                # -> Filter Width on Blender 5.2
            if prev is not None:
                ctl.pin(nd, 3, prev)          # -> Height, i.e. a NORMAL vector
            prev = (nd, 0)
        cbad = 0
        for nd in ctl.t.nodes:
            if nd.bl_idname == "ShaderNodeBump":
                lk = {l.to_socket.name for l in ctl.t.links
                      if l.to_node.name == nd.name}
                if "Height" not in lk or "Filter Width" in lk:
                    cbad += 1
        chk("every_bump_drives_height_not_filter_width",
            not bad and nbump >= 12 and cbad == 2,
            "%d bump stages across %d materials, all with Height linked and "
            "nothing in Filter Width; the same graph pinned BY INDEX -- the "
            "shipped idiom, reproduced here as the negative control -- miswires "
            "%d of 2 (Blender 5.2 inserted Filter Width at index 2). Faults: %s"
            % (nbump, len(mats), cbad, bad[:4] or "none"))

        c = K.coll("HKSELF")
        f = build_figure(seed=4242, lod=LOD_L0, role="paddock", kind="stand")
        ob = emit_mesh("HKSELF_Fig", f["mesh"], c, mats)
        me = ob.data
        have = {a.name for a in me.attributes}
        chk("vertex_channels_survive_emit",
            set(Mesh.CHANNELS) | {"hk_col"} <= have,
            "attributes on the emitted mesh: %s" % sorted(
                a for a in have if a.startswith("hk_")))
        try:
            K.assert_no_external_assets()
            ok = True
            why = "zero image-texture nodes, zero external image files"
        except RuntimeError as exc:
            ok = False
            why = str(exc)
        chk("law1_no_external_assets", ok, why)
    else:
        chk("bpy_half", True, "skipped -- not running inside Blender")

    print("\n  humankit selftest: %d checks, %d FAILED %s"
          % (len(out), len(fails), fails or ""))
    return not fails


if __name__ == "__main__":
    _argv = sys.argv
    _argv = _argv[_argv.index("--") + 1:] if "--" in _argv else _argv[1:]
    if "--selftest" in _argv or not _argv:
        sys.exit(0 if selftest() else 1)

