"""BEATS 2-6 — the car itself, keyed. The other 73 % of the film.

    /opt/blender-5.2.0-linux-x64/blender -b world/beat1_anim.blend \
        --factory-startup -P anim/build_car_anim.py -- \
        --out world/car_anim.blend

WHAT WAS MISSING
----------------
`world/beat1_anim.blend` animates 616 parts over frames 1-792 and stops. The
camera flies all 2,978 frames and the audio is doppler-solved from the same
telemetry, but between frame 793 and frame 2,978 — **2,186 frames, 73 % of the
film** — nothing put the car anywhere. Beat 2 (the launch), beat 4 (the transit),
beat 5 (the flying lap) and beat 6 (the ending) had a camera tracking an object
that was not there.

WHAT IS ANIMATED, AND WHAT IS DELIBERATELY NOT
-----------------------------------------------
`CAR_ROOT` already exists: an empty at (0, 0, 0.340) with all 616 car meshes
parented to it, carrying round 1's ride height. It is the whole car's handle and
it is keyed here with six channels — location and an XYZ Euler — so the car moves
as the rigid body it is. **Beat 1 is untouched by this**: its 616 per-part
F-curves are in CAR_ROOT's LOCAL space and CAR_ROOT holds its rest pose for every
one of frames 1-792, so the assembly plays exactly as it did.

The wheels need two more degrees of freedom each, so this build inserts eight
empties — `CARRIG_STEER_<C>` and `CARRIG_SPIN_<C>` per corner — at the four
measured wheel centres, and REPARENTS the rotating and steering parts onto them
with a compensating `matrix_parent_inverse`. That compensation is the point: it
makes the reparenting a no-op at rest, so beat 1's flight paths for those same
parts are bit-identical afterwards. The build asserts that on all 632 objects
against matrices captured BEFORE anything is touched, and refuses to save if one
of them moved.

NOT ANIMATED, AND NAMED SO THE OMISSION IS A DECISION:

  * THE STEERING WHEEL. `SW_` is 65 parts on a raked column whose axis is not
    measured anywhere in this project. Beats 2-6 are all exterior — the tightest
    lens on the cockpit is 32 mm from 3 m, through the halo — so a wrong column
    axis would be a worse defect than a still wheel. Beat 1 presents it in
    close-up and beat 1 does not move it either.
  * THE FRONT WISHBONES. `suspension_front_*` stays on CAR_ROOT while the upright
    steers. Real wishbone ball joints sit on the steering axis, so at this car's
    7.33 deg of lock the outboard ends move by millimetres.
  * SUSPENSION LINKAGE. The wheels DO take suspension travel — the body's
    dive-squat and lean move relative to them, up to 55 mm, and `anim/carrig.py`
    solves each hub's height so the tyre stays on the road. What is not modelled
    is the linkage that would have to move with it: the wishbones stay on the
    chassis. At an F1 wishbone's geometry that shows as millimetres at the
    outboard ball joint, mostly behind the wheel and the brake drum, and the
    alternative — a tyre hovering 55 mm above its own shadow under braking — is
    the most visible defect a car animation has.

BEAT 3 IS SOMEBODY ELSE'S JOB AND THIS DOES NOT PRE-EMPT IT
-----------------------------------------------------------
The destruction sim is a separate, larger piece of work. Frames 865-1056 are
authored here as ONE CONTINUOUS RIGID MOTION straight through the glass — the
car does not react to the impact, shed a part, or deviate by a millimetre — for
two reasons. Continuous motion is what a sim layers ON TOP of: an author who
guessed at the impact response would have to be undone first. And the alternative
is a hole, which is what this file exists to close.

ASSUMED, for whoever picks beat 3 up:

  * the car's rigid path through the aperture is the telemetry's, unmodified;
  * `wheel_rot_rad` continues in rolling contact across the breach — no lock-up,
    no spin-up on impact;
  * the body does not yaw, pitch or roll in response to the glass. The only
    attitude in frames 865-1056 is the telemetry's own dive/squat plus the road.

THE KEYS ARE PER-FRAME AND LINEAR, ON PURPOSE
----------------------------------------------
2,978 keys per channel, interpolation LINEAR. The car is not a performance to be
edited; it is a solved trajectory, and the only honest way to key a solved
trajectory is to sample it. BEZIER with automatic handles would put overshoot
between samples that the solve does not contain — and Cycles reads the F-curves
at sub-frame times for motion blur, so that overshoot would land in the picture
rather than staying in the graph editor.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

_R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R2, "anim"))
sys.path.insert(0, os.path.join(_R2, "tools"))
import carrig as CR                                                # noqa: E402

FPS_HZ = 24


# --------------------------------------------------------------- the corners --
# Which parts turn with the wheel, which turn with the steering, and which do
# neither. Classified by what the part IS on a real car, not by prefix:
#
#   SPINS   the tyre, the rim and everything bolted to it, plus the rotating half
#           of the brake — disc, its vanes, the bell that carries it, the hub it
#           runs on and the retaining nut.
#   STEERS  the rest of the corner's brake assembly: the caliper and its pads and
#           pistons, the brake lines, the aero drum and its ducting, the shield
#           and the upright. All of it is mounted to the upright, so all of it
#           steers and none of it spins.
#
# The 2022-generation aero DRUM is upright-mounted and stationary; the wheel COVER
# is rimmed-mounted and rotates. They are different parts and they are on
# different sides of this line.
BRAKE_SPINS = ("_Bell", "_Disc", "_DiscVanes", "_Hub", "_Nut")


def part_role(name, corner):
    """'spin', 'steer' or None for a part of `corner`."""
    if name.startswith("wheel_tyre_%s_" % corner):
        return "spin"
    if name.startswith("brake_assembly_%s_" % corner):
        tail = name[len("brake_assembly_%s" % corner):]
        return "spin" if tail in BRAKE_SPINS else "steer"
    return None


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", default=os.path.join(_R2, "docs/beat_sheet.json"))
    p.add_argument("--telemetry",
                   default=os.path.join(_R2, "telemetry/telemetry.csv"))
    p.add_argument("--spec", default=os.path.join(_R2, "docs/circuit_spec.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def set_key_defaults():
    """Born LINEAR. Blender 5.x's slotted actions make post-hoc fixing fragile."""
    e = bpy.context.preferences.edit
    e.keyframe_new_interpolation_type = "LINEAR"
    e.keyframe_new_handle_type = "VECTOR"


