#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
armco_w_beam.py — CIRCUIT VITRINE, per-item hero campaign, item ``armco_w_beam``
(zone ``barriers``, wave 1, build order 52, **7 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every W-beam guardrail element on the circuit, built as a **closed 3.0 mm steel
shell** — a true W section with rolled return lips, punched splice and post
slots that are real holes with a real punched wall, a real 320 mm lapped splice
at every joint, and the circuit's 38 recorded incidents deformed into the metal
rather than painted onto it.

WHY THE LAST ONE WAS REJECTED, AND WHAT CHANGED
-----------------------------------------------
    "the barrier is a smooth tube ... no bolts, no posts, no scuffs"

``build_barriers.build_armco`` swept an 11-point open profile along a polyline.
Three things were structurally missing and no material could have hidden them:

  1. **No thickness.**  An open strip has no edge.  At 2.6 m the top lip of a
     guardrail is the single most legible thing about it: 3 mm of steel rolled
     through 78 deg with a lit top face and a hard shadow under it.
  2. **No holes.**  The splice slots and the post slot are the only places the
     eye can check the scale of the object.  Eight button-heads in two columns
     is the read of "guardrail"; a blank sheet is the read of "extrusion".
  3. **Not a W.**  The old profile put the centre ridge 24 mm forward of the
     edges.  On a real W-beam the centre ridge is the DEEPEST point — it is what
     bears on the post and takes the post bolt — and the edges stand 30 mm
     forward of it.  Getting that backwards inverts every shadow in the section.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 2.6 = 1435.9 px/m     ->     1 px = 0.696 mm

    the 312 mm section              448 px tall   (manifest: onscreen_px_4k 445)
    the 83 mm corrugation depth     119 px
    the 3.0 mm sheet thickness      4.3 px          <- must be geometry
    the 16 mm return lip            23 px           <- must be geometry
    the 4 mm lip fillet             5.7 px          <- must be geometry
    a 30 x 18 mm splice slot        43 x 26 px      <- must be a hole
    the 1.5 mm hem radius           2.2 px          <- must be geometry
    zinc spangle, 5-40 mm           7-57 px         <- shading, and it is

Anything in that list that is not mesh is a placeholder at 2.6 m.  All of it is
mesh except the spangle, which has no silhouette and no occlusion.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  7 items depend on it.
===============================================================================
Dependants named in the manifest, and what each of them must call:

    armco_splice_bolt   ``splice_sites(...)``   8 slots per joint, world frame
    armco_spacer_block  ``post_sites(...)``     post-bolt slot, world frame
    armco_reflector     ``reflector_sites(...)``top-lip mount points
    armco_terminal      ``run_ends(side)``      where a run stops and needs one
    advertising_board   ``face_point(...)``     a point on the traffic face
    scuff_mark_barrier  ``face_point(...)`` + ``ATTRS``
    marshal_access_gate ``run_ends(side)``, ``GATE_STATIONS``

--- 1. THE SECTION ------------------------------------------------------------

    SEC_H = 0.3120   section height, lip tip to lip tip
    SEC_D = 0.0830   depth: traffic face (valley) to post face (centre ridge)
    SEC_T = 0.0030   sheet thickness (EN 1317 profile A / "glissiere" gauge)
    LIP_L = 0.0160   return flange, folded 78 deg toward traffic
    ARMCO_TOP = 1.012 m  (FIA 3-beam), unchanged from ``build_barriers``

    ``profile_mid()``    -> (K,2) array of (t, v), the sheet MID-SURFACE, t
                            measured POSITIVE AWAY FROM THE TRACK from the
                            traffic face.  t = 0 is the barrier face and is
                            exactly ``world_contract.barrier_offset(s, side)``.
    ``section_loop(lod)``-> the closed shell outline used by the mesher, with
                            per-point normal, arc length, curvature and the four
                            shading attributes.

    RAIL_HZ3 = [0.072, 0.386, 0.700]   bottom-edge heights above ground datum
    RAIL_HZ2 = [0.150, 0.560]          0.700 + 0.312 = 1.012 = ARMCO_TOP.
                                       build_barriers publishes 0.080/0.390 for
                                       the lower two; with a real 312 mm
                                       section those INTERPENETRATE by 2 mm.
                                       See the RAIL_HZ3 comment.

--- 2. WHERE THE PANELS ARE ---------------------------------------------------

    ``barrier_line(side)``  -> the sampled barrier polyline: world points, the
                               station of each, arc length.  Reproduces
                               ``build_barriers.barrier_nodes`` including the
                               history jitter clamp (|lat| <= 0.25 m by
                               contract) and the run straightening.
    ``panels(side)``        -> the list of Panel records for one side: node
                               index, arc-length span, station, element length,
                               rail count, lap flags, damage.
    ``ELEMENT_L``           -> the three element lengths and the radius bands
                               that select them.  A 4.00 m element cannot be
                               cold-bent below ~200 m radius without kinking, so
                               tight corners get 2.00 m and 1.33 m elements.
                               This is real practice AND it is why the barrier
                               does not read as a 12-sided polygon at T4.

--- 3. THE MOUNTING POINTS OTHER ITEMS NEED -----------------------------------

    ``post_sites(side)``      -> [{s, arc, world, tangent, normal, up,
                                   ground_z, slot_z[], slot_w, slot_h, nrail}]
                                 one per post.  The post stands at the CENTRE
                                 of the 320 mm lap, not at the panel node --
                                 a W-beam splice is made at a post.
    ``splice_sites(side)``    -> 8 per joint per rail: two columns at +-76 mm
                                 from the post, four rows at v = 52, 104, 208,
                                 260 mm.  Each is an already-punched hole.
    ``reflector_sites(side)`` -> [{s, world, normal, up}] top lip, every 2nd bay
    ``run_ends(side)``        -> [{arc, world, tangent, is_start}] terminals
    ``face_point(s, side, h)``-> world point on the traffic face at height h
    ``_splice_columns(p)``    -> sheet-local x of the bolt columns (internal,
                                 but it is the one place the pattern is defined)

    Every one of them returns WORLD coordinates already, and every z comes from
    ``world_contract.ground_z``.  No dependant needs to know the local frame.

--- 4. EMITTING ---------------------------------------------------------------

    ``build(sides=(+1,-1), lod_anchor=..., windows=...)`` emits into collection
    ``W_Item_ArmcoWBeam`` with object prefix ``AWB_``.  ONE OBJECT PER BAY —
    a bay is one node-to-node element carrying 2 or 3 rails, which is exactly
    what the manifest counts as an instance.  The full circuit is **1789** bays
    against the manifest's estimate of 1821 (-1.8 %): 1460 four-metre elements,
    172 of 2.00 m and 157 of 1.33 m on the tight radii, plus closure elements
    at every run end and marshal gate.  See §2.

    ``macro_rig(aim, coll, name)`` places a camera at EXACTLY
    ``nearest_camera_m`` on ``lens_at_closest_mm`` against a ``hero_aim()``
    record; ``hero_aim()`` picks the station by score — traffic face lit at
    62 deg incidence, a real incident in the bay, inside a ``HERO_WINDOWS``
    entry.  ``spine_frame(p, ln, nxt, x)`` is the single definition of where an
    element physically is, and both the mesher and the lap-continuity selftest
    call it.

    ``lod_anchor`` is a list of world points — the camera path — and the mesh
    density of every bay is graded by its distance to the nearest of them.
    Pass the beat-4/5/6 camera corridor for world assembly.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library.  Measured by
                          ``item_gate``: ``no_external_assets``.
 2. no real brands        this item carries no lettering.  The painted runs use
                          ``build_barriers.LIVERY`` verbatim (9 invented
                          colours), knocked 25 % toward an industrial enamel so
                          they read as painted steel and not as a car.
 3. car scale             the 2.005 m car sets the incident lobe widths and the
                          0.55 m scuff band height, not intuition.
 4. z = 0 is one plane    never assumed: every z is ``C.ground_z(s, u)``.
 5. embed >= 20 mm        THE W-BEAM DOES NOT STAND ON THE GROUND.  Its lowest
                          edge is 80 mm clear of the datum by FIA/EN convention
                          (RAIL_HZ3[0]).  ``armco_post`` owns the embedment and
                          this module exports ``post_sites`` so it embeds at the
                          right stations.  ``C.BASE_EMBED_M`` is re-exported.
 6. recentre + TexCoord   every bay's mesh is local to its own centre, in a
                          canonical frame (+X along the panel, +Y away from the
                          track, +Z up), |P| < 2.3 m.  The material reads
                          ``TexCoord->Object`` plus per-vertex attributes and a
                          per-OBJECT texture offset so that no two bays get the
                          same spangle.  ``Geometry->Position`` appears nowhere.
 7. chunk along s         one bay is <= 4.33 m of circuit.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names four axes.  All four are in the MESH, not in a transform:

  "3.86-4.09 m panels"        element length is sampled per node and the sheet
                              is re-meshed at that length; plus 2.00 m and
                              1.33 m elements on tight radii and closure
                              elements of arbitrary length at run ends and at
                              the 16 marshal gates.  Measured spread of the
                              built population is reported by ``--selftest``.
  "3-beam vs 2-beam in 70 m   ``rail_count`` verbatim from build_barriers: a
   blocks"                    piecewise-constant 70 m block hash, 2-beam on 30 %
                              of the LEFT side only.  A 2-beam bay is a
                              different object with a different vertex count.
  "38 incident scars          ``History`` reproduced verbatim from
   (brush 44 %, hit 34 %,     build_barriers, so this module's dents are in the
   repaired 15 %, heavy 7 %)" same places as its paint transfer.  A dent is a
                              lateral push-back PLUS a loss of corrugation depth
                              PLUS a plastic hinge at each lobe end PLUS edge
                              buckling waves PLUS vertical drag.  Five separate
                              geometric consequences, because that is what a
                              car does to 3 mm of steel.
  "9 fictional liveries on    ``run_paint`` verbatim: 30 % of maintenance runs
   30 % of runs"              are painted, colour from the 9-entry LIVERY table.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/armco_w_beam.py -- --test --save world/items/armco_w_beam_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/armco_w_beam.py -- --selftest
"""

from __future__ import annotations

import argparse
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

import world_contract as C                                        # noqa: E402
import itemkit as K                                               # noqa: E402

__version__ = "1.0.0"

ITEM = "armco_w_beam"
COLL = "W_Item_ArmcoWBeam"
PFX = "AWB_"
XPFX = "AWBSTAND_"          # test-scene stand-ins owned by OTHER items.  It is
                            # deliberately NOT a superset of PFX-with-suffix:
                            # the gate is run with --prefix AWB_ and would
                            # otherwise measure someone else's geometry as mine.

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 2.6
LENS_MM = 35.0
ONSCREEN_PX_4K = 445.0
INSTANCES_DECLARED = 1821
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 1435.9
PX_M = 1.0 / PX_PER_M                                        # 0.696 mm

# --- the section -------------------------------------------------------------
# EN 1317 profile A / AASHTO M-180 metric.  The circuit is a 4.00 m-element,
# 2.00 m-post-pitch European installation (build_barriers.PANEL_L / POST_PITCH),
# so the sheet is the 3.0 mm European gauge, not the 2.67 mm US 12-gauge.
SEC_H = 0.3120            # lip tip to lip tip
SEC_D = 0.0830            # traffic face (valleys) -> post face (centre ridge)
SEC_T = 0.0030            # sheet thickness
EDGE_T = 0.0525           # depth of the edge flat.  Derived: it puts both webs
                          # at 47 deg, which is what a rolled W-beam is.
EDGE_FLAT = 0.0300        # height of the edge flat below the fold
LIP_L = 0.0160            # return flange length
LIP_DEG = 78.0            # fold angle from the edge flat (90 nominal, rolled
                          # slightly closed, which is what the rolls produce)
R_LIP = 0.0040            # lip fold radius (inside)
R_EDGE = 0.0200           # edge flat -> web
R_VALLEY = 0.0250         # the two troughs
R_RIDGE = 0.0250          # the centre ridge

# --- the rails ---------------------------------------------------------------
ARMCO_TOP = 1.012                       # FIA 3-beam.  build_barriers agrees.
# Bottom-edge height of each rail above the ground datum.
#
# THE 2 mm CORRECTION, AND WHY IT IS NOT A DRIFT FROM build_barriers.
# build_barriers publishes [0.080, 0.390, 0.700].  With the standard 312 mm
# section that puts the top edge of rail 1 at 0.392 and the bottom edge of rail
# 2 at 0.390 -- the two rolled lips INTERPENETRATE by 2 mm.  It never showed
# because that module's rail was an open strip with no thickness and no lip, so
# there was nothing there to intersect.  A closed shell with a 16 mm return lip
# has, and 2 mm of interpenetrating steel at 1436 px/m is a 3 px black seam
# running the whole length of the barrier.
# The one number that must not move is ARMCO_TOP = 1.012 (contract + FIA), so
# the TOP rail keeps 0.700 exactly and the lower two drop to give a 2 mm air
# gap, which is what a real triple-rail installation has between beams.
RAIL_HZ3 = [0.072, 0.386, 0.700]        # 0.700 + 0.312 = 1.012 = ARMCO_TOP
RAIL_HZ2 = [0.150, 0.560]               # 0.150 + 0.312 = 0.462, 98 mm of gap

# --- the elements ------------------------------------------------------------
PANEL_L = 4.00            # nominal element (build_barriers)
POST_PITCH = 2.00         # post centres (build_barriers)
SPLICE_LAP_M = 0.320      # lapped splice length.  4.00 + 0.32 = 4.32 m sheet,
                          # which is the real 4.30 m element to the roll.
LAP_RAMP_M = 0.220        # over how much the sheet steps back into the lap

# radius bands -> element length.  A 4.00 m element cold-bends comfortably to
# ~200 m radius; below that it kinks at the splice, which at 1436 px/m is a
# 50 mm = 72 px facet error at every joint.  Real installations use shortened
# elements, and so does this.
ELEMENT_L = [(30.0, 1.330), (70.0, 2.000), (1e9, 4.000)]
# How much of the barrier line's curvature an element of each nominal length
# actually takes up.  A 4.00 m sheet is essentially a straight chord between its
# two posts -- which is why the barrier reads as a polygon through a corner, and
# why the short elements above exist at all.
FOLLOW = {4.000: 0.15, 2.000: 0.55, 1.330: 0.85}

# --- slots -------------------------------------------------------------------
POST_SLOT = (0.070, 0.022)      # (along the panel, across the section) m
SPLICE_SLOT = (0.030, 0.018)
SPLICE_DX = 0.076               # splice-bolt column offset from the joint
SPLICE_V = (0.052, 0.104, 0.208, 0.260)   # the four bolt rows, v from the
                                          # bottom lip.  Two columns x four
                                          # rows = the 8 slots of the standard.
SLOT_DIE_ROLL = 0.00035         # entry-face draw-in of a punched hole
SLOT_BURR = 0.00018             # exit-face burr

# --- fabrication and erection ------------------------------------------------
SAG_M = 0.0035            # mid-span bow toward traffic
OILCAN_M = 0.00055        # roll-forming flatness deviation on the flats
ERECT_LAT_M = 0.0022      # per-element lateral set-out error
ERECT_ROLL_DEG = 0.35     # per-element roll about the panel axis

# --- damage ------------------------------------------------------------------
DENT_FLATTEN = 0.62       # how much of the corrugation a full-depth hit eats
DENT_DRAG = 0.16          # vertical drag per metre of push-back
BUCKLE_AMP = 0.0075       # edge buckling wave amplitude at a heavy hit
BUCKLE_LAM = (0.085, 0.165)

# fictional test-car liveries — verbatim from build_barriers so this module's
# painted runs and its paint transfer come from ONE palette.  No real teams.
LIVERY = [
    (0.055, 0.135, 0.150), (0.640, 0.090, 0.070), (0.070, 0.180, 0.520),
    (0.880, 0.560, 0.040), (0.780, 0.780, 0.800), (0.100, 0.330, 0.170),
    (0.560, 0.110, 0.360), (0.930, 0.900, 0.250), (0.180, 0.180, 0.200),
]

# build_barriers.GATE_STATIONS — the 16 marshal access openings.  A run is
# broken at each one and closed with a non-standard element on both sides.
GATE_STATIONS = [305.0, 742.0, 968.0, 1032.0, 1288.0, 1590.0, 1782.0, 1930.0,
                 2196.0, 2372.0, 2560.0, 2726.0, 2905.0, 3092.0, 3300.0, 3612.0]
GATE_CLEAR_M = 3.60       # the opening

BASE_EMBED_M = C.BASE_EMBED_M     # re-exported: armco_post needs it, and one
                                  # import is better than two.
LAP_LEN = C.LAP
BARRIER_JITTER_MAX_M = C.BARRIER_JITTER_MAX_M

# The doppler hover, s = 2555 on the right of travel, is the hero window this
# item is filmed in ("at 2.6 m from the doppler hover the section is fully
# readable" -- the manifest's own note).  build_barriers' HERO table calls the
# same span 2470..2650 side -1, tier 2.
HERO_S = 2555.0
HERO_SIDE = -1

# per-vertex attributes.  Everything that is constant over a bay is an OBJECT
# property instead (see `_object_props`), which saves 52 bytes a vertex over
# 4.0 M vertices.
ATTRS = ("awb_age", "awb_rust", "awb_scuff", "awb_pmix", "awb_fresh",
         "awb_dent", "awb_pocket", "awb_upz", "awb_edge", "awb_lap",
         "awb_slot", "awb_face")
OBJ_PROPS = ("awb_painted", "awb_run_r", "awb_run_g", "awb_run_b",
             "awb_pt_r", "awb_pt_g", "awb_pt_b",
             "awb_ofs_x", "awb_ofs_y", "awb_ofs_z", "awb_seed")

SEED = 20260729


# ==============================================================================
#  1.  DETERMINISTIC NOISE  —  byte-identical to build_barriers
# ==============================================================================
# Copied rather than imported: build_barriers imports bpy at module scope and
# builds 240 000 stones at import time.  These eight functions are the whole of
# what is shared, and they are pure numpy, so copying them costs nothing and
# guarantees that this module's incidents land on the same metre of circuit as
# build_barriers' paint transfer.  Verified equal in `selftest`.

_U32 = np.uint32


def hash01(*keys):
    """FNV-1a over integer key arrays -> float64 in [0,1).  Broadcasts."""
    h = np.zeros(np.broadcast(*[np.asarray(k) for k in keys]).shape
                 if len(keys) > 1 else np.shape(keys[0]), dtype=np.uint32)
    h[...] = _U32(2166136261)
    with np.errstate(over="ignore"):
        for k in keys:
            kk = np.asarray(k)
            kk = np.rint(kk).astype(np.int64) if kk.dtype.kind == "f" else kk.astype(np.int64)
            kk = (kk & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ kk) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def h01(*keys):
    return float(hash01(*[np.array([k]) for k in keys])[0])


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise1(x, seed=0):
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x).astype(np.int64)
    f = x - i
    a = hash01(i, np.full_like(i, seed))
    b = hash01(i + 1, np.full_like(i, seed))
    u = _smooth(f)
    return a * (1.0 - u) + b * u


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    x = np.asarray(x, dtype=np.float64)
    tot = np.zeros_like(x)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot += amp * vnoise1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp01((np.asarray(x, dtype=np.float64) - e0) / max(1e-9, (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ==============================================================================
#  2.  THE MAINTENANCE / INCIDENT HISTORY  —  reproduced from build_barriers
# ==============================================================================
# The manifest's third variation axis IS this field: "38 incident scars
# (brush 44 %, hit 34 %, repaired 15 %, heavy 7 %)".  Reproducing it exactly
# rather than inventing a new one is the difference between the dent and the
# paint smear being the same event and being two unrelated events 40 m apart.

PS, NS, SGRID = C.PS, C.NS, C.SGRID

CRASH_W = {1: 1.00, 2: 0.25, 3: 0.75, 4: 0.95, 5: 0.40, 6: 0.30, 7: 0.30, 8: 0.85,
           9: 0.30, 10: 0.55, 11: 0.60, 12: 1.00, 13: 0.25, 14: 0.30, 15: 0.60}


def crash_field():
    s = SGRID
    w = np.full(NS, 0.045)
    for c in C.SPEC["corners"]:
        if not c["is_numbered_corner"]:
            continue
        i = c["index"]
        sa = c["s_apex"]
        cw = CRASH_W.get(i, 0.3)
        du = ((s - sa + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5
        w += cw * 1.05 * np.exp(-0.5 * ((du + 55.0) / 62.0) ** 2)
        w += cw * 0.85 * np.exp(-0.5 * ((du - 45.0) / 48.0) ** 2)
    return w


class History:
    """Maintenance runs and the 38 incidents.  Verbatim from build_barriers."""

    def __init__(self):
        self.runs, self.age, self.rid = {}, {}, {}
        for side in (+1, -1):
            self.runs[side], self.age[side] = self._runs(side)
            arr = np.zeros(NS)
            for i, (a, b, _ag) in enumerate(self.runs[side]):
                arr[(SGRID >= a) & (SGRID < b)] = i + 1 + (0 if side > 0 else 500)
            self.rid[side] = arr
        self.inc = self._incidents()

    def _runs(self, side):
        seed = 5100 + (side > 0) * 37
        runs, s = [], 0.0
        sector_age = fbm1(np.arange(0, LAP_LEN, 50.0) / 640.0, seed=seed + 3)
        k = 0
        while s < LAP_LEN:
            u = h01(seed, k, 11)
            L = 25.0 + 195.0 * (u ** 1.7)
            e = min(LAP_LEN, s + L)
            sa = float(np.interp(s, np.arange(0, LAP_LEN, 50.0), sector_age))
            v = h01(seed, k, 29)
            if v < 0.085:
                age = 0.02 + 0.10 * h01(seed, k, 31)
            elif v < 0.20:
                age = 0.18 + 0.22 * h01(seed, k, 37)
            else:
                age = float(clamp01(0.35 + 0.62 * sa + 0.22 * (h01(seed, k, 41) - 0.5)))
            runs.append((s, e, float(age)))
            s = e
            k += 1
        arr = np.zeros(NS)
        for (a, b, ag) in runs:
            arr[(SGRID >= a) & (SGRID < b)] = ag
        return runs, arr

    def _incidents(self):
        w = crash_field()
        cdf = np.cumsum(w)
        cdf /= cdf[-1]
        out = []
        for i in range(38):
            u = h01(7717, i, 3)
            sa = float(np.interp(u, cdf, SGRID))
            side = -1 if h01(7717, i, 5) < 0.72 else +1
            sev = h01(7717, i, 9)
            if sev < 0.44:
                kind, ext, depth = "brush", 5.0 + 9.0 * h01(7717, i, 13), 0.010
            elif sev < 0.78:
                kind, ext, depth = "hit", 8.0 + 14.0 * h01(7717, i, 13), 0.055
            elif sev < 0.93:
                kind, ext, depth = "repaired", 12.0 + 12.0 * h01(7717, i, 13), 0.012
            else:
                kind, ext, depth = "heavy", 16.0 + 14.0 * h01(7717, i, 13), 0.190
            out.append(dict(s=sa, side=side, kind=kind, extent=ext, depth=depth,
                            epoch=h01(7717, i, 17),
                            livery=LIVERY[int(h01(7717, i, 19) * (len(LIVERY) - 1e-6))],
                            idx=i))
        return out

    def age_at(self, s, side):
        i = (np.rint(np.asarray(s) % LAP_LEN / PS).astype(np.int64)) % NS
        return self.age[side][i]

    def run_id(self, s, side):
        i = (np.rint(np.asarray(s) % LAP_LEN / PS).astype(np.int64)) % NS
        return self.rid[side][i]

    def scars(self, s, side):
        """(dent m, scuff, paint_mix, paint_rgb, fresh) at station(s)."""
        s = np.atleast_1d(np.asarray(s, dtype=np.float64))
        dent = np.zeros_like(s)
        scuff = np.zeros_like(s)
        pmix = np.zeros_like(s)
        fresh = np.zeros_like(s)
        prgb = np.zeros(s.shape + (3,))
        for inc in self.inc:
            if inc["side"] != side:
                continue
            du = ((s - inc["s"] + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5
            r = inc["extent"] * 0.5
            g = np.exp(-0.5 * (du / max(1.0, r * 0.55)) ** 2)
            g *= (np.abs(du) < r * 1.6)
            lobe = g * (0.55 + 0.9 * vnoise1(du * 0.35 + inc["idx"] * 13.0, 771))
            if inc["kind"] == "repaired":
                fresh = np.maximum(fresh, (np.abs(du) < r).astype(float))
                dent = np.maximum(dent, lobe * inc["depth"] * 0.4)
            else:
                dent = np.maximum(dent, lobe * inc["depth"])
            sc = g * (1.0 - 0.55 * inc["epoch"])
            scuff = np.maximum(scuff, sc)
            gp = np.exp(-0.5 * (du / max(0.8, r * 0.24)) ** 2) * (np.abs(du) < r * 0.8)
            pm = gp * (0.85 - 0.6 * inc["epoch"])
            upd = pm > pmix
            pmix = np.where(upd, pm, pmix)
            prgb[upd] = inc["livery"]
        return dent, clamp01(scuff), clamp01(pmix), prgb, fresh

    def align(self, s, side):
        s = np.asarray(s, dtype=np.float64)
        seed = 8800 + (side > 0) * 13
        lat = (fbm1(s / 47.0, seed=seed, oct=3) - 0.5) * 0.075
        lat += (fbm1(s / 7.3, seed=seed + 5, oct=2) - 0.5) * 0.020
        vert = -(fbm1(s / 33.0, seed=seed + 9, oct=3)) * 0.045
        vert += -(fbm1(s / 5.1, seed=seed + 11, oct=2)) * 0.012
        return lat, vert


HIST = History()


def rail_count(s, side):
    """3-beam is standard; quieter infield stretches carry 2.  Piecewise
    constant on 70 m blocks so it never changes inside an element.
    Verbatim from build_barriers."""
    blk = np.floor(np.asarray(s) / 70.0).astype(np.int64)
    r = hash01(blk, np.full(blk.shape, 6100 + (side > 0)))
    return np.where((r < 0.30) & (side > 0), 2, 3)


def run_paint(rid):
    """Is this maintenance run painted, and which of the 9 liveries?"""
    rid = np.atleast_1d(np.asarray(rid)).astype(np.int64)
    flag = (hash01(rid, np.full(rid.shape, 4441)) < 0.30).astype(np.float64)
    hue = hash01(rid, np.full(rid.shape, 4457))
    return flag, hue


def livery_of(hue):
    """hue in [0,1) -> an industrial enamel version of one of the 9 liveries.

    LIVERY is a CAR palette.  A guardrail painted in it straight reads as a
    prop; knocked 25 % toward a warm off-white it reads as the enamel a circuit
    actually buys, and it is still recognisably the same nine colours.
    """
    i = int(np.clip(hue, 0.0, 0.9999) * len(LIVERY))
    c = np.array(LIVERY[i], float)
    return tuple(c * 0.75 + np.array([0.086, 0.081, 0.072]))


# ==============================================================================
#  3.  THE SECTION PROFILE
# ==============================================================================
#
#          v
#          ^        the closed shell, drawn at 4x depth.  t = 0 is the
#   0.312 -+  __    BARRIER FACE (world_contract.barrier_offset), t grows
#          | (  \   AWAY from the track.  The centre ridge at t = 0.083 is
#          |  \  \  what bears on the post and carries the post bolt; the
#          |   \  ) two edge flats stand 30.5 mm forward of it.  Getting
#   0.234 -+   (      that relationship backwards is what made the last
#          |    \  \  build's shadows read as a tube.
#   0.156 -+     \  )   <- centre ridge, post bearing, post-bolt slot
#          |     /  /
#   0.078 -+   (   /
#          |  /  /
#       0 -+ (__/         <- rolled return lip, 16 mm at 78 deg
#          +-------------> t
#            0     0.083

def _rot90(d):
    return np.stack([-d[..., 1], d[..., 0]], axis=-1)


def _cross2(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _fillet_path(A, R, arc_chord, line_step, min_arc_seg=None):
    """Tessellate a 2-D polyline with a fillet at every interior vertex.

    Returns (P (K,2), Tg (K,2) unit tangent, curv (K,) signed 1/R, arclen (K,)).
    `curv` is positive where the path turns left (toward +rot90(tangent)); the
    shading attributes read it, so it has to be signed, not |k|.

    NO POINT IS EMITTED TWICE.  The first version emitted the junction between
    an arc and the line after it from both sides, which put a zero-length edge
    at every one of the seven fillets -- and a zero-length edge is a free pass
    on a 10th-percentile edge check.  A gate cannot tell a degenerate edge from
    a fine one, so the mesher must not make any.
    """
    if min_arc_seg is None:
        min_arc_seg = MIN_ARC_SEG
    A = np.asarray(A, float)
    n = len(A)
    R = list(R)
    seg = A[1:] - A[:-1]
    Ls = np.linalg.norm(seg, axis=1)
    d = seg / Ls[:, None]

    tl = np.zeros(n)
    sweep = np.zeros(n)
    turn = np.zeros(n)
    for i in range(1, n - 1):
        c = float(np.clip(np.dot(-d[i - 1], d[i]), -1.0, 1.0))
        phi = math.acos(c)                        # interior angle
        if phi > math.pi - 1e-6:
            continue
        tl[i] = R[i] / math.tan(phi * 0.5)
        sweep[i] = math.pi - phi
        turn[i] = 1.0 if _cross2(d[i - 1], d[i]) > 0 else -1.0
        avail = min(Ls[i - 1], Ls[i]) * 0.48
        if tl[i] > avail:                        # never let two fillets collide
            tl[i] = avail
            R[i] = tl[i] * math.tan(phi * 0.5)

    P, Tg, K = [], [], []
    for i in range(n - 1):
        p0 = A[i] + d[i] * tl[i]
        p1 = A[i + 1] - d[i] * tl[i + 1]
        seglen = float(np.linalg.norm(p1 - p0))
        m = max(1, int(math.ceil(seglen / line_step)))
        j0 = 0 if i == 0 else 1            # the arc before already gave p0
        for j in range(j0, m + 1):
            t = j / m
            P.append(p0 + (p1 - p0) * t)
            Tg.append(d[i])
            K.append(0.0)
        if i + 1 <= n - 2 and sweep[i + 1] > 1e-9:
            r = R[i + 1]
            sg = turn[i + 1]
            nrm = _rot90(d[i]) * sg
            ctr = p1 + nrm * r
            a0 = math.atan2(p1[1] - ctr[1], p1[0] - ctr[0])
            sw = sweep[i + 1] * sg
            arclen = abs(sw) * r
            m2 = max(min_arc_seg, int(math.ceil(arclen / arc_chord)))
            for j in range(1, m2 + 1):       # j=0 is p1, already emitted
                a = a0 + sw * (j / m2)
                P.append(ctr + np.array([math.cos(a), math.sin(a)]) * r)
                tg = np.array([-math.sin(a), math.cos(a)]) * sg
                Tg.append(tg)
                K.append(sg / r)
    P = np.array(P)
    Tg = np.array(Tg)
    Tg = Tg / np.maximum(np.linalg.norm(Tg, axis=1, keepdims=True), 1e-12)
    K = np.array(K)
    al = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return P, Tg, K, al


def _control_raw():
    """Design intent: the theoretical corners of the section, before the
    fillets eat into them."""
    a = math.radians(LIP_DEG)
    dt = LIP_L * math.sin(a)
    dv = LIP_L * math.cos(a)
    return np.array([
        (EDGE_T - dt, 0.0 + dv),          # bottom lip tip
        (EDGE_T, 0.0),                    # bottom fold
        (EDGE_T, EDGE_FLAT),              # end of the bottom edge flat
        (0.0, 0.0780),                    # lower valley (traffic face)
        (SEC_D, 0.1560),                  # centre ridge (post face)
        (0.0, 0.2340),                    # upper valley
        (EDGE_T, SEC_H - EDGE_FLAT),      # start of the top edge flat
        (EDGE_T, SEC_H),                  # top fold
        (EDGE_T - dt, SEC_H - dv),        # top lip tip
    ])


_PROF_R = [0.0, R_LIP, R_EDGE, R_VALLEY, R_RIDGE, R_VALLEY, R_EDGE, R_LIP, 0.0]

_CTRL_SOLVED = None


def profile_mid():
    """The sheet MID-SURFACE control polygon, solved so that the OUTER SURFACE
    of the finished shell measures exactly SEC_H x SEC_D.

    Why this needs solving at all: a 25 mm fillet at the centre ridge pulls the
    apex 11.5 mm off the theoretical corner, and the same happens at both
    valleys, so a control polygon written straight from the catalogue produces a
    section 63 mm deep instead of 83 -- 24 % shallow, which is a 29 px error in
    the corrugation depth at the filmed distance and reads as a flattened rail.
    Six fixed-point iterations on an affine (t, v) correction of the control
    polygon converge to under a micron.
    """
    global _CTRL_SOLVED
    if _CTRL_SOLVED is not None:
        return _CTRL_SOLVED
    A0 = _control_raw()
    at, bt, av, bv = 1.0, 0.0, 1.0, 0.0
    for _ in range(8):
        A = A0.copy()
        A[:, 0] = A0[:, 0] * at + bt
        A[:, 1] = A0[:, 1] * av + bv
        P = _shell_outline(A, 0.0006, 0.004, 12)
        t0, t1 = P[:, 0].min(), P[:, 0].max()
        v0, v1 = P[:, 1].min(), P[:, 1].max()
        kt = SEC_D / max(t1 - t0, 1e-9)
        kv = SEC_H / max(v1 - v0, 1e-9)
        at, bt = at * kt, bt * kt - t0 * kt
        av, bv = av * kv, bv * kv - v0 * kv
    A = A0.copy()
    A[:, 0] = A0[:, 0] * at + bt
    A[:, 1] = A0[:, 1] * av + bv
    _CTRL_SOLVED = A
    return A


def _shell_outline(ctrl, arc_chord, line_step, hem_n):
    """The closed outer outline for a given control polygon.  Used by the
    solver; `section_loop` does the same thing but keeps the bookkeeping."""
    mid, tg, kv, al = _fillet_path(ctrl, list(_PROF_R), arc_chord, line_step)
    nrm = _rot90(tg)
    half = SEC_T * 0.5
    front = mid + nrm * half
    back = mid - nrm * half
    pts = list(front)
    K = len(mid)
    for j in range(1, hem_n):
        a = math.atan2(nrm[K - 1][1], nrm[K - 1][0]) - math.pi * (j / hem_n)
        pts.append(mid[K - 1] + np.array([math.cos(a), math.sin(a)]) * half)
    pts += list(back[::-1])
    for j in range(1, hem_n):
        a = math.atan2(-nrm[0][1], -nrm[0][0]) - math.pi * (j / hem_n)
        pts.append(mid[0] + np.array([math.cos(a), math.sin(a)]) * half)
    return np.array(pts)

# LOD -> (arc chord, straight step, hem segments, longitudinal step, real slots)
LOD_TABLE = [
    (0.00160, 0.0085, 7, 0.028, True),     # 0  hero      d < 8 m
    (0.00280, 0.0150, 6, 0.090, True),     # 1  near      d < 26 m
    (0.00450, 0.0280, 5, 0.300, False),    # 2  mid       d < 110 m
    (0.01000, 0.0900, 3, 0.900, False),    # 3  far
]
# EVERY fillet gets at least this many segments however coarse the LOD.  The
# four small-radius fillets (the two lip folds and the two edge bends) are the
# whole of the section's fine detail; letting a distant LOD reduce them to three
# facets each would take the finest decile of the pooled edge distribution from
# 1.6 px to 6.8 px, and the object would stop resolving at its own filmed
# distance while looking, from the module's point of view, like a saving.
MIN_ARC_SEG = 6


_SEC_CACHE = {}


def section_loop(lod):
    """The CLOSED shell outline of one rail, in (t, v).

    Returns a dict with, per loop point:
        P      (L,2)  position
        N      (L,2)  outward unit normal
        arc    (L,)   arc length around the loop (the material's v texture axis)
        face   (L,)   1 on the traffic side of the sheet, 0 on the post side
        upz    (L,)   the outward normal's v component  (= world +Z)
        curv   (L,)   signed curvature, positive = convex outward
        pocket (L,)   0..1 water-holding: faces up AND is concave
        edge   (L,)   0..1 a formed arris the paint chips off and the zinc wears
        arcw   (L,)   1 on a fillet, 0 on a flat (kills oil-canning on arcs)
    and the bookkeeping the mesher needs:
        IF, IB (K,)   loop index of the front / back copy of mid-path point k
        HEMT, HEMB    the two end hems as ordered loop-index lists, endpoints
                      included, so the caps and the slot rims never have to
                      reverse-engineer the loop layout.  The first version did,
                      and got 568 non-manifold edges for its trouble.
    """
    if lod in _SEC_CACHE:
        return _SEC_CACHE[lod]
    arc_chord, line_step, hem_n, _lstep, _slots = LOD_TABLE[lod]
    mid, tg, kv, al = _fillet_path(profile_mid(), list(_PROF_R),
                                   arc_chord, line_step)
    nrm = _rot90(tg)                       # points toward the traffic side (-t)
    half = SEC_T * 0.5
    front = mid + nrm * half
    back = mid - nrm * half
    K = len(mid)

    pts, nn, cu, aw = [], [], [], []

    def push(p, n, c, a):
        pts.append(p); nn.append(n); cu.append(c); aw.append(a)

    IF = np.arange(K)
    for k in range(K):
        push(front[k], nrm[k], kv[k], 1.0 if abs(kv[k]) > 1e-9 else 0.0)
    # top hem: front[K-1] -> back[K-1], sweeping through the sheared end
    a0 = math.atan2(nrm[K - 1][1], nrm[K - 1][0])
    HEMT = [K - 1]
    for j in range(1, hem_n):
        a = a0 - math.pi * (j / hem_n)
        HEMT.append(len(pts))
        push(mid[K - 1] + np.array([math.cos(a), math.sin(a)]) * half,
             np.array([math.cos(a), math.sin(a)]), 1.0 / half, 1.0)
    IB = np.empty(K, np.int64)
    for k in range(K - 1, -1, -1):
        IB[k] = len(pts)
        push(back[k], -nrm[k], -kv[k], 1.0 if abs(kv[k]) > 1e-9 else 0.0)
    HEMT.append(int(IB[K - 1]))
    # bottom hem: back[0] -> front[0]
    a0 = math.atan2(-nrm[0][1], -nrm[0][0])
    HEMB = [int(IB[0])]
    for j in range(1, hem_n):
        a = a0 - math.pi * (j / hem_n)
        HEMB.append(len(pts))
        push(mid[0] + np.array([math.cos(a), math.sin(a)]) * half,
             np.array([math.cos(a), math.sin(a)]), 1.0 / half, 1.0)
    HEMB.append(0)

    P = np.array(pts)
    N = np.array(nn)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    cu = np.array(cu)
    aw = np.array(aw)

    d = np.roll(P, -1, axis=0) - P
    seg = np.linalg.norm(d, axis=1)
    arc = np.concatenate([[0.0], np.cumsum(seg)[:-1]])

    face = (N[:, 0] < 0).astype(float)              # normal points toward -t
    upz = N[:, 1]
    concave = np.clip(-cu, 0.0, None)
    pocket = clamp01(np.clip(upz, 0, 1) ** 1.2 * np.clip(concave * 0.030, 0, 1) * 1.6)
    edge = clamp01(np.clip(cu, 0, None) * 0.0055)

    out = dict(P=P, N=N, arc=arc, face=face, upz=upz, curv=cu, pocket=pocket,
               edge=edge, arcw=aw, K=K, nloop=len(P), hem=hem_n,
               IF=IF, IB=IB, HEMT=HEMT, HEMB=HEMB, vprof=mid[:, 1],
               tprof=mid[:, 0], midarc=al)
    _SEC_CACHE[lod] = out
    return out


# ==============================================================================
#  4.  THE BARRIER LINE AND THE ELEMENT BREAKDOWN
# ==============================================================================

_LINE_CACHE = {}


def barrier_line(side, ds=0.5):
    """The sampled barrier polyline for one side, in the WORLD frame.

    Reproduces build_barriers.barrier_nodes' geometry exactly: contract
    `barrier_offset` plus the module's own bounded history jitter (clamped to
    `BARRIER_JITTER_MAX_M` by contract), ground datum from `C.ground_z`, then
    the low-curvature runs straightened and stepped, which is what a string-line
    erection actually produces.
    """
    key = (side, ds)
    if key in _LINE_CACHE:
        return _LINE_CACHE[key]
    s = np.arange(0.0, LAP_LEN, ds)
    lat_j, ver_j = HIST.align(s, side)
    lat_j = np.clip(lat_j, -BARRIER_JITTER_MAX_M, BARRIER_JITTER_MAX_M)
    off = C.barrier_offset(s, side) + lat_j
    P = np.asarray(C.su_to_world(s, off * side), float)
    P[:, 2] = C.ground_z(s, off, side) + ver_j
    Pc = np.vstack([P, P[:1]])
    sc = np.concatenate([s, [LAP_LEN]])
    seg = np.linalg.norm(np.diff(Pc, axis=0)[:, :2], axis=1)
    L = np.concatenate([[0.0], np.cumsum(seg)])

    # local radius of the barrier line, smoothed over 6 m so a 0.5 m sample step
    # cannot manufacture curvature out of the jitter
    d = np.diff(Pc[:, :2], axis=0)
    hd = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    w = max(3, int(round(6.0 / ds)) | 1)
    k = np.ones(w) / w
    hs = np.convolve(np.concatenate([hd[-w:], hd, hd[:w]]), k, mode="same")[w:-w]
    dh = np.gradient(hs) / np.maximum(seg, 1e-6)
    Rloc = 1.0 / np.maximum(np.abs(dh), 1e-9)
    Rloc = np.concatenate([Rloc, Rloc[-1:]])

    bt = C.barrier_type(s, side)
    bt = np.concatenate([bt, bt[:1]])
    out = dict(P=Pc, s=sc, L=L, R=Rloc, btype=bt, total=float(L[-1]), side=side)
    _LINE_CACHE[key] = out
    return out


def _sample_line(ln, q, col):
    return np.interp(q, ln["L"], ln[col])


def _sample_pt(ln, q):
    return np.stack([np.interp(q, ln["L"], ln["P"][:, c]) for c in range(3)], axis=-1)


def element_length(R):
    for (lim, L) in ELEMENT_L:
        if R < lim:
            return L
    return ELEMENT_L[-1][1]


class Panel(object):
    __slots__ = ("i", "L0", "L1", "s0", "s1", "sm", "side", "nom", "lap0",
                 "lap1", "nrail", "run", "closure", "lod", "post_local")

    def __repr__(self):
        return "<Panel %s s=%.1f L=%.3f rails=%d lod=%d%s>" % (
            "L" if self.side > 0 else "R", self.sm, self.L1 - self.L0,
            self.nrail, self.lod, " closure" if self.closure else "")


def _armco_runs(ln):
    """[(L_start, L_end)] of continuous Armco, broken at the marshal gates."""
    m = ln["btype"] == C.B_ARMCO
    L = ln["L"]
    s = ln["s"]
    # cut a GATE_CLEAR_M opening at every marshal gate station
    for gs in GATE_STATIONS:
        du = np.abs(((s - gs + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5)
        m &= ~(du < GATE_CLEAR_M * 0.5)
    d = np.diff(np.concatenate([[0], m.astype(int), [0]]))
    st = np.where(d == 1)[0]
    en = np.where(d == -1)[0]
    out = []
    for a, b in zip(st, en):
        b = min(b, len(L) - 1)
        if L[b] - L[a] > 2.4:
            out.append((float(L[a]), float(L[b])))
    return out


def panels(side):
    """The element breakdown for one side.  See ELEMENT_L for the radius bands.

    Every run is set out from its own start, so a run whose length is not a
    whole number of elements finishes on a CLOSURE element of whatever is left
    -- which is what happens on site, and is a third of this item's dimensional
    variation.
    """
    ln = barrier_line(side)
    out = []
    idx = 0
    for (ra, rb) in _armco_runs(ln):
        q = ra
        while q < rb - 0.35:
            R = float(_sample_line(ln, q + 1.0, "R"))
            nom = element_length(R)
            jitter = 0.965 + 0.070 * h01(4400 + (side > 0), idx, 3)
            step = nom * jitter
            closure = False
            # CLOSURE.  A run never divides into a whole number of elements, so
            # the fitters shorten the last TWO rather than leaving a 0.3 m
            # offcut or stretching one to 6.2 m -- both of which the first
            # version produced, and neither of which is a guardrail element.
            rem = rb - q
            if rem < step * 1.65:
                if rem >= 2.10:
                    step = rem * 0.5
                else:
                    step = rem
                closure = True
            p = Panel()
            p.i = idx
            p.L0, p.L1 = q, q + step
            p.side = side
            p.nom = nom
            p.closure = closure or (q <= ra + 1e-6)
            p.s0 = float(_sample_line(ln, p.L0, "s"))
            p.s1 = float(_sample_line(ln, min(p.L1, ln["total"]), "s"))
            p.sm = float(_sample_line(ln, 0.5 * (p.L0 + p.L1), "s"))
            p.lap0 = q > ra + 1e-6
            p.lap1 = (q + step) < rb - 0.35
            p.nrail = int(rail_count(np.array([p.sm]), side)[0])
            p.run = int(HIST.run_id(p.sm, side))
            # POSTS.  A W-beam splice is made AT a post: the post bolt goes
            # through the middle of the 320 mm lap and the eight splice bolts
            # sit in two columns either side of it.  So the joint post is at
            # the LAP CENTRE, not at the node -- putting it at the node moves
            # the whole bolt pattern half a lap upstream and leaves one column
            # of four hanging off the end of the sheet, which is what the
            # first build did.  Plus a mid-element post on anything long
            # enough, which is what a 2.00 m post pitch means on a 4 m element.
            hp = SPLICE_LAP_M * 0.5 if p.lap0 else 0.0
            p.post_local = [hp] + ([hp + step * 0.5] if step > 3.0 else [])
            p.lod = 3
            out.append(p)
            idx += 1
            q += step
    return out


def _grade_lod(pl, anchor):
    """Distance-graded mesh density.  `anchor` = the camera path, world points."""
    if anchor is None or not len(anchor):
        for p in pl:
            p.lod = 2
        return
    A = np.asarray(anchor, float)
    for p in pl:
        ln = barrier_line(p.side)
        c = _sample_pt(ln, 0.5 * (p.L0 + p.L1))
        d = float(np.min(np.linalg.norm(A - c[None, :], axis=1)))
        p.lod = 0 if d < 5.0 else (1 if d < 22.0 else (2 if d < 110.0 else 3))


# ==============================================================================
#  5.  THE MOUNTING-POINT EXPORTS  (this is the FOUNDATION interface)
# ==============================================================================

def _frame(ln, q):
    """(origin, tangent, outward normal, up) on the barrier line at arc q."""
    o = _sample_pt(ln, q)
    a = _sample_pt(ln, q - 0.25)
    b = _sample_pt(ln, q + 0.25)
    t = b - a
    t[..., 2] = 0.0
    t = t / np.maximum(np.linalg.norm(t, axis=-1, keepdims=True), 1e-12)
    up = np.zeros_like(t)
    up[..., 2] = 1.0
    n = np.cross(t, up)                       # right of travel
    n = n * (-float(ln["side"]))              # -> away from the track
    n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    return o, t, n, up


def post_sites(side, pl=None):
    """Every post station on `side`.  ``armco_post`` and ``armco_spacer_block``
    build here; the post-bolt slot in the centre ridge is already punched."""
    ln = barrier_line(side)
    out = []
    for p in (pl if pl is not None else panels(side)):
        hz = RAIL_HZ3 if p.nrail == 3 else RAIL_HZ2
        for pl_ in p.post_local:
            q = p.L0 + pl_
            o, t, n, u = _frame(ln, q)
            s = float(_sample_line(ln, q, "s"))
            out.append(dict(s=s, arc=float(q), side=side, world=tuple(o),
                            tangent=tuple(t), normal=tuple(n), up=tuple(u),
                            ground_z=float(o[2]),
                            slot_z=[float(o[2] + h + 0.1560) for h in hz],
                            slot_w=POST_SLOT[0], slot_h=POST_SLOT[1],
                            nrail=p.nrail, panel=p.i))
    return out


def splice_sites(side, pl=None):
    """The 8 punched splice slots at every lapped joint.  ``armco_splice_bolt``
    puts a button head in each one; the slot is already a hole in the mesh."""
    ln = barrier_line(side)
    out = []
    for p in (pl if pl is not None else panels(side)):
        if not p.lap1:
            continue
        hz = RAIL_HZ3 if p.nrail == 3 else RAIL_HZ2
        q = p.L1 + SPLICE_LAP_M * 0.5          # the post at the lap centre
        o, t, n, u = _frame(ln, q)
        s = float(_sample_line(ln, q, "s"))
        for h in hz:
            for dx in (-SPLICE_DX, +SPLICE_DX):
                for v in SPLICE_V:
                    tt = _profile_t_at_v(v)
                    w = o + t * dx + n * tt + u * (h + v)
                    out.append(dict(s=s, side=side, world=tuple(w),
                                    normal=tuple(n), tangent=tuple(t),
                                    up=tuple(u), v=v, dx=dx, rail_z=h,
                                    slot_w=SPLICE_SLOT[0], slot_h=SPLICE_SLOT[1],
                                    panel=p.i))
    return out


def reflector_sites(side, pl=None):
    """Where ``armco_reflector`` clips on: the top lip of the top rail, at
    every second post, which is the 4 m spacing a circuit actually uses."""
    ln = barrier_line(side)
    out = []
    for p in (pl if pl is not None else panels(side)):
        if (p.i % 2) or p.closure:
            continue
        hz = RAIL_HZ3 if p.nrail == 3 else RAIL_HZ2
        q = p.L0 + (p.L1 - p.L0) * 0.5
        o, t, n, u = _frame(ln, q)
        w = o + n * EDGE_T + u * (hz[-1] + SEC_H)
        out.append(dict(s=float(_sample_line(ln, q, "s")), side=side,
                        world=tuple(w), normal=tuple(n), tangent=tuple(t),
                        up=tuple(u), panel=p.i))
    return out


def run_ends(side):
    """[(arc, world, direction, is_start)] -- where ``armco_terminal`` goes."""
    ln = barrier_line(side)
    out = []
    for (a, b) in _armco_runs(ln):
        for (q, st) in ((a, True), (b, False)):
            o, t, n, u = _frame(ln, q)
            out.append(dict(arc=float(q), world=tuple(o), tangent=tuple(t),
                            normal=tuple(n), up=tuple(u), is_start=st,
                            s=float(_sample_line(ln, q, "s")), side=side))
    return out


def _profile_t_at_v(v):
    """Depth of the sheet mid-surface at height v.  Used by the exports so a
    dependant's bolt lands ON the metal instead of 30 mm off it."""
    P = profile_mid()
    return float(np.interp(v, P[:, 1], P[:, 0])) if v <= SEC_H else EDGE_T


def face_point(s, side, height, panel_list=None):
    """World point on the TRAFFIC FACE of the barrier at station `s` and
    `height` above the local ground datum.  For ``advertising_board`` and
    ``scuff_mark_barrier``."""
    ln = barrier_line(side)
    q = float(np.interp(s % LAP_LEN, ln["s"], ln["L"]))
    o, t, n, u = _frame(ln, q)
    return tuple(o + u * height)


def spine_frame(p, ln, nxt, x):
    """Where a sheet is, at sheet-local arc `x`.  -> (origin (N,3), outward
    normal (N,3)).  Vectorised.

    THE SINGLE DEFINITION OF ELEMENT PLACEMENT.  `build_bay` meshes with it and
    `selftest` measures with it, so a lap-continuity check cannot pass against a
    re-derivation of the maths it is supposed to be checking.

    The element is a CHORD PINNED TO ITS TWO NODES, blended toward the barrier
    polyline by `fol` (a 4.00 m sheet barely bends, a 1.33 m sheet bends to the
    radius).  Through the 320 mm lap it follows the NEXT element's chord,
    because being bolted through eight holes to that sheet is what makes two
    sheets parallel.
    """
    x = np.atleast_1d(np.asarray(x, float))
    Lp = p.L1 - p.L0
    fol = FOLLOW.get(p.nom, 0.45)
    # THROUGH THE LAP, THE SHEET IS THE NEXT ELEMENT'S SHEET.  That means its
    # follow factor too, not just its chord.  Using this element's `fol` in the
    # lap and the neighbour's in its own head made the two disagree wherever the
    # nominal length changes -- 4.00 m (fol 0.15) butting a 1.33 m (fol 0.85) at
    # the entry to the T4 hairpin opened them 67.5 mm apart.  Every one of those
    # is a hole in the barrier, and there is one at every length transition
    # around the lap.
    fol_lap = FOLLOW.get(nxt.nom, 0.45) if nxt is not None else fol
    q = p.L0 + x
    O = _sample_pt(ln, q)
    a_ = _sample_pt(ln, q - 0.25)
    b_ = _sample_pt(ln, q + 0.25)
    T = b_ - a_
    T[:, 2] = 0.0
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    N = np.cross(T, np.array([0.0, 0.0, 1.0])[None, :]) * (-float(p.side))
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    def chord(qa, qb):
        A = _sample_pt(ln, qa)
        B = _sample_pt(ln, qb)
        d = (B - A).copy()
        d[2] = 0.0
        d /= max(np.linalg.norm(d), 1e-12)
        nn = np.cross(d, np.array([0.0, 0.0, 1.0])) * (-float(p.side))
        return A, B, nn / max(np.linalg.norm(nn), 1e-12)

    A0, B0, N0 = chord(p.L0, p.L1)
    if nxt is not None:
        A1, B1, N1 = chord(nxt.L0, nxt.L1)
        Ln = max(nxt.L1 - nxt.L0, 1e-9)
    else:
        A1, B1, N1, Ln = A0, B0, N0, max(Lp, 1e-9)
    lap = (x > Lp)[:, None]
    u0 = (x / max(Lp, 1e-9))[:, None]
    u1 = ((x - Lp) / Ln)[:, None]
    Och = np.where(lap, A1[None, :] + (B1 - A1)[None, :] * u1,
                   A0[None, :] + (B0 - A0)[None, :] * u0)
    Nch = np.where(lap, N1[None, :], N0[None, :])
    f = np.where(lap, fol_lap, fol)
    Ow = Och * (1.0 - f) + O * f
    Nw = Nch * (1.0 - f) + N * f
    Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)
    return Ow, Nw


