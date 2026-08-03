#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_surface.py — CIRCUIT VITRINE: the driving surface.

Builds, into the collection ``W_Surface``:

  * ``SURF_Track``        the 3 675.00 m racing surface (asphalt, verges, negative
                          kerbs, all markings) as ONE welded cyclic mesh.
  * ``SURF_AccessRoad``   the unrubbered concrete apron + R150 merge arc that carries
                          the car from the breached glass wall onto the pit straight.
  * ``SURF_Kerb_*``       35 individually generated two-tone serrated kerbs - no two
                          share a mesh, a length, a serration phase, a paint-block
                          length, a wear field or a pigment.
  * ``SURF_GridNum_*``    painted grid-slot numerals on the pit straight.

Everything is generated from ``world/world_contract.py`` (geometry that is shared with
another module), ``docs/circuit_spec.json`` and ``telemetry/telemetry.csv``.  No image
textures, no HDRIs, no downloaded assets: every pattern is either explicit per-vertex
geometry or a procedural node network evaluated in 3-D.

THE CONTRACT OWNS THE DATUM.  This module used to carry its own ``half_width``, its own
cross-slope, its own undulation and its own access-road elevation, and the assembly
review found all four disagreeing with the neighbours (a 0.978 m width error over 14 %
of the lap; a Beat-4 ribbon that z-fought architecture's paving six times in 116 m).
Every one of those numbers now comes from ``world_contract``:

    C.half_width(s)     C.verge_edge(s)     C.ground_z(s, u)     C.centreline(s)
    C.access_route_arrays / C.access_edges / C.access_ribbon_polygon

and this module adds exactly one thing on top of the datum: a racing-line micro layer
bounded by ``C.MICRO_LAYER_MAX_M`` and multiplied by ``C.micro_window`` so it is
identically zero at and beyond ``half_width``.  See §0 of build_surface.md.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py -- --render
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py -- --verify

Idempotent: re-running wipes and rebuilds the collection, its meshes and its materials.

PUBLIC INTERFACE for the other builders (import this module, call ``prepare()`` first
if you are not calling ``build()``):

    racing_line_offset(s)      lateral offset (m, +ve = left of travel) of the driven
                               line from the centreline, at lap station s.
    surface_z(s, u)            C.ground_z(s, u) + this module's micro layer.  Use
                               C.ground_z unless you specifically want the racing-line
                               compaction dip; the two differ by <= 18 mm and only
                               inside the racing surface.
    centreline(s)              -> (x, y, z, heading_rad, curvature)   [= C.centreline]
    su_to_world(s, u)          -> (x, y, z)
    track_half_width(s)        = C.half_width
    outer_edge(s, side)        -> (x, y, z) of the outermost point of this module's
                               geometry = C.verge_edge(s), which is what the runoff
                               and terrain builders butt to.

See build_surface.md for the design decisions.
"""

import bpy
import json
import math
import os
import sys
import time

import numpy as np

# --------------------------------------------------------------------------- paths
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import world_contract as C           # noqa: E402  THE integration contract
SPEC_PATH = os.path.join(_ROOT, "docs", "circuit_spec.json")
TELEM_PATH = os.path.join(_ROOT, "telemetry", "telemetry.csv")
RENDER_DIR = os.path.join(_ROOT, "render", "world", "surface")

COLL_NAME = "W_Surface"
PFX = "SURF_"
MPFX = "M_Surf_"

# ------------------------------------------------------------------ build resolution
ROW_DS_MAX = 0.70          # longitudinal row spacing on straights (m)
ROW_DS_MIN = 0.34          # hard floor
ROW_SAGITTA = 0.0012       # chord tolerance that drives row spacing in corners
HERO_DS = 0.38             # forced spacing where the camera comes close
KERB_DS = 0.03125          # 8 samples per 250 mm serration
N_RS_COLS = 35             # columns across the racing surface (odd -> one on centre)
KERB_BAND = C.KERB_W       # 1.50 m, outboard of the racing surface  (contract §3)
VERGE_BAND = C.VERGE_W     # 1.00 m, outboard of the kerb band       (contract §3)
ACCESS_SAW_M = float(getattr(C, "ACCESS_RIBBON_SAW_M", 0.30))
                           # the sawn edge strip this module lays outside the declared
                           # ribbon edge, == C.access_ribbon_polygon()'s default margin,
                           # so architecture's cut line IS this mesh's boundary

# THE RIBBON'S END CAPS — ASSEMBLY DEFECT #2, AND THE CONTRACT'S ANSWER TO IT.
#
# `C.access_ribbon_polygon(margin)` widens the ribbon LATERALLY by `margin` and leaves
# the caps on the bare route stations, while the old `in_access_ribbon` tested
# `tt >= -margin` — so each consumer walked the START CAP back through the glass wall by
# its own margin, and the three margins were different:
#
#   road_corridor_mask  ACCESS_CORRIDOR_MARGIN_M 3.00 -> terrain cut to x = 12.00
#   build_architecture  RIBBON_SAW_M             0.30 -> paving cut to x = 14.70
#   build_surface       (no margin on the cap)        -> this mesh STARTED at x = 15.000
#
# 1 276 of 7 467 samples over x 4..17, y +-14 had no usable ground: a 3.0 m deep band
# across the whole 12 m driving width, 0.300 m of it FULLY OPEN, at the exact metre the
# car and the camera pass through as the glass breaches (`CAM_GLASS_GAP.png`).
#
# Contract 1.0.1 settled it the only way that does not create a worse defect: the start
# cap is PINNED at `ACCESS_RIBBON_T_MIN` = 0.0 = the breach plane, world x = 15.000, for
# every consumer and every margin.  Behind the glass is the showroom floor — round 1's
# `Floor`, 30.0 x 22.0, top z = 0.000, world x -15..+15 (spec 10.1), and the re-levelled
# `ExteriorGround` (spec 10.3(b), exactly z = 0.000 over world x 10..90).  Paving 3 m of
# it from HERE would have been a 3 m x 12.6 m coplanar overlap with `Floor` in the hero
# frame — trading a hole for a z-fight.  This module therefore reads the pin rather than
# choosing a margin of its own, and the end cap alone carries the saw, because that is
# where `in_access_ribbon` still applies one (`tt <= ACCESS_TOTAL + margin`).
RIBBON_T_MIN = float(getattr(C, "ACCESS_RIBBON_T_MIN", 0.0))
RIBBON_CAP_END_M = ACCESS_SAW_M

# THE TRACK / APRON-PLATFORM JOINT.  SURF_Track's outer edge is C.verge_edge(s) exactly.
# build_architecture's apron bay grid ALSO starts at C.verge_edge and then insets every
# bay 12 mm, so both meshes stop at the same coordinate and the 12 mm between them falls
# 0.300 m to the sub-base: at a 12.47 deg sun, a black line down 220 m of the pit
# straight.  Two surfaces cannot both stop at a shared coordinate and hope; one of them
# has to lap the other DELIBERATELY.  build_surface laps: `SURF_ApronJoint` carries the
# asphalt edge OUTBOARD of verge_edge as a real recessed sealant joint, so the joint is
# what a construction joint looks like whatever the neighbour's bay origin turns out to
# be.  Contract-overridable for the same reason as RIBBON_CAP_M.
APRON_JOINT_LAP_M = float(getattr(C, "APRON_JOINT_LAP_M", 0.050))
APRON_JOINT_DEPTH_M = float(getattr(C, "APRON_JOINT_DEPTH_M", 0.005))

CAR_WIDTH = C.CAR_BODY_W_M  # 2.005, measured (round2_inventory.md S2).  RULE 1,
                           # world_contract 1.2.0 S10c: the car box is the
                           # contract's, because the placement gate, the transit
                           # keep-out and this module all have to mean the same car.
CAR_HALF = CAR_WIDTH * 0.5

LAP = C.LAP                # 3675.0

# stations where the camera is close enough to demand the finest rows
HERO_ZONES = [(0.0, 300.0), (880.0, 1090.0), (1500.0, 1930.0),
              (2380.0, 2760.0), (3050.0, LAP)]

# --------------------------------------------------------------------------- state
_S = {}          # module cache


# ============================================================================
#  1. SPEC / TELEMETRY
# ============================================================================
def _load_spec():
    with open(SPEC_PATH) as f:
        return json.load(f)


def _load_telemetry():
    """Lap-station-indexed speed / accel from the telemetry CSV (source of truth).

    telemetry.csv covers dais -> glass -> apron -> merge -> line -> one full lap, so
    its ``s_m`` carries a 381.88 m transit prefix (spec.transit
    total_length_dais_to_line_m).  Verified against the analytic centreline: frame 400
    lands on (479.32, 563.26) which is s_track = 517.02 to 1 cm.
    """
    if not os.path.exists(TELEM_PATH):
        return None
    import csv
    s, v, al, at = [], [], [], []
    with open(TELEM_PATH) as f:
        for r in csv.DictReader(f):
            s.append(float(r["s_m"]))
            v.append(float(r["speed_ms"]))
            al.append(float(r["accel_long_ms2"]))
            at.append(float(r["accel_lat_ms2"]))
    s = np.asarray(s)
    off = 381.88
    m = s >= off
    st = s[m] - off
    keep = st <= LAP + 1e-6
    return dict(s=st[keep], v=np.asarray(v)[m][keep],
                a_long=np.asarray(al)[m][keep], a_lat=np.abs(np.asarray(at)[m][keep]))


# ============================================================================
#  2. CENTRELINE AND ELEVATION  —  BOTH DELEGATED TO THE CONTRACT
# ============================================================================
#
# This module used to carry its own re-integration of the element list and its own
# PVI/vertical-curve evaluator.  Both agreed with the contract to 1e-12 — that was
# never where the divergence was — but contract RULE 1 is that a number two modules
# need lives in one place, so they are gone.  What is kept here is the ELEMENT TABLE
# (tag, kind, radius, length, start station), because the kerb plan and the racing-line
# solve are indexed by corner and the contract does not publish that mapping.  The
# table's provenance is checked against the contract in `prepare()`.

centreline = C.centreline               # (x, y, z, heading_rad, curvature), scalar
_centreline_arrays = C.centreline_arrays  # -> (X, Y, H, K)
elevation_c = C.elevation_c             # centreline z, scalar or array


def _elements(spec):
    """The element table: tag / type / radius / turn / length / start station.

    Positions are NOT computed here.  `C.centreline` is the one implementation, and
    `prepare()` verifies that every element start it returns lands on the spec's own
    published `start_world` to within a centimetre.
    """
    els = []
    for e in spec["elements"]:
        els.append(dict(name=e["name"], kind=e["type"], R=e.get("radius_m"),
                        turn=e.get("turn_deg"), L=float(e["length_m"]),
                        s0=float(e["s_start"]), start_world=e["start_world"],
                        tag=e["name"].split()[0]))
    return els


def _find_el(els, s):
    lo, hi = 0, len(els) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if els[mid]["s0"] <= s:
            lo = mid
        else:
            hi = mid - 1
    return els[lo]


def _local_radius(s):
    e = _find_el(_S["els"], s % LAP)
    return None if (e["kind"] == "S" or not e["R"]) else float(e["R"])


# ============================================================================
#  4. CYCLIC FIELD HELPERS
# ============================================================================
_FS = 0.25                      # field sample step (m)
_FN = int(round(LAP / _FS))     # 14700


def _fgrid():
    return np.arange(_FN) * _FS


def _csmooth(a, sigma_m):
    """Cyclic gaussian smooth of a station-indexed field."""
    if sigma_m <= 0:
        return a
    sig = sigma_m / _FS
    rad = int(math.ceil(sig * 3.0))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sig) ** 2)
    k /= k.sum()
    return np.convolve(np.concatenate([a[-rad:], a, a[:rad]]), k, mode="same")[rad:-rad]


def _fsample(field, s):
    """Cyclic linear sample of a station field."""
    x = np.asarray(s, float) % LAP / _FS
    i0 = np.floor(x).astype(int) % _FN
    i1 = (i0 + 1) % _FN
    f = x - np.floor(x)
    return field[i0] * (1 - f) + field[i1] * f


# ============================================================================
#  5. TRACK SECTION AND CROSS-SLOPE  —  BOTH DELEGATED TO THE CONTRACT
# ============================================================================
#
# THE WIDTH BUG.  `_build_width` used to set the 16 m pit-straight span to
# [3115 + 30, 250 - 30] and then smooth it with a +-30 m raised cosine — which CENTRES
# the 60 m transition on the element boundary instead of STARTING it there, so
# half_width(3115) came out 7.022 instead of 8.000.  build_barriers pins the runoff,
# the painted verge, the advertising boards and the barrier offsets to
# verge_edge = half_width + 2.50, so that error left a strip of UNBUILT GROUND down
# both edges of the pit straight — the surface the onboard follow runs at 330 km/h.
#
# MEASURED against the contract before the fix, and `verify()` still measures it:
#   peak            0.978 m per side, at s = 3115.000 and s = 250.000 exactly
#   rms over a lap  0.156 m
#   extent          520 m of the 3675 m lap (14.14 %) more than 10 mm out,
#                   mean 0.170 m inside that band
# The assembly review reported this as "a 0.63 m strip"; that number does not
# reproduce as either the peak (0.978 m) or the mean over the affected stretch
# (0.170 m), so the figures above are what this module publishes.  It is not smoothed here any more, it is not smoothed anywhere:
# spec §9 says LINEAR and `C.half_width` is a 14-key np.interp that anyone can
# reproduce exactly.
#
# The cross-slope (banking, the T4 camber override, the drainage crown), the
# undulation, the negative-kerb troughs and the 12 mm verge drain all moved into
# `C.ground_z` for the same reason: build_barriers needed them and could not have
# them, because its datum was expressed in |lat| and banking is antisymmetric in u.

track_half_width = C.half_width         # spec §9, LINEAR, transition OUTSIDE the section


# ============================================================================
#  7. VALUE NOISE (deterministic, numpy)
# ============================================================================
def _hash2(ix, iy, seed):
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    h = (ix * 374761393 + iy * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h.astype(np.float64) / 4294967295.0


def _vnoise(x, y, seed):
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    a = _hash2(ix, iy, seed); b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed); d = _hash2(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def _vnoise1(x, seed):
    return _vnoise(x, np.zeros_like(x), seed)


# ============================================================================
#  8. THE RACING LINE  (out-in-out, derived from the spec corner table)
# ============================================================================
def _pchip_cyclic(xs, ys, xq, period):
    """Fritsch-Carlson monotone cubic through cyclic keys — no overshoot, so the
    interpolated line can never leave the track between keys."""
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    n = len(xs)
    xe = np.concatenate([xs[-2:] - period, xs, xs[:2] + period])
    ye = np.concatenate([ys[-2:], ys, ys[:2]])
    h = np.diff(xe)
    delta = np.diff(ye) / h
    m = np.zeros(len(xe))
    for i in range(1, len(xe) - 1):
        if delta[i - 1] * delta[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i])
    m[0] = delta[0]; m[-1] = delta[-1]
    q = np.asarray(xq, float) % period
    i = np.clip(np.searchsorted(xe, q, side="right") - 1, 0, len(xe) - 2)
    t = (q - xe[i]) / h[i]
    t2 = t * t; t3 = t2 * t
    return (ye[i] * (2 * t3 - 3 * t2 + 1) + m[i] * h[i] * (t3 - 2 * t2 + t)
            + ye[i + 1] * (-2 * t3 + 3 * t2) + m[i + 1] * h[i] * (t3 - t2))


def _build_racing_line(spec):
    """The driven line, as F1 drivers actually place a car:

      * turn-in from the far edge, apex at the inside kerb, track-out to the far edge;
      * the apex station is moved LATE on slow corners (the slower the corner, the more
        the driver sacrifices entry for exit) and left geometric on the fast ones;
      * approach and exit lengths scale with speed, so 330 km/h T1 starts moving 110 m
        out while 80 km/h T4 does it in 25 m;
      * where two consecutive edge points collide (the esses, T1->T2, T13->T14) they are
        MERGED to their mean, which is what straightens a sequence of alternating
        corners into one flowing diagonal instead of a zig-zag.
    """
    els = {e["tag"]: e for e in _S["els"]}
    keys = []          # (station, lateral, kind)
    for c in spec["corners"]:
        tag = c["name"].split()[0]
        e = els.get(tag)
        if e is None:
            continue
        sg = 1.0 if c["direction"] == "left" else -1.0     # +1 => inside is +u (left)
        arc = e["L"]
        v_ap = float(c["apex_kph"]) / 3.6
        v_ex = float(c["exit_kph"]) / 3.6
        v_en = float(c["entry_kph"]) / 3.6

        # late apex on slow corners, geometric on fast ones
        if v_ap * 3.6 < 120:
            late = 0.20
        elif v_ap * 3.6 < 190:
            late = 0.11
        else:
            late = 0.04
        s_ap = e["s0"] + arc * (0.5 + late)

        w_ap = track_half_width(s_ap)
        # inside wheel over the white line and onto the kerb -> car centre 0.55 m in
        u_ap = sg * float(w_ap - 0.55)
        if float(c["radius_m"]) >= 130:
            u_ap = sg * float(w_ap - 0.85)   # fast kinks do not need the whole kerb

        # The lateral placement for a corner happens on the APPROACH, at approach
        # speed, not at apex speed: the car is already on the far edge while it is
        # still braking from 296 km/h into an 80 km/h hairpin.  So the lead and trail
        # come from the telemetry speed either side of the arc, not from the corner's
        # own apex speed — which is what stops a 176 deg hairpin being handed a 20 m
        # turn-in ramp.
        v_in = max(float(_fsample(_S["speed"], e["s0"] - 70.0)), 12.0)
        v_out = max(float(_fsample(_S["speed"], e["s0"] + arc + 50.0)), 12.0)
        lead = float(np.clip(0.95 * v_in + 10.0, 30.0, 175.0))
        trail = float(np.clip(1.05 * v_out + 10.0, 35.0, 185.0))
        s_in = e["s0"] - lead
        s_out = e["s0"] + arc + trail
        u_in = -sg * float(track_half_width(s_in) - 1.15)
        u_out = -sg * float(track_half_width(s_out) - 0.85)
        keys.append([s_in % LAP, u_in, "edge"])
        # A kink has a point apex.  A 176 deg hairpin does not: the width buys the
        # line almost nothing once the turn angle is large (the classic
        # R_line = R + w/(sec(th/2) - 1) is +0.5 m at 176 deg), so the car simply
        # RIDES the inside through the middle of the arc.  Dwell grows with turn
        # angle and is zero below 40 deg.
        dwell = arc * float(np.clip((abs(float(c["turn_deg"])) - 40.0) / 140.0, 0.0, 0.62))
        if dwell > 6.0:
            a0 = max(e["s0"] + arc * 0.10, s_ap - dwell * 0.5)
            a1 = min(e["s0"] + arc * 0.95, s_ap + dwell * 0.5)
            keys.append([a0 % LAP, u_ap, "apex"])
            keys.append([a1 % LAP, u_ap, "apex"])
        else:
            keys.append([s_ap % LAP, u_ap, "apex"])
        keys.append([s_out % LAP, u_out, "edge"])

    keys.sort(key=lambda k: k[0])

    # --- resolve collisions cyclically ------------------------------------
    def cyc_gap(a, b):
        d = (b - a) % LAP
        return d if d < LAP * 0.5 else d - LAP

    changed = True
    while changed and len(keys) > 6:
        changed = False
        n = len(keys)
        for i in range(n):
            j = (i + 1) % n
            gap = cyc_gap(keys[i][0], keys[j][0])
            if gap > 26.0:
                continue
            a, b = keys[i], keys[j]
            if a[2] == "edge" and b[2] == "edge":
                s_new = (a[0] + gap * 0.5) % LAP
                keys[i] = [s_new, (a[1] + b[1]) * 0.5, "edge"]
                keys.pop(j)
            elif a[2] == "edge" and b[2] == "apex":
                keys.pop(i)              # no room to swing wide before the apex
            elif a[2] == "apex" and b[2] == "edge":
                keys.pop(j)              # no room to track out before the next entry
            else:
                keys[i] = [a[0], (a[1] + b[1]) * 0.5, "apex"]
                keys.pop(j)
            changed = True
            break

    # --- long straights: nobody holds the white line for 800 m --------------
    # Between a track-out and the next turn-in on the SAME side of the road the
    # purely geometric answer is "stay pinned to the edge".  Real cars ease back
    # toward the middle and come out again — the edge is dirty, it is off the
    # rubber, and there is nothing to gain.  One relaxation key per long same-side
    # gap produces exactly that bulge, and it is what puts the rubbered-in band of
    # the 810 m pit straight where the onboard follow needs it.
    nk = len(keys)
    relax = []
    for i in range(nk):
        a, b = keys[i], keys[(i + 1) % nk]
        gap = cyc_gap(a[0], b[0])
        if gap < 190.0 or a[2] != "edge" or b[2] != "edge":
            continue
        if a[1] * b[1] <= 0:
            continue                          # opposite sides: the line crosses anyway
        relax.append([(a[0] + gap * 0.5) % LAP, (a[1] + b[1]) * 0.5 * 0.40, "relax"])
    keys.extend(relax)
    keys.sort(key=lambda k: k[0])

    # --- how much width is there TIME to use? -------------------------------
    # Out-in-out is only free when there is room.  Between two corners 40-55 m apart
    # (the esse links, S12 between T12 and T13) the geometric answer swings the car
    # from edge to edge, which is a 14 m radius at 115 km/h — about 25 g.  A car that
    # moves Du sideways over L metres of road, on a raised-cosine, needs a path
    # curvature of  2*Du/L^2 * pi^2/2 ; inverting it against the fraction of the §7
    # lateral budget a driver will spend on placement rather than on cornering gives
    # the excursion the road actually affords, and clamping each edge key to it is
    # what turns a zig-zag into a flowing line through the esses.
    def a_lat_of(vv):
        return min(15.0 + 0.0050 * vv * vv, 48.0)

    nk = len(keys)
    for i in range(nk):
        if keys[i][2] == "apex":
            continue
        lo, hi = -99.0, 99.0
        for step in (-1, 1):
            j = i
            for _ in range(nk):
                j = (j + step) % nk
                if keys[j][2] == "apex":
                    break
            Lg = abs(cyc_gap(keys[i][0], keys[j][0]))
            sm = (keys[i][0] + cyc_gap(keys[i][0], keys[j][0]) * 0.5) % LAP
            vv = max(float(_fsample(_S["speed"], sm)), 10.0)
            kuse = 0.55 * a_lat_of(vv) / (vv * vv)
            du = 2.0 * kuse * Lg * Lg / (math.pi ** 2)
            lo = max(lo, keys[j][1] - du)
            hi = min(hi, keys[j][1] + du)
        if lo > hi:
            lo = hi = 0.5 * (lo + hi)
        keys[i][1] = float(np.clip(keys[i][1], lo, hi))

    ks = np.array([k[0] for k in keys])
    ku = np.array([k[1] for k in keys])
    o = np.argsort(ks)
    ks, ku = ks[o], ku[o]

    g = _fgrid()
    line = _pchip_cyclic(ks, ku, g, LAP)
    line = _csmooth(line, 4.0)                     # kills the C2 kinks at the keys
    lim = _S["half_w"] - 0.35
    line = np.clip(line, -lim, lim)
    line = _enforce_drivable(line, lim)
    _S["line"] = line
    _S["line_keys"] = (ks, ku)


def _line_curvature(line):
    X, Y, H, _ = _centreline_arrays(_fgrid())
    px = X - np.sin(H) * line
    py = Y + np.cos(H) * line

    def d(a):
        return (np.roll(a, -1) - np.roll(a, 1)) / (2 * _FS)
    dx, dy = d(px), d(py)
    ddx, ddy = d(dx), d(dy)
    k = np.abs(dx * ddy - dy * ddx) / np.maximum((dx * dx + dy * dy) ** 1.5, 1e-12)
    # The surface centreline is arcs and straights with no clothoids (see the module
    # note: the §6.1 transitions belong to the driven line, not to the road, or the
    # road stops matching telemetry.csv).  Curvature therefore STEPS at every element
    # joint, and a difference stencil turns each step into a spike.  A 2 m filter
    # removes the artefact and leaves what a car and a tyre actually integrate over.
    return _csmooth(k, 2.0)


def _enforce_drivable(line, lim):
    """The drawn line must be a line the SPEC'S OWN CAR could drive.

    Pure out-in-out geometry produces nonsense where two same-direction corners are
    close together — between T12 and T13 (55 m apart) it swung the car to the far
    edge and back, a 14 m radius at 115 km/h, i.e. about 25 g.  So the line is
    relaxed until its curvature satisfies the §7 vehicle model everywhere:

        v(s)^2 * kappa(s)  <=  a_lat(v) = min(15.0 + 0.0050 v^2, 48.0)

    with v(s) taken from telemetry.csv.  Relaxation is a curvature-weighted cyclic
    Laplacian, so it only touches the stations that are actually over the limit and
    leaves every apex — which is under the limit by construction, the line's radius
    being larger than the track's — exactly where it was placed.
    """
    v = np.maximum(_S["speed"], 8.0)
    a_lat = np.minimum(15.0 + 0.0050 * v * v, 48.0)
    _, _, _, kc = _centreline_arrays(_fgrid())
    # The spec solved every apex speed so that the CENTRELINE sits exactly on the
    # lateral limit, so "a_lat/v^2" alone leaves the line no headroom at all inside a
    # corner.  The honest ceiling is therefore the looser of two statements: the line
    # is never tighter than the corner it is in, and it never exceeds the model's
    # lateral capacity by more than the ~2 % a real line gains.
    def ceiling(ln):
        # "never tighter than riding the inside edge of the corner it is in": an
        # offset curve concentric with the centreline has curvature k/(1-u*k), and
        # inside a 176 deg hairpin that IS the racing line, so the concentric value
        # is the honest floor on the allowed radius.  The vehicle-model term is the
        # other half; the looser of the two governs.
        conc = np.abs(kc) / np.maximum(1.0 - ln * kc, 0.35)
        return np.maximum(np.maximum(1.06 * conc, 1.03 * a_lat / (v * v)), 1.0 / 900.0)

    kmax = ceiling(line)
    best = line.copy()
    worst = float((_line_curvature(line) / kmax - 1.0).max())
    sigma = 6.0
    for it in range(240):
        if worst < 0.06:
            break
        kmax = ceiling(line)
        ex = _line_curvature(line) / kmax - 1.0
        # The relief mask must itself be smooth on the scale of the smoothing, or the
        # blend introduces a fresh kink at the mask edge and the solve runs away.
        w = _csmooth(np.clip((ex - 0.05) / 0.7, 0.0, 1.0), max(sigma * 0.9, 4.0))
        w = w / max(w.max(), 1e-6) * min(float(np.clip(ex.max(), 0, 1)), 1.0)
        cand = np.clip(line * (1.0 - 0.22 * w) + _csmooth(line, sigma) * (0.22 * w),
                       -lim, lim)
        wc = float((_line_curvature(cand) / ceiling(cand) - 1.0).max())
        if wc < worst:
            line, worst, best = cand, wc, cand.copy()
        else:
            sigma = sigma * 1.35                 # this scale is exhausted; go wider
            if sigma > 55.0:
                break
    line = best
    _S["line_curv_residual"] = worst
    _S["line_min_radius"] = float(1.0 / max(_line_curvature(line).max(), 1e-9))
    _S["line_lat_g_max"] = float((_S["speed"] ** 2 * _line_curvature(line) / 9.81).max())
    return line


def racing_line_offset(s):
    """Lateral offset (m, +ve = left of the direction of travel) of the driven line."""
    return _fsample(_S["line"], s)


# ============================================================================
#  9. USAGE FIELDS from the telemetry  (rubber, spread, braking, polish)
# ============================================================================
def _build_usage(spec, tel):
    g = _fgrid()
    if tel is not None:
        o = np.argsort(tel["s"])
        v = np.interp(g, tel["s"][o], tel["v"][o])
        al = np.interp(g, tel["s"][o], tel["a_long"][o])
        at = np.interp(g, tel["s"][o], tel["a_lat"][o])
    else:                                   # fallback: corner table only
        v = np.full(_FN, 60.0); al = np.zeros(_FN); at = np.zeros(_FN)

    accel = np.clip(al / 9.0, 0, 1)          # traction rubber laid on corner exit
    brake = np.clip(-al / 26.0, 0, 1)        # lock-up / scrub under braking
    lat = np.clip(at / 45.0, 0, 1)

    rubber = np.clip(0.46 + 0.80 * accel + 0.62 * brake + 0.58 * lat, 0.0, 1.35)
    rubber = _csmooth(rubber, 16.0)

    # where the cars are all on the same line the band is narrow; on a straight they
    # fan out and the deposit spreads
    spread = np.clip(3.7 - 2.4 * lat - 0.6 * brake, 1.05, 3.9)
    spread = _csmooth(spread, 22.0)

    brake_f = _csmooth(np.clip(brake ** 1.15, 0, 1), 7.0)
    polish = _csmooth(np.clip(0.25 + 0.6 * lat + 0.45 * accel, 0, 1), 30.0)

    _S["rubber"] = rubber
    _S["spread"] = spread
    _S["brake"] = brake_f
    _S["polish"] = polish
    _S["speed"] = _csmooth(v, 8.0)
    # the "one plane" zones of spec §2 (pit straight + transit route) used to be built
    # here and used by the crown and the undulation.  Both moved into C.ground_z, which
    # carries the same field; nothing in this module needs it any more.


# ============================================================================
# 10. RESURFACING ZONES  (macro anti-tiling: the lap is not one age of asphalt)
# ============================================================================
# station of each transverse construction joint, and the age of the slab that FOLLOWS
# it.  A real circuit is resurfaced in campaigns; the joints land where a resurfacing
# contract stopped, which is always at a corner exit or a straight end, never mid-apex.
RESURFACE = [
    (0.0,    0.10, 4.35, 0.55),   # (joint station, age 0..1, paving-lane width, lane phase)
    (250.0,  0.62, 4.75, 0.15),
    (789.3,  0.30, 4.05, 0.80),
    (1025.3, 0.86, 4.55, 0.40),
    (1315.5, 0.22, 4.20, 0.05),
    (1904.0, 0.71, 4.85, 0.62),
    (2403.0, 0.44, 4.40, 0.28),
    (2746.0, 0.93, 4.10, 0.72),
    (3115.0, 0.06, 4.65, 0.48),   # the pit straight is the freshest — it is resurfaced
]                                 # every year because it takes the start


def _build_zones():
    g = _fgrid()
    edges = np.array([r[0] for r in RESURFACE])
    idx = np.clip(np.searchsorted(edges, g, side="right") - 1, 0, len(RESURFACE) - 1)
    age = np.array([r[1] for r in RESURFACE])[idx]
    _S["zone_age"] = age
    _S["zone_idx"] = idx


# ============================================================================
# 11. SURFACE ELEVATION  z(s, u)  =  C.ground_z  +  the racing-line micro layer
# ============================================================================
#
# `C.ground_z` carries everything that another module can see: the centreline
# elevation, the banking, the drainage crown, the low-frequency undulation, the
# negative-kerb troughs, the 12 mm verge drain and — outboard of verge_edge — the
# -1.6 % runoff fall.  It IS this module's old `surface_z` minus the two terms below.
#
# What stays private here is the pair of terms that depend on the RACING LINE: a 9 mm
# compaction dip along the driven line and a 4.5 mm washboard in the heavy braking
# zones.  They are private because computing them needs the 240-iteration drivability
# solve in §8, and dragging that into a file five builders import at load time would
# be absurd for a term that is already sub-millimetre at the track edge.
#
# Contract §2 permits exactly that, under two conditions, and both are enforced by
# construction rather than promised:
#     |extra| <= C.MICRO_LAYER_MAX_M   -> np.clip
#     extra  == 0 for |u| >= half_width -> multiplied by C.micro_window
# so no other module can ever see this layer, and the road cannot part company with
# the kerb that sits on it.

def _micro(S, U):
    """This module's PRIVATE micro layer.  Bounded and windowed; see contract §2."""
    d = U - _fsample(_S["line"], S)
    rub = _fsample(_S["rubber"], S)
    brk = _fsample(_S["brake"], S)
    z = -0.0090 * rub * np.exp(-(d / 2.8) ** 2)
    z += 0.0045 * brk * np.sin(S * (2 * math.pi / 1.85)) * np.exp(-(d / 3.4) ** 2)
    z = np.clip(z, -C.MICRO_LAYER_MAX_M, C.MICRO_LAYER_MAX_M)
    return z * C.micro_window(S, U)


def surface_z(s, u):
    """Surface elevation at (lap station, signed lateral offset, +ve = LEFT).

    == C.ground_z(s, u) + this module's racing-line micro layer.  Other modules should
    call C.ground_z; this exists for the mesh builders here and for anything that
    genuinely wants the driven-line compaction dip (the car, the tyre contact patch).
    """
    scalar = (np.ndim(s) == 0 and np.ndim(u) == 0)
    if "line" not in _S:
        prepare()
    S = np.atleast_1d(np.asarray(s, float))
    U = np.atleast_1d(np.asarray(u, float))
    S, U = np.broadcast_arrays(S, U)
    z = C.ground_z(S, U) + _micro(S, U)
    return float(z.reshape(-1)[0]) if scalar else z


def su_to_world(s, u):
    x, y, _z, h, _k = centreline(s)
    nx, ny = -math.sin(h), math.cos(h)
    return (x + nx * u, y + ny * u, float(surface_z(s, u)))


def outer_edge(s, side):
    """Outermost point of this module's geometry (side = +1 left, -1 right).

    This is C.verge_edge(s) exactly — half_width + 1.50 m kerb band + 1.00 m painted
    verge — and it is the surface build_barriers' runoff platform butts to.
    """
    return su_to_world(s, side * float(C.verge_edge(s)))


# ============================================================================
# 12. KERB PLAN
# ============================================================================
#  side: 'in'  = inside of the corner (apex side), 'out' = outside.
#  f0/f1 are fractions of the arc length measured from the arc start, so a run can
#  begin before the geometric corner and end after it — which is what real kerbs do.
#  Every entry carries the reason it is there.
KERB_PLAN = {
    "T1":  [("in", -0.06, 1.12, "apex kerb, 330 km/h braking zone runs onto it"),
            ("out", -0.34, 0.06, "turn-in kerb: the car is still braking at the edge"),
            ("out", 0.62, 1.62, "exit kerb, wide open onto the T1-T2 link")],
    "T2":  [("in", -0.05, 1.20, "apex kerb of the linked left"),
            ("out", 0.70, 1.90, "exit kerb onto the east chute")],
    "T3":  [("in", -0.08, 1.15, "295 km/h kink: the apex kerb is the only one used"),
            ("out", 0.60, 1.75, "exit kerb, 4.89 g runs the car straight to the edge")],
    "T4":  [("in", -0.04, 1.10, "hairpin apex kerb — the hero corner of the film"),
            ("out", -0.58, 0.04, "entry kerb after 143.8 m of downhill braking"),
            ("out", 0.86, 1.70, "exit kerb at the foot of La Rampe")],
    "T5":  [("in", -0.03, 1.10, "apex kerb, uphill right"),
            ("out", 0.74, 1.75, "exit kerb onto the climb straight")],
    "T6":  [("in", -0.05, 1.22, "esse 1 apex"),
            ("out", 0.80, 2.05, "exit kerb; also serves as T7's turn-in kerb")],
    "T7":  [("in", -0.05, 1.22, "esse 2 apex"),
            ("out", 0.80, 1.95, "exit kerb into T8")],
    "T8":  [("in", -0.05, 1.25, "summit apex, off-camber; split by the negative kerb"),
            ("out", 0.85, 1.90, "exit kerb, car light over the crest")],
    "T9":  [("in", -0.05, 1.32, "esse 4 apex"),
            ("out", 0.85, 2.10, "exit kerb onto the summit run")],
    "T10": [("in", -0.04, 1.06, "first apex of the increasing-radius sweeper"),
            ("out", -0.30, 0.05, "turn-in kerb, 281 km/h")],
    "T11": [("in", -0.06, 1.12, "second apex, car accelerating to 294 km/h"),
            ("out", 0.78, 2.00, "long exit kerb — 55 m of runoff behind it")],
    "T12": [("in", -0.10, 1.22, "apex of the downhill heavy-braking left"),
            ("out", -0.75, 0.02, "turn-in kerb at the low point"),
            ("out", 0.90, 2.40, "exit kerb; split by the negative kerb")],
    "T13": [("in", -0.05, 1.55, "short slow left, the kerb outlives the arc"),
            ("out", 1.00, 2.60, "exit kerb through the link to T14")],
    "T14": [("in", -0.06, 1.45, "right flick apex"),
            ("out", 0.90, 2.40, "exit kerb into the T15 approach")],
    "T15": [("in", -0.04, 1.18, "final corner apex, 207 km/h onto the pit straight"),
            ("out", 0.72, 1.85, "exit kerb, 30 m of asphalt runoff behind it")],
}


def _build_kerb_runs(spec):
    els = {e["tag"]: e for e in _S["els"]}
    dirs = {c["name"].split()[0]: c["direction"] for c in spec["corners"]}
    runs = []
    for tag, plan in KERB_PLAN.items():
        e = els[tag]
        sg_in = 1.0 if dirs[tag] == "left" else -1.0
        for k, (side, f0, f1, why) in enumerate(plan):
            sgn = sg_in if side == "in" else -sg_in
            s0 = e["s0"] + e["L"] * f0
            s1 = e["s0"] + e["L"] * f1
            runs.append(dict(tag=tag, side=side, sign=sgn, s0=s0, s1=s1,
                             idx=k, why=why))

    # --- negative kerbs (spec §9): T8 apex, T12 exit ------------------------
    # The TROUGH is cut by C.ground_z, so its stations come from the contract or the
    # serrated runs would be split somewhere other than where the road actually dips.
    neg = [(float(a), float(b), float(sd)) for (a, b, sd) in C.NEG_KERBS]
    _S["neg_kerbs"] = neg

    # split any serrated run that the trough occupies
    out = []
    for r in runs:
        pieces = [(r["s0"], r["s1"])]
        for (a, b, side) in neg:
            if abs(side - r["sign"]) > 1e-6:
                continue
            nxt = []
            for (p0, p1) in pieces:
                if b < p0 - 1.0 or a > p1 + 1.0:
                    nxt.append((p0, p1)); continue
                if a - 1.6 > p0 + 3.0:
                    nxt.append((p0, a - 1.6))
                if b + 1.6 < p1 - 3.0:
                    nxt.append((b + 1.6, p1))
            pieces = nxt
        for j, (p0, p1) in enumerate(pieces):
            q = dict(r); q["s0"] = p0; q["s1"] = p1
            q["name"] = "%s%s_%s%d%s" % (PFX + "Kerb_", r["tag"], r["side"], r["idx"],
                                         "" if len(pieces) == 1 else chr(97 + j))
            out.append(q)
    _S["kerb_runs"] = out

    # per-station, per-side "is there a kerb here" for the verge paint mask
    g = _fgrid()
    for side, key in ((1.0, "kerb_L"), (-1.0, "kerb_R")):
        f = np.zeros(_FN)
        for r in out:
            if abs(r["sign"] - side) > 1e-6:
                continue
            a, b = r["s0"] % LAP, r["s1"] % LAP
            m = (g >= a) & (g <= b) if a < b else ((g >= a) | (g <= b))
            f[m] = 1.0
        for (a, b, sd) in neg:
            if abs(sd - side) > 1e-6:
                continue
            a %= LAP; b %= LAP
            m = (g >= a) & (g <= b) if a < b else ((g >= a) | (g <= b))
            f[m] = 1.0
        _S[key] = _csmooth(f, 1.2)


# ============================================================================
# 13. MESH PLUMBING
# ============================================================================
def _new_mesh(name, co, quads, smooth=True):
    me = bpy.data.meshes.new(name)
    nv = co.shape[0]; npo = quads.shape[0]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(co, dtype=np.float32).ravel())
    me.loops.add(npo * 4)
    me.loops.foreach_set("vertex_index",
                         np.ascontiguousarray(quads, dtype=np.int32).ravel())
    me.polygons.add(npo)
    me.polygons.foreach_set("loop_start",
                            (np.arange(npo, dtype=np.int32) * 4))
    me.update()
    me.validate(verbose=False)
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(npo, dtype=bool))
    return me


