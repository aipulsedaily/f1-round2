"""THE BREACH SIM — build the scene, bake it, and export the transforms.

    blender -b --factory-startup -P sim/build_breach_sim.py -- \
        --out sim/out/breach_sim.blend --bake --export sim/out/breach_bake.npz

WHAT THIS IS
============
A rigid-body destruction sim of the showroom's east curtain wall, run on a
uniform WORLD-time grid at 240 Hz and exported as a transform table.  It is a
SEPARATE, SMALL scene on purpose: the shipping world is 4.0 GB / 28,781 objects
and `push_scene` is not resumable, so a sim that lived inside it would have to be
re-uploaded in full every time a threshold moved.  What ships is the TABLE.

WHY THE SIM RUNS IN WORLD TIME
------------------------------
See `sim/breachlib.py`.  Baking on film frames would integrate gravity per film
frame while the ramp holds the car at 15.4 %, making the debris 6.5x too heavy
for the picture during the only 8 s anyone is looking at it.

WHAT IS SIMULATED, AND WHAT IS NOT
==================================
SIMULATED
    every glass shard from `sim/fracture.py`                     ~3,000 bodies
    the five mullions in and beside the aperture, in 8 segments each, joined by
    breakable FIXED constraints — so mullion 5 fails where it is hit, and 3 and
    7 articulate into the bent stubs `mullion_bent_stub` is specified to be
    the transom rails across those bays, bolted to the mullions with breakable
    constraints at their real shear-block positions
    the PVB bridges: 15 % of shards keep a stretchy link to a neighbour, which
    is what stops laminated glass behaving like a bag of gravel

NOT SIMULATED, AND SAID PLAINLY
    the car.  It is a PASSIVE KINEMATIC boundary condition following the
    animation in `world/car_anim.blend` exactly.  Through beat 3 that animation
    is one continuous rigid motion with no yaw, no pitch response and no
    lock-up, and this sim does not change it.

    THE JUSTIFICATION THAT USED TO BE HERE WAS WRONG BY 75x (R2-099) AND IS
    WITHDRAWN.
    It read "an F1 car is 798 kg against 4.9 kg of glass per pane, and the
    honest response to 26 kJ of pane is a few mm/s".  A pane is 2.17 x 6.025 m
    of 11.5 mm laminate = 375 kg, and the six fractured bays total 2,240.9 kg
    in this file's OWN `shard_meta`.  The car carries 798 x 16.4 =
    13,087 kg.m/s and the shard field takes up to 5,946 kg.m/s of it — 45 %.
    "A few mm/s" is not supported by any number in this file.  The kinematic
    proxy is a DECISION, not a consequence: the car's motion through beat 3 is
    authored, continuity-gated and shared with the camera rig, and making it
    dynamic would put a solver in the middle of the one continuous take.  What
    it costs is that the car does not decelerate through the wall, and that
    cost is real and is not measured here.  If the car SHOULD react, that is a
    change to `anim/carrig.py` and belongs in a report, not here.
    the dust.  A rigid-body solver has nothing to say about it.

THE APERTURE IS MEASURED, NOT DRAWN
-----------------------------------
`mullion_intact.breach_state()` declares mullions 4, 5 and 6 destroyed, 3 and 7
bent, and the camera anchors frame "the 9.6 x 5.6 m hole".  Those are the
ACCEPTANCE CRITERIA, not the construction: this scene sets constraint thresholds
from section properties and then MEASURES the aperture the sim produces.
`--calibrate` sweeps the thresholds and prints the resulting aperture so the
number that ships is one the solver agreed to.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy                                                        # noqa: E402
from mathutils import Euler, Matrix, Vector                       # noqa: E402
import numpy as np                                                # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim"),
           os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
import fracture as FR                                             # noqa: E402
import shardmesh as SM                                            # noqa: E402

T0 = time.time()
plan_for_sag = {}


def log(msg):
    print("[breach %7.1fs] %s" % (time.time() - T0, msg))
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
#  SOLVER SETTINGS.  Every one of these has a reason and a failure mode.
# --------------------------------------------------------------------------- #
SUBSTEPS = 8            # 240 Hz x 8 = 1,920 Hz integration.  A 12 mm shard at
                        # 16 m/s moves 8 mm per substep at this rate, i.e. less
                        # than its own thickness, which is the condition for not
                        # tunnelling through the floor.
SOLVER_ITER = 24        # the default 10 leaves a 3,000-body pile visibly soft
MARGIN = 0.00015        # 0.15 mm.  BLENDER'S DEFAULT IS 0.040 m, which is THREE
                        # AND A HALF TIMES the thickness of this glass: every
                        # shard would rest 40 mm off its neighbour and the wall
                        # would look like a cloud before anything hit it.
                        # It must ALSO be smaller than `shardmesh.KERF_M`, or
                        # the margin re-creates exactly the initial overlap the
                        # kerf exists to remove.  0.15 vs 0.40 mm leaves 0.5 mm
                        # of real air between neighbours.
                        # This is the single most important number in the file,
                        # and the still test is what proves it.
FRICTION_GLASS = 0.32
REST_GLASS = 0.14       # glass on concrete barely bounces; it skitters
FRICTION_ALU = 0.45
REST_ALU = 0.10
CAR_FRICTION = 0.55     # THE CAR PROXY'S SURFACE.  Kept at what shipped so
                        # that nothing in this file changes under its own
                        # steam; it is exposed as `--car-friction` because it
                        # is the ONLY material constant in this scene that is
                        # not derived from anything, and it is the second
                        # highest in the file -- above aluminium-on-anything
                        # and just under concrete.  Painted composite is not
                        # grippier than aluminium.  See R2-385.
DAMP_LIN, DAMP_ANG = 0.02, 0.06

# --------------------------------------------------------------------------- #
#  AIR (R2-388).  The one force in this problem that is missing entirely.
# --------------------------------------------------------------------------- #
#  A rigid-body solver has no air in it, and this scene throws 730 kg of glass
#  and aluminium down a forecourt at 16 m/s.  At that speed the drag on a
#  mullion segment is the same order as its own weight, and R2-384 measured the
#  car dragging one along its deck at 8.81 m/s2 -- a force air alone would have
#  cancelled.  Leaving it out is not conservative; it is the reason the debris
#  neither sheds nor stops.
#
#  NOTHING HERE IS CHOSEN.
#    rho          1.225 kg/m3, ISA sea level
#    Cd           1.17, a flat plate normal to the flow (textbook)
#    A_proj       Cauchy: the mean projected area of a CONVEX body over all
#                 orientations is exactly S/4.  S is summed off the body's OWN
#                 collision mesh, so it is the same geometry Bullet collides
#                 with and not an estimate of it.
#    v_ref        the car's speed where its nose meets the glass, 16.398 m/s.
#                 It is the only speed in this problem that was not chosen by
#                 anybody: it falls out of `world/car_anim_measured.json`.
#
#  WHY A LINEARISATION, SAID PLAINLY.  Real drag is quadratic and Blender's
#  rigid body offers only `linear_damping`, an exponential rate.  So the drag
#  is linearised ABOUT v_ref: it is exact at 16.4 m/s, over-states below it and
#  under-states above it.  That is the honest direction for this defect --
#  the bodies that travel too far are the ones near v_ref, and the ones the
#  linearisation over-damps are moving at walking pace.
#
#  AND THE SCALING IS RIGHT, WHICH A FORCE FIELD'S WOULD NOT BE.  Blender's
#  DRAG effector applies the same FORCE to every body regardless of size, i.e.
#  an acceleration inversely proportional to mass -- exactly backwards for
#  debris of one thickness, whose area is proportional to its mass.  Per-body
#  `linear_damping` gives force proportional to m*v, which for constant
#  thickness is force proportional to area.  That is why this is a per-body
#  damping and not a field.
RHO_AIR = 1.225
CD_PLATE = 1.17
AIR_DRAG = False            # set from --air-drag
AIR_VREF = 0.0              # set in build() from the car itself


def air_damping(surface_area_m2, mass_kg):
    """Blender's `linear_damping` for a body of this surface area and mass.

    Blender/Bullet apply v *= (1 - d)^dt per substep, so d is one minus the
    per-second survival factor: d = 1 - exp(-lambda).
    """
    if not AIR_DRAG or mass_kg <= 0.0 or surface_area_m2 <= 0.0:
        return DAMP_LIN
    a_proj = 0.25 * surface_area_m2                       # Cauchy
    lam = 0.5 * RHO_AIR * CD_PLATE * a_proj * AIR_VREF / mass_kg
    return float(min(0.99, max(DAMP_LIN, 1.0 - math.exp(-lam))))
SLEEP_LIN, SLEEP_ANG = 0.010, 0.030      # m/s and rad/s

# Constraint breaking thresholds.  Bullet's threshold is an IMPULSE budget, not
# a force, so these are calibrated (see --calibrate) from a starting point that
# is at least dimensionally motivated:
#   glass edge bite: 16 mm of 11.5 mm laminate under a pressure plate fails in
#   bending at a few hundred N per 100 mm of edge; the shard masses are grams to
#   kilograms, so the impulse that frees one is small.
THRESH_GLASS_EDGE = 2.5
THRESH_PVB = 0.9        # the interlayer tears at a much lower impulse than the
                        # glass edge but at a much larger displacement, which is
                        # why it is a spring and not a fixed joint
# THE MULLION THRESHOLDS (R2-092), AND WHY THEY ARE THE SECOND PARAMETER THE
# WALL OPENS
# ON.  `t_bond_per_m` decides whether the glass leaves.  THESE decide whether
# the opening is wider than the car.  Across a 40x sweep of the bond threshold
# (4000, 1000, 400, 200, 100) mullions 3, 4, 6 and 7 never moved more than
# 45 mm; only mullion 5, which the car strikes head-on at y = 0, responded at
# all.  The bond sweep alone therefore could never widen the hole past the bay
# it hit, and every attempt to open the wall by moving the bond alone was
# pulling on the wrong lever.
#
# THE DIMENSIONAL CHECK THAT CONDEMNS 900/1400.  Blender hands
# `breaking_threshold` to Bullet's setBreakingImpulseThreshold, which compares
# it against the impulse applied in ONE substep.  At 240 Hz x 8 substeps a
# threshold T is a sustained force of T x 1920 N.  So 900 = 1.73 MN and
# 1400 = 2.69 MN.  The real member is a 75 x 160 mm 6063-T6 extrusion: it
# fails in bending at roughly 30 kN (T = 16) and its base studs go in shear at
# roughly 200 kN (T = 104).  The shipped numbers were 55x and 13x too strong —
# not a tuned value, a value that had never been converted into units.
#
# WHAT IT COSTS THE NULL: NOTHING.  Over 480 wake-all frames with no car, the
# null bake at 40/120 is BIT-IDENTICAL to the same bake at 900/1400 on every
# statistic — the frame bodies move 0.175 mm under dead load, so these
# thresholds are never approached.  The bracket is clean and it is measured:
# 15/50 breaks the null (the wall begins to shed itself, bay 7 sag 200 px), and
# 40/120 sits a comfortable 3x above that.  See sim/tmp/{n1,n2}.json.
THRESH_MULLION_JOINT = 40.0      # segment-to-segment, 6063-T6, 0.075 x 0.160
                                 # = 76.8 kN sustained.  Was 900 = 1.73 MN.
THRESH_MULLION_BASE = 120.0      # the anchor studs into the slab
                                 # = 230 kN sustained.  Was 1400 = 2.69 MN.
# THE TRANSOM THRESHOLD (R2-281).  THE THIRD SURVIVOR OF R2-092'S SWEEP.
# ---------------------------------------------------------------------
# R2-092 converted `THRESH_MULLION_JOINT` and `THRESH_MULLION_BASE` into units
# and left this one and the head constraint alone.  260 is 260 x 1920 =
# **499 kN** and the comment on the line names the fastener that is supposed to
# carry it: `wall_iface`'s screw port SP1, "M6 self-tapper, 6.0 mm nominal,
# cuts its own thread; 40 mm minimum engagement", TWO of them per transom end
# (counted off `transom_landings`, 90 mm apart at all 33 stations).
#
# You do not need the arithmetic to see it is wrong: the same block priced the
# mullion's cast-in anchor studs at 120.  260 is TWO SELF-TAPPING SCREWS MORE
# THAN TWICE AS STRONG AS THE ANCHORS IN THE SLAB.
#
# The arithmetic, in `sim/frame_thresholds.py`, which runs outside Blender so
# it can be checked without a 2 h 25 m bake.  Three modes, smallest governs:
#   screw shear   0.60 x 700 MPa (A2-70, EN 1993-1-8 alpha_v through the
#                 thread) x 20.12 mm^2 (M6 A_s) = 8 450 N x 2 =  16 901 N
#   thread strip  FED-STD-H28 internal shear area 659.9 mm^2, reduced to 80.0 %
#                 because SP1 is an OPEN race (5.0 mm mouth on an 8.5 mm bore
#                 = 72.1 deg of circumference missing), x 152 MPa 6063-T6
#                 ultimate shear x 2                          = 160 463 N
#   bearing       6.0 x 40.0 mm x 0.80 x 1.5 x 241 MPa x 2    = 138 785 N
# Screw shear governs at **16.90 kN**, and T = 16 901 / 1920 = **8.80**.
# The shipped 260 is **29.5x** that.
#
# The previous estimate of this joint was "~15 kN, call it T = 8" and was
# stated as engineering judgement.  It was right to within 13 %.  What is new
# here is that the number now comes from the declared grade and the declared
# engagement rather than from a feel for the fastener, and that the two modes
# that DON'T govern have been computed rather than dismissed -- the open-race
# reduction in particular was the one that could have made the aluminium
# govern instead, and it does not: 160 kN against 17 kN.
#
# WHAT IS STILL JUDGEMENT, stated so it can be argued with:
#   * the shear plane passes through the thread, not a plain shank.  A plain
#     shank would give 23.75 kN, T = 12.4.
#   * no flute reduction: a thread-CUTTING screw's flutes are at the lead, not
#     at the joint face.  A 15 % allowance would give 14.37 kN, T = 7.5.
#   * shear, not tension, is the scalar that stands for all six DOF of a FIXED
#     constraint.  The pair's tensile capacity is 28.2 kN, so this is the
#     conservative end.
# The derived value therefore sits in a defensible band of T = 7.5 .. 12.4 and
# 8.8 is what the declared numbers give with no allowances either way.
THRESH_TRANSOM = 8.8             # two M6 self-tappers into SP1 = 16.90 kN.
                                 # Was 260 = 499 kN (R2-281).
# THE BOND.  Every pair of shards that shares boundary is joined, and the joint
# is as strong as the glass across that boundary — so the threshold is PER METRE
# of shared edge, not per pair.  This is the constraint set that makes the crack
# PROPAGATE instead of appearing: the impact breaks what it can reach, those
# shards load their neighbours, and the aperture is whatever survives.
# Without it a pre-fractured wall is a stack of loose tiles; see
# `fracture.adjacency`'s note and the wake-all null control.
# CALIBRATED, not guessed.  40.0 was a dimensional guess and it was ~100x too
# low: the wake-all null control (no car in the scene at all) shed 1,287 of
# 3,796 shards under gravity alone.  4000 stopped that, and 4000 is what
# shipped — but 4000 BOUGHT THE NULL WITH THE PICTURE, and it did not even buy
# the null.  Over the same 480 wake-all frames the shipped 4000 has a MEDIAN
# displacement of 15.21 mm against 100's 8.48, and 264 shards over 50 mm
# against 100's 5.  It is WORSE on the wall as a whole.  All 4000 buys is the
# binary "nothing over 0.25 m", and it buys that by making the glass
# unbreakable, which is the exact failure mode "a null that passes because
# nothing can move".  A stiffer constraint network is HARDER for 24
# sequential-impulse iterations to satisfy, not easier — see `null_verdict`'s
# `mobility` field, which exists so that this can never again be invisible.
#
# AND THAT SENTENCE IS NOW MEASURED, NOT ASSERTED — R2-199, THE BLOW-UP.
# ---------------------------------------------------------------------
# `sim/tmp/bu1..bu9.json` characterised two clusters of ejected shards: A, 480
# shards to 137.05 m/s at sim frames ~170-179, and B, 348 shards to 106.5 m/s
# at ~240-259, cluster B with NO measurable contact — p50 distance to the
# nearest car proxy part 1.02 m, nothing within 10 mm of a static surface,
# nearest neighbour 15 mm.  Cluster B was left open and undiagnosed.
#
# **BOTH CLUSTERS BELONG TO A BAKE THAT IS NOT THE ONE IN THE FILM.**  bu1..bu9
# ran at 19:36-19:46 on `sim/tmp/breach_bake.npz` — bond 4000, mullion
# 900/1400, the SUPERSEDED config.  `breach_full_m1.npz` (22:28, bond 100,
# mullion 40/120) is what `apply_breach` keyed, and the identity is not an
# inference: the shipped film table's last frame is **bit-identical** to
# `breach_full_m1`'s last frame (max |diff| = 0 m) and **626.781 m** from
# `breach_bake`'s.  Measured on the two bakes with one script, same method:
#
#     bond_per_m                 4000        100
#     shards over 60 m/s          828          7
#     peak speed                137.05     110.41  m/s
#     cluster A                   480          0
#     cluster B                   348          0
#
# Every other input is identical — same fracture plan, same seed, 3,796 shards,
# 12,756 bonds, 641 glass edges, 539 PVB, 14,075 constraints — so the bond and
# mullion thresholds are the only independent variable and this is a controlled
# experiment that had already been run and never read across.
#
# WHY, AND IT IS NOT THE STORY THAT LOOKED OBVIOUS.  The predicted mechanism
# was a stretched joint slinging a shard back: it is REFUTED.  At peak-1 the
# hot shards' PVB partners are stretched a median of 1.4 mm with **0.0 %** over
# the 45 mm limit, and their bonded neighbours 1.9 mm with **0.0 %** over
# 100 mm.  Nothing is stretched, nothing is touching, and one sim frame later
# the shard is doing 137 m/s backwards.  The second prediction — a fixed
# breaking IMPULSE, so v = J/m — is refuted too, and by its own controls:
# `m * v_peak` for cluster B has a median of 0.834 kg m/s, temptingly close to
# THRESH_PVB = 0.9, but the ordinary population sits at 0.616 (ratio 1.34, not
# the 5x predicted) and the log v vs log m slope over the hot set is **-0.017,
# r = -0.06** — no mass dependence at all — while the ORDINARY shards show
# -0.358, r = -0.80.  Reported as failing rather than dropped.
#
# What survives is the plain reading, and it is the sentence above: at 4000 a
# bond's cap is a median **168 kg m/s**, which for the median 14.98 g shard is
# **11,215 m/s** of headroom.  The network therefore never sheds a constraint,
# stays fully connected and over-determined, and the residual the 24 iterations
# cannot satisfy leaves as velocity.  At 100 the same cap is 4.2 kg m/s, bonds
# break, the network relaxes, and 828 ejections become 7.
#
# So cluster B is closed as a defect of the superseded config.  The 7 that
# remain at bond 100 are a DIFFERENT mechanism and are the stretched-joint case
# the prediction described: 66.7 % of them are over the PVB's 45 mm limit at
# peak-1 (p50 stretch 105 mm) against 3.6 % of ordinary shards.  Seven shards,
# and the freeze is off camera, so they are logged rather than chased.
#
# THE RESIDUAL IS STILL OPEN (R2-097).  At 100 the wake-all null loses 3 of
# 3,796 and the panes that stay sag 11.5 px against a 1 px criterion.  It also
# missed that criterion at 4000 (10.75 px) and it has never met it at any
# threshold.  That is a SOLVER_ITER / SUBSTEPS defect in a 14,075-constraint
# island, not a threshold defect, and it is unpriced: the old >=40 h estimate
# was chasing a bay-2 figure that `camera_ranges` had inflated 6.5x.
THRESH_BOND_PER_M = 100.0

GLASS_X_IN, GLASS_X_OUT = 14.955, 14.9665


# --------------------------------------------------------------------------- #
#  small helpers
# --------------------------------------------------------------------------- #

def new_mesh_obj(name, V, F, coll, origin=(0, 0, 0), mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [list(f) for f in F])
    me.validate(verbose=False)
    me.update()
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = tuple(origin)
    coll.objects.link(ob)
    return ob


def _add_box_to_mesh(ob, lo, hi):
    """Append a second box to an existing object's mesh, in WORLD coordinates.

    Used to give one rigid body two disjoint lumps — a mullion's extrusion and
    its pressure plate, with the glazing pocket between them.  The body's
    collision shape must therefore be COMPOUND or MESH, not CONVEX_HULL: a
    convex hull of the two lumps would fill the pocket straight back in and
    reintroduce the very penetration this exists to remove.
    """
    import bmesh
    lo = np.asarray(lo, float) - np.asarray(ob.location, float)
    hi = np.asarray(hi, float) - np.asarray(ob.location, float)
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    vs = [bm.verts.new((float(x), float(y), float(z)))
          for x in (lo[0], hi[0]) for y in (lo[1], hi[1])
          for z in (lo[2], hi[2])]
    bm.verts.ensure_lookup_table()
    for f in ([0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
              [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]):
        bm.faces.new([vs[i] for i in f])
    bm.to_mesh(me)
    bm.free()
    me.update()
    # the second lump is a collider too, and the penetration gate must see it —
    # the pressure plate sits 3.5 mm in front of the glass and that clearance is
    # exactly the kind of number nobody checks until it is negative
    BOX_COLLIDERS.append((ob.name + "_plate",
                          np.asarray(lo, float) + np.asarray(ob.location,
                                                             float),
                          np.asarray(hi, float) + np.asarray(ob.location,
                                                             float)))
    return ob


def box_obj(name, lo, hi, coll, mat=None):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    c = 0.5 * (lo + hi)
    V = np.array([[x, y, z] for x in (lo[0] - c[0], hi[0] - c[0])
                  for y in (lo[1] - c[1], hi[1] - c[1])
                  for z in (lo[2] - c[2], hi[2] - c[2])], float)
    F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
         [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    ob = new_mesh_obj(name, V, F, coll, origin=c, mat=mat)
    BOX_COLLIDERS.append((name, lo.copy(), hi.copy()))
    return ob


def simple_mat(name, base, rough=0.2, metal=0.0, trans=0.0, ior=1.52):
    """A minimal but not dishonest shader.  The film's real glass and anodising
    live in `world/items/`; this scene exists to be SIMULATED and to be LOOKED
    AT frame by frame, and both need the glass to refract rather than be grey.

    Every socket is addressed BY NAME.  Blender 5.2 moved Principled `Normal`
    from index 5 to 6 and an index-addressed bump chain lands silently in
    `Thin Wall`, rendering a plausible flat surface that is wrong.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = tuple(base) + (1.0,)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = trans
    if "IOR" in b.inputs:
        b.inputs["IOR"].default_value = ior
    return m


