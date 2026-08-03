"""THE CAMERA — one unbroken path, first frame to last. The film's governing law.

    /opt/blender-5.2.0-linux-x64/blender -b <world.blend> --factory-startup \
        -P anim/build_camera_rig.py -- --sheet docs/beat_sheet.json \
        --telemetry telemetry/telemetry.csv --out world/camera_rig.blend

THE LAW
-------
    "The entire video — assembly, wall breach, drive to the track, the full lap,
     the ending — is a SINGLE unbroken camera take. Zero cuts. Zero crossfades.
     Zero hidden whip-pan cheats. One camera, one continuous path through space
     and time, first frame to last frame."

Everything here bends to that. There is exactly ONE camera object — every other
camera in the incoming scene is deleted, both because the law says one and
because the render worker prewarms every camera it finds. It is never hidden,
never swapped, never re-parented mid-shot. If a move is impossible, the answer
is a different move, not a cut.

WHAT IS ANIMATED
----------------
  * location and rotation, from every beat's keys, eased
  * focal length — the lens changes DURING the take, which is legal and is how a
    real oner breathes; a cut is not
  * aperture and focus distance — "DOF as the presenter" in Beat 1, focus pulls
    from part to part, eased, never snapped
  * exposure — the camera crosses from a darkened showroom interior to full
    daylight. THE BRIEF PUTS THIS ON THE CAMERA, NEVER ON THE GRADE: a per-beat
    grade change would betray the cut-free illusion, so the exposure ramp lives
    here as an animated value. It is keyed RELATIVE to whatever exposure the
    incoming scene is calibrated at, not to an absolute 0.0.

WHAT WAS WRONG WITH THIS FILE, AND IS NOT NOW
---------------------------------------------
Four defects, all of the same family — an artefact that passed every check
because no check measured the thing that mattered.

1. **Beats 2-5 had no camera.** This file read `sheet["beat1"]["camera_keys"]`
   and `sheet["beat6"]["keys"]` and nothing else. 24 keys for 2,978 frames. Over
   the 1,960-frame gap the camera drifted a 123 m straight line at 1.5 m/s with
   its orientation FROZEN, while the car was a median 612 m away. Key loading is
   now driven by the beat list, so a beat that exists gets read.

2. **The continuity gate was orthogonal to the failure.** A slow straight drift
   has no position jump and no rotation step, so `CAMERA_RIG_CONTINUOUS` was a
   true statement about a rig pointed at nothing. The AIM GATE below measures
   the angle between the camera's -Z axis and the direction to each beat's
   DECLARED SUBJECT, every frame, and where that subject lands in the frame.

3. **Beat 6's keys were offset by +3.0 s** (`b6_start + k["t"] + 3.0`), which
   put its final 3 s hold at film 124.1-127.1 — entirely past the end of a
   2,978-frame film — and put the camera's peel-off 260 m from the car. Three
   numbers say the offset should be zero: beat 6's peel-off position
   [129.84, 2.37, 2.8] is EXACTLY the car's own telemetry position at world
   t = 69.631 lifted 2.8 m; its declared peel speed 83.1 m/s is the car's 83.05
   there; and with no offset the 3 s hold lands exactly on the film's last 3 s.

4. **Beat 6 had no rotation at all.** Its keys carry position, lens and speed
   and no `look_at`, so the `if k.get("look_at")` branch never fired for them:
   the frozen orientation ran not to frame 2714 but to the last frame of the
   film. Rotation for beat 6 is now derived from the beat's declared subject in
   `sheet["aim"]["6_ending"]` without moving one of its keys.

5. **Beat 6 does not start on a frame, and its keys were rounded onto one.**
   R2-063. The beat begins at 113.1 s, so 113.1 x 24 = 2714.4 and every one of
   its eight declared keys lands at .4 of a frame. This file forced each
   declared POSITION onto `round(t * FPS)` and called that "reproduced
   exactly". At the peel-off the camera is doing 83.1 m/s, so 0.4 of a frame is
   **1.385 m of position error placed on frame 2642** — and the campath gate
   measured the consequence as a -473 m/s^2 spike, a 25 m/s speed swing across
   f2642-2646, and a 19.1 deg/frame aim swing at f2644 that is **32 % of the
   frame width in one frame**, the second-worst smear in the film. The
   beat-5/beat-6 hand-off is now blended over 36 frames and the rounding is not
   applied inside that window. See the block in main().

THE FAILURE MODE ALL FIVE SHARE
-------------------------------
Not one of them was a bad camera move. Every one was an artefact of HOW THE
KEYS WERE ASSEMBLED — a beat nobody read, an offset nobody checked, a branch
that never fired, a rounding nobody measured — and every one passed whatever
gate existed at the time. The gates that catch them are `tools/continuity_gate
--campath` (render-free, per frame) and the AIM GATE below, and the reason both
exist is that a claim about a camera is not a measurement of one.

TIME REMAPPING AND MOTION BLUR — AND THE ARGUMENT THAT WAS WRONG HERE
---------------------------------------------------------------------
Beat 3 slows WORLD time while the camera keeps flying in real time — the brief
calls that contrast "the money moment of the entire video".

This file used to key `motion_blur_shutter = 0.5 * world_time_scale[f]`, and
justified it with this, which reads as obviously correct and is not:

    "A 180-degree shutter at 24 fps exposes for 1/48 s of WORLD time. If world
     time runs at 15 % and the shutter is left alone, the blur is nearly 7x too
     long and the slow-motion reads as smeared rather than crisp."

THE SLOWDOWN IS ALREADY IN THE ANIMATION. Cycles integrates motion blur over
`shutter` FILM frames by evaluating the depsgraph at sub-frame FILM times, and
everything that moves in this film is keyed on film frames sampled through
`filmtime.world_time_table`. During beat 3 the car's displacement PER FILM FRAME
is therefore already 15.4 % of what it would be at 1:1 — so one film frame spans
1/24 * 0.154 = 1/156 s of world time, and half of that, the 180-degree shutter,
is 1/312 s. That is EXACTLY what a 156 fps high-speed camera with a 180-degree
shutter would have recorded, which is what real slow motion is.

Scaling the shutter by the same factor applies the slowdown a SECOND time. It is
a double correction, and both R2-037 (measured from the other end: static
geometry got 6.5x less blur than the camera's own motion warranted) and
`PLAN-scope-optimisation.md` sec 11.7 (which suspected it and could not verify
it) are the same defect seen from two sides. The number is the same 6.5x because
it is 1 / 0.15372, the ramp's floor.

SO THE SHUTTER IS A CONSTANT 180 DEGREES, FIRST FRAME TO LAST. Not a compromise
between two clocks: there is only one clock, because the second correction was
never needed. Three things follow and are worth stating because they are the
questions this decision has to answer:

  * it cannot read as a cut, a stutter or a pulse, because it does not change.
    An animated shutter in a single continuous take is a real risk — the eye
    reads a blur change as an edit — and the fix removes the animation rather
    than smoothing it.
  * it does not move the exposure. Cycles normalises the motion-blur integral;
    `motion_blur_shutter` sets blur LENGTH, not how much light lands. So this
    change does not interact with the exposure work in DEFECT B.
  * the HERO tiering has to be re-derived against it, because tier membership is
    defined in resolvable pixels and resolvable pixels depend on this number.
    `tools/screen_presence.py --uniform-shutter` is that measurement.

`--shutter-mode world` restores the old behaviour, for A/B only. It is not a
supported way to render the film.

The time map itself moved to `anim/filmtime.py`, because the version that lived
here integrated to 3.73 s of world time against a declared 1.6 s — 2.13 s of
extra world time, i.e. the car 2.13 s further round the lap than the beat sheet,
the doppler station and beat 6's peel-off all assume.

CONTINUITY IS VERIFIED, NOT ASSERTED
------------------------------------
After building, every frame is stepped and the camera's world position, rotation
and aim are sampled. A discontinuity is a CUT by another name; a camera pointed
away from its subject is a shot of nothing. Both fail the build. This project's
whole method is that a claim is not evidence.
"""

import argparse
import csv
import json
import math
import os
import sys

import bpy
from mathutils import Vector, Quaternion, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import filmtime as FT                                              # noqa: E402
from carpath import Car                                            # noqa: E402

FPS = FT.FPS

sys.path.insert(0, os.path.join(R2, "world"))
try:
    import film_exposure as FX                                    # noqa: E402
except Exception as _e:                                           # pragma: no cover
    FX = None
    print(">> WARNING: world/film_exposure.py did not import (%s); the "
          "exposure ramp cannot be checked against the film's calibration"
          % _e)

