#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marshal_post_column.py — THE marshal post frame column.  Item 130, wave 1.

    manifest:  nearest_camera_m 6.0   lens 35 mm   onscreen_px_4k 1742
               instances 120          hero True    beats ['5']
               variation_axes: scaffold tube vs box section / base plate & pins
                               / paint
    pixels:    px_per_m = (3840 * 35 / 36) / 6.0 = 622.2 px/m
               -> 1 screen pixel = 1.607 mm on this column.

Everything at or above ~1.6 mm is a resolved feature and therefore MESH:
a 48.3 mm scaffold tube is 30 px across, a 24 mm A/F nut is 15 px, an M16
thread pitch is 1.25 px, a weld ripple is 1.7 px, the 3.2 mm annulus of an
open tube end is 2 px, a saw burr is 1 px.  None of that can be a shader.

WHAT IS AND IS NOT GEOMETRY, AND WHY
    MESH   tube ovality/bow/lean, knock dents (0.8-3.5 mm deep) with their
           raised lips, hot-dip zinc runs, the ERW seam ridge, saw-cut ends
           with real wall annulus and burr, plastic end caps, right-angle and
           swivel couplers (rolled saddle bands, hinge rivets, T-bolts, 22 mm
           nuts, protruding thread), M16 anchor studs with a REAL helical
           thread, hex nuts with their 30 deg chamfer, washers, base plates
           with drilled and chamfered holes, adjustable base-jack Acme threads
           and collar nuts, fillet welds with stack-of-dimes ripple, gussets,
           drilled fixing holes with burrs, welded bracket lugs, driven ground
           pins with hammer-mushroomed heads, sole boards, nails, cable ties
           with their ratchet heads, twisted tie wire, inspection tags.
    SHADER paint chips.  A paint film is 0.15 mm thick = 0.09 px, so its
           RELIEF is genuinely sub-pixel and its COLOUR BOUNDARY is the thing
           that reads.  Chips, primer, rust bleed, zinc spangle, white rust,
           mud splash and chalking are therefore shader work — stated here so
           nobody has to wonder whether it was an oversight.

===========================================================================
THE INTERFACE  (this item is a FOUNDATION.  marshal_post_deck,
                marshal_post_roof, marshal_post_screen, marshal_post_sign,
                marshal_telephone and marshal_light_panel all build on it and
                cannot ask questions.  Everything below is public and stable.)
===========================================================================

FRAMES
    Frame                       .o origin, .x .y .z orthonormal axes, .r a
                                characteristic radius (m), .tag a string.
                                .mat4() -> 4x4 numpy.  Every mount point in
                                this module is a Frame.

THE PLAN LAYER (no Blender, no geometry — call it to find out where things go)
    post_frame(uid)             -> PostFrameSpec.  Deterministic from uid.
    PostFrameSpec
        .uid .kind .paint        'tube' | 'shs' | 'angle' | 'shoe'
        .W .D                    frame width (across the front) and depth (m)
        .plat                    deck height above grade (0.0 for ground level)
        .head_z                  top of the corner columns (m above grade)
        .columns                 [ColumnSpec], each with .pos = (x, y) in the
                                 POST-LOCAL frame and .role
        .mounts                  dict name -> Frame, POST-LOCAL.  ONLY the
                                 frames that are exact without building:
                                 foot_<role>, head_nominal_<role> and
                                 deck_level_<role>.  Anything that hangs off a
                                 FITTING is not here, because it moves with the
                                 leg's lean, bow and kink -- ask a BUILT
                                 PostFrame for those.

POST-LOCAL FRAME — the convention every dependant must use
        origin  the post's ground point (world z from world_ground_z)
        +X      along the frame width, to the RIGHT looking from the track
        +Y      AWAY from the track  (so the open front is at -Y and looks at
                the circuit; the back wall is at +Y).  This is the same
                convention build_dressing.build_marshal_post already uses.
        +Z      up

MOUNT NAMES.  On a ColumnSpec/Column they are unsuffixed and POST-LOCAL; on a
built PostFrame every one is suffixed with its column's role (fl / fr / rl /
rr / mid_rear / mast / brace_n) and is in WORLD coordinates.  Print
`sorted(pf.mounts)` on any built post to see exactly what that post grew.

        foot_<role>             the column's ground point.  .z up.
        head_<role>             top of the column.  .r = the section's
                                circumscribed radius.  ROOF BEARING.
        deck_seat_<role>        the coupler or welded cleat that carries the
                                deck bearer.  .o is the free end of the stub,
                                .x runs along the bearer.  marshal_post_deck
                                lands its bearers here.
        deck_level_<role>       on a raised post only: the point on the column
                                axis at deck height.
        roof_seat_<role>        the coupler that carries the roof bearer.
        <role>_ledger_<n>       EVERY coupler / welded bracket on that column,
                                in build order.  .o is the FREE END of the
                                115-175 mm ledger stub this module already
                                built, .x is the axis pointing away from the
                                column, .r is the stub radius.  A dependant
                                continues its member from .o along .x -- the
                                stub is the coupler's own captured tube and is
                                NOT the dependant's member.  The tag that says
                                what a given ledger is for lives beside it as
                                `ledger_<n>_tag` on the COLUMN's mounts dict
                                ('deck_bearer', 'deck_transom', 'roof_bearer',
                                'roof_purlin', 'screen_rail', 'phone_rail',
                                'brace').
        screen_face[_<role>]    a U-bolt saddle at 0.95-1.30 m above the deck,
                                already bolted to the column, with a backing
                                plate.  .y is the OUTWARD normal, .o is on the
                                plate's outer face, .r its half width.
                                marshal_post_screen bolts to this plate.
        sign_band               the same fitting on the front-left column at
                                1.52-1.94 m.  marshal_post_sign.
        phone_lug               a welded 6 mm lug with two M10 holes on the
                                rear or mid-rear column at 1.12-1.36 m.
                                marshal_telephone.
        panel_mount             a U-bolt saddle near the top of the mast.
        panel_mast_top          top of the light-panel mast column.  Absent on
                                the ~45 % of posts that have no mast -- test
                                for it, do not assume it.

BUILD
    materials()                 -> [galv, paint, forged, timber, grout, poly]
                                idempotent, named 'MPC_*'.  Slot order is
                                MAT_GALV/MAT_PAINT/MAT_FORGED/MAT_TIMBER/
                                MAT_GROUT/MAT_POLY = 0..5.
    build_column(spec, coll, mats, name=None, place=None) -> Column
                                ONE column, its own vertex data, recentred on
                                emit.  Object name 'MPC_<name>'.
    build_post_frame(spec, coll, mats, place=None) -> PostFrame
                                one post's whole set of columns.
    build(coll_name='MPC_Columns', n_posts=25, seed=0, stations=None)
                                -> [PostFrame].  Places against
                                world_contract.world_ground_z, never an assumed
                                z, and records the value used on every object
                                as ['mpc_world_ground_z'].
    post_plan(n=25, seed=0)     -> [dict(s, side, lat, ...)] stations around
                                the lap, standing off the barrier face and
                                clamped inside platform_edge.

THE HARD-SURFACE TOOLKIT (reusable — every marshal_* and most trackside items
need bolts, welds and sections, and re-deriving them 30 times is how a world
stops looking like one world)
    Acc                         vertex/face accumulator with absolute index
                                control, per-vertex uv/base/aux/wear channels
                                and a recentre-on-emit.
    sweep(acc, C, U, V, S, ...)  general closed-section sweep.
    circle_section / rrect_section / angle_section / lsect_edges
    open_end(...)               saw-cut tube end: wall annulus, burr, bore.
    plate(...)                  rectangular plate, chamfered, with real drilled
                                and chamfered holes.
    hex_nut(...) washer(...) thread_stud(...) dome_head(...)
    weld_bead(...)              fillet weld with stack-of-dimes ripple.
    section_fillet_weld(...)    the same, run round a swept section's foot.
    cable_tie(...) tie_wire(...) tag_plate(...) nail(...) ground_pin(...)

PER-VERTEX CHANNELS (the shader contract)
    uv    (u, v)   METRES: u around the section, v along the member.
    base  RGBA     paint colour (linear) + A = member id in [0,1]
    aux   RGBA     (edge_exposure, weld, machined, uid)
    wear  RGBA     (chip, dirt, rust, age)

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/marshal_post_column.py -- --test \
        --out world/items/marshal_post_column_test.blend
