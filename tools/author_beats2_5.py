"""THE MISSING TWO-THIRDS OF THE CAMERA — beats 2, 3, 4 and 5, authored.

    .venv/bin/python tools/author_beats2_5.py [--dry-run]

Writes `beat2`/`beat3`/`beat4`/`beat5` blocks (and an `aim` block for every
beat, including 1 and 6) into `docs/beat_sheet.json`. Touches nothing else in
that file: beat 1's 16 keys and beat 6's 8 keys are read, never rewritten.

THE DEFECT THIS FIXES
---------------------
`beat_sheet.json` carried camera keys for beat 1 and beat 6 only — 24 keys for
2,978 frames. Over the 1,960-frame gap the built rig drifted a 123 m straight
line at 1.5 m/s with **no rotation key at all after frame 754**, while the car
was a median 612 m away and beyond 500 m for 69 % of it. The continuity gate
passed it, correctly, because a slow straight drift has no jumps. Nothing
measured whether the camera was pointed at the film. `build_camera_rig.py` now
carries an AIM GATE that does; this file supplies the camera it measures.

HOW THE CAMERA IS DESCRIBED
---------------------------
Not as 480 hand-typed keys. As ~50 CHOREOGRAPHY ANCHORS — a position, a lens,
and a statement of what the shot is looking at — which are then:

  * splined in film time as ONE cubic Hermite across all four beats — one, not
    four, because a per-beat spline puts the right position at a beat boundary
    and the wrong VELOCITY there (measured at the beat-4/5 junction: 74 m/s
    arriving, 103 m/s leaving, a 29 m/s step inside one frame) — with Bessel
    tangents and Fritsch-Carlson limiting, so "decelerate into a hover and stop"
    produces a deceleration rather than an overshoot past the station;
  * sampled onto keys at an ADAPTIVE spacing, dense where the subject's bearing
    changes fast (the doppler pass swings 192 deg/s) and sparse where it does
    not, so the rig stays an editable animation rather than a per-frame bake;
  * aimed, per key, at the car's real telemetry position at that key's WORLD
    time — which is not its film time, because beat 3's ramp permanently
    offsets the two clocks (see `anim/filmtime.py`).

Anchors that belong to the track are written in track coordinates
(station, lateral, height) and resolved through the telemetry, so a camera
"11 m inside the hairpin, 1.0 m up" stays there whatever the elevation does.

WHAT EACH BEAT IS, AND WHY
--------------------------
2_launch  The camera leaves beat 1's push, descends around the car's right rear
          quarter and STOPS. A launch reads faster from a static low camera than
          from one already moving: the 10 sanctioned wheelspin frames happen with
          the lens 5.5 m from the rear tyre and the camera barely drifting. Only
          once the car is past does the camera swing up and give chase, and it is
          deliberately slower than the car so the car pulls away into the glass.

3_breach  The money moment, and the one beat where the camera has to earn its
          slow motion. World time collapses to 15.4 % over 6 frames as the nose
          meets the glass. The camera does the opposite of the world: it
          accelerates, from 3.1 m/s at the impact to 10.1 m/s at the hand-off,
          and covers 55 m while the car covers 37.6. It threads the 9.6 x 5.6 m
          aperture 2 m to the car's right with shards hanging at 21 mm, crosses
          the wake, climbs, and arrives ahead-left and 5 m up looking BACK at the
          car coming through a curtain of glass with the wound behind it. That
          composition is the reason to slow time down; a chase from behind would
          not have been.

4_transit The car powers away from a camera that is briefly ahead of it, passes
          underneath, and the camera falls in behind, rising to 17 m to carry the
          paddock and the merge arc in one frame, then diving back to 5.6 m to
          cross the start/finish line UNDER the gantry 45 m behind the car. The exposure ramp does NOT live here: it is keyed to the frame
          the camera actually crosses the glass plane, which is 6.4 s of screen
          time earlier, in beat 3.

5_lap     A camera cannot follow a car that reaches 91.9 m/s; at 12 m per frame
          the geometry of a chase is brutal. So it does not try. The lap is a
          sequence of EARNED vantages, chosen where the car does something —
          T1 turn-in, the 295 km/h T3 kink, the 295->80 km/h braking event into
          the hairpin and the hairpin itself from the outside at 2.4 m (the
          inside is where the misplaced L03 catch fence lives), a helicopter arc
          rising over the esses, the T10/T11 sweeper from the outside, the
          declared doppler station where the camera hovers and lets 313 km/h go
          past 26 m away, then a long-lens follow into T12's braking zone before
          the camera catches the car again through T13-T15 and closes into the
          top-down follow that beat 6 peels out of. Three times the camera leaves
          the car and flies ahead to be somewhere first; the lens goes long while
          it repositions and wide again as the car arrives, which is how you keep
          a subject large while the camera is doing something else.

WHAT IS VERIFIED HERE, AND WHAT IS NOT
--------------------------------------
This file reports camera speed, acceleration, camera-to-car distance and the
lateral offset from the centreline for every emitted key, and refuses to write
if the camera and the car occupy the same space at the same frame or if the move
leaves an envelope derived from the CAR's own numbers (1.5x its peak speed,
2x its peak lateral g). It does NOT prove the camera misses the world's geometry — only `tools/placement_gate.py`
run against the assembled world can do that, and it is run against the per-frame
path the rig build emits.
"""

import argparse
import bisect
import csv
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
import filmtime as FT                                              # noqa: E402

from carpath import (Car, centreline_table, cl_at, lateral_of,     # noqa: E402
                     CAR_HALF_LEN, CAR_HALF_W, CAR_TOP_Z)

# The circuit's own geometry contract — the ONE definition of where the
# centreline runs and which way its lateral axis points. Beat 5's bridge thread
# below is written in the bridge's own frame, and that frame has to be the same
# one `world/build_architecture.py` built the bridge in.
sys.path.insert(0, os.path.join(R2, "world"))
import world_contract as WC                                        # noqa: E402

FPS = FT.FPS

# The film is shot on a 36 mm sensor width; the rig and the beat-1 generator
# both assume it, so framing offsets resolve against the same number they do.
SENSOR_W_MM = 36.0

# The camera may never be inside the car, measured to the surface of the car's
# oriented box (5.698 x 2.005 x 0.992 sitting on the road), not to its reference
# point. The floor is 1.40 m because the film's tightest camera-to-car figure is
# not mine to choose: beat 6's DECLARED peel-off sits at 2.80 m over a road the
# car's roof reaches 0.99 m above, i.e. 1.81 m of clearance, and that key is
# fixed. Anything the lap does has to live above that number, not below it.
CAM_CAR_MIN_M = 1.40

# ------------------------------------------------ BEAT 5: THE BRIDGE THREAD --
# R2-971 / R2-1004.  Le Pont de la Plongee crosses the lap at s = 2410 and the
# camera used to fly OVER it.  Measured on the built path: at f2174 it crosses
# the bridge plane at u = -29.27 m and 11.89 m above the road — 5.1 m ABOVE the
# soffit and 29 m OUTBOARD of the centreline, neither under the bridge nor over
# the track, while `docs/circuit_spec.md` §10 says this pass "threads under it
# at ~5 m altitude".  The consequence was measured, not inferred: the car is
# WHOLLY HIDDEN for f2180-2191.  Twelve frames of a one-shot film with no
# subject in them.
#
# The cure is a WINDOWED DISPLACEMENT of the camera in the bridge's own frame,
# and deliberately not a re-authored anchor: an anchor pulls the spline for
# hundreds of frames either side of itself and cannot be held interior to a
# 94-frame window, which is the property everything below depends on.  Two
# independent smootherstep windows, one per axis, so the camera comes back
# outboard BEFORE it is at its lowest instead of flying low over the racing
# surface.  Smootherstep has zero first and second derivative at both ends, so
# the correction is C2 in frame and can introduce neither a step nor a kink.
#
#     lateral   +20.0 m inboard    f2133 -> 2165  ...  2178 -> 2210
#     vertical   -7.5 m            f2133 -> 2166  ...  2190 -> 2222
#
# WHY THE DISPLACEMENT IS THAT SIZE.  It sits in the middle of a measured
# plateau of exactly zero blocked frames spanning du 18..24 m x dz -6..-11 m
# (`tools/r2731_pont_full_sightline.py`, whose --selftest reproduces two
# independent depth-tested raycasts at two different stations).  It is not a
# minimum-effort value on the plateau's edge: a plateau 6 m x 5 m wide is what
# makes the fix survive a tenth of a metre of key-emission error.
#
# WHY THE RAMPS ARE THESE WIDTHS — this is the part that was got wrong once and
# then measured.  R2-738 authored the SAME displacement over a 22-frame lateral
# OUT ramp (f2178->2200) and it cost 91.2 m/s^2 = 9.29 g: 95 % of this file's
# own craft limit below, and 1.86x the shipped path's own peak.  The whole spike
# was in that one ramp, at f2193.  Widening it to 32 frames and starting both
# in-ramps 12 frames earlier (f2145 -> f2133) leaves the displacement, and
# therefore the occlusion result, untouched — that is what the width of the
# plateau buys — and brings the peak to 47.7 m/s^2 = 4.86 g, BELOW the shipped
# path's own 49.1.  The fix costs nothing in the camera envelope instead of
# nearly exhausting it.  Wider still was measured at 43.9 m/s^2 and NOT taken:
# it starts eating the hold at the bottom of the pass, which is the shot.
#
# WHY IT IS AN OFFSET AND NOT A PATH.  The support is f2131-2224, interior to
# beat 5 (f1191-2714) by 940 and 490 frames, so both beat boundaries are
# bit-identical BY CONSTRUCTION, and beats 2, 3, 4 and the seam bridge emit the
# keys they always did because this term is exactly zero — not nearly zero —
# outside its own window.  `render/film_path_R2971_PONT_B5_REBASED.json` is the
# same displacement baked onto a whole-film path; adopting a file like that
# wholesale is how beat 1 gets silently reverted by 9.9 m over 2,472 frames to
# buy twelve frames in beat 5.  That trap has now caught two agents (R2-737,
# R2-1004 "Defect 1").  Carry the offset, never the file.  Being a pure function
# of the frame index is exactly what lets it be carried.
#
# KEY DENSITY WAS CHECKED AND NOTHING WAS CHANGED FOR IT.  The offset is inside
# `sample()`, so the adaptive walk sees it in the BEARING and densifies on its
# own: through the ramps the emitted spacing goes 5-8 frames to 4-8, and beat 5
# gains exactly one key (316 -> 317).  Reconstructing the offset from the keys
# actually emitted is worst 0.259 m against the exact curve — and the BUILT path
# already differs from this file's own spline by 0.128 m over f2120-2240 before
# this term exists, so the residual is inside the instrument that ships.  A
# displacement-per-key criterion was swept over seven settings: the best of them
# buys 0.259 m -> 0.046 m for 21 extra keys through the window, and the milder
# ones buy almost nothing (0.16-0.23 m).  On a zero-blocked plateau 6 m x 5 m
# wide that is not worth a new mechanism, and it is the same verdict for the
# same reason as R2-087's rejection of a global speed criterion further down.
#
# AND IT MAKES THE ENVELOPE BETTER, not worse.  Measured on this file's own
# per-frame spline over all of beats 2-5: the worst camera acceleration anywhere
# was 61.94 m/s^2 at f2194 — inside this window, and put there by the bridge
# pass itself — and with the thread in it is 53.75 m/s^2 at f2560.  The frame
# that used to be the film's worst is no longer in the top of the census.
#
# PONT_S is `world/build_architecture.py:5739`, which is module-level there
# precisely so a station has one reader per module instead of a copy per module.
# It cannot be imported (that file imports bpy at module level), so it is
# spelled out here as `tools/r2731_pont_camera_apply.py` and
# `tools/r2731_pont_camera_candidate.py` already spell it out.  If the bridge
# ever moves, those four move together.
PONT_S = 2410.0
PONT_DU, PONT_U_WIN = 20.0, (2133.0, 2165.0, 2178.0, 2210.0)
PONT_DZ, PONT_Z_WIN = -7.5, (2133.0, 2166.0, 2190.0, 2222.0)
PONT_F0, PONT_F1 = 2131, 2224                  # the support, both ends included
_PONT_LAT = None