# The brief's interior-to-daylight ramp, in stops. Applied as a DELTA from the
# scene's own calibrated exposure — see the exposure block in main().
# ONE SOURCE: world/film_exposure.py owns both ends of the ramp.
INTERIOR_STOPS = FX.INTERIOR_STOPS if FX else 0.85


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", required=True)
    p.add_argument("--telemetry", required=True)
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--explode", default=os.path.join(R2, "docs/explode_plan.json"),
                   help="the 15 exploded clusters — beat 1's declared subject")
    p.add_argument("--beat1anim", default=os.path.join(R2, "world/beat1_anim_anim.json"),
                   help="when each cluster seats, so beat 1's subject is where "
                        "the parts ARE and not where they started")
    p.add_argument("--out", required=True)
    p.add_argument("--shutter", type=float, default=0.5,
                   help="180 degree shutter = 0.5 of a frame")
    p.add_argument("--shutter-mode", choices=("flat", "world"), default="flat",
                   help="flat: one 180-degree shutter for the whole take, which "
                        "is correct because the world-time ramp is already in "
                        "the animation. world: the old 0.5*world_time_scale "
                        "double correction, kept for A/B ONLY (R2-037).")
    p.add_argument("--res", type=int, nargs=2, default=[3840, 2160],
                   help="the delivery format, which is what the aim gate's "
                        "frame-containment test is judged against")
    return p.parse_args(argv)


def set_key_defaults():
    e = bpy.context.preferences.edit
    e.keyframe_new_interpolation_type = "BEZIER"
    e.keyframe_new_handle_type = "AUTO_CLAMPED"


# --------------------------------------------------------------- key loading --
def load_keys(sheet):
    """Every beat's camera keys, in film time. Driven by the BEAT LIST.

    The old version named two blocks by hand. Naming them by hand is how four
    beats went missing without anything noticing, so the beats drive the loop and
    a beat with no block is reported by name rather than skipped in silence.
    """
    keys, per_beat, missing = [], {}, []
    b6_start = None
    for b in sheet["beats"]:
        name = b["name"]
        block = sheet.get("beat" + name.split("_")[0], {})
        ks = block.get("camera_keys") or block.get("keys") or []
        if not ks:
            missing.append(name)
            per_beat[name] = 0
            continue
        if name == "6_ending":
            # Beat 6's keys are stored RELATIVE to the beat's own start, and are
            # the only ones that are. No +3.0: see this module's docstring.
            # They are rebuilt in main() from beat6_path() so the declared
            # trajectory is sampled densely enough to hand off from beat 5 and
            # to carry a rotation, which these keys have never had.
            b6_start = b["start_s"]
            per_beat[name] = len(ks)
            continue
        per_beat[name] = len(ks)
        for k in ks:
            k = dict(k)
            k.setdefault("beat", name)
            keys.append(k)

    # ---- THE BEAT-1 -> BEAT-2 SEAM BRIDGE.  R2-064. ----------------------
    #
    # Beat 1's last key is at frame 754 and beat 2's first at 793, and for 39
    # frames NOTHING was declared. That is not a slow passage the author chose;
    # it is a hole, and Blender filled it: the AUTO_CLAMPED handle at frame 793
    # was computed from a 39-frame neighbour on one side and a 2-frame one on
    # the other, and produced 11.3447 m/s where the keys ask for 9.3838, with
    # +98.49 m/s^2 landing on frame 794 — 21x the median |a| of its own
    # neighbourhood. No anchor inside `tools/author_beats2_5.py` could fix that
    # while the gap existed, because beat 2's emission window starts at 793:
    # the fix has to put KEYS in the hole, and this is where they are loaded.
    #
    # They live in their own block rather than in `beat2.camera_keys` because
    # the seam's four invariants — chord 2.0893 m, speed 1.2727 m/s, look angle
    # 13.2504 deg, lens delta -0.051 mm — are properties of the key at t=31.4
    # and the key at t=33.041667, and `work/campath/beat1_probe.py` finds that
    # second key as `sorted(beat2.camera_keys)[0]`. Inserting a key before it
    # would have silently re-pointed that probe at a different pair and printed
    # four different numbers for a seam that had not moved.
    #
    # Absent block = the pre-R2-064 sheet, and it is reported rather than
    # skipped in silence, because "a beat block quietly missing" is the exact
    # shape of the defect that left four beats with no camera at all.
    bridge = (sheet.get("beat1_2_seam") or {}).get("camera_keys") or []
    per_beat["1_2_seam"] = len(bridge)
    if not bridge:
        missing.append("1_2_seam (beat1->beat2 bridge, frames 755-792)")
    for k in bridge:
        k = dict(k)
        k.setdefault("beat", "1_2_seam")
        keys.append(k)

    keys.sort(key=lambda k: k["t"])
    return keys, per_beat, missing, b6_start


def basis_quat(v, ref):
    """Camera quaternion looking along `v` with image-up pulled toward `ref`."""
    zc = -v
    xc = ref.cross(zc)
    if xc.length < 1e-6:
        return None
    xc = xc.normalized()
    return Matrix((xc, zc.cross(xc), zc)).transposed().to_quaternion()


def look_quat(view, travel, prev_q, prev_v, gap_frames):
    """Camera orientation for a look direction, with a STABLE roll.

    `Vector.to_track_quat("-Z", "Y")` resolves roll by pulling the camera's +Y
    toward world +Z. That is undefined when the view direction IS world -Z and
    ill-conditioned for roughly 25 deg either side. Beat 5 ends with the camera
    2.0 m directly above the car at 83 m/s — a deliberate top-down follow — and
    the measured cost was a 36.9 deg-per-frame roll spin while the AIM angle sat
    at 0.0 deg: the lens never left the car and the picture barrel-rolled. The
    aim gate cannot see that. The continuity gate can, and did, which is the
    argument for keeping both.

    Two cheaper fixes were tried and both are in the measurements:

      * blend the reference from world +Z toward the direction of travel as the
        view goes vertical. The blended vector passes NEAR THE VIEW AXIS on a
        camera looking down-and-backward, the cross product's sign flips, and
        the result was 175 deg in one frame — worse than the problem.
      * narrow that blend window to the 26 deg cone. Same failure, 90 deg.

    So the roll is PARALLEL-TRANSPORTED: each key takes the previous key's
    orientation and applies the minimal rotation that carries the old view
    direction onto the new one. That is continuous by construction and cannot
    flip, because there is no cross product whose sign can change. Transport
    alone drifts, so it is then corrected toward a reference — world +Z where
    that is well-conditioned, the direction of travel where it is not, nothing
    where neither is — by at most 3 deg per FRAME of key gap. Beat 1's keys are
    42 frames apart, so its correction is effectively unlimited and it keeps the
    level horizon it had; beat 5's are 2 to 8 frames apart, so its roll is
    pulled level gently instead of snapping.
    """
    v = view.normalized()
    zc = -v
    if prev_q is None or prev_v is None:
        for ref in (Vector((0.0, 0.0, 1.0)),
                    Vector((travel.x, travel.y, 0.0)) if travel else None):
            if ref is None or ref.length < 1e-6:
                continue
            if ref.normalized().cross(zc).length >= 0.45:
                q = basis_quat(v, ref.normalized())
                if q:
                    return q, v
        q = basis_quat(v, Vector((1.0, 0.0, 0.0)) if abs(zc.x) < 0.9
                       else Vector((0.0, 1.0, 0.0)))
        return q, v

    # transport
    axis = prev_v.cross(v)
    c = max(-1.0, min(1.0, prev_v.dot(v)))
    if axis.length > 1e-9:
        q = Quaternion(axis.normalized(), math.atan2(axis.length, c)) @ prev_q
    else:
        q = prev_q.copy()

    ref = None
    for cand in (Vector((0.0, 0.0, 1.0)),
                 Vector((travel.x, travel.y, 0.0)) if travel else None):
        if cand is None or cand.length < 1e-6:
            continue
        cand = cand.normalized()
        if cand.cross(zc).length >= 0.45:
            ref = cand
            break
    if ref is not None:
        up_des = (ref - zc * ref.dot(zc)).normalized()
        up_now = q @ Vector((0.0, 1.0, 0.0))
        err = math.atan2(up_now.cross(up_des).dot(v), up_now.dot(up_des))
        lim = math.radians(3.0 * max(gap_frames, 1))
        q = Quaternion(v, max(-lim, min(lim, err))) @ q

    if q.dot(prev_q) < 0.0:
        q = Quaternion((-q.w, -q.x, -q.y, -q.z))
    return q, v


