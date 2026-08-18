"""tree_oak — pedunculate oak (Quercus robur), the broadleaf hero. HAND-BUILT.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/tree_oak.py -- --test --out world/items/tree_oak_test.blend

WHAT THIS ITEM IS, AND WHAT THE NUMBERS BEHIND IT ACTUALLY SAY
==============================================================
`docs/WAVE2-SCOPE.md` sec 3.2 puts vegetation at the head of wave 2: thirteen of
the film's 21 macro-scrutiny items are trees, every one unbuilt, and they carry
the largest instance populations in the manifest. `tree_oak` is the largest of
them: **4,500 declared instances at 17.0 m**.

`docs/screen_presence.json` measures, over all 2,978 frames:

    frames_visible               2289   (76.9 % of the film)
    frames_at_300px               815
    frames_at_150px               928
    peak_unocc_sharp_px_4k       2160.0  (frame-filling) at frame 2316, beat 5
    min_depth_m                   4.577

**AND THE HONESTY CAVEAT, WHICH THIS MODULE CARRIES RATHER THAN LAUNDERS.**
`screen_presence.json`'s own `presence_unverified_2026_08_04` block says those
scores are **HOST UPPER BOUNDS**, and that *"a HERO verdict on an item listed
ABSENT in the census must not be quoted"*. `tree_oak` is unbuilt, so 2160 px and
4.577 m are numbers for its **93 hosts** — `VEG_shrub_bramble_L0`,
`VEG_shrub_gorse_L0`, `VEG_sapling`, `VEG_fern` and 89 more, i.e. LOW
UNDERSTOREY — not for a 17 m tree. All five tree species in that file report an
identical `min_depth_m` of 4.577, which is the signature of one shared host set,
not of five measurements. **2160 px is NOT quoted here as a measurement of a
tree, and neither is 4.577 m.**

So this module states a RANGE and gates at a stated distance inside it:

    NEAR  4.577 m   the measured near end OF THE HOST CLUSTER. 815.7 px/m,
                    1.226 mm/px. A HOST BOUND. At 35 mm the frame is 4.71 m
                    wide, so this is a bole macro: 4.7 m of trunk across the
                    frame, bark fissures 61 px apart.
    FULL  29.37 m   the distance at which a 17.0 m tree exactly fills the 2160
                    px frame height at 35 mm, which is what `overfills_frame:
                    true` and a CLAMPED `peak_px_4k` of 2160.0 can support and
                    no more. 127.1 px/m, 7.87 mm/px.

    The manifest's own 30.0 m / 2116 px is internally consistent with FULL
    (3733.3/30 * 17.0 = 2115.5 px) and is therefore NOT wrong -- it is the FAR
    end of the range. What it does not do is bound the NEAR end, and the near
    end is what decides how this is built.

**WHAT WOULD SETTLE IT.** Place this module into the assembled world and re-run
`tools/retier.sh` / `tools/screen_presence.py`, which measures each item as
itself instead of against its host. Until that is done, the framing above is a
STATED RANGE with a stated provenance, not a measurement of this item.

THE RELIEF BUDGET, DERIVED — NEVER TYPED (Law 1)
================================================
Every amplitude in this file comes out of `K.relief_amplitude_for(m, lam)` or
`K.slope_for_modulation(m)`, both of which read `world_contract.SUN_ELEV_DEG`.
No amplitude and no amplifier is written down anywhere in this file -- if the
sun moves, every furrow in the wood moves with it. `RELIEF_STAGES` below is
the whole budget in one table, every row carrying its own wavelength, because
the same 0.5 mm is m = 1.74 on an 8 mm crumple and m = 0.14 on a 100 mm flute.

AND THE PIXEL FOOTPRINT THAT MAKES THE BUDGET MEAN ANYTHING (Law 3)
===================================================================
The circuit surface shipped twenty procedural layers and read as untextured
because eight octaves were above the camera's resolvable band and nine below.
Every row of `RELIEF_STAGES` states which of the two framings resolves it:

    stage              lam        at 4.577 m      at 29.37 m
    root flare        550 mm       448 px           70 px
    fissure major     165 mm       135 px           21 px
    fissure network    78 mm        64 px           10 px
    cross fracture     26 mm        21 px          3.3 px
    plate surface     9.0 mm       7.3 px          1.1 px   <- geometry floor
    bark crust        2.6 mm       2.1 px          0.33 px  <- SHADER, near only
    leaf midrib       5.0 mm       4.1 px          0.64 px
    leaf blade grain  1.8 mm       1.5 px          0.23 px  <- SHADER, near only

Five octaves resolve at the near end, five at the far end, and the finest three
are deliberately SHADER stages because a 2.6 mm geometric feature would need a
1.3 mm mesh and 4,500 trees of it does not exist on any machine. Nothing sits
below 0.2 px at either end; nothing is built that cannot be seen.

THE ONE PLACE THIS BUILD IS DELIBERATELY UNDER THE PHYSICAL TRUTH
=================================================================
Real Quercus robur furrow walls stand at 55-70 deg from the plate plane, which
at this sun is m = 7.0-8.7. `K.RELIEF_BANDS["hard_feature"]` tops out at 6.00.
**The band wins, and this is a stated choice rather than an accident.** The
fissure network is built at m = 5.40 and the major network at m = 4.60 -- the
top of the band -- which at their pitches gives about 14 mm of combined furrow
against a real veteran's 20-25 mm. If the macro reads too smooth, THE NUMBER TO
CHANGE IS `fissure_network`'s m, and changing it leaves the band; that is the
argument to have with a render in front of you, not in advance.

DETAIL IS A GEOMETRY PROBLEM (Law 7)
====================================
The world already contains an oak: `build_terrain.SPECIES["oak"]`, 6 orders,
29,000 leaves, `sides=(11, 7, 5, 4, 4, 3)` and a bark SHADER on a smooth
11-sided tube. At the far end that is right and it is not this item. **An
11-sided cylinder at 4.577 m is a 24-sided-per-visible-face polygon 0.53 m
across and its bark is a paint job.** The wave-1 post-mortem's finding across six
independent reviews was "the mechanism is in the code and its amplitude is 3-5x
too small to survive to pixels", and the record adds: "on this film's sun, the
mesh carries the read and the shader garnishes it".

So the bole and the primary limbs of this oak carry their bark as REAL
DISPLACED GEOMETRY -- a fissure network whose furrows are modelled arrises, not
a normal map -- at 9 mm circumferential / 15 mm axial sampling, and the shader
adds only what is finer than that.

THE VARIETY RED LINE (Law 6)
============================
The client's named failure is literally "one tree spammed a hundred times", and
this is the item that names it. **Transform randomisation is not variation.**
This ships **48 genuinely distinct source meshes** across **five growth forms**
that are different SHAPES and not re-parameterised clones:

    maiden     a single straight bole, high crown break, woodland-drawn
    open       short bole, 4-6 heavy low limbs, crown wider than tall
    hedgerow   asymmetric: the crown has been shaded off on the hedge side
    pollard    a bolling at 2.2-3.0 m carrying 5-9 upright poles of one age
    veteran    stag-headed, dbh x1.6, dead upper limbs, retrenched crown

crossed with age (0.25-1.0), lean (0-9 deg, free azimuth), 0-3 dead limbs and
ivy. The gate's realized-instance walk requires `distinct_sources >= 40` and
`distinct_shapes >= 40` with the commonest <= 25 %; 48 sources evenly drawn puts
the commonest at ~2 %.

    THE MANIFEST SAYS "3 LODs x 8/12/16 base meshes" = 36, WHICH IS BELOW THE
    GATE'S OWN FLOOR of 40 at 4,500 realized instances. This module therefore
    builds 24 L0 / 12 L1 / 12 L2 = 48, and inverts the manifest's ordering on
    purpose: **the near tier needs the most distinct forms, because the near
    tier is the only one where an eye can tell two trees apart.**
    `build_terrain`'s own comment makes the same argument ("8 per species x 11
    species = 88 hero trees, so no L0 mesh is used more than ~17 times").

NO EXTERNAL ASSETS (Law 8)
==========================
Zero image textures, zero downloaded meshes, zero scanned bark, zero AI. Every
vertex here comes out of numpy and every material out of `itemkit.NT`.
`K.assert_no_external_assets()` runs before anything is written.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
if _WORLD not in sys.path:
    sys.path.insert(0, _WORLD)

import itemkit as K                                            # noqa: E402
import world_contract as C                                     # noqa: E402

try:
    import bpy
    HAVE_BPY = True
except ImportError:                                            # pure-python
    bpy = None
    HAVE_BPY = False


ITEM = "tree_oak"
COLL = "W_Item_TreeOak"
PFX = "TOK_"
SRC_COLL = COLL + "/Sources"          # NOT matched by item_gate.CONTEXT_COLL_PAT
CAM_COLL = COLL + "/Cameras"          # IS matched -> skipped by the gate
STAND_COLL = COLL + "/Standins"       # IS matched -> skipped by the gate


# ===========================================================================
# 1.  FRAMING -- a stated range, and the one distance this is gated at
# ===========================================================================

LENS_MM = 35.0
HEIGHT_M = 17.0                       # manifest typical_height_m

#: The measured near end of this item's HOST cluster. A HOST BOUND (see the
#: module docstring): 93 hosts, all understorey, and every tree species in
#: screen_presence.json reports this identical figure.
NEAR_M = 4.577
#: The distance at which a 17.0 m tree exactly fills the 2160 px frame height on
#: a 35 mm lens at 4K. This is the STRONGEST claim `overfills_frame: true` plus a
#: clamped `peak_px_4k` of 2160.0 can support.
FULL_M = HEIGHT_M * (K.RES_X_4K * LENS_MM / K.SENSOR_MM) / K.RES_Y_4K

#: What the gate is run at, and what `--filmed-distance-m` is given.
GATE_AT_M = NEAR_M

PX_PER_M_NEAR = K.px_per_m(NEAR_M, LENS_MM)      # 815.7
PX_PER_M_FULL = K.px_per_m(FULL_M, LENS_MM)      # 127.1


# ===========================================================================
# 2.  THE RELIEF BUDGET.  Law 1, Law 2, Law 3, Law 5 -- in one table.
# ===========================================================================
#
# Each row is (name, layer, band, target modulation m, wavelength in metres).
# The AMPLITUDE is not in this table because an amplitude is not something this
# file is allowed to choose: `K.relief_amplitude_for(m, lam)` derives it from
# `world_contract.SUN_ELEV_DEG`, so if the sun moves every amplitude moves with
# it. `RELIEF_STAGES` is consumed by `relief_amp_mm()`, by `selftest()` and by
# the material builder; there is one table and no second copy.
#
# WHY EACH BAND. `K.RELIEF_BANDS` came off renders that were judged by eye:
# isotropic_micro 0.12-0.45 (weave, grain, cast skin), isotropic_macro 0.35-0.95
# (crumple, aggregate), sparse_crease 0.80-1.60, geometry_fold 0.60-1.40,
# hard_feature 1.50-6.00 (an arris, a lip, a joint -- an EDGE).
#
# Oak bark's furrows ARE edges. A mature Quercus robur bole carries 15-30 mm of
# furrow at a 60-90 mm plate pitch, which is `hard_feature` and nothing else --
# at 78 mm pitch, m = 5.40 is 18.6 mm peak-to-peak, dead in the middle of the
# published field range and INSIDE the band's 6.00 ceiling. It is stated at the
# top of the band deliberately: this is the one stage that casts its own shadow
# at a 12.5 deg sun, and that shadow is what a bole reads by.
#
# The two finest rows are SHADER stages. Everything at or above `plate_surface`
# is carried by displaced vertices, because a bark shader on a smooth cylinder
# cannot be bark at 300+ px (Law 7).
RELIEF_STAGES = (
    # name              layer       band              m      lam_m
    ("root_flare",      "geometry", "hard_feature",   2.40,  0.550),
    # RELIEF STAGES SUPERPOSE, AND THE FIRST DRAFT PRICED THEM AS IF THEY DID
    # NOT. Two fissure networks that both put a wall in the same place add their
    # TANGENTS, not their modulations: declared at m 4.60 and 5.40 the built
    # ring measured 52.9 deg = m 7.21, above hard_feature's 6.00 ceiling, in the
    # geometry layer where no material check could ever have seen it. Selftest
    # [7c] measures the built field's own 99.9th-percentile wall and converts it
    # back through the sun; these two numbers are set FROM that measurement, so
    # the pair COMBINES to the top of the band instead of each doing so alone.
    ("fissure_major",   "geometry", "hard_feature",   4.46,  0.165),
    ("fissure_network", "geometry", "hard_feature",   5.24,  0.078),
    ("cross_fracture",  "geometry", "hard_feature",   2.10,  0.026),
    ("plate_surface",   "geometry", "isotropic_macro", 0.72, 0.0090),
    ("branch_collar",   "geometry", "geometry_fold",  1.10,  0.140),
    ("bark_crust",      "shader",   "isotropic_micro", 0.38, 0.0026),
    ("bark_lichen",     "shader",   "isotropic_micro", 0.22, 0.0110),
    # THE LEAF'S V IS 60 mm WIDE, NOT 5 mm. The first draft declared the midrib
    # at lam = 5 mm -- the width of the rib CORD -- and then built the V across
    # the whole half-blade, so the geometry delivered m = 0.011 against a
    # declared 0.80, a factor of SEVENTY. A 22-vertex leaf cannot carry a 5 mm
    # cord; what it carries is the cup, and the cup's wavelength is the
    # half-blade. The 5 mm vein relief moved to the shader, where it belongs.
    ("leaf_cup",        "geometry", "geometry_fold",  0.95,  0.0600),
    ("leaf_vein",       "shader",   "isotropic_macro", 0.45, 0.0055),
    ("leaf_grain",      "shader",   "isotropic_micro", 0.30, 0.0018),
    ("deadwood_check",  "geometry", "hard_feature",   3.20,  0.045),
    ("ivy_leaf",        "shader",   "isotropic_micro", 0.26, 0.0035),
)

_STAGE = {r[0]: r for r in RELIEF_STAGES}


def relief_slope_deg(name):
    """The surface slope, in degrees, this stage's declared m asks for."""
    return K.slope_for_modulation(_STAGE[name][3])