def _add_uv(me, name, uv):
    lay = me.uv_layers.new(name=name)
    lay.uv.foreach_set("vector", np.ascontiguousarray(uv, dtype=np.float32).ravel())


def _add_col(me, name, data):
    at = me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    at.data.foreach_set("color", np.ascontiguousarray(data, dtype=np.float32).ravel())


def _obj(name, me, coll, mat):
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    coll.objects.link(ob)
    return ob


# ============================================================================
# 14. ROW / COLUMN LAYOUT
# ============================================================================
def _row_stations():
    ss = [0.0]
    while ss[-1] < LAP:
        s = ss[-1]
        R = _local_radius(s)
        ds = ROW_DS_MAX if R is None else min(ROW_DS_MAX, math.sqrt(8.0 * R * ROW_SAGITTA))
        for (a, b) in HERO_ZONES:
            if a <= s <= b:
                ds = min(ds, HERO_DS)
        # resolve every element boundary and every resurfacing joint on a row
        for e in _S["els"]:
            d = e["s0"] - s
            if 0 < d < ds:
                ds = max(d, 0.02)
        for r in RESURFACE:
            d = r[0] - s
            if 0 < d < ds:
                ds = max(d, 0.02)
        ss.append(s + max(ds, ROW_DS_MIN))
    ss = np.array(ss[:-1])
    return ss


def _col_layout():
    """(kind, value) per column, ordered right (-u) to left (+u).
       kind 0 = fraction of the half width, kind 1 = metres outboard of the edge."""
    kerb = [0.125 * i for i in range(1, 13)]          # 12 -> 1.50 m
    verge = [KERB_BAND + 0.2 * i for i in range(1, 6)]  # 5  -> 2.50 m
    cols = []
    for o in reversed(kerb + verge):
        cols.append((1, -o))
    for i in range(N_RS_COLS):
        cols.append((0, -1.0 + 2.0 * i / (N_RS_COLS - 1)))
    for o in kerb + verge:
        cols.append((1, o))
    return cols


# ============================================================================
# 15. THE ROAD MESH
# ============================================================================
def _build_road(coll, mat):
    S1 = _row_stations()
    nr = len(S1)
    cols = _col_layout()
    nc = len(cols)

    S = np.repeat(S1[:, None], nc, axis=1)
    Wh = track_half_width(S)
    U = np.empty_like(S)
    band = np.empty(nc)
    for j, (kind, val) in enumerate(cols):
        if kind == 0:
            U[:, j] = val * Wh[:, j]
            band[j] = 0.0
        else:
            U[:, j] = np.sign(val) * (Wh[:, j] + abs(val))
            band[j] = 0.5 if abs(val) <= KERB_BAND + 1e-9 else 1.0

    X, Y, H, _K = _centreline_arrays(S.ravel())
    X = X.reshape(S.shape); Y = Y.reshape(S.shape); H = H.reshape(S.shape)
    NX = -np.sin(H); NY = np.cos(H)
    # THE DATUM, plus this module's windowed micro layer.  The crown, the banking, the
    # undulation, the negative-kerb troughs and the 12 mm verge drain are all inside
    # C.ground_z now — the last of those used to be added here, one line below, which
    # is precisely how it came to be a number that only this module knew about.
    Z = surface_z(S, U)

    co = np.stack([X + NX * U, Y + NY * U, Z], axis=-1).reshape(-1, 3)

    idx = np.arange(nr * nc).reshape(nr, nc)
    idx_next = np.roll(idx, -1, axis=0)          # cyclic weld at the start/finish line
    quads = np.stack([idx[:, :-1], idx_next[:, :-1], idx_next[:, 1:], idx[:, 1:]],
                     axis=-1).reshape(-1, 4)

    me = _new_mesh(PFX + "Track", co, quads)

    # ---- per-loop UVs (metric).  The wrap row is given s = LAP, not s = 0, so the
    # station coordinate is continuous across the start/finish line.
    Sl = S.copy()
    Sw = S.copy(); Sw[0, :] = LAP                     # station as seen by the wrap quad
    line = _fsample(_S["line"], S)
    lw = line.copy(); lw[0, :] = _fsample(_S["line"], np.array([LAP - 1e-6]))[0]

    def loopvals(a_this, a_next):
        # quad corner order: (r,c) (r+1,c) (r+1,c+1) (r,c+1)
        return np.stack([a_this[:, :-1], a_next[:, :-1],
                         a_next[:, 1:], a_this[:, 1:]], axis=-1).reshape(-1, 4)

    Sn = np.roll(Sl, -1, axis=0); Sn[-1, :] = Sw[0, :]
    Un = np.roll(U, -1, axis=0)
    Ln = np.roll(line, -1, axis=0); Ln[-1, :] = lw[0, :]

    uv_s = loopvals(Sl, Sn).ravel()
    uv_u = loopvals(U, Un).ravel()
    uv_d = uv_u - loopvals(line, Ln).ravel()
    _add_uv(me, "uv_su", np.stack([uv_u, uv_s], axis=-1))
    _add_uv(me, "uv_rl", np.stack([uv_d, uv_s], axis=-1))

    # ---- per-vertex fields
    rub = _fsample(_S["rubber"], S)
    spr = _fsample(_S["spread"], S)
    brk = _fsample(_S["brake"], S)
    pol = _fsample(_S["polish"], S)
    _add_col(me, "trk", np.stack([rub, spr / 8.0, brk, pol], axis=-1).reshape(-1, 4))

    kl = _fsample(_S["kerb_L"], S)
    kr = _fsample(_S["kerb_R"], S)
    kp = np.where(U >= 0, kl, kr)
    age = _fsample(_S["zone_age"], S)
    bandv = np.repeat(band[None, :], nr, axis=0)
    _add_col(me, "geo", np.stack([Wh / 16.0, kp, bandv / 2.0, age],
                                 axis=-1).reshape(-1, 4))

    ob = _obj(PFX + "Track", me, coll, mat)
    return ob, nr, nc, quads.shape[0]


# ============================================================================
# 16. KERBS  (every one generated individually — no instancing, no arrays)
# ============================================================================
def _kerb_profile_cols():
    """Across-kerb columns: (t 0..1 across the 1.50 m, extra dz, kind).

    kind 0 = ordinary column, 1 = outer vertical face, 2 = INNER VERTICAL RISER.

    THE RISER WAS MISSING.  spec S9 puts the kerb 25 mm proud at its track-side lip,
    and the profile duly started at +21 mm above the road — with nothing between the
    two.  The kerb was an open shell whose leading edge floated 21 mm over the asphalt
    along all 35 runs: a 21 mm slot at a 12.47 deg sun with a 4.52 shadow ratio, i.e.
    a dark line down the inside of every kerb on the circuit, and a place a ray can get
    under the geometry.  Two columns at t = 0.000 now make that step a real vertical
    face, and its bottom sits `C.BASE_EMBED_M` (20 mm) INTO the datum, which is the
    contract's own published embed for anything standing on the ground and what stops a
    10 mm mesh tolerance opening a lit gap under it.
    """
    return [
        (0.000,  0.000, 2),   # skirt bottom: C.BASE_EMBED_M below the road
        (0.000, -0.004, 0),   # track-side arris, the top of the 25 mm riser
        (0.035,  0.000, 0),
        (0.140,  0.000, 0),
        (0.330,  0.000, 0),
        (0.530,  0.000, 0),
        (0.730,  0.000, 0),
        (0.900,  0.000, 0),
        (0.968, -0.006, 0),   # outer arris chamfer
        (1.000, -0.016, 0),
        (1.000, -0.062, 1),   # vertical outer face down to the verge
    ]


def _build_kerbs(coll, mat):
    objs = []
    prof = _kerb_profile_cols()
    nc = len(prof)
    tris = 0
    for ri, r in enumerate(_S["kerb_runs"]):
        seed = ri * 7919 + 13
        rng = np.random.default_rng(seed)
        L = r["s1"] - r["s0"]
        if L < 4.0:
            continue
        n = max(int(round(L / KERB_DS)), 8)
        S1 = r["s0"] + np.arange(n + 1) * (L / n)
        along = S1 - r["s0"]

        # ---- per-kerb identity ------------------------------------------------
        # precast sections: real kerbs are cast in ~2 m units and never lie perfectly
        # flush.  Section length, height step and roll differ per kerb AND per unit.
        sec_len = float(rng.uniform(1.85, 2.25))
        sec_i = np.floor(along / sec_len).astype(int)
        nsec = int(sec_i.max()) + 2
        sec_dz = rng.normal(0.0, 0.0022, nsec)[sec_i]
        sec_roll = rng.normal(0.0, 0.0035, nsec)[sec_i]
        sec_amp = 1.0 - np.abs(rng.normal(0.0, 0.10, nsec))[sec_i]

        # paint blocks: 1.00 m nominal (spec), jittered because they are hand-painted
        blk_len = float(rng.uniform(0.955, 1.055))
        blk_phase = float(rng.uniform(0.0, 1.0))
        blk = along / blk_len + blk_phase

        # serration phase relative to the paint, different on every kerb
        ser_phase = float(rng.uniform(0.0, 1.0))
        pitch = 0.250
        ph = (along / pitch + ser_phase) % 1.0
        # rounded sawtooth: fast rise, long fall — the profile a cast kerb actually has
        serr = np.where(ph < 0.42, 0.5 - 0.5 * np.cos(math.pi * ph / 0.42),
                        0.5 + 0.5 * np.cos(math.pi * (ph - 0.42) / 0.58))

        # wear: peaks at the point the cars actually strike, which is the apex end of
        # an inside kerb and the far end of an exit kerb
        wpos = 0.42 if r["side"] == "in" else 0.72
        wear = np.exp(-((along / L - wpos) / 0.30) ** 2)
        wear = np.clip(wear * float(rng.uniform(0.55, 1.0))
                       + 0.18 * _vnoise1(along * 0.35, seed) , 0, 1)
        # impact damage: a handful of individually knocked-down serrations
        chip = np.zeros_like(along)
        for _ in range(int(rng.integers(2, 7))):
            c = float(rng.uniform(0.05, 0.95)) * L
            w = float(rng.uniform(0.25, 1.4))
            chip += np.exp(-((along - c) / w) ** 2) * float(rng.uniform(0.4, 1.0))
        chip = np.clip(chip, 0, 1)

        # end ramps — a kerb tapers into the road, it does not start as a 50 mm step
        ramp_in = float(rng.uniform(1.1, 2.4))
        ramp_out = float(rng.uniform(1.3, 2.8))
        taper = np.clip(along / ramp_in, 0, 1) * np.clip((L - along) / ramp_out, 0, 1)
        taper = taper ** 0.8

        Wh = track_half_width(S1)
        sgn = r["sign"]

        S = np.repeat(S1[:, None], nc, axis=1)
        T = np.array([p[0] for p in prof])[None, :]
        DZ = np.array([p[1] for p in prof])[None, :]
        FACE = np.array([p[2] for p in prof])[None, :]

        u = sgn * (Wh[:, None] + T * KERB_BAND)
        # spec §9: 25 mm proud at the track-side lip, 50 mm at the outer lip,
        # 25 mm serration amplitude on a 250 mm pitch => 75 mm peak.
        base = 0.025 + 0.025 * T
        ser_amp = 0.025 * (0.25 + 0.75 * T)
        sw = (1.0 - 0.55 * wear[:, None]) * sec_amp[:, None] * (1.0 - 0.75 * chip[:, None])
        h = base + ser_amp * serr[:, None] * sw
        h = h * taper[:, None] + DZ
        h = h + sec_dz[:, None] + sec_roll[:, None] * (T - 0.5) * KERB_BAND
        h = np.where(FACE == 1, np.minimum(h, -0.004), h)
        h = np.where(FACE == 2, -C.BASE_EMBED_M, h)

        # the kerb sits ON the datum.  C.micro_window is identically zero for
        # |u| >= half_width and every kerb column is outboard of it, so the road mesh
        # and the kerb foot meet at exactly the same z with nothing to reconcile.
        road = C.ground_z(S, u)
        Z = road + h

        X, Y, H, _ = _centreline_arrays(S.ravel())
        X = X.reshape(S.shape); Y = Y.reshape(S.shape); H = H.reshape(S.shape)
        co = np.stack([X - np.sin(H) * u, Y + np.cos(H) * u, Z], axis=-1).reshape(-1, 3)

        idx = np.arange((n + 1) * nc).reshape(n + 1, nc)
        if sgn > 0:
            quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                             axis=-1).reshape(-1, 4)
        else:
            quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                             axis=-1).reshape(-1, 4)

        me = _new_mesh(r["name"], co, quads)
        _add_uv(me, "uv_k", _kerb_uv(T, along, n, nc, sgn))

        hue = float(rng.uniform(0.0, 1.0))
        val = float(rng.uniform(0.0, 1.0))
        # Paint wears off the SERRATION RIDGES, not off "the high side of the kerb".
        # Baking absolute height here made the wear mask a smooth ramp across the
        # width, and the shader turned it into fog over the whole kerb.  What the
        # shader needs is the serration phase itself, so the concrete shows through in
        # crisp bands on the ridge tops the way a struck kerb actually looks.
        ridge = np.repeat(serr[:, None], nc, axis=1)
        rub = np.clip((0.35 + 0.9 * wear) * float(rng.uniform(0.5, 1.0)), 0, 1)
        nv = (n + 1) * nc
        _add_col(me, "kb", np.stack([
            (blk[:, None] / 256.0 + np.zeros_like(T)).ravel(),
            (wear[:, None] + np.zeros_like(T)).ravel(),
            (rub[:, None] + np.zeros_like(T)).ravel(),
            ridge.ravel()], axis=-1).reshape(nv, 4))
        _add_col(me, "kb2", np.stack([
            np.full(nv, hue), np.full(nv, val),
            (chip[:, None] + np.zeros_like(T)).ravel(),
            (T + np.zeros_like(S)).ravel()], axis=-1))

        ob = _obj(r["name"], me, coll, mat)
        ob["kerb_reason"] = r["why"]
        objs.append(ob)
        tris += quads.shape[0] * 2
    return objs, tris


def _kerb_uv(T, along, n, nc, sgn):
    a = np.repeat(along[:, None], nc, axis=1)
    t_all = np.repeat(T, n + 1, axis=0)

    def lv(x):
        if sgn > 0:
            q = np.stack([x[:-1, :-1], x[1:, :-1], x[1:, 1:], x[:-1, 1:]], axis=-1)
        else:
            q = np.stack([x[:-1, :-1], x[:-1, 1:], x[1:, 1:], x[1:, :-1]], axis=-1)
        return q.reshape(-1, 4).ravel()
    return np.stack([lv(t_all) * KERB_BAND, lv(a)], axis=-1)


