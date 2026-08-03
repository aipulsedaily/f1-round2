#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
world_contract.py — CIRCUIT VITRINE: the integration contract.

THE SINGLE SOURCE OF TRUTH for everything two or more modules must agree on.

This module exists because six builders each verified their own work in isolation
and the assembled world was broken: three incompatible ground datums, a coplanar
z-fight down the whole of Beat 4, the Beat-4 corridor built twice 0.5 m apart, and
three different answers for the width of the main straight.  Every one of those is
a *shared* quantity that nobody owned.  This file owns them.

    RULE 1.  If two modules need the same number, it is defined HERE and nowhere
             else.  You import it.  You do not reimplement it, you do not
             re-derive it from circuit_spec.json, and you do not "match" it.
    RULE 2.  This module imports nothing but the standard library and numpy.
             No bpy.  It must be runnable as  `python3 world_contract.py --selftest`
             from a bare shell, and importable from inside Blender by every builder.
    RULE 3.  Nothing in here is a suggestion.  A module that disagrees with the
             contract is the thing that is wrong, including build_surface, which is
             merely where most of the datum came from.

    Contract version 1.0.0.  Read WORLD_CONTRACT.md beside this file for WHY each
    decision went the way it did, and for the mapping from the five review findings
    to the contract element that prevents each one.

-------------------------------------------------------------------------------
THE FIVE HEADLINE OBLIGATIONS
-------------------------------------------------------------------------------
  1. GROUND.        `ground_z(s, u)` is THE ground datum for the whole 3675 m lap
                    corridor.  It carries crown, banking, undulation, negative
                    kerbs, the verge drain AND the outward runoff fall.  Nobody
                    computes ground height from the centreline elevation.

  2. WIDTH.         `half_width(s)`.  Spec §9, LINEAR over 60 m, transition lying
                    OUTSIDE the named section.  half_width(3115) = half_width(250)
                    = 8.000 exactly.

  3. CORRIDOR.      `road_corridor_mask()` / `platform_edge()`.  The terrain module
                    CUTS a hole; it does not blend.  The road programme owns every
                    square metre inside `platform_edge(s, side)`.

  4. BEAT 4.        `CORRIDOR_OWNER`, `ACCESS_RIBBON_*`.  One walled corridor, built
                    by build_barriers.  One access ribbon, built by build_surface,
                    with architecture cutting its paving to
                    `access_ribbon_polygon()`.

  5. LIGHT.         `SUN_*`, `SKY_*`, `REFERENCE_EXPOSURE_EXTERIOR`,
                    `lambert_radiance()`.  build_sky is the physical light and it
                    wins.  Material calibration references these numbers.

-------------------------------------------------------------------------------
COORDINATE AND SIGN CONVENTIONS — READ THIS BEFORE ANYTHING ELSE
-------------------------------------------------------------------------------
  world frame    +X east, +Y north, +Z up.  Origin = round-1 showroom floor centre.
                 z = 0.000 is the showroom finished floor AND the pit-straight
                 racing surface at the start/finish line.  ALL geometry ships in
                 this frame.

  circuit frame  a.k.a. the "design frame".  The pit straight runs along +x with
                 the centreline on y = 0.  world = Rz(40 deg) * (circuit - (-350, 72))
                 + (15, 0).  Use `circuit_to_world` / `world_to_circuit`.

  s              lap station in metres, 0 <= s < 3675.0, measured along the
                 centreline from the start/finish line in the racing direction
                 (counter-clockwise).  Cyclic: every function here takes s % LAP.

  u              SIGNED lateral offset in metres from the centreline,
                 **POSITIVE TO THE LEFT OF THE DIRECTION OF TRAVEL**.

                 THIS IS THE ONE THAT BIT US.  build_barriers and build_dressing
                 speak (lat, side) with lat >= 0 and side = +1 left / -1 right.
                 A datum expressed in |lat| CANNOT carry banking, because banking
                 is antisymmetric in u — which is exactly why the old
                 build_barriers.ground_z had no banking and sat 0.68 m out at
                 T10/T11.  Every function here that takes a lateral takes signed u.
                 For the (lat, side) callers, every such function also accepts an
                 optional `side` argument: pass it and the lateral is treated as an
                 unsigned distance and multiplied by `side`.  So

                     ground_z(s, lat, side)      ==  ground_z(s, side * lat)

                 is a drop-in replacement for the old barriers signature.

  side           +1 = LEFT of travel, -1 = RIGHT of travel.  A corner with
                 turn_deg > 0 turns left, so its OUTSIDE is side = -1.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import sys

import numpy as np

__version__ = "1.2.1"
# 1.2.1  PROSE ONLY.  NOT ONE VALUE MOVES — verified by evaluating every public
#        function of 1.2.0 and 1.2.1 on the same inputs and requiring bit-identical
#        output.  The v1.2.0 D1 note and S10c below both claimed the driven-line
#        polyline "reproduces telemetry.csv's own x, y to 1.0e-4 m".  That was TRUE
#        WHEN WRITTEN and is now FALSE, in the good direction: it described the
#        CHORD, and R2-042 has since made `tools/build_telemetry.py` evaluate the
#        transit merge as the declared R150 / 40 deg arc.  The artefact now
#        reproduces the ROUTE to 8.83e-05 m and stands 9.0407 m off the chord
#        (selftest [18], which was inverted with R2-042's one permitted edit to
#        this file).  The claim is re-worded where it appears, S10c's "this is not
#        decided yet" framing is retired, and its pointer to `build_barriers` S21 is
#        updated: S21 has been DELETED, having been measured a no-op (north-wall
#        push +3.347 m -> 0.000 m) once the two curves agreed.
#
# 1.2.0  THREE DEFECTS, BATCHED because the world assembly is a 4.19 GB remote job
#        and a contract change moves no vertex until it is rebuilt.  R2-042, R2-043,
#        R2-044 in DEFECT-LOG-R2.md.
#
#        D1  THE CONTRACT AND THE TELEMETRY DISAGREED ABOUT WHERE THE CAR DRIVES,
#            BY UP TO 9.044 m.  `access_route_point` merges on the declared R150 /
#            40 deg arc; `tools/build_telemetry.py` integrates the SAME merge from
#            `SPEC["transit"]["legs"]` as a STRAIGHT CHORD between the leg
#            endpoints, and a 104.7 m arc of R150 stands 9.04 m off its own chord.
#            MEASURED, telemetry.csv re-projected onto `access_route_arrays`:
#            max |v| 9.0442 m at route t = 101.9, and the car's SWEPT BOX runs up
#            to 4.647 m OUTBOARD of the ribbon's own declared edge over 60.1 m of
#            the transit.  Every keep-out this file published was derived from the
#            ribbon; the placement gate measures the TELEMETRY.  That is how
#            `ARCH_PitWall` (1.067 m) and `ARCH_RetainEdge` (1.198 m, then 1.526 m)
#            came to be inside the car body at 200+ km/h, and it is why v1.1.1's
#            #46 fix cleared them BY LUCK rather than by construction.
#
#            THE FIX IS RULE 1.  The driven line is now DERIVED HERE, from the same
#            `SPEC["transit"]["legs"]` block build_telemetry integrates — so the
#            contract and the telemetry solver share ONE curve without this file
#            reading a CSV (RULE 2).  WHEN WRITTEN, that polyline reproduced
#            telemetry.csv's own x, y to **1.0e-4 m** over all 219 transit frames,
#            because the CSV was built on the same chord.  SINCE R2-042 IT NO
#            LONGER DOES, AND MUST NOT: the CSV drives the declared arc, which
#            `access_route_arrays` reproduces to **8.83e-05 m**, and this chord
#            polyline now stands **9.0407 m** away from it.  See the v1.2.1 note
#            above and selftest [18].  `transit_keepout()` is now
#            the UNION of the declared ribbon and the driven swept car box, which
#            is the correct keep-out under BOTH readings of which curve is right.
#            NEW: `transit_drive_point/arrays/project`, `transit_drive_keepout`,
#            `TRANSIT_DRIVE_*`, `CAR_*`.
#            `PIT_WALL_S0` DOES NOT MOVE (3447.7092): the ribbon's crossing at
#            3447.709 is later than the driven box's at 3446.007, so the union is
#            the ribbon's.  Nothing on the pit straight rebuilds for D1.
#
#        D2  THE CIRCUIT CROSSES ITS OWN CORRIDOR  (R2-035, open since v1.0.1).
#            `barrier_offset` was a pure function of (s, side) and could not know
#            another LEG of the same track was in the way.  Swept into world space
#            and re-projected: **406 of 14 700 stations (2.76 %)** of the declared
#            barrier face on side +1 landed inside ANOTHER leg's road corridor,
#            worst **7.493 m** at s = 786 landing on the s = 1182.4 leg's
#            CENTRELINE.  v1.1.0 "improved" 3.56 % -> 2.76 % without touching the
#            worst case: the rate cap moved the COUNT, not the INTRUSION.
#            `build_barriers` S4b had carried a private clamp for this since the
#            T4 Armco wall, and handed the defect back.
#
#            `owned_edge(s, side)` is promoted INTO the contract (S9b) and
#            `barrier_offset` is clamped by it.  MEASURED AFTER: **0 of 14 700**
#            on both sides, and S4b's clamp now activates on **0.00 %** of the lap.
#            `barrier_offset_declared()` publishes the pre-ownership line so the
#            two can always be diffed.
#              * `barrier_offset(s, +1)`  -44.598 m .. 0.000, rms 8.110, over
#                s 661-884 and 1081-1213 (9.76 % of stations); side -1 IDENTICAL
#              * `platform_edge(s, +1)`    -2.460 m .. 0.000, rms 0.671 (the runoff
#                programme, not the barrier, sets it over that stretch)
#              * `corridor_rim`, and terrain's weld ring with it, over the same span
#              * `rim_buildable` is False beyond ownership as well as in the transit
#                keep-out: it used to say BUILDABLE at 30 stations where the rim sits
#                inside the car's swept path by up to 1.481 m.
#            `ground_z`, `half_width`, `runoff_edge`, `apron_zone`, `access_*`,
#            every light and every tolerance are BIT-IDENTICAL to 1.1.1.
#
#        D3  RULE 1 SWEEP.  `build_barriers.BARRIER_BREAK_RATE` was a private 2.00
#            against this file's 1.95 — a strict `>` test that could never fire on
#            a line the contract calls continuous, so the break detector was dead.
#            It, `BARRIER_TAPER_MAX`, `CLAMP_BLEND_M`, `BARRIER_MIN_CLEAR_M`,
#            `CORRIDOR_BIAS` and the car box all come from here now.
#
#        COST: the ownership solve is 239 k projections and adds ~4.2 s to import.
#        It is EAGER on purpose — a lazy cap is a second answer waiting to happen.
#
# 1.1.1  THE PIT WALL STOOD IN THE BEAT-4 TRANSIT LANE and the contract put it
#        there.  DEFECT #46, measured at 1.067 m inside the car's swept volume with
#        the car doing 207.0 km/h, plus `ARCH_RetainEdge` at 1.198 m on the same
#        50 m of road.  Both come from ONE line of this file: `s_lp0` pinned
#        `barrier_offset(s, +1)` to `PIT_WALL_Y` from the declared garage frontage
#        (s = 3430.0) while the pit-exit road does not come inboard of that line
#        until s = 3447.73.  See §10a for the derivation and §9's TRANSIT KEEP-OUT
#        for the second object.
#
#        WHAT MOVES.  `PIT_WALL_S0` is now DERIVED from `access_edges` instead of
#        from `GARAGE_X0`, and the open pit-exit apron runs up to it, so:
#          * `barrier_offset(s, +1)`  s 3385-3493: up to +11.62 m outboard
#          * `platform_edge(s, +1)`   the same stretch, and the rim with it
#          * `apron_zone(s, +1)`      1.000 over 17.7 m more of pit straight
#          * `ground_z`               the apron tie follows `apron_zone`
#          * `barrier_type(s, +1)`    B_NONE instead of B_CONCRETE over s 3430-3448
#        Every baked mesh on the pit straight rebuilds.  Nowhere else on the lap
#        changes by so much as a float ulp — asserted in selftest [14c].
#
#        NEW PUBLIC SURFACE: `PIT_WALL_S0`, `PIT_WALL_X0`, `PIT_WALL_TERMINAL_M`,
#        `PIT_WALL_TERMINAL_FLARE_M`, `pit_wall_span()`, `pit_wall_face()`,
#        `TRANSIT_KEEPOUT_M`, `transit_keepout()`, `rim_buildable()`.
#
# 1.1.0  FOUR DEFECTS CLOSED, and a CONTINUITY GATE added so the first of them cannot
#        come back.  See WORLD_CONTRACT.md and DEFECT-LOG-R2.md R2-031..R2-034.
#
#        D1  `barrier_offset` stepped up to 51.99 m IN ONE METRE.  TWO independent
#            mechanisms, not one (§8):
#              (a) `_Corridor.maxoff` used 1e6 as its "no geometric cap" sentinel and
#                  then BOX-FILTERED it.  A box filter over a field containing 1e6 is
#                  not a smoother: one sentinel left in a 41-sample window gives
#                  1e6/41 = 24 390, so the cap flipped from "no cap" to 14.0 m in a
#                  single sample.  That is the 51.99 m at s = 904 (+1), the 21.40 m at
#                  s = 1060 (+1), 15.26 at 1743 (-1), 9.38 at 1819 (-1), 8.64 at
#                  2665 (+1).  The sentinel is now finite, the box filter is gone, and
#                  the published line is CONE-ERODED so it is provably Lipschitz.
#              (b) the pit-straight overrides were hard boolean-mask assignments with
#                  no ramp, so grass/asphalt/gravel switched branch in one sample at
#                  every mask edge.  That is the 46.31 m at s = 250 (-1) and the
#                  15.69 m at s = 3114 (-1).  They are now `_ramp`-weighted blends on
#                  the same ramp the RUNOFF_ZONES use.
#            `barrier_offset` is now 2.00-Lipschitz BY CONSTRUCTION, asserted at 0.25 m
#            over the whole lap on both sides in `selftest()` §12.
#
#        D2  `_undulation` evaluated value noise on RAW `s`, whose noise lattice does
#            not contain a whole number of cells per lap, so THE DATUM did not close on
#            itself: 6.75 mm of step across the start/finish line.  The noise now runs
#            on an integer number of cells per lap and wraps its lattice index, so
#            `ground_z(0, u) == ground_z(LAP, u)` to float64 round-off.
#
#        D3  `access_z` disagreed with `ground_z` by up to 90.2 mm on the Beat-4 ribbon
#            — 9x TOL_SEAM_M, on an edge two modules share.  `build_surface` had
#            already routed around it (build_surface.md §5.4).  `access_z` IS
#            `ground_z` now; it is kept only as a named alias for its nine callers.
#
#        D4  APRON_JOINT_LAP_M and APRON_JOINT_DEPTH_M were read by build_surface AND
#            build_architecture as `getattr(C, name, default)` and agreed only because
#            they shared a fallback.  RULE 1 says they live here.  They do.
#
# 1.0.1  in_access_ribbon's start cap is pinned at ACCESS_RIBBON_T_MIN = 0.0 (the glass
#        plane, world x = 15.000) instead of `-margin`.  Three modules were using three
#        different margins for the SAME boundary and 64 m2 of the Beat-3 -> Beat-4 hinge
#        had no ground at all.  See in_access_ribbon's docstring.  Nothing else moves:
#        world_ground_z already called it with margin = 0, so no ownership changes.

__all__ = [
    # frames
    "LAP", "PIVOT_DESIGN", "PIVOT_WORLD", "ROT_DEG",
    "world_to_circuit", "circuit_to_world",
    # centreline
    "centreline", "centreline_arrays", "project", "su_to_world", "world_su",
    "elevation_c",
    # section
    "half_width", "verge_edge", "kerb_top_z", "micro_window",
    "KERB_W", "VERGE_W", "KERB_LIP_INNER_M", "KERB_LIP_OUTER_M",
    "KERB_SERRATION_AMP_M", "KERB_SERRATION_PITCH_M",
    "NEG_KERB_DEPTH_M", "NEG_KERB_W", "NEG_KERBS",
    "PIT_STRAIGHT_W", "STANDARD_W", "HAIRPIN_W", "ESSES_W", "ACCESS_ROAD_W",
    "TRANSITION_LEN", "CROWN_FALL",
    # datum
    "ground_z", "world_ground_z", "PLATFORM_FALL", "VERGE_DRAIN_M",
    "MICRO_LAYER_MAX_M", "BASE_EMBED_M",
    # runoff programme
    "runoff_widths", "runoff_edge", "barrier_offset", "platform_edge",
    "barrier_type", "fence_allowed", "apron_zone", "platform_owner",
    "B_ARMCO", "B_TECPRO3", "B_CONCRETE", "B_NONE",
    "BARRIER_JITTER_MAX_M", "RUNOFF_ZONES", "APEX_BEDS",
    "PIT_WALL_Y", "PIT_SOUTH_BARRIER_Y",
    "PIT_WALL_S0", "PIT_WALL_X0", "PIT_WALL_TERMINAL_M",
    "PIT_WALL_TERMINAL_FLARE_M", "pit_wall_span", "pit_wall_face",
    "TRANSIT_KEEPOUT_M", "transit_keepout", "rim_buildable",
    "BARRIER_MAX_LATERAL_RATE", "BARRIER_BREAK_RATE", "RATE_EPS",
    "CORRIDOR_SMOOTH_K_M",
    "PIT_OVERRIDE_RAMP_M", "MAXOFF_NONE_M", "MAXOFF_REACH_M",
    # ownership  (v1.2.0, R2-035)
    "owned_edge", "barrier_offset_declared", "ownership_report",
    "CORRIDOR_BIAS_M", "BARRIER_TAPER_MAX_RATE", "OWNERSHIP_BLEND_M",
    "BARRIER_MIN_CLEAR_M", "OWNED_SOLVE_DS_M", "OWNED_SOLVE_NT",
    "OWNED_SELF_WINDOW_M", "OWNED_SELF_U_TOL_M",
    # the driven transit line and the car box  (v1.2.0)
    "TRANSIT_DRIVE_NODES", "TRANSIT_DRIVE_CUM_M", "TRANSIT_DRIVE_LEN_M",
    "transit_drive_point", "transit_drive_arrays", "transit_drive_project",
    "transit_drive_keepout", "TRANSIT_DRIVE_CLEAR_M",
    "CAR_BODY_LEN_M", "CAR_BODY_W_M", "CAR_BODY_H_M", "CAR_BODY_HALF_W_M",
    "CAR_RIDE_HEIGHT_M", "CAR_CLEARANCE_M", "CAR_SWEPT_HALF_W_M",
    "CAR_SWEPT_PAD_M",
    # corridor
    "road_corridor_mask", "corridor_rim", "corridor_rim_polyline",
    "CORRIDOR_BATTER_M", "PLATFORM_MARGIN_M", "PLATFORM_MARGIN_WALL_M",
    # transit / beat 4
    "access_route_point", "access_route_arrays", "access_edges", "access_z",
    "access_ribbon_polygon", "in_access_ribbon", "access_project",
    "ACCESS_CORRIDOR_MARGIN_M", "ACCESS_RIBBON_T_MIN", "ACCESS_RIBBON_SAW_M",
    "CORRIDOR_OWNER", "CORRIDOR_DELETE_NAMES",
    "TRANSIT_WALL_S0", "TRANSIT_WALL_S1", "TRANSIT_NORTH_S1", "TRANSIT_SOUTH_S1",
    "TRANSIT_NORTH_OFFSET_M", "TRANSIT_SOUTH_OFFSET_M",
    "TRANSIT_NORTH_TOP_Z", "TRANSIT_SOUTH_TOP_Z", "TRANSIT_PORTAL_X",
    "transit_wall_span", "transit_wall_point", "FORECOURT_BOLLARD_X",
    "ACCESS_L1", "ACCESS_L2", "ACCESS_L3", "ACCESS_MERGE", "ACCESS_BLEND",
    "ACCESS_TOTAL", "ACCESS_HALF_W", "ACCESS_R", "ACCESS_GLASS_X",
    "ACCESS_MERGE_LATERAL",
    # apron
    "APRON_Z", "APRON_TIE_M", "apron_platform_mask", "APRON_REGIONS_CIRCUIT",
    "APRON_JOINT_LAP_M", "APRON_JOINT_DEPTH_M", "platform_field",
    "ribbon_edge_u",
    # ownership
    "OWNER_TRACK", "OWNER_ROAD", "OWNER_ACCESS", "OWNER_APRON", "OWNER_TERRAIN",
    # provenance
    "summary", "stamp", "selftest", "SPEC",
    # light
    "SUN_DIR", "SUN_ELEV_DEG", "SUN_BEARING_DEG", "SUN_ENERGY", "SUN_COLOR",
    "SUN_IRRADIANCE", "SUN_ANGULAR_DIAM_DEG", "SKY_SUN_ROTATION_DEG",
    "SKY_AIR", "SKY_AEROSOL", "SKY_OZONE", "SKY_ALTITUDE",
    "SKY_IRRADIANCE", "SKY_TINT", "DIRECT_TO_DIFFUSE",
    "E_DIRECT_HORIZONTAL", "REFERENCE_EXPOSURE_EXTERIOR",
    "VIEW_TRANSFORM", "VIEW_LOOK", "VISUAL_RANGE_M",
    "lambert_radiance", "SUN_SHADOW_RATIO", "DIFFUSE_FRACTION",
    "TOL_RECESS_RADIANCE", "recess_relative_radiance", "recess_is_black",
    "max_recess_depth",
    # tolerances
    "TOL_SEAM_M", "TOL_DATUM_M", "TOL_COPLANAR_M",
    "TOL_CLOSURE_M", "CONTINUITY_BOUNDS",
]

# ===========================================================================
#  0.  SPEC
# ===========================================================================

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
SPEC_PATH = os.path.join(_ROOT, "docs", "circuit_spec.json")

with open(SPEC_PATH, "r") as _f:
    SPEC = json.load(_f)

LAP = float(SPEC["headline"]["length_m"])              # 3675.0

_DATUM = SPEC["datum"]["circuit_design_frame"]
ROT_DEG = float(_DATUM["rotation_deg_about_z"])        # 40.0
PIVOT_DESIGN = tuple(float(v) for v in _DATUM["pivot_design"])   # (-350.0, 72.0)
PIVOT_WORLD = tuple(float(v) for v in _DATUM["pivot_world"])     # (15.0, 0.0)

_CR = math.cos(math.radians(ROT_DEG))
_SR = math.sin(math.radians(ROT_DEG))


def world_to_circuit(x, y):
    """world (x, y) -> circuit/design frame (cx, cy).  Vectorised."""
    vx = np.asarray(x, float) - PIVOT_WORLD[0]
    vy = np.asarray(y, float) - PIVOT_WORLD[1]
    return (vx * _CR + vy * _SR + PIVOT_DESIGN[0],
            -vx * _SR + vy * _CR + PIVOT_DESIGN[1])


def circuit_to_world(cx, cy):
    """circuit/design frame (cx, cy) -> world (x, y).  Vectorised."""
    vx = np.asarray(cx, float) - PIVOT_DESIGN[0]
    vy = np.asarray(cy, float) - PIVOT_DESIGN[1]
    return (vx * _CR - vy * _SR + PIVOT_WORLD[0],
            vx * _SR + vy * _CR + PIVOT_WORLD[1])


# ===========================================================================
#  1.  CENTRELINE  (exact, analytic, world frame)
# ===========================================================================
#
# Re-integrated from the element list rather than trusting the published
# per-element `start_world`, which is rounded to 1 cm: a 5 mm step at each of the
# 31 element joints reads, when sampled at 0.25 m, as 0.08 of spurious curvature.
# Integrating from the datum (329.396, 169.820) heading 40.000 deg reproduces every
# published start point to well under a centimetre and is exactly C1.
#
# Verified in --selftest against the spec's own 202 published centreline control
# points and against its published closure residual.

def _build_elements():
    x = float(SPEC["datum"]["start_finish_world"][0])
    y = float(SPEC["datum"]["start_finish_world"][1])
    h = math.radians(float(SPEC["datum"]["racing_direction_world_deg"]))
    els = []
    worst = 0.0
    for e in SPEC["elements"]:
        R = e.get("radius_m")
        turn = e.get("turn_deg")
        L = float(e["length_m"])
        worst = max(worst, math.hypot(x - e["start_world"][0], y - e["start_world"][1]))
        els.append(dict(name=e["name"], tag=e["name"].split()[0], kind=e["type"],
                        R=(float(R) if R else None), turn=turn, L=L,
                        s0=float(e["s_start"]), x0=x, y0=y, h0=h))
        if e["type"] == "S" or not R:
            x += math.cos(h) * L
            y += math.sin(h) * L
        else:
            sg = 1.0 if turn >= 0 else -1.0
            cx = x - sg * R * math.sin(h)
            cy = y + sg * R * math.cos(h)
            h += sg * L / R
            x = cx + sg * R * math.sin(h)
            y = cy - sg * R * math.cos(h)
    return els, worst, math.hypot(x - els[0]["x0"], y - els[0]["y0"])


_ELS, ELEMENT_REINTEGRATION_MAX_DEV_M, ELEMENT_CLOSURE_M = _build_elements()
_EL_S0 = np.array([e["s0"] for e in _ELS])
_EL_BY_TAG = {e["tag"]: e for e in _ELS}


def _find_el(s):
    i = int(np.searchsorted(_EL_S0, s % LAP, side="right")) - 1
    return _ELS[max(i, 0)]


def centreline(s):
    """(x, y, z, heading_rad, curvature) at lap station s.  Scalar."""
    s = float(s) % LAP
    e = _find_el(s)
    t = s - e["s0"]
    if e["kind"] == "S" or not e["R"]:
        h = e["h0"]
        return (e["x0"] + math.cos(h) * t, e["y0"] + math.sin(h) * t,
                float(elevation_c(s)), h, 0.0)
    R = e["R"]
    sg = 1.0 if e["turn"] >= 0 else -1.0
    h = e["h0"] + sg * t / R
    cx = e["x0"] - sg * R * math.sin(e["h0"])
    cy = e["y0"] + sg * R * math.cos(e["h0"])
    return (cx + sg * R * math.sin(h), cy - sg * R * math.cos(h),
            float(elevation_c(s)), h, sg / R)


def centreline_arrays(S):
    """Vectorised centreline: -> (X, Y, H, K) for an array of stations."""
    S = np.asarray(S, float) % LAP
    X = np.empty_like(S); Y = np.empty_like(S)
    H = np.empty_like(S); K = np.empty_like(S)
    idx = np.searchsorted(_EL_S0, S, side="right") - 1
    for i, e in enumerate(_ELS):
        m = idx == i
        if not m.any():
            continue
        t = S[m] - e["s0"]
        if e["kind"] == "S" or not e["R"]:
            H[m] = e["h0"]
            X[m] = e["x0"] + math.cos(e["h0"]) * t
            Y[m] = e["y0"] + math.sin(e["h0"]) * t
            K[m] = 0.0
        else:
            R = e["R"]; sg = 1.0 if e["turn"] >= 0 else -1.0
            h = e["h0"] + sg * t / R
            cx = e["x0"] - sg * R * math.sin(e["h0"])
            cy = e["y0"] + sg * R * math.cos(e["h0"])
            X[m] = cx + sg * R * np.sin(h)
            Y[m] = cy - sg * R * np.cos(h)
            H[m] = h
            K[m] = sg / R
    return X, Y, H, K


# --------------------------------------------------------------- station field
_FS = 0.25                              # field sample step (m)
_FN = int(round(LAP / _FS))             # 14700


def _fgrid():
    return np.arange(_FN) * _FS


def _csmooth(a, sigma_m):
    """Cyclic gaussian smooth of a station-indexed field on the _FS grid."""
    if sigma_m <= 0:
        return a
    sig = sigma_m / _FS
    rad = int(math.ceil(sig * 3.0))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sig) ** 2)
    k /= k.sum()
    return np.convolve(np.concatenate([a[-rad:], a, a[:rad]]), k, mode="same")[rad:-rad]


def _fsample(field, s):
    """Cyclic linear sample of a station field on the _FS grid."""
    x = np.asarray(s, float) % LAP / _FS
    i0 = np.floor(x).astype(np.int64) % _FN
    i1 = (i0 + 1) % _FN
    f = x - np.floor(x)
    return field[i0] * (1 - f) + field[i1] * f


# --------------------------------------------------- world -> (s, u) inversion
_PROJ_DS = 0.25
_PX, _PY, _PH, _PK = centreline_arrays(_fgrid())
_PSTEP = 16                                    # coarse stride: 4.0 m
_CX = np.ascontiguousarray(_PX[::_PSTEP])
_CY = np.ascontiguousarray(_PY[::_PSTEP])