def _smoother(t):
    """Smootherstep: zero FIRST and SECOND derivative at both ends."""
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def _win(f, w):
    """1.0 on the plateau, 0.0 outside, smootherstep on the two ramps."""
    f0, f1, f2, f3 = w
    if f <= f0 or f >= f3:
        return 0.0
    if f < f1:
        return _smoother((f - f0) / (f1 - f0))
    if f <= f2:
        return 1.0
    return _smoother((f3 - f) / (f3 - f2))


def pont_offset(f):
    """Beat 5's bridge thread — world metres, at film frame `f`.

    EXACTLY zero outside f2131-2224, so every other beat is untouched bit for
    bit and both beat-5 boundaries are identical without anyone having to
    assert it afterwards.
    """
    global _PONT_LAT
    if not (PONT_F0 <= f <= PONT_F1):
        return (0.0, 0.0, 0.0)
    if _PONT_LAT is None:
        _x, _y, _z, hdg, _k = WC.centreline(PONT_S)
        _PONT_LAT = (-math.sin(hdg), math.cos(hdg), 0.0)
    wu = PONT_DU * _win(f, PONT_U_WIN)
    return (wu * _PONT_LAT[0], wu * _PONT_LAT[1], PONT_DZ * _win(f, PONT_Z_WIN))


# ---------------------------------------------------------------- THE SEAM --
# R2-064. Beat 1's last key and beat 2's first key are the two ends of a
# 39-frame hole. Nothing was declared inside it, so the path there was whatever
# Blender's AUTO_CLAMPED handles inferred from a 39-frame neighbour on the left
# and a 2-frame neighbour on the right, and what they inferred was 11.34 m/s
# where the keys ask for 9.38, arriving through 98.5 m/s^2 in one frame.
#
# Both keys are now ANCHORS of this file's spline, so the acceleration across
# the seam is authored here rather than emerging from an interpolator. Neither
# VALUE is chosen here — they are transcribed:
#
#   B1_LAST   docs/beat_sheet.json beat1.camera_keys, t = 31.4, and its own
#             note fixes it: "beat 2's first key is 2.09 m away 39 frames later
#             at 39.95 mm, so this key is fixed and beats 1 and 2 join at
#             1.29 m/s with no step in position, aim or focal length"
#   B2_FIRST  the key this file itself emitted at frame 793 before R2-064, kept
#             to the digit so the four seam invariants (chord 2.0893 m, speed
#             1.2727 m/s, look angle 13.2504 deg, lens delta -0.051 mm) are
#             preserved BY CONSTRUCTION rather than by luck. `check_seam()`
#             below refuses to write the sheet if the emitted key ever stops
#             reproducing it exactly.
#
# The aim specs are transcribed the same way. At frame 793 the car is still on
# the dais (world time -1.03 s, `Car.state` parks it at the origin), so
# `aim_car(along_m=A, z_off=Z)` resolves to exactly `[A, 0, Z]` and the two
# look_at values below are the declared ones read straight off.
SEAM_F = 793
SEAM_T = SEAM_F / FPS                                   # 33.0416666..., not 33.0
SEAM_POS = [5.0337, -5.3157, 1.2622]
SEAM_LENS = 39.949
SEAM_FSTOP = 3.196
SEAM_ALONG = -0.0143                                    # look_at x
SEAM_ZOFF = 0.5985                                      # look_at z

# BEAT 1'S LAST KEY DOES NOT LAND ON A FRAME EITHER. It is declared at t = 31.4
# and 31.4 x 24 = 753.6, and `build_camera_rig.py` puts its declared position on
# frame 754 — the same rounding R2-063 found at the beat-5/6 hand-off, four
# tenths of a frame again. The spline is therefore anchored at 754/24 and NOT at
# 31.4: the camera is at [6.8, -4.4, 1.9] on frame 754 in the built rig, so a
# spline that thinks it is there 0.4 of a frame earlier hands the first bridge
# frame 0.0209 m of position error. MEASURED with the anchor at 31.4: frame 755
# built at 1.7064 m/s against an authored 1.20, a one-frame blip with -13.7
# m/s^2 behind it, 17.9x its own neighbourhood.
#
# THE FOUR SEAM INVARIANTS ARE UNAFFECTED. They are properties of the two KEYS,
# and `beat1.camera_keys` still declares t = 31.4; this is the anchor time the
# authoring spline uses, and it is chosen to match the artefact rather than the
# declaration. `tools/seam_gate.py` measures both, which is how the difference
# stays visible.
B1_LAST_F = 754
B1_LAST_T = B1_LAST_F / FPS
B1_LAST_POS = [6.80, -4.40, 1.90]
B1_LAST_LENS = 40.0
B1_LAST_FSTOP = 3.2
B1_LAST_ALONG = 0.15                                    # beat 1's look_at x
B1_LAST_ZOFF = 0.75                                     # beat 1's look_at z

# The bridge occupies the frames between the two, exclusive of both: beat 1's
# key list and beat 2's key list are not touched, so `work/campath/beat1_probe.py`
# measures the same pair of keys before and after and reports the same four
# numbers. The bridge is written to its own `beat1_2_seam` block and
# `anim/build_camera_rig.py` loads it by name.
#
# THE NAME IS NOT COSMETIC. `sim/apply_breach.py` and `sim/witness.py` both walk
# `sheet.keys()` and take every block whose name `startswith("beat")` — the
# convention that already exists here, and a comment in each of them records
# that missing a block through this filter has bitten before. A block called
# `seam_1_2` is invisible to both: apply_breach's camera polyline would run the
# 2.09 m seam as a straight chord and witness's key interpolation would span a
# 39-frame hole. Naming it `beat1_2_seam` makes both of them see it with no
# change to either file, which is worth more than a tidier name.
SEAM_BRIDGE_F0 = int(round(B1_LAST_T * FPS)) + 1        # 755
SEAM_BRIDGE_F1 = SEAM_F - 1                             # 792


# ------------------------------------------------------------------ anchors --
def track_point(car, world_of_frame, film_t, ds, u, h_above):
    """World point `ds` metres along the track from the car, `u` left, `h` up.

    Resolved through the CAR's own line rather than the centreline: `u` is then
    an offset from where the car actually is, which is what a camera operator
    means by "9 m to its left", and it stays meaningful through an apex where
    the racing line is hard against the kerb.
    """
    f = max(1, min(len(world_of_frame) - 1, int(round(film_t * FPS))))
    wt = world_of_frame[f]
    ts = car.track_s(wt) + ds
    twt = car.t_at_track_s(ts) if ts >= 0 else wt
    p, hd, _v = car.state(twt)
    left = (-math.sin(hd), math.cos(hd), 0.0)
    return [p[0] + left[0] * u, p[1] + left[1] * u, p[2] + h_above]


def cl_point(cl, track_s, u, h):
    """A world point at an ABSOLUTE track station, `u` left of the centreline.

    Used where the vantage is a place rather than a relationship to the car —
    above all the declared doppler station, whose approach has to be laid out in
    stations so the deceleration into the hover can be given the ~170 m it needs
    at 2.5 g instead of the 18 g the first draft measured.
    """
    p, hd = cl_at(cl, track_s)
    left = (-math.sin(hd), math.cos(hd), 0.0)
    return [p[0] + left[0] * u, p[1] + left[1] * u, p[2] + h]


def A(t, pos, lens, fstop=4.0, aim=None, note=""):
    return {"t": float(t), "pos": pos, "lens": float(lens), "fstop": float(fstop),
            "aim": aim or {}, "note": note}


def aim_car(lead_s=0.0, along_m=0.0, z_off=0.55, lat_m=0.0,
            frame_u=0, frame_v=0):
    """Where the lens points, relative to the car, in the CAR's own frame.

    `along_m` positive is toward the nose; `lead_s` multiplies the car's current
    speed, which is how an operator leads a fast subject without leading a slow
    one by the same distance. Both show up honestly in the aim gate as a nonzero
    angle to the car's reference point, so they are kept small.

    R2-2161 -- `frame_u` / `frame_v` ARE A DIFFERENT UNIT AND THAT IS THE POINT.
    ------------------------------------------------------------------------
    They say WHERE IN THE PICTURE the car sits, in FRAME WIDTHS from centre:
    +u is right, +v is up, 0.5 is the frame edge.  `lat_m` cannot express that,
    because beat 5's subject range runs from 1.6 m at the hairpin to 195 m at
    T10 -- a `lat_m` that reads as a tasteful third of a frame at 100 m swings
    the car clean out of the picture at 2 m.  A framing offset is an angle, and
    an angle is metres over distance, so the distance has to be in the unit.

    Resolved at emission against the ACTUAL camera position and the ACTUAL lens
    at that instant, so the composition an anchor asks for is the composition
    the frame gets, at any range and any focal length.

    They are the ONLY aim parameters that move the subject in frame without
    moving the camera, which is why this pass uses them: the whole positional
    envelope -- speed, acceleration, clearance, collision -- is untouched, and
    every gate that measures the camera's PATH sees an identical path.
    """
    return {"mode": "car", "lead_s": lead_s, "along_m": along_m,
            "z_off": z_off, "lat_m": lat_m,
            "frame_u": frame_u, "frame_v": frame_v}


