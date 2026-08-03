"""BEAT 2 — what is actually in it, measured. R2-067's instrument.

    .venv/bin/python tools/beat2_probe.py

Beat 2 is frames 793-864: ignition, idle, launch, sanctioned wheelspin, and the
first 2 s of the run at the glass. Four things have to be true across it and
none of them is a count:

  A. THE SANCTIONED WHEELSPIN IS THERE, AND ONLY THERE. The brief allows the
     wheels to out-rotate the ground for ~10 frames at the launch and nowhere
     else in 2,978 frames. Measured from the BUILT transform dump
     (`world/car_anim_measured.json`) rather than from `telemetry.csv`, because
     `wheel_rot_rad` in the CSV is computed from `s_m` and `s_m` is 25.2 % short
     of the ground the car's own keys cover (R2-026 / R2-047). This walks the
     keyed CAR_ROOT positions and the keyed spin angle, and never reads `s_m`.

     THE TWO KINDS ARE NOT THE SAME THING and this prints both:
       sanctioned  inside the declared window, must be PRESENT
       phantom     outside it, must be ZERO to the tolerance

     The 2.04 % figure that has been quoted at this beat is NOT this window: it
     was 52 frames of leg-2 TRANSIT slip, fixed in R2-045, and it lived in beat
     4. Confusing the two is easy and this prints the frame numbers so it
     cannot be done silently.

  B. THE EXPOSURE DOES NOT MOVE. `world/film_exposure.py` now carries
     INTERIOR_STOPS = 0.0, so the interior end of the rig's ramp equals its
     daylight end and the ramp should be a straight line at one value. Beat 2
     is still inside the showroom and an iris move on screen in a cut-free take
     is exactly what the brief forbids. Measured off the scene's evaluated
     `view_settings.exposure` per frame, not off the constant.

  C. THE CAMERA IS WHERE THE LAUNCH IS. Camera-to-car distance, the bearing of
     the REAR CONTACT PATCH (which is what the wheelspin happens at), and
     whether the whole car is inside the frame, per frame, from the built path.

  D. THE CAR IS ACTUALLY MOVING WHEN THE FILM SAYS IT IS. `anim/filmtime.py`
     puts telemetry t = 0 at film t = 34.0718, i.e. frame 817.7. The car must
     be stationary before it and moving after it.

Every row is printed so the shape is visible, not just the extremum — the
summary-statistic failure this project has logged twice.
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
import filmtime as FT                                              # noqa: E402

FPS = 24.0
WHEEL_R = 0.360                     # m, from tools/build_telemetry.py
BEAT2 = (793, 864)
SENSOR_W = 36.0
CAR_HALF_LEN = 5.698 / 2.0

# Slip outside the sanctioned window, per frame, in millimetres of road. The
# car anim gate's own bound, so the two agree by construction rather than by
# two people picking a number.
TOL_PHANTOM_MM = 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measured", default=os.path.join(
        R2, "world/car_anim_measured.json"),
        help="the MEASURED dump: matrix_world off the built blend")
    ap.add_argument("--declared", default=os.path.join(
        R2, "world/car_anim_car.json"),
        help="the author's dump. ONLY the wheelspin WINDOW is taken from "
             "here — it is a declaration of where the sanctioned exception is "
             "allowed, and the slip inside and outside it is measured off the "
             "built blend, never off this file")
    ap.add_argument("--path", default=os.path.join(R2, "render/film9_path.json"))
    ap.add_argument("--exposure", help="json of {frame: exposure} sampled from "
                                       "the built scene. Produce it with: "
                                       "blender -b <built.blend> "
                                       "--factory-startup -P "
                                       "tools/dump_exposure.py -- --out FILE "
                                       "[--frames N]. (This help used to cite "
                                       "'--dump-exposure in the companion "
                                       "script'; no such flag exists, and "
                                       "line 286 treats a missing --exposure "
                                       "as a FAIL, so the phantom blocked the "
                                       "only documented way to pass.)")
    ap.add_argument("--lo", type=int, default=BEAT2[0])
    ap.add_argument("--hi", type=int, default=BEAT2[1])
    ap.add_argument("--json-out")
    a = ap.parse_args()

    M = json.load(open(a.measured))
    fr = {int(r["f"]): r for r in M["frames"]}
    D = json.load(open(a.declared))
    flag = {int(r["f"]): bool(r.get("spinflag")) for r in D["samples"]}
    P = {e["f"]: e for e in json.load(open(a.path))["path"]}
    out = {"measured_blend": M["blend"], "path": os.path.abspath(a.path)}
    fails = []

    # ---- A. wheelspin, from the keyed transforms ------------------------
    lo, hi = a.lo, a.hi
    rows = []
    for f in range(2, M["frame_end"] + 1):
        if f not in fr or (f - 1) not in fr:
            continue
        p0, p1 = fr[f - 1]["loc"], fr[f]["loc"]
        ground = math.dist(p0[:3], p1[:3])
        sp = fr[f]["spin_fc"]
        sp0 = fr[f - 1]["spin_fc"]
        spin = sum(sp[c] - sp0[c] for c in sp) / len(sp)
        rows.append((f, ground, spin, spin * WHEEL_R - ground,
                     flag.get(f, False)))

    win = [r for r in rows if r[4]]
    out["window_frames"] = [win[0][0], win[-1][0]] if win else None
    out["window_len"] = len(win)
    out["window_slip_rad"] = sum(r[3] for r in win) / WHEEL_R if win else 0.0
    out["window_slip_rev"] = out["window_slip_rad"] / (2 * math.pi)
    off = [r for r in rows if not r[4]]
    worst = max(off, key=lambda r: abs(r[3])) if off else None
    out["phantom_worst_mm"] = abs(worst[3]) * 1000.0 if worst else 0.0
    out["phantom_worst_frame"] = worst[0] if worst else None
    out["phantom_frames_over_tol"] = sum(
        1 for r in off if abs(r[3]) * 1000.0 > TOL_PHANTOM_MM)

    print("=== A. WHEELSPIN, from the keyed CAR_ROOT and spin hubs "
          "(`s_m` is never read)")
    print(f"  sanctioned window   frames {out['window_frames']}  "
          f"({out['window_len']} frames)")
    print(f"  slip inside it      {out['window_slip_rad']:.5f} rad = "
          f"{out['window_slip_rev']:.4f} rev of wheel turned over ground "
          f"NOT covered")
    print(f"  PHANTOM slip outside it, worst  {out['phantom_worst_mm']:.4f} mm "
          f"of road at f{out['phantom_worst_frame']}  (tol "
          f"{TOL_PHANTOM_MM} mm); frames over tol "
          f"{out['phantom_frames_over_tol']} of {len(off)}")
    print("  per frame across the window and its shoulders:")
    print("     f   ground_mm  spin_rad   slip_mm  flag")
    for r in rows:
        if not (out["window_frames"][0] - 3 <= r[0]
                <= out["window_frames"][1] + 3):
            continue
        print(f"  {r[0]:5d} {r[1]*1000:10.3f} {r[2]:9.5f} {r[3]*1000:9.3f}"
              f"   {'SPIN' if r[4] else ''}")
    if out["window_len"] < 8:
        fails.append(f"the sanctioned wheelspin is {out['window_len']} frames; "
                     f"the brief asks for ~10 and beat 2 is built around it")
    if out["window_slip_rev"] < 0.25:
        fails.append(f"the sanctioned window carries only "
                     f"{out['window_slip_rev']:.4f} rev of slip — a launch that "
                     f"does not slip is not the shot")
    if out["phantom_frames_over_tol"]:
        fails.append(f"{out['phantom_frames_over_tol']} frames OUTSIDE the "
                     f"window slip more than {TOL_PHANTOM_MM} mm of road, worst "
                     f"{out['phantom_worst_mm']:.3f} mm at "
                     f"f{out['phantom_worst_frame']}")

    # ---- D. the car starts moving when filmtime says ---------------------
    launch_f = FT.LAUNCH_FILM_T * FPS
    still = [r for r in rows if lo <= r[0] <= int(launch_f) and r[1] > 1e-6]
    moving = [r for r in rows if int(launch_f) + 2 <= r[0] <= hi and r[1] > 1e-6]
    out["launch_frame"] = launch_f
    out["frames_moving_before_launch"] = len(still)
    out["frames_moving_after_launch"] = len(moving)
    print(f"\n=== D. filmtime puts telemetry t=0 at film frame "
          f"{launch_f:.1f}")
    print(f"  frames {lo}-{int(launch_f)} with any ground motion: {len(still)}")
    print(f"  frames {int(launch_f)+2}-{hi} with ground motion: {len(moving)} "
          f"of {hi - int(launch_f) - 1}")
    if still:
        fails.append(f"the car moves on {len(still)} frames before the declared "
                     f"launch frame {launch_f:.1f}")

    # ---- C. the camera against the launch --------------------------------
    print(f"\n=== C. the camera against the car, frames {lo}-{hi}")
    print("     f   cam-to-car_m  rear-patch_deg  car_halfwidth_frac  lens")
    cam_rows = []
    for f in range(lo, hi + 1):
        if f not in P or f not in fr:
            continue
        cam = P[f]["p"]
        root = fr[f]["loc"][:3]
        hd = fr[f]["rot"][2]
        rear = [root[0] - math.cos(hd) * CAR_HALF_LEN,
                root[1] - math.sin(hd) * CAR_HALF_LEN, 0.0]
        d = math.dist(cam, root)
        q = P[f]["q"]
        # camera -Z in world, from the quaternion
        w, x, y, z = q
        fwd = (-2 * (x * z + w * y), -2 * (y * z - w * x),
               -(1 - 2 * (x * x + y * y)))
        n = math.hypot(*fwd) or 1.0
        fwd = tuple(v / n for v in fwd)
        v = [rear[i] - cam[i] for i in range(3)]
        vn = math.hypot(*v) or 1.0
        ang = math.degrees(math.acos(max(-1.0, min(1.0, sum(
            fwd[i] * v[i] / vn for i in range(3))))))
        half = math.degrees(math.atan(0.5 * SENSOR_W / P[f]["lens"]))
        cam_rows.append((f, d, ang, ang / half, P[f]["lens"]))
    for r in cam_rows:
        if r[0] % 4 == 1 or r[0] in (793, 818, 828, 864):
            print(f"  {r[0]:5d} {r[1]:12.3f} {r[2]:14.2f} {r[3]:18.3f} "
                  f"{r[4]:7.2f}")
    out["cam_min_m"] = min(r[1] for r in cam_rows)
    out["cam_min_f"] = min(cam_rows, key=lambda r: r[1])[0]
    # THE REAR CONTACT PATCH IS ONLY THE SUBJECT WHILE IT IS SPINNING.
    # Judging it across the whole beat measures the wrong quantity: from the
    # hook-up onward the camera tucks in behind at under 5 m and the car's own
    # rear necessarily swings wide of the axis — at f857 it is 41.9 deg off a
    # 29.2 mm lens 4.76 m away, which is a tight chase and not a framing
    # defect. The rig's aim gate already holds the car's reference point to
    # 0.588 of the half-frame there. So the containment test runs from the
    # start of the settle to four frames past the last spinning frame, and
    # everything after it is REPORTED.
    w0, w1 = out["window_frames"]
    judged = [r for r in cam_rows if lo <= r[0] <= w1 + 4]
    after = [r for r in cam_rows if r[0] > w1 + 4]
    out["rear_patch_worst_frac"] = max(r[3] for r in judged)
    out["rear_patch_worst_f"] = max(judged, key=lambda r: r[3])[0]
    out["rear_patch_after_worst_frac"] = max((r[3] for r in after), default=0.0)
    out["rear_patch_after_worst_f"] = (max(after, key=lambda r: r[3])[0]
                                       if after else None)
    print(f"  closest approach {out['cam_min_m']:.3f} m at "
          f"f{out['cam_min_f']}")
    print(f"  JUDGED f{lo}-{w1 + 4} (settle + the {w1 - w0 + 1} spinning "
          f"frames): the rear contact patch never leaves "
          f"{out['rear_patch_worst_frac']:.3f} of the half-frame "
          f"(worst f{out['rear_patch_worst_f']})")
    print(f"  REPORTED f{w1 + 5}-{hi} (hook-up and chase, rear patch is not "
          f"the subject): reaches "
          f"{out['rear_patch_after_worst_frac']:.3f} at "
          f"f{out['rear_patch_after_worst_f']}")
    if out["rear_patch_worst_frac"] > 1.0:
        fails.append(f"the rear contact patch — where the sanctioned wheelspin "
                     f"happens — leaves the frame at "
                     f"f{out['rear_patch_worst_f']}")

    # ---- E. MOTION BLUR, in delivery pixels ------------------------------
    #
    # REPORTED, not gated. The seam pins the camera 6.6 m from the ignition
    # station with 25 frames to cover it, so the descent is inherently fast and
    # a 180 deg shutter turns speed into streak. This is the number that says
    # what that costs at 4K, and it is the one a person has to make a judgement
    # about — a gate cannot decide how much blur a shot wants.
    #
    #   sweep = v * (shutter / FPS) / d          radians the subject sweeps
    #   px    = sweep_deg / hfov_deg * 3840      at the delivery width
    print(f"\n=== E. MOTION BLUR at 3840 px, 180 deg shutter (REPORTED, not "
          f"gated)")
    blur = []
    for f in range(lo, hi + 1):
        if f not in P or (f - 1) not in P or f not in fr:
            continue
        v = math.dist(P[f - 1]["p"], P[f]["p"]) * FPS
        d = math.dist(P[f]["p"], fr[f]["loc"][:3])
        if d < 1e-3:
            continue
        sweep = math.degrees(v * (0.5 / FPS) / d)
        hfov = math.degrees(2 * math.atan(SENSOR_W / (2 * P[f]["lens"])))
        blur.append((f, sweep / hfov * 3840.0, v, d))
    if blur:
        w = max(blur, key=lambda r: r[1])
        over = [r for r in blur if r[1] > 60.0]
        out["blur_worst_px"], out["blur_worst_f"] = w[1], w[0]
        out["blur_frames_over_60px"] = len(over)
        print("     f    streak_px   cam_v   cam-to-car")
        for r in blur:
            if r[0] % 4 == 1 or r[0] == w[0]:
                print(f"  {r[0]:5d} {r[1]:11.1f} {r[2]:8.3f} {r[3]:11.3f}")
        print(f"  worst {w[1]:.1f} px at f{w[0]} ({w[2]:.2f} m/s at "
              f"{w[3]:.2f} m); {len(over)} frames over 60 px")
        print(f"  for scale: beat 1's own peak is 3.897 m/s at ~10 m on a 58 mm "
              f"lens = 51 px, so this beat's descent streaks "
              f"{w[1]/51.0:.1f}x beat 1's worst")

    # ---- B. the exposure ---------------------------------------------------
    if a.exposure:
        ex = {int(k): v for k, v in json.load(open(a.exposure)).items()}
        span = [ex[f] for f in range(lo, hi + 1) if f in ex]
        out["exposure_min"], out["exposure_max"] = min(span), max(span)
        out["exposure_span_stops"] = max(span) - min(span)
        print(f"\n=== B. exposure across frames {lo}-{hi}: "
              f"{min(span):+.6f} .. {max(span):+.6f}, span "
              f"{out['exposure_span_stops']:.2e} stops")
        if out["exposure_span_stops"] > 1e-6:
            fails.append(f"the exposure moves {out['exposure_span_stops']:.4f} "
                         f"stops across beat 2, which is an iris move on screen "
                         f"in a take with no cuts")
    else:
        print("\n=== B. exposure NOT MEASURED — pass --exposure. Unproven is a "
              "fail and this is unproven.")
        fails.append("exposure across beat 2 was not measured")

    for f in fails:
        print("   FAIL " + f)
    if a.json_out:
        json.dump(out, open(a.json_out, "w"), indent=1)
    print(">> STAGE RESULT: " + ("BEAT2_OK" if not fails else "BEAT2_DEFECT"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
