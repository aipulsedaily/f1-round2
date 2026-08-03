#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
heras_fence_panel.py — CIRCUIT VITRINE, per-item hero campaign, item
``heras_fence_panel`` (zone ``transit_corridor``, wave 1, build order 62,
**5 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every temporary (Heras) fence panel in the world, built as a real welded
assembly — a 40-42.5 mm round-tube frame bent through its top corners, a 4 mm
welded-wire fabric of 34-36 verticals and 5-7 horizontals with a weld nugget at
every one of its 170-250 crossings, open tube spigots you can see down, and a
population in which the lean, the dents, the snapped wires and the gaps are
different on every single panel because they are different MESHES.

    manifest: 3.5 x 2.0 m.  Perimeter plus 3 internal runs.
              "The lean and the gaps are the whole read."

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 3.0 = 1244.4 px/m      ->   1 px = 0.804 mm

    the 2.000 m panel height        2489 px  (overfills the 2160 px frame)
    the 41.5 mm frame tube            52 px   <- must be a round TUBE
    the 4.0 mm mesh wire               5 px   <- must be a tube, not a plane
    the 8 mm two-layer mesh depth     10 px   <- verticals and horizontals are
                                                 SEPARATE LAYERS, not coplanar
    a 7.6 mm weld nugget               9 px   <- must be geometry, 210 of them
    the 1.5 mm tube wall at the        1.9 px <- the spigot bore is a real hole
      open spigot                                with a real rim
    the 4 mm crank where a horizontal  5 px   <- the wire visibly kinks to land
      wire lands on the frame upright              on the upright
    2-4 mm of belly in the fabric    2.5-5 px <- per-wire, per-bay, random phase
    a 0.10 m corner bend radius      124 px   <- and the verticals under it get
                                                 progressively shorter
    zinc spangle, 5-40 mm            6-50 px  <- shading, and it is

Everything in that list except the spangle is mesh.  A fence rendered as a
transparent plane with a grid on it — which is what the world had — is a
placeholder at any resolution, and at 3.0 m it is a hole in the frame.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Dependants named in the manifest, and the exact call each of them makes.  Every
one returns WORLD coordinates with z already taken from
``world_contract.world_ground_z``; no dependant needs to know the local frame.

    heras_fence_foot     ``foot_sites()``     -> one record per BLOCK.  A block
                                                 serves the joint between two
                                                 panels (two spigots, two holes)
                                                 or one run end.  That is why
                                                 the manifest counts 950 feet
                                                 against 900 panels.
    heras_fence_coupler  ``coupler_sites()``  -> one record per JOINT: the two
                                                 spigot axes it clamps, the
                                                 clamp height, and whether the
                                                 joint is one of the ~8 % with
                                                 no coupler fitted.
    heras_banner_scrim   ``scrim_sites()``    -> the ~35 % of panels that carry
                                                 a banner, each with the four
                                                 corners of the frame opening in
                                                 world space and the eyelet /
                                                 tie points down both uprights.
    cable_tie_offcut     ``tie_sites()``      -> every point on this item where
                                                 a cable tie is or was: scrim
                                                 eyelets, sign fixings, the
                                                 coupler tails.
    paddock_gate         ``run_ends()``       -> where a fence run stops and a
                                                 gate leaf has to close it, with
                                                 the opening width and the two
                                                 jamb panels' spigot axes.

Also public, and used by the test scene and by any assembly pass:

    ``RUNS``              the fence PROGRAMME: named polylines in the circuit
                          design frame plus two runs referred to the transit
                          route, with their gate openings.  Editing this table
                          is how the world's fence line changes; nothing else
                          in this module knows where a fence is.
    ``panel_slots()``     every 3.5 m slot on every run: present or missing,
                          world centre, run direction, outward normal, ground z,
                          lean, width, panel id and geometry seed.
    ``panel_frame(slot)`` -> (R, O) the 3x3 rotation and world origin of a
                          panel's local frame, so a dependant can put its own
                          geometry in panel space.
    ``PANEL_LOCAL``       the local frame's contract: +X along the run, +Y to
                          the MESH side (the frame tube stands proud on -Y,
                          which is the public face), +Z up, origin at the
                          midpoint of the two spigot cuts.
    ``build(...)``        emit.  Collection ``W_Item_HerasFencePanel``, object
                          prefix ``HFP_``.  ONE OBJECT PER PANEL.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library.  Measured by
                          ``item_gate``: ``no_external_assets``.
 2. no real brands        the only lettering-adjacent mark on a panel is the
                          hire depot's sprayed colour band on the top rail and a
                          punched aluminium asset tag.  The band's colour comes
                          from ``build_dressing``'s existing 31-brand book (this
                          module invents nothing); the tag carries a PUNCHED
                          NUMERIC CODE, not a name.
 3. car scale             the 2.005 m car sets the gate openings (every opening
                          is >= 4.0 m so a car and a tug can pass) and the
                          corridor standoff.
 4. z = 0 is one plane    never assumed.  Every panel's base comes from
                          ``C.world_ground_z(x, y)`` and every run is rejected
                          where that function says the ground belongs to the
                          racing surface or the access ribbon.
 5. embed >= 20 mm        THE PANEL DOES NOT STAND ON THE GROUND.  It stands in
                          a concrete foot block, which is ``heras_fence_foot``.
                          The spigot cut sits ``FOOT_LIFT_M`` = 0.030 above the
                          datum, inside the block's cup; this module exports
                          ``foot_sites()`` with the ground z so the block embeds
                          ``C.BASE_EMBED_M``.  The one exception is modelled
                          rather than hidden: on the ~2 % of panels whose block
                          is missing, the spigot is driven INTO the ground and
                          ``slot.foot_missing`` says so.
 6. recentre + TexCoord   every panel's mesh is local to its own frame with
                          |P| < 2.1 m.  The material reads ``TexCoord->Object``
                          plus per-vertex attributes plus a per-OBJECT texture
                          offset, so no two panels share a spangle.
                          ``Geometry->Position`` appears nowhere.
 7. chunk along s         one panel is <= 3.5 m of fence.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names four axes.  Three of them are mesh and the fourth is a
per-object shader seed that is itself driven by mesh state:

  "4.5 % missing"     ``panel_slots`` removes 4.5 % of slots outright, biased
                      toward the middles of runs and never at a run end (a
                      missing end panel would leave the run unsupported).  The
                      gap is real: the two neighbours keep their feet, their
                      couplers hang open, and the run ends get closure panels.

  "panel lean"        every panel leans about its own foot line.  The lean is a
                      transform — and transforms are not variation — so it is
                      not offered as the answer to anything: it is CORRELATED
                      along a run through a random walk with a coupler-stiffness
                      term, so a run reads as a floppy chain rather than as
                      independent noise, and it drives geometry through the
                      mesh belly and the frame sag.

  "mesh dent"         0-3 dents per panel, each an elliptical push in the
                      fabric with its own centre, extent, depth and rim
                      sharpness.  A dent displaces both wire layers AND the
                      weld nuggets between them, and it locally REFINES the
                      wire sampling so the kink at the rim is a kink and not a
                      chord.  On top of that every panel has a unique per-wire
                      per-bay belly, a panel-scale bow and a twist: no two
                      fabrics are the same surface.

  "galvanising bloom" a per-object float that scales the white-rust layer,
                      correlated with the panel's age and with how much of it
                      is in the wet zone.  It is shading — but the places it
                      grows (weld crevices, the spigot bore, the underside of
                      the bottom rail, dent rims where the zinc cracked) are
                      baked per-vertex from the geometry that produced them.

And, beyond the four the manifest names, the population carries genuinely
different OBJECTS, not one object jittered:

    width           3.500 m standard, plus 2.000 m and 1.200 m closure panels
                    at run ends and both sides of every gate opening
    top style       round-top (bend R 0.10-0.13) and square-top (R 0.020 with
                    corner weld beads) — two hire lots in the same fleet
    horizontals     5, 6 or 7 — three fabric lots
    spigots         extended (verticals run 40-70 mm below the bottom rail) or
                    flush — two manufacturers
    damage          snapped verticals (stub top and bottom), verticals cut and
                    bent aside, a bent bottom rail, a folded corner
    asset tag       present on ~55 %, with a punched code that differs

===============================================================================
WHAT WAS MEASURED  (not claimed — measured, 2026-07-29)
===============================================================================
    programme        875 slots on 14 runs, 2939 m of fence line
                     (manifest 900, -2.8 %); 771 standing, 104 gaps.
                     Of the gaps, 4.5 % are the manifest's deliberate removals
                     and the rest are panels the KEEP-OUT rejected: the access
                     ribbon crossing pad_s_w, the showroom footprint crossing
                     int_a/b/c, the pit lane crossing corr_n.
    keep-out         every standing panel passes `placeable`: the ground under
                     it belongs to the declared apron, it is 6.37 m clear of
                     the racing surface edge at worst, and none is inside the
                     access ribbon.
    triangles        14,279,066 over 771 objects (18.5 k/panel; 210 k on the
                     11-19 hero panels, 2.4 k on the 400+ background ones)
    p10 edge         1.55 mm = 1.93 px at 3.0 m / 35 mm  (gate limit 6 px)
    material         21 procedural texture nodes reachable from the output,
                     0 image nodes, 0 external files  (gate needs 6)
    variation        cv_size 0.0969, 258 distinct topologies over 771 objects,
                     measured on INDIVIDUAL OBJECTS — this item is not
                     geometry-nodes instanced, so the gate's `distinct_sources`
                     escape hatch does not apply to it.
    gate             ITEM_ACCEPTED, all four checks.
    NOT verified     the closest a built panel comes to the transit ROUTE
                     CENTRELINE is 7.80 m (measured over 1500 route samples).
                     The manifest films this item at 3.0 m, which a camera
                     4.80 m off the centreline reaches inside a 12.0 m ribbon —
                     but the camera rig is not this module's and the 3.0 m was
                     not independently confirmed.  The detail is built to
                     3.0 m regardless, and the macro camera is at exactly
                     3.0000 m.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/heras_fence_panel.py -- --test \
        --save world/items/heras_fence_panel_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/heras_fence_panel.py -- --selftest
"""

from __future__ import annotations

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
except Exception:                                   # pragma: no cover
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                          # noqa: E402
import itemkit as K                                               # noqa: E402

ITEM = "heras_fence_panel"
COLL = "W_Item_HerasFencePanel"
PFX = "HFP_"
STANDIN_PFX = "HSTD_"


# ==============================================================================
#  1.  THE MANIFEST RECORD IS THE SPECIFICATION
# ==============================================================================

def _manifest_record(item=ITEM):
    path = os.path.join(_ROOT, "docs", "item_manifest.json")
    with open(path, "r") as f:
        man = json.load(f)
    for it in man["items"]:
        if it["id"] == item:
            return it
    raise SystemExit("REFUSING: %r is not in the item manifest." % item)


REC = _manifest_record()
FILMED_AT_M = float(REC["nearest_camera_m"])            # 3.0
LENS_MM = float(REC["lens_at_closest_mm"])              # 35
ONSCREEN_PX_4K = float(REC["onscreen_px_4k"])           # 2160
DECLARED_INSTANCES = int(REC["instances"])              # 900
HERO = bool(REC["hero"])
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_MM / SENSOR_MM) / FILMED_AT_M       # 1244.4
PX_M = 1.0 / PX_PER_M                                            # 0.000804 m
DETAIL_LIMIT_M = 6.0 * PX_M                                      # 0.004823 m


def log(*a):
    print(">>", *a)
    sys.stdout.flush()


# ==============================================================================
#  2.  DETERMINISTIC RANDOMNESS
# ==============================================================================
#
# Every decision in this module is a pure function of integer keys.  Rebuilding
# the world twice must give the same 815 panels with the same 815 dents, or the
# render farm's chunk boundaries become visible seams.

_U32 = np.uint32


def hash01(*keys):
    """FNV-1a over integer keys -> float64 in [0, 1).  Scalars or arrays."""
    arrs = [np.asarray(k) for k in keys]
    shape = np.broadcast(*arrs).shape if len(arrs) > 1 else arrs[0].shape
    h = np.full(shape, _U32(2166136261), dtype=np.uint32)
    with np.errstate(over="ignore"):
        for kk in arrs:
            k = np.rint(kk).astype(np.int64) if kk.dtype.kind == "f" \
                else kk.astype(np.int64)
            k = (k & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ k) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def h01(*keys):
    return float(hash01(*[np.int64(k) for k in keys]))


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * h01(*keys)


def rint(lo, hi, *keys):
    return int(lo + math.floor((hi - lo + 1) * h01(*keys) * 0.9999999))


def chance(p, *keys):
    return h01(*keys) < p


def pick(seq, *keys):
    return seq[min(len(seq) - 1, int(h01(*keys) * len(seq)))]


def _s5(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def n1(x, seed=0):
    """1-D value noise, quintic interpolation, in [0, 1]."""
    x = np.asarray(x, float)
    i = np.floor(x).astype(np.int64)
    f = x - i
    a = hash01(i, np.full_like(i, seed))
    b = hash01(i + 1, np.full_like(i, seed))
    return a + (b - a) * _s5(f)


def fbm1(x, seed=0, oct=4, gain=0.5, lac=2.07):
    x = np.asarray(x, float)
    tot = np.zeros_like(x)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot = tot + amp * n1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def sstep(a, b, x):
    return _s5(np.clip((np.asarray(x, float) - a) / max(1e-9, b - a), 0.0, 1.0))


def unit(v):
    v = np.asarray(v, float)
    n = float(np.linalg.norm(v))
    return v / (n if n > 1e-12 else 1.0)


# ==============================================================================
#  3.  THE PANEL'S LOCAL FRAME  —  the contract every dependant builds on
# ==============================================================================

PANEL_LOCAL = """
+X  along the run, panel width, origin at the panel's own centre
+Y  toward the MESH.  The frame tube's centre plane is y = 0, so the tube
    stands ~20 mm proud on the -Y side: -Y IS THE PUBLIC FACE and it is the
    side the macro camera is on.
+Z  up.  z = 0 is the CUT END OF THE SPIGOTS, i.e. the bottom of the steel,
    which sits FOOT_LIFT_M above world_ground_z inside the foot block's cup.
