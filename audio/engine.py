"""THE POWER UNIT. A 1.6 L V6 turbo hybrid, built as a mechanism.

Everything below is synthesised. There is no sample, no loop, no recorded engine
anywhere in this file or in anything it imports.

WHAT IS ACTUALLY MODELLED
-------------------------
* FIRING ORDER, not "a fundamental". A 90-degree V6 with a 120-degree crank
  spacing fires 1-4-3-6-2-5. Bank A (1,2,3) therefore fires at crank angles
  0/240/480 and bank B (4,5,6) at 120/360/600 -- each bank an even 240-degree
  train, the two banks 120 degrees apart. The banks are generated separately,
  each is driven through ITS OWN primary + collector pipe, and only then summed.
  A single even 3/rev impulse train would be numerically equivalent in its line
  spectrum and audibly wrong in its texture, because the two banks' pipes are
  not the same length.

* EXHAUST AS A PIPE, not as a formant curve. The primaries are modelled as
  quarter-wave resonators closed at the valve (c_hot / 4L, odd orders) and the
  collector + tailpipe as half-wave open-open resonators (c_hot / 2L, all
  orders). c_hot = 686 m/s at a 900 C gas temperature, from the same
  331.3*sqrt(1+T/273.15) used for the air outside. That is where the note's
  formants come from; they are consequences of two lengths, not tuned constants.

* TURBO with a real shaft. Shaft speed lags manifold demand through a
  first-order inertia (tau = 240 ms spooling, 900 ms coasting down -- a turbo
  spools far faster than it slows), so lifting off leaves the compressor still
  turning. The whine sits on shaft ORDERS, and the surge/flutter on a closed
  throttle is generated from the pressure the compressor is still making.

* MGU-H on the same shaft (its whine is electrical, so it is a much purer tone
  than the blade noise), and MGU-K harvesting under braking and deploying under
  power.

* OVERRUN. With the throttle shut the injectors cut: the combustion pulse train
  stops, the pumping noise does not, and unburnt charge lights in the hot pipe
  as pops. Driven from a throttle derived from the circuit spec's OWN vehicle
  model (a_power = 800/v, a_drag = 0.00092 v^2, a_traction = min(11+0.0022v^2,
  20)), not from a hand-drawn curve.

* SHIFTS. Upshift: 80-120 ms torque interruption with an ignition crack on
  re-engage. Downshift: a throttle blip that pulls the revs UP to match the
  lower gear, with the crackle that follows.

* THE LAUNCH. From rest the engine is not tied to the wheels at all -- the
  clutch slips. The lock fraction is taken from the telemetry's own slip ratio
  (wheel surface speed against ground speed), which runs 0.96 at the first frame
  and closes over ten frames, so the crossfade from launch-control hold to
  wheel-derived rpm is measured, not drawn.

CLOCKS
------
Everything in here is synthesised on the WORLD clock. Beat 3's ramp is applied
once, later, by warping the finished world-clock signal onto the film clock in
`master.py` -- so the engine smears down in pitch and stretches in time by
exactly the same factor as the picture, with no special case anywhere in this
file.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _sig

from . import dsp
from .scene import WHEEL_R          # one definition, in scene.py

# ---------------------------------------------------------------- driveline --
# THE GEARBOX IS SOLVED, NOT GUESSED, AND THE FIRST VERSION OF IT WAS WRONG.
#
# The telemetry's own peak is 91.888 m/s (330.8 km/h, the circuit spec headline).
# Eighth is chosen as a long top that pulls 13,200 rpm there, 1,200 short of the
# shift point, which fixes the final drive exactly:
#     wheel_rps = 91.888 / (2*pi*0.36) = 40.626
#     FD = 13200 / (40.626 * 0.84 * 60) = 6.4471
# The eight ratios are then geometric with r1/r8 = 3.5, which puts first's top
# at 103.1 km/h and eighth's at 360.9 km/h.
#
# WHAT THE FIRST TABLE DID, WRITTEN DOWN SO IT IS NOT REPEATED: with
# [2.94 .. 0.84] and FD 6.10, seventh already stayed under the shift point at
# vmax, so the ladder stopped at seventh and EIGHTH GEAR WAS NEVER SELECTED IN
# THE WHOLE FILM. A gear table with a dead top gear is exactly the kind of
# plausible-looking artefact this project keeps producing, so the check is now a
# reported number: `gear_max` must reach 7 (index) and `rpm_at_vmax` must land
# near 13,200.
GEAR_RATIOS = np.array([2.9400, 2.4582, 2.0554, 1.7186, 1.4370, 1.2015, 1.0046, 0.8400])
FINAL_DRIVE = 6.4471
RPM_IDLE = 4300.0
RPM_MAX = 15000.0
RPM_SHIFT_UP = 14400.0
RPM_LAUNCH_HOLD = 10800.0
IDLE_THROTTLE = 0.08         # the throttle that holds an idle with no road load
LAUNCH_DECAY_S = 1.20        # clutch take-up: how fast the hold bleeds to idle
DRIVELINE_TAU_S = 0.090      # see scene.py: also what filters R2-026's seam

C_EXHAUST = 331.3 * np.sqrt(1.0 + 900.0 / 273.15)      # 686 m/s at 900 C
PRIMARY_L = (0.62, 0.66)      # m, bank A / bank B -- deliberately unequal
COLLECTOR_L = 1.15            # m, collector to turbine
TAILPIPE_L = 0.55             # m


def throttle_from_spec(v, accel_long, spec):
    """Throttle 0..1 and brake 0..1, from the circuit spec's vehicle model."""
    vm = spec["vehicle_model"]
    v = np.maximum(np.asarray(v, dtype=np.float64), 0.5)
    a_drag = 0.00092 * v * v
    a_pow = np.minimum(800.0 / v, np.minimum(11.0 + 0.0022 * v * v, 20.0))
    need = np.asarray(accel_long, dtype=np.float64) + a_drag
    thr = np.clip(need / np.maximum(a_pow, 1e-6), 0.0, 1.0)
    a_brake = np.minimum(1.25 + 2.2e-4 * v * v, 5.0) * 9.81
    brake = np.clip(-(np.asarray(accel_long) + a_drag) / a_brake, 0.0, 1.0)
    _ = vm
    return thr, brake


