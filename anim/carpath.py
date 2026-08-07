"""THE CAR, sampled — one implementation, imported by the author and the gate.

Standard library only: `tools/author_beats2_5.py` runs under the project venv
and `anim/build_camera_rig.py` runs inside Blender, and if they disagreed about
where the car is then the gate would be measuring the author's opinion instead
of the film. Extracted from the authoring tool for exactly that reason.
"""

import bisect
import csv
import math
import os

# The car, measured (MASTER-PLAN section 5): 5.698 x 2.005 m, 0.340 m ride height.
CAR_LEN = 5.698
CAR_HALF_LEN = CAR_LEN / 2.0
CAR_HALF_W = 2.005 / 2.0
CAR_TOP_Z = 0.992

# Telemetry station of the start/finish line, so track s = telemetry s - this.
SF_TELEMETRY_S = 381.88


# ---------------------------------------------------------------- lap-down --
# THE LAP IS OVER AT THE LINE, AND THE CAR BEHAVES LIKE IT.
#
# The telemetry stops 4.15 m short of the start/finish line on the car's second
# crossing (world t 72.5833, track s 3670.85 of a 3675.0 m lap). Everything after
# that is authored, and what is authored is the lap-down: the driver crosses the
# line, lifts, brakes, and comes to rest on the pit straight. Deceleration is
# grip-limited and an F1 car's grip is aero-assisted, so it falls with speed:
#
#     a(v) = [ A_ROLL + (A_BRAKE + K_AERO * v^2) * smoothstep(v / V_RELEASE) ]
#            * smoothstep(dt / ONSET_S)
#
#   A_ROLL     rolling resistance and engine braking. It never vanishes, which is
#              what makes the car reach EXACTLY zero in finite time and stay there
#              rather than crawl asymptotically for the rest of the film.
#   A_BRAKE    the brake at low speed, where only mechanical grip is available.
#   K_AERO     the aero term: +30.6 m/s^2 at the 89.767 m/s (323.2 km/h) the car
#              crosses the line at, so peak deceleration is 3.60 g. An F1 car can
#              do 5-6 g there, so this is a firm lap-down brake and not a limit stop.
#   V_RELEASE  the brake is progressively released below 54 km/h; the last ~60 m
#              are a roll, which is how a car actually comes to a stand.
#   ONSET_S    the driver's foot. Deceleration eases in from zero, so there is no
#              acceleration step at the beat-5/beat-6 seam.
#
# The brake point is DERIVED, not chosen: it is the world time at which the car
# crosses the start/finish line, 72.62957 s. Film frame 2714 (the last frame of
# beat 5) is at world 72.61153 and frame 2715 (the first frame of beat 6) is at
# 72.65320, so the lift happens BETWEEN the two frames of the f2714/2715 seam.
# Beat 5 therefore ends with the car flat out and its last frame is unchanged to
# 0.000e+00 m, and the whole of the lap-down is inside beat 6.
LAPDOWN_A_ROLL = 1.2          # m/s^2
LAPDOWN_A_BRAKE = 7.0         # m/s^2
LAPDOWN_K_AERO = 0.0038       # 1/m
LAPDOWN_V_RELEASE = 15.0      # m/s
LAPDOWN_ONSET_S = 0.30        # s
LAPDOWN_DT = 5.0e-4           # s, the integration step
LAPDOWN_SPAN_S = 24.0         # s of table; the film needs 11.0

# A/B only. `F1_LAPDOWN=0` restores the pre-R2-943 constant-speed extrapolation so
# a control arm can be built from the same source. It is not a shipping switch and
# nothing on the ship path may read it.
LAPDOWN_ENABLED = os.environ.get("F1_LAPDOWN", "1") != "0"


def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