"""

# --- the section, in metres.  Heras M200-class temporary fence panel. ---------
PANEL_W = 3.500         # nominal, over the outside of the uprights
PANEL_H = 2.000         # nominal, over the outside of the top rail
TUBE_OD = 0.0415        # 41.5 mm o.d. frame tube
TUBE_WALL = 0.0015      # 1.5 mm wall — visible at the open spigot
WIRE_D = 0.0040         # 4.0 mm mesh wire
V_PITCH = 0.100         # 100 mm between vertical wires
BEND_R = 0.110          # round-top corner bend radius
RAIL_BOT_Z = 0.100      # bottom rail AXIS above the spigot cut
SPIGOT_BORE_M = 0.115   # how far down the bore you can see
FOOT_LIFT_M = 0.030     # spigot cut above the ground datum, inside the cup
GATE_MIN_W = 4.20       # every opening passes a car (2.005 m) and a tug

TUBE_R = TUBE_OD * 0.5
WIRE_R = WIRE_D * 0.5

# Where the two wire layers live, relative to the frame tube's centre plane.
# The verticals lie against the tube (tangent, hence weldable to the top and
# bottom rails); the horizontals lie against the verticals.  8 mm of real
# depth = 10 px at the filmed distance, and it is the difference between a
# fabric and a decal.
Y_V = TUBE_R + WIRE_R                 # 0.02275
Y_H = TUBE_R + 3.0 * WIRE_R           # 0.02675


# ==============================================================================
#  4.  ACCUMULATOR AND PRIMITIVES
# ==============================================================================
#
# One Acc per PANEL, so a panel is one object and the gate's per-instance
# statistics are genuinely per instance.

ATTR_F = ("kind", "arc", "ang", "wear", "bloom", "endc", "weld", "dent", "mark")

K_FRAME, K_VWIRE, K_HWIRE, K_WELD, K_BORE, K_TAG, K_RIVET = 0, 1, 2, 3, 4, 5, 6


class Acc(object):
    def __init__(self, name):
        self.name = name
        self._V, self._Q, self._T, self._mq, self._mt = [], [], [], [], []
        self._A = {a: [] for a in ATTR_F}
        self.n = 0
        self.parts = 0

    def add(self, V, quads=None, tris=None, mat=0, **attr):
        V = np.ascontiguousarray(np.asarray(V, np.float64).reshape(-1, 3))
        m = V.shape[0]
        if m == 0:
            return 0
        base = self.n
        self._V.append(V)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            self._Q.append(q)
            self._mq.append(np.full(q.shape[0], mat, np.int32))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self._T.append(t)
            self._mt.append(np.full(t.shape[0], mat, np.int32))
        for a in ATTR_F:
            v = attr.get(a, 0.0)
            if np.ndim(v) == 0:
                self._A[a].append(np.full(m, float(v), np.float32))
            else:
                self._A[a].append(np.broadcast_to(
                    np.asarray(v, np.float32).ravel(), (m,)).astype(np.float32))
        self.n += m
        self.parts += 1
        return base

    def oriented(self, V, quads=None, tris=None, ref=None, **kw):
        """Add faces, flipping any whose normal disagrees with `ref`.

        Winding is the single most tedious bug class in generated geometry and
        a flipped face under a 12.5 deg sun is a black hole in the frame.  For
        a swept tube the outward reference is analytic (the radial direction),
        so there is no reason to guess: compute the normal and compare.
        """
        V = np.asarray(V, float).reshape(-1, 3)
        if quads is not None and len(quads):
            Q = np.asarray(quads, np.int64).reshape(-1, 4).copy()
            a, b, c = V[Q[:, 0]], V[Q[:, 1]], V[Q[:, 2]]
            nrm = np.cross(b - a, c - a)
            bad = np.einsum("ij,ij->i", nrm, np.asarray(ref[0], float)) < 0.0
            Q[bad] = Q[bad][:, ::-1]
        else:
            Q = None
        if tris is not None and len(tris):
            T = np.asarray(tris, np.int64).reshape(-1, 3).copy()
            a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
            nrm = np.cross(b - a, c - a)
            bad = np.einsum("ij,ij->i", nrm, np.asarray(ref[1], float)) < 0.0
            T[bad] = T[bad][:, ::-1]
        else:
            T = None
        return self.add(V, quads=Q, tris=T, **kw)

    def solid(self, V, quads=None, tris=None, **kw):
        """Add a CLOSED solid, orienting every face outward by signed volume."""
        V = np.asarray(V, np.float64).reshape(-1, 3)
        Q = None if quads is None else np.asarray(quads, np.int64).reshape(-1, 4)
        T = None if tris is None else np.asarray(tris, np.int64).reshape(-1, 3)
        vol = 0.0
        if T is not None and len(T):
            a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
            vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if Q is not None and len(Q):
            for (i, j, k) in ((0, 1, 2), (0, 2, 3)):
                a, b, c = V[Q[:, i]], V[Q[:, j]], V[Q[:, k]]
                vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if vol < 0.0:
            if Q is not None and len(Q):
                Q = Q[:, ::-1].copy()
            if T is not None and len(T):
                T = T[:, ::-1].copy()
        return self.add(V, quads=Q, tris=T, **kw)

    def build(self, coll, mats, R, O, name=None):
        V = np.concatenate(self._V) if self._V else np.zeros((0, 3))
        Q = np.concatenate(self._Q) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T) if self._T else np.zeros((0, 3), np.int64)
        mq = np.concatenate(self._mq) if self._mq else np.zeros(0, np.int32)
        mt = np.concatenate(self._mt) if self._mt else np.zeros(0, np.int32)
        nv, nq, nt = V.shape[0], Q.shape[0], T.shape[0]
        nf = nq + nt
        me = bpy.data.meshes.new(name or self.name)
        me.vertices.add(nv)
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        me.loops.add(nq * 4 + nt * 3)
        loops = np.empty(nq * 4 + nt * 3, np.int32)
        loops[:nq * 4] = Q.astype(np.int32).ravel()
        loops[nq * 4:] = T.astype(np.int32).ravel()
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(nf)
        ls = np.empty(nf, np.int32)
        lt = np.empty(nf, np.int32)
        ls[:nq] = np.arange(nq, dtype=np.int32) * 4
        lt[:nq] = 4
        ls[nq:] = nq * 4 + np.arange(nt, dtype=np.int32) * 3
        lt[nq:] = 3
        me.polygons.foreach_set("loop_start", ls)
        me.polygons.foreach_set("loop_total", lt)
        mi = np.empty(nf, np.int32)
        mi[:nq] = mq
        mi[nq:] = mt
        me.polygons.foreach_set("material_index", mi)
        me.update(calc_edges=True)
        for a in ATTR_F:
            at = me.attributes.new(PFX.lower() + a, "FLOAT", "POINT")
            at.data.foreach_set("value", np.concatenate(self._A[a]))
        me.validate(verbose=False)
        shade_by_angle(me, 32.0)
        ob = bpy.data.objects.new(name or self.name, me)
        for m in mats:
            ob.data.materials.append(m)
        coll.objects.link(ob)
        place(ob, R, O)
        return ob, dict(verts=nv, quads=nq, tris=nt,
                        triangles=nq * 2 + nt, parts=self.parts)


def place(ob, R, O):
    from mathutils import Matrix, Vector
    M = Matrix(((R[0][0], R[1][0], R[2][0], O[0]),
                (R[0][1], R[1][1], R[2][1], O[1]),
                (R[0][2], R[1][2], R[2][2], O[2]),
                (0.0, 0.0, 0.0, 1.0)))
    ob.matrix_world = M
    return ob


def shade_by_angle(me, deg=32.0):
    """Smooth everywhere except across a real arris.

    A drawn wire and a rolled tube are tangent-continuous all the way round, so
    flat-shading them turns an 8-facet wire into 8 visible bands 1.5 mm wide —
    2 px at the filmed distance.  The genuinely sharp edges are the sheared wire
    ends, the spigot rim and the tag, and those stay sharp.  Done in numpy
    against the `sharp_edge` attribute because `shade_auto_smooth` needs a
    VIEW_3D context and cannot run headless.
    """
    npoly, nloop, nedge = len(me.polygons), len(me.loops), len(me.edges)
    if not nedge or not npoly:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))
    fn = np.empty(npoly * 3, np.float32)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32); me.loops.foreach_get("vertex_index", lv)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64)
    b = lv[nxt].astype(np.int64)
    nvert = np.int64(len(me.vertices))
    key = np.minimum(a, b) * nvert + np.maximum(a, b)
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)
    order = np.argsort(key, kind="stable")
    ks, fs = key[order], face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    f0 = np.zeros(ng, np.int64)
    f1 = np.full(ng, -1, np.int64)
    np.copyto(f0, fs[np.flatnonzero(first)])
    second = np.flatnonzero(~first)
    if len(second):
        f1[grp[second]] = fs[second]
    dot = np.ones(ng)
    two = f1 >= 0
    if two.any():
        dot[two] = np.einsum("ij,ij->i", fn[f0[two]], fn[f1[two]])
    ang = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    sharp_key = ks[np.flatnonzero(first)][ang > deg]
    ev = np.empty(nedge * 2, np.int32)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(nedge, 2).astype(np.int64)
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * nvert
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _grid_quads(n, m, close_m=False):
    mm = m if close_m else m - 1
    i = np.arange(n - 1)[:, None]
    j = np.arange(mm)[None, :]
    j1 = (j + 1) % m
    return np.stack([(i * m + j).ravel(), (i * m + j1).ravel(),
                     ((i + 1) * m + j1).ravel(), ((i + 1) * m + j).ravel()], 1)


def _fan(centre_idx, ring, reverse=False):
    b = np.asarray(ring, np.int64)
    a = np.full(len(b), centre_idx, np.int64)
    c = np.roll(b, -1)
    return np.stack([a, c, b], 1) if reverse else np.stack([a, b, c], 1)


def frames_along(path, up_hint=(0.0, 0.0, 1.0)):
    """Parallel-transport frames.  (T, N, B) with B = T x N, right-handed."""
    P = np.asarray(path, float)
    n = P.shape[0]
    T = np.zeros((n, 3))
    T[:-1] = P[1:] - P[:-1]
    T[-1] = T[-2] if n > 1 else np.array([0.0, 0.0, 1.0])
    if n > 2:
        T[1:-1] = P[2:] - P[:-2]
    T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    N = np.zeros((n, 3))
    up = unit(up_hint)
    r = np.cross(up, T[0])
    if np.linalg.norm(r) < 1e-6:
        r = np.cross(np.array([1.0, 0.0, 0.0]), T[0])
    N[0] = unit(r)
    for i in range(1, n):
        v = N[i - 1] - T[i] * float(np.dot(N[i - 1], T[i]))
        if np.linalg.norm(v) < 1e-9:
            v = np.cross(up, T[i])
        N[i] = unit(v)
    B = np.cross(T, N)
    return T, N, B


def tube_along(acc, path, r, nsides, mat=0, caps=(True, True), phase=0.0,
               up_hint=(0.0, 0.0, 1.0), arc0=0.0, **attrs):
    """Sweep a circular tube along a polyline.  Returns a dict of end data.

    `arc` and `ang` are baked per vertex: arc length along the member and the
    angle around it, normalised.  Every shader layer that has to follow a wire
    — the drawing striations, the rust run off a cut end, the bloom on the
    upper surface where water sits — reads those two and nothing else.
    """
    P = np.asarray(path, float).reshape(-1, 3)
    n = P.shape[0]
    if n < 2:
        return None
    T, N, B = frames_along(P, up_hint)
    ang = np.arange(nsides) * (2.0 * math.pi / nsides) + phase
    ca, sa = np.cos(ang), np.sin(ang)
    rr = np.broadcast_to(np.asarray(r, float).reshape(-1), (n,))
    RAD = (ca[None, :, None] * N[:, None, :] + sa[None, :, None] * B[:, None, :])
    V = P[:, None, :] + rr[:, None, None] * RAD
    seg = np.zeros(n)
    seg[1:] = np.cumsum(np.linalg.norm(P[1:] - P[:-1], axis=1))
    arc = np.broadcast_to((seg + arc0)[:, None], (n, nsides))
    aang = np.broadcast_to((ang / (2.0 * math.pi))[None, :], (n, nsides))
    kw = dict(attrs)
    for k, v in list(kw.items()):
        if np.ndim(v) == 1 and len(v) == n:
            kw[k] = np.broadcast_to(np.asarray(v)[:, None], (n, nsides)).ravel()
    Vf = V.reshape(-1, 3)
    Q = _grid_quads(n, nsides, close_m=True)
    refq = RAD[:-1, :, :].reshape(-1, 3)
    kw.pop("arc", None)
    kw.pop("ang", None)
    acc.oriented(Vf, quads=Q, ref=(refq, None), mat=mat,
                 arc=arc.ravel(), ang=aang.ravel(), **kw)
    out = dict(P0=P[0], P1=P[-1], T0=T[0], T1=T[-1], N0=N[0], B0=B[0],
               N1=N[-1], B1=B[-1], arc_end=float(seg[-1] + arc0))
    # flat caps
    for (do, i, sgn) in ((caps[0], 0, -1.0), (caps[1], n - 1, +1.0)):
        if not do:
            continue
        ring = V[i]
        cV = np.concatenate([ring, P[i][None, :]])
        tri = _fan(nsides, np.arange(nsides))
        ref = np.broadcast_to((sgn * T[i])[None, :], (nsides, 3))
        ca_kw = {k: (v if np.ndim(v) == 0 else 0.0) for k, v in attrs.items()
                 if k not in ("arc", "ang")}
        acc.oriented(cV, tris=tri, ref=(None, ref), mat=mat,
                     arc=float(seg[i] + arc0), ang=0.0, **ca_kw)
    return out


def cup_end(acc, P, T, N, Bv, r_out, wall, depth, nsides, mat=0, plug_t=1.0,
            **attrs):
    """An OPEN tube end: rim annulus, bore wall, and the plug of dirt in it.

    At 1244 px/m the 1.5 mm wall is 1.9 px and the bore is 46 px across.  A
    capped tube end reads as a solid bar; this is the single detail that says
    "hollow section" at the foot of every panel in the frame.
    """
    r_in = r_out - wall
    ang = np.arange(nsides) * (2.0 * math.pi / nsides)
    RAD = (np.cos(ang)[:, None] * N[None, :] + np.sin(ang)[:, None] * Bv[None, :])
    outer = P[None, :] + r_out * RAD
    inner0 = P[None, :] + r_in * RAD
    zin = P + T * depth
    inner1 = zin[None, :] + r_in * RAD
    plug = P + T * (depth * plug_t)
    plug_ring = plug[None, :] + (r_in * 0.985) * RAD
    V = np.concatenate([outer, inner0, inner1, plug_ring, plug[None, :]])
    b_out, b_i0, b_i1, b_pr, b_pc = 0, nsides, 2 * nsides, 3 * nsides, 4 * nsides
    j = np.arange(nsides)
    j1 = (j + 1) % nsides
    ann = np.stack([b_out + j, b_out + j1, b_i0 + j1, b_i0 + j], 1)
    bore = np.stack([b_i0 + j, b_i0 + j1, b_i1 + j1, b_i1 + j], 1)
    lip = np.stack([b_i1 + j, b_i1 + j1, b_pr + j1, b_pr + j], 1)
    ref_ann = np.broadcast_to((-T)[None, :], (nsides, 3))
    ref_bore = -RAD
    ref_lip = np.broadcast_to((-T)[None, :], (nsides, 3))
    tri = _fan(b_pc, b_pr + j)
    ref_tri = np.broadcast_to((-T)[None, :], (nsides, 3))
    Q = np.concatenate([ann, bore, lip])
    refq = np.concatenate([ref_ann, ref_bore, ref_lip])
    kwv = {k: v for k, v in attrs.items()}
    acc.oriented(V, quads=Q, tris=tri, ref=(refq, ref_tri), mat=mat, **kwv)


def _icosa():
    t = (1.0 + 5.0 ** 0.5) / 2.0
    V = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
                  (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                  (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    F = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
                  (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
                  (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                  (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)])
    return V / np.linalg.norm(V, axis=1, keepdims=True), F


def icosphere(sub=1):
    V, F = _icosa()
    for _ in range(sub):
        Vl = [tuple(v) for v in V]
        idx = {tuple(np.round(v, 9)): i for i, v in enumerate(V)}
        nf = []
        for (a, b, c) in F:
            mid = []
            for (i, j) in ((a, b), (b, c), (c, a)):
                p = (V[i] + V[j]) * 0.5
                p = p / np.linalg.norm(p)
                key = tuple(np.round(p, 9))
                if key not in idx:
                    idx[key] = len(Vl)
                    Vl.append(tuple(p))
                mid.append(idx[key])
            ab, bc, ca = mid
            nf += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        V = np.array(Vl)
        F = np.array(nf)
    return V, F


_ICO = {s: icosphere(s) for s in (0, 1)}


def blob(acc, ctr, ex, ey, ez, sub=1, mat=0, warp=None, **attrs):
    """An ellipsoidal solid — the weld nugget, and nothing else."""
    V0, F = _ICO[sub]
    V = (np.asarray(ctr, float)[None, :]
         + V0[:, 0:1] * np.asarray(ex, float)[None, :]
         + V0[:, 1:2] * np.asarray(ey, float)[None, :]
         + V0[:, 2:3] * np.asarray(ez, float)[None, :])
    if warp is not None:
        V = V + warp(V0)
    return acc.solid(V, tris=F, mat=mat, **attrs)


# ==============================================================================
#  5.  THE PANEL SPEC  —  every panel is a different object, decided here
# ==============================================================================
#
# "i dont want repeat stuff aka one tree spammed 100 times"
#
# A hire fleet IS a set of nominally identical panels; what makes a real fence
# line read is that every one of them has had a different life.  So the spec
# below is not "jitter": it is a manufacturing lot plus a service history, and
# both of them change the MESH.  Two panels differ in width, in corner style,
# in how many horizontal wires the fabric has, in which verticals have been cut
# out, in where they have been hit and how hard, and in whether the tag is
# still on.  Nothing here is expressed as a transform.


class Dent(object):
    __slots__ = ("cx", "cz", "rx", "rz", "depth", "p")

    def __init__(self, cx, cz, rx, rz, depth, p):
        self.cx, self.cz, self.rx, self.rz = cx, cz, rx, rz
        self.depth, self.p = depth, p


class Spec(object):
    """Everything about one panel's geometry, from one integer seed."""

    def __init__(self, seed, width=PANEL_W, lod=3):
        s = int(seed)
        self.seed = s
        self.lod = int(lod)

        # ---- manufacturing lot ------------------------------------------
        # Three hire lots in the fleet.  A lot decides the tube gauge, the
        # corner style and the fabric, and those are topology, not tint.
        self.lot = rint(0, 2, s, 11)
        self.round_top = self.lot != 1                      # lot 1 is square-top
        self.bend_r = (rnd(0.098, 0.128, s, 12) if self.round_top
                       else rnd(0.018, 0.026, s, 12))
        self.tube_r = (0.0415 if self.lot == 0 else
                       (0.0400 if self.lot == 1 else 0.0425)) * 0.5
        self.tube_r *= rnd(0.996, 1.004, s, 13)             # rolling tolerance
        self.wall = TUBE_WALL * rnd(0.92, 1.10, s, 14)
        self.wire_r = WIRE_R * rnd(0.955, 1.045, s, 15)
        self.n_h = (5, 6, 6, 6, 7)[rint(0, 4, s, 16)]
        self.v_pitch = V_PITCH * rnd(0.975, 1.028, s, 17)
        # lot 2 leaves the uprights long below the bottom rail; lot 0 and 1
        # cut them nearly flush.  Two different objects at the foot.
        self.spigot = (rnd(0.042, 0.072, s, 18) if self.lot == 2
                       else rnd(0.004, 0.016, s, 18))
        self.rail_bot = RAIL_BOT_Z * rnd(0.90, 1.12, s, 19)

        # ---- nominal size, with a real rolling tolerance -----------------
        self.w = float(width) * rnd(0.9975, 1.0025, s, 20)
        self.h = PANEL_H * rnd(0.997, 1.003, s, 21)

        # ---- service history --------------------------------------------
        self.age = clamp01(rnd(0.10, 1.00, s, 22) ** 0.8)
        self.bloom = clamp01(rnd(0.05, 1.00, s, 23) * (0.35 + 0.85 * self.age))
        self.mud = clamp01(rnd(0.0, 1.0, s, 24) ** 1.5)
        self.fresh = 1.0 - self.age

        # dents.  A 3.5 m panel that has been in a paddock for a season has
        # been reversed into, leant on and had a forklift tine through it.
        nd = (0, 0, 1, 1, 1, 2, 2, 3)[rint(0, 7, s, 30)]
        self.dents = []
        for k in range(nd):
            self.dents.append(Dent(
                cx=rnd(-self.w * 0.42, self.w * 0.42, s, 31, k),
                cz=rnd(0.22, self.h * 0.92, s, 32, k),
                rx=rnd(0.10, 0.62, s, 33, k),
                rz=rnd(0.09, 0.50, s, 34, k),
                depth=rnd(0.012, 0.085, s, 35, k) * (1.0 if chance(0.72, s, 36, k)
                                                     else -1.0),
                p=rnd(0.85, 2.4, s, 37, k)))

        # panel-scale bow of the fabric and a twist of the whole frame
        self.bow = rnd(-0.020, 0.026, s, 40) * (0.35 + self.age)
        self.twist = rnd(-0.016, 0.016, s, 41) * (0.35 + self.age)
        self.rail_sag = rnd(-0.014, 0.008, s, 42) * (0.3 + self.age)
        self.frame_bow = rnd(-0.010, 0.010, s, 43) * (0.3 + self.age)

        # cut / snapped verticals.  A real fence line has these and a rendered
        # one never does.  `cut_v` are gone between two horizontals (stubs left
        # welded top and bottom); `bent_v` are cut once and levered aside.
        self.cut_v, self.bent_v = [], []
        if chance(0.16, s, 50):
            for k in range(rint(1, 3, s, 51)):
                self.cut_v.append(rint(0, 60, s, 52, k))
        if chance(0.09, s, 55):
            for k in range(rint(1, 2, s, 56)):
                self.bent_v.append(rint(0, 60, s, 57, k))

        # a folded bottom corner — the classic forklift signature
        self.fold = (rnd(0.10, 0.26, s, 60) if chance(0.07, s, 61) else 0.0)
        self.fold_side = 1 if chance(0.5, s, 62) else -1

        # the asset tag, and the depot's sprayed colour band on the top rail
        self.tag = chance(0.55, s, 70)
        self.tag_z = rnd(1.15, 1.62, s, 71)
        self.tag_code = int(h01(s, 72) * 1023) | 0x11
        self.band = chance(0.42, s, 75)
        self.band_x = rnd(-0.30, 0.30, s, 76)
        self.band_w = rnd(0.075, 0.155, s, 77)

        # ---- derived geometry -------------------------------------------
        self.xR = self.w * 0.5 - self.tube_r
        self.z_top = self.h - self.tube_r                 # top rail axis
        self.z_bot = self.rail_bot                        # bottom rail axis
        self.z_spig = -self.spigot                        # spigot cut (local z)
        # the mesh field
        self.mx = self.xR - rnd(0.038, 0.052, s, 80)
        n_v = int(round(2.0 * self.mx / self.v_pitch)) + 1
        self.n_v = max(6, n_v)
        self.xv = np.linspace(-self.mx, self.mx, self.n_v)
        self.hz = np.linspace(self.z_bot, self.z_top, self.n_h + 2)[1:-1]
        self.zc = np.concatenate([[self.z_bot], self.hz, [self.z_top]])
        # per-wire, per-bay belly.  This is what makes a fabric a fabric: each
        # bay of each wire bows out of plane by its own few millimetres with
        # its own sign, which at 1244 px/m is 2-5 px of relief repeated 245
        # times across the panel and never twice the same.
        self.belly = (hash01(np.arange(self.n_v)[:, None],
                             np.arange(self.n_h + 1)[None, :],
                             np.full((self.n_v, self.n_h + 1), s)) - 0.5) \
            * (0.0072 * (0.45 + 0.9 * self.age))
        self.wander = s * 7 + 3

    # -------------------------------------------------------------- the fabric
    def yfield(self, X, Z):
        """Out-of-plane displacement of the fabric at (X, Z), metres.

        Shared by both wire layers and by the weld nuggets between them, so a
        nugget cannot float off its crossing when a dent moves the wires.
        """
        X = np.asarray(X, float)
        Z = np.asarray(Z, float)
        tx = np.clip((X + self.mx) / (2.0 * self.mx), 0.0, 1.0)
        tz = np.clip((Z - self.z_bot) / (self.z_top - self.z_bot), 0.0, 1.0)
        y = self.bow * np.sin(np.pi * tx) * np.sin(np.pi * tz)
        y = y + self.twist * (X / max(self.mx, 1e-6)) * (tz - 0.5) * 2.0
        for d in self.dents:
            r = np.sqrt(((X - d.cx) / d.rx) ** 2 + ((Z - d.cz) / d.rz) ** 2)
            m = r < 1.0
            y = y + np.where(m, d.depth * (1.0 - np.minimum(r, 1.0) ** 2) ** d.p,
                             0.0)
        return y

    def belly_at(self, iv, Z):
        """Bay belly for vertical wire `iv` at height Z.  Zero at every weld."""
        Z = np.asarray(Z, float)
        k = np.clip(np.searchsorted(self.zc, Z, side="right") - 1,
                    0, len(self.zc) - 2)
        t = (Z - self.zc[k]) / np.maximum(self.zc[k + 1] - self.zc[k], 1e-9)
        return self.belly[iv, k] * np.sin(np.pi * np.clip(t, 0.0, 1.0))

    def top_z_at(self, x):
        """Underside of the top rail's AXIS at panel x — follows the bend."""
        x = np.asarray(x, float)
        xb = self.xR - self.bend_r
        z = np.full(x.shape, self.z_top)
        m = np.abs(x) > xb
        if m.any():
            dx = np.abs(x[m]) - xb
            z[m] = (self.z_top - self.bend_r
                    + np.sqrt(np.maximum(self.bend_r ** 2 - dx ** 2, 0.0)))
        return z


