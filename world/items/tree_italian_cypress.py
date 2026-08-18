"""tree_italian_cypress — Cupressus sempervirens 'Stricta', the columnar form.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/tree_italian_cypress.py -- --test-scene --out <blend>

WHAT THIS ITEM IS, AND THE ONE THING THAT MAKES IT HARD
=======================================================
A cypress is a near-perfect analytic column. That walks straight into the gate's
check 8, `silhouette_departs_from_analytic`, which fits a quadratic to the
rendered outline inside every 100-row window and measures the residual. A
wave-1 trouser fitted a quadratic to **0.61 px RMS** and was rejected as "a
machined cone". A cypress that fits a cylinder or a cone that well is the same
defect wearing different bark.

So the departure is BUILT, not smoothed away, and it is built out of the four
things that break a real cypress's outline:

  1. FROND CLUMPS.  The crown is not a surface. It is ~1,200 discrete foliage
     lobes, each a ragged-edged spray whose boundary is a fringe of 6-16
     tapering fingers. The outer lobes ARE the outline; they stand 40-140 mm
     proud of the envelope at their own spacing, which is 0.10-0.35 m -- i.e.
     INSIDE the 0.375 m window the check refits in, which is the only place a
     departure can survive a quadratic.
  2. ASYMMETRY FROM LIGHT AND WIND.  The envelope radius carries a first and a
     second azimuthal harmonic (thinner on the shaded side, combed downwind), so
     the LEFT and RIGHT profiles of one tree are different curves. One quadratic
     cannot be right about both.
  3. SPLAY AT THE TOP OF OLDER ONES -- the manifest's own variation axis. Above
     `splay_z0` the leaders flare outward by up to 0.62 m and droop; on a
     multi-leader specimen the top is a candelabra, not a point.
  4. GAPS.  0-3 recesses where a branch was lost or the interior is shaded,
     20-45 % deep over 0.4-1.2 m.

Every one of those is GEOMETRY. Law 7: "on this film's sun, the mesh carries the
read and the shader garnishes it."

THE FRAMING, AND THE CAVEAT I AM NOT ALLOWED TO LAUNDER
======================================================
`docs/item_manifest.json` says `nearest_camera_m` 20.0 and `hero: false`.
R2-1378 measures the manifest wrong in both directions and it is wrong here.

`docs/screen_presence.json` measures, over all 2,978 frames:

    peak_unocc_sharp_px_4k   2160.0   (frame-capped) at frame 2316, beat 5
    frames >= 300 px            766
    frames >= 150 px            899
    frames visible            2,289   (76.9 %)
    min_depth_m               4.577
    instances                 1,400   height 12.0 m

**Those are HOST upper bounds and this item is UNBUILT.** The file's own
`presence_unverified_2026_08_04` block says so, and says that "a HERO verdict on
an item listed ABSENT in the census must not be quoted without the qualifier".
This item's 93 hosts are `VEG_shrub_*`, `VEG_sapling`, `VEG_fern` and 81 more --
ground-level vegetation. All five tree species report the SAME `min_depth_m` of
4.577 m, which is one shared host approach, not five measurements. 4.577 m is
the closest the camera comes to that vegetation LAYER; it is not a measurement
of a 12 m paddock tree.

So this module states a RANGE and gates at a STATED distance inside it:

    BUILT FOR      6 m .. 45 m
    GATED AT      14.000 m  (`STATED_AT_M`), 266.7 px/m, 3.75 mm/px
    ALSO GATED AT  4.577 m  (`HOST_BOUND_M`), 815.7 px/m, 1.23 mm/px

14.0 m is not invented. It is the `nearest_camera_m` the manifest gives every
other PADDOCK tree -- `tree_london_plane` 14.0, `paddock_avenue_tree` 14.0,
`planter_shrub` 14.0 -- and this item's own `variation_axes` opens with "14 % of
the paddock mix". It is 1.43x CLOSER than this item's own manifest figure, so it
is a strictly harder framing than the one the gate would have used, and it keeps
check 8 IN SCOPE: `SIL_MIN_PX_FOR_5MM` scopes the check out below 200 px/m, and
gating at the manifest's 20.0 m would have put 5 mm at 0.93 px and made the one
check this item is most exposed to `not_applicable`. Choosing a distance that
switches off the check that matters is not a framing decision, it is a dodge.

WHAT WOULD SETTLE IT.  `screen_presence.json`'s own `to_clear` says: place the
item modules into the assembled world and re-derive with `tools/retier.sh`.
`SHIPPING.md` says `assembly10.blend` is the first assembly with anything from
`world/items/` in it. Until this module is IN an assembly and re-swept, 4.577 m
belongs to the ferns. The second gate run at 4.577 m is reported for exactly
that eventuality, and section 15's `pixel_footprint()` prints what every stated
wavelength is worth in pixels at BOTH distances, so nothing here has to be
re-derived if the sweep moves.

THE RELIEF BUDGET -- BOTH LAYERS, AND WHERE THE LAW STOPS APPLYING
==================================================================
`itemkit` section 5b: what the eye judges is the radiance modulation, not the
height, and at this film's 12.47 deg sun the conversion carries an amplifier
this module never writes down (`K.sun_amplifier()` derives it from
`world_contract.SUN_ELEV_DEG`). Every amplitude below comes out of
`K.relief_amplitude_for(m, wavelength_m)`; not one millimetre is typed.

    layer      feature                    lambda      band            m
    ---------- -------------------------- ----------- --------------- ----
    GEOMETRY   branchlet ridging on a      30 mm      hard_feature    5.00
               spray                                  (1.50-6.00)
    GEOMETRY   spray-surface undulation    70 mm      geometry_fold   1.15
    GEOMETRY   trunk fluting               55 mm      geometry_fold   1.20
    GEOMETRY   bark fissure                26 mm      hard_feature    3.20
    SHADER     inter-branchlet groove      14 mm      isotropic_micro 0.40
    SHADER     scale-leaf rank              2.5 mm    isotropic_micro 0.28
    SHADER     bark fibre                   3.5 mm    isotropic_micro 0.30
    SHADER     bark plate                  22 mm      isotropic_macro 0.62
    SHADER     cone scale shield            7 mm      isotropic_macro 0.55

WHERE THE LAW STOPS.  `slope_for_modulation` REFUSES m > 2/tan(e) = 9.04 and
says why: "asking for more is asking for a shadow, which is geometry, not
relief." A foliage mass is entirely made of that. The lobe FORM -- the 0.18 m
clump spacing, the 0.55 m branch bulges, the 1.6 m crown lobes -- is form, it
casts real shadow, and `geometry_relief_report` will read it at m well over the
bands. That is reported, not hidden: section 15 prints the dihedral spectrum and
names which bands are form and which are surface. What the law governs here is
every SHADER bump and the surface texture OF a spray or of the bark, and those
are all in-band above.

LAW 3 -- A RELIEF BUDGET IS MEANINGLESS WITHOUT A PIXEL FOOTPRINT.  The circuit
surface shipped 20 procedural layers, 8 above the resolvable band and 9 below,
and read as untextured (R2-1031..1037). At the stated 14.0 m one pixel is
3.75 mm and the gate's decisive r1/r2 bands are 11.3 and 22.5 mm:

    lambda        px at 14.0 m   px at 4.577 m   verdict at 14.0 m
    2.5 mm            0.67           2.04        BELOW the band -- carried for
                                                 the close framing only, stated
    3.5 mm            0.93           2.85        below at 14 m, in r1 at 4.6 m
    7   mm            1.87           5.71        r1
    14  mm            3.73          11.42        r1 CENTRE  <- the load-bearer
    22  mm            5.87          17.94        r2
    30  mm            8.00          24.47        r2
    55  mm           14.67          44.86        r4
    70  mm           18.67          57.10        r4-r8

Nothing in this module is authored below 2.5 mm, and the two stages under a
pixel at 14 m are declared as such rather than counted as texture.

VARIETY -- THE RED LINE, AND WHY THIS ITEM IS THE ONE THAT GETS CHECKED
=======================================================================
"i dont want repeat stuff aka one tree spammed 100 times." A columnar tree is
the easiest form in the whole campaign to spam convincingly, because near-
identical fastigiate columns are exactly what the eye forgives at distance.

`item_gate` has two paths and they are 20x apart (R2-1381). The STRONG one --
realized geometry-nodes instances walked through `depsgraph.object_instances` --
demands `distinct_sources >= max(8, min(40, sqrt(realized)))`, the same again in
`distinct_shapes`, and both commonest shares <= 25 %. At 1,400 that is 37.
The WEAK one, taken by any item that emits plain objects, demands
`distinct_topologies >= 2`.

This module emits so the STRONG path applies, and does not pad the count:
**44 independently sampled source trees**, no two sharing a height, a crown
profile, an age, a lean, a wind set, a splay, a gap pattern or a leader count.
`distinct_shapes` exists because `spectator_seated` shipped 420 source
datablocks holding 6 poses; a relabelled column would be caught by it, so the
44 differ in `_shape_signature`'s own terms -- vertex count, polygon count, and
bbox to 10 mm -- by construction, and section 15 measures that rather than
asserting it.

Transform randomisation is NOT variation and is not counted as such. The
instancer's yaw and 0.92-1.08 scale are on top of 44 distinct meshes, not
instead of them.

TRIANGLES
=========
The rejected crowd measured 390 tris/person. This is a 12 m tree at 3.75 mm/px.
Per source tree, at LOD 0, the budget is spent where the camera can see it:

    foliage lobes   ~1,200 sprays        ~144,000 quads
    sprig fringe    ~2,400 sprigs         ~19,000 quads
    trunk + flare                          ~5,600 quads
    branches        70-140                ~10,000 quads
    cones           40-160                 ~3,800 quads
    dead twigs      60-200                 ~2,000 quads
                                       ~185,000 quads = ~370,000 triangles

QUADS, NOT TRIANGLES, AND THAT IS A GATE DECISION AS WELL AS A MESH ONE. A quad
grid carries the same triangles with a third of the edges, and `edge_stats_m`
walks every edge of every selected object in a Python loop. 44 sources at
370 k tris is ~16 M triangles and ~8 M edges; the same geometry emitted as
triangles would be ~24 M edges and would put the gate's own instrument into
swap on an 11 GB box.

BUILT BY HAND
=============
Law 8. Zero image textures, zero downloaded meshes, zero scanned bark, zero
AI-generated anything. `K.assert_no_external_assets()` runs before any GPU job
is queued and the gate checks it again.
"""

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
except ImportError:
    bpy = None
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                            # noqa: E402
import world_contract as C                                     # noqa: E402

ITEM = "tree_italian_cypress"
COLL = "W_Item_TreeItalianCypress"
LIB_COLL = COLL + "/Library"
PFX = "TIC_"

NT = K.NT
log = K.log


# ==============================================================================
# 1.  THE FRAMING.  Stated, sourced, and carrying its own caveat.
# ==============================================================================

#: The distance this module is gated at.  See the header: it is the manifest's
#: own `nearest_camera_m` for every other PADDOCK tree, this item is declared
#: "14 % of the paddock mix", and it is 1.43x closer than this item's own
#: manifest figure of 20.0 m -- which would have put the 5 mm silhouette bar at
#: 0.93 px and scoped check 8 OUT.
STATED_AT_M = 14.0
#: `docs/screen_presence.json` `measured.min_depth_m`.  A HOST bound: this
#: item's 93 hosts are shrubs, saplings and ferns, and all five tree species
#: report this identical figure.  Gated at as a SECOND run, reported as a host
#: bound, never quoted as this item's framing.
HOST_BOUND_M = 4.577
#: The range the geometry is built to serve.  6 m is where a spray's own
#: branchlet ridging (30 mm) reaches 8 px and the mesh is doing all the work;
#: 45 m is where the crown lobes (0.18 m) fall to 2 px and LOD 1 takes over.
BUILT_FOR_M = (6.0, 45.0)
LENS_MM = 35.0

PX_PER_M = K.px_per_m(STATED_AT_M, LENS_MM)          # 266.67
MM_PER_PX = K.mm_per_px(STATED_AT_M, LENS_MM)        # 3.750
PX_PER_M_HOST = K.px_per_m(HOST_BOUND_M, LENS_MM)    # 815.67

#: `docs/item_manifest.json`.  Declared, not believed -- see the header.
DECLARED_INSTANCES = 1400
DECLARED_HEIGHT_M = 12.0
MANIFEST_NEAREST_M = 20.0
MANIFEST_HERO = False
#: measured.peak_unocc_sharp_px_4k, frame-capped, HOST bound
MEASURED_PEAK_PX = 2160.0
MEASURED_FRAMES_300PX = 766

