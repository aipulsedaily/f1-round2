#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_figure.py — THE DRIVER.  manifest item ``driver_figure``, wave 1, item 63.

    manifest:  nearest_camera_m 3.0    lens 21 mm    onscreen_px_4k 523
               instances 1             hero True     zone people
    pixels:    px_per_m = (3840 * 21 / 36) / 3.0 = 746.67 px/m
               -> 1 screen pixel is 1.339 mm ON THIS FIGURE.

    "At the T4 hairpin station the cockpit passes within ~3-5 m of a 21 mm lens
     for 3.9 s while the car yaws 176 degrees, and the onboard follow runs 560 m
     beside it - an empty seat with a slack harness would be the single most
     glaring hole in the film.  Only the helmet, shoulders, upper arms and hands
     are ever visible above the cockpit rim, and every one of them is covered,
     so no skin and no face are needed.  The head must move: it stays level under
     lateral load while the car rolls, and it leads the steering into an apex.
     A rigidly bolted head is worse than no driver."
                                                    -- docs/item_manifest.json

WHAT "NO SKIN AND NO FACE ARE NEEDED" MEANS FOR THE SCOPE
--------------------------------------------------------
It means this item is not a nude body that four other agents dress.  It is the
COVERED FIGURE: the thing the lens sees.  So this module builds a complete,
filmable driver — body form, pose, suit, balaclava, gloves, boots, helmet, HANS,
harness, arm restraints, drink tube, radio earpiece — and every garment is a
separate builder with its own material set and its own object, so that

    driver_helmet, driver_gloves, driver_race_suit, driver_boots_and_feet

(the four manifest items that declare ``depends_on: driver_figure``) can each
replace exactly one of them without touching anything else.  Their versions are
the definitive ones.  These are the foundation's own, complete rather than
placeholder, because "an empty seat" is not allowed to persist until four more
agents land.  ``build(parts=...)`` takes the set of parts to emit, so a
dependant asks for the figure WITHOUT the helmet and drops its own on the
``anchor('helmet')`` frame.

EVERY DIMENSION BELOW IS IN METRES AND EVERY ONE OF THEM IS A REAL MEASUREMENT.
A 1.339 mm pixel means these are all resolved features and all of them are MESH:

    harness webbing weave rib          1.6 mm pitch      1.2 px
    webbing edge stitch bead           1.8 mm x 3.0 mm   1.3 px
    tear-off film                      0.25 mm thick     0.19 px  (the STACK
                                       of 6 is 2.9 mm with the air gaps = 2.2 px,
                                       and the pull tabs are 18 x 12 mm = 13 px)
    glove external seam welt           2.6 mm            1.9 px
    glove silicone grip rib            1.3 mm            1.0 px
    helmet visor aperture step         3.0 mm            2.2 px
    helmet chin-intake grille bar      2.4 mm            1.8 px
    HANS carbon 3K twill tow           1.7 mm            1.3 px
    suit flat-felled seam welt         9.0 mm x 1.35 mm  6.7 px
    suit topstitch bead                1.8 mm @ 3.2 mm   1.3 px
    embroidered badge satin stitch     0.45 mm           0.34 px  (material)
    skin pore                          0.25 mm           0.19 px  (never seen)

===========================================================================
THE INTERFACE  (this item is a FOUNDATION.  Four items build on it and none of
                them can ask a question.  Everything here is public and stable.)
===========================================================================