"""

import math
import os
import sys

import numpy as np

try:
    import bpy
except ImportError:                                       # plan layer only
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLD)
for _p in (WORLD, os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                # noqa: E402
import itemkit as K                                               # noqa: E402

PFX = "MPC_"
ROOT_COLL = "MPC_Columns"
SENSOR_MM = 36.0

MAT_GALV, MAT_PAINT, MAT_FORGED, MAT_TIMBER, MAT_GROUT, MAT_POLY = range(6)
MAT_NAMES = ["Galv", "Paint", "Forged", "Timber", "Grout", "Poly"]

TAU = 2.0 * math.pi


# --------------------------------------------------------------------------- #
#  1.  determinism                                                              #
# --------------------------------------------------------------------------- #

def hash01(*keys):
    """[0,1) from any tuple of numbers/strings.  Same idiom as the other items."""
    h = 2166136261
    for k in keys:
        s = k if isinstance(k, str) else ("%.7g" % float(k))
        for ch in s:
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h ^= (h >> 13)
    h = (h * 2654435761) & 0xFFFFFFFF
    h ^= (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0


def rnd(a, b, *keys):
    return a + (b - a) * hash01(*keys)


def rint(a, b, *keys):
    return int(a + (b - a + 1) * hash01(*keys) * 0.999999)


def chance(p, *keys):
    return hash01(*keys) < p


def pick(seq, *keys):
    return seq[int(hash01(*keys) * len(seq) * 0.999999)]


def srgb(hexs):
    """'#rrggbb' -> linear rgb tuple."""
    h = hexs.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[i * 2:i * 2 + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# --------------------------------------------------------------------------- #
#  2.  the accumulator                                                          #
# --------------------------------------------------------------------------- #

class Acc:
    """Vertex/face accumulator with ABSOLUTE index control.

    Per-vertex channels (the shader contract, see the module docstring):
        uv    (u, v)  in METRES: u around the section, v along the member.
        base  RGBA    paint colour (linear) + A = member id
        aux   RGBA    (edge_exposure, weld, machined, uid)
        wear  RGBA    (chip, dirt, rust, age)
    """

    __slots__ = ("name", "_V", "_UV", "_B", "_A", "_W",
                 "_Fq", "_Ft", "_Mq", "_Mt", "_Sq", "_St", "_n")

    def __init__(self, name):
        self.name = name
        self._V, self._UV, self._B, self._A, self._W = [], [], [], [], []
        self._Fq, self._Ft = [], []
        self._Mq, self._Mt = [], []
        self._Sq, self._St = [], []
        self._n = 0

    # -- vertices ----------------------------------------------------------
    def verts(self, P, uv=None, base=(0.1, 0.1, 0.1, 0.0),
              aux=(0.0, 0.0, 0.0, 0.0), wear=(0.0, 0.0, 0.0, 0.0)):
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
        IDX = np.asarray(IDX, np.int64)
        R, Cu = IDX.shape
        if R < 2 or Cu < 2:
            return
        j1 = (np.arange(Cu) + 1) % Cu if wrap_u else np.arange(1, Cu)
        j0 = np.arange(Cu) if wrap_u else np.arange(Cu - 1)
        A = IDX[:-1][:, j0]
        B = IDX[:-1][:, j1]
        Cc = IDX[1:][:, j1]
        D = IDX[1:][:, j0]
        Q = np.stack([A, B, Cc, D], -1).reshape(-1, 4)
        if flip:
            Q = Q[:, ::-1]
        self.quads(Q, mat, smooth)

    def fan(self, ring, ctr_idx, mat=0, smooth=False, flip=False, wrap=True):
        ring = np.asarray(ring, np.int64).ravel()
        j1 = (np.arange(len(ring)) + 1) % len(ring) if wrap else \
            np.arange(1, len(ring))
        j0 = np.arange(len(ring)) if wrap else np.arange(len(ring) - 1)
        T = np.stack([np.full(len(j0), ctr_idx), ring[j0], ring[j1]], -1)
        if flip:
            T = T[:, ::-1]
        self.tris(T, mat, smooth)

    # -- placement ---------------------------------------------------------
    def xform(self, R=None, t=None):
        """Apply a rotation and translation to everything accumulated so far."""
        if not self._V:
            return
        V = np.concatenate(self._V, 0)
        if R is not None:
            V = V @ np.asarray(R, float).T
        if t is not None:
            V = V + np.asarray(t, float).reshape(1, 3)
        self._V = [V]

    @property
    def n(self):
        return self._n

    def bounds(self):
        V = np.concatenate(self._V, 0)
        return V.min(0), V.max(0)

    # -- realise ------------------------------------------------------------
    def emit(self, coll, mats, name=None, shade_smooth_angle=None):
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
            mm.append(np.concatenate(self._Mt))
            ss.append(np.concatenate(self._St))
        if self._Fq:
            Q = np.concatenate(self._Fq, 0)
            polys.append((4, Q))
            mm.append(np.concatenate(self._Mq))
            ss.append(np.concatenate(self._Sq))
        if not polys:
            return None
        loops = np.concatenate([F.ravel() for _k, F in polys]).astype(np.int32)
        ltot = np.concatenate([np.full(len(F), k, np.int32) for k, F in polys])
        lstart = np.zeros(len(ltot), np.int32)
        np.cumsum(ltot[:-1], out=lstart[1:])
        M = np.concatenate(mm)
        S = np.concatenate(ss)

        # LAW 6: recentre on emit.  |P| ~ 1000 m kills float32 inside any
        # procedural, and every material here reads TexCoord -> Object.
        ctr = 0.5 * (V.min(0) + V.max(0))
        V = V - ctr

        nm = (name or self.name)
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


def chan(val, M, K):
    """Broadcast a channel to (M, K, 4)."""
    a = np.asarray(val, float)
    if a.ndim == 1:
        return np.broadcast_to(a[None, None, :], (M, K, 4))
    if a.ndim == 2 and a.shape[0] == M and a.shape[1] == 4:
        return np.broadcast_to(a[:, None, :], (M, K, 4))
    if a.ndim == 2 and a.shape[0] == K and a.shape[1] == 4:
        return np.broadcast_to(a[None, :, :], (M, K, 4))
    return a.reshape(M, K, 4)


# --------------------------------------------------------------------------- #
#  3.  frames and small vector helpers                                          #
# --------------------------------------------------------------------------- #

def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


class Frame:
    """A mount point.  .o origin, .x/.y/.z orthonormal axes, .r a radius."""

    __slots__ = ("o", "x", "y", "z", "r", "tag")

    def __init__(self, o, x, y, z, r=0.03, tag=""):
        self.o = np.asarray(o, float)
        self.x = unit(x)
        self.y = unit(y)
        self.z = unit(z)
        self.r = float(r)
        self.tag = tag

    def mat4(self):
        M = np.eye(4)
        M[:3, 0] = self.x
        M[:3, 1] = self.y
        M[:3, 2] = self.z
        M[:3, 3] = self.o
        return M

    def transformed(self, R, t):
        R = np.asarray(R, float)
        return Frame(R @ self.o + np.asarray(t, float), R @ self.x,
                     R @ self.y, R @ self.z, self.r, self.tag)

    def __repr__(self):
        return "Frame(%s o=%s r=%.4f)" % (self.tag, np.round(self.o, 4), self.r)


def rotz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_axis(axis, deg):
    a = math.radians(deg)
    k = unit(np.asarray(axis, float))
    K = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.eye(3) + math.sin(a) * K + (1.0 - math.cos(a)) * (K @ K)


def frames_along(P, ref=(1.0, 0.0, 0.0)):
    """Parallel-transported orthonormal frames along a polyline.  -> T, U, V."""
    P = np.asarray(P, float)
    M = len(P)
    T = np.empty((M, 3))
    T[:-1] = P[1:] - P[:-1]
    T[-1] = T[-2]
    if M > 2:
        T[1:-1] = 0.5 * (P[2:] - P[:-2])
    T = unit(T)
    U = np.empty((M, 3))
    r = np.asarray(ref, float)
    u0 = r - T[0] * float(np.dot(r, T[0]))
    if np.linalg.norm(u0) < 1e-9:
        r = np.array([0.0, 1.0, 0.0])
        u0 = r - T[0] * float(np.dot(r, T[0]))
    U[0] = unit(u0)
    for i in range(1, M):
        u = U[i - 1] - T[i] * float(np.dot(U[i - 1], T[i]))
        if np.linalg.norm(u) < 1e-9:
            u = np.cross(T[i], U[i - 1])
        U[i] = unit(u)
    V = np.cross(T, U)
    return T, U, V


def angdiff(a, b):
    d = (np.asarray(a, float) - b + math.pi) % TAU - math.pi
    return d


# --------------------------------------------------------------------------- #
#  4.  sections                                                                 #
# --------------------------------------------------------------------------- #

def circle_section(n, r):
    """CCW closed circle, (n,2), plus a uniform edge-exposure array."""
    th = np.arange(n) * TAU / n
    S = np.stack([np.cos(th), np.sin(th)], -1) * r
    return S, np.full(n, 0.28), th


def _arc(cx, cy, r, a0, a1, n):
    a = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], -1)


def rrect_section(w, h, cr, nc=8, ns=6):
    """CCW rounded-rectangle, centred.  -> (K,2), edge (K,).

    `edge` is 1.0 at the middle of each corner arc and 0.10 on the flats: that
    is exactly where paint chips off a box section and where the zinc polishes.
    """
    hw, hh = w * 0.5, h * 0.5
    xi, yi = hw - cr, hh - cr
    pts, edg = [], []
    corners = [(xi, -yi, -math.pi / 2, 0.0), (xi, yi, 0.0, math.pi / 2),
               (-xi, yi, math.pi / 2, math.pi),
               (-xi, -yi, math.pi, 1.5 * math.pi)]
    # side runs, taken in the same order: +x face, +y face, -x face, -y face
    for i, (cx, cy, a0, a1) in enumerate(corners):
        A = _arc(cx, cy, cr, a0, a1, nc)
        pts.append(A)
        t = np.linspace(-1.0, 1.0, nc)
        edg.append(0.10 + 0.90 * np.exp(-(t * 1.35) ** 2))
        b0 = A[-1]
        nxt = corners[(i + 1) % 4]
        b1 = _arc(nxt[0], nxt[1], cr, nxt[2], nxt[3], nc)[0]
        if ns > 0:
            f = np.linspace(0.0, 1.0, ns + 2)[1:-1]
            pts.append(b0[None, :] + (b1 - b0)[None, :] * f[:, None])
            edg.append(np.full(ns, 0.10))
    S = np.concatenate(pts, 0)
    E = np.concatenate(edg, 0)
    return S, E


def angle_section(a, b, t, r_root=0.008, r_toe=0.004, nc=6, ns=5):
    """CCW equal/unequal steel angle, origin at the outer heel.  -> (K,2), edge.

    Laid out with the heel at (-a/2, -b/2) so the section is roughly centred.
    """
    x0, y0 = -a * 0.5, -b * 0.5
    x1, y1 = x0 + a, y0 + b
    pts, edg = [], []

    def line(p, q, n, e):
        f = np.linspace(0.0, 1.0, n + 1)[:-1]
        pts.append(np.asarray(p)[None, :] + (np.asarray(q) - np.asarray(p))[None, :]
                   * f[:, None])
        edg.append(np.full(n, e))

    ro = 0.0025                                     # outer heel radius
    # outer heel corner
    pts.append(_arc(x0 + ro, y0 + ro, ro, math.pi, 1.5 * math.pi, nc))
    edg.append(np.full(nc, 0.85))
    line((x0 + ro, y0), (x1 - r_toe, y0), ns * 2, 0.10)
    # toe of the horizontal leg
    pts.append(_arc(x1 - r_toe, y0 + r_toe, r_toe, -math.pi / 2, 0.0, nc))
    edg.append(np.full(nc, 1.00))
    line((x1, y0 + r_toe), (x1, y0 + t - r_toe), 2, 0.55)
    pts.append(_arc(x1 - r_toe, y0 + t - r_toe, r_toe, 0.0, math.pi / 2, nc))
    edg.append(np.full(nc, 0.95))
    line((x1 - r_toe, y0 + t), (x0 + t + r_root, y0 + t), ns * 2, 0.10)
    # inner root fillet
    pts.append(_arc(x0 + t + r_root, y0 + t + r_root, r_root,
                    1.5 * math.pi, math.pi, nc))
    edg.append(np.full(nc, 0.05))
    line((x0 + t, y0 + t + r_root), (x0 + t, y1 - r_toe), ns * 2, 0.10)
    pts.append(_arc(x0 + t - r_toe, y1 - r_toe, r_toe, 0.0, math.pi / 2, nc))
    edg.append(np.full(nc, 0.95))
    line((x0 + t - r_toe, y1), (x0 + r_toe, y1), 2, 0.55)
    pts.append(_arc(x0 + r_toe, y1 - r_toe, r_toe, math.pi / 2, math.pi, nc))
    edg.append(np.full(nc, 1.00))
    line((x0, y1 - r_toe), (x0, y0 + ro), ns * 2, 0.10)
    S = np.concatenate(pts, 0)
    E = np.concatenate(edg, 0)
    return S, E


def section_outward(S):
    """Outward 2D normals of a CCW closed section.  -> (K,2)."""
    S = np.asarray(S, float)
    nxt = np.roll(S, -1, 0)
    prv = np.roll(S, 1, 0)
    d1 = nxt - S
    d2 = S - prv
    n1 = np.stack([d1[:, 1], -d1[:, 0]], -1)
    n2 = np.stack([d2[:, 1], -d2[:, 0]], -1)
    return unit(n1 + n2)


def section_perimeter_u(S):
    """Cumulative perimeter coordinate (metres) round a closed section."""
    d = np.linalg.norm(np.roll(S, -1, 0) - S, axis=1)
    return np.concatenate([[0.0], np.cumsum(d)[:-1]])


# --------------------------------------------------------------------------- #
#  5.  the sweep                                                                #
# --------------------------------------------------------------------------- #

def sweep(acc, Cp, U, V, S, mat=0, base=(0.1, 0.1, 0.1, 0.0),
          aux=(0.0, 0.0, 0.0, 0.0), wear=(0.0, 0.0, 0.0, 0.0),
          edge=None, smooth=True, close_u=True, vcoord=None, flip=False,
          uoff=0.0, faces=True):
    """Sweep a closed section along a framed path.

    Cp (M,3) centres; U, V (M,3) section axes; S (K,2) or (M,K,2) section.
    -> the (M,K) absolute index grid, so callers can bridge to it.
    """
    Cp = np.asarray(Cp, float)
    U = np.asarray(U, float)
    V = np.asarray(V, float)
    S = np.asarray(S, float)
    M = len(Cp)
    if S.ndim == 2:
        S = np.broadcast_to(S[None, :, :], (M, S.shape[0], 2))
    K = S.shape[1]
    # Cp may be (M,3) -- one centre per ring -- or (M,K,3), a per-VERTEX centre,
    # which is what a hand-trowelled mortar collar needs: its top rim is ragged
    # in z as well as in radius, and that cannot be expressed in a 2D section.
    if Cp.ndim == 3:
        Cctr = Cp.mean(1)
        P = Cp + S[:, :, 0:1] * U[:, None, :] + S[:, :, 1:2] * V[:, None, :]
    else:
        Cctr = Cp
        P = (Cp[:, None, :] + S[:, :, 0:1] * U[:, None, :]
             + S[:, :, 1:2] * V[:, None, :])
    uu = section_perimeter_u(S.mean(0)) + uoff
    if vcoord is None:
        seg = np.linalg.norm(np.diff(Cctr, axis=0), axis=1)
        vv = np.concatenate([[0.0], np.cumsum(seg)])
    else:
        vv = np.broadcast_to(np.asarray(vcoord, float), (M,))
    UVg = np.stack([np.broadcast_to(uu[None, :], (M, K)),
                    np.broadcast_to(vv[:, None], (M, K))], -1)
    A = np.array(chan(aux, M, K), float)
    if edge is not None:
        e = np.asarray(edge, float)
        A[..., 0] = e[None, :] if e.ndim == 1 else e
    i0 = acc.verts(P.reshape(-1, 3), uv=UVg.reshape(-1, 2),
                   base=chan(base, M, K).reshape(-1, 4),
                   aux=A.reshape(-1, 4),
                   wear=chan(wear, M, K).reshape(-1, 4))
    IDX = i0 + np.arange(M * K).reshape(M, K)
    if faces:
        acc.grid_faces(IDX, mat, smooth, wrap_u=close_u, flip=flip)
    return IDX


def bridge(acc, IA, IB, mat=0, smooth=False, wrap=True, flip=False):
    """Quad strip between two equal-length index rings."""
    IA = np.asarray(IA, np.int64).ravel()
    IB = np.asarray(IB, np.int64).ravel()
    acc.grid_faces(np.stack([IA, IB], 0), mat, smooth, wrap_u=wrap, flip=flip)


# --------------------------------------------------------------------------- #
#  6.  hard-surface primitives                                                  #
# --------------------------------------------------------------------------- #

def open_end(acc, c, u, v, w, S, wall, mat, base, aux, wear, edge=None,
             depth=0.045, burr=0.00018, uid=0.0, dirn=1.0):
    """A saw-cut open end of a hollow section.

    c centre of the end plane, (u, v) the section axes, w the OUTWARD axis.
    Builds: the end annulus (wall thick — 3.2 mm is 2 screen px and it is the
    single cue that says 'tube' rather than 'rod'), a saw burr on the outer
    arris, the bore going `depth` in, and a dark closure at the bottom of it.
    """
    S = np.asarray(S, float)
    K = len(S)
    nrm = section_outward(S)
    th = np.arctan2(S[:, 1], S[:, 0])
    br = burr * (0.35 + 0.65 * np.array([hash01(uid, "burr", k) for k in range(K)]))
    S_out = S + nrm * br[:, None]
    S_in = S - nrm * wall
    axm = np.asarray(w, float) * dirn

    def ring(sec, off):
        P = (np.asarray(c, float)[None, :] + sec[:, 0:1] * np.asarray(u)[None, :]
             + sec[:, 1:2] * np.asarray(v)[None, :] + axm[None, :] * off)
        uvv = np.stack([section_perimeter_u(sec), np.full(K, off)], -1)
        a = np.tile(np.asarray(aux, float).reshape(1, 4), (K, 1))
        if edge is not None:
            a[:, 0] = np.asarray(edge, float)
        return P, uvv, a

    rings = []
    # outer arris (with burr), end face, inner arris, then the bore
    specs = [(S_out, 0.0, 0.9, 0.25), (S_in, 0.0, 0.55, 1.0),
             (S_in, -0.0016, 0.2, 1.0), (S_in, -depth * 0.45, 0.05, 0.85),
             (S_in, -depth, 0.02, 0.6)]
    for (sec, off, ee, mc) in specs:
        P, uvv, a = ring(sec, off)
        a[:, 0] = ee
        a[:, 2] = mc
        i0 = acc.verts(P, uv=uvv, base=base, aux=a, wear=wear)
        rings.append(i0 + np.arange(K))
    for i in range(len(rings) - 1):
        bridge(acc, rings[i], rings[i + 1], mat,
               smooth=(i >= 2), wrap=True, flip=(dirn < 0))
    # closure disc deep in the bore
    Pc = np.asarray(c, float) + axm * (-depth)
    ic = acc.verts(Pc.reshape(1, 3), uv=np.zeros((1, 2)), base=base,
                   aux=np.array([[0.0, 0.0, 0.4, aux[3]]]), wear=wear)
    acc.fan(rings[-1], ic, mat, smooth=False, flip=(dirn > 0))
    return rings[0]


def cap_flat(acc, c, u, v, S, mat, base, aux, wear, edge=None, flip=False):
    """Flat closure of a section (a welded cap face)."""
    S = np.asarray(S, float)
    K = len(S)
    P = (np.asarray(c, float)[None, :] + S[:, 0:1] * np.asarray(u)[None, :]
         + S[:, 1:2] * np.asarray(v)[None, :])
    a = np.tile(np.asarray(aux, float).reshape(1, 4), (K, 1))
    if edge is not None:
        a[:, 0] = np.asarray(edge, float)
    i0 = acc.verts(P, uv=np.stack([section_perimeter_u(S), np.zeros(K)], -1),
                   base=base, aux=a, wear=wear)
    ic = acc.verts(np.asarray(c, float).reshape(1, 3), uv=np.zeros((1, 2)),
                   base=base, aux=np.asarray(aux, float).reshape(1, 4), wear=wear)
    acc.fan(i0 + np.arange(K), ic, mat, smooth=False, flip=flip)
    return i0 + np.arange(K)


def rect_loop_counts(x0, x1, y0, y1, step):
    """Per-edge sample counts for `rect_loop`, so two rects can share them."""
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    out = []
    for i in range(4):
        a = np.array(corners[i], float)
        b = np.array(corners[(i + 1) % 4], float)
        out.append(max(1, int(round(float(np.linalg.norm(b - a)) / step))))
    return tuple(out)


def rect_loop(x0, x1, y0, y1, step, counts=None):
    """CCW closed loop on a rectangle, corners always included."""
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if counts is None:
        counts = rect_loop_counts(x0, x1, y0, y1, step)
    pts = []
    for i in range(4):
        a = np.array(corners[i], float)
        b = np.array(corners[(i + 1) % 4], float)
        f = np.linspace(0.0, 1.0, counts[i] + 1)[:-1]
        pts.append(a[None, :] + (b - a)[None, :] * f[:, None])
    return np.concatenate(pts, 0)


def _cell_rings(outer, centre, r, nv, grade=1.7):
    """Rings from a circle of radius r at `centre` out to the loop `outer`."""
    d = outer - np.asarray(centre, float)[None, :]
    ang = np.arctan2(d[:, 1], d[:, 0])
    inner = np.asarray(centre, float)[None, :] + r * np.stack(
        [np.cos(ang), np.sin(ang)], -1)
    t = np.linspace(0.0, 1.0, nv + 1) ** grade
    return inner[None] + (outer - inner)[None] * t[:, None, None], ang


def plate(acc, hw, hd, t, holes, mat, base, aux, wear, z0=0.0,
          chamfer=0.0009, hole_ch=0.0007, step=0.0045, nv=7, nv_bot=3,
          uid=0.0, face_edge=0.08):
    """A rectangular steel plate with real drilled, chamfered holes.

    `holes` is [(x, y, r)] and must be 1, 2 or 4 holes in a symmetric layout —
    the plate is decomposed into one cell per hole and each cell meshed as a
    circle-to-rectangle annulus, which gives clean quads, a real bore wall and
    a chamfered rim without a boolean.
    """
    c = chamfer
    xs = sorted(set(round(h[0], 6) for h in holes))
    ys = sorted(set(round(h[1], 6) for h in holes))
    xb = [-hw + c] + ([0.5 * (xs[0] + xs[1])] if len(xs) > 1 else []) + [hw - c]
    yb = [-hd + c] + ([0.5 * (ys[0] + ys[1])] if len(ys) > 1 else []) + [hd - c]
    ztop, zbot = z0 + t, z0
    for (hx, hy, hr) in holes:
        i = 0 if len(xb) == 2 or hx <= xb[1] else 1
        j = 0 if len(yb) == 2 or hy <= yb[1] else 1
        cell = rect_loop(xb[i], xb[i + 1], yb[j], yb[j + 1], step)
        K = len(cell)
        R, ang = _cell_rings(cell, (hx, hy), hr + hole_ch, nv)
        Rb, _ = _cell_rings(cell, (hx, hy), hr + hole_ch, nv_bot)
        ee = np.full(K, face_edge)

        def emit_face(RR, z, flip):
            idx = []
            for k in range(len(RR)):
                P = np.concatenate([RR[k], np.full((K, 1), z)], 1)
                a = np.tile(np.asarray(aux, float).reshape(1, 4), (K, 1))
                a[:, 0] = np.where(k == 0, 0.75, face_edge)
                a[:, 2] = 0.15 if k else 0.55
                i0 = acc.verts(P, uv=RR[k], base=base, aux=a, wear=wear)
                idx.append(i0 + np.arange(K))
            G = np.stack(idx, 0)
            acc.grid_faces(G, mat, False, wrap_u=True, flip=flip)
            return G[0]

        top0 = emit_face(R, ztop, False)
        bot0 = emit_face(Rb, zbot, True)
        # hole: chamfer -> bore -> chamfer
        cx, cy = hx, hy
        bore_ang = ang
        rings = []
        for (rr, zz, mc, ee2) in ((hr, ztop - hole_ch, 0.95, 0.9),
                                  (hr, zbot + hole_ch, 0.95, 0.5)):
            P = np.stack([cx + rr * np.cos(bore_ang), cy + rr * np.sin(bore_ang),
                          np.full(K, zz)], -1)
            a = np.tile(np.asarray(aux, float).reshape(1, 4), (K, 1))
            a[:, 0] = ee2
            a[:, 2] = mc
            i0 = acc.verts(P, uv=np.stack([np.zeros(K), np.full(K, zz)], -1),
                           base=base, aux=a, wear=wear)
            rings.append(i0 + np.arange(K))
        bridge(acc, top0, rings[0], mat, smooth=False, flip=True)
        bridge(acc, rings[0], rings[1], mat, smooth=True, flip=True)
        bridge(acc, rings[1], bot0, mat, smooth=False, flip=True)
    # perimeter band: chamfer, side, chamfer.  Both loops MUST carry the same
    # point count or the band cannot be bridged, so the counts are computed
    # once from the inner rect and reused.
    cnt = rect_loop_counts(-hw + c, hw - c, -hd + c, hd - c, step)
    inner = rect_loop(-hw + c, hw - c, -hd + c, hd - c, step, counts=cnt)
    outer = rect_loop(-hw, hw, -hd, hd, step, counts=cnt)
    lv = [(inner, ztop, 0.95), (outer, ztop - c, 1.0), (outer, zbot + c, 1.0),
          (inner, zbot, 0.8)]
    prv = None
    for (lp, zz, ee) in lv:
        Kk = len(lp)
        P = np.concatenate([lp, np.full((Kk, 1), zz)], 1)
        a = np.tile(np.asarray(aux, float).reshape(1, 4), (Kk, 1))
        a[:, 0] = ee
        i0 = acc.verts(P, uv=lp, base=base, aux=a, wear=wear)
        cur = i0 + np.arange(Kk)
        if prv is not None:
            bridge(acc, prv, cur, mat, smooth=False, flip=True)
        prv = cur


def hex_nut(acc, o, u, v, w, af, h, bore_r, mat, base, aux, wear,
            nseg=48, pitch=None, uid=0.0):
    """A hex nut with its real 30 deg chamfer and a threaded bore.

    The chamfer is what makes a nut read as a nut: it turns the six corners
    into a circle on the top face and leaves the curved intersection lines
    down the flats.  Modelled by intersecting the hex prism with a cone,
    which produces those curves for free.
    """
    o = np.asarray(o, float)
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    th = np.arange(nseg) * TAU / nseg
    ap = af * 0.5
    hexr = ap / np.cos(((th + math.pi / 6) % (math.pi / 3)) - math.pi / 6)
    rface = ap * 1.012
    ch = (hexr.max() - rface) * math.tan(math.radians(30.0))
    zs = np.concatenate([np.linspace(0.0, ch, 6), np.linspace(ch, h - ch, 4)[1:],
                         np.linspace(h - ch, h, 6)[1:]])
    Rr = np.minimum(hexr[None, :], (rface + np.minimum(zs, h - zs)
                                    * math.tan(math.radians(60.0)))[:, None])
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([Rr * np.cos(th)[None, :], Rr * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(zs), nseg, 1)).copy()
    a[..., 0] = 0.30 + 0.65 * (np.abs(hexr[None, :] - Rr) < 1e-6)
    a[..., 2] = 0.35
    sweep(acc, Cp, np.tile(u, (len(zs), 1)), np.tile(v, (len(zs), 1)), S,
          mat, base, a, wear, smooth=False)
    # faces (annulus from the chamfer circle to the bore) and the bore
    for (zz, flip) in ((h, False), (0.0, True)):
        rings = []
        for rr in (rface, bore_r):
            P = o[None, :] + w[None, :] * zz + \
                rr * (np.cos(th)[:, None] * u[None, :]
                      + np.sin(th)[:, None] * v[None, :])
            aa = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
            aa[:, 0] = 0.5
            aa[:, 2] = 0.75
            i0 = acc.verts(P, uv=np.stack([th * rr, np.full(nseg, zz)], -1),
                           base=base, aux=aa, wear=wear)
            rings.append(i0 + np.arange(nseg))
        bridge(acc, rings[0], rings[1], mat, smooth=False, flip=flip)
    thread_bore(acc, o, u, v, w, bore_r, h, mat, base, aux, wear,
                pitch=pitch, nseg=nseg, uid=uid)


def _thread_profile(f, crest=0.10, flat=0.78):
    g = np.abs(f * 2.0 - 1.0)
    return np.clip((g - crest) / flat, 0.0, 1.0)


def thread_stud(acc, o, u, v, w, r_maj, pitch, length, mat, base, aux, wear,
                nseg=32, rows_per_pitch=5, uid=0.0, chamfer=True):
    """A real helical external thread.  r(theta, z) = major - depth*profile.

    At 1.607 mm/px an M16's 2 mm pitch is 1.25 px, which is exactly the scale
    at which a smooth peg and a bolt stop looking alike.
    """
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    depth = 0.613 * pitch
    r_root = r_maj - depth
    nrow = max(6, int(round(length / pitch * rows_per_pitch)))
    zs = np.linspace(0.0, length, nrow + 1)
    th = np.arange(nseg) * TAU / nseg
    f = np.mod(zs[:, None] / pitch - th[None, :] / TAU, 1.0)
    R = r_root + (r_maj - r_root) * _thread_profile(f)
    if chamfer:
        # The lead chamfer is at the FREE end of the stud -- that is the end a
        # die ran off and the end a nut is started on.  The first version put
        # it at z = 0, i.e. underneath the nut, where it can never be seen and
        # where it made the shank look swaged.
        lead = np.clip((length - zs) / (pitch * 1.2), 0.0, 1.0)[:, None]
        R = R * (0.74 + 0.26 * lead)
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([R * np.cos(th)[None, :], R * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(zs), nseg, 1)).copy()
    a[..., 0] = 0.55
    a[..., 2] = 0.90
    sweep(acc, Cp, np.tile(u, (len(zs), 1)), np.tile(v, (len(zs), 1)), S,
          mat, base, a, wear, smooth=True)
    cap_flat(acc, o + w * length, u, v,
             np.stack([R[-1] * np.cos(th), R[-1] * np.sin(th)], -1),
             mat, base, (0.4, 0.0, 0.95, aux[3]), wear)
    return r_maj


def thread_bore(acc, o, u, v, w, r_bore, length, mat, base, aux, wear,
                pitch=None, nseg=32, uid=0.0):
    """The inside of a nut: a threaded bore, wound the other way round."""
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.arange(nseg) * TAU / nseg
    if pitch:
        nrow = max(5, int(round(length / pitch * 4)))
        zs = np.linspace(0.0, length, nrow + 1)
        f = np.mod(zs[:, None] / pitch - th[None, :] / TAU, 1.0)
        R = r_bore + 0.55 * pitch * _thread_profile(f)
    else:
        zs = np.linspace(0.0, length, 3)
        R = np.full((3, nseg), r_bore)
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([R * np.cos(th)[None, :], R * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(zs), nseg, 1)).copy()
    a[..., 0] = 0.05
    a[..., 2] = 0.95
    sweep(acc, Cp, np.tile(u, (len(zs), 1)), np.tile(v, (len(zs), 1)), S,
          mat, base, a, wear, smooth=True, flip=True)


def washer(acc, o, u, v, w, r_out, r_in, t, mat, base, aux, wear, nseg=40,
           dish=0.0):
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.arange(nseg) * TAU / nseg
    rings = []
    for (rr, zz, ee, mc) in ((r_in, 0.0, 0.6, 0.8), (r_out, dish, 0.9, 0.5),
                             (r_out, dish + t, 0.9, 0.5), (r_in, t, 0.6, 0.8)):
        P = o[None, :] + w[None, :] * zz + rr * (
            np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :])
        a = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
        a[:, 0] = ee
        a[:, 2] = mc
        i0 = acc.verts(P, uv=np.stack([th * rr, np.full(nseg, zz)], -1),
                       base=base, aux=a, wear=wear)
        rings.append(i0 + np.arange(nseg))
    for i in range(3):
        bridge(acc, rings[i], rings[i + 1], mat, smooth=(i == 1), flip=False)
    bridge(acc, rings[3], rings[0], mat, smooth=False, flip=False)


def dome_head(acc, o, u, v, w, r, h, mat, base, aux, wear, nseg=32, nrow=8,
              flat=0.35):
    """A domed rivet / round-head fastener."""
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.arange(nseg) * TAU / nseg
    t = np.linspace(0.0, 1.0, nrow + 1)
    ang = t * (math.pi * 0.5) * (1.0 - flat) + 0.0
    R = r * np.cos(ang) ** 0.72
    Z = h * np.sin(ang)
    Cp = o[None, :] + w[None, :] * Z[:, None]
    S = np.stack([R[:, None] * np.cos(th)[None, :],
                  R[:, None] * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(t), nseg, 1)).copy()
    a[..., 0] = 0.75
    a[..., 2] = 0.5
    G = sweep(acc, Cp, np.tile(u, (len(t), 1)), np.tile(v, (len(t), 1)), S,
              mat, base, a, wear, smooth=True)
    ic = acc.verts((o + w * h * 1.0).reshape(1, 3), uv=np.zeros((1, 2)),
                   base=base, aux=np.asarray(aux, float).reshape(1, 4), wear=wear)
    acc.fan(G[-1], ic, mat, smooth=True, flip=False)
    return G[0]


def weld_bead(acc, A, B, NA, NB, mat, base, aux, wear, bulge=0.0022,
              nsec=11, ripple=0.30, pitch=0.0026, uid=0.0, closed=True,
              flip=False):
    """A fillet weld with a stack-of-dimes ripple.

    A (M,3) toe on surface A, B (M,3) toe on surface B, NA/NB their normals.
    The ripple pitch is 2.6 mm = 1.6 screen px at this item's filmed distance,
    so it is the difference between a weld and a smooth chamfer.
    """
    A = np.asarray(A, float)
    B = np.asarray(B, float)
    NA = np.asarray(NA, float)
    NB = np.asarray(NB, float)
    M = len(A)
    if NA.ndim == 1:
        NA = np.tile(NA, (M, 1))
    if NB.ndim == 1:
        NB = np.tile(NB, (M, 1))
    bis = unit(NA + NB)
    d = np.linalg.norm(np.diff(A, axis=0), axis=1)
    vv = np.concatenate([[0.0], np.cumsum(d)])
    ph = np.array([hash01(uid, "w", int(i)) for i in range(1)])[0] * TAU
    phi = np.linspace(0.0, 1.0, nsec)
    # crescent ripple: the phase shifts across the bead so each dime curves
    rp = 1.0 + ripple * np.cos(TAU * vv[:, None] / pitch
                               + phi[None, :] * 1.9 + ph)
    rp *= 1.0 + 0.10 * np.cos(TAU * vv[:, None] / (pitch * 7.3) + 1.1)
    bl = bulge * np.sin(math.pi * phi) ** 0.78
    P = (A[:, None, :] * (1.0 - phi)[None, :, None]
         + B[:, None, :] * phi[None, :, None]
         + bis[:, None, :] * (bl[None, :] * rp)[:, :, None])
    # sink the toes 0.2 mm into the parent surfaces so there is no crack
    P[:, 0, :] -= NA * 0.0002
    P[:, -1, :] -= NB * 0.0002
    K = nsec
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (M, K, 1)).copy()
    a[..., 0] = 0.35
    a[..., 1] = np.clip(1.25 * np.sin(math.pi * phi) ** 0.35, 0.0, 1.0)[None, :]
    uvv = np.stack([np.broadcast_to(phi[None, :] * bulge * 3.0, (M, K)),
                    np.broadcast_to(vv[:, None], (M, K))], -1)
    i0 = acc.verts(P.reshape(-1, 3), uv=uvv.reshape(-1, 2),
                   base=chan(base, M, K).reshape(-1, 4), aux=a.reshape(-1, 4),
                   wear=chan(wear, M, K).reshape(-1, 4))
    IDX = i0 + np.arange(M * K).reshape(M, K)
    if closed:
        IDX = np.vstack([IDX, IDX[0:1]])
    acc.grid_faces(IDX, mat, True, wrap_u=False, flip=flip)
    return IDX


def section_fillet_weld(acc, S, z_plate, leg_a, leg_b, mat, base, aux, wear,
                        uid=0.0, bulge=None, flip=False):
    """Run a fillet weld round the foot of a swept section standing on a plate."""
    S = np.asarray(S, float)
    n2 = section_outward(S)
    A = np.concatenate([S + n2 * leg_a, np.full((len(S), 1), z_plate)], 1)
    B = np.concatenate([S, np.full((len(S), 1), z_plate + leg_b)], 1)
    NA = np.tile(np.array([0.0, 0.0, 1.0]), (len(S), 1))
    NB = np.concatenate([n2, np.zeros((len(S), 1))], 1)
    return weld_bead(acc, A, B, NA, NB, mat, base, aux, wear,
                     bulge=(bulge if bulge is not None else leg_a * 0.42),
                     uid=uid, closed=True, flip=flip)


def box_beam(acc, p0, p1, w, h, mat, base, aux, wear, up=(0, 0, 1), nrow=2,
             edge=0.7, smooth=False):
    """A simple rectangular bar between two points (gussets, lugs, cleats)."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    ax = unit(p1 - p0)
    u = unit(np.cross(np.asarray(up, float), ax))
    if np.linalg.norm(u) < 1e-9:
        u = unit(np.cross(np.array([1.0, 0.0, 0.0]), ax))
    v = np.cross(ax, u)
    S, E = rrect_section(w, h, min(w, h) * 0.14, nc=3, ns=1)
    t = np.linspace(0.0, 1.0, nrow + 1)
    Cp = p0[None, :] + (p1 - p0)[None, :] * t[:, None]
    G = sweep(acc, Cp, np.tile(u, (len(t), 1)), np.tile(v, (len(t), 1)), S,
              mat, base, aux, wear, edge=E * edge, smooth=smooth)
    cap_flat(acc, p0, u, v, S, mat, base, aux, wear, edge=E * edge, flip=True)
    cap_flat(acc, p1, u, v, S, mat, base, aux, wear, edge=E * edge, flip=False)
    return G


def tri_gusset(acc, o, u, v, w, a, b, t, mat, base, aux, wear, uid=0.0,
               nose=0.010):
    """A triangular gusset plate with a clipped nose, standing in the (u, w) plane."""
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    pts2 = np.array([[0.0, 0.0], [a, 0.0], [a - nose, nose * 0.9],
                     [nose * 0.9, b - nose], [0.0, b]])
    P0 = o[None, :] + pts2[:, 0:1] * u[None, :] + pts2[:, 1:2] * w[None, :]
    A = P0 - v * (t * 0.5)
    B = P0 + v * (t * 0.5)
    a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (len(pts2), 1))
    a4[:, 0] = 0.85
    ia = acc.verts(A, uv=pts2, base=base, aux=a4, wear=wear)
    ib = acc.verts(B, uv=pts2, base=base, aux=a4, wear=wear)
    IA = ia + np.arange(len(pts2))
    IB = ib + np.arange(len(pts2))
    acc.tris(np.array([[IA[0], IA[2], IA[1]], [IA[0], IA[3], IA[2]],
                       [IA[0], IA[4], IA[3]]]), mat, False)
    acc.tris(np.array([[IB[0], IB[1], IB[2]], [IB[0], IB[2], IB[3]],
                       [IB[0], IB[3], IB[4]]]), mat, False)
    acc.grid_faces(np.stack([IA, IB], 0), mat, False, wrap_u=True, flip=True)
    return P0