# ============================================================================
# 17. THE ACCESS RIBBON  (unrubbered concrete, mu 0.90 — spec §7 / §10.5)
# ============================================================================
#
# BEAT 4 WAS A COPLANAR Z-FIGHT FOR ITS WHOLE LENGTH.  Scanning world y = 0 from
# x = -5 to +111, the winning surface flipped SIX times over 116 m between
# SURF_AccessRoad, ARCH_Paving_Paddock, ARCH_Paving_Apron and ARCH_Markings, at
# separations of 1.4-9.0 mm.  At 4K with a flying camera that is stroboscopic depth
# fighting straight through the beat the brief calls the world-design linchpin.
#
# THE RULE THAT FIXES IT IS `C.TOL_COPLANAR_M`'s: CUT, DO NOT OFFSET.  The contract
# gives build_surface the driving surface and gives build_architecture a polygon to
# cut its paving to — `C.access_ribbon_polygon(margin=0.30)`.  This function builds
# EXACTLY that polygon's interior, so architecture's cut line and this mesh's boundary
# are the same line and there is nothing left to overlap.
#
# THREE THINGS THIS GEOMETRY GETS FROM THE CONTRACT, NOT FROM ITSELF
#
#   route      `C.access_route_arrays` — the spec §10.5 legs: 49.60 m straight from the
#              glass plane, R150 / 40 deg left merge arc, then the pit-straight heading.
#
#   edges      `C.access_edges` — the inboard edge is CLIPPED so the ribbon can never
#              cross SURF_Track's own cross-section.  The clip first engages at route
#              station t = 95.33 m; unclipped, the old ribbon ran 74 mm UNDER the
#              racing surface for the last 59 m of the merge.
#
#   z          `C.ground_z` — and this is the one place this module DEPARTS from a
#              contract v1.0.0 function, deliberately and with the measurement:
#
#              `C.access_z(t, v)` eases from the flat apron onto `ground_z` with a
#              weight that is a function of t alone, finishing at the merge point
#              t = 154.32.  But the ribbon starts SHARING AN EDGE with SURF_Track at
#              t = 95.33, so along 59 m of that shared edge `access_z` sits up to
#              80.4 mm above `ground_z` (max 88.4 mm anywhere on the ribbon).  That is
#              8x `C.TOL_SEAM_M` on a boundary two modules share, in the beat the
#              camera flies at rooftop height.
#
#              Measured instead:  `C.ground_z` is ALREADY exactly 0.000000 over the
#              whole 49.60 m apron run, at every lateral across the ribbon and 0.30 m
#              beyond both edges — the contract's own apron tie (§7) does it, because
#              `apron_zone` is 1.000 along the whole approach.  So the ribbon is built
#              on `ground_z` and nothing else:
#
#                * spec §10.3(b)'s "first 50 m outside the glass exactly 0 % and
#                  exactly level with the interior floor" is satisfied EXACTLY, not to
#                  a tolerance — max |z| over the apron run is 0.000000 m;
#                * the join to SURF_Track is 0.000 mm for the whole 149 m the two
#                  meshes share an edge, not 80 mm;
#                * there is ONE datum function under the whole beat, which is the
#                  entire point of the contract.
#
#              `access_z` is therefore redundant and should be retired or redefined as
#              `ground_z` in the next contract revision.  Reported, not assumed: see
#              `verify()`, which measures both numbers on every build.
#
# THE SAWN EDGE STRIP.  `access_ribbon_polygon`'s default 0.30 m margin is described in
# the contract as "the sawn edge strip build_surface lays along the ribbon".  It is laid
# here — but only where the edge is FREE, i.e. where it butts architecture's slab.  Where
# the inboard edge has converged onto SURF_Track's painted verge there is no slab to butt
# to and a 0.30 m overhang would be a 0.30 m coplanar overlap on the runoff platform, so
# the strip is faded out with the convergence.  One number, `free_in`, gates both edges.

def _access_path(t):
    """Route point at t metres from the glass plane.  -> (x, y, heading).  = contract."""
    return C.access_route_point(t)


def _saw_owner_gate(X1, Y1, H1, v, ds):
    """1 where the surface just outboard of ribbon lateral `v` is architecture's paving.

    The sawn edge strip exists so that THIS mesh's boundary is the line
    build_architecture cuts its slabs to.  Laying it where the neighbour is NOT
    architecture would just overlap somebody else — specifically `build_barriers`'
    runoff platform, which butts `verge_edge` and is not cut to the ribbon.  So the
    gate is a direct question to the contract: who owns the ground 150 mm beyond this
    edge?  Smoothed over 3 m of route so the strip does not switch on and off per row.
    """
    px = X1 - np.sin(H1) * (v + np.sign(v) * 0.15)
    py = Y1 + np.cos(H1) * (v + np.sign(v) * 0.15)
    _z, own = C.world_ground_z(px, py)
    g = np.array([1.0 if str(o) == C.OWNER_APRON else 0.0 for o in own])
    # DILATE FIRST, THEN SMOOTH.  A plain mean filter rounds the shoulders, so the strip
    # came out 0.273 m where architecture was still cutting at 0.300 — a 27 mm gap, i.e.
    # the same class of defect one row further out.  Dilating by more than the smoothing
    # radius makes the strip provably FULL WIDTH wherever the neighbour is architecture,
    # and lets it taper only over ground nobody cuts to it.
    rd = max(int(round(2.0 / ds)), 1)
    rs = max(int(round(1.5 / ds)), 1)
    pad = np.concatenate([np.full(rd, g[0]), g, np.full(rd, g[-1])])
    dil = np.max(np.stack([pad[i:i + len(g)] for i in range(2 * rd + 1)]), axis=0)
    k = np.ones(2 * rs + 1) / (2 * rs + 1)
    out = np.convolve(np.concatenate([np.full(rs, dil[0]), dil, np.full(rs, dil[-1])]),
                      k, mode="same")[rs:-rs]
    return np.clip(out, 0.0, 1.0)


def _access_layout(ds=0.30, nc=45):
    """Rows, columns and per-row edge data for the ribbon.  Pure contract arithmetic.

    THE CAPS COME FROM THE CONTRACT, NOT FROM HERE.  `T` runs from
    `C.ACCESS_RIBBON_T_MIN` (0.0 — the breach plane, pinned in contract 1.0.1 so no
    margin can walk it back through the glass wall) to `ACCESS_TOTAL + saw`, which is
    the only cap `in_access_ribbon` still widens.  Building the start cap anywhere else
    is what left a 0.300 m x 12.75 m fully-open slot in the Beat 3 -> Beat 4 hinge.
    """
    t0, t1 = RIBBON_T_MIN, C.ACCESS_TOTAL + RIBBON_CAP_END_M
    n = int(math.ceil((t1 - t0) / ds))
    T1 = np.linspace(t0, t1, n + 1)
    X1, Y1, H1 = C.access_route_arrays(T1)
    vin1, vout1 = C.access_edges(T1)

    # How much room is there between the ribbon's declared inboard edge and the racing
    # surface's own outer edge?  > 0 => free, butting architecture's paving.
    # == 0 => the ribbon is riding SURF_Track's painted verge and owns nothing inboard.
    Sc, Uc = C.project(X1, Y1)
    free_in = vin1 - (C.verge_edge(Sc) - Uc)
    # TWO EDGES, TWO GATES.  The first version gated BOTH saw strips on `free_in`, which
    # is a property of the INBOARD edge only, so the outboard strip vanished for the last
    # 150 m of the ribbon while build_architecture went on cutting its apron slabs
    # 0.30 m clear of the declared edge — an unbuilt strip along the outboard edge over
    # the stations the two share.  The inboard strip must fade (past t = 95.3 there is
    # no slab to butt: the ribbon is riding SURF_Track's own painted verge and 0.30 m
    # of overhang would lie ON the racing surface).  The outboard one must not.
    saw_in = ACCESS_SAW_M * C.smoothstep(0.05, 0.35, free_in)
    saw_out = ACCESS_SAW_M * _saw_owner_gate(X1, Y1, H1, vout1, float(T1[1] - T1[0]))

    lo = vin1 - saw_in
    hi = np.maximum(vout1 + saw_out, lo + 0.02)         # the gore closes to a nose

    # THE CLIP HAS TO BE MADE IN WORLD TERMS, NOT IN ROUTE TERMS.
    # `C.access_edges` clips the inboard edge with `E - U` evaluated at the ROUTE
    # CENTRELINE, and this mesh then offsets from that centreline along the ROUTE
    # NORMAL.  Over the R150 merge arc the route heading and the track heading differ
    # by up to 11.2 deg, so an edge that is exactly `verge_edge` in route coordinates
    # lands `v * (1 - cos dtheta)` INSIDE it in world coordinates.  Measured on the
    # built mesh: 126 vertices up to 49.99 mm inboard of `C.verge_edge`, around
    # s = 3430, t = 125 — the ribbon lying ON the racing surface, at exactly the same
    # `ground_z`, i.e. a zero-separation coplanar pair ~1.9 m2 in area, in the middle
    # of the Beat-4 merge.  Three fixed-point passes against `C.project` push the edge
    # back out; it converges to microns because the correction is second order.
    for _ in range(3):
        px_ = X1 - np.sin(H1) * lo
        py_ = Y1 + np.cos(H1) * lo
        se_, ue_ = C.project(px_, py_)
        over = C.verge_edge(se_) - np.abs(ue_)          # > 0 => on the racing surface
        lo = lo + np.maximum(over, 0.0)
    lo = np.minimum(lo, hi - 0.02)
    hi = np.maximum(hi, lo + 0.02)
    f = np.linspace(0.0, 1.0, nc)[None, :]
    V = lo[:, None] + (hi - lo)[:, None] * f
    return dict(T=T1, X=X1, Y=Y1, H=H1, vin=vin1, vout=vout1,
                saw=saw_in, saw_in=saw_in, saw_out=saw_out,
                free_in=free_in, lo=lo, hi=hi, V=V, n=n, nc=nc)


def _build_access(coll, mat):
    L = _access_layout()
    T1, X1, Y1, H1, V = L["T"], L["X"], L["Y"], L["H"], L["V"]
    n, nc = L["n"], L["nc"]

    PX = X1[:, None] - np.sin(H1)[:, None] * V
    PY = Y1[:, None] + np.cos(H1)[:, None] * V
    S, U = C.project(PX.ravel(), PY.ravel())
    Z = C.ground_z(S, U).reshape(V.shape)           # THE DATUM.  Nothing else.

    co = np.stack([PX, PY, Z], axis=-1).reshape(-1, 3)
    idx = np.arange((n + 1) * nc).reshape(n + 1, nc)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
    me = _new_mesh(PFX + "AccessRoad", co, quads)

    def lv(a):
        return np.stack([a[:-1, :-1], a[1:, :-1], a[1:, 1:], a[:-1, 1:]],
                        axis=-1).reshape(-1, 4).ravel()

    Tg = np.repeat(T1[:, None], nc, axis=1)
    _add_uv(me, "uv_su", np.stack([lv(V), lv(Tg)], axis=-1))
    # Distance from each edge, so the markings can be painted relative to a boundary
    # that MOVES.  The pit-exit lane's outer white line is 100 mm in from the slab edge
    # for its whole length, and the slab edge is a converging curve.
    din = V - L["vin"][:, None]
    dout = L["vout"][:, None] - V
    _add_uv(me, "uv_edge", np.stack([lv(din), lv(dout)], axis=-1))

    wid = np.repeat((L["vout"] - L["vin"])[:, None], nc, axis=1)
    fre = np.repeat(np.clip(L["free_in"] / 0.35, 0.0, 1.0)[:, None], nc, axis=1)
    onp = np.repeat((T1 / max(C.ACCESS_TOTAL, 1e-9))[:, None], nc, axis=1)
    _add_col(me, "rib", np.stack([wid / 16.0, fre, onp, np.zeros_like(wid)],
                                 axis=-1).reshape(-1, 4))

    ob = _obj(PFX + "AccessRoad", me, coll, mat)
    ob["contract_ribbon_polygon_margin_m"] = ACCESS_SAW_M
    ob["contract_ribbon_t_min_m"] = RIBBON_T_MIN
    ob["contract_ribbon_cap_end_m"] = RIBBON_CAP_END_M
    ob["route_t_range_m"] = [float(T1[0]), float(T1[-1])]
    return ob, quads.shape[0]


# ============================================================================
# 17b. THE TRACK / APRON-PLATFORM JOINT  —  the lap, stated once
# ============================================================================
#
# ASSEMBLY DEFECT: "a 12 mm open joint, 300 mm deep, along the whole pit-exit apron
# edge".  SURF_Track's outer edge ends at u = 10.500 = C.verge_edge(s).
# ARCH_Paving_ApronPlatform lays a regular 2.4 x 3.0 m bay grid whose first column
# starts at `verge_edge.min()` and then insets every bay 12 mm, so its first bay begins
# at u = 10.512 and its own clearance test (`d_in = u - verge_edge`) never fires.
# Between the two the ray falls 0.300 m to the sub-base.  Verified at s = 3247 / 3305 /
# 3361, over the whole 220 m of the pit-exit apron, at a 12.47 deg sun.
#
# TWO SURFACES CANNOT BOTH STOP AT A SHARED COORDINATE AND HOPE.  `verge_edge` is where
# this module's road ENDS; it cannot also be where the neighbour's slab begins unless
# one of them laps the other, and a lap has to be somebody's declared geometry with a
# number attached.  build_surface laps, because it is the module that owns the datum the
# joint is cut in and because an asphalt-to-concrete joint is physically a feature of the
# ASPHALT side: a formed groove, sealed with bitumen, 5 mm proud-of-nothing and never a
# void.
#
# `SURF_ApronJoint` runs from u = verge_edge (EXACTLY SURF_Track's outer edge, same row
# stations, same `C.ground_z`, so the butt is 0.000 mm by construction) out to
# u = verge_edge + APRON_JOINT_LAP_M, with a 5 mm sealant invert and a 1.6 mm lap that
# tucks under whatever the neighbour lays.  Three outcomes, all correct:
#
#   neighbour starts at 10.512 (today)  -> a 12 mm wide, 5 mm deep sealed joint groove,
#                                          not a 12 mm wide, 300 mm deep slot
#   neighbour adopts the lap (10.550)   -> the whole 50 mm groove is the joint, lit
#   neighbour butts at 10.500           -> the strip is entirely under the slab, 1.6 mm
#                                          below it, and there is nothing to see
#
# Applied ONLY where `C.apron_zone(s, +1) > 0.5` — the same predicate
# build_architecture uses to decide the apron platform exists at all
# (`build_apron_platform`: `keep = WC.apron_zone(S, +1) > 0.5`).  Everywhere else the
# outboard neighbour is `build_barriers`' runoff platform, which butts `verge_edge` with
# no inset and needs no lap; lapping it would be 3 675 m x 2 of new coplanar overlap.

def _apron_joint_cols():
    """(offset outboard of verge_edge, dz) across the joint."""
    L = APRON_JOINT_LAP_M
    d = APRON_JOINT_DEPTH_M
    return [(0.00 * L, 0.0000),        # == SURF_Track's outer edge, exactly
            (0.16 * L, -d),            # sealant invert
            (0.44 * L, -d),
            (0.64 * L, -0.32 * d),
            (1.00 * L, -0.32 * d)]     # the lap