# The largest angle a framing offset is allowed to add to the aim gate's
# reading.  The gate's per-beat bounds are 14 deg (beat 4) to 26 deg (beat 6)
# and the framing offset lands on top of whatever aim error is already there,
# so it is capped rather than trusted.  12 deg leaves beat 5 -- worst 1.30 deg
# against a 22 deg bound -- more than eight degrees of headroom it never uses.
FRAME_OFF_MAX_DEG = 12.0

# How close to the frame edge the SUBJECT'S EDGE may come, in half-frames.  The
# rig's own framing gate fails at 0.92 (`sheet.aim.frame_margin`) measured to
# the subject POINT for beats 2-6; 0.85 measured to the subject's EDGE is
# strictly tighter than that, so this cannot be the thing that trips it.
FRAME_SAFE_EDGE = 0.85

# The car's bounding-sphere radius: half the diagonal of the 5.698 x 2.005 x
# 0.992 box the collision floor already uses.  It is what turns "put the car at
# 0.5" into a statement about the PICTURE rather than about a point.
SUBJ_RADIUS_M = 3.06

RENDER_ASPECT = 2160.0 / 3840.0


def _frame_offset_world(cam_pos, target, lens_mm, frame_u, frame_v):
    """Shift `target` so the subject lands at (frame_u, frame_v) HALF-FRAMES.

    THE UNIT IS THE GATE'S UNIT, deliberately.  `anim/build_camera_rig.py`
    scores framing as `u = (x/-z) / (0.5*sensor_w/lens)`, i.e. half-frames, and
    fails the beat at 0.92.  An author who writes 0.45 here is writing the same
    number the gate will read back, so there is no conversion in which a
    misunderstanding can hide.  The first draft of this used frame WIDTHS and
    failed the gate at 0.929 for exactly that reason: the vertical half-frame is
    0.28 widths, so a "0.16 width" rise was really 0.57 of the way to the top.

    AND THE REQUEST IS CLAMPED BY THE SUBJECT'S OWN ANGULAR SIZE.  A framing
    offset that is tasteful at 195 m puts the car half out of the picture at
    26 m, because the car is 24 % of the frame wide there.  So the offset is
    reduced until the car's EDGE sits inside `FRAME_SAFE_EDGE`.  That is what
    makes this parameter safe to author across beat 5's 1.6 m -> 195 m range
    without a per-anchor distance table that would go stale the moment an
    anchor moved.

    Moving the AIM POINT right pushes the SUBJECT left, so the world shift is
    the negative of the requested screen position.
    """
    if not frame_u and not frame_v:
        return target
    d = [target[i] - cam_pos[i] for i in range(3)]
    D = math.sqrt(sum(c * c for c in d))
    if D < 1e-6:
        return target
    fwd = [c / D for c in d]
    up_w = (0.0, 0.0, 1.0)
    # Looking straight down or straight up leaves "right" undefined; fall back
    # to the world Y axis so the basis stays continuous instead of flipping.
    if abs(fwd[2]) > 0.999:
        up_w = (0.0, 1.0, 0.0)
    right = [fwd[1] * up_w[2] - fwd[2] * up_w[1],
             fwd[2] * up_w[0] - fwd[0] * up_w[2],
             fwd[0] * up_w[1] - fwd[1] * up_w[0]]
    rn = math.sqrt(sum(c * c for c in right)) or 1.0
    right = [c / rn for c in right]
    up = [right[1] * fwd[2] - right[2] * fwd[1],
          right[2] * fwd[0] - right[0] * fwd[2],
          right[0] * fwd[1] - right[1] * fwd[0]]

    lens = max(lens_mm, 1e-6)
    half_w = 0.5 * SENSOR_W_MM / lens                    # tan of half h-fov
    half_h = 0.5 * SENSOR_W_MM * RENDER_ASPECT / lens    # tan of half v-fov

    # the subject's own angular radius, in half-frames, at this range
    r_u = (SUBJ_RADIUS_M / D) / half_w
    r_v = (SUBJ_RADIUS_M / D) / half_h
    lim_u = max(FRAME_SAFE_EDGE - r_u, 0.0)
    lim_v = max(FRAME_SAFE_EDGE - r_v, 0.0)
    fu = max(-lim_u, min(lim_u, frame_u))
    fv = max(-lim_v, min(lim_v, frame_v))

    ox = -fu * half_w * D
    oy = -fv * half_h * D

    # cap the angle this is allowed to contribute to the aim gate
    hyp = math.hypot(ox, oy)
    if hyp > 1e-9:
        ang = math.degrees(math.atan(hyp / D))
        if ang > FRAME_OFF_MAX_DEG:
            sc = math.tan(math.radians(FRAME_OFF_MAX_DEG)) * D / hyp
            ox, oy = ox * sc, oy * sc
    return [target[i] + right[i] * ox + up[i] * oy for i in range(3)]


def lerp_aim(a0, a1, u, car, wt, cam_pos=None, lens_mm=None):
    """Resolve the aim target at fraction u between two anchors' aim specs.

    `cam_pos` / `lens_mm` are what let `frame_u` / `frame_v` mean anything; when
    they are absent the framing offsets are simply not applied, so every caller
    that does not know where the camera is gets exactly the pre-R2-2161 aim.
    """
    def target(a):
        if a.get("mode") == "point" and a.get("blend", 1.0) >= 1.0:
            return list(a["p"])
        p, hd, v = car.state(wt)
        f = (math.cos(hd), math.sin(hd), 0.0)
        left = (-math.sin(hd), math.cos(hd), 0.0)
        d = a.get("lead_s", 0.0) * v + a.get("along_m", 0.0)
        q = [p[0] + f[0] * d + left[0] * a.get("lat_m", 0.0),
             p[1] + f[1] * d + left[1] * a.get("lat_m", 0.0),
             p[2] + a.get("z_off", 0.55)]
        if a.get("mode") == "point":
            b = a.get("blend", 1.0)
            q = [q[i] + (a["p"][i] - q[i]) * b for i in range(3)]
        if cam_pos is not None and lens_mm is not None:
            q = _frame_offset_world(cam_pos, q, lens_mm,
                                    a.get("frame_u", 0.0), a.get("frame_v", 0.0))
        return q
    t0, t1 = target(a0), target(a1)
    e = u * u * (3.0 - 2.0 * u)                       # ease, so aim never kinks
    return [t0[i] + (t1[i] - t0[i]) * e for i in range(3)]


# ------------------------------------------------------------------- spline --
def _tangents(anchors):
    """Per-axis tangents: Bessel secant average, Fritsch-Carlson limited.

    THREE splines were tried through these anchors and the first two were
    measurably wrong, in the way a camera path is wrong — not visibly, but in
    metres per second:

      * uniform Catmull-Rom ignores that the anchors are 0.5 s apart in one
        place and 3.4 s apart in another;
      * CENTRIPETAL Catmull-Rom fixes the cusps but not the speed. The camera
        arrives at the doppler station off a 100 m/s run and then holds a 1.4 m
        drift for 3.2 s. A knot-parameterised tangent at that anchor still
        carries the arrival's momentum, and the measured result was 109.6 m/s
        and 78 g at the very last anchors of the lap.

    So the tangent at each anchor is the time-weighted average of the two
    adjacent secant velocities (Bessel — the right non-uniform generalisation of
    Catmull-Rom) and is then clamped by the Fritsch-Carlson rule: zero on a sign
    change, otherwise no more than three times the smaller adjacent secant. That
    is what makes "decelerate into a hover and stop" produce a deceleration
    rather than an overshoot past the station and back.
    """
    n = len(anchors)
    ts = [a["t"] for a in anchors]
    ps = [a["pos"] for a in anchors]
    sec = [[(ps[i + 1][c] - ps[i][c]) / (ts[i + 1] - ts[i]) for c in range(3)]
           for i in range(n - 1)]
    tan = []
    for i in range(n):
        v = []
        for c in range(3):
            if i == 0:
                m = sec[0][c]
            elif i == n - 1:
                m = sec[-1][c]
            else:
                d0, d1 = sec[i - 1][c], sec[i][c]
                h0 = ts[i] - ts[i - 1]
                h1 = ts[i + 1] - ts[i]
                if d0 * d1 <= 0.0:
                    m = 0.0
                else:
                    m = (h1 * d0 + h0 * d1) / (h0 + h1)
                    lim = 3.0 * min(abs(d0), abs(d1))
                    m = math.copysign(min(abs(m), lim), m)
            v.append(m)
        tan.append(v)
    return ts, ps, tan


# THE CACHE IS KEYED ON id(), AND id() IS REUSED. R2-084.
#
# `_TAN_CACHE[id(anchors)]` is correct for exactly one anchor chain per
# process, which is all `main()` ever builds — and it is WRONG, silently and
# non-deterministically, for any caller that builds more than one. CPython
# frees a chain when the caller rebinds it and hands the SAME address to the
# next one, so the second chain hits the first chain's entry and every
# subsequent `catmull_rom` returns a camera that belongs to another sheet.
#
# MEASURED, on a 24-variant anchor sweep of the T3 pass: **24 distinct chains,
# ONE id, one cache entry, and all 24 reported the identical 56.55 % smear** —
# including chains whose T3 anchor sat 17 m higher. The failure depends on
# allocator behaviour, so the same script gives different answers on different
# runs depending on what else is holding a reference; an earlier run of the
# same sweep produced four distinct ids and an answer that alternated with the
# loop index. A wrong number that changes between runs is worse than a wrong
# number, because it cannot be reproduced and argued with.
#
# THE FIX IS TO HOLD THE CHAIN. An entry keeps a reference to the anchors it
# was computed from, so that object cannot be freed and its address cannot be
# reused while the entry lives; the hit is then verified with `is`, which is
# O(1) and cannot be fooled. Fingerprinting the contents instead would be O(n)
# on every one of the ~40,000 calls a single build makes and would defeat the
# cache it is protecting.
#
# At the cap the cache is CLEARED WHOLESALE rather than evicted one entry at a
# time. That is deliberate and it is the only safe eviction: the aliasing
# hazard needs a SURVIVING stale entry to collide with, so dropping every
# reference at once leaves nothing to alias against, while dropping one entry
# frees exactly one address for the next chain to land on.
_TAN_CACHE = {}
_TAN_CACHE_CAP = 4096


def catmull_rom(anchors, t):
    """Cubic Hermite through the anchor positions in film time."""
    key = id(anchors)
    hit = _TAN_CACHE.get(key)
    if hit is None or hit[0] is not anchors:
        if len(_TAN_CACHE) >= _TAN_CACHE_CAP:
            _TAN_CACHE.clear()
        hit = (anchors,) + tuple(_tangents(anchors))
        _TAN_CACHE[id(anchors)] = hit
    _owner, ts, ps, tan = hit
    i = bisect.bisect_right(ts, t) - 1
    i = min(max(i, 0), len(ts) - 2)
    h = ts[i + 1] - ts[i]
    u = max(0.0, min(1.0, (t - ts[i]) / h))
    u2, u3 = u * u, u * u * u
    h00 = 2 * u3 - 3 * u2 + 1
    h10 = u3 - 2 * u2 + u
    h01 = -2 * u3 + 3 * u2
    h11 = u3 - u2
    return [h00 * ps[i][c] + h10 * h * tan[i][c]
            + h01 * ps[i + 1][c] + h11 * h * tan[i + 1][c] for c in range(3)]