# --- level of detail ----------------------------------------------------------
#
# Four grades, chosen by distance to the nearest camera anchor.  The hero grade
# is built to the pixel table in the docstring; the others fall away along the
# axes the eye stops resolving first — the number of facets round a wire goes
# before the wire does, and the weld nuggets go before the fabric does.
#
#            frame    frame  wire   wire   nugget    dent
#            sides    step   sides  step   subdiv    refine
LOD = {
    3: dict(fs=28, fstep=0.016, ws=8, wstep=0.020, nug=1, dref=0.005),
    2: dict(fs=12, fstep=0.080, ws=6, wstep=0.120, nug=0, dref=0.032),
    1: dict(fs=10, fstep=0.130, ws=5, wstep=0.260, nug=-1, dref=0.0),
    0: dict(fs=8, fstep=0.320, ws=4, wstep=0.620, nug=-1, dref=0.0),
}


def _stations(a, b, step, refine=(), rad=0.05, fine=0.006, ends=0.010):
    """Positions across [a, b], denser at the ends and near `refine`."""
    n = max(2, int(round(abs(b - a) / max(step, 1e-6))) + 1)
    out = [np.linspace(a, b, n)]
    for u in refine:
        if fine > 0 and a - rad < u < b + rad:
            out.append(np.arange(max(a, u - rad), min(b, u + rad) + 1e-9, fine))
    if ends > 0:
        out.append(np.linspace(a, min(a + ends, b), 3))
        out.append(np.linspace(max(b - ends, a), b, 3))
    x = np.unique(np.concatenate(out))
    keep = [x[0]]
    for v in x[1:]:
        if v - keep[-1] > 3.5e-4:
            keep.append(v)
    keep[-1] = b
    return np.array(keep)


# ==============================================================================
#  6.  THE PANEL, AS GEOMETRY
# ==============================================================================

WELD_FLAT = 0.00060      # how far a resistance weld presses the two wires
                         # together.  0.6 mm each side = a real 0.8 px waist at
                         # every one of the 210 crossings, and it is why the
                         # fabric reads as welded rather than as two grids.


def _fold_disp(sp, X, Z):
    """The folded bottom corner — a forklift tine through the fabric."""
    if sp.fold <= 0.0:
        return 0.0
    x0 = sp.fold_side * sp.mx
    dx = np.abs(np.asarray(X, float) - x0) / sp.fold
    dz = np.clip(np.asarray(Z, float) / (sp.fold * 1.6), 0.0, 3.0)
    w = np.clip(1.0 - dx, 0.0, 1.0) * np.clip(1.0 - dz, 0.0, 1.0)
    return -sp.fold * 0.55 * w * w


def _wander(sp, t, k, amp=0.00042):
    return (n1(np.asarray(t, float) * 11.0 + k * 3.7, sp.wander) - 0.5) * 2.0 * amp


def _weld_flat_v(sp, Z):
    Z = np.asarray(Z, float)
    out = np.zeros_like(Z)
    for hz in sp.hz:
        out = out + WELD_FLAT * np.exp(-((Z - hz) / 0.0052) ** 2)
    return out


def _weld_flat_h(sp, X):
    X = np.asarray(X, float)
    out = np.zeros_like(X)
    d = np.abs(X[:, None] - sp.xv[None, :])
    out = WELD_FLAT * np.exp(-(d / 0.0052) ** 2).sum(axis=1)
    return out


def _frame_y(sp, X, Z):
    """Out-of-plane bow of the FRAME.  Small: a tube frame is stiff."""
    tx = np.clip((np.asarray(X, float) + sp.xR) / (2.0 * sp.xR), 0.0, 1.0)
    tz = np.clip((np.asarray(Z, float) - sp.z_spig)
                 / max(sp.z_top - sp.z_spig, 1e-6), 0.0, 1.0)
    return sp.frame_bow * np.sin(np.pi * tx) * np.sin(np.pi * tz)


def _frame_path(sp, step):
    """(x, z) polyline of the frame U: up the left, over the top, down the right."""
    zb = sp.z_top - sp.bend_r
    xb = sp.xR - sp.bend_r
    up_l = _stations(sp.z_spig, zb, step, ends=0.006)
    seg = [np.stack([np.full_like(up_l, -sp.xR), up_l], 1)]
    na = max(4, int(round((math.pi * 0.5 * sp.bend_r) / min(step, 0.010))) + 1)
    a = np.linspace(math.pi, math.pi * 0.5, na)[1:]
    seg.append(np.stack([-xb + sp.bend_r * np.cos(a),
                         zb + sp.bend_r * np.sin(a)], 1))
    top = _stations(-xb, xb, step, ends=0.006)[1:-1]
    seg.append(np.stack([top, np.full_like(top, sp.z_top)], 1))
    a = np.linspace(math.pi * 0.5, 0.0, na)
    seg.append(np.stack([xb + sp.bend_r * np.cos(a),
                         zb + sp.bend_r * np.sin(a)], 1))
    down_r = _stations(zb, sp.z_spig, step, ends=0.006)[1:]
    seg.append(np.stack([np.full_like(down_r, sp.xR), down_r], 1))
    return np.concatenate(seg)


def build_frame(acc, sp, L, mat=0):
    """The bent tube frame, the bottom rail, the corner welds and the bores."""
    XZ = _frame_path(sp, L["fstep"])
    X, Z = XZ[:, 0], XZ[:, 1]
    Y = _frame_y(sp, X, Z)
    P = np.stack([X, Y, Z], 1)
    # wear: the outer arris of the top rail and the two uprights at carrying
    # height are what a hand and a stack rub bare.
    carry = np.exp(-((Z - 1.05) / 0.42) ** 2)
    wear = clamp01(0.22 + 0.55 * np.clip((Z - sp.z_top + 0.16) / 0.16, 0, 1)
                   + 0.45 * carry * (np.abs(X) > sp.xR - 0.02))
    bl = np.full_like(Z, sp.bloom) * (0.55 + 0.75 * np.exp(-Z / 0.55))
    mark = np.zeros_like(Z)
    if sp.band:
        mark = ((np.abs(X - sp.band_x * sp.xR) < sp.band_w)
                & (Z > sp.z_top - 0.02)).astype(float)
    tube_along(acc, P, sp.tube_r, L["fs"], mat=mat, caps=(False, False),
               up_hint=(0.0, 1.0, 0.0),
               kind=float(K_FRAME), wear=wear, bloom=bl, mark=mark,
               endc=np.zeros_like(Z), weld=np.zeros_like(Z),
               dent=np.zeros_like(Z))

    # ---- the two open spigots ------------------------------------------
    # Their bores are the darkest thing in the frame and the reason the foot of
    # the fence reads as steel rather than as a stick.
    for sgn in (-1.0, +1.0):
        p = np.array([sgn * sp.xR, _frame_y(sp, sgn * sp.xR, sp.z_spig),
                      sp.z_spig])
        cup_end(acc, p, np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0]),
                np.array([0.0, 1.0, 0.0]), sp.tube_r, sp.wall,
                min(SPIGOT_BORE_M, sp.z_bot - sp.z_spig + 0.02), L["fs"],
                mat=mat, plug_t=rnd(0.45, 0.97, sp.seed, 90, int(sgn)),
                kind=float(K_BORE), endc=1.0, wear=0.85,
                bloom=min(1.0, sp.bloom * 1.6 + 0.25), weld=0.0, dent=0.0,
                mark=0.0, arc=0.0, ang=0.0)

    # ---- the bottom rail, welded between the uprights -------------------
    xs = _stations(-sp.xR - 0.004, sp.xR + 0.004, L["fstep"], ends=0.004)
    t = (xs + sp.xR) / (2.0 * sp.xR)
    zr = sp.z_bot + sp.rail_sag * np.sin(np.pi * np.clip(t, 0, 1))
    yr = _frame_y(sp, xs, zr)
    Pr = np.stack([xs, yr, zr], 1)
    tube_along(acc, Pr, sp.tube_r, L["fs"], mat=mat, caps=(True, True),
               up_hint=(0.0, 1.0, 0.0), kind=float(K_FRAME),
               wear=np.full_like(xs, 0.35),
               bloom=np.full_like(xs, min(1.0, sp.bloom * 1.45 + 0.20)),
               endc=np.zeros_like(xs), weld=np.zeros_like(xs),
               dent=np.zeros_like(xs), mark=np.zeros_like(xs))

    # ---- weld beads: the rail's two T-joints, and the corners on a
    #      square-top panel where the frame is four tubes, not one ---------
    if L["nug"] >= 0:
        r = sp.tube_r
        for sgn in (-1.0, +1.0):
            c = np.array([sgn * (sp.xR - r * 0.55), 0.0, sp.z_bot])
            for k, ay in enumerate((-1.0, 1.0)):
                blob(acc, c + np.array([0.0, ay * r * 0.72, 0.0]),
                     (r * 0.62, 0, 0), (0, r * 0.30, 0), (0, 0, r * 0.95),
                     sub=L["nug"], mat=mat, kind=float(K_WELD), weld=1.0,
                     wear=0.15, bloom=min(1.0, sp.bloom * 1.7 + 0.3),
                     endc=0.25, dent=0.0, mark=0.0, arc=0.0, ang=0.0)
        if not sp.round_top:
            for sgn in (-1.0, +1.0):
                c = np.array([sgn * (sp.xR - sp.bend_r * 0.4), 0.0,
                              sp.z_top - sp.bend_r * 0.4])
                blob(acc, c, (r * 0.85, 0, 0), (0, r * 1.12, 0), (0, 0, r * 0.85),
                     sub=L["nug"], mat=mat, kind=float(K_WELD), weld=1.0,
                     wear=0.2, bloom=min(1.0, sp.bloom * 1.6 + 0.3),
                     endc=0.2, dent=0.0, mark=0.0, arc=0.0, ang=0.0)


def _dent_at(sp, X, Z):
    """|displacement| from the dents alone, normalised — drives the shader."""
    X = np.asarray(X, float)
    Z = np.asarray(Z, float)
    out = np.zeros(np.broadcast(X, Z).shape)
    for d in sp.dents:
        r = np.sqrt(((X - d.cx) / d.rx) ** 2 + ((Z - d.cz) / d.rz) ** 2)
        out = np.maximum(out, np.where(r < 1.0,
                                       (1.0 - np.minimum(r, 1.0) ** 2) ** d.p, 0.0))
    return out


def _dent_z_refine(sp):
    zs = []
    for d in sp.dents:
        zs.append(np.linspace(max(0.0, d.cz - d.rz), d.cz + d.rz, 9))
    return np.concatenate(zs) if zs else np.zeros(0)


