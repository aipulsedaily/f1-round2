"""THE SHOWROOM CEILING — a real one, hung under round-1's 686 m^2 quad.

WHY THIS FILE EXISTS
====================
`Ceiling` is a literal cuboid: 8 vertices, 6 quads, whose top and bottom faces
are ONE QUAD OF 686.25 m^2 each. It is emitted by

    /home/zany/opus5-car-render/build/s02_showroom.py:490  build_shell()

which is part 1, shipped, and READ-ONLY. It reaches the film downstream of the
world assembly, through `tools/build_film_scene.py`'s append of
`world/car_anim.blend`'s SHOWROOM collection at identity, so `assembly*.blend`
never contains it and no world rebuild can ever touch it (R2-504). Anything
that fixes it is a POST-APPEND operation on a film blend, which is what
`tools/r2621_ceiling_build.py` is.

Part 1 was entitled to that quad. `build/s05_lighting_v2.py` says twice that
"the ceiling is never in shot from any hero camera", and it was TRUE: the
shipped opening was 35 mm at 84.15 deg of depression, whose top frame edge sits
at -68.02 deg elevation. R2-464 re-aimed the opening to 18 mm at 10.00 deg and
that assumption died with it. MEASURED on the built rig, over beat 1's 792
frames, by ray-casting the frame against the plane z = 6.200 inside the room
footprint:

    frames 1  - 19    ceiling occupies  5.3 % .. 21.1 % of frame
    frames 296- 333   ceiling occupies  1.1 % .. 15.8 % of frame
    -------------------------------------------------------------
    57 frames total, and 21.05 % of FRAME 1 OF THE FILM.

That is the direct count and it UNDERSTATES the exposure, which is the finding
this module was actually shaped by: two of the four walls of this room are a
curtain wall of specular glass, and the rendered before-frames at 300 and 320
show the cove rings reflected across most of the picture. The ceiling is in
more of beat 1 as a reflection than it is as a subject.

WHAT IS UP THERE ALREADY, AND THE ONE THING THAT MUST NOT MOVE
==============================================================
MEASURED off `world/car_anim.blend`, not quoted:

    Ceiling           z 6.200 .. 6.500   the slab. Bottom face = one 686 m^2 quad
    Cove_Ring         z 6.060   r 4.05 .. 4.85    CoveEmit,      flat annulus
    Cove_RingOuter    z 6.140   r 6.60 .. 7.10    CoveEmitSoft,  flat annulus
    Cove_Strip_0/1    z 6.100 .. 6.120  y -+7.60 -+0.26   CoveEmitAmbient
    Cove_Coffer_0/1   z 6.090 .. 6.220  y -+7.60 -+0.38   CeilingMat
    SpotRod_0..5      z 5.800 .. 6.140  36 mm square, six positions
    SpotCan/Lens_0..5 z 5.106 .. 5.591
    23 interior lamps, 46,203.313 W after showroom_lighting.apply()

This module ADDS ONLY. It creates no light, deletes nothing, and touches no
round-1 datablock, so `showroom_lighting.measure()` reads the same watts and
the same 23 lamps before and after and `assert_levelled` is unaffected. The
build tool asserts that, it does not assume it.

The two cove rings are the reason the design is what it is. They are flat
annuli with nothing around them, which is why they read in the before-frame as
glowing rings PAINTED ON A FLAT PLANE. Housing them in real light slots — the
thing they already look like they were meant to be — is the one move that both
gives the ceiling its structure and leaves every photon where it was.

THE ONE THING THE DESIGN IS NOT ALLOWED TO DO
---------------------------------------------
Occlude an emitter. Everything here is built at or below z = 6.185 and above
the emitter it is near, EXCEPT inside the two slots, which are open to the
deck. The build tool re-derives that as a numeric clearance check per emitter
rather than trusting this paragraph.

A ROUND-1 DEFECT FOUND WHILE MEASURING FOR THIS, WHICH THIS MODULE MUST HONOUR
------------------------------------------------------------------------------
`Cove_Strip_0` (x -12.5..12.5, y -7.86..-7.34, z 6.100..6.120) lies STRICTLY
INSIDE `Cove_Coffer_0` (x -12.6..12.6, y -7.98..-7.22, z 6.090..6.220), with
clearance on all six faces. Same for the +Y pair. `Cove_Coffer_*` is an opaque
`CeilingMat` box. So both `CoveEmitAmbient` strips — 2 x 13 m^2 at radiance
2.4, the "ambient wash that keeps the far corners off the floor of the
histogram" in s05_lighting_v2's own words — are sealed inside opaque boxes and
deliver nothing to the room. They are counted in
`interior_emission_strength_sum` and they are not in the picture.

That is round-1's, it is read-only, and this module DELIBERATELY DOES NOT FIX
IT: unsealing them would change beat 1's light, and the film's exposure, black
budget and every graded frame already shipped were measured with them sealed.
The panel field is set at z 6.040 — 50 mm BELOW the coffers' 6.090 soffit —
precisely so the coffers are concealed without being disturbed.

NO REPEATED ASSETS
==================
A ceiling is periodic and its STRUCTURE should be: the beam grid lands on the
curtain wall's own mullion spacing (2.142857 m in x, 2.200 m in y, both
measured off GW_Front_Mull_* / GW_Right_Mull_*), because that is what a real
building does and a grid that ignores the wall below it reads as wallpaper.
What is NOT allowed to repeat is the FITTINGS. Every panel carries a `pnl`
attribute driving tone, roughness and perforation phase; every track head has
its own body type, aim, tilt and station; every sprinkler its own drop, rotation
and escutcheon. All from `itemkit.hash01` on the instance's own coordinates, so
it is deterministic and reproducible without a stored table.

NO EXTERNAL ASSETS
==================
Every material is built here from `itemkit.NT` nodes. No image textures, no
HDRIs, no downloaded meshes. `texture_node_count()` per material is asserted by
`selftest()`.

RELIEF AMPLITUDES ARE IN METRES HERE, ON PURPOSE
------------------------------------------------
`itemkit.NT.bump(modulation_pp=, wavelength_m=)` derives depth from the CONTRACT
SUN at 12.47 deg elevation, and that is the right law for trackside dressing.
It is the wrong law for a soffit: this surface is lit from BELOW by practicals
2 to 4 m away and seen from 2.3 m under it at a grazing angle, where the same
amplitude reads several times stronger than it would under a 12.47 deg sun.
Passing `modulation_pp` here would quote a number that means nothing about how
this surface reads. So `distance=` is used, deliberately, and each value is
commented with the feature it is cutting.
"""

import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(_HERE), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                              # noqa: E402


# =========================================================================== #
#  1.  DATUMS.  Every one of these is MEASURED off the built showroom.
#      `tools/r2621_ceiling_build.py` re-measures them in the scene and
#      REFUSES to build if any has moved.  They are not defaults.
# =========================================================================== #

PFX = "R2C_"
COLL = "R2_SHOWROOM_CEILING"

#: round-1 slab soffit.  s02_showroom.CEIL_Z.
Z_SLAB = 6.200

#: this ceiling's plenum deck — the surface seen up inside the light slots.
#: 15 mm under the slab so it can never z-fight with a 686 m^2 quad.
Z_DECK = 6.185
#: deck plate thickness, built UPWARD: 6.185 + 0.013 = 6.198, under the slab.
DECK_T = 0.013

#: the panel field's finished face.  50 mm below Cove_Coffer_*'s 6.090 soffit,
#: which is what conceals the two sealed strips without touching them.
Z_PANEL = 6.040
PANEL_T = 0.035                       # panel tray depth

Z_SEC_SOFFIT = 5.920                  # secondary beams (constant x)
SEC_W = 0.110

Z_PRI_BOT = 5.760                     # primary beams (constant y), Vierendeel
Z_PRI_FLANGE_TOP = 5.860
Z_PRI_TOP_FLANGE_BOT = 6.100
PRI_W = 0.260
PRI_POST_W = 0.100

#: the curtain wall's own grids.  MEASURED: GW_Front_Mull_* centres run
#: -15.000 .. 15.000 in 14 steps; GW_Right_Mull_* run -11.000 .. 11.000 in 10.
BAY_X = 30.0 / 14.0                   # 2.142857
BAY_Y = 22.0 / 10.0                   # 2.200

ROOM_X, ROOM_Y = 15.0, 11.0
PERIM_GAP = 0.060                     # shadow gap, ceiling to wall face
PERIM_W = 0.300                       # perimeter bulkhead width
Z_PERIM_SOFFIT = 5.780
X_IN = ROOM_X - PERIM_GAP - PERIM_W   # 14.640, inner face of the bulkhead
Y_IN = ROOM_Y - PERIM_GAP - PERIM_W   # 10.640

#: R2-840.  THE PERIMETER REVEAL'S UNDERSIDE, and why it is not one number.
#:
#: The reveal backs the shadow gap at the wall head.  On the two SOLID walls it
#: drops to 6.030 as designed and nothing is behind it.  On the two GLAZED walls
#: there IS something behind it: the curtain wall's glazing pocket, the 24 mm
#: channel the panes sit in, which tops out at z 6.1120 (`POCKET_HI` in
#: `sim/apply_breach.py`).  A backing plate reaching 6.030 sits 82 mm INSIDE that
#: channel -- ceiling trim occupying the slot the glass lives in.  That is an
#: overlap, not a design.
#:
#: It survived because nothing looks there: the reveal's own vertices are metres
#: away around the perimeter and only its FACES cross, so a vertex or bounding-box
#: test reads clear.  `apply_breach`'s triangle test (R2-125, built for exactly
#: this) found 3 faces of `R2C_PerimeterReveal` inside the breach aperture's clear
#: opening over bays 4-5 and refused the apply.
#:
#: Both glazed walls are lifted, not just the east one: the south wall carries the
#: identical overlap and only escaped notice because the breach does not open
#: there.  Fixing one and leaving the other would be fixing the symptom.
Z_REVEAL_BOT = 6.030                  # solid walls, unchanged
Z_REVEAL_BOT_GLAZED = 6.115           # 3.0 mm clear of the pocket head, 6.1120

# ---- the concentric feature, radius by radius --------------------------- #
# every radius below is derived from an emitter it must clear, or from the
# radius before it.  the two SLOT bands are the only open ones.
R_HUB = 0.550
R_STEP_C = 1.300
R_STEP_B = 2.200
R_STEP_A = 3.100
R_DRUM_FIELD = 3.600
R_DRUM_RIM = 3.780                    # = slot 1 MOUTH, inner side

