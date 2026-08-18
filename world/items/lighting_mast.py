#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lighting_mast.py — per-item hero campaign, item ``lighting_mast``
(zone ``paddock``, manifest build order 406, **1 dependant
(``lighting_mast_head``), 0 dependencies**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Eleven hot-dip galvanised steel lattice masts in the paddock, each one a
**triangular lattice of three CHS legs and a welded zigzag of bracing**, bolted
down through a cast plinth on four holding-down bolts, spliced at a bolted ring
flange, and carrying a head frame of independently-yawed spigots — so that what
the lens reads is a piece of fabricated structural steelwork with a weld at
every node, a nut on every bolt, a galvanising run down every downward face and
a crystalline zinc spangle on every square millimetre of it, and not a grey
tapered stick.

--------------------------------------------------------------------------------
1.  THE FRAMING, AND WHY THE MANIFEST AND THE PRESENCE SWEEP ARE BOTH WRONG
--------------------------------------------------------------------------------
This module was dispatched on a measurement that says
``peak_unocc_sharp_px_4k = 2160.0`` — frame-filling — with 138 frames at
>= 300 px. **That number is not a measurement of a lighting mast and this module
does not quote it as one.**

``docs/screen_presence.json``'s own ``presence_unverified_2026_08_04`` block
says the scores are HOST UPPER BOUNDS, and this item's ``host_tier`` is
**ZONE** — the coarsest there is. Its eight declared hosts are

    ARCH_Paving_Paddock   ARCH_RaceControl      ARCH_PaddockBuildings
    ARCH_Ground_ServiceRoad  ARCH_Ground_Compound  ARCH_Ground_Furniture
    ARCH_Ground_Fences    ARCH_Ground_Decks

i.e. the whole paddock. The decisive evidence that the score is the *zone's* and
not the mast's is one line down in the same file: ``lighting_mast_head`` — a
0.6 m luminaire — carries the **identical** host list, the **identical**
``frames_visible`` (1203), the **identical** ``min_depth_m`` (7.602) and the
**identical** ``peak_sharp_frame`` (956). The two rows differ only by the
``height_m`` they were multiplied by. 7.602 m is how close the camera gets to
the paddock *paving*; the camera stands on that paving for the first 44 s of the
film, because world (0, 0) is circuit (-361.49, +81.64), which is inside the
paddock rectangle.

**And the sweep was pointed at the wrong camera.** ``MEASURED_AGAINST`` in the
same file names ``world/camera_rig_path.json`` — the R2-1007 orphan, byte
identical to ``film16``. The live camera is ``render/film17_path.json``
(``docs/LIVE-CAMERA.md``). That is R2-1381a below; it bounds the error to beat 1
only, but beat 1 is 169 of this item's 1203 visible frames.

So the framing here is DERIVED, in section 2, from the live camera path and a
placement this module states and defends. The manifest's own numbers are quoted
for the record and used for nothing:

    manifest    nearest_camera_m 25.0   onscreen_px_4k 1792   hero FALSE
    sweep       peak_unocc_sharp 2160.0 at f956 (HOST, zone-tier, film16)
    THIS MODULE see FILMED_AT_M / ONSCREEN_PX_4K below, and R2-1362

--------------------------------------------------------------------------------
2.  THE PIXEL BUDGET — WHICH OCTAVES ACTUALLY RESOLVE
--------------------------------------------------------------------------------
R2-1031..1037: the circuit surface carried twenty procedural layers and read as
untextured because eight octaves were above the camera's resolvable band and
nine below. A lattice mast spans a wide band, so the band is written down here
and every wavelength in section 6 is placed against it.

``PX_PER_M`` and ``MM_PER_PX`` are computed, never typed. The gate's decisive
fine bands are r1 and r2 — 1 px and 2 px — and its coarse bands are r8 and r16.
The table ``octaves()`` prints is the module's own answer to Law 3 and the
selftest reproduces it.

--------------------------------------------------------------------------------
3.  RELIEF — STATED AS RADIANCE, NEVER AS MILLIMETRES
--------------------------------------------------------------------------------
Every bump in section 6 is asked for as ``modulation_pp=`` plus
``wavelength_m=``; ``itemkit`` derives the millimetres from
``world_contract.SUN_ELEV_DEG`` (12.47 deg, tan e = 0.2213). The amplifier is
not written down anywhere in this file — ``K.sun_amplifier()`` derives it, so a
sun that moves moves it.

Bands used, and why each stage is in the one it is in (the brief's own split):

    bolt heads, weld beads, flange chamfers, galvanising runs   hard_feature
    the zinc spangle itself                                     isotropic_micro

**ZINC SPANGLE IS A NAMED REJECTION AND IT IS BUILT HERE.** Wave 1's
``armco_w_beam`` review found *"no zinc spangle — zero crystal boundaries, zero
polygonal facets, zero dendrite"* in a 0.63 x 0.56 m crop. Spangle is the
solidification structure of the zinc: polygonal grains 5-25 mm across with sharp
crystal boundaries, each grain a slightly different crystallographic orientation
and therefore a slightly different reflectance, with a dendritic sub-structure
inside it. Section 6 builds it as a Voronoi cell field with a hard boundary
ridge, a per-cell tilt, and a finer dendrite Voronoi inside the cells.

**Voronoi is 2.17/scale, not 1.0/scale** (Law 5, and it is aimed at exactly this
material). Nothing in this file writes ``scale=``; every texture is asked for by
``wavelength_m=``, and ``selftest [W]`` RENDERS the spangle node alone through
``K.emitted_wavelength_m`` and counts the cells, because a check that uses the
constant under test on both sides is not a check (R2-058).

--------------------------------------------------------------------------------
4.  BOTH LAYERS
--------------------------------------------------------------------------------
"On this film's sun, the mesh carries the read and the shader garnishes it" —
five of the seven wave-1 modules that passed the relief check did so on geometry
alone. A lattice mast is almost entirely mesh relief, and that is deliberate:

    the lattice itself          3 legs + 78 braces of real swept tube
    a fillet weld bead          a real torus at every brace end, 156 per mast
    the splice ring flange      two real plates, six real bolts, six real nuts
    the holding-down bolts      real hex nuts, real washers, real projections
    the baseplate gussets       real triangular ribs with real fillet welds
    the step bolts              real rungs, 300 mm centres
    the cable riser + saddles   real conduit, real clips, on one leg only

``tools/relief_audit.py`` reports both layers and the selftest calls the
geometry half directly.

--------------------------------------------------------------------------------
5.  VARIATION AT A POPULATION OF ELEVEN
--------------------------------------------------------------------------------
The gate's floor is ``max(8, min(40, sqrt(n)))`` = **8 distinct sources with the
commonest <= 25 %**, and it only applies on the REALIZED-INSTANCE path. This
module takes that path deliberately (``mullion_intact``'s shape: one real
carrier object with a Geometry Nodes tree of ObjectInfo -> Transform -> Join,
``As Instance`` on), because emitting eleven plain objects would land on the
weak path — ``cv_size >= 0.03`` and ``distinct_topologies >= 2`` — and the
question would never be asked. ``verify_instances`` walks the same
``depsgraph.object_instances`` the gate walks and REFUSES if a mast is not at
its own station, so "declared but unrealized" (R2-018/019) cannot happen
silently.

**AND THERE IS A REAL TENSION HERE, WHICH THIS MODULE STATES RATHER THAN HIDES.**
A lighting mast is a manufactured product off one production line. Eleven of
them being eleven *different structures* would be less true than eleven of them
being the same structure differently built, differently fitted and differently
weathered. So the eleven differ in the way real ones differ:

    height class        4 classes (manifest axis): 9.0 / 10.5 / 12.0 / 13.5 m
    node pitch          falls out of the height and the leg count, so the
                        lattice TOPOLOGY differs mast to mast
    section splice      1 or 2 splices depending on height
    base enclosure      on 5 of 11 (manifest axis: "on ~half")
    head spigots        3..6, each on its own yaw
    ladder side         which of the 3 faces carries the step bolts
    riser side          which leg carries the cable, and it is never the ladder
    lean                plumb to +-0.35 deg, about a random bearing
    plinth              size, proud height and chamfer all drawn per mast
    galvanising age     0..1, driving spangle coarseness, white-rust bloom and
                        run-down staining per instance
    damage              a scuffed base band, a bent brace, a missing step bolt

That gives eleven distinct meshes and therefore eleven distinct
``_shape_signature`` fingerprints. Measured numbers are in ``census()`` and in
the gate report; this module reports them and does not assert a verdict.

--------------------------------------------------------------------------------
6.  PLACEMENT
--------------------------------------------------------------------------------
z = 0.000 is one plane. Every mast is seated with ``K.seat_on_ground`` through
``world_contract.world_ground_z``, embedding ``BASE_EMBED_M``; no assumed z
appears anywhere. Every material reads ``TexCoord -> Object``; ``NT`` has no
``position()``.

A 12 m mast is subject to ``tools/placement_gate.py``. The stations in
``STATIONS`` are chosen to clear the road corridor, the car's driven path and
the camera's flight path, and section 11 states the clearance each one has.
**The placement gate's own ``--campath`` default is the R2-1007 orphan** — pass
``--campath render/film17_path.json``. No allow-list is used.

Law 8: no external assets, no image textures, no real sponsor names. The base
enclosure's decal is drawn from ``build_dressing.BRANDS`` through
``K.pick_brand``; no 32nd brand is invented.
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
except Exception:                                    # pragma: no cover
    bpy = None
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                               # noqa: E402
import world_contract as C                                        # noqa: E402

__version__ = "1.0.0"

ITEM = "lighting_mast"
COLL = "W_Item_LightingMast"
SRC_COLL = "W_Item_LightingMast_Sources"
PFX = "LMA_"            # the carrier object and this module's datablocks
SPFX = "LMASRC_"        # the ten instanced source meshes. Deliberately NOT
                        # "LMA_"-prefixed: the gate must not count them as
                        # loose objects (that would put us on the weak
                        # per_instance_variation path -- see section 5).

_T0 = time.time()
VERBOSE = True


def log(msg):
    if VERBOSE:
        sys.stdout.write("[%s %7.1fs] %s\n" % (ITEM, time.time() - _T0, msg))
        sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# --- what the manifest says, quoted for the record and used for NOTHING -------
MANIFEST_NEAREST_M = 25.0
MANIFEST_PX_4K = 1792.0
MANIFEST_HERO = False           # ... while the presence sweep proposes HERO.
MANIFEST_HEIGHT_M = 12.0
MANIFEST_VARIATION_AXES = ("4 heights", "base enclosure on ~half",
                           "galvanising weathering")
SWEEP_PEAK_UNOCC_SHARP_PX = 2160.0      # HOST upper bound, ZONE tier, film16
SWEEP_PEAK_FRAME = 956

# --- what this module is built to. DERIVED; see section 1 and R2-1362. --------
# Produced by `derive_framing()` from the LIVE camera path (`film17`, via
# `tools/live_campath.py`), the ELEVEN AUTHORED STATIONS, the authored height
# classes, and the real camera orientation. The literals here are what that
# derivation returned; `selftest [F]` re-derives and REFUSES if they disagree,
# so they cannot drift from the camera.
FILMED_AT_M = 84.178
LENS_MM = 32.0
ONSCREEN_PX_4K = 588.0
FILMED_FRAME = 1038                     # beat 3 (f865-f1056), NOT beat 4
FILMED_STATION = (-402.0, 59.5)         # circuit; authored site #16
INSTANCES_DECLARED = 11
TYPICAL_H_M = 12.0                      # the manifest's; the AUTHORED classes
                                        # are 11.1-16.4 m -- see HEIGHT_CLASSES

PX_PER_M = (K.RES_X_4K * LENS_MM / K.SENSOR_MM) / FILMED_AT_M
MM_PER_PX = 1000.0 / PX_PER_M


def octaves(px_per_m=None):
    """Law 3, as a table. Which feature sizes land in which of the gate's bands.

    The gate measures fine structure at r1 and r2 and coarse at r8/r16
    (`item_gate.BANDS`). A wavelength above the r16 band is a shape, not a
    texture; one below r1 is a material and will never reach the image. Every
    `wavelength_m=` in section 6 is placed against this table and the selftest
    reproduces it.
    """
    ppm = PX_PER_M if px_per_m is None else float(px_per_m)
    rows = []
    for r in (1, 2, 4, 8, 16):
        rows.append({"band_px": r, "wavelength_m": r / ppm,
                     "wavelength_mm": 1000.0 * r / ppm})
    return {"px_per_m": ppm, "mm_per_px": 1000.0 / ppm, "bands": rows,
            "resolvable_mm": 1000.0 / ppm}


# ==============================================================================
#  0b. THE DERIVATION — the number this module is built to, from the LIVE camera
# ==============================================================================

def derive_framing(stations=None, heights=None, verbose=True):
    """MEASURE where the camera is when it sees one of these. No manifest.

    THE PROBLEM THIS SOLVES. `docs/screen_presence.json` scores this item
    against ZONE-tier hosts (section 1) and the manifest's 25.0 m / 1792 px is
    not reproducible from the live camera for ANY authored mast station. So the
    framing is measured here, from four things that are all authorities:

      * the LIVE camera path, `render/film17_path.json`, read through
        `tools/live_campath.py`, which compares the sha256 in
        `docs/LIVE-CAMERA.md` on every load and RAISES on a mismatch. NEVER
        `world/camera_rig_path.json` -- that is the R2-1007 orphan, and
        `tools/placement_gate.py`'s own `--campath` default is still pointed at
        it, which is why section 11 passes `--campath` explicitly.
      * the ELEVEN AUTHORED STATIONS: `world/build_architecture.py` offers 20
        candidate sites and `_free()` accepts exactly 11 of them. That 11 is
        the manifest's `instances`, and `docs/ITEM-PRESENCE-CENSUS.md`'s
        `ground_light_masts=11`. This module does not invent stations.
      * the real camera ORIENTATION. Distance alone is a trap here and it is
        measured, not argued: authored site (-292.0, 45.5) passes 5.2 m from
        the lens at f1083, which distance-only arithmetic calls 7,560 px, and
        it is OUT OF FRAME ABOVE THE TOP EDGE at every one of those frames --
        the camera is climbing and pitched down at the car, and the vertical
        half-FOV at 32 mm is 17.6 deg. Its real best is 378 px. Distance-only
        scoring overstates that station by 20x.
      * the SHOWROOM. The camera is INSIDE the pavilion for f1..f961 -- all of
        beat 1, all of beat 2, and the first 97 frames of beat 3 -- and the
        pavilion footprint is entirely inside the paddock rectangle. Those
        frames are what put `min_depth_m` at 7.602 in the census. A sightline
        from inside the building to an exterior mast is at best through
        glazing, so `exterior` (f > 961) is reported separately and IS the
        figure this module builds to. Reporting the interior figure as well is
        deliberate: it is the most favourable honest reading and it is 1.5 km
        of lens away from the manifest's story anyway.

    Returns a dict. `selftest [F]` compares it against the module constants.
    """
    _tools = os.path.join(_ROOT, "tools")
    if _tools not in sys.path:
        sys.path.insert(0, _tools)
    import live_campath                                          # noqa: E402
    d = live_campath.load()
    P = d["path"]
    st = list(STATIONS if stations is None else stations)
    hs = [r["height_m"] for r in records()] if heights is None else list(heights)

    W = np.array([C.circuit_to_world(sx, sy) for (sx, sy) in st], float)
    H = np.asarray(hs, float)

    def cam_basis(q):
        w, x, y, z = q
        # Blender's Matrix.to_quaternion() convention; forward is -Z.
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        return R[:, 0], R[:, 1], -R[:, 2]        # right, up, forward

    best = {"exterior": None, "full": None}
    counts = {"exterior_300px": 0, "exterior_150px": 0, "full_300px": 0}
    for e in P:
        f = int(e["f"])
        cp = np.asarray(e["p"], float)
        lens = float(e["lens"])
        right, up, fwd = cam_basis(e["q"])
        tan_x = 0.5 * K.SENSOR_MM / lens
        tan_y = 0.5 * (K.SENSOR_MM * K.RES_Y_4K / K.RES_X_4K) / lens
        for i in range(len(st)):
            # sample the mast up its own height: an object can be in frame at
            # its waist and out of it at its head, and the head is the part
            # that leaves first on a climbing camera.
            zs = np.linspace(0.0, H[i], 9)
            inframe = False
            for zz in zs:
                v = np.array([W[i][0], W[i][1], zz]) - cp
                dz = float(v @ fwd)
                if dz <= 0.0:
                    continue
                if (abs(float(v @ right)) <= tan_x * dz
                        and abs(float(v @ up)) <= tan_y * dz):
                    inframe = True
                    break
            if not inframe:
                continue
            v = np.array([W[i][0], W[i][1], 0.5 * H[i]]) - cp
            dist = float(np.linalg.norm(v))
            px = H[i] * lens * K.RES_X_4K / (K.SENSOR_MM * dist)
            row = {"frame": f, "station": st[i], "height_m": float(H[i]),
                   "distance_m": dist, "lens_mm": lens, "px_4k": px}
            if px >= 300.0:
                counts["full_300px"] += 1
            if best["full"] is None or px > best["full"]["px_4k"]:
                best["full"] = row
            if f > 961:                                   # exterior sightlines
                if px >= 300.0:
                    counts["exterior_300px"] += 1
                if px >= 150.0:
                    counts["exterior_150px"] += 1
                if best["exterior"] is None or px > best["exterior"]["px_4k"]:
                    best["exterior"] = row
    out = {"camera": live_campath.declared_campath(), "stations": st,
           "n_stations": len(st), "best_exterior": best["exterior"],
           "best_full_take": best["full"], "counts": counts,
           "showroom_interior_frames": "f1..f961 (camera inside the pavilion)"}
    if verbose:
        b = best["exterior"]
        log("DERIVED framing: %.2f m on a %.1f mm lens at frame %d, station "
            "%s, a %.2f m mast -> %.0f px of 2160"
            % (b["distance_m"], b["lens_mm"], b["frame"], b["station"],
               b["height_m"], b["px_4k"]))
        log("  full-take best (INCLUDING the 961 frames with the camera inside "
            "the showroom): %.2f m, %.0f px at f%d"
            % (best["full"]["distance_m"], best["full"]["px_4k"],
               best["full"]["frame"]))
        log("  exterior frames at >=300 px: %d;  >=150 px: %d"
            % (counts["exterior_300px"], counts["exterior_150px"]))
    return out


# ==============================================================================
#  1.  DETERMINISTIC PER-MAST DRAWS
# ==============================================================================
# `K.hash01` carries the murmur finaliser; the naive FNV form collapses seven
# degrees of freedom into one and 14 of 15 wave-1 modules shipped it.

SEED = 0x4C4D41            # 'LMA'


def h(uid, k):
    return K.hash01(SEED, int(uid), int(k))


def hpick(uid, k, seq):
    return seq[min(int(h(uid, k) * len(seq)), len(seq) - 1)]


def hspan(uid, k, a, b):
    return a + (b - a) * h(uid, k)


# ==============================================================================
#  2.  GEOMETRY PRIMITIVES — swept tube, torus, hex prism, chamfered box
# ==============================================================================
# All of them emit (verts, quads) in the mast's own local frame, base at z = 0,
# +Z up. `Acc` concatenates and keeps a per-vertex `weld` and `zone` attribute
# that the materials read through ShaderNodeAttribute; that is how the weld-bead
# ripple, the base scuff band and the white-rust bloom know where they are
# without any world-space coordinate (Law 6).

class Acc(object):
    """Vertex/quad accumulator with per-vertex attributes."""

    def __init__(self):
        self.V, self.Q, self.T = [], [], []
        self.A = {"lm_weld": [], "lm_zone": []}
        self.n = 0

    def add(self, V, quads=None, tris=None, weld=0.0, zone=0.0):
        V = np.ascontiguousarray(V, float).reshape(-1, 3)
        if not len(V):
            return
        if quads is not None and len(quads):
            self.Q.append(np.asarray(quads, np.int64).reshape(-1, 4) + self.n)
        if tris is not None and len(tris):
            self.T.append(np.asarray(tris, np.int64).reshape(-1, 3) + self.n)
        self.V.append(V)
        wv = np.asarray(weld, float)
        self.A["lm_weld"].append(np.full(len(V), 0.0) + wv if wv.ndim == 0
                                 else wv.astype(float))
        zv = np.asarray(zone, float)
        self.A["lm_zone"].append(np.full(len(V), 0.0) + zv if zv.ndim == 0
                                 else zv.astype(float))
        self.n += len(V)

    def out(self):
        if not self.V:
            z = np.zeros((0, 3))
            return z, np.zeros((0, 4), np.int64), np.zeros((0, 3), np.int64), {}
        V = np.concatenate(self.V, axis=0)
        Q = (np.concatenate(self.Q, axis=0) if self.Q
             else np.zeros((0, 4), np.int64))
        T = (np.concatenate(self.T, axis=0) if self.T
             else np.zeros((0, 3), np.int64))
        A = {k: np.concatenate(v, axis=0) for k, v in self.A.items()}
        return V, Q, T, A


def _frame(d):
    """Orthonormal (u, v, w) with w along d, plus |d|. Stable for any d."""
    d = np.asarray(d, float)
    L = float(np.linalg.norm(d))
    w = d / max(L, 1e-12)
    a = np.array([0.0, 0.0, 1.0]) if abs(w[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(a, w)
    u /= max(np.linalg.norm(u), 1e-12)
    v = np.cross(w, u)
    return u, v, w, L


def _ring_quads(nz, nu):
    i = np.arange(nz)[:, None]
    j = np.arange(nu)[None, :]
    j1 = (j + 1) % nu
    return np.stack([(i * nu + j).ravel(), (i * nu + j1).ravel(),
                     ((i + 1) * nu + j1).ravel(), ((i + 1) * nu + j).ravel()],
                    axis=1)


def _fan(centre_idx, ring_idx, reverse=False):
    n = len(ring_idx)
    a = ring_idx
    b = np.roll(ring_idx, -1)
    c = np.full(n, centre_idx)
    return np.stack([c, b, a], axis=1) if reverse else np.stack([c, a, b], axis=1)


def tube(acc, p0, p1, r0, r1, nu=16, nz=2, cap0=True, cap1=True,
         phase=0.0, **kw):
    """A swept circular tube from p0 to p1, radius r0 -> r1.

    CAPPED BY DEFAULT, and that is not tidiness: `new_mesh(orient=True)` decides
    winding by exact signed volume, and an OPEN tube encloses nothing and is
    `undecidable` (itemkit section 3b measured exactly this on `armco_w_beam`).
    A capped tube is a closed shell and the volume decides it.
    """
    u, v, w, L = _frame(np.asarray(p1, float) - np.asarray(p0, float))
    if L < 1e-9:
        return
    ts = np.linspace(0.0, 1.0, nz + 1)
    ang = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False) + phase
    ring = np.cos(ang)[:, None] * u[None, :] + np.sin(ang)[:, None] * v[None, :]
    R = r0 + (r1 - r0) * ts
    Ctr = np.asarray(p0, float)[None, :] + np.outer(ts * L, w)
    V = (Ctr[:, None, :] + R[:, None, None] * ring[None, :, :]).reshape(-1, 3)
    Q = _ring_quads(nz, nu)
    tris = []
    extra = []
    base = len(V)
    if cap0:
        extra.append(np.asarray(p0, float))
        tris.append(_fan(base + len(extra) - 1, np.arange(nu), reverse=True))
    if cap1:
        extra.append(np.asarray(p1, float))
        tris.append(_fan(base + len(extra) - 1, np.arange(nz * nu, (nz + 1) * nu)))
    if extra:
        V = np.concatenate([V, np.asarray(extra, float)], axis=0)
    acc.add(V, quads=Q, tris=(np.concatenate(tris, axis=0) if tris else None), **kw)


def torus(acc, centre, axis, R, r, nu=18, nv=9, **kw):
    """A torus — the fillet weld bead at a brace end, and every washer face."""
    u, v, w, _ = _frame(axis)
    a = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    b = np.linspace(0.0, 2.0 * np.pi, nv, endpoint=False)
    ca, sa = np.cos(a)[:, None], np.sin(a)[:, None]
    cb, sb = np.cos(b)[None, :], np.sin(b)[None, :]
    rad = R + r * cb
    P = (np.asarray(centre, float)[None, None, :]
         + (rad * ca)[:, :, None] * u[None, None, :]
         + (rad * sa)[:, :, None] * v[None, None, :]
         + (r * sb)[:, :, None] * w[None, None, :])
    i = np.arange(nu)[:, None]
    j = np.arange(nv)[None, :]
    i1 = (i + 1) % nu
    j1 = (j + 1) % nv
    Q = np.stack([(i * nv + j).ravel(), (i1 * nv + j).ravel(),
                  (i1 * nv + j1).ravel(), (i * nv + j1).ravel()], axis=1)
    acc.add(P.reshape(-1, 3), quads=Q, **kw)


def loft(acc, rings, cap0=True, cap1=True, **kw):
    """Loft a stack of equal-length CLOSED rings. The general shell.

    `rings` is a list of (n, 3) arrays, all the same length. Used for the
    chamfered plinth, the baseplate, the flange plates and the gussets. Capped
    at both ends by default, for the same reason `tube` is: `new_mesh` decides
    winding by exact signed volume and an open shell encloses nothing.
    """
    R = [np.asarray(r, float).reshape(-1, 3) for r in rings]
    n = len(R[0])
    if any(len(r) != n for r in R):
        raise ValueError("loft: every ring must have the same length; got %s"
                         % [len(r) for r in R])
    nz = len(R) - 1
    V = np.concatenate(R, axis=0)
    i = np.arange(nz)[:, None]
    j = np.arange(n)[None, :]
    j1 = (j + 1) % n
    Q = np.stack([(i * n + j).ravel(), (i * n + j1).ravel(),
                  ((i + 1) * n + j1).ravel(), ((i + 1) * n + j).ravel()], axis=1)
    tris, extra = [], []
    if cap0:
        extra.append(R[0].mean(axis=0))
        tris.append(_fan(len(V) + len(extra) - 1, np.arange(n), reverse=True))
    if cap1:
        extra.append(R[-1].mean(axis=0))
        tris.append(_fan(len(V) + len(extra) - 1, np.arange(nz * n, (nz + 1) * n)))
    if extra:
        V = np.concatenate([V, np.asarray(extra, float)], axis=0)
    acc.add(V, quads=Q, tris=(np.concatenate(tris, axis=0) if tris else None), **kw)


def _rect_ring(cx, cy, hx, hy, z):
    """Four corners of an axis-aligned rectangle at height z, CCW from -x-y."""
    return np.array([[cx - hx, cy - hy, z], [cx + hx, cy - hy, z],
                     [cx + hx, cy + hy, z], [cx - hx, cy + hy, z]])


def chamfered_box(acc, cx, cy, z0, z1, hx, hy, ch, **kw):
    """A rectangular block with a chamfer on its top AND bottom arrises.

    The chamfer is the point. A square arris on a cast plinth at this film's
    12.47 deg sun is a specular line; a 25 mm chamfer is a lit facet with its
    own shade, and it is the cheapest `hard_feature` on the object.
    """
    rings = [_rect_ring(cx, cy, hx - ch, hy - ch, z0),
             _rect_ring(cx, cy, hx, hy, z0 + ch),
             _rect_ring(cx, cy, hx, hy, z1 - ch),
             _rect_ring(cx, cy, hx - ch, hy - ch, z1)]
    loft(acc, rings, cap0=True, cap1=True, **kw)


def hex_prism(acc, centre, axis, across_flats, height, chamfer=None, phase=0.0,
              **kw):
    """A hexagon nut or bolt head, with the chamfer real steel nuts have.

    A nut with a square top arris reads as a plastic hexagon. The chamfer is
    ~0.08 of the across-flats and it is what makes the head a machined part.
    """
    u, v, w, _ = _frame(axis)
    Rf = 0.5 * float(across_flats)
    Rc = Rf / math.cos(math.radians(30.0))
    ch = 0.08 * Rc if chamfer is None else float(chamfer)
    a = np.deg2rad(np.arange(6) * 60.0) + phase
    ctr = np.asarray(centre, float)

    def ring(rad, t):
        return (ctr[None, :] + (rad * np.cos(a))[:, None] * u[None, :]
                + (rad * np.sin(a))[:, None] * v[None, :]
                + t * w[None, :])

    rings = [ring(Rc - ch, 0.0), ring(Rc, ch), ring(Rc, height - ch),
             ring(Rc - ch, height)]
    loft(acc, rings, cap0=True, cap1=True, **kw)


def washer(acc, centre, axis, r_in, r_out, t, nu=16, **kw):
    """A plain washer: an annulus with real thickness. Reads at 2 px and is one
    of the fixings whose ABSENCE was a named wave-1 rejection."""
    u, v, w, _ = _frame(axis)
    ang = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    ring = np.cos(ang)[:, None] * u[None, :] + np.sin(ang)[:, None] * v[None, :]
    ctr = np.asarray(centre, float)
    Vs = []
    for rad, zz in ((r_in, 0.0), (r_out, 0.0), (r_out, t), (r_in, t)):
        Vs.append(ctr[None, :] + rad * ring + zz * w[None, :])
    V = np.concatenate(Vs, axis=0)
    Q = []
    for s in range(4):
        a0 = s * nu
        a1 = ((s + 1) % 4) * nu
        j = np.arange(nu)
        j1 = (j + 1) % nu
        Q.append(np.stack([a0 + j, a0 + j1, a1 + j1, a1 + j], axis=1))
    acc.add(V, quads=np.concatenate(Q, axis=0), **kw)


# ==============================================================================
#  3.  THE MAST RECORD — eleven of them, every dimension drawn deterministically
# ==============================================================================
# HEIGHT CLASSES — NOT INVENTED. `world/build_architecture.py::_lightmast`
# draws `rng.choice((11.5, 13.0, 14.5, 16.0)) + rng.uniform(-0.4, 0.4)`, i.e.
# 11.1-16.4 m. That is the manifest's "4 heights" variation axis and it is the
# world's own number. The manifest's `typical_height_m: 12.0` is BELOW the
# authored minimum, so every px figure computed from 12.0 -- including the
# manifest's own 1792 -- understates the object by 8-37 %.
#
# The exact per-mast draws cannot be reproduced: `_lightmast` shares
# `random.Random(6100)` with the Heras fence runs above it, so the stream
# position depends on how much fencing was built. The CLASSES are reproduced;
# the assignment is this module's own `hash01`, and says so.
HEIGHT_CLASSES = (11.5, 13.0, 14.5, 16.0)
HEIGHT_WEIGHTS = (3, 3, 3, 2)          # sums to 11

# CHS sizes, metres. Real hot-rolled circular hollow sections.
CHS = {"leg_lower": 0.1143, "leg_upper": 0.0889, "brace": 0.0483,
       "tie": 0.0603, "spigot": 0.0603, "riser": 0.032, "rung": 0.020}
WALL = 0.005

# STATIONS, circuit frame (x, y). NOT CHOSEN BY THIS MODULE.
#
# `world/build_architecture.py:3349-3355` offers TWENTY candidate sites and
# filters them through its own `_free(x, y, 1.2)`. MEASURED by importing that
# module under Blender and calling `_free` on all twenty: exactly ELEVEN are
# accepted, and eleven is the manifest's `instances` and
# `docs/ITEM-PRESENCE-CENSUS.md`'s `ground_light_masts=11`. Inventing eleven
# stations of my own would have put hero masts where the world has none and
# left the world's eleven as tapered cylinders.
#
# THE NINE REJECTED, for the record, so a later change to `_free` is visible:
#   (-336.0, 86.5) (-268.0, 73.5) (-140.0, 73.5) (-74.0, 86.5) (-8.0, 73.5)
#   (58.0, 86.5) (-96.0, 45.5) (-232.0, 59.5) (-166.0, 112.5)
STATIONS = (
    (-476.0, 84.0), (-440.0, 62.0), (-412.0, 92.0), (-208.0, 86.5),
    (92.0, 62.0), (-424.0, 45.5), (-292.0, 45.5), (44.0, 45.5),
    (-402.0, 59.5), (-58.0, 112.5), (78.0, 96.0),
)
STATIONS_REJECTED = (
    (-336.0, 86.5), (-268.0, 73.5), (-140.0, 73.5), (-74.0, 86.5),
    (-8.0, 73.5), (58.0, 86.5), (-96.0, 45.5), (-232.0, 59.5),
    (-166.0, 112.5),
)


def records(n=INSTANCES_DECLARED):
    """Eleven masts. Every draw is `hash01`-derived, so the set is reproducible
    and any one of them can be rebuilt alone."""
    heights = []
    for hclass, wgt in zip(HEIGHT_CLASSES, HEIGHT_WEIGHTS):
        heights += [hclass] * wgt
    out = []
    for uid in range(n):
        H = heights[uid % len(heights)]
        # face width tapers; a real lattice mast is ~1/10 of its height at base
        w0 = 0.098 * H + hspan(uid, 1, -0.06, 0.06)
        w1 = 0.045 * H + hspan(uid, 2, -0.02, 0.02)
        # node pitch: chosen so the panel aspect is ~0.9-1.15, which is what
        # makes the TOPOLOGY differ between height classes rather than just the
        # scale. `nnode` is the per-mast panel count.
        nnode = int(round(H / hspan(uid, 3, 0.82, 0.98)))
        nnode = max(8, min(18, nnode))
        rec = {
            "uid": uid,
            "height_m": H,
            "w0": w0, "w1": w1,
            "nnode": nnode,
            "n_splice": 1 if H < 13.0 else 2,   # 3 of 11 single-spliced
            # 5 of 11 -- the manifest's "on ~half"
            "enclosure": (uid in (1, 3, 4, 7, 10)),
            "n_spigot": 3 + int(h(uid, 5) * 4.0),          # 3..6
            "ladder_face": int(h(uid, 6) * 3.0) % 3,
            "riser_leg": None,                              # set below
            "lean_deg": hspan(uid, 8, 0.05, 0.35),
            "lean_bearing": hspan(uid, 9, 0.0, 2.0 * math.pi),
            "plinth_hx": hspan(uid, 10, 0.50, 0.62),
            "plinth_proud": hspan(uid, 11, 0.14, 0.30),
            "plinth_ch": hspan(uid, 12, 0.018, 0.032),
            "age": h(uid, 13),                              # galvanising age
            "scuff": h(uid, 14) < 0.55,
            "bent_brace": int(h(uid, 15) * 40.0) if h(uid, 16) < 0.45 else -1,
            "missing_rung": int(h(uid, 17) * 20.0) if h(uid, 18) < 0.4 else -1,
            "yaw": hspan(uid, 19, 0.0, 2.0 * math.pi),
            "station": STATIONS[uid % len(STATIONS)],
        }
        # the cable riser is never on the ladder face's own leg -- a real
        # installation keeps the climbing face clear
        rec["riser_leg"] = (rec["ladder_face"] + 1 + int(h(uid, 7) * 2.0)) % 3
        rec["spigot_yaw"] = [hspan(uid, 30 + i, -0.55, 0.55)
                             for i in range(rec["n_spigot"])]
        out.append(rec)
    return out


# ==============================================================================
#  4.  ONE MAST, AS GEOMETRY
# ==============================================================================
# ZONE codes baked per vertex. Materials read them via ShaderNodeAttribute; no
# material anywhere in this file reads a world position.
Z_STEEL, Z_WELD, Z_CONCRETE, Z_ENCLOSURE = 0.0, 1.0, 2.0, 3.0


def _leg_axis(rec, k, z):
    """Offset of leg k from the mast axis at height `z` ABOVE THE BASEPLATE.

    Returns (x, y, 0) -- the caller adds the absolute z. It returned the height
    in the z component first and every caller then added z again, which built
    every mast at twice its own height; the bbox in `census()` is what caught
    it, which is why the census prints the bbox rather than the nominal.
    """
    H = rec["height_m"]
    t = min(max(z / H, 0.0), 1.0)
    w = rec["w0"] + (rec["w1"] - rec["w0"]) * t
    a = 2.0 * math.pi * k / 3.0 + math.pi / 6.0
    r = w / math.sqrt(3.0)
    return np.array([r * math.cos(a), r * math.sin(a), 0.0])


def build_mast_arrays(rec):
    """Verts, quads, tris and per-vertex attributes for ONE mast. Local frame,
    base of the PLINTH at z = 0."""
    acc = Acc()
    H = rec["height_m"]
    pr = rec["plinth_proud"]
    age = rec["age"]
    kw = dict(zone=Z_STEEL)

    # ---- the plinth, cast in situ ---------------------------------------
    chamfered_box(acc, 0.0, 0.0, -0.10, pr, rec["plinth_hx"], rec["plinth_hx"],
                  rec["plinth_ch"], zone=Z_CONCRETE)

    # ---- the grout bed under the baseplate -------------------------------
    bp_h = 0.360                       # baseplate half-width
    chamfered_box(acc, 0.0, 0.0, pr, pr + 0.032, bp_h + 0.030, bp_h + 0.030,
                  0.010, zone=Z_CONCRETE)

    # ---- the baseplate ----------------------------------------------------
    z_bp = pr + 0.032
    t_bp = 0.028
    chamfered_box(acc, 0.0, 0.0, z_bp, z_bp + t_bp, bp_h, bp_h, 0.006, **kw)

    # ---- four holding-down bolts, with washer, levelling nut and top nut --
    for i in range(4):
        a = math.pi / 4.0 + i * math.pi / 2.0
        rr = bp_h - 0.075
        p = np.array([rr * math.cos(a), rr * math.sin(a), 0.0])
        ax = np.array([0.0, 0.0, 1.0])
        # the levelling nut sits UNDER the plate: this is how a real mast is
        # plumbed, and it is why there is a grout gap to see through
        hex_prism(acc, p + [0, 0, z_bp - 0.026], ax, 0.046, 0.024, **kw)
        washer(acc, p + [0, 0, z_bp + t_bp], ax, 0.017, 0.032, 0.005, **kw)
        hex_prism(acc, p + [0, 0, z_bp + t_bp + 0.005], ax, 0.046, 0.024, **kw)
        # the projecting thread -- 2-4 threads proud is correct and it is what
        # says the bolt was cut long and set in concrete
        tube(acc, p + [0, 0, z_bp + t_bp + 0.029], p + [0, 0, z_bp + t_bp + 0.058],
             0.0152, 0.0150, nu=16, nz=1, **kw)

    z0 = z_bp + t_bp                    # the steel starts on the plate

    # ---- the three legs, spliced --------------------------------------------
    r_lo, r_up = CHS["leg_lower"] * 0.5, CHS["leg_upper"] * 0.5
    z_spl = [z0 + H * f for f in ((0.46,) if rec["n_splice"] == 1
                                  else (0.34, 0.68))]
    seg_z = [z0] + z_spl + [z0 + H]
    for k in range(3):
        for s in range(len(seg_z) - 1):
            za, zb = seg_z[s], seg_z[s + 1]
            ra = r_lo if s == 0 else r_up
            rb = r_lo if s == 0 else r_up
            nz = max(2, int((zb - za) / 0.35))
            pa = _leg_axis(rec, k, za - z0) + [0, 0, za]
            pb = _leg_axis(rec, k, zb - z0) + [0, 0, zb]
            tube(acc, pa, pb, ra, rb, nu=24, nz=nz, **kw)

    # ---- the splice ring flanges -------------------------------------------
    for zs in z_spl:
        for k in range(3):
            c = _leg_axis(rec, k, zs - z0) + [0, 0, zs]
            ax = np.array([0.0, 0.0, 1.0])
            R = r_up + 0.048
            for dz in (-0.018, 0.0):
                loft(acc, [_ring(c + [0, 0, dz], ax, R - 0.004, 0),
                           _ring(c + [0, 0, dz + 0.004], ax, R, 0),
                           _ring(c + [0, 0, dz + 0.014], ax, R, 0),
                           _ring(c + [0, 0, dz + 0.018], ax, R - 0.004, 0)],
                     **kw)
            for b in range(6):
                ab = 2.0 * math.pi * b / 6.0 + 0.2
                pb = c + np.array([(R - 0.020) * math.cos(ab),
                                   (R - 0.020) * math.sin(ab), -0.024])
                hex_prism(acc, pb, ax, 0.032, 0.019, **kw)
                hex_prism(acc, pb + [0, 0, 0.055], ax, 0.032, 0.019, **kw)
                tube(acc, pb + [0, 0, 0.018], pb + [0, 0, 0.056],
                     0.0102, 0.0102, nu=18, nz=1, **kw)
            # the flange-to-leg fillet weld, both plates
            torus(acc, c + [0, 0, -0.021], ax, r_up + 0.007, 0.0065,
                  nu=22, nv=10, weld=1.0, zone=Z_WELD)
            torus(acc, c + [0, 0, 0.021], ax, r_up + 0.007, 0.0065,
                  nu=22, nv=10, weld=1.0, zone=Z_WELD)

    # ---- the bracing: a welded zigzag on each of the three faces -----------
    nn = rec["nnode"]
    pitch = H / nn
    rb = CHS["brace"] * 0.5
    nbrace = 0
    for f in range(3):
        ka, kb = f, (f + 1) % 3
        # each face is phased differently so the three faces are not one
        # pattern rotated -- a real mast's faces are erected independently
        ph = (f * 1) % 2
        for i in range(nn):
            za = z0 + i * pitch
            zb = z0 + (i + 1) * pitch
            up = ((i + ph) % 2 == 0)
            p0 = _leg_axis(rec, ka if up else kb, za - z0) + [0, 0, za]
            p1 = _leg_axis(rec, kb if up else ka, zb - z0) + [0, 0, zb]
            bend = 0.0
            if nbrace == rec["bent_brace"]:
                bend = 0.055           # a fork-lift found this one
            d = p1 - p0
            mid = 0.5 * (p0 + p1)
            if bend:
                n = np.cross(d, [0, 0, 1.0])
                n /= max(np.linalg.norm(n), 1e-9)
                tube(acc, p0, mid + bend * n, rb, rb, nu=18, nz=1, **kw)
                tube(acc, mid + bend * n, p1, rb, rb, nu=18, nz=1, **kw)
            else:
                tube(acc, p0, p1, rb, rb, nu=18, nz=2, **kw)
            for (pe, kleg, ze) in ((p0, ka if up else kb, za),
                                   (p1, kb if up else ka, zb)):
                ax = (p1 - p0) if pe is p0 else (p0 - p1)
                torus(acc, pe + 0.012 * ax / max(np.linalg.norm(ax), 1e-9),
                      ax, rb + 0.006, 0.0055, nu=18, nv=10,
                      weld=1.0, zone=Z_WELD)
            nbrace += 1
        # a horizontal tie at every third node -- the plan bracing
        for i in range(0, nn + 1, 3):
            za = z0 + i * pitch
            p0 = _leg_axis(rec, ka, za - z0) + [0, 0, za]
            p1 = _leg_axis(rec, kb, za - z0) + [0, 0, za]
            tube(acc, p0, p1, CHS["tie"] * 0.5, CHS["tie"] * 0.5, nu=14, nz=2,
                 **kw)

    # ---- baseplate gussets: two triangular ribs per leg, welded both sides -
    # A 10 mm plate rib is 1.5 px at the filmed distance and its WELD is what
    # actually reads -- a 6 mm fillet throws 27 mm of shadow at a 12.47 deg sun
    # (see `octaves()`), which is 4 px. The rib is why the shadow is there.
    for k in range(3):
        p = _leg_axis(rec, k, 0.0) + [0, 0, z0]
        rad = np.array([p[0], p[1], 0.0])
        d = rad / max(np.linalg.norm(rad), 1e-9)
        n = np.array([-d[1], d[0], 0.0])
        for sgn in (-1.0, 1.0):
            c0 = p + sgn * n * (r_lo + 0.010)
            tri = np.array([c0, c0 + d * 0.150, c0 + np.array([0.0, 0.0, 0.30])])
            loft(acc, [tri - 0.005 * n, tri + 0.005 * n],
                 cap0=True, cap1=True, **kw)
        # ONE weld collar per leg, where the leg meets the plate
        torus(acc, p + np.array([0.0, 0.0, 0.006]), np.array([0.0, 0.0, 1.0]),
              r_lo + 0.008, 0.007, nu=22, nv=10, weld=1.0, zone=Z_WELD)

    # ---- step bolts up one face, with one of them missing ------------------
    lf = rec["ladder_face"]
    ka, kb = lf, (lf + 1) % 3
    nr = int((H - 2.4) / 0.30)
    for i in range(nr):
        z = z0 + 2.4 + i * 0.30
        if i == rec["missing_rung"]:
            continue
        pa = _leg_axis(rec, ka, z - z0) + [0, 0, z]
        pb = _leg_axis(rec, kb, z - z0) + [0, 0, z]
        m = 0.5 * (pa + pb)
        dirn = (pb - pa)
        dirn /= max(np.linalg.norm(dirn), 1e-9)
        tube(acc, m - dirn * 0.085, m + dirn * 0.085, CHS["rung"] * 0.5,
             CHS["rung"] * 0.5, nu=18, nz=1, **kw)

    # ---- the cable riser on one leg, with saddle clips ---------------------
    rk = rec["riser_leg"]
    zr0, zr1 = z0 + 0.10, z0 + H - 0.35
    steps = max(4, int((zr1 - zr0) / 0.60))
    prev = None
    for i in range(steps + 1):
        z = zr0 + (zr1 - zr0) * i / steps
        c = _leg_axis(rec, rk, z - z0) + [0, 0, z]
        d = c[:2] / max(np.linalg.norm(c[:2]), 1e-9)
        p = c + np.array([d[0], d[1], 0.0]) * (r_up + CHS["riser"] * 0.5 + 0.006)
        if prev is not None:
            tube(acc, prev, p, CHS["riser"] * 0.5, CHS["riser"] * 0.5,
                 nu=18, nz=1, **kw)
        prev = p
    for i in range(0, steps + 1, 2):
        z = zr0 + (zr1 - zr0) * i / steps
        c = _leg_axis(rec, rk, z - z0) + [0, 0, z]
        d = c[:2] / max(np.linalg.norm(c[:2]), 1e-9)
        p = c + np.array([d[0], d[1], 0.0]) * (r_up + 0.004)
        torus(acc, p, np.array([d[0], d[1], 0.0]), CHS["riser"] * 0.5 + 0.006,
              0.004, nu=16, nv=9, **kw)

    # ---- the head frame and its spigots ------------------------------------
    zh = z0 + H
    ring_r = rec["w1"] / math.sqrt(3.0) + 0.10
    ax = np.array([0.0, 0.0, 1.0])
    # Two hexagonal tube rings and six verticals -- a FABRICATED frame, not a
    # solid disc. A 0.6 m solid plate at the top of a lattice mast would be
    # heavier than the mast and would read as one.
    hexpt = [np.array([ring_r * math.cos(2.0 * math.pi * i / 6.0),
                       ring_r * math.sin(2.0 * math.pi * i / 6.0), 0.0])
             for i in range(6)]
    for dz in (0.0, 0.30):
        for i in range(6):
            a = hexpt[i] + [0, 0, zh + dz]
            b = hexpt[(i + 1) % 6] + [0, 0, zh + dz]
            tube(acc, a, b, CHS["tie"] * 0.5, CHS["tie"] * 0.5, nu=16, nz=1, **kw)
    for i in range(6):
        a = hexpt[i] + [0, 0, zh]
        tube(acc, a, a + [0, 0, 0.30], CHS["brace"] * 0.5, CHS["brace"] * 0.5,
             nu=16, nz=1, **kw)
        torus(acc, a + [0, 0, 0.014], ax, CHS["brace"] * 0.5 + 0.006, 0.005,
              nu=16, nv=9, weld=1.0, zone=Z_WELD)
    # the three legs die into the lower hex ring
    for k in range(3):
        pk = _leg_axis(rec, k, H) + [0, 0, z0 + H]
        torus(acc, pk + [0, 0, -0.010], ax, r_up + 0.008, 0.0065,
              nu=20, nv=10, weld=1.0, zone=Z_WELD)
        tube(acc, pk, np.array([0.0, 0.0, zh + 0.02]), r_up, r_up * 0.7,
             nu=18, nz=1, **kw)
    for i in range(rec["n_spigot"]):
        a = 2.0 * math.pi * i / rec["n_spigot"] + rec["spigot_yaw"][i]
        d = np.array([math.cos(a), math.sin(a), 0.0])
        p0 = np.array([0.0, 0.0, zh + 0.34]) + d * (ring_r - 0.02)
        p1 = p0 + d * 0.190 + np.array([0.0, 0.0, 0.055])
        tube(acc, p0, p1, CHS["spigot"] * 0.5, CHS["spigot"] * 0.5,
             nu=18, nz=2, **kw)
        torus(acc, p0 + 0.014 * d, d, CHS["spigot"] * 0.5 + 0.006, 0.005,
              nu=16, nv=9, weld=1.0, zone=Z_WELD)
        # the clamp band the luminaire bolts to -- `lighting_mast_head`'s
        # mounting interface, published in interface_json()
        torus(acc, p1 - 0.030 * d, d, CHS["spigot"] * 0.5 + 0.009, 0.008,
              nu=16, nv=9, **kw)

    # ---- the base enclosure, on 5 of 11 ------------------------------------
    if rec["enclosure"]:
        ex, ey, ez = 0.30, 0.185, 0.90
        cx = rec["plinth_hx"] + ex + 0.02
        chamfered_box(acc, cx, 0.0, pr, pr + ez, ex, ey, 0.008,
                      zone=Z_ENCLOSURE)
        # door: a recessed panel with a real reveal, two hinges, a hasp
        chamfered_box(acc, cx + ex - 0.004, 0.0, pr + 0.06, pr + ez - 0.06,
                      0.006, ey - 0.030, 0.003, zone=Z_ENCLOSURE)
        for zz in (pr + 0.14, pr + ez - 0.14):
            tube(acc, [cx + ex, ey - 0.030, zz], [cx + ex + 0.022, ey - 0.030, zz],
                 0.011, 0.011, nu=10, nz=1, zone=Z_ENCLOSURE)
        chamfered_box(acc, cx + ex + 0.006, -ey + 0.055, pr + 0.44, pr + 0.50,
                      0.006, 0.028, 0.002, zone=Z_ENCLOSURE)
        # louvres -- four real slots, each a lipped blade
        for i in range(4):
            zz = pr + 0.20 + i * 0.045
            chamfered_box(acc, cx + ex - 0.002, 0.0, zz, zz + 0.012, 0.004,
                          ey - 0.070, 0.002, zone=Z_ENCLOSURE)
        # the gland plate and the conduit leaving the bottom
        tube(acc, [cx, 0.0, pr + 0.02], [cx, 0.0, pr - 0.05], 0.020, 0.020,
             nu=10, nz=1, zone=Z_ENCLOSURE)

    V, Q, T, A = acc.out()
    return V, Q, T, A


def _ring(centre, axis, R, _unused, nu=24):
    u, v, w, _ = _frame(axis)
    ang = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    return (np.asarray(centre, float)[None, :]
            + (R * np.cos(ang))[:, None] * u[None, :]
            + (R * np.sin(ang))[:, None] * v[None, :])


# ==============================================================================
#  5.  MATERIALS — layered history, and every wavelength placed against octaves()
# ==============================================================================
# LAW 7, "nothing has a history". The wave-1 pattern this must not repeat, across
# six reviews: "not one rust bleed, not one white-rust bloom, not one chip, not
# one paint transfer"; "not one fixing is visible anywhere on the deck" against a
# claim of ~90 screws. The fixings here are real geometry (section 4); this
# section is the history ON them.
#
# AND THE HONEST PART FIRST, because it decides everything below. At the DERIVED
# framing 1 px = 24.66 mm. Placed against `octaves()`:
#
#   feature                       physical      px at 84.18 m   gate band
#   ------------------------------------------------------------------------
#   lattice brace, 48.3 mm OD     48.3 mm       1.96 px         r2   <-- reads
#   leg, 114.3 mm OD             114.3 mm       4.63 px         r4
#   galvanising run / drip        30-70 mm      1.2-2.8 px      r1-r2 <-- reads
#   HD nut, across flats          46 mm         1.87 px         r2
#   plinth chamfer                25 mm         1.01 px         r1
#   ZINC SPANGLE, coarse grain    18 mm         0.73 px         BELOW r1
#   spangle dendrite               4.2 mm       0.17 px         BELOW r1
#   weld bead ripple               7 mm         0.28 px         BELOW r1
#   lattice panel pitch          0.9-1.1 m      36-45 px        ABOVE r16
#
# SO: at the distance the film actually uses, THE FINE-BAND SIGNAL OF THIS ITEM
# IS ITS OWN STRUCTURE. The braces land in r2 and the runs in r1-r2; the spangle,
# the dendrite and the weld ripple are all sub-pixel and contribute as AGGREGATE
# ROUGHNESS AND REFLECTANCE, not as visible pattern.
#
# THE SPANGLE IS STILL BUILT, AT ITS PHYSICAL SIZE, AND IS NOT TUNED TO THE BAND.
# Retuning an 18 mm zinc crystal to 25 mm so it lands in r1 would be R2-1031..37
# run backwards -- authoring the physics to suit the instrument -- and it would
# be a lie the moment anybody looked at the macro. Hot-dip regular spangle is
# 5-25 mm and large spangle reaches ~40 mm; 14-26 mm is drawn per mast, because
# that is what the coating is. It is sub-pixel at 84 m, it is 0.7-3.3 px if this
# item is ever seen at the manifest's (refuted) 25 m, and it is unmistakable in
# the macro. Its ABSENCE was a named wave-1 rejection and its presence is not
# contingent on a threshold.

LAM_SPANGLE = 0.018          # zinc crystal grain, m. Physical. 0.73 px at 84 m.
LAM_DENDRITE = 0.0042        # the arms inside a grain
LAM_RUN = 0.045              # a galvanising run/drip down a member -- r1..r2
LAM_WELD_RIPPLE = 0.007      # the stack of ripples along a fillet bead
LAM_BLAST = 0.0018           # the blasted steel under the coating
LAM_BLOOM = 0.220            # white-rust bloom patches -- a coarse, r8 feature
LAM_STREAK = 0.030           # run-down staining ACROSS the streak;
                             # x7 longer down, via _vmul(1, 1, 0.14). 1.2 px.
LAM_BUG = 0.026              # bug holes / the cast arris on the plinth
LAM_CHIP = 0.030             # paint chips at the enclosure door edge

# Modulation targets. Stated as RADIANCE, per itemkit section 5b; the
# millimetres are derived from the contract sun and never typed.
M_SPANGLE_FACET = 0.34       # isotropic_micro 0.12-0.45
M_SPANGLE_EDGE = 0.42        # the crystal BOUNDARY -- top of the micro band
M_DENDRITE = 0.19            # isotropic_micro
M_RUN = 2.60                 # hard_feature 1.5-6.0
M_WELD_RIPPLE = 2.90         # hard_feature -- a bead IS an edge
M_BLAST = 0.22               # isotropic_micro
M_CONC_AGG = 0.55            # isotropic_macro 0.35-0.95 (exposed aggregate)
M_CONC_CHAMFER = 1.90        # hard_feature (the cast arris and its form marks)
M_PAINT_ORANGE = 0.26        # isotropic_micro (powder-coat orange peel)
M_PAINT_CHIP = 1.85          # hard_feature -- a chip edge is an EDGE


def relief_plan(verbose=True):
    """THE RELIEF BUDGET, both bands, printed. `K.relief_budget` bounds BOTH
    ways -- 0.79 was rejected as a machined cone just as 3.76 was as stucco."""
    micro = [("spangle_facet", LAM_SPANGLE, K.relief_amplitude_for(M_SPANGLE_FACET, LAM_SPANGLE)),
             ("spangle_edge", LAM_SPANGLE, K.relief_amplitude_for(M_SPANGLE_EDGE, LAM_SPANGLE)),
             ("dendrite", LAM_DENDRITE, K.relief_amplitude_for(M_DENDRITE, LAM_DENDRITE)),
             ("blast_micro", LAM_BLAST, K.relief_amplitude_for(M_BLAST, LAM_BLAST)),
             ("paint_orange", 0.0035, K.relief_amplitude_for(M_PAINT_ORANGE, 0.0035))]
    hard = [("galv_run", LAM_RUN, K.relief_amplitude_for(M_RUN, LAM_RUN)),
            ("weld_ripple", LAM_WELD_RIPPLE, K.relief_amplitude_for(M_WELD_RIPPLE, LAM_WELD_RIPPLE)),
            ("conc_chamfer", LAM_BUG, K.relief_amplitude_for(M_CONC_CHAMFER, LAM_BUG)),
            ("paint_chip", LAM_CHIP, K.relief_amplitude_for(M_PAINT_CHIP, LAM_CHIP))]
    macro = [("conc_aggregate", 0.014, K.relief_amplitude_for(M_CONC_AGG, 0.014))]
    if verbose:
        log("relief budget -- sun %.4f deg, amplifier %.3fx (DERIVED, never typed)"
            % (K.sun_elev_deg(), K.sun_amplifier()))
    return {"isotropic_micro": K.relief_budget(micro, band="isotropic_micro",
                                               verbose=verbose),
            "hard_feature": K.relief_budget(hard, band="hard_feature",
                                            verbose=verbose),
            "isotropic_macro": K.relief_budget(macro, band="isotropic_macro",
                                               verbose=verbose)}


def _vmul(t, vec, xyz):
    """NORMALISE THE FACTOR SO max|component| == 1.0, ALWAYS. See below.

    `_vector_gain` returns the LARGEST absolute component ("the FINEST
    direction is the one that sets the slope"), and the emitted wavelength is
    `declared / gain`. So a factor with any component above 1.0 silently makes
    the texture FINER than the wavelength the module declared -- and the bump
    amplitude was computed for the DECLARED one, so the modulation is wrong by
    the same factor.

    THAT IS NOT HYPOTHETICAL, IT IS WHAT THIS FILE DID. The galvanising run
    asked for a 45 mm wavelength through a (5.5, 5.5, 1.0) multiply, and
    therefore EMITTED 8.18 mm at m = 8.58 -- 43 % over the hard_feature ceiling
    -- while every number in this module said 45 mm and m = 2.60. It was
    invisible until the stage was made auditable at all (the CombineXYZ trap
    above), and `relief_audit` found it on the very next run. Anisotropy is
    expressed by SHRINKING the long axis, never by stretching the short one.
    """
    """Anisotropic vector multiply that `itemkit._vector_gain` CAN READ.

    `NT.pin` assumes a 3-tuple is a colour and appends 1.0, which a VECTOR
    socket refuses -- so the obvious workaround is a CombineXYZ node. That
    workaround is a TRAP: `_vector_gain` walks back from a texture's Vector
    socket and can only read a multiply whose factor is a LITERAL, so a
    node-driven factor reads as gain 0 and `_tex_wavelength_m` returns None.
    Three of this module's bump stages came back "no procedural texture found
    upstream of Height" for exactly that reason, i.e. INVISIBLE TO THE RELIEF
    AUDIT -- which is the one instrument that can see a dead stack.

    Setting `default_value` directly is what pin would do without its colour
    special-case, and it keeps the stage auditable.
    """
    xyz = tuple(float(v) for v in xyz)
    if abs(max(abs(v) for v in xyz) - 1.0) > 1e-9:
        raise ValueError(
            "_vmul%s: the largest component must be exactly 1.0, or the "
            "texture emits `declared / %.4f` and every modulation computed "
            "from the declared wavelength is wrong by that factor. Shrink the "
            "long axis instead of stretching the short one."
            % (xyz, max(abs(v) for v in xyz)))
    nd = t.n("ShaderNodeVectorMath", operation="MULTIPLY")
    t.pin(nd, 0, vec)
    nd.inputs[1].default_value = tuple(float(v) for v in xyz)
    return (nd, 0)


def _decorrelated_coords(t):
    """Object coordinates OFFSET BY A PER-MESH SEED.

    Law 6 gives every material `TexCoord -> Object`, which is right and is why
    nothing here blotches at |P| ~ 1000 m -- but it also means eleven masts get
    the IDENTICAL procedural field, in phase. That is the wave-1 pit-wall
    defect verbatim: "one realisation of the concrete ... whatever the shader
    did, it did identically 119 times, in phase." The fix is a per-mesh scalar
    attribute translated into a coordinate offset, so the pattern MOVES rather
    than merely changing tone.
    """
    obj = t.object_coords()
    seed = t.attr("lm_seed", out=2)
    off = t.comb(t.math("MULTIPLY", seed, 137.31),
                 t.math("MULTIPLY", seed, 211.77),
                 t.math("MULTIPLY", seed, 97.13))
    return t.vmath("ADD", obj, off), seed


def mat_galv(name=PFX + "Galv"):
    """Hot-dip galvanised steel: spangle, runs, weld beads, white rust, wear.

    THE STACK, in the order light meets it:
      1. the blasted steel under the coating          isotropic_micro
      2. the zinc SPANGLE -- polygonal crystal grains, each with its own
         reflectance (crystallographic orientation) and its own facet tilt,
         separated by a hard boundary ridge          isotropic_micro
      3. the DENDRITE inside each grain              isotropic_micro
      4. GALVANISING RUNS -- where the zinc drained and froze, on and below
         every downward-facing member                hard_feature
      5. WELD BEAD ripple, masked to the real bead geometry by `lm_weld`
                                                     hard_feature
      6. WHITE RUST bloom where water sits, driven by the world NORMAL (a
         normal is not a position; it does not lose precision at |P| ~ 1000 m
         and Law 6 is about coordinates)
      7. RUN-DOWN STAINING below the fixings
      8. the BASE SCUFF band, 0.25-0.85 m, where things hit it
      9. BRIGHT ZINC on the arrises, via the Bevel-normal edge-wear idiom --
         which `socket_blend_scan` records as a NOTE and must never fail.
    """
    t = K.NT(name)
    P, seed = _decorrelated_coords(t)
    weld = t.attr("lm_weld", out=2)
    hgt = t.attr("lm_h", out=2)
    age = t.attr("lm_age", out=2)

    geo = t.n("ShaderNodeNewGeometry")
    up = t.sep((geo, 1), 2)                       # world normal z: 1 up, -1 down
    upness = t.maprange(up, 0.15, 0.85, 0.0, 1.0)
    downness = t.maprange(up, -0.75, -0.15, 1.0, 0.0)

    # --- 1. the blasted steel --------------------------------------------
    blast = t.noise(P, wavelength_m=LAM_BLAST, detail=6.0, rough=0.62)

    # --- 2. the spangle ---------------------------------------------------
    # DISTANCE_TO_EDGE is literally the crystal boundary; F1's Color output is
    # a per-cell constant, which is what a per-grain crystallographic
    # orientation looks like to the light.
    lam_sp = t.fmix(age, LAM_SPANGLE * 1.44, LAM_SPANGLE * 0.78)
    sp_edge = t.vor(P, wavelength_m=LAM_SPANGLE, feature="DISTANCE_TO_EDGE")
    sp_cell = t.vor(P, wavelength_m=LAM_SPANGLE, feature="F1", out=1)
    sp_ridge = t.ramp(sp_edge, [(0.00, (1.0, 1.0, 1.0)), (0.09, (0.35, 0.35, 0.35)),
                                (0.30, (0.0, 0.0, 0.0))])
    sp_facet = t.sep(sp_cell, 0)

    # --- 3. the dendrite inside the grain ---------------------------------
    dend = t.vor(_vmul(t, P, (1.0, 1.0, 0.38)),
                 wavelength_m=LAM_DENDRITE, feature="F1")

    # --- 4. galvanising runs, only where zinc could drain -----------------
    run_f = t.wave(_vmul(t, P, (1.0, 1.0, 0.16)),
                   wavelength_m=LAM_RUN, direction="X", distortion=2.4,
                   detail=3.0)
    run = t.math("MULTIPLY", run_f, downness)

    # --- 5. the weld bead ripple ------------------------------------------
    ripple_f = t.wave(P, wavelength_m=LAM_WELD_RIPPLE, direction="X",
                      distortion=1.1, detail=2.0)
    ripple = t.math("MULTIPLY", ripple_f, weld)

    # --- 6. white rust, 7. staining, 8. scuff -----------------------------
    bloom_n = t.noise(P, wavelength_m=LAM_BLOOM, detail=4.0, rough=0.5)
    bloom = t.math("MULTIPLY", t.math("MULTIPLY", bloom_n, upness), age,
                   clamp=True)
    streak = t.noise(_vmul(t, P, (1.0, 1.0, 0.14)),
                     wavelength_m=LAM_STREAK, detail=5.0, rough=0.6)
    stain = t.math("MULTIPLY", t.math("MULTIPLY", streak, age), downness,
                   clamp=True)
    scuff = t.math("MULTIPLY",
                   t.maprange(hgt, 0.85, 0.25, 0.0, 1.0),
                   t.noise(_vmul(t, P, (1.0, 1.0, 0.33)),
                           wavelength_m=0.035, detail=4.0), clamp=True)

    # --- 9. bright zinc on the arrises. THE EDGE-WEAR IDIOM. --------------
    # A Bevel normal dotted with the geometry normal: 1.0 on a flat face, < 1
    # on a convex arris. `socket_blend_scan` records this as a NOTE and it must
    # never be failed -- it is the idiom `armco_w_beam` carries.
    bev = t.n("ShaderNodeBevel")
    bev.samples = 8
    t.pin_named(bev, "Radius", 0.004)
    edge = t.maprange(t.vmath("DOT_PRODUCT", bev, (geo, 1)), 0.86, 1.0, 1.0, 0.0)

    # ---------------- COLOUR ---------------------------------------------
    ZINC = K.srgb_linear("#9aa0a4")
    ZINC_D = K.srgb_linear("#6f767b")
    ZINC_BR = K.srgb_linear("#c8ced2")
    WHITE_R = K.srgb_linear("#d8dad4")
    STAINC = K.srgb_linear("#5c5a52")
    base = t.cmix(t.fmix(age, 0.25, 0.80), ZINC, ZINC_D)
    base = t.cmix(t.math("MULTIPLY", sp_facet, 0.45), base, ZINC_BR)
    base = t.cmix(t.math("MULTIPLY", sp_ridge, 0.30), base, ZINC_D)
    base = t.cmix(t.math("MULTIPLY", bloom, 0.85), base, WHITE_R)
    base = t.cmix(t.math("MULTIPLY", stain, 0.55), base, STAINC)
    base = t.cmix(t.math("MULTIPLY", scuff, 0.60), base, ZINC_BR)
    base = t.cmix(t.math("MULTIPLY", edge, 0.70), base, ZINC_BR)

    rough = t.fmix(age, 0.34, 0.58)
    rough = t.fmix(t.math("MULTIPLY", bloom, 0.9), rough, 0.88)
    rough = t.fmix(t.math("MULTIPLY", sp_facet, 0.5), rough, 0.28)
    rough = t.fmix(t.math("MULTIPLY", edge, 0.8), rough, 0.19)
    rough = t.fmix(t.math("MULTIPLY", run, 0.5), rough, 0.30)

    # ---------------- RELIEF, CHAINED, WIRED BY NAME ----------------------
    # Blender 5.2 moved Principled's `Normal` from index 5 to 6 and moved
    # `Filter Width` into Bump index 2; `NT.bump` and `principled_out` both wire
    # by NAME. Nothing in this file pins a shading socket by index.
    n1 = t.bump(blast, 1.0, modulation_pp=M_BLAST, wavelength_m=LAM_BLAST,
                height_pp=0.60)
    n2 = t.bump(sp_facet, 1.0, modulation_pp=M_SPANGLE_FACET,
                wavelength_m=LAM_SPANGLE, height_pp=1.0, normal=n1)
    n3 = t.bump(sp_ridge, 1.0, modulation_pp=M_SPANGLE_EDGE,
                wavelength_m=LAM_SPANGLE, height_pp=1.0, normal=n2)
    n4 = t.bump(dend, 1.0, modulation_pp=M_DENDRITE, wavelength_m=LAM_DENDRITE,
                height_pp=0.60, normal=n3)
    n5 = t.bump(run, 1.0, modulation_pp=M_RUN, wavelength_m=LAM_RUN,
                height_pp=0.55, normal=n4)
    n6 = t.bump(ripple, 1.0, modulation_pp=M_WELD_RIPPLE,
                wavelength_m=LAM_WELD_RIPPLE, height_pp=0.55, normal=n5)

    t.principled_out(base_color=base, roughness=rough, metallic=0.86,
                     normal=n6)
    return t.m


def mat_conc(name=PFX + "Conc"):
    """The cast plinth: aggregate, form-board grain, a chamfer that catches the
    sun, bug holes, and the water line every kerbside plinth grows."""
    t = K.NT(name)
    P, seed = _decorrelated_coords(t)
    hgt = t.attr("lm_h", out=2)
    age = t.attr("lm_age", out=2)
    geo = t.n("ShaderNodeNewGeometry")
    up = t.sep((geo, 1), 2)
    upness = t.maprange(up, 0.2, 0.9, 0.0, 1.0)

    agg = t.noise(P, wavelength_m=0.014, detail=7.0, rough=0.58)
    bug = t.vor(P, wavelength_m=LAM_BUG, feature="F1")
    bugm = t.ramp(bug, [(0.0, (1, 1, 1)), (0.16, (0, 0, 0))])
    board = t.wave(P, wavelength_m=0.150, direction="Z", distortion=0.7,
                   detail=2.0)
    grime = t.noise(_vmul(t, P, (1.0, 1.0, 0.125)),
                    wavelength_m=0.090, detail=5.0)
    water = t.math("MULTIPLY", t.maprange(hgt, 0.02, 0.16, 1.0, 0.0), grime,
                   clamp=True)

    CONC = K.srgb_linear("#a9a49b")
    CONC_D = K.srgb_linear("#7d7970")
    CONC_W = K.srgb_linear("#5f5c55")
    base = t.cmix(t.math("MULTIPLY", agg, 0.55), CONC, CONC_D)
    base = t.cmix(t.math("MULTIPLY", bugm, 0.8), base, CONC_W)
    base = t.cmix(t.math("MULTIPLY", water, 0.7), base, CONC_W)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", upness, age), 0.35),
                  base, CONC_D)
    rough = t.fmix(agg, 0.72, 0.93)

    n1 = t.bump(agg, 1.0, modulation_pp=M_CONC_AGG, wavelength_m=0.014,
                height_pp=0.60)
    n2 = t.bump(bugm, 1.0, modulation_pp=M_CONC_CHAMFER, wavelength_m=LAM_BUG,
                height_pp=1.0, normal=n1)
    n3 = t.bump(board, 1.0, modulation_pp=0.62, wavelength_m=0.150,
                height_pp=0.80, normal=n2)
    t.principled_out(base_color=base, roughness=rough, metallic=0.0, normal=n3)
    return t.m


def mat_cabinet(name=PFX + "Cabinet"):
    """The base enclosure: powder coat over galvanising, chalked by the sun,
    chipped at the door edge down to bright zinc, with an invented brand's
    colour on the door. Law 2 -- the brand comes from the ONE book."""
    t = K.NT(name)
    P, seed = _decorrelated_coords(t)
    age = t.attr("lm_age", out=2)
    geo = t.n("ShaderNodeNewGeometry")

    b = K.pick_brand(SEED, 77)
    PAINT = K.srgb_linear(b[1])
    ZINC_BR = K.srgb_linear("#c8ced2")
    CHALK = K.srgb_linear("#c9ccc8")

    peel = t.noise(P, wavelength_m=0.0035, detail=6.0, rough=0.55)
    chip = t.vor(P, wavelength_m=LAM_CHIP, feature="F1")
    chipm = t.ramp(chip, [(0.0, (1, 1, 1)), (0.10, (0, 0, 0))])
    chalk = t.noise(P, wavelength_m=0.180, detail=4.0)
    bev = t.n("ShaderNodeBevel")
    bev.samples = 6
    t.pin_named(bev, "Radius", 0.003)
    edge = t.maprange(t.vmath("DOT_PRODUCT", bev, (geo, 1)), 0.85, 1.0, 1.0, 0.0)

    base = t.cmix(t.math("MULTIPLY", chalk, t.math("MULTIPLY", age, 0.55)),
                  PAINT, CHALK)
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", chipm, age), 0.9),
                  base, ZINC_BR)
    base = t.cmix(t.math("MULTIPLY", edge, 0.75), base, ZINC_BR)
    rough = t.fmix(peel, 0.36, 0.55)
    rough = t.fmix(t.math("MULTIPLY", chalk, age), rough, 0.80)

    n1 = t.bump(peel, 1.0, modulation_pp=M_PAINT_ORANGE, wavelength_m=0.0035,
                height_pp=0.60)
    n2 = t.bump(chipm, 1.0, modulation_pp=M_PAINT_CHIP, wavelength_m=LAM_CHIP,
                height_pp=1.0, normal=n1)
    t.principled_out(base_color=base, roughness=rough, metallic=0.25, normal=n2)
    return t.m


def materials():
    return {"galv": mat_galv(), "conc": mat_conc(), "cab": mat_cabinet()}


# ==============================================================================
#  6.  EMISSION — meshes, attributes, material slots, and the instancer
# ==============================================================================

_MAT_ORDER = ("galv", "conc", "cab")
_ZONE_SLOT = {Z_STEEL: 0, Z_WELD: 0, Z_CONCRETE: 1, Z_ENCLOSURE: 2}


def build_mast_object(rec, coll_, mats):
    """One mast as a real object, recentred on emit, seated on the contract."""
    V, Q, T, A = build_mast_arrays(rec)
    name = "%sMast%02d_H%04.1f" % (SPFX, rec["uid"], rec["height_m"])

    # per-vertex fields the materials read. `lm_h` is height above the mast's
    # own base and survives `new_mesh`'s recentring, which a raw object-space z
    # would not; `lm_seed` is what decorrelates eleven copies of one procedural.
    zmin = float(V[:, 2].min())
    A = dict(A)
    A["lm_h"] = (V[:, 2] - zmin).astype(np.float64)
    A["lm_age"] = np.full(len(V), float(rec["age"]))
    A["lm_seed"] = np.full(len(V), float(h(rec["uid"], 99)))

    me, off = K.new_mesh(name, V, quads=Q, tris=T, smooth_deg=33.0)
    base_local_z = float(V[:, 2].min() - off[2])      # negative after recentring
    K.bake_attributes(me, A)

    for k in _MAT_ORDER:
        me.materials.append(mats[k])
    # polygon -> slot, from the zone of the polygon's first corner. Quads come
    # first out of `Acc`, then tris, which is the order `new_mesh` builds them.
    zone = A["lm_zone"]
    first = np.concatenate([Q[:, 0] if len(Q) else np.zeros(0, np.int64),
                            T[:, 0] if len(T) else np.zeros(0, np.int64)])
    idx = np.array([_ZONE_SLOT.get(float(z), 0) for z in zone[first]], np.int32)
    if len(idx) == len(me.polygons):
        me.polygons.foreach_set("material_index", idx)
    else:                                            # never silently mis-assign
        raise RuntimeError("REFUSING: %d material indices for %d polygons"
                           % (len(idx), len(me.polygons)))

    ob = bpy.data.objects.new(name, me)
    ob.location = off
    coll_.objects.link(ob)
    return ob, np.asarray(off, float), {"verts": len(V),
                                        "triangles": len(Q) * 2 + len(T),
                                        "base_local_z": base_local_z}


def station_world(rec):
    """The mast's ORIGIN in world metres. Law 5 and Law 9 in one place.

    The station is circuit-frame and goes through `world_contract.circuit_to_world`
    -- a 40 deg rotation about a pivot, NOT an offset. Reading the manifest's
    "circuit x -480..+100" as world x is wrong by hundreds of metres.
    """
    sx, sy = rec["station"]
    wx, wy = C.circuit_to_world(float(sx), float(sy))
    return float(wx), float(wy)


def build(scene=None, instanced=True, limit=None, stats=None):
    """Emit the eleven masts.

    instanced=True (default, and what ships): one real carrier object carrying a
    Geometry Nodes tree that instances the other ten AT THEIR OWN STATIONS from
    ten DISTINCT meshes, so `depsgraph.object_instances` -- which is what
    `item_gate.realized_instances` walks -- sees a realized population. See
    section 5 for why this and not eleven plain objects.
    """
    t0 = time.time()
    purge()
    root = K.coll(COLL)
    src = _coll_unlinked(SRC_COLL)
    mats = materials()
    recs = records()
    if limit:
        recs = recs[:limit]

    built, tot = [], dict(objects=0, verts=0, triangles=0)
    for r in recs:
        ob, off, info = build_mast_object(r, src, mats)
        wx, wy = station_world(r)
        # Law 9: NEVER an assumed z. `seat_on_ground` goes through
        # `world_contract.world_ground_z` and RAISES where terrain owns the
        # ground rather than inventing a height. `base_local_z` is the mesh's
        # own lowest point AFTER `new_mesh` recentred it, which is what the
        # helper's docstring asks for and is negative.
        #
        # EMBED 0.100, NOT THE CONTRACT FLOOR OF 0.020, and it is a stated
        # choice not a stray literal: the lowest point of this mesh is the
        # BOTTOM OF A CAST CONCRETE PLINTH, which is buried. Embedding only
        # 20 mm would stand the plinth 80 mm higher than it was drawn.
        # `seat_on_ground` refuses anything SHALLOWER than BASE_EMBED_M; deeper
        # is allowed and this says why.
        zorigin = K.seat_on_ground(wx, wy, base_local_z=info["base_local_z"],
                                   embed_m=0.100)
        ob.location = (wx, wy, zorigin)
        built.append((r, ob, np.array([wx, wy, zorigin]), info))
        tot["objects"] += 1
        tot["verts"] += info["verts"]
        tot["triangles"] += info["triangles"]
        log("mast %02d  circuit %8.1f %6.1f  H %5.2f m  nnode %2d  spl %d  "
            "enc %d  spig %d  %7d tris"
            % (r["uid"], r["station"][0], r["station"][1], r["height_m"],
               r["nnode"], r["n_splice"], int(r["enclosure"]), r["n_spigot"],
               info["triangles"]))

    ci = _carrier_index(built)
    if instanced and len(built) > 1:
        rc, carrier, Oc, _ = built[ci]
        src.objects.unlink(carrier)
        root.objects.link(carrier)
        carrier.name = "%sMast%02d_H%04.1f" % (PFX, rc["uid"], rc["height_m"])
        others = [(ob, O) for (r, ob, O, _) in built if r["uid"] != rc["uid"]]
        bpy.context.view_layer.update()
        _instancer(carrier, others, Oc)
        verify_instances(carrier, {ob.data.name: O for (ob, O) in others})
    else:
        for (r, ob, O, _) in built:
            src.objects.unlink(ob)
            root.objects.link(ob)
            ob.name = "%sMast%02d_H%04.1f" % (PFX, r["uid"], r["height_m"])
        bpy.context.view_layer.update()

    tot["seconds"] = round(time.time() - t0, 1)
    if stats is not None:
        stats.update(tot)
    log("built %d masts, %d triangles in %.1f s"
        % (tot["objects"], tot["triangles"], tot["seconds"]))
    return root


def _carrier_index(built):
    """The mast the gate will frame and judge.

    `item_gate.pick_subject` takes the MEDIAN-triangle object of the item, and
    with one carrier that is the carrier -- so the carrier IS the choice of
    subject and it must be the TYPICAL mast, not the best one. So: the median
    of the eleven by triangle count, which lands on a mid height class.
    """
    order = sorted(range(len(built)), key=lambda i: built[i][3]["triangles"])
    return order[len(order) // 2]


def _coll_unlinked(name):
    """A collection deliberately NOT linked into the scene.

    The ten source meshes must exist as objects (Geometry Nodes' Object Info
    references objects, not meshes) and must NOT be selectable by the gate: if
    they were, `instance_variation` would count eleven loose objects, the
    realized-instance branch would never run, and `per_instance_variation`
    would be graded on the WEAK path -- `cv_size >= 0.03` and
    `distinct_topologies >= 2`, with no cap on the commonest source at all.
    """
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    return c


def _instancer(carrier, others, Oc):
    """Object Info -> Transform -> Join, ten times. Explicit and deterministic.

    Transform Space is ORIGINAL, so the source object's own transform is
    ignored and the instance lands at `carrier.matrix_world @ Translation`.
    `Oc` is PASSED IN rather than read off `carrier.matrix_world`, because a
    freshly linked object's world matrix is the identity until the depsgraph
    updates -- `matrix_world` is not evaluated for hidden objects and is stale
    for fresh ones, which is Law 10.
    """
    ng = bpy.data.node_groups.new(PFX + "Field", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gin = ng.nodes.new("NodeGroupInput")
    gout = ng.nodes.new("NodeGroupOutput")
    join = ng.nodes.new("GeometryNodeJoinGeometry")
    ng.links.new(gin.outputs[0], join.inputs[0])
    Oc = np.asarray(Oc, float)
    for i, (ob, O) in enumerate(others):
        oi = ng.nodes.new("GeometryNodeObjectInfo")
        oi.transform_space = "ORIGINAL"
        oi.inputs["Object"].default_value = ob
        oi.inputs["As Instance"].default_value = True
        oi.location = (-520, -180 * i)
        tr = ng.nodes.new("GeometryNodeTransform")
        tr.location = (-270, -180 * i)
        ng.links.new(oi.outputs["Geometry"], tr.inputs["Geometry"])
        d = np.asarray(O, float) - Oc
        tr.inputs["Translation"].default_value = (float(d[0]), float(d[1]),
                                                  float(d[2]))
        ng.links.new(tr.outputs["Geometry"], join.inputs[0])
    ng.links.new(join.outputs[0], gout.inputs[0])
    md = carrier.modifiers.new(PFX + "Field", "NODES")
    md.node_group = ng
    return ng


def verify_instances(carrier, want):
    """MEASURE what the depsgraph realizes. R2-018/019: an UNPROVEN instance
    population is a FAIL, not a skip, and a PASS emitted on something never
    measured is the defect this exists to make impossible."""
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    seen, shapes = {}, set()
    for inst in deps.object_instances:
        if not inst.is_instance or inst.parent is None:
            continue
        if inst.parent.name != carrier.name:
            continue
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        seen[ob.data.name] = np.array(inst.matrix_world.translation)
        shapes.add((len(ob.data.vertices), len(ob.data.polygons)))
    bad = []
    for k, O in want.items():
        if k not in seen:
            bad.append("%s was never realized" % k)
        elif not np.allclose(seen[k], O, atol=1e-4):
            bad.append("%s landed at %s, wanted %s"
                       % (k, np.round(seen[k], 4), np.round(O, 4)))
    if len(seen) != len(want):
        bad.append("%d realized from %d wanted" % (len(seen), len(want)))
    if bad:
        raise RuntimeError("REFUSING: instancing is wrong: " + "; ".join(bad[:5]))
    log("instances verified: %d realized, %d distinct source meshes, "
        "%d distinct (verts, polys) fingerprints, commonest share %.4f, "
        "max |dO| < 0.1 mm"
        % (len(seen), len(set(seen)), len(shapes), 1.0 / max(len(seen), 1)))
    return seen


def purge():
    return K.purge(PFX, COLL), K.purge(SPFX, SRC_COLL)


# ==============================================================================
#  7.  THE TEST SCENE AND THE MACRO
# ==============================================================================

def _strip_factory_startup():
    """Delete Blender's default Cube / Camera / Light from the TEST scene only.

    `--factory-startup` is not an empty scene and this project has been bitten
    by that twice: `itemkit.emitted_wavelength_m` refuses to run unless its
    scene is exactly its own plane and camera, because the default Cube once
    sat between an ortho camera and a measurement plane and returned one
    identical number for fourteen stages. Here the Cube shows up in
    `placement_gate` as a context finding 0.602 m inside the CAR'S PATH, which
    is noise in a report whose whole job is to be read.

    Scoped to `test_scene` and to the three factory names, and it checks the
    Cube really is the 8-vertex factory cube before removing it -- `build()`
    may be called into the film scene and must delete nothing it does not own.
    """
    for nm in ("Cube", "Camera", "Light"):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        if ob.type == "MESH" and len(ob.data.vertices) != 8:
            continue
        bpy.data.objects.remove(ob, do_unlink=True)


def test_scene(samples=256, limit=None, stats=None):
    """Build, light to the contract, ground, and stage the 4K macro."""
    scene = bpy.context.scene
    _strip_factory_startup()
    root = build(scene=scene, stats=stats, limit=limit)
    cams = K.coll(COLL + "/Cameras", root)
    stand = K.coll(COLL + "/Standins", root)
    K.contract_sun(PFX, scene=scene, coll_=root)

    carrier = _carrier(root)
    bpy.context.view_layer.update()
    # `matrix_world` is stale for a fresh object (Law 10); `matrix_basis` is not.
    O = np.array(carrier.matrix_basis.translation)
    # `fill_z` is a STATED choice, not an invented height: a 70 m WORLD-aligned
    # square around a station cannot stay inside the paddock rectangle, which is
    # axis-aligned in the CIRCUIT frame 40 deg away, so part of it falls where
    # `world_ground_z` returns NaN because terrain owns the ground. The declared
    # platform there is `APRON_Z`, and this plane is a Standin the gate excludes
    # from every measurement -- it exists to catch a contact shadow.
    K.ground_plane(PFX, stand, centre=(O[0], O[1]), span=70.0, res=160,
                   fill_z=C.APRON_Z)

    # ---- THE MACRO. 3840 x 2160, and the distance is ASSERTED. -----------
    # `macro_rig` refuses any other resolution without a keyword named on
    # purpose (R2-020: 11 of 28 wave-1 heroes shipped 1080p and were scored as
    # 4K), and refuses a camera that is not standing where it says it is.
    dims = np.array(carrier.dimensions)
    aim = O + np.array([0.0, 0.0, 0.5 * dims[2]])
    # the gate's own view geometry: 35 deg up, 40 deg past perpendicular, so
    # the raking light runs ACROSS the lattice rather than along it.
    th = math.radians(35.0)
    az = math.radians(130.0)
    d = np.array([math.cos(th) * math.cos(az), math.cos(th) * math.sin(az),
                  math.sin(th)])
    loc = aim + d * FILMED_AT_M
    cam, dist, ppm = K.macro_rig(PFX + "CAM_MACRO_4K", tuple(loc), tuple(aim),
                                 LENS_MM, cams, scene=scene, samples=samples,
                                 want_distance_m=FILMED_AT_M)
    K.assert_no_external_assets()
    log("macro: %.3f m, %.1f mm, %.2f px/m, %.3f mm/px; the mast is %.0f px of "
        "%d" % (dist, LENS_MM, ppm, 1000.0 / ppm, dims[2] * ppm, K.RES_Y_4K))
    return root


def _carrier(root=None):
    root = root or bpy.data.collections.get(COLL)
    for ob in root.objects:
        if ob.type == "MESH" and ob.name.startswith(PFX):
            return ob
    raise RuntimeError("REFUSING: no carrier object in %s" % COLL)


# ==============================================================================
#  8.  THE PUBLIC INTERFACE — what `lighting_mast_head` may rely on
# ==============================================================================

def mount_stations():
    """Every luminaire spigot, in the MAST'S OWN LOCAL FRAME, metres.

    `lighting_mast_head` (55 instances, 11 masts x 3-6 heads) cannot ask this
    module questions at build time, so the spigot geometry is written down:
    an outer diameter, a length, a clamp-band station and a yaw. If it is not
    published it will be re-derived and it will drift.
    """
    out = []
    for r in records():
        H = r["height_m"]
        ring_r = r["w1"] / math.sqrt(3.0) + 0.10
        zh = 0.032 + 0.028 + r["plinth_proud"] + H
        rows = []
        for i in range(r["n_spigot"]):
            a = 2.0 * math.pi * i / r["n_spigot"] + r["spigot_yaw"][i]
            rows.append({"index": i, "yaw_rad": a,
                         "root_local": [math.cos(a) * (ring_r - 0.02),
                                        math.sin(a) * (ring_r - 0.02),
                                        zh + 0.34],
                         "axis": [math.cos(a) * 0.960, math.sin(a) * 0.960,
                                  0.277],
                         "length_m": 0.198, "od_m": CHS["spigot"],
                         "clamp_band_from_tip_m": 0.030})
        out.append({"uid": r["uid"], "station_circuit": list(r["station"]),
                    "station_world": list(station_world(r)),
                    "height_m": H, "n_spigot": r["n_spigot"], "spigots": rows})
    return out


def interface_json(path=None):
    path = path or os.path.join(_HERE, "%s_interface.json" % ITEM)
    fr = None
    try:
        fr = derive_framing(verbose=False)
    except Exception as e:                                   # noqa: BLE001
        fr = {"error": str(e)}
    return K.interface_json(
        ITEM, path=path,
        version=__version__,
        collection=COLL, prefix=PFX, source_prefix=SPFX,
        instances=INSTANCES_DECLARED,
        stations_circuit=[list(s) for s in STATIONS],
        stations_world=[list(station_world(r)) for r in records()],
        stations_rejected_by_free=[list(s) for s in STATIONS_REJECTED],
        stations_authority=("world/build_architecture.py:3349-3355 offers 20 "
                            "sites; _free(x, y, 1.2) accepts exactly these 11"),
        height_classes_m=list(HEIGHT_CLASSES),
        height_classes_authority="world/build_architecture.py::_lightmast",
        heights_m=[r["height_m"] for r in records()],
        framing_DERIVED={"filmed_at_m": FILMED_AT_M, "lens_mm": LENS_MM,
                         "onscreen_px_4k": ONSCREEN_PX_4K,
                         "frame": FILMED_FRAME,
                         "station_circuit": list(FILMED_STATION),
                         "px_per_m": PX_PER_M, "mm_per_px": MM_PER_PX,
                         "camera": "render/film17_path.json (docs/LIVE-CAMERA.md)",
                         "derivation": fr},
        framing_MANIFEST={"nearest_camera_m": MANIFEST_NEAREST_M,
                          "onscreen_px_4k": MANIFEST_PX_4K,
                          "hero": MANIFEST_HERO,
                          "typical_height_m": MANIFEST_HEIGHT_M,
                          "status": "NOT REPRODUCIBLE from the live camera for "
                                    "any authored station; see R2-1362"},
        framing_SWEEP={"peak_unocc_sharp_px_4k": SWEEP_PEAK_UNOCC_SHARP_PX,
                       "peak_frame": SWEEP_PEAK_FRAME,
                       "status": "HOST upper bound, host_tier ZONE, measured "
                                 "against film16; see R2-1361"},
        octaves=octaves(),
        relief_bands=K.RELIEF_BANDS,
        materials={"steel": PFX + "Galv", "concrete": PFX + "Conc",
                   "enclosure": PFX + "Cabinet"},
        mount_stations=mount_stations(),
        variation_axes=list(MANIFEST_VARIATION_AXES),
        supersedes=("world/build_architecture.py::_lightmast -- a tapered "
                    "cylinder r 0.16 -> 0.10 m. At the derived framing that is "
                    "a solid 13 px bar; this is an open lattice of 2-5 px "
                    "members. The SILHOUETTE is the change."),
    )


# ==============================================================================
#  9.  CENSUS AND SELFTEST — measured, not asserted
# ==============================================================================

def census(verbose=True):
    """What the eleven actually are. Printed so a reader can check the claims in
    section 5 rather than believe them."""
    recs = records()
    rows = []
    for r in recs:
        V, Q, T, A = build_mast_arrays(r)
        d = V.max(axis=0) - V.min(axis=0)
        rows.append({"uid": r["uid"], "height_m": r["height_m"],
                     "verts": len(V), "tris": len(Q) * 2 + len(T),
                     "bbox": [round(float(x), 3) for x in d],
                     "nnode": r["nnode"], "enclosure": r["enclosure"],
                     "n_spigot": r["n_spigot"]})
        if verbose:
            log("uid %2d  H %5.2f  nnode %2d  enc %d  spig %d  %7d tris  "
                "bbox %6.3f x %6.3f x %6.3f"
                % (r["uid"], r["height_m"], r["nnode"], int(r["enclosure"]),
                   r["n_spigot"], rows[-1]["tris"], d[0], d[1], d[2]))
    sig = {(x["verts"], x["tris"]) for x in rows}
    if verbose:
        log("%d masts, %d distinct (verts, tris) fingerprints, commonest "
            "share %.4f, total %d tris"
            % (len(rows), len(sig), 1.0 / len(rows) if len(sig) == len(rows)
               else float("nan"), sum(x["tris"] for x in rows)))
    return {"rows": rows, "distinct_fingerprints": len(sig),
            "total_tris": sum(x["tris"] for x in rows)}


def selftest(verbose=True):
    ok, fail = [], []

    def chk(name, good, detail):
        (ok if good else fail).append(name)
        if verbose:
            print("  %-34s %s %s" % (name, "PASS" if good else "FAIL", detail))

    # [F] the framing is the LIVE camera's, and the constants have not drifted
    try:
        fr = derive_framing(verbose=False)
        b = fr["best_exterior"]
        d_ok = abs(b["distance_m"] - FILMED_AT_M) < 0.05
        l_ok = abs(b["lens_mm"] - LENS_MM) < 1e-6
        p_ok = abs(b["px_4k"] - ONSCREEN_PX_4K) < 1.0
        f_ok = b["frame"] == FILMED_FRAME
        chk("F_framing_is_the_live_camera", d_ok and l_ok and p_ok and f_ok,
            "%.3f m / %.1f mm / %.0f px at f%d from %s (constants %.3f / %.1f "
            "/ %.0f / f%d); %d exterior frames >= 300 px"
            % (b["distance_m"], b["lens_mm"], b["px_4k"], b["frame"],
               os.path.basename(fr["camera"]), FILMED_AT_M, LENS_MM,
               ONSCREEN_PX_4K, FILMED_FRAME, fr["counts"]["exterior_300px"]))
        chk("F_manifest_is_refuted",
            abs(b["px_4k"] - MANIFEST_PX_4K) > 100.0,
            "manifest %.0f px, sweep %.0f px, MEASURED %.0f px -- the sweep "
            "overstates by %.2fx and the manifest by %.2fx"
            % (MANIFEST_PX_4K, SWEEP_PEAK_UNOCC_SHARP_PX, b["px_4k"],
               SWEEP_PEAK_UNOCC_SHARP_PX / b["px_4k"],
               MANIFEST_PX_4K / b["px_4k"]))
    except Exception as e:                                   # noqa: BLE001
        chk("F_framing_is_the_live_camera", False, "RAISED: %r" % (e,))

    # [S] the stations are the world's, not this module's
    chk("S_eleven_authored_stations",
        len(STATIONS) == INSTANCES_DECLARED == 11
        and len(set(STATIONS)) == 11
        and not (set(STATIONS) & set(STATIONS_REJECTED)),
        "11 accepted, %d rejected, no overlap; the accepted set is "
        "build_architecture's _free() output" % len(STATIONS_REJECTED))

    # [P] every station is inside the declared paddock rectangle
    px0, px1, py0, py1 = C.APRON_REGIONS_CIRCUIT["paddock"]
    inside = all(px0 <= sx <= px1 and py0 <= sy <= py1 for (sx, sy) in STATIONS)
    chk("P_stations_inside_the_paddock", inside,
        "APRON_REGIONS_CIRCUIT['paddock'] = x %.1f..%.1f y %.1f..%.1f"
        % (px0, px1, py0, py1))

    # [G] the ground is the contract's and no station lands on terrain
    zs, owners = [], set()
    try:
        for r in records():
            wx, wy = station_world(r)
            zs.append(K.ground_z(wx, wy))
            owners.add(K.ground_owner(wx, wy))
        chk("G_ground_is_the_contract", True,
            "z %.4f..%.4f m, owners %s -- no assumed z, no NaN"
            % (min(zs), max(zs), sorted(str(o) for o in owners)))
    except Exception as e:                                   # noqa: BLE001
        chk("G_ground_is_the_contract", False, "RAISED: %r" % (e,))

    # [R] the relief budget is inside its bands, on BOTH sides
    plan = relief_plan(verbose=False)
    bad = [r["name"] for rows in plan.values() for r in rows
           if r["verdict"] != "ok"]
    chk("R_relief_inside_its_bands", not bad,
        "%d stages, %d outside: %s; amplifier %.3fx DERIVED from "
        "SUN_ELEV_DEG %.5f"
        % (sum(len(v) for v in plan.values()), len(bad), bad or "none",
           K.sun_amplifier(), K.sun_elev_deg()))

    # [R2] and the bands are BOUNDED BOTH WAYS -- the check can fail
    lo = K.modulation_for_amplitude(0.001, LAM_SPANGLE)
    hi = K.modulation_for_amplitude(3.0, LAM_SPANGLE)
    ctl = K.relief_budget([("too_little", LAM_SPANGLE, 0.001),
                           ("too_much", LAM_SPANGLE, 3.0)],
                          band="isotropic_micro", verbose=False)
    chk("R2_control_the_band_rejects_both_ends",
        ctl[0]["verdict"] == "LOW" and ctl[1]["verdict"] == "HIGH",
        "0.001 mm -> m %.4f LOW, 3.000 mm -> m %.3f HIGH at an %.1f mm "
        "wavelength" % (lo, hi, LAM_SPANGLE * 1000.0))

    # [O] every declared wavelength is placed against the resolvable band
    oc = octaves()
    r1 = oc["bands"][0]["wavelength_m"]
    r16 = oc["bands"][4]["wavelength_m"]
    lams = {"spangle": LAM_SPANGLE, "dendrite": LAM_DENDRITE, "run": LAM_RUN,
            "weld_ripple": LAM_WELD_RIPPLE, "blast": LAM_BLAST,
            "bloom": LAM_BLOOM, "streak": LAM_STREAK}
    below = sorted(k for k, v in lams.items() if v < r1)
    inband = sorted(k for k, v in lams.items() if r1 <= v <= r16)
    chk("O_octaves_are_stated_not_assumed", True,
        "1 px = %.2f mm at %.2f m/%.0f mm. IN the r1..r16 band: %s. BELOW r1 "
        "(sub-pixel, contributes as aggregate roughness, NOT retuned to suit "
        "the instrument): %s"
        % (oc["mm_per_px"], FILMED_AT_M, LENS_MM, inband, below))

    # [V] eleven distinct meshes, and the fingerprints really are distinct
    cs = census(verbose=False)
    chk("V_eleven_distinct_shapes",
        cs["distinct_fingerprints"] == INSTANCES_DECLARED,
        "%d masts -> %d distinct (verts, tris) fingerprints, commonest share "
        "%.4f (gate floor: 8 sources / 8 shapes / <= 0.25); %d tris total"
        % (INSTANCES_DECLARED, cs["distinct_fingerprints"],
           1.0 / INSTANCES_DECLARED, cs["total_tris"]))

    # [B] no station may sit under the beat-6 hold sightline window
    # circuit_spec.md sec 10.6: the ray crosses y = +40.5 at circuit x ~ -344..-347.
    near = [s for s in STATIONS if -352.0 <= s[0] <= -339.0 and s[1] <= 46.0]
    chk("B_clear_of_the_beat6_hold_ray", not near,
        "no station in circuit x -352..-339 at y <= 46.0 (the window where the "
        "Beat-6 hold ray crosses the paddock's south boundary); nearest "
        "station in x is %.1f" % min(abs(s[0] + 345.5) for s in STATIONS))

    # [W] THE WAVELENGTH, MEASURED OFF A RENDER. R2-058 and Law 5.
    # `[8b]`-style round-trips are an ALGEBRAIC IDENTITY -- they use the
    # constant under test on both sides and pass for any value of it, including
    # a wrong one. This renders the spangle Voronoi alone through an
    # orthographic camera and COUNTS the cells, with two controls: a Wave of
    # known closed form, and the naive `scale = 1/lam` reading the law warns
    # about, which must come back WRONG or the probe cannot discriminate.
    if HAVE_BPY:
        try:
            def _mk(nt):
                return nt.vor(nt.object_coords(), wavelength_m=LAM_SPANGLE,
                              feature="F1")

            def _ctl(nt):
                return nt.wave(nt.object_coords(), wavelength_m=0.010,
                               direction="X")

            def _neg(nt):
                n = nt.n("ShaderNodeTexVoronoi", voronoi_dimensions="3D")
                nt.pin(n, 0, nt.object_coords())
                nt.pin(n, 2, 1.0 / LAM_SPANGLE)      # DELIBERATELY the bug
                return (n, 0)

            got = K.emitted_wavelength_m(_mk, span=0.60, px=2048)
            ctl_ = K.emitted_wavelength_m(_ctl, span=0.60, px=2048)
            neg = K.emitted_wavelength_m(_neg, span=0.60, px=2048)
            err = abs(got - LAM_SPANGLE) / LAM_SPANGLE
            chk("W_spangle_wavelength_off_a_render",
                err < 0.20 and abs(ctl_ - 0.010) / 0.010 < 0.02 and neg / LAM_SPANGLE > 1.8,
                "declared %.3f mm, RENDERED and counted %.3f mm, %.1f %% apart "
                "(itemkit states +-20 %% for a fractal cell field); control: a "
                "10.000 mm Wave returns %.4f mm, %.2f %% out; NEGATIVE CONTROL: "
                "the naive scale=1/lam reading Law 5 warns about emits %.3f mm, "
                "%.2fx off -- so the probe can fail"
                % (LAM_SPANGLE * 1000, got * 1000, 100 * err, ctl_ * 1000,
                   100 * abs(ctl_ - 0.010) / 0.010, neg * 1000, neg / LAM_SPANGLE))
        except Exception as e:                               # noqa: BLE001
            chk("W_spangle_wavelength_off_a_render", False, "RAISED: %r" % (e,))

    if verbose:
        print("\n  %s selftest: %d checks, %d FAILED"
              % (ITEM, len(ok) + len(fail), len(fail)))
    return not fail


# ==============================================================================
# 10.  CLI
# ==============================================================================

def main():
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--build", action="store_true")
    p.add_argument("--test-scene", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--census", action="store_true")
    p.add_argument("--derive-framing", action="store_true")
    p.add_argument("--interface", action="store_true")
    p.add_argument("--not-instanced", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)

    if a.derive_framing:
        print(json.dumps(derive_framing(), indent=1, default=float))
    if a.census:
        census()
    if a.selftest and not (a.build or a.test_scene):
        good = selftest()
        if not HAVE_BPY:
            print(">> STAGE RESULT: selftest(pure-python) %s"
                  % ("PASS" if good else "FAIL"))
        if not good:
            raise SystemExit(2)
    if a.interface:
        interface_json(a.out if a.out and a.out.endswith(".json") else None)
    if a.build or a.test_scene:
        stats = {}
        if a.test_scene:
            test_scene(samples=a.samples, limit=a.limit, stats=stats)
        else:
            build(instanced=not a.not_instanced, limit=a.limit, stats=stats)
        interface_json()
        if a.selftest:
            if not selftest():
                raise SystemExit(2)
        if a.out:
            bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
            log("saved %s" % a.out)
        print(">> STAGE RESULT: build %d objects, %d triangles"
              % (stats.get("objects", 0), stats.get("triangles", 0)))
        print(">> gate: " + " ".join(K.gate_command(
            ITEM, a.out or "<blend>", collection=COLL,
            filmed_distance_m=FILMED_AT_M, onscreen_px_4k=ONSCREEN_PX_4K)))


if __name__ == "__main__":
    main()