def build_fabric(acc, sp, L, mat=1, matw=2):
    """35 verticals, 6 horizontals, and a weld nugget at every crossing."""
    dref = L["dref"]
    dentz = _dent_z_refine(sp)
    cut = set(i % sp.n_v for i in sp.cut_v)
    bent = set(i % sp.n_v for i in sp.bent_v)
    ztop_all = sp.top_z_at(sp.xv)

    # ------------------------------------------------------- vertical wires
    for iv in range(sp.n_v):
        x = float(sp.xv[iv])
        z0 = sp.z_bot - rnd(0.006, 0.017, sp.seed, 100, iv)
        z1 = float(ztop_all[iv]) + rnd(0.001, 0.013, sp.seed, 101, iv)
        # Refining every wire around every crossing and every dent rim is what
        # the hero grade is for; at 25 m and beyond a 0.6 mm weld waist is a
        # tenth of a pixel and paying 8x the triangles for it is how a world
        # runs out of memory.  dref == 0 turns the refinement off entirely.
        ref = (list(sp.hz) + list(dentz)) if dref > 0 else []
        spans = [(z0, z1, 0.0, 0.0)]
        if iv in cut:
            k = rint(0, max(0, sp.n_h - 1), sp.seed, 102, iv)
            zc0 = float(sp.zc[k]) + rnd(0.0, 0.02, sp.seed, 103, iv)
            zc1 = float(sp.zc[min(k + 2, len(sp.zc) - 1)]) \
                - rnd(0.0, 0.02, sp.seed, 104, iv)
            if zc1 - zc0 > 0.05:
                spans = [(z0, zc0, 0.0, 1.0), (zc1, z1, 1.0, 0.0)]
        lever = 0.0
        if iv in bent:
            lever = rnd(0.03, 0.11, sp.seed, 105, iv) * (1 if chance(
                0.5, sp.seed, 106, iv) else -1)
            zk = float(pick(list(sp.zc[:-1]), sp.seed, 107, iv))
            spans = [(z0, z1, 0.0, 1.0)]
        for (za, zb, e0, e1) in spans:
            if zb - za < 0.02:
                continue
            Zs = _stations(za, zb, L["wstep"], refine=ref,
                           rad=(dref * 2.2 if dref > 0 else 0.0),
                           fine=(dref if dref > 0 else 0.0), ends=0.006)
            Y = (Y_V + sp.yfield(x, Zs) + sp.belly_at(iv, Zs)
                 + _weld_flat_v(sp, Zs) + _fold_disp(sp, x, Zs)
                 + _wander(sp, Zs, iv))
            Xs = x + _wander(sp, Zs, iv + 500, 0.00035)
            if lever != 0.0:
                w = clamp01((Zs - zk) / 0.25)
                Y = Y + lever * w * w
                Xs = Xs + lever * 0.35 * w * w
            P = np.stack([Xs, Y, Zs], 1)
            end = (np.exp(-((Zs - za) / 0.012) ** 2) * (0.35 + 0.65 * e0)
                   + np.exp(-((Zs - zb) / 0.012) ** 2) * (0.35 + 0.65 * e1))
            dn = _dent_at(sp, Xs, Zs)
            wl = np.zeros_like(Zs)
            for hz in sp.hz:
                wl = np.maximum(wl, np.exp(-((Zs - hz) / 0.010) ** 2))
            tube_along(acc, P, sp.wire_r, L["ws"], mat=mat, caps=(True, True),
                       up_hint=(0.0, 1.0, 0.0), kind=float(K_VWIRE),
                       wear=clamp01(0.10 + 0.5 * dn),
                       bloom=clamp01(sp.bloom * (0.6 + 0.9 * np.exp(-Zs / 0.5))
                                     + 0.35 * wl + 0.30 * dn),
                       endc=clamp01(end), weld=wl, dent=dn,
                       mark=np.zeros_like(Zs))

    # ----------------------------------------------------- horizontal wires
    for jh in range(sp.n_h):
        z = float(sp.hz[jh])
        Xs = _stations(-sp.xR, sp.xR, L["wstep"],
                       refine=(list(sp.xv) if dref > 0 else []),
                       rad=(dref * 2.2 if dref > 0 else 0.0),
                       fine=(dref if dref > 0 else 0.0), ends=0.006)
        crank = sstep(sp.xR - 0.085, sp.xR - 0.004, np.abs(Xs))
        Y = (Y_H - (Y_H - Y_V) * crank + sp.yfield(Xs, z)
             - _weld_flat_h(sp, Xs) + _fold_disp(sp, Xs, z)
             + _wander(sp, Xs, jh + 90))
        Zs = z + _wander(sp, Xs, jh + 300, 0.00040) \
            + rnd(-0.0016, 0.0016, sp.seed, 110, jh) * np.sin(
                np.pi * (Xs + sp.xR) / (2.0 * sp.xR))
        P = np.stack([Xs, Y, Zs], 1)
        end = (np.exp(-((Xs + sp.xR) / 0.010) ** 2)
               + np.exp(-((Xs - sp.xR) / 0.010) ** 2))
        dn = _dent_at(sp, Xs, Zs)
        wl = np.zeros(len(Xs))
        d = np.abs(Xs[:, None] - sp.xv[None, :])
        wl = np.exp(-(d / 0.010) ** 2).max(axis=1)
        tube_along(acc, P, sp.wire_r, L["ws"], mat=mat, caps=(True, True),
                   up_hint=(0.0, 1.0, 0.0), kind=float(K_HWIRE),
                   wear=clamp01(0.10 + 0.5 * dn),
                   bloom=clamp01(sp.bloom * (0.72 + 0.8 * math.exp(-z / 0.5))
                                 + 0.35 * wl + 0.30 * dn),
                   endc=clamp01(end), weld=wl, dent=dn, mark=np.zeros(len(Xs)))

    # ------------------------------------------------------- weld nuggets
    if L["nug"] < 0:
        return
    r = sp.wire_r
    ex = (r * 1.95, 0.0, 0.0)
    ey = (0.0, r * 1.45, 0.0)
    ez = (0.0, 0.0, r * 1.95)
    for jh in range(sp.n_h):
        z = float(sp.hz[jh])
        for iv in range(sp.n_v):
            if iv in cut or iv in bent:
                continue
            x = float(sp.xv[iv])
            yb = sp.yfield(x, z) + _fold_disp(sp, x, z)
            yv = Y_V + yb + WELD_FLAT
            yh = Y_H + yb - WELD_FLAT
            dn = float(_dent_at(sp, x, z))
            blob(acc, (x, 0.5 * (yv + yh), z), ex, ey, ez, sub=L["nug"],
                 mat=matw, kind=float(K_WELD), weld=1.0, wear=0.12,
                 bloom=clamp01(sp.bloom * 1.35 + 0.30), endc=0.30,
                 dent=dn, mark=0.0, arc=0.0, ang=0.0)
    # mesh-to-frame welds: every vertical on the two rails, every horizontal
    # on the two uprights.  82 more nuggets, and they are the joints that
    # actually hold the fabric in.
    yfr = sp.tube_r + r * 0.40
    for iv in range(sp.n_v):
        x = float(sp.xv[iv])
        for z in (sp.z_bot, float(sp.top_z_at(np.array([x]))[0])):
            blob(acc, (x, yfr, z), (r * 1.6, 0, 0), (0, r * 1.5, 0),
                 (0, 0, r * 1.6), sub=L["nug"], mat=matw, kind=float(K_WELD),
                 weld=1.0, wear=0.12, bloom=clamp01(sp.bloom * 1.4 + 0.32),
                 endc=0.30, dent=0.0, mark=0.0, arc=0.0, ang=0.0)
    for jh in range(sp.n_h):
        z = float(sp.hz[jh])
        for sgn in (-1.0, 1.0):
            blob(acc, (sgn * sp.xR, yfr, z), (r * 1.5, 0, 0), (0, r * 1.5, 0),
                 (0, 0, r * 1.6), sub=L["nug"], mat=matw, kind=float(K_WELD),
                 weld=1.0, wear=0.12, bloom=clamp01(sp.bloom * 1.4 + 0.32),
                 endc=0.30, dent=0.0, mark=0.0, arc=0.0, ang=0.0)


def build_tag(acc, sp, L, mat=3):
    """The hire depot's punched asset tag, riveted to the near upright.

    It carries a PUNCHED NUMERIC CODE and no name — the brief forbids invented
    thirty-second brands, and a hire tag is a number anyway.  It is 62 x 26 mm,
    which is 77 x 32 px at the filmed distance, so the ten punch marks are 4 px
    each and they read.
    """
    if not sp.tag or L["nug"] < 0:
        return
    x0 = -sp.xR
    y0 = -(sp.tube_r + 0.0007)
    z0 = sp.tag_z
    tilt = rnd(-0.14, 0.14, sp.seed, 120)
    hw, hh, th = 0.031, 0.0130, 0.0011
    ct, st = math.cos(tilt), math.sin(tilt)
    ux = np.array([ct, 0.0, st])
    uz = np.array([-st, 0.0, ct])
    uy = np.array([0.0, -1.0, 0.0])
    ctr = np.array([x0, y0, z0])
    V, Q = [], []
    for sy in (-1.0, 1.0):
        for sx in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                V.append(ctr + ux * (sx * hw) + uz * (sz * hh)
                         + uy * (sy * th * 0.5))
    V = np.array(V)
    Q = np.array([(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4),
                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)])
    acc.solid(V, quads=Q, mat=mat, kind=float(K_TAG), wear=0.55,
              bloom=0.10, endc=0.15, weld=0.0, dent=0.0, mark=0.0,
              arc=0.0, ang=0.0)
    # the punched code: ten positions, a raised dimple where the bit is set
    for b in range(10):
        if not (sp.tag_code >> b) & 1:
            continue
        u = (-0.9 + 1.8 * b / 9.0) * hw
        c = ctr + ux * u + uz * (hh * 0.20) + uy * (th * 0.5)
        blob(acc, c, tuple(ux * 0.0020), tuple(uy * 0.0011), tuple(uz * 0.0020),
             sub=0, mat=mat, kind=float(K_TAG), wear=0.75, bloom=0.05,
             endc=0.4, weld=0.0, dent=0.0, mark=0.0, arc=0.0, ang=0.0)
    # two rivets through into the upright
    for sx in (-1.0, 1.0):
        c = ctr + ux * (sx * hw * 0.78) + uz * (-hh * 0.45) + uy * (th * 0.5)
        blob(acc, c, tuple(ux * 0.0026), tuple(uy * 0.0015), tuple(uz * 0.0026),
             sub=0, mat=mat, kind=float(K_RIVET), wear=0.9, bloom=0.35,
             endc=0.6, weld=0.0, dent=0.0, mark=0.0, arc=0.0, ang=0.0)


def panel_mesh(sp, name):
    """One Spec -> one Acc holding one complete panel in its local frame."""
    acc = Acc(name)
    L = LOD[sp.lod]
    build_frame(acc, sp, L, mat=0)
    build_fabric(acc, sp, L, mat=1, matw=1)
    build_tag(acc, sp, L, mat=1)
    return acc


# ==============================================================================
#  7.  THE FENCE PROGRAMME  —  where the 900 panels actually are
# ==============================================================================
#
# The manifest's note is the specification:  "Perimeter plus 3 internal runs",
# 900 panels.  580 x 74.5 m of paddock is 1309 m of perimeter and three runs
# down its length is another 1710 m; at 3.5 m a panel that is 863 slots, which
# is the arithmetic behind the manifest's 900.  This table is that programme,
# stated once, in the CIRCUIT DESIGN FRAME (spec paddock_design), plus two runs
# stated in TRANSIT ROUTE coordinates because they follow the Beat-4 corridor
# and not the paddock grid.
#
# It also supersedes ``build_architecture._heras``, whose six runs are all here
# (pad_n, pad_w, pad_e, int_a, int_c, west_return, and the three compound runs)
# at the same coordinates, so swapping this module in does not give the world a
# second fence line 0.7 m from the first.
#
# WHERE THE SOUTH SIDE ISN'T.  The paddock's south boundary is y = 40.5, and
# for circuit x in [-245, +75] that boundary IS the back wall of the 14-bay
# garage block.  A fence there would be a fence against a building.  So the
# south run exists only where there is no building: west of the garages, where
# it separates the paddock from the pit-exit apron, and east of them.
#
# GATE OPENINGS are (centre along the run in metres, clear width).  Every one is
# at least GATE_MIN_W = 4.20 m, which passes the measured 2.005 m car and a tug
# side by side.  `paddock_gate` reads them back through ``run_ends()``.

_PADX0, _PADX1, _PADY0, _PADY1 = -480.0, 100.0, 40.5, 115.0
_INSET = 0.70

RUNS = [
    dict(id="pad_n", frame="circuit", tier=2,
         pts=[(_PADX0 + _INSET, _PADY1 - _INSET), (_PADX1 - _INSET, _PADY1 - _INSET)],
         gates=[(52.0, 6.0), (185.0, 8.0), (362.0, 6.0), (530.0, 7.0)]),
    dict(id="pad_w", frame="circuit", tier=2,
         pts=[(_PADX0 + _INSET, _PADY0 + _INSET), (_PADX0 + _INSET, _PADY1 - _INSET)],
         gates=[(37.0, 7.0)]),
    dict(id="pad_e", frame="circuit", tier=2,
         pts=[(_PADX1 - _INSET, _PADY0 + _INSET), (_PADX1 - _INSET, _PADY1 - _INSET)],
         gates=[(28.0, 7.0)]),
    dict(id="pad_s_w", frame="circuit", tier=1,
         pts=[(_PADX0 + _INSET, _PADY0 + _INSET), (-246.0, _PADY0 + _INSET)],
         gates=[(60.0, 8.0), (168.0, 9.0)]),
    dict(id="pad_s_e", frame="circuit", tier=2,
         pts=[(76.0, _PADY0 + _INSET), (_PADX1 - _INSET, _PADY0 + _INSET)],
         gates=[]),
    # the three internal runs the manifest counts
    dict(id="int_a", frame="circuit", tier=1,
         pts=[(-474.0, 90.4), (94.0, 90.4)],
         gates=[(92.0, 7.0), (224.0, 6.0), (392.0, 8.0), (515.0, 6.0)]),
    dict(id="int_b", frame="circuit", tier=1,
         pts=[(-474.0, 76.0), (94.0, 76.0)],
         gates=[(120.0, 8.0), (300.0, 7.0), (452.0, 6.0)]),
    dict(id="int_c", frame="circuit", tier=1,
         pts=[(-474.0, 62.4), (94.0, 62.4)],
         gates=[(74.0, 7.0), (256.0, 8.0), (430.0, 6.0)]),
    # the plant compound, verbatim from build_architecture
    dict(id="comp_s", frame="circuit", tier=3,
         pts=[(-470.0, 86.0), (-400.0, 86.0)], gates=[(34.0, 5.0)]),
    dict(id="comp_e", frame="circuit", tier=3,
         pts=[(-400.0, 86.0), (-400.0, 112.0)], gates=[]),
    dict(id="comp_n", frame="circuit", tier=3,
         pts=[(-470.0, 112.0), (-400.0, 112.0)], gates=[]),
    dict(id="west_return", frame="circuit", tier=3,
         pts=[(-472.0, 62.0), (-472.0, 88.0)], gates=[]),
    # THE HERO RUNS.  These are the panels the Beat-4 camera goes past.
    #
    # NOT along the walled part of the corridor: route stations 6..96 already
    # have a 2.40 m cut-faced concrete wall on the left and a tyre wall plus
    # debris fence on the right (world_contract TRANSIT_*), and a Heras panel
    # tucked behind either of them would never be seen.  Where the walls run
    # out, the route crosses the open pit-exit apron, and THAT is fenced:
    #
    #   apron_a  a service line across the apron at circuit y = 30, which the
    #            transit route crosses diagonally.  The two run ends either
    #            side of that crossing are the closest fence panels to the
    #            camera in the whole film — the opening is cut automatically by
    #            `placeable`, not by hand, so it cannot drift if the route does.
    #   corr_n   the left-hand hem of the route from where the retaining wall
    #            stops (t = 96) until the pit lane begins.
    dict(id="apron_a", frame="circuit", tier=0,
         pts=[(-462.0, 30.0), (-262.0, 30.0)], gates=[(48.0, 9.0)]),
    dict(id="corr_n", frame="route", tier=0, t=(92.0, 128.0), v=+7.8, gates=[]),
]

JOINT_GAP = 0.014       # between two coupled panels' uprights
STD_W = (PANEL_W, 2.000, 1.200)     # the hire fleet's three panel widths


def _run_world_pts(run, ds=2.0):
    """The run's polyline in WORLD coordinates, densely sampled."""
    if run["frame"] == "circuit":
        P = np.asarray(run["pts"], float)
        out = [P[0]]
        for k in range(1, len(P)):
            a, b = P[k - 1], P[k]
            L = float(np.linalg.norm(b - a))
            n = max(2, int(L / ds) + 1)
            out.extend(a + (b - a) * np.linspace(0, 1, n)[1:, None])
        Pc = np.asarray(out, float)
        wx, wy = C.circuit_to_world(Pc[:, 0], Pc[:, 1])
        return np.stack([np.asarray(wx, float), np.asarray(wy, float)], 1)
    t0, t1 = run["t"]
    T = np.linspace(t0, t1, max(2, int((t1 - t0) / ds) + 1))
    X, Y, H = C.access_route_arrays(T)
    v = float(run["v"])
    return np.stack([X - np.sin(H) * v, Y + np.cos(H) * v], 1)


# --- keep-out ----------------------------------------------------------------
#
# "you need to make sure theres no building no fences etc ont he road"
#
# One rule discharges the placement gate for this whole item: a panel may only
# stand where `world_ground_z` says the ground belongs to the DECLARED APRON.
# That is a positive test, not a list of exclusions, so it cannot be defeated by
# a case nobody thought of — the racing surface, the runoff platform, the access
# ribbon and the terrain all fail it by construction.

_SHOWROOM_C = (-380.5, -342.9, 63.6, 100.1)     # circuit frame, spec §paddock
_PITLANE_C = (-245.0, 130.0, 11.5, 23.5)
_GARAGE_C = (-245.0, 75.0, 23.5, 40.5)
_KEEP_PAD = 2.00        # metres of clearance added to every named structure
_RIBBON_PAD = 1.60      # beyond the 6.0 m half width of the access ribbon
_ROAD_PAD = 1.50        # beyond half_width(s) of the racing surface


def placeable(x, y):
    """-> (ok, z).  Vectorised.  z is the ground datum where ok."""
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    z, own = C.world_ground_z(x, y)
    ok = np.array([o == C.OWNER_APRON for o in np.atleast_1d(own)])
    ok &= np.isfinite(z)
    # the racing surface, with margin, even though the apron test already
    # excludes it: two independent tests is how a keep-out stays a keep-out
    s, u = C.project(x, y)
    ok &= np.abs(u) > (C.half_width(s) + C.KERB_W + C.VERGE_W + _ROAD_PAD)
    ok &= ~C.in_access_ribbon(x, y, margin=_RIBBON_PAD)
    cx, cy = C.world_to_circuit(x, y)
    for (a, b, c, d) in (_SHOWROOM_C, _PITLANE_C, _GARAGE_C):
        ok &= ~((cx > a - _KEEP_PAD) & (cx < b + _KEEP_PAD)
                & (cy > c - _KEEP_PAD) & (cy < d + _KEEP_PAD))
    return ok, z


# --- slots -------------------------------------------------------------------

class Slot(object):
    __slots__ = ("rid", "k", "seed", "w", "c", "d", "n", "z", "lean", "yaw",
                 "present", "foot_missing", "lod", "spec", "seg", "first",
                 "last", "scrim", "tier")

    def __init__(self, **kw):
        for a in self.__slots__:
            setattr(self, a, kw.get(a))

    def __repr__(self):
        return "<Slot %s#%d w=%.3f %s>" % (self.rid, self.k, self.w,
                                           "present" if self.present else "GAP")


def _segments(run, L):
    """[(a, b)] arc-length spans of the run left after its gate openings."""
    cuts = []
    for (c, w) in run.get("gates", ()):
        w = max(float(w), GATE_MIN_W)
        cuts.append((c - w * 0.5, c + w * 0.5))
    cuts.sort()
    segs, a = [], 0.0
    for (g0, g1) in cuts:
        if g0 > a + 1.0:
            segs.append((a, min(g0, L)))
        a = max(a, g1)
    if L - a > 1.0:
        segs.append((a, L))
    return segs