def cable_tie(acc, ctr, u, v, w, r, mat, base, aux, wear, uid=0.0,
              width=0.0046, thick=0.0012, tail=0.030, nseg=44):
    """A nylon cable tie: the strap, the ratchet head, and a cut tail."""
    ctr = np.asarray(ctr, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.linspace(0.0, TAU, nseg)
    rr = r + thick * 0.5 + 0.0004 * np.sin(th * 3.0 + hash01(uid, "ct") * 6.0)
    Cp = ctr[None, :] + rr[:, None] * (np.cos(th)[:, None] * u[None, :]
                                       + np.sin(th)[:, None] * v[None, :])
    T, U2, V2 = frames_along(Cp, ref=w)
    S, E = rrect_section(thick, width, thick * 0.35, nc=3, ns=1)
    sweep(acc, Cp, U2, V2, S, mat, base, aux, wear, edge=E * 0.6, smooth=False)
    # head
    hp = ctr + (r + thick * 1.6) * u + w * 0.0
    box_beam(acc, hp - w * width * 0.7, hp + w * width * 0.7,
             0.0072, 0.0055, mat, base, aux, wear, up=u, nrow=1)
    # tail
    tp0 = hp + u * 0.0025
    tdir = unit(v * 0.75 + w * 0.30 - u * 0.15)
    box_beam(acc, tp0, tp0 + tdir * tail, thick, width, mat, base, aux, wear,
             up=u, nrow=3)


def tie_wire(acc, ctr, u, v, w, r, mat, base, aux, wear, uid=0.0, turns=3.0,
             wr=0.0012, nseg=90):
    """Twisted galvanised tie wire — what actually holds half of a real post on."""
    ctr = np.asarray(ctr, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.linspace(0.0, TAU * turns, int(nseg * turns))
    zz = np.linspace(-wr * 1.4 * turns, wr * 1.4 * turns, len(th))
    rr = r + wr + 0.0003 * np.sin(th * 2.3)
    Cp = (ctr[None, :] + rr[:, None] * (np.cos(th)[:, None] * u[None, :]
                                        + np.sin(th)[:, None] * v[None, :])
          + zz[:, None] * w[None, :])
    T, U2, V2 = frames_along(Cp, ref=w)
    S, _E = circle_section(9, wr)[0:2]
    sweep(acc, Cp, U2, V2, S, mat, base, aux, wear, smooth=True)
    # the twisted tail
    p0 = Cp[-1]
    tw = np.linspace(0.0, 1.0, 22)
    tp = p0[None, :] + unit(np.cross(w, u))[None, :] * (tw[:, None] * 0.034)
    tp += w[None, :] * (0.0016 * np.sin(tw * 26.0))[:, None]
    T3, U3, V3 = frames_along(tp, ref=w)
    sweep(acc, tp, U3, V3, S, mat, base, aux, wear, smooth=True)


def tag_plate(acc, o, u, v, w, mat, base, aux, wear, uid=0.0,
              wdt=0.052, hgt=0.082, t=0.0016):
    """A scaffold inspection tag hanging on a wire loop."""
    o = np.asarray(o, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    S, E = rrect_section(wdt, hgt, 0.006, nc=4, ns=2)
    Cp = np.stack([o - v * t * 0.5, o + v * t * 0.5], 0)
    sweep(acc, Cp, np.tile(u, (2, 1)), np.tile(w, (2, 1)), S, mat, base, aux,
          wear, edge=E, smooth=False)
    cap_flat(acc, o - v * t * 0.5, u, w, S, mat, base, aux, wear, edge=E,
             flip=True)
    cap_flat(acc, o + v * t * 0.5, u, w, S, mat, base, aux, wear, edge=E)
    # the wire loop through the top of the tag
    th = np.linspace(-2.5, 2.5, 26)
    rr = 0.016
    lp = (o + w * (hgt * 0.5 + rr * 0.6))[None, :] + rr * (
        np.sin(th)[:, None] * u[None, :] + np.cos(th)[:, None] * w[None, :])
    T2, U2, V2 = frames_along(lp, ref=v)
    sweep(acc, lp, U2, V2, circle_section(8, 0.0011)[0], MAT_FORGED, base,
          aux, wear, smooth=True)


def nail(acc, o, w, u, r, head_r, head_h, length, mat, base, aux, wear,
         uid=0.0, bent=0.0):
    """A driven nail with a hammer-marked head."""
    o = np.asarray(o, float)
    w = unit(np.asarray(w, float))
    u = unit(np.asarray(u, float) - w * float(np.dot(u, w)))
    v = np.cross(w, u)
    nrow = 6
    t = np.linspace(0.0, 1.0, nrow + 1)
    Cp = o[None, :] - w[None, :] * (t[:, None] * length)
    Cp += u[None, :] * (bent * t ** 2)[:, None]
    rr = r * (1.0 - 0.55 * np.clip((t - 0.72) / 0.28, 0, 1))
    S = np.stack([rr[:, None] * np.cos(np.arange(12) * TAU / 12)[None, :],
                  rr[:, None] * np.sin(np.arange(12) * TAU / 12)[None, :]], -1)
    sweep(acc, Cp, np.tile(u, (nrow + 1, 1)), np.tile(v, (nrow + 1, 1)), S,
          mat, base, aux, wear, smooth=True)
    # head: struck, so slightly domed and slightly off-axis
    hh = hash01(uid, "nail")
    dome_head(acc, o, u, v, w, head_r, head_h * (0.7 + 0.6 * hh), mat, base,
              (0.9, 0.0, 0.25, aux[3]), wear, nseg=16, nrow=4, flat=0.55)


def ground_pin(acc, o, w, u, r, above, below, mat, base, aux, wear, uid=0.0):
    """A driven steel pin whose head the sledge has mushroomed over."""
    o = np.asarray(o, float)
    w = unit(np.asarray(w, float))
    u = unit(np.asarray(u, float) - w * float(np.dot(u, w)))
    v = np.cross(w, u)
    nseg = 20
    th = np.arange(nseg) * TAU / nseg
    zs = np.concatenate([np.linspace(-below, above - 0.012, 8),
                         np.linspace(above - 0.012, above, 6)[1:]])
    t = np.clip((zs - (above - 0.012)) / 0.012, 0.0, 1.0)
    # the mushroom: metal flowed sideways and split into a ragged flange
    rag = 1.0 + 0.16 * np.sin(th * 5.0 + hash01(uid, "pin") * 6.0) \
        + 0.09 * np.sin(th * 11.0 + 2.0)
    R = r * (1.0 + 0.55 * t ** 1.6)[:, None] * rag[None, :]
    R *= (1.0 - 0.22 * np.clip((-zs) / max(below, 1e-6), 0, 1))[:, None]
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([R * np.cos(th)[None, :], R * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(zs), nseg, 1)).copy()
    a[..., 0] = 0.3 + 0.6 * t[:, None]
    sweep(acc, Cp, np.tile(u, (len(zs), 1)), np.tile(v, (len(zs), 1)), S,
          mat, base, a, wear, smooth=True)
    cap_flat(acc, o + w * above, u, v,
             np.stack([R[-1] * np.cos(th) * 0.98, R[-1] * np.sin(th) * 0.98], -1),
             mat, base, (0.95, 0.0, 0.15, aux[3]), wear)


# --------------------------------------------------------------------------- #
#  7.  scaffold couplers — the single most recognisable object on a post        #
# --------------------------------------------------------------------------- #
#
# A right-angle ("double") coupler is two rolled saddle bands on a forged body,
# each closed by a T-bolt through a pair of lugs.  At 622 px/m the parts that
# have to exist are: the 4 mm band with its cut ends, the hinge rivet with its
# domed head, the T-bolt shank, the 22 mm A/F nut, and the 4-9 mm of thread
# sticking out past it.  A coupler modelled as a lump is the "smooth tube"
# rejection one level down.

TUBE_OD = 0.0483                       # 48.3 mm scaffold tube
TUBE_WALL = 0.0032
BAND_T = 0.0040                        # rolled band plate thickness
BAND_W = 0.0245                        # band width
BAND_WRAP = math.radians(196.0)


def _band(acc, ctr, u, v, w, r_in, wrap, a0, mat, base, aux, wear, uid=0.0,
          t=BAND_T, wid=BAND_W, nseg=26):
    """One rolled saddle band: a strip of plate wrapped round the tube."""
    ctr = np.asarray(ctr, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    th = np.linspace(a0, a0 + wrap, nseg)
    # section in the (radial, axial) plane: a rectangle t x wid
    Cp = ctr[None, :] + r_in * (np.cos(th)[:, None] * u[None, :]
                                + np.sin(th)[:, None] * v[None, :])
    RAD = (np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :])
    AX = np.tile(w, (nseg, 1))
    S, E = rrect_section(t, wid, t * 0.28, nc=3, ns=2)
    S = S + np.array([t * 0.5, 0.0])[None, :]
    G = sweep(acc, Cp, RAD, AX, S, mat, base, aux, wear, edge=E * 0.8,
              smooth=False)
    # cut ends
    for (i, flip) in ((0, True), (nseg - 1, False)):
        cap_flat(acc, Cp[i], RAD[i], AX[i], S, mat, base,
                 (0.85, 0.0, 0.85, aux[3]), wear, edge=E, flip=flip)
    return th, Cp, RAD


def _tbolt(acc, o, ax, up, mat, base, aux, wear, uid=0.0, shank_r=0.0070,
           gap=0.020, af=0.0220, nut_h=0.0125, stick=0.0065):
    """T-bolt through two lugs, with its nut and the thread past the nut."""
    o = np.asarray(o, float)
    ax = unit(np.asarray(ax, float))
    up = unit(np.asarray(up, float) - ax * float(np.dot(up, ax)))
    sd = np.cross(ax, up)
    # shank
    nrow = 3
    t = np.linspace(0.0, 1.0, nrow + 1)
    Cp = o[None, :] + ax[None, :] * (t[:, None] * gap)
    S = circle_section(20, shank_r)[0]
    sweep(acc, Cp, np.tile(up, (nrow + 1, 1)), np.tile(sd, (nrow + 1, 1)), S,
          mat, base, aux, wear, smooth=True)
    # the T head, hooked into the slot in the far lug
    box_beam(acc, o - up * 0.0145, o + up * 0.0145, 0.0092, 0.0072,
             mat, base, (0.8, 0.0, 0.3, aux[3]), wear, up=ax, nrow=1)
    # nut + protruding thread
    hex_nut(acc, o + ax * gap, up, sd, ax, af, nut_h, shank_r * 0.86,
            mat, base, aux, wear, nseg=36, pitch=0.0020, uid=uid)
    thread_stud(acc, o + ax * (gap + nut_h - 0.0006), up, sd, ax, shank_r,
                0.0020, stick, mat, base, aux, wear, nseg=24,
                rows_per_pitch=4, uid=uid)


def _pin(acc, o, ax, r, length, mat, base, aux, wear, uid=0.0, head=True):
    """A hinge rivet: a short shank with a domed head swaged on each end."""
    o = np.asarray(o, float)
    ax = unit(np.asarray(ax, float))
    u = unit(np.cross(ax, np.array([0.0, 0.0, 1.0])
                      if abs(ax[2]) < 0.9 else np.array([1.0, 0.0, 0.0])))
    v = np.cross(ax, u)
    t = np.linspace(-0.5, 0.5, 3)
    Cp = o[None, :] + ax[None, :] * (t[:, None] * length)
    S = circle_section(16, r)[0]
    sweep(acc, Cp, np.tile(u, (3, 1)), np.tile(v, (3, 1)), S, mat, base, aux,
          wear, smooth=True)
    if head:
        for sg in (1.0, -1.0):
            dome_head(acc, o + ax * (sg * length * 0.5), u, v, ax * sg,
                      r * 1.55, r * 0.62, mat, base,
                      (0.9, 0.0, 0.4, aux[3]), wear, nseg=16, nrow=4, flat=0.5)


def _saddle(acc, ctr, u, v, w, r_in, gap_dir, mat, base, aux, wear, uid=0.0,
            t=BAND_T, wid=BAND_W, lug=0.0145, half_gap_deg=8.5):
    """The saddle of a scaffold coupler: TWO half-bands, hinged and bolted.

    The first version of this modelled one C-shaped band with a 164 deg mouth,
    which put the two bolt lugs 71 mm apart -- a clamp that could never close
    on a 48 mm tube.  A real coupler is a ring SPLIT INTO HALVES: a hinge
    rivet on one side, and on the other two lugs 10 mm apart with the T-bolt
    between them.  That difference is 6 screen px wide and it is the whole
    reason a coupler looks like a coupler.

    -> (bolt_origin, bolt_axis, bolt_gap) ready for `_tbolt`.
    """
    ctr = np.asarray(ctr, float)
    u, v, w = np.asarray(u, float), np.asarray(v, float), np.asarray(w, float)
    hg = math.radians(half_gap_deg)
    wrap = math.pi - 2.0 * hg

    def radial(a):
        return math.cos(a) * u + math.sin(a) * v

    for a0 in (gap_dir + hg, gap_dir + math.pi + hg):
        _band(acc, ctr, u, v, w, r_in, wrap, a0, mat, base, aux, wear,
              uid=uid, t=t, wid=wid)
    outs = []
    for sg in (+1.0, -1.0):
        rd = radial(gap_dir + sg * hg)
        box_beam(acc, ctr + rd * (r_in + t * 0.35),
                 ctr + rd * (r_in + t + lug), 0.0044, wid * 0.86, mat, base,
                 aux, wear, up=w, nrow=1)
        outs.append(ctr + rd * (r_in + t + lug * 0.52))
    hin = []
    for sg in (+1.0, -1.0):
        rd = radial(gap_dir + math.pi + sg * hg)
        box_beam(acc, ctr + rd * (r_in + t * 0.35),
                 ctr + rd * (r_in + t + lug * 0.72), 0.0044, wid * 0.80, mat,
                 base, aux, wear, up=w, nrow=1)
        hin.append(ctr + rd * (r_in + t + lug * 0.40))
    _pin(acc, 0.5 * (hin[0] + hin[1]), w, 0.0028, wid * 0.96, MAT_FORGED,
         base, aux, wear, uid=uid)
    bax = unit(outs[0] - outs[1])
    sep = float(np.linalg.norm(outs[0] - outs[1]))
    return outs[1] - bax * 0.0026, bax, sep + 0.0052


def coupler(acc, ctr, tube_ax, out_ax, kind, mat, base, aux, wear, uid=0.0,
            r_tube=TUBE_OD * 0.5, stub=0.150, stub_r=TUBE_OD * 0.5,
            galv_base=None):
    """A right-angle (kind 0) or swivel (kind 1) scaffold coupler.

    ctr       centre of the coupler on the column axis
    tube_ax   the column's axis (the saddle that grips the column wraps this)
    out_ax    the direction the captured ledger runs
    -> Frame at the FREE END of the ledger stub.  The stub is the coupler's own
       captured tube; a dependant continues its member from that frame.
    """
    ctr = np.asarray(ctr, float)
    ta = unit(np.asarray(tube_ax, float))
    oa = unit(np.asarray(out_ax, float) - ta * float(np.dot(out_ax, ta)))
    side = np.cross(ta, oa)
    gb = base if galv_base is None else galv_base
    r_in = r_tube + 0.0004

    # --- saddle 1: grips the column.  Its bolt faces AWAY from the ledger,
    #     which is where a fitter's spanner can actually reach it.
    bo, bax, bgap = _saddle(acc, ctr, oa, side, ta, r_in, math.pi, mat, gb,
                            aux, wear, uid=uid)
    _tbolt(acc, bo, bax, ta, MAT_FORGED, gb, aux, wear, uid=uid + 0.5,
           gap=bgap, stick=rnd(0.004, 0.011, uid, "st1"))

    # --- the forged body between the two saddles ----------------------------
    off = r_tube + BAND_T + 0.0026 + stub_r
    bctr = ctr + oa * (r_tube + BAND_T * 0.5 + 0.0035)
    if kind == 0:
        box_beam(acc, bctr - side * 0.0125, bctr + side * 0.0125, 0.0150,
                 0.0170, MAT_FORGED, gb, (0.6, 0.0, 0.2, aux[3]), wear,
                 up=oa, nrow=1)
    else:
        # swivel: a rivet boss between two plates, so the ledger can rake
        _pin(acc, bctr, oa, 0.0068, 0.0230, MAT_FORGED, gb,
             (0.8, 0.0, 0.35, aux[3]), wear, uid=uid + 0.1)
        for sg in (-1.0, 1.0):
            box_beam(acc, bctr + side * (sg * 0.0092) - oa * 0.0090,
                     bctr + side * (sg * 0.0092) + oa * 0.0090, 0.0060,
                     0.0250, MAT_FORGED, gb, (0.85, 0.0, 0.3, aux[3]), wear,
                     up=ta, nrow=1)

    # --- saddle 2: grips the ledger -----------------------------------------
    rake = 0.0 if kind == 0 else math.radians(rnd(-24.0, 24.0, uid, "rake"))
    la = unit(oa * math.cos(rake) + ta * math.sin(rake))
    lctr = ctr + oa * off
    lu2 = unit(np.cross(la, side))
    gd2 = math.pi * 0.5 if chance(0.5, uid, "gd2") else -math.pi * 0.5
    bo2, bax2, bgap2 = _saddle(acc, lctr, lu2, side, la, stub_r + 0.0004, gd2,
                               mat, gb, aux, wear, uid=uid + 0.25)
    _tbolt(acc, bo2, bax2, la, MAT_FORGED, gb, aux, wear, uid=uid + 0.75,
           gap=bgap2, stick=rnd(0.004, 0.011, uid, "st2"))

    # --- the captured ledger stub -------------------------------------------
    # It starts just clear of the column's own saddle and runs out `stub`.
    near = -(off - r_tube - BAND_T - 0.0070)
    zs = np.linspace(near, stub, 7)
    Cp = lctr[None, :] + la[None, :] * zs[:, None]
    S = circle_section(36, stub_r)[0]
    sweep(acc, Cp, np.tile(lu2, (len(zs), 1)), np.tile(side, (len(zs), 1)),
          S, mat, gb, aux, wear, smooth=True)
    open_end(acc, Cp[-1], lu2, side, la, S, TUBE_WALL, mat, gb, aux, wear,
             uid=uid + 0.9, dirn=1.0)
    open_end(acc, Cp[0], lu2, side, la, S, TUBE_WALL, mat, gb, aux, wear,
             uid=uid + 0.95, dirn=-1.0)
    return Frame(Cp[-1], la, side, lu2, stub_r, "ledger")


def welded_bracket(acc, o, out_n, up, w, h, t, mat, base, aux, wear, uid=0.0,
                   holes=2, hole_r=0.0055, weld=True):
    """A welded steel bracket lug — the box-section frame's answer to a coupler.

    -> Frame at the face of the lug, .y = outward, for whatever bolts to it.
    """
    o = np.asarray(o, float)
    n = unit(np.asarray(out_n, float))
    up = unit(np.asarray(up, float) - n * float(np.dot(up, n)))
    sd = np.cross(n, up)
    # the lug plate stands proud of the face
    S, E = rrect_section(w, h, 0.006, nc=4, ns=2)
    Cp = np.stack([o, o + n * t], 0)
    G = sweep(acc, Cp, np.tile(sd, (2, 1)), np.tile(up, (2, 1)), S,
              mat, base, aux, wear, edge=E, smooth=False)
    cap_flat(acc, o + n * t, sd, up, S, mat, base, aux, wear, edge=E)
    if weld:
        A = np.concatenate([S, np.zeros((len(S), 1))], 1)
        n2 = section_outward(S)
        Aw = o[None, :] + (S[:, 0:1] + n2[:, 0:1] * 0.0052) * sd[None, :] + \
            (S[:, 1:2] + n2[:, 1:2] * 0.0052) * up[None, :]
        Bw = o[None, :] + S[:, 0:1] * sd[None, :] + S[:, 1:2] * up[None, :] \
            + n[None, :] * 0.0050
        NA = np.tile(n, (len(S), 1))
        NB = (n2[:, 0:1] * sd[None, :] + n2[:, 1:2] * up[None, :])
        weld_bead(acc, Aw, Bw, NA, NB, mat, base, (0.3, 1.0, 0.0, aux[3]),
                  wear, bulge=0.0021, uid=uid, closed=True)
    for i in range(holes):
        hy = (i - (holes - 1) * 0.5) * (h * 0.42)
        hc = o + n * (t * 0.5) + up * hy
        th = np.arange(18) * TAU / 18
        rings = []
        for (rr, ss) in ((hole_r, -t * 0.5), (hole_r, t * 0.5)):
            P = hc[None, :] + n[None, :] * ss + rr * (
                np.cos(th)[:, None] * sd[None, :] + np.sin(th)[:, None] * up[None, :])
            i0 = acc.verts(P, uv=np.stack([th * rr, np.full(18, ss)], -1),
                           base=base,
                           aux=np.tile(np.array([0.6, 0.0, 0.9, aux[3]]), (18, 1)),
                           wear=wear)
            rings.append(i0 + np.arange(18))
        bridge(acc, rings[0], rings[1], mat, smooth=True, flip=True)
    return Frame(o + n * t, sd, n, up, max(w, h) * 0.5, "bracket")


# --------------------------------------------------------------------------- #
#  8.  the specification layer  (deterministic, no Blender)                     #
# --------------------------------------------------------------------------- #
#
# The three variation axes the manifest already decided:
#     scaffold tube vs box section  ->  KINDS
#     base plate & pins             ->  BASES
#     paint                         ->  PAINTS
# Every one of them changes the GEOMETRY, not a transform.  A 'tube' column and
# an 'shs' column do not share a vertex, a base plate and a base jack do not
# share a topology, and a galvanised column and a painted one differ in the
# mesh as well (paint means overpainted couplers, a strimmer-scarred foot and
# no zinc runs).

KINDS = ("tube", "shs", "angle", "shoe")
BASES = ("scaffold_baseplate", "adjustable_jack", "welded_plate_anchor",
         "ground_pin", "concrete_socket")
PAINTS = ("galv", "galv_band", "painted", "primer", "worn_paint")

# build_dressing's SHELTER_COLS, verbatim, so a marshal post is the same family
# of colours whichever module built the part.  Plus two circuit-furniture greys.
COLUMN_COLOURS = ['#2f4f6d', '#5d6b57', '#7a2f2a', '#3b3f45', '#8a7a4a',
                  '#2b5c50', '#9a978c', '#b0921f']
PRIMER_COL = '#7c3a22'


class ColumnSpec:
    """Every per-instance decision for ONE column, drawn from one integer uid."""

    __slots__ = ("uid", "kind", "base", "paint", "colour", "h", "pos", "role",
                 "lean_deg", "lean_dir", "bow", "od", "wall", "bw", "bh",
                 "corner_r", "dents", "drips", "couplers", "brackets", "holes",
                 "ties", "tag", "cap", "age", "dirt", "rust", "chip", "res",
                 "bands", "kink",
                 "yaw", "sole", "post_uid", "gussets", "mid_z", "screen_z",
                 "sign_z", "phone_z", "deck_z", "notes")

    def __repr__(self):
        return ("ColumnSpec(uid=%s %s/%s/%s h=%.3f role=%s)"
                % (self.uid, self.kind, self.base, self.paint, self.h,
                   self.role))


def column_spec(uid, kind=None, base=None, paint=None, h=None, role="corner",
                pos=(0.0, 0.0), yaw=0.0, post_uid=0, deck_z=0.0, res=1.0,
                colour=None, age=None):
    """-> ColumnSpec.  Deterministic; overrides win."""
    k = float(uid)
    sp = ColumnSpec()
    sp.uid = uid
    sp.post_uid = post_uid
    sp.role = role
    sp.pos = (float(pos[0]), float(pos[1]))
    sp.yaw = float(yaw)
    sp.res = float(res)
    sp.deck_z = float(deck_z)
    sp.notes = []

    sp.kind = kind or pick(KINDS, k, "kind")
    sp.base = base or pick(BASES, k, "base")
    sp.paint = paint or pick(PAINTS, k, "paint")
    # a scaffold post is not welded to an anchor plate, and a box frame is not
    # stood on a loose scaffold plate: the two axes are not independent in the
    # real world and pretending they are is what makes procedural work read as
    # noise instead of as an object.
    if sp.kind == "tube" and sp.base in ("welded_plate_anchor",):
        sp.base = "scaffold_baseplate" if chance(0.6, k, "bfix") else "adjustable_jack"
    if sp.kind in ("shs", "angle") and sp.base in ("adjustable_jack",):
        sp.base = "welded_plate_anchor"
    if sp.kind == "shoe":
        sp.base = "welded_plate_anchor"
    if sp.kind == "tube" and sp.paint == "primer":
        sp.paint = "galv_band"

    sp.h = float(h) if h is not None else rnd(2.15, 2.62, k, "h")
    sp.colour = colour or pick(COLUMN_COLOURS, k, "col")
    sp.age = float(age) if age is not None else rnd(0.10, 0.98, k, "age")
    sp.dirt = rnd(0.25, 1.00, k, "dirt")
    sp.rust = rnd(0.02, 0.85, k, "rust") * (0.35 + 0.9 * sp.age)
    sp.chip = (rnd(0.05, 0.35, k, "chip") if sp.paint == "painted"
               else rnd(0.45, 0.95, k, "chip") if sp.paint == "worn_paint"
               else rnd(0.10, 0.40, k, "chip"))

    sp.lean_deg = rnd(0.0, 1.9, k, "lean") ** 1.5
    sp.lean_dir = rnd(0.0, 360.0, k, "leand")
    sp.bow = rnd(-0.0075, 0.0075, k, "bow")

    # --- section -----------------------------------------------------------
    if sp.kind in ("tube", "shoe"):
        sp.od = TUBE_OD * rnd(0.995, 1.005, k, "od")
        sp.wall = pick([0.0032, 0.0032, 0.0040, 0.0026], k, "wall")
        sp.bw = sp.bh = sp.od
        sp.corner_r = sp.od * 0.5
    elif sp.kind == "shs":
        sp.bw = pick([0.060, 0.060, 0.050, 0.080], k, "bw")
        sp.bh = sp.bw if chance(0.72, k, "sq") else pick([0.040, 0.060], k, "bh")
        sp.wall = pick([0.0030, 0.0030, 0.0040, 0.0025], k, "wall")
        sp.corner_r = sp.wall * 2.5
        sp.od = max(sp.bw, sp.bh)
    else:                                                    # angle
        sp.bw = pick([0.060, 0.070, 0.050], k, "bw")
        sp.bh = sp.bw
        sp.wall = pick([0.0060, 0.0070, 0.0050], k, "wall")
        sp.corner_r = 0.0025
        sp.od = sp.bw

    sp.sole = chance(0.55, k, "sole") and sp.base in ("scaffold_baseplate",
                                                      "ground_pin")

    # --- knock history -----------------------------------------------------
    nd = rint(2, 8, k, "nd")
    sp.dents = []
    for i in range(nd):
        # one knock in three is a proper hit -- a dropped scaffold board or a
        # recovery tractor -- and those have to show in the SILHOUETTE, not
        # just in the shading.  0.9-5.2 mm is 0.6-3.2 screen px of profile.
        big = chance(0.34, k, "dbig", i)
        sp.dents.append(dict(
            z=rnd(0.03, 0.96, k, "dz", i) * sp.h,
            th=rnd(0.0, TAU, k, "dth", i),
            depth=(rnd(0.0026, 0.0052, k, "dd", i) if big
                   else rnd(0.0009, 0.0026, k, "dd", i)),
            sz=(rnd(0.020, 0.045, k, "dsz", i) if big
                else rnd(0.008, 0.022, k, "dsz", i)),
            sth=(rnd(0.40, 0.85, k, "dsth", i) if big
                 else rnd(0.20, 0.52, k, "dsth", i)),
            lip=rnd(0.14, 0.38, k, "dlip", i)))
    # a permanent set: a tube that has been hit hard enough stays bent, and a
    # bent leg is the single most legible sign that a post has a history
    sp.kink = None
    if chance(0.30, k, "kink"):
        sp.kink = dict(z=rnd(0.25, 0.80, k, "kz") * sp.h,
                       amp=rnd(0.004, 0.017, k, "kamp"),
                       dirn=rnd(0.0, 360.0, k, "kdir"),
                       slope=rnd(0.0, 0.011, k, "kslope"))
    sp.drips = []
    if sp.paint in ("galv", "galv_band"):
        for i in range(rint(2, 9, k, "ndr")):
            sp.drips.append(dict(
                z=rnd(0.0, 0.30, k, "drz", i) ** 1.7 * sp.h,
                th=rnd(0.0, TAU, k, "drth", i),
                hgt=rnd(0.00025, 0.0011, k, "drh", i),
                sz=rnd(0.010, 0.038, k, "drsz", i),
                sth=rnd(0.10, 0.26, k, "drst", i)))

    # --- what it carries ---------------------------------------------------
    sp.couplers, sp.brackets, sp.holes, sp.ties = [], [], [], []
    sp.gussets = 0
    sp.mid_z = sp.deck_z if sp.deck_z > 0.02 else rnd(0.42, 0.62, k, "mz")
    sp.screen_z = rnd(0.95, 1.30, k, "scz") + sp.deck_z
    sp.sign_z = rnd(1.52, 1.94, k, "sgz")
    sp.phone_z = rnd(1.12, 1.36, k, "phz")
    # painted marker bands on galvanised tube: post identification colours,
    # brushed on by hand, and the first thing to chip.
    sp.bands = []
    if sp.paint == "galv_band":
        for i in range(rint(1, 2, k, "nb")):
            b0 = rnd(0.18, 0.86, k, "bz", i) * sp.h
            sp.bands.append((b0, b0 + rnd(0.085, 0.230, k, "bwid", i)))
        if chance(0.45, k, "topband"):
            sp.bands.append((sp.h - rnd(0.10, 0.20, k, "tb"), sp.h + 0.02))
    sp.tag = chance(0.34, k, "tag") and sp.kind in ("tube", "shoe")
    sp.cap = pick(["open", "open", "plastic", "welded", "plastic"], k, "cap")
    if sp.kind in ("shs", "angle"):
        sp.cap = pick(["welded", "welded", "open", "plastic"], k, "cap2")
        sp.gussets = rint(0, 2, k, "gus")
    for i in range(rint(0, 3, k, "nties")):
        sp.ties.append(dict(z=rnd(0.35, 0.97, k, "tz", i) * sp.h,
                            kind=0 if chance(0.6, k, "tk", i) else 1))
    return sp


class PostFrameSpec:
    """The plan of ONE marshal post's structural frame.  No geometry."""

    __slots__ = ("uid", "kind", "paint", "colour", "W", "D", "plat", "head_z",
                 "columns", "mounts", "n_columns", "mast", "age", "notes")

    def __repr__(self):
        return ("PostFrameSpec(uid=%s %s W=%.2f D=%.2f plat=%.2f n=%d)"
                % (self.uid, self.kind, self.W, self.D, self.plat,
                   len(self.columns)))


def post_frame(uid, n_columns=None):
    """-> PostFrameSpec.  THE plan every dependant reads.

    A real post is ONE build: the four legs come off the same lorry, in the
    same system, in the same paint.  What differs within a post is history —
    which leg got hit, which one was re-founded after the ground moved, how
    much zinc is left on the one facing the weather.  What differs BETWEEN
    posts is the system itself.
    """
    k = float(uid) * 7.13 + 11.0
    sp = PostFrameSpec()
    sp.uid = uid
    sp.notes = []
    sp.kind = pick(KINDS, k, "pkind")
    sp.paint = pick(PAINTS, k, "ppaint")
    if sp.kind == "tube" and sp.paint == "primer":
        sp.paint = "galv"
    sp.colour = pick(COLUMN_COLOURS, k, "pcol")
    sp.age = rnd(0.12, 0.95, k, "page")
    # build_dressing.post_pad's own draw ranges, so the frame this module
    # builds fits the shelter that module already builds round it.
    sp.W = rnd(2.10, 3.40, k, 301)
    sp.D = rnd(1.50, 2.30, k, 302)
    Hh = rnd(2.15, 2.55, k, 303)
    sp.plat = rnd(0.75, 1.15, k, 308) if chance(0.40, k, "raised") else 0.0
    sp.head_z = sp.plat + Hh
    sp.mast = chance(0.55, k, "mast")

    hw, hd = sp.W * 0.5, sp.D * 0.5
    roles = [("corner_fl", (-hw, -hd)), ("corner_fr", (hw, -hd)),
             ("corner_rl", (-hw, hd)), ("corner_rr", (hw, hd))]
    if sp.W > 2.85 and chance(0.65, k, "mid"):
        roles.append(("mid_rear", (0.0, hd)))
    if sp.mast:
        mx = (1.0 if chance(0.5, k, "mside") else -1.0) * (hw + rnd(0.55, 1.05, k, "moff"))
        roles.append(("mast", (mx, -hd - rnd(0.10, 0.55, k, "mdep"))))
    if n_columns is not None:
        while len(roles) > n_columns:
            roles.pop()
        i = 0
        while len(roles) < n_columns:
            # a brace leg: real posts grow a fifth and sixth leg where the
            # ground has moved or a bay has been added
            sx = (1.0 if (i % 2) else -1.0) * hw
            roles.append(("brace_%d" % i, (sx, hd + rnd(0.45, 0.85, k, "bd", i))))
            i += 1

    sp.columns = []
    for i, (role, pos) in enumerate(roles):
        cu = uid * 1000 + i
        h = (sp.head_z + rnd(-0.02, 0.02, cu, "hj")) if role != "mast" else \
            rnd(2.55, 3.25, cu, "mh")
        kind = sp.kind
        base = None
        paint = sp.paint
        # one leg in six has been replaced or re-founded — a different base,
        # sometimes a different section entirely.
        if chance(0.16, cu, "replaced"):
            base = pick(BASES, cu, "rbase")
            sp.notes.append("%s re-founded" % role)
        if chance(0.09, cu, "resection"):
            kind = pick(KINDS, cu, "rkind")
            sp.notes.append("%s replaced with %s" % (role, kind))
        if role == "mast":
            kind = "tube" if chance(0.7, cu, "mk") else "shs"
        cs = column_spec(cu, kind=kind, base=base, paint=paint, h=h,
                         role=role, pos=pos, post_uid=uid,
                         deck_z=(sp.plat if role.startswith("corner") else 0.0),
                         colour=sp.colour,
                         age=float(np.clip(sp.age + rnd(-0.18, 0.18, cu, "ag"),
                                           0.02, 1.0)))
        # what each leg carries — decided at the FRAME level, because the deck
        # bearer runs between two named legs and a dependant has to know which.
        if role.startswith("corner"):
            front = role.endswith("fl") or role.endswith("fr")
            left = role.endswith("fl") or role.endswith("rl")
            ax_x = 1.0 if left else -1.0
            ax_y = 1.0 if front else -1.0
            cs.couplers.append(dict(z=sp.plat - 0.075 if sp.plat > 0.02
                                    else rnd(0.40, 0.55, cu, "cz0"),
                                    dirx=ax_x, diry=0.0, kind=0, tag="deck_bearer"))
            cs.couplers.append(dict(z=(sp.plat - 0.075 if sp.plat > 0.02
                                       else rnd(0.40, 0.55, cu, "cz0")) - 0.062,
                                    dirx=0.0, diry=ax_y, kind=0, tag="deck_transom"))
            cs.couplers.append(dict(z=sp.head_z - rnd(0.06, 0.16, cu, "cz1"),
                                    dirx=ax_x, diry=0.0, kind=0, tag="roof_bearer"))
            if chance(0.62, cu, "c3"):
                cs.couplers.append(dict(z=cs.screen_z, dirx=0.0, diry=ax_y,
                                        kind=0, tag="screen_rail"))
            if chance(0.40, cu, "c4"):
                cs.couplers.append(dict(z=rnd(0.75, 1.55, cu, "cz4"),
                                        dirx=ax_x * 0.72, diry=ax_y * 0.69,
                                        kind=1, tag="brace"))
        elif role == "mid_rear":
            cs.couplers.append(dict(z=sp.head_z - rnd(0.08, 0.20, cu, "cz1"),
                                    dirx=1.0, diry=0.0, kind=0, tag="roof_purlin"))
            cs.couplers.append(dict(z=cs.phone_z, dirx=0.0, diry=1.0, kind=0,
                                    tag="phone_rail"))
        elif role == "mast":
            cs.couplers = []
            cs.tag = chance(0.5, cu, "mtag")
        else:
            cs.couplers.append(dict(z=rnd(0.9, 1.6, cu, "bz"), dirx=0.0,
                                    diry=-1.0, kind=1, tag="brace"))
        sp.columns.append(cs)
    sp.n_columns = len(sp.columns)
    # PLAN-LEVEL MOUNTS, in POST-LOCAL coordinates.  Only the frames that are
    # exact from the plan alone appear here: a leg's ground point, its deck
    # level and its nominal head.  Everything that hangs off a FITTING --
    # ledger stubs, screen saddles, the sign band, the phone lug -- depends on
    # where the shaft actually is after its lean, bow and kink, and those are
    # millimetre-scale offsets this layer does not know.  Those frames exist
    # only on a BUILT PostFrame, in world coordinates.  Declaring them here
    # and leaving them empty is how a dependant ends up bolting a sign to a
    # position no steel occupies, so this dict tells the truth about what it
    # can and cannot answer.
    sp.mounts = {}
    ex = np.array([1.0, 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    for cs in sp.columns:
        r = cs.role.replace("corner_", "")
        x, y = cs.pos
        rad = cs.od * 0.5 if cs.kind in ("tube", "shoe") else \
            0.5 * math.hypot(cs.bw, cs.bh)
        sp.mounts["foot_%s" % r] = Frame((x, y, 0.0), ex, ey, ez, rad,
                                         "foot_%s" % r)
        sp.mounts["head_nominal_%s" % r] = Frame((x, y, cs.h), ex, ey, ez, rad,
                                                 "head_nominal_%s" % r)
        if cs.deck_z > 0.02:
            sp.mounts["deck_level_%s" % r] = Frame((x, y, cs.deck_z), ex, ey,
                                                   ez, rad, "deck_level_%s" % r)
    return sp


# --------------------------------------------------------------------------- #
#  9.  base assemblies — variation axis 2, "base plate & pins"                  #
# --------------------------------------------------------------------------- #
#
# Five topologies, not five parameter values.  BASE_EMBED_M is honoured by
# every one of them: the lowest geometry sits at -0.020 m or below, so nothing
# floats and nothing has to be told what the ground height is twice.

EMBED = C.BASE_EMBED_M


def _ch(sp, member_id=0.0):
    """The four per-vertex channels for this column's steelwork.

    base.a is PAINT COVERAGE: 1 where the base colour applies, 0 where the
    surface is bare zinc.  MPC_Galv reads it as the marker-band mask; MPC_Paint
    is only ever assigned to fully-painted members and reads it as a
    coverage floor.  Per-member dye drift lives in aux.a (the instance uid),
    not here, so the two meanings cannot collide.
    """
    col = srgb(sp.colour if sp.paint in ("painted", "worn_paint", "galv_band")
               else PRIMER_COL if sp.paint == "primer" else '#8d9296')
    cov = 1.0 if sp.paint in ("painted", "worn_paint", "primer") else 0.0
    base = (col[0], col[1], col[2], cov if member_id == 0.0 else member_id)
    aux = (0.3, 0.0, 0.0, hash01(sp.uid, "u"))
    wear = (sp.chip, sp.dirt, sp.rust, sp.age)
    return base, aux, wear


def _paint_mat(sp):
    return MAT_PAINT if sp.paint in ("painted", "worn_paint", "primer") \
        else MAT_GALV


def build_base(acc, sp, S_foot, out_dirs, mats_unused=None):
    """Emit the column's base assembly.  -> z where the shaft starts.

    S_foot is the column's own section (K,2) at its foot, so the fillet weld
    and the shoe fit the section that is actually there.
    """
    base, aux, wear = _ch(sp)
    mat = _paint_mat(sp)
    gal = MAT_GALV
    k = float(sp.uid)
    r_circ = float(np.max(np.linalg.norm(S_foot, axis=1)))

    if sp.base == "scaffold_baseplate":
        t = 0.005
        hw = rnd(0.070, 0.078, k, "bpw")
        z_sole = 0.0
        if sp.sole:
            # a timber sole board, half buried, mud-stained, sawn ends
            sw, sd, st = rnd(0.14, 0.24, k, "sw"), rnd(0.20, 0.42, k, "sd"), 0.036
            bt, ba, bw = (0.28, 0.20, 0.12, 0.4), (0.55, 0.0, 0.2, aux[3]), \
                (0.2, sp.dirt, 0.1, sp.age)
            plate(acc, sw * 0.5, sd * 0.5, st, [(0.0, 0.0, 0.0035)], MAT_TIMBER,
                  bt, ba, bw, z0=-EMBED - 0.012, chamfer=0.0016, step=0.010,
                  nv=4, nv_bot=2, uid=k)
            z_sole = -EMBED - 0.012 + st
        else:
            z_sole = -EMBED
        holes = [(x * hw * 0.62, y * hw * 0.62, 0.009)
                 for x in (-1, 1) for y in (-1, 1)]
        plate(acc, hw, hw, t, holes, gal if sp.paint != "painted" else mat,
              base, aux, wear, z0=z_sole, uid=k)
        # the spigot the tube drops over
        zs = np.linspace(z_sole + t, z_sole + t + 0.115, 6)
        S = circle_section(30, TUBE_OD * 0.5 - TUBE_WALL - 0.0010)[0]
        Cp = np.stack([np.zeros(6), np.zeros(6), zs], -1)
        u = np.tile(np.array([1.0, 0, 0]), (6, 1))
        v = np.tile(np.array([0, 1.0, 0]), (6, 1))
        sweep(acc, Cp, u, v, S, gal, base, aux, wear, smooth=True)
        cap_flat(acc, Cp[-1], u[0], v[0], S, gal, base, aux, wear)
        section_fillet_weld(acc, circle_section(30, TUBE_OD * 0.5 - TUBE_WALL)[0],
                            z_sole + t, 0.0055, 0.0050, gal, base,
                            (0.3, 1.0, 0.0, aux[3]), wear, uid=k)
        if sp.sole:
            for i in range(rint(2, 4, k, "nnail")):
                hx, hy, _r = holes[i % 4]
                nail(acc, np.array([hx, hy, z_sole + t + 0.0015]),
                     np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), 0.0022,
                     0.0060, 0.0022, 0.055, MAT_FORGED, base,
                     (0.9, 0, 0.3, aux[3]), wear, uid=k + i)
        return z_sole + t

    if sp.base == "adjustable_jack":
        t = 0.006
        hw = 0.075
        holes = [(x * 0.046, y * 0.046, 0.009) for x in (-1, 1) for y in (-1, 1)]
        plate(acc, hw, hw, t, holes, gal, base, aux, wear, z0=-EMBED, uid=k)
        stem_r = 0.0130
        pitch = 0.0060
        ext = rnd(0.075, 0.235, k, "jack")
        z0 = -EMBED + t
        thread_stud(acc, np.array([0.0, 0.0, z0]), np.array([1.0, 0, 0]),
                    np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), stem_r,
                    pitch, ext + 0.075, MAT_FORGED, base, aux, wear,
                    nseg=28, rows_per_pitch=6, uid=k, chamfer=False)
        # the collar nut: a pressed steel wheel with two tommy lugs
        nz = z0 + ext
        hex_nut(acc, np.array([0.0, 0.0, nz]), np.array([1.0, 0, 0]),
                np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), 0.0505, 0.0225,
                stem_r * 0.94, MAT_FORGED, base, aux, wear, nseg=44,
                pitch=pitch, uid=k)
        for a in (0.0, math.pi):
            d = np.array([math.cos(a), math.sin(a), 0.0])
            box_beam(acc, np.array([0.0, 0.0, nz + 0.011]) + d * 0.024,
                     np.array([0.0, 0.0, nz + 0.011]) + d * 0.052,
                     0.0085, 0.0085, MAT_FORGED, base,
                     (0.8, 0, 0.2, aux[3]), wear, nrow=1)
        return nz + 0.0225 - 0.0035

    if sp.base == "welded_plate_anchor":
        t = pick([0.008, 0.010, 0.012], k, "bt")
        hw = max(r_circ + rnd(0.032, 0.055, k, "bmar"), 0.070)
        hd = hw
        holes = [(x * (hw - 0.021), y * (hd - 0.021), 0.0095)
                 for x in (-1, 1) for y in (-1, 1)]
        # grout bed: a mortar pad squeezed out under the plate
        gt = rnd(0.008, 0.022, k, "grout")
        nth = 40
        th = np.arange(nth) * TAU / nth
        rr = (hw * 1.30 + 0.012 * np.sin(th * 3.0 + k)
              + 0.008 * np.sin(th * 7.0 + 2.0))
        Sg = np.stack([rr * np.cos(th), rr * np.sin(th)], -1)
        zs = np.array([-EMBED - 0.010, -EMBED + gt * 0.55, -EMBED + gt])
        sc = np.array([1.0, 0.98, 0.86])
        Cp = np.stack([np.zeros(3), np.zeros(3), zs], -1)
        Sarr = Sg[None] * sc[:, None, None]
        gb = (0.19, 0.18, 0.165, 0.0)
        G = sweep(acc, Cp, np.tile([1.0, 0, 0], (3, 1)),
                  np.tile([0, 1.0, 0], (3, 1)), Sarr, MAT_GROUT, gb,
                  (0.4, 0, 0, aux[3]), (0.1, sp.dirt, 0.05, sp.age), smooth=True)
        cap_flat(acc, np.array([0.0, 0.0, -EMBED + gt]), np.array([1.0, 0, 0]),
                 np.array([0, 1.0, 0]), Sg * 0.86, MAT_GROUT, gb,
                 (0.4, 0, 0, aux[3]), (0.1, sp.dirt, 0.05, sp.age))
        z0 = -EMBED + gt
        plate(acc, hw, hd, t, holes, mat, base, aux, wear, z0=z0, uid=k)
        zt = z0 + t
        section_fillet_weld(acc, S_foot, zt, 0.0062, 0.0058, mat, base,
                            (0.3, 1.0, 0.0, aux[3]), wear, uid=k)
        for (hx, hy, hr) in holes:
            o = np.array([hx, hy, zt])
            washer(acc, o, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]),
                   np.array([0, 0, 1.0]), 0.0150, 0.0090, 0.0030, MAT_FORGED,
                   base, (0.7, 0, 0.4, aux[3]), wear)
            hex_nut(acc, o + np.array([0, 0, 0.0030]), np.array([1.0, 0, 0]),
                    np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), 0.0240,
                    0.0130, 0.0072, MAT_FORGED, base,
                    (0.75, 0, 0.45, aux[3]), wear, nseg=42, pitch=0.0020,
                    uid=k + hx)
            stick = rnd(0.006, 0.030, k, "stick", hx, hy)
            thread_stud(acc, o + np.array([0, 0, 0.0155]), np.array([1.0, 0, 0]),
                        np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), 0.0080,
                        0.0020, stick, MAT_FORGED, base,
                        (0.6, 0, 0.95, aux[3]), wear, nseg=26,
                        rows_per_pitch=5, uid=k + hy)
        return zt

    if sp.base == "ground_pin":
        t = 0.005
        hw = rnd(0.068, 0.080, k, "bpw")
        tilt = rnd(0.0, 1.4, k, "rock")
        holes = [(x * hw * 0.60, y * hw * 0.60, 0.009)
                 for x in (-1, 1) for y in (-1, 1)]
        plate(acc, hw, hw, t, holes, MAT_GALV, base, aux, wear, z0=-EMBED,
              uid=k)
        for i in range(2):
            hx, hy, _r = holes[i * 3]
            ground_pin(acc, np.array([hx, hy, -EMBED + t + 0.004]),
                       np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), 0.0080,
                       0.010, 0.16, MAT_FORGED, base,
                       (0.8, 0, 0.3, aux[3]), wear, uid=k + i)
        # a packing stone under the high corner, because the plate rocks
        if chance(0.5, k, "pack"):
            nth = 14
            th = np.arange(nth) * TAU / nth
            rr = 0.022 * (1.0 + 0.35 * np.sin(th * 3.0 + k))
            Sg = np.stack([rr * np.cos(th), rr * np.sin(th)], -1)
            zs = np.array([-EMBED - 0.012, -EMBED - 0.004, -EMBED + 0.001])
            Cp = np.stack([np.full(3, hw * 0.5), np.full(3, -hw * 0.5), zs], -1)
            sc = np.array([0.8, 1.0, 0.75])
            sweep(acc, Cp, np.tile([1.0, 0, 0], (3, 1)),
                  np.tile([0, 1.0, 0], (3, 1)), Sg[None] * sc[:, None, None],
                  MAT_GROUT, (0.16, 0.15, 0.14, 0), (0.5, 0, 0, aux[3]),
                  (0, sp.dirt, 0, sp.age), smooth=True)
        # the spigot
        zs = np.linspace(-EMBED + t, -EMBED + t + 0.105, 5)
        S = circle_section(28, TUBE_OD * 0.5 - TUBE_WALL - 0.0010)[0]
        Cp = np.stack([np.zeros(5), np.zeros(5), zs], -1)
        sweep(acc, Cp, np.tile([1.0, 0, 0], (5, 1)),
              np.tile([0, 1.0, 0], (5, 1)), S, MAT_GALV, base, aux, wear,
              smooth=True)
        cap_flat(acc, Cp[-1], np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), S,
                 MAT_GALV, base, aux, wear)
        return -EMBED + t

    # concrete_socket: the leg is grouted straight into a blockout
    depth = rnd(0.10, 0.16, k, "sock")
    # A mortar collar is trowelled by hand round a leg and then left: it is
    # lumpy, it slumps on one side, and its top edge is ragged where the
    # trowel came off.  A cone of revolution reads as a plastic funnel.
    nth = 64
    th = np.arange(nth) * TAU / nth
    lump = (1.0 + 0.085 * np.sin(th * 3.0 + k)
            + 0.055 * np.sin(th * 5.0 + 2.3 + k)
            + 0.032 * np.sin(th * 9.0 + 1.1)
            + 0.018 * np.sin(th * 17.0 + 0.4))
    rr = (r_circ + rnd(0.030, 0.058, k, "colr")) * lump
    hcol = rnd(0.040, 0.072, k, "colh")
    zs = np.array([-EMBED - 0.02, -EMBED + hcol * 0.22, -EMBED + hcol * 0.62,
                   -EMBED + hcol])
    sc = np.array([1.0, 0.93, 0.70, 0.47])
    Sg = np.stack([rr * np.cos(th), rr * np.sin(th)], -1)
    Cp = np.stack([np.zeros(4), np.zeros(4), zs], -1)
    Cp = np.tile(Cp[:, None, :], (1, nth, 1))
    Cp[-1, :, 2] += (0.0035 * np.sin(th * 7.0 + 1.9)
                     + 0.0022 * np.sin(th * 13.0 + 0.6))
    Cp[-2, :, 2] += 0.0018 * np.sin(th * 11.0 + 2.4)
    gb = (0.20, 0.19, 0.175, 0.0)
    G = sweep(acc, Cp, np.tile([1.0, 0, 0], (4, 1)),
              np.tile([0, 1.0, 0], (4, 1)), Sg[None] * sc[:, None, None],
              MAT_GROUT, gb, (0.5, 0, 0, aux[3]),
              (0.1, sp.dirt, 0.05, sp.age), smooth=True)
    # the mortar collar closes onto the section
    Sf = S_foot * 1.02
    P = np.concatenate([Sf, np.full((len(Sf), 1), -EMBED + 0.052)], 1)
    i0 = acc.verts(P, uv=Sf, base=gb,
                   aux=np.tile(np.array([0.5, 0, 0, aux[3]]), (len(Sf), 1)),
                   wear=np.tile(np.array([0.1, sp.dirt, 0.05, sp.age]),
                                (len(Sf), 1)))
    ring = i0 + np.arange(len(Sf))
    nn = min(len(Sf), nth)
    idxA = G[-1][np.round(np.linspace(0, nth - 1e-6, len(Sf), endpoint=False)
                          ).astype(int) % nth]
    bridge(acc, idxA, ring, MAT_GROUT, smooth=False, flip=True)
    return -EMBED - 0.02