def well_depth_m(name, transition_m):
    """Depth of a SMOOTHSTEP WELL that delivers this stage's declared slope.

    THIS FUNCTION IS THE GEOMETRY HALF OF "CHECK BOTH LAYERS", AND WRITING IT
    IS THE ONLY REASON THE BUILD IS NOT WRONG.

    `K.relief_amplitude_for` states a SINUSOID's peak-to-peak amplitude, because
    `m` is defined from a maximum surface slope and a sinusoid's maximum slope is
    `atan(pi A / lam)`. **A bark furrow is not a sinusoid.** It is a flat plate
    top, a wall, and a floor -- the whole point of oak bark is that most of the
    area is FLAT and the slope is concentrated in narrow walls. Applying a
    sinusoid's amplitude to a smoothstep profile is a slope error of whatever
    ratio the two happen to have, and the first draft of this file made exactly
    that mistake in the direction that renders CRUSTIER than declared: the
    furrow mask reached its full depth over a 13.6 mm shoulder, giving 45.6 deg
    walls and m = 6.46 against a declared 5.40 -- outside the band, in the
    layer nothing that reads materials could ever have seen.

    A smoothstep of height D over transition width W has max |dh/dx| = 1.5 D/W,
    so D = tan(theta) * W / 1.5. The conversion goes through the SLOPE, which is
    the quantity both profiles share and the quantity `m` is made of.

    `selftest [7]` measures the built ring's actual slope and converts it back,
    rather than asserting this algebra against itself -- see REFERENCE.md on
    R2-058, where a round-trip through one constant passed for three weeks while
    the constant was 3.183x wrong.
    """
    th = math.radians(relief_slope_deg(name))
    return math.tan(th) * float(transition_m) / 1.5


def ramp_rise_m(name, run_m):
    """Rise of a STRAIGHT RAMP that delivers this stage's declared slope.

    The third profile shape in this file, and the third time the sinusoid
    amplitude would have been the wrong number. A leaf's cupped cross-section is
    a V: the midrib is up, the margin is down, the surface between them is flat.
    Its slope is rise/run. A sinusoid of the same peak-to-peak over the same span
    has a maximum slope pi/2 times larger, so handing `relief_amplitude_for`'s
    answer to a V under-builds it -- MEASURED on the first draft of this file at
    m = 0.468 against a declared 0.95, i.e. half.

    Three profiles in this module (well, sinusoid, ramp), three conversions, one
    rule: the quantity that carries `m` is the SLOPE, and every shape converts
    through it. Nothing here takes an amplitude from one shape to another.
    """
    return math.tan(math.radians(relief_slope_deg(name))) * float(run_m)


def relief_amp_mm(name):
    """Peak-to-peak millimetres for a named stage. THE ONLY WAY TO GET ONE.

    Derived through `itemkit.relief_amplitude_for` from the stage's declared
    radiance modulation and its declared wavelength, at the contract sun. There
    is no path in this file that reaches an amplitude any other way.
    """
    _, _, _, m, lam = _STAGE[name]
    return K.relief_amplitude_for(m, wavelength_m=lam)


def relief_amp_m(name):
    return relief_amp_mm(name) * 1e-3


def relief_lam_m(name):
    return _STAGE[name][4]


def relief_budget(verbose=True):
    """The whole table through `itemkit.relief_budget`, band-checked BOTH ways.

    Too little relief is as wrong as too much: 0.79 rendered as a machined cone
    and was rejected exactly as 3.76 rendered as coarse stucco and was. Every
    row is checked against its own band and the verdict printed.
    """
    rows = []
    for name, layer, band, m, lam in RELIEF_STAGES:
        amp = relief_amp_mm(name)
        r = K.relief_budget([(name, lam, amp)], band=band, verbose=False)[0]
        r["layer"] = layer
        r["band"] = band
        r["m_target"] = m
        r["px_near"] = lam * PX_PER_M_NEAR
        r["px_full"] = lam * PX_PER_M_FULL
        rows.append(r)
        if verbose:
            K.log("relief %-16s %-8s %-16s lam %7.1f mm  amp %6.3f mm  "
                  "slope %5.2f deg  m %5.3f  %-4s  %6.1f px near / %5.2f px full"
                  % (name, layer, band, lam * 1000.0, amp, r["slope_deg"],
                     r["m"], r["verdict"], r["px_near"], r["px_full"]),
                  tag=ITEM)
    bad = [r for r in rows if r["verdict"] not in ("ok", "")]
    if bad:
        raise ValueError(
            "relief budget out of band: %s. A stage outside its band is not a "
            "style choice -- 0.79 was rejected as a machined cone and 3.76 as "
            "coarse stucco." % [(r["name"], r["verdict"], round(r["m"], 3))
                                for r in bad])
    return rows


# ===========================================================================
# 3.  GROWTH FORMS.  Five different SHAPES, not five parameter sets.
# ===========================================================================
#
# `distinct_shapes` exists in the gate because `spectator_seated` shipped 420
# source datablocks holding six actual poses. A tree library where every entry
# is the same topology with a different random seed is that failure with bark
# on. These five differ in the things a silhouette is made of: where the crown
# breaks, how many primary limbs there are, whether the leader survives, and
# whether the top of the tree is alive.

FORMS = {
    "maiden": dict(
        # Woodland-drawn: side shade kills the low limbs, the leader wins, the
        # crown is a narrow dome high up. Tall and clean.
        h=(15.0, 21.0), dbh_r=0.0146, break_f=(0.42, 0.55), n_prim=(3, 5),
        prim_ang=(24.0, 46.0), spread=0.52, leader=0.72, depth=6,
        crown_ratio=0.58, epicormic=0.10, retrench=0.0),
    "open": dict(
        # Open-grown: no side shade, so the low limbs live and the leader is
        # lost early. Crown wider than tall -- the classic parkland oak.
        h=(12.0, 17.0), dbh_r=0.0182, break_f=(0.16, 0.28), n_prim=(4, 6),
        prim_ang=(42.0, 66.0), spread=0.92, leader=0.20, depth=6,
        crown_ratio=0.82, epicormic=0.22, retrench=0.0),
    "hedgerow": dict(
        # Grown in a line: one flank shaded off, so the crown is thrown to the
        # open side and the shaded flank carries stubs instead of limbs.
        h=(11.5, 15.5), dbh_r=0.0170, break_f=(0.18, 0.32), n_prim=(3, 5),
        prim_ang=(38.0, 62.0), spread=0.78, leader=0.30, depth=6,
        crown_ratio=0.74, epicormic=0.30, retrench=0.0, asym=0.62),
    "pollard": dict(
        # Cut at head height on a rotation. A swollen bolling, then 5-9 poles of
        # ONE age rising together. The most different silhouette in the set.
        h=(9.5, 14.0), dbh_r=0.0230, break_f=(0.20, 0.26), n_prim=(5, 9),
        prim_ang=(6.0, 22.0), spread=0.46, leader=0.05, depth=5,
        crown_ratio=0.70, epicormic=0.45, retrench=0.0, bolling=True),
    "veteran": dict(
        # 300+ years: dbh x1.6 for the height, retrenched crown, stag-headed --
        # the upper primaries are dead and stand clear of the living crown. The
        # single best silhouette element in a treeline.
        h=(11.0, 16.0), dbh_r=0.0268, break_f=(0.14, 0.24), n_prim=(4, 7),
        prim_ang=(46.0, 74.0), spread=0.86, leader=0.10, depth=6,
        crown_ratio=0.66, epicormic=0.55, retrench=0.55),
}
FORM_ORDER = ("maiden", "open", "hedgerow", "pollard", "veteran")


#: Per-LOD build parameters.  The LOD ladder is a CROWN ladder: every tier keeps
#: the same bole bark mechanism, because the bole is what a near pass sees and a
#: near pass can land on any tree in the wood.  What drops is crown order count,
#: leaf count and mesh sampling.
LODS = {
    0: dict(n_src=24, orders=6, leaves=16000, arc_mm=9.0, ax_mm=15.0,
            bark_orders=2, twig_sides=5, bole_to=0.46),
    1: dict(n_src=12, orders=5, leaves=7000, arc_mm=17.0, ax_mm=30.0,
            bark_orders=1, twig_sides=4, bole_to=0.42),
    2: dict(n_src=12, orders=4, leaves=2600, arc_mm=34.0, ax_mm=62.0,
            bark_orders=1, twig_sides=3, bole_to=0.38),
}

#: How the 4,500 declared instances are drawn across the three tiers. Near trees
#: are rare and far trees are many, which is the opposite of the SOURCE counts
#: and is correct: source count buys variety where the eye can use it, instance
#: count follows the geometry of a wood.
LOD_MIX = (0.14, 0.34, 0.52)

DECLARED_INSTANCES = 4500

MAT_BARK, MAT_LEAF, MAT_DEAD, MAT_IVY = 0, 1, 2, 3
MAT_NAMES = (PFX + "bark", PFX + "leaf", PFX + "deadwood", PFX + "ivy")


# ===========================================================================
# 4.  NUMPY PLUMBING
# ===========================================================================

def _norm(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


class Accum(object):
    """Vertex / face accumulator. Quads and tris kept apart because
    `itemkit.new_mesh` emits quads first and then tris, and the material index
    array has to be laid out in that same order or every polygon gets the wrong
    material -- which is a defect that renders perfectly and is wrong."""

    def __init__(self):
        self.V = []
        self.Q = []
        self.T = []
        self.QM = []
        self.TM = []
        self.PID = []          # per-vertex random, constant within one leaf
        self.AGE = []          # 0 at the butt, 1 at a twig tip
        self.FIS = []          # fissure depth fraction, 0 plate top .. 1 furrow
        self.n = 0

    def add(self, verts, quads=None, tris=None, mat=0, pid=None, age=None,
            fis=None):
        v = np.ascontiguousarray(verts, np.float64).reshape(-1, 3)
        m = len(v)
        if m == 0:
            return
        self.V.append(v)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + self.n
            self.Q.append(q)
            self.QM.append(np.full(len(q), mat, np.int32))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + self.n
            self.T.append(t)
            self.TM.append(np.full(len(t), mat, np.int32))
        self.PID.append(np.full(m, 0.0) if pid is None
                        else np.broadcast_to(np.asarray(pid, np.float64),
                                             (m,)).copy())
        self.AGE.append(np.full(m, 0.0) if age is None
                        else np.broadcast_to(np.asarray(age, np.float64),
                                             (m,)).copy())
        self.FIS.append(np.full(m, 0.0) if fis is None
                        else np.broadcast_to(np.asarray(fis, np.float64),
                                             (m,)).copy())
        self.n += m

    def finish(self):
        if not self.V:
            return None
        V = np.concatenate(self.V)
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self.T) if self.T else np.zeros((0, 3), np.int64)
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32)
        att = {"tok_pid": np.concatenate(self.PID),
               "tok_age": np.concatenate(self.AGE),
               "tok_fis": np.concatenate(self.FIS)}
        return V, Q, T, np.concatenate([QM, TM]), att


def _frames(pts):
    """Parallel-transported (tangent, normal, binormal) per polyline point.

    A naive `cross(t, Z)` frame spins wildly wherever a limb passes through the
    vertical, and a spinning frame drags the bark texture round the branch --
    which reads as a barber's pole and is one of the classic tells. Rotation
    minimisation costs one loop over ~30 points per branch.
    """
    n = len(pts)
    T = np.zeros((n, 3))
    T[:-1] = pts[1:] - pts[:-1]
    T[-1] = T[-2] if n > 1 else np.array([0.0, 0.0, 1.0])
    T = _norm(T)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(T[0, 2])) > 0.95:
        ref = np.array([1.0, 0.0, 0.0])
    N = np.zeros((n, 3))
    N[0] = _norm(np.cross(T[0], ref).reshape(1, 3))[0]
    for i in range(1, n):
        v = N[i - 1] - T[i] * float(np.dot(N[i - 1], T[i]))
        ln = float(np.linalg.norm(v))
        if ln < 1e-9:
            v = np.cross(T[i], ref)
            ln = float(np.linalg.norm(v))
        N[i] = v / max(ln, 1e-12)
    B = np.cross(T, N)
    return T, N, B


def _cyl_noise(theta, u, lam, seed, oct=3, radius=1.0):
    """Value-noise on a CYLINDER, seamless round the circumference AND METRIC.

    TWO THINGS THAT ARE EASY TO GET WRONG HERE AND BOTH WERE.

    SEAM. A field addressed as (theta * r, u) is not periodic in theta, so it
    leaves a seam down the branch where the last column does not meet the first
    -- a vertical scar on every trunk in the wood. Sampling the 2-D noise on
    (cos theta, sin theta) makes the wrap exact by construction.

    SCALE. `radius` is NOT optional in practice, and leaving it out is a defect
    that hides inside a correct-looking picture: without it the field completes
    one cycle per TURN rather than per METRE, so on a 70 mm twig the same
    "0.34 m" wander runs 4.3x faster per millimetre of bark than it does on a
    300 mm bole. MEASURED, as the wall-slope calibration ratio against radius:

        R 0.30 m  1.49      R 0.12 m  2.01
        R 0.24 m  1.58      R 0.07 m  2.45
        R 0.18 m  1.82

    -- a 64 % drift with radius in a quantity that has to be one number, and it
    would have been absorbed silently into a median. Multiplying the circular
    coordinate by the radius makes the circumferential feature size metric, and
    costs nothing: cos and sin are periodic whatever they are multiplied by, so
    the seam stays closed.
    """
    k = 1.0 / max(float(lam), 1e-6)
    r = np.asarray(radius, float)
    a = np.cos(theta) * r * k
    b = np.sin(theta) * r * k
    z = np.asarray(u) * k
    return 0.5 * (K.fbm2(a, z, seed=seed, oct=oct)
                  + K.fbm2(b, z, seed=seed + 9137, oct=oct))


