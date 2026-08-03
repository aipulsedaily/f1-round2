#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spectator_seated.py — CIRCUIT VITRINE round 2, manifest item ``spectator_seated``.

    254 px tall, head 47 px, at the closest point of the Beat-6 crane-out.
    NO FACES ... Spend the budget on POSTURE and SILHOUETTE instead. Torso angle,
    shoulder line, knee position and where the arms are is 100 % of the read.
    A stand where every figure has the same shoulder angle is the crowd
    equivalent of one tree spammed a hundred times.
                                                    -- docs/item_manifest.json

WHAT THIS IS
------------
A procedural seated-human generator.  Not a mesh: a *system*.  Every figure is
solved from scratch — anthropometry, posture, forward kinematics for the spine
and neck, two-bone inverse kinematics for both arms and both legs — and then
skinned by lofting elliptical cross-sections along the solved skeleton.  Nothing
is a copy of anything.  Two figures with the same posture name and different
statures do not share a single vertex, because the IK re-solves the elbow and the
knee for the new limb lengths.

    px_per_m = (3840 * 28 / 36) / 14.7 = 203.2 px/m   ->  1 px = 4.92 mm

That number drives every decision below:

  * a fold in a sleeve at 8 mm deep is 1.6 px of shading — folds are MESH, baked
    into the loft as a radial offset field, not a bump map;
  * a nose is 22 mm = 4.5 px in profile, an ear 12 mm = 2.4 px — both are modelled,
    both are silhouette, neither is a "face";
  * an eye is 25 mm wide = 5 px of a HEAD that is 47 px tall.  There are no eyes,
    no mouths, no nostrils.  The manifest is right: at this scale they read as
    dirt.  The hair mass, the collar line and the head angle carry the head.

THE LAWS THIS FILE IS HELD TO  (docs/ITEM-CAMPAIGN-BRIEF.md)
-----------------------------------------------------------
  * Everything procedural and built by hand.  Zero image textures, zero external
    assets, zero AI anything.  The six materials here are noise/voronoi/wave only.
  * Recentred on emit: the mesh origin is the SEAT PAN CENTRE (see the frame
    below), so every vertex is within ~1 m of the object origin and
    ``TexCoord -> Object`` is exact even with the grandstand 380 m from the world
    origin.  No material in this file touches ``Geometry -> Position``.
  * Scale is anthropometric, not intuitive: segment lengths are fractions of
    stature from the standard Dempster/NASA-STD-3000 tables, and the seat they
    sit on is build_architecture's real grandstand rake (0.50 m seat pitch,
    0.88 m tread, 0.335 m rise, pan 0.445 m above its own tread).

--------------------------------------------------------------------------------
THE INTERFACE — this item is a FOUNDATION, eight items depend on it
--------------------------------------------------------------------------------
Dependants (from the manifest): crowd_flag_handheld, crowd_idle_motion,
spectator_bag_and_coat, spectator_child, spectator_seated_leaning,
spectator_standing_in_row, spectator_umbrella, spectator_with_phone.
None of them can ask me a question, so everything they need is here and stable.

1.  THE FIGURE LOCAL FRAME.  Every figure mesh is authored in, and every anchor
    below is expressed in, this frame:

        origin   the CENTRE OF THE SEAT PAN'S TOP SURFACE
        +Y       the direction the spectator faces (down the rake, at the track)
        +Z       world up
        +X       the spectator's own RIGHT

    ``seat_anchor_matrix(x, y_pan_centre, z_pan_top, facing_deg)`` builds the
    placement matrix.  ``RAKE`` holds the grandstand numbers this frame is
    calibrated against, mirrored from build_architecture.GS_BLOCKS.

2.  ``sample_spec(index, seed=SEED)  -> FigureSpec``
    Deterministic.  The same (index, seed) always gives the same person: stature,
    build, sex-ish proportions, 8 % children, garment silhouette, hair style,
    palette, posture and per-instance posture jitter.  Ask for index 4211 twice,
    get the same human.  A dependant that needs "the person in seat N" asks for
    the same index the crowd field used and gets the identical figure.

3.  ``solve_skeleton(spec)  -> dict[str, Joint]``
    The posed skeleton: 30 joints, each with a position and an orthonormal frame
    (columns = right / forward / bone-axis).  This is the animation interface —
    ``crowd_idle_motion`` should perturb ``spec.pose`` (a plain dict of angles and
    IK targets) and re-solve, NOT try to deform the emitted mesh.  Re-solving is
    ~1.5 ms; the mesh rebuild is ~120 ms.

4.  ``anchors(spec)  -> dict[str, 4x4]``
    Attachment frames for everything that hangs off a spectator, all in the frame
    of (1), all right-handed, all with +Z pointing "out of" the attachment:

        head_top      crown, +Z up along the skull axis     -> spectator_headwear
        head_front    brow centre, +Z forward               -> headwear peak
        ear_L/ear_R   ear centre, +Z out of the ear         -> spectator_ear_defenders
        hand_L/hand_R GRIP AXIS: origin at the middle of the fist, +Z along the
                      held shaft (thumb end is +Z)          -> crowd_flag_handheld,
                                                               spectator_umbrella,
                                                               spectator_with_phone
        lap           top of the thighs, +Z up              -> spectator_bag_and_coat
        seat_L/seat_R the seat surface beside the hip       -> bag on the seat
        under_seat    floor under the pan, +Z up            -> bag under the seat
        shoulder_L/R  deltoid top, +Z up-and-out            -> coat over a shoulder
        chest, back   torso surface, +Z out                 -> lanyard, draped coat
        knee_L/knee_R patella, +Z forward along the thigh
        foot_L/foot_R sole contact, +Z up
        pelvis        the root                              -> idle motion

5.  ``POSTURES`` — 15 named base postures (the manifest asks for 8-12), each a
    plain dict.  A dependant that needs a new posture (``spectator_seated_leaning``,
    ``spectator_standing_in_row``) should ADD an entry, not re-model a figure:
    ``POSTURES["my_new_one"] = posture(...)`` and it is immediately available to
    ``sample_spec`` through ``POSTURE_WEIGHTS``.

6.  ``GARMENTS`` / ``HAIR_STYLES`` / ``PALETTE`` — the wardrobe registry that
    ``spectator_clothing`` extends.  A garment entry is pure data: sleeve length,
    hem station, thickness, collar, hood, material key, looseness (which drives
    the fold amplitude).  Adding a garment adds it to the crowd; no geometry code
    changes.

7.  ``figure_mesh(spec, detail=...) -> bpy.types.Mesh`` and
    ``build(...) -> list[bpy.types.Object]``.
    ``detail`` is the LOD knob, and it is a distance decision, not a taste one:

        'hero'  <= 25 m   ~11.6 k tris  full folds, thumbs, ears, nose, cuffs
        'mid'   25-70 m   ~3.9 k tris   coarser rings, no thumbs, no ears
        'far'   > 70 m    ~1.9 k tris   silhouette and colour only

8.  ``build_library(n, detail) -> (collection, objects)`` and
    ``build_crowd_field(name, seat_points, library, n_sources, base=...) ->
    object``.
    THE POPULATION INTERFACE, and what ``crowd_density_field`` should call.
    7 800 unique hero figures is 90 M triangles and ~5 GB of mesh; the film
    cannot carry it and does not need to.  Build a library of unique figures and
    instance it with the geometry-nodes field, which picks a different source per
    seat and adds a per-seat yaw.  ``item_gate`` walks the realized instances and
    measures ``distinct_sources`` / ``top_source_share`` -- a large library is
    not decoration, it is the thing that check is looking for.
    Measured, not assumed: library objects carry ``hide_render = True`` and
    geometry nodes still instances them, so the sources never render at the
    origin while every instance does.

9.  ``seat_anchor_on_ground(x, y, pan_height_m)`` for the dependants that seat a
    figure on something standing on the WORLD ground -- a folding stool on the GA
    bank, a kerb, a step.  It reads ``world_contract.world_ground_z`` and embeds
    by ``BASE_EMBED_M``; it raises rather than guessing where terrain owns the
    ground.  Figures on the grandstand rake take their z FROM THE SEAT instead
    (``seat_anchor_matrix``), because the rake is architecture's datum, not the
    ground datum.  A grounded shoe additionally sinks ``FOOT_EMBED_M`` = 6 mm
    into whatever it stands on -- not BASE_EMBED_M's 20 mm, which would bury a
    26 mm sole in the concrete.

--------------------------------------------------------------------------------
MEASURED, NOT CLAIMED
--------------------------------------------------------------------------------
Run the acceptance gate, do not trust this docstring:

    /opt/blender-5.2.0-linux-x64/blender -b world/items/spectator_seated_test.blend \\
        --factory-startup -P tools/item_gate.py -- --item spectator_seated \\
        --prefix SPECSEAT_ --out render/items/spectator_seated/gate.json

Build the test scene (TRIBUNE PRINCIPALE at its real world position, 383 m from
the origin so the Object-coordinate law is actually under test, lit by the
world_contract sun, carrying the WHOLE declared population of 7 800):

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \\
        -P world/items/spectator_seated.py -- --test \\
        --out world/items/spectator_seated_test.blend

WHAT THE MACRO RENDERS FOUND, in order, because none of it was predictable from
the code and all of it was invisible until the frame existed:

  1. every figure sat FACING THE BACK WALL -- the placement applied a second
     Rz(180) on top of the local frame's own facing convention;
  2. the torso tapered to a cone at C7, so the arms hung off a stalk with a ball
     at each shoulder: 260 bowling pins.  Fixed with a real trapezius yoke;
  3. the full neck length stood between the shoulders and the skull -- a bright
     skin-toned column, a third of the head's height;
  4. the hair's crown pole sat a full thickness ABOVE the last ring: a 58 deg
     cowlick spike on every skull.  Moving it onto the crown then put it BELOW
     the ring, the fan folded inward, and the bare scalp came through the middle
     of the hair.  It is measured off the ring now;
  5. the garment hem flared at seat level and the buttock flattening spread it
     into a disc: every heavy figure wore a cape;
  6. the yoke, once it existed, stood proud of the chest all the way round and
     read as a poncho with a rim.