# --------------------------------------------------------------------------- #
# 10.  the shaft                                                                #
# --------------------------------------------------------------------------- #

class Shaft:
    """The column's axis: rows, points and frames, with lean and bow baked in.

    Everything that attaches to the column asks the shaft where it is, so a
    coupler on a leaning, bowed tube leans and bows with it instead of hovering
    beside it.
    """

    def __init__(self, sp, z0, z1, rows):
        self.sp = sp
        self.z0, self.z1 = z0, z1
        self.z = np.asarray(rows, float)
        d = math.radians(sp.lean_dir)
        ax = np.array([-math.sin(d), math.cos(d), 0.0])
        R = rot_axis(ax, sp.lean_deg)
        t = np.clip((self.z - z0) / max(z1 - z0, 1e-6), 0.0, 1.0)
        P = np.stack([np.zeros_like(self.z), np.zeros_like(self.z),
                      self.z - z0], -1) @ R.T
        bd = np.array([math.cos(d), math.sin(d), 0.0])
        P = P + bd[None, :] * (sp.bow * np.sin(math.pi * t))[:, None]
        kk = getattr(sp, "kink", None)
        if kk:
            kd = math.radians(kk["dirn"])
            kv = np.array([math.cos(kd), math.sin(kd), 0.0])
            u = np.clip((self.z - kk["z"]) / 0.12, 0.0, 1.0)
            off = kk["amp"] * (u * u * (3.0 - 2.0 * u))
            off = off + kk["slope"] * np.maximum(self.z - kk["z"] - 0.12, 0.0)
            P = P + kv[None, :] * off[:, None]
        P[:, 2] += z0
        self.P = P
        self.T, self.U, self.V = frames_along(P, ref=(1.0, 0.0, 0.0))
        self.t = t

    def at(self, z):
        """-> (point, u, v, w) at height z, by interpolation along the shaft."""
        zc = float(np.clip(z, self.z[0], self.z[-1]))
        i = int(np.searchsorted(self.z, zc)) - 1
        i = max(0, min(i, len(self.z) - 2))
        f = (zc - self.z[i]) / max(self.z[i + 1] - self.z[i], 1e-9)
        p = self.P[i] * (1 - f) + self.P[i + 1] * f
        w = unit(self.T[i] * (1 - f) + self.T[i + 1] * f)
        u = unit(self.U[i] * (1 - f) + self.U[i + 1] * f)
        return p, u, np.cross(w, u), w


def shaft_rows(sp, z0, z1):
    """Row stations: 6 mm base, refined at dents, drips and the two ends.

    6 mm is 3.7 screen px at this item's filmed distance; a 26 mm dent gets
    another 2 mm of refinement so its lip is a lip and not a facet.
    """
    step = 0.006 / max(sp.res, 0.2)
    zs = [np.arange(z0, z1 + step, step)]
    zs.append(np.linspace(z0, min(z0 + 0.30, z1), 90))       # foot, drips, mud
    zs.append(np.linspace(max(z1 - 0.10, z0), z1, 26))       # the cut end
    for d in sp.dents:
        a = np.clip(d["z"] - d["sz"] * 2.6, z0, z1)
        b = np.clip(d["z"] + d["sz"] * 2.6, z0, z1)
        if b > a:
            zs.append(np.linspace(a, b, max(8, int((b - a) / 0.0022))))
    kk = getattr(sp, "kink", None)
    if kk:
        a = np.clip(kk["z"] - 0.10, z0, z1)
        b = np.clip(kk["z"] + 0.22, z0, z1)
        if b > a:
            zs.append(np.linspace(a, b, 60))
    for d in sp.drips:
        a = np.clip(d["z"] - d["sz"] * 2.2, z0, z1)
        b = np.clip(d["z"] + d["sz"] * 2.2, z0, z1)
        if b > a:
            zs.append(np.linspace(a, b, 14))
    for c in sp.couplers:
        a = np.clip(c["z"] - 0.030, z0, z1)
        b = np.clip(c["z"] + 0.030, z0, z1)
        if b > a:
            zs.append(np.linspace(a, b, 10))
    z = np.unique(np.clip(np.concatenate(zs), z0, z1))
    return z