def _fit(length, seed=0, jamb=(True, True)):
    """Fill one segment with the fleet's three panel widths.

    A real fence line does not end on a whole panel.  Where a run meets a gate
    or simply stops, the last bay is closed with whatever short panel the depot
    sent — a 2.0 m or a 1.2 m — and the leftover is left as a gap.  So the jamb
    panels are chosen FIRST and the 3.5 m panels fill what is left, which is
    both what happens on site and what puts genuinely different objects at
    every opening instead of one width repeated 786 times.
    """
    head, tail, rem = [], [], length
    for i, want in enumerate(jamb):
        if not want:
            continue
        w = STD_W[1] if chance(0.55, seed, 400, i) else STD_W[2]
        if rem < w + JOINT_GAP + PANEL_W:
            continue
        (head if i == 0 else tail).append(w)
        rem -= w + JOINT_GAP
    mid = []
    while rem >= PANEL_W + JOINT_GAP:
        mid.append(PANEL_W)
        rem -= PANEL_W + JOINT_GAP
    for w in STD_W[1:]:
        if rem >= w + JOINT_GAP:
            mid.insert(rint(0, len(mid), seed, 401), w)
            rem -= w + JOINT_GAP
            break
    return head + mid + tail, rem


_SLOTS_CACHE = {}


def panel_slots(runs=None):
    """Every panel slot in the world, present or not.  Cached, deterministic."""
    key = id(runs) if runs is not None else 0
    if key in _SLOTS_CACHE:
        return _SLOTS_CACHE[key]
    runs = RUNS if runs is None else runs
    slots = []
    pid = 0
    for ri, run in enumerate(runs):
        P = _run_world_pts(run)
        d = np.linalg.norm(P[1:] - P[:-1], axis=1)
        arc = np.concatenate([[0.0], np.cumsum(d)])
        L = float(arc[-1])

        def at(a):
            i = int(np.clip(np.searchsorted(arc, a) - 1, 0, len(P) - 2))
            t = (a - arc[i]) / max(arc[i + 1] - arc[i], 1e-9)
            p = P[i] + (P[i + 1] - P[i]) * t
            v = P[i + 1] - P[i]
            v = v / max(np.linalg.norm(v), 1e-9)
            return p, v

        for si, (a0, a1) in enumerate(_segments(run, L)):
            widths, rem = _fit(a1 - a0, seed=(ri * 101 + si),
                               jamb=(a0 > 0.5, a1 < L - 0.5))
            if not widths:
                continue
            a = a0 + rem * 0.5
            lean = rnd(-1.4, 1.4, ri, si, 900)
            for k, w in enumerate(widths):
                seed = (ri * 1000003 + si * 7919 + k * 131 + 17) & 0x7FFFFFFF
                c, dv = at(a + w * 0.5)
                nv = np.array([-dv[1], dv[0]])
                # the lean is a random walk down the run, damped by the
                # couplers: neighbours lean together, which is what makes a
                # fence line read as a chain and not as noise
                lean = (lean * 0.72 + rnd(-2.9, 2.9, seed, 200) * 0.62)
                lean = float(np.clip(lean, -4.6, 4.6))
                first = k == 0
                last = k == len(widths) - 1
                present = not (chance(0.045, seed, 201) and not first and not last)
                sx = np.linspace(-0.5, 0.5, 5) * w
                px = c[0] + dv[0] * sx
                py = c[1] + dv[1] * sx
                ok, zz = placeable(px, py)
                if not ok.all():
                    present = False
                z = float(np.nanmax(zz)) if np.isfinite(zz).any() else 0.0
                slots.append(Slot(
                    rid=run["id"], k=k, seed=seed, w=w, c=(float(c[0]), float(c[1])),
                    d=(float(dv[0]), float(dv[1])), n=(float(nv[0]), float(nv[1])),
                    z=z, lean=lean, yaw=rnd(-1.5, 1.5, seed, 202),
                    present=bool(present),
                    foot_missing=bool(chance(0.020, seed, 203)),
                    lod=0, spec=None, seg=si, first=first, last=last,
                    scrim=bool(chance(0.35, seed, 204)), tier=run.get("tier", 2)))
                pid += 1
                a += w + JOINT_GAP
    _SLOTS_CACHE[key] = slots
    return slots


def panel_frame(slot):
    """-> (R, O): the 3x3 rotation (columns = local X, Y, Z) and world origin.

    +X along the run, +Y to the mesh side, +Z up; the origin is the midpoint of
    the two spigot cuts, FOOT_LIFT_M above the ground datum.  The lean is a
    rotation about the LOCAL X axis through that origin, which is the physical
    truth: both spigots stay in their blocks and the panel tips over them.
    """
    dx, dy = slot.d
    yaw = math.radians(slot.yaw)
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    ex = np.array([dx * cy_ - dy * sy_, dx * sy_ + dy * cy_, 0.0])
    ex = ex / np.linalg.norm(ex)
    ey0 = np.array([-ex[1], ex[0], 0.0])
    ez0 = np.array([0.0, 0.0, 1.0])
    th = math.radians(slot.lean)
    ct, st = math.cos(th), math.sin(th)
    ey = ey0 * ct + ez0 * st
    ez = -ey0 * st + ez0 * ct
    lift = FOOT_LIFT_M if not slot.foot_missing else -C.BASE_EMBED_M * 1.4
    O = np.array([slot.c[0], slot.c[1], slot.z + lift])
    return np.stack([ex, ey, ez], 0), O          # rows = local axes


# ==============================================================================
#  8.  THE INTERFACE THE FIVE DEPENDANTS BUILD ON
# ==============================================================================

def _to_world(R, O, p):
    p = np.asarray(p, float)
    return O + p[..., 0:1] * R[0] + p[..., 1:2] * R[1] + p[..., 2:3] * R[2]


def _spec_of(slot):
    if slot.spec is None:
        slot.spec = Spec(slot.seed, width=slot.w, lod=slot.lod)
    return slot.spec


def spigot_axes(slot):
    """-> [(base_world, top_world)] for the panel's two uprights."""
    sp = _spec_of(slot)
    R, O = panel_frame(slot)
    out = []
    for sgn in (-1.0, 1.0):
        b = _to_world(R, O, np.array([sgn * sp.xR, 0.0, sp.z_spig]))
        t = _to_world(R, O, np.array([sgn * sp.xR, 0.0, sp.z_top - sp.bend_r]))
        out.append((b, t))
    return out


def foot_sites(runs=None):
    """ONE RECORD PER CONCRETE BLOCK, for ``heras_fence_foot``.

    A block serves a JOINT — two adjacent panels drop one spigot each into its
    two holes — or a run end, where it takes a single spigot.  That is why the
    manifest counts 950 blocks against 900 panels and it is the reason this is
    a function and not "two per panel".

    Each record:
        world       block centre on the ground datum (z = world_ground_z)
        ground_z    the datum there; the block embeds C.BASE_EMBED_M below it
        axis_dir    unit vector along the fence line (the hole axis spacing)
        normal      unit vector across it
        spigots     [(world_point, radius)] the one or two tubes it receives
        panels      the panel ids it serves
        lone        True at a run end / beside a gap: only one spigot
    """
    out = []
    slots = [s for s in panel_slots(runs) if s.present]
    by_run = {}
    for s in slots:
        by_run.setdefault((s.rid, s.seg), []).append(s)
    for key, ss in by_run.items():
        ss = sorted(ss, key=lambda s: s.k)
        for i, s in enumerate(ss):
            if s.foot_missing:
                continue
            sp = _spec_of(s)
            R, O = panel_frame(s)
            ax = R[0]
            nv = R[1] * 0.0 + np.array([-ax[1], ax[0], 0.0])
            for end, sgn in ((0, -1.0), (1, +1.0)):
                spg = _to_world(R, O, np.array([sgn * sp.xR, 0.0, sp.z_spig]))
                nb = None
                if sgn > 0 and i + 1 < len(ss) and ss[i + 1].k == s.k + 1:
                    nb = ss[i + 1]
                elif sgn < 0:
                    if i > 0 and ss[i - 1].k == s.k - 1:
                        continue        # that joint's block was emitted already
                spg2, ids = None, [id(s)]
                if nb is not None:
                    sp2 = _spec_of(nb)
                    R2, O2 = panel_frame(nb)
                    spg2 = _to_world(R2, O2, np.array([-sp2.xR, 0.0, sp2.z_spig]))
                    ids.append(id(nb))
                ctr = spg if spg2 is None else (spg + spg2) * 0.5
                zg, own = C.world_ground_z(float(ctr[0]), float(ctr[1]))
                out.append(dict(
                    world=(float(ctr[0]), float(ctr[1]),
                           float(zg if np.isfinite(zg) else s.z)),
                    ground_z=float(zg if np.isfinite(zg) else s.z),
                    axis_dir=tuple(float(v) for v in ax),
                    normal=tuple(float(v) for v in nv),
                    spigots=[(tuple(float(v) for v in spg), float(sp.tube_r))]
                    + ([(tuple(float(v) for v in spg2), float(sp2.tube_r))]
                       if spg2 is not None else []),
                    lone=spg2 is None, run=s.rid, panel=s.k, owner=own))
    return out


def coupler_sites(runs=None):
    """ONE RECORD PER JOINT, for ``heras_fence_coupler``.

    The clamp bridges the two uprights that meet at the joint.  ~8 % of joints
    have no coupler fitted, which is exactly the variation axis the coupler's
    own manifest record names — decided HERE so the two modules agree.
    """
    out = []
    slots = [s for s in panel_slots(runs) if s.present]
    by_run = {}
    for s in slots:
        by_run.setdefault((s.rid, s.seg), []).append(s)
    for key, ss in by_run.items():
        ss = sorted(ss, key=lambda s: s.k)
        for i in range(len(ss) - 1):
            a, b = ss[i], ss[i + 1]
            if b.k != a.k + 1:
                continue
            spa, spb = _spec_of(a), _spec_of(b)
            Ra, Oa = panel_frame(a)
            Rb, Ob = panel_frame(b)
            for hz, tagn in ((1.42, "upper"), (0.30, "lower")):
                pa = _to_world(Ra, Oa, np.array([spa.xR, 0.0, hz]))
                pb = _to_world(Rb, Ob, np.array([-spb.xR, 0.0, hz]))
                fitted = not chance(0.08, a.seed, 300, int(hz * 10))
                if tagn == "lower" and chance(0.55, a.seed, 301):
                    continue            # most joints carry only the top clamp
                out.append(dict(
                    world=tuple(float(v) for v in (pa + pb) * 0.5),
                    tube_a=(tuple(float(v) for v in pa), float(spa.tube_r)),
                    tube_b=(tuple(float(v) for v in pb), float(spb.tube_r)),
                    axis=tuple(float(v) for v in Ra[2]),
                    across=tuple(float(v) for v in Ra[0]),
                    fitted=bool(fitted), height=hz, run=a.rid,
                    panels=(a.k, b.k)))
    return out