def project(x, y, chunk=20000):
    """world (x, y) -> (s, u) on the LAP centreline.

    u is SIGNED, positive to the left of the direction of travel.  Exact to well
    under a millimetre: a nearest-sample search on a 0.25 m polyline followed by a
    first-order tangential/normal correction, whose residual is O(dt^2 * k / 2)
    = 2.8e-4 m at the tightest radius on the circuit.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    n = x.size
    S = np.empty(n); U = np.empty(n)
    off = np.arange(-_PSTEP, _PSTEP + 1)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        dx = x[a:b, None] - _CX[None, :]
        dy = y[a:b, None] - _CY[None, :]
        ic = np.argmin(dx * dx + dy * dy, axis=1) * _PSTEP
        idx = (ic[:, None] + off[None, :]) % _FN
        fx = x[a:b, None] - _PX[idx]
        fy = y[a:b, None] - _PY[idx]
        j = np.argmin(fx * fx + fy * fy, axis=1)
        i = idx[np.arange(b - a), j]
        h = _PH[i]
        ex = x[a:b] - _PX[i]
        ey = y[a:b] - _PY[i]
        S[a:b] = (i * _PROJ_DS + (ex * np.cos(h) + ey * np.sin(h))) % LAP
        U[a:b] = -ex * np.sin(h) + ey * np.cos(h)
    return S, U


def world_su(x, y):
    """Alias of `project` kept for readability at call sites."""
    return project(x, y)


# The circuit's own bounding box, so the corridor tests can reject the far field
# without a nearest-point search.  build_terrain asks these questions of 556 480
# grid points every rebuild; 92 % of them are nowhere near the road.
_BB = (float(_PX.min()), float(_PX.max()), float(_PY.min()), float(_PY.max()))


def _near_circuit(x, y, pad):
    return ((x >= _BB[0] - pad) & (x <= _BB[1] + pad) &
            (y >= _BB[2] - pad) & (y <= _BB[3] + pad))


def su_to_world(s, u, side=None):
    """(station, signed lateral) -> world (x, y, z) ON THE GROUND DATUM."""
    if side is not None:
        u = np.asarray(u, float) * float(side)
    S = np.atleast_1d(np.asarray(s, float))
    U = np.atleast_1d(np.asarray(u, float))
    S, U = np.broadcast_arrays(S, U)
    X, Y, H, _ = centreline_arrays(S)
    Z = ground_z(S, U)
    P = np.stack([X - np.sin(H) * U, Y + np.cos(H) * U, Z], axis=-1)
    if np.ndim(s) == 0 and np.ndim(u) == 0:
        return (float(P[0, 0]), float(P[0, 1]), float(P[0, 2]))
    return P


# ===========================================================================
#  2.  ELEVATION  (spec §5: tangent grades + symmetric parabolic vertical curves)
# ===========================================================================
#
# All three existing implementations (build_surface.elevation_c, build_barriers
# Centre._elev, build_terrain Circuit.elev) agree with each other and with this one
# to 1e-12; this is not where the divergence was.  It is here so nobody has to keep
# a fourth copy.

_PVI = SPEC["elevation"]["station_z_pvi"]
_PS = np.array([float(p["s"]) for p in _PVI])
_PZ = np.array([float(p["z"]) for p in _PVI])
_PL = np.array([float(p.get("vertical_curve_len_m", 0.0)) for p in _PVI])
_PG = np.zeros(len(_PS))
for _i in range(len(_PS) - 1):
    _PG[_i] = (_PZ[_i + 1] - _PZ[_i]) / (_PS[_i + 1] - _PS[_i])
_PG[-1] = _PG[-2]


def elevation_c(s):
    """Centreline elevation z at lap station s.  Scalar or array."""
    scalar = np.ndim(s) == 0
    x = np.atleast_1d(np.asarray(s, float)) % LAP
    seg = np.clip(np.searchsorted(_PS, x, side="right") - 1, 0, len(_PS) - 2)
    z = _PZ[seg] + _PG[seg] * (x - _PS[seg])
    for j in range(1, len(_PS) - 1):
        Lv = _PL[j]
        if Lv <= 0.0:
            continue
        a0, a1 = _PS[j] - Lv * 0.5, _PS[j] + Lv * 0.5
        m = (x >= a0) & (x <= a1)
        if not m.any():
            continue
        xx = x[m] - a0
        g1, g2 = _PG[j - 1], _PG[j]
        z[m] = _PZ[j] + g1 * (xx - Lv * 0.5) + (g2 - g1) * xx * xx / (2.0 * Lv)
    return float(z[0]) if scalar else z


# ===========================================================================
#  3.  TRACK SECTION  (spec §9)  —  THE WIDTH BUG, FIXED
# ===========================================================================
#
# spec §9 declares five section widths and one transition rule:
#
#     pit straight (S15 + S0)   16.0 m      standard   14.0 m
#     T4 hairpin (widened)      15.0 m      esses T6-T9 (narrowed)  13.0 m
#     access road / pit exit    12.0 m
#     "Width transitions are linear over 60 m so no seam is visible from the air."
#
# THE RULE, stated once and for all:  a named section carries its full declared
# width over EXACTLY its element extent.  The 60 m linear transition lies entirely
# OUTSIDE the section, in the neighbour.  Therefore
#
#     half_width(3115.000) = 8.000   (S15 s_start, the pit straight opens here)
#     half_width(3055.000) = 7.000   (60 m earlier, still standard section)
#     half_width( 250.000) = 8.000   (T1 s_start, the pit straight closes here)
#     half_width( 310.000) = 7.000   (60 m later, standard again)
#
# What went wrong before:
#   build_surface._build_width set the 16 m span to [3115+30, 250-30] and then
#   applied a +-30 m raised cosine, CENTRING the transition on the element
#   boundary instead of starting it there -> 14.04 m at s = 3115.
#   build_terrain._ramped set the span to [3115, 3675] and box-filtered it over
#   60 m, which is the same centring error -> 15.00 m at s = 3115.
#   build_barriers.half_width had it right; everyone else was 0.98 m out over 13 %
#   of the lap, and because barriers pins runoff, verge, boards and barrier
#   offsets to verge_edge = half_width + 2.5, that left a 0.63 m strip of UNBUILT
#   GROUND along both edges of the pit straight.
#
# LINEAR, not raised-cosine.  The spec says linear; a 1.0 m width change over 60 m
# is a 0.95 deg deflection of the road edge and a real circuit has exactly that
# joint.  A C1 rounding would have to be adopted by all five consumers or none, and
# "none" is the only one that cannot drift.

_TS = SPEC["track_section"]
PIT_STRAIGHT_W = float(_TS["pit_straight_m"])       # 16.0
STANDARD_W = float(_TS["standard_m"])               # 14.0
HAIRPIN_W = float(_TS["hairpin_m"])                 # 15.0
ESSES_W = float(_TS["esses_m"])                     # 13.0
ACCESS_ROAD_W = float(_TS["access_road_m"])         # 12.0
TRANSITION_LEN = float(_TS["transition_len_m"])     # 60.0

KERB_W = float(_TS["kerb"]["width_m"])              # 1.50
VERGE_W = 1.00                                      # spec §9 prose: painted verge
KERB_LIP_OUTER_M = float(_TS["kerb"]["outer_lip_mm"]) / 1000.0     # 0.050
KERB_LIP_INNER_M = float(_TS["kerb"]["inner_lip_mm"]) / 1000.0     # 0.025
KERB_SERRATION_AMP_M = float(_TS["kerb"]["serration_amplitude_mm"]) / 1000.0   # 0.025
KERB_SERRATION_PITCH_M = float(_TS["kerb"]["serration_pitch_mm"]) / 1000.0     # 0.250
NEG_KERB_DEPTH_M = float(_TS["negative_kerb"]["depth_mm"]) / 1000.0            # -0.060
NEG_KERB_W = float(_TS["negative_kerb"]["width_m"])                            # 0.80

# named section extents, taken from the element list to the metre they actually are
_S_PIT_OPEN = _EL_BY_TAG["S15"]["s0"]                                   # 3115.0
_S_PIT_CLOSE = _EL_BY_TAG["T1"]["s0"]                                   # 250.0
_S_HAIRPIN_0 = _EL_BY_TAG["T4"]["s0"]                                   # 939.2693
_S_HAIRPIN_1 = _S_HAIRPIN_0 + _EL_BY_TAG["T4"]["L"]                     # 1025.2791
_S_ESSES_0 = _EL_BY_TAG["T6"]["s0"]                                     # 1545.4708
_S_ESSES_1 = _EL_BY_TAG["T9"]["s0"] + _EL_BY_TAG["T9"]["L"]             # 1904.0411

# piecewise-linear keys, half widths, unwrapped so the pit straight brackets s = 0
_HW_KEYS = np.array([
    0.0,                                   # inside the pit straight
    _S_PIT_CLOSE,                          # 250.000   pit straight closes
    _S_PIT_CLOSE + TRANSITION_LEN,         # 310.000
    _S_HAIRPIN_0 - TRANSITION_LEN,         # 879.269
    _S_HAIRPIN_0,                          # 939.269   hairpin opens
    _S_HAIRPIN_1,                          # 1025.279  hairpin closes
    _S_HAIRPIN_1 + TRANSITION_LEN,         # 1085.279
    _S_ESSES_0 - TRANSITION_LEN,           # 1485.471
    _S_ESSES_0,                            # 1545.471  esses open
    _S_ESSES_1,                            # 1904.041  esses close
    _S_ESSES_1 + TRANSITION_LEN,           # 1964.041
    _S_PIT_OPEN - TRANSITION_LEN,          # 3055.000
    _S_PIT_OPEN,                           # 3115.000  pit straight opens
    LAP,
])
_HW_VALS = np.array([
    PIT_STRAIGHT_W, PIT_STRAIGHT_W, STANDARD_W,
    STANDARD_W, HAIRPIN_W, HAIRPIN_W, STANDARD_W,
    STANDARD_W, ESSES_W, ESSES_W, STANDARD_W,
    STANDARD_W, PIT_STRAIGHT_W, PIT_STRAIGHT_W,
]) * 0.5


def half_width(s):
    """Half of the racing surface at lap station s (m).  Spec §9.  Scalar/array."""
    scalar = np.ndim(s) == 0
    x = np.atleast_1d(np.asarray(s, float)) % LAP
    v = np.interp(x, _HW_KEYS, _HW_VALS)
    return float(v[0]) if scalar else v


def verge_edge(s):
    """Centreline -> outboard edge of the painted verge (m).

    half_width + 1.50 m kerb band + 1.00 m painted verge.  This is the OUTERMOST
    edge of build_surface's own mesh, the surface every other module butts to, and
    the anchor for the whole runoff programme.
    """
    return half_width(s) + KERB_W + VERGE_W


def kerb_top_z(s, u, side=None, serration_phase=None):
    """Top of a serrated kerb at (s, u), for clearance checks only.

    The kerb is 1.50 m wide, 25 mm proud at the track-side lip and 50 mm at the
    outer lip, with a 25 mm serration on a 250 mm pitch riding on top (spec §9 ->
    75 mm peak).  Kerb GEOMETRY belongs to build_surface; this function exists so
    the camera rig, the car and the collision gate can ask "how high is the kerb
    here" without meshing one.
    """
    if side is not None:
        u = np.asarray(u, float) * float(side)
    S = np.atleast_1d(np.asarray(s, float))
    U = np.atleast_1d(np.asarray(u, float))
    S, U = np.broadcast_arrays(S, U)
    t = np.clip((np.abs(U) - half_width(S)) / KERB_W, 0.0, 1.0)
    lip = KERB_LIP_INNER_M + (KERB_LIP_OUTER_M - KERB_LIP_INNER_M) * t
    if serration_phase is None:
        serr = KERB_SERRATION_AMP_M                  # worst case = ridge crest
    else:
        serr = KERB_SERRATION_AMP_M * 0.5 * (
            1.0 + np.cos(2.0 * math.pi * np.asarray(serration_phase, float)))
    return ground_z(S, U) + lip + serr


# ===========================================================================
#  4.  CROSS-SLOPE:  banking (spec §4) + T4 camber override + drainage crown
# ===========================================================================

def _build_cross():
    g = _fgrid()
    bank = np.zeros(_FN)          # signed dz/du: +ve means the surface rises LEFT
    for c in SPEC["corners"]:
        tag = c["name"].split()[0]
        e = _EL_BY_TAG.get(tag)
        if e is None or not c.get("is_numbered_corner", True):
            continue
        deg = float(c.get("banking_deg") or 0.0)
        if abs(deg) < 1e-6:
            continue
        sg = 1.0 if c["direction"] == "left" else -1.0
        # banked INTO the turn: the OUTSIDE is higher.  the inside of a left corner
        # is +u, so the plane falls toward +u  =>  dz/du = -sg*tan(bank).
        val = -sg * math.tan(math.radians(deg))
        a, b = e["s0"], e["s0"] + e["L"]
        bank[(g >= a) & (g <= b)] = val
    bank = _csmooth(bank, 14.0)   # 40-50 m of ease-in either side of every arc

    for ov in SPEC.get("camber_overrides", []):
        if ov["corner"] != "T4":
            continue
        e = _EL_BY_TAG["T4"]
        a, b = e["s0"] - 60.0, e["s0"] + e["L"] * 0.5
        m = (g >= a) & (g <= b)
        t = np.clip((g[m] - a) / (b - a), 0, 1)
        adverse = float(ov["entry_pct"]) / 100.0      # -0.015, falling from the turn
        bank[m] = bank[m] * t + adverse * (1.0 - t) ** 1.4
    bank = _csmooth(bank, 6.0)

    # parabolic drainage crown, suppressed wherever the road is deliberately banked
    cw = np.clip(1.0 - np.abs(bank) / math.tan(math.radians(1.2)), 0.0, 1.0)
    return bank, _csmooth(cw, 12.0)


_BANK, _CROWN_W = _build_cross()

# the "one plane" zones (spec §2 / §10.5): the pit straight and the transit route
# are declared ONE PLANE with the paddock, so they get a shallower crown and a
# calmer surface than the rest of the lap.
_FLAT = np.zeros(_FN)
_FLAT[(_fgrid() >= _S_PIT_OPEN) | (_fgrid() <= 300.0)] = 1.0
_FLAT = _csmooth(_FLAT, 25.0)

CROWN_FALL = 0.0145            # mean cross-fall at the racing-surface edge (1.45 %)
CROWN_FLAT_SUPPRESS = 0.45     # how much of it the declared-flat zones lose
VERGE_DRAIN_M = 0.012          # the painted verge drains this much harder than the
                               # racing surface, reached at |u| = verge_edge
PLATFORM_FALL = -0.016         # runoff platform cross-fall outboard of verge_edge


def _cross_z(S, U, Wh):
    bank = _fsample(_BANK, S)
    cw = _fsample(_CROWN_W, S)
    crown = -CROWN_FALL * Wh * (np.abs(U) / np.maximum(Wh, 0.1)) ** 2
    crown *= (1.0 - CROWN_FLAT_SUPPRESS * _fsample(_FLAT, S))
    return bank * U + crown * cw


# ===========================================================================
#  5.  UNDULATION  (deterministic value noise, no telemetry, no racing line)
# ===========================================================================
#
# Low-frequency surface relief, wavelengths >= ~3 m.  Everything shorter is carried
# by the shader's bump, which resolves far better than 0.7 m mesh rows could.
#
# DELIBERATELY EXCLUDED from the datum: build_surface's two racing-line-dependent
# micro terms — the -9 mm compaction dip along the driven line and the +4.5 mm
# braking-zone washboard.  Both are gaussian-windowed on (u - racing_line(s)) with
# 2.8 m and 3.4 m sigmas, so they are already < 1 mm by the time they reach the
# track edge and they are invisible to every other module; but computing them here
# would drag the 240-iteration drivability solve for the racing line into a module
# that five builders import.  build_surface MAY add them on top of ground_z inside
# the racing surface, under two conditions that make them provably harmless:
#
#     |extra| <= MICRO_LAYER_MAX_M   everywhere, and
#     extra == 0 for |u| >= half_width(s).
#
# `micro_window(s, u)` below is provided so that second condition is not a promise
# but a multiplication.

MICRO_LAYER_MAX_M = 0.018      # MEASURED, not asserted: over 200 000 random (s, u)
                               # inside the racing surface, |surface_z - ground_z|
                               # is max 14.4 mm, p99 11.1 mm, p50 0.7 mm, and the
                               # analytic worst case of the two excluded terms is
                               # 0.009*1.35 + 0.0045 = 16.6 mm.


def _hash2(ix, iy, seed):
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    h = (ix * 374761393 + iy * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h.astype(np.float64) / 4294967295.0


def _vnoise(x, y, seed, nx=None):
    """Quintic-interpolated value noise.

    `nx` wraps the X LATTICE INDEX at `nx` cells.  THIS IS DEFECT 2 (v1.1.0).
    The station axis is cyclic — s and s + LAP are the same metre of road — but
    a noise lattice is only cyclic if a whole number of its cells fits in a lap.
    `s / 46.0` puts 79.891 cells in 3675 m, so cell 0 and cell 79.891 carry
    unrelated hashes and THE DATUM had a 6.75 mm step across the start/finish
    line: inside TOL_SEAM_M, hidden under the painted S/F line, and still a step
    in the ground the film drives down at 300 km/h.  Pass `nx` and the lattice
    closes on itself exactly.
    """
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    if nx is None:
        ix1 = ix + 1
    else:
        ix = ix % int(nx)
        ix1 = (ix + 1) % int(nx)
    a = _hash2(ix, iy, seed); b = _hash2(ix1, iy, seed)
    c = _hash2(ix, iy + 1, seed); d = _hash2(ix1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


# Whole cells per lap, so the noise lattice is cyclic in s.  Chosen as
# round(LAP / target_wavelength) for the three published wavelengths, which moves
# each of them by less than 0.15 %:
#
#     target 46.0 m -> 80 cells  -> 45.9375 m   (-0.136 %)
#     target 15.5 m -> 237 cells -> 15.5063 m   (+0.041 %)
#     target  4.8 m -> 766 cells ->  4.79765 m  (-0.049 %)
#
# The amplitudes (30 / 14 / 5.5 mm) are untouched.  The PATTERN moves — the cell
# boundaries drift by up to 0.11 of a cell over the lap — so every module that
# BAKED a mesh against v1.0.x's ground_z must rebuild.  Measured effect on the
# datum is reported by --selftest.
_UND_CELLS = (80, 237, 766)


def _undulation(S, U):
    amp = 1.0 - 0.55 * _fsample(_FLAT, S)     # the main straight is flatter
    t = (np.asarray(S, float) % LAP) / LAP    # cyclic lap fraction
    n1, n2, n3 = _UND_CELLS
    z = 0.0300 * amp * (_vnoise(t * n1, U / 27.0, 17, n1) - 0.5) * 2.0
    z += 0.0140 * amp * (_vnoise(t * n2, U / 9.5, 91, n2) - 0.5) * 2.0
    z += 0.0055 * amp * (_vnoise(t * n3, U / 3.1, 233, n3) - 0.5) * 2.0
    return z


def micro_window(s, u, side=None):
    """1 inside the racing surface, 0 at and beyond half_width(s), C1 between.

    Multiply any build_surface-private micro displacement by this and it cannot
    reach a module boundary.
    """
    if side is not None:
        u = np.asarray(u, float) * float(side)
    S = np.atleast_1d(np.asarray(s, float))
    U = np.atleast_1d(np.asarray(u, float))
    S, U = np.broadcast_arrays(S, U)
    Wh = half_width(S)
    t = np.clip((Wh - np.abs(U)) / 1.0, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ===========================================================================
#  6.  NEGATIVE KERBS  (spec §9: -60 mm x 0.80 m at the T8 apex and the T12 exit)
# ===========================================================================

def _build_neg_kerbs():
    dirs = {c["name"].split()[0]: c["direction"] for c in SPEC["corners"]}
    e8, e12 = _EL_BY_TAG["T8"], _EL_BY_TAG["T12"]
    ap8 = e8["s0"] + e8["L"] * 0.62               # a shade past the geometric apex
    s12 = e12["s0"] + e12["L"] * 1.05
    return [(ap8 - 13.0, ap8 + 16.0, 1.0 if dirs["T8"] == "left" else -1.0),
            (s12, s12 + 30.0, -1.0 if dirs["T12"] == "left" else 1.0)]


NEG_KERBS = _build_neg_kerbs()      # [(s0, s1, side), ...]


def _neg_kerb_z(S, U, Wh):
    z = np.zeros_like(S)
    for (a, b, side) in NEG_KERBS:
        t = (np.abs(U) - Wh) / NEG_KERB_W
        along = np.clip((S - a) / 1.6, 0, 1) * np.clip((b - S) / 1.6, 0, 1)
        prof = np.clip(t / 0.16, 0, 1) * np.clip((1.0 - t) / 0.16, 0, 1)
        prof = np.where((t >= 0) & (t <= 1.0), prof, 0.0)
        m = (np.sign(U) == side) & (S >= a - 2.0) & (S <= b + 2.0)
        z = np.where(m, z + NEG_KERB_DEPTH_M * along * prof, z)
    return z


# ===========================================================================
#  7.  ground_z  —  THE DATUM
# ===========================================================================
#
#   |u| <= verge_edge(s)      the built road cross-section: centreline elevation,
#                             plus banking and drainage crown, plus undulation,
#                             plus the negative-kerb troughs, less the 12 mm the
#                             painted verge drains harder than the racing surface.
#                             This IS build_surface's own mesh, to the millimetre.
#
#   |u| >  verge_edge(s)      the runoff platform: the road-edge elevation carried
#                             outboard at a constant -1.6 %.  Gravel traps are dug
#                             0.24 m INTO this by build_barriers; runoff asphalt is
#                             laid ON it; the Armco foot stands ON it; terrain
#                             never touches it.
#
# The extension freezes the whole road-edge value (including banking and
# undulation) and adds the linear fall.  That is the single most important
# consequence of this file: at 4 deg of banking on T10/T11 the outboard road edge
# is 0.66 m below the centreline, and a runoff platform that starts from the
# CENTRELINE elevation instead — which is what the old build_barriers.ground_z did
# — is 0.66 m out before it has fallen a single metre.

APRON_TIE_M = 8.0        # over how many metres the runoff platform gives up its
                         # outward fall and ties into the declared z = 0.000 apron


def ground_z(s, u, side=None):
    """THE ground datum.  z of the finished ground at (station, signed lateral).

    Pass `side` (+1 left / -1 right) to use the (unsigned lat, side) convention.

    Scalar in -> float out.  Array in -> ndarray out.  Broadcasts.
    """
    scalar = (np.ndim(s) == 0 and np.ndim(u) == 0)
    if side is not None:
        u = np.abs(np.asarray(u, float)) * float(side)
    S = np.atleast_1d(np.asarray(s, float)) % LAP
    U = np.atleast_1d(np.asarray(u, float))
    S, U = np.broadcast_arrays(S, U)

    Wh = half_width(S)
    E = Wh + KERB_W + VERGE_W                      # verge_edge
    A = np.abs(U)
    Uc = np.sign(U) * np.minimum(A, E)             # clamped to the road cross-section

    z = (elevation_c(S) + _cross_z(S, Uc, Wh) + _undulation(S, Uc)
         + _neg_kerb_z(S, Uc, Wh))
    # the painted verge drains a touch harder than the racing surface
    z -= np.clip((np.abs(Uc) - Wh - KERB_W) / VERGE_W, 0, 1) * VERGE_DRAIN_M

    # outboard of the verge: the runoff platform, falling at -1.6 % from the ROAD
    # EDGE (banking and all), except where it abuts the declared z = 0.000 apron.
    d = np.maximum(0.0, A - E)
    z_fall = z + PLATFORM_FALL * d

    # THE APRON TIE.  spec §2 makes z = 0.000 the pit-straight surface; spec §10.5
    # makes the pit-exit apron "one plane at z = 0.000"; spec §9 crowns the racing
    # surface.  All three are true, and they meet at the track edge, where the
    # crown has already taken the road edge to -0.10 m.  A real pit exit resolves
    # that with a shallow valley gutter at the road edge and then flat concrete,
    # and so does this: outboard of the verge, wherever the corridor programme
    # carries NO barrier (which is exactly and only the open pit-exit apron,
    # circuit x -480..-245 on the left of the pit straight), the platform gives up
    # its outward fall over APRON_TIE_M and lands on APRON_Z.
    # 0.10 m over 8.0 m is 1.25 % — a channel, not a step.
    ap = np.where(U >= 0.0, COR.sample("apronw", S, +1), COR.sample("apronw", S, -1))
    w = ap * smoothstep(0.0, APRON_TIE_M, d)
    z = z_fall * (1.0 - w) + APRON_Z * w

    return float(z.reshape(-1)[0]) if scalar else z


# ===========================================================================
#  8.  THE RUNOFF PROGRAMME  (spec §9 table -> a station-sampled cross-section)
# ===========================================================================
#
# Ported verbatim from build_barriers so that `barrier_offset` is numerically
# identical to the barrier line that is already built, and so that a change to the
# runoff table moves the barrier, the platform edge, the terrain hole and the
# dressing standoff together instead of one at a time.

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


def _sstep(t):
    return t * t * (3.0 - 2.0 * t)


def smoothstep(e0, e1, x):
    return _sstep(np.clip((np.asarray(x, float) - e0) / max(1e-9, (e1 - e0)), 0.0, 1.0))


def _vnoise1(x, seed=0):
    x = np.asarray(x, float)
    i = np.floor(x).astype(np.int64)
    f = x - i
    a = hash01(i, np.full_like(i, seed))
    b = hash01(i + 1, np.full_like(i, seed))
    return a * (1.0 - _sstep(f)) + b * _sstep(f)


def _fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    x = np.asarray(x, float)
    tot = np.zeros_like(x)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot += amp * _vnoise1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


PS = 1.0                                        # runoff profile step (m)
NS = int(round(LAP / PS))                       # 3675
SGRID = np.arange(NS, dtype=np.float64) * PS

B_ARMCO, B_TECPRO3, B_CONCRETE, B_NONE = 0, 1, 2, 3


def _ramp(s0, s1, ramp, s=SGRID):
    """1 inside [s0, s1], smoothly 0 outside over `ramp` metres, cyclic-safe."""
    a = smoothstep(-ramp, 0.0, ((s - s0 + LAP * 0.5) % LAP) - LAP * 0.5)
    b = 1.0 - smoothstep(0.0, ramp, ((s - s1 + LAP * 0.5) % LAP) - LAP * 0.5)
    return np.minimum(a, b)


# ---------------------------------------------------------------------------
#  SMOOTH MIN/MAX AND CONE EROSION  —  the two tools §8 uses instead of
#  np.maximum / np.minimum, and why (DEFECT 1, v1.1.0)
# ---------------------------------------------------------------------------
#
# `np.maximum` of two smooth ramps is CONTINUOUS but not C1: it kinks where the
# branches cross.  The corridor cross-section is assembled almost entirely out of
# maxima and minima, so every crossover was a crease in the barrier line, in
# `runoff_edge` and in `platform_edge` — and `platform_edge` is the polyline
# build_terrain WELDS ITS FIRST RING OF VERTICES TO, under a 12.47 deg sun.
#
# `_smax` / `_smin` are the quadratic polynomial smooth-max/min.  They differ from
# the hard operator by AT MOST k/4, and only within k of a crossover.  k is chosen
# so that k/4 = 0.15 m, which is INSIDE `BARRIER_JITTER_MAX_M` = 0.25 m — the
# lateral freedom build_barriers is already contractually allowed to use on the
# barrier line — so no consumer's clearance analysis changes.  `_smax` only ever
# moves an edge OUTBOARD and `_smin` only ever inboard, so the terrain hole can
# only grow and the barrier can only move away from the racing surface.
#
# `_cone_erode` is the tool for the geometric cap.  cone(c)(s) = min_j (c(j) +
# rate*|s-j|).  Three properties, all of which the contract needs and none of
# which a convolution has:
#
#   1. the result is EXACTLY `rate`-Lipschitz whatever `c` does, including if `c`
#      steps.  A box or gaussian filter of a stepped field is still a smoothed
#      step whose slope goes as (step / width); a cone erosion's slope is `rate`
#      by construction.  This is what makes the continuity bound in §12 a
#      PROPERTY rather than an observation.
#   2. the result is never below min(c).  build_barriers' first attempt at this
#      subtracted a BOX-SMOOTHED deficit and produced -18.80 m on side +1 — a
#      barrier face 18.8 m past the centreline, which is how BR_Armco_L03/L04
#      came to lie across the T4 braking zone.  A cone cannot do that.
#   3. it is a NO-OP wherever `c` is already `rate`-Lipschitz, so setting `rate`
#      at the runoff programme's own steepest declared lateral rate leaves every
#      station the cap never touched bit-for-bit unchanged.
#
# BARRIER_MAX_LATERAL_RATE is calibrated from the RUNOFF_ZONES table itself.  A
# zone of total width W ramped by `_ramp` over R metres moves the corridor edge at
# up to 1.5*W/R (the peak slope of a smoothstep is 1.5/R).  Over the shipped
# table that is:
#
#     T10T11  70.0 m over 60 m  -> 1.750 m/m     T3   55.0 over 50 -> 1.650
#     T8      45.0 m over 40 m  -> 1.688 m/m     T1   57.0 over 55 -> 1.555
#     T4/T12/T15 30.0 over 45   -> 1.000 m/m     T5 grass 20/45    -> 0.667
#
# so 1.750 m/m is the steepest lateral motion any SINGLE entry declares.  Two
# zones, an apex bed and a pin blend can land on the same station, and they do:
# the S11 doppler pin's ramp-in overlaps T10T11's ramp-out, and the assembled
# programme line peaks at 1.9447 m/m at s = 2459 on side -1.  That measurement is
# the LOWER bound on this number.
#
# The UPPER bound is that a lateral taper steeper than about 1 : 0.5 is not a
# barrier line at all, it is TWO barrier lines — the run ends and another begins
# further out, which is what a circuit builds where a runoff opens — and every
# consumer that looks for a break in the line looks for it at 2.00 m/m
# (build_barriers.BARRIER_BREAK_RATE, a STRICT `>` test that must never fire on a
# line the contract calls continuous).  1.95 is the tightest round number above
# the programme and strictly below that threshold: 0.3 % of margin over the
# former, 2.5 % under the latter.  If a change to RUNOFF_ZONES pushes the
# programme over it, selftest [12b] FAILS and says so rather than letting the
# erosion silently reshape the declared line.
#
# It is the number `barrier_offset` is eroded at AND the number §12 asserts
# against, deliberately: the bound and the construction are one number, not two.
# Consumers should import it rather than keep their own copy (RULE 1).
CORRIDOR_SMOOTH_K_M = 0.60          # 4 * 0.15 m; see BARRIER_JITTER_MAX_M
BARRIER_MAX_LATERAL_RATE = 1.95     # m of lateral per m of station

# THE THRESHOLD A CONSUMER TESTS AT, AND IT IS NOT THE SAME NUMBER, v1.2.0.
#
# `build_barriers` looks for a break in the line with a STRICT `>` and used to
# carry a private 2.00 for it — 2.5 % of dead band above a line the contract
# guarantees at 1.95, so the detector could never fire whatever the corridor did
# (D3).  Setting it to 1.95 makes it fire on FLOAT ROUND-OFF: MEASURED on the
# shipped line, `max |d off / ds|` is 1.9499999999999993 on side +1 and
# **1.9500000000000028** on side -1 — 2.9e-15 over, at 11 stations, which blanked
# 17 m of Armco on the right-hand side of the lap for nothing.  (Found by
# measuring the artefact after making the "two-line" change, not by reading it.)
#
# `_cone_erode` builds the line as repeated `e[i-1] + rate*ds`, so a station where
# the erosion binds lands on `rate` to within a few ULPs either way, and the sign
# of that error is not something a contract can promise.  So the contract
# publishes BOTH numbers: the rate it GUARANTEES, and the rate at which a
# consumer may call the line broken.  RATE_EPS is 1 micron of lateral per metre
# of station — far below anything geometric, far above the round-off — and it is
# the same epsilon the continuity gate in S14 already allowed itself.
RATE_EPS = 1.0e-6
BARRIER_BREAK_RATE = BARRIER_MAX_LATERAL_RATE + RATE_EPS

# "no geometric cap".  A SENTINEL, and it must stay finite and modest: the whole
# of DEFECT 1(a) was 1e6 poured into a mean.  It only has to exceed the largest
# offset the runoff programme can ask for, which is 81.95 m on the shipped table.
MAXOFF_NONE_M = 200.0
MAXOFF_REACH_M = 55.0               # how far either side of a tight corner its
                                    # inside cap reaches (unchanged from v1.0.x)

# --------------------------------------------------------- THE OWNERSHIP CAP
# v1.2.0 / R2-035.  The numbers S9b's solve runs on.  They are stated here, next
# to the rate cap they sit beside in `_Corridor._build`, because the two caps
# answer the same question from different directions: MAXOFF_* is "how far out
# can a barrier stand before the geometry of THIS corner forbids it", the
# OWNED_* / CORRIDOR_BIAS_M group is "how far out before ANOTHER LEG owns the
# ground".  Ported unchanged from `build_barriers` S4b, which has been running
# them on the shipped world since the T4 Armco wall — so promoting them moves no
# barrier that module already built.  See S9b for the derivation of each.
OWNED_SOLVE_DS_M = 2.0              # station step of the ownership solve
OWNED_SOLVE_NT = 65                 # lateral samples per station
OWNED_SELF_WINDOW_M = 2.0           # |ds| within which a projection counts as
                                    # THIS station's own.  A TOLERANCE, not an
                                    # exclusion window — see S9b.
OWNED_SELF_U_TOL_M = 0.25           # ... and the matching lateral tolerance
CORRIDOR_BIAS_M = 0.75              # deliberate over-reach at the medial axis: a
                                    # hidden sliver of overlap between two legs
                                    # beats a hole between them
BARRIER_TAPER_MAX_RATE = 0.30       # m of lateral per m of station, 1 : 3.3 — the
                                    # steepest a barrier line may move INSIDE a
                                    # stretch the ownership cap has bitten
OWNERSHIP_BLEND_M = 60.0            # how far either side of a capped station that
                                    # taper is allowed to reach
BARRIER_MIN_CLEAR_M = 1.00          # the tightest clearance above `verge_edge`
                                    # this contract declares anywhere (the pit
                                    # wall: y = +11.5 against a verge edge at
                                    # 10.5).  ASSERTED in selftest [17], never
                                    # used to clamp.


def _smax(a, b, k=CORRIDOR_SMOOTH_K_M):
    """C1 maximum.  >= max(a, b), and <= max(a, b) + k/4."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    h = np.clip(1.0 - np.abs(a - b) / k, 0.0, 1.0)
    return np.maximum(a, b) + 0.25 * k * h * h