# ==============================================================================
#  6.  THE PANEL MESHER
# ==============================================================================

def _long_samples(p, lod):
    """Longitudinal sample positions along one sheet, in metres from its head.

    Forced samples: both ends, the lap ramp, every post, every slot boundary,
    and a refinement wherever the incident field is changing fast.  Everything
    else is filled to the LOD's step.
    """
    step = LOD_TABLE[lod][3]
    slots = LOD_TABLE[lod][4]
    L = p.L1 - p.L0
    sheet = L + (SPLICE_LAP_M if p.lap1 else 0.0)
    forced = {0.0, sheet}
    if lod <= 2:
        # the lap step is 3.4 mm.  At LOD 3 the bay is over 110 m away, where
        # 3.4 mm is 0.12 px, so resolving the ramp there buys nothing and costs
        # three sections on 900 bays.
        forced.update([LAP_RAMP_M, SPLICE_LAP_M, SPLICE_LAP_M + LAP_RAMP_M])
    for pl_ in p.post_local:
        forced.add(pl_)
        if slots:
            forced.update([pl_ - POST_SLOT[0], pl_ + POST_SLOT[0]])
    if p.lap1:
        forced.update([L, L + SPLICE_LAP_M])
    if slots:
        for pl_ in p.post_local:
            for f in (-1.0, -0.62, -0.28, 0.0, 0.28, 0.62, 1.0):
                forced.add(pl_ + f * POST_SLOT[0] * 0.5)
    for xc in _splice_columns(p):
        for f in (-1.0, -0.62, -0.28, 0.0, 0.28, 0.62, 1.0):
            if slots:
                forced.add(xc + f * SPLICE_SLOT[0] * 0.5)
    forced = sorted(x for x in forced if -1e-6 <= x <= sheet + 1e-6)
    out = [forced[0]]
    for a, b in zip(forced[:-1], forced[1:]):
        if b - a < 1e-5:
            continue
        m = max(1, int(math.ceil((b - a) / step)))
        for j in range(1, m + 1):
            out.append(a + (b - a) * j / m)
    return np.array(out)