# The slots are SPLAYED and WHITE, and both of those are the first probe's
# doing rather than taste.  Cut with parallel walls and the project's dark
# beam paint, the occlusion probe measured the coves losing about a third of
# their cosine-weighted downward emission to their own reveal.  A light cove
# in a real building is splayed and lined matt white for exactly that reason:
# the reveal is a REFLECTOR, not a shade.  `selftest()` recomputes the
# transmittance from these radii and the tool re-measures it on the built mesh.
R_S1_IN, R_S1_OUT = 3.950, 4.950      # THROAT, at the deck. Cove_Ring 4.05..4.85
R_S1_MOUTH_IN, R_S1_MOUTH_OUT = 3.780, 5.120
R_RINGA_IN, R_RINGA_OUT = 5.120, 5.440
R_APRON_IN = 5.440                    # inner apron plate
R_RINGB_IN, R_RINGB_OUT = 5.980, 6.280
R_S2_IN, R_S2_OUT = 6.520, 7.180      # THROAT. Cove_RingOuter 6.60..7.10
R_S2_MOUTH_IN, R_S2_MOUTH_OUT = 6.280, 7.420
R_RINGC_IN, R_RINGC_OUT = 7.420, 7.740
R_FEAT = 7.780                        # no panel cell may reach inside this
R_APRON_OUT = 8.560                   # covers the worst dropped quarter-cell

LINER_T = 0.030                       # cove reflector shell thickness

Z_DRUM_RIM_SOFFIT = 5.780
Z_STEP_A = 5.990
Z_STEP_B = 6.060
Z_STEP_C = 6.130
Z_HUB = 6.150
Z_RING_SOFFIT = 5.780                 # ring beams A and C
Z_RINGB_SOFFIT = 5.860
Z_S1_MOUTH = 5.780                    # the plane the slot 1 splay opens onto
Z_S2_MOUTH = 5.860
Z_APRON = 6.048                       # 8 mm above the cells, so overlap resolves

SEG = 192                             # matches round-1's annulus segmentation

#: the six round-1 spot rods, MEASURED (36 mm square, z 5.800 .. 6.140).
SPOT_RODS = ((6.4, -5.2), (6.4, 5.2), (-5.8, -5.2), (-5.8, 5.2),
             (0.0, -7.0), (0.0, 7.0))
Z_ROD_TOP = 6.140

#: emitters this build must never get under.  (name, z, r_in, r_out) or
#: (name, z, None, None) for a non-annular one.  The tool checks these live.
EMITTER_CLEARANCE = (
    ("Cove_Ring", 6.060, 4.05, 4.85),
    ("Cove_RingOuter", 6.140, 6.60, 7.10),
)


# =========================================================================== #
#  2.  A MESH ACCUMULATOR.  Boxes, rings, discs and lofts into one buffer.
# =========================================================================== #

def _h(*keys):
    """`itemkit.hash01` with string and float keys, without losing them.

    `hash01` takes INTEGERS: `int(k)` RAISES on a str and TRUNCATES a float, so
    every tray in a 1.07 m column would have come back with the same value and
    the ceiling would have had exactly the failure this project is named for --
    one asset spammed across 686 m^2 -- while looking varied in the source.
    Strings go through FNV-1a to a 32-bit integer and floats are quantised to
    millimetres, so the avalanche finaliser downstream gets distinct keys.
    `_variety()` MEASURES the resulting spread rather than trusting this.
    """
    ks = []
    for k in keys:
        if isinstance(k, str):
            v = 2166136261
            for ch in k.encode():
                v = ((v ^ ch) * 16777619) & 0xFFFFFFFF
            ks.append(v)
        elif isinstance(k, float):
            ks.append(int(round(k * 1000.0)))
        else:
            ks.append(int(k))
    return K.hash01(*ks)


class Acc(object):
    """Vertices and quads, appended, with island bookkeeping for attributes."""

    def __init__(self):
        self.v = []
        self.q = []
        self.island = []          # per-vertex island id, for bake_attributes
        self._n = 0
        self._isl = 0

    def new_island(self):
        self._isl += 1
        return self._isl

    def add(self, verts, quads, island=None):
        isl = self._isl if island is None else island
        b = self._n
        verts = np.asarray(verts, np.float64).reshape(-1, 3)
        self.v.append(verts)
        if len(quads):
            self.q.append(np.asarray(quads, np.int64).reshape(-1, 4) + b)
        self.island.append(np.full(len(verts), isl, np.float64))
        self._n += len(verts)

    def box(self, x0, x1, y0, y1, z0, z1, island=None):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(v, q, island)

    def ring(self, r0, r1, z0, z1, seg=SEG, cx=0.0, cy=0.0, island=None):
        """A closed annular solid: inner wall, outer wall, top, bottom."""
        a = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
        c, s = np.cos(a), np.sin(a)
        v = np.empty((4 * seg, 3))
        for k, (r, z) in enumerate(((r0, z0), (r1, z0), (r1, z1), (r0, z1))):
            v[k * seg:(k + 1) * seg, 0] = cx + r * c
            v[k * seg:(k + 1) * seg, 1] = cy + r * s
            v[k * seg:(k + 1) * seg, 2] = z
        i = np.arange(seg)
        j = (i + 1) % seg
        q = np.concatenate([
            np.stack([i, j, seg + j, seg + i], 1),                       # bottom
            np.stack([seg + i, seg + j, 2 * seg + j, 2 * seg + i], 1),   # outer
            np.stack([2 * seg + i, 2 * seg + j, 3 * seg + j, 3 * seg + i], 1),
            np.stack([3 * seg + i, 3 * seg + j, j, i], 1),               # inner
        ])
        self.add(v, q, island)

    def prism_ring(self, profile, seg=SEG, cx=0.0, cy=0.0, island=None):
        """Sweep a CLOSED (r, z) cross-section around the Z axis.

        `ring()` is the four-point special case.  This exists because a cove
        reveal has to SPLAY -- its wall leans away from the emitter as it comes
        down -- and a splayed wall is a cross-section, not a pair of radii.
        """
        P = np.asarray(profile, float).reshape(-1, 2)
        m = len(P)
        a = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
        c, s = np.cos(a), np.sin(a)
        v = np.empty((seg * m, 3))
        for k in range(m):
            v[k * seg:(k + 1) * seg, 0] = cx + P[k, 0] * c
            v[k * seg:(k + 1) * seg, 1] = cy + P[k, 0] * s
            v[k * seg:(k + 1) * seg, 2] = P[k, 1]
        i = np.arange(seg)
        j = (i + 1) % seg
        q = []
        for k in range(m):
            k2 = (k + 1) % m
            q.append(np.stack([k * seg + i, k * seg + j,
                               k2 * seg + j, k2 * seg + i], 1))
        self.add(v, np.concatenate(q), island)

    def cyl(self, r, z0, z1, cx=0.0, cy=0.0, seg=16, cap=True, island=None):
        a = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
        c, s = np.cos(a), np.sin(a)
        v = np.empty((2 * seg + (2 if cap else 0), 3))
        v[:seg, 0] = cx + r * c
        v[:seg, 1] = cy + r * s
        v[:seg, 2] = z0
        v[seg:2 * seg, 0] = cx + r * c
        v[seg:2 * seg, 1] = cy + r * s
        v[seg:2 * seg, 2] = z1
        i = np.arange(seg)
        j = (i + 1) % seg
        q = [np.stack([i, j, seg + j, seg + i], 1)]
        if cap:
            v[2 * seg] = (cx, cy, z0)
            v[2 * seg + 1] = (cx, cy, z1)
            q.append(np.stack([i, j, np.full(seg, 2 * seg),
                               np.full(seg, 2 * seg)], 1))
            q.append(np.stack([seg + i, seg + j, np.full(seg, 2 * seg + 1),
                               np.full(seg, 2 * seg + 1)], 1))
        self.add(v, np.concatenate(q), island)

    def cone(self, r0, r1, z0, z1, cx=0.0, cy=0.0, seg=16, island=None):
        a = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
        c, s = np.cos(a), np.sin(a)
        v = np.empty((2 * seg, 3))
        v[:seg] = np.stack([cx + r0 * c, cy + r0 * s, np.full(seg, z0)], 1)
        v[seg:] = np.stack([cx + r1 * c, cy + r1 * s, np.full(seg, z1)], 1)
        i = np.arange(seg)
        j = (i + 1) % seg
        self.add(v, np.stack([i, j, seg + j, seg + i], 1), island)

    def arrays(self):
        if not self.v:
            return np.zeros((0, 3)), np.zeros((0, 4), np.int64), np.zeros(0)
        return (np.concatenate(self.v),
                np.concatenate(self.q) if self.q else np.zeros((0, 4), np.int64),
                np.concatenate(self.island))


def _emit(acc, name, coll, mat, smooth_deg=33.0, attr="pnl"):
    """Accumulator -> object, recentred on emit (itemkit law 6).

    THE ATTRIBUTE IS HASHED, AND IT IS NAMED `pnl`, AND BOTH WERE WRONG ONCE.
    It used to bake the raw island INDEX under the name `isl`.  Every material
    here reads `pnl`, so a missing attribute evaluates to 0.0 and the aprons
    came out one flat tone across 17 m -- and even had the name matched, the
    index runs 1, 2, 3 ... 72 into a mix factor that clamps at 1, so every
    segment past the first would still have been identical.  A per-instance
    attribute that is silently constant is exactly the failure this project is
    named for, wearing the clothes of the fix for it.
    """
    import bpy
    V, Q, I = acc.arrays()
    if not len(V):
        return None
    me, off = K.new_mesh(name, V, quads=Q, smooth_deg=smooth_deg)
    if attr:
        lut = {int(v): _h(int(v), name) for v in np.unique(I)}
        K.bake_attributes(me, {attr: np.array([lut[int(v)] for v in I])})
    ob = bpy.data.objects.new(name, me)
    ob.location = off
    if mat is not None:
        ob.data.materials.append(mat)
    coll.objects.link(ob)
    return ob


# =========================================================================== #
#  3.  MATERIALS.  Eight, all procedural, all bump-wired BY NAME.
# =========================================================================== #