None of those are things a gate can see.  That is what the macro pass is for.
"""

from __future__ import annotations

import argparse
import colorsys
import math
import os
import sys

import numpy as np

try:
    import bpy
    from mathutils import Matrix, Vector
    HAVE_BPY = True
except Exception:                                            # pragma: no cover
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
if _WORLD not in sys.path:
    sys.path.insert(0, _WORLD)

try:
    import world_contract as WC
    HAVE_WC = True
except Exception:                                            # pragma: no cover
    WC = None
    HAVE_WC = False

__version__ = "1.0.0"

# =========================================================================== #
#  0.  THE MANIFEST'S OWN NUMBERS — the specification, not a guess             #
# =========================================================================== #
ITEM_ID = "spectator_seated"
NEAREST_CAMERA_M = 14.7
LENS_AT_CLOSEST_MM = 28.0
ONSCREEN_PX_4K = 254.0
TYPICAL_HEIGHT_M = 1.25
INSTANCES = 7800
SENSOR_MM = 36.0
RES_X_4K = 3840

#: 203.2 px per metre.  One screen pixel is 4.92 mm on this item.
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M
PX_M = 1.0 / PX_PER_M

OBJ_PREFIX = "SPECSEAT_"
COLLECTION = "ITEM_spectator_seated"
SEED = 20260729

# =========================================================================== #
#  1.  THE SEAT THEY SIT ON                                                    #
# =========================================================================== #
# Mirrored from build_architecture.GS_BLOCKS / _seat() / _grandstand_block().
# These are the numbers the local frame is calibrated against; if the grandstand
# ever moves, this dict is the one place that has to follow it.
#
#   pan top          = tread top + 0.445      (_seat kind 0: xbox at z 0.42, 50 mm)
#   pan centre in y  = tread front edge - 0.42 * tread
#   seat pitch       = 0.50 m                 (ncol = int(L / 0.50))
#   tread top        = z0 + 0.16              (0.16 m precast tread slab)
#   z0 for row r     = front_deck + r * rise,  front_deck = 2.40
RAKE = dict(
    seat_pitch_m=0.500,
    pan_above_tread_m=0.445,
    pan_half_depth_m=0.220,
    pan_half_width_m=0.220,
    backrest_y_m=-0.220,          # figure-local y of the seat back face
    tread_slab_m=0.160,
    front_deck_m=2.400,
    # per-block (name, tread, rise) exactly as build_architecture has them
    blocks=[("TRIBUNE OUEST", 0.92, 0.345), ("TRIBUNE T15", 0.86, 0.335),
            ("VIRAGE OUEST", 0.95, 0.355), ("TRIBUNE PRINCIPALE", 0.88, 0.335),
            ("TRIBUNE EST", 0.90, 0.340), ("TRIBUNE TEMPORAIRE", 0.82, 0.330)],
)
#: how far a grounded shoe sinks into whatever it stands on (see _foot)
FOOT_EMBED_M = 0.006
#: figure-local z of the tread the seat is bolted to (where most feet go)
TREAD_Z = -RAKE["pan_above_tread_m"]
#: figure-local z of the tread one row in front (where extended legs go)
TREAD_DOWN_Z = TREAD_Z - 0.335
#: figure-local y of that lower tread's front edge, for the TRIBUNE PRINCIPALE rake
TREAD_NOSING_Y = RAKE["pan_half_depth_m"] - 0.070

# =========================================================================== #
#  2.  ANTHROPOMETRY                                                           #
# =========================================================================== #
# Segment lengths as fractions of standing stature.  Adult column is the standard
# Dempster/Drillis-Contini set; the child column is the same measurements taken on
# a 7-9 year old, where the head is a much larger fraction and the legs a smaller
# one.  A child is NOT a scaled adult and a crowd built as if it were reads wrong
# even at 47 px, because the head/shoulder ratio is the thing the eye checks.
FRAC_ADULT = dict(
    sit_height=0.520, head_h=0.1300, head_w=0.0890, head_d=0.1130,
    neck_len=0.0350, neck_r=0.0325, torso_len=0.3550,
    shoulder_hw=0.1150, upperarm=0.1860, forearm=0.1460, hand_len=0.1080,
    thigh=0.2450, shank=0.2460, foot_len=0.1520, foot_h=0.0400,
    hip_hw=0.0950, hip_hd=0.0700, waist_hw=0.0850, waist_hd=0.0620,
    chest_hw=0.1000, chest_hd=0.0640, upperarm_r=0.0275, forearm_r=0.0235,
    wrist_r=0.0165, thigh_r=0.0455, knee_r=0.0355, calf_r=0.0330, ankle_r=0.0225,
)
FRAC_CHILD = dict(
    sit_height=0.540, head_h=0.1620, head_w=0.1010, head_d=0.1250,
    neck_len=0.0280, neck_r=0.0290, torso_len=0.3490,
    shoulder_hw=0.1030, upperarm=0.1720, forearm=0.1330, hand_len=0.1020,
    thigh=0.2280, shank=0.2280, foot_len=0.1450, foot_h=0.0370,
    hip_hw=0.0880, hip_hd=0.0650, waist_hw=0.0830, waist_hd=0.0620,
    chest_hw=0.0930, chest_hd=0.0600, upperarm_r=0.0280, forearm_r=0.0240,
    wrist_r=0.0160, thigh_r=0.0480, knee_r=0.0370, calf_r=0.0345, ankle_r=0.0230,
)


def _segments(stature, child_f, build_k, shoulder_k, leg_k, arm_k):
    """Absolute segment dimensions in metres for one person."""
    out = {}
    for k, va in FRAC_ADULT.items():
        vc = FRAC_CHILD[k]
        out[k] = (va + (vc - va) * child_f) * stature
    out["shoulder_hw"] *= shoulder_k
    for k in ("thigh", "shank"):
        out[k] *= leg_k
    for k in ("upperarm", "forearm"):
        out[k] *= arm_k
    # radial build: girth scales harder than skeleton.  ~ (k-1) on a cube root of
    # mass, so a 1.30 build is a heavy but not cartoon figure.
    for k in ("hip_hw", "hip_hd", "waist_hw", "waist_hd", "chest_hw", "chest_hd",
              "upperarm_r", "forearm_r", "wrist_r", "thigh_r", "knee_r",
              "calf_r", "ankle_r", "neck_r"):
        out[k] *= build_k
    # the belly and the waist take the weight first
    out["waist_hd"] *= 1.0 + 0.55 * max(0.0, build_k - 1.0)
    out["waist_hw"] *= 1.0 + 0.30 * max(0.0, build_k - 1.0)
    out["hip_hd"] *= 1.0 + 0.25 * max(0.0, build_k - 1.0)
    return out


# =========================================================================== #
#  3.  DETERMINISTIC NOISE  (numpy, no bpy, no textures)                       #
# =========================================================================== #
_U32 = np.uint32


def _hash3(ix, iy, iz, seed):
    """FNV-1a-ish integer hash -> float64 in [0, 1).  Broadcasts."""
    with np.errstate(over="ignore"):
        h = np.full(np.broadcast(ix, iy, iz).shape, _U32(2166136261), dtype=np.uint32)
        for k in (ix, iy, iz, np.int64(seed)):
            kk = (np.asarray(k).astype(np.int64) & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ kk) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def vnoise3(P, seed=0):
    """Trilinear value noise on (...,3) points -> [0,1)."""
    P = np.asarray(P, float)
    i = np.floor(P).astype(np.int64)
    f = P - i
    w = f * f * (3.0 - 2.0 * f)
    acc = 0.0
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                h = _hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
                wx = w[..., 0] if dx else 1.0 - w[..., 0]
                wy = w[..., 1] if dy else 1.0 - w[..., 1]
                wz = w[..., 2] if dz else 1.0 - w[..., 2]
                acc = acc + h * wx * wy * wz
    return acc


def fbm3(P, seed=0, oct=3, lac=2.07, gain=0.5):
    a, f, s, n = 1.0, 1.0, 0.0, 0.0
    for o in range(oct):
        n += a * vnoise3(np.asarray(P) * f, seed + o * 7919)
        s += a
        a *= gain
        f *= lac
    return n / s


# =========================================================================== #
#  4.  SMALL LINEAR ALGEBRA (numpy; mathutils is not available outside bpy)     #
# =========================================================================== #
def _n(v):
    v = np.asarray(v, float)
    L = np.linalg.norm(v)
    return v / L if L > 1e-12 else np.array([0.0, 0.0, 1.0])


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _euler(pitch_deg, roll_deg, yaw_deg):
    """Anatomical composite: yaw about +Z (left +), roll about +Y (right lean +),
    pitch about +X (right-hand rule; sign meaning depends on the bone direction,
    so every caller below states which way it bends)."""
    return _rz(math.radians(yaw_deg)) @ _ry(math.radians(roll_deg)) @ _rx(math.radians(pitch_deg))


def _frame_from_z(ez, up_hint=(0.0, 1.0, 0.0)):
    """Right-handed (ex, ey, ez) with ez given."""
    ez = _n(ez)
    h = np.asarray(up_hint, float)
    if abs(float(np.dot(h, ez))) > 0.97:
        h = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(h, ez))) > 0.97:
            h = np.array([0.0, 0.0, 1.0])
    ex = _n(np.cross(h, ez))
    ey = np.cross(ez, ex)
    return np.stack([ex, ey, ez], axis=1)          # columns


class Joint:
    """A solved joint: world-of-figure position plus an orthonormal frame whose
    third column is the bone axis (pointing at the child)."""
    __slots__ = ("p", "R")

    def __init__(self, p, R):
        self.p = np.asarray(p, float)
        self.R = np.asarray(R, float)

    @property
    def ex(self):
        return self.R[:, 0]

    @property
    def ey(self):
        return self.R[:, 1]

    @property
    def ez(self):
        return self.R[:, 2]

    def m4(self):
        M = np.eye(4)
        M[:3, :3] = self.R
        M[:3, 3] = self.p
        return M


def _ik2(root, target, l1, l2, swivel_deg, pole_hint):
    """Two-bone IK.  -> (mid, end, reached).

    Returns the elbow/knee position and the achieved end position.  If the target
    is out of reach the limb straightens and points AT the target: a short person
    whose feet cannot find the tread gets dangling legs, which is exactly what
    happens in a real grandstand and is 8 % of this crowd.
    """
    root = np.asarray(root, float)
    target = np.asarray(target, float)
    d = target - root
    L = float(np.linalg.norm(d))
    reached = True
    if L < 1e-6:
        d = np.array([0.0, 0.0, -1.0])
        L = 1e-6
    u = d / L
    Lmax = (l1 + l2) * 0.9985
    if L > Lmax:
        reached = False
        L = Lmax
        target = root + u * L
    Lmin = abs(l1 - l2) * 1.02 + 1e-4
    if L < Lmin:
        L = Lmin
        target = root + u * L
    cos_a = np.clip((l1 * l1 + L * L - l2 * l2) / (2.0 * l1 * L), -1.0, 1.0)
    a = math.acos(float(cos_a))
    # the swivel plane: a reference perpendicular, rotated about the root->target axis
    ref = np.asarray(pole_hint, float)
    ref = ref - u * float(np.dot(ref, u))
    if np.linalg.norm(ref) < 1e-6:
        ref = np.cross(u, [0.0, 0.0, 1.0])
    ref = _n(ref)
    bi = np.cross(u, ref)
    phi = math.radians(swivel_deg)
    nrm = ref * math.cos(phi) + bi * math.sin(phi)
    mid = root + l1 * (u * math.cos(a) + nrm * math.sin(a))
    return mid, target, reached


# =========================================================================== #
#  5.  THE WARDROBE REGISTRY  (spectator_clothing extends this)                 #
# =========================================================================== #
# Pure data.  `looseness` drives the baked fold amplitude; `thick` is the radial
# offset over bare skin; `sleeve` is the fraction of the arm the sleeve covers
# (0 = vest, 0.38 = t-shirt, 1.0 = full).  `hem` is the fraction of the torso
# from the pan upward at which the garment starts (below it: the bottom garment).
GARMENTS = {
    "tee":        dict(sleeve=0.36, thick=0.007, looseness=0.85, collar=0.010,
                       hood=0.0, hem=0.10, mat="cloth", flare=0.012, w=0.24),
    "polo":       dict(sleeve=0.42, thick=0.008, looseness=0.62, collar=0.026,
                       hood=0.0, hem=0.12, mat="cloth", flare=0.010, w=0.10),
    "longsleeve": dict(sleeve=0.97, thick=0.008, looseness=0.90, collar=0.012,
                       hood=0.0, hem=0.10, mat="cloth", flare=0.014, w=0.12),
    "shirt":      dict(sleeve=0.98, thick=0.011, looseness=1.25, collar=0.034,
                       hood=0.0, hem=0.06, mat="cloth", flare=0.022, w=0.09),
    "sweat":      dict(sleeve=1.00, thick=0.019, looseness=1.05, collar=0.024,
                       hood=0.0, hem=0.14, mat="knit", flare=0.006, w=0.09),
    "hoodie":     dict(sleeve=1.00, thick=0.024, looseness=1.15, collar=0.020,
                       hood=1.0, hem=0.13, mat="knit", flare=0.008, w=0.13),
    "jacket":     dict(sleeve=1.00, thick=0.030, looseness=0.80, collar=0.042,
                       hood=0.35, hem=0.09, mat="shell", flare=0.020, w=0.11),
    "puffer":     dict(sleeve=1.00, thick=0.050, looseness=0.45, collar=0.050,
                       hood=0.55, hem=0.10, mat="shell", flare=0.016, w=0.07),
    "gilet":      dict(sleeve=0.05, thick=0.034, looseness=0.50, collar=0.044,
                       hood=0.0, hem=0.11, mat="shell", flare=0.014, w=0.03),
    "vest":       dict(sleeve=0.02, thick=0.005, looseness=0.70, collar=0.006,
                       hood=0.0, hem=0.10, mat="cloth", flare=0.010, w=0.02),
}
BOTTOMS = {
    "jeans":    dict(thick=0.010, looseness=0.75, mat="denim", cuff=1.00, w=0.34),
    "trousers": dict(thick=0.009, looseness=0.95, mat="cloth", cuff=1.00, w=0.16),
    "joggers":  dict(thick=0.014, looseness=1.10, mat="knit", cuff=0.96, w=0.18),
    "shorts":   dict(thick=0.011, looseness=1.20, mat="cloth", cuff=0.46, w=0.19),
    "skirt":    dict(thick=0.010, looseness=1.30, mat="cloth", cuff=0.34, w=0.06),
    "cargo":    dict(thick=0.012, looseness=1.05, mat="cloth", cuff=1.00, w=0.07),
}
SHOES = {
    "trainer": dict(sole=0.026, h=0.098, len_k=1.00, toe=0.55, w=0.44),
    "runner":  dict(sole=0.032, h=0.104, len_k=1.02, toe=0.60, w=0.22),
    "boot":    dict(sole=0.030, h=0.150, len_k=0.97, toe=0.45, w=0.14),
    "flat":    dict(sole=0.014, h=0.070, len_k=0.96, toe=0.62, w=0.14),
    "sandal":  dict(sole=0.018, h=0.052, len_k=0.99, toe=0.70, w=0.06),
}
# hairline (u0) is given per style at the front / side / back of the skull, where
# u is the head spheroid parameter: +1 crown, -1 chin plane.
HAIR_STYLES = {
    "buzz":     dict(front=0.16, side=-0.10, back=-0.24, thick=0.004, fuzz=0.5, tail=0.0, bun=0.0, w=0.13),
    "short":    dict(front=0.22, side=-0.06, back=-0.18, thick=0.016, fuzz=1.0, tail=0.0, bun=0.0, w=0.28),
    "crop":     dict(front=0.30, side=0.02, back=-0.12, thick=0.022, fuzz=1.3, tail=0.0, bun=0.0, w=0.12),
    "medium":   dict(front=0.20, side=-0.22, back=-0.42, thick=0.026, fuzz=1.1, tail=0.0, bun=0.0, w=0.14),
    "long":     dict(front=0.18, side=-0.34, back=-0.62, thick=0.030, fuzz=0.9, tail=0.0, bun=0.0, w=0.10),
    "ponytail": dict(front=0.24, side=-0.14, back=-0.30, thick=0.018, fuzz=0.6, tail=1.0, bun=0.0, w=0.09),
    "bun":      dict(front=0.26, side=-0.10, back=-0.24, thick=0.016, fuzz=0.5, tail=0.0, bun=1.0, w=0.07),
    "bald":     dict(front=0.85, side=0.30, back=-0.05, thick=0.008, fuzz=1.6, tail=0.0, bun=0.0, w=0.07),
}

#: garment dyes.  A race-weekend crowd is mostly neutral with team colour in it —
#: an all-primary crowd looks like a toy, an all-grey crowd looks like a car park.
PALETTE = [
    ("#22262b", 1.00), ("#141821", 0.85), ("#3a4149", 0.90), ("#5d666e", 0.75),
    ("#8f9499", 0.60), ("#d6d8d6", 0.55), ("#f0eee8", 0.35), ("#1e3350", 0.85),
    ("#2c5f8a", 0.60), ("#3b7ea1", 0.35), ("#12303a", 0.40), ("#7b2027", 0.55),
    ("#a8322c", 0.50), ("#c9503a", 0.35), ("#d97b2b", 0.30), ("#e0a92c", 0.22),
    ("#2f5d3a", 0.40), ("#5b7a3a", 0.28), ("#6d5a3f", 0.30), ("#4b3a55", 0.20),
    ("#8d4a6b", 0.18), ("#c9c2a8", 0.30), ("#9aa7b5", 0.35), ("#2a2f52", 0.35),
]
DENIM = [("#33465e", 1.0), ("#26374a", 0.9), ("#4a5f78", 0.7), ("#1d2733", 0.8),
         ("#6b7b8c", 0.4), ("#2b2b30", 0.6)]
SKIN_TONES = [
    ("#f3d3bd", 0.16), ("#eac3a5", 0.17), ("#d9a684", 0.16), ("#c68a63", 0.14),
    ("#a86b46", 0.12), ("#8a5231", 0.10), ("#6b3d22", 0.08), ("#4a2a17", 0.07),
]
HAIR_COLS = [
    ("#181310", 0.30), ("#2b1d13", 0.20), ("#4a3120", 0.15), ("#6a4a2c", 0.10),
    ("#8a6a3e", 0.07), ("#b09161", 0.05), ("#9a9a97", 0.06), ("#d6d3cb", 0.04),
    ("#7a3418", 0.03),
]


def _srgb(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return o


def _pick(rng, table):
    tot = sum(w for _, w in table)
    r = rng.random() * tot
    for k, w in table:
        r -= w
        if r <= 0:
            return k
    return table[-1][0]


def _jit_col(rgb, rng, hue=0.02, sat=0.14, val=0.16):
    h, l, s = colorsys.rgb_to_hls(*rgb)
    h = (h + rng.uniform(-hue, hue)) % 1.0
    l = min(1.0, max(0.005, l * (1.0 + rng.uniform(-val, val))))
    s = min(1.0, max(0.0, s * (1.0 + rng.uniform(-sat, sat))))
    return list(colorsys.hls_to_rgb(h, l, s))


# =========================================================================== #
#  6.  THE POSTURE LIBRARY                                                     #
# =========================================================================== #
# A posture is a dict of angles and IK TARGETS, not joint rotations, so that it
# adapts to the person: the same "elbows on knees" solves to different elbow
# angles for a 1.58 m and a 1.93 m figure, and that difference is real geometry.
#
# Targets are given in a normalised seat frame and resolved against the solved
# body in `solve_skeleton`:
#   hand targets  ('knee'|'lap'|'seat'|'chest'|'free'|'head'|'thigh'), offset xyz
#   foot targets  ('tread'|'down'|'tuck'|'dangle'|'cross'|'rail'), offset xyz
#
# Angles, all degrees:
#   lean       torso forward lean  (+ forward)      distributed up the spine
#   slump      how much of the lean is a C-curve rather than a hip hinge
#   side       lateral lean (+ to the figure's right)
#   twist      torso rotation (+ to the figure's left)
#   head_*     pitch (+ down), yaw (+ left), roll (+ right ear down)
#   shrug      shoulder elevation
def posture(name, weight=1.0, **kw):
    d = dict(
        name=name, weight=weight, lean=6.0, slump=0.35, side=0.0, twist=0.0,
        head_pitch=2.0, head_yaw=0.0, head_roll=0.0, shrug=0.0,
        hand_L=("thigh", (0.0, 0.02, 0.03)), hand_R=("thigh", (0.0, 0.02, 0.03)),
        swivel_L=-42.0, swivel_R=-42.0,
        foot_L=("tread", (0.0, 0.0, 0.0)), foot_R=("tread", (0.0, 0.0, 0.0)),
        knee_out_L=7.0, knee_out_R=7.0, ankle_L=0.0, ankle_R=0.0,
        seat_slide=-0.055,        # sit-bones behind the pan centre (+ = forward)
        wrist_L=0.0, wrist_R=0.0, child_only=False, adult_only=False,
    )
    d.update(kw)
    d["name"] = name
    return d


POSTURES = {p["name"]: p for p in [
    posture("upright", 1.00, lean=4, slump=0.25, head_pitch=1,
            hand_L=("thigh", (0.0, 0.06, 0.04)), hand_R=("thigh", (0.0, 0.06, 0.04)),
            swivel_L=-38, swivel_R=-38),
    posture("forward_elbows_knees", 0.95, lean=31, slump=0.55, head_pitch=6,
            hand_L=("knee", (-0.055, 0.02, 0.11)), hand_R=("knee", (0.055, 0.02, 0.11)),
            swivel_L=-8, swivel_R=-8, seat_slide=0.015,
            foot_L=("tread", (0.0, 0.03, 0.0)), foot_R=("tread", (0.0, 0.03, 0.0)),
            knee_out_L=13, knee_out_R=13),
    posture("back_arms_folded", 0.90, lean=-9, slump=0.15, head_pitch=-2,
            hand_L=("chest", (0.075, 0.035, -0.03)), hand_R=("chest", (-0.075, 0.035, -0.03)),
            swivel_L=32, swivel_R=32, seat_slide=-0.075,
            foot_L=("down", (0.0, -0.04, 0.0)), foot_R=("down", (0.0, -0.04, 0.0)),
            knee_out_L=11, knee_out_R=11),
    posture("back_arms_spread", 0.55, lean=-11, slump=0.10, head_pitch=-4,
            hand_L=("seat", (0.10, -0.16, 0.16)), hand_R=("seat", (-0.10, -0.16, 0.16)),
            swivel_L=-4, swivel_R=-4, seat_slide=-0.080, shrug=-3,
            foot_L=("down", (0.02, 0.0, 0.0)), foot_R=("down", (-0.02, 0.0, 0.0)),
            knee_out_L=16, knee_out_R=16),
    posture("turn_to_neighbour", 0.85, lean=9, slump=0.30, twist=26, side=4,
            head_yaw=34, head_pitch=1,
            hand_L=("thigh", (0.02, 0.10, 0.05)), hand_R=("knee", (0.02, -0.02, 0.10)),
            swivel_L=-30, swivel_R=-16, knee_out_L=9, knee_out_R=6),
    # the hand targets are INSIDE the arm's reach on purpose: a target past the
    # reach straightens the limb, and two straight arms read as two sticks.
    posture("cheer_both_arms", 0.28, lean=-4, slump=0.10, head_pitch=-11, shrug=9,
            hand_L=("free", (0.26, 0.11, 0.40)), hand_R=("free", (-0.26, 0.11, 0.40)),
            swivel_L=-64, swivel_R=-64, seat_slide=0.010,
            foot_L=("tread", (0.0, 0.02, 0.0)), foot_R=("tread", (0.0, 0.02, 0.0))),
    posture("point_one_arm", 0.34, lean=7, slump=0.25, twist=-8,
            head_pitch=-5, head_yaw=-12,
            hand_L=("thigh", (0.0, 0.05, 0.03)), hand_R=("free", (-0.36, 0.34, 0.34)),
            swivel_L=-40, swivel_R=-52),
    posture("hands_behind_head", 0.30, lean=-7, slump=0.15, head_pitch=-3,
            hand_L=("head", (0.085, -0.10, 0.055)), hand_R=("head", (-0.085, -0.10, 0.055)),
            swivel_L=-88, swivel_R=-88, seat_slide=-0.070,
            foot_L=("down", (0.0, 0.02, 0.0)), foot_R=("down", (0.0, 0.02, 0.0)),
            knee_out_L=18, knee_out_R=18),
    posture("elbow_on_knee_side", 0.60, lean=22, slump=0.45, side=11, twist=-13,
            head_pitch=4, head_roll=7,
            hand_L=("thigh", (0.0, 0.09, 0.04)), hand_R=("head", (-0.045, 0.055, -0.10)),
            swivel_L=-34, swivel_R=-2, seat_slide=0.005, knee_out_R=15),
    posture("slouch_low", 0.75, lean=17, slump=0.85, head_pitch=8,
            hand_L=("lap", (0.045, 0.02, 0.02)), hand_R=("lap", (-0.045, 0.02, 0.02)),
            swivel_L=-24, swivel_R=-24, seat_slide=0.085,
            foot_L=("down", (0.0, 0.11, 0.0)), foot_R=("down", (0.0, 0.11, 0.0)),
            knee_out_L=14, knee_out_R=14),
    posture("hands_in_lap", 0.85, lean=8, slump=0.40, head_pitch=4,
            hand_L=("lap", (0.035, 0.03, 0.025)), hand_R=("lap", (-0.035, 0.03, 0.025)),
            swivel_L=-30, swivel_R=-30, knee_out_L=5, knee_out_R=5),
    posture("reach_down_side", 0.30, lean=26, slump=0.50, side=15, twist=17,
            head_pitch=17, head_yaw=13,
            hand_L=("seat", (0.20, -0.02, -0.30)), hand_R=("knee", (0.02, 0.0, 0.09)),
            swivel_L=-14, swivel_R=-20, seat_slide=0.020),
    posture("watching_up", 0.55, lean=2, slump=0.20, head_pitch=-14, head_yaw=-7,
            hand_L=("knee", (-0.03, 0.02, 0.10)), hand_R=("thigh", (0.0, 0.10, 0.05)),
            swivel_L=-12, swivel_R=-36, knee_out_L=10, knee_out_R=8),
    posture("legs_crossed", 0.45, lean=6, slump=0.30, side=-3, twist=-6,
            head_pitch=2, head_yaw=-8,
            hand_L=("knee", (0.0, 0.05, 0.10)), hand_R=("thigh", (0.0, 0.08, 0.05)),
            swivel_L=-20, swivel_R=-38, foot_L=("cross", (0.0, 0.0, 0.0)),
            foot_R=("tread", (-0.03, 0.0, 0.0)), knee_out_L=-9, knee_out_R=10,
            ankle_L=-16),
    posture("child_kneel_up", 0.55, lean=9, slump=0.20, head_pitch=-6,
            hand_L=("free", (0.16, 0.30, 0.10)), hand_R=("free", (-0.16, 0.30, 0.10)),
            swivel_L=-30, swivel_R=-30, seat_slide=0.020,
            foot_L=("kneel", (0.0, 0.0, 0.0)), foot_R=("kneel", (0.0, 0.0, 0.0)),
            knee_out_L=13, knee_out_R=13, child_only=True),
    posture("child_perch", 0.60, lean=12, slump=0.30, head_pitch=1, head_yaw=16,
            hand_L=("seat", (0.13, -0.05, 0.02)), hand_R=("seat", (-0.13, -0.05, 0.02)),
            swivel_L=-18, swivel_R=-18, seat_slide=0.070,
            foot_L=("dangle", (0.0, 0.0, 0.0)), foot_R=("dangle", (0.02, 0.03, 0.0)),
            knee_out_L=6, knee_out_R=8, child_only=True),
]}


# =========================================================================== #
#  7.  THE PERSON                                                              #
# =========================================================================== #
class FigureSpec(dict):
    """A plain dict subclass so dependants can serialise it and read it without
    importing anything.  Attribute access is a convenience only."""

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e


def sample_spec(index, seed=SEED, force_posture=None, force_child=None):
    """Deterministic person number `index`.  Same (index, seed) -> same human."""
    import random
    rng = random.Random((int(seed) * 1000003) ^ (int(index) * 2654435761))

    child = rng.random() < 0.08 if force_child is None else bool(force_child)
    if child:
        child_f = rng.uniform(0.55, 1.0)
        stature = rng.uniform(1.09, 1.51) - 0.10 * (child_f - 0.55)
        build_k = rng.uniform(0.86, 1.10)
    else:
        child_f = 0.0
        # a bimodal stature population reads as mixed adults rather than as one
        # scaled template: two overlapping normals, not a single uniform.
        if rng.random() < 0.48:
            stature = min(1.86, max(1.49, rng.gauss(1.633, 0.062)))
        else:
            stature = min(1.99, max(1.58, rng.gauss(1.766, 0.068)))
        build_k = min(1.42, max(0.83, rng.gauss(1.045, 0.115)))

    fem = rng.random() < (0.34 if not child else 0.48)
    shoulder_k = rng.uniform(0.90, 0.965) if fem else rng.uniform(0.985, 1.055)
    bust = rng.uniform(0.010, 0.032) * (1.0 + 0.5 * (build_k - 1.0)) if fem else 0.0

    # posture choice, respecting child-only / adult-only entries
    cand = [p for p in POSTURES.values()
            if not (p["child_only"] and not child) and not (p["adult_only"] and child)]
    if force_posture:
        pos = POSTURES[force_posture]
    else:
        tot = sum(p["weight"] for p in cand)
        r = rng.random() * tot
        pos = cand[-1]
        for p in cand:
            r -= p["weight"]
            if r <= 0:
                pos = p
                break

    top = _pick(rng, [(k, v["w"]) for k, v in GARMENTS.items()])
    bot = _pick(rng, [(k, v["w"]) for k, v in BOTTOMS.items()])
    if child and top in ("jacket", "puffer", "gilet"):
        top = rng.choice(["tee", "hoodie", "longsleeve", "sweat"])
    shoe = _pick(rng, [(k, v["w"]) for k, v in SHOES.items()])
    hair = _pick(rng, [(k, v["w"]) for k, v in HAIR_STYLES.items()])
    if child and hair == "bald":
        hair = "short"
    if not fem and hair in ("long", "ponytail", "bun") and rng.random() < 0.72:
        hair = rng.choice(["short", "crop", "buzz", "medium"])

    top_col = _jit_col(_srgb(_pick(rng, PALETTE)), rng)
    bot_col = _jit_col(_srgb(_pick(rng, DENIM if BOTTOMS[bot]["mat"] == "denim"
                                   else PALETTE)), rng, val=0.12)
    skin = _jit_col(_srgb(_pick(rng, SKIN_TONES)), rng, hue=0.006, sat=0.08, val=0.07)
    hair_col = _jit_col(_srgb(_pick(rng, HAIR_COLS)), rng, hue=0.01, sat=0.10, val=0.18)
    shoe_col = _jit_col(_srgb(_pick(rng, PALETTE)), rng, val=0.20)

    # per-instance posture jitter: every angle moves, and the two sides move
    # independently, so no two figures share a shoulder line.
    j = dict(
        lean=rng.gauss(0, 4.2), slump=rng.uniform(-0.12, 0.12),
        side=rng.gauss(0, 4.0), twist=rng.gauss(0, 7.5),
        head_pitch=rng.gauss(0, 5.5), head_yaw=rng.gauss(0, 13.0),
        head_roll=rng.gauss(0, 4.5), shrug=rng.gauss(0, 2.6),
        swivel_L=rng.gauss(0, 9.0), swivel_R=rng.gauss(0, 9.0),
        knee_out_L=rng.gauss(0, 4.5), knee_out_R=rng.gauss(0, 4.5),
        seat_slide=rng.gauss(0, 0.018),
        hand_L=(rng.gauss(0, 0.024), rng.gauss(0, 0.026), rng.gauss(0, 0.022)),
        hand_R=(rng.gauss(0, 0.024), rng.gauss(0, 0.026), rng.gauss(0, 0.022)),
        foot_L=(rng.gauss(0, 0.026), rng.gauss(0, 0.033), 0.0),
        foot_R=(rng.gauss(0, 0.026), rng.gauss(0, 0.033), 0.0),
    )
    mirror = rng.random() < 0.5

    return FigureSpec(
        index=int(index), seed=int(seed), child=child, child_f=child_f,
        stature=stature, build_k=build_k, fem=fem, bust=bust,
        shoulder_k=shoulder_k, leg_k=rng.uniform(0.955, 1.045),
        arm_k=rng.uniform(0.96, 1.04), neck_k=rng.uniform(0.9, 1.12),
        head_k=rng.uniform(0.96, 1.045),
        posture=pos["name"], jitter=j, mirror=mirror,
        top=top, bottom=bot, shoe=shoe, hair=hair,
        hood_up=(GARMENTS[top]["hood"] > 0.5 and rng.random() < 0.22),
        col_top=top_col, col_bottom=bot_col, col_skin=skin, col_hair=hair_col,
        col_shoe=shoe_col,
        sleeve_push=rng.uniform(0.0, 0.22) if GARMENTS[top]["sleeve"] > 0.8 else 0.0,
        fold_seed=rng.randrange(1 << 24), fold_k=rng.uniform(0.75, 1.35),
        belly=rng.uniform(0.0, 0.030) * max(0.0, build_k - 0.95) * 12.0,
        posture_rng=rng.random(),
    )


def pose_of(spec):
    """The resolved posture dict for `spec` (base posture + per-instance jitter).

    Public so `crowd_idle_motion` can take this, perturb it over time and re-solve
    without touching the mesh code.
    """
    p = dict(POSTURES[spec["posture"]])
    j = spec["jitter"]
    m = -1.0 if spec["mirror"] else 1.0
    for k in ("lean", "slump", "side", "twist", "head_pitch", "head_yaw",
              "head_roll", "shrug", "seat_slide"):
        p[k] = p[k] + j[k]
    if m < 0:                        # a real mirrored figure, not a rotated copy
        p["side"] = -p["side"]
        p["twist"] = -p["twist"]
        p["head_yaw"] = -p["head_yaw"]
        p["head_roll"] = -p["head_roll"]
        for a, b in (("hand_L", "hand_R"), ("foot_L", "foot_R"),
                     ("swivel_L", "swivel_R"), ("knee_out_L", "knee_out_R"),
                     ("ankle_L", "ankle_R")):
            pa, pb = p[a], p[b]
            if isinstance(pa, tuple) and isinstance(pa[1], tuple):
                p[a] = (pb[0], (-pb[1][0], pb[1][1], pb[1][2]))
                p[b] = (pa[0], (-pa[1][0], pa[1][1], pa[1][2]))
            else:
                p[a], p[b] = pb, pa
    for side in ("L", "R"):
        k = "hand_" + side
        p[k] = (p[k][0], tuple(a + b for a, b in zip(p[k][1], j[k])))
        k = "foot_" + side
        p[k] = (p[k][0], tuple(a + b for a, b in zip(p[k][1], j[k])))
        p["swivel_" + side] += j["swivel_" + side]
        p["knee_out_" + side] += j["knee_out_" + side]
    p["slump"] = min(0.95, max(0.0, p["slump"] + j["slump"]))
    return p


# =========================================================================== #
#  8.  THE SKELETON SOLVE                                                      #
# =========================================================================== #
SPINE_SEGS = ("l5", "l3", "t12", "t8", "t4", "c7")
#: how the total forward lean is distributed up the spine in the two limits.
#: HINGE is a flat back rotating about the hips; CURVE is a slumped C-back.
_HINGE_W = np.array([0.34, 0.24, 0.16, 0.12, 0.09, 0.05])
_CURVE_W = np.array([0.06, 0.11, 0.17, 0.22, 0.24, 0.20])


def solve_skeleton(spec, pose=None):
    """-> dict[str, Joint] in the figure local frame (origin = seat pan centre)."""
    p = pose_of(spec) if pose is None else pose
    S = _segments(spec["stature"], spec["child_f"], spec["build_k"],
                  spec["shoulder_k"], spec["leg_k"], spec["arm_k"])
    S = dict(S)
    S["neck_len"] *= spec["neck_k"]
    for k in ("head_h", "head_w", "head_d"):
        S[k] *= spec["head_k"]
    J = {}

    # ---- pelvis ---------------------------------------------------------- #
    # the sit bones are on the pan; the pelvis centre is above and behind them.
    sit_y = p["seat_slide"]
    pelv_h = 0.085 + 0.03 * spec["build_k"]
    Rp = _euler(0.0, p["side"] * 0.30, p["twist"] * 0.30)
    pelvis = np.array([0.0, sit_y - 0.012, pelv_h * (1.0 - 0.25 * p["slump"])])
    J["pelvis"] = Joint(pelvis, Rp)

    # ---- spine ------------------------------------------------------------ #
    w = _HINGE_W * (1.0 - p["slump"]) + _CURVE_W * p["slump"]
    w = w / w.sum()
    # `torso_len` is measured FROM THE PAN to C7, and the spine chain starts at
    # the pelvis joint which is already `pelv_h` up: the chain gets the remainder.
    # Getting this wrong made every figure 0.12 m too tall — sitting height came
    # out 0.59 x stature instead of the tabulated 0.52.
    spine_run = max(0.12, S["torso_len"] - pelv_h)
    seg_len = spine_run * np.array([0.155, 0.175, 0.185, 0.185, 0.175, 0.125])
    R = Rp.copy()
    q = pelvis.copy()
    for i, nm in enumerate(SPINE_SEGS):
        # a bone pointing +Z leans FORWARD for a NEGATIVE rotation about +X
        R = R @ _euler(-p["lean"] * w[i], p["side"] * w[i] * 1.15,
                       p["twist"] * w[i] * 1.25)
        J["spine_" + nm] = Joint(q.copy(), R.copy())
        q = q + R[:, 2] * seg_len[i]
    J["chest_top"] = Joint(q.copy(), R.copy())
    chestR = R.copy()

    # ---- neck and head ---------------------------------------------------- #
    Rn = chestR @ _euler(-p["head_pitch"] * 0.35, p["head_roll"] * 0.30,
                         p["head_yaw"] * 0.30)
    neck0 = q + chestR[:, 1] * (0.012 * spec["stature"]) + chestR[:, 2] * (0.006 * spec["stature"])
    J["neck"] = Joint(neck0, Rn)
    Rh = Rn @ _euler(-p["head_pitch"] * 0.65, p["head_roll"] * 0.70,
                     p["head_yaw"] * 0.70)
    # 0.80, not 1.00: the head sits DOWN into the shoulder yoke.  The first pass
    # put the full neck length between the trapezius and the skull and every
    # figure in the stand read as a bottle - a bright skin-toned column under
    # the head, 15 px of it, which at 47 px of head is a third of the read.
    head_base = neck0 + Rn[:, 2] * (S["neck_len"] * 0.80)
    J["head"] = Joint(head_base, Rh)
    # the skull centre sits forward of the atlas, not on it
    hc = head_base + Rh[:, 2] * (S["head_h"] * 0.46) + Rh[:, 1] * (S["head_d"] * 0.055)
    J["head_centre"] = Joint(hc, Rh)

    # ---- shoulders -------------------------------------------------------- #
    shrug = math.radians(p["shrug"])
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        cl = q + chestR[:, 0] * (sgn * S["shoulder_hw"] * 0.30) \
               + chestR[:, 2] * (-0.030 * spec["stature"] + 0.02 * shrug)
        sh = q + chestR[:, 0] * (sgn * S["shoulder_hw"]) \
               + chestR[:, 2] * (-0.052 * spec["stature"] + 0.055 * shrug) \
               + chestR[:, 1] * (-0.006 * spec["stature"])
        J["clav_" + side] = Joint(cl, chestR.copy())
        J["shoulder_" + side] = Joint(sh, chestR.copy())

    # ---- hips ------------------------------------------------------------- #
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        hp = pelvis + Rp[:, 0] * (sgn * S["hip_hw"] * 0.72) \
                    + Rp[:, 1] * (0.010) + Rp[:, 2] * (-0.020)
        J["hip_" + side] = Joint(hp, Rp.copy())

    # ---- legs (IK to a foot target) --------------------------------------- #
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        hip = J["hip_" + side]
        kind, off = p["foot_" + side]
        ankle_r = S["ankle_r"]
        foot_z = TREAD_Z + S["foot_h"] * 0.55
        if kind == "tread":
            tgt = np.array([sgn * (S["hip_hw"] * 0.80), RAKE["pan_half_depth_m"] - 0.045,
                            foot_z])
        elif kind == "down":
            tgt = np.array([sgn * (S["hip_hw"] * 0.90), TREAD_NOSING_Y + 0.20,
                            TREAD_DOWN_Z + S["foot_h"] * 0.55])
        elif kind == "tuck":
            tgt = np.array([sgn * (S["hip_hw"] * 0.75), 0.055, foot_z + 0.02])
        elif kind == "cross":
            tgt = np.array([-sgn * 0.075, 0.30, TREAD_Z + 0.31])
        elif kind == "kneel":
            tgt = np.array([sgn * (S["hip_hw"] * 0.80), -0.16, 0.02])
        else:                                        # dangle
            tgt = np.array([sgn * (S["hip_hw"] * 0.85), 0.30,
                            max(TREAD_Z + S["foot_h"] * 0.55, -S["thigh"] - S["shank"] * 0.92)])
        tgt = tgt + np.array(off)
        pole = np.array([sgn * math.sin(math.radians(p["knee_out_" + side])), 1.0,
                         0.35])
        knee, ankle, reached = _ik2(hip.p, tgt, S["thigh"], S["shank"],
                                    0.0, pole)
        if not reached and kind in ("tread", "down"):
            # the foot did not make the step: it hangs, toe down.  8 % children.
            d = _n(ankle - hip.p)
            ankle = hip.p + d * (S["thigh"] + S["shank"]) * 0.98
            knee, ankle, _ = _ik2(hip.p, ankle, S["thigh"], S["shank"], 0.0, pole)
        za = _n(knee - hip.p)
        J["knee_" + side] = Joint(knee, _frame_from_z(za, up_hint=(0, 1, 0)))
        zb = _n(ankle - knee)
        J["ankle_" + side] = Joint(ankle, _frame_from_z(zb, up_hint=(0, 1, 0)))
        # the foot: pitch from the ankle, toe-out yaw
        fdir = _n(np.array([sgn * math.sin(math.radians(9.0)), 1.0, 0.0]))
        pitch = math.radians(p["ankle_" + side] + (-24.0 if not reached else 0.0))
        fdir = _n(fdir + np.array([0.0, 0.0, math.tan(pitch)]))
        J["foot_" + side] = Joint(ankle, _frame_from_z(fdir, up_hint=(0, 0, 1)))

    # ---- arms (IK to a hand target) --------------------------------------- #
    lap_z = None
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        sh = J["shoulder_" + side]
        knee = J["knee_" + side].p
        kind, off = p["hand_" + side]
        if kind == "knee":
            base = knee + np.array([0.0, 0.0, S["knee_r"]])
        elif kind == "thigh":
            base = (J["hip_" + side].p + knee) * 0.5 + np.array([0.0, 0.0, S["thigh_r"]])
        elif kind == "lap":
            if lap_z is None:
                lap_z = float(max((J["hip_L"].p + J["knee_L"].p)[2],
                                  (J["hip_R"].p + J["knee_R"].p)[2]) * 0.5) + S["thigh_r"]
            mid = (J["knee_L"].p + J["knee_R"].p) * 0.5
            base = np.array([0.0, mid[1] * 0.55 + 0.02, lap_z + 0.02])
        elif kind == "chest":
            base = J["spine_t8"].p + chestR[:, 1] * (S["chest_hd"] + 0.045)
        elif kind == "seat":
            base = np.array([sgn * (RAKE["pan_half_width_m"] + 0.055), -0.02, 0.045])
        elif kind == "head":
            base = J["head_centre"].p
        else:                                        # free
            base = J["chest_top"].p
        tgt = base + np.array(off) * np.array([1.0, 1.0, 1.0])
        pole = -chestR[:, 1] * 0.6 + np.array([0.0, 0.0, -1.0])
        elbow, wrist, _ = _ik2(sh.p, tgt, S["upperarm"], S["forearm"],
                               p["swivel_" + side] * (-1.0 if side == "L" else 1.0),
                               pole)
        za = _n(elbow - sh.p)
        J["elbow_" + side] = Joint(elbow, _frame_from_z(za, up_hint=(0, 1, 0)))
        zb = _n(wrist - elbow)
        J["wrist_" + side] = Joint(wrist, _frame_from_z(zb, up_hint=(0, 1, 0)))
        hand_dir = zb
        J["hand_" + side] = Joint(wrist + hand_dir * (S["hand_len"] * 0.42),
                                  _frame_from_z(hand_dir, up_hint=chestR[:, 1]))
    J["_seg"] = S
    J["_pose"] = p
    return J


# =========================================================================== #
#  9.  THE SKIN — lofted elliptical sections with baked cloth folds             #
# =========================================================================== #
MAT_SKIN, MAT_CLOTH, MAT_KNIT, MAT_DENIM, MAT_SHELL, MAT_HAIR, MAT_SHOE = range(7)
MAT_NAMES = ["Skin", "Cloth", "Knit", "Denim", "Shell", "Hair", "Shoe"]
_MATKEY = {"cloth": MAT_CLOTH, "knit": MAT_KNIT, "denim": MAT_DENIM,
           "shell": MAT_SHELL}

DETAIL = {
    "hero": dict(nrad_torso=30, nrad_limb=18, nrad_head=28, ds=0.017,
                 folds=1.0, hands=1, ears=1, nose=1, hair_rings=9),
    "mid":  dict(nrad_torso=18, nrad_limb=11, nrad_head=16, ds=0.030,
                 folds=0.7, hands=0, ears=0, nose=1, hair_rings=6),
    "far":  dict(nrad_torso=10, nrad_limb=7, nrad_head=9, ds=0.055,
                 folds=0.0, hands=0, ears=0, nose=0, hair_rings=3),
}


class _Acc:
    """Vertex/face accumulator.  Quads where possible, tris at the poles."""

    def __init__(self):
        self.V, self.C, self.F, self.M = [], [], [], []
        self.n = 0

    def add(self, verts, cols, faces, mat):
        verts = np.asarray(verts, float).reshape(-1, 3)
        k = len(verts)
        self.V.append(verts)
        if np.ndim(cols) == 1:
            cols = np.tile(np.asarray(cols, float)[None, :3], (k, 1))
        self.C.append(np.asarray(cols, float).reshape(-1, 3))
        for f in faces:
            self.F.append([int(i) + self.n for i in f])
            self.M.append(mat)
        self.n += k

    # -- a strip of rings --------------------------------------------------- #
    def tube(self, rings, mat, cols, cap0=None, cap1=None):
        """rings: list of (nrad,3).  cols: (3,) or list of (3,) per ring."""
        nr = len(rings)
        nrad = len(rings[0])
        V = np.concatenate([np.asarray(r, float) for r in rings], axis=0)
        if isinstance(cols, (list, tuple)) and len(cols) == nr and np.ndim(cols[0]) == 1:
            C = np.concatenate([np.tile(np.asarray(c, float)[None, :3], (nrad, 1))
                                for c in cols], axis=0)
        else:
            C = np.tile(np.asarray(cols, float)[None, :3], (nr * nrad, 1))
        F = []
        for i in range(nr - 1):
            a, b = i * nrad, (i + 1) * nrad
            for j in range(nrad):
                k = (j + 1) % nrad
                F.append((a + j, a + k, b + k, b + j))
        base = self.n
        self.add(V, C, F, mat)
        if cap0 is not None:
            self._pole(base, nrad, cap0, mat, C[0], flip=True)
        if cap1 is not None:
            self._pole(base + (nr - 1) * nrad, nrad, cap1, mat, C[-1], flip=False)

    def _pole(self, ring_start, nrad, apex, mat, col, flip):
        idx = self.n
        self.add(np.asarray(apex, float)[None, :], np.asarray(col)[None, :3], [], mat)
        for j in range(nrad):
            k = (j + 1) % nrad
            f = (ring_start + j, ring_start + k, idx)
            self.F.append([f[2], f[1], f[0]] if flip else list(f))
            self.M.append(mat)


def _ring(P, ex, ey, rx, ry, th, mod=None, off=None):
    """One elliptical cross-section.  `mod` scales, `off` adds metres radially."""
    c, s = np.cos(th), np.sin(th)
    if mod is not None:
        c = c * mod
        s = s * mod
    X = c * rx
    Y = s * ry
    if off is not None:
        d = np.stack([np.cos(th), np.sin(th)], axis=1)
        X = X + d[:, 0] * off
        Y = Y + d[:, 1] * off
    return P[None, :] + X[:, None] * ex[None, :] + Y[:, None] * ey[None, :]


def _smooth_polyline(P, passes=2, w=0.5):
    P = np.asarray(P, float).copy()
    for _ in range(passes):
        Q = P.copy()
        Q[1:-1] = (1 - w) * P[1:-1] + w * 0.5 * (P[:-2] + P[2:])
        P = Q
    return P


def _resample(P, n):
    P = np.asarray(P, float)
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-9:
        return np.tile(P[0], (n, 1))
    t = np.linspace(0.0, d[-1], n)
    return np.stack([np.interp(t, d, P[:, k]) for k in range(3)], axis=1)


def _transport(P, up0):
    """Parallel-transport frames along a polyline. -> list of (ex, ey, ez)."""
    n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    frames = []
    ref = np.asarray(up0, float)
    ref = _n(ref - T[0] * float(np.dot(ref, T[0])))
    for i in range(n):
        if i:
            v = np.cross(T[i - 1], T[i])
            s = np.linalg.norm(v)
            if s > 1e-9:
                v = v / s
                a = math.atan2(s, float(np.dot(T[i - 1], T[i])))
                ca, sa = math.cos(a), math.sin(a)
                ref = ref * ca + np.cross(v, ref) * sa + v * float(np.dot(v, ref)) * (1 - ca)
                ref = _n(ref - T[i] * float(np.dot(ref, T[i])))
        ex = _n(np.cross(ref, T[i]))
        ey = np.cross(T[i], ex)
        frames.append((ex, ey, T[i]))
    return frames


def _sstep01(x):
    x = min(1.0, max(0.0, float(x)))
    return x * x * (3.0 - 2.0 * x)


def _station_z(P):
    """Height of a torso station above the seat pan, in the figure local frame."""
    return float(P[2])


def _folds(pts, th, amp, seed, k=(9.0, 26.0, 5.0)):
    """Baked cloth folds: a radial offset field in metres, evaluated on the ring
    points themselves so folds are continuous across parts of the garment.

    THIS IS GEOMETRY.  At 203 px/m an 8 mm fold is 1.6 px of shading and a 40 mm
    fold at the hem is 8 px of silhouette; a normal map cannot put the hem in the
    wrong place, which is what makes cloth look like cloth.
    """
    if amp <= 0.0:
        return None
    P = np.asarray(pts, float)
    a = fbm3(P * np.array(k), seed=seed, oct=3) - 0.5
    b = vnoise3(P * np.array([k[0] * 2.6, k[1] * 0.7, k[2] * 2.4]),
                seed=seed + 5501) - 0.5
    return amp * (a * 1.45 + b * 0.55)


# ---- the parts ------------------------------------------------------------ #
def _torso(acc, spec, J, D, cfg):
    S, p = J["_seg"], J["_pose"]
    g = GARMENTS[spec["top"]]
    b = BOTTOMS[spec["bottom"]]
    nrad = cfg["nrad_torso"]
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)

    # centreline: pelvis -> chest_top, through the solved spine
    P = [J["pelvis"].p - J["pelvis"].R[:, 2] * (0.045 * spec["stature"])]
    P += [J["spine_" + s].p for s in SPINE_SEGS]
    P.append(J["chest_top"].p)
    P = _resample(np.asarray(P), 9)
    P = _smooth_polyline(P, 2, 0.5)
    n = max(14, int(np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)) / cfg["ds"]))
    P = _resample(P, n)
    P = _smooth_polyline(P, 1, 0.35)
    frames = _transport(P, up0=J["pelvis"].R[:, 1])
    t = np.linspace(0.0, 1.0, n)

    # radial profile: seat mass -> hip -> waist -> chest -> shoulder yoke -> neck
    # THE TOP OF THE TORSO IS A SLAB, NOT A CONE.  The first pass tapered the
    # chest to neck_r*2.15 at C7, so the arms hung off a narrow stalk with a
    # ball at each shoulder and every figure read as a bowling pin.  The upper
    # chest stays wide and the shoulder yoke below does the trapezius.
    key_t = np.array([0.00, 0.10, 0.28, 0.48, 0.68, 0.86, 1.00])
    kx = np.array([S["hip_hw"] * 1.02, S["hip_hw"], S["waist_hw"],
                   S["waist_hw"] * 1.03, S["chest_hw"], S["chest_hw"] * 1.00,
                   S["chest_hw"] * 0.80])
    ky = np.array([S["hip_hd"] * 1.16, S["hip_hd"] * 1.04, S["waist_hd"],
                   S["waist_hd"] * 1.02, S["chest_hd"], S["chest_hd"] * 0.99,
                   S["chest_hd"] * 0.86])
    RX = np.interp(t, key_t, kx)
    RY = np.interp(t, key_t, ky)

    hem = g["hem"]
    rings, cols, mats = [], [], []
    cs_top = np.asarray(spec["col_top"], float)
    cs_bot = np.asarray(spec["col_bottom"], float)
    for i in range(n):
        ex, ey, ez = frames[i]
        ti = t[i]
        cloth_top = ti >= hem
        thick = g["thick"] if cloth_top else b["thick"]
        loose = g["looseness"] if cloth_top else b["looseness"]
        col = cs_top if cloth_top else cs_bot
        mat = _MATKEY[g["mat"]] if cloth_top else _MATKEY[b["mat"]]
        # cross-section shaping: flat-ish back, spine groove, belly, bust, blades
        m = np.ones(nrad)
        back = np.exp(-((np.cos(th - 1.5 * math.pi) - 1.0) * 3.4) ** 2)
        front = np.exp(-((np.cos(th - 0.5 * math.pi) - 1.0) * 3.0) ** 2)
        m -= 0.055 * back * (0.4 + 0.6 * math.sin(math.pi * min(1.0, ti / 0.9)))
        blades = np.exp(-(((th - 1.5 * math.pi) ** 2) / 0.20))
        m += 0.030 * blades * math.exp(-((ti - 0.70) / 0.14) ** 2)
        belly = spec["belly"] * math.exp(-((ti - 0.24) / 0.20) ** 2)
        offs = np.zeros(nrad)
        offs += belly * front
        if spec["bust"] > 0 and not spec["child"]:
            bl = np.exp(-((th - (0.5 * math.pi - 0.36)) ** 2) / 0.030)
            br = np.exp(-((th - (0.5 * math.pi + 0.36)) ** 2) / 0.030)
            offs += spec["bust"] * (bl + br) * math.exp(-((ti - 0.60) / 0.10) ** 2)
        # garment thickness ramps in at the hem, and the hem itself stands off.
        # THE FLARE IS GATED ABOVE THE PAN.  In macro pass 2 the hem sat at
        # ti = 0.09, which on a seated figure is level with the seat, so the
        # flare and the fold field pushed the cloth out 40 mm and the buttock
        # flattening then spread it into a flat disc: every heavy figure wore a
        # cape.  Cloth pinched under a sitter does not billow, it is under him.
        if cloth_top:
            ramp = min(1.0, (ti - hem) / 0.10)
            offs += thick * (0.35 + 0.65 * ramp)
            above = _sstep01((_station_z(P[i]) - 0.045) / 0.085)
            offs += g["flare"] * above * math.exp(-((ti - hem) / 0.055) ** 2)
            # THE HEM ITSELF: a 4 mm lip where the fabric doubles back.  1 px at
            # the filmed distance, and it is the difference between a garment
            # and a painted stripe.
            offs += 0.004 * math.exp(-((ti - hem) / 0.016) ** 2)
            # placket / zip line down the front centre of anything that opens
            if g["collar"] > 0.020:
                offs -= 0.0035 * np.exp(-((th - 0.5 * math.pi) / 0.11) ** 2)
            # kangaroo pocket on a hoodie or sweat
            if g["hood"] > 0.5 or spec["top"] == "sweat":
                offs += 0.0075 * np.clip(np.cos(th - 0.5 * math.pi), 0, 1) ** 2 \
                    * math.exp(-((ti - (hem + 0.13)) / 0.075) ** 2)
        else:
            offs += thick
            # waistband: a 6 mm band, which is where the top garment stops
            offs += 0.006 * math.exp(-((ti - (hem - 0.030)) / 0.022) ** 2)
            if ti > hem - 0.10:
                offs += b["thick"] * 0.5
        ring = _ring(P[i], ex, ey, RX[i], RY[i], th, mod=m, off=offs)
        # k_z is deliberately much lower than k_x/k_y: a low z-frequency makes
        # the noise features LONG in z, which is what a garment hanging off the
        # shoulders actually does - vertical drape folds, not random lumps.
        # folds die out where the body meets the pan
        seat_fade = _sstep01((float(P[i][2]) - 0.030) / 0.080)
        f = _folds(ring, th, cfg["folds"] * 0.0170 * loose * spec["fold_k"] * seat_fade,
                   spec["fold_seed"], k=(9.5, 9.5, 3.6))
        if f is not None:
            crease = 1.0 + 1.9 * math.exp(-((ti - 0.30) / 0.13) ** 2) * p["lean"] / 30.0
            # ... and the horizontal band a shirt bunches into where a SEATED
            # person's waist compresses.  It is not the same fold system as the
            # drape and it does not read as one.
            bz = 0.0
            if cloth_top:
                camp = 0.0060 * loose * spec["fold_k"] * cfg["folds"] * \
                    math.exp(-((ti - 0.26) / 0.17) ** 2)
                ph = (vnoise3(ring * np.array([4.0, 4.0, 0.6]),
                              seed=spec["fold_seed"] + 8821) - 0.5) * 2.6
                bz = camp * np.sin(ring[:, 2] * 44.0 + ph)
            ring = _ring(P[i], ex, ey, RX[i], RY[i], th, mod=m,
                         off=offs + f * max(0.35, crease) + bz)
        rings.append(ring)
        cols.append(col)
        mats.append(mat)

    # buttocks and thighs are compressed by the pan: flatten anything below it
    for i, r in enumerate(rings):
        low = r[:, 2] < 0.012
        if low.any():
            r[low, 2] = 0.012 - (0.012 - r[low, 2]) * 0.12
            wide = low & (np.abs(r[:, 0]) > 1e-6)
            r[wide, 0] *= 1.020

    # emit as material runs so the hem is a real edge, not a blend
    i0 = 0
    for i in range(1, n + 1):
        if i == n or mats[i] != mats[i0]:
            seg = rings[i0:i]
            cap0 = None
            cap1 = None
            if i0 == 0:
                cap0 = P[0] - frames[0][2] * (RY[0] * 0.55)
                # the buttock pole must stay inside the 50 mm seat pan, not
                # under it: a pole below the pan is flesh through the shell.
                cap0 = np.array([cap0[0], cap0[1], max(float(cap0[2]), -0.024)])
            if i == n:
                cap1 = P[-1] + frames[-1][2] * (RX[-1] * 0.25)
            if len(seg) >= 2:
                acc.tube(seg, mats[i0], cols[i0:i], cap0=cap0, cap1=cap1)
            if i < n:                      # overlap one ring so there is no gap
                i0 = i - 1
                acc.tube([rings[i - 1], rings[i]], mats[i], cols[i - 1:i + 1])
                i0 = i
    return P, frames, RX, RY


def _yoke(acc, spec, J, cfg):
    """THE SHOULDER LINE.  An arc from one acromion, over the trapezius, to the
    other, with the section running fore-aft x vertical.

    This is the part the manifest is talking about when it says the shoulder line
    is 100 % of the read.  Without it the torso ends in a cone, the arms hang off
    it as two detached balls, and 254 px of figure reads as a skittle - which is
    exactly what the first render of this item showed.  With it there is an
    acromion corner, a slope down from the neck, and the arms are attached to
    something.  It is also what covers the base of the neck.
    """
    S = J["_seg"]
    g = GARMENTS[spec["top"]]
    chestR = J["chest_top"].R
    sl, sr = J["shoulder_L"].p, J["shoulder_R"].p
    mid = J["chest_top"].p + chestR[:, 2] * (0.009 * spec["stature"]) \
        - chestR[:, 1] * (0.004 * spec["stature"])
    cl = J["clav_L"].p + chestR[:, 2] * (0.018 * spec["stature"])
    cr = J["clav_R"].p + chestR[:, 2] * (0.018 * spec["stature"])
    P = _resample(np.stack([sl, cl, mid, cr, sr]), 7)
    P = _smooth_polyline(P, 2, 0.45)
    P = _resample(P, max(9, int(np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1))
                                / (cfg["ds"] * 1.15))))
    frames = _transport(P, up0=chestR[:, 1])
    t = np.linspace(0.0, 1.0, len(P))
    ua = S["upperarm_r"]
    # rx runs vertical (see _transport with up0 = forward), ry fore-aft
    # A TRAPEZIUS, NOT A SHOULDER PAD.  Macro pass 3 had rf at 0.86 of chest
    # depth and the yoke stood proud of the torso all the way round: it read as
    # a poncho with a rim, on 260 people.  The section now sits INSIDE the chest
    # everywhere except at the acromion, where it becomes the deltoid and has to
    # match the arm's own first ring (r0 * 1.42) or there is a visible step.
    rv = np.interp(t, [0.0, 0.14, 0.5, 0.86, 1.0],
                   [ua * 1.42, ua * 1.00, S["chest_hd"] * 0.42,
                    ua * 1.00, ua * 1.42])
    rf = np.interp(t, [0.0, 0.14, 0.5, 0.86, 1.0],
                   [ua * 1.36, S["chest_hd"] * 0.66, S["chest_hd"] * 0.62,
                    S["chest_hd"] * 0.66, ua * 1.36])
    nrad = max(10, cfg["nrad_limb"])
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    sleeveless = g["sleeve"] < 0.10
    rings, cols, mats = [], [], []
    for i in range(len(P)):
        ex, ey, ez = frames[i]
        ti = t[i]
        edge = min(ti, 1.0 - ti)
        clothed = not (sleeveless and edge < 0.13)
        offs = np.full(nrad, g["thick"] if clothed else 0.0)
        if clothed:
            # the SHOULDER SEAM: a 3 mm groove over the acromion, where every
            # sleeve is stitched to every body panel that has ever existed
            offs -= 0.0030 * math.exp(-((edge - 0.135) / 0.045) ** 2)
        r = _ring(P[i], ex, ey, rv[i], rf[i], th, off=offs)
        if clothed and cfg["folds"] > 0:
            f = _folds(r, th, cfg["folds"] * 0.011 * g["looseness"] * spec["fold_k"],
                       spec["fold_seed"] + 41, k=(12.0, 12.0, 9.0))
            r = _ring(P[i], ex, ey, rv[i], rf[i], th, off=offs + f)
        rings.append(r)
        cols.append(np.asarray(spec["col_top"] if clothed else spec["col_skin"], float))
        mats.append(_MATKEY[g["mat"]] if clothed else MAT_SKIN)
    i0 = 0
    for i in range(1, len(P) + 1):
        if i == len(P) or mats[i] != mats[i0]:
            seg = rings[i0:i]
            cap0 = P[0] - frames[0][2] * (rv[0] * 0.70) if i0 == 0 else None
            cap1 = P[-1] + frames[-1][2] * (rv[-1] * 0.70) if i == len(P) else None
            if len(seg) >= 2:
                acc.tube(seg, mats[i0], cols[i0:i], cap0=cap0, cap1=cap1)
            if i < len(P):
                acc.tube([rings[i - 1], rings[i]], mats[i], cols[i - 1:i + 1])
                i0 = i


def _limb(acc, spec, J, D, cfg, side, is_arm):
    S, p = J["_seg"], J["_pose"]
    nrad = cfg["nrad_limb"]
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    if is_arm:
        a, b, c = J["shoulder_" + side].p, J["elbow_" + side].p, J["wrist_" + side].p
        r0, r1, r2 = S["upperarm_r"], S["forearm_r"] * 1.05, S["wrist_r"]
        g = GARMENTS[spec["top"]]
        cover = max(0.0, g["sleeve"] - spec["sleeve_push"])
        thick, loose = g["thick"], g["looseness"]
        cloth_mat = _MATKEY[g["mat"]]
        cloth_col = np.asarray(spec["col_top"], float)
        joint_t = 0.5
        bulge = 1.42                      # deltoid
    else:
        a, b, c = J["hip_" + side].p, J["knee_" + side].p, J["ankle_" + side].p
        r0, r1, r2 = S["thigh_r"], S["knee_r"], S["ankle_r"]
        bo = BOTTOMS[spec["bottom"]]
        cover = bo["cuff"]
        thick, loose = bo["thick"], bo["looseness"]
        cloth_mat = _MATKEY[bo["mat"]]
        cloth_col = np.asarray(spec["col_bottom"], float)
        joint_t = 0.5
        bulge = 1.10
    skin_col = np.asarray(spec["col_skin"], float)

    L1 = float(np.linalg.norm(b - a))
    L2 = float(np.linalg.norm(c - b))
    n1 = max(4, int(L1 / cfg["ds"]))
    n2 = max(4, int(L2 / cfg["ds"]))
    P = np.concatenate([a + (b - a) * np.linspace(0, 1, n1, endpoint=False)[:, None],
                        b + (c - b) * np.linspace(0, 1, n2 + 1)[:, None]], axis=0)
    # round the joint: a local smoothing pass around the elbow / knee only
    w = np.exp(-((np.arange(len(P)) - n1) / 2.1) ** 2)
    Q = P.copy()
    Q[1:-1] = P[1:-1] * (1 - 0.55 * w[1:-1, None]) + \
        0.5 * (P[:-2] + P[2:]) * (0.55 * w[1:-1, None])
    P = Q
    frames = _transport(P, up0=(0.0, 1.0, 0.0))
    t = np.linspace(0.0, 1.0, len(P))
    tj = n1 / float(len(P) - 1)

    key = np.array([0.0, 0.06, tj * 0.55, tj, tj + (1 - tj) * 0.30, 1.0])
    val = np.array([r0 * bulge, r0 * (1.02 if is_arm else 1.06), r0 * 0.86,
                    r1, r1 * (1.16 if not is_arm else 0.95), r2])
    R = np.interp(t, key, val)
    if not is_arm:                        # the calf belly
        R = R + S["calf_r"] * 0.30 * np.exp(-((t - (tj + (1 - tj) * 0.26)) / 0.12) ** 2)
    # elliptical: limbs are not round
    ecc = np.interp(t, [0.0, tj, 1.0], [1.14, 1.05, 0.92] if is_arm
                    else [1.10, 1.02, 0.86])

    rings, cols, mats = [], [], []
    for i in range(len(P)):
        ex, ey, ez = frames[i]
        ti = t[i]
        clothed = ti <= cover
        offs = np.zeros(nrad)
        col = cloth_col if clothed else skin_col
        mat = cloth_mat if clothed else MAT_SKIN
        if clothed:
            offs += thick * (1.0 + 0.9 * max(0.0, 1.0 - abs(ti - cover) / 0.18) ** 2)
            # THE CUFF.  A sleeve that just stops is a painted line; a sleeve
            # that doubles back into a 5 mm band is a sleeve.  1 px at 14.7 m,
            # and the highlight it catches is what says "garment".
            if cover < 0.985:
                offs += 0.005 * math.exp(-((ti - cover) / 0.028) ** 2)
            if not is_arm:                      # trouser cuff / turn-up
                offs += 0.004 * math.exp(-((ti - cover) / 0.024) ** 2)
            # fabric bunches inside the bend of the joint
            bend = math.exp(-((ti - tj) / 0.13) ** 2)
            fam = cfg["folds"] * loose * spec["fold_k"] * (0.0080 + 0.0145 * bend)
            f = _folds(_ring(P[i], ex, ey, R[i] * ecc[i], R[i], th),
                       th, fam, spec["fold_seed"] + (7 if is_arm else 13),
                       k=(11.0, 11.0, 7.0))
            if f is not None:
                offs = offs + f
        else:
            offs += 0.0
        ring = _ring(P[i], ex, ey, R[i] * ecc[i], R[i], th, off=offs)
        rings.append(ring)
        cols.append(col)
        mats.append(mat)

    i0 = 0
    for i in range(1, len(P) + 1):
        if i == len(P) or mats[i] != mats[i0]:
            seg = rings[i0:i]
            cap0 = P[0] - frames[0][2] * (R[0] * 0.85) if i0 == 0 else None
            cap1 = P[-1] + frames[-1][2] * (R[-1] * 0.65) if i == len(P) else None
            if len(seg) >= 2:
                acc.tube(seg, mats[i0], cols[i0:i], cap0=cap0, cap1=cap1)
            if i < len(P):
                acc.tube([rings[i - 1], rings[i]], mats[i], cols[i - 1:i + 1])
                i0 = i
    return P, frames, R


def _hand(acc, spec, J, cfg, side):
    """A closed fist mass with a thumb ridge.  A hand is 0.19 m = 39 px long and
    5 px wide; fingers are not resolvable, the SHAPE of the fist is."""
    S = J["_seg"]
    wr = J["wrist_" + side]
    hd = J["hand_" + side]
    ez = hd.R[:, 2]
    ex = hd.R[:, 0]
    ey = hd.R[:, 1]
    L = S["hand_len"] * 0.92
    w = S["wrist_r"] * 2.35
    h = S["wrist_r"] * 1.55
    nrad = max(8, cfg["nrad_limb"] - 4)
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    ts = np.linspace(0.0, 1.0, 7)
    rings = []
    for tt in ts:
        rr = 0.55 + 0.62 * math.sin(math.pi * (0.22 + 0.78 * tt)) ** 0.7
        rr *= 1.0 - 0.30 * max(0.0, tt - 0.72) / 0.28
        P = wr.p + ez * (L * tt)
        rings.append(_ring(P, ex, ey, w * 0.5 * rr, h * 0.5 * rr, th))
    acc.tube(rings, MAT_SKIN, np.asarray(spec["col_skin"], float),
             cap0=wr.p - ez * (w * 0.12),
             cap1=wr.p + ez * (L * 1.06))
    if cfg["hands"]:
        sgn = -1.0 if side == "L" else 1.0
        tb = []
        for k, tt in enumerate(np.linspace(0.10, 0.72, 4)):
            P = wr.p + ez * (L * tt) + ex * (sgn * w * 0.42) + ey * (h * 0.10)
            r = w * (0.20 - 0.05 * k / 3.0)
            tb.append(_ring(P, ex, ey, r, r * 0.9, th))
        acc.tube(tb, MAT_SKIN, np.asarray(spec["col_skin"], float),
                 cap0=tb[0].mean(axis=0) - ez * (L * 0.05),
                 cap1=tb[-1].mean(axis=0) + ez * (L * 0.06))


def _foot(acc, spec, J, cfg, side):
    S = J["_seg"]
    sh = SHOES[spec["shoe"]]
    fj = J["foot_" + side]
    ez = fj.R[:, 2]                      # along the foot, toward the toe
    ex = fj.R[:, 0]
    ey = fj.R[:, 1]
    L = S["foot_len"] * sh["len_k"]
    w = S["ankle_r"] * 2.05
    ank = J["ankle_" + side].p
    heel = ank - ez * (L * 0.26)
    nrad = max(8, cfg["nrad_limb"] - 2)
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    # THE SOLE PLANE.  A rounded elliptical sole floats the figure ~20 mm off the
    # tread, and at 203 px/m that is 4 px of daylight under every shoe in the
    # stand.  A grounded foot gets its sole levelled and flattened onto the plane
    # the IK solved the ankle onto; a dangling or tiptoe foot keeps its own axis,
    # because a foot in the air has no reason to be level.
    grounded = abs(float(ez[2])) < 0.22
    # 6 mm of embedment into the tread.  Not BASE_EMBED_M's 20 mm: that is for
    # things standing on the WORLD ground datum, and a 26 mm shoe sole sunk 20 mm
    # into a concrete step is a foot in the concrete.  6 mm is contact - it
    # closes the hairline gap that otherwise renders as a bright 1 px line under
    # every shoe in the stand when the sun rakes along the rake.
    sole_z = float(ank[2] - S["foot_h"] * 0.55) - (FOOT_EMBED_M if grounded else 0.0)
    ts = np.linspace(0.0, 1.0, 9)
    rings, cols = [], []
    col_shoe = np.asarray(spec["col_shoe"], float)
    for tt in ts:
        P = heel + ez * (L * tt)
        hh = sh["h"] * (0.98 - 0.62 * max(0.0, tt - 0.30) / 0.70)
        ww = w * (0.86 + 0.30 * math.sin(math.pi * min(1.0, 0.25 + tt)))
        ww *= 1.0 - 0.35 * max(0.0, tt - sh["toe"]) / max(1e-3, 1.0 - sh["toe"])
        c = P + ey * (hh * 0.5)
        if grounded:
            c = c + np.array([0.0, 0.0, (sole_z + hh * 0.5) - c[2]])
        r = _ring(c, ex, ey, ww * 0.5, hh * 0.5, th)
        if grounded:
            r[:, 2] = np.maximum(r[:, 2], sole_z)
        rings.append(r)
        cols.append(col_shoe)
    acc.tube(rings, MAT_SHOE, cols,
             cap0=rings[0].mean(axis=0) - ez * (L * 0.055),
             cap1=rings[-1].mean(axis=0) + ez * (L * 0.045))


def _head(acc, spec, J, cfg):
    S = J["_seg"]
    hc = J["head_centre"]
    ex, ey, ez = hc.R[:, 0], hc.R[:, 1], hc.R[:, 2]
    hw, hd, hh = S["head_w"] * 0.5, S["head_d"] * 0.5, S["head_h"] * 0.5
    nrad = cfg["nrad_head"]
    nu = max(9, int(math.pi * hh / (cfg["ds"] * 0.95)))
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    u = np.linspace(-0.985, 0.985, nu)
    skin = np.asarray(spec["col_skin"], float)
    front = np.cos(th - 0.5 * math.pi)
    rings = []
    for uu in u:
        rr = math.sqrt(max(0.0, 1.0 - uu * uu))
        rx = hw * rr
        ry = hd * rr
        P = hc.p + ez * (hh * uu)
        m = np.ones(nrad)
        # jaw: narrower and shorter than the cranium
        jaw = max(0.0, -uu - 0.10) / 0.90
        m -= 0.30 * jaw * (0.55 + 0.45 * np.clip(-front, 0, 1))
        # chin: a forward point at the bottom front
        off = np.zeros(nrad)
        off += hd * 0.30 * jaw ** 1.5 * np.clip(front, 0, 1) ** 3
        # occiput
        off += hd * 0.085 * math.exp(-((uu - 0.10) / 0.45) ** 2) * np.clip(-front, 0, 1) ** 2
        # brow
        off += hd * 0.055 * math.exp(-((uu - 0.18) / 0.13) ** 2) * np.clip(front, 0, 1) ** 4
        if cfg["nose"]:
            off += hd * 0.30 * math.exp(-((uu - 0.005) / 0.115) ** 2) * \
                np.exp(-((np.cos(th - 0.5 * math.pi) - 1.0) * 7.0) ** 2)
        if cfg["ears"]:
            # AN EAR IS 12 mm AND THE RING SAMPLES EVERY 12.9 deg.  The first
            # version used a 13.7 deg Gaussian, so the whole ear landed between
            # two vertices and every head in the stand grew a pair of pointed
            # horns.  A feature narrower than two samples is not a feature, it is
            # an artefact: the lobe is wider than the sample spacing now, and
            # smaller, because at 2.5 px an ear is a shading event, not a shape.
            for a0 in (0.0, math.pi):
                off += hw * 0.115 * math.exp(-((uu - 0.020) / 0.130) ** 2) * \
                    np.exp(-(((np.angle(np.exp(1j * (th - a0)))) / 0.46) ** 2))
        rings.append(_ring(P, ex, ey, rx, ry, th, mod=m, off=off))
    acc.tube(rings, MAT_SKIN, skin,
             cap0=hc.p - ez * (hh * 1.02) + ey * (hd * 0.16),
             cap1=hc.p + ez * (hh * 1.005))

    # neck.  It starts INSIDE the chest and inside the yoke: what is visible is
    # the 25-40 mm between the collar and the jaw, which is all a neck should be
    # at 47 px of head.
    nb = J["neck"]
    ntop = J["head"].p
    nrad2 = max(8, nrad - 10)
    th2 = np.linspace(0.0, 2.0 * math.pi, nrad2, endpoint=False)
    nr = []
    g = GARMENTS[spec["top"]]
    for k, tt in enumerate(np.linspace(-0.85, 1.05, 6)):
        P = nb.p + (ntop - nb.p) * tt
        # a real neck is wider at the base (sternocleidomastoid) and deeper than
        # it is wide, and it never gets thinner than 0.9 of the throat
        r = S["neck_r"] * (1.42 - 0.42 * min(1.0, max(0.0, tt)))
        nr.append(_ring(P, nb.R[:, 0], nb.R[:, 1], r * 1.02, r * 1.10, th2))
    acc.tube(nr, MAT_SKIN, skin)
    # collar: sits on the yoke around the neck base, not as a ring on the throat
    if g["collar"] > 0.004:
        cr = []
        for k, tt in enumerate((-0.55, -0.30, -0.05)):
            P = nb.p + (ntop - nb.p) * tt
            r = S["neck_r"] * (1.62 + 0.16 * k) + g["collar"] * (0.6 + 0.4 * k)
            rr = _ring(P, nb.R[:, 0], nb.R[:, 1], r * 1.14, r * 1.04, th2)
            if cfg["folds"] > 0:
                f = _folds(rr, th2, cfg["folds"] * 0.006 * g["looseness"],
                           spec["fold_seed"] + 617, k=(20.0, 20.0, 20.0))
                rr = _ring(P, nb.R[:, 0], nb.R[:, 1], r * 1.14, r * 1.04, th2, off=f)
            cr.append(rr)
        acc.tube(cr, _MATKEY[g["mat"]], np.asarray(spec["col_top"], float))


def _hair(acc, spec, J, cfg):
    st = HAIR_STYLES[spec["hair"]]
    S = J["_seg"]
    hc = J["head_centre"]
    ex, ey, ez = hc.R[:, 0], hc.R[:, 1], hc.R[:, 2]
    hw, hd, hh = S["head_w"] * 0.5, S["head_d"] * 0.5, S["head_h"] * 0.5
    nrad = cfg["nrad_head"]
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    col = np.asarray(spec["col_hair"], float)
    # the hairline u0(theta): front / side / back interpolated round the skull
    f = np.clip(np.cos(th - 0.5 * math.pi), -1, 1)
    fp = np.clip(f, 0.0, 1.0)
    fn = np.clip(-f, 0.0, 1.0)
    u0 = np.where(f > 0, st["side"] + (st["front"] - st["side"]) * fp ** 1.4,
                  st["side"] + (st["back"] - st["side"]) * fn ** 1.2)
    # break the hairline: a mathematically perfect curve round the skull is the
    # tell that gave the first pass its "beret" look
    u0 = u0 + (vnoise3(np.stack([np.cos(th) * 3.0, np.sin(th) * 3.0,
                                 np.full(nrad, spec["fold_seed"] % 97 * 0.37)], axis=1),
                       seed=spec["fold_seed"] + 4409) - 0.5) * 0.16
    nrings = cfg["hair_rings"]
    rings = []
    for i in range(nrings):
        s = i / float(nrings - 1)
        uu = u0 + (0.985 - u0) * (s ** 0.85)
        rr = np.sqrt(np.clip(1.0 - uu * uu, 0.0, 1.0))
        thick = st["thick"] * (0.25 + 0.75 * math.sin(math.pi * min(1.0, 0.15 + s)))
        pts = hc.p[None, :] + ez[None, :] * (hh * uu)[:, None]
        X = np.cos(th) * (hw * rr) + np.cos(th) * thick
        Y = np.sin(th) * (hd * rr) + np.sin(th) * thick
        R = pts + X[:, None] * ex[None, :] + Y[:, None] * ey[None, :]
        # the occiput mass and a bit of body in the hair
        R += ez[None, :] * (thick * 0.55 * uu)[:, None]
        if cfg["folds"] > 0:
            n = (fbm3(R * np.array([46.0, 46.0, 30.0]),
                      seed=spec["fold_seed"] + 991, oct=3) - 0.5)
            R += (n * st["thick"] * 0.85 * st["fuzz"])[:, None] * \
                _n_rows(R - hc.p[None, :])
        rings.append(R)
    # THE CROWN POLE, and it has been wrong twice.  First it sat a full hair
    # thickness above the last ring: a 20 mm spike over a 13 mm radius, 4 px of
    # horn on 260 skulls.  Then it sat BELOW the last ring - the hair shell is
    # offset outward AND upward, so an apex measured from the head centre landed
    # 2 mm under the rim, the fan folded inward and the bare skull came through
    # the middle of the hair.  That is the pale crown in macro pass 2.
    # Measure the apex off the RING, which is the only thing that knows where the
    # hair actually is.
    acc.tube(rings, MAT_HAIR, col,
             cap1=rings[-1].mean(axis=0) + ez * (st["thick"] * 0.85 + hw * 0.055))
    # the rim: skirt the lowest ring back to the scalp so the shell is closed
    inner = []
    uu = u0
    rr = np.sqrt(np.clip(1.0 - uu * uu, 0.0, 1.0))
    X = np.cos(th) * (hw * rr) * 0.995
    Y = np.sin(th) * (hd * rr) * 0.995
    inner = hc.p[None, :] + ez[None, :] * (hh * uu)[:, None] + \
        X[:, None] * ex[None, :] + Y[:, None] * ey[None, :]
    acc.tube([inner, rings[0]], MAT_HAIR, col)

    if st["tail"] > 0.5:
        base = hc.p - ey * (hd * 0.92) + ez * (hh * 0.12)
        tip = base - ey * (hd * 0.55) - ez * (hh * 1.25)
        tr = []
        for k, tt in enumerate(np.linspace(0, 1, 6)):
            P = base + (tip - base) * tt + ez * (-0.02 * math.sin(math.pi * tt))
            r = hw * (0.34 - 0.20 * tt)
            tr.append(_ring(P, ex, ez, r, r * 0.85,
                            np.linspace(0, 2 * math.pi, max(8, nrad - 12), endpoint=False)))
        acc.tube(tr, MAT_HAIR, col, cap0=base + ey * 0.005, cap1=tip)
    if st["bun"] > 0.5:
        c = hc.p - ey * (hd * 0.88) + ez * (hh * 0.62)
        br = []
        for uu2 in np.linspace(-0.95, 0.95, 6):
            r = math.sqrt(max(0.0, 1 - uu2 * uu2)) * hw * 0.46
            br.append(_ring(c - ey * (hw * 0.30 * uu2), ex, ez, r, r,
                            np.linspace(0, 2 * math.pi, max(8, nrad - 12), endpoint=False)))
        acc.tube(br, MAT_HAIR, col, cap0=c - ey * (hw * 0.42), cap1=c + ey * (hw * 0.42))


def _n_rows(A):
    L = np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-12)
    return A / L


def _hood(acc, spec, J, cfg):
    """A hood: down behind the neck, or up over the head.  A big silhouette
    change for 300 triangles, and 22 % of hoodie wearers have it up."""
    g = GARMENTS[spec["top"]]
    if g["hood"] <= 0.0:
        return
    S = J["_seg"]
    hc = J["head_centre"]
    ex, ey, ez = hc.R[:, 0], hc.R[:, 1], hc.R[:, 2]
    hw, hd, hh = S["head_w"] * 0.5, S["head_d"] * 0.5, S["head_h"] * 0.5
    col = np.asarray(spec["col_top"], float)
    mat = _MATKEY[g["mat"]]
    nrad = max(10, cfg["nrad_head"] - 8)
    th = np.linspace(0.0, 2.0 * math.pi, nrad, endpoint=False)
    if spec["hood_up"]:
        rings = []
        for i, uu in enumerate(np.linspace(-0.55, 0.98, 7)):
            rr = math.sqrt(max(0.0, 1.0 - uu * uu)) ** 0.82
            k = 1.30 + 0.10 * (1 - uu)
            P = hc.p + ez * (hh * uu * 1.06) - ey * (hd * 0.10)
            m = np.ones(nrad) - 0.34 * np.clip(np.cos(th - 0.5 * math.pi), 0, 1) ** 2 * \
                max(0.0, (uu + 0.2))
            r = _ring(P, ex, ey, hw * rr * k + g["thick"] * 1.5,
                      hd * rr * k + g["thick"] * 1.5, th, mod=m)
            f = _folds(r, th, cfg["folds"] * 0.010 * g["looseness"],
                       spec["fold_seed"] + 313, k=(16.0, 16.0, 12.0))
            if f is not None:
                r = _ring(P, ex, ey, hw * rr * k + g["thick"] * 1.5,
                          hd * rr * k + g["thick"] * 1.5, th, mod=m, off=f)
            rings.append(r)
        acc.tube(rings, mat, col, cap1=hc.p + ez * (hh * 1.12))
    else:
        base = J["neck"].p - J["neck"].R[:, 1] * (S["neck_r"] * 1.15)
        rings = []
        for i, tt in enumerate(np.linspace(0.0, 1.0, 6)):
            P = base - J["neck"].R[:, 1] * (S["neck_r"] * 1.5 * tt) \
                     - J["neck"].R[:, 2] * (S["neck_r"] * 3.4 * tt)
            r = S["neck_r"] * (1.5 + 1.6 * math.sin(math.pi * min(1.0, 0.15 + tt)))
            rr = _ring(P, J["neck"].R[:, 0], J["neck"].R[:, 1], r * 1.25, r * 0.62, th)
            f = _folds(rr, th, cfg["folds"] * 0.011 * g["looseness"],
                       spec["fold_seed"] + 77, k=(15.0, 15.0, 15.0))
            if f is not None:
                rr = _ring(P, J["neck"].R[:, 0], J["neck"].R[:, 1],
                           r * 1.25, r * 0.62, th, off=f)
            rings.append(rr)
        acc.tube(rings, mat, col, cap0=base + J["neck"].R[:, 2] * 0.01,
                 cap1=rings[-1].mean(axis=0))


# =========================================================================== #
# 10.  ANCHORS — the attachment interface for the eight dependent items         #
# =========================================================================== #
def anchors(spec, J=None):
    """-> dict[str, 4x4 nested list] in the figure local frame."""
    J = solve_skeleton(spec) if J is None else J
    S = J["_seg"]
    out = {}

    def put(name, p, ez, ey_hint):
        R = _frame_from_z(ez, up_hint=ey_hint)
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = np.asarray(p, float)
        out[name] = M.tolist()

    hc = J["head_centre"]
    hh = S["head_h"] * 0.5
    put("head_top", hc.p + hc.R[:, 2] * hh, hc.R[:, 2], hc.R[:, 1])
    put("head_centre", hc.p, hc.R[:, 2], hc.R[:, 1])
    put("head_front", hc.p + hc.R[:, 1] * (S["head_d"] * 0.5) + hc.R[:, 2] * (hh * 0.18),
        hc.R[:, 1], hc.R[:, 2])
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        put("ear_" + side, hc.p + hc.R[:, 0] * (sgn * S["head_w"] * 0.5)
            + hc.R[:, 2] * (hh * 0.045), sgn * hc.R[:, 0], hc.R[:, 2])
        w = J["wrist_" + side]
        h = J["hand_" + side]
        # GRIP AXIS: perpendicular to the forearm, through the fist
        grip = _n(np.cross(h.R[:, 2], h.R[:, 0]))
        put("hand_" + side, h.p, grip, h.R[:, 2])
        put("wrist_" + side, w.p, w.R[:, 2], w.R[:, 1])
        put("knee_" + side, J["knee_" + side].p + J["knee_" + side].R[:, 1] * S["knee_r"],
            J["knee_" + side].R[:, 1], (0, 0, 1))
        put("foot_" + side, J["ankle_" + side].p - np.array([0, 0, S["foot_h"] * 0.5]),
            (0, 0, 1), J["foot_" + side].R[:, 2])
        put("shoulder_" + side, J["shoulder_" + side].p
            + J["shoulder_" + side].R[:, 2] * (S["upperarm_r"] * 1.2),
            _n(J["shoulder_" + side].R[:, 2] + sgn * J["shoulder_" + side].R[:, 0] * 0.6),
            J["shoulder_" + side].R[:, 1])
        put("seat_" + side, np.array([sgn * (RAKE["pan_half_width_m"] + 0.02), -0.03, 0.0]),
            (0, 0, 1), (0, 1, 0))
    lap = (J["knee_L"].p + J["knee_R"].p + J["hip_L"].p + J["hip_R"].p) * 0.25
    put("lap", lap + np.array([0, 0, S["thigh_r"]]), (0, 0, 1), (0, 1, 0))
    put("under_seat", np.array([0.0, 0.0, TREAD_Z]), (0, 0, 1), (0, 1, 0))
    ch = J["spine_t8"]
    put("chest", ch.p + ch.R[:, 1] * (S["chest_hd"] + 0.02), ch.R[:, 1], ch.R[:, 2])
    put("back", ch.p - ch.R[:, 1] * (S["chest_hd"] + 0.02), -ch.R[:, 1], ch.R[:, 2])
    put("pelvis", J["pelvis"].p, J["pelvis"].R[:, 2], J["pelvis"].R[:, 1])
    return out


# =========================================================================== #
# 11.  MESH EMISSION                                                           #
# =========================================================================== #
def figure_arrays(spec, detail="hero"):
    """Pure-numpy build. -> (verts (n,3), cols (n,3), faces list, matidx list)."""
    cfg = DETAIL[detail]
    J = solve_skeleton(spec)
    acc = _Acc()
    _torso(acc, spec, J, detail, cfg)
    _yoke(acc, spec, J, cfg)
    for side in ("L", "R"):
        _limb(acc, spec, J, detail, cfg, side, is_arm=False)
    for side in ("L", "R"):
        _limb(acc, spec, J, detail, cfg, side, is_arm=True)
        _hand(acc, spec, J, cfg, side)
        _foot(acc, spec, J, cfg, side)
    _head(acc, spec, J, cfg)
    _hood(acc, spec, J, cfg)
    if not (spec["hood_up"] and GARMENTS[spec["top"]]["hood"] > 0.5):
        _hair(acc, spec, J, cfg)
    V = np.concatenate(acc.V, axis=0)
    C = np.concatenate(acc.C, axis=0)
    return V, C, acc.F, acc.M, J


def figure_mesh(spec, detail="hero", name=None):
    """-> bpy Mesh, recentred on the seat pan centre (the figure local frame)."""
    V, C, F, M, J = figure_arrays(spec, detail)
    me = bpy.data.meshes.new(name or ("%sFig%05d" % (OBJ_PREFIX, spec["index"])))
    me.from_pydata(V.tolist(), [], F)
    me.validate(verbose=False)
    if len(me.polygons) == len(M):
        me.polygons.foreach_set("material_index", M)
        me.polygons.foreach_set("use_smooth", [True] * len(M))
    ca = me.color_attributes.new(name="Dye", type='FLOAT_COLOR', domain='POINT')
    flat = np.concatenate([C, np.ones((len(C), 1))], axis=1).ravel()
    ca.data.foreach_set("color", flat)
    me.update()
    for nm in MAT_NAMES:
        me.materials.append(_material(nm))
    return me


def seat_anchor_matrix(x, y_pan_centre, z_pan_top, facing_deg=0.0, base=None):
    """Placement matrix for one figure ON A GRANDSTAND SEAT.

    (x, y_pan_centre, z_pan_top) is the centre of the seat pan's top surface in
    whatever frame `base` maps to the world - pass the circuit->world matrix and
    give the seat in circuit coordinates, which is how build_architecture authors
    the rake.  z_pan_top comes FROM THE SEAT, so there is no assumed z anywhere.
    """
    M = Matrix.Translation((x, y_pan_centre, z_pan_top)) @ \
        Matrix.Rotation(math.radians(facing_deg), 4, 'Z')
    return (base @ M) if base is not None else M


def seat_anchor_on_ground(x_world, y_world, pan_height_m=0.44, facing_deg=0.0):
    """Placement matrix for a figure seated on something standing on the WORLD
    GROUND - a folding stool on the GA bank, a kerb, a step, a coolbox.

    -> (Matrix, ground_z, owner).  The ground comes from
    `world_contract.world_ground_z`, never from an assumed z, and the support is
    embedded by BASE_EMBED_M as law 5 requires.  `pan_height_m` is the height of
    the thing being sat on: 0.44 a stool, 0.32 a coolbox, 0.15 a kerb, 0.00 the
    ground itself.

    For `spectator_folding_stool`, `ga_picnic_group` and anything else off the
    rake: use this, not seat_anchor_matrix.
    """
    if not HAVE_WC:                                    # pragma: no cover
        raise RuntimeError("world_contract is required to sit a figure on the "
                           "ground: there is no fallback datum and inventing "
                           "one is the defect the contract exists to prevent.")
    z, owner = WC.world_ground_z(float(x_world), float(y_world))
    if not np.isfinite(z):
        raise ValueError("world_ground_z is NaN at (%.3f, %.3f): terrain owns "
                         "this point and has not been asked. Do not guess."
                         % (x_world, y_world))
    z = float(z) - WC.BASE_EMBED_M + float(pan_height_m)
    return (Matrix.Translation((x_world, y_world, z)) @
            Matrix.Rotation(math.radians(facing_deg), 4, 'Z')), float(z), owner


# =========================================================================== #
# 12.  MATERIALS — six, all procedural, all TexCoord->Object                    #
# =========================================================================== #
_MAT_CACHE = {}


def _nd(nt, typ, loc=(0, 0), **kw):
    n = nt.nodes.new(typ)
    n.location = loc
    for k, v in kw.items():
        if hasattr(n, k):
            setattr(n, k, v)
    return n


def _set(node, key, val):
    try:
        node.inputs[key].default_value = val
    except Exception:
        pass


def _link(nt, a, b, key):
    try:
        nt.links.new(a, b.inputs[key])
    except Exception:
        pass


def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = _nd(nt, 'ShaderNodeOutputMaterial', (1200, 0))
    b = _nd(nt, 'ShaderNodeBsdfPrincipled', (900, 0))
    nt.links.new(b.outputs[0], out.inputs[0])
    tc = _nd(nt, 'ShaderNodeTexCoord', (-1600, 0))
    dye = _nd(nt, 'ShaderNodeVertexColor', (-1600, 300))
    dye.layer_name = "Dye"
    return m, nt, b, tc.outputs['Object'], dye.outputs['Color']


def _noise(nt, loc, scale, det=6.0, rough=0.55, dist=0.0, vec=None):
    n = _nd(nt, 'ShaderNodeTexNoise', loc)
    _set(n, 'Scale', scale)
    _set(n, 'Detail', det)
    _set(n, 'Roughness', rough)
    _set(n, 'Distortion', dist)
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n


def _wave(nt, loc, scale, dist=0.0, det=2.0, vec=None, bands='X'):
    n = _nd(nt, 'ShaderNodeTexWave', loc)
    n.wave_type = 'BANDS'
    n.bands_direction = bands
    n.wave_profile = 'SIN'
    _set(n, 'Scale', scale)
    _set(n, 'Distortion', dist)
    _set(n, 'Detail', det)
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n


def _vor(nt, loc, scale, vec=None, feature='F1', rand=1.0):
    n = _nd(nt, 'ShaderNodeTexVoronoi', loc)
    n.feature = feature
    _set(n, 'Scale', scale)
    _set(n, 'Randomness', rand)
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n


def _ramp(nt, loc, stops):
    n = _nd(nt, 'ShaderNodeValToRGB', loc)
    el = n.color_ramp.elements
    while len(el) > len(stops):
        el.remove(el[-1])
    for i, (p, c) in enumerate(stops):
        if i >= len(el):
            el.new(p)
        el[i].position = p
        el[i].color = c
    return n


def _math(nt, loc, op, a, b=None, clamp=False):
    n = _nd(nt, 'ShaderNodeMath', loc)
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, n.inputs[i])
    return n


def _mixc(nt, loc, a, b, fac, blend='MIX'):
    n = _nd(nt, 'ShaderNodeMix', loc)
    n.data_type = 'RGBA'
    n.blend_type = blend
    if isinstance(fac, float):
        n.inputs['Factor'].default_value = fac
    else:
        nt.links.new(fac, n.inputs['Factor'])
    for sock, val in ((6, a), (7, b)):
        if isinstance(val, (tuple, list)):
            n.inputs[sock].default_value = tuple(val)
        else:
            nt.links.new(val, n.inputs[sock])
    return n


def _material(kind):
    """Six layered procedural materials.  Every one reads TexCoord->Object; not
    one of them touches Geometry->Position (law 6: at |P| ~ 400 m a
    position-driven procedural loses precision and blotches)."""
    key = OBJ_PREFIX + kind
    if key in _MAT_CACHE and key in {m.name for m in bpy.data.materials}:
        return _MAT_CACHE[key]
    ex = bpy.data.materials.get(key)
    if ex is not None:
        _MAT_CACHE[key] = ex
        return ex
    m, nt, b, obj, dye = _base(key)

    if kind == "Skin":
        # tone variation, subsurface, oily forehead vs matte cheek, fine bump
        mot = _noise(nt, (-1250, -120), 9.0, 8.0, 0.62, vec=obj)
        mr = _ramp(nt, (-1000, -120), [(0.34, (0.86, 0.80, 0.78, 1)),
                                       (0.72, (1.06, 1.02, 1.00, 1))])
        _link(nt, mot.outputs['Fac'], mr, 'Fac')
        c1 = _mixc(nt, (-720, 120), dye, mr.outputs['Color'], 0.55, 'MULTIPLY')
        red = _noise(nt, (-1250, -420), 3.1, 5.0, 0.5, dist=1.2, vec=obj)
        rr = _ramp(nt, (-1000, -420), [(0.45, (1, 1, 1, 1)), (0.85, (1.10, 0.86, 0.82, 1))])
        _link(nt, red.outputs['Fac'], rr, 'Fac')
        c2 = _mixc(nt, (-480, 120), c1.outputs[2], rr.outputs['Color'], 0.34, 'MULTIPLY')
        nt.links.new(c2.outputs[2], b.inputs['Base Color'])
        _set(b, 'Subsurface Weight', 0.14)
        _set(b, 'Subsurface Radius', (0.36, 0.11, 0.06))
        _set(b, 'Subsurface Scale', 0.012)
        rn = _noise(nt, (-1250, -700), 21.0, 6.0, 0.5, vec=obj)
        rq = _math(nt, (-1000, -700), 'MULTIPLY_ADD', rn.outputs['Fac'], 0.16)
        rq.inputs[2].default_value = 0.46
        nt.links.new(rq.outputs[0], b.inputs['Roughness'])
        pore = _vor(nt, (-1250, -980), 900.0, vec=obj)
        bn = _nd(nt, 'ShaderNodeBump', (-720, -980))
        _set(bn, 'Strength', 0.10)
        _set(bn, 'Distance', 0.0016)
        nt.links.new(pore.outputs['Distance'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])

    elif kind in ("Cloth", "Knit", "Shell"):
        weave_s = {"Cloth": 620.0, "Knit": 260.0, "Shell": 900.0}[kind]
        rough0 = {"Cloth": 0.80, "Knit": 0.90, "Shell": 0.52}[kind]
        sheen = {"Cloth": 0.28, "Knit": 0.55, "Shell": 0.10}[kind]
        # dye unevenness: real fabric is not one colour, it fades where it folds
        fade = _noise(nt, (-1250, -100), 6.5, 8.0, 0.60, dist=0.8, vec=obj)
        fr = _ramp(nt, (-1000, -100), [(0.30, (0.80, 0.79, 0.78, 1)),
                                       (0.78, (1.12, 1.11, 1.10, 1))])
        _link(nt, fade.outputs['Fac'], fr, 'Fac')
        c1 = _mixc(nt, (-740, 120), dye, fr.outputs['Color'], 0.42, 'MULTIPLY')
        # a wash of grime along the lower folds
        gr = _noise(nt, (-1250, -380), 2.4, 9.0, 0.72, dist=1.8, vec=obj)
        grr = _ramp(nt, (-1000, -380), [(0.52, (0, 0, 0, 1)), (0.82, (1, 1, 1, 1))])
        _link(nt, gr.outputs['Fac'], grr, 'Fac')
        gm = _math(nt, (-820, -380), 'MULTIPLY', grr.outputs['Color'], 0.16)
        c2 = _mixc(nt, (-500, 120), c1.outputs[2], (0.10, 0.095, 0.088, 1),
                   gm.outputs[0])
        nt.links.new(c2.outputs[2], b.inputs['Base Color'])
        # the weave: two crossed bands + a lint voronoi, into a bump
        w1 = _wave(nt, (-1250, -700), weave_s, 0.6, 2.0, vec=obj, bands='X')
        w2 = _wave(nt, (-1250, -900), weave_s * 1.02, 0.6, 2.0, vec=obj, bands='Y')
        wm = _math(nt, (-1000, -800), 'MULTIPLY', w1.outputs['Fac'], w2.outputs['Fac'])
        lint = _vor(nt, (-1250, -1120), weave_s * 0.42, vec=obj, feature='F1')
        lm = _math(nt, (-1000, -1120), 'MULTIPLY_ADD', lint.outputs['Distance'], 0.55)
        lm.inputs[2].default_value = 0.0
        wl = _math(nt, (-820, -900), 'ADD', wm.outputs[0], lm.outputs[0])
        bn = _nd(nt, 'ShaderNodeBump', (-560, -900))
        _set(bn, 'Strength', 0.55 if kind != "Shell" else 0.30)
        _set(bn, 'Distance', 0.0035 if kind != "Shell" else 0.0022)
        nt.links.new(wl.outputs[0], bn.inputs['Height'])
        # a second, coarse bump for the creases the mesh does not carry
        cn = _noise(nt, (-1250, -1400), 55.0, 7.0, 0.66, vec=obj)
        bn2 = _nd(nt, 'ShaderNodeBump', (-330, -900))
        _set(bn2, 'Strength', 0.22)
        _set(bn2, 'Distance', 0.010)
        nt.links.new(cn.outputs['Fac'], bn2.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], bn2.inputs['Normal'])
        nt.links.new(bn2.outputs['Normal'], b.inputs['Normal'])
        rn = _noise(nt, (-1250, -1650), 14.0, 6.0, 0.55, vec=obj)
        rq = _math(nt, (-1000, -1650), 'MULTIPLY_ADD', rn.outputs['Fac'], 0.16)
        rq.inputs[2].default_value = rough0 - 0.08
        nt.links.new(rq.outputs[0], b.inputs['Roughness'])
        _set(b, 'Sheen Weight', sheen)
        _set(b, 'Sheen Roughness', 0.32)
        if kind == "Shell":
            _set(b, 'Coat Weight', 0.10)
            _set(b, 'Coat Roughness', 0.30)

    elif kind == "Denim":
        fade = _noise(nt, (-1250, -100), 5.0, 9.0, 0.62, dist=1.1, vec=obj)
        fr = _ramp(nt, (-1000, -100), [(0.28, (0.74, 0.76, 0.80, 1)),
                                       (0.80, (1.22, 1.20, 1.16, 1))])
        _link(nt, fade.outputs['Fac'], fr, 'Fac')
        c1 = _mixc(nt, (-740, 120), dye, fr.outputs['Color'], 0.62, 'MULTIPLY')
        # twill: a steep diagonal band, which is what makes denim denim
        tw = _wave(nt, (-1250, -520), 420.0, 0.35, 3.0, vec=obj, bands='DIAGONAL')
        tr = _ramp(nt, (-1000, -520), [(0.35, (0.88, 0.88, 0.90, 1)),
                                       (0.62, (1.08, 1.07, 1.05, 1))])
        _link(nt, tw.outputs['Fac'], tr, 'Fac')
        c2 = _mixc(nt, (-500, 120), c1.outputs[2], tr.outputs['Color'], 0.5, 'MULTIPLY')
        nt.links.new(c2.outputs[2], b.inputs['Base Color'])
        slub = _vor(nt, (-1250, -820), 700.0, vec=obj, feature='F1')
        bn = _nd(nt, 'ShaderNodeBump', (-720, -760))
        _set(bn, 'Strength', 0.45)
        _set(bn, 'Distance', 0.003)
        mixh = _math(nt, (-980, -760), 'ADD', tw.outputs['Fac'], slub.outputs['Distance'])
        nt.links.new(mixh.outputs[0], bn.inputs['Height'])
        cn = _noise(nt, (-1250, -1100), 42.0, 7.0, 0.7, vec=obj)
        bn2 = _nd(nt, 'ShaderNodeBump', (-470, -760))
        _set(bn2, 'Strength', 0.26)
        _set(bn2, 'Distance', 0.009)
        nt.links.new(cn.outputs['Fac'], bn2.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], bn2.inputs['Normal'])
        nt.links.new(bn2.outputs['Normal'], b.inputs['Normal'])
        rn = _noise(nt, (-1250, -1380), 11.0, 6.0, 0.5, vec=obj)
        rq = _math(nt, (-1000, -1380), 'MULTIPLY_ADD', rn.outputs['Fac'], 0.14)
        rq.inputs[2].default_value = 0.76
        nt.links.new(rq.outputs[0], b.inputs['Roughness'])
        _set(b, 'Sheen Weight', 0.22)

    elif kind == "Hair":
        # strand direction from a stretched voronoi; tips lighter than roots
        st = _vor(nt, (-1250, -200), 130.0, vec=obj, feature='F1', rand=0.85)
        sr = _ramp(nt, (-1000, -200), [(0.10, (0.55, 0.52, 0.50, 1)),
                                       (0.62, (1.35, 1.30, 1.24, 1))])
        _link(nt, st.outputs['Distance'], sr, 'Fac')
        c1 = _mixc(nt, (-740, 120), dye, sr.outputs['Color'], 0.60, 'MULTIPLY')
        gy = _noise(nt, (-1250, -520), 24.0, 7.0, 0.6, vec=obj)
        gr = _ramp(nt, (-1000, -520), [(0.62, (0, 0, 0, 1)), (0.92, (1, 1, 1, 1))])
        _link(nt, gy.outputs['Fac'], gr, 'Fac')
        gm = _math(nt, (-820, -520), 'MULTIPLY', gr.outputs['Color'], 0.28)
        c2 = _mixc(nt, (-500, 120), c1.outputs[2], (0.36, 0.34, 0.32, 1), gm.outputs[0])
        nt.links.new(c2.outputs[2], b.inputs['Base Color'])
        bnn = _vor(nt, (-1250, -820), 320.0, vec=obj, feature='F1')
        bn = _nd(nt, 'ShaderNodeBump', (-720, -820))
        _set(bn, 'Strength', 0.62)
        _set(bn, 'Distance', 0.0035)
        nt.links.new(bnn.outputs['Distance'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
        rn = _noise(nt, (-1250, -1100), 40.0, 6.0, 0.6, vec=obj)
        rq = _math(nt, (-1000, -1100), 'MULTIPLY_ADD', rn.outputs['Fac'], 0.20)
        rq.inputs[2].default_value = 0.30
        nt.links.new(rq.outputs[0], b.inputs['Roughness'])
        _set(b, 'Specular IOR Level', 0.42)

    else:                                              # Shoe
        pn = _noise(nt, (-1250, -120), 40.0, 8.0, 0.65, vec=obj)
        pr = _ramp(nt, (-1000, -120), [(0.32, (0.78, 0.78, 0.78, 1)),
                                       (0.75, (1.10, 1.10, 1.10, 1))])
        _link(nt, pn.outputs['Fac'], pr, 'Fac')
        c1 = _mixc(nt, (-740, 120), dye, pr.outputs['Color'], 0.50, 'MULTIPLY')
        scuff = _noise(nt, (-1250, -420), 12.0, 9.0, 0.75, dist=2.0, vec=obj)
        sr = _ramp(nt, (-1000, -420), [(0.58, (0, 0, 0, 1)), (0.80, (1, 1, 1, 1))])
        _link(nt, scuff.outputs['Fac'], sr, 'Fac')
        sm = _math(nt, (-820, -420), 'MULTIPLY', sr.outputs['Color'], 0.42)
        c2 = _mixc(nt, (-500, 120), c1.outputs[2], (0.075, 0.068, 0.060, 1),
                   sm.outputs[0])
        nt.links.new(c2.outputs[2], b.inputs['Base Color'])
        gr = _vor(nt, (-1250, -760), 260.0, vec=obj, feature='F1')
        bn = _nd(nt, 'ShaderNodeBump', (-720, -760))
        _set(bn, 'Strength', 0.40)
        _set(bn, 'Distance', 0.0035)
        nt.links.new(gr.outputs['Distance'], bn.inputs['Height'])
        st = _wave(nt, (-1250, -1040), 320.0, 0.2, 2.0, vec=obj, bands='Z')
        bn2 = _nd(nt, 'ShaderNodeBump', (-470, -760))
        _set(bn2, 'Strength', 0.18)
        _set(bn2, 'Distance', 0.004)
        nt.links.new(st.outputs['Fac'], bn2.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], bn2.inputs['Normal'])
        nt.links.new(bn2.outputs['Normal'], b.inputs['Normal'])
        rn = _noise(nt, (-1250, -1320), 18.0, 6.0, 0.55, vec=obj)
        rq = _math(nt, (-1000, -1320), 'MULTIPLY_ADD', rn.outputs['Fac'], 0.22)
        rq.inputs[2].default_value = 0.48
        nt.links.new(rq.outputs[0], b.inputs['Roughness'])

    _MAT_CACHE[key] = m
    return m


# =========================================================================== #
# 13.  BUILD                                                                   #
# =========================================================================== #
def _collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in par.children:
        par.children.link(c)
    return c


def build(collection_name=COLLECTION, placements=None, seed=SEED, detail="hero",
          index0=0, parent=None, report=True):
    """Emit one object per figure.

    `placements` is a list of dicts:
        dict(matrix=<4x4 or None>, x=, y=, z=, facing_deg=, index=, detail=,
             posture=, child=)
    Everything is optional; `matrix` wins over x/y/z/facing_deg.  Returns the
    list of created objects.  Each object is named
    ``SPECSEAT_Fig<index>_<posture>`` so a dependant can find "the figure in
    seat N" by name as well as by index.
    """
    coll = _collection(collection_name, parent)
    if placements is None:
        placements = [dict(x=(i % 20 - 9.5) * RAKE["seat_pitch_m"],
                           y=0.0, z=0.0) for i in range(20)]
    objs = []
    for k, pl in enumerate(placements):
        idx = pl.get("index", index0 + k)
        spec = sample_spec(idx, seed, force_posture=pl.get("posture"),
                           force_child=pl.get("child"))
        det = pl.get("detail", detail)
        me = figure_mesh(spec, det)
        nm = "%sFig%05d_%s" % (OBJ_PREFIX, idx, spec["posture"])
        ob = bpy.data.objects.new(nm, me)
        me.name = nm
        if pl.get("matrix") is not None:
            ob.matrix_world = pl["matrix"]
        else:
            ob.matrix_world = seat_anchor_matrix(
                pl.get("x", 0.0), pl.get("y", 0.0), pl.get("z", 0.0),
                pl.get("facing_deg", 0.0), base=pl.get("base"))
        ob["spec_index"] = idx
        ob["posture"] = spec["posture"]
        ob["stature_m"] = round(spec["stature"], 4)
        ob["child"] = spec["child"]
        ob["lod"] = det
        coll.objects.link(ob)
        objs.append(ob)
    if report:
        tris = sum(len(o.data.polygons) for o in objs)
        print(">> %s: %d figures, %d faces, %d postures, %d children"
              % (collection_name, len(objs), tris,
                 len({o["posture"] for o in objs}),
                 sum(1 for o in objs if o["child"])))
    return objs


# =========================================================================== #
# 13b. THE CROWD FIELD — library + geometry-nodes instancer                    #
# =========================================================================== #
# 7,800 seated spectators as 7,800 unique 11.6 k-triangle meshes is 90 M
# triangles and ~5 GB of mesh data. The film cannot carry that and does not need
# to: past ~25 m a figure is 120 px and two figures with different postures,
# statures and garments are indistinguishable from two different people even if
# a third of the stand shares a mesh.
#
# So the population is built as a LIBRARY of unique figures plus an instancer.
# What matters is that the library is large enough that no source dominates -
# `item_gate.realized_instances` measures exactly that, `distinct_sources` and
# `top_source_share`, because "one tree spammed 100 times" is a source-count
# failure and no amount of per-instance rotation fixes it.
#
# This is also the interface `crowd_density_field` (wave 2) needs: it decides
# WHICH seats are occupied, calls build_library once and build_crowd_field per
# grandstand block.
LIBRARY_COLLECTION = OBJ_PREFIX + "Library"


def build_library(n, detail="hero", seed=SEED, index0=1000000,
                  collection_name=LIBRARY_COLLECTION, parent=None):
    """`n` unique figure meshes for a crowd instancer to pick from.

    The objects are linked but `hide_render = True`: geometry nodes' Collection
    Info still reads them (measured, not assumed - see the note in the module
    header), so the sources never render at the origin while every instance does.
    -> (collection, [objects])
    """
    coll = _collection(collection_name, parent)
    objs = []
    for i in range(n):
        spec = sample_spec(index0 + i, seed)
        nm = "%sLib%05d_%s" % (OBJ_PREFIX, i, spec["posture"])
        me = figure_mesh(spec, detail, name=nm)
        ob = bpy.data.objects.new(nm, me)
        ob.hide_render = True
        ob["spec_index"] = index0 + i
        ob["posture"] = spec["posture"]
        ob["stature_m"] = round(spec["stature"], 4)
        ob["child"] = spec["child"]
        coll.objects.link(ob)
        objs.append(ob)
    print(">> library: %d unique figures at %s LOD, %d faces"
          % (len(objs), detail, sum(len(o.data.polygons) for o in objs)))
    return coll, objs


def _crowd_node_group(name, library, n_sources, yaw_sd_deg, seed):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); gi.location = (-600, 0)
    go = ng.nodes.new('NodeGroupOutput'); go.location = (600, 0)
    ci = ng.nodes.new('GeometryNodeCollectionInfo'); ci.location = (-600, -220)
    ci.inputs['Collection'].default_value = library
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints'); iop.location = (200, 0)
    iop.inputs['Pick Instance'].default_value = True
    ridx = ng.nodes.new('FunctionNodeRandomValue'); ridx.location = (-300, -480)
    ridx.data_type = 'INT'
    for s in ridx.inputs:
        if not s.enabled:
            continue
        if s.name == 'Min':
            s.default_value = 0
        elif s.name == 'Max':
            s.default_value = max(0, n_sources - 1)
        elif s.name == 'Seed':
            s.default_value = int(seed) % 30000
    rrot = ng.nodes.new('FunctionNodeRandomValue'); rrot.location = (-300, -760)
    rrot.data_type = 'FLOAT_VECTOR'
    yr = math.radians(yaw_sd_deg)
    for s in rrot.inputs:
        if not s.enabled:
            continue
        if s.name == 'Min':
            s.default_value = (0.0, 0.0, -yr)
        elif s.name == 'Max':
            s.default_value = (0.0, 0.0, yr)
        elif s.name == 'Seed':
            s.default_value = (int(seed) + 7717) % 30000
    ng.links.new(gi.outputs[0], iop.inputs['Points'])
    ng.links.new(ci.outputs['Instances'], iop.inputs['Instance'])
    for s in ridx.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs['Instance Index'])
            break
    for s in rrot.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs['Rotation'])
            break
    ng.links.new(iop.outputs['Instances'], go.inputs[0])
    return ng


def build_crowd_field(name, seat_points, library, n_sources, base=None,
                      collection_name=COLLECTION, seed=SEED, yaw_sd_deg=7.0,
                      parent=None):
    """Instance `library`'s figures onto `seat_points`.

    `seat_points` is a list of (x, y, z) SEAT PAN CENTRES in the frame `base`
    maps to the world - the same anchor `seat_anchor_matrix` takes, so a caller
    can mix loose objects and instanced ones on one seating plan.

    The object is named with OBJ_PREFIX so `item_gate` can find it and walk the
    instances it emits: an instancer the gate cannot attribute to this item is an
    instancer whose variation nobody measures.
    -> the instancer object
    """
    coll = _collection(collection_name, parent)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in seat_points], [], [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = base if base is not None else Matrix.Identity(4)
    coll.objects.link(ob)
    ng = _crowd_node_group(name + "_GN", library, n_sources, yaw_sd_deg, seed)
    md = ob.modifiers.new("crowd", 'NODES')
    md.node_group = ng
    ob["instances"] = len(seat_points)
    ob["library_sources"] = n_sources
    print(">> crowd field %s: %d instances from %d unique sources (%.4f each)"
          % (name, len(seat_points), n_sources, 1.0 / max(1, n_sources)))
    return ob


# =========================================================================== #
# 14.  THE TEST SCENE                                                          #
# =========================================================================== #
# A real fragment of TRIBUNE PRINCIPALE at its real world position (383 m from
# the world origin, so the Object-coordinate law is actually under test), lit by
# the world_contract sun, with the camera at the manifest's own 14.7 m / 28 mm.
GS_FRONT = -34.0
GS_WALK_D = 2.60
TEST_BLOCK = dict(name="TRIBUNE PRINCIPALE", tread=0.88, rise=0.335,
                  front_deck=2.40, base="#22282d", accent="#e2e6e9")


def _c2w_matrix():
    """circuit frame -> world frame, from the contract."""
    if HAVE_WC:
        rot = math.radians(WC.ROT_DEG)
        pd, pw = WC.PIVOT_DESIGN, WC.PIVOT_WORLD
    else:                                             # pragma: no cover
        rot, pd, pw = math.radians(40.0), (-350.0, 72.0), (15.0, 0.0)
    return (Matrix.Translation((pw[0], pw[1], 0.0)) @
            Matrix.Rotation(rot, 4, 'Z') @
            Matrix.Translation((-pd[0], -pd[1], 0.0)))


def _test_rig(coll, x0, x1, rows, rng):
    """The rake the figures sit on: treads, risers, seat shells.

    STAND-IN, and labelled as one: in the assembled world these are
    build_architecture's ARCH_Grandstand meshes.  It exists so the macro render
    shows figures on the seat geometry they were dimensioned against instead of
    floating in space.  Prefix TESTRIG_ keeps it out of the item gate.
    """
    import bmesh
    tread, rise, deck = TEST_BLOCK["tread"], TEST_BLOCK["rise"], TEST_BLOCK["front_deck"]
    bm = bmesh.new()
    bs = bmesh.new()

    def _box(target, p0, p1):
        x0_, y0_, z0_ = p0
        x1_, y1_, z1_ = p1
        vs = [target.verts.new(v) for v in
              [(x0_, y0_, z0_), (x1_, y0_, z0_), (x1_, y1_, z0_), (x0_, y1_, z0_),
               (x0_, y0_, z1_), (x1_, y0_, z1_), (x1_, y1_, z1_), (x0_, y1_, z1_)]]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2),
                  (0, 4, 7, 3), (1, 2, 6, 5)):
            target.faces.new([vs[i] for i in f])

    def box(p0, p1):
        _box(bm, p0, p1)

    def seatbox(p0, p1):
        _box(bs, p0, p1)

    y_first = GS_FRONT - GS_WALK_D
    pans = []
    for r in range(rows):
        yb = y_first - r * tread
        yf = yb - tread
        z0 = deck + r * rise
        box((x0, yf, z0 - 0.02), (x1, yb, z0 + 0.16))
        box((x0, yf - 0.16, z0 - rise), (x1, yf, z0 + 0.16))
        ncol = int((x1 - x0) / RAKE["seat_pitch_m"])
        for c in range(ncol):
            sx = x0 + 0.25 + c * RAKE["seat_pitch_m"]
            sy = yb - tread * 0.42
            sz = z0 + 0.16
            # bucket seat, build_architecture _seat() kind 0, Rz(180) applied
            seatbox((sx - 0.22, sy - 0.22, sz + 0.395), (sx + 0.22, sy + 0.22, sz + 0.445))
            seatbox((sx - 0.22, sy - 0.245, sz + 0.42), (sx + 0.22, sy - 0.195, sz + 0.86))
            seatbox((sx - 0.22, sy + 0.18, sz + 0.405), (sx + 0.22, sy + 0.24, sz + 0.495))
            for sxx in (-0.215, 0.215):
                box((sx + sxx - 0.02, sy - 0.14, sz), (sx + sxx + 0.02, sy + 0.02, sz + 0.42))
            pans.append((sx, sy, sz + 0.445, r, c))
    # the seats themselves: TRIBUNE PRINCIPALE's base #22282d, which is what the
    # crowd is actually read against
    mes = bpy.data.meshes.new("TESTRIG_Seats")
    bs.to_mesh(mes)
    bs.free()
    ms = bpy.data.materials.new("TESTRIG_SeatShell")
    ms.use_nodes = True
    bss = ms.node_tree.nodes.get("Principled BSDF")
    if bss:
        bss.inputs['Base Color'].default_value = tuple(_srgb(TEST_BLOCK["base"])) + (1,)
        bss.inputs['Roughness'].default_value = 0.55
    mes.materials.append(ms)
    obs = bpy.data.objects.new("TESTRIG_Seats", mes)
    obs.matrix_world = _c2w_matrix()
    coll.objects.link(obs)
    me = bpy.data.meshes.new("TESTRIG_Rake")
    bm.to_mesh(me)
    bm.free()
    # albedo 0.33, not 0.52: precast concrete under a blue sky at 0.52 renders as
    # a pale blue field that swamps the crowd, and the crowd is the item.
    mt = bpy.data.materials.new("TESTRIG_Concrete")
    mt.use_nodes = True
    bs = mt.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs['Base Color'].default_value = (0.33, 0.325, 0.31, 1)
        bs.inputs['Roughness'].default_value = 0.88
    me.materials.append(mt)
    ob = bpy.data.objects.new("TESTRIG_Rake", me)
    ob.matrix_world = _c2w_matrix()
    coll.objects.link(ob)
    return pans


def _contract_sky():
    """The contract sun and sky.  world_contract §13 is build_sky's MEASURED
    light; fix_audit_blend.procedural_world() is the same sun rounded to 12.5 deg
    / -58.0 deg, so this is that world at full precision, plus the SUN lamp that
    the contract says carries the key (SKY_SUN_DISC = False)."""
    sun_dir = WC.SUN_DIR if HAVE_WC else (0.5178540, -0.8277670, 0.2159390)
    energy = WC.SUN_ENERGY if HAVE_WC else 115.754
    col = WC.SUN_COLOR if HAVE_WC else (1.0, 0.71632, 0.38712)
    w = bpy.data.worlds.get("R2_ProceduralSky") or bpy.data.worlds.new("R2_ProceduralSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = _nd(nt, 'ShaderNodeOutputWorld', (600, 0))
    bg = _nd(nt, 'ShaderNodeBackground', (400, 0))
    sky = _nd(nt, 'ShaderNodeTexSky', (120, 0))
    avail = {e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items}
    for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        if want in avail:
            sky.sky_type = want
            break
    for attr, val in (("sun_elevation", math.radians(
                          WC.SUN_ELEV_DEG if HAVE_WC else 12.47061)),
                      ("sun_rotation", math.radians(
                          WC.SKY_SUN_ROTATION_DEG if HAVE_WC else 147.96966)),
                      ("sun_disc", False),
                      ("air_density", WC.SKY_AIR if HAVE_WC else 1.0),
                      ("dust_density", WC.SKY_AEROSOL if HAVE_WC else 0.45),
                      ("ozone_density", WC.SKY_OZONE if HAVE_WC else 1.30),
                      ("altitude", 0.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg.inputs['Strength'].default_value = WC.SKY_STRENGTH if HAVE_WC else 1.0
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    ld = bpy.data.lights.new("R2_Sun", 'SUN')
    ld.energy = energy
    ld.color = col
    ld.angle = math.radians(WC.SUN_ANGULAR_DIAM_DEG if HAVE_WC else 0.545)
    lo = bpy.data.objects.new("R2_Sun", ld)
    lo.rotation_euler = Vector(sun_dir).to_track_quat('Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(lo)
    return lo


def build_test_scene(out_path, n_rows=30, n_cols=320, occupancy=0.82,
                     seed=SEED, detail="hero", max_figures=380,
                     population=INSTANCES, library=420):
    """The shot this item has to survive: 14.7 m, 28 mm, contract sun.

    THE SCENE REALIZES THE WHOLE DECLARED POPULATION, 7,800 figures, because a
    per-instance variation check that cannot see the population is not a check.
    The first version of this scene emitted 260 loose objects and the gate said
    so and passed anyway; the gate was then fixed to refuse, and it was right to.

        max_figures  loose UNIQUE objects, in the camera's frustum, hero LOD.
                     These carry the p10-edge and material measurements and are
                     what the macro render actually shows.
        library      unique meshes behind them, instanced by a geometry-nodes
                     field over every remaining occupied seat.

    population = max_figures + instances, exactly `population` people.
    """
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    sc.cycles.samples = 256
    sc.view_settings.view_transform = WC.VIEW_TRANSFORM if HAVE_WC else 'AgX'
    sc.view_settings.exposure = WC.REFERENCE_EXPOSURE_EXTERIOR if HAVE_WC else -3.048
    try:
        sc.view_settings.look = 'None'
    except Exception:
        pass

    import random
    rng = random.Random(seed)
    coll_rig = _collection("TESTRIG")
    x0 = -0.5 * n_cols * RAKE["seat_pitch_m"]
    x1 = -x0
    pans = _test_rig(coll_rig, x0, x1, n_rows, rng)
    base = _c2w_matrix()

    # occupancy, with real clustering: people arrive in twos and threes and
    # leave gaps, they do not fill a stand like a checkerboard.
    seats = sorted(pans, key=lambda p: (p[3], p[4]))
    taken = []
    for (sx, sy, sz, r, c) in seats:
        f = occupancy
        if r < 2:
            f *= 0.88                       # the front row is exposed and colder
        if rng.random() < f:
            taken.append((sx, sy, sz, r, c))
    if len(taken) < population:
        raise RuntimeError("rake seats %d occupied but %d declared: enlarge the "
                           "test rake rather than under-populating the check"
                           % (len(taken), population))
    rng.shuffle(taken)
    taken = taken[:population]
    # the loose UNIQUE band is the seats nearest the middle of the rake front,
    # which is where the camera will be put
    taken.sort(key=lambda p: (abs(p[0]) * 1.0 + p[3] * 0.55))
    near = sorted(taken[:max_figures], key=lambda p: (p[3], p[4]))
    rest = taken[max_figures:]

    placements = []
    for i, (sx, sy, sz, r, c) in enumerate(near):
        # FACING = 0, not 180.  The figure local frame already has +Y as the
        # direction the spectator faces, and the grandstand rake is authored
        # with the seats opening toward circuit +y (build_architecture applies
        # its own Rz(180) because ITS seat is modelled backrest-forward).
        # Adding a second 180 sat all 260 of them facing the back wall, which is
        # exactly what the first macro render showed.
        yaw = rng.gauss(0.0, 7.0)
        placements.append(dict(x=sx, y=sy, z=sz, facing_deg=yaw,
                               base=base, index=r * 1000 + c))
    objs = build(COLLECTION, placements, seed=seed, detail=detail)

    # ---- the rest of the declared population, realized as instances --------
    libcoll, libobjs = build_library(library, detail=detail, seed=seed)
    field = build_crowd_field("%sCrowdField" % OBJ_PREFIX,
                              [(p[0], p[1], p[2]) for p in rest],
                              libcoll, len(libobjs), base=base, seed=seed)
    print(">> population: %d loose unique + %d instanced = %d (declared %d)"
          % (len(objs), len(rest), len(objs) + len(rest), INSTANCES))

    _contract_sky()

    # ---- the camera: EXACTLY the manifest's distance and lens ---------------
    cam = bpy.data.cameras.new("CAM_SPECSEAT_MACRO")
    cam.lens = LENS_AT_CLOSEST_MM
    cam.sensor_width = SENSOR_MM
    cam.dof.use_dof = False
    co = bpy.data.objects.new("CAM_SPECSEAT_MACRO", cam)
    sc.collection.objects.link(co)
    sc.camera = co

    # aim at the crowd mass; nearest figure lands at exactly NEAREST_CAMERA_M
    pts = [o.matrix_world.translation for o in objs]
    focus = Vector((sum(p.x for p in pts) / len(pts),
                    sum(p.y for p in pts) / len(pts),
                    sum(p.z for p in pts) / len(pts)))
    # The Beat-6 crane-out is above and in front of the stand, moving out over
    # the track: the lens is in front, high, looking back and down.  The manifest
    # says it "passes the front top edge at ~9 m", so the depression angle is
    # ~26 deg off horizontal, not the 39 deg of the first pass - at 39 deg the
    # frame is all crowns and no shoulders, and shoulders are the read.
    d_c = Vector(base @ Vector((0.0, 1.0, 0.0)) - base @ Vector((0.0, 0.0, 0.0)))
    d_c.normalize()                                   # circuit +y in world
    up = Vector((0.0, 0.0, 1.0))
    aim = (focus + d_c * 11.0 + up * 5.0)
    co.location = aim
    dvec = (focus - aim)
    co.rotation_euler = dvec.to_track_quat('-Z', 'Y').to_euler()
    # slide the camera along its view axis until the nearest figure is 14.7 m
    fwd = (focus - aim).normalized()
    near = min((Vector(o.matrix_world.translation) - co.location).length for o in objs)
    co.location = co.location + fwd * (near - NEAREST_CAMERA_M)
    near2 = min((Vector(o.matrix_world.translation) - co.location).length for o in objs)
    for _ in range(6):
        err = near2 - NEAREST_CAMERA_M
        if abs(err) < 0.005:
            break
        co.location = co.location + fwd * err
        near2 = min((Vector(o.matrix_world.translation) - co.location).length
                    for o in objs)
    print(">> camera at %.3f m from the nearest seated figure, %.1f mm lens"
          % (near2, cam.lens))

    # ---- a STUDY camera, not the deliverable -------------------------------
    # The macro above is the manifest's shot and this stand is backlit by the
    # contract sun (the front normal is -0.97 on the sun vector), so it is dark
    # ON PURPOSE and that is the truth of the frame.  Judging fold geometry and
    # weave in a shadow is judging nothing, so there is a second camera on the
    # lit side at 6 m / 85 mm.  It is a microscope, not a shot.
    # It is the MACRO CAMERA with a longer lens: same station, same light, same
    # subject, 3.03x the pixels per metre.  The first attempt put a free camera
    # 6 m from the tallest figure on the sun side, which - once the rake grew to
    # its real 320 x 30 - buried the lens inside the crowd and photographed the
    # back of somebody's jacket.  Anything that has to find a clear line of sight
    # through 7,800 people will keep finding a new way not to.
    scam = bpy.data.cameras.new("CAM_SPECSEAT_STUDY")
    scam.lens = 85.0
    scam.sensor_width = SENSOR_MM
    scam.dof.use_dof = False
    sco = bpy.data.objects.new("CAM_SPECSEAT_STUDY", scam)
    sc.collection.objects.link(sco)
    sco.location = co.location.copy()
    sco.rotation_euler = co.rotation_euler.copy()
    print(">> study camera: macro station, 85 mm -> %.0f px/m (macro %.0f px/m)"
          % (PX_PER_M * 85.0 / LENS_AT_CLOSEST_MM, PX_PER_M))
    print(">> px_per_m at that distance = %.1f  (1 px = %.2f mm)"
          % (PX_PER_M, PX_M * 1000.0))

    if HAVE_WC:
        WC.stamp(sc.collection)
    sc.collection["item"] = ITEM_ID
    sc.collection["spectator_seated_version"] = __version__

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_path),
                                relative_remap=False, compress=False)
    ext = [i.filepath for i in bpy.data.images if i.source == 'FILE']
    print(">> external image references: %s" % (ext if ext else "none"))
    print(">> saved %s (%.1f MB)" % (out_path,
                                     os.path.getsize(out_path) / 1048576.0))
    return objs


def _cli():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", default=os.path.join(_HERE, "spectator_seated_test.blend"))
    ap.add_argument("--rows", type=int, default=30)
    ap.add_argument("--cols", type=int, default=320)
    ap.add_argument("--max", type=int, default=380)
    ap.add_argument("--library", type=int, default=420)
    ap.add_argument("--population", type=int, default=INSTANCES)
    ap.add_argument("--detail", default="hero")
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    if a.test:
        build_test_scene(a.out, n_rows=a.rows, n_cols=a.cols, seed=a.seed,
                         detail=a.detail, max_figures=a.max,
                         population=a.population, library=a.library)
    else:
        build()


if __name__ == "__main__" and HAVE_BPY:
    _cli()