def _smin(a, b, k=CORRIDOR_SMOOTH_K_M):
    """C1 minimum.  <= min(a, b), and >= min(a, b) - k/4."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    h = np.clip(1.0 - np.abs(a - b) / k, 0.0, 1.0)
    return np.minimum(a, b) - 0.25 * k * h * h


def _cone_erode(c, rate, ds=PS, laps=2):
    """Cyclic cone erosion:  out(s) = min_j ( c(j) + rate*|s - j| ).

    `rate`-Lipschitz by construction, <= c everywhere, and never below min(c).
    Two forward and two backward sweeps close the cycle for any rate > 0.
    """
    step = float(rate) * float(ds)
    e = np.asarray(c, float).copy()
    n = e.size
    for _ in range(laps):
        for i in range(n):
            v = e[i - 1] + step
            if v < e[i]:
                e[i] = v
    for _ in range(laps):
        for i in range(n - 1, -1, -1):
            v = e[(i + 1) % n] + step
            if v < e[i]:
                e[i] = v
    return e


# (label, s0, s1, side, asphalt_m, gravel_m, barrier, ramp)     spec §9 table
RUNOFF_ZONES = [
    ("T1",      170.0,  430.0, -1, 45.0, 12.0, B_TECPRO3, 55.0),
    ("T3",      688.0,  900.0, +1, 40.0, 15.0, B_ARMCO,   50.0),
    ("T4",      893.0, 1082.0, -1,  0.0, 30.0, B_TECPRO3, 45.0),
    ("T5",     1168.0, 1360.0, +1,  0.0,  0.0, B_ARMCO,   45.0),   # 20 m grass
    ("T8",     1706.0, 1868.0, -1, 20.0, 25.0, B_ARMCO,   40.0),
    ("T10T11", 2105.0, 2445.0, -1, 55.0, 15.0, B_ARMCO,   60.0),
    ("T12",    2618.0, 2792.0, -1,  0.0, 30.0, B_TECPRO3, 45.0),
    ("T15",    2985.0, 3160.0, -1, 30.0,  0.0, B_ARMCO,   45.0),
    # the hairpin INSIDE is a paved apron, not runoff: the kerb-height camera
    # stands on it and the tyre wall is 4.0 m behind the lens (spec §11 Beat 5)
    ("T4i",     900.0, 1080.0, +1,  2.4,  0.0, B_ARMCO,   30.0),
]

# apex-side gravel beds ("everywhere else ... a gravel bed on the apex side")
APEX_BEDS = [
    ("T1i",   258.0,  372.0, +1, 9.0), ("T2i",  400.0,  462.0, +1, 8.0),
    ("T3i",   722.0,  798.0, -1, 8.0), ("T5i", 1204.0, 1318.0, -1, 10.0),
    ("T6i",  1548.0, 1606.0, +1, 7.0), ("T7i", 1648.0, 1712.0, -1, 7.0),
    ("T8i",  1752.0, 1812.0, +1, 7.0), ("T9i", 1857.0, 1906.0, -1, 7.0),
    ("T10i", 2146.0, 2242.0, +1, 11.0), ("T11i", 2298.0, 2404.0, +1, 11.0),
    ("T12i", 2703.0, 2748.0, +1, 9.0), ("T13i", 2804.0, 2830.0, +1, 8.0),
    ("T14i", 2900.0, 2930.0, -1, 8.0), ("T15i", 3026.0, 3118.0, +1, 10.0),
]

PIT_WALL_Y = float(SPEC["paddock"]["pit_wall_design_y"])            # +11.5
PIT_SOUTH_BARRIER_Y = 19.0                                          # spec §9
GARAGE_X0 = float(SPEC["paddock"]["garages_design"]["x"][0])        # -245.0
GARAGE_X1 = 130.0                                                   # spec §10.7
APRON_X0 = float(SPEC["paddock"]["apron_design"]["x"][0])           # -480.0

# The pit-straight overrides used to be HARD BOOLEAN MASKS.  DEFECT 1(b): a mask
# assignment changes the field in one sample at every edge, so `grass`, `asphalt`
# and `gravel` switched branch instantly and the barrier line stepped 46.31 m at
# s = 250 (side -1, where the pit mask ends and the T1 runoff zone — 45 m asphalt
# + 12 m gravel — was already at full weight) and 15.69 m at s = 3114.  They are
# `_ramp`-weighted blends now, on the same ramp the RUNOFF_ZONES use.
#
# 45 m, chosen to match the two pit-straight PINS that already existed alongside
# these masks (`_ramp(3430, 130, 45)` for the pit wall) and to sit inside the
# 30-60 m band every entry in RUNOFF_ZONES uses.  It is also half the 90 m the
# spec gives for a width transition either side of the pit straight, so the
# corridor's ramp is never slower than the section it wraps.
PIT_OVERRIDE_RAMP_M = 45.0


def _design_x_on_pit_straight(s):
    """design (= circuit) x for a station on the pit straight."""
    su = np.where(s < 250.0, s + LAP, s)
    return su - LAP


def _pit_straight_station(design_x):
    """Inverse of `_design_x_on_pit_straight`: circuit x -> lap station."""
    return float(design_x + LAP) % LAP


class _Corridor:
    """Station-sampled cross-section programme for both sides of the circuit."""

    def __init__(self):
        self.asph = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self.grav = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self.grass = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self.btype = {+1: np.full(NS, B_ARMCO), -1: np.full(NS, B_ARMCO)}
        self.fence = {+1: np.zeros(NS, bool), -1: np.zeros(NS, bool)}
        self.apex = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self.maxoff = {+1: np.full(NS, MAXOFF_NONE_M), -1: np.full(NS, MAXOFF_NONE_M)}
        self.pins = {+1: [], -1: []}
        self.off = {}
        self.off_declared = {}  # the line BEFORE the ownership cap (v1.2.0).
                                # `off` IS this until `_apply_ownership_cap()`
                                # runs at the end of S9b; after it, the two differ
                                # exactly where another leg owns the ground.
        self.prog = {}          # the runoff PROGRAMME's line, before the cap
        self.capped = {}        # ... after the cap, before the erosion
        self.wallw = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self.apronw = {+1: np.zeros(NS), -1: np.zeros(NS)}
        self._build()

    def _build(self):
        s = SGRID
        base = 18.0 + 7.0 * _fbm1(s / 260.0, seed=4001, oct=3)   # 18-25 m of grass
        for side in (+1, -1):
            self.grass[side] = base.copy()
            self.fence[side][:] = True

        for (lbl, s0, s1, side, asp, grv, btp, rmp) in RUNOFF_ZONES:
            w = _ramp(s0, s1, rmp)
            self.asph[side] = np.maximum(self.asph[side], w * asp)
            self.grav[side] = np.maximum(self.grav[side], w * grv)
            self.btype[side][w > 0.55] = btp
            if lbl == "T5":
                self.grass[side] = np.maximum(self.grass[side], w * 20.0)

        for (lbl, s0, s1, side, wid) in APEX_BEDS:
            self.apex[side] = np.maximum(self.apex[side], _ramp(s0, s1, 22.0) * wid)

        # doppler station: pin the barrier 4.00 m clear of the hovering camera,
        # which stands 26.0 m off the centreline on the RIGHT of S11 (spec §11)
        self.pins[-1].append((_ramp(2495.0, 2620.0, 55.0), 30.0))

        # --- pit straight overrides -----------------------------------------
        # DEFECT 1(b).  RAMPED, not masked.  The CONTINUOUS fields (grass,
        # asphalt, gravel) are blended with `_ramp` weights over
        # PIT_OVERRIDE_RAMP_M; the DISCRETE labels (btype, fence) keep a mask,
        # because a barrier is Armco or it is concrete and there is no half of
        # one — and the two indicator fields those labels feed (`wallw`,
        # `apronw`) are smoothed downstream, which is where their continuity
        # comes from.  `w >= 1.0` reproduces the old boolean masks EXACTLY, so
        # not one station changes barrier type.
        #
        # The mask edges are derived from the declared circuit-x extents rather
        # than written out, so a paddock change moves the ramp with the wall.
        w_pit = _ramp(_S_PIT_OPEN, _S_PIT_CLOSE, PIT_OVERRIDE_RAMP_M)
        # v1.1.1 / DEFECT #46.  The pit wall used to start at the DECLARED garage
        # frontage, `_pit_straight_station(GARAGE_X0)` = 3430.0 — 17.7 m before the
        # pit-exit road comes inboard of it, so the contract asked for a concrete
        # wall across the transit lane and build_architecture built one.  The wall
        # starts at the crossing now, and the open pit-exit apron runs up to it, so
        # the apron ENDS exactly where the wall BEGINS.  See §10a.
        s_lp0 = PIT_WALL_S0                               # 3447.73 (was 3430.0)
        s_lp1 = _pit_straight_station(GARAGE_X1)          #  130.0
        s_op0 = _pit_straight_station(APRON_X0)           # 3195.0
        w_lp = _ramp(s_lp0, s_lp1, PIT_OVERRIDE_RAMP_M)
        w_op = _ramp(s_op0, s_lp0, PIT_OVERRIDE_RAMP_M)
        E = verge_edge(s)
        # the DISCRETE label masks.  They are cut at the SAME station the pin ramps
        # to, so the label and the ramp cannot disagree about WHERE the wall starts.
        # (They still OVERLAP in their 45 m transitions — `_ramp` puts a transition
        # outside its span by design, so `wallw` and `apronw` are both ~1 within
        # PIT_OVERRIDE_RAMP_M of the boundary.  That is deliberate and unchanged.)
        dx = _design_x_on_pit_straight(s)
        x_lp0 = PIT_WALL_S0 - LAP                         # circuit x of the nose
        pit_m = w_pit >= 1.0
        lp_m = pit_m & (dx >= x_lp0) & (dx <= GARAGE_X1)
        op_m = pit_m & (dx > APRON_X0) & (dx < x_lp0)

        # south (right of travel): spec §9's barrier line at circuit y = -19,
        # and no runoff at all — the pit straight has a wall, not a gravel trap.
        self.grass[-1] = (self.grass[-1] * (1.0 - w_pit)
                          + (PIT_SOUTH_BARRIER_Y - E) * w_pit)
        self.asph[-1] *= (1.0 - w_pit)
        self.grav[-1] *= (1.0 - w_pit)
        self.pins[-1].append((_ramp(3160.0, 190.0, 70.0), PIT_SOUTH_BARRIER_Y))
        self.btype[-1][pit_m] = B_ARMCO

        # north (left of travel): the pit wall over the garages, open apron over
        # the pit exit, mown grass at the two ends.
        self.grass[+1] = (self.grass[+1] * (1.0 - w_lp)
                          + (PIT_WALL_Y - E) * w_lp)
        self.pins[+1].append((_ramp(s_lp0, s_lp1, PIT_OVERRIDE_RAMP_M), PIT_WALL_Y))
        self.btype[+1][lp_m] = B_CONCRETE
        self.fence[+1][lp_m] = False
        self.btype[+1][op_m] = B_NONE
        self.fence[+1][op_m] = False
        w_rest = np.clip(w_pit - w_lp - w_op, 0.0, 1.0)
        self.grass[+1] = (self.grass[+1] * (1.0 - w_rest)
                          + np.clip(self.grass[+1], 10.0, 26.0) * w_rest)

        # infield debris fence only where the infield is publicly accessible
        acc = np.zeros(NS, bool)
        for (a, b) in [(240.0, 470.0), (700.0, 1120.0), (1500.0, 1960.0),
                       (2680.0, 2960.0), (3300.0, LAP)]:
            acc |= (s >= a) & (s <= b)
        acc |= (s <= 250.0)
        self.fence[+1] &= acc

        # geometric clamp on the INSIDE of a corner: you cannot stand a barrier
        # 30 m inside a 28 m-radius hairpin.
        #
        # DEFECT 1(a) LIVED HERE.  The old code wrote the "no cap" sentinel as
        # 1e6 and then BOX-FILTERED the field:
        #
        #     cap  = np.full(NS, 1e6);  cap[inside_corner] = max(5, 0.5*R)
        #     capm = min-filter(cap, +-55 m)
        #     maxoff = np.convolve(capm, ones(41)/41)          <- THE DEFECT
        #
        # A mean is not a smoother when one of its inputs is a sentinel.  With a
        # single 1e6 left in the 41-sample window the mean is 1e6/41 = 24 390; with
        # none it is 14.0.  `np.minimum(raw, maxoff)` therefore went from "no cap"
        # to "14.0 m" IN ONE SAMPLE.  MEASURED on the shipped v1.0.1:
        #
        #     side  s      maxoff before -> after      barrier_offset before -> after
        #      +1   904    24403.902 ->    14.000       65.988 ->  14.000   51.99 m/m
        #      +1  1060       14.000 -> 24403.902       14.000 ->  35.398   21.40 m/m
        #      -1  1743       41.000 -> 24430.244       41.000 ->  56.255   15.26 m/m
        #      -1  1819    24436.098 ->    47.000       56.379 ->  47.000    9.38 m/m
        #      +1  2665    24414.634 ->    25.000       33.638 ->  25.000    8.64 m/m
        #
        # This is the step that put BR_Armco_L03/L04 and BR_FenceStruct_L03/L04
        # wall-to-wall across the T4 braking zone.  build_barriers §4b built a
        # cone-eroded taper by hand to survive it and handed the defect back.
        #
        # THE FIX.  The sentinel is finite and the box filter is gone: the cap is
        # published RAW (min-filtered only, which is a real geometric statement —
        # a 28 m hairpin caps its own inside for MAXOFF_REACH_M either side) and
        # the STEP IT LEAVES IN `np.minimum` IS TAKEN OUT BY CONE EROSION of the
        # finished line, below.  Erosion cannot be defeated by a step the way a
        # convolution can.
        _, _, _, kcur = centreline_arrays(s)
        Rloc = np.where(np.abs(kcur) > 1e-9, 1.0 / np.maximum(np.abs(kcur), 1e-9),
                        MAXOFF_NONE_M)
        for side in (+1, -1):
            ins = (np.sign(kcur) == side) & (np.abs(kcur) > 1e-9)
            cap = np.full(NS, MAXOFF_NONE_M)
            cap[ins] = np.maximum(5.0, 0.50 * Rloc[ins])
            capm = cap.copy()
            for sh in range(1, int(round(MAXOFF_REACH_M / PS)) + 1):
                capm = np.minimum(capm, np.roll(cap, sh))
                capm = np.minimum(capm, np.roll(cap, -sh))
            self.maxoff[side] = capm

        # freeze the offset field: a deterministic function of station alone
        for side in (+1, -1):
            margin = 1.5 + 1.2 * _fbm1(s / 90.0, seed=911 + (side > 0))
            runoff = _smax(self.asph[side] + self.grav[side], self.grass[side])
            prog = verge_edge(s) + _smax(runoff, 4.0) + margin
            for (w, target) in self.pins[side]:
                prog = prog * (1.0 - w) + float(target) * w
            self.prog[side] = prog
            self.capped[side] = np.minimum(prog, self.maxoff[side])
            self.off[side] = _cone_erode(self.capped[side],
                                         BARRIER_MAX_LATERAL_RATE)
            self.off_declared[side] = self.off[side].copy()

        # --- smooth weights derived from the barrier programme ---------------
        # A hard btype test would put a step in platform_edge and in ground_z at
        # the station where the type changes; both are consumed as continuous
        # fields, so the indicators are smoothed on the same 45 m as the pins.
        #
        # v1.1.0: where the region is DECLARED as a ramp (the pit wall, the pit
        # exit apron), the ramp is used directly instead of a box filter of its
        # own label.  A box filter of the label runs out over 22 m while the
        # declared ramp runs out over PIT_OVERRIDE_RAMP_M = 45 m, so the wall
        # MARGIN reopened to 6.0 m while the corridor was still 1.0 m wide, and
        # `platform_edge` came out INSIDE `barrier_offset + PLATFORM_MARGIN_M`
        # over 22 m at each end of the pit wall.  The box filter is kept as the
        # general case, unioned in, so a B_CONCRETE or B_NONE run declared
        # anywhere else still gets a smoothed indicator.  A declared ramp is C1
        # (a smoothstep); a box filter of a 0/1 label is only C0, and `apronw`
        # feeds ground_z's apron tie, so the difference is a crease in THE DATUM.
        # Tying `apronw` to the declared ramp also makes `apron_zone` equal 1.0
        # over EXACTLY the spec S10.7 rectangle (circuit x -480..-245, s 3195..
        # 3430); the box filter shrank it 23 m at each end, so 46 m of DECLARED
        # z = 0.000 apron was being handed the -1.6 % platform fall instead.
        ker = np.ones(45) / 45.0
        declared = {"wallw": {+1: w_lp, -1: np.zeros(NS)},
                    "apronw": {+1: w_op, -1: np.zeros(NS)}}
        for side in (+1, -1):
            for name, want in (("wallw", B_CONCRETE), ("apronw", B_NONE)):
                ind = (self.btype[side] == want).astype(np.float64)
                pad = np.concatenate([ind[-44:], ind, ind[:44]])
                sm = np.convolve(pad, ker, mode="same")[44:-44]
                sm = np.maximum(sm, declared[name][side])
                getattr(self, name)[side] = np.clip(sm, 0.0, 1.0)

        # empty zones: nothing above max_height inside the declared camera volumes
        self.zone_cap = {+1: np.full(NS, 99.0), -1: np.full(NS, 99.0)}
        for side in (+1, -1):
            X, Y, H, _ = centreline_arrays(s)
            o = self.off[side] * side
            px, py = world_to_circuit(X - np.sin(H) * o, Y + np.cos(H) * o)
            for zn in SPEC["empty_zones"]:
                inz = ((px >= zn["x"][0]) & (px <= zn["x"][1]) &
                       (py >= zn["y"][0]) & (py <= zn["y"][1]))
                self.zone_cap[side][inz] = np.minimum(
                    self.zone_cap[side][inz], float(zn["max_height_m"]))
            self.fence[side] &= (self.zone_cap[side] > 4.9)

    def sample(self, name, s, side):
        f = getattr(self, name)[side]
        x = np.asarray(s, float) % LAP
        if f.dtype == bool or name in ("btype",):
            i = (np.rint(x / PS).astype(np.int64)) % NS
            return f[i]
        return np.interp(x, SGRID, f, period=LAP)


# COR = _Corridor() USED TO BE BUILT HERE.  It is built at the end of §10 instead,
# because v1.1.1's `_pit_wall_start()` reads `access_edges` — THE PIT WALL'S EXTENT
# IS A FUNCTION OF WHERE THE PIT-EXIT ROAD RUNS, and a contract that pins the wall
# without asking the road is how the wall came to stand in the transit lane.  See
# §10's PIT WALL block.  Nothing between here and there evaluates COR at import
# time except `_MAX_PLATFORM`, which moved with it.


def runoff_widths(s, side):
    """-> dict of the runoff cross-section widths at (s, side), all in metres.

    asphalt / gravel / grass are measured OUTBOARD FROM verge_edge(s).
    `apex` is the apex-side gravel bed width, also from verge_edge.
    """
    return dict(asphalt=COR.sample("asph", s, side),
                gravel=COR.sample("grav", s, side),
                grass=COR.sample("grass", s, side),
                apex=COR.sample("apex", s, side))


def runoff_edge(s, side):
    """Centreline -> outboard edge of the built runoff (asphalt + gravel or grass)."""
    w = runoff_widths(s, side)
    return verge_edge(s) + _smax(_smax(w["asphalt"] + w["gravel"],
                                       w["grass"]), w["apex"])


def barrier_offset(s, side):
    """Centreline -> the BARRIER FACE, in metres, on `side`.

    A pure function of station.  build_barriers may add its own bounded lateral
    history jitter on top (|jitter| <= 0.25 m by contract) so a barrier line is not
    a drawing-board curve; nobody else may.

    v1.2.0: CLAMPED TO `owned_edge`.  Until v1.1.1 this was the runoff programme
    alone, and on 406 of 14 700 stations it put the barrier face inside ANOTHER
    LEG of the same circuit — 7.493 m in at worst, on that leg's centreline.  See
    S9b, and `barrier_offset_declared` for the pre-ownership line.
    """
    return COR.sample("off", s, side)


def barrier_offset_declared(s, side):
    """The barrier face BEFORE the ownership cap — the v1.1.1 line, unchanged.

    Published for provenance and for the gate in selftest [17], which needs an
    artefact already known to be bad to fail against.  NOBODY SHOULD BUILD ON
    THIS: on side +1 it reaches 7.493 m into another leg's racing surface.
    """
    return COR.sample("off_declared", s, side)


BARRIER_JITTER_MAX_M = 0.25


def barrier_type(s, side):
    """-> B_ARMCO / B_TECPRO3 / B_CONCRETE / B_NONE at (s, side)."""
    return COR.sample("btype", s, side)


def fence_allowed(s, side):
    """-> bool: may a 3.6 m debris fence stand here (access + empty-zone rules)."""
    return COR.sample("fence", s, side)


def apron_zone(s, side):
    """0..1: how much this station's platform is the DECLARED PIT-EXIT APRON.

    1 over circuit x -480..-245 on the left of the pit straight (s 3200..3420),
    0 everywhere else, smoothly.  Where this is > 0.5 the platform surface outboard
    of verge_edge is unrubbered concrete built by build_architecture, not runoff
    built by build_barriers, and `ground_z` ties it to APRON_Z (see APRON_TIE_M).
    """
    return COR.sample("apronw", s, side)


def platform_owner(s, side):
    """Who lays the surface outboard of verge_edge at (s, side)."""
    return np.where(apron_zone(s, side) > 0.5, OWNER_APRON, OWNER_ROAD)


# ===========================================================================
#  9.  THE ROAD CORRIDOR  —  the hole the terrain module cuts
# ===========================================================================
#
# build_terrain's height field is a CELL = 2.5 m grid.  A track edge is a 3675 m
# curve with a 1 cm tolerance.  A 2.5 m grid cannot represent it, so "blend the
# terrain into the road" is not an available move: at best it produces a 2.5 m
# sawtooth along both edges of the circuit, and at worst — which is what happened —
# it produces TER_Ground standing 0.381 m PROUD OF THE TARMAC over 5.3 % of the
# racing surface and burying 50 555 m2 of runoff asphalt, 42 419 m2 of gravel and
# 240 000 individually generated stones.
#
# So it is a HOLE.
#
#   platform_edge(s, side)   the outboard limit of the road programme.  Everything
#                            inboard of it is built by build_surface (to
#                            verge_edge) and build_barriers (verge_edge outward).
#                            Terrain creates NO ground geometry inside it.
#
#   corridor_rim(s, side)    the world-space point where terrain's first ring of
#                            vertices must sit, and the z it must sit at.  Terrain
#                            welds to this polyline and blends outward into natural
#                            ground over CORRIDOR_BATTER_M.
#
# Vegetation is the exception and is deliberately so: terrain MAY scatter grass,
# weeds and gravel-edge planting inside the corridor — the verges want it and the
# user has asked for it — but it must place them with `ground_z`, never with its
# own height field, and never inside the runoff asphalt or the gravel beds
# (`runoff_widths`).  That is the whole of "not a grass gray line": the runoff is
# visible because terrain no longer paves over it, and the verge is alive because
# terrain still plants on it.

PLATFORM_MARGIN_M = 6.0        # ground the road programme builds beyond the
                               # barrier / runoff, for the Armco foot, the fence
                               # posts and a mown shoulder
PLATFORM_MARGIN_WALL_M = 0.6   # ... but only a footing where the barrier is a
                               # solid CONCRETE wall, because the ground behind a
                               # pit wall belongs to the pit lane, not to us
CORRIDOR_BATTER_M = 34.0       # terrain's blend length from the rim into nature


def platform_edge(s, side):
    """Centreline -> the outboard limit of the road programme (m).

    Everything inboard of this is built by build_surface (to verge_edge) and
    build_barriers (verge_edge outward).  build_terrain builds no ground here and
    build_architecture paves none of it.
    """
    w = COR.sample("wallw", s, side)
    m = PLATFORM_MARGIN_M + (PLATFORM_MARGIN_WALL_M - PLATFORM_MARGIN_M) * w
    return _smax(barrier_offset(s, side), runoff_edge(s, side)) + m


def _platform_edge_declared(s, side):
    """`platform_edge` built on `barrier_offset_declared`.

    THE INPUT TO THE OWNERSHIP SOLVE, and it must be the DECLARED line, not the
    capped one: the solve asks "how far out does this station's corridor reach
    before another leg is nearer", and the honest lateral range to search is the
    one the runoff programme asked for before anything clamped it.  Using the
    capped line would make the solve a fixed point of itself, and would stop
    `owned_edge` from being the same array `build_barriers` S4b has been running
    on the shipped world.
    """
    w = COR.sample("wallw", s, side)
    m = PLATFORM_MARGIN_M + (PLATFORM_MARGIN_WALL_M - PLATFORM_MARGIN_M) * w
    return _smax(barrier_offset_declared(s, side), runoff_edge(s, side)) + m


# _MAX_PLATFORM moved to the end of §10 with COR — it is the only import-time
# evaluation between here and there that needs the corridor to exist.


def corridor_rim(s, side):
    """-> (x, y, z) world, the rim of the road corridor.  Terrain welds here."""
    e = platform_edge(s, side)
    return su_to_world(s, e * side)


def corridor_rim_polyline(side, ds=2.0):
    """Closed world-space polyline (N, 3) of one side of the corridor rim."""
    S = np.arange(0.0, LAP, float(ds))
    return corridor_rim(S, side)


# --------------------------------------------------- THE TRANSIT KEEP-OUT, v1.1.1
# DEFECT #46's SECOND OBJECT.  The worse of the two placement violations was not
# the pit wall, it was `ARCH_RetainEdge` at 1.198 m into the car's path — the
# retaining edge build_architecture stands along `corridor_rim` wherever the ground
# just outboard of the rim belongs to the paddock platform.
#
# THE RIM ITSELF CROSSES THE TRANSIT LANE.  `platform_edge(s, +1)` runs 30.92 m at
# s = 3400, 22.73 at 3410 and 12.28 at 3429 while the car crosses the same stations
# at u = 26.0, 22.9 and 15.9, so the two lines cross at s ~= 3405 and from there
# east the corridor rim lies INBOARD of the transit route.  That is correct and
# intended — the transit deliberately leaves the circuit and crosses the paddock —
# but it means the rim is a line you may not build ON for 40 m of its length, and
# nothing said so.  `_fc_clearance` (the showroom forecourt) was the only keep-out
# build_architecture applied.
#
# So the contract states it, once, for every module that stands anything on a
# corridor rim: barrier terminal, retaining edge, fence post, kerb, bollard.
TRANSIT_KEEPOUT_M = 1.20     # LATERAL keep-out beyond the ribbon edge for anything
                             # that STANDS ON the ground.  Calibrated on the gate
                             # the world is measured with: tools/placement_gate.py
                             # sweeps the car body's 1.0025 m half-width plus a
                             # 0.60 m margin, and the transit line runs 1.00 m
                             # inside the ribbon's outboard edge where it crosses
                             # the rim, so the swept volume reaches 0.60 m past the
                             # ribbon edge.  1.20 m leaves 0.60 m of air between the
                             # swept volume and anything standing here.
                             #
                             # It is NOT `ACCESS_CORRIDOR_MARGIN_M` (3.0), which is
                             # terrain's height-field keep-out, and it is NOT
                             # `ACCESS_RIBBON_SAW_M` (0.30), which is paving's joint.
                             # Three different questions about the same edge; the
                             # contract has now been bitten by conflating two of
                             # them once already (see in_access_ribbon).


def transit_keepout(x, y, margin=None):
    """True where nothing that STANDS ON THE GROUND may be built.

    The Beat-4 transit lane plus `TRANSIT_KEEPOUT_M`.  Ground surfaces are fine —
    the car drives on them — and so is anything at ribbon level.  This is for
    objects with height: walls, retaining edges, posts, kerbs, terminals.

    v1.2.0: THE UNION OF THE DECLARED ROAD AND THE DRIVEN LINE.  Until v1.1.1
    this was the ribbon alone, and the car does not stay on the ribbon: the
    telemetry's merge is a straight chord where this file's is an R150 arc, and
    the swept car box runs up to 4.647 m OUTBOARD of the ribbon's own edge over
    60.1 m of the transit (see the v1.2.0 D1 note and S10c).  A keep-out derived
    from the ribbon alone therefore leaves the car's actual path unprotected —
    which is exactly how `ARCH_PitWall` and `ARCH_RetainEdge` ended up inside the
    car body at 200+ km/h.  The union is the correct answer WHICHEVER of the two
    curves is eventually declared right, so it does not have to wait for that
    argument to be settled.
    """
    m = TRANSIT_KEEPOUT_M if margin is None else float(margin)
    return in_access_ribbon(x, y, margin=m) | transit_drive_keepout(x, y)


def rim_buildable(s, side, ds=None):
    """True where a module may STAND something on the corridor rim at (s, side).

    False where the rim runs through the transit keep-out, AND false where the rim
    is beyond the ground this station's corridor OWNS.  Ask this before laying a
    retaining edge, a barrier terminal or a fence along `corridor_rim`.

    v1.2.0 added the ownership term, and it was not theoretical: MEASURED against
    telemetry.csv on v1.1.1, `corridor_rim(s, +1)` lies inside the car's swept
    volume at 62 of 14 700 stations, and this function said BUILDABLE at 30 of
    them — s 764..917, worst 1.481 m in, where the T3 runoff's 72.8 m rim reaches
    across onto the S4/T5 leg the car is driving at speed.  `build_architecture`
    happens not to build there today because its own `PLAT_RECTS` test excludes
    it; nothing in the CONTRACT said so, and 435 item agents read this function.
    """
    S = np.atleast_1d(np.asarray(s, float))
    p = np.atleast_2d(corridor_rim(S, side))
    own = np.asarray(platform_edge(S, side) <= owned_edge(S, side) + 1e-9, bool)
    return (~transit_keepout(p[:, 0], p[:, 1])) & own


def road_corridor_mask(x, y, margin=0.0, ribbon_margin=None):
    """True where the ROAD PROGRAMME owns the ground and terrain must not build.

    Covers the 3675 m lap corridor out to `platform_edge` on both sides, plus the
    access ribbon and the Beat-4 walled corridor.  `margin` shrinks (negative) or
    grows (positive) the region; terrain should cut at margin = 0 and may test
    with a small positive margin when deciding which grid cells to drop entirely.

    `ribbon_margin` overrides `ACCESS_CORRIDOR_MARGIN_M` for the ribbon term alone.
    THE TWO MARGINS ARE DIFFERENT THINGS AND CONFLATING THEM COST 64 m2 OF GROUND:

      * `ACCESS_CORRIDOR_MARGIN_M` = 3.0 is how far outboard of the ribbon edge
        TERRAIN must keep its height field, because the Beat-4 corridor walls stand
        at +8.0 / -7.0 against a 6.0 m ribbon half-width and their footings need
        ground the road programme controls.  It is a KEEP-OUT for a 2.5 m grid.
      * `ACCESS_RIBBON_SAW_M` = 0.30 is how far outboard of the ribbon edge PAVING
        must stop, so build_surface's sawn edge strip and build_architecture's slab
        meet at a joint instead of interpenetrating.  It is a JOINT.

    Terrain's keep-out is not architecture's joint.  Subtracting the 3.0 m keep-out
    from the declared apron (which is what `apron_platform_mask` used to do) left a
    3 m strip either side of the ribbon that terrain had cut and architecture had
    not paved — while `world_ground_z` said, correctly, that architecture owned it.
    `apron_platform_mask` therefore subtracts the ribbon at the SAW margin, and only
    terrain uses the keep-out.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    out = np.zeros(x.shape, bool)
    near = _near_circuit(x, y, _MAX_PLATFORM + max(margin, 0.0) + 1.0)
    if near.any():
        s, u = project(x[near], y[near])
        lim = np.where(u >= 0.0, platform_edge(s, +1), platform_edge(s, -1)) + margin
        out[near] = np.abs(u) <= lim
    rm = ACCESS_CORRIDOR_MARGIN_M if ribbon_margin is None else float(ribbon_margin)
    rib = _near_circuit(x, y, _MAX_PLATFORM) | (
        (x > ACCESS_GLASS_X - 20.0) & (x < 250.0) & (y > -40.0) & (y < 120.0))
    if rib.any():
        out[rib] |= in_access_ribbon(x[rib], y[rib], margin=rm + margin)
    return out