# --------------------------------------------------------------------------- #
#  RIGID BODIES AND CONSTRAINTS, IN BATCHES.
#
#  `bpy.ops.rigidbody.object_add` costs 22.8 ms per call and `constraint_add`
#  costs 43.2 ms, MEASURED on this box, and both get worse as the scene fills
#  because each one runs a depsgraph update over everything already in it.  At
#  3,000 shards and 1,000 constraints that is not a slow build, it is an
#  unfinishable one — the first attempt was still inside the operator loop four
#  minutes in with 175 MB resident and nothing to show.
#
#  Two fast paths, both measured against the operators they replace:
#    * `rigidbody.objects_add` (PLURAL) does 1,200 objects in 0.21 s and the
#      per-body settings are then plain property writes: 0.01 s for 1,200.
#    * a constraint empty COPIES with its `rigid_body_constraint` intact, so one
#      operator call makes the template and `obj.copy()` makes the other 899 at
#      0.09 ms each.  500x.
#
#  The copy path is only safe because the copy is linked into the SAME
#  `rigidbody_world.constraints` collection; `_check_world()` asserts the counts
#  at the end rather than assuming it worked.
# --------------------------------------------------------------------------- #

WAKE_ALL = False
_DRAG_LOG = []
_RB_QUEUE = {"ACTIVE": [], "PASSIVE": []}
_RB_PROPS = {}