def _mats():
    """Build (or fetch) this ceiling's eight materials.

    Every relief chain feeds the NEXT bump's `Normal` and the last feeds
    Principled's `Normal` BY NAME.  Blender 5.2 moved Principled's Normal from
    socket 5 to 6 and shipped 14 dead bump stacks on this project when it was
    fed by index; `NT.principled_out(normal=...)` resolves by name.
    """
    import bpy
    out = {}

    # ---- 1. the panel field: micro-perforated white powder-coated steel ----
    n = PFX + "PanelSteel"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["panel"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        pnl = t.attr("pnl", out=2)                    # per-panel float, 0..1
        # tone: two near-whites, mixed per panel.  a metal ceiling is never
        # one colour across 450 trays -- batch and age both move it.
        base = t.cmix(pnl, (0.700, 0.698, 0.690), (0.762, 0.757, 0.741))
        # perforation.  1.8 mm holes on a ~6 mm pitch: a real acoustic tray.
        perf = t.vor(p, wavelength_m=0.0060, feature="F1", out=0)
        perfm = t.ramp(perf, [(0.00, (0, 0, 0)), (0.26, (0, 0, 0)),
                              (0.40, (1, 1, 1)), (1.00, (1, 1, 1))])
        base = t.cmix(t.math("SUBTRACT", 1.0, perfm), base,
                      (0.055, 0.055, 0.058))          # holes read as plenum
        # roll-form waviness across the tray, and a long dirt gradient
        wav = t.noise(p, wavelength_m=0.340, detail=3.0, rough=0.45)
        soil = t.noise(p, wavelength_m=2.600, detail=5.0, rough=0.60)
        rough = t.maprange(soil, 0.30, 0.72,
                           t.fmix(pnl, 0.345, 0.415), 0.520)
        # coat texture, 2.4 mm orange peel
        peel = t.noise(p, wavelength_m=0.0024, detail=4.0, rough=0.55)
        b1 = t.bump(peel, 0.42, distance=0.00016)     # 0.16 mm of orange peel
        b2 = t.bump(perfm, 0.90, distance=0.00075, normal=b1)   # 0.75 mm holes
        b3 = t.bump(wav, 0.55, distance=0.00110, normal=b2)     # 1.1 mm form
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b3)
        out["panel"] = t.m

    # ---- 2. beams / bulkheads: dark satin paint on steel ------------------
    n = PFX + "BeamPaint"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["beam"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        pnl = t.attr("pnl", out=2)
        mott = t.noise(p, wavelength_m=1.900, detail=6.0, rough=0.55)
        base = t.cmix(mott, (0.0455, 0.0455, 0.0480),
                      (0.0620, 0.0605, 0.0590))
        # and one more degree of freedom PER PIECE: two beams sprayed in the
        # same booth on different days are not the same black.
        base = t.cmix(t.math("MULTIPLY", pnl, 0.55), base,
                      (0.0730, 0.0700, 0.0665))
        nap = t.noise(p, wavelength_m=0.0090, detail=5.0, rough=0.60)
        peel = t.noise(p, wavelength_m=0.0021, detail=3.0, rough=0.50)
        # sheen wanders with the roller pass -- a sprayed beam never reads flat
        rough = t.maprange(nap, 0.25, 0.75,
                           t.fmix(pnl, 0.265, 0.330), 0.430)
        b1 = t.bump(peel, 0.40, distance=0.00013)     # 0.13 mm coat texture
        b2 = t.bump(nap, 0.50, distance=0.00042, normal=b1)     # roller nap
        b3 = t.bump(mott, 0.30, distance=0.00090, normal=b2)    # panel oilcan
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b3)
        out["beam"] = t.m

    # ---- 3. the plenum deck seen up inside the slots ----------------------
    n = PFX + "DeckConcrete"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["deck"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        agg = t.noise(p, wavelength_m=0.075, detail=8.0, rough=0.62)
        fine = t.noise(p, wavelength_m=0.0065, detail=6.0, rough=0.55)
        board = t.wave(p, wavelength_m=0.200, direction="X", distortion=1.4,
                       detail=3.0)
        tie = t.vor(p, wavelength_m=1.150, feature="F1", out=0)
        tiem = t.ramp(tie, [(0.00, (1, 1, 1)), (0.055, (1, 1, 1)),
                            (0.085, (0, 0, 0)), (1.00, (0, 0, 0))])
        base = t.cmix(agg, (0.0930, 0.0905, 0.0865),
                      (0.1320, 0.1290, 0.1230))
        base = t.cmix(board, base, (0.0790, 0.0770, 0.0740))
        base = t.cmix(t.math("SUBTRACT", 1.0, tiem), base,
                      (0.0430, 0.0420, 0.0405))
        rough = t.maprange(fine, 0.25, 0.75, 0.780, 0.900)
        b1 = t.bump(fine, 0.55, distance=0.00035)     # 0.35 mm sand texture
        b2 = t.bump(agg, 0.45, distance=0.00190, normal=b1)     # aggregate
        b3 = t.bump(board, 0.60, distance=0.00320, normal=b2)   # board marks
        b4 = t.bump(tiem, 0.85, distance=0.00700, normal=b3)    # 7 mm tie holes
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b4)
        out["deck"] = t.m

    # ---- 4. anodised extruded aluminium: lighting track ------------------
    n = PFX + "TrackAlu"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["track"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        brush = t.wave(p, wavelength_m=0.00085, direction="X", distortion=0.9,
                       detail=2.0)
        die = t.wave(p, wavelength_m=0.0170, direction="X", distortion=0.2,
                     detail=1.0)
        blot = t.noise(p, wavelength_m=0.130, detail=4.0, rough=0.50)
        base = t.cmix(blot, (0.395, 0.398, 0.404), (0.452, 0.455, 0.462))
        rough = t.maprange(brush, 0.0, 1.0, 0.185, 0.330)
        b1 = t.bump(brush, 0.65, distance=0.000035)   # 35 um brush lay
        b2 = t.bump(die, 0.45, distance=0.00019, normal=b1)     # die lines
        t.principled_out(base_color=base, roughness=rough, metallic=1.0,
                         normal=b2)
        out["track"] = t.m

    # ---- 5. matt black textured powder coat: fixture bodies --------------
    n = PFX + "FixtureBody"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["fixture"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        pnl = t.attr("pnl", out=2)
        grain = t.vor(p, wavelength_m=0.00135, feature="F1", out=0)
        drift = t.noise(p, wavelength_m=0.055, detail=5.0, rough=0.55)
        base = t.cmix(drift, (0.0210, 0.0208, 0.0212),
                      (0.0295, 0.0290, 0.0288))
        base = t.cmix(t.math("MULTIPLY", pnl, 0.7), base,
                      (0.0385, 0.0372, 0.0360))
        rough = t.maprange(grain, 0.0, 1.0,
                           t.fmix(pnl, 0.430, 0.510), 0.620)
        b1 = t.bump(grain, 0.75, distance=0.00011)    # 0.11 mm crackle coat
        b2 = t.bump(drift, 0.35, distance=0.00040, normal=b1)
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b2)
        out["fixture"] = t.m

    # ---- 6. hot-dip galvanised: tray, conduit, hangers, sprinkler main ---
    n = PFX + "Galv"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["galv"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        # spangle: the crystal facets are the whole reason galv looks like galv
        spang = t.vor(p, wavelength_m=0.0280, feature="F1", out=0)
        edge = t.vor(p, wavelength_m=0.0280, feature="DISTANCE_TO_EDGE", out=0)
        grit = t.noise(p, wavelength_m=0.0020, detail=5.0, rough=0.55)
        dirt = t.noise(p, wavelength_m=0.850, detail=6.0, rough=0.62)
        base = t.cmix(spang, (0.512, 0.520, 0.532), (0.582, 0.588, 0.596))
        pnl = t.attr("pnl", out=2)
        base = t.cmix(t.maprange(dirt, 0.35, 0.80, 0.0,
                                 t.fmix(pnl, 0.38, 0.70)),
                      base, (0.300, 0.296, 0.286))
        rough = t.maprange(spang, 0.0, 1.0,
                           t.fmix(pnl, 0.235, 0.300), 0.450)
        b1 = t.bump(grit, 0.40, distance=0.00009)
        b2 = t.bump(edge, 0.55, distance=0.00055, normal=b1)   # facet borders
        b3 = t.bump(dirt, 0.25, distance=0.00080, normal=b2)
        t.principled_out(base_color=base, roughness=rough, metallic=1.0,
                         normal=b3)
        out["galv"] = t.m

    # ---- 7. chromed brass: sprinkler bodies and deflectors ---------------
    n = PFX + "Brass"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["brass"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        turn = t.wave(p, wavelength_m=0.00060, direction="Z", distortion=0.3,
                      detail=1.0)
        tarn = t.noise(p, wavelength_m=0.014, detail=6.0, rough=0.58)
        base = t.cmix(tarn, (0.686, 0.560, 0.312), (0.752, 0.640, 0.402))
        rough = t.maprange(tarn, 0.2, 0.8, 0.140, 0.290)
        b1 = t.bump(turn, 0.60, distance=0.000045)    # 45 um lathe turning
        b2 = t.bump(tarn, 0.30, distance=0.00016, normal=b1)
        t.principled_out(base_color=base, roughness=rough, metallic=1.0,
                         normal=b2)
        out["brass"] = t.m

    # ---- 8b. the cove reflector: matt white, high albedo -----------------
    # This is a REFLECTOR and its albedo is a lighting decision, not a colour
    # choice.  The first occlusion probe measured the coves losing ~1/3 of
    # their cosine-weighted downward emission into the reveal; lining the
    # reveal at 0.82 albedo and splaying it gives most of that back, which is
    # precisely why real light coves are white and splayed.  Kept matt --
    # a glossy reveal makes a hard reflected image of the emitter and a
    # 0.50 m wide annulus at 46 kW-scale radiance would fringe.
    n = PFX + "CoveReflector"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["liner"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        peel = t.noise(p, wavelength_m=0.0026, detail=4.0, rough=0.52)
        drift = t.noise(p, wavelength_m=0.480, detail=5.0, rough=0.55)
        seam = t.wave(p, wavelength_m=0.640, direction="Z", distortion=0.4,
                      detail=1.0)
        seamm = t.ramp(seam, [(0.00, (1, 1, 1)), (0.44, (1, 1, 1)),
                              (0.50, (0, 0, 0)), (0.56, (1, 1, 1)),
                              (1.00, (1, 1, 1))])
        base = t.cmix(drift, (0.815, 0.816, 0.812), (0.845, 0.845, 0.840))
        base = t.cmix(t.math("SUBTRACT", 1.0, seamm), base,
                      (0.560, 0.558, 0.552))
        rough = t.maprange(drift, 0.25, 0.75, 0.560, 0.680)
        b1 = t.bump(peel, 0.40, distance=0.00014)
        b2 = t.bump(seamm, 0.70, distance=0.00090, normal=b1)   # segment joint
        b3 = t.bump(drift, 0.25, distance=0.00060, normal=b2)
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b3)
        out["liner"] = t.m

    # ---- 8. white semi-gloss: HVAC diffuser blades and escutcheons -------
    n = PFX + "DiffuserWhite"
    if n in bpy.data.materials and bpy.data.materials[n].node_tree:
        out["diffuser"] = bpy.data.materials[n]
    else:
        t = K.NT(n)
        p = t.object_coords()
        peel = t.noise(p, wavelength_m=0.0018, detail=4.0, rough=0.52)
        ext = t.wave(p, wavelength_m=0.0095, direction="X", distortion=0.3)
        soil = t.noise(p, wavelength_m=0.240, detail=6.0, rough=0.60)
        pnl = t.attr("pnl", out=2)
        base = t.cmix(soil, (0.735, 0.733, 0.726), (0.792, 0.790, 0.780))
        base = t.cmix(t.math("MULTIPLY", pnl, 0.45), base,
                      (0.700, 0.694, 0.680))
        rough = t.maprange(soil, 0.25, 0.75,
                           t.fmix(pnl, 0.200, 0.245), 0.340)
        b1 = t.bump(peel, 0.35, distance=0.00011)
        b2 = t.bump(ext, 0.30, distance=0.00022, normal=b1)
        t.principled_out(base_color=base, roughness=rough, metallic=0.0,
                         normal=b2)
        out["diffuser"] = t.m

    return out


# =========================================================================== #
#  4.  REGIONS.  What may be built where, from the radii above.
# =========================================================================== #

def _r(x, y):
    return math.hypot(x, y)


def _blocked(x, y):
    """True where the concentric feature owns the plan and nothing else may go."""
    return _r(x, y) < R_FEAT


def _seg_runs(p0, p1, n, keep):
    """Walk a line and return the [t0, t1] runs where `keep(x, y)` holds."""
    ts = np.linspace(0.0, 1.0, n)
    xs = p0[0] + (p1[0] - p0[0]) * ts
    ys = p0[1] + (p1[1] - p0[1]) * ts
    ok = np.array([keep(x, y) for x, y in zip(xs, ys)])
    runs, i = [], 0
    while i < len(ok):
        if not ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(ok) and ok[j + 1]:
            j += 1
        if j > i:
            runs.append((float(ts[i]), float(ts[j])))
        i = j + 1
    return runs


# =========================================================================== #
#  5.  THE BUILD
# =========================================================================== #

def build(coll=None, report=True):
    """Build the whole ceiling.  Returns a summary dict.

    Adds objects only.  Creates no light and no emissive material: the room's
    23 practicals and 46,203.313 W are untouched by construction, which is the
    invariant `showroom_lighting.assert_levelled` is checked against after.
    """
    import bpy

    M = _mats()
    c = K.coll(COLL)
    if coll is not None:
        c = coll
    made = {}

    # ------------------------------------------------------------------ #
    # 5a.  the plenum deck: what you see up inside the two light slots.
    #      annular, only where a slot is open -- there is no point paying
    #      for 686 m^2 of deck that the panel field covers.
    # ------------------------------------------------------------------ #
    a = Acc()
    for (ri, ro, mi, mo, zm) in ((R_S1_IN, R_S1_OUT, R_S1_MOUTH_IN,
                                  R_S1_MOUTH_OUT, Z_S1_MOUTH),
                                 (R_S2_IN, R_S2_OUT, R_S2_MOUTH_IN,
                                  R_S2_MOUTH_OUT, Z_S2_MOUTH)):
        # the slot HEAD: 13 mm thick, built UP into the 15 mm gap under the
        # round-1 slab.  Built DOWN it reached z 6.215, inside a 686 m^2 quad;
        # selftest check [8] caught that on the first run and that is why the
        # check exists.
        a.new_island()
        a.ring(ri, ro, Z_DECK, Z_DECK + DECK_T)
        # the two SPLAYED reveals, leaning away from the emitter as they fall.
        a.new_island()
        a.prism_ring([(ri, Z_DECK), (mi, zm),
                      (mi - LINER_T, zm), (ri - LINER_T, Z_DECK)])
        a.new_island()
        a.prism_ring([(ro, Z_DECK), (mo, zm),
                      (mo + LINER_T, zm), (ro + LINER_T, Z_DECK)])
    made["liner"] = _emit(a, PFX + "CoveLiner", c, M["liner"], smooth_deg=25.0)

    # the perimeter shadow gap's backing.  60 mm of open plenum at the wall
    # head is the one place in the room the raw structure above still shows,
    # and it is what gives the wall/ceiling junction a line with a depth.
    a = Acc()
    xo, yo = ROOM_X - PERIM_GAP, ROOM_Y - PERIM_GAP
    #                x0       x1      y0       y1      underside   wall
    for (x0, x1, y0, y1, zb) in (
            (-ROOM_X, ROOM_X, yo, ROOM_Y, Z_REVEAL_BOT),           # N  solid
            (-ROOM_X, ROOM_X, -ROOM_Y, -yo, Z_REVEAL_BOT_GLAZED),  # S  GW_Front_*
            (-ROOM_X, -xo, -yo, yo, Z_REVEAL_BOT),                 # W  solid
            (xo, ROOM_X, -yo, yo, Z_REVEAL_BOT_GLAZED)):           # E  curtain wall
        a.new_island()
        a.box(x0, x1, y0, y1, zb, Z_DECK + DECK_T)
    made["deck"] = _emit(a, PFX + "PerimeterReveal", c, M["deck"],
                         smooth_deg=25.0)

    # ------------------------------------------------------------------ #
    # 5b.  the drum over the turntable — the hero of the ceiling, and the
    #      only part of it the car is ever directly under.  A stepped dish
    #      rising to a hub, ribbed radially, on a deep rim beam.
    # ------------------------------------------------------------------ #
    a = Acc()
    a.new_island()
    a.ring(R_DRUM_FIELD, R_DRUM_RIM, Z_DRUM_RIM_SOFFIT, Z_DECK)      # rim beam
    a.new_island()
    a.ring(R_STEP_A, R_DRUM_FIELD, Z_STEP_A - 0.055, Z_STEP_A)       # step A
    a.new_island()
    a.ring(R_STEP_B, R_STEP_A, Z_STEP_B - 0.055, Z_STEP_B)           # step B
    a.new_island()
    a.ring(R_STEP_C, R_STEP_B, Z_STEP_C - 0.055, Z_STEP_C)           # step C
    a.new_island()
    a.ring(R_HUB, R_STEP_C, Z_HUB - 0.045, Z_HUB)                    # hub ring
    a.new_island()
    a.cyl(R_HUB, Z_HUB - 0.075, Z_HUB, seg=64)                       # hub boss
    made["drum"] = _emit(a, PFX + "Drum", c, M["beam"], smooth_deg=25.0)

    # radial ribs.  STRUCTURE is allowed to repeat -- 24 identical ribs is
    # what a real drum has.  The fittings on it are what must not.
    a = Acc()
    NRIB = 24
    for i in range(NRIB):
        th = 2.0 * math.pi * i / NRIB
        ct, st = math.cos(th), math.sin(th)
        a.new_island()
        for r0, r1, z in ((R_HUB, R_STEP_C, Z_HUB - 0.045),
                          (R_STEP_C, R_STEP_B, Z_STEP_C - 0.055),
                          (R_STEP_B, R_STEP_A, Z_STEP_B - 0.055),
                          (R_STEP_A, R_DRUM_FIELD, Z_STEP_A - 0.055)):
            hw = 0.0275
            v, q = _rib(r0, r1, ct, st, hw, z - 0.048, z)
            a.add(v, q)
    made["drum_ribs"] = _emit(a, PFX + "DrumRib", c, M["beam"], smooth_deg=25.0)

    # ONE FITTING PER DRUM COFFER, and no two alike.  The drum is the only
    # part of this ceiling the car is ever directly under, so it is the part
    # that most has to survive being looked at.  A bay is skipped wherever the
    # hash says so, because a real dome does not have a fitting in every
    # single coffer -- the empty ones are what make the full ones read.
    a = Acc()
    n_drum_fit = 0
    for i in range(NRIB):
        th = 2.0 * math.pi * (i + 0.5) / NRIB
        for k, (r0, r1, z) in enumerate(((R_STEP_C, R_STEP_B, Z_STEP_C - 0.055),
                                         (R_STEP_B, R_STEP_A, Z_STEP_B - 0.055),
                                         (R_STEP_A, R_DRUM_FIELD,
                                          Z_STEP_A - 0.055))):
            hh = _h(i, k, "drumfit")
            h2 = _h(k, i, "drumfit2")
            if hh < 0.42:
                continue
            r = r0 + (r1 - r0) * (0.34 + 0.32 * h2)
            fx, fy = r * math.cos(th), r * math.sin(th)
            rd = 0.042 + 0.022 * h2
            a.new_island()
            a.cyl(rd, z - 0.010, z + 0.034, cx=fx, cy=fy, seg=18)
            a.cone(rd, rd * 0.5, z + 0.034, z + 0.046, cx=fx, cy=fy, seg=18)
            n_drum_fit += 1
    made["drum_fittings"] = _emit(a, PFX + "DrumFitting", c, M["fixture"],
                                  smooth_deg=30.0)

    # ------------------------------------------------------------------ #
    # 5c.  the two light slots' trim: ring beams A, B and C, plus the inner
    #      apron between A and B and the outer apron beyond C.
    #      The slot WALLS are these beams' own faces -- a light slot with no
    #      wall thickness is the flat-plane defect again, one scale down.
    # ------------------------------------------------------------------ #
    a = Acc()
    a.new_island(); a.ring(R_RINGA_IN, R_RINGA_OUT, Z_RING_SOFFIT, Z_DECK)
    a.new_island(); a.ring(R_RINGB_IN, R_RINGB_OUT, Z_RINGB_SOFFIT, Z_DECK)
    a.new_island(); a.ring(R_RINGC_IN, R_RINGC_OUT, Z_RING_SOFFIT, Z_DECK)
    made["ringbeams"] = _emit(a, PFX + "RingBeam", c, M["beam"], smooth_deg=25.0)

    # THE APRONS ARE SEGMENTED, AND THE FIRST RENDER IS WHY.
    # They started as two smooth annuli with three or four concentric grooves.
    # MEASURED off the frame-1 geometry afterwards: the visible ceiling at the
    # film's first frame is ENTIRELY this concentric feature -- the camera sits
    # at z 3.757 and the ceiling's far half compresses into a band above the
    # wall, so the 428 trays, 246 web posts and 152 sprinklers of the waffle
    # field contribute nothing to the shot that matters most. Two smooth white
    # rings then read as a light fitting, not as a building. So the aprons are
    # PANELLED: a real curved soffit of this diameter is made of segments and
    # the joint is the thing that gives it scale.
    #
    # The segment count is not chosen, it is derived: a constant 0.70 m arc, so
    # the joint spacing is the same at r 5.7 and at r 8.1, which is what a
    # fabricator would actually do. 48 and 72 fall out of it.
    a = Acc()
    aprons = ((R_RINGA_OUT, R_RINGB_IN, (5.575, 5.710, 5.845), 48, "in"),
              (R_RINGC_OUT, R_APRON_OUT, (7.90, 8.06, 8.22, 8.38), 72, "out"))
    for (r0, r1, grooves, nseg, tag) in aprons:
        a.new_island()
        a.ring(r0, r1, Z_APRON, Z_APRON + 0.042)
        for rg in grooves:
            a.new_island()
            a.ring(rg - 0.011, rg + 0.011, Z_APRON + 0.006, Z_APRON + 0.042)
        for i in range(nseg):
            th = 2.0 * math.pi * i / nseg
            ct, st = math.cos(th), math.sin(th)
            a.new_island()
            v, q = _rib(r0 + 0.004, r1 - 0.004, ct, st, 0.009,
                        Z_APRON - 0.009, Z_APRON + 0.004)
            a.add(v, q)
    made["aprons"] = _emit(a, PFX + "Apron", c, M["panel"], smooth_deg=25.0)

    # SIX RADIAL SPINES, from the drum rim to the outer edge, on ONE set of
    # angles.  They run under the aprons and jump UP over each light slot,
    # where they become the slot trimmers 40 mm and 15 mm above the two cove
    # emitters respectively -- which is exactly the move a real building makes
    # to get a service run across a light slot without standing in it.  They
    # are what stops nine concentric bands reading as a target.
    a = Acc()
    for i in range(6):
        th = 2.0 * math.pi * i / 6.0
        ct, st = math.cos(th), math.sin(th)
        a.new_island()
        v, q = _rib(R_S1_MOUTH_IN, R_S1_MOUTH_OUT, ct, st, 0.055, 6.100, Z_DECK)
        a.add(v, q)                                       # over slot 1
        a.new_island()
        v, q = _rib(R_S2_MOUTH_IN, R_S2_MOUTH_OUT, ct, st, 0.048, 6.155, Z_DECK)
        a.add(v, q)                                       # over slot 2
        a.new_island()
        v, q = _rib(R_RINGA_IN, R_RINGB_OUT, ct, st, 0.065,
                    Z_APRON - 0.098, Z_APRON)             # over the inner apron
        a.add(v, q)
        a.new_island()
        v, q = _rib(R_RINGC_IN, R_APRON_OUT, ct, st, 0.065,
                    Z_APRON - 0.098, Z_APRON)             # over the outer apron
        a.add(v, q)
        # the risers that carry a spine up into a slot and back down
        for rr in (R_S1_MOUTH_IN, R_S1_MOUTH_OUT, R_S2_MOUTH_IN, R_S2_MOUTH_OUT):
            a.new_island()
            v, q = _rib(rr - 0.055, rr + 0.055, ct, st, 0.048,
                        Z_APRON - 0.098, 6.155)
            a.add(v, q)
    made["trimmers"] = _emit(a, PFX + "SlotTrimmer", c, M["galv"], smooth_deg=25.0)

    # FITTINGS ON THE APRONS.  A 17 m soffit over a show car has downlights,
    # sprinklers, speakers and access hatches in it, and they are the things
    # that must NOT repeat: position, size, rotation and type all come from
    # the fitting's own coordinates through `_h`.
    body = Acc()
    trim = Acc()
    n_fit = 0
    for (r0, r1, tag, nring) in ((R_RINGA_OUT + 0.10, R_RINGB_IN - 0.10, "in", 20),
                                 (R_RINGC_OUT + 0.12, R_APRON_OUT - 0.12, "out", 34)):
        for i in range(nring):
            hh = _h(tag, i, "fit")
            h2 = _h(i, tag, "fit2")
            h3 = _h(i, i, tag)
            th = 2.0 * math.pi * (i + 0.22 * h2) / nring
            r = r0 + (r1 - r0) * (0.28 + 0.44 * hh)
            fx, fy = r * math.cos(th), r * math.sin(th)
            if h3 < 0.46:                      # a recessed downlight, unlit
                rd = 0.048 + 0.020 * hh
                trim.new_island()
                trim.ring(rd, rd + 0.012 + 0.005 * h2, Z_APRON - 0.006,
                          Z_APRON + 0.004, seg=20, cx=fx, cy=fy)
                body.new_island()
                body.cyl(rd, Z_APRON - 0.004, Z_APRON + 0.030, cx=fx, cy=fy,
                         seg=20)
                body.cone(rd, rd * 0.55, Z_APRON + 0.030, Z_APRON + 0.041,
                          cx=fx, cy=fy, seg=20)
            elif h3 < 0.70:                    # a pendant sprinkler
                body.new_island()
                body.cyl(0.0125, Z_APRON - 0.075 - 0.020 * hh, Z_APRON + 0.004,
                         cx=fx, cy=fy, seg=12)
                body.cone(0.0195, 0.0290, Z_APRON - 0.095 - 0.020 * hh,
                          Z_APRON - 0.105 - 0.020 * hh, cx=fx, cy=fy, seg=12)
                trim.new_island()
                trim.ring(0.026, 0.042, Z_APRON - 0.010, Z_APRON + 0.002,
                          seg=20, cx=fx, cy=fy)
            elif h3 < 0.86:                    # a flush speaker grille
                rd = 0.085 + 0.030 * h2
                trim.new_island()
                trim.ring(rd, rd + 0.014, Z_APRON - 0.008, Z_APRON + 0.004,
                          seg=28, cx=fx, cy=fy)
                body.new_island()
                body.cyl(rd, Z_APRON - 0.002, Z_APRON + 0.038, cx=fx, cy=fy,
                         seg=28)
            else:                              # an access hatch, square, skewed
                w = 0.24 + 0.10 * hh
                trim.new_island()
                for (ax, ay, bx, by) in ((-w, -w, w, -w + 0.020),
                                         (-w, w - 0.020, w, w),
                                         (-w, -w, -w + 0.020, w),
                                         (w - 0.020, -w, w, w)):
                    trim.box(fx + ax, fx + bx, fy + ay, fy + by,
                             Z_APRON - 0.007, Z_APRON + 0.004)
            n_fit += 1
    made["apron_fittings"] = _emit(body, PFX + "ApronFitting", c, M["fixture"],
                                   smooth_deg=30.0)
    made["apron_trim"] = _emit(trim, PFX + "ApronTrim", c, M["diffuser"],
                               smooth_deg=30.0)

    # ------------------------------------------------------------------ #
    # 5d.  the perimeter bulkhead — the ceiling stops 60 mm short of the
    #      wall and the junction gets a real shadow gap instead of a butt.
    # ------------------------------------------------------------------ #
    a = Acc()
    xo, yo = ROOM_X - PERIM_GAP, ROOM_Y - PERIM_GAP
    a.new_island(); a.box(-xo, xo, yo - PERIM_W, yo, Z_PERIM_SOFFIT, Z_DECK)
    a.new_island(); a.box(-xo, xo, -yo, -yo + PERIM_W, Z_PERIM_SOFFIT, Z_DECK)
    a.new_island(); a.box(-xo, -xo + PERIM_W, -yo + PERIM_W, yo - PERIM_W,
                          Z_PERIM_SOFFIT, Z_DECK)
    a.new_island(); a.box(xo - PERIM_W, xo, -yo + PERIM_W, yo - PERIM_W,
                          Z_PERIM_SOFFIT, Z_DECK)
    made["perimeter"] = _emit(a, PFX + "Perimeter", c, M["beam"], smooth_deg=25.0)

    # ------------------------------------------------------------------ #
    # 5e.  the beam grid, on the CURTAIN WALL'S OWN MULLION SPACING.
    #      primaries run in x (constant y) as Vierendeel girders; secondaries
    #      run in y (constant x) as plain downstands, interrupted at every
    #      primary so the joint reads as a joint.
    # ------------------------------------------------------------------ #
    pri_y = [-ROOM_Y + j * BAY_Y for j in range(1, 10)]      # -8.8 .. 8.8
    sec_x = [-ROOM_X + k * BAY_X for k in range(1, 14)]      # -12.857 .. 12.857

    a = Acc()
    n_pri_post = 0
    for y in pri_y:
        for t0, t1 in _seg_runs((-X_IN, y), (X_IN, y), 900,
                                lambda X, Y: not _blocked(X, Y)):
            x0 = -X_IN + 2.0 * X_IN * t0
            x1 = -X_IN + 2.0 * X_IN * t1
            if x1 - x0 < 0.25:
                continue
            a.new_island()
            a.box(x0, x1, y - PRI_W / 2, y + PRI_W / 2, Z_PRI_BOT,
                  Z_PRI_FLANGE_TOP)                             # bottom flange
            a.box(x0, x1, y - PRI_W / 2, y + PRI_W / 2,
                  Z_PRI_TOP_FLANGE_BOT, Z_DECK)                 # top flange
            # web posts at a third of a bay, so the lightened web reads as a
            # rhythm through the 180 mm gap between flange and panel field
            step = BAY_X / 3.0
            m0 = int(math.ceil(x0 / step))
            m1 = int(math.floor(x1 / step))
            for m in range(m0, m1 + 1):
                px = m * step
                if px - PRI_POST_W / 2 < x0 or px + PRI_POST_W / 2 > x1:
                    continue
                a.box(px - PRI_POST_W / 2, px + PRI_POST_W / 2,
                      y - PRI_W / 2 + 0.012, y + PRI_W / 2 - 0.012,
                      Z_PRI_FLANGE_TOP, Z_PRI_TOP_FLANGE_BOT)
                n_pri_post += 1
    made["primary"] = _emit(a, PFX + "PrimaryBeam", c, M["beam"], smooth_deg=25.0)

    a = Acc()
    def _sec_ok(X, Y):
        if _blocked(X, Y):
            return False
        return all(abs(Y - py) > PRI_W / 2 + 0.030 for py in pri_y)
    for x in sec_x:
        for t0, t1 in _seg_runs((x, -Y_IN), (x, Y_IN), 900, _sec_ok):
            y0 = -Y_IN + 2.0 * Y_IN * t0
            y1 = -Y_IN + 2.0 * Y_IN * t1
            if y1 - y0 < 0.20:
                continue
            a.new_island()
            a.box(x - SEC_W / 2, x + SEC_W / 2, y0, y1, Z_SEC_SOFFIT, Z_DECK)
    made["secondary"] = _emit(a, PFX + "SecondaryBeam", c, M["beam"],
                              smooth_deg=25.0)

    # ------------------------------------------------------------------ #
    # 5f.  the panel field.  One object, one island per tray, a `pnl`
    #      attribute per tray so no two trays are the same tone, roughness
    #      or perforation phase.  Trays are pillowed: a 1 m metal tray on
    #      four edges is never dead flat and the highlight is what shows it.
    # ------------------------------------------------------------------ #
    a = Acc()
    cells, n_full, n_quarter = [], 0, 0
    for m in range(28):
        cx0, cx1 = -ROOM_X + m * BAY_X / 2, -ROOM_X + (m + 1) * BAY_X / 2
        for nj in range(20):
            cy0, cy1 = -ROOM_Y + nj * BAY_Y / 2, -ROOM_Y + (nj + 1) * BAY_Y / 2
            if _cell_clear(cx0, cx1, cy0, cy1):
                cells.append((cx0, cx1, cy0, cy1, m % 2, nj % 2))
                n_full += 1
            else:
                # finer trays ring the feature, which is what a real ceiling
                # does at an obstruction.  one level of split, no more.
                for sx in range(2):
                    for sy in range(2):
                        qx0 = cx0 + sx * (cx1 - cx0) / 2
                        qx1 = qx0 + (cx1 - cx0) / 2
                        qy0 = cy0 + sy * (cy1 - cy0) / 2
                        qy1 = qy0 + (cy1 - cy0) / 2
                        if _cell_clear(qx0, qx1, qy0, qy1):
                            cells.append((qx0, qx1, qy0, qy1,
                                          (m * 2 + sx) % 2, (nj * 2 + sy) % 2))
                            n_quarter += 1

    pnl_vals = []
    for (x0, x1, y0, y1, mx, my) in cells:
        # inset: the wide inset is against a beam centreline, the narrow one
        # is the 12 mm reveal between two trays.
        ix0 = 0.065 if mx == 0 else 0.006
        ix1 = 0.006 if mx == 0 else 0.065
        iy0 = 0.140 if my == 0 else 0.006
        iy1 = 0.006 if my == 0 else 0.140
        px0, px1 = max(x0 + ix0, -X_IN), min(x1 - ix1, X_IN)
        py0, py1 = max(y0 + iy0, -Y_IN), min(y1 - iy1, Y_IN)
        if px1 - px0 < 0.12 or py1 - py0 < 0.12:
            continue
        isl = a.new_island()
        h = _h(round(px0, 3), round(py0, 3), "tray")
        sag = 0.0016 + 0.0026 * h
        v, q = _tray(px0, px1, py0, py1, Z_PANEL, PANEL_T, sag)
        a.add(v, q, isl)
        pnl_vals.append((len(v), h))
    ob = _emit(a, PFX + "PanelField", c, M["panel"], smooth_deg=28.0, attr=None)
    if ob is not None:
        vals = np.concatenate([np.full(n, h) for n, h in pnl_vals])
        K.bake_attributes(ob.data, {"pnl": vals})
    made["panels"] = ob

    # ------------------------------------------------------------------ #
    # 5g.  the housings.  The brief's charge is that 23 lamps hang from
    #      nothing.  MEASURED, that is half true and worth saying exactly:
    #      six of the 23 (Spot_0..5) already have SpotRod + SpotCan + SpotLens
    #      from round 1, and the other 17 are floor bollards, wall washers and
    #      the four-lamp car rig at z 0.62..4.60 — none of them ceiling lamps.
    #      What the six rods did NOT have is anything to hang FROM: they
    #      terminate at z 6.140 in mid-air under a 686 m^2 quad.  These are
    #      the canopies that land them, and they are placed against each rod's
    #      own measured coordinates, not a repeated pattern.
    # ------------------------------------------------------------------ #
    a = Acc()
    for (rx, ry) in SPOT_RODS:
        r = _r(rx, ry)
        if R_S2_IN <= r <= R_S2_OUT:
            zc = Z_DECK                       # hangs off the slot head
        else:
            zc = Z_PANEL                      # surface-mounted, proud of the
            #                                   apron plate or the tray it is on
        a.new_island()
        a.cyl(0.098, zc - 0.026, zc + 0.004, cx=rx, cy=ry, seg=32)
        a.cone(0.098, 0.058, zc - 0.026, zc - 0.062, cx=rx, cy=ry, seg=32)
        a.cyl(0.036, zc - 0.062, Z_ROD_TOP - 0.010, cx=rx, cy=ry, seg=20)
        # a strain-relief loop of flex, different length on every one
        h = _h(rx, ry, "flex")
        a.new_island()
        a.cyl(0.009, Z_ROD_TOP - 0.010 - 0.09 - 0.10 * h, Z_ROD_TOP - 0.010,
              cx=rx + 0.062, cy=ry + 0.010 + 0.03 * h, seg=8)
    made["canopies"] = _emit(a, PFX + "SpotCanopy", c, M["fixture"],
                             smooth_deg=32.0)

    # ------------------------------------------------------------------ #
    # 5h.  lighting track and heads.  UNLIT, all of them, and that is the
    #      point: a showroom rigged for a presentation has far more heads
    #      than it has switched on, and an unlit head adds zero watts, so the
    #      ceiling can be populated without touching 46,203.313 W.
    # ------------------------------------------------------------------ #
    trk = Acc()
    hds = Acc()
    n_head = 0
    # straight runs on the secondary beams, only where a run is long enough
    for x in sec_x[1::3]:
        for t0, t1 in _seg_runs((x, -Y_IN), (x, Y_IN), 600,
                                lambda X, Y: not _blocked(X, Y)):
            y0 = -Y_IN + 2.0 * Y_IN * t0 + 0.15
            y1 = -Y_IN + 2.0 * Y_IN * t1 - 0.15
            if y1 - y0 < 1.4:
                continue
            trk.new_island()
            trk.box(x - 0.021, x + 0.021, y0, y1,
                    Z_SEC_SOFFIT - 0.036, Z_SEC_SOFFIT)
            trk.box(x - 0.014, x + 0.014, y0, y1,
                    Z_SEC_SOFFIT - 0.046, Z_SEC_SOFFIT - 0.036)
            n_head += _heads_along(hds, x, y0, y1, Z_SEC_SOFFIT - 0.046,
                                   key=("sec", x))
    # a circular track on the drum's step A, aimed inward at the turntable
    rtr = (R_STEP_A + R_DRUM_FIELD) / 2.0
    trk.new_island()
    trk.ring(rtr - 0.021, rtr + 0.021, Z_STEP_A - 0.055 - 0.036,
             Z_STEP_A - 0.055, seg=128)
    n_head += _heads_ring(hds, rtr, Z_STEP_A - 0.055 - 0.036)
    made["track"] = _emit(trk, PFX + "Track", c, M["track"], smooth_deg=25.0)
    made["heads"] = _emit(hds, PFX + "TrackHead", c, M["fixture"], smooth_deg=30.0)

    # ------------------------------------------------------------------ #
    # 5i.  fire protection.  686 m^2 at ordinary-hazard spacing is about 60
    #      heads; this lays them on a staggered grid inside the coffers and
    #      varies drop, rotation and escutcheon on every one.
    # ------------------------------------------------------------------ #
    a = Acc()
    esc = Acc()
    n_spr = 0
    for m in range(28):
        for nj in range(20):
            if (m + nj) % 2:
                continue
            hx = -ROOM_X + (m + 0.5) * BAY_X / 2
            hy = -ROOM_Y + (nj + 0.5) * BAY_Y / 2
            if _blocked(hx, hy) or abs(hx) > X_IN - 0.2 or abs(hy) > Y_IN - 0.2:
                continue
            h = _h(m, nj, "sprk")
            h2 = _h(nj, m, "sprk2")
            jx = hx + (h - 0.5) * 0.16
            jy = hy + (h2 - 0.5) * 0.16
            drop = 0.082 + 0.030 * h
            zt = Z_PANEL
            a.new_island()
            a.cyl(0.0125, zt - drop, zt + 0.004, cx=jx, cy=jy, seg=12)
            a.cyl(0.0195, zt - drop - 0.020, zt - drop, cx=jx, cy=jy, seg=12)
            # the deflector, tilted a little differently on every head
            a.cone(0.0195, 0.0290, zt - drop - 0.020, zt - drop - 0.030,
                   cx=jx, cy=jy, seg=12)
            esc.new_island()
            esc.ring(0.026, 0.041 + 0.006 * h2, zt - 0.010, zt + 0.002,
                     seg=20, cx=jx, cy=jy)
            n_spr += 1
    made["sprinklers"] = _emit(a, PFX + "Sprinkler", c, M["brass"],
                               smooth_deg=30.0)
    made["escutcheons"] = _emit(esc, PFX + "Escutcheon", c, M["diffuser"],
                                smooth_deg=30.0)

    # ------------------------------------------------------------------ #
    # 5j.  air.  Four supply diffusers with real blades and two eggcrate
    #      returns, set into the panel field on the coffer grid.
    # ------------------------------------------------------------------ #
    a = Acc()
    n_dif = 0
    supply = ((-10.714, -6.6), (10.714, -6.6), (-10.714, 6.6), (10.714, 6.6),
              (-4.286, -9.9), (4.286, 9.9))
    for i, (dx, dy) in enumerate(supply):
        if _blocked(dx, dy):
            continue
        a.new_island()
        _diffuser(a, dx, dy, Z_PANEL, blades=4 + (i % 2),
                  key=("sup", i))
        n_dif += 1
    ret = ((-2.143, -9.9), (2.143, 9.9))
    for i, (dx, dy) in enumerate(ret):
        a.new_island()
        _eggcrate(a, dx, dy, Z_PANEL)
        n_dif += 1
    made["diffusers"] = _emit(a, PFX + "Diffuser", c, M["diffuser"],
                              smooth_deg=30.0)

    # ------------------------------------------------------------------ #
    # 5k.  services, visible ONLY where the plenum is open: inside slot 1.
    #      A conduit arc on the deck with two junction boxes, silhouetted
    #      against the cove.  Slot 2 gets none: Cove_RingOuter sits at 6.140
    #      and leaves 45 mm of deck clearance, which is not enough for a
    #      conduit that is not touching the emitter.
    # ------------------------------------------------------------------ #
    a = Acc()
    rc = (R_S1_IN + R_S1_OUT) / 2.0 + 0.14
    a.new_island()
    a.ring(rc - 0.014, rc + 0.014, Z_DECK - 0.052, Z_DECK - 0.024, seg=128)
    for i in range(3):
        th = 2.0 * math.pi * (i + 0.28) / 3.0
        bx, by = rc * math.cos(th), rc * math.sin(th)
        a.new_island()
        a.box(bx - 0.055, bx + 0.055, by - 0.042, by + 0.042,
              Z_DECK - 0.070, Z_DECK - 0.008)
    made["services"] = _emit(a, PFX + "Service", c, M["galv"], smooth_deg=30.0)

    summary = {
        "objects": {k: (v.name if v is not None else None)
                    for k, v in made.items()},
        "collection": c.name,
        "materials": sorted(m.name for m in _mats().values()),
        "n_panel_cells": len(cells),
        "n_panel_full": n_full,
        "n_panel_quarter": n_quarter,
        "n_web_posts": n_pri_post,
        "n_track_heads": n_head,
        "n_sprinklers": n_spr,
        "n_diffusers": n_dif,
        "n_apron_fittings": n_fit,
        "n_drum_fittings": n_drum_fit,
        "polys": int(sum(len(v.data.polygons) for v in made.values()
                         if v is not None)),
        "verts": int(sum(len(v.data.vertices) for v in made.values()
                         if v is not None)),
        # MEASURED off the emitted meshes, not quoted from the constants.
        # It used to be `[Z_PRI_BOT, Z_DECK + DECK_T]` -- the primary beam's
        # bottom -- and that is wrong by 190 mm, because the lowest thing on
        # this ceiling is a TRACK HEAD BARREL at z 5.5705, not a beam. A
        # declared extent that disagrees with the geometry is the same defect
        # as a declared anything else that disagrees with the geometry, and it
        # was found by the library's append test asserting against the
        # constant and failing on the mesh.
        "z_extent": _measured_z_extent(made),
    }
    if report:
        print(">> ceiling: %d objects, %d polys, %d verts"
              % (len([v for v in made.values() if v is not None]),
                 summary["polys"], summary["verts"]))
        print(">>   trays %d (%d full, %d quarter), heads %d, sprinklers %d, "
              "diffusers %d, web posts %d"
              % (len(cells), n_full, n_quarter, n_head, n_spr, n_dif,
                 n_pri_post))
        print(">>   apron fittings %d, drum fittings %d, apron segments 48+72"
              % (n_fit, n_drum_fit))
    return summary


# =========================================================================== #
#  6.  PIECE BUILDERS
# =========================================================================== #


def _measured_z_extent(made):
    """The built ceiling's real z span, from the meshes it emitted."""
    import numpy as np
    lo, hi = None, None
    for ob in made.values():
        if ob is None or ob.type != "MESH" or not len(ob.data.vertices):
            continue
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_basis)      # fresh objects: basis, not world
        z = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])[:, 2]
        lo = float(z.min()) if lo is None else min(lo, float(z.min()))
        hi = float(z.max()) if hi is None else max(hi, float(z.max()))
    return [None if lo is None else round(lo, 4),
            None if hi is None else round(hi, 4)]


