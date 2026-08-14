"""THE POWER UNIT. A 1.6 L V6 turbo hybrid, built as a mechanism.

Everything below is synthesised. There is no sample, no loop, no recorded engine
anywhere in this file or in anything it imports.

WHAT IS ACTUALLY MODELLED
-------------------------
* FIRING ORDER, not "a fundamental". A 90-degree V6 with a 120-degree crank
  spacing fires 1-4-3-6-2-5. Bank A (1,2,3) therefore fires at crank angles
  0/240/480 and bank B (4,5,6) at 120/360/600. Each of the SIX cylinders gets
  its own blowdown, its own charge and its own primary pipe; they meet for the
  first time in the collector. A single even 3/rev impulse train would be
  numerically equivalent in its line spectrum and audibly wrong in its texture.

* EXHAUST AS A PIPE, and as a DELAY LINE rather than as a handful of tuned
  bandpasses. Six quarter-wave primaries closed at the valve (odd orders of
  c_hot/4L) feed a shared half-wave collector and tailpipe (all orders of
  c_hot/2L), each a bidirectional waveguide with a frequency-dependent loss at
  the open end. c_hot = 686 m/s at a 900 C gas temperature, from the same
  331.3*sqrt(1+T/273.15) used for the air outside. The formants are consequences
  of eight lengths, not tuned constants -- and the mode series is COMPLETE to
  Nyquist rather than truncated at its first three or four terms.

* BLOWDOWN, not a bump. The exhaust valve cracks against 8-12 bar, the flow
  chokes at once and the pressure front is close to a shock. Load sets the
  steepness of that front, so the engine gets harmonically richer under power
  and thins off-throttle instead of merely changing volume.

  THESE THREE ARE R2-1401, AND THEY ARE THE CLIENT'S "HAIR BLOWER". The truncated
  modal bank stopped at 1,936 Hz and the excitation was a raised cosine whose
  spectrum was gone by 2 kHz, so every octave above that in the whole film was
  produced by noise generators. Measured on the shipped master, the harmonic-to-
  noise ratio above 2.6 kHz was -0.65 dB. The numbers are in `verify.py`'s
  `harmonic` gate, which exists so that this class of defect is a failing test
  and not an opinion.

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
PRIMARY_L = (0.62, 0.66)      # m, bank A / bank B -- nominal, per bank
COLLECTOR_L = 1.15            # m, collector to turbine
TAILPIPE_L = 0.55             # m

# SIX PRIMARIES, NOT TWO (R2-1401).
#
# The old model ran one pipe per BANK, so all three cylinders of a bank were
# excited into an identical resonator and their partials landed on top of each
# other exactly. That is a synthesiser's engine: perfectly stacked partials with
# a smooth envelope. A real one has a spiky, irregular partial profile, and the
# reason is geometric -- the three cylinders of a bank sit ~98 mm apart along the
# block and the collector is at one end of it, so their primaries CANNOT be the
# same length. Teams equalise with bends and get close; they do not get equal.
#
# Modelled as +/-6 % about each bank's nominal, which puts the six quarter-wave
# fundamentals at 260-295 Hz -- a CLUSTER of six slightly detuned pipe series
# rather than two. Every harmonic of the firing frequency therefore meets a
# different sum of six pipe responses, which is where an uneven partial profile
# comes from. It is also why the two banks beat against each other instead of
# summing to a single clean note.
PRIMARY_L_CYL = (
    PRIMARY_L[0] * 1.060, PRIMARY_L[0] * 1.000, PRIMARY_L[0] * 0.941,   # bank A
    PRIMARY_L[1] * 1.058, PRIMARY_L[1] * 0.997, PRIMARY_L[1] * 0.945,   # bank B
)
# Firing order 1-4-3-6-2-5 on a 120-degree crank: bank A (cyl 1,2,3) fires at
# crank 0/240/480, bank B (cyl 4,5,6) at 120/360/600, both inside the 720-degree
# cycle. Index here is the cylinder, matching PRIMARY_L_CYL.
CYL_PHASE_DEG = (0.0, 240.0, 480.0, 120.0, 360.0, 600.0)

# ===================== THE FIRING GEOMETRY, B7 (R2-4066) =====================
# FIA 2025 Art. 5.2.10 permits the crankshaft only THREE con-rod journals, and
# Art. 5.2.7 fixes the vee at 90 degrees. Three journals shared between six
# cylinders in a 90-degree vee is not a free choice of firing angles: the two
# cylinders on a journal are forced 90 degrees apart, and the three journals sit
# at 120-degree intervals. That gives 0/90, 240/330, 480/570 -- an UNEVEN
# 90/150/90/150/90/150 pattern whose period is 240 degrees of crank, i.e. TWO
# THIRDS of a revolution. The firing fundamental is therefore engine order 1.5,
# half of the even-fired 3.
#
# The spectrum falls out exactly. The 240-degree pattern is two pulses 90
# degrees = a quarter revolution apart, so the even comb is multiplied by
# |1 + exp(-i 2 pi m / 4)| = 2|cos(pi m / 4)| at engine order m:
#
#     order   1.5    3.0    4.5    6.0    7.5    9.0   12.0
#     A(m)   0.383  0.707  0.924  0.000  0.924  0.707  1.000
#
# an EXACT null at order 6 and full strength at order 12, with order 1.5 sitting
# 20*log10(0.383/0.707) = -5.34 dB under order 3. That is what G-IDENTITY gates.
#
# THIS CONTRADICTS A REASONED DECISION IN THIS FILE (`_collector_tail`, which
# argues that a shared turbine collector leaves no half-order burble). Both can
# be partly right: a shared collector ATTENUATES the half order, it does not
# cancel it, and no measured F1 spectrum was obtainable to settle it -- every
# publisher returned 403. So it ships behind a weight, defaulting to the
# regulation geometry, with 0.0 restoring the even-fired engine exactly.
CYL_PHASE_DEG_UNEVEN = (0.0, 240.0, 480.0, 90.0, 330.0, 570.0)
HALF_ORDER_WEIGHT = 1.0       # 0.0 = even 120-degree crank, 1.0 = Art. 5.2.10
FIRING_ORDER_EVEN = 3.0
FIRING_ORDER_HALF = 1.5
# Per-cylinder TIMING dispersion, so the order-6 null is not mathematically
# perfect. Journal machining, rod length and valve-timing scatter put the real
# firing angles within a degree or two of nominal; 1.5 % of the mean 120-degree
# firing interval is 1.8 degrees. Stable per cylinder, declared not drawn, so
# the engine is the same engine in every render.
CYL_TIMING_DEG = (0.0, 1.42, -0.86, 1.03, -1.61, 0.55)


def firing_angles_deg(half_order_weight=HALF_ORDER_WEIGHT):
    """The six firing angles inside the 720-degree cycle.

    Interpolating the ANGLES rather than cross-fading two signals keeps exactly
    six blowdown events at every weight -- a cross-fade would put twelve pulses
    in the cycle at w = 0.5, which is not an engine.
    """
    w = float(np.clip(half_order_weight, 0.0, 1.0))
    a = np.asarray(CYL_PHASE_DEG, dtype=np.float64) * (1.0 - w) \
        + np.asarray(CYL_PHASE_DEG_UNEVEN, dtype=np.float64) * w
    return a + np.asarray(CYL_TIMING_DEG, dtype=np.float64)


# ===================== THE WASTEGATE TAILPIPE (Art. 5.9.2) ===================
# The regulations mandate a SEPARATE wastegate exhaust and cap its exit area at
# 1500 mm^2. Everything about this path is that number and the gas path it sits
# on; nothing here is a tone control.
WASTEGATE_AREA_MM2 = 1500.0
_WG_A = np.sqrt(WASTEGATE_AREA_MM2 * 1e-6 / np.pi)          # 21.85 mm radius
WASTEGATE_L = 0.35            # m, collector bypass to the exit -- short by design
# radiated pressure is the derivative of volume flow up to ka ~ 1, so the
# radiation corner is c_air / (2 pi a). 2493 Hz here against 840 Hz for the
# 65 mm main tailpipe: the wastegate is brighter BECAUSE the regulation makes it
# small, which is the physical fact `rasp` was standing in for.
WASTEGATE_RAD_HZ = float(343.0 / (2.0 * np.pi * _WG_A))
# CORRECTED AFTER THE R2-4069 RENDER, AND THE INCONSISTENCY IS NOT MINE.
# `_collector_tail` states "for a 65 mm tailpipe that corner is c_air/(2*pi*a) ~
# 840 Hz", which only holds if 65 mm is the RADIUS -- a 130 mm bore, larger than
# any F1 tailpipe. The figure is inherited from that comment; this line is set to
# agree with it so the two numbers in one file cannot disagree, and both readings
# are written down rather than one being quietly picked. `master_R2-4069.json`
# was rendered before this correction and carries 1679.7 Hz in its report; the
# audio is unaffected, because nothing reads this constant except the report.
TAILPIPE_RAD_HZ = float(343.0 / (2.0 * np.pi * 0.065))      # 840 Hz, per _collector_tail
# area ratio against a 65 mm main pipe: how much of the collector's wave takes
# the bypass when the gate is fully open
# THE OPEN QUESTION THIS LEAVES, STATED. Against a 32.5 mm radius this is
# 0.452; against the 65 mm radius `_collector_tail` declares it is 0.113, i.e.
# 12 dB lower. The R2-4069 render used 0.452 and DELIVERED the wastegate at an
# RMS of 0.0317 against the main exhaust's 0.0759 -- 7.6 dB under it, which is a
# defensible level for a bypass path on its own terms. It is left at 0.452 with
# the arithmetic written down rather than moved on a number the file itself is
# not consistent about; the falsifier for the next pass is the measured RMS
# ratio, not this fraction.
WASTEGATE_AREA_FRAC = float(WASTEGATE_AREA_MM2 / (np.pi * 32.5 ** 2))
WASTEGATE_OPEN_SH = 0.55      # normalised shaft speed at which boost reaches
                              # target and the gate starts to bypass

COMPRESSOR_BB_LO_HZ = 4000.0  # see the blade-noise block in `synth`
COMPRESSOR_BB_HI_HZ = 13000.0
# per-cylinder charge scatter: no engine is balanced, and this is the residual
# after the ECU has trimmed each injector. +/-5 % is a normal figure.
CYL_CHARGE = (1.000, 0.962, 1.043, 0.978, 1.031, 0.986)

# THE PIPES WERE STRUCK, NOT DRIVEN (R2-2001). The client's second note was not
# "still noise", it was "a wind machine with someone banging on tubes". The
# banging is this block, and it is measurable rather than a matter of taste.
#
# Solve the comb loop's poles exactly -- the denominator of
# y[n] = x[n] -/+ g*LP(y[n-D]) is (1 - c z^-1) -/+ g(1-c) z^-D, a polynomial --
# and every mode's decay time falls out. At the shipped 0.70/0.62 the primary's
# fundamental had T60 = 37.7 ms and Q = 4.4, the collector 48.6 ms and Q = 6.5.
# A V6 at 11,000 rpm fires every 1.82 ms. So ALL 99 primary modes below 9 kHz
# rang for longer than the interval to the next firing event -- median 7.5x, worst
# 20.7x, and 100 % of them at every rpm in the film. A resonator still ringing at
# 20x the drive interval is not being driven by the engine; it is being struck by
# it, which is exactly the sound the client described.
#
# Note the overlap itself is NOT the defect and cannot be removed: at 11,000 rpm
# the firing interval (1.82 ms) is already shorter than one primary's acoustic
# round trip (1.91 ms), so a real engine also always has a previous pulse in the
# pipe. The DEPTH of the overlap is the defect -- 20 pulses ringing at once
# instead of 3 or 4.
#
# Why the gain and not the damping. The obvious fix -- steeper in-loop damping --
# is a trap, and the measurement says so. A lowpass inside the loop is dispersive,
# so lowering its corner or raising its order shortens the effective pipe for high
# modes and the series stops being harmonic. Measured max deviation from the odd
# c/4L series below 9 kHz: 1.4 % (24 cents) as shipped, 2.3 % at damp_hz 2400, and
# 20.5 % -- over two and a half semitones -- for a 3rd-order loop at 1200 Hz. An
# inharmonic partial series is the definition of a struck bell, so damping harder
# in the loop would have bought a quieter ring by making it a MORE bell-like one.
# damp_hz therefore does not move. The loop gain is frequency-flat in delay and
# is the only lever that shortens the ring without detuning the instrument.
#
# The physical reading of a lower number: the shipped values counted radiation
# from the open end and nothing else, and radiation alone really is that lossless
# -- an unflanged 42 mm pipe reflects ~0.98 at 1 kHz. What was missing is
# everything else a turbocharged exhaust does to a pressure wave: gas leaving at
# 100+ m/s convects energy out of the primary, and the turbine sitting past the
# collector is a near-total acoustic sink rather than a reflector. Both are
# broadband, and both belong in the round-trip magnitude.
PIPE_LOOP_GAIN = 0.34         # reflection magnitude per round trip at DC: was
                              # 0.70, radiation only. T60 at the fundamental
                              # 37.7 -> 12.5 ms, Q 4.36 -> 1.45, ring-through at
                              # 11,000 rpm 20.7x -> 6.9x.
PIPE_DAMP_HZ = 3200.0         # radiation loss rises with frequency: see comb_pipe.
                              # DO NOT LOWER: see the dispersion note above.
COLLECTOR_LOOP_GAIN = 0.14    # the turbine is a large, lossy obstruction -- and
                              # at 0.62 it was not modelled as nearly lossy
                              # enough: this was the longest-ringing element in
                              # the whole exhaust at T60 = 48.6 ms, Q = 6.5, and
                              # its 1.15 m round trip is already 1.84 firing
                              # intervals long before any ring is added. A
                              # turbine at racing mass flow is close to an
                              # anechoic termination -- extracting that energy is
                              # what it is FOR -- so it should return very little
                              # of the wave, which 0.62 plainly does not model.
                              # Now T60 11.9 ms, Q 1.59, which puts the collector
                              # at the same Q as the primaries (1.45) instead of
                              # 4.5x their ring.
COLLECTOR_DAMP_HZ = 2600.0


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


def _primary(x, primary_l, sr):
    """One CYLINDER's primary: a quarter-wave tube closed at the exhaust valve.

    A delay line, not a bank of four tuned bandpasses -- see `dsp.comb_pipe` for
    why the modal version was the defect. Closed at the valve and open into the
    collector, so the reflection at the far end inverts and the series is the odd
    orders of c/4L, all the way to Nyquist instead of stopping at the 7th.
    """
    D = 2.0 * primary_l / C_EXHAUST * sr             # round trip, in samples
    return dsp.comb_pipe(x, round(D), PIPE_LOOP_GAIN, PIPE_DAMP_HZ, sr, invert=True)


def _collector_tail(x, sr):
    """The COMMON path: all six primaries merge into one collector, one turbine,
    one tailpipe. Routing each bank through its own full pipe -- which a much
    earlier version did -- leaves the 1.5-per-revolution bank order uncancelled,
    and a V6 whose two banks share a turbine does not have a half-order burble.
    It is also what made the exhaust's strongest line 340 Hz when the firing
    fundamental was 681 Hz.

    Both sections are open at both ends (the collector opens into the turbine
    volute, the tailpipe into the air), so both take the ALL-order c/2L series.
    """
    D_col = round(2.0 * COLLECTOR_L / C_EXHAUST * sr)
    D_tail = round(2.0 * TAILPIPE_L / C_EXHAUST * sr)
    y = dsp.comb_pipe(x, D_col, COLLECTOR_LOOP_GAIN, COLLECTOR_DAMP_HZ, sr)
    y = dsp.comb_pipe(y, D_tail, PIPE_LOOP_GAIN * 0.8, PIPE_DAMP_HZ, sr)
    # RADIATION FROM THE OPEN END. A pipe mouth is a poor radiator at low
    # frequency and an efficient one above ka ~ 1: the radiated pressure is the
    # time derivative of the volume flow, i.e. a +6 dB/octave tilt, shelving flat
    # once the mouth is large compared with the wavelength. For a 65 mm tailpipe
    # that corner is c_air/(2*pi*a) ~ 840 Hz. Implemented as a first-order shelf
    # rather than a true differentiator so it does not run away at Nyquist.
    #
    # This is not a brightener bolted on. It is the last physical stage of the
    # exhaust and it was simply missing: the old modal bank returned the pressure
    # INSIDE the pipe and radiated it unchanged.
    b, a = _sig.butter(1, 840.0, btype="highpass", fs=sr)
    return 0.45 * y + 0.85 * _sig.lfilter(b, a, y)


def synth(t_world, v, accel_long, slip, wheel_w, spec, sr,
          ignition_t=-2.30, idle_until_t=-0.05, seed=20260802,
          to_film=None, t_world_film=None, half_order_weight=HALF_ORDER_WEIGHT):
    """The whole power unit. Returns (signal, rpm, gear, info).

    THE TWO GRIDS, AND THE ONE LAW BETWEEN THEM  (R2-4064)
    -----------------------------------------------------
    Called with `to_film=None` this synthesises on whatever grid `t_world` is,
    which is what it has always done: `master.py` then ran the result through
    `WorldGrid.to_film`, a Catmull-Rom VARISPEED RESAMPLER. Beat 3's world clock
    runs down to a scale of 0.153719, so every partial the engine produced during
    the breach came out transposed 6.5051x down -- 31.4 semitones. Measured on the
    delivered master the engine's spectral centroid over 36-44 s is 217.7 Hz and
    it is 55 % of that beat's energy, which is why the breach reads 711.5 Hz
    against a 1200 Hz bar and 4.97 % above 4 kHz against 8 %.

    Called with `to_film` and `t_world_film` it does what R2-4035 already does for
    the shards: **the SCHEDULE is stretched and the PITCH is not.** Concretely,

      * everything that carries WORLD-TIME MEMORY -- the driveline/rotating-
        assembly lag (90 ms), the turbo shaft's 240/900 ms inertia, the injector
        lag, the MGU harvest/deploy lags, the launch clutch -- is integrated on
        the WORLD grid, where those time constants are the physical ones, and the
        resulting trajectory is then mapped onto the film grid;
      * everything that is a FREQUENCY -- crank phase, the pipe delay lines, the
        shaft-order tones, the filter corners -- is rendered in FILM-RATE samples
        at its true value, so a 690 Hz firing fundamental is 690 Hz on screen
        however slowly the picture is running.

    Real slow-motion sound design re-times events; it does not varispeed an
    engine two and a half octaves down. `tools/r2_4064_engine_grid_witness.py`
    measures both paths from the same telemetry and the same clock.

    `t_world_film` is world time at each FILM sample (`clock.world_at_film(
    clock.film_t)`), in float64 -- it is what every absolute-time gate in here
    (ignition, idle, starter) is compared against, so it must not be the float32
    that `to_film` returns.
    """
    n = t_world.shape[0]
    n_world = n
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

    # THE REV-MATCH BLIP IS PART OF THE TRAJECTORY, not of the voice: it is the
    # crank actually turning faster, and the turbo's inertia downstream has to
    # see it. So it is built here on the WORLD grid and carried into `rpm_eff`,
    # which is then mapped. The AUDIBLE shift envelopes (`cut`, `crack`) are
    # rebuilt below on whichever grid the voice is rendered on.
    dg_w = np.diff(gear.astype(np.int16), prepend=gear[0])
    blip_w = np.zeros(n_world)
    n_bl = int(0.13 * sr)
    for i in np.flatnonzero(dg_w < 0):
        a, b = int(i), min(int(i) + n_bl, n_world)
        if b <= a:
            continue
        blip_w[a:b] += 900.0 * np.sin(np.linspace(0.0, np.pi, b - a)) ** 2
    rpm_eff = np.clip(rpm + blip_w, 0.0, RPM_MAX)
    rpm_at_vmax = float(rpm_eff[int(np.argmax(v))])

    # --- the rest of the world-time memory, before the grid changes --------
    fuel = np.clip(thr / 0.06, 0.0, 1.0)                       # injector cut on overrun
    fuel = dsp.onepole_lag(fuel, 0.02, sr)
    # TURBO SHAFT. demand -> shaft speed, spool 240 ms, coast-down 900 ms
    # (asymmetric on purpose: a turbo accelerates far faster than it
    # decelerates). Those are WORLD seconds -- a turbocharger does not spool
    # faster because the camera is running slow -- so the integrator runs here,
    # on the world grid, and its output is mapped like every other trajectory.
    demand = np.clip(rpm_eff / RPM_MAX, 0.0, 1.0) ** 0.55 * (0.25 + 0.75 * fuel)
    sh = np.empty(n_world)
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
    for a0 in range(0, n_world, blk):
        b0 = min(a0 + blk, n_world)
        m = float(demand[a0])
        c = a_up if m > acc else a_dn
        acc = m + (acc - m) * (c ** (b0 - a0))
        sh[a0:b0] = acc
    sh = dsp.lp(sh, 12.0, sr, 2)
    del demand
    harvest = dsp.onepole_lag(np.clip(brake, 0.0, 1.0), 0.06, sr)
    deploy = dsp.onepole_lag(np.clip(thr, 0.0, 1.0), 0.10, sr)

    # ============ THE SCHEDULE IS MAPPED; THE PITCH IS NOT (R2-4064) ========
    if to_film is not None:
        if t_world_film is None:
            raise ValueError("to_film requires t_world_film (world time at each "
                             "film sample, float64)")
        tt = np.asarray(t_world_film, dtype=np.float64)
        n = tt.shape[0]

        def _map(x, lo=None, hi=None):
            y = np.asarray(to_film(np.asarray(x, dtype=np.float64)), dtype=np.float64)
            # Catmull-Rom is an interpolating cubic and can overshoot at a step,
            # so every mapped track is re-clipped to its own physical range.
            return y if (lo is None and hi is None) else np.clip(y, lo, hi)

        # gear is an INTEGER track: nearest-neighbour, never a cubic, so the
        # resample cannot invent a one-sample gear between two real ones.
        iw = np.clip(np.rint((tt - float(t_world[0])) * sr).astype(np.int64),
                     0, n_world - 1)
        gear = gear[iw]
        rpm_eff = _map(rpm_eff, 0.0, RPM_MAX)
        lock = _map(lock, 0.0, 1.0)
        thr = _map(thr, 0.0, 1.0)
        brake = _map(brake, 0.0, 1.0)
        fuel = _map(fuel, 0.0, 1.0)
        sh = _map(sh, 0.0, 1.0)
        harvest = _map(harvest, 0.0, 1.0)
        deploy = _map(deploy, 0.0, 1.0)
        running = tt >= ignition_t
        del iw
    else:
        tt = t_world
    del blip_w

    # --- the audible shift envelopes, on the VOICE's grid ------------------
    dg = np.diff(gear.astype(np.int16), prepend=gear[0])
    up = np.flatnonzero(dg > 0)
    dn = np.flatnonzero(dg < 0)
    cut = np.ones(n)
    crack = np.zeros(n, dtype=np.float32)
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
    for i in dn:
        a, b = int(i), min(int(i) + n_bl, n)
        if b <= a:
            continue
        ncr = min(int(0.05 * sr), b - a)
        env = np.exp(-np.linspace(0.0, 5.0, ncr))
        crack[a:a + ncr] += (_ev_rng(2, i).standard_normal(ncr) * env * 0.5).astype(np.float32)

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
    # DERIVATION: cycle-to-cycle combustion variation is correlated over a
    # handful of cycles, not from one cycle to the next -- the residual gas and
    # the wall temperature that cause it carry over. A V6 at 11,000 rpm runs
    # 91.7 cycles per second, so a correlation length of about a dozen cycles is
    # a 7 Hz corner. It is the persistence of the physical cause, not a smoothing
    # taste.
    # derivation: 7 Hz = a dozen firing cycles at racing rpm -- see above.
    jit = dsp.lp(dsp.white(n, seed + 1), 7.0, sr, 2)
    jit = jit / max(float(np.abs(jit).max()), 1e-9)
    ph_crank = ph_crank + 0.004 * np.cumsum(jit * f_crank) * (2.0 * np.pi / sr)

    # --- combustion pulse trains, one per CYLINDER ------------------------
    # 720-degree cycle. Each cylinder gets its own blowdown, its own charge and
    # its own primary pipe; they meet for the first time in the collector.
    ph_cycle = ph_crank * 0.5                                  # one 720-deg cycle

    # `fuel` was integrated on the world grid above, with the injector's own
    # lag, and mapped; everything on this line is memoryless in the mapped
    # tracks and is therefore simply evaluated here.
    load = np.clip(0.25 + 0.75 * thr, 0.0, 1.0)
    running_gain = np.clip(rpm_eff / RPM_IDLE, 0.0, 1.0)

    # THE PUMPING FLOOR IS 0.38, NOT 0.25 (R2-1401). With the injectors cut the
    # engine is still turning at 13,800 rpm and the pistons are still pushing a
    # full cylinder of air down each primary every cycle -- that motored pumping
    # pulse rings the pipes at the same 3-per-revolution firing rate, which is
    # why a real overrun is a hard hollow TONE and not a hiss. Under-driving the
    # pipe here is what left the broadband `pump` layer carrying the overrun on
    # its own: measured, harmonic content led broadband by only 1.3 dB through
    # every braking zone in the lap.
    gate = (0.35 + 0.65 * load) * (0.38 + 0.62 * fuel) * cut

    # LOAD SHAPES THE PULSE, NOT JUST ITS HEIGHT (R2-1401).
    #
    # The old model multiplied one fixed pulse shape by `gate`, so the ONLY thing
    # throttle did to the exhaust was change its volume. A source whose spectrum
    # never changes and whose level and pitch do is, precisely, a fan with a speed
    # control -- which is what the client heard.
    #
    # Physically, load is cylinder pressure at exhaust-valve opening. At full
    # throttle the valve cracks against three or four times the pressure it sees
    # on a trailing throttle, the flow chokes harder and sooner, and the blowdown
    # front is correspondingly steeper. Steeper front = more high harmonics. So
    # load drives the ATTACK FRACTION, and the engine gets genuinely harder and
    # brighter under power rather than just louder. Measured across the range
    # this moves the exhaust's spectral centroid by about an octave.
    attack = 0.30 - 0.20 * load * np.clip(fuel, 0.0, 1.0)
    # blowdown duration is roughly fixed in CRANK ANGLE (~61 degrees), which is
    # already what a phase-driven width means -- it shortens in time with rpm on
    # its own, with no rpm term here.
    #
    # BUT THE RISE HAS A FLOOR IN SECONDS, NOT IN CRANK ANGLE (R2-2002).
    #
    # `attack` above is a FRACTION of a crank-angle-fixed window, so the rise
    # time in seconds falls as 1/rpm with nothing stopping it. Measured at full
    # load it ran 237 us at 4,300 rpm and 71 us at 14,400 -- and a 71 us
    # raised-cosine edge is spectrally flat past 10 kHz. The consequence is the
    # worst possible coupling to the pipes: the excitation's energy above 2 kHz
    # rose 10.3 dB from idle to the limiter (-16.7 -> -6.3 dB of the total) so the
    # model hit the high modes hardest exactly where it also fired most often.
    # That is a hammer, and hammering a resonator is what the client heard as
    # tubes. R2-2001 shortens the ring; this stops striking it so hard.
    #
    # A real blowdown cannot rise that fast at any rpm. The pressure at the port
    # is set by choked discharge through the opening valve curtain, whose time
    # constant is V/(A_eff * c) -- a TIME, independent of crank speed. Higher
    # cylinder pressure chokes harder and discharges faster, so the floor is
    # shorter under load, which is the same direction R2-1401's load-shaping
    # already runs.
    #
    # The floor only ever LENGTHENS a rise, so below ~6,000 rpm it does nothing
    # at all and R2-1401's behaviour there is untouched, bit for bit. Where it
    # does bite it keeps the load span: at 14,400 rpm full load 180 us against
    # overrun 420 us is still 2.3x, where the unfloored model had 71 vs 212 us.
    rise_floor_s = 180e-6 + (420e-6 - 180e-6) * (1.0 - load * np.clip(fuel, 0.0, 1.0))
    cycle_s = 120.0 / np.maximum(rpm_eff, 1.0)               # one 720-deg cycle
    attack = np.clip(np.maximum(attack, rise_floor_s / (0.085 * cycle_s)), 0.02, 0.60)
    fire_deg = firing_angles_deg(half_order_weight)
    charges = []
    for cyl in range(6):
        p = ph_cycle + fire_deg[cyl] / 720.0 * 2.0 * np.pi
        charges.append(dsp.blowdown_pulse(p, 0.085, attack) * CYL_CHARGE[cyl])

    exhaust = np.zeros(n, dtype=np.float64)
    merged = np.zeros(n, dtype=np.float64)
    for cyl in range(6):
        d = charges[cyl] * gate * 0.52
        # what the primary radiates back up the bank, and what it hands the
        # collector -- the same wave, taken at two points on one pipe
        y = _primary(d, PRIMARY_L_CYL[cyl], sr)
        exhaust += y * 0.16
        merged += y
    exhaust += _collector_tail(merged, sr) * 0.55

    # --- THE WASTEGATE TAILPIPE (FIA 2025 Art. 5.9.2), a second, brighter,
    # --- TURBINE-BYPASSING pulse path.  R2-4066.
    #
    # This is the correct physical origin of the brightness that `rasp` -- a
    # band of white noise at 300-2600 Hz, i.e. the client's exact complaint band
    # -- was faking. The regulations mandate a separate wastegate exhaust of at
    # most 1500 mm^2, and what comes out of it has NOT been through the turbine:
    # it is blowdown straight off the collector, so it keeps the high harmonics
    # the turbine otherwise extracts, and it radiates from a much smaller mouth.
    #
    # 1500 mm^2 is an equivalent diameter of 43.7 mm (a = 21.9 mm), so its
    # radiation corner c_air/(2*pi*a) = 2493 Hz against the 65 mm main tailpipe's
    # 840 Hz -- the brightness is a consequence of the regulation's own area
    # limit and of nothing else.
    #
    # A wastegate is a boost-control device: it opens as the shaft approaches
    # the speed that makes target boost, and it is driven fully open on a shut
    # throttle to stop the turbine overspeeding. Both are in `wg` below.
    wg_open = np.clip((sh - WASTEGATE_OPEN_SH) / 0.30, 0.0, 1.0)
    wg_open = np.maximum(wg_open, np.clip(1.0 - fuel, 0.0, 1.0) * (sh > 0.25))
    wgas = dsp.comb_pipe(merged * wg_open, round(2.0 * WASTEGATE_L / C_EXHAUST * sr),
                         PIPE_LOOP_GAIN * 0.8, PIPE_DAMP_HZ, sr)
    _bw, _aw = _sig.butter(1, WASTEGATE_RAD_HZ, btype="highpass", fs=sr)
    wastegate = (0.30 * wgas + 1.00 * _sig.lfilter(_bw, _aw, wgas)) * WASTEGATE_AREA_FRAC
    del wgas
    exhaust *= running_gain
    wastegate *= running_gain
    del charges, merged

    # --- rasp and pump: DELETED (B7 / R2-4066) ----------------------------
    # `rasp` was `white -> bandpass(300, 2600) -> AM at the firing rate`, at
    # 0.085 of the sum. Three separate things were wrong with it and only the
    # third is arguable:
    #   1. 300-2600 Hz IS the client's complaint band. The one component of this
    #      engine that was broadband by construction was placed exactly where
    #      the complaint lives.
    #   2. It is a `white()` reaching a bus through a fixed filter, which is the
    #      construction G-CONSTRUCT exists to ban.
    #   3. Its own comment says it stands in for combustion irregularity -- but
    #      cycle-to-cycle irregularity is already modelled, twice and
    #      physically: the crank jitter at `ph_crank` and the per-cylinder charge
    #      scatter in `CYL_CHARGE`. It was modelling the same fact a third time,
    #      as noise.
    # `pump` was `white -> bandpass(120, 900)` for the overrun, and its own
    # comment already said the periodic part of the overrun goes down the
    # primaries with everything else (R2-1401 raised the pumping floor to 0.38
    # for exactly that reason). What is left after that is a hiss standing in
    # for a tone the waveguide is already producing.
    #
    # The overrun crackle -- `pops` -- is kept: it is an EVENT PROCESS (unburnt
    # charge lighting off in the pipe at discrete instants), not a stationary
    # bed, and it is the signature of this engine.
    over = np.clip(1.0 - fuel, 0.0, 1.0) * (rpm_eff > RPM_IDLE * 1.3)
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
    # `sh` -- the shaft speed -- was integrated on the WORLD grid above, because
    # 240 ms of spool is 240 ms of world time whatever the picture is doing, and
    # it has already been mapped onto this grid if there is one.
    shaft_rps = sh * 125000.0 / 60.0                       # up to 125,000 rpm
    boost = sh ** 1.8

    # TORQUE RIPPLE ON THE TURBINE (R2-1401). The turbine is not fed a steady
    # stream; it is hit by six blowdown pulses per cycle, so the shaft carries a
    # small speed ripple AT THE FIRING FREQUENCY. That ripple frequency-modulates
    # every compressor tone, putting sidebands a firing-interval either side of
    # each of them -- which is why a real turbo tone is grainy and locked to the
    # engine, and why an unmodulated sine at the same frequency reads as a test
    # tone. The depth falls with shaft speed because the rotating inertia is
    # fixed and the ripple has less of a cycle to act over: 0.9 % at spool,
    # ~0.2 % at 125,000 rpm.
    ripple = 0.009 / np.maximum(sh, 0.05) * 0.05
    shaft_rps = shaft_rps * (1.0 + np.clip(ripple, 0.0, 0.012)
                             * np.sin(dsp.integrate_phase(f_crank * 3.0, sr)))

    # THE TURBO WAS THE HAIR DRYER, ALMOST LITERALLY (R2-1401).
    #
    # It used to be `whine` on shaft orders 6/12/18 plus 2.5-11 kHz white noise at
    # 0.55 -- and the arithmetic makes the noise the whole story. At full boost the
    # shaft turns 2,083 rev/s, so order 6 lands at 12.5 kHz, order 12 at 25 kHz and
    # order 18 at 37 kHz: two of the three tones are ultrasonic whenever the car is
    # actually pulling, and the third is at the very top of hearing. Everything
    # audible from the turbocharger through the entire flying lap was therefore a
    # band of filtered white noise. A hair dryer IS a small compressor wheel making
    # broadband noise in a volute, so the client's description was not a metaphor;
    # he identified the component.
    #
    # WHAT A COMPRESSOR ACTUALLY RADIATES, in descending audibility here:
    #  * LOW SHAFT ORDERS (1-4). Rotor imbalance, and the pressure field sweeping
    #    past the asymmetric volute tongue once per revolution. 1.7-8 kHz across
    #    this shaft's range -- squarely audible, and roughly the "order of
    #    magnitude above the firing frequency" a turbo is heard at.
    #  * BLADE PASSING. The wheel has 7 full blades and 7 splitters, so the
    #    passage count is 14 and the splitters' shorter chord leaves order 7
    #    present as well. At 125,000 rpm those are ultrasonic, which is correct
    #    and is exactly why they must NOT be the only tonal content -- but during
    #    spool they sweep up through the audible band, and that rising tone is the
    #    sound of a turbo spooling.
    #  * BROADBAND. Real, and secondary. It is now a sixth of what it was, it is
    #    rolled off above 9 kHz, and it is modulated at the blade rate instead of
    #    being stationary hiss, because the turbulence is shed by passing blades.
    whine = np.zeros(n, dtype=np.float64)
    for order, amp, det in ((1, 0.34, 1.0), (2, 0.46, 1.0), (3, 0.30, 1.0019),
                            (4, 0.17, 0.9986), (7, 0.26, 1.0), (14, 0.38, 1.0),
                            (28, 0.10, 1.0)):
        f = shaft_rps * order * det
        lim = sr * 0.44
        # above Nyquist the tone does not exist; gate it rather than folding it
        m = (f < lim).astype(np.float64)
        whine += amp * np.sin(dsp.integrate_phase(np.minimum(f, lim), sr)) * m
    f_bpf = shaft_rps * 14.0
    blade_am = 0.55 + 0.45 * np.sin(dsp.integrate_phase(
        np.minimum(f_bpf, sr * 0.44), sr)) * (f_bpf < sr * 0.44)
    # THE COMPRESSOR'S BROADBAND IS KEPT ABOVE THE COMPLAINT BAND (B7 / R2-4066).
    # 1800-9000 Hz put a stationary noise band straight through 1.8-2.6 kHz,
    # which is where `rasp` also sat and where the client's word lives. What a
    # centrifugal compressor actually radiates broadband is blade-wake
    # turbulence, whose energy is carried at and above the blade-passing
    # frequency -- so the band's LOWER edge is 4 kHz by declaration and its
    # UPPER edge TRACKS THE SHAFT at 1.6 x BPF, clamped to 13 kHz. A band whose
    # top moves with the shaft cannot read as a fixed filter, which a stationary
    # one does.
    # DERIVATION: blade-wake turbulence carries its energy at and above the
    # blade-passing frequency, which for 14 passages at 60-2,083 rev/s is
    # 840 Hz to 29 kHz. The 4 kHz lower edge is the BPF at the shaft speed
    # below which the compressor is not yet making boost; the upper edge tracks
    # the shaft at 1.6 x BPF, below.
    # derivation: the blade-passing frequency band -- see above.
    blade = _sig.sosfilt(dsp.sos_band(COMPRESSOR_BB_LO_HZ, COMPRESSOR_BB_HI_HZ,
                                      sr, 4), dsp.white(n, seed + 4))
    blade = dsp.tv_onepole_lp(blade, np.clip(f_bpf * 1.6, COMPRESSOR_BB_LO_HZ * 1.5,
                                             min(COMPRESSOR_BB_HI_HZ, sr * 0.44)), sr)
    blade *= 0.09 * blade_am * 2.2      # the tracking lowpass costs ~7 dB of band
    turbo = (whine * 0.35 + blade) * boost * 0.055
    # compressor surge on a shut throttle while the shaft is still spinning
    flutter_rate = np.maximum(shaft_rps * 0.004, 8.0)
    flutter = np.abs(np.sin(dsp.integrate_phase(flutter_rate, sr)))
    # DERIVATION: compressor surge is a Helmholtz oscillation of the plenum
    # against the compressor duct, and what is audible is the broadband
    # rush of flow reversing through the diffuser vanes each cycle. Its band is
    # set by the vane passage width -- 8-15 mm at 343 m/s gives 700 Hz to 5 kHz
    # for the first passage mode -- and its RATE is the Helmholtz frequency,
    # carried by `flutter` above.
    # derivation: the diffuser vane passage's first mode -- see above.
    surge = _sig.sosfilt(dsp.sos_band(700.0, 5000.0, sr, 4), dsp.white(n, seed + 5))
    turbo += surge * flutter * over * boost * 0.10

    # --- MGU-H (on the turbo shaft) and MGU-K -----------------------------
    mguh = np.sin(dsp.integrate_phase(np.minimum(shaft_rps * 2.0, sr * 0.44), sr)) * 0.6
    mguh += np.sin(dsp.integrate_phase(np.minimum(shaft_rps * 4.0, sr * 0.44), sr)) * 0.25
    mguh *= boost * 0.016
    # `harvest` / `deploy` carry world-time lags and were integrated and mapped
    # with the rest of the trajectory.
    f_k = np.clip(rpm_eff / 60.0 * 26.0, 0.0, sr * 0.44)
    mguk = (np.sin(dsp.integrate_phase(f_k, sr)) * 0.7
            + np.sin(dsp.integrate_phase(np.minimum(f_k * 1.5, sr * 0.44), sr)) * 0.3)
    mguk *= (harvest * 0.055 + deploy * 0.018)

    # --- starter motor, before the catch ----------------------------------
    st = np.clip((tt - ignition_t) / 0.55, 0.0, 1.0) * np.clip(
        (ignition_t + 0.9 - tt) / 0.35, 0.0, 1.0)
    st = np.clip(st, 0.0, 1.0)
    f_st = 240.0 + 300.0 * np.clip((tt - ignition_t) / 0.9, 0.0, 1.0)
    starter = (np.sin(dsp.integrate_phase(f_st, sr)) * 0.5
               + np.sin(dsp.integrate_phase(f_st * 2.0, sr)) * 0.2)
    # DERIVATION: a starter's broadband is brush and pinion-mesh noise radiated
    # through the bell housing, whose first panel modes for a 0.3 m aluminium
    # casing lie between 400 Hz and 4 kHz. Above that the casing does not
    # radiate; below it the crank's own inertia swamps it.
    # derivation: the bell housing's own panel modes -- see above.
    starter += _sig.sosfilt(dsp.sos_band(400.0, 4000.0, sr, 4), dsp.white(n, seed + 6)) * 0.5
    starter *= st * 0.05

    # BALANCE, MEASURED AND CORRECTED. At exhaust 0.085 / rasp 0.55 the rasp ran
    # 6x the exhaust in RMS and OWNED the spectrum: the strongest line in a
    # 13,011 rpm pull was a random noise peak at 1,150 Hz, not the 681 Hz firing
    # fundamental, and the f0 tracker in verify.py -- correctly -- could not find
    # an engine in it. A V6 that measures as filtered noise is filtered noise.
    # The harmonic exhaust now leads by about 5:1 in RMS and the rasp is texture
    # under it, which is the relationship a real exhaust has.
    #
    # R2-1401 CUT THE RASP AGAIN, from 0.13 to 0.085. Not because the balance
    # against the exhaust changed, but because the exhaust now OCCUPIES the band
    # the rasp sits in: the old modal bank stopped at 1,936 Hz, so between 2 and
    # 2.6 kHz the rasp was the only thing there and was carrying the engine's
    # apparent brightness on its own. With the waveguide radiating harmonics
    # through that band on their own account, the same rasp level reads as haze
    # laid over the top -- which is the failure its own comment above describes.
    # THE COMPONENT RMS TABLE IS NOW REPORTED (see `info["component_rms"]`), so
    # this balance is auditable instead of asserted.
    parts = {
        # 0.55 -> 0.75: LEVEL COMPENSATION FOR R2-2001/2002, NOT A LOUDER ENGINE.
        # Shortening the ring and softening the strike removes energy: measured on
        # the dry exhaust the bus fell 1.5-4.4 dB on throttle (mean 2.69) and
        # 6.4 dB on overrun. Everything else in this bus -- rasp, turbo, mguh,
        # mguk, pump -- is fixed-level, and the bus is then trimmed as a whole to
        # -10 LUFS-S, so an uncompensated exhaust drop hands 2.7 dB of the engine
        # to its own noise layers. That is the wind-machine complaint, made worse
        # by the fix for the tube complaint. +2.69 dB (x1.364) puts the exhaust
        # back exactly where R2-1401 balanced it against them.
        #
        # This restores RMS, so the transients come back very slightly prouder
        # than before against a ring that is now 3x shorter. That is the intended
        # direction: a clean pulse at the firing rate is what an engine IS. What
        # was wrong was the twenty pulses still ringing behind it.
        #
        # B7 / R2-4066: `rasp` (0.085) and `pump` (0.16) are DELETED, and the
        # exhaust is NOT raised to compensate. Deleting a broadband layer and
        # then turning the harmonic one up to hold the bus level would restore
        # the very ratio the deletion exists to change; the bus is trimmed as a
        # whole to its LUFS-S target downstream, which is where a level is
        # supposed to be set. `harmonic_over_broadband_db` below is the number
        # that must move, and it is reported.
        "exhaust": exhaust * 0.75,
        "wastegate": wastegate * 0.75,
        "pops": pops * 0.26, "turbo": turbo,
        "mguh": mguh, "mguk": mguk,
        "crack": crack.astype(np.float64) * 0.30 * running_gain,
        "starter": starter,
    }
    sig = sum(parts.values())
    # the pipe's own radiation rolloff: a tailpipe is not a full-range driver
    sig = _sig.sosfilt(_sig.butter(1, 11000.0, btype="lowpass", fs=sr, output="sos"), sig)
    sig = _sig.sosfilt(_sig.butter(2, 28.0, btype="highpass", fs=sr, output="sos"), sig)

    # THE TONAL/BROADBAND SPLIT, AS A REPORTED NUMBER (R2-1401). The whole
    # defect was a ratio nobody was measuring, so it is measured here, over the
    # samples where the engine is actually pulling. `harmonic` is everything
    # whose spectrum is a line series locked to the crank or the shaft;
    # `broadband` is everything that is noise by construction. The client's
    # complaint is that the second number was too close to the first.
    _hot = (rpm_eff > RPM_IDLE * 1.5) & (thr > 0.5)
    _sel = _hot if _hot.sum() > sr else slice(None)

    def _rms(a):
        return float(np.sqrt(np.mean(np.asarray(a, dtype=np.float64)[_sel] ** 2)))
    _harm = _rms(parts["exhaust"] + parts["wastegate"] + parts["turbo"]
                 + parts["mguh"] + parts["mguk"])
    _bb = _rms(parts["pops"] + parts["crack"])

    idling = tt >= idle_until_t
    info = {
        "component_rms_on_throttle": {k: _rms(v) for k, v in parts.items()},
        "harmonic_over_broadband_db": float(
            20.0 * np.log10(max(_harm, 1e-12) / max(_bb, 1e-12))),
        "primary_lengths_m": list(PRIMARY_L_CYL),
        "primary_quarter_wave_per_cylinder_hz": [
            float(C_EXHAUST / (4.0 * L)) for L in PRIMARY_L_CYL],
        "exhaust_topmost_mode_hz": float(sr * 0.45),
        "exhaust_synthesis": ("digital waveguide: six per-cylinder quarter-wave "
                              "primaries into a shared half-wave collector and "
                              "tailpipe, mode series complete to Nyquist"),
        "rpm_min_running": float(rpm_eff[idling].min()) if idling.any() else 0.0,
        "rpm_max": float(rpm_eff.max()),
        "gear_min": int(gear.min()), "gear_max": int(gear.max()),
        "upshifts": int(up.shape[0]), "downshifts": int(dn.shape[0]),
        "final_drive": FINAL_DRIVE, "gear_ratios": GEAR_RATIOS.tolist(),
        # measured on the WORLD grid, before any mapping: `v` is the telemetry's
        # own track and `rpm_eff` may no longer be the same length as it
        "rpm_at_vmax": rpm_at_vmax,
        "vmax_ms": float(np.max(v)),
        "c_exhaust_ms": float(C_EXHAUST),
        "primary_quarter_wave_hz": [float(C_EXHAUST / (4.0 * L)) for L in PRIMARY_L],
        "collector_half_wave_hz": float(C_EXHAUST / (2.0 * COLLECTOR_L)),
        "turbo_shaft_rpm_max": float(shaft_rps.max() * 60.0),
        "overrun_fraction": float((over > 0.5).mean()),
        "throttle_mean": float(thr[running].mean()) if running.any() else 0.0,
        "clutch_lock_at_t0": float(lock[np.searchsorted(tt, 0.0)]),
        # ---- R2-4064 / R2-4066: the two things B7 and the grid law changed ---
        "rendered_on": "film grid" if to_film is not None else "world grid",
        "grid_law": ("the SCHEDULE (rpm, gear, throttle, injector, turbo shaft, "
                     "MGU lags, clutch) is integrated on the world grid with "
                     "world time constants and then mapped; the PITCH (crank "
                     "phase, pipe delays, shaft orders, filter corners) is "
                     "rendered in film-rate samples at its true value"),
        "half_order_weight": float(half_order_weight),
        "firing_angles_deg": [float(a) for a in fire_deg],
        "firing_intervals_deg": [float(x) for x in np.diff(
            np.concatenate([np.sort(fire_deg), [np.sort(fire_deg)[0] + 720.0]]))],
        "firing_fundamental_order": float(
            FIRING_ORDER_HALF if half_order_weight > 0.0 else FIRING_ORDER_EVEN),
        "firing_geometry": (
            "FIA 2025 Art. 5.2.10 permits three con-rod journals, which with the "
            "Art. 5.2.7 90-degree vee forces uneven 90/150 firing. The two "
            "sub-trains are 90 degrees = a quarter revolution apart, so the "
            "even-fired comb is multiplied by |1 + exp(-i*pi*m/2)| and the "
            "amplitude weighting is A(m) = |cos(pi*m/4)|: an EXACT null at "
            "order 6, full strength at order 12, and order 1.5 at "
            "20*log10(cos(0.375*pi)/cos(0.75*pi)) = -5.34 dB relative to "
            "order 3. Implemented as the firing-angle table itself rather than "
            "as an even bank plus a quarter-revolution delay line: the two are "
            "algebraically the same signal, and the table is the form this file "
            "already had. NOT CORROBORATED AGAINST A MEASURED F1 SPECTRUM -- "
            "every publisher returned 403 -- so it ships behind "
            "`half_order_weight` and `engine.py`'s own shared-collector "
            "argument may still be partly right: a collector ATTENUATES the "
            "half order, it does not cancel it."),
        "wastegate": {
            "area_mm2": WASTEGATE_AREA_MM2,
            "length_m": WASTEGATE_L,
            "radiation_corner_hz": WASTEGATE_RAD_HZ,
            "main_tailpipe_radiation_corner_hz": float(TAILPIPE_RAD_HZ),
            "open_fraction_of_running": float(
                (wg_open > 0.5)[running].mean()) if running.any() else 0.0,
            "why": ("FIA 2025 Art. 5.9.2 mandates a separate wastegate exhaust "
                    "of at most 1500 mm^2. Its gas has NOT been through the "
                    "turbine, and its mouth is 43.7 mm equivalent diameter "
                    "against the main tailpipe's 65 mm, so its radiation corner "
                    "is 2493 Hz against 840 Hz. That is the physical origin of "
                    "the brightness the deleted `rasp` was faking with a band "
                    "of white noise at 300-2600 Hz."),
        },
        "deleted_broadband_layers": {
            "rasp": "white -> bp(300, 2600) AM'd at the firing rate, gain 0.085",
            "pump": "white -> bp(120, 900) on overrun, gain 0.16",
            "why": ("both were stationary noise beds standing in for facts that "
                    "are modelled physically elsewhere -- cycle-to-cycle "
                    "irregularity by the crank jitter and CYL_CHARGE, the "
                    "overrun tone by the 0.38 pumping floor down the primaries "
                    "-- and `rasp`'s band IS the client's complaint band"),
        },
    }
    return sig.astype(np.float32), rpm_eff, gear, info