def surface_disp(sp, zrow, th, seam_th):
    """Radial displacement field on the shaft: dents, their lips, zinc runs,
    the ERW seam bead, and a slow mill-scale waviness.  Metres, (M, K)."""
    M, K = len(zrow), len(th)
    d = np.zeros((M, K))
    Z = zrow[:, None]
    TH = th[None, :]
    for dn in sp.dents:
        gz = np.exp(-((Z - dn["z"]) / dn["sz"]) ** 2)
        gt = np.exp(-(angdiff(TH, dn["th"]) / dn["sth"]) ** 2)
        g = gz * gt
        # the lip: displaced metal piles up round the rim of a knock
        rz = np.exp(-(((Z - dn["z"]) / (dn["sz"] * 1.65)) ** 2))
        rt = np.exp(-((angdiff(TH, dn["th"]) / (dn["sth"] * 1.65)) ** 2))
        d -= dn["depth"] * g
        d += dn["depth"] * dn["lip"] * np.clip(rz * rt - g, 0.0, 1.0) * 1.9
    for dr in sp.drips:
        gz = np.exp(-((Z - dr["z"]) / dr["sz"]) ** 2)
        gt = np.exp(-(angdiff(TH, dr["th"]) / dr["sth"]) ** 2)
        d += dr["hgt"] * gz * gt
    # ERW longitudinal seam: a 0.55 mm bead the mill never quite dressed off
    if sp.kind in ("tube", "shoe"):
        d += 0.00055 * np.exp(-(angdiff(TH, seam_th) / 0.085) ** 2) * \
            (0.7 + 0.3 * np.sin(Z * 41.0 + seam_th))
    # Mill waviness.  The first version ran at 0.12 mm on a 140 mm period,
    # which under a 12.5 deg sun read as bamboo banding down every tube --
    # a 4 % surface slope is a visible shading step even though the amplitude
    # is a tenth of a pixel.  Real drawn tube is wavy over ~0.7 m, not 0.14 m.
    d += 0.00016 * np.sin(Z * 8.6 + TH * 0.7 + hash01(sp.uid, "w1") * 6.3)
    d += 0.00004 * np.sin(Z * 31.0 - TH * 3.0 + hash01(sp.uid, "w2") * 6.3)
    return d


def u_bolt(acc, shaft, z, out_dir, r_sec, mat, base, aux, wear, uid=0.0,
           bar_r=0.0050, plate_w=0.055, plate_h=0.030, plate_t=0.005):
    """A U-bolt saddle round the column with a backing plate and two nuts.

    This is what actually holds a sign, a screen rail or a telephone box on a
    post, and unlike a drilled hole it needs no boolean — so it is a mount a
    dependant can rely on being there.  -> Frame on the outer face of the
    backing plate, .y outward.
    """
    p, u, v, w = shaft.at(z)
    n = unit(np.asarray(out_dir, float) - w * float(np.dot(out_dir, w)))
    s = np.cross(w, n)
    reach = r_sec + bar_r + 0.0016
    leg = 0.030 + rnd(0.0, 0.012, uid, "ubleg")
    th = np.linspace(-math.pi * 0.5, math.pi * 0.5, 30)
    arc = p[None, :] + reach * (np.cos(th)[:, None] * (-n)[None, :]
                                + np.sin(th)[:, None] * s[None, :])
    path = np.concatenate([(arc[0] + n * leg)[None, :], arc,
                           (arc[-1] + n * leg)[None, :]], 0)
    T2, U2, V2 = frames_along(path, ref=w)
    S = circle_section(14, bar_r)[0]
    sweep(acc, path, U2, V2, S, mat, base, aux, wear, smooth=True)
    for e in (path[0], path[-1]):
        cap_flat(acc, e, U2[0], V2[0], S, mat, base,
                 (0.7, 0.0, 0.9, aux[3]), wear)
    # backing plate spanning the two legs, then a washer and a nut on each
    pw = max(plate_w, 2.0 * reach + 0.020)
    pn = leg - 0.013
    pc = p + n * pn
    S2, E2 = rrect_section(pw, plate_h, 0.004, nc=3, ns=2)
    Cp = np.stack([pc - n * plate_t * 0.5, pc + n * plate_t * 0.5], 0)
    sweep(acc, Cp, np.tile(s, (2, 1)), np.tile(w, (2, 1)), S2, mat, base,
          aux, wear, edge=E2, smooth=False)
    cap_flat(acc, Cp[0], s, w, S2, mat, base, aux, wear, edge=E2, flip=True)
    cap_flat(acc, Cp[1], s, w, S2, mat, base, aux, wear, edge=E2)
    for sg in (-1.0, 1.0):
        o = p + n * (pn + plate_t * 0.5) + s * (sg * reach)
        washer(acc, o, s, w, n, bar_r * 2.4, bar_r * 1.12, 0.0022, MAT_FORGED,
               base, (0.7, 0, 0.4, aux[3]), wear, nseg=18)
        hex_nut(acc, o + n * 0.0022, s, w, n, 0.0170, 0.0080, bar_r * 0.92,
                MAT_FORGED, base, (0.75, 0, 0.45, aux[3]), wear, nseg=30,
                pitch=0.0015, uid=uid + sg)
    return Frame(pc + n * plate_t * 0.5, s, n, w, pw * 0.5, "ubolt")


# --------------------------------------------------------------------------- #
# 11.  the column                                                               #
# --------------------------------------------------------------------------- #

class Column:
    """One built column.  .obj, .spec, .mounts (Frames), .tris, .verts."""

    __slots__ = ("obj", "spec", "mounts", "tris", "verts", "ground_z", "owner")

    def __init__(self):
        self.mounts = {}
        self.tris = 0
        self.verts = 0
        self.ground_z = 0.0
        self.owner = ""


def column_section(sp, nseg_scale=1.0):
    """-> S (K,2), edge (K,), theta (K,), r_circ."""
    if sp.kind in ("tube", "shoe"):
        n = max(20, int(round(48 * nseg_scale)))
        S, E, th = circle_section(n, sp.od * 0.5)
    elif sp.kind == "shs":
        S, E = rrect_section(sp.bw, sp.bh, sp.corner_r,
                             nc=max(4, int(round(8 * nseg_scale))),
                             ns=max(3, int(round(7 * nseg_scale))))
        th = np.arctan2(S[:, 1], S[:, 0])
    else:
        S, E = angle_section(sp.bw, sp.bh, sp.wall,
                             nc=max(3, int(round(6 * nseg_scale))),
                             ns=max(3, int(round(5 * nseg_scale))))
        th = np.arctan2(S[:, 1], S[:, 0])
    return S, E, th, float(np.max(np.linalg.norm(S, axis=1)))


def build_column(spec, coll, mats, name=None, place=None):
    """Build ONE column.  -> Column.

    `place` is an optional (R, t) applied to every vertex and every mount
    before emit, so the caller can put the column in the world without the
    module knowing anything about the world.
    """
    sp = spec
    acc = Acc(PFX + (name or ("C%06d" % int(sp.uid))))
    base, aux, wear = _ch(sp)
    mat = _paint_mat(sp)
    S0, E0, TH0, r_circ = column_section(sp, nseg_scale=max(sp.res, 0.45))
    n2 = section_outward(S0)
    K = len(S0)
    mounts = {}

    # ---- 1. the base --------------------------------------------------------
    z_shaft0 = build_base(acc, sp, S0, None)
    if sp.kind == "shoe":
        z_shaft0 = z_shaft0 + 0.004
    if sp.base in ("scaffold_baseplate", "ground_pin") and sp.kind == "tube":
        z_shaft0 = z_shaft0 + 0.0015                 # the tube sits on the plate

    # ---- 2. the shaft -------------------------------------------------------
    rows = shaft_rows(sp, z_shaft0, sp.h)
    sh = Shaft(sp, z_shaft0, sp.h, rows)
    M = len(rows)
    seam_th = rnd(0.0, TAU, sp.uid, "seam")
    disp = surface_disp(sp, rows, TH0, seam_th)
    S = S0[None, :, :] + n2[None, :, :] * disp[:, :, None]
    # the foot ring is not displaced, so the weld and the plate still fit
    S[0] = S0
    wr = np.tile(np.asarray(wear, float), (M, 1))
    # mud and salt climb the first 350 mm; the strimmer works the first 120 mm
    climb = np.clip(1.0 - (rows - z_shaft0) / 0.35, 0.0, 1.0) ** 1.6
    wr[:, 1] = np.clip(wear[1] * (0.45 + 0.85 * climb), 0.0, 1.0)
    wr[:, 2] = np.clip(wear[2] * (0.6 + 0.9 * climb), 0.0, 1.0)
    ax = np.tile(np.asarray(aux, float), (M, 1))
    ax[:, 0] = 0.0
    A3 = np.tile(ax[:, None, :], (1, K, 1)).copy()
    A3[..., 0] = E0[None, :] * (0.65 + 0.5 * climb[:, None])
    bsr = np.tile(np.asarray(base, float), (M, 1))
    for (b0, b1) in getattr(sp, "bands", []):
        # a hand-brushed band has a wobbly edge, not a masked one
        wob = 0.004 * np.sin(rows * 47.0 + b0 * 31.0)
        cov = (np.clip((rows - b0 + wob) / 0.004, 0, 1)
               * np.clip((b1 - rows + wob) / 0.004, 0, 1))
        bsr[:, 3] = np.maximum(bsr[:, 3], cov)
    smooth = sp.kind in ("tube", "shoe")
    sweep(acc, sh.P, sh.U, sh.V, S, mat, bsr, A3, wr, smooth=smooth,
          vcoord=rows - z_shaft0)

    # ---- 3. the ends --------------------------------------------------------
    p_top, u_t, v_t, w_t = sh.at(sp.h)
    S_top = S[-1]
    if sp.cap == "open":
        open_end(acc, p_top, u_t, v_t, w_t, S_top, sp.wall, mat, base, aux,
                 wear, edge=E0, depth=0.055, uid=sp.uid, dirn=1.0)
    elif sp.cap == "plastic":
        pc = (0.05, 0.05, 0.055, 0.0)
        if chance(0.5, sp.uid, "capcol"):
            pc = srgb('#9c2a1c') + (0.0,)
        cw = 0.0022
        S_c = S_top + n2 * cw
        Cp = np.stack([p_top - w_t * 0.030, p_top + w_t * 0.004], 0)
        sweep(acc, Cp, np.tile(u_t, (2, 1)), np.tile(v_t, (2, 1)), S_c,
              MAT_POLY, pc, (0.4, 0, 0, aux[3]),
              (0.1, wear[1], 0.0, wear[3]), edge=E0, smooth=smooth)
        cap_flat(acc, p_top + w_t * 0.004, u_t, v_t, S_c * 0.995, MAT_POLY,
                 pc, (0.6, 0, 0, aux[3]), (0.1, wear[1], 0.0, wear[3]))
        open_end(acc, p_top - w_t * 0.030, u_t, v_t, w_t, S_c, cw, MAT_POLY,
                 pc, (0.4, 0, 0, aux[3]), (0.1, wear[1], 0, wear[3]),
                 depth=0.006, uid=sp.uid, dirn=-1.0)
    else:                                              # welded cap plate
        cw = 0.0035
        S_c = S_top + n2 * 0.0035
        Cp = np.stack([p_top, p_top + w_t * cw], 0)
        sweep(acc, Cp, np.tile(u_t, (2, 1)), np.tile(v_t, (2, 1)), S_c,
              mat, base, aux, wear, edge=E0, smooth=False)
        cap_flat(acc, p_top + w_t * cw, u_t, v_t, S_c, mat, base,
                 (0.25, 0, 0.2, aux[3]), wear, edge=E0)
        Aw = p_top[None, :] + (S_c[:, 0:1] + n2[:, 0:1] * 0.0006) * u_t[None, :] \
            + (S_c[:, 1:2] + n2[:, 1:2] * 0.0006) * v_t[None, :] + w_t[None, :] * cw
        Bw = p_top[None, :] + S_top[:, 0:1] * u_t[None, :] \
            + S_top[:, 1:2] * v_t[None, :] - w_t[None, :] * 0.0048
        NA = (n2[:, 0:1] * u_t[None, :] + n2[:, 1:2] * v_t[None, :])
        weld_bead(acc, Aw, Bw, NA, NA, mat, base, (0.3, 1.0, 0, aux[3]), wear,
                  bulge=0.0016, uid=sp.uid + 3.0, closed=True)
    # the foot: an open tube shows its wall where it meets the plate
    if sp.kind in ("tube", "shoe") and sp.base in ("scaffold_baseplate",
                                                   "ground_pin"):
        open_end(acc, sh.P[0], sh.U[0], sh.V[0], sh.T[0], S0, sp.wall, mat,
                 base, aux, wr[0], edge=E0, depth=0.030, uid=sp.uid + 1.0,
                 dirn=-1.0)

    # ---- 4. the shoe (hybrid columns) --------------------------------------
    if sp.kind == "shoe":
        sh_h = rnd(0.16, 0.24, sp.uid, "shoeh")
        S_s, E_s = rrect_section(sp.od + 0.028, sp.od + 0.028, 0.010, nc=6, ns=4)
        zs = np.linspace(z_shaft0 - 0.004, z_shaft0 - 0.004 + sh_h, 4)
        Cp = np.stack([np.zeros(4), np.zeros(4), zs], -1)
        sweep(acc, Cp, np.tile([1.0, 0, 0], (4, 1)),
              np.tile([0, 1.0, 0], (4, 1)), S_s, mat, base, aux,
              np.tile(np.asarray(wear, float), (4, 1)), edge=E_s, smooth=False)
        open_end(acc, Cp[-1], np.array([1.0, 0, 0]), np.array([0, 1.0, 0]),
                 np.array([0, 0, 1.0]), S_s, 0.0040, mat, base, aux, wear,
                 edge=E_s, depth=0.025, uid=sp.uid + 2.0)
        section_fillet_weld(acc, S_s, z_shaft0 - 0.004, 0.0060, 0.0056, mat,
                            base, (0.3, 1.0, 0, aux[3]), wear, uid=sp.uid + 4.0)
        for i in range(2):
            zb = z_shaft0 - 0.004 + sh_h * (0.30 + 0.42 * i)
            d = np.array([math.cos(i * 1.05), math.sin(i * 1.05), 0.0])
            o = np.array([0.0, 0.0, zb]) - d * (sp.od * 0.5 + 0.016 + 0.010)
            thread_stud(acc, o, np.array([0, 0, 1.0]), np.cross(d, [0, 0, 1.0]),
                        d, 0.0060, 0.0018, sp.od + 0.052, MAT_FORGED, base,
                        (0.6, 0, 0.9, aux[3]), wear, nseg=20, rows_per_pitch=4,
                        uid=sp.uid + i)
            hex_nut(acc, o + d * (sp.od + 0.036), np.array([0, 0, 1.0]),
                    np.cross(d, [0, 0, 1.0]), d, 0.0190, 0.0100, 0.0054,
                    MAT_FORGED, base, (0.75, 0, 0.45, aux[3]), wear, nseg=30,
                    pitch=0.0018, uid=sp.uid + i)

    # ---- 5. gussets ---------------------------------------------------------
    for i in range(sp.gussets):
        a = rnd(0.0, TAU, sp.uid, "gus", i)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        sdv = np.cross(np.array([0, 0, 1.0]), d)
        gl = rnd(0.075, 0.125, sp.uid, "gl", i)
        o = np.array([0.0, 0.0, z_shaft0]) + d * (r_circ - 0.001)
        tri_gusset(acc, o, d, sdv, np.array([0, 0, 1.0]), gl, gl * 1.05,
                   0.0060, mat, base, (0.85, 0, 0.1, aux[3]), wear,
                   uid=sp.uid + i)

    # ---- 6. couplers and brackets ------------------------------------------
    nled = 0
    for ci, c in enumerate(sp.couplers):
        z = float(np.clip(c["z"], z_shaft0 + 0.09, sp.h - 0.05))
        p, u, v, w = sh.at(z)
        d = np.array([c["dirx"], c["diry"], 0.0])
        if np.linalg.norm(d) < 1e-6:
            d = np.array([1.0, 0.0, 0.0])
        d = unit(d)
        if sp.kind in ("tube", "shoe"):
            fr = coupler(acc, p, w, d, c["kind"], mat, base, aux, wear,
                         uid=sp.uid * 3.0 + ci, r_tube=sp.od * 0.5,
                         stub=rnd(0.115, 0.175, sp.uid, "stub", ci),
                         stub_r=TUBE_OD * 0.5)
        else:
            # a welded frame does not use couplers: it uses a welded cleat and
            # a bolted splice.  Different topology, same interface.
            o = p + d * (r_circ - 0.0015)
            fr = welded_bracket(acc, o, d, w, 0.058, 0.075, 0.0070, mat, base,
                                aux, wear, uid=sp.uid * 3.0 + ci, holes=2)
            fr = Frame(fr.o, fr.x, fr.y, fr.z, 0.028, "ledger")
        mounts["ledger_%d" % nled] = fr
        mounts["ledger_%d_tag" % nled] = c.get("tag", "")
        if c.get("tag") == "deck_bearer":
            mounts["deck_seat"] = Frame(fr.o, fr.x, fr.y, fr.z, fr.r,
                                        "deck_seat")
        if c.get("tag") == "roof_bearer" or c.get("tag") == "roof_purlin":
            mounts["roof_seat"] = Frame(fr.o, fr.x, fr.y, fr.z, fr.r,
                                        "roof_seat")
        nled += 1

    # ---- 7. the mount hardware the dependants bolt to ----------------------
    outward = np.array([0.0, -1.0, 0.0])
    if sp.role.endswith("rl") or sp.role.endswith("rr") or sp.role == "mid_rear":
        outward = np.array([0.0, 1.0, 0.0])
    if sp.role.startswith("corner") or sp.role == "mid_rear":
        zsc = float(np.clip(sp.screen_z, z_shaft0 + 0.25, sp.h - 0.25))
        mounts["screen_face"] = u_bolt(acc, sh, zsc, outward, r_circ, mat,
                                       base, aux, wear, uid=sp.uid + 11.0)
    if sp.role == "corner_fl":
        zsg = float(np.clip(sp.sign_z, z_shaft0 + 0.4, sp.h - 0.18))
        mounts["sign_band"] = u_bolt(acc, sh, zsg, np.array([0.0, -1.0, 0.0]),
                                     r_circ, mat, base, aux, wear,
                                     uid=sp.uid + 12.0, plate_h=0.036)
    if sp.role in ("mid_rear", "corner_rl"):
        zph = float(np.clip(sp.phone_z, z_shaft0 + 0.4, sp.h - 0.3))
        p, u, v, w = sh.at(zph)
        o = p + np.array([0.0, 1.0, 0.0]) * (r_circ - 0.0015)
        mounts["phone_lug"] = welded_bracket(
            acc, o, np.array([0.0, 1.0, 0.0]), w, 0.070, 0.090, 0.0060, mat,
            base, aux, wear, uid=sp.uid + 13.0, holes=2, hole_r=0.0052)
    if sp.role == "mast":
        zlp = sp.h - rnd(0.10, 0.28, sp.uid, "lp")
        mounts["panel_mount"] = u_bolt(acc, sh, zlp, np.array([0.0, -1.0, 0.0]),
                                       r_circ, mat, base, aux, wear,
                                       uid=sp.uid + 14.0, plate_h=0.052)

    # ---- 8. ties, wire, tag -------------------------------------------------
    for ti, t in enumerate(sp.ties):
        z = float(np.clip(t["z"], z_shaft0 + 0.05, sp.h - 0.05))
        p, u, v, w = sh.at(z)
        if t["kind"] == 0:
            cable_tie(acc, p, u, v, w, r_circ + 0.0006, MAT_POLY,
                      (0.02, 0.02, 0.022, 0.0), (0.5, 0, 0, aux[3]),
                      (0.1, wear[1], 0.0, wear[3]), uid=sp.uid + ti)
        else:
            tie_wire(acc, p, u, v, w, r_circ + 0.0004, MAT_GALV,
                     (0.30, 0.31, 0.32, 0.0), (0.5, 0, 0.2, aux[3]),
                     (0.1, wear[1], wear[2], wear[3]), uid=sp.uid + ti,
                     turns=rnd(2.0, 4.0, sp.uid, "tw", ti))
    if sp.tag:
        z = float(np.clip(rnd(1.35, 1.75, sp.uid, "tagz"), z_shaft0 + 0.5,
                          sp.h - 0.2))
        p, u, v, w = sh.at(z)
        d = unit(np.array([rnd(-1, 1, sp.uid, "tgx"), -1.0, 0.0]))
        sdv = np.cross(w, d)
        tag_plate(acc, p + d * (r_circ + 0.020) - w * 0.052, sdv, d, w,
                  MAT_POLY, (0.55, 0.40, 0.03, 0.0), (0.5, 0, 0, aux[3]),
                  (0.2, wear[1], 0.0, wear[3]), uid=sp.uid)

    # ---- 9. the frames the dependants read ---------------------------------
    p, u, v, w = sh.at(sp.h)
    mounts["head"] = Frame(p, u, v, w, r_circ, "head")
    mounts["foot"] = Frame(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0, 0]),
                           np.array([0, 1.0, 0]), np.array([0, 0, 1.0]),
                           r_circ, "foot")
    if sp.deck_z > 0.02:
        pd, ud, vd, wd = sh.at(sp.deck_z)
        mounts["deck_level"] = Frame(pd, ud, vd, wd, r_circ, "deck_level")

    # ---- 10. emit -----------------------------------------------------------
    R = rotz(sp.yaw)
    t0 = np.array([sp.pos[0], sp.pos[1], 0.0])
    if place is not None:
        Rp, tp = place
        R = np.asarray(Rp, float) @ R
        t0 = np.asarray(Rp, float) @ t0 + np.asarray(tp, float)
    acc.xform(R, t0)
    ob = acc.emit(coll, mats, name=PFX + (name or ("C%06d" % int(sp.uid))))
    col = Column()
    col.obj = ob
    col.spec = sp
    col.mounts = {k: (v.transformed(R, t0) if isinstance(v, Frame) else v)
                  for k, v in mounts.items()}
    if ob is not None:
        col.tris = sum(max(len(p.vertices) - 2, 1) for p in ob.data.polygons)
        col.verts = len(ob.data.vertices)
        ob["mpc_kind"] = sp.kind
        ob["mpc_base"] = sp.base
        ob["mpc_paint"] = sp.paint
        ob["mpc_role"] = sp.role
        ob["mpc_height_m"] = float(sp.h)
    return col


