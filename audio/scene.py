"""THE SOURCE AND THE LISTENER, sampled: the car from telemetry, the camera from
the rig path, and the surface the tyres are on, from the world's own geometry.

Nothing here invents motion. Every number is read from
`telemetry/telemetry.csv`, `world/camera_rig_path.json` or
`docs/circuit_spec.json`, and where those three disagree the disagreement is
MEASURED and reported rather than smoothed away.

R2-026 AND THE ONE DECISION THIS FILE EXISTS TO MAKE
----------------------------------------------------
For every telemetry row with `s_m` below ~12 m,  x / s_m = 1.25207, because the
launch run was scaled onto the geometry (dais to glass = 15.00 m in world X)
while `s_m`, `speed_ms` and `wheel_rot_rad` stayed on the unscaled 11.98 m run.

Measured here, not quoted:

    frame 45   s_m 11.202   x 14.026   speed_ms 14.451   d|p|/dt 17.961   +24.3 %
    at the glass (s_m = 11.98)         speed_ms 14.954   d|p|/dt 16.729   +11.9 %

+24.3 % is 3.77 semitones. Beat 2's entire subject is a launch, so an engine
note that is nearly four semitones flat at the moment the nose meets the glass
is not a rounding error, it is the beat's defect.

    THE ENGINE IS DRIVEN FROM `v_world = d|p(x,y,z)|/dt`, NOT FROM `speed_ms`.

Justification, in order of weight:

 1. The picture is drawn from `x, y, z`. `anim/build_camera_rig.py` aims at
    `x, y, z`; the car mesh is placed at `x, y, z`. Whatever the CSV declares,
    the car the audience sees covers 15.00 m between the dais and the glass, and
    the engine has to be the engine of THAT car.
 2. It costs nothing anywhere else. Over the whole film the two agree: 4054.030 m
    of walked position against 4052.730 m of declared arc, 0.032 % over 4 km, and
    the p99 of |v_world/speed_ms - 1| for s_m > 20 m is 2.1 %.
 3. The alternative — driving from `speed_ms` and accepting the launch error —
    would put the audio's one measurable claim (pitch tracks speed) into direct
    conflict with the picture in the one beat that is about speed.

The cost, stated: `v_world` is a numerical derivative of a 24 Hz position track,
and that track has a corner where the 1.25207 scaling stops. Over frames 45-48
`v_world` steps 17.96 -> 15.65 m/s, i.e. -55 m/s^2 for three frames, which is not
a real acceleration. It is filtered by the DRIVELINE INERTIA lag in `engine.py`
(a first-order lag on crankshaft speed, tau = 90 ms, which a real 830 kg car with
a rotating assembly has whether or not the CSV does). The lag is physical, is
applied over the whole film, and is not a special case at the seam. What it
cannot do is fix the picture: the wheels will still visibly under-rotate by 25 %
through the launch, which is R2-026's, not the audio's, to fix.
"""

from __future__ import annotations

import bisect
import csv
import json
import math
import os
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import savgol_filter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WHEEL_R = 0.36              # m; implied by the CSV itself to 1.3e-7 (see report)
#                             THE one definition; audio/engine.py imports it.
WHEELBASE = 3.60            # m, used only as a surface-transition length
CAR_LEN = 5.698
# THE start/finish station lives in anim/carpath.py and is imported, not
# restated. Two homes for one number is how a project ends up with an exposure
# hardcoded in two render setups and derived in neither.
def _sf_telemetry_s():
    import sys
    anim = os.path.join(ROOT, "anim")
    if anim not in sys.path:
        sys.path.insert(0, anim)
    import carpath
    return float(carpath.SF_TELEMETRY_S)


SF_TELEMETRY_S = _sf_telemetry_s()

# The geometry control rate lives in audio/spatial.py (CTRL_HZ). It is not
# restated here.


