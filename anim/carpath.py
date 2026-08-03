"""THE CAR, sampled — one implementation, imported by the author and the gate.

Standard library only: `tools/author_beats2_5.py` runs under the project venv
and `anim/build_camera_rig.py` runs inside Blender, and if they disagreed about
where the car is then the gate would be measuring the author's opinion instead
of the film. Extracted from the authoring tool for exactly that reason.
"""

import bisect
import csv
import math

# The car, measured (MASTER-PLAN section 5): 5.698 x 2.005 m, 0.340 m ride height.
CAR_LEN = 5.698
CAR_HALF_LEN = CAR_LEN / 2.0
CAR_HALF_W = 2.005 / 2.0
CAR_TOP_Z = 0.992

# Telemetry station of the start/finish line, so track s = telemetry s - this.
SF_TELEMETRY_S = 381.88


# ---------------------------------------------------------------- telemetry --
class Car:
    """The car's world state at any WORLD time, from the one source of truth.

    Past the end of the telemetry (world t > 72.583, i.e. film t > 113.06) the
    car has crossed the line and the CSV stops. It is continued along the
    circuit's own centreline at its final speed rather than in a straight line,
    because "the car streaking on" in beat 6 streaks into T1, not into the
    terrain 990 m off the outside of the corner.
    """

    def __init__(self, csv_path, spec):
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

    def _lerp(self, arr, t):
        i = bisect.bisect_left(self.t, t)
        i = min(max(i, 1), len(self.t) - 1)
        a = (t - self.t[i - 1]) / (self.t[i] - self.t[i - 1])
        return arr[i - 1] + (arr[i] - arr[i - 1]) * a

    def state(self, t):
        """(pos, heading_rad, speed) at world time t. t<=0 parks it on the dais."""
        if t <= 0.0:
            return ([self.x[0], self.y[0], self.z[0]], self.h[0], 0.0)
        if t <= self.t_end:
            return ([self._lerp(self.x, t), self._lerp(self.y, t),
                     self._lerp(self.z, t)], self._lerp(self.h, t),
                    self._lerp(self.v, t))
        # extrapolate along the centreline, wrapping the lap
        v = self.v[-1]
        s = self.s[-1] + v * (t - self.t_end)
        track_s = (s - SF_TELEMETRY_S) % self.spec["headline"]["length_m"]
        p, hd = cl_at(self._cl, track_s)
        return ([p[0], p[1], p[2]], hd, v)

    def pos(self, t):
        return self.state(t)[0]

    def fwd(self, t):
        h = self.state(t)[1]
        return (math.cos(h), math.sin(h), 0.0)

    def track_s(self, t):
        """Distance round the lap, metres from the start/finish line."""
        if t <= self.t_end:
            return self._lerp(self.s, t) - SF_TELEMETRY_S
        return (self.s[-1] + self.v[-1] * (t - self.t_end)) - SF_TELEMETRY_S

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


