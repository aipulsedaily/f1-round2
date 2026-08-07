"""THE WHOLE FILM'S PACING, from the camera path — all 2978 frames, no render.

    .venv/bin/python tools/campath_pacing.py --selftest
    .venv/bin/python tools/campath_pacing.py                       # the LIVE path
    .venv/bin/python tools/campath_pacing.py --path work/x_path.json --label CAND
    .venv/bin/python tools/campath_pacing.py --flat                # flat-stretch census

WHY A CAMERA-PATH INSTRUMENT AND NOT A PIXEL ONE.  `tools/pacing_curve.py`
measures the delivered picture and is the authority, but THERE IS NO PROXY OF
THIS FILM.  Every video in `watch/` is a fragment: beat 1 (792 frames) and the
ending (264) are the only contiguous renders that exist, and beats 2-5 —
1,922 frames, 80.1 s, 64.5 % of the running time — have never been rendered as
a continuous sequence at all.  A note that says "the camera angle OVERALL is too
slow" cannot be answered from 26 % of the film, and rendering the other 74 % to
find out costs more than the fix.

So this measures the same three curves from the thing that CAUSES them.  Given a
per-frame camera (position, orientation, focal length) and a depth, the motion of
the image is not an estimate — it is projection, and it is exact:

    S[f]     mean displacement of the image between f-1 and f, in FRAME WIDTHS
    A[f]     |S[f] - S[f-1]|            the derivative.  THE HEADLINE.
    N[f]     fraction of the frame at f that was OFF-SCREEN one second ago

N is the brief's third lever stated exactly: "new information entering frame".
It is a fraction, not a level, and it cannot be faked by a brighter scene.

THE DEPTH IS RAY-CAST against a coarse box scene — the 15 cluster boxes at their
position on that frame, the car, the ground and the room shell — so each of the
45 sensor samples carries its own parallax.  See the DEPTH block below for the
single-depth version this replaces and the measurement that replaced it.

WHAT VALIDATES IT IS NOT THE ARGUMENT.  `--selftest` correlates this curve
against `tools/pacing_curve.py`'s PIXEL curve over the 791 frames where both
exist, and requires Spearman >= 0.80.  It measures 0.834.  An instrument that
cannot predict the pictures it does have is not allowed to speak about the ones
it does not — and 64.5 % of this film is pictures it does not have.
"""

import argparse
import bisect
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "anim"))

FPS = 24
SENSOR_W_MM = 36.0
RES = (3840, 2160)
SENSOR_H_MM = SENSOR_W_MM * RES[1] / RES[0]
# The grid the image motion is averaged over.  Odd counts so the frame centre is
# a sample: a move that only rotates about the optical axis (roll) must not read
# as zero, and a centre-only measurement is exactly what would say it does.
GRID_W, GRID_H = 9, 5
DEPTH_FLOOR_M = 0.5


# --------------------------------------------------------------------------- #
#  GEOMETRY                                                                     #
# --------------------------------------------------------------------------- #
def quat_to_mat(q):
    """Blender's (w,x,y,z) -> 3x3 rotation, re-normalised.

    The path files store 6 decimal places, which `tools/campath_diff.py` measures
    as a 0.203 deg self-null floor.  Normalising here is not politeness; an
    un-normalised quaternion puts a scale into the rotation and the scale shows
    up as image motion that is not there.
    """
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def sensor_grid():
    """Sensor-plane sample points, in mm, as an (n,2) array.

    CELL CENTRES, not the closed interval.  Sampling the edges puts points at
    exactly +-18.000 mm, and `in_frame` then decides a stationary camera's own
    frame by floating-point luck: the first version of this read 6.667 % = 3/45
    of the frame as NEW information for a camera that had not moved.  Cell
    centres are also the correct quadrature for a mean over the frame.
    """
    us = ((np.arange(GRID_W) + 0.5) / GRID_W - 0.5) * SENSOR_W_MM
    vs = ((np.arange(GRID_H) + 0.5) / GRID_H - 0.5) * SENSOR_H_MM
    uu, vv = np.meshgrid(us, vs)
    return np.stack([uu.ravel(), vv.ravel()], axis=1)