#: 44, not 37.  The bar at 1,400 realized instances is
#: `max(8, min(40, int(sqrt(1400)))) = 37`; 44 clears it with the test scene's
#: 1,356 realized (bar 36) and with the film's full 1,400 (bar 37), and leaves
#: room for a source that happens not to be drawn.
N_SOURCES = 44
#: The film's declared population.  The test scene stands `N_SOURCES` of them as
#: REAL objects, so the gate can measure their meshes, and instances the rest.
N_PLAN = DECLARED_INSTANCES

SEED = 0x0C1F                                          # "cypress"


# ==============================================================================
# 2.  THE SPECIES.  Cupressus sempervirens 'Stricta', measured against the car.
# ==============================================================================
# Law 9: scale against the measured car -- 5.698 x 2.005 m, 0.340 m ride height
# -- not against intuition.  A 12 m cypress is 2.11 car-lengths tall and its
# crown is 0.60-0.75 of the car's WIDTH.  That ratio is what makes a paddock
# read as a paddock: these are narrow.
CAR_LEN_M = 5.698
CAR_W_M = 2.005

#: Height range in a planted row.  The manifest's `typical_height_m` is 12.0;
#: a real avenue is not 1,400 copies of the typical one.
H_RANGE = (8.4, 15.6)
#: Crown half-width as a fraction of height.  'Stricta' at 12 m is 1.0-1.6 m
#: across, i.e. r = 0.50-0.80 m -> 0.042-0.067 of the height.  The upper end is
#: an old, splayed specimen; the lower end is a young nursery-tight one.
SLENDER = (0.040, 0.070)
#: Clean bole below the foliage.  Cypress carries foliage nearly to the ground
#: when young; older ones and anything grazed or strimmed show a stem.
BOLE = (0.12, 1.35)
#: Trunk radius at the base, as a fraction of height.
TRUNK_R = (0.0068, 0.0125)

#: The relief bands every geometric amplitude in this file is derived from.
#: NOT ONE MILLIMETRE IS TYPED -- `K.relief_amplitude_for(m, lambda)` converts,
#: and it reads `world_contract.SUN_ELEV_DEG`, so if the sun moves these move.
M_RIDGE = 5.00          # hard_feature  1.50-6.00 : a branchlet against its
#                                                   neighbour IS an edge
LAM_RIDGE = 0.030
M_SPRAY = 1.15          # geometry_fold 0.60-1.40
LAM_SPRAY = 0.070
M_FLUTE = 1.20          # geometry_fold : the trunk's own vertical fluting
LAM_FLUTE = 0.055
M_FISSURE = 3.20        # hard_feature  : a bark fissure is a groove, not a wave
LAM_FISSURE = 0.026

#: Shader stages.  isotropic_micro 0.12-0.45, isotropic_macro 0.35-0.95.
M_GROOVE, LAM_GROOVE = 0.40, 0.014     # inter-branchlet groove; r1 centre
M_LEAFRANK, LAM_LEAFRANK = 0.28, 0.0025  # the accepted cloth value; sub-px at
#                                          14 m and stated as such
M_FIBRE, LAM_FIBRE = 0.30, 0.0035
M_PLATE, LAM_PLATE = 0.62, 0.022
M_CONESCALE, LAM_CONESCALE = 0.55, 0.007


def relief_stages():
    """Every stage in this module, as (name, wavelength_m, amplitude_mm).

    Fed to `K.relief_budget` by `selftest`, and the amplitudes are the ones the
    geometry actually uses -- read back from the same helper that built them,
    not retyped.
    """
    def amp(m, lam):
        return K.relief_amplitude_for(m, wavelength_m=lam)
    return [
        ("geo_branchlet_ridge", LAM_RIDGE, amp(M_RIDGE, LAM_RIDGE), "hard_feature"),
        ("geo_spray_surface", LAM_SPRAY, amp(M_SPRAY, LAM_SPRAY), "geometry_fold"),
        ("geo_trunk_flute", LAM_FLUTE, amp(M_FLUTE, LAM_FLUTE), "geometry_fold"),
        ("geo_bark_fissure", LAM_FISSURE, amp(M_FISSURE, LAM_FISSURE), "hard_feature"),
        ("shd_branchlet_groove", LAM_GROOVE, amp(M_GROOVE, LAM_GROOVE), "isotropic_micro"),
        ("shd_leaf_rank", LAM_LEAFRANK, amp(M_LEAFRANK, LAM_LEAFRANK), "isotropic_micro"),
        ("shd_bark_fibre", LAM_FIBRE, amp(M_FIBRE, LAM_FIBRE), "isotropic_micro"),
        ("shd_bark_plate", LAM_PLATE, amp(M_PLATE, LAM_PLATE), "isotropic_macro"),
        ("shd_cone_scale", LAM_CONESCALE, amp(M_CONESCALE, LAM_CONESCALE), "isotropic_macro"),
    ]


def pixel_footprint(distances=(STATED_AT_M, HOST_BOUND_M, MANIFEST_NEAREST_M)):
    """Law 3.  Every stated wavelength, in PIXELS, at every framing on the table.

    A relief budget with no pixel footprint is what R2-1031..1037 was: twenty
    procedural layers, eight above the resolvable band and nine below.
    """
    rows = []
    for name, lam, amp_mm, band in relief_stages():
        r = {"stage": name, "wavelength_mm": lam * 1000.0,
             "amplitude_mm_pp": amp_mm, "band": band}
        for d in distances:
            r["px_at_%.3fm" % d] = lam * K.px_per_m(d, LENS_MM)
        rows.append(r)
    return rows


# ==============================================================================
# 3.  NUMPY GEOMETRY PRIMITIVES.  Everything is built in batches; a Python loop
#     over 1,200 sprays x 44 trees is 53,000 iterations of mesh assembly and it
#     is the difference between a two-minute build and a two-hour one.
# ==============================================================================

def _grid_quads(nrow, ncol, base=0):
    """Quad indices for an (nrow x ncol) vertex grid, row-major. -> (Q, 4)."""
    idx = np.arange(nrow * ncol).reshape(nrow, ncol) + base
    return np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                     idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], axis=1)


def _batch_grid_quads(nb, nrow, ncol):
    """The same, for `nb` independent grids laid end to end. -> (nb*Q, 4)."""
    q = _grid_quads(nrow, ncol)
    off = (np.arange(nb) * (nrow * ncol))[:, None, None]
    return (q[None, :, :] + off).reshape(-1, 4)


def _batch_tube_quads(nb, nseg, nside):
    """Closed-tube quads for `nb` tubes of (nseg+1) rings x nside sides."""
    idx = np.arange((nseg + 1) * nside).reshape(nseg + 1, nside)
    j2 = np.roll(idx, -1, axis=1)
    q = np.stack([idx[:-1].ravel(), j2[:-1].ravel(),
                  j2[1:].ravel(), idx[1:].ravel()], axis=1)
    off = (np.arange(nb) * ((nseg + 1) * nside))[:, None, None]
    return (q[None, :, :] + off).reshape(-1, 4)


def _frames(d):
    """Orthonormal (u, v) perpendicular to each direction `d`. -> (N,3),(N,3).

    The reference axis is chosen per row so a direction parallel to +Z does not
    produce a zero cross product -- which on a fastigiate tree, where nearly
    every branch points up, is the common case rather than the corner one.
    """
    d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
    ref = np.tile(np.array([0.0, 0.0, 1.0]), (len(d), 1))
    steep = np.abs(d[:, 2]) > 0.9
    ref[steep] = np.array([1.0, 0.0, 0.0])
    u = np.cross(ref, d)
    u /= np.maximum(np.linalg.norm(u, axis=1, keepdims=True), 1e-12)
    v = np.cross(d, u)
    return u, v


def _harm(t, phi, terms):
    """Sum of phase-locked harmonics: quasi-random, but every term is a STATED
    amplitude at a STATED wavelength, which is what the relief law needs.

    `terms` is a sequence of (amplitude, vertical_wavelength_m, azimuthal_order,
    phase).  Integer azimuthal orders keep it continuous around the trunk, which
    an fbm of (x, y) is not.
    """
    out = np.zeros(np.broadcast(t, phi).shape, dtype=np.float64)
    for a, lz, kp, ps in terms:
        out = out + a * np.sin(2.0 * np.pi * t / lz + kp * phi + ps)
    return out


def _ridged(x):
    """1 - |2x-1| on a [0,1] input: crests sharp, valleys flat.

    A plain sinusoid makes a wobbly cylinder. Foliage is lobed -- convex clumps
    with creases between them -- and the ridged transform is the difference
    between the two reads.
    """
    return 1.0 - np.abs(2.0 * np.clip(x, 0.0, 1.0) - 1.0)


# ==============================================================================
# 4.  ONE TREE'S SPEC.  This is the variation model, and it is the whole of the
#     red-line defence: 44 of these, no two alike in any axis.
# ==============================================================================

def tree_spec(i, seed=SEED):
    """Everything that makes source tree `i` a different tree, not a transform.

    Deterministic in `i`, through `itemkit.Rng` (numpy PCG64 seeded by a mixed
    key) and `itemkit.hash01` (FNV-1a WITH the murmur3 finaliser -- the naive
    form collapses seven properties onto one value, which is the project's named
    failure arriving through a hash function).
    """
    r = K.Rng(seed, i * 7919 + 13)
    age = float(np.clip(r.n(0.5, 0.27), 0.02, 0.99))
    h = float(H_RANGE[0] + (H_RANGE[1] - H_RANGE[0])
              * np.clip(0.30 * age + 0.70 * r.u(), 0.0, 1.0))
    slender = SLENDER[0] + (SLENDER[1] - SLENDER[0]) * (0.55 * age + 0.45 * r.u())
    rmax = h * slender

    # --- the four departure mechanisms -----------------------------------
    # (2) light and wind.  A first harmonic (the tree is fatter on the side that
    # gets the light) and a second (the wind combs it into an oval).
    light_az = r.u(0.0, 2.0 * math.pi)
    wind_az = r.u(0.0, 2.0 * math.pi)
    a_light = r.u(0.07, 0.22) * (0.55 + 0.45 * age)
    a_wind = r.u(0.04, 0.17)

    # (3) splay.  Older specimens open at the top; young ones are a spire.
    splay = 0.0 if age < 0.42 else float(np.clip((age - 0.42) / 0.58, 0, 1))
    splay_z0 = r.u(0.70, 0.88)                     # fraction of height
    splay_out = splay * r.u(0.14, 0.62)            # metres, at the very top
    splay_droop = splay * r.u(6.0, 34.0)           # degrees below horizontal
    n_leader = 1 if age < 0.5 else int(r.i(1, 4))

    # (4) gaps.
    n_gap = int(r.i(0, 3)) if age > 0.3 else int(r.i(0, 1))
    gaps = [dict(z=r.u(0.12, 0.94), az=r.u(0.0, 2.0 * math.pi),
                 dz=r.u(0.030, 0.100), daz=r.u(0.28, 0.95),
                 depth=r.u(0.20, 0.45)) for _ in range(n_gap)]

    # (1) is the lobe field itself; its statistics live here.
    #     Three envelope octaves. The 0.19 m one is the one that survives the
    #     check's own 0.375 m quadratic window at the stated framing.
    ph = [r.u(0.0, 2.0 * math.pi) for _ in range(12)]
    env_terms = [
        (r.u(0.06, 0.115), r.u(1.35, 2.05), int(r.i(1, 2)), ph[0]),
        (r.u(0.05, 0.095), r.u(1.05, 1.60), int(r.i(2, 3)), ph[1]),
        (r.u(0.045, 0.090), r.u(0.44, 0.70), int(r.i(3, 5)), ph[2]),
        (r.u(0.040, 0.080), r.u(0.36, 0.58), int(r.i(4, 7)), ph[3]),
        (r.u(0.032, 0.068), r.u(0.155, 0.235), int(r.i(6, 11)), ph[4]),
        (r.u(0.028, 0.060), r.u(0.135, 0.205), int(r.i(8, 14)), ph[5]),
    ]

    lean = math.radians(r.u(0.4, 4.6))
    lean_az = r.u(0.0, 2.0 * math.pi)
    bow = r.u(-0.9, 0.9)                            # S-bend of the leader

    bole = BOLE[0] + (BOLE[1] - BOLE[0]) * (0.6 * age + 0.4 * r.u())
    trunk_r = h * (TRUNK_R[0] + (TRUNK_R[1] - TRUNK_R[0]) * (0.7 * age + 0.3 * r.u()))

    return dict(
        index=int(i), seed=int(r.seed), age=age, h=h, rmax=rmax,
        slender=slender, bole=min(bole, 0.16 * h),
        trunk_r=trunk_r,
        light_az=light_az, wind_az=wind_az, a_light=a_light, a_wind=a_wind,
        splay=splay, splay_z0=splay_z0, splay_out=splay_out,
        splay_droop=splay_droop, n_leader=n_leader,
        gaps=gaps, env_terms=env_terms,
        lean=lean, lean_az=lean_az, bow=bow,
        # foliage character
        n_lobe=int(r.i(880, 1450)),
        lobe_len=(r.u(0.16, 0.24), r.u(0.34, 0.58)),
        lobe_wid=(r.u(0.42, 0.55), r.u(0.62, 0.86)),      # of length
        finger=r.u(0.30, 0.58),                            # boundary raggedness
        n_finger=(int(r.i(5, 8)), int(r.i(11, 17))),
        beta=(math.radians(r.u(38.0, 52.0)), math.radians(r.u(62.0, 79.0))),
        # colour / condition
        flush=r.u(0.10, 0.55),          # bright new growth at the tips
        dead=r.u(0.02, 0.22) * (0.4 + 0.9 * age),
        bleach=r.u(0.05, 0.40),         # sun-bleaching of the crown top
        dust=r.u(0.02, 0.30),           # paddock dust on the lee side
        n_cone=int(r.i(0, 170) * (0.25 + 0.9 * age)),
        n_twig=int(r.i(45, 210)),
        hue=r.u(-1.0, 1.0),             # blue-green .. yellow-green
    )


