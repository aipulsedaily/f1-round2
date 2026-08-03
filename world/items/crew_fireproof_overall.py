#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crew_fireproof_overall.py — THE garment.  Item 134, wave 1, 18 dependants.

    manifest:  nearest_camera_m 10.0   lens 35 mm   onscreen_px_4k 653
               instances 110           hero True
    pixels:    px_per_m = (3840 * 35 / 36) / 10.0 = 373.33 px/m
               -> 1 screen pixel = 2.679 mm on this garment.

Everything at or above ~3 mm is a resolved feature and therefore has to be
MESH: seam welts (9 mm), topstitch beads (1.8 mm x 3.2 mm pitch), cuff ribs
(4.4 mm), collar thickness (2.6 mm), zip teeth, patch relief (1.2 mm),
waistband gathers (12 mm), and above all the FOLDS.

    "Nomex hangs stiffer than cotton - fewer, larger folds, and it holds a
     crease at the elbow and the back of the knee.  Get the fold LANGUAGE
     right once here and 110 figures inherit it."

===========================================================================
THE INTERFACE  (this item is a foundation; 18 items build on it and cannot
                ask questions.  Everything below is public and stable.)
===========================================================================

BODY / POSE
    Build(...)                  anthropometry.  BUILDS['regular'|'slight'|
                                'heavy'|'tall'|'short'|'broad'|'lean_tall'|
                                'stocky'] are the presets the crew draws from.
    POSES                       dict name -> Pose.  20 poses covering every
                                crew_* dependant: 'crouch_gun', 'kneel_l',
                                'kneel_r', 'carry_tyre_high', 'carry_tyre_low',
                                'jack_ready', 'jack_down', 'lean_over_car',
                                'stand_ready', 'stand_relaxed', 'arms_folded',
                                'hands_hips', 'radio_hand', 'point_forward',
                                'reach_forward', 'stop_go_board',
                                'stabilise_lean', 'wing_adjust_kneel',
                                'walk_a', 'watch_hands_low'.
    Skeleton(build, pose)       forward kinematics.  .J['wrist_r'] etc. gives
                                the world position of every joint; .F['...']
                                gives its 3x3 frame (columns = x, y, z).
                                .contact_dz is what you add to put the
                                figure's SOLE PLANE on z = 0.  The garment
                                itself never touches the ground; the boots do.

THE GARMENT
    SuitSpec                    every per-instance decision, all of it drawn
                                deterministically from one integer uid.
    suit_spec(uid, **over)      -> SuitSpec.  Overrides win, so a dependant
                                that needs a specific pose says
                                suit_spec(7, pose='crouch_gun').
    build_suit(spec, coll, mats, name=None) -> Suit
                                ONE garment.  Recentred on emit, materials
                                read TexCoord->Object.  Object name is
                                'CFO_<name>'.

    Suit.obj                    the Blender object
    Suit.spec, Suit.skel        what made it
    Suit.landmarks              THE ATTACHMENT CONTRACT, world coordinates:

        name            origin is                       use it for
        --------------  -----------------------------  ---------------------
        cuff_wrist_l/r  centre of the knit cuff mouth   gloves
        cuff_ankle_l/r  centre of the leg cuff mouth    boots
        collar_mouth    centre of the collar opening    balaclava, helmet
        head            head centre                     helmet
        ear_l/r         ear centre                      headset cups
        belt_back       small of the back, on the belt  radio belt pack
        belt_l/r        hip, on the belt                tool pouch, tether
        shoulder_l/r    top of the shoulder seam        headset band, harness
        chest_patch     centre of the left chest patch  team crest overlay
        back_panel      centre of the back yoke         name/number overlay
        knee_l/r        front of the knee panel         knee pad
        grip_l/r        centre of the closed hand       wheelgun, tyre, board
        sole_l/r        sole contact point (z = ground) boots, footprint

        Every landmark is a Frame: .o (3,), .x (3,), .y (3,), .z (3,), .r
        (a characteristic radius in metres).  .y is the OUTWARD normal for
        patches and the DOWN-THE-LIMB axis for cuffs; .z is up-ish.  Use
        Frame.mat4() for a ready-made 4x4.

    MATERIALS
    materials()                 -> [shell, knit, embroidery, hardware]
                                idempotent, named 'CFO_*'.  Slot order is
                                MAT_SHELL/MAT_KNIT/MAT_EMB/MAT_HW = 0..3.

    THE FOLD LANGUAGE (reusable by every soft-goods item downstream)
    FOLD                        the measured constants: Nomex buckling
                                half-wavelength, crease depth, drape sag.
    fold_stack(...)             the composed displacement field.
    felled_seam(d)              flat-felled welt profile, metres -> metres.
    stitch_run(...)             emits real topstitch beads along a curve.

    THE FAMILY
    build(coll_name='CFO_Crew', n=110, seed=0, box_c=(cx, cy), cam_at=None)
                                -> [Suit].  Places against
                                world_contract.world_ground_z, never an
                                assumed z, and records the value it used on
                                each object as ['cfo_world_ground_z'].
    crew_layout(n, box_c, seed)  -> [((circuit_x, circuit_y), facing_deg,
                                pose_name)].  `facing_deg` is the CIRCUIT
                                bearing the figure faces.

    THE SOFT-GOODS TOOLKIT (reusable by marshal_overall, hi_vis_tabard,
    driver_race_suit, crew_headset and anything else made of cloth)
    Acc                         vertex/face accumulator with ABSOLUTE index
                                control -- needed wherever two pieces must
                                share vertices rather than duplicate them.
    sweep(path, U, V, A, B, N, ...) -> Piece
                                superelliptic swept tube with a per-sample
                                displacement callback and a curvature guard.
    patch_on(...)               rounded-rect applique lying ON a piece, with
                                a satin-stitch bead.
    stitch_run(...)             real topstitch beads along a curve.
    seam_curve / ring_curve     sample a seam line off a piece.
    chain_axes(...)             non-twisting section axes along a limb.

    PLACEHOLDERS -- NOT THIS ITEM
    under_forms(suit, coll, mat)  emits STANDIN_* balaclava, gloves and boots
                                so the macro render can be judged as a garment
                                on a person.  crew_helmet_visor and
                                crew_gloves_and_boots replace them; the
                                acceptance gate cannot see them because they
                                are not CFO_-prefixed.

===========================================================================
MODELLING NOTES (choices a reader would otherwise have to reverse-engineer)
===========================================================================
* The trouser legs SPLIT out of the trunk with real pants topology: the trunk
  ring is halved at the front and back centre lines, each half becomes the
  outboard half of a leg ring, and the inboard half is generated at the crotch
  and inflated over the first 90 mm of thigh.  That is what makes the seat and
  the crotch read; it cannot be faked with overlapping tubes because a thigh
  is wider than a hip half-width and would poke out.
* The SLEEVES are overlapping tubes with a rolled sleeve head, not a cut
  armscye.  The trunk at the shoulder is 0.115H half-wide and the sleeve cap
  spans 0.055H..0.165H, so the sleeve covers the trunk everywhere the two
  meet; the visible junction IS the armscye and the 2 mm sleeve-head roll sits
  on it.  A cut armscye would be more correct topologically and identical at
  373 px/m.  Stated rather than hidden.
* Nothing here is a linked duplicate, a particle system or a geometry-nodes
  instance.  Every suit is its own vertex data, from its own parameter draw.
  That is deliberate: the gate can then MEASURE per-instance variation instead
  of being told about it.

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/crew_fireproof_overall.py -- --test --n 60 \
        --out world/items/crew_fireproof_overall_test.blend