# ===========================================================================
# 10.  THE TRANSIT ROUTE, THE ACCESS RIBBON AND THE BEAT-4 CORRIDOR
# ===========================================================================
#
# spec §10.5.  Three legs of geometry that the camera crosses in one take, and the
# place the assembled world came apart worst.
#
#   * SURF_AccessRoad, ARCH_Paving_Paddock, ARCH_Paving_Apron and ARCH_Markings all
#     covered the same 116 m of ground at separations of 1.4-9.0 mm, and the
#     winning surface flipped six times along the route.  At 4K with a flying
#     camera that is stroboscopic depth fighting through the beat the brief calls
#     "the world-design linchpin".
#   * The walled corridor was built twice, 0.5 m apart: BR_Transit_* at
#     +8.0 / -7.0 and ARCH_ApronCorridor at +8.5 / -7.5.
#
# THE DECISIONS
#
#   OWNERSHIP OF THE RIBBON.  build_surface owns the driving surface of the
#   transit route — it is a road, it is continuous with the racing surface it
#   merges into, and it must share that surface's datum exactly or the merge is a
#   seam at 219.5 km/h.  build_architecture CUTS ITS PAVING to
#   `access_ribbon_polygon()` and lays no slab, no marking and no drain inside it.
#   Markings on the ribbon are build_surface's.
#
#   THE RIBBON IS DEAD FLAT AT z = 0.000 FOR THE FIRST 49.6 m.  Not crowned.
#   spec §10.3(b) requires the first 50 m outside the glass to be exactly 0 % and
#   exactly level with the interior floor so the breach debris "keeps travelling on
#   the plane it started on"; §10.5 says "the apron, the road and the racing
#   surface are one plane at z = 0.000".  build_surface's -0.0125*|u|^1.7 crown put
#   the ribbon edge 75 mm below the apron and violated both.  Over the merge arc
#   the ribbon eases from that plane onto `ground_z`, and past the merge point it
#   IS `ground_z`, so the join to SURF_Track is exact by construction.
#
#   THE RIBBON IS CLIPPED TO THE OUTSIDE OF verge_edge.  The R150 arc converges on
#   the pit straight; unclipped, the ribbon's inboard edge crosses the track
#   centreline and lies 74 mm under SURF_Track for the last stretch of the merge.
#   `access_edges` returns the clipped inboard edge.  The car still merges "inside
#   the track edge" as spec §10.5 requires — it drives across the painted verge,
#   which on the pit straight is plain asphalt because no kerb is planned there.
#
#   THE WALLED CORRIDOR IS BUILT BY build_barriers.  Reasons, in order:
#     1. It is safety furniture — a retaining wall, a belted tyre stack, a debris
#        fence and a portal.  Every one of those is a build_barriers primitive with
#        a per-unit variation model; build_architecture's version is loose tyres
#        intersecting a concrete plinth.
#     2. build_barriers already isolated its version into a BR_Transit collection
#        "so they can be deleted wholesale if that module builds them too".  It
#        does not need to be.
#   ARCH_ApronCorridor is DELETED — by name, see CORRIDOR_DELETE_NAMES.
#
#   THE EXTENT.  Neither of the two built versions was right, and neither was the
#   spec.  Measured along the route with `project` against `verge_edge` (this is
#   the --selftest table):
#
#       route t   south wall face      clearance to the painted verge edge
#          75 m   circuit y +19.47                8.967 m
#          85 m   circuit y +14.49                3.992 m
#          90 m   circuit y +12.24                1.737 m
#          93 m   circuit y +10.96                0.460 m   <- old BR_Transit end
#          95 m   circuit y +10.14               -0.359 m   <- ON the verge
#
#     so the spec's "middle 90 m of the apron run" at a constant -7.0 m offset is
#     not buildable: the R150 merge arc converges on the pit straight and the
#     south wall runs out of road at t = 95.  build_architecture found the same
#     wall (its own arithmetic put the collision at its s = 90, which is this
#     t = 102) and solved it by shortening the whole corridor to 70 m and starting
#     it 12 m later, which throws away 20 m of the camera's walled run to fix a
#     problem that only the south wall has.
#
#     The corridor is therefore ASYMMETRIC, which is also what a real pit exit is:
#
#       north retaining wall   t = 6.0 -> 96.0   90.0 m, the spec literal.
#                              Worst approach to the racing surface 14.2 m; it
#                              ends on open apron at circuit (-269, +24).
#       south tyre wall+fence  t = 6.0 -> 90.0   84.0 m, terminated where its face
#                              still has 1.74 m of verge in front of it, with a
#                              proper barrier terminal, because beyond that point
#                              the pit exit is merging and a wall between the road
#                              and the track is exactly the wrong object.
#
#     Both start at t = 6.0 (world x = 21.0) rather than the old 3.0: the forecourt
#     bollard line stands at world x = 19.5 with bollards at y = +-9.0, and a wall
#     face at y = +8.0 / -7.0 starting before x = 21 fouls them and crowds the
#     facade at the frame where the camera clears the glass.
#
#     The camera therefore flies 90 m of corridor, walled on both sides for 84 m
#     of it, and the wall that peels away first is the one on the side the road is
#     about to merge into.  That is a motivated reveal, not a compromise.

ACCESS_L1 = 11.98                       # dais -> glass, inside (spec §10.5 leg 1)
ACCESS_L2 = 49.60                       # glass -> merge start (leg 2), FLAT
ACCESS_R = 150.0                        # merge arc radius (leg 3)
ACCESS_ARC_DEG = 40.0
ACCESS_L3 = ACCESS_R * math.radians(ACCESS_ARC_DEG)      # 104.7198
ACCESS_MERGE = ACCESS_L2 + ACCESS_L3                     # 154.3198
ACCESS_BLEND = 90.0                     # spec §10.5: "blends the last 5 m
                                        # laterally over 90 m"
ACCESS_TOTAL = ACCESS_MERGE + ACCESS_BLEND               # 244.3198
ACCESS_HALF_W = ACCESS_ROAD_W * 0.5                      # 6.0
ACCESS_ARC_C = (64.60, 150.00)          # merge arc centre, world
ACCESS_GLASS_X = 15.0                   # the breach plane
ACCESS_MERGE_LATERAL = 5.02             # spec §10.5: the arc ends 5.02 m left of
                                        # the pit-straight centreline
ACCESS_CORRIDOR_MARGIN_M = 3.0          # TERRAIN'S KEEP-OUT beyond the ribbon edge,
                                        # for the Beat-4 corridor wall feet (+8.0 /
                                        # -7.0 against a 6.0 m half-width).  Lateral
                                        # only — see in_access_ribbon.
ACCESS_RIBBON_SAW_M = 0.30              # PAVING'S JOINT with the ribbon: the sawn
                                        # edge strip, and access_ribbon_polygon()'s
                                        # default margin.  build_architecture's
                                        # RIBBON_SAW_M is this number.

APRON_Z = 0.000                         # spec §10.5: the apron IS the z = 0 plane

# ------------------------------------------------------- THE TRACK/APRON JOINT
# DEFECT 4.  These two numbers were read by BOTH build_surface (line 136) and
# build_architecture (line 121) as `float(getattr(C, name, default))`, and they
# agreed only because the two files happened to carry the same fallback literal.
# That is not agreement, it is a coincidence with a version number: change one
# fallback and the asphalt lap and the concrete slab part company silently, over
# 241 m of pit straight, at a 5 mm sealant invert nobody would see until it was
# rendered.  RULE 1 of this module's own docstring already required them here.
#
# The joint: build_surface carries SURF_Track's asphalt edge OUTBOARD past
# `verge_edge(s)` by APRON_JOINT_LAP_M as a real recessed sealant joint
# (SURF_ApronJoint), APRON_JOINT_DEPTH_M deep.  build_architecture's paving slab
# BEGINS on the outer end of that lap, at `verge_edge(s) + APRON_JOINT_LAP_M`.
# The two meet AT A DECLARED JOINT rather than at a tolerance, which is the same
# rule TOL_COPLANAR_M states: cut, do not offset.
#
# Both modules keep their `getattr(C, ..., default)` form, so a builder pinned to
# a v1.0.x contract still works; from v1.1.0 on, the getattr finds these.
APRON_JOINT_LAP_M = 0.050               # 50 mm of asphalt lap past verge_edge
APRON_JOINT_DEPTH_M = 0.005             # 5 mm sealant invert in the lap


def access_route_point(t):
    """Route centreline at t metres from the glass plane (world x = +15).

    -> (x, y, heading_rad).  Straight for t <= 49.60, then the R150 / 40 deg left
    merge arc, then straight along the pit-straight heading.
    """
    t = float(t)
    if t <= ACCESS_L2:
        return (ACCESS_GLASS_X + t, 0.0, 0.0)
    if t <= ACCESS_MERGE:
        a = (t - ACCESS_L2) / ACCESS_R
        return (ACCESS_ARC_C[0] + ACCESS_R * math.sin(a),
                ACCESS_ARC_C[1] - ACCESS_R * math.cos(a), a)
    ang = math.radians(ACCESS_ARC_DEG)
    d = t - ACCESS_MERGE
    return (161.02 + math.cos(ang) * d, 35.09 + math.sin(ang) * d, ang)


def access_route_arrays(T):
    """Vectorised `access_route_point` -> (X, Y, H)."""
    T = np.asarray(T, float)
    X = np.empty_like(T); Y = np.empty_like(T); H = np.empty_like(T)
    m1 = T <= ACCESS_L2
    X[m1] = ACCESS_GLASS_X + T[m1]; Y[m1] = 0.0; H[m1] = 0.0
    m2 = (T > ACCESS_L2) & (T <= ACCESS_MERGE)
    a = (T[m2] - ACCESS_L2) / ACCESS_R
    X[m2] = ACCESS_ARC_C[0] + ACCESS_R * np.sin(a)
    Y[m2] = ACCESS_ARC_C[1] - ACCESS_R * np.cos(a)
    H[m2] = a
    m3 = T > ACCESS_MERGE
    ang = math.radians(ACCESS_ARC_DEG)
    d = T[m3] - ACCESS_MERGE
    X[m3] = 161.02 + math.cos(ang) * d
    Y[m3] = 35.09 + math.sin(ang) * d
    H[m3] = ang
    return X, Y, H


def access_edges(T):
    """Ribbon edges at route stations T.

    -> (v_in, v_out): signed lateral offsets from the ROUTE centreline, positive to
    the left of travel, of the inboard (track-side, right) and outboard (left)
    edges.  v_in is clipped so the ribbon never overlaps the racing surface's own
    cross-section, and the outboard edge tapers into the track edge over the last
    90 m so the apron dies as a gore rather than a step.
    """
    T = np.atleast_1d(np.asarray(T, float))
    X, Y, H = access_route_arrays(T)
    S, U = project(X, Y)                       # where the route sits w.r.t. the lap
    E = verge_edge(S)                          # track cross-section outer edge

    v_out = np.full(T.shape, ACCESS_HALF_W)
    gore = T > ACCESS_MERGE
    if gore.any():
        f = np.clip((T[gore] - ACCESS_MERGE) / ACCESS_BLEND, 0.0, 1.0)
        v_end = E[gore] - U[gore]              # the track edge, in route coords
        v_out[gore] = ACCESS_HALF_W * (1.0 - f) + v_end * f

    # the inboard edge may not cross the racing surface's outer edge
    v_in = np.maximum(-ACCESS_HALF_W, E - U)
    v_in = np.minimum(v_in, v_out)
    return v_in, v_out


def ribbon_edge_u(s, which="out"):
    """The access ribbon's edge AT LAP STATION s, in lap coordinates (signed u).

    -> `u` of the ribbon's outboard ("out") or inboard ("in") edge, or NaN at any
    station the ribbon does not reach.  Scalar or array.

    DEFECT #47, v1.1.1, AND IT IS RULE 1 AGAIN.  Three modules cut to the ribbon's
    outboard edge and all three found it for themselves:

      build_surface       lays the ribbon, so it HAS the edge exactly
      build_barriers      swept u in 0.10 m steps asking `in_access_ribbon`, took
                          the last sample INSIDE, and then stood off it by
                          `ACCESS_RIBBON_SAW_M` = 0.30 m
      build_architecture  cuts its slab at the same 0.30 m through `apron_clearance`

    MEASURED on the assembled world at 0.5 x 0.10 m: **22.95 m2** of ground with no
    surface on it at all, in a 0.20-0.30 m wide strip running from u ~= 11.0 to
    u ~= 11.2 over s 3455-3560, bounded by `SURF_AccessRoad` on one lip and
    `BR_Verge_L` on the other, their rims 8-22 mm apart in z.  It is the 0.30 m
    stand-off, plus up to 0.10 m of the sweep's own quantisation, and nobody laid it.

    `ACCESS_RIBBON_SAW_M` IS PAVING'S JOINT.  Its docstring says so: it exists so
    build_architecture's PRECAST SLAB and build_surface's sawn edge meet at a joint
    instead of interpenetrating.  build_barriers lays hot asphalt on the same datum;
    there is nothing to saw, so it butts.  Both surfaces come from `ground_z`, so a
    butt joint is EXACT and not toleranced — the same argument `in_access_ribbon`
    makes about the glass plane.

    This function is the edge, published once, to 1 mm.
    """
    scalar = np.ndim(s) == 0
    S = np.atleast_1d(np.asarray(s, float)) % LAP
    tab = _RIB_EDGE_U[0 if which == "out" else 1]
    i = np.rint(S / _RIB_EDGE_BIN).astype(np.int64) % len(tab)
    v = tab[i]
    return float(v[0]) if scalar else v


def access_z(t, v):
    """Ribbon surface z at route station t, lateral v (signed, + left of travel).

    RETIRED AS A SEPARATE DATUM IN v1.1.0.  THIS IS `ground_z`, EXPRESSED IN ROUTE
    COORDINATES, AND NOTHING ELSE.  It is kept as a named function only because
    nine call sites in four modules read it; it is a coordinate change, not a
    second answer, and a caller may replace it with
    `ground_z(*project(x, y))` at any time.

    DEFECT 3, and it is the clean example of why the contract has RULE 1.  v1.0.x
    eased from a flat apron onto `ground_z` with a weight that was a function of
    the ROUTE STATION t ALONE, completing at the merge point t = 154.32.  But the
    ribbon starts SHARING AN EDGE with SURF_Track at t = 95.33.  Along the 149.3 m
    of shared edge the two answers differed by up to 80.2 mm, and by up to 90.2 mm
    somewhere on the ribbon — 9x TOL_SEAM_M, on a boundary two modules share, in
    the beat the camera flies at rooftop height.  build_surface measured it,
    routed around it and handed it back (build_surface.md §5.4); build_terrain,
    build_architecture and items/access_road_slab did not, and were building to
    the wrong one of the two.

    NOTHING IS LOST.  spec §10.3(b)'s "the first 50 m outside the glass exactly
    0 % and exactly level with the interior floor" still holds EXACTLY rather than
    to a tolerance, because `ground_z` is already identically APRON_Z = 0.000000
    over the whole 49.60 m apron run and 0.30 m beyond both ribbon edges — the
    contract's own apron tie (§7) does it, `apron_zone` being 1.000 along the
    whole approach.  --selftest measures both claims on every run.
    """
    T = np.atleast_1d(np.asarray(t, float))
    V = np.atleast_1d(np.asarray(v, float))
    T, V = np.broadcast_arrays(T, V)
    X, Y, H = access_route_arrays(T)
    S, U = project(X - np.sin(H) * V, Y + np.cos(H) * V)
    z = ground_z(S, U)
    if np.ndim(t) == 0 and np.ndim(v) == 0:
        return float(z.reshape(-1)[0])
    return z


_RT = np.linspace(0.0, ACCESS_TOTAL, 981)
_RX, _RY, _RH = access_route_arrays(_RT)


def access_project(x, y, chunk=20000):
    """world (x, y) -> (t, v) on the ACCESS ROUTE.  v signed, + left of travel."""
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    n = x.size
    TT = np.empty(n); VV = np.empty(n)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        dx = x[a:b, None] - _RX[None, :]
        dy = y[a:b, None] - _RY[None, :]
        j = np.argmin(dx * dx + dy * dy, axis=1)
        h = _RH[j]
        ex = x[a:b] - _RX[j]; ey = y[a:b] - _RY[j]
        TT[a:b] = _RT[j] + ex * np.cos(h) + ey * np.sin(h)
        VV[a:b] = -ex * np.sin(h) + ey * np.cos(h)
    return TT, VV


_RVIN, _RVOUT = access_edges(_RT)


# ------------------------------------------------- THE RIBBON'S EDGES, BY STATION
# Built once, at 1 mm of lateral resolution, by sweeping the declared edges into
# world space and re-projecting them onto the lap.  Stations the ribbon never
# reaches carry NaN, so a caller cannot silently extrapolate an edge across the
# 240 m of pit straight the ribbon is nowhere near — which is exactly the mistake
# `np.interp` makes on a station axis covered only in patches.
_RIB_EDGE_BIN = 0.25


def _build_ribbon_edge_u():
    T = np.linspace(0.0, ACCESS_TOTAL, 48001)
    X, Y, H = access_route_arrays(T)
    vin, vout = access_edges(T)
    n = int(round(LAP / _RIB_EDGE_BIN))
    out = []
    for V, agg in ((vout, np.maximum), (vin, np.minimum)):
        S, U = project(X - np.sin(H) * V, Y + np.cos(H) * V)
        tab = np.full(n, np.nan)
        idx = (np.rint(S / _RIB_EDGE_BIN).astype(np.int64)) % n
        for k in range(len(idx)):
            j = idx[k]
            tab[j] = U[k] if np.isnan(tab[j]) else float(agg(tab[j], U[k]))
        out.append(tab)
    return out


_RIB_EDGE_U = _build_ribbon_edge_u()


# ===========================================================================
# 10c.  THE DRIVEN TRANSIT LINE   —   R2-042, v1.2.0, SETTLED IN v1.2.1
# ===========================================================================
#
# READ THIS FIRST, v1.2.1.  EVERYTHING BELOW IS THE STATE OF PLAY BEFORE R2-042
# WAS DECIDED, AND IT IS KEPT BECAUSE THE MEASUREMENTS IN IT ARE STILL THE REASON
# THIS BLOCK EXISTS.  What has changed since:
#
#   * R2-042 IS DECIDED (docs/R2-042-DECISION.md).  The declared R150 / 40 deg arc
#     is the road.  `tools/build_telemetry.py` now evaluates the transit merge
#     analytically off the ACCESS_* constants instead of interpolating the four
#     leg endpoints, so THE CONTRACT AND THE TELEMETRY NO LONGER DISAGREE:
#     telemetry.csv reproduces `access_route_arrays` to 8.83e-05 m over the 99
#     apron+merge frames, of which 5e-5 m is the CSV's own 4-dp write quantum.
#   * THE 9.044 m IS STILL THERE, ON THE OTHER SIDE.  It is now the distance from
#     the artefact to `transit_drive_arrays` — the CHORD this block publishes,
#     9.0407 m measured.  So every sentence below that reads "the car is 9.044 m
#     off the route" should now be read as "the chord is 9.044 m off both".
#   * THE CHORD IS STILL PUBLISHED and `transit_keepout` is still the UNION of it
#     and the ribbon.  That union was conservative under both readings and stays
#     conservative under the settled one; it costs nothing and it is what
#     `PIT_WALL_S0` and the placement gate were re-derived against.  Do not narrow
#     it to the ribbon without re-running the gate.
#   * `build_barriers` S21's private workaround IS GONE.  It read telemetry.csv
#     directly and pushed the Beat-4 corridor's north wall outboard to stay clear
#     of the chord-driven car.  MEASURED both ways before deleting: against the
#     pre-R2-042 CSV it pushed the north wall +3.347 m over 32.4 m; against the
#     corrected CSV, and with the table removed, +0.000 m on both walls.  The
#     corridor walls now stand on TRANSIT_NORTH_OFFSET_M / _SOUTH_ exactly.
#
# ---- as written for v1.2.0, before the decision ---------------------------
#
# THE CONTRACT AND THE TELEMETRY DISAGREE ABOUT WHERE THE CAR IS, BY 9.044 m.
#
# `access_route_point` above merges onto the pit straight on the declared R150 /
# 40 deg arc.  `tools/build_telemetry.py` — the file MASTER-PLAN calls "THE single
# source of truth for motion", the file the camera rig, the audio mix and
# `tools/placement_gate.py` all read — builds the same merge out of
# `SPEC["transit"]["legs"]` by LINEARLY INTERPOLATING the four leg endpoints:
#
#     tx = np.interp(tr_s, cum, [p[0] for p in pts])      build_telemetry.py:281
#
# A 104.72 m arc of radius 150 stands 150*(1 - cos(20 deg)) = 9.04 m off its own
# chord, and the chord is on the OUTBOARD side.  So the car in telemetry.csv
# drives up to 9.044 m to the LEFT of the road this file declares.  MEASURED, the
# CSV re-projected onto `access_route_arrays`:
#
#     route t      0..45     59.6    76.7    86.3   96.6..107.5   130.4   154.0
#     car v        +0.00    +3.23   +7.02   +8.28    +8.95..9.04  +6.47   +0.13
#
# and against the ribbon's own outboard edge (+6.00 m over the merge), the car's
# CENTRE is up to 3.044 m outside its road and its SWEPT BOX up to 4.647 m
# outside, over 60.1 m of the transit.  (Those are the line sampled at 0.01 m;
# at the telemetry's own 24 fps frames the same three numbers read 9.0406,
# 3.041 and 4.643 — selftest [18] prints the frame-sampled ones, because the
# frames are the artefact and the dense line is the model of it.)
#
# THIS IS THE SAME SHAPE AS THE `barrier_offset` DEFECT: two modules consuming the
# same offset and disagreeing about it.  Its consequences are the two placement
# violations that started this thread —
#
#     car_path  ARCH_RetainEdge  1.198 m in  at (138.431, 27.140, -0.179)
#     car_path  ARCH_PitWall     1.067 m in  at (144.282,  29.425, +0.200)
#
# — because every keep-out v1.1.1 published (`transit_keepout`, `rim_buildable`,
# `_pit_wall_start`) was derived from the RIBBON while the gate measures the
# TELEMETRY.  v1.1.1 cleared both objects, but by luck: the ribbon's crossing of
# `PIT_WALL_Y` happens to fall 1.70 m LATER than the driven box's.
# `build_barriers` S21 found the same divergence independently, and carried a
# private workaround that read telemetry.csv directly and ended
# "Delete this the day the telemetry and access_route_point agree."
# THAT DAY CAME.  S21 was measured a no-op against the corrected telemetry and
# deleted in v1.2.1; see the v1.2.1 note at the head of this section.
#
# WHAT THIS BLOCK DOES, AND WHAT IT DELIBERATELY DOES NOT DO.
#
#   It publishes the DRIVEN line, derived HERE from the SAME spec block
#   build_telemetry integrates.  That is RULE 1 satisfied without breaking
#   RULE 2 — the contract still reads nothing but SPEC, numpy and the standard
#   library, and it still does not read telemetry.csv.  WHEN WRITTEN, this
#   polyline reproduced telemetry.csv's own x, y to 1.0e-4 m over all 219 transit
#   frames; SINCE R2-042 IT DOES NOT, and selftest [18] asserts the inverse — the
#   CSV reproduces `access_route_arrays` to 8.83e-05 m and this chord is 9.0407 m
#   away from it.  The chord is kept, published and gated; it is no longer the
#   thing the artefact sits on.
#
#   It did NOT decide which curve is right, and said so: making the telemetry
#   follow the arc re-times Beat 4 and re-keys a 479-key camera rig; making the
#   ribbon follow the chord throws away a declared R150 merge.  R2-042 has SINCE
#   BEEN DECIDED, in favour of the arc, and the telemetry moved.  What the
#   contract does regardless is refuse to let anything stand in EITHER curve,
#   which is what `transit_keepout` does.  The union was correct under both
#   readings and remains correct under the settled one; the ribbon alone was
#   correct under neither.

TRANSIT_DRIVE_NODES = np.array(
    [SPEC["transit"]["legs"][0]["from_world"][:2]]
    + [l["to_world"][:2] for l in SPEC["transit"]["legs"]], float)
TRANSIT_DRIVE_CUM_M = np.concatenate(
    [[0.0], np.cumsum([float(l["length_m"]) for l in SPEC["transit"]["legs"]])])
TRANSIT_DRIVE_LEN_M = float(TRANSIT_DRIVE_CUM_M[-1])          # 381.88

# The car box, MEASURED (round2_inventory.md S2: x -2.678..3.020, y -1.003..1.003,
# z 0.340..1.332).  It lived as a literal in build_surface (CAR_WIDTH), in
# build_barriers (CAR_HALF_W / CAR_CLEAR_M / CAR_PAD_M) and in
# tools/placement_gate.py (0.5 * 2.005 + CAR_MARGIN).  RULE 1.
CAR_BODY_LEN_M = 5.698
CAR_BODY_W_M = 2.005
CAR_BODY_H_M = 0.992
CAR_BODY_HALF_W_M = 0.5 * CAR_BODY_W_M                        # 1.0025
CAR_RIDE_HEIGHT_M = 0.340
CAR_CLEARANCE_M = 0.60           # tools/placement_gate.py CAR_MARGIN: the courtesy
                                 # air the gate sweeps around the body
CAR_SWEPT_HALF_W_M = CAR_BODY_HALF_W_M + CAR_CLEARANCE_M      # 1.6025
# ...and the gate sweeps an AXIS-ALIGNED BOX of that half-side, whose corners
# reach sqrt(2) further than its faces.  A module clearing the CIRCLE still fails
# the gate on a diagonal; this is the radius that clears the box.
CAR_SWEPT_PAD_M = CAR_SWEPT_HALF_W_M * math.sqrt(2.0) + 0.05  # 2.3164

TRANSIT_DRIVE_CLEAR_M = 0.60     # air between the swept car box and anything that
                                 # STANDS on the ground beside the driven line.
                                 # The same 0.60 m of margin TRANSIT_KEEPOUT_M was
                                 # calibrated to leave, stated against the curve
                                 # the gate actually measures instead of against
                                 # the one it does not.


def transit_drive_point(d):
    """The DRIVEN transit line at `d` metres from the dais.  -> (x, y).

    The four `SPEC["transit"]["legs"]` endpoints, linearly interpolated — which is
    what `tools/build_telemetry.py` integrates, to the metre and to the millimetre.
    NOT `access_route_point`, which is the declared ROAD.  See this section's head.
    """
    x, y = transit_drive_arrays(d)
    return (float(np.reshape(x, -1)[0]), float(np.reshape(y, -1)[0]))


def transit_drive_arrays(D):
    """Vectorised `transit_drive_point` -> (X, Y)."""
    D = np.asarray(D, float)
    return (np.interp(D, TRANSIT_DRIVE_CUM_M, TRANSIT_DRIVE_NODES[:, 0]),
            np.interp(D, TRANSIT_DRIVE_CUM_M, TRANSIT_DRIVE_NODES[:, 1]))


_TD = np.linspace(0.0, TRANSIT_DRIVE_LEN_M, 3821)     # 0.10 m
_TDX, _TDY = transit_drive_arrays(_TD)