def add_rb(ob, kind="ACTIVE", mass=1.0, shape="CONVEX_HULL", friction=0.4,
           rest=0.1, start_asleep=False, kinematic=False):
    """Queue a rigid body.  `flush_rb()` creates them all in two operator
    calls."""
    _RB_QUEUE[kind].append(ob)
    _RB_PROPS[ob.name] = dict(kind=kind, mass=mass, shape=shape,
                              friction=friction, rest=rest,
                              start_asleep=start_asleep, kinematic=kinematic)
    return None


def flush_rb():
    n = 0
    for kind, obs in _RB_QUEUE.items():
        if not obs:
            continue
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.rigidbody.objects_add(type=kind)
        for o in obs:
            o.select_set(False)
        for o in obs:
            p = _RB_PROPS[o.name]
            rb = o.rigid_body
            if rb is None:
                raise RuntimeError("no rigid body on %s after objects_add"
                                   % o.name)
            rb.collision_shape = p["shape"]
            rb.mass = max(p["mass"], 1e-5)
            rb.friction = p["friction"]
            rb.restitution = p["rest"]
            rb.use_margin = True
            rb.collision_margin = MARGIN
            # R2-388: the drag is computed from the body's OWN collision mesh,
            # here, in the one place every body passes through.  `polygons.area`
            # is the closed surface area of the very geometry Bullet uses, so
            # Cauchy's S/4 needs no shape assumption and no table lookup.
            if p["kind"] == "ACTIVE" and AIR_DRAG:
                try:
                    S = float(sum(pl.area for pl in o.data.polygons))
                except AttributeError:
                    S = 0.0
                rb.linear_damping = air_damping(S, rb.mass)
                _DRAG_LOG.append((o.name, S, rb.mass, rb.linear_damping))
            else:
                rb.linear_damping = DAMP_LIN
            rb.angular_damping = DAMP_ANG
            rb.use_deactivation = True
            rb.deactivate_linear_velocity = SLEEP_LIN
            rb.deactivate_angular_velocity = SLEEP_ANG
            rb.use_start_deactivated = bool(p["start_asleep"]) and not WAKE_ALL
            if p["kind"] == "PASSIVE":
                rb.kinematic = bool(p["kinematic"])
            n += 1
    for k in _RB_QUEUE:
        _RB_QUEUE[k] = []
    return n


_CON_TEMPLATE = {}


def _template(kind, coll):
    if kind in _CON_TEMPLATE:
        return _CON_TEMPLATE[kind]
    e = bpy.data.objects.new("CONTPL_%s" % kind, None)
    e.empty_display_size = 0.05
    coll.objects.link(e)
    bpy.context.view_layer.objects.active = e
    e.select_set(True)
    bpy.ops.rigidbody.constraint_add(type=kind)
    e.select_set(False)
    _CON_TEMPLATE[kind] = e
    return e


_CON_QUEUE = []


def add_constraint(name, a, b, coll, kind="FIXED", thresh=None, loc=None,
                   post=None):
    """Queue a constraint.  Deferred because a constraint needs BOTH its bodies
    to exist, and the bodies are created in one batch at the end of the build."""
    _CON_QUEUE.append((name, a, b, coll, kind, thresh, loc, post))
    return None


def flush_constraints():
    made = []
    for (name, a, b, coll, kind, thresh, loc, post) in _CON_QUEUE:
        e = _make_constraint(name, a, b, coll, kind, thresh, loc)
        if post is not None:
            post(e.rigid_body_constraint)
        made.append(e)
    del _CON_QUEUE[:]
    # the templates are constraint empties with no bodies; leaving them in the
    # world would be 2 dangling constraints and a solver warning per bake
    for kind, tpl in list(_CON_TEMPLATE.items()):
        bpy.data.objects.remove(tpl, do_unlink=True)
        del _CON_TEMPLATE[kind]
    return made


def _make_constraint(name, a, b, coll, kind="FIXED", thresh=None, loc=None):
    tpl = _template(kind, coll)
    e = tpl.copy()
    e.name = name
    e.empty_display_size = 0.05
    e.location = tuple(loc if loc is not None else a.location)
    # `Object.copy()` in 5.x carries the source's collection membership, so both
    # links have to be guarded or the second one raises.
    if e.name not in coll.objects:
        coll.objects.link(e)
    rbc = bpy.context.scene.rigidbody_world.constraints
    if rbc is not None and e.name not in rbc.objects:
        rbc.objects.link(e)
    c = e.rigid_body_constraint
    if c is None:
        raise RuntimeError("the copied empty %s carries no constraint" % name)
    c.object1, c.object2 = a, b
    c.disable_collisions = False
    if thresh is not None:
        c.use_breaking = True
        c.breaking_threshold = float(thresh)
    return e


# --------------------------------------------------------------------------- #
#  THE SCENE
# --------------------------------------------------------------------------- #