"""

import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLD)
for p in (WORLD, os.path.join(ROOT, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import world_contract as C                                    # noqa: E402
import itemkit as K                                               # noqa: E402

PFX = "CFO_"
ROOT_COLL = "CFO_Crew"

MAT_SHELL, MAT_KNIT, MAT_EMB, MAT_HW = 0, 1, 2, 3
MAT_NAMES = ["Nomex", "Knit", "Embroidery", "Hardware"]


# --------------------------------------------------------------------------- #
#  1.  determinism                                                              #
# --------------------------------------------------------------------------- #

def hash01(*keys):
    """[0,1) from any tuple of numbers/strings.  Same everywhere in round 2."""
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


def rint(lo, hi, *keys):
    return int(lo + (hi + 1 - lo) * hash01(*keys)) if hi >= lo else lo


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
    s, a, f = np.zeros_like(np.asarray(x, float)), 1.0, 1.0
    n = 0.0
    for i in range(oct):
        s = s + a * _vnoise1(np.asarray(x, float) * f, seed + i * 131)
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
    s = np.zeros_like(np.asarray(x, float))
    a, f, n = 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * _vnoise2(np.asarray(x, float) * f, np.asarray(y, float) * f,
                             seed + i * 977)
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


def _norm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


# --------------------------------------------------------------------------- #
#  2.  mesh accumulator with ABSOLUTE index control                             #
# --------------------------------------------------------------------------- #

class Acc:
    """Vertex/face accumulator.

    Unlike build_dressing's MB this hands back absolute vertex indices, because
    the pants split needs the trunk's own ring vertices to become the outboard
    half of each leg ring.  A garment that duplicates that seam gets a shading
    crack right down the crotch.

    Per-vertex channels:
        uv    (u, v)  in METRES over the cloth: u around, v along.  The weave,
                      the rib and the stitch relief all key off this, so the
                      thread count is physical wherever the shader looks.
        base  RGBA    panel colour (linear) + A = dye-lot id in [0,1]
        aux   RGBA    (seam, sheen_boost, panel_id, uid)
        wear  RGBA    (abrasion, dirt, oil, sunfade)
    """

    __slots__ = ("name", "_V", "_UV", "_B", "_A", "_W", "_Fq", "_Ft",
                 "_Mq", "_Mt", "_Sq", "_St", "_n")

    def __init__(self, name):
        self.name = name
        self._V, self._UV, self._B, self._A, self._W = [], [], [], [], []
        self._Fq, self._Ft, self._Mq, self._Mt, self._Sq, self._St = \
            [], [], [], [], [], []
        self._n = 0

    # -- vertices ----------------------------------------------------------
    def verts(self, P, uv=None, base=(0.1, 0.1, 0.1, 0.0),
              aux=(0.0, 0.0, 0.0, 0.0), wear=(0.0, 0.0, 0.0, 0.0)):
        """-> start index.  P is (N,3); channels broadcast or (N,c)."""
        P = np.asarray(P, float).reshape(-1, 3)
        n = len(P)
        if n == 0:
            return self._n
        self._V.append(P)
        for store, val, w in ((self._UV, uv, 2), (self._B, base, 4),
                              (self._A, aux, 4), (self._W, wear, 4)):
            if val is None:
                store.append(np.zeros((n, w)))
            else:
                a = np.asarray(val, float)
                store.append(np.tile(a.reshape(1, w), (n, 1)) if a.ndim == 1
                             else a.reshape(n, w))
        i0 = self._n
        self._n += n
        return i0

    # -- faces (ABSOLUTE indices) ------------------------------------------
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
        """IDX (R, Cu) index grid -> quads.  wrap_u closes the ring."""
        IDX = np.asarray(IDX, np.int64)
        R, Cu = IDX.shape
        a = IDX[:-1, :] if not wrap_u else IDX[:-1, :]
        j1 = (np.arange(Cu) + 1) % Cu if wrap_u else np.arange(1, Cu)
        j0 = np.arange(Cu) if wrap_u else np.arange(Cu - 1)
        A = IDX[:-1][:, j0]; B = IDX[:-1][:, j1]
        Cc = IDX[1:][:, j1]; D = IDX[1:][:, j0]
        Q = np.stack([A, B, Cc, D], -1).reshape(-1, 4)
        if flip:
            Q = Q[:, ::-1]
        self.quads(Q, mat, smooth)

    # -- realise ------------------------------------------------------------
    def emit(self, coll, mats, name=None):
        if self._n == 0:
            return None
        V = np.concatenate(self._V, 0)
        UV = np.concatenate(self._UV, 0)
        B = np.concatenate(self._B, 0)
        A = np.concatenate(self._A, 0)
        W = np.concatenate(self._W, 0)
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

        # LAW 6: recentre on emit.  |P| ~ 1000 m kills float32 inside any
        # procedural, and every material here reads TexCoord -> Object.
        ctr = 0.5 * (V.min(0) + V.max(0))
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
        for cname, arr in (("base", B), ("aux", A), ("wear", W)):
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
#  3.  shader graph DSL                                                         #
# --------------------------------------------------------------------------- #

class NG:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self._x = 0

    def n(self, t, defaults=None, **kw):
        nd = self.nt.nodes.new(t)
        self._x += 180
        nd.location = (self._x, (self._x // 180 % 7) * 250)
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
            node.inputs[idx].default_value = (*v, 1.0) if len(v) == 3 else tuple(v)
        else:
            node.inputs[idx].default_value = float(v)

    def _feed_named(self, node, name, v):
        """`_feed`, addressing the socket BY NAME.  Use this for Normal.

        R2-038 was `itemkit.bump()` pinning ShaderNodeBump by index after
        Blender 5.2 inserted `Filter Width` at index 2.  This file carries its
        own copy of that mistake one node downstream.  The live order of
        ShaderNodeBsdfPrincipled in 5.2 is

            [0] Base Color [1] Metallic [2] Roughness [3] IOR [4] Alpha
            [5] THIN WALL  [6] Normal   [7] Weight ...

        and every `_feed(b, 5, <bump>)` in this module -- all six of them, one
        per material -- was written when index 5 was `Normal`.  So the whole
        repaired bump chain was being wired into **Thin Wall** and the Normal
        socket of all four Principled BSDFs was left unconnected.  Measured:
        the R2-038 repair moved 0.00 % of this item's pixels, mean |diff|
        1.88e-05 against a noise floor of 1.93e-05 -- a perfect null, because
        no relief reached the shader on either side of it.

        itemkit has no `socket_audit()` -- that name is a phantom this
        docstring used to cite, and the real check is `itemkit --selftest`
        check [0].  It could not see this either way: it asserts the indices
        ITEMKIT assumes, and `_feed` is a private copy living here.
        Indices 0, 1 and 2 (Base Color, Metallic, Roughness) did not move and
        are left alone -- a rename is not a move, and neither is a socket
        inserted after you.
        """
        if v is None:
            return
        for i, s in enumerate(node.inputs):
            if s.name == name:
                return self._feed(node, i, v)
        raise RuntimeError(
            "%s has no input named %r; it has %s"
            % (node.bl_idname, name, [s.name for s in node.inputs]))

    def lk(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def attr(self, name):
        return self.n("ShaderNodeAttribute", attribute_name=name)

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
            self._feed(m, 3, scale)
        return m

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n("ShaderNodeMixRGB", blend_type=blend)
        self._feed(m, 0, fac); self._feed(m, 1, a); self._feed(m, 2, b)
        return m

    def noise(self, vec=None, scale=5.0, detail=8.0, rough=0.55, dist=0.0,
              dim='3D'):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dim,
                    defaults={2: scale, 3: detail, 4: rough, 8: dist})
        self._feed(nd, 0, vec)
        return nd

    def voro(self, vec=None, scale=10.0, rand=1.0, feature='F1', dim='3D'):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions=dim, defaults={2: scale, 8: rand})
        self._feed(nd, 0, vec)
        return nd

    def wave(self, vec=None, scale=10.0, dist=0.0, detail=2.0, band='X',
             wtype='BANDS', prof='SIN'):
        nd = self.n("ShaderNodeTexWave", wave_type=wtype, bands_direction=band,
                    wave_profile=prof, defaults={1: scale, 2: dist, 3: detail})
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

    def bump(self, height, strength=0.2, dist=None, normal=None,
             modulation_pp=None, wavelength_m=None, height_pp=1.0):
        """Height -> normal perturbation.  WIRED BY NAME, stated in RADIANCE.

        TWO defects lived in the four lines this replaces.

        WIRED BY NAME (R2-038).  Blender 5.2 inserted `Filter Width` at index 2,
        so the live socket order is

            [0] Strength  [1] Distance  [2] Filter Width  [3] Height  [4] Normal

        The old body pinned `height` to index 2 and the incoming normal chain to
        index 3: the height signal went into Filter Width, and the Height socket
        of the FIRST bump in every chain kept its constant default.  A constant
        has zero gradient, so that stage contributed NO relief at all, and every
        later stage read a normal chain where its height should be.  It was
        silent -- the material built, rendered, and passed the gate's node-count
        check; only `relief_reads_as_lip_and_shade` could ever have seen it.
        Never pin this node by index again.

        STATE THE RADIANCE MODULATION, NOT THE METRES (itemkit section 5b,
        ITEM-CAMPAIGN-BRIEF 4a).  Give `modulation_pp` with `wavelength_m` and
        the depth is derived from the contract sun: m = 2 sin(theta) / tan(e),
        a 4.52x amplifier at this film's 12.47 deg.  An amplitude with no
        wavelength is not a relief specification -- the same 0.5 mm is m = 0.57
        on an 8 mm crumple and m = 0.045 on a 100 mm flute.  `height_pp` is the
        peak-to-peak swing of the height signal reaching the socket, so a stage
        can state the modulation of the BAND it means rather than of a
        hypothetical full-range height.
        """
        if (dist is None) == (modulation_pp is None):
            raise ValueError("bump() takes exactly one of dist= or "
                             "modulation_pp= (with wavelength_m=): itemkit 5b")
        if modulation_pp is not None:
            if not wavelength_m:
                raise ValueError("bump(modulation_pp=) needs wavelength_m=; an "
                                 "amplitude with no wavelength is not a relief "
                                 "specification.")
            try:
                _s = abs(float(strength))
            except (TypeError, ValueError):
                _s = 1.0         # a masked strength: aim at where the mask is 1
            dist = (K.relief_amplitude_for(modulation_pp, wavelength_m)
                        * 1e-3 / max(_s * float(height_pp), 1e-9))
        b = self.n("ShaderNodeBump")
        self._feed(b, b.inputs.find("Strength"), strength)
        self._feed(b, b.inputs.find("Distance"), dist)
        self._feed(b, b.inputs.find("Height"), height)
        if normal is not None:
            self._feed(b, b.inputs.find("Normal"), normal)
        return b


def _bsdf_in(b, *names):
    for nm in names:
        if nm in b.inputs:
            return b.inputs[nm]
    return None


# --------------------------------------------------------------------------- #
#  4.  anthropometry and the skeleton                                           #
# --------------------------------------------------------------------------- #
#
# Every length is a fraction of stature H.  The numbers are the standard adult
# male segment fractions (Drillis & Contini / NASA-STD-3000 style), adjusted so
# that with H = 1.78 m the joint heights land on: ankle 0.069, knee 0.507,
# hip 0.926, waist 1.068, shoulder 1.433, chin 1.549 m.  Girths are solved
# from real circumferences rather than guessed radii:
#     chest 100 cm -> semi-axes 0.1010 H x 0.0758 H  (superellipse n = 2.45)
#     waist  86 cm -> 0.0871 H x 0.0652 H
#     hip    98 cm -> 0.1000 H x 0.0736 H
# so a "regular" build is a 100/86/98 crew member, not a cylinder.

BONES = [
    # name,      parent,     offset in the parent frame (units of H)
    ("pelvis",   None,       (0.0000,  0.0000,  0.0000)),
    ("spine1",   "pelvis",   (0.0000,  0.0000,  0.0750)),
    ("spine2",   "spine1",   (0.0000, -0.0020,  0.0900)),
    ("spine3",   "spine2",   (0.0000,  0.0020,  0.0950)),
    ("neck",     "spine3",   (0.0000,  0.0060,  0.0500)),
    ("head",     "neck",     (0.0000,  0.0020,  0.0550)),
    ("clav_r",   "spine3",   (0.0380,  0.0100,  0.0180)),
    ("shldr_r",  "clav_r",   (0.0720,  0.0000, -0.0130)),
    ("elbow_r",  "shldr_r",  (0.0000,  0.0000, -0.1800)),
    ("wrist_r",  "elbow_r",  (0.0000,  0.0000, -0.1420)),
    ("hand_r",   "wrist_r",  (0.0000,  0.0000, -0.0430)),
    ("clav_l",   "spine3",   (-0.0380, 0.0100,  0.0180)),
    ("shldr_l",  "clav_l",   (-0.0720, 0.0000, -0.0130)),
    ("elbow_l",  "shldr_l",  (0.0000,  0.0000, -0.1800)),
    ("wrist_l",  "elbow_l",  (0.0000,  0.0000, -0.1420)),
    ("hand_l",   "wrist_l",  (0.0000,  0.0000, -0.0430)),
    ("hip_r",    "pelvis",   (0.0565,  0.0000, -0.0200)),
    ("knee_r",   "hip_r",    (0.0000,  0.0000, -0.2350)),
    ("ankle_r",  "knee_r",   (0.0000,  0.0000, -0.2460)),
    ("toe_r",    "ankle_r",  (0.0000,  0.1150, -0.0390)),
    ("hip_l",    "pelvis",   (-0.0565, 0.0000, -0.0200)),
    ("knee_l",   "hip_l",    (0.0000,  0.0000, -0.2350)),
    ("ankle_l",  "knee_l",   (0.0000,  0.0000, -0.2460)),
    ("toe_l",    "ankle_l",  (0.0000,  0.1150, -0.0390)),
]
BONE_PARENT = {n: p for n, p, _o in BONES}
BONE_OFF = {n: np.array(o, float) for n, _p, o in BONES}
PELVIS_H = 0.5400          # pelvis origin height, fraction of H


def _rot(rx, ry, rz):
    """Rz @ Ry @ Rx, degrees."""
    a, b, c = math.radians(rx), math.radians(ry), math.radians(rz)
    ca, sa = math.cos(a), math.sin(a)
    cb, sb = math.cos(b), math.sin(b)
    cc, sc = math.cos(c), math.sin(c)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]], float)
    Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]], float)
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]], float)
    return Rz @ Ry @ Rx


class Build:
    """One body.  All girths are MULTIPLIERS on the regular section."""

    __slots__ = ("name", "H", "girth", "belly", "shoulder", "limb", "arm_g",
                 "leg_g", "neck_g", "stoop")

    def __init__(self, name, H=1.780, girth=1.0, belly=0.0, shoulder=1.0,
                 limb=1.0, arm_g=1.0, leg_g=1.0, neck_g=1.0, stoop=0.0):
        self.name = name
        self.H = float(H)
        self.girth = girth        # torso section scale
        self.belly = belly        # 0..1, moves volume to the lower front
        self.shoulder = shoulder  # biacromial scale
        self.limb = limb          # limb LENGTH scale (long-limbed vs compact)
        self.arm_g = arm_g
        self.leg_g = leg_g
        self.neck_g = neck_g
        self.stoop = stoop        # thoracic kyphosis, degrees-ish 0..1


BUILDS = {
    "slight":     Build("slight",     1.720, 0.865, 0.00, 0.940, 1.030,
                        0.870, 0.895, 0.925, 0.10),
    "lean_tall":  Build("lean_tall",  1.882, 0.895, 0.00, 0.975, 1.075,
                        0.905, 0.920, 0.955, 0.05),
    "regular":    Build("regular",    1.780, 1.000, 0.05, 1.000, 1.000,
                        1.000, 1.000, 1.000, 0.12),
    "broad":      Build("broad",      1.812, 1.075, 0.10, 1.105, 0.980,
                        1.115, 1.055, 1.075, 0.16),
    "heavy":      Build("heavy",      1.762, 1.185, 0.62, 1.055, 0.955,
                        1.130, 1.130, 1.105, 0.24),
    "stocky":     Build("stocky",     1.692, 1.115, 0.34, 1.075, 0.930,
                        1.095, 1.075, 1.090, 0.20),
    "short":      Build("short",      1.646, 0.955, 0.12, 0.975, 0.955,
                        0.960, 0.965, 0.985, 0.14),
    "tall":       Build("tall",       1.925, 1.020, 0.06, 1.030, 1.060,
                        1.010, 1.005, 1.010, 0.08),
}
BUILD_NAMES = list(BUILDS.keys())


class Frame:
    """origin + orthonormal basis + a characteristic radius, world metres."""

    __slots__ = ("o", "x", "y", "z", "r", "name")

    def __init__(self, o, x, y, z, r=0.05, name=""):
        self.o = np.asarray(o, float)
        self.x = _norm(x); self.y = _norm(y); self.z = _norm(z)
        self.r = float(r)
        self.name = name

    def mat4(self):
        M = np.eye(4)
        M[:3, 0] = self.x; M[:3, 1] = self.y; M[:3, 2] = self.z
        M[:3, 3] = self.o
        return M

    def __repr__(self):
        return "Frame(%s o=%.3f,%.3f,%.3f r=%.3f)" % (
            self.name, self.o[0], self.o[1], self.o[2], self.r)


class Pose:
    """Joint rotations in degrees, applied in the PARENT's frame.

    Sign convention, so a dependant can invent its own pose without guessing:
        elbow  rx > 0   flexes (hand comes forward)
        knee   rx < 0   flexes (heel comes back)
        hip    rx > 0   flexes (thigh comes forward)
        shldr  ry < 0 on the RIGHT abducts (arm swings away from the body);
               ry > 0 on the LEFT does the same.  `mirror=True` handles it.
        spine* rx > 0   bends forward
    root_z is added to the pelvis height in units of H; root_rot tilts the
    whole figure.
    """

    __slots__ = ("name", "j", "root_z", "root_rot", "note")

    def __init__(self, name, j=None, root_z=0.0, root_rot=(0, 0, 0), note=""):
        self.name = name
        self.j = dict(j or {})
        self.root_z = root_z
        self.root_rot = root_rot
        self.note = note

    def copy(self, name=None, **kw):
        p = Pose(name or self.name, dict(self.j), self.root_z, self.root_rot,
                 self.note)
        for k, v in kw.items():
            setattr(p, k, v)
        return p


def _P(name, root_z=0.0, root_rot=(0, 0, 0), note="", **j):
    return Pose(name, j, root_z, root_rot, note)


# --- the 20 poses.  Every crew_* dependant in the manifest has one. ---------
POSES = {
 "stand_ready": _P(
    "stand_ready", note="wheel gunner waiting, weight even",
    spine1=(2, 0, 0), spine2=(3, 0, 1), spine3=(2, 0, -1), neck=(-4, 0, 0),
    clav_r=(0, -3, 0), shldr_r=(-6, -9, 0), elbow_r=(26, 0, 8),
    wrist_r=(6, 0, 0),
    clav_l=(0, 3, 0), shldr_l=(-5, 9, 0), elbow_l=(23, 0, -8), wrist_l=(5, 0, 0),
    hip_r=(-2, -4, 0), knee_r=(-5, 0, 0), ankle_r=(3, 0, 4),
    hip_l=(-1, 4, 0), knee_l=(-4, 0, 0), ankle_l=(3, 0, -4)),

 "stand_relaxed": _P(
    "stand_relaxed", note="weight on one leg, hip dropped",
    root_rot=(0, 2.5, 0),
    spine1=(1, -3, 0), spine2=(3, -2, 2), spine3=(3, 1, -1), neck=(-6, 0, 2),
    clav_r=(0, -2, 0), shldr_r=(-3, -7, 0), elbow_r=(17, 0, 6),
    clav_l=(0, 2, 0), shldr_l=(-2, 6, 0), elbow_l=(14, 0, -5),
    hip_r=(-3, -2, 0), knee_r=(-3, 0, 0), ankle_r=(2, 0, 3),
    hip_l=(-6, 7, 0), knee_l=(-14, 0, 0), ankle_l=(6, 0, -6)),

 "hands_hips": _P(
    "hands_hips", note="watching the stop, elbows out",
    spine1=(1, 0, 0), spine2=(2, 0, 0), spine3=(-2, 0, 0), neck=(-8, 0, 0),
    clav_r=(-4, -8, 0), shldr_r=(-6, -44, 0), elbow_r=(84, 0, 62),
    wrist_r=(10, 0, 16),
    clav_l=(-4, 8, 0), shldr_l=(-5, 42, 0), elbow_l=(82, 0, -60),
    wrist_l=(10, 0, -16),
    hip_r=(-2, -5, 0), knee_r=(-4, 0, 0), hip_l=(-2, 5, 0), knee_l=(-4, 0, 0)),

 "arms_folded": _P(
    "arms_folded", note="garage technician, arms crossed",
    spine1=(2, 0, 0), spine2=(4, 0, 0), spine3=(-1, 0, 0), neck=(-5, 0, 0),
    clav_r=(2, -4, 0), shldr_r=(-16, -18, 0), elbow_r=(112, 0, 46),
    wrist_r=(4, 0, -20),
    clav_l=(2, 4, 0), shldr_l=(-14, 17, 0), elbow_l=(108, 0, -44),
    wrist_l=(4, 0, 20),
    hip_r=(-2, -4, 0), knee_r=(-5, 0, 0), hip_l=(-2, 4, 0), knee_l=(-5, 0, 0)),

 "crouch_gun": _P(
    "crouch_gun", root_z=-0.128, root_rot=(16, 0, 0),
    note="wheel gunner down on the gun, deep knee bend",
    spine1=(9, 0, 0), spine2=(12, 0, 2), spine3=(6, 0, -2), neck=(-16, 0, 0),
    clav_r=(-3, -6, 0), shldr_r=(-46, -14, 0), elbow_r=(58, 0, 10),
    wrist_r=(12, 0, 6),
    clav_l=(-3, 6, 0), shldr_l=(-40, 13, 0), elbow_l=(52, 0, -9),
    wrist_l=(10, 0, -6),
    hip_r=(62, -9, 0), knee_r=(-84, 0, 0), ankle_r=(24, 0, 5),
    hip_l=(56, 10, 0), knee_l=(-78, 0, 0), ankle_l=(22, 0, -5)),

 "crouch_ready": _P(
    "crouch_ready", root_z=-0.072, root_rot=(11, 0, 0),
    note="tyre carrier crouched, tyre held low in front",
    spine1=(7, 0, 0), spine2=(9, 0, 0), spine3=(4, 0, 0), neck=(-13, 0, 0),
    clav_r=(-2, -5, 0), shldr_r=(-34, -11, 0), elbow_r=(74, 0, 12),
    clav_l=(-2, 5, 0), shldr_l=(-33, 11, 0), elbow_l=(72, 0, -12),
    hip_r=(44, -8, 0), knee_r=(-58, 0, 0), ankle_r=(16, 0, 4),
    hip_l=(42, 8, 0), knee_l=(-56, 0, 0), ankle_l=(15, 0, -4)),

 "kneel_r": _P(
    "kneel_r", root_z=-0.212, root_rot=(6, 0, -3),
    note="right knee on the deck, left foot planted - THE mechanic pose",
    spine1=(5, 0, 1), spine2=(8, 0, 2), spine3=(3, 0, -1), neck=(-12, 0, -3),
    clav_r=(-2, -5, 0), shldr_r=(-30, -12, 0), elbow_r=(66, 0, 10),
    wrist_r=(10, 0, 5),
    clav_l=(-2, 5, 0), shldr_l=(-26, 12, 0), elbow_l=(60, 0, -10),
    hip_r=(-16, -6, 0), knee_r=(-96, 0, 0), ankle_r=(-24, 0, 3),
    hip_l=(78, 12, 0), knee_l=(-84, 0, 0), ankle_l=(12, 0, -6)),

 "kneel_l": _P(
    "kneel_l", root_z=-0.212, root_rot=(6, 0, 3),
    note="mirror of kneel_r",
    spine1=(5, 0, -1), spine2=(8, 0, -2), spine3=(3, 0, 1), neck=(-12, 0, 3),
    clav_l=(-2, 5, 0), shldr_l=(-30, 12, 0), elbow_l=(66, 0, -10),
    wrist_l=(10, 0, -5),
    clav_r=(-2, -5, 0), shldr_r=(-26, -12, 0), elbow_r=(60, 0, 10),
    hip_l=(-16, 6, 0), knee_l=(-96, 0, 0), ankle_l=(-24, 0, -3),
    hip_r=(78, -12, 0), knee_r=(-84, 0, 0), ankle_r=(12, 0, 6)),

 "wing_adjust_kneel": _P(
    "wing_adjust_kneel", root_z=-0.238, root_rot=(19, 0, 0),
    note="front wing adjuster, both knees down, reaching in low",
    spine1=(12, 0, 0), spine2=(15, 0, 1), spine3=(7, 0, -1), neck=(-22, 0, 0),
    clav_r=(-4, -7, 0), shldr_r=(-58, -10, 0), elbow_r=(72, 0, 8),
    wrist_r=(16, 0, 4),
    clav_l=(-4, 7, 0), shldr_l=(-55, 10, 0), elbow_l=(70, 0, -8),
    hip_r=(-14, -7, 0), knee_r=(-104, 0, 0), ankle_r=(-28, 0, 4),
    hip_l=(-14, 7, 0), knee_l=(-102, 0, 0), ankle_l=(-28, 0, -4)),

 "carry_tyre_high": _P(
    "carry_tyre_high", note="tyre carried at chest, elbows tight, torso back",
    root_rot=(-7, 0, 0),
    spine1=(-4, 0, 0), spine2=(-3, 0, 0), spine3=(2, 0, 0), neck=(2, 0, 0),
    clav_r=(-6, -6, 0), shldr_r=(-46, -26, 0), elbow_r=(98, 0, 44),
    wrist_r=(8, 0, 10),
    clav_l=(-6, 6, 0), shldr_l=(-44, 26, 0), elbow_l=(96, 0, -42),
    wrist_l=(8, 0, -10),
    hip_r=(4, -6, 0), knee_r=(-8, 0, 0), ankle_r=(4, 0, 4),
    hip_l=(4, 6, 0), knee_l=(-8, 0, 0), ankle_l=(4, 0, -4)),

 "carry_tyre_low": _P(
    "carry_tyre_low", root_z=-0.038, root_rot=(9, 0, 4),
    note="tyre swinging low at the thigh, one shoulder dropped",
    spine1=(6, 0, -3), spine2=(7, 0, -4), spine3=(2, 0, 2), neck=(-10, 0, 3),
    clav_r=(-1, -4, 0), shldr_r=(-14, -22, 0), elbow_r=(38, 0, 14),
    clav_l=(-1, 4, 0), shldr_l=(-10, 15, 0), elbow_l=(30, 0, -12),
    hip_r=(18, -8, 0), knee_r=(-30, 0, 0), ankle_r=(9, 0, 5),
    hip_l=(12, 9, 0), knee_l=(-24, 0, 0), ankle_l=(7, 0, -5)),

 "jack_ready": _P(
    "jack_ready", root_z=-0.058, root_rot=(24, 0, 0),
    note="front jack man, bent at the waist, both hands on the handle",
    spine1=(14, 0, 0), spine2=(17, 0, 0), spine3=(6, 0, 0), neck=(-30, 0, 0),
    clav_r=(-3, -5, 0), shldr_r=(-40, -9, 0), elbow_r=(34, 0, 6),
    clav_l=(-3, 5, 0), shldr_l=(-39, 9, 0), elbow_l=(33, 0, -6),
    hip_r=(30, -7, 0), knee_r=(-26, 0, 0), ankle_r=(10, 0, 4),
    hip_l=(26, 8, 0), knee_l=(-22, 0, 0), ankle_l=(9, 0, -4)),

 "jack_down": _P(
    "jack_down", root_z=-0.148, root_rot=(31, 0, 0),
    note="jack driven home, deep lunge, weight forward",
    spine1=(17, 0, 2), spine2=(20, 0, 2), spine3=(8, 0, -2), neck=(-36, 0, 0),
    clav_r=(-4, -6, 0), shldr_r=(-56, -8, 0), elbow_r=(28, 0, 5),
    clav_l=(-4, 6, 0), shldr_l=(-54, 8, 0), elbow_l=(27, 0, -5),
    hip_r=(66, -8, 0), knee_r=(-72, 0, 0), ankle_r=(22, 0, 4),
    hip_l=(18, 9, 0), knee_l=(-20, 0, 0), ankle_l=(4, 0, -4)),

 "lean_over_car": _P(
    "lean_over_car", root_rot=(33, 0, 0), root_z=-0.020,
    note="mechanic reaching into the cockpit",
    spine1=(16, 0, -2), spine2=(19, 0, -3), spine3=(9, 0, 2), neck=(-38, 0, 3),
    clav_r=(-5, -6, 0), shldr_r=(-66, -12, 0), elbow_r=(46, 0, 9),
    clav_l=(-5, 6, 0), shldr_l=(-62, 12, 0), elbow_l=(44, 0, -9),
    hip_r=(28, -6, 0), knee_r=(-14, 0, 0), ankle_r=(6, 0, 4),
    hip_l=(26, 7, 0), knee_l=(-12, 0, 0), ankle_l=(5, 0, -4)),

 "reach_forward": _P(
    "reach_forward", note="both arms out at chest height",
    spine1=(3, 0, 0), spine2=(4, 0, 0), spine3=(1, 0, 0), neck=(-6, 0, 0),
    clav_r=(-5, -6, 0), shldr_r=(-78, -14, 0), elbow_r=(22, 0, 8),
    clav_l=(-5, 6, 0), shldr_l=(-76, 14, 0), elbow_l=(20, 0, -8),
    hip_r=(-2, -5, 0), knee_r=(-6, 0, 0), hip_l=(-2, 5, 0), knee_l=(-6, 0, 0)),

 "radio_hand": _P(
    "radio_hand", note="one hand cupped to the ear cup, other on the hip",
    spine1=(2, 0, 2), spine2=(3, 0, 2), spine3=(0, 0, -2), neck=(-6, 0, -6),
    clav_r=(-8, -10, 0), shldr_r=(-38, -52, 0), elbow_r=(122, 0, 74),
    wrist_r=(6, 0, 18),
    clav_l=(-3, 6, 0), shldr_l=(-8, 34, 0), elbow_l=(86, 0, -56),
    hip_r=(-2, -4, 0), knee_r=(-5, 0, 0), hip_l=(-3, 5, 0), knee_l=(-9, 0, 0)),

 "point_forward": _P(
    "point_forward", note="release man, arm out, weight forward",
    root_rot=(6, 0, 0),
    spine1=(4, 0, -3), spine2=(5, 0, -4), spine3=(2, 0, 3), neck=(-8, 0, 6),
    clav_r=(-6, -8, 0), shldr_r=(-88, -18, 0), elbow_r=(12, 0, 6),
    clav_l=(-1, 4, 0), shldr_l=(-8, 10, 0), elbow_l=(34, 0, -10),
    hip_r=(10, -6, 0), knee_r=(-14, 0, 0), ankle_r=(5, 0, 4),
    hip_l=(-8, 8, 0), knee_l=(-6, 0, 0), ankle_l=(2, 0, -5)),

 "stop_go_board": _P(
    "stop_go_board", note="lollipop / board held up and out",
    spine1=(1, 0, 0), spine2=(2, 0, 0), spine3=(0, 0, 0), neck=(-4, 0, 0),
    clav_r=(-9, -9, 0), shldr_r=(-104, -20, 0), elbow_r=(30, 0, 10),
    clav_l=(-9, 9, 0), shldr_l=(-98, 20, 0), elbow_l=(28, 0, -10),
    hip_r=(-2, -5, 0), knee_r=(-4, 0, 0), hip_l=(-2, 5, 0), knee_l=(-4, 0, 0)),

 "stabilise_lean": _P(
    "stabilise_lean", root_rot=(13, 0, -6), root_z=-0.030,
    note="side stabiliser bracing the car, one arm down and across",
    spine1=(8, 0, 5), spine2=(9, 0, 6), spine3=(3, 0, -4), neck=(-16, 0, -6),
    clav_r=(-3, -5, 0), shldr_r=(-36, -6, 0), elbow_r=(20, 0, 6),
    clav_l=(-2, 5, 0), shldr_l=(-16, 14, 0), elbow_l=(48, 0, -12),
    hip_r=(20, -8, 0), knee_r=(-22, 0, 0), ankle_r=(8, 0, 5),
    hip_l=(6, 10, 0), knee_l=(-12, 0, 0), ankle_l=(4, 0, -6)),

 "walk_a": _P(
    "walk_a", note="crossing the lane, mid stride",
    spine1=(3, 0, -2), spine2=(3, 0, -3), spine3=(1, 0, 3), neck=(-5, 0, 2),
    clav_r=(-2, -4, 0), shldr_r=(-26, -8, 0), elbow_r=(40, 0, 8),
    clav_l=(1, 4, 0), shldr_l=(14, 8, 0), elbow_l=(22, 0, -8),
    hip_r=(26, -5, 0), knee_r=(-14, 0, 0), ankle_r=(10, 0, 4),
    hip_l=(-18, 5, 0), knee_l=(-32, 0, 0), ankle_l=(16, 0, -4)),

 "watch_hands_low": _P(
    "watch_hands_low", note="hands clasped low in front, waiting",
    spine1=(3, 0, 0), spine2=(5, 0, 0), spine3=(0, 0, 0), neck=(-8, 0, 0),
    clav_r=(-1, -4, 0), shldr_r=(-16, -9, 0), elbow_r=(58, 0, 40),
    wrist_r=(6, 0, 14),
    clav_l=(-1, 4, 0), shldr_l=(-15, 9, 0), elbow_l=(57, 0, -38),
    wrist_l=(6, 0, -14),
    hip_r=(-2, -4, 0), knee_r=(-6, 0, 0), hip_l=(-2, 4, 0), knee_l=(-6, 0, 0)),
}
POSE_NAMES = list(POSES.keys())

# which poses put a knee on the deck (drives the knee/shin wear and the
# ground contact solve)
KNEELING = {"kneel_r": ("r",), "kneel_l": ("l",),
            "wing_adjust_kneel": ("r", "l")}


class Skeleton:
    """Forward kinematics for one (Build, Pose).

    .J[name] -> world position (3,)      .F[name] -> 3x3 frame, columns x,y,z
    .H, .b, .pose                        .contact_dz  (add to sit on z = 0)
    All in a LOCAL frame whose origin is under the figure's contact point and
    whose +Y is the direction the figure faces.  place() gives you the world
    transform.
    """

    def __init__(self, build, pose):
        self.b = build
        self.pose = pose
        H = build.H
        self.H = H
        limb = build.limb
        J, F = {}, {}
        root_R = _rot(*pose.root_rot)
        root_p = np.array([0.0, 0.0, (PELVIS_H + pose.root_z) * H])
        for name, parent, off in BONES:
            off = np.array(off, float) * H
            # limb-length scaling: arms and legs stretch with `limb`
            if name in ("elbow_r", "elbow_l", "wrist_r", "wrist_l",
                        "hand_r", "hand_l", "knee_r", "knee_l",
                        "ankle_r", "ankle_l"):
                off = off * limb
            if name in ("clav_r", "clav_l", "shldr_r", "shldr_l"):
                off = off * np.array([build.shoulder, 1.0, 1.0])
            if name in ("hip_r", "hip_l"):
                off = off * np.array([0.5 + 0.5 * build.girth, 1.0, 1.0])
            rx, ry, rz = pose.j.get(name, (0.0, 0.0, 0.0))
            if name.startswith("spine") or name == "neck":
                rx = rx + build.stoop * 4.0
            R = _rot(rx, ry, rz)
            if parent is None:
                F[name] = root_R @ R
                J[name] = root_p.copy()
            else:
                J[name] = J[parent] + F[parent] @ off
                F[name] = F[parent] @ R
        self.J, self.F = J, F

        # ---- ground contact -------------------------------------------------
        # sole plane: ankle joint minus the malleolus height, measured along
        # the foot's own down axis so a plantar-flexed ankle still touches.
        ank_h = 0.039 * H
        soles = []
        for s in ("r", "l"):
            soles.append(J["ankle_" + s][2] - ank_h)
        knees = []
        if pose.name in KNEELING:
            for s in KNEELING[pose.name]:
                # front of the knee, garment radius included
                kf = J["knee_" + s] + F["knee_" + s] @ np.array(
                    [0.0, 0.052 * H, 0.0])
                knees.append(kf[2] - 0.030 * H)
        lo = min(soles + knees) if knees else min(soles)
        # GROUND CONTRACT.  This garment never stands on the ground -- the boots
        # do (crew_gloves_and_boots), and the sole plane below is where they
        # start.  The one place cloth DOES touch is a kneeling knee, and cloth
        # over a knee pad compresses about 6 mm rather than embedding the
        # BASE_EMBED_M a rigid object would, so that is what it does.  The z it
        # is placed at still comes from world_contract.world_ground_z, never
        # from an assumed height (see build()).
        self.contact_dz = -lo + (0.006 if knees else 0.0)
        for k in J:
            J[k] = J[k] + np.array([0.0, 0.0, self.contact_dz])
        self.sole_z = {s: J["ankle_" + s][2] - ank_h for s in ("r", "l")}

    # -- chains ------------------------------------------------------------
    def chain(self, names):
        return [self.J[n] for n in names]


# --------------------------------------------------------------------------- #
#  5.  curves, frames and cross-sections                                        #
# --------------------------------------------------------------------------- #

def catmull(P, n, alpha=0.5):
    """Centripetal Catmull-Rom through P (K,3) -> (n,3), plus tangents."""
    P = np.asarray(P, float)
    K = len(P)
    Q = np.vstack([P[0] + (P[0] - P[1]), P, P[-1] + (P[-1] - P[-2])])
    t = [0.0]
    for i in range(1, len(Q)):
        t.append(t[-1] + max(np.linalg.norm(Q[i] - Q[i - 1]), 1e-9) ** alpha)
    t = np.array(t)
    s = np.linspace(t[1], t[-2], n)
    out = np.zeros((n, 3))
    for j, sv in enumerate(s):
        i = int(np.searchsorted(t, sv) - 1)
        i = max(1, min(i, len(Q) - 3))
        t0, t1, t2, t3 = t[i - 1], t[i], t[i + 1], t[i + 2]
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        A1 = (t1 - sv) / (t1 - t0) * p0 + (sv - t0) / (t1 - t0) * p1
        A2 = (t2 - sv) / (t2 - t1) * p1 + (sv - t1) / (t2 - t1) * p2
        A3 = (t3 - sv) / (t3 - t2) * p2 + (sv - t2) / (t3 - t2) * p3
        B1 = (t2 - sv) / (t2 - t0) * A1 + (sv - t0) / (t2 - t0) * A2
        B2 = (t3 - sv) / (t3 - t1) * A2 + (sv - t1) / (t3 - t1) * A3
        out[j] = (t2 - sv) / (t2 - t1) * B1 + (sv - t1) / (t2 - t1) * B2
    return out


def arclen(P):
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(d)])


def resample(P, n):
    """arc-length resample of a polyline"""
    s = arclen(P)
    if s[-1] < 1e-9:
        return np.repeat(P[:1], n, 0)
    want = np.linspace(0.0, s[-1], n)
    out = np.zeros((n, 3))
    for k in range(3):
        out[:, k] = np.interp(want, s, P[:, k])
    return out


def frames_along(P, up_hint):
    """Rotation-minimising frames along a polyline.

    Returns T (tangent), U (side), V (front-ish) per sample.  Parallel
    transport, because a Frenet frame flips at every inflection and a garment
    built on a flipped frame twists its seams around the limb.
    """
    n = len(P)
    T = np.zeros((n, 3))
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T = _norm(T)
    U = np.zeros((n, 3)); V = np.zeros((n, 3))
    u0 = np.asarray(up_hint, float)
    u0 = u0 - T[0] * float(np.dot(u0, T[0]))
    if np.linalg.norm(u0) < 1e-6:
        u0 = np.cross(T[0], [1.0, 0.0, 0.0])
    U[0] = _norm(u0)
    V[0] = _norm(np.cross(T[0], U[0]))
    for i in range(1, n):
        v = U[i - 1] - T[i] * float(np.dot(U[i - 1], T[i]))
        if np.linalg.norm(v) < 1e-9:
            v = np.cross(T[i], V[i - 1])
        U[i] = _norm(v)
        V[i] = _norm(np.cross(T[i], U[i]))
    return T, U, V


def superellipse(theta, a, b, n=2.4):
    """(x, y) on a superellipse.  n=2 is an ellipse; a torso is 2.3-2.6."""
    ct, st = np.cos(theta), np.sin(theta)
    e = 2.0 / n
    x = a * np.sign(ct) * np.abs(ct) ** e
    y = b * np.sign(st) * np.abs(st) ** e
    return x, y


# --------------------------------------------------------------------------- #
#  6.  THE FOLD LANGUAGE                                                        #
# --------------------------------------------------------------------------- #
#
# What makes cloth read as cloth is not noise, it is a small number of NAMED
# mechanisms, each with a length scale set by the fabric's bending stiffness.
# Two-layer Nomex III at ~460 g/m^2 buckles at a much longer wavelength than
# cotton, which is exactly why a race suit looks the way it does: few, fat,
# soft-crested folds, and one hard SET crease at each joint that stays there
# when the joint straightens.
#
#   LAMBDA_FLEX   68 mm   half-wavelength of a compression fold at a joint.
#                        Cotton shirting is 24-30 mm; poplin 18.  A race-suit
#                        elbow at 90 deg shows 2-3 folds over ~140 mm, which
#                        is what this number reproduces.
#   LAMBDA_HANG   112 mm  circumferential wavelength of a free-hanging flute,
#                        so a trouser leg gets 4-5 flutes, not 12.
#   CREASE_W      6.5 mm  half-width of a SET crease.  It is a groove, not a
#                        ridge: the fabric has been folded and the fold line
#                        sits below the surrounding surface.
#   SAG_PER_M     0.052   how far a horizontal sleeve's cloth centreline drops
#                        below the limb centreline, per metre of free span.

class FOLD:
    LAMBDA_FLEX = 0.068
    LAMBDA_HANG = 0.112
    CREASE_W = 0.0065
    CREASE_DEPTH = 0.0050
    SAG_PER_M = 0.052
    MICRO_AMP = 0.0031        # crumple, 40-90 mm wavelength
    HANG_AMP = 0.0104
    FLEX_AMP = 0.0192
    TENSION_AMP = 0.0058
    MIN_GAP = 0.0015          # never let cloth pass through the body


def crest(x, sharp=1.0):
    """Fold cross-profile.  x in radians.

    A stiff fabric's fold is NOT a sine: the crest is broad (the cloth is
    bending around its own thickness) and the valley is narrower and deeper
    (two faces are being pulled together).  `sharp` skews it.
    """
    c = 0.5 + 0.5 * np.cos(x)
    return (c ** (1.0 / (1.0 + 0.9 * sharp))) * 2.0 - 1.0


def groove(d, w=FOLD.CREASE_W, depth=FOLD.CREASE_DEPTH):
    """A SET crease: a narrow negative groove with a slight lip either side."""
    t = np.abs(np.asarray(d, float)) / max(w, 1e-9)
    core = np.exp(-2.9 * t * t)
    lip = np.exp(-1.4 * (t - 1.85) ** 2) * 0.34
    return -depth * core + depth * lip


def felled_seam(d, w=0.0092, h=0.00135, side=1.0):
    """Flat-felled seam welt.  d = signed distance from the seam line (m).

    A felled seam is asymmetric: the folded-under edge stands proud on ONE
    side with a hard step, and dies away smoothly on the other.  9.2 mm wide,
    1.35 mm proud -- 3.4 x 0.5 screen pixels at this item's filmed distance,
    which is why it is mesh and not a bump map.
    """
    t = (np.asarray(d, float) * side + w * 0.5) / w
    prof = sstep(0.0, 0.30, t) * (1.0 - sstep(0.90, 1.0, t))
    # the needle pulls the cloth in on the far side of the fell
    pull = -0.30 * h * np.exp(-((t + 0.28) / 0.30) ** 2)
    return h * prof + pull


def plain_seam(d, w=0.0060, h=0.00075):
    """Pressed-open seam: two small ridges with a valley between them."""
    t = np.asarray(d, float) / max(w, 1e-9)
    return h * (np.exp(-((t - 0.55) / 0.45) ** 2)
                + np.exp(-((t + 0.55) / 0.45) ** 2)
                - 0.55 * np.exp(-(t / 0.35) ** 2))


def flex_folds(v, v_joint, flex_rad, side_w, uid=0.0, phase=0.0,
               lam=FOLD.LAMBDA_FLEX, amp=FOLD.FLEX_AMP):
    """Compression folds on the INSIDE of a flexed joint.

    v        arc-length along the limb (m), array
    v_joint  arc-length of the joint
    flex_rad flexion angle in radians (0 = straight)
    side_w   angular weight 0..1: 1 on the inside of the bend, 0 outside
    Returns a radial displacement in metres.

    The number of folds is not a style choice: the excess arc length on the
    inside of the bend is r*theta, and a sheet of this bending stiffness
    buckles into humps of half-wavelength LAMBDA_FLEX, so n = excess/lambda,
    rounded, clamped to 1..4.  That is the whole reason a Nomex elbow has
    three folds and a cotton one has seven.
    """
    if flex_rad <= 0.02:
        return np.zeros_like(v)
    n = int(np.clip(round(flex_rad * 0.19 / lam * 2.4), 1, 4))
    span = lam * (n + 0.9)
    t = (v - v_joint) / span
    win = np.exp(-3.1 * t * t)
    a = amp * min(flex_rad / 1.4, 1.25) * side_w
    ph = phase + 6.283 * hash01(uid, v_joint, "flex")
    return a * win * crest(6.283 * (v - v_joint) / (2.0 * lam) + ph, 0.55)


def set_crease(v, v_joint, flex_rad, side_w, memory=1.0):
    """The crease the suit KEEPS.  Present even when the joint is straight."""
    d = v - v_joint
    strength = (0.35 + 0.65 * min(flex_rad / 1.2, 1.0)) * memory
    return groove(d, FOLD.CREASE_W * 1.25,
                  FOLD.CREASE_DEPTH * strength) * side_w


def hang_flutes(theta, v, v0, v1, n_flutes, amp=FOLD.HANG_AMP, uid=0.0,
                wander=1.15):
    """Longitudinal flutes on a free-hanging tube.

    Amplitude ramps from 0 at the suspended end to full at the free end, the
    phase drifts slowly along the tube (a real flute wanders across the cloth
    instead of running dead straight), and the crest profile is the stiff-
    fabric one so the flutes read as folds rather than as corrugation.
    """
    t = clamp01((v - v0) / max(v1 - v0, 1e-9))
    ramp = sstep(0.0, 0.55, t) * (1.0 - 0.25 * sstep(0.82, 1.0, t))
    ph = 6.283 * hash01(uid, n_flutes, "hang") + \
        wander * (fbm1(v * 4.4 + hash01(uid, "w") * 40.0, seed=11) - 0.5) * 6.283
    return amp * ramp * crest(n_flutes * theta + ph, 0.75)


def tension_folds(theta, v, src_theta, src_v, dirn, amp=FOLD.TENSION_AMP,
                  lam=0.085, reach=0.30, uid=0.0):
    """Diagonal folds radiating from a suspension point (shoulder, belt)."""
    du = (theta - src_theta) * 0.195
    dv = v - src_v
    r = np.sqrt(du * du + dv * dv)
    proj = du * dirn[0] + dv * dirn[1]
    fall = np.exp(-(r / reach) ** 1.6)
    ph = 6.283 * hash01(uid, src_v, "ten")
    return amp * fall * crest(6.283 * proj / lam + ph, 0.4)


def micro_crumple(theta, v, uid=0.0, amp=FOLD.MICRO_AMP, scale=1.0,
                  ku=21.0, kv=19.0):
    """The 25-60 mm unevenness that stops cloth looking extruded.

    2.2 mm at 373 px/m is 0.8 px of relief with a 10-22 px wavelength: it is
    the difference between 'garment' and 'tube', and it has to be geometry
    because a bump map on a straight silhouette still reads as a tube.
    """
    a = theta * 0.145 + hash01(uid, "cx") * 30.0
    b = v + hash01(uid, "cy") * 30.0
    f = (fbm2(a * ku * scale, b * kv * scale, seed=int(uid * 977) % 9973,
              oct=3, gain=0.52) - 0.5)
    g = (fbm2(a * ku * 2.5 * scale, b * kv * 2.5 * scale,
              seed=(int(uid * 331) + 55) % 9973, oct=2, gain=0.5) - 0.5)
    # squared, not sinusoidal: cloth is flat panels separated by creases, and a
    # smooth sine over a limb reads as muscle.  This is the single change that
    # stopped the first build looking like an anatomy study.
    return amp * np.tanh(3.1 * (1.75 * f + 0.62 * g)) / math.tanh(1.35)


def fold_stack(theta, v, cfg):
    """Compose the named mechanisms for one piece.  cfg is a dict of lists."""
    d = np.zeros_like(v)
    for (vj, fr, sw, ph) in cfg.get("flex", []):
        d = d + flex_folds(v, vj, fr, sw, cfg["uid"], ph)
    for (vj, fr, sw, mem) in cfg.get("crease", []):
        d = d + set_crease(v, vj, fr, sw, mem)
    for (v0, v1, nf, amp) in cfg.get("hang", []):
        d = d + hang_flutes(theta, v, v0, v1, nf, amp, cfg["uid"])
    for (st, sv, dirn, amp, lam, reach) in cfg.get("tension", []):
        d = d + tension_folds(theta, v, st, sv, dirn, amp, lam, reach,
                              cfg["uid"])
    if cfg.get("micro", True):
        d = d + micro_crumple(theta, v, cfg["uid"],
                              cfg.get("micro_amp", FOLD.MICRO_AMP),
                              cfg.get("micro_scale", 1.0))
    return d


# --------------------------------------------------------------------------- #
#  7.  swept surfaces                                                           #
# --------------------------------------------------------------------------- #

def sect_normal(theta, a, b, nexp):
    """Outward unit normal of a superellipse, in section (u, v) coordinates."""
    ct, st = np.cos(theta), np.sin(theta)
    e = 2.0 / nexp
    x = np.sign(ct) * np.abs(ct) ** e
    y = np.sign(st) * np.abs(st) ** e
    gx = (nexp / np.maximum(a, 1e-9)) * np.abs(x) ** (nexp - 1.0) * np.sign(x)
    gy = (nexp / np.maximum(b, 1e-9)) * np.abs(y) ** (nexp - 1.0) * np.sign(y)
    L = np.sqrt(gx * gx + gy * gy) + 1e-12
    return gx / L, gy / L


class Piece:
    """A swept surface: (R rows, N cols) of positions, params and indices."""

    __slots__ = ("P", "TH", "V", "IDX", "A", "B", "NEXP", "path", "U", "W",
                 "R", "N", "name", "circ")

    def __init__(self, name):
        self.name = name


def sweep(path, U, V, A, B, NEXP, N, theta0=0.5 * math.pi, theta_dir=-1.0,
          disp=None, sag=None, name="p"):
    """Build a swept superelliptic tube.

    path (R,3), U/V (R,3) section axes, A/B (R,) semi-axes, NEXP (R,).
    Column j has theta = theta0 + theta_dir * 2*pi*j/N, so with the defaults
    j=0 is FRONT, j=N/4 is the figure's RIGHT, j=N/2 is BACK.  Every piece in
    this module uses that convention, which is what lets the trouser legs take
    the trunk's ring halves without a lookup table.

    disp(TH, VV, RR) -> radial displacement in metres (may be None).
    sag(VV) -> (dx, dy, dz) world offset applied to the whole ring.
    """
    R = len(path)
    j = np.arange(N)
    TH = (theta0 + theta_dir * 2.0 * math.pi * j / N)[None, :].repeat(R, 0)
    AA = np.asarray(A, float)[:, None]
    BB = np.asarray(B, float)[:, None]
    NN = np.asarray(NEXP, float)[:, None]
    x, y = superellipse(TH, AA, BB, NN)
    nx, ny = sect_normal(TH, AA, BB, NN)
    s = arclen(np.asarray(path, float))
    VV = s[:, None].repeat(N, 1)
    # CURVATURE GUARD.  A swept tube folds through itself on the inside of a
    # bend whose radius of curvature is smaller than the tube's own radius --
    # a 96 deg knee is exactly that case, and it produced a black knot at the
    # ankle of every kneeling figure.  Shrink the section there instead, and
    # push the ring centre outboard of the bend so the limb keeps its volume.
    P0a = np.asarray(path, float)
    d1 = np.gradient(P0a, axis=0)
    d2 = np.gradient(d1, axis=0)
    sp = np.maximum(np.linalg.norm(d1, axis=1), 1e-9)
    kap = np.linalg.norm(np.cross(d1, d2), axis=1) / (sp ** 3)
    Rcur = 1.0 / np.maximum(kap, 1e-6)
    lim = np.maximum(Rcur * 0.80, 0.012)
    rmax = np.maximum(AA[:, 0], BB[:, 0])
    shrink = np.minimum(1.0, lim / np.maximum(rmax, 1e-9))
    shrink = np.minimum.accumulate(
        np.minimum(shrink, np.roll(shrink, 1)))[::-1][::-1]
    sm = np.convolve(shrink, np.ones(9) / 9.0, mode='same')
    sm[:4] = shrink[:4]; sm[-4:] = shrink[-4:]
    sm = np.clip(sm, 0.45, 1.0)[:, None]
    x = x * sm
    y = y * sm
    AA = AA * sm; BB = BB * sm
    RR = np.sqrt(x * x + y * y)
    if disp is not None:
        d = disp(TH, VV, RR)
        x = x + nx * d
        y = y + ny * d
    Pt = (np.asarray(path, float)[:, None, :]
          + np.asarray(U, float)[:, None, :] * x[:, :, None]
          + np.asarray(V, float)[:, None, :] * y[:, :, None])
    if sag is not None:
        Pt = Pt + sag(VV)[..., :]
    pc = Piece(name)
    pc.P, pc.TH, pc.V = Pt, TH, VV
    pc.A, pc.B, pc.NEXP = AA, BB, NN
    pc.path, pc.U, pc.W = np.asarray(path, float), np.asarray(U, float), \
        np.asarray(V, float)
    pc.R, pc.N = R, N
    # circumferential arc-length coordinate, in metres, for the weave and for
    # seam distances that must be measured ON the cloth
    dxy = np.sqrt(np.diff(x, axis=1, append=x[:, :1]) ** 2
                  + np.diff(y, axis=1, append=y[:, :1]) ** 2)
    pc.circ = np.cumsum(dxy, axis=1) - dxy[:, :1]
    return pc


def piece_normals(P, wrap=True):
    """Per-vertex normals of a grid, outward if the winding is ok."""
    R, N, _ = P.shape
    dv = np.zeros_like(P)
    dv[1:-1] = P[2:] - P[:-2]
    dv[0] = P[1] - P[0]
    dv[-1] = P[-1] - P[-2]
    if wrap:
        du = np.roll(P, -1, 1) - np.roll(P, 1, 1)
    else:
        du = np.zeros_like(P)
        du[:, 1:-1] = P[:, 2:] - P[:, :-2]
        du[:, 0] = P[:, 1] - P[:, 0]
        du[:, -1] = P[:, -1] - P[:, -2]
    n = np.cross(du, dv)
    return _norm(n)


def bilerp(P, r, c, wrap=True):
    """Sample a grid at fractional (row, col)."""
    R, N = P.shape[0], P.shape[1]
    r = np.clip(np.asarray(r, float), 0, R - 1.001)
    c = np.asarray(c, float)
    r0 = r.astype(int); r1 = np.minimum(r0 + 1, R - 1)
    fr = (r - r0)[..., None]
    if wrap:
        c = c % N
        c0 = c.astype(int); c1 = (c0 + 1) % N
    else:
        c = np.clip(c, 0, N - 1.001)
        c0 = c.astype(int); c1 = np.minimum(c0 + 1, N - 1)
    fc = (c - c0)[..., None]
    return ((P[r0, c0] * (1 - fc) + P[r0, c1] * fc) * (1 - fr)
            + (P[r1, c0] * (1 - fc) + P[r1, c1] * fc) * fr)


def stitch_run(acc, pts, nrm, tan, pitch=0.0032, duty=0.56, w=0.0018,
               h=0.00042, mat=MAT_EMB, base=(0.06, 0.06, 0.06, 0.0),
               aux=(0.0, 0.6, 0.0, 0.0), wear=(0.0, 0.0, 0.0, 0.0),
               jitter=0.00016, uid=0.0):
    """Real topstitch: one lifted bead per stitch, 3.2 mm pitch.

    1.8 x 3.2 mm at 373 px/m is 0.67 x 1.2 screen pixels -- right at the
    resolution limit, which is exactly where geometry stops being optional and
    a bump map starts to shimmer.  The beads are lifted 0.42 mm and jittered,
    because a machine-sewn line that is perfectly straight reads as a decal.
    """
    pts = np.asarray(pts, float)
    if len(pts) < 2:
        return
    s = arclen(pts)
    L = s[-1]
    if L < pitch * 2:
        return
    m = int(L / pitch)
    sv = (np.arange(m) + 0.5) * pitch
    P = np.zeros((m, 3)); Nn = np.zeros((m, 3)); Tt = np.zeros((m, 3))
    for k in range(3):
        P[:, k] = np.interp(sv, s, pts[:, k])
        Nn[:, k] = np.interp(sv, s, nrm[:, k])
        Tt[:, k] = np.interp(sv, s, tan[:, k])
    Nn = _norm(Nn); Tt = _norm(Tt)
    Bt = _norm(np.cross(Tt, Nn))
    jj = (np.array([hash01(uid, i, "sj") for i in range(m)]) - 0.5) * 2.0
    kk = np.array([hash01(uid, i, "sk") for i in range(m)])
    half = pitch * duty * 0.5
    lift = h * (0.72 + 0.56 * kk)
    off = Bt * (jj * jitter)[:, None]
    A = P - Tt * half + off + Nn * (lift * 0.35)[:, None]
    Bp = P + Tt * half + off + Nn * (lift * 0.35)[:, None]
    ww = w * 0.5
    V = np.concatenate([
        A - Bt * ww, Bp - Bt * ww, Bp + Bt * ww, A + Bt * ww,
        P + Nn * lift[:, None] + off - Bt * (ww * 0.42) - Tt * (half * 0.55),
        P + Nn * lift[:, None] + off + Bt * (ww * 0.42) - Tt * (half * 0.55),
        P + Nn * lift[:, None] + off + Bt * (ww * 0.42) + Tt * (half * 0.55),
        P + Nn * lift[:, None] + off - Bt * (ww * 0.42) + Tt * (half * 0.55),
    ], 0)
    i0 = acc.verts(V, uv=np.tile([[0.0, 0.0]], (len(V), 1)),
                   base=base, aux=aux, wear=wear)
    a, b, c, d = i0, i0 + m, i0 + 2 * m, i0 + 3 * m
    e, f, g, hh = i0 + 4 * m, i0 + 5 * m, i0 + 6 * m, i0 + 7 * m
    r = np.arange(m)
    Q = np.concatenate([
        np.stack([a + r, e + r, hh + r, d + r], -1),     # near side wall
        np.stack([e + r, f + r, g + r, hh + r], -1),     # crown
        np.stack([f + r, b + r, c + r, g + r], -1),      # far side wall
    ], 0)
    acc.quads(Q, mat, smooth=True)


# --------------------------------------------------------------------------- #
#  8.  the teams  (LAW 2: every name comes out of the existing brand book)      #
# --------------------------------------------------------------------------- #

_BRANDS = None


def brand_book():
    """The 31 invented brands, imported from build_dressing.  Never forked.

    Inventing a 32nd brand fragments the world's identity, so this refuses to
    fall back to a local copy: if the brand book cannot be imported the build
    stops instead of quietly making one up.
    """
    global _BRANDS
    if _BRANDS is None:
        import build_dressing as D
        _BRANDS = D.BRANDS
    return _BRANDS


class Team:
    __slots__ = ("name", "shell", "accent", "trim", "stitch", "title",
                 "second", "sleeve_brand", "dark")

    def __init__(self, name, shell, accent, trim, stitch, title, second,
                 sleeve_brand):
        self.name = name
        self.shell = shell
        self.accent = accent
        self.trim = trim
        self.stitch = stitch
        self.title = title
        self.second = second
        self.sleeve_brand = sleeve_brand
        self.dark = (0.2126 * shell[0] + 0.7152 * shell[1]
                     + 0.0722 * shell[2]) < 0.10


_TEAMS = None


def teams():
    """Ten pit crews.  Colourways are BUILT from the brand book's own palette,
    so a VERSANT crew wears VERSANT navy and the boards say the same thing."""
    global _TEAMS
    if _TEAMS is not None:
        return _TEAMS
    B = {b[0]: b for b in brand_book()}

    def col(nm, which):
        return srgb(B[nm][1] if which == "bg" else B[nm][2])

    def mixc(a, b, t):
        return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))

    spec = [
        # team title,   shell from,        accent from,   trim,   second, sleeve
        ("VERSANT",     ("VERSANT", "bg"), ("VERSANT", "fg"), "CIRRUS",
         "OCTAL", "NORDVAL"),
        ("OCTAL",       ("OCTAL", "bg"),   ("OCTAL", "fg"),   "CADENCE",
         "PYLON", "CALIBRE"),
        ("CADENCE",     ("CADENCE", "bg"), ("CADENCE", "fg"), "OBSIDIAN",
         "SABLIER", "VERITAS"),
        ("SEPTIME",     ("SEPTIME", "bg"), ("SEPTIME", "fg"), "BRIAR",
         "TERRA NOVA", "HALCYON"),
        ("PALLAS",      ("PALLAS", "bg"),  ("PALLAS", "fg"),  "PRIMEUR",
         "VERITAS", "OBSIDIAN"),
        ("ZEPHYR",      ("ZEPHYR", "bg"),  ("ZEPHYR", "fg"),  "ALTIS",
         "CIRRUS", "FONTAINE"),
        ("NOVEM",       ("NOVEM", "bg"),   ("NOVEM", "fg"),   "MARENGO",
         "PRIMEUR", "ORTHO"),
        ("LUMIERE",     ("LUMIERE", "bg"), ("LUMIERE", "fg"), "VOLTAIC",
         "ARDENT", "MERIDIAN"),
        ("MARQUE",      ("MARQUE", "bg"),  ("MARQUE", "fg"),  "OBSIDIAN",
         "MERIDIAN", "ATELIER 9"),
        ("ARDENT",      ("ARDENT", "bg"),  ("ARDENT", "fg"),  "LUMIERE",
         "VOLTAIC", "KESTREL"),
    ]
    out = []
    for i, (nm, sh, ac, tr, sec, slv) in enumerate(spec):
        shell = col(*sh)
        # a fireproof shell is dyed, not printed: pull it a little off the
        # brand's flat brand-guide colour so ten crews are not ten swatches
        shell = mixc(shell, (0.055, 0.052, 0.050), 0.10 + 0.07 * hash01(i, "sh"))
        accent = col(*ac)
        trim = srgb(B[tr][1]) if hash01(i, "tr") < 0.5 else srgb(B[tr][2])
        # thread is a different fibre in a different bath: on a dark shell it
        # is lighter, on a light shell darker, never the same value as either
        shl = 0.2126 * shell[0] + 0.7152 * shell[1] + 0.0722 * shell[2]
        stitch = (mixc(accent, (0.78, 0.76, 0.70), 0.55) if shl < 0.11
                  else mixc(accent, (0.035, 0.033, 0.030), 0.62))
        out.append(Team(nm, shell, accent, trim, stitch, nm, sec, slv))
    _TEAMS = out
    return out


# crew first names / surnames: invented, deliberately pan-European paddock
_FIRST = ["LUC", "MATEO", "JENS", "PAVEL", "TOMAS", "ANDRE", "RUBEN", "KAI",
          "SIMON", "MARCO", "OLLIE", "NIKO", "SASHA", "EMIL", "DAAN", "GIL",
          "RAFA", "BRUNO", "IVAN", "ARNE", "COLM", "TEO", "JORIS", "MILO"]
_LAST = ["VANTIER", "KROLL", "BASSAN", "REMY", "DELOUX", "HAVERS", "MONTEL",
         "SIKORA", "BRENNAN", "LAUDET", "OSTBY", "MERCIER", "FALK", "ROVIRA",
         "TAMM", "GILLET", "PERRAULT", "NAUDIN", "STEENS", "CARRAZ",
         "LINDQVIST", "BOUVET", "ARLETT", "DUMAS"]


# --------------------------------------------------------------------------- #
#  9.  the per-instance draw                                                    #
# --------------------------------------------------------------------------- #

class SuitSpec:
    __slots__ = ("uid", "build", "pose", "team", "collar_up", "sleeve_push",
                 "zip_open", "belt_cinch", "knee_dirt", "shin_wear",
                 "age", "dirt", "oil", "fade", "res", "name_tape",
                 "chest_pocket", "thigh_pocket", "epaulette", "cuff_style",
                 "leg_len", "sleeve_len", "hem_roll", "number", "dyelot",
                 "kneel_side", "tuck")

    def __repr__(self):
        return ("SuitSpec(uid=%d %s %s %s collar=%s push=%.2f)"
                % (self.uid, self.build.name, self.pose.name, self.team.name,
                   self.collar_up, self.sleeve_push))


def suit_spec(uid, **over):
    """Deterministic per-instance draw.  Overrides win.

    The manifest's variation_axes are all here and all of them move GEOMETRY,
    not just colour:
        team colours      -> panel colour blocking AND which panels exist
        collar up/down    -> two different collar constructions
        sleeves pushed up -> the sleeve is shortened and the excess becomes a
                             real bunched torus at the forearm
        knee dirt         -> wear channel + a glazed, bagged knee panel
        kneeling wear     -> shin abrasion + the shin cloth is pulled tight
        fit by build      -> 8 anthropometries, girths solved from real
                             circumferences
    plus pose (20), stature (1.65-1.93 m), dye lot, hem roll, pocket set,
    epaulettes, cuff style, name tape and mesh resolution.
    """
    s = SuitSpec()
    s.uid = int(uid)
    u = float(uid)
    s.build = BUILDS[pick(BUILD_NAMES, u, "build")]
    s.pose = POSES[pick(POSE_NAMES, u, "pose")]
    s.team = teams()[int(hash01(u, "team") * len(teams())) % len(teams())]
    s.collar_up = chance(0.34, u, "collar")
    s.sleeve_push = (rnd(0.10, 0.30, u, "push") if chance(0.30, u, "pushq")
                     else 0.0)
    s.zip_open = rnd(0.0, 0.16, u, "zip") if chance(0.35, u, "zipq") else 0.0
    s.belt_cinch = rnd(0.55, 1.0, u, "belt")
    s.knee_dirt = rnd(0.10, 0.95, u, "knee")
    s.shin_wear = rnd(0.05, 0.85, u, "shin")
    s.age = rnd(0.05, 0.92, u, "age")
    s.dirt = rnd(0.06, 0.80, u, "dirt")
    s.oil = rnd(0.0, 0.75, u, "oil")
    s.fade = rnd(0.05, 0.85, u, "fade")
    s.res = 1.0
    s.name_tape = "%s %s" % (pick(_FIRST, u, "fn"), pick(_LAST, u, "ln"))
    s.number = rint(2, 79, u, "num")
    s.chest_pocket = chance(0.72, u, "cp")
    s.thigh_pocket = chance(0.46, u, "tp")
    s.epaulette = chance(0.58, u, "ep")
    s.cuff_style = pick(["knit", "knit", "knit", "tab"], u, "cuff")
    s.leg_len = rnd(0.985, 1.022, u, "ll")
    s.sleeve_len = rnd(0.975, 1.028, u, "sl")
    s.hem_roll = chance(0.30, u, "hr")
    s.dyelot = rnd(0.0, 1.0, u, "dl")
    s.tuck = chance(0.42, u, "tuck")
    for k, v in over.items():
        if k == "build" and isinstance(v, str):
            v = BUILDS[v]
        if k == "pose" and isinstance(v, str):
            v = POSES[v]
        if k == "team" and isinstance(v, int):
            v = teams()[v % len(teams())]
        setattr(s, k, v)
    s.kneel_side = KNEELING.get(s.pose.name, ())
    if s.kneel_side:
        s.knee_dirt = max(s.knee_dirt, 0.62)
        s.shin_wear = max(s.shin_wear, 0.48)
    return s


# --------------------------------------------------------------------------- #
# 10.  surface utilities: axes along a chain, appliques, bands                   #
# --------------------------------------------------------------------------- #

def chain_axes(path, keyP, keyF, front_col=1):
    """Section axes (Ex = lateral right, Ey = anterior) along a limb.

    The anterior direction is carried from the BONE frames, not from a fixed
    world vector, so a flexed elbow's sleeve seam stays on the outside of the
    forearm instead of spiralling round it.
    """
    P = np.asarray(path, float)
    R = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T = _norm(T)
    ks = arclen(np.asarray(keyP, float))
    ks = ks / max(ks[-1], 1e-9)
    s = arclen(P)
    s = s / max(s[-1], 1e-9)
    Fy = np.zeros((R, 3))
    for k in range(3):
        Fy[:, k] = np.interp(s, ks, [f[:, front_col][k] for f in keyF])
    Fy = _norm(Fy)
    Ey = _norm(Fy - T * np.sum(Fy * T, axis=1, keepdims=True))
    Ex = _norm(np.cross(Ey, -T))
    return T, Ex, Ey


def emit_piece(acc, pc, base, aux, wear, mat=MAT_SHELL, wrap=True, flip=False,
               rows=None):
    R, N = pc.R, pc.N
    uv = np.stack([pc.circ, pc.V], -1).reshape(-1, 2)
    i0 = acc.verts(pc.P.reshape(-1, 3), uv=uv,
                   base=np.asarray(base).reshape(-1, 4),
                   aux=np.asarray(aux).reshape(-1, 4),
                   wear=np.asarray(wear).reshape(-1, 4))
    IDX = i0 + np.arange(R * N).reshape(R, N)
    sub = IDX if rows is None else IDX[rows[0]:rows[1]]
    acc.grid_faces(sub, mat, wrap_u=wrap, flip=flip)
    return IDX


def rrect_mask(gr, gc, hr, hc, rad):
    """Signed inside-ness of a rounded rectangle in grid units (>0 inside)."""
    ar = np.abs(gr) - (hr - rad)
    ac = np.abs(gc) - (hc - rad)
    ar = np.maximum(ar, 0.0); ac = np.maximum(ac, 0.0)
    outside = np.sqrt(ar * ar + ac * ac) - rad
    inner = np.minimum(hr - np.abs(gr), hc - np.abs(gc))
    return np.where((np.abs(gr) > hr - rad) & (np.abs(gc) > hc - rad),
                    -outside, inner)


def patch_on(acc, pc, NRM, rc, cc, hr, hc, lift, mat, base, aux, wear,
             nr=None, nc=None, rad=0.30, bead=0.0, bead_col=None,
             uid=0.0, wrap=True, uvscale=1.0, tilt=0.0):
    """A rounded-rect applique lying ON the piece's surface.

    Built by sampling the host surface, so a pocket on a folded sleeve folds
    with it.  `lift` is the applique's thickness (m); `bead` adds a raised
    satin-stitch border, which is what makes an embroidered patch read as
    embroidery rather than as a sticker at 373 px/m.
    Returns (IDX grid, centre point, normal) for landmarks.
    """
    nr = nr or max(int(hr * 2) + 3, 7)
    nc = nc or max(int(hc * 2) + 3, 7)
    gr = np.linspace(-hr, hr, nr)[:, None].repeat(nc, 1)
    gc = np.linspace(-hc, hc, nc)[None, :].repeat(nr, 0)
    if tilt:
        t = math.radians(tilt)
        gr2 = gr * math.cos(t) - gc * math.sin(t)
        gc2 = gr * math.sin(t) + gc * math.cos(t)
    else:
        gr2, gc2 = gr, gc
    ins = rrect_mask(gr, gc, hr, hc, rad * min(hr, hc))
    edge = clamp01(ins / max(0.45 * min(hr, hc), 1e-6))
    P = bilerp(pc.P, rc + gr2, cc + gc2, wrap)
    Nn = _norm(bilerp(NRM, rc + gr2, cc + gc2, wrap))
    h = lift * (0.30 + 0.70 * sstep(0.0, 1.0, edge))
    if bead > 0.0:
        h = h + bead * np.exp(-((edge - 0.16) / 0.15) ** 2)
    P = P + Nn * h[..., None]
    # roll the outer ring under so the applique has a real edge, not a cliff
    outer = ins <= 0.0
    P[outer] = bilerp(pc.P, (rc + gr2)[outer], (cc + gc2)[outer], wrap) \
        + Nn[outer] * (lift * 0.10)
    uu = (gc * uvscale)[..., None]
    vv = (gr * uvscale)[..., None]
    uv = np.concatenate([uu, vv], -1).reshape(-1, 2)
    bb = np.asarray(base, float)
    if bb.ndim == 1:
        bb = np.tile(bb, (nr * nc, 1))
    if bead_col is not None:
        m = np.exp(-((edge - 0.16) / 0.15) ** 2).reshape(-1)[:, None]
        bb = bb * (1 - m) + np.asarray(bead_col, float)[None, :] * m
    i0 = acc.verts(P.reshape(-1, 3), uv=uv, base=bb,
                   aux=aux, wear=wear)
    IDX = i0 + np.arange(nr * nc).reshape(nr, nc)
    acc.grid_faces(IDX, mat, wrap_u=False, flip=False)
    ctr = bilerp(pc.P, np.array([rc]), np.array([cc]), wrap)[0]
    nn = _norm(bilerp(NRM, np.array([rc]), np.array([cc]), wrap))[0]
    return IDX, ctr, nn


def seam_curve(pc, NRM, col, r0, r1, off_cols=0.0):
    """Sample a longitudinal seam line: points, normals, tangents."""
    rr = np.arange(r0, r1, dtype=float)
    cc = np.full_like(rr, col + off_cols)
    P = bilerp(pc.P, rr, cc)
    Nn = _norm(bilerp(NRM, rr, cc))
    T = np.gradient(P, axis=0)
    return P, Nn, _norm(T)


def ring_curve(pc, NRM, row, c0=0, c1=None, off_rows=0.0):
    """Sample a transverse seam line around the piece."""
    c1 = pc.N if c1 is None else c1
    cc = np.arange(c0, c1, dtype=float)
    rr = np.full_like(cc, row + off_rows)
    P = bilerp(pc.P, rr, cc)
    Nn = _norm(bilerp(NRM, rr, cc))
    T = np.gradient(P, axis=0)
    return P, Nn, _norm(T)


# --------------------------------------------------------------------------- #
# 11.  the sections                                                             #
# --------------------------------------------------------------------------- #
#   p       a        b       n      what
# p = 0 sits at 0.500 H (just above the crotch) and p = 1 at 0.880 H, so the
# trunk carries the SEAT.  The first build split the legs off at the hip and
# the seat had to be invented by the blend, which produced a loincloth.
TRUNK_SECT = [
    (0.00, 0.1012, 0.0748, 2.30),   # crotch level, where the legs take over
    (0.04, 0.1008, 0.0754, 2.31),   # ... left parallel on purpose: see below
    (0.08, 0.0995, 0.0762, 2.32),   # the seat, widest
    (0.16, 0.1000, 0.0755, 2.36),
    (0.26, 0.0930, 0.0716, 2.40),   # waist, 92 cm with ease
    (0.38, 0.0972, 0.0754, 2.42),
    (0.48, 0.1030, 0.0800, 2.44),
    (0.58, 0.1076, 0.0832, 2.45),   # chest, 107 cm with ease
    (0.66, 0.1070, 0.0822, 2.46),   # armpit
    (0.80, 0.1042, 0.0792, 2.50),   # shoulder, under the sleeve caps
    (0.88, 0.0898, 0.0690, 2.50),
    (0.95, 0.0638, 0.0558, 2.30),
    (1.00, 0.0452, 0.0428, 2.15),   # neck
]
#   t along the leg from the split (0) to the cuff (1)
# Radii are SOLVED from circumference, not guessed: at H = 1.78 m these give
# thigh 62 cm, above-knee 48 cm, knee 44 cm, calf 45 cm, ankle cuff 27 cm --
# a 60 cm thigh with 2 cm of ease, which is what a Nomex leg measures.  The
# first build of this file guessed 0.079 H and produced an 88 cm thigh.
LEG_SECT = [
    (0.00, 0.0578, 0.0585, 2.12),   # top of thigh, still forming the seat
    (0.12, 0.0548, 0.0544, 2.10),
    (0.30, 0.0498, 0.0492, 2.08),
    (0.50, 0.0448, 0.0440, 2.06),   # above the knee -- cloth, not a base layer
    (0.60, 0.0424, 0.0416, 2.04),   # knee
    (0.70, 0.0428, 0.0412, 2.04),   # calf, cloth hangs OFF it
    (0.84, 0.0378, 0.0366, 2.04),
    (0.95, 0.0292, 0.0286, 2.02),
    (1.00, 0.0244, 0.0240, 2.02),   # ankle cuff, gathered over a boot top
]
#   t along the arm from the cap (0) to the wrist (1)
# Same solve: upper arm 37 cm, elbow 32 cm, forearm 26 cm, wrist cuff 18 cm.
SLV_SECT = [
    (0.00, 0.0428, 0.0414, 2.14),   # the cap, over the deltoid
    (0.10, 0.0388, 0.0376, 2.10),
    (0.28, 0.0352, 0.0344, 2.08),
    (0.46, 0.0318, 0.0311, 2.06),   # elbow
    (0.62, 0.0300, 0.0293, 2.05),
    (0.80, 0.0262, 0.0255, 2.04),
    (0.92, 0.0208, 0.0203, 2.03),
    (1.00, 0.0172, 0.0168, 2.02),   # wrist cuff
]


def sect_interp(keys, p, H, sa=1.0, sb=1.0):
    ps = np.array([k[0] for k in keys])
    A = np.interp(p, ps, [k[1] for k in keys]) * H * sa
    B = np.interp(p, ps, [k[2] for k in keys]) * H * sb
    Nx = np.interp(p, ps, [k[3] for k in keys])
    return A, B, Nx


def dtheta(a, b):
    """signed angular difference wrapped to (-pi, pi]"""
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return d


class Suit:
    __slots__ = ("obj", "spec", "skel", "landmarks", "tris", "verts", "name")


def build_suit(spec, coll, mats, name=None, place=None):
    """One garment.  `place` is an optional (3,) world translation applied to
    the whole figure AFTER the local build (feet already sit on z = 0)."""
    b = spec.build
    H = b.H
    uid = float(spec.uid)
    skel = Skeleton(b, spec.pose)
    J, F = skel.J, skel.F
    T = spec.team
    shell = np.array(T.shell, float)
    accent = np.array(T.accent, float)
    trim = np.array(T.trim, float)
    # Trim dyed in the same bath as the shell never reaches the brand-guide
    # value; a pure #f4f4f4 collar on a navy suit reads as a bib.
    def knock(c, k):
        return c * (1.0 - k) + shell * k
    accent_trim = knock(accent, 0.42)
    accent_soft = knock(accent, 0.62)
    nm = name or ("Suit%03d" % spec.uid)
    acc = Acc(PFX + nm)
    LM = {}
    res = spec.res
    E_TRUNK = 0.0070 / max(res, 0.2)
    E_LIMB = 0.0064 / max(res, 0.2)

    dl = spec.dyelot

    def paint(nverts_shape, col, panel=0.0, sheen=0.0, dye=0.0):
        bb = np.zeros(nverts_shape + (4,))
        bb[..., 0], bb[..., 1], bb[..., 2] = col[0], col[1], col[2]
        bb[..., 3] = dl * 0.6 + dye
        aa = np.zeros(nverts_shape + (4,))
        aa[..., 1] = sheen
        aa[..., 2] = panel
        aa[..., 3] = (uid * 0.61803398875) % 1.0
        return bb, aa

    # ======================================================================
    #  TRUNK
    # ======================================================================
    keyP = [J["pelvis"] + F["pelvis"] @ np.array([0, 0, -0.040 * H]),
            J["spine1"], J["spine2"], J["spine3"], J["neck"],
            J["neck"] + F["neck"] @ np.array([0, 0.004 * H, 0.030 * H])]
    keyF = [F["pelvis"], F["spine1"], F["spine2"], F["spine3"], F["neck"],
            F["neck"]]
    raw = catmull(np.array(keyP), 160)
    L_tr = arclen(raw)[-1]
    R_tr = max(int(L_tr / E_TRUNK), 40)
    path = resample(raw, R_tr)
    Tt, Ex, Ey = chain_axes(path, keyP, keyF)
    p = np.linspace(0.0, 1.0, R_tr)
    sa = 0.34 + 0.66 * b.girth
    sb = 0.28 + 0.72 * b.girth
    A, B, NX = sect_interp(TRUNK_SECT, p, H, sa, sb)
    # shoulders scale independently of girth
    shw = 1.0 + (b.shoulder - 1.0) * sstep(0.58, 0.86, p)
    A = A * shw
    # belly: volume goes to the lower FRONT, and it moves the section forward
    win = np.exp(-((p - 0.26) / 0.20) ** 2)
    B = B + b.belly * 0.026 * H * win
    path = path + Ey * (b.belly * 0.014 * H * win)[:, None]
    # the buttocks: the section centre moves BACK over the seat, which is what
    # gives an overall its rear silhouette
    seatw = np.exp(-((p - 0.135) / 0.150) ** 2)
    path = path - Ey * (0.0125 * H * seatw)[:, None]

    v_all = arclen(path)
    L = v_all[-1]
    v_waist = float(np.interp(0.26, p, v_all))
    v_belt = float(np.interp(0.285, p, v_all))
    v_yoke = float(np.interp(0.735, p, v_all))
    v_chest = float(np.interp(0.575, p, v_all))
    v_arm = float(np.interp(0.660, p, v_all))

    waist_flex = math.radians(abs(spec.pose.j.get("spine1", (0, 0, 0))[0]
                                  + spec.pose.j.get("spine2", (0, 0, 0))[0]))
    N_TR = int(round(max(A.max() * 2 * math.pi, 0.6) / E_TRUNK / 4.0)) * 4
    N_TR = max(N_TR, 96)
    if N_TR % 2:
        N_TR += 1

    plack_w = 0.0170                     # half width of the front placket
    belt_r = 0.0225                       # half width of the belt band

    def trunk_disp(TH, VV, RR):
        front = clamp01(np.cos(dtheta(TH, 0.5 * math.pi))) ** 1.5
        back = clamp01(np.cos(dtheta(TH, -0.5 * math.pi))) ** 1.5
        side = clamp01(np.abs(np.sin(dtheta(TH, 0.5 * math.pi)))) ** 2.0
        d = np.zeros_like(TH)
        # 1. the jacket skirt below the belt hangs in a few stiff flutes
        d += hang_flutes(TH, VV, v_belt, 0.0, rint(3, 5, uid, "tf"),
                         FOLD.HANG_AMP * 0.85, uid)
        # 2. a bend at the waist buckles the FRONT and stretches the back
        d += flex_folds(VV, v_waist, waist_flex, front * 0.9, uid)
        d += set_crease(VV, v_waist, waist_flex, front, 0.75)
        d -= 0.0022 * back * sstep(0.0, 0.6, waist_flex)
        # 3. the belt drags the cloth in and throws radial folds above it
        cinch = spec.belt_cinch
        d -= 0.0125 * cinch * np.exp(-((VV - v_belt) / 0.052) ** 2)
        d += 0.0068 * cinch * np.exp(-((VV - v_belt - 0.055) / 0.048) ** 2) \
            * crest(11.0 * TH + 3.1 * hash01(uid, "bg"), 0.9)
        # 4. suspension folds off both shoulders, and the chest strain between
        for sgn, key in ((1.0, "r"), (-1.0, "l")):
            st = 0.5 * math.pi - sgn * 0.9
            d += tension_folds(TH, VV, st, v_arm, (sgn * 0.94, -0.34),
                               FOLD.TENSION_AMP * 1.60, 0.088, 0.30, uid)
            d += tension_folds(TH, VV, -0.5 * math.pi + sgn * 0.85, v_arm,
                               (-sgn * 0.90, -0.44), FOLD.TENSION_AMP * 1.30,
                               0.098, 0.28, uid + 3.0)
        # 5. the yoke seam holds the cloth: a slight pull above, slack below
        d += 0.0016 * np.exp(-((VV - v_yoke) / 0.030) ** 2) * back
        # 6. micro crumple everywhere, stronger where the cloth is slack
        slack = 0.55 + 0.45 * sstep(0.30, 0.02, np.abs(VV - v_belt))
        d += micro_crumple(TH, VV, uid, FOLD.MICRO_AMP * 1.15,
                           ku=16.0, kv=7.5) * slack
        # ---- seams (mesh, 9.2 mm wide, 1.35 mm proud) ---------------------
        d += felled_seam(dtheta(TH, 0.0) * RR, side=1.0)          # right side
        d += felled_seam(dtheta(TH, math.pi) * RR, side=-1.0)     # left side
        d += felled_seam(VV - v_yoke, side=-1.0) * (VV > v_waist)  # yoke
        d += plain_seam(VV - v_belt) * 0.85                       # waist join
        return d

    trunk = sweep(path, Ex, Ey, A, B, NX, N_TR, disp=trunk_disp, name="trunk")
    NRM_tr = piece_normals(trunk.P)

    # ---- trunk colour blocking -------------------------------------------
    THt, VVt = trunk.TH, trunk.V
    pgrid = np.interp(VVt, v_all, p)
    col_tr = np.zeros(THt.shape + (3,))
    col_tr[:] = shell
    backw = clamp01(np.cos(dtheta(THt, -0.5 * math.pi)))
    # contrast yoke across the shoulders and upper back
    yoke = (sstep(v_yoke - 0.0016, v_yoke + 0.0016, VVt)
            * sstep(0.30, 0.42, backw))
    yoke = np.maximum(yoke, sstep(0.800, 0.806, pgrid))
    for k in range(3):
        col_tr[..., k] = col_tr[..., k] * (1 - yoke) + accent_trim[k] * yoke
    # a contrast side panel on some teams
    if chance(0.45, uid, "sidepanel"):
        sp = (np.exp(-((dtheta(THt, 0.0) / 0.30) ** 2))
              + np.exp(-((dtheta(THt, math.pi) / 0.30) ** 2)))
        sp = np.where(sp > 0.62, 1.0, 0.0) * sstep(0.050, 0.056, pgrid) \
            * (1 - sstep(0.800, 0.806, pgrid))
        for k in range(3):
            col_tr[..., k] = col_tr[..., k] * (1 - sp) + trim[k] * sp
    base_tr, aux_tr = paint(THt.shape, shell)
    base_tr[..., :3] = col_tr
    base_tr[..., 3] = dl * 0.6 + 0.4 * (yoke > 0.5)
    aux_tr[..., 0] = 0.0
    # seam mask for the shader's stitch relief and thread sheen
    aux_tr[..., 0] = np.maximum.reduce([
        np.exp(-((dtheta(THt, 0.0) * trunk.A[:, 0:1]) / 0.006) ** 2),
        np.exp(-((dtheta(THt, math.pi) * trunk.A[:, 0:1]) / 0.006) ** 2),
        np.exp(-((VVt - v_yoke) / 0.006) ** 2) * (VVt > v_waist),
        np.exp(-((VVt - v_belt) / 0.006) ** 2)])

    # ---- trunk wear -------------------------------------------------------
    wear_tr = np.zeros(THt.shape + (4,))
    frontw = clamp01(np.cos(dtheta(THt, 0.5 * math.pi)))
    upw = sstep(0.55, 0.95, pgrid)
    wear_tr[..., 0] = spec.age * (0.25 + 0.45 * upw * backw
                                  + 0.30 * np.exp(-((pgrid - 0.26) / 0.14) ** 2))
    wear_tr[..., 1] = spec.dirt * (0.30 + 0.55 * frontw
                                   * np.exp(-((pgrid - 0.14) / 0.18) ** 2)
                                   + 0.4 * fbm2(THt * 1.7, VVt * 5.0,
                                                seed=int(uid) % 811, oct=4))
    wear_tr[..., 2] = spec.oil * frontw * clamp01(
        fbm2(THt * 2.6 + uid, VVt * 7.5, seed=(int(uid) + 31) % 977, oct=4)
        * 1.9 - 0.75) * (1 - sstep(0.55, 0.80, pgrid))
    wear_tr[..., 3] = spec.fade * (0.42 + 0.58 * sstep(0.66, 0.86, pgrid))
    wear_tr = np.clip(wear_tr, 0.0, 1.0)

    IDX_tr = emit_piece(acc, trunk, base_tr, aux_tr, wear_tr, MAT_SHELL,
                        wrap=True, flip=True)

    # ======================================================================
    #  LEGS  --  real pants topology: each leg takes half of the trunk's
    #            bottom ring, and generates the inboard half at the crotch.
    # ======================================================================
    half = N_TR // 2
    up_p = F["pelvis"] @ np.array([0.0, 0.0, 1.0])
    leg_pieces = {}
    for side, sgn in (("r", 1.0), ("l", -1.0)):
        hipJ, kneeJ, ankJ = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        up_leg = F["hip_" + side] @ np.array([0.0, 0.0, 1.0])
        kP = [hipJ + up_leg * (0.035 * H), hipJ,
              hipJ + 0.5 * (kneeJ - hipJ), kneeJ,
              kneeJ + 0.5 * (ankJ - kneeJ), ankJ,
              # THE HEM STOPS AT THE BOOT TOP, ~125 mm off the deck.  Running it
              # past the ankle put the lowest garment vertex 0.1 mm above the
              # apron -- a trouser leg dragging on the ground, measured.
              ankJ + (kneeJ - ankJ) * (0.30 - 0.15 * spec.leg_len)]
        kF = [F["hip_" + side], F["hip_" + side], F["hip_" + side],
              F["knee_" + side], F["knee_" + side], F["ankle_" + side],
              F["ankle_" + side]]
        raw = catmull(np.array(kP), 400)
        # THE LEG PATH MUST START IN THE TRUNK'S BOTTOM-RING PLANE.  Starting it
        # above the hip made the blend target sit 97 mm higher than the ring it
        # blends from, so the first rows were pulled UP as they were pushed
        # down and the seat ended in a horizontal ledge across both thighs.
        z_split = float(trunk.P[0].mean(0)[2])
        r0 = int(np.argmin(np.abs(raw[:, 2] - z_split)))
        raw = raw[r0:]
        Lg = arclen(raw)[-1]
        R_lg = max(int(Lg / E_LIMB), 60)
        lpath = resample(raw, R_lg)
        Tl, Exl, Eyl = chain_axes(lpath, kP, kF)
        vg = arclen(lpath)
        tg = vg / vg[-1]
        Al, Bl, Nl = sect_interp(LEG_SECT, tg, H,
                                 0.40 + 0.60 * b.leg_g, 0.40 + 0.60 * b.leg_g)
        v_hip = float(np.interp(0.055, tg, vg))
        v_knee = float(vg[int(np.argmin(np.abs(
            np.linalg.norm(lpath - kneeJ, axis=1))))])
        v_cuff = vg[-1] - 0.062
        t_cuff = float(np.interp(v_cuff, vg, tg))
        knee_fx = math.radians(abs(spec.pose.j.get("knee_" + side,
                                                   (0, 0, 0))[0]))
        hip_fx = math.radians(max(spec.pose.j.get("hip_" + side,
                                                  (0, 0, 0))[0], 0.0))
        kneels = side in spec.kneel_side
        nflut = rint(3, 5, uid, "lf", side)
        out_th = 0.0 if side == "r" else math.pi        # outseam (lateral)
        in_th = math.pi if side == "r" else 0.0         # inseam (medial)

        def leg_disp(TH, VV, RR, v_knee=v_knee, v_hip=v_hip, knee_fx=knee_fx,
                     hip_fx=hip_fx, kneels=kneels, nflut=nflut,
                     out_th=out_th, in_th=in_th, side=side, v_cuff=v_cuff,
                     vend=vg[-1]):
            frontw = clamp01(np.cos(dtheta(TH, 0.5 * math.pi))) ** 1.5
            backw = clamp01(np.cos(dtheta(TH, -0.5 * math.pi))) ** 1.5
            d = np.zeros_like(TH)
            # the knee: folds behind it, and the crease it KEEPS
            d += flex_folds(VV, v_knee, knee_fx, backw, uid + 7.0)
            d += set_crease(VV, v_knee, knee_fx, backw, 1.0)
            # the hip: folds in front of it when the thigh comes up
            d += flex_folds(VV, v_hip + 0.03, hip_fx, frontw, uid + 11.0)
            d += set_crease(VV, v_hip + 0.03, hip_fx, frontw, 0.55)
            # the shin hangs free below the knee -> a few stiff flutes
            d += hang_flutes(TH, VV, v_knee + 0.02, v_cuff, nflut,
                             FOLD.HANG_AMP * 1.10,
                             uid + (1.0 if side == "r" else 2.0))
            # ... and the thigh hangs off the seat
            d += hang_flutes(TH, VV, v_hip, v_knee - 0.05, max(nflut - 1, 3),
                             FOLD.HANG_AMP * 0.72, uid + 21.0)
            # the cuff gathers the leg in and the cloth stacks above it
            d -= 0.0105 * np.exp(-((VV - vend) / 0.055) ** 2)
            d += 0.0046 * np.exp(-((VV - v_cuff + 0.026) / 0.034) ** 2) \
                * crest(7.0 * TH + 5.0 * hash01(uid, "cg", side), 0.85)
            # the break over the boot top: 2 transverse ripples, the thing
            # that says 'these are trousers over boots' at any distance
            brk = 0.0040 * np.exp(-((VV - v_cuff + 0.062) / 0.048) ** 2)
            d += brk * crest(6.283 * (VV - v_cuff + 0.062) / 0.078
                             + 2.0 * hash01(uid, "brk", side), 0.5)
            if kneels:
                # kneeling: the knee bags out and the shin is pulled tight
                d += 0.0088 * frontw * np.exp(-((VV - v_knee) / 0.075) ** 2)
                d -= 0.0035 * frontw * np.exp(
                    -((VV - v_knee - 0.13) / 0.075) ** 2)
            d += micro_crumple(TH, VV, uid + (3.0 if side == "r" else 5.0),
                               FOLD.MICRO_AMP, ku=12.5, kv=9.0)
            # ---- seams ---------------------------------------------------
            d += felled_seam(dtheta(TH, out_th) * RR, side=1.0)
            d += felled_seam(dtheta(TH, in_th) * RR, side=-1.0)
            d += plain_seam(VV - v_cuff)
            # knit rib: 4.4 mm pitch, 0.7 mm proud.  1.6 px wide at the
            # filmed distance, so it is geometry.
            nrib = max(int(round(2 * math.pi * RR.mean() / 0.0044)), 8)
            d += 0.00070 * sstep(v_cuff, v_cuff + 0.010, VV) \
                * crest(nrib * TH, 1.5)
            return d

        leg = sweep(lpath, Exl, Eyl, Al, Bl, Nl, N_TR, disp=leg_disp,
                    name="leg_" + side)

        # ---- the split: row 0 is the trunk's ring, then it inflates -------
        P0 = np.zeros((N_TR, 3))
        if side == "r":
            src = np.arange(0, half + 1)
            P0[src] = trunk.P[0, src]
            new = np.arange(half + 1, N_TR)
            q = (new - half) / float(half)
        else:
            src = np.concatenate([np.arange(half, N_TR), [0]])
            P0[np.arange(half, N_TR)] = trunk.P[0, np.arange(half, N_TR)]
            P0[0] = trunk.P[0, 0]
            new = np.arange(1, half)
            # left col 0 IS the trunk's front centre and col `half` its back,
            # so the inboard arc runs front -> back: q must count the other way
            q = 1.0 - new / float(half)
        # The inboard half of the crotch ring is a flattened SEMI-ELLIPSE, not
        # a straight line: a straight line has to grow into a 0.31 m semicircle
        # over 0.23 m of thigh, and the pleats that expansion makes fan across
        # the inner leg like a paper lantern.  Parameterised by the same angle
        # the leg ring uses, it inflates smoothly instead.
        pb, pf = trunk.P[0, half], trunk.P[0, 0]
        mid = 0.5 * (pb + pf)
        halfv = 0.5 * (pf - pb)
        phi = 0.5 * math.pi - 2.0 * math.pi * new / float(N_TR)
        crot = (mid[None, :] + halfv[None, :] * np.sin(phi)[:, None]
                + Ex[0][None, :] * (0.020 * np.cos(phi) + sgn * 0.0018 * H
                                    )[:, None]
                - up_p[None, :] * (0.0050 * H
                                   * (0.5 - 0.5 * np.cos(phi)))[:, None])
        P0[new] = crot
        # The start ring is SWEPT down the leg path, not held still: holding it
        # still makes the first rows coincide and the seat ends in a horizontal
        # shelf you can see from 10 m.
        travel = (lpath - lpath[0])[:, None, :]
        # ONE blend length for the whole ring.  Letting the inboard half close
        # faster than the outboard half leaves the outer cloth still extruded
        # while the inner is already round, and the difference between them is
        # a flat triangular web from the crotch to the outside of the thigh.
        fblend = sstep(0.0, 0.090 * H, vg)[:, None, None]
        leg.P = (P0[None, :, :] + travel) * (1.0 - fblend) + leg.P * fblend
        NRM_lg = piece_normals(leg.P)

        # ---- colour / wear ------------------------------------------------
        THl, VVl = leg.TH, leg.V
        col_lg = np.zeros(THl.shape + (3,))
        col_lg[:] = shell
        if chance(0.45, uid, "sidepanel"):
            sp = (np.abs(dtheta(THl, out_th)) < 0.30) * 1.0 \
                * (1 - sstep(0.955, 0.962, tg))[:, None]
            for k in range(3):
                col_lg[..., k] = col_lg[..., k] * (1 - sp) + trim[k] * sp
        cuffm = sstep(v_cuff - 0.0014, v_cuff + 0.0014, VVl)
        for k in range(3):
            col_lg[..., k] = col_lg[..., k] * (1 - cuffm) + accent_trim[k] * cuffm
        base_lg, aux_lg = paint(THl.shape, shell)
        base_lg[..., :3] = col_lg
        aux_lg[..., 0] = np.maximum.reduce([
            np.exp(-((dtheta(THl, out_th) * leg.A[:, 0:1]) / 0.006) ** 2),
            np.exp(-((dtheta(THl, in_th) * leg.A[:, 0:1]) / 0.006) ** 2),
            np.exp(-((VVl - v_cuff) / 0.006) ** 2)])
        aux_lg[..., 1] = 0.55 * cuffm
        wear_lg = np.zeros(THl.shape + (4,))
        frontw = clamp01(np.cos(dtheta(THl, 0.5 * math.pi)))
        kneew = np.exp(-((VVl - v_knee) / 0.085) ** 2) * frontw ** 1.4
        shinw = sstep(v_knee + 0.04, v_knee + 0.20, VVl) * frontw ** 1.6 \
            * (1 - sstep(vg[-1] - 0.09, vg[-1], VVl))
        hemw = sstep(vg[-1] - 0.16, vg[-1], VVl)
        wear_lg[..., 0] = np.clip(
            spec.age * 0.28 + spec.knee_dirt * 0.80 * kneew
            + spec.shin_wear * 0.85 * shinw + 0.35 * hemw * spec.age, 0, 1)
        wear_lg[..., 1] = np.clip(
            spec.dirt * (0.25 + 0.5 * hemw)
            + spec.knee_dirt * (0.55 + 0.45 * fbm2(THl * 2.2, VVl * 9.0,
                                                   seed=int(uid) % 733)) * kneew
            + spec.shin_wear * 0.45 * shinw
            + 0.35 * spec.dirt * fbm2(THl * 1.9, VVl * 6.0,
                                      seed=(int(uid) + 7) % 733), 0, 1)
        wear_lg[..., 2] = np.clip(spec.oil * 0.7 * clamp01(
            fbm2(THl * 3.1 + uid, VVl * 8.0, seed=(int(uid) + 13) % 977) * 2.0
            - 0.95) * (0.4 + 0.6 * frontw), 0, 1)
        wear_lg[..., 3] = spec.fade * (0.35 + 0.35 * frontw)

        uvl = np.stack([leg.circ, leg.V], -1)
        # Row 0's OUTBOARD half is literally the trunk's bottom ring -- shared
        # indices, not a duplicate, so there is no shading crack down the seat.
        # Its INBOARD half is new: those vertices are the crotch line.
        i0 = acc.verts(leg.P[1:].reshape(-1, 3), uv=uvl[1:].reshape(-1, 2),
                       base=base_lg[1:].reshape(-1, 4),
                       aux=aux_lg[1:].reshape(-1, 4),
                       wear=wear_lg[1:].reshape(-1, 4))
        IDX_lg = np.zeros((R_lg, N_TR), np.int64)
        IDX_lg[1:] = i0 + np.arange((R_lg - 1) * N_TR).reshape(R_lg - 1, N_TR)
        IDX_lg[0] = IDX_tr[0]
        ic = acc.verts(leg.P[0, new], uv=uvl[0, new],
                       base=base_lg[0, new], aux=aux_lg[0, new],
                       wear=wear_lg[0, new])
        IDX_lg[0, new] = ic + np.arange(len(new))
        r_cuff = int(np.searchsorted(vg, v_cuff))
        acc.grid_faces(IDX_lg[:r_cuff], MAT_SHELL, wrap_u=True, flip=False)
        acc.grid_faces(IDX_lg[r_cuff - 1:], MAT_KNIT, wrap_u=True, flip=False)
        leg_pieces[side] = (leg, NRM_lg, IDX_lg, vg, tg, v_knee, v_cuff,
                            out_th, in_th, R_lg, lpath, Exl, Eyl)

    # the crotch gusset: bridge the two legs' inboard arcs so the seat is
    # closed.  4.5 mm apart, but a hole is a hole.
    legR, legL = leg_pieces["r"], leg_pieces["l"]
    nb = 3
    qb = np.arange(half + 1, N_TR)
    ql = (N_TR - qb) % N_TR
    IR = legR[2][:nb][:, qb]
    IL = legL[2][:nb][:, ql]
    G = np.stack([IR[:, :-1], IR[:, 1:], IL[:, 1:], IL[:, :-1]], -1)
    acc.quads(G.reshape(-1, 4), MAT_SHELL, smooth=True)

    # ======================================================================
    #  SLEEVES  --  capped tubes.  The cap forms the top of the shoulder and
    #  swallows the trunk's narrowed upper section; their intersection IS the
    #  armscye, and the sleeve-head roll sits on it.
    # ======================================================================
    slv_pieces = {}
    for side, sgn in (("r", 1.0), ("l", -1.0)):
        shJ, elJ, wrJ = J["shldr_" + side], J["elbow_" + side], J["wrist_" + side]
        up_arm = _norm(shJ - elJ)
        kP = [shJ + up_arm * (0.030 * H), shJ,
              shJ + 0.5 * (elJ - shJ), elJ,
              elJ + 0.5 * (wrJ - elJ), wrJ,
              wrJ + _norm(wrJ - elJ) * (0.020 * H * spec.sleeve_len)]
        kF = [F["shldr_" + side], F["shldr_" + side], F["shldr_" + side],
              F["elbow_" + side], F["elbow_" + side], F["wrist_" + side],
              F["wrist_" + side]]
        raw = catmull(np.array(kP), 180)
        La = arclen(raw)[-1]
        R_sv = max(int(La / E_LIMB), 50)
        spath = resample(raw, R_sv)
        Ts, Exs, Eys = chain_axes(spath, kP, kF)
        vs = arclen(spath)
        push = spec.sleeve_push
        v_end = vs[-1] * (1.0 - push)
        ts = np.clip(vs / max(v_end, 1e-6), 0.0, 1.0)
        R_sv = int(np.searchsorted(vs, v_end)) + 1
        spath, Ts, Exs, Eys = spath[:R_sv], Ts[:R_sv], Exs[:R_sv], Eys[:R_sv]
        vs, ts = vs[:R_sv], ts[:R_sv]
        ag = 0.42 + 0.58 * b.arm_g
        As, Bs, Ns = sect_interp(SLV_SECT, ts, H, ag, ag)
        if push > 0.0:
            # a pushed sleeve is not a shorter sleeve: the same cloth is still
            # there, stacked into a bunched torus above the elbow.
            As = As * (1.0 + 0.30 * sstep(0.80, 1.0, ts))
            Bs = Bs * (1.0 + 0.30 * sstep(0.80, 1.0, ts))
        v_elb = float(vs[int(np.argmin(np.linalg.norm(spath - elJ, axis=1)))])
        v_cuf = vs[-1] - (0.030 if push > 0 else 0.058)
        elb_fx = math.radians(abs(spec.pose.j.get("elbow_" + side,
                                                  (0, 0, 0))[0]))
        nfl = rint(3, 4, uid, "sf", side)
        # the sleeve's own seam runs down the back of the arm (theta = -pi/2)
        seam_th = -0.5 * math.pi
        N_SV = int(round(max(As.max() * 2 * math.pi, 0.3) / E_LIMB / 2.0)) * 2
        N_SV = max(N_SV, 64)

        def slv_disp(TH, VV, RR, v_elb=v_elb, elb_fx=elb_fx, nfl=nfl,
                     v_cuf=v_cuf, vend=vs[-1], side=side, push=push):
            frontw = clamp01(np.cos(dtheta(TH, 0.5 * math.pi))) ** 1.5
            d = np.zeros_like(TH)
            d += flex_folds(VV, v_elb, elb_fx, frontw, uid + 13.0)
            d += set_crease(VV, v_elb, elb_fx, frontw, 1.0)
            d += hang_flutes(TH, VV, 0.055, v_cuf, nfl, FOLD.HANG_AMP * 0.90,
                             uid + (17.0 if side == "r" else 19.0))
            # the sleeve head is EASED into the armscye: a rolled ridge
            d += 0.0021 * np.exp(-((VV - 0.030) / 0.020) ** 2)
            d -= 0.0090 * np.exp(-((VV - vend) / 0.040) ** 2)
            d += 0.0040 * np.exp(-((VV - v_cuf + 0.020) / 0.026) ** 2) \
                * crest(6.0 * TH + 4.0 * hash01(uid, "sg", side), 0.85)
            if push > 0.0:
                # 3-4 hard rings of stacked cloth
                # 3-4 rings of stacked cloth, wandering: a pushed sleeve
                # never stacks in perfect parallel bands
                wob = 0.011 * (fbm1(TH * 1.9 + uid, seed=17) - 0.5)
                d += 0.0068 * sstep(0.74, 0.97, VV / max(vend, 1e-6)) \
                    * crest(6.283 * (VV - vend + wob) / 0.047
                            + 1.7 * hash01(uid, "pu"), 0.45)
            d += micro_crumple(TH, VV, uid + (23.0 if side == "r" else 29.0),
                               FOLD.MICRO_AMP * 0.92, ku=10.5, kv=10.0)
            d += felled_seam(dtheta(TH, seam_th) * RR, side=1.0)
            d += plain_seam(VV - v_cuf)
            nrib = max(int(round(2 * math.pi * RR.mean() / 0.0044)), 8)
            d += 0.00070 * sstep(v_cuf, v_cuf + 0.010, VV) \
                * crest(nrib * TH, 1.5)
            return d

        slv = sweep(spath, Exs, Eys, As, Bs, Ns, N_SV, disp=slv_disp,
                    name="slv_" + side)
        NRM_sv = piece_normals(slv.P)
        THs, VVs = slv.TH, slv.V
        col_sv = np.zeros(THs.shape + (3,))
        col_sv[:] = shell
        # contrast upper sleeve, tied to the yoke
        ys = (1.0 - sstep(0.178, 0.184, ts)) * 1.0
        for k in range(3):
            col_sv[..., k] = col_sv[..., k] * (1 - ys[:, None]) \
                + accent_trim[k] * ys[:, None]
        if chance(0.52, uid, "slvband"):
            bd = ((np.abs(ts - 0.36) < 0.030) * 1.0)[:, None]
            for k in range(3):
                col_sv[..., k] = col_sv[..., k] * (1 - bd) + trim[k] * bd
        cuffm = sstep(v_cuf - 0.0014, v_cuf + 0.0014, VVs)
        for k in range(3):
            col_sv[..., k] = col_sv[..., k] * (1 - cuffm) + accent_trim[k] * cuffm
        base_sv, aux_sv = paint(THs.shape, shell)
        base_sv[..., :3] = col_sv
        aux_sv[..., 0] = np.maximum(
            np.exp(-((dtheta(THs, seam_th) * slv.A[:, 0:1]) / 0.006) ** 2),
            np.exp(-((VVs - v_cuf) / 0.006) ** 2))
        aux_sv[..., 1] = 0.55 * cuffm
        wear_sv = np.zeros(THs.shape + (4,))
        fw = clamp01(np.cos(dtheta(THs, 0.5 * math.pi)))
        elbw = np.exp(-((VVs - v_elb) / 0.075) ** 2) * (1 - 0.5 * fw)
        cufw = sstep(v_cuf - 0.10, vs[-1], VVs)
        wear_sv[..., 0] = np.clip(spec.age * (0.30 + 0.75 * elbw + 0.55 * cufw),
                                  0, 1)
        wear_sv[..., 1] = np.clip(
            spec.dirt * (0.22 + 0.75 * cufw)
            + 0.4 * spec.dirt * fbm2(THs * 2.0, VVs * 8.0,
                                     seed=(int(uid) + 41) % 733), 0, 1)
        wear_sv[..., 2] = np.clip(spec.oil * 0.8 * cufw * clamp01(
            fbm2(THs * 3.4 + uid, VVs * 9.0,
                 seed=(int(uid) + 53) % 977) * 2.1 - 1.0), 0, 1)
        wear_sv[..., 3] = (spec.fade * (0.30 + 0.65
                                * (1 - sstep(0.05, 0.40, ts))))[:, None]

        uvs = np.stack([slv.circ, slv.V], -1)
        i0 = acc.verts(slv.P.reshape(-1, 3), uv=uvs.reshape(-1, 2),
                       base=base_sv.reshape(-1, 4), aux=aux_sv.reshape(-1, 4),
                       wear=wear_sv.reshape(-1, 4))
        IDX_sv = i0 + np.arange(R_sv * N_SV).reshape(R_sv, N_SV)
        r_cf = int(np.searchsorted(vs, v_cuf))
        acc.grid_faces(IDX_sv[:r_cf], MAT_SHELL, wrap_u=True, flip=False)
        acc.grid_faces(IDX_sv[r_cf - 1:], MAT_KNIT, wrap_u=True, flip=False)

        # ---- the sleeve cap: a flattened dome that IS the shoulder --------
        K = 7
        capu = -Ts[0]
        cap_h = 0.0215 * H
        rings = []
        for k in range(1, K + 1):
            a = (k / float(K)) * 0.5 * math.pi
            s_ = math.cos(a) ** 0.50
            hgt = cap_h * math.sin(a) ** 0.92
            th = slv.TH[0]
            x, y = superellipse(th, As[0] * s_, Bs[0] * s_, Ns[0])
            cr = (spath[0][None, :] + Exs[0][None, :] * x[:, None]
                  + Eys[0][None, :] * y[:, None] + capu[None, :] * hgt)
            cr = cr + capu[None, :] * (micro_crumple(
                th, np.full_like(th, 0.02 + 0.01 * k), uid + 33.0,
                FOLD.MICRO_AMP * 0.8)[:, None])
            rings.append(cr)
        pole = spath[0] + capu * (cap_h * 1.02)
        capP = np.concatenate(rings[:-1], 0)
        bcap = np.tile(base_sv[0:1].repeat(K - 1, 0).reshape(-1, 4)[:1],
                       (len(capP), 1))
        bcap[:, :3] = np.tile(col_sv[0], (K - 1, 1))
        acap = np.zeros((len(capP), 4)); acap[:, 3] = (uid * 0.618) % 1.0
        wcap = np.tile(wear_sv[0:1, 0:1].reshape(1, 4), (len(capP), 1))
        wcap[:, 3] = min(spec.fade * 1.15, 1.0)     # the shoulders see the sun
        ic = acc.verts(capP, uv=np.tile([[0.0, 0.0]], (len(capP), 1)),
                       base=bcap, aux=acap, wear=wcap)
        CI = ic + np.arange((K - 1) * N_SV).reshape(K - 1, N_SV)
        allc = np.concatenate([IDX_sv[0:1], CI], 0)
        acc.grid_faces(allc, MAT_SHELL, wrap_u=True, flip=True)
        ip = acc.verts(pole[None, :], uv=[[0.0, 0.0]], base=bcap[:1],
                       aux=acap[:1], wear=wcap[:1])
        jj = np.arange(N_SV)
        acc.tris(np.stack([CI[-1][jj], np.full(N_SV, ip),
                           CI[-1][(jj + 1) % N_SV]], -1), MAT_SHELL, True)
        slv_pieces[side] = (slv, NRM_sv, IDX_sv, vs, ts, v_elb, v_cuf,
                            seam_th, R_sv, N_SV, spath, Exs, Eys, capu)

    # ======================================================================
    #  DETAILS
    # ======================================================================
    def band_around(pc, NRM, r0, r1, prof, mat, col, aux4, wear4, nrow=9,
                    gather=None, cols=None, wrap=True):
        """A raised band lying on a piece (belt, collar stand, cuff tab)."""
        cc = np.arange(pc.N, dtype=float) if cols is None else np.asarray(cols,
                                                                          float)
        tt = np.linspace(0.0, 1.0, nrow)
        RR = (r0 + (r1 - r0) * tt)[:, None].repeat(len(cc), 1)
        CC = cc[None, :].repeat(nrow, 0)
        P = bilerp(pc.P, RR, CC, wrap)
        Nn = _norm(bilerp(NRM, RR, CC, wrap))
        lift = prof(tt)[:, None]
        if gather is not None:
            lift = lift + gather(tt[:, None], CC)
        P = P + Nn * lift[..., None]
        uvb = np.stack([bilerp(pc.circ[..., None], RR, CC, wrap)[..., 0],
                        bilerp(pc.V[..., None], RR, CC, wrap)[..., 0]], -1)
        bb = np.zeros(P.shape[:2] + (4,)); bb[..., :3] = col; bb[..., 3] = dl
        i0 = acc.verts(P.reshape(-1, 3), uv=uvb.reshape(-1, 2),
                       base=bb.reshape(-1, 4), aux=aux4, wear=wear4)
        I = i0 + np.arange(P.shape[0] * P.shape[1]).reshape(P.shape[:2])
        acc.grid_faces(I, mat, wrap_u=wrap, flip=False)
        return I, P, Nn

    def two_row_stitch(P, Nn, Tn, gap=0.0058, col=None, uid_=0.0):
        cth = np.asarray(col if col is not None else T.stitch, float)
        Bt = _norm(np.cross(Tn, Nn))
        for k, s in ((0, -0.5), (1, 0.5)):
            stitch_run(acc, P + Bt * (s * gap), Nn, Tn,
                       base=(cth[0], cth[1], cth[2], 0.0), uid=uid_ + k)

    # ---- placket + zip ----------------------------------------------------
    r_top = R_tr - 3
    r_bot = int(np.searchsorted(v_all, v_waist - 0.10))
    ncp = int(round(plack_w * 2 / max(trunk.circ[0, 1], 1e-4)))
    ncp = max(ncp, 5)
    pl_rows = np.arange(r_bot, r_top, dtype=float)
    pl_cols = np.linspace(-ncp * 0.5, ncp * 0.5, ncp + 1)
    PR = pl_rows[:, None].repeat(len(pl_cols), 1)
    PC = pl_cols[None, :].repeat(len(pl_rows), 0)
    Pp = bilerp(trunk.P, PR, PC)
    Np = _norm(bilerp(NRM_tr, PR, PC))
    e = clamp01(1.0 - np.abs(pl_cols) / (ncp * 0.5))
    liftp = 0.0016 * sstep(0.0, 0.28, e) + 0.0007
    Pp = Pp + Np * liftp[None, :, None]
    bb = np.zeros(Pp.shape[:2] + (4,)); bb[..., :3] = shell; bb[..., 3] = dl
    aa = np.zeros(Pp.shape[:2] + (4,)); aa[..., 0] = 0.8; aa[..., 3] = (uid * .618) % 1
    ww = np.zeros(Pp.shape[:2] + (4,))
    ww[..., 0] = spec.age * 0.55; ww[..., 1] = spec.dirt * 0.35
    ww[..., 3] = spec.fade * 0.5
    ip = acc.verts(Pp.reshape(-1, 3),
                   uv=np.stack([PC * 0.004, PR * 0.004], -1).reshape(-1, 2),
                   base=bb.reshape(-1, 4), aux=aa.reshape(-1, 4),
                   wear=ww.reshape(-1, 4))
    IP = ip + np.arange(Pp.shape[0] * Pp.shape[1]).reshape(Pp.shape[:2])
    acc.grid_faces(IP, MAT_SHELL, wrap_u=False, flip=False)
    for s in (-1.0, 1.0):
        Pc, Nc, Tc = seam_curve(trunk, NRM_tr, s * ncp * 0.5, r_bot, r_top)
        two_row_stitch(Pc + Nc * 0.0018, Nc, Tc, 0.0042, uid_=uid + 60 + s)

    # the zip itself: two rows of teeth and a slider.  3.1 mm pitch teeth are
    # 1.2 px each -- individually sub-pixel, collectively a hard specular line,
    # which is exactly what a zip does at 10 m.
    zr = np.arange(r_bot + 2, min(r_top, R_tr - 4), dtype=float)
    for s in (-1.0, 1.0):
        zc = np.full_like(zr, s * 1.25)
        Pz = bilerp(trunk.P, zr, zc); Nz = _norm(bilerp(NRM_tr, zr, zc))
        Tz = _norm(np.gradient(Pz, axis=0))
        stitch_run(acc, Pz + Nz * 0.0020, Nz, Tz, pitch=0.0031, duty=0.62,
                   w=0.0026, h=0.00085, mat=MAT_HW,
                   base=(0.42, 0.40, 0.36, 0.0), aux=(0.0, 1.0, 0.0, 0.0),
                   wear=(spec.age * 0.7, 0, 0, 0), uid=uid + 71 + s)
    sl_r = float(min(r_top - 1, R_tr - 5)) * (1.0 - spec.zip_open) \
        + r_bot * spec.zip_open
    Ps = bilerp(trunk.P, np.array([sl_r]), np.array([0.0]))[0]
    Ns = _norm(bilerp(NRM_tr, np.array([sl_r]), np.array([0.0])))[0]
    Tz = _norm(bilerp(trunk.P, np.array([sl_r + 3]), np.array([0.0]))[0] - Ps)
    Bz = _norm(np.cross(Tz, Ns))
    sld = []
    for (du, dv, dw) in [(-0.007, -0.014, 0.0022), (0.007, -0.014, 0.0022),
                         (0.007, 0.012, 0.0022), (-0.007, 0.012, 0.0022),
                         (-0.0055, -0.012, 0.0060), (0.0055, -0.012, 0.0060),
                         (0.0055, 0.010, 0.0060), (-0.0055, 0.010, 0.0060)]:
        sld.append(Ps + Bz * du + Tz * dv + Ns * dw)
    isl = acc.verts(np.array(sld), uv=np.zeros((8, 2)),
                    base=(0.40, 0.38, 0.35, 0.0), aux=(0, 1, 0, 0),
                    wear=(spec.age, 0, 0, 0))
    acc.quads(isl + np.array([[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1],
                              [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]),
              MAT_HW, smooth=False)
    # the puller tab
    pt = []
    for (du, dv, dw) in [(-0.0045, 0.011, 0.0062), (0.0045, 0.011, 0.0062),
                         (0.0045, 0.038, 0.0050), (-0.0045, 0.038, 0.0050)]:
        pt.append(Ps + Bz * du + Tz * dv + Ns * dw)
    ipt = acc.verts(np.array(pt), uv=np.zeros((4, 2)),
                    base=(0.36, 0.34, 0.32, 0.0), aux=(0, 1, 0, 0),
                    wear=(spec.age, 0, 0, 0))
    acc.quads(np.array([[ipt, ipt + 1, ipt + 2, ipt + 3]]), MAT_HW, False)

    # ---- the belt ---------------------------------------------------------
    r_belt = float(np.searchsorted(v_all, v_belt))
    bw = 0.021
    rb0 = r_belt - bw / max(np.diff(v_all).mean(), 1e-6)
    rb1 = r_belt + bw / max(np.diff(v_all).mean(), 1e-6)

    def belt_prof(t):
        return 0.0031 * (0.25 + 0.75 * sstep(0.0, 0.20, t)
                         * (1.0 - sstep(0.80, 1.0, t)))

    def belt_gather(t, cc):
        backness = clamp01(np.cos(dtheta(2 * math.pi * cc / N_TR - 0.5 * math.pi,
                                         -0.5 * math.pi)))
        return (0.0022 * spec.belt_cinch * backness ** 2
                * crest(2 * math.pi * cc / 9.0 + 3.0 * hash01(uid, "bl"), 1.1)
                * np.sin(math.pi * t))

    aux_b = np.zeros(4); aux_b[1] = 0.35; aux_b[3] = (uid * 0.618) % 1
    wr_b = np.array([spec.age * 0.7, spec.dirt * 0.55, spec.oil * 0.3,
                     spec.fade * 0.6])
    I_belt, P_belt, N_belt = band_around(
        trunk, NRM_tr, rb0, rb1, belt_prof, MAT_SHELL, accent_soft,
        tuple(aux_b), tuple(wr_b), nrow=11, gather=belt_gather)
    # buckle at the front
    kbuck = []
    Pb = bilerp(trunk.P, np.array([r_belt]), np.array([0.0]))[0]
    Nb = _norm(bilerp(NRM_tr, np.array([r_belt]), np.array([0.0])))[0]
    Tb = _norm(bilerp(trunk.P, np.array([r_belt + 3]), np.array([0.0]))[0] - Pb)
    Bb = _norm(np.cross(Tb, Nb))
    for (du, dv, dw) in [(-0.026, -0.020, 0.004), (0.026, -0.020, 0.004),
                         (0.026, 0.020, 0.004), (-0.026, 0.020, 0.004),
                         (-0.026, -0.020, 0.0085), (0.026, -0.020, 0.0085),
                         (0.026, 0.020, 0.0085), (-0.026, 0.020, 0.0085)]:
        kbuck.append(Pb + Bb * du + Tb * dv + Nb * dw)
    ib = acc.verts(np.array(kbuck), uv=np.zeros((8, 2)),
                   base=(0.34, 0.32, 0.29, 0.0), aux=(0, 1, 0, 0),
                   wear=(spec.age, spec.dirt * 0.5, 0, 0))
    acc.quads(ib + np.array([[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1],
                             [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]),
              MAT_HW, smooth=False)

    # ---- the collar -------------------------------------------------------
    neck_up = F["neck"] @ np.array([0.0, 0.0, 1.0])
    ctr_top = path[-1]
    if spec.collar_up:
        prof_c = [(0.000, 1.000), (0.010, 1.030), (0.021, 1.058),
                  (0.032, 1.082), (0.041, 1.102), (0.047, 1.115),
                  (0.0495, 1.118), (0.0475, 1.086), (0.0405, 1.070),
                  (0.031, 1.055)]
    else:
        prof_c = [(0.000, 1.000), (0.010, 1.022), (0.020, 1.052),
                  (0.029, 1.092), (0.034, 1.145), (0.034, 1.238),
                  (0.026, 1.272), (0.015, 1.322), (0.002, 1.352),
                  (-0.014, 1.360), (-0.028, 1.336)]
    radial = trunk.P[-1] - ctr_top[None, :]
    radial = radial - neck_up[None, :] * (radial @ neck_up)[:, None]
    Cp = np.stack([ctr_top[None, :] + radial * sc + neck_up[None, :] * dz
                   for (dz, sc) in prof_c], 0)
    jj = np.arange(N_TR)
    wob = 0.0016 * crest(5.0 * 2 * math.pi * jj / N_TR
                         + 6.0 * hash01(uid, "cw"), 1.0)
    Cp = Cp + (radial / np.maximum(np.linalg.norm(radial, axis=1,
                                                  keepdims=True), 1e-9))[None] \
        * (wob[None, :, None] * np.linspace(0, 1, len(prof_c))[:, None, None])
    bbc = np.zeros(Cp.shape[:2] + (4,)); bbc[..., :3] = accent_trim
    bbc[..., 3] = dl
    aac = np.zeros(Cp.shape[:2] + (4,)); aac[..., 3] = (uid * 0.618) % 1
    wwc = np.zeros(Cp.shape[:2] + (4,))
    wwc[..., 0] = spec.age * 0.85
    wwc[..., 1] = spec.dirt * 0.55
    wwc[..., 3] = spec.fade * 0.9
    uvc = np.stack([np.tile(trunk.circ[-1], (len(prof_c), 1)),
                    np.tile(np.array([d for d, _ in prof_c])[:, None],
                            (1, N_TR))], -1)
    icv = acc.verts(Cp.reshape(-1, 3), uv=uvc.reshape(-1, 2),
                    base=bbc.reshape(-1, 4), aux=aac.reshape(-1, 4),
                    wear=wwc.reshape(-1, 4))
    IC = icv + np.arange(Cp.shape[0] * N_TR).reshape(Cp.shape[0], N_TR)
    acc.grid_faces(np.concatenate([IDX_tr[-1:], IC], 0), MAT_SHELL,
                   wrap_u=True, flip=True)
    LM["collar_mouth"] = Frame(Cp[-1].mean(0), Ex[-1], neck_up,
                               np.cross(Ex[-1], neck_up),
                               float(np.linalg.norm(radial, axis=1).mean()),
                               "collar_mouth")

    # ---- pockets, panels, patches ----------------------------------------
    rpm = 1.0 / max(float(np.diff(v_all).mean()), 1e-6)          # rows per m
    cpm_tr = 1.0 / max(float(trunk.circ[0, 1] - trunk.circ[0, 0]), 1e-6)
    r_chest = float(np.searchsorted(v_all, v_chest))
    emb_aux = (0.0, 0.9, 0.0, (uid * 0.618) % 1.0)
    emb_wear = (spec.age * 0.6, spec.dirt * 0.4, 0.0, spec.fade * 0.8)

    if spec.chest_pocket:
        for sgn2, w_, h_ in ((-1.0, 0.052, 0.060),):
            cc0 = sgn2 * 15.0
            patch_on(acc, trunk, NRM_tr, r_chest - 1.0, cc0,
                     h_ * rpm, w_ * cpm_tr, 0.0021, MAT_SHELL,
                     (shell[0], shell[1], shell[2], dl),
                     (0.55, 0.0, 0.0, (uid * .618) % 1),
                     (spec.age * .7, spec.dirt * .5, spec.oil * .4,
                      spec.fade * .7), rad=0.22, bead=0.0009,
                     bead_col=(T.stitch[0], T.stitch[1], T.stitch[2], 0.0),
                     uid=uid)
            # the flap, standing slightly away from the pocket mouth
            patch_on(acc, trunk, NRM_tr, r_chest - 1.0 + h_ * rpm * 0.92, cc0,
                     0.020 * rpm, w_ * cpm_tr * 1.05, 0.0038, MAT_SHELL,
                     (shell[0] * .96, shell[1] * .96, shell[2] * .96, dl),
                     (0.55, 0.0, 0.0, (uid * .618) % 1),
                     (spec.age * .8, spec.dirt * .5, 0.0, spec.fade * .8),
                     rad=0.30, bead=0.0008,
                     bead_col=(T.stitch[0], T.stitch[1], T.stitch[2], 0.0))

    _, cp_o, cp_n = patch_on(
        acc, trunk, NRM_tr, r_chest + 2.0, 15.0,
        0.026 * rpm, 0.036 * cpm_tr, 0.0013, MAT_EMB,
        (accent[0], accent[1], accent[2], 0.0), emb_aux, emb_wear,
        rad=0.34, bead=0.0011,
        bead_col=(trim[0], trim[1], trim[2], 0.0), uid=uid)
    LM["chest_patch"] = Frame(cp_o, Ex[-1], cp_n, np.cross(Ex[-1], cp_n),
                              0.036, "chest_patch")

    r_yoke = float(np.searchsorted(v_all, v_yoke))
    _, bp_o, bp_n = patch_on(
        acc, trunk, NRM_tr, r_yoke - 5.0, float(half),
        0.020 * rpm, 0.082 * cpm_tr, 0.0012, MAT_EMB,
        (trim[0], trim[1], trim[2], 0.0), emb_aux, emb_wear, rad=0.20,
        bead=0.0010, bead_col=(accent[0], accent[1], accent[2], 0.0), uid=uid)
    LM["back_panel"] = Frame(bp_o, Ex[-1], bp_n, np.cross(Ex[-1], bp_n),
                             0.082, "back_panel")

    # sleeve brand patches + epaulettes
    for side in ("r", "l"):
        slv, NRM_sv, IDX_sv, vs, ts, v_elb, v_cuf, seam_th, R_sv, N_SV, \
            spath, Exs, Eys, capu = slv_pieces[side]
        cpm_s = 1.0 / max(float(slv.circ[0, 1] - slv.circ[0, 0]), 1e-6)
        rpm_s = 1.0 / max(float(np.diff(vs).mean()), 1e-6)
        r_up = float(np.searchsorted(vs, vs[-1] * 0.22))
        out_c = N_SV * 0.25 if side == "r" else N_SV * 0.75
        patch_on(acc, slv, NRM_sv, r_up, out_c, 0.021 * rpm_s,
                 0.030 * cpm_s, 0.0012, MAT_EMB,
                 (trim[0], trim[1], trim[2], 0.0), emb_aux, emb_wear,
                 rad=0.30, bead=0.0010,
                 bead_col=(accent[0], accent[1], accent[2], 0.0), uid=uid + 5)
        if spec.epaulette:
            patch_on(acc, slv, NRM_sv, 3.0, out_c, 0.030 * rpm_s,
                     0.014 * cpm_s, 0.0026, MAT_SHELL,
                     (accent[0], accent[1], accent[2], dl),
                     (0.5, 0.0, 0.0, (uid * .618) % 1),
                     (spec.age * .8, spec.dirt * .4, 0.0, spec.fade), rad=0.35,
                     bead=0.0008,
                     bead_col=(T.stitch[0], T.stitch[1], T.stitch[2], 0.0))
        # seam stitching down the back of the sleeve, and round the cuff
        Pc, Nc, Tc = seam_curve(slv, NRM_sv, N_SV * 0.75 if side == "r"
                                else N_SV * 0.75, 2, R_sv - 2)
        two_row_stitch(Pc, Nc, Tc, uid_=uid + 80 + (0 if side == "r" else 1))
        rc_ = float(np.searchsorted(vs, v_cuf))
        Pr, Nr, Tr = ring_curve(slv, NRM_sv, rc_)
        Pr = np.vstack([Pr, Pr[:1]]); Nr = np.vstack([Nr, Nr[:1]])
        Tr = np.vstack([Tr, Tr[:1]])
        two_row_stitch(Pr, Nr, Tr, 0.0050,
                       uid_=uid + 90 + (0 if side == "r" else 1))
        # cuff mouth: roll the knit under so the opening has real thickness
        endr = slv.P[-1]
        cen = spath[-1]
        rad2 = endr - cen[None, :]
        Tend = _norm(spath[-1] - spath[max(len(spath) - 9, 0)])
        rad2 = rad2 - Tend[None, :] * (rad2 @ Tend)[:, None]
        rn = np.maximum(np.linalg.norm(rad2, axis=1, keepdims=True), 1e-9)
        roll = []
        for (dz, sc) in [(0.0, 1.0), (0.0028, 0.985), (0.0042, 0.955),
                         (0.0036, 0.925), (0.0010, 0.912)]:
            roll.append(cen[None, :] + rad2 * sc + Tend[None, :] * dz)
        RP = np.stack(roll, 0)
        bbr = np.zeros(RP.shape[:2] + (4,)); bbr[..., :3] = accent_trim
        aar = np.zeros(RP.shape[:2] + (4,)); aar[..., 1] = 0.6
        wwr = np.zeros(RP.shape[:2] + (4,))
        wwr[..., 0] = min(spec.age * 1.2, 1.0); wwr[..., 1] = spec.dirt
        irv = acc.verts(RP.reshape(-1, 3), uv=np.zeros((RP[..., 0].size, 2)),
                        base=bbr.reshape(-1, 4), aux=aar.reshape(-1, 4),
                        wear=wwr.reshape(-1, 4))
        IR2 = irv + np.arange(RP.shape[0] * N_SV).reshape(RP.shape[0], N_SV)
        acc.grid_faces(np.concatenate([IDX_sv[-1:], IR2], 0), MAT_KNIT,
                       wrap_u=True, flip=False)
        LM["cuff_wrist_" + side] = Frame(
            RP[-1].mean(0), Exs[-1], Tend, np.cross(Exs[-1], Tend),
            float(rn.mean()) * 0.92, "cuff_wrist_" + side)
        LM["shoulder_" + side] = Frame(
            spath[0] + capu * (0.0215 * H), Exs[0], capu,
            np.cross(Exs[0], capu), 0.055 * H, "shoulder_" + side)

    # ---- leg details: knee panel, cuff roll, seam stitching ---------------
    for side in ("r", "l"):
        leg, NRM_lg, IDX_lg, vg, tg, v_knee, v_cuff, out_th, in_th, R_lg, \
            lpath, Exl, Eyl = leg_pieces[side]
        cpm_l = 1.0 / max(float(leg.circ[0, 1] - leg.circ[0, 0]), 1e-6)
        rpm_l = 1.0 / max(float(np.diff(vg).mean()), 1e-6)
        r_knee = float(np.searchsorted(vg, v_knee))
        _, kn_o, kn_n = patch_on(
            acc, leg, NRM_lg, r_knee + 1.0, 0.0, 0.105 * rpm_l,
            0.062 * cpm_l, 0.0022, MAT_SHELL,
            (shell[0] * 0.97, shell[1] * 0.97, shell[2] * 0.97, dl + 0.25),
            (0.5, 0.0, 0.0, (uid * .618) % 1),
            (min(spec.age * 0.6 + spec.knee_dirt * 0.7, 1.0),
             spec.knee_dirt, spec.oil * 0.5, spec.fade * 0.6),
            rad=0.26, bead=0.0010,
            bead_col=(T.stitch[0], T.stitch[1], T.stitch[2], 0.0), uid=uid + 9)
        LM["knee_" + side] = Frame(kn_o, Exl[int(r_knee)], kn_n,
                                   np.cross(Exl[int(r_knee)], kn_n), 0.062,
                                   "knee_" + side)
        if spec.thigh_pocket:
            patch_on(acc, leg, NRM_lg, r_knee - 0.22 * rpm_l,
                     (1.0 if side == "r" else -1.0) * 0.055 * cpm_l,
                     0.062 * rpm_l, 0.048 * cpm_l, 0.0024, MAT_SHELL,
                     (shell[0], shell[1], shell[2], dl),
                     (0.55, 0.0, 0.0, (uid * .618) % 1),
                     (spec.age * .7, spec.dirt * .6, spec.oil * .5,
                      spec.fade * .6), rad=0.24, bead=0.0009,
                     bead_col=(T.stitch[0], T.stitch[1], T.stitch[2], 0.0))
        for th_, sgn3 in ((out_th, 1.0), (in_th, -1.0)):
            colj = (0.5 * math.pi - th_) / (2 * math.pi) * N_TR
            Pc, Nc, Tc = seam_curve(leg, NRM_lg, colj % N_TR, 3, R_lg - 2)
            two_row_stitch(Pc, Nc, Tc,
                           uid_=uid + 100 + sgn3 + (0 if side == "r" else 4))
        rc_ = float(np.searchsorted(vg, v_cuff))
        Pr, Nr, Tr = ring_curve(leg, NRM_lg, rc_)
        Pr = np.vstack([Pr, Pr[:1]]); Nr = np.vstack([Nr, Nr[:1]])
        Tr = np.vstack([Tr, Tr[:1]])
        two_row_stitch(Pr, Nr, Tr, 0.0050,
                       uid_=uid + 110 + (0 if side == "r" else 1))
        # rolled hem at the leg mouth
        cen = lpath[-1]
        Tend = _norm(lpath[-1] - lpath[max(len(lpath) - 9, 0)])
        rad2 = leg.P[-1] - cen[None, :]
        rad2 = rad2 - Tend[None, :] * (rad2 @ Tend)[:, None]
        rolls = ([(0.0, 1.0), (0.004, 0.99), (0.008, 0.965), (0.010, 0.930),
                  (0.007, 0.905), (0.001, 0.900)] if spec.hem_roll
                 else [(0.0, 1.0), (0.0032, 0.975), (0.0046, 0.945),
                       (0.0036, 0.920), (0.0008, 0.910)])
        RP = np.stack([cen[None, :] + rad2 * sc + Tend[None, :] * dz
                       for (dz, sc) in rolls], 0)
        bbr = np.zeros(RP.shape[:2] + (4,)); bbr[..., :3] = accent_trim
        aar = np.zeros(RP.shape[:2] + (4,)); aar[..., 1] = 0.6
        wwr = np.zeros(RP.shape[:2] + (4,))
        wwr[..., 0] = min(spec.age * 1.3, 1.0)
        wwr[..., 1] = min(spec.dirt * 1.4, 1.0)
        irv = acc.verts(RP.reshape(-1, 3), uv=np.zeros((RP[..., 0].size, 2)),
                        base=bbr.reshape(-1, 4), aux=aar.reshape(-1, 4),
                        wear=wwr.reshape(-1, 4))
        IR2 = irv + np.arange(RP.shape[0] * N_TR).reshape(RP.shape[0], N_TR)
        acc.grid_faces(np.concatenate([IDX_lg[-1:], IR2], 0), MAT_KNIT,
                       wrap_u=True, flip=False)
        rn = float(np.linalg.norm(rad2, axis=1).mean())
        LM["cuff_ankle_" + side] = Frame(RP[-1].mean(0), Exl[-1], Tend,
                                         np.cross(Exl[-1], Tend), rn * 0.92,
                                         "cuff_ankle_" + side)

    # ---- trunk seam stitching --------------------------------------------
    r_arm = float(np.searchsorted(v_all, v_arm))
    for colj in (N_TR * 0.25, N_TR * 0.75):
        Pc, Nc, Tc = seam_curve(trunk, NRM_tr, colj, 2, int(r_arm))
        two_row_stitch(Pc, Nc, Tc, uid_=uid + 120 + colj)
    for rr, c0, c1 in ((r_yoke, int(N_TR * 0.18), int(N_TR * 0.82)),):
        Pr, Nr, Tr = ring_curve(trunk, NRM_tr, rr, c0, c1)
        if c1 - c0 == N_TR:
            Pr = np.vstack([Pr, Pr[:1]]); Nr = np.vstack([Nr, Nr[:1]])
            Tr = np.vstack([Tr, Tr[:1]])
        two_row_stitch(Pr, Nr, Tr, 0.0050, uid_=uid + 130 + rr)
    # collar edge
    Pe = np.vstack([Cp[-1], Cp[-1][:1]])
    Ne = _norm(Pe - np.vstack([Cp[-3], Cp[-3][:1]]))
    Te = _norm(np.gradient(Pe, axis=0))
    two_row_stitch(Pe - Ne * 0.0016, _norm(np.cross(Te, Ne)), Te, 0.0038,
                   uid_=uid + 140)

    # ---- the name tape and the crew number on the back yoke ---------------
    try:
        import build_dressing as _D
        txt = _D.text_poly(spec.name_tape.split()[1], 0.11)
    except Exception:
        txt = None
    if txt is not None and len(txt[0]):
        TV, TF, TW = txt
        caph = 0.028
        sc = caph
        wm = TW * sc
        gr = -TV[:, 1] * sc * rpm            # text y is up -> rows
        gc = -(TV[:, 0] * sc - wm * 0.5) * cpm_tr
        rr = r_yoke - 5.0 + gr
        cc = float(half) + gc
        Pt2 = bilerp(trunk.P, rr, cc)
        Nt2 = _norm(bilerp(NRM_tr, rr, cc))
        Pt2 = Pt2 + Nt2 * 0.0011
        it = acc.verts(Pt2, uv=np.stack([TV[:, 0] * sc, TV[:, 1] * sc], -1),
                       base=(accent[0], accent[1], accent[2], 0.0),
                       aux=emb_aux, wear=emb_wear)
        acc.tris(it + TF, MAT_EMB, smooth=True)

    # ======================================================================
    #  LANDMARKS the 18 dependants attach to
    # ======================================================================
    up_w = np.array([0.0, 0.0, 1.0])
    fwd = _norm(F["spine3"] @ np.array([0.0, 1.0, 0.0]))
    LM["head"] = Frame(J["head"] + F["head"] @ np.array([0, 0.006 * H,
                                                         0.035 * H]),
                       F["head"] @ np.array([1.0, 0, 0]),
                       F["head"] @ np.array([0, 1.0, 0]),
                       F["head"] @ np.array([0, 0, 1.0]), 0.098, "head")
    for s2, g in (("r", 1.0), ("l", -1.0)):
        LM["ear_" + s2] = Frame(
            J["head"] + F["head"] @ np.array([g * 0.078, -0.004 * H,
                                              0.024 * H]),
            F["head"] @ np.array([g, 0, 0]), F["head"] @ np.array([0, 1.0, 0]),
            F["head"] @ np.array([0, 0, 1.0]), 0.042, "ear_" + s2)
        LM["grip_" + s2] = Frame(
            J["hand_" + s2] + F["hand_" + s2] @ np.array([0, 0.012 * H,
                                                          -0.020 * H]),
            F["hand_" + s2] @ np.array([g, 0, 0]),
            F["hand_" + s2] @ np.array([0, 1.0, 0]),
            F["hand_" + s2] @ np.array([0, 0, 1.0]), 0.045, "grip_" + s2)
        LM["sole_" + s2] = Frame(
            np.array([J["ankle_" + s2][0], J["ankle_" + s2][1],
                      skel.sole_z[s2]]),
            np.array([1.0, 0, 0]), fwd, up_w, 0.055, "sole_" + s2)
    rb = float(np.searchsorted(v_all, v_belt))
    for nm2, cj in (("belt_back", float(half)), ("belt_r", N_TR * 0.25),
                    ("belt_l", N_TR * 0.75)):
        o = bilerp(trunk.P, np.array([rb]), np.array([cj]))[0]
        n2 = _norm(bilerp(NRM_tr, np.array([rb]), np.array([cj])))[0]
        LM[nm2] = Frame(o + n2 * 0.004, np.cross(up_w, n2), n2, up_w, 0.021,
                        nm2)

    # ======================================================================
    #  EMIT
    # ======================================================================
    ob = acc.emit(coll, mats, PFX + nm)
    if place is not None:
        ob.location = tuple(float(c) for c in
                            (np.array(ob.location) + np.asarray(place, float)))
        for k in LM:
            LM[k].o = LM[k].o + np.asarray(place, float)
    su = Suit()
    su.obj = ob
    su.spec = spec
    su.skel = skel
    su.landmarks = LM
    su.name = nm
    su.verts = len(ob.data.vertices)
    su.tris = sum(max(len(p.vertices) - 2, 1) for p in ob.data.polygons)
    ob["cfo_team"] = T.name
    ob["cfo_pose"] = spec.pose.name
    ob["cfo_build"] = b.name
    ob["cfo_uid"] = spec.uid
    return su


# --------------------------------------------------------------------------- #
# 12.  materials                                                                #
# --------------------------------------------------------------------------- #

def _new_mat(name):
    m = bpy.data.materials.get(PFX + name)
    if m is None:
        m = bpy.data.materials.new(PFX + name)
    g = NG(m)
    out = g.n("ShaderNodeOutputMaterial")
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.lk(bsdf, 0, out, 0)
    return m, g, bsdf, out


def _chan(g):
    base = g.attr("base")
    aux = g.attr("aux")
    wear = g.attr("wear")
    bs = g.sep(base)          # r,g,b = colour ; alpha via separate
    au = g.sep(aux)           # r seam, g sheen, b panel
    we = g.sep(wear)          # r abrasion, g dirt, b oil
    tc = g.n("ShaderNodeTexCoord")
    uv = g.sepxyz((tc, 2))    # u = metres around the cloth, v = metres along
    # LAW 6: object space, never Geometry->Position.
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    return base, aux, wear, bs, au, we, tc, uv, obj


def mat_nomex():
    """The shell.  Two-layer aramid twill, dyed, worn, and lived in.

    Seven layers of history, each of which is a thing that physically happened
    to this garment:
      1  the TWILL itself -- 0.62 mm yarns, a 2/1 diagonal wale, slubby.
      2  the DYE LOT -- panels cut from different bolts never match exactly,
         and the shader knows which panel it is on (base.a).
      3  UV FADE on the shoulders and the outsides of the sleeves, where a
         12.5 deg sun has been hitting the same cloth all season.  Aramid
         fades warm and chalky, it does not go grey.
      4  GROUND-IN DIRT, keyed to the weave's valleys, not painted on the
         crowns -- that is what makes dirt look like dirt.
      5  OIL AND FUEL, which do the opposite of dirt: they darken AND gloss.
      6  ABRASION at the knees, elbows and cuffs: the twill's surface fibres
         are broken, so the cloth goes lighter, fuzzier, and its sheen lifts
         while its specular falls.
      7  the SEAM, which is 1.35 mm of folded cloth carrying a thread that is
         a different fibre with a different roughness.
    """
    m, g, b, _ = _new_mat("Nomex")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    U, V = (uv, 0), (uv, 1)
    seam, sheenv = (au, 0), (au, 1)
    abr, dirt, oil = (we, 0), (we, 1), (we, 2)
    # sun fade lives in wear's ALPHA, which SeparateColor cannot see -- the
    # Attribute node's own Alpha output is the only way to it.
    fadev = (wear, 3)

    # ---- 1. the twill ----------------------------------------------------
    # 0.62 mm yarn pitch = 1613 cycles/m.  A twill's wale runs at ~63 deg, so
    # the diagonal is built from a rotated combination of u and v rather than
    # from two independent bands.
    puv = g.comb(U, V, 0.0)
    warp = g.wave(puv, scale=1613.0, dist=0.0, detail=0.0, band='X')
    weft = g.wave(g.vmath('ADD', puv, (0.00031, 0.0, 0.0)), scale=1613.0,
                  dist=0.0, detail=0.0, band='Y')
    diag = g.comb(g.math('ADD', g.math('MULTIPLY', U, 0.4472),
                         g.math('MULTIPLY', V, 0.8944)), 0.0, 0.0)
    wale = g.wave(diag, scale=538.0, dist=0.0, detail=0.0, band='X')
    slub = g.noise(g.vmath('MULTIPLY', puv, (11.0, 420.0, 1.0)), scale=3.0,
                   detail=3.0, rough=0.55)
    weave = g.math('MAXIMUM', g.math('MULTIPLY', warp, 0.94),
                   g.math('MULTIPLY', weft, 0.88))
    weave = g.math('ADD', g.math('MULTIPLY', weave, 0.62),
                   g.math('MULTIPLY', wale, 0.26))
    weave = g.math('ADD', weave, g.math('MULTIPLY', slub, 0.12), clamp=True)
    valley = g.math('SUBTRACT', 1.0, weave)

    # ---- 2. dye lot / panel ----------------------------------------------
    # dye-lot drift is a PANEL-scale effect (150-300 mm), not a metre-scale
    # airbrush: at scale 1.7 on a 1.8 m object it painted a soft gradient down
    # every back and the suits read as sublimated sportswear.
    lot = g.noise(g.vmath('MULTIPLY', obj, (6.5, 6.5, 6.5)), scale=2.0,
                  detail=5.0, rough=0.55)
    lotk = g.math('ADD', 0.972, g.math('MULTIPLY',
                                       g.math('SUBTRACT', lot, 0.5), 0.056))
    col = g.mix(0.0, base, base)
    col = g.n("ShaderNodeMixRGB", blend_type='MULTIPLY')
    g._feed(col, 0, 1.0); g._feed(col, 1, base)
    g._feed(col, 2, g.comb(lotk, lotk, lotk))

    # ---- 3. UV fade -------------------------------------------------------
    patch = g.noise(g.vmath('MULTIPLY', obj, (3.2, 3.2, 3.2)), scale=2.0,
                    detail=6.0)
    fk = g.math('MULTIPLY', fadev,
                g.math('ADD', 0.45, g.math('MULTIPLY', patch, 0.75)),
                clamp=True)
    hsv = g.n("ShaderNodeHueSaturation")
    g._feed(hsv, 0, 0.508)
    g._feed(hsv, 1, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', fk, 0.34)))
    g._feed(hsv, 2, g.math('ADD', 1.0, g.math('MULTIPLY', fk, 0.20)))
    g._feed(hsv, 3, 1.0)
    g._feed(hsv, 4, col)
    col = g.mix(g.math('MULTIPLY', fk, 0.92), col, hsv)

    # ---- 6. abrasion (before dirt: worn cloth then gets dirty) ------------
    pill = g.voro(g.vmath('MULTIPLY', obj, (240.0, 240.0, 240.0)), scale=1.0,
                  rand=0.9, feature='F1')
    fuzz = g.noise(g.vmath('MULTIPLY', obj, (95.0, 95.0, 95.0)), scale=2.0,
                   detail=6.0, rough=0.62)
    abrk = g.math('MULTIPLY', abr,
                  g.math('ADD', 0.45, g.math('MULTIPLY', fuzz, 1.1)),
                  clamp=True)
    worn = g.n("ShaderNodeHueSaturation")
    g._feed(worn, 0, 0.5)
    g._feed(worn, 1, 0.62); g._feed(worn, 2, 1.34); g._feed(worn, 3, 1.0)
    g._feed(worn, 4, col)
    col = g.mix(g.math('MULTIPLY', abrk, 0.72), col, worn)

    # ---- 4. dirt ----------------------------------------------------------
    grime = g.noise(g.vmath('MULTIPLY', obj, (7.5, 7.5, 7.5)), scale=2.5,
                    detail=7.0, rough=0.64)
    grit = g.voro(g.vmath('MULTIPLY', obj, (520.0, 520.0, 520.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    dk = g.math('MULTIPLY',
                g.math('MULTIPLY', dirt,
                       g.math('ADD', 0.30, g.math('MULTIPLY', grime, 1.25))),
                g.math('ADD', 0.38, g.math('MULTIPLY', valley, 0.95)),
                clamp=True)
    dk = g.math('ADD', dk, g.math('MULTIPLY',
                                  g.math('MULTIPLY', dirt, grit), 0.18),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.86), col, (0.052, 0.045, 0.038))

    # ---- 5. oil and fuel --------------------------------------------------
    ok = g.math('MULTIPLY', oil,
                g.ramp(g.noise(g.vmath('MULTIPLY', obj, (14.0, 14.0, 14.0)),
                               scale=2.0, detail=6.0),
                       [(0.42, (0, 0, 0)), (0.62, (1, 1, 1))]), clamp=True)
    col = g.mix(g.math('MULTIPLY', ok, 0.80), col,
                g.mix(0.72, col, (0.020, 0.017, 0.014)))
    g._feed(b, 0, col)

    # ---- roughness --------------------------------------------------------
    rough = g.math('SUBTRACT', 0.925, g.math('MULTIPLY', valley, 0.045))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.075))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', ok, 0.42))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', abrk, 0.055))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', seam, 0.10),
                   clamp=True)
    g._feed(b, 2, rough)
    sp = _bsdf_in(b, "Specular IOR Level", "Specular")
    if sp:
        sp.default_value = 0.22

    # ---- cloth SHEEN.  Without it a garment renders as painted plastic.
    for nm_, val in (("Sheen Weight",
                      g.math('ADD', 0.22,
                             g.math('MULTIPLY',
                                    g.math('ADD', abrk,
                                           g.math('MULTIPLY', sheenv, 0.5)),
                                    0.30))),
                     ("Sheen Roughness",
                      g.math('SUBTRACT', 0.70,
                             g.math('MULTIPLY', abrk, 0.12)))):
        if nm_ in b.inputs:
            g._feed(b, nm_, val)
    if "Sheen Tint" in b.inputs:
        g._feed(b, "Sheen Tint", g.mix(0.5, col, (1.0, 0.96, 0.90)))

    # ---- relief -----------------------------------------------------------
    crumple = g.noise(g.vmath('MULTIPLY', obj, (52.0, 52.0, 52.0)), scale=2.0,
                      detail=5.0, rough=0.58)
    h = g.math('ADD', g.math('MULTIPLY', weave, 0.28),
               g.math('MULTIPLY', crumple, 0.30))
    h = g.math('ADD', h, g.math('MULTIPLY', abrk, 0.22))
    h = g.math('ADD', h, g.math('MULTIPLY', seam, 0.34))
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES.  itemkit section 5b,
    # ITEM-CAMPAIGN-BRIEF 4a.  m = 2 sin(theta) / tan(e); this film's 12.47 deg
    # sun is a 4.52x amplifier and its ceiling is 2/tan(e) = 9.04, past which no
    # slope exists that will deliver the asked-for modulation.
    #
    # THIS IS CLOTH ON A PERSON, AND CLOTH ON A PERSON HAS A RECORDED ANSWER.
    # Three amplitude sets were rendered and REJECTED on the human figures:
    # m 0.79 read as a machined cone, 3.76 as coarse stucco, 1.66 as thick felt;
    # m = 0.28, RELIEF_BANDS["isotropic_micro"], was ACCEPTED, with the creases
    # carrying the rest.  That is the number this garment is now aimed at.
    #
    # EVERY STAGE IN THIS MODULE IS A DELIBERATE RE-TUNE DOWNWARD, and they are
    # not close calls.  Measured honestly -- from the band's own weight in the
    # height sum, and from the wavelength the texture actually has once its
    # COORDINATE PRE-MULTIPLY is included -- what this material shipped was
    #
    #   nomex [0] crumple  w 0.30  lam 15.385 mm  m 8.877   25.2  mm p-p
    #             twill    w 0.163 lam  0.195 mm  m 9.043   13.7  mm p-p
    #             wale     w 0.073 lam  0.584 mm  m 9.039    6.1  mm p-p
    #   nomex [1] slub     w 0.50  lam  1.270 mm  m 9.016    5.2  mm p-p
    #
    # 25 mm of bump on a crumple 15 mm across is not felt, it is corrugated
    # iron, and it sat within 2 % of the terminator.  It was never seen because
    # R2-038 left the Height socket on a constant, so the whole stack was dead
    # and its Distance was never a variable anyone could have judged.  A rebuild
    # makes it real for the first time, which is exactly why it cannot ship as
    # it stands.
    #
    # WHICH BAND IS NAMED.  `h` is a sum of four, so one wavelength for the
    # stage is a choice.  The crumple is named: it is ungated, it carries the
    # largest single weight, and at 15.4 mm it is 5.7 screen pixels at this
    # item's 373 px/m -- it is the band the eye actually resolves.  With it at
    # 0.28 the rest of the stage lands at
    #
    #   twill  w 0.163  lam 0.195 mm  m 7.230     0.073 px -- see below
    #   seam   w 0.34   lam 1.35  mm  m 3.359     hard_feature, gated, correct
    #   wale   w 0.073  lam 0.584 mm  m 1.757     hard_feature
    #   abrk   w 0.22   lam 8.42  mm  m 0.375     isotropic_micro, gated
    #   slub   w 0.034  lam 1.27  mm  m 0.380     isotropic_micro
    #
    # THE ONE THING THIS MIGRATION COULD NOT FIX.  The twill lands at m 7.230,
    # off the top of every band, because `weave` enters `h` at 0.28 while
    # sitting at a 79x shorter wavelength than the crumple: the two are locked
    # together by the height expression and only one of them can be aimed.  It
    # is left where it falls because (a) 0.195 mm is a fourteenth of a screen
    # pixel here, so it perturbs the shading lobe -- and the sampling variance
    # -- rather than drawing a read, and (b) putting BOTH bands inside
    # isotropic_micro needs `weave`'s weight in this sum cut from 0.28 to about
    # 0.011, which is a restructure of the height expression and not a change of
    # depth.  THAT, AND THE WAVE PITCH BELOW, ARE THE NEXT TWO EDITS ON THIS
    # MATERIAL.  Stage [1] carries the twill at a defensible m 1.057.
    #
    # THE WAVELENGTHS COME FROM THE LITERALS THAT PICKED THE SCALES -- INCLUDING
    # THE COORDINATE PRE-MULTIPLIES, WHICH ARE THE WHOLE STORY HERE.  `crumple`
    # is a Noise of scale 2.0 read on obj * 52, so it is 104 cycles/m and 15.4
    # mm, not the 800 mm a reader of the Scale socket alone would report -- a
    # factor of 52, and therefore a factor of 52 in every slope.
    #
    # AND THE WAVE BANDS ARE 3.183x FINER THAN 1/Scale.  A ShaderNodeTexWave
    # multiplies the coordinate by 20 before the sine, so its period is
    # 2*pi/20 = 0.31416 of 1/Scale; that closed form is what itemkit's own
    # header used as the CONTROL when it measured the Noise and Voronoi factors
    # (probe 0.3136 against 0.31416).  So this shader's twill is 0.195 mm and
    # not the "0.62 mm yarn pitch" section 1 declares, its wale is 0.584 mm and
    # its 4.4 mm knit rib is 1.384 mm.  Nothing here changes a Scale -- that is
    # a frequency repair and it is a different job -- but the modulations are
    # computed against the pitch the node EMITS, because that is the surface the
    # sun will actually meet.
    LAM_CRUMPLE = K.NOISE_WAVELENGTH_FACTOR / (52.0 * 2.0)    # 15.38 mm
    LAM_SLUB = K.NOISE_WAVELENGTH_FACTOR / (3.0 * 420.0)      #  1.27 mm
    bmp = g.bump(h, 0.30, modulation_pp=0.28, wavelength_m=LAM_CRUMPLE,
                 height_pp=0.30)
    # the fine layer: the slub is named (w 0.5, 1.27 mm), also at the accepted
    # cloth 0.28.  The twill riding on it lands at m 1.057 (`geometry_fold`) and
    # the wale at m 0.158 -- an aramid twill's yarn crown really is a ridge at
    # its own scale, and this is the stage where it is stated honestly.
    fine = g.bump(g.math('ADD', g.math('MULTIPLY', slub, 0.5),
                         g.math('MULTIPLY', weave, 0.5)), 0.13,
                  normal=bmp, modulation_pp=0.28, wavelength_m=LAM_SLUB,
                  height_pp=0.50)
    g._feed_named(b, "Normal", fine)
    return m


def mat_knit():
    """Cuff and hem rib.  4.4 mm rib, fuzzy, and it has been stretched."""
    m, g, b, _ = _new_mat("Knit")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    abr, dirt = (we, 0), (we, 1)
    puv = g.comb((uv, 0), (uv, 1), 0.0)
    rib = g.wave(puv, scale=227.0, dist=0.0, detail=0.0, band='X',
                 prof='SIN')
    loop = g.voro(g.vmath('MULTIPLY', obj, (330.0, 330.0, 330.0)), scale=1.0,
                  rand=0.85, feature='SMOOTH_F1')
    fuzz = g.noise(g.vmath('MULTIPLY', obj, (140.0, 140.0, 140.0)), scale=2.0,
                   detail=6.0, rough=0.66)
    lot = g.noise(g.vmath('MULTIPLY', obj, (3.0, 3.0, 3.0)), scale=2.0,
                  detail=4.0)
    k = g.math('ADD', 0.93, g.math('MULTIPLY', g.math('SUBTRACT', lot, 0.5),
                                   0.18))
    col = g.n("ShaderNodeMixRGB", blend_type='MULTIPLY')
    g._feed(col, 0, 1.0); g._feed(col, 1, base); g._feed(col, 2, g.comb(k, k, k))
    grime = g.noise(g.vmath('MULTIPLY', obj, (10.0, 10.0, 10.0)), scale=2.5,
                    detail=6.0)
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.42, g.math('MULTIPLY', grime, 1.05)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.80), col, (0.048, 0.042, 0.036))
    lift = g.n("ShaderNodeHueSaturation")
    g._feed(lift, 0, 0.5); g._feed(lift, 1, 0.70); g._feed(lift, 2, 1.28)
    g._feed(lift, 3, 1.0); g._feed(lift, 4, col)
    col = g.mix(g.math('MULTIPLY', abr, 0.6), col, lift)
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('ADD', 0.945, g.math('MULTIPLY', dk, 0.05),
                         clamp=True))
    if "Sheen Weight" in b.inputs:
        g._feed(b, "Sheen Weight", 0.40)
        g._feed(b, "Sheen Roughness", 0.78)
    h = g.math('ADD', g.math('MULTIPLY', rib, 0.62),
               g.math('MULTIPLY', loop, 0.26))
    h = g.math('ADD', h, g.math('MULTIPLY', fuzz, 0.20))
    # STATED AS RADIANCE MODULATION (itemkit 5b, brief 4a; the long argument is
    # in `mat_nomex`).  A DELIBERATE RE-TUNE DOWNWARD: shipped, the rib band
    # ran 34.1 mm p-p, m 9.036 against a ceiling of 9.043 -- the stage was
    # pinned at the terminator and only R2-038's dead Height socket hid it.
    #
    # THE RIB IS NOT 4.4 mm.  A ShaderNodeTexWave multiplies the coordinate by
    # 20 before the sine, so its period is 2*pi/20 = 0.31416 of 1/Scale -- that
    # is the closed form itemkit's own header uses as the CONTROL for its Noise
    # and Voronoi factors, and the probe returned 0.3136 against it.  Scale 227
    # therefore emits a 1.384 mm rib, not the 4.405 mm this docstring claims,
    # and `itemkit._tex_wavelength_m` used to return 1.0/Scale for a Wave and so
    # reported the long figure.  R2-058 fixed that: itemkit now publishes
    # `WAVE_WAVELENGTH_FACTOR = 2*pi/20` and the audit agrees with this module,
    # so the local copy of the closed form above is gone and there is ONE
    # source.  The depth below is chosen against the rib the
    # node ACTUALLY EMITS.  Correcting the pitch is a frequency change, not a
    # depth change, and belongs to whoever owns the look of this cuff: Scale
    # would go 227 -> 71 for a true 4.4 mm rib.
    #
    # 1.000 is the middle of RELIEF_BANDS["geometry_fold"] (0.60-1.40), and a
    # knit rib IS a fold -- a regular corrugation of the fabric, not a grain.
    # It is kept well under the 1.66 that rendered as thick felt on these same
    # figures, and it only ever covers cuffs and hems.  49 um p-p.
    # HONEST CONSEQUENCE: with the rib that fine, `loop` (6.58 mm) and `fuzz`
    # (5.71 mm) fall to m 0.089 and 0.079, under the isotropic_micro floor --
    # the height sum's weights (0.62 / 0.26 / 0.20) were chosen for three bands
    # of similar size and the rib is now 4.8x finer than the other two.  That is
    # the pitch bug above showing through, not a depth choice.
    LAM_RIB = K.WAVE_WAVELENGTH_FACTOR / 227.0              # 1.384 mm (Wave)
    g._feed_named(b, "Normal", g.bump(h, 0.55, modulation_pp=1.000, wavelength_m=LAM_RIB,
                                      height_pp=0.62))
    return m


def mat_embroidery():
    """Satin stitch.  Thread runs one way, so the highlight is anisotropic and
    the surface is made of 0.35 mm rounded ridges, not of ink."""
    m, g, b, _ = _new_mat("Embroidery")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    puv = g.comb((uv, 0), (uv, 1), 0.0)
    satin = g.wave(puv, scale=2860.0, dist=0.0, detail=0.0, band='Y')
    twist = g.wave(g.vmath('MULTIPLY', puv, (1.0, 1.0, 1.0)), scale=1200.0,
                   dist=1.2, detail=1.0, band='X')
    lint = g.noise(g.vmath('MULTIPLY', obj, (180.0, 180.0, 180.0)), scale=2.0,
                   detail=5.0)
    grime = g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 9.0)), scale=2.0,
                    detail=5.0)
    dk = g.math('MULTIPLY', (we, 1),
                g.math('ADD', 0.4, g.math('MULTIPLY', grime, 1.0)), clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.6), base, (0.055, 0.050, 0.044))
    col = g.mix(g.math('MULTIPLY', (wear, 3), 0.35), col,
                g.mix(0.5, col, (0.72, 0.70, 0.64)))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', 0.52,
                         g.math('MULTIPLY', satin, 0.10), clamp=True))
    if "Sheen Weight" in b.inputs:
        g._feed(b, "Sheen Weight", 0.45)
    sp = _bsdf_in(b, "Specular IOR Level", "Specular")
    if sp:
        sp.default_value = 0.55
    h = g.math('ADD', g.math('MULTIPLY', satin, 0.70),
               g.math('MULTIPLY', twist, 0.18))
    h = g.math('ADD', h, g.math('MULTIPLY', lint, 0.12))
    # STATED AS RADIANCE MODULATION (itemkit 5b, brief 4a; argument in
    # `mat_nomex`).  A DELIBERATE RE-TUNE DOWNWARD: shipped, the satin band
    # ran 17.6 mm p-p at m 9.0432 -- 9.0434 is the ceiling.  It was 0.0002 pp
    # off being an arithmetic error rather than a surface.
    #
    # THE RIDGE IS 0.110 mm, NOT 0.35 mm.  A ShaderNodeTexWave multiplies the
    # coordinate by 20 before the sine, so its period is 2*pi/20 = 0.31416 of
    # 1/Scale -- the closed form itemkit's header uses as the control for its
    # own Noise and Voronoi factors.  Scale 2860 emits 0.110 mm.  The depth is
    # chosen against what the node emits; correcting the pitch to the 0.35 mm
    # this docstring wants is Scale 2860 -> 898, a frequency change and not this
    # migration's to make.
    #
    # 0.450 is the top of RELIEF_BANDS["isotropic_micro"] (0.12-0.45), the band
    # for a woven or cast skin, and the top rather than the middle because the
    # satin's directional ridge is the whole reason this material is not a
    # sticker.  It is capped there and not taken into `hard_feature` for the
    # reason `armco_w_beam` wrote down about its own skin-pass marks: at
    # 373 px/m a 0.110 mm ridge is a twenty-fourth of a screen pixel, and a
    # sub-pixel band driven hard does not resolve, it ALIASES.  1.7 um p-p.
    # HONEST CONSEQUENCE: `twist` falls to m 0.049 and `lint` to m 0.002, i.e.
    # both go silent as relief.  They are locked to the satin by the height sum
    # and cannot be raised without lifting it too.  `satin` still drives the
    # roughness independently, which is where this badge's anisotropy really
    # comes from; the two quiet bands are the price of not restructuring `h`.
    LAM_SATIN = K.WAVE_WAVELENGTH_FACTOR / 2860.0           # 0.110 mm (Wave)
    g._feed_named(b, "Normal", g.bump(h, 0.42, modulation_pp=0.450, wavelength_m=LAM_SATIN,
                                      height_pp=0.70))
    return m


def mat_hardware():
    """Zip teeth, slider, buckle.  Nickel that has been done up 400 times."""
    m, g, b, _ = _new_mat("Hardware")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    brush = g.noise(g.vmath('MULTIPLY', obj, (900.0, 26.0, 900.0)), scale=2.0,
                    detail=5.0, rough=0.6)
    micro = g.noise(g.vmath('MULTIPLY', obj, (420.0, 420.0, 420.0)), scale=2.0,
                    detail=4.0)
    tarn = g.voro(g.vmath('MULTIPLY', obj, (140.0, 140.0, 140.0)), scale=1.0,
                  rand=1.0, feature='F1')
    col = g.mix(g.math('MULTIPLY', (we, 0), 0.55), base,
                g.mix(0.5, base, (0.09, 0.075, 0.058)))
    col = g.mix(g.math('MULTIPLY', tarn, 0.22), col, (0.16, 0.14, 0.12))
    g._feed(b, 0, col)
    g._feed(b, 1, 0.92)
    g._feed(b, 2, g.math('ADD', 0.24,
                         g.math('ADD', g.math('MULTIPLY', brush, 0.20),
                                g.math('MULTIPLY', (we, 0), 0.22)),
                         clamp=True))
    # STATED AS RADIANCE MODULATION (itemkit 5b, brief 4a; argument in
    # `mat_nomex`).  A DELIBERATE RE-TUNE DOWNWARD: shipped, the brush band
    # (w 0.6 on a 0.89 mm streak) ran 5.28 mm p-p at m 9.030 against a 9.043
    # ceiling -- 5 mm of relief on a zip tooth.
    #
    # 0.400 is the upper half of RELIEF_BANDS["isotropic_micro"] (0.12-0.45),
    # which is the band for BLASTED AND BRUSHED METAL, and it is taken at the
    # upper end so that the co-band `micro` lands at m 0.125, just inside the
    # same band, instead of going silent.  12.5 um p-p, which is what a brushed
    # nickel slider that has been done up 400 times actually carries.
    # `brush` is a Noise of scale 2.0 read on obj * (900, 26, 900): 1800
    # cycles/m across the streaks, 52 cycles/m along them, so the named
    # wavelength is 0.89 mm -- the one the gradient crosses.  Along the streaks
    # it is 30.8 mm and m 0.009, which is what makes it read as brushed.
    LAM_BRUSH = K.NOISE_WAVELENGTH_FACTOR / (900.0 * 2.0)   # 0.89 mm
    g._feed_named(b, "Normal", g.bump(g.math('ADD', g.math('MULTIPLY', brush, 0.6),
                                             g.math('MULTIPLY', micro, 0.4)), 0.22,
                                      modulation_pp=0.400, wavelength_m=LAM_BRUSH,
                                      height_pp=0.60))
    return m


_MATS = None


def materials(force=False):
    """The four slots, in index order.  Idempotent."""
    global _MATS
    if _MATS is not None and not force:
        if all(m.name in bpy.data.materials for m in _MATS):
            return _MATS
    _MATS = [mat_nomex(), mat_knit(), mat_embroidery(), mat_hardware()]
    return _MATS


# --------------------------------------------------------------------------- #
# 13.  the family, and the test scene                                           #
# --------------------------------------------------------------------------- #

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    """Idempotence: everything this module owns is CFO_* and goes first."""
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PFX) or me.users == 0:
            bpy.data.meshes.remove(me)


def crew_layout(n, box_c=(-160.0, 17.5), seed=0):
    """Where 110 crew actually stand in a pit lane.

    Not a scatter: a working stop has a fixed geometry (four gunners on the
    corners, two carriers per corner, jacks fore and aft, stabilisers on the
    flanks, a release man out front) and everyone else is queueing, watching
    from the wall, or walking.  Returns [(circuit_xy, facing_deg, pose_hint)].
    """
    cx, cy = box_c
    out = []
    # index 0 is THE HERO of the macro frame: a tyre carrier crossing the lane
    # toward the wall, three-quarters on to the lens, with the whole stop
    # working behind him.  Everyone at a stop faces inward, so without him the
    # item's own macro render is 60 backs.
    out.append(((cx + 2.6, cy - 3.3), -104.0, "carry_tyre_high"))
    # --- the stop itself, car axis along circuit +x -----------------------
    wheel = [(1.72, 0.86), (1.72, -0.86), (-1.68, 0.86), (-1.68, -0.86)]
    for i, (dx, dy) in enumerate(wheel):
        out.append(((cx + dx, cy + dy), -90.0 if dy > 0 else 90.0,
                    "crouch_gun"))
        out.append(((cx + dx + 0.42, cy + dy * 1.62), -102.0 if dy > 0 else 102.0,
                    "crouch_ready"))
        out.append(((cx + dx - 0.46, cy + dy * 1.70), -78.0 if dy > 0 else 78.0,
                    "carry_tyre_high"))
    out.append(((cx + 3.35, cy), 180.0, "jack_ready"))
    out.append(((cx - 3.55, cy - 0.10), 0.0, "jack_down"))
    out.append(((cx + 0.15, cy + 1.35), -90.0, "stabilise_lean"))
    out.append(((cx + 0.15, cy - 1.35), 90.0, "stabilise_lean"))
    out.append(((cx + 4.20, cy + 0.85), 168.0, "point_forward"))
    out.append(((cx + 4.05, cy - 1.05), 150.0, "stop_go_board"))
    out.append(((cx - 0.90, cy + 1.15), -100.0, "lean_over_car"))
    out.append(((cx + 1.05, cy - 1.20), 80.0, "kneel_r"))
    out.append(((cx - 2.10, cy + 1.28), -100.0, "kneel_l"))
    out.append(((cx + 2.55, cy + 1.30), -116.0, "wing_adjust_kneel"))
    out.append(((cx + 2.40, cy - 1.32), 108.0, "reach_forward"))
    # --- the wall line, and the queue down the lane -----------------------
    k = len(out)
    i = 0
    while len(out) < n:
        u = hash01(seed, i, "lay")
        v = hash01(seed, i, "lay2")
        w = hash01(seed, i, "lay3")
        if i < 14:                       # against the pit wall, watching
            x = cx + 12.5 + i * 1.34 + (u - 0.5) * 0.5
            y = cy - 4.65 + (v - 0.5) * 0.45
            f = 8.0 + (w - 0.5) * 34.0
            ph = pick(["hands_hips", "arms_folded", "watch_hands_low",
                       "stand_ready", "radio_hand"], seed, i, "wp")
        elif i < 34:                     # the next box up the lane
            x = cx + 24.0 + (i - 14) * 1.46 + (u - 0.5) * 0.9
            y = cy + 1.4 - 4.2 * v
            f = -90.0 if y > cy else 90.0
            f += (w - 0.5) * 60.0
            ph = pick(POSE_NAMES, seed, i, "np")
        else:                            # deeper down the lane, receding
            x = cx + 52.0 + (i - 34) * 1.15 + (u - 0.5) * 2.4
            y = cy + 3.2 - 7.0 * v
            f = 90.0 + (w - 0.5) * 220.0
            ph = pick(POSE_NAMES, seed, i, "dp")
        out.append(((x, y), f, ph))
        i += 1
    return out[:n]


def build(coll_name=ROOT_COLL, n=110, seed=0, box_c=(-160.0, 17.5),
          cam_at=None, lod=True, do_purge=True):
    """Emit the crew.  Returns [Suit].

    Every suit is its own mesh from its own parameter draw -- no linked
    duplicates, no geometry-nodes instancing -- so per-instance variation is
    something the acceptance gate can MEASURE rather than be told.
    """
    if do_purge:
        purge()
    mats = materials()
    root = _coll(coll_name)
    lay = crew_layout(n, box_c, seed)
    suits = []
    for i, ((cxx, cyy), fdeg, phint) in enumerate(lay):
        wx, wy = C.circuit_to_world(cxx, cyy)
        gz, owner = C.world_ground_z(wx, wy)
        if not np.isfinite(gz):
            gz = 0.0
        uid = seed * 1000 + i
        sp = suit_spec(uid, pose=phint)
        if cam_at is not None and lod:
            d = math.hypot(wx - cam_at[0], wy - cam_at[1])
            sp.res = 1.0 if d < 16.0 else (0.72 if d < 30.0 else 0.52)
        # face the figure: rotate the whole skeleton about z
        # local +Y is FORWARD; rotating by yaw sends it to world bearing
        # yaw+90, so the -90 is what makes `fdeg` mean 'circuit bearing
        # this person is facing'.
        yaw = math.radians(fdeg + C.ROT_DEG - 90.0)
        cz, sz = math.cos(yaw), math.sin(yaw)
        base_rot = spec_rot = np.array([[cz, -sz, 0.0], [sz, cz, 0.0],
                                        [0.0, 0.0, 1.0]])
        sp.pose = sp.pose.copy(sp.pose.name)
        su = build_suit(sp, root, mats, name="S%03d" % i)
        # rotate + place.  Feet are already on local z = 0, so the only
        # vertical number that touches the world is world_ground_z.
        ob = su.obj
        ob.rotation_mode = 'ZYX'
        ob.rotation_euler = (0.0, 0.0, yaw)
        loc = np.array(ob.location)
        ob.location = (float(wx + (base_rot @ loc)[0]),
                       float(wy + (base_rot @ loc)[1]),
                       float(gz + loc[2]))
        M = np.eye(4); M[:3, :3] = base_rot
        M[:3, 3] = np.array([wx, wy, gz])
        for kk in su.landmarks:
            f = su.landmarks[kk]
            f.o = M[:3, :3] @ f.o + M[:3, 3]
            f.x = M[:3, :3] @ f.x
            f.y = M[:3, :3] @ f.y
            f.z = M[:3, :3] @ f.z
        su.obj["cfo_world_ground_z"] = float(gz)
        su.obj["cfo_ground_owner"] = str(owner)
        suits.append(su)
    return suits


def contract_light(scene=None):
    """The film's one sun, plus its sky.  Numbers from world_contract S13."""
    sc = scene or bpy.context.scene
    import fix_audit_blend as FA
    FA.procedural_world()
    sun = bpy.data.objects.get("CFO_Sun")
    if sun is None:
        d = bpy.data.lights.new("CFO_Sun", 'SUN')
        sun = bpy.data.objects.new("CFO_Sun", d)
        sc.collection.objects.link(sun)
    L = sun.data
    L.energy = C.SUN_ENERGY
    L.color = C.SUN_COLOR
    L.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    d = np.array(C.SUN_DIR, float)
    z = np.array([0.0, 0.0, 1.0])
    axis = np.cross(z, -d)
    ang = math.acos(float(np.clip(np.dot(z, -d), -1, 1)))
    if np.linalg.norm(axis) < 1e-9:
        axis = np.array([1.0, 0.0, 0.0])
    axis = axis / np.linalg.norm(axis)
    sun.rotation_mode = 'AXIS_ANGLE'
    sun.rotation_axis_angle = (ang, *axis)
    sun.location = (0.0, 0.0, 40.0)
    sc.view_settings.view_transform = C.VIEW_TRANSFORM
    sc.view_settings.look = C.VIEW_LOOK
    sc.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    return sun