def transit_drive_project(x, y, chunk=20000):
    """world (x, y) -> (d, v) on the DRIVEN transit line.

    `v` is the signed lateral, positive to the left of travel.  A nearest-sample
    search on a 0.10 m polyline: the line is four straight chords, so the sample
    step is the whole of the error and it is bounded by (0.05)^2/(2*R) = 0 on a
    straight and by the 0.05 m sample itself at the two kinks.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    n = x.size
    D = np.empty(n); V = np.empty(n)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        dx = x[a:b, None] - _TDX[None, :]
        dy = y[a:b, None] - _TDY[None, :]
        j = np.argmin(dx * dx + dy * dy, axis=1)
        jn = np.clip(j + 1, 0, len(_TD) - 1)
        jp = np.clip(j - 1, 0, len(_TD) - 1)
        hx = _TDX[jn] - _TDX[jp]
        hy = _TDY[jn] - _TDY[jp]
        h = np.hypot(hx, hy)
        hx = hx / np.maximum(h, 1e-12)
        hy = hy / np.maximum(h, 1e-12)
        ex = x[a:b] - _TDX[j]
        ey = y[a:b] - _TDY[j]
        D[a:b] = _TD[j] + ex * hx + ey * hy
        V[a:b] = -ex * hy + ey * hx
    return D, V


def transit_drive_keepout(x, y, margin=None):
    """True inside the swept car box along the DRIVEN transit line, plus margin.

    `margin` defaults to `TRANSIT_DRIVE_CLEAR_M`.  The half-width is
    `CAR_SWEPT_HALF_W_M` — the same body-plus-margin the placement gate sweeps —
    so a module that respects this cannot be reported by the gate as being in the
    car's path over the transit.
    """
    m = TRANSIT_DRIVE_CLEAR_M if margin is None else float(margin)
    d, v = transit_drive_project(x, y)
    return ((d >= 0.0) & (d <= TRANSIT_DRIVE_LEN_M)
            & (np.abs(v) <= CAR_SWEPT_HALF_W_M + m))


# ===========================================================================
# 10a.  THE PIT WALL'S WEST END   —   DEFECT #46, v1.1.1
# ===========================================================================
#
# MEASURED ON THE ASSEMBLED WORLD (docs/placement_report_r2.json, contract 1.0.1):
#
#     car_path   ARCH_RetainEdge   1.198 m in   at world (138.431, 27.140, -0.179)
#     car_path   ARCH_PitWall      1.067 m in   at world (144.282,  29.425, +0.200)
#
# and the car is doing 207.0 km/h at that frame (telemetry i = 138, world
# (144.75, 29.17), lap station 3443.15, u = +10.94).  Both objects are inside the
# CAR BODY envelope (half-width 1.0025 m), not merely inside the gate's 0.60 m
# courtesy margin: the wall face sits 0.533 m from the driven centreline.
#
# THE WALL IS THE THING THAT IS MISPLACED, AND IT IS MISPLACED BY THIS FILE.
# v1.0.x pinned `barrier_offset(s, +1)` to PIT_WALL_Y over the whole declared
# garage frontage, `_pit_straight_station(GARAGE_X0)` = s 3430.0 eastward, and
# build_architecture built its wall on that pin.  But the pit-exit road — the
# access ribbon, which IS the pit lane for these 150 m — is still OUTBOARD of
# PIT_WALL_Y at s = 3430 and does not come inboard of it until s = 3447.73.
# Between those two stations the contract asked for a solid concrete wall
# standing in the middle of the road, and got one.
#
# MEASURED on this revision's own geometry, the ribbon's OUTBOARD edge
# re-projected onto the lap:
#
#     s      3430    3435    3440    3445   3447.73   3450    3455    3460
#     u_out  14.06   13.16   12.34   11.75   11.500   11.33   11.09   11.02
#
# so the crossing is at s = 3447.73 (circuit x = -227.27) and east of it the whole
# ribbon lies inboard of the wall line, converging on a gore edge ~0.4 m outboard
# of `verge_edge`.  A pit wall standing 1.00 m outboard of the track edge is then
# 0.5-0.6 m clear of the road for the rest of its length, which is what a pit wall
# IS.  There is no station where a wall could stand BETWEEN the transit lane and
# the racing line: at s = 3443 the two are 10.94 m apart and `verge_edge` is 10.50,
# so the whole gap is track.  The answer is not a different y.  It is that the wall
# BEGINS AT THE CROSSING, which is what a real circuit does — the pit wall starts
# after the pit exit has merged, never before it.
#
# THE TERMINAL IS PART OF THE WALL.  v1.0.x's build_architecture had already found
# half of this by hand and moved its own west end to circuit x = -228.0 with a
# 4.2 m tapered nose — and the NOSE is what the placement gate caught, because the
# nose tapers in HEIGHT only and its face is still on PIT_WALL_Y.  So the contract
# publishes the terminal's length AND its lateral flare, and the station it
# publishes is where the NOSE stands, not where the first full-height unit does.
#
# The flare is where the clearance comes from and it is a real object: a flared
# barrier terminal, set back from the running face and brought forward over its
# length, is standard circuit furniture.
#
#     nose face      PIT_WALL_Y + PIT_WALL_TERMINAL_FLARE_M = 12.10 at s = 3447.73
#     running face   PIT_WALL_Y                             = 11.50 from s = 3452.73
#
# CLEARANCE DELIVERED, measured against telemetry.csv (not asserted — the contract
# does not read telemetry; tools/placement_gate.py is the check):
#
#     s = 3447.73  car u 9.23, swept volume top 10.83, nose face 12.10 -> 1.27 m
#     s = 3452.73  car u 7.36, swept volume top  8.96, wall face 11.50 -> 2.54 m
#
# WHAT ELSE MOVES.  `w_lp` (the pit-wall pin and the B_CONCRETE label) and `w_op`
# (the open pit-exit apron) share this station now: the apron ENDS where the wall
# BEGINS, which is the same statement made once instead of twice from GARAGE_X0.
# That extends `apron_zone` — and therefore `ground_z`'s apron tie — by 17.7 m of
# pit straight, and moves `platform_edge` on the left over the same stretch.
# Every baked mesh on the pit straight rebuilds.

PIT_WALL_TERMINAL_M = 5.0        # length of the wall's west terminal.  The
                                 # CONTRACT owns it because the station it
                                 # publishes is the terminal's nose, and a module
                                 # that guessed a different length would put the
                                 # nose somewhere the contract never checked.
PIT_WALL_TERMINAL_FLARE_M = 0.60  # how far OUTBOARD of PIT_WALL_Y the nose face
                                 # stands, flaring linearly in to the running face
                                 # over PIT_WALL_TERMINAL_M.  This is the wall's
                                 # clearance to the pit-exit road, and it is a
                                 # flared terminal, not a fudge factor.


def _pit_wall_start():
    """-> lap station of the pit wall's westernmost geometry (its nose).

    THE RULE:  a pit wall separates the pit lane from the track, so it may only
    stand where the pit-exit road is already on the pit-lane side of it.  The last
    station at which anything belonging to the pit exit is outboard of PIT_WALL_Y
    is the last station at which a wall on that line would be standing in the
    road; the wall's nose goes there.

    "ANYTHING BELONGING TO THE PIT EXIT" IS TWO CURVES, v1.2.0.  The declared
    ribbon's outboard edge, and the outboard face of the swept car box on the
    DRIVEN line (S10c) — because those two are up to 9.044 m apart and it is the
    driven one the placement gate measures.  v1.1.1 asked only the ribbon and got
    the right answer by 1.70 m of luck:

        ribbon outboard edge crosses PIT_WALL_Y at s = 3447.709
        driven swept box       crosses PIT_WALL_Y at s = 3446.007

    Derived, not declared, so that moving the merge arc, the ribbon width, the
    telemetry's legs or PIT_WALL_Y moves the wall with them instead of silently
    re-opening #46.
    """
    cross = []
    T = np.linspace(0.0, ACCESS_TOTAL, 24001)
    X, Y, H = access_route_arrays(T)
    _vin, vout = access_edges(T)
    S, U = project(X - np.sin(H) * vout, Y + np.cos(H) * vout)
    # only the pit straight can host the wall, and only east of the merge arc
    m = (S >= _S_PIT_OPEN) & (T > ACCESS_L2) & (U >= PIT_WALL_Y)
    if m.any():
        cross.append(float(S[m].max()))

    D = np.linspace(0.0, TRANSIT_DRIVE_LEN_M, 7641)
    DX, DY = transit_drive_arrays(D)
    S2, U2 = project(DX, DY)
    m2 = ((S2 >= _S_PIT_OPEN) & (D > ACCESS_L2)
          & (U2 + CAR_SWEPT_HALF_W_M >= PIT_WALL_Y))
    if m2.any():
        cross.append(float(S2[m2].max()))

    if not cross:                      # neither curve ever reaches the wall line
        return _pit_straight_station(GARAGE_X0)
    return max(cross)


PIT_WALL_S0 = _pit_wall_start()                       # 3447.73
PIT_WALL_X0 = (PIT_WALL_S0 - LAP) + PIT_WALL_TERMINAL_M   # circuit x of the first
                                                          # full-height wall unit


def pit_wall_span():
    """-> (s0, s1) lap stations of the pit wall INCLUDING its west terminal.

    s0 is the nose.  build_architecture builds the flared terminal over
    [s0, s0 + PIT_WALL_TERMINAL_M] and the running wall from there to s1.
    """
    return (PIT_WALL_S0, _pit_straight_station(GARAGE_X1))


def pit_wall_face(s):
    """-> the wall's face offset (signed u) at lap station s, terminal flare and all.

    PIT_WALL_Y east of the terminal; flared out to
    PIT_WALL_Y + PIT_WALL_TERMINAL_FLARE_M at the nose.  NaN where there is no wall.
    """
    scalar = np.ndim(s) == 0
    S = np.atleast_1d(np.asarray(s, float)) % LAP
    s0, s1 = pit_wall_span()
    d = (S - s0) % LAP
    span = (s1 - s0) % LAP
    f = np.clip(d / PIT_WALL_TERMINAL_M, 0.0, 1.0)
    y = PIT_WALL_Y + PIT_WALL_TERMINAL_FLARE_M * (1.0 - f)
    y = np.where(d <= span, y, np.nan)
    return float(y[0]) if scalar else y


# ===========================================================================
#  THE CORRIDOR IS BUILT HERE, not in §8, because it needs the block above.
# ===========================================================================

COR = _Corridor()


# ===========================================================================
#  9b.  OWNERSHIP  —  WHICH LEG OWNS THIS PATCH OF GROUND      R2-035, v1.2.0
# ===========================================================================
#
# THE CIRCUIT CROSSES ITS OWN CORRIDOR.  `barrier_offset` is a pure function of
# (s, side): `verge_edge + max(runoff, 4) + margin`, capped only by the
# inside-of-a-corner radius rule.  Nothing in it can know that ANOTHER LEG of the
# same 3675 m circuit, folded into a finite site, is in the way — and on this
# layout one is.  spec S9 gives T3 (a right-hander, so its OUTSIDE is side +1)
# 40 m of asphalt and 15 m of gravel; T3 is a 140 m kink, so the inside-corner
# clamp never bites, and the declared face comes out at 66.9 m for the whole of
# T3 and S3.  S4 and T5 run back past that side 51-67 m away and 5-7 m higher.
#
# MEASURED — the declared face swept into world space and re-projected onto the
# nearest centreline, 14 700 stations at 0.25 m, "inside" meaning within
# `half_width + 0.50 m` of a leg more than 2 m of arc length away (the road
# corridor `tools/placement_gate.py` judges the world by):
#
#     side  face inside SOME OTHER leg's road corridor      worst intrusion
#      +1        406 of 14 700 stations   (2.76 %)              7.493 m
#      -1          0 of 14 700 stations   (0.00 %)                   —
#
#     worst at s = 786.0, landing at |u| = 0.007 m on the leg at s = 1182.4 —
#     ON THAT LEG'S CENTRELINE, at the width of a painted line.
#
# v1.0.1 measured 3.56 % with THE SAME 7.493 m worst case.  v1.1.0's rate cap
# reduced the COUNT and not the INTRUSION, and reading that as progress is the
# mistake this section exists to close.  What got BUILT out of it, before
# build_barriers grew a private clamp, was BR_Armco_L03/L04 and
# BR_FenceStruct_L03/L04 lying wall-to-wall across the T4 braking zone.
#
# ---------------------------------------------------------------------------
# THE SOLVE, AND WHY IT NEEDS NO EXCLUSION WINDOW
# ---------------------------------------------------------------------------
#
# `road_corridor_mask` has always resolved this correctly, and it is worth saying
# why: it asks `project`, which returns the NEAREST centreline station over the
# WHOLE lap, so the mask is the union of the branches and terrain cuts exactly
# that.  This section asks `project` the same question, station by station:
#
#     for each station s on a OWNED_SOLVE_DS_M grid, and each of OWNED_SOLVE_NT
#     laterals spanning [verge_edge(s), _platform_edge_declared(s, side)], put the
#     point in world space and project it back.  The first lateral whose
#     projection is NOT this station's own is where this station stops owning the
#     ground.
#
# The obvious alternative — a KD-tree over dense centreline samples with an
# ARC-LENGTH EXCLUSION WINDOW so a station does not read its own neighbours as a
# foreign leg — was rejected, and the reason is the important part: A WINDOW IS A
# TUNING PARAMETER THAT CAN SILENTLY DISABLE THE CHECK.  Set it too narrow and a
# tight hairpin reads as a foreign leg; too wide and a genuine crossing is
# swallowed.  (Measured, while building this: a naive "nearest station more than
# 2 m of arc away" pre-filter on a 2 m grid excludes exactly one neighbour and
# returns 4.0 m — the grid step — for every station on the circuit.  It looks
# like a measurement and it is the grid.)
#
# Using `project`'s GLOBAL nearest inverts the question: nothing has to be
# excluded, only RECOGNISED.  And the own-station answer is not merely close, it
# is EXACT, for a geometric reason: the sample lies on the normal at s, the
# normal of a straight is perpendicular by construction and the normal of a
# circular arc passes through its centre, so for every element on this circuit
# (all are straights or circular arcs — there is not one clothoid) the foot of
# the perpendicular IS station s.  MEASURED over all 238 940 samples:
#
#     SELF samples     max |ds| = 0.0000 m   max |du| = 8.2e-14 m   (231 987)
#     FOREIGN samples  min |ds| = 43.381 m   max |ds| =    555.0 m     (6 953)
#
# so the two populations are separated by 43.4 m of arc length and ANY tolerance
# in (0, 43.381) gives a bit-identical answer.  `OWNED_SELF_WINDOW_M` = 2.0 m
# sits 2.0 m above the self population and 41.4 m below the foreign one.  It is a
# NUMERICAL TOLERANCE for `project`'s 0.25 m polyline (worst-case station
# residual half a step, 0.125 m, for a sample not on the grid) and not a
# geometric exclusion.  Two controls, both run in selftest [17]:
#
#     the T4 HAIRPIN, R = 28 m, the tightest radius on the circuit — 43 solve
#     stations, max self |ds| 0.0000 m: a hairpin is never mistaken for a foreign
#     leg, however tight.
#
#     the PIT STRAIGHT, the longest run — 406 solve stations, 0 foreign samples,
#     while the solve finds 6 953 elsewhere: the test is not silently dead, it is
#     correctly finding nothing where there is nothing.
#
# `CORRIDOR_BIAS_M` = 0.75 m of deliberate over-reach past the medial axis: two
# adjacent corridors sharing a hidden 0.75 m sliver is invisible, a 0.75 m hole
# between them is a lit gap at a 12.5 deg sun.
#
# ---------------------------------------------------------------------------
# THE CLAMP, AND ITS THREE PROPERTIES
# ---------------------------------------------------------------------------
#
#     avail(s)  = max(verge_edge + 4.0, owned_edge - platform margin)
#                 the ground this station can actually stand a barrier on, never
#                 tighter than verge_edge + 4.0 so `avail` can never be the thing
#                 that pushes a barrier TOWARDS the track.
#     target(s) = min(declared, avail)                    the hard answer
#     soft(s)   = verge_edge + cone_erode(target - verge_edge,
#                                         BARRIER_TAPER_MAX_RATE)
#                 the same line slope-limited IN CLEARANCE ABOVE THE VERGE, which
#                 is the quantity that must never go to zero
#     line(s)   = min(lerp(target, soft, w), avail)
#                 blended in ONLY where the cap actually bites
#
#   1. IT CANNOT REACH THE TRACK, AND THAT IS A PROOF.  `cone_erode(c, r) >=
#      min(c)`, and `min(target - verge_edge) >= BARRIER_MIN_CLEAR_M` because the
#      declared line's own minimum is the pit wall's 1.000 m and `avail -
#      verge_edge >= 4.0`.  A convex combination of two fields both >= that bound
#      is >= that bound, and the final `min(., avail)` only lowers toward it.
#   2. IT IS BUILDABLE.  Inside a capped stretch the line moves at no more than
#      BARRIER_TAPER_MAX_RATE — a 1 : 3.3 taper, which is what a circuit builds
#      where a runoff collapses into a hairpin apron.
#   3. IT IS A NO-OP WHERE THE CAP DOES NOT BITE.  `w == 0` there and `line ==
#      target == declared`, bit for bit: side -1 in its entirety, 90.24 % of the
#      0.25 m stations on side +1.
#
# THE PROVENANCE, AND WHY NO BARRIER MESH MOVES.  This is `build_barriers` S4b,
# ported unchanged, down to the grid steps and the tolerances.  That module has
# been building the shipped world off this exact line since the T4 Armco wall and
# handing the defect back with every report ("ANY MODULE THAT NEEDS THE BARRIER
# LINE THROUGH THIS STRETCH MUST READ build_barriers.barrier_offset, NOT
# world_contract.barrier_offset").  Promoting it changes nothing about the
# barriers; what it changes is that `build_dressing`, `build_terrain`,
# `build_architecture` and 435 item modules — every one of which reads the
# contract, not build_barriers — stop being handed a line that runs 7.5 m into
# another leg's racing surface.  S4b's clamp measures 0.00 % activation after
# this and is kept only as the assertion it always also was.

def _build_owned():
    """Fraction of (platform_edge_declared - verge_edge) each station owns."""
    G = np.arange(0.0, LAP, OWNED_SOLVE_DS_M)
    T = np.linspace(0.0, 1.0, OWNED_SOLVE_NT)
    out, diag = {}, {}
    for side in (+1, -1):
        e = verge_edge(G)
        pe = _platform_edge_declared(G, side)
        U = (e[:, None] + (pe - e)[:, None] * T[None, :]) * side
        SS = np.repeat(G[:, None], OWNED_SOLVE_NT, 1)
        X, Y, H, _ = centreline_arrays(SS.ravel())
        s2, u2 = project(X - np.sin(H) * U.ravel(), Y + np.cos(H) * U.ravel(),
                         chunk=8000)
        ds = np.abs(((s2 - SS.ravel() + LAP * 0.5) % LAP)
                    - LAP * 0.5).reshape(-1, OWNED_SOLVE_NT)
        du = np.abs(np.abs(u2).reshape(-1, OWNED_SOLVE_NT) - np.abs(U))
        foreign = (ds > OWNED_SELF_WINDOW_M) | (du > OWNED_SELF_U_TOL_M)
        fb = np.where(foreign.any(axis=1), foreign.argmax(axis=1), OWNED_SOLVE_NT)
        cap = np.where(fb == 0, 0.0,
                       T[np.clip(fb - 1, 0, OWNED_SOLVE_NT - 1)])
        # a station may not own more than either of its neighbours does: the
        # solve is sampled every 2 m and a barrier is continuous between them.
        cap = np.maximum(cap, np.maximum(np.roll(cap, 1), np.roll(cap, -1)))
        out[side] = np.interp(SGRID, G, cap, period=LAP)
        diag[side] = dict(grid=G, foreign=foreign, ds=ds, du=du)
    return out, diag


_OWNED, _OWNED_DIAG = _build_owned()


def owned_edge(s, side):
    """Outboard limit of the ground this station's corridor OWNS, in metres.

    Equal to `_platform_edge_declared` over 95.5 % of the corridor.  Where the
    circuit passes its own corridor it is the medial axis between the two legs
    plus `CORRIDOR_BIAS_M` — the same partition `project`, and therefore
    `road_corridor_mask`, already makes, so the union of the legs is exactly the
    hole build_terrain cuts.  See S9b.
    """
    c = np.interp(np.asarray(s, float) % LAP, SGRID, _OWNED[side], period=LAP)
    e = verge_edge(s)
    pe = _platform_edge_declared(s, side)
    return np.minimum(pe, e + (pe - e) * c + CORRIDOR_BIAS_M)


def _apply_ownership_cap():
    """Clamp `COR.off` to `owned_edge`.  See S9b for the three properties."""
    for side in (+1, -1):
        e = verge_edge(SGRID)
        oe = owned_edge(SGRID, side)
        wall = COR.sample("wallw", SGRID, side)
        marg = (PLATFORM_MARGIN_M
                + (PLATFORM_MARGIN_WALL_M - PLATFORM_MARGIN_M) * wall)
        avail = np.maximum(e + 4.0, oe - marg)
        bo = COR.off_declared[side]

        target = np.minimum(bo, avail)
        soft = e + _cone_erode(target - e, BARRIER_TAPER_MAX_RATE)

        hit = (bo - avail) > 1e-9
        k = int(round(OWNERSHIP_BLEND_M / PS))
        w = hit.astype(np.float64)
        for sh in range(1, k + 1):
            w = np.maximum(w, np.maximum(np.roll(hit, sh), np.roll(hit, -sh)))
        half = max(1, k // 3)
        ker = np.ones(2 * half + 1) / (2 * half + 1)
        w = np.convolve(np.concatenate([w[-half:], w, w[:half]]),
                        ker, mode="same")[half:-half]
        w = np.clip(w * 1.25, 0.0, 1.0)
        w = w * w * (3.0 - 2.0 * w)

        line = np.minimum(target * (1.0 - w) + soft * w, avail)

        # THE INVARIANT, asserted at import.  `build_barriers` raises the same
        # assertion; if this contract ever breaks it, the world build stops here
        # instead of building a barrier inside build_surface's own mesh.
        clr = line - e
        if float(clr.min()) < BARRIER_MIN_CLEAR_M - 1e-6:
            raise AssertionError(
                "ownership cap put the barrier line inside verge_edge + %.3f on "
                "side %+d: min clearance %.4f m at s = %.1f"
                % (BARRIER_MIN_CLEAR_M, side, float(clr.min()),
                   float(SGRID[int(clr.argmin())])))
        COR.off[side] = line


_apply_ownership_cap()


def ownership_report():
    """How far the ownership cap moved the declared line, and where.

    A DICT OF MEASUREMENTS, in metres.  Consumers that need to know whether they
    are in a capped stretch should ask `owned_edge`; this is for the defect log
    and for the rebuild agent's diff.
    """
    r = {}
    for side in (+1, -1):
        d = COR.off_declared[side] - COR.off[side]
        m = d > 1e-9
        clr = COR.off[side] - verge_edge(SGRID)
        rate, i = _cyclic_rate(COR.off[side], PS)
        r["L" if side > 0 else "R"] = dict(
            frac_of_lap=round(float(m.mean()), 4),
            max_pull_in_m=round(float(d.max()), 3),
            rms_pull_in_m=round(float(np.sqrt((d * d).mean())), 4),
            mean_where_capped=round(float(d[m].mean()) if m.any() else 0.0, 3),
            min_clearance_m=round(float(clr.min()), 4),
            min_clearance_s=round(float(SGRID[int(clr.argmin())]), 1),
            max_lateral_rate=round(rate, 6),
            identical_frac=round(float((d <= 1e-9).mean()), 4),
            owned_lt_platform_frac=round(float(
                (owned_edge(SGRID, side)
                 < _platform_edge_declared(SGRID, side) - 1e-9).mean()), 4))
    return r


_MAX_PLATFORM = float(max(platform_edge(SGRID, +1).max(),
                          platform_edge(SGRID, -1).max()))


ACCESS_RIBBON_T_MIN = 0.0    # THE START CAP IS THE GLASS PLANE, AND NO MARGIN MAY
                             # EXTEND BEHIND IT.  See in_access_ribbon.


def in_access_ribbon(x, y, margin=0.0):
    """True inside the access ribbon (plus `margin` metres), world (x, y).

    `margin` is a LATERAL allowance — the sawn edge strip on the paving side and the
    corridor wall footings on terrain's side.  IT IS NOT A LONGITUDINAL ONE.

    THE ASSEMBLY DEFECT THIS FIXES.  The old test was `tt >= -margin`, which walked
    the ribbon's start cap BACK THROUGH THE GLASS WALL by the caller's margin, and the
    three callers used three different margins for the same boundary:

        road_corridor_mask   ACCESS_CORRIDOR_MARGIN_M 3.00  -> terrain cut to x = 12.00
        build_architecture   RIBBON_SAW_M             0.30  -> paving cut to x = 14.70
        build_surface        the ribbon itself              -> mesh STARTS at x = 15.000

    Nobody built x 12.0 -> 15.0.  Measured on a 0.10 x 0.5 m grid over x 4..17,
    y +-14: 1 276 of 7 467 samples had NO USABLE GROUND (~64 m2) — a continuous 3.0 m
    deep band across the whole 12 m driving width, at the exact metre the car and the
    camera pass through as the car breaches the glass (`CAM_GLASS_GAP.png`).

    The ribbon BEGINS at the breach plane, `ACCESS_GLASS_X` = 15.000, by construction:
    spec 10.3(b) is about "the first 50 m OUTSIDE the glass", and behind the glass is
    the showroom floor, which is build_architecture's.  So the start cap is pinned at
    `ACCESS_RIBBON_T_MIN` = 0.0 whatever the margin, every consumer's cut lands on
    x = 15.000 exactly, and the paving butts the ribbon at the threshold.

    A module that keeps its own `-saw - t` term reopens the slot on its own side; the
    contract cannot reach into it.  There is nothing to be gained from a longitudinal
    margin here: the surfaces meet on a declared plane at z = APRON_Z, so a butt joint
    is exact, not toleranced.
    """
    tt, vv = access_project(x, y)
    lo = np.interp(tt, _RT, _RVIN) - margin
    hi = np.interp(tt, _RT, _RVOUT) + margin
    return ((tt >= ACCESS_RIBBON_T_MIN) & (tt <= ACCESS_TOTAL + margin) &
            (vv >= lo) & (vv <= hi))


def access_ribbon_polygon(margin=0.30, n=200):
    """Closed world-space polygon (N, 2) of the ribbon plus `margin` metres.

    THIS IS THE CUT.  build_architecture removes every paving bay, marking, drain
    and slab whose footprint intersects this polygon, and clips the bays that
    straddle it.  The default 0.30 m margin is the sawn edge strip build_surface
    lays along the ribbon so the two surfaces meet at a joint and not at an
    interpenetration.
    """
    T = np.linspace(0.0, ACCESS_TOTAL, int(n))
    X, Y, H = access_route_arrays(T)
    vin, vout = access_edges(T)
    nx, ny = -np.sin(H), np.cos(H)
    left = np.stack([X + nx * (vout + margin), Y + ny * (vout + margin)], axis=1)
    right = np.stack([X + nx * (vin - margin), Y + ny * (vin - margin)], axis=1)
    return np.vstack([left, right[::-1]])


# --------------------------------------------------------- the Beat-4 corridor
CORRIDOR_OWNER = "build_barriers"
CORRIDOR_DELETE_NAMES = ("ARCH_ApronCorridor",)

TRANSIT_WALL_S0 = 6.0          # route stations, metres from the glass plane
TRANSIT_NORTH_S1 = 96.0        # 90.0 m — the spec §10.5 literal, and it fits
TRANSIT_SOUTH_S1 = 90.0        # 84.0 m — where the south wall runs out of verge
TRANSIT_WALL_S1 = TRANSIT_NORTH_S1        # the camera's walled run, 90.0 m
TRANSIT_NORTH_OFFSET_M = +8.0  # cut-faced concrete retaining wall (left of travel)
TRANSIT_SOUTH_OFFSET_M = -7.0  # tyre stack + debris fence (right of travel)
TRANSIT_NORTH_TOP_Z = 2.40     # wall height; +0.16 m coping is build_barriers'
TRANSIT_SOUTH_TOP_Z = 2.00     # tyre wall; the fence above it reaches 4.30
TRANSIT_PORTAL_X = 58.0        # world x of the pit-exit gate portal (spec §10.5)
TRANSIT_PORTAL_CLEAR_M = 2.6   # half length of the gap left in the tyre wall
FORECOURT_BOLLARD_X = 19.5     # build_architecture's glass-frontage bollard line

# Anything that stands on the ground — barrier post, fence post, wall, tyre stack,
# marshal post, ad board, bollard, tree — embeds AT LEAST this far into the datum,
# so a 10 mm mesh tolerance can never open a lit gap under it at a grazing sun.
BASE_EMBED_M = 0.020


def transit_wall_span(side):
    """-> (t0, t1) route-station span of the corridor wall on `side`."""
    return (TRANSIT_WALL_S0,
            TRANSIT_NORTH_S1 if side > 0 else TRANSIT_SOUTH_S1)


def transit_wall_point(t, side):
    """Wall base point, world (x, y, z), at route station t.  side +1 = north."""
    x, y, h = access_route_point(t)
    off = TRANSIT_NORTH_OFFSET_M if side > 0 else TRANSIT_SOUTH_OFFSET_M
    return (x - math.sin(h) * off, y + math.cos(h) * off, APRON_Z)


# ===========================================================================
# 11.  THE APRON / PADDOCK PLATFORM   (spec §10.7, architecture's ground)
# ===========================================================================
#
# The paddock, the pit lane, the pit-exit apron and the showroom forecourt are ONE
# DECLARED PLANE at z = 0.000.  build_architecture owns their surfaces.  Terrain
# does not build ground inside them either — it already had a `built` platform
# concept; this is the same region stated once so the extents cannot drift.

_PAD = SPEC["paddock"]
# v1.1.1: THE PIT LANE BEGINS WHERE THE PIT WALL BEGINS.  Its inner edge is
# PIT_WALL_Y, so a pit-lane rectangle that starts west of the wall's nose declares
# a boundary at y = +11.5 in a place where there is no wall — and leaves the strip
# circuit y 10.55..11.50 over x -245..-227 belonging to nobody, while `apron_zone`
# (which now runs up to the wall, §10a) tells build_architecture to pave it.
# MEASURED: build_architecture's own "paving stays inside the contract's declared
# rectangles" went from 0 to 350 of 35 381 up-faces outside.  The apron runs east
# to the nose and the pit lane starts there; it is one boundary, stated once.
_PIT_NOSE_X = PIT_WALL_X0 - PIT_WALL_TERMINAL_M          # -227.2908
APRON_REGIONS_CIRCUIT = {
    "pit_lane":  (_PIT_NOSE_X, GARAGE_X1, PIT_WALL_Y, _PAD["pit_lane_design_y"][1]),
    "garages":   tuple(_PAD["garages_design"]["x"]) + tuple(_PAD["garages_design"]["y"]),
    "paddock":   tuple(_PAD["paddock_design"]["x"]) + tuple(_PAD["paddock_design"]["y"]),
    "apron":     ((float(_PAD["apron_design"]["x"][0]), _PIT_NOSE_X)
                  + tuple(_PAD["apron_design"]["y"])),
}
FORECOURT_WORLD = dict(cx=-0.5, cy=0.0, hx=26.5, hy=22.0)   # build_architecture's


def apron_platform_mask(x, y, raw=False):
    """True where build_architecture paves the z = 0.000 platform.

    The spec's declared extents OVERLAP the circuit — spec §10.7 gives the
    pit-exit apron as circuit x -480..-245, y 0..+45, and y = 0 is the pit-straight
    CENTRELINE, so taken literally architecture paves 10.5 m of the racing surface
    and 241 m of its painted verge.  ARCH_Paving_Apron already did: it starts at
    circuit y = 9.5 against a verge edge at y = 10.5, which is a 1.0 m wide, 241 m
    long coplanar overlap at a 55-70 mm offset — a lit ledge down the whole pit
    straight that the assembly review did not even reach.

    So the declared regions are returned MINUS the road corridor and MINUS the
    access ribbon.  Pass raw=True for the literal spec rectangles.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    cx, cy = world_to_circuit(x, y)
    m = np.zeros(x.shape, bool)
    for (x0, x1, y0, y1) in APRON_REGIONS_CIRCUIT.values():
        m |= (cx >= x0) & (cx <= x1) & (cy >= y0) & (cy <= y1)
    f = FORECOURT_WORLD
    m |= ((np.abs(x - f["cx"]) <= f["hx"]) & (np.abs(y - f["cy"]) <= f["hy"]))
    if raw:
        return m
    # the LAP corridor and the ribbon's JOINT — not terrain's 3 m keep-out.  See
    # road_corridor_mask.
    return m & ~road_corridor_mask(x, y, ribbon_margin=ACCESS_RIBBON_SAW_M)