def path_point(anchors, f):
    """The authored camera POSITION at film frame `f`.

    The spline, plus beat 5's bridge thread. ONE definition, called by the key
    emission below and by the per-frame envelope measurement in `main()`, so
    the position that gets MEASURED is the position that gets WRITTEN — the
    alternative is a report about a camera the sheet does not contain.
    """
    p = catmull_rom(anchors, f / FPS)
    d = pont_offset(f)
    return [p[0] + d[0], p[1] + d[1], p[2] + d[2]]


def scalar_at(anchors, t, field):
    ts = [a["t"] for a in anchors]
    i = bisect.bisect_right(ts, t) - 1
    i = min(max(i, 0), len(anchors) - 2)
    u = (t - ts[i]) / max(ts[i + 1] - ts[i], 1e-9)
    u = max(0.0, min(1.0, u))
    e = u * u * (3.0 - 2.0 * u)
    return anchors[i][field] + (anchors[i + 1][field] - anchors[i][field]) * e


def aim_at(anchors, t, car, wt, cam_pos=None, lens_mm=None):
    ts = [a["t"] for a in anchors]
    i = bisect.bisect_right(ts, t) - 1
    i = min(max(i, 0), len(anchors) - 2)
    u = (t - ts[i]) / max(ts[i + 1] - ts[i], 1e-9)
    return lerp_aim(anchors[i]["aim"], anchors[i + 1]["aim"],
                    max(0.0, min(1.0, u)), car, wt,
                    cam_pos=cam_pos, lens_mm=lens_mm)


# ------------------------------------------------------- key emission (adaptive)
MAX_KEY_GAP = 8        # frames — never coarser than a third of a second
MIN_KEY_GAP = 2        # frames
BEARING_PER_KEY_DEG = 5.0   # emit a key before the subject's bearing has moved
                            # this far, so bezier interpolation of the rotation
                            # channels never has room to stray

# R2-064. The spacing above is driven by BEARING alone, and bearing is not the
# only thing a bezier has to reproduce between two keys. Beat 2 decelerates from
# 6.2 m/s to 0.3 m/s over the eight frames into the ignition station while the
# subject's bearing barely moves, so the adaptive walk emitted ONE key across
# the whole braking event and the interpolation ran 2.64x the chord speed of the
# pair it sat between. A key is therefore also emitted before the SPEED has
# changed by more than this much.
#
# ON FOR BEAT 2 AND THE SEAM ONLY, deliberately. It was recommended as follow-up
# work on the argument that switching it on globally would relayout beats 3-5
# and move a path that already passes three gates.
#
# THE FOLLOW-UP WAS DONE. R2-087. It was switched on globally, the sheet was
# re-authored, the rig rebuilt and every gate re-run, and the answer is NO —
# not because of the blast radius, but because there is nothing on the other
# side of it:
#
#   keys                    433 -> 451 (+18). Beat 2 and beat 4 do not move at
#                           all; beat 3 gains 2, beat 5 gains 16.
#   continuity_gate campath IDENTICAL. PASS, 0 FAIL, the same five advisories,
#                           and the same per-beat speed and rotation maxima to
#                           better than 0.1 %.
#   seam_gate --selftest    7/7 both ways.  subject_sweep --selftest 7/7 both ways.
#   worst BULGE, gated      1.570x -> 1.520x at f2313-2321. The one gain, on a
#                           figure already 15 % inside its own 1.80 bound.
#   local accel p99.9       4.20x -> 4.25x, and f2258 goes 4.19x -> 4.24x. It
#                           is marginally WORSE on the other census.
#   built path              324 frames move by more than a millimetre, 321 of
#                           them inside beat 5, worst 0.234 m at f1576, and the
#                           lens moves up to 1.12 mm at f2239.
#
# So it buys a 3.2 % improvement in a passing number and invalidates any
# rendered frame of the 1,524-frame beat that is 67 % of the master's render
# cost. The criterion is not wrong — it is the remedy for a SPECIFIC failure,
# a speed that changes while the bearing does not, and beat 2's braking event
# ran 2.64x the chord of the pair it sat between. Beats 3-5 do not do that.
# The right form of "enable it globally" is to leave it off and let
# `seam_gate --census` name the interval that needs it; today that census's
# worst gated interval anywhere is 1.570x.
#
# It stays off by default so nobody switches it on by accident, and now there
# is a measurement here rather than a caution.
SPEED_PER_KEY_FRAC = 0.20      # of the faster of the two frames
SPEED_PER_KEY_FLOOR_MS = 0.30  # so a slow drift does not emit densely


def emit_keys(anchors, f0, f1, world_of_frame, car, beat_name,
              frames=None, speed_key=False):
    """Sample the spline onto keys at an adaptive spacing.

    `frames` overrides the adaptive walk with an explicit list, which is how
    the seam bridge gets a spacing that RAMPS out of frame 754 and back into
    frame 793 instead of a uniform one. Blender's AUTO_CLAMPED handle at a key
    is computed from the two neighbouring keys' positions, so a key with a
    1-frame neighbour on one side and an 8-frame neighbour on the other gets a
    tangent dominated by the long side and overshoots: measured at frame 755,
    1.22 -> 1.71 m/s against an authored 1.20. Ramping the spacing is the same
    remedy R2-063 used at the beat-5/6 hand-off, and for the same reason.

    `speed_key` adds the speed criterion described above.
    """
    def sample(f):
        t = f / FPS
        wt = world_of_frame[f]
        # `path_point`, not `catmull_rom`: the bridge thread is part of where
        # the camera IS, so it has to be inside the sample the keys are cut
        # from, inside the bearing the adaptive walk spaces on, and inside the
        # focus distance that falls out of the pair. Adding it afterwards to
        # `world` alone — which is what a candidate sheet does — leaves the
        # focus pull aimed at where the camera used to be.
        pos = path_point(anchors, f)
        # the lens at this instant, because a framing offset is an angle and an
        # angle is only a picture once you know the field of view it sits in
        look = aim_at(anchors, t, car, wt, cam_pos=pos,
                      lens_mm=scalar_at(anchors, t, "lens"))
        return pos, look

    def bearing(f):
        pos, look = sample(f)
        d = [look[i] - pos[i] for i in range(3)]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        return [v / n for v in d]

    def speed(f):
        a = catmull_rom(anchors, (f - 1) / FPS)
        b = catmull_rom(anchors, f / FPS)
        return math.dist(a, b) * FPS

    # The emission window is the anchors' own span, clipped to the beat. A key
    # emitted past the last anchor is Catmull-Rom EXTRAPOLATION, which is where
    # the first draft of this function put the camera 680 m/s inside the car.
    f0 = max(f0, int(math.ceil(anchors[0]["t"] * FPS)))
    f1 = min(f1, int(math.floor(anchors[-1]["t"] * FPS)))

    if frames is not None:
        walk = [f for f in frames if f0 <= f <= f1]
        if not walk:
            raise SystemExit(f">> FAIL: {beat_name}: none of the {len(frames)} "
                             f"explicit frames lie inside {f0}-{f1}")
    else:
        walk = None

    keys, f = [], f0
    while True:
        pos, look = sample(f)
        t = f / FPS
        keys.append({
            "t": round(t, 5), "beat": beat_name,
            "world": [round(v, 4) for v in pos],
            "look_at": [round(v, 4) for v in look],
            "lens_mm": round(scalar_at(anchors, t, "lens"), 3),
            "fstop": round(scalar_at(anchors, t, "fstop"), 3),
            "focus_distance_m": round(max(math.dist(pos, look), 0.1), 4),
        })
        if f >= f1:
            break
        if walk is not None:
            nxt = [g for g in walk if g > f]
            f = min(nxt) if nxt else f1
            continue
        b0 = bearing(f)
        v0 = speed(f) if speed_key else 0.0
        step = MIN_KEY_GAP
        for cand in range(MIN_KEY_GAP, MAX_KEY_GAP + 1):
            g = min(f + cand, f1)
            b1 = bearing(g)
            dot = max(-1.0, min(1.0, sum(b0[i] * b1[i] for i in range(3))))
            if math.degrees(math.acos(dot)) > BEARING_PER_KEY_DEG:
                break
            if speed_key:
                v1 = speed(g)
                if abs(v1 - v0) > max(SPEED_PER_KEY_FLOOR_MS,
                                      SPEED_PER_KEY_FRAC * max(v0, v1)):
                    break
            step = cand
        f = min(f + step, f1)
    return keys


def ramped_frames(f_lo, f_hi):
    """Frame numbers from `f_lo` to `f_hi` whose gaps ramp 1,2,3,... and back.

    Both ends therefore have a 1-frame neighbour, which is what makes the
    AUTO_CLAMPED handles at the two keys OUTSIDE this range — beat 1's last and
    beat 2's first — symmetric enough not to be dragged by the long side.
    """
    span = f_hi - f_lo
    if span <= 2:
        return list(range(f_lo, f_hi + 1))
    front, back, k = [], [], 1
    while True:
        if sum(front) + sum(back) + k > span:
            break
        front.append(k)
        if sum(front) + sum(back) + k > span:
            break
        back.insert(0, k)
        k += 1
    gaps = front + back
    rest = span - sum(gaps)
    if rest:                                   # the slack goes in the middle,
        i = gaps.index(max(gaps))              # where the curve is quietest
        gaps[i] += rest
    out, f = [f_lo], f_lo
    for g in gaps:
        f += g
        out.append(f)
    assert out[-1] == f_hi, (out, gaps, span)
    return out