def wipe():
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for d in (bpy.data.meshes, bpy.data.materials, bpy.data.actions):
        for x in list(d):
            d.remove(x)


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def build(args):
    global WAKE_ALL
    WAKE_ALL = bool(getattr(args, "wake_all", False))
    wipe()
    sc = bpy.context.scene
    # The rigid body world has to exist BEFORE any constraint empty is made:
    # `_make_constraint` links its copies straight into
    # `rigidbody_world.constraints`, and a copy that is not in that collection
    # is an empty with settings nobody reads.
    if sc.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    car = BL.Car()
    ok, why = car.identity_ok()
    if not ok:
        raise SystemExit("REFUSING: %s.  The sim must be driven by the car the "
                         "film renders." % why)
    log("car identity ok: %s" % why)

    # R2-388: the air's reference speed is the car's own speed where its nose
    # reaches the glass -- read off the measured animation, not chosen here.
    global AIR_DRAG, AIR_VREF
    AIR_DRAG = getattr(args, "air_drag", "off") == "derived"
    _fi = car.impact_frame()
    _wt = np.array([car.clock.world_t(_fi - 0.5), car.clock.world_t(_fi + 0.5)])
    _l, _ = car.at_world_t(_wt)
    AIR_VREF = float(np.linalg.norm(_l[1] - _l[0]) / (_wt[1] - _wt[0]))
    log("air drag: %s, v_ref %.4f m/s (car at the glass plane, film f%.3f)"
        % ("DERIVED" if AIR_DRAG else "OFF", AIR_VREF, _fi))

    t0, t1, nsim = BL.sim_window(car)
    if args.frames:
        nsim = min(nsim, int(args.frames))
        t1 = t0 + (nsim - 1) / float(BL.SIM_FPS)
    wts = BL.sim_frame_world_t(t0, nsim)
    sc.render.fps = BL.SIM_FPS
    sc.render.fps_base = 1.0
    sc.frame_start, sc.frame_end = 1, nsim
    log("world window %.4f .. %.4f s, %d sim frames at %d Hz"
        % (t0, t1, nsim, BL.SIM_FPS))

    C_glass = coll("SIM_Glass")
    C_frame = coll("SIM_Frame")
    C_static = coll("SIM_Static")
    C_car = coll("SIM_Car")
    C_con = coll("SIM_Constraints")

    M_glass = simple_mat("SIM_Glass", (0.86, 0.91, 0.89), rough=0.03,
                         trans=1.0, ior=1.52)
    M_alu = simple_mat("SIM_Alu", (0.35, 0.356, 0.362), rough=0.30, metal=1.0)
    M_conc = simple_mat("SIM_Conc", (0.34, 0.34, 0.33), rough=0.75)
    M_car = simple_mat("SIM_Car", (0.05, 0.06, 0.09), rough=0.35)

    # ---- 1. static ground ------------------------------------------------- #
    # The showroom floor (round 1's, top z = 0.000 exactly) and the forecourt
    # outside it, which is the same plane -- that coincidence is the scale key
    # for the whole building and it is why shards slide straight out of the hole.
    floor_in = box_obj("SIM_FloorIn", (-15.0, -11.0, -0.30), (14.94, 11.0, 0.0),
                       C_static, M_conc)
    floor_out = box_obj("SIM_FloorOut", (15.0, -14.0, -0.30), (46.0, 14.0, 0.0),
                        C_static, M_conc)
    # THE SILL, AS A POCKET AND NOT A BLOCK.
    #
    # `glazing_pockets()` is explicit that THE PANE IS BIGGER THAN THE HOLE:
    # 22.5 mm of every edge is hidden, 16.0 of it clamped under the pressure
    # plate.  Modelled as one solid box from z = 0 to 0.110 the sill therefore
    # OCCUPIES 22.5 mm of every bottom-edge shard, and 582 clamped shards start
    # the sim penetrating static geometry by twenty times their own collision
    # margin.  The wake-all null control found it: with no car in the scene at
    # all the wall left at a peak of 151 m/s and 1,891 of 2,987 shards were
    # "gone".  Bonding the shards to each other had halved the number and hidden
    # the cause.
    #
    # So the sill is built as the two pieces it actually is — the pocket floor
    # BEHIND the glass line and the pressure-plate upstand IN FRONT of it — with
    # the glazing pocket itself (x 14.945 .. 14.970, z below 0.0865) left open
    # for the glass to sit in.  The capture is then mechanical: the glass is
    # between the isolator and the plate, touching neither at frame 1.
    #
    # AND IT SPANS BETWEEN THE MULLIONS, NOT THROUGH THEM.  A sill box running
    # the full width in the mullion's own x band puts every mullion foot 88 mm
    # inside it, and the head beam puts every head 110 mm inside that.  The
    # wake-all null control found it as a mullion travelling 0.709 m in 0.225 s
    # — FASTER THAN FREE FALL, which is the signature of an ejection rather than
    # a collapse.  The penetration gate did not see it because the gate only
    # tested SHARDS; it now tests every body.
    W0 = BL.wall_iface()
    _st = W0["stations"]
    _hs = 0.5 * W0["section"]["sightline_m"]
    sill_parts, head_parts = [], []
    _spans = ([(-11.05, _st[0]["y"] - _hs)]
              + [(_st[i]["y"] + _hs, _st[i + 1]["y"] - _hs)
                 for i in range(len(_st) - 1)]
              + [(_st[-1]["y"] + _hs, 11.05)])
    for _i, (_y0, _y1) in enumerate(_spans):
        if _y1 - _y0 < 1e-6:
            continue
        sill_parts.append(box_obj("SIM_Sill%02d" % _i, (14.84, _y0, 0.0),
                                  (14.945, _y1, 0.110), C_static, M_alu))
        sill_parts.append(box_obj("SIM_SillPlate%02d" % _i, (14.970, _y0, 0.0),
                                  (15.0, _y1, 0.110), C_static, M_alu))
        sill_parts.append(box_obj("SIM_SillPocket%02d" % _i,
                                  (14.945, _y0, 0.0),
                                  (14.970, _y1, 0.0865), C_static, M_alu))
        head_parts.append(box_obj("SIM_Head%02d" % _i, (14.84, _y0, 6.1125),
                                  (14.945, _y1, 6.30), C_static, M_alu))
        head_parts.append(box_obj("SIM_HeadPlate%02d" % _i,
                                  (14.970, _y0, 6.1125),
                                  (15.0, _y1, 6.30), C_static, M_alu))
        head_parts.append(box_obj("SIM_HeadPocket%02d" % _i,
                                  (14.945, _y0, 6.1135),
                                  (14.970, _y1, 6.30), C_static, M_alu))
    # the two the constraints attach to: a thin structural bracket BEHIND the
    # mullion line, clear of every mullion body (which stops at x = 14.945)
    sill = box_obj("SIM_SillBracket", (14.80, -11.05, 0.0),
                   (14.84, 11.05, 0.110), C_static, M_alu)
    head = box_obj("SIM_HeadBracket", (14.80, -11.05, 6.1125),
                   (14.84, 11.05, 6.30), C_static, M_alu)
    # the threshold strip the ribbon starts on, x 14.94 .. 15.0, so nothing
    # falls down a 60 mm slot at the breach plane
    thr = box_obj("SIM_Threshold", (14.94, -14.0, -0.30), (15.0, 14.0, 0.0),
                  C_static, M_conc)
    # THE OUTFIELD, AND WHY THE FLOOR HAD AN EDGE TO FALL OFF (R2-197).
    #
    # `SIM_FloorIn` stops at x 14.94 / |y| 11 and `SIM_FloorOut` at x 46 /
    # |y| 14.  The field's maximum horizontal travel in the shipped 6.9 s bake
    # is **653 m**.  So 70 bodies ran off the end of the static ground and were
    # still in FREE FALL at the last key, the worst 154.6 m down at 108.2 m/s —
    # and because apply_breach extrapolates CONSTANT, they then hang there,
    # motionless, 154 m underground, for the remaining 1,813 frames of the take.
    #
    # This was not tunnelling.  Measured at the sim frame each one first crosses
    # z = 0: 55 of the 70 are OUTSIDE the union of the three slabs above (28
    # beyond x 46, 27 past |y| 14, 1 west of x -15), crossing at a median
    # -0.34 m/s — a body walking off a ledge, not a body punching through one.
    # The other 15 cross inside the footprint and are the real tunnelling
    # residue, at 1.9 % of what the edge costs.
    #
    # The outfield is sized from that 653 m with a 1.5x margin, and it is a
    # SINGLE BOX so it costs one broadphase proxy.  It sits 1 mm below the
    # floor slabs' top so it can never win a contact against them inside the
    # showroom.  `motion_report` counts what lands on it, because a catch slab
    # that silently absorbs a different bug is worse than no catch slab.
    OUTFIELD_M = 1000.0
    out_field = box_obj("SIM_Outfield", (-OUTFIELD_M, -OUTFIELD_M, -0.60),
                        (OUTFIELD_M, OUTFIELD_M, -0.001), C_static, M_conc)
    for ob in ([floor_in, floor_out, thr, sill, head, out_field]
               + sill_parts + head_parts):
        add_rb(ob, "PASSIVE", shape="BOX", friction=0.62, rest=0.06)
    log("static ground built")

    # ---- 2. the frame ----------------------------------------------------- #
    W = BL.wall_iface()
    S = W["section"]
    st = W["stations"]
    bs = {b["uid"]: b["beat3"] for b in W["breach_state"]}
    NSEG = args.mullion_segments
    mull = {}                    # uid -> [segment objects, bottom first]
    for r in st:
        uid, y = r["uid"], r["y"]
        z0, z1 = r["foot_z"], r["head_z"]
        active = bs[uid] in ("destroyed", "bent_stub")
        # THE MULLION IS TWO BOXES, NOT ONE.  Same defect as the sill: a solid
        # 14.840 .. 15.000 box fills the glazing pocket the glass lives in, and
        # every clamped shard starts 22.5 mm inside it.  The extrusion stops at
        # the rebate face (14.945) and the cap and pressure plate start at
        # 14.970; between them is the pocket, which is where the glass is.
        # Both pieces are ONE rigid body per segment, joined rigidly, because a
        # pressure plate screwed to a mullion is one structural member.
        xb0, xb1 = S["body_back_x"], S["rebate_face_x"]
        xf0, xf1 = S["plate_back_x"], S["cap_face_x"]
        segs = []
        n = NSEG if active else 1
        hs = 0.5 * S["sightline_m"]
        for k in range(n):
            a = z0 + (z1 - z0) * k / n
            b = z0 + (z1 - z0) * (k + 1) / n
            # TWO BODIES, not one body with two lumps.  Blender's COMPOUND
            # collision shape takes its geometry from an object's CHILDREN; on
            # an object with none it is degenerate, and the wake-all null went
            # from 1,891 shards leaving on their own to 220 but kept a 188 m/s
            # peak because the mullions had no usable collider.  Two convex
            # boxes joined by a FIXED constraint at ten times the mullion's own
            # joint threshold is the same member, and it is a shape Bullet can
            # actually integrate.
            ob = box_obj("MUL%02d_S%02d" % (uid, k),
                         (xb0, y - hs, a), (xb1, y + hs, b), C_frame, M_alu)
            pl = box_obj("MUL%02d_S%02d_P" % (uid, k),
                         (xf0, y - hs, a), (xf1, y + hs, b), C_frame, M_alu)
            # a real 6063-T6 mullion is 4.7 kg/m of metal, not a solid billet
            m = 4.7 * (b - a)
            if active:
                add_rb(ob, "ACTIVE", mass=0.72 * m, shape="BOX",
                       friction=FRICTION_ALU, rest=REST_ALU,
                       start_asleep=True)
                add_rb(pl, "ACTIVE", mass=0.28 * m, shape="BOX",
                       friction=FRICTION_ALU, rest=REST_ALU,
                       start_asleep=True)
                add_constraint("CON_MUL%02d_S%02d_P" % (uid, k), ob, pl, C_con,
                               thresh=args.t_mullion_joint * 10.0,
                               loc=(0.5 * (xb1 + xf0), y, 0.5 * (a + b)))
            else:
                add_rb(ob, "PASSIVE", shape="BOX", friction=FRICTION_ALU,
                       rest=REST_ALU)
                add_rb(pl, "PASSIVE", shape="BOX", friction=FRICTION_ALU,
                       rest=REST_ALU)
            segs.append(ob)
        mull[uid] = segs
        if active:
            # base anchor, then segment-to-segment
            add_constraint("CON_MUL%02d_BASE" % uid, segs[0], sill, C_con,
                           thresh=args.t_mullion_base * (
                               3.0 if bs[uid] == "bent_stub" else 1.0),
                           loc=(xf1, y, z0))
            for k in range(len(segs) - 1):
                z = z0 + (z1 - z0) * (k + 1) / n
                add_constraint("CON_MUL%02d_J%02d" % (uid, k), segs[k],
                               segs[k + 1], C_con,
                               thresh=args.t_mullion_joint * (
                                   3.0 if bs[uid] == "bent_stub" else 1.0),
                               loc=(xf1, y, z))
            # THE HEAD IS A MOVEMENT JOINT, NOT A HANGER.  R2-268.
            #
            # As shipped this is a FIXED constraint at t_mullion_joint * 0.5 =
            # 20, which at 240 Hz x 8 substeps is 38.4 kN sustained.  What it
            # carries once the car has taken mullion 5's bottom 1.55 m out is
            # 4.65 m of extrusion at 4.7 kg/m plus half of six transom stubs:
            # 396 N.  NINETY-SEVEN TIMES the load, across a joint that
            # `wall_iface` itself records as `head_expansion_gap_m` = 17.2 mm
            # at this very mullion.  A stick curtain wall is BOTTOM-anchored;
            # the head exists so the mullion can grow and shrink without being
            # loaded.  So in the shipped bake six of mullion 5's eight segments
            # hang in the air with nothing under them, all three transoms keep
            # their support, and the film renders an unbroken grid across the
            # hole.
            #
            # `slider` is the physical model: lateral load only.  Lock x and y
            # (wind, in and out), leave z and all rotation free, keep the same
            # breaking threshold for the lateral capacity it really does have.
            #
            # R2-282: `slider` IS NOW THE DEFAULT.  The re-bake is a decision
            # and it has been made; `land_breach.sh`'s stage-0 gate has been
            # moved onto the new set so a bake at the OLD one is now what the
            # pipeline refuses.
            #
            # AND THE THRESHOLD IS DELIBERATELY NOT TOUCHED.  20 stays.  The
            # lateral capacity of a head anchor is not declared anywhere in
            # `wall_iface` -- unlike SP1, which declares its fastener, its
            # grade and its engagement -- so it cannot be derived and will not
            # be invented.  Keeping it means NOTHING THAT FALLS IN THIS BAKE
            # CAN HAVE BEEN BOUGHT BY WEAKENING THE HEAD: the only thing that
            # changed here is the joint's KIND, and that follows from a
            # declared geometric fact (a 17.2 mm expansion gap at this very
            # station, and a gap at all eleven) rather than from a number
            # somebody chose.
            def _slider(c):
                for _ax in ("x", "y"):
                    setattr(c, "use_limit_lin_%s" % _ax, True)
                    setattr(c, "limit_lin_%s_lower" % _ax, 0.0)
                    setattr(c, "limit_lin_%s_upper" % _ax, 0.0)
                c.use_limit_lin_z = False
                for _ax in ("x", "y", "z"):
                    setattr(c, "use_limit_ang_%s" % _ax, False)

            _sl = getattr(args, "head_restraint", "fixed") == "slider"
            add_constraint("CON_MUL%02d_HEAD" % uid, segs[-1], head, C_con,
                           kind="GENERIC" if _sl else "FIXED",
                           thresh=args.t_mullion_joint * 0.5,
                           loc=(xf1, y, z1),
                           post=_slider if _sl else None)
    log("mullions: %d bodies" % sum(len(v) for v in mull.values()))

    # transoms: three full-width rails, bolted into the front screw port
    trans = []
    for zi, z in enumerate(W["transom_landings"]["z"]
                           if isinstance(W.get("transom_landings"), dict)
                           and "z" in W.get("transom_landings", {})
                           else (1.600, 3.100, 4.600)):
        for i in range(len(st) - 1):
            y0, y1 = st[i]["y"], st[i + 1]["y"]
            a, b = mull[st[i]["uid"]], mull[st[i + 1]["uid"]]
            act = (bs[st[i]["uid"]] != "intact" or
                   bs[st[i + 1]["uid"]] != "intact")
            # two lumps again: a transom that spans 14.840 .. 14.976 fills the
            # glazing pocket and puts every shard it crosses inside it
            ob = box_obj("TRN_z%d_b%02d" % (zi, i),
                         (S["body_back_x"], y0 + 0.0375, z - 0.030),
                         (S["rebate_face_x"], y1 - 0.0375, z + 0.030),
                         C_frame, M_alu)
            pl = box_obj("TRN_z%d_b%02d_P" % (zi, i),
                         (S["plate_back_x"], y0 + 0.0375, z - 0.030),
                         (S["cap_face_x"], y1 - 0.0375, z + 0.030),
                         C_frame, M_alu)
            m = 2.9 * (y1 - y0)
            if act:
                add_rb(ob, "ACTIVE", mass=0.7 * m, shape="BOX",
                       friction=FRICTION_ALU, rest=REST_ALU, start_asleep=True)
                add_rb(pl, "ACTIVE", mass=0.3 * m, shape="BOX",
                       friction=FRICTION_ALU, rest=REST_ALU, start_asleep=True)
                add_constraint("CON_TRN%d_%02d_P" % (zi, i), ob, pl, C_con,
                               thresh=args.t_transom * 10.0,
                               loc=(S["rebate_face_x"], 0.5 * (y0 + y1), z))
                for segs, yy in ((a, y0), (b, y1)):
                    tgt = _seg_at(segs, z)
                    add_constraint("CON_TRN%d_%02d_%s" % (zi, i,
                                                          "a" if yy == y0
                                                          else "b"),
                                   ob, tgt, C_con, thresh=args.t_transom,
                                   loc=(S["plate_front_x"], yy, z))
            else:
                add_rb(ob, "PASSIVE", shape="BOX", friction=FRICTION_ALU,
                       rest=REST_ALU)
                add_rb(pl, "PASSIVE", shape="BOX", friction=FRICTION_ALU,
                       rest=REST_ALU)
            trans.append(ob)
    log("transoms: %d" % len(trans))

    # ---- 3. the glass ----------------------------------------------------- #
    plan = FR.load(args.shards)
    rects, roles = plan["rects"], plan["roles"]
    shards = []
    meta = []
    thick = GLASS_X_OUT - GLASS_X_IN
    for bay in sorted(plan["panes"]):
        role = roles[bay]
        if role == "intact":
            continue                      # built, but not as a rigid body
        u0, u1, v0, v1 = rects[bay]
        uidA = bay
        uidB = bay + 1
        for s in plan["panes"][bay]:
            V, F = SM.prism(s["poly"], GLASS_X_IN, GLASS_X_OUT,
                            detail=args.detail, seed=1000 * bay + s["id"])
            org = SM.origin_of(s["poly"], GLASS_X_IN, GLASS_X_OUT)
            nm = "GS_b%02d_%05d" % (bay, s["id"])
            ob = new_mesh_obj(nm, V, F, C_glass, origin=org, mat=M_glass)
            vol = SM.volume(V, F)
            add_rb(ob, "ACTIVE", mass=vol * BL.RHO_GLASS, shape="CONVEX_HULL",
                   friction=FRICTION_GLASS, rest=REST_GLASS, start_asleep=True)
            shards.append(ob)
            meta.append(dict(name=nm, bay=bay, id=s["id"], area=s["area"],
                             volume=vol, mass=vol * BL.RHO_GLASS,
                             origin=org.tolist(), clamped=bool(s["clamped"]),
                             laminated=bool(s["laminated"]),
                             r_impact=s["r_impact"], aspect=s["aspect"]))
        log("bay %d (%s): %d shards" % (bay, role, len(plan["panes"][bay])))

    # the intact panes are ONE passive body each -- they are pre-fractured in
    # the pattern but nothing in this beat touches them, and 439 sleeping bodies
    # that never wake are 439 bodies of solver cost for no picture.
    for bay in sorted(plan["panes"]):
        if roles[bay] != "intact":
            continue
        u0, u1, v0, v1 = rects[bay]
        ob = box_obj("GP_intact_b%02d" % bay, (GLASS_X_IN, u0, v0),
                     (GLASS_X_OUT, u1, v1), C_glass, M_glass)
        add_rb(ob, "PASSIVE", shape="BOX", friction=FRICTION_GLASS,
               rest=REST_GLASS)

    # ---- 4. glass held by the frame, and the PVB -------------------------- #
    by_name = {o.name: o for o in shards}
    n_edge = n_pvb = 0
    cent = {}
    for m in meta:
        cent[m["name"]] = np.array(m["origin"])
    for bay in sorted(plan["panes"]):
        if roles[bay] == "intact":
            continue
        u0, u1, v0, v1 = rects[bay]
        hid = 0.0225
        for s in plan["panes"][bay]:
            nm = "GS_b%02d_%05d" % (bay, s["id"])
            ob = by_name.get(nm)
            if ob is None or not s["clamped"]:
                continue
            c = s["centroid"]
            # which of the four clamped edges is it on?
            d = [(c[0] - u0, "L"), (u1 - c[0], "R"),
                 (c[1] - v0, "B"), (v1 - c[1], "T")]
            d.sort()
            side = d[0][1]
            if side == "L":
                tgt = _seg_at(mull[bay], c[1])
            elif side == "R":
                tgt = _seg_at(mull[bay + 1], c[1])
            elif side == "B":
                tgt = sill
            else:
                tgt = head
            add_constraint("CONG_%s" % nm, ob, tgt, C_con,
                           thresh=args.t_glass_edge,
                           loc=(GLASS_X_IN, c[0], c[1]))
            n_edge += 1
    # THE BONDS: the pane is a solid until its cracks open
    n_bond = 0
    for bay, rows in plan.get("bonds", {}).items():
        if roles.get(bay) == "intact":
            continue
        for (ia, ib, L) in rows:
            a = by_name.get("GS_b%02d_%05d" % (bay, ia))
            b = by_name.get("GS_b%02d_%05d" % (bay, ib))
            if a is None or b is None:
                continue
            add_constraint("CONB_b%02d_%05d_%05d" % (bay, ia, ib), a, b, C_con,
                           thresh=args.t_bond_per_m * L,
                           loc=(0.5 * (a.location[0] + b.location[0]),
                                0.5 * (a.location[1] + b.location[1]),
                                0.5 * (a.location[2] + b.location[2])))
            n_bond += 1
    log("shard-to-shard bonds: %d" % n_bond)

    # PVB: each laminated shard springs to its nearest neighbour in the SAME bay
    for bay in sorted(plan["panes"]):
        if roles[bay] == "intact":
            continue
        ss = plan["panes"][bay]
        cs = np.array([s["centroid"] for s in ss])
        lam = [i for i, s in enumerate(ss) if s["laminated"]]
        for i in lam:
            dd = np.linalg.norm(cs - cs[i], axis=1)
            dd[i] = 1e9
            j = int(np.argmin(dd))
            a = by_name.get("GS_b%02d_%05d" % (bay, ss[i]["id"]))
            b = by_name.get("GS_b%02d_%05d" % (bay, ss[j]["id"]))
            if a is None or b is None:
                continue
            add_constraint("CONP_b%02d_%05d" % (bay, ss[i]["id"]), a, b,
                           C_con, kind="GENERIC_SPRING", thresh=args.t_pvb,
                           loc=(GLASS_X_IN,
                                0.5 * (cs[i][0] + cs[j][0]),
                                0.5 * (cs[i][1] + cs[j][1])),
                           post=_pvb_post)
            n_pvb += 1
    log("queued constraints: %d glass edge, %d bond, %d PVB, %d total"
        % (n_edge, n_bond, n_pvb, len(_CON_QUEUE)))

    # ---- 5. the car ------------------------------------------------------- #
    parts = [] if args.no_car else BL.car_proxy_parts()
    # Blender 5.x SLOTTED actions: `Action.fcurves` is gone.  An action is
    # layers -> strips -> channelbag(slot) -> fcurves, and an object binds to
    # BOTH the action and a slot.  Sharing one action across the 18 proxy parts
    # is the whole reason the car costs 6 curves instead of 108.
    act = bpy.data.actions.new("CAR_PROXY")
    slot = act.slots.new(id_type="OBJECT", name="Object")
    cbag = act.layers.new("L").strips.new(type="KEYFRAME").channelbag(
        slot, ensure=True)
    fcs = []
    for path, n in (("location", 3), ("rotation_euler", 3)):
        for i in range(n):
            fcs.append(cbag.fcurves.new(path, index=i))
    loc, rot = car.at_world_t(wts)
    for i, fc in enumerate(fcs):
        vals = loc[:, i] if i < 3 else rot[:, i - 3]
        fc.keyframe_points.add(count=nsim)
        flat = np.empty(2 * nsim)
        flat[0::2] = np.arange(1, nsim + 1)
        flat[1::2] = vals
        fc.keyframe_points.foreach_set("co", flat)
        # keyframe_new_interpolation_type is NOT honoured by keyframe_insert in
        # 5.2 (71,472 of 71,472 keys came out BEZIER).  foreach_set does not go
        # through it at all, so set the enum on every point and PROVE it by
        # evaluating the curve, below.
        fc.keyframe_points.foreach_set(
            "interpolation", [1] * nsim)          # 1 == LINEAR
        fc.update()

    # ---- 5b.  WITHDRAWING THE BOUNDARY CONDITION  (R2-386) ---------------- #
    #
    # The proxy is a boundary condition for the BREACH.  The car crosses the
    # glass plane at sim frame 145 and its tail clears it 80 frames later; the
    # sim window then runs for another 1,430 frames, over which the AUTHORED
    # animation takes the car 262 m down the forecourt and up to 58.2 m/s.  For
    # all of that the proxy is a sealed, rigid, aerodynamically-null box with
    # infinite mass, and every body it has picked up rides it (R2-384).
    #
    # `--car-collide-until X` stops the proxy colliding once the car's ORIGIN
    # passes world x = X.  It does NOT touch the car's transform: the same six
    # curves drive the same eighteen parts to the same places, and the parts go
    # on being drawn and go on being keyed.  What changes is one boolean.
    #
    # WHICH BOOLEAN, AND WHY THIS ONE.  `sim/tmp/test_rb_enabled.py` puts an
    # active cube on a passive kinematic plate and keys, in turn,
    # `rigid_body.enabled`, `rigid_body.kinematic` and
    # `rigid_body.collision_collections`, then asks the only question that
    # settles it: does the cube fall through?  In Blender 5.2 the first two are
    # NOT honoured per frame -- the cube sits there for all 60 frames -- and
    # only the collision collections work.  So the switch is a move from
    # collision collection 0, which every other body in this scene is in, to
    # collection 1, which nothing is in.
    #
    # The keys go on the SHARED action, so the whole proxy costs two more
    # curves rather than thirty-six, and every part switches on the same frame
    # by construction.
    wd_frame = 0
    until_x = float(getattr(args, "car_collide_until", 0.0) or 0.0)
    if parts and until_x > 0.0:
        past = np.where(loc[:, 0] > until_x)[0]
        if len(past) == 0:
            raise SystemExit(
                "REFUSING: --car-collide-until %.3f is never reached; the car "
                "spans x %.3f .. %.3f over this sim window."
                % (until_x, loc[0, 0], loc[-1, 0]))
        wd_frame = int(past[0]) + 1                # 1-based sim frame
        for idx, before, after in ((0, 1.0, 0.0), (1, 0.0, 1.0)):
            fc = cbag.fcurves.new("rigid_body.collision_collections",
                                  index=idx)
            fc.keyframe_points.add(count=2)
            fc.keyframe_points.foreach_set(
                "co", [1.0, before, float(wd_frame), after])
            fc.keyframe_points.foreach_set("interpolation", [0, 0])  # CONSTANT
            fc.update()
        log("car proxy WITHDRAWS at sim frame %d (car origin x %.3f > %.3f, "
            "world t %.4f, film f%.1f)"
            % (wd_frame, loc[wd_frame - 1, 0], until_x, wts[wd_frame - 1],
               BL.Clock().frame_at_world_t(wts[wd_frame - 1])))

    car_objs = []
    for nm, pts in parts:
        P = np.asarray(pts, float)
        hull_f = _hull_faces(P)
        ob = new_mesh_obj("CARP_%s" % nm, P, hull_f, C_car, origin=(0, 0, 0),
                          mat=M_car)
        ob.animation_data_create()
        ob.animation_data.action = act
        ob.animation_data.action_slot = slot
        add_rb(ob, "PASSIVE", shape="CONVEX_HULL",
               friction=float(getattr(args, "car_friction", CAR_FRICTION)),
               rest=0.05, kinematic=True)
        car_objs.append(ob)
    log("car proxy: %d convex parts on one shared %d-key LINEAR action, "
        "friction %.3f, withdraw %s%s"
        % (len(car_objs), nsim,
           float(getattr(args, "car_friction", CAR_FRICTION)),
           ("sim f%d" % wd_frame) if wd_frame else "never",
           "  [NULL CONTROL: NO CAR]" if args.no_car else ""))

    # ---- 6. the rigid body world ------------------------------------------ #
    n_rb = flush_rb()
    log("rigid bodies created: %d" % n_rb)
    cons = flush_constraints()
    log("constraints created: %d" % len(cons))
    w = sc.rigidbody_world
    w.substeps_per_frame = int(args.substeps)
    w.solver_iterations = int(args.solver_iter)
    w.time_scale = 1.0
    w.point_cache.frame_start = 1
    w.point_cache.frame_end = nsim
    sc.gravity = (0.0, 0.0, -9.81)
    sc.use_gravity = True

    _check_world(sc, info_expect=dict(bodies=n_rb, constraints=len(cons)))
    pen = penetration_gate(shards + list(C_frame.objects)
                           + list(C_static.objects))
    log("penetration gate: %s" % json.dumps(pen, default=float))
    if pen.get("penetrating"):
        raise SystemExit(
            "REFUSING TO BAKE: %d bodies start inside other geometry, worst "
            "%.4f m (%s into %s).  A destruction sim that begins with "
            "penetration measures its own initial condition, not the impact."
            % (pen["penetrating"], pen["worst"][0]["depth_m"],
               pen["worst"][0]["shard"], pen["worst"][0]["into"]))
    info = dict(
        world_t0=t0, world_t1=t1, sim_fps=BL.SIM_FPS, sim_frames=nsim,
        origin_rule=SM.ORIGIN_RULE,
        impact_world_t=car.impact_world_t(),
        impact_film_frame=car.impact_frame(),
        n_shards=len(shards), n_frame_bodies=len(C_frame.objects),
        n_constraints=len(sc.rigidbody_world.constraints.objects),
        n_bodies=len(sc.rigidbody_world.collection.objects),
        substeps=int(args.substeps), solver_iterations=int(args.solver_iter),
        collision_margin=MARGIN,
        thresholds=dict(glass_edge=args.t_glass_edge, pvb=args.t_pvb,
                        mullion_joint=args.t_mullion_joint,
                        mullion_base=args.t_mullion_base,
                        transom=args.t_transom,
                        # R2-282: the head joint's KIND is part of the
                        # configuration, not a build detail.  It goes in the
                        # thresholds block because `land_breach.sh`'s stage-0
                        # gate reads that block and nothing else, and a bake
                        # whose head model is not recorded is a bake whose
                        # frame behaviour cannot be attributed afterwards.
                        head_restraint=getattr(args, "head_restraint",
                                               "fixed"),
                        head=args.t_mullion_joint * 0.5,
                        bond_per_m=args.t_bond_per_m),
        # R2-386.  The proxy's configuration is part of the bake's identity:
        # two bakes at the same thresholds and different proxy settings are
        # different bakes, and a table that does not say which it was cannot
        # be attributed afterwards.  `land_breach.sh`'s stage-0 gate reads
        # `thresholds` by name and ignores keys it does not list, so this
        # block is additive and breaks nothing.
        air_drag=dict(
            mode=getattr(args, "air_drag", "off"),
            rho=RHO_AIR, cd=CD_PLATE, v_ref=AIR_VREF,
            bodies=len(_DRAG_LOG),
            damping_min=min([r[3] for r in _DRAG_LOG], default=None),
            damping_median=float(np.median([r[3] for r in _DRAG_LOG]))
            if _DRAG_LOG else None,
            damping_max=max([r[3] for r in _DRAG_LOG], default=None),
            examples={r[0]: dict(S_m2=round(r[1], 5), mass_kg=round(r[2], 5),
                                 linear_damping=round(r[3], 5))
                      for r in _DRAG_LOG[:3]
                      + [x for x in _DRAG_LOG if x[0] == "MUL05_S02"]}),
        car_proxy=dict(
            friction=float(getattr(args, "car_friction", CAR_FRICTION)),
            collide_until_x=float(getattr(args, "car_collide_until", 0.0)),
            withdraw_sim_frame=int(wd_frame),
            parts=len(car_objs)),
        detail=args.detail,
        penetration_gate=pen,
        shard_meta=meta)
    return info, dict(shards=shards, car=car_objs, frame=list(C_frame.objects),
                      action=act)


