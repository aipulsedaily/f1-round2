"""THE CAR'S POSE — body and wheels — at any WORLD time. One implementation.

Imported by `anim/build_car_anim.py` (which runs inside Blender and writes the
keys) and by `tools/car_anim_gate.py` (which runs under the project venv and
measures them).  Extracted for the same reason `anim/carpath.py` was: the author
and the gate must not each have an opinion about where the car is.

WHAT THIS ADDS TO `carpath.Car`, AND WHAT IT DELIBERATELY DOES NOT
-----------------------------------------------------------------
`carpath.Car` already answers "where is the car, which way is it pointing, how
fast is it going" and is read by the camera rig AND the audio.  **Nothing here
recomputes any of those three.**  `pose()` calls `Car.state()` for x, y and
heading exactly as the camera does, so the car cannot end up somewhere the lens
is not looking.

What is added is the rest of a car:

  * WHEEL ROTATION      `wheel_rot_rad`, offset so it is ZERO at world t = 0
  * STEER               Ackermann from the telemetry's own curvature column
  * BODY PITCH / ROLL   `pitch_rad` / `roll_rad` (dive-squat and lateral lean)
  * THE GROUND          the height and attitude of the road UNDER THE FOUR
                        CONTACT PATCHES, which the telemetry does not carry

THE GROUND, AND WHY THE Z COLUMN IS NOT ENOUGH
----------------------------------------------
`telemetry.csv`'s `z` is the CENTRELINE elevation from the spec's PVI table.  It
is a height, and a car needs a plane: a height alone cannot say that the car is
nose-up 2.98 deg climbing La Rampe's 5.2 % grade, or leaning with a banked
corner.  Worse, three separate places disagree with it by construction:

  1. THE DAIS.  Beat 1 ends with the car seated on `Turntable_Deck`, top
     z = +0.340 (measured on the blend; `circuit_spec.showroom.dais.deck_top_z`
     declares the same number).  The telemetry's z is 0.0000 at t = 0.  Driving
     the car straight off the z column therefore drops it 340 mm through the
     deck on the first frame of beat 2 — a hard cut in a film that has none.
     `circuit_spec.showroom.dais.delivery_ramp` is the sanctioned answer:
     "0.340 m rise over 2.60 m (13.1 %), full 3.0 m width, from the dais lip
     X=+3.70 to X=+6.30".  It is modelled here as ground, and the wheels roll
     down it.

     NOTE FOR WHOEVER OWNS THE SHOWROOM: that ramp is DECLARED but NOT BUILT.
     `docs/item_manifest.md` carries it as item 13, `dais_delivery_ramp`, with
     the note "Without it the car steps off a 340 mm cliff at launch", and there
     is no `world/items/dais_delivery_ramp.py`.  The car is animated onto the
     declared profile, so the geometry can arrive later and match; until it does,
     the car rolls down an invisible slope.

  2. THE CROWN.  `world_contract.ground_z(s, 0)` is -0.0113 m at the
     start/finish line, not 0.0000: the racing surface is crowned and the
     centreline sits 11 mm below the z = 0 datum the pit straight is declared on.
     Measured against the whole lap the z column is out by a mean of +5 mm and a
     worst of -32 mm.  Small, and free to fix, because the road's own height
     function is importable.

  3. GRADE AND CAMBER.  Neither is a height at all.  They are the derivative of
     one, and they are what the car's attitude is made of.

So the vertical is resolved by a FOUR-WHEEL CONTACT SOLVE against
`world_contract.ground_z` — the same function `world/build_surface.py` builds the
road mesh from, so the car sits on the road that exists rather than on a second
opinion about where the road is.  x, y and heading are untouched.

WHAT THE CONTACT SOLVE DOES NOT INCLUDE, STATED
-----------------------------------------------
`build_surface.surface_z` = `ground_z` + a racing-line compaction dip of at most
`MICRO_LAYER_MAX_M` = 0.018 m.  That module imports `bpy` and cannot be loaded by
the gate, so the dip is not in the contact height.  It is a sub-2 cm surface
texture under a 0.72 m tyre; it is named here so its absence is a decision and
not an oversight.

Suspension travel is not modelled either: the contact solve is rigid, so a wheel
follows the ground exactly and the body follows the wheels exactly.  The
telemetry's own `pitch_rad` / `roll_rad` (+-1.6 deg / +-1.4 deg) are ADDED on top
as the compliance term, which is what they were built to be.

THE WHEELS ARE DRIVEN BY THE GROUND, NOT BY `s_m`.  READ THIS BEFORE CHANGING IT
--------------------------------------------------------------------------------
`wheel_rot_rad` is `s_m / 0.36` plus the sanctioned launch slip, and **`s_m` is
not the distance the car covers**.  R2-026, explained by R2-047 and still open:
leg 0's `length_m` (11.980 m) is measured from the car's NOSE to the glass while
its `from_world`/`to_world` are ORIGIN positions 15.000 m apart, so
`transit_path` stretches 11.980 m of arc length across 15.000 m of world X.
Measured on the shipped CSV, per leg, world displacement against `s_m`:

    leg 0  launch    world  14.7847 m    s_m  11.8080 m    ratio 1.25209
    leg 1  apron     world  49.5331 m    s_m  49.4898 m    ratio 1.00087
    leg 2  merge     world 104.5881 m    s_m 104.5693 m    ratio 1.00018
    leg 3  pit       world 214.5359 m    s_m 214.4634 m    ratio 1.00034

Leg 0 alone is out by **3.020 m — the car's nose offset, exactly**.  Driving the
wheels off `s_m` therefore turns them 3.020 / 0.36 = **8.39 rad (1.335
revolutions) too few over the 47 frames of the launch**, which is the same 47
frames in which the film sanctions its one and only wheelspin.  The two nearly
cancel: the declared slip is +9.14 rad, the drag is -8.39 rad, and a launch
authored off the column would show a net 0.75 rad of spin where 9.14 was
intended.  R2-047 records this consequence and declines to fix it in the
telemetry, because the honest fix moves the breach frame and with it beat 3's
ramp, `filmtime.GLASS_WORLD_T` and the 124.0833 s master.

**That fix is not needed to put rubber on road, and this file does not attempt
it.**  Nothing here moves the car: x, y and heading are `Car.state`'s, so the
breach still lands on frame 865 and the camera and the audio see the film they
were built against.  Only the WHEELS change, and they are driven by

    spin(t) = ground_distance(t) / WHEEL_RADIUS_M  +  slip(t)

where `ground_distance` is the arc length of the telemetry's OWN x/y/z polyline
— the same points `carpath.Car` hands the camera — and `slip` is the telemetry's
own declared departure from rolling contact, `wheel_rot_rad - s_m / r`, which is
flat everywhere outside the flagged `wheelspin` window and rises across it to
9.1399 rad.  So:

  * outside the window the tyres are in EXACT rolling contact with the ground
    the body actually covers, by construction, everywhere in the film;
  * the sanctioned wheelspin survives at its full declared 9.1399 rad;
  * the series is non-decreasing (a sum of two non-decreasing series).

THE SLIP IS SHIFTED ONE FRAME LATER, AND THAT IS THE WHOLE OF THE CHANGE TO IT
------------------------------------------------------------------------------
`slip` is **2.22222 rad at row 0**, before the car has moved at all: R2-041's
repair wrote `slip_accum = cumsum(slip_per_frame)`, so `slip_accum[0]` already
holds a whole frame's worth.  Keying that absolutely would stand beat 1's wheels
127 deg away from the pose round 1 modelled and beat 1 presents to camera, for
all 792 frames of the assembly.

So the knots are re-phased by one frame — `slip_rig[0] = 0`, `slip_rig[i] =
slip[i-1]` — which is the Riemann sum with the interval credited to its END
rather than its start.  `slip_rig` reaches the same 9.1399 rad on the same held
plateau; **no slip is discarded**, it simply starts from zero where the car
starts from rest.  `tools/car_anim_gate.py` re-measures both facts off the built
blend rather than taking this paragraph's word for it.
"""