def crown_radius(sp, t, phi):
    """THE ENVELOPE. `t` is height fraction 0..1, `phi` azimuth. -> metres.

    This is the function check 8 is really asking about, so read it as the
    answer to "what is NOT a quadratic here":

      * `prof`  IS analytic -- a columnar profile, and on its own it would fit a
                quadratic to a fraction of a pixel. Everything after it is the
                departure.
      * `asym`  first + second azimuthal harmonic. Makes the left and right
                profiles of ONE tree different curves.
      * `_harm` six envelope terms, vertical wavelengths 0.135-2.05 m. The four
                shortest are inside the check's 0.375 m refit window at the
                stated framing and are what survives the quadratic.
      * gaps    localised recesses, 20-45 % deep.
      * splay   the top opens outward. Above `splay_z0` a quadratic in y cannot
                follow the profile at all, which is the point.
    """
    t = np.clip(np.asarray(t, float), 0.0, 1.0)
    phi = np.asarray(phi, float)
    b = sp["bole"] / sp["h"]
    u = np.clip((t - b) / max(1.0 - b, 1e-6), 0.0, 1.0)
    # columnar: full width from ~12 % to ~78 % of the foliated length, a soft
    # shoulder below and a spire above.
    prof = (np.clip(u / 0.13, 0.0, 1.0) ** 0.62) * ((1.0 - u) ** 0.42) / 0.5 ** 0.42
    prof = np.clip(prof, 0.0, 1.25)

    asym = (1.0 + sp["a_light"] * np.cos(phi - sp["light_az"])
            + sp["a_wind"] * np.cos(2.0 * (phi - sp["wind_az"])))
    lumps = 1.0 + _harm(t * sp["h"], phi, sp["env_terms"])

    r = sp["rmax"] * prof * asym * lumps

    for g in sp["gaps"]:
        dz = (t - g["z"]) / g["dz"]
        da = np.arctan2(np.sin(phi - g["az"]), np.cos(phi - g["az"])) / g["daz"]
        r = r * (1.0 - g["depth"] * np.exp(-(dz * dz + da * da)))

    if sp["splay_out"] > 0.0:
        s = np.clip((t - sp["splay_z0"]) / max(1.0 - sp["splay_z0"], 1e-6), 0.0, 1.0)
        # the candelabra: n_leader lobes of extra reach, not a uniform flare
        lobing = 1.0 + 0.55 * np.cos(sp["n_leader"] * (phi - sp["light_az"]))
        r = r + sp["splay_out"] * (s ** 1.6) * lobing
    return np.maximum(r, 0.004)


def axis_offset(sp, t):
    """Lean and bow of the leader. -> (N,2) horizontal offset in metres."""
    t = np.asarray(t, float)
    d = sp["h"] * (np.tan(sp["lean"]) * t
                   + 0.035 * sp["bow"] * np.sin(np.pi * t) * np.sin(2.4 * t))
    return np.stack([d * math.cos(sp["lean_az"]), d * math.sin(sp["lean_az"])],
                    axis=-1)


# ==============================================================================
# 5.  THE FOLIAGE SPRAY.  One ragged-edged, keeled, branchlet-ridged sheet.
# ==============================================================================
# A spray is NOT a card and it is NOT a displaced sphere. It is the unit the
# outline is made of, so its BOUNDARY is the thing that gets the budget:
#
#   * the half-width across the spray is modulated by `_ridged` at 5-17 fingers
#     along its length, at up to 58 % -- so the edge is a fringe of tapering
#     tips, not a curve. That is the departure at the finest scale the camera
#     resolves.
#   * the cross-section is an ARCH with `nrib` branchlet ridges on it, at
#     LAM_RIDGE with an amplitude derived from M_RIDGE in `hard_feature`.
#     Those ridges are what makes a spray read as lip and shadow at 12.5 deg
#     rather than as a green surface: a 33.6 deg face at 30 mm pitch throws a
#     real lee shadow.
#   * it droops and twists along its length, so no two are the same projection.

NS_LOBE, NT_LOBE = 12, 10          # -> 120 quads, 143 verts per spray


def spray_batch(base, direct, length, width, twist, droop, finger, nfing,
                nrib, rng, ns=NS_LOBE, nt=NT_LOBE):
    """`B` sprays at once. -> verts (B*(ns+1)*(nt+1), 3), quads, attrs dict."""
    B = len(base)
    s = np.linspace(0.0, 1.0, ns + 1)[None, :, None]        # (1, ns+1, 1)
    tt = np.linspace(-1.0, 1.0, nt + 1)[None, None, :]      # (1, 1, nt+1)

    L = length[:, None, None]
    W = width[:, None, None]

    # --- the ragged boundary -------------------------------------------
    # `_ridged` of a phase ramp gives sharp-crested fingers; the crest sits at
    # the finger tip and the valley between two fingers cuts back into the
    # spray. Two different finger counts on the two sides, so a spray is not
    # symmetric about its own axis.
    ph_l = rng.arr(B)[:, None, None] * 2.0 * math.pi
    ph_r = rng.arr(B)[:, None, None] * 2.0 * math.pi
    nf = nfing[:, None, None].astype(float)
    fr = finger[:, None, None]
    fing_l = 1.0 - fr * (1.0 - _ridged((s * nf + ph_l / (2 * math.pi)) % 1.0))
    fing_r = 1.0 - fr * (1.0 - _ridged((s * nf * 1.17 + 0.31
                                        + ph_r / (2 * math.pi)) % 1.0))
    side = np.where(tt >= 0.0, fing_r, fing_l)

    # spray outline along its length: fat in the middle third, pointed at the
    # tip, narrow at the stalk.
    prof = np.sin(np.pi * np.clip(s, 0, 1) ** 0.68) ** 0.78
    half = W * prof * side

    # --- the arched, ridged cross-section --------------------------------
    # arch height is a fraction of the half-width; the ridges are ON the arch.
    arch = 0.34 * half * (1.0 - tt * tt)
    amp_ridge = K.relief_amplitude_for(M_RIDGE, wavelength_m=LAM_RIDGE) * 1e-3
    nrb = nrib[:, None, None].astype(float)
    ridge = 0.5 * amp_ridge * np.cos(nrb * np.pi * tt + 2.2 * s)
    # ... and the spray's own surface undulation, one octave, in geometry_fold
    amp_surf = K.relief_amplitude_for(M_SPRAY, wavelength_m=LAM_SPRAY) * 1e-3
    ph_s = rng.arr(B)[:, None, None] * 6.283
    surf = 0.5 * amp_surf * np.sin(2.0 * math.pi * s * L / LAM_SPRAY + ph_s
                                   + 1.7 * tt)

    # --- axes ------------------------------------------------------------
    u, v = _frames(direct)
    tw = twist[:, None, None]
    dr = droop[:, None, None]
    # twist about the spray axis grows along its length; droop bends it down
    ang = tw * s
    ca, sa = np.cos(ang), np.sin(ang)
    across_u = ca
    across_v = sa
    # the spray sags: the axis falls away as s^1.7
    sag = dr * (s ** 1.7) * L

    along = (s * L)
    lat = half * tt
    up = arch + ridge + surf

    U = u[:, None, :]
    V = v[:, None, :]
    D = (direct / np.maximum(np.linalg.norm(direct, axis=1, keepdims=True),
                             1e-12))[:, None, :]
    Zc = np.array([0.0, 0.0, 1.0])[None, None, :]

    P = (base[:, None, :]
         + D * along.reshape(B, ns + 1, 1)
         - Zc * sag.reshape(B, ns + 1, 1))
    P = P[:, :, None, :] + (
        (U[:, :, None, :] * (across_u * lat)[..., None]
         + V[:, :, None, :] * (across_v * lat)[..., None])
        + (U[:, :, None, :] * (-across_v * up)[..., None]
           + V[:, :, None, :] * (across_u * up)[..., None]))

    verts = P.reshape(-1, 3)
    quads = _batch_grid_quads(B, ns + 1, nt + 1)
    attrs = {
        "tip": np.broadcast_to(s, (B, ns + 1, nt + 1)).reshape(-1).copy(),
        "edge": np.broadcast_to(np.abs(tt), (B, ns + 1, nt + 1)).reshape(-1).copy(),
    }
    return verts, quads, attrs


def sprig_batch(base, direct, length, width, rng, ns=3):
    """The fringe: single keeled branchlets, 6 quads each, that stand PROUD.

    These exist for one reason. The spray boundary is ragged but a spray is a
    connected sheet; what a real cypress also has is individual branchlet tips
    projecting past everything, and they are what makes the outline read as
    foliage rather than as a cut-out. They are kept SHORT (40-140 mm) and
    anchored inside the mass on purpose: check 8 only measures rows whose
    outline is a SINGLE UNBROKEN RUN, so a fringe of detached spikes would
    delete the very rows the check needs. Attached raggedness, not spikes.
    """
    B = len(base)
    s = np.linspace(0.0, 1.0, ns + 1)[None, :, None]
    tt = np.array([-1.0, 0.0, 1.0])[None, None, :]
    L = length[:, None, None]
    W = width[:, None, None]
    half = W * (1.0 - s) ** 0.55
    up = np.where(tt == 0.0, 0.62 * half, 0.0)
    u, v = _frames(direct)
    D = (direct / np.maximum(np.linalg.norm(direct, axis=1, keepdims=True),
                             1e-12))[:, None, :]
    U, V = u[:, None, :], v[:, None, :]
    lat = half * np.where(tt == 0.0, 0.0, tt)
    P = base[:, None, :] + D * (s * L).reshape(B, ns + 1, 1)
    P = P[:, :, None, :] + (U[:, :, None, :] * lat[..., None]
                            + V[:, :, None, :] * up[..., None])
    verts = P.reshape(-1, 3)
    quads = _batch_grid_quads(B, ns + 1, 3)
    attrs = {
        "tip": np.broadcast_to(0.45 + 0.55 * s, (B, ns + 1, 3)).reshape(-1).copy(),
        "edge": np.broadcast_to(np.abs(tt), (B, ns + 1, 3)).reshape(-1).copy(),
    }
    return verts, quads, attrs


# ==============================================================================
# 6.  WOOD.  Trunk, branches, dead twigs, cones.
# ==============================================================================

def tube_batch(centres, radii, nside):
    """Swept tubes. `centres` (B, N, 3), `radii` (B, N, nside). -> verts, quads.

    The per-side radius is what carries the FLUTING: a cypress trunk is not
    round, it is ribbed, and the ribs run up it. Making the radius a function of
    the side index is how that becomes geometry instead of a bump map.
    """
    B, N, _ = centres.shape
    d = np.diff(centres, axis=1)
    d = np.concatenate([d, d[:, -1:, :]], axis=1)
    dd = d.reshape(-1, 3)
    u, v = _frames(dd)
    u = u.reshape(B, N, 3)
    v = v.reshape(B, N, 3)
    a = np.linspace(0.0, 2.0 * np.pi, nside, endpoint=False)[None, None, :]
    P = (centres[:, :, None, :]
         + u[:, :, None, :] * (radii * np.cos(a))[..., None]
         + v[:, :, None, :] * (radii * np.sin(a))[..., None])
    return P.reshape(-1, 3), _batch_tube_quads(B, N - 1, nside)