def _dent_profile(x_s, side, sheet_s0, sheet_s1):
    """Incident deformation sampled along a sheet, in STATION space."""
    dent, scuff, pmix, prgb, fresh = HIST.scars(x_s, side)
    return dent, scuff, pmix, prgb, fresh


def _splice_columns(p):
    """Sheet-local x of the two splice-bolt columns at each lap this sheet has.

    The columns straddle the POST at the centre of the lap, +-76 mm, which is
    the standard pattern: two columns of four bolts either side of the post
    bolt.  Both laps a sheet takes part in are covered -- the one at its head,
    where the upstream neighbour laps over it, and the one at its tail, where
    it laps over the downstream neighbour -- so the eight bolts at a joint pass
    through both sheets, which is the whole point of a splice.
    """
    L = p.L1 - p.L0
    cols = []
    if p.lap0:
        cols += [SPLICE_LAP_M * 0.5 - SPLICE_DX, SPLICE_LAP_M * 0.5 + SPLICE_DX]
    if p.lap1:
        cols += [L + SPLICE_LAP_M * 0.5 - SPLICE_DX,
                 L + SPLICE_LAP_M * 0.5 + SPLICE_DX]
    return cols


def _slot_rects(p, lod, rail_z_index):
    """[(xc, vc, a, b, kind)] slots on this sheet, in (x along sheet, v)."""
    if not LOD_TABLE[lod][4]:
        return []
    L = p.L1 - p.L0
    out = []
    for pl_ in p.post_local:
        out.append((pl_, 0.1560, POST_SLOT[0] * 0.5, POST_SLOT[1] * 0.5, "post"))
    for xc in _splice_columns(p):
        for v in SPLICE_V:
            out.append((xc, v, SPLICE_SLOT[0] * 0.5,
                        SPLICE_SLOT[1] * 0.5, "splice"))
    keep = []
    sheet = L + (SPLICE_LAP_M if p.lap1 else 0.0)
    for (xc, vc, a, b, k) in out:
        if xc - a > 0.004 and xc + a < sheet - 0.004:
            keep.append((xc, vc, a, b, k))
    return keep