def _build_apron_joint(coll, mat):
    S1 = _row_stations()
    keep = C.apron_zone(S1, +1) > 0.5
    # ... AND NOT WHERE THE RIBBON IS THE NEIGHBOUR.  The apron platform and the Beat-4
    # ribbon both reach `verge_edge` on the left of the pit straight, and they overlap
    # over s 3402..3429.  There the track's neighbour is `SURF_AccessRoad`, which butts
    # `verge_edge` exactly on the same `C.ground_z` and needs no joint at all — laying
    # one would put this module's own two meshes 1.6 mm apart over 1.35 m2.  Found by
    # the BVH self-census, not by reading the code.
    mid = C.su_to_world(S1, C.verge_edge(S1) + APRON_JOINT_LAP_M * 0.5)
    keep &= ~C.in_access_ribbon(mid[:, 0], mid[:, 1], margin=ACCESS_SAW_M)
    if not keep.any():
        return None, 0, 0.0
    idx = np.where(keep)[0]
    runs = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)
    prof = _apron_joint_cols()
    nc = len(prof)
    off = np.array([p[0] for p in prof])[None, :]
    dzc = np.array([p[1] for p in prof])[None, :]
    co_all, q_all, uv_all, base = [], [], [], 0
    length = 0.0
    for run in runs:
        if len(run) < 2:
            continue
        Sr = S1[run]
        n = len(Sr)
        S = np.repeat(Sr[:, None], nc, axis=1)
        U = C.verge_edge(S) + off
        Z = C.ground_z(S, U) + dzc
        X, Y, H, _ = _centreline_arrays(S.ravel())
        X = X.reshape(S.shape); Y = Y.reshape(S.shape); H = H.reshape(S.shape)
        co = np.stack([X - np.sin(H) * U, Y + np.cos(H) * U, Z], axis=-1).reshape(-1, 3)
        i = base + np.arange(n * nc).reshape(n, nc)
        q = np.stack([i[:-1, :-1], i[1:, :-1], i[1:, 1:], i[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
        A = np.repeat(off, n, axis=0)          # metres across the joint

        def lv(a):
            return np.stack([a[:-1, :-1], a[1:, :-1], a[1:, 1:], a[:-1, 1:]],
                            axis=-1).reshape(-1, 4).ravel()
        uv_all.append(np.stack([lv(A), lv(S)], axis=-1))
        co_all.append(co); q_all.append(q)
        base += n * nc
        length += float(Sr[-1] - Sr[0])
    if not co_all:
        return None, 0, 0.0
    co = np.concatenate(co_all, axis=0)
    quads = np.concatenate(q_all, axis=0)
    me = _new_mesh(PFX + "ApronJoint", co, quads, smooth=False)
    _add_uv(me, "uv_su", np.concatenate(uv_all, axis=0))
    ob = _obj(PFX + "ApronJoint", me, coll, mat)
    ob["contract_apron_joint_lap_m"] = APRON_JOINT_LAP_M
    ob["contract_apron_joint_depth_m"] = APRON_JOINT_DEPTH_M
    ob["contract_predicate"] = "C.apron_zone(s, +1) > 0.5"
    return ob, quads.shape[0], length


# ============================================================================
# 18. SHADER DSL
# ============================================================================
class _G:
    def __init__(self, nt):
        self.nt = nt
        self.x = -2600.0
        self.y = 0.0

    def n(self, kind, **props):
        nd = self.nt.nodes.new(kind)
        nd.location = (self.x, self.y)
        self.x += 190
        if self.x > 600:
            self.x = -2600.0
            self.y -= 260
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def set(self, sock, v):
        if v is None:
            return
        if hasattr(v, "is_output"):
            self.nt.links.new(v, sock)
        else:
            sock.default_value = v

    def sin(self, node, name, typ=None):
        for s in node.inputs:
            if s.name == name and (typ is None or s.type == typ):
                return s
        raise KeyError(name)

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.set(nd.inputs[0], a)
        if b is not None:
            self.set(nd.inputs[1], b)
        if c is not None:
            self.set(nd.inputs[2], c)
        return nd.outputs[0]

    def mr(self, v, f0, f1, t0=0.0, t1=1.0, clamp=True, interp="LINEAR"):
        nd = self.n("ShaderNodeMapRange", clamp=clamp, interpolation_type=interp)
        self.set(nd.inputs["Value"], v)
        self.set(nd.inputs["From Min"], f0); self.set(nd.inputs["From Max"], f1)
        self.set(nd.inputs["To Min"], t0); self.set(nd.inputs["To Max"], t1)
        return nd.outputs[0]

    def mixc(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type="MIX")
        self.set(self.sin(nd, "Factor", "VALUE"), fac)
        self.set(self.sin(nd, "A", "RGBA"), a)
        self.set(self.sin(nd, "B", "RGBA"), b)
        return nd.outputs["Result"]

    def vmulc(self, a, b):
        """Component-wise colour multiply — used to apply a contrast field to a base
        colour without moving its mean, which mixing toward an absolute colour cannot
        do."""
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
        self.set(self.sin(nd, "Factor", "VALUE"), 1.0)
        self.set(self.sin(nd, "A", "RGBA"), a)
        self.set(self.sin(nd, "B", "RGBA"), b)
        return nd.outputs["Result"]

    def grey(self, v):
        """Scalar -> neutral colour."""
        nd = self.n("ShaderNodeCombineColor")
        for i in range(3):
            self.set(nd.inputs[i], v)
        return nd.outputs[0]

    def mixf(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.set(self.sin(nd, "Factor", "VALUE"), fac)
        self.set(self.sin(nd, "A", "VALUE"), a)
        self.set(self.sin(nd, "B", "VALUE"), b)
        return nd.outputs["Result"]

    def rgb(self, r, g, b):
        nd = self.n("ShaderNodeRGB")
        nd.outputs[0].default_value = (r, g, b, 1.0)
        return nd.outputs[0]

    def comb(self, x, y, z=0.0):
        nd = self.n("ShaderNodeCombineXYZ")
        self.set(nd.inputs[0], x); self.set(nd.inputs[1], y); self.set(nd.inputs[2], z)
        return nd.outputs[0]

    def sep(self, v):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.set(nd.inputs[0], v)
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def noise(self, vec, scale, detail=6.0, rough=0.5, dist=0.0, dim="3D"):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dim)
        if dim == "1D":
            self.set(nd.inputs["W"], vec)
        else:
            self.set(nd.inputs["Vector"], vec)
        self.set(nd.inputs["Scale"], scale)
        self.set(nd.inputs["Detail"], detail)
        self.set(nd.inputs["Roughness"], rough)
        self.set(nd.inputs["Distortion"], dist)
        return nd.outputs["Fac"], nd.outputs["Color"]

    def voro(self, vec, scale, feature="F1", rand=1.0, smooth=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature, voronoi_dimensions="3D")
        self.set(nd.inputs["Vector"], vec)
        self.set(nd.inputs["Scale"], scale)
        self.set(nd.inputs["Randomness"], rand)
        if "Smoothness" in nd.inputs:
            self.set(nd.inputs["Smoothness"], smooth)
        return nd

    def wnoise(self, vec):
        nd = self.n("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
        self.set(nd.inputs["Vector"], vec)
        return nd.outputs["Value"], nd.outputs["Color"]

    def scale(self, vec, f):
        nd = self.n("ShaderNodeVectorMath", operation="SCALE")
        self.set(nd.inputs[0], vec)
        self.set(nd.inputs["Scale"], f)
        return nd.outputs["Vector"]

    def vmul(self, vec, v3):
        nd = self.n("ShaderNodeVectorMath", operation="MULTIPLY")
        self.set(nd.inputs[0], vec)
        nd.inputs[1].default_value = v3
        return nd.outputs["Vector"]

    def vadd(self, a, b):
        nd = self.n("ShaderNodeVectorMath", operation="ADD")
        self.set(nd.inputs[0], a); self.set(nd.inputs[1], b)
        return nd.outputs["Vector"]

    def bump(self, height, strength=1.0, distance=1.0, normal=None):
        nd = self.n("ShaderNodeBump")
        self.set(nd.inputs["Strength"], strength)
        self.set(nd.inputs["Distance"], distance)
        self.set(nd.inputs["Height"], height)
        if normal is not None:
            self.set(nd.inputs["Normal"], normal)
        return nd.outputs["Normal"]

    def band(self, v, a, b, soft=0.012):
        """1 inside [a,b], 0 outside, with `soft` metres of anti-aliasing."""
        lo = self.mr(v, a - soft, a + soft, 0.0, 1.0)
        hi = self.mr(v, b - soft, b + soft, 1.0, 0.0)
        return self.math("MULTIPLY", lo, hi)

    def sband(self, v, a, b, soft=0.012):
        """`band` where the limits may themselves be sockets."""
        lo = self.mr(self.math("SUBTRACT", v, a), -soft, soft, 0.0, 1.0)
        hi = self.mr(self.math("SUBTRACT", v, b), -soft, soft, 1.0, 0.0)
        return self.math("MULTIPLY", lo, hi)

    def tag(self, name, sock):
        """Label the node a socket comes from so a debug pass can find and view it.

        Every intermediate layer of the asphalt is tagged.  This is not decoration:
        the only way to answer "why is the racing line not reading" is to put the
        mask on screen by itself, and without labels there is no handle on a graph
        of 400 anonymous nodes.  ``--debug-layers`` renders one plan view per tag.
        """
        try:
            sock.node.label = "DBG:" + name
        except Exception:
            pass
        return sock


# ============================================================================
# 19. ASPHALT MATERIAL
# ============================================================================
def _mat_asphalt():
    mat = bpy.data.materials.new(MPFX + "Asphalt")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = _G(nt)

    uv0 = g.n("ShaderNodeUVMap"); uv0.uv_map = "uv_su"
    uv1 = g.n("ShaderNodeUVMap"); uv1.uv_map = "uv_rl"
    u, s, _ = g.sep(uv0.outputs["UV"])
    d, _s2, _ = g.sep(uv1.outputs["UV"])
    trk = g.n("ShaderNodeAttribute"); trk.attribute_name = "trk"
    geo = g.n("ShaderNodeAttribute"); geo.attribute_name = "geo"
    tr_r, tr_g, tr_b = g.sep(trk.outputs["Color"])
    ge_r, ge_g, ge_b = g.sep(geo.outputs["Color"])
    rubber, spread, brake = tr_r, g.math("MULTIPLY", tr_g, 8.0), tr_b
    polish = trk.outputs["Alpha"]
    Wh = g.math("MULTIPLY", ge_r, 16.0)
    kerb_here, bandv, age = ge_g, g.math("MULTIPLY", ge_b, 2.0), geo.outputs["Alpha"]

    au = g.math("ABSOLUTE", u)
    # the band wanders: a season of cars does not put the line in exactly the same
    # place twice, and a perfectly symmetric stripe is the giveaway of a painted-on
    # racing line.
    wob_f, _ = g.noise(g.math("MULTIPLY", s, 0.011), 1.0, detail=3.0, dim="1D")
    d = g.math("SUBTRACT", d, g.mr(wob_f, 0.0, 1.0, -0.75, 0.75))
    ad = g.math("ABSOLUTE", d)
    edge = g.math("SUBTRACT", Wh, au)          # +ve inside the racing surface
    on_track = g.mr(edge, -0.02, 0.02, 0.0, 1.0)

    P = g.n("ShaderNodeTexCoord").outputs["Object"]

    # ---- FIVE detail scales, all evaluated in 3-D world space -------------------
    # Sizes are set against what a pixel is worth at the two closest camera stations:
    # the doppler hover is 26 m out on a 50 mm lens (4.9 mm/px at 4K) and the T4
    # kerb-height camera is ~5 m out on a 21 mm (2.2 mm/px).  A 14 mm chip is 3 px at
    # the first and 6 px at the second, so the aggregate has to BE 14 mm — the first
    # pass used 80 mm cells and read as smooth tarmac in a macro crop.
    macro2_f, _ = g.noise(g.scale(P, 0.0072), 1.0, detail=3.0, rough=0.55)   # 140 m
    macro_f, _ = g.noise(g.scale(P, 0.030), 1.0, detail=5.0, rough=0.62)     # 33 m
    pour = g.voro(g.scale(P, 0.105), 1.0, "F1", 0.92)                        # 9.5 m
    mott_f, _ = g.noise(g.scale(P, 1.55), 1.0, detail=6.0, rough=0.60)       # 0.65 m
    # a real asphalt is a GRADED aggregate - 14 mm down through 8 mm to fines - so
    # one voronoi scale reads as a quilt.  Three scales, each on a coordinate warped
    # by the one below it, breaks the lattice completely.
    # THE WARP MUST BE SMALLER THAN THE CELL IT WARPS.  A +-15 mm displacement on an
    # 18 mm aggregate cell does not break the lattice, it DESTROYS the cell: every
    # stone is smeared into its neighbours and the 18 mm layer degenerates into
    # high-frequency noise.  Measured on the plan probe, the surface read as sandpaper
    # at 3.1 mm/px — grain everywhere, not one stone the eye could resolve as a stone.
    # 6.5 mm distorts the cell outlines, which is what a crushed aggregate looks like,
    # and leaves them cells.
    _warp_f, warp_c = g.noise(g.scale(P, 24.0), 1.0, detail=3.0)
    Pw = g.vadd(P, g.scale(g.vadd(warp_c, (-0.5, -0.5, -0.5)), 0.0065))
    agg0 = g.voro(g.scale(P, 33.0), 1.0, "SMOOTH_F1", 1.0, 0.14)             # 30 mm
    agg = g.voro(g.scale(Pw, 56.0), 1.0, "SMOOTH_F1", 1.0, 0.10)             # 18 mm
    aggb = g.voro(g.scale(P, 112.0), 1.0, "SMOOTH_F1", 1.0, 0.22)            # 9 mm
    agg2 = g.voro(g.scale(Pw, 235.0), 1.0, "F1", 1.0)                        # 4 mm
    # A SMOOTH_F1 Color output is a BLEND of the neighbouring cell colours, so using it
    # as a per-stone hash gives every stone a tone that fades into the next one — which
    # is precisely how three discrete lithologies average back to one grey.  This hard
    # F1 twin shares the warped coordinate and the scale, so its cells ARE the smooth
    # layer's cells, and its Color is constant across each of them.
    agg_id = g.voro(g.scale(Pw, 56.0), 1.0, "F1", 1.0)                       # ids only
    grain_f, _ = g.noise(g.scale(P, 430.0), 1.0, detail=3.0, rough=0.55)     # 2.3 mm
    micro_f, _ = g.noise(g.scale(P, 1600.0), 1.0, detail=2.0, rough=0.5)     # 0.6 mm
    # Streaks must run ALONG the road.  Scaling object space by (0.1, 0.1, 1) is
    # isotropic in plan and produces blobs, which is why the first helicopter frame
    # came back looking like camouflage.  The metric UV gives the direction for free:
    # 0.31 m across by 18 m along, plus a finer tyre-width layer.
    streak_f, _ = g.noise(g.comb(g.math("MULTIPLY", u, 3.2),
                                 g.math("MULTIPLY", s, 0.055), 0.0),
                          1.0, detail=4.0, rough=0.55)
    streak2_f, _ = g.noise(g.comb(g.math("MULTIPLY", u, 11.0),
                                  g.math("MULTIPLY", s, 0.30), 0.0),
                           1.0, detail=3.0, rough=0.5)

    # -- resurfacing zones: age from the baked attribute, tint from the macro noise --
    # 0.42 of age swing here made the helicopter frame read as camouflage: at 33 m
    # the noise is exactly the scale of the road's own width.  0.16 keeps the zones
    # distinguishable without cloud.
    age_v = g.math("ADD", age, g.math("MULTIPLY", g.math("SUBTRACT", macro_f, 0.5), 0.16),
                   clamp=True)
    # THE REFLECTANCE LADDER — and the reason the assembly frame came back "a flat grey
    # gradient with no aggregate".
    #
    # The previous pass drove the base down to 0.032 (fresh) / 0.076 (old) because a
    # plan-view render measured 0.083 and that read as light concrete NEXT TO A RUBBERED
    # LINE THAT WAS NOT DARK ENOUGH.  The fix was applied to the wrong end of the ladder.
    # Two things follow from `C.REFERENCE_EXPOSURE_EXTERIOR` = -3.048 and AgX:
    #
    #   * mid grey is albedo 0.18.  A 0.032 surface sits 2.49 stops below it, which is
    #     the part of AgX where the tone curve's slope is lowest — so the +-0.5
    #     multiplicative chip contrast this material generates arrives on screen
    #     compressed to a fraction of a stop.  The aggregate was BUILT and then TONE
    #     MAPPED OUT.  At 0.10 the same contrast lands 1.15 stops below mid grey, on the
    #     straight part of the curve, and survives.
    #   * what makes a racing line read is the RATIO, not the absolute.  Old bleached
    #     dense-graded asphalt measures 0.10-0.13 albedo, fresh 0.045-0.055, and a
    #     rubbered-in line 0.028-0.035.  So the ladder below is the real one and the
    #     rubber layer is retuned to land on the bottom of it (3.3 : 1 against the old
    #     zones, 1.5 : 1 against the freshest) instead of collapsing to 0.012.
    #
    # Binder is warm-neutral, not grey: a neutral base under a 12.5 deg sun is lit almost
    # entirely by the blue sky dome and renders visibly blue, which is the single most
    # common tell of CG tarmac.
    col_fresh = g.rgb(0.0600, 0.0559, 0.0507)
    col_old = g.rgb(0.1360, 0.1281, 0.1147)
    base = g.mixc(age_v, col_fresh, col_old)
    # broad pour-to-pour tint drift (the mixer truck was not the same every load)
    base = g.mixc(g.mr(macro2_f, 0.25, 0.75, 0.0, 0.45), base,
                  g.mixc(0.5, base, g.rgb(0.0815, 0.0775, 0.0700)))
    # PAVER MATS.  A 9.5 m Voronoi CELL ID, not its distance field: each mixer load
    # went down at its own temperature and compacted to its own tone, and the boundary
    # between two loads is a line, not a gradient.  This is the one layer that is
    # allowed to be strong at the 10 m scale - the equivalent smooth-noise version is
    # what made the first helicopter frame read as camouflage, because fractal noise at
    # the road's own width is a cloud and a cell is a paving mat.
    pour_id = g.sep(pour.outputs["Color"])[2]
    base = g.vmulc(base, g.grey(g.mr(pour_id, 0.0, 1.0, 0.865, 1.135)))
    base = g.mixc(g.math("MULTIPLY", g.mr(pour.outputs["Distance"], 0.0, 0.10, 1.0, 0.0),
                         0.35),
                  base, g.rgb(0.0492, 0.0474, 0.0447))

    # -- mid-scale segregation: every paver leaves patches that are chip-rich or
    #    binder-rich at roughly half a metre.  Without it the surface is featureless
    #    between the 10 m pour cells and the 15 mm chips, which is the scale a
    #    2.4 m-high lens 26 m away lands on.
    segreg = g.mr(mott_f, 0.28, 0.78, 0.0, 1.0)
    base = g.mixc(g.math("MULTIPLY", segreg, 0.22), base, g.rgb(0.0605, 0.0585, 0.0545))

    # -- aggregate, as a MULTIPLICATIVE contrast field ------------------------------
    # Chip tops catch the light, binder crevices swallow it, and the mean stays on the
    # zone colour.  Mixing toward an absolute chip colour (the first version) cannot do
    # that: it drags a 0.030 fresh zone and a 0.077 old zone to the same place, which
    # also destroyed the resurfacing zones the anti-tiling depends on.
    agg_d = agg.outputs["Distance"]
    # A graded aggregate is graded: a few 30 mm faces, a lot of 18 mm, 9 mm filling
    # between them and 4 mm fines in the mortar.  Weighting them equally (the first
    # version) reads as sandpaper because the eye never finds a stone big enough to
    # recognise as one - the biggest layer has to dominate.
    # A CRUSHED STONE IS FLAT-TOPPED AND HAS MORTAR ROUND IT.  The first window,
    # 0.05..0.46, called almost the whole cell a chip top, so the field had no mortar
    # anywhere and the surface rendered as a dense even stipple — embossed rubber, not
    # graded aggregate (measured on the plan probe at 3.1 mm/px).  Narrowing the window
    # gives each stone a saturated flat face and leaves binder-rich mortar between them,
    # which is what the eye reads as "stones IN something" rather than "bumps".
    chip_hi = g.math("MAXIMUM",
                     g.math("MULTIPLY", g.mr(agg_d, 0.03, 0.33, 1.0, 0.0), 1.15),
                     g.math("MULTIPLY",
                            g.mr(aggb.outputs["Distance"], 0.04, 0.25, 1.0, 0.0), 0.30))
    chip_hi = g.math("MAXIMUM", chip_hi,
                     g.math("MULTIPLY",
                            g.mr(agg0.outputs["Distance"], 0.03, 0.26, 1.0, 0.0),
                            g.mr(g.sep(agg0.outputs["Color"])[0], 0.56, 0.76, 0.0, 1.45)))
    chip_hi = g.math("MULTIPLY", chip_hi, g.mr(segreg, 0.0, 1.0, 0.40, 1.0))
    # polished stone under the driven line reflects instead of scattering
    chip_hi = g.math("MULTIPLY", chip_hi,
                     g.math("SUBTRACT", 1.0, g.math("MULTIPLY", polish, 0.40)))
    chip_lo = g.mr(agg_d, 0.30, 0.62, 0.0, 1.0)              # binder between the chips
    fine_hi = g.mr(agg2.outputs["Distance"], 0.0, 0.30, 1.0, 0.0)   # 4 mm secondary stone
    grain_c = g.mr(grain_f, 0.18, 0.82, -1.0, 1.0)
    g.tag("chip_hi", chip_hi)
    # PLUCK-OUTS.  A dense-graded surfacing loses individual stones — a 20-60 mm socket
    # with a dark, rough floor and a bright fractured rim.  They are the single most
    # recognisable "this is a used road surface" cue at the macro station and they are
    # what a uniform voronoi field can never produce, because a voronoi has no holes.
    pluck_v = g.voro(g.scale(Pw, 21.0), 1.0, "F1", 1.0)
    pluck_id = g.sep(pluck_v.outputs["Color"])[2]
    pluck = g.math("MULTIPLY", g.mr(pluck_id, 0.955, 0.972, 0.0, 1.0),
                   g.mr(pluck_v.outputs["Distance"], 0.030, 0.012, 0.0, 1.0))
    pluck = g.math("MULTIPLY", pluck, g.mr(age, 0.15, 0.85, 0.35, 1.0))
    g.tag("pluck", pluck)
    # WEIGHTS.  The chip term carried 1.35 against a 0.032 base, i.e. it was generating
    # +-0.20 stops of contrast on the part of AgX with the least slope.  The base is now
    # on the straight part of the curve, so the same layer reads; the coefficients are
    # raised anyway because the assembly frame's complaint was "no aggregate", and the
    # binder term is raised harder than the chip term so the surface darkens BETWEEN the
    # stones rather than blowing the stones out.
    lum = g.math("ADD", 1.0, g.math("MULTIPLY", chip_hi, 1.58))
    lum = g.math("SUBTRACT", lum, g.math("MULTIPLY", chip_lo, 0.68))
    lum = g.math("ADD", lum, g.math("MULTIPLY", fine_hi, 0.15))
    lum = g.math("ADD", lum, g.math("MULTIPLY", grain_c, 0.09))
    lum = g.math("SUBTRACT", lum, g.math("MULTIPLY", pluck, 0.55))
    lum = g.math("MAXIMUM", lum, 0.15)
    # THREE LITHOLOGIES, NOT A HUE RAMP.  A quarry delivers one rock; a circuit that has
    # been resurfaced nine times has several, and a single load is itself a mix.  A
    # continuous hue ramp across the cells (the previous version) averages to grey at any
    # distance where a cell is under a pixel, which is exactly the doppler station.
    # Three DISCRETE stone colours selected by a per-cell hash keep their identity when
    # they average, because the average of three separated colours is not one of them:
    # pale quartzite/limestone, mid granodiorite, dark basalt.
    cell_h = g.sep(agg_id.outputs["Color"])[1]
    lith_a = g.mr(cell_h, 0.34, 0.36, 0.0, 1.0)              # pale -> mid
    lith_b = g.mr(cell_h, 0.70, 0.72, 0.0, 1.0)              # mid  -> dark
    chip_tint = g.mixc(lith_a, g.rgb(1.26, 1.22, 1.13), g.rgb(1.02, 1.00, 0.96))
    chip_tint = g.mixc(lith_b, chip_tint, g.rgb(0.70, 0.71, 0.77))
    # ... and the 9 mm layer gets its own, uncorrelated, draw
    cell_b = g.sep(agg_id.outputs["Color"])[0]
    tint_b = g.mixc(g.mr(cell_b, 0.52, 0.54, 0.0, 1.0),
                    g.rgb(1.18, 1.14, 1.06), g.rgb(0.86, 0.87, 0.90))
    chip_tint = g.mixc(0.34, chip_tint, tint_b)
    # a stone only shows its colour where it is actually exposed
    chip_tint = g.mixc(g.mr(chip_hi, 0.03, 0.42, 0.0, 1.0), g.rgb(1.0, 1.0, 1.0),
                       chip_tint)
    base = g.vmulc(base, g.vmulc(chip_tint, g.grey(lum)))
    # the pluck socket floor is fresh, unweathered binder: darker and browner
    base = g.mixc(g.math("MULTIPLY", pluck, 0.62), base, g.rgb(0.0212, 0.0196, 0.0184))

    # -- BINDER FLUSHING ("fatty" / bleeding patches) --------------------------------
    # Where the mat was laid rich or the traffic has kneaded it, bitumen rises and
    # drowns the stone.  The patch is DARKER and much SMOOTHER than the surface round
    # it, so it is nearly invisible in plan and blazes at a 12.47 deg sun — which is
    # exactly the condition every frame in this film is shot under.  It is also the
    # cheapest thing that stops 3 675 m of tarmac reading as one material.
    fat_f, _ = g.noise(g.scale(P, 0.34), 1.0, detail=4.0, rough=0.55)
    fat = g.mr(fat_f, 0.60, 0.79, 0.0, 1.0)
    fat = g.math("MULTIPLY", fat, g.mr(rubber, 0.35, 1.15, 0.25, 1.0))
    fat = g.math("MULTIPLY", fat, g.mr(edge, 0.4, 3.0, 0.15, 1.0))
    g.tag("flush", fat)
    base = g.vmulc(base, g.grey(g.mr(fat, 0.0, 1.0, 1.0, 0.66)))

    # -- longitudinal paving-lane joints; lane width and phase differ per zone --------
    lane_w = g.mr(age, 0.0, 1.0, 4.05, 4.85)
    lane_ph = g.math("MULTIPLY", age, 5.4)
    lane_t = g.math("DIVIDE", g.math("ADD", u, lane_ph), lane_w)
    lane_fr = g.math("SUBTRACT", g.math("FRACT", lane_t), 0.5)
    lane_d = g.math("MULTIPLY", g.math("ABSOLUTE", lane_fr), lane_w)
    lane_j = g.mr(lane_d, 0.008, 0.040, 1.0, 0.0)
    # the paver's own edge: the last 350 mm of a lane is worked by the screed's end
    # plate and finishes very slightly coarser and lighter than the middle of the mat.
    # This is what makes paving lanes read from 100 m up, where a 30 mm joint cannot.
    lane_shoulder = g.mr(lane_d, 0.40, 0.05, 0.0, 1.0)

    # -- transverse construction joints at the resurfacing boundaries ---------------
    tj = None
    for r in RESURFACE:
        dd = g.math("ABSOLUTE", g.math("SUBTRACT", s, r[0]))
        b = g.mr(dd, 0.012, 0.055, 1.0, 0.0)
        tj = b if tj is None else g.math("MAXIMUM", tj, b)
    # timing loops: a pair of saw cuts at the line and at both sector splits
    for st in (LAP - 0.35, LAP - 6.0, 1200.0, 2450.0):
        dd = g.math("ABSOLUTE", g.math("SUBTRACT", s, st))
        tj = g.math("MAXIMUM", tj, g.mr(dd, 0.010, 0.030, 1.0, 0.0))
    joints = g.math("MAXIMUM", lane_j, tj)
    base = g.vmulc(base, g.grey(g.math("ADD", 1.0,
                                       g.math("MULTIPLY", lane_shoulder, 0.16))))
    base = g.mixc(g.math("MULTIPLY", joints, 0.72), base, g.rgb(0.0308, 0.0294, 0.0294))

    # -- crack sealant "tar snakes", only where the asphalt is old -------------------
    # A crack-sealant snake is ONE sinuous line, so the field it is a level-set of
    # must be smooth.  detail 8 + distortion 1.9 made the 0.5 level-set a dense
    # fractal web, and because sealant also lowers roughness it glinted - the
    # helicopter frame came back looking like frost on the whole road.  Low detail,
    # mild distortion, and a low-frequency coverage mask so cracks appear in patches
    # rather than everywhere.
    snoise_f, snoise_c = g.noise(g.scale(P, 0.055), 1.0, detail=2.0, rough=0.40,
                                 dist=0.55)
    snake = g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", snoise_f, 0.5)),
                 0.005, 0.016, 1.0, 0.0)
    cover_f, _ = g.noise(g.scale(P, 0.021), 1.0, detail=3.0, rough=0.55)
    snake = g.math("MULTIPLY", snake, g.mr(cover_f, 0.52, 0.70, 0.0, 1.0))
    snake = g.math("MULTIPLY", snake, g.mr(age, 0.45, 0.90, 0.0, 1.0))
    snake = g.math("MULTIPLY", snake, g.mr(edge, 0.0, 2.5, 0.35, 1.0))
    base = g.mixc(g.math("MULTIPLY", snake, 0.9), base, g.rgb(0.0243, 0.0236, 0.0232))

    # -- repairs, in the two shapes a real circuit actually carries -------------------
    # (a) MILLED AREAS: irregular, where a whole area was planed out and re-laid.  The
    #     first version had only these, at a 0.02-wide id window on 16 m cells - about
    #     four on the entire 3 675 m lap, which is why the plan view came back as an
    #     unbroken ribbon.  Widened to roughly one per 250 m.
    patch_v = g.voro(g.scale(P, 0.075), 1.0, "F1", 0.85)
    pid = g.sep(patch_v.outputs["Color"])[2]
    milled = g.math("MULTIPLY", g.mr(pid, 0.858, 0.872, 0.0, 1.0),
                    g.mr(patch_v.outputs["Distance"], 0.42, 0.30, 0.0, 1.0))
    # (b) SAW-CUT PATCHES: a saw cuts straight lines, so these are rectangles in road
    #     space, not blobs.  A cell grid of 34 m x 4.4 m in (s, u) with a per-cell hash
    #     decides which cells carry one and how big and where inside the cell it sits;
    #     the result is ~25 per lap, none the same size, all axis-aligned to the road
    #     the way a saw and a paver actually work.
    cs = g.math("DIVIDE", s, 34.0)
    cu = g.math("DIVIDE", g.math("ADD", u, 40.0), 4.4)
    ci = g.math("FLOOR", cs); cj = g.math("FLOOR", cu)
    fs = g.math("FRACT", cs); fu = g.math("FRACT", cu)
    rv, rc = g.wnoise(g.comb(ci, cj, 5.0))
    r0, r1, r2 = g.sep(rc)
    has = g.mr(rv, 0.895, 0.905, 0.0, 1.0)
    a0 = g.mr(r0, 0.0, 1.0, 0.06, 0.34)
    a1 = g.math("ADD", a0, g.mr(r1, 0.0, 1.0, 0.30, 0.62))
    b0 = g.mr(r2, 0.0, 1.0, 0.05, 0.40)
    b1 = g.math("ADD", b0, g.mr(rv, 0.0, 1.0, 0.35, 0.55))
    rect = g.math("MULTIPLY", g.sband(fs, a0, a1, 0.0035), g.sband(fu, b0, b1, 0.0035))
    sawn = g.math("MULTIPLY", has, rect)
    # the saw kerf itself: a 25 mm bitumen-sealed line round the perimeter of the cut
    rect_in = g.math("MULTIPLY",
                     g.sband(fs, g.math("ADD", a0, 0.0009), g.math("SUBTRACT", a1, 0.0009),
                             0.0004),
                     g.sband(fu, g.math("ADD", b0, 0.006), g.math("SUBTRACT", b1, 0.006),
                             0.002))
    kerf = g.math("MULTIPLY", has, g.math("SUBTRACT", rect, rect_in, clamp=True))
    patch = g.math("MAXIMUM", milled, sawn)
    g.tag("patch", patch)
    # a repair is younger than what surrounds it, so it is DARKER, and how much darker
    # depends on how long ago it was done - the per-cell hash drives that too
    patch_col = g.mixc(g.mr(r1, 0.0, 1.0, 0.0, 1.0),
                       g.rgb(0.0386, 0.0368, 0.0347), g.rgb(0.0754, 0.0724, 0.0665))
    patch_col = g.vmulc(patch_col, g.grey(g.math("ADD", 0.72,
                                                 g.math("MULTIPLY", chip_hi, 0.9))))
    base = g.mixc(g.math("MULTIPLY", patch, 0.88), base, patch_col)
    base = g.mixc(g.math("MULTIPLY", kerf, 0.85), base, g.rgb(0.0221, 0.0212, 0.0206))

    # ================= paint ========================================================
    paint_a = None
    paint_col = g.rgb(0.62, 0.615, 0.60)

    def add_paint(mask, col=None):
        nonlocal paint_a, paint_col
        if paint_a is None:
            paint_a = mask
        else:
            paint_a = g.math("MAXIMUM", paint_a, mask)
        if col is not None:
            paint_col = g.mixc(mask, paint_col, col)

    # track-edge white line (100 mm, outer edge on the track limit)
    edge_line = g.band(edge, 0.02, 0.12, 0.006)
    add_paint(edge_line)
    # green verge outboard of a kerb; plain asphalt shoulder where there is none
    verge_m = g.math("MULTIPLY", g.mr(bandv, 0.72, 0.92, 0.0, 1.0), kerb_here)
    add_paint(g.math("MULTIPLY", verge_m, 0.92), g.rgb(0.030, 0.078, 0.031))
    # 100 mm white on the inboard lip of the verge
    vw = g.math("MULTIPLY",
                g.band(g.math("SUBTRACT", au, Wh), KERB_BAND + 0.00, KERB_BAND + 0.10,
                       0.006), kerb_here)
    add_paint(vw, g.rgb(0.60, 0.60, 0.585))

    # start/finish line: 400 mm across the full width
    sf = g.math("MAXIMUM", g.band(s, LAP - 0.40, LAP + 0.02, 0.008),
                g.band(s, -0.02, 0.02, 0.008))
    add_paint(g.math("MULTIPLY", sf, on_track))

    # grid boxes: 10 rows, staggered, 2.6 x 6.0 m, 100 mm outline + 300 mm front bar
    grid = None
    for i in range(20):
        row = i // 2
        side = 1.0 if (i % 2 == 0) else -1.0          # pole on the inside of T1 (left)
        s_front = LAP - 9.0 - row * 8.0 - (0.0 if i % 2 == 0 else 4.0)
        uc = side * 3.55
        inb = g.band(u, uc - 1.30, uc + 1.30, 0.006)
        ins = g.band(s, s_front - 6.0, s_front, 0.006)
        box = g.math("MULTIPLY", inb, ins)
        core = g.math("MULTIPLY", g.band(u, uc - 1.20, uc + 1.20, 0.006),
                      g.band(s, s_front - 5.90, s_front - 0.30, 0.006))
        outline = g.math("SUBTRACT", box, core, clamp=True)
        grid = outline if grid is None else g.math("MAXIMUM", grid, outline)
    add_paint(g.math("MULTIPLY", grid, on_track))

    # pit-exit blend line: solid white, from the merge, converging over 90 m
    s_m = LAP - 215.60
    tb = g.mr(s, s_m, s_m + 90.0, 0.0, 1.0)
    u_b = g.mr(tb, 0.0, 1.0, 8.0, 2.0)
    blend = g.math("MULTIPLY",
                   g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", u, u_b)),
                        0.06, 0.10, 1.0, 0.0),
                   g.band(s, s_m, s_m + 90.0, 0.2))
    add_paint(g.math("MULTIPLY", blend, on_track))

    # paint wear.  These lines are repainted for the meeting, so what takes them off is
    # tyres crossing them, not age: the wear has to be driven by distance from the
    # DRIVEN LINE.  The first version added 0.45 of 33 m macro noise, which deleted the
    # track-edge line for 40 m at a time - visible as a dashed white line in the plan
    # view, and a dashed line at a race circuit means something entirely different.
    wear = g.math("MULTIPLY", rubber, g.mr(ad, 0.6, 3.2, 1.0, 0.10))
    wear = g.math("ADD", wear, g.math("MULTIPLY", g.mr(grain_f, 0.35, 0.78, 0.0, 1.0), 0.34))
    wear = g.math("ADD", wear, g.math("MULTIPLY",
                                      g.mr(macro_f, 0.42, 0.86, 0.0, 1.0), 0.18))
    # a fresh coat over an old one: the paint gang goes round before the event, so the
    # line survives even where it is scrubbed, it just goes grey and thin
    paint_a = g.math("MULTIPLY", paint_a,
                     g.mr(wear, 0.50, 1.25, 1.0, 0.42))
    # chipped paint reveals the aggregate underneath
    paint_a = g.math("MULTIPLY", paint_a,
                     g.mr(agg2.outputs["Distance"], 0.03, 0.13, 0.62, 1.0))
    # ... and where it IS scrubbed it greys off rather than vanishing
    paint_col = g.mixc(g.mr(wear, 0.55, 1.25, 0.0, 0.62), paint_col,
                       g.rgb(0.255, 0.252, 0.246))
    # RETRO-REFLECTIVE GLASS BEADS.  Circuit line paint is dressed with 0.2-0.8 mm glass
    # ballotini while it is wet — it is what makes a white line legible in a headlight
    # and, at a 12.47 deg sun 4.5 shadow-lengths long, what makes it GLITTER instead of
    # sitting there as a flat grey rectangle.  A 0.4 mm bead is sub-pixel at every
    # station except the macro one, and that is the point: sub-pixel specular that
    # averages to a slightly brighter, slightly sharper line is exactly what a real
    # beaded line does on camera.
    bead = g.voro(g.scale(P, 2400.0), 1.0, "F1", 1.0)
    bead_hi = g.mr(bead.outputs["Distance"], 0.36, 0.06, 0.0, 1.0)
    bead_hi = g.math("MULTIPLY", bead_hi,
                     g.mr(g.sep(bead.outputs["Color"])[2], 0.55, 0.95, 0.0, 1.0))
    beads = g.math("MULTIPLY", bead_hi, paint_a)
    g.tag("beads", beads)
    paint_col = g.vmulc(paint_col, g.grey(g.math("ADD", 1.0,
                                                 g.math("MULTIPLY", beads, 0.34))))
    g.tag("paint_a", paint_a)
    g.tag("base_dry", base)
    base = g.mixc(paint_a, base, paint_col)

    # ================= rubber ========================================================
    # THE BAND MUST HAVE AN EDGE.  The first version ran a halo out to
    # spread*3.3 + 1.6 m, which at the 3.9 m spread of a straight is 14.5 m - wider
    # than the road.  Rendered from the helicopter arc that is not a racing line, it is
    # one side of the tarmac being darker than the other, and it read as a lighting
    # error.  A real rubbered band is a legible object: a flat dark heart the width the
    # cars actually use, a shoulder of about a metre, and a short feather.  Measured
    # off the plan view: heart 0.55*spread (1.2 m at the hairpin, 2.1 m on the straight
    # per side), shoulder to 1.05*spread, feather to 1.9*spread + 0.9 m.
    # ... and the feather is additionally capped at 78 % of the half width, so however
    # much the cars fan out there is always clean tarmac against the white line.  On
    # the 16 m pit straight the uncapped feather reached 8.3 m, i.e. the edge, and the
    # whole straight simply went one shade darker instead of showing a corridor.
    feather = g.math("MINIMUM", g.math("ADD", g.math("MULTIPLY", spread, 1.90), 0.9),
                     g.math("MULTIPLY", Wh, 0.78))
    core = g.math("SUBTRACT", 1.0,
                  g.mr(ad, g.math("MULTIPLY", spread, 0.55),
                       g.math("MULTIPLY", spread, 1.05), 0.0, 1.0))
    halo = g.math("SUBTRACT", 1.0,
                  g.mr(ad, g.math("MULTIPLY", spread, 1.05), feather, 0.0, 1.0))
    # the two tyre tracks inside the band.  Measured car: 2.005 m wide, so the tyre
    # centres sit about 0.82 m either side of the car's centreline.  Every car that
    # has ever run here put rubber there, and it is what makes the band read as tyre
    # marks rather than as an airbrushed stripe when the lens is 5 m away at T4.
    trk_l = g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", ad, 0.82)), 0.10, 0.30, 1.0, 0.0)
    dep = g.mr(rubber, 0.40, 1.25, 0.62, 1.0)
    rub = g.math("MULTIPLY", dep,
                 g.math("ADD", core, g.math("MULTIPLY", halo, 0.34)))
    rub = g.math("ADD", rub, g.math("MULTIPLY", g.math("MULTIPLY", trk_l, core), 0.16))
    rub = g.math("MULTIPLY", rub, g.mr(streak_f, 0.22, 0.80, 0.84, 1.08))
    rub = g.math("MULTIPLY", rub, g.mr(streak2_f, 0.25, 0.78, 0.90, 1.06))
    # LAUNCH RUBBER.  Twenty cars leave twenty pairs of black stripes off the grid and
    # they are the most recognisable marking on any pit straight - and the onboard
    # follow in beat 5 runs straight over them at 330 km/h.  Each slot lays its own,
    # decaying over ~17 m as the car hooks up, with a per-slot length and intensity.
    launch = None
    for i in range(20):
        row = i // 2
        side = 1.0 if (i % 2 == 0) else -1.0
        s_front = LAP - 9.0 - row * 8.0 - (0.0 if i % 2 == 0 else 4.0)
        uc = side * 3.55
        ln = 13.0 + 1.35 * ((i * 7) % 5)
        lane = g.band(u, uc - 0.92, uc + 0.92, 0.06)
        along = g.math("MULTIPLY",
                       g.mr(s, s_front - 0.6, s_front + 0.6, 0.0, 1.0),
                       g.mr(s, s_front + 0.6, s_front + ln, 1.0, 0.0))
        b = g.math("MULTIPLY", lane, g.math("MULTIPLY", along,
                                            0.72 + 0.055 * ((i * 3) % 5)))
        launch = b if launch is None else g.math("MAXIMUM", launch, b)
    rub = g.math("MAXIMUM", rub, launch)
    rub = g.math("MULTIPLY", rub, on_track)
    rub = g.math("MINIMUM", rub, 1.0)
    g.tag("rub", rub)
    g.tag("on_track", on_track)
    g.tag("core", core)
    # RUBBER IS A RATIO, NOT A FLOOR.  The previous version multiplied to 0.24 and then
    # mixed 0.70 of the way to 0.0128, which lands a fully-rubbered heart on ~0.012
    # albedo — below fresh asphalt, below the sealant, below anything else on the
    # circuit, and two and a half stops into AgX's toe where nothing has texture.  A
    # rubbered-in racing line measures 0.028-0.035 and the thing that makes it read is
    # that it is a THIRD of the bleached tarmac beside it, not that it is black.  These
    # two numbers put the heart on 0.030 against 0.100 clean: 3.3 : 1, and the 15 mm
    # chips survive through it because the multiply no longer swamps them.
    base = g.vmulc(base, g.grey(g.mr(rub, 0.0, 1.0, 1.0, 0.60)))
    base = g.mixc(g.math("MULTIPLY", rub, 0.20), base, g.rgb(0.0232, 0.0214, 0.0208))

    # marbles: granulated rubber swept off the line, outboard of the used width
    marb_ring = g.math("MULTIPLY",
                       g.mr(ad, g.math("MULTIPLY", spread, 1.7),
                            g.math("MULTIPLY", spread, 2.4), 0.0, 1.0),
                       g.mr(edge, 0.0, 1.2, 0.0, 1.0))
    marb = g.math("MULTIPLY", marb_ring,
                  g.mr(agg2.outputs["Distance"], 0.02, 0.16, 1.0, 0.0))
    marb = g.math("MULTIPLY", marb, g.math("MULTIPLY", rubber, 0.85))
    base = g.mixc(g.math("MULTIPLY", marb, 0.7), base, g.rgb(0.0442, 0.0368, 0.0331))

    # lock-up / scrub streaks in the heavy braking zones
    wander_f, _ = g.noise(g.math("MULTIPLY", s, 0.02), 1.0, detail=2.0, dim="1D")
    dev = g.mr(wander_f, 0.0, 1.0, -1.4, 1.4)
    skid = None
    for off in (-1.15, -0.35, 0.30, 1.05):
        dd = g.math("ABSOLUTE", g.math("SUBTRACT", d, g.math("ADD", dev, off)))
        b = g.mr(dd, 0.07, 0.19, 1.0, 0.0)
        skid = b if skid is None else g.math("MAXIMUM", skid, b)
    inter_f, _ = g.noise(g.math("MULTIPLY", s, 0.55), 1.0, detail=3.0, dim="1D")
    skid = g.math("MULTIPLY", skid, g.mr(inter_f, 0.30, 0.72, 0.0, 1.0))
    skid = g.math("MULTIPLY", skid, g.math("POWER", brake, 1.4))
    skid = g.math("MULTIPLY", skid, on_track)
    base = g.mixc(g.math("MULTIPLY", skid, 0.85), base, g.rgb(0.0206, 0.0190, 0.0185))

    # dust and grit drifting in from the runoff, plus water staining down the camber
    dust_f, _ = g.noise(g.scale(P, 0.22), 1.0, detail=6.0, rough=0.6)
    dust = g.math("MULTIPLY", g.mr(edge, 2.4, -1.0, 0.0, 1.0),
                  g.mr(dust_f, 0.25, 0.85, 0.15, 1.0))
    dust = g.math("MULTIPLY", dust, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", rub, 0.8)))
    g.tag("dust", dust)
    base = g.mixc(g.math("MULTIPLY", dust, 0.52), base, g.rgb(0.1290, 0.1112, 0.0853))

    # -- DRAINAGE RUNNELS -------------------------------------------------------------
    # Water leaves the crown and runs to the verge, and where it runs often enough it
    # washes the fines out and lays a pale mineral stain in a fan of shallow channels.
    # They run ACROSS the road, at the cross-fall, which is the one direction nothing
    # else in this material runs — so they break the longitudinal grain of the streaks,
    # the lane joints and the racing line all at once.  Strongest at the low edge and
    # under the verge drain, absent under the rubber, which is where they physically are.
    run_f, _ = g.noise(g.comb(g.math("MULTIPLY", s, 2.4),
                              g.math("MULTIPLY", au, 0.09), 0.0),
                       1.0, detail=4.0, rough=0.5)
    runnel = g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", run_f, 0.5)), 0.02, 0.13, 1.0, 0.0)
    runnel = g.math("MULTIPLY", runnel, g.mr(edge, 3.6, 0.2, 0.0, 1.0))
    runnel = g.math("MULTIPLY", runnel,
                    g.math("SUBTRACT", 1.0, g.math("MULTIPLY", rub, 0.85)))
    runnel = g.math("MULTIPLY", runnel, g.mr(age, 0.20, 0.85, 0.30, 1.0))
    g.tag("runnel", runnel)
    base = g.mixc(g.math("MULTIPLY", runnel, 0.34), base, g.rgb(0.1420, 0.1330, 0.1160))

    # ================= roughness ====================================================
    rough = g.mr(age_v, 0.0, 1.0, 0.72, 0.86)
    rough = g.math("ADD", rough, g.math("MULTIPLY",
                                        g.mr(grain_f, 0.2, 0.8, -0.055, 0.055), 1.0))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", polish, 0.11))
    # A 0.30 roughness drop made the rubbered band BRIGHTER at grazing angles than
    # the asphalt around it - the specular gain cancelled the albedo loss and the
    # racing line vanished from the low pit-straight frame.  0.12 keeps the sheen
    # without hiding the line.
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", rub, 0.12))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", snake, 0.15))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", paint_a, 0.16))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", beads, 0.34))
    rough = g.math("ADD", rough, g.math("MULTIPLY", dust, 0.14))
    rough = g.math("ADD", rough, g.math("MULTIPLY", marb, 0.10))
    # flushed binder is the smoothest thing on the circuit and pluck sockets are the
    # roughest: the two together are what make the surface change character across a
    # frame instead of carrying one roughness with noise on it
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", fat, 0.30))
    rough = g.math("ADD", rough, g.math("MULTIPLY", pluck, 0.16))
    rough = g.math("ADD", rough, g.math("MULTIPLY", runnel, 0.07))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.97), 0.24)

    # ANISOTROPY.  Tyres polish stone ALONG the direction of travel, so a racing line is
    # not just darker and smoother — its specular lobe is stretched down the road, and at
    # a 12.47 deg sun that is the difference between a dark stripe and a surface that has
    # been driven on.  The tangent comes from `uv_su`, whose v axis is the lap station,
    # so the stretch direction is the road's own, corner by corner, for free.  Bounded at
    # 0.55 in the heart of the band: a fully anisotropic road reads as brushed metal.
    tang = g.n("ShaderNodeTangent")
    tang.direction_type = 'UV_MAP'
    tang.uv_map = "uv_su"
    aniso = g.math("MULTIPLY", g.mr(rub, 0.10, 1.00, 0.06, 0.55),
                   g.mr(polish, 0.0, 1.0, 0.55, 1.0))
    aniso = g.math("ADD", aniso, g.math("MULTIPLY", fat, 0.18))
    g.tag("aniso", aniso)

    # ================= height / bump =================================================
    # THE HEIGHT FIELD IS THE CHIP FIELD.  `mr(agg_d, 0.0, 0.45)` is a smooth DOME per
    # cell, and a field of domes at 18 mm is exactly the pebbled-rubber look the probe
    # came back with.  Driving the bump from `chip_hi` instead gives flat faces with a
    # sharp shoulder, which is what a crushed stone bedded in binder actually is.
    h_meso = g.math("MULTIPLY", chip_hi, 0.62)
    h_meso = g.math("ADD", h_meso,
                    g.math("MULTIPLY", g.mr(agg2.outputs["Distance"], 0.0, 0.3, 0.0, 1.0), 0.28))
    h_meso = g.math("ADD", h_meso, g.math("MULTIPLY", grain_f, 0.30))
    # Rubber FILLS the mortar, it does not plane the stones off.  Suppressing 55 % of
    # the meso relief under the band left the racing line with no aggregate at all —
    # measured 0.141 rms contrast at the 18 mm scale against 0.222 on the clean tarmac
    # 4 m away, i.e. the hero surface of the onboard follow was the smoothest thing in
    # frame.  0.28 keeps the stone and still reads as filled.
    h_meso = g.math("MULTIPLY", h_meso,
                    g.math("SUBTRACT", 1.0, g.math("MULTIPLY", rub, 0.28)))
    h_meso = g.math("SUBTRACT", h_meso, g.math("MULTIPLY", joints, 0.85))
    h_meso = g.math("ADD", h_meso, g.math("MULTIPLY", patch, 0.30))
    h_meso = g.math("SUBTRACT", h_meso, g.math("MULTIPLY", snake, 0.20))
    h_meso = g.math("ADD", h_meso, g.math("MULTIPLY", paint_a, 0.42))
    # a pluck-out is a HOLE — the one negative feature in the height field that is not a
    # cut line, and the reason the rake frame reads as a surface rather than a print
    h_meso = g.math("SUBTRACT", h_meso, g.math("MULTIPLY", pluck, 1.45))
    # flushed binder has drowned the stone, so the meso relief goes away with it
    h_meso = g.math("MULTIPLY", h_meso,
                    g.math("SUBTRACT", 1.0, g.math("MULTIPLY", fat, 0.62)))
    h_meso = g.math("SUBTRACT", h_meso, g.math("MULTIPLY", runnel, 0.22))

    # The two finest bump layers are deliberately weak.  A 0.6 mm and a 2.3 mm normal
    # perturbation is far below the ray footprint at any distance past about 8 m, so
    # past that they are pure noise: Cycles samples them at random within the pixel,
    # the denoiser smears the result into swirls, and the whole road reads as marbled
    # paper from the helicopter arc - which is exactly what the first version of this
    # frame came back as.  Keep them for the macro station, keep them quiet.
    nrm = g.bump(micro_f, strength=0.42, distance=0.00035)
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", grain_f, 0.6),
                        g.math("MULTIPLY", g.mr(agg2.outputs["Distance"], 0.0, 0.3, 0.0, 1.0),
                               0.4)),
                 strength=0.58, distance=0.0013, normal=nrm)
    nrm = g.bump(h_meso, strength=1.0, distance=0.0055, normal=nrm)
    nrm = g.bump(mott_f, strength=0.40, distance=0.0035, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Metallic"], 0.0)
    # 0.38 put enough sky in the specular lobe to turn a warm-grey binder blue in every
    # frame - the classic CG-tarmac tell.  Bitumen-coated stone is a dull dielectric;
    # 0.24 keeps the wet-look sheen on the rubbered line and takes the sky off the rest.
    g.set(bsdf.inputs["Specular IOR Level"], 0.24)
    g.set(bsdf.inputs["Anisotropic"], aniso)
    g.set(bsdf.inputs["Tangent"], tang.outputs["Tangent"])
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


# ============================================================================
# 20. KERB MATERIAL
# ============================================================================
def _mat_kerb():
    mat = bpy.data.materials.new(MPFX + "Kerb")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = _G(nt)

    kb = g.n("ShaderNodeAttribute"); kb.attribute_name = "kb"
    kb2 = g.n("ShaderNodeAttribute"); kb2.attribute_name = "kb2"
    blk_n, wear, rubv = g.sep(kb.outputs["Color"])
    ridge = kb.outputs["Alpha"]      # serration profile 0..1, NOT absolute height
    hue, val, chip = g.sep(kb2.outputs["Color"])
    across = kb2.outputs["Alpha"]
    uvk = g.n("ShaderNodeUVMap"); uvk.uv_map = "uv_k"
    _ku, kv, _ = g.sep(uvk.outputs["UV"])

    P = g.n("ShaderNodeTexCoord").outputs["Object"]
    cgrain, _ = g.noise(g.scale(P, 240.0), 1.0, detail=3.0)
    cagg = g.voro(g.scale(P, 55.0), 1.0, "SMOOTH_F1", 1.0, 0.3)
    blotch, _ = g.noise(g.scale(P, 2.6), 1.0, detail=6.0, rough=0.62)
    fine, _ = g.noise(g.scale(P, 26.0), 1.0, detail=5.0)

    # ---- two-tone: floor(blk) even => red, odd => white (spec: 1.00 m alternation)
    blk = g.math("MULTIPLY", blk_n, 256.0)
    parity = g.math("FRACT", g.math("MULTIPLY", blk, 0.5))
    edge_aa = g.math("MULTIPLY", g.math("FRACT", blk), 1.0)
    is_red = g.mr(parity, 0.49, 0.51, 1.0, 0.0)

    # per-kerb pigment identity: sun-bleached orange-pink through to deep oxide red
    red = g.mixc(hue, g.rgb(0.3200, 0.0330, 0.0225), g.rgb(0.2050, 0.0480, 0.0310))
    red = g.mixc(g.math("MULTIPLY", val, 0.6), red, g.rgb(0.3550, 0.1050, 0.0620))
    white = g.mixc(val, g.rgb(0.4950, 0.4870, 0.4650), g.rgb(0.3650, 0.3590, 0.3430))
    paint = g.mixc(is_red, white, red)
    # the first pass mottled the paint at 0.30 and every kerb came back looking like
    # watercolour; real kerb paint is flat, and the variation belongs in the WEAR
    paint = g.mixc(g.mr(blotch, 0.3, 0.75, 0.0, 0.13), paint,
                   g.mixc(0.5, paint, g.rgb(0.28, 0.27, 0.25)))

    concrete = g.mixc(g.mr(cagg.outputs["Distance"], 0.0, 0.5, 0.45, 0.0),
                      g.rgb(0.1650, 0.1600, 0.1500), g.rgb(0.2350, 0.2280, 0.2150))
    concrete = g.mixc(g.mr(cgrain, 0.3, 0.7, 0.0, 0.35), concrete,
                      g.rgb(0.1250, 0.1200, 0.1130))

    # paint wears off the serration RIDGE TOPS first, in crisp bands, and a little
    # more toward the outer lip where the tyre lands hardest
    peak = g.math("MULTIPLY", g.mr(ridge, 0.42, 0.90, 0.0, 1.0),
                  g.mr(across, 0.0, 1.0, 0.50, 1.0))
    worn = g.math("MULTIPLY", wear, g.math("ADD", 0.14, g.math("MULTIPLY", peak, 0.90)))
    worn = g.math("ADD", worn, g.math("MULTIPLY", chip, 0.55))
    worn = g.math("MULTIPLY", worn, g.mr(fine, 0.25, 0.8, 0.82, 1.12))
    worn = g.math("MINIMUM", worn, 1.0)
    col = g.mixc(worn, paint, concrete)

    # rubber smeared across the striking face
    rr = g.math("MULTIPLY", rubv, g.mr(ridge, 0.25, 0.85, 0.20, 1.0))
    rr = g.math("MULTIPLY", rr, g.mr(fine, 0.2, 0.85, 0.35, 1.0))
    col = g.mixc(g.math("MULTIPLY", rr, 0.80), col, g.rgb(0.0175, 0.0155, 0.0150))

    # grit and dirt collecting in the serration valleys and against the track-side lip
    valley = g.mr(ridge, 0.42, 0.05, 0.0, 1.0)
    dirt = g.math("MULTIPLY", valley, g.mr(blotch, 0.25, 0.8, 0.3, 1.0))
    dirt = g.math("MAXIMUM", dirt, g.math("MULTIPLY", g.mr(across, 0.10, 0.0, 0.0, 1.0), 0.8))
    col = g.mixc(g.math("MULTIPLY", dirt, 0.55), col, g.rgb(0.0950, 0.0820, 0.0620))

    # BIOFILM.  A kerb is a damp, shaded, horizontal concrete surface with a serrated
    # profile: the valleys hold water and grow algae, and it survives on the OUTBOARD
    # half, away from the tyres that scrub the apex end clean.  Dark olive-green and
    # very rough — the one detail that separates a kerb that has stood through a winter
    # from a freshly extruded one.  Two scales, so it is patchy at 0.7 m and mottled at
    # 70 mm rather than an even wash.
    moss_a, _ = g.noise(g.scale(P, 1.4), 1.0, detail=5.0, rough=0.62)
    moss_b, _ = g.noise(g.scale(P, 14.0), 1.0, detail=4.0, rough=0.55)
    moss = g.math("MULTIPLY", g.mr(moss_a, 0.52, 0.80, 0.0, 1.0),
                  g.mr(moss_b, 0.30, 0.72, 0.25, 1.0))
    moss = g.math("MULTIPLY", moss, g.mr(across, 0.35, 0.95, 0.10, 1.0))
    moss = g.math("MULTIPLY", moss, g.mr(ridge, 0.55, 0.10, 0.15, 1.0))
    moss = g.math("MULTIPLY", moss,
                  g.math("SUBTRACT", 1.0, g.math("MULTIPLY", wear, 0.85), clamp=True))
    g.tag("kerb_moss", moss)
    col = g.mixc(g.math("MULTIPLY", moss, 0.72), col, g.rgb(0.0335, 0.0412, 0.0215))
    # ... and the paint-block edge holds water, so it carries a thin dark tide line
    tide = g.math("MULTIPLY", g.mr(g.math("ABSOLUTE",
                                          g.math("SUBTRACT", edge_aa, 0.5)),
                                   0.46, 0.50, 0.0, 1.0),
                  g.mr(moss_a, 0.40, 0.72, 0.0, 1.0))
    col = g.mixc(g.math("MULTIPLY", tide, 0.30), col, g.rgb(0.0625, 0.0580, 0.0485))

    rough = g.math("ADD", 0.52, g.math("MULTIPLY", worn, 0.30))
    rough = g.math("ADD", rough, g.math("MULTIPLY", dirt, 0.16))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", rr, 0.22))
    rough = g.math("ADD", rough, g.math("MULTIPLY", moss, 0.20))
    rough = g.math("ADD", rough, g.math("MULTIPLY", g.mr(cgrain, 0.2, 0.8, -0.05, 0.05), 1.0))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.95), 0.28)

    h = g.math("MULTIPLY", g.mr(cagg.outputs["Distance"], 0.0, 0.5, 0.0, 1.0), 0.6)
    h = g.math("ADD", h, g.math("MULTIPLY", cgrain, 0.4))
    h = g.math("ADD", h, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, worn), 0.22))
    h = g.math("ADD", h, g.math("MULTIPLY", moss, 0.30))
    nrm = g.bump(cgrain, strength=0.5, distance=0.0006)
    nrm = g.bump(h, strength=1.0, distance=0.0022, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], col)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], 0.42)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