def scrim_sites(runs=None):
    """The ~35 % of panels carrying a banner, for ``heras_banner_scrim``.

    Returns the FRAME OPENING in world space — the rectangle the scrim is
    stretched over, inset to the inside of the tube — plus the tie points down
    both uprights and along the top rail, which is where the scrim's eyelets
    have to be and where it sags between them.
    """
    out = []
    for s in panel_slots(runs):
        if not (s.present and s.scrim):
            continue
        sp = _spec_of(s)
        R, O = panel_frame(s)
        x0, x1 = -sp.xR + sp.tube_r, sp.xR - sp.tube_r
        z0, z1 = sp.z_bot + sp.tube_r, sp.z_top - sp.tube_r
        corners = [_to_world(R, O, np.array([x, 0.0, z]))
                   for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        ties = []
        for zz in np.linspace(z0 + 0.06, z1 - 0.06, 5):
            for xx in (x0, x1):
                ties.append(_to_world(R, O, np.array([xx, 0.0, float(zz)])))
        for xx in np.linspace(x0 + 0.18, x1 - 0.18, max(3, int(s.w / 0.7))):
            ties.append(_to_world(R, O, np.array([float(xx), 0.0, z1])))
        out.append(dict(
            corners=[tuple(float(v) for v in c) for c in corners],
            ties=[tuple(float(v) for v in t) for t in ties],
            face_normal=tuple(float(-v) for v in R[1]),   # the public face
            width=float(x1 - x0), height=float(z1 - z0),
            run=s.rid, panel=s.k, seed=int(s.seed),
            sun_face=float(np.dot(-R[1], np.array(C.SUN_DIR)))))
    return out


def tie_sites(runs=None):
    """Every cable-tie position on this item, for ``cable_tie_offcut``."""
    out = []
    for sc in scrim_sites(runs):
        for t in sc["ties"]:
            out.append(dict(world=t, host="scrim_eyelet", run=sc["run"]))
    for cp in coupler_sites(runs):
        if not cp["fitted"]:
            continue
        out.append(dict(world=cp["world"], host="coupler_tail", run=cp["run"]))
    return out


def run_ends(runs=None):
    """Where a run stops and a gate leaf has to close it, for ``paddock_gate``."""
    out = []
    slots = [s for s in panel_slots(runs) if s.present]
    by_run = {}
    for s in slots:
        by_run.setdefault((s.rid, s.seg), []).append(s)
    for (rid, seg), ss in by_run.items():
        ss = sorted(ss, key=lambda s: s.k)
        for (s, sgn, kind) in ((ss[0], -1.0, "start"), (ss[-1], +1.0, "end")):
            sp = _spec_of(s)
            R, O = panel_frame(s)
            p = _to_world(R, O, np.array([sgn * sp.xR, 0.0, sp.z_spig]))
            out.append(dict(world=tuple(float(v) for v in p),
                            axis=tuple(float(v) for v in R[2]),
                            along=tuple(float(v * sgn) for v in R[0]),
                            radius=float(sp.tube_r), height=float(sp.z_top),
                            run=rid, segment=seg, which=kind))
    return out


# ==============================================================================
#  9.  THE MATERIAL  —  hot-dip zinc, four seasons in a paddock
# ==============================================================================

class NT(object):
    """Node DSL that knows which socket a Mix node actually uses."""

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 1
        nd.location = ((self.x % 16) * 220, -(self.x // 16) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, idx, src):
        if src is None:
            return
        while isinstance(src, tuple) and len(src) == 2 and isinstance(src[0], tuple):
            src = src[0]
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[idx].default_value = float(src)

    def cmix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, 0, fac); self.pin(nd, 6, a); self.pin(nd, 7, b)
        return (nd, 2)

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, 0, fac); self.pin(nd, 2, a); self.pin(nd, 3, b)
        return (nd, 0)

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        return (nd, 0)

    def vmath(self, op, a=None, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        if scale is not None:
            self.pin(nd, 3, scale)
        return (nd, 0)

    def noise(self, vec, scale, detail=8.0, rough=0.55, dist=0.0, lac=2.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 3, detail)
        self.pin(nd, 4, rough); self.pin(nd, 5, lac); self.pin(nd, 8, dist)
        return (nd, 0)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 8, rand)
        return (nd, out)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, bands_direction="X"):
        nd = self.n("ShaderNodeTexWave", wave_type="BANDS",
                    bands_direction=bands_direction)
        self.pin(nd, 0, vec); self.pin(nd, 1, scale)
        self.pin(nd, 2, distortion); self.pin(nd, 3, detail)
        return (nd, 1)

    def grad(self, vec, kind="LINEAR"):
        nd = self.n("ShaderNodeTexGradient", gradient_type=kind)
        self.pin(nd, 0, vec)
        return (nd, 1)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, 0, src)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = tuple(stops[0][1]) + (1.0,)
        for pos, col in stops[1:]:
            e = el.new(pos)
            e.color = tuple(col) + (1.0,)
        return (nd, 0)

    def attr(self, name, out=2, typ="GEOMETRY"):
        nd = self.n("ShaderNodeAttribute", attribute_type=typ)
        nd.attribute_name = name
        return (nd, out)

    def maprange(self, v, f0, f1, t0, t1, clamp=True):
        nd = self.n("ShaderNodeMapRange")
        nd.clamp = clamp
        self.pin(nd, 0, v); self.pin(nd, 1, f0); self.pin(nd, 2, f1)
        self.pin(nd, 3, t0); self.pin(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance=None, normal=None,
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
        if (distance is None) == (modulation_pp is None):
            raise ValueError("bump() takes exactly one of distance= or "
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
            distance = (K.relief_amplitude_for(modulation_pp, wavelength_m)
                        * 1e-3 / max(_s * float(height_pp), 1e-9))
        nd = self.n("ShaderNodeBump")
        self.pin(nd, nd.inputs.find("Strength"), strength)
        self.pin(nd, nd.inputs.find("Distance"), distance)
        self.pin(nd, nd.inputs.find("Height"), height)
        if normal is not None:
            self.pin(nd, nd.inputs.find("Normal"), normal)
        return (nd, 0)

    def geo(self, out):
        nd = self.n("ShaderNodeNewGeometry")
        return (nd, out)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)


# LINEAR reflectances.  Hot-dip zinc is DARKER than intuition: a fresh spangled
# coat measures 0.55-0.65 specular but weathers to 0.18-0.25 diffuse within a
# year.  A fence that renders white is a fence with the albedo of paper — and
# 700 of them white is a paddock made of chalk.
PAL = dict(
    zinc_fresh=(0.3900, 0.4020, 0.4180),
    zinc_dull=(0.2350, 0.2420, 0.2560),
    zinc_dark=(0.1380, 0.1430, 0.1520),
    white_rust=(0.3050, 0.3000, 0.2880),      # zinc carbonate, chalky, matte
    red_rust=(0.1040, 0.0410, 0.0175),
    rust_bright=(0.2100, 0.0880, 0.0330),
    steel_bare=(0.1480, 0.1480, 0.1530),
    grime=(0.0300, 0.0282, 0.0258),
    dust=(0.1360, 0.1215, 0.0975),
    mud=(0.0720, 0.0565, 0.0392),
    alu=(0.4200, 0.4230, 0.4260),
)


def mat_panel():
    """One material for the whole panel: frame, fabric, welds, tag.

    ELEVEN histories, in the order the steel acquired them, and no image
    anywhere:

        zinc spangle, per-panel crystal size (the dip lot)
          -> wire-drawing striations that run ALONG each member
          -> carbonate bloom, in the weld crevices and the wet zone first
          -> red rust out of every sheared end and every punched tag hole
          -> rust RUNNING DOWN from those ends
          -> paddock dust, heavier low and on upward-facing surfaces
          -> mud thrown at the bottom 350 mm by every vehicle that passed
          -> rain wash cutting clean streaks back through the film
          -> the depot's sprayed colour band on the top rail
          -> zinc cracked white along every dent rim
          -> burnish where a hand, a stack or a coupler has rubbed it bare

    TWO COORDINATE STREAMS.  `OBJ` is the panel's own canonical frame — +X
    along the panel, +Y to the mesh, +Z up, |P| < 2.1 m — and it is what every
    gravity-aligned effect reads, so `pz` really is height above the spigot cut.
    `NZ` is the same thing plus a PER-OBJECT random offset, and it is what every
    noise reads, so 771 panels do not share one spangle.  Feeding the offset
    stream to a height-dependent layer is the bug that made the first W-beam
    render as painted cream; it is not repeated here.
    """
    name = PFX + "Galv"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    t = NT(name)
    A = PFX.lower()
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)                                   # Object — NEVER Position

    ofs = t.comb(t.attr(A + "ofs_x", 2, "OBJECT"),
                 t.attr(A + "ofs_y", 2, "OBJECT"),
                 t.attr(A + "ofs_z", 2, "OBJECT"))
    NZ = t.vmath("ADD", OBJ, ofs)
    px = t.sep(OBJ, 0)
    pz = t.sep(OBJ, 2)                              # height above the spigot cut

    kind = t.attr(A + "kind")
    arc = t.attr(A + "arc")
    ang = t.attr(A + "ang")
    wear = t.attr(A + "wear")
    bloomv = t.attr(A + "bloom")
    endc = t.attr(A + "endc")
    weldv = t.attr(A + "weld")
    dentv = t.attr(A + "dent")
    markv = t.attr(A + "mark")

    age = t.attr(A + "age", 2, "OBJECT")
    bloom_o = t.attr(A + "bloomo", 2, "OBJECT")
    mud_o = t.attr(A + "mudo", 2, "OBJECT")
    lot = t.attr(A + "lot", 2, "OBJECT")
    bandcol = t.comb(t.attr(A + "band_r", 2, "OBJECT"),
                     t.attr(A + "band_g", 2, "OBJECT"),
                     t.attr(A + "band_b", 2, "OBJECT"))

    up = t.sep(t.geo(1), 2)                          # world normal z: "faces up"
    upmask = t.maprange(up, 0.05, 0.85, 0.0, 1.0)

    # ------------------------------------------------------------- 1. ZINC
    # Dendritic spangle.  Crystal size is a property of the DIP, so it comes
    # from the object's lot: 5-40 mm, which is 6-50 px at the filmed distance
    # and the single most identifying feature of galvanised steel this close.
    # SPANGLE SIZE IS A PROPERTY OF THE SECTION, NOT A CONSTANT.  A 4 mm wire
    # dipped at 450 C loses its heat in seconds and freezes 1-4 mm crystals; a
    # 41.5 mm tube holds it and grows 8-25 mm ones.  The first pass used one
    # scale for both and set it from the sheet-steel figure, so the wires got a
    # 38 mm crystal — nine times their own diameter — and rendered as a smooth
    # gradient.  At 0.46 m the wire is 79 px across and that was the whole
    # material.
    is_wire = t.maprange(kind, 0.55, 1.35, 0.0, 1.0)
    sc = t.fmix(is_wire, t.maprange(lot, 0.0, 2.0, 52.0, 128.0),
                t.maprange(lot, 0.0, 2.0, 290.0, 620.0))
    spang = t.vor(NZ, sc, "F1", 1, 0.98)
    cellv = t.sep(spang, 0)
    cellu = t.sep(spang, 1)
    edge = t.vor(NZ, sc, "DISTANCE_TO_EDGE", 0, 0.98)   # crystal BOUNDARIES
    edgem = t.maprange(edge, 0.0, 0.085, 1.0, 0.0)
    # dendrite arms inside each crystal, oriented by the crystal's own key
    dend = t.noise(t.vmath("SCALE", t.vmath("ADD", NZ, t.vmath("SCALE", spang,
                                                               scale=0.35)),
                           scale=5.2), 240.0, 6.0, 0.74, dist=1.6)
    fine = t.noise(NZ, 940.0, 3.0, 0.5)

    zinc = t.cmix(t.maprange(cellv, 0.06, 0.94, 0.0, 1.0),
                  PAL["zinc_dull"], PAL["zinc_fresh"])
    zinc = t.cmix(t.maprange(dend, 0.30, 0.74, 0.0, 0.95), zinc, PAL["zinc_dark"])
    zinc = t.cmix(t.math("MULTIPLY", edgem, 0.55), zinc, PAL["zinc_dark"])
    zinc = t.cmix(t.maprange(fine, 0.3, 0.7, 0.0, 0.30), zinc, PAL["zinc_dark"])

    # drawing striations: fine lines ALONG the member.  arc is metres of member,
    # so 1400 bands/m is a 0.7 mm pitch — 0.9 px, right at the resolving limit,
    # which is exactly where a drawn wire's surface lives.
    draw = t.wave(t.comb(t.math("MULTIPLY", ang, 1.0),
                         t.math("MULTIPLY", arc, 0.09), 0.0),
                  46.0, 1.9, 4.0)
    drawm = t.maprange(draw, 0.18, 0.82, 0.0, 1.0)
    zinc = t.cmix(t.math("MULTIPLY", drawm, 0.30), zinc, PAL["zinc_dark"])

    # ------------------------------------------------- 2. CARBONATE BLOOM
    # White rust is a BLOTCH, not a wash, and it grows where water sits: the
    # weld crevices, the underside of the bottom rail, the bore of the spigot,
    # and everything in the splash zone.  Uniform bloom is what turns a fence
    # into chalk.
    wet = t.math("ADD", t.math("MULTIPLY", weldv, 0.90),
                 t.math("MULTIPLY", upmask, 0.42), clamp=True)
    wet = t.math("ADD", wet, t.maprange(pz, 0.55, 0.02, 0.0, 0.55), clamp=True)
    blot = t.noise(t.vmath("SCALE", NZ, scale=1.0), 7.5, 9.0, 0.70)
    blot2 = t.noise(t.vmath("SCALE", NZ, scale=1.0), 44.0, 7.0, 0.62)
    wr = t.math("MULTIPLY",
                t.math("ADD", t.math("MULTIPLY", bloom_o, 0.86), 0.16),
                t.math("ADD", t.math("MULTIPLY", wet, 0.95), 0.16))
    wr = t.math("MULTIPLY", wr, t.math("ADD", bloomv, 0.25))
    wr = t.math("MULTIPLY", wr, t.maprange(blot, 0.50, 0.84, 0.00, 1.30))
    wr = t.math("MULTIPLY", wr, t.maprange(blot2, 0.38, 0.80, 0.06, 1.20),
                clamp=True)
    col = t.cmix(wr, zinc, PAL["white_rust"])

    # ------------------------------------------------------ 3. RED RUST
    # Zinc is sacrificial, so red rust only starts where the coating is GONE:
    # a sheared wire end, the punched tag holes, the rivets, the dent rims
    # where the coating cracked.  Then it runs down.
    bare = t.math("ADD", t.math("MULTIPLY", endc, 1.0),
                  t.math("MULTIPLY", dentv, 0.34), clamp=True)
    bare = t.math("MULTIPLY", bare, t.math("ADD", t.math("MULTIPLY", age, 0.85),
                                           0.18), clamp=True)
    streak = t.noise(t.comb(t.math("MULTIPLY", t.sep(NZ, 0), 7.0),
                            t.sep(NZ, 1),
                            t.math("MULTIPLY", t.sep(NZ, 2), 0.16)),
                     58.0, 8.0, 0.72)
    run = t.math("MULTIPLY", t.maprange(streak, 0.44, 0.86, 0.0, 1.0),
                 t.math("MULTIPLY", age, 0.55))
    rustm = t.math("ADD", bare, t.math("MULTIPLY", run,
                                       t.maprange(endc, 0.0, 0.35, 0.0, 1.0)),
                   clamp=True)
    rustc = t.cmix(t.maprange(t.noise(NZ, 260.0, 5.0, 0.6), 0.35, 0.7, 0.0, 1.0),
                   PAL["red_rust"], PAL["rust_bright"])
    col = t.cmix(t.math("MULTIPLY", rustm, 0.92), col, rustc)
    col = t.cmix(t.math("MULTIPLY", wear, t.math("SUBTRACT", 0.55,
                                                 t.math("MULTIPLY", age, 0.30))),
                 col, PAL["steel_bare"])

    # ------------------------------------- 4. DUST, MUD, AND THE RAIN WASH
    dustn = t.noise(t.vmath("SCALE", NZ, scale=(1.0)), 16.0, 7.0, 0.62)
    dustm = t.math("MULTIPLY", t.maprange(pz, 1.7, 0.15, 0.10, 0.85),
                   t.maprange(dustn, 0.3, 0.8, 0.35, 1.0))
    dustm = t.math("MULTIPLY", dustm,
                   t.math("ADD", 0.35, t.math("MULTIPLY", upmask, 0.85)),
                   clamp=True)
    col = t.cmix(t.math("MULTIPLY", dustm, 0.60), col, PAL["dust"])

    splat = t.vor(t.vmath("SCALE", NZ, scale=3.4), 55.0, "F1", 0, 1.0)
    mudm = t.math("MULTIPLY", mud_o, t.maprange(pz, 0.42, 0.03, 0.0, 1.0))
    mudm = t.math("MULTIPLY", mudm, t.maprange(splat, 0.02, 0.42, 1.0, 0.0),
                  clamp=True)
    col = t.cmix(t.math("MULTIPLY", mudm, 0.88), col, PAL["mud"])

    wash = t.wave(t.comb(t.math("MULTIPLY", t.sep(NZ, 0), 26.0),
                         t.sep(NZ, 1), t.math("MULTIPLY", t.sep(NZ, 2), 0.07)),
                  9.0, 1.6, 4.0)
    washm = t.math("MULTIPLY", t.maprange(wash, 0.52, 0.9, 0.0, 1.0),
                   t.maprange(pz, 0.25, 1.4, 0.0, 0.85))
    col = t.cmix(t.math("MULTIPLY", washm, 0.42), col, zinc)

    # --------------------------------------- 5. THE DEPOT'S SPRAYED BAND
    # Overspray does not have a hard edge and it does not cover: it is a thin
    # coat over spangle, so the crystals still read through it.
    bandm = t.math("MULTIPLY", markv,
                   t.maprange(t.noise(NZ, 120.0, 5.0, 0.6), 0.25, 0.75, 0.55, 1.0))
    col = t.cmix(t.math("MULTIPLY", bandm, 0.82), col,
                 t.cmix(0.18, bandcol, zinc))

    # the aluminium tag is not galvanised steel
    tagm = t.maprange(kind, 4.6, 5.4, 0.0, 1.0)
    col = t.cmix(t.math("MULTIPLY", tagm, 0.75), col, PAL["alu"])

    # ------------------------------------ 5b. HANDLING SCRATCHES AND CREVICE
    # A hire panel is dragged off a lorry, stacked twenty deep and dragged
    # back.  The marks run ALONG the member because that is the way it slides.
    scr = t.vor(t.comb(t.math("MULTIPLY", arc, 130.0),
                       t.math("MULTIPLY", ang, 26.0),
                       t.sep(NZ, 2)), 1.0, "F1", 0, 1.0)
    scrm = t.math("MULTIPLY", t.maprange(scr, 0.0, 0.05, 1.0, 0.0),
                  t.math("ADD", t.math("MULTIPLY", wear, 0.85), 0.10))
    col = t.cmix(t.math("MULTIPLY", scrm, 0.55), col, PAL["steel_bare"])

    # the crevice where a wire crosses a wire never dries and never gets
    # cleaned: it is the darkest thing on the panel and it is 9 px across
    crev = t.math("MULTIPLY", weldv,
                  t.maprange(t.noise(NZ, 300.0, 5.0, 0.6), 0.2, 0.8, 0.5, 1.0))
    col = t.cmix(t.math("MULTIPLY", crev, 0.42), col, PAL["grime"])

    # ---------------------------------------------------------- 6. ROUGHNESS
    # Per-crystal roughness is the main cue that says SPANGLE: adjacent
    # crystals are differently oriented and catch the sun differently, which is
    # why a galvanised surface glitters in patches instead of reflecting.
    rough = t.fmix(t.maprange(cellu, 0.05, 0.95, 0.0, 1.0), 0.50, 0.22)
    rough = t.fmix(t.math("MULTIPLY", edgem, 0.75), rough, 0.62)
    rough = t.fmix(t.math("MULTIPLY", drawm, 0.60), rough, 0.55)
    rough = t.fmix(wr, rough, 0.86)                       # bloom is matte chalk
    rough = t.fmix(t.math("MULTIPLY", rustm, 0.9), rough, 0.78)
    rough = t.fmix(t.math("MULTIPLY", dustm, 0.7), rough, 0.72)
    rough = t.fmix(t.math("MULTIPLY", mudm, 0.9), rough, 0.66)
    rough = t.fmix(t.math("MULTIPLY", wear, 0.6), rough, 0.16)
    rough = t.fmix(t.math("MULTIPLY", scrm, 0.7), rough, 0.13)
    rough = t.fmix(t.math("MULTIPLY", crev, 0.8), rough, 0.90)   # burnished
    rough = t.math("ADD", rough,
                   t.math("MULTIPLY", t.maprange(fine, 0.2, 0.8, -0.05, 0.05), 1.0))

    metal = t.math("SUBTRACT", 1.0,
                   t.math("ADD", t.math("MULTIPLY", wr, 0.80),
                          t.math("ADD", t.math("MULTIPLY", rustm, 0.72),
                                 t.math("ADD", t.math("MULTIPLY", mudm, 0.92),
                                        t.math("MULTIPLY", dustm, 0.34))),
                          clamp=True), clamp=True)
    metal = t.math("MULTIPLY", metal,
                   t.math("SUBTRACT", 1.0, t.math("MULTIPLY", crev, 0.55)),
                   clamp=True)

    # --------------------------------------------------------------- 7. BUMP
    # Spangle relief is real: a hot-dip crystal boundary stands 20-60 um proud,
    # which is a twentieth of a pixel of displacement but a very visible change
    # of normal at a grazing 12.5 deg sun.  Pitting under the bloom is coarser.
    relief = t.math("ADD", t.math("MULTIPLY", edgem, 0.70),
                    t.math("ADD", t.math("MULTIPLY", drawm, 0.45),
                           t.math("MULTIPLY", t.noise(NZ, 1500.0, 4.0, 0.55), 0.25)))
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES.  itemkit section 5b,
    # ITEM-CAMPAIGN-BRIEF 4a.  m = 2 sin(theta) / tan(e), and at this film's
    # 12.47 deg sun that is a 4.52x amplifier with a hard ceiling of 2/tan(e) =
    # 9.04 -- past which a normal is asking for a shadow, not for relief.
    #
    # TWO OF THESE THREE ARE DELIBERATE RE-TUNES DOWNWARD.  This panel was
    # audited at m_median 8.88 against that 9.04 ceiling: it was not a dead
    # stack, it was pinned at the terminator, the same failure as `tyre_blanket`
    # at m 6.0.  Measured honestly, band by band, the shipped depths were
    #
    #   [0] edgem  w 0.70  lam  4.77 mm  m 2.430   0.424 mm p-p of crystal
    #   [1] pit    w 1.00  lam  4.21 mm  m 6.346   1.320 mm p-p of pitting
    #   [2] crust  w 1.00  lam 16.69 mm  m 4.771   3.300 mm p-p of mud
    #
    # and [0] and [1] are argued down below.  [2] IS LEFT ALONE: 4.771 is inside
    # RELIEF_BANDS["hard_feature"] (1.5-6.0), a dried mud crust genuinely is a
    # lipped, flaking edge and not a crumple, and `mudm` gates it to the splash
    # zone at the foot of the panel.  Note for whoever comes next: 3.3 mm p-p is
    # a large fraction of a 4.0 mm mesh wire, so if the wires ever read as
    # furred, [2] is the stage and 1.5 mm of crust is the honest ceiling.
    #
    # [0] -- 2.430 -> 0.360.  THE MODULE'S OWN PHYSICS SAYS SO, three lines up:
    # "a hot-dip crystal boundary stands 20-60 um proud".  It shipped 424 um,
    # seven times its own stated maximum, and as an UNGATED ISOTROPIC field --
    # exactly the shape the law exists to stop (1.66 rendered as thick felt,
    # 3.76 as coarse stucco).  0.360 is what 60 um -- the top of the module's
    # own range -- produces at the crystal pitch, and it lands in
    # RELIEF_BANDS["isotropic_micro"] (0.12-0.45), the band for cast skin and
    # blasted metal.  The crystal pitch is NOT a literal here: `sc` is a node,
    # 290-620 for a wire and 52-128 for a tube, so the wavelength is written
    # from the middle of the WIRE lot -- the mesh, not the frame, is the surface
    # the eye is on.  At the ends of that lot the same Distance is m 0.490 (fine
    # crystals) and m 0.229 (coarse); on the tube's 17-42 mm crystals it falls
    # to m 0.041-0.101,
    # which is right, because a tube's crystal is a swell, not a wall.
    # At 0.360 the stage's other bands become: noise 1.07 mm m 0.574
    # (isotropic_macro), drawm 21.7 mm m 0.051 (silent, and it is a colour and
    # roughness cue anyway).
    #
    # [1] -- 6.346 -> 2.000.  6.346 is above the top of EVERY band the record
    # supports, and 1.32 mm p-p of pitting is a third of the diameter of the
    # 4.0 mm wire it is pitting: a fence that deep in the section is scrap, not
    # dressing.  2.000 is the floor of `hard_feature`, which is the right band
    # -- a corrosion pit is an EDGE, and `wr`/`rustm` gate it to the metal that
    # has actually lost its zinc -- and it puts 0.304 mm p-p on the surface,
    # which is what advanced pitting on galvanised wire really measures.  The
    # scratch band `scrm` follows it down to m 1.12 (`sparse_crease`).
    #
    # THE WAVELENGTHS COME FROM THE LITERALS THAT PICKED THE SCALES.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 455.0   #  4.77 mm, mid wire lot
    LAM_PIT = K.NOISE_WAVELENGTH_FACTOR / 380.0         #  4.21 mm
    LAM_CRUST = K.VORONOI_WAVELENGTH_FACTOR / 130.0     # 16.69 mm
    b1 = t.bump(relief, 0.55, modulation_pp=0.360, wavelength_m=LAM_SPANGLE,
                height_pp=0.70)
    pit = t.noise(t.vmath("SCALE", NZ, scale=1.0), 380.0, 6.0, 0.68)
    pitm = t.math("MULTIPLY", pit, t.math("ADD", wr, t.math("MULTIPLY", rustm, 1.2)))
    b2 = t.bump(t.math("ADD", pitm, t.math("MULTIPLY", scrm, 0.55)),
                0.60, normal=b1,
                modulation_pp=2.000, wavelength_m=LAM_PIT)
    crust = t.vor(t.vmath("SCALE", NZ, scale=1.0), 130.0, "F1", 0, 0.9)
    b3 = t.bump(t.math("MULTIPLY", crust,
                       t.math("ADD", t.math("MULTIPLY", mudm, 1.3),
                              t.math("MULTIPLY", rustm, 0.8))),
                0.55, normal=b2,
                modulation_pp=4.7713, wavelength_m=LAM_CRUST)

    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, 0, col)
    for nm, v in (("Metallic", metal), ("Roughness", rough), ("Normal", b3),
                  ("IOR", 2.4)):
        if nm in [i.name for i in bsdf.inputs]:
            t.pin(bsdf, [i.name for i in bsdf.inputs].index(nm), v)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs[0])
    return t.m