def _check_world(sc, info_expect):
    """The batch paths above are fast BECAUSE they bypass the operators, so the
    thing the operators would have guaranteed has to be asserted here."""
    w = sc.rigidbody_world
    if w is None or w.collection is None or w.constraints is None:
        raise SystemExit("REFUSING: no rigid body world / collections")
    nb = len([o for o in w.collection.objects if o.rigid_body is not None])
    nc = len([o for o in w.constraints.objects
              if o.rigid_body_constraint is not None])
    if nb < info_expect["bodies"]:
        raise SystemExit("REFUSING: %d bodies in the world, %d were created"
                         % (nb, info_expect["bodies"]))
    if nc < info_expect["constraints"]:
        raise SystemExit("REFUSING: %d constraints in the world, %d created"
                         % (nc, info_expect["constraints"]))
    dangling = [o.name for o in w.constraints.objects
                if o.rigid_body_constraint is not None and
                (o.rigid_body_constraint.object1 is None or
                 o.rigid_body_constraint.object2 is None)]
    if dangling:
        raise SystemExit("REFUSING: %d constraints have a missing body: %s"
                         % (len(dangling), dangling[:5]))
    log("world check: %d bodies, %d constraints, 0 dangling" % (nb, nc))


BOX_COLLIDERS = []          # (name, lo, hi) in WORLD, filled by box_obj