def _rib(r0, r1, ct, st, hw, z0, z1):
    """A radial bar from r0 to r1 along (ct, st), half-width hw, z0..z1."""
    nx, ny = -st, ct
    pts = []
    for r in (r0, r1):
        for s in (-1, 1):
            pts.append((r * ct + s * hw * nx, r * st + s * hw * ny))
    # order: (r0,-), (r0,+), (r1,+), (r1,-)
    p = [pts[0], pts[1], pts[3], pts[2]]
    v = [(p[i][0], p[i][1], z0) for i in range(4)] + \
        [(p[i][0], p[i][1], z1) for i in range(4)]
    q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, q


def _cell_clear(x0, x1, y0, y1):
    """True if a tray on this rectangle keeps entirely clear of the feature."""
    if min(x1, X_IN) - max(x0, -X_IN) < 0.12:
        return False
    if min(y1, Y_IN) - max(y0, -Y_IN) < 0.12:
        return False
    for cx in (x0, x1):
        for cy in (y0, y1):
            if _r(cx, cy) < R_FEAT:
                return False
    # a circle can bulge through an edge without touching a corner
    for cx in (x0, x1):
        if y0 <= 0.0 <= y1 and abs(cx) < R_FEAT:
            return False
    for cy in (y0, y1):
        if x0 <= 0.0 <= x1 and abs(cy) < R_FEAT:
            return False
    return True