def fcurves_of(ob):
    """Every F-curve on an object, across Blender 4.x and 5.x action layouts."""
    ad = getattr(ob, "animation_data", None)
    act = getattr(ad, "action", None)
    if act is None:
        return []
    if hasattr(act, "fcurves"):                       # legacy (Blender <= 4.x)
        return list(act.fcurves)
    out = []
    slot = getattr(ad, "action_slot", None)
    for layer in act.layers:
        for strip in layer.strips:
            bags = []
            if slot is not None:
                bag = strip.channelbag(slot)
                if bag:
                    bags.append(bag)
            if not bags:
                bags = list(getattr(strip, "channelbags", []))
            for bag in bags:
                out += list(bag.fcurves)
    return out


def beat6_path(sheet, spec):
    """Beat 6's declared trajectory, resampled — WITHOUT moving one of its keys.

    Beat 6 ships 8 keys spanning 14 s, i.e. one every 48 frames, and the last
    two of them straddle the hand-off from beat 5's 2-to-8-frame keys. Blender's
    AUTO_CLAMPED handles do not know that, and the measured consequence was the
    camera surging to 125 m/s across the peel-off — 50 % over beat 6's own
    declared 83.1 m/s — for about a third of a second.

    The fix is not to move a key. Beat 6 declares its trajectory as

        "minimum-energy cubic from (peel, v=83.1 m/s along the pit straight) to
         (hold, v=0) in 11.0 s; peak |a| 19.9 m/s^2 (2.03 g) at the peel-off"

    and each key carries the SPEED the camera should have there. A cubic Hermite
    whose tangent magnitudes are those declared speeds IS that trajectory, and
    its chord/dt agrees with the mean of each pair of declared speeds to better
    than 1.5 % on all seven segments — so this reconstructs the intent rather
    than replacing it. The 8 declared keys are reproduced exactly, at their own
    frames; what is added is intermediate samples between them.
    """
    b6 = sheet["beat6"]
    start = next(b["start_s"] for b in sheet["beats"] if b["name"] == "6_ending")
    ks = sorted(b6["keys"], key=lambda k: k["t"])
    ts = [start + float(k["t"]) for k in ks]
    ps = [[float(v) for v in k["world"]] for k in ks]
    vs = [float(k.get("speed", 0.0)) for k in ks]
    lens = [float(k.get("lens_mm", 24.0)) for k in ks]

    heading = math.radians(float(spec["datum"]["racing_direction_world_deg"]))
    dirs = []
    for i in range(len(ks)):
        if i == 0:
            d = [math.cos(heading), math.sin(heading), 0.0]     # along the pit straight
        elif i == len(ks) - 1:
            d = [ps[i][c] - ps[i - 1][c] for c in range(3)]
        else:
            a = [ps[i][c] - ps[i - 1][c] for c in range(3)]
            b = [ps[i + 1][c] - ps[i][c] for c in range(3)]
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(x * x for x in b)) or 1.0
            d = [a[c] / na + b[c] / nb for c in range(3)]
        n = math.sqrt(sum(x * x for x in d)) or 1.0
        dirs.append([x / n for x in d])

    def at(t):
        i = 0
        while i < len(ts) - 2 and t > ts[i + 1]:
            i += 1
        h = ts[i + 1] - ts[i]
        u = max(0.0, min(1.0, (t - ts[i]) / h))
        u2, u3 = u * u, u * u * u
        h00 = 2 * u3 - 3 * u2 + 1
        h10 = u3 - 2 * u2 + u
        h01 = -2 * u3 + 3 * u2
        h11 = u3 - u2
        p = [h00 * ps[i][c] + h10 * h * dirs[i][c] * vs[i]
             + h01 * ps[i + 1][c] + h11 * h * dirs[i + 1][c] * vs[i + 1]
             for c in range(3)]
        L = lens[i] + (lens[i + 1] - lens[i]) * (u * u * (3.0 - 2.0 * u))
        return p, L

    return ts, at


def beat_of_frame(sheet, f):
    t = f / FPS
    last = sheet["beats"][0]["name"]
    for b in sheet["beats"]:
        if t >= b["start_s"]:
            last = b["name"]
    return last


# ------------------------------------------------------------ the aim subject --
class Subject:
    """WHERE THE FILM IS, per frame. The thing the aim gate measures against.

    Three kinds, all declared in `sheet["aim"]`:

      * the CAR, from telemetry at that frame's world time (beats 2-5, and beat
        6 until its keys leave the car). This is the honest subject: the film is
        about the car, and "the camera is pointed at the film" means pointed at
        it.
      * a FIXED POINT (beat 6's closing wide, whose declared content is the
        breached facade at [15, 0, 3.1] — `wound_enters_frame_t` is 6.0).
      * the EXPLODED PARTS FIELD for beat 1 — the nearest of the 15 cluster
        volumes from `docs/explode_plan.json`, measured to the EDGE of its
        bounding sphere rather than its centre.

        The first model written here was "the cluster this key nominates",
        interpolated between keys, and it failed beat 1 at 114 deg with the
        subject off-screen on 197 of 792 frames. A second, independently
        written measurement against the field says the opposite: median 0.00
        deg, worst 9.84 deg, never off-screen. Both numbers are correct and the
        first question is the wrong one. Beat 1 is a WEAVE through a field of
        parts; between two presentations the camera is looking at the parts in
        between, which is the film. Nominating one cluster and calling
        everything else a miss measures the model, not the rig — and shipping
        that as a gate would have sent someone to "fix" a camera that is
        working. The per-key nominated-cluster figure is still computed and
        reported, clearly labelled as a DIAGNOSTIC, and it does not gate.
    """

    def __init__(self, sheet, car, world_of_frame, explode=None, anim=None):
        self.sheet = sheet
        self.car = car
        self.W = world_of_frame
        self.aim = sheet.get("aim", {})
        self.b1 = sorted(sheet.get("beat1", {}).get("camera_keys", []),
                         key=lambda k: k["t"])
        self.b6_start = next(b["start_s"] for b in sheet["beats"]
                             if b["name"] == "6_ending")
        # THE FIELD MOVES. Each cluster hangs at bbox_centre + explode_offset
        # until it flies to bbox_centre and seats. A model that uses only the
        # exploded position is stale for the whole back half of the beat, and
        # it reported the camera 9.8 deg from the front wing at frame 648 when
        # the rendered frame at 648 is the glass wall with no part in it. The
        # seat frames come from `world/beat1_anim_anim.json`, which is what the
        # part animation was actually built from.
        self.field = []
        land = {c: v["last_land"] for c, v in (anim or {}).get("clusters", {}).items()}
        self.flight_f = float((anim or {}).get("flight_s", 1.55)) * FPS
        for name, c in (explode or {}).get("clusters", {}).items():
            off = c["explode_offset"]
            fin = Vector([(c["bbox_min"][i] + c["bbox_max"][i]) / 2 for i in range(3)])
            exp = fin + Vector(off)
            rad = max(0.5 * (Vector(c["bbox_max"]) - Vector(c["bbox_min"])).length, 0.05)
            self.field.append((name, exp, fin, rad, land.get(name)))

    def nearest_field(self, f, pos, fwd):
        """(cluster centre, angle to its EDGE) for the cluster the lens is on."""
        best = None
        for name, exp, fin, rad, land in self.field:
            if land is None:
                ctr = exp
            else:
                u = max(0.0, min(1.0, (f - (land - self.flight_f)) / max(self.flight_f, 1.0)))
                ctr = exp.lerp(fin, u * u * (3.0 - 2.0 * u))
            d = ctr - pos
            n = max(d.length, 1e-9)
            a = math.degrees(math.acos(max(-1.0, min(1.0, fwd.dot(d / n)))))
            a = max(0.0, a - math.degrees(math.asin(min(1.0, rad / max(n, rad)))))
            if best is None or a < best[1]:
                best = (ctr, a, name)
        return best

    def nominated(self, f):
        """DIAGNOSTIC ONLY: the cluster the nearest beat-1 key names."""
        t = f / FPS
        pts = [(k["t"], k["look_at"], k.get("focus_target"))
               for k in self.b1 if k.get("look_at")]
        if not pts:
            return None, None
        best = min(pts, key=lambda p: abs(p[0] - t))
        return Vector(best[1]), best[2]

    def _car_point(self, f, z_off):
        p = self.car.pos(self.W[f])
        return Vector((p[0], p[1], p[2] + z_off))

    def at(self, f, beat):
        spec = self.aim.get(beat, {})
        if beat == "1_assembly":
            return None            # handled by nearest_field(), which needs the
            #                        camera's own forward vector
        if beat == "6_ending":
            t = f / FPS - self.b6_start
            zo = spec.get("z_off", 0.80)
            car = self._car_point(f, zo)
            pt = Vector(spec["fixed_point"])
            t0 = spec.get("car_until_t", 4.0)
            t1 = spec.get("point_from_t", 6.0)
            if t <= t0:
                return car
            if t >= t1:
                return pt
            u = (t - t0) / max(t1 - t0, 1e-9)
            u = u * u * (3.0 - 2.0 * u)
            return car.lerp(pt, u)
        return self._car_point(f, spec.get("z_off", 0.80))

    def bound(self, beat):
        return float(self.aim.get(beat, {}).get("bound_deg", 25.0))

    def undeclared(self, sheet):
        """Beats with no aim declaration, and beat 6 with no fixed point.

        UNPROVEN IS A FAIL. A beat whose subject nobody has written down cannot
        be checked, and quietly defaulting to "the car" would let the next
        missing declaration through the same hole the missing camera keys went
        through. What makes it measurable is a `sheet["aim"][<beat>]` entry
        naming the subject and its bound.
        """
        bad = []
        for b in sheet["beats"]:
            spec = self.aim.get(b["name"])
            if not spec or "bound_deg" not in spec:
                bad.append(f'sheet["aim"]["{b["name"]}"] is missing; the gate '
                           f'cannot say what this beat is pointed at')
            elif b["name"] == "6_ending" and "fixed_point" not in spec:
                bad.append('sheet["aim"]["6_ending"]["fixed_point"] is missing; '
                           'the closing wide has no declared subject')
        return bad


