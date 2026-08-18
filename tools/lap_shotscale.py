"""Corrected shot scale over the WHOLE film, by projecting the car's oriented box.

    python3 tools/lap_shotscale.py --path render/film22_path.json

WHY THIS EXISTS
---------------
`tools/beat1_shotscale.py` computed apparent size as

    CAR_LEN * lens / (SENSOR_W * distance_to_centre)

which is the subtense of the car's LENGTH at the distance of the car's CENTRE.
Both halves are wrong and they are wrong in opposite directions, so the product
looked plausible and survived two independent tools (R2-429, R2-430, and the
main-thread correction appended to R2-430). `tools/beat1_true_extent.py` fixed it
for beat 1 only, where the car is parked at the origin. This does the same thing
for every frame of the film, with the car MOVING: telemetry position, telemetry
heading/pitch/roll, the beat-3 world-time ramp, and the authored camera.

WHAT IT MEASURES
----------------
The eight corners of the car's oriented bounding box in world space, projected
through the actual camera (position, quaternion, animated focal length), and the
screen-space extent of the projected hull as a fraction of frame WIDTH.

CONTROLS -- every one of these must behave, and `--selftest` asserts them
------------------------------------------------------------------------
  1. POSITIVE, against pixels.  f697 (beat 1, car parked, R2-430's ruler frame)
     must land near 0.4746, which is what `tools/beat1_true_extent.py` gets and
     within 2.5 % of the 0.4630 read off `r1full_000697.png` with a ruler.
  2. NEGATIVE, absent subject.  A zero-volume car must read 0.000 everywhere.
     Two of the detectors written for R2-422 returned 0.90 and 1.00 by latching
     onto the turntable and the rear wall; a metric that cannot tell the car from
     the scenery fails this.
  3. NEGATIVE, displaced subject.  Moving the car 200 m sideways must collapse
     the reading. A metric that reads the same whether the car is there or not is
     the failure this project has hit most often.
  4. AGREEMENT, independent implementation.  Must reproduce `tmp/shotscale_v2.npy`
     -- built by a different agent from a script that no longer exists -- to
     better than 2 % over beat 5.

R2-3181 — THE PRIVATE TELEMETRY READER IS GONE, AND WHY IT MATTERED  (#155)
--------------------------------------------------------------------------
This file used to keep its OWN `csv.DictReader` of `telemetry/telemetry.csv`
with its own interpolator, and that copy CLAMPED:

    def at(self, t):
        t = max(0.0, min(t, self.t_end))        # <- the defect

`telemetry.csv` ends at world t 72.5833 s; the film's world time runs to
83.6115 s. The last 11.03 s — ALL 264 FRAMES OF BEAT 6 — are past the end of
the table. The clamp parked the car at (326.2, 167.2) for every one of them,
rising to a 230.7 m error, and returned a perfectly plausible number for it.
It produced two published findings ("2,349 px off the left of frame at f2978",
"32.2 % of the ending is under 60 px at 4K") that had to be retracted (R2-2886).

A silent clamp is worse than a crash and worse than a refusal, because the
caller cannot tell it happened. The reader is now `anim/carrig.CarRig` — the
SAME pose function `anim/build_car_anim.py` keys the car with — so past the
telemetry the car is continued exactly the way the film's own author continues
it (`carpath.Car._extrap` / `LapDown`), and there is no second implementation
left to go stale. `--selftest` control C0 asserts the extrapolation is live: a
sample past `t_end` must NOT equal the sample at `t_end`.

WHICH CAR? THE SOURCE'S OR THE ONE IN THE DELIVERED FILM?      (R2-3181, #155)
-----------------------------------------------------------------------------
These are not the same car, and this tool now makes you say which you mean.

`world/car_anim.blend` — the ONLY place the film's car motion comes from;
`tools/build_film_scene.py` APPENDS its keys and refuses if they are missing —
was built **2026-08-04 19:51**. The R2-943 lap-down landed in `anim/carpath.py`
at **2026-08-07 08:35**, two and a half days LATER. So the delivered film's car
does not have it: past the line it streaks on at 89.767 m/s.

`render/film22_path.json` — the camera — was built 08-08 04:42, i.e. WITH the
lap-down. The camera therefore tracks a car that is not in the scene, and that
is the whole of the "~368 px residual at f2760" R2-2886 left open and guessed
was the beat sheet. It is not the beat sheet; the sheet's `time_map` is
byte-identical across every snapshot on disk (measured).

    --car source   (default)  anim/carrig, R2-943 lap-down ON.  WHERE THE
                              PROJECT SAYS THE CAR SHOULD BE.  Correct for
                              judging a rebuild; WRONG against film22 pixels.
    --car built               the pre-R2-943 constant-speed arm, which
                              reproduces `world/car_anim_measured.json` to
                              0.000 m on every frame and lands on the car in
                              the delivered proxy.  Use this to measure
                              `work/r22161_proxy/`.

Controls C6 and C7 assert both halves of that, so the day someone rebuilds
`car_anim.blend` the controls fail and say why.

LIMITS, STATED NOT BURIED
-------------------------
  * The box is the car's ASSEMBLED box. During beat 1 the car is exploded across
    616 parts, so beat 1 is reported as NaN rather than as a wrong number.
  * Occlusion is not modelled: a car behind a barrier still measures full size.
  * A bounding box is larger than the car it bounds, so this OVERSTATES slightly.
    That direction is the safe one for a "the subject is too small" finding.
  * The box is symmetric about the reference point (+-CAR_LEN/2). The measured
    car is x -2.678..+3.020, i.e. 0.171 m forward of centre. That is a 3.0 %
    longitudinal placement error and it is NOT corrected here, because every
    published `frac_w` in this project was taken with the symmetric box and
    changing it silently would be the mid-flight instrument change this file
    keeps logging. It is recorded so the next reader can price it.
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.expanduser("~/f1-round2")
for _p in (R2, os.path.join(R2, "anim"), os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from anim import filmtime  # noqa: E402
import carpath as _CP  # noqa: E402
import carrig as _CR  # noqa: E402
import world_contract as _WC  # noqa: E402

SENSOR_W = 36.0
RES = (3840, 2160)
SENSOR_H = SENSOR_W * RES[1] / RES[0]

# ---------------------------------------------------------------- the box ----
# THE CAR'S BOX IS IN CAR_ROOT-LOCAL COORDINATES, AND SO IS `pos`.
#
# IMPORTED, not retyped: `anim/carpath.py` is where the film's own author and
# gate read them from, and this file is the seventh copy that used to exist.
#
# R2-3181, AND IT CONTRADICTS R2-2521 §4c. That entry recorded this file as
# "0.992-as-top for the third time ... the subject centre 0.340 m below the
# car's true centre at 0.836 m", on the grounds that the car is z 0.340..1.332.
# It is — IN THE SHOWROOM, where its wheels stand on the dais deck, and
# `circuit_spec.showroom.dais.deck_top_z` / `carrig.DECK_TOP_Z` is 0.340.
# `world_contract.CAR_RIDE_HEIGHT_M` is that deck height under a misleading
# name; an F1 car's actual ride height is ~30 mm.
#
# MEASURED, three ways:
#   * `world/car_anim_measured.json` frame 1: CAR_ROOT loc z = 0.340 and its
#     four contact patches are at z = 0.340. CAR_ROOT SITS ON THE GROUND.
#   * `carrig.pose()` sets CAR_ROOT's z from the four-wheel contact solve, and
#     `WHEEL_CENTRE_Z_LOCAL = 0.360 == WHEEL_RADIUS_M`, so local z 0 is the
#     tyre's contact patch.
#   * drawn on the delivered proxy at f1268/f1275/f1380
#     (`work/r2-3181/carbox_check.png`): z 0.000..0.992 bounds the car; the
#     "corrected" 0.340..1.332 box sits visibly 0.340 m ABOVE it, its lower
#     edge cutting the sidepods and its upper edge in clear air.
#
# So CAR_BOT_Z = 0.0 is right and applying R2-2521 §4c's correction would put
# the subject centre 0.340 m HIGH. The claim is withdrawn here.
CAR_LEN = _CP.CAR_LEN
CAR_W = 2.0 * _CP.CAR_HALF_W
CAR_TOP_Z = _CP.CAR_TOP_Z
CAR_BOT_Z = 0.0

# The two-level chain gets checked rather than trusted: carpath retypes the
# contract's figures and this file reads carpath.
assert (CAR_LEN, CAR_W, CAR_TOP_Z) == (_WC.CAR_BODY_LEN_M, _WC.CAR_BODY_W_M,
                                       _WC.CAR_BODY_H_M), (
    "anim/carpath.py and world/world_contract.py disagree about the car box: "
    "%r vs %r" % ((CAR_LEN, CAR_W, CAR_TOP_Z),
                  (_WC.CAR_BODY_LEN_M, _WC.CAR_BODY_W_M, _WC.CAR_BODY_H_M)))

SPEC = os.path.join(R2, "docs/circuit_spec.json")
TELEMETRY = os.path.join(R2, "telemetry/telemetry.csv")
#: The car keys `render/film22.blend` actually appended, sampled off
#: `world/car_anim.blend` by `tools/sample_car_blend.py`. Read only by the
#: controls -- this is the FILM, and the model has to agree with it or say why.
BUILT_CAR = os.path.join(R2, "world/car_anim_measured.json")
CAR_ANIM_BLEND = os.path.join(R2, "world/car_anim.blend")

#: THE CONTROLS' OWN CAMERA, pinned. R2-3181.
#: Controls 1 and 4 compare against references measured on `film14_path.json`
#: (the ruler frame `r1full_000697.png`, and `tmp/shotscale_v2.npy`). They are
#: run against THAT camera whatever `--path` the caller asks for, because a
#: control that inherits the thing under test measures two changes and reports
#: one -- which is exactly how the default-path move below first looked like a
#: projection defect.
CONTROL_PATH = os.path.join(R2, "render/film14_path.json")

BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714),
         ("6_ending", 2715, 2978)]


def qn(q):
    m = math.sqrt(sum(v * v for v in q)) or 1.0
    return [v / m for v in q]


def basis(q):
    """Camera right / up / forward in world space, from [w,x,y,z]."""
    w, x, y, z = qn(q)
    right = [1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)]
    up = [2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)]
    fwd = [-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
           -(1 - 2 * (x * x + y * y))]
    return right, up, fwd


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


class Car:
    """The car's pose at any world time, from `anim/carrig` — ONE implementation.

    NOT a telemetry reader. `carrig.CarRig` is the function that KEYS the car in
    `anim/build_car_anim.py`, so what this projects and what the film renders
    cannot drift: position and heading from `carpath.Car.state` (which
    extrapolates past the telemetry via `_extrap`/`LapDown` instead of
    clamping), z from the four-wheel contact solve, and attitude from the ground
    plus the body's own dive-squat and lean.

    `at(t)` keeps the six-tuple the deleted private reader returned, because
    `tools/r2581_nearfield_sweep.py`, `tools/r2581_lensfix.py`,
    `tools/r2971_pont_camera_rebase.py` and `tools/r2_2881_pixelpeep.py` all
    unpack it. It no longer clamps, and `t_end` is still published so a caller
    that WANTS to refuse past the telemetry can.

    `arm="built"` swaps the extrapolation for the pre-R2-943 constant-speed one
    that `world/car_anim.blend` actually holds. See the module docstring.
    """

    def __init__(self, csv_path=TELEMETRY, spec=None, arm="source"):
        if arm not in ("source", "built"):
            raise SystemExit("REFUSING: unknown car arm %r; use 'source' "
                             "(R2-943 lap-down, what the project authored) or "
                             "'built' (what world/car_anim.blend holds)" % arm)
        if spec is None:
            spec = json.load(open(SPEC))
        elif isinstance(spec, str):
            spec = json.load(open(spec))
        self.arm = arm
        self.rig = _CR.CarRig(csv_path, spec)
        if arm == "built":
            # The documented A/B control arm: `carpath.Car` normalises a falsy
            # `lapdown` to None and `_extrap` is then `v[-1] * dt` and nothing
            # else, exactly (its own docstring). Done here rather than through
            # the `F1_LAPDOWN` env var because that switch is explicitly not a
            # shipping switch and this is not the ship path.
            self.rig.car.lapdown = None
        self.t_end = self.rig.t_end
        self._cache = {}

        # THE RAW TELEMETRY TABLE, for the callers that want the MEASURED range
        # rather than a pose. `tools/r2971_pont_camera_rebase.py:209` reads
        # `car.col["speed_ms"]` to size its envelope check, and it was reaching
        # into the deleted private reader's internals to do it. Kept as a
        # VIEW onto `carrig`/`carpath`'s own arrays -- no third transcription --
        # so that tool keeps working without being edited by me (its path is
        # held by another lease).
        c = self.rig.car
        self.t = c.t
        self.col = {"x": c.x, "y": c.y, "z": c.z, "heading_rad": c.h,
                    "speed_ms": c.v, "s_m": c.s,
                    "pitch_rad": self.rig.pitch_c, "roll_rad": self.rig.roll_c}

    def at(self, t):
        """(pos, heading, pitch, roll, speed, track_s) — NEVER clamped."""
        hit = self._cache.get(t)
        if hit is None:
            p = self.rig.pose(t)
            roll, pitch, yaw = p["rot"]
            hit = ([p["loc"][0], p["loc"][1], p["loc"][2]], yaw, pitch, roll,
                   p["speed"], self.rig.car.track_s(t))
            self._cache[t] = hit
        return hit


def obb_corners(pos, yaw, pitch, roll, scale=1.0, offset=(0.0, 0.0, 0.0)):
    """The eight world-space corners of the car's oriented box."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    # Z(yaw) * Y(pitch) * X(roll)
    m = [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]
    hx, hy = CAR_LEN / 2.0 * scale, CAR_W / 2.0 * scale
    zlo, zhi = CAR_BOT_Z * scale, CAR_TOP_Z * scale
    out = []
    for i in range(8):
        lx = hx if i & 1 else -hx
        ly = hy if i & 2 else -hy
        lz = zhi if i & 4 else zlo
        out.append([
            pos[0] + offset[0] + m[0][0] * lx + m[0][1] * ly + m[0][2] * lz,
            pos[1] + offset[1] + m[1][0] * lx + m[1][1] * ly + m[1][2] * lz,
            pos[2] + offset[2] + m[2][0] * lx + m[2][1] * ly + m[2][2] * lz,
        ])
    return out