def build_rail(p, ln, rail_z, lod, sec, dmg):
    """One W-beam rail of one bay -> (verts (N,3) LOCAL, quads (M,4), attrs).

    Local frame: +X along the panel from its head, +Y away from the track,
    +Z up.  The caller turns that into the object matrix.
    """
    X = _long_samples(p, lod)
    nx = len(X)
    K = sec["nloop"]
    Pl = sec["P"]                          # (K,2) in (t, v)
    Nl = sec["N"]

    # ---- longitudinal fields ------------------------------------------------
    sheet = X[-1]
    Lp = p.L1 - p.L0
    q = p.L0 + X                                    # arc position on the line
    s_of = np.interp(q, ln["L"], ln["s"])
    dent, scuff, pmix, prgb, fresh = dmg(s_of)

    # 1. THE LAP.  The head of every sheet steps BACK by one thickness so the
    #    upstream neighbour laps OVER it: a car sliding downstream never meets
    #    an exposed edge.  Uniform treatment => no cumulative drift.
    lap_w = np.zeros(nx)
    if p.lap0:
        lap_w = 1.0 - smoothstep(SPLICE_LAP_M, SPLICE_LAP_M + LAP_RAMP_M, X)
    t_lap = lap_w * (SEC_T + 0.0004)

    # 2. SAG between posts, and the post hold-points
    posts = np.array(list(p.post_local) + [p.post_local[0] + Lp])
    tin = np.zeros(nx)
    for a, b in zip(posts[:-1], posts[1:]):
        m = (X >= a) & (X <= b)
        if b - a > 1e-6:
            tin[m] = (X[m] - a) / (b - a)
    sag = -SAG_M * (0.55 + 0.9 * h01(7301, p.i, p.side > 0)) * np.sin(np.pi * tin)

    # 3. ROLL-FORMING FLATNESS.  Thin sheet is never flat between the stiff
    #    corrugations; this is the difference between "steel" and "extrusion".
    oil = OILCAN_M * (fbm1(X * 6.2 + p.i * 31.7, seed=911 + p.i, oct=3) - 0.5) * 2.0

    # 4. DAMAGE.  Five consequences, not one.
    hold = np.sin(np.pi * np.clip(tin, 0, 1)) ** 0.6
    push = dent * (0.55 + 0.45 * hold) * (0.60 + 0.80 * vnoise1(q * 0.9, 331))
    # PLASTIC HINGE.  3 mm sheet does not fair out of a dent -- it yields at a
    # line and stays straight either side of it.  Sharpening the lobe with a
    # tanh of its own normalised depth turns the gaussian bruise a smooth
    # displacement would give into the creased, faceted thing a car leaves.
    if push.max() > 0.004:
        pn = push / max(push.max(), 1e-9)
        push = push.max() * (np.tanh((pn - 0.34) * 3.6) * 0.5 + 0.5) \
            * np.clip(pn * 2.4, 0, 1)
    flat = clamp01(push / 0.120) * DENT_FLATTEN            # corrugation eaten
    drop = -DENT_DRAG * push                               # dragged down
    buck = np.zeros(nx)
    if push.max() > 0.06:
        lam = BUCKLE_LAM[0] + (BUCKLE_LAM[1] - BUCKLE_LAM[0]) * h01(881, p.i, 5)
        buck = BUCKLE_AMP * clamp01((push - 0.06) / 0.13) * np.sin(
            2.0 * np.pi * (X / lam + h01(881, p.i, 9)))

    # 5. ERECTION.  Each element is set out by hand off a string line.
    e_lat = ERECT_LAT_M * (h01(6101, p.i, p.side > 0) - 0.5) * 2.0
    e_roll = math.radians(ERECT_ROLL_DEG) * (h01(6101, p.i, 17) - 0.5) * 2.0

    # ---- the swept grid -----------------------------------------------------
    tt = Pl[:, 0][None, :]
    vv = Pl[:, 1][None, :]
    amp = (1.0 - flat)[:, None]
    # the corrugation flattens toward the EDGE plane, which is what a car does:
    # the valleys are pushed back and the ridge pulled forward.
    tloc = EDGE_T + (tt - EDGE_T) * amp
    vloc = vv + np.zeros((nx, 1))

    # oil-canning only on the flats
    tloc = tloc + (oil[:, None] * (1.0 - sec["arcw"])[None, :])
    # edge buckling: maximum at the lips, zero at the post-bearing ridge
    wedge = (np.abs(vv - SEC_H * 0.5) / (SEC_H * 0.5)) ** 1.6
    tloc = tloc + buck[:, None] * wedge
    # bodily push-back, lap step, sag
    tloc = tloc + (push + t_lap + sag + e_lat)[:, None]
    vloc = vloc + drop[:, None]
    # element roll
    cz = SEC_H * 0.5
    tloc, vloc = (tloc + (vloc - cz) * math.sin(e_roll),
                  vloc - (tloc - EDGE_T) * math.sin(e_roll))

    V = np.empty((nx, K, 3), np.float64)
    V[:, :, 0] = X[:, None]
    V[:, :, 1] = tloc
    V[:, :, 2] = vloc + rail_z

    # ---- attributes ---------------------------------------------------------
    age = HIST.age_at(s_of, p.side)
    rust = clamp01((age - 0.40) * 1.75 + 0.25 * scuff
                   + 0.34 * (fbm1(s_of / 11.0, seed=1201, oct=3) - 0.5))
    A = {}
    ones_k = np.ones(K)
    A["awb_age"] = np.outer(age, ones_k)
    A["awb_rust"] = np.outer(rust, ones_k)
    A["awb_dent"] = np.outer(clamp01(push / 0.19), ones_k)
    A["awb_pmix"] = np.outer(pmix, ones_k)
    A["awb_fresh"] = np.outer(fresh, ones_k)
    A["awb_lap"] = np.outer(lap_w, ones_k)
    # scuff is a BAND: a car hits the barrier with its wheel and its flank, and
    # the band sits where the car's shoulder is -- 0.30 to 0.90 m over the
    # ground for the 2.005 m wide, 0.340 m ride-height car this film is about.
    zz = (vloc + rail_z)
    band = np.exp(-0.5 * ((zz - 0.58) / 0.31) ** 2)
    A["awb_scuff"] = np.outer(scuff, ones_k) * band * sec["face"][None, :]
    A["awb_pocket"] = np.tile(sec["pocket"], (nx, 1))
    A["awb_upz"] = np.tile(sec["upz"], (nx, 1))
    A["awb_edge"] = np.tile(sec["edge"], (nx, 1))
    A["awb_face"] = np.tile(sec["face"], (nx, 1))

    # ---- slots --------------------------------------------------------------
    # The slot field is computed for EVERY lod -- below LOD 1 the hole is not
    # cut, but the punching is still where the rust starts, and a 30 mm slot at
    # 110 m is 1.0 px: the right answer there is a shading feature, not a hole,
    # and pretending it does not exist would put a clean rail behind a dirty one.
    slots_all = _slot_rects(p, 0, 0)
    sl = np.zeros((nx, K))
    for (xc, vc, a, b, _k) in slots_all:
        dx = (X[:, None] - xc) / (a * 2.6)
        dv = (vv - vc) / (b * 3.4)
        below = np.clip((vc - vv) / 0.055, 0.0, 1.0)
        sl = np.maximum(sl, np.exp(-(dx * dx + dv * dv)) * (0.35 + 0.65 * below))
    A["awb_slot"] = clamp01(sl) * np.ones((nx, 1))

    slots = _slot_rects(p, lod, 0)
    quads = _grid_with_slots(V, sec, X, slots)
    return V.reshape(-1, 3), quads, {k: v.reshape(-1) for k, v in A.items()}, X


def _grid_with_slots(V, sec, X, slots):
    """Quad connectivity for the swept grid, with real punched holes.

    THE METHOD.  Cells whose centre falls inside a slot are deleted; the
    boundary vertices of the hole are then PROJECTED onto the slot's ellipse,
    which turns a staircase into an exact oval without adding a single vertex
    and without a T-junction anywhere.  The metal being drawn in around a punch
    is what actually happens, so the mild distortion of the ring of cells around
    the hole is not an artefact -- it is the die.

    The front and back sheets share a MID-PATH index, so the two boundary loops
    are walked in (column, mid-index) space and are in 1:1 correspondence by
    construction.  The punched wall bridges them directly, and the die roll on
    the entry face and the burr on the exit face go on here too.
    """
    nx, K = V.shape[0], V.shape[1]
    ii, kk = np.meshgrid(np.arange(nx - 1), np.arange(K), indexing="ij")
    q = np.stack([ii * K + kk,
                  ii * K + (kk + 1) % K,
                  (ii + 1) * K + (kk + 1) % K,
                  (ii + 1) * K + kk], axis=-1).reshape(-1, 4)
    if not slots:
        return q

    IF, IB = sec["IF"], sec["IB"]
    vprof = sec["vprof"]
    Km = sec["K"]
    kill = np.zeros((nx - 1, K), bool)
    walls = []
    cellc_x = 0.5 * (X[:-1] + X[1:])

    for (xc, vc, a, b, kind) in slots:
        js = np.where(np.abs(vprof - vc) < b)[0]
        if len(js) < 3:
            continue
        j0, j1 = int(js[0]), int(js[-1])
        icell = np.where((cellc_x > xc - a) & (cellc_x < xc + a))[0]
        if len(icell) < 2:
            continue
        i0, i1 = int(icell[0]), int(icell[-1]) + 1

        # cells to delete, in loop-index space, on both sheets
        kf0, kf1 = int(IF[j0]), int(IF[j1])
        kb0, kb1 = int(IB[j1]), int(IB[j0])
        kill[i0:i1, min(kf0, kf1):max(kf0, kf1)] = True
        kill[i0:i1, min(kb0, kb1):max(kb0, kb1)] = True

        # the boundary walk, in (column, mid index) -- identical on both sheets
        walk = ([(i, j0) for i in range(i0, i1 + 1)]
                + [(i1, j) for j in range(j0 + 1, j1 + 1)]
                + [(i, j1) for i in range(i1 - 1, i0 - 1, -1)]
                + [(i0, j) for j in range(j1 - 1, j0, -1)])

        # project onto the slot ellipse, in PROFILE space so the corrugation
        # and the damage displacement are untouched
        for (i, j) in walk:
            for (lut, sgn) in ((IF, +1.0), (IB, -1.0)):
                kc = int(lut[j])
                dx = X[i] - xc
                dvp = vprof[j] - vc
                r = math.hypot(dx / max(a, 1e-9), dvp / max(b, 1e-9))
                if r < 1e-9:
                    continue
                V[i, kc, 0] = xc + dx / r
                V[i, kc, 2] += (dvp / r - dvp)
                # die roll on the entry (traffic) face, burr on the exit face
                V[i, kc, 1] += (SLOT_DIE_ROLL if sgn > 0 else SLOT_BURR) * sgn
        walls.append((walk, IF, IB))

    q = q.reshape(nx - 1, K, 4)[~kill]
    extra = []
    for (walk, lutf, lutb) in walls:
        n = len(walk)
        for j in range(n):
            i_a, j_a = walk[j]
            i_b, j_b = walk[(j + 1) % n]
            f0 = i_a * K + int(lutf[j_a])
            f1 = i_b * K + int(lutf[j_b])
            b0 = i_a * K + int(lutb[j_a])
            b1 = i_b * K + int(lutb[j_b])
            if f0 == f1 and b0 == b1:
                continue
            extra.append((f0, f1, b1, b0))
    if extra:
        q = np.vstack([q, np.array(extra, np.int64)])
    return q