# ------------------------------------------------------------ choreography --
def build_anchors(car, W):
    """Every anchor, per beat. `W` is the film-frame -> world-time table."""
    cl = centreline_table(car.spec, 2.0)

    def tp(t, ds, u, h):
        return track_point(car, W, t, ds, u, h)

    def cp(track_s, u, h):
        return cl_point(cl, track_s, u, h)

    b2 = [
        # --- the seam, R2-064. Two transcribed anchors, not choreography. ---
        A(B1_LAST_T, B1_LAST_POS, B1_LAST_LENS, B1_LAST_FSTOP,
          aim_car(along_m=B1_LAST_ALONG, z_off=B1_LAST_ZOFF),
          "BEAT 1'S LAST KEY, transcribed. The spline starts here so the "
          "camera leaves beat 1 at the speed beat 1 is actually travelling "
          "(1.107 m/s measured) instead of at whatever a one-sided endpoint "
          "tangent implies. This anchor emits no key inside beat 1: the "
          "bridge starts at frame 755."),
        A(SEAM_T, SEAM_POS, SEAM_LENS, SEAM_FSTOP,
          aim_car(along_m=SEAM_ALONG, z_off=SEAM_ZOFF),
          "BEAT 2'S FIRST KEY, pinned. Being an INTERIOR anchor is the whole "
          "point: Fritsch-Carlson now limits the departure tangent to 3x the "
          "smaller adjacent secant, which takes the speed leaving frame 793 "
          "from 8.85 m/s to 3.17 m/s against the 3.33 m/s beat 1 delivers. "
          "The old first anchor sat at t = 33.00 — half a frame BEFORE this "
          "key and outside beat 2's own emission window, so it could never "
          "control the departure it was written to control."),
        # The old t=33.70 'arrived: low, beside the rear wheel' station is
        # GONE, deliberately. It sat 1.0 m from the ignition station 9 frames
        # later, which is what forced 5.67 m of descent into 16 frames and made
        # the late acceleration violent no matter how it was smoothed. The
        # descent is now one segment, frame 793 to the ignition station, and it
        # peaks at 8.92 m/s instead of 9.94 authored / 11.34 built.
        A(34.07, [-1.55, -5.30, 0.58], 35, 2.8, aim_car(along_m=-1.6, z_off=0.40),
          "IGNITION / LAUNCH. camera static, lens 5.5 m off the rear tyre"),
        A(34.55, [-0.55, -5.28, 0.60], 35, 2.8, aim_car(along_m=-1.4, z_off=0.40),
          "10 frames of sanctioned wheelspin; the car erupts past a still camera"),
        A(35.20, [4.60, -4.90, 0.88], 32, 3.2, aim_car(z_off=0.55),
          "hook-up; the camera swings up and gives chase, deliberately slower"),
        A(36.00, [10.60, -4.00, 1.50], 28, 4.0, aim_car(lead_s=0.06, z_off=0.70),
          "the nose meets the glass. beat 3 begins on this frame"),
    ]

    b3 = [
        A(36.00, [10.60, -4.00, 1.50], 28, 4.0, aim_car(lead_s=0.06, z_off=0.70),
          "IMPACT. world time collapses to 15.4 % over 6 frames"),
        A(37.20, [13.90, -2.30, 1.95], 21, 4.0, aim_car(along_m=1.6, z_off=0.60),
          "at the aperture, converging on its centre line; shards blooming"),
        A(38.60, [17.60, -1.20, 2.35], 21, 4.0, aim_car(along_m=-1.2, z_off=0.60),
          "through the 9.6 x 5.6 m hole, 2 m off the car, inside the cloud"),
        A(40.20, [24.00, 1.60, 3.30], 24, 4.0, aim_car(along_m=-1.0, z_off=0.70),
          "crossing the wake left, climbing; glass hanging between lens and car"),
        A(41.80, [38.00, 6.50, 4.90], 28, 4.5, aim_car(z_off=0.70),
          "MONEY FRAME: ahead-left and 5 m up, looking BACK at the car coming "
          "through the curtain, the wound in the building behind it"),
        A(43.00, [48.00, 8.00, 5.60], 32, 5.0, aim_car(z_off=0.80),
          "time blooms back over 15 frames; the car surges"),
        A(44.00, [58.00, 7.00, 5.40], 32, 5.6, aim_car(lead_s=0.05, z_off=0.80),
          "hand-off to beat 4 at 10.1 m/s, still ahead of the car"),
    ]

    b4 = [
        A(44.00, [58.00, 7.00, 5.40], 32, 5.6, aim_car(lead_s=0.05, z_off=0.80),
          "the car is about to pass underneath and power away"),
        A(45.10, [76.00, 13.00, 9.50], 32, 5.6, aim_car(z_off=0.80),
          "rising off the apron; the car overtakes the camera"),
        A(46.30, [112.00, 26.00, 15.50], 35, 5.6, aim_car(z_off=0.80),
          "17 m up over the merge arc: paddock, pit lane and circuit in one frame"),
        A(47.50, [172.00, 55.00, 17.00], 35, 5.6, aim_car(z_off=0.80),
          "cutting the chord of the R150 merge; the car is on the arc below"),
        A(48.60, [236.00, 96.00, 11.00], 35, 5.6, aim_car(z_off=0.80),
          "diving back down onto the pit straight behind the car"),
        A(49.60, [295.00, 141.00, 5.60], 35, 5.6, aim_car(z_off=0.80),
          "crossing the line 45 m behind the car and UNDER the start/finish "
          "gantry. 5.60 m and not the 6.20 the first draft used: the placement "
          "gate measured the gantry's lowest structure in the camera's way at "
          "z = 7.05, which left the 1.20 m camera sphere 0.513 m of clearance"),
    ]

    b5 = [
        A(49.60, [295.00, 141.00, 5.60], 35, 5.6, aim_car(z_off=0.80),
          "beat 5 opens on the same frame beat 4 closed: one camera, no seam"),
        A(50.90, tp(50.90, -42, -2.0, 5.0), 35, 5.6, aim_car(z_off=0.75, frame_u=0.306, frame_v=-0.148),
          "still 42 m back: the camera matches the car's 85 m/s before it starts "
          "closing, because doing both at once bulges the spline to 111 m/s"),
        A(52.20, tp(52.20, -30, -6.0, 3.0), 35, 5.6, aim_car(z_off=0.70, frame_u=-0.34, frame_v=-0.111),
          "dropping right as the car brakes for T1. The camera does NOT brake "
          "with it — holding ~70 m/s through the braking zone is what closes it "
          "from 30 m back to 2 m back without a speed oscillation"),
        A(53.10, tp(53.10, -16, -9.0, 2.2), 40, 5.6, aim_car(z_off=0.70, frame_u=-0.374, frame_v=0.185),
          "tucked low off the right rear at 197 km/h into T1"),
        A(54.10, tp(54.10, -2, -15.0, 2.4), 40, 5.6, aim_car(z_off=0.70, frame_u=0.408, frame_v=0.111),
          "T1 apex from the outside, on the runoff, level with the kerb line"),
        A(55.70, tp(55.70, 0, -12.0, 4.5), 35, 5.6, aim_car(z_off=0.80, frame_u=0, frame_v=-0.222),
          "T2 Threshold, level with the car and rising"),
        A(57.20, tp(57.20, 14, -14.0, 7.0), 40, 5.6, aim_car(z_off=0.80, frame_u=-0.442, frame_v=-0.074),
          "east chute: the camera overtakes on the outside and starts running "
          "ahead — the only way to be somewhere before a 295 km/h car is"),
        A(59.00, cp(680, 6.0, 5.0), 40, 5.6, aim_car(z_off=0.80, frame_u=0.34, frame_v=0.148),
          "40 m ahead, crossing to the left of the line, descending"),
        # R2-085. THE '20 m AWAY' IN THIS NOTE WAS NEVER A DISTANCE TO THE CAR.
        # `cp(s, u, h)` is an ABSOLUTE station, so its `u` is an offset from the
        # CENTRELINE — and from t = 59.00 to t = 61.60 nothing in the anchor list
        # controls where the car is. The camera was authored to cross the racing
        # line from u = +20 to u = -20 over s 773 -> 848 while the car, which is
        # 13 m/s faster because the camera is spending its speed budget on 40 m
        # of lateral travel, caught it up and arrived at the crossing point at
        # the same moment. MEASURED at frame 1461:
        #
        #     closest approach       3.263 m   against a note that says 20 m
        #     relative speed        37.0 m/s, 40.3 m/s of it across the sightline
        #     required rotation     29.46 deg/frame = 51 % of the frame width
        #     the car subtends      82 deg of a 53.6 deg frame
        #
        # It is not a spline artefact and not a key artefact. The AUTHOR'S OWN
        # Catmull-Rom, sampled directly with no key emission and no Blender in
        # the loop, gives 3.263 m and 29.45 deg/frame — the built path gives
        # 3.263 and 29.457. The camera was asked for this.
        #
        # WHY EVERY GATE PASSED IT. The rig's aim gate scored beat 5 at 2.52 deg
        # because the camera IS pointed at the car; the camera-to-car BOX check
        # below scored 2.15 m against a 1.40 m floor because it is a collision
        # floor, not a photography one. R2-062's finding, from the other end of
        # the film: aim error and photographability are independent.
        #
        # THE FIX IS ONE SIGN. The anchor moves to the INSIDE of the kink — T3 is
        # a right-hander (spec: turn -28 deg, apex s 755), so u = -20 is inside,
        # and it is the side the next four anchors already run down into T4's
        # outside. The camera therefore stops crossing the racing line here at
        # all. `tools/subject_sweep.py` on the author's spline, frames 1400-1530:
        #
        #     u       h     worst sweep   closest    peak speed   peak accel
        #    +20     3.0      56.55 %      3.17 m     94.1 m/s      6.68 g   <- shipped
        #    +20    20.0      16.80 %     11.57 m     95.4 m/s      7.15 g
        #      0     3.0      11.81 %     10.51 m     84.7 m/s      4.29 g
        #    -16     3.0       6.28 %     17.97 m     83.1 m/s      3.36 g
        #    -20     3.0       7.01 %     20.00 m     83.2 m/s      3.43 g   <- this
        #    -24     3.0       7.79 %     21.39 m     83.3 m/s      3.51 g
        #
        # The station and the height were swept too and are worse on every axis:
        # moving the anchor downstream to s = 790 or 805 makes the camera sprint,
        # 111-122 m/s and 10-12 g. Height alone cannot fix it — at u = +20 it
        # takes h = 20 m to reach a WARN, and that is an aerial, not this shot.
        #
        # ALSO MEASURED AND NOT TAKEN: moving t=59.00 to u = -6 as well removes
        # the remaining s 680 -> 773 crossing and is better again (5.60 %,
        # 19.34 m, 2.49 g). It is not taken because it deletes a declared
        # choreographic move — "crossing to the left of the line" — to buy
        # margin on a number that already clears its WARN threshold by 1.7x,
        # and because one anchor is the smallest edit that closes the defect.
        #
        # CLEARANCE, from world_contract at s = 773: half_width 7.0 m, the right
        # barrier at u = -34.37, ground at u = -20 is z = -1.284 against a
        # centreline z of -0.643, so this anchor sits 3.64 m above the run-off
        # with 14 m of lateral room. The neighbouring anchors at s = 848 and 903
        # already fly u = -20 and -21 and are gated there.
        A(60.23, cp(773, -20.0, 3.0), 32, 5.6, aim_car(z_off=0.70, frame_u=-0.408, frame_v=0),
          "T3 Long Kink at 295 km/h from the INSIDE of the kink. The closest "
          "the car comes is 20.00 m, which is what this note used to claim and "
          "did not measure — see R2-085. 7.0 % of the frame width per frame at "
          "the pass: the fastest sustained pan of the lap outside the "
          "helicopter arc, and readable"),
        A(61.60, cp(848, -20.0, 5.0), 40, 5.6, aim_car(z_off=0.70, frame_u=0.272, frame_v=-0.185),
          "the camera has overtaken and is braking with the car. Stopping a "
          "camera from 68 m/s to a standstill takes 200 m, so it is laid out as "
          "four decelerating anchors and not as one; the first draft crammed it "
          "into a single segment and measured 16.8 g"),
        A(63.00, cp(903, -21.0, 4.6), 50, 5.6, aim_car(z_off=0.70, frame_u=0, frame_v=0.259),
          "the 295->80 km/h braking event comes head-on AT the lens, from 5.6 m up: BR_FenceMesh_L03 has a panel at s = 909.8, u = -14.10, top z = 0.88, and at 3.4 m the camera sphere passed 0.160 m from it"),
        A(64.40, cp(943, -17.0, 2.8), 40, 5.6, aim_car(z_off=0.60, frame_u=0.374, frame_v=-0.111),
          "down to 1.6 m on the hairpin entry; the car arrives on the brakes"),
        A(65.67, cp(976, -12.0, 2.4), 28, 5.6, aim_car(z_off=0.55, frame_u=-0.306, frame_v=0.074),
          "T4 LE PIN apex from the OUTSIDE at 2.4 m. Two drafts of this shot were on the inside and the placement gate rejected both: at u = +13 the camera sphere reached 1.181 m into BR_TyreWall_T4, and at u = +10.5 it still reached 1.095 m into BR_FenceMesh_L03 — the same catch fence that is itself 7.606 m INTO the racing line at s = 926 and 1.434 m into the car\'s own swept path. The inside of this hairpin is furniture, and some of the furniture is in the wrong place"),
        A(67.30, tp(67.30, -18, 4.0, 3.4), 35, 5.6, aim_car(z_off=0.60, frame_u=0, frame_v=-0.259),
          "hairpin exit: the camera drops in behind, low, on the surface"),
        A(70.00, tp(70.00, -26, 0.0, 2.6), 32, 5.6, aim_car(z_off=0.70, frame_u=0.34, frame_v=-0.037),
          "climbing S4 with the car"),
        A(73.01, tp(73.01, -14, -9.0, 4.4), 35, 5.6, aim_car(z_off=0.70, frame_u=-0.272, frame_v=0.185),
          "T5 La Rampe, inside, uphill"),
        A(76.00, cp(1400, 22.0, 26.0), 50, 5.6, aim_car(z_off=0.80, frame_u=0.442, frame_v=-0.296),
          "rising into the helicopter arc over the infield ridge"),
        A(78.85, cp(1557, 50.0, 40.0), 55, 5.6, aim_car(z_off=0.80, frame_u=-0.374, frame_v=-0.296),
          "T6 Weave 1 from 52 m out and 40 m up"),
        A(80.97, cp(1678, 62.0, 48.0), 60, 5.6, aim_car(z_off=0.80, frame_u=0.408, frame_v=-0.185),
          "T7 Weave 2: the arc leads the car through the esses"),
        A(83.21, cp(1824, 52.0, 46.0), 65, 5.6, aim_car(z_off=0.80, frame_u=-0.34, frame_v=0.222),
          "T8 Crest, the summit. the arc starts to leave the car here"),
        A(85.31, cp(1995, 34.0, 40.0), 70, 5.6, aim_car(z_off=0.80, frame_u=0.306, frame_v=-0.259),
          "T9 seen from 105 m ahead: the camera is already running for T10. From "
          "the esses to the station the stations are laid out on a smooth speed "
          "profile (57, 65, 76, 84, 86 m/s) rather than at the corners, because "
          "an anchor list that reads well and accelerates badly is still a bad "
          "camera move"),
        A(88.00, cp(2215, 2.0, 25.0), 75, 5.6, aim_car(z_off=0.80, frame_u=-0.408, frame_v=0.111),
          "crossing the track line ahead of the car, descending"),
        A(90.01, cp(2370, -26.0, 14.0), 80, 5.6, aim_car(z_off=0.80, frame_u=0.374, frame_v=-0.222),
          "T10 Panorama 1 at 255 km/h, seen from 195 m down the road: the camera "
          "is already on the doppler line and braking for it"),
        A(91.40, cp(2470, -26.0, 9.5), 85, 5.6, aim_car(z_off=0.80, frame_u=-0.238, frame_v=0.148),
          "T11 behind us; 170 m of deceleration is what a hover costs"),
        A(92.40, cp(2515, -26.0, 7.0), 85, 5.6, aim_car(z_off=0.80, frame_u=0.17, frame_v=-0.111),
          "settling onto the station: 45, 33, 22, 8, 1.5 m/s, five anchors, "
          "because arriving at a hover in one is a 6 g stop"),
        A(93.10, cp(2538, -26.0, 5.6), 80, 5.6, aim_car(z_off=0.80, frame_u=-0.102, frame_v=0.074), "settling"),
        A(93.60, cp(2549, -26.0, 5.0), 70, 5.6, aim_car(z_off=0.80, frame_u=0.068, frame_v=0), "settling"),
        A(94.10, [-579.60, -46.80, 4.86], 45, 5.6, aim_car(z_off=0.70, frame_u=-0.51, frame_v=0),
          "ARRIVED at the declared doppler station [-578.82, -47.47, 4.802], "
          "26.0 m off the centreline at s = 2555"),
        A(94.63, [-579.10, -47.20, 4.81], 40, 5.6, aim_car(z_off=0.60, frame_u=0.51, frame_v=0),
          "THE DOPPLER BEAT: 313 km/h passes 26 m away. The lens goes 85 -> 40 as "
          "the car closes, so the subject stays large while the camera does not "
          "move at all — the reverse of a chase, and the reason the audio's "
          "7.55-semitone sweep needs no special-casing. 40 mm and not the 24 the "
          "first draft used: at 24 mm a 5.698 m car at the declared 26.1 m slant "
          "range spans 12.5 deg of a 73.7 deg horizontal field, i.e. 14.6 % of "
          "the picture width, which is not a car ripping past. 40 mm puts it at "
          "24.3 %. Both were rendered and looked at"),
        A(96.60, [-577.60, -48.60, 4.76], 70, 5.6, aim_car(z_off=0.80, frame_u=0.476, frame_v=0.111),
          "3.0 s below 3 m/s across the pass — the hover the brief asks for"),
        A(97.60, [-568.80, -60.80, 5.20], 90, 5.6, aim_car(z_off=0.80, frame_u=-0.17, frame_v=-0.074),
          "the whip after the car. A hover to 50 m/s is the one move in the film "
          "that costs more than beat 6's 2.03 g; three anchors keep it near 3"),
        A(98.60, [-543.10, -96.40, 7.20], 120, 5.6, aim_car(z_off=0.80, frame_u=0.238, frame_v=-0.185),
          "long-lens follow into T12 Plongee's braking zone, 110 m away"),
        A(100.37, tp(100.37, -105, -6.0, 9.0), 85, 5.6, aim_car(z_off=0.80, frame_u=-0.34, frame_v=0.111),
          "T13 Hook: the camera is moving again and closing"),
        A(102.45, tp(102.45, -80, 4.0, 8.0), 70, 5.6, aim_car(z_off=0.80, frame_u=0.306, frame_v=-0.148),
          "T14 Flick"),
        A(105.19, tp(105.19, -70, 0.0, 6.0), 55, 5.6, aim_car(z_off=0.80, frame_u=-0.272, frame_v=0.185),
          "T15 Gate, the last corner, camera closing hard"),
        A(106.30, tp(106.30, -62, -1.0, 5.4), 45, 5.6, aim_car(z_off=0.80, frame_u=0.204, frame_v=-0.222),
          "T15 exit, closing"),
        A(107.60, tp(107.60, -34, 0.0, 4.6), 40, 5.6, aim_car(z_off=0.75, frame_u=-0.17, frame_v=-0.111),
          "onto the pit straight at 300+ km/h, tucking in"),
        A(109.00, tp(109.00, -8, 1.5, 3.6), 32, 5.6, aim_car(z_off=0.72, frame_u=0.102, frame_v=-0.074),
          "the tight onboard-like follow"),
        A(109.60, tp(109.60, 0, 0.6, 3.0), 32, 5.6, aim_car(z_off=0.78, frame_u=0, frame_v=0),
          "directly over the car at 83 m/s"),
        # 2642 / 24, NOT 110.10. Beat 6's key t = -3.0 lands on film 110.1, which
        # is frame 2642.4; the rig keys it at 2642. Ending beat 5's spline at
        # 110.10 therefore asked the camera to cover 0.0583 s of travel in one
        # 0.0417 s frame — 119 m/s where the declared peel speed is 83.1, purely
        # from rounding. Landing the last anchor on the frame the key actually
        # occupies removes it.
        A(2642 / 24.0, [129.84, 2.37, 2.80], 32, 5.6, aim_car(z_off=0.80),
          "BEAT 6's declared peel-off point, matched exactly, on the frame the "
          "key actually occupies. Hand-off at 83 m/s, aim z-offset matched to "
          "beat 6's own so the two beats agree about where the car is"),
    ]
    return {"2_launch": b2, "3_breach": b3, "4_transit": b4, "5_lap": b5}