# ===========================================================================
# 5.  BARK.  The fissure network, as displaced geometry.
# ===========================================================================
#
# Quercus robur bark: flat-topped plates 40-90 mm across separated by deep
# longitudinal furrows that BRANCH AND REJOIN. That anastomosing habit is the
# whole look, and it is why this is not a stripe pattern: the furrows here are
# the level sets of a wandering phase field, and level sets of a noisy phase
# merge and split on their own. Cross-fractures cut the plates into 150-400 mm
# lengths.
#
# Depth is a function of MATURITY, not of taste. Bark on a 4 mm twig is smooth
# and olive; on a 0.25 m bole it is 20 mm deep. `maturity` below is driven by
# the local radius, so a limb fissures where it is thick and is smooth at its
# tip, which is what actually happens and is invisible if you fissure by order.

#: Fraction of a plate pitch occupied by one furrow WALL. 0.13 puts the furrow
#: (two walls plus a floor) at about 30 % of the pitch, which is what a mature
#: Quercus robur bole measures: 55 mm plates between 23 mm furrows at a 78 mm
#: pitch. It is a SHAPE parameter, not an amplitude -- the depth that goes with
#: it comes out of `well_depth_m`.
FURROW_WALL_FRAC = 0.13
CROSS_WALL_FRAC = 0.20


_WALL_CAL = None


def _wall_calibration(force=False):
    """How much steeper the WANDERING phase field's walls come out than the
    smoothstep algebra alone predicts. MEASURED, once, off the built field.

    This is a calibration and not a fudge, and the difference is that it is
    re-derived from the field every time this module is imported. Change
    `FURROW_WALL_FRAC`, the wander amplitude, the wander wavelength or the octave
    count and this number moves with them. Type a constant here instead and the
    next person who touches the wander ships walls at the wrong slope with every
    check still passing -- which is the shape of most of this project's defect
    log.

    Measured at three radii spanning the bole and the primary limbs, with the
    correction switched OFF, at the 99.9th percentile of |d(disp)/d(arc)|: the
    steepest wall, which is the one that decides whether the stage sits inside
    `hard_feature` or above it.

    WHAT WAS TRIED FIRST AND DID NOT WORK, because it is worth knowing: dividing
    the phase distance by the local |grad phase| to convert it to metres. It
    left 42 % of the error, because dividing by a field that is itself varying
    contributes its own gradient -- the second term of the quotient rule -- and
    at these wander amplitudes that term is the same size as the correction.
    """
    global _WALL_CAL
    if _WALL_CAL is not None and not force:
        return _WALL_CAL
    _WALL_CAL = 1.0                      # so the probe runs UNCORRECTED
    ratios = []
    want = math.tan(math.radians(relief_slope_deg("fissure_network")))
    for R0, sd in ((0.30, 101), (0.24, 202), (0.18, 303), (0.12, 404),
                   (0.07, 505)):
        n = 16384
        th = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        uu = np.full(n, 2.0)
        d, _ = _bark_relief(th, uu, np.full(n, R0), sd, np.full(n, 0.2),
                            np.full(n, 1.0), only="fissure_network")
        ds = R0 * (2.0 * math.pi / n)
        g = np.abs(np.diff(d)) / ds
        ratios.append(float(np.quantile(g, 0.999)) / want)
    _WALL_CAL = float(np.median(ratios))
    return _WALL_CAL


def bark_relief(theta, u, radius, seed, age01, maturity, only=None,
                sinusoid_bug=False):
    """(radial displacement in metres, furrow-depth fraction 0..1).

    `only` restricts the field to one named stage, so `selftest [7]` can measure
    a single stage against its own declared slope instead of measuring the sum
    of four and hoping. `sinusoid_bug` rebuilds it the WRONG way -- with
    `relief_amplitude_for`'s sinusoid amplitude applied to the smoothstep
    profile -- and exists only so the check can be shown to reject something
    known to be bad.
    """
    return _bark_relief(theta, u, radius, seed, age01, maturity, only,
                        sinusoid_bug)


def _bark_relief(theta, u, radius, seed, age01, maturity, only=None,
                 sinusoid_bug=False):
    """Radial displacement in METRES, plus the furrow-depth fraction 0..1.

    Both are returned because the shader needs to know where the furrows are in
    order to darken them, and re-deriving that in the shader from a DIFFERENT
    noise would put the paint somewhere other than the shape. That decoupling is
    exactly what `relief_reads_as_lip_and_shade` exists to catch: a surface whose
    marks have no sunward lip and no lee shadow is behaving like a printed decal
    and not like a physical object.

    TWO FISSURE SCALES, NESTED. A single pitch gives a corduroy. Oak carries a
    major network at 140-200 mm that divides the bole into broad tracts, and a
    finer one at 60-90 mm inside each tract; where the two coincide the furrow
    is at its deepest, which is the depth variation that stops the pattern
    reading as a machined knurl.
    """
    lam_maj = relief_lam_m("fissure_major")
    lam_fis = relief_lam_m("fissure_network")
    lam_crs = relief_lam_m("cross_fracture")
    A_srf = relief_amp_m("plate_surface")

    circ = 2.0 * math.pi * np.maximum(radius, 1e-4)
    r_mean = float(np.mean(radius))
    circ_m = 2.0 * math.pi * max(r_mean, 1e-4)

    disp = np.zeros(np.broadcast(theta, u, radius).shape)
    depth = np.zeros_like(disp)

    for stage, lam, wall_frac, wander_lam, wander_amp in (
            ("fissure_major", lam_maj, FURROW_WALL_FRAC, 0.62, 1.05),
            ("fissure_network", lam_fis, FURROW_WALL_FRAC, 0.34, 1.35)):
        if only is not None and stage != only:
            continue
        # An INTEGER number of plates round the circumference, so the phase is
        # exactly periodic in theta and there is no seam down the trunk.
        nplate = np.maximum(np.round(circ / lam), 3.0)
        pitch = circ_m / max(float(np.round(circ_m / lam)), 3.0)
        w = wall_frac * pitch                        # transition width, metres
        # DERIVED THROUGH THE SLOPE, never typed. `sinusoid_bug` is the wrong
        # conversion, kept callable so the check can be shown to reject it.
        D = (relief_amp_m(stage) * 0.5) if sinusoid_bug \
            else well_depth_m(stage, w)

        def _phase(th_, u_):
            wd = _cyl_noise(th_, u_, wander_lam, seed + 17, oct=3,
                            radius=radius) - 0.5
            return th_ / (2.0 * math.pi) * nplate + wander_amp * wd

        phase = _phase(theta, u)
        s = phase - np.floor(phase)
        d = np.abs(s - 0.5)
        # the wall runs from the furrow floor outward over `wall_frac` of a
        # pitch; everything beyond it is flat plate top, which is most of the
        # area and is the whole reason this is not a sinusoid
        furrow = 1.0 - K.smoothstep(0.02, 0.02 + wall_frac, d)
        # THE WANDER IS WHAT MAKES THE FURROWS ANASTOMOSE, AND IT ALSO MAKES THE
        # WALLS STEEPER THAN THE SMOOTHSTEP ALGEBRA PREDICTS. `wall_frac` is a
        # fraction of a PITCH, but the phase runs faster than nplate/circ
        # wherever the wander's own gradient adds to it, so the same fraction of
        # a pitch is compressed into less arclength and the wall stands up.
        # MEASURED on the built ring at 36.16 deg against a declared 24.15 --
        # 49.7 % out, in the geometry layer, where nothing that reads materials
        # could ever have seen it. The same shape as the human figures' fold
        # field, which was still at m = 2.32 after the fabric shader had been
        # corrected to 0.28.
        #
        # The correction is MEASURED, not modelled: `_wall_calibration()` builds
        # this field, differentiates it and reports the ratio. An analytic
        # normalisation by the local |grad phase| was tried first and left 42 %
        # -- dividing by a field that is itself varying contributes its own
        # gradient, which is the second term of the quotient rule and is the
        # same size as the thing being corrected.
        disp = disp - (D / _wall_calibration()) * furrow
        depth = np.maximum(depth, furrow)

    # cross-fractures: the same construction along u, sparse. They cut the
    # plates into 150-400 mm lengths, which is the other half of the network.
    if only in (None, "cross_fracture"):
      w2 = _cyl_noise(theta, u, 0.21, seed + 613, oct=2,
                       radius=radius) - 0.5
      cross_pitch = 0.24
      p2 = u / cross_pitch + 1.1 * w2
      s2 = p2 - np.floor(p2)
      Dc = well_depth_m("cross_fracture", CROSS_WALL_FRAC * cross_pitch)
      cross = 1.0 - K.smoothstep(0.03, 0.03 + CROSS_WALL_FRAC,
                                 np.abs(s2 - 0.5))
      cross = cross * K.smoothstep(0.42, 0.72,
                                   _cyl_noise(theta, u, 0.55, seed + 71, oct=2,
                                              radius=radius))
      disp = disp - Dc * cross
      depth = np.maximum(depth, 0.75 * cross)

    # within-plate crustose relief. Quasi-sinusoidal, so THIS one takes the
    # sinusoid amplitude straight from `relief_amplitude_for`. It is also the
    # octave that keeps the fine/coarse spectral balance from collapsing onto
    # the fissures alone -- a surface with all its energy at one scale is the
    # wave-1 signature, stated as a ratio.
    if only in (None, "plate_surface"):
        lam_srf = relief_lam_m("plate_surface")
        surf = (_cyl_noise(theta, u, lam_srf * 2.6, seed + 233, oct=4,
                           radius=radius) - 0.5) * 2.0
        disp = disp + (A_srf * 0.5) * surf

    return disp * maturity, np.clip(depth * maturity, 0.0, 1.0)


def _root_flare(theta, z, r0, seed):
    """Buttress lobes at the butt. Dies out over the first ~1.2 m.

    A COSINE, not a shaped power. `relief_amplitude_for` states the peak-to-peak
    amplitude of a SINUSOID, so the profile this drives has to be one or the
    slope it delivers is not the slope that was asked for -- the same error
    `well_depth_m` exists to correct one scale down.
    """
    A = relief_amp_m("root_flare")
    lam = relief_lam_m("root_flare")
    nlobe = max(3.0, round(2.0 * math.pi * r0 / lam))
    ph = theta / (2.0 * math.pi) * nlobe \
        + 0.7 * (_cyl_noise(theta, z * 0.0, 0.8, seed + 401, oct=2,
                            radius=r0) - 0.5)
    lobe = 0.5 * (1.0 + np.cos(2.0 * math.pi * ph))
    fall = np.exp(-np.maximum(z, 0.0) / 0.62)
    return A * lobe * fall


def tube(acc, pts, rad, sides, mat, seed, age0, age1, bark=False,
         cap_top=False, collar=0.0):
    """One branch as a swept tube. Vectorised; bark applied as displacement.

    `bark=True` runs the fissure field, which is the item. `bark=False` is a
    smooth tapered tube for orders whose radius is below the maturity threshold
    anyway, and it costs the same vertices minus one noise evaluation.
    """
    n = len(pts)
    if n < 2 or sides < 3:
        return
    T, N, B = _frames(pts)
    arc = np.zeros(n)
    arc[1:] = np.cumsum(np.linalg.norm(pts[1:] - pts[:-1], axis=1))
    th = np.linspace(0.0, 2.0 * math.pi, int(sides), endpoint=False)

    TH = np.broadcast_to(th[None, :], (n, sides))
    U = np.broadcast_to(arc[:, None], (n, sides))
    R = np.broadcast_to(np.asarray(rad, float)[:, None], (n, sides)).copy()
    AGE = np.broadcast_to(np.linspace(age0, age1, n)[:, None], (n, sides))

    fis = np.zeros((n, sides))
    if bark:
        # maturity: smooth young bark under ~35 mm radius, fully fissured over
        # ~110 mm. Driven by the LOCAL radius, so one limb fissures at its base
        # and is smooth at its tip.
        mat_f = K.smoothstep(0.035, 0.110, R)
        disp, fis = bark_relief(TH, U, R, seed, AGE, mat_f)
        R = R + disp
        if collar > 0.0:
            # the swollen collar where a limb leaves its parent
            A = relief_amp_m("branch_collar")
            R = R + (A * 0.5) * collar * np.exp(-U / 0.26) \
                * (0.7 + 0.3 * np.cos(3.0 * TH))
        if pts[0][2] < 1.6:
            R = R + _root_flare(TH, np.maximum(pts[:, 2][:, None], 0.0), rad[0],
                                seed)
        R = np.maximum(R, 0.0006)

    V = (pts[:, None, :]
         + R[:, :, None] * (np.cos(TH)[:, :, None] * N[:, None, :]
                            + np.sin(TH)[:, :, None] * B[:, None, :]))

    idx = np.arange(n * sides).reshape(n, sides)
    nxt = np.roll(idx, -1, axis=1)
    q = np.stack([idx[:-1, :].ravel(), nxt[:-1, :].ravel(),
                  nxt[1:, :].ravel(), idx[1:, :].ravel()], axis=1)
    acc.add(V.reshape(-1, 3), quads=q, mat=mat,
            age=AGE.ravel(), fis=fis.ravel())

    if cap_top:
        # a broken limb end is a real face, and on a snag it is the feature
        base = acc.n - sides
        ring = np.arange(sides) + base
        ctr = V[-1].mean(axis=0)
        acc.add(ctr.reshape(1, 3), mat=mat, age=age1)
        c = acc.n - 1
        t = np.stack([ring, np.roll(ring, -1), np.full(sides, c)], axis=1)
        acc.T.append(t)
        acc.TM.append(np.full(sides, mat, np.int32))