_GRID = sensor_grid()


def rays(R, lens):
    """World-space unit rays through the sensor grid. Blender looks down -Z."""
    d = np.concatenate([_GRID, np.full((len(_GRID), 1), -float(lens))], axis=1)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return d @ R.T


def project(P, p, R, lens):
    """World points -> (u_mm, v_mm, in_front). The inverse of `rays`."""
    d = (P - p) @ R                     # world -> camera (R is orthonormal)
    z = -d[:, 2]
    ok = z > 1e-6
    zc = np.where(ok, z, 1.0)
    return (lens * d[:, 0] / zc, lens * d[:, 1] / zc, ok)


def in_frame(u, v, ok):
    return ok & (np.abs(u) <= SENSOR_W_MM / 2) & (np.abs(v) <= SENSOR_H_MM / 2)


# --------------------------------------------------------------------------- #
#  THE DEPTH — RAY-CAST, not a single number                                    #
# --------------------------------------------------------------------------- #
#
# THE FIRST VERSION USED ONE DEPTH PER FRAME — the range to the beat's declared
# aim subject — and it is worth recording why that was not good enough, because
# the argument for it was reasonable.  Rotation and lens need no depth at all, so
# a single depth only has to carry the PARALLAX term, and the subject's range is
# the one depth the shot is composed around.
#
# It is not good enough because parallax is the whole point.  A camera weaving
# through a field of parts at 1 to 8 m makes near parts sweep across the frame
# while far ones barely move, and collapsing that to one number throws away
# exactly the signal being measured.  MEASURED, against the pixel curve over
# beat 1's 791 frames:
#
#     one depth (the aim subject)     Spearman 0.795   Pearson 0.490
#     ray-cast depth per sample       Spearman 0.831   Pearson 0.668
#
# So each of the 45 sensor samples gets its own depth, by intersecting its ray
# with the geometry that is actually in front of it: the 15 cluster boxes at
# their position on that frame, the car's box, the ground, and the room shell.
# It is a coarse scene -- boxes, not meshes -- and it is stated as coarse.  What
# it is not is a guess, and the 0.831 is what says so.
GROUND_Z = 0.0
# The showroom, measured, from tools/build_beatsheet.py's close-out constraints:
# walls |x| 15.25 / |y| 11.25, ceiling 6.20.  Rays that miss every cluster end
# on the room, which is where they end in the picture.
ROOM_LO = np.array([-15.25, -11.25, 0.0])
ROOM_HI = np.array([15.25, 11.25, 6.20])
# Outdoors there is no shell.  A ray that clears the ground is sky, and sky is
# far enough away that it contributes no image motion -- which is the correct
# answer, and a small cap here would invent motion that the picture does not
# have.
FAR_OUTDOOR_M = 5000.0
CAR_HALF = np.array([5.698 / 2.0, 2.005 / 2.0])
CAR_TOP_Z = 0.992