import bisect
import csv
import math
import os
import sys

import numpy as np

_R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_R2, "anim"), os.path.join(_R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# UNGUARDED, like `tools/build_telemetry.py`'s import of the same module: a
# try/except fallback to a flat road would be a silent-plausible-data failure,
# and the car would sit 3.4 m under La Rampe with nothing saying so.
import world_contract as C                                       # noqa: E402
from carpath import Car, SF_TELEMETRY_S, centreline_table, cl_at  # noqa: E402


# ------------------------------------------------- the car, MEASURED, not read
# All five figures come from `world/beat1_anim.blend` at frame 792 (the seated
# pose), via the world bounding box of `wheel_tyre_<CORNER>_Tyre`, and every one
# of them is exact to 5 decimal places:
#
#   wheel centres   FL (+1.80000, +0.84750, 0.70000)   FR (+1.80000, -0.84750, ...)
#                   RL (-1.80000, +0.79750, 0.70000)   RR (-1.80000, -0.79750, ...)
#   tyre bbox z     0.34002 .. 1.06178, centre 0.70090
#
# The rolling radius is therefore 0.70000 - 0.34002 = 0.35998 m, and
# `tools/build_telemetry.py --wheel-radius` defaults to 0.36.  THE TELEMETRY'S
# WHEEL RADIUS AND THE MODELLED TYRE AGREE TO 0.02 mm.  That is not an assumption
# this file makes; it is a reconciliation `tools/car_anim_gate.py --selftest`
# re-measures off the blend.
AXLE_X_FRONT = +1.800
AXLE_X_REAR = -1.800
WHEELBASE_M = AXLE_X_FRONT - AXLE_X_REAR                    # 3.600
HALF_TRACK_FRONT = 0.84750
HALF_TRACK_REAR = 0.79750
MEAN_TRACK_M = HALF_TRACK_FRONT + HALF_TRACK_REAR           # 1.645
WHEEL_CENTRE_Z_LOCAL = 0.360        # above CAR_ROOT, == the rolling radius
WHEEL_RADIUS_M = 0.360

CORNERS = (("FL", AXLE_X_FRONT, +HALF_TRACK_FRONT, True),
           ("FR", AXLE_X_FRONT, -HALF_TRACK_FRONT, True),
           ("RL", AXLE_X_REAR, +HALF_TRACK_REAR, False),
           ("RR", AXLE_X_REAR, -HALF_TRACK_REAR, False))

# ---------------------------------------------------------------- the showroom
# `docs/circuit_spec.json` -> showroom.dais.  Read here rather than hardcoded so
# a change to the spec moves the car.
DECK_TOP_Z = 0.340
DAIS_LIP_X = 3.700
RAMP_FOOT_X = 6.300

# Past this telemetry station the showroom is behind the car and the ground is
# the declared flat apron.  The ramp foot is at x = 6.30 and the car's rear axle
# clears it at x = 8.10; 20 m is comfortably clear of both and comfortably short
# of the merge.
SHOWROOM_S_M = 20.0

# The transit's four legs are all declared `grade_pct: 0.0` from z = 0, and
# `world_contract.APRON_Z` is 0.000.  The lap's own surface at the line is
# -0.0113 m (the crown).  Tie the two over the last 30 m of the pit straight
# rather than stepping 11 mm at the start/finish line, which is precisely the
# frame R2-046 already makes people look at.
APRON_TIE_S_M = 30.0


def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def _ramp_ground(x):
    """The declared dais deck + delivery ramp, as a height along the launch axis.

    The launch leg runs dead straight from world (0, 0) to (15, 0), so the
    telemetry's station IS the world x here and no projection is needed.  The
    dais is a disc of radius 3.70 m and the car is on its diameter, so the lip
    the wheels cross is at x = +3.70.
    """
    if x <= DAIS_LIP_X:
        return DECK_TOP_Z
    if x >= RAMP_FOOT_X:
        return 0.0
    return DECK_TOP_Z * (RAMP_FOOT_X - x) / (RAMP_FOOT_X - DAIS_LIP_X)


def _wheel_envelope(x, r=WHEEL_RADIUS_M, n=241):
    """Contact height of a wheel of radius `r` rolling over `_ramp_ground`.

    A 0.72 m wheel does not follow a piecewise-linear ramp; it bridges the two
    convex breaks and cuts the concave one.  Sampling the ground's dilation by
    the wheel disc is the standard envelope and it costs nothing here, because it
    is only ever evaluated over the 6.2 m of showroom the ramp occupies.

    Without it the profile has four slope discontinuities, and differentiating a
    slope discontinuity twice is an infinite pitch acceleration on one frame —
    the class of defect this whole job exists to keep out of the seams.
    """
    best = -1e9
    for i in range(n):
        d = -r + 2.0 * r * i / (n - 1.0)
        h = _ramp_ground(x + d) + math.sqrt(max(r * r - d * d, 0.0))
        if h > best:
            best = h
    return best - r


def contact_z(x_world, s_tel, u):
    """Height of the ground under a contact patch.

    `x_world` is the patch's world X and is what the SHOWROOM branch uses, because
    the dais and its ramp are declared in world X and — see the header — world X
    and `s_m` run 25.2 % apart over exactly this span.  `s_tel` is the telemetry
    station of the patch, so `s_tel - SF_TELEMETRY_S` is the lap station, and it is
    what the ROAD branch uses because `world_contract.ground_z` is parameterised in
    (station, lateral).  `u` is positive to the LEFT of the racing direction.
    """
    if s_tel < SHOWROOM_S_M:
        return _wheel_envelope(x_world)
    track_s = (s_tel - SF_TELEMETRY_S) % C.LAP
    road = float(C.ground_z(track_s, u))
    if s_tel >= SF_TELEMETRY_S:
        return road
    # the transit's declared flat apron, tied into the crowned road at the line
    w = smoothstep((s_tel - (SF_TELEMETRY_S - APRON_TIE_S_M)) / APRON_TIE_S_M)
    return road * w


class CarRig:
    """Full rigid pose plus wheel state, at any world time."""

    def __init__(self, csv_path, spec):
        self.car = Car(csv_path, spec)
        rows = list(csv.DictReader(open(csv_path)))
        self.pitch_c = [float(r["pitch_rad"]) for r in rows]
        self.roll_c = [float(r["roll_rad"]) for r in rows]
        self.curv_c = [float(r["curvature"]) for r in rows]
        self.wheel_c = [float(r["wheel_rot_rad"]) for r in rows]
        self.s_c = [float(r["s_m"]) for r in rows]
        self.spin_c = [float(r["wheelspin"]) for r in rows]
        self.t_end = self.car.t_end
        self._cl = centreline_table(spec, 2.0)

        # ---- the telemetry's own declared departure from rolling contact --
        # Identical in definition to `tools/wheel_rotation_gate.py`'s
        # measurement B, re-phased one frame later so it starts at zero. See
        # the header for why, and for the proof that nothing is discarded.
        slip = [self.wheel_c[i] - self.s_c[i] / WHEEL_RADIUS_M
                for i in range(len(rows))]
        self.slip_c = [0.0] + slip[:-1]
        self.slip_declared_total = slip[-1]

        # ---- the ground the body ACTUALLY covers -------------------------
        # Arc length of the polyline the car is KEYED ON: the telemetry's x and y
        # with the contact solve's z, not the telemetry's z. Those differ by up
        # to 0.340 m down the delivery ramp, and a wheel rolling down a slope
        # covers the hypotenuse. Measured: driving this off the telemetry's flat
        # z instead leaves 1.4e-02 rad per frame of phantom slip through the
        # ramp, which the gate would then have to be given a tolerance to
        # forgive — and a tolerance wide enough to forgive a real defect is how
        # this project got R2-041.
        #
        # `Car.state` lerps position between the same rows this walks, so between
        # two rows the cumulative length is not an approximation of the path; it
        # IS the path.
        self.dist_c = [0.0]
        prev = (self.car.x[0], self.car.y[0], self.pose_z(self.car.t[0]))
        for i in range(1, len(rows)):
            cur = (self.car.x[i], self.car.y[i], self.pose_z(self.car.t[i]))
            self.dist_c.append(self.dist_c[-1] + math.dist(prev, cur))
            prev = cur

    # ---------------------------------------------------------- the columns --
    def _col(self, arr, t):
        """Interpolate a column with the SAME lerp `Car.state` uses for x, y, z."""
        return self.car._lerp(arr, t)

    def ground_distance(self, t):
        """Metres of ground the car's reference point has covered by world time t.

        Past the end of the telemetry `carpath.Car.state` continues the car along
        the circuit's centreline at its final speed, and centreline arc length
        advances at exactly that speed, so the continuation is `v * dt`.
        """
        if t <= 0.0:
            return 0.0
        if t <= self.t_end:
            return self._col(self.dist_c, t)
        return self.dist_c[-1] + self.car.v[-1] * (t - self.t_end)

    def slip(self, t):
        """Radians of NON-ROLLING wheel rotation — the sanctioned launch spin."""
        if t <= 0.0:
            return 0.0
        if t <= self.t_end:
            return self._col(self.slip_c, t)
        return self.slip_c[-1]

    def spin(self, t):
        """Wheel rotation in radians. ZERO at t = 0, non-decreasing forever.

        Rolling contact against the ground the body actually covers, plus the
        telemetry's own declared slip. Both terms are non-decreasing, so this is.
        """
        return self.ground_distance(t) / WHEEL_RADIUS_M + self.slip(t)

    def curvature(self, t):
        if t <= 0.0:
            return 0.0
        if t <= self.t_end:
            return self._col(self.curv_c, t)
        # extrapolating: the car is on the circuit's centreline, so the
        # centreline's own curvature is the curvature. Central difference on
        # heading over 4 m, which is the table's own two-sample resolution.
        s = self.car.track_s(t) % C.LAP
        _p0, h0 = cl_at(self._cl, (s - 2.0) % C.LAP)
        _p1, h1 = cl_at(self._cl, (s + 2.0) % C.LAP)
        dh = (h1 - h0 + math.pi) % (2.0 * math.pi) - math.pi
        return dh / 4.0

    def steer(self, t):
        """Front-wheel steer angle, positive = left, from Ackermann.

        `delta = atan(wheelbase * curvature)`.  Derived, not scaled to taste: at
        the tightest corner on the circuit (T4 Le Pin, curvature 0.0357 = R 28 m)
        it gives 7.32 deg, which is what a 3.600 m wheelbase needs to get round a
        28 m radius and is a plausible F1 lock.

        The telemetry's `steer_norm` column is `curvature * 2.8` — the same
        quantity on an arbitrary normalisation — and the two agree to 5.0e-06
        over all 1,743 rows.  The curvature column is used because it is the one
        with units.
        """
        return math.atan(WHEELBASE_M * self.curvature(t))

    def body_pitch(self, t):
        """Dive/squat only. The road's grade is added by the contact solve."""
        if t <= 0.0:
            return 0.0
        if t <= self.t_end:
            return self._col(self.pitch_c, t)
        return 0.0                        # extrapolated at constant speed

    def body_roll(self, t):
        """Lateral lean only. The road's camber is added by the contact solve."""
        if t <= 0.0:
            return 0.0
        if t <= self.t_end:
            return self._col(self.roll_c, t)
        # same closed form `tools/build_telemetry.py` uses, on the extrapolated
        # speed and the centreline's curvature
        ay = self.car.v[-1] ** 2 * self.curvature(t)
        return max(-1.0, min(1.0, ay / 45.0)) * math.radians(1.4)

    def wheelspin_flag(self, t):
        if t <= 0.0 or t > self.t_end:
            return 0.0
        return self._col(self.spin_c, t)

    # ------------------------------------------------------- the contact solve
    def contacts(self, t):
        """Ground height under each of the four contact patches, as a dict."""
        p, hd, _v = self.car.state(t)
        s_tel = self.car.track_s(t) + SF_TELEMETRY_S
        cs, sn = math.cos(hd), math.sin(hd)
        out = {}
        for name, ax, hy, _front in CORNERS:
            # STATION for the road branch: the axle offsets are resolved along
            # the path, because the road's own height function is parameterised
            # in (station, lateral) and at the tightest radius on the circuit
            # (28 m) the arc-length error of a 1.8 m offset is 0.019 m of
            # station, i.e. 1e-4 m of height on the steepest grade in the film.
            # WORLD X for the showroom branch, because the dais and its ramp are
            # declared in world X and world X is not `s_m` over that span.
            x_world = p[0] + ax * cs - hy * sn
            out[name] = contact_z(x_world, s_tel + ax, hy)
        return out

    def pose_z(self, t):
        """CAR_ROOT's world z alone — the mean of the four contact heights."""
        z = self.contacts(t)
        return 0.25 * (z["FL"] + z["FR"] + z["RL"] + z["RR"])

    # ------------------------------------------------------- the suspension --
    def hub_z_local(self, corner_z, ax, hy, loc_z, roll, pitch):
        """The hub's LOCAL z that puts its wheel centre one radius above `corner_z`.

        THE WHEELS DO NOT PITCH AND ROLL WITH THE BODY. `pitch_rad` and
        `roll_rad` are dive-squat and lateral lean — the chassis moving on its
        suspension — and a chassis moving on its suspension moves relative to
        four wheels that stay on the road. Rotating the whole car rigidly about
        CAR_ROOT instead lifts an axle off the ground by `axle_x * tan(pitch)`,
        which at this car's declared +-1.6 deg and 1.800 m is **50 mm**, plus
        21 mm from +-1.4 deg of roll across a 0.848 m half-track. A tyre hovering
        55 mm over its own shadow is the most visible defect a car animation has.

        So each hub is given the compliance back out (`-roll`, `-pitch` on the
        hub) and the vertical that re-plants it, solved exactly rather than
        approximated:

            z_world = loc_z - ax*sin(p) + (hy*sin(r) + k*cos(r))*cos(p)

        is the world height of a hub at local (ax, hy, k) under CAR_ROOT's
        Rz.Ry.Rx, and the yaw drops out of it. Setting z_world = corner_z + r_w
        and solving for k is one line and has no small-angle assumption in it.
        """
        want = corner_z + WHEEL_RADIUS_M
        num = (want - loc_z + ax * math.sin(pitch)) / math.cos(pitch)
        return (num - hy * math.sin(roll)) / math.cos(roll)

    # -------------------------------------------------------------- the pose --
    def pose(self, t):
        """Everything the rig needs, at world time t.

        `loc` is CAR_ROOT's world location: x and y straight from `Car.state`,
        z from the contact solve.  `rot` is an XYZ Euler — Blender applies X then
        Y then Z, i.e. roll, then pitch, then yaw, which is the vehicle
        convention.  `spin` is the wheels' rotation about their own +Y, `steer`
        the front wheels' about their own +Z.
        """
        p, hd, v = self.car.state(t)
        z = self.contacts(t)
        zf = 0.5 * (z["FL"] + z["FR"])
        zr = 0.5 * (z["RL"] + z["RR"])
        zl = 0.5 * (z["FL"] + z["RL"])
        zright = 0.5 * (z["FR"] + z["RR"])
        root_z = 0.25 * (z["FL"] + z["FR"] + z["RL"] + z["RR"])

        # nose DOWN is a positive rotation about +Y (a point at +X goes to -Z),
        # so a front contact BELOW the rear one is a positive pitch.
        pitch_ground = -math.atan2(zf - zr, WHEELBASE_M)
        # the left side UP is a positive rotation about +X (a point at +Y goes
        # to +Z), so a left contact above the right one is a positive roll.
        roll_ground = math.atan2(zl - zright, MEAN_TRACK_M)

        body_roll = self.body_roll(t)
        body_pitch = self.body_pitch(t)
        roll = roll_ground + body_roll
        pitch = pitch_ground + body_pitch
        steer = self.steer(t)

        hubs = {}
        for name, ax, hy, is_front in CORNERS:
            hubs[name] = {
                "loc": (ax, hy,
                        self.hub_z_local(z[name], ax, hy, root_z, roll, pitch)),
                # the compliance taken back out, so the wheel stays flat on the
                # ground the body is moving relative to; the GROUND's own pitch
                # and roll are left in, because the wheels really do follow those
                "rot": (-body_roll, -body_pitch, steer if is_front else 0.0),
            }

        return {
            "loc": (p[0], p[1], root_z),
            "rot": (roll, pitch, hd),
            "spin": self.spin(t),
            "steer": steer,
            "hubs": hubs,
            "speed": v,
            "heading": hd,
            "pitch_ground": pitch_ground,
            "roll_ground": roll_ground,
            "body_pitch": body_pitch,
            "body_roll": body_roll,
            "contacts": z,
            "telemetry_z": p[2],
        }

    def pose_series(self, times):
        """Poses over a whole series of world times, WITH the wheels rolled.

        `spin(t)` on its own is the continuous quantity: rolling contact along
        the telemetry's own polyline. But the film's keys are LINEAR and per
        frame, so what the car does on screen is travel the CHORD between two
        keyed positions — and the film's frames are not aligned with the
        telemetry's rows (frame 818 lands at world t = 0.0115 s), so those chords
        are not the row chords. Building the rotation from the series that is
        actually keyed makes rolling contact exact by construction instead of
        exact to a polygonisation term, and it lets the gate check it with no
        tolerance for curvature at all.

        Measured difference over the whole film: 1.0 m in 5,046 m, 0.02 %.
        """
        poses = [self.pose(t) for t in times]
        d, prev = 0.0, None
        for t, p in zip(times, poses):
            if prev is not None:
                d += math.dist(prev, p["loc"])
            prev = p["loc"]
            p["spin"] = d / WHEEL_RADIUS_M + self.slip(t)
            p["ground_m"] = d
        return poses


def world_time_table(sheet_path, total_frames=None):
    """film frame -> world time, through `anim/filmtime.py`. One map, shared."""
    import json
    import filmtime as FT
    sheet = json.load(open(sheet_path))
    n = int(total_frames or sheet["total_frames"])
    scales, info = FT.build_time_map(sheet, n)
    return FT.world_time_table(scales, n), info, sheet