def gear_and_rpm(v, slip, wheel_w, sr, t_world, ignition_t, idle_until_t):
    """(rpm, gear, clutch_lock) on the world grid.

    Gear choice: the LOWEST gear that stays under the upshift point, which is
    what a driver does -- the lowest usable gear gives the most torque and the
    highest revs. Taking the HIGHEST gear under the shift point instead (the
    obvious-looking version) puts a descending ratio table permanently in eighth
    and silently kills every shift transient in the film.
    """
    v = np.asarray(v, dtype=np.float64)
    wheel_rps = v / (2.0 * np.pi * WHEEL_R)
    r_all = wheel_rps[:, None] * GEAR_RATIOS[None, :] * FINAL_DRIVE * 60.0
    ok = r_all <= RPM_SHIFT_UP
    gear = np.where(ok.any(axis=1), ok.argmax(axis=1), GEAR_RATIOS.shape[0] - 1).astype(np.int8)

    # hold a gear for at least 120 ms so a noisy speed track cannot hunt
    hold = int(0.12 * sr)
    g = gear.copy()
    last = g[0]
    since = hold
    step = max(hold // 4, 1)
    for i in range(0, g.shape[0], step):
        if g[i] != last:
            if since < hold:
                g[i:i + step] = last
                since += step
                continue
            last = g[i]
            since = 0
        else:
            since += step
    gear = g

    rpm_wheel = np.take_along_axis(r_all, gear[:, None].astype(np.int64), axis=1)[:, 0]

    # THE CLUTCH. From rest the engine is not tied to the wheels at all. It is
    # held near RPM_LAUNCH_HOLD and the clutch slips; the hold bleeds toward idle
    # as the clutch takes up, and the engine follows whichever is HIGHER --
    # which is the slipping clutch at first and the gearbox once the road speed
    # has caught up. That crossover IS the classic launch shape: the revs drop as
    # the clutch loads, then climb again as the car accelerates.
    #
    # It is not driven off the tyre-slip flag alone. The telemetry sanctions
    # wheelspin for ten frames only (0.42 s, ending at 7 km/h); a clutch that
    # locked there would put the engine at 900 rpm, i.e. stalled. Slip is used
    # instead to gate the wheelspin FLARE (see `lock` below), and the engine's
    # own speed comes from the max().
    hold = RPM_IDLE + (RPM_LAUNCH_HOLD - RPM_IDLE) * np.exp(
        -np.maximum(t_world, 0.0) / LAUNCH_DECAY_S)
    hold = np.where(t_world >= 0.0, hold, RPM_IDLE)
    rpm = np.maximum(rpm_wheel, hold)
    lock = np.clip(rpm_wheel / np.maximum(rpm, 1.0), 0.0, 1.0)

    # before the launch the engine is at idle; before ignition it is not running
    pre = t_world < idle_until_t
    rpm = np.where(pre, RPM_IDLE, np.maximum(rpm, RPM_IDLE))
    crank = np.clip((t_world - ignition_t) / 0.9, 0.0, 1.0)     # starter -> catch
    rpm = np.where(t_world < ignition_t, 0.0, rpm * np.where(pre, crank, 1.0))

    rpm = np.clip(rpm, 0.0, RPM_MAX)
    # driveline + rotating-assembly inertia
    rpm = dsp.onepole_lag(rpm, DRIVELINE_TAU_S, sr, init=0.0)
    return rpm, gear, lock


def _resonators(x, freqs, qs, gains, sr):
    """Sum of 2-pole peaking resonators -- a pipe's modes, not an EQ curve."""
    out = np.zeros(x.shape[0], dtype=np.float64)
    for f, q, gn in zip(freqs, qs, gains):
        if f >= sr * 0.45:
            continue
        w0 = 2.0 * np.pi * f / sr
        alpha = np.sin(w0) / (2.0 * q)
        b = np.array([alpha, 0.0, -alpha])
        a = np.array([1.0 + alpha, -2.0 * np.cos(w0), 1.0 - alpha])
        out += gn * _sig.lfilter(b / a[0], a / a[0], x)
    return out


def _primaries(x, primary_l, sr):
    """One bank's primaries: a quarter-wave tube closed at the exhaust valve."""
    f = [C_EXHAUST / (4.0 * primary_l) * k for k in (1, 3, 5, 7)]
    return _resonators(x, f, [7.0] * 4, [1.00, 0.55, 0.32, 0.20], sr)


def _collector_tail(x, sr):
    """The COMMON path: both banks merge into one collector, one turbine, one
    tailpipe. Routing each bank through its own full pipe -- which the first
    version did -- leaves the 1.5-per-revolution bank order uncancelled, and a
    V6 whose two banks share a turbine does not have a half-order burble. It is
    also what made the exhaust's strongest line 340 Hz when the firing
    fundamental was 681 Hz.
    """
    f_col = [C_EXHAUST / (2.0 * COLLECTOR_L) * k for k in (1, 2, 3, 4, 5)]
    f_tail = [C_EXHAUST / (2.0 * TAILPIPE_L) * k for k in (1, 2, 3)]
    y = _resonators(x, f_col, [5.0] * 5, [0.85, 0.50, 0.34, 0.24, 0.16], sr)
    y += _resonators(x, f_tail, [4.0] * 3, [0.45, 0.28, 0.18], sr)
    return y


def synth(t_world, v, accel_long, slip, wheel_w, spec, sr,
          ignition_t=-2.30, idle_until_t=-0.05, seed=20260802):
    """The whole power unit on the world grid. Returns (mono signal, info)."""
    n = t_world.shape[0]
    rng = np.random.default_rng(seed)
    rpm, gear, lock = gear_and_rpm(v, slip, wheel_w, sr, t_world, ignition_t, idle_until_t)
    thr, brake = throttle_from_spec(v, accel_long, spec)
    # AN ENGINE THAT IS RUNNING IS BEING FUELLED (R2-954).
    #
    # `throttle_from_spec` inverts a ROAD-LOAD model: the throttle needed to
    # produce a given acceleration THROUGH A CLOSED CLUTCH. Below the speed at
    # which first gear pulls idle -- RPM_IDLE / (r1 * FD * 60) * 2*pi*R =
    # 8.55 m/s -- there is no closed clutch and the model has nothing to say.
    # `gear_and_rpm` already knows that: it holds the crank at RPM_IDLE and
    # reports `lock`, the fraction of engine speed the gearbox is actually
    # supplying.
    #
    # Without this the car that stops on the pit straight at f2936 sits at
    # 4,300 rpm with `thr` = 2e-5, so `fuel` = 3e-4 and the injectors are CUT:
    # the last sound in the film was a motored engine at 12.8 % of its
    # combustion gate, which is a stall, not an idle. The floor is the same
    # 0.08 the pre-launch idle already uses, faded in with the clutch, and it
    # is a `maximum` so it is a bit-exact no-op wherever the road-load model
    # has an answer -- measured over the whole film, it is inactive until world
    # t = 78.06 s, which is 5.5 s past the end of the telemetry.
    thr = np.maximum(thr, IDLE_THROTTLE * (1.0 - lock))
    running = (t_world >= ignition_t)
    thr = np.where(t_world < idle_until_t, IDLE_THROTTLE, thr) * running
    brake = brake * running

    # --- shift events -----------------------------------------------------
    # EVERY EVENT DRAWS FROM ITS OWN STREAM, KEYED ON ITS OWN SAMPLE INDEX
    # (R2-958). One shared `rng` walked through the upshifts, then the
    # downshifts, then the overrun pops, so the pops' stream position was a
    # function of HOW MANY SHIFTS THE FILM CONTAINED. The lap-down adds seven
    # downshifts in the last 11 s; those seven draws re-seeded every pop in the
    # film, and the first overrun of the lap -- world t 10.809, 61.8 s BEFORE
    # the end of the telemetry -- came out different. That was the last leak of
    # the ending into the film, and it was the one a block-boundary argument
    # could never have explained: it is 61 seconds early, not 21 milliseconds.
    #
    # Keying on `int(i)` also makes the stream independent of event ORDER, so
    # neither a new event nor a re-ordered one can perturb an existing one.
    def _ev_rng(kind, i):
        return np.random.default_rng([seed, kind, int(i)])

    dg = np.diff(gear.astype(np.int16), prepend=gear[0])
    up = np.flatnonzero(dg > 0)
    dn = np.flatnonzero(dg < 0)
    cut = np.ones(n)
    crack = np.zeros(n, dtype=np.float32)
    blip = np.zeros(n)
    n_dip = int(0.095 * sr)
    for i in up:
        a, b = int(i), min(int(i) + n_dip, n)
        if b <= a:
            continue
        w = np.linspace(0.0, np.pi, b - a)
        cut[a:b] *= 1.0 - 0.62 * np.sin(w) ** 2       # seamless box: not a full cut
        ncr = min(int(0.014 * sr), b - a)
        env = np.exp(-np.linspace(0.0, 9.0, ncr))
        crack[b - ncr:b] += (_ev_rng(1, i).standard_normal(ncr) * env * 0.40).astype(np.float32)
    n_bl = int(0.13 * sr)
    for i in dn:
        a, b = int(i), min(int(i) + n_bl, n)
        if b <= a:
            continue
        w = np.linspace(0.0, np.pi, b - a)
        blip[a:b] += 900.0 * np.sin(w) ** 2           # rev-match blip, rpm
        ncr = min(int(0.05 * sr), b - a)
        env = np.exp(-np.linspace(0.0, 5.0, ncr))
        crack[a:a + ncr] += (_ev_rng(2, i).standard_normal(ncr) * env * 0.5).astype(np.float32)
    rpm_eff = np.clip(rpm + blip, 0.0, RPM_MAX)

    # --- crank phase ------------------------------------------------------
    f_crank = rpm_eff / 60.0
    ph_crank = dsp.integrate_phase(f_crank, sr)
    # cycle-to-cycle combustion irregularity: no crankshaft holds a frequency
    # exactly, and perfectly flat partials are the clearest tell of a synth.
    #
    # THE JITTER IS 0.4 % OF THE INSTANTANEOUS CRANK SPEED, NOT 0.4 % OF THE
    # FILM'S MEAN CRANK SPEED (R2-956). It was written as
    #
    #     ph += 0.004 * cumsum(jit) * (2*pi/sr) * f_crank.mean()
    #
    # and `f_crank.mean()` is a reduction over the WHOLE WORLD GRID. That one
    # scalar made every sample of the engine a function of every other sample of
    # the engine: changing only the last 11 s of the film changed the crank phase
    # from sample 42 onward. Measured on a 20 s bench where only the second half
    # of the speed track was altered:
    #
    #     rpm over the first half            bit-identical
    #     engine signal over the first half  first difference at sample 42 of
    #                                        960,000; delta RMS 0.0287 against a
    #                                        signal RMS of 0.0489, i.e. -4.6 dB
    #
    # It is inaudible -- same rpm, same gears, same pipes, a differently seeded
    # wander -- and it is still a defect, because it means the film before a
    # change cannot be shown to survive the change, and R2-943 is exactly such a
    # change.
    #
    # The replacement is a prefix sum and therefore causal, and it is the more
    # physical statement of the two: cycle-to-cycle variation is a fraction of
    # the speed the crank is turning AT THAT MOMENT, so it is small at a 4,300 rpm
    # idle and large at 14,400 rpm, where the old form applied the film's average
    # to both.
    jit = dsp.lp(dsp.white(n, seed + 1), 7.0, sr, 2)
    jit = jit / max(float(np.abs(jit).max()), 1e-9)
    ph_crank = ph_crank + 0.004 * np.cumsum(jit * f_crank) * (2.0 * np.pi / sr)

    # --- combustion pulse trains, per bank --------------------------------
    # 720-degree cycle: bank A at 0/240/480, bank B at 120/360/600.
    ph_cycle = ph_crank * 0.5                                  # one 720-deg cycle
    banks = []
    for bank, offsets in ((0, (0.0, 240.0, 480.0)), (1, (120.0, 360.0, 600.0))):
        train = np.zeros(n, dtype=np.float32)
        for k, off in enumerate(offsets):
            p = ph_cycle + off / 720.0 * 2.0 * np.pi
            # per-cylinder charge variation: real engines are not balanced
            train += dsp.phase_pulse(p, 0.055) * (1.0 + 0.05 * ((bank * 3 + k) % 5 - 2) / 2.0)
        banks.append(train)

    load = np.clip(0.25 + 0.75 * thr, 0.0, 1.0)
    fuel = np.clip(thr / 0.06, 0.0, 1.0)                       # injector cut on overrun
    fuel = dsp.onepole_lag(fuel, 0.02, sr)
    running_gain = np.clip(rpm_eff / RPM_IDLE, 0.0, 1.0)

    gate = (0.35 + 0.65 * load) * (0.25 + 0.75 * fuel) * cut
    dA = banks[0] * gate * 0.55
    dB = banks[1] * gate * 0.50
    exhaust = (_primaries(dA, PRIMARY_L[0], sr) + _primaries(dB, PRIMARY_L[1], sr)) * 0.60
    exhaust += _collector_tail(dA + dB, sr)
    exhaust *= running_gain

    # --- rasp: the irregular combustion energy ----------------------------
    # AM'd at the firing rate. Concentrated at 300-2600 Hz where exhaust energy
    # actually lives; a wide flat band renders as haze laid OVER the engine
    # instead of as the engine's own noise.
    noise = dsp.white(n, seed + 2)
    noise = _sig.sosfilt(dsp.sos_band(300.0, 2600.0, sr, 6), noise)
    fire = 0.5 * (1.0 + np.sin(dsp.integrate_phase(f_crank * 3.0, sr)))
    rasp = noise * (0.35 + 0.65 * fire ** 1.6)
    rasp *= np.interp(rpm_eff, [0.0, RPM_IDLE, RPM_MAX], [0.0, 0.10, 0.55]) * (0.4 + 0.6 * load)
    rasp *= cut

    # --- overrun: pumping air, and unburnt charge lighting in the pipe -----
    over = np.clip(1.0 - fuel, 0.0, 1.0) * (rpm_eff > RPM_IDLE * 1.3)
    pump = _sig.sosfilt(dsp.sos_band(120.0, 900.0, sr, 4), dsp.white(n, seed + 3))
    pump = pump * (0.5 + 0.5 * fire) * over * np.interp(rpm_eff, [RPM_IDLE, RPM_MAX], [0.05, 0.30])
    pops = np.zeros(n, dtype=np.float64)
    idx = np.flatnonzero(np.diff((over > 0.5).astype(np.int8)) > 0)
    for i in idx:
        r = _ev_rng(3, i)
        for k in range(r.integers(4, 11)):
            a = int(i) + int(r.uniform(0.02, 0.55) * sr)
            if a + 2000 >= n:
                continue
            L = int(r.uniform(0.004, 0.020) * sr)
            env = np.exp(-np.linspace(0.0, 7.0, L))
            pops[a:a + L] += r.standard_normal(L) * env * r.uniform(0.25, 1.0)
    pops = _sig.sosfilt(dsp.sos_band(180.0, 3500.0, sr, 4), pops) * 0.9

    # --- turbocharger -----------------------------------------------------
    # demand -> shaft speed, spool 240 ms, coast-down 900 ms (asymmetric on
    # purpose: a turbo accelerates far faster than it decelerates).
    demand = np.clip(rpm_eff / RPM_MAX, 0.0, 1.0) ** 0.55 * (0.25 + 0.75 * fuel)
    sh = np.empty(n)
    a_up = float(np.exp(-1.0 / (0.240 * sr)))
    a_dn = float(np.exp(-1.0 / (0.900 * sr)))
    # DEMAND IS READ AT THE BLOCK'S FIRST SAMPLE, NOT AVERAGED OVER THE BLOCK
    # (R2-957). `demand[a0:b0].mean()` reads 2,048 samples ahead of where the
    # resulting shaft speed is written, which put a 21.3 ms (at 96 kHz) backward
    # window on every change: with R2-956's jitter leak closed, this was the
    # ENTIRE remaining dependence of the film on its own ending -- the first
    # differing sample on a 20 s bench sat exactly on the block boundary
    # straddling the change, 765 samples early, at a magnitude of 0.0087 on a
    # signal of RMS 0.049. `demand` is a smooth function of rpm through a 90 ms
    # driveline lag and a 240/900 ms turbo inertia, so its value at the block's
    # start and its mean over 21 ms differ by far less than the quantisation the
    # block structure already imposes.
    blk = 2048
    acc = 0.0
    for a0 in range(0, n, blk):
        b0 = min(a0 + blk, n)
        m = float(demand[a0])
        c = a_up if m > acc else a_dn
        acc = m + (acc - m) * (c ** (b0 - a0))
        sh[a0:b0] = acc
    sh = dsp.lp(sh, 12.0, sr, 2)
    shaft_rps = sh * 125000.0 / 60.0                       # up to 125,000 rpm
    boost = sh ** 1.8

    ph_sh = dsp.integrate_phase(np.maximum(shaft_rps, 1.0), sr)
    whine = np.zeros(n, dtype=np.float64)
    for order, amp, det in ((6, 0.55, 1.0), (12, 0.40, 1.0027), (18, 0.16, 0.9981)):
        f = shaft_rps * order * det
        if float(np.nanmax(f)) < sr * 0.45:
            whine += amp * np.sin(dsp.integrate_phase(f, sr))
        else:
            m = f < sr * 0.45
            whine += amp * np.sin(dsp.integrate_phase(np.minimum(f, sr * 0.44), sr)) * m
    blade = _sig.sosfilt(dsp.sos_band(2500.0, 11000.0, sr, 4), dsp.white(n, seed + 4)) * 0.55
    turbo = (whine * 0.35 + blade) * boost * 0.055
    # compressor surge on a shut throttle while the shaft is still spinning
    flutter_rate = np.maximum(shaft_rps * 0.004, 8.0)
    flutter = np.abs(np.sin(dsp.integrate_phase(flutter_rate, sr)))
    surge = _sig.sosfilt(dsp.sos_band(700.0, 5000.0, sr, 4), dsp.white(n, seed + 5))
    turbo += surge * flutter * over * boost * 0.10

    # --- MGU-H (on the turbo shaft) and MGU-K -----------------------------
    mguh = np.sin(dsp.integrate_phase(np.minimum(shaft_rps * 2.0, sr * 0.44), sr)) * 0.6
    mguh += np.sin(dsp.integrate_phase(np.minimum(shaft_rps * 4.0, sr * 0.44), sr)) * 0.25
    mguh *= boost * 0.016
    harvest = dsp.onepole_lag(np.clip(brake, 0.0, 1.0), 0.06, sr)
    deploy = dsp.onepole_lag(np.clip(thr, 0.0, 1.0), 0.10, sr)
    f_k = np.clip(rpm_eff / 60.0 * 26.0, 0.0, sr * 0.44)
    mguk = (np.sin(dsp.integrate_phase(f_k, sr)) * 0.7
            + np.sin(dsp.integrate_phase(np.minimum(f_k * 1.5, sr * 0.44), sr)) * 0.3)
    mguk *= (harvest * 0.055 + deploy * 0.018)

    # --- starter motor, before the catch ----------------------------------
    st = np.clip((t_world - ignition_t) / 0.55, 0.0, 1.0) * np.clip(
        (ignition_t + 0.9 - t_world) / 0.35, 0.0, 1.0)
    st = np.clip(st, 0.0, 1.0)
    f_st = 240.0 + 300.0 * np.clip((t_world - ignition_t) / 0.9, 0.0, 1.0)
    starter = (np.sin(dsp.integrate_phase(f_st, sr)) * 0.5
               + np.sin(dsp.integrate_phase(f_st * 2.0, sr)) * 0.2)
    starter += _sig.sosfilt(dsp.sos_band(400.0, 4000.0, sr, 4), dsp.white(n, seed + 6)) * 0.5
    starter *= st * 0.05

    # BALANCE, MEASURED AND CORRECTED. At exhaust 0.085 / rasp 0.55 the rasp ran
    # 6x the exhaust in RMS and OWNED the spectrum: the strongest line in a
    # 13,011 rpm pull was a random noise peak at 1,150 Hz, not the 681 Hz firing
    # fundamental, and the f0 tracker in verify.py -- correctly -- could not find
    # an engine in it. A V6 that measures as filtered noise is filtered noise.
    # The harmonic exhaust now leads by about 5:1 in RMS and the rasp is texture
    # under it, which is the relationship a real exhaust has.
    sig = (exhaust * 0.55 + rasp * 0.13 + pump * 0.35 + pops * 0.15
           + turbo + mguh + mguk + crack.astype(np.float64) * 0.30 * running_gain
           + starter)
    # the pipe's own radiation rolloff: a tailpipe is not a full-range driver
    sig = _sig.sosfilt(_sig.butter(1, 11000.0, btype="lowpass", fs=sr, output="sos"), sig)
    sig = _sig.sosfilt(_sig.butter(2, 28.0, btype="highpass", fs=sr, output="sos"), sig)

    idling = t_world >= idle_until_t
    info = {
        "rpm_min_running": float(rpm_eff[idling].min()) if idling.any() else 0.0,
        "rpm_max": float(rpm_eff.max()),
        "gear_min": int(gear.min()), "gear_max": int(gear.max()),
        "upshifts": int(up.shape[0]), "downshifts": int(dn.shape[0]),
        "final_drive": FINAL_DRIVE, "gear_ratios": GEAR_RATIOS.tolist(),
        "rpm_at_vmax": float(rpm_eff[np.argmax(v)]),
        "vmax_ms": float(np.max(v)),
        "c_exhaust_ms": float(C_EXHAUST),
        "primary_quarter_wave_hz": [float(C_EXHAUST / (4.0 * L)) for L in PRIMARY_L],
        "collector_half_wave_hz": float(C_EXHAUST / (2.0 * COLLECTOR_L)),
        "turbo_shaft_rpm_max": float(shaft_rps.max() * 60.0),
        "overrun_fraction": float((over > 0.5).mean()),
        "throttle_mean": float(thr[running].mean()) if running.any() else 0.0,
        "clutch_lock_at_t0": float(lock[np.searchsorted(t_world, 0.0)]),
    }
    return sig.astype(np.float32), rpm_eff, gear, info