def _box_sdf(px, py, cx, cy, hx, hy):
    """Signed distance to an axis-aligned box.  <= 0 inside.  Exact."""
    qx = np.abs(px - cx) - hx
    qy = np.abs(py - cy) - hy
    outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return outside + inside


def platform_field(x, y):
    """Metres OUTSIDE the declared z = 0.000 platform.  <= 0 inside it.

    `apron_platform_mask(raw=True)` AS A SIGNED FIELD, so build_terrain can CLIP a
    cell that straddles the platform edge instead of dropping or keeping it whole.

    DEFECT #50, v1.1.1.  build_terrain cuts a hole for `road_corridor_mask` and
    nothing else.  For the DECLARED PLATFORM it only FLATTENS its height field —
    `built = max(pad, r1)`, `z_nat = z_nat*(1-built) - 0.20*built` — so `TER_Ground`
    is still there, under build_architecture's concrete, at whatever height the
    flattening leaves it.  MEASURED on the assembled world, casting the full ray
    stack in 7 585 columns over the pit-exit apron:

        ARCH_Paving_Paddock x TER_Ground   859 columns   |dz| p50 15.59 mm
                                           s 3196-3406, u 41.0-45.0
        ARCH_Paving_PitLane x TER_Ground    60 columns   |dz| p50 16.59 mm
        49 of 7 585 columns (0.65 %) have two DIFFERENTLY-OWNED surfaces within 2 mm

    Two owners on one square metre, which under a moving camera in a cut-free film
    is a flicker with nowhere to hide.  `TOL_COPLANAR_M`'s own rule is "cut, do not
    offset", and the contract already declares who owns this ground: §12's
    `world_ground_z` hands every one of those columns to `build_architecture:paving`.
    Terrain simply had no field to cut it with.  Now it has one.

    The RAW rectangles are used deliberately: where they overlap the circuit, the
    corridor field already says "do not build", so `min(corridor_field,
    platform_field)` is exactly `road_corridor_mask | apron_platform_mask` with no
    third case to get wrong.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    cx, cy = world_to_circuit(x, y)
    f = np.full(x.shape, np.inf)
    for (x0, x1, y0, y1) in APRON_REGIONS_CIRCUIT.values():
        f = np.minimum(f, _box_sdf(cx, cy, 0.5 * (x0 + x1), 0.5 * (y0 + y1),
                                   0.5 * (x1 - x0), 0.5 * (y1 - y0)))
    fc = FORECOURT_WORLD
    return np.minimum(f, _box_sdf(x, y, fc["cx"], fc["cy"], fc["hx"], fc["hy"]))


# ===========================================================================
# 12.  world_ground_z  —  one query, any point, and who owns it
# ===========================================================================

OWNER_TRACK = "build_surface:SURF_Track"
OWNER_ROAD = "build_barriers:runoff platform"
OWNER_ACCESS = "build_surface:SURF_AccessRoad"
OWNER_APRON = "build_architecture:paving"
OWNER_TERRAIN = "build_terrain:TER_Ground"


def world_ground_z(x, y):
    """-> (z, owner) for any world point.  z is NaN where terrain owns the ground.

    THE PRIORITY ORDER, highest first, and it is exhaustive and disjoint:

        1. the racing surface        |u| <= verge_edge(s)      build_surface
        2. the access ribbon         in_access_ribbon(x, y)    build_surface
        3. the runoff platform       |u| <= platform_edge      build_barriers
        4. the declared apron        apron_platform_mask       build_architecture
        5. everything else                                     build_terrain

    Use this to sit ANY object on the ground — marshal post, ad board, tyre stack,
    tree, camera collision proxy, the car — and the assembly review's findings
    cannot recur through your module.  Note that 1-3 all return the SAME function,
    `ground_z`; the owner string tells you whose mesh is actually there.
    """
    scalar = (np.ndim(x) == 0 and np.ndim(y) == 0)
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    z = np.full(x.shape, np.nan)
    own = np.full(x.shape, OWNER_TERRAIN, dtype=object)

    s = np.zeros(x.shape); u = np.full(x.shape, 1e9)
    near = _near_circuit(x, y, _MAX_PLATFORM + 1.0)
    if near.any():
        s[near], u[near] = project(x[near], y[near])
    E = verge_edge(s)
    lim = np.where(u >= 0.0, platform_edge(s, +1), platform_edge(s, -1))
    on_track = np.abs(u) <= E
    in_plat = (np.abs(u) <= lim) & ~on_track
    rib = in_access_ribbon(x, y) & ~on_track

    ap = apron_platform_mask(x, y, raw=True) & ~on_track & ~in_plat & ~rib
    z[ap] = APRON_Z
    own[ap] = OWNER_APRON

    plat = in_plat & ~rib
    if plat.any():
        z[plat] = ground_z(s[plat], u[plat])
        own[plat] = np.where(
            np.where(u[plat] >= 0.0, apron_zone(s[plat], +1),
                     apron_zone(s[plat], -1)) > 0.5, OWNER_APRON, OWNER_ROAD)

    if rib.any():
        tt, vv = access_project(x[rib], y[rib])
        z[rib] = access_z(tt, vv)
        own[rib] = OWNER_ACCESS

    if on_track.any():
        z[on_track] = ground_z(s[on_track], u[on_track])
        own[on_track] = OWNER_TRACK

    if scalar:
        return float(z[0]), str(own[0])
    return z, own


# ===========================================================================
# 13.  THE LIGHTING CONTRACT
# ===========================================================================
#
# build_sky is the PHYSICAL LIGHT of this film and it wins.  Every number below is
# build_sky's shipped, measured value, copied here so that material calibration,
# exposure and any future relight have ONE reference.
#
# What went wrong before: build_terrain.md §2.1 published a "fixed" lighting rig
# (sun 120 W/m2 at (1.000, 0.735, 0.470), aerosol 1.45, ozone 1.80, direct:diffuse
# 3.0:1, AgX -2.70) and instructed task #27 to "ADOPT S2.1 VERBATIM".  Task #27 did
# not, and was right not to: build_sky measured the sun against its own sky instead
# of assuming it.  The net exposure is close by luck (terrain's assumed total
# horizontal irradiance is 1.331x too high, its exposure 0.348 stops too dark, so
# the level lands within 0.07 stops) but the COLOUR and the KEY:FILL RATIO are not:
#
#     direct : diffuse   terrain assumed 3.00 : 1     actual 2.072 : 1
#     sun colour         terrain assumed (1, .735, .470)  actual (1, .71632, .38712)
#     sky tint           terrain assumed neutral-ish  actual (.3115, .5582, 1.0000)
#
# Shadows are 45 % brighter relative to key than terrain's turf albedo was tuned
# for, and they are markedly bluer.  Every material calibrated against §2.1 must be
# re-checked against `lambert_radiance` below.

SUN_DIR = (0.5178540, -0.8277670, 0.2159390)     # unit, world frame
SUN_ELEV_DEG = 12.47061
SUN_BEARING_DEG = -57.96966
SUN_SHADOW_RATIO = 4.5222                        # horizontal run per unit height
SUN_ANGULAR_DIAM_DEG = 0.545
SUN_SOLID_ANGLE_SR = 7.10530e-5

SUN_IRRADIANCE = (115.754, 82.917, 44.811)       # W/m^2 NORMAL to the sun
SUN_ENERGY = 115.754                             # Blender SUN lamp strength
SUN_COLOR = (1.00000, 0.71632, 0.38712)          # Blender SUN lamp colour

SKY_MODEL = "MULTIPLE_SCATTERING"                # Blender 5.x has no NISHITA enum
SKY_AIR = 1.00
SKY_AEROSOL = 0.45                               # low ON PURPOSE: the bottom 1.1 km
SKY_OZONE = 1.30                                 # of aerosol is explicit geometry
SKY_ALTITUDE = 0.0
SKY_SUN_DISC = False                             # the SUN lamp is the light
SKY_SUN_ROTATION_DEG = 147.96966                 # = 90 - bearing (measured)
SKY_STRENGTH = 1.0

SKY_IRRADIANCE = (4.228, 7.577, 13.573)          # sky-only, horizontal surface
SKY_TINT = (0.3115, 0.5582, 1.0000)
E_DIRECT_HORIZONTAL = tuple(v * math.sin(math.radians(SUN_ELEV_DEG))
                            for v in SUN_IRRADIANCE)     # (24.996, 17.905, 9.676)
DIRECT_TO_DIFFUSE = 2.072                        # sum(E_DIRECT_HORIZONTAL)/sum(SKY)

VISUAL_RANGE_M = 23000.0                         # Koschmieder, 2 % contrast
SIGMA_EXT_550 = 3.912 / VISUAL_RANGE_M           # 1.7009e-4 /m

# EXPOSURE IS A HAND-OFF.  build_sky never writes scene.view_settings; the camera
# rig does.  An albedo-0.18 horizontal surface in full sun renders at 1.4888 linear
# (mean of the three channels), so putting it on AgX mid-grey costs -3.048 stops.
REFERENCE_EXPOSURE_EXTERIOR = -3.048
VIEW_TRANSFORM = "AgX"
VIEW_LOOK = "None"                               # ONE lens, ONE grade, no per-beat
                                                 # look changes (the brief's law)


def lambert_radiance(albedo, normal_up=True):
    """Linear render value of a lambertian horizontal surface under THIS sky.

    -> (r, g, b) per-channel radiance.  `albedo` may be a scalar or an (r, g, b).
    Check value: lambert_radiance(0.18) = (1.6740, 1.4600, 1.3324), mean 1.4888,
    which is the number REFERENCE_EXPOSURE_EXTERIOR was solved against.

    This is the function a material calibration should be run against.  If a
    material's rendered patch does not land within a few percent of this for its
    intended albedo, the material is wrong, not the light.
    """
    a = np.broadcast_to(np.asarray(albedo, float), (3,))
    e = np.array(E_DIRECT_HORIZONTAL) + np.array(SKY_IRRADIANCE)
    if not normal_up:
        e = np.array(SKY_IRRADIANCE)
    return tuple(a * e / math.pi)


# ---------------------------------------------------------------------------
#  SELF-SHADOWING:  WHEN DOES A RECESS RENDER BLACK?      DEFECT #48, v1.1.1
# ---------------------------------------------------------------------------
#
# WHY THIS IS IN THE CONTRACT AND NOT IN A MODULE.  build_architecture's own gate
# bounds the DEPTH of a recess (`DEPTH_LIM` = 66 mm) and the FRACTION of columns
# that land low (3 %).  The pit-exit apron's outer edge measured 34.2-34.5 mm deep
# and 0.66 % of columns, so it passed both — and it rendered as **3,390 pure-black
# pixels**, every one of them below 0.02 luminance, in a frame whose track surface
# reads 0.1729 and whose darkest legitimate joint reads above 0.05.
#
# BOUNDING DEPTH DOES NOT BOUND BLACKNESS.  Blackness is a function of depth AND
# width AND the sun's elevation and bearing, and this world's sun is 12.47 deg up.
# At that elevation `SUN_SHADOW_RATIO` = 4.5222 metres of horizontal run per metre
# of height, so a 34 mm step casts a 155 mm shadow: any recess narrower than
# 155 mm has NO DIRECT SUN ON ITS FLOOR AT ALL, whatever the depth gate says.
# What is left is sky, and a slot only sees the sky through its own mouth.
#
# THE MODEL.  Two terms, both closed-form, both for an infinitely long straight
# recess of width `w` and depth `d` running on bearing `b`:
#
#   DIRECT.  The sun clears the lip after `d * SUN_SHADOW_RATIO` of horizontal
#            run; the component of that run ACROSS the recess is
#            `|sin(b - SUN_BEARING_DEG)|`.  The lit strip is what is left of `w`.
#
#   DIFFUSE. The sky view factor from the floor of an infinite slot is the
#            standard crossed-strings result  F = sqrt(1 + r^2) - r,  r = d/w.
#            F = 1 for a flat surface (r = 0) and 0.0725 for the r = 6.87 slot
#            that rendered black.
#
# and they are weighted by the declared irradiances, so this function moves when
# `build_sky` moves.  It returns a RELATIVE RADIANCE — the floor of the recess
# against the flat surface beside it, same albedo — which is directly comparable
# to the pixel measurement that found the defect.
#
# CALIBRATION of TOL_RECESS_RADIANCE, against MEASURED GEOMETRY on the assembled
# world and MEASURED PIXELS in the frame it rendered — not against taste:
#
#   THE DEFECT       w = 0.005 m, d = 0.0343 m  ->  0.024
#                    3,390 px below 0.02 display luminance, ray-cast to
#                    ARCH_Paving_ApronPlatform at 34.17-34.45 mm below datum,
#                    u = 12.097-12.102, 4.9-11.4 m from the lens (probeH.json).
#   THE SHALLOWEST   the sawn bay joints beside it: probeH's scanline at py = 1990
#   LEGITIMATE       found 7 of 1920 columns more than 5 mm low, so every other
#   JOINT IN FRAME   joint is under 5 mm deep at 8 mm wide  ->  0.180
#   the sealant lap  w = 0.050 m, d = 0.005 m   ->  0.711   invisible
#
# 0.10 is 4.2x above the defect and 1.8x below the shallowest legitimate joint in
# the same frame.  The gate REPORTS the worst recess it finds whether or not it
# fails, so a joint drifting toward black is visible before it crosses.
DIFFUSE_FRACTION = 1.0 / (1.0 + DIRECT_TO_DIFFUSE)      # 0.3255
TOL_RECESS_RADIANCE = 0.10       # a recess may not render darker than this
                                 # fraction of the flat surface beside it


def recess_relative_radiance(width_m, depth_m, bearing_deg=0.0):
    """Radiance of a straight recess's floor / the flat surface beside it.

    `width_m` across, `depth_m` down, `bearing_deg` = the direction the recess
    RUNS, in the world frame (0 = +X, 90 = +Y), which is how much of the sun's
    shadow reach is spent crossing it.  Scalar or array; 1.0 means "as bright as
    the surface beside it", 0.0 means black.

    Same albedo both sides — this answers "is the joint darker than the slab",
    which is the question a rendered frame asks.
    """
    w = np.maximum(np.asarray(width_m, float), 1e-9)
    d = np.maximum(np.asarray(depth_m, float), 0.0)
    across = np.abs(np.sin(np.radians(np.asarray(bearing_deg, float)
                                      - SUN_BEARING_DEG)))
    lit = np.clip(1.0 - d * SUN_SHADOW_RATIO * across / w, 0.0, 1.0)
    r = d / w
    view = np.sqrt(1.0 + r * r) - r
    return (1.0 - DIFFUSE_FRACTION) * lit + DIFFUSE_FRACTION * view


def recess_is_black(width_m, depth_m, bearing_deg=0.0):
    """True where a recess of these proportions renders as a BLACK LINE.

    This is the check `DEPTH_LIM` could not make.  Test it against the artefact
    that is already known to be bad — recess_is_black(0.005, 0.0343) is True —
    before trusting it anywhere.
    """
    return recess_relative_radiance(width_m, depth_m,
                                    bearing_deg) < TOL_RECESS_RADIANCE


def max_recess_depth(width_m, bearing_deg=0.0):
    """Deepest a recess `width_m` wide may be before it renders black.

    The number a builder actually needs: "my joint is 8 mm wide, how deep may it
    be?"  Solved by bisection on `recess_relative_radiance`, which is monotone
    decreasing in depth.
    """
    w = float(width_m)
    lo, hi = 0.0, 10.0 * max(w, 1e-6)
    while recess_relative_radiance(w, hi, bearing_deg) >= TOL_RECESS_RADIANCE:
        hi *= 2.0
        if hi > 1e4:
            return float("inf")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if recess_relative_radiance(w, mid, bearing_deg) >= TOL_RECESS_RADIANCE:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ===========================================================================
# 14.  TOLERANCES  —  what "agrees" means, numerically
# ===========================================================================
#
# The old build_barriers.md claimed SEAM_DROP = 0.015 "absorbs up to 15 mm of
# disagreement".  The measured disagreement at the verge edge was min -0.680 m,
# max +0.691 m, p95 |0.49| m — off by 46x.  A tolerance is only a tolerance if
# something measures it, so these are the numbers the assembly gate checks.

TOL_DATUM_M = 0.001      # two modules asking `ground_z` the same question must
                         # get answers within 1 mm.  They will: it is one function.
TOL_SEAM_M = 0.010       # a module's own mesh may sit up to 10 mm off the datum at
                         # a shared boundary (mesh row spacing, bevels, chamfers).
                         # Beyond that it is a defect, not a tolerance.
TOL_COPLANAR_M = 0.030   # two SEPARATELY-OWNED surfaces closer than this in z over
                         # a shared footprint are a z-fight.  The only legal fix is
                         # for one of them not to be there: cut, do not offset.
SEAM_DROP_M = 0.0        # RETIRED.  Nothing hides under anything any more.

TOL_CLOSURE_M = 1.0e-6   # THE DATUM MUST CLOSE ON ITSELF.  `ground_z(s, u)` and
                         # `ground_z(s + LAP, u)` are the same metre of road, so
                         # the limit from either side of the start/finish line must
                         # be the same number.  1 micron: 1000x below TOL_DATUM_M,
                         # 17x above the 5.7e-8 m the datum's own 5.2 % grade
                         # contributes over the 1e-6 m the test steps back from the
                         # seam, and 1e10 x above the float64 round-off the fixed
                         # implementation actually leaves (1.1e-16 m).
                         # v1.0.1 failed this at 6.75e-3 m.  See _vnoise.


# ===========================================================================
# 14b.  CONTINUITY  —  the bounds, and how each one was calibrated
# ===========================================================================
#
# THIS SECTION EXISTS BECAUSE DEFECT 1 SURVIVED FOR THREE CONTRACT REVISIONS AND
# A WHOLE ASSEMBLY REVIEW.  --selftest had 74 checks and not one of them looked at
# whether anything was CONTINUOUS.  `barrier_offset` stepped 51.99 m in one metre,
# an Armco wall was built across the T4 racing surface, build_barriers wrote a
# 200-line workaround, and the contract still said PASS.  A gate that cannot fail
# on the artefact you already know is bad is not an instrument.
#
# Every entry is (name, bound, unit, how the bound was calibrated).  The gate in
# selftest() §12 samples each quantity over the WHOLE 3675 m lap at the stated
# step and asserts max |d f / ds| <= bound.  Bounds are stated here, in the
# contract, not buried in the test, so a consumer can read the number it is
# entitled to rely on.
#
# TWO RULES ABOUT THESE NUMBERS
#
#   1. A bound is calibrated from a DECLARED quantity — a spec grade, a ramp
#      length in RUNOFF_ZONES, a filter width in this file — never from "what it
#      happens to measure today".  The measured value is printed beside it so the
#      margin is visible, but the measurement is not the bound.
#   2. Sampling step matters more than the bound does.  A step of e mm sampled at
#      h metres reads as e/1000h m/m, so the datum's 6.75 mm start/finish step is
#      INVISIBLE at h = 0.25 m (0.027 m/m, under the 0.10 bound) and obvious at
#      h = 0.01 m (0.675 m/m).  `ground_z` is therefore gated at 0.01 m across the
#      seam and has a dedicated exact closure test; everything else is gated at
#      0.25 m, where the smallest step it can hide is 0.25 * bound.
# Bounds that are a DECLARED RATE are stated as that rate plus _RATE_EPS, because
# the gate resamples a 1 m station field at 0.25 m and (0.25 * r) / 0.25 is not
# always exactly r in float64.  1e-6 m/m is a micron of lateral per metre of
# station: far below anything geometric, far above the round-off.  It is
# `RATE_EPS`, published in S8 beside the rate it guards, because
# `build_barriers`' break test needs exactly the same allowance (v1.2.0).
_RATE_EPS = RATE_EPS

CONTINUITY_BOUNDS = {
    "half_width": (0.0170, 0.25,
                   "spec S9: 1.0 m of half-width over the 60 m LINEAR transition "
                   "= 0.016667 m/m exactly, + round-off"),
    "verge_edge": (0.0170, 0.25,
                   "half_width + two constants; same bound"),
    "elevation_c": (0.0550, 0.25,
                    "spec S5: max |PVI tangent grade| = 5.200 %.  Inside a "
                    "symmetric parabolic vertical curve the gradient lies between "
                    "its two tangent grades, so the tangent maximum IS the "
                    "maximum, + 5 % round-off"),
    "barrier_offset": (BARRIER_MAX_LATERAL_RATE + _RATE_EPS, 0.25,
                       "steepest lateral motion a single RUNOFF_ZONES entry "
                       "declares is 1.5*(asph+grav)/ramp = 1.750 m/m at T10T11; "
                       "the assembled programme peaks at 1.9447 where the S11 "
                       "doppler pin overlaps T10T11's ramp-out; the break test "
                       "every consumer uses is a strict > 2.00.  ENFORCED by "
                       "_cone_erode at exactly this rate"),
    "runoff_asphalt": (BARRIER_MAX_LATERAL_RATE + _RATE_EPS, 0.25, "as barrier_offset"),
    "runoff_gravel": (BARRIER_MAX_LATERAL_RATE + _RATE_EPS, 0.25, "as barrier_offset"),
    "runoff_grass": (BARRIER_MAX_LATERAL_RATE + _RATE_EPS, 0.25, "as barrier_offset"),
    "runoff_apex": (BARRIER_MAX_LATERAL_RATE + _RATE_EPS, 0.25, "as barrier_offset"),
    "runoff_edge": (1.9700, 0.25,
                    "verge_edge (0.0170) + the widest cross-section component "
                    "(1.950), + round-off"),
    "platform_edge": (2.1000, 0.25,
                      "max(barrier_offset, runoff_edge) (1.970) + the wall-margin "
                      "ramp, which is a 45-sample box filter of a 0/1 indicator "
                      "times (6.0 - 0.6) m = 0.120 m/m, + round-off"),
    "apron_zone": (0.0340, 0.25,
                   "the declared pit-exit ramp: a smoothstep over "
                   "PIT_OVERRIDE_RAMP_M = 45 m, whose peak slope is 1.5/45 = "
                   "0.033333 /m exactly, + round-off.  (The general case, a "
                   "45-sample box filter of a 0/1 label, is gentler at 1/45 = "
                   "0.0222 /m, so this bound covers both)"),
    "ground_z": (0.1000, 0.01,
                 "max PVI grade 5.200 % + the banking transition carried to the "
                 "verge edge (max d(bank)/ds = 0.001839 /m over the 14 m csmooth, "
                 "x 10.5 m = 1.931 %) + the undulation (0.55 %) = 7.68 %, + 30 % "
                 "for the negative-kerb ramps and the apron tie not being proved "
                 "disjoint from the rest"),
    "corridor_rim_z": (0.1500, 0.25,
                       "ground_z (0.100) + the platform's own -1.6 % cross-fall "
                       "dragged along by platform_edge's 2.10 m/m = 3.4 %"),
}

# the laterals `ground_z` is gated at: the centreline, the racing-surface edge,
# both kerb lines, the verge edge, and four stations out on the runoff platform,
# on BOTH sides — banking is antisymmetric in u, so a one-sided sweep proves half
# of nothing.
_GZ_LATERALS = (0.0, 3.0, -3.0, 6.5, -6.5, 8.0, -8.0, 10.5, -10.5,
                18.0, -18.0, 30.0, -30.0, 45.0, -45.0, 60.0, -60.0)


def _cyclic_rate(f, step):
    """max |df/ds| of a field sampled on a CLOSED lap grid, and where."""
    f = np.asarray(f, float)
    d = np.abs(np.diff(np.concatenate([f, f[:1]]))) / step
    i = int(d.argmax())
    return float(d.max()), i


def continuity_report(mod=None, verbose=False):
    """THE CONTINUITY GATE.  -> (ok, rows, notes).

    `mod` may be ANY module exposing this contract's public API, so the gate can
    be pointed at a previous revision and made to fail on an artefact already
    known to be bad.  That is the only technique that has reliably worked on this
    project: nine of the instruments here turned out to be the broken thing.
    Run `python3 world_contract.py --gate-selftest` to see it fail v1.0.1.

    Every row is (name, bound, measured, step_m, worst_s, ok).
    """
    C = mod if mod is not None else sys.modules[__name__]
    lap = float(C.LAP)
    rows = []
    notes = []

    def add(name, val, step, S):
        bound, want_step, _why = CONTINUITY_BOUNDS[name]
        r, i = _cyclic_rate(val, step)
        rows.append((name, bound, r, step, float(S[i]), r <= bound))

    # ---- the 0.25 m lap sweep -------------------------------------------
    step = 0.25
    S = np.arange(0.0, lap, step)
    add("half_width", C.half_width(S), step, S)
    add("verge_edge", C.verge_edge(S), step, S)
    add("elevation_c", C.elevation_c(S), step, S)
    for side in (+1, -1):
        sfx = " (side %+d)" % side
        for nm, v in (("barrier_offset", C.barrier_offset(S, side)),
                      ("runoff_edge", C.runoff_edge(S, side)),
                      ("platform_edge", C.platform_edge(S, side)),
                      ("apron_zone", C.apron_zone(S, side))):
            bound, _ws, _why = CONTINUITY_BOUNDS[nm]
            r, i = _cyclic_rate(v, step)
            rows.append((nm + sfx, bound, r, step, float(S[i]), r <= bound))
        w = C.runoff_widths(S, side)
        for k in ("asphalt", "gravel", "grass", "apex"):
            nm = "runoff_" + k
            bound, _ws, _why = CONTINUITY_BOUNDS[nm]
            r, i = _cyclic_rate(w[k], step)
            rows.append((nm + sfx, bound, r, step, float(S[i]), r <= bound))
        rim = np.asarray(C.corridor_rim(S, side))[:, 2]
        bound, _ws, _why = CONTINUITY_BOUNDS["corridor_rim_z"]
        r, i = _cyclic_rate(rim, step)
        rows.append(("corridor_rim_z" + sfx, bound, r, step, float(S[i]), r <= bound))

    # ---- THE DATUM, at 0.01 m -------------------------------------------
    # 367 500 stations x 17 laterals is 6.2 M evaluations, so it goes in chunks.
    # It has to be this fine: see CONTINUITY_BOUNDS rule 2.
    gstep = 0.01
    bound = CONTINUITY_BOUNDS["ground_z"][0]
    worst = (0.0, 0.0, 0.0)
    n = int(round(lap / gstep))
    for u in _GZ_LATERALS:
        for a in range(0, n, 200000):
            b = min(n, a + 200000)
            Sg = np.arange(a, b + 1, dtype=np.float64) * gstep   # +1 to overlap
            z = C.ground_z(Sg % lap, np.full(Sg.shape, float(u)))
            d = np.abs(np.diff(z)) / gstep
            i = int(d.argmax())
            if d[i] > worst[0]:
                worst = (float(d[i]), float(Sg[i]), float(u))
        # close the lap: last sample back to s = 0
        za = float(C.ground_z((lap - gstep) % lap, float(u)))
        zb = float(C.ground_z(0.0, float(u)))
        r = abs(zb - za) / gstep
        if r > worst[0]:
            worst = (r, 0.0, float(u))
    rows.append(("ground_z (17 laterals)", bound, worst[0], gstep, worst[1],
                 worst[0] <= bound))
    notes.append("ground_z worst at u = %+.1f m" % worst[2])

    # ---- THE DATUM CLOSES ON ITSELF -------------------------------------
    # The exact test, not the sampled one.  ground_z takes s % LAP, so the two
    # sides of the seam are reached as s -> LAP- and s -> 0+.
    d = 1.0e-6
    U = np.array(_GZ_LATERALS, float)
    za = C.ground_z(np.full(U.shape, lap - d), U)
    zb = C.ground_z(np.zeros(U.shape), U)
    gz_bound = CONTINUITY_BOUNDS["ground_z"][0]
    clo = float(np.abs(np.asarray(za) - np.asarray(zb)).max())
    rows.append(("ground_z LAP closure", TOL_CLOSURE_M, clo, d, 0.0,
                 clo <= TOL_CLOSURE_M))
    notes.append("closure measured %.3e m against a %.1e m tolerance, stepping "
                 "back %.0e m from the seam; the datum's own slope bound of "
                 "%.4f m/m accounts for %.1e m of that.  v1.0.1 measured "
                 "6.75e-03 m here" % (clo, TOL_CLOSURE_M, d, gz_bound,
                                      gz_bound * d))

    ok = all(r[5] for r in rows)
    if verbose:
        for r in rows:
            print("  %-4s %-34s bound %10.6f  measured %10.6f  at s = %8.2f  "
                  "(step %.2f m)" % ("ok" if r[5] else "FAIL",
                                     r[0], r[1], r[2], r[4], r[3]))
        for nline in notes:
            print("       " + nline)
    return ok, rows, notes


# ===========================================================================
# 15.  PROVENANCE
# ===========================================================================

def summary():
    """A small dict every builder should stamp onto its root collection, so a
    finished .blend records which contract it was built against and the assembly
    gate can diff them instead of guessing."""
    return dict(
        contract_version=__version__,
        lap_m=LAP,
        half_width_3115=float(half_width(_S_PIT_OPEN)),
        half_width_250=float(half_width(_S_PIT_CLOSE)),
        verge_edge_3115=float(verge_edge(_S_PIT_OPEN)),
        platform_fall=PLATFORM_FALL,
        verge_drain_m=VERGE_DRAIN_M,
        apron_z=APRON_Z,
        apron_tie_m=APRON_TIE_M,
        apron_joint_lap_m=APRON_JOINT_LAP_M,
        apron_joint_depth_m=APRON_JOINT_DEPTH_M,
        barrier_max_lateral_rate=BARRIER_MAX_LATERAL_RATE,
        corridor_smooth_k_m=CORRIDOR_SMOOTH_K_M,
        # v1.2.0.  A .blend stamped with these can be told apart from a 1.1.1
        # build by NUMBERS and not by a version string a rebuild might forget.
        corridor_bias_m=CORRIDOR_BIAS_M,
        owned_capped_frac=[float((COR.off_declared[s] - COR.off[s] > 1e-9).mean())
                           for s in (+1, -1)],
        owned_max_pull_in_m=[float((COR.off_declared[s] - COR.off[s]).max())
                             for s in (+1, -1)],
        transit_drive_len_m=TRANSIT_DRIVE_LEN_M,
        transit_drive_clear_m=TRANSIT_DRIVE_CLEAR_M,
        car_box=[CAR_BODY_LEN_M, CAR_BODY_W_M, CAR_BODY_H_M],
        pit_wall_s0=PIT_WALL_S0,
        pit_override_ramp_m=PIT_OVERRIDE_RAMP_M,
        undulation_cells_per_lap=list(_UND_CELLS),
        platform_margin_m=PLATFORM_MARGIN_M,
        corridor_owner=CORRIDOR_OWNER,
        corridor_delete=list(CORRIDOR_DELETE_NAMES),
        transit_wall=[TRANSIT_WALL_S0, TRANSIT_SOUTH_S1, TRANSIT_NORTH_S1],
        access_total_m=ACCESS_TOTAL,
        sun_energy=SUN_ENERGY,
        sun_color=list(SUN_COLOR),
        exposure=REFERENCE_EXPOSURE_EXTERIOR,
        view_transform=VIEW_TRANSFORM,
        tol=dict(datum=TOL_DATUM_M, seam=TOL_SEAM_M, coplanar=TOL_COPLANAR_M,
                 closure=TOL_CLOSURE_M),
    )


def stamp(datablock):
    """Write `summary()` onto any Blender ID as custom properties."""
    for k, v in summary().items():
        datablock["wc_" + k] = json.dumps(v) if isinstance(v, (list, dict)) else v


# ===========================================================================
# 16.  SELF TEST
# ===========================================================================

def selftest(verbose=True):
    """Numeric verification of every claim this module makes.  -> (ok, report)."""
    import io
    out = io.StringIO()
    fails = []
    n_chk = [0]

    def chk(name, cond, detail=""):
        n_chk[0] += 1
        (out.write("  ok   %-52s %s\n" % (name, detail)) if cond
         else (out.write("  FAIL %-52s %s\n" % (name, detail)), fails.append(name)))

    out.write("world_contract %s  self test\n" % __version__)
    out.write("\n[1] centreline\n")
    chk("element re-integration vs published start_world",
        ELEMENT_REINTEGRATION_MAX_DEV_M < 0.01,
        "max dev %.4f m" % ELEMENT_REINTEGRATION_MAX_DEV_M)
    chk("loop closure", ELEMENT_CLOSURE_M < 0.05, "%.4f m" % ELEMENT_CLOSURE_M)
    pts = np.array([[p[0], p[1]] for p in SPEC["centerline"]["points"]])
    S, U = project(pts[:, 0], pts[:, 1])
    chk("202 published control points lie on the centreline",
        np.abs(U).max() < 0.15, "max |u| = %.4f m" % np.abs(U).max())
    lap_sum = sum(float(e["length_m"]) for e in SPEC["elements"])
    chk("element lengths sum to LAP", abs(lap_sum - LAP) < 1e-6,
        "%.4f vs %.1f" % (lap_sum, LAP))

    out.write("\n[2] elevation\n")
    for p in SPEC["elevation"]["station_z_pvi"]:
        if p["vertical_curve_len_m"] == 0.0:
            chk("PVI s=%.0f passes through z=%.3f" % (p["s"], p["z"]),
                abs(elevation_c(p["s"]) - p["z"]) < 1e-9,
                "%.6f" % elevation_c(p["s"]))
    zr = elevation_c(np.arange(0.0, LAP, 1.0))
    chk("elevation range matches headline",
        abs((zr.max() - zr.min()) - SPEC["headline"]["elevation_range_m"]) < 0.25,
        "%.3f vs %.3f" % (zr.max() - zr.min(),
                          SPEC["headline"]["elevation_range_m"]))

    out.write("\n[3] half_width  (THE FIX)\n")
    for (s, want) in ((3115.0, 8.0), (250.0, 8.0), (3055.0, 7.0), (310.0, 7.0),
                      (0.0, 8.0), (3400.0, 8.0), (100.0, 8.0),
                      (_S_HAIRPIN_0, 7.5), (_S_HAIRPIN_1, 7.5),
                      (_S_ESSES_0, 6.5), (_S_ESSES_1, 6.5),
                      (700.0, 7.0), (2500.0, 7.0)):
        chk("half_width(%.4f) == %.3f" % (s, want),
            abs(half_width(s) - want) < 1e-9, "%.6f" % half_width(s))
    mid = 0.5 * (3055.0 + 3115.0)
    chk("transition is LINEAR at its midpoint",
        abs(half_width(mid) - 7.5) < 1e-9, "%.6f" % half_width(mid))
    chk("verge_edge(3115) == 10.5", abs(verge_edge(3115.0) - 10.5) < 1e-9,
        "%.6f" % verge_edge(3115.0))

    out.write("\n[4] ground_z\n")
    Sg = np.arange(0.0, LAP, 1.0)
    for u in (0.0,):
        d = np.abs(ground_z(Sg, np.full_like(Sg, u)) - elevation_c(Sg))
        chk("|ground_z(s,0) - elevation_c(s)| is only crown+undulation",
            d.max() < 0.05, "max %.4f m" % d.max())
    # continuity across the verge edge
    E = verge_edge(Sg)
    for side in (+1, -1):
        a = ground_z(Sg, (E - 1e-4) * side)
        b = ground_z(Sg, (E + 1e-4) * side)
        chk("ground_z is continuous at verge_edge, side %+d" % side,
            np.abs(a - b).max() < 1e-5, "max step %.2e m" % np.abs(a - b).max())
    # banking actually reaches the runoff
    e10 = _EL_BY_TAG["T10"]
    s10 = e10["s0"] + e10["L"] * 0.5
    hi = ground_z(s10, -verge_edge(s10))
    lo = ground_z(s10, +verge_edge(s10))
    chk("T10 is banked across the full section",
        (hi - lo) > 1.0, "outside-inside = %+.3f m over %.1f m" % (hi - lo,
                                                                  2 * verge_edge(s10)))
    b45 = ground_z(s10, -45.0) - ground_z(s10, -verge_edge(s10))
    chk("runoff platform falls from the BANKED edge, not the centreline",
        abs(b45 - PLATFORM_FALL * (45.0 - verge_edge(s10))) < 1e-9,
        "%.4f m over %.1f m" % (b45, 45.0 - verge_edge(s10)))
    old = elevation_c(s10) + PLATFORM_FALL * (45.0 - verge_edge(s10))
    new = ground_z(s10, -45.0)
    chk("... and that is what the old barriers datum got wrong",
        abs(new - old) > 0.30, "contract - old = %+.3f m at T10 apex, 45 m out"
        % (new - old))

    out.write("\n[5] runoff programme\n")
    for side in (+1, -1):
        bo = barrier_offset(Sg, side)
        pe = platform_edge(Sg, side)
        chk("barrier_offset side %+d is finite and sane" % side,
            np.isfinite(bo).all() and bo.min() > verge_edge(Sg).min(),
            "%.2f .. %.2f m" % (bo.min(), bo.max()))
        # THE FORMULA, checked as an identity rather than against a hard label.
        # v1.0.x compared `pe` against a margin picked by `barrier_type`, which is
        # a STEP, while `platform_edge` uses `wallw`, which is a RAMP.  The two
        # disagree wherever a wall's declared ramp outlives its label — and on the
        # pit straight it does, because the pit-wall PIN holds the barrier line at
        # circuit y = +11.5 for 45 m past the last B_CONCRETE station.  So the
        # identity is checked exactly, and the floor is checked against the
        # tightest margin the contract declares anywhere.
        wallwv = COR.sample("wallw", Sg, side)
        mv = PLATFORM_MARGIN_M + (PLATFORM_MARGIN_WALL_M - PLATFORM_MARGIN_M) * wallwv
        chk("platform_edge IS max(barrier, runoff) + margin(wallw), side %+d" % side,
            np.abs(pe - (_smax(bo, runoff_edge(Sg, side)) + mv)).max() < 1e-12,
            "max residual %.2e m over %d stations"
            % (np.abs(pe - (_smax(bo, runoff_edge(Sg, side)) + mv)).max(), Sg.size))
        chk("platform_edge clears the barrier by the wall margin, side %+d" % side,
            (pe >= bo + PLATFORM_MARGIN_WALL_M - 1e-9).all(),
            "%.2f .. %.2f m; min clearance beyond the barrier %.3f m of %.3f"
            % (pe.min(), pe.max(), (pe - bo).min(), PLATFORM_MARGIN_WALL_M))
        free = wallwv <= 1e-9
        chk("... and by the FULL margin wherever no wall is declared, side %+d" % side,
            (pe[free] >= bo[free] + PLATFORM_MARGIN_M - 1e-9).all(),
            "%.1f %% of the lap has no wall weight; min clearance there %.3f m of "
            "%.1f  (%.1f %% of stations are labelled B_CONCRETE)"
            % (100.0 * free.mean(), (pe[free] - bo[free]).min(), PLATFORM_MARGIN_M,
               100.0 * (barrier_type(Sg, side) == B_CONCRETE).mean()))
    # spec §9 pins
    pit = np.array([3300.0, 3500.0, 0.0, 120.0])
    chk("pit-straight south barrier pinned to circuit y = -19",
        np.abs(barrier_offset(pit, -1) - 19.0).max() < 0.35,
        "%.3f .. %.3f" % (barrier_offset(pit, -1).min(),
                          barrier_offset(pit, -1).max()))
    chk("pit wall pinned to circuit y = +11.5",
        np.abs(barrier_offset(np.array([3500.0, 3600.0, 50.0]), +1) - 11.5).max() < 0.35,
        "%.3f" % barrier_offset(3550.0, +1))

    out.write("\n[6] transit route / access ribbon\n")
    x, y, h = access_route_point(0.0)
    chk("route starts on the glass plane x = +15", abs(x - 15.0) < 1e-9 and abs(y) < 1e-9)
    x, y, h = access_route_point(ACCESS_L2)
    chk("apron run ends at (64.60, 0)", abs(x - 64.6) < 1e-6 and abs(y) < 1e-6,
        "(%.3f, %.3f)" % (x, y))
    x, y, h = access_route_point(ACCESS_MERGE)
    chk("merge arc ends at spec (161.02, 35.09)",
        math.hypot(x - 161.02, y - 35.09) < 0.02, "(%.3f, %.3f)" % (x, y))
    Sm, Um = project(np.array([x]), np.array([y]))
    chk("... which is 5.02 m left of the pit-straight centreline",
        abs(float(Um[0]) - ACCESS_MERGE_LATERAL) < 0.03, "u = %+.3f m" % Um[0])
    T = np.linspace(0.0, ACCESS_TOTAL, 2000)
    zt = access_z(T, np.zeros_like(T))
    chk("ribbon is DEAD FLAT z=0.000 for the first 49.6 m",
        np.abs(zt[T <= ACCESS_L2]).max() < 1e-9,
        "max |z| = %.2e" % np.abs(zt[T <= ACCESS_L2]).max())
    Xr, Yr, Hr = access_route_arrays(T)
    Sr, Ur = project(Xr, Yr)
    zg = ground_z(Sr, Ur)
    chk("ribbon IS ground_z past the merge point",
        np.abs(zt[T > ACCESS_MERGE] - zg[T > ACCESS_MERGE]).max() < 1e-9,
        "max %.2e m" % np.abs(zt[T > ACCESS_MERGE] - zg[T > ACCESS_MERGE]).max())
    vin, vout = access_edges(T)
    uin = Ur + vin
    chk("ribbon never crosses inboard of verge_edge",
        (uin >= verge_edge(Sr) - 1e-6).all(),
        "min clearance %+.4f m" % (uin - verge_edge(Sr)).min())
    tclip = T[np.argmax((verge_edge(Sr) - Ur) > -ACCESS_HALF_W)]
    chk("clip engages before the merge (this is the overlap that was there)",
        tclip < ACCESS_MERGE, "first clipped at t = %.1f m of %.1f"
        % (tclip, ACCESS_MERGE))

    # --- the corridor MOUTH.  assembly finding #2: three modules used three margins
    #     for the same boundary and 64 m2 at the Beat-3 -> Beat-4 hinge had no ground.
    xm = np.arange(4.0, 17.001, 0.10)
    ym = np.arange(-14.0, 14.001, 0.25)
    Xm, Ym = np.meshgrid(xm, ym, indexing="ij")
    xm2, ym2 = Xm.ravel(), Ym.ravel()
    worst = 0.0
    for mg in (0.0, ACCESS_RIBBON_SAW_M, ACCESS_CORRIDOR_MARGIN_M, 9.0):
        r = in_access_ribbon(xm2, ym2, margin=mg)
        if r.any():
            worst = max(worst, abs(float(xm2[r].min()) - ACCESS_GLASS_X))
    chk("the ribbon's start cap is the glass plane for EVERY margin",
        worst <= 0.101, "max start-cap error %.3f m over margins 0 .. 9 m" % worst)
    zm, om = world_ground_z(xm2, ym2)
    cm = road_corridor_mask(xm2, ym2)
    void = np.isnan(zm) & cm
    # WHAT THIS CHECKS, AND WHAT IT CANNOT.  `world_ground_z` is the MODEL.  It
    # returns a finished height and an owner's name from arithmetic; no module has
    # to have laid a polygon for it to answer.  So `isnan(world_ground_z)` finds
    # ground that is DECLARED BY NOBODY -- a real and different defect -- and by
    # construction it CANNOT find ground that is declared, owned, and never built.
    # 390 m2 of the pit-exit apron was in the second category and both of these
    # checks passed cleanly over it the whole time.
    #
    # This module may not import bpy (Rule 2), so the mesh-side question lives in
    # `tools/ground_coverage_probe.py`, which casts a ray straight down at each
    # declared sample and requires a face near the declared height.  Do not read
    # either check below as evidence that anything was built.
    chk("no ground is cut that nobody DECLARES, at the glass mouth "
        "(model-side: says nothing about whether a face exists)",
        void.sum() == 0, "%d of %d samples (%.1f m2)  was 1276 (~64 m2)"
        % (void.sum(), void.size, void.sum() * 0.10 * 0.25))
    Tv = np.arange(0.0, ACCESS_TOTAL + 1e-6, 0.5)
    Vv = np.arange(-12.0, 12.001, 0.25)
    TT, VV = np.meshgrid(Tv, Vv, indexing="ij")
    Xv, Yv, Hv = access_route_arrays(TT.ravel())
    xv = Xv - np.sin(Hv) * VV.ravel()
    yv = Yv + np.cos(Hv) * VV.ravel()
    zv, ov = world_ground_z(xv, yv)
    voidr = np.isnan(zv) & road_corridor_mask(xv, yv)
    chk("... and none along the whole 244 m ribbon corridor "
        "(model-side, same caveat)",
        voidr.sum() == 0, "%d of %d samples (%.1f m2)"
        % (voidr.sum(), voidr.size, voidr.sum() * 0.5 * 0.25))

    out.write("\n[7] beat-4 corridor\n")
    for side, lbl in ((+1, "north concrete"), (-1, "south tyre wall")):
        t0, t1 = transit_wall_span(side)
        Tw = np.linspace(t0, t1, 400)
        P = np.array([transit_wall_point(t, side) for t in Tw])
        Sw, Uw = project(P[:, 0], P[:, 1])
        clear = np.abs(Uw) - verge_edge(Sw)
        cxc, cyc = world_to_circuit(P[:, 0], P[:, 1])
        chk("%s clears the racing surface" % lbl, clear.min() > 1.5,
            "%.1f m of wall, min clearance %.3f m (ends at circuit (%.0f, %+.2f))"
            % (t1 - t0, clear.min(), cxc[-1], cyc[-1]))
        _, vo = access_edges(Tw)
        off = abs(TRANSIT_NORTH_OFFSET_M if side > 0 else TRANSIT_SOUTH_OFFSET_M)
        chk("%s stands clear of the access ribbon" % lbl,
            (off - np.maximum(vo, ACCESS_HALF_W)).min() > 0.9,
            "min gap %.3f m" % (off - np.maximum(vo, ACCESS_HALF_W)).min())
    chk("the camera's walled run is the spec-literal 90 m",
        abs((TRANSIT_NORTH_S1 - TRANSIT_WALL_S0) - 90.0) < 1e-9,
        "%.1f m" % (TRANSIT_NORTH_S1 - TRANSIT_WALL_S0))
    xb, _, _ = access_route_point(TRANSIT_WALL_S0)
    chk("corridor starts clear of the forecourt bollard line",
        xb > FORECOURT_BOLLARD_X + 1.0,
        "wall starts at world x = %.1f, bollards at %.1f" % (xb, FORECOURT_BOLLARD_X))
    chk("the pit-exit portal is inside the walled run",
        TRANSIT_WALL_S0 < (TRANSIT_PORTAL_X - ACCESS_GLASS_X) < TRANSIT_SOUTH_S1,
        "portal at t = %.1f" % (TRANSIT_PORTAL_X - ACCESS_GLASS_X))

    out.write("\n[8] lighting\n")
    n = math.sqrt(sum(v * v for v in SUN_DIR))
    chk("SUN_DIR is unit", abs(n - 1.0) < 1e-6, "|d| = %.8f" % n)
    chk("SUN_ELEV_DEG matches SUN_DIR",
        abs(math.degrees(math.asin(SUN_DIR[2])) - SUN_ELEV_DEG) < 1e-4)
    chk("SKY_SUN_ROTATION_DEG == 90 - bearing",
        abs(SKY_SUN_ROTATION_DEG - (90.0 - SUN_BEARING_DEG)) < 1e-4)
    lr = lambert_radiance(0.18)
    chk("lambert_radiance(0.18) mean == 1.4888",
        abs(sum(lr) / 3.0 - 1.4888) < 5e-4, "(%.4f, %.4f, %.4f) mean %.4f"
        % (lr[0], lr[1], lr[2], sum(lr) / 3.0))
    d2d = sum(E_DIRECT_HORIZONTAL) / sum(SKY_IRRADIANCE)
    chk("DIRECT_TO_DIFFUSE is derived, not asserted",
        abs(d2d - DIRECT_TO_DIFFUSE) < 2e-3, "%.4f" % d2d)

    out.write("\n[9] the apron tie  (declared flat z=0 vs the crowned road)\n")
    # THE WINDOW IS FOUND, NOT TYPED.  It was `np.arange(3200.0, 3421.0, 5.0)`
    # against a real apron that runs s 3173..3470: the check saw 221 m of 297 m
    # (74 %) and was blind to 27 m at the west end and 49 m at the east end.  The
    # east-end blind spot is exactly the ground v1.1.1 added when it moved the pit
    # wall 17.7 m, plus the taper past it -- so the one stretch of apron that had
    # just changed was the one stretch this check did not look at, and it passed
    # with `(apron_zone > 0.9).mean() == 1.0000`, maximum margin, throughout.
    #
    # This is the third instance of one shape in this module's neighbourhood: a
    # window sized to a literal, or to a contract quantity that is not the one
    # under test, silently reporting the slice it can see as the whole.  The other
    # two were `build_apron_platform`'s station window and its `UMAX`.  A probe
    # whose reported range maximum is its own window boundary is clipping, and
    # that number should always be read as suspicious.
    _scan = np.arange(3050.0, 3600.0, 0.5)
    _hit = np.nonzero(apron_zone(_scan, +1) > 0.5)[0]
    _s0 = float(_scan[_hit[0]]) if len(_hit) else 3200.0
    _s1 = float(_scan[_hit[-1]]) if len(_hit) else 3420.0
    sa = np.arange(_s0, _s1 + 5.0, 5.0)
    chk("the apron-tie check's own window covers the whole declared apron",
        sa.min() <= _s0 + 1e-9 and sa.max() >= _s1 - 5.0,
        "apron_zone > 0.5 runs s %.1f..%.1f; this window is s %.1f..%.1f"
        % (_s0, _s1, sa.min(), sa.max()))
    chk("pit-exit apron zone found on the left of the pit straight",
        (apron_zone(sa, +1) > 0.9).mean() > 0.8,
        "s %.0f..%.0f, circuit x %.0f..%.0f  (%.0f m of apron, found not typed)"
        % (sa.min(), sa.max(), sa.min() - LAP, sa.max() - LAP, _s1 - _s0))
    chk("no apron tie anywhere on the right", apron_zone(SGRID, -1).max() < 1e-9)

    # THE FOUR DECLARED RECTANGLES ARE NOT DISJOINT, AND SOMETHING DEPENDS ON IT.
    # `apron.x1` and `pit_lane.x0` are both `_PIT_NOSE_X`, derived, and they moved
    # 17.7 m west with the pit wall in v1.1.1.  `garages.x0 = -245` and
    # `paddock.x0 = -480` are raw spec literals and did not move, so both reach
    # into the apron rectangle.  `build_architecture.apron_clearance` treats any
    # sample inside pit_lane / garages / paddock as HANDED OVER and cuts the apron
    # slab there, which is only safe while those bay fields actually pave it.
    # Measured on the shipped module build they do -- but nothing checked that,
    # and the identical assumption at the `platform_edge` line is exactly what
    # left 390 m2 declared, owned and unlaid (R2-132).
    #
    # This check does not make them disjoint: doing so would move real geometry
    # and a world rebuild is the owner's call.  It PINS the overlap so the day one
    # of these rectangles moves again, someone is told, instead of finding out
    # from a hole.
    _ovr = {}
    for _a, _b in itertools.combinations(sorted(APRON_REGIONS_CIRCUIT), 2):
        _ax0, _ax1, _ay0, _ay1 = APRON_REGIONS_CIRCUIT[_a]
        _bx0, _bx1, _by0, _by1 = APRON_REGIONS_CIRCUIT[_b]
        _w = min(_ax1, _bx1) - max(_ax0, _bx0)
        _h = min(_ay1, _by1) - max(_ay0, _by0)
        if _w > 0.0 and _h > 0.0:
            _ovr["%s x %s" % (_a, _b)] = _w * _h
    _KNOWN = {"apron x garages": 301.06, "apron x paddock": 1137.19}
    _same = (set(_ovr) == set(_KNOWN) and
             all(abs(_ovr[k] - _KNOWN[k]) < 0.05 for k in _KNOWN))
    chk("the declared platform rectangles overlap by exactly the known amount",
        _same, "%s  (total %.2f m2; these are the pairs `apron_clearance` hands "
        "over on, and a change here silently re-cuts the apron slab)"
        % (", ".join("%s %.2f m2" % (k, v) for k, v in sorted(_ovr.items())),
           sum(_ovr.values())))
    # "BEYOND THE TIE" MEANS apron_zone == 1, NOT > 0.999.  With the window above
    # widened to the real apron, `> 0.999` admits s 3420..3470, where apron_zone
    # is 0.99987 -- still INSIDE the tie's blend -- and the exactness assertion
    # failed at 5.325e-05 m.  That is not a defect in the apron; it is the check
    # having been given a predicate that did not mean what its name said, and
    # getting away with it for as long as its station window stopped at 3420 where
    # apron_zone is exactly 1 anyway.  Verified against HEAD: the old check reads
    # 0.00e+00 over s 3200..3420 and 5.325e-05 m over the true extent.
    #
    # The tolerance is NOT relaxed.  The claim is split into the two claims it was
    # always making: exact where the tie has finished, and bounded where it has
    # not -- and the second one prints its worst number every run.
    core = sa[apron_zone(sa, +1) >= 1.0]
    far = ground_z(core, np.full_like(core, 30.0))
    chk("apron is exactly APRON_Z beyond the tie (apron_zone == 1)",
        np.abs(far - APRON_Z).max() < 1e-12,
        "s %.0f..%.0f, max |z| = %.2e m" % (core.min(), core.max(),
                                            np.abs(far).max()))
    # NO SECOND CHECK ON THE BLEND BAND.  I added one ("under 1 mm of APRON_Z")
    # and it failed at 209 mm, because the blend band is precisely where the
    # ground is still ramping from the crowned road to the flat apron -- 209 mm is
    # the tie doing its job.  That band is already bounded, correctly and by
    # gradient rather than by offset, by the two checks immediately below: max
    # cross-grade 3.04 % and max 7.3 mm of longitudinal step per 0.5 m, the second
    # of which already sweeps s 3150..3480 and so covers the whole widened window
    # with room either side.  A third check with a bound I picked would have been
    # noise at best and a number to tune at worst.
    lat = np.linspace(verge_edge(3300.0), 30.0, 400)
    prof = ground_z(np.full_like(lat, 3300.0), lat)
    grad = np.abs(np.diff(prof) / np.diff(lat)).max()
    chk("the tie is a gutter, not a step",
        grad < 0.060, "max cross-grade %.2f %%, %.0f mm rise over %.1f m"
        % (100.0 * grad, 1000.0 * (prof.max() - prof.min()), APRON_TIE_M))
    dz = np.abs(np.diff(ground_z(np.arange(3150.0, 3480.0, 0.5),
                                 np.full(660, 30.0))))
    chk("the apron's far edge ramps longitudinally, no step",
        dz.max() < 0.010, "max %.1f mm per 0.5 m of station" % (1000 * dz.max()))
    chk("the right-hand platform still falls at -1.6 %",
        abs((ground_z(3300.0, -25.0) - ground_z(3300.0, -verge_edge(3300.0)))
            / (25.0 - verge_edge(3300.0)) - PLATFORM_FALL) < 1e-9)

    out.write("\n[10] mask / query coverage\n")
    gx, gy = np.meshgrid(np.arange(-700.0, 700.0, 25.0),
                         np.arange(-300.0, 1000.0, 25.0))
    gx = gx.ravel(); gy = gy.ravel()
    m = road_corridor_mask(gx, gy)
    zz, ow = world_ground_z(gx, gy)
    chk("road_corridor_mask runs at terrain scale",
        m.shape == gx.shape, "%d points, %.1f %% inside the corridor"
        % (gx.size, 100.0 * m.mean()))
    chk("world_ground_z answers everywhere the mask is true",
        np.isfinite(zz[m]).all(),
        "owners: %s" % ", ".join(sorted(set(ow[m].tolist()))))
    chk("world_ground_z hands the rest to terrain or to the apron",
        set(np.unique(ow[~m]).tolist()) <= {OWNER_TERRAIN, OWNER_APRON},
        "%.1f %% terrain, %.1f %% declared apron"
        % (100.0 * (ow[~m] == OWNER_TERRAIN).mean(),
           100.0 * (ow[~m] == OWNER_APRON).mean()))
    # exhaustive AND disjoint: every point gets exactly one owner, and the three
    # masks a builder actually keys off never claim the same square metre
    cut = road_corridor_mask(gx, gy)
    pave = apron_platform_mask(gx, gy)
    chk("road corridor and architecture's paving are disjoint",
        not (cut & pave).any(), "%d overlapping samples" % int((cut & pave).sum()))
    chk("terrain's ground is exactly the complement",
        ((~cut & ~pave) == (ow == OWNER_TERRAIN)).all(),
        "%.1f %% of the sampled world" % (100.0 * (ow == OWNER_TERRAIN).mean()))
    raww = apron_platform_mask(gx, gy, raw=True)
    chk("the spec's declared apron rectangles DO overlap the circuit",
        (raww & cut).any(),
        "%d of %d declared samples are road, and are now cut"
        % (int((raww & cut).sum()), int(raww.sum())))

    out.write("\n[11] public API: scalar in -> scalar out, array in -> array out\n")
    sa = np.array([100.0, 1000.0, 2200.0, 3400.0])
    ua = np.array([0.0, 5.0, -12.0, 30.0])
    scal = [("ground_z", lambda: ground_z(100.0, 5.0)),
            ("half_width", lambda: half_width(100.0)),
            ("verge_edge", lambda: verge_edge(100.0)),
            ("elevation_c", lambda: elevation_c(100.0)),
            ("access_z", lambda: access_z(30.0, 0.0)),
            ("su_to_world", lambda: su_to_world(100.0, 5.0)[2])]
    ok_s = all(isinstance(f(), float) for _, f in scal)
    chk("scalar calls return floats", ok_s,
        ", ".join("%s=%.4f" % (n, f()) for n, f in scal))
    arr = [("ground_z", ground_z(sa, ua)), ("half_width", half_width(sa)),
           ("verge_edge", verge_edge(sa)), ("elevation_c", elevation_c(sa)),
           ("barrier_offset", barrier_offset(sa, -1)),
           ("platform_edge", platform_edge(sa, -1)),
           ("runoff_edge", runoff_edge(sa, -1)),
           ("micro_window", micro_window(sa, ua)),
           ("kerb_top_z", kerb_top_z(sa, ua))]
    chk("array calls broadcast to the input shape",
        all(np.shape(v) == sa.shape for _, v in arr),
        ", ".join("%s%s" % (n, np.shape(v)) for n, v in arr))
    chk("ground_z(s, lat, side) == ground_z(s, side*lat)",
        abs(ground_z(2196.0, 45.0, -1) - ground_z(2196.0, -45.0)) < 1e-12,
        "%.5f" % ground_z(2196.0, 45.0, -1))
    chk("everything in __all__ exists",
        all(hasattr(sys.modules[__name__], n) for n in __all__),
        "%d public names" % len(__all__))
    chk("summary() is JSON-serialisable", bool(json.dumps(summary())),
        "contract_version=%s" % summary()["contract_version"])

    # =====================================================================
    out.write("\n[12] CONTINUITY  (v1.1.0 — the gate defect 1 got past)\n")
    ok_c, rows, notes = continuity_report()
    for (name, bound, meas, cstep, at_s, good) in rows:
        chk(name, good, "%10.6f of %10.6f  at s = %8.2f  (sampled %.2f m)"
            % (meas, bound, at_s, cstep))
    for nline in notes:
        out.write("       %s\n" % nline)

    out.write("\n[12b] the mechanisms of defect 1, closed at the source\n")
    # (a) the sentinel is finite and is never fed to a mean
    chk("maxoff sentinel is finite and modest",
        MAXOFF_NONE_M < 1000.0 and
        MAXOFF_NONE_M > max(float(COR.prog[+1].max()), float(COR.prog[-1].max())),
        "%.1f, against a max programme offset of %.2f m"
        % (MAXOFF_NONE_M, max(float(COR.prog[+1].max()),
                              float(COR.prog[-1].max()))))
    # (b) the runoff programme itself respects the rate it declares, so the
    #     erosion is a guard and not a crutch.  If this fails, RUNOFF_ZONES has
    #     been given a ramp too short for its width and the TABLE is the defect.
    for side in (+1, -1):
        r, i = _cyclic_rate(COR.prog[side], PS)
        chk("RUNOFF_ZONES' own line is inside the declared rate, side %+d" % side,
            r <= BARRIER_MAX_LATERAL_RATE,
            "%.4f of %.4f m/m at s = %.0f  (the PRE-CAP programme: this is the "
            "field the pit-straight masks used to step 46.31 m)"
            % (r, BARRIER_MAX_LATERAL_RATE, SGRID[i]))
    # (c) the erosion is exact, not approximate
    for side in (+1, -1):
        # v1.2.0: against `off_declared`, NOT `off`.  `off` now carries the
        # ownership cap as well, and a row that says "erosion" while measuring
        # erosion + ownership has stopped measuring what it claims.
        d = COR.capped[side] - COR.off_declared[side]
        chk("erosion only ever moves the line INBOARD, side %+d" % side,
            float(d.min()) >= -1e-12,
            "identical on %.1f %% of the lap; max pull-in %.2f m"
            % (100.0 * (d < 1e-9).mean(), float(d.max())))
    # (d) THE INVARIANT build_barriers asserts at import.  If the contract ever
    #     breaks it, build_barriers raises and the whole world build stops.
    Sf = np.arange(0.0, LAP, 0.25)
    for side in (+1, -1):
        clr = barrier_offset(Sf, side) - verge_edge(Sf)
        chk("barrier line clears verge_edge by >= 1.000 m, side %+d" % side,
            float(clr.min()) >= 1.0 - 1e-9,
            "min %.4f m at s = %.2f (the pit wall: spec S10.7 y=+11.5 against a "
            "verge edge at 10.5)" % (clr.min(), Sf[clr.argmin()]))
    chk("smooth max/min deviate by at most k/4",
        abs(float(_smax(np.array([0.0]), np.array([0.0]))[0])
            - 0.25 * CORRIDOR_SMOOTH_K_M) < 1e-12
        and 0.25 * CORRIDOR_SMOOTH_K_M <= BARRIER_JITTER_MAX_M,
        "k = %.3f m -> %.3f m, inside BARRIER_JITTER_MAX_M = %.3f m"
        % (CORRIDOR_SMOOTH_K_M, 0.25 * CORRIDOR_SMOOTH_K_M, BARRIER_JITTER_MAX_M))

    out.write("\n[13] access_z IS ground_z  (defect 3)\n")
    Ta = np.linspace(0.0, ACCESS_TOTAL, 1500)
    Va = np.linspace(-8.0, 8.0, 65)
    TT, VV = np.meshgrid(Ta, Va, indexing="ij")
    Xa, Ya, Ha = access_route_arrays(TT.ravel())
    Sa2, Ua2 = project(Xa - np.sin(Ha) * VV.ravel(), Ya + np.cos(Ha) * VV.ravel())
    dz = np.abs(access_z(TT.ravel(), VV.ravel()) - ground_z(Sa2, Ua2))
    chk("access_z - ground_z is IDENTICALLY zero on the ribbon",
        float(dz.max()) == 0.0, "max %.3e m over %d samples  (was 90.2 mm)"
        % (dz.max(), dz.size))
    flat = TT.ravel() <= ACCESS_L2
    chk("... and spec S10.3(b)'s flat 49.6 m still holds EXACTLY",
        float(np.abs(access_z(TT.ravel()[flat], VV.ravel()[flat])).max()) == 0.0,
        "max |z| = %.3e m over the apron run, all laterals"
        % np.abs(access_z(TT.ravel()[flat], VV.ravel()[flat])).max())

    out.write("\n[14] the track/apron joint  (defect 4)\n")
    chk("APRON_JOINT_LAP_M is owned HERE, not by two getattr fallbacks",
        abs(APRON_JOINT_LAP_M - 0.050) < 1e-12, "%.3f m" % APRON_JOINT_LAP_M)
    chk("APRON_JOINT_DEPTH_M is owned HERE",
        abs(APRON_JOINT_DEPTH_M - 0.005) < 1e-12, "%.3f m" % APRON_JOINT_DEPTH_M)
    chk("the joint is inside the seam tolerance it is meant to remove",
        APRON_JOINT_DEPTH_M < TOL_COPLANAR_M and APRON_JOINT_LAP_M > TOL_SEAM_M,
        "lap %.3f m > TOL_SEAM %.3f, invert %.3f m < TOL_COPLANAR %.3f"
        % (APRON_JOINT_LAP_M, TOL_SEAM_M, APRON_JOINT_DEPTH_M, TOL_COPLANAR_M))

    # ------------------------------------------------------------------ [15]
    out.write("\n[15] THE PIT WALL IS NOT IN THE TRANSIT LANE  (defect #46, v1.1.1)\n")
    #
    # THE MEASUREMENT, and it is written so it can be pointed at ANY declared wall
    # start, not just the one this revision publishes — see `_wall_clear` below.
    # A check that can only be evaluated at the value it was written for cannot
    # fail, which is R2-012.
    _T = np.linspace(0.0, ACCESS_TOTAL, 24001)
    _X, _Y, _H = access_route_arrays(_T)
    _vi, _vo = access_edges(_T)
    _So, _Uo = project(_X - np.sin(_H) * _vo, _Y + np.cos(_H) * _vo)
    # Binned per station, with -inf where the ribbon does not reach — NOT
    # interpolated.  `np.interp` over a station axis the ribbon only covers in
    # patches extrapolates its endpoint across the 240 m of pit straight the
    # ribbon is nowhere near, which reads as a 65 m intrusion that is not there.
    _BIN = 0.25
    _NB = int(round(LAP / _BIN))
    _ribmax = np.full(_NB, -np.inf)
    np.maximum.at(_ribmax, (np.rint(_So / _BIN).astype(np.int64)) % _NB, _Uo)

    def _wall_clear(s_start):
        """min (wall face - ribbon outboard edge) over a wall starting at s_start.

        Negative means the wall stands IN the pit-exit road.  Stations the ribbon
        does not reach are not counted — there is nothing there to be clear of.
        """
        _e1 = _pit_straight_station(GARAGE_X1)
        _d = np.arange(0.0, (_e1 - s_start) % LAP, _BIN)
        _sw = (s_start + _d) % LAP
        _face = PIT_WALL_Y + PIT_WALL_TERMINAL_FLARE_M * (
            1.0 - np.clip(_d / PIT_WALL_TERMINAL_M, 0.0, 1.0))
        _u = _ribmax[(np.rint(_sw / _BIN).astype(np.int64)) % _NB]
        _m = np.isfinite(_u)
        return float(np.min(_face[_m] - _u[_m])) if _m.any() else float("inf")

    _clear = _wall_clear(PIT_WALL_S0)
    chk("the pit wall never stands in the pit-exit road",
        _clear > 0.0,
        "min face-to-ribbon %.3f m over the whole %.1f m wall, nose at s = %.2f "
        "(circuit x %.2f)"
        % (_clear, (pit_wall_span()[1] - pit_wall_span()[0]) % LAP,
           PIT_WALL_S0, PIT_WALL_S0 - LAP))
    # THE SAME CHECK, AGAINST THE ARTEFACT ALREADY KNOWN TO BE BAD.  v1.0.x/v1.1.0
    # started the wall at the declared garage frontage; the assembled world built
    # from it measured ARCH_PitWall 1.067 m inside the car's swept volume.  If this
    # row ever passes, the check has stopped measuring anything.
    _bad_s0 = _pit_straight_station(GARAGE_X0)
    _bad = _wall_clear(_bad_s0)
    chk("... and the check FAILS the wall start v1.1.0 shipped",
        _bad < 0.0,
        "s = %.2f (circuit x %.1f, GARAGE_X0) gives %.3f m — the wall face is "
        "%.3f m INSIDE the ribbon's outboard edge"
        % (_bad_s0, GARAGE_X0, _bad, -_bad))
    chk("the wall's nose is the station the contract derives",
        abs((PIT_WALL_X0 - PIT_WALL_TERMINAL_M) - (PIT_WALL_S0 - LAP)) < 1e-9,
        "nose circuit x %.4f, first full-height unit %.4f, terminal %.2f m"
        % (PIT_WALL_S0 - LAP, PIT_WALL_X0, PIT_WALL_TERMINAL_M))
    chk("pit_wall_face is the flare at the nose and PIT_WALL_Y past the terminal",
        abs(pit_wall_face(PIT_WALL_S0)
            - (PIT_WALL_Y + PIT_WALL_TERMINAL_FLARE_M)) < 1e-9
        and abs(pit_wall_face(PIT_WALL_S0 + PIT_WALL_TERMINAL_M + 1.0)
                - PIT_WALL_Y) < 1e-9
        and np.isnan(pit_wall_face(PIT_WALL_S0 - 5.0)),
        "%.3f at the nose, %.3f past the terminal, NaN before it"
        % (pit_wall_face(PIT_WALL_S0), pit_wall_face(PIT_WALL_S0 + 10.0)))
    # THE TRANSIT KEEP-OUT.  `rim_buildable` must be False where the rim is inside
    # the keep-out and True everywhere else — and it must actually block
    # something, or it is R2-018's gate that is clean on an empty set.  v1.2.0
    # gave it a SECOND reason to say no (ownership, [17]), so the two are
    # separated here: this row is only about the transit.
    _rs = np.arange(0.0, LAP, 1.0)
    _rp_all = np.atleast_2d(corridor_rim(_rs, +1))
    _ko = np.asarray(transit_keepout(_rp_all[:, 0], _rp_all[:, 1]), bool)
    _rb = np.asarray(rim_buildable(_rs, +1), bool)
    chk("rim_buildable blocks the stations where the rim crosses the transit lane",
        _ko.any() and _rs[_ko].min() > 3300.0 and not _rb[_ko].any(),
        "%d of %d stations blocked for the transit, s %.0f..%.0f; side -1 blocks "
        "%d; %d more are blocked by OWNERSHIP ([17])"
        % (int(_ko.sum()), len(_rs), _rs[_ko].min(), _rs[_ko].max(),
           int(np.asarray(transit_keepout(
               *np.atleast_2d(corridor_rim(_rs, -1))[:, :2].T), bool).sum()),
           int((~_rb & ~_ko).sum())))
    chk("... and every transit-blocked rim point really is inside the keep-out",
        bool(np.all(in_access_ribbon(_rp_all[_ko, 0], _rp_all[_ko, 1],
                                     margin=TRANSIT_KEEPOUT_M)
                    | transit_drive_keepout(_rp_all[_ko, 0], _rp_all[_ko, 1]))),
        "ribbon + %.2f m, UNION the driven swept box + %.2f m"
        % (TRANSIT_KEEPOUT_M, TRANSIT_DRIVE_CLEAR_M))

    # ------------------------------------------------------------------ [16]
    out.write("\n[16] A DEPTH BOUND IS NOT A BLACKNESS BOUND  (defect #48, v1.1.1)\n")
    _def_r = float(recess_relative_radiance(0.005, 0.0343))
    _joint_r = float(recess_relative_radiance(0.008, 0.005))
    _lap_r = float(recess_relative_radiance(APRON_JOINT_LAP_M,
                                            APRON_JOINT_DEPTH_M))
    chk("the model calls THE MEASURED DEFECT black",
        recess_is_black(0.005, 0.0343),
        "5 mm wide, 34.3 mm deep -> %.4f of the surface beside it "
        "(bound %.2f); it rendered 3390 px below 0.02 against a track at 0.1729"
        % (_def_r, TOL_RECESS_RADIANCE))
    chk("... and it does NOT call the joints in the same frame black",
        (not recess_is_black(0.008, 0.005))
        and (not recess_is_black(APRON_JOINT_LAP_M, APRON_JOINT_DEPTH_M)),
        "sawn bay joint 8x5 mm -> %.4f, the sealant lap %.0fx%.0f mm -> %.4f"
        % (_joint_r, 1000 * APRON_JOINT_LAP_M, 1000 * APRON_JOINT_DEPTH_M,
           _lap_r))
    chk("the bound separates them by a real margin",
        _def_r < TOL_RECESS_RADIANCE * 0.5 < TOL_RECESS_RADIANCE * 1.5 < _joint_r,
        "defect %.4f (x%.1f under), shallowest legitimate joint %.4f (x%.1f over)"
        % (_def_r, TOL_RECESS_RADIANCE / _def_r, _joint_r,
           _joint_r / TOL_RECESS_RADIANCE))
    # THE POINT OF THE WHOLE SECTION: architecture's DEPTH_LIM = 66 mm passes the
    # defect.  Show that a depth bound cannot express this, at the declared sun.
    chk("a 66 mm DEPTH bound cannot express this",
        recess_is_black(0.005, 0.020) and recess_is_black(0.005, 0.010)
        and (max_recess_depth(0.005) < 0.066),
        "at 5 mm wide the deepest NON-black recess is %.1f mm, not 66 mm; "
        "at 12.47 deg the sun needs %.3f m of run to clear a %.0f mm step"
        % (1000 * max_recess_depth(0.005), 0.0343 * SUN_SHADOW_RATIO, 34.3))
    chk("max_recess_depth inverts the model",
        all(abs(recess_relative_radiance(w, max_recess_depth(w))
                - TOL_RECESS_RADIANCE) < 1e-6
            for w in (0.004, 0.008, 0.05, 0.30)),
        "8 mm -> %.1f mm, 50 mm -> %.1f mm, 300 mm -> %.0f mm"
        % (1000 * max_recess_depth(0.008), 1000 * max_recess_depth(0.050),
           1000 * max_recess_depth(0.300)))
    chk("the model follows the SUN, not a constant",
        recess_relative_radiance(0.10, 0.02) < 1.0
        and abs(SUN_SHADOW_RATIO
                - 1.0 / math.tan(math.radians(SUN_ELEV_DEG))) < 1e-3,
        "SUN_SHADOW_RATIO %.4f = cot(%.3f deg); a 34 mm step casts %.0f mm "
        "of shadow" % (SUN_SHADOW_RATIO, SUN_ELEV_DEG,
                       1000 * 0.0343 * SUN_SHADOW_RATIO))

    # ------------------------------------------------------------------ [17]
    out.write("\n[17] THE CIRCUIT DOES NOT CROSS ITS OWN CORRIDOR  (R2-035, v1.2.0)\n")
    #
    # THE SWEEP.  Every one of the 14 700 stations of the field grid, both sides:
    # put the declared barrier face in world space, project it back, and ask
    # whether it landed inside ANY OTHER leg's road corridor — `half_width + the
    # 0.50 m courtesy margin tools/placement_gate.py judges the world by`, on a
    # leg more than OWNED_SELF_WINDOW_M of arc length away.  The answer must be
    # ZERO.  It is written to take ANY offset function, so it can be pointed at
    # the line already known to be bad; a check that has never failed has not been
    # shown to work.
    _SG = np.arange(_FN) * _FS
    _SX, _SY, _SH, _ = centreline_arrays(_SG)

    def _cross_sweep(offfn):
        r = {}
        for side in (+1, -1):
            o = np.asarray(offfn(_SG, side), float)
            s2, u2 = project(_SX - np.sin(_SH) * (o * side),
                             _SY + np.cos(_SH) * (o * side))
            far = np.abs(((s2 - _SG + LAP * 0.5) % LAP)
                         - LAP * 0.5) > OWNED_SELF_WINDOW_M
            depth = (half_width(s2) + 0.50) - np.abs(u2)
            bad = far & (depth > 0.0)
            n = int(bad.sum())
            i = int(np.argmax(np.where(bad, depth, -1e9))) if n else 0
            r[side] = (n, float(depth[i]) if n else 0.0,
                       float(_SG[i]), float(s2[i]), float(u2[i]))
        return r

    _now = _cross_sweep(barrier_offset)
    _was = _cross_sweep(barrier_offset_declared)
    for side in (+1, -1):
        n, w, s_at, s_on, u_on = _now[side]
        chk("barrier face is outside every OTHER leg's road, side %+d" % side,
            n == 0,
            "%d of %d stations%s" % (n, _FN, "" if n == 0 else
                                     "  worst %.3f m in at s = %.1f, landing on "
                                     "the leg at s = %.1f, u = %+.3f"
                                     % (w, s_at, s_on, u_on)))
    # THE POSITIVE CONTROL: the same sweep, on the line this revision replaced.
    n, w, s_at, s_on, u_on = _was[+1]
    chk("... and the SAME sweep FAILS the line v1.1.1 shipped",
        n > 0 and w > 7.0,
        "%d of %d stations (%.2f %%), worst %.3f m in at s = %.1f landing at "
        "u = %+.3f on the leg at s = %.1f — v1.0.1 measured 3.56 %% with THE "
        "SAME worst case, so the rate cap moved the count, not the intrusion"
        % (n, _FN, 100.0 * n / _FN, w, s_at, u_on, s_on))
    # THE NEGATIVE CONTROL: a line that provably cannot leave its own corridor.
    _neg = _cross_sweep(lambda s, sd: verge_edge(s) + 1.0)
    chk("... and PASSES a line that cannot leave its own corridor",
        _neg[+1][0] == 0 and _neg[-1][0] == 0,
        "verge_edge + 1.00 m: 0 of %d on both sides" % _FN)

    # THE SELF/FOREIGN SEPARATION — the whole justification for the 2.0 m
    # tolerance, measured rather than argued.  If these two populations ever
    # overlap, the tolerance is doing real work and has to be re-derived.
    _sd = np.concatenate([_OWNED_DIAG[s]["ds"].ravel() for s in (+1, -1)])
    _fg = np.concatenate([_OWNED_DIAG[s]["foreign"].ravel() for s in (+1, -1)])
    _du = np.concatenate([_OWNED_DIAG[s]["du"].ravel() for s in (+1, -1)])
    chk("the ownership solve's SELF and FOREIGN populations do not overlap",
        (not _fg.all()) and _fg.any()
        and float(_sd[~_fg].max()) < OWNED_SELF_WINDOW_M
        < float(_sd[_fg].min()),
        "self max |ds| %.4f m (n=%d), foreign min |ds| %.3f m (n=%d); the %.1f m "
        "tolerance sits %.1f m above one and %.1f m below the other, and any "
        "value in that gap gives a bit-identical answer"
        % (_sd[~_fg].max(), int((~_fg).sum()), _sd[_fg].min(), int(_fg.sum()),
           OWNED_SELF_WINDOW_M, OWNED_SELF_WINDOW_M - _sd[~_fg].max(),
           _sd[_fg].min() - OWNED_SELF_WINDOW_M))
    chk("... and the lateral tolerance separates them too",
        float(_du[~_fg].max()) < OWNED_SELF_U_TOL_M,
        "self max |du| %.2e m against a %.2f m tolerance"
        % (_du[~_fg].max(), OWNED_SELF_U_TOL_M))
    # CONTROL 1, the tight hairpin: a window too NARROW reads a hairpin's own
    # neighbours as a foreign leg.  T4 is R = 28 m, the tightest on the circuit.
    _g = _OWNED_DIAG[+1]["grid"]
    _t4 = (_g >= _EL_BY_TAG["T4"]["s0"]) & (_g <= _EL_BY_TAG["T4"]["s0"]
                                            + _EL_BY_TAG["T4"]["L"])
    _t4self = _OWNED_DIAG[+1]["ds"][_t4][~_OWNED_DIAG[+1]["foreign"][_t4]]
    chk("CONTROL: the tightest hairpin on the circuit is not read as a foreign leg",
        _t4.any() and _t4self.size > 0 and float(_t4self.max())
        < OWNED_SELF_WINDOW_M,
        "T4, R = %.1f m, %d solve stations: max self |ds| %.4f m"
        % (_EL_BY_TAG["T4"]["R"], int(_t4.sum()), _t4self.max()))
    # CONTROL 2, the longest straight: a window too WIDE swallows real crossings
    # and the solve silently disables itself.  It must find NOTHING on the pit
    # straight (there is nothing) while finding plenty elsewhere (there is).
    _ps = (_g >= _S_PIT_OPEN) | (_g <= _S_PIT_CLOSE)
    chk("CONTROL: the solve is not silently disabled on the longest straight",
        int(_OWNED_DIAG[+1]["foreign"][_ps].sum()) == 0 and int(_fg.sum()) > 1000,
        "pit straight: %d solve stations, 0 foreign samples; the same solve finds "
        "%d foreign samples elsewhere on the lap"
        % (int(_ps.sum()), int(_fg.sum())))

    _or = ownership_report()
    for side, key in ((+1, "L"), (-1, "R")):
        d = COR.off_declared[side] - COR.off[side]
        chk("the ownership cap only ever moves the line INBOARD, side %+d" % side,
            float(d.min()) >= -1e-12,
            "identical on %.2f %% of the lap; max pull-in %.3f m, rms %.4f m, "
            "capped over %.2f %%" % (100.0 * _or[key]["identical_frac"],
                                     _or[key]["max_pull_in_m"],
                                     _or[key]["rms_pull_in_m"],
                                     100.0 * _or[key]["frac_of_lap"]))
    _Sf = np.arange(0.0, LAP, 0.25)
    for side in (+1, -1):
        clr = barrier_offset(_Sf, side) - verge_edge(_Sf)
        chk("the capped line still clears verge_edge by >= %.3f m, side %+d"
            % (BARRIER_MIN_CLEAR_M, side),
            float(clr.min()) >= BARRIER_MIN_CLEAR_M - 1e-9,
            "min %.4f m at s = %.2f" % (clr.min(), _Sf[clr.argmin()]))
        chk("owned_edge never exceeds the declared platform edge, side %+d" % side,
            float((owned_edge(_Sf, side)
                   - _platform_edge_declared(_Sf, side)).max()) <= 1e-9,
            "owned_edge is tighter than the declared platform on %.2f %% of the "
            "lap" % (100.0 * _or["L" if side > 0 else "R"]
                     ["owned_lt_platform_frac"]))
    # THE BREAK TEST.  `build_barriers` cuts the barrier where the declared line
    # JUMPS, with a STRICT `>`.  Against 2.00 that could never fire on a
    # 1.95-Lipschitz line (dead); against a flat 1.95 it fires on float
    # round-off.  Both failure modes are checked here, on the real line.
    _brk = []
    for side in (+1, -1):
        _bo = COR.off[side]
        _dr = np.abs(np.diff(np.concatenate([_bo, _bo[:1]]))) / PS
        _brk.append((side, float(_dr.max()), int((_dr > BARRIER_BREAK_RATE).sum())))
    chk("the break test does NOT fire on the contract's own line",
        all(n == 0 for _s, _m, n in _brk),
        "max |d off/ds| %s against a strict > %.6f; a flat %.2f would fire at "
        "%d + %d stations on float round-off alone"
        % (", ".join("%.17g (side %+d)" % (m, s) for s, m, _n in _brk),
           BARRIER_BREAK_RATE, BARRIER_MAX_LATERAL_RATE,
           int((np.abs(np.diff(np.concatenate([COR.off[+1], COR.off[+1][:1]])))
                / PS > BARRIER_MAX_LATERAL_RATE).sum()),
           int((np.abs(np.diff(np.concatenate([COR.off[-1], COR.off[-1][:1]])))
                / PS > BARRIER_MAX_LATERAL_RATE).sum())))
    _fake = COR.off[-1].copy()
    _fake[1000] += 3.0                     # a 3.0 m/m step: a jump, not a line
    _fdr = np.abs(np.diff(np.concatenate([_fake, _fake[:1]]))) / PS
    chk("... and it DOES fire on a line with a real jump in it",
        int((_fdr > BARRIER_BREAK_RATE).sum()) == 2,
        "a 3.0 m step in one metre of station is caught at %d stations; the "
        "epsilon is %.0e m/m, six orders under the 46.31 m step v1.0.1 shipped"
        % (int((_fdr > BARRIER_BREAK_RATE).sum()), RATE_EPS))

    # AND THE RIM.  This is where the defect reaches an object that gets built:
    # `rim_buildable` said BUILDABLE at 30 stations whose rim sits inside the
    # car's swept path by up to 1.481 m, all of them on the far leg at T3.
    _rs2 = np.arange(0.0, LAP, 1.0)
    _own_block = ~np.asarray(
        platform_edge(_rs2, +1) <= owned_edge(_rs2, +1) + 1e-9, bool)
    chk("rim_buildable refuses the rim where another leg owns the ground",
        _own_block.any() and not np.asarray(
            rim_buildable(_rs2[_own_block], +1), bool).any(),
        "%d of %d stations refused for ownership, s %.0f..%.0f"
        % (int(_own_block.sum()), len(_rs2),
           _rs2[_own_block].min(), _rs2[_own_block].max()))

    # ------------------------------------------------------------------ [18]
    out.write("\n[18] THE DRIVEN TRANSIT LINE IS THE DECLARED ARC  (R2-042, INVERTED)\n")
    #
    # THIS ASSERTION USED TO POINT THE OTHER WAY, AND IT WAS RIGHT TO.  Until
    # 2026-08-02 it asserted that S10c's CHORD polyline reproduced telemetry.csv
    # to 1.0e-4 m, which it did: `tools/build_telemetry.py` built the transit by
    # interpolating the four leg endpoints.  docs/R2-042-DECISION.md settled which
    # of the two curves is the road — the declared R150 / 40 deg arc — and
    # build_telemetry now evaluates the merge analytically off the ACCESS_*
    # constants below.  So the check inverts: the artefact must now reproduce the
    # ROUTE, and the chord it used to sit on must be 9.04 m away.  The chord is
    # still published (S10c) and `transit_keepout` is still the union of both,
    # which is conservative and costs nothing.
    #
    # The contract does not READ the CSV at import (RULE 2), and says so out loud
    # rather than silently passing when it is missing.
    _csv = os.path.join(_ROOT, "telemetry", "telemetry.csv")
    if os.path.exists(_csv):
        import csv as _csvmod
        with open(_csv) as _f:
            _tel = list(_csvmod.DictReader(_f))
        _tsm = np.array([float(r["s_m"]) for r in _tel])
        _tx = np.array([float(r["x"]) for r in _tel])
        _ty = np.array([float(r["y"]) for r in _tel])
        _m = _tsm <= TRANSIT_DRIVE_LEN_M
        # Route station BY LEG FRACTION, not by `s - 11.98`: the spec rounds the
        # merge to 104.700 m where R150 x 40 deg is 104.7198, and a global-station
        # mapping would inherit that 19.8 mm and call it a defect.
        _lg = SPEC["transit"]["legs"]
        _lL = np.array([float(l["length_m"]) for l in _lg])
        _lc = np.concatenate([[0.0], np.cumsum(_lL)])
        _s = _tsm[_m]
        _rt = (np.clip((_s - _lc[1]) / _lL[1], 0.0, 1.0) * ACCESS_L2
               + np.clip((_s - _lc[2]) / _lL[2], 0.0, 1.0) * ACCESS_L3)
        _mg = (_s >= _lc[1]) & (_s < _lc[3])          # the apron and the merge
        _rx, _ry, _ = access_route_arrays(_rt[_mg])
        _err = np.hypot(_rx - _tx[_m][_mg], _ry - _ty[_m][_mg])
        _cx, _cy = transit_drive_arrays(_s[_mg])
        _chord = np.hypot(_cx - _tx[_m][_mg], _cy - _ty[_m][_mg])
        chk("telemetry.csv drives the DECLARED ARC, and no longer its chord",
            int(_mg.sum()) > 80 and float(_err.max()) < 1.5e-4
            and float(_chord.max()) > 5.0,
            "max %.2e m from `access_route_arrays` over %d apron+merge frames "
            "(the CSV writes x,y to 4 dp, so 5e-5 m of that is the artefact's own "
            "quantum), while `transit_drive_arrays` — the chord this check used to "
            "assert — now reads %.4f m away.  Same 9.04 m, other side of the fix"
            % (_err.max(), int(_mg.sum()), _chord.max()))
        # ... and the harm that divergence did, measured on the artefact.
        _t, _v = access_project(_tx[_m], _ty[_m])
        _on = (_t >= 0.0) & (_t <= ACCESS_MERGE)
        _vi, _vo = access_edges(np.clip(_t[_on], 0.0, ACCESS_TOTAL))
        chk("... so the swept car box is back inside the ribbon's own edge",
            float((_v[_on] + CAR_SWEPT_HALF_W_M - _vo).max()) < 0.0
            and float(np.abs(_v[_on]).max()) < 1.5e-4,
            "worst %+.3f m outboard over the merge, against +4.643 m before, and "
            "the centreline offset is %.2e m against 9.0406 m.  An R150 arc stands "
            "%.2f m off its own chord and the car was on the chord"
            % ((_v[_on] + CAR_SWEPT_HALF_W_M - _vo).max(),
               np.abs(_v[_on]).max(),
               ACCESS_R * (1.0 - math.cos(math.radians(ACCESS_ARC_DEG * 0.5)))))
    else:
        chk("telemetry.csv is present so the driven line can be verified", False,
            "NOT FOUND at %s — this check is UNPROVEN, which is a FAIL.  The "
            "polyline is still derived from SPEC['transit']['legs'], the same "
            "block build_telemetry.py integrates." % _csv)
    chk("the driven line is the spec's transit legs, end to end",
        abs(TRANSIT_DRIVE_LEN_M
            - float(SPEC["transit"]["total_length_dais_to_line_m"])) < 0.01
        and abs(transit_drive_point(0.0)[0]) < 1e-9
        and abs(transit_drive_point(TRANSIT_DRIVE_LEN_M)[0]
                - float(SPEC["datum"]["start_finish_world"][0])) < 0.01,
        "%.2f m, dais (%.1f, %.1f) to the start/finish line (%.2f, %.2f)"
        % ((TRANSIT_DRIVE_LEN_M,) + transit_drive_point(0.0)
           + transit_drive_point(TRANSIT_DRIVE_LEN_M)))
    # THE KEEP-OUT IS A UNION, AND EACH HALF MUST BE ABLE TO BLOCK ALONE.
    _q = np.array([transit_drive_point(d) for d in (30.0, 100.0, 250.0)])
    _in_drive = transit_drive_keepout(_q[:, 0], _q[:, 1])
    _in_rib = in_access_ribbon(_q[:, 0], _q[:, 1], margin=TRANSIT_KEEPOUT_M)
    chk("the driven centreline is inside the keep-out at every station",
        bool(np.all(_in_drive)) and bool(np.all(transit_keepout(_q[:, 0],
                                                                _q[:, 1]))),
        "3 probes on the driven line; the RIBBON term alone catches %d of them"
        % int(np.sum(_in_rib)))
    _far = np.array([[400.0, 400.0], [-200.0, 60.0]])
    chk("... and it does not block the far field",
        not bool(np.any(transit_keepout(_far[:, 0], _far[:, 1]))),
        "two points 200-400 m away are buildable")
    chk("PIT_WALL_S0 is derived from BOTH curves and takes the later crossing",
        abs(PIT_WALL_S0 - 3447.7092) < 0.01,
        "%.4f — the ribbon's crossing; the driven swept box crosses at 3446.007, "
        "so v1.1.1's ribbon-only derivation was right here by 1.70 m of luck"
        % PIT_WALL_S0)

    out.write("\n%s  (%d checks, %d failed)\n"
              % ("PASS" if not fails else "FAIL", n_chk[0], len(fails)))
    rep = out.getvalue()
    if verbose:
        print(rep)
    return (not fails), rep


def _gate_selftest(other_path):
    """THE GATE, RUN AGAINST A CONTRACT ALREADY KNOWN TO BE BAD.

    `python3 world_contract.py --gate-selftest <path/to/old/world_contract.py>`

    A continuity gate that passes v1.0.1 is not a gate.  This loads another
    revision of this module under a private name and runs `continuity_report`
    against it through the public API alone.  It EXPECTS FAILURE and exits
    non-zero if the old contract passes.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_wc_under_test", other_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    print("gate self-test: %s  (version %s)" % (other_path, old.__version__))
    ok, rows, notes = continuity_report(old, verbose=True)
    bad = [r for r in rows if not r[5]]
    print("\n%d of %d rows FAIL on that contract." % (len(bad), len(rows)))
    if ok:
        print("THE GATE IS WRONG: it passed a contract already known to be bad.")
        return False
    print("The gate fails it.  That is the result this run is looking for.")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--gate-selftest":
        sys.exit(0 if _gate_selftest(sys.argv[2]) else 1)
    ok, _ = selftest()
    sys.exit(0 if ok else 1)