# --------------------------------------------------------------------- car ----
class Telemetry:
    def __init__(self, csv_path=None, spec=None):
        csv_path = csv_path or os.path.join(ROOT, "telemetry", "telemetry.csv")
        rows = list(csv.DictReader(open(csv_path)))
        self.col = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
        c = self.col
        self.t = c["t_s"]
        self.n = self.t.shape[0]
        self.t_end = float(self.t[-1])
        self.spec = spec

        # --- world arc length and the speed it implies ------------------------
        d = np.sqrt(np.diff(c["x"]) ** 2 + np.diff(c["y"]) ** 2 + np.diff(c["z"]) ** 2)
        self.S_world = np.concatenate([[0.0], np.cumsum(d)])
        # Savitzky-Golay derivative: a centred 7-point quadratic fit. Plain
        # np.gradient would hand the ramp of R2-026's seam straight through as a
        # two-sample spike; SG is still a derivative, not a smoother of the
        # signal, and its window (0.29 s) is far shorter than any real transient
        # in a 24 Hz motion track.
        dt = float(np.median(np.diff(self.t)))
        self.v_world = savgol_filter(self.S_world, 7, 2, deriv=1, delta=dt)
        self.v_world = np.maximum(self.v_world, 0.0)
        self.v_decl = c["speed_ms"]

        # --- wheel angular speed ---------------------------------------------
        # `wheel_rot_rad` carries the launch wheelspin as an accumulating excess
        # (2.222 -> 9.660 rad over frames 0-9) and then RESETS to the rolling
        # angle at frame 10. The reset is a discontinuity in the column, not in
        # the wheel. Its derivative is repaired by dropping the two samples that
        # straddle the reset and interpolating across them.
        wr = c["wheel_rot_rad"]
        w = np.gradient(wr, self.t)
        bad = np.flatnonzero(w < -1.0)
        if bad.size:
            lo, hi = int(bad.min()) - 1, int(bad.max()) + 2
            good = np.array([max(lo, 0), min(hi, w.shape[0] - 1)])
            w[good[0] + 1:good[1]] = np.interp(
                np.arange(good[0] + 1, good[1]), good, w[good])
        self.wheel_w = w                                  # rad/s
        self.wheel_surface_v = w * WHEEL_R
        self.reset_indices = bad.tolist()

        # slip ratio, and the clutch lock it implies
        denom = np.maximum(np.maximum(self.wheel_surface_v, self.v_world), 1e-3)
        self.slip = np.clip((self.wheel_surface_v - self.v_world) / denom, 0.0, 1.0)
        self.wheelspin = c["wheelspin"]

        # --- the R2-026 measurement, kept as data -----------------------------
        m = c["s_m"] < 12.0
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(self.v_decl > 0.3, self.v_world / self.v_decl, np.nan)
        far = c["s_m"] > 20.0
        self.r2026 = {
            "declared_total_s_m": float(c["s_m"][-1]),
            "walked_world_arc_m": float(self.S_world[-1]),
            "global_ratio": float(self.S_world[-1] / c["s_m"][-1]),
            "x_over_s_launch_median": float(np.median(
                (c["x"] / np.maximum(c["s_m"], 1e-9))[(c["s_m"] > 0.5) & (c["s_m"] < 11.9)])),
            "launch_rows": int(m.sum()),
            "max_speed_ratio_launch": float(np.nanmax(ratio[m])),
            "max_speed_error_pct_launch": float((np.nanmax(ratio[m]) - 1.0) * 100.0),
            "semitones_error_at_worst": float(12.0 * math.log2(np.nanmax(ratio[m]))),
            "ratio_at_glass": float(np.interp(11.98, c["s_m"], self.v_world)
                                    / np.interp(11.98, c["s_m"], self.v_decl)),
            "p99_abs_ratio_error_past_20m": float(np.nanpercentile(np.abs(ratio[far] - 1.0), 99)),
            "implied_wheel_radius_m": float(np.median(
                np.gradient(c["s_m"], self.t)[200:1700] / np.gradient(wr, self.t)[200:1700])),
            "seam_v_world_step_ms2": float(np.min(np.diff(self.v_world[40:55]) * 24.0)),
        }

        # --- centreline continuation past the end of the CSV ------------------
        self._cl = None
        if spec is not None:
            import sys
            anim = os.path.join(ROOT, "anim")
            if anim not in __import__("sys").path:
                sys.path.insert(0, anim)
            import carpath
            self._cl = np.array(carpath.centreline_table(spec, 1.0))
            self._lap = float(spec["headline"]["length_m"])
            # THE LAP-DOWN (R2-943). The audio must walk the same table the
            # camera rig and the car's keys walk, or the engine will be at
            # 323 km/h under a car that has stopped. `t_brake` is derived the
            # same way `carpath.Car` derives it: the line crossing, not the
            # end of the CSV.
            #
            # WHICH v_end SEEDS IT (R2-955). Not `v_world[-1]`. R2-026's rule is
            # "follow the car the AUDIENCE sees", and past the end of the CSV the
            # car the audience sees is not differentiated from a position track --
            # its position IS `LapDown`'s distance along the centreline, and
            # `anim/carpath.Car` seeds that table from the CSV's `speed_ms[-1]`.
            # Seeding a second table from `v_world[-1]` instead put the audio's
            # car 2.349 mm from the picture's at f2936 for no gain. The same rule
            # that makes the engine follow `v_world` ON the telemetry makes it
            # follow the lap-down's own v PAST it, because there the lap-down is
            # what the picture is drawn from.
            #
            # Cost, stated: the two seeds differ by 0.955 mm/s, so `speed` steps
            # by that much at `t_end` -- 1.1e-5 relative, i.e. 1.8e-4 cents of
            # engine pitch and 1.4e-4 dB of tyre level, under a 90 ms driveline
            # lag. The A-side (`F1_LAPDOWN=0`) is untouched: with no lap-down,
            # `_extrap` still uses the `vend` `sample()` passes it, which is the
            # pre-R2-943 `v_world[-1]`.
            self._carpath = carpath
            self._lapdown = None
            self.v_extrap = float(self.v_world[-1])
            if carpath.LAPDOWN_ENABLED:
                self.v_extrap = float(self.col["speed_ms"][-1])
            s_to_line = self._lap - ((float(self.col["s_m"][-1])
                                      - SF_TELEMETRY_S) % self._lap)
            self.t_brake = self.t_end + s_to_line / self.v_extrap
            if carpath.LAPDOWN_ENABLED:
                self._lapdown = carpath.LapDown(self.v_extrap)

    # ------------------------------------------------------------- sampling --
    def sample(self, wt, speed_source="v_world"):
        """Car state at world time(s) `wt`.

        Returns dict of arrays: pos (N,3), heading, speed, accel_long, curvature,
        steer, wheel_w, slip, s_m (telemetry station), track_s.
        Before t=0 the car is parked on the dais; past the end of the CSV it is
        continued along the circuit centreline at its final speed, exactly as
        `anim/carpath.Car.state` does, so the audio and the camera rig agree
        about where the car is in beat 6.
        """
        wt = np.asarray(wt, dtype=np.float64)
        c = self.col
        tc = np.clip(wt, 0.0, self.t_end)
        out = {}
        v = self.v_world if speed_source == "v_world" else self.v_decl
        for name, arr in (("x", c["x"]), ("y", c["y"]), ("z", c["z"]),
                          ("heading", c["heading_rad"]), ("speed", v),
                          ("accel_long", c["accel_long_ms2"]),
                          ("accel_lat", c["accel_lat_ms2"]),
                          ("curvature", c["curvature"]), ("steer", c["steer_norm"]),
                          ("wheel_w", self.wheel_w), ("slip", self.slip),
                          ("wheelspin", self.wheelspin), ("s_m", c["s_m"])):
            out[name] = np.interp(tc, self.t, arr)
        out["speed"] = np.where(wt < 0.0, 0.0, out["speed"])
        out["slip"] = np.where(wt < 0.0, 0.0, out["slip"])
        out["wheel_w"] = np.where(wt < 0.0, 0.0, out["wheel_w"])

        past = wt > self.t_end
        if past.any() and self._cl is not None:
            # ONE seed for the whole continuation -- see R2-955 in __init__. With
            # the lap-down off this is the pre-R2-943 `v[-1]` of the chosen
            # speed source, exactly.
            vend = self.v_extrap if self._lapdown is not None else float(v[-1])
            wp = wt[past]
            d, vv, aa = self._extrap(wp, vend)
            s = float(c["s_m"][-1]) + d
            ts = (s - SF_TELEMETRY_S) % self._lap
            px, py, pz, hh = self._cl_at(ts)
            out["x"][past], out["y"][past], out["z"][past] = px, py, pz
            out["heading"][past] = hh
            out["speed"][past] = vv
            # LONGITUDINAL ACCELERATION ACROSS THE LIFT (R2-953).
            # `-aa` alone puts a STEP at t_end: the CSV's last row is
            # +1.5073 m/s^2 (the car is flat out) and the lap-down's flat-out
            # segment is a CONSTANT SPEED, so accel_long jumped 1.5073 -> 0.000
            # in one sample. `engine.throttle_from_spec` reads accel_long
            # directly, so that step is a 0.74 dB one-sample step on the
            # combustion gate 46 ms before the beat-5/beat-6 seam -- a click, and
            # a claim that the driver lifted before the line.
            #
            # The handover is made over THE FLAT-OUT SEGMENT ITSELF -- t_end to
            # t_brake, 46.2 ms, the 4.15 m the telemetry stops short of the line
            # -- and not over the lap-down's 0.30 s onset. Both remove the step;
            # only this one keeps `accel_long` equal to d(speed)/dt once the
            # driver has lifted. Blending over the onset instead left
            # accel_long at +0.796 m/s^2 at f2715, 23 ms AFTER the lift, while
            # the speed track the same call returns was already falling: two
            # fields of one sample disagreeing about which way the car is going.
            # Past t_brake this is exactly `-aa`.
            if self._lapdown is not None:
                a_flat = float(c["accel_long_ms2"][-1])
                s_on = np.clip((wp - self.t_end)
                               / max(self.t_brake - self.t_end, 1e-9), 0.0, 1.0)
                s_on = s_on * s_on * (3.0 - 2.0 * s_on)
                out["accel_long"][past] = a_flat * (1.0 - s_on) - aa
            out["s_m"][past] = s
            # rolling contact: scale the last wheel rate by the speed ratio
            # rather than dividing by a wheel radius this file does not own.
            out["wheel_w"][past] = float(self.wheel_w[-1]) * (vv / vend)
        out["pos"] = np.stack([out["x"], out["y"], out["z"]], axis=1)
        out["track_s"] = out["s_m"] - SF_TELEMETRY_S
        return out

    def _extrap(self, wt, vend):
        """(distance since t_end, speed, deceleration) past the telemetry.

        Vectorised twin of `anim/carpath.Car._extrap`, reading the SAME
        `carpath.LapDown` table, so the audio's car and the picture's car are one
        object. Verified against it frame by frame in `verify.py`.
        """
        dt = wt - self.t_end
        if self._lapdown is None:
            return vend * dt, np.full_like(dt, vend), np.zeros_like(dt)
        d = vend * dt
        vv = np.full_like(dt, vend)
        aa = np.zeros_like(dt)
        m = wt > self.t_brake
        if m.any():
            ld = self._lapdown
            d0 = vend * (self.t_brake - self.t_end)
            u = np.clip((wt[m] - self.t_brake) / ld.dt, 0.0, len(ld.d) - 1.0001)
            i = u.astype(np.int64)
            f = u - i
            D = np.asarray(ld.d); V = np.asarray(ld.v); A = np.asarray(ld.a)
            d[m] = d0 + D[i] + (D[i + 1] - D[i]) * f
            vv[m] = V[i] + (V[i + 1] - V[i]) * f
            aa[m] = A[i] + (A[i + 1] - A[i]) * f
        return d, vv, aa

    def _cl_at(self, ts):
        S, CX, CY, CZ, H = self._cl.T
        i = np.clip(np.searchsorted(S, ts), 1, S.shape[0] - 1)
        a = (ts - S[i - 1]) / np.maximum(S[i] - S[i - 1], 1e-9)
        dh = (H[i] - H[i - 1] + math.pi) % (2 * math.pi) - math.pi
        return (CX[i - 1] + (CX[i] - CX[i - 1]) * a,
                CY[i - 1] + (CY[i] - CY[i - 1]) * a,
                CZ[i - 1] + (CZ[i] - CZ[i - 1]) * a,
                H[i - 1] + dh * a)