def main():
    a = parse_args()
    set_key_defaults()
    spec = json.load(open(a.spec))
    sheet = json.load(open(a.sheet))
    total = int(sheet["total_frames"])

    scene = bpy.context.scene
    scene.render.fps = FPS_HZ
    scene.frame_start = 1
    scene.frame_end = total

    root = bpy.data.objects.get("CAR_ROOT")
    if root is None:
        raise SystemExit("no CAR_ROOT in this blend — wrong input file")
    if root.animation_data and root.animation_data.action:
        raise SystemExit("CAR_ROOT is already animated; refusing to key it twice")

    rig = CR.CarRig(a.telemetry, spec)
    W, ramp_info, _ = CR.world_time_table(a.sheet, total)
    for r in ramp_info:
        assert abs(r["achieved_world_s"] - r["declared_world_s"]) < 1e-6, r
    print(">> time map: ramp %s frames %s, floor %.5f, world %.4f s == %s"
          % (ramp_info[0]["beat"], ramp_info[0]["frames"],
             ramp_info[0]["solved_floor"], ramp_info[0]["achieved_world_s"],
             ramp_info[0]["declared_world_s"]))

    # ---- ground truth, captured BEFORE anything is touched ---------------
    # Not the objects' own transforms compared with themselves later: copies,
    # taken now. A check that compares a value with itself is the failure mode
    # `build_beat1_anim.py` already shipped once.
    scene.frame_set(792)
    bpy.context.view_layer.update()
    before = {o.name: o.matrix_world.copy() for o in bpy.data.objects}

    # ---- the Vitrines must NOT be part of the car ------------------------
    # 16 display-case clones in PROPS are parented to CAR_ROOT. They share mesh
    # datablocks with real car parts, which is why they ended up there, and they
    # are furniture bolted to the showroom floor. Animating CAR_ROOT without
    # this would fly a vitrine full of brake discs round the circuit at 330 km/h.
    vitrines = [o for o in root.children if o.name.startswith("Vitrine_")]
    for o in vitrines:
        w = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = w
    print(">> unparented %d Vitrine_* clones from CAR_ROOT (they are showroom "
          "furniture, not car parts)" % len(vitrines))

    # ---- the eight hub empties -------------------------------------------
    #
    # Linked into the CAR collection, NOT the scene collection. `CAR` is the
    # unit the film scene appends — 616 meshes and CAR_ROOT — and a collection
    # that does not contain the parents of its own members is a collection that
    # appends into a broken car. Nothing in this project has appended it yet, so
    # nothing would have caught it.
    car_col = bpy.data.collections.get("CAR")
    if car_col is None or root.name not in car_col.objects:
        raise SystemExit("CAR_ROOT is not in a collection named CAR — the hub "
                         "empties would not travel with the car when it is "
                         "appended into the film scene")
    hubs = {}
    for corner, ax, hy, is_front in CR.CORNERS:
        off = Vector((ax, hy, CR.WHEEL_CENTRE_Z_LOCAL))
        steer = bpy.data.objects.new("CARRIG_STEER_%s" % corner, None)
        steer.empty_display_type = "PLAIN_AXES"
        steer.empty_display_size = 0.25
        car_col.objects.link(steer)
        steer.parent = root
        steer.location = off
        steer.rotation_mode = "XYZ"

        spin = bpy.data.objects.new("CARRIG_SPIN_%s" % corner, None)
        spin.empty_display_type = "PLAIN_AXES"
        spin.empty_display_size = 0.20
        car_col.objects.link(spin)
        spin.parent = steer
        spin.location = Vector((0.0, 0.0, 0.0))
        spin.rotation_mode = "XYZ"

        hubs[corner] = {"steer": steer, "spin": spin, "off": off,
                        "front": is_front}

    bpy.context.view_layer.update()

    # ---- reparent, with the compensation that makes it a no-op at rest ----
    #
    #   world_old = ROOT_w . PINV_old . basis
    #   world_new = ROOT_w . HUB_local . PINV_new . basis
    #   =>  PINV_new = HUB_local^-1 . PINV_old
    #
    # written in the general form even though PINV_old is identity on this blend,
    # because a general form cannot be silently invalidated by a future reparent.
    moved = {"spin": 0, "steer": 0}
    for corner, _ax, _hy, is_front in CR.CORNERS:
        h = hubs[corner]
        # SPIN's local matrix is relative to STEER; the composite from CAR_ROOT
        # is what the compensation has to invert.
        composite = {"spin": h["steer"].matrix_local @ h["spin"].matrix_local,
                     "steer": h["steer"].matrix_local}
        for ob in list(root.children):
            role = part_role(ob.name, corner)
            if role is None:
                continue
            if role == "steer" and not is_front:
                continue           # a rear upright neither spins nor steers
            pinv_old = ob.matrix_parent_inverse.copy()
            ob.parent = h[role]
            ob.matrix_parent_inverse = composite[role].inverted() @ pinv_old
            moved[role] += 1
    bpy.context.view_layer.update()
    print(">> reparented %d parts onto the spin hubs and %d onto the steer hubs"
          % (moved["spin"], moved["steer"]))

    # ---- PROVE the reparent moved nothing --------------------------------
    scene.frame_set(792)
    bpy.context.view_layer.update()
    worst, worst_name = 0.0, None
    for name, m0 in before.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        d = max((ob.matrix_world[r][c] - m0[r][c]) for r in range(4)
                for c in range(4))
        d = max(abs(d), max(abs(ob.matrix_world[r][c] - m0[r][c])
                            for r in range(4) for c in range(4)))
        if d > worst:
            worst, worst_name = d, name
    print(">> reparent invariance: worst matrix element moved %.3e (%s), over "
          "%d objects at frame 792" % (worst, worst_name, len(before)))
    if worst > 1e-6:
        raise SystemExit("REFUSING TO SAVE: reparenting moved %s by %.3e. The "
                         "matrix_parent_inverse compensation is wrong and beat "
                         "1 would no longer assemble to round 1's pose."
                         % (worst_name, worst))

    if a.dry_run:
        print(">> dry run: nothing keyed, nothing saved")
        return

    # ---- key everything ---------------------------------------------------
    t0 = time.time()
    root.rotation_mode = "XYZ"
    times = [max(W[f], 0.0) for f in range(1, total + 1)]
    poses = rig.pose_series(times)
    samples = []
    for f, (wt, p) in enumerate(zip(times, poses), start=1):
        root.location = Vector(p["loc"])
        root.rotation_euler = p["rot"]
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        for corner, _ax, _hy, _is_front in CR.CORNERS:
            h = hubs[corner]
            hp = p["hubs"][corner]
            h["steer"].location = Vector(hp["loc"])
            h["steer"].rotation_euler = hp["rot"]
            h["steer"].keyframe_insert("location", frame=f)
            h["steer"].keyframe_insert("rotation_euler", frame=f)
            h["spin"].rotation_euler = (0.0, p["spin"], 0.0)
            h["spin"].keyframe_insert("rotation_euler", frame=f)
        samples.append({"f": f, "wt": round(wt, 6),
                        "loc": [round(v, 6) for v in p["loc"]],
                        "rot": [round(v, 8) for v in p["rot"]],
                        "spin": round(p["spin"], 6),
                        "steer": round(p["steer"], 8),
                        "speed": round(p["speed"], 5),
                        "ground_m": round(p["ground_m"], 6),
                        "contacts": {k: round(v, 6)
                                     for k, v in p["contacts"].items()},
                        "spinflag": rig.wheelspin_flag(wt)})
    print(">> keyed %d frames on CAR_ROOT and 8 hub empties in %.1f s"
          % (total, time.time() - t0))

    # ---- LINEAR, set explicitly and then PROVED by evaluation --------------
    #
    # `preferences.edit.keyframe_new_interpolation_type = "LINEAR"` is NOT
    # honoured by `keyframe_insert` in Blender 5.2: the first run of this build
    # set it and measured 71,472 of 71,472 keys still BEZIER. So every key is set
    # explicitly.
    #
    # Setting a flag and then reading the same flag back proves nothing — it is
    # the check-that-cannot-fail this project has already shipped once. What is
    # asserted instead is the PROPERTY the flag is wanted for: the curve
    # evaluated half way between two keys must equal the mean of them. That is
    # what Cycles samples for motion blur, and a bezier handle fails it.
    curves = []
    for ob in [root] + [h[k] for h in hubs.values() for k in ("spin", "steer")]:
        ad = ob.animation_data
        if not (ad and ad.action):
            continue
        for layer in ad.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves += list(bag.fcurves)
    probes = [f + 0.5 for f in range(2, total, max(total // 400, 1))]

    def worst_midpoint_error():
        w, where = 0.0, None
        for fc in curves:
            span = max(abs(kp.co[1]) for kp in fc.keyframe_points) or 1.0
            for t in probes:
                f0, f1 = int(math.floor(t)), int(math.ceil(t))
                want = 0.5 * (fc.evaluate(f0) + fc.evaluate(f1))
                e = abs(fc.evaluate(t) - want) / span
                if e > w:
                    w, where = e, (fc.data_path, fc.array_index, t)
        return w, where

    # NEGATIVE-TO-POSITIVE CONTROL: the same probe, on the curves as inserted.
    # If this reads ~0 the probe cannot tell bezier from linear and the assertion
    # below would be theatre.
    before_mid, before_where = worst_midpoint_error()

    nkeys = 0
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
            kp.handle_left_type = kp.handle_right_type = "VECTOR"
            nkeys += 1
        fc.update()

    worst_mid, worst_where = worst_midpoint_error()
    print(">> %d keys on %d curves; worst mid-frame departure from linear: "
          "as inserted %.3e (%s) -> after setting LINEAR %.3e (%s)"
          % (nkeys, len(curves), before_mid, before_where, worst_mid,
             worst_where))
    if before_mid < 1e-4:
        raise SystemExit("REFUSING TO SAVE: the linearity probe reads %.3e on "
                         "the curves as Blender inserted them, so it cannot "
                         "distinguish bezier from linear and proves nothing."
                         % before_mid)
    if worst_mid > 1e-6:
        raise SystemExit("REFUSING TO SAVE: the F-curves do not interpolate "
                         "linearly between keys (worst %.3e at %s). On a "
                         "per-frame bake that is overshoot the solve does not "
                         "contain, and Cycles samples it for motion blur."
                         % (worst_mid, worst_where))

    import fix_audit_blend as FA
    out = FA.save_clean(a.out)

    side = os.path.splitext(out)[0] + "_car.json"
    json.dump({"blend": out,
               "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "frames": [1, total], "fps": FPS_HZ,
               "telemetry": a.telemetry, "sheet": a.sheet,
               "wheel_radius_m": CR.WHEEL_RADIUS_M,
               "wheelbase_m": CR.WHEELBASE_M,
               "spin_parts": moved["spin"], "steer_parts": moved["steer"],
               "vitrines_unparented": [o.name for o in vitrines],
               "slip_declared_total_rad": rig.slip_declared_total,
               "ground_distance_m": rig.ground_distance(W[total]),
               "samples": samples},
              open(side, "w"))
    print(">> wrote %s (%.1f MB) and %s"
          % (out, os.path.getsize(out) / 1048576.0,
             os.path.relpath(side, _R2)))
    print(">> STAGE RESULT: CAR_ANIM_BUILT")


if __name__ == "__main__":
    main()