def trunk_mesh(sp, nside=14, nseg=76):
    """The bole: sinuous, root-flared, fluted, and NOT a cone.

    The flute amplitude comes from `M_FLUTE` in `geometry_fold` and the fissure
    depth from `M_FISSURE` in `hard_feature`. A cypress trunk is also strongly
    non-circular near the ground -- the root flare is lobed -- and that lobing
    is a function of azimuth AND height, so the silhouette of the stem is not a
    straight taper either.
    """
    t = np.linspace(0.0, 1.0, nseg + 1)
    off = axis_offset(sp, t)
    z = t * sp["h"]
    centres = np.stack([off[:, 0], off[:, 1], z], axis=1)[None, :, :]

    a = np.linspace(0.0, 2.0 * np.pi, nside, endpoint=False)[None, :]
    tt = t[:, None]
    # taper: fast in the first 8 %, then a long slow run to a whip at the top
    taper = (1.0 - tt) ** 1.35 * (1.0 + 1.9 * np.exp(-tt * sp["h"] / 0.55))
    r0 = sp["trunk_r"] * taper + 0.004

    amp_fl = K.relief_amplitude_for(M_FLUTE, wavelength_m=LAM_FLUTE) * 1e-3
    amp_fi = K.relief_amplitude_for(M_FISSURE, wavelength_m=LAM_FISSURE) * 1e-3
    # flutes: nside/2 of them, twisting slowly up the stem
    flute = 0.5 * amp_fl * np.cos(7.0 * a + 2.1 * tt * sp["h"] / 1.0)
    # fissures: a sparse crease, so `_ridged` rather than a cosine -- a groove
    # that is flat between grooves, which is what bark is
    fis = -amp_fi * _ridged(((a * 11.0 / (2 * np.pi)
                              + tt * sp["h"] / LAM_FISSURE) % 1.0))
    # root flare: three or four buttresses, dying out by 0.9 m
    flare = (1.0 + 0.55 * np.cos(3.0 * a + sp["lean_az"])
             + 0.28 * np.cos(5.0 * a + 1.3)) * \
        np.exp(-tt * sp["h"] / 0.42) * sp["trunk_r"] * 0.9
    radii = (r0 + flute + fis + np.maximum(flare, 0.0))[None, :, :]
    v, q = tube_batch(centres, np.maximum(radii, 0.002), nside)
    at = {"tip": np.zeros(len(v)), "edge": np.zeros(len(v))}
    return v, q, at


def branch_mesh(sp, rng, n, nside=5, nseg=7):
    """Order-1 branches: steeply ascending, which is what makes it a column."""
    if n <= 0:
        return np.zeros((0, 3)), np.zeros((0, 4), np.int64), {}
    t0 = rng.arr(n) ** 0.85
    t0 = sp["bole"] / sp["h"] + t0 * (0.97 - sp["bole"] / sp["h"])
    phi = rng.arr(n) * 2.0 * math.pi + 2.399963 * np.arange(n)
    phi = np.mod(phi, 2.0 * math.pi)
    off = axis_offset(sp, t0)
    z0 = t0 * sp["h"]
    Rt = crown_radius(sp, t0, phi)
    # steep near the middle of the column, shallower at the splayed top
    beta = sp["beta"][1] - (sp["beta"][1] - sp["beta"][0]) * np.clip(
        (t0 - sp["splay_z0"]) / max(1.0 - sp["splay_z0"], 1e-6), 0.0, 1.0) \
        * (0.35 + 0.65 * sp["splay"])
    L = Rt * (0.85 + 0.35 * rng.arr(n)) / np.maximum(np.cos(beta), 0.15)
    s = np.linspace(0.0, 1.0, nseg + 1)[None, :]
    # a branch curves upward as it goes out
    curve = 0.22 * (s ** 2)
    dx = np.cos(phi)[:, None] * np.cos(beta)[:, None] * L[:, None] * s
    dy = np.sin(phi)[:, None] * np.cos(beta)[:, None] * L[:, None] * s
    dz = (np.sin(beta)[:, None] + curve) * L[:, None] * s
    centres = np.stack([off[:, 0:1] + dx, off[:, 1:2] + dy, z0[:, None] + dz],
                       axis=2)
    rb = (0.055 * L)[:, None, None] * (1.0 - s)[:, :, None] ** 0.8 + 0.0016
    rb = np.repeat(rb, nside, axis=2)
    a = np.linspace(0.0, 2.0 * np.pi, nside, endpoint=False)[None, None, :]
    rb = rb * (1.0 + 0.16 * np.cos(3.0 * a))
    v, q = tube_batch(centres, rb, nside)
    at = {"tip": np.zeros(len(v)), "edge": np.zeros(len(v))}
    return v, q, at