# ------------------------------------------------------------------ camera ----
class CameraPath:
    """The LISTENER. 2,978 keyed samples of position, orientation and lens.

    Blender camera convention: the lens looks down local -Z, local +Y is up,
    local +X is right. The two ears are placed at +/- 0.0875 m along local +X,
    which is the standard interaural half-distance; putting them on the CAMERA's
    right rather than on world +X is what makes a roll audible.
    """

    EAR_HALF = 0.0875

    def __init__(self, path_json=None, fps=24):
        # R2-1705.  THE DEFAULT USED TO BE `world/camera_rig_path.json`, WHICH IS
        # NOT THE FILM'S CAMERA.  That file is an orphan of a retired build
        # script -- `anim/build_camera_rig.py` names its output
        # `splitext(--out)[0] + "_path.json"`, so the name is a side effect of an
        # argument and no build step owns it.  It sat byte-identical to
        # `film16_path.json` for three days while the film had moved on, and
        # `audio/master.py` built the LISTENER from it by calling CameraPath()
        # with no argument at all.
        #
        # The listener being on the wrong camera is not a subtle error: over
        # beat 1 the two paths differ by up to 9.866 m and 103.3 deg, which puts
        # the binaural image on the WRONG EAR for 318 of 792 frames (azimuth
        # error max 178.1 deg) and the level p50 2.19 dB out.  Beats 2-6 are
        # unaffected -- the two curves converge to exactly zero at f754, which
        # is beat 1's last camera key.
        #
        # `live_campath.load()` takes no path argument, so the wrong file is
        # unreachable rather than merely detectable, and it checks the
        # declaration's sha256 -- a rebuild that changes the camera without
        # announcing it RAISES here instead of being adopted silently.
        # An explicit `path_json` is still honoured for A/Bs and controls.
        if path_json is None:
            _tools = os.path.join(ROOT, "tools")
            if _tools not in sys.path:
                sys.path.insert(0, _tools)
            from live_campath import load as _load_live
            d = _load_live()
        else:
            d = json.load(open(path_json))
        self.frames = int(d["frames"])
        p = d["path"]
        self.P = np.array([q["p"] for q in p], dtype=np.float64)
        self.Q = np.array([q["q"] for q in p], dtype=np.float64)   # (w,x,y,z)
        self.lens = np.array([q["lens"] for q in p], dtype=np.float64)
        self.fps = fps
        self.frame_t = (np.arange(self.frames) + 1.0) / fps - 1.0 / fps   # frame f at (f-1)/fps

        # continuous position, PCHIP per component
        self._px = [PchipInterpolator(self.frame_t, self.P[:, k]) for k in range(3)]

        # orientation: hemisphere-align the quaternions once so nlerp is safe,
        # then interpolate the three basis vectors directly (they are what the
        # panner needs, and re-normalising them is cheaper than a slerp).
        Q = self.Q.copy()
        for i in range(1, Q.shape[0]):
            if np.dot(Q[i], Q[i - 1]) < 0:
                Q[i] = -Q[i]
        R = _quat_to_matrix(Q)                     # (N,3,3) columns = local x,y,z
        self._pr = [[PchipInterpolator(self.frame_t, R[:, r, c]) for c in range(3)]
                    for r in range(3)]
        self._plens = PchipInterpolator(self.frame_t, self.lens)

    def at(self, tau):
        """(pos (N,3), basis (N,3,3), lens) at film time tau."""
        # clamp: the film runs 1/fps past the last key (beat 6 holds a composed
        # frame), and a cubic extrapolation there would be an invented camera.
        tau = np.clip(np.asarray(tau, dtype=np.float64),
                      self.frame_t[0], self.frame_t[-1])
        pos = np.stack([f(tau) for f in self._px], axis=1)
        R = np.stack([np.stack([self._pr[r][c](tau) for c in range(3)], axis=1)
                      for r in range(3)], axis=1)
        # re-orthonormalise (PCHIP per element does not preserve SO(3))
        ex = R[:, :, 0]; ez = R[:, :, 2]
        ez = ez / np.linalg.norm(ez, axis=1, keepdims=True)
        ex = ex - ez * np.sum(ex * ez, axis=1, keepdims=True)
        ex = ex / np.linalg.norm(ex, axis=1, keepdims=True)
        ey = np.cross(ez, ex)
        R = np.stack([ex, ey, ez], axis=2)
        return pos, R, self._plens(tau)

    def ears(self, tau):
        pos, R, _ = self.at(tau)
        right = R[:, :, 0] * self.EAR_HALF
        return pos - right, pos + right, pos, R