# ----------------------------------------------------------- beat 6's aiming --
def beat6_aim(sheet, spec):
    """Rotation for beat 6's EXISTING keys, without moving one of them.

    Beat 6's eight keys carry position, lens and speed and NO look_at, so
    `build_camera_rig.py` never keyed a rotation for them either: the frozen
    orientation that the defect report found after frame 754 in fact runs to the
    last frame of the film. The keys are left exactly as they are; what is added
    is the beat's declared SUBJECT, from which the rig derives rotation.

    R2-1701 (folding R2-85x, previously stranded in
    `docs/R2851_beat_sheet_CANDIDATE.json`): the subject is THE CAR for the whole
    of beat 6 —

        t -3.0 .. +11.0  the car

    and not the hand-off to the facade this function used to declare. The old
    reading followed the spec's `wound_enters_frame_t = 6.0` literally, but
    aiming AT the wound from t=+4.0 costs an 82 deg swing in 1.8 s (peak
    89.7 deg/s) — a whip that smears the whole frame — and it puts the film's
    subject off screen from f2845, 5.5 s before the last frame. Tracking the car
    peaks at 9.0 deg/s, a 10x reduction, because the camera is then following
    something that is genuinely traversing that arc rather than jumping to a
    point 82 deg away. `fixed_point` is kept so the wound stays declared and the
    sight-line gate still has something to measure, but with `point_from_t` at
    the end of the beat it is never reached: the aim is the car throughout.

    `bound_deg` tightens 32.0 -> 26.0 because the closing lens now pushes to
    130 mm; the bound is a fraction of the frame, and the frame is narrower.
    """
    wound = list(spec["showroom"]["breach_face_centre_world"])
    return {"subject": "the car, for the whole of beat 6",
            "fixed_point": wound,
            "car_until_t": 11.0, "point_from_t": 11.0,
            "z_off": 0.80, "bound_deg": 26.0,
            "why": "R2-85x. The shipped sheet handed the aim off to the breached "
                   "facade at t=+4.0. That cost an 82 deg swing in 1.8 s (peak "
                   "89.7 deg/s, a whip that smears the whole frame) and put the "
                   "film's subject off-screen from f2845 -- 5.5 s before the "
                   "last frame. Tracking the car for the whole beat costs "
                   "9.0 deg/s peak, a 10x reduction, because the camera is "
                   "following something that is actually moving through that arc "
                   "instead of jumping to a point 82 deg away.",
            "superseded": {
                "subject": "car until t=+4.0, then the breached facade",
                "car_until_t": 4.0, "point_from_t": 6.0, "bound_deg": 32.0}}