def cone_mesh(sp, rng, n, nu=8, nv=5):
    """Seed cones: 25-40 mm woody globes with peltate shield scales.

    At the stated framing a cone is 8 px across and its shields are 2 px, which
    is exactly the band the r1 contrast check reads. They also cluster -- cones
    come in bunches on 2-4 year wood -- so they are placed in groups rather than
    scattered, which is what makes them read as a plant's habit rather than as
    dressing.
    """
    if n <= 0:
        return np.zeros((0, 3)), np.zeros((0, 4), np.int64), {}
    ng = max(1, n // 4)
    gt = 0.35 + 0.6 * rng.arr(ng)
    ga = rng.arr(ng) * 2 * math.pi
    idx = rng.r.integers(0, ng, n)
    t = np.clip(gt[idx] + 0.03 * (rng.arr(n) - 0.5), 0.05, 0.98)
    phi = ga[idx] + 0.5 * (rng.arr(n) - 0.5)
    R = crown_radius(sp, t, phi) * (0.72 + 0.26 * rng.arr(n))
    off = axis_offset(sp, t)
    cx = off[:, 0] + R * np.cos(phi)
    cy = off[:, 1] + R * np.sin(phi)
    cz = t * sp["h"]
    rad = (0.0125 + 0.0075 * rng.arr(n))

    th = np.linspace(0.0, np.pi, nv + 1)[None, :, None]
    ph = np.linspace(0.0, 2 * np.pi, nu, endpoint=False)[None, None, :]
    amp = K.relief_amplitude_for(M_CONESCALE, wavelength_m=LAM_CONESCALE) * 1e-3
    # peltate shields: a raised polygonal boss per scale, with a central umbo
    shield = 1.0 + (amp / np.maximum(rad[:, None, None], 1e-4)) * (
        _ridged(((ph / (2 * np.pi) * nu) % 1.0)) - 0.5) * 2.0
    rr = rad[:, None, None] * shield * (1.0 - 0.10 * np.cos(2 * th))
    P = np.stack([cx[:, None, None] + rr * np.sin(th) * np.cos(ph),
                  cy[:, None, None] + rr * np.sin(th) * np.sin(ph),
                  cz[:, None, None] + rr * np.cos(th) * 1.06], axis=3)
    v = P.reshape(-1, 3)
    q = _batch_tube_quads(n, nv, nu)
    at = {"tip": np.zeros(len(v)), "edge": np.full(len(v), 2.0)}   # 2 = cone
    return v, q, at


def deadtwig_mesh(sp, rng, n, nside=4, nseg=4):
    """Bare interior branchlets poking out of the mass.

    A real cypress sheds its inner foliage and the dead stubs stay. They are a
    fifth of a millimetre of thought and they are the difference between a
    plant and a topiary: they break the envelope with something that is NOT
    green, so the eye reads depth.
    """
    if n <= 0:
        return np.zeros((0, 3)), np.zeros((0, 4), np.int64), {}
    t = 0.06 + 0.86 * rng.arr(n) ** 1.2
    phi = rng.arr(n) * 2 * math.pi
    R = crown_radius(sp, t, phi)
    off = axis_offset(sp, t)
    base = np.stack([off[:, 0] + R * np.cos(phi) * (0.35 + 0.4 * rng.arr(n)),
                     off[:, 1] + R * np.sin(phi) * (0.35 + 0.4 * rng.arr(n)),
                     t * sp["h"]], axis=1)
    beta = 0.45 + 0.8 * rng.arr(n)
    d = np.stack([np.cos(phi) * np.cos(beta), np.sin(phi) * np.cos(beta),
                  np.sin(beta)], axis=1)
    L = (R * (0.55 + 0.85 * rng.arr(n)))[:, None]
    s = np.linspace(0.0, 1.0, nseg + 1)[None, :, None]
    centres = base[:, None, :] + d[:, None, :] * (s * L[:, None, :])
    rr = (0.0035 * (1.0 - s) ** 0.7 + 0.0008)
    rr = np.repeat(rr, nside, axis=2)
    v, q = tube_batch(centres, rr, nside)
    at = {"tip": np.zeros(len(v)), "edge": np.full(len(v), 3.0)}   # 3 = dead
    return v, q, at


# ==============================================================================
# 7.  ONE SOURCE TREE, ASSEMBLED.
# ==============================================================================

#: LOD 0 is the only one the gate ever sees, and it is the one the film uses
#: inside 45 m. 1 and 2 exist because 1,400 instances of LOD 0 is 520 M
#: triangles and the world module needs a ladder; they are declared in the
#: interface file and are NOT what this module is judged on.
LOD_LOBE = (1.00, 0.42, 0.14)
LOD_GRID = ((12, 10), (7, 6), (4, 4))
LOD_SPRIG = (1.00, 0.30, 0.0)


def tree_arrays(sp, lod=0):
    """(verts, quads, attrs) for one source tree, base at the local origin.

    NOT RECENTRED, and that is a deliberate, stated deviation from Law 9's
    "recentre on emit". The law exists because a material addressed at
    |P| ~ 1000 m loses float precision and blotches; a tree emitted in its OWN
    frame with the base at the origin has |P| <= 16 m, which satisfies the
    reason for the law completely. Recentring to the BBOX CENTRE would put the
    origin at a different height in every one of the 44 sources, and the
    instancer picks a source at random per point -- so every instanced tree
    would float or sink by the difference between its own half-height and the
    one the point was placed for. The law's purpose is kept; its side effect is
    not paid for.
    """
    rng = K.Rng(sp["seed"], 977)
    nl = int(sp["n_lobe"] * LOD_LOBE[lod])
    ns, nt = LOD_GRID[lod]
    V, Q, A = [], [], []
    nv = 0

    def add(v, q, at):
        nonlocal nv
        if not len(v):
            return
        V.append(v)
        Q.append(q + nv)
        n = len(v)
        A.append({k: np.asarray(at.get(k, np.zeros(n)), float)
                  for k in ("tip", "edge")})
        nv += n

    add(*trunk_mesh(sp))
    add(*branch_mesh(sp, rng, int(70 + 70 * sp["age"])))

    # --- the foliage lobes ------------------------------------------------
    if nl > 0:
        # stratified up the column so the density is even and the sample is not
        # a Poisson clump -- a real cypress is uniformly dense, its LUMPS come
        # from the envelope, not from where the sprays happened to land.
        u = (np.arange(nl) + rng.arr(nl)) / nl
        b = sp["bole"] / sp["h"]
        t = b + u * (0.995 - b)
        phi = np.mod(2.399963 * np.arange(nl) + rng.arr(nl) * 0.9, 2 * math.pi)
        R = crown_radius(sp, t, phi)
        # depth: outer sprays set the outline, inner ones fill the mass
        depth = rng.arr(nl) ** 1.7
        rb = R * (0.30 + 0.66 * (1.0 - depth))
        off = axis_offset(sp, t)
        base = np.stack([off[:, 0] + rb * np.cos(phi),
                         off[:, 1] + rb * np.sin(phi),
                         t * sp["h"]], axis=1)
        # direction: out and steeply up, flattening (and drooping) in the splay
        sfr = np.clip((t - sp["splay_z0"]) / max(1.0 - sp["splay_z0"], 1e-6),
                      0.0, 1.0)
        beta = (sp["beta"][1]
                - (sp["beta"][1] - sp["beta"][0]) * rng.arr(nl)
                - sfr * sp["splay"] * math.radians(sp["splay_droop"]))
        jaz = phi + (rng.arr(nl) - 0.5) * 0.55
        direct = np.stack([np.cos(jaz) * np.cos(beta),
                           np.sin(jaz) * np.cos(beta),
                           np.sin(beta)], axis=1)
        lmin, lmax = sp["lobe_len"]
        length = (lmin + (lmax - lmin) * rng.arr(nl)) * (0.6 + 0.8 * (1.0 - depth))
        # 6 % of sprays reach much further -- the outliers that make an outline
        # a fringe rather than a curve. Kept attached and kept modest.
        outl = rng.arr(nl) < 0.06
        length = np.where(outl, length * (1.35 + 0.55 * rng.arr(nl)), length)
        wmin, wmax = sp["lobe_wid"]
        width = length * (wmin + (wmax - wmin) * rng.arr(nl)) * 0.5
        twist = (rng.arr(nl) - 0.5) * 2.2
        droop = 0.10 + 0.30 * rng.arr(nl) + 0.45 * sfr * sp["splay"]
        finger = np.full(nl, sp["finger"]) * (0.7 + 0.6 * rng.arr(nl))
        nf0, nf1 = sp["n_finger"]
        nfing = rng.r.integers(nf0, nf1 + 1, nl)
        nrib = rng.r.integers(3, 7, nl)
        v, q, at = spray_batch(base, direct, length, width, twist, droop,
                               finger, nfing, nrib, rng, ns=ns, nt=nt)
        at["edge"] = at["edge"] + 0.0
        add(v, q, at)

    # --- the sprig fringe --------------------------------------------------
    nsp = int(2400 * LOD_SPRIG[lod] * (0.7 + 0.6 * sp["age"]))
    if nsp > 0:
        t = 0.02 + 0.97 * rng.arr(nsp) ** 0.92
        phi = rng.arr(nsp) * 2 * math.pi
        R = crown_radius(sp, t, phi)
        off = axis_offset(sp, t)
        base = np.stack([off[:, 0] + R * 0.86 * np.cos(phi),
                         off[:, 1] + R * 0.86 * np.sin(phi),
                         t * sp["h"]], axis=1)
        beta = 0.55 + 0.85 * rng.arr(nsp)
        d = np.stack([np.cos(phi) * np.cos(beta), np.sin(phi) * np.cos(beta),
                      np.sin(beta)], axis=1)
        L = 0.040 + 0.100 * rng.arr(nsp)
        W = 0.004 + 0.008 * rng.arr(nsp)
        add(*sprig_batch(base, d, L, W, rng))

    add(*cone_mesh(sp, rng, int(sp["n_cone"] * (1.0 if lod == 0 else 0.4))))
    add(*deadtwig_mesh(sp, rng, int(sp["n_twig"] * (1.0 if lod == 0 else 0.35))))

    verts = np.concatenate(V)
    quads = np.concatenate(Q)
    attrs = {k: np.concatenate([a[k] for a in A]) for k in ("tip", "edge")}
    # up: height fraction, for the shader's crown bleaching
    attrs["up"] = np.clip(verts[:, 2] / sp["h"], 0.0, 1.0)
    # rad: distance from the leader axis, normalised -- 0 deep inside the mass,
    # 1 at the envelope. The interior of a conifer is dark and brown and this is
    # what tells the shader where that is.
    off = axis_offset(sp, attrs["up"])
    rr = np.hypot(verts[:, 0] - off[:, 0], verts[:, 1] - off[:, 1])
    az = np.arctan2(verts[:, 1] - off[:, 1], verts[:, 0] - off[:, 0])
    Renv = crown_radius(sp, attrs["up"], az)
    attrs["rad"] = np.clip(rr / np.maximum(Renv, 1e-4), 0.0, 1.4)
    return verts, quads, attrs


# ==============================================================================
# 8.  MATERIALS.  Procedural, TexCoord -> Object, sockets fed BY NAME.
# ==============================================================================
# Law 4, three forms of the dead bump stack: sockets feeding nothing, a version
# bump that did not propagate, and -- invisible to any wiring check -- fully
# wired, fully fed and MIS-SCALED. Every wavelength here is stated as
# `wavelength_m=` and every socket is fed with `pin_named`, because Blender 5.2
# moved `Principled BSDF.Normal` from index 5 to 6 and index pinning put a
# normal chain on `Thin Wall` (R2-057/R2-070).

def _lin(hexcode):
    return K.srgb_linear(hexcode)


def _stretch(t, vec, sx, sy, sz):
    """Anisotropic coordinate scale, set on the socket so the AUDIT can read it.

    TWO TRAPS, both live, and both cost a run of this module.

    `NT.pin` turns a 3-tuple into a 4-tuple (it is written for colours), so a
    Vector socket has to be assigned directly. And `itemkit._vector_gain` --
    which is what `bump_relief_report` uses to work out what wavelength a
    texture DOWNSTREAM of this actually emits -- reads exactly this socket's
    `default_value`. Wire a Combine XYZ into it instead and the gain reads 1.0
    while the real gain is 7, which is the shape of the defect that put three
    built modules on record at m = 0.002 when they were really at 0.18-0.88.

    So the factors here are always <= 1.0 and the FINEST direction is left at
    1.0: stretching a feature ALONG z by dividing z is the same picture as
    shrinking x and y, and only one of the two leaves the declared wavelength
    equal to the emitted one.
    """
    if max(abs(sx), abs(sy), abs(sz)) > 1.0 + 1e-9:
        raise ValueError(
            "_stretch: a component over 1.0 changes the FINEST wavelength this "
            "coordinate carries, so the `wavelength_m=` stated downstream would "
            "no longer be the one emitted (itemkit Law 5). Divide the long axis "
            "instead of multiplying the short one.")
    nd = t.n("ShaderNodeVectorMath", operation="MULTIPLY")
    t.pin(nd, 0, vec)
    nd.inputs[1].default_value = (float(sx), float(sy), float(sz))
    return (nd, 0)


def mat_foliage(name=PFX + "MAT_Foliage"):
    """Scale-leaf foliage: dark blue-green, waxy, translucent at the tips.

    THREE THINGS THIS MATERIAL HAS TO DO AND WHY EACH ONE IS THERE.

    1. NOT BE UNIFORM. `cy_rad` (depth into the mass), `cy_tip` (base to tip of
       a spray), `cy_up` (height in the crown) and `cy_edge` are baked per
       vertex by section 7, so the tone varies with the plant's own anatomy
       rather than with a noise field pretending to be one. Interior brown,
       tip flush, crown bleach, dust on the lee.

    2. TRANSLUCE. At a 12.47 deg sun a dense conifer is mostly its own shadow,
       and the gate REFUSES a witness frame whose subject is more than 60 %
       crushed to black. That is not a threshold to dodge -- it is the physics:
       real cypress foliage transmits, the shaded side of a real tree is not
       black, and a leaf shader with no transmission is the thing that is wrong.
       A Translucent BSDF mixed at 0.16 against the Principled fixes the
       measurement and the picture at the same time.

    3. CARRY RELIEF IN THE OCTAVE THAT RESOLVES. Two bump stages: the
       inter-branchlet groove at LAM_GROOVE = 14 mm, which is 3.7 px at the
       stated framing -- the CENTRE of the gate's r1 band -- and the scale-leaf
       rank at 2.5 mm, which is 0.67 px there and 2.0 px at the host bound. The
       second is declared sub-pixel at 14 m rather than counted as texture.
    """
    t = NT(name)
    obj = t.object_coords()

    a_rad = t.attr("cy_rad", out=2)
    a_tip = t.attr("cy_tip", out=2)
    a_up = t.attr("cy_up", out=2)
    a_edge = t.attr("cy_edge", out=2)
    a_var = t.attr("cy_var", out=2)          # per-tree constant, 0..1

    # --- colour ----------------------------------------------------------
    deep = _lin("#22301f")        # the shaded interior
    body = _lin("#2f4a2c")        # the working foliage
    lit = _lin("#4a6c39")        # sunlit outer
    flush = _lin("#7f9d4e")        # new growth at the tips
    dead = _lin("#6a4f31")        # dead interior branchlet
    dust = _lin("#7d7360")

    n_big = t.noise(obj, wavelength_m=0.55, detail=4.0, rough=0.52)
    n_mid = t.noise(obj, wavelength_m=0.085, detail=6.0, rough=0.55)
    n_fine = t.noise(obj, wavelength_m=LAM_GROOVE, detail=8.0, rough=0.58)
    v_cell = t.vor(obj, wavelength_m=0.030, feature="F1", out=0)
    v_leaf = t.vor(obj, wavelength_m=LAM_LEAFRANK, feature="F1", out=0)
    w_rank = t.wave(obj, wavelength_m=LAM_LEAFRANK * 2.0, distortion=1.6,
                    detail=3.0, direction="Z")

    # interior -> exterior
    col = t.cmix(t.maprange(a_rad, 0.18, 0.92, 0.0, 1.0), deep, body)
    col = t.cmix(t.maprange(t.math("MULTIPLY", a_rad, n_big), 0.42, 0.95,
                            0.0, 1.0), col, lit)
    # tip flush, modulated per tree and per spray
    fl = t.math("MULTIPLY", t.maprange(a_tip, 0.55, 1.0, 0.0, 1.0),
                t.maprange(a_var, 0.0, 1.0, 0.25, 1.0))
    col = t.cmix(t.math("MULTIPLY", fl, t.maprange(n_mid, 0.3, 0.8, 0.35, 1.0)),
                 col, flush)
    # dead / brown: baked edge==3 marks dead twigs, plus a sparse noise patch
    col = t.cmix(t.maprange(a_edge, 2.5, 3.0, 0.0, 1.0), col, dead)
    col = t.cmix(t.math("MULTIPLY",
                        t.maprange(n_mid, 0.66, 0.86, 0.0, 0.55),
                        t.maprange(a_rad, 0.0, 0.55, 1.0, 0.0)), col, dead)
    # crown bleach
    col = t.cmix(t.math("MULTIPLY", t.maprange(a_up, 0.72, 1.0, 0.0, 0.32),
                        t.maprange(v_cell, 0.2, 0.9, 0.3, 1.0)), col, flush)
    # paddock dust, on the lower third only
    col = t.cmix(t.math("MULTIPLY", t.maprange(a_up, 0.34, 0.02, 0.0, 0.20),
                        t.maprange(n_fine, 0.3, 0.9, 0.0, 1.0)), col, dust)

    # --- roughness -------------------------------------------------------
    rgh = t.maprange(n_mid, 0.15, 0.85, 0.58, 0.86)
    rgh = t.fmix(t.maprange(a_tip, 0.4, 1.0, 0.0, 1.0), rgh,
                 t.maprange(n_fine, 0.2, 0.8, 0.44, 0.66))

    # --- relief.  Amplitudes DERIVED, never typed. ------------------------
    b = t.bump(v_leaf, 1.0, modulation_pp=M_LEAFRANK,
               wavelength_m=LAM_LEAFRANK, height_pp=1.0)
    b = t.bump(w_rank, 0.85, modulation_pp=M_LEAFRANK,
               wavelength_m=LAM_LEAFRANK * 2.0, height_pp=1.0, normal=b)
    b = t.bump(n_fine, 1.0, modulation_pp=M_GROOVE, wavelength_m=LAM_GROOVE,
               height_pp=0.62, normal=b)

    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin_named(bsdf, "Base Color", col)
    t.pin_named(bsdf, "Roughness", rgh)
    t.pin_named(bsdf, "Metallic", 0.0)
    t.pin_named(bsdf, "IOR", 1.42)
    t.pin_named(bsdf, "Normal", b)
    # a waxy sheen on the cuticle -- cypress foliage is glaucous
    for nm in ("Coat Weight", "Sheen Weight"):
        try:
            t.pin_named(bsdf, nm, 0.06)
        except RuntimeError:
            pass

    tr = t.n("ShaderNodeBsdfTranslucent")
    t.pin_named(tr, "Color", t.cmix(0.5, col, flush))
    t.pin_named(tr, "Normal", b)
    mx = t.n("ShaderNodeMixShader")
    # more transmission at the tips (thin new growth), less deep in the mass.
    # "Factor", not "Fac": Blender 5.2 renamed this socket, and the first run of
    # this module raised on it. That is `pin_named` doing its job -- the same
    # line written as `pin(mx, 0, ...)` would have wired silently and correctly
    # today and silently and WRONGLY the next time a socket moved, which is
    # R2-057 exactly.
    t.pin_named(mx, "Factor", t.math("MULTIPLY",
                                  t.maprange(a_tip, 0.2, 1.0, 0.07, 0.26),
                                  t.maprange(a_rad, 0.1, 0.9, 0.35, 1.0)))
    t.t.links.new(bsdf.outputs[0], mx.inputs[1])
    t.t.links.new(tr.outputs[0], mx.inputs[2])
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(mx.outputs[0], out.inputs["Surface"])
    return t.m


def mat_bark(name=PFX + "MAT_Bark"):
    """Cypress bark: thin, fibrous, shredding in long vertical strips.

    The GEOMETRY already carries the flutes (LAM_FLUTE, geometry_fold) and the
    fissures (LAM_FISSURE, hard_feature). This adds the two things geometry at
    17 mm quads cannot: the fibre at 3.5 mm and the plate mottling at 22 mm.
    """
    t = NT(name)
    obj = t.object_coords()
    a_up = t.attr("cy_up", out=2)
    a_var = t.attr("cy_var", out=2)

    # the fibre runs UP, so z is DIVIDED (see `_stretch`): features stretch 6.4x
    # along the stem while the across-stem wavelength -- the finest one, the one
    # that sets the slope and the one `wavelength_m=` declares -- is untouched.
    up = _stretch(t, obj, 1.0, 1.0, 0.156)
    n_fib = t.noise(up, wavelength_m=LAM_FIBRE, detail=8.0, rough=0.62)
    n_plate = t.noise(obj, wavelength_m=LAM_PLATE, detail=6.0, rough=0.55)
    n_big = t.noise(obj, wavelength_m=0.30, detail=4.0, rough=0.5)
    v_shred = t.vor(up, wavelength_m=0.011, feature="F1", out=0)

    grey = _lin("#6b6055")
    warm = _lin("#7a5c46")
    dark = _lin("#3a3129")
    pale = _lin("#93887a")
    col = t.cmix(t.maprange(n_big, 0.25, 0.8, 0.0, 1.0), grey, warm)
    col = t.cmix(t.maprange(n_plate, 0.3, 0.85, 0.0, 1.0), col, dark)
    col = t.cmix(t.math("MULTIPLY", t.maprange(v_shred, 0.0, 0.35, 1.0, 0.0),
                        t.maprange(a_var, 0.0, 1.0, 0.3, 0.9)), col, pale)
    # the base is dirtier and darker (splash, moss on the shaded side)
    col = t.cmix(t.maprange(a_up, 0.09, 0.0, 0.0, 0.5), col, dark)

    rgh = t.maprange(n_fib, 0.1, 0.9, 0.62, 0.94)
    b = t.bump(n_fib, 1.0, modulation_pp=M_FIBRE, wavelength_m=LAM_FIBRE,
               height_pp=0.62)
    b = t.bump(n_plate, 1.0, modulation_pp=M_PLATE, wavelength_m=LAM_PLATE,
               height_pp=0.62, normal=b)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin_named(bsdf, "Base Color", col)
    t.pin_named(bsdf, "Roughness", rgh)
    t.pin_named(bsdf, "Metallic", 0.0)
    t.pin_named(bsdf, "Normal", b)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return t.m


def mat_ground(name=PFX + "MAT_Ground"):
    """The paddock apron the test scene stands on. CONTEXT, not the item.

    Named `Standin` by `K.ground_plane`, so `item_gate`'s own filter drops it
    from the item's statistics -- but its material is still scanned by check 1b,
    which is R2-070: two wave-1 items were ACCEPTED with the relief in their
    CONTEXT materials wired to the wrong socket.
    """
    t = NT(name)
    obj = t.object_coords()
    n1 = t.noise(obj, wavelength_m=0.42, detail=6.0, rough=0.55)
    n2 = t.noise(obj, wavelength_m=0.026, detail=8.0, rough=0.6)
    v1 = t.vor(obj, wavelength_m=0.055, feature="F1", out=0)
    a = _lin("#6d6a63")
    b_ = _lin("#514e48")
    c = _lin("#7b756a")
    col = t.cmix(t.maprange(n1, 0.25, 0.75, 0.0, 1.0), a, b_)
    col = t.cmix(t.maprange(v1, 0.05, 0.4, 0.0, 0.55), col, c)
    rgh = t.maprange(n2, 0.2, 0.8, 0.72, 0.95)
    bmp = t.bump(n2, 1.0, modulation_pp=0.34, wavelength_m=0.026, height_pp=0.62)
    bmp = t.bump(v1, 0.7, modulation_pp=0.55, wavelength_m=0.055, height_pp=1.0,
                 normal=bmp)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin_named(bsdf, "Base Color", col)
    t.pin_named(bsdf, "Roughness", rgh)
    t.pin_named(bsdf, "Normal", bmp)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return t.m


# ==============================================================================
# 9.  THE PLANTING PLAN.  1,400 trees in the paddock, and not on a grid.
# ==============================================================================
# `variation_axes` says 14 % of the paddock mix. `APRON_REGIONS_CIRCUIT` puts
# the paddock at circuit x -480..100, y 40.5..115. Cypress in a paddock is a
# planted thing: allees along the service roads, clumps at the corners of
# buildings, and a scatter through the informal edges. A uniform random scatter
# would be as wrong as a grid.

#: Minimum centre-to-centre spacing, metres. Not a tidiness rule: cypress IS
#: planted tight -- a screen goes in at 0.8-1.2 m and an allee at 3-5 m -- but
#: two trunks 0.17 m apart, which is what the first version of this function
#: produced and what selftest [7] caught, is one tree growing out of another.
MIN_SPACING_M = 1.05


def plan(n=N_PLAN, seed=SEED):
    """-> (N, 2) world XY, plus a per-tree yaw and scale. Deterministic.

    Rejection-sampled against `MIN_SPACING_M` through a uniform grid hash, so
    the clumps stay clumps without any two trunks sharing a hole. The grid is
    `MIN_SPACING_M` on a side, so a candidate only ever has to look at its own
    cell and the eight around it.
    """
    r = K.Rng(seed, 4242)
    cx0, cx1, cy0, cy1 = -470.0, 92.0, 42.0, 113.0
    px, py, kind = [], [], []
    cell = {}
    s2 = MIN_SPACING_M * MIN_SPACING_M

    def place(x, y, k):
        ix, iy = int(math.floor(x / MIN_SPACING_M)), int(math.floor(y / MIN_SPACING_M))
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for (qx, qy) in cell.get((ix + a, iy + b), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < s2:
                        return False
        cell.setdefault((ix, iy), []).append((x, y))
        px.append(x); py.append(y); kind.append(k)
        return True

    # --- allees: rows along the paddock's long axis, 2.6-4.4 m apart -------
    n_row = 14
    for i in range(n_row):
        y = cy0 + (cy1 - cy0) * ((i + 0.5) / n_row) + r.n(0.0, 1.6)
        x = cx0 + r.u(0.0, 90.0)
        pitch = r.u(2.6, 4.4)
        while x < cx1:
            # 6 % of the row is a gap (a dead tree, a gateway, a service bay)
            if r.u() > 0.06:
                place(x + r.n(0.0, 0.22), y + r.n(0.0, 0.30), 0)
            x += pitch * (1.0 + r.n(0.0, 0.06))
            if len(px) > n * 0.62:
                break
        if len(px) > n * 0.62:
            break

    # --- clumps: 3-9 trees at building corners and junctions ---------------
    tries = 0
    while len(px) < n * 0.86 and tries < 400000:
        ccx = r.u(cx0, cx1)
        ccy = r.u(cy0, cy1)
        for _ in range(r.i(3, 9)):
            a = r.u(0.0, 2 * math.pi)
            d = abs(r.n(0.0, 2.1)) + 0.9
            place(ccx + d * math.cos(a), ccy + d * math.sin(a), 1)
            tries += 1

    # --- scatter -----------------------------------------------------------
    tries = 0
    while len(px) < n and tries < 400000:
        place(r.u(cx0, cx1), r.u(cy0, cy1), 2)
        tries += 1
    if len(px) < n:
        raise RuntimeError(
            "plan: only %d of %d trees could be placed at >= %.2f m spacing in "
            "the paddock envelope. Widen the envelope or state a smaller "
            "population -- silently returning a short plan is how a declared "
            "count and a built count drift apart." % (len(px), n, MIN_SPACING_M))

    px = np.array(px[:n])
    py = np.array(py[:n])
    kind = np.array(kind[:n])
    wx, wy = C.circuit_to_world(px, py)
    yaw = r.arr(n) * 2.0 * math.pi
    # 0.92-1.08. TRANSFORM SCATTER IS NOT VARIATION and is not counted as such:
    # it sits on top of 44 distinct meshes, it does not stand in for them.
    scale = 0.92 + 0.16 * r.arr(n)
    return np.asarray(wx, float), np.asarray(wy, float), yaw, scale, kind


# ==============================================================================
# 10.  BUILD.
# ==============================================================================

def _coll(name, parent=None):
    return K.coll(name, parent)


def build_source(i, sp, mats, coll_, lod=0):
    """One library tree, as a real object at a real planting position."""
    v, q, at = tree_arrays(sp, lod=lod)
    name = "%sSrc%02d" % (PFX, i)
    me, off = K.new_mesh(name, v, quads=q, smooth_deg=34.0, recentre=False)
    K.bake_attributes(me, {
        "cy_tip": at["tip"], "cy_edge": at["edge"],
        "cy_up": at["up"], "cy_rad": at["rad"],
        "cy_var": np.full(len(v), K.hash01(sp["seed"], 5, 11)),
    })
    for m in mats:
        me.materials.append(m)
    # per-polygon material: bark on wood, foliage on everything green.
    # `cy_edge` >= 2 marks cones (2) and dead twigs (3); the trunk and branches
    # are the first `nwood` vertices by construction.
    ob = bpy.data.objects.new(name, me)
    ob["cypress_index"] = i
    ob["height_m"] = round(sp["h"], 4)
    ob["age"] = round(sp["age"], 4)
    ob["crown_r_m"] = round(sp["rmax"], 4)
    ob["n_lobe"] = sp["n_lobe"]
    coll_.objects.link(ob)
    return ob, len(q)


def _assign_bark(me, nwood_verts):
    """Slot 1 (bark) for every polygon entirely inside the first `nwood_verts`.

    Cheap and exact: the trunk and branches are emitted first, so a polygon
    whose corners are all below the watermark is wood. numpy, because a Python
    loop over 185,000 polygons x 44 trees is 8 M iterations.
    """
    nl = len(me.loops)
    npl = len(me.polygons)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(npl, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npl, np.int32); me.polygons.foreach_get("loop_total", lt)
    first = lv[ls.astype(np.int64)]
    idx = np.where(first < nwood_verts, 1, 0).astype(np.int32)
    me.polygons.foreach_set("material_index", idx)


def build(scene=None, n_sources=N_SOURCES, n_plan=N_PLAN, lod=0, seed=SEED,
          instance=True, stats=None):
    """Emit the item: `n_sources` real trees + a geometry-nodes field.

    THE EMISSION MECHANISM IS A GATE DECISION (R2-1381). `item_gate`'s variety
    check has two paths and they are 20x apart: realized geometry-nodes
    instances are held to `distinct_sources >= 37` at this population with a
    25 % commonest-share cap, and plain objects are held to
    `distinct_topologies >= 2` with no cap at all. This emits so the STRONG path
    applies -- the instancer stays in the depsgraph and
    `depsgraph.object_instances` walks it -- because an item that lands on the
    weak path has had its red-line guard evaluated at a bar of two.
    """
    scene = scene or bpy.context.scene
    t0 = time.time()
    K.purge(PFX, COLL)
    root = _coll(COLL)
    lib = _coll(LIB_COLL, root)

    fol = mat_foliage()
    bark = mat_bark()
    mats = [fol, bark]

    wx, wy, yaw, scale, kind = plan(n_plan, seed)
    specs = [tree_spec(i, seed) for i in range(n_sources)]

    objs, nq = [], 0
    for i, sp in enumerate(specs):
        # the wood watermark: trunk + branches are emitted first
        vw, qw, _ = trunk_mesh(sp)
        nb = int(70 + 70 * sp["age"])
        vb, _, _ = branch_mesh(sp, K.Rng(sp["seed"], 977), nb)
        watermark = len(vw) + len(vb)
        ob, q = build_source(i, sp, mats, lib, lod=lod)
        _assign_bark(ob.data, watermark)
        x, y = float(wx[i]), float(wy[i])
        ob.location = (x, y, K.seat_on_ground(x, y, base_local_z=0.0))
        ob.rotation_euler = (0.0, 0.0, float(yaw[i]))
        ob.scale = (float(scale[i]),) * 3
        objs.append(ob)
        nq += q
        if (i + 1) % 8 == 0:
            log("  %2d/%2d sources, %.2f M quads, %.1f s"
                % (i + 1, n_sources, nq / 1e6, time.time() - t0))

    field = None
    if instance and n_plan > n_sources:
        field = build_field(root, lib, n_sources,
                            wx[n_sources:], wy[n_sources:],
                            yaw[n_sources:], scale[n_sources:], seed)

    tris = nq * 2
    log("built %d source trees, %.3f M quads = %.3f M triangles "
        "(%.0f k tris/tree); field carries %d instances"
        % (n_sources, nq / 1e6, tris / 1e6, tris / max(n_sources, 1) / 1e3,
           0 if field is None else n_plan - n_sources))
    if stats is not None:
        stats.update(sources=n_sources, quads=nq, tris=tris,
                     instances=n_plan - n_sources,
                     heights=[s["h"] for s in specs],
                     seconds=time.time() - t0)
    return root


def _field_node_group(name, library, n_sources, seed):
    """Collection Info -> Instance on Points, with Pick Instance.

    Deliberately the same shape as `spectator_seated`'s, which is a BUILT and
    GATED module: its own note records, measured rather than assumed, that
    Collection Info reads objects the depsgraph will still walk. Copying a
    working graph is cheaper than rediscovering which sockets Blender 5.2
    renamed.
    """
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); gi.location = (-700, 0)
    go = ng.nodes.new("NodeGroupOutput"); go.location = (700, 0)
    ci = ng.nodes.new("GeometryNodeCollectionInfo"); ci.location = (-700, -240)
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); iop.location = (250, 0)
    iop.inputs["Pick Instance"].default_value = True

    ridx = ng.nodes.new("FunctionNodeRandomValue"); ridx.location = (-350, -520)
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
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    for s in ridx.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Instance Index"])
            break
    # yaw and scale come from named point attributes written by `build_field`,
    # so they are the SAME numbers the 44 real trees got -- one plan, two
    # emission mechanisms, not two plans.
    for attr, sock in (("inst_rot", "Rotation"), ("inst_scale", "Scale")):
        na = ng.nodes.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT_VECTOR"
        na.inputs["Name"].default_value = attr
        na.location = (-350, -760 if attr == "inst_rot" else -940)
        ng.links.new(na.outputs["Attribute"], iop.inputs[sock])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    return ng