def main():
    a = parse_args()
    set_key_defaults()
    sheet = json.load(open(a.sheet))
    spec = json.load(open(a.spec))
    total_frames = int(sheet["total_frames"])

    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.resolution_x, scene.render.resolution_y = a.res
    scene.render.resolution_percentage = 100
    scene.render.use_motion_blur = True
    scene.render.motion_blur_position = "CENTER"

    # ---- the one camera --------------------------------------------------
    #
    # ONE means one. The scene inherits round 1's hero cameras
    # (CAM_FrontQuarter, CAM_RearQuarter, CAM_HeroLow, CAM_TopDown) and they are
    # not just untidy: the render worker PREWARMS EVERY CAMERA IN THE SCENE at
    # load, and `tools/fix_audit_blend.py` records an incident where that cost
    # condemned a healthy instance on the readiness probe. On a 4 GB world it is
    # minutes per camera. They go.
    dropped = [o.name for o in list(scene.objects) if o.type == "CAMERA"]
    for name in dropped:
        ob = bpy.data.objects.get(name)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    for cd in list(bpy.data.cameras):
        if cd.users == 0:
            bpy.data.cameras.remove(cd)
    if dropped:
        print(f">> dropped {len(dropped)} inherited camera(s): {', '.join(dropped)}")

    cam_data = bpy.data.cameras.new("ONER")
    cam = bpy.data.objects.new("ONER", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.sensor_width = 36.0
    cam_data.sensor_fit = "AUTO"
    cam_data.dof.use_dof = True
    cam.rotation_mode = "QUATERNION"

    # ---- THE FAR CLIP.  R2-061, and it put a black band across the last shot.
    #
    # This was never set, so ONER shipped with Blender's factory `clip_end` of
    # 1000.0 m -- against `world/build_sky.py`'s own documented hand-off of
    # >= 50 km for the aerosol slab. In beat 6 the camera climbs to ~124 m and
    # holds for the film's final 11 seconds, and beyond 1 km it was clipping the
    # ground away: 56 FULL-WIDTH ROWS OF PURE BLACK, 7.8 % of the closing frame.
    #
    # It was diagnosed as a terrain-extent problem and it is not. Three proofs:
    #   * an alpha render of f2860 shows rows 136-275 at alpha 0.000 -- NOTHING
    #     IS DRAWN there, not "something dark" -- with the first geometry at row
    #     276. Predicted from a 1 km clip and this camera's height and lens:
    #     row 303.9, against a measured 304 fully-opaque.
    #   * three cameras in ONE scene, same ground, same sky, same exposure:
    #     clip 1 km -> 71 black rows; clip 200 km -> 0; and a mostly-sky control
    #     camera -> 0, so the counter is not merely measuring sky.
    #   * the shipping scene: 56 -> 0 full-width black rows, and zero pixels
    #     below 0.02 anywhere (luminance p01 0.0000 -> 0.2224).
    #
    # The defect was fixed once in a built blend by a repair script. THAT IS NOT
    # ENOUGH: the rig is rebuilt on every telemetry or beat-sheet change, and
    # each rebuild reintroduced the 1 km plane. It belongs here, at the source.
    #
    # 200 km comfortably clears the sky slab; `clip_start` is pulled in to 0.05 m
    # because beat 1 passes within 0.505 m of the car and the default 0.1 m is
    # close enough to matter at a 58 mm lens.
    cam_data.clip_start = 0.05
    cam_data.clip_end = 200000.0

    # ---- the two clocks --------------------------------------------------
    scales, ramp_info = FT.build_time_map(sheet, total_frames)
    for r in ramp_info:
        assert abs(r["achieved_world_s"] - r["declared_world_s"]) < 1e-6, (
            "the beat-3 ramp does not integrate to its declared world duration: "
            f"{r}")
        print(f">> time map: {r['beat']} frames {r['frames']} floor "
              f"{r['solved_floor']:.5f}, world {r['achieved_world_s']:.4f} s "
              f"== declared {r['declared_world_s']} s")
    W = FT.world_time_table(scales, total_frames)
    car = Car(a.telemetry, spec)
    explode = json.load(open(a.explode)) if os.path.exists(a.explode) else {}
    anim = json.load(open(a.beat1anim)) if os.path.exists(a.beat1anim) else {}
    subject = Subject(sheet, car, W, explode, anim)
    print(f">> beat 1's subject: the exploded field, {len(subject.field)} clusters")

    # ---- keys ------------------------------------------------------------
    keys, per_beat, missing, _b6 = load_keys(sheet)
    aim6 = sheet.get("aim", {}).get("6_ending", {})

    undeclared = subject.undeclared(sheet)
    if undeclared:
        for u in undeclared:
            print("   FAIL " + u)
        print(">> STAGE RESULT: CAMERA_RIG_AIM_UNDECLARED")
        sys.exit(1)

    # ---- beat 6: resample its own declared trajectory, and AIM it ---------
    b6_ts, b6_at = beat6_path(sheet, spec)
    b6_f0, b6_f1 = int(round(b6_ts[0] * FPS)), int(round(b6_ts[-1] * FPS))
    declared_f = {int(round(t * FPS)): t for t in b6_ts}

    def b6_bearing(f):
        p, _L = b6_at(f / FPS)
        s = subject.at(f, "6_ending")
        d = Vector(s) - Vector(p)
        return d.normalized() if d.length > 1e-9 else Vector((0, 0, -1))

    # R2-086, and this is the REFINEMENT, not the fix — the fix is deleting the
    # declared-position override below, and it was isolated by building without
    # this block. Bracketing each declared time with the frames either side of
    # it, rather than only its rounded frame, pins the curve on both sides of a
    # point that falls at .4 of a frame. Measured against `beat6_path`'s own
    # analytic curve over f2690-2974, which is the only reference that knows
    # where beat 6 is supposed to be:
    #
    #     override in place          max 1.1251 m   max speed error 9.27 m/s
    #     override removed           max 0.0213 m   max speed error 0.148 m/s
    #     override removed + this    max 0.0047 m   max speed error 0.076 m/s
    #
    # So the override is 98 % of it and this is the last 4.5x, for 6 extra keys
    # in 264 frames. It is kept because it is nearly free and because the same
    # reasoning — a curve is authored by its handle solver wherever its keys are
    # far apart — is what the seam bridge and the hand-off ramp are both for.
    # The film-wide local-accel census is IDENTICAL with and without it, so it
    # is not what closed f2680.
    b6_frames = set(declared_f)
    for t in b6_ts:
        b6_frames.add(max(b6_f0, min(b6_f1, int(math.floor(t * FPS)))))
        b6_frames.add(max(b6_f0, min(b6_f1, int(math.ceil(t * FPS)))))
    f = b6_f0
    while f < b6_f1:
        b0 = b6_bearing(f)
        step = 2
        for cand in range(2, 9):
            g = min(f + cand, b6_f1)
            if math.degrees(math.acos(max(-1.0, min(1.0, b0.dot(b6_bearing(g)))))) > 5.0:
                break
            step = cand
        f = min(f + step, b6_f1)
        b6_frames.add(f)

    # ---- THE BEAT 5 -> BEAT 6 HAND-OFF.  R2-063, and it is a ROUNDING. -----
    #
    # BEAT 6 DOES NOT START ON A FRAME.  Its beat begins at 113.1 s and every one
    # of its eight declared keys is at a whole number of seconds from there, so
    # every one lands at .4 of a frame: 113.1 x 24 = 2714.4.  The block below
    # used to force each declared POSITION onto `round(t * FPS)` and call that
    # "reproduced exactly".  It is not exact; it is 0.4 of a frame of travel
    # early, and at the peel-off the camera is doing 83.1 m/s, so it is
    #
    #     1.385 m of position error placed on frame 2642.
    #
    # MEASURED CONSEQUENCE, on render/film9_path.json via the campath gate:
    #
    #     f2642   88.3 m/s   the camera lurches forward onto the misplaced key
    #     f2643   68.5 m/s   -473 m/s^2 in one frame, and the aim swings 14.5
    #     f2644   63.7 m/s   deg/frame, then 19.1 -- 32 % OF THE FRAME WIDTH IN
    #                        ONE FRAME, a FAIL, the second-worst smear in the film
    #     f2645   78.0 m/s   and the curve climbing back to where it should be
    #     f2646   85.3 m/s
    #
    # The rotation is not a separate defect.  The camera is a few metres off a
    # car it is following, so 1.4 m of position error IS a large aim change; the
    # smear and the speed swing are one event seen twice.
    #
    # AND THE TWO TRAJECTORIES DISAGREE ANYWAY.  Beat 5's last key (f2641) and
    # beat 6's declared peel are 3.6775 m apart across 1.40 frames, which is
    # 63.0 m/s, while beat 5 arrives at 88.2 and beat 6 declares 83.1.  About
    # 1.5 m of the two authored paths simply do not meet.  Neither is this
    # file's to move -- beat 5 comes from tools/author_beats2_5.py and beat 6
    # from docs/circuit_spec.json -- so the disagreement is RECONCILED here,
    # which is what beat6_path() already exists to do.
    #
    # The reconciliation is the same cubic Hermite the rest of this function
    # uses: from beat 5's last key with beat 5's own arrival velocity, to beat
    # 6's curve `HANDOFF_FRAMES` later with beat 6's own velocity there.  Spread
    # over 1.5 s the 1.5 m is a ~1 % speed adjustment instead of a 25 % step.
    # Inside that window the declared-position override is NOT applied, because
    # applying it is the defect.
    #
    # THE LENGTH IS SWEPT, NOT PICKED.  Built and measured with the campath gate
    # at each value:
    #     24 frames   the FAIL is gone; a 14 % rotation WARN is left at 2649-53
    #     36 frames   clean: no FAIL and no WARN anywhere in 2637-2714
    #     48 frames   also clean, and disturbs 12 more frames for nothing
    # so 36 is the shortest length that leaves the region clean.
    HANDOFF_FRAMES = 36

    def _b6_vel(t, dt=1.0 / (FPS * 64)):
        a, _ = b6_at(t - dt)
        b, _ = b6_at(t + dt)
        return (Vector(b) - Vector(a)) / (2.0 * dt)          # m/s

    prev_keys = sorted((k for k in keys if k["t"] * FPS < b6_f0 - 1e-6),
                       key=lambda k: k["t"])
    blend = None
    if len(prev_keys) >= 2:
        k_in, k_before = prev_keys[-1], prev_keys[-2]
        f_in = int(round(k_in["t"] * FPS))
        f_end = min(b6_f0 + HANDOFF_FRAMES, b6_f1)
        if f_end > f_in + 1:
            p_in = Vector(k_in["world"])
            v_in = ((p_in - Vector(k_before["world"]))
                    / max(k_in["t"] - k_before["t"], 1e-9))      # m/s
            p_end = Vector(b6_at(f_end / FPS)[0])
            v_end = _b6_vel(f_end / FPS)
            span = (f_end - f_in) / FPS                          # s

            def blend(f):
                u = (f - f_in) / (f_end - f_in)
                u2, u3 = u * u, u * u * u
                return (p_in * (2 * u3 - 3 * u2 + 1)
                        + v_in * span * (u3 - 2 * u2 + u)
                        + p_end * (-2 * u3 + 3 * u2)
                        + v_end * span * (u3 - u2))
            # SAMPLE ON A RAMP, NOT FLAT OUT.  The first draft keyed every frame
            # of the blend, on the argument that beat 5 arrives on 1-frame keys
            # and Blender's handles must not reintroduce a step.  That fixed the
            # position and BROKE THE ROLL: look_quat() corrects the transported
            # roll toward level by at most 3 deg per FRAME OF KEY GAP, so
            # 1-frame keys give it 3 deg per key, and the camera came out of the
            # top-down follow still 43 deg off a level horizon at f2678 and did
            # not recover until f2694 -- against f2670 on the shipped path. A
            # 43 deg horizon righting itself over 16 frames is a barrel roll,
            # which is the exact defect look_quat's docstring exists to prevent.
            #
            # So the spacing MATCHES beat 5 at the junction and relaxes: 1, 2,
            # 3, ... up to 8 frames. Dense where the handles need it, loose
            # where the roll needs it.
            g, step = f_in, 1
            while g < f_end:
                g = min(g + step, f_end)
                b6_frames.add(g)
                step = min(step + 1, 8)
            print(f">> beat 5 -> beat 6 hand-off: blended over frames "
                  f"{f_in}-{f_end}. Beat 5 arrives at {v_in.length:.1f} m/s; "
                  f"beat 6's curve is at {v_end.length:.1f} m/s there; the "
                  f"declared keys sit at "
                  f"{b6_ts[0] * FPS - int(b6_ts[0] * FPS):.2f} of a frame and "
                  f"their positions are NOT forced onto a rounded frame inside "
                  f"this window.")

    b6_added = 0
    b6_blended = 0
    for f in sorted(b6_frames):
        p, L = b6_at(f / FPS)
        in_blend = blend is not None and f <= f_end
        if in_blend:
            p = list(blend(f))
            b6_blended += 1
        else:
            # R2-086. THE OTHER SIX KEYS. R2-063 established that beat 6's
            # declared keys land at .4 of a frame and that forcing a declared
            # POSITION onto `round(t*FPS)` is 1.4 m of position error at
            # 83 m/s. It then suppressed that only INSIDE the 36-frame hand-off
            # window, and left the branch that does it standing for the other
            # six declared keys — which is every key from t = 112.1 to the end
            # of the film.
            #
            # This is what it cost, on the path built with the branch still in:
            #
            #   f2689  76.29 m/s          f2713  70.78 m/s     each declared key
            #   f2690  72.72   -86 m/s2   f2714  67.56   -77   is a sawtooth: the
            #   f2691  66.44  -151 m/s2   f2715  61.84  -137   camera lurches onto
            #   f2692  61.23  -125 m/s2   f2716  57.06  -115   the misplaced point
            #   f2693  58.04   -77 m/s2   f2717  54.08   -72   and hauls itself back
            #   f2694  56.87   -28 m/s2
            #
            # A +-10 m/s swing about a curve whose own worst acceleration is
            # 6.7 m/s^2, repeated at every declared key, once a second through
            # the closing wide. `beat6_path()`'s analytic curve over the same
            # frames decays 72.3 -> 63.9 m/s at a steady -6 to -7 m/s^2 with no
            # discontinuity anywhere, so the sawtooth is entirely this branch.
            #
            # WHY NO GATE SAW IT, and this is the part worth keeping. The
            # campath gate's C2 kink detector is a robust-z against the MEDIAN
            # |a| of a +-12 frame window — and the sawtooth's period is 24
            # frames, so the window is full of the defect and the median rises
            # to meet it. f2691 scores 3.15x against a bound of 8. The only
            # frame that scores is f2680, at 13.76x, and it scores because it
            # sits at the EDGE of the affected region where the window still
            # contains quiet frames from inside the blend. **A local-median
            # detector is blinded by a periodic defect whose period is shorter
            # than its window; it can only see the first tooth.** C1 saw
            # nothing at all because beat 6's subject is 355 m away, so a metre
            # of camera error is 0.16 deg.
            #
            # THE FIX IS TO DELETE THE BRANCH. `b6_at(f/FPS)` IS the curve
            # through the declared keys — `beat6_path` builds a Hermite with
            # `at(ts[i]) == ps[i]` — so sampling it at whole frames reproduces
            # every declared key AT ITS DECLARED TIME, 0.4 of a frame after the
            # nearest frame, which is where the key actually is. The old branch
            # reproduced it in SPACE at the WRONG TIME, and that is the whole
            # of R2-063 restated. `sheet["beat6"]["keys"]` is untouched, so
            # every other consumer of the declared keys reads what it read
            # before.
            b6_added += 1
        s = subject.at(f, "6_ending")
        keys.append({"t": f / FPS, "beat": "6_ending", "world": p,
                     "look_at": [s.x, s.y, s.z], "lens_mm": L, "fstop": 5.6,
                     "focus_distance_m": max((Vector(s) - Vector(p)).length, 0.1)})
    per_beat["6_ending"] = sum(1 for k in keys if k["beat"] == "6_ending")
    keys.sort(key=lambda k: k["t"])
    print(f">> beat 6: {len(declared_f)} declared keys, {b6_added} intermediate "
          f"samples of its own declared cubic added, {b6_blended} frames taken "
          f"from the beat-5 hand-off blend instead, and rotation supplied for "
          f"all of them")

    # Orientation is solved in ONE ordered pass over every key, before anything
    # is inserted, because `look_quat` carries state from the previous key and
    # inserting in two passes must not be allowed to change what it produces.
    prev_q = prev_v = None
    prev_f = None
    for i, k in enumerate(keys):
        f = max(1, min(total_frames, int(round(k["t"] * FPS))))
        k["_f"] = f
        here = Vector(k["world"])

        # Direction of travel from the neighbouring keys: the roll reference for
        # any near-vertical view. See look_quat().
        pk = Vector(keys[i - 1]["world"]) if i > 0 else here
        nk = Vector(keys[i + 1]["world"]) if i + 1 < len(keys) else here
        travel = nk - pk

        look = k.get("look_at")
        k["_q"] = None
        if look:
            gap = (f - prev_f) if prev_f is not None else 1
            q, prev_v = look_quat(Vector(look) - here, travel, prev_q, prev_v, gap)
            prev_q, prev_f = q, f
            k["_q"] = q

    def insert(sub):
        for k in sub:
            f = k["_f"]
            cam.location = Vector(k["world"])
            cam.keyframe_insert("location", frame=f)
            if k["_q"] is not None:
                cam.rotation_quaternion = k["_q"]
                cam.keyframe_insert("rotation_quaternion", frame=f)
            cam_data.lens = float(k.get("lens_mm", 35.0))
            cam_data.keyframe_insert("lens", frame=f)
            cam_data.dof.aperture_fstop = float(k.get("fstop", 2.8))
            cam_data.dof.keyframe_insert("aperture_fstop", frame=f)
            if k.get("focus_distance_m"):
                cam_data.dof.focus_distance = float(k["focus_distance_m"])
                cam_data.dof.keyframe_insert("focus_distance", frame=f)

    def sample(lo, hi):
        out = []
        for f in range(lo, hi + 1):
            scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            ce = cam.evaluated_get(dg)
            m = ce.matrix_world
            out.append((tuple(m.translation), tuple(m.to_quaternion()),
                        ce.data.lens))
        return out

    def all_curves():
        return fcurves_of(cam) + fcurves_of(cam_data) + fcurves_of(cam_data.dof)

    # ---- THE HANDLE PIN AT FRAME 754.  R2-064, second half. --------------
    #
    # Blender computes a key's AUTO_CLAMPED handle from the two neighbouring
    # KEYS. Beat 1's last key had no key after it for 39 frames; the bridge
    # gives it one 1 frame later, and that alone re-slopes its INCOMING handle
    # and therefore the f718 -> f754 segment. MEASURED, before this pin
    # existed: beat 1 moved by up to 157.14 mm at frame 741, over frames
    # 601-754 — inside the material the review calls the best in the film, and
    # the one thing this work was told not to disturb.
    #
    # So the incoming handle at 754 is captured from a curve built WITHOUT the
    # bridge and written back as FREE afterwards. The OUTGOING handle is left
    # alone deliberately: with the next key one frame away, the segment it
    # governs is evaluated only at its two endpoints, both of which are keys,
    # so it cannot reach the picture.
    #
    # This is not asserted from the API's behaviour — the rig re-samples frames
    # 1-754 on both sides of the insertion and prints the difference, and
    # REFUSES to save if it is not zero.
    #
    # WHAT THIS PIN DOES NOT COVER, and it is worth knowing. R2-065.
    # It holds beat 1 against the BRIDGE. It does not hold beat 1 against beat
    # 2, and beat 2 reaches back into it: re-profiling beat 2's leading keys
    # moves beat 1's frame 740 by 34.35 mm (y and z, x untouched) on a segment
    # whose two keys — 718 and 754 — never change value, because Blender's
    # AUTO_CLAMPED solve at 754 is not a function of its two neighbours alone.
    # ATTRIBUTED, not assumed: building this same code against the pre-R2-064
    # sheet reproduces the old path to 0.0 mm, and building it against the new
    # sheet with the bridge block EMPTIED still shows the 34.35 mm — so it is
    # beat 2's keys, not the bridge, and not the two-pass insertion.
    # `FCurve.update()` is a no-op on both, so it is not a stale-handle effect
    # either.
    #
    # There is no "beat 1 alone" value to pin to: the 718 -> 754 segment
    # depends on what follows 754, and something always does. The practical
    # consequence, stated so it is not discovered by a diff: BEAT 1'S FRAMES
    # ~686-753 MUST BE RE-RENDERED WHENEVER BEAT 2'S LEADING KEYS MOVE. 34 mm
    # at 8 m is 0.246 deg, about 19 px of subject shift at 4K.
    PIN_F = 754
    bridge = [k for k in keys if k.get("beat") == "1_2_seam"]
    rest = [k for k in keys if k.get("beat") != "1_2_seam"]

    # `FCurve.update()` is not called anywhere in here, and it does not need
    # to be. THE FIRST DRAFT OF THIS COMMENT SAID IT DID, and blamed `update()`
    # for the 34.35 mm beat 1 moves by. That was wrong and it was wrong in the
    # way MASTER-PLAN section 6 warns about: the cause was assumed instead of
    # attributed. Running `update()` over the pre-R2-064 rig's curves and
    # re-sampling frames 1-754 moves them by 0.000000 mm — it is a no-op on
    # both sheets, and the 34.35 mm is beat 2's keys (R2-065).
    insert(rest)
    pinned, before = {}, None
    if bridge:
        # EVERY key at or before 754, both handles — not just frame 754's.
        # Pinning only 754 left 20.7 um of position and 1.9e-3 of quaternion at
        # frame 730, because inserting the bridge also moved the handles on the
        # key at frame 718, whose own value never changes either. The segment
        # 718 -> 754 is drawn from 718's RIGHT handle and 754's LEFT handle, so
        # both ends of every beat-1 segment have to be held for the claim
        # "beat 1 is untouched" to be structural rather than approximate.
        for fc in all_curves():
            for kp in fc.keyframe_points:
                f = int(round(kp.co[0]))
                if f <= PIN_F:
                    pinned[(fc.data_path, fc.array_index, f)] = (
                        (float(kp.handle_left[0]), float(kp.handle_left[1])),
                        (float(kp.handle_right[0]), float(kp.handle_right[1])),
                        kp.handle_left_type, kp.handle_right_type)
        before = sample(1, PIN_F)
        insert(bridge)
        for fc in all_curves():
            for kp in fc.keyframe_points:
                f = int(round(kp.co[0]))
                h = pinned.get((fc.data_path, fc.array_index, f))
                if h is None:
                    continue
                hl, hr, tl, tr = h
                kp.handle_left_type = "FREE"
                kp.handle_left = hl
                if f < PIN_F:
                    # 754's RIGHT handle governs only the 754 -> 755 segment,
                    # which is one frame long and therefore evaluated only at
                    # its two endpoints, both of which are keys. It is left to
                    # Blender deliberately: it is the seam, not beat 1.
                    kp.handle_right_type = "FREE"
                    kp.handle_right = hr
        after = sample(1, PIN_F)
        dp, dp_f = max(((Vector(a[0]) - Vector(b[0])).length, i + 1)
                       for i, (a, b) in enumerate(zip(before, after)))
        # COMPONENTWISE, not 2*acos(|q0.q1|). That angle is ill-conditioned at
        # identity: `matrix.to_quaternion()` returns float32 components whose
        # norm is 1 +- 1e-7, so a quaternion dotted with ITSELF gives 0.9999999
        # and the angle reads 0.069 deg. This check reported that as beat 1
        # moving, on frames whose quaternion components are bit-identical.
        dq, dq_f = max((max(abs(x - y) for x, y in zip(a[1], b[1])), i + 1)
                       for i, (a, b) in enumerate(zip(before, after)))
        dl = max(abs(a[2] - b[2]) for a, b in zip(before, after))
        print(f">> seam bridge: {len(bridge)} keys over frames "
              f"{bridge[0]['_f']}-{bridge[-1]['_f']}; the incoming handle at "
              f"frame {PIN_F} is pinned on {len(pinned)} channels")
        print(f">> beat 1 frames 1-{PIN_F} across the insertion: "
              f"{dp * 1e6:.4f} nm (worst f{dp_f}), quaternion "
              f"{dq:.3e} per component (worst f{dq_f}), lens {dl:.3e} mm "
              f"— float32 storage of an F-curve handle is ~1.2e-7 relative")
        if dp > 1e-6 or dq > 1e-6 or dl > 1e-6:
            print("   FAIL adding the seam bridge moved beat 1. The pin did "
                  "not hold and beat 1's f648-792 is the material this project "
                  "is least willing to re-render.")
            print(">> STAGE RESULT: SEAM_BRIDGE_MOVED_BEAT1")
            sys.exit(1)

    # ---- time map + shutter ---------------------------------------------
    #
    # ONE SHUTTER FOR THE WHOLE TAKE. See the docstring: the ramp is already in
    # the animation, so scaling the shutter by it again is a double correction.
    # The `world` mode is kept only so the two can be rendered against each other.
    if a.shutter_mode == "flat":
        scene.render.motion_blur_shutter = a.shutter
        shutter_span = (a.shutter, a.shutter)
    else:
        for f in range(1, total_frames + 1):
            scene.render.motion_blur_shutter = a.shutter * scales[f - 1]
            scene.render.keyframe_insert("motion_blur_shutter", frame=f)
        shutter_span = (a.shutter * min(scales), a.shutter * max(scales))
    print(">> shutter: mode=%s, %.4f-%.4f of a frame (%.1f-%.1f degrees)%s"
          % (a.shutter_mode, shutter_span[0], shutter_span[1],
             360.0 * shutter_span[0], 360.0 * shutter_span[1],
             "" if a.shutter_mode == "flat" else
             "   <-- A/B ONLY, this is the R2-037 double correction"))

    # ---- sample the built rig, every frame -------------------------------
    # The EVALUATED camera, not the authored one: the lens is an animated
    # property and reading it off the original datablock is reading the value
    # the last keyframe_insert happened to leave behind.
    path = []
    for f in range(1, total_frames + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        path.append({"f": f,
                     "p": [round(v, 5) for v in m.translation],
                     "q": [round(v, 6) for v in m.to_quaternion()],
                     "lens": round(ce.data.lens, 4)})

    # ---- exposure: interior -> daylight, ON THE CAMERA -------------------
    #
    # NOT at beat 4's start. The brief hangs the ramp on beat 4 because that is
    # where its own approximate timings put the camera leaving the building; in
    # the beat sheet as built, the camera crosses the glass plane x = +15.0 in
    # the middle of beat 3, 6.4 s of screen time earlier. Keying it to the frame
    # the camera ACTUALLY crosses is the same intent measured against the
    # artefact instead of against the prose.
    glass_x = float(spec["showroom"]["breach_face_centre_world"][0])
    cross_f = None
    for i in range(1, len(path)):
        if path[i - 1]["p"][0] < glass_x <= path[i]["p"][0]:
            cross_f = path[i]["f"]
            break
    if cross_f is None:
        cross_f = int(round(next(b["start_s"] for b in sheet["beats"]
                                 if b["name"] == "4_transit") * FPS))
        print(">> WARNING: the camera never crosses the glass plane; exposure "
              "ramp falls back to beat 4's start")
    # RELATIVE TO THE SCENE'S OWN EXPOSURE, not absolute. The ramp used to key
    # -0.85 -> 0.00, which is only correct if the world happens to be calibrated
    # at 0.00. `render/world/assembly/assembly_render_setup.json` records the
    # assembled circuit calibrated at **-3.628** under AgX, so keying 0.00 was
    # 3.6 stops over — and the first full-world frame rendered through this rig
    # came back washed out, which is how it was found. The DAYLIGHT end of the
    # ramp is now whatever the scene was already set to, and the interior end is
    # that minus the brief's ~1 stop.
    daylight = float(scene.view_settings.exposure)
    interior = daylight - INTERIOR_STOPS
    f0 = max(1, cross_f - 3)
    f1 = min(total_frames, f0 + 15)
    scene.view_settings.exposure = interior
    scene.view_settings.keyframe_insert("exposure", frame=f0)
    scene.view_settings.exposure = daylight
    scene.view_settings.keyframe_insert("exposure", frame=f1)
    print(f">> exposure ramp {interior:+.3f} -> {daylight:+.3f} over frames "
          f"{f0}-{f1} (the scene's own daylight exposure is {daylight:+.3f}; "
          f"camera crosses x={glass_x} at frame {cross_f})")
    # THE RAMP IS A DELTA (R2-027), WHICH MAKES THE INCOMING SCENE'S OWN
    # EXPOSURE PART OF THE ANSWER.  Keying relative to 0.000 is correct when the
    # scene is calibrated at 0.000 and 3.6 stops over when it is not, and
    # nothing said which it was.  world/film_exposure.py is the one place that
    # knows, so the disagreement is reported here in stops rather than
    # discovered in a washed-out frame.
    exposure_note = None
    if FX is not None:
        delta = daylight - FX.FILM_EXPOSURE
        exposure_note = {"scene_daylight": round(daylight, 4),
                         "film_exposure": FX.FILM_EXPOSURE,
                         "delta_stops": round(delta, 4),
                         "calibrated": abs(delta) <= FX.MEASUREMENT_RESOLUTION_STOPS}
        if abs(delta) > FX.MEASUREMENT_RESOLUTION_STOPS:
            print(f"   NOTE: this scene's view exposure is {daylight:+.3f} but "
                  f"the film's measured daylight calibration is "
                  f"{FX.FILM_EXPOSURE:+.3f} — the ramp is therefore keyed "
                  f"{delta:+.3f} stops off the film's grade. That is expected "
                  f"when authoring the rig into an interior scene such as "
                  f"beat1_anim.blend, and a DEFECT in the assembled world, "
                  f"where render_setup2/3 set film_exposure.FILM_EXPOSURE "
                  f"before this runs. Recorded in the continuity report.")

    # ---- GATE 1: every beat has keys, and has ROTATION keys --------------
    #
    # A beat with no camera key is the defect this rebuild exists to fix. A beat
    # with location keys and no rotation key is the SAME defect wearing a
    # disguise: that is exactly what beat 6 was, and it is why the frozen
    # orientation ran to the last frame of the film rather than to frame 2714.
    # Blender 5.x actions are SLOTTED: `action.fcurves` no longer exists and the
    # curves live under layers -> strips -> channelbag(slot). Reading them is
    # what makes this a measurement of the built rig rather than a count of the
    # calls this script made, so it is worth the four lines.
    loc_frames, rot_frames = set(), set()
    for fc in fcurves_of(cam):
        tgt = (loc_frames if fc.data_path == "location" else
               rot_frames if fc.data_path == "rotation_quaternion" else None)
        if tgt is None:
            continue
        for kp in fc.keyframe_points:
            tgt.add(int(round(kp.co[0])))

    coverage, beat_fail = [], []
    bl = sheet["beats"]
    for i, b in enumerate(bl):
        fa = int(round(b["start_s"] * FPS)) + 1
        fb = (int(round(bl[i + 1]["start_s"] * FPS)) if i + 1 < len(bl)
              else total_frames)
        nl = sum(1 for f in loc_frames if fa <= f <= fb)
        nr = sum(1 for f in rot_frames if fa <= f <= fb)
        coverage.append({"beat": b["name"], "frames": [fa, fb],
                         "location_keys": nl, "rotation_keys": nr})
        if nl == 0:
            beat_fail.append(f"{b['name']} has NO location key in {fa}-{fb}")
        if nr == 0:
            beat_fail.append(f"{b['name']} has NO rotation key in {fa}-{fb}")

    # ---- GATE 2: continuity ---------------------------------------------
    worst_jump = worst_rot = 0.0
    worst_jump_f = worst_rot_f = 0
    for i in range(1, len(path)):
        p, pp = Vector(path[i]["p"]), Vector(path[i - 1]["p"])
        d = (p - pp).length
        if d > worst_jump:
            worst_jump, worst_jump_f = d, path[i]["f"]
        r, pr = Quaternion(path[i]["q"]), Quaternion(path[i - 1]["q"])
        ang = math.degrees(2.0 * math.acos(min(1.0, abs(r.dot(pr)))))
        if ang > worst_rot:
            worst_rot, worst_rot_f = ang, path[i]["f"]

    # A oner has no teleports. The camera flies fast — the doppler whip and the
    # 330 km/h follow are legitimately quick — so the threshold is generous, but
    # a genuine cut would be tens of metres in one frame.
    JUMP_LIMIT = 12.0      # m per frame  (~288 m/s, faster than the car)
    ROT_LIMIT = 45.0       # deg per frame

    # ---- GATE 3: AIM -----------------------------------------------------
    #
    # THE GATE THAT DID NOT EXIST. Two measurements per frame, both physical:
    #
    #   angle_deg   between the camera's -Z axis and the direction to the beat's
    #               declared subject. Independent of lens: it says where the
    #               camera is pointed.
    #   u, v        where that subject lands in the frame, in units of the
    #               half-frame, computed from the frame's ACTUAL keyed focal
    #               length and the scene's render aspect. |u| or |v| over 1.0 is
    #               a subject that is off-screen. This is the one that catches a
    #               camera which is nearly pointed at the car through an 85 mm
    #               lens, where "nearly" is still off the edge of the picture.
    #
    # A subject BEHIND the camera fails outright rather than folding to a small
    # angle through the projection, which is how this class of check usually
    # goes quietly wrong.
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    sw = cam_data.sensor_width
    sh = sw * ry / rx
    margin = float(sheet.get("aim", {}).get("frame_margin", 0.92))

    aim_rows = []
    per_beat_worst = {}
    aim_fail = []
    behind = 0
    diag_nominated = {"worst": 0.0, "frame": 0, "cluster": None, "over_25": 0}
    for e in path:
        f = e["f"]
        beat = beat_of_frame(sheet, f)
        q = Quaternion(e["q"])
        pos = Vector(e["p"])
        fwd = (q @ Vector((0.0, 0.0, -1.0))).normalized()

        if beat == "1_assembly":
            if not subject.field:
                continue
            s, ang, _name = subject.nearest_field(f, pos, fwd)
            nom, nom_name = subject.nominated(f)
            if nom is not None:
                dn = nom - pos
                if dn.length > 1e-6:
                    na = math.degrees(math.acos(max(-1.0, min(
                        1.0, fwd.dot(dn.normalized())))))
                    if na > 25.0:
                        diag_nominated["over_25"] += 1
                    if na > diag_nominated["worst"]:
                        diag_nominated.update(worst=na, frame=f, cluster=nom_name)
            d = s - pos
        else:
            s = subject.at(f, beat)
            if s is None:
                continue
            d = s - pos
            if d.length < 1e-6:
                continue
            ang = math.degrees(math.acos(max(-1.0, min(1.0, fwd.dot(
                d.normalized())))))
        if beat == "1_assembly":
            # A VOLUME, not a point. Beat 1's subject is a cluster's bounding
            # sphere and the camera is sometimes inside one, where the centre's
            # projection is meaningless (it reported 296 half-frames while the
            # sphere filled the picture). The containment test is therefore the
            # angle to the sphere's EDGE against the frame's HALF-HEIGHT field
            # of view — the strictest of the frame's two half-angles.
            half_v = math.degrees(math.atan(0.5 * sh / e["lens"]))
            u = v = ang / max(half_v, 1e-6)
        else:
            local = q.inverted() @ d                   # camera space, -Z ahead
            if local.z >= -1e-6:
                behind += 1
                u = v = 9.99
            else:
                u = (local.x / -local.z) / (0.5 * sw / e["lens"])
                v = (local.y / -local.z) / (0.5 * sh / e["lens"])
        w = per_beat_worst.setdefault(beat, {"ang": 0.0, "ang_f": 0,
                                             "off": 0.0, "off_f": 0,
                                             "dist_m": 0.0, "n": 0})
        w["n"] += 1
        if ang > w["ang"]:
            w["ang"], w["ang_f"] = ang, f
        off = max(abs(u), abs(v))
        if off > w["off"]:
            w["off"], w["off_f"] = off, f
        w["dist_m"] = max(w["dist_m"], d.length)
        aim_rows.append((f, beat, round(ang, 3), round(u, 3), round(v, 3),
                         round(d.length, 2)))

    for beat, w in per_beat_worst.items():
        bnd = subject.bound(beat)
        w["bound_deg"] = bnd
        if w["ang"] > bnd:
            aim_fail.append(f"{beat}: worst aim {w['ang']:.2f} deg at frame "
                            f"{w['ang_f']} exceeds its stated bound {bnd:.1f}")
        if w["off"] > margin:
            aim_fail.append(f"{beat}: subject reaches {w['off']:.3f} of the "
                            f"half-frame at frame {w['off_f']} (margin {margin})")
    if behind:
        aim_fail.append(f"the subject is BEHIND the camera on {behind} frames")

    worst_aim = max(((w["ang"], b, w["ang_f"]) for b, w in per_beat_worst.items()),
                    default=(0.0, "-", 0))

    # ---- save ------------------------------------------------------------
    out = os.path.abspath(a.out)
    sys.path.insert(0, os.path.join(R2, "tools"))
    import fix_audit_blend as FA
    FA.save_clean(out)

    base = os.path.splitext(out)[0]
    json.dump({"frames": total_frames, "keys": len(keys),
               "keys_per_beat": per_beat,
               "beats_without_keys": missing,
               "coverage": coverage,
               "worst_position_jump_m": round(worst_jump, 4),
               "worst_jump_frame": worst_jump_f,
               "worst_rotation_step_deg": round(worst_rot, 3),
               "worst_rotation_frame": worst_rot_f,
               "worst_aim_deg": round(worst_aim[0], 3),
               "worst_aim_beat": worst_aim[1],
               "worst_aim_frame": worst_aim[2],
               "aim_per_beat": per_beat_worst,
               "aim_frame_margin": margin,
               "beat1_nominated_cluster_diagnostic": diag_nominated,
               "resolution": [rx, ry],
               "jump_limit_m": JUMP_LIMIT, "rot_limit_deg": ROT_LIMIT,
               "time_map": ramp_info,
               "exposure_ramp_frames": [f0, f1],
               "exposure_calibration": exposure_note,
               "shutter_mode": a.shutter_mode,
               "shutter_frames": list(shutter_span),
               "shutter_degrees": [round(360.0 * shutter_span[0], 2),
                                   round(360.0 * shutter_span[1], 2)],
               "blend": out},
              open(base + "_continuity.json", "w"), indent=1)
    json.dump({"frames": total_frames, "path": path},
              open(base + "_path.json", "w"))

    # ---- report ----------------------------------------------------------
    print(f">> ONER camera: {len(keys)} keys over {total_frames} frames "
          f"({total_frames / FPS:.1f} s) at {rx}x{ry}")
    for c in coverage:
        print(f"     {c['beat']:<12} frames {c['frames'][0]:5d}-{c['frames'][1]:5d}"
              f"   {c['location_keys']:4d} loc   {c['rotation_keys']:4d} rot")
    print(f">> worst position jump  {worst_jump:8.3f} m at frame {worst_jump_f} "
          f"(limit {JUMP_LIMIT})")
    print(f">> worst rotation step  {worst_rot:8.3f} deg at frame {worst_rot_f} "
          f"(limit {ROT_LIMIT})")
    print(">> AIM GATE — angle from the camera's -Z to the beat's declared subject")
    for b in [x["name"] for x in sheet["beats"]]:
        w = per_beat_worst.get(b)
        if not w:
            print(f"     {b:<12}  NOT MEASURED")
            continue
        print(f"     {b:<12}  worst {w['ang']:7.2f} deg at frame {w['ang_f']:5d}"
              f"  (bound {w['bound_deg']:5.1f})   frame-offset {w['off']:5.3f}"
              f"  max subject range {w['dist_m']:8.1f} m")
    print(f">> worst aim anywhere   {worst_aim[0]:8.3f} deg at frame "
          f"{worst_aim[2]} ({worst_aim[1]})")
    print(f">> DIAGNOSTIC, NOT A GATE — beat 1 against the single cluster its "
          f"nearest key nominates: worst {diag_nominated['worst']:.2f} deg at "
          f"frame {diag_nominated['frame']} ({diag_nominated['cluster']}), "
          f"{diag_nominated['over_25']} frames over 25 deg. That model is "
          f"REJECTED: beat 1 is a weave THROUGH the field and between two "
          f"presentations the lens is on the parts in between. It is printed "
          f"only so nobody re-derives it and 'fixes' a camera that is working.")
    print(">> per-beat verdict:")
    for b in [x["name"] for x in sheet["beats"]]:
        w = per_beat_worst.get(b)
        bad = [x for x in aim_fail if x.startswith(b + ":")]
        print(f"     {b:<12}  {'FAIL' if bad else 'PASS'}"
              + ("   " + bad[0].split(": ", 1)[1] if bad else ""))
    print(f">> saved {out}")

    fails = beat_fail + aim_fail
    if worst_jump > JUMP_LIMIT:
        fails.append(f"position jump {worst_jump:.3f} m at frame {worst_jump_f}")
    if worst_rot > ROT_LIMIT:
        fails.append(f"rotation step {worst_rot:.3f} deg at frame {worst_rot_f}")
    if missing:
        fails.append("beats with no camera keys at all: " + ", ".join(missing))
    if fails:
        for x in fails:
            print("   FAIL " + x)
        print(">> STAGE RESULT: CAMERA_RIG_FAIL")
    else:
        print(">> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED")


if __name__ == "__main__":
    main()