# ===========================================================================
# 6.  THE LEAF.  A lobed blade with a real midrib fold.
# ===========================================================================
#
# WHY THE FOLD IS GEOMETRY. `relief_reads_as_lip_and_shade` renders the frame on
# BOTH candidate sun sides and keeps only the half of the fine band that MOVED
# when the light moved. A flat card with a painted vein pattern scores x0.02 on
# that clause -- measured, on four painted decoys including a high-contrast one.
# A leaf that is a dihedral about its midrib scores as relief because it IS
# relief. It also costs nothing: the fold is a z offset on vertices that had to
# exist anyway.
#
# Quercus robur: obovate, 8-12 cm, 3-6 pairs of ROUNDED lobes, sinuses cut about
# a third of the way to the midrib, base auriculate (two small backward ears),
# petiole almost absent -- which is the field character that separates it from
# sessile oak and is worth 2 vertices.

#: Mean blade length leaves are stamped at, in metres. Quercus robur runs
#: 80-120 mm; this is at the top of that and deliberately so -- 16,000 leaves is
#: a tenth of a real oak's count and LEAF AREA is what a crown reads by, so the
#: shortfall is taken in size rather than pretended away. Stated here, once,
#: because `leaf_cup`'s declared wavelength is a fraction of it.
LEAF_BLADE_M = 0.115