# --------------------------------------------------------------------------- #
# 12.  shader graph DSL                                                         #
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

        R2-057.  The live order of ShaderNodeBsdfPrincipled on Blender 5.2 is

            [0] Base Color [1] Metallic [2] Roughness [3] IOR [4] Alpha
            [5] THIN WALL  [6] Normal   [7] Weight ...

        and `_feed(b, 5, <bump>)` -- written when index 5 was `Normal` -- put
        the whole relief chain of `context_pad` and `context_ground` into
        `Thin Wall`, leaving those two Principled BSDFs with an unconnected
        `Normal`.  Thin Wall is a boolean-ish shading switch, so the bump was
        computed in full and then discarded: no error, no black frame, a
        completely plausible render.  This is the same defect as
        crew_fireproof_overall's, found by sweeping for it rather than by
        looking at pictures.

        itemkit's socket check inside `selftest()` cannot see this: it asserts
        the indices ITEMKIT assumes, and `_feed` is a private copy living here.
        A helper that resolves by name and RAISES when the name is gone is the
        only version of this that a future socket move cannot break silently.

        Indices 0 and 2 (Base Color, Roughness) did not move and are left
        alone -- a rename is not a move, and neither is a socket inserted
        after you.
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
        s = self.n("ShaderNodeSeparateColor")
        self._feed(s, 0, v)
        return s

    def sepxyz(self, v):
        s = self.n("ShaderNodeSeparateXYZ")
        self._feed(s, 0, v)
        return s

    def comb(self, a=None, b=None, c=None):
        m = self.n("ShaderNodeCombineXYZ")
        self._feed(m, 0, a)
        self._feed(m, 1, b)
        self._feed(m, 2, c)
        return m

    def math(self, op, a=None, b=None, c=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._feed(m, 0, a)
        self._feed(m, 1, b)
        self._feed(m, 2, c)
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
        self._feed(m, 0, fac)
        self._feed(m, 1, a)
        self._feed(m, 2, b)
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

    def geo(self, out=1):
        g = self.n("ShaderNodeNewGeometry")
        return (g, out)


def _in(b, *names):
    for nm in names:
        if nm in b.inputs:
            return nm
    return None


class SocketGone(KeyError):
    """No candidate socket name resolved, so a value was about to vanish."""


def _set(g, b, val, *names):
    """Write `val` to the first of `names` this node actually has.

    R2-072 -- THIS USED TO DROP THE VALUE SILENTLY.

    `if nm is not None: ...` and nothing else.  Because it addresses BY NAME a
    socket INSERTION cannot break it -- that is the whole point of the shape,
    and it is why R2-057/R2-070 could not happen through this helper.  A
    socket RENAME or REMOVAL is the case it did not cover: the write would go
    nowhere, forever, and unlike a miswired relief chain it leaves no artefact
    signature at all.  `tools/socket_blend_scan.py` can see a bump that landed
    on `Thin Wall`; nothing can see a Roughness that was never written,
    because the socket just holds its default and a default is a legal value.

    MEASURED BEFORE CHANGING, because "raise" is not automatically right and
    70+ call sites that legitimately probe for an optional socket would be
    broken by it.  `tools/socket_setter_census.py`:

        147 static call sites across the four modules that use this shape
        141 of them pass ONE name, with no alternative to fall back to
          6 pass an alias list, all of them ('Specular IOR Level', 'Specular')
        328 calls OBSERVED at runtime building every material in those modules
          0 dropped
          0 alias lists that fell through to a later candidate

    So the optionality is theoretical: every alias list resolves on its FIRST
    name today, and not one call site depends on a miss being tolerated.  That
    makes raising safe now and useful later, and it keeps the alias mechanism
    intact -- this raises only when NO candidate resolved, which is exactly
    "the value was dropped".

    The alias lists are still doing real work, by the way: on 5.2 Principled
    has 'Specular IOR Level' and has NO 'Specular', so those six sites are one
    Blender version away from being the only thing standing between this
    module and a silently unset specular.
    """
    nm = _in(b, *names)
    if nm is None:
        raise SocketGone(
            "%s has no socket named %s -- its sockets are %s. This write was "
            "silently dropped before R2-072; a value that goes nowhere leaves "
            "no signature in the built blend, so it is a raise now."
            % (b.bl_idname, " / ".join(repr(n) for n in names),
               [s.name for s in b.inputs]))
    g._feed(b, nm, val)


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
    """The four per-vertex channels + object-space coordinates.

    LAW 6: TexCoord -> Object, NEVER Geometry -> Position.  At |P| ~ 1000 m a
    position-driven procedural loses all precision, and that is exactly what
    blotched the first pass.
    """
    base = g.attr("base")
    aux = g.attr("aux")
    wear = g.attr("wear")
    bs = g.sep(base)
    au = g.sep(aux)
    we = g.sep(wear)
    tc = g.n("ShaderNodeTexCoord")
    uv = g.sepxyz((tc, 2))
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    return base, aux, wear, bs, au, we, tc, uv, obj


# --------------------------------------------------------------------------- #
# 13.  materials                                                                #
# --------------------------------------------------------------------------- #
#
# Six surfaces, each built as a stack of things that PHYSICALLY HAPPENED to
# the part, in the order they happened.  A flat colour is a placeholder; so is
# a noise node wired to Base Color and nothing else.

SUNV = tuple(float(v) for v in C.SUN_DIR)


def _sun_face(g, k=1.0):
    """0..1 how square this surface faces the 12.5 deg sun.

    Geometry->Normal is a legal read (it is not Position) and it is the only
    honest way to put the season's UV fade on the sides that actually got it.
    """
    nrm = g.n("ShaderNodeNewGeometry")
    d = g.vmath('DOT_PRODUCT', (nrm, 1), SUNV)
    return g.math('MULTIPLY', g.math('MAXIMUM', (d, 1), 0.0), k, clamp=True)


def mat_galv():
    """Hot-dip galvanised steel.  Eight layers of history.

      1  the SPANGLE -- zinc freezes into 3-10 mm crystals, which at 622 px/m
         are 2-6 px across and are the single thing that says 'galvanised'.
         Each crystal gets its own normal tilt and its own brightness.
      2  the dip itself: sags, runs and the slightly wavy skin of a bath dip.
      3  WEATHERING -- bright spangly zinc goes matt mid-grey as the carbonate
         film builds.  Driven by wear.a (age), not painted on.
      4  WHITE RUST -- wet-storage staining where water has sat: chalky,
         powdery, light, and it kills the reflection completely.
      5  CONTACT POLISH on the arrises and on everything a boot or a spanner
         has touched (aux.r): brighter, smoother, slightly warm.
      6  CUT AND DRILLED FACES (aux.b) have no zinc at all -- they are bare
         steel and they are the first thing to rust.
      7  RUST bleeding out of those and out of the knocks (wear.b).
      8  ROAD DIRT climbing the first 350 mm (wear.g), keyed into the surface
         relief so it sits in the valleys.
    """
    m, g, b, _ = _new_mat("Galv")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    uid = (aux, 3)

    # ---- 1. spangle -------------------------------------------------------
    jit = g.vmath('ADD', obj, g.vmath('MULTIPLY', g.comb(uid, uid, uid),
                                      (3.1, 5.7, 2.3)))
    sp_cell = g.voro(jit, scale=165.0, rand=1.0, feature='F1')
    sp_col = g.voro(jit, scale=165.0, rand=1.0, feature='F1')
    sp_d2 = g.voro(jit, scale=165.0, rand=1.0, feature='SMOOTH_F1')
    # per-crystal brightness: Voronoi Color is a per-cell random
    cellr = g.sep((sp_col, 1))
    # discrete brightness steps: zinc crystals are individually oriented, so
    # neighbouring grains differ in a jump, not a gradient
    facet = g.math('SUBTRACT',
                   g.ramp((cellr, 0), [(0.06, (0, 0, 0)), (0.22, (0.28, 0.28, 0.28)),
                                       (0.44, (0.52, 0.52, 0.52)),
                                       (0.68, (0.80, 0.80, 0.80)),
                                       (0.90, (1, 1, 1))]), 0.5)
    # a finer second population, the way a real dip has big and small grains
    sp2 = g.voro(g.vmath('MULTIPLY', jit, (2.7, 2.7, 2.7)), scale=165.0,
                 rand=1.0, feature='F1')
    sp2c = g.sep((sp2, 1))

    # ---- 2. dip skin ------------------------------------------------------
    skin = g.noise(g.vmath('MULTIPLY', obj, (46.0, 46.0, 46.0)), scale=2.0,
                   detail=6.0, rough=0.55)
    sag = g.noise(g.vmath('MULTIPLY', obj, (7.0, 7.0, 90.0)), scale=2.0,
                  detail=5.0, rough=0.6)

    # ---- 3. weathering ----------------------------------------------------
    patch = g.noise(g.vmath('MULTIPLY', obj, (3.4, 3.4, 3.4)), scale=2.0,
                    detail=7.0, rough=0.58)
    agek = g.math('MULTIPLY', age,
                  g.math('ADD', 0.42, g.math('MULTIPLY', patch, 1.15)),
                  clamp=True)
    agek = g.math('ADD', agek, g.math('MULTIPLY', _sun_face(g), 0.12),
                  clamp=True)
    bright = g.mix(g.math('MULTIPLY', facet, 1.9),
                   (0.222, 0.232, 0.248), (0.448, 0.456, 0.462))
    bright = g.mix(g.math('MULTIPLY', (sp2c, 0), 0.30), bright,
                   (0.332, 0.339, 0.350))
    dull = g.mix(g.math('MULTIPLY', patch, 0.9), (0.078, 0.081, 0.086),
                 (0.138, 0.141, 0.146))
    col = g.mix(agek, bright, dull)

    # ---- 4. white rust ----------------------------------------------------
    wr_n = g.noise(g.vmath('MULTIPLY', obj, (11.0, 11.0, 5.5)), scale=2.5,
                   detail=8.0, rough=0.65)
    wr = g.math('MULTIPLY', g.ramp(wr_n, [(0.52, (0, 0, 0)), (0.68, (1, 1, 1))]),
                g.math('MULTIPLY', age, 1.15), clamp=True)
    wr = g.math('MULTIPLY', wr, g.math('SUBTRACT', 1.0,
                                       g.math('MULTIPLY', edge, 0.75)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', wr, 0.82), col, (0.395, 0.400, 0.392))

    # ---- 5. contact polish -------------------------------------------------
    pol = g.math('MULTIPLY', edge,
                 g.math('ADD', 0.35, g.math('MULTIPLY', skin, 0.9)), clamp=True)
    col = g.mix(g.math('MULTIPLY', pol, 0.55), col, (0.452, 0.458, 0.466))

    # ---- 6. cut faces: bare steel ------------------------------------------
    steel = g.mix(g.math('MULTIPLY', skin, 0.6), (0.205, 0.207, 0.211),
                  (0.286, 0.288, 0.293))
    col = g.mix(g.math('MULTIPLY', mach, 0.88), col, steel)

    # ---- 7. rust ------------------------------------------------------------
    rn = g.noise(g.vmath('MULTIPLY', obj, (17.0, 17.0, 9.0)), scale=3.0,
                 detail=8.0, rough=0.68)
    scab = g.voro(g.vmath('MULTIPLY', obj, (300.0, 300.0, 300.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    rk = g.math('MULTIPLY', rust,
                g.ramp(rn, [(0.40, (0, 0, 0)), (0.70, (1, 1, 1))]), clamp=True)
    rk = g.math('MULTIPLY', rk,
                g.math('ADD', 0.30, g.math('ADD',
                                           g.math('MULTIPLY', mach, 1.1),
                                           g.math('MULTIPLY', edge, 0.55))),
                clamp=True)
    # bleed: a rust stain runs DOWN, so stretch the mask vertically
    bleed = g.noise(g.vmath('MULTIPLY', obj, (26.0, 26.0, 2.2)), scale=2.5,
                    detail=7.0, rough=0.62)
    rbl = g.math('MULTIPLY', g.math('MULTIPLY', rust, bleed), 0.75, clamp=True)
    col = g.mix(g.math('MULTIPLY', rbl, 0.42), col, (0.115, 0.055, 0.026))
    col = g.mix(g.math('MULTIPLY', rk, 0.90), col,
                g.mix(g.math('MULTIPLY', (scab, 0), 0.8), (0.148, 0.055, 0.022),
                      (0.230, 0.098, 0.036)))

    # ---- 7b. THE MARKER BAND.  Hand-brushed enamel over zinc adheres badly,
    # so it chips in big flakes at the arrises and along the brush ridges, and
    # what is left has gone chalky in one season of a 12.5 deg sun.
    cov = (base, 3)
    brush = g.wave(g.vmath('MULTIPLY', obj, (1.0, 1.0, 1.0)), scale=340.0,
                   dist=7.0, detail=3.0, band='Z')
    flake = g.voro(g.vmath('MULTIPLY', obj, (120.0, 120.0, 120.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1')
    loss = g.math('MULTIPLY', chip,
                  g.math('ADD', 0.30, g.math('MULTIPLY', edge, 1.6)), clamp=True)
    off_ = g.ramp(g.math('SUBTRACT',
                         g.math('ADD', g.math('MULTIPLY', (flake, 0), 0.65),
                                g.math('MULTIPLY', brush, 0.35)),
                         g.math('MULTIPLY', loss, 0.72)),
                  [(0.16, (1, 1, 1)), (0.30, (0, 0, 0))])
    bandk = g.math('MULTIPLY', cov,
                   g.math('SUBTRACT', 1.0, g.math('MULTIPLY', (off_, 0), 0.94)),
                   clamp=True)
    bcol = g.n("ShaderNodeHueSaturation")
    g._feed(bcol, 0, 0.5)
    g._feed(bcol, 1, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', agek, 0.40)))
    g._feed(bcol, 2, g.math('ADD', 0.86, g.math('MULTIPLY', brush, 0.22)))
    g._feed(bcol, 3, 1.0)
    g._feed(bcol, 4, base)
    col = g.mix(bandk, col, bcol)

    # ---- 7c. RAIN STREAKS.  Water runs off every fitting and carries the
    # zinc carbonate down with it, so a galvanised post is striped, not evenly
    # weathered.  The stripes run vertically in WORLD terms and the column is
    # vertical, so a Z-stretched object-space noise is the honest field.
    strk = g.noise(g.vmath('MULTIPLY', obj, (34.0, 34.0, 1.35)), scale=2.5,
                   detail=8.0, rough=0.66)
    sk = g.math('MULTIPLY', g.ramp(strk, [(0.44, (0, 0, 0)), (0.63, (1, 1, 1))]),
                g.math('ADD', 0.30, g.math('MULTIPLY', age, 0.95)), clamp=True)
    sk = g.math('MULTIPLY', sk, g.math('SUBTRACT', 1.0,
                                       g.math('MULTIPLY', edge, 0.6)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', sk, 0.46), col, (0.062, 0.064, 0.061))

    # ---- 8. dirt ------------------------------------------------------------
    gr = g.noise(g.vmath('MULTIPLY', obj, (5.5, 5.5, 3.0)), scale=2.5,
                 detail=8.0, rough=0.64)
    grit = g.voro(g.vmath('MULTIPLY', obj, (620.0, 620.0, 620.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.35, g.math('MULTIPLY', gr, 1.40)), clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('SUBTRACT', 1.05,
                                       g.math('MULTIPLY', edge, 0.55)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.88), col,
                g.mix(g.math('MULTIPLY', (grit, 0), 0.5), (0.052, 0.044, 0.034),
                      (0.086, 0.072, 0.055)))
    g._feed(b, 0, col)

    # ---- metal, roughness --------------------------------------------------
    # WHY THIS IS TUNED THE WAY IT IS.  The first pass summed six roughness
    # terms and saturated at 1.0 on any weathered column; a metal at roughness
    # 1.0 is a lambertian pale grey, which is exactly what the render came back
    # as -- 120 tubes that looked like bamboo.  Zinc stays a metal all its life:
    # it gets ROUGHER and DARKER, it does not stop reflecting.  So the terms are
    # weighted to land in 0.30-0.78 and the de-metalling is only what genuinely
    # is not metal any more (white rust powder, rust scale, the painted band).
    met = g.math('SUBTRACT', 1.0, g.math('ADD',
                                         g.math('MULTIPLY', wr, 0.42),
                                         g.math('MULTIPLY', rk, 0.88)),
                 clamp=True)
    met = g.math('MULTIPLY', met, g.math('SUBTRACT', 1.0,
                                         g.math('MULTIPLY', bandk, 0.97)),
                 clamp=True)
    met = g.math('MULTIPLY', met, g.math('SUBTRACT', 1.0,
                                         g.math('MULTIPLY', dk, 0.30)),
                 clamp=True)
    _set(g, b, met, "Metallic")
    rough = g.math('ADD', 0.315, g.math('MULTIPLY', agek, 0.185))
    rough = g.math('ADD', rough, g.math('MULTIPLY', bandk, 0.115))
    rough = g.math('ADD', rough, g.math('MULTIPLY', wr, 0.165))
    rough = g.math('ADD', rough, g.math('MULTIPLY', rk, 0.240))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.110))
    rough = g.math('ADD', rough, g.math('MULTIPLY', sk, 0.130))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', pol, 0.150))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', mach, 0.095))
    rough = g.math('ADD', rough,
                   g.math('MULTIPLY', g.math('SUBTRACT', skin, 0.5), 0.085))
    rough = g.math('MINIMUM', g.math('MAXIMUM', rough, 0.22), 0.78)
    _set(g, b, rough, "Roughness")

    # ---- relief -------------------------------------------------------------
    # the spangle facets are the primary normal event; everything else rides
    # on them.
    # The spangle is the item's signature: 3-10 mm zinc crystals are 2-6 screen
    # px at 622 px/m, so each one has to tilt the normal on its own.  Distance
    # 0.0035 m is the crystal's own relief, not a guess.
    # Each crystal is a shallow facet, so the height field is the DISTANCE to
    # the cell seed (a cone per cell), not the per-cell random (which is flat
    # inside a cell and would only crease the boundaries).
    #
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # What the eye judges is what the bump does to the LIGHT, and under this
    # film's 12.47 deg sun that carries a 4.52x amplifier: m = 2 sin(theta) /
    # tan(e).  Three amplitude sets were rendered and REJECTED on the human
    # figures and every one had been chosen in millimetres.  Every
    # `modulation_pp` below REPRODUCES the Distance this module already
    # shipped, to better than 1e-6 relative -- NOTHING HERE IS A RE-TUNE.  What
    # changed is that the module now SAYS WHAT IT AIMS THE LIGHT AT, and that
    # the depths move if the sun does.
    #
    # THE WAVELENGTHS COME FROM THE SAME LITERALS THAT PICKED THE SCALES, and
    # where the coordinate is PRE-MULTIPLIED the two literals multiply:
    # `vmath('MULTIPLY', obj, (46,46,46))` into `noise(scale=2.0)` is a 17.39 mm
    # feature, not the 800 mm a reader of the Scale socket alone would report.
    # (`bump_relief_report` reads that socket alone, so do not copy its column.)
    #
    # EVERY HEIGHT HERE IS A SUM, so one wavelength per stage is a CHOICE and
    # not a reading.  The band named is the one that is ALWAYS PRESENT and
    # carries most of the height; `height_pp` is that band's own weight in the
    # sum, so the stated m is THAT band's modulation rather than a full-swing
    # fiction.  At the same Distance the other bands are:
    #
    #   [0] spangle cone  w 0.78  lam 13.15 mm  m 3.614  <- named
    #       smooth F1     w 0.22  lam 13.15 mm  m 1.104
    #       fine 2nd pop  w 0.34  lam  4.87 mm  m 4.129
    #   [1] dip skin      w 0.55  lam 17.39 mm  m 5.540  <- named
    #       drainage sag  w 0.45  lam  8.89 mm  m 7.041  (Z; 114.3 mm in XY,
    #                                                     where m 0.869)
    #       rust scab     w 0.90  lam  7.23 mm  m 8.593  gated by wear.b
    #       weld bead     w 0.35  vertex mask -- no wavelength
    #       marker band   w 0.22  mask         -- no wavelength
    #       rain streak   w 0.12  lam 18.82 mm  m 1.396  gated by age
    #   [2] road grit     w 0.50  lam  3.50 mm  m 1.048  <- named
    #       white rust    w 0.50  lam 58.18 mm  m 0.064  gated by age
    #
    # NOT RE-TUNED, AND WHY [1] IS LEFT AT 5.54.  An ungated isotropic field
    # above m ~ 1.5 is the felt this law exists to prevent, and the dip skin is
    # one.  It cannot be corrected from a call site: ONE Distance serves six
    # bands whose m spans 0.06 to 8.59, so dividing it by twelve to bring the
    # skin into isotropic_macro would take the rust scab -- a real void with
    # real walls -- down to m 0.7 with it.  The fix is to split the sum across
    # stages or reweight it, both of which are structural.  Reported, not
    # nudged.  The header above also claims Distance 0.0035 for [0]; the code
    # has always said 0.0030, and 0.0030 is what is preserved here.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 165.0     # 13.15 mm
    LAM_SKIN = K.NOISE_WAVELENGTH_FACTOR / (46.0 * 2.0)   # 17.39 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / 620.0        #  3.50 mm
    h1 = g.math('ADD', g.math('MULTIPLY', (sp_cell, 0), 0.78),
                g.math('MULTIPLY', (sp_d2, 0), 0.22))
    h1 = g.math('ADD', h1, g.math('MULTIPLY', (sp2, 0), 0.34))
    bmp = g.bump(h1, 0.78, modulation_pp=3.6143, wavelength_m=LAM_SPANGLE,
                 height_pp=0.78)
    h2 = g.math('ADD', g.math('MULTIPLY', skin, 0.55),
                g.math('MULTIPLY', sag, 0.45))
    h2 = g.math('ADD', h2, g.math('MULTIPLY', g.math('MULTIPLY', rk, (scab, 0)),
                                  0.9))
    h2 = g.math('ADD', h2, g.math('MULTIPLY', weld, 0.35))
    h2 = g.math('ADD', h2, g.math('MULTIPLY', bandk, 0.22))
    h2 = g.math('ADD', h2, g.math('MULTIPLY', sk, 0.12))
    bmp = g.bump(h2, 0.26, normal=bmp,
                 modulation_pp=5.5395, wavelength_m=LAM_SKIN, height_pp=0.55)
    fine = g.bump(g.math('ADD', g.math('MULTIPLY', (grit, 0), 0.5),
                         g.math('MULTIPLY', wr, 0.5)), 0.13, normal=bmp,
                  modulation_pp=1.048138, wavelength_m=LAM_GRIT,
                  height_pp=0.50)
    _set(g, b, fine, "Normal")
    return m


def mat_paint():
    """Chipped enamel over red-oxide primer over steel that is now rusting.

      1  the topcoat, with a per-member dye drift (base.a) so no two legs on a
         post are exactly the same blue.
      2  brush and roller ORANGE PEEL, 2-4 mm, plus runs where it was laid on
         too thick and sags where it was laid on upside down.
      3  CHALKING on the sun side: a 12.5 deg sun all season lightens and
         desaturates the top face of everything.
      4  CHIPS.  A paint film is 0.15 mm thick = 0.09 screen px, so the chip's
         RELIEF is genuinely sub-pixel and its COLOUR BOUNDARY is what reads.
         Chips key off aux.r (arrises), which is why the box sections lose
         their corners first.
      5  a second, rarer chip population that goes all the way to bare metal.
      6  RUST creeping out from under the film at the chip edges, and the
         BLEED STREAK running down from each one.
      7  road dirt in the low-gloss valleys.
      8  the weld bead (aux.g), which was painted over and now shows through as
         a different sheen.
    """
    m, g, b, _ = _new_mat("Paint")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    memb = (aux, 3)

    # ---- 1. topcoat + dye drift --------------------------------------------
    lot = g.noise(g.vmath('MULTIPLY', obj, (2.2, 2.2, 2.2)), scale=2.0,
                  detail=5.0, rough=0.55)
    k = g.math('ADD', 0.955, g.math('MULTIPLY',
                                    g.math('SUBTRACT',
                                           g.math('ADD',
                                                  g.math('MULTIPLY', lot, 0.7),
                                                  g.math('MULTIPLY', memb, 0.3)),
                                           0.5), 0.11))
    col = g.mix(0.0, base, base)
    col = g.n("ShaderNodeMixRGB", blend_type='MULTIPLY')
    g._feed(col, 0, 1.0)
    g._feed(col, 1, base)
    g._feed(col, 2, g.comb(k, k, k))

    # ---- 2. orange peel, runs, sags ----------------------------------------
    peel = g.noise(g.vmath('MULTIPLY', obj, (330.0, 330.0, 330.0)), scale=2.0,
                   detail=4.0, rough=0.5)
    # mill scale telegraphs through two coats of enamel: broad, soft, and it is
    # what stops a flat face reading as a swatch
    scale_ = g.noise(g.vmath('MULTIPLY', obj, (13.0, 13.0, 13.0)), scale=2.5,
                     detail=7.0, rough=0.62)
    runs = g.wave(g.vmath('MULTIPLY', obj, (34.0, 34.0, 1.1)), scale=6.0,
                  dist=6.0, detail=3.0, band='Z')
    runm = g.math('MULTIPLY', g.ramp(runs, [(0.62, (0, 0, 0)), (0.86, (1, 1, 1))]),
                  0.55, clamp=True)

    # ---- 3. chalking --------------------------------------------------------
    sunk = g.math('MULTIPLY', _sun_face(g),
                  g.math('ADD', 0.35, g.math('MULTIPLY', age, 0.95)),
                  clamp=True)
    hsv = g.n("ShaderNodeHueSaturation")
    g._feed(hsv, 0, 0.5)
    g._feed(hsv, 1, 0.70)
    g._feed(hsv, 2, 1.24)
    g._feed(hsv, 3, 1.0)
    g._feed(hsv, 4, col)
    col = g.mix(g.math('MULTIPLY', sunk, 0.44), col, hsv)
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', scale_, 0.45), 0.30),
                col, g.mix(0.35, col, (0.020, 0.019, 0.018)))

    # ---- 4/5. chips ----------------------------------------------------------
    # WHY THIS IS WRITTEN AS A MOVING THRESHOLD.  The first version subtracted
    # the chip drive from a noise and ramped the result over [0.10, 0.20].  The
    # noise sits around 0.49 and the drive is around 0.08, so the ramp input was
    # ~0.44 everywhere and the mask was IDENTICALLY ZERO: 57 % of the columns
    # rendered as flat cream with not one chip on them.  A mask whose threshold
    # is a constant and whose input is not normalised is a mask that never
    # fires.  Here the drive is ADDED to a 0-1 field and the ramp sits near the
    # top of the range, so an arris (edge = 1) chips and a flat (edge = 0.1)
    # does not -- which is how paint actually comes off a box section.
    cn = g.voro(g.vmath('MULTIPLY', obj, (150.0, 150.0, 150.0)), scale=1.0,
                rand=1.0, feature='SMOOTH_F1')
    cnr = g.ramp((cn, 0), [(0.0, (0, 0, 0)), (0.38, (1, 1, 1))])
    cn2 = g.noise(g.vmath('MULTIPLY', obj, (46.0, 46.0, 46.0)), scale=2.0,
                  detail=8.0, rough=0.66)
    cn3 = g.noise(g.vmath('MULTIPLY', obj, (190.0, 190.0, 190.0)), scale=2.0,
                  detail=6.0, rough=0.60)
    cm = g.math('ADD', g.math('MULTIPLY', (cnr, 0), 0.34),
                g.math('ADD', g.math('MULTIPLY', cn2, 0.46),
                       g.math('MULTIPLY', cn3, 0.20)))
    drive = g.math('MULTIPLY', chip,
                   g.math('ADD', 0.18, g.math('MULTIPLY', edge, 1.70)),
                   clamp=True)
    drive = g.math('ADD', drive, g.math('MULTIPLY', age, 0.07), clamp=True)
    chip1 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.55)),
                   [(0.885, (0, 0, 0)), (0.985, (1, 1, 1))])
    chip2 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.42)),
                   [(0.985, (0, 0, 0)), (1.070, (1, 1, 1))])
    primer = g.mix(g.math('MULTIPLY', cn2, 0.7), srgb(PRIMER_COL),
                   (0.145, 0.052, 0.030))
    col = g.mix(g.math('MULTIPLY', (chip1, 0), 0.94), col, primer)
    steel = g.mix(g.math('MULTIPLY', peel, 0.6), (0.150, 0.150, 0.154),
                  (0.230, 0.232, 0.238))
    col = g.mix(g.math('MULTIPLY', (chip2, 0), 0.92), col, steel)

    # ---- 6. rust from the chips, and the bleed ------------------------------
    scab = g.voro(g.vmath('MULTIPLY', obj, (420.0, 420.0, 420.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    rk = g.math('MULTIPLY', rust,
                g.math('ADD', g.math('MULTIPLY', (chip1, 0), 0.95),
                       g.math('ADD', g.math('MULTIPLY', mach, 0.35),
                              g.math('MULTIPLY', edge, 0.08))), clamp=True)
    bleed = g.noise(g.vmath('MULTIPLY', obj, (30.0, 30.0, 2.0)), scale=2.5,
                    detail=7.0, rough=0.62)
    rbl = g.math('MULTIPLY', g.math('MULTIPLY', rust, bleed),
                 g.math('ADD', 0.12, g.math('MULTIPLY', (chip1, 0), 1.1)),
                 clamp=True)
    col = g.mix(g.math('MULTIPLY', rbl, 0.42), col, (0.128, 0.058, 0.026))
    col = g.mix(g.math('MULTIPLY', rk, 0.92), col,
                g.mix(g.math('MULTIPLY', (scab, 0), 0.75), (0.155, 0.058, 0.024),
                      (0.245, 0.105, 0.038)))

    # ---- 7. dirt -------------------------------------------------------------
    gr = g.noise(g.vmath('MULTIPLY', obj, (6.0, 6.0, 3.2)), scale=2.5,
                 detail=8.0, rough=0.64)
    grit = g.voro(g.vmath('MULTIPLY', obj, (700.0, 700.0, 700.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.34, g.math('MULTIPLY', gr, 1.35)), clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('SUBTRACT', 1.05,
                                       g.math('MULTIPLY', edge, 0.6)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.86), col,
                g.mix(g.math('MULTIPLY', (grit, 0), 0.5), (0.050, 0.042, 0.032),
                      (0.082, 0.068, 0.052)))
    g._feed(b, 0, col)

    # ---- surface response ---------------------------------------------------
    met = g.math('ADD', g.math('MULTIPLY', (chip2, 0), 0.85),
                 g.math('MULTIPLY', mach, 0.6), clamp=True)
    met = g.math('MULTIPLY', met, g.math('SUBTRACT', 1.0,
                                         g.math('MULTIPLY', rk, 0.9)),
                 clamp=True)
    _set(g, b, met, "Metallic")
    rough = g.math('ADD', 0.28, g.math('MULTIPLY', age, 0.30))
    rough = g.math('ADD', rough, g.math('MULTIPLY', sunk, 0.24))
    rough = g.math('ADD', rough, g.math('MULTIPLY', (chip1, 0), 0.22))
    rough = g.math('ADD', rough, g.math('MULTIPLY', rk, 0.34))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.20))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', runm, 0.16))
    rough = g.math('ADD', rough,
                   g.math('MULTIPLY', g.math('SUBTRACT', peel, 0.5), 0.13),
                   clamp=True)
    _set(g, b, rough, "Roughness")
    _set(g, b, 0.45, "Specular IOR Level", "Specular")
    cw = g.math('MULTIPLY',
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', age, 0.85)),
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', (chip1, 0), 1.0)),
                clamp=True)
    _set(g, b, g.math('MULTIPLY', cw, 0.32), "Coat Weight")
    _set(g, b, g.math('ADD', 0.14, g.math('MULTIPLY', age, 0.30)),
         "Coat Roughness")

    # ---- relief -------------------------------------------------------------
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both modulations REPRODUCE the shipped Distance exactly; neither is a
    # re-tune.  The named band is the ungated one that carries the stage, and
    # `height_pp` is its own weight in the sum.  At the same Distance:
    #
    #   [0] orange peel   w 0.30  lam   2.42 mm  m 6.169  <- named
    #       paint runs    w 0.34  lam 151.52 mm  m 0.153  gated ramp, and
    #                                                     scaled x0.55 inside
    #       mill scale    w 0.22  lam  49.23 mm  m 0.305
    #       weld bead     w 0.30  vertex mask -- no wavelength
    #       chip1 (-ve)   w 0.16  mask        -- no wavelength
    #       rust scab     w 0.85  lam   5.17 mm  m 7.040  gated by wear.b
    #   [1] road grit     w 0.55  lam   3.10 mm  m 0.992  <- named
    #       orange peel   w 0.45  lam   2.42 mm  m 1.037
    #
    # NOT RE-TUNED, AND WHY [0] IS LEFT AT 6.169.  The docstring's own claim is
    # that a paint film is 0.15 mm thick and its relief is sub-pixel, so an
    # orange peel modulating radiance by 6.2 p-p is plainly not what this module
    # meant -- it is above the hard_feature ceiling and it is ungated.  But the
    # single Distance also carries the rust scab at m 7.04, which for a real
    # scale of rust IS a hard feature, and the two cannot be separated without
    # restructuring the height sum.  Left at the author's stated intent and
    # reported, rather than nudged; a 20x cut here would delete the rust.
    LAM_PEEL = K.NOISE_WAVELENGTH_FACTOR / (330.0 * 2.0)   # 2.42 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / 700.0         # 3.10 mm
    h = g.math('ADD', g.math('MULTIPLY', peel, 0.30),
               g.math('MULTIPLY', runm, 0.34))
    h = g.math('ADD', h, g.math('MULTIPLY', scale_, 0.22))
    h = g.math('ADD', h, g.math('MULTIPLY', weld, 0.30))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', (chip1, 0), 0.16))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', rk, (scab, 0)),
                                0.85))
    bmp = g.bump(h, 0.24, modulation_pp=6.169464, wavelength_m=LAM_PEEL,
                 height_pp=0.30)
    fine = g.bump(g.math('ADD', g.math('MULTIPLY', (grit, 0), 0.55),
                         g.math('MULTIPLY', peel, 0.45)), 0.11, normal=bmp,
                  modulation_pp=0.992013, wavelength_m=LAM_GRIT,
                  height_pp=0.55)
    _set(g, b, fine, "Normal")
    return m


def mat_forged():
    """Forged and hot-rolled fastener steel: couplers, nuts, bolts, pins.

    A coupler is drop-forged, so it has a scaly black oxide skin everywhere it
    was not machined, and bright turned faces everywhere it was.  aux.b is that
    boundary.  Then: wrench polish on the flats, grease in the threads, and
    rust in the crevices where the water sits.
    """
    m, g, b, _ = _new_mat("Forged")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)

    scale_ = g.noise(g.vmath('MULTIPLY', obj, (95.0, 95.0, 95.0)), scale=2.0,
                     detail=7.0, rough=0.62)
    lump = g.noise(g.vmath('MULTIPLY', obj, (28.0, 28.0, 28.0)), scale=2.0,
                   detail=6.0, rough=0.58)
    # turning marks on the machined faces: concentric, so key them off uv.u
    turn = g.wave(g.comb((uv, 0), (uv, 1), 0.0), scale=2600.0, dist=0.6,
                  detail=1.0, band='X')
    black = g.mix(g.math('MULTIPLY', lump, 0.8), (0.052, 0.050, 0.049),
                  (0.098, 0.094, 0.090))
    bright = g.mix(g.math('MULTIPLY', turn, 0.55), (0.335, 0.338, 0.345),
                   (0.445, 0.449, 0.456))
    col = g.mix(g.math('MULTIPLY', mach, 0.92), black, bright)
    pol = g.math('MULTIPLY', edge,
                 g.math('ADD', 0.4, g.math('MULTIPLY', scale_, 0.9)), clamp=True)
    col = g.mix(g.math('MULTIPLY', pol, 0.55), col, (0.512, 0.516, 0.524))
    # zinc-plated fasteners: base.a > 0.5 flags them
    zn = g.math('MULTIPLY', g.math('GREATER_THAN', (base, 3), 0.55),
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', age, 0.7)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', zn, 0.8), col, (0.485, 0.470, 0.395))
    # rust: fasteners rust in the crevices and under the nuts first
    rn = g.noise(g.vmath('MULTIPLY', obj, (46.0, 46.0, 46.0)), scale=3.0,
                 detail=8.0, rough=0.68)
    pit = g.voro(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    rk = g.math('MULTIPLY', rust,
                g.ramp(rn, [(0.35, (0, 0, 0)), (0.68, (1, 1, 1))]), clamp=True)
    rk = g.math('MULTIPLY', rk, g.math('SUBTRACT', 1.15,
                                       g.math('MULTIPLY', pol, 0.9)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', rk, 0.90), col,
                g.mix(g.math('MULTIPLY', (pit, 0), 0.7), (0.140, 0.052, 0.021),
                      (0.225, 0.094, 0.033)))
    # grease / anti-seize on the threads
    grz = g.math('MULTIPLY', mach,
                 g.math('MULTIPLY', g.noise(g.vmath('MULTIPLY', obj,
                                                    (60.0, 60.0, 60.0)),
                                            scale=2.0, detail=5.0), 1.2),
                 clamp=True)
    col = g.mix(g.math('MULTIPLY', grz, 0.35), col, (0.032, 0.028, 0.022))
    gr = g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 5.0)), scale=2.5,
                 detail=7.0, rough=0.62)
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.2, g.math('MULTIPLY', gr, 1.2)), clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.55), col, (0.048, 0.041, 0.032))
    g._feed(b, 0, col)

    met = g.math('SUBTRACT', 1.0, g.math('MULTIPLY', rk, 0.85), clamp=True)
    _set(g, b, met, "Metallic")
    rough = g.math('ADD', 0.62, g.math('MULTIPLY', rk, 0.30))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', mach, 0.30))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', pol, 0.24))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', grz, 0.16))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.15), clamp=True)
    _set(g, b, rough, "Roughness")
    h = g.math('ADD', g.math('MULTIPLY', lump, 0.42),
               g.math('MULTIPLY', scale_, 0.35))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY',
                                     g.math('MULTIPLY', rk, (pit, 0)), 0.9))
    h = g.math('ADD', h, g.math('MULTIPLY',
                                g.math('MULTIPLY', mach, turn), 0.20))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.  At the same
    # Distance the bands of [0] are:
    #
    #   [0] forge lumps   w 0.42  lam 28.57 mm  m 0.434  <- named, ungated
    #       forge scale   w 0.35  lam  8.42 mm  m 1.217  ungated
    #       rust pitting  w 0.90  lam  2.41 mm  m 6.993  gated by wear.b
    #       turning marks w 0.20  UV wave, Scale 2600 -- NO metric wavelength:
    #                             its Vector is `comb(uv.x, uv.y, 0)`, so the
    #                             pitch depends on the unwrap and this module
    #                             never states a texel density.  This is the
    #                             texture `bump_relief_report` reaches FIRST and
    #                             calls 0.385 mm / m 8.98; that number is an
    #                             artefact of traversal order and of reading a
    #                             UV scale as if it were metres.
    #   [1] rust pitting  w 0.80  lam  2.41 mm  m 1.122  <- named
    #
    # [0] is the only stage in this module whose named band sits comfortably
    # inside a RELIEF_BANDS entry (isotropic_micro) without argument.
    LAM_LUMP = K.NOISE_WAVELENGTH_FACTOR / (28.0 * 2.0)    # 28.57 mm
    LAM_PIT = K.VORONOI_WAVELENGTH_FACTOR / 900.0          #  2.41 mm
    bmp = g.bump(h, 0.26, modulation_pp=0.433841, wavelength_m=LAM_LUMP,
                 height_pp=0.42)
    _set(g, b, g.bump(g.math('MULTIPLY', (pit, 0), 0.8), 0.10, normal=bmp,
                      modulation_pp=1.12244, wavelength_m=LAM_PIT,
                      height_pp=0.80), "Normal")
    return m