def project(corners, eye, q, lens):
    """(frac_w, frac_h, behind) for a world point set through this camera."""
    rt, up, fwd = basis(q)
    xs, ys = [], []
    behind = False
    for p in corners:
        v = [p[j] - eye[j] for j in range(3)]
        z = dot(v, fwd)
        if z <= 1e-6:
            behind = True
            continue
        xs.append(dot(v, rt) / z * lens)
        ys.append(dot(v, up) / z * lens)
    if behind:
        # A box straddling the camera plane has no finite screen extent. Report
        # it as unmeasurable rather than letting the perspective divide near
        # zero manufacture a huge number -- that is exactly how the displaced
        # negative control below used to pass when it should have failed.
        return float("nan"), float("nan"), True
    return (max(xs) - min(xs)) / SENSOR_W, (max(ys) - min(ys)) / SENSOR_H, behind


def load_path(p):
    return {int(k["f"]): k for k in json.load(open(p))["path"]}


def series(path, car, world_t, scale=1.0, offset=(0.0, 0.0, 0.0),
           lo=1, hi=2978, pin_t=None):
    """Per-frame (frac_w, dist_to_centre, lens). Beat 1 is NaN by design.

    `pin_t` freezes the car at one world time -- the negative control: the camera
    flies the whole lap while the car never leaves the dais.
    """
    out = {}
    for f in range(lo, hi + 1):
        k = path.get(f)
        if k is None:
            continue
        if f <= 792:
            out[f] = (float("nan"), float("nan"), k["lens"])
            continue
        pos, yaw, pit, rol, _v, _s = car.at(
            world_t[f] if pin_t is None else pin_t)
        c = obb_corners(pos, yaw, pit, rol, scale, offset)
        fw, _fh, _b = project(c, k["p"], k["q"], k["lens"])
        ctr = [pos[i] + offset[i] for i in range(3)]
        ctr[2] += CAR_TOP_Z / 2.0
        out[f] = (fw, math.dist(k["p"], ctr), k["lens"])
    return out