# Bodies that TOUCH share a face, and a shared face is two float evaluations of
# the same plane: the gate measures 5.7e-7 m of "penetration" at every mullion
# plate sitting on its sill pocket.  10 microns is 0.05 px at the closest a
# shard is ever filmed and four orders below the 88 mm this gate exists to
# catch, so it separates contact from interpenetration without inventing slack.
PEN_TOL_M = 1.0e-5


def penetration_gate(bodies, plan=None, tol=PEN_TOL_M, skip_own=True):
    """NOTHING MAY START INSIDE ANYTHING.

    The wake-all null control caught a wall that left at 151 m/s with no car in
    the scene, and the cause was 582 clamped shards initialised 22.5 mm inside
    the sill and the mullions — their own declared edge bite, modelled as solid
    metal.  A null control is a slow way to find that; this is the fast one, and
    it runs before every bake.

    Exact for boxes: every body's vertices are tested against every registered
    box, in that body's own world placement.  Refuses on any penetration deeper
    than `tol` and names the worst offenders.

    IT TESTS EVERY BODY, NOT JUST THE GLASS.  The first version tested shards
    only, and missed a mullion foot sitting 88 mm inside the sill and a mullion
    head 110 mm inside the head beam — full-width boxes laid across the mullion
    line.  That showed up in the null as a body travelling 0.709 m in 0.225 s,
    FASTER THAN FREE FALL, which is what an ejection looks like and what a
    collapse never does.  A gate that only looks where you already suspect is
    not a gate.

    BUT IT ONLY *REFUSES* ON BODIES THAT CAN MOVE — R2-283.
    ------------------------------------------------------
    R2-197 added `SIM_Outfield`, a 2 km catch slab spanning z -0.60 .. -0.001,
    and said in as many words that it "sits 1 mm below the floor slabs' top so
    it can never win a contact against them".  The floor slabs run z -0.30 ..
    0.0.  So by construction the outfield contains 299 mm of `SIM_FloorIn`,
    `SIM_FloorOut` and `SIM_Threshold`, this gate reported three penetrators,
    and `build_breach_sim.py` HAS REFUSED TO BAKE SINCE THAT COMMIT.  It went
    in without a bake behind it — the shipped table `breach_full_m1.npz`
    predates it and registers 233 boxes to this build's 234 — so the first
    thing anybody who tried to re-bake would hit is a gate stopping them on a
    deliberate overlap between two slabs that cannot move.

    The rule the gate is actually for is "nothing may be EJECTED by its own
    initial condition", and a PASSIVE body cannot be ejected: it has no
    velocity state and Bullet never integrates it.  Every defect this gate has
    ever caught — 582 clamped shards inside the sill, a mullion foot 88 mm
    inside it, a head 110 mm inside the head beam — was an ACTIVE body, and
    all of them are still refused.  Static-into-static overlap is REPORTED,
    with its worst offenders, and does not stop the bake.  It is not dropped,
    because a catch slab that silently overlaps something else is exactly the
    thing R2-197 said it did not want to be.
    """
    if not BOX_COLLIDERS:
        return dict(status="VACUOUS: no box colliders registered")
    lo = np.array([b[1] for b in BOX_COLLIDERS])
    hi = np.array([b[2] for b in BOX_COLLIDERS])
    names = [b[0] for b in BOX_COLLIDERS]
    worst = []            # movable bodies -- these REFUSE the bake
    static_worst = []     # passive-into-passive -- reported only
    for ob in bodies:
        if ob.data is None or not len(ob.data.vertices):
            continue
        V = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
        # depth inside box k = min over axes of min(v-lo, hi-v), >0 == inside
        d = np.minimum(V[:, None, :] - lo[None, :, :],
                       hi[None, :, :] - V[:, None, :]).min(axis=2)
        if skip_own:
            # a box is trivially "inside itself"; and the plate lump shares its
            # parent's name with a suffix
            for kk, nm in enumerate(names):
                if nm == ob.name or nm == ob.name + "_plate":
                    d[:, kk] = -1.0
        if d.max() > tol:
            k = int(np.unravel_index(np.argmax(d), d.shape)[1])
            rb = getattr(ob, "rigid_body", None)
            movable = rb is None or rb.type == "ACTIVE"
            (worst if movable else static_worst).append(
                (float(d.max()), ob.name, names[k]))
    worst.sort(reverse=True)
    static_worst.sort(reverse=True)
    return dict(bodies_tested=len(bodies), boxes=len(BOX_COLLIDERS),
                penetrating=len(worst), tol_m=tol,
                worst=[dict(depth_m=w[0], shard=w[1], into=w[2])
                       for w in worst[:8]],
                # reported, not refused on -- see the docstring (R2-283)
                static_overlaps=len(static_worst),
                static_worst=[dict(depth_m=w[0], body=w[1], into=w[2])
                              for w in static_worst[:8]])


def _pvb_post(c):
    """The interlayer STRETCHES: 1.5 mm of PVB pulls to several times its own
    length before it tears, which is the whole reason laminated glass hangs
    together in sheets instead of raining down."""
    for ax in ("x", "y", "z"):
        setattr(c, "use_limit_lin_%s" % ax, True)
        setattr(c, "limit_lin_%s_lower" % ax, -0.045)
        setattr(c, "limit_lin_%s_upper" % ax, 0.045)
        setattr(c, "use_spring_%s" % ax, True)
        setattr(c, "spring_stiffness_%s" % ax, 55.0)
        setattr(c, "spring_damping_%s" % ax, 0.6)


def _seg_at(segs, z):
    """The mullion segment whose z span contains z (nearest if outside)."""
    best, bd = segs[0], 1e9
    for ob in segs:
        c = ob.location[2]
        d = abs(c - z)
        if d < bd:
            best, bd = ob, d
    return best


def _hull_faces(P):
    """Convex hull faces of a small point cloud, via bmesh."""
    import bmesh
    bm = bmesh.new()
    for p in P:
        bm.verts.new((float(p[0]), float(p[1]), float(p[2])))
    bm.verts.ensure_lookup_table()
    import mathutils                                              # noqa: F401
    res = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    bmesh.ops.delete(bm, geom=res["geom_interior"], context="VERTS")
    bm.verts.ensure_lookup_table()
    idx = {v: i for i, v in enumerate(bm.verts)}
    faces = [[idx[v] for v in f.verts] for f in bm.faces]
    verts = [tuple(v.co) for v in bm.verts]
    bm.free()
    return faces if len(verts) == len(P) else _hull_faces_reindexed(P, verts,
                                                                   faces)


def _hull_faces_reindexed(P, verts, faces):
    """convex_hull dropped interior points, so the caller's P no longer matches.
    Map back by nearest vertex; the clouds are tiny so this is exact."""
    P = np.asarray(P, float)
    out = []
    for f in faces:
        out.append([int(np.argmin(np.linalg.norm(P - np.array(verts[i]),
                                                 axis=1))) for i in f])
    return out


# --------------------------------------------------------------------------- #
#  PROOF that the car curve is linear, by EVALUATION
# --------------------------------------------------------------------------- #

MOTION_PATHS = ("location", "rotation_euler")


def _act_fcurves(act, motion_only=True):
    """The action's fcurves.

    `motion_only` keeps this to the six curves that carry the car's TRANSFORM.
    R2-386 puts a second pair of curves on the same action -- the proxy's
    collision collections, which are booleans and are CONSTANT on purpose --
    and `prove_linear` must neither test them for linearity nor index the car's
    location array with their array_index.  They are counted separately so the
    exclusion is visible rather than silent.
    """
    out = []
    for lay in act.layers:
        for st in lay.strips:
            for sl in act.slots:
                cb = st.channelbag(sl)
                if cb:
                    out.extend(list(cb.fcurves))
    if motion_only:
        out = [fc for fc in out if fc.data_path in MOTION_PATHS]
    return out


def prove_linear(act, nsim, car, wts):
    """Read the flag AND evaluate the curve.  The flag has lied before."""
    out = {"n_keys": 0, "flag_linear": 0, "max_eval_err_m": 0.0,
           "max_bezier_err_m": 0.0,
           "non_motion_curves": len(_act_fcurves(act, motion_only=False))
           - len(_act_fcurves(act))}
    loc, rot = car.at_world_t(wts)
    for fc in _act_fcurves(act):
        kps = fc.keyframe_points
        out["n_keys"] += len(kps)
        out["flag_linear"] += sum(1 for k in kps if k.interpolation == "LINEAR")
        ref = loc[:, fc.array_index] if fc.data_path == "location" \
            else rot[:, fc.array_index]
        # evaluate at half-frames: LINEAR must land on the mean of neighbours
        for f in range(1, min(nsim, 400)):
            got = fc.evaluate(f + 0.5)
            want = 0.5 * (ref[f - 1] + ref[f])
            out["max_eval_err_m"] = max(out["max_eval_err_m"],
                                        abs(got - want))
    out["max_eval_err_m"] = float(out["max_eval_err_m"])
    out["all_flags_linear"] = bool(out["flag_linear"] == out["n_keys"])
    # POSITIVE CONTROL: a bezier curve must FAIL the same test
    fc = _act_fcurves(act)[0]
    saved = [k.interpolation for k in fc.keyframe_points]
    for k in fc.keyframe_points:
        k.interpolation = "BEZIER"
    fc.update()
    ref = loc[:, fc.array_index]
    for f in range(1, min(nsim, 400)):
        out["max_bezier_err_m"] = max(
            out["max_bezier_err_m"],
            abs(fc.evaluate(f + 0.5) - 0.5 * (ref[f - 1] + ref[f])))
    for k, s in zip(fc.keyframe_points, saved):
        k.interpolation = s
    fc.update()
    out["max_bezier_err_m"] = float(out["max_bezier_err_m"])
    out["control_fires"] = bool(out["max_bezier_err_m"] > 10.0 * max(
        out["max_eval_err_m"], 1e-12))
    return out