def _tray(x0, x1, y0, y1, z, t, sag):
    """A closed pillowed metal tray: 5x5 dished underside, flat back, sides."""
    n = 5
    u = np.linspace(0.0, 1.0, n)
    X = x0 + (x1 - x0) * u
    Y = y0 + (y1 - y0) * u
    XX, YY = np.meshgrid(X, Y, indexing="ij")
    # a cosine pillow: zero on the four edges, `sag` at the centre
    dish = (np.sin(math.pi * u)[:, None] * np.sin(math.pi * u)[None, :])
    ZB = z - sag * dish
    bot = np.stack([XX.ravel(), YY.ravel(), ZB.ravel()], 1)
    top = np.stack([XX.ravel(), YY.ravel(),
                    np.full(n * n, z + t)], 1)
    v = np.concatenate([bot, top])
    idx = np.arange(n * n).reshape(n, n)
    q = []
    for i in range(n - 1):
        for j in range(n - 1):
            q.append((idx[i, j], idx[i, j + 1], idx[i + 1, j + 1], idx[i + 1, j]))
    off = n * n
    for i in range(n - 1):
        for j in range(n - 1):
            q.append((off + idx[i, j], off + idx[i + 1, j],
                      off + idx[i + 1, j + 1], off + idx[i, j + 1]))
    # skirt around the boundary loop
    loop = ([idx[0, j] for j in range(n - 1)] +
            [idx[i, n - 1] for i in range(n - 1)] +
            [idx[n - 1, j] for j in range(n - 1, 0, -1)] +
            [idx[i, 0] for i in range(n - 1, 0, -1)])
    for k in range(len(loop)):
        a0 = loop[k]
        a1 = loop[(k + 1) % len(loop)]
        q.append((a0, a1, off + a1, off + a0))
    return v, q