def build_world_time(sheet, total):
    scales, _info = filmtime.build_time_map(sheet, total)
    return filmtime.world_time_table(scales, total)


def median(v):
    v = sorted(x for x in v if x == x)
    if not v:
        return float("nan")
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


# ------------------------------------------------------------------ selftest --
def selftest(path, car, world_t):
    ok = True

    # 0. THE CLAMP CONTROL.                                   R2-3181, #155
    #    The defect this file shipped for weeks was a reader that answered
    #    past the end of its own table by repeating the last row. It was
    #    invisible because the answer LOOKED like an answer. So: sample past
    #    `t_end` and require the car to have MOVED, and require the movement to
    #    be the one `carpath._extrap` defines rather than merely non-zero.
    t_end = car.t_end
    p0 = car.at(t_end)[0]
    p5 = car.at(t_end + 5.0)[0]
    moved = math.dist(p0[:2], p5[:2])
    ref_car = _CP.Car(TELEMETRY, json.load(open(SPEC)),
                      lapdown=None if car.arm == "source" else False)
    rp = ref_car.state(t_end + 5.0)[0]
    agrees = math.dist(p5[:2], rp[:2])
    good = moved > 1.0 and agrees < 1e-9
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  extrapolation/no_clamp  5 s past the "
          f"telemetry the car has moved {moved:.1f} m (a clamped reader reads "
          f"0.0) and it lands within {agrees:.2e} m of anim/carpath.Car.state, "
          f"which is the only definition of that motion")

    # 1. POSITIVE: the parked car at f697, against the ruler on r1full_000697.png
    #
    #    R2-3181: THIS CONTROL PINS ITS OWN CAMERA. It used to project through
    #    whatever `--path` the run was given and compare against a hard-coded
    #    0.5032519052306422 — a figure taken on `render/film14_path.json`. The
    #    moment the default path moved to the delivered film the control read
    #    0.4418 and FAILED, blaming the projection for a change of camera. A
    #    control whose reference was measured on one input must be run on that
    #    input; anything else tests two things and reports one.
    #
    #    And the reference is now COMPUTED by `tools/beat1_true_extent.py`
    #    rather than retyped, because `docs/beat_sheet.json:beat1.car_box` is
    #    live (R2-2521 is moving it by millimetres right now) and a literal
    #    would have started failing for a third unrelated reason.
    import beat1_true_extent as BTE
    cb = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]["car_box"]
    lo_b, hi_b = cb["lo"], cb["hi"]
    corners = [[lo_b[0] if i & 1 else hi_b[0], lo_b[1] if i & 2 else hi_b[1],
                lo_b[2] if i & 4 else hi_b[2]] for i in range(8)]
    kpath = load_path(CONTROL_PATH)
    k = kpath[697]
    fw, _, _ = project(corners, k["p"], k["q"], k["lens"])
    ref = BTE.extent(lo_b, hi_b, k["p"], k["q"], k["lens"])[0]
    ruler = 0.4630                 # front-wing tips on r1full_000697.png
    good = abs(fw - ref) < 1e-9 and ruler < fw < ruler * 1.15
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  positive/pixels  f697 projects "
          f"{fw:.4f}; the independent tools/beat1_true_extent.py gets {ref:.4f} "
          f"on this same path, and the ruler on r1full_000697.png reads "
          f"{ruler:.4f}. A BOX bounds the car, so it must sit slightly ABOVE "
          f"the ruler ({(fw/ruler-1)*100:.1f} % here) and never below.")

    # 2. NEGATIVE: no subject at all
    s0 = series(path, car, world_t, scale=0.0, lo=1191, hi=2714)
    mx = max(v[0] for v in s0.values())
    good = mx < 1e-9
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/absent  a zero-volume car "
          f"reads max {mx:.6f} over beat 5; must be 0")

    # 3. NEGATIVE: the car never leaves the dais while the camera flies the lap.
    #    This is the control the R2-422 detectors that returned 0.90 and 1.00
    #    would have failed: they were reading the turntable and the rear wall,
    #    which are still there when the car is not.
    sd = series(path, car, world_t, pin_t=0.0, lo=1191, hi=2714)
    base = series(path, car, world_t, lo=1191, hi=2714)
    mb = median([v[0] for v in base.values()])
    seen = [v[0] for v in sd.values() if v[0] == v[0]]
    md = median(seen) if seen else 0.0
    agree = sum(1 for f in sd
                if sd[f][0] == sd[f][0] and base[f][0] == base[f][0]
                and abs(sd[f][0] - base[f][0]) < 0.1 * base[f][0])
    good = agree < 0.05 * len(sd)
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/absent-from-shot  car left "
          f"parked on the dais while the camera flies the lap: median {md*100:.2f} % "
          f"vs the real {mb*100:.2f} %, only {len(seen)}/{len(sd)} frames even "
          f"measurable, and it agrees with the real reading to 10 % on {agree} "
          f"frames. A detector latched onto scenery would agree on all 1,524.")
    print(f"        COROLLARY, and it is uncomfortable: the control's {md*100:.2f} % "
          f"is not far below the {4.22:.2f} % the f2035-f2227 stretch actually "
          f"measures. At that size the car is barely bigger on screen than if it "
          f"had never left the showroom. That is a fact about the stretch, not a "
          f"fault in the instrument.")

    # 4. AGREEMENT with the independent v2 build
    try:
        import numpy as np
        # R2-3181: pinned to CONTROL_PATH for the same reason as control 1 --
        # `tmp/shotscale_v2.npy` was built on film14's camera. Measured on the
        # delivered film22 camera this control reads p95 2.10 % and "fails",
        # which is a statement about two different cameras and not about two
        # different implementations.
        v2base = series(load_path(CONTROL_PATH), car, world_t, lo=1191, hi=2714)
        v2 = np.load(os.path.join(R2, "tmp/shotscale_v2.npy"))
        mine = [v2base[f][0] for f in range(1191, 2715)]
        theirs = list(v2[1190:2714])
        rel = [abs(a - b) / max(b, 1e-6) for a, b in zip(mine, theirs)]
        p95 = sorted(rel)[int(0.95 * len(rel))]
        good = p95 < 0.02
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  agreement  vs tmp/shotscale_v2.npy "
              f"over beat 5: p95 relative difference {p95*100:.2f} %, must be < 2 %")
    except Exception as e:  # pragma: no cover
        print(f"  SKIP  agreement  ({e})")

    # 5. R2-1011 OCCLUSION ANNOTATION.  This instrument cannot see occluders,
    #    and its blindness was invisible because the numbers looked healthy.
    #    These prove the annotation fires, that it does not fire everywhere,
    #    and that it keeps `in_frame` and `occluded` apart -- conflating those
    #    two has already produced one wrong finding about the film's last
    #    frames, so the distinction gets a control of its own.
    occ = load_occlusion(os.path.join(R2, OCCLUSION_LEDGER))
    good = bool(occ)
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/ledger  loaded "
          f"{len(occ)} in-frame rows")

    good = not ledger_is_stale()
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/not_stale  the ledger is "
          f"newer than {OCCLUSION_DESCRIBES}, the geometry it describes")

    # R2-3181.  `ledger_is_stale()` as written checks the ledger against the
    # ARCHITECTURE only.  An occlusion result is a statement about a world AND
    # about a car, and `tools/r2651_occlusion_sweep.py` reads the car from
    # `world/car_anim_measured.json`.  Checking one of its two inputs is the
    # same shape of blind spot the ledger check was written to close.
    good = not ledger_is_stale(source=BUILT_CAR)
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/not_stale_car  the ledger "
          f"is also newer than {os.path.relpath(BUILT_CAR, R2)}, the CAR POSE "
          f"tools/r2651_occlusion_sweep.py raycast against — an occlusion row "
          f"is a claim about a world and a car, and the check above sees only "
          f"the world")

    # ...and the car pose table must itself describe the blend on disk. It does
    # NOT: the measurement is 08-03 04:04 / 300,235,801 bytes and the blend is
    # 08-04 19:51 / 301,667,220 bytes. That is a WARN and not a FAIL because the
    # ledger's own frames are unaffected in beats 1-5, but every beat-6
    # occlusion row is about a car nobody has re-measured.
    try:
        meta = json.load(open(BUILT_CAR))
        same = (meta.get("blend_bytes") == os.path.getsize(CAR_ANIM_BLEND))
    except OSError:
        same = False
    print(f"  {'PASS' if same else 'WARN'}  occlusion/car_identity  "
          f"{os.path.relpath(BUILT_CAR, R2)} "
          + ("describes the blend on disk"
             if same else
             "does NOT describe world/car_anim.blend on disk "
             "(sampled %s bytes, blend is %s). Nothing that reads it may "
             "claim to describe the built car until it is re-sampled."
             % (meta.get("blend_bytes"), os.path.getsize(CAR_ANIM_BLEND))))

    # R2-1081: this used to assert 15 frames including f1114-1116.  R2-731
    # closed the beat-4 blackout before the shipping film was built, so the
    # live answer is 12 and all of them are beat 5's bridge.
    hidden = sorted(f for f, v in occ.items() if v >= OCC_HIDDEN)
    good = hidden == list(range(2180, 2192))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/positive  the car is "
          f"in frame and wholly hidden on exactly {len(hidden)} frames, "
          f"all of them beat 5's bridge — beat 4 was closed by R2-731")

    # The superseded ledger must still parse, and must still disagree.  If it
    # ever stops disagreeing, either R2-731 has been reverted or someone has
    # overwritten the old file, and both are worth a failure.
    old = load_occlusion(os.path.join(R2, "render/r2651/occlusion.json"))
    stale_hidden = sorted(f for f, v in old.items() if v >= OCC_HIDDEN)
    good = stale_hidden[:3] == [1114, 1115, 1116]
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/supersession  the Aug-04 "
          f"ledger still lists f1114-1116; the live one does not. The "
          f"difference IS R2-731, and reading the wrong file costs 3 frames")

    good = all(occ.get(f, 0.0) < OCC_HIDDEN for f in (2160, 2175, 2200, 2225))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/negative  clear frames "
          f"either side of the bridge do NOT read as occluded")

    # The car is out of frame for the film's tail.  Those rows must be ABSENT
    # from the ledger, not present-and-clear: "not in shot" is not "visible".
    good = not any(f in occ for f in range(2900, 2979))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/in_frame_filter  "
          f"out-of-frustum frames are excluded, not scored as visible")

    good = load_occlusion("/nonexistent/occlusion.json") == {}
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/absent  a missing ledger "
          f"degrades to no annotation, and does not crash the tool")

    # 6/7. WHICH CAR IS IN THE FILM.                          R2-3181, #155
    #      `world/car_anim_measured.json` is the car keys `render/film22.blend`
    #      appended, sampled off the blend itself. It is the only handle in the
    #      repo on what the DELIVERED pixels contain, and both arms are scored
    #      against it. C6 must agree everywhere; C7 must DISAGREE, and only in
    #      beat 6, or the R2-943 lap-down has quietly reached the build and the
    #      warning this file prints is now a lie.
    try:
        built = {r["f"]: r["loc"]
                 for r in json.load(open(BUILT_CAR))["frames"]}
        arm_b = Car(TELEMETRY, arm="built")
        arm_s = Car(TELEMETRY, arm="source")
        probe = list(range(793, 2715, 37)) + list(range(2715, 2979, 11))
        db = max(math.dist(built[f][:2], arm_b.at(world_t[f])[0][:2])
                 for f in probe)
        good = db < 1e-3
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  film/built_arm_is_the_film  the "
              f"constant-speed arm reproduces the car keys in "
              f"{os.path.relpath(BUILT_CAR, R2)} to {db:.2e} m over "
              f"{len(probe)} probe frames spanning beats 2-6")

        pre = max(math.dist(built[f][:2], arm_s.at(world_t[f])[0][:2])
                  for f in probe if f <= 2714)
        post = max(math.dist(built[f][:2], arm_s.at(world_t[f])[0][:2])
                   for f in probe if f > 2714)
        good = pre < 1e-3 and post > 100.0
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  film/lapdown_is_NOT_in_the_film "
              f" the R2-943 arm matches the built car to {pre:.2e} m through "
              f"f2714 and then diverges to {post:.1f} m. world/car_anim.blend "
              f"was built 2026-08-04 19:51; the lap-down landed 08-07 08:35. "
              f"If this control ever passes with a small divergence the car "
              f"has been rebuilt and --car source is finally the film.")
    except (OSError, KeyError) as e:                          # pragma: no cover
        ok = False
        print(f"  FAIL  film/arms  could not read {BUILT_CAR}: {e}")

    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