def mat_timber():
    """Weathered softwood sole board: grain, checks, saw marks, mud, cement."""
    m, g, b, _ = _new_mat("Timber")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    edge, mach = (au, 0), (au, 2)
    dirt, rust, age = (we, 1), (we, 2), (wear, 3)

    # growth rings: stretched noise along the board, then banded
    ring = g.noise(g.vmath('MULTIPLY', obj, (2.0, 44.0, 44.0)), scale=3.0,
                   detail=8.0, rough=0.60)
    band = g.wave(g.comb(g.math('MULTIPLY', ring, 1.0), 0.0, 0.0), scale=26.0,
                  dist=2.0, detail=2.0, band='X')
    fib = g.noise(g.vmath('MULTIPLY', obj, (3.0, 620.0, 620.0)), scale=2.0,
                  detail=5.0, rough=0.55)
    late = g.ramp(band, [(0.35, (0, 0, 0)), (0.62, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', (late, 0), 0.85), (0.148, 0.098, 0.052),
                (0.088, 0.055, 0.028))
    col = g.mix(g.math('MULTIPLY', fib, 0.30), col, (0.175, 0.122, 0.068))
    # silvering: UV and rain take softwood to grey from the outside in
    sil = g.math('MULTIPLY', age,
                 g.math('ADD', 0.5, g.math('MULTIPLY', _sun_face(g), 0.9)),
                 clamp=True)
    col = g.mix(g.math('MULTIPLY', sil, 0.72), col,
                g.mix(g.math('MULTIPLY', (late, 0), 0.5), (0.148, 0.142, 0.130),
                      (0.098, 0.094, 0.088)))
    # checks and splits along the grain
    chk = g.wave(g.vmath('MULTIPLY', obj, (1.0, 12.0, 12.0)), scale=52.0,
                 dist=9.0, detail=3.0, band='Y')
    ck = g.math('MULTIPLY', g.ramp(chk, [(0.86, (0, 0, 0)), (0.97, (1, 1, 1))]),
                g.math('ADD', 0.25, g.math('MULTIPLY', age, 1.0)), clamp=True)
    col = g.mix(g.math('MULTIPLY', ck, 0.9), col, (0.018, 0.013, 0.009))
    # saw marks across the sawn ends
    saw = g.wave(g.comb((uv, 0), (uv, 1), 0.0), scale=520.0, dist=0.3,
                 detail=1.0, band='Y')
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', mach, saw), 0.25), col,
                (0.155, 0.115, 0.070))
    # mud and dried cement
    gr = g.noise(g.vmath('MULTIPLY', obj, (7.5, 7.5, 7.5)), scale=2.5,
                 detail=8.0, rough=0.64)
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.30, g.math('MULTIPLY', gr, 1.3)), clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.72), col, (0.048, 0.038, 0.026))
    cem = g.math('MULTIPLY',
                 g.ramp(g.noise(g.vmath('MULTIPLY', obj, (16.0, 16.0, 16.0)),
                                scale=2.5, detail=7.0),
                        [(0.60, (0, 0, 0)), (0.74, (1, 1, 1))]),
                 g.math('MULTIPLY', age, 0.9), clamp=True)
    col = g.mix(g.math('MULTIPLY', cem, 0.65), col, (0.320, 0.316, 0.305))
    g._feed(b, 0, col)
    rough = g.math('ADD', 0.72, g.math('MULTIPLY', sil, 0.18))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.10), clamp=True)
    _set(g, b, rough, "Roughness")
    _set(g, b, 0.24, "Specular IOR Level", "Specular")
    h = g.math('ADD', g.math('MULTIPLY', (late, 0), 0.42),
               g.math('MULTIPLY', fib, 0.30))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', ck, 0.85))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] latewood ring w 0.42  NO WAVELENGTH -- see below   (always present)
    #       fibre, across w 0.30  lam  1.29 mm  m 6.176  <- named, ungated
    #                             (the same noise is 266.7 mm ALONG the board;
    #                              1.29 mm is the across-grain read)
    #       checks/splits w 0.85  lam  1.60 mm  m 8.188  gated by ramp x age
    #   [1] fibre, across w 0.60  lam  1.29 mm  m 1.862  <- named
    #       saw marks     w 0.40  UV wave, Scale 520 -- no metric wavelength
    #
    # WHY THE CHARACTER BAND IS NOT THE ONE NAMED.  `late` is what a weathered
    # sole board reads as -- the soft earlywood erodes and the latewood stands
    # proud -- and it carries the most height.  It has NO wavelength that can be
    # written from a literal: `band` is a Wave whose Vector input is the ring
    # noise's VALUE, not a coordinate, so its Scale of 26.0 is 26 bands per unit
    # of noise, and converting that to a ring pitch needs the noise's mean
    # gradient, which is not in this source.  Writing a millimetre figure for it
    # would be exactly the invented constant this law exists to stop.  So the
    # named band is `fib`, which is ungated, always present, and whose 1.29 mm
    # comes straight from 620.0 x 2.0.  The ring band remains unquantified and
    # is called out here so the next reader knows it is unquantified rather
    # than assuming the stated m covers it.
    #
    # NOT RE-TUNED.  m 6.176 on an ungated field is over the hard_feature
    # ceiling, but the same Distance carries the checks at m 8.19, and a check
    # in a weathered board IS a hard edge; the two share one Distance and
    # cannot be separated without restructuring the sum.  Reported.
    LAM_FIB = K.NOISE_WAVELENGTH_FACTOR / (620.0 * 2.0)    # 1.29 mm
    bmp = g.bump(h, 0.32, modulation_pp=6.17612, wavelength_m=LAM_FIB,
                 height_pp=0.30)
    _set(g, b, g.bump(g.math('ADD', g.math('MULTIPLY', fib, 0.6),
                             g.math('MULTIPLY', saw, 0.4)), 0.12, normal=bmp,
                      modulation_pp=1.861628, wavelength_m=LAM_FIB,
                      height_pp=0.60), "Normal")
    return m


def mat_grout():
    """Mortar bedding, grout collar and packing stone."""
    m, g, b, _ = _new_mat("Grout")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    dirt, age = (we, 1), (wear, 3)
    agg = g.voro(g.vmath('MULTIPLY', obj, (150.0, 150.0, 150.0)), scale=1.0,
                 rand=1.0, feature='F1')
    aggc = g.sep((agg, 1))
    sand = g.voro(g.vmath('MULTIPLY', obj, (780.0, 780.0, 780.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    lait = g.noise(g.vmath('MULTIPLY', obj, (14.0, 14.0, 14.0)), scale=2.5,
                   detail=8.0, rough=0.62)
    col = g.mix(g.math('MULTIPLY', lait, 0.85), (0.135, 0.130, 0.122),
                (0.205, 0.200, 0.190))
    col = g.mix(g.math('MULTIPLY', (aggc, 0), 0.45), col, (0.098, 0.092, 0.084))
    col = g.mix(g.math('MULTIPLY', (sand, 0), 0.35), col, (0.245, 0.240, 0.228))
    eff = g.math('MULTIPLY', age,
                 g.ramp(g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 9.0)),
                                scale=2.5, detail=7.0),
                        [(0.55, (0, 0, 0)), (0.75, (1, 1, 1))]), clamp=True)
    col = g.mix(g.math('MULTIPLY', eff, 0.55), col, (0.330, 0.328, 0.318))
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.3, g.math('MULTIPLY', lait, 1.1)), clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.6), col, (0.042, 0.036, 0.028))
    g._feed(b, 0, col)
    _set(g, b, g.math('SUBTRACT', 0.90, g.math('MULTIPLY', (sand, 0), 0.08)),
         "Roughness")
    _set(g, b, 0.22, "Specular IOR Level", "Specular")
    h = g.math('ADD', g.math('MULTIPLY', (agg, 0), 0.5),
               g.math('MULTIPLY', lait, 0.3))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] aggregate     w 0.50  lam 14.47 mm  m 1.735  <- named, ungated
    #       laitance      w 0.30  lam 45.71 mm  m 0.335  ungated
    #   [1] sand grains   w 1.00  lam  2.78 mm  m 1.916  <- named (the height
    #                             is a single texture, so height_pp is 1.0)
    #
    # Both sit in RELIEF_BANDS["hard_feature"] (1.50-6.00) at the LOW end, and
    # that is the right claim for this surface rather than an accident: proud
    # aggregate and a sand grain in a mortar bed are real bodies with real
    # walls, not a crumple.  Nothing here is an isotropic field pretending to
    # be one.  Left as shipped.
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 150.0          # 14.47 mm
    LAM_SAND = K.VORONOI_WAVELENGTH_FACTOR / 780.0         #  2.78 mm
    bmp = g.bump(h, 0.30, modulation_pp=1.734658, wavelength_m=LAM_AGG,
                 height_pp=0.50)
    _set(g, b, g.bump((sand, 0), 0.16, normal=bmp,
                      modulation_pp=1.9162, wavelength_m=LAM_SAND), "Normal")
    return m


def mat_poly():
    """Injection-moulded polymer: end caps, cable ties, inspection tags."""
    m, g, b, _ = _new_mat("Poly")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    edge = (au, 0)
    dirt, age = (we, 1), (wear, 3)
    spark = g.voro(g.vmath('MULTIPLY', obj, (1500.0, 1500.0, 1500.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1')
    flow = g.noise(g.vmath('MULTIPLY', obj, (4.0, 260.0, 260.0)), scale=2.0,
                   detail=5.0, rough=0.55)
    col = g.mix(g.math('MULTIPLY', flow, 0.22), base, (0.030, 0.030, 0.033))
    chalk = g.math('MULTIPLY', age,
                   g.math('ADD', 0.35, g.math('MULTIPLY', _sun_face(g), 1.0)),
                   clamp=True)
    col = g.mix(g.math('MULTIPLY', chalk, 0.5), col, (0.230, 0.226, 0.216))
    gr = g.noise(g.vmath('MULTIPLY', obj, (22.0, 22.0, 22.0)), scale=2.5,
                 detail=7.0, rough=0.6)
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.25, g.math('MULTIPLY', gr, 1.2)), clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.55), col, (0.040, 0.034, 0.026))
    g._feed(b, 0, col)
    _set(g, b, g.math('ADD', 0.38, g.math('ADD',
                                          g.math('MULTIPLY', chalk, 0.34),
                                          g.math('MULTIPLY', dk, 0.16))),
         "Roughness")
    _set(g, b, 0.42, "Specular IOR Level", "Specular")
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Reproduces the shipped Distance; not a re-tune.
    #
    #   [0] EDM spark     w 0.60  lam 1.45 mm  m 1.465  <- named, ungated
    #       flow lines    w 0.40  lam 3.08 mm  m 0.465  ungated (the same noise
    #                             is 200 mm ALONG the flow; 3.08 mm is the
    #                             across-flow read)
    #
    # The spark-eroded mould skin at 1.465 is the top of
    # RELIEF_BANDS["sparse_crease"] and just under the 1.5 that would make an
    # UNGATED isotropic field the felt.  It is the only stage in this module
    # where the deepest band and the named band are the same thing, so the
    # number is a real claim about the whole surface.  Left as shipped.
    LAM_SPARK = K.VORONOI_WAVELENGTH_FACTOR / 1500.0       # 1.45 mm
    bmp = g.bump(g.math('ADD', g.math('MULTIPLY', (spark, 0), 0.6),
                        g.math('MULTIPLY', flow, 0.4)), 0.14,
                 modulation_pp=1.46507, wavelength_m=LAM_SPARK, height_pp=0.60)
    _set(g, b, bmp, "Normal")
    return m


_MATS = None


def materials(force=False):
    """The six slots, in index order.  Idempotent."""
    global _MATS
    if _MATS is not None and not force:
        if all(m.name in bpy.data.materials for m in _MATS):
            return _MATS
    _MATS = [mat_galv(), mat_paint(), mat_forged(), mat_timber(), mat_grout(),
             mat_poly()]
    return _MATS


# --------------------------------------------------------------------------- #
# 14.  the family                                                               #
# --------------------------------------------------------------------------- #

class PostFrame:
    """One built post frame: its columns and the mounts, in WORLD coordinates."""

    __slots__ = ("spec", "columns", "mounts", "origin", "yaw_deg", "ground_z",
                 "owner", "station")

    def __init__(self):
        self.columns = []
        self.mounts = {}


def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    """Idempotence: everything this module owns is MPC_* and goes first."""
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PFX) or me.users == 0:
            bpy.data.meshes.remove(me)


def build_post_frame(spec, coll, mats, origin=(0.0, 0.0, 0.0), yaw_deg=0.0,
                     res=1.0, tag=""):
    """Build every column of one post.  -> PostFrame with world-space mounts."""
    R = rotz(yaw_deg)
    t = np.asarray(origin, float)
    pf = PostFrame()
    pf.spec = spec
    pf.origin = t
    pf.yaw_deg = float(yaw_deg)
    for cs in spec.columns:
        cs.res = res
        col = build_column(cs, coll, mats,
                           name="%s%03d_%s" % (tag, int(spec.uid), cs.role),
                           place=(R, t))
        pf.columns.append(col)
        suffix = cs.role.replace("corner_", "")
        for k, v in col.mounts.items():
            if not isinstance(v, Frame):
                continue
            if k in ("head", "deck_seat", "roof_seat", "deck_level", "foot"):
                pf.mounts["%s_%s" % (k, suffix)] = v
            elif k in ("screen_face", "sign_band", "phone_lug", "panel_mount"):
                pf.mounts["%s_%s" % (k, suffix)] = v
                pf.mounts.setdefault(k, v)
            else:
                pf.mounts["%s_%s" % (suffix, k)] = v
    if spec.mast:
        for k in list(pf.mounts):
            if k.startswith("head_mast"):
                pf.mounts["panel_mast_top"] = pf.mounts[k]
    return pf


def family_plan(n_posts=25, total=120, seed=0, first=None):
    """-> [(uid, n_columns)] summing to exactly `total` columns.

    The manifest says 120 columns across 25 posts.  4.8 legs per post is not a
    number any single post has, so the plan hands out 4, 5 and 6 legs in the
    proportion that lands on 120 and lets post_frame decide which extra legs a
    given post actually grew.
    """
    uids = [seed * 100 + i for i in range(n_posts)]
    nat = []
    for u in uids:
        sp = post_frame(u)
        nat.append(len(sp.columns))
    diff = total - sum(nat)
    order = sorted(range(n_posts), key=lambda i: hash01(seed, i, "fp"))
    j = 0
    while diff != 0 and j < n_posts * 6:
        i = order[j % n_posts]
        if diff > 0 and nat[i] < 7:
            nat[i] += 1
            diff -= 1
        elif diff < 0 and nat[i] > 4:
            nat[i] -= 1
            diff += 1
        j += 1
    out = list(zip(uids, nat))
    if first is not None:
        i = [j for j, (u, _n) in enumerate(out) if u == first]
        if i:
            out.insert(0, out.pop(i[0]))
    return out