class LapDown:
    """Distance and speed at `dt` seconds past the brake point, from one table.

    Tabulated once at LAPDOWN_DT and interpolated, so every consumer — the camera
    rig's aim, the car's own keys, the wheel rotation and the audio — walks the
    identical curve. Two of them re-integrating it independently is exactly the
    class of disagreement `carpath.py` was extracted to prevent.
    """

    def __init__(self, v0, a_roll=None, a_brake=None, k_aero=None,
                 v_release=None, onset_s=None, dt=LAPDOWN_DT, span=LAPDOWN_SPAN_S):
        self.v0 = v0
        self.dt = dt
        self.a_roll = LAPDOWN_A_ROLL if a_roll is None else a_roll
        self.a_brake = LAPDOWN_A_BRAKE if a_brake is None else a_brake
        self.k_aero = LAPDOWN_K_AERO if k_aero is None else k_aero
        self.v_release = LAPDOWN_V_RELEASE if v_release is None else v_release
        self.onset_s = LAPDOWN_ONSET_S if onset_s is None else onset_s
        n = int(round(span / dt))
        self.d = [0.0] * (n + 1)
        self.v = [v0] * (n + 1)
        self.a = [0.0] * (n + 1)
        v, d = v0, 0.0
        for i in range(1, n + 1):
            a = self.accel_at_speed(v) * _smoothstep((i * dt) / self.onset_s)
            v = max(0.0, v - a * dt)
            d += v * dt
            self.d[i], self.v[i], self.a[i] = d, v, (a if v > 0.0 else 0.0)
        self.t_stop = next((i * dt for i, vv in enumerate(self.v) if vv <= 0.0), None)
        self.d_stop = self.d[int(self.t_stop / dt)] if self.t_stop is not None else None
        self.peak_a = max((self.v[i] - self.v[i + 1]) / dt for i in range(n))

    def accel_at_speed(self, v):
        return (self.a_roll
                + (self.a_brake + self.k_aero * v * v) * _smoothstep(v / self.v_release))

    def at(self, dt_s):
        """(distance travelled, speed, deceleration) `dt_s` seconds past the lift."""
        if dt_s <= 0.0:
            return 0.0, self.v0, 0.0
        i = int(dt_s / self.dt)
        if i >= len(self.d) - 1:
            return self.d[-1], self.v[-1], self.a[-1]
        a = (dt_s - i * self.dt) / self.dt
        return (self.d[i] + (self.d[i + 1] - self.d[i]) * a,
                self.v[i] + (self.v[i + 1] - self.v[i]) * a,
                self.a[i] + (self.a[i + 1] - self.a[i]) * a)


# ---------------------------------------------------------------- telemetry --
class Car:
    """The car's world state at any WORLD time, from the one source of truth.

    Past the end of the telemetry (world t > 72.583, i.e. film t > 113.06) the
    car has crossed the line and the CSV stops. It is continued along the
    circuit's own centreline rather than in a straight line, because "the car
    streaking on" in beat 6 streaks into T1, not into the terrain 990 m off the
    outside of the corner.

    It is NOT continued at its final speed. The flying lap ends at the line and
    the driver lifts: see the lap-down block above and `_extrap`. That change is
    R2-943 and it is what puts a subject in the film's last frame — a car held at
    89.767 m/s travels 913 m in the closing 11 s and finishes 1,000 m from the
    camera at 79 px wide, which R2-862 watched at 4K and called a smudge.
    """

    def __init__(self, csv_path, spec, lapdown=None):
        rows = list(csv.DictReader(open(csv_path)))
        self.t = [float(r["t_s"]) for r in rows]
        self.s = [float(r["s_m"]) for r in rows]
        self.x = [float(r["x"]) for r in rows]
        self.y = [float(r["y"]) for r in rows]
        self.z = [float(r["z"]) for r in rows]
        self.v = [float(r["speed_ms"]) for r in rows]
        self.h = [float(r["heading_rad"]) for r in rows]
        self.t_end = self.t[-1]
        self.spec = spec
        self._cl = centreline_table(spec, 2.0)
        self.lap_m = float(spec["headline"]["length_m"])

        # The lift happens when the car crosses the line, not when the CSV runs
        # out: the telemetry stops 4.15 m short of it.
        s_to_line = self.lap_m - ((self.s[-1] - SF_TELEMETRY_S) % self.lap_m)
        self.t_brake = self.t_end + s_to_line / self.v[-1]
        if lapdown is None:
            lapdown = LapDown(self.v[-1]) if LAPDOWN_ENABLED else None
        self.lapdown = lapdown

    def _lerp(self, arr, t):
        i = bisect.bisect_left(self.t, t)
        i = min(max(i, 1), len(self.t) - 1)
        a = (t - self.t[i - 1]) / (self.t[i] - self.t[i - 1])
        return arr[i - 1] + (arr[i] - arr[i - 1]) * a

    def _extrap(self, t):
        """(metres of centreline covered since `t_end`, speed, deceleration).

        The one place the post-telemetry motion is defined. Flat out to the line,
        then the lap-down. With `LAPDOWN_ENABLED` false this is the pre-R2-943
        `v[-1] * dt` and nothing else, exactly.
        """
        dt = t - self.t_end
        if self.lapdown is None:
            return self.v[-1] * dt, self.v[-1], 0.0
        if t <= self.t_brake:
            return self.v[-1] * dt, self.v[-1], 0.0
        d0 = self.v[-1] * (self.t_brake - self.t_end)
        d, v, a = self.lapdown.at(t - self.t_brake)
        return d0 + d, v, a

    def state(self, t):
        """(pos, heading_rad, speed) at world time t. t<=0 parks it on the dais."""
        if t <= 0.0:
            return ([self.x[0], self.y[0], self.z[0]], self.h[0], 0.0)
        if t <= self.t_end:
            return ([self._lerp(self.x, t), self._lerp(self.y, t),
                     self._lerp(self.z, t)], self._lerp(self.h, t),
                    self._lerp(self.v, t))
        # extrapolate along the centreline, wrapping the lap
        d, v, _a = self._extrap(t)
        s = self.s[-1] + d
        track_s = (s - SF_TELEMETRY_S) % self.lap_m
        p, hd = cl_at(self._cl, track_s)
        return ([p[0], p[1], p[2]], hd, v)

    def decel(self, t):
        """Longitudinal deceleration, m/s^2, positive when slowing. 0 on telemetry."""
        if t <= self.t_end:
            return 0.0
        return self._extrap(t)[2]

    def pos(self, t):
        return self.state(t)[0]

    def fwd(self, t):
        h = self.state(t)[1]
        return (math.cos(h), math.sin(h), 0.0)

    def track_s(self, t):
        """Distance round the lap, metres from the start/finish line."""
        if t <= self.t_end:
            return self._lerp(self.s, t) - SF_TELEMETRY_S
        return (self.s[-1] + self._extrap(t)[0]) - SF_TELEMETRY_S

    def t_at_track_s(self, track_s):
        target = track_s + SF_TELEMETRY_S
        i = bisect.bisect_left(self.s, target)
        i = min(max(i, 1), len(self.s) - 1)
        a = (target - self.s[i - 1]) / (self.s[i] - self.s[i - 1])
        return self.t[i - 1] + (self.t[i] - self.t[i - 1]) * a

    def frame_at_track_s(self, track_s, world_of_frame):
        """First film frame whose world time puts the car at or past `track_s`."""
        wt = self.t_at_track_s(track_s)
        for f in range(1, len(world_of_frame)):
            if world_of_frame[f] >= wt:
                return f
        return len(world_of_frame) - 1

    def line(self, t):
        """The car's centre segment: (rear_point, front_point). Used for the
        'is the camera inside the car' test — a point test on the reference
        point alone would miss the nose entirely."""
        p, h, _ = self.state(t)
        f = (math.cos(h), math.sin(h), 0.0)
        rear = [p[i] - f[i] * CAR_HALF_LEN for i in range(3)]
        front = [p[i] + f[i] * CAR_HALF_LEN for i in range(3)]
        return rear, front