# ============================================================================
# 21. CONCRETE MATERIAL  (unrubbered access road, mu 0.90)
# ============================================================================
def _mat_concrete():
    mat = bpy.data.materials.new(MPFX + "Concrete")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = _G(nt)
    uv = g.n("ShaderNodeUVMap"); uv.uv_map = "uv_su"
    u, t, _ = g.sep(uv.outputs["UV"])
    uve = g.n("ShaderNodeUVMap"); uve.uv_map = "uv_edge"
    d_in, d_out, _ = g.sep(uve.outputs["UV"])       # metres from each declared edge
    rib = g.n("ShaderNodeAttribute"); rib.attribute_name = "rib"
    rb_r, rb_g, _rb_b = g.sep(rib.outputs["Color"])
    wid = g.math("MULTIPLY", rb_r, 16.0)            # ribbon width (m) at this row
    free_in = rb_g                                  # 1 where the inboard edge is free
    P = g.n("ShaderNodeTexCoord").outputs["Object"]

    macro, _ = g.noise(g.scale(P, 0.055), 1.0, detail=5.0, rough=0.6)
    stain, _ = g.noise(g.scale(P, 0.5), 1.0, detail=7.0, rough=0.68)
    broom, _ = g.noise(g.vmul(P, (0.02, 0.02, 1.0)), 46.0, detail=2.0)
    grit = g.voro(g.scale(P, 90.0), 1.0, "F1", 1.0)
    micro, _ = g.noise(g.scale(P, 700.0), 1.0, detail=2.0)

    base = g.mixc(macro, g.rgb(0.1980, 0.1930, 0.1830), g.rgb(0.2620, 0.2560, 0.2420))
    base = g.mixc(g.mr(stain, 0.35, 0.85, 0.0, 0.55), base, g.rgb(0.1350, 0.1300, 0.1210))
    base = g.mixc(g.mr(grit.outputs["Distance"], 0.0, 0.25, 0.25, 0.0), base,
                  g.rgb(0.3050, 0.2980, 0.2820))

    # 4.5 m saw-cut contraction joints across, 4.0 m construction joints along
    tj = g.mr(g.math("MULTIPLY",
                     g.math("ABSOLUTE", g.math("SUBTRACT", g.math("FRACT",
                            g.math("DIVIDE", t, 4.5)), 0.5)), 4.5), 0.010, 0.035, 1.0, 0.0)
    lj = g.mr(g.math("MULTIPLY",
                     g.math("ABSOLUTE", g.math("SUBTRACT", g.math("FRACT",
                            g.math("DIVIDE", g.math("ADD", u, 2.0), 4.0)), 0.5)), 4.0),
              0.010, 0.030, 1.0, 0.0)
    joints = g.math("MAXIMUM", tj, lj)
    # PER-SLAB TONE.  Every 4.5 x 4.0 m bay was poured, floated and cured on its own
    # day, and jointed concrete always reads as a chequer of slightly different greys -
    # it is the thing that says "concrete" from 40 m, where the broom finish and the
    # 20 mm joints are both sub-pixel.  Two hashes per slab: overall tone, and how much
    # of the fine limestone floated to the surface.
    sid_v, sid_c = g.wnoise(g.comb(g.math("FLOOR", g.math("DIVIDE", t, 4.5)),
                                   g.math("FLOOR", g.math("DIVIDE",
                                                          g.math("ADD", u, 2.0), 4.0)),
                                   2.0))
    sid_r, sid_g, _sid_b = g.sep(sid_c)
    base = g.vmulc(base, g.grey(g.mr(sid_v, 0.0, 1.0, 0.855, 1.145)))
    base = g.mixc(g.mr(sid_r, 0.62, 0.94, 0.0, 0.40), base, g.rgb(0.2950, 0.2880, 0.2700))

    # MAP CRAZING.  Every power-floated slab carries a net of hairline shrinkage cracks
    # at roughly 40-120 mm, and they are the reason a concrete apron reads as concrete
    # rather than as grey paint the moment a lens gets inside 3 m.  A Voronoi
    # DISTANCE_TO_EDGE field IS a crack network — no thresholding a noise level-set into
    # a fractal web, which is what made the asphalt's first tar-snake pass look like
    # frost.  Two scales, the finer one only where the surface has weathered.
    craze_a = g.voro(g.scale(P, 11.0), 1.0, "DISTANCE_TO_EDGE", 1.0)
    craze_b = g.voro(g.scale(P, 27.0), 1.0, "DISTANCE_TO_EDGE", 1.0)
    craze = g.math("MAXIMUM",
                   g.mr(craze_a.outputs["Distance"], 0.004, 0.022, 1.0, 0.0),
                   g.math("MULTIPLY",
                          g.mr(craze_b.outputs["Distance"], 0.003, 0.014, 1.0, 0.0),
                          0.55))
    craze = g.math("MULTIPLY", craze, g.mr(stain, 0.30, 0.78, 0.25, 1.0))
    g.tag("craze", craze)
    base = g.mixc(g.math("MULTIPLY", craze, 0.42), base, g.rgb(0.1080, 0.1050, 0.1000))

    # EFFLORESCENCE.  Lime carried to the surface by water leaves a chalky white bloom,
    # and it blooms where the water goes: out of the joints and down the fall.  It is
    # the only thing on this surface brighter than the slab, so it is what stops the
    # apron reading as one flat value across 116 m of Beat 4.
    eff_f, _ = g.noise(g.scale(P, 0.9), 1.0, detail=5.0, rough=0.6)
    eff = g.math("MULTIPLY", g.mr(eff_f, 0.56, 0.84, 0.0, 1.0),
                 g.mr(joints, 0.0, 0.55, 0.30, 1.0))
    eff = g.math("MULTIPLY", eff, g.mr(grit.outputs["Distance"], 0.02, 0.20, 0.45, 1.0))
    g.tag("efflor", eff)
    base = g.mixc(g.math("MULTIPLY", eff, 0.50), base, g.rgb(0.4250, 0.4230, 0.4080))

    base = g.mixc(g.math("MULTIPLY", joints, 0.75), base, g.rgb(0.0900, 0.0870, 0.0830))

    # the car has been down here exactly once, so the rubber is a single pair of
    # streaks either side of the launch axis, not a rubbered-in line
    launch = g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", g.math("ABSOLUTE", u), 0.72)),
                  0.10, 0.32, 1.0, 0.0)
    launch = g.math("MULTIPLY", launch, g.mr(t, 0.0, 34.0, 1.0, 0.0))
    launch = g.math("MULTIPLY", launch, g.mr(stain, 0.3, 0.8, 0.4, 1.0))
    base = g.mixc(g.math("MULTIPLY", launch, 0.55), base, g.rgb(0.0420, 0.0390, 0.0380))

    # ================= pit-exit markings ===========================================
    # The contract gives this module the ribbon's markings: build_architecture cuts
    # ARCH_Markings to the same polygon it cuts its paving to, so if these are not
    # painted here the pit exit has none at all.  Everything is keyed off `uv_edge`,
    # the DISTANCE FROM EACH DECLARED EDGE, because both edges are converging curves —
    # a line painted at a fixed lateral would walk off the slab.
    #
    #   * 100 mm continuous white either side: the pit-exit lane, spec §10.5.  The
    #     inboard one is dropped where the ribbon has merged onto SURF_Track's verge
    #     and the track's own blend line takes over (it is painted by M_Surf_Asphalt
    #     from s = 3459.4 over 90 m, which is exactly where this one stops).
    #   * 45 deg chevron hatch in the closing wedge, 0.30 m stripes on a 1.2 m pitch,
    #     which is what a real pit exit paints on the gore.
    wide = g.mr(wid, 1.20, 2.20, 0.0, 1.0)
    ml_out = g.math("MULTIPLY", g.band(d_out, 0.10, 0.20, 0.006), wide)
    ml_in = g.math("MULTIPLY", g.math("MULTIPLY",
                                      g.band(d_in, 0.10, 0.20, 0.006), wide), free_in)
    mark = g.math("MAXIMUM", ml_out, ml_in)
    # chevrons: fringe pattern in (t + 1.6*v), 0.30 m of paint per 1.20 m
    chev_c = g.math("FRACT", g.math("DIVIDE",
                                    g.math("ADD", t, g.math("MULTIPLY", u, 1.6)), 1.20))
    chev = g.math("MULTIPLY", g.band(chev_c, 0.0, 0.25, 0.02),
                  g.math("MULTIPLY", g.mr(wid, 0.55, 1.10, 0.0, 1.0),
                         g.mr(wid, 2.60, 4.20, 1.0, 0.0)))
    chev = g.math("MULTIPLY", chev, g.math("SUBTRACT", 1.0, free_in, clamp=True))
    mark = g.math("MAXIMUM", mark, chev)
    # concrete paint weathers by abrasion and by the sun, not by tyres — there are no
    # tyres here.  It chalks and it picks up the grit relief underneath.
    mark = g.math("MULTIPLY", mark, g.mr(stain, 0.22, 0.86, 1.0, 0.58))
    mark = g.math("MULTIPLY", mark, g.mr(grit.outputs["Distance"], 0.02, 0.14, 0.55, 1.0))
    mark = g.math("MULTIPLY", mark, g.math("SUBTRACT", 1.0,
                                           g.math("MULTIPLY", joints, 0.85), clamp=True))
    mark_col = g.mixc(g.mr(macro, 0.3, 0.8, 0.0, 0.45),
                      g.rgb(0.560, 0.556, 0.540), g.rgb(0.352, 0.350, 0.338))
    base = g.mixc(mark, base, mark_col)

    rough = g.math("ADD", 0.80, g.math("MULTIPLY", g.mr(broom, 0.2, 0.8, -0.07, 0.07), 1.0))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", launch, 0.18))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", mark, 0.16))
    rough = g.math("ADD", rough, g.math("MULTIPLY", eff, 0.10))
    rough = g.math("ADD", rough, g.math("MULTIPLY", craze, 0.06))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.96), 0.4)

    h = g.math("MULTIPLY", broom, 0.5)
    h = g.math("ADD", h, g.math("MULTIPLY", g.mr(grit.outputs["Distance"], 0.0, 0.3, 0.0, 1.0), 0.5))
    h = g.math("SUBTRACT", h, g.math("MULTIPLY", joints, 0.9))
    h = g.math("SUBTRACT", h, g.math("MULTIPLY", craze, 0.55))
    h = g.math("ADD", h, g.math("MULTIPLY", mark, 0.30))   # paint fills the broom finish
    nrm = g.bump(micro, strength=0.45, distance=0.0006)
    nrm = g.bump(h, strength=1.0, distance=0.0030, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], 0.32)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