def post_plan(n=25, seed=0):
    """Where 25 marshal posts stand: corner exits first, then straight infill.

    Every station is standing on the runoff platform BEHIND the barrier face
    and inside platform_edge, so `world_ground_z` owns the ground under it and
    the placement gate has nothing to find.
    """
    corners = C.SPEC["corners"]
    out = []
    for ci, c in enumerate(corners):
        tag = c["name"].split()[0]
        e = C._EL_BY_TAG.get(tag)
        if e is None:
            continue
        s_out = (e["s0"] + e["L"] + rnd(6.0, 40.0, ci, "sx")) % C.LAP
        side = -1 if c.get("direction") == "left" else +1     # outside of turn
        out.append(dict(s=float(s_out), side=int(side), why="%s exit" % tag))
    out.sort(key=lambda p: p["s"])
    # infill so no gap exceeds 300 m
    infill = []
    for i, p in enumerate(out):
        q = out[(i + 1) % len(out)]
        gap = (q["s"] - p["s"]) % C.LAP
        if gap > 300.0:
            npt = int(gap // 260.0)
            for j in range(npt):
                ss = (p["s"] + gap * (j + 1) / (npt + 1)) % C.LAP
                sd = p["side"] if hash01(ss, "sd") < 0.5 else q["side"]
                if float(C.barrier_type(ss, sd)) in (2.0, 3.0):
                    sd = -sd
                infill.append(dict(s=float(ss), side=int(sd), why="infill"))
    out = out + infill
    out.sort(key=lambda p: p["s"])
    while len(out) > n:
        # drop the closest-spaced pair member, deterministically
        gaps = [((out[(i + 1) % len(out)]["s"] - out[i]["s"]) % C.LAP, i)
                for i in range(len(out))]
        gaps.sort()
        out.pop(gaps[0][1])
    i = 0
    while len(out) < n:
        gaps = [(((out[(j + 1) % len(out)]["s"] - out[j]["s"]) % C.LAP), j)
                for j in range(len(out))]
        gaps.sort(reverse=True)
        g, j = gaps[0]
        ss = (out[j]["s"] + g * 0.5) % C.LAP
        sd = out[j]["side"]
        if float(C.barrier_type(ss, sd)) in (2.0, 3.0):
            sd = -sd
        out.append(dict(s=float(ss), side=int(sd), why="spacing"))
        out.sort(key=lambda p: p["s"])
        i += 1
        if i > 60:
            break
    # ------------------------------------------------------------------ #
    #  Lateral placement, and the trap in it.
    #
    #  A marshal post stands BEHIND the barrier, so the obvious rule is
    #  lat = barrier_offset(s, side) + 1.6.  That rule is wrong on its own,
    #  and the first build proved it: post 6 came out with all six columns
    #  2.3-4.2 m from the centreline -- ON THE RACING SURFACE.  The circuit
    #  doubles back on itself, so a point 35 m outboard of the T4 exit is
    #  only 2.5 m from the centreline of the T4 ENTRY, and (s, u) coordinates
    #  taken at one station say nothing about how close the point is to
    #  another one.  `project` answers the question that actually matters --
    #  the distance to the NEAREST centreline -- so every candidate is
    #  re-projected, and its whole 2.9 m footprint with it.
    # ------------------------------------------------------------------ #
    def footprint_ok(x, y, need=0.35):
        a = np.linspace(0.0, TAU, 9)[:-1]
        px = np.concatenate([[x], x + 2.9 * np.cos(a)])
        py = np.concatenate([[y], y + 2.9 * np.sin(a)])
        S2, U2 = C.project(px, py)
        for i in range(len(px)):
            sd = 1 if U2[i] >= 0 else -1
            if abs(float(U2[i])) < float(C.barrier_offset(float(S2[i]), sd)) + need:
                return False
        return True

    keep = []
    for k, p in enumerate(out):
        placed = False
        for ds in (0.0, 18.0, -18.0, 40.0, -40.0, 75.0, -75.0):
            for sd in (p["side"], -p["side"]):
                ss = (p["s"] + ds) % C.LAP
                bo = float(C.barrier_offset(ss, sd))
                pe = float(C.platform_edge(ss, sd))
                for f in (rnd(1.30, 2.10, k, "lat"), 1.10, 2.60, 3.40):
                    lat = min(max(bo + f, bo + 0.9), max(pe - 0.5, bo + 0.9))
                    x, y, _z = C.su_to_world(ss, lat, sd)
                    if not footprint_ok(float(x), float(y)):
                        continue
                    gz, _own = C.world_ground_z(float(x), float(y))
                    if not np.isfinite(gz):
                        continue
                    p["s"], p["side"], p["lat"] = float(ss), int(sd), float(lat)
                    p["world"] = (float(x), float(y))
                    p["moved_m"] = float(ds)
                    placed = True
                    break
                if placed:
                    break
            if placed:
                break
        if placed:
            keep.append(p)
    dropped = len(out) - len(keep)
    out = keep
    # top up through the SAME validator, so a post added to close a gap is
    # held to the same footprint rule as one that was there from the start
    guard = 0
    while len(out) < n and guard < 400:
        guard += 1
        out.sort(key=lambda q: q["s"])
        gaps = [(((out[(j + 1) % len(out)]["s"] - out[j]["s"]) % C.LAP), j)
                for j in range(len(out))]
        gaps.sort(reverse=True)
        g, j = gaps[0]
        got = False
        for f in (0.50, 0.35, 0.65, 0.25, 0.75):
            ss = (out[j]["s"] + g * f) % C.LAP
            for sd in (out[j]["side"], -out[j]["side"]):
                bo = float(C.barrier_offset(ss, sd))
                pe = float(C.platform_edge(ss, sd))
                lat = min(max(bo + 1.6, bo + 0.9), max(pe - 0.5, bo + 0.9))
                x, y, _z = C.su_to_world(ss, lat, sd)
                gz, _own = C.world_ground_z(float(x), float(y))
                if np.isfinite(gz) and footprint_ok(float(x), float(y)):
                    out.append(dict(s=float(ss), side=int(sd), lat=float(lat),
                                    world=(float(x), float(y)), why="topup",
                                    moved_m=0.0))
                    got = True
                    break
            if got:
                break
        if not got:
            # this gap cannot take a post; nudge it so the next pass tries the
            # second-widest instead of spinning on the same one
            out[j]["s"] = (out[j]["s"] + 1.0) % C.LAP
    out.sort(key=lambda q: q["s"])
    print(">> post_plan: %d posts, %d station(s) had no legal footprint behind "
          "the barrier and were moved or replaced" % (len(out), dropped))
    for k, p in enumerate(out):
        s, side = p["s"], p["side"]
        # the post faces the circuit: post-local +Y points AWAY from the track
        _X, _Y, H, _K = C.centreline_arrays(np.array([s]))
        head = float(H[0])
        # outward bearing = the direction of increasing |lat| on this side
        outb = head + (math.pi * 0.5 if side > 0 else -math.pi * 0.5)
        p["yaw_deg"] = math.degrees(outb) - 90.0 + rnd(-7.0, 7.0, k, "yaw")
        p["k"] = k
    return out


def build(coll_name=ROOT_COLL, n_posts=25, total=120, seed=0, stations=None,
          res=1.0, do_purge=True, cam_at=None, lod=False, hero_uid=None):
    """Emit the whole family.  -> [PostFrame].

    Every column is its own vertex data from its own parameter draw — no
    linked duplicates, no geometry-nodes instancing — so per-instance variation
    is something the acceptance gate can MEASURE rather than be told about.
    """
    if do_purge:
        purge()
    mats = materials()
    root = _coll(coll_name)
    plan = stations if stations is not None else post_plan(n_posts, seed)
    fam = family_plan(len(plan), total, seed, first=hero_uid)
    frames = []
    for i, p in enumerate(plan):
        uid, ncol = fam[i]
        spec = post_frame(uid, n_columns=ncol)
        wx, wy = p["world"]
        gz, owner = C.world_ground_z(wx, wy)
        if not np.isfinite(gz):
            # terrain owns the ground here; the runoff platform's own datum is
            # the honest fallback and it is the one build_barriers uses.
            gz = float(C.ground_z(p["s"], p["lat"], p["side"]))
            owner = "fallback:ground_z"
        r = res
        if lod and cam_at is not None:
            d = math.hypot(wx - cam_at[0], wy - cam_at[1])
            r = res if d < 22.0 else (0.55 * res if d < 70.0 else 0.34 * res)
        pf = build_post_frame(spec, root, mats, origin=(wx, wy, float(gz)),
                              yaw_deg=p["yaw_deg"], res=r, tag="P")
        pf.ground_z = float(gz)
        pf.owner = str(owner)
        pf.station = p
        for col in pf.columns:
            if col.obj is not None:
                col.obj["mpc_world_ground_z"] = float(gz)
                col.obj["mpc_ground_owner"] = str(owner)
                col.obj["mpc_station_s"] = float(p["s"])
                col.obj["mpc_side"] = int(p["side"])
        frames.append(pf)
    return frames


# --------------------------------------------------------------------------- #
# 15.  the test scene                                                           #
# --------------------------------------------------------------------------- #

def contract_light(scene=None):
    """The film's one sun, plus its sky.  Numbers from world_contract S13."""
    sc = scene or bpy.context.scene
    import fix_audit_blend as FA
    FA.procedural_world()
    sun = bpy.data.objects.get("MPC_Sun")
    if sun is None:
        d = bpy.data.lights.new("MPC_Sun", 'SUN')
        sun = bpy.data.objects.new("MPC_Sun", d)
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


def context_pad(pf, name="CTX_Pad"):
    """The hardstanding the post stands on.  CONTEXT ONLY, prefixed CTX_ so the
    acceptance gate never counts it as this item."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NG(mat)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (2.2, 2.2, 2.2)), scale=2.0,
                 detail=8.0, rough=0.6)
    agg = g.voro(g.vmath('MULTIPLY', obj, (78.0, 78.0, 78.0)), scale=1.0,
                 rand=1.0, feature='F1')
    aggc = g.sep((agg, 1))
    sand = g.voro(g.vmath('MULTIPLY', obj, (560.0, 560.0, 560.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    trowel = g.wave(g.vmath('MULTIPLY', obj, (1.0, 1.0, 1.0)), scale=7.0,
                    dist=13.0, detail=4.0, band='X')
    crack = g.voro(g.vmath('MULTIPLY', obj, (0.62, 0.62, 0.62)), scale=1.0,
                   rand=1.0, feature='DISTANCE_TO_EDGE')
    col = g.mix(g.math('MULTIPLY', n1, 0.9), (0.062, 0.060, 0.055),
                (0.118, 0.114, 0.106))
    col = g.mix(g.math('MULTIPLY', trowel, 0.28), col, (0.086, 0.084, 0.079))
    # exposed aggregate where the laitance has worn off the traffic line
    expo = g.math('MULTIPLY', g.ramp(n1, [(0.42, (0, 0, 0)), (0.66, (1, 1, 1))]),
                  0.8, clamp=True)
    col = g.mix(g.math('MULTIPLY', expo, 0.55), col,
                g.mix(g.math('MULTIPLY', (aggc, 0), 0.8), (0.042, 0.040, 0.036),
                      (0.108, 0.100, 0.088)))
    col = g.mix(g.math('MULTIPLY', (sand, 0), 0.22), col, (0.145, 0.141, 0.132))
    # A slab is not crazy paving.  The first version ran the crack voronoi at
    # 2.6 cells/m with a 14 mm-wide seam, which tiled the whole hardstanding
    # into 380 mm flagstones.  Real shrinkage cracking is sparse: a few long
    # runs where the slab happened to restrain itself, and metres of nothing.
    # So the network is coarse (0.6 cells/m), the seam is 4 mm, and a coverage
    # mask deletes about three quarters of it.
    ckcov = g.ramp(g.noise(g.vmath('MULTIPLY', obj, (0.9, 0.9, 0.9)), scale=2.0,
                           detail=6.0, rough=0.6),
                   [(0.63, (0, 0, 0)), (0.74, (1, 1, 1))])
    ck = g.ramp((crack, 0), [(0.0, (1, 1, 1)), (0.0035, (0, 0, 0))])
    ck = g.math('MULTIPLY', (ck, 0), (ckcov, 0), clamp=True)
    col = g.mix(g.math('MULTIPLY', ck, 0.42), col, (0.040, 0.039, 0.036))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', 0.92, g.math('MULTIPLY', (sand, 0), 0.07)))
    bm = g.bump(g.math('SUBTRACT',
                       g.math('ADD', g.math('MULTIPLY', (agg, 0), 0.55),
                              g.math('MULTIPLY', n1, 0.25)),
                       g.math('MULTIPLY', ck, 0.30)), 0.42, 0.006)
    g._feed_named(b, "Normal", g.bump((sand, 0), 0.18, 0.0012, normal=bm))
    W = float(pf.spec.W) + 1.30
    D = float(pf.spec.D) + 1.45
    hw, hd = W * 0.5, D * 0.5
    nx, ny = 150, 150
    xs = np.linspace(-hw, hw, nx)
    ys = np.linspace(-hd, hd, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z = (0.004 * np.sin(X * 2.1) * np.cos(Y * 1.7)
         - 0.006 * np.clip(1.0 - (np.hypot(X, Y) / (hw * 0.85)), 0, 1))
    # a poured slab has a broken, gravel-buried edge, not a laser-cut one
    ang = np.arctan2(Y, X)
    rr = np.maximum(np.abs(X) / hw, np.abs(Y) / hd)
    brk = (0.012 * np.sin(ang * 7.0 + 1.3) + 0.008 * np.sin(ang * 17.0)
           + 0.005 * np.sin(ang * 31.0 + 2.1))
    Z -= np.clip((rr - (0.972 + brk)) / 0.028, 0.0, 1.0) * 0.026
    V = np.stack([X, Y, Z - 0.004], -1).reshape(-1, 3)
    idx = np.arange(nx * ny).reshape(nx, ny)
    F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                 -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = tuple(float(v) for v in pf.origin)
    ob.rotation_euler = (0.0, 0.0, math.radians(pf.yaw_deg))
    bpy.context.scene.collection.objects.link(ob)
    return ob


def context_ground(centre, size=150.0, name="CTX_Ground"):
    """The runoff platform this post stands on, out to the horizon.

    CONTEXT ONLY (CTX_ prefix, invisible to the acceptance gate).  It exists
    because a column rendered against an empty sky is a turntable, not a shot:
    without ground there is no bounce, no contact shadow and nothing for the
    eye to scale the object against.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NG(mat)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (0.9, 0.9, 0.9)), scale=2.0,
                 detail=9.0, rough=0.62)
    grav = g.voro(g.vmath('MULTIPLY', obj, (95.0, 95.0, 95.0)), scale=1.0,
                  rand=1.0, feature='F1')
    gcol = g.sep((grav, 1))
    gsm = g.voro(g.vmath('MULTIPLY', obj, (95.0, 95.0, 95.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    fines = g.voro(g.vmath('MULTIPLY', obj, (620.0, 620.0, 620.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1')
    n3 = g.noise(g.vmath('MULTIPLY', obj, (7.0, 7.0, 7.0)), scale=2.5,
                 detail=8.0, rough=0.6)
    col = g.mix(g.math('MULTIPLY', n1, 0.9), (0.030, 0.031, 0.026),
                (0.062, 0.060, 0.050))
    col = g.mix(g.math('MULTIPLY', n3, 0.55), col, (0.048, 0.043, 0.032))
    # each stone gets its own value, which is what makes gravel read as gravel
    col = g.mix(g.math('MULTIPLY', (gcol, 0), 0.72), col, (0.105, 0.100, 0.088))
    col = g.mix(g.math('MULTIPLY', (fines, 0), 0.30), col, (0.022, 0.021, 0.019))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', 0.93, g.math('MULTIPLY', (gsm, 0), 0.10)))
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (gsm, 0), 0.75),
                       g.math('MULTIPLY', n3, 0.25)), 0.55, 0.009)
    g._feed_named(b, "Normal", g.bump((fines, 0), 0.20, 0.0015, normal=bm))
    n = 240
    h = size * 0.5
    # graded sampling: 40 mm cells within 6 m of the post, coarse out to the
    # horizon, so the ground under the lens is real and the far field is cheap
    t = np.linspace(-1.0, 1.0, n)
    xs = np.sign(t) * (np.abs(t) ** 2.1) * h
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    r = np.hypot(X, Y)
    Z = (0.045 * np.sin(X * 0.44) * np.cos(Y * 0.37)
         + 0.014 * np.sin(X * 1.7 + 0.6) * np.cos(Y * 1.4)
         + 0.005 * np.sin(X * 6.1 + 2.2) * np.cos(Y * 5.3))
    Z *= np.clip((r - 2.4) / 5.0, 0.0, 1.0)          # flat where the post is
    Z *= np.clip((h - r) / 3.0, 0.0, 1.0)            # and flat at the rim
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(n * n).reshape(n, n)
    F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                 -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (float(centre[0]), float(centre[1]), float(centre[2]) - 0.012)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def context_skirt(centre, r0=26.0, r1=1400.0, name="CTX_Skirt"):
    """The far field, from the edge of the detailed ground out to the horizon.

    It is a SEPARATE object with a SEPARATE material for one reason, and it is
    the reason the brief gives for TexCoord->Object: a 620 m ground object has
    object coordinates out to +-310 m, and a voronoi at 95 cells/m on that
    range is 29,000 cycles of float32 -- the detail simply dissolves, which is
    what made the first pass's ground a flat brown sheet.  Fine detail lives on
    a 26 m object; the far field carries only metre-scale variation.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NG(mat)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (0.055, 0.055, 0.055)), scale=2.0,
                 detail=7.0, rough=0.62)
    n2 = g.noise(g.vmath('MULTIPLY', obj, (0.28, 0.28, 0.28)), scale=2.0,
                 detail=6.0, rough=0.58)
    col = g.mix(g.math('MULTIPLY', n1, 0.95), (0.028, 0.030, 0.024),
                (0.062, 0.058, 0.044))
    col = g.mix(g.math('MULTIPLY', n2, 0.55), col, (0.044, 0.042, 0.032))
    g._feed(b, 0, col)
    g._feed(b, 2, 0.94)
    nr, na = 90, 168
    rr = r0 * (r1 / r0) ** np.linspace(0.0, 1.0, nr)
    aa = np.linspace(0.0, TAU, na, endpoint=False)
    R, A = np.meshgrid(rr, aa, indexing="ij")
    Z = (0.9 * np.sin(R * np.cos(A) * 0.012) * np.cos(R * np.sin(A) * 0.0095)
         + 0.35 * np.sin(R * np.cos(A) * 0.041 + 1.1))
    Z *= np.clip((R - 30.0) / 45.0, 0.0, 1.0)
    V = np.stack([R * np.cos(A), R * np.sin(A), Z], -1).reshape(-1, 3)
    idx = np.arange(nr * na).reshape(nr, na)
    j1 = (np.arange(na) + 1) % na
    F = np.stack([idx[:-1][:, np.arange(na)], idx[:-1][:, j1],
                  idx[1:][:, j1], idx[1:][:, np.arange(na)]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (float(centre[0]), float(centre[1]), float(centre[2]) - 0.030)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def macro_camera(target, name="CAM_MPC_MACRO", dist=6.0, lens=35.0,
                 bearing_deg=0.0, eye_h=1.62, look_at=None):
    """EXACTLY the manifest's shot: 6.0 m on a 35 mm lens.

    `dist` is measured to `target`, which is the mid-height of the hero
    column -- the dimension the manifest's 1742 onscreen px is measuring.
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
    tgt = np.asarray(target, float)
    br = math.radians(bearing_deg)
    horiz = math.sqrt(max(dist * dist - (eye_h - tgt[2]) ** 2, 0.04))
    pos = np.array([tgt[0] + math.cos(br) * horiz,
                    tgt[1] + math.sin(br) * horiz, eye_h])
    d = (np.asarray(look_at, float) if look_at is not None else tgt) - pos
    ob.location = tuple(float(v) for v in pos)
    from mathutils import Vector
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((float(d[0]), float(d[1]), float(d[2]))
                               ).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True
    cam.dof.focus_distance = float(np.linalg.norm(tgt - pos))
    cam.dof.aperture_fstop = 5.6
    print(">> macro camera %s: %.4f m to the hero column, %.0f mm  "
          "(manifest: 6.0 m / 35 mm)"
          % (name, float(np.linalg.norm(tgt - pos)), lens))
    return ob


def test_scene(out=None, seed=0, n_posts=25, total=120, samples=256,
               res=(1920, 1080), quality=1.0, hero=0):
    """The acceptance scene: 25 marshal post frames at their real stations,
    the contract sun, and one camera at the manifest's own distance and lens."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    plan = post_plan(n_posts, seed)
    # THE HERO POST IS CHOSEN, NOT TAKEN.  The macro render is the only place a
    # human sees this item, so it should be the post that shows the most of it:
    # the widest spread of section kinds and base types among its own legs, a
    # light-panel mast, and a raised deck so the legs are full length.  Picking
    # post 0 by default put four identical galvanised tubes in the frame and
    # said nothing about the other four archetypes.
    fam0 = family_plan(len(plan), total, seed)
    scored = []
    for (u, ncol) in fam0:
        sp = post_frame(u, n_columns=ncol)
        # ...and it has to FIT.  At 6.0 m a 35 mm lens sees 3.47 m of frame
        # height, so a 3.5 m leg has 0 mm of headroom and runs off the top.
        # The manifest already names the height this item is measured at --
        # typical_height_m 2.8, which is 1742 px of a 2160-line master and
        # leaves 19 % of the frame as air.  Score toward that.
        sc_ = (len({(c.kind, c.base) for c in sp.columns}) * 2
               + len({c.base for c in sp.columns})
               + (2 if sp.mast else 0) + (2 if sp.plat > 0.02 else 0)
               + len(sp.columns) * 0.25
               - 12.0 * abs(sp.head_z - 2.80))
        # and, best of all, a post that has BOTH systems on it -- a scaffold
        # leg with couplers next to a welded box leg with gussets and anchor
        # bolts.  That is one frame that shows a human two of the four
        # archetypes and the fact that they coexist on the same post.
        fam_ = {("tube" if c.kind in ("tube", "shoe") else "box")
                for c in sp.columns}
        if len(fam_) > 1:
            sc_ += 6.0
        scored.append((sc_, u))
    scored.sort(reverse=True)
    hero_uid = scored[int(hero) % len(scored)][1]
    hw = plan[0]["world"]
    frames = build(n_posts=n_posts, total=total, seed=seed, stations=plan,
                   res=quality, cam_at=hw, lod=True, hero_uid=hero_uid)
    contract_light(sc)
    g0 = (frames[0].origin[0], frames[0].origin[1], frames[0].origin[2])
    context_ground(g0, 27.0)
    context_skirt(g0, 13.0, 1400.0)
    for pf in frames[:3]:
        context_pad(pf, name="CTX_Pad_%d" % int(pf.spec.uid))
    hf = frames[0]
    # Frame the POST, not one leg: at 6.0 m a 35 mm lens sees 6.17 x 3.47 m,
    # which is the whole frame with air round it.  Stand off the circuit side
    # (post-local -Y) and swing 27 deg so the lens sees the front face AND one
    # side, and so the 12.5 deg sun rakes across the couplers instead of
    # flattening them.  `dist` is then solved so the NEAREST column axis is
    # exactly the manifest's 6.000 m from the lens.
    # THE MANIFEST'S OWN ARITHMETIC, followed exactly:
    #     onscreen_px_4k = height_m * lens * 3840 / (36 * nearest_camera_m)
    #                    = 2.8 * 35 * 3840 / (36 * 6.0) = 1742 px
    # so the hero column is 6.000 m from the lens and fills 81 % of the frame
    # height.  Standing off the post's front-left diagonal puts the other three
    # legs behind it in depth instead of stacked on top of it, and the 12.5 deg
    # sun then rakes ACROSS the couplers rather than down the tube.
    hcol = None
    for role in ("corner_fl", "corner_fr"):
        for col in hf.columns:
            if col.spec.role == role and hcol is None:
                hcol = col
    hcol = hcol or hf.columns[0]
    gz = float(hf.origin[2])
    foot = hcol.mounts["foot"].o
    head = hcol.mounts["head"].o
    tgt = foot + (head - foot) * 0.50
    ctr = np.mean([c.mounts["foot"].o for c in hf.columns], axis=0)
    # aim a little off the hero, toward the rest of the post, so the item sits
    # left of centre and the frame has somewhere to go
    lat = ctr - foot
    lat[2] = 0.0
    look = tgt + unit(lat) * 0.92
    look[2] = tgt[2] - 0.10
    br = math.radians(hf.yaw_deg + 232.0)
    eye = float(tgt[2]) + 0.06

    def _seg_d(pos, a, b):
        ab = b - a
        t = float(np.clip(np.dot(pos - a, ab) / max(float(np.dot(ab, ab)), 1e-9),
                          0.0, 1.0))
        return float(np.linalg.norm(pos - (a + ab * t)))

    def _nearest(dd):
        horiz = math.sqrt(max(dd * dd - (eye - tgt[2]) ** 2, 0.01))
        pos = np.array([tgt[0] + math.cos(br) * horiz,
                        tgt[1] + math.sin(br) * horiz, eye])
        return pos, min(_seg_d(pos, c.mounts["foot"].o, c.mounts["head"].o)
                        for c in hf.columns)

    # `nearest_camera_m` is the closest the lens ever gets to THE ITEM, so it
    # is measured to the nearest column AXIS, not to the one we happen to be
    # aiming at.  Aiming at the hero and calling that 6.0 m put a different leg
    # 5.58 m away -- closer than the manifest allows.  Solve for it instead.
    best = min(((abs(_nearest(dd)[1] - 6.0), dd)
                for dd in np.linspace(4.5, 11.0, 1301)))
    dist_used = float(best[1])
    _pos, dmin = _nearest(dist_used)
    cam = macro_camera(tgt, dist=dist_used, lens=35.0,
                       bearing_deg=math.degrees(br), eye_h=eye, look_at=look)
    print(">> nearest column AXIS %.4f m from the lens (manifest 6.0); aim "
          "point %.3f m; hero column fills %.0f px of a 2160-line master"
          % (dmin, dist_used, hcol.spec.h * 35.0 * 3840.0 / (36.0 * dist_used)))
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
    ncol = sum(len(f.columns) for f in frames)
    tris = sum(c.tris for f in frames for c in f.columns)
    vts = sum(c.verts for f in frames for c in f.columns)
    print(">> %d posts, %d columns, %d triangles, %d verts (%.0f tris/column)"
          % (len(frames), ncol, tris, vts, tris / max(ncol, 1)))
    kinds = {}
    for f in frames:
        for c in f.columns:
            kk = (c.spec.kind, c.spec.base, c.spec.paint)
            kinds[kk] = kinds.get(kk, 0) + 1
    print(">> %d distinct (kind, base, paint) combinations across %d columns"
          % (len(kinds), ncol))
    print(">> hero post uid=%s kind=%s paint=%s W=%.2f D=%.2f plat=%.2f"
          % (hf.spec.uid, hf.spec.kind, hf.spec.paint, hf.spec.W, hf.spec.D,
             hf.spec.plat))
    print(">> hero column: %s / %s / %s  h=%.3f  tris=%d"
          % (hcol.spec.kind, hcol.spec.base, hcol.spec.paint, hcol.spec.h,
             hcol.tris))
    print(">> mounts on the hero post: %s"
          % ", ".join(sorted(k for k, v in hf.mounts.items()
                             if isinstance(v, Frame))))
    if out:
        import fix_audit_blend as FA
        FA.save_clean(out)
    return frames, cam


def _cli():
    argv = sys.argv
    a = argv[argv.index("--") + 1:] if "--" in argv else []

    def opt(name, default=None, cast=str):
        return cast(a[a.index(name) + 1]) if name in a else default

    if "--test" in a:
        out = opt("--out")
        if out and not os.path.isabs(out):
            out = os.path.join(ROOT, out)
        test_scene(out=out, seed=opt("--seed", 0, int),
                   n_posts=opt("--posts", 25, int),
                   total=opt("--total", 120, int),
                   quality=opt("--quality", 1.0, float),
                   hero=opt("--hero", 0, int))
    elif "--one" in a:
        mats = materials()
        col = _coll(ROOT_COLL)
        sp = column_spec(opt("--uid", 3, int), kind=opt("--kind"),
                         base=opt("--base"), paint=opt("--paint"))
        c = build_column(sp, col, mats)
        print(">>", sp, "tris", c.tris, "verts", c.verts)
        contract_light()
        if "--out" in a:
            import fix_audit_blend as FA
            FA.save_clean(opt("--out"))
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli()