def _quat_to_matrix(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    n = np.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    R = np.empty((q.shape[0], 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - z * w); R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w); R[:, 2, 1] = 2 * (y * z + x * w); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


# ----------------------------------------------------------------- surfaces ---
# Boundaries are DECLARED geometry, read from docs/circuit_spec.json:
#   dais deck        x <  3.70            (dais radius 3.70, deck top z 0.34)
#   delivery ramp    3.70 <= x <  6.30    (0.340 m rise over 2.60 m, 13.1 %)
#   showroom floor   6.30 <= x < 15.00    (polished concrete, mu_derate 0.85)
#   glass debris     15.00 <= x < x_deb   (extent from the shard ballistics)
#   apron concrete   x_deb <= x < 64.60   ("apron run (flat, unrubbered)")
#   access asphalt   merge arc + pit-straight approach  (mu_derate 0.90)
#   circuit asphalt  from the start/finish line onward  (mu_derate 1.00)
#   painted line     a 0.50 m band at every start/finish crossing
#   kerb             |lateral offset| inside the kerb band -- see below
SURFACES = ("dais", "ramp", "showroom_floor", "glass_debris", "apron",
            "access_road", "asphalt", "paint", "kerb", "gravel")


def half_width_at(spec, track_s):
    """Half track width (m) at a station, from the spec's section table."""
    sec = spec["track_section"]
    els = spec["elements"]
    s0 = np.array([e["s_start"] for e in els])
    names = [e["name"] for e in els]
    w = np.empty_like(np.asarray(track_s, dtype=np.float64))
    idx = np.clip(np.searchsorted(s0, np.asarray(track_s) % spec["headline"]["length_m"],
                                  side="right") - 1, 0, len(els) - 1)
    full = np.empty(len(els))
    for i, nm in enumerate(names):
        if "pit straight" in nm:
            full[i] = sec["pit_straight_m"]
        elif nm.startswith("T4"):
            full[i] = sec["hairpin_m"]
        elif nm[:2] in ("T6", "T7", "T8", "T9") or "esse" in nm:
            full[i] = sec["esses_m"]
        else:
            full[i] = sec["standard_m"]
    w[...] = full[idx] * 0.5
    return w


def classify(spec, pos, track_s, lateral, debris_end_x):
    """Fractional surface mix per sample. Rows sum to 1.

    Transitions are cross-faded over one wheelbase of travel so a boundary is a
    3.6 m event, not a sample-accurate switch -- because the front and rear
    contact patches really are 3.6 m apart and really do cross a joint at
    different times.
    """
    x = pos[:, 0]
    n = x.shape[0]
    f = {k: np.zeros(n, dtype=np.float64) for k in SURFACES}

    inside = pos[:, 1] > -1e9  # all samples; the showroom legs are x-ordered
    ramp_w = WHEELBASE

    def band(lo, hi):
        """smooth 0..1..0 indicator of x in [lo, hi) with wheelbase edges."""
        a = np.clip((x - lo) / ramp_w + 0.5, 0.0, 1.0)
        b = np.clip((hi - x) / ramp_w + 0.5, 0.0, 1.0)
        return np.minimum(a, b)

    on_road = track_s >= 0.0            # past the start/finish line
    f["dais"] = band(-1e6, 3.70)
    f["ramp"] = band(3.70, 6.30)
    f["showroom_floor"] = band(6.30, 15.00)
    f["glass_debris"] = band(15.00, debris_end_x)
    f["apron"] = band(debris_end_x, 64.60)

    # after the merge arc the car is on the access road, then on the circuit.
    # Both are keyed off track_s, which is negative until the line.
    acc = np.clip((track_s + SF_TELEMETRY_S - 169.3) / 20.0, 0.0, 1.0) * \
        np.clip(-track_s / 20.0 + 1.0, 0.0, 1.0)
    f["access_road"] = np.where(x > 64.6, acc, 0.0)
    f["asphalt"] = np.clip(track_s / 20.0, 0.0, 1.0) * (x > 64.6)

    # painted start/finish line: a 0.50 m band, crossed at track_s = 0 and 3675
    lap = spec["headline"]["length_m"]
    for line_s in (0.0, lap):
        d = np.abs(track_s - line_s)
        f["paint"] += np.clip(1.0 - d / 0.25, 0.0, 1.0)

    # kerb: |lateral| between the track edge and the track edge + kerb width
    hw = half_width_at(spec, np.maximum(track_s, 0.0))
    kw = spec["track_section"]["kerb"]["width_m"]
    al = np.abs(lateral)
    onk = np.clip((al - hw) / 0.15, 0.0, 1.0) * np.clip((hw + kw - al) / 0.15, 0.0, 1.0)
    f["kerb"] = np.where(on_road, onk, 0.0)
    # gravel: beyond the kerb where a gravel trap is declared
    f["gravel"] = np.where(on_road, np.clip((al - hw - kw) / 0.5, 0.0, 1.0), 0.0)
    # A CONTACT PATCH IS ON ONE SURFACE AT A TIME. Kerb and gravel are OFF the
    # asphalt, so they displace it instead of adding to it. Without this the
    # positive control -- a track deliberately run 0.75 m onto the kerb --
    # normalised to a 50/50 kerb/asphalt mix and the gate read it as no kerb at
    # all, which is a gate that could not have failed.
    off_track = np.clip(f["kerb"] + f["gravel"], 0.0, 1.0)
    f["asphalt"] = f["asphalt"] * (1.0 - off_track)
    f["access_road"] = f["access_road"] * (1.0 - off_track)

    tot = np.zeros(n)
    for k in SURFACES:
        f[k] = np.maximum(f[k], 0.0)
        tot += f[k]
    tot = np.maximum(tot, 1e-9)
    for k in SURFACES:
        f[k] /= tot
    return f


def lateral_offsets(spec, pos):
    """Signed lateral offset from the circuit centreline, and the station.

    Same element walk as `anim/carpath.centreline_table` -- imported, not
    re-derived, because two files disagreeing about where the track is would be
    worse than either being wrong.
    """
    import sys
    anim = os.path.join(ROOT, "anim")
    if anim not in sys.path:
        sys.path.insert(0, anim)
    import carpath
    tab = np.array(carpath.centreline_table(spec, 1.0))
    S, CX, CY, CZ, H = tab.T
    lat = np.empty(pos.shape[0])
    st = np.empty(pos.shape[0])
    CH, SH = np.cos(H), np.sin(H)
    step = 40000
    for a in range(0, pos.shape[0], step):
        b = min(a + step, pos.shape[0])
        dx = pos[a:b, 0][:, None] - CX[None, :]
        dy = pos[a:b, 1][:, None] - CY[None, :]
        j = (dx * dx + dy * dy).argmin(1)
        ddx = pos[a:b, 0] - CX[j]; ddy = pos[a:b, 1] - CY[j]
        lat[a:b] = -ddx * SH[j] + ddy * CH[j]
        st[a:b] = S[j] + ddx * CH[j] + ddy * SH[j]
    return lat, st