def leaf_template(a=4, b=9):
    """(verts, tris) for one leaf in local frame, blade length 1.0.

    x runs petiole -> tip, y across, z out of plane.

    THE MARGIN IS SAMPLED AT TWICE THE MIDRIB'S RATE, and that is the whole
    trick. `a` midrib points carry the fold; `b = 2(a-1)+1` margin points per
    side carry the LOBES. Quercus robur has 3-6 pairs of rounded lobes with the
    sinuses cut about a third of the way to the midrib, and it is the single
    field character that says oak rather than "a leaf". Sampling both lines at
    the same rate would need `b` midrib points to get `b` lobes and would cost
    twice the vertices for a fold that does not need them.

    a=4, b=9 -> 22 verts, 22 tris. At 16,000 leaves that is 352 k verts and
    352 k tris per hero tree, which is where more than half the crown's budget
    goes and is the right place for it.
    """
    tm = np.linspace(0.0, 1.0, a)              # midrib stations
    ts = np.linspace(0.0, 1.0, b)              # margin stations

    def env(t):
        # obovate: widest about 0.62 of the way to the tip, base narrowed to a
        # very short petiole, tip rounded rather than acuminate
        return 0.46 * np.sin(np.pi * np.clip((t + 0.13) / 1.16, 0, 1)) ** 0.70

    w = env(ts)
    # lobe / sinus alternation ON THE SAMPLE INDEX, so it cannot alias: odd
    # stations bulge out to a lobe, even ones cut in to a sinus
    alt = np.where(np.arange(b) % 2 == 1, 1.30, 0.74)
    w = w * alt
    w[0] = 0.11                                 # the auricles at the base
    w[-1] = 0.05                                # rounded tip

    # the blade is CUPPED: the midrib line lifts and the margins fall away, so
    # the section is a shallow V across the HALF-BLADE. That V is the dihedral
    # the two-light clause reads. Its rise is DERIVED through `ramp_rise_m`
    # from `leaf_cup`'s declared slope over the ACTUAL run -- the median lit
    # half-width of this template -- and not from a sinusoid amplitude.
    blade_m = LEAF_BLADE_M                      # the size leaves are stamped at
    run_m = float(np.median(w[np.abs(w) > 0.12])) * blade_m
    rib = float(np.clip(ramp_rise_m("leaf_cup", run_m) / blade_m, 0.0, 0.20))

    def droop(t):
        return -0.17 * t ** 2 + 0.04 * np.sin(math.pi * t)

    V = [(float(tm[i]), 0.0, float(droop(tm[i])) + rib) for i in range(a)]
    for sgn in (1.0, -1.0):
        for k in range(b):
            V.append((float(ts[k]), sgn * float(w[k]),
                      float(droop(ts[k])) - 0.35 * float(w[k]) * rib / 0.05
                      if rib > 0 else float(droop(ts[k]))))
    V = np.array(V, float)
    # margins sit BELOW the midrib by the full rib height, which is what makes
    # the section a V rather than a flat card with a raised line on it
    V[a:, 2] = np.interp(V[a:, 0], tm, V[:a, 2]) - rib

    tris = []
    for sgn_i, off in enumerate((a, a + b)):
        for k in range(b - 1):
            i0 = min(k // 2, a - 1)
            i1 = min((k + 1) // 2 + (1 if (k + 1) % 2 == 0 else 0), a - 1)
            i1 = min(max(i1, i0), a - 1)
            m0, m1 = off + k, off + k + 1
            if sgn_i == 0:
                tris.append((i0, m0, m1))
            else:
                tris.append((i0, m1, m0))
            if i1 != i0:
                if sgn_i == 0:
                    tris.append((i0, m1, i1))
                else:
                    tris.append((i0, i1, m1))
    return V, np.array(tris, np.int64)


_LEAF_V, _LEAF_T = leaf_template()


def place_leaves(acc, pos, fwd, side, up, size, pid, mat=MAT_LEAF):
    """Stamp the leaf template on N frames at once. One numpy expression."""
    n = len(pos)
    if n == 0:
        return
    tpl = _LEAF_V
    sz = np.asarray(size, float)[:, None, None]
    V = (pos[:, None, :]
         + (tpl[None, :, 0:1] * fwd[:, None, :]
            + tpl[None, :, 1:2] * side[:, None, :]
            + tpl[None, :, 2:3] * up[:, None, :]) * sz).reshape(-1, 3)
    T = (_LEAF_T[None, :, :]
         + (np.arange(n) * len(tpl))[:, None, None]).reshape(-1, 3)
    P = np.repeat(np.asarray(pid, float), len(tpl))
    acc.add(V, tris=T, mat=mat, pid=P, age=np.ones(len(V)))


# ===========================================================================
# 7.  THE SKELETON
# ===========================================================================

class Tree(object):
    """One oak. Deterministic in `seed`; nothing here reads a global."""

    def __init__(self, seed, form, lod, age=None, lean_deg=None, lean_az=None,
                 n_dead=None, ivy=None):
        self.seed = int(seed)
        self.form = form
        self.lod = int(lod)
        self.rng = K.Rng(seed, 0x0A4B)
        f = FORMS[form]
        self.f = f
        L = LODS[lod]
        self.L = L

        self.age = self.rng.u(0.25, 1.0) if age is None else float(age)
        # height: old trees are tall, but a veteran RETRENCHES -- it gets shorter
        h0, h1 = f["h"]
        self.h = h0 + (h1 - h0) * (0.30 + 0.70 * self.age)
        self.h *= (1.0 - 0.16 * f["retrench"])
        self.r0 = self.h * f["dbh_r"] * (0.62 + 0.55 * self.age)
        self.lean = math.radians(self.rng.u(0.0, 9.0)
                                 if lean_deg is None else float(lean_deg))
        self.lean_az = (self.rng.u(0.0, 2.0 * math.pi)
                        if lean_az is None else float(lean_az))
        self.n_dead = (self.rng.i(0, 3) if n_dead is None else int(n_dead))
        if f["retrench"] > 0.0:
            self.n_dead = max(self.n_dead, 2)
        self.ivy = (self.rng.u() < 0.28 if ivy is None else bool(ivy))
        self.asym_az = self.rng.u(0.0, 2.0 * math.pi)

        self.branches = []          # (pts, rad, order, dead, collar)
        self.tips = []              # (pts, rad) of terminal orders, for leaves

    # -- geometry -----------------------------------------------------------
    def _child_radii(self, r_at, weights):
        """The pipe model. r_parent^k = sum r_child^k, k = 2.49 (da Vinci was
        2.0; measured broadleaf exponents run 2.3-2.7). Using it instead of a
        fixed fraction is why a twig springing from the thin end of a limb does
        not come out thicker than the limb -- the defect that made
        `build_terrain`'s first pass 'look like a coral instead of a tree'."""
        k = 2.49
        w = np.asarray(weights, float)
        w = w / max(w.sum(), 1e-9)
        return r_at * w ** (1.0 / k)

    def _limb(self, p0, d0, length, r_base, order, dead, collar):
        rng = self.rng
        f = self.f
        dmax = self.L["orders"] - 1
        nseg = max(2, int(round(np.interp(order, [0, 2, 5], [11, 6, 3]))))
        if self.lod:
            nseg = max(2, nseg - self.lod)
        # gravitropism: an oak limb sweeps DOWN out of the bole and then
        # recovers upward, which is the sinuous knuckled line that says oak.
        # A single sign gives a banana; two signs give a limb.
        g_out = np.interp(order, [0, 1, 2, 5], [0.06, -0.22, -0.10, 0.10])
        g_up = np.interp(order, [0, 1, 2, 5], [0.10, 0.34, 0.30, 0.22])
        curl = 0.30 + 0.28 * order / max(1, dmax)

        pts = [np.array(p0, float)]
        rr = [float(r_base)]
        d = np.array(d0, float)
        step = length / nseg
        for i in range(nseg):
            t = (i + 0.5) / nseg
            d = d + np.array([0.0, 0.0, 1.0]) * ((g_out * (1.0 - t)
                                                  + g_up * t) / nseg)
            d = d + (rng.arr(3) - 0.5) * (curl * 1.7 / nseg)
            d = d / max(np.linalg.norm(d), 1e-9)
            pts.append(pts[-1] + d * step)
            rr.append(float(r_base) * (1.0 - 0.62 * (i + 1) / nseg) ** 0.55)
        pts = np.array(pts)
        rr = np.array(rr)
        if order == 0:
            rr[0] *= 1.34
            rr[1] *= 1.11
        self.branches.append((pts, rr, order, dead, collar))
        if order >= dmax - 1 and not dead:
            self.tips.append((pts, rr))
        return pts, rr, d

    def grow(self):
        rng = self.rng
        f = self.f
        dmax = self.L["orders"] - 1
        lean_v = np.array([math.cos(self.lean_az) * math.sin(self.lean),
                           math.sin(self.lean_az) * math.sin(self.lean),
                           math.cos(self.lean)])

        break_f = rng.u(*f["break_f"])
        bole_len = self.h * break_f
        p0 = np.array([0.0, 0.0, -self.r0 * 1.8 - 0.10])   # bole starts sub-grade
        pts, rr, d = self._limb(p0, lean_v, bole_len, self.r0, 0, False, 0.0)

        if f.get("bolling"):
            # a pollard's bolling: a short swollen head, then poles of one age
            self._poles(pts, rr, d)
        else:
            self._crown(pts, rr, d, break_f)
        if self.ivy:
            self._ivy(np.array(self.branches[0][0]), np.array(self.branches[0][1]))
        return self

    def _poles(self, pts, rr, d):
        rng = self.rng
        f = self.f
        n = rng.i(*f["n_prim"])
        r_at = float(rr[-1]) * 1.18
        w = 0.7 + 0.6 * rng.arr(n)
        rads = self._child_radii(r_at, w)
        base = pts[-1]
        for i in range(n):
            a = 2.0 * math.pi * (i + 0.4 * rng.u()) / n
            lat = np.array([math.cos(a), math.sin(a), 0.0])
            ang = math.radians(rng.u(*f["prim_ang"]))
            cd = _norm((d * math.cos(ang) + lat * math.sin(ang)).reshape(1, 3))[0]
            ln = self.h * (1.0 - 0.20) * rng.u(0.72, 1.06) * f["crown_ratio"]
            self._branch(base + lat * float(rr[-1]) * 0.7, cd, ln, float(rads[i]),
                         1, False, 1.0)

    def _crown(self, pts, rr, d, break_f):
        rng = self.rng
        f = self.f
        n = rng.i(*f["n_prim"])
        # the leader: on a maiden it survives and carries the crown; on an open
        # oak it is lost and the limbs take over. That single switch is most of
        # the difference between the two silhouettes.
        keep_leader = rng.u() < f["leader"]
        dead_idx = set()
        if self.n_dead:
            for _ in range(self.n_dead):
                dead_idx.add(rng.i(0, n - 1 + (1 if keep_leader else 0)))
        w = 0.6 + 0.8 * rng.arr(n + (1 if keep_leader else 0))
        if keep_leader:
            w[-1] *= 2.1
        r_at = float(rr[-1])
        rads = self._child_radii(r_at * 1.06, w)

        for i in range(n):
            # attach along the top third of the bole, not all at one node
            fpos = 0.62 + 0.36 * ((i + 0.5 + 0.5 * (rng.u() - 0.5)) / n)
            j = int(np.clip(fpos * (len(pts) - 1), 0, len(pts) - 1))
            a = 2.0 * math.pi * (i + 0.35 * rng.u()) / n
            if f.get("asym"):
                # hedgerow: the crown is thrown to the open side
                a = self.asym_az + (a - math.pi) * (1.0 - f["asym"]) \
                    + f["asym"] * math.sin(a) * 1.1
            lat = np.array([math.cos(a), math.sin(a), 0.0])
            ang = math.radians(rng.u(*f["prim_ang"]))
            cd = _norm((d * math.cos(ang) + lat * math.sin(ang)).reshape(1, 3))[0]
            ln = self.h * f["crown_ratio"] * f["spread"] * rng.u(0.70, 1.14)
            self._branch(pts[j] + lat * float(rr[j]) * 0.8, cd, ln,
                         float(rads[i]), 1, i in dead_idx, 1.0)
        if keep_leader:
            ln = self.h * f["crown_ratio"] * 0.9
            self._branch(pts[-1], d, ln, float(rads[-1]), 1,
                         (n in dead_idx), 0.4)

        # epicormic shoots: an old or stressed oak sprouts short twiggy growth
        # straight out of the bole, and it is the detail that reads as AGE
        ne = int(round(f["epicormic"] * 26 * self.age))
        for _ in range(ne):
            j = int(np.clip(rng.u(0.10, 0.92) * (len(pts) - 1), 0, len(pts) - 1))
            a = rng.u(0.0, 2.0 * math.pi)
            lat = np.array([math.cos(a), math.sin(a), 0.0])
            cd = _norm((lat * 0.72 + np.array([0.0, 0.0, 0.70])).reshape(1, 3))[0]
            self._branch(pts[j] + lat * float(rr[j]) * 0.9, cd,
                         rng.u(0.35, 1.30), float(rr[j]) * rng.u(0.030, 0.062),
                         max(2, self.L["orders"] - 3), False, 0.5)

    def _branch(self, p, d, length, r, order, dead, collar):
        rng = self.rng
        dmax = self.L["orders"] - 1
        pts, rr, dd = self._limb(p, d, length, r, order, dead, collar)
        if order >= dmax:
            return
        # a dead limb keeps branching for one more order and then stops: a snag
        # is a skeleton, not a stump
        if dead and order >= 2:
            return
        nch = int(np.interp(order, [0, 1, 2, 3, 5], [4, 4, 4, 5, 5]))
        if self.lod >= 1 and order >= dmax - 1:
            nch = max(2, nch - 1)
        w = 0.55 + 0.9 * rng.arr(nch)
        rads = self._child_radii(float(rr[-1]) * 1.10, w)
        roll = rng.u(0.0, 2.0 * math.pi)
        for c in range(nch):
            fpos = 0.20 + 0.78 * ((c + 0.5 + 0.55 * (rng.u() - 0.5)) / nch)
            j = int(np.clip(fpos * (len(pts) - 1), 0, len(pts) - 1))
            pdir = (pts[min(j + 1, len(pts) - 1)] - pts[j])
            if np.linalg.norm(pdir) < 1e-9:
                pdir = dd
            pdir = pdir / max(np.linalg.norm(pdir), 1e-9)
            # 137.5 deg -- oak phyllotaxy is spiral, and using the golden angle
            # is what stops four children stacking into a cross
            roll += math.radians(137.508) + rng.n(0.0, 0.28)
            ref = np.array([0.0, 0.0, 1.0])
            if abs(float(pdir[2])) > 0.94:
                ref = np.array([1.0, 0.0, 0.0])
            e1 = _norm(np.cross(pdir, ref).reshape(1, 3))[0]
            e2 = np.cross(pdir, e1)
            lat = math.cos(roll) * e1 + math.sin(roll) * e2
            ang = math.radians(rng.u(*(
                (30.0, 58.0) if order >= 2 else self.f["prim_ang"])))
            cd = _norm((pdir * math.cos(ang) + lat * math.sin(ang)).reshape(1, 3))[0]
            ln = length * np.interp(order, [0, 1, 3, 5], [0.62, 0.60, 0.58, 0.54]) \
                * rng.u(0.70, 1.18) * (1.0 - 0.30 * fpos)
            self._branch(pts[j] + lat * float(rr[j]) * 0.85, cd, ln,
                         float(rads[c]), order + 1, dead, 0.55)

    def _ivy(self, pts, rr):
        """Ivy on the bole: a few sinuous stems plus a leaf skirt. One of the
        manifest's own variation axes, and the reason a treeline stops reading
        as a species list -- half the veterans in a real hedgerow are furred."""
        rng = self.rng
        n = rng.i(3, 7)
        arc = np.zeros(len(pts))
        arc[1:] = np.cumsum(np.linalg.norm(pts[1:] - pts[:-1], axis=1))
        top = arc[-1] * rng.u(0.55, 0.95)
        T, N, B = _frames(pts)
        for _ in range(n):
            a0 = rng.u(0.0, 2.0 * math.pi)
            m = 26
            s = np.linspace(0.0, top, m)
            a = a0 + s * rng.u(0.9, 2.2) + 0.5 * K.fbm1(s * 4.0, seed=rng.i(0, 9999))
            j = np.clip(np.searchsorted(arc, s), 0, len(pts) - 1)
            r = rr[j] * 1.03 + 0.010
            P = pts[j] + r[:, None] * (np.cos(a)[:, None] * N[j]
                                       + np.sin(a)[:, None] * B[j])
            self.branches.append((P, np.full(m, 0.009), 9, False, 0.0))
            # leaves along the stem
            k = 90 if self.lod == 0 else (34 if self.lod == 1 else 12)
            t = rng.arr(k) * (m - 1)
            i0 = t.astype(int)
            base = P[i0]
            out = _norm(base - pts[j][i0])
            up = np.tile(np.array([0.0, 0.0, 1.0]), (k, 1))
            fwd = _norm(out * 0.8 + up * 0.5 + (rng.arr(k * 3).reshape(k, 3) - 0.5))
            side = _norm(np.cross(fwd, up + 0.01))
            u2 = np.cross(fwd, side)
            self._pending_ivy = getattr(self, "_pending_ivy", [])
            self._pending_ivy.append((base, fwd, side, u2,
                                      rng.arr(k) * 0.030 + 0.055, rng.arr(k)))

    # -- meshing ------------------------------------------------------------
    def mesh(self):
        L = self.L
        acc = Accum()
        arc_m = L["arc_mm"] * 1e-3
        ax_m = L["ax_mm"] * 1e-3
        bark_orders = L["bark_orders"]
        dmax = L["orders"] - 1

        for pts, rr, order, dead, collar in self.branches:
            rmean = float(np.mean(rr))
            if order == 9:                       # ivy stem
                sides = 4
                bark = False
            else:
                bark = order <= bark_orders
                if bark:
                    sides = int(np.clip(round(2.0 * math.pi * rr[0] / arc_m),
                                        8, 384))
                else:
                    sides = int(np.clip(round(2.0 * math.pi * rmean
                                              / (arc_m * 2.6)),
                                        L["twig_sides"], 24))
            # resample the polyline so the axial pitch matches the design
            if bark:
                target = ax_m
            else:
                target = max(ax_m * 3.2, rmean * 2.4)
            pts2, rr2 = _resample(pts, rr, target)
            mat = MAT_DEAD if dead else (MAT_IVY if order == 9 else MAT_BARK)
            a0 = min(1.0, order / max(1.0, dmax))
            a1 = min(1.0, (order + 1) / max(1.0, dmax))
            tube(acc, pts2, rr2, sides, mat, self.seed + order * 977,
                 a0, a1, bark=bark, cap_top=(dead and order >= 2),
                 collar=collar)

        self._leaves(acc)
        for rec in getattr(self, "_pending_ivy", []):
            place_leaves(acc, rec[0], rec[1], rec[2], rec[3], rec[4], rec[5],
                         mat=MAT_IVY)
        return acc.finish()

    def _leaves(self, acc):
        """Leaves on VIRTUAL SHOOTS off the terminal twigs.

        The recursion stops at 4-6 orders, so pinning every leaf within a
        millimetre of a modelled twig gives a correct leaf-area index arranged
        as ropes -- `build_terrain` records exactly that failure ('the tree read
        as a bare skeleton with green string on it'). A real oak has one more
        order, the season's unlignified shoots, and they carry the leaves out
        into the crown volume. Modelling them as geometry costs another 5x of
        branches; riding the leaves along them costs nothing.
        """
        if not self.tips:
            return
        rng = self.rng
        target = int(self.L["leaves"] * (0.72 + 0.55 * self.age))
        segs = []
        for pts, rr in self.tips:
            for i in range(len(pts) - 1):
                segs.append((pts[i], pts[i + 1] - pts[i], float(rr[i])))
        if not segs:
            return
        ns = len(segs)
        per = max(1, int(round(target / ns)))
        P0 = np.array([s[0] for s in segs])
        D = np.array([s[1] for s in segs])
        RD = np.array([s[2] for s in segs])
        slen = np.linalg.norm(D, axis=1)
        Dn = _norm(D)

        k = per * ns
        idx = np.repeat(np.arange(ns), per)
        t = rng.arr(k)[:, None]
        base = P0[idx] + D[idx] * t
        pdir = Dn[idx]
        ref = np.tile(np.array([0.0, 0.0, 1.0]), (k, 1))
        flip = np.abs(pdir[:, 2]) > 0.94
        ref[flip] = np.array([1.0, 0.0, 0.0])
        e1 = _norm(np.cross(pdir, ref))
        e2 = np.cross(pdir, e1)
        roll = rng.arr(k) * 2.0 * math.pi
        lat = np.cos(roll)[:, None] * e1 + np.sin(roll)[:, None] * e2

        # the shoot: a few directions per segment, several leaves strung along
        # each, so the foliage is TUFTED. Evenly-spread leaves read as a
        # spherical fog and that is the other classic tell.
        ngrp = max(2, per // 3)
        grp = rng.r.integers(0, ngrp, k) + idx * ngrp
        gd = _norm(rng.r.random((ngrp * ns, 3)) - 0.5
                   + np.repeat(Dn, ngrp, axis=0) * 0.60
                   + np.array([0.0, 0.0, -0.20]))[grp]
        along = (rng.arr(k) ** 0.62)[:, None] * (slen[idx][:, None]
                                                 * (0.9 + 1.6 * self.f["spread"]))
        pos = base + lat * (RD[idx][:, None] * 1.06) + gd * along

        ang = rng.r.uniform(0.55, 1.35, k)[:, None]
        fwd = _norm(pdir * np.cos(ang) + lat * np.sin(ang))
        # droop: an oak leaf hangs, and the hang is what makes a crown read as
        # a surface with a lit top and a dark underside rather than a green ball
        fwd = _norm(fwd + np.array([0.0, 0.0, -1.0])
                    * rng.r.uniform(0.10, 0.62, k)[:, None])
        side = _norm(np.cross(fwd, np.array([0.011, 0.007, 1.0])))
        up = np.cross(fwd, side)
        # twist about the midrib, per leaf
        tw = rng.r.uniform(-0.55, 0.55, k)[:, None]
        side2 = _norm(side * np.cos(tw) + up * np.sin(tw))
        up2 = np.cross(fwd, side2)

        # leaves are OVERSIZED ~1.3x on purpose: 16,000 leaves is a tenth of a
        # real oak's count, and the leaf AREA is what a crown reads by. Stated
        # here rather than hidden in a constant.
        size = 0.098 + 0.055 * rng.arr(k)
        place_leaves(acc, pos, fwd, side2, up2, size, rng.arr(k))


def _resample(pts, rad, step):
    """Resample a polyline to an even arclength pitch, radii interpolated."""
    d = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
    arc = np.concatenate([[0.0], np.cumsum(d)])
    total = float(arc[-1])
    if total < 1e-6:
        return pts, np.asarray(rad, float)
    n = max(2, int(math.ceil(total / max(step, 1e-4))) + 1)
    s = np.linspace(0.0, total, n)
    out = np.stack([np.interp(s, arc, pts[:, i]) for i in range(3)], axis=1)
    rr = np.interp(s, arc, np.asarray(rad, float))
    return out, rr


# ===========================================================================
# 8.  MATERIALS.  Everything procedural; every wavelength stated in metres.
# ===========================================================================

def _srgb(h):
    return K.srgb_linear(h)


def mat_bark():
    """Oak bark. The SHADER GARNISHES; the mesh carries the read.

    Three things this does that a bark shader usually does not:

    1. IT READS THE GEOMETRY. `tok_fis` is the furrow-depth fraction the
       displacement field itself computed, baked per vertex. The furrows are
       darkened from THAT, not from a second noise -- so the paint and the shape
       are the same object. Deriving them separately is how a surface ends up
       with a lip in one place and a shadow in another, which is the decoupling
       `relief_reads_as_lip_and_shade` exists to catch.
    2. IT READS THE AGE. `tok_age` runs 0 at the butt to 1 at a twig tip, so
       young bark is smooth olive-grey and old bark is deep grey-brown with
       corky ridges, on one material.
    3. ITS BUMP STAGES ARE FINER THAN THE MESH. 2.6 mm and 11 mm, both below the
       9 mm circumferential / 15 mm axial sampling of the bole. Anything coarser
       would be relief the geometry is already carrying, applied twice.
    """
    t = K.NT(MAT_NAMES[MAT_BARK])
    obj = t.object_coords()
    fis = t.attr("tok_fis", out=2)
    age = t.attr("tok_age", out=2)

    # colour: three greys crossed with a warm heartwood tone in the furrows
    plate = t.noise(obj, wavelength_m=0.085, detail=6.0, rough=0.58)
    mott = t.noise(obj, wavelength_m=0.022, detail=8.0, rough=0.62)
    lich = t.vor(obj, wavelength_m=0.130, feature="F1", out=0)

    base = t.ramp(plate, [
        (0.00, _srgb("#3b352c")),
        (0.42, _srgb("#5a5145")),
        (0.68, _srgb("#6d6455")),
        (1.00, _srgb("#7d7361")),
    ])
    # furrows are darker and warmer -- the shadowed interior of the bark
    furrowed = t.cmix(fis, base, _srgb("#231d16"))
    # lichen: pale grey-green crusts, denser low down and on one side
    lichmask = t.math("MULTIPLY",
                      t.maprange(lich, 0.0, 0.35, 1.0, 0.0),
                      t.maprange(age, 0.0, 0.55, 1.0, 0.15))
    col = t.cmix(t.math("MULTIPLY", lichmask, 0.62), furrowed,
                 _srgb("#9aa08a"))
    # young bark at the twig end is olive and smooth
    col = t.cmix(t.maprange(age, 0.55, 1.0, 0.0, 1.0), col, _srgb("#6b6a4a"))
    col = t.cmix(t.math("MULTIPLY", mott, 0.30), col, _srgb("#4a4238"))

    # relief -- BOTH stages below the mesh's own sampling pitch
    lam_c = relief_lam_m("bark_crust")
    lam_l = relief_lam_m("bark_lichen")
    crust = t.noise(obj, wavelength_m=lam_c, detail=6.0, rough=0.65)
    scale = t.vor(obj, wavelength_m=lam_l, feature="F1", out=0)
    b1 = t.bump(crust, 1.0,
                modulation_pp=_STAGE["bark_crust"][3], wavelength_m=lam_c,
                height_pp=0.62)
    b2 = t.bump(scale, 0.85, normal=b1,
                modulation_pp=_STAGE["bark_lichen"][3], wavelength_m=lam_l,
                height_pp=0.80)

    rough = t.maprange(mott, 0.0, 1.0, 0.94, 0.72)
    bsdf = t.principled_out(base_color=col, roughness=rough, metallic=0.0)
    # BY NAME. Blender 5.2 moved `Normal` from index 5 to 6 and put `Thin Wall`
    # where it used to be -- R2-057, and it renders perfectly while moving
    # 0.00 % of the pixels.
    t.pin_named(bsdf, "Normal", b2)
    return t


def mat_leaf():
    """Oak leaf. Thin, translucent, veined, and NOT one green.

    The colour spread is per-leaf via `tok_pid` and it matters more than it
    sounds: a canopy of one green is the vegetation version of "six sampled
    stones cluster at one hue", which is a wave-1 verdict on `terrain_ground`.
    """
    t = K.NT(MAT_NAMES[MAT_LEAF])
    obj = t.object_coords()
    pid = t.attr("tok_pid", out=2)

    # a minority of leaves are turning; most are not. Opening this too far made
    # `build_terrain`'s first cut look like half the treeline was dead.
    turn = t.maprange(pid, 0.86, 1.0, 0.0, 1.0)
    tone = t.noise(obj, wavelength_m=0.60, detail=4.0, rough=0.5)
    green = t.ramp(t.fmix(0.55, pid, tone), [
        (0.00, _srgb("#2f4a17")),
        (0.35, _srgb("#3d5c1c")),
        (0.62, _srgb("#4a6b21")),
        (1.00, _srgb("#5c7a2b")),
    ])
    autumn = t.ramp(pid, [(0.0, _srgb("#8a7326")), (1.0, _srgb("#a05a1e"))])
    col = t.cmix(turn, green, autumn)
    # veins: paler, and running along the blade
    lam_g = relief_lam_m("leaf_grain")
    vein = t.vor(obj, wavelength_m=0.0055, feature="DISTANCE_TO_EDGE", out=0)
    col = t.cmix(t.maprange(vein, 0.0, 0.25, 0.55, 0.0), col, _srgb("#7f8c4a"))

    grain = t.noise(obj, wavelength_m=lam_g, detail=5.0, rough=0.6)
    b = t.bump(grain, 1.0, modulation_pp=_STAGE["leaf_grain"][3],
               wavelength_m=lam_g, height_pp=0.62)
    bsdf = t.principled_out(base_color=col, roughness=0.42, metallic=0.0)
    t.pin_named(bsdf, "Normal", b)
    # a leaf is 0.2 mm of translucent tissue; without this a backlit crown is a
    # black card and the dapple under an oak has no colour in it
    for nm, v in (("Subsurface Weight", 0.22), ("Subsurface Radius", None)):
        if nm in bsdf.inputs and v is not None:
            bsdf.inputs[nm].default_value = v
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.004, 0.010, 0.002)
    return t


def mat_deadwood():
    """A dead limb: bark gone, silvered sapwood, deep radial checks.

    `tree_dead_standing`'s manifest note calls standing deadwood "the single
    best silhouette element in a treeline, and the one that stops a wood looking
    generated". A stag-headed veteran carries its own.
    """
    t = K.NT(MAT_NAMES[MAT_DEAD])
    obj = t.object_coords()
    lam = relief_lam_m("deadwood_check")
    grain = t.noise(t.vmath("MULTIPLY", obj, (7.0, 7.0, 0.55)),
                    wavelength_m=0.030, detail=8.0, rough=0.62)
    check = t.vor(t.vmath("MULTIPLY", obj, (5.0, 5.0, 0.30)),
                  wavelength_m=lam, feature="DISTANCE_TO_EDGE", out=0)
    col = t.ramp(grain, [
        (0.00, _srgb("#6a6259")),
        (0.45, _srgb("#8a8177")),
        (0.80, _srgb("#9d968b")),
        (1.00, _srgb("#aaa49a")),
    ])
    col = t.cmix(t.maprange(check, 0.0, 0.16, 1.0, 0.0), col, _srgb("#2e2822"))
    b1 = t.bump(check, 1.0, modulation_pp=_STAGE["deadwood_check"][3],
                wavelength_m=lam, height_pp=0.80)
    b2 = t.bump(grain, 0.7, normal=b1,
                modulation_pp=_STAGE["bark_crust"][3],
                wavelength_m=relief_lam_m("bark_crust"), height_pp=0.62)
    bsdf = t.principled_out(base_color=col,
                            roughness=t.maprange(grain, 0.0, 1.0, 0.92, 0.74))
    t.pin_named(bsdf, "Normal", b2)
    return t


def mat_ivy():
    """Hedera helix on the bole: dark, waxy, lobed."""
    t = K.NT(MAT_NAMES[MAT_IVY])
    obj = t.object_coords()
    pid = t.attr("tok_pid", out=2)
    lam = relief_lam_m("ivy_leaf")
    tone = t.noise(obj, wavelength_m=0.24, detail=5.0, rough=0.55)
    col = t.ramp(t.fmix(0.5, pid, tone), [
        (0.00, _srgb("#16290f")),
        (0.45, _srgb("#1e3a15")),
        (0.80, _srgb("#2a4a1c")),
        (1.00, _srgb("#3c5a2a")),
    ])
    vein = t.vor(obj, wavelength_m=0.010, feature="DISTANCE_TO_EDGE", out=0)
    col = t.cmix(t.maprange(vein, 0.0, 0.20, 0.45, 0.0), col, _srgb("#8fa06a"))
    grain = t.noise(obj, wavelength_m=lam, detail=5.0, rough=0.6)
    b = t.bump(grain, 1.0, modulation_pp=_STAGE["ivy_leaf"][3],
               wavelength_m=lam, height_pp=0.62)
    bsdf = t.principled_out(base_color=col, roughness=0.28, metallic=0.0)
    t.pin_named(bsdf, "Normal", b)
    return t


def materials():
    return [mat_bark().m, mat_leaf().m, mat_deadwood().m, mat_ivy().m]


# ===========================================================================
# 9.  BUILD
# ===========================================================================

def _emit(name, arrays, mats, coll_):
    V, Q, T, PM, att = arrays
    me, off = K.new_mesh(name, V, quads=Q, tris=T, smooth_deg=33.0)
    for m in mats:
        me.materials.append(m)
    if len(me.polygons) == len(PM):
        me.polygons.foreach_set("material_index",
                                np.ascontiguousarray(PM, np.int32))
    else:                                          # validate() dropped polygons
        K.log("WARNING %s: %d polygons after validate, %d material ids -- "
              "material assignment SKIPPED rather than misapplied"
              % (name, len(me.polygons), len(PM)), tag=ITEM)
    if len(me.vertices) == len(att["tok_pid"]):
        K.bake_attributes(me, att)
    ob = bpy.data.objects.new(name, me)
    ob.location = off
    coll_.objects.link(ob)
    return ob, me


def _source_specs(n0=None, n1=None, n2=None):
    """The library plan: which (lod, form, age, lean, dead, ivy) each source is.

    Deterministic and printable, so 'is this actually 48 different trees' is a
    question that can be answered by reading a table instead of by trusting a
    count. Forms are dealt round-robin so no LOD tier is one form.
    """
    out = []
    counts = {0: LODS[0]["n_src"] if n0 is None else n0,
              1: LODS[1]["n_src"] if n1 is None else n1,
              2: LODS[2]["n_src"] if n2 is None else n2}
    sid = 0
    for lod in (0, 1, 2):
        n = counts[lod]
        for i in range(n):
            form = FORM_ORDER[(i + lod) % len(FORM_ORDER)]
            r = K.Rng(0xC0FFEE, lod, i)
            out.append(dict(
                sid=sid, lod=lod, form=form,
                seed=0x5EED0000 + lod * 1000 + i,
                age=round(0.25 + 0.75 * ((i * 7 + lod * 3) % n) / max(n - 1, 1), 4),
                lean_deg=round(r.u(0.0, 9.0), 3),
                lean_az=round(r.u(0.0, 2.0 * math.pi), 4),
                n_dead=int(r.i(0, 3)),
                ivy=bool(r.u() < 0.28)))
            sid += 1
    return out


def _gn_group(name, src_coll):
    """Instance on Points, from a collection, index-picked per point.

    THE POINT OF DOING IT THIS WAY. `item_gate.realized_instances` walks
    `depsgraph.object_instances`, and that is the ONLY path on which the variety
    red line is actually enforced: 4,500 real objects would be graded by
    `cv_size >= 0.03` and `distinct_topologies >= 2` and nothing else -- no cap
    on the commonest source at all. Leaving the instancer in the depsgraph is
    what makes the strong check apply. An item declaring thousands of instances
    that yields no realized instances is scored UNPROVEN, which is a FAIL and
    not a skip (R2-018/019).
    """
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    nds = ng.nodes
    lks = ng.links
    gin = nds.new("NodeGroupInput")
    gout = nds.new("NodeGroupOutput")
    gin.location = (-900, 0)
    gout.location = (600, 0)

    ci = nds.new("GeometryNodeCollectionInfo")
    ci.location = (-600, -260)
    ci.inputs["Collection"].default_value = src_coll
    for nm, val in (("Separate Children", True), ("Reset Children", True)):
        if nm in ci.inputs:
            ci.inputs[nm].default_value = val

    def named(attr, dtype):
        n = nds.new("GeometryNodeInputNamedAttribute")
        n.data_type = dtype
        n.inputs["Name"].default_value = attr
        return n

    a_src = named("tok_src", "INT")
    a_rot = named("tok_rot", "FLOAT_VECTOR")
    a_scl = named("tok_scl", "FLOAT")
    a_src.location = (-600, 120)
    a_rot.location = (-600, -40)
    a_scl.location = (-600, -160)

    iop = nds.new("GeometryNodeInstanceOnPoints")
    iop.location = (200, 0)
    lks.new(gin.outputs[0], iop.inputs["Points"])
    lks.new(ci.outputs["Instances"], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    lks.new(a_src.outputs["Attribute"], iop.inputs["Instance Index"])
    rot_sock = iop.inputs["Rotation"]
    if rot_sock.bl_idname == "NodeSocketRotation":
        e2r = nds.new("FunctionNodeEulerToRotation")
        e2r.location = (-300, -40)
        lks.new(a_rot.outputs["Attribute"], e2r.inputs[0])
        lks.new(e2r.outputs[0], rot_sock)
    else:
        lks.new(a_rot.outputs["Attribute"], rot_sock)
    lks.new(a_scl.outputs["Attribute"], iop.inputs["Scale"])
    lks.new(iop.outputs["Instances"], gout.inputs[0])
    return ng


def _field_points(n, rng, span=520.0):
    """Where the population stands. A treeline, not a lattice.

    Poisson-ish: a jittered grid with a rejection thinning driven by a coarse
    noise field, so the wood has glades and thickets instead of an even
    spacing. The gate does not measure this; the film does.
    """
    m = int(n * 2.4)
    x = (rng.arr(m) - 0.5) * span
    y = (rng.arr(m) - 0.5) * span
    dens = K.fbm2(x / 60.0, y / 60.0, seed=771, oct=4)
    keep = rng.arr(m) < np.clip(dens * 1.55, 0.05, 1.0)
    x, y = x[keep], y[keep]
    if len(x) > n:
        x, y = x[:n], y[:n]
    elif len(x) < n:
        k = n - len(x)
        x = np.concatenate([x, (rng.arr(k) - 0.5) * span])
        y = np.concatenate([y, (rng.arr(k) - 0.5) * span])
    return x, y


def build(scene=None, sources=None, instances=DECLARED_INSTANCES,
          field_span=520.0, stats=None):
    """Emit the library and the instanced population into `COLL`.

    `sources` overrides the (24, 12, 12) library plan -- it exists so a smoke
    test can build four trees on an 11 GB box, and NOT so a gate run can be made
    cheap. The count actually built is reported.
    """
    K._require_bpy("build")
    scene = scene or bpy.context.scene
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    src_c = K.coll(SRC_COLL, root)

    mats = materials()
    specs = _source_specs(*(sources or (None, None, None)))
    K.log("library plan: %d sources -- %s"
          % (len(specs), ", ".join("L%d/%s" % (s["lod"], s["form"])
                                   for s in specs[:8]) + " ..."), tag=ITEM)

    objs, tri_tot, vert_tot = [], 0, 0
    for s in specs:
        tr = Tree(s["seed"], s["form"], s["lod"], age=s["age"],
                  lean_deg=s["lean_deg"], lean_az=s["lean_az"],
                  n_dead=s["n_dead"], ivy=s["ivy"]).grow()
        arrays = tr.mesh()
        if arrays is None:
            raise RuntimeError("source %d produced no geometry" % s["sid"])
        name = PFX + "SRC_L%d_%02d_%s" % (s["lod"], s["sid"], s["form"])
        ob, me = _emit(name, arrays, mats, src_c)
        # the library stands in a row well clear of the field, so it is visible,
        # measurable and not tangled with the population
        ob.location = (float(ob.location[0]) - 900.0 + 26.0 * s["sid"],
                       float(ob.location[1]) - 900.0,
                       float(ob.location[2]) + K.ground_z(0.0, 0.0))
        ntri = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
        tri_tot += ntri
        vert_tot += len(me.vertices)
        objs.append(ob)
        K.log("  %-28s h %5.2f m  age %.2f  %7d verts  %8d tris  %s%s"
              % (name, tr.h, tr.age, len(me.vertices), ntri,
                 "dead %d " % tr.n_dead if tr.n_dead else "",
                 "ivy" if tr.ivy else ""), tag=ITEM)

    # -- the population -----------------------------------------------------
    rng = K.Rng(0xF0BE, 7)
    n = int(instances)
    x, y = _field_points(n, rng, span=field_span)
    z = np.full(n, K.ground_z(0.0, 0.0)) - C.BASE_EMBED_M
    P = np.stack([x, y, z], axis=1)

    # which source each point uses. Drawn per TIER by the film's own mix, then
    # uniformly inside the tier, so no source can exceed ~1/n_in_tier of its
    # tier and the commonest overall lands far below the gate's 25 % cap.
    by_lod = {0: [], 1: [], 2: []}
    for i, s in enumerate(specs):
        by_lod[s["lod"]].append(i)
    tier = rng.r.choice(3, size=n, p=np.array(LOD_MIX) / sum(LOD_MIX))
    src = np.zeros(n, np.int32)
    for l in (0, 1, 2):
        m = tier == l
        pool = by_lod[l] or [0]
        src[m] = np.array(pool)[rng.r.integers(0, len(pool), int(m.sum()))]

    rot = np.zeros((n, 3))
    rot[:, 2] = rng.arr(n) * 2.0 * math.pi
    rot[:, 0] = (rng.arr(n) - 0.5) * math.radians(5.0)
    rot[:, 1] = (rng.arr(n) - 0.5) * math.radians(5.0)
    scl = 0.82 + 0.40 * rng.arr(n)

    me = bpy.data.meshes.new(PFX + "FIELD")
    me.vertices.add(n)
    me.vertices.foreach_set("co", np.ascontiguousarray(P, np.float32).ravel())
    me.update()
    a = me.attributes.new("tok_src", "INT", "POINT")
    a.data.foreach_set("value", np.ascontiguousarray(src, np.int32))
    a = me.attributes.new("tok_rot", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", np.ascontiguousarray(rot, np.float32).ravel())
    a = me.attributes.new("tok_scl", "FLOAT", "POINT")
    a.data.foreach_set("value", np.ascontiguousarray(scl, np.float32))
    field = bpy.data.objects.new(PFX + "FIELD", me)
    root.objects.link(field)
    ng = _gn_group(PFX + "GN_Instance", src_c)
    mod = field.modifiers.new(PFX + "GN", "NODES")
    mod.node_group = ng

    if stats is not None:
        stats.update(sources=len(specs), triangles=tri_tot, vertices=vert_tot,
                     instances=n)
    K.log("LIBRARY %d sources, %d triangles, %d vertices; FIELD %d instances"
          % (len(specs), tri_tot, vert_tot, n), tag=ITEM)
    return root


# ===========================================================================
# 10.  TEST SCENE, MACRO, INTERFACE
# ===========================================================================

def macro_aim(root):
    """Where the deliverable macro looks: the butt of the tallest L0 veteran.

    Chosen by rule, not by convenience -- the veteran is the form that carries
    the deepest bark, the dead limbs and the ivy, and the BUTT is where the
    fissure network is at its full depth. A macro of the smoothest part of the
    smoothest tree is a picture of a different item.
    """
    best, bz = None, -1e9
    for ob in bpy.data.objects:
        if not ob.name.startswith(PFX + "SRC_L0"):
            continue
        d = ob.dimensions
        sc = float(d.z) + (6.0 if "veteran" in ob.name else 0.0) \
            + (3.0 if "open" in ob.name else 0.0)
        if sc > bz:
            best, bz = ob, sc
    return best


def test_scene(samples=256, sources=None, instances=DECLARED_INSTANCES,
               field_span=520.0, stats=None):
    scene = bpy.context.scene
    root = build(scene=scene, sources=sources, instances=instances,
                 field_span=field_span, stats=stats)
    cams = K.coll(CAM_COLL, root)
    stand = K.coll(STAND_COLL, root)
    # `contract_sun` ALWAYS makes the lamp and MEASURES its emitted direction --
    # 2 of 28 wave-1 test scenes had no sun at all and R2-021 records the same
    # author writing one that pointed upward twice in one session.
    K.contract_sun(PFX, scene=scene, coll_=root)
    # z = 0.000 is simultaneously showroom floor, paddock apron, access road and
    # racing surface. Outside those the contract has NO closed form and returns
    # NaN, so a standin plane this wide has to say what it wants there rather
    # than have a height invented for it.
    K.ground_plane(PFX, stand, span=max(160.0, field_span * 1.1), res=180,
                   fill_z=0.0)

    hero = macro_aim(root)
    if hero is None:
        raise RuntimeError("no L0 source to point the macro at")
    lo = np.array(hero.bound_box).min(axis=0) + np.array(hero.location)
    hi = np.array(hero.bound_box).max(axis=0) + np.array(hero.location)
    # aim at the bole at 2.1 m -- the height a standing eye meets a trunk, and
    # the band where oak bark is deepest
    aim = np.array([0.5 * (lo[0] + hi[0]), 0.5 * (lo[1] + hi[1]),
                    float(lo[2]) + 2.10])
    az = math.radians(38.0)
    el = math.radians(9.0)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                  math.sin(el)])
    loc = aim + d * GATE_AT_M
    K.macro_rig(PFX + "CAM_MACRO_4K", tuple(float(v) for v in loc),
                tuple(float(v) for v in aim), LENS_MM, cams, scene=scene,
                samples=samples, want_distance_m=GATE_AT_M, tolerance_m=0.02)
    # a second camera at the far end of the stated range, so the same tree can
    # be judged whole as well as close. NOT the deliverable; recorded as such.
    K.add_camera(PFX + "CAM_FULL_4K",
                 tuple(float(v) for v in (aim + np.array([0.0, 0.0, 6.0])
                                          + d * FULL_M)),
                 tuple(float(v) for v in (aim + np.array([0.0, 0.0, 6.0]))),
                 LENS_MM, cams)
    K.assert_no_external_assets()
    return root


def interface_json(path=None):
    """What dependants may rely on. `tree_oak` has 2 declared dependants."""
    rows = relief_budget(verbose=False)
    return K.interface_json(
        ITEM, path=path,
        collection=COLL,
        source_collection=SRC_COLL,
        prefix=PFX,
        materials={"bark": MAT_NAMES[0], "leaf": MAT_NAMES[1],
                   "deadwood": MAT_NAMES[2], "ivy": MAT_NAMES[3]},
        material_slot_order=list(MAT_NAMES),
        vertex_attributes={
            "tok_pid": "per-leaf random [0,1), constant within one leaf",
            "tok_age": "0 at the butt, 1 at a twig tip; drives bark maturity",
            "tok_fis": "furrow depth fraction, 0 plate top .. 1 furrow floor",
        },
        instancing={
            "mechanism": "GeometryNodeInstanceOnPoints, Pick Instance from "
                         + SRC_COLL,
            "point_attributes": {"tok_src": "INT source index",
                                 "tok_rot": "FLOAT_VECTOR euler",
                                 "tok_scl": "FLOAT uniform scale"},
            "declared_instances": DECLARED_INSTANCES,
            "lod_mix_l0_l1_l2": list(LOD_MIX),
            "sources_per_lod": {str(k): LODS[k]["n_src"] for k in (0, 1, 2)},
        },
        framing={
            "near_m": NEAR_M,
            "far_full_frame_m": round(FULL_M, 3),
            "gated_at_m": GATE_AT_M,
            "lens_mm": LENS_MM,
            "px_per_m_near": round(PX_PER_M_NEAR, 1),
            "px_per_m_full": round(PX_PER_M_FULL, 1),
            "PROVENANCE": (
                "near_m is screen_presence.json min_depth_m for this item's 93 "
                "HOSTS (understorey shrubs, ferns, saplings), NOT for a tree; "
                "all five tree species report the identical 4.577 m, which is "
                "the signature of one shared host set. far_full_frame_m is "
                "derived from the manifest's 17.0 m height and a clamped "
                "peak_px_4k of 2160.0. NEITHER IS A MEASUREMENT OF THIS ITEM. "
                "What would settle it: place this module in the assembled "
                "world and re-run tools/retier.sh."),
        },
        relief_budget=[{k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in r.items()} for r in rows],
        sun={"elev_deg": K.sun_elev_deg(),
             "amplifier_vs_45deg": round(K.sun_amplifier(), 4)},
        seating="base embeds >= world_contract.BASE_EMBED_M below "
                "world_contract.world_ground_z(x, y)",
        height_range_m=[min(FORMS[f]["h"][0] for f in FORMS),
                        max(FORMS[f]["h"][1] for f in FORMS)],
        forms={k: FORMS[k]["h"] for k in FORM_ORDER},
    )


# ===========================================================================
# 11.  SELFTEST -- measured, with negative controls
# ===========================================================================

def selftest(verbose=True):
    ok = True

    def chk(tag, cond, msg):
        nonlocal ok
        ok = ok and bool(cond)
        if verbose:
            print("  %-4s %s -- %s" % ("ok" if cond else "FAIL", tag, msg))

    print("[1] the relief budget is DERIVED from the contract sun")
    rows = relief_budget(verbose=verbose)
    chk("1a", abs(K.sun_elev_deg() - C.SUN_ELEV_DEG) < 1e-9,
        "sun read from world_contract: %.5f deg, amplifier %.4fx"
        % (K.sun_elev_deg(), K.sun_amplifier()))
    chk("1b", all(r["verdict"] == "ok" for r in rows),
        "%d stages, all inside their declared band" % len(rows))
    # NEGATIVE CONTROL: the check must reject something known to be wrong.
    try:
        K.relief_budget([("bogus", 0.078, 60.0)], band="hard_feature",
                        verbose=False)
        bad = K.relief_budget([("bogus", 0.078, 60.0)], band="hard_feature",
                              verbose=False)[0]["verdict"]
    except Exception:                                          # noqa: BLE001
        bad = "raised"
    chk("1c", bad in ("HIGH", "raised"),
        "negative control: 60 mm at a 78 mm wavelength is scored %r, not 'ok'"
        % bad)

    print("[2] no amplitude and no amplifier in this file is typed")
    src = open(os.path.abspath(__file__), "r", encoding="utf-8").read()
    # The needles are ASSEMBLED so they do not appear as literals in the file
    # being searched. A grep for a string that the grep itself contains is a
    # check that can never pass, which is how the first run of this failed.
    amp_needles = ["4" + ".52", "4" + ".5x", "0" + ".2213", "0" + ".22125"]
    hits = [s for s in amp_needles if s in src]
    chk("2a", not hits,
        "the sun amplifier and tan(e) appear nowhere as literals (searched %d "
        "spellings, %d hits) -- they are read from world_contract every time"
        % (len(amp_needles), len(hits)))
    amp = relief_amp_mm("fissure_network")
    lam = relief_lam_m("fissure_network")
    back = K.modulation_for_amplitude(amp, lam)
    chk("2b", abs(back - _STAGE["fissure_network"][3]) < 1e-6,
        "fissure_network round-trips: m %.4f -> %.4f mm -> m %.4f"
        % (_STAGE["fissure_network"][3], amp, back))

    print("[3] the pixel footprint -- Law 3, both ends of the stated range")
    lams = sorted(set(r[4] for r in RELIEF_STAGES))
    near = [l * PX_PER_M_NEAR for l in lams]
    full = [l * PX_PER_M_FULL for l in lams]
    chk("3a", min(near) >= 1.0,
        "finest stage is %.2f px at %.3f m -- nothing below a pixel at the "
        "near end" % (min(near), NEAR_M))
    chk("3b", max(full) <= 2160.0,
        "coarsest stage is %.0f px at %.2f m -- nothing above the frame"
        % (max(full), FULL_M))
    chk("3c", sum(1 for p in full if p >= 2.0) >= 3,
        "%d of %d octaves still resolve at the FAR end"
        % (sum(1 for p in full if p >= 2.0), len(full)))

    print("[4] the framing is internally consistent with the manifest")
    manifest_px = 3733.333333 / 30.0 * HEIGHT_M
    chk("4a", abs(manifest_px - 2116.0) < 2.0,
        "the manifest's 30.0 m / 2116 px reproduces to %.1f px, so 30 m is the "
        "FAR end of the range and not an error" % manifest_px)
    chk("4b", GATE_AT_M < 30.0,
        "gated at %.3f m, %.2fx nearer than the manifest's 30.0 m"
        % (GATE_AT_M, 30.0 / GATE_AT_M))

    print("[5] the library is 48 genuinely different trees")
    specs = _source_specs()
    chk("5a", len(specs) >= 40,
        "%d sources vs the gate's floor of 40 at 4,500 realized instances "
        "(manifest's 8/12/16 = 36 would MISS it)" % len(specs))
    forms = set(s["form"] for s in specs)
    chk("5b", len(forms) == 5, "5 growth forms present: %s" % sorted(forms))
    keys = set((s["form"], round(s["age"], 2), round(s["lean_deg"], 1),
                s["n_dead"], s["ivy"]) for s in specs)
    chk("5c", len(keys) >= len(specs) * 0.9,
        "%d of %d sources have a distinct (form, age, lean, dead, ivy) key"
        % (len(keys), len(specs)))
    top = max(LOD_MIX) / max(1, min(LODS[l]["n_src"] for l in (0, 1, 2)))
    chk("5d", top <= 0.25,
        "worst-case commonest source share %.3f, gate cap 0.25" % top)
    n0 = LODS[0]["n_src"]
    chk("5e", n0 >= (n0 + LODS[1]["n_src"] + LODS[2]["n_src"]) / 2,
        "L0 is %d of %d sources, so the gate's MEDIAN-triangle subject is an "
        "L0 hero and not a distant proxy"
        % (n0, n0 + LODS[1]["n_src"] + LODS[2]["n_src"]))

    print("[6] the leaf is a dihedral with lobes, not a card")
    a, b = 4, 9
    V, T = leaf_template(a, b)
    blade_m = LEAF_BLADE_M
    # MEASURE THE V THE TEMPLATE ACTUALLY BUILDS, at matched x, and convert the
    # slope back through the sun. Comparing raw z MEANS is what hid the first
    # draft's factor-of-70: the midrib and the margin are sampled at different
    # rates, so the droop term alone moved the two means by 0.55 mm and buried
    # a 0.14 mm rib inside it.
    xm = V[a:a + b, 0]
    dz = np.interp(xm, V[:a, 0], V[:a, 2]) - V[a:a + b, 2]
    half = np.abs(V[a:a + b, 1])
    live = half > 0.12
    slope = np.degrees(np.arctan((dz[live] * blade_m)
                                 / np.maximum(half[live] * blade_m, 1e-9)))
    m_cup = K.modulation_for_slope(float(np.median(slope)))
    lo_f, hi_f = K.RELIEF_BANDS["geometry_fold"]
    chk("6a", lo_f <= m_cup <= hi_f,
        "the blade's own cross-section stands at %.2f deg = m %.3f, inside "
        "geometry_fold [%.2f, %.2f]; declared leaf_cup m %.2f. That is "
        "%.2f mm of lift across a %.0f mm half-blade"
        % (float(np.median(slope)), m_cup, lo_f, hi_f, _STAGE["leaf_cup"][3],
           1000.0 * blade_m * float(np.median(dz[live])),
           1000.0 * blade_m * float(np.median(half[live]))))
    w = np.abs(V[a:a + b, 1])
    turns = int(np.sum(np.diff(np.sign(np.diff(w))) != 0))
    chk("6b", turns >= 4,
        "the margin turns %d times over %d stations -- %d lobes and %d sinuses "
        "per side, not an ellipse" % (turns, b, b // 2, b // 2))
    # NEGATIVE CONTROL: an un-lobed envelope of the same blade must NOT pass
    env = 0.46 * np.sin(np.pi * np.clip((np.linspace(0, 1, b) + 0.13) / 1.16,
                                        0, 1)) ** 0.70
    ctl_turns = int(np.sum(np.diff(np.sign(np.diff(env))) != 0))
    chk("6c", ctl_turns < 4,
        "negative control: the same blade WITHOUT the lobe alternation turns "
        "%d times and would fail this check" % ctl_turns)
    chk("6d", len(V) <= 24 and len(T) <= 24,
        "%d verts / %d tris per leaf -- 16,000 of them is %.2f M tris, which "
        "is the crown's whole budget and has to be this cheap"
        % (len(V), len(T), 16000 * len(T) / 1e6))

    print("[7] the bark field, MEASURED off the field itself")
    th = np.array([0.0, 2.0 * math.pi - 1e-9])
    u = np.array([1.3, 1.3])
    r = np.array([0.22, 0.22])
    d, f = bark_relief(th, u, r, 12345, np.array([0.2, 0.2]),
                       np.array([1.0, 1.0]))
    chk("7a", abs(float(d[0] - d[1])) < 1e-5,
        "theta = 0 and theta = 2pi agree to %.2e m -- no seam down the trunk"
        % abs(float(d[0] - d[1])))
    # NEGATIVE CONTROL: a planar field addressed as (theta*r, u) does NOT wrap
    plan = K.fbm2(np.array([0.0, 2.0 * math.pi * 0.22]) / 0.078,
                  np.array([1.3, 1.3]) / 0.078, seed=1)
    chk("7b", abs(float(plan[0] - plan[1])) > 1e-3,
        "negative control: the planar addressing this replaces is discontinuous "
        "by %.4f at the wrap" % abs(float(plan[0] - plan[1])))

    # -- THE ONE THAT MATTERS. Measure the SLOPE the built field delivers and
    # convert it back through the sun, instead of round-tripping an amplitude
    # through the constant that produced it (REFERENCE.md on R2-058: an
    # algebraic identity cannot fail for any value of the constant).
    R0 = 0.22
    n = 32768
    th2 = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    u2 = np.full(n, 2.0)
    d2, f2 = bark_relief(th2, u2, np.full(n, R0), 77,
                         np.full(n, 0.15), np.full(n, 1.0))
    ds = R0 * (2.0 * math.pi / n)                    # arclength per sample
    grad = np.abs(np.diff(d2)) / ds
    slope_meas = math.degrees(math.atan(float(np.quantile(grad, 0.999))))
    m_meas = K.modulation_for_slope(slope_meas)
    lo, hi = K.RELIEF_BANDS["hard_feature"]
    chk("7c", lo <= m_meas <= hi,
        "the built ring's 99.9th-percentile wall stands at %.2f deg = m %.3f, "
        "inside hard_feature [%.2f, %.2f]. Declared: fissure_network m %.2f, "
        "fissure_major m %.2f"
        % (slope_meas, m_meas, lo, hi, _STAGE["fissure_network"][3],
           _STAGE["fissure_major"][3]))
    pp = float(d2.max() - d2.min()) * 1000.0
    chk("7d", 7.0 <= pp <= 26.0,
        "one ring at r = %.2f m swings %.2f mm peak-to-peak. A real veteran "
        "runs 20-25 mm; this is DELIBERATELY under it because 55-70 deg walls "
        "are m = 7.0-8.7 and hard_feature stops at 6.00 (see the module "
        "docstring)" % (R0, pp))
    chk("7e", float(f2.max()) > 0.85 and float((f2 > 0.5).mean()) < 0.50,
        "furrows occupy %.0f %% of the circumference and reach depth %.2f -- "
        "narrow grooves between FLAT PLATES, which is why the profile is a "
        "smoothstep well and not a sinusoid"
        % (100.0 * float((f2 > 0.5).mean()), float(f2.max())))
    # -- ONE STAGE IN ISOLATION, against its OWN declared slope. This is the
    # check on `well_depth_m` itself, and it is NOT an identity: the field is
    # built, sampled, differentiated, and the answer compared with the number
    # the stage asked for. REFERENCE.md's R2-058 is the reason that distinction
    # is worth this much code -- a round-trip through the constant under test
    # passed for three weeks while the constant was 3.183x wrong.
    def _measure(only, bug=False):
        dd, _ = bark_relief(th2, u2, np.full(n, R0), 77, np.full(n, 0.15),
                            np.full(n, 1.0), only=only, sinusoid_bug=bug)
        g = np.abs(np.diff(dd)) / ds
        # THE SAME STATISTIC THE CALIBRATION USES. `max()` over 32,768 samples
        # is one sample and moves several degrees with the seed; p99.9 is 33
        # samples and is what "the steepest wall" means.
        return math.degrees(math.atan(float(np.quantile(g, 0.999))))

    got = _measure("fissure_network")
    want = relief_slope_deg("fissure_network")
    chk("7f", abs(got - want) / want < 0.10,
        "fissure_network ALONE, built and then measured off the built field: "
        "%.2f deg against the %.2f deg its declared m = %.2f asks for, "
        "%.1f %% apart"
        % (got, want, _STAGE["fissure_network"][3],
           100.0 * abs(got - want) / want))
    # NEGATIVE CONTROL: the sinusoid amplitude on this smoothstep -- the first
    # draft of this file -- must MISS the declared slope and be rejected by the
    # check that just passed the real one.
    bad = _measure("fissure_network", bug=True)
    chk("7g", abs(bad - want) / want > 0.20,
        "negative control: handing this profile relief_amplitude_for's SINUSOID "
        "amplitude gives %.2f deg = m %.2f, %.0f %% off the declared %.2f deg "
        "/ m %.2f -- REJECTED"
        % (bad, K.modulation_for_slope(bad), 100.0 * abs(bad - want) / want,
           want, _STAGE["fissure_network"][3]))
    # maturity gate: a twig must be SMOOTH
    d3, _ = bark_relief(th2[:512], u2[:512], np.full(512, 0.006), 77,
                        np.full(512, 0.9),
                        np.full(512, float(K.smoothstep(0.035, 0.110, 0.006))))
    chk("7h", float(d3.max() - d3.min()) * 1000.0 < 0.30,
        "a 6 mm twig swings %.4f mm -- young bark is smooth, and it is the "
        "LOCAL RADIUS that decides, not the branch order"
        % (float(d3.max() - d3.min()) * 1000.0))

    print("[8] the pipe model, not a fixed fraction")
    t = Tree(1, "open", 0)
    r_at = 0.10
    rs = t._child_radii(r_at, [1.0, 1.0, 1.0, 1.0])
    chk("8a", abs(float(np.sum(rs ** 2.49)) - r_at ** 2.49) < 1e-9,
        "4 children of a 100 mm limb come out at %.1f mm each and conserve "
        "r^2.49 exactly" % (1000.0 * float(rs[0])))
    chk("8b", float(rs[0]) < r_at,
        "a child is thinner than its parent (%.1f < %.1f mm) -- the defect "
        "that made the first terrain pass 'look like a coral'"
        % (1000.0 * float(rs[0]), 1000.0 * r_at))

    print("[9] no external assets are reachable from this module")
    # Same assembled-needle trick as [2a], and for the same reason.
    ext = ["ShaderNodeTex" + "Image", "." + "hdr", "." + "exr", "." + "png\"",
           "images." + "load", "bpy.ops." + "import"]
    hits = [s for s in ext if s in src]
    chk("9a", not hits,
        "none of %d external-asset spellings appears in the source (%s). "
        "Law 8, checked for free before any GPU job." % (len(ext), hits or "0"))
    lam_used = set()
    for name, layer, band, m, lam in RELIEF_STAGES:
        lam_used.add(lam)
    chk("9b", "scale=" not in src.replace("scale=None", "")
        .replace("scale=1.0", "").replace("scale=", "wavelength_m=", 0)
        or src.count("wavelength_m=") >= src.count("scale="),
        "every texture is addressed by wavelength_m (%d) at least as often as "
        "by scale (%d) -- Law 5, and reading 1.0/scale for a Voronoi is 2.17x "
        "out" % (src.count("wavelength_m="), src.count("scale=")))

    print("\n%s" % ("SELFTEST PASSED" if ok else "SELFTEST FAILED"))
    return ok


# ===========================================================================
# 12.  CLI
# ===========================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--build", action="store_true")
    p.add_argument("--test", action="store_true",
                   help="build + sun + ground + the 4K macro rig")
    p.add_argument("--out", default=None, help="save the .blend here")
    p.add_argument("--interface", default=None)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--sources", type=int, nargs=3, default=None,
                   metavar=("N_L0", "N_L1", "N_L2"),
                   help="override the (24, 12, 12) library plan -- for smoke "
                        "tests on an 11 GB box, not for gate runs")
    p.add_argument("--instances", type=int, default=DECLARED_INSTANCES)
    p.add_argument("--field-span", type=float, default=520.0)
    p.add_argument("--budget", action="store_true",
                   help="print the relief budget and stop")
    a = p.parse_args(argv)

    if a.budget:
        relief_budget(verbose=True)
        return 0
    if a.selftest and not (a.build or a.test):
        return 0 if selftest() else 1

    K._require_bpy("main")
    stats = {}
    if a.test:
        test_scene(samples=a.samples, sources=a.sources,
                   instances=a.instances, field_span=a.field_span, stats=stats)
    else:
        build(sources=a.sources, instances=a.instances,
              field_span=a.field_span, stats=stats)
        K.assert_no_external_assets()
    if a.interface:
        interface_json(a.interface)
    else:
        interface_json(os.path.join(_HERE, ITEM + "_interface.json"))
    if a.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                    compress=True)
        K.log("saved %s (%.1f MB)"
              % (a.out, os.path.getsize(a.out) / 1e6), tag=ITEM)
    if a.selftest:
        selftest()
    print(">> STAGE RESULT: TREE_OAK_BUILT sources=%d triangles=%d "
          "instances=%d" % (stats.get("sources", 0), stats.get("triangles", 0),
                            stats.get("instances", 0)))
    K.log("gate: " + " ".join(K.gate_command(
        ITEM, a.out or "<blend>", collection=COLL,
        filmed_distance_m=GATE_AT_M)), tag=ITEM)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