THE FRAME
    Every vertex this module authors, and every anchor it publishes, is in the
    DRIVER FRAME:

        origin   the H-POINT: the hip joint centre, mid-pelvis
        +X       the direction the driver faces (the car's nose)
        +Y       the driver's own LEFT
        +Z       world up

    ``seat_matrix(hpoint_world, heading_deg, recline_deg=0.0)`` builds the 4x4
    that puts the figure in a car.  ``PACKAGE`` reports the space the figure
    needs, so a cockpit can be checked against it (see COCKPIT FIT below).

ANTHROPOMETRY AND POSE
    ``Anthro(stature=1.780, ...)``      segment lengths, breadths, depths.
                                        ``DRIVER`` is the built preset.
    ``DriverPose``                      every joint angle + the four INPUTS that
                                        make the figure act:
                                          steer_deg      wheel angle (+ = left)
                                          lat_g          lateral load (+ = left)
                                          chassis_roll_deg
                                          throttle, brake
    ``POSES``                           named presets: 'hairpin_apex' (the shot),
                                        'straight', 'braking', 'exit',
                                        'grid_idle', 'hands_off'.
    ``solve(pose, anthro) -> Skeleton``
                                        forward kinematics + 2-bone IK for both
                                        arms onto the WHEEL GRIPS and both legs
                                        onto the PEDALS.  ``skel.J['wrist_l']``
                                        is a position, ``skel.F['wrist_l']`` an
                                        orthonormal 3x3 (columns = x, y, z).
                                        ``skel.wheel`` is the wheel frame it
                                        solved against.

    THE HEAD IS NOT BOLTED ON.  ``head_solve(pose)`` implements the manifest's
    requirement directly:  head roll = chassis_roll * NECK_ROLL_FOLLOW
    (0.22 — the neck refuses most of the chassis's roll and keeps the eyes level)
    + lat_g * NECK_LOAD_LEAN (2.6 deg/g outboard, which is what the neck actually
    loses under load), and head yaw LEADS the steering into the apex by
    ``STEER_LEAD`` (0.34 of wheel angle, capped at 19 deg).  Change ``pose.lat_g``
    and ``pose.steer_deg`` per frame and the whole figure re-solves; nothing
    downstream has to know how.

THE ANCHOR CONTRACT — world-of-the-figure frames for everything that attaches
    ``anchors(skel) -> dict[str, Frame]``.  A ``Frame`` has ``.o`` (origin),
    ``.x/.y/.z`` (orthonormal columns), ``.r`` (a characteristic radius, m) and
    ``.mat4()``.

        helmet          head centre, +Z out of the crown, +X out of the visor
        helmet_chin     centre of the chin bar, +Z forward   (drink connector)
        ear_l / ear_r   ear centre, +Z out of the ear         (earpiece, radio)
        collar          the suit collar mouth, +Z up          (balaclava skirt)
        hans_yoke       the HANS yoke seat on the shoulders
        tether_l/r      the helmet tether posts, +Z aft
        shoulder_l/r    top of the deltoid                    (harness path)
        chest           sternum surface, +Z out               (badge, harness)
        back            between the scapulae, +Z out          (extraction handle)
        wrist_l/r       the sleeve cuff mouth                 (GLOVES)
        grip_l/r        THE GRIP AXIS: origin at the centre of the closed fist,
                        +Z along the held bar, +X out of the back of the hand
        ankle_l/r       the trouser cuff mouth                (BOOTS)
        sole_l/r        the sole plane, +Z up                 (pedal contact)
        knee_l/r        patella, +Z forward
        belt_l/r        the lap-belt anchor on the hip
        crotch          the anti-submarine belt anchor
        seat_back       the seat contact plane behind the shoulders

WHAT EACH BUILDER EMITS  (all objects are prefixed ``DRV_``; all are recentred
on emit and every material reads TexCoord -> Object, per law 6)

    build_suit(...)          DRV_Suit          Nomex, 3 layers, real seams
    build_balaclava(...)     DRV_Balaclava     rib-knit hood
    build_gloves(...)        DRV_Glove_L/R     external-seam, silicone grip
    build_boots(...)         DRV_Boot_L/R
    build_helmet(...)        DRV_Helmet_Shell / _Visor / _Tearoffs / _Trim
    build_hans(...)          DRV_HANS
    build_harness(...)       DRV_Harness_Web / _HW
    build_extras(...)        DRV_ArmRestraint / DRV_DrinkTube / DRV_Earpiece

    ``build(coll_name='DRV_Driver', pose='hairpin_apex', parts=ALL_PARTS,
            place=None, uid=0) -> Driver``
    is the single entry point.  ``Driver.objs`` is the object list,
    ``Driver.anchors`` the frame dict, ``Driver.skel`` the solved skeleton.

MATERIALS
    ``materials() -> list``, idempotent, named ``DRV_*``.  Slot order is the
    MAT_* constants:  NOMEX, KNIT, LEATHER, GRIP, PAINT, VISOR, TEAROFF, CARBON,
    WEBBING, HARDWARE, FOAM, RUBBER, EMB, SILICONE.  Every mesh this module
    emits carries all fourteen slots in that order, so a dependant that re-emits
    one garment does not have to rebuild the palette.

    Per-vertex channels every builder writes and every shader reads:
        uv     (u, v) in METRES over the surface — u around, v along.  Thread
               count, weave pitch and stitch pitch are therefore PHYSICAL.
        base   RGBA  panel colour (linear) + A = dye-lot id
        aux    RGBA  (seam, sheen_boost, panel_id, uid)
        wear   RGBA  (abrasion, dirt, oil, sunfade)
        liv    RGBA  four signed distance fields, in metres, for the helmet
               livery.  A livery boundary is thresholded in the SHADER off an
               analytic SDF, so the colour break is crisp to a third of a pixel
               no matter how coarse the shell mesh is.  That is the only honest
               way to get a hard-edged decal with zero image textures.

COCKPIT FIT — A FINDING, NOT A CLAIM
    ``PACKAGE`` publishes the volume this figure occupies about its H-point.
    Measured against round 1's cockpit interior (docs/inventory_iter.json, the
    CI_* objects, whose contact plane is z = 0.340 because the showroom car
    stands on a 0.340 m dais), the round-1 cockpit is NOT anthropometrically
    sized: its seat pan sits 0.42 m above the car's contact plane and its
    headrest centre 0.68 m, i.e. 0.26 m of hip-to-head rise, where a 1.78 m
    driver reclined at 41 deg needs 0.52 m.  The round-1 CI_* interior is a
    stylised dressing, not a package.  This module does NOT shrink the driver to
    fit it — a 1.32 m driver would read as a child at 3 m.  It publishes the
    package it needs and builds its own cockpit proxy for the test scene.  See
    ``PACKAGE`` and ``COCKPIT_PROXY``.

WHAT IS STILL WRONG WITH IT (measured or seen, not guessed)
-----------------------------------------------------------
* THE CONTRACT SKY IS 3.47 STOPS HOT.  An 18 % diffuse card 1.2 m in front of
  CAM_DRV_MACRO under tools/fix_audit_blend.procedural_world() renders at 1.99
  linear where it should render at 0.18.  Every item macro shot under that
  world is hot by the same amount, which is why so many of them read as pale
  clay.  This scene sets view_settings.exposure = -2.8; the WORLD was not
  touched, because it is the contract.  Somebody owns this globally.
* The two HANS tethers read as thin floating pins beside the shoulder at 3 m.
  They are 19 mm webbing seen edge-on, which is correct, but they do not read
  as attached.  Needs a visible swage and a slacker curve.
* The felled seams on the suit (1.95 mm proud, 1.5 px) do not read at the
  delivered 523 px.  They are correct and they are there; they are simply
  under the noise floor of the shot.  driver_race_suit should decide whether
  to exaggerate them.
* The proxy tub's cockpit opening still stair-steps by 7.4 mm at the fore and
  aft ends of the cut.  The padded coaming covers most of it.  PROXY only.
* The visor reads as a bright reflection band rather than a dark shield from
  above.  That IS what a visor does under an open sky and the manifest asks
  for exactly that reflection, but it wants judging against the assembled
  world rather than against a bare sky.

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/driver_figure.py -- --test \
        --out world/items/driver_figure_test.blend
"""

import argparse
import json
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLD)
for _p in (WORLD, os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import world_contract as C
except Exception as _e:                                   # pragma: no cover
    C = None
    print(f"!! world_contract unavailable ({_e}); ground placement disabled")

PFX = "DRV_"
ROOT_COLL = "DRV_Driver"

# ---- the manifest's own numbers, used to size every feature ---------------- #
NEAR_M = 3.0
LENS_MM = 21.0
RES_X_4K = 3840
SENSOR_MM = 36.0
PX_PER_M = (RES_X_4K * LENS_MM / SENSOR_MM) / NEAR_M          # 746.667
PX_M = 1.0 / PX_PER_M                                          # 1.339 mm

MAT_NOMEX, MAT_KNIT, MAT_LEATHER, MAT_GRIP, MAT_PAINT, MAT_VISOR, \
    MAT_TEAROFF, MAT_CARBON, MAT_WEBBING, MAT_HARDWARE, MAT_FOAM, \
    MAT_RUBBER, MAT_EMB, MAT_SILICONE = range(14)
MAT_NAMES = ["Nomex", "Knit", "Leather", "Grip", "Paint", "Visor", "Tearoff",
             "Carbon", "Webbing", "Hardware", "Foam", "Rubber", "Embroidery",
             "Silicone"]


# --------------------------------------------------------------------------- #
#  1.  determinism — one hash, shared with the rest of round 2                  #
# --------------------------------------------------------------------------- #

def hash01(*keys):
    h = 0x811C9DC5
    for k in keys:
        if isinstance(k, str):
            for ch in k:
                h = ((h ^ ord(ch)) * 0x01000193) & 0xFFFFFFFF
        else:
            v = int(round(float(k) * 1024.0)) & 0xFFFFFFFF
            for _ in range(4):
                h = ((h ^ (v & 0xFF)) * 0x01000193) & 0xFFFFFFFF
                v >>= 8
    h ^= h >> 15
    h = (h * 0x2545F491) & 0xFFFFFFFF
    h ^= h >> 13
    return (h & 0xFFFFFF) / float(0x1000000)


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * hash01(*keys)


def pick(seq, *keys):
    return seq[min(int(hash01(*keys) * len(seq)), len(seq) - 1)]


def chance(p, *keys):
    return hash01(*keys) < p


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def sstep(e0, e1, x):
    t = clamp01((np.asarray(x, float) - e0) / max(e1 - e0, 1e-12))
    return t * t * (3.0 - 2.0 * t)


def _vnoise1(x, seed=0):
    x = np.asarray(x, float)
    i = np.floor(x)
    f = x - i

    def h(k):
        k = (np.asarray(k, np.int64) * 1103515245 + seed * 12345 + 7919)
        k = (k ^ (k >> 13)) * 60493
        return ((k ^ (k >> 16)) & 0xFFFF) / 65535.0
    a, b = h(i.astype(np.int64)), h(i.astype(np.int64) + 1)
    u = f * f * (3.0 - 2.0 * f)
    return a * (1 - u) + b * u


def fbm1(x, seed=0, oct=4, gain=0.5, lac=2.03):
    x = np.asarray(x, float)
    s, a, f, n = np.zeros_like(x), 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * _vnoise1(x * f, seed + i * 131)
        n += a
        a *= gain
        f *= lac
    return s / n


def _vnoise2(x, y, seed=0):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x - ix, y - iy

    def h(a, b):
        k = ((a.astype(np.int64) & 0xFFFFF) * 374761393
             + (b.astype(np.int64) & 0xFFFFF) * 668265263
             + (int(seed) & 0xFFFFF) * 2654435761) & 0x7FFFFFFF
        k = ((k ^ (k >> 13)) * 1274126177) & 0x7FFFFFFF
        return ((k ^ (k >> 16)) & 0xFFFF) / 65535.0
    a = h(ix, iy); b = h(ix + 1, iy); c = h(ix, iy + 1); d = h(ix + 1, iy + 1)
    ux = fx * fx * (3 - 2 * fx); uy = fy * fy * (3 - 2 * fy)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def fbm2(x, y, seed=0, oct=4, gain=0.5, lac=2.07):
    x = np.asarray(x, float); y = np.asarray(y, float)
    s, a, f, n = np.zeros_like(x), 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * _vnoise2(x * f, y * f, seed + i * 977)
        n += a
        a *= gain
        f *= lac
    return s / n


def srgb(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def rotmat(axis, ang):
    """Rodrigues, right-handed, radians."""
    a = unit(np.asarray(axis, float))
    c, s = math.cos(ang), math.sin(ang)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) * c + s * K + (1 - c) * np.outer(a, a)


def rx(t): return rotmat((1, 0, 0), t)
def ry(t): return rotmat((0, 1, 0), t)
def rz(t): return rotmat((0, 0, 1), t)


# --------------------------------------------------------------------------- #
#  2.  mesh accumulator                                                         #
# --------------------------------------------------------------------------- #

class Acc:
    """Vertex/face accumulator with absolute index control.

    Absolute indices matter here for the same reason they did in the crew
    overall: the glove finger tubes have to SHARE the palm's ring vertices, and
    the helmet shell has to share the visor aperture's rim with the trim, or
    every one of those junctions gets a shading crack at 1.3 mm per pixel.
    """

    __slots__ = ("name", "_V", "_UV", "_B", "_A", "_W", "_L",
                 "_Fq", "_Ft", "_Mq", "_Mt", "_Sq", "_St", "_n")

    def __init__(self, name):
        self.name = name
        self._V, self._UV, self._B, self._A, self._W, self._L = \
            [], [], [], [], [], []
        self._Fq, self._Ft, self._Mq, self._Mt, self._Sq, self._St = \
            [], [], [], [], [], []
        self._n = 0

    def verts(self, P, uv=None, base=(0.05, 0.05, 0.05, 0.0),
              aux=(0.0, 0.0, 0.0, 0.0), wear=(0.0, 0.0, 0.0, 0.0),
              liv=(-1.0, -1.0, -1.0, 0.0)):
        P = np.asarray(P, float).reshape(-1, 3)
        n = len(P)
        if n == 0:
            return self._n
        self._V.append(P)
        for store, val, w in ((self._UV, uv, 2), (self._B, base, 4),
                              (self._A, aux, 4), (self._W, wear, 4),
                              (self._L, liv, 4)):
            if val is None:
                store.append(np.zeros((n, w)))
            else:
                a = np.asarray(val, float)
                store.append(np.tile(a.reshape(1, w), (n, 1)) if a.ndim == 1
                             else a.reshape(n, w))
        i0 = self._n
        self._n += n
        return i0

    @property
    def n(self):
        return self._n

    def quads(self, I, mat=0, smooth=True):
        I = np.asarray(I, np.int64).reshape(-1, 4)
        if len(I) == 0:
            return
        self._Fq.append(I)
        self._Mq.append(np.full(len(I), int(mat), np.int32))
        self._Sq.append(np.full(len(I), bool(smooth), bool))

    def tris(self, I, mat=0, smooth=True):
        I = np.asarray(I, np.int64).reshape(-1, 3)
        if len(I) == 0:
            return
        self._Ft.append(I)
        self._Mt.append(np.full(len(I), int(mat), np.int32))
        self._St.append(np.full(len(I), bool(smooth), bool))

    def grid_faces(self, IDX, mat=0, smooth=True, wrap_u=False, flip=False):
        """IDX (R, Cu) -> quads.  Rows are v, columns are u."""
        IDX = np.asarray(IDX, np.int64)
        R, Cu = IDX.shape
        if R < 2 or Cu < 2:
            return
        j1 = (np.arange(Cu) + 1) % Cu if wrap_u else np.arange(1, Cu)
        j0 = np.arange(Cu) if wrap_u else np.arange(Cu - 1)
        A = IDX[:-1][:, j0]; B = IDX[:-1][:, j1]
        Cc = IDX[1:][:, j1]; D = IDX[1:][:, j0]
        Q = np.stack([A, B, Cc, D], -1).reshape(-1, 4)
        if flip:
            Q = Q[:, ::-1]
        self.quads(Q, mat, smooth)

    def fan(self, centre_idx, ring, mat=0, smooth=True, flip=False):
        ring = np.asarray(ring, np.int64)
        a = ring
        b = np.roll(ring, -1)
        c = np.full(len(ring), int(centre_idx), np.int64)
        T = np.stack([a, b, c], -1)
        if flip:
            T = T[:, ::-1]
        self.tris(T, mat, smooth)

    def cap(self, ring, mat=0, smooth=False, flip=False, uv=None,
            base=None, aux=None, wear=None, liv=None, P=None):
        """Close a ring with a fan through a new centre vertex."""
        ring = np.asarray(ring, np.int64)
        if P is None:
            raise ValueError("cap needs the ring positions")
        c = P.mean(0)
        ci = self.verts(c.reshape(1, 3), uv=uv, base=base, aux=aux, wear=wear,
                        liv=liv)
        self.fan(ci, ring, mat, smooth, flip)
        return ci

    def emit(self, coll, mats, name=None, recentre=True):
        if self._n == 0:
            return None
        V = np.concatenate(self._V, 0)
        UV = np.concatenate(self._UV, 0)
        B = np.concatenate(self._B, 0)
        A = np.concatenate(self._A, 0)
        W = np.concatenate(self._W, 0)
        L = np.concatenate(self._L, 0)
        polys, mm, ss = [], [], []
        if self._Ft:
            T = np.concatenate(self._Ft, 0)
            polys.append((3, T))
            mm.append(np.concatenate(self._Mt)); ss.append(np.concatenate(self._St))
        if self._Fq:
            Q = np.concatenate(self._Fq, 0)
            polys.append((4, Q))
            mm.append(np.concatenate(self._Mq)); ss.append(np.concatenate(self._Sq))
        if not polys:
            return None
        loops = np.concatenate([F.ravel() for _k, F in polys]).astype(np.int32)
        ltot = np.concatenate([np.full(len(F), k, np.int32) for k, F in polys])
        lstart = np.zeros(len(ltot), np.int32)
        np.cumsum(ltot[:-1], out=lstart[1:])
        M = np.concatenate(mm); S = np.concatenate(ss)

        ctr = 0.5 * (V.min(0) + V.max(0)) if recentre else np.zeros(3)
        V = V - ctr

        nm = name or self.name
        me = bpy.data.meshes.new(nm)
        me.vertices.add(len(V))
        me.loops.add(len(loops))
        me.polygons.add(len(ltot))
        me.vertices.foreach_set("co", V.ravel())
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.foreach_set("loop_start", lstart)
        me.polygons.foreach_set("loop_total", ltot)
        me.update(calc_edges=True)
        me.polygons.foreach_set("use_smooth", S)
        me.polygons.foreach_set("material_index", M)
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", UV[loops].ravel())
        for cname, arr in (("base", B), ("aux", A), ("wear", W), ("liv", L)):
            ca = me.color_attributes.new(name=cname, type='FLOAT_COLOR',
                                         domain='POINT')
            ca.data.foreach_set("color", arr.ravel())
        me.validate(verbose=False)
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(nm, me)
        ob.location = tuple(float(c) for c in ctr)
        coll.objects.link(ob)
        return ob


# --------------------------------------------------------------------------- #
#  3.  lofting toolkit                                                          #
# --------------------------------------------------------------------------- #

def catmull(P, n, alpha=0.5):
    """Centripetal Catmull-Rom through P (K,3) resampled to n points."""
    P = np.asarray(P, float)
    K = len(P)
    if K < 3:
        t = np.linspace(0, 1, n)[:, None]
        return P[0] * (1 - t) + P[-1] * t
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    d = np.linalg.norm(np.diff(Q, axis=0), axis=1) ** alpha
    t = np.concatenate([[0.0], np.cumsum(np.maximum(d, 1e-9))])
    tt = np.linspace(t[1], t[-2], n)
    seg = np.clip(np.searchsorted(t, tt) - 1, 1, len(Q) - 3)
    out = np.zeros((n, 3))
    for k in range(n):
        i = seg[k]
        t0, t1, t2, t3 = t[i - 1], t[i], t[i + 1], t[i + 2]
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        u = tt[k]
        A1 = (t1 - u) / (t1 - t0) * p0 + (u - t0) / (t1 - t0) * p1
        A2 = (t2 - u) / (t2 - t1) * p1 + (u - t1) / (t2 - t1) * p2
        A3 = (t3 - u) / (t3 - t2) * p2 + (u - t2) / (t3 - t2) * p3
        B1 = (t2 - u) / (t2 - t0) * A1 + (u - t0) / (t2 - t0) * A2
        B2 = (t3 - u) / (t3 - t1) * A2 + (u - t1) / (t3 - t1) * A3
        out[k] = (t2 - u) / (t2 - t1) * B1 + (u - t1) / (t2 - t1) * B2
    return out


def arclen(P):
    P = np.asarray(P, float)
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(d)])


def resample(P, n):
    s = arclen(P)
    if s[-1] < 1e-9:
        return np.tile(P[0], (n, 1))
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1)


def frames_along(P, up_hint=(0, 0, 1)):
    """Parallel-transport frames.  -> T (S,3), U (S,3), V (S,3)."""
    P = np.asarray(P, float)
    S = len(P)
    T = np.zeros((S, 3))
    T[:-1] = P[1:] - P[:-1]
    T[-1] = T[-2]
    T[1:-1] = 0.5 * (P[2:] - P[:-2])
    T = unit(T)
    up = unit(np.asarray(up_hint, float))
    u0 = up - T[0] * np.dot(up, T[0])
    if np.linalg.norm(u0) < 1e-6:
        u0 = np.array([1.0, 0.0, 0.0]) - T[0] * T[0][0]
    U = np.zeros((S, 3)); U[0] = unit(u0)
    for i in range(1, S):
        a, b = T[i - 1], T[i]
        ax = np.cross(a, b)
        na = np.linalg.norm(ax)
        if na < 1e-9:
            U[i] = U[i - 1]
        else:
            ang = math.atan2(na, float(np.dot(a, b)))
            U[i] = rotmat(ax / na, ang) @ U[i - 1]
        U[i] = unit(U[i] - b * float(np.dot(U[i], b)))
    V = np.cross(T, U)
    return T, U, V


def superellipse(TH, a, b, n):
    """Radius of a superellipse at angle TH.  a, b, n broadcast against TH."""
    ct, st = np.cos(TH), np.sin(TH)
    return 1.0 / np.maximum(
        (np.abs(ct / np.maximum(a, 1e-9)) ** n
         + np.abs(st / np.maximum(b, 1e-9)) ** n) ** (1.0 / n), 1e-9)


def loft(Cn, X, Y, A, B, EXP, N, disp=None, theta0=0.0, tw=None):
    """Superelliptic loft.

    Cn  (S,3) centres.  X, Y (S,3) section axes.  A, B (S,) semi-axes.
    EXP (S,) superellipse exponent.  N angular samples.
    disp(TH (S,N), VV (S,N), R (S,N)) -> radial offset (S,N), in metres.
    tw  (S,) optional per-station twist of the section, radians.
    -> P (S,N,3), TH (S,N), VV (S,N), R (S,N)
    """
    S = len(Cn)
    th = np.linspace(0.0, 2.0 * math.pi, N, endpoint=False) + theta0
    TH = np.tile(th.reshape(1, N), (S, 1))
    if tw is not None:
        TH = TH + np.asarray(tw, float).reshape(S, 1)
    v = arclen(Cn)
    VV = np.tile(v.reshape(S, 1), (1, N))
    R = superellipse(TH, np.asarray(A).reshape(S, 1),
                     np.asarray(B).reshape(S, 1), np.asarray(EXP).reshape(S, 1))
    if disp is not None:
        R = R + disp(TH, VV, R)
    P = (Cn.reshape(S, 1, 3)
         + (R * np.cos(TH)).reshape(S, N, 1) * X.reshape(S, 1, 3)
         + (R * np.sin(TH)).reshape(S, N, 1) * Y.reshape(S, 1, 3))
    return P, TH, VV, R


def grid_normals(P, wrap_u=True):
    """Vertex normals of an (S,N,3) loft grid."""
    S, N, _ = P.shape
    du = np.zeros_like(P); dv = np.zeros_like(P)
    if wrap_u:
        du = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    else:
        du[:, 1:-1] = P[:, 2:] - P[:, :-2]
        du[:, 0] = P[:, 1] - P[:, 0]
        du[:, -1] = P[:, -1] - P[:, -2]
    dv[1:-1] = P[2:] - P[:-2]
    dv[0] = P[1] - P[0]
    dv[-1] = P[-1] - P[-2]
    Nn = np.cross(dv, du)
    return unit(Nn)


def ring_uv(TH, VV, R):
    """(u, v) in metres: u is arc around the section, v is arc along."""
    return np.stack([TH * R, VV], -1)


def tube(path, r, N=24, closed_ends=True, taper=None):
    """Simple circular tube along a path.  -> (P (S,N,3), T, U, V)."""
    P0 = np.asarray(path, float)
    S = len(P0)
    T, U, V = frames_along(P0)
    rr = np.full(S, float(r)) if np.isscalar(r) else np.asarray(r, float)
    if taper is not None:
        rr = rr * np.asarray(taper, float)
    th = np.linspace(0, 2 * math.pi, N, endpoint=False)
    P = (P0.reshape(S, 1, 3)
         + (rr.reshape(S, 1) * np.cos(th).reshape(1, N)).reshape(S, N, 1) * U.reshape(S, 1, 3)
         + (rr.reshape(S, 1) * np.sin(th).reshape(1, N)).reshape(S, N, 1) * V.reshape(S, 1, 3))
    return P, T, U, V


# --------------------------------------------------------------------------- #
#  4.  shader graph DSL                                                         #
# --------------------------------------------------------------------------- #

class NG:
    """Node-graph builder.

    Inputs are addressed BY NAME, never by index.  Blender 5.2 inserted
    'Thin Wall' at Principled input 5, so every index-addressed graph in this
    project that fed a bump into slot 5 is now feeding Thin Wall.  Names do not
    move.
    """

    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self._x = 0
        self._row = 0

    def n(self, t, defaults=None, **kw):
        nd = self.nt.nodes.new(t)
        self._x += 190
        self._row = (self._row + 1) % 9
        nd.location = (self._x, self._row * 260)
        for k, v in kw.items():
            setattr(nd, k, v)
        if defaults:
            for i, v in defaults.items():
                nd.inputs[i].default_value = v
        return nd

    def _feed(self, node, idx, v):
        if v is None:
            return
        if isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], node.inputs[idx])
        elif (isinstance(v, tuple) and len(v) == 2
              and isinstance(v[0], bpy.types.Node)):
            self.nt.links.new(v[0].outputs[v[1]], node.inputs[idx])
        elif isinstance(v, (tuple, list)):
            cur = node.inputs[idx].default_value
            try:
                w = len(cur)
            except TypeError:
                w = 1
            if w == 4 and len(v) == 3:
                node.inputs[idx].default_value = (*v, 1.0)
            elif w == 3 and len(v) == 4:
                node.inputs[idx].default_value = tuple(v[:3])
            else:
                node.inputs[idx].default_value = tuple(v)
        else:
            node.inputs[idx].default_value = float(v)

    def set(self, node, name, v):
        self._feed(node, name, v)
        return node

    def lk(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def attr(self, name):
        return self.n("ShaderNodeAttribute", attribute_name=name)

    def uv(self):
        return (self.n("ShaderNodeUVMap", uv_map="UVMap"), 0)

    def sep(self, v):
        s = self.n("ShaderNodeSeparateColor"); self._feed(s, 0, v); return s

    def sepxyz(self, v):
        s = self.n("ShaderNodeSeparateXYZ"); self._feed(s, 0, v); return s

    def comb(self, a=None, b=None, c=None):
        m = self.n("ShaderNodeCombineXYZ")
        self._feed(m, 0, a); self._feed(m, 1, b); self._feed(m, 2, c)
        return m

    def math(self, op, a=None, b=None, c=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._feed(m, 0, a); self._feed(m, 1, b); self._feed(m, 2, c)
        return m

    def vmath(self, op, a=None, b=None, scale=None):
        m = self.n("ShaderNodeVectorMath", operation=op)
        self._feed(m, 0, a)
        if b is not None:
            if (isinstance(b, (tuple, list)) and len(b) == 3
                    and not isinstance(b[0], bpy.types.Node)):
                m.inputs[1].default_value = tuple(b)
            else:
                self._feed(m, 1, b)
        if scale is not None:
            self._feed(m, "Scale", scale)
        return m

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n("ShaderNodeMixRGB", blend_type=blend)
        self._feed(m, 0, fac); self._feed(m, 1, a); self._feed(m, 2, b)
        return m

    def noise(self, vec=None, scale=5.0, detail=8.0, rough=0.55, dist=0.0,
              dim='3D'):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dim)
        for k, v in (("Scale", scale), ("Detail", detail), ("Roughness", rough),
                     ("Distortion", dist)):
            if k in nd.inputs:
                nd.inputs[k].default_value = v
        self._feed(nd, 0, vec)
        return nd

    def voro(self, vec=None, scale=10.0, rand=1.0, feature='F1', dim='3D',
             smooth=None):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions=dim)
        for k, v in (("Scale", scale), ("Randomness", rand),
                     ("Smoothness", smooth)):
            if v is not None and k in nd.inputs:
                nd.inputs[k].default_value = v
        self._feed(nd, 0, vec)
        return nd

    def wave(self, vec=None, scale=10.0, dist=0.0, detail=2.0, band='X',
             wtype='BANDS', prof='SIN', droughness=0.5, dscale=1.0):
        nd = self.n("ShaderNodeTexWave", wave_type=wtype, bands_direction=band,
                    wave_profile=prof)
        for k, v in (("Scale", scale), ("Distortion", dist), ("Detail", detail),
                     ("Detail Scale", dscale), ("Detail Roughness", droughness)):
            if k in nd.inputs:
                nd.inputs[k].default_value = v
        self._feed(nd, 0, vec)
        return nd

    def ramp(self, fac, stops):
        r = self.n("ShaderNodeValToRGB")
        self._feed(r, 0, fac)
        el = r.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = (*stops[0][1], 1.0)
        for (p, c) in stops[1:]:
            el.new(p).color = (*c, 1.0)
        return r

    def bump(self, height, strength=0.2, dist=1.0, normal=None):
        b = self.n("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = dist
        self._feed(b, "Height", height)
        if normal is not None:
            self._feed(b, "Normal", normal)
        return b

    def principled(self):
        return self.n("ShaderNodeBsdfPrincipled")

    def out(self, shader):
        o = self.n("ShaderNodeOutputMaterial")
        self.nt.links.new(shader.outputs[0], o.inputs["Surface"])
        return o


# --------------------------------------------------------------------------- #
#  5.  the fourteen materials                                                   #
#                                                                               #
#  Every one reads TexCoord -> Object (law 6) for its 3D fields and the UV      #
#  layer, which this module writes IN METRES, for anything whose scale is a     #
#  thread count.  Not one of them touches Geometry -> Position and not one of   #
#  them samples an image.                                                       #
# --------------------------------------------------------------------------- #

MATS = {}


def _new_mat(name):
    nm = PFX + name
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    g = NG(m)
    b = g.principled()
    out = g.out(b)
    return m, g, b, out


class Ch4:
    """Four scalar channels off one FLOAT_COLOR attribute.

    Separate Color gives three outputs, not four -- the alpha comes off the
    Attribute node itself.  Every channel this module writes is meaningful, so
    dropping the fourth would silently lose sunfade and the per-instance uid.
    """

    def __init__(self, g, name):
        self.a = g.attr(name)
        self.s = g.sep(self.a)

    def __call__(self, i):
        return (self.s, i) if i < 3 else (self.a, 3)


def _common(g):
    """base, aux, wear, liv, object-space P (metres), uv (metres)."""
    base = g.attr("base")
    aux = Ch4(g, "aux")
    wear = Ch4(g, "wear")
    liv = g.attr("liv")
    tc = g.n("ShaderNodeTexCoord")
    p = (tc, 3)                      # Object
    uv = g.uv()
    return base, aux, wear, liv, p, uv


def lift(g, base, k):
    """A LIGHTER (or darker) version of the base colour, k x it.

    THE BUG THIS FIXES.  Every "worn/faded/polished" variant in the first cut
    of these materials was written as ``mix(0.5, base, (0.72, 0.70, 0.68))``,
    meaning "halfway to a light grey".  On a Nomex base of 0.009 linear that is
    not a variation, it is a FORTY-FOLD lift, and it is why the first macro
    render came back as a white clay figure.  A variation on a colour is a
    MULTIPLE of it.
    """
    return g.mix(1.0, base, (k, k, k), blend='MULTIPLY')


def _uvxy(g, uv, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    """Scale the metre-UV into a texture vector."""
    s = g.sepxyz(uv)
    return g.comb(g.math('ADD', g.math('MULTIPLY', (s, 0), sx), ox),
                  g.math('ADD', g.math('MULTIPLY', (s, 1), sy), oy), 0.0)


def mat_nomex():
    """Three-layer FIA 8856-2018 knit: a 2/1 twill face over a quilted mid.

    The weave is authored in the METRE UV, so the thread count is physical:
    the face twill is 1.45 mm and reads as 1.08 screen pixels at 3 m.  What
    actually sells Nomex at this distance is not the weave, it is that the
    cloth is MATTE with a low, wide sheen lobe and that the dye sits unevenly
    over a fibre that will not take dye evenly.  Both are here.
    """
    m, g, b, out = _new_mat("Nomex")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    # --- the twill: two wave banks at +-63 deg in the cloth plane ----------
    d1 = _uvxy(g, uv, 690.0, 340.0)
    d2 = _uvxy(g, uv, -690.0, 340.0)
    w1 = g.wave(d1, scale=1.0, dist=0.9, detail=3.0, band='X', prof='SIN')
    w2 = g.wave(d2, scale=1.0, dist=0.9, detail=3.0, band='X', prof='SIN')
    twill = g.math('MULTIPLY', g.math('ADD', w1, w2), 0.5)
    # yarn slub: the individual filament bundle, 0.55 mm
    slub = g.noise(_uvxy(g, uv, 1800.0, 1800.0), scale=1.0, detail=6.0,
                   rough=0.62, dim='2D')
    # quilting: the 12 mm channel stitch of the mid layer, only where panel==1
    quilt = g.wave(_uvxy(g, uv, 0.0, 83.0), scale=1.0, dist=0.0, detail=1.0,
                   band='Y', prof='TRI')

    # --- dye ---------------------------------------------------------------
    lot = g.noise(g.vmath('MULTIPLY', p, (7.0, 7.0, 7.0)), scale=1.0,
                  detail=4.0, rough=0.5)
    col = g.mix(g.math('MULTIPLY', lot, 0.30), base, lift(g, base, 1.42))
    col = g.mix(g.math('MULTIPLY', fade, 0.55), col, lift(g, base, 1.85))
    # abrasion polishes the twill flat and lifts the colour
    abrn = g.noise(g.vmath('MULTIPLY', p, (26.0, 26.0, 26.0)), scale=1.0,
                   detail=7.0, rough=0.7)
    abrm = g.ramp(g.math('MULTIPLY', abr, g.math('ADD', 0.45, abrn)),
                  [(0.24, (0, 0, 0)), (0.62, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', abrm, 0.60), col, lift(g, base, 2.30))
    # oil and brake dust off the gloves, on the chest and the cuffs
    grime = g.voro(g.vmath('MULTIPLY', p, (34.0, 34.0, 34.0)), scale=1.0,
                   rand=0.9, feature='F1')
    col = g.mix(g.math('MULTIPLY', dirt,
                       g.math('ADD', 0.30, g.math('MULTIPLY', grime, 0.9)),
                       clamp=True),
                col, (0.0165, 0.0142, 0.0118))
    col = g.mix(g.math('MULTIPLY', oil, 0.7, clamp=True), col,
                (0.0060, 0.0050, 0.0044))
    g.set(b, "Base Color", col)

    # --- response ----------------------------------------------------------
    rough = g.math('ADD', 0.815,
                   g.math('MULTIPLY', g.math('SUBTRACT', slub, 0.5), 0.16))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', abrm, 0.17))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', sheen, 0.10))
    g.set(b, "Roughness", g.math('MINIMUM', rough, 0.96))
    # SHEEN IS A THIN LOBE, NOT A SECOND ALBEDO.  0.34 with a near-white tint
    # was adding a 0.30-albedo white layer over a 0.009 fabric -- 30x the
    # colour underneath it.  Nomex has a low, tight sheen and it is the
    # FABRIC's colour, not white.
    g.set(b, "Sheen Weight", g.math('ADD', 0.055, g.math('MULTIPLY', sheen, 0.055)))
    g.set(b, "Sheen Roughness", 0.34)
    g.set(b, "Sheen Tint", lift(g, base, 3.2))
    g.set(b, "Specular IOR Level", 0.28)

    # --- relief: twill + slub + seam ridge + quilt channel ------------------
    h = g.math('ADD', g.math('MULTIPLY', twill, 0.55),
               g.math('MULTIPLY', slub, 0.45))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', panel, quilt), 0.9))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 1.4))
    g.set(b, "Normal", g.bump(h, 0.52, 0.0022))
    return m


def mat_knit():
    """1x1 rib knit — the balaclava, the sleeve cuffs, the collar lining.

    Rib is a COURSE structure: the wales run one way at 1.9 mm and the courses
    cross them at 1.35 mm, and the loop heads catch light in a line.  Three wave
    banks and a fuzz noise; the fuzz is what stops knit reading as corduroy.
    """
    m, g, b, out = _new_mat("Knit")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    wale = g.wave(_uvxy(g, uv, 526.0, 0.0), scale=1.0, dist=0.25, detail=2.0,
                  band='X', prof='SIN')
    course = g.wave(_uvxy(g, uv, 0.0, 740.0), scale=1.0, dist=0.35, detail=2.0,
                    band='Y', prof='SIN')
    loop = g.wave(_uvxy(g, uv, 263.0, 370.0), scale=1.0, dist=1.4, detail=3.0,
                  band='DIAGONAL', prof='SIN')
    fuzz = g.noise(g.vmath('MULTIPLY', p, (900.0, 900.0, 900.0)), scale=1.0,
                   detail=4.0, rough=0.75)
    pill = g.voro(g.vmath('MULTIPLY', p, (260.0, 260.0, 260.0)), scale=1.0,
                  rand=1.0, feature='F1')

    col = g.mix(g.math('MULTIPLY', fade, 0.55), base, lift(g, base, 1.55))
    col = g.mix(g.math('MULTIPLY', dirt, 0.8, clamp=True), col,
                (0.0140, 0.0128, 0.0118))
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', fuzz, 0.45), 0.6,
                       clamp=True), col, lift(g, base, 2.10))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('ADD', 0.88, g.math('MULTIPLY',
                                     g.math('SUBTRACT', fuzz, 0.5), 0.10)))
    g.set(b, "Sheen Weight", 0.11)
    g.set(b, "Sheen Roughness", 0.45)
    g.set(b, "Sheen Tint", lift(g, base, 3.0))
    g.set(b, "Specular IOR Level", 0.20)
    h = g.math('ADD', g.math('MULTIPLY', wale, 0.75),
               g.math('MULTIPLY', course, 0.42))
    h = g.math('ADD', h, g.math('MULTIPLY', loop, 0.28))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('SUBTRACT', pill, 0.6), 0.5))
    h = g.math('ADD', h, g.math('MULTIPLY', fuzz, 0.20))
    g.set(b, "Normal", g.bump(h, 0.5, 0.0013))
    return m


def mat_leather():
    """Glove back and finger panels: 0.55 mm goat, chrome-tanned, matt finish.

    Grain is a two-scale Voronoi — the coarse hill/valley cell at 1.6 mm and the
    fine pore at 0.35 mm — plus the stretch flattening over the knuckles, which
    is the ``abrasion`` channel.  Leather that is uniformly grained reads as
    plastic; the knuckles have to be smoother than the web.
    """
    m, g, b, out = _new_mat("Leather")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    grain = g.voro(g.vmath('MULTIPLY', p, (620.0, 620.0, 620.0)), scale=1.0,
                   rand=0.96, feature='DISTANCE_TO_EDGE')
    pore = g.voro(g.vmath('MULTIPLY', p, (2900.0, 2900.0, 2900.0)), scale=1.0,
                  rand=1.0, feature='DISTANCE_TO_EDGE')
    crease = g.noise(g.vmath('MULTIPLY', p, (130.0, 130.0, 130.0)), scale=1.0,
                     detail=8.0, rough=0.68)
    burnish = g.ramp(g.math('MULTIPLY', abr, g.math('ADD', 0.5, crease)),
                     [(0.20, (0, 0, 0)), (0.70, (1, 1, 1))])

    col = g.mix(g.math('MULTIPLY', crease, 0.35), base, lift(g, base, 0.62))
    col = g.mix(g.math('MULTIPLY', burnish, 0.65), col, lift(g, base, 2.05))
    col = g.mix(g.math('MULTIPLY', dirt, 0.85, clamp=True), col,
                (0.0105, 0.0090, 0.0078))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('SUBTRACT',
                 g.math('ADD', 0.64,
                        g.math('MULTIPLY', g.math('SUBTRACT', grain, 0.5), 0.13)),
                 g.math('MULTIPLY', burnish, 0.26)))
    g.set(b, "Specular IOR Level", 0.45)
    g.set(b, "Coat Weight", g.math('MULTIPLY', burnish, 0.10))
    g.set(b, "Coat Roughness", 0.42)
    h = g.math('ADD', g.math('MULTIPLY', grain, 0.9),
               g.math('MULTIPLY', pore, 0.35))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('SUBTRACT', crease, 0.5), 1.1))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 1.2))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', burnish, 0.5))
    g.set(b, "Normal", g.bump(h, 0.30, 0.0009))
    return m


def mat_grip():
    """Silicone grip print on the glove palm, and the wheel's own suede.

    The printed rib is MESH (1.3 mm, 1.0 px).  The material's job is the
    difference between silicone and leather: silicone is darker, glossier at a
    grazing angle, and it picks up a smear of rubber dust that leather does not.
    """
    m, g, b, out = _new_mat("Grip")
    base, aux, wear, liv, p, uv = _common(g)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    fine = g.noise(g.vmath('MULTIPLY', p, (1500.0, 1500.0, 1500.0)), scale=1.0,
                   detail=5.0, rough=0.6)
    bloom = g.voro(g.vmath('MULTIPLY', p, (180.0, 180.0, 180.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1', smooth=0.35)
    polish = g.ramp(abr, [(0.15, (0, 0, 0)), (0.75, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', fine, 0.35), base, lift(g, base, 1.50))
    col = g.mix(g.math('MULTIPLY', dirt, 0.7, clamp=True), col,
                (0.0125, 0.0115, 0.0105))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('SUBTRACT',
                 g.math('ADD', 0.58, g.math('MULTIPLY', bloom, 0.16)),
                 g.math('MULTIPLY', polish, 0.30)))
    g.set(b, "Specular IOR Level", 0.52)
    h = g.math('ADD', g.math('MULTIPLY', fine, 0.6), g.math('MULTIPLY', bloom, 0.5))
    g.set(b, "Normal", g.bump(h, 0.22, 0.0006))
    return m


def mat_paint():
    """Helmet livery.

    THE LIVERY IS GEOMETRY-FREE AND STILL HARD-EDGED.  Every vertex of the shell
    carries four signed distance fields, in metres, to the four livery
    boundaries; the shader thresholds each one with a 0.4 mm smoothstep.  So the
    colour break is sharp to a third of a screen pixel however coarse the shell
    mesh is, and there is not an image texture anywhere near it.

    Over the top: two-stage clear.  Orange peel at 4.5 mm — the single most
    reliable tell that a painted shell is real and not a shaded sphere — plus
    polish swirl, wet-sanded flats round the vents, and the dust that a helmet
    picks up in a pit lane.
    """
    m, g, b, out = _new_mat("Paint")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    L = g.sep(liv)
    lA = g.n("ShaderNodeSeparateXYZ")
    g._feed(lA, 0, liv)

    HL = brand_palette()
    # base coat, then each band composited over it through its own SDF.
    # The `liv` channels carry 0.5 + signed_distance_metres * 25, so one
    # channel unit is 40 mm and a 0.40 mm transition is 0.010 units --
    # a third of a screen pixel at 3 m.
    col = g.mix(g.math('MULTIPLY', panel, 1.0), HL["shell"], HL["crown"])
    e = 0.010
    for ch, c in ((0, HL["sweep"]), (1, HL["chevron"]), (2, HL["accent"])):
        k = g.ramp((lA, ch), [(0.5 - e, (0, 0, 0)), (0.5 + e, (1, 1, 1))])
        col = g.mix(k, col, c)
    # the 1.6 mm pinstripe along the sweep boundary: |sdf| < 0.8 mm is 0.020
    pin = g.ramp(g.math('ABSOLUTE', g.math('SUBTRACT', (lA, 0), 0.5)),
                 [(0.018, (1, 1, 1)), (0.026, (0, 0, 0))])
    col = g.mix(pin, col, HL["pin"])

    # metallic flake in the sweep only
    flake = g.voro(g.vmath('MULTIPLY', p, (5200.0, 5200.0, 5200.0)), scale=1.0,
                   rand=1.0, feature='F1')
    fl = g.ramp(flake, [(0.55, (0, 0, 0)), (0.95, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', fl, 0.13), col, (0.66, 0.63, 0.58))

    # dust, and the rubber marbles that stick to a helmet at a hairpin
    dust = g.noise(g.vmath('MULTIPLY', p, (55.0, 55.0, 55.0)), scale=1.0,
                   detail=9.0, rough=0.66)
    dm = g.ramp(g.math('MULTIPLY', dirt, g.math('ADD', 0.35, dust)),
                [(0.28, (0, 0, 0)), (0.80, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', dm, 0.26), col, (0.0225, 0.0198, 0.0166))
    g.set(b, "Base Color", col)

    swirl = g.noise(g.vmath('MULTIPLY', p, (900.0, 900.0, 900.0)), scale=1.0,
                    detail=4.0, rough=0.5)
    g.set(b, "Roughness",
          g.math('ADD', 0.085, g.math('ADD',
                                      g.math('MULTIPLY', dm, 0.34),
                                      g.math('MULTIPLY', swirl, 0.05))))
    g.set(b, "Metallic", g.math('MULTIPLY', fl, 0.26))
    g.set(b, "Specular IOR Level", 0.6)
    g.set(b, "Coat Weight", g.math('SUBTRACT', 0.36, g.math('MULTIPLY', dm, 0.22)))
    g.set(b, "Coat Roughness",
          g.math('ADD', 0.075, g.math('MULTIPLY', dm, 0.26)))

    peel = g.noise(g.vmath('MULTIPLY', p, (215.0, 215.0, 215.0)), scale=1.0,
                   detail=3.0, rough=0.45)
    scratch = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=740.0,
                     dist=13.0, detail=5.0, band='DIAGONAL', prof='SAW')
    h = g.math('ADD', g.math('MULTIPLY', peel, 1.0),
               g.math('MULTIPLY', g.math('MULTIPLY', scratch, abr), 0.55))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 0.8))
    g.set(b, "Coat Normal", g.bump(h, 0.16, 0.0022))
    g.set(b, "Normal", g.bump(g.math('MULTIPLY', peel, 0.4), 0.06, 0.0022))
    return m


def mat_visor():
    """3.0 mm tinted polycarbonate, 62 % VLT.

    Transmissive, not black.  What makes a visor read as glass rather than as a
    dark panel is the second surface: light gets in, crosses 3 mm of tinted
    plastic, and comes back out — so the reflection and the transmitted image
    are offset.  Principled transmission with a real IOR (1.586) and a real
    thickness does that.  On top: the wipe arc a driver's glove leaves, and the
    fine circular scratch field from the tear-off tabs.
    """
    m, g, b, out = _new_mat("Visor")
    base, aux, wear, liv, p, uv = _common(g)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    smear = g.noise(g.vmath('MULTIPLY', p, (42.0, 42.0, 42.0)), scale=1.0,
                    detail=7.0, rough=0.55)
    scr = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=1350.0,
                 dist=7.5, detail=6.0, band='X', prof='SAW')
    dust = g.voro(g.vmath('MULTIPLY', p, (700.0, 700.0, 700.0)), scale=1.0,
                  rand=1.0, feature='F1')
    dm = g.ramp(dust, [(0.86, (0, 0, 0)), (0.99, (1, 1, 1))])
    # A dark visor is 20-30 % VLT, not 86 %.  The first cut transmitted 86 %
    # and rendered as a clear window with the sky straight through it, which
    # is why the aperture read as a hole in the render.
    g.set(b, "Base Color", (0.0072, 0.0078, 0.0098))
    g.set(b, "Transmission Weight", 0.22)
    g.set(b, "IOR", 1.586)
    g.set(b, "Roughness",
          g.math('ADD', 0.022,
                 g.math('ADD', g.math('MULTIPLY', g.math('MULTIPLY', smear, oil), 0.11),
                        g.math('MULTIPLY', dm, 0.30))))
    g.set(b, "Coat Weight", 0.45)
    g.set(b, "Coat Roughness", 0.018)
    h = g.math('ADD', g.math('MULTIPLY', g.math('MULTIPLY', scr, abr), 0.7),
               g.math('MULTIPLY', g.math('MULTIPLY', smear, oil), 0.5))
    h = g.math('ADD', h, g.math('MULTIPLY', dm, 0.4))
    g.set(b, "Normal", g.bump(h, 0.10, 0.0004))
    return m


def mat_tearoff():
    """0.25 mm clear PET tear-off.

    Six of them.  Each one is 92 % transmissive and 4 % hazy, and the haze
    COMPOUNDS: the bottom film in a stack of six is looking through 1.5 mm of
    plastic and five interfaces, which is exactly why a used stack goes milky at
    the edges.  ``panel`` carries the film's index in the stack, so the haze
    grows down the stack instead of every film being identical.
    """
    m, g, b, out = _new_mat("Tearoff")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    haze = g.noise(g.vmath('MULTIPLY', p, (320.0, 320.0, 320.0)), scale=1.0,
                   detail=6.0, rough=0.6)
    scr = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=2600.0,
                 dist=14.0, detail=6.0, band='DIAGONAL', prof='SAW')
    grit = g.voro(g.vmath('MULTIPLY', p, (1600.0, 1600.0, 1600.0)), scale=1.0,
                  rand=1.0, feature='F1')
    gm = g.ramp(grit, [(0.88, (0, 0, 0)), (1.0, (1, 1, 1))])
    # SIX FILMS AT 92 % TRANSMISSION IS TWELVE AIR INTERFACES, EACH REFLECTING
    # 4 % OF A VERY BRIGHT SKY.  The first cut did exactly that and the stack
    # rendered as a milky white band that hid the visor completely -- the one
    # thing the manifest asks this helmet for.  A real tear-off is optically
    # clean; what you see of it is its EDGES and its TAB, not its face.
    g.set(b, "Base Color", (0.965, 0.970, 0.965))
    g.set(b, "Transmission Weight",
          g.math('SUBTRACT', 0.990, g.math('MULTIPLY', panel, 0.012)))
    g.set(b, "IOR", 1.575)
    g.set(b, "Roughness",
          g.math('ADD', 0.006,
                 g.math('ADD',
                        g.math('MULTIPLY', g.math('MULTIPLY', haze, panel), 0.045),
                        g.math('MULTIPLY', gm, 0.12))))
    g.set(b, "Coat Weight", 0.0)
    h = g.math('ADD', g.math('MULTIPLY', scr, 0.35), g.math('MULTIPLY', gm, 0.5))
    h = g.math('ADD', h, g.math('MULTIPLY', haze, 0.12))
    g.set(b, "Normal", g.bump(h, 0.035, 0.00035))
    return m


def mat_carbon():
    """3K 2x2 twill prepreg — the HANS yoke, the helmet chin plate, the seat.

    A 3K tow is 1.7 mm wide and the twill repeat is 6.8 mm.  At 1.34 mm/px the
    TOW is 1.3 px and the repeat is 5 px, so the weave has to be right and it has
    to be ANISOTROPIC: a carbon tow is a bundle of parallel filaments and it
    shines along its own direction, which is what makes real carbon shimmer as
    the light moves and painted carbon not.  Two wave banks at right angles plus
    a tangent rotation driven by which bank wins.
    """
    m, g, b, out = _new_mat("Carbon")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    warp = g.wave(_uvxy(g, uv, 147.0, 0.0), scale=1.0, dist=0.0, detail=2.0,
                  band='X', prof='TRI')
    weft = g.wave(_uvxy(g, uv, 0.0, 147.0), scale=1.0, dist=0.0, detail=2.0,
                  band='Y', prof='TRI')
    # 2x2 twill: the over/under pattern shifts by one tow per pick
    twill = g.wave(_uvxy(g, uv, 73.5, 73.5), scale=1.0, dist=0.0, detail=1.0,
                   band='DIAGONAL', prof='SAW')
    tw = g.ramp(twill, [(0.0, (0, 0, 0)), (0.5, (0, 0, 0)),
                        (0.5, (1, 1, 1)), (1.0, (1, 1, 1))])
    over = g.mix(tw, warp, weft)
    fil = g.noise(_uvxy(g, uv, 4200.0, 300.0), scale=1.0, detail=4.0,
                  rough=0.5, dim='2D')
    pin = g.voro(g.vmath('MULTIPLY', p, (900.0, 900.0, 900.0)), scale=1.0,
                 rand=1.0, feature='F1')
    pm = g.ramp(pin, [(0.93, (0, 0, 0)), (1.0, (1, 1, 1))])

    col = g.mix(g.math('MULTIPLY', over, 0.55), (0.0075, 0.0078, 0.0085),
                (0.030, 0.031, 0.035))
    col = g.mix(g.math('MULTIPLY', fil, 0.30), col, (0.048, 0.049, 0.054))
    col = g.mix(g.math('MULTIPLY', dirt, 0.6, clamp=True), col,
                (0.026, 0.023, 0.020))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('ADD', 0.145,
                 g.math('ADD', g.math('MULTIPLY', pm, 0.35),
                        g.math('MULTIPLY', g.math('SUBTRACT', fil, 0.5), 0.07))))
    g.set(b, "Anisotropic", 0.72)
    g.set(b, "Anisotropic Rotation", g.math('MULTIPLY', tw, 0.25))
    g.set(b, "Coat Weight", g.math('SUBTRACT', 0.26, g.math('MULTIPLY', abr, 0.16)))
    g.set(b, "Coat Roughness",
          g.math('ADD', 0.05, g.math('MULTIPLY', abr, 0.22)))
    h = g.math('ADD', g.math('MULTIPLY', over, 1.0), g.math('MULTIPLY', fil, 0.25))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', pm, 1.2))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 0.9))
    g.set(b, "Normal", g.bump(h, 0.30, 0.0014))
    return m


def mat_webbing():
    """FIA 8853-2016 harness webbing: 76 mm shoulder, 51 mm lap.

    Polyester, 2/2 twill, ~1.6 mm rib across the width and a hard selvedge at
    each edge that is denser, glossier and 0.35 mm thicker than the field.  The
    selvedge is MESH; the rib is here.  Webbing that has been through a season
    is bleached along the top face and grubby along the bottom, so ``sunfade``
    and ``dirt`` pull in opposite directions.
    """
    m, g, b, out = _new_mat("Webbing")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    rib = g.wave(_uvxy(g, uv, 0.0, 625.0), scale=1.0, dist=0.30, detail=3.0,
                 band='Y', prof='SIN')
    cross = g.wave(_uvxy(g, uv, 340.0, 0.0), scale=1.0, dist=0.25, detail=2.0,
                   band='X', prof='SIN')
    yarn = g.noise(_uvxy(g, uv, 2400.0, 700.0), scale=1.0, detail=5.0,
                   rough=0.6, dim='2D')
    fuzz = g.voro(g.vmath('MULTIPLY', p, (1400.0, 1400.0, 1400.0)), scale=1.0,
                  rand=1.0, feature='F1')

    col = g.mix(g.math('MULTIPLY', fade, 0.60), base, lift(g, base, 1.75))
    col = g.mix(g.math('MULTIPLY', dirt, 0.85, clamp=True), col,
                (0.0115, 0.0100, 0.0086))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', abr, yarn), 0.55), col,
                lift(g, base, 2.20))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('SUBTRACT',
                 g.math('ADD', 0.70,
                        g.math('MULTIPLY', g.math('SUBTRACT', yarn, 0.5), 0.13)),
                 g.math('MULTIPLY', sheen, 0.18)))
    g.set(b, "Sheen Weight", 0.085)
    g.set(b, "Sheen Roughness", 0.32)
    g.set(b, "Sheen Tint", lift(g, base, 3.4))
    g.set(b, "Specular IOR Level", 0.36)
    h = g.math('ADD', g.math('MULTIPLY', rib, 0.95),
               g.math('MULTIPLY', cross, 0.35))
    h = g.math('ADD', h, g.math('MULTIPLY', yarn, 0.30))
    h = g.math('ADD', h, g.math('MULTIPLY',
                                g.math('MULTIPLY', g.math('SUBTRACT', fuzz, 0.7), abr),
                                1.4))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 1.5))
    g.set(b, "Normal", g.bump(h, 0.42, 0.0011))
    return m


def mat_hardware():
    """Buckle plates, adjuster bars, tether hooks, visor pivots, zip pulls.

    ``panel`` picks the alloy: 0 = passivated stainless, 0.5 = hard-anodised
    aluminium, 1 = titanium.  ``sheen`` picks brushed vs. bead-blasted.  One
    material, three metals, because the harness has all three on it and a single
    grey would flatten the whole cluster.
    """
    m, g, b, out = _new_mat("Hardware")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)

    brush = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=1650.0,
                   dist=2.2, detail=4.0, band='X', prof='SAW')
    blast = g.voro(g.vmath('MULTIPLY', p, (5200.0, 5200.0, 5200.0)), scale=1.0,
                   rand=1.0, feature='F1')
    pit = g.voro(g.vmath('MULTIPLY', p, (620.0, 620.0, 620.0)), scale=1.0,
                 rand=1.0, feature='F1')
    pm = g.ramp(pit, [(0.90, (0, 0, 0)), (1.0, (1, 1, 1))])
    film = g.noise(g.vmath('MULTIPLY', p, (95.0, 95.0, 95.0)), scale=1.0,
                   detail=6.0, rough=0.6)

    steel = (0.552, 0.556, 0.562)
    anod = lift(g, base, 0.55)
    tita = (0.542, 0.520, 0.492)
    col = g.mix(g.ramp(panel, [(0.0, (0, 0, 0)), (0.5, (1, 1, 1))]), steel, anod)
    col = g.mix(g.ramp(panel, [(0.5, (0, 0, 0)), (1.0, (1, 1, 1))]), col, tita)
    col = g.mix(g.math('MULTIPLY', dirt, 0.55, clamp=True), col,
                (0.0230, 0.0200, 0.0170))
    g.set(b, "Base Color", col)
    g.set(b, "Metallic",
          g.math('SUBTRACT', 1.0, g.math('MULTIPLY',
                                         g.math('MULTIPLY', panel, 0.35), 1.0)))
    r = g.math('ADD', 0.30, g.math('MULTIPLY', blast, 0.22))
    r = g.math('SUBTRACT', r, g.math('MULTIPLY', sheen, 0.16))
    r = g.math('SUBTRACT', r, g.math('MULTIPLY', abr, 0.13))
    r = g.math('ADD', r, g.math('MULTIPLY', pm, 0.35))
    g.set(b, "Roughness", r)
    g.set(b, "Anisotropic", g.math('MULTIPLY', sheen, 0.6))
    h = g.math('ADD', g.math('MULTIPLY', g.math('MULTIPLY', brush, sheen), 0.6),
               g.math('MULTIPLY', blast, 0.35))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', pm, 1.6))
    h = g.math('ADD', h, g.math('MULTIPLY', film, 0.15))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 1.0))
    g.set(b, "Normal", g.bump(h, 0.13, 0.0007))
    return m


def mat_foam():
    """Open-cell EPP and the fire-retardant Nomex-faced comfort liner.

    Only ever seen in slivers — inside the helmet aperture, under the HANS
    yoke, behind the collar — but those slivers are 3 to 10 px wide and a flat
    dark grey there reads as a hole.
    """
    m, g, b, out = _new_mat("Foam")
    base, aux, wear, liv, p, uv = _common(g)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    cell = g.voro(g.vmath('MULTIPLY', p, (450.0, 450.0, 450.0)), scale=1.0,
                  rand=1.0, feature='DISTANCE_TO_EDGE')
    fine = g.voro(g.vmath('MULTIPLY', p, (1700.0, 1700.0, 1700.0)), scale=1.0,
                  rand=1.0, feature='F1')
    nap = g.noise(g.vmath('MULTIPLY', p, (2600.0, 2600.0, 2600.0)), scale=1.0,
                  detail=4.0, rough=0.7)
    col = g.mix(g.math('MULTIPLY', cell, 0.55), base, lift(g, base, 1.60))
    col = g.mix(g.math('MULTIPLY', dirt, 0.6, clamp=True), col,
                (0.0095, 0.0085, 0.0076))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('ADD', 0.90, g.math('MULTIPLY', g.math('SUBTRACT', nap, 0.5), 0.08)))
    g.set(b, "Sheen Weight", 0.06)
    g.set(b, "Specular IOR Level", 0.15)
    h = g.math('ADD', g.math('MULTIPLY', cell, 0.9), g.math('MULTIPLY', fine, 0.5))
    h = g.math('ADD', h, g.math('MULTIPLY', nap, 0.35))
    g.set(b, "Normal", g.bump(h, 0.40, 0.0011))
    return m


def mat_rubber():
    """Drink tube, helmet edge beading, visor gasket, boot sole rand."""
    m, g, b, out = _new_mat("Rubber")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    grain = g.noise(g.vmath('MULTIPLY', p, (720.0, 720.0, 720.0)), scale=1.0,
                    detail=6.0, rough=0.62)
    mould = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=280.0,
                   dist=1.4, detail=3.0, band='Y', prof='SIN')
    bloom = g.voro(g.vmath('MULTIPLY', p, (250.0, 250.0, 250.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1', smooth=0.4)
    col = g.mix(g.math('MULTIPLY', grain, 0.30), base, lift(g, base, 1.48))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', bloom, fade), 0.60), col,
                lift(g, base, 2.60))
    col = g.mix(g.math('MULTIPLY', dirt, 0.6, clamp=True), col,
                (0.0090, 0.0082, 0.0072))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('SUBTRACT', g.math('ADD', 0.72, g.math('MULTIPLY', bloom, 0.14)),
                 g.math('MULTIPLY', abr, 0.22)))
    g.set(b, "Specular IOR Level", 0.42)
    h = g.math('ADD', g.math('MULTIPLY', grain, 0.7),
               g.math('MULTIPLY', g.math('MULTIPLY', mould, panel), 0.8))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 1.1))
    g.set(b, "Normal", g.bump(h, 0.26, 0.0009))
    return m


def mat_emb():
    """Satin-stitch embroidery on the badges and the number panel.

    A satin stitch is a bundle of parallel rayon filaments laid at 0.45 mm
    pitch across the shape, and it is GLOSSY — that is why an embroidered badge
    catches light where the Nomex around it does not.  The stitch direction here
    follows the metre-UV, so a badge sewn across the chest and one sewn down the
    sleeve do not shine at the same time.
    """
    m, g, b, out = _new_mat("Embroidery")
    base, aux, wear, liv, p, uv = _common(g)
    seam, sheen, panel, uid = aux(0), aux(1), aux(2), aux(3)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    stitch = g.wave(_uvxy(g, uv, 2220.0, 0.0), scale=1.0, dist=0.2, detail=2.0,
                    band='X', prof='SIN')
    fil = g.noise(_uvxy(g, uv, 6000.0, 400.0), scale=1.0, detail=4.0,
                  rough=0.55, dim='2D')
    fray = g.voro(g.vmath('MULTIPLY', p, (2600.0, 2600.0, 2600.0)), scale=1.0,
                  rand=1.0, feature='F1')
    col = g.mix(g.math('MULTIPLY', fil, 0.30), base, lift(g, base, 1.45))
    col = g.mix(g.math('MULTIPLY', dirt, 0.5, clamp=True), col,
                (0.0125, 0.0110, 0.0100))
    g.set(b, "Base Color", col)
    g.set(b, "Roughness",
          g.math('SUBTRACT', g.math('ADD', 0.36, g.math('MULTIPLY', fil, 0.16)),
                 g.math('MULTIPLY', sheen, 0.12)))
    g.set(b, "Sheen Weight", 0.20)
    g.set(b, "Sheen Roughness", 0.20)
    g.set(b, "Sheen Tint", lift(g, base, 2.4))
    g.set(b, "Specular IOR Level", 0.55)
    g.set(b, "Anisotropic", 0.55)
    h = g.math('ADD', g.math('MULTIPLY', stitch, 1.0), g.math('MULTIPLY', fil, 0.3))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('SUBTRACT', fray, 0.8), 0.9))
    g.set(b, "Normal", g.bump(h, 0.45, 0.0006))
    return m


def mat_silicone():
    """Custom-moulded earpiece and the drink-tube bite valve.

    Translucent: a 6 mm lump of medical silicone in an ear glows at the rim in
    raking sun, which is the only reason it reads at all under a helmet.
    """
    m, g, b, out = _new_mat("Silicone")
    base, aux, wear, liv, p, uv = _common(g)
    abr, dirt, oil, fade = wear(0), wear(1), wear(2), wear(3)
    orange = g.noise(g.vmath('MULTIPLY', p, (600.0, 600.0, 600.0)), scale=1.0,
                     detail=5.0, rough=0.5)
    bub = g.voro(g.vmath('MULTIPLY', p, (2100.0, 2100.0, 2100.0)), scale=1.0,
                 rand=1.0, feature='F1')
    bm = g.ramp(bub, [(0.90, (0, 0, 0)), (1.0, (1, 1, 1))])
    g.set(b, "Base Color", base)
    g.set(b, "Roughness", g.math('ADD', 0.30, g.math('MULTIPLY', orange, 0.14)))
    g.set(b, "Subsurface Weight", 0.55)
    g.set(b, "Subsurface Scale", 0.006)
    g.set(b, "Specular IOR Level", 0.5)
    h = g.math('ADD', g.math('MULTIPLY', orange, 0.6), g.math('MULTIPLY', bm, 0.8))
    g.set(b, "Normal", g.bump(h, 0.18, 0.0006))
    return m


_MAT_FN = [mat_nomex, mat_knit, mat_leather, mat_grip, mat_paint, mat_visor,
           mat_tearoff, mat_carbon, mat_webbing, mat_hardware, mat_foam,
           mat_rubber, mat_emb, mat_silicone]


def materials():
    """Idempotent.  -> list in MAT_* slot order."""
    if MATS.get("_built"):
        return [MATS[n] for n in MAT_NAMES]
    for nm, fn in zip(MAT_NAMES, _MAT_FN):
        MATS[nm] = fn()
    MATS["_built"] = True
    return [MATS[n] for n in MAT_NAMES]


# --------------------------------------------------------------------------- #
#  6.  the brand book — REUSED verbatim from build_dressing, never extended     #
# --------------------------------------------------------------------------- #
#
# Law 2: "No real sponsor names, no real team liveries.  31 invented brands
# already exist in build_dressing's brand book and 12 are shared with
# build_architecture - reuse them."  These eight are lifted character for
# character and colour for colour out of build_dressing.BRANDS.  Nothing here
# invents a 32nd.

BRANDS = {
    "MERIDIAN":        ('#111114', '#f4c518', "PNEUMATIQUES"),
    "ARDENT":          ('#e0561a', '#191512', "CARBURANTS"),
    "VOLTAIC":         ('#101014', '#d9f23a', "CHARGE"),
    "ALTIS":           ('#0b5d63', '#f0fbfa', "AVIATION"),
    "CALIBRE":         ('#232628', '#e46a1f', "OUTILLAGE"),
    "OBSIDIAN":        ('#0c0c0e', '#f2f2f2', "GESTION"),
    "LUMIERE":         ('#d8a417', '#241d10', "ENERGIE"),
    "CIRCUIT VITRINE": ('#26292d', '#f5f5f2', "LE CIRCUIT"),
}

# The driver's own helmet design.  A helmet livery is a PERSONAL design, not a
# sponsor board, so it is built from the world's palette rather than from a
# brand mark: LUMIERE's amber, ARDENT's orange, SABLIER's bone.
LIVERY = {
    "shell":   '#12161c',    # graphite base
    "crown":   '#0a0d11',    # near-black over the crown
    "sweep":   '#d8a417',    # LUMIERE amber, the big sweep
    "chevron": '#eef0ee',    # bone white, the forward chevron
    "accent":  '#e0561a',    # ARDENT orange, the brow accent
    "pin":     '#e8dcc0',    # SABLIER bone, the 1.6 mm separating pinstripe
}
SUIT_COL = {
    "shell":   '#1b2230',       # graphite-navy body
    "panel":   '#232932',
    "amber":   '#c9971a',       # LUMIERE amber, the shoulder and upper-arm panel
    "bone":    '#d7dad3',       # SABLIER bone, the 40 mm divider
    "accent":  '#d8a417',
    "collar":  '#0d1015',
    "cuff":    '#1b2029',
}


def suit_livery(t, uid=0, sleeve=False):
    """Per-vertex panel colour, keyed on the garment's own t.

    "Only the shoulders, upper arms and the top of the chest are ever visible
     above the cockpit rim - build for that framing."   -- the manifest.

    So that is exactly where the livery is: an amber yoke over both shoulders
    and the top third of each sleeve, split from the graphite body by a 40 mm
    bone divider.  Below the cockpit rim the suit is plain, because nothing
    down there is ever seen and a busy pattern there would only cost render
    time.  The amber and the bone are the SAME two colours as the helmet's
    sweep and pinstripe, which is what makes a driver read as one design
    rather than as a helmet and a separate garment.
    """
    t = np.asarray(t, float)
    shell = np.array(srgb(SUIT_COL["shell"]))
    amber = np.array(srgb(SUIT_COL["amber"]))
    bone = np.array(srgb(SUIT_COL["bone"]))
    if sleeve:
        k_amber = 1.0 - sstep(0.205, 0.240, t)
        k_bone = sstep(0.205, 0.240, t) * (1.0 - sstep(0.268, 0.300, t))
    else:
        k_amber = sstep(0.878, 0.900, t)
        k_bone = sstep(0.838, 0.856, t) * (1.0 - sstep(0.878, 0.900, t))
    k_shell = np.clip(1.0 - k_amber - k_bone, 0.0, 1.0)
    C = (shell.reshape(1, 3) * k_shell.reshape(-1, 1)
         + amber.reshape(1, 3) * k_amber.reshape(-1, 1)
         + bone.reshape(1, 3) * k_bone.reshape(-1, 1))
    return np.concatenate([C, np.full((len(C), 1), hash01(uid, "dye"))], 1)


def brand_palette():
    return {k: srgb(v) for k, v in LIVERY.items()}


# --------------------------------------------------------------------------- #
#  7.  type — glyph outlines baked from Blender's bundled vector font           #
#                                                                               #
#  Not an image.  ``bpy.data.curves`` of type FONT tessellates to a polygon at  #
#  whatever resolution is asked for, and the result is a real triangle mesh, so #
#  a wordmark on a helmet or a badge is GEOMETRY and its edges are as sharp as  #
#  the lens.  A 5 mm letter stroke is 3.7 screen pixels at 3 m and there is no  #
#  resolution at which a raster would have been acceptable.                     #
# --------------------------------------------------------------------------- #

_GLYPH = {}
_CAPH = [None]


def _bake_glyph(ch, res=6):
    cu = bpy.data.curves.new("_drv_glyph", 'FONT')
    cu.body = ch
    cu.size = 1.0
    cu.extrude = 0.0
    cu.align_x = 'LEFT'
    cu.align_y = 'TOP_BASELINE'
    cu.resolution_u = res
    ob = bpy.data.objects.new("_drv_glyph", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.zeros((0, 2)); F = np.zeros((0, 3), int)
    if me is not None and len(me.vertices):
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        me.calc_loop_triangles()
        if len(me.loop_triangles):
            tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
            me.loop_triangles.foreach_get("vertices", tri)
            F = tri.reshape(-1, 3).astype(np.int64)
            V = co[:, :2].copy()
    ev.to_mesh_clear()
    bpy.context.scene.collection.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return V, F


def glyph(ch):
    if _CAPH[0] is None:
        V, _F = _bake_glyph("H")
        _CAPH[0] = float(V[:, 1].max()) if len(V) else 0.7
    if ch in _GLYPH:
        return _GLYPH[ch]
    if ch == " ":
        out = (np.zeros((0, 2)), np.zeros((0, 3), int), 0.30)
        _GLYPH[ch] = out
        return out
    V, F = _bake_glyph(ch)
    k = 1.0 / max(_CAPH[0], 1e-6)
    if len(V):
        V = V * k
        V[:, 0] -= V[:, 0].min()
        adv = float(V[:, 0].max())
    else:
        adv = 0.30
    out = (V, F, adv)
    _GLYPH[ch] = out
    return out


def text_poly(body, tracking=0.12):
    """-> verts (N,2) in cap-heights, tris (M,3), total width in cap-heights."""
    VS, FS, x, n0 = [], [], 0.0, 0
    for ch in body:
        V, F, adv = glyph(ch)
        if len(V):
            VS.append(V + np.array([x, 0.0]))
            FS.append(F + n0)
            n0 += len(V)
        x += adv + (tracking if ch != " " else 0.0)
    x = max(0.0, x - tracking)
    return (np.concatenate(VS) if VS else np.zeros((0, 2)),
            np.concatenate(FS) if FS else np.zeros((0, 3), int), x)


# --------------------------------------------------------------------------- #
#  8.  anthropometry                                                            #
# --------------------------------------------------------------------------- #

class Anthro:
    """Segment lengths and breadths for a race-fit male driver.

    Fractions of stature are the Dempster / NASA-STD-3000 values; the girths are
    the 40th-percentile athletic male, narrowed 4 % at the waist and widened 3 %
    at the shoulder, which is what a driver's body composition actually does.
    A driver is SMALL: the FIA minimum is 80 kg including the seat, and the
    grid clusters at 1.72-1.82 m.
    """

    __slots__ = ("H", "name",
                 "head_len", "head_br", "head_dep", "head_r",
                 "neck_r", "neck_len",
                 "trunk", "sh_half", "sh_drop", "sh_fwd",
                 "chest_hw", "chest_hd", "waist_hw", "waist_hd",
                 "hip_hw", "hip_hd", "hip_sep",
                 "upper_arm", "forearm", "hand_len", "hand_br", "hand_th",
                 "r_delt", "r_biceps", "r_elbow", "r_fore", "r_wrist",
                 "thigh", "shank", "foot_len", "foot_br",
                 "r_thigh", "r_knee", "r_calf", "r_ankle",
                 "fing_len", "fing_r", "thumb")

    def __init__(self, stature=1.780, name="driver"):
        H = float(stature)
        self.H, self.name = H, name
        self.head_len = 0.1300 * H          # chin to vertex   0.2314
        self.head_br = 0.0855 * H           # bitragion        0.1522
        self.head_dep = 0.1100 * H          # glabella-occiput 0.1958
        self.head_r = 0.0505 * H            # mean skull radius
        self.neck_r = 0.0330 * H            # 0.0587
        self.neck_len = 0.0590 * H          # C7 to head base
        self.trunk = 0.2500 * H             # H-point to C7 along the spine 0.445
        self.sh_half = 0.1080 * H           # glenohumeral half-separation 0.1922
        self.sh_drop = 0.030                # shoulder joint below C7
        self.sh_fwd = 0.040                 # and forward of it
        self.chest_hw = 0.0885 * H          # 0.1575
        self.chest_hd = 0.0625 * H          # 0.1113
        self.waist_hw = 0.0790 * H          # 0.1406
        self.waist_hd = 0.0545 * H
        self.hip_hw = 0.0925 * H            # 0.1647
        self.hip_hd = 0.0620 * H
        self.hip_sep = 0.0480 * H           # +-0.0854
        self.upper_arm = 0.1830 * H         # 0.3257
        self.forearm = 0.1450 * H           # 0.2581
        self.hand_len = 0.1080 * H          # 0.1922
        self.hand_br = 0.0500 * H           # 0.0890
        self.hand_th = 0.0165 * H           # 0.0294
        self.r_delt = 0.0300 * H
        self.r_biceps = 0.0268 * H
        self.r_elbow = 0.0250 * H
        self.r_fore = 0.0252 * H
        self.r_wrist = 0.0163 * H
        self.thigh = 0.2420 * H             # 0.4308
        self.shank = 0.2420 * H
        self.foot_len = 0.1520 * H          # 0.2706
        self.foot_br = 0.0550 * H
        self.r_thigh = 0.0500 * H
        self.r_knee = 0.0345 * H
        self.r_calf = 0.0350 * H
        self.r_ankle = 0.0205 * H
        # digits: MCP -> tip, as a fraction of hand length
        self.fing_len = {"i": 0.390, "m": 0.430, "r": 0.400, "l": 0.315}
        self.fing_r = {"i": 0.0107, "m": 0.0109, "r": 0.0101, "l": 0.0090}
        self.thumb = (0.046, 0.033, 0.027, 0.0128)   # mc, prox, dist, radius


DRIVER = Anthro(1.780, "driver")


# --------------------------------------------------------------------------- #
#  9.  frames                                                                   #
# --------------------------------------------------------------------------- #

class Frame:
    __slots__ = ("o", "x", "y", "z", "r", "name")

    def __init__(self, o, x, y, z, r=0.05, name=""):
        self.o = np.asarray(o, float)
        self.x = unit(np.asarray(x, float))
        self.z = unit(np.asarray(z, float))
        self.y = unit(np.cross(self.z, self.x))
        self.x = np.cross(self.y, self.z)
        self.r = float(r)
        self.name = name

    @classmethod
    def from_cols(cls, o, M, r=0.05, name=""):
        return cls(o, M[:, 0], M[:, 1], M[:, 2], r, name)

    def M(self):
        return np.stack([self.x, self.y, self.z], 1)

    def mat4(self):
        m = np.eye(4)
        m[:3, :3] = self.M()
        m[:3, 3] = self.o
        return m

    def local(self, p):
        return self.o + self.M() @ np.asarray(p, float)

    def __repr__(self):
        return (f"<Frame {self.name} o=({self.o[0]:.3f},{self.o[1]:.3f},"
                f"{self.o[2]:.3f}) r={self.r:.3f}>")


# --------------------------------------------------------------------------- #
# 10.  the pose, and what the driver is DOING                                   #
# --------------------------------------------------------------------------- #

# How the neck answers the chassis.  Measured behaviour, not invention:
#   * a driver's head does NOT roll with the car.  He keeps his eyes level and
#     the neck absorbs most of the chassis roll.
#   * what he cannot resist is the lateral g, which pulls the 6.5 kg of head
#     plus helmet outboard.  About 2.6 deg per g is what is left after the neck
#     and the HANS have done their work.
#   * and he LEADS the corner: the head is already pointed at the apex before
#     the car is.
NECK_ROLL_FOLLOW = 0.22          # fraction of chassis roll the head keeps
NECK_LOAD_LEAN = 2.60            # deg of outboard head lean per g
NECK_LOAD_SHIFT = 0.0042         # m of outboard head translation per g
STEER_LEAD = 0.34                # head yaw as a fraction of wheel angle
STEER_LEAD_MAX = 19.0            # deg
TRUNK_LOAD_BEND = 1.35           # deg of trunk lateral bend per g
TRUNK_LOAD_SHIFT = 0.0060        # m the harness still allows, per g


class DriverPose:
    """Everything that decides the figure.  Copy it and change one field."""

    __slots__ = ("name", "recline_deg", "pelvis_tilt_deg",
                 "steer_deg", "lat_g", "long_g", "chassis_roll_deg",
                 "throttle", "brake", "head_pitch_deg", "head_yaw_bias_deg",
                 "harness_tension", "grip_l", "grip_r", "note")

    def __init__(self, name, recline_deg=36.0, pelvis_tilt_deg=9.0,
                 steer_deg=0.0, lat_g=0.0, long_g=0.0, chassis_roll_deg=0.0,
                 throttle=0.0, brake=0.0, head_pitch_deg=-3.0,
                 head_yaw_bias_deg=0.0, harness_tension=1.0,
                 grip_l=1.0, grip_r=1.0, note=""):
        self.name = name
        self.recline_deg = recline_deg
        self.pelvis_tilt_deg = pelvis_tilt_deg
        self.steer_deg = steer_deg
        self.lat_g = lat_g
        self.long_g = long_g
        self.chassis_roll_deg = chassis_roll_deg
        self.throttle = throttle
        self.brake = brake
        self.head_pitch_deg = head_pitch_deg
        self.head_yaw_bias_deg = head_yaw_bias_deg
        self.harness_tension = harness_tension
        self.grip_l = grip_l                 # 1 = closed on the bar, 0 = open
        self.grip_r = grip_r
        self.note = note

    def copy(self, name=None, **kw):
        p = DriverPose(name or self.name)
        for s in self.__slots__:
            setattr(p, s, getattr(self, s))
        if name:
            p.name = name
        for k, v in kw.items():
            setattr(p, k, v)
        return p


POSES = {
    # THE SHOT.  T4 hairpin, s = 939-1025, the camera on the inside kerb at
    # z = +0.85 on a 21 mm lens.  The car is mid-rotation: full lock on, 2.9 g
    # of lateral load, the chassis rolled 2.4 deg onto its outside corner, and
    # the driver already looking at the exit.
    "hairpin_apex": DriverPose(
        "hairpin_apex", recline_deg=36.0, pelvis_tilt_deg=9.0,
        steer_deg=62.0, lat_g=2.90, long_g=-0.35, chassis_roll_deg=2.4,
        throttle=0.22, brake=0.0, head_pitch_deg=-2.5, head_yaw_bias_deg=4.0,
        harness_tension=1.0, grip_l=1.0, grip_r=1.0,
        note="the frame the manifest names"),
    "straight": DriverPose(
        "straight", steer_deg=2.0, lat_g=0.10, long_g=1.30,
        chassis_roll_deg=0.1, throttle=1.0, head_pitch_deg=-1.5,
        note="the onboard follow down the pit straight"),
    "braking": DriverPose(
        "braking", steer_deg=-4.0, lat_g=-0.15, long_g=-4.60,
        chassis_roll_deg=-0.2, brake=1.0, head_pitch_deg=1.5,
        harness_tension=1.25, note="5 g stop; the harness is doing the work"),
    "exit": DriverPose(
        "exit", steer_deg=-24.0, lat_g=-1.80, long_g=1.10,
        chassis_roll_deg=-1.6, throttle=0.85, head_pitch_deg=-3.5,
        note="unwinding onto the throttle"),
    "grid_idle": DriverPose(
        "grid_idle", recline_deg=37.5, steer_deg=0.0, lat_g=0.0,
        chassis_roll_deg=0.0, head_pitch_deg=2.0, harness_tension=0.80,
        note="stationary, harness slack, hands resting"),
    "hands_off": DriverPose(
        "hands_off", steer_deg=0.0, grip_l=0.0, grip_r=0.0,
        head_pitch_deg=0.0, harness_tension=0.9,
        note="both hands off the wheel - for the pit-stop shots"),
}


# --------------------------------------------------------------------------- #
# 11.  the cockpit package this figure needs                                    #
# --------------------------------------------------------------------------- #
#
# Published as data because four dependants and at least one car agent need it
# and cannot ask.  All of it in the DRIVER FRAME (origin = H-point).

WHEEL_C = np.array([0.300, 0.0, 0.393])   # steering wheel centre
WHEEL_TILT_DEG = 25.0                     # top of the wheel leans toward driver
WHEEL_GRIP_OFF = 0.112                    # grip bar centre, off the wheel axis
WHEEL_GRIP_LEN = 0.133                    # bar length  (round 1: SW_GripL 0.133)
WHEEL_GRIP_A = 0.0221                     # bar semi-axis across  (44.2 mm)
WHEEL_GRIP_B = 0.0175                     # bar semi-axis through (35.0 mm)
PEDAL_ANKLE = np.array([0.755, 0.075, 0.215])   # ankle joint at the pedal

PACKAGE = {
    "frame": "origin = H-point (hip joint centre); +X forward; +Y driver left; "
             "+Z up",
    "stature_m": DRIVER.H,
    "recline_deg_from_vertical": 36.0,
    "hip_to_c7_m": DRIVER.trunk,
    "hip_to_head_centre_rise_m": 0.552,
    "hip_to_helmet_crown_m": 0.697,
    "hip_to_ankle_m": float(np.linalg.norm(PEDAL_ANKLE)),
    "hip_to_toe_x_m": 0.905,
    "shoulder_half_separation_m": DRIVER.sh_half,
    "shoulder_outer_half_width_m": 0.246,
    "wheel_centre_m": WHEEL_C.tolist(),
    "shoulder_yaw_per_steer_deg": 0.20,
    "wheel_tilt_deg": WHEEL_TILT_DEG,
    "grip_offset_m": WHEEL_GRIP_OFF,
    "cockpit_rim_above_hip_m": 0.335,
    "knee_apex_above_hip_m": 0.150,
    # ---- the reconciliation with round 1's car, stated as numbers ----------
    "round1_note": (
        "Round 1's CI_* cockpit interior (docs/inventory_iter.json; the car's "
        "contact plane is z = 0.340 because the showroom car stands on a dais) "
        "is LONGITUDINALLY right and VERTICALLY compressed.  Its interior tub "
        "spans z 0.710-1.070, a usable depth of 0.360 m, and its seat pan low "
        "point (0.749) to headrest centre (0.998) is 0.249 m of hip-to-head "
        "rise.  This figure needs 0.552 m.  Put the H-point at CAR_ROOT "
        "(0.200, 0.000, 0.520) and the feet land exactly in CI_pedals "
        "(ankle 0.955, 0.735 vs pedals x 0.870-1.078, z 0.678-0.849) and the "
        "helmet crown at 1.217 sits just under MB_chassis_cockpit's 1.271 - "
        "but the seat pan must then drop 0.23 m and SW_* must move 0.155 m aft "
        "and 0.154 m up.  NOT FIXED HERE: this module builds its own proxy and "
        "publishes the numbers rather than shrinking the driver to a 1.32 m "
        "child to fit a decorative tub."),
    "round1_h_point_recommendation": [0.200, 0.000, 0.520],
    "round1_wheel_delta_m": [-0.155, 0.0, 0.154],
}


# --------------------------------------------------------------------------- #
# 12.  the skeleton                                                             #
# --------------------------------------------------------------------------- #

SPINE = [("pelvis", 0.000), ("l5", 0.085), ("t12", 0.185), ("t8", 0.290),
         ("t4", 0.385), ("c7", 0.445)]


def ik2(S, W, l1, l2, pole):
    """Two-bone IK.  -> elbow/knee position.  Never returns NaN."""
    S = np.asarray(S, float); W = np.asarray(W, float)
    d = W - S
    L = float(np.linalg.norm(d))
    reach = (l1 + l2) * 0.9985
    if L > reach:
        d = d * (reach / max(L, 1e-9))
        W = S + d
        L = reach
    L = max(L, abs(l1 - l2) * 1.0015, 1e-6)
    a = (l1 * l1 - l2 * l2 + L * L) / (2.0 * L)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    n = d / L
    p = np.asarray(pole, float)
    p = p - n * float(np.dot(p, n))
    nn = np.linalg.norm(p)
    p = p / nn if nn > 1e-9 else np.cross(n, (0, 0, 1.0))
    return S + n * a + unit(p) * h, W


class Skeleton:
    """Solved joint positions and frames, in the DRIVER FRAME."""

    def __init__(self, pose, an=DRIVER):
        self.pose = pose
        self.an = an
        self.J = {}
        self.F = {}
        self._solve()

    # -- helpers -----------------------------------------------------------
    def _put(self, name, o, x, z, r=0.05):
        self.J[name] = np.asarray(o, float)
        self.F[name] = Frame(o, x, None, z, r, name).M()

    def _solve(self):
        an, po = self.an, self.pose
        rec = math.radians(po.recline_deg)
        latb = math.radians(po.lat_g * TRUNK_LOAD_BEND)
        # --- spine ---------------------------------------------------------
        # trunk axis leans BACK by `recline` about the driver's +Y (left) axis,
        # with a real lumbar lordosis and thoracic kyphosis on top of it, and a
        # lateral bend proportional to the load the harness has not taken.
        up = np.array([0.0, 0.0, 1.0])
        prev = np.zeros(3)
        self.J["pelvis"] = prev.copy()
        segs = []
        for i in range(1, len(SPINE)):
            nm, s = SPINE[i]
            s0 = SPINE[i - 1][1]
            ds = s - s0
            t = s / an.trunk
            # lordosis pulls the lower spine forward, kyphosis the upper back
            curve = (0.115 * math.sin(math.pi * min(t / 0.45, 1.0))
                     - 0.085 * math.sin(math.pi * max(t - 0.45, 0.0) / 0.55))
            ang = rec + curve
            d = np.array([-math.sin(ang), 0.0, math.cos(ang)])
            d = rz(latb * t) @ d
            d = d + np.array([0.0, -math.sin(latb * t) * 0.55, 0.0])
            d = unit(d)
            prev = prev + d * ds
            self.J[nm] = prev.copy()
            segs.append((nm, d))
        # spine frames: z along the segment, x forward
        for nm, d in segs:
            fwd = unit(np.cross(np.array([0.0, 1.0, 0.0]), d))
            self._put(nm, self.J[nm], fwd, d, 0.10)
        self._put("pelvis", self.J["pelvis"],
                  unit(np.array([math.cos(math.radians(po.pelvis_tilt_deg)), 0.0,
                                 math.sin(math.radians(po.pelvis_tilt_deg))])),
                  segs[0][1], an.hip_hw)

        c7 = self.J["c7"]
        tz = segs[-1][1]
        tx = unit(np.cross(np.array([0.0, 1.0, 0.0]), tz))
        ty = np.cross(tz, tx)

        # --- shoulders ------------------------------------------------------
        # A DRIVER TURNS HIS SHOULDERS INTO THE LOCK.  Without it the outside
        # arm simply cannot reach: at 62 deg of wheel the right wrist came out
        # 0.583 m from the right shoulder against an arm of 0.584 m, the IK
        # clamped, and the hand ended up 12 mm off its own grip with the elbow
        # locked straight.  Measured on the solved skeleton, not guessed.
        # 0.20 of the wheel angle puts the outboard shoulder 37 mm forward,
        # which is most of what the reach was short by.
        shoulder_yaw = math.radians(0.20 * po.steer_deg)
        Ryaw = rotmat(tz, shoulder_yaw)
        shift = po.lat_g * TRUNK_LOAD_SHIFT / max(po.harness_tension, 0.35)
        for sd, s in (("l", +1.0), ("r", -1.0)):
            tyr = Ryaw @ ty
            cl = c7 + tyr * (s * an.sh_half * 0.42) + tz * 0.012
            sh = (c7 + tyr * (s * an.sh_half) - tz * an.sh_drop
                  + tx * an.sh_fwd - ty * shift)
            self._put("clav_" + sd, cl, tx, ty * s, 0.020)
            self._put("sh_" + sd, sh, tx, tz, an.r_delt)

        # --- the wheel, and the grips -------------------------------------
        wt = math.radians(-WHEEL_TILT_DEG)
        Wn = ry(wt) @ np.array([1.0, 0.0, 0.0])       # wheel face normal
        Wu = ry(wt) @ np.array([0.0, 0.0, 1.0])       # "up" in the wheel plane
        Ws = np.cross(Wu, Wn)                          # "left" in the plane
        st = math.radians(po.steer_deg)
        R = rotmat(Wn, st)
        Wu, Ws = R @ Wu, R @ Ws
        self.wheel = Frame(WHEEL_C, Wn, None, Wu, 0.140, "wheel")
        self.wheel_side = Ws
        self.grip = {}
        for sd, s in (("l", +1.0), ("r", -1.0)):
            gc = WHEEL_C + Ws * (s * WHEEL_GRIP_OFF)
            # the bar axis: the wheel's own "up", canted 7 deg inward at the top
            ax = unit(Wu - Ws * (s * math.tan(math.radians(7.0))))
            self.grip[sd] = Frame(gc, Wn, None, ax, WHEEL_GRIP_A, "grip_" + sd)

        # --- arms: IK onto the grips ---------------------------------------
        for sd, s in (("l", +1.0), ("r", -1.0)):
            G = self.grip[sd]
            hold = po.grip_l if sd == "l" else po.grip_r
            # WHERE THE WRIST GOES, AND WHY.  A hand closed on a vertical bar
            # has its long axis PERPENDICULAR to that bar: the knuckles are
            # across the bar from the wrist, not above it.  The first cut put
            # the wrist 85 mm straight back along the wheel normal, which made
            # the palm's long axis point AT the bar -- so the bar passed
            # straight through the palm and the fingers wrapped a circle 30 mm
            # away from anything.  In the inspection render the wheel rim went
            # through the hand.
            #
            # The rule, and build_glove() derives the identical frame from it:
            #     palm normal  = +G.x  (out of the palm, at the bar)
            #     hand axis    = inboard, so the wrist sits OUTBOARD of the bar
            #     stack axis   = G.z   (the bar; four fingers stack along it)
            W = (G.o + G.y * (s * (an.hand_len * 0.49))
                 - G.x * (WHEEL_GRIP_B + 0.0165) - G.z * 0.010)
            if hold < 0.5:
                W = self.J["sh_" + sd] + np.array([0.16, s * 0.06, -0.16])
            S = self.J["sh_" + sd]
            pole = unit(np.array([-0.25, s * 0.86, -0.44]))
            E, W = ik2(S, W, an.upper_arm, an.forearm, pole)
            self.J["el_" + sd] = E
            self.J["wr_" + sd] = W
            ua = unit(E - S)
            fa = unit(W - E)
            # upper arm frame: z down the bone, x forward-ish
            self._put("sh_" + sd, S, unit(np.cross(np.array([0.0, s, 0.0]), ua)),
                      ua, an.r_delt)
            self._put("el_" + sd, E, unit(np.cross(np.cross(ua, fa), fa)), fa,
                      an.r_elbow)
            # wrist frame: z along the grip bar (the hand is closed on it),
            # x out of the back of the hand
            if hold >= 0.5:
                self._put("wr_" + sd, W, G.x, G.z, an.r_wrist)
            else:
                self._put("wr_" + sd, W, unit(np.cross(np.array([0, s, 0]), fa)),
                          fa, an.r_wrist)

        # --- legs: IK onto the pedals --------------------------------------
        for sd, s in (("l", +1.0), ("r", -1.0)):
            hip = np.array([0.0, s * an.hip_sep, 0.0])
            self.J["hip_" + sd] = hip
            ped = PEDAL_ANKLE * np.array([1.0, s, 1.0])
            # the throttle foot is further forward on its pedal than the brake
            ap = po.throttle if sd == "r" else po.brake
            ped = ped + np.array([0.012 * ap, 0.0, -0.010 * ap])
            pole = unit(np.array([0.30, s * 0.62, 0.72]))
            K, A = ik2(hip, ped, an.thigh, an.shank, pole)
            self.J["kn_" + sd] = K
            self.J["ank_" + sd] = A
            th = unit(K - hip); sh_ = unit(A - K)
            self._put("hip_" + sd, hip,
                      unit(np.cross(np.array([0.0, s, 0.0]), th)), th, an.r_thigh)
            self._put("kn_" + sd, K, unit(np.cross(np.cross(th, sh_), sh_)), sh_,
                      an.r_knee)
            # the foot: sole plane roughly normal to the pedal face
            fdir = unit(np.array([0.62, s * 0.06, 0.78]))
            self._put("ank_" + sd, A, np.array([0.0, s, 0.0]), fdir, an.r_ankle)
            self.J["ball_" + sd] = A + fdir * (an.foot_len * 0.62)
            self.J["toe_" + sd] = A + fdir * (an.foot_len * 0.92)

        # --- head: the manifest's requirement, implemented -------------------
        self.head_roll_deg, self.head_yaw_deg, self.head_pitch_deg = \
            head_solve(po)
        neck_base = c7 + tz * 0.028 + tx * 0.030
        Hm = (rz(math.radians(self.head_yaw_deg))
              @ rotmat(np.array([0.0, 1.0, 0.0]), math.radians(-self.head_pitch_deg))
              @ rx(math.radians(self.head_roll_deg)))
        hx, hy, hz = Hm[:, 0], Hm[:, 1], Hm[:, 2]
        lat_shift = -po.lat_g * NECK_LOAD_SHIFT
        head_c = (neck_base + hz * (an.neck_len + an.head_r * 0.62)
                  + hx * 0.012 + np.array([0.0, lat_shift, 0.0]))
        self.J["neck"] = neck_base
        self._put("neck", neck_base, tx, unit(head_c - neck_base), an.neck_r)
        self.J["head"] = head_c
        self._put("head", head_c, hx, hz, an.head_r)

    def chain(self, names):
        return np.array([self.J[n] for n in names])


def head_solve(po):
    """-> (roll_deg, yaw_deg, pitch_deg) in the driver frame.

    "The head must move: it stays level under lateral load while the car rolls,
     and it leads the steering into an apex.  A rigidly bolted head is worse
     than no driver."   -- the manifest, verbatim.

    Positive roll tilts the crown toward the driver's RIGHT.  Positive lat_g is
    an acceleration toward his LEFT (a left-hand corner), which throws the head
    right, so the two signs agree.  Positive steer is left lock.
    """
    roll = (po.chassis_roll_deg * NECK_ROLL_FOLLOW
            + po.lat_g * NECK_LOAD_LEAN)
    yaw = max(-STEER_LEAD_MAX, min(STEER_LEAD_MAX, po.steer_deg * STEER_LEAD))
    yaw += po.head_yaw_bias_deg
    pitch = po.head_pitch_deg - po.long_g * 0.45
    return roll, yaw, pitch


def solve(pose="hairpin_apex", an=DRIVER):
    if isinstance(pose, str):
        pose = POSES[pose]
    return Skeleton(pose, an)


def seat_matrix(hpoint_world, heading_deg=0.0, extra=None):
    """4x4 that puts the DRIVER FRAME into a world (or car) frame."""
    M = np.eye(4)
    M[:3, :3] = rz(math.radians(heading_deg))
    M[:3, 3] = np.asarray(hpoint_world, float)
    if extra is not None:
        M = np.asarray(extra, float) @ M
    return M


# --------------------------------------------------------------------------- #
# 13.  the body as SECTION DATA — the interface the garment agents need         #
#                                                                               #
#  This module never emits skin.  The manifest is explicit: "every one of them  #
#  is covered, so no skin and no face are needed."  What a garment builder      #
#  actually needs is not a body mesh, it is the SECTIONS: where the surface is, #
#  how wide, how deep, how boxy, and which way is up.  So that is what is       #
#  published, and every garment in this file is lofted from it.                 #
# --------------------------------------------------------------------------- #

def axes_along(P, left_hint=(0.0, 1.0, 0.0)):
    """-> T (tangent), L (left), F (forward), each (S,3), non-twisting."""
    P = np.asarray(P, float)
    S = len(P)
    T = np.zeros((S, 3))
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T = unit(T)
    L = np.zeros((S, 3))
    l0 = np.asarray(left_hint, float)
    l0 = l0 - T[0] * float(np.dot(l0, T[0]))
    if np.linalg.norm(l0) < 1e-7:
        l0 = np.cross(T[0], (1.0, 0.0, 0.0))
    L[0] = unit(l0)
    for i in range(1, S):
        a, b = T[i - 1], T[i]
        ax = np.cross(a, b)
        na = np.linalg.norm(ax)
        if na < 1e-9:
            L[i] = L[i - 1]
        else:
            L[i] = rotmat(ax / na, math.atan2(na, float(np.dot(a, b)))) @ L[i - 1]
        L[i] = unit(L[i] - b * float(np.dot(L[i], b)))
    F = np.cross(L, T)
    return T, L, F


def sect_lerp(keys, t):
    """keys = [(t, v0, v1, ...)] sorted; t array -> (len(t), nvals)."""
    K = np.asarray([k[0] for k in keys], float)
    V = np.asarray([k[1:] for k in keys], float)
    t = np.asarray(t, float)
    out = np.zeros((len(t), V.shape[1]))
    for j in range(V.shape[1]):
        out[:, j] = np.interp(t, K, V[:, j])
    return out


#  trunk profile.  t = 0 at the seat pan, 1 at the top of the shoulder yoke.
#     t,   half-width, half-depth, superellipse exp, forward offset
TRUNK_KEYS = [
    (0.00, 0.1690, 0.1240, 2.55, -0.006),   # under the seat belt line
    (0.10, 0.1655, 0.1180, 2.60, -0.002),   # iliac crest
    (0.22, 0.1470, 0.1010, 2.55,  0.004),   # waist
    (0.34, 0.1420, 0.1040, 2.70,  0.006),   # lower rib
    (0.50, 0.1520, 0.1140, 2.95,  0.004),   # mid chest
    (0.66, 0.1610, 0.1190, 3.10, -0.002),   # nipple line, pecs
    (0.80, 0.1720, 0.1140, 3.15, -0.010),   # upper chest / armpit
    (0.90, 0.1980, 0.1030, 3.00, -0.016),   # deltoid yoke
    (0.97, 0.1900, 0.0930, 2.70, -0.018),   # shoulder crest
    (1.00, 0.1560, 0.0800, 2.40, -0.014),   # neck root
]

ARM_KEYS = [                                # t = 0 shoulder, 1 wrist
    (0.00, 0.0620, 0.0605, 2.5),
    (0.10, 0.0605, 0.0575, 2.5),            # deltoid cap, the widest point
    (0.28, 0.0492, 0.0470, 2.3),
    (0.46, 0.0405, 0.0392, 2.2),            # just above the elbow
    (0.53, 0.0392, 0.0405, 2.5),            # olecranon
    (0.62, 0.0450, 0.0420, 2.3),            # forearm flexor mass
    (0.74, 0.0402, 0.0372, 2.2),
    (0.88, 0.0318, 0.0272, 2.3),
    (1.00, 0.0292, 0.0212, 2.6),            # wrist: flat, not round
]

LEG_KEYS = [
    (0.00, 0.0955, 0.0930, 2.5),
    (0.20, 0.0855, 0.0830, 2.4),
    (0.42, 0.0730, 0.0715, 2.4),
    (0.52, 0.0640, 0.0625, 2.6),            # knee
    (0.62, 0.0655, 0.0640, 2.4),            # calf head
    (0.72, 0.0610, 0.0585, 2.3),
    (0.88, 0.0450, 0.0430, 2.3),
    (1.00, 0.0378, 0.0330, 2.5),            # ankle
]


def trunk_sections(skel, S=260, pad_lo=0.155, pad_hi=0.060):
    """-> C (S,3), L (S,3), F (S,3), A (S,), B (S,), E (S,), t (S,)

    A is the HALF-WIDTH (along L, the driver's left), B the HALF-DEPTH (along
    F, forward), E the superellipse exponent.  A garment lofts against these
    and adds its own thickness; that is the whole contract.
    """
    an = skel.an
    sp = skel.chain([n for n, _ in SPINE])
    d0 = unit(sp[1] - sp[0])
    d1 = unit(sp[-1] - sp[-2])
    key = np.vstack([sp[0] - d0 * pad_lo, sp, sp[-1] + d1 * pad_hi])
    P = resample(catmull(key, S * 3), S)
    T, L, F = axes_along(P, (0.0, 1.0, 0.0))
    s = arclen(P)
    t = (s - s[0]) / max(s[-1] - s[0], 1e-9)
    K = sect_lerp(TRUNK_KEYS, t)
    A, B, E, off = K[:, 0], K[:, 1], K[:, 2], K[:, 3]
    C = P + F * off.reshape(-1, 1)
    return C, L, F, A, B, E, t


def arm_sections(skel, side, S=190):
    an = skel.an
    sd = side
    S0 = skel.J["sh_" + sd]; E0 = skel.J["el_" + sd]; W0 = skel.J["wr_" + sd]
    key = np.vstack([S0 + (S0 - E0) * 0.14, S0, E0, W0, W0 + (W0 - E0) * 0.06])
    P = resample(catmull(key, S * 3), S)
    sgn = 1.0 if sd == "l" else -1.0
    T, L, F = axes_along(P, (0.0, 0.0, -1.0) if sgn > 0 else (0.0, 0.0, -1.0))
    s = arclen(P)
    t = (s - s[0]) / max(s[-1] - s[0], 1e-9)
    K = sect_lerp(ARM_KEYS, t)
    return P, L, F, K[:, 0], K[:, 1], K[:, 2], t


def leg_sections(skel, side, S=150):
    sd = side
    H0 = skel.J["hip_" + sd]; K0 = skel.J["kn_" + sd]; A0 = skel.J["ank_" + sd]
    key = np.vstack([H0 + (H0 - K0) * 0.10, H0, K0, A0])
    P = resample(catmull(key, S * 3), S)
    T, L, F = axes_along(P, (0.0, 1.0, 0.0))
    s = arclen(P)
    t = (s - s[0]) / max(s[-1] - s[0], 1e-9)
    K = sect_lerp(LEG_KEYS, t)
    return P, L, F, K[:, 0], K[:, 1], K[:, 2], t


# --------------------------------------------------------------------------- #
# 14.  the language of cloth                                                    #
# --------------------------------------------------------------------------- #

class CLOTH:
    """Measured constants for a three-layer aramid driver's overall.

    Aramid knit is STIFFER than cotton: it buckles at a longer half-wavelength
    and it holds a crease.  Every number here is a length in metres and every
    one of them is above the 1.34 mm pixel, so every one of them is mesh.
    """
    THICK = 0.0034            # three layers, quilted
    FELL_W = 0.0092           # flat-felled seam welt width
    FELL_H = 0.00195          # and how proud it stands (1.5 screen px at 3 m)
    STITCH_W = 0.0019         # topstitch bead width
    STITCH_H = 0.00090        # and height
    STITCH_P = 0.0032         # pitch
    STITCH_GAUGE = 0.0062     # gap between the two rows of a felled seam
    BUCKLE = 0.058            # buckling half-wavelength of the shell
    CREASE_D = 0.0042         # depth of a held crease
    CREASE_W = 0.020
    MICRO = 0.00095           # amplitude of the ever-present crumple
    DRAPE = 0.0075            # how far slack cloth hangs off the form


def crest(x, sharp=1.0):
    """A soft one-sided ridge: 1 at x=0, 0 by |x|=1, with a sharp shoulder."""
    x = np.abs(np.asarray(x, float))
    v = np.clip(1.0 - x, 0.0, 1.0)
    return v ** (1.0 + 2.0 * sharp) * (3.0 - 2.0 * v) ** 0.5


def welt(d, w=CLOTH.FELL_W, h=CLOTH.FELL_H):
    """Flat-felled seam profile.  d = signed distance from the seam line."""
    d = np.asarray(d, float)
    a = np.abs(d)
    core = np.clip(1.0 - a / (w * 0.5), 0.0, 1.0)
    prof = core * core * (3.0 - 2.0 * core)
    # a felled seam is a STEP, not a symmetric ridge: one side carries the
    # folded allowance and stands proud, the other lies flat
    step = 0.5 + 0.5 * np.tanh(d / (w * 0.16))
    return h * prof * (0.55 + 0.75 * step)


def stitch_field(d, gauge=CLOTH.STITCH_GAUGE, w=CLOTH.STITCH_W,
                 h=CLOTH.STITCH_H, s=None, pitch=CLOTH.STITCH_P):
    """Two rows of topstitch either side of a seam, as a height field.

    The bead is BROKEN at the stitch pitch: real topstitch is a row of discrete
    3.2 mm stitches, and a continuous cord reads as piping instead.
    """
    d = np.asarray(d, float)
    hgt = np.zeros_like(d)
    for row in (-0.5 * gauge, +0.5 * gauge):
        a = np.abs(d - row)
        prof = np.clip(1.0 - a / (w * 0.5), 0.0, 1.0)
        prof = prof * prof * (3.0 - 2.0 * prof)
        if s is not None:
            duty = 0.5 + 0.5 * np.cos(2.0 * math.pi * np.asarray(s) / pitch)
            prof = prof * (0.30 + 0.70 * duty ** 0.6)
        hgt = np.maximum(hgt, h * prof)
    return hgt


def micro_crumple(u, v, uid=0.0, amp=CLOTH.MICRO, scale=1.0):
    """The crumple that is on every square centimetre of worn cloth."""
    a = fbm2(u / (0.026 * scale), v / (0.031 * scale), seed=int(uid * 977) + 11,
             oct=4, gain=0.55)
    b = fbm2(u / (0.0085 * scale), v / (0.0092 * scale),
             seed=int(uid * 331) + 907, oct=3, gain=0.5)
    return amp * ((a - 0.5) * 1.5 + (b - 0.5) * 0.55)


def flex_folds(v, v_joint, flex, width, uid=0.0, phase=0.0,
               n=3, amp=CLOTH.CREASE_D):
    """Concentric compression folds on the inside of a flexed joint.

    A bent elbow does not wrinkle randomly: the cloth on the inside of the bend
    has nowhere to go and buckles into 2-4 arcs whose spacing is set by the
    cloth's own stiffness, and their depth is proportional to the flexion.
    """
    v = np.asarray(v, float)
    d = (v - v_joint) / max(width, 1e-6)
    env = np.exp(-(d * d) * 1.6)
    ph = 2.0 * math.pi * (d * n * 0.5 + phase + hash01(uid, "fold"))
    return amp * flex * env * (0.55 * np.cos(ph) + 0.45 * np.cos(ph * 2.07 + 1.1))


def seg_distance(P, A, B):
    """Distance from points P (N,3) to segments A,B (M,3) -> (N,M) and the
    parameter along each segment.  Vectorised; used for the harness press."""
    P = np.asarray(P, float).reshape(-1, 1, 3)
    A = np.asarray(A, float).reshape(1, -1, 3)
    B = np.asarray(B, float).reshape(1, -1, 3)
    AB = B - A
    L2 = np.sum(AB * AB, -1)
    t = np.sum((P - A) * AB, -1) / np.maximum(L2, 1e-12)
    t = np.clip(t, 0.0, 1.0)
    Q = A + AB * t[..., None]
    D = np.linalg.norm(P - Q, axis=-1)
    return D, t, Q


class StrapPress:
    """The compression a tensioned strap makes in the cloth under it.

    "The belt-over-shoulder compression is the detail."   -- the manifest, on
    driver_race_suit.  It is a 6-9 mm trough with a raised lip either side where
    the cloth the strap displaced has to go, and it is the single thing that
    makes a harness look TIGHT rather than laid on.  The suit is built after the
    harness for exactly this reason.
    """

    def __init__(self, segs, half_w, depth, lip=0.45, tension=1.0):
        self.A = np.array([s[0] for s in segs], float)
        self.B = np.array([s[1] for s in segs], float)
        self.hw = np.asarray(half_w, float)
        self.depth = np.asarray(depth, float) * tension
        self.lip = lip

    def __call__(self, P, chunk=60000):
        P = np.asarray(P, float).reshape(-1, 3)
        out = np.zeros(len(P))
        for i in range(0, len(P), chunk):
            D, _t, _Q = seg_distance(P[i:i + chunk], self.A, self.B)
            r = D / np.maximum(self.hw.reshape(1, -1), 1e-6)
            trough = -self.depth.reshape(1, -1) * np.clip(1.0 - r * r, 0.0, 1.0) ** 0.75
            lip = (self.depth.reshape(1, -1) * self.lip
                   * np.clip(1.0 - np.abs(r - 1.28) / 0.62, 0.0, 1.0) ** 1.5)
            v = trough + lip
            k = np.argmin(v, axis=1)
            out[i:i + chunk] = v[np.arange(len(k)), k]
        return out


def none_press(P):
    return np.zeros(len(np.asarray(P, float).reshape(-1, 3)))


# --------------------------------------------------------------------------- #
# 15.  hard-goods primitives                                                    #
# --------------------------------------------------------------------------- #

def rr_section(hw, hth, n=2.6, M=64, edge_boost=0.0):
    """Closed rounded-rectangle section, returned as (M,2) in (across, through).

    A webbing strap is not a rectangle: the selvedge is a hard rolled edge, it
    is 0.35 mm THICKER than the field, and it is what you actually see in
    silhouette against a suit.  ``edge_boost`` is that.
    """
    th = np.linspace(0, 2 * math.pi, M, endpoint=False)
    r = superellipse(th, hw, hth, n)
    x = r * np.cos(th); y = r * np.sin(th)
    if edge_boost:
        k = np.clip((np.abs(x) - hw * 0.80) / (hw * 0.20), 0.0, 1.0)
        y = y * (1.0 + edge_boost * k * k)
    return np.stack([x, y], 1)


def sweep_section(acc, path, L, N, sect, mat, disp=None, uv0=0.0,
                  base=(0.05, 0.05, 0.05, 0.0), aux=None, wear=None,
                  cap_ends=False, smooth=True, uid=0.0):
    """Sweep a fixed 2-D section (M,2) along a path with frames (L across,
    N through).  ``disp(S_idx, M_idx, x, y, s, w) -> (dx_across, dy_through)``.
    -> index grid (S, M)."""
    P = np.asarray(path, float)
    S = len(P)
    M = len(sect)
    X = np.tile(sect[:, 0].reshape(1, M), (S, 1))
    Y = np.tile(sect[:, 1].reshape(1, M), (S, 1))
    s = arclen(P)
    SS = np.tile(s.reshape(S, 1), (1, M))
    # arc length around the section, for the UV
    d = np.linalg.norm(np.diff(np.vstack([sect, sect[:1]]), axis=0), axis=1)
    w = np.concatenate([[0.0], np.cumsum(d)[:-1]])
    WW = np.tile(w.reshape(1, M), (S, 1))
    if disp is not None:
        dx, dy = disp(X, Y, SS, WW)
        X = X + dx; Y = Y + dy
    Q = (P.reshape(S, 1, 3) + X.reshape(S, M, 1) * L.reshape(S, 1, 3)
         + Y.reshape(S, M, 1) * N.reshape(S, 1, 3))
    uv = np.stack([WW + uv0, SS], -1).reshape(-1, 2)
    i0 = acc.verts(Q.reshape(-1, 3), uv=uv, base=base,
                   aux=aux if aux is not None else (0, 0, 0, uid),
                   wear=wear)
    IDX = i0 + np.arange(S * M).reshape(S, M)
    acc.grid_faces(IDX, mat, smooth, wrap_u=True)
    if cap_ends:
        acc.cap(IDX[0], mat, smooth=False, flip=True, P=Q[0], base=base,
                aux=aux if aux is not None else (0, 0, 0, uid), wear=wear,
                uv=np.array([[0.0, s[0]]]))
        acc.cap(IDX[-1], mat, smooth=False, P=Q[-1], base=base,
                aux=aux if aux is not None else (0, 0, 0, uid), wear=wear,
                uv=np.array([[0.0, s[-1]]]))
    return IDX, Q


def revolve(acc, prof, frame, naz=96, mat=0, base=(0.05, 0.05, 0.05, 0.0),
            aux=(0, 0, 0, 0), wear=None, smooth=True, close=True, th0=0.0):
    """Revolve a (r, z) profile about the frame's +Z.  -> (S, naz) grid."""
    prof = np.asarray(prof, float)
    S = len(prof)
    th = np.linspace(0, 2 * math.pi, naz, endpoint=False) + th0
    R = prof[:, 0].reshape(S, 1)
    Z = prof[:, 1].reshape(S, 1)
    x = R * np.cos(th).reshape(1, naz)
    y = R * np.sin(th).reshape(1, naz)
    z = np.tile(Z, (1, naz))
    P = (frame.o.reshape(1, 1, 3)
         + x[..., None] * frame.x.reshape(1, 1, 3)
         + y[..., None] * frame.y.reshape(1, 1, 3)
         + z[..., None] * frame.z.reshape(1, 1, 3))
    u = np.tile((th * 0.0 + 1.0).reshape(1, naz), (S, 1)) * R * th.reshape(1, naz)
    v = np.tile(arclen(prof if prof.shape[1] == 3 else
                       np.column_stack([prof[:, 0], np.zeros(S), prof[:, 1]])
                       ).reshape(S, 1), (1, naz))
    i0 = acc.verts(P.reshape(-1, 3), uv=np.stack([u, v], -1).reshape(-1, 2),
                   base=base, aux=aux, wear=wear)
    IDX = i0 + np.arange(S * naz).reshape(S, naz)
    acc.grid_faces(IDX, mat, smooth, wrap_u=True, flip=close)
    return IDX, P


def disc_plate(acc, frame, r_out, thick, mat, chamfer=0.0012, naz=128,
               base=(0.05, 0.05, 0.05, 0.0), aux=(0, 0, 0, 0), r_in=0.0,
               wear=None):
    """A machined disc with chamfered rim, closed top and bottom."""
    c = chamfer
    prof = [(r_in, 0.0)] if r_in > 0 else [(0.0, 0.0)]
    prof += [(r_out - c, 0.0), (r_out, -c), (r_out, -thick + c),
             (r_out - c, -thick)]
    prof += [(r_in, -thick)] if r_in > 0 else [(0.0, -thick)]
    prof = np.array(prof, float)
    IDX, P = revolve(acc, prof, frame, naz, mat, base, aux, wear, smooth=True)
    if r_in <= 0:
        acc.fan(IDX[0, 0], IDX[0], mat, False)          # degenerate but closed
    return IDX, P


def hex_head(acc, frame, across, height, mat, base=(0.05, 0.05, 0.05, 0.0),
             aux=(0, 0, 0, 0), socket=True):
    """A cap-head fastener: cylindrical head, chamfer, hex socket.

    A 5 mm cap screw is 3.7 screen pixels here and its socket is 2.1.  Painting
    a dot would have been visible as a painted dot.
    """
    r = across * 0.5
    prof = np.array([(0.0, 0.0), (r * 0.62, 0.0), (r * 0.62, -0.0004),
                     (r - 0.0004, -0.0006), (r, -0.0014),
                     (r, -height + 0.0004), (r - 0.0006, -height),
                     (0.0, -height)], float)
    IDX, P = revolve(acc, prof, frame, 40, mat, base, aux, smooth=True)
    if socket:
        s = r * 0.58
        th = np.linspace(0, 2 * math.pi, 6, endpoint=False) + math.pi / 6.0
        rim = np.stack([s * np.cos(th), s * np.sin(th)], 1)
        dep = height * 0.55
        top = (frame.o.reshape(1, 3) + rim[:, :1] * frame.x
               + rim[:, 1:2] * frame.y)
        bot = top - frame.z * dep
        i0 = acc.verts(np.vstack([top, bot]), base=base, aux=aux)
        ring = i0 + np.arange(6)
        ring2 = i0 + 6 + np.arange(6)
        acc.grid_faces(np.stack([ring, ring2]), mat, False, wrap_u=True)
        acc.fan(acc.verts(np.mean(bot, 0).reshape(1, 3), base=base, aux=aux),
                ring2, mat, False, flip=True)
    return IDX


def knurl_ring(acc, frame, r, h, n_teeth, depth, mat, base, aux):
    """A knurled grip ring — a real toothed cylinder, not a bump map."""
    th = np.linspace(0, 2 * math.pi, n_teeth * 3, endpoint=False)
    rr = r - depth * (0.5 + 0.5 * np.cos(th * n_teeth))
    z = np.array([0.0, -h])
    P = np.zeros((2, len(th), 3))
    for k, zz in enumerate(z):
        P[k] = (frame.o.reshape(1, 3)
                + (rr * np.cos(th)).reshape(-1, 1) * frame.x
                + (rr * np.sin(th)).reshape(-1, 1) * frame.y
                + zz * frame.z)
    uv = np.stack([np.tile(th.reshape(1, -1) * r, (2, 1)),
                   np.tile(z.reshape(2, 1), (1, len(th)))], -1)
    i0 = acc.verts(P.reshape(-1, 3), uv=uv.reshape(-1, 2), base=base, aux=aux)
    IDX = i0 + np.arange(2 * len(th)).reshape(2, len(th))
    acc.grid_faces(IDX, mat, True, wrap_u=True)
    return IDX


def text_flat(acc, body, frame, cap_h, mat, depth=0.00035, tracking=0.12,
              base=(0.05, 0.05, 0.05, 0.0), aux=(0, 0, 0, 0), centre=True,
              wear=None, bend=None):
    """Extrude a wordmark as real geometry on a frame's XY plane.

    ``bend(p2 (N,2)) -> (N,3)`` optionally maps the flat letter plane onto a
    curved surface, which is how the helmet gets a wordmark that follows the
    shell instead of floating off it.
    """
    V, F, w = text_poly(body, tracking)
    if not len(V):
        return
    V = V * cap_h
    if centre:
        V = V - np.array([w * cap_h * 0.5, cap_h * 0.5])
    if bend is None:
        def bend(p2):
            return (frame.o.reshape(1, 3) + p2[:, :1] * frame.x
                    + p2[:, 1:2] * frame.y)
    lo = bend(V)
    nrm = np.cross(frame.x, frame.y)
    hi = lo + nrm.reshape(1, 3) * depth
    uv = V.copy()
    i0 = acc.verts(np.vstack([lo, hi]), uv=np.vstack([uv, uv]), base=base,
                   aux=aux, wear=wear)
    n = len(V)
    acc.tris(F + i0 + n, mat, False)
    acc.tris(F[:, ::-1] + i0, mat, False)
    # side walls along the outline edges (edges used by exactly one triangle)
    from collections import Counter
    cnt = Counter()
    for tri in F:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            cnt[(min(a, b), max(a, b))] += 1
    bnd = [e for e, c in cnt.items() if c == 1]
    if bnd:
        E = np.array(bnd, np.int64)
        Q = np.stack([E[:, 0] + i0, E[:, 1] + i0,
                      E[:, 1] + i0 + n, E[:, 0] + i0 + n], -1)
        acc.quads(Q, mat, False)


# --------------------------------------------------------------------------- #
# 16.  the HANS yoke                                                            #
# --------------------------------------------------------------------------- #
#
# Carbon head-and-neck support.  It matters here for three reasons and only one
# of them is safety: it is the thing the shoulder straps actually run over (so
# the strap does not sit on the shoulder at all), it is what stops the helmet
# from dropping onto the chest, and its two tethers are the most legible piece
# of hardware in the whole cockpit at 3 m.

class HANS:
    __slots__ = ("yoke_path", "yoke_L", "yoke_N", "hw", "th",
                 "post_l", "post_r", "top", "arm_end_l", "arm_end_r")


def hans_path(skel, an=DRIVER):
    """The yoke centre-line: forward along the left collarbone, round behind
    the neck, forward along the right.  Returned with its section frames."""
    c7 = skel.J["c7"]
    tz = unit(skel.J["c7"] - skel.J["t4"])
    tx = unit(np.cross(np.array([0.0, 1.0, 0.0]), tz))
    ty = np.cross(tz, tx)
    key = []
    # forward arm tips, then back over the shoulders, then behind the neck
    for s, lab in ((+1.0, "l"), (-1.0, "r")):
        sh = skel.J["sh_" + s and "sh_l"] if False else skel.J["sh_" + lab]
    L = skel.J["sh_l"]; R = skel.J["sh_r"]
    up = tz
    fwd = tx
    lat = ty
    def pt(sgn, along, out, rise):
        base = c7 + lat * (sgn * out) + up * rise + fwd * along
        return base
    key = [pt(+1, 0.150, 0.108, 0.006),
           pt(+1, 0.108, 0.132, 0.020),
           pt(+1, 0.030, 0.150, 0.036),
           pt(+1, -0.045, 0.128, 0.052),
           pt(+1, -0.078, 0.070, 0.062),
           pt(0.0, -0.090, 0.000, 0.066),
           pt(-1, -0.078, 0.070, 0.062),
           pt(-1, -0.045, 0.128, 0.052),
           pt(-1, 0.030, 0.150, 0.036),
           pt(-1, 0.108, 0.132, 0.020),
           pt(-1, 0.150, 0.108, 0.006)]
    P = resample(catmull(np.array(key), 600), 300)
    T, Lax, Fax = axes_along(P, up)
    return P, Lax, Fax, T


def build_hans(acc, skel, mats, an=DRIVER, uid=0):
    """-> HANS with the frames the tethers and the shoulder straps need."""
    P, Lax, Fax, T = hans_path(skel, an)
    S = len(P)
    t = np.linspace(0, 1, S)
    # the yoke is a tapered aerofoil-ish section: wide and thin over the
    # shoulder, deep and narrow up the back of the neck
    m = np.abs(t - 0.5) * 2.0                       # 1 at the tips, 0 at the back
    hw = 0.0105 + 0.0175 * (1.0 - m) ** 1.3 + 0.0050 * m      # across the body
    hth = 0.0215 - 0.0120 * m ** 1.4                          # up the back
    M = 56
    sect = rr_section(1.0, 1.0, 3.1, M)

    def disp(X, Y, SS, WW):
        # per-station scaling of the unit section, plus the moulded rib that
        # runs the length of a real yoke
        sx = np.interp(SS[:, 0], arclen(P), hw).reshape(-1, 1)
        sy = np.interp(SS[:, 0], arclen(P), hth).reshape(-1, 1)
        rib = 0.0010 * np.clip(1.0 - np.abs(Y / np.maximum(sy, 1e-6)) / 0.35,
                               0, 1) ** 2
        return X * (sx - 1.0), Y * (sy - 1.0) + rib * np.sign(Y + 1e-9)

    # sweep with an explicit "up" of the local body normal
    Nn = np.zeros_like(P)
    ctr = skel.J["c7"]
    Nn = unit(P - (ctr + unit(skel.J["c7"] - skel.J["t4"])
                   * ((P - ctr) @ unit(skel.J["c7"] - skel.J["t4"])).reshape(-1, 1)))
    Lw = unit(np.cross(T, Nn))
    IDX, Q = sweep_section(acc, P, Lw, Nn, sect, MAT_CARBON, disp=disp,
                           base=(0.008, 0.008, 0.009, 0.0),
                           aux=(0.0, 0.6, 0.0, uid),
                           wear=(0.18, 0.12, 0.0, 0.0), cap_ends=True,
                           uid=uid)

    h = HANS()
    h.yoke_path, h.yoke_L, h.yoke_N = P, Lw, Nn
    h.hw, h.th = hw, hth
    h.top = P[S // 2]

    # --- the two tether posts, on top of the back plate -------------------
    up = unit(skel.J["c7"] - skel.J["t4"])
    tx = unit(np.cross(np.array([0.0, 1.0, 0.0]), up))
    ty = np.cross(up, tx)
    for sgn, lab in ((+1.0, "l"), (-1.0, "r")):
        o = h.top + ty * (sgn * 0.052) + Nn[S // 2] * 0.026 + up * 0.014
        fr = Frame(o, tx, None, unit(Nn[S // 2] * 0.55 + up * 0.83), 0.006)
        prof = np.array([(0.0, 0.0), (0.0072, 0.0), (0.0072, -0.0030),
                         (0.0052, -0.0042), (0.0052, -0.0125),
                         (0.0090, -0.0125), (0.0090, -0.0165),
                         (0.0000, -0.0165)], float)
        revolve(acc, prof, fr, 40, MAT_HARDWARE,
                base=(0.09, 0.09, 0.10, 0.0), aux=(0.0, 0.7, 0.5, uid),
                wear=(0.35, 0.10, 0.0, 0.0))
        hex_head(acc, Frame(o + fr.z * 0.0016, tx, None, fr.z), 0.0086, 0.0032,
                 MAT_HARDWARE, base=(0.10, 0.10, 0.11, 0.0),
                 aux=(0.0, 0.8, 0.5, uid))
        setattr(h, "post_" + lab, fr)
    h.arm_end_l = Frame(P[0], T[0], None, Nn[0], 0.014)
    h.arm_end_r = Frame(P[-1], -T[-1], None, Nn[-1], 0.014)

    # --- the shoulder pads on the underside -------------------------------
    for a, b in ((0.06, 0.26), (0.74, 0.94)):
        i0, i1 = int(a * S), int(b * S)
        pp = P[i0:i1] - Nn[i0:i1] * 0.006
        n = len(pp)
        tt = np.linspace(0, 1, n)
        pw = (0.019 + 0.011 * np.sin(math.pi * tt)).reshape(n, 1)
        pd = (0.0055 + 0.0045 * np.sin(math.pi * tt)).reshape(n, 1)
        psect = rr_section(1.0, 1.0, 2.6, 40)

        def pdisp(X, Y, SS, WW, pw=pw, pd=pd, n=n):
            return X * (pw - 1.0), Y * (pd - 1.0)
        sweep_section(acc, pp, unit(np.cross(T[i0:i1], Nn[i0:i1])), -Nn[i0:i1],
                      psect, MAT_FOAM, disp=pdisp,
                      base=(0.020, 0.019, 0.018, 0.0),
                      aux=(0.0, 0.0, 0.0, uid), wear=(0.25, 0.30, 0.0, 0.0),
                      cap_ends=True, uid=uid)
    return h


def build_tethers(acc, skel, h, helmet_posts, uid=0):
    """The two helmet tethers.  19 mm flat webbing, a swaged end fitting at
    each end and a sliding adjuster on the left one, because they are never
    both set the same."""
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        A = getattr(h, "post_" + lab)
        B = helmet_posts[lab]
        d = B.o - A.o
        mid = 0.5 * (A.o + B.o) + unit(np.cross(d, (0, 1.0, 0))) * 0.004
        key = np.vstack([A.o + A.z * 0.010, A.o + A.z * 0.020,
                         mid, B.o - B.z * 0.020, B.o - B.z * 0.010])
        P = resample(catmull(key, 200), 110)
        T, L, N = axes_along(P, np.cross(d, (0, 0, 1.0)))
        M = 60
        sect = rr_section(0.0095, 0.0013, 2.4, M, edge_boost=0.22)

        def disp(X, Y, SS, WW, uid=uid):
            rib = 0.00022 * np.cos(2 * math.pi * X / 0.0016)
            st = np.zeros_like(X)
            for row in (-0.0068, 0.0068):
                st += 0.00028 * np.clip(
                    1.0 - np.abs(X - row) / 0.0009, 0, 1) ** 1.5 * (
                    0.35 + 0.65 * (0.5 + 0.5 * np.cos(2 * math.pi * SS / 0.0030)))
            return np.zeros_like(X), (rib + st) * np.sign(Y + 1e-9)
        sweep_section(acc, P, L, N, sect, MAT_WEBBING, disp=disp,
                      base=(0.020, 0.020, 0.022, 0.0),
                      aux=(0.0, 0.35, 0.0, uid),
                      wear=(0.12, 0.18, 0.0, 0.10), cap_ends=True, uid=uid)
        # swaged end fittings
        for fr, s in ((A, 1.0), (B, -1.0)):
            o = fr.o + fr.z * (0.010 * s if s > 0 else -0.010)
            ff = Frame(o, fr.x, None, fr.z)
            prof = np.array([(0.0, 0.0), (0.0075, 0.0), (0.0075, -0.0090),
                             (0.0050, -0.0110), (0.0050, -0.0150),
                             (0.0000, -0.0150)], float)
            revolve(acc, prof, ff, 32, MAT_HARDWARE,
                    base=(0.085, 0.085, 0.090, 0.0), aux=(0.0, 0.6, 0.5, uid),
                    wear=(0.30, 0.12, 0.0, 0.0))
        if lab == "l":
            i = 42
            fr = Frame(P[i], L[i], None, N[i])
            _adjuster(acc, fr, 0.011, 0.0028, uid, panel=1.0)


def _adjuster(acc, fr, hw, hth, uid, panel=0.5):
    """A three-bar slide.  Two outer bars, a knurled centre bar, and the frame
    around them; the strap threads over-under-over."""
    w = hw * 1.42
    for dz, r in ((-hth * 2.6, 0.0016), (0.0, 0.0019), (hth * 2.6, 0.0016)):
        p0 = fr.o + fr.z * dz - fr.x * w
        p1 = fr.o + fr.z * dz + fr.x * w
        P = np.linspace(p0, p1, 14)
        T, L, N = axes_along(P, fr.z)
        sect = rr_section(r, r * 0.86, 2.2, 24)
        sweep_section(acc, P, L, N, sect, MAT_HARDWARE,
                      base=(0.075, 0.075, 0.080, 0.0),
                      aux=(0.0, 0.55, panel, uid),
                      wear=(0.40, 0.10, 0.0, 0.0), cap_ends=True, uid=uid)
    for sx in (-1.0, 1.0):
        p0 = fr.o + fr.x * (sx * w) - fr.z * hth * 3.1
        p1 = fr.o + fr.x * (sx * w) + fr.z * hth * 3.1
        P = np.linspace(p0, p1, 10)
        T, L, N = axes_along(P, fr.x)
        sect = rr_section(0.0018, 0.0016, 2.2, 20)
        sweep_section(acc, P, L, N, sect, MAT_HARDWARE,
                      base=(0.075, 0.075, 0.080, 0.0),
                      aux=(0.0, 0.55, panel, uid),
                      wear=(0.40, 0.10, 0.0, 0.0), cap_ends=True, uid=uid)


# --------------------------------------------------------------------------- #
# 17.  the six-point harness                                                    #
# --------------------------------------------------------------------------- #

class Harness:
    """Built BEFORE the suit so the suit can be compressed under it."""
    __slots__ = ("straps", "press", "buckle", "anchors", "paths")


def _trunk_eval(TS, tt, theta, out=0.0):
    """Point + outward normal on the trunk surface at (height t, angle theta).

    theta = 0 is the driver's LEFT, pi/2 is FRONT, pi is RIGHT, 3pi/2 is BACK.
    """
    C, L, F, A, B, E, t = TS
    tt = np.atleast_1d(np.asarray(tt, float))
    th = np.atleast_1d(np.asarray(theta, float))
    i = np.interp(tt, t, np.arange(len(t)))
    i0 = np.clip(i.astype(int), 0, len(t) - 2)
    fr = (i - i0).reshape(-1, 1)
    def lp(X):
        X = np.asarray(X)
        return X[i0] * (1 - fr) + X[i0 + 1] * fr
    Cc = lp(C); Ll = unit(lp(L)); Ff = unit(lp(F))
    Aa = lp(A.reshape(-1, 1)).ravel(); Bb = lp(B.reshape(-1, 1)).ravel()
    Ee = lp(E.reshape(-1, 1)).ravel()
    R = superellipse(th, Aa, Bb, Ee) + out
    P = (Cc + (R * np.cos(th)).reshape(-1, 1) * Ll
         + (R * np.sin(th)).reshape(-1, 1) * Ff)
    Nn = unit((np.cos(th) / np.maximum(Aa, 1e-6)).reshape(-1, 1) * Ll
              + (np.sin(th) / np.maximum(Bb, 1e-6)).reshape(-1, 1) * Ff)
    return P, Nn


def harness_paths(skel, TS, hans, an=DRIVER):
    """Strap centre-lines, as (points, normals, half-width, depth, name).

    The shoulder straps do NOT touch the shoulder: they run over the HANS
    yoke's arms, which is why the yoke has to exist before them.
    """
    po = skel.pose
    ten = po.harness_tension
    off = CLOTH.THICK + 0.0016
    out = []

    buck_t, buck_th = 0.300, math.pi / 2.0
    Bp, Bn = _trunk_eval(TS, [buck_t], [buck_th], out=off + 0.010)
    B0, Bnn = Bp[0], Bn[0]

    up = unit(skel.J["c7"] - skel.J["t4"])
    lat = unit(np.cross(up, unit(np.cross(np.array([0.0, 1.0, 0.0]), up))))

    # --- shoulder straps ---------------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        yk = hans.yoke_path
        n = len(yk)
        i_arm = int((0.14 if sgn > 0 else 0.86) * n)
        i_sh = int((0.30 if sgn > 0 else 0.70) * n)
        arm = yk[i_arm] + hans.yoke_N[i_arm] * 0.006
        shl = yk[i_sh] + hans.yoke_N[i_sh] * 0.008
        p1, _ = _trunk_eval(TS, [0.46], [math.pi / 2 - sgn * 0.30], out=off)
        p2, _ = _trunk_eval(TS, [0.63], [math.pi / 2 - sgn * 0.44], out=off)
        back1, _ = _trunk_eval(TS, [0.86], [1.5 * math.pi + sgn * 0.42], out=off)
        anc = skel.J["t8"] - unit(skel.J["t4"] - skel.J["t8"]) * 0.0 \
            + np.array([-0.130, sgn * 0.118, 0.010])
        key = np.vstack([B0 + np.array([0.006, sgn * 0.030, 0.010]),
                         p1[0], p2[0], arm, shl, back1[0], anc])
        P = resample(catmull(key, 400), 240)
        # the normal: away from the spine, which is what a strap lies against
        axis0 = skel.J["pelvis"]; axis1 = skel.J["c7"]
        ax = unit(axis1 - axis0)
        rel = P - axis0
        Nn = unit(rel - ax.reshape(1, 3) * (rel @ ax).reshape(-1, 1))
        out.append((P, Nn, 0.0380, 0.0090 * ten, "shoulder_" + lab))

    # --- lap straps --------------------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        p1, _ = _trunk_eval(TS, [0.235], [math.pi / 2 - sgn * 0.55], out=off)
        p2, _ = _trunk_eval(TS, [0.150], [math.pi / 2 - sgn * 1.05], out=off)
        p3, _ = _trunk_eval(TS, [0.090], [sgn * 0.10 + (0.0 if sgn > 0 else math.pi)],
                            out=off)
        anc = np.array([-0.012, sgn * 0.215, -0.030])
        key = np.vstack([B0 + np.array([0.002, sgn * 0.022, -0.020]),
                         p1[0], p2[0], p3[0], anc])
        P = resample(catmull(key, 300), 170)
        axis0 = skel.J["pelvis"]; ax = unit(skel.J["l5"] - skel.J["pelvis"])
        rel = P - axis0
        Nn = unit(rel - ax.reshape(1, 3) * (rel @ ax).reshape(-1, 1))
        out.append((P, Nn, 0.0255, 0.0072 * ten, "lap_" + lab))

    # --- anti-submarine straps --------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        p1, _ = _trunk_eval(TS, [0.180], [math.pi / 2 - sgn * 0.16], out=off)
        p2, _ = _trunk_eval(TS, [0.075], [math.pi / 2 - sgn * 0.20], out=off)
        anc = np.array([0.118, sgn * 0.050, -0.128])
        key = np.vstack([B0 + np.array([-0.004, sgn * 0.012, -0.030]),
                         p1[0], p2[0], anc])
        P = resample(catmull(key, 260), 130)
        Nn = np.tile(unit(np.array([0.55, 0.0, 0.83])).reshape(1, 3), (len(P), 1))
        Nn = unit(Nn + np.array([0.0, sgn * 0.18, 0.0]))
        out.append((P, Nn, 0.0255, 0.0062 * ten, "crotch_" + lab))

    return out, Frame(B0, unit(np.cross(np.array([0.0, 1.0, 0.0]), Bnn)),
                      None, Bnn, 0.046, "buckle")


def build_harness(acc, skel, TS, hans, mats, an=DRIVER, uid=0):
    paths, buckle = harness_paths(skel, TS, hans, an)
    hn = Harness()
    hn.paths = paths
    hn.buckle = buckle

    segs, hws, deps = [], [], []
    for P, Nn, hw, dep, name in paths:
        for i in range(len(P) - 1):
            segs.append((P[i], P[i + 1]))
            hws.append(hw * 1.02)
            deps.append(dep)
    hn.press = StrapPress(segs, np.array(hws), np.array(deps),
                          tension=skel.pose.harness_tension)

    webcol = srgb('#171a20')
    for P, Nn, hw, dep, name in paths:
        shoulder = name.startswith("shoulder")
        M = 148 if shoulder else 112
        th = 0.0022 if shoulder else 0.0019
        sect = rr_section(hw, th, 2.9, M, edge_boost=0.30)
        T, L, _F = axes_along(P, Nn[0])
        L = unit(np.cross(T, Nn))
        stitch_in = hw - 0.0062

        def disp(X, Y, SS, WW, hw=hw, si=stitch_in, uid=uid, nm=name):
            # 1.6 mm weave rib across the width — 1.2 screen pixels, and the
            # reason a harness glints in a line rather than as a slab
            rib = 0.00042 * (0.5 + 0.5 * np.cos(2 * math.pi * X / 0.0016))
            # a 2/2 twill also has a slow diagonal, 6.4 mm
            diag = 0.00012 * np.cos(2 * math.pi * (X * 0.5 + SS * 0.5) / 0.0064)
            # two rows of edge stitch, broken at the 3.0 mm stitch pitch
            st = np.zeros_like(X)
            duty = 0.5 + 0.5 * np.cos(2 * math.pi * SS / 0.0030)
            for row in (-si, si):
                st += 0.00040 * np.clip(1.0 - np.abs(X - row) / 0.0010,
                                        0, 1) ** 1.4 * (0.30 + 0.70 * duty ** 0.7)
            # the webbing is not flat: it cups slightly under tension
            cup = -0.00055 * (1.0 - (X / max(hw, 1e-6)) ** 2)
            # and it has a memory of every fold it has ever been packed in
            fold = 0.00016 * (fbm2(SS / 0.085, X / 0.030,
                                   seed=int(hash01(nm, uid) * 8000)) - 0.5) * 2.0
            return np.zeros_like(X), (rib + diag + st + cup + fold) * np.sign(Y + 1e-9)

        sweep_section(acc, P, L, Nn, sect, MAT_WEBBING, disp=disp,
                      base=(*webcol, hash01(name, uid)),
                      aux=(0.0, 0.30, 0.0, uid),
                      wear=(0.10, 0.16, 0.02, 0.22 if shoulder else 0.10),
                      cap_ends=True, uid=uid)

        # hardware on the strap: an adjuster part way down, an anchor eye at
        # the far end, and a folded, bar-tacked tail below the adjuster
        i = int(len(P) * (0.62 if shoulder else 0.70))
        fr = Frame(P[i], L[i], None, Nn[i])
        _adjuster(acc, fr, hw, th, uid, panel=0.0 if shoulder else 0.5)
        _anchor_eye(acc, Frame(P[-1], L[-1], None, Nn[-1]), hw, uid)
        if shoulder:
            _harness_label(acc, P, L, Nn, hw, uid, name)

    _build_buckle(acc, buckle, paths, uid)
    hn.straps = paths
    return hn


def _anchor_eye(acc, fr, hw, uid):
    """The eye bolt the strap ends on, plus the folded webbing loop round it."""
    prof = np.array([(0.0, 0.0), (0.0105, 0.0), (0.0105, -0.0038),
                     (0.0072, -0.0050), (0.0072, -0.0180),
                     (0.0000, -0.0180)], float)
    revolve(acc, prof, Frame(fr.o - fr.z * 0.004, fr.x, None, fr.z), 40,
            MAT_HARDWARE, base=(0.080, 0.080, 0.085, 0.0),
            aux=(0.0, 0.6, 0.0, uid), wear=(0.42, 0.15, 0.0, 0.0))
    th = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    R = 0.0125
    C = fr.o - fr.z * 0.006
    P = (C.reshape(1, 3) + (R * np.cos(th)).reshape(-1, 1) * fr.x
         + (R * np.sin(th)).reshape(-1, 1) * fr.y)
    P = np.vstack([P, P[:1]])
    T, L, N = axes_along(P, fr.z)
    sect = rr_section(hw * 0.55, 0.0021, 2.6, 44, edge_boost=0.25)
    sweep_section(acc, P, L, N, sect, MAT_WEBBING,
                  base=(0.018, 0.019, 0.022, 0.0), aux=(0.0, 0.3, 0.0, uid),
                  wear=(0.20, 0.20, 0.0, 0.15), uid=uid)


def _harness_label(acc, P, L, Nn, hw, uid, name):
    """The sewn-on identification label.  Invented text only."""
    i = int(len(P) * 0.30)
    fr = Frame(P[i] + Nn[i] * 0.0026, L[i], None, Nn[i])
    w, h = hw * 1.55, 0.0125
    gx = np.linspace(-w * 0.5, w * 0.5, 26)
    gy = np.linspace(-h * 0.5, h * 0.5, 12)
    GX, GY = np.meshgrid(gx, gy)
    curl = 0.00045 * np.sin(GX / w * 3.1) * np.clip((GY / h + 0.5), 0, 1)
    Q = (fr.o.reshape(1, 1, 3) + GX[..., None] * fr.x + GY[..., None] * fr.y
         + curl[..., None] * fr.z)
    i0 = acc.verts(Q.reshape(-1, 3),
                   uv=np.stack([GX, GY], -1).reshape(-1, 2),
                   base=(0.62, 0.61, 0.58, 0.0), aux=(0.0, 0.2, 0.0, uid),
                   wear=(0.20, 0.25, 0.0, 0.30))
    IDX = i0 + np.arange(Q.shape[0] * Q.shape[1]).reshape(Q.shape[:2])
    acc.grid_faces(IDX, MAT_WEBBING, True)
    text_flat(acc, "CALIBRE  HARNAIS 6PT",
              Frame(fr.o + fr.z * 0.00050, fr.x, None, fr.z), 0.0026,
              MAT_EMB, depth=0.00028, tracking=0.16,
              base=(0.020, 0.021, 0.024, 0.0), aux=(0.0, 0.9, 0.0, uid))
    text_flat(acc, "LOT 41-7",
              Frame(fr.o + fr.z * 0.00050 - fr.y * 0.0042, fr.x, None, fr.z),
              0.0022, MAT_EMB, depth=0.00026, tracking=0.18,
              base=(0.020, 0.021, 0.024, 0.0), aux=(0.0, 0.9, 0.0, uid))


def _build_buckle(acc, fr, paths, uid):
    """A rotary cam-lock: base, six lugs, the turning cover with its lever,
    a knurled rim, the release arrow and the five strap tongues."""
    base_c = (0.085, 0.086, 0.090, 0.0)
    anod = (0.035, 0.036, 0.040, 0.0)
    o = fr.o
    zz = fr.z
    b = Frame(o + zz * 0.0090, fr.x, None, zz)
    # base plate
    prof = np.array([(0.0, 0.0), (0.0400, 0.0), (0.0446, -0.0016),
                     (0.0460, -0.0042), (0.0460, -0.0076),
                     (0.0432, -0.0090), (0.0000, -0.0090)], float)
    revolve(acc, prof, b, 128, MAT_HARDWARE, base=base_c,
            aux=(0.0, 0.65, 0.0, uid), wear=(0.30, 0.12, 0.0, 0.0))
    # five tongue slots as raised guides around the rim
    for k, ang in enumerate((0.0, 1.15, 2.30, math.pi + 0.95, math.pi + 2.10)):
        d = math.cos(ang) * fr.x + math.sin(ang) * fr.y
        p0 = b.o + d * 0.030 - zz * 0.0006
        p1 = b.o + d * 0.0505 - zz * 0.0006
        P = np.linspace(p0, p1, 8)
        T, L, N = axes_along(P, zz)
        sect = rr_section(0.0135, 0.0022, 3.0, 28)
        sweep_section(acc, P, L, N, sect, MAT_HARDWARE, base=base_c,
                      aux=(0.0, 0.6, 0.0, uid), wear=(0.35, 0.10, 0.0, 0.0),
                      cap_ends=True, uid=uid)
    # the rotating cover
    c = Frame(o + zz * 0.0168, fr.x, None, zz)
    prof = np.array([(0.0, 0.0), (0.0300, 0.0), (0.0345, -0.0022),
                     (0.0362, -0.0050), (0.0362, -0.0072),
                     (0.0330, -0.0078), (0.0000, -0.0078)], float)
    revolve(acc, prof, c, 128, MAT_HARDWARE, base=anod,
            aux=(0.0, 0.45, 0.5, uid), wear=(0.45, 0.10, 0.0, 0.0))
    knurl_ring(acc, Frame(c.o - zz * 0.0022, fr.x, None, zz), 0.0362, 0.0028,
               46, 0.00055, MAT_HARDWARE, anod, (0.0, 0.45, 0.5, uid))
    # the lever
    lp = np.array([c.o + fr.x * 0.006 + zz * 0.0010,
                   c.o + fr.x * 0.026 + zz * 0.0030,
                   c.o + fr.x * 0.040 + zz * 0.0075])
    P = resample(catmull(lp, 60), 26)
    T, L, N = axes_along(P, zz)
    sect = rr_section(0.0072, 0.0026, 3.0, 34)
    sweep_section(acc, P, L, N, sect, MAT_HARDWARE, base=anod,
                  aux=(0.0, 0.5, 0.5, uid), wear=(0.55, 0.08, 0.0, 0.0),
                  cap_ends=True, uid=uid)
    text_flat(acc, "TOURNER", Frame(c.o + zz * 0.0002 - fr.x * 0.014,
                                    fr.x, None, zz), 0.0032, MAT_HARDWARE,
              depth=-0.00022, tracking=0.20, base=(0.02, 0.02, 0.022, 0.0),
              aux=(0.0, 0.9, 0.5, uid))


# --------------------------------------------------------------------------- #
# 18.  the race suit                                                            #
# --------------------------------------------------------------------------- #

def _dth(TH, th0, R):
    """Signed distance IN METRES from the angular seam at th0."""
    d = (TH - th0 + math.pi) % (2.0 * math.pi) - math.pi
    return d * R


def loft_emit(acc, C, X, Y, A, B, E, N, mat, disp=None, base=None, aux=None,
              wear=None, uid=0.0, wrap=True, uv_scale=1.0, smooth=True,
              theta0=0.0):
    """Loft + emit + return the grids the caller needs for seams and patches."""
    P, TH, VV, R = loft(C, X, Y, A, B, E, N, disp=disp, theta0=theta0)
    S = P.shape[0]
    uv = np.stack([TH * R * uv_scale, VV * uv_scale], -1).reshape(-1, 2)
    nb = base if base is not None else (0.05, 0.05, 0.05, 0.0)
    na = aux if aux is not None else (0.0, 0.0, 0.0, uid)
    i0 = acc.verts(P.reshape(-1, 3), uv=uv, base=nb, aux=na, wear=wear)
    IDX = i0 + np.arange(S * N).reshape(S, N)
    acc.grid_faces(IDX, mat, smooth, wrap_u=wrap)
    return IDX, P, TH, VV, R


def build_suit(acc, skel, TS, hn, hans, an=DRIVER, uid=0):
    """The overall.

    Built AFTER the harness so ``hn.press`` can push the cloth in under every
    strap, and after the HANS so the yoke can do the same over the shoulders.
    That ordering is the whole reason the belt-over-shoulder compression looks
    like tension rather than like decoration.
    """
    po = skel.pose
    C, L, F, A, B, E, t = TS
    S = len(C)
    N = 232
    shell = srgb(SUIT_COL["shell"])
    panel = srgb(SUIT_COL["panel"])
    off = CLOTH.THICK

    # the yoke of the HANS presses too, over a much wider footprint
    ysegs = [(hans.yoke_path[i], hans.yoke_path[i + 1])
             for i in range(len(hans.yoke_path) - 1)]
    ypress = StrapPress(ysegs, np.full(len(ysegs), 0.030),
                        np.full(len(ysegs), 0.0055))

    tt = np.tile(t.reshape(S, 1), (1, N))
    seams = []

    def disp(TH, VV, R):
        d = np.zeros_like(R)
        # ---- garment thickness and the drape of slack cloth ---------------
        d += off
        slack = sstep(0.10, 0.30, tt) * (1.0 - sstep(0.62, 0.86, tt))
        d += CLOTH.DRAPE * 0.35 * slack * (0.6 + 0.4 * np.sin(TH * 2.0))

        # ---- seams ---------------------------------------------------------
        # side seams (both sides), centre back, front placket edge
        for th0 in (0.0, math.pi):
            d += welt(_dth(TH, th0, R))
            d += stitch_field(_dth(TH, th0, R), s=VV)
        dcb = _dth(TH, 1.5 * math.pi, R)
        m_cb = sstep(0.02, 0.08, tt) * (1.0 - sstep(0.80, 0.90, tt))
        d += welt(dcb) * m_cb + stitch_field(dcb, s=VV) * m_cb
        # waist seam, all the way round
        dw = (VV - np.interp(0.255, t, arclen(C)))
        d += welt(dw, w=0.0075, h=0.0011)
        d += stitch_field(dw, s=TH * R)
        # back yoke seam
        dy = (VV - np.interp(0.795, t, arclen(C)))
        m_y = 0.5 + 0.5 * np.cos(np.clip((TH - 1.5 * math.pi + math.pi)
                                         % (2 * math.pi) - math.pi, -1.6, 1.6)
                                 * (math.pi / 1.6))
        d += (welt(dy, w=0.0080, h=0.0012) + stitch_field(dy, s=TH * R)) * m_y

        # ---- the front placket over the zip -------------------------------
        dz = _dth(TH, math.pi / 2.0, R)
        m_z = sstep(0.08, 0.14, tt) * (1.0 - sstep(0.93, 0.99, tt))
        plack = 0.0022 * np.clip(1.0 - np.abs(dz) / 0.0130, 0, 1) ** 0.35
        d += plack * m_z
        d += (stitch_field(np.abs(dz) - 0.0118, gauge=0.0, w=0.0018, s=VV)
              * m_z)

        # ---- anatomy the cloth is stretched over ---------------------------
        # pectorals
        pec = (crest((tt - 0.665) / 0.115)
               * crest(_dth(TH, math.pi / 2.0, R) / 0.085 - 0.0))
        pecl = crest((tt - 0.665) / 0.115) * (
            crest((_dth(TH, math.pi / 2.0, R) - 0.052) / 0.058)
            + crest((_dth(TH, math.pi / 2.0, R) + 0.052) / 0.058))
        d += 0.0075 * pecl
        # scapulae
        sc = crest((tt - 0.775) / 0.090) * (
            crest((_dth(TH, 1.5 * math.pi, R) - 0.062) / 0.052)
            + crest((_dth(TH, 1.5 * math.pi, R) + 0.062) / 0.052))
        d += 0.0055 * sc
        # trapezius ridge
        tr = crest((tt - 0.945) / 0.075) * crest(
            (np.abs(_dth(TH, 1.5 * math.pi, R)) - 0.075) / 0.075)
        d += 0.0060 * tr
        # the ribs, faintly, on a driver
        rb = (0.0011 * np.cos(2 * math.pi * (VV - 0.30) / 0.036)
              * crest((tt - 0.50) / 0.20)
              * crest(_dth(TH, math.pi / 2.0, R) / 0.14))
        d += rb

        # ---- folds ---------------------------------------------------------
        u_m = TH * R
        d += micro_crumple(u_m, VV, uid=uid, amp=CLOTH.MICRO)
        # the cloth gathers at the waist under the lap belt
        d += (0.0022 * np.cos(2 * math.pi * u_m / 0.052 + hash01(uid, "w") * 6.0)
              * crest((tt - 0.215) / 0.10))
        # and pulls in tension lines from the shoulder straps to the buckle
        d += (0.0016 * np.cos(2 * math.pi * (u_m * 0.6 + VV * 0.8) / 0.075)
              * sstep(0.30, 0.45, tt) * (1.0 - sstep(0.70, 0.86, tt)))
        return d

    def seam_only(TH, VV, R):
        h = np.zeros_like(R)
        for th0 in (0.0, math.pi, 1.5 * math.pi):
            h = np.maximum(h, welt(_dth(TH, th0, R)))
        h = np.maximum(h, welt(VV - np.interp(0.255, t, arclen(C)),
                               w=0.0075, h=0.0011))
        h = np.maximum(h, welt(VV - np.interp(0.795, t, arclen(C)),
                               w=0.0080, h=0.0012))
        return h

    # first pass without the strap press, to find where the cloth actually is
    P0, TH0, VV0, R0 = loft(C, L, F, A, B, E, N, disp=disp)
    pr = hn.press(P0.reshape(-1, 3)).reshape(S, N)
    yp = ypress(P0.reshape(-1, 3)).reshape(S, N)
    press = pr + yp

    def disp2(TH, VV, R):
        return disp(TH, VV, R) + press

    aux_seam = np.zeros((S * N, 4))
    aux_seam[:, 0] = np.clip(seam_only(TH0, VV0, R0).ravel() / CLOTH.FELL_H,
                             0.0, 1.0)
    aux_seam[:, 1] = np.clip(-press.ravel() * 55.0, 0.0, 1.0)
    aux_seam[:, 3] = uid
    IDX, P, TH, VV, R = loft_emit(
        acc, C, L, F, A, B, E, N, MAT_NOMEX, disp=disp2,
        base=suit_livery(tt.ravel(), uid),
        aux=aux_seam,
        wear=_suit_wear(tt, TH0, press, uid), uid=uid)

    # --- shoulder cap: from the top ring in to the neck opening -----------
    top = P[-1]
    nk_o = skel.J["neck"]
    nz = unit(skel.J["head"] - skel.J["neck"])
    nx = unit(np.cross(np.array([0.0, 1.0, 0.0]), nz))
    ny = np.cross(nz, nx)
    K = 22
    th = np.linspace(0.0, 2.0 * math.pi, N, endpoint=False)
    neck_r = an.neck_r + off + 0.0075
    NK = (nk_o.reshape(1, 3) + (neck_r * np.cos(th)).reshape(N, 1) * ny
          + (neck_r * np.sin(th)).reshape(N, 1) * nx)
    rows = [top]
    for k in range(1, K):
        a = k / float(K)
        s = a * a * (3.0 - 2.0 * a)
        row = top * (1 - s) + NK * s
        rise = (0.030 * math.sin(math.pi * a) *
                (0.55 + 0.45 * np.cos(th - 1.5 * math.pi)))
        row = row + nz.reshape(1, 3) * rise.reshape(N, 1)
        rows.append(row)
    rows.append(NK)
    CAP = np.array(rows)
    capr = np.linalg.norm(CAP - nk_o.reshape(1, 1, 3), axis=-1)
    cp = hn.press(CAP.reshape(-1, 3)).reshape(CAP.shape[0], N) \
        + ypress(CAP.reshape(-1, 3)).reshape(CAP.shape[0], N)
    CAP = CAP + unit(CAP - nk_o.reshape(1, 1, 3)) * cp[..., None]
    uvc = np.stack([np.tile(th.reshape(1, N) * 0.12, (CAP.shape[0], 1)),
                    np.tile(arclen(CAP[:, 0]).reshape(-1, 1), (1, N))
                    + np.interp(1.0, t, arclen(C))], -1)
    i0 = acc.verts(CAP.reshape(-1, 3), uv=uvc.reshape(-1, 2),
                   base=suit_livery(np.full(CAP.shape[0] * N, 0.95), uid),
                   aux=(0, 0, 0, uid), wear=(0.06, 0.05, 0.0, 0.10))
    CIDX = i0 + np.arange(CAP.shape[0] * N).reshape(CAP.shape[0], N)
    acc.grid_faces(CIDX, MAT_NOMEX, True, wrap_u=True)

    # --- collar ------------------------------------------------------------
    coll = srgb(SUIT_COL["collar"])
    ch = 0.045
    prof_r = np.array([0.0, 0.30, 0.62, 0.88, 1.0])
    CR = []
    for a in prof_r:
        r = neck_r + 0.0030 + 0.0032 * math.sin(math.pi * a) - 0.0015 * a
        row = (nk_o.reshape(1, 3) + (r * np.cos(th)).reshape(N, 1) * ny
               + (r * np.sin(th)).reshape(N, 1) * nx
               + nz.reshape(1, 3) * (a * ch))
        CR.append(row)
    CR = np.array(CR)
    uvr = np.stack([np.tile(th.reshape(1, N) * neck_r, (len(CR), 1)),
                    np.tile((prof_r * ch).reshape(-1, 1), (1, N))], -1)
    i0 = acc.verts(CR.reshape(-1, 3), uv=uvr.reshape(-1, 2),
                   base=(*coll, hash01(uid, "coll")), aux=(0.0, 0.4, 0.0, uid),
                   wear=(0.14, 0.18, 0.02, 0.05))
    RIDX = i0 + np.arange(len(CR) * N).reshape(len(CR), N)
    acc.grid_faces(RIDX, MAT_KNIT, True, wrap_u=True)

    # --- sleeves ------------------------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        _sleeve(acc, skel, lab, sgn, hn, an, uid, shell, off)
    # --- legs ---------------------------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        _trouser(acc, skel, lab, sgn, an, uid, shell, off)

    # --- the extraction handle across the upper back -----------------------
    _extraction_handle(acc, TS, skel, uid)
    # --- badges -------------------------------------------------------------
    _suit_badges(acc, TS, skel, an, uid, press_fn=lambda P: hn.press(P) + ypress(P))
    return IDX, P


def _suit_wear(tt, TH, press, uid):
    """(abrasion, dirt, oil, sunfade) per vertex.

    A driver's suit is not uniformly grubby.  It is polished where the harness
    rubs, oily at the cuffs and the chest where his gloves land, and bleached
    across the shoulders where it has sat in the sun on a grid.
    """
    S, N = tt.shape
    abr = np.clip(-press * 90.0, 0, 1) * 0.55 + 0.06
    abr += 0.25 * sstep(0.86, 1.0, tt)
    dirt = 0.10 + 0.22 * sstep(0.10, 0.02, tt) + 0.16 * np.clip(-press * 60, 0, 1)
    oil = 0.05 + 0.20 * (sstep(0.45, 0.62, tt) * (1 - sstep(0.72, 0.85, tt))
                         * crest(_dth(TH, math.pi / 2.0, np.ones_like(TH)) / 1.2))
    fade = 0.12 + 0.30 * sstep(0.78, 0.98, tt)
    W = np.stack([abr, dirt, oil, fade], -1).reshape(-1, 4)
    return np.clip(W, 0.0, 1.0)


def _sleeve(acc, skel, lab, sgn, hn, an, uid, shell, off):
    P, L, F, A, B, E, t = arm_sections(skel, lab, S=200)
    S = len(P)
    N = 132
    tt = np.tile(t.reshape(S, 1), (1, N))
    v_elbow = float(np.interp(0.50, t, arclen(P)))
    flex = 0.85

    def disp(TH, VV, R):
        d = np.full_like(R, off)
        # the outer sleeve seam and the underarm seam
        for th0, m in ((0.0, 1.0), (math.pi, 1.0)):
            dd = _dth(TH, th0, R)
            d += welt(dd, w=0.0078, h=0.0012) * m
            d += stitch_field(dd, gauge=0.0055, s=VV) * m
        # elbow patch: a doubled panel, 1.1 mm proud, with its own stitch line
        ep = (sstep(0.40, 0.44, tt) * (1.0 - sstep(0.66, 0.70, tt))
              * crest(_dth(TH, 0.5 * math.pi, R) / 0.070))
        d += 0.0011 * ep
        d += stitch_field(np.abs(_dth(TH, 0.5 * math.pi, R)) - 0.062,
                          gauge=0.0, w=0.0016, s=VV) * (
            sstep(0.40, 0.44, tt) * (1.0 - sstep(0.66, 0.70, tt)))
        # deltoid and triceps under the cloth
        d += 0.0060 * crest((tt - 0.09) / 0.13)
        d += 0.0030 * crest((tt - 0.26) / 0.16) * crest(
            _dth(TH, 1.5 * math.pi, R) / 0.055)
        # flexion folds inside the elbow
        d += flex_folds(VV, v_elbow, flex, 0.075, uid=uid + 3,
                        n=3, amp=CLOTH.CREASE_D) * crest(
            _dth(TH, 0.5 * math.pi, R) / 0.085)
        # tension across the outside of the elbow
        d -= 0.0018 * crest((tt - 0.52) / 0.10) * crest(
            _dth(TH, 1.5 * math.pi, R) / 0.070)
        # slack hanging under the upper arm
        d += CLOTH.DRAPE * 0.30 * crest((tt - 0.22) / 0.20) * np.clip(
            np.sin(TH + 0.4), 0, 1) ** 2
        d += micro_crumple(TH * R, VV, uid=uid + 7, amp=CLOTH.MICRO)
        return d

    P0, TH0, VV0, R0 = loft(P, L, F, A, B, E, N, disp=disp)
    pr = hn.press(P0.reshape(-1, 3)).reshape(S, N)

    def disp2(TH, VV, R):
        return disp(TH, VV, R) + pr

    wear = np.stack([
        np.clip(0.10 + 0.42 * sstep(0.42, 0.60, tt) - pr * 70.0, 0, 1),
        np.clip(0.10 + 0.30 * sstep(0.80, 1.0, tt), 0, 1),
        np.clip(0.04 + 0.28 * sstep(0.84, 1.0, tt), 0, 1),
        np.clip(0.14 + 0.26 * (1 - sstep(0.0, 0.35, tt)), 0, 1)], -1
    ).reshape(-1, 4)
    IDX, PP, TH, VV, R = loft_emit(
        acc, P, L, F, A, B, E, N, MAT_NOMEX, disp=disp2,
        base=suit_livery(tt.ravel(), uid, sleeve=True),
        aux=(0.0, 0.0, 0.0, uid), wear=wear, uid=uid)

    # knitted cuff at the wrist
    _knit_band(acc, P[-1], unit(P[-1] - P[-6]),
               unit(np.cross(np.array([0.0, sgn, 0.0]), unit(P[-1] - P[-6]))),
               A[-1] + off, B[-1] + off, E[-1], 0.058, N, uid, srgb(SUIT_COL["cuff"]))
    return IDX


def _trouser(acc, skel, lab, sgn, an, uid, shell, off):
    P, L, F, A, B, E, t = leg_sections(skel, lab, S=160)
    S = len(P)
    N = 108
    tt = np.tile(t.reshape(S, 1), (1, N))
    v_knee = float(np.interp(0.52, t, arclen(P)))

    def disp(TH, VV, R):
        d = np.full_like(R, off)
        for th0 in (0.0, math.pi):
            dd = _dth(TH, th0, R)
            d += welt(dd, w=0.0078, h=0.0012)
            d += stitch_field(dd, gauge=0.0055, s=VV)
        d += 0.0012 * (sstep(0.44, 0.48, tt) * (1 - sstep(0.62, 0.66, tt))
                       * crest(_dth(TH, 0.5 * math.pi, R) / 0.075))
        d += flex_folds(VV, v_knee, 0.75, 0.085, uid=uid + 11, n=3) * crest(
            _dth(TH, 1.5 * math.pi, R) / 0.090)
        d += 0.0055 * crest((tt - 0.64) / 0.16) * crest(
            _dth(TH, 1.5 * math.pi, R) / 0.070)
        d += CLOTH.DRAPE * 0.45 * crest((tt - 0.30) / 0.26) * np.clip(
            -np.sin(TH), 0, 1) ** 2
        d += micro_crumple(TH * R, VV, uid=uid + 13, amp=CLOTH.MICRO * 1.15)
        return d

    wear = np.stack([np.clip(0.08 + 0.30 * sstep(0.44, 0.62, tt), 0, 1),
                     np.clip(0.14 + 0.24 * sstep(0.80, 1.0, tt), 0, 1),
                     np.full_like(tt, 0.05),
                     np.full_like(tt, 0.10)], -1).reshape(-1, 4)
    loft_emit(acc, P, L, F, A, B, E, N, MAT_NOMEX, disp=disp,
              base=(*shell, hash01(uid, "dye")), aux=(0.0, 0.0, 0.0, uid),
              wear=wear, uid=uid)
    _knit_band(acc, P[-1], unit(P[-1] - P[-6]),
               unit(np.cross(np.array([0.0, sgn, 0.0]), unit(P[-1] - P[-6]))),
               A[-1] + off, B[-1] + off, E[-1], 0.062, N, uid,
               srgb(SUIT_COL["cuff"]))


def _knit_band(acc, o, axis, left, a, b, e, length, N, uid, col):
    """A ribbed knit cuff.  The rib is MESH: 3.4 mm wales, 1.1 mm deep."""
    K = 26
    fwd = unit(np.cross(left, axis))
    th = np.linspace(0, 2 * math.pi, N, endpoint=False)
    rows, uvs = [], []
    for k in range(K):
        s = k / float(K - 1)
        r = superellipse(th, a * (1.0 - 0.10 * s), b * (1.0 - 0.10 * s), e)
        rib = 0.0011 * (0.5 + 0.5 * np.cos(th * max(int(2 * math.pi * a / 0.0034), 8)))
        r = r + 0.0016 + rib * (0.25 + 0.75 * math.sin(math.pi * min(s * 1.15, 1.0)))
        p = (o.reshape(1, 3) + (r * np.cos(th)).reshape(N, 1) * left
             + (r * np.sin(th)).reshape(N, 1) * fwd
             + axis.reshape(1, 3) * (s * length))
        rows.append(p)
        uvs.append(np.stack([th * a, np.full(N, s * length)], -1))
    R = np.array(rows)
    i0 = acc.verts(R.reshape(-1, 3), uv=np.array(uvs).reshape(-1, 2),
                   base=(*col, hash01(uid, "knit")), aux=(0.0, 0.35, 0.0, uid),
                   wear=(0.22, 0.26, 0.10, 0.08))
    IDX = i0 + np.arange(K * N).reshape(K, N)
    acc.grid_faces(IDX, MAT_KNIT, True, wrap_u=True)
    return IDX


def _extraction_handle(acc, TS, skel, uid):
    """The webbing handle across the shoulder blades a marshal lifts him by."""
    th0 = 1.5 * math.pi
    pts = []
    for a in np.linspace(-1.0, 1.0, 9):
        p, n = _trunk_eval(TS, [0.845 + 0.012 * (1 - a * a)],
                           [th0 + a * 0.52], out=CLOTH.THICK + 0.0030
                           + 0.0075 * (1 - a * a))
        pts.append(p[0])
    P = resample(catmull(np.array(pts), 240), 130)
    T, L, N = axes_along(P, unit(skel.J["c7"] - skel.J["t8"]))
    ctr = skel.J["t8"]
    ax = unit(skel.J["c7"] - skel.J["t8"])
    rel = P - ctr
    Nn = unit(rel - ax.reshape(1, 3) * (rel @ ax).reshape(-1, 1))
    Lw = unit(np.cross(T, Nn))
    sect = rr_section(0.0155, 0.0022, 2.8, 72, edge_boost=0.28)

    def disp(X, Y, SS, WW):
        rib = 0.00024 * (0.5 + 0.5 * np.cos(2 * math.pi * X / 0.0016))
        st = np.zeros_like(X)
        for row in (-0.0100, 0.0100):
            st += 0.00034 * np.clip(1 - np.abs(X - row) / 0.0009, 0, 1) ** 1.4
        return np.zeros_like(X), (rib + st) * np.sign(Y + 1e-9)
    sweep_section(acc, P, Lw, Nn, sect, MAT_WEBBING, disp=disp,
                  base=(0.30, 0.24, 0.05, 0.0), aux=(0.0, 0.3, 0.0, uid),
                  wear=(0.18, 0.20, 0.0, 0.30), cap_ends=True, uid=uid)


def _surface_bend(TS, t0, th0, w, h, out):
    """-> a function mapping flat (x, y) in metres onto the trunk surface."""
    def bend(p2):
        p2 = np.asarray(p2, float).reshape(-1, 2)
        C, L, F, A, B, E, t = TS
        i = int(np.interp(t0, t, np.arange(len(t))))
        Rloc = float(superellipse(np.array([th0]), A[i], B[i], E[i])[0])
        dth = p2[:, 0] / max(Rloc, 1e-6)
        dv = p2[:, 1]
        varr = arclen(C)
        v0 = float(np.interp(t0, t, varr))
        tt = np.interp(v0 + dv, varr, t)
        P, Nn = _trunk_eval(TS, tt, th0 + dth, out=out)
        return P
    return bend


def _patch(acc, TS, t0, th0, w, h, uid, text, cap, col_bg, col_fg,
           tracking=0.14, strap=None):
    """An appliqued badge: a rounded panel, a merrowed edge bead, a satin
    wordmark and the pucker the stitching pulls into the cloth around it."""
    nu, nv = 44, 30
    gx = np.linspace(-w * 0.5, w * 0.5, nu)
    gy = np.linspace(-h * 0.5, h * 0.5, nv)
    GX, GY = np.meshgrid(gx, gy)
    rx = np.clip((np.abs(GX) - (w * 0.5 - 0.006)) / 0.006, 0, 1)
    ry = np.clip((np.abs(GY) - (h * 0.5 - 0.006)) / 0.006, 0, 1)
    rr = np.sqrt(rx * rx + ry * ry)
    keep = rr < 1.0
    lift = (0.0014 + 0.0009 * (1.0 - np.clip(rr, 0, 1)) ** 0.5
            + 0.0006 * np.cos(GX / w * 7.0) * (0.5 + 0.5 * GY / h))
    bend = _surface_bend(TS, t0, th0, w, h, CLOTH.THICK)
    flat = np.stack([GX.ravel(), GY.ravel()], 1)
    P = bend(flat)
    Nn = unit(P - P.mean(0))
    P = P + Nn * lift.ravel()[:, None] * 0.0
    # push the badge outward along the local surface normal
    p1 = bend(flat + np.array([0.0006, 0.0]))
    p2 = bend(flat + np.array([0.0, 0.0006]))
    nrm = unit(np.cross(p1 - P, p2 - P))
    P = P + nrm * lift.ravel()[:, None]
    i0 = acc.verts(P, uv=flat, base=(*col_bg, hash01(text, uid)),
                   aux=(0.0, 0.55, 0.0, uid), wear=(0.10, 0.14, 0.0, 0.20))
    IDX = i0 + np.arange(nu * nv).reshape(nv, nu)
    for r in range(nv - 1):
        for cc in range(nu - 1):
            pass
    ok = keep[:-1, :-1] & keep[:-1, 1:] & keep[1:, 1:] & keep[1:, :-1]
    Q = np.stack([IDX[:-1, :-1], IDX[:-1, 1:], IDX[1:, 1:], IDX[1:, :-1]], -1)
    acc.quads(Q[ok], MAT_EMB, True)
    # the wordmark, sitting 0.35 mm proud of the badge
    fr = Frame(P.mean(0), unit(bend(np.array([[0.01, 0.0]]))[0] - P.mean(0)),
               None, unit(nrm.mean(0)))
    def bend_txt(p2):
        q = bend(p2)
        pp1 = bend(p2 + np.array([0.0006, 0.0]))
        pp2 = bend(p2 + np.array([0.0, 0.0006]))
        nn = unit(np.cross(pp1 - q, pp2 - q))
        return q + nn * (0.0026 + 0.0004)
    text_flat(acc, text, fr, cap, MAT_EMB, depth=0.00045, tracking=tracking,
              base=(*col_fg, 0.0), aux=(0.0, 0.95, 0.0, uid), bend=bend_txt)


def _suit_badges(acc, TS, skel, an, uid, press_fn=None):
    B = BRANDS
    _patch(acc, TS, 0.700, math.pi / 2 - 0.44, 0.070, 0.030, uid,
           "CIRCUIT VITRINE", 0.0090, srgb(B["CIRCUIT VITRINE"][0]),
           srgb(B["CIRCUIT VITRINE"][1]), tracking=0.10)
    _patch(acc, TS, 0.700, math.pi / 2 + 0.44, 0.058, 0.026, uid,
           "MERIDIAN", 0.0092, srgb(B["MERIDIAN"][0]), srgb(B["MERIDIAN"][1]))
    _patch(acc, TS, 0.560, math.pi / 2 - 0.10, 0.086, 0.024, uid,
           "ARDENT", 0.0110, srgb(B["ARDENT"][0]), srgb(B["ARDENT"][1]),
           tracking=0.20)
    _patch(acc, TS, 0.900, 1.5 * math.pi, 0.130, 0.030, uid,
           "OBSIDIAN", 0.0125, srgb(B["OBSIDIAN"][0]), srgb(B["OBSIDIAN"][1]),
           tracking=0.22)
    _patch(acc, TS, 0.300, math.pi / 2 + 0.62, 0.048, 0.020, uid,
           "CALIBRE", 0.0075, srgb(B["CALIBRE"][0]), srgb(B["CALIBRE"][1]))


# --------------------------------------------------------------------------- #
# 19.  the head form and the balaclava                                          #
# --------------------------------------------------------------------------- #

HEAD_KEYS = [                      # z, half-width (lateral), half-depth, exp, x-offset
    (+0.1180, 0.0120, 0.0140, 2.2, -0.006),
    (+0.1020, 0.0480, 0.0560, 2.3, -0.007),
    (+0.0800, 0.0625, 0.0755, 2.4, -0.008),
    (+0.0500, 0.0715, 0.0885, 2.5, -0.008),
    (+0.0200, 0.0762, 0.0955, 2.6, -0.006),
    (-0.0050, 0.0770, 0.0975, 2.6, -0.002),
    (-0.0300, 0.0738, 0.0952, 2.6,  0.003),
    (-0.0550, 0.0668, 0.0890, 2.6,  0.008),
    (-0.0800, 0.0560, 0.0790, 2.7,  0.012),
    (-0.1000, 0.0455, 0.0650, 2.8,  0.012),
    (-0.1150, 0.0400, 0.0510, 2.6,  0.004),
    (-0.1450, 0.0585, 0.0605, 2.4, -0.010),
    (-0.1900, 0.0640, 0.0655, 2.4, -0.014),
]


def head_frame(skel):
    o = skel.J["head"]
    M = skel.F["head"]
    return Frame(o, M[:, 0], None, M[:, 2], skel.an.head_r, "head")


def head_sections(skel, S=120, off=0.0):
    """Slices of the skull in the head frame.  -> C, L, F, A, B, E, z"""
    hf = head_frame(skel)
    K = np.array(HEAD_KEYS, float)
    z = np.linspace(K[0, 0], K[-1, 0], S)
    A = np.interp(z, K[::-1, 0], K[::-1, 1]) + off
    Bd = np.interp(z, K[::-1, 0], K[::-1, 2]) + off
    E = np.interp(z, K[::-1, 0], K[::-1, 3])
    ox = np.interp(z, K[::-1, 0], K[::-1, 4])
    C = (hf.o.reshape(1, 3) + z.reshape(S, 1) * hf.z
         + ox.reshape(S, 1) * hf.x)
    L = np.tile(hf.y.reshape(1, 3), (S, 1))
    F = np.tile(hf.x.reshape(1, 3), (S, 1))
    return C, L, F, A, Bd, E, z


def build_balaclava(acc, skel, an, uid=0):
    """Aramid knit hood: rib at the face opening, flat seams, neck skirt.

    Under a full-face helmet almost none of it is seen — but the sliver at the
    jaw and the skirt inside the collar are 4 to 9 px wide, and a hole there is
    the reason a helmeted figure reads as a mannequin head on a stick.
    """
    C, L, F, A, B, E, z = head_sections(skel, S=132, off=0.0016)
    S = len(C)
    N = 128
    hf = head_frame(skel)
    zz = np.tile(z.reshape(S, 1), (1, N))
    col = srgb('#101319')

    def disp(TH, VV, R):
        d = np.zeros_like(R)
        # the knit is 1.6 mm thick and it stretches thin over the crown
        d += 0.0016 - 0.0004 * sstep(0.04, 0.10, zz)
        # a brow ridge and an occiput under it
        d += 0.0035 * crest((zz - 0.012) / 0.030) * crest(
            _dth(TH, 0.5 * math.pi, R) / 0.055)
        d += 0.0040 * crest((zz + 0.020) / 0.055) * crest(
            _dth(TH, 1.5 * math.pi, R) / 0.060)
        # the ears, which the helmet's ear pockets have to clear
        for th0 in (0.0, math.pi):
            d += 0.0075 * crest((zz + 0.004) / 0.028) * crest(
                _dth(TH, th0, R) / 0.022)
        # the crown seam, and the two panel seams over the temples
        d += welt(_dth(TH, 0.5 * math.pi, R), w=0.0050, h=0.00055) * sstep(
            -0.10, -0.04, zz)
        for th0 in (0.0, math.pi):
            d += welt(_dth(TH, th0, R), w=0.0048, h=0.00050)
        # rib knit round the face opening
        d += 0.00075 * (0.5 + 0.5 * np.cos(TH * 46.0)) * crest((zz - 0.010) / 0.075)
        d += micro_crumple(TH * R, VV, uid=uid + 23, amp=0.00055, scale=0.55)
        return d

    # --- the eye opening is a real hole -----------------------------------
    P, TH, VV, R = loft(C, L, F, A, B, E, N, disp=disp)
    th = TH[0]
    dth_face = (th - 0.5 * math.pi + math.pi) % (2 * math.pi) - math.pi
    ZZ = zz
    ap = ((np.abs(dth_face) < 0.62)
          & (ZZ < 0.030) & (ZZ > -0.030))
    uv = np.stack([TH * R, VV], -1).reshape(-1, 2)
    i0 = acc.verts(P.reshape(-1, 3), uv=uv, base=(*col, 0.0),
                   aux=(0.0, 0.30, 0.0, uid), wear=(0.16, 0.10, 0.22, 0.05))
    IDX = i0 + np.arange(S * N).reshape(S, N)
    j1 = (np.arange(N) + 1) % N
    ok = ~(ap[:-1, :] | ap[:-1, j1] | ap[1:, j1] | ap[1:, :])
    Q = np.stack([IDX[:-1, :], IDX[:-1, j1], IDX[1:, j1], IDX[1:, :]], -1)
    acc.quads(Q[ok], MAT_KNIT, True)
    # the dark inside of the head, so the opening is a void and not a hole
    Pi, _TH, _VV, _R = loft(C, L, F, A * 0.965, B * 0.965, E, N,
                            disp=lambda TH, VV, R: np.zeros_like(R))
    i1 = acc.verts(Pi.reshape(-1, 3), uv=uv, base=(0.006, 0.006, 0.007, 0.0),
                   aux=(0.0, 0.0, 0.0, uid), wear=(0.0, 0.0, 0.0, 0.0))
    IDI = i1 + np.arange(S * N).reshape(S, N)
    acc.grid_faces(IDI, MAT_FOAM, True, wrap_u=True, flip=True)
    # the rolled rib edge round the opening
    bnd = ap[:-1, :] ^ ap[1:, :]
    return IDX


# --------------------------------------------------------------------------- #
# 20.  hands and gloves                                                         #
#                                                                               #
#  "Hands on the wheel at 3 m.  The SW cluster already resolves to macro        #
#   standard - gloves that do not match that standard will be the weak point    #
#   of the frame."                        -- the manifest, on driver_gloves     #
#                                                                               #
#  So the fingers are not posed, they are SOLVED.  Each phalanx is placed       #
#  tangent to the wrap circle of the grip it is holding: radius = grip radius   #
#  + finger radius, advance = 2*asin(l/2R) per bone.  Change the grip section   #
#  and the hand closes differently, which is what "hands working the wheel"     #
#  in the variation axes actually means.                                        #
# --------------------------------------------------------------------------- #

DIGITS = ("i", "m", "r", "l")
# MCP position in the hand's local frame: (x fore, y palm-out, z toward thumb)
MCP_Z = {"i": +0.0330, "m": +0.0090, "r": -0.0155, "l": -0.0390}
MCP_X = {"i": 0.0955, "m": 0.0985, "r": 0.0940, "l": 0.0855}
PHAL = {"i": (0.0345, 0.0215, 0.0195), "m": (0.0385, 0.0245, 0.0205),
        "r": (0.0355, 0.0230, 0.0195), "l": (0.0290, 0.0175, 0.0170)}


def _wrap_chain(mcp2, bar2, R, lens, wrap_dir=+1.0):
    """Joint positions of one finger wrapped on a circle.  All in the hand's
    local (x, y) plane.  -> list of 2-vectors, MCP first."""
    d = mcp2 - bar2
    ph = math.atan2(d[1], d[0])
    out = [mcp2.copy()]
    cur = ph
    for i, l in enumerate(lens):
        adv = 2.0 * math.asin(min(l / (2.0 * R), 0.999))
        cur = cur + wrap_dir * adv
        out.append(bar2 + R * np.array([math.cos(cur), math.sin(cur)]))
    return out


def _finger(put, dig, mcp2, bar2, Rw, r0, r1, uid, close, mat_back, mat_palm,
            col, sect_n=34, cap=None):
    lens = PHAL[dig]
    J2 = _wrap_chain(mcp2, bar2, Rw, [l * (0.35 + 0.65 * close) for l in lens])
    z = MCP_Z[dig]
    key = np.array([[p[0], p[1], z] for p in J2])
    # a real finger is not a straight chain: it converges toward the middle
    key[:, 2] += np.linspace(0.0, -0.0055 * np.sign(z + 1e-9) * abs(z) / 0.03, len(key))
    P = resample(catmull(key, 260), 96)
    T, L, N = axes_along(P, (0.0, 0.0, 1.0))
    S = len(P)
    tt = np.linspace(0, 1, S)
    # joint bulges at the three knuckles
    sarc = arclen(P)
    knots = [0.0]
    for l in lens:
        knots.append(knots[-1] + l * (0.35 + 0.65 * close))
    rad = (r0 + (r1 - r0) * tt)
    for k in knots[1:-1]:
        rad = rad + 0.0016 * crest((sarc - k) / 0.0095)
    rad = rad + 0.0011 * crest((sarc - knots[-1] * 0.995) / 0.010)
    M = sect_n
    th = np.linspace(0, 2 * math.pi, M, endpoint=False)
    TH = np.tile(th.reshape(1, M), (S, 1))
    RR = np.tile(rad.reshape(S, 1), (1, M))
    # the pad side is flatter and wider than the nail side
    flat = 1.0 - 0.20 * np.clip(np.sin(TH), 0, 1) ** 2
    wide = 1.0 + 0.14 * np.abs(np.cos(TH)) ** 2
    R = RR * flat * wide
    # external seams down both sides of the finger — the glove's signature
    for th0 in (0.0, math.pi):
        d = (TH - th0 + math.pi) % (2 * math.pi) - math.pi
        R = R + welt(d * R, w=0.0026, h=0.00105)
        R = R + stitch_field(d * R, gauge=0.0034, w=0.0011, h=0.00040,
                             s=np.tile(sarc.reshape(S, 1), (1, M)), pitch=0.0022)
    # flexion creases across the pad at each joint
    for k in knots[1:-1]:
        R = R - 0.00075 * crest((np.tile(sarc.reshape(S, 1), (1, M)) - k) / 0.0042) \
            * np.clip(np.sin(TH), 0, 1) ** 1.5
    # the silicone grip ribs on the pad side, 1.3 mm
    grip = (0.00042 * (0.5 + 0.5 * np.cos(
        2 * math.pi * np.tile(sarc.reshape(S, 1), (1, M)) / 0.0026))
        * np.clip(np.sin(TH), 0, 1) ** 2)
    R = R + grip
    Q = (P.reshape(S, 1, 3) + (R * np.cos(TH)).reshape(S, M, 1) * L.reshape(S, 1, 3)
         + (R * np.sin(TH)).reshape(S, M, 1) * N.reshape(S, 1, 3))
    uv = np.stack([TH * R, np.tile(sarc.reshape(S, 1), (1, M))], -1)
    IDX, QW = put(Q, uv.reshape(-1, 2), col, (0.0, 0.4, 0.0, uid),
                  (0.30, 0.16, 0.10, 0.05), mat_back, True)
    if cap is not None:
        cap(IDX, Q, -1, mat_back, col, (0.0, 0.4, 0.0, uid),
            (0.30, 0.16, 0.10, 0.05), +1)
        cap(IDX, Q, 0, mat_back, col, (0.0, 0.4, 0.0, uid),
            (0.30, 0.16, 0.10, 0.05), -1)
    return P, sarc


def build_glove(acc, skel, lab, an=DRIVER, uid=0):
    """One glove, solved onto its own grip."""
    sgn = +1.0 if lab == "l" else -1.0
    W = skel.J["wr_" + lab]
    M = skel.F["wr_" + lab]
    Gx, Gy, Gz = M[:, 0], M[:, 1], M[:, 2]
    # The hand frame, derived from the SAME rule the skeleton placed the wrist
    # with (see Skeleton._solve).  x = wrist -> knuckles, INBOARD across the
    # bar; y = out of the palm, at the bar; z = the bar axis, index uppermost.
    # The right hand's frame is left-handed on purpose -- it is the mirror of
    # the left one -- and `flip` reverses its winding on emit.
    hx = -sgn * Gy
    hy = Gx
    hz = Gz
    flip = (sgn < 0)
    O = W

    def place(Pl):
        Pl = np.asarray(Pl, float).reshape(-1, 3)
        return (O.reshape(1, 3) + Pl[:, :1] * hx + Pl[:, 1:2] * hy
                + Pl[:, 2:3] * hz)

    def put(Pg, uv, base, aux, wear, mat, wrap, flipx=False):
        sh = Pg.shape
        Q = place(Pg.reshape(-1, 3)).reshape(sh)
        i0 = acc.verts(Q.reshape(-1, 3), uv=uv, base=base, aux=aux, wear=wear)
        IDX = i0 + np.arange(sh[0] * sh[1]).reshape(sh[0], sh[1])
        acc.grid_faces(IDX, mat, True, wrap_u=wrap, flip=(flip ^ flipx))
        return IDX, Q

    def cap(IDX, Q, row, mat, base, aux, wear, outward):
        """Close a swept tube's end.  EVERY FINGERTIP WAS AN OPEN PIPE in the
        first cut, and the isolated-glove render showed daylight through the
        hand."""
        ring = IDX[row]
        pts = Q[row]
        c = pts.mean(0)
        # dome the cap out a little so a fingertip is round, not a lid
        nrm = unit(c - Q[row - outward].mean(0))
        ci = acc.verts((c + nrm * float(np.linalg.norm(pts - c, axis=1).mean())
                        * 0.62).reshape(1, 3),
                       uv=np.array([[0.0, 0.0]]), base=base, aux=aux, wear=wear)
        acc.fan(ci, ring, mat, True, flip=(flip ^ (outward < 0)))

    leather = srgb('#14171d')
    accent = srgb(SUIT_COL["accent"])
    # the grip bar, in the hand's own frame.  It IS the wheel's bar: the
    # x is the wrist-to-knuckle distance the skeleton used, the y is the bar
    # half-thickness plus the palm's.
    bar2 = np.array([an.hand_len * 0.49, WHEEL_GRIP_B + 0.0165])
    close = skel.pose.grip_l if lab == "l" else skel.pose.grip_r

    # --- the palm block ----------------------------------------------------
    S, N = 74, 96
    xs = np.linspace(-0.052, 0.100, S)          # -0.052 is up the gauntlet
    th = np.linspace(0, 2 * math.pi, N, endpoint=False)
    TH = np.tile(th.reshape(1, N), (S, 1))
    XX = np.tile(xs.reshape(S, 1), (1, N))
    tt = np.clip((XX + 0.052) / 0.152, 0, 1)
    # half-width (along z) and half-thickness (along y)
    hwid = np.interp(tt[:, 0], [0.0, 0.30, 0.36, 0.52, 0.78, 1.0],
                     [0.0345, 0.0330, 0.0300, 0.0355, 0.0430, 0.0455])
    hthk = np.interp(tt[:, 0], [0.0, 0.30, 0.36, 0.52, 0.78, 1.0],
                     [0.0250, 0.0235, 0.0185, 0.0175, 0.0180, 0.0165])
    expo = np.interp(tt[:, 0], [0.0, 0.4, 1.0], [2.6, 2.8, 3.1])
    R = superellipse(TH, hthk.reshape(S, 1), hwid.reshape(S, 1), expo.reshape(S, 1))
    # thenar and hypothenar eminences on the palm side (+y)
    palmside = np.clip(np.cos(TH), 0, 1) ** 1.5
    R = R + 0.0060 * palmside * crest((tt - 0.66) / 0.30) * np.clip(
        np.sin(TH + math.pi * 0.5) * 0 + np.clip(np.sin(TH), -1, 1) * 0 + 1.0, 0, 1) * 0
    thenar = crest((tt - 0.70) / 0.26) * crest((np.sin(TH) - 0.75) / 0.55)
    hypo = crest((tt - 0.68) / 0.28) * crest((np.sin(TH) + 0.75) / 0.55)
    R = R + (0.0068 * thenar + 0.0044 * hypo) * palmside
    # knuckle relief across the back (-y)
    backside = np.clip(-np.cos(TH), 0, 1) ** 1.5
    for dg in DIGITS:
        zz = MCP_Z[dg]
        ang = math.atan2(zz, -0.016)
        d = (TH - (math.pi - ang) + math.pi) % (2 * math.pi) - math.pi
        R = R + 0.0032 * backside * crest((tt - 0.955) / 0.10) * crest(d / 0.34)
    # the gauntlet flares
    R = R + 0.0060 * crest((tt - 0.02) / 0.16)
    # external seam down each side of the hand
    for th0 in (math.pi * 0.5, math.pi * 1.5):
        d = (TH - th0 + math.pi) % (2 * math.pi) - math.pi
        R = R + welt(d * R, w=0.0030, h=0.00110) * crest((tt - 0.62) / 0.55)
    # the silicone grip print: chevrons on the palm
    chev = (0.00045 * (0.5 + 0.5 * np.cos(2 * math.pi *
                                          (XX * 1.0 + np.abs(TH - math.pi * 0.5) * 0.010)
                                          / 0.0028)) * palmside
            * crest((tt - 0.70) / 0.34))
    R = R + chev
    # wrist crease and the cuff strap trough
    R = R - 0.0016 * crest((tt - 0.335) / 0.045)
    Rax = R * np.cos(TH)
    Q = np.stack([XX,
                  R * np.cos(TH),
                  R * np.sin(TH)], -1)
    uv = np.stack([TH * R, XX], -1)
    PIDX, PQ = put(Q, uv.reshape(-1, 2), (*leather, hash01(lab, uid)),
                   (0.0, 0.45, 0.0, uid), (0.34, 0.18, 0.12, 0.06),
                   MAT_LEATHER, True)
    cap(PIDX, Q, -1, MAT_GRIP, (*leather, hash01(lab, uid)),
        (0.0, 0.45, 0.0, uid), (0.34, 0.18, 0.12, 0.06), +1)
    cap(PIDX, Q, 0, MAT_KNIT, (*srgb(SUIT_COL["cuff"]), 0.0),
        (0.0, 0.3, 0.0, uid), (0.2, 0.2, 0.0, 0.05), -1)

    # --- the four fingers --------------------------------------------------
    for dg in DIGITS:
        rf = an.fing_r[dg] * 0.99
        Rw = 0.0198 + rf
        mcp2 = np.array([MCP_X[dg], 0.0060])
        _finger(put, dg, mcp2, bar2, Rw, rf, rf * 0.80, uid, close,
                MAT_LEATHER, MAT_GRIP, (*leather, hash01(dg, uid)), cap=cap)

    # --- the thumb: wraps the other way, over the front of the grip --------
    tmc, tp, td, tr = an.thumb
    base3 = np.array([0.052, 0.012, 0.0335])
    k1 = base3 + np.array([0.030, 0.020, 0.014])
    k2 = k1 + np.array([0.024, 0.014, -0.006])
    k3 = k2 + np.array([0.016, -0.004, -0.010])
    key = np.array([base3, k1, k2, k3])
    P = resample(catmull(key, 220), 74)
    T, L, N = axes_along(P, (0.0, 0.0, 1.0))
    S2 = len(P); M2 = 34
    th2 = np.linspace(0, 2 * math.pi, M2, endpoint=False)
    TH2 = np.tile(th2.reshape(1, M2), (S2, 1))
    sarc = arclen(P)
    rad = np.interp(sarc / sarc[-1], [0, 0.35, 0.62, 0.85, 1.0],
                    [tr * 1.30, tr * 1.06, tr * 1.00, tr * 0.94, tr * 0.72])
    rad = rad + 0.0016 * crest((sarc - sarc[-1] * 0.40) / 0.010)
    RR = np.tile(rad.reshape(S2, 1), (1, M2))
    for th0 in (0.0, math.pi):
        d = (TH2 - th0 + math.pi) % (2 * math.pi) - math.pi
        RR = RR + welt(d * RR, w=0.0028, h=0.00105)
    Q2 = (P.reshape(S2, 1, 3)
          + (RR * np.cos(TH2)).reshape(S2, M2, 1) * L.reshape(S2, 1, 3)
          + (RR * np.sin(TH2)).reshape(S2, M2, 1) * N.reshape(S2, 1, 3))
    uv2 = np.stack([TH2 * RR, np.tile(sarc.reshape(S2, 1), (1, M2))], -1)
    TIDX, TQ = put(Q2, uv2.reshape(-1, 2), (*leather, hash01("t", uid)),
                   (0.0, 0.4, 0.0, uid), (0.36, 0.18, 0.14, 0.05),
                   MAT_LEATHER, True)
    cap(TIDX, Q2, -1, MAT_LEATHER, (*leather, hash01("t", uid)),
        (0.0, 0.4, 0.0, uid), (0.36, 0.18, 0.14, 0.05), +1)

    # --- the gauntlet closure strap and its pull tab ----------------------
    _glove_strap(put, uid, accent)
    # --- the knitted inner cuff ------------------------------------------
    S3, N3 = 14, 96
    xs3 = np.linspace(-0.062, -0.048, S3)
    th3 = np.linspace(0, 2 * math.pi, N3, endpoint=False)
    TH3 = np.tile(th3.reshape(1, N3), (S3, 1))
    XX3 = np.tile(xs3.reshape(S3, 1), (1, N3))
    R3 = superellipse(TH3, 0.0250, 0.0340, 2.5) + 0.0012 + \
        0.0009 * (0.5 + 0.5 * np.cos(TH3 * 44.0))
    Q3 = np.stack([XX3, R3 * np.cos(TH3), R3 * np.sin(TH3)], -1)
    put(Q3, np.stack([TH3 * R3, XX3], -1).reshape(-1, 2),
        (*srgb(SUIT_COL["cuff"]), 0.0), (0.0, 0.3, 0.0, uid),
        (0.20, 0.24, 0.05, 0.05), MAT_KNIT, True)

    # --- the brand on the cuff -------------------------------------------
    frm = Frame(place(np.array([[-0.020, -0.0295, 0.0]]))[0],
                place(np.array([[1.0, -0.0295, 0.0]]))[0]
                - place(np.array([[0.0, -0.0295, 0.0]]))[0],
                None,
                place(np.array([[0.0, -1.0, 0.0]]))[0]
                - place(np.array([[0.0, 0.0, 0.0]]))[0])
    text_flat(acc, "MERIDIAN", frm, 0.0058, MAT_EMB, depth=0.00040,
              tracking=0.16, base=(*srgb(BRANDS["MERIDIAN"][1]), 0.0),
              aux=(0.0, 0.95, 0.0, uid))
    if lab == "r":
        # the biometric sensor pod, right hand only
        fr2 = Frame(place(np.array([[0.086, -0.020, 0.030]]))[0],
                    hx, None, -hy)
        prof = np.array([(0.0, 0.0), (0.0060, 0.0), (0.0072, -0.0016),
                         (0.0072, -0.0040), (0.0000, -0.0050)], float)
        revolve(acc, prof, fr2, 28, MAT_RUBBER,
                base=(0.020, 0.020, 0.023, 0.0), aux=(0.0, 0.5, 1.0, uid),
                wear=(0.2, 0.1, 0.0, 0.0))


def _glove_strap(put, uid, accent):
    """The hook-and-loop wrist strap: a doubled webbing band, a folded-back
    tab, and the stitched keeper it threads through."""
    S, N = 30, 60
    xs = np.linspace(-0.030, -0.006, S)
    th = np.linspace(0, 2 * math.pi, N, endpoint=False)
    TH = np.tile(th.reshape(1, N), (S, 1))
    XX = np.tile(xs.reshape(S, 1), (1, N))
    R = superellipse(TH, 0.0258, 0.0348, 2.6) + 0.0024
    R = R + 0.00035 * (0.5 + 0.5 * np.cos(TH * 90.0))
    # the strap does not close all the way round: it stops at an overlap
    Q = np.stack([XX, R * np.cos(TH), R * np.sin(TH)], -1)
    put(Q, np.stack([TH * R, XX], -1).reshape(-1, 2), (0.024, 0.025, 0.029, 0.0),
        (0.0, 0.35, 0.0, uid), (0.25, 0.20, 0.05, 0.15), MAT_WEBBING, True)
    # the folded pull tab: a doubled webbing loop lying BACK along the cuff,
    # 22 x 14 mm, not the 26 mm flat blade the first cut stood off the wrist
    nu2, nv2 = 18, 12
    u = np.linspace(0.0, 1.0, nu2)
    v = np.linspace(-1.0, 1.0, nv2)
    UU, VV = np.meshgrid(u, v, indexing='ij')
    ang = -0.55 + UU * 1.25
    rr = 0.0374 + 0.0052 * np.sin(math.pi * np.clip(UU * 1.15, 0, 1))
    x = -0.0225 - UU * 0.0075
    y = rr * np.cos(ang) * 0.0 + (0.0364 + 0.0060 * np.sin(math.pi * UU))
    z = VV * 0.0070 + 0.0180
    Q2 = np.stack([x, y * np.cos(0.30) - z * np.sin(0.30) * 0.0,
                   z * np.cos(0.30) + 0.0], -1)
    put(Q2, np.stack([UU * 0.022, VV * 0.007], -1).reshape(-1, 2),
        (0.020, 0.021, 0.024, 0.0), (0.0, 0.35, 0.0, uid),
        (0.30, 0.22, 0.05, 0.15), MAT_WEBBING, False)


# --------------------------------------------------------------------------- #
# 21.  boots                                                                    #
# --------------------------------------------------------------------------- #

def build_boot(acc, skel, lab, an=DRIVER, uid=0):
    """Thin-soled suede driving boot.

    "Barely visible in the footwell, but the footwell is modelled (CI_footwell)
     and an empty one is worse than a cheap boot."   -- the manifest.
    """
    sgn = +1.0 if lab == "l" else -1.0
    A = skel.J["ank_" + lab]
    M = skel.F["ank_" + lab]
    fz = M[:, 2]                       # along the foot, toward the toe
    fy = M[:, 0]                       # across
    fx = np.cross(fy, fz)
    O = A

    def place(Pl):
        Pl = np.asarray(Pl, float).reshape(-1, 3)
        return (O.reshape(1, 3) + Pl[:, :1] * fz + Pl[:, 1:2] * fy
                + Pl[:, 2:3] * fx)

    def put(Pg, uv, base, aux, wear, mat, wrap, flipx=False):
        sh = Pg.shape
        Q = place(Pg.reshape(-1, 3)).reshape(sh)
        i0 = acc.verts(Q.reshape(-1, 3), uv=uv, base=base, aux=aux, wear=wear)
        IDX = i0 + np.arange(sh[0] * sh[1]).reshape(sh[0], sh[1])
        acc.grid_faces(IDX, mat, True, wrap_u=wrap, flip=((sgn < 0) ^ flipx))
        return IDX

    L = an.foot_len
    S, N = 96, 76
    xs = np.linspace(-0.075, L * 0.86, S)
    tt = (xs + 0.075) / (L * 0.86 + 0.075)
    th = np.linspace(0, 2 * math.pi, N, endpoint=False)
    TH = np.tile(th.reshape(1, N), (S, 1))
    XX = np.tile(xs.reshape(S, 1), (1, N))
    TT = np.tile(tt.reshape(S, 1), (1, N))
    hw = np.interp(tt, [0.0, 0.18, 0.34, 0.52, 0.78, 0.93, 1.0],
                   [0.0400, 0.0430, 0.0455, 0.0490, 0.0470, 0.0380, 0.0240])
    hh = np.interp(tt, [0.0, 0.18, 0.34, 0.52, 0.78, 0.93, 1.0],
                   [0.0620, 0.0560, 0.0450, 0.0360, 0.0320, 0.0270, 0.0180])
    cz = np.interp(tt, [0.0, 0.30, 0.55, 1.0], [0.040, 0.006, -0.010, -0.014])
    R = superellipse(TH, hw.reshape(S, 1), hh.reshape(S, 1), 2.9)
    # the sole is FLAT: a boot is not a tube
    Zc = R * np.sin(TH) + cz.reshape(S, 1)
    Yc = R * np.cos(TH)
    sole_z = -0.030 - 0.004 * TT
    Zc = np.maximum(Zc, sole_z)
    # lace panel valley down the instep
    lace = crest(((TH - math.pi * 0.5 + math.pi) % (2 * math.pi) - math.pi) / 0.32)
    Zc = Zc - 0.0035 * lace * crest((TT - 0.42) / 0.44)
    # heel counter and toe cap, both stitched panels standing proud
    prox = 0.0016 * crest((TT - 0.10) / 0.14) + 0.0014 * crest((TT - 0.92) / 0.10)
    Zc = Zc + prox * np.sin(TH) * 0.0
    Q = np.stack([XX, Yc, Zc], -1)
    put(Q, np.stack([TH * R, XX], -1).reshape(-1, 2),
        (0.030, 0.032, 0.038, 0.0), (0.0, 0.30, 0.0, uid),
        (0.30, 0.34, 0.06, 0.10), MAT_LEATHER, True)
    # the sole: a thin plate with a lugged edge
    S2, N2 = 60, 34
    u2 = np.linspace(0.02, 0.99, S2)
    v2 = np.linspace(-1, 1, N2)
    U2, V2 = np.meshgrid(u2, v2, indexing='ij')
    xw = np.interp(U2, [0.0, 0.18, 0.34, 0.52, 0.78, 0.93, 1.0],
                   [0.0400, 0.0430, 0.0455, 0.0490, 0.0470, 0.0380, 0.0240])
    Xs = -0.075 + U2 * (L * 0.86 + 0.075)
    Ys = V2 * xw
    Zs = -0.030 - 0.004 * U2 - 0.0075 * (1.0 - V2 ** 2) ** 0.4
    Zs = Zs + 0.0010 * np.cos(2 * math.pi * Xs / 0.012)
    put(np.stack([Xs, Ys, Zs], -1),
        np.stack([Ys, Xs], -1).reshape(-1, 2), (0.012, 0.012, 0.014, 0.0),
        (0.0, 0.25, 1.0, uid), (0.55, 0.40, 0.05, 0.0), MAT_RUBBER, False,
        flipx=True)
    # laces: two flat ribbons crossing the instep, five crossings
    for k in range(5):
        u = 0.44 + k * 0.098
        p0 = np.array([-0.075 + u * (L * 0.86 + 0.075), -0.030,
                       np.interp(u, [0, 1], [0.010, -0.014]) + 0.020])
        p1 = np.array([-0.075 + (u + 0.075) * (L * 0.86 + 0.075), 0.030,
                       np.interp(u + 0.075, [0, 1], [0.010, -0.014]) + 0.018])
        for a, b in ((p0, p1), (p0 * np.array([1, -1, 1]),
                                p1 * np.array([1, -1, 1]))):
            P = np.linspace(a, b, 10)
            T, Lx, Nn = axes_along(P, (0, 0, 1.0))
            sect = rr_section(0.0032, 0.0009, 2.4, 18)
            sh = (len(P), 18)
            X = np.tile(sect[:, 0].reshape(1, 18), (len(P), 1))
            Y = np.tile(sect[:, 1].reshape(1, 18), (len(P), 1))
            Qp = (P.reshape(-1, 1, 3) + X[..., None] * Lx.reshape(-1, 1, 3)
                  + Y[..., None] * Nn.reshape(-1, 1, 3))
            put(Qp, np.stack([X, np.tile(arclen(P).reshape(-1, 1), (1, 18))],
                             -1).reshape(-1, 2),
                (0.020, 0.021, 0.024, 0.0), (0.0, 0.4, 0.0, uid),
                (0.4, 0.3, 0.0, 0.1), MAT_WEBBING, True)
    # the heel pull loop
    P = np.array([[-0.070, -0.018, 0.030], [-0.086, 0.0, 0.048],
                  [-0.070, 0.018, 0.030]])
    P = resample(catmull(P, 60), 20)
    T, Lx, Nn = axes_along(P, (0, 0, 1.0))
    sect = rr_section(0.0075, 0.0013, 2.6, 24, edge_boost=0.2)
    X = np.tile(sect[:, 0].reshape(1, 24), (len(P), 1))
    Y = np.tile(sect[:, 1].reshape(1, 24), (len(P), 1))
    Qp = (P.reshape(-1, 1, 3) + X[..., None] * Lx.reshape(-1, 1, 3)
          + Y[..., None] * Nn.reshape(-1, 1, 3))
    put(Qp, np.stack([X, np.tile(arclen(P).reshape(-1, 1), (1, 24))],
                     -1).reshape(-1, 2), (*srgb(SUIT_COL["accent"]), 0.0),
        (0.0, 0.3, 0.0, uid), (0.4, 0.3, 0.0, 0.2), MAT_WEBBING, True)


# --------------------------------------------------------------------------- #
# 22.  the helmet                                                               #
#                                                                               #
#  "209 px at 3.0 m through a 21 mm lens at the hairpin station.  The tear-off  #
#   stack on the visor and the raking reflection across it are the two things   #
#   that make a helmet look like it is being worn rather than displayed.        #
#   Invented livery only."                 -- the manifest, on driver_helmet    #
#                                                                               #
#  1.339 mm per pixel over a 0.29 m shell.  Everything below is a measurement:  #
#     shell wall               3.4 mm     2.5 px   -> the aperture edge is MESH #
#     visor                    3.0 mm     2.2 px                                #
#     tear-off film            0.25 mm    0.19 px  -> the STACK is 2.9 mm       #
#     tear-off tab            18 x 12 mm   13 px   -> unmissable, so six of     #
#                                                     them are individually     #
#                                                     placed and one is bent    #
#     chin grille bar          2.4 mm      1.8 px                               #
#     pivot screw head         5.0 mm      3.7 px                               #
#     livery pinstripe         1.6 mm      1.2 px  -> analytic SDF, not a mesh  #
#                                                     edge and not a texture    #
# --------------------------------------------------------------------------- #

HELM_KEYS = [                # z, half-width(lateral), half-depth(fore-aft), exp, x-offset
    (+0.1520, 0.0180, 0.0200, 2.2, -0.004),
    (+0.1400, 0.0520, 0.0570, 2.3, -0.005),
    (+0.1200, 0.0840, 0.0930, 2.4, -0.006),
    (+0.0900, 0.1055, 0.1180, 2.5, -0.006),
    (+0.0500, 0.1195, 0.1345, 2.6, -0.004),
    (+0.0000, 0.1258, 0.1430, 2.7,  0.000),
    (-0.0400, 0.1268, 0.1452, 2.8,  0.004),
    (-0.0800, 0.1240, 0.1445, 2.9,  0.009),
    (-0.1100, 0.1175, 0.1420, 3.0,  0.013),
    (-0.1400, 0.1060, 0.1360, 3.0,  0.016),
    (-0.1650, 0.0920, 0.1255, 2.9,  0.017),
]
SHELL_T = 0.0034
LINER_T = 0.0215


def _helm_rim_z(phi):
    """The bottom edge of the shell, as a function of azimuth from the front."""
    c = np.cos(phi)
    return (-0.1650 + 0.0385 * (1.0 - np.clip(c, -1, 1)) * 0.5
            + 0.0090 * np.clip(-c, 0, 1))


def _helm_profile(z):
    K = np.array(HELM_KEYS, float)
    zk = K[::-1, 0]
    return (np.interp(z, zk, K[::-1, 1]), np.interp(z, zk, K[::-1, 2]),
            np.interp(z, zk, K[::-1, 3]), np.interp(z, zk, K[::-1, 4]))


def helm_surface(PHI, SS, off=0.0):
    """-> (x, y, z) in the HEAD FRAME.  PHI is azimuth from the FRONT, positive
    to the driver's left; SS runs 0 at the crown to 1 at the bottom rim."""
    zc = 0.1520
    zr = _helm_rim_z(PHI)
    g = 0.5 - 0.5 * np.cos(math.pi * np.clip(SS, 0, 1))
    g = g ** 0.94
    Z = zc + (zr - zc) * g
    a, b, e, ox = _helm_profile(Z)
    # theta measured from the LEFT in the section, so phi=0 (front) is theta=pi/2
    TH = math.pi * 0.5 - PHI
    R = superellipse(TH, a, b, e) + off
    Y = R * np.cos(TH)                       # driver's left
    X = R * np.sin(TH) + ox                  # forward
    return X, Y, Z


def _aperture_q(PHI, Z):
    """< 1 inside the visor aperture.  A superellipse in (phi, z)."""
    p0 = 1.255                                # 71.9 deg each side
    zc = -0.0420 - 0.0070 * np.cos(np.clip(PHI, -1.6, 1.6) * 1.15)
    zh = 0.0305 + 0.0030 * np.cos(np.clip(PHI, -1.6, 1.6) * 2.0)
    return (np.abs(PHI / p0) ** 3.4 + np.abs((Z - zc) / zh) ** 2.1)


def _chin_q(PHI, Z):
    """< 1 inside the chin intake."""
    return (np.abs(PHI / 0.320) ** 3.6
            + np.abs((Z + 0.1330) / 0.0185) ** 3.0)


def _livery_sdf(PHI, Z):
    """Three signed distance fields, in metres, positive INSIDE the band.

    Sharp-edged livery with zero image textures and zero dependence on mesh
    density: the shader thresholds these with a 0.4 mm smoothstep, so the
    colour break lands within a third of a screen pixel of the true curve.
    """
    ap = np.abs(PHI) / math.pi
    # THE DESIGN HAS TO BE WHERE THE LENS IS.  The first cut ran the sweep from
    # z = -0.073 at the front, which is BEHIND the visor and the tear-off stack
    # -- the whole design was hidden by the one part of the helmet that is not
    # painted.  Everything now lives on the shell ABOVE the aperture, which is
    # what a 21 mm lens at 3 m actually sees of a helmet in a cockpit.
    #
    # A: the amber sweep, starting just over the brow and rising to the crown
    #    at the back.  50 mm at the front, 90 mm at the back.
    cen = 0.0140 + 0.0620 * ap ** 0.80
    hw = 0.0250 + 0.0200 * ap
    A = hw - np.abs(Z - cen)
    # B: the bone pinstripe riding 12 mm above the sweep, 20 mm wide
    cenb = cen + hw + 0.0165
    B = 0.0100 - np.abs(Z - cenb)
    # C: the ARDENT brow line, 12 mm, right on the aperture's top edge
    cenc = -0.0060 - 0.0080 * np.cos(np.clip(PHI, -1.7, 1.7) * 1.1)
    C = 0.0060 - np.abs(Z - cenc)
    C = np.minimum(C, 0.045 - np.abs(np.abs(PHI) - 0.80))
    return A, B, C


def _liv_ch(x):
    """Pack a signed distance in metres into a 0..1 attribute channel.
    0.5 is the boundary; one channel unit is 0.040 m."""
    return 0.5 + np.clip(np.asarray(x, float), -0.020, 0.020) * 25.0


def build_helmet(acc, skel, an=DRIVER, uid=0):
    """-> dict of the frames other things bolt to (tether posts, chin
    connector, ear positions)."""
    hf = head_frame(skel)
    O, HX, HY, HZ = hf.o, hf.x, hf.y, hf.z

    def to_world(X, Y, Z):
        return (O.reshape(*([1] * (np.ndim(X))), 3)
                + X[..., None] * HX + Y[..., None] * HY + Z[..., None] * HZ)

    N, S = 512, 264
    phi = (np.linspace(0.0, 2.0 * math.pi, N, endpoint=False) + math.pi) \
        % (2.0 * math.pi) - math.pi
    ss = np.linspace(0.0, 1.0, S)
    PHI = np.tile(phi.reshape(1, N), (S, 1))
    SS = np.tile(ss.reshape(S, 1), (1, N))
    X, Y, Z = helm_surface(PHI, SS)
    qa = _aperture_q(PHI, Z)
    qc = _chin_q(PHI, Z)

    # ---- snap the row nearest each aperture edge exactly onto it ----------
    for q_fn in (_aperture_q, _chin_q):
        for col in range(N):
            qcol = q_fn(PHI[:, col], Z[:, col])
            inside = qcol < 1.0
            if not inside.any():
                continue
            idx = np.where(inside)[0]
            for edge in (idx[0] - 1, idx[-1] + 1):
                if edge < 1 or edge >= S - 1:
                    continue
                lo, hi = ss[edge], ss[edge + (1 if edge < idx[0] else -1)]
                for _ in range(26):
                    mid = 0.5 * (lo + hi)
                    xx, yy, zz = helm_surface(np.array([phi[col]]),
                                              np.array([mid]))
                    if q_fn(np.array([phi[col]]), zz)[0] < 1.0:
                        hi = mid
                    else:
                        lo = mid
                SS[edge, col] = 0.5 * (lo + hi)
    X, Y, Z = helm_surface(PHI, SS)
    qa = _aperture_q(PHI, Z)
    qc = _chin_q(PHI, Z)
    cut = (qa < 1.0) | (qc < 1.0)

    # ---- surface relief that is not worth a separate object ---------------
    d = np.zeros_like(Z)
    # the raised eyebrow over the aperture and the step down into it
    d += 0.0022 * crest((np.sqrt(np.maximum(qa, 0)) - 1.14) / 0.16)
    d -= 0.0016 * crest((np.sqrt(np.maximum(qa, 0)) - 1.02) / 0.05)
    # THE TWO TOP INTAKE DUCTS.  The first cut put a 7.5 mm raised ring round a
    # 3 mm dish, which rendered as two white crescents with a dark stud in the
    # middle -- it read as a scar, not as a duct.  A duct is a FAIRING that
    # tapers away downstream with a SLOT at its leading edge, so that is what
    # this is: a 5 mm teardrop 0.34 rad x 44 mm with an 11 mm slot at the front
    # of it.
    for sgn in (+1.0, -1.0):
        du = (PHI - sgn * 0.44) / 0.30
        dv = (Z - 0.1030) / 0.030
        taper = 1.0 + 0.55 * np.clip(-dv, 0.0, 1.5)      # tail runs aft
        r = np.sqrt(du * du + (dv / taper) ** 2)
        d += 0.0052 * crest(r) ** 1.15
        slot = np.sqrt(((PHI - sgn * 0.44) / 0.150) ** 2
                       + ((Z - 0.1200) / 0.0105) ** 2)
        d -= 0.0110 * crest(slot) ** 0.55
    # the rear exhaust louvres
    for k in (-1, 0, 1):
        r = np.abs(Z - (0.0620 + k * 0.0175))
        m = crest((np.abs(PHI) - math.pi) / 0.55)
        d -= 0.0030 * crest(r / 0.0055) * m
    # the rear aero spoiler: a real step, 14 mm proud at its trailing edge
    sp = crest((np.abs(PHI) - math.pi) / 0.85) * crest((Z + 0.0620) / 0.0330)
    d += 0.0140 * sp ** 1.25
    # the shallow centre channel over the crown
    d -= 0.0018 * crest(Z / 0.20) * crest(np.abs(PHI) / 0.22) * (Z > 0.06)
    # the moulded ear pockets
    for sgn in (+1.0, -1.0):
        r = np.sqrt(((PHI - sgn * math.pi * 0.5) / 0.34) ** 2
                    + ((Z + 0.0450) / 0.038) ** 2)
        d += 0.0026 * crest(r / 1.0)
    # a helmet is hand-laid: it is not a perfect surface
    d += 0.00016 * (fbm2(PHI * 9.5, Z * 105.0, seed=717) - 0.5) * 2.0

    X2, Y2, Z2 = helm_surface(PHI, SS, off=0.0)
    NRM = np.stack([X2, Y2, Z2], -1)
    ctr = np.array([0.004, 0.0, 0.010])
    NRM = unit(NRM - ctr.reshape(1, 1, 3))
    P = np.stack([X2, Y2, Z2], -1) + NRM * d[..., None]

    A, B, Cc = _livery_sdf(PHI, Z)
    liv = np.stack([_liv_ch(A), _liv_ch(B), _liv_ch(Cc),
                    np.zeros_like(A)], -1).reshape(-1, 4)
    aux = np.stack([np.clip(np.abs(d) * 120.0, 0, 1),
                    np.full_like(d, 0.4),
                    np.clip(sstep(0.05, 0.16, Z) * 0.0 + (Z > 0.075) * 1.0, 0, 1),
                    np.full_like(d, uid)], -1).reshape(-1, 4)
    wear = np.stack([np.clip(0.10 + 0.35 * sstep(-0.02, -0.13, Z), 0, 1),
                     np.clip(0.14 + 0.34 * sstep(0.02, -0.15, Z), 0, 1),
                     np.clip(0.05 + 0.30 * crest((np.sqrt(np.maximum(qa, 0)) - 1.1)
                                                 / 0.35), 0, 1),
                     np.full_like(d, 0.18)], -1).reshape(-1, 4)

    W = to_world(P[..., 0], P[..., 1], P[..., 2])
    uv = np.stack([PHI * 0.13, Z], -1).reshape(-1, 2)
    i0 = acc.verts(W.reshape(-1, 3), uv=uv, base=(*srgb(LIVERY["shell"]), 0.0),
                   aux=aux, wear=wear, liv=liv)
    IDX = i0 + np.arange(S * N).reshape(S, N)
    j1 = (np.arange(N) + 1) % N
    ok = ~(cut[:-1, :] | cut[:-1, j1] | cut[1:, j1] | cut[1:, :])
    Q = np.stack([IDX[:-1, :], IDX[:-1, j1], IDX[1:, j1], IDX[1:, :]], -1)
    acc.quads(Q[ok], MAT_PAINT, True)

    # ---- the shell wall at every cut edge and at the bottom rim -----------
    def wall(mask, matid, depth=SHELL_T, inward=0.0):
        """Extrude the boundary of `mask` inward to make a real edge."""
        bnd = np.zeros_like(mask)
        bnd[:-1, :] |= mask[1:, :] ^ mask[:-1, :]
        bnd[1:, :] |= mask[1:, :] ^ mask[:-1, :]
        bnd[:, :] |= mask[:, j1] ^ mask
        bnd[:, j1] |= mask[:, j1] ^ mask
        bnd &= ~mask
        # build a wall ring per column run - approximate but watertight enough
        rows, cols = np.where(bnd)
        if not len(rows):
            return
        Pin = (np.stack([X2, Y2, Z2], -1) + NRM * (d[..., None] - depth)
               - NRM * inward)
        Win = to_world(Pin[..., 0], Pin[..., 1], Pin[..., 2])
        i1 = acc.verts(Win[rows, cols], uv=uv.reshape(S, N, 2)[rows, cols],
                       base=(0.010, 0.010, 0.011, 0.0),
                       aux=(0.0, 0.2, 0.0, uid), wear=(0.3, 0.2, 0.0, 0.0))
        lut = -np.ones((S, N), np.int64)
        lut[rows, cols] = i1 + np.arange(len(rows))
        # quads between adjacent boundary cells, in both grid directions
        for da, db in ((0, 1), (1, 0)):
            r2 = rows + da; c2 = (cols + db) % N
            good = (r2 < S) & (lut[np.clip(r2, 0, S - 1), c2] >= 0)
            if not good.any():
                continue
            a0 = IDX[rows[good], cols[good]]
            a1 = IDX[r2[good], c2[good]]
            b0 = lut[rows[good], cols[good]]
            b1 = lut[r2[good], c2[good]]
            acc.quads(np.stack([a0, a1, b1, b0], -1), matid, False)

    wall(qa < 1.0, MAT_CARBON)
    wall(qc < 1.0, MAT_CARBON)

    # ---- the interior: liner, cheek pads, and a dark void -----------------
    Sl, Nl = 96, 160
    phl = (np.linspace(0.0, 2 * math.pi, Nl, endpoint=False) + math.pi) \
        % (2 * math.pi) - math.pi
    ssl = np.linspace(0.012, 0.995, Sl)
    PL = np.tile(phl.reshape(1, Nl), (Sl, 1))
    SL = np.tile(ssl.reshape(Sl, 1), (1, Nl))
    XL, YL, ZL = helm_surface(PL, SL, off=-LINER_T)
    WL = to_world(XL, YL, ZL)
    i2 = acc.verts(WL.reshape(-1, 3),
                   uv=np.stack([PL * 0.11, ZL], -1).reshape(-1, 2),
                   base=(0.0090, 0.0088, 0.0092, 0.0), aux=(0.0, 0.0, 0.0, uid),
                   wear=(0.25, 0.30, 0.15, 0.0))
    ILN = i2 + np.arange(Sl * Nl).reshape(Sl, Nl)
    acc.grid_faces(ILN, MAT_FOAM, True, wrap_u=True, flip=True)

    # ---- the visor -------------------------------------------------------
    posts = _helmet_visor(acc, to_world, uid)
    # ---- hardware, aero, decals ------------------------------------------
    out = _helmet_hardware(acc, skel, to_world, hf, uid)
    _helmet_decals(acc, to_world, uid)
    _chin_grille(acc, to_world, uid)
    return out


def _visor_surface(PHI, SS, off):
    """The visor is a separate shell, 2.0 mm outboard of the helmet's."""
    return helm_surface(PHI, SS, off=off)


def _helmet_visor(acc, to_world, uid):
    """3 mm visor plus six tear-offs, each an individually placed film."""
    Nv, Sv = 260, 74
    p0 = 1.395
    phi = np.linspace(-p0, p0, Nv)
    zt = np.linspace(0.0, 1.0, Sv)
    PHI = np.tile(phi.reshape(1, Nv), (Sv, 1))
    # visor outline: taller than the aperture, in the same family of curves
    zc = -0.0420 - 0.0070 * np.cos(np.clip(PHI, -1.6, 1.6) * 1.15)
    zh = (0.0400 + 0.0035 * np.cos(np.clip(PHI, -1.6, 1.6) * 2.0)) * \
        np.clip(1.0 - (np.abs(PHI) / p0) ** 5.0, 0.02, 1.0) ** 0.30
    ZZ = zc + (np.tile(zt.reshape(Sv, 1), (1, Nv)) * 2.0 - 1.0) * zh

    def surf(off):
        zcr = _helm_rim_z(PHI)
        g = np.clip((0.1520 - ZZ) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
        ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
        X, Y, Z = helm_surface(PHI, ss, off=off)
        return np.stack([X, Y, ZZ * 0.0 + Z], -1)

    for k, (off, mat, base, thick) in enumerate((
            (0.0020, MAT_VISOR, (0.0090, 0.0094, 0.0112, 0.0), 0.0030),)):
        A = surf(off)
        Bq = surf(off + thick)
        for Pg, flip in ((Bq, False), (A, True)):
            Wp = to_world(Pg[..., 0], Pg[..., 1], Pg[..., 2])
            i0 = acc.verts(Wp.reshape(-1, 3),
                           uv=np.stack([PHI * 0.13, Pg[..., 2]], -1).reshape(-1, 2),
                           base=base, aux=(0.0, 0.5, 0.0, uid),
                           wear=(0.22, 0.10, 0.30, 0.0))
            I = i0 + np.arange(Sv * Nv).reshape(Sv, Nv)
            acc.grid_faces(I, mat, True, flip=flip)
            if not flip:
                topA, botA = I[0], I[-1]
                leftA, rightA = I[:, 0], I[:, -1]
                keep = (I, Wp)
        # rim of the visor: join the two skins all the way round
        Wa = to_world(A[..., 0], A[..., 1], A[..., 2])
        Wb = to_world(Bq[..., 0], Bq[..., 1], Bq[..., 2])
        ia = acc.verts(np.vstack([Wa[0], Wa[-1], Wa[:, 0], Wa[:, -1]]),
                       base=base, aux=(0.0, 0.5, 0.0, uid))
        ib = acc.verts(np.vstack([Wb[0], Wb[-1], Wb[:, 0], Wb[:, -1]]),
                       base=base, aux=(0.0, 0.5, 0.0, uid))
        n = Nv + Nv + Sv + Sv
        seg = [(0, Nv), (Nv, Nv), (2 * Nv, Sv), (2 * Nv + Sv, Sv)]
        for s0, ln in seg:
            a = ia + s0 + np.arange(ln - 1)
            acc.quads(np.stack([a, a + 1, ib + s0 + np.arange(ln - 1) + 1,
                                ib + s0 + np.arange(ln - 1)], -1), mat, False)

    # ---- the tear-off stack ----------------------------------------------
    #  Six films.  Each is a little smaller than the one under it, each is
    #  offset 0.55 mm outboard, and each has its own pull tab on the left
    #  edge, fanned so no two tabs are parallel.  The top one has a dog-eared
    #  corner because the driver has already caught it once with a glove.
    for k in range(5):
        off = 0.0052 + k * 0.00042
        shrink = 1.0 - 0.013 * (4 - k)
        Zk = zc + (np.tile(zt.reshape(Sv, 1), (1, Nv)) * 2.0 - 1.0) * zh * shrink
        Pk = np.zeros((Sv, Nv, 3))
        zcr = _helm_rim_z(PHI * shrink)
        g = np.clip((0.1520 - Zk) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
        ssk = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
        Xk, Yk, Zk2 = helm_surface(PHI * shrink, ssk, off=off)
        dogear = np.zeros_like(Xk)
        if k == 4:
            r = np.sqrt(((PHI + p0 * shrink) / 0.20) ** 2
                        + ((np.tile(zt.reshape(Sv, 1), (1, Nv)) - 1.0) / 0.22) ** 2)
            dogear = 0.0075 * crest(r / 1.0) ** 1.2
        Wk = to_world(Xk, Yk, Zk2)
        NN = unit(np.stack([Xk, Yk, Zk2], -1)
                  - np.array([0.004, 0.0, 0.010]).reshape(1, 1, 3))
        Wk = Wk + to_world(NN[..., 0] * dogear, NN[..., 1] * dogear,
                           NN[..., 2] * dogear) - to_world(
            np.zeros_like(dogear), np.zeros_like(dogear), np.zeros_like(dogear))
        i0 = acc.verts(Wk.reshape(-1, 3),
                       uv=np.stack([PHI * 0.13, Zk2], -1).reshape(-1, 2),
                       base=(0.86, 0.87, 0.86, 0.0),
                       aux=(0.0, 0.0, (4 - k) / 4.0, uid),
                       wear=(0.10 + 0.14 * (4 - k), 0.08, 0.20, 0.0))
        I = i0 + np.arange(Sv * Nv).reshape(Sv, Nv)
        acc.grid_faces(I, MAT_TEAROFF, True)
        # the pull tab: a flap folded out of the film's left edge
        _tearoff_tab(acc, to_world, PHI[0, 0] * shrink, zc[0, 0], zh[0, 0] * shrink,
                     off, k, uid)
    return None


def _tearoff_tab(acc, to_world, phi_edge, zc0, zh0, off, k, uid):
    nu, nv = 14, 10
    u = np.linspace(0.0, 1.0, nu)
    v = np.linspace(-1.0, 1.0, nv)
    U, V = np.meshgrid(u, v, indexing='ij')
    fan = math.radians(-14.0 + k * 5.5)
    ph = phi_edge - U * 0.145
    zz = zc0 + V * 0.0090 + U * math.tan(fan) * 0.030
    zcr = _helm_rim_z(ph)
    g = np.clip((0.1520 - zz) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
    ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
    X, Y, Z = helm_surface(ph, ss, off=off + U * 0.0075 * (0.4 + 0.6 * U))
    W = to_world(X, Y, Z)
    i0 = acc.verts(W.reshape(-1, 3), uv=np.stack([U * 0.02, V * 0.01], -1).reshape(-1, 2),
                   base=(0.94, 0.95, 0.94, 0.0), aux=(0.0, 0.0, (4 - k) / 4.0, uid),
                   wear=(0.25, 0.20, 0.10, 0.0))
    I = i0 + np.arange(nu * nv).reshape(nu, nv)
    acc.grid_faces(I, MAT_TEAROFF, True)


def _helmet_hardware(acc, skel, to_world, hf, uid):
    """Pivot plates, tether posts, edge beading, chin curtain, top sliders."""
    out = {"posts": {}, "ear": {}}

    def at(phi, z, off=0.0):
        zcr = _helm_rim_z(np.array([phi]))
        g = np.clip((0.1520 - z) / max(0.1520 - zcr[0], 1e-6), 0.0, 1.0)
        ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
        X, Y, Z = helm_surface(np.array([phi]), ss, off=off)
        p = np.array([X[0], Y[0], Z[0]])
        n = unit(p - np.array([0.004, 0.0, 0.010]))
        return p, n

    # --- visor pivot plates ------------------------------------------------
    for sgn in (+1.0, -1.0):
        p, n = at(sgn * 1.505, -0.0330, 0.0060)
        o = to_world(np.array([p[0]]), np.array([p[1]]), np.array([p[2]]))[0]
        nw = (to_world(np.array([n[0]]), np.array([n[1]]), np.array([n[2]]))[0]
              - to_world(np.zeros(1), np.zeros(1), np.zeros(1))[0])
        nw = unit(nw)
        fr = Frame(o, unit(np.cross(np.array([0.0, 0.0, 1.0]), nw)), None, nw)
        prof = np.array([(0.0, 0.0), (0.0190, 0.0), (0.0212, -0.0014),
                         (0.0212, -0.0042), (0.0182, -0.0056),
                         (0.0000, -0.0056)], float)
        revolve(acc, prof, fr, 56, MAT_HARDWARE, base=(0.045, 0.046, 0.050, 0.0),
                aux=(0.0, 0.55, 0.5, uid), wear=(0.35, 0.18, 0.0, 0.0))
        knurl_ring(acc, Frame(fr.o + nw * 0.0006, fr.x, None, nw), 0.0212,
                   0.0016, 34, 0.00040, MAT_HARDWARE, (0.045, 0.046, 0.050, 0.0),
                   (0.0, 0.55, 0.5, uid))
        for a in (0.0, 2.094, 4.189):
            q = fr.o + (fr.x * math.cos(a) + fr.y * math.sin(a)) * 0.0138
            hex_head(acc, Frame(q + nw * 0.0012, fr.x, None, nw), 0.0050,
                     0.0022, MAT_HARDWARE, base=(0.070, 0.070, 0.075, 0.0),
                     aux=(0.0, 0.75, 0.0, uid))
        out["ear"]["l" if sgn > 0 else "r"] = fr

    # --- tether posts ------------------------------------------------------
    for sgn in (+1.0, -1.0):
        p, n = at(sgn * 2.62, -0.0560, 0.0020)
        o = to_world(np.array([p[0]]), np.array([p[1]]), np.array([p[2]]))[0]
        nw = unit(to_world(np.array([n[0]]), np.array([n[1]]), np.array([n[2]]))[0]
                  - to_world(np.zeros(1), np.zeros(1), np.zeros(1))[0])
        fr = Frame(o, unit(np.cross(np.array([0.0, 0.0, 1.0]), nw)), None, nw)
        prof = np.array([(0.0, 0.0), (0.0105, 0.0), (0.0105, -0.0024),
                         (0.0060, -0.0034), (0.0060, -0.0120),
                         (0.0092, -0.0120), (0.0092, -0.0158),
                         (0.0000, -0.0158)], float)
        revolve(acc, prof, Frame(o + nw * 0.0158, fr.x, None, nw), 44,
                MAT_HARDWARE, base=(0.085, 0.085, 0.090, 0.0),
                aux=(0.0, 0.65, 0.5, uid), wear=(0.30, 0.15, 0.0, 0.0))
        out["posts"]["l" if sgn > 0 else "r"] = Frame(o + nw * 0.0130, fr.x,
                                                      None, nw, 0.006)

    # --- the rubber edge bead all the way round the bottom rim -------------
    Nb = 300
    phb = np.linspace(-math.pi, math.pi, Nb)
    zb = _helm_rim_z(phb)
    Xb, Yb, Zb = helm_surface(phb, np.ones(Nb) * 0.9985, off=-0.0012)
    Wb = to_world(Xb, Yb, Zb)
    Wb = np.vstack([Wb, Wb[:1]])
    T, L, Nn = axes_along(Wb, hf.z)
    sect = rr_section(0.0038, 0.0026, 2.4, 26)
    sweep_section(acc, Wb, L, Nn, sect, MAT_RUBBER,
                  base=(0.0095, 0.0095, 0.0100, 0.0), aux=(0.0, 0.2, 1.0, uid),
                  wear=(0.30, 0.30, 0.0, 0.10), uid=uid)

    # --- the chin curtain --------------------------------------------------
    nu, nv = 40, 16
    u = np.linspace(-0.95, 0.95, nu)
    v = np.linspace(0.0, 1.0, nv)
    U, V = np.meshgrid(u, v, indexing='ij')
    phc = U * 1.15
    zcur = _helm_rim_z(phc) - V * 0.030
    Xc, Yc, Zc2 = helm_surface(phc, np.ones_like(phc) * 0.999, off=-0.0035)
    Xc = Xc * (1.0 - 0.10 * V); Yc = Yc * (1.0 - 0.10 * V)
    Wc = to_world(Xc, Yc, zcur)
    i0 = acc.verts(Wc.reshape(-1, 3),
                   uv=np.stack([U * 0.10, V * 0.03], -1).reshape(-1, 2),
                   base=(0.012, 0.012, 0.014, 0.0), aux=(0.0, 0.25, 0.0, uid),
                   wear=(0.20, 0.35, 0.10, 0.05))
    I = i0 + np.arange(nu * nv).reshape(nu, nv)
    acc.grid_faces(I, MAT_KNIT, True)
    return out


def _chin_grille(acc, to_world, uid):
    """Six vertical bars, 2.4 mm across, and the plenum behind them."""
    for k in range(6):
        ph = -0.268 + k * 0.1072
        nv = 12
        v = np.linspace(0.0, 1.0, nv)
        zz = -0.1520 + v * 0.0380
        X, Y, Z = helm_surface(np.full(nv, ph), np.zeros(nv), off=0.0)
        zcr = _helm_rim_z(np.full(nv, ph))
        g = np.clip((0.1520 - zz) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
        ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
        X, Y, Z = helm_surface(np.full(nv, ph), ss, off=-0.0035)
        W = to_world(X, Y, Z)
        T, L, Nn = axes_along(W, (0.0, 0.0, 1.0))
        sect = rr_section(0.0012, 0.0026, 3.4, 20)
        sweep_section(acc, W, L, Nn, sect, MAT_HARDWARE,
                      base=(0.0135, 0.0136, 0.0145, 0.0),
                      aux=(0.0, 0.15, 0.5, uid),
                      wear=(0.20, 0.40, 0.0, 0.0), cap_ends=True, uid=uid,
                      smooth=False)
    # plenum wall behind the grille, so the intake is a hole into somewhere
    nu, nv = 34, 12
    U, V = np.meshgrid(np.linspace(-0.36, 0.36, nu),
                       np.linspace(0.0, 1.0, nv), indexing='ij')
    zz = -0.1560 + V * 0.0440
    zcr = _helm_rim_z(U)
    g = np.clip((0.1520 - zz) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
    ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
    X, Y, Z = helm_surface(U, ss, off=-0.0180)
    W = to_world(X, Y, Z)
    i0 = acc.verts(W.reshape(-1, 3),
                   uv=np.stack([U * 0.10, zz], -1).reshape(-1, 2),
                   base=(0.0060, 0.0060, 0.0065, 0.0), aux=(0.0, 0.0, 0.0, uid),
                   wear=(0.2, 0.4, 0.0, 0.0))
    I = i0 + np.arange(nu * nv).reshape(nu, nv)
    acc.grid_faces(I, MAT_FOAM, True)


def _helmet_decals(acc, to_world, uid):
    """Wordmarks and the racing number, as real extruded geometry.

    A 6 mm letter stroke is 4.5 screen pixels.  Painted-on lettering would have
    been a lie at this distance; these are meshes lying 0.35 mm proud of the
    clear coat, exactly like a laid decal under lacquer.
    """
    def bend_for(phi0, z0, cap, rot=0.0, off=0.0022):
        def bend(p2):
            p2 = np.asarray(p2, float).reshape(-1, 2)
            c, s = math.cos(rot), math.sin(rot)
            xx = p2[:, 0] * c - p2[:, 1] * s
            yy = p2[:, 0] * s + p2[:, 1] * c
            ph = phi0 + xx / 0.128
            zz = z0 + yy
            zcr = _helm_rim_z(ph)
            g = np.clip((0.1520 - zz) / np.maximum(0.1520 - zcr, 1e-6), 0.0, 1.0)
            ss = np.arccos(np.clip(1.0 - 2.0 * g ** (1 / 0.94), -1, 1)) / math.pi
            X, Y, Z = helm_surface(ph, ss, off=off)
            return to_world(X, Y, Z)
        return bend

    def put(text, phi0, z0, cap, col, rot=0.0, tracking=0.14):
        b = bend_for(phi0, z0, cap, rot)
        fr = Frame(b(np.array([[0.0, 0.0]]))[0],
                   b(np.array([[0.01, 0.0]]))[0] - b(np.array([[0.0, 0.0]]))[0],
                   None,
                   b(np.array([[0.0, 0.0]]))[0] - np.array([0.0, 0.0, 0.0]))
        text_flat(acc, text, fr, cap, MAT_PAINT, depth=0.00035,
                  tracking=tracking, base=(*col, 0.0),
                  aux=(0.0, 0.9, 0.0, uid), wear=(0.15, 0.10, 0.0, 0.1),
                  bend=b)

    put("ARDENT", +1.90, -0.0980, 0.0175, srgb(BRANDS["ARDENT"][1]))
    put("ARDENT", -1.90, -0.0980, 0.0175, srgb(BRANDS["ARDENT"][1]))
    put("VOLTAIC", +0.98, +0.0680, 0.0110, srgb(BRANDS["VOLTAIC"][1]))
    put("VOLTAIC", -0.98, +0.0680, 0.0110, srgb(BRANDS["VOLTAIC"][1]))
    put("9", math.pi, +0.0150, 0.0460, srgb(LIVERY["chevron"]))
    put("CIRCUIT VITRINE", 0.0, -0.1000, 0.0072,
        srgb(BRANDS["CIRCUIT VITRINE"][1]), tracking=0.20)
    put("ALTIS", math.pi, -0.1050, 0.0105, srgb(BRANDS["ALTIS"][1]))


# --------------------------------------------------------------------------- #
# 23.  the rest of what a driver is wearing                                     #
# --------------------------------------------------------------------------- #

def build_extras(acc, skel, hans, hn, helm, an=DRIVER, uid=0):
    """Arm restraints, the drink tube, the radio earpiece and its lead.

    ``crew_headset`` is this item's declared dependency and does not exist yet
    (there is no world/items/crew_headset.py).  A driver does not wear a crew
    headset anyway — he wears a moulded in-ear piece on a twisted pair that
    routes to the helmet's radio connector — so that is what is built, and the
    contract for it is published in ``anchors()['ear_l'|'ear_r']`` so the
    crew_headset agent can put a boom-mic version on the same frames.
    """
    # --- arm restraints ----------------------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        W = skel.J["wr_" + lab]
        M = skel.F["wr_" + lab]
        # ROUTE IT DOWN THE OUTSIDE OF THE FOREARM.  A straight line from the
        # wrist to the lap anchor goes clean through the steering wheel, and
        # in the first hand render two 20 mm webbing blades stood up through
        # the rim.  A real arm restraint follows the arm to the elbow and then
        # drops to the belt.
        E = skel.J["el_" + lab]
        fa0 = unit(W - E)
        out_dir = unit(np.cross(fa0, np.array([0.0, 0.0, 1.0]))) * sgn
        anc = np.array([-0.020, sgn * 0.170, -0.055])
        loop_c = W - fa0 * 0.052
        key = np.vstack([loop_c,
                         loop_c - fa0 * 0.10 + out_dir * 0.016,
                         E + out_dir * 0.028 - np.array([0.0, 0.0, 0.030]),
                         0.5 * (E + anc) + out_dir * 0.020
                         - np.array([0.0, 0.0, 0.030]),
                         anc])
        P = resample(catmull(key, 200), 90)
        T, L, Nn = axes_along(P, (0.0, 0.0, 1.0))
        sect = rr_section(0.0100, 0.0013, 2.4, 40, edge_boost=0.22)

        def disp(X, Y, SS, WW):
            rib = 0.00022 * (0.5 + 0.5 * np.cos(2 * math.pi * X / 0.0016))
            return np.zeros_like(X), rib * np.sign(Y + 1e-9)
        sweep_section(acc, P, L, Nn, sect, MAT_WEBBING, disp=disp,
                      base=(0.0165, 0.0170, 0.0200, 0.0), aux=(0.0, 0.3, 0.0, uid),
                      wear=(0.16, 0.20, 0.0, 0.25), cap_ends=True, uid=uid)
        # the wrist loop it is sewn to.  It goes ROUND THE FOREARM, so its
        # plane is normal to the forearm, not to the wheel: the first cut put
        # it in the wheel plane and it rendered as a hoop hanging in the air
        # beside the hand.
        th = np.linspace(0, 2 * math.pi, 56, endpoint=False)
        r = an.r_wrist + CLOTH.THICK + 0.0135
        fa = unit(W - skel.J["el_" + lab])
        e1 = unit(np.cross(fa, np.array([0.0, 0.0, 1.0])))
        e2 = np.cross(fa, e1)
        C0 = W - fa * 0.052
        ring = (C0.reshape(1, 3) + (r * np.cos(th)).reshape(-1, 1) * e1
                + (r * np.sin(th)).reshape(-1, 1) * e2)
        ring = np.vstack([ring, ring[:1]])
        T2, L2, N2 = axes_along(ring, M[:, 0])
        sweep_section(acc, ring, L2, N2, rr_section(0.0095, 0.0016, 2.5, 32,
                                                    edge_boost=0.2),
                      MAT_WEBBING, base=(0.0165, 0.0170, 0.0200, 0.0),
                      aux=(0.0, 0.3, 0.0, uid), wear=(0.20, 0.22, 0.0, 0.25),
                      uid=uid)
        _adjuster(acc, Frame(P[30], L[30], None, Nn[30]), 0.010, 0.0016, uid,
                  panel=0.5)

    # --- the drink tube ----------------------------------------------------
    hf = head_frame(skel)
    chin = hf.o + hf.x * 0.126 - hf.z * 0.118
    key = np.vstack([chin,
                     chin + np.array([-0.020, 0.055, -0.055]),
                     skel.J["c7"] + np.array([0.055, 0.130, -0.010]),
                     skel.J["t8"] + np.array([0.090, 0.150, -0.020]),
                     skel.J["t12"] + np.array([0.060, 0.155, -0.040])])
    P = resample(catmull(key, 260), 130)
    T, L, Nn = axes_along(P, (0.0, 0.0, 1.0))
    r = 0.0034 + 0.0008 * np.clip(1.0 - arclen(P) / 0.05, 0, 1)
    S = len(P); M2 = 22
    th = np.linspace(0, 2 * math.pi, M2, endpoint=False)
    RR = np.tile(r.reshape(S, 1), (1, M2))
    Q = (P.reshape(S, 1, 3)
         + (RR * np.cos(th)).reshape(S, M2, 1) * L.reshape(S, 1, 3)
         + (RR * np.sin(th)).reshape(S, M2, 1) * Nn.reshape(S, 1, 3))
    i0 = acc.verts(Q.reshape(-1, 3),
                   uv=np.stack([np.tile(th.reshape(1, M2) * 0.0035, (S, 1)),
                                np.tile(arclen(P).reshape(S, 1), (1, M2))],
                               -1).reshape(-1, 2),
                   base=(0.030, 0.031, 0.034, 0.0), aux=(0.0, 0.3, 1.0, uid),
                   wear=(0.15, 0.25, 0.0, 0.05))
    IDX = i0 + np.arange(S * M2).reshape(S, M2)
    acc.grid_faces(IDX, MAT_RUBBER, True, wrap_u=True)
    # the quick-release connector at the helmet end
    # the quick release, at the CHIN BAR where it plugs in.  The first cut put
    # a 13.6 mm polished cylinder at P[3], a third of the way down the neck,
    # and it rendered as a camera lens growing out of the driver's collar.
    fr = Frame(P[1], L[1], None, unit(P[0] - P[3]))
    prof = np.array([(0.0, 0.0), (0.0045, 0.0), (0.0045, -0.0055),
                     (0.0036, -0.0062), (0.0036, -0.0115), (0.0, -0.0115)],
                    float)
    revolve(acc, prof, fr, 24, MAT_RUBBER, base=(0.0125, 0.0128, 0.0140, 0.0),
            aux=(0.0, 0.2, 1.0, uid), wear=(0.2, 0.3, 0.0, 0.0))

    # --- earpieces and the radio lead --------------------------------------
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        # IN the ear, which means inside the helmet: nothing of it is ever
        # seen.  The first cut sat it 18 mm proud of the head in a skin colour
        # and it rendered as a pink pill on the side of the neck.
        e = hf.o + hf.y * (sgn * 0.0700) - hf.z * 0.0120 - hf.x * 0.0300
        fr = Frame(e, hf.x, None, hf.y * sgn)
        prof = np.array([(0.0, 0.0), (0.0050, 0.0004), (0.0058, -0.0026),
                         (0.0052, -0.0056), (0.0034, -0.0074),
                         (0.0000, -0.0082)], float)
        revolve(acc, prof, fr, 26, MAT_SILICONE,
                base=(0.055, 0.052, 0.050, 0.0), aux=(0.0, 0.2, 0.0, uid),
                wear=(0.1, 0.1, 0.0, 0.0))
        key = np.vstack([e + hf.y * (sgn * 0.006),
                         e + hf.y * (sgn * 0.020) - hf.z * 0.045,
                         skel.J["c7"] + np.array([0.0, sgn * 0.060, 0.010]),
                         skel.J["t8"] + np.array([-0.030, sgn * 0.070, 0.0])])
        Pc = resample(catmull(key, 200), 80)
        T2, L2, N2 = axes_along(Pc, (0.0, 0.0, 1.0))
        Mc = 14
        thc = np.linspace(0, 2 * math.pi, Mc, endpoint=False)
        rc = 0.0016 + 0.00028 * np.cos(arclen(Pc) / 0.0022 * 2 * math.pi)
        RC = np.tile(rc.reshape(-1, 1), (1, Mc))
        Qc = (Pc.reshape(-1, 1, 3)
              + (RC * np.cos(thc)).reshape(-1, Mc, 1) * L2.reshape(-1, 1, 3)
              + (RC * np.sin(thc)).reshape(-1, Mc, 1) * N2.reshape(-1, 1, 3))
        i1 = acc.verts(Qc.reshape(-1, 3),
                       uv=np.stack([np.tile(thc.reshape(1, Mc) * 0.0016,
                                            (len(Pc), 1)),
                                    np.tile(arclen(Pc).reshape(-1, 1), (1, Mc))],
                                   -1).reshape(-1, 2),
                       base=(0.020, 0.021, 0.024, 0.0), aux=(0.0, 0.4, 1.0, uid),
                       wear=(0.1, 0.2, 0.0, 0.0))
        IC = i1 + np.arange(len(Pc) * Mc).reshape(len(Pc), Mc)
        acc.grid_faces(IC, MAT_RUBBER, True, wrap_u=True)


# --------------------------------------------------------------------------- #
# 24.  the anchor contract                                                      #
# --------------------------------------------------------------------------- #

def anchors(skel, helm=None, hans=None, an=DRIVER):
    """Every frame anything attaches to.  See the module docstring."""
    A = {}
    hf = head_frame(skel)
    A["helmet"] = hf
    A["helmet_chin"] = Frame(hf.o + hf.x * 0.128 - hf.z * 0.112, hf.z, None,
                             hf.x, 0.030, "helmet_chin")
    for lab, sgn in (("l", +1.0), ("r", -1.0)):
        A["ear_" + lab] = Frame(hf.o + hf.y * (sgn * 0.0755) - hf.z * 0.010
                                - hf.x * 0.018, hf.x, None, hf.y * sgn,
                                0.014, "ear_" + lab)
        M = skel.F["wr_" + lab]
        A["wrist_" + lab] = Frame(skel.J["wr_" + lab], M[:, 0], None, M[:, 2],
                                  an.r_wrist + CLOTH.THICK, "wrist_" + lab)
        A["grip_" + lab] = skel.grip[lab]
        A["shoulder_" + lab] = Frame(skel.J["sh_" + lab],
                                     skel.F["sh_" + lab][:, 0], None,
                                     np.array([0.0, 0.0, 1.0]), an.r_delt,
                                     "shoulder_" + lab)
        Ma = skel.F["ank_" + lab]
        A["ankle_" + lab] = Frame(skel.J["ank_" + lab], Ma[:, 0], None,
                                  Ma[:, 2], an.r_ankle + CLOTH.THICK,
                                  "ankle_" + lab)
        A["sole_" + lab] = Frame(skel.J["ball_" + lab]
                                 - np.array([0.0, 0.0, 0.030]),
                                 np.array([1.0, 0.0, 0.0]), None,
                                 np.array([0.0, 0.0, 1.0]), an.foot_br * 0.5,
                                 "sole_" + lab)
        A["knee_" + lab] = Frame(skel.J["kn_" + lab], skel.F["kn_" + lab][:, 0],
                                 None, skel.F["kn_" + lab][:, 2], an.r_knee,
                                 "knee_" + lab)
        A["belt_" + lab] = Frame(np.array([-0.012, sgn * 0.215, -0.030]),
                                 np.array([1.0, 0.0, 0.0]), None,
                                 np.array([0.0, 0.0, 1.0]), 0.030,
                                 "belt_" + lab)
    nk = skel.J["neck"]
    A["collar"] = Frame(nk, skel.F["neck"][:, 0], None, skel.F["neck"][:, 2],
                        an.neck_r + CLOTH.THICK + 0.008, "collar")
    A["chest"] = Frame(*_frame_on_trunk(skel, 0.660, math.pi / 2), name="chest")
    A["back"] = Frame(*_frame_on_trunk(skel, 0.845, 1.5 * math.pi), name="back")
    A["crotch"] = Frame(np.array([0.118, 0.0, -0.128]),
                        np.array([1.0, 0.0, 0.0]), None,
                        np.array([0.0, 0.0, 1.0]), 0.040, "crotch")
    A["seat_back"] = Frame(skel.J["t8"] - np.array([0.135, 0.0, 0.0]),
                           np.array([1.0, 0.0, 0.0]), None,
                           np.array([0.0, 0.0, 1.0]), 0.20, "seat_back")
    A["wheel"] = skel.wheel
    if hans is not None:
        A["hans_yoke"] = Frame(hans.top, np.array([1.0, 0.0, 0.0]), None,
                               np.array([0.0, 0.0, 1.0]), 0.15, "hans_yoke")
    if helm is not None:
        for lab in ("l", "r"):
            if lab in helm.get("posts", {}):
                A["tether_" + lab] = helm["posts"][lab]
    return A


def _frame_on_trunk(skel, t0, th0):
    TS = trunk_sections(skel)
    P, Nn = _trunk_eval(TS, [t0], [th0], out=CLOTH.THICK)
    z = np.array([0.0, 0.0, 1.0])
    x = unit(np.cross(np.cross(Nn[0], z), Nn[0])) if abs(
        float(np.dot(Nn[0], z))) < 0.98 else np.array([1.0, 0.0, 0.0])
    return P[0], Nn[0], None, Nn[0]


# --------------------------------------------------------------------------- #
# 25.  build                                                                    #
# --------------------------------------------------------------------------- #

ALL_PARTS = ("hans", "harness", "suit", "balaclava", "gloves", "boots",
             "helmet", "extras")


class Driver:
    __slots__ = ("objs", "skel", "anchors", "pose", "coll", "package",
                 "ground_z", "stats")


def _coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def build(coll_name=ROOT_COLL, pose="hairpin_apex", an=DRIVER, uid=0,
          parts=ALL_PARTS, place=None, ground_xy=None, verbose=True):
    """Emit the figure.  -> Driver.

    ``place`` is a 4x4 taking the DRIVER FRAME into the world.  ``ground_xy``,
    if given, is a world (x, y) whose ``world_contract.world_ground_z`` is
    looked up and reported on every object as ``drv_world_ground_z`` — the
    figure itself never stands on the ground (he is bolted into a car), so he
    does not embed, but the value that was USED is recorded rather than assumed.
    """
    import time
    t0 = time.time()
    mats = materials()
    coll = _coll(coll_name)
    skel = solve(pose, an)
    TS = trunk_sections(skel)

    gz = None
    if ground_xy is not None and C is not None:
        z, owner = C.world_ground_z(np.array([ground_xy[0]]),
                                    np.array([ground_xy[1]]))
        gz = float(z[0])
        if verbose:
            print(f">> world_ground_z({ground_xy[0]:.2f}, {ground_xy[1]:.2f}) "
                  f"= {gz:.4f} m  (owner {owner[0]})")

    objs = []
    hans = harn = helm = None

    if "hans" in parts:
        a = Acc(PFX + "HANS")
        hans = build_hans(a, skel, mats, an, uid)
        o = a.emit(coll, mats, PFX + "HANS")
        if o:
            objs.append(o)
    if hans is None:
        hans = build_hans(Acc("_tmp"), skel, mats, an, uid)

    if "helmet" in parts:
        a = Acc(PFX + "Helmet")
        helm = build_helmet(a, skel, an, uid)
        o = a.emit(coll, mats, PFX + "Helmet")
        if o:
            objs.append(o)
    if helm is None:
        helm = build_helmet(Acc("_tmp"), skel, an, uid)

    if "harness" in parts:
        a = Acc(PFX + "Harness")
        harn = build_harness(a, skel, TS, hans, mats, an, uid)
        build_tethers(a, skel, hans, helm["posts"], uid)
        o = a.emit(coll, mats, PFX + "Harness")
        if o:
            objs.append(o)
    if harn is None:
        harn = build_harness(Acc("_tmp"), skel, TS, hans, mats, an, uid)

    if "suit" in parts:
        a = Acc(PFX + "Suit")
        build_suit(a, skel, TS, harn, hans, an, uid)
        o = a.emit(coll, mats, PFX + "Suit")
        if o:
            objs.append(o)
    if "balaclava" in parts:
        a = Acc(PFX + "Balaclava")
        build_balaclava(a, skel, an, uid)
        o = a.emit(coll, mats, PFX + "Balaclava")
        if o:
            objs.append(o)
    if "gloves" in parts:
        for lab in ("l", "r"):
            a = Acc(PFX + "Glove_" + lab.upper())
            build_glove(a, skel, lab, an, uid + (0 if lab == "l" else 1))
            o = a.emit(coll, mats, PFX + "Glove_" + lab.upper())
            if o:
                objs.append(o)
    if "boots" in parts:
        for lab in ("l", "r"):
            a = Acc(PFX + "Boot_" + lab.upper())
            build_boot(a, skel, lab, an, uid + (0 if lab == "l" else 1))
            o = a.emit(coll, mats, PFX + "Boot_" + lab.upper())
            if o:
                objs.append(o)
    if "extras" in parts:
        a = Acc(PFX + "Extras")
        build_extras(a, skel, hans, harn, helm, an, uid)
        o = a.emit(coll, mats, PFX + "Extras")
        if o:
            objs.append(o)

    if place is not None:
        from mathutils import Matrix
        Mw = Matrix([list(r) for r in np.asarray(place, float)])
        for o in objs:
            o.matrix_world = Mw @ o.matrix_world

    tris = 0
    for o in objs:
        o["drv_pose"] = skel.pose.name
        o["drv_item"] = "driver_figure"
        if gz is not None:
            o["drv_world_ground_z"] = gz
        tris += sum(max(len(p.vertices) - 2, 1) for p in o.data.polygons)

    d = Driver()
    d.objs = objs
    d.skel = skel
    d.anchors = anchors(skel, helm, hans, an)
    d.pose = skel.pose
    d.coll = coll
    d.package = PACKAGE
    d.ground_z = gz
    d.stats = {"objects": len(objs), "triangles": tris,
               "seconds": round(time.time() - t0, 1)}
    if verbose:
        print(f">> driver_figure: {len(objs)} objects, {tris} triangles, "
              f"{d.stats['seconds']} s")
        print(f">> head: roll {skel.head_roll_deg:+.2f} deg, "
              f"yaw {skel.head_yaw_deg:+.2f} deg, "
              f"pitch {skel.head_pitch_deg:+.2f} deg  "
              f"(lat {skel.pose.lat_g:+.2f} g, steer {skel.pose.steer_deg:+.1f} deg, "
              f"chassis roll {skel.pose.chassis_roll_deg:+.2f} deg)")
    return d


# --------------------------------------------------------------------------- #
# 26.  the cockpit proxy — TEST SCENE ONLY, and deliberately not DRV_-prefixed  #
# --------------------------------------------------------------------------- #
#
# The acceptance gate is run with --prefix DRV_, so none of this is measured as
# part of the item, and none of it is claimed as part of the item.  It exists so
# the macro render can be judged: a driver floating in space cannot be judged,
# because half of what makes a driver read is what he is wedged into.
#
# Its dimensions come out of PACKAGE, not out of round 1's CI_* interior, for
# the reason PACKAGE['round1_note'] states.

COCKPIT_PROXY = {
    "rim_above_hip_m": 0.335,
    "seat_pan_below_hip_m": 0.075,
    "headrest_behind_head_m": 0.145,
    "sidehead_half_gap_m": 0.180,
}


TUB_KEYS = [        # x, half-width, deck top z, floor z, section exponent
    (-0.90, 0.150, 0.560, -0.120, 2.6),
    (-0.72, 0.235, 0.545, -0.180, 2.9),
    (-0.55, 0.300, 0.430, -0.235, 3.1),
    (-0.38, 0.330, 0.398, -0.252, 3.3),
    (-0.10, 0.342, 0.362, -0.256, 3.5),
    (+0.20, 0.338, 0.350, -0.252, 3.6),
    (+0.50, 0.320, 0.340, -0.244, 3.5),
    (+0.80, 0.278, 0.318, -0.228, 3.3),
    (+1.10, 0.196, 0.256, -0.188, 3.1),
    (+1.40, 0.098, 0.150, -0.112, 2.8),
]


TUB_OPEN_HALF_ANGLE = 0.95      # rad, CONSTANT.  See build_cockpit_proxy.
TUB_OPEN_XC = 0.055
TUB_OPEN_XL = 0.480


def _tub_open_x(dth):
    """Fore and aft ends of the cockpit opening at a fixed angular offset.

    THE OPENING IS DEFINED THE OTHER WAY ROUND ON PURPOSE.  Defining it as
    "|theta| < a(x)" and cutting faces on the raw grid leaves a 12 mm stair all
    down the cockpit rim -- 9 screen pixels at 3 m, and it showed up in the
    first inspection render as a saw-tooth.  Snapping the theta of one vertex
    per row does not fix it either: the snapped vertex hops between two columns
    as the row advances, which turns the stair into a zigzag.

    So the ANGULAR edge is put exactly on grid columns (a constant half-angle,
    hence a dead-straight line down the tub) and only the FORE/AFT ends are
    snapped, in x, where the grid is dense and monotone.
    """
    k = np.clip(1.0 - (np.abs(dth) / TUB_OPEN_HALF_ANGLE) ** 3.226, 0.0, 1.0)
    half = TUB_OPEN_XL * np.sqrt(k)
    return TUB_OPEN_XC - half, TUB_OPEN_XC + half


def build_cockpit_proxy(coll, skel, mats, an=DRIVER, uid=0):
    """A survival-cell section, sized from PACKAGE.

    NOT the car.  The car is somebody else's item and round 1's MB_/CI_ cluster
    is the real one.  This exists so the macro render can be judged: the
    manifest's whole framing argument is "only the helmet, shoulders, upper arms
    and hands are ever visible ABOVE THE COCKPIT RIM", and without a rim at the
    right height there is nothing to judge that against.  Its rim sits at
    PACKAGE['cockpit_rim_above_hip_m'] = 0.335 m above the H-point.
    """
    a = Acc("PROXY_Cockpit")
    hf = head_frame(skel)
    K = np.array(TUB_KEYS, float)
    # 560 x 288 is 3.6 mm along the tub and 7.4 mm around it.  SNAPPING THE
    # BOUNDARY VERTEX WAS WORSE THAN NOT SNAPPING: when the nearest row index
    # changes between two columns the snapped vertex and its unsnapped
    # neighbour no longer share the boundary edge, and the rim grew a row of
    # spikes instead of a stair.  Resolution is the honest fix here -- this is
    # a proxy, not the item, and 3.6 mm is 2.7 screen pixels at 3 m.
    S, N = 560, 288
    x0 = np.linspace(K[0, 0], K[-1, 0], S)
    th = np.linspace(-math.pi, math.pi, N, endpoint=False)
    TH = np.tile(th.reshape(1, N), (S, 1))
    XX = np.tile(x0.reshape(S, 1), (1, N))
    dth = np.abs((TH - math.pi * 0.5 + math.pi) % (2 * math.pi) - math.pi)
    inside_th = dth[0] < TUB_OPEN_HALF_ANGLE - 1e-9
    xf, xr = _tub_open_x(dth[0])
    hw = np.interp(XX, K[:, 0], K[:, 1])
    zt = np.interp(XX, K[:, 0], K[:, 2])
    zb = np.interp(XX, K[:, 0], K[:, 3])
    ex = np.interp(XX, K[:, 0], K[:, 4])
    zc = (zt + zb) * 0.5
    hh = (zt - zb) * 0.5
    R = superellipse(TH, hw, hh, ex)
    # a monocoque is not a tube: it has a flat floor and a keel
    Y = R * np.cos(TH)
    Z = np.maximum(zc + R * np.sin(TH), zb)
    cut = (inside_th.reshape(1, N)
           & (XX > xf.reshape(1, N) + 1e-9) & (XX < xr.reshape(1, N) - 1e-9))

    def emit_skin(scale, flip, mat, base, wear):
        Ys = Y * scale
        Zs = zc + (Z - zc) * scale
        P = np.stack([XX, Ys, Zs], -1)
        i0 = a.verts(P.reshape(-1, 3),
                     uv=np.stack([TH * 0.30, XX], -1).reshape(-1, 2),
                     base=base, aux=(0.0, 0.45, 0.0, uid), wear=wear)
        I = i0 + np.arange(S * N).reshape(S, N)
        j1 = (np.arange(N) + 1) % N
        Q = np.stack([I[:-1, :], I[:-1, j1], I[1:, j1], I[1:, :]], -1)
        if flip:
            a.quads(Q.reshape(-1, 4)[:, ::-1], mat, True)
        else:
            ok = ~(cut[:-1, :] | cut[:-1, j1] | cut[1:, j1] | cut[1:, :])
            a.quads(Q[ok], mat, True)
        return I

    OUT = emit_skin(1.0, False, MAT_CARBON, (0.0095, 0.0096, 0.0104, 0.0),
                    (0.28, 0.30, 0.05, 0.10))
    INN = emit_skin(0.965, True, MAT_FOAM, (0.0075, 0.0074, 0.0078, 0.0),
                    (0.25, 0.35, 0.10, 0.0))
    # the rim wall: a real 12 mm edge round the cockpit opening
    j1 = (np.arange(N) + 1) % N
    bnd = np.zeros_like(cut)
    bnd[:-1] |= cut[1:] ^ cut[:-1]
    bnd[1:] |= cut[1:] ^ cut[:-1]
    bnd |= cut[:, j1] ^ cut
    bnd[:, j1] |= cut[:, j1] ^ cut
    bnd &= ~cut
    rr, cc = np.where(bnd)
    for da, db in ((0, 1), (1, 0)):
        r2 = np.clip(rr + da, 0, S - 1); c2 = (cc + db) % N
        good = bnd[r2, c2]
        if good.any():
            a.quads(np.stack([OUT[rr[good], cc[good]], OUT[r2[good], c2[good]],
                              INN[r2[good], c2[good]], INN[rr[good], cc[good]]],
                             -1), MAT_CARBON, False)

    # --- the padded coaming, on the ANALYTIC opening curve ------------------
    # It is what a real cockpit has, and it also covers the 7.4 mm stair the
    # face-cull leaves on the fore and aft ends of the opening.
    ncoam = 240
    tt = np.linspace(0.0, 2.0 * math.pi, ncoam, endpoint=False)
    dth_c = TUB_OPEN_HALF_ANGLE * np.sin(tt)
    xf_c, xr_c = _tub_open_x(dth_c)
    xc = np.where(np.cos(tt) >= 0.0, xr_c, xf_c)
    thc = math.pi * 0.5 + dth_c
    hwc = np.interp(xc, K[:, 0], K[:, 1])
    ztc = np.interp(xc, K[:, 0], K[:, 2])
    zbc = np.interp(xc, K[:, 0], K[:, 3])
    exc = np.interp(xc, K[:, 0], K[:, 4])
    zcc = (ztc + zbc) * 0.5
    hhc = (ztc - zbc) * 0.5
    rc = superellipse(thc, hwc, hhc, exc)
    Pc = np.stack([xc, rc * np.cos(thc), zcc + rc * np.sin(thc)], -1)
    Pc = np.vstack([Pc, Pc[:1]])
    Tc, Lc, Nc = axes_along(Pc, (0.0, 0.0, 1.0))
    sweep_section(a, Pc, Lc, Nc, rr_section(0.0180, 0.0135, 3.0, 40),
                  MAT_FOAM, base=(0.0110, 0.0110, 0.0118, 0.0),
                  aux=(0.0, 0.15, 0.0, uid), wear=(0.30, 0.35, 0.05, 0.0),
                  uid=uid)

    # --- headrest and the two side head restraints -------------------------
    for o, sz, mat in ((hf.o - hf.x * 0.175 - hf.z * 0.020, (0.080, 0.185, 0.110),
                        MAT_FOAM),
                       (hf.o + hf.y * 0.182 - hf.x * 0.045, (0.120, 0.052, 0.098),
                        MAT_FOAM),
                       (hf.o - hf.y * 0.182 - hf.x * 0.045, (0.120, 0.052, 0.098),
                        MAT_FOAM)):
        nu2, nv2 = 48, 30
        uu = np.linspace(0, 2 * math.pi, nu2, endpoint=False)
        vv = np.linspace(-1, 1, nv2)
        U2, V2 = np.meshgrid(uu, vv, indexing='ij')
        r = superellipse(U2, sz[0], sz[2], 3.4) * np.sqrt(
            np.clip(1 - V2 ** 2, 0, 1)) ** 0.30
        Q = np.stack([o[0] + r * np.cos(U2), o[1] + V2 * sz[1],
                      o[2] + r * np.sin(U2)], -1)
        i2 = a.verts(Q.reshape(-1, 3),
                     uv=np.stack([U2 * 0.05, V2 * 0.05], -1).reshape(-1, 2),
                     base=(0.0125, 0.0125, 0.0135, 0.0), aux=(0.0, 0.0, 0.0, uid),
                     wear=(0.30, 0.32, 0.0, 0.0))
        I2 = i2 + np.arange(nu2 * nv2).reshape(nu2, nv2)
        a.grid_faces(I2, mat, True, wrap_u=True)

    _proxy_wheel(a, skel, uid)
    return a.emit(coll, mats, "PROXY_Cockpit")


def _proxy_wheel(a, skel, uid):
    """Enough wheel for the hands to be gripping something.

    The real wheel is round 1's SW_* cluster, which the manifest calls out as
    already resolving to macro standard.  This is a stand-in at EXACTLY the
    package geometry the fingers were wrapped against: grip bar 44.2 x 35.0 mm,
    133 mm long, 112 mm off the wheel axis.  Change WHEEL_GRIP_A/B and both the
    bar and every finger that holds it move together.
    """
    W = skel.wheel
    Ws = skel.wheel_side
    # --- the rim: TWO ARCS, top and bottom, ending at the grips -----------
    # THE GRIPS ARE THE WIDEST PART OF THE WHEEL.  The first cut ran a closed
    # rim at 0.1345 outboard of grips at 0.112, so a 33 mm suede tube stood
    # between the camera and both hands and the fingers were invisible in every
    # render.  An F1 wheel is a yoke: two grips joined across the top and the
    # bottom, nothing outboard of them.
    for u0, u1 in ((0.40, math.pi - 0.40), (math.pi + 0.40, 2 * math.pi - 0.40)):
        nu = 80
        u = np.linspace(u0, u1, nu)
        r = superellipse(u, WHEEL_GRIP_OFF + 0.0040, 0.0905, 3.6)
        P = (W.o.reshape(1, 3) + (r * np.cos(u)).reshape(nu, 1) * Ws
             + (r * np.sin(u)).reshape(nu, 1) * W.z)
        T, L, Nn = axes_along(P, W.x)
        # suede over the carbon, not bare weave: at 6.8 mm the twill repeat on
        # a 33 mm tube reads as braided rope, which the first render showed.
        sweep_section(a, P, L, Nn, rr_section(0.0155, 0.0120, 3.0, 44),
                      MAT_GRIP, base=(0.0115, 0.0114, 0.0120, 0.0),
                      aux=(0.0, 0.25, 0.0, uid), wear=(0.35, 0.24, 0.10, 0.0),
                      cap_ends=True, uid=uid)
    # --- the centre plate, with the display bezel and the hub --------------
    nv = 20
    uu = np.linspace(0.0, 2 * math.pi, 72, endpoint=False)
    vv = np.linspace(0.0, 1.0, nv)
    U2, V2 = np.meshgrid(uu, vv, indexing='ij')
    rr = superellipse(U2, 0.0985, 0.0605, 3.4) * V2
    Q = (W.o.reshape(1, 1, 3)
         + (rr * np.cos(U2))[..., None] * Ws.reshape(1, 1, 3)
         + (rr * np.sin(U2))[..., None] * W.z.reshape(1, 1, 3)
         + (0.0060 * (1.0 - V2 ** 2))[..., None] * W.x.reshape(1, 1, 3))
    i0 = a.verts(Q.reshape(-1, 3),
                 uv=np.stack([U2 * 0.02, V2 * 0.06], -1).reshape(-1, 2),
                 base=(0.0080, 0.0081, 0.0088, 0.0), aux=(0.0, 0.5, 0.0, uid),
                 wear=(0.25, 0.20, 0.10, 0.0))
    I = i0 + np.arange(Q.shape[0] * nv).reshape(Q.shape[0], nv)
    a.grid_faces(I, MAT_CARBON, True, wrap_u=True)
    # the display, so the centre is not a blank slab
    fr = Frame(W.o + W.x * 0.0068, Ws, None, W.z)
    for (hw2, hh2, dep, mat, col) in ((0.0700, 0.0330, 0.0016, MAT_HARDWARE,
                                       (0.020, 0.020, 0.023, 0.0)),
                                      (0.0640, 0.0280, 0.0026, MAT_VISOR,
                                       (0.010, 0.011, 0.013, 0.0))):
        nu3 = 4
        th3 = np.linspace(0.0, 2 * math.pi, 48, endpoint=False)
        rr3 = superellipse(th3, hw2, hh2, 5.0)
        for lay in range(2):
            z3 = dep * lay
            Pp = (fr.o.reshape(1, 3) + (rr3 * np.cos(th3)).reshape(-1, 1) * fr.x
                  + (rr3 * np.sin(th3)).reshape(-1, 1) * fr.y
                  + fr.z * 0.0)
        Pp = (fr.o.reshape(1, 3) + (rr3 * np.cos(th3)).reshape(-1, 1) * Ws
              + (rr3 * np.sin(th3)).reshape(-1, 1) * W.z
              + W.x.reshape(1, 3) * dep)
        ctr = a.verts((fr.o + W.x * dep).reshape(1, 3),
                      base=col, aux=(0.0, 0.6, 0.5, uid))
        ii = a.verts(Pp, base=col, aux=(0.0, 0.6, 0.5, uid))
        a.fan(ctr, ii + np.arange(len(th3)), mat, False)
    # --- the two grips ------------------------------------------------------
    for lab in ("l", "r"):
        G = skel.grip[lab]
        Pg = np.linspace(G.o - G.z * WHEEL_GRIP_LEN * 0.5,
                         G.o + G.z * WHEEL_GRIP_LEN * 0.5, 44)
        T, L, Nn = axes_along(Pg, G.x)
        sect = rr_section(WHEEL_GRIP_B, WHEEL_GRIP_A, 2.8, 52)
        tt = np.linspace(0, 1, len(Pg)).reshape(-1, 1)

        def disp(X, Y, SS, WW, tt=tt):
            bulge = 1.0 + 0.09 * np.sin(math.pi * tt) ** 2
            rib = 0.00035 * (0.5 + 0.5 * np.cos(2 * math.pi * SS / 0.0060))
            return X * (bulge - 1.0), Y * (bulge - 1.0) + rib * np.sign(Y + 1e-9)
        sweep_section(a, Pg, L, Nn, sect, MAT_GRIP, disp=disp,
                      base=(0.0135, 0.0135, 0.0148, 0.0),
                      aux=(0.0, 0.2, 0.0, uid),
                      wear=(0.45, 0.25, 0.15, 0.0), cap_ends=True, uid=uid)


# --------------------------------------------------------------------------- #
# 27.  the test scene                                                           #
# --------------------------------------------------------------------------- #

SUN_ELEV_DEG = 12.5
SUN_BEARING_DEG = -58.0
SCENE_EXPOSURE_EV = -2.8      # measured; see build_test_scene()
GREY_CARD_LINEAR_AT_EV0 = 1.99
T4_STATION_S = 982.0          # the middle of T4, from circuit_spec's element table
KERB_CAM_Z = 0.850            # "kerb-height hairpin station on the INSIDE kerb
                              #  of T4 at z=+0.85, 21 mm" -- camera_model
HIP_ABOVE_ROAD = 0.260        # where this figure's H-point sits in a car


def procedural_world():
    """The contract sun.  Identical to tools/fix_audit_blend.procedural_world:
    Sky Texture at 12.5 deg elevation and -58 deg bearing, no external files."""
    try:
        import fix_audit_blend as FAB
        return FAB.procedural_world()
    except Exception as e:
        print(f"   (local sky: {e})")
    w = bpy.data.worlds.get("R2_ProceduralSky") or bpy.data.worlds.new(
        "R2_ProceduralSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    avail = {e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items}
    for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        if want in avail:
            sky.sky_type = want
            break
    for attr, val in (("sun_elevation", math.radians(SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(SUN_BEARING_DEG)),
                      ("sun_intensity", 0.85), ("sun_size", math.radians(0.545)),
                      ("altitude", 120.0), ("air_density", 1.35),
                      ("dust_density", 2.2), ("ozone_density", 1.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def _ground_patch(coll, mats, cx, cy, gz, r=9.0, n=64):
    """A disc of the racing surface under the rig, so the figure is lit by a
    real bounce and casts a shadow onto something.  Embedded BASE_EMBED_M
    below the ground datum so it can never float, per law 5."""
    a = Acc("PROXY_Ground")
    u = np.linspace(-r, r, n)
    X, Y = np.meshgrid(u, u, indexing='ij')
    if C is not None:
        Z, _own = C.world_ground_z((X + cx).ravel(), (Y + cy).ravel())
        Z = np.nan_to_num(Z, nan=gz).reshape(X.shape)
    else:
        Z = np.full_like(X, gz)
    Z = Z - 0.020
    P = np.stack([X + cx, Y + cy, Z], -1)
    i0 = a.verts(P.reshape(-1, 3),
                 uv=np.stack([X, Y], -1).reshape(-1, 2),
                 base=(0.0135, 0.0136, 0.0142, 0.0), aux=(0.0, 0.0, 0.0, 0.0),
                 wear=(0.3, 0.4, 0.1, 0.2))
    I = i0 + np.arange(n * n).reshape(n, n)
    a.grid_faces(I, MAT_RUBBER, True)
    return a.emit(coll, mats, "PROXY_Ground")


def build_test_scene(out_path, pose="hairpin_apex", uid=0, res=(3840, 2160),
                     samples=256):
    """The scene the acceptance gate and the macro render are run on."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 24
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    # THE CONTRACT SKY IS 3.5 STOPS HOT AND THAT IS A MEASUREMENT, NOT A TASTE.
    # A pure-diffuse 18 % grey card placed 1.2 m in front of CAM_DRV_MACRO under
    # tools/fix_audit_blend.procedural_world() renders at 1.99 linear.  It should
    # render at 0.18.  log2(0.18 / 1.99) = -3.47 stops.  Left at 0, every
    # material in this file -- Nomex at 0.013 albedo, carbon at 0.008, webbing
    # at 0.008 -- lands between 0.5 and 0.9 linear and AgX turns the whole
    # figure into pale clay, which is exactly what the first two macro renders
    # of this item looked like.  -3.2 is the 0.28 of a stop of headroom a
    # sunlit subject wants over a grey card.
    #
    # THIS IS A SCENE-LEVEL FINDING, NOT AN ITEM ONE: every item macro rendered
    # under that world is hot by the same amount.  Reported rather than
    # silently corrected; `rq render --exposure` can override it per job.
    sc.view_settings.exposure = SCENE_EXPOSURE_EV

    procedural_world()

    # --- where in the world -------------------------------------------------
    if C is not None:
        wx, wy, _wz = C.su_to_world(T4_STATION_S, -3.0)
        gz, owner = C.world_ground_z(np.array([wx]), np.array([wy]))
        gz = float(gz[0])
        head = float(C.centreline(T4_STATION_S)[2])
        print(f">> T4 station s={T4_STATION_S}: world ({wx:.2f}, {wy:.2f}), "
              f"ground z {gz:.4f} m, owner {owner[0]}, heading "
              f"{math.degrees(head):.1f} deg")
    else:
        wx, wy, gz, head = 0.0, 0.0, 0.0, 0.0

    heading_deg = math.degrees(head)
    M = seat_matrix(np.array([wx, wy, gz + HIP_ABOVE_ROAD]), heading_deg)

    mats = materials()
    d = build(pose=pose, uid=uid, place=M, ground_xy=(wx, wy))
    coll = _coll(ROOT_COLL)

    pc = _coll("DRV_Proxy")
    skel = d.skel
    ob = build_cockpit_proxy(pc, skel, mats)
    from mathutils import Matrix
    Mw = Matrix([list(r) for r in np.asarray(M, float)])
    if ob:
        ob.matrix_world = Mw @ ob.matrix_world
    _ground_patch(pc, mats, wx, wy, gz)

    # --- the camera the manifest specifies ----------------------------------
    A = d.anchors
    R3 = np.asarray(M, float)[:3, :3]
    T3 = np.asarray(M, float)[:3, 3]

    def w(p):
        return R3 @ np.asarray(p, float) + T3

    helmet = w(A["helmet"].o)
    gl = w(A["grip_l"].o); gr = w(A["grip_r"].o)
    aim = helmet * 0.52 + (gl + gr) * 0.5 * 0.48
    cams = []
    for name, bearing_off, rise in (("CAM_DRV_MACRO", 46.0, None),
                                    ("CAM_DRV_PROFILE", 104.0, None)):
        ang = math.radians(heading_deg + bearing_off)
        czw = gz + KERB_CAM_Z
        dz = czw - aim[2]
        rr = math.sqrt(max(NEAR_M ** 2 - dz * dz, 0.01))
        pos = np.array([aim[0] + rr * math.cos(ang), aim[1] + rr * math.sin(ang),
                        czw])
        cams.append(_camera(name, pos, aim, LENS_MM))
    # AN INSPECTION CAMERA, NOT A DELIVERABLE.  The manifest's own shot is a
    # 21 mm lens at 3 m, which puts the whole figure inside 523 px of a 3840 px
    # frame - correct for the film and useless for judging a seam.  This one is
    # 1.90 m on a 65 mm lens from above the left shoulder: the same 0.7 m of
    # figure across 2,180 px, which is 4.2 x the delivered pixel density, so
    # anything that survives here survives the master.
    ang = math.radians(heading_deg + 40.0)
    ins_aim = helmet * 0.50 + (gl + gr) * 0.5 * 0.50
    pos = np.array([ins_aim[0] + 2.12 * math.cos(ang),
                    ins_aim[1] + 2.12 * math.sin(ang),
                    ins_aim[2] + 0.58])
    cams.append(_camera("CAM_DRV_INSPECT", pos, ins_aim, 55.0))
    # and one on the left hand alone: 0.62 m on a 90 mm lens is 0.19 m of hand
    # across 2,050 px, 3.9 x the delivered density.  "Hands on the wheel at 3 m
    # ... gloves that do not match that standard will be the weak point of the
    # frame" -- the manifest, on driver_gloves.  This is where that is checked.
    hand_aim = w(A["grip_l"].o)
    hang = math.radians(heading_deg + 74.0)          # off his own left side
    cams.append(_camera("CAM_DRV_HAND",
                        np.array([hand_aim[0] + 0.52 * math.cos(hang),
                                  hand_aim[1] + 0.52 * math.sin(hang),
                                  hand_aim[2] + 0.20]), hand_aim, 90.0))
    sc.camera = bpy.data.objects[cams[0]]
    dist = np.linalg.norm(np.array(bpy.data.objects[cams[0]].location) - aim)
    print(f">> {cams[0]}: {dist:.4f} m from the aim point on a "
          f"{LENS_MM:.0f} mm lens  (manifest: {NEAR_M} m, {LENS_MM:.0f} mm)")
    print(f">> px_per_m at that distance = "
          f"{(RES_X_4K * LENS_MM / SENSOR_MM) / dist:.1f}")

    # --- report ------------------------------------------------------------
    print(f">> objects: {[o.name for o in d.objs]}")
    print(f">> anchors: {len(d.anchors)}")

    try:
        import fix_audit_blend as FAB
        FAB.save_clean(out_path)
    except Exception as e:
        print(f"   (save_clean unavailable: {e}) - saving directly")
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_path),
                                    relative_remap=False, compress=False)
    print(f">> saved {out_path} "
          f"({os.path.getsize(out_path) / 1048576:.1f} MB)")
    return d


def _camera(name, pos, aim, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.02
    cd.clip_end = 400.0
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    d = unit(np.asarray(aim, float) - np.asarray(pos, float))
    # Blender cameras look down -Z with +Y up
    z = -d
    x = unit(np.cross(np.array([0.0, 0.0, 1.0]), z))
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0.0, 0.0])
    y = np.cross(z, x)
    from mathutils import Matrix
    m = Matrix(((x[0], y[0], z[0], pos[0]),
                (x[1], y[1], z[1], pos[1]),
                (x[2], y[2], z[2], pos[2]),
                (0.0, 0.0, 0.0, 1.0)))
    ob.matrix_world = m
    return name


# --------------------------------------------------------------------------- #
# 28.  cli                                                                      #
# --------------------------------------------------------------------------- #

def _args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--pose", default="hairpin_apex")
    p.add_argument("--uid", type=int, default=0)
    p.add_argument("--out", default=os.path.join(HERE,
                                                 "driver_figure_test.blend"))
    p.add_argument("--res", type=int, nargs=2, default=[3840, 2160])
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--interface", default=None,
                   help="write the anchor contract out as json")
    return p.parse_args(argv)


def _dump_interface(d, path):
    out = {
        "item": "driver_figure",
        "frame": PACKAGE["frame"],
        "package": {k: v for k, v in PACKAGE.items()},
        "pose": d.pose.name,
        "head_solve": {"roll_deg": d.skel.head_roll_deg,
                       "yaw_deg": d.skel.head_yaw_deg,
                       "pitch_deg": d.skel.head_pitch_deg,
                       "law": "roll = chassis_roll*%.2f + lat_g*%.2f; "
                              "yaw = clamp(steer*%.2f, %.1f) + bias"
                              % (NECK_ROLL_FOLLOW, NECK_LOAD_LEAN,
                                 STEER_LEAD, STEER_LEAD_MAX)},
        "materials": MAT_NAMES,
        "parts": list(ALL_PARTS),
        "objects": [o.name for o in d.objs],
        "stats": d.stats,
        "anchors": {k: {"o": [float(x) for x in f.o],
                        "x": [float(x) for x in f.x],
                        "y": [float(x) for x in f.y],
                        "z": [float(x) for x in f.z],
                        "r": float(f.r)} for k, f in d.anchors.items()},
        "poses": {k: {s: getattr(v, s) for s in v.__slots__}
                  for k, v in POSES.items()},
    }
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f">> interface -> {path}")


def main():
    a = _args()
    if a.test:
        d = build_test_scene(a.out, pose=a.pose, uid=a.uid,
                             res=tuple(a.res), samples=a.samples)
        _dump_interface(d, a.interface or os.path.join(
            HERE, "driver_figure_interface.json"))
        print(">> STAGE RESULT: DRIVER_TEST_SCENE_BUILT")
    else:
        d = build(pose=a.pose, uid=a.uid)
        print(">> STAGE RESULT: DRIVER_BUILT")


if __name__ == "__main__":
    main()