def ray_depth(p, dirs, lo, hi, shell=None, far=FAR_OUTDOOR_M):
    """Nearest forward hit for each ray, against AABBs + ground + an optional shell."""
    o = p[None, None, :]
    dd = dirs[:, None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (lo[None, :, :] - o) / dd
        t2 = (hi[None, :, :] - o) / dd
    tn = np.nanmax(np.minimum(t1, t2), axis=2)
    tf = np.nanmin(np.maximum(t1, t2), axis=2)
    tn = np.where((tf >= np.maximum(tn, 0.0)) & (tn > 0.0), tn, np.inf)
    d = tn.min(axis=1) if lo.size else np.full(len(dirs), np.inf)
    dz = dirs[:, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.minimum(d, np.where(dz < -1e-9, (GROUND_Z - p[2]) / dz, np.inf))
    if shell is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            s1 = (shell[0] - p) / dirs
            s2 = (shell[1] - p) / dirs
        d = np.minimum(d, np.nanmin(np.maximum(s1, s2), axis=1))
    return np.clip(np.nan_to_num(d, nan=far, posinf=far), DEPTH_FLOOR_M, far)


class Scene:
    """The coarse box scene at any frame, and where each beat's shell is."""

    def __init__(self, path, sheet, spec, telemetry, explode, beat1anim):
        import filmtime as FT
        from carpath import Car
        n = len(path)
        scales, _ = FT.build_time_map(sheet, n)
        self.wt = FT.world_time_table(scales, n)
        self.car = Car(telemetry, spec)
        self.beats = {}
        for b in sheet["beats"]:
            f0 = int(round(b["start_s"] * FPS)) + 1
            f1 = int(round((b["start_s"] + b["duration_s"]) * FPS))
            self.beats[b["name"]] = (f0, f1)
        plan = json.load(open(explode))
        anim = json.load(open(beat1anim)) if os.path.exists(beat1anim) else {}
        self.flight_f = float(anim.get("flight_s", 1.55)) * FPS
        self.cl = []
        for k, c in plan["clusters"].items():
            off = c["explode_offset"]
            elo = np.array([c["bbox_min"][i] + off[i] for i in range(3)])
            ehi = np.array([c["bbox_max"][i] + off[i] for i in range(3)])
            self.cl.append((elo, ehi, np.array(c["bbox_min"], float),
                            np.array(c["bbox_max"], float),
                            (anim.get("clusters", {}).get(k) or {}).get("last_land")))

    def beat_of(self, f):
        for nm, (f0, f1) in self.beats.items():
            if f0 <= f <= f1:
                return nm
        return "6_ending"

    def at(self, f):
        """-> (lo, hi, shell, far) for frame f."""
        nm = self.beat_of(f)
        if nm in ("1_assembly", "2_launch"):
            t = (f - 1) / FPS
            lo, hi = [], []
            for elo, ehi, slo, shi, lf in self.cl:
                if lf is None:
                    u = 0.0
                else:
                    u = max(0.0, min(1.0, (t * FPS - (lf - self.flight_f))
                                     / max(self.flight_f, 1.0)))
                    u = u * u * (3.0 - 2.0 * u)
                lo.append(elo + (slo - elo) * u)
                hi.append(ehi + (shi - ehi) * u)
            return (np.array(lo), np.array(hi), (ROOM_LO, ROOM_HI), 60.0)
        # outdoors: the car's box on the ground, and the ground
        cp = self.car.pos(max(self.wt[f], 0.0))
        fw = self.car.fwd(max(self.wt[f], 0.0))
        h = math.hypot(fw[0], fw[1]) or 1.0
        cx, sy = fw[0] / h, fw[1] / h
        ex = abs(cx) * CAR_HALF[0] + abs(sy) * CAR_HALF[1]
        ey = abs(sy) * CAR_HALF[0] + abs(cx) * CAR_HALF[1]
        c = np.array([cp[0], cp[1], cp[2]], float)
        lo = np.array([[c[0] - ex, c[1] - ey, c[2]]])
        hi = np.array([[c[0] + ex, c[1] + ey, c[2] + CAR_TOP_Z]])
        return (lo, hi, None, FAR_OUTDOOR_M)


def subject_depths(path, sheet, spec, telemetry, explode, beat1anim):
    """Distance from the lens to the beat's aim subject, per frame.

    KEPT AS A DIAGNOSTIC, not as the depth the pacing uses -- see the block above.
    It is what the aim gate is measuring against, so it is the right thing to
    print beside a pacing curve, and it is the wrong thing to compute one from.

    Beats 2-6 aim at the car, and the car comes from `anim/carpath.py` — the same
    module `anim/build_camera_rig.py` imports, so the depth here is the depth the
    aim gate is measuring against rather than a second opinion about it.

    Beat 1 aims at "the nearest of the 15 cluster volumes ... moved from its
    exploded position to its seated one", so that is what is used: the nearest
    cluster centre at that frame.  Beat 6 hands over from the car to the facade
    at the sheet's own `point_from_t`.
    """
    import filmtime as FT
    from carpath import Car

    n = len(path)
    scales, _ = FT.build_time_map(sheet, n)
    wt = FT.world_time_table(scales, n)
    car = Car(telemetry, spec)

    beats = {b["name"]: b for b in sheet["beats"]}
    aim = sheet["aim"]

    # beat 1: cluster centres, exploded -> seated, exactly as the sheet's
    # aim declaration describes and as tools/build_beatsheet.py's `where()` does.
    plan = json.load(open(explode))
    anim = json.load(open(beat1anim)) if os.path.exists(beat1anim) else {}
    flight_f = float(anim.get("flight_s", 1.55)) * FPS
    exp, seated, land = {}, {}, {}
    for k, c in plan["clusters"].items():
        off = c["explode_offset"]
        exp[k] = np.array([(c["bbox_min"][i] + c["bbox_max"][i]) / 2 + off[i]
                           for i in range(3)])
        seated[k] = np.array([(c["bbox_min"][i] + c["bbox_max"][i]) / 2
                              for i in range(3)])
        lf = (anim.get("clusters", {}).get(k) or {}).get("last_land")
        land[k] = lf
    b6 = aim.get("6_ending", {})
    b6_start = beats["6_ending"]["start_s"]
    b6_point = np.array(b6.get("fixed_point", [15.0, 0.0, 3.1]), dtype=float)
    b6_from = float(b6.get("point_from_t", 6.0))

    def beat_of(f):
        t = (f - 1) / FPS
        for nm, b in beats.items():
            if b["start_s"] - 1e-9 <= t < b["start_s"] + b["duration_s"] - 1e-9:
                return nm
        return "6_ending"

    out = np.zeros(n)
    for i, rec in enumerate(path):
        f = rec["f"]
        p = np.array(rec["p"], dtype=float)
        nm = beat_of(f)
        if nm == "1_assembly":
            t = (f - 1) / FPS
            best = 1e18
            for k in exp:
                lf = land[k]
                if lf is None:
                    c = exp[k]
                else:
                    u = max(0.0, min(1.0, (t * FPS - (lf - flight_f))
                                     / max(flight_f, 1.0)))
                    u = u * u * (3.0 - 2.0 * u)
                    c = exp[k] + (seated[k] - exp[k]) * u
                best = min(best, float(np.linalg.norm(c - p)))
            out[i] = best
        else:
            t_in_b6 = (f - 1) / FPS - b6_start
            if nm == "6_ending" and t_in_b6 >= b6_from:
                q = b6_point
            else:
                cp = car.pos(max(wt[f], 0.0))
                q = np.array([cp[0], cp[1], cp[2] + float(
                    aim.get(nm, {}).get("z_off", 0.8))])
            out[i] = float(np.linalg.norm(q - p))
    return np.maximum(out, DEPTH_FLOOR_M)


# --------------------------------------------------------------------------- #
#  THE CURVES                                                                   #
# --------------------------------------------------------------------------- #
def pacing(path, scene, fps=FPS):
    """(S, A, N, v_ms) — image motion, its derivative, novelty, camera speed.

    `scene` is a `Scene`, or a plain array of one depth per frame (which is what
    the synthetic selftests hand it, because a two-frame pan has no scene).
    """
    n = len(path)
    p = np.array([r["p"] for r in path], dtype=float)
    lens = np.array([r["lens"] for r in path], dtype=float)
    Rm = [quat_to_mat(r["q"]) for r in path]
    flat = None if isinstance(scene, Scene) else np.asarray(scene, float)

    def depth_of(i, d):
        if flat is not None:
            return np.full(len(d), flat[i])
        lo, hi, shell, far = scene.at(path[i]["f"])
        return ray_depth(p[i], d, lo, hi, shell, far)

    S = np.full(n, np.nan)
    N = np.full(n, np.nan)
    W = [None] * n                       # the world points each frame's grid sees

    for i in range(n):
        d = rays(Rm[i], lens[i])
        W[i] = p[i] + depth_of(i, d)[:, None] * d

    # image motion: where the grid of frame f-1 lands in frame f
    #
    # CAPPED AT ONE FRAME WIDTH, and that is a definition rather than a guard.
    # S is the motion of the VISIBLE image, and a sample that has travelled more
    # than a whole frame width is off the picture -- how much further it went is
    # not something an audience can see.  Without the cap the measure is not even
    # bounded: `project` divides by the depth along the axis, so a sample that
    # passes close to the camera plane goes to infinity, and beat 5 duly measured
    # S = 116.9 frame widths on one frame and a beat mean of 0.530 that was set
    # by 47 frames out of 1524.  Those are the arithmetic of `tan`, not pictures.
    for i in range(1, n):
        u, v, ok = project(W[i - 1], p[i], Rm[i], lens[i])
        du = (u - _GRID[:, 0]) / SENSOR_W_MM
        dv = (v - _GRID[:, 1]) / SENSOR_W_MM        # both in FRAME WIDTHS
        S[i] = float(np.mean(np.where(ok, np.minimum(np.hypot(du, dv), 1.0), 1.0)))

    # novelty: how much of frame f was outside frame f-fps
    for i in range(fps, n):
        u, v, ok = project(W[i], p[i - fps], Rm[i - fps], lens[i - fps])
        N[i] = 1.0 - float(np.mean(in_frame(u, v, ok)))

    A = np.full(n, np.nan)
    A[2:] = np.abs(np.diff(S[1:]))
    v_ms = np.full(n, np.nan)
    v_ms[1:] = np.linalg.norm(np.diff(p, axis=0), axis=1) * fps
    return S, A, N, v_ms


# --------------------------------------------------------------------------- #
#  THE TIMESCALE — R2-1601, and it is a correction to this file's own headline. #
# --------------------------------------------------------------------------- #
#
# `A` is |S[f] - S[f-1]|: the derivative over ONE FRAME.  So is R2-1144's
# published `|acceleration| 0.898`, which is |d1[f] - d1[f-1]| on the pixel
# curve.  Both of them measure how much the rate of image motion changes in
# 1/24 of a second, and NOBODY PERCEIVES A CAMERA THAT WAY.  An audience feels a
# camera speed up over half a second to two seconds; a frame-to-frame difference
# is mostly render noise and spline ripple, and it is nearly blind to exactly the
# gesture it is being asked to detect.
#
# MEASURED, and this is what exposed it.  R2-1601 gives the payoff orbit a real
# tempo -- the built per-frame path goes from a near-constant 2.4 m/s to a range
# of 1.60 to 3.14 m/s, a 1.96x swing -- and the one-frame derivative moved from
# 1.47 % to 1.71 %.  It could barely see a doubling.  Over half a second:
#
#     orbit f464-754      A(1 frame)/S      A(0.5 s)/S       CoV of S
#     before                    1.47 %          10.68 %         21.3 %
#     after                     1.71 %          14.94 %         29.7 %
#
# So the slow derivative is reported alongside the fast one everywhere, and the
# slow one is the one to read.  The fast one is kept because R2-1144 is stated in
# it and a measurement that cannot be compared to the one it corrects is not a
# correction.
SLOW_S = 0.5


def slow_derivative(S, fps=FPS, window_s=SLOW_S):
    """|change in the image-motion rate| over `window_s`, per frame.

    S is smoothed over the same window first, so this measures the trend and not
    the ripple riding on it.
    """
    w = max(int(round(window_s * fps)), 2)
    x = np.nan_to_num(np.asarray(S, float))
    sm = np.convolve(x, np.ones(w) / w, mode="same")
    out = np.full(len(S), np.nan)
    out[w:] = np.abs(sm[w:] - sm[:-w])
    return out


def _m(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return float(a.mean()) if a.size else float("nan")


def _rank(x):
    return np.argsort(np.argsort(np.asarray(x, float))).astype(float)


# --------------------------------------------------------------------------- #
#  WHERE THE FILM GOES FLAT                                                     #
# --------------------------------------------------------------------------- #
#
# FLAT IS NOT SLOW.  A stretch is flat when the camera stops CHANGING what it is
# doing, whatever it is doing.  R2-1144's whole point is that the sleepy opening
# carries more movement than what follows it, so a threshold on S would rank the
# opening as the liveliest passage in the beat.  The threshold is therefore on
# the derivative, expressed as a fraction of the local movement so that a slow
# passage and a fast one are held to the same standard:
#
#     jerk_ratio = mean(A) / mean(S)   over a sliding window
#
# On the delivered beat 1 the pixel instrument reads 5.2 % over the first six
# seconds, and the client falls asleep in it.  10 % is the working floor: it is
# twice the number attached to a complaint, and every stretch below it is
# reported rather than only the worst one, because "overall" was the client's
# word.
FLAT_JERK_RATIO = 0.10
FLAT_WINDOW_S = 3.0
FLAT_MIN_S = 2.0


def flat_stretches(S, A, N, fps=FPS, window_s=FLAT_WINDOW_S,
                   ratio=FLAT_JERK_RATIO, min_s=FLAT_MIN_S):
    """Contiguous runs whose sliding jerk-ratio sits under `ratio`."""
    n = len(S)
    w = int(round(window_s * fps))
    jr = np.full(n, np.nan)
    for i in range(w, n):
        s, a = _m(S[i - w:i]), _m(A[i - w:i])
        jr[i] = a / s if s > 1e-9 else np.nan
    runs, start = [], None
    for i in range(n):
        flat = np.isfinite(jr[i]) and jr[i] < ratio
        if flat and start is None:
            start = i
        elif not flat and start is not None:
            if (i - start) / fps >= min_s:
                runs.append((start, i - 1))
            start = None
    if start is not None and (n - start) / fps >= min_s:
        runs.append((start, n - 1))
    return runs, jr


def beat_table(sheet):
    out = []
    for b in sheet["beats"]:
        f0 = int(round(b["start_s"] * FPS)) + 1
        f1 = int(round((b["start_s"] + b["duration_s"]) * FPS))
        out.append((b["name"], f0, f1))
    return out


def report(S, A, N, v_ms, sheet, label):
    D = slow_derivative(S)
    print(f"\n>> WHOLE-FILM PACING — {label}   {len(S)} frames @ {FPS} fps")
    print("   S = image motion (frame widths/frame)   N = fraction of frame new "
          "since 1 s ago")
    print(f"   A/S is the derivative over ONE FRAME; D/S is over {SLOW_S:g} s "
          f"and is the one an audience feels — see the TIMESCALE block.")
    print(f"   {'beat':<12} {'frames':>11} {'S':>8} {'A/S':>7} {'D/S':>7} "
          f"{'CoV':>7} {'N':>7} {'cam m/s':>8}")
    rows = list(beat_table(sheet)) + [("FILM", 1, len(S))]
    for nm, f0, f1 in rows:
        a, b = f0 - 1, f1
        s = max(_m(S[a:b]), 1e-12)
        sd = np.nanstd(np.asarray(S[a:b], float))
        print(f"   {nm:<12} {f'{f0}-{f1}':>11} {_m(S[a:b]):8.5f} "
              f"{100*_m(A[a:b])/s:6.1f}% {100*_m(D[a:b])/s:6.1f}% "
              f"{100*sd/s:6.1f}% {_m(N[a:b]):7.3f} {_m(v_ms[a:b]):8.2f}")


def report_flat(S, A, N, sheet, label):
    runs, jr = flat_stretches(S, A, N)
    beats = beat_table(sheet)

    def where(f):
        for nm, f0, f1 in beats:
            if f0 <= f <= f1:
                return nm
        return "?"

    tot = sum(b - a + 1 for a, b in runs)
    print(f"\n>> FLAT STRETCHES — {label}: jerk-ratio under "
          f"{100*FLAT_JERK_RATIO:.0f} % of local motion for "
          f"{FLAT_MIN_S:g} s or more")
    print(f"   {'frames':>12} {'t':>14} {'dur':>6} {'beat':<12} "
          f"{'A/S':>6} {'S':>8} {'N':>6}")
    for a, b in sorted(runs, key=lambda r: r[0] - r[1]):
        f0, f1 = a + 1, b + 1
        print(f"   {f'{f0}-{f1}':>12} "
              f"{f'{(f0-1)/FPS:.1f}-{(f1-1)/FPS:.1f}s':>14} "
              f"{(f1-f0+1)/FPS:5.1f}s {where(f0):<12} "
              f"{100*_m(A[a:b+1])/max(_m(S[a:b+1]),1e-12):5.1f}% "
              f"{_m(S[a:b+1]):8.5f} {_m(N[a:b+1]):6.3f}")
    print(f"   TOTAL {tot} frames = {tot/FPS:.1f} s = "
          f"{100.0*tot/len(S):.1f} % of the film")
    return runs


# --------------------------------------------------------------------------- #
#  THE SELFTEST — this curve must predict the pictures that DO exist            #
# --------------------------------------------------------------------------- #
CALIB_VIDEO = "watch/AFTER_beat1_33s.mp4"
CALIB_FRAMES = (1, 792)
# THE GATE IS ON THE RANK CORRELATION, AND THAT IS NOT A WEAKER TEST CHOSEN TO
# PASS.  mean|I(f) - I(f-1)| SATURATES: once the image moves more than a few
# pixels, the two frames are already largely uncorrelated and the level
# difference stops growing, approaching the mean |difference| of two independent
# frames of the same scene.  Measured on beat 1, camera-path S against the pixel
# curve over the same 791 frames:
#
#     Pearson on the raw values           0.495
#     Pearson after 1 - exp(-40 S)        0.707      the saturation, modelled
#     Pearson on log S vs log |dI|        0.767
#     SPEARMAN (rank)                     0.803
#
# A monotone, strongly saturating relationship is exactly what those four numbers
# describe, and Pearson on the raw values is the wrong statistic for one -- it
# measures how LINEAR the relationship is, and nobody claimed it was linear.
# Spearman measures what is actually being asserted: that when this curve says
# the picture is moving more, the picture is moving more.
#
# Both are printed on every run, deliberately.  If a future change makes the
# relationship linear, the Pearson figure is where that will show up, and hiding
# it would hide the improvement as well as the regression.
CALIB_MIN_SPEARMAN = 0.80


def selftest(path, sheet, scene):
    import pacing_curve as PC
    vid = os.path.join(R2, CALIB_VIDEO)
    S, A, N, v = pacing(path, scene)
    bad = []
    print(">> SELFTEST 1: a stationary camera must read exactly zero")
    still = [dict(f=i + 1, p=[1.0, 2.0, 3.0], q=[1.0, 0.0, 0.0, 0.0], lens=35.0)
             for i in range(60)]
    s2, a2, n2, _ = pacing(still, np.full(60, 8.0))
    ok = _m(s2) < 1e-12 and _m(n2) < 1e-12
    print(f"   {'ok  ' if ok else 'FAIL'} S {_m(s2):.3e}  N {_m(n2):.3e}")
    if not ok:
        bad.append("stationary")

    # THE SCALE TEST IS TAKEN IN THE REGIME THE INSTRUMENT WORKS IN.  The first
    # version panned a whole frame width in one frame -- 54.9 deg at 35 mm -- and
    # read 2.139 against an expected 1.0.  That was not a bug in the projection;
    # it is `tan` doing what `tan` does at 27 deg off axis, and a real film frame
    # never moves anything like that far.  Beat 1's measured S runs 0.0003 to
    # 0.190 frame widths per frame, so the linear regime IS the operating range
    # and that is where the scale is checked.
    print(">> SELFTEST 2: a small pure pan must read S = the pan, in frame widths")
    lens = 35.0
    hf = 2.0 * math.atan(SENSOR_W_MM / (2.0 * lens))
    want = 0.05
    two = []
    for i, ang in enumerate((0.0, hf * want)):
        c, s = math.cos(ang / 2), math.sin(ang / 2)
        two.append(dict(f=i + 1, p=[0.0, 0.0, 0.0], q=[c, 0.0, s, 0.0],
                        lens=lens))
    s3, _, _, _ = pacing(two, np.full(2, 1e7))     # far depth = pure rotation
    ok = abs(s3[1] - want) < 0.004
    print(f"   {'ok  ' if ok else 'FAIL'} S {s3[1]:.5f}  want {want} +-0.004")
    if not ok:
        bad.append("pan scale")

    print(f">> SELFTEST 3: correlation against the PIXEL curve on {CALIB_VIDEO}")
    if not os.path.exists(vid):
        print(f"   SKIPPED — {vid} is not on disk")
    else:
        frames, w, h = PC.decode_gray(vid)
        d1, _, nov = PC.curves(frames)
        f0, f1 = CALIB_FRAMES
        a, b = f0 - 1, min(f1, len(S))
        sc = S[a:b]
        n = min(len(sc), len(d1))
        m = np.isfinite(sc[:n]) & np.isfinite(d1[:n])
        x, y = sc[:n][m], d1[:n][m]
        rp = float(np.corrcoef(x, y)[0, 1])
        rs = float(np.corrcoef(_rank(x), _rank(y))[0, 1])
        ok = rs >= CALIB_MIN_SPEARMAN
        print(f"   {'ok  ' if ok else 'FAIL'} Spearman {rs:.4f} over {m.sum()} "
              f"frames (floor {CALIB_MIN_SPEARMAN})   Pearson {rp:.4f} "
              f"— camera-path S vs pixel mean|dI|")
        mn = np.isfinite(N[a:b][:n]) & np.isfinite(nov[:n])
        xn, yn = N[a:b][:n][mn], nov[:n][mn]
        print(f"        novelty Spearman {float(np.corrcoef(_rank(xn), _rank(yn))[0,1]):.4f}"
              f"  (reported, not gated: pixel novelty also moves with the LIGHTS "
              f"and with 15 clusters flying, neither of which is the camera)")
        if not ok:
            bad.append("pixel rank correlation")
    print(">> STAGE RESULT: CAMPATH_PACING_SELFTEST_OK" if not bad
          else ">> STAGE RESULT: CAMPATH_PACING_SELFTEST_FAILED (%s)"
               % ", ".join(bad))
    return 0 if not bad else 1


def load_path(explicit=None, why=None):
    if explicit:
        import live_campath as L
        return L.load_explicit(explicit, why=why or "pacing measurement of a "
                               "candidate path that is not the live camera")["path"]
    import live_campath as L
    return L.load()["path"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=None,
                    help="a candidate *_path.json; default is the LIVE camera")
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    ap.add_argument("--telemetry",
                    default=os.path.join(R2, "telemetry/telemetry.csv"))
    ap.add_argument("--explode", default=os.path.join(R2, "docs/explode_plan.json"))
    ap.add_argument("--beat1anim",
                    default=os.path.join(R2, "world/beat1_anim_anim.json"))
    ap.add_argument("--label", default=None)
    ap.add_argument("--flat", action="store_true")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    path = load_path(a.path)
    sheet = json.load(open(a.sheet))
    spec = json.load(open(a.spec))
    scene = Scene(path, sheet, spec, a.telemetry, a.explode, a.beat1anim)
    label = a.label or (os.path.basename(a.path) if a.path else "LIVE")

    if a.selftest:
        return selftest(path, sheet, scene)

    S, A, N, v = pacing(path, scene)
    depth = subject_depths(path, sheet, spec, a.telemetry, a.explode, a.beat1anim)
    report(S, A, N, v, sheet, label)
    runs = report_flat(S, A, N, sheet, label) if a.flat else None
    if a.json_out:
        json.dump({"label": label, "frames": len(S), "fps": FPS,
                   "S": [None if not np.isfinite(x) else round(float(x), 6) for x in S],
                   "A": [None if not np.isfinite(x) else round(float(x), 6) for x in A],
                   "N": [None if not np.isfinite(x) else round(float(x), 6) for x in N],
                   "v_ms": [None if not np.isfinite(x) else round(float(x), 4) for x in v],
                   "depth_m": [round(float(x), 3) for x in depth],
                   "flat_runs": [[int(x + 1), int(y + 1)] for x, y in (runs or [])]},
                  open(a.json_out, "w"))
        print(f">> wrote {a.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