def ground_plane(centre, size=44.0, name="CTX_Apron"):
    """Context only, NOT part of this item and NOT emitted by build().

    The pit-lane apron the crew stand on, so the macro render has contact
    shadows and a bounce.  Prefixed CTX_ so the acceptance gate never counts it
    as the garment, and kept to 44 m because at 160 m it reached the racing
    surface and tripped tools/placement_gate.py 0.856 m into the road corridor.
    The world assembly never sees this object -- build() does not emit it."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NG(m)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (2.5, 2.5, 2.5)), scale=2.0,
                 detail=8.0, rough=0.6)
    n2 = g.voro(g.vmath('MULTIPLY', obj, (85.0, 85.0, 85.0)), scale=1.0,
                rand=1.0, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', n1, 0.9), (0.055, 0.054, 0.052),
                (0.105, 0.102, 0.098))
    col = g.mix(g.math('MULTIPLY', n2, 0.35), col, (0.036, 0.035, 0.034))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', 0.86, g.math('MULTIPLY', n2, 0.10)))
    g._feed_named(b, "Normal", g.bump(g.math('ADD', g.math('MULTIPLY', n2, 0.6),
                                             g.math('MULTIPLY', n1, 0.4)), 0.18, 0.05))
    me = bpy.data.meshes.new(name)
    h = size * 0.5
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [],
                   [(0, 1, 2, 3)])
    me.update()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = (centre[0], centre[1], centre[2])
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mat_underform():
    """Matte black knit for the PLACEHOLDER under-forms.  Not part of this item."""
    m, g, b, _ = _new_mat("UnderForm")
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (160.0, 160.0, 160.0)), scale=2.0,
                 detail=6.0)
    n2 = g.voro(g.vmath('MULTIPLY', obj, (420.0, 420.0, 420.0)), scale=1.0,
                rand=0.9, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', n1, 0.5), (0.016, 0.016, 0.018),
                (0.034, 0.033, 0.036))
    g._feed(b, 0, col)
    g._feed(b, 2, 0.93)
    if "Sheen Weight" in b.inputs:
        g._feed(b, "Sheen Weight", 0.5)
        g._feed(b, "Sheen Roughness", 0.75)
    # STATED AS RADIANCE MODULATION (itemkit 5b, brief 4a; argument in
    # `mat_nomex`).  A DELIBERATE RE-TUNE DOWNWARD: shipped, the `n2` band
    # (w 0.6 on a 5.17 mm cell) ran 5.4 mm p-p at m 8.651.  This is a matte
    # black knit, so it is aimed at the accepted human-figure cloth value,
    # m = 0.28, RELIEF_BANDS["isotropic_micro"]; 51 um p-p, and `n1` follows to
    # m 0.193, in the same band.  These are STANDIN_ placeholders that the gate
    # cannot see, but a stand-in at the terminator would still light the real
    # garment's shadows wrongly in any macro render used to judge it.
    LAM_LOOP = K.VORONOI_WAVELENGTH_FACTOR / 420.0          # 5.17 mm
    g._feed_named(b, "Normal", g.bump(g.math('ADD', g.math('MULTIPLY', n2, 0.6),
                                             g.math('MULTIPLY', n1, 0.4)), 0.30,
                                      modulation_pp=0.28, wavelength_m=LAM_LOOP,
                                      height_pp=0.60))
    return m


def _blob(acc, ctr, ex, ey, ez, rx, ry, rz, nu=28, nv=16, squash=None,
          mat=0, base=(0.02, 0.02, 0.022, 0.0)):
    """One superellipsoid, for the placeholder under-forms."""
    th = np.linspace(0, 2 * math.pi, nu, endpoint=False)
    ph = np.linspace(-0.5 * math.pi, 0.5 * math.pi, nv)
    TH, PH = np.meshgrid(th, ph)
    cx = np.cos(PH) * np.cos(TH) * rx
    cy = np.cos(PH) * np.sin(TH) * ry
    cz = np.sin(PH) * rz
    if squash is not None:
        cz = cz * squash(np.sin(PH))
    P = (np.asarray(ctr, float)[None, None, :]
         + np.asarray(ex, float)[None, None, :] * cx[..., None]
         + np.asarray(ey, float)[None, None, :] * cy[..., None]
         + np.asarray(ez, float)[None, None, :] * cz[..., None])
    i0 = acc.verts(P.reshape(-1, 3), uv=np.zeros((nu * nv, 2)), base=base,
                   aux=(0, 0, 0, 0), wear=(0, 0, 0, 0))
    I = i0 + np.arange(nu * nv).reshape(nv, nu)
    acc.grid_faces(I, mat, wrap_u=True, flip=False)
    return I


def under_forms(suit, coll, mat, name=None):
    """PLACEHOLDER balaclava head, gloves and boots.

    NOT PART OF THIS ITEM and deliberately prefixed STANDIN_ so the acceptance
    gate (--prefix CFO_) cannot see them.  `crew_helmet_visor` and
    `crew_gloves_and_boots` own these for real; they exist here only so the
    macro render can be judged as a garment ON A PERSON instead of as an empty
    suit floating in a pit lane.  Delete them the moment those items land.

    Everything is hung off THIS module's own landmarks, which is also the first
    real test of the attachment contract: if a glove lands 40 mm off the cuff
    here it will land 40 mm off the cuff for crew_gloves_and_boots too.
    """
    L = suit.landmarks
    acc = Acc("STANDIN_" + (name or suit.name))
    up = np.array([0.0, 0.0, 1.0])

    # head + neck, filling the collar mouth
    hd = L["head"]
    _blob(acc, hd.o, hd.x, hd.y, hd.z, 0.088, 0.099, 0.113)
    _blob(acc, hd.o - hd.z * 0.108 + hd.y * 0.012, hd.x, hd.y, hd.z,
          0.062, 0.068, 0.070, nu=22, nv=12)
    cm = L["collar_mouth"]
    _blob(acc, cm.o + cm.y * 0.020, cm.x, cm.z, cm.y, 0.058, 0.062, 0.052,
          nu=22, nv=12)

    for s2 in ("r", "l"):
        # GLOVES hang off the cuff mouth, along the cuff's own down-limb axis
        cw = L["cuff_wrist_" + s2]
        ax = cw.y
        side = _norm(np.cross(ax, up)) if abs(float(np.dot(ax, up))) < 0.97 \
            else np.array([1.0, 0.0, 0.0])
        pal = _norm(np.cross(side, ax))
        _blob(acc, cw.o + ax * 0.048, side, pal, ax,
              0.043, 0.036, 0.058, nu=20, nv=12)
        _blob(acc, cw.o + ax * 0.092 + pal * 0.008, side, pal, ax,
              0.038, 0.032, 0.030, nu=18, nv=10)

        # BOOTS: a foot on the sole plane plus an ankle inside the leg cuff
        so = L["sole_" + s2]
        fwd = _norm(np.array([so.y[0], so.y[1], 0.0]))
        lat = _norm(np.cross(fwd, up))
        _blob(acc, so.o + up * 0.046 + fwd * 0.038, lat, fwd, up,
              0.048, 0.130, 0.044, nu=22, nv=12)
        _blob(acc, so.o + up * 0.092 - fwd * 0.028, lat, fwd, up,
              0.048, 0.062, 0.052, nu=20, nv=12)
        ck = L["cuff_ankle_" + s2]
        _blob(acc, ck.o + ck.y * 0.030, ck.x, ck.z, ck.y,
              0.045, 0.050, 0.048, nu=20, nv=10)
    ob = acc.emit(coll, [mat], "STANDIN_" + (name or suit.name))
    return ob


def macro_camera(hero, name="CAM_CFO_MACRO", dist=10.0, lens=35.0,
                 bearing_deg=None):
    """EXACTLY the manifest's shot: 10.0 m on a 35 mm lens.

    The distance is measured to the garment's chest, because that is the part
    the 653 px in `onscreen_px_4k` is measuring.
    """
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = SENSOR_MM
    cam.sensor_fit = 'HORIZONTAL'
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cam)
        bpy.context.scene.collection.objects.link(ob)
    ob.data = cam
    tgt = hero.landmarks["chest_patch"].o.copy()
    tgt[2] = max(hero.landmarks["belt_back"].o[2] + 0.16, 1.18)
    if bearing_deg is None:
        f = hero.landmarks["chest_patch"].y
        bearing_deg = math.degrees(math.atan2(f[1], f[0]))
    br = math.radians(bearing_deg)
    eye_h = 1.50
    horiz = math.sqrt(max(dist * dist - (eye_h - tgt[2]) ** 2, 0.04))
    pos = np.array([tgt[0] + math.cos(br) * horiz,
                    tgt[1] + math.sin(br) * horiz,
                    tgt[2] + (eye_h - tgt[2])])
    d = tgt - pos
    ob.location = tuple(float(v) for v in pos)
    # Look-at by quaternion.  Hand-rolled Euler angles for a camera are the
    # reason the first macro render was 4K of tarmac and sky: Blender's euler
    # ORDER is applied right-to-left and the sign of the yaw term is not the
    # one you write down from the diagram.
    from mathutils import Vector
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((float(d[0]), float(d[1]), float(d[2]))
                               ).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True
    cam.dof.focus_distance = float(np.linalg.norm(d))
    cam.dof.aperture_fstop = 4.0
    print(">> macro camera %s at %.3f m, %.0f mm  (manifest: 10.0 m / 35 mm)"
          % (name, float(np.linalg.norm(tgt - pos)), lens))
    return ob


SENSOR_MM = 36.0


def test_scene(n=60, out=None, seed=0, samples=192, res=(3840, 2160)):
    """The acceptance scene: a pit-lane crew, the contract sun, one camera at
    the manifest's own distance and lens."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    box = (-160.0, 17.5)
    wx, wy = C.circuit_to_world(*box)
    gz, _o = C.world_ground_z(wx, wy)
    cam_guess = (wx, wy)
    suits = build(n=n, seed=seed, box_c=box, cam_at=cam_guess)
    uf = mat_underform()
    ufc = _coll("STANDIN_UnderForms")
    for su in suits:
        under_forms(su, ufc, uf)
    contract_light(sc)
    ground_plane((wx, wy, float(gz if np.isfinite(gz) else 0.0)), 44.0)
    hero = suits[0]      # the front-right wheel gunner, down on the gun
    # Stand off the pit wall, three-quarters on to the car's axis: the hero
    # faces the lens, the car's line spreads the rest of the stop ACROSS the
    # frame instead of stacking it behind him, and the sightline threads
    # between the two near-side crew rather than through one of them.
    ho = hero.landmarks["chest_patch"].o
    bx, by = C.circuit_to_world(box[0] + 3.7, box[1] - 13.1)
    cam = macro_camera(hero, dist=10.0, lens=35.0,
                       bearing_deg=math.degrees(math.atan2(by - ho[1],
                                                           bx - ho[0])))
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    cy = sc.cycles
    cy.samples = samples
    cy.use_denoising = True
    cy.max_bounces = 12
    cy.diffuse_bounces = 6
    cy.glossy_bounces = 6
    cy.transmission_bounces = 8
    try:
        cy.device = 'GPU'
    except Exception:
        pass
    tris = sum(sum(max(len(p.vertices) - 2, 1) for p in s.obj.data.polygons)
               for s in suits)
    print(">> %d suits, %d triangles, %d verts"
          % (len(suits), tris,
             sum(len(s.obj.data.vertices) for s in suits)))
    if out:
        import fix_audit_blend as FA
        FA.save_clean(out)
    return suits, cam


def _cli():
    argv = sys.argv
    a = argv[argv.index("--") + 1:] if "--" in argv else []
    if "--test" in a:
        n = int(a[a.index("--n") + 1]) if "--n" in a else 60
        out = a[a.index("--out") + 1] if "--out" in a else None
        seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 0
        test_scene(n=n, out=(os.path.join(ROOT, out) if out and
                             not os.path.isabs(out) else out), seed=seed)
    elif "--one" in a:
        mats = materials()
        col = _coll(ROOT_COLL)
        sp = suit_spec(int(a[a.index("--uid") + 1]) if "--uid" in a else 3)
        if "--pose" in a:
            sp.pose = POSES[a[a.index("--pose") + 1]]
            sp.kneel_side = KNEELING.get(sp.pose.name, ())
        su = build_suit(sp, col, mats)
        print(">>", sp, "tris", su.tris, "verts", su.verts)
        contract_light()
        if "--out" in a:
            import fix_audit_blend as FA
            FA.save_clean(a[a.index("--out") + 1])


if __name__ == "__main__":
    _cli()