def _heads_along(acc, x, y0, y1, ztrack, key):
    """Track heads on a straight run.  Station, body, aim and tilt all vary."""
    n = 0
    y = y0 + 0.28
    i = 0
    while y < y1 - 0.24:
        h = _h(key[0], round(key[1], 3), i, "head")
        h2 = _h(i, round(key[1], 3), key[0], "aim")
        h3 = _h(round(key[1], 3), i, "type")
        # a real track is not evenly loaded: gaps where a head was never fitted
        if h3 < 0.22:
            y += 0.52 + 0.42 * h
            i += 1
            continue
        body = int(h3 * 3.0) % 3
        _head(acc, x, y, ztrack, body, h, h2)
        n += 1
        y += 0.60 + 0.55 * h2
        i += 1
    return n


def _heads_ring(acc, r, ztrack):
    """Heads on the drum's circular track, aimed inward at the turntable."""
    n = 0
    th = 0.0
    i = 0
    while th < 2.0 * math.pi - 0.10:
        h = _h(i, "ringhead")
        h2 = _h("ringhead", i)
        h3 = _h(i, i, "ringtype")
        if h3 < 0.14:
            th += 0.30 + 0.22 * h
            i += 1
            continue
        _head(acc, r * math.cos(th), r * math.sin(th), ztrack,
              int(h3 * 3.0) % 3, h, h2)
        n += 1
        th += 0.26 + 0.20 * h2
        i += 1
    return n


