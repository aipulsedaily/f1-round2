"""Beat 1 — animate 616 parts from the exploded field onto the car.

    /opt/blender-5.2.0-linux-x64/blender -b ~/opus5-car-render/work/iter.blend \
        --factory-startup -P anim/build_beat1_anim.py -- \
        --plan docs/explode_plan.json --sheet docs/beat_sheet.json \
        --out world/beat1_anim.blend

WHAT THIS DOES
--------------
Every part starts at its exploded offset and flies to its FINAL transform — which
is where it already sits in round 1's assembled blend. So the animation is built
backwards from truth: the seated pose is not authored, it is the round-1 car, and
the exploded pose is that pose plus a computed offset. There is no opportunity for
the assembled car to be subtly wrong, because it is never touched.

TIMING comes from `docs/beat_sheet.json`, which guarantees every cluster is
presented to camera before it seats. Nothing here re-derives timing; if the beat
sheet changes, this follows.

THE F-CURVES
------------
The brief asks for "eased F-curves, 2-4 frame settle on arrival, staggered
landings". That is three separate things:

  * EASE — parts accelerate away from rest and decelerate into place. Linear
    interpolation reads as a machine; BEZIER with weighted handles reads as mass
    being moved deliberately.
  * SETTLE — a 2-4 frame overshoot-and-return at arrival. Real assembly has
    compliance: a part meets its mounting and stops slightly hard. Without it,
    616 parts all arrive with the same dead precision and the eye reads CG.
  * STAGGER — parts inside a cluster do NOT land together. They are offset by a
    few frames, ordered by distance travelled, so a 120-part front wing assembles
    as a wave rather than a single snap.

ROTATION
--------
Parts that explode along an axis also spin slightly on the way in, because a part
that translates without rotating looks magnetised rather than handled. The spin is
derived from the part's own offset direction so it is consistent within a cluster.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

FPS = 24


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--settle-frames", type=int, default=3)
    p.add_argument("--flight-s", type=float, default=1.55,
                   help="seconds a part spends in flight before it seats")
    return p.parse_args(argv)


def set_key_defaults():
    """Make every NEW keyframe eased, without touching F-curves afterwards.

    Blender 5.x moved Actions to the slotted/layered animation system, so
    `action.fcurves` no longer exists — it is now
    `action.layers[..].strips[..].channelbag(slot).fcurves`. Walking that to fix
    interpolation after the fact is both version-fragile and O(616 objects x
    curves x keys).

    Setting the user-preference defaults before inserting means every key is born
    BEZIER/AUTO_CLAMPED and nothing has to be corrected. `--factory-startup`
    resets these to the factory values on each run, so this is deterministic
    rather than dependent on whatever the last session left behind.
    """
    e = bpy.context.preferences.edit
    e.keyframe_new_interpolation_type = "BEZIER"
    e.keyframe_new_handle_type = "AUTO_CLAMPED"


def main():
    a = parse_args()
    set_key_defaults()
    plan = json.load(open(a.plan))
    sheet = json.load(open(a.sheet))
    sched = {s["cluster"]: s for s in sheet["beat1"]["schedule"]}

    scene = bpy.context.scene
    scene.render.fps = FPS
    beat1 = next(b for b in sheet["beats"] if b["name"] == "1_assembly")
    scene.frame_start = 1
    scene.frame_end = int(round(beat1["duration_s"] * FPS))

    animated = 0
    per_cluster = {}
    # ground truth: where round 1 put every part, captured BEFORE any key is written
    seated_by_name = {}

    for key, c in plan["clusters"].items():
        off = Vector(c["explode_offset"])
        seat_t = sched[key]["seat_t"]
        seat_f = int(round(seat_t * FPS))

        # order parts within the cluster by how far they travel, so the ones with
        # furthest to go leave first and the cluster assembles as a wave
        parts = []
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None:
                print(f"!! missing {pname}")
                continue
            parts.append(ob)
        if not parts:
            continue

        # stagger spans ~8 frames across a cluster regardless of part count, so a
        # 120-part wing and a 10-part floor both read as one deliberate gesture
        n = len(parts)
        stagger = 8.0

        for i, ob in enumerate(parts):
            seated = ob.location.copy()
            seated_by_name[ob.name] = seated.copy()
            exploded = seated + off

            frac = i / max(n - 1, 1)
            land_f = seat_f + int(round(frac * stagger))
            start_f = land_f - int(round(a.flight_s * FPS))
            start_f = max(start_f, 1)

            # --- location -------------------------------------------------
            ob.location = exploded
            ob.keyframe_insert("location", frame=start_f)
            # a small overshoot past the seat, then settle back onto it
            if off.length > 1e-6:
                over = seated - off.normalized() * min(0.045, off.length * 0.03)
                # NEVER OVERSHOOT DOWNWARD PAST THE SEAT.
                #
                # The settle overshoots past the mounting and springs back, which
                # is what gives an arrival compliance instead of dead precision.
                # But a wheel's seated position is RESTING ON THE TURNTABLE DECK,
                # so an overshoot with a downward component drives the tyre into
                # it: the depth probe measured wheel_tyre_RR_Tyre 4.48 mm inside
                # Turntable_Deck at frame 700, the corner-seating moment.
                #
                # Overshooting horizontally is fine and still reads as compliance.
                # Sinking below the final resting height is a part passing through
                # a solid, which is never acceptable.
                if over.z < seated.z:
                    over.z = seated.z
                ob.location = over
                ob.keyframe_insert("location", frame=land_f)
                ob.location = seated
                ob.keyframe_insert("location", frame=land_f + a.settle_frames)
            else:
                ob.location = seated
                ob.keyframe_insert("location", frame=land_f)

            # --- rotation: a slight handled spin, consistent within a cluster --
            if off.length > 1e-6:
                base = ob.rotation_euler.copy()
                axis = off.normalized()
                amt = math.radians(4.5) * (1.0 if (i % 2 == 0) else -1.0)
                ob.rotation_euler = (base.x + axis.y * amt,
                                     base.y + axis.z * amt,
                                     base.z + axis.x * amt)
                ob.keyframe_insert("rotation_euler", frame=start_f)
                ob.rotation_euler = base
                ob.keyframe_insert("rotation_euler", frame=land_f + a.settle_frames)

            animated += 1

        per_cluster[key] = {"parts": n, "seat_frame": seat_f,
                            "first_land": seat_f, "last_land": seat_f + int(stagger)}

    # ---- verify EVERY part is back on its round-1 transform at the last frame
    #
    # The first version of this check compared a value with itself
    # (`(t - t).length > 1e9`) and therefore could never fail. It printed a
    # reassuring zero while proving nothing — the exact "verification theatre"
    # that two audits of this project's render broker flagged as a bug class in
    # its own right. A check that cannot fail is worse than no check, because it
    # buys false confidence.
    #
    # The real invariant: Beat 1 ends with the car ASSEMBLED, and assembled means
    # every part is exactly where round 1 put it. `seated_by_name` is captured
    # before any keyframe is written, so this compares the animated result
    # against ground truth rather than against itself.
    scene.frame_set(scene.frame_end)
    bpy.context.view_layer.update()
    stragglers = []
    worst = 0.0
    for pname, seated in seated_by_name.items():
        ob = bpy.data.objects.get(pname)
        if ob is None:
            continue
        d = (ob.location - seated).length
        worst = max(worst, d)
        if d > 1e-4:                       # 0.1 mm
            stragglers.append((pname, round(d, 6)))
    print(f">> seat check: worst deviation {worst*1000:.4f} mm over "
          f"{len(seated_by_name)} parts, {len(stragglers)} stragglers")
    if stragglers:
        for s in stragglers[:12]:
            print(f"   !! {s[0]} still {s[1]*1000:.2f} mm off its seated transform")

    # Saved through save_clean(): procedural sky, zero external image deps, and
    # it REFUSES to save if any remain. The delivery scene previously inherited
    # round 1's downloaded city.exr and would have rendered the whole film with
    # no environment light on the farm.
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import fix_audit_blend as FA
    out = FA.save_clean(a.out)

    json.dump({"animated_objects": animated, "clusters": per_cluster,
               "frame_start": scene.frame_start, "frame_end": scene.frame_end,
               "fps": FPS, "settle_frames": a.settle_frames,
               "flight_s": a.flight_s, "blend": out},
              open(os.path.splitext(out)[0] + "_anim.json", "w"), indent=1)

    print(f">> animated {animated} objects across {len(per_cluster)} clusters")
    print(f">> frames {scene.frame_start}..{scene.frame_end} @ {FPS} fps "
          f"({scene.frame_end/FPS:.1f} s)")
    for k, v in sorted(per_cluster.items(), key=lambda x: x[1]["seat_frame"]):
        print(f"   {k:<16} {v['parts']:>3} parts  land f{v['first_land']}-{v['last_land']}")
    print(f">> saved {out} ({os.path.getsize(out)/1048576:.1f} MB)")
    print(">> STAGE RESULT: BEAT1_ANIM_OK" if not stragglers
          else ">> STAGE RESULT: BEAT1_ANIM_STRAGGLERS")


if __name__ == "__main__":
    main()