# --------------------------------------------------------------- centreline --
def centreline_table(spec, step):
    """(s, x, y, z, heading) every `step` metres, straight off the spec elements.

    Same element walk as `tools/placement_gate.road_samples`, deliberately: two
    files disagreeing about where the track is would be worse than either being
    wrong. Elevation comes from the spec's PVI table.
    """
    pvi = spec["elevation"]["station_z_pvi"]
    ps = [float(p["s"]) for p in pvi]
    pz = [float(p["z"]) for p in pvi]

    def zof(s):
        i = bisect.bisect_left(ps, s)
        if i <= 0:
            return pz[0]
        if i >= len(ps):
            return pz[-1]
        a = (s - ps[i - 1]) / (ps[i] - ps[i - 1])
        return pz[i - 1] + (pz[i] - pz[i - 1]) * a

    out = []
    for el in spec["elements"]:
        x0, y0 = el["start_world"][0], el["start_world"][1]
        h0 = math.radians(el["heading_world_deg"])
        L, s0 = el["length_m"], el["s_start"]
        n = max(int(L / step), 1)
        R = el.get("radius_m")
        turn = el.get("turn_deg")
        for i in range(n):
            d = i * L / n
            if el["type"] == "S" or not R:
                x, y, h = x0 + math.cos(h0) * d, y0 + math.sin(h0) * d, h0
            else:
                sign = 1.0 if (turn or 0) >= 0 else -1.0
                h = h0 + sign * d / R
                cx = x0 - sign * R * math.sin(h0)
                cy = y0 + sign * R * math.cos(h0)
                x = cx + sign * R * math.sin(h)
                y = cy - sign * R * math.cos(h)
            s = s0 + d
            out.append((s, x, y, zof(s), h))
    return out


def cl_at(table, s):
    ss = [r[0] for r in table]
    i = bisect.bisect_left(ss, s)
    i = min(max(i, 1), len(table) - 1)
    a = (s - ss[i - 1]) / max(ss[i] - ss[i - 1], 1e-9)
    r0, r1 = table[i - 1], table[i]
    p = [r0[1] + (r1[1] - r0[1]) * a,
         r0[2] + (r1[2] - r0[2]) * a,
         r0[3] + (r1[3] - r0[3]) * a]
    dh = (r1[4] - r0[4] + math.pi) % (2 * math.pi) - math.pi
    return p, r0[4] + dh * a


def lateral_of(table, p):
    """(signed lateral offset from the centreline, station s) for a world point.

    Positive is LEFT of the racing direction. Coarse nearest-sample search then
    a local projection — the table is 2 m, so the projection is what carries the
    accuracy.
    """
    best = None
    for (s, x, y, z, h) in table:
        d2 = (p[0] - x) ** 2 + (p[1] - y) ** 2
        if best is None or d2 < best[0]:
            best = (d2, s, x, y, h)
    _d2, s, x, y, h = best
    dx, dy = p[0] - x, p[1] - y
    along = dx * math.cos(h) + dy * math.sin(h)
    lat = -dx * math.sin(h) + dy * math.cos(h)
    return lat, s + along