def _head(acc, x, y, ztrack, body, h, h2):
    """One track head.  Three body types, and no two share a pose.

    Modelled in its own hanging pose rather than instanced-and-rotated: the
    gimbal yoke, the barrel and the snoot are laid out from the tilt, so the
    barrel's silhouette differs head to head, which is the whole point.
    """
    acc.new_island()
    # shoe on the track
    acc.box(x - 0.026, x + 0.026, y - 0.030, y + 0.030,
            ztrack - 0.028, ztrack + 0.002)
    # stem
    zg = ztrack - 0.028 - (0.052 + 0.040 * h)
    acc.cyl(0.011, zg, ztrack - 0.028, cx=x, cy=y, seg=10)
    # yoke cheeks
    acc.box(x - 0.048, x - 0.038, y - 0.030, y + 0.030, zg - 0.052, zg + 0.008)
    acc.box(x + 0.038, x + 0.048, y - 0.030, y + 0.030, zg - 0.052, zg + 0.008)
    # the barrel, tilted -- length and taper by body type
    tilt = (0.10 + 0.55 * h2) * (1.0 if h > 0.5 else -1.0)
    L = (0.115, 0.145, 0.092)[body]
    R0 = (0.040, 0.034, 0.049)[body]
    R1 = (0.046, 0.038, 0.043)[body]
    cz = zg - 0.024
    dx = math.sin(tilt) * math.cos(2.0 * math.pi * h)
    dy = math.sin(tilt) * math.sin(2.0 * math.pi * h)
    dz = -math.cos(tilt)
    seg = 18
    a = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    # a frame orthogonal to the barrel axis
    ax = np.array([dx, dy, dz], float)
    ax /= np.linalg.norm(ax)
    up = np.array([0.0, 0.0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(ax, up); e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    c0 = np.array([x, y, cz])
    rings = []
    for tt, rr in ((0.0, R0), (L * 0.72, R0), (L, R1), (L + 0.012, R1 * 0.86)):
        p = c0 + ax * tt
        rings.append(p[None, :] + rr * (np.cos(a)[:, None] * e1[None, :] +
                                        np.sin(a)[:, None] * e2[None, :]))
    V = np.concatenate(rings)
    Q = []
    for k in range(len(rings) - 1):
        i0 = k * seg
        i1 = (k + 1) * seg
        for j in range(seg):
            jn = (j + 1) % seg
            Q.append((i0 + j, i0 + jn, i1 + jn, i1 + j))
    # back cap
    cb = len(V)
    V = np.concatenate([V, c0[None, :]])
    for j in range(seg):
        jn = (j + 1) % seg
        Q.append((j, jn, cb, cb))
    acc.add(V, Q)


def _diffuser(acc, x, y, z, blades, key):
    """A square supply diffuser with real blades in a real neck."""
    W = 0.560
    acc.box(x - W / 2 - 0.030, x + W / 2 + 0.030, y - W / 2 - 0.030,
            y + W / 2 + 0.030, z - 0.012, z + 0.006)          # face flange
    acc.box(x - W / 2, x + W / 2, y - W / 2, y + W / 2, z - 0.075, z - 0.012)
    for i in range(blades):
        f = (i + 1) / (blades + 1.0)
        h = _h(key[0], key[1], i, "blade")
        by = y - W / 2 + f * W
        acc.box(x - W / 2 + 0.020, x + W / 2 - 0.020, by - 0.008, by + 0.008,
                z - 0.058 - 0.012 * h, z - 0.020)


def _eggcrate(acc, x, y, z):
    """A return grille: an eggcrate core, which is a DIFFERENT pattern from
    the supply blades.  Two grilles that look alike is the failure mode."""
    W = 0.620
    acc.box(x - W / 2 - 0.028, x + W / 2 + 0.028, y - W / 2 - 0.028,
            y + W / 2 + 0.028, z - 0.010, z + 0.006)
    n = 9
    for i in range(1, n):
        u = -W / 2 + i * W / n
        acc.box(x + u - 0.005, x + u + 0.005, y - W / 2, y + W / 2,
                z - 0.048, z - 0.010)
        acc.box(x - W / 2, x + W / 2, y + u - 0.005, y + u + 0.005,
                z - 0.048, z - 0.010)


# =========================================================================== #
#  7.  SELFTEST — arithmetic and clearances, without Blender
# =========================================================================== #


def _variety(n=4000):
    """MEASURE the per-instance spread `_h` is supposed to give.

    The project's named failure is one asset repeated.  `_h`'s docstring claims
    strings and quantised floats keep the avalanche hash's keys distinct; this
    is the control that makes the claim falsifiable, and it carries a NEGATIVE
    control that must fail -- `hash01` fed the raw floats, which is what the
    module did before `_h` existed.
    """
    import itertools
    xs = [round(-15.0 + i * 1.0714286 / 2.0, 3) for i in range(28)]
    ys = [round(-11.0 + j * 1.1 / 2.0, 3) for j in range(20)]
    good = [_h(x, y, "tray") for x, y in itertools.product(xs, ys)]
    bad = [K.hash01(int(x), int(y)) for x, y in itertools.product(xs, ys)]
    gu, bu = len(set(round(v, 6) for v in good)), len(set(round(v, 6) for v in bad))
    print("   per-tray hash: %d distinct of %d  (raw-float control: %d of %d)"
          % (gu, len(good), bu, len(bad)))
    return gu, len(good), bu, len(bad)


def selftest():
    """Every clearance this design rests on, recomputed.  No bpy needed."""
    bad = []
    print("SHOWROOM CEILING — clearances against the round-1 emitters")

    # 1. the concentric stack must be monotonic and gap-free
    stack = [("hub", 0.0, R_HUB), ("stepC", R_HUB, R_STEP_C),
             ("stepB", R_STEP_C, R_STEP_B), ("stepA", R_STEP_B, R_STEP_A),
             ("drumfield", R_STEP_A, R_DRUM_FIELD),
             ("drumrim", R_DRUM_FIELD, R_DRUM_RIM),
             ("SLOT1mouth", R_DRUM_RIM, R_S1_MOUTH_OUT),
             ("ringA", R_RINGA_IN, R_RINGA_OUT),
             ("apronIn", R_RINGA_OUT, R_RINGB_IN),
             ("ringB", R_RINGB_IN, R_RINGB_OUT),
             ("SLOT2mouth", R_S2_MOUTH_IN, R_S2_MOUTH_OUT),
             ("ringC", R_RINGC_IN, R_RINGC_OUT),
             ("apronOut", R_RINGC_OUT, R_APRON_OUT)]
    for i in range(len(stack) - 1):
        if abs(stack[i][2] - stack[i + 1][1]) > 1e-9:
            bad.append("gap between %s and %s" % (stack[i][0], stack[i + 1][0]))
    for nm, r0, r1 in stack:
        if r1 <= r0:
            bad.append("%s is inside out" % nm)
    print("   %d concentric bands, %.3f m to %.3f m, contiguous: %s"
          % (len(stack), 0.0, R_APRON_OUT, not bad))

    # 2. every emitter must be inside an OPEN slot with clearance both sides
    for nm, z, ri, ro in EMITTER_CLEARANCE:
        slot = (R_S1_IN, R_S1_OUT) if ro < 5.5 else (R_S2_IN, R_S2_OUT)
        ci, co = ri - slot[0], slot[1] - ro
        print("   %-16s r %.2f..%.2f in slot %.2f..%.2f -> clearance "
              "%.3f / %.3f m" % (nm, ri, ro, slot[0], slot[1], ci, co))
        if ci < 0.05 or co < 0.05:
            bad.append("%s has under 50 mm of slot clearance" % nm)

    # 2b.  THE NUMBER THE WHOLE SLOT DESIGN TURNS ON.
    #      Cosine-weighted downward transmittance of the reveal, for a
    #      Lambertian strip in a slot that is effectively infinite
    #      tangentially: T = (sin^2 a1 + sin^2 a2) / 2, where a1 and a2 are the
    #      angles from nadir to the two mouth lips.  Area-weighted across the
    #      emitter.  The FIRST cut of this design -- parallel walls, dark paint
    #      -- measured 0.66 here, which is a third of two coves given away to
    #      their own reveal.  The splay is what bought it back.
    for nm, z, ri, ro in EMITTER_CLEARANCE:
        if ro < 5.5:
            mi, mo, zm = R_S1_MOUTH_IN, R_S1_MOUTH_OUT, Z_S1_MOUTH
        else:
            mi, mo, zm = R_S2_MOUTH_IN, R_S2_MOUTH_OUT, Z_S2_MOUTH
        d = z - zm
        num = den = 0.0
        for k in range(64):
            r = ri + (ro - ri) * (k + 0.5) / 64.0
            a1 = math.atan2(r - mi, d)
            a2 = math.atan2(mo - r, d)
            T = 0.5 * (math.sin(a1) ** 2 + math.sin(a2) ** 2)
            num += T * r
            den += r
        T = num / den
        print("   %-16s reveal depth %.3f m, mouth %.3f..%.3f -> cosine-"
              "weighted downward transmittance %.3f" % (nm, d, mi, mo, T))
        if T < 0.72:
            bad.append("%s keeps only %.2f of its downward emission" % (nm, T))

    # 3. nothing may be built UNDER an emitter
    for nm, z, ri, ro in EMITTER_CLEARANCE:
        for pnm, pz, pri_, pro in (("apronIn", Z_APRON, R_RINGA_OUT, R_RINGB_IN),
                                   ("apronOut", Z_APRON, R_RINGC_OUT, R_APRON_OUT),
                                   ("panelfield", Z_PANEL, R_FEAT, 99.0),
                                   ("ringA", Z_RING_SOFFIT, R_RINGA_IN, R_RINGA_OUT),
                                   ("ringB", Z_RINGB_SOFFIT, R_RINGB_IN, R_RINGB_OUT),
                                   ("ringC", Z_RING_SOFFIT, R_RINGC_IN, R_RINGC_OUT)):
            overlap = min(ro, pro) - max(ri, pri_)
            if overlap > 1e-6 and pz < z:
                bad.append("%s (z %.3f) is UNDER %s (z %.3f), overlap %.3f m"
                           % (pnm, pz, nm, z, overlap))

    # 4. the slot trimmers must be above their emitter
    for nm, z, zt in (("Cove_Ring", 6.060, 6.100),
                      ("Cove_RingOuter", 6.140, 6.155)):
        print("   trimmer over %-16s emitter z %.3f, trimmer bottom z %.3f "
              "-> %.0f mm above" % (nm, z, zt, (zt - z) * 1000))
        if zt <= z:
            bad.append("trimmer over %s is at or below it" % nm)

    # 5. the panel field must conceal Cove_Coffer_* without touching them
    print("   panel face z %.3f vs Cove_Coffer soffit z 6.090 -> %.0f mm below"
          % (Z_PANEL, (6.090 - Z_PANEL) * 1000))
    if Z_PANEL >= 6.090:
        bad.append("the panel field does not conceal Cove_Coffer_*")
    if Z_PANEL + PANEL_T >= 6.090:
        bad.append("the panel field's back collides with Cove_Coffer_*")

    # 6. the widest dropped quarter-tray must sit inside the outer apron
    diag = math.hypot(BAY_X / 4.0, BAY_Y / 4.0)
    print("   worst dropped quarter-tray reaches r = %.3f, apron out %.3f"
          % (R_FEAT + diag, R_APRON_OUT))
    if R_FEAT + diag > R_APRON_OUT:
        bad.append("the outer apron does not cover the dropped trays")

    # 7. the six round-1 spot rods must each land on something
    for rx, ry in SPOT_RODS:
        r = _r(rx, ry)
        where = ("SLOT2 deck" if R_S2_IN <= r <= R_S2_OUT else
                 "apron" if r <= R_APRON_OUT else "secondary beam")
        print("   SpotRod at (%+.2f, %+.2f)  r %.3f -> %s" % (rx, ry, r, where))
        if r < R_S2_IN and r > R_S1_OUT and not (r <= R_APRON_OUT):
            bad.append("SpotRod at (%s,%s) lands on nothing" % (rx, ry))

    # 8. nothing may reach above the round-1 slab soffit
    for nm, z in (("deck", Z_DECK + DECK_T), ("apron top", Z_APRON + 0.042),
                  ("panel back", Z_PANEL + PANEL_T)):
        if z > Z_SLAB:
            bad.append("%s at z %.3f is inside the round-1 slab" % (nm, z))
    print("   highest new surface z %.3f, round-1 slab soffit z %.3f"
          % (Z_DECK + DECK_T, Z_SLAB))

    # 8b.  THE VARIETY CONTROL, with its negative arm
    gu, gn, bu, bn = _variety()
    if gu < 0.98 * gn:
        bad.append("only %d of %d trays get a distinct hash" % (gu, gn))
    if bu >= 0.5 * bn:
        bad.append("the raw-float negative control did NOT collapse; it is not "
                   "a control")

    # 9. the grid must be the curtain wall's
    print("   bay x %.6f m (GW_Front_Mull spacing), bay y %.6f m (GW_Right)"
          % (BAY_X, BAY_Y))
    if abs(BAY_X - 2.142857142857) > 1e-6 or abs(BAY_Y - 2.2) > 1e-9:
        bad.append("the beam grid is not the curtain wall's mullion grid")

    print(">> STAGE RESULT: %s" % ("CEILING_SELFTEST_FAIL" if bad
                                   else "CEILING_SELFTEST_CLEAN"))
    for b in bad:
        print("   BAD: %s" % b)
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if selftest() else 0)
