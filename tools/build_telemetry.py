"""THE single source of truth for motion. Everything downstream reads this CSV.

    .venv/bin/python tools/build_telemetry.py \
        --spec docs/circuit_spec.json --out telemetry/telemetry.csv --fps 24

WHAT READS THIS FILE
--------------------
wheel rotation, steering articulation, chassis pitch/roll, the camera
choreography's timing, and every layer of the audio mix. The brief is explicit
that ONE artefact owns this and everyone else reads from it, because the moment
two components each compute their own speed profile they drift, and a drift
between picture and sound in a cut-free shot is unfixable in the edit.

THE SOLVER
----------
Classic quasi-steady-state lap simulation, three passes over a fine arc-length
grid:

  1. CORNER LIMIT — the fastest a corner can be taken, v = sqrt(a_lat(v) * R).
     a_lat itself depends on v (downforce rises with v^2), so this is solved by
     fixed-point iteration rather than in closed form.
  2. FORWARD PASS — accelerate from each point under min(traction, power) minus
     drag minus grade. Traction-limited off the corner, power-limited down the
     straight.
  3. BACKWARD PASS — the same in reverse under braking. The final speed at any
     point is min(corner, forward, backward): you cannot be going faster than the
     corner allows, faster than you could have accelerated to, or faster than you
     could still slow down from.

Geometry is evaluated ANALYTICALLY from the spec's elements (straights and
circular arcs), not from the 202 exported control points. The control points are
a rendering convenience with a stated worst chord error of 0.123 m; integrating
speed along chords would accumulate that error into the lap time and hence into
the audio sync.

THAT POLICY NOW APPLIES TO THE TRANSIT TOO  (R2-042, docs/R2-042-DECISION.md).
Until 2026-08-02 the lap obeyed the paragraph above and the transit did not: the
transit's world positions were `np.interp` over the four leg ENDPOINTS, i.e. the
CHORD of a declared R150 / 40 deg merge arc.  A 104.7 m arc of R150 stands
150*(1-cos(20 deg)) = 9.05 m off its own chord, and the code drove 104.700 m of
arc-length `s` along a 102.607 m chord, so the SPEED was wrong as well as the
position.  The car's swept box ran up to 4.643 m outboard of its own road's edge,
for 60.1 m of Beat 4, at 200+ km/h, on camera.  `transit_path()` below evaluates
the same four legs as elements — straights linearly, the merge as the arc — off
the SAME constants the world is built from (`world_contract.access_route_*`), so
there is one merge curve and not two.

ROLLING CONTACT
---------------
wheel_rot_rad = cumulative_distance / wheel_radius, everywhere, with exactly one
sanctioned exception: the ~10-frame launch wheelspin in Beat 2, which is flagged
in its own column so a later rolling-contact check does not "correct" it.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))
# THE ROAD IS THE CONTRACT'S, SO THE MERGE ARC IS TOO  (R2-042).  This is the
# one import, and it is deliberately UNGUARDED: a try/except fallback to the old
# chord would be exactly the silent-plausible-data failure `elevation()` below
# was rewritten to refuse.  `world_contract` reads only json/math/os/sys/numpy
# and never reads this file's output, so there is no cycle; the contract's RULE 2
# (it may not import from tools/) is untouched by importing it FROM tools.
import world_contract as WC                                      # noqa: E402

G = 9.81


def load_spec(path):
    return json.load(open(path))


def build_geometry(spec, ds=0.25):
    """Analytic (s, x, y, heading, curvature) along the lap."""
    S, X, Y, H, K = [], [], [], [], []
    for el in spec["elements"]:
        x0, y0 = el["start_world"][0], el["start_world"][1]
        h0 = math.radians(el["heading_world_deg"])
        L = el["length_m"]
        s0 = el["s_start"]
        n = max(int(round(L / ds)), 1)
        if el["type"] == "S" or not el.get("radius_m"):
            for i in range(n):
                t = i * L / n
                S.append(s0 + t); X.append(x0 + math.cos(h0) * t)
                Y.append(y0 + math.sin(h0) * t); H.append(h0); K.append(0.0)
        else:
            R = float(el["radius_m"])
            turn = math.radians(el["turn_deg"])
            sign = 1.0 if turn >= 0 else -1.0
            # arc turning left for positive turn_deg
            for i in range(n):
                t = i * L / n
                dth = sign * t / R
                h = h0 + dth
                # centre is perpendicular to the start heading
                cx = x0 - sign * R * math.sin(h0)
                cy = y0 + sign * R * math.cos(h0)
                X.append(cx + sign * R * math.sin(h))
                Y.append(cy - sign * R * math.cos(h))
                S.append(s0 + t); H.append(h); K.append(sign / R)
    return (np.array(S), np.array(X), np.array(Y), np.array(H), np.array(K))


def elevation(spec, s, total):
    """Elevation from the spec's PVI stations and parabolic vertical curves.

    The spec uses real vertical-alignment geometry: `station_z_pvi` lists points
    of vertical intersection (station, elevation, curve length), with constant
    tangent grades between them joined by symmetric parabolas. Straight-line
    interpolation between PVIs would give a piecewise-linear road with a grade
    discontinuity at every PVI — visible as a kink in a low chase shot and, worse,
    a step in the grade term that feeds the speed solver.

    A symmetric vertical curve of length L about a PVI runs from
    BVC = s_pvi - L/2 to EVC = s_pvi + L/2, and within it

        z(x) = z_BVC + g1*x + (g2 - g1) / (2L) * x^2       (x measured from BVC)

    which is C1 at both ends: it leaves on the incoming grade and arrives on the
    outgoing one.

    THIS FUNCTION USED TO RETURN ZEROS WHEN IT DID NOT RECOGNISE THE SCHEMA.
    It looked for `profile`/`points`, this spec has `station_z_pvi`, and the whole
    telemetry silently described a table-flat circuit while the spec described
    11.63 m of elevation. Nothing failed; the CSV was complete and wrong. It now
    raises instead, because a silent fallback to plausible-looking data is the
    single most expensive failure mode this project has.
    """
    prof = spec.get("elevation") or {}
    pvi = prof.get("station_z_pvi")
    if not pvi:
        raise SystemExit(
            "elevation: no 'station_z_pvi' in spec['elevation'] "
            f"(keys present: {sorted(prof)}). Refusing to render a flat circuit.")

    ps = np.array([p["s"] for p in pvi], float)
    pz = np.array([p["z"] for p in pvi], float)
    pl = np.array([p.get("vertical_curve_len_m", 0.0) for p in pvi], float)

    # tangent grades between consecutive PVIs
    grades = np.zeros(len(ps))
    for i in range(len(ps) - 1):
        grades[i] = (pz[i + 1] - pz[i]) / max(ps[i + 1] - ps[i], 1e-9)
    grades[-1] = grades[-2] if len(ps) > 1 else 0.0

    def z_at(x):
        """Elevation at station x.

        A point can lie inside the vertical curve of the PVI that OPENS its
        segment or the one that CLOSES it, so both must be tested. The first
        version tested only the opening PVI, which meant every closing curve was
        skipped and the elevation stepped at each segment boundary: grade came
        out at -12.5%/+20.3% against a design range of -4.45%/+5.20%, with
        9.45 %/m discontinuities. A road with a grade step is a kink the chase
        camera would fly straight through.
        """
        i = int(np.searchsorted(ps, x, side="right") - 1)
        i = min(max(i, 0), len(ps) - 1)

        for j in (i, i + 1):                      # opening PVI, then closing PVI
            if j < 1 or j > len(ps) - 2:
                continue
            L = pl[j]
            if L <= 1e-6:
                continue
            bvc, evc = ps[j] - L / 2.0, ps[j] + L / 2.0
            if bvc <= x <= evc:
                g1, g2 = grades[j - 1], grades[j]
                z_bvc = pz[j] - g1 * (L / 2.0)
                u = x - bvc
                return z_bvc + g1 * u + (g2 - g1) / (2.0 * L) * u * u

        # on tangent: ride the grade of the segment this station belongs to
        k = min(i, len(ps) - 2)
        return pz[k] + grades[k] * (x - ps[k])

    sq = np.mod(np.asarray(s, float), total)
    return np.array([z_at(float(x)) for x in sq])


def a_lat(v):     return np.minimum(15.0 + 0.0050 * v * v, 48.0)
def a_trac(v):    return np.minimum(11.0 + 0.0022 * v * v, 20.0)
def a_pow(v):     return 800.0 / np.maximum(v, 5.0)
def a_drag(v):    return 0.00092 * v * v
def a_brk(v):     return np.minimum(1.25 + 2.2e-4 * v * v, 5.0) * G


def corner_limit(K):
    """v = sqrt(a_lat(v)/|K|), solved by fixed point since a_lat depends on v."""
    v = np.full(K.shape, 120.0)
    R = np.where(np.abs(K) > 1e-9, 1.0 / np.maximum(np.abs(K), 1e-9), 1e9)
    for _ in range(60):
        v = np.sqrt(a_lat(v) * R)
    return np.minimum(v, 400.0)


def solve_speed(S, K, grade, vmax_cap, ds):
    vc = np.minimum(corner_limit(K), vmax_cap)
    n = len(S)

    fwd = vc.copy()
    for i in range(1, n):
        v = fwd[i - 1]
        acc = min(a_trac(v), a_pow(v)) - a_drag(v) - G * grade[i - 1]
        cand = math.sqrt(max(v * v + 2.0 * acc * ds, 1.0))
        fwd[i] = min(vc[i], cand)

    bwd = vc.copy()
    for i in range(n - 2, -1, -1):
        v = bwd[i + 1]
        dec = a_brk(v) + a_drag(v) + G * grade[i]
        cand = math.sqrt(max(v * v + 2.0 * dec * ds, 1.0))
        bwd[i] = min(vc[i], cand)

    return np.minimum(np.minimum(fwd, bwd), vc)


def _smootherstep(f):
    """C2 ease with zero slope AND zero curvature at both ends: 6f^5-15f^4+10f^3.

    The cubic 3f^2-2f^3 was tried first and rejected on a measurement.  Its second
    derivative is 6 at both ends, so a car converging on it is still turning when
    it reaches the start/finish line: `accel_lat_ms2` stepped 4.034 -> 0.000 m/s^2
    and `roll_rad` 0.126 deg -> 0 in the single frame across the transit/lap seam.
    That is a discontinuity at a beat boundary, introduced by the fix, in a film
    whose one law is that there are none.  The quintic ends flat at both ends and
    its peak curvature is LOWER (5.774 against 6.000), so it costs nothing.
    """
    return f * f * f * (f * (f * 6.0 - 15.0) + 10.0)


def transit_path(tr_s, legs, sf_xy, sf_head_deg):
    """(x, y, heading) at transit arc-length stations `tr_s`, ANALYTICALLY.

    R2-042.  The four legs of `SPEC["transit"]["legs"]`, evaluated as the elements
    they declare instead of as the chords between their endpoints:

      leg 0  dais -> glass      straight, world x 0 -> 15
      leg 1  the apron run      straight, world x 15 -> 64.6   (= the route's first
                                49.60 m, `access_route_point` t 0 -> ACCESS_L2)
      leg 2  the merge          THE R150 / 40 deg ARC, `access_route_point`
                                t ACCESS_L2 -> ACCESS_MERGE.  This is the fix: the
                                chord of this arc stands 9.05 m OUTBOARD of it —
                                left of travel, away from the track — which is why
                                the car was outside its own road and not inside it.
      leg 3  merge -> the line  the pit straight, entered TANGENT at 40 deg and
                                converging the arc's 5.02 m of lateral offset onto
                                the racing centreline on a quintic ease.

    EACH LEG IS PARAMETERISED BY ITS OWN FRACTION, not by a global station, so
    every leg node lands at exactly the station the spec declares and the speed
    profile — which is built from `length_m` and never touches this function — is
    left bit-identical.  The cost is that leg 2's declared 104.700 m is stretched
    over the true 104.7198 m of R150 x 40 deg: 0.019 %, 19 mm over the whole leg.
    The alternative is a 20 mm step at the leg node, and a step is worse than a
    scale on a curve whose derivative drives the audio.

    WHY LEG 3 IS NOT THE SPEC'S CHORD.  The arc exits 5.023 m LEFT of the pit
    straight's centreline (contract `ACCESS_MERGE_LATERAL` = 5.02, measured here at
    lap u = +5.023 against `half_width` = 8.0, so the car is already on the racing
    surface and has 215.6 m of it to converge across).  The spec's leg-3 chord
    spends that 5.02 m linearly, which meets the merge at a 18.67 deg kink and the
    START/FINISH LINE at a 1.33 deg one — in a film with no cuts, at 288.6 km/h.
    The quintic ease has zero slope AND zero curvature at both ends, so the car
    leaves the arc tangent, crosses the line tangent AND straight, and it never
    departs the spec's own chord by more than 0.74 m.

    HEADING IS RETURNED AND IT IS REAL.  The transit heading column used to be
    zeros, so the car pointed due east through a 40 deg merge and then snapped
    0 -> 40 deg in one frame at the line.  Everything that reads it — the audio's
    exhaust position and directivity, the camera author's car box — was reading
    that.  See main() for what is written.
    """
    s = np.asarray(tr_s, float)
    L = np.array([float(l["length_m"]) for l in legs], float)
    cum = np.concatenate([[0.0], np.cumsum(L)])

    # The contract's route and the spec's legs have to be THE SAME ROAD; if they
    # are not, this file must stop rather than average them.
    ex, ey, eh = WC.access_route_point(WC.ACCESS_MERGE)
    for name, got, want, tol in (
            ("leg 1 starts at the glass plane",
             legs[1]["from_world"][0], WC.ACCESS_GLASS_X, 1e-9),
            ("leg 1 is the contract's apron run", L[1], WC.ACCESS_L2, 1e-9),
            ("leg 2 is the contract's merge arc", L[2], WC.ACCESS_L3, 0.025),
            ("the arc exits where leg 2 ends (x)", ex, legs[2]["to_world"][0], 0.01),
            ("the arc exits where leg 2 ends (y)", ey, legs[2]["to_world"][1], 0.01),
            ("the arc exits on the racing direction",
             math.degrees(eh), sf_head_deg, 1e-9),
            ("leg 3 ends on the start/finish line (x)",
             legs[3]["to_world"][0], sf_xy[0], 0.01),
            ("leg 3 ends on the start/finish line (y)",
             legs[3]["to_world"][1], sf_xy[1], 0.01)):
        if abs(float(got) - float(want)) > tol:
            raise SystemExit("transit_path: %s — %.6f vs %.6f (tol %g)"
                             % (name, got, want, tol))

    X = np.empty_like(s)
    Y = np.empty_like(s)
    H = np.empty_like(s)

    def frac(i):
        return np.clip((s - cum[i]) / L[i], 0.0, 1.0)

    # ---- leg 0: the launch, dais to glass ---------------------------------
    # UNCHANGED, AND KNOWINGLY SO.  Its `length_m` 11.980 is the distance from the
    # car's NOSE (world x = +3.020, the measured body front) to the glass, while
    # its endpoints are ORIGIN positions 15.000 m apart — the two datums of R2-026.
    # Interpolating the endpoints over the declared length is what puts the car
    # through the glass at the frame the spec's 1.78 s says it does; "fixing" the
    # geometry here without fixing the datum would delay the breach by 0.4 s and
    # move a beat boundary.  Logged, not silently corrected.
    m = s < cum[1]
    f = frac(0)[m]
    p0 = legs[0]["from_world"]
    p1 = legs[0]["to_world"]
    X[m] = p0[0] + f * (p1[0] - p0[0])
    Y[m] = p0[1] + f * (p1[1] - p0[1])
    H[m] = math.atan2(p1[1] - p0[1], p1[0] - p0[0])

    # ---- legs 1 and 2: the contract's route, straight then ARC ------------
    m = (s >= cum[1]) & (s < cum[3])
    t = np.where(s < cum[2],
                 frac(1) * WC.ACCESS_L2,
                 WC.ACCESS_L2 + frac(2) * WC.ACCESS_L3)[m]
    X[m], Y[m], H[m] = WC.access_route_arrays(t)

    # ---- leg 3: onto the pit straight, tangent at both ends ---------------
    ang = math.radians(sf_head_deg)
    dirv = np.array([math.cos(ang), math.sin(ang)])
    nrm = np.array([-math.sin(ang), math.cos(ang)])
    e = np.array([ex, ey]) - np.asarray(sf_xy, float)
    l0 = float(e @ dirv)                       # -215.589: the arc exit, behind
    v0 = float(e @ nrm)                        # +5.023 m left of the centreline
    if not (l0 < -100.0 and 4.0 < v0 < 6.0):
        raise SystemExit("transit_path: leg 3 anchor is not where the merge ends "
                         "(long %.3f, lat %.3f)" % (l0, v0))
    m = s >= cum[3]
    f = frac(3)[m]
    lon = l0 * (1.0 - f)
    lat = v0 * (1.0 - _smootherstep(f))
    X[m] = sf_xy[0] + lon * dirv[0] + lat * nrm[0]
    Y[m] = sf_xy[1] + lon * dirv[1] + lat * nrm[1]
    # d(lat)/d(lon) from the closed form, so the heading is exact at f = 0 and 1
    dlat_df = -v0 * 30.0 * f * f * (1.0 - f) * (1.0 - f)
    H[m] = ang + np.arctan2(dlat_df, -l0)
    return X, Y, H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--ds", type=float, default=0.25)
    ap.add_argument("--wheel-radius", type=float, default=0.36)
    a = ap.parse_args()

    spec = load_spec(a.spec)
    total = spec["headline"]["length_m"]
    S, X, Y, H, K = build_geometry(spec, a.ds)
    Z = elevation(spec, S, total)
    grade = np.gradient(Z, S, edge_order=1)

    vcap = spec["headline"]["vmax_kph"] / 3.6
    V = solve_speed(S, K, grade, vcap, a.ds)

    # two extra relaxation sweeps: the first backward pass uses the corner limit
    # as its seed, which can leave a braking zone that starts a metre or two late
    for _ in range(2):
        V = solve_speed_relax(S, K, grade, V, a.ds)

    dt = a.ds / np.maximum(V, 1.0)
    T = np.concatenate([[0.0], np.cumsum(dt)[:-1]])
    lap_t = float(T[-1] + dt[-1])

    print(f">> lap solved: {lap_t:8.3f} s   spec says {spec['headline']['lap_time_s']:.3f} s "
          f"(delta {lap_t - spec['headline']['lap_time_s']:+.3f})")
    print(f">> vmax {V.max()*3.6:6.1f} km/h (spec {spec['headline']['vmax_kph']:.1f})   "
          f"vmin {V.min()*3.6:5.1f} km/h (spec {spec['headline']['vmin_kph']:.1f})")

    # before the first write, not before the last: `_solve.json` lands beside the
    # CSV and used to be written first, so a fresh output directory crashed the
    # run AFTER the 8 s solve and BEFORE anything was saved.
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"lap_time_s": lap_t, "vmax_kph": float(V.max() * 3.6),
               "vmin_kph": float(V.min() * 3.6), "samples": int(len(S)),
               "ds_m": a.ds},
              open(os.path.splitext(a.out)[0] + "_solve.json", "w"), indent=1)

    # ---- prepend the transit: dais -> glass -> apron -> merge -> line ----
    # The brief requires the telemetry to cover the launch and transit beats,
    # not just the lap, because the SAME csv drives the audio and the camera
    # through Beats 2-4. A lap-only file would leave the engine note and the
    # wheel rotation undefined for the 8.9 s in which the car breaks out of the
    # building — the most acoustically dramatic part of the whole film.
    #
    # Speeds come from the spec's own leg model (which the circuit synthesiser
    # already corrected: the launch run is 11.98 m from the car's nose at X=+3.02
    # to the glass at X=+15.00, giving 53.8 km/h at impact, not the 85-100 km/h
    # the source design claimed). Each leg is integrated at constant acceleration
    # between its entry and exit speed, which is what the leg times encode.
    legs = spec["transit"]["legs"]
    tr_s, tr_v = [], []
    s_acc, v_prev = 0.0, 0.0
    for leg in legs:
        L = float(leg["length_m"])
        v1 = float(leg["exit_kph"]) / 3.6
        n = max(int(round(L / a.ds)), 2)
        u = np.linspace(0.0, L, n, endpoint=False)
        # constant-a between v_prev and v1 over L:  v(u) = sqrt(v0^2 + 2*a*u)
        acc = (v1 * v1 - v_prev * v_prev) / (2.0 * max(L, 1e-9))
        vv = np.sqrt(np.maximum(v_prev * v_prev + 2.0 * acc * u, 0.25))
        tr_s.append(s_acc + u)
        tr_v.append(vv)
        s_acc += L
        v_prev = v1
    tr_s = np.concatenate(tr_s)
    tr_v = np.concatenate(tr_v)
    tr_dt = a.ds / np.maximum(tr_v, 0.5)
    tr_T = np.concatenate([[0.0], np.cumsum(tr_dt)[:-1]])
    transit_t = float(tr_T[-1] + tr_dt[-1])
    print(f">> transit: {s_acc:7.2f} m in {transit_t:6.3f} s   "
          f"(spec {spec['transit']['total_length_dais_to_line_m']:.2f} m / "
          f"{spec['transit']['total_time_dais_to_line_s']:.2f} s)")

    # Transit world positions are NOT computed here any more.  They are evaluated
    # ANALYTICALLY, at the frame stations themselves, once those are known — see
    # `transit_path` and the resampling below.  Interpolating a 0.25 m table of an
    # R150 arc would put a 0.05 mm chord error back into a file whose whole
    # docstring is about not doing that; evaluating at the frames has none.
    # `tr_s`, `tr_v` and `tr_T` above are untouched by the change: the transit's
    # speed and timing come from `length_m` alone and never read a position, which
    # is why the fix moves x and y by 9.04 m and moves no clock by one sample.

    # ---- resample onto frames --------------------------------------------
    total_t = transit_t + lap_t
    nfr = int(math.floor(total_t * a.fps))
    ft = np.arange(nfr) / a.fps
    lap_mask = ft >= transit_t
    # transit portion, then the lap continuing from the start/finish line
    lt = ft[lap_mask] - transit_t
    ls = np.interp(lt, T, S)
    lv = np.interp(lt, T, V)

    tt = ft[~lap_mask]
    ts = np.interp(tt, tr_T, tr_s)
    tv = np.interp(tt, tr_T, tr_v)

    # the transit, on the declared elements, evaluated at the frames themselves
    tx, ty, th = transit_path(ts, legs, (float(X[0]), float(Y[0])),
                              float(spec["datum"]["racing_direction_world_deg"]))
    tz = np.zeros_like(ts)
    # transit curvature: 0 on the straights, 1/R through the merge, and the
    # quintic's own curvature on the run to the line.  It is what `accel_lat`
    # (v^2 * k) and `steer_norm` are made of, and both used to read zero for the
    # whole of a 40 deg merge taken at 200+ km/h.
    tk = np.gradient(np.unwrap(th), ts, edge_order=1)

    fv = np.concatenate([tv, lv])
    fx = np.concatenate([tx, np.interp(ls, S, X)])
    fy = np.concatenate([ty, np.interp(ls, S, Y)])
    fz = np.concatenate([tz, np.interp(ls, S, Z)])
    fk = np.concatenate([tk, np.interp(ls, S, K)])
    fh = np.concatenate([np.unwrap(th), np.interp(ls, S, np.unwrap(H))])
    # `s_m` is continuous across the whole film: transit distance then lap
    # distance, so wheel rotation integrates without a discontinuity at the line.
    fs = np.concatenate([ts, s_acc + ls])

    # rolling contact everywhere: rotation = distance / wheel radius
    wheel = fs / a.wheel_radius

    # SANCTIONED VIOLATION — Beat 2 launch wheelspin. The brief permits exactly
    # one departure from rolling contact: ~10 frames where the wheels spin faster
    # than the car travels. It is flagged in its own column so a later
    # rolling-contact audit reads it as intentional instead of "correcting" it.
    spin_frames = 10
    spin = np.zeros(nfr)
    spin[:spin_frames] = 1.0
    # Add the slip as extra rotation, tapering as the tyre hooks up.
    #
    # THE SLIP IS AN ACCUMULATED ANGLE AND IT PERSISTS.  R2-041: this used to be
    # `extra[:spin_frames] = cumsum(...)` and nothing else, so `extra` was a
    # WINDOW: 9.0821 rad at frame 9 and 0.0 at frame 10.  Adding a window to a
    # monotonic ramp threw the whole accumulated slip away in one frame and the
    # wheels snapped BACKWARDS 1.4454 revolutions at frame 10 -- during the
    # launch, which is the one moment in the film where the eye is on the wheels.
    #
    # A wheel that has spun 1.45 turns more than it travelled does not un-spin
    # when it hooks up; it resumes rolling contact from its new phase.  So the
    # cumulative slip is HELD at its final value for every subsequent frame, and
    # `wheel_rot_rad` stays the strictly increasing quantity that every consumer
    # (the wheel driver, the audio's tyre roar) assumes it is.
    extra = np.zeros(nfr)
    taper = np.linspace(1.0, 0.0, spin_frames) ** 1.5
    slip_per_frame = taper * 2.4 / a.fps / a.wheel_radius * 8.0
    slip_accum = np.cumsum(slip_per_frame)
    extra[:spin_frames] = slip_accum
    extra[spin_frames:] = slip_accum[-1]           # HOLD, do not drop
    wheel = wheel + extra

    # MONOTONICITY IS MEASURED HERE, NOT ASSUMED DOWNSTREAM.  `fs` is a
    # cumulative distance and `extra` is non-decreasing by construction, so a
    # backwards step is impossible -- which is exactly the sort of statement that
    # was true about the old code too, right up to the frame where it was not.
    dw = np.diff(wheel)
    if dw.size and dw.min() < -1e-9:
        i = int(np.argmin(dw))
        raise AssertionError(
            "wheel_rot_rad steps BACKWARDS by %.5f rad (%.4f rev) at frame %d; "
            "rotation must be monotonic across the whole take"
            % (-dw[i], -dw[i] / (2.0 * math.pi), i + 1))
    total_slip_rev = float(slip_accum[-1]) / (2.0 * math.pi)
    roll_rev = float(fs[-1]) / (2.0 * math.pi * a.wheel_radius)
    print(">> wheel: %.4f rev total = %.4f rev of rolling contact "
          "(%.2f m / %.4f m circumference) + %.4f rev of sanctioned launch slip; "
          "min step %+.6f rad"
          % (float(wheel[-1]) / (2.0 * math.pi), roll_rev, float(fs[-1]),
             2.0 * math.pi * a.wheel_radius, total_slip_rev,
             float(dw.min()) if dw.size else 0.0))
    # longitudinal acceleration -> pitch (dive/squat); lateral -> roll
    ax = np.gradient(fv, ft, edge_order=1)
    ay = fv * fv * fk
    pitch = np.clip(-ax / 30.0, -1.0, 1.0) * math.radians(1.6)
    roll = np.clip(ay / 45.0, -1.0, 1.0) * math.radians(1.4)
    steer = np.clip(fk * 2.8, -1.0, 1.0)      # normalised, wheelbase-scaled

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "t_s", "s_m", "x", "y", "z", "speed_ms", "speed_kph",
                    "curvature", "heading_rad", "accel_long_ms2", "accel_lat_ms2",
                    "wheel_rot_rad", "steer_norm", "pitch_rad", "roll_rad",
                    "wheelspin"])
        for i in range(nfr):
            w.writerow([i, f"{ft[i]:.6f}", f"{fs[i]:.4f}", f"{fx[i]:.4f}",
                        f"{fy[i]:.4f}", f"{fz[i]:.4f}", f"{fv[i]:.5f}",
                        f"{fv[i]*3.6:.3f}", f"{fk[i]:.7f}", f"{fh[i]:.6f}",
                        f"{ax[i]:.4f}", f"{ay[i]:.4f}", f"{wheel[i]:.5f}",
                        f"{steer[i]:.5f}", f"{pitch[i]:.6f}", f"{roll[i]:.6f}",
                        int(spin[i])])

    print(f">> wrote {a.out}  {nfr} frames @ {a.fps} fps  ({nfr/a.fps:.2f} s)")
    print(">> STAGE RESULT: TELEMETRY_OK")


def solve_speed_relax(S, K, grade, vseed, ds):
    """One more forward/backward pass seeded with the current solution."""
    n = len(S)
    vc = vseed.copy()
    fwd = vc.copy()
    for i in range(1, n):
        v = fwd[i - 1]
        acc = min(a_trac(v), a_pow(v)) - a_drag(v) - G * grade[i - 1]
        fwd[i] = min(vc[i], math.sqrt(max(v * v + 2.0 * acc * ds, 1.0)))
    bwd = fwd.copy()
    for i in range(n - 2, -1, -1):
        v = bwd[i + 1]
        dec = a_brk(v) + a_drag(v) + G * grade[i]
        bwd[i] = min(fwd[i], math.sqrt(max(v * v + 2.0 * dec * ds, 1.0)))
    return bwd



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="build_telemetry")