def _end_caps(nx, K, sec):
    """The sheared ends of the sheet: a 3 mm strip of real metal, not an open
    shell.  The two hems are fanned so the cap closes completely -- the first
    version bridged only front-to-back and left two half-discs open at every
    end of every rail, which is where 568 non-manifold edges came from."""
    IF, IB = sec["IF"], sec["IB"]
    Km = sec["K"]
    out = []
    for (i0, flip) in ((0, False), (nx - 1, True)):
        base = i0 * K
        for j in range(Km - 1):
            a0 = base + int(IF[j])
            a1 = base + int(IF[j + 1])
            b0 = base + int(IB[j])
            b1 = base + int(IB[j + 1])
            out.append((a0, a1, b1, b0) if not flip else (a0, b0, b1, a1))
    tris = []
    for (i0, flip) in ((0, False), (nx - 1, True)):
        base = i0 * K
        for hem in (sec["HEMT"], sec["HEMB"]):
            c = base + hem[0]
            for j in range(1, len(hem) - 1):
                p = base + hem[j]
                r = base + hem[j + 1]
                tris.append((c, p, r) if not flip else (c, r, p))
    return (np.array(out, np.int64) if out else np.zeros((0, 4), np.int64),
            np.array(tris, np.int64) if tris else np.zeros((0, 3), np.int64))


# ==============================================================================
#  7.  EMITTING A BAY
# ==============================================================================

def _new_mesh(name, verts, quads=None, tris=None, recalc=True,
              smooth_deg=34.0):
    """Fast mesh build, then ONE bmesh pass to make the normals consistent.

    `recalc` is not optional decoration.  A closed shell with a punched wall in
    it has three different families of face whose winding is decided by three
    different pieces of index arithmetic, and a single family emitted backwards
    is a black hole in the render that no gate measures.  bmesh already knows
    how to answer the question; the alternative is to be clever about it and be
    wrong somewhere.
    """
    me = bpy.data.meshes.new(name)
    verts = np.ascontiguousarray(verts, dtype=np.float32)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    polys, counts = [], []
    if quads is not None and len(quads):
        polys.append(np.asarray(quads, np.int32).ravel())
        counts.append(np.full(len(quads), 4, np.int32))
    if tris is not None and len(tris):
        polys.append(np.asarray(tris, np.int32).ravel())
        counts.append(np.full(len(tris), 3, np.int32))
    if polys:
        loops = np.concatenate(polys)
        counts = np.concatenate(counts)
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
        me.loops.add(len(loops))
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(len(counts))
        me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    if recalc and len(me.polygons):
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
    if smooth_deg is not None and len(me.polygons):
        _shade_by_angle(me, smooth_deg)
    return me


def _shade_by_angle(me, deg=34.0):
    """Smooth shading everywhere except across a real arris.

    A rolled W section is TANGENT-CONTINUOUS all the way round -- every fillet
    meets its straight at a shared tangent -- so flat shading it is simply
    wrong: it turns a 358-facet ring into 358 visible facets, each 1.5-4 mm
    wide, which at 1436 px/m is 2-6 px of banding on the one surface the whole
    item is judged by.  The genuinely sharp edges are the sheared end of the
    sheet and the wall of every punched slot, and those must stay sharp.

    Done in numpy against the `sharp_edge` attribute rather than through
    `shade_auto_smooth`, which needs a VIEW_3D context and therefore cannot run
    headless (see the project's Blender 5.x notes).
    """
    npoly = len(me.polygons)
    nloop = len(me.loops)
    nedge = len(me.edges)
    if not nedge:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))

    fn = np.empty(npoly * 3, np.float32)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32)
    me.loops.foreach_get("vertex_index", lv)

    # loop i -> (this vertex, next vertex within the same polygon)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64)
    b = lv[nxt].astype(np.int64)
    lo = np.minimum(a, b)
    hi = np.maximum(a, b)
    key = lo * np.int64(len(me.vertices)) + hi
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)

    order = np.argsort(key, kind="stable")
    ks = key[order]
    fs = face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    # first and (if present) second face of each edge group
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
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * np.int64(len(me.vertices))
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.searchsorted(sk, ekey)
        idx = np.clip(idx, 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _bake(me, attrs, uv):
    for name in ATTRS:
        if name not in attrs:
            continue
        a = me.attributes.new(name, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(attrs[name], np.float32))
    if uv is not None and len(me.loops):
        lay = me.uv_layers.new(name="awb_uv")
        li = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", li)
        lay.uv.foreach_set("vector",
                           np.ascontiguousarray(uv[li], np.float32).ravel())


def _object_props(ob, p, run_col, painted, pt_col, seed):
    ob["awb_painted"] = float(painted)
    ob["awb_run_r"], ob["awb_run_g"], ob["awb_run_b"] = [float(c) for c in run_col]
    ob["awb_pt_r"], ob["awb_pt_g"], ob["awb_pt_b"] = [float(c) for c in pt_col]
    # per-object texture offset: the ONLY thing that stops 1789 bays sharing one
    # spangle.  Object-space textures are the contract's rule; this is how you
    # keep them from being a rubber stamp.
    # 24 m, not 240.  Cycles evaluates procedurals in float32; at a Voronoi
    # scale of 38 an offset of 240 puts the lookup at 9120 units from the
    # origin, where float32 has ~1000 steps per 26 mm cell.  24 m keeps it at
    # 16 000 steps a cell and still gives every bay its own realisation out of
    # about 10^9 distinguishable ones.
    ob["awb_ofs_x"] = float(h01(seed, 3) * 24.0)
    ob["awb_ofs_y"] = float(h01(seed, 5) * 24.0)
    ob["awb_ofs_z"] = float(h01(seed, 7) * 24.0)
    ob["awb_seed"] = float(seed % 4096)
    ob["item"] = ITEM
    ob["awb_panel"] = int(p.i)
    ob["awb_side"] = int(p.side)
    ob["awb_station"] = float(p.sm)
    ob["awb_nrail"] = int(p.nrail)
    ob["awb_lod"] = int(p.lod)


def build_bay(p, coll, mat, sections, nxt=None):
    """One bay -> one object.  2 or 3 rails, one mesh, recentred."""
    ln = barrier_line(p.side)
    sec = sections[p.lod]
    hz = RAIL_HZ3 if p.nrail == 3 else RAIL_HZ2

    def dmg(s_of):
        return HIST.scars(s_of, p.side)

    VS, QS, TS, AS, UV = [], [], [], {k: [] for k in ATTRS}, []
    base = 0
    for ri, rz in enumerate(hz):
        V, Q, A, X = build_rail(p, ln, rz, p.lod, sec, dmg)
        nx = len(X)
        K = sec["nloop"]
        cq, ct = _end_caps(nx, K, sec)
        VS.append(V)
        QS.append(np.vstack([Q, cq]) + base)
        TS.append(ct + base)
        for k in ATTRS:
            AS[k].append(A[k])
        u = np.repeat(X, K)
        v = np.tile(sec["arc"], nx) + ri * 1.7
        UV.append(np.stack([u, v], axis=1))
        base += len(V)

    V = np.vstack(VS)
    Q = np.vstack(QS)
    TRI = np.vstack(TS)
    A = {k: np.concatenate(v) for k, v in AS.items()}
    UVa = np.vstack(UV)

    # ---- the barrier line is a curve; lay the sheet onto it -----------------
    #
    # THE LAP HAS TO BE CONTINUOUS.  Two sheets bolted face to face through a
    # 320 mm lap are PARALLEL in the lap; the direction change between elements
    # happens AT the splice, as a kink, not as a wedge.  The first version blended
    # each sheet between the polyline and a chord through its OWN mid frame, so
    # neither the ends nor the directions matched at a joint: on a 40 m radius a
    # 4 m element opened a 32 mm wedge over the lap, which at 1436 px/m is a 46 px
    # black gap at every single splice.  CAM_ALONG showed the barrier as a row of
    # separate plates.
    #
    # So: the chord is pinned to the two NODES (consecutive elements therefore
    # meet exactly), and over the lap the sheet follows the NEXT element's chord,
    # which is what being bolted to it means.
    L0, L1 = p.L0, p.L1
    Lp = L1 - L0
    sheet = Lp + (SPLICE_LAP_M if p.lap1 else 0.0)
    Ow, Nw = spine_frame(p, ln, nxt, V[:, 0])
    W = Ow + Nw * V[:, 1:2] + np.array([0.0, 0.0, 1.0])[None, :] * V[:, 2:3]
    o0, t0, n0, _u0 = _frame(ln, L0 + sheet * 0.5)

    # ---- recentre into a canonical local frame -----------------------------
    ctr = W.mean(axis=0)
    M = np.stack([t0, n0, np.array([0.0, 0.0, 1.0])], axis=1)   # columns
    Loc = (W - ctr[None, :]) @ M

    nm = "%sBay_%s%05d" % (PFX, "L" if p.side > 0 else "R", p.i)
    me = _new_mesh(nm, Loc, Q, TRI)
    _bake(me, A, UVa)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nm, me)
    ob.location = tuple(float(x) for x in ctr)
    ob.rotation_mode = "QUATERNION"
    from mathutils import Matrix
    ob.rotation_quaternion = Matrix(((M[0][0], M[0][1], M[0][2]),
                                     (M[1][0], M[1][1], M[1][2]),
                                     (M[2][0], M[2][1], M[2][2]))).to_quaternion()

    flag, hue = run_paint(np.array([p.run]))
    painted = float(flag[0])
    run_col = livery_of(float(hue[0]))
    _, _, pmix, prgb, _ = HIST.scars(np.array([p.sm]), p.side)
    pt = tuple(prgb[0]) if pmix[0] > 0.01 else (0.5, 0.5, 0.5)
    _object_props(ob, p, run_col, painted, pt, SEED + p.i * 17 + (p.side > 0) * 7919)
    coll.objects.link(ob)
    return ob, len(V), len(Q) + len(TRI)


# ==============================================================================
#  8.  THE MATERIAL
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
        self.col = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 1
        nd.location = ((self.x % 14) * 220, -(self.x // 14) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, idx, src):
        if src is None:
            return
        while isinstance(src, tuple) and len(src) == 2 and isinstance(src[0], tuple):
            src = src[0]                  # a helper's (node, socket) double-wrapped
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[idx].default_value = float(src)

    # --- typed helpers, each returning a (node, socket) pair ----------------
    def pin_named(self, nd, name, src):
        """`pin`, addressing the socket BY NAME, and RAISING if it is gone.

        R2-057.  This class is a private copy of itemkit's node DSL, so
        itemkit's socket check -- which asserts the indices ITEMKIT assumes --
        is blind to every index used here.  Blender 5.2 moved
        ShaderNodeBsdfPrincipled's `Normal` from 5 to 6 (a `Thin Wall` socket
        was inserted at 5); the modules that still said 5 delivered their whole
        bump chain into `Thin Wall` and rendered plausibly with no relief at
        all.  The indices in this file happened to be right; being right by
        luck is not a property worth keeping, so the socket that moves is now
        addressed by the name that does not.
        """
        if src is None:
            return
        for i, s in enumerate(nd.inputs):
            if s.name == name:
                return self.pin(nd, i, src)
        raise RuntimeError(
            "%s has no input named %r; it has %s"
            % (nd.bl_idname, name, [s.name for s in nd.inputs]))

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

    def noisec(self, vec, scale, detail=6.0, rough=0.5):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 3, detail)
        self.pin(nd, 4, rough)
        return (nd, 1)

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

    def bevel(self, radius, samples=8):
        nd = self.n("ShaderNodeBevel")
        nd.samples = samples
        self.pin(nd, 0, radius)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)


# Linear reflectances.  Hot-dip zinc is DARKER than intuition says: a fresh
# spangled coat measures 0.55-0.65 specular but only ~0.30 diffuse, and it goes
# to 0.18-0.22 within a year as the carbonate patina forms.  A guardrail that
# reads as white in a render is a guardrail with the albedo of paper.
PAL = dict(
    # THESE ARE METAL F0 TINTS, NOT DIFFUSE ALBEDOS.  Zinc's normal-incidence
    # reflectance is ~0.55 broadband and weathered zinc is duller; the numbers
    # below are what the crystal facets return once six years of dulling is in
    # them.  They are deliberately higher than the first build's, which set
    # them as if they were diffuse albedos and then drove `metal` to 0.13 with
    # the weathering masks -- between the two the rail rendered as painted
    # plaster.  A metal that is not metallic is the thing that reads wrong.
    zinc_fresh=(0.4000, 0.4100, 0.4250),
    zinc_dull=(0.2550, 0.2620, 0.2750),
    zinc_dark=(0.1500, 0.1550, 0.1650),
    white_rust=(0.2950, 0.2900, 0.2790),     # zinc carbonate bloom, chalky
    red_rust=(0.1020, 0.0405, 0.0180),
    rust_bright=(0.2050, 0.0860, 0.0335),
    steel_bare=(0.1450, 0.1450, 0.1500),     # a punched edge, zinc worn off
    grime=(0.0265, 0.0250, 0.0232),          # rubber + brake dust + road spray
    dust=(0.1220, 0.1090, 0.0885),
    rubber=(0.0215, 0.0208, 0.0205),
    lichen=(0.0900, 0.1030, 0.0640),
)