def _mat_joint():
    """Bitumen sealant in the track / apron construction joint.

    Deliberately NOT black.  The defect this geometry closes reads as a black line at
    the track edge because a 0.300 m void is unlit; a real sealed joint is weathered
    bitumen at roughly the reflectance of the tarmac beside it, dulled by the grit that
    gets trodden into it, and it disappears at 26 m.  Anything darker than about 0.024
    would reinstate the line this exists to remove, so the palette is bounded and the
    variation is in the grit and the sheen, not in the tone.
    """
    mat = bpy.data.materials.new(MPFX + "Joint")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = _G(nt)
    uv = g.n("ShaderNodeUVMap"); uv.uv_map = "uv_su"
    a, s, _ = g.sep(uv.outputs["UV"])            # metres across / lap station
    P = g.n("ShaderNodeTexCoord").outputs["Object"]

    # the sealant was run from a lance by hand: it wanders, it pools, it skips
    wob, _ = g.noise(g.math("MULTIPLY", s, 0.9), 1.0, detail=3.0, dim="1D")
    lance = g.mr(wob, 0.15, 0.85, 0.55, 1.15)
    fill = g.mr(g.math("DIVIDE", a, g.math("MULTIPLY", lance, APRON_JOINT_LAP_M)),
                0.10, 0.86, 1.0, 0.0)
    grit = g.voro(g.scale(P, 130.0), 1.0, "SMOOTH_F1", 1.0, 0.2)
    dirt, _ = g.noise(g.scale(P, 3.2), 1.0, detail=6.0, rough=0.6)
    skip, _ = g.noise(g.math("MULTIPLY", s, 0.35), 1.0, detail=2.0, dim="1D")

    seal = g.mixc(g.mr(dirt, 0.3, 0.8, 0.0, 0.55),
                  g.rgb(0.0268, 0.0250, 0.0242), g.rgb(0.0392, 0.0368, 0.0344))
    aggr = g.mixc(g.mr(grit.outputs["Distance"], 0.02, 0.30, 1.0, 0.0),
                  g.rgb(0.0520, 0.0500, 0.0470), g.rgb(0.0930, 0.0880, 0.0800))
    # where the lance skipped, the joint shows the sawn arris of the two slabs
    f = g.math("MULTIPLY", fill, g.mr(skip, 0.20, 0.42, 0.35, 1.0))
    col = g.mixc(f, aggr, seal)
    col = g.mixc(g.math("MULTIPLY", g.mr(dirt, 0.55, 0.92, 0.0, 1.0), 0.42), col,
                 g.rgb(0.0810, 0.0700, 0.0545))          # trodden-in grit

    rough = g.mixf(f, 0.86, 0.54)
    rough = g.math("ADD", rough, g.math("MULTIPLY",
                                        g.mr(dirt, 0.2, 0.8, -0.05, 0.09), 1.0))
    rough = g.math("MAXIMUM", g.math("MINIMUM", rough, 0.95), 0.34)
    h = g.math("MULTIPLY", g.mr(grit.outputs["Distance"], 0.0, 0.3, 0.0, 1.0), 0.6)
    h = g.math("ADD", h, g.math("MULTIPLY", f, 0.5))
    nrm = g.bump(h, strength=0.8, distance=0.0018)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], col)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], 0.26)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.displacement_method = 'BUMP'
    return mat


def _mat_paint():
    mat = bpy.data.materials.new(MPFX + "GridPaint")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = _G(nt)
    P = g.n("ShaderNodeTexCoord").outputs["Object"]
    n1, _ = g.noise(g.scale(P, 4.0), 1.0, detail=7.0, rough=0.65)
    n2, _ = g.noise(g.scale(P, 90.0), 1.0, detail=3.0)
    col = g.mixc(g.mr(n1, 0.3, 0.8, 0.0, 0.55), g.rgb(0.58, 0.575, 0.560),
                 g.rgb(0.20, 0.196, 0.188))
    alpha = g.mr(n1, 0.30, 0.62, 1.0, 0.22)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], col)
    g.set(bsdf.inputs["Roughness"], g.mr(n2, 0.2, 0.8, 0.55, 0.78))
    g.set(bsdf.inputs["Alpha"], alpha)
    g.set(bsdf.inputs["Specular IOR Level"], 0.35)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ============================================================================
# 22. GRID NUMERALS
# ============================================================================
def _build_grid_numbers(coll, mat):
    objs = []
    try:
        for i in range(20):
            slot = i + 1
            row = i // 2
            side = 1.0 if (i % 2 == 0) else -1.0
            s_front = LAP - 9.0 - row * 8.0 - (0.0 if i % 2 == 0 else 4.0)
            uc = side * 3.55
            bpy.ops.object.text_add()
            ob = bpy.context.object
            ob.data.body = str(slot)
            ob.data.align_x = 'CENTER'
            ob.data.align_y = 'CENTER'
            ob.data.size = 1.05
            me = ob.to_mesh().copy()
            bpy.data.objects.remove(ob, do_unlink=True)
            co = np.array([v.co[:] for v in me.vertices], float)
            if co.size == 0:
                bpy.data.meshes.remove(me)
                continue
            # Glyph local (x right, y up) -> track.  Two things matter and both were
            # wrong first time:
            #   * the numeral is read by a driver walking UP the grid, so glyph +y
            #     must be +s (further away) - that part was right;
            #   * that same viewer's right hand is -u, so glyph +x maps to -u.
            #     Mapping it to +u paints every number mirrored.
            # And the number goes BESIDE the box, outboard of it, which is where a
            # real grid paints it - not 1.6 m behind the tail of the box.
            s_txt = s_front - 3.0
            uu = (uc + side * 2.45) - co[:, 0]
            ss = s_txt + co[:, 1]
            X, Y, H, _ = _centreline_arrays(ss)
            Z = surface_z(ss, uu) + 0.0035
            world = np.stack([X - np.sin(H) * uu, Y + np.cos(H) * uu, Z], axis=-1)
            for j, v in enumerate(me.vertices):
                v.co = world[j]
            name = "%sGridNum_%02d" % (PFX, slot)
            me.name = name
            me.materials.clear()
            me.materials.append(mat)
            nob = bpy.data.objects.new(name, me)
            coll.objects.link(nob)
            objs.append(nob)
    except Exception as exc:                                   # pragma: no cover
        print("  ! grid numerals skipped:", exc)
    return objs


# ============================================================================
# 23. PURGE / BUILD
# ============================================================================
def _purge():
    coll = bpy.data.collections.get(COLL_NAME)
    if coll:
        for ob in list(coll.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if isinstance(me, bpy.types.Mesh) and me.users == 0:
                bpy.data.meshes.remove(me)
        for sc in bpy.data.scenes:
            if coll.name in sc.collection.children:
                sc.collection.children.unlink(coll)
        bpy.data.collections.remove(coll)
    for m in list(bpy.data.materials):
        if m.name.startswith(MPFX):
            bpy.data.materials.remove(m)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PFX) and me.users == 0:
            bpy.data.meshes.remove(me)


def prepare():
    """Populate the module cache without touching the Blender scene."""
    if _S.get("ready"):
        return _S
    spec = _load_spec()
    _S["spec"] = spec
    _S["els"] = _elements(spec)
    # PROVENANCE, not faith.  The element table here is only tag/type/radius/length/
    # station; every position comes from C.centreline.  Check that the contract's
    # centreline actually lands on the spec's own published element start points, so
    # a future edit to either cannot silently move this module's kerbs and grid.
    worst = 0.0
    for e in _S["els"]:
        x, y, _z, _h, _k = C.centreline(e["s0"])
        worst = max(worst, math.hypot(x - e["start_world"][0], y - e["start_world"][1]))
    _S["element_start_max_dev_m"] = worst
    if worst > 0.02:
        raise RuntimeError("contract centreline disagrees with the spec's element "
                           "start points by %.4f m" % worst)
    _S["half_w"] = C.half_width(_fgrid())
    tel = _load_telemetry()
    _build_usage(spec, tel)
    _build_racing_line(spec)
    _build_zones()
    _build_kerb_runs(spec)
    _S["telemetry"] = tel is not None
    _S["contract_version"] = C.__version__
    _S["ready"] = True
    return _S


def build():
    t0 = time.time()
    _purge()
    prepare()

    coll = bpy.data.collections.new(COLL_NAME)
    bpy.context.scene.collection.children.link(coll)

    m_asph = _mat_asphalt()
    m_kerb = _mat_kerb()
    m_conc = _mat_concrete()
    m_joint = _mat_joint()
    m_paint = _mat_paint()

    road, nr, nc, road_q = _build_road(coll, m_asph)
    kerbs, kerb_tris = _build_kerbs(coll, m_kerb)
    acc, acc_q = _build_access(coll, m_conc)
    joint, joint_q, joint_len = _build_apron_joint(coll, m_joint)
    nums = _build_grid_numbers(coll, m_paint)

    tris = road_q * 2 + kerb_tris + acc_q * 2 + joint_q * 2
    for o in nums:
        tris += len(o.data.polygons)

    # verification
    ln = _S["line"]
    lim = _S["half_w"] - 0.35
    summary = dict(
        module="world/build_surface.py",
        collection=COLL_NAME,
        objects=len(coll.objects),
        triangles=int(tris),
        road_rows=int(nr), road_cols=int(nc),
        road_quads=int(road_q),
        kerb_runs=len(kerbs),
        kerb_triangles=int(kerb_tris),
        access_quads=int(acc_q),
        apron_joint_quads=int(joint_q),
        apron_joint_len_m=round(joint_len, 1),
        apron_joint_lap_m=APRON_JOINT_LAP_M,
        ribbon_t_min_m=RIBBON_T_MIN,
        ribbon_cap_end_m=RIBBON_CAP_END_M,
        grid_numerals=len(nums),
        materials=[m_asph.name, m_kerb.name, m_conc.name, m_joint.name,
                   m_paint.name],
        lap_m=LAP,
        racing_line_max_abs_m=float(np.max(np.abs(ln))),
        racing_line_inside_track=bool(np.all(np.abs(ln) <= lim + 1e-9)),
        racing_line_apex_hits=int(np.sum(np.abs(ln) > (lim - 0.25))),
        half_width_range_m=[float(_S["half_w"].min()), float(_S["half_w"].max())],
        elevation_range_m=[float(elevation_c(_fgrid()).min()),
                           float(elevation_c(_fgrid()).max())],
        telemetry_used=_S["telemetry"],
        negative_kerbs=[[float(a), float(b), float(sd)] for (a, b, sd) in _S["neg_kerbs"]],
        contract_version=C.__version__,
        build_s=round(time.time() - t0, 2),
    )
    # PROCEDURAL TEXTURE CENSUS.  The assembly review's stated reason the world reads as
    # placeholder is that it carries 22 procedural texture nodes across six modules.
    # "There is not one image texture in this module" is only half a claim without the
    # other half, so both halves are counted on every build.
    tex, img, nodes = {}, 0, 0
    for m in (m_asph, m_kerb, m_conc, m_joint, m_paint):
        n_t = n_i = 0
        for nd in m.node_tree.nodes:
            nodes += 1
            if nd.bl_idname.startswith("ShaderNodeTex"):
                if nd.bl_idname == "ShaderNodeTexImage":
                    n_i += 1
                elif nd.bl_idname != "ShaderNodeTexCoord":
                    n_t += 1
        tex[m.name] = n_t
        img += n_i
    summary["procedural_texture_nodes"] = tex
    summary["procedural_texture_nodes_total"] = int(sum(tex.values()))
    summary["shader_nodes_total"] = int(nodes)
    summary["image_texture_nodes"] = int(img)
    summary["contract"] = verify(quiet=True)
    return summary


# ============================================================================
# 23b. CONTRACT CONFORMANCE GATE
# ============================================================================
#
# The single lesson of the assembly review is that six agents each verified their own
# work in isolation and the assembled world was broken.  So this does not check that
# the module agrees with itself.  Every number below is this module's geometry measured
# against `world_contract`, and where the two disagree the disagreement is printed with
# its magnitude rather than hidden behind a tolerance.

def _old_build_width():
    """The PRE-CONTRACT `_build_width`, kept only so `verify()` can quantify the fix.

    It is never called by `build()`.  It exists because "the width bug is fixed" is a
    claim, and "the width bug was 0.978 m over 14.1 % of the lap and is now 0.000 m"
    is a measurement.
    """
    ts = _load_spec()["track_section"]
    g = _fgrid()
    w = np.full(_FN, ts["standard_m"])

    def setrange(a, b, val):
        a %= LAP; b %= LAP
        m = (g >= a) & (g <= b) if a < b else ((g >= a) | (g <= b))
        w[m] = val
    setrange(3115.0 + 30.0, 250.0 - 30.0, ts["pit_straight_m"])
    setrange(905.0, 1055.0, ts["hairpin_m"])
    setrange(1545.0, 1905.0, ts["esses_m"])
    return _csmooth(w, 15.0) * 0.5