# ------------------------------------------------------------------- report --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--telemetry", default=os.path.join(R2, "telemetry/telemetry.csv"))
    ap.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sheet = json.load(open(args.sheet))
    spec = json.load(open(args.spec))
    N = int(sheet["total_frames"])
    car = Car(args.telemetry, spec)

    scales, ramp_info = FT.build_time_map(sheet, N)
    W = FT.world_time_table(scales, N)
    for r in ramp_info:
        assert abs(r["achieved_world_s"] - r["declared_world_s"]) < 1e-6, r
        print(f">> ramp {r['beat']}: frames {r['frames']}, floor solved "
              f"{r['solved_floor']:.5f} (declared {r['declared_floor']}), "
              f"world {r['achieved_world_s']:.4f} s == declared "
              f"{r['declared_world_s']} s, ease {r['ease_in_frames']} in / "
              f"{r['ease_out_frames']} out")

    anchors = build_anchors(car, W)
    beats = {b["name"]: b for b in sheet["beats"]}

    # ONE SPLINE, not four. Beats 2-5 share their boundary anchors (36.00, 44.00,
    # 49.60), so splining each beat separately still puts the camera in the right
    # place at a junction — and gives it the WRONG VELOCITY there, because each
    # spline's endpoint tangent is one-sided. Measured at the beat-4/beat-5
    # boundary: 74 m/s arriving, 103 m/s leaving, a 29 m/s step inside one frame.
    # Concatenating first is what makes the junctions C1, and it is the same
    # class of error as the defect this file exists to fix: a per-beat artefact
    # that looks correct until you measure across the boundary.
    chain = []
    for name in ("2_launch", "3_breach", "4_transit", "5_lap"):
        for a in anchors[name]:
            if chain and abs(a["t"] - chain[-1]["t"]) < 1e-6:
                continue
            chain.append(a)

    # Beat 6's first key already occupies film 110.1 (its own t = -3.0), which
    # is inside beat 5's span. Beat 5 therefore stops one frame short of it
    # rather than writing a second key on the same frame: two keys on one frame
    # is a silent race over which one wins, and the whole point here is that
    # nothing about this camera is decided silently.
    b6_start = next(b["start_s"] for b in sheet["beats"] if b["name"] == "6_ending")
    b6_first_f = min(int(round((b6_start + float(k["t"])) * FPS))
                     for k in sheet["beat6"]["keys"])

    out_blocks, all_keys = {}, []
    for name in ("2_launch", "3_breach", "4_transit", "5_lap"):
        b = beats[name]
        f0 = int(round(b["start_s"] * FPS)) + 1
        f1 = int(round((b["start_s"] + b["duration_s"]) * FPS))
        if f1 >= b6_first_f:
            f1 = b6_first_f - 1
        ks = emit_keys(chain, f0, f1, W, car, name,
                       speed_key=(name == "2_launch"))
        out_blocks[name] = ks
        all_keys += ks
        print(f">> {name:<10} frames {f0:5d}-{f1:5d}  {len(ks):4d} keys "
              f"from {len(anchors[name]):2d} anchors")

    # ---- THE SEAM BRIDGE, frames 755-792.  R2-064. ----------------------
    #
    # Off the SAME chain, so the bridge and beat 2 are one cubic Hermite and
    # the velocity at frame 793 is continuous by construction rather than by
    # agreement between two solves. It goes into its own block because putting
    # it in `beat2` would make `sorted(beat2.camera_keys)[0]` a different key
    # and every seam number ever quoted would change without the seam moving.
    seam_frames = ramped_frames(SEAM_BRIDGE_F0, SEAM_BRIDGE_F1)
    seam_keys = emit_keys(chain, SEAM_BRIDGE_F0, SEAM_BRIDGE_F1, W, car,
                          "1_2_seam", frames=seam_frames, speed_key=True)
    all_keys += seam_keys
    print(f">> {'1_2_seam':<10} frames {SEAM_BRIDGE_F0:5d}-{SEAM_BRIDGE_F1:5d}"
          f"  {len(seam_keys):4d} keys — the 39-frame hole beat 1 and beat 2 "
          f"left between them")
    print(f">> seam bridge spacing (ramped out of f754 and into f793): "
          + " ".join(str(g) for g in
                     [seam_frames[i + 1] - seam_frames[i]
                      for i in range(len(seam_frames) - 1)]))

    # ---- and REFUSE to write if the pinned key stopped reproducing ------
    #
    # The four seam invariants are properties of two keys. Beat 1's is not
    # written by this file, so the only way this file can break them is by
    # emitting a different key at frame 793 — which is exactly what happens if
    # somebody edits an anchor near the seam without noticing. Checked against
    # the transcribed constants, in the artefact this run produced.
    k793 = [k for k in out_blocks["2_launch"] if int(round(k["t"] * FPS)) == SEAM_F]
    seam_fail = []
    if len(k793) != 1:
        seam_fail.append(f"expected exactly one beat-2 key on frame {SEAM_F}, "
                         f"emitted {len(k793)}")
    else:
        k = k793[0]
        want = {"world": [round(v, 4) for v in SEAM_POS],
                "look_at": [round(SEAM_ALONG, 4), 0.0, round(SEAM_ZOFF, 4)],
                "lens_mm": round(SEAM_LENS, 3), "fstop": round(SEAM_FSTOP, 3)}
        for fld, wv in want.items():
            gv = k[fld]
            same = (all(abs(a - b) < 5e-5 for a, b in zip(gv, wv))
                    if isinstance(wv, list) else abs(gv - wv) < 5e-4)
            if not same:
                seam_fail.append(f"beat 2's key at frame {SEAM_F} has "
                                 f"{fld} = {gv}, not the pinned {wv}")
    if seam_fail:
        for m in seam_fail:
            print("   FAIL " + m)
        print(">> the four seam invariants (chord 2.0893 m, speed 1.2727 m/s, "
              "look angle 13.2504 deg, lens delta -0.051 mm) are beat 1's "
              "hand-off contract and this run would have moved them.")
        print(">> STAGE RESULT: SEAM_PIN_BROKEN")
        sys.exit(1)
    print(f">> seam pin: beat 2's frame-{SEAM_F} key reproduces the declared "
          f"world/look_at/lens/fstop exactly; the four invariants are held by "
          f"construction")

    # ---- measure what was just authored --------------------------------
    #
    # PER FRAME off the spline, not per key. Adaptive key spacing means a finite
    # difference between consecutive KEYS divides by anything from 2 to 8
    # frames, and differentiating that twice reports accelerations that are an
    # artefact of the sampling rather than a property of the move (the first run
    # of this said 42 g). The spline is what the rig follows, so the spline is
    # what gets measured.
    cl = centreline_table(spec, 4.0)
    worst_speed = (0.0, 0)
    worst_acc = (0.0, 0)
    worst_near = (1e9, 0)
    if True:
        fa = int(math.ceil(chain[0]["t"] * FPS))
        fb = int(math.floor(chain[-1]["t"] * FPS))
        pts = {f: path_point(chain, f) for f in range(fa, fb + 1)}
        for f in range(fa, fb + 1):
            wt = W[max(1, min(N, f))]
            p, hd, _v = car.state(wt)
            d = obb_dist(pts[f], p, hd)
            if d < worst_near[0]:
                worst_near = (d, f)
            if f - 1 in pts:
                v = math.dist(pts[f], pts[f - 1]) * FPS
                if v > worst_speed[0]:
                    worst_speed = (v, f)
                if f - 2 in pts:
                    v0 = math.dist(pts[f - 1], pts[f - 2]) * FPS
                    acc = abs(v - v0) * FPS
                    if acc > worst_acc[0]:
                        worst_acc = (acc, f)
    worst_near, near_frame = worst_near
    worst_speed, speed_frame = worst_speed
    worst_acc, acc_frame = worst_acc

    print(f">> {len(all_keys)} keys authored across beats 2-5")
    print(f">> worst-case key spacing {max_key_gap(all_keys)} frames "
          f"(cap {MAX_KEY_GAP}); the rig, not a bake")
    print(f">> camera speed          max {worst_speed:8.2f} m/s "
          f"({worst_speed * 3.6:.0f} km/h) at frame {speed_frame}")
    print(f">> camera acceleration   max {worst_acc:8.2f} m/s^2 "
          f"({worst_acc / 9.81:.2f} g) at frame {acc_frame}")
    print(f">> camera-to-car BOX     min {worst_near:8.3f} m at frame {near_frame} "
          f"(floor {CAM_CAR_MIN_M} m)")

    # ---- what beat 5's bridge thread costs, reported every run -------------
    #
    # The displacement's whole justification is that it is CHEAPER in the camera
    # envelope than the path it replaces (R2-1004), and a justification nobody
    # re-measures is a claim. Both profiles are read off this file's own spline,
    # over R2-740's window, so they are comparable to each other; the built path
    # smooths them both by roughly the same amount.
    PW = (2120, 2240)

    def _acc_peak(with_thread):
        pp = {}
        for f in range(PW[0] - 4, PW[1] + 5):
            p = catmull_rom(chain, f / FPS)
            if with_thread:
                d = pont_offset(f)
                p = [p[0] + d[0], p[1] + d[1], p[2] + d[2]]
            pp[f] = p
        vs = [math.dist(pp[f], pp[f + 1]) * FPS for f in range(PW[0] - 4, PW[1] + 4)]
        acc = [abs(vs[i + 1] - vs[i]) * FPS for i in range(len(vs) - 1)]
        return max(vs), max(acc)
    _v_off, _a_off = _acc_peak(False)
    _v_on, _a_on = _acc_peak(True)
    print(f">> beat-5 bridge thread  f{PONT_F0}-{PONT_F1}, du +{PONT_DU:.1f} m "
          f"inboard / dz {PONT_DZ:.1f} m: over f{PW[0]}-{PW[1]} peak |a| "
          f"{_a_off:.1f} -> {_a_on:.1f} m/s^2 "
          f"({_a_off / 9.81:.2f} -> {_a_on / 9.81:.2f} g), "
          f"peak v {_v_off:.1f} -> {_v_on:.1f} m/s")

    # The envelope is derived from the car, not fitted to the camera. A camera
    # that has to outrun a 84.5 m/s car needs headroom over it, and a camera is
    # not limited by tyres, so:
    #   speed  <= 1.5 x the car's own peak speed
    #   accel  <= 2.0 x the car's own peak lateral g (4.89 g at T3)
    # Both are far inside the continuity gate's 12 m/frame (288 m/s), which is
    # the only hard bound; these are craft limits and they are stated here so
    # they cannot quietly be relaxed to whatever the camera happened to measure.
    v_car = max(car.v)
    g_car = max(c["lateral_g"] for c in spec["corners"])
    speed_limit = 1.5 * v_car
    accel_limit = 2.0 * g_car * 9.81
    print(f">> envelope: speed limit {speed_limit:.1f} m/s (1.5 x the car's "
          f"{v_car:.1f}), accel limit {accel_limit / 9.81:.2f} g "
          f"(2 x the car's {g_car:.2f} g at T3)")
    fails = []
    if worst_near < CAM_CAR_MIN_M:
        fails.append(f"camera {worst_near:.3f} m from the car box at frame {near_frame}")
    if worst_speed > speed_limit:
        fails.append(f"camera speed {worst_speed:.1f} m/s at frame {speed_frame}")
    if worst_acc > accel_limit:
        fails.append(f"camera accel {worst_acc / 9.81:.2f} g at frame {acc_frame}")
    if fails:
        for f in fails:
            print("   FAIL " + f)
        print(">> STAGE RESULT: CAMERA_ENVELOPE_VIOLATION")
        sys.exit(1)

    # lateral offsets, reported so a reader can see where the camera flies
    print(">> lateral offset from the centreline at the lap's named vantages:")
    for anc in anchors["5_lap"]:
        lat, sta = lateral_of(cl, anc["pos"])
        print(f"     film {anc['t']:7.2f}  s={sta:8.1f}  u={lat:+8.2f} m  "
              f"z={anc['pos'][2]:6.2f}  {anc['note'][:58]}")

    if args.dry_run:
        print(">> dry run: beat_sheet.json not written")
        return

    # The bridge shipped for a few hours under the name `seam_1_2`, which the
    # `startswith("beat")` consumers could not see. Drop the old key rather
    # than leaving two blocks of camera keys in the file, which is precisely
    # the way a stale duplicate gets picked up later.
    sheet.pop("seam_1_2", None)
    sheet["beat1_2_seam"] = {
        "authored_by": "tools/author_beats2_5.py",
        "defect": "R2-064",
        "why": "beat 1's last key (t=31.4, frame 754) and beat 2's first "
               "(t=33.041667, frame 793) had 39 frames of nothing between "
               "them. Blender's AUTO_CLAMPED handle at 793 was computed from "
               "a 39-frame neighbour and a 2-frame one and overshot to "
               "11.3447 m/s through 98.49 m/s^2. These keys are that hole, "
               "filled off the same spline beat 2 is emitted from. They are "
               "NOT in beat2.camera_keys on purpose: the four seam invariants "
               "are properties of those two keys and any tool that finds them "
               "by list position must keep finding the same pair.",
        "frames": [SEAM_BRIDGE_F0, SEAM_BRIDGE_F1],
        "loaded_by": "anim/build_camera_rig.py load_keys()",
        "camera_keys": seam_keys,
    }
    for name, ks in out_blocks.items():
        key = "beat" + name.split("_")[0]
        sheet[key] = {"authored_by": "tools/author_beats2_5.py",
                      "anchors": [{"t": x["t"], "world": [round(v, 4) for v in x["pos"]],
                                   "lens_mm": x["lens"], "note": x["note"]}
                                  for x in anchors[name]],
                      "camera_keys": ks}

    # Beat 5's keys are the anchors PLUS the bridge thread, and a reader holding
    # only the anchors cannot reproduce them. This block says so, in the file
    # the rebuild reads, so nobody re-derives the offset from the difference or
    # re-applies it on top with `tools/r2731_pont_camera_candidate.py`.
    sheet["beat5"]["pont_thread"] = {
        "defect": "R2-971 / R2-1004 — the beat-5 bridge blackout",
        "why": "the camera crossed Le Pont de la Plongee 5.1 m ABOVE the soffit "
               "and 29 m outboard, and the car was wholly hidden f2180-2191. "
               "circuit_spec.md 10 specifies this pass as 'threads under it at "
               "~5 m altitude'. These keys carry a windowed displacement into "
               "the clear opening: the ANCHORS ALONE DO NOT REPRODUCE THEM.",
        "applied_by": "tools/author_beats2_5.py pont_offset(), inside "
                      "emit_keys' own sampler — not a post-pass on `world`",
        "station_s": PONT_S,
        "lateral_m": PONT_DU, "lateral_window": list(PONT_U_WIN),
        "vertical_m": PONT_DZ, "vertical_window": list(PONT_Z_WIN),
        "support_frames": [PONT_F0, PONT_F1],
        "interior_to_beat5_by_frames": [PONT_F0 - 1191, 2714 - PONT_F1],
        "measured": "occlusion 12 blocked frames -> 0 across all four bridge "
                    "bands; peak |a| over f2120-2240 below the path it "
                    "replaces; clearance 2.391 m against placement_gate's "
                    "1.20 m camera sphere; both beat-5 boundaries identical.",
        "do_not": "do NOT merge render/film_path_R2971_PONT_B5_REBASED.json or "
                  "any other film_path_*.json to get this. Those are whole-film "
                  "paths and adopting one reverts beat 1 by up to 9.9 m over "
                  "2,472 frames (R2-737, R2-1004 Defect 1). The offset is a "
                  "pure function of the frame index and rebases exactly.",
    }

    sheet["aim"] = {
        "why": "the continuity gate measured jumps, not aim. this block states, "
               "per beat, WHAT the camera must be pointed at, so the aim gate in "
               "anim/build_camera_rig.py has a subject to measure against.",
        "1_assembly": {
            "subject": "the exploded parts field: the nearest of the 15 cluster "
                       "volumes in docs/explode_plan.json, measured to the EDGE "
                       "of its bounding sphere, moved from its exploded position "
                       "to its seated one on the seat frames in "
                       "world/beat1_anim_anim.json",
            "bound_deg": 30.0,
            "authored_by": "not this file — beat 1's keys come from "
                           "tools/build_beatsheet.py",
            "status": "R2-029 FIXED. Beat 1 now carries 20 keys: the 15 "
                      "presentations plus a four-key CLOSE-OUT over frames "
                      "591-754 that swings around the nose instead of through "
                      "the car, shooting the NOSE/FW/RW seats and the "
                      "simultaneous four-corner landing at 696. Two separate "
                      "defects were in there: the 163-frame two-key gap (48.88 "
                      "deg off the field at frame 669, glass wall in the "
                      "picture at 648) AND keys authored against an older "
                      "docs/explode_plan.json, which put FD 18.3 deg and NOSE "
                      "33.9 deg OUTSIDE the frame at their own presentations. "
                      "Both are gated now by tools/build_beatsheet.py, which "
                      "fails the pre-fix sheet.",
        },
        "1_assembly_rejected_model": {
            "subject": "the single cluster the nearest key nominates",
            "worst_deg": 118.95,
            "why_rejected": "beat 1 is a weave THROUGH the field; between two "
                            "presentations the lens is on the parts in between. "
                            "This model called 273 frames a miss that the picture "
                            "shows are not. Recorded so nobody re-derives it and "
                            "sends someone to fix a camera that is working.",
        },
        "2_launch": {"subject": "car", "z_off": 0.55, "bound_deg": 20.0},
        "3_breach": {"subject": "car", "z_off": 0.65, "bound_deg": 24.0},
        "4_transit": {"subject": "car", "z_off": 0.80, "bound_deg": 14.0},
        "5_lap": {"subject": "car", "z_off": 0.80, "bound_deg": 22.0},
        "6_ending": beat6_aim(sheet, spec),
        "frame_margin": 0.92,
    }
    sheet["time_map"] = {
        "note": "film frame -> world time. beat 3's ramp offsets the two clocks "
                "permanently; anything sampling the telemetry per frame must "
                "walk this. Implementation: anim/filmtime.py",
        "launch_film_t": FT.LAUNCH_FILM_T,
        "glass_world_t": FT.GLASS_WORLD_T,
        "ramps": ramp_info,
    }
    for r in sheet.get("speed_ramps", []):
        if r["beat"] == "3_breach":
            r["min_world_time_scale"] = round(ramp_info[0]["solved_floor"], 6)
            r["min_world_time_scale_note"] = (
                "SOLVED, not chosen: the declared 8.0 s screen / 1.6 s world "
                "forces a mean scale of exactly 0.20, which with a 6-frame ease "
                "in and a 15-frame ease out lands the floor here. The previous "
                "0.20 was the floor AND the mean, which is only possible with "
                "no ease at all; the implementation that shipped with it "
                "integrated to 3.73 s of world time, not 1.6.")
    json.dump(sheet, open(args.sheet, "w"), indent=1)
    print(f">> wrote {args.sheet}")
    print(">> STAGE RESULT: BEATS_2_5_AUTHORED")