def mat_wbeam():
    """Hot-dip galvanised W-beam, six years outside beside a racing circuit.

    Eleven surface histories, in the order the metal acquired them, and no image
    anywhere:

        zinc spangle -> skin-pass roll marks -> carbonate patina, in the
        pockets first -> crevice corrosion in the lap -> red rust running down
        from the punchings and the cut ends -> road film, heavy low and on the
        traffic face -> rain wash cutting clean streaks through it -> enamel on
        the 30 % of runs that are painted -> chipping off every arris ->
        tyre-rubber and paint transfer at the scars -> burnish where a car has
        brushed it.

    TWO COORDINATE STREAMS, AND THE BUG THAT MADE THEM NECESSARY.  `OBJ` is the
    bay's own canonical frame -- +X along the panel, +Y away from the track, +Z
    UP -- and it is what every gravity-aligned and face-aligned effect reads.
    `NZ` is the same thing plus a per-object random offset, and it is what every
    noise reads, so that 1789 bays do not share one spangle.  The first version
    fed the OFFSET coordinate to the road film and the rust streaks, so `pz`
    was a random number between 0 and 240 instead of the height above the
    ground, and every height-dependent layer in the shader silently switched
    off.  The rail came back looking like painted cream.
    """
    name = PFX + "WBeam"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)                                   # Object -- NEVER Position

    ofs = t.comb(t.attr("awb_ofs_x", 2, "OBJECT"),
                 t.attr("awb_ofs_y", 2, "OBJECT"),
                 t.attr("awb_ofs_z", 2, "OBJECT"))
    NZ = t.vmath("ADD", OBJ, ofs)
    pz = t.sep(OBJ, 2)                  # height above the bay centre, metres
    px = t.sep(OBJ, 0)                  # along the panel
    py = t.sep(OBJ, 1)                  # out from the track

    age = t.attr("awb_age")
    rust_a = t.attr("awb_rust")
    scuff = t.attr("awb_scuff")
    pmix = t.attr("awb_pmix")
    fresh = t.attr("awb_fresh")
    dent = t.attr("awb_dent")
    pocket = t.attr("awb_pocket")
    upz = t.attr("awb_upz")
    edgea = t.attr("awb_edge")
    lapa = t.attr("awb_lap")
    slota = t.attr("awb_slot")
    facea = t.attr("awb_face")

    painted = t.attr("awb_painted", 2, "OBJECT")
    runcol = t.comb(t.attr("awb_run_r", 2, "OBJECT"),
                    t.attr("awb_run_g", 2, "OBJECT"),
                    t.attr("awb_run_b", 2, "OBJECT"))
    ptcol = t.comb(t.attr("awb_pt_r", 2, "OBJECT"),
                   t.attr("awb_pt_g", 2, "OBJECT"),
                   t.attr("awb_pt_b", 2, "OBJECT"))

    # ---------------------------------------------------------------- 1. ZINC
    # Hot-dip spangle: dendritic zinc crystals.  On a 3 mm sheet dipped at
    # 450 C the crystals run 6-40 mm, which at 1436 px/m is 9-57 px -- the
    # single most identifying feature of galvanised steel at this distance, and
    # the reason a flat grey metal reads as aluminium.
    spang_d = t.vor(NZ, 38.0, "F1", 0, 0.95)
    spang_c = t.vor(NZ, 38.0, "F1", 1, 0.95)
    cellv = t.sep(spang_c, 0)
    cellw = t.sep(spang_c, 1)
    # dendrite arms: a strongly anisotropic noise, oriented per crystal
    dend = t.noise(t.vmath("SCALE", NZ, scale=4.6), 165.0, 5.0, 0.74, dist=1.3)
    fine = t.noise(NZ, 700.0, 3.0, 0.5)

    zinc_base = t.cmix(t.maprange(cellv, 0.08, 0.92, 0.0, 1.0),
                       PAL["zinc_dull"], PAL["zinc_fresh"])
    zinc_base = t.cmix(t.maprange(dend, 0.32, 0.70, 0.0, 0.85),
                       zinc_base, PAL["zinc_dark"])

    # skin-pass / roll-forming marks: fine lines ALONG the panel
    # Skin-pass marks run ALONG the panel (the rolling direction), so the
    # bands vary with height: 1.6 mm pitch = 2.3 px at the filmed distance.
    roll = t.wave(t.comb(t.sep(NZ, 2), t.sep(NZ, 1), t.sep(NZ, 0)),
                  2500.0, 0.7, 2.0)

    # ------------------------------------------------------- 2. AGE / PATINA
    # White rust is a BLOTCH, not a wash.  It grows where water sits and dries:
    # the two valley pockets, behind both lips, and in the lap crevice.  Making
    # it uniform is what turned the first render into painted cream.
    wet = t.math("ADD", t.math("MULTIPLY", pocket, 1.35),
                 t.math("MULTIPLY", lapa, 0.95), clamp=True)
    blot = t.noise(t.vmath("SCALE", NZ, scale=1.0), 9.0, 9.0, 0.68)
    blot2 = t.noise(t.vmath("SCALE", NZ, scale=1.0), 48.0, 7.0, 0.60)
    wr = t.math("MULTIPLY", age, t.math("ADD", t.math("MULTIPLY", wet, 0.85),
                                        0.16))
    # The thresholds decide COVERAGE.  An old rail is 25-45 % bloomed, in
    # patches; at 0.42/0.34 the first build had it at essentially 100 % and the
    # whole barrier went the colour of chalk.
    wr = t.math("MULTIPLY", wr, t.maprange(blot, 0.52, 0.82, 0.00, 1.25))
    wr = t.math("MULTIPLY", wr, t.maprange(blot2, 0.40, 0.80, 0.08, 1.15),
                clamp=True)
    wr = t.math("MULTIPLY", wr, t.math("SUBTRACT", 1.0,
                                       t.math("MULTIPLY", fresh, 0.94)),
                clamp=True)
    col = t.cmix(wr, zinc_base, PAL["white_rust"])

    # ------------------------------------------------ 3. RUNNING RED RUST
    # Red rust only starts where the zinc is thin or gone: the punched slot
    # walls, the sheared ends, the deep scars.  Then it RUNS DOWN.  The streak
    # is a vertical stretch of noise in the bay's OWN frame, which is exactly
    # why that frame is canonical and why the offset does not go in here.
    streak = t.noise(t.comb(t.math("MULTIPLY", t.sep(NZ, 0), 6.5),
                            t.sep(NZ, 1),
                            t.math("MULTIPLY", t.sep(NZ, 2), 0.14)),
                     52.0, 8.0, 0.70)
    src = t.math("ADD", t.math("MULTIPLY", slota, 1.15),
                 t.math("MULTIPLY", dent, 0.70), clamp=True)
    src = t.math("ADD", src, t.math("MULTIPLY", edgea, 0.40), clamp=True)
    run = t.math("MULTIPLY", src, t.maprange(streak, 0.30, 0.66, 0.0, 1.5))
    run = t.math("MULTIPLY", run, t.math("ADD", t.math("MULTIPLY", rust_a, 0.95),
                                         0.35), clamp=True)
    rustcol = t.cmix(t.maprange(blot2, 0.3, 0.7, 0.0, 1.0),
                     PAL["red_rust"], PAL["rust_bright"])
    col = t.cmix(run, col, rustcol)
    # bare steel in the punchings themselves
    col = t.cmix(t.math("MULTIPLY", slota,
                        t.maprange(slota, 0.74, 0.99, 0.0, 0.90)),
                 col, PAL["steel_bare"])

    # ---------------------------------------------------------- 4. ROAD FILM
    # A barrier 30 m from a racing surface is filthy.  Rubber dust, brake dust
    # and road spray, heaviest at the bottom and on the traffic face, cut
    # through by the rain that sheets off the two lips and the ridge.
    lowz = t.maprange(pz, -0.48, 0.06, 1.05, 0.10)
    splat = t.vor(t.vmath("SCALE", NZ, scale=1.0), 30.0, "F1", 0, 1.0)
    film = t.math("MULTIPLY", lowz, t.maprange(splat, 0.04, 0.50, 1.25, 0.30))
    film = t.math("MULTIPLY", film,
                  t.math("ADD", t.math("MULTIPLY", facea, 0.60), 0.42))
    # rain wash: vertical clean streaks under the lips
    wash = t.wave(t.comb(t.math("MULTIPLY", t.sep(NZ, 0), 1.0),
                         t.math("MULTIPLY", t.sep(NZ, 2), 0.12),
                         t.sep(NZ, 1)), 26.0, 2.8, 3.0, "X")
    film = t.math("MULTIPLY", film, t.maprange(wash, 0.15, 0.92, 0.70, 1.18))
    film = t.math("MULTIPLY", film,
                  t.math("ADD", t.math("MULTIPLY", age, 0.50), 0.55), clamp=True)
    col = t.cmix(t.math("MULTIPLY", film, 0.82), col, PAL["grime"])
    # a dry dust film on the up-facing top lip and the ridge shelf
    dustm = t.math("MULTIPLY", t.maprange(upz, 0.30, 0.96, 0.0, 1.0),
                   t.maprange(blot2, 0.30, 0.82, 0.10, 0.95))
    col = t.cmix(t.math("MULTIPLY", dustm, 0.50), col, PAL["dust"])

    # ------------------------------------------------------------- 5. LICHEN
    lich = t.vor(t.vmath("SCALE", NZ, scale=1.0), 90.0, "F1", 0, 1.0)
    lm = t.math("MULTIPLY", t.math("MULTIPLY", age, pocket),
                t.maprange(lich, 0.02, 0.24, 1.0, 0.0))
    lm = t.math("MULTIPLY", lm, t.maprange(pz, 0.10, -0.35, 0.0, 1.0), clamp=True)
    col = t.cmix(t.math("MULTIPLY", lm, 0.85), col, PAL["lichen"])

    # -------------------------------------------------------------- 6. PAINT
    # Enamel over galvanising adheres badly: it chalks, it chips off every
    # arris, and it flakes wherever the metal has been struck.
    chip_n = t.noise(t.vmath("SCALE", NZ, scale=1.0), 175.0, 8.0, 0.68)
    bev = t.bevel(0.0035, 10)
    geo = t.n("ShaderNodeNewGeometry")
    facing = t.vmath("DOT_PRODUCT", bev, (geo, 1))
    edgew = t.maprange((facing[0], 1), 0.62, 0.995, 1.0, 0.0)
    chip = t.math("MULTIPLY",
                  t.math("ADD", t.math("MULTIPLY", edgea, 0.85), edgew),
                  t.maprange(chip_n, 0.36, 0.72, 0.10, 1.5))
    chip = t.math("ADD", chip, t.math("MULTIPLY", dent, 1.25), clamp=True)
    chip = t.math("MULTIPLY", chip,
                  t.math("ADD", t.math("MULTIPLY", age, 0.95), 0.22), clamp=True)
    chalk = t.math("MULTIPLY", age, 0.60)
    pcol = t.cmix(chalk, runcol, (0.360, 0.352, 0.336))
    pcol = t.cmix(t.math("MULTIPLY", t.maprange(blot, 0.32, 0.78, 0.0, 1.0),
                         0.34), pcol, (0.250, 0.245, 0.236))
    pmask = t.math("MULTIPLY", painted, t.math("SUBTRACT", 1.0, chip, clamp=True))
    col = t.cmix(pmask, col, pcol)

    # ------------------------------------- 7. TRANSFER AND BURNISH AT A SCAR
    trans = t.math("MULTIPLY", pmix,
                   t.maprange(t.noise(t.vmath("SCALE", NZ, scale=1.0),
                                      230.0, 5.0, 0.6), 0.30, 0.74, 0.15, 1.35))
    col = t.cmix(t.math("MULTIPLY", trans, 0.90), col, ptcol)
    # rubber laid on in streaks ALONG the barrier, which is how it gets there
    rub = t.math("MULTIPLY", scuff,
                 t.maprange(t.wave(t.comb(t.math("MULTIPLY", t.sep(NZ, 0), 1.0),
                                          t.math("MULTIPLY", t.sep(NZ, 2), 0.05),
                                          t.sep(NZ, 1)), 300.0, 3.8, 2.0),
                            0.22, 0.82, 0.10, 1.0))
    col = t.cmix(t.math("MULTIPLY", rub, 0.78), col, PAL["rubber"])
    burn = t.math("MULTIPLY", scuff, t.math("SUBTRACT", 1.0, rub, clamp=True))
    col = t.cmix(t.math("MULTIPLY", burn, 0.55), col, (0.3450, 0.3500, 0.3560))

    # ----------------------------------------------------------- ROUGHNESS
    rough = t.maprange(cellw, 0.0, 1.0, 0.33, 0.55)
    rough = t.math("ADD", rough, t.math("MULTIPLY",
                                        t.maprange(roll, 0.2, 0.8, -0.05, 0.05),
                                        1.0))
    rough = t.fmix(t.math("MULTIPLY", wr, 0.95), rough, 0.88)          # chalky
    rough = t.fmix(t.math("MULTIPLY", run, 0.95), rough, 0.93)          # rust
    rough = t.fmix(t.math("MULTIPLY", film, 0.9), rough, 0.80)
    rough = t.fmix(pmask, rough, t.fmix(chalk, 0.30, 0.76))
    rough = t.fmix(t.math("MULTIPLY", burn, 0.9), rough, 0.11)          # polished
    rough = t.fmix(t.math("MULTIPLY", rub, 0.75), rough, 0.58)
    rough = t.math("MULTIPLY", rough,
                   t.maprange(t.noise(t.vmath("SCALE", NZ, scale=1.0),
                                      380.0, 6.0, 0.55), 0.3, 0.7, 0.90, 1.10),
                   clamp=True)

    # Zinc is a metal; everything that has grown ON it is not -- but a
    # carbonate bloom and a film of road dust are THIN, and the metal still
    # answers through them.  Weighting them as full dielectric coverage is what
    # drove `metal` to 0.13 and turned a guardrail into a plaster wall.  Red
    # rust is the one that really is opaque.
    dielectric = t.math("ADD",
                        t.math("ADD", t.math("MULTIPLY", wr, 0.70),
                               t.math("MULTIPLY", run, 0.95), clamp=True),
                        t.math("ADD", t.math("MULTIPLY", film, 0.55),
                               t.math("MULTIPLY", lm, 1.0), clamp=True),
                        clamp=True)
    metal = t.fmix(pmask, t.fmix(dielectric, 0.94, 0.05), 0.0)

    # ------------------------------------------------------------- 8. BUMP
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES.  itemkit section 5b,
    # ITEM-CAMPAIGN-BRIEF 4a.  What the eye judges is what the bump does to the
    # LIGHT, and this film's 12.47 deg sun is a 4.52x amplifier on any slope:
    # m = 2 sin(theta) / tan(e).  Three amplitude sets were rendered and
    # REJECTED on the human figures, every one of them chosen in millimetres.
    #
    # NONE OF THESE FIVE IS A RE-TUNE.  Each `modulation_pp` reproduces the
    # Distance this module already shipped to better than 1e-6 relative; what
    # has changed is that the module now says what it is aiming the light at.
    #
    # A HEIGHT THAT IS A SUM HAS NO SINGLE WAVELENGTH, so each stage names ONE
    # band and `height_pp` is that band's own weight in the sum.  Every band,
    # at the shipped Distance:
    #
    #   [0] dend     w 0.45  lam  2.11 mm  m 1.640  dendrite arms      <- named
    #       spang_d  w 0.55  lam 57.11 mm  m 0.075  the crystal itself
    #   [1] roll     w 0.20  lam  0.13 mm  m 0.447  skin-pass marks    <- named
    #       fine     w 0.32  lam  2.29 mm  m 0.039  mill grain
    #   [2] pit      w 1.00  lam  1.68 mm  m 5.320  corrosion pitting  <- named
    #   [3] dpit     w 1.00  lam 26.67 mm  m 1.216  the scar's dimples <- named
    #   [4] chip_n   w 1.00  lam  9.14 mm  m 0.283  paint film         <- named
    #
    # [0] NAMES THE DENDRITE, NOT THE SPANGLE, even though the spangle carries
    # more of the height: at 57 mm the crystal's own swell is m 0.075 and does
    # essentially nothing, while the 2.11 mm dendrite grain at 1.640 is what the
    # stage actually does to the light.  Naming the quiet band would have put a
    # number in this call that the surface does not deliver.  1.640 is a hair
    # over the felt line and it is ungated -- but 0.124 mm p-p is the physically
    # right proudness for hot-dip dendrite arms, and the whole point of this
    # material is that galvanising glitters at a grazing sun.  Left alone,
    # flagged: it is the first stage to trim if the rail reads as felt.
    # [2] and [3] sit in RELIEF_BANDS["hard_feature"]/["sparse_crease"] and are
    # gated (`run`/`wr` rust, `dent`), so they act on a fraction of the area.
    # [1] is deliberately tiny for the reason written above it, and its `fine`
    # band at 0.039 is below the floor where a stage does anything at all.
    #
    # THE WAVELENGTHS COME FROM THE SAME LITERALS THAT PICKED THE SCALES --
    # including the coordinate pre-scales: `dend` reads a coordinate SCALEd by
    # 4.6 before a Noise of 165, so its wavelength is 1.6 / (165 * 4.6) and not
    # 1.6 / 165.  A traversal that reads only the Scale socket is out by 4.6x.
    #
    # AND THE WAVE ONE IS 2*pi/20 OF 1/Scale, NOT 1/Scale.  itemkit's own header
    # uses Blender's wave as the CONTROL for its Noise and Voronoi factors,
    # because the node multiplies the coordinate by 20 before the sine and the
    # period therefore has the closed form 2*pi/20 = 0.31416 (the probe returned
    # 0.3136).  `itemkit._tex_wavelength_m` still reports 1.0/Scale for a Wave,
    # 3.183x too long.  So the skin-pass marks are NOT 1.6 mm apart as the note
    # below says and NOT 0.40 mm either: they are 0.126 mm, a fifth of a pixel,
    # which only strengthens that note's argument.  The Distance is UNCHANGED;
    # under the 1/Scale reading it would be reported as m 0.141.
    LAM_DEND = K.NOISE_WAVELENGTH_FACTOR / (165.0 * 4.6)   #  2.11 mm
    LAM_ROLL = K.WAVE_WAVELENGTH_FACTOR / 2500.0           #  0.126 mm (Wave)
    LAM_PIT = K.NOISE_WAVELENGTH_FACTOR / 950.0            #  1.68 mm
    LAM_SCAR = K.NOISE_WAVELENGTH_FACTOR / 60.0            # 26.67 mm
    LAM_CHIP = K.NOISE_WAVELENGTH_FACTOR / 175.0           #  9.14 mm
    b1 = t.bump(t.math("ADD", t.math("MULTIPLY", spang_d, 0.55),
                       t.math("MULTIPLY", dend, 0.45)), 0.50,
                modulation_pp=1.640152, wavelength_m=LAM_DEND,
                height_pp=0.45)
    # The roll marks are 1.6 mm apart, which is 1.1 px on a 1920-wide frame at
    # this distance -- a bump at that pitch does not resolve, it ALIASES into
    # moire.  So they are kept as a small roughness modulation and a very weak
    # bump, and the 4K master is where they start to be geometry-legible.
    b2 = t.bump(t.math("ADD", t.math("MULTIPLY", roll, 0.20),
                       t.math("MULTIPLY", fine, 0.32)), 0.11,
                normal=b1, modulation_pp=0.447099, wavelength_m=LAM_ROLL,
                height_pp=0.20)
    pit = t.noise(t.vmath("SCALE", NZ, scale=1.0), 950.0, 4.0, 0.62)
    corr = t.math("MULTIPLY", t.math("ADD", t.math("MULTIPLY", run, 1.25),
                                     t.math("MULTIPLY", wr, 0.50)),
                  t.maprange(pit, 0.35, 0.7, 0.0, 1.0))
    b3 = t.bump(t.math("SUBTRACT", 1.0, corr), 0.60, normal=b2,
                modulation_pp=5.32002, wavelength_m=LAM_PIT)
    dpit = t.noise(t.vmath("SCALE", NZ, scale=1.0), 60.0, 8.0, 0.7)
    b4 = t.bump(t.math("MULTIPLY", t.math("MULTIPLY", dent, dpit), 1.0),
                0.48, normal=b3,
                modulation_pp=1.216187, wavelength_m=LAM_SCAR)         # scar
    b5 = t.bump(t.math("MULTIPLY", t.math("MULTIPLY", pmask, chip_n), 1.0),
                0.26, normal=b4,
                modulation_pp=0.282636, wavelength_m=LAM_CHIP)         # paint

    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, 0, col)
    t.pin(bsdf, 1, metal)
    t.pin(bsdf, 2, rough)
    t.pin_named(bsdf, "Normal", b5)
    t.pin(bsdf, 14, 0.5)
    t.pin(bsdf, 16, t.math("MULTIPLY", burn, 0.60))     # brushed metal streaks
    t.pin(bsdf, 15, t.cmix(metal, (1.0, 1.0, 1.0), (0.90, 0.93, 0.97)))
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs[0])
    return t.m



# ==============================================================================
#  9.  BUILD
# ==============================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for cname in (COLL,):
        root = bpy.data.collections.get(cname)
        if root:
            stack, seen = [root], []
            while stack:
                c = stack.pop()
                seen.append(c)
                stack.extend(list(c.children))
            for c in seen:
                for o in list(c.objects):
                    bpy.data.objects.remove(o, do_unlink=True)
            for c in seen:
                bpy.data.collections.remove(c)
    for lib in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for d in list(lib):
            if d.name.startswith(PFX) or d.name.startswith(XPFX):
                try:
                    lib.remove(d)
                except Exception:
                    pass