def _mesh_xyz(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def verify(quiet=False, n_samples=200000, seed=20260728):
    """Measure this module against `world_contract`.  Returns a dict of numbers."""
    prepare()
    r = {}
    rng = np.random.default_rng(seed)
    g = _fgrid()

    # ---- 1. half_width: the fix, quantified ---------------------------------
    old = _old_build_width()
    new = C.half_width(g)
    d = np.abs(old - new)
    r["half_width_old_vs_contract_max_m"] = float(d.max())
    r["half_width_old_vs_contract_rms_m"] = float(np.sqrt((d * d).mean()))
    r["half_width_old_frac_lap_over_10mm"] = float((d > 0.010).mean())
    r["half_width_now_vs_contract_max_m"] = float(
        np.abs(track_half_width(g) - new).max())
    r["half_width_at_3115"] = float(track_half_width(3115.0))
    r["half_width_at_250"] = float(track_half_width(250.0))
    r["half_width_at_3085_midpoint"] = float(track_half_width(3085.0))

    # ---- 2. surface_z vs the datum ------------------------------------------
    S = rng.uniform(0.0, LAP, n_samples)
    W = C.half_width(S)
    U = rng.uniform(-1.0, 1.0, n_samples) * W
    dz = np.abs(surface_z(S, U) - C.ground_z(S, U))
    r["micro_layer_max_m"] = float(dz.max())
    r["micro_layer_p99_m"] = float(np.percentile(dz, 99))
    r["micro_layer_p50_m"] = float(np.percentile(dz, 50))
    r["micro_layer_within_contract_bound"] = bool(dz.max() <= C.MICRO_LAYER_MAX_M + 1e-12)
    # ... and identically zero at and beyond half_width, which is what lets the kerbs,
    # the runoff platform and the terrain rim all sit on C.ground_z alone.
    Uo = np.sign(rng.uniform(-1, 1, 40000)) * (
        C.half_width(S[:40000]) + rng.uniform(0.0, 2.5, 40000))
    r["micro_layer_outside_track_max_m"] = float(
        np.abs(surface_z(S[:40000], Uo) - C.ground_z(S[:40000], Uo)).max())

    # ---- 3. built meshes vs the datum ---------------------------------------
    # Two DIFFERENT questions, and conflating them hides both:
    #   (a) is the mesh the datum?           mesh z vs surface_z(S, U) it was built from
    #   (b) what does a NEIGHBOUR get?       mesh z vs C.ground_z(C.project(x, y))
    # (b) is looser than (a) by the round-trip error of C.project, which is this
    # module's only remaining source of disagreement with anyone and is reported below
    # with its own magnitude so nobody has to guess where it came from.
    co = _mesh_xyz(PFX + "Track")
    if co is not None:
        S1 = _row_stations(); cols = _col_layout()
        rows, nc = len(S1), len(cols)
        Sg = np.repeat(S1[:, None], nc, axis=1)
        Wg = C.half_width(Sg)
        Ug = np.empty_like(Sg)
        for j, (kind, val) in enumerate(cols):
            Ug[:, j] = (val * Wg[:, j] if kind == 0
                        else np.sign(val) * (Wg[:, j] + abs(val)))
        if co.shape[0] == rows * nc:
            r["track_mesh_vs_datum_exact_max_m"] = float(
                np.abs(co[:, 2] - surface_z(Sg, Ug).ravel()).max())
            # the outer edge of this module's mesh IS C.verge_edge, by construction
            r["outer_edge_vs_verge_edge_exact_max_m"] = float(max(
                np.abs(np.abs(Ug[:, 0]) - C.verge_edge(S1)).max(),
                np.abs(np.abs(Ug[:, -1]) - C.verge_edge(S1)).max()))
        k = rng.choice(co.shape[0], size=min(80000, co.shape[0]), replace=False)
        s, u = C.project(co[k, 0], co[k, 1])
        e = np.abs(co[k, 2] - surface_z(s, u))
        r["track_mesh_vs_datum_reprojected_max_m"] = float(e.max())
        away = np.minimum(s, LAP - s) > 1.0        # away from the S/F line, see below
        r["track_mesh_vs_datum_reprojected_max_m_off_sf"] = float(e[away].max())
        for j, lbl in ((0, "right"), (nc - 1, "left")):
            idx = np.arange(rows) * nc + j
            se, ue = C.project(co[idx, 0], co[idx, 1])
            r["outer_edge_%s_vs_verge_edge_reproj_max_m" % lbl] = float(
                np.abs(np.abs(ue) - C.verge_edge(se)).max())

    # C.project's own round trip, so (b) above is attributable rather than mysterious.
    Sp = rng.uniform(0.0, LAP, 120000)
    Up = rng.uniform(-1.0, 1.0, 120000) * C.verge_edge(Sp)
    Xp, Yp, Hp, _Kp = C.centreline_arrays(Sp)
    sp, up = C.project(Xp - np.sin(Hp) * Up, Yp + np.cos(Hp) * Up)
    r["contract_project_ds_max_m"] = float(
        np.abs((sp - Sp + LAP * 0.5) % LAP - LAP * 0.5).max())
    r["contract_project_du_max_m"] = float(np.abs(up - Up).max())

    # ---- 3b. A CONTRACT DEFECT THIS MODULE FOUND AND CANNOT FIX --------------
    # `C._undulation` evaluates value noise on raw S, which is NOT cyclic, so the datum
    # STEPS across the start/finish line.  It is inherited from this module's old
    # `_undulation` — the bug is mine originally — but it now lives in world_contract
    # and only world_contract can close it (multiply S by a whole number of noise cells
    # per lap, or ease the last 30 m into the first).  Measured below across the full
    # cross-section.  It is inside C.TOL_SEAM_M and it lands under the 400 mm painted
    # start/finish line, but it is a step in THE datum on the pit straight, which is
    # where the onboard follow crosses at 330 km/h, so it is reported every build.
    uu = np.linspace(-C.verge_edge(0.0), C.verge_edge(0.0), 421)
    step = C.ground_z(np.full_like(uu, LAP - 1e-9), uu) - C.ground_z(np.zeros_like(uu), uu)
    r["contract_datum_sf_line_step_m"] = float(np.abs(step).max())
    r["contract_datum_sf_line_step_within_TOL_SEAM"] = bool(
        np.abs(step).max() <= C.TOL_SEAM_M)

    # ---- 4. the access ribbon ------------------------------------------------
    L = _access_layout()
    T1, V, nc2 = L["T"], L["V"], L["nc"]
    PXr = L["X"][:, None] - np.sin(L["H"])[:, None] * V
    PYr = L["Y"][:, None] + np.cos(L["H"])[:, None] * V
    Sr, Ur = C.project(PXr.ravel(), PYr.ravel())
    Zr = C.ground_z(Sr, Ur).reshape(V.shape)
    apron = T1 <= C.ACCESS_L2
    r["ribbon_apron_run_max_abs_z_m"] = float(np.abs(Zr[apron]).max())
    r["ribbon_apron_run_len_m"] = float(C.ACCESS_L2)
    # the seam this module shares with SURF_Track: the ribbon's inboard edge wherever
    # that edge has converged onto the racing surface's own outer edge.
    clip = L["free_in"] <= 1e-9
    if clip.any():
        px = L["X"][clip] - np.sin(L["H"][clip]) * L["vin"][clip]
        py = L["Y"][clip] + np.cos(L["H"][clip]) * L["vin"][clip]
        ss, uu = C.project(px, py)
        z_built = C.ground_z(ss, uu)
        z_accessz = C.access_z(T1[clip], L["vin"][clip])
        r["ribbon_track_seam_built_max_m"] = float(np.abs(z_built - C.ground_z(ss, uu)).max())
        r["ribbon_track_seam_if_access_z_max_m"] = float(
            np.abs(z_accessz - C.ground_z(ss, uu)).max())
        r["ribbon_track_shared_edge_len_m"] = float(T1[clip].max() - T1[clip].min())
        r["ribbon_clip_engages_at_t_m"] = float(T1[clip].min())
    # how far C.access_z would have put the ribbon off the datum, anywhere on it
    r["access_z_vs_ground_z_max_m"] = float(
        np.abs(C.access_z(np.repeat(T1[:, None], nc2, axis=1).ravel(), V.ravel())
               - Zr.ravel()).max())
    # this mesh's boundary IS C.access_ribbon_polygon(0.30) wherever the edge is free
    freeE = L["free_in"] > 0.35
    r["ribbon_saw_strip_m"] = float(L["saw"].max())
    r["ribbon_saw_matches_polygon_max_m"] = float(np.abs(
        (L["hi"][freeE] - L["vout"][freeE]) - ACCESS_SAW_M).max())
    # area of ribbon that lies outboard of verge_edge, i.e. on top of the runoff
    # programme.  build_barriers must cut its platform to the ribbon over this stretch.
    dt = float(T1[1] - T1[0])
    wid = np.maximum(L["vout"] - L["vin"], 0.0)
    r["ribbon_area_m2"] = float((wid * dt).sum())
    r["ribbon_area_over_platform_m2"] = float((wid * dt)[clip].sum())
    if clip.any():
        sc, _ = C.project(L["X"][clip], L["Y"][clip])
        r["ribbon_over_platform_s_range"] = [float(sc.min()), float(sc.max())]

    cor = _mesh_xyz(PFX + "AccessRoad")
    if cor is not None:
        s2, u2 = C.project(cor[:, 0], cor[:, 1])
        r["ribbon_mesh_vs_ground_z_max_m"] = float(np.abs(cor[:, 2] - C.ground_z(s2, u2)).max())
        onap = cor[:, 0] <= C.ACCESS_GLASS_X + C.ACCESS_L2
        r["ribbon_mesh_apron_max_abs_z_m"] = float(np.abs(cor[onap, 2]).max())
        r["ribbon_mesh_x_min_m"] = float(cor[:, 0].min())
        # THE RIBBON MUST NOT LIE ON THE RACING SURFACE.  `C.access_edges` clips the
        # inboard edge to `verge_edge`, so the two meshes share a 149 m edge exactly —
        # which is also why the BVH census reports one AccessRoad/Track pair: coincident
        # boundary triangles touch.  The number that separates "shares an edge" from
        # "lies on top of the track" is the LATERAL excursion, so it is measured.
        near = np.abs(np.abs(u2) - C.verge_edge(s2)) < 5.0
        if near.any():
            exc = (C.verge_edge(s2[near]) - np.abs(u2[near]))
            r["ribbon_inboard_of_verge_edge_max_m"] = float(exc.max())
            r["ribbon_verts_inboard_over_1mm"] = int((exc > 0.001).sum())

    # ---- 4b. THE CORRIDOR MOUTH AT THE GLASS PLANE  (assembly defect #2) ------
    # Three modules used three different margins for the SAME boundary and nobody
    # built x 12.0 -> 15.0.  These are the four numbers, measured, not asserted.
    r["ribbon_t_min_contract"] = RIBBON_T_MIN
    r["ribbon_cap_end_m"] = RIBBON_CAP_END_M
    r["ribbon_mesh_t_min_m"] = float(T1.min())
    r["ribbon_mesh_t_max_m"] = float(T1.max())
    x_mesh = float(cor[:, 0].min()) if cor is not None else C.ACCESS_GLASS_X
    r["ribbon_mesh_cap_vs_glass_plane_m"] = float(x_mesh - C.ACCESS_GLASS_X)
    # EVERY consumer's cut must land on the same x.  Sample the three predicates that
    # decide it and report the widest disagreement in metres — this is the number that
    # was 3.000 (terrain 12.00, paving 14.70, this mesh 15.000) and must now be 0.000.
    xb = C.ACCESS_GLASS_X - np.arange(-0.05, 4.001, 0.005)
    caps = {}
    for nm, mg in (("terrain_keepout", C.ACCESS_CORRIDOR_MARGIN_M),
                   ("paving_saw", ACCESS_SAW_M), ("bare", 0.0)):
        m = C.in_access_ribbon(xb, np.zeros_like(xb), margin=mg)
        caps[nm] = float(xb[m].min()) if m.any() else None
    caps["build_surface_mesh"] = x_mesh
    r["glass_cap_x_by_consumer"] = caps
    vals = [v for v in caps.values() if v is not None]
    r["glass_cap_max_disagreement_m"] = float(max(vals) - min(vals))
    # ... and the same question asked of the terrain cut itself
    cut = C.road_corridor_mask(xb, np.zeros_like(xb))
    x_cut = float(xb[cut].min()) if cut.any() else C.ACCESS_GLASS_X
    r["corridor_mask_reaches_x_m"] = x_cut
    r["corridor_cap_inside_building_m"] = float(max(0.0, C.ACCESS_GLASS_X - x_cut))
    r["corridor_cap_unbuilt_beyond_ribbon_m"] = float(max(0.0, x_mesh - x_cut))
    # the mouth itself: the review's own grid, answered by the contract.  Every sample
    # over x 4..17, y +-14 must name an owner; `build_surface` must own exactly the
    # ribbon and nothing behind the glass.
    gx, gy = np.meshgrid(np.arange(4.0, 17.001, 0.10), np.arange(-14.0, 14.001, 0.5))
    gz, gown = C.world_ground_z(gx.ravel(), gy.ravel())
    nm = np.array([str(o) for o in gown])
    r["glass_mouth_samples"] = int(nm.size)
    r["glass_mouth_terrain_owned"] = int((nm == C.OWNER_TERRAIN).sum())
    r["glass_mouth_surface_owned"] = int(np.char.startswith(nm, "build_surface").sum())
    r["glass_mouth_surface_x_range"] = [
        float(gx.ravel()[np.char.startswith(nm, "build_surface")].min()),
        float(gx.ravel()[np.char.startswith(nm, "build_surface")].max())]
    # the outboard sawn strip must exist wherever build_architecture cuts to it
    vo = L["vout"]
    pxo = L["X"] - np.sin(L["H"]) * (vo + 0.15)
    pyo = L["Y"] + np.cos(L["H"]) * (vo + 0.15)
    _zo, owno = C.world_ground_z(pxo, pyo)
    m_arch = np.array([str(o) == C.OWNER_APRON for o in owno])
    r["ribbon_saw_out_min_where_arch_owns_m"] = (
        float(L["saw_out"][m_arch].min()) if m_arch.any() else None)
    r["ribbon_saw_out_route_m_where_arch_owns"] = float(
        m_arch.sum() * float(T1[1] - T1[0]))
    r["ribbon_saw_out_shortfall_max_m"] = (
        float((ACCESS_SAW_M - L["saw_out"][m_arch]).max()) if m_arch.any() else 0.0)

    # ---- 4c. THE TRACK / APRON JOINT  (assembly defect #3) -------------------
    jo = _mesh_xyz(PFX + "ApronJoint")
    if jo is not None:
        sj, uj = C.project(jo[:, 0], jo[:, 1])
        d = np.abs(uj) - C.verge_edge(sj)
        r["apron_joint_verts"] = int(jo.shape[0])
        r["apron_joint_across_range_m"] = [float(d.min()), float(d.max())]
        r["apron_joint_s_range"] = [float(sj.min()), float(sj.max())]
        # the inner edge IS SURF_Track's outer edge: same rows, same u, same ground_z
        S1r = _row_stations()
        keep = C.apron_zone(S1r, +1) > 0.5
        Sk = S1r[keep]
        Uk = C.verge_edge(Sk)
        r["apron_joint_inner_vs_track_edge_max_m"] = float(np.abs(
            (C.ground_z(Sk, Uk) + 0.0) - surface_z(Sk, Uk)).max())
        # what the joint replaces: architecture's first bay begins 12 mm outboard of
        # verge_edge and the sub-base is 0.300 m down.  Measured at the review's own
        # three stations.
        probes = []
        for s0 in (3247.0, 3305.0, 3361.0):
            u0 = float(C.verge_edge(s0)) + 0.006
            zj = float(C.ground_z(s0, u0)) - APRON_JOINT_DEPTH_M
            probes.append([s0, round(u0, 4), round(zj - float(C.ground_z(s0, u0)), 4)])
        r["apron_joint_probe_s_u_dz"] = probes
        r["apron_joint_was_open_depth_m"] = 0.300
        r["apron_joint_now_depth_m"] = APRON_JOINT_DEPTH_M
        r["apron_joint_lap_vs_arch_inset_m"] = [APRON_JOINT_LAP_M, 0.012]

    # ---- 5. Beat 4: the review's own scan line, y = 0, x = -5 .. +111 --------
    x = np.arange(-5.0, 111.001, 0.25)
    y = np.zeros_like(x)
    zz, own = C.world_ground_z(x, y)
    names = [str(o) for o in own]
    flips = sum(1 for i in range(1, len(names)) if names[i] != names[i - 1])
    r["beat4_scan_ownership_changes"] = int(flips)
    r["beat4_scan_owners"] = sorted(set(names))
    r["beat4_scan_unowned_points"] = int(np.isnan(zz).sum())
    r["beat4_scan_surface_owned_m"] = float(
        0.25 * sum(1 for nm in names if nm.startswith("build_surface")))

    # ... and the same scan done as a RAYCAST against the geometry that was actually
    # built, because "the contract says who owns it" and "two meshes are 1.4 mm apart
    # under the flying camera" are different claims and the review measured the second.
    # It can only speak for the meshes in the scene, so with build_architecture absent
    # it proves this module does not fight ITSELF; what stops it fighting the paddock is
    # `ribbon_saw_matches_polygon_max_m` above.
    try:
        import mathutils
        objs = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith(PFX)]
        hits = np.zeros(len(x), int)
        gaps = []
        down = mathutils.Vector((0.0, 0.0, -1.0))
        for i, xx in enumerate(x):
            zs = []
            for ob in objs:
                mw = ob.matrix_world
                inv = mw.inverted()
                org = inv @ mathutils.Vector((float(xx), 0.0, 80.0))
                dr = (inv.to_3x3() @ down).normalized()
                ok, loc, _nrm, _idx = ob.ray_cast(org, dr, distance=300.0)
                if ok:
                    zs.append(float((mw @ loc).z))
            hits[i] = len(zs)
            if len(zs) > 1:
                zs.sort(reverse=True)
                gaps.append(zs[0] - zs[1])
        r["beat4_raycast_points"] = int(len(x))
        r["beat4_raycast_max_surfaces_at_a_point"] = int(hits.max())
        r["beat4_raycast_points_with_two_surfaces"] = int((hits > 1).sum())
        r["beat4_raycast_coplanar_pairs_under_TOL"] = int(
            sum(1 for g in gaps if g < C.TOL_COPLANAR_M))
    except Exception as exc:                                    # pragma: no cover
        r["beat4_raycast_error"] = str(exc)

    # ---- 5b. THIS MODULE AGAINST ITSELF, at triangle level -------------------
    # `tools/collision_gate.py` is object-vs-environment and reports CLEAN on a blend
    # that contains no car, which is precisely the kind of vacuous pass the assembly
    # review exists because of.  The question that is NOT vacuous is whether the four
    # mesh families this module builds — track, 35 kerbs, ribbon, apron joint —
    # intersect EACH OTHER.  `SURF_ApronJoint` is new and shares a 233.7 m edge with
    # `SURF_Track`, so it has to be proved rather than argued.
    try:
        from mathutils.bvhtree import BVHTree
        deps = bpy.context.evaluated_depsgraph_get()
        trees, names = [], []
        for ob in bpy.data.objects:
            if ob.type != 'MESH' or not ob.name.startswith(PFX):
                continue
            trees.append(BVHTree.FromObject(ob, deps))
            names.append(ob.name)
        pairs = []
        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                ov = trees[i].overlap(trees[j])
                if ov:
                    pairs.append([names[i], names[j], len(ov)])
        r["self_bvh_objects"] = len(trees)
        r["self_bvh_intersecting_pairs"] = len(pairs)
        # Categorise, because "39 intersecting pairs" is not a finding, it is a number.
        # A kerb SITS ON the road: contract SS4 embeds anything standing on the ground by
        # C.BASE_EMBED_M, so kerb-vs-track pairs are the embed and are expected.  Anything
        # else is not, and is listed by name.
        kt = [q for q in pairs if "Kerb" in q[0] + q[1] and "Track" in q[0] + q[1]]
        kk = [q for q in pairs if "Kerb" in q[0] and "Kerb" in q[1]]
        other = [q for q in pairs if q not in kt and q not in kk]
        r["self_bvh_kerb_on_track_pairs"] = len(kt)
        r["self_bvh_kerb_on_kerb_pairs"] = len(kk)
        r["self_bvh_unexplained_pairs"] = [q[:2] for q in other]
    except Exception as exc:                                    # pragma: no cover
        r["self_bvh_error"] = str(exc)

    # ---- 5c. THE KERB FOOT --------------------------------------------------
    # The profile's track-side lip used to start 21 mm above the road with nothing
    # under it — an open shell edge along all 35 runs, at a sun with a 4.52 shadow
    # ratio.  Measure what the riser actually does: its top, its bottom, and the
    # embed below the datum.
    try:
        prof = _kerb_profile_cols()
        embeds, risers = [], []
        for rr in _S["kerb_runs"]:
            L0 = rr["s1"] - rr["s0"]
            if L0 < 4.0:
                continue
            sm = 0.5 * (rr["s0"] + rr["s1"])
            um = rr["sign"] * float(C.half_width(sm))
            co2 = _mesh_xyz(rr["name"])
            if co2 is None:
                continue
            s3, u3 = C.project(co2[:, 0], co2[:, 1])
            dz3 = co2[:, 2] - C.ground_z(s3, u3)
            inner = np.abs(np.abs(u3) - C.half_width(s3)) < 0.02
            if inner.any():
                embeds.append(float(dz3[inner].min()))
                risers.append(float(dz3[inner].max() - dz3[inner].min()))
        if embeds:
            r["kerb_inner_embed_min_m"] = float(min(embeds))
            r["kerb_inner_embed_max_m"] = float(max(embeds))
            r["kerb_inner_riser_max_m"] = float(max(risers))
            r["kerb_embed_meets_BASE_EMBED"] = bool(
                max(embeds) <= -C.BASE_EMBED_M + 1e-9)
    except Exception as exc:                                    # pragma: no cover
        r["kerb_foot_error"] = str(exc)

    # ---- 6. kerb tops against the spec, through the contract ----------------
    # the trough, isolated against the LOCAL cross-section: measured at the trough
    # centre against the chord from the track edge to just outboard of the 0.80 m band,
    # so the crown, the banking and the verge drain all cancel.
    depth = []
    for (a, b, sd) in _S["neg_kerbs"]:
        sm = 0.5 * (a + b)
        w = float(C.half_width(sm))
        d0, dm, d1 = 0.02, C.NEG_KERB_W * 0.5, C.NEG_KERB_W + 0.10
        z0 = float(C.ground_z(sm, sd * (w + d0)))
        z1 = float(C.ground_z(sm, sd * (w + d1)))
        zt = float(C.ground_z(sm, sd * (w + dm)))
        depth.append(round(zt - (z0 + (z1 - z0) * (dm - d0) / (d1 - d0)), 4))
    r["neg_kerb_depth_m"] = depth          # spec §9 wants -0.060
    r["contract_version"] = C.__version__

    if not quiet:
        print("\n=== build_surface -> world_contract conformance ===")
        for k2 in sorted(r):
            print("  %-42s %s" % (k2, r[k2]))
    return r


# ============================================================================
# 24. TEST RENDER HARNESS
# ============================================================================
_SHOT_NOTES = {
    "doppler_pass": "the spec's doppler hover station: 26.0 m out, 2.40 m over grade,"
                    " aimed 50 m down-road because the surface there is at 5 deg",
    "hairpin_kerb": "kerb height OUTSIDE T4 looking across it - the film's hero corner",
    "straight_low": "onboard height down the pit straight: grid, S/F line, faded paint",
    "sweeper_air": "T10/T11 from the helicopter arc - racing line and kerbs from above",
    "wide_repeat_check": "wide over the esses, hunting for recognisable repeats",
    "macro_asphalt": "1.3 m of frame: aggregate, segregation, tar snakes, lane joint",
    "kerb_macro": "1 m of kerb: serrations, precast joints, paint blocks, wear, rubber",
    "negative_kerb": "the T8 apex negative kerb, -60 mm x 0.80 m",
    "grid_launch": "the grid at onboard height: launch rubber, boxes, numerals, S/F",
    "access_road": "the mu 0.90 concrete apron out of the breach - a different surface",
    "pit_edge_16m": "s=3115, where the 16 m pit straight opens: the road edge must "
                    "reach C.verge_edge or the unbuilt strip is still there",
    "merge_seam": "route t=104..150: concrete meeting asphalt along the edge the "
                  "ribbon shares with SURF_Track, raked so a 1 mm step would light up",
    "apron_flat": "the 49.60 m apron run, dead flat at z=0.000 per spec 10.3(b), with "
                  "the pit-exit lane markings this module now owns",
    "pit_width_plan": "true-scale plan across s=3115: the road edge must land ON the "
                      "platform edge, not 0.978 m inside it",
    "albedo_probe": "PHOTOMETRIC. 12.0 m of pit straight in true-scale plan with an "
                    "18 % card, view_transform=Standard so the pixel IS linear "
                    "reflectance and the asphalt can be MEASURED",
    "apron_joint_macro": "50 mm at 1.15 m ACROSS the joint: the track/apron joint "
                         "against a stand-in "
                         "built to architecture's measured 12 mm bay inset and 0.300 m "
                         "sub-base drop. A/B on one variable: SURF_ApronJoint",
    "apron_joint_rake": "0.35 m off the deck, 92 m down the pit-exit apron edge: the "
                        "track/apron joint, raked by the 12.47 deg sun",
    "glass_cap_plan": "true-scale plan of the corridor mouth with the three disputed "
                      "cut lines: x 12.00 (terrain), 14.70 (paving), 15.00 (the pin)",
    "rake_low": "0.60 m off the deck along the 12.47 deg sun azimuth: surface relief "
                "either exists here or the tarmac is a painted plane",
}


def _mk_sun(scene):
    """TEST-ONLY light rig, built ENTIRELY from `world_contract` §8.

    The previous version of this function invented its own sun — energy 5.0, colour
    (1.000, 0.705, 0.435), aerosol 1.6, ozone 2.0, exposure -0.85 with an
    'AgX - Medium High Contrast' look — and every material in this module was tuned
    under it.  That is assembly-review finding #5 committed inside a test harness: a
    surface calibrated against a light that does not exist looks wrong the moment
    build_sky is switched on.

    Every number here is now `C.SUN_*` / `C.SKY_*` / `C.REFERENCE_EXPOSURE_EXTERIOR`,
    which are build_sky's shipped, MEASURED values.  A Blender SUN emits along its own
    -Z, so the local Z axis must be the direction-TO-sun.
    """
    v = np.array(C.SUN_DIR, float); v /= np.linalg.norm(v)
    lamp = bpy.data.lights.new("TEST_Sun", 'SUN')
    lamp.energy = C.SUN_ENERGY
    lamp.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    lamp.color = C.SUN_COLOR
    ob = bpy.data.objects.new("TEST_Sun", lamp)
    scene.collection.objects.link(ob)
    up = np.array([0, 0, 1.0])
    x = np.cross(up, v); x /= np.linalg.norm(x)
    y = np.cross(v, x)
    ob.matrix_world = [[x[0], y[0], v[0], 0], [x[1], y[1], v[1], 0],
                       [x[2], y[2], v[2], 0], [0, 0, 0, 1]]
    w = bpy.data.worlds.new("TEST_Sky")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = C.SKY_MODEL                     # MULTIPLE_SCATTERING (5.x: no NISHITA)
    sky.sun_elevation = math.radians(C.SUN_ELEV_DEG)
    sky.sun_rotation = math.radians(C.SKY_SUN_ROTATION_DEG)
    sky.altitude = C.SKY_ALTITUDE
    sky.air_density = C.SKY_AIR
    if hasattr(sky, "dust_density"):               # 5.x dropped it; guard anyway
        sky.dust_density = C.SKY_AEROSOL
    for attr, val in (("aerosol_density", C.SKY_AEROSOL),
                      ("ozone_density", C.SKY_OZONE)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    sky.sun_disc = C.SKY_SUN_DISC                  # False: the SUN lamp IS the key
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = C.SKY_STRENGTH
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return ob


def _grey_card(scene, centre, heading, size=0.28, albedo=0.18, offset=0.55, su=False):
    """TEST-ONLY 18 % lambertian card, so a macro crop can be MEASURED, not eyeballed.

    C.lambert_radiance(0.18) = (1.6744, 1.4600, 1.3321).  If the card does not render
    at that linear value under this rig, the rig is wrong; if the tarmac beside it does
    not sit at its intended albedo relative to the card, the MATERIAL is wrong.  That
    is the whole of contract §8 turned into something a pixel probe can answer.
    """
    for n in ("TEST_GreyCard",):
        ob = bpy.data.objects.get(n)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
    m = bpy.data.materials.get("TEST_GreyCardMat") or \
        bpy.data.materials.new("TEST_GreyCardMat")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1.0)
        b.inputs["Roughness"].default_value = 1.0
        b.inputs["Specular IOR Level"].default_value = 0.0
        b.inputs["Metallic"].default_value = 0.0
    ct, st = math.cos(heading), math.sin(heading)
    h = size * 0.5
    # offset to one side of the aim point: a card big enough to measure and centred in
    # frame is a card that hides the material it exists to calibrate.  0.28 m at the
    # macro station is ~340 px of an 85 mm frame, which is plenty to average.
    cx = centre[0] - st * offset
    cy = centre[1] + ct * offset
    pts = []
    for a, bb in ((-h, -h), (h, -h), (h, h), (-h, h)):
        px = cx + a * ct - bb * st
        py = cy + a * st + bb * ct
        if su:
            # ON THE DATUM, corner by corner.  A flat card laid at the aim point's z
            # floats over a crowned road — 50 mm at 4.6 m of lateral, which at a 12.47
            # deg sun throws a 226 mm shadow and turns the calibration reference into
            # the brightest ERROR in frame.  Each corner therefore sits on
            # `C.ground_z` + 4 mm, so the card is a decal on the road, not a tile.
            ss, uu = C.project(np.array([px]), np.array([py]))
            pz = float(C.ground_z(ss, uu)[0]) + 0.004
        else:
            pz = centre[2] + 0.004
        pts.append((px, py, pz))
    me = _new_mesh("TEST_GreyCard", np.array(pts), np.array([[0, 1, 2, 3]]))
    me.materials.append(m)
    scene.collection.objects.link(bpy.data.objects.new("TEST_GreyCard", me))


def _set_lens(cd, lens):
    """`lens` is millimetres, or ("ORTHO", width_m[, roll_rad]) for a plan view."""
    if isinstance(lens, tuple):
        cd.type = 'ORTHO'
        cd.ortho_scale = float(lens[1])
    else:
        cd.type = 'PERSP'
        cd.lens = float(lens)
        cd.sensor_width = 36.0


def _aim(ob, lens, target):
    """Point a camera.  An ORTHO plan view with a roll is aimed straight down and
    rolled so the road runs along frame +X; everything else tracks its target."""
    if isinstance(lens, tuple) and len(lens) > 2:
        ob.rotation_euler = (0.0, 0.0, float(lens[2]))
    else:
        _look_at(ob, target)


def _look_at(ob, target):
    import mathutils
    d = mathutils.Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _test_flat(scene, centre):
    """TEST-ONLY stand-in apron for the shots that are off the circuit centreline
    (the access road).  Spec 2 puts the paddock, the apron and the showroom floor on
    one plane at z = 0, so a flat plane is the right stand-in here - unlike on the
    circuit, where the road is graded and a plane would slice through it."""
    gm = bpy.data.materials.get("TEST_GroundMat") or bpy.data.materials.new("TEST_GroundMat")
    gm.use_nodes = True
    b = gm.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (0.085, 0.083, 0.078, 1.0)
        b.inputs["Roughness"].default_value = 0.90
    R = 260.0
    co = np.array([[centre[0] - R, centre[1] - R, -0.012],
                   [centre[0] + R, centre[1] - R, -0.012],
                   [centre[0] + R, centre[1] + R, -0.012],
                   [centre[0] - R, centre[1] + R, -0.012]])
    me = _new_mesh("TEST_Ground", co, np.array([[0, 1, 2, 3]]))
    me.materials.append(gm)
    scene.collection.objects.link(bpy.data.objects.new("TEST_Ground", me))


def _test_props(scene, station=None, car=True, span=420.0, ds=6.0):
    """TEST-ONLY context.  None of this is created by build().

    `station=None` builds the stand-in ground for the WHOLE LAP, which is what the
    5090 blends use: one ground, several cameras, no per-shot swap and therefore no
    chance of judging two frames against two different stand-ins.

    A flat ground plane does not work: at the doppler station the road is falling at
    -2.82 %, so a plane pinned to the local z rises through the track 100 m away and
    hides the very surface the frame exists to judge.
    """
    for n in ("TEST_Ground", "TEST_CarBox"):
        ob = bpy.data.objects.get(n)
        if ob:
            me_old = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me_old.users == 0:
                bpy.data.meshes.remove(me_old)
    gm = bpy.data.materials.get("TEST_GroundMat") or bpy.data.materials.new("TEST_GroundMat")
    gm.use_nodes = True
    b = gm.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (0.048, 0.052, 0.028, 1.0)
        b.inputs["Roughness"].default_value = 0.96

    if station is None:
        S1 = np.arange(0.0, LAP + ds, ds)
    else:
        S1 = station + np.arange(-span, span + 0.1, ds)
    # THE STAND-IN IS NOW THE CONTRACT'S OWN GROUND, not a guess at it.  It used to be a
    # hand-tuned drop table hung off this module's cross-slope, which is how a test
    # harness ends up validating a road against terrain that no other module builds.
    # Out to C.platform_edge it IS C.ground_z — the same surface build_barriers paves —
    # and only beyond the corridor rim does it batter away into stand-in landscape, at
    # the contract's own CORRIDOR_BATTER_M.
    frac = [0.0, 0.15, 0.35, 0.60, 0.85, 1.00]       # verge_edge -> platform_edge
    beyond = [(8.0, -0.55), (22.0, -1.5), (60.0, -4.0),
              (150.0, -9.5), (340.0, -22.0)]          # rim -> stand-in landscape
    E = C.verge_edge(S1)
    PE = {+1: C.platform_edge(S1, +1), -1: C.platform_edge(S1, -1)}
    ucols, dzcols = [], []
    for sg in (-1, +1):                               # right side first, then left
        seq = ([(f, 0.0) for f in frac] +
               [("out", b) for b in beyond])
        if sg < 0:
            seq = seq[::-1]
        for a, b in seq:
            if a == "out":
                ucols.append(sg * (PE[sg] + b[0])); dzcols.append(np.full_like(S1, b[1]))
            else:
                ucols.append(sg * (E + a * (PE[sg] - E))); dzcols.append(np.zeros_like(S1))
    U = np.stack(ucols, axis=1)
    DZ = np.stack(dzcols, axis=1)
    SS = np.repeat(S1[:, None], U.shape[1], axis=1)
    Z = C.ground_z(SS, U) + DZ
    X, Y, H, _ = _centreline_arrays(SS.ravel())
    X = X.reshape(SS.shape); Y = Y.reshape(SS.shape); H = H.reshape(SS.shape)
    co = np.stack([X - np.sin(H) * U, Y + np.cos(H) * U, Z], axis=-1).reshape(-1, 3)
    nr, nc = SS.shape
    idx = np.arange(nr * nc).reshape(nr, nc)
    # THE TWO SIDES MUST NOT BE JOINED.  The first version of this rewrite emitted one
    # continuous quad strip, which laid a chord from -verge_edge to +verge_edge straight
    # ACROSS the road at the two edge heights.  The road crowns up between them by only
    # 0.10 m, so wherever the undulation or the banking took the chord above the crown
    # the stand-in punched through the tarmac — 30 m-long olive teardrops in the plan
    # view, found by rendering it.  Two disjoint quad blocks, one per side.
    half = nc // 2
    qL = np.stack([idx[:-1, :half - 1], idx[1:, :half - 1],
                   idx[1:, 1:half], idx[:-1, 1:half]], axis=-1).reshape(-1, 4)
    qR = np.stack([idx[:-1, half:-1], idx[1:, half:-1],
                   idx[1:, half + 1:], idx[:-1, half + 1:]], axis=-1).reshape(-1, 4)
    q = np.concatenate([qL, qR], axis=0)
    me = _new_mesh("TEST_Ground", co, q)
    me.materials.append(gm)
    scene.collection.objects.link(bpy.data.objects.new("TEST_Ground", me))

    if not car or station is None:
        return
    _car_box(scene, station)


def _test_old_edge(scene, s0, s1, ds=0.5, lift=0.25):
    """TEST-ONLY overlay: the ground the OLD `_build_width` failed to pave.

    A magenta band from the old road's verge edge out to `C.verge_edge`, floated 0.25 m
    so it reads in a plan view.  `build_barriers` pinned its runoff, its painted verge,
    its advertising boards and its whole barrier line to `C.verge_edge`; `build_surface`
    stopped up to 0.978 m short of it.  This band IS that strip.  In `pit_width_plan.png`
    it now lies entirely on tarmac, which is the frame's whole argument.
    """
    ob = bpy.data.objects.get("TEST_OldEdge")
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
    m = bpy.data.materials.get("TEST_OldEdgeMat") or \
        bpy.data.materials.new("TEST_OldEdgeMat")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.62, 0.03, 0.36, 1.0)
    em.inputs["Strength"].default_value = 4.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])

    S1 = np.arange(s0, s1 + ds, ds)
    e_old = _fsample(_old_build_width(), S1) + KERB_BAND + VERGE_BAND
    e_new = C.verge_edge(S1)
    X, Y, H, _ = _centreline_arrays(S1)
    n = len(S1)
    co, quads = [], []
    for sg in (-1.0, 1.0):
        base = len(co)
        for i in range(n):
            for u in (sg * e_old[i], sg * e_new[i]):
                z = float(C.ground_z(S1[i], u)) + lift
                co.append((X[i] - math.sin(H[i]) * u, Y[i] + math.cos(H[i]) * u, z))
        for i in range(n - 1):
            a = base + i * 2
            quads.append((a, a + 2, a + 3, a + 1))
    me = _new_mesh("TEST_OldEdge", np.array(co), np.array(quads), smooth=False)
    me.materials.append(m)
    scene.collection.objects.link(bpy.data.objects.new("TEST_OldEdge", me))