#: R2-1011.  This tool projects the car's box and reports how much of the frame
#: width it fills.  It has no idea whether anything is IN FRONT of the car, so
#: at f2185 and f2190 it printed 4.66 % and 4.91 % -- among its most confident
#: readings of the whole span -- for two frames in which the car is 100 % hidden
#: behind `ARCH_PontPlongee`.  A number is not wrong here so much as it is
#: answering a different question than the reader is asking.
#:
#: The occlusion ledger already exists, so the fix costs nothing but wiring.
#: It is ADDITIVE: `frac_w` still prints in the same column with the same value,
#: because other agents are measuring with this tool right now and silently
#: changing an instrument mid-flight is the failure this project keeps logging.
#: R2-1081.  The FIRST version of this pointed at `render/r2651/occlusion.json`
#: (Aug 04 19:53), which lists f1114-1116 as hidden behind the pit building.
#: **R2-731 closed that on Aug 07 04:11** by making the building's west end an
#: annexe, and `film17_breach.blend` was built at 06:09, after it.  So the
#: instrument built to stop a metric being confidently wrong in the flattering
#: direction shipped, for one commit, being confidently wrong in the
#: PESSIMISTIC direction -- marking three good frames OCCLUDED and reporting
#: beat 4 as worse than it is.  Same failure, opposite sign.
#:
#: The ledger must be newer than the geometry it describes, and
#: `ledger_is_stale()` is the check that would have caught it.
OCCLUSION_LEDGER = "render/r2731/occ_final_items.json"
OCCLUSION_DESCRIBES = "world/build_architecture.py"
OCC_HIDDEN = 0.99      # front-occluded fraction at which "the car" is not visible