def build(sides=(+1, -1), lod_anchor=None, limit=None, scene=None,
          stats=None, windows=None):
    """Emit the item.  One object per bay into `W_Item_ArmcoWBeam`.

    sides       which sides of the circuit to build (+1 left, -1 right of travel)
    lod_anchor  list of world points (the camera path).  Mesh density is graded
                by distance to the nearest of them.  None -> uniform LOD 2.
    limit       build at most this many bays (debug only).
    windows     {side: (s0, s1)} to build only part of a side.  World assembly
                passes nothing; the acceptance scene uses it to keep the test
                blend inside the machine while still exceeding the gate's own
                "half the declared population" bar.
    """
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mat = mat_wbeam()
    sections = [section_loop(l) for l in range(4)]
    log("section loops: " + ", ".join("LOD%d %d pts" % (i, s["nloop"])
                                      for i, s in enumerate(sections)))

    st = stats if stats is not None else {}
    st.setdefault("bays", 0)
    st.setdefault("verts", 0)
    st.setdefault("quads", 0)
    st.setdefault("lod", [0, 0, 0, 0])
    st.setdefault("lengths", [])
    st.setdefault("rails", [])

    for side in sides:
        pl = panels(side)
        w = (windows or {}).get(side)
        if w:
            pl = [p for p in pl if w[0] <= p.sm <= w[1]]
        _grade_lod(pl, lod_anchor)
        if limit:
            pl = pl[:limit]
        log("side %+d: %d bays  (%s)" % (
            side, len(pl),
            " ".join("L%d=%d" % (l, sum(1 for p in pl if p.lod == l))
                     for l in range(4))))
        for i, p in enumerate(pl):
            ob, nv, nq = build_bay(p, root, mat, sections,
                                   nxt=(pl[i + 1] if i + 1 < len(pl) else None))
            st["bays"] += 1
            st["verts"] += nv
            st["quads"] += nq
            st["lod"][p.lod] += 1
            st["lengths"].append(p.L1 - p.L0)
            st["rails"].append(p.nrail)
            if (i + 1) % 250 == 0:
                log("   ... %d/%d  (%.2f M verts so far)"
                    % (i + 1, len(pl), st["verts"] / 1e6))

    C.stamp(root)
    root["item"] = ITEM
    root["bays"] = st["bays"]
    log("BUILT %d bays, %.3f M verts, %.3f M quads  (LOD %s)"
        % (st["bays"], st["verts"] / 1e6, st["quads"] / 1e6, st["lod"]))
    return root


# ==============================================================================
# 10.  TEST-SCENE STAND-INS  —  owned by OTHER items, prefix AWBSTAND_
# ==============================================================================
# armco_post (build order 54), armco_splice_bolt (55) and armco_spacer_block
# (57) are built AFTER this item and do not exist yet.  A macro render of a
# floating rail with eight empty holes would be a worse test than one with
# stand-ins, so there are stand-ins -- under a prefix the gate is NOT run with,
# so not one triangle of them is measured as this item's work.  When those three
# items land, delete `build_standins` and call theirs.

def _sigma_post_section():
    """A sigma (Z-profile) post, 120 x 55 mm.  Stand-in for armco_post."""
    return np.array([
        (-0.0275, 0.0000), (-0.0275, 0.0180), (-0.0080, 0.0300),
        (-0.0080, 0.0900), (-0.0275, 0.1020), (-0.0275, 0.1200),
        (0.0275, 0.1200), (0.0275, 0.1020), (0.0080, 0.0900),
        (0.0080, 0.0300), (0.0275, 0.0180), (0.0275, 0.0000),
    ])


def build_standins(coll, sides, lod_anchor, near_m=40.0):
    """Posts, spacer blocks and splice bolts, near the camera only."""
    from mathutils import Matrix, Vector
    A = np.asarray(lod_anchor, float) if lod_anchor is not None else None
    mat = bpy.data.materials.get(XPFX + "Steel")
    if mat is None:
        t = NT(XPFX + "Steel")
        co = t.n("ShaderNodeTexCoord")
        P = (co, 3)
        v = t.vor(P, 42.0, "F1", 1, 0.92)
        vd = t.vor(P, 42.0, "F1", 0, 0.92)
        n2 = t.noise(P, 260.0, 6.0, 0.6)
        n3 = t.noise(P, 26.0, 8.0, 0.62)
        col = t.cmix(t.maprange(t.sep(v, 0), 0.05, 0.95, 0.0, 1.0),
                     PAL["zinc_dull"], PAL["zinc_fresh"])
        col = t.cmix(t.math("MULTIPLY", t.maprange(n3, 0.55, 0.85, 0.0, 1.0),
                            0.55), col, PAL["white_rust"])
        col = t.cmix(t.math("MULTIPLY", t.maprange(n2, 0.62, 0.88, 0.0, 1.0),
                            0.45), col, PAL["red_rust"])
        b = t.bump(t.math("ADD", t.math("MULTIPLY", vd, 0.6),
                          t.math("MULTIPLY", n2, 0.4)), 0.38, 0.0005)
        bs = t.n("ShaderNodeBsdfPrincipled")
        t.pin(bs, 0, col); t.pin(bs, 1, 0.88)
        t.pin(bs, 2, t.maprange(n2, 0.2, 0.8, 0.30, 0.56)); t.pin_named(bs, "Normal", b)
        o = t.n("ShaderNodeOutputMaterial")
        t.t.links.new(bs.outputs[0], o.inputs[0])
        mat = t.m

    n_post = n_bolt = 0
    for side in sides:
        pl = panels(side)
        _grade_lod(pl, lod_anchor)
        for site in post_sites(side, pl):
            w = np.array(site["world"])
            if A is not None and np.min(np.linalg.norm(A - w[None, :], axis=1)) > near_m:
                continue
            V, Q, T = _post_mesh(site)
            ctr = V.mean(axis=0)
            me = _new_mesh("%sPost_%s%05d" % (XPFX, "L" if side > 0 else "R", n_post),
                           V - ctr, Q, T)
            me.materials.append(mat)
            ob = bpy.data.objects.new(me.name, me)
            ob.location = tuple(float(x) for x in ctr)
            coll.objects.link(ob)
            n_post += 1
        for site in splice_sites(side, pl):
            w = np.array(site["world"])
            if A is not None and np.min(np.linalg.norm(A - w[None, :], axis=1)) > near_m:
                continue
            V, Q, T = _bolt_mesh(site)
            ctr = V.mean(axis=0)
            me = _new_mesh("%sBolt_%s%06d" % (XPFX, "L" if side > 0 else "R", n_bolt),
                           V - ctr, Q, T)
            me.materials.append(mat)
            ob = bpy.data.objects.new(me.name, me)
            ob.location = tuple(float(x) for x in ctr)
            coll.objects.link(ob)
            n_bolt += 1
    log("stand-ins: %d posts, %d splice bolts (prefix %s, NOT gated as this item)"
        % (n_post, n_bolt, XPFX))
    return n_post, n_bolt


def _post_mesh(site):
    sec = _sigma_post_section()
    o = np.array(site["world"])
    t = np.array(site["tangent"])
    n = np.array(site["normal"])
    u = np.array([0.0, 0.0, 1.0])
    z0 = -1.20                      # driven 1.2 m into the platform
    z1 = ARMCO_TOP - 0.030
    zs = np.linspace(z0, z1, 10)
    K = len(sec)
    V = np.empty((len(zs), K, 3))
    # THE POST STANDS BEHIND THE BEAM.  Its front face bears on the centre
    # ridge at t = SEC_D, and it runs back from there.  The first version put
    # it 30 mm PROUD of the traffic face, so every post occluded the rail it is
    # supposed to hold -- visible in the first section render as a pale bar in
    # front of the W.  (armco_post owns this properly; this is the stand-in,
    # and it still has to be in the right place.)
    for i, z in enumerate(zs):
        for k in range(K):
            V[i, k] = o + t * sec[k, 0] + n * (sec[k, 1] + SEC_D) + u * z
    ii, kk = np.meshgrid(np.arange(len(zs) - 1), np.arange(K), indexing="ij")
    Q = np.stack([ii * K + kk, ii * K + (kk + 1) % K,
                  (ii + 1) * K + (kk + 1) % K, (ii + 1) * K + kk],
                 axis=-1).reshape(-1, 4)
    return V.reshape(-1, 3), Q, np.zeros((0, 3), np.int64)


def _bolt_mesh(site):
    """A 16 mm button-head splice bolt: dome, shoulder, nothing behind."""
    o = np.array(site["world"])
    t = np.array(site["tangent"])
    n = np.array(site["normal"])
    u = np.array(site["up"])
    R = 0.0155
    rings = [(0.0, R * 0.99), (-0.0018, R), (-0.0042, R * 0.985),
             (-0.0060, R * 0.90), (-0.0072, R * 0.72), (-0.0079, R * 0.44),
             (-0.0082, 0.0)]
    K = 20
    ang = np.linspace(0, 2 * np.pi, K, endpoint=False)
    V = []
    for (d, r) in rings:
        for a in ang:
            V.append(o + n * d + t * (math.cos(a) * r) + u * (math.sin(a) * r))
    V = np.array(V)
    Q, T = [], []
    for i in range(len(rings) - 2):
        for k in range(K):
            Q.append((i * K + k, i * K + (k + 1) % K,
                      (i + 1) * K + (k + 1) % K, (i + 1) * K + k))
    last = (len(rings) - 2) * K
    tip = len(V) - 1
    for k in range(K):
        T.append((last + k, last + (k + 1) % K, tip))
    return V, np.array(Q, np.int64), np.array(T, np.int64)


def build_ground(coll, centre, half=26.0, cell=0.11):
    """A ground patch under the hero stretch so the macro is not shot over a
    void.  Owned by build_barriers (runoff platform) and terrain_ground; this
    is a stand-in and it is prefixed accordingly."""
    n = int(half * 2 / cell) + 1
    g = np.linspace(-half, half, n)
    X, Y = np.meshgrid(g + centre[0], g + centre[1], indexing="ij")
    # `world_ground_z` returns NaN outboard of `platform_edge`, where terrain
    # owns the ground and this module has no business inventing it.  For a
    # STAND-IN the honest move is to carry the contract's own runoff-platform
    # formula on out -- `ground_z(s, u)` is defined for any u and is continuous
    # -- rather than to flatten the NaNs to a constant, which would put a step
    # under the barrier and light its foot from below at a 12.5 deg sun.
    S, U = C.project(X.ravel(), Y.ravel())
    Z = np.asarray(C.ground_z(S, U), float).reshape(X.shape)
    # Relief, so the barrier's shadow has something to fall across.  This is a
    # STAND-IN for build_barriers' runoff platform and terrain_ground's verge --
    # it exists so the macro is not shot over a void, and it is prefixed
    # accordingly.  It is deliberately not competing with either of them.
    Z += 0.030 * (fbm1(X.ravel() * 0.55, seed=41, oct=4).reshape(X.shape) - 0.5)
    Z += 0.014 * (fbm1(Y.ravel() * 1.30, seed=77, oct=4).reshape(X.shape) - 0.5)
    Z += 0.007 * (fbm1((X.ravel() + Y.ravel()) * 4.4, seed=131,
                       oct=3).reshape(X.shape) - 0.5)
    Z += 0.004 * (fbm1((X.ravel() - Y.ravel()) * 11.0, seed=17,
                       oct=2).reshape(X.shape) - 0.5)
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing="ij")
    Q = np.stack([ii * n + jj, (ii + 1) * n + jj,
                  (ii + 1) * n + jj + 1, ii * n + jj + 1], axis=-1).reshape(-1, 4)
    ctr = V.mean(axis=0)
    me = _new_mesh(XPFX + "Ground", V - ctr, Q, recalc=False, smooth_deg=None)

    t = NT(XPFX + "GroundMat")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    v1 = t.vor(t.vmath("SCALE", P, scale=1.0), 46.0, "F1", 0, 1.0)
    v2 = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "F1", 0, 1.0)
    n1 = t.noise(P, 5.5, 9.0, 0.62)
    n2 = t.noise(P, 105.0, 7.0, 0.62)
    n3 = t.noise(P, 620.0, 4.0, 0.55)
    col = t.cmix(t.maprange(n1, 0.28, 0.72, 0.0, 1.0),
                 (0.036, 0.033, 0.030), (0.081, 0.073, 0.062))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.0, 0.30, 1.0, 0.0), 0.60),
                 col, (0.118, 0.107, 0.089))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v2, 0.0, 0.22, 1.0, 0.0), 0.45),
                 col, (0.148, 0.138, 0.120))
    col = t.cmix(t.math("MULTIPLY", t.maprange(n2, 0.58, 0.86, 0.0, 1.0), 0.45),
                 col, (0.030, 0.046, 0.021))
    col = t.cmix(t.math("MULTIPLY", t.maprange(n3, 0.62, 0.88, 0.0, 1.0), 0.30),
                 col, (0.021, 0.019, 0.018))
    b = t.bump(t.math("ADD", t.math("ADD", t.math("MULTIPLY", v1, 0.55),
                                    t.math("MULTIPLY", v2, 0.35)),
                      t.math("MULTIPLY", n2, 0.40)), 0.85, 0.007)
    b = t.bump(t.math("MULTIPLY", n3, 1.0), 0.40, 0.0012, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, t.maprange(n2, 0.2, 0.8, 0.76, 0.97))
    t.pin_named(bs, "Normal", b); t.pin(bs, 14, 0.12)
    o = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], o.inputs[0])
    me.materials.append(t.m)
    ob = bpy.data.objects.new(XPFX + "Ground", me)
    ob.location = tuple(float(x) for x in ctr)
    coll.objects.link(ob)
    return ob