# ==============================================================================
# 10.  EMIT
# ==============================================================================
#
# The depot's colour bands come from build_dressing's EXISTING brand book, not
# from a 32nd invented name.  These are the background colours of the first
# twelve entries of `build_dressing.BRANDS`, verbatim; the list is copied rather
# than imported because build_dressing pulls in bpy and 250 kB of world builder
# that an item module has no business loading.
BRAND_BOOK = [
    ("VERSANT", "#12385e"), ("OCTAL", "#c8442a"), ("CADENCE", "#1d1f22"),
    ("SEPTIME", "#0f6b52"), ("PALLAS", "#5a2d6e"), ("TERRA NOVA", "#7a5a24"),
    ("ZEPHYR", "#0f7fa8"), ("BRIAR", "#4a5a2c"), ("NOVEM", "#a01d3c"),
    ("ORTHO", "#2b2f33"), ("LUMIERE", "#d8a417"), ("MARQUE", "#171a1d"),
]


def _srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX) or ob.name.startswith(STANDIN_PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    c = bpy.data.collections.get(COLL)
    if c:
        bpy.data.collections.remove(c)


def _grade_lod(slots, anchor):
    """LOD by distance to the nearest camera anchor.  Never a global setting."""
    if not anchor:
        for s in slots:
            s.lod = 1
        return
    A = np.asarray(anchor, float)[:, :2]
    P = np.array([s.c for s in slots])
    d = np.sqrt(((P[:, None, :] - A[None, :, :]) ** 2).sum(-1)).min(axis=1)
    for s, dd in zip(slots, d):
        s.lod = 3 if dd <= 10.0 else (2 if dd <= 26.0 else (1 if dd <= 150.0 else 0))


def _object_props(ob, sp, slot):
    # Per-object texture offset: the ONLY thing that stops 771 panels sharing
    # one spangle.  24 m, not 240 — Cycles evaluates procedurals in float32 and
    # at a Voronoi scale of 78 an offset of 240 puts the lookup 18 700 units
    # from the origin, where the mantissa has run out of cell.
    ob[PFX.lower() + "ofs_x"] = float(h01(sp.seed, 3) * 24.0)
    ob[PFX.lower() + "ofs_y"] = float(h01(sp.seed, 5) * 24.0)
    ob[PFX.lower() + "ofs_z"] = float(h01(sp.seed, 7) * 24.0)
    ob[PFX.lower() + "age"] = float(sp.age)
    ob[PFX.lower() + "bloomo"] = float(sp.bloom)
    ob[PFX.lower() + "mudo"] = float(sp.mud)
    ob[PFX.lower() + "lot"] = float(sp.lot)
    bn, bh = BRAND_BOOK[int(h01(sp.seed, 9) * len(BRAND_BOOK)) % len(BRAND_BOOK)]
    r, g, b = _srgb(bh)
    ob[PFX.lower() + "band_r"] = r
    ob[PFX.lower() + "band_g"] = g
    ob[PFX.lower() + "band_b"] = b
    ob["item"] = ITEM
    ob["hfp_run"] = slot.rid
    ob["hfp_k"] = int(slot.k)
    ob["hfp_lod"] = int(slot.lod)
    ob["hfp_width"] = float(slot.w)
    ob["hfp_lean_deg"] = float(slot.lean)
    ob["hfp_brand_band"] = bn


def build(scene=None, lod_anchor=None, limit=None, runs=None, coll=None):
    """Emit one object per present panel.  -> (collection, stats)."""
    t0 = time.time()
    scene = scene or bpy.context.scene
    root = coll or _coll(COLL)
    mat = mat_panel()
    slots = [s for s in panel_slots(runs) if s.present]
    _grade_lod(slots, lod_anchor)
    if limit:
        slots = slots[:limit]
    tris = verts = 0
    nl = {0: 0, 1: 0, 2: 0, 3: 0}
    for s in slots:
        sp = Spec(s.seed, width=s.w, lod=s.lod)
        s.spec = sp
        name = "%sPanel_%s_%03d" % (PFX, s.rid, s.k)
        acc = panel_mesh(sp, name)
        R, O = panel_frame(s)
        ob, st = acc.build(root, [mat], R, O, name=name)
        _object_props(ob, sp, s)
        tris += st["triangles"]
        verts += st["verts"]
        nl[s.lod] += 1
    stats = dict(panels=len(slots), triangles=tris, verts=verts, by_lod=nl,
                 seconds=round(time.time() - t0, 1))
    log("built %d panels, %d triangles (%.0f/panel) in %.0f s   LOD %s"
        % (stats["panels"], tris, tris / max(len(slots), 1), stats["seconds"], nl))
    return root, stats


# ==============================================================================
# 11.  LIGHT, CAMERA, TEST SCENE
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them."""
    from mathutils import Vector
    scene = scene or bpy.context.scene
    w = bpy.data.worlds.new(PFX + "World")
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
    for attr, val in (("sun_disc", False),
                      ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG)),
                      ("sun_intensity", 1.0),
                      ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                      ("altitude", C.SKY_ALTITUDE),
                      ("air_density", C.SKY_AIR),
                      ("aerosol_density", C.SKY_AEROSOL),
                      ("ozone_density", C.SKY_OZONE)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w

    lt = bpy.data.lights.new(PFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(STANDIN_PFX + "Sun", lt)
    d = Vector(C.SUN_DIR)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2, elev %.2f deg, bearing %.2f deg; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.01
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    return ob


def hero_aim(exclude=(), runs=None, target_inc=62.0, window=(42.0, 102.0)):
    """Which panel the macro is shot on, and from WHICH SIDE.  By score.

    Five things decide it and none of them is convenience:

      1. THE LIT FACE MUST BE RAKING-LIT.  62 deg of incidence is the target:
         the fabric is still lit and every wire throws its own shadow across
         the panel behind it.  A fence lit face-on is a grey haze — which is
         exactly how the old one read — and a fence lit from behind is a
         silhouette with no material in it at all.
         A fence has TWO faces, so both are scored and the camera goes on the
         better one; getting that choice wrong is the difference between a
         macro of a surface and a macro of a shadow.
      2. IT MUST BE ON A RUN THE FILM GOES PAST.  tier 0 is the Beat-4 corridor
         and the pit-exit apron; tier 1 is the paddock lines the transit crosses.
      3. THERE MUST BE DAMAGE IN IT.  A pristine hire panel is a rendering of a
         catalogue.  Dents, a cut wire and a real lean all score.
      4. IT MUST HAVE A NEIGHBOUR AND A GAP IN SIGHT — "the lean and the gaps
         are the whole read", so the macro has to contain both.
      5. IT MUST BE A FULL 3.5 m PANEL, because that is the object the manifest
         counts and the closure panels are a different width.

    `target_inc` = 155 asks instead for the BACKLIT read, which is what the
    transit camera actually sees for most of Beat 4.
    """
    sun = np.array(C.SUN_DIR, float)
    slots = [s for s in panel_slots(runs) if s.present]
    by = {}
    for s in slots:
        by.setdefault((s.rid, s.seg), []).append(s)
    cand = []
    for key, ss in by.items():
        ss = sorted(ss, key=lambda x: x.k)
        ks = {x.k for x in ss}
        for s in ss:
            if s.w < PANEL_W - 0.1:
                continue
            sp = Spec(s.seed, width=s.w, lod=3)
            R, O = panel_frame(s)
            best = None
            for side in (-1.0, +1.0):
                face = side * (-R[1])
                inc = math.degrees(math.acos(float(np.clip(np.dot(face, sun),
                                                           -1.0, 1.0))))
                if best is None or abs(inc - target_inc) < abs(best[0] - target_inc):
                    best = (inc, side)
            inc, side = best
            dmg = sum(abs(d.depth) for d in sp.dents) + 0.05 * len(sp.cut_v) \
                + 0.05 * len(sp.bent_v)
            gap = 1.0 if ((s.k + 1) not in ks or (s.k - 1) not in ks) else 0.0
            nbr = 1.0 if ((s.k + 1) in ks or (s.k - 1) in ks) else 0.0
            score = (120.0 * min(dmg / 0.14, 1.0)
                     + 34.0 * abs(s.lean) / 4.6
                     + 45.0 * gap + 28.0 * nbr
                     + 60.0 * (2 - min(s.tier, 2))
                     # 5. IT MUST HAVE A HISTORY.  The first pass shot the
                     # best-DAMAGED panel, which happened to be a nearly new
                     # one (age 0.39, bloom 0.10), and the macro came back
                     # reading as clean chrome.  Weathering is half of what
                     # this item is judged on, so it is half of the score.
                     + 130.0 * (0.35 * sp.age + 0.65 * sp.bloom)
                     + 30.0 * sp.mud
                     - 2.6 * abs(inc - target_inc))
            cand.append((score, s, sp, inc, side, dmg, gap))
    lit = [c for c in cand if window[0] <= c[3] <= window[1]]
    pool = lit if lit else cand
    pool.sort(key=lambda c: -c[0])
    for c in pool:
        if (c[1].rid, c[1].k) in exclude:
            continue
        _s, slot, sp, inc, side, dmg, gap = c
        return dict(slot=slot, spec=sp, sun_incidence_deg=inc, side=side,
                    damage_m=dmg, has_gap=bool(gap), score=_s,
                    n_lit_candidates=len(lit), n_candidates=len(cand))
    raise RuntimeError("no hero panel found")


def macro_rig(aim, cams, name, yaw_deg=19.0, elev_deg=3.5, height=1.00):
    """Place a camera at EXACTLY nearest_camera_m on lens_at_closest_mm.

    3.000 m is the NEAREST the lens ever gets to this item, so the camera sits
    on the perpendicular through the aim point at exactly 3.000 m and is then
    ROTATED, not moved, to look along the line.  Moving it to get the angle
    would bring the near panel inside 3.000 m — and the manifest already says
    the panel overfills the frame at that distance.

    THE CAMERA IS ON THE -Y SIDE, which is the face the frame tube stands proud
    of.  Getting that sign wrong films the back of the fabric, where the tube is
    behind the mesh and the panel has no relief at all.
    """
    slot, sp = aim["slot"], aim["spec"]
    side = float(aim.get("side", -1.0))
    R, O = panel_frame(slot)
    surf = O + R[0] * 0.0 + R[2] * height
    el = math.radians(elev_deg)
    off = side * (-R[1]) * math.cos(el) + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    off = off / np.linalg.norm(off)
    cam_p = surf + off * FILMED_AT_M
    look = surf + R[0] * (FILMED_AT_M * math.tan(math.radians(yaw_deg)))
    cam = add_camera(name, tuple(cam_p), tuple(look), LENS_MM, cams)
    d = float(np.linalg.norm(cam_p - surf))
    fh = d * (SENSOR_MM * 2160.0 / 3840.0) / LENS_MM
    log("%s: %.4f m from the panel face on a %.1f mm lens (manifest %.1f m / "
        "%.0f mm)" % (name, d, LENS_MM, FILMED_AT_M, LENS_MM))
    log("   run %s panel #%d  lean %+.2f deg  sun incidence %.1f deg on the "
        "%s face  %d dents  gap-in-shot %s"
        % (slot.rid, slot.k, slot.lean, aim["sun_incidence_deg"],
           "mesh" if side > 0 else "tube", len(sp.dents), aim["has_gap"]))
    log("   frame %.3f x %.3f m; the %.3f m panel height reads %.0f px of 2160 "
        "(manifest %.0f, overfills)"
        % (d * SENSOR_MM / LENS_MM, fh, sp.h, sp.h / fh * 2160.0, ONSCREEN_PX_4K))
    return cam, cam_p, surf


# ------------------------------------------------------------------ stand-ins
#
# The macro has to be judged in context, so the acceptance scene carries the
# ground the panels stand on and CRUDE proxies for the two items that are not
# mine: `heras_fence_foot` and `heras_fence_coupler`.  They are deliberately
# prefixed HSTD_ so the gate's --prefix HFP_ cannot count them: measuring my
# own item's triangles and then including someone else's stand-ins would be a
# number that answers a different question than the one asked.

def mat_standin(name, base, rough=0.72, scale=30.0, bumpstr=0.25):
    if PFX + name in bpy.data.materials:
        return bpy.data.materials[PFX + name]
    t = NT(PFX + name)
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    n1_ = t.noise(P, scale, 8.0, 0.6)
    n2_ = t.noise(P, scale * 11.0, 5.0, 0.55)
    v1 = t.vor(P, scale * 0.35, "F1", 0, 1.0)
    col = t.cmix(t.maprange(n1_, 0.35, 0.7, 0.0, 1.0),
                 tuple(c * 0.80 for c in base), tuple(c * 1.18 for c in base))
    col = t.cmix(t.maprange(v1, 0.02, 0.35, 0.35, 0.0),
                 col, tuple(c * 0.62 for c in base))
    r = t.fmix(t.maprange(n2_, 0.3, 0.75, 0.0, 1.0), rough * 0.86, rough * 1.12)
    b = t.bump(t.math("ADD", t.math("MULTIPLY", n2_, 0.7),
                      t.math("MULTIPLY", v1, 0.5)), bumpstr, 0.004)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, 0, col)
    names = [i.name for i in bsdf.inputs]
    t.pin(bsdf, names.index("Roughness"), r)
    t.pin(bsdf, names.index("Normal"), b)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs[0])
    return t.m


def build_far_ground(coll, centre, half=900.0, cell=25.0):
    """The apron does not stop at 30 m and neither may the stand-in.

    Blender's Sky Texture returns BLACK below the horizon, so a finite ground
    patch renders as a hard black band across the frame behind the fence — an
    artefact of the test scene that would be read as a defect in the item.
    """
    n = int(2 * half / cell) + 1
    g = np.linspace(-half, half, n)
    X, Y = np.meshgrid(g + centre[0], g + centre[1], indexing="ij")
    Z, own = C.world_ground_z(X.ravel(), Y.ravel())
    Z = np.where(np.isfinite(Z), Z, 0.0).reshape(X.shape) - 0.004
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    Q = _grid_quads(n, n, close_m=False)
    me = bpy.data.meshes.new(STANDIN_PFX + "FarGround")
    me.from_pydata([tuple(v) for v in V], [], [tuple(q) for q in Q])
    me.update()
    ob = bpy.data.objects.new(STANDIN_PFX + "FarGround", me)
    ob.data.materials.append(mat_standin("Far", (0.140, 0.139, 0.131),
                                         0.86, 1.2, 0.10))
    coll.objects.link(ob)
    return ob


def build_ground(coll, centre, half=34.0, cell=0.18):
    n = int(2 * half / cell) + 1
    g = np.linspace(-half, half, n)
    X, Y = np.meshgrid(g + centre[0], g + centre[1], indexing="ij")
    Z, own = C.world_ground_z(X.ravel(), Y.ravel())
    Z = np.where(np.isfinite(Z), Z, 0.0).reshape(X.shape)
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    Q = _grid_quads(n, n, close_m=False)
    me = bpy.data.meshes.new(STANDIN_PFX + "Ground")
    me.from_pydata([tuple(v) for v in V], [], [tuple(q) for q in Q])
    me.update()
    ob = bpy.data.objects.new(STANDIN_PFX + "Ground", me)
    ob.data.materials.append(mat_standin("Concrete", (0.185, 0.183, 0.176),
                                         0.74, 22.0, 0.30))
    coll.objects.link(ob)
    return ob


def build_standins(coll, near, near_m=45.0, runs=None):
    """Proxy feet and couplers so the macro reads as an assembled fence."""
    A = np.asarray(near, float)[:, :2]
    mfoot = mat_standin("Precast", (0.150, 0.148, 0.142), 0.80, 28.0, 0.45)
    mgalv = mat_standin("Galv2", (0.150, 0.154, 0.160), 0.36, 90.0, 0.30)
    acc = Acc(STANDIN_PFX + "Feet")
    nf = 0
    for f in foot_sites(runs):
        p = np.array(f["world"], float)
        if np.sqrt(((p[:2][None, :] - A) ** 2).sum(-1)).min() > near_m:
            continue
        ax = np.array(f["axis_dir"], float)
        nv = np.array([-ax[1], ax[0], 0.0])
        z0 = f["ground_z"] - C.BASE_EMBED_M
        ctr = np.array([p[0], p[1], z0 + 0.075])
        ex, ey, ez = ax * 0.300, nv * 0.110, np.array([0.0, 0.0, 0.075])
        V = []
        for sz in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                for sx in (-1.0, 1.0):
                    ch = 0.86 if sz > 0 else 1.0
                    V.append(ctr + ex * sx * ch + ey * sy * ch + ez * sz)
        acc.solid(np.array(V),
                  quads=np.array([(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4),
                                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]), mat=0)
        # the two cups the spigots drop into — the read that says Heras block
        for (sp_w, r_) in f["spigots"]:
            c = np.array(sp_w, float)
            c = np.array([c[0], c[1], z0 + 0.150])
            ring = np.arange(10) * (2 * math.pi / 10)
            top = c[None, :] + np.stack([np.cos(ring) * (r_ + 0.012),
                                         np.sin(ring) * (r_ + 0.012),
                                         np.zeros(10)], 1)
            bot = top - np.array([0.0, 0.0, 0.055])
            VV = np.concatenate([top, bot, c[None, :] - [0, 0, 0.055]])
            j = np.arange(10)
            j1 = (j + 1) % 10
            QQ = np.stack([j, j1, 10 + j1, 10 + j], 1)
            TT = _fan(20, 10 + j)
            acc.solid(VV, quads=QQ, tris=TT, mat=0)
        nf += 1
    if nf:
        ob, _ = acc.build(coll, [mfoot], np.eye(3), np.zeros(3),
                          name=STANDIN_PFX + "Feet")
    acc = Acc(STANDIN_PFX + "Couplers")
    nc = 0
    for cp in coupler_sites(runs):
        if not cp["fitted"]:
            continue
        p = np.array(cp["world"], float)
        if np.sqrt(((p[:2][None, :] - A) ** 2).sum(-1)).min() > near_m:
            continue
        ax = np.array(cp["axis"], float)
        acr = np.array(cp["across"], float)
        out = np.cross(ax, acr)
        V = []
        for sz in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                for sx in (-1.0, 1.0):
                    V.append(p + acr * sx * 0.062 + out * sy * 0.030
                             + ax * sz * 0.021)
        V = np.array(V)
        Q = np.array([(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4),
                      (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)])
        acc.solid(V, quads=Q, mat=0)
        nc += 1
    if nc:
        acc.build(coll, [mgalv], np.eye(3), np.zeros(3),
                  name=STANDIN_PFX + "Couplers")
    log("stand-ins: %d foot blocks, %d couplers within %.0f m of the lens"
        % (nf, nc, near_m))


def _gap_aim(runs=None):
    """The best-lit missing panel with a standing neighbour on both sides."""
    slots = panel_slots(runs)
    by = {}
    for s in slots:
        by.setdefault((s.rid, s.seg), {})[s.k] = s
    best = None
    for key, d in by.items():
        for k, s in d.items():
            if s.present or s.tier > 1:
                continue
            if (k - 1) not in d or (k + 1) not in d:
                continue
            if not (d[k - 1].present and d[k + 1].present):
                continue
            sc = 3.0 - s.tier + abs(d[k - 1].lean - d[k + 1].lean)
            if best is None or sc > best[0]:
                best = (sc, s)
    if best is None:
        return None
    s = best[1]
    R, O = panel_frame(s)
    n = -R[1]
    if float(np.dot(n, np.array(C.SUN_DIR))) < 0:
        n = -n
    return R, O, n


def test_scene(samples=256, limit=None, quick=False):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 3.000 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # TWO hero sites, not one.  The best-lit damaged panel and the best gap in
    # the line are rarely the same panel, and a macro of whichever happens to
    # be prettiest is a claim about one object out of 771.
    # A is the RAKING-LIT read, which is where the material and the geometry
    # are judged.  B is the BACKLIT read at 155 deg, which is what the transit
    # camera actually gets for most of Beat 4 — a fence is a lattice against a
    # low sun and it has to survive that too.
    aimA = hero_aim(target_inc=62.0)
    aimB = hero_aim(target_inc=155.0, window=(140.0, 180.0),
                    exclude={(aimA["slot"].rid, aimA["slot"].k),
                             (aimA["slot"].rid, aimA["slot"].k + 1),
                             (aimA["slot"].rid, aimA["slot"].k - 1)})
    anchor = []
    for a in (aimA, aimB):
        R, O = panel_frame(a["slot"])
        surf = O + R[2] * 1.05
        el = math.radians(7.0)
        off = a["side"] * (-R[1]) * math.cos(el) \
            + np.array([0.0, 0.0, 1.0]) * math.sin(el)
        anchor += [tuple(surf + off / np.linalg.norm(off) * FILMED_AT_M),
                   tuple(surf)]

    gs = _gap_aim()
    if gs is not None:
        anchor.append((float(gs[1][0]), float(gs[1][1]), float(gs[1][2])))
    root = _coll(COLL)
    build(scene=scene, lod_anchor=anchor, limit=limit, coll=root)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=stand)

    macro, cam_p, surf = macro_rig(aimA, cams, PFX + "CAM_MACRO")
    macroB, camB_p, surfB = macro_rig(aimB, cams, PFX + "CAM_MACRO_B",
                                      yaw_deg=-22.0, elev_deg=2.0, height=0.72)
    gsite = _gap_aim()
    for a in (aimA, aimB):
        R, O = panel_frame(a["slot"])
        build_ground(stand, (float(O[0]), float(O[1])), half=30.0, cell=0.16)
    if gsite is not None:
        anchor.append((float(gsite[1][0]), float(gsite[1][1]), float(gsite[1][2])))
        build_ground(stand, (float(gsite[1][0]), float(gsite[1][1])),
                     half=26.0, cell=0.20)
    R0, O0 = panel_frame(aimA["slot"])
    build_far_ground(stand, (float(O0[0]), float(O0[1])))
    build_standins(stand, anchor, near_m=46.0)

    R, O = panel_frame(aimA["slot"])
    NY = aimA["side"] * (-R[1])           # unit vector out of the LIT face
    # a wider look so the run can be judged as a line rather than as an object
    add_camera(PFX + "CAM_WIDE",
               tuple(O + NY * 12.0 + R[0] * (-7.0) + np.array([0, 0, 1.75])),
               tuple(O + R[0] * 9.0 + np.array([0, 0, 0.95])), 40.0, cams)
    # straight down the line: the read that catches the lean chain and the gaps
    add_camera(PFX + "CAM_ALONG",
               tuple(O + R[0] * (-8.5) + NY * 1.35 + np.array([0, 0, 1.55])),
               tuple(O + R[0] * 22.0 + np.array([0, 0, 1.05])), 80.0, cams)
    # the foot: the spigot bore, the block, the bottom rail and the mud line.
    # AIMED AT THE UPRIGHT, not at the ground beside it — the first framing put
    # the stand-in foot block across the bottom half of the frame and the item
    # itself in a strip along the top.
    fx = float(aimA["spec"].xR)
    add_camera(PFX + "CAM_FOOT",
               tuple(O + NY * 0.62 + R[0] * (fx - 0.34) + R[2] * 0.40),
               tuple(O + R[0] * fx + R[2] * 0.14), 70.0, cams, fstop=16.0)
    # the fabric, square on: the crossings, the nuggets and the belly
    add_camera(PFX + "CAM_FABRIC",
               tuple(O + NY * 0.46 + R[2] * 1.15),
               tuple(O + R[2] * 1.15 - NY * 0.02), 85.0, cams, fstop=22.0)
    # the top corner: the bend, the shortening verticals and the sprayed band
    add_camera(PFX + "CAM_CORNER",
               tuple(O + NY * 0.75 + R[0] * (-1.15) + R[2] * 2.25),
               tuple(O + R[0] * (-1.45) + R[2] * 1.90), 70.0, cams, fstop=16.0)

    # THE GAP.  The manifest's note is "the lean and the gaps are the whole
    # read", so one camera does nothing but look at a missing panel: two open
    # spigots, two blocks still in place, the couplers hanging on nothing.
    g = _gap_aim()
    if g is not None:
        Rg, Og, ng = g
        add_camera(PFX + "CAM_GAP",
                   tuple(Og + ng * 4.4 + Rg[0] * (-2.2) + np.array([0, 0, 1.45])),
                   tuple(Og + np.array([0, 0, 0.85])), 45.0, cams)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 12.  MEASUREMENT  —  the things the gate cannot see
# ==============================================================================

def selftest():
    """Measure the population, the keep-out, the section and the interface.

    The gate measures four numbers about one blend.  These are the four the
    gate cannot ask: is the fence where a fence belongs, is any of it on the
    road, do the panels actually differ, and does the interface the five
    dependants build on return something a dependant could use.
    """
    ok = True
    print("=" * 78)
    print("heras_fence_panel selftest   (%.1f px/m at %.1f m / %.0f mm; "
          "1 px = %.3f mm)" % (PX_PER_M, FILMED_AT_M, LENS_MM, PX_M * 1000))
    print("=" * 78)

    def chk(label, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("   %-4s %s%s" % ("PASS" if cond else "FAIL", label,
                                ("   " + detail) if detail else ""))

    # ---- 1. the population -------------------------------------------------
    slots = panel_slots()
    pres = [s for s in slots if s.present]
    gaps = [s for s in slots if not s.present]
    fence_m = sum(s.w for s in slots)
    print("\n1. THE PROGRAMME")
    print("   %d slots on %d runs, %.0f m of fence line" %
          (len(slots), len(RUNS), fence_m))
    print("   %d panels standing, %d gaps (%.1f %%)" %
          (len(pres), len(gaps), 100.0 * len(gaps) / max(len(slots), 1)))
    from collections import Counter
    wc = Counter(round(s.w, 3) for s in slots)
    print("   widths: " + ", ".join("%.1f m x%d" % (k, v)
                                    for k, v in sorted(wc.items())))
    chk("population is within 15 %% of the manifest's %d" % DECLARED_INSTANCES,
        abs(len(slots) - DECLARED_INSTANCES) / DECLARED_INSTANCES < 0.15,
        "%d slots" % len(slots))
    chk("more than one panel width exists", len(wc) >= 3)

    # ---- 2. the keep-out ---------------------------------------------------
    print("\n2. KEEP-OUT  (nothing on the road, the ribbon or a building)")
    P = np.array([s.c for s in pres])
    okp, zz = placeable(P[:, 0], P[:, 1])
    s_, u_ = C.project(P[:, 0], P[:, 1])
    clear = np.abs(u_) - (C.half_width(s_) + C.KERB_W + C.VERGE_W)
    print("   closest standing panel to the racing surface edge: %.2f m" %
          clear.min())
    chk("every standing panel is placeable", okp.all(),
        "%d rejected" % int((~okp).sum()))
    chk("no panel within %.1f m of the racing surface" % _ROAD_PAD,
        clear.min() > _ROAD_PAD)
    rib = C.in_access_ribbon(P[:, 0], P[:, 1], margin=0.0)
    chk("no panel inside the access ribbon", not rib.any())
    T = np.linspace(0.0, C.ACCESS_TOTAL, 1500)
    X, Y, H = C.access_route_arrays(T)
    d = np.sqrt(((P[:, None, 0] - X[None, :]) ** 2
                 + (P[:, None, 1] - Y[None, :]) ** 2)).min()
    print("   closest standing panel to the transit ROUTE CENTRELINE: %.2f m"
          % d)
    print("   (the manifest films this item at %.1f m; a camera %.2f m off the"
          % (FILMED_AT_M, max(0.0, d - FILMED_AT_M)))
    print("    route centreline reaches it.  The 12.0 m ribbon allows 6.0 m.)")

    # ---- 3. the panels differ ----------------------------------------------
    print("\n3. VARIATION  (the manifest names four axes)")
    specs = [Spec(s.seed, width=s.w, lod=3) for s in pres[:400]]
    print("   lean            %+.2f .. %+.2f deg, sd %.2f" %
          (min(s.lean for s in pres), max(s.lean for s in pres),
           float(np.std([s.lean for s in pres]))))
    nd = Counter(len(sp.dents) for sp in specs)
    print("   dents/panel     " + ", ".join("%d:%d" % (k, v)
                                            for k, v in sorted(nd.items())))
    print("   bloom           %.2f .. %.2f" % (min(sp.bloom for sp in specs),
                                               max(sp.bloom for sp in specs)))
    print("   top style       round %d / square %d" %
          (sum(1 for sp in specs if sp.round_top),
           sum(1 for sp in specs if not sp.round_top)))
    print("   horizontals     " + ", ".join(
        "%d:%d" % (k, v) for k, v in sorted(Counter(sp.n_h for sp in specs).items())))
    print("   verticals       %d .. %d" % (min(sp.n_v for sp in specs),
                                           max(sp.n_v for sp in specs)))
    print("   cut wires       %d panels, bent-aside %d panels" %
          (sum(1 for sp in specs if sp.cut_v),
           sum(1 for sp in specs if sp.bent_v)))
    print("   asset tag       %d of %d" % (sum(1 for sp in specs if sp.tag),
                                           len(specs)))
    sig = set((sp.n_v, sp.n_h, len(sp.dents), len(sp.cut_v), len(sp.bent_v),
               sp.round_top, sp.tag, round(sp.w, 3)) for sp in specs)
    chk("distinct topology signatures across the first 400 panels",
        len(sig) >= 40, "%d" % len(sig))
    chk("panel widths vary (gate needs cv_size >= 0.03)",
        float(np.std([s.w for s in pres]) / np.mean([s.w for s in pres])) > 0.03,
        "cv_w = %.4f" % float(np.std([s.w for s in pres])
                              / np.mean([s.w for s in pres])))

    # ---- 4. the section resolves ------------------------------------------
    print("\n4. THE SECTION AT %.1f m  (limit %.2f mm = 6 px)" %
          (FILMED_AT_M, DETAIL_LIMIT_M * 1000))
    for lod in (3, 2, 1, 0):
        L = LOD[lod]
        wchord = 2.0 * WIRE_R * math.sin(math.pi / L["ws"])
        fchord = 2.0 * TUBE_R * math.sin(math.pi / L["fs"])
        print("   lod %d  wire facet %5.2f mm = %5.2f px   frame facet %5.2f mm"
              " = %5.2f px" % (lod, wchord * 1000, wchord * PX_PER_M,
                               fchord * 1000, fchord * PX_PER_M))
        if lod == 3:
            chk("hero wire facet resolves below 6 px",
                wchord * PX_PER_M <= 6.0)
            chk("hero frame facet resolves below 6 px",
                fchord * PX_PER_M <= 6.0)
    sp = Spec(12345, lod=3)
    print("   mesh depth (two layers)      %5.2f mm = %5.2f px" %
          ((Y_H - Y_V + 2 * sp.wire_r) * 1000,
           (Y_H - Y_V + 2 * sp.wire_r) * PX_PER_M))
    print("   frame proud of the fabric    %5.2f mm = %5.2f px" %
          ((sp.tube_r + Y_H) * 1000, (sp.tube_r + Y_H) * PX_PER_M))
    print("   spigot wall                  %5.2f mm = %5.2f px" %
          (sp.wall * 1000, sp.wall * PX_PER_M))
    print("   crossings per 3.5 m panel    %d verticals x %d horizontals = %d"
          % (sp.n_v, sp.n_h, sp.n_v * sp.n_h))

    # ---- 5. the interface --------------------------------------------------
    print("\n5. THE INTERFACE THE FIVE DEPENDANTS BUILD ON")
    feet = foot_sites()
    coup = coupler_sites()
    scr = scrim_sites()
    ties = tie_sites()
    ends = run_ends()
    print("   foot_sites()     %4d blocks   (manifest heras_fence_foot: 950)"
          % len(feet))
    print("   coupler_sites()  %4d joints   (manifest heras_fence_coupler: 900,"
          " %d unfitted)" % (len(coup), sum(1 for c in coup if not c["fitted"])))
    print("   scrim_sites()    %4d panels   (manifest heras_banner_scrim: 320,"
          " %.0f %% of standing)" % (len(scr), 100.0 * len(scr) / max(len(pres), 1)))
    print("   tie_sites()      %4d points" % len(ties))
    print("   run_ends()       %4d ends" % len(ends))
    chk("every foot site has a finite ground z from world_ground_z",
        all(np.isfinite(f["ground_z"]) for f in feet))
    zg = np.array([f["ground_z"] for f in feet])
    chk("no foot site sits on an assumed z",
        len(set(np.round(zg, 6))) > 1 or abs(C.APRON_Z) < 1e-9,
        "%d distinct ground heights" % len(set(np.round(zg, 4))))
    chk("scrim coverage is near the manifest's 35 %%",
        0.28 <= len(scr) / max(len(pres), 1) <= 0.42)
    chk("coupler unfitted fraction is near the manifest's 8 %%",
        0.03 <= sum(1 for c in coup if not c["fitted"]) / max(len(coup), 1) <= 0.14)

    # ---- 6. determinism ----------------------------------------------------
    print("\n6. DETERMINISM")
    _SLOTS_CACHE.clear()
    again = panel_slots()
    same = (len(again) == len(slots)
            and all(abs(a.lean - b.lean) < 1e-12 and a.present == b.present
                    and abs(a.w - b.w) < 1e-12
                    for a, b in zip(again, slots)))
    chk("rebuilding gives the same population", same)

    print("\n" + "=" * 78)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    print("=" * 78)
    return ok


# ==============================================================================
# 13.  CLI
# ==============================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true",
                    help="build the acceptance scene")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--save", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=256)
    a = ap.parse_args(argv)

    if a.selftest or not (a.test or a.save):
        selftest()
        if not a.test:
            return
    if not HAVE_BPY:
        raise SystemExit("REFUSING: --test needs Blender.")
    t0 = time.time()
    test_scene(samples=a.samples, limit=a.limit)
    if a.save:
        out = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        # NOTHING may leave here with an external dependency.
        rem = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if rem:
            raise SystemExit("REFUSING TO SAVE: external images %s" % rem)
        bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False,
                                    compress=False)
        log("saved %s (%.1f MB) in %.0f s"
            % (out, os.path.getsize(out) / 1048576.0, time.time() - t0))
    log("STAGE RESULT: HERAS_FENCE_PANEL_BUILT")


if __name__ == "__main__":
    main()