def obb_dist(p, car_pos, heading):
    """Distance from a world point to the SURFACE of the car's oriented box.

    The car is 5.698 x 2.005 x 0.992 sitting on the road at `car_pos` with its
    reference point on the ground. Measuring to the reference point instead
    would call a camera 2.8 m directly overhead "1.8 m from the car" when it is
    in fact 1.81 m clear of the roof — a difference that matters exactly at
    beat 6's peel-off, which is the tightest camera-to-car figure in the film.
    """
    c, s = math.cos(heading), math.sin(heading)
    d = [p[0] - car_pos[0], p[1] - car_pos[1], p[2] - car_pos[2]]
    lx = d[0] * c + d[1] * s
    ly = -d[0] * s + d[1] * c
    lz = d[2] - CAR_TOP_Z * 0.5
    ex, ey, ez = CAR_HALF_LEN, CAR_HALF_W, CAR_TOP_Z * 0.5
    ox = max(abs(lx) - ex, 0.0)
    oy = max(abs(ly) - ey, 0.0)
    oz = max(abs(lz) - ez, 0.0)
    outside = math.sqrt(ox * ox + oy * oy + oz * oz)
    if outside > 0.0:
        return outside
    return max(abs(lx) - ex, abs(ly) - ey, abs(lz) - ez)   # negative = inside


def max_key_gap(keys):
    fs = sorted(int(round(k["t"] * FPS)) for k in keys)
    return max((b - a for a, b in zip(fs, fs[1:])), default=0)



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="author_beats2_5")