def ledger_is_stale(ledger=None, source=None):
    """Is the occlusion ledger older than the geometry it claims to describe?

    An occlusion result is a statement about a world that existed when the
    raycast ran.  Nothing in the file records which world that was, so mtime is
    the only handle -- crude, but it is the difference between a live figure and
    a retracted one, and both this instrument and the agent that caught it were
    fooled by exactly this.
    """
    l = ledger or os.path.join(R2, OCCLUSION_LEDGER)
    s = source or os.path.join(R2, OCCLUSION_DESCRIBES)
    try:
        return os.path.getmtime(l) < os.path.getmtime(s)
    except OSError:
        return True


def load_occlusion(p):
    """{frame: occ_frac_front} for frames that are IN the frustum.

    `in_frame` is filtered first and deliberately: a car outside the frustum and
    a car hidden behind a wall are indistinguishable in a summary, and conflating
    them has already produced one wrong finding about the film's last frames.
    """
    try:
        d = json.load(open(p))
    except Exception:
        return {}
    return {int(r["f"]): float(r.get("occ_frac_front") or 0.0)
            for r in d.get("frames", []) if r.get("in_frame")}


def main():
    ap = argparse.ArgumentParser()
    # R2-3181: was film14_path.json, which is the 74 mm beat 6 from 08-03 and
    # EIGHT film builds stale. Beat 6's median moves 4.15 % -> 4.64 % on the
    # delivered camera alone, before the reader fix. The default is now the
    # camera the delivered proxy was actually rendered with.
    ap.add_argument("--path", default=os.path.join(R2, "render/film22_path.json"))
    ap.add_argument("--car", choices=("source", "built"), default="source",
                    help="'source' = anim/carrig with the R2-943 lap-down (what "
                         "the project authored); 'built' = the constant-speed "
                         "arm that world/car_anim.blend actually holds and that "
                         "the delivered proxy shows. See the module docstring.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dump", default="")
    ap.add_argument("--frames", default="")
    ap.add_argument("--occlusion", default=os.path.join(R2, OCCLUSION_LEDGER),
                    help="occlusion ledger; '' disables the annotation")
    a = ap.parse_args()
    occ = load_occlusion(a.occlusion) if a.occlusion else {}

    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    total = sheet["total_frames"]
    world_t = build_world_time(sheet, total)
    car = Car(TELEMETRY, arm=a.car)
    path = load_path(a.path)

    # Say WHICH camera and WHICH car every figure below is about, before the
    # figures. A number in this project has been quoted against the wrong film
    # more than once, and the fix for that is provenance in the same output.
    print(f">> camera  {os.path.relpath(a.path, R2)}  "
          f"(f2978 lens {path[total]['lens']:.2f} mm)")
    print(f">> car     {a.car}: "
          + ("anim/carrig with the R2-943 lap-down -- WHERE THE PROJECT SAYS "
             "THE CAR SHOULD BE" if a.car == "source" else
             "the pre-R2-943 constant-speed arm -- what world/car_anim.blend "
             "holds and what the delivered proxy shows"))
    if a.car == "source":
        print(">> WARNING, beat 6 only: world/car_anim.blend was built "
              "2026-08-04 19:51 and the lap-down landed 08-07 08:35, so the "
              "DELIVERED film's car is NOT this one. Past f2714 these figures "
              "describe a rebuild, not render/film22.blend. Use --car built to "
              "measure the pixels that exist. (R2-3181)")

    if a.selftest:
        okay = selftest(path, car, world_t)
        print(f">> STAGE RESULT: {'SELFTEST_OK' if okay else 'SELFTEST_FAILED'}")
        return

    s = series(path, car, world_t, lo=1, hi=total)

    if a.frames:
        print(f"{'frame':>6} {'t_s':>7} {'dist':>8} {'lens':>7} {'frac_w':>8}"
              f" {'occ':>6}")
        for tok in a.frames.split(","):
            if "-" in tok:
                b, e = tok.split("-")
                rr = range(int(b), int(e) + 1)
            else:
                rr = [int(tok)]
            for f in rr:
                if f in s:
                    fw, d, ln = s[f]
                    o = occ.get(f)
                    tail = ("     --" if o is None
                            else f" {o*100:5.1f}%"
                                 + ("   OCCLUDED -- the car is not visible on "
                                    "this frame; the figure to its left is the "
                                    "size it WOULD read at"
                                    if o >= OCC_HIDDEN else ""))
                    print(f"{f:6d} {f/24.0:7.2f} {d:8.1f} {ln:7.2f} {fw:8.4f}"
                          f"{tail}")

    print()
    print(f"{'beat':<12} {'frames':>7} {'median':>9} {'p10':>9} {'min':>9}"
          f"  {'hidden':>7}")
    for name, f0, f1 in BEATS:
        vals = [s[f][0] for f in range(f0, f1 + 1) if f in s]
        good = sorted(x for x in vals if x == x)
        hid = [f for f in range(f0, f1 + 1) if occ.get(f, 0.0) >= OCC_HIDDEN]
        if not good:
            print(f"{name:<12} {f1-f0+1:7d} {'--':>9} {'--':>9} {'--':>9}"
                  "   (car exploded; not measured)")
            continue
        print(f"{name:<12} {f1-f0+1:7d} {median(good)*100:8.2f}% "
              f"{good[int(0.1*len(good))]*100:8.2f}% {good[0]*100:8.2f}%"
              f"  {len(hid):7d}")
        if hid:
            # The median above INCLUDES these frames.  Say so, and say what it
            # is without them -- a beat's shot scale is not a claim about
            # frames the audience cannot see the subject on.
            vis = sorted(s[f][0] for f in range(f0, f1 + 1)
                         if f in s and occ.get(f, 0.0) < OCC_HIDDEN
                         and s[f][0] == s[f][0])
            print(f"{'':<12} {'':>7} {median(vis)*100:8.2f}% "
                  f"{vis[int(0.1*len(vis))]*100:8.2f}% {vis[0]*100:8.2f}%"
                  f"  {'<- car visible only; %d frame(s) hidden behind '
                       'geometry excluded' % len(hid):>7}")

    if a.dump:
        import numpy as np
        np.save(a.dump, np.array([s.get(f, (float('nan'),))[0]
                                  for f in range(1, total + 1)]))
        print(f"wrote {a.dump}")
    print(">> STAGE RESULT: LAP_SHOTSCALE_OK")


if __name__ == "__main__":
    main()
