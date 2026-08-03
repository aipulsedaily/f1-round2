"""FILM TIME <-> WORLD TIME. One mapping, imported by everything that needs it.

Standard library only, so it can be imported both by `tools/author_beats2_5.py`
under the project venv and by `anim/build_camera_rig.py` inside Blender.

WHY THIS FILE EXISTS
--------------------
The film is one take of `total_frames` at 24 fps. The car's motion lives in
`telemetry/telemetry.csv`, indexed by WORLD time. Beat 3 slows world time to a
floor while the camera keeps flying in real time, so the two clocks diverge by a
fixed amount and never re-converge. Anything that asks "where is the car in
frame N" has to walk the same ramp, or it is aiming at a car that is not there.

Before this file, `build_camera_rig.build_time_map()` was the only implementation
and it did not integrate to the declared world duration:

    declared   docs/beat_sheet.json speed_ramps[0]: screen_s 8.0 -> world_s 1.6
    implemented  ease over the first third, hold, ease over the last third,
                 floor 0.20  ->  mean scale 0.4667  ->  3.73 s of world time

2.13 s of world time too much. That is not a rounding error: it moves the car
2.13 s further round the lap than every other artefact in the project expects.
Three independent numbers say 1.6 s is the correct figure and they agree to
about 30 ms:

    car nose reaches the glass (telemetry s = 11.98)     world t = 1.9282
    beat 3 starts (docs/beat_sheet.json)                 film t = 36.0
      => LAUNCH_FILM_T = 34.0718

    beat 6 peel-off world [129.84, 2.37, 2.8]  is EXACTLY the car's own position
    at world t = 69.6314 (telemetry gives 129.8403, 2.3749) lifted to 2.8 m, and
    the declared peel speed 83.1 m/s matches the car's 83.05 m/s there.
      beat 6 key t = -3.0 must therefore land at film t = 110.1, i.e. beat 6
      start (113.1) + (-3.0), and:
        110.1 - 69.6314 - 34.0718 = 6.397  ==  8.0 - 1.6   (the ramp's loss)

    car crosses the start/finish line at world t = 9.1013
      -> film 9.1013 + 34.0718 + 6.4 = 49.573, and beat 5 starts at 49.6.

So the ramp must consume exactly 1.6 s of world time over its 192 frames, i.e.
a MEAN world_time_scale of exactly 0.20.

WHAT THAT COSTS, STATED PLAINLY
-------------------------------
A mean of 0.20 with a floor of 0.20 leaves no room for any ease at all. The
brief allows the floor to sit anywhere in 15-25 %, and the arithmetic is
unforgiving: with symmetric-smoothstep eases of Ni and No frames inside N,

    mean = floor + ((Ni + No) / 2N) * (1 - floor)      (approximately)

so a 15 % floor buys only about 21 frames of ease in total across 192. The ramp
below therefore snaps down over 6 frames (0.25 s) as the nose meets the glass
and blooms back over 15 frames (0.63 s) as the car clears the debris, with the
floor SOLVED so the integral is exactly the declared 1.6 s. Both eases are C1
smoothstep — smooth, not stepped, as the brief requires — they are simply fast.
A fast collapse on impact and a slower release is also the right shape
dramatically; a symmetric 8 s dip would have been the wrong one even if the
arithmetic had allowed it.
"""

FPS = 24

# Beat 3's ramp shape. Frame counts, not fractions: the ramp is 192 frames long
# and the eases are short enough that a fraction would round badly.
RAMP_EASE_IN_FRAMES = 6
RAMP_EASE_OUT_FRAMES = 15

# The car starts moving (telemetry t = 0) at this film time. Derived, not
# chosen: 36.0 (beat 3 start) minus 1.92815 (world t at telemetry s = 11.98,
# the nose at the glass plane x = +15.0).
LAUNCH_FILM_T = 34.0718
GLASS_WORLD_T = 1.92815


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _ramp_scales(n_frames, floor, n_in, n_out):
    """world_time_scale for each of the ramp's n_frames, as a list."""
    out = []
    hold = n_frames - n_in - n_out
    for i in range(n_frames):
        if i < n_in:
            k = 1.0 - (1.0 - floor) * smoothstep((i + 1) / n_in)
        elif i < n_in + hold:
            k = floor
        else:
            j = i - n_in - hold
            k = floor + (1.0 - floor) * smoothstep((j + 1) / n_out)
        out.append(k)
    return out


def solve_floor(n_frames, world_s, n_in, n_out, fps=FPS):
    """The floor that makes the ramp integrate to exactly `world_s` seconds.

    Bisection rather than algebra because the eases are discrete sums, and a
    closed form that is 1/24 s out is a closed form that is wrong.
    """
    target = world_s * fps                      # sum of scales
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        s = sum(_ramp_scales(n_frames, mid, n_in, n_out))
        if s < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build_time_map(sheet, total_frames, fps=FPS):
    """world_time_scale for every frame 1..total_frames, as a list indexed [f-1].

    Returns (scales, info). `info` carries the solved floor and the achieved
    world duration so a caller can assert against the declared one instead of
    trusting this docstring.
    """
    scales = [1.0] * total_frames
    beats = {b["name"]: b for b in sheet["beats"]}
    info = []
    for ramp in sheet.get("speed_ramps", []):
        b = beats.get(ramp["beat"])
        if not b:
            continue
        f0 = int(round(b["start_s"] * fps)) + 1          # first frame of the beat
        f1 = int(round((b["start_s"] + b["duration_s"]) * fps))
        n = f1 - f0 + 1
        world_s = float(ramp["world_s"])
        n_in = min(RAMP_EASE_IN_FRAMES, n // 4)
        n_out = min(RAMP_EASE_OUT_FRAMES, n // 4)
        floor = solve_floor(n, world_s, n_in, n_out, fps)
        ks = _ramp_scales(n, floor, n_in, n_out)
        for i, k in enumerate(ks):
            f = f0 + i
            if 1 <= f <= total_frames:
                scales[f - 1] = k
        info.append({"beat": ramp["beat"], "frames": [f0, f1], "n": n,
                     "declared_world_s": world_s,
                     "achieved_world_s": sum(ks) / fps,
                     "solved_floor": floor,
                     "ease_in_frames": n_in, "ease_out_frames": n_out,
                     "declared_floor": ramp.get("min_world_time_scale")})
    return scales, info


def world_time_table(scales, total_frames, fps=FPS, launch_film_t=LAUNCH_FILM_T):
    """WORLD time (telemetry seconds) at every frame 1..total_frames.

    Negative before the car moves — the camera is alive during beat 1 and the
    idle, the car is not. Callers clamp at 0.
    """
    launch_f = launch_film_t * fps
    w = [0.0] * (total_frames + 1)
    for f in range(1, total_frames + 1):
        if f <= launch_f:
            w[f] = (f / fps) - launch_film_t          # scale is 1 before beat 3
        else:
            w[f] = w[f - 1] + scales[f - 1] / fps
    return w