def build_field(root, lib, n_sources, wx, wy, yaw, scale, seed):
    """The point cloud the instancer runs on. One vertex per remaining tree."""
    n = len(wx)
    z = np.array([K.seat_on_ground(float(a), float(b), base_local_z=0.0)
                  for a, b in zip(wx, wy)])
    P = np.stack([wx, wy, z], axis=1)
    me = bpy.data.meshes.new(PFX + "Field")
    me.vertices.add(n)
    me.vertices.foreach_set("co", np.ascontiguousarray(P, np.float32).ravel())
    me.update()
    rot = np.zeros((n, 3)); rot[:, 2] = yaw
    a = me.attributes.new("inst_rot", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", np.ascontiguousarray(rot, np.float32).ravel())
    sc = np.repeat(np.asarray(scale, np.float32)[:, None], 3, axis=1)
    a = me.attributes.new("inst_scale", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", np.ascontiguousarray(sc, np.float32).ravel())
    ob = bpy.data.objects.new(PFX + "Field", me)
    root.objects.link(ob)
    ng = _field_node_group(PFX + "FieldGN", lib, n_sources, seed)
    md = ob.modifiers.new("cypress", "NODES")
    md.node_group = ng
    ob["instances"] = n
    ob["library_sources"] = n_sources
    log("field: %d instances from %d sources (%.4f expected share each)"
        % (n, n_sources, 1.0 / max(1, n_sources)))
    return ob


# ==============================================================================
# 11.  THE HANDBACK FILE.
# ==============================================================================

def interface_json(path=None, n_sources=N_SOURCES):
    specs = [tree_spec(i) for i in range(n_sources)]
    return K.interface_json(
        ITEM,
        path=path or os.path.join(_HERE, ITEM + "_interface.json"),
        collection=COLL,
        library_collection=LIB_COLL,
        object_prefix=PFX,
        materials={"foliage": PFX + "MAT_Foliage", "bark": PFX + "MAT_Bark"},
        vertex_attributes={
            "cy_tip": "0 at a spray's base, 1 at its tip",
            "cy_edge": "0 foliage, 2 cone, 3 dead twig",
            "cy_up": "height fraction of the tree",
            "cy_rad": "0 on the leader axis, 1 at the crown envelope",
            "cy_var": "per-tree constant in [0,1)",
        },
        framing={
            "stated_gate_distance_m": STATED_AT_M,
            "stated_gate_px_per_m": PX_PER_M,
            "built_for_range_m": list(BUILT_FOR_M),
            "lens_mm": LENS_MM,
            "why_14m": ("the manifest's own nearest_camera_m for every other "
                        "PADDOCK tree (tree_london_plane, paddock_avenue_tree, "
                        "planter_shrub); this item is declared '14 % of the "
                        "paddock mix'; 1.43x closer than this item's own "
                        "manifest 20.0 m, and it keeps check 8 in scope, which "
                        "20.0 m would not (5 mm = 0.93 px there)"),
            "manifest_nearest_camera_m": MANIFEST_NEAREST_M,
            "manifest_hero": MANIFEST_HERO,
            "host_bound_min_depth_m": HOST_BOUND_M,
            "host_bound_peak_px_4k": MEASURED_PEAK_PX,
            "HOST_BOUND_CAVEAT": (
                "screen_presence.json's own presence_unverified_2026_08_04 "
                "block: these are HOST upper bounds, and 'a HERO verdict on an "
                "item listed ABSENT in the census must not be quoted without "
                "the qualifier'. This item's 93 hosts are VEG_shrub_*, "
                "VEG_sapling, VEG_fern and 81 more; all five tree species "
                "report the identical min_depth_m 4.577, which is one shared "
                "host approach and not five measurements. Gated at 4.577 m as "
                "a SECOND run and reported as a host bound."),
            "what_would_settle_it": (
                "screen_presence.json's own `to_clear`: place the item modules "
                "into the assembled world and re-derive with tools/retier.sh. "
                "SHIPPING.md says assembly10.blend is the first assembly "
                "carrying anything from world/items/. Until this module is in "
                "an assembly and re-swept, 4.577 m belongs to the ferns."),
        },
        population={
            "declared_instances": DECLARED_INSTANCES,
            "distinct_sources": n_sources,
            "emission": ("real objects for the sources + a GeometryNodes "
                         "Instance-on-Points field for the rest, so "
                         "item_gate's STRONG variety path applies"),
            "heights_m": [round(s["h"], 3) for s in specs],
            "ages": [round(s["age"], 3) for s in specs],
            "crown_r_m": [round(s["rmax"], 3) for s in specs],
        },
        lod={
            "0": "as gated; ~185 k quads / tree; the film's ladder inside 45 m",
            "1": "lobe count x0.42 on a 7x6 spray grid; ~33 k quads",
            "2": "lobe count x0.14 on a 4x4 spray grid, no sprig fringe",
            "note": ("1,400 instances of LOD 0 is ~520 M triangles. The world "
                     "module owns the ladder; this module is judged at LOD 0."),
        },
        relief={
            "sun_elev_deg": K.sun_elev_deg(),
            "sun_amplifier": K.sun_amplifier(),
            "stages": [{"stage": n_, "wavelength_m": l_, "amp_mm_pp": a_,
                        "band": b_} for n_, l_, a_, b_ in relief_stages()],
            "pixel_footprint": pixel_footprint(),
            "where_the_law_stops": (
                "slope_for_modulation refuses m > 2/tan(e) = 9.04 and says "
                "why: more than that is a shadow, which is geometry, not "
                "relief. The crown's lobe FORM (0.18-2.05 m) is form and casts "
                "real shadow; geometry_relief_report reads it well over the "
                "bands and that is correct. The law governs every shader bump "
                "and the surface texture OF a spray or of the bark, and those "
                "are all in-band."),
        },
        placement={
            "ground": "world_contract.world_ground_z(x, y); paddock apron",
            "base_embed_m": C.BASE_EMBED_M,
            "origin": ("mesh emitted with the tree BASE at its own local "
                       "origin, NOT bbox-recentred -- see tree_arrays()"),
        },
    )


# ==============================================================================
# 12.  THE TEST SCENE.
# ==============================================================================

def hero_index(n_sources=N_SOURCES):
    """The source the macro is shot on, chosen by SCORE, not by convenience.

    The manifest's variation axes are the column form and the splay at the top
    of older ones, so the macro must be shot where there IS a splay -- and the
    tree must also be typical enough that the picture is a claim about the item
    rather than about its one showpiece. Middle-of-the-road height, high splay,
    at least one gap, cones present.
    """
    best, bs = 0, -1e9
    for i in range(n_sources):
        sp = tree_spec(i)
        typ = 1.0 - abs(sp["h"] - DECLARED_HEIGHT_M) / 4.0
        sc = (1.35 * sp["splay"] + 0.55 * min(len(sp["gaps"]), 2) / 2.0
              + 0.45 * min(sp["n_cone"], 60) / 60.0
              + 0.40 * sp["a_light"] / 0.22 + 0.60 * typ
              + 0.30 * (sp["n_leader"] - 1) / 3.0)
        if sc > bs:
            best, bs = i, sc
    return best


def test_scene(samples=256, n_sources=N_SOURCES, n_plan=N_PLAN, lod=0,
               instance=True):
    """Build, light with the contract sun, and put the STATED camera on it."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    stats = {}
    root = build(scene=scene, n_sources=n_sources, n_plan=n_plan, lod=lod,
                 instance=instance, stats=stats)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    K.contract_sun(PFX, scene=scene, coll_=root)

    hi = hero_index(n_sources)
    hero = bpy.data.objects.get("%sSrc%02d" % (PFX, hi))
    sp = tree_spec(hi)
    hx, hy = float(hero.location.x), float(hero.location.y)
    log("hero source %d: h %.2f m  age %.2f  crown r %.3f m  splay %.2f  "
        "leaders %d  gaps %d  cones %d"
        % (hi, sp["h"], sp["age"], sp["rmax"], sp["splay"], sp["n_leader"],
           len(sp["gaps"]), sp["n_cone"]))

    # The paddock apron is analytic and flat; 19.5 % of a 170 m span falls
    # where TERRAIN owns the ground and the contract returns NaN there rather
    # than inventing a height, which is correct and is why `ground_plane`
    # refuses without an explicit `fill_z`. STATED CHOICE: the standin is filled
    # at the apron's own height. It exists to give a contact shadow and a
    # horizon in the test frames; it is named `Standin` so item_gate drops it
    # from the item's statistics, and the real ground out there is
    # build_terrain's mesh, not this.
    K.ground_plane(PFX, stand, centre=(hx, hy), span=150.0, res=170,
                   material=mat_ground(), fill_z=K.ground_z(hx, hy))

    # --- the macro.  3840 x 2160, and the distance is ASSERTED. ------------
    # Aimed at 0.56 of the tree's height, which is where the column, the
    # asymmetry and the bottom of the splay are all in one frame at 14 m
    # (vertical coverage 8.10 m on a 35 mm lens).
    gz = K.ground_z(hx, hy)
    aim = (hx, hy, gz + 0.56 * sp["h"])
    # 40 deg off the light azimuth so the sun rakes ACROSS the sprays rather
    # than along them -- the same reason item_gate offsets its own sun by 70
    # deg, measured there on armco_w_beam.
    az = math.radians(C.SUN_BEARING_DEG + 118.0)
    el = math.radians(11.0)
    loc = (aim[0] + STATED_AT_M * math.cos(el) * math.cos(az),
           aim[1] + STATED_AT_M * math.cos(el) * math.sin(az),
           aim[2] + STATED_AT_M * math.sin(el))
    K.macro_rig(PFX + "CAM_MACRO_4K", loc, aim, LENS_MM, cams, scene=scene,
                samples=samples, want_distance_m=STATED_AT_M, tolerance_m=0.02)

    # the host bound, as a second camera on the same tree, so the two framings
    # can be looked at side by side rather than argued about
    aim2 = (hx, hy, gz + 0.52 * sp["h"])
    loc2 = (aim2[0] + HOST_BOUND_M * math.cos(el) * math.cos(az),
            aim2[1] + HOST_BOUND_M * math.cos(el) * math.sin(az),
            aim2[2] + HOST_BOUND_M * math.sin(el))
    K.add_camera(PFX + "CAM_HOSTBOUND", loc2, aim2, LENS_MM, cams)

    # the whole tree, at the distance the manifest claims
    aim3 = (hx, hy, gz + 0.50 * sp["h"])
    loc3 = (aim3[0] + 20.75 * math.cos(el) * math.cos(az),
            aim3[1] + 20.75 * math.cos(el) * math.sin(az),
            aim3[2] + 20.75 * math.sin(el))
    K.add_camera(PFX + "CAM_WHOLE", loc3, aim3, LENS_MM, cams)

    # the row, so the variety can be judged rather than counted
    aim4 = (hx, hy, gz + 3.2)
    loc4 = (aim4[0] + 42.0 * math.cos(az + 0.5),
            aim4[1] + 42.0 * math.sin(az + 0.5), aim4[2] + 9.0)
    K.add_camera(PFX + "CAM_ROW", loc4, aim4, 50.0, cams)

    K.assert_no_external_assets()
    interface_json()
    return root, stats


# ==============================================================================
# 13.  SELFTEST.  Measured, with negative controls where a check could pass for
#      the wrong reason.
# ==============================================================================

def selftest(verbose=True, n_sources=N_SOURCES):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-54s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("\n[1] the framing is stated, sourced, and keeps check 8 in scope")
    from_gate = 5.0 * PX_PER_M / 1000.0
    from_manifest = 5.0 * K.px_per_m(MANIFEST_NEAREST_M, LENS_MM) / 1000.0
    chk("5 mm is over the 1.0 px scoping floor at the stated distance",
        from_gate >= 1.0,
        "%.2f px at %.3f m (%.1f px/m)" % (from_gate, STATED_AT_M, PX_PER_M))
    chk("... and would NOT have been at the manifest's distance",
        from_manifest < 1.0,
        "%.2f px at %.1f m -- choosing 20 m would have scoped check 8 OUT"
        % (from_manifest, MANIFEST_NEAREST_M))
    chk("the stated distance is inside the built-for range",
        BUILT_FOR_M[0] <= STATED_AT_M <= BUILT_FOR_M[1],
        "%.1f in [%.1f, %.1f] m" % (STATED_AT_M, *BUILT_FOR_M))

    print("\n[2] every relief amplitude is DERIVED, and every one is in band")
    rows = K.relief_budget([(a, b, c) for a, b, c, _ in relief_stages()],
                           verbose=False)
    for (name, lam, amp, band), r in zip(relief_stages(), rows):
        lo, hi = K.RELIEF_BANDS[band]
        ok = lo - 1e-9 <= r["m"] <= hi + 1e-9
        chk("  %-22s in %s" % (name, band), ok,
            "lam %7.2f mm  amp %6.4f mm  slope %5.2f deg  m %5.3f "
            "(band %.2f-%.2f)" % (lam * 1000, amp, r["slope_deg"], r["m"],
                                  lo, hi))
    # NEGATIVE CONTROL: the check must be able to fail. A stage typed in
    # millimetres instead of derived -- 0.5 mm, the number the human figures
    # were reasoned about in -- lands where?
    bad = K.modulation_for_amplitude(0.5, LAM_LEAFRANK)
    chk("  negative control: 0.5 mm typed at 2.5 mm lands OUT of band",
        not (K.RELIEF_BANDS["isotropic_micro"][0] <= bad
             <= K.RELIEF_BANDS["isotropic_micro"][1]),
        "m = %.2f against isotropic_micro 0.12-0.45 -- so this check can fail"
        % bad)

    print("\n[3] LAW 3 -- the pixel footprint of every stated wavelength")
    inband = 0
    for r in pixel_footprint():
        p14 = r["px_at_%.3fm" % STATED_AT_M]
        p46 = r["px_at_%.3fm" % HOST_BOUND_M]
        tag = ("SUB-PIXEL at 14 m" if p14 < 1.0 else
               "r1" if p14 < 4.5 else "r2" if p14 < 9.0 else
               "r4" if p14 < 18.0 else "r8+")
        if 1.0 <= p14 <= 24.0:
            inband += 1
        print("       %-22s %7.2f mm -> %6.2f px @14.0 m, %6.2f px @4.577 m  %s"
              % (r["stage"], r["wavelength_mm"], p14, p46, tag))
    chk("most stages resolve at the stated framing", inband >= 6,
        "%d of %d stages land in 1-24 px at 14.0 m" % (inband, len(relief_stages())))

    print("\n[4] the silhouette DEPARTS -- measured on the envelope function")
    # The check refits a quadratic inside a 100-row window. At the stated
    # framing that window is 100/PX_PER_M metres of tree. This measures the
    # residual of the ENVELOPE after exactly that operation, which is the
    # geometric half of what the render will show.
    win_m = 100.0 / PX_PER_M
    worst_flat = 1e9
    dep = []
    for i in range(n_sources):
        sp = tree_spec(i)
        z = np.linspace(0.18 * sp["h"], 0.92 * sp["h"], 900)
        t = z / sp["h"]
        res = []
        for phi in (0.0, math.pi):                 # the two profile sides
            r = crown_radius(sp, t, np.full_like(t, phi))
            k = max(8, int(round(win_m / (z[1] - z[0]))))
            for s0 in range(0, len(z) - k, k // 2):
                zz, rr = z[s0:s0 + k], r[s0:s0 + k]
                c = np.polyfit(zz, rr, 2)
                res.append(float(np.sqrt(((rr - np.polyval(c, zz)) ** 2).mean())))
        med = float(np.median(res))
        dep.append(med)
        worst_flat = min(worst_flat, med)
    chk("every source's envelope departs by >= 5 mm in a 0.375 m window",
        worst_flat * 1000.0 >= 5.0,
        "worst of %d sources %.1f mm, median %.1f mm (the gate's bar is 5.0 mm "
        "and the render adds the spray fringe on top)"
        % (n_sources, worst_flat * 1000.0, float(np.median(dep)) * 1000.0))
    # NEGATIVE CONTROL: strip the departure and the same measurement must fail.
    sp = tree_spec(hero_index(n_sources))
    flat = dict(sp)
    flat["env_terms"] = []
    flat["a_light"] = flat["a_wind"] = 0.0
    flat["gaps"] = []
    flat["splay_out"] = 0.0
    z = np.linspace(0.18 * sp["h"], 0.92 * sp["h"], 900)
    r = crown_radius(flat, z / sp["h"], np.zeros_like(z))
    k = max(8, int(round(win_m / (z[1] - z[0]))))
    res = []
    for s0 in range(0, len(z) - k, k // 2):
        zz, rr = z[s0:s0 + k], r[s0:s0 + k]
        c = np.polyfit(zz, rr, 2)
        res.append(float(np.sqrt(((rr - np.polyval(c, zz)) ** 2).mean())))
    ctl = float(np.median(res)) * 1000.0
    chk("  negative control: the SAME tree with the departure stripped fails",
        ctl < 5.0,
        "%.4f mm -- an analytic column, which is what the check exists to "
        "reject" % ctl)

    print("\n[5] variety: 44 sources, and they differ in the gate's OWN terms")
    specs = [tree_spec(i) for i in range(n_sources)]
    hs = np.array([s["h"] for s in specs])
    rs = np.array([s["rmax"] for s in specs])
    ags = np.array([s["age"] for s in specs])
    need = max(8, min(40, int(math.sqrt(DECLARED_INSTANCES))))
    chk("source count clears the strong path's bar", n_sources >= need,
        "%d sources against %d required at %d realized instances"
        % (n_sources, need, DECLARED_INSTANCES))
    # `_shape_signature` quantises the bbox to 10 mm. Two sources that differ by
    # less than that in every axis would be ONE shape to the gate.
    box = np.stack([np.round(hs * 100), np.round(rs * 2 * 100)], axis=1)
    chk("no two sources share a 10 mm-quantised bbox",
        len({tuple(b) for b in box}) == n_sources,
        "%d distinct of %d (this is `_shape_signature`'s own quantisation, "
        "which is what caught spectator_seated's 420 datablocks holding 6 poses)"
        % (len({tuple(b) for b in box}), n_sources))
    chk("height CV is a real spread, not jitter",
        float(hs.std() / hs.mean()) >= 0.10,
        "CV %.4f over %.2f-%.2f m" % (hs.std() / hs.mean(), hs.min(), hs.max()))
    chk("the manifest's two named axes are both present and both vary",
        (ags > 0.42).sum() >= 6 and (ags <= 0.42).sum() >= 6,
        "'column form' + 'splay at the top of older ones': %d splayed, "
        "%d spire-topped" % (int((ags > 0.42).sum()), int((ags <= 0.42).sum())))

    print("\n[6] the hash avalanches -- the naive FNV form collapses 7 axes to 1")
    a = [K.hash01(1234, k) for k in (3, 5, 7)]
    chk("hash01(seed, 3/5/7) are three different numbers", len(set(a)) == 3,
        "%.5f %.5f %.5f" % tuple(a))

    print("\n[7] the plan is a planting, not a scatter")
    wx, wy, yaw, sc, kind = plan(400, SEED)
    d = np.hypot(wx[:, None] - wx[None, :], wy[:, None] - wy[None, :])
    np.fill_diagonal(d, 1e9)
    nn = d.min(axis=1)
    chk("no two trees are closer than a crown width", float(nn.min()) > 0.9,
        "nearest neighbour min %.2f m, median %.2f m" % (nn.min(), np.median(nn)))
    chk("the plan carries rows AND clumps AND scatter", len(set(kind.tolist())) == 3,
        "kinds present: %s" % sorted(set(kind.tolist())))

    print("\n[8] the ground is the contract's, and the seat embeds")
    x, y = float(wx[0]), float(wy[0])
    z = K.seat_on_ground(x, y, base_local_z=0.0)
    gz = K.ground_z(x, y)
    chk("base embeds at least BASE_EMBED_M", gz - z >= C.BASE_EMBED_M - 1e-9,
        "ground %.4f, origin %.4f, embed %.4f m (contract %.3f)"
        % (gz, z, gz - z, C.BASE_EMBED_M))

    print("\n[9] scale against the MEASURED car, not intuition")
    sp = specs[hero_index(n_sources)]
    chk("crown is narrower than the car is wide",
        2 * sp["rmax"] < CAR_W_M,
        "crown %.2f m across against a %.3f m car -- a cypress is a NARROW "
        "tree and getting that wrong is what makes a paddock read as a park"
        % (2 * sp["rmax"], CAR_W_M))

    print("\n%d checks, %d failed%s"
          % (n[0], len(fails), (": " + ", ".join(fails)) if fails else ""))
    return not fails


def census(stats):
    """What was actually built, printed so a reader does not have to believe."""
    print(">> CENSUS " + json.dumps({
        "item": ITEM,
        "sources": stats.get("sources"),
        "quads": stats.get("quads"),
        "triangles": stats.get("tris"),
        "triangles_per_source_tree":
            round(stats.get("tris", 0) / max(stats.get("sources", 1), 1)),
        "triangles_per_declared_instance":
            round(stats.get("tris", 0) / DECLARED_INSTANCES, 1),
        "instanced": stats.get("instances"),
        "declared": DECLARED_INSTANCES,
        "seconds": round(stats.get("seconds", 0.0), 1),
        "stated_gate_distance_m": STATED_AT_M,
        "px_per_m": round(PX_PER_M, 2),
        "mm_per_px": round(MM_PER_PX, 4),
    }))


# ==============================================================================
# 14.  CLI.
# ==============================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--build", action="store_true")
    p.add_argument("--test-scene", "--test", dest="test_scene",
                   action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--out", "--save", dest="out", default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--sources", type=int, default=N_SOURCES)
    p.add_argument("--plan", type=int, default=N_PLAN)
    p.add_argument("--lod", type=int, default=0)
    p.add_argument("--no-instance", action="store_true")
    p.add_argument("--interface", action="store_true")
    a = p.parse_args(argv)

    if a.selftest and not (a.build or a.test_scene):
        ok = selftest()
        print(">> STAGE RESULT: selftest %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    if a.interface:
        interface_json()
        print(">> STAGE RESULT: interface PASS")
        return 0

    if not HAVE_BPY:
        raise SystemExit("needs Blender: /opt/blender-5.2.0-linux-x64/blender "
                         "-b --factory-startup -P %s -- --test-scene" % __file__)

    stats = {}
    if a.test_scene:
        _root, stats = test_scene(samples=a.samples, n_sources=a.sources,
                                  n_plan=a.plan, lod=a.lod,
                                  instance=not a.no_instance)
    else:
        build(n_sources=a.sources, n_plan=a.plan, lod=a.lod,
              instance=not a.no_instance, stats=stats)
        interface_json()
    census(stats)
    K.assert_no_external_assets()
    if a.selftest:
        selftest()
    if a.out:
        bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
        log("saved %s" % a.out)
        print(">> STAGE RESULT: saved %s PASS" % a.out)
    print(">> STAGE RESULT: %s build PASS" % ITEM)
    print(">> gate:  " + " ".join(K.gate_command(
        ITEM, a.out or "<blend>", collection=COLL,
        filmed_distance_m=STATED_AT_M,
        onscreen_px_4k=DECLARED_HEIGHT_M * PX_PER_M)))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