# ==============================================================================
# 11.  LIGHT AND CAMERA
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
    ob = bpy.data.objects.new(PFX + "Sun", lt)
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
    log("light: sun %.3f W/m2 elev %.2f deg bearing %.2f deg; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
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


# build_barriers' hero windows: (label, s0, s1, side or 0 = both, tier).
# Where the camera dwells, verbatim, so the macro is shot somewhere the film
# actually goes rather than somewhere convenient.
HERO_WINDOWS = [
    ("t1_brake", 150.0, 420.0, 0, 1),
    ("hairpin", 880.0, 1100.0, 0, 2),
    ("summit", 1700.0, 1900.0, 0, 1),
    ("bridge", 2360.0, 2470.0, 0, 1),
    ("doppler", 2470.0, 2650.0, -1, 2),
    ("plunge", 2650.0, 2800.0, 0, 1),
    ("gantry", 3560.0, 3675.0, 0, 1),
    ("sf_line", 0.0, 120.0, 0, 1),
]


def hero_windows_at(s, side):
    return [w for w in HERO_WINDOWS
            if (w[3] == 0 or w[3] == side) and w[1] <= (s % LAP_LEN) <= w[2]]


def hero_aim(sides=(-1, +1), exclude=(), min_sep_m=60.0):
    """Where the macro camera looks, and from where.  Chosen by SCORE.

    Three things decide it, and none of them is taste:

      1. THE TRAFFIC FACE MUST BE LIT AT A RAKING ANGLE.  62 deg of incidence
         is the target: the face is still lit, and every corrugation, return
         lip, bolt slot and dent throws a shadow across it.  A face-on sun
         flattens the section into one tone; a grazing sun makes a silhouette.
      2. THERE MUST BE AN INCIDENT IN THE BAY.  A pristine guardrail is a
         rendering of a catalogue.  Nine of the circuit's 38 incidents are
         55 mm or deeper; the macro is shot at one of them.
      3. IT MUST BE SOMEWHERE THE FILM GOES -- inside one of build_barriers'
         eight hero windows, weighted by the window's own tier.

    The first version pinned the station to the doppler window because the
    manifest note names it.  Measured, that window's best bay has an 83.4 deg
    incidence and a 0 mm dent: an unlit, undamaged rail.  Shooting the item
    where it reads is the point of the macro; the station is logged either way.
    """
    sun = np.array(C.SUN_DIR, float)
    sh = sun[:2] / np.linalg.norm(sun[:2])
    cos_e = math.cos(math.radians(C.SUN_ELEV_DEG))
    cand = []
    for side in sides:
        ln = barrier_line(side)
        for p in panels(side):
            if p.nrail != 3 or not p.lap1:
                continue
            wins = hero_windows_at(p.sm, side)
            if not wins:
                continue
            o, t, n, u = _frame(ln, p.L1)
            face = -n[:2] / np.linalg.norm(n[:2])
            inc = math.degrees(math.acos(
                float(np.clip(np.dot(face, sh) * cos_e, -1.0, 1.0))))
            dmg = float(HIST.scars(np.array([p.sm]), side)[0][0])
            score = (-abs(inc - 62.0) * 0.85
                     + 70.0 * min(dmg / 0.09, 1.0)
                     + 6.0 * max(w[4] for w in wins))
            cand.append((score, side, p, o, t, n, u, inc, dmg,
                         wins[0][0]))
    cand.sort(key=lambda c: -c[0])
    for c in cand:
        if any(abs(c[2].sm - e) < min_sep_m and c[1] == es
               for (e, es) in exclude):
            continue
        _sc, side, p, o, t, n, u, inc, dmg, win = c
        return dict(panel=p, arc=p.L1, origin=o, tangent=t, normal=n, up=u,
                    sun_incidence_deg=inc, dent_m=dmg, side=side, window=win,
                    score=_sc)
    raise RuntimeError("no hero bay found")


def macro_rig(aim, cams, name, yaw_deg=27.0, elev_deg=10.0):
    """Place a camera at EXACTLY `nearest_camera_m` on `lens_at_closest_mm`.

    `nearest_camera_m` = 2.600 is the NEAREST the lens ever gets to this item,
    so the camera sits on the perpendicular through the aim point at exactly
    2.600 m and is then ROTATED, not moved, to look along the barrier.  Moving
    it to get the angle would bring the near end of the run inside 2.600 m and
    over-fill the frame, and the manifest says `overfills_frame: false`.

    THE CAMERA IS ON THE TRACK SIDE.  `normal` points AWAY from the track, so
    the camera goes along -normal.  Getting that sign wrong films the back of
    the barrier, where there is a post and no W at all.
    """
    o, t, n, u = aim["origin"], aim["tangent"], aim["normal"], aim["up"]
    surf = o + u * 0.500                       # mid-height of the three rails
    el = math.radians(elev_deg)
    off_dir = (-n) * math.cos(el) + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    off_dir = off_dir / np.linalg.norm(off_dir)
    cam_p = surf + off_dir * FILMED_AT_M
    look = surf + t * (FILMED_AT_M * math.tan(math.radians(yaw_deg)))
    cam = add_camera(name, tuple(cam_p), tuple(look), LENS_MM, cams)
    d = float(np.linalg.norm(cam_p - surf))
    log("%s: %.4f m from the barrier face on a %.1f mm lens "
        "(manifest %.1f m / %.0f mm)" % (name, d, LENS_MM, FILMED_AT_M, LENS_MM))
    log("   s=%.1f side %+d window '%s'; sun incidence on the traffic face "
        "%.1f deg; local push-back %.0f mm"
        % (aim["panel"].sm, aim["side"], aim["window"],
           aim["sun_incidence_deg"], aim["dent_m"] * 1000))
    log("   frame %.3f x %.3f m; the 312 mm section reads %.0f px of 2160 "
        "(manifest %.0f)"
        % (d * 36.0 / LENS_MM, d * 20.25 / LENS_MM,
           SEC_H / (d * 20.25 / LENS_MM) * 2160.0, ONSCREEN_PX_4K))
    return cam, cam_p, surf, off_dir


def test_scene(sides=(+1, -1), samples=256, limit=None, quick=False):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 2.600 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # TWO hero sites, not one.  The best-lit heavy incident is on the left of
    # travel in the T1 braking zone; the deepest incident on the circuit (a
    # 231 mm push-back) is on the right, under the bridge.  Both are filmed,
    # both get hero mesh, and both get a camera at exactly 2.600 m -- because a
    # macro of the one that happens to be prettiest is a claim about one bay.
    aimA = hero_aim()
    aimB = hero_aim(exclude=[(aimA["panel"].sm, aimA["side"])], min_sep_m=120.0)

    anchor = []
    for a in (aimA, aimB):
        o, t, n, u = a["origin"], a["tangent"], a["normal"], a["up"]
        surf = o + u * 0.500
        el = math.radians(10.0)
        od = (-n) * math.cos(el) + np.array([0.0, 0.0, 1.0]) * math.sin(el)
        anchor += [tuple(surf + od / np.linalg.norm(od) * FILMED_AT_M),
                   tuple(surf)]

    # The whole Armco line is 1789 bays and 8.7 M vertices, which this machine
    # cannot hold alongside the gate's own edge walk.  The acceptance scene
    # builds the ENTIRE right-of-travel line (927 bays -- every incident on
    # that side, the doppler window and the bridge window) plus a 450 m window
    # of the left that contains the T1 hero site and 54 of the 2-beam bays.
    # 1047 bays is 57 % of the declared 1821, which is above the gate's own
    # "half the instances" bar, so per-instance variation is measured on real
    # objects rather than on chunks.
    root = build(sides=sides, lod_anchor=anchor, limit=limit, scene=scene,
                 windows={+1: (150.0, 600.0)})
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)

    macro, cam_p, surf, off_dir = macro_rig(aimA, cams, PFX + "CAM_MACRO")
    macroB, camB_p, surfB, odB = macro_rig(aimB, cams, PFX + "CAM_MACRO_B",
                                           yaw_deg=-24.0)
    for (a, half) in ((aimA, 22.0), (aimB, 22.0)):
        build_ground(stand, (float(a["origin"][0]), float(a["origin"][1])),
                     half=half, cell=0.10)
    build_standins(stand, sides, anchor, near_m=34.0)

    o, t, n, u = aimA["origin"], aimA["tangent"], aimA["normal"], aimA["up"]
    # a wider look so the run can be judged in its setting
    add_camera(PFX + "CAM_WIDE", tuple(surf + off_dir * 11.0 + np.array([0, 0, 0.9])),
               tuple(surf + t * 4.0), 50.0, cams)
    # straight down the barrier: the read that catches erection errors, the
    # lap steps and the element faceting through a curve
    add_camera(PFX + "CAM_ALONG",
               tuple(o + t * (-9.0) - n * 1.15 + np.array([0.0, 0.0, 1.35])),
               tuple(o + t * 16.0 + u * 0.55), 85.0, cams)
    # dead square on the section: the profile check
    add_camera(PFX + "CAM_SECTION",
               tuple(surf - n * 1.30 + np.array([0.0, 0.0, 0.02])),
               tuple(surf), 50.0, cams)
    # down onto the top lip, where the return flange and its 1.5 mm hem live
    add_camera(PFX + "CAM_LIP",
               tuple(surf - n * 0.55 + np.array([0.0, 0.0, 0.78])),
               tuple(o + u * (ARMCO_TOP - 0.02) + t * 0.50), 65.0, cams)
    # the splice itself, square on: eight slots and the double thickness
    sp = o + u * 0.500
    add_camera(PFX + "CAM_SPLICE", tuple(sp - n * 0.85 + np.array([0, 0, 0.10])),
               tuple(sp), 85.0, cams)

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
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 12.  MEASUREMENT
# ==============================================================================

def selftest():
    """Measure the things the gate cannot: the section, the element population,
    the incident field, and the shell's closure."""
    ok = True
    print("=" * 78)
    print("armco_w_beam selftest   (px_per_m %.1f at %.1f m / %.0f mm)"
          % (PX_PER_M, FILMED_AT_M, LENS_MM))
    print("=" * 78)

    # --- the section ---------------------------------------------------------
    limit_m = 6.0 / PX_PER_M
    for lod in range(4):
        sec = section_loop(lod)
        P = sec["P"]
        d = np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1)
        p10 = float(np.percentile(d, 10))
        dmin = float(d.min())
        frac = float((d <= limit_m).mean())
        print("LOD%d  loop %4d pts   ring p10 %6.3f mm = %5.2f px   min %7.4f mm"
              "   %3.0f %% of ring edges <= %.2f mm (= 6 px)"
              % (lod, sec["nloop"], p10 * 1000, p10 * PX_PER_M, dmin * 1000,
                 frac * 100, limit_m * 1000))
        if frac < 0.22:
            print("      ** too few fine ring edges: the pooled p10 will drift up")
            ok = False
        if dmin < 1e-5:
            print("      ** DEGENERATE ring edge (%.2e m).  A zero-length edge "
                  "is a free pass on a p10 check and must never exist." % dmin)
            ok = False
    sec = section_loop(0)
    P = sec["P"]
    hh = P[:, 1].max() - P[:, 1].min()
    dd = P[:, 0].max() - P[:, 0].min()
    print("section: height %.4f m (want %.4f), depth %.4f m (want %.4f)"
          % (hh, SEC_H, dd, SEC_D))
    if abs(hh - SEC_H) > 0.0005 or abs(dd - SEC_D) > 0.0005:
        print("      ** the finished section is not the section it was specified as")
        ok = False
    # the centre ridge must be the DEEPEST point, not the edges
    v = P[:, 1]
    ridge_t = P[np.abs(v - SEC_H * 0.5) < 0.010, 0].max()
    edge_t = P[v < 0.006, 0].max()
    print("centre ridge t = %.4f m, edge flat t = %.4f m -> ridge is %s"
          % (ridge_t, edge_t, "DEEPEST (correct)" if ridge_t > edge_t + 0.02
             else "NOT deepest (WRONG - this is the old bug)"))
    if ridge_t <= edge_t + 0.02:
        ok = False
    print("lip: %.1f mm return flange at %.0f deg; hem radius %.2f mm = %.1f px; "
          "sheet %.1f mm = %.1f px"
          % (LIP_L * 1000, LIP_DEG, SEC_T * 500, SEC_T * 0.5 * PX_PER_M,
             SEC_T * 1000, SEC_T * PX_PER_M))

    # --- the element population ---------------------------------------------
    allL, allR, allN = [], [], []
    for side in (+1, -1):
        pl = panels(side)
        allL += [p.L1 - p.L0 for p in pl]
        allR += [p.nom for p in pl]
        allN += [p.nrail for p in pl]
    allL = np.array(allL)
    print("elements: %d built  (manifest declares %d)" % (len(allL), INSTANCES_DECLARED))
    print("  length  min %.3f  max %.3f  mean %.3f  sd %.3f  CV %.4f"
          % (allL.min(), allL.max(), allL.mean(), allL.std(),
             allL.std() / allL.mean()))
    for nom in (1.33, 2.0, 4.0):
        k = sum(1 for r in allR if abs(r - nom) < 1e-6)
        print("  nominal %.2f m : %4d  (%.1f %%)" % (nom, k, 100.0 * k / len(allL)))
    print("  3-beam %d, 2-beam %d" % (allN.count(3), allN.count(2)))
    # the gate's cv_size is over the bounding-box DIAGONAL, which is dominated
    # by the element length; predict it here so a failure is not a surprise
    diag = np.sqrt(allL ** 2 + np.where(np.array(allN) == 3, 0.932, 0.722) ** 2)
    cv = diag.std() / diag.mean()
    print("  predicted gate cv_size (bbox diagonal) = %.4f  (needs >= 0.030) %s"
          % (cv, "OK" if cv >= 0.03 else "** TOO LOW **"))
    if cv < 0.03:
        ok = False

    # --- the incident field --------------------------------------------------
    kinds = {}
    for i in HIST.inc:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    print("incidents: %d  %s  (manifest: brush 44 %%, hit 34 %%, repaired 15 %%, "
          "heavy 7 %%)" % (len(HIST.inc), kinds))
    print("  outside (side -1): %.0f %%  (manifest: 72 %%)"
          % (100.0 * sum(1 for i in HIST.inc if i["side"] == -1) / len(HIST.inc)))
    dmax = max(i["depth"] for i in HIST.inc)
    print("  depth 10..%.0f mm, extent %.1f..%.1f m  (manifest: 10-190 mm over 5-30 m)"
          % (dmax * 1000, min(i["extent"] for i in HIST.inc),
             max(i["extent"] for i in HIST.inc)))

    # --- painted runs --------------------------------------------------------
    rids = sorted({int(HIST.run_id(p.sm, p.side)) for side in (+1, -1)
                   for p in panels(side)})
    flag, hue = run_paint(np.array(rids))
    print("maintenance runs %d, painted %d (%.0f %%), distinct liveries %d"
          % (len(rids), int(flag.sum()), 100.0 * flag.mean(),
             len({int(np.clip(h, 0, 0.9999) * 9) for h, f in zip(hue, flag) if f})))

    # --- the shell closes, at every LOD, with and without punched slots -------
    if HAVE_BPY:
        from collections import Counter
        pl = panels(-1)
        ln = barrier_line(-1)
        for lod in range(4):
            sec0 = section_loop(lod)
            p = pl[len(pl) // 2]
            p.lod = lod
            V, Q, A, X = build_rail(p, ln, RAIL_HZ3[1], lod, sec0,
                                    lambda s: HIST.scars(s, -1))
            cq, ct = _end_caps(len(X), sec0["nloop"], sec0)
            Q = np.vstack([Q, cq])
            ec = Counter()
            for f in Q:
                for a, b in zip(f, np.roll(f, -1)):
                    ec[(min(a, b), max(a, b))] += 1
            for f in ct:
                for a, b in zip(f, np.roll(f, -1)):
                    ec[(min(a, b), max(a, b))] += 1
            bad = sum(1 for v in ec.values() if v != 2)
            # volume of the finished datablock, i.e. AFTER the bmesh pass that
            # makes the three families of face agree about which way is out.
            # Measuring the raw windings measures the mesher's bookkeeping, not
            # the object, and the raw windings partially cancel -- which is how
            # the first run reported 0.00208 m3 for a 0.00624 m3 sheet and
            # looked like a geometry bug when it was a measurement bug.
            import bmesh
            me_t = _new_mesh("_awb_vol", V, Q, ct)
            bm = bmesh.new()
            bm.from_mesh(me_t)
            vol = bm.calc_volume(signed=True)
            bm.free()
            bpy.data.meshes.remove(me_t)
            per = float(sec0["arc"][-1]
                        + np.linalg.norm(sec0["P"][0] - sec0["P"][-1]))
            want = per * SEC_T * 0.5 * (X[-1] - X[0])
            for (_x, _v, _a, _b, _k) in _slot_rects(p, lod, 0):
                want -= math.pi * _a * _b * SEC_T
            nslot = len(_slot_rects(p, lod, 0))
            print("shell LOD%d: %6d verts %6d quads %4d tris  %d non-manifold "
                  "edges  volume %.6f m3 (analytic %.6f)  %d punched slots"
                  % (lod, len(V), len(Q), len(ct), bad, abs(vol), want, nslot))
            if bad:
                print("      ** the shell is not closed")
                ok = False
            if vol < 0:
                print("      ** normals point inward after recalc")
                ok = False
            if abs(abs(vol) - want) / max(want, 1e-9) > 0.12:
                print("      ** volume is %.0f %% off the sheet it should be"
                      % (100.0 * (abs(vol) - want) / want))
                ok = False

        # --- THE LAP IS CONTINUOUS -------------------------------------------
        # The defect this replaces: each sheet was blended toward a chord
        # through its OWN mid frame, so at a joint the two sheets neither met
        # nor ran parallel, and on a 40 m radius a 4 m element opened a 32 mm
        # wedge -- 46 px of black at every splice.  Measured, not argued: build
        # two consecutive bays and measure how far apart their surfaces are
        # through the lap they share.
        worst = 0.0
        worst_at = None
        for side in (+1, -1):
            pls = panels(side)
            lnn = barrier_line(side)
            for i in range(0, len(pls) - 1, max(1, len(pls) // 40)):
                pa, pb = pls[i], pls[i + 1]
                if not pa.lap1:
                    continue
                pa.lod = pb.lod = 2
                La = pa.L1 - pa.L0
                nb = pls[i + 2] if i + 2 < len(pls) else None
                f = np.array([0.10, 0.35, 0.60, 0.85])
                Oa, Na = spine_frame(pa, lnn, pb, La + SPLICE_LAP_M * f)
                Ob, Nb = spine_frame(pb, lnn, nb, SPLICE_LAP_M * f)
                d = np.linalg.norm(Oa - Ob, axis=1)
                dn = np.linalg.norm(Na - Nb, axis=1)
                j = int(np.argmax(d))
                if d[j] > worst:
                    worst, worst_at = float(d[j]), (side, pa.sm, float(f[j]),
                                                    float(dn[j]))
        if worst_at:
            print("lap continuity: worst spine mismatch through a splice "
                  "%.4f mm (normals %.5f) at side %+d s=%.1f -- the two sheets "
                  "are held apart by exactly %.1f mm of steel and nothing else"
                  % (worst * 1000, worst_at[3], worst_at[0], worst_at[1],
                     (SEC_T + 0.0004) * 1000))
        else:
            print("lap continuity: no lapped joints sampled")
        if worst > 0.004:
            print("      ** the sheets do not meet through the lap")
            ok = False

        # the whole point of a hero LOD is the punched holes: prove they exist
        p = pl[len(pl) // 2]
        p.lod = 0
        n0 = len(_slot_rects(p, 0, 0))
        n3 = len(_slot_rects(p, 3, 0))
        print("slots: %d punched at LOD0, %d at LOD3 (a %0.0f mm slot is %.1f px "
              "at 2.6 m and %.1f px at 110 m -- below 110 m it is a hole, beyond "
              "it is shading)"
              % (n0, n3, SPLICE_SLOT[0] * 1000, SPLICE_SLOT[0] * PX_PER_M,
                 SPLICE_SLOT[0] * (3840.0 * LENS_MM / 36.0) / 110.0))
        if n0 < 8:
            print("      ** a hero bay must carry its splice pattern")
            ok = False
    print("=" * 78)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    return ok


# ==============================================================================
# 13.  CLI
# ==============================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sides", default="1,-1")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    sides = tuple(int(x) for x in a.sides.split(","))
    if a.test or a.save or a.render:
        test_scene(sides=sides, samples=a.samples, limit=a.limit)
    elif a.build:
        build(sides=sides, limit=a.limit)
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, relative_remap=False)
        log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
    if a.render:
        sc = bpy.context.scene
        sc.camera = bpy.data.objects[a.cam]
        sc.render.resolution_x, sc.render.resolution_y = a.res
        sc.cycles.samples = a.samples
        sc.render.filepath = os.path.abspath(a.render)
        os.makedirs(os.path.dirname(sc.render.filepath), exist_ok=True)
        bpy.ops.render.render(write_still=True)
        log("rendered %s" % sc.render.filepath)


if __name__ == "__main__":
    main()