# --------------------------------------------------------------------------- #
#  BAKE and EXPORT
# --------------------------------------------------------------------------- #

def bake(nsim):
    sc = bpy.context.scene
    log("baking %d frames ..." % nsim)
    ctx = bpy.context.copy()
    ctx["point_cache"] = sc.rigidbody_world.point_cache
    with bpy.context.temp_override(**ctx):
        bpy.ops.ptcache.bake(bake=True)
    log("bake done")


def export(objs, info, path):
    """Step the baked cache and record every body's world transform.

    Positions as float32 metres and rotations as float32 quaternions.  The table
    IS the deliverable: `push_scene` is not resumable and a multi-GB scene that
    drops at 90 % restarts from zero, so what crosses the wire is 3,000 x N x 7
    floats and not a point cache.
    """
    sc = bpy.context.scene
    names = [o.name for o in objs]
    n, nf = len(objs), info["sim_frames"]
    loc = np.zeros((nf, n, 3), np.float32)
    quat = np.zeros((nf, n, 4), np.float32)
    dg = bpy.context.evaluated_depsgraph_get()
    for fi in range(nf):
        sc.frame_set(fi + 1)
        dg.update()
        for j, o in enumerate(objs):
            m = o.matrix_world
            loc[fi, j] = (m[0][3], m[1][3], m[2][3])
            q = m.to_quaternion()
            quat[fi, j] = (q.w, q.x, q.y, q.z)
        if fi % 100 == 0:
            log("  export frame %d/%d" % (fi + 1, nf))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, loc=loc, quat=quat,
                        names=np.array(names),
                        world_t=BL.sim_frame_world_t(info["world_t0"], nf))
    info["export"] = dict(path=path, bodies=n, frames=nf,
                          bytes=os.path.getsize(path))
    return loc, quat


def motion_report(loc, quat, names, info):
    """Did anything actually MOVE?  A null must be proven, not accepted."""
    d = np.linalg.norm(loc[-1] - loc[0], axis=1)
    per = np.linalg.norm(np.diff(loc, axis=0), axis=2)     # (nf-1, n)
    return dict(
        bodies=len(names),
        moved_gt_1mm=int((d > 0.001).sum()),
        moved_gt_100mm=int((d > 0.100).sum()),
        max_displacement_m=float(d.max()),
        median_displacement_m=float(np.median(d)),
        peak_speed_ms=float((per.max() * BL.SIM_FPS)),
        never_moved=int((d <= 1e-6).sum()),
        below_floor=int((loc[:, :, 2].min(axis=0) < -0.02).sum()),
        outside_x=int((loc[:, :, 0].max(axis=0) > 60.0).sum()),
        # R2-197.  `below_floor` alone cannot tell a body that TUNNELLED from a
        # body that walked off the edge of the static ground, and the two have
        # different fixes.  Split it by where the body was when it crossed:
        # inside the three slabs' footprint is a solver failure, outside it is a
        # missing floor.  `caught_by_the_outfield` must be the whole of the
        # second column once SIM_Outfield exists -- if it is not, the catch slab
        # is absorbing something it was not built for.
        left_the_slab_footprint=int(_off_edge(loc)),
        below_floor_inside_the_footprint=int(
            (loc[:, :, 2].min(axis=0) < -0.02).sum() - _off_edge(loc)),
        caught_by_the_outfield=int(
            ((loc[:, :, 2].min(axis=0) < -0.02)
             & (loc[:, :, 2].min(axis=0) > -0.60)).sum()),
        nan=int(np.isnan(loc).sum() + np.isnan(quat).sum()))


# the three slabs `build()` lays down, as one place rather than three literals
SLAB_FOOTPRINT = ((-15.00, 14.94, -11.0, 11.0),
                  (14.94, 15.00, -14.0, 14.0),
                  (15.00, 46.00, -14.0, 14.0))


def _off_edge(loc):
    """How many bodies first go below z = 0 while OUTSIDE the slab footprint."""
    n = 0
    for i in range(loc.shape[1]):
        below = np.where(loc[:, i, 2] < 0.0)[0]
        if not len(below) or below[0] == 0:
            continue
        x, y = loc[below[0], i, 0], loc[below[0], i, 1]
        if not any(x0 <= x <= x1 and y0 <= y <= y1
                   for x0, x1, y0, y1 in SLAB_FOOTPRINT):
            n += 1
    return n


RELEASE_FRAME = 860        # nothing can be SEEN to sag before the swap


def camera_ranges(plan, release=RELEASE_FRAME):
    """The closest the ONE camera gets to each bay WHILE THAT BAY IS IN SHOT.

    THE BUG THIS REPLACES (R2-093)
    -----------------------------
    The old version took the nearest beat-sheet camera KEY to the bay's CENTRE
    over the whole take, and did not ask whether the bay was inside the frame,
    nor whether the frame was after the shards were released.  It priced bay 2
    at 3.52 m.  Bay 2's nearest range on a frame where bay 2 is actually inside
    the 3840x2160 raster, after release, is 22.87 m — 6.5x further, so every
    pixel figure taken through it was 6.5x too big.  That is where the 7.1 px
    sag came from.

    Three things are fixed and each one moved the number:
      * the camera comes from `sim/out/oner_camera_track.json`, the applied
        scene's own animated transform at every one of the 2,978 frames, not
        from 417 authored keys;
      * the bay is sampled on a 5x5 grid and every sample is tested against the
        raster, so a bay behind the camera or off the edge does not count;
      * frames before `release` do not count, because until then the INTACT
        pane renders and its silhouette is fixed by construction.

    The returned `mm_per_px` is still the BEST (smallest) over the in-shot
    frames, so `max_sag_mm * mm_per_px` remains a conservative upper bound: it
    assumes the worst sag and the closest view coincide, and they need not.
    `sim/sagpx.py` measures the per-frame product for real when the caller has
    the sag on the film's own frame grid.
    """
    try:
        import sagpx as SP
        track = SP.load_track()
    except Exception as exc:                                    # noqa: BLE001
        log("camera_ranges: no camera track (%s); ranges unavailable" % exc)
        return {}
    R = SP._rot(track["quat"])
    C, LN, FR_ = track["loc"], track["lens"], track["frame"]
    out = {}
    for bay, (u0, u1, v0, v1) in plan.get("rects", {}).items():
        P = np.array([[GLASS_X_OUT, u, v]
                      for u in np.linspace(u0, u1, 5)
                      for v in np.linspace(v0, v1, 5)])
        best, nfr = None, 0
        for i in range(len(C)):
            if FR_[i] < release:
                continue
            L = (P - C[i]) @ R[i]
            dep = -L[:, 2]
            fpx = SP.RES_X * LN[i] / SP.SENSOR
            with np.errstate(divide="ignore", invalid="ignore"):
                px = SP.RES_X * 0.5 + fpx * L[:, 0] / dep
                py = SP.RES_Y * 0.5 - fpx * L[:, 1] / dep
            ok = ((dep > 1e-6) & (px >= 0) & (px < SP.RES_X)
                  & (py >= 0) & (py < SP.RES_Y))
            if not ok.any():
                continue
            nfr += 1
            d = float(dep[ok].min())
            mmpx = 1000.0 * SP.SENSOR / (SP.RES_X * LN[i]) * d
            if best is None or mmpx < best[0]:
                best = (mmpx, d, float(LN[i]), int(FR_[i]))
        if best is None:
            out[bay] = dict(frames_in_shot=0, never_in_shot=True)
            continue
        out[bay] = dict(closest_m=best[1], lens_mm=best[2],
                        px_per_m=float(1000.0 / best[0]),
                        mm_per_px=best[0], frames_in_shot=nfr,
                        at_frame=best[3])
    return out