def _test_apron_neighbour(scene, s0=3298.0, s1=3312.0, inset=0.012, drop=0.300,
                          width=4.0, back=1.6):
    """TEST-ONLY stand-in for `ARCH_Paving_ApronPlatform`, built to its MEASURED
    geometry, so assembly defect #3 can be photographed instead of described.

    `build_apron_platform` lays a regular 2.4 x 3.0 m bay grid whose first column is
    `verge_edge.min()` and then insets every bay by `inset` = 12 mm; under it a closed
    sub-base sits `drop` = 0.300 m down.  Reproducing exactly those two numbers here —
    and nothing else about that module — makes the pair of frames an A/B on ONE
    variable: whether `SURF_ApronJoint` exists.

    With it absent the ray falls 0.300 m between u = 10.500 and u = 10.512.
    With it present the ray lands 5 mm down, in a sealed groove.
    """
    for n in list(bpy.data.objects):
        if n.name.startswith("TEST_ApronNb"):
            bpy.data.objects.remove(n, do_unlink=True)
    m = bpy.data.materials.get("TEST_ApronNbMat") or \
        bpy.data.materials.new("TEST_ApronNbMat")
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value = (0.205, 0.200, 0.190, 1.0)
        bs.inputs["Roughness"].default_value = 0.88
        bs.inputs["Specular IOR Level"].default_value = 0.32
    S1 = np.arange(s0, s1 + 0.25, 0.25)
    n = len(S1)
    E = C.verge_edge(S1)
    co, quads = [], []
    # ... and a strip of TRACK-side stand-in behind the camera's near edge, so the
    # frame is the two real surfaces and the joint between them, nothing else.
    for lvl, (ua, ub, dz) in enumerate(((inset, width, 0.0), (0.0, width, -drop))):
        base = len(co)
        for i in range(n):
            for uu in (E[i] + ua, E[i] + ub):
                x, y, _z, h, _k = C.centreline(float(S1[i]))
                z = float(C.ground_z(float(S1[i]), float(uu))) + dz
                co.append((x - math.sin(h) * uu, y + math.cos(h) * uu, z))
        for i in range(n - 1):
            k = base + i * 2
            quads.append((k, k + 2, k + 3, k + 1))
    me = _new_mesh("TEST_ApronNb", np.array(co), np.array(quads), smooth=False)
    me.materials.append(m)
    scene.collection.objects.link(bpy.data.objects.new("TEST_ApronNb", me))


def _test_glass_marks(scene):
    """TEST-ONLY overlay for `glass_cap_plan`: the three lines the review found three
    different answers for.

      MAGENTA  world x = 12.000 — where `road_corridor_mask` used to cut terrain's
               height field, i.e. 3.0 m INSIDE the showroom (contract 1.0.0)
      AMBER    world x = 14.700 — where build_architecture's `-RIBBON_SAW_M - t` term
               used to cut its paving
      CYAN     world x = 15.000 — `C.ACCESS_GLASS_X`, the breach plane, which is where
               contract 1.0.1 pins `ACCESS_RIBBON_T_MIN` and where this mesh now starts

    In the frame the ribbon's cap edge must land ON the cyan line with nothing between
    them, and the magenta and amber lines must lie on bare ground that belongs to the
    showroom floor, not to this module.
    """
    for n in list(bpy.data.objects):
        if n.name.startswith("TEST_GlassMark"):
            bpy.data.objects.remove(n, do_unlink=True)
    for nm, x, col in (("A", 12.000, (0.62, 0.03, 0.36)),
                       ("B", 14.700, (0.72, 0.36, 0.02)),
                       ("C", 15.000, (0.02, 0.55, 0.62))):
        m = bpy.data.materials.get("TEST_GlassMat_" + nm) or \
            bpy.data.materials.new("TEST_GlassMat_" + nm)
        m.use_nodes = True
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = col + (1.0,)
        em.inputs["Strength"].default_value = 5.0
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], o.inputs["Surface"])
        w = 0.020
        co = np.array([[x - w, -11.0, 0.30], [x + w, -11.0, 0.30],
                       [x + w, +11.0, 0.30], [x - w, +11.0, 0.30]])
        me = _new_mesh("TEST_GlassMark_" + nm, co, np.array([[0, 1, 2, 3]]), smooth=False)
        me.materials.append(m)
        scene.collection.objects.link(
            bpy.data.objects.new("TEST_GlassMark_" + nm, me))


def _car_box(scene, station, name="TEST_CarBox"):
    """A box the exact size of the measured car (5.698 x 2.005 x 0.992, ride 0.340)
    sitting on the racing line, so scale can be read in every frame."""
    ob = bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
    u = float(racing_line_offset(station))
    cx, cy, cz = su_to_world(station, u)
    _x, _y, _z, h, _k = centreline(station)
    L, W, Hh, ride = 5.698, 2.005, 0.992, 0.340
    pts = []
    for sx in (-L * .5, L * .5):
        for sy in (-W * .5, W * .5):
            for sz in (ride, ride + Hh):
                pts.append((sx, sy, sz))
    ct, st = math.cos(h), math.sin(h)
    pts = [(cx + c[0] * ct - c[1] * st, cy + c[0] * st + c[1] * ct, cz + c[2]) for c in pts]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
             (0, 2, 6, 4), (1, 5, 7, 3)]
    bm = bpy.data.meshes.new(name)
    bm.from_pydata(pts, [], faces)
    cm = bpy.data.materials.get("TEST_CarMat") or bpy.data.materials.new("TEST_CarMat")
    cm.use_nodes = True
    bb = cm.node_tree.nodes.get("Principled BSDF")
    if bb:
        bb.inputs["Base Color"].default_value = (0.40, 0.012, 0.020, 1.0)
        bb.inputs["Roughness"].default_value = 0.28
    bm.materials.append(cm)
    scene.collection.objects.link(bpy.data.objects.new(name, bm))


def _scene_settings(scene, res, samples, measure=False):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    # THE FILM'S GRADE, from the contract, not this harness's invention.  These frames
    # used to be shot at -0.85 stops with an 'AgX - Medium High Contrast' look, which is
    # 2.2 stops and a whole tone curve away from what build_sky and the camera rig will
    # actually deliver: contract §8 fixes ONE lens and ONE grade for the film, AgX with
    # Look = None at REFERENCE_EXPOSURE_EXTERIOR.  A material judged under anything else
    # is finding #5 all over again.
    if measure:
        # PHOTOMETRIC MODE.  AgX is a display transform: it compresses the shadows,
        # which is exactly where a 0.03-albedo tarmac lives, so "is the aggregate
        # reading" cannot be answered from an AgX frame — the answer would be a
        # property of the tone curve.  Standard at the same exposure makes the pixel
        # LINEAR REFLECTANCE (a lambertian albedo-a horizontal surface lands on
        # a * 2^REFERENCE_EXPOSURE_EXTERIOR * sum(E)/pi / 1.0, and the 18 % card
        # therefore lands on 0.180 exactly), so a probe render can be measured with
        # arithmetic instead of eyeballed.
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    else:
        scene.view_settings.view_transform = C.VIEW_TRANSFORM
        scene.view_settings.look = C.VIEW_LOOK
        scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR


def _shot_defs():
    """(name, cam_pos, target, lens_mm, stand_in_station, want_car) for every frame."""
    prepare()
    els = {e["tag"]: e for e in _S["els"]}
    s_ap4 = els["T4"]["s0"] + els["T4"]["L"] * 0.5

    def cam_at(st, u, dz, tst, tu, dtz=0.0):
        c = su_to_world(st, u); t = su_to_world(tst, tu)
        return ((c[0], c[1], c[2] + dz), (t[0], t[1], t[2] + dtz))

    # Kerb height on the OUTSIDE of the hairpin, looking ACROSS it at the apex.  Both
    # earlier framings sat inside the 28 m radius, where the infield fills 80 % of the
    # frame whichever way the lens points - a fine composition and a useless surface
    # test.  From the outside of the entry the whole 15 m width lies between the lens
    # and the apex kerb, which is the frame that judges the rubbered band, the crown
    # and the kerb in one go.
    hp = cam_at(s_ap4 - 18.0, -(float(track_half_width(s_ap4 - 18.0)) + 2.2), 0.80,
                s_ap4 + 4.0, float(racing_line_offset(s_ap4 + 4.0)), 0.30)
    st = cam_at(LAP - 120.0, 2.0, 1.35, LAP - 2.0, 0.5, 0.4)
    sw = cam_at(2260.0, -95.0, 55.0, 2300.0, 0.0)
    wd = cam_at(1700.0, -150.0, 95.0, 1760.0, 0.0)
    # off the rubbered band, straddling the track-edge line, so the crop shows
    # aggregate and worn paint rather than a uniform black stripe
    mc = cam_at(3498.2, 6.55, 1.15, 3500.5, 7.15)
    km = cam_at(2178.0, float(track_half_width(2178.0)) + 3.2, 0.55,
                2181.4, float(track_half_width(2181.4)) + 0.75)
    # the negative kerb is where build() actually cut it, not where a fraction of the
    # T8 arc happens to land - the first version aimed 40 m short of the trough and the
    # frame came back showing nothing but horizon.
    nk_a, nk_b, nk_side = _S["neg_kerbs"][0]
    nk_m = 0.5 * (nk_a + nk_b)
    # ACROSS the trough, from the track side.  A 60 mm depression viewed along its own
    # length is invisible; it only reads in profile, and the split it forces in the
    # serrated run only reads from inside the corner.
    nk = cam_at(nk_m - 4.5, nk_side * (float(track_half_width(nk_m)) - 3.2), 1.50,
                nk_m + 0.5, nk_side * (float(track_half_width(nk_m)) + 0.40), -0.03)
    # the doppler frame must show the TARMAC at the closest approach.  Aiming 60 m up
    # the road (the first version) put the surface on the horizon and filled the frame
    # with stand-in ground: the one shot in the film where this material is 26 m from a
    # 50 mm lens has to be judged on the tarmac, not on the vanishing point.
    # Down-road, not across it.  From 2.4 m at 26 m out the tarmac is at a 7 deg
    # grazing angle, so a frame aimed at the closest approach is 80 % stand-in ground
    # and 20 % edge-on road; aimed 50 m up the road it is 50 m of continuous surface,
    # which is what has to survive a 4K pass.
    dp_t = su_to_world(2578.0, float(racing_line_offset(2578.0)))
    dp_t = (dp_t[0], dp_t[1], dp_t[2] + 0.05)
    # the grid: launch rubber, boxes, numerals and the start/finish line, from the
    # height the onboard follow crosses them at 330 km/h
    # Raised and oblique, not on the deck: launch stripes run AWAY from a car-height
    # camera and foreshorten to nothing.  From 9 m at 13 deg they read as stripes.
    gl = cam_at(LAP - 64.0, -10.0, 9.0, LAP - 20.0, 1.0, 0.0)
    # the mu change.  Spec 7 puts the access road at mu 0.90 and 10.5 makes it
    # concrete, so it is a different SURFACE, not a tint - broom finish, saw-cut
    # contraction joints, no rubbered line, and one pair of launch streaks because the
    # car has been down here exactly once.  The camera crosses it in beat 4 and there
    # was no test frame on it at all until this one.
    ax0 = _access_path(6.0); ax1 = _access_path(58.0)
    ar_p = (ax0[0] - 2.0, ax0[1] - 6.5, 3.4)
    ar_t = (ax1[0], ax1[1], 0.15)

    # ---- the three CONTRACT frames -----------------------------------------
    # 1. PIT_EDGE_16M.  s = 3115.0 is where the pit straight opens.  The old
    #    `_build_width` gave half_width(3115) = 7.022; the contract gives 8.000, and
    #    build_barriers had 8.000 all along — so this edge used to fall 0.978 m short
    #    of the ground everyone else built against.  The stand-in platform in
    #    `_test_props` now starts at C.verge_edge EXACTLY, so if this module's road
    #    edge does not reach it the frame shows daylight through the gap.  Low and
    #    along the edge, at the station itself.
    pw_s = 3115.0
    pe = cam_at(pw_s - 34.0, -(float(C.verge_edge(pw_s - 34.0)) - 0.9), 1.15,
                pw_s + 46.0, -(float(C.verge_edge(pw_s + 46.0)) - 0.9), 0.10)
    # 2. MERGE_SEAM.  Route t = 112 m: the ribbon has converged and its inboard edge IS
    #    SURF_Track's painted verge for the next 130 m.  With `C.access_z` this join
    #    stood 48 mm proud here (80 mm at t = 95); built on `C.ground_z` it is 0.000.
    #    A 35 mm lens 1.2 m up, raking along the joint so a millimetre of step would
    #    catch the 12.5 deg sun as a lit line.
    mx0, my0, mh0 = C.access_route_point(104.0)
    mx1, my1, mh1 = C.access_route_point(150.0)
    v0, _ = C.access_edges(np.array([104.0])); v0 = float(v0[0])
    v1, _ = C.access_edges(np.array([150.0])); v1 = float(v1[0])
    ms_p = (mx0 - math.sin(mh0) * (v0 - 1.6), my0 + math.cos(mh0) * (v0 - 1.6), 1.20)
    ms_t = (mx1 - math.sin(mh1) * v1, my1 + math.cos(mh1) * v1, -0.10)
    # 3. APRON_FLAT.  Down the 49.60 m apron run from just outside the glass, at the
    #    height Beat 4's camera clears the breach.  spec §10.3(b) demands exactly 0 %
    #    and exactly level with the showroom floor; this frame is where a crown would
    #    show, and where the new pit-exit lane markings live.
    af_p = (C.ACCESS_GLASS_X + 1.5, -3.2, 2.60)
    af_t = (C.ACCESS_GLASS_X + 62.0, 3.0, 0.00)
    # 4. PIT_WIDTH_PLAN.  The same defect the contract author photographed as a magenta
    #    band, seen from directly overhead in TRUE SCALE across the s = 3115 boundary.
    #    The stand-in platform starts at C.verge_edge and is a different material, so
    #    the road edge and the platform edge are a hard colour boundary: if this
    #    module's half_width were still 0.978 m short the olive would run 0.978 m into
    #    where the tarmac belongs, on both sides, for 46 m of frame.
    pl_s = 3090.0                       # centred on the 3055 -> 3115 transition band
    pl_c = su_to_world(pl_s, 0.0)
    _plx, _ply, _plz, pl_h, _plk = centreline(pl_s)
    pw_plan_p = (pl_c[0], pl_c[1], pl_c[2] + 90.0)
    pw_plan_t = (pl_c[0], pl_c[1], pl_c[2])
    pw_plan_lens = ("ORTHO", 82.0, pl_h)

    # 5. ALBEDO_PROBE.  A true-scale plan view of 12.0 m of the pit straight with the
    #    18 % card in frame, rendered with view_transform = Standard so the pixel IS
    #    linear reflectance.  This is the only frame in the module that can answer
    #    "what albedo is this tarmac and does the aggregate have any contrast" with a
    #    number rather than an opinion.  s = 3500 is 175 m before the line: rubbered
    #    band, clean tarmac either side of it, the track-edge line, and a lane joint.
    ap_s = 3500.0
    ap_c = su_to_world(ap_s, 0.0)
    _apx, _apy, _apz, ap_h, _apk = centreline(ap_s)
    ap_p = (ap_c[0], ap_c[1], ap_c[2] + 40.0)
    ap_t = (ap_c[0], ap_c[1], ap_c[2])
    # rolled 90 deg from the road heading, so the 12.0 m ortho width runs ACROSS the
    # track (u -6..+6) and the calibration card at u = +4.6 is inside the frame.
    ap_lens = ("ORTHO", 12.0, ap_h + math.pi * 0.5)
    # 6. RAKE_LOW.  The grazing-sun frame: 0.60 m off the deck, looking down the
    #    12.47 deg sun's own azimuth, which is where surface relief either exists or
    #    is revealed as a painted-on texture.
    rk = cam_at(3560.0, 3.2, 0.60, 3470.0, 1.2, 0.10)

    # 7. APRON_JOINT_RAKE.  Assembly defect #3, in the one condition that showed it: a
    #    35 mm lens 0.35 m off the deck, looking 90 m down the pit-exit apron edge with
    #    the 12.47 deg sun raking along the joint.  A 12 mm wide, 300 mm deep slot reads
    #    as a black line here; a 12 mm wide, 5 mm deep sealed groove does not.
    aj_s = 3260.0
    aj_p = su_to_world(aj_s, float(C.verge_edge(aj_s)) - 1.10)
    aj_t = su_to_world(aj_s + 92.0, float(C.verge_edge(aj_s + 92.0)) + 0.02)
    aj = ((aj_p[0], aj_p[1], aj_p[2] + 0.35), (aj_t[0], aj_t[1], aj_t[2] + 0.02))
    # 8. GLASS_CAP_PLAN.  Assembly defect #2, in true-scale plan: 24 m of the corridor
    #    mouth from directly overhead, with the three disputed cut lines drawn.
    gc_p = (C.ACCESS_GLASS_X + 5.0, 0.0, 34.0)
    gc_t = (C.ACCESS_GLASS_X + 5.0, 0.0, 0.0)

    # 9. APRON_JOINT_MACRO.  The A/B frame for defect #3: an 85 mm lens 1.05 m from the
    #    joint and 0.30 m above it, against a stand-in built to build_architecture's
    #    MEASURED bay inset (12 mm) and sub-base drop (0.300 m).  0.44 m of frame at
    #    4K = 0.11 mm/px, so the 12 mm joint is 105 px wide and there is nowhere to
    #    hide.  Rendered twice: `--blend=joint` and `--blend=jointoff`.
    # ACROSS the joint, not along it.  The first framing sat 0.30 m up at 1.05 m and
    # looked 16 deg down the edge; at that incidence a 5 mm groove and a 300 mm slot
    # are the same soft diagonal and the frame settles nothing.  0.55 m up, 0.90 m
    # inboard, 50 mm: the surface is at 28 deg, both sides are in frame, and the ray
    # can reach the bottom of whatever is there.
    jm_s = 3304.0
    jm_c = su_to_world(jm_s + 0.05, float(C.verge_edge(jm_s + 0.05)) + 0.30)
    jm_p = su_to_world(jm_s - 0.35, float(C.verge_edge(jm_s - 0.35)) - 0.60)
    jm = ((jm_p[0], jm_p[1], jm_p[2] + 0.75), (jm_c[0], jm_c[1], jm_c[2] - 0.004))

    return [
        ("doppler_pass", (-578.82, -47.47, 4.802), dp_t, 85.0, 2555.0, True),
        ("apron_joint_macro", jm[0], jm[1], 50.0, jm_s, False),
        ("apron_joint_rake", aj[0], aj[1], 35.0, aj_s + 40.0, False),
        ("glass_cap_plan", gc_p, gc_t, ("ORTHO", 24.0, 0.0), None, False),
        ("albedo_probe", ap_p, ap_t, ap_lens, ap_s, False),
        ("rake_low", rk[0], rk[1], 50.0, 3520.0, False),
        ("hairpin_kerb", hp[0], hp[1], 21.0, s_ap4 - 14.0, True),
        ("straight_low", st[0], st[1], 35.0, LAP - 34.0, True),
        ("sweeper_air", sw[0], sw[1], 40.0, 2300.0, True),
        ("wide_repeat_check", wd[0], wd[1], 24.0, 1760.0, True),
        ("macro_asphalt", mc[0], mc[1], 85.0, 3500.0, True),
        ("kerb_macro", km[0], km[1], 85.0, 2181.0, True),
        ("negative_kerb", nk[0], nk[1], 35.0, nk_m, False),   # car box sat in the trough
        ("grid_launch", gl[0], gl[1], 40.0, LAP - 30.0, False),
        ("access_road", ar_p, ar_t, 28.0, None, False),
        ("pit_edge_16m", pe[0], pe[1], 35.0, pw_s + 6.0, False),
        ("merge_seam", ms_p, ms_t, 35.0, 3420.0, False),
        ("apron_flat", af_p, af_t, 24.0, None, False),
        ("pit_width_plan", pw_plan_p, pw_plan_t, pw_plan_lens, pw_s, False),
    ]


# the frames grouped into 5090 blends.  The worker PREWARMS EVERY CAMERA in a blend at
# load (~4 s each) and 19 of them blew a readiness probe and destroyed an instance, so
# these are deliberately small.  Grouping is by what the frame is FOR, not by locality.
BLEND_GROUPS = {
    "contract": ["pit_edge_16m", "merge_seam", "apron_flat", "pit_width_plan"],
    "ribbon": ["access_road"],
    "surface": ["doppler_pass", "straight_low", "sweeper_air", "wide_repeat_check"],
    "macro": ["macro_asphalt", "kerb_macro", "hairpin_kerb", "negative_kerb",
              "grid_launch"],
    "probe": ["albedo_probe", "macro_asphalt"],
    "rake": ["rake_low", "access_road"],
    "defects": ["apron_joint_rake", "glass_cap_plan", "merge_seam", "apron_flat"],
    "joint": ["apron_joint_macro"],
    "jointoff": ["apron_joint_macro"],       # ... with SURF_ApronJoint deleted
}
MEASURE_GROUPS = {"probe"}          # rendered photometric (Standard), not AgX


def make_test_blend(group, path, res=(3840, 2160), samples=512):
    """Write a .blend carrying the whole-lap stand-in ground and the group's cameras.

    The 5090 worker renders one named camera per job, so every camera in a group sees
    exactly the same world — which is the point.  The old harness rebuilt the stand-in
    ground per shot, so two frames could disagree about the ground and neither would
    show it.
    """
    prepare()
    scene = bpy.context.scene
    _scene_settings(scene, res, samples, measure=(group in MEASURE_GROUPS))
    scene.cycles.device = 'GPU'
    _mk_sun(scene)
    _test_props(scene, None)                 # ONE ground, the whole lap, C.ground_z
    names = BLEND_GROUPS[group]
    defs = {d[0]: d for d in _shot_defs()}
    made = []
    for nm in names:
        _name, pos, tgt, lens, station, want_car = defs[nm]
        cd = bpy.data.cameras.new("CAM_" + nm)
        _set_lens(cd, lens)
        ob = bpy.data.objects.new("CAM_" + nm, cd)
        scene.collection.objects.link(ob)
        ob.location = pos
        _aim(ob, lens, tgt)
        made.append(ob.name)
        if nm == "pit_width_plan":
            _test_old_edge(scene, 3040.0, 3140.0)
        if nm == "glass_cap_plan":
            _test_glass_marks(scene)
        if nm == "apron_joint_macro":
            # THE WHOLE-LAP STAND-IN HAS TO GO FOR THIS ONE.  `_test_props` lays the
            # contract's own ground from `verge_edge` outward, which is coplanar with
            # both the joint and the neighbour stand-in and buries the thing the frame
            # exists to photograph — and puts 100 m of receding olive behind it.
            for _n in ("TEST_Ground",):
                _o = bpy.data.objects.get(_n)
                if _o:
                    bpy.data.objects.remove(_o, do_unlink=True)
            _test_apron_neighbour(scene)
            if group == "jointoff":
                ob0 = bpy.data.objects.get(PFX + "ApronJoint")
                if ob0:
                    bpy.data.objects.remove(ob0, do_unlink=True)
        if want_car and station is not None and group not in MEASURE_GROUPS:
            # A MEASUREMENT FRAME CONTAINS ONLY THE THING BEING MEASURED.  The car box
            # belonging to another camera in the same blend put a 5.7 m red box and its
            # blue sky-lit shadow across a third of the calibration frame, and every
            # number came back contaminated.
            _car_box(scene, station, "TEST_CarBox_" + nm)
        if nm in ("macro_asphalt", "kerb_macro"):
            _grey_card(scene, tgt, math.atan2(tgt[1] - pos[1], tgt[0] - pos[0]))
            bpy.data.objects["TEST_GreyCard"].name = "TEST_GreyCard_" + nm
        if nm == "albedo_probe":
            # 1.00 m at 12.0 m of ortho width on a 3840 px frame = 320 px of card,
            # parked 4.6 m off the centreline where there is no rubber and no paint.
            _grey_card(scene, tgt, lens[2] - math.pi * 0.5, size=1.00, albedo=0.18,
                       offset=4.60, su=True)
            bpy.data.objects["TEST_GreyCard"].name = "TEST_GreyCard_" + nm
    scene.camera = bpy.data.objects[made[0]]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("  wrote %s  cameras=%s" % (path, made))
    return made


def render_tests(res=(1280, 720), samples=96, only=None):
    """LOCAL render of the surface test frames (GTX 1070).  `only` is a set of shot
    names.  The 5090 path is `make_test_blend` + tools/r5090, which is what the
    published frames come from; this exists for fast iteration."""
    prepare()
    os.makedirs(RENDER_DIR, exist_ok=True)
    scene = bpy.context.scene
    _scene_settings(scene, res, samples)
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = (dv.type == 'CUDA')
        scene.cycles.device = 'GPU'
    except Exception as exc:
        print("  ! GPU unavailable, CPU render:", exc)

    _mk_sun(scene)
    cam_d = bpy.data.cameras.new("TEST_Cam")
    cam = bpy.data.objects.new("TEST_Cam", cam_d)
    scene.collection.objects.link(cam)
    scene.camera = cam

    written = []
    for name, pos, tgt, lens, station, want_car in _shot_defs():
        if only and name not in only:
            continue
        note = _SHOT_NOTES[name]
        for n in ("TEST_Ground", "TEST_CarBox", "TEST_GreyCard", "TEST_OldEdge"):
            ob = bpy.data.objects.get(n)
            if ob:
                bpy.data.objects.remove(ob, do_unlink=True)
        if name == "pit_width_plan":
            _test_old_edge(scene, 3040.0, 3140.0)
        if station is not None:
            _test_props(scene, station, car=want_car)
        else:
            _test_flat(scene, tgt)
        if name in ("macro_asphalt", "kerb_macro"):
            # an 18 % lambertian card in frame turns "does this look like asphalt"
            # into "is the tarmac 0.055 +- of the card", which is a measurement.
            _grey_card(scene, (tgt[0], tgt[1], tgt[2]), math.atan2(tgt[1] - pos[1],
                                                                   tgt[0] - pos[0]))
        cam.location = pos
        _set_lens(cam_d, lens)
        _aim(cam, lens, tgt)
        scene.render.filepath = os.path.join(RENDER_DIR, name + ".png")
        print("  render %-18s lens %-8s %s" % (name, lens, note))
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print("       %.1f s" % (time.time() - t0))
        written.append(scene.render.filepath)
    return written


# ============================================================================
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    s = build()
    print("\n=== build_surface ===")
    for k, v in s.items():
        if k == "contract":
            continue
        print("  %-26s %s" % (k, v))
    print("\n=== world_contract conformance (v%s) ===" % C.__version__)
    for k in sorted(s["contract"]):
        print("  %-42s %s" % (k, s["contract"][k]))
    if "--verify" in argv:
        import json as _json
        os.makedirs(RENDER_DIR, exist_ok=True)
        p = os.path.join(RENDER_DIR, "contract_conformance.json")
        with open(p, "w") as f:
            _json.dump(s["contract"], f, indent=2, default=float)
        print("  wrote", p)
    for a in argv:
        if a.startswith("--blend="):
            grp = a.split("=", 1)[1]
            make_test_blend(grp, os.path.join(_HERE, "surface_test_%s.blend" % grp))
            return s
    if "--render" in argv:
        only = None
        for a in argv:
            if a.startswith("--only="):
                only = set(a.split("=", 1)[1].split(","))
        for p in render_tests(only=only):
            print("  wrote", p)
    if "--save" in argv:
        # Drop the factory-startup Cube/Camera/Light before saving.  They are not this
        # module's geometry, and leaving them in made `tools/placement_gate.py` report
        # `Cube` in the car's driven path — a real failure, of a default object, in the
        # one blend that exists to prove this module puts nothing on the road.
        for ob in list(bpy.data.objects):
            if not ob.name.startswith(PFX):
                bpy.data.objects.remove(ob, do_unlink=True)
        out = os.path.join(_HERE, "surface_only.blend")
        bpy.ops.wm.save_as_mainfile(filepath=out)
        print("  saved", out, "objects=%d" % len(bpy.data.objects))
    return s


if __name__ == "__main__":
    main()