def creep_vs_ring(loc, meta, plan, roles_wanted=("retained", "intact")):
    """Is the residual motion CREEPING or RINGING?

    They look identical in a single end-frame number and they are completely
    different defects.  Creep at 11 mm per 0.25 s is 300 mm by the end of the
    sim window and the wall is on the floor.  A bounded ring at 3 mm is a soft
    constraint network humming, which is a shimmer to fix, not a collapse.

    Measured over the second half of the window, where the initial settle is
    over: DRIFT is the least-squares slope extrapolated to the whole window,
    RING is the peak-to-peak of the same series about that trend.
    """
    roles = plan.get("roles", {})
    keep = [i for i, m in enumerate(meta)
            if roles.get(m.get("bay", -1)) in roles_wanted]
    if not keep:
        return dict(status="no retained/intact shards in this plan")
    d = np.linalg.norm(loc - loc[0][None], axis=2)[:, keep]
    med = np.median(d, axis=1)
    n = len(med)
    h = med[n // 2:]
    t = np.arange(len(h), dtype=float)
    if len(h) < 4:
        return dict(status="window too short")
    A = np.vstack([t, np.ones_like(t)]).T
    slope, icpt = np.linalg.lstsq(A, h, rcond=None)[0]
    resid = h - (slope * t + icpt)
    return dict(
        frames=n, measured_over="second half",
        drift_mm_per_frame=float(1000.0 * slope),
        drift_mm_over_window=float(1000.0 * slope * n),
        ring_peak_to_peak_mm=float(1000.0 * (resid.max() - resid.min())),
        median_mm=float(1000.0 * np.median(h)),
        verdict=("CREEP" if abs(slope) * n > 2.0 * (resid.max() - resid.min())
                 else "RING"))


def null_verdict(loc, meta, plan):
    """THE NULL'S PASS CRITERION, IN PIXELS.

    Two parts, and the second is the one that was a judgement until now:

      1. NOTHING LEAVES.  No shard may move more than 0.25 m with no car in the
         scene.  This is binary.
      2. NOTHING THAT STAYS MAY BE SEEN TO MOVE.  The panes that are still
         there in beat 6 — the retained and intact bays — may not sag more than
         ONE PIXEL at the range the camera actually films them at.  A millimetre
         is not a tolerance on its own; it is only a tolerance next to a
         distance and a lens.

    The destroyed bays are excluded on purpose: they leave the wall, and their
    motion is the shot rather than a defect.

    A THIRD CRITERION, ADDED BECAUSE ITS ABSENCE IS WHAT BROKE THE WALL
    ------------------------------------------------------------------
    R2-092.  This field is permanent.  Read it on every null.
    A null that passes because nothing CAN move is not a null.  Raising
    `THRESH_BOND_PER_M` to 4000 made criterion 1 pass by making the glass
    unbreakable, and the same parameter then produced a 0.65 x 1.92 m aperture
    against a declared 9.6 x 5.6 m.  So this function also reports
    `mobility`: with `--wake-all` and no car, how many bodies moved AT ALL.
    A null in which literally nothing moved by even a micron is reporting that
    the solver never integrated the wall, not that the wall is well built.
    The verdict carries it; the caller must read it.

    THE PIXEL FIGURE IS AN UPPER BOUND, AND SAYS SO
    -----------------------------------------------
    `max_sag_px` is this bay's WORST sag times its BEST in-shot pixel scale.
    Those two need not occur on the same frame, so the product is a bound and
    not a measurement.  The old code did the same thing with a range that was
    also wrong — see `camera_ranges` — and reported 7.1 px where the honest
    bound is 1.4.  For the per-frame product use `sim/sagpx.py`.
    """
    rng = camera_ranges(plan)
    roles = plan.get("roles", {})
    d = np.linalg.norm(loc[-1] - loc[0], axis=1)
    per_bay, worst_px, worst_bay = {}, 0.0, None
    for i, m in enumerate(meta):
        per_bay.setdefault(m.get("bay", -1), []).append(d[i])
    out = dict(criterion="retained/intact bays sag < 1 px at their own "
                         "measured camera range", bays={})
    for bay, v in sorted(per_bay.items()):
        if bay not in rng or "mm_per_px" not in rng[bay]:
            # a bay the camera never frames after release has no pixel scale.
            # Skipping it silently is how a KeyError becomes a clean exit 0.
            out.setdefault("bays_never_in_shot", []).append(bay)
            continue
        v = np.array(v)
        mm = 1000.0 * v.max()
        px = mm / rng[bay]["mm_per_px"]
        keeps = roles.get(bay) in ("retained", "intact")
        out["bays"][str(bay)] = dict(
            role=roles.get(bay), n=len(v), max_sag_mm=float(mm),
            closest_m=rng[bay]["closest_m"], mm_per_px=rng[bay]["mm_per_px"],
            max_sag_px=float(px), counts=bool(keeps))
        if keeps and px > worst_px:
            worst_px, worst_bay = px, bay
    out["worst_px_on_a_pane_that_stays"] = float(worst_px)
    out["worst_bay"] = worst_bay
    out["nothing_left"] = bool(d.max() <= 0.25)
    out["max_displacement_m"] = float(d.max())
    out["px_figure_is"] = ("an UPPER BOUND: this bay's worst sag times its best "
                           "in-shot pixel scale, which need not be the same "
                           "frame.  sim/sagpx.py measures the per-frame "
                           "product.")
    # THE MOBILITY CHECK.  A null that passes because nothing CAN move is not a
    # null.  If the wall barely moves at all under --wake-all, that is a report
    # about the constraint network being unbreakable, not about it being sound,
    # and it is exactly how THRESH_BOND_PER_M reached 4000.
    out["mobility"] = dict(
        moved_gt_1mm=int((d > 0.001).sum()), of=int(len(d)),
        moved_gt_10mm=int((d > 0.010).sum()),
        moved_gt_50mm=int((d > 0.050).sum()),
        median_mm=float(1000.0 * np.median(d)),
        note="compare across thresholds, not against a limit.  Over 480 "
             "wake-all frames the SHIPPED 4000 gives median 15.21 mm and 264 "
             "shards over 50 mm; 100 gives 8.48 mm and 5.  The stiffer network "
             "moves MORE, because 24 sequential-impulse iterations satisfy it "
             "less well.")
    out["PASS"] = bool(out["nothing_left"] and worst_px <= 1.0)
    return out


def _unused_placeholder():
    return None


def sag_report(loc, names, meta, plan):
    """WHERE the wall moved, split by class and by pane role.

    A single median over 4,000 bodies hides the only distinction that matters:
    bays 3-6 leave the wall anyway, so their motion is the shot; bays 2 and 7
    are the RETAINED panes that have to hang in the frame spider-webbed for the
    rest of the film, and a millimetre of sag there is a defect that never
    recovers.
    """
    import re
    d = np.linalg.norm(loc[-1] - loc[0], axis=1)
    out = {}
    cls = {}
    for i, n in enumerate(names):
        cls.setdefault(re.match(r"[A-Z]+", n).group(0), []).append(i)
    for k, idx in sorted(cls.items()):
        dd = d[idx]
        out[k] = dict(n=len(idx), median_m=float(np.median(dd)),
                      p95_m=float(np.percentile(dd, 95)),
                      max_m=float(dd.max()))
    roles = plan.get("roles", {})
    by_role = {}
    for i, m in enumerate(meta):
        r = roles.get(m.get("bay", -1))
        if r is None:
            continue
        by_role.setdefault(r, []).append(d[i])
    for r, v in by_role.items():
        v = np.array(v)
        out["role_" + r] = dict(n=len(v), median_m=float(np.median(v)),
                                p95_m=float(np.percentile(v, 95)),
                                max_m=float(v.max()))
    return out


def aperture_report(loc, meta, info, settle_frac=0.75):
    """THE APERTURE THE SIM PRODUCED, measured on the wall plane.

    A shard counts as GONE if it ended more than `GONE_M` from where it started.
    The hole is the bounding box of the gone shards in (y, z).

    DO NOT SHIP THIS NUMBER.  R2-094: a bbox of ORIGINS reports a 13.01 x
    5.79 m aperture from TWO shards at opposite corners of the glazing, which
    is the control `aperture.aperture_controls.TRAP_two_corners` fires on.
    The honest measure is the largest CONNECTED vacated region on a raster of
    the wall plane, with the mullion strips passable only where that mullion
    segment has actually left: `sim/aperture.py::hole`, scored by
    `sim/breach_metrics.py`.  This function is kept only so the two measures
    can be printed side by side.

    R2-095: the declared 9.6 m is the clear span between the two BENT mullions
    at y = +-4.4.  It is not a glass aperture and never was.  The glass in
    bays 3-6 tops out at 8.77 m, and reaching even that needs bays 2 and 7,
    which the plan marks `retained`.
    """
    GONE_M = 0.25
    st = np.array([m["origin"] for m in meta])
    en = loc[-1]
    gone = np.linalg.norm(en - st, axis=1) > GONE_M
    if not gone.any():
        return dict(gone=0, note="NOTHING MOVED")
    y, z = st[gone][:, 1], st[gone][:, 2]
    return dict(
        gone=int(gone.sum()), of=len(meta),
        y_min=float(y.min()), y_max=float(y.max()),
        z_min=float(z.min()), z_max=float(z.max()),
        width_m=float(y.max() - y.min()), height_m=float(z.max() - z.min()),
        declared_width_m=9.6, declared_height_m=5.6,
        gone_mass_kg=float(sum(m["mass"] for m, g in zip(meta, gone) if g)),
        total_mass_kg=float(sum(m["mass"] for m in meta)))


# --------------------------------------------------------------------------- #

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--shards",
                   default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    p.add_argument("--out", default=os.path.join(R2, "sim/out/breach_sim.blend"))
    p.add_argument("--export",
                   default=os.path.join(R2, "sim/out/breach_bake.npz"))
    p.add_argument("--report",
                   default=os.path.join(R2, "sim/out/breach_sim.json"))
    p.add_argument("--frames", type=int, default=0,
                   help="truncate the sim window (pilot runs only)")
    p.add_argument("--detail", type=int, default=0)
    p.add_argument("--mullion-segments", type=int, default=8)
    p.add_argument("--bake", action="store_true")
    p.add_argument("--wake-all", action="store_true",
                   help="THE NULL THAT CAN FAIL: clear `use_start_deactivated` "
                        "so every body is AWAKE at frame 1.  With --no-car the "
                        "wall must then stand under gravity on its own.  A "
                        "sleeping wall standing still proves only that Bullet "
                        "left it asleep.")
    p.add_argument("--no-car", action="store_true",
                   help="THE NULL CONTROL: build the wall with no car in the "
                        "scene.  Nothing may move.  A destruction sim that "
                        "cannot pass this is measuring its own initial "
                        "penetration, not the impact.")
    p.add_argument("--t-glass-edge", type=float, default=THRESH_GLASS_EDGE)
    p.add_argument("--t-pvb", type=float, default=THRESH_PVB)
    p.add_argument("--t-mullion-joint", type=float,
                   default=THRESH_MULLION_JOINT)
    p.add_argument("--t-mullion-base", type=float, default=THRESH_MULLION_BASE)
    p.add_argument("--t-transom", type=float, default=THRESH_TRANSOM,
                   help="transom end into the mullion's screw port SP1.  "
                        "DERIVED, not fitted: two M6 A2-70 self-tappers, "
                        "shear governs at 16.90 kN, T = 8.8 "
                        "(sim/frame_thresholds.py).  The old 260 was 499 kN, "
                        "29.5x this, and more than twice "
                        "THRESH_MULLION_BASE -- two screws stronger than the "
                        "anchor studs in the slab (R2-275, R2-281).")
    p.add_argument("--head-restraint", choices=("fixed", "slider"),
                   default="slider",
                   help="how the mullion meets the head beam.  `slider` is "
                        "the physical model and is now the DEFAULT: lateral "
                        "load only, free in z, which is what the declared "
                        "17.2 mm head_expansion_gap_m is.  `fixed` is what "
                        "shipped -- a 38.4 kN rigid joint across that gap, so "
                        "a mullion whose base has gone hangs from its head "
                        "(R2-268).  Kept as an option because it is the "
                        "before-half of the experiment.")
    p.add_argument("--t-bond-per-m", type=float, default=THRESH_BOND_PER_M)
    p.add_argument("--air-drag", choices=("off", "derived"), default="derived",
                   help="aerodynamic drag on every ACTIVE body, linearised "
                        "about the car's speed at the glass plane and sized "
                        "from each body's own collision-mesh surface area "
                        "(Cauchy, S/4).  `derived` IS NOW THE DEFAULT (R2-400): "
                        "the decision has been made and measured -- 2,646 "
                        "bodies still moving at the table's last key become "
                        "27, against the shipped table's own 70, and the "
                        "aperture comes out better rather than worse.  `off` "
                        "is what shipped -- NO AIR AT ALL, in a scene that "
                        "throws 730 kg of glass down a forecourt at 16 m/s -- "
                        "and is kept only because it is the before-half of "
                        "the experiment (R2-388, R2-392, R2-395).")
    p.add_argument("--car-friction", type=float, default=CAR_FRICTION,
                   help="the car proxy's surface friction.  Bullet MULTIPLIES "
                        "the two bodies' values, so this scales every "
                        "tangential force the car can put into the debris.")
    p.add_argument("--car-collide-until", type=float, default=0.0,
                   help="world x of the CAR'S ORIGIN past which the proxy "
                        "stops colliding.  0 = never (what shipped).  The "
                        "car's tail clears the glass plane at origin x = "
                        "17.678 (GLASS_PLANE_X 15.000 - TAIL_DX -2.678).  "
                        "The transform is untouched either way.")
    p.add_argument("--substeps", type=int, default=SUBSTEPS)
    p.add_argument("--solver-iter", type=int, default=SOLVER_ITER)
    return p.parse_args(argv)


def main():
    a = parse_args()
    info, objs = build(a)
    global plan_for_sag
    plan_for_sag = FR.load(a.shards)
    car = BL.Car()
    t0 = info["world_t0"]
    wts = BL.sim_frame_world_t(t0, info["sim_frames"])
    info["linearity"] = prove_linear(objs["action"], info["sim_frames"], car,
                                     wts)
    log("linearity: %s" % json.dumps(info["linearity"]))
    if not info["linearity"]["all_flags_linear"] or \
            info["linearity"]["max_eval_err_m"] > 1e-5 or \
            not info["linearity"]["control_fires"]:
        raise SystemExit("REFUSING: the car proxy's curve is not LINEAR by "
                         "evaluation.  %s" % info["linearity"])
    if a.bake:
        bake(info["sim_frames"])
        loc, quat = export(objs["shards"] + objs["frame"], info, a.export)
        meta = info["shard_meta"] + [
            dict(name=o.name, origin=list(o.location), mass=0.0, bay=-1,
                 id=-1, area=0.0, volume=0.0, clamped=False, laminated=False,
                 r_impact=0.0, aspect=1.0) for o in objs["frame"]]
        names = [o.name for o in objs["shards"] + objs["frame"]]
        info["motion"] = motion_report(loc, quat, names, info)
        info["sag"] = sag_report(loc, names, info["shard_meta"], plan_for_sag)
        info["null_verdict"] = null_verdict(
            loc[:, :len(objs["shards"])], info["shard_meta"], plan_for_sag)
        info["creep_vs_ring"] = creep_vs_ring(
            loc[:, :len(objs["shards"])], info["shard_meta"], plan_for_sag)
        info["aperture"] = aperture_report(
            loc[:, :len(objs["shards"])], info["shard_meta"], info)
        log("motion: %s" % json.dumps(info["motion"]))
        log("sag: %s" % json.dumps(info["sag"], default=float))
        log("creep_vs_ring: %s" % json.dumps(info["creep_vs_ring"],
                                             default=float))
        log("NULL VERDICT: %s  worst %.2f px on bay %s (%s)"
            % ("PASS" if info["null_verdict"]["PASS"] else "FAIL",
               info["null_verdict"]["worst_px_on_a_pane_that_stays"],
               info["null_verdict"]["worst_bay"],
               json.dumps(info["null_verdict"]["bays"], default=float)[:300]))
        log("aperture: %s" % json.dumps(info["aperture"]))
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    info["blend"] = a.out
    info["blend_bytes"] = os.path.getsize(a.out)
    with open(a.report, "w") as fh:
        json.dump(info, fh, indent=1, default=float)
    log("wrote %s (%.1f MB) and %s"
        % (a.out, info["blend_bytes"] / 1e6, a.report))


if __name__ == "__main__":
    main()
