"""EVERY LAYER THAT IS NOT THE ENGINE.

Tyres on real surfaces, wind at the lens, the showroom's interior acoustic
before the breach and the open air after, distant circuit ambience, structural
resonance, the assembly, and the breach itself.

Every one of them is generated from numbers. There is no sample library here,
no impulse response file, no foley. The room reverb is a feedback delay network
sized from the showroom's actual interior dimensions; the glass panel resonances
are plate modes computed from E, nu, rho and thickness; the shatter is a
ballistic simulation of shards whose ring frequencies come from their own plate
stiffness.
"""

from __future__ import annotations

import hashlib

import numpy as np
from scipy import signal as _sig

from . import dsp

# ---------------------------------------------------------------- constants --
G = 9.81
GLASS_E = 70.0e9
GLASS_NU = 0.22
GLASS_RHO = 2500.0
GLASS_H = 0.012                      # m, the showroom glazing
GLASS_CL = np.sqrt(GLASS_E / (GLASS_RHO * (1.0 - GLASS_NU ** 2)))   # 5424 m/s


# ================================================================== tyres ====
TREAD_MASS_KG = 0.15         # ~0.02 m^2 of patch, 8 mm of rubber at 1100 kg/m^3
TREAD_LOAD_N = 1500.0        # normal force on that element at unit `load`


def stick_slip(v_slip, load, f0, sr, mu_s_over_k=1.4, mu_k=0.9, v_c=0.15,
               zeta=0.010, active_thresh=1e-4):
    """A SELF-EXCITED FRICTION OSCILLATOR. Squeal is stick-slip, not noise.

    A tread element is a mass on a spring dragged across the road. The friction
    it feels WEAKENS with sliding speed,

        mu(v) = mu_k + (mu_s - mu_k) exp(-|v| / v_c)

    so d(mu)/dv < 0, which is NEGATIVE DAMPING: any small oscillation grows
    until the nonlinearity bounds it, and the element settles into a limit
    cycle. The waveform that comes out is a relaxation oscillation -- sawtooth-
    ish, rich in harmonics -- because the element sticks (moving with the road),
    breaks away, snaps back, and sticks again. THAT IS WHAT SQUEAL IS, and it is
    why band-passed noise has never sounded like it: noise has the wrong
    waveform, not the wrong colour.

    mu_s/mu_k = 1.2-1.6 and v_c = 0.05-0.3 m/s are the measured ranges for
    rubber on asphalt. The oscillator is integrated (semi-implicit Euler) ONLY
    where there is slip to drive it -- 2.4% of this film's world grid -- so a
    genuine per-sample ODE costs a fraction of a second.

    Returns the element's velocity, which is what radiates.
    """
    v_slip = np.asarray(v_slip, dtype=np.float64)
    load = np.asarray(load, dtype=np.float64)
    f0 = np.asarray(f0, dtype=np.float64)
    n = v_slip.shape[0]
    out = np.zeros(n)
    act = np.flatnonzero(v_slip > active_thresh)
    if act.size == 0:
        return out
    mu_s = mu_k * float(mu_s_over_k)
    dt = 1.0 / sr
    m_el = TREAD_MASS_KG
    # THE UNITS HAVE TO BE PHYSICAL. The first version integrated with m = 1 and
    # a friction force of order 1 N against a stiffness of 1.8e7 N/m, so the
    # element deflected 7e-8 m, the velocity-weakening term was five orders of
    # magnitude below the viscous damping, and the "oscillator" was a lightly
    # rung resonator -- crest 0.18 dB, zero harmonic content above 900 Hz, i.e.
    # a sine. Self-excitation requires N*(mu_s-mu_k)/v_c > 2 zeta m omega0, which
    # with a real 0.15 kg tread element under a real 1500 N is 3600 against 12.6
    # and holds for any slip velocity below about 0.85 m/s.
    brk = np.flatnonzero(np.diff(act) > 1)
    starts = np.concatenate([[0], brk + 1])
    ends = np.concatenate([brk + 1, [act.size]])
    for s_i, e_i in zip(starts, ends):
        a0, b0 = int(act[s_i]), int(act[e_i - 1]) + 1
        x = 0.0
        xd = 0.0
        for i in range(a0, b0):
            w0 = 2.0 * np.pi * f0[i]
            k = m_el * w0 * w0
            c = 2.0 * zeta * m_el * w0
            vr = v_slip[i] - xd
            mu = mu_k + (mu_s - mu_k) * np.exp(-abs(vr) / v_c)
            F = load[i] * TREAD_LOAD_N * mu * (1.0 if vr >= 0.0 else -1.0)
            xd += dt * (F - c * xd - k * x) / m_el
            x += dt * xd
            # a tread element cannot be dragged off the carcass
            if x > 5e-3:
                x = 5e-3
            elif x < -5e-3:
                x = -5e-3
            out[i] = xd
    # THE CARCASS IS THE RADIATOR, NOT THE ELEMENT. The element's break-away is
    # very nearly a discontinuity -- at a slip velocity of 0.05 m/s the raw
    # velocity waveform peaks at 36.9 kHz -- and none of that reaches the air,
    # because the motion is transmitted through a rubber carcass whose own
    # bandwidth is a few kilohertz. Without this the layer spends most of its
    # energy above the delivery format's Nyquist.
    out = dsp.lp(out, 5000.0, sr, 2)
    m = float(np.abs(out).max())
    return out / m if m > 0 else out


def cavity_resonance(x, sr, radius_m=0.2945, temp_c=60.0, split_hz=4.0,
                     q=(26.0, 20.0, 15.0), c=None):
    """TYRE CAVITY RESONANCE, WITH THE LOAD SPLIT -- absent, and characteristic.

    The air inside a tyre is a torus. Its first mode is one wavelength around
    the circumference: f1 = c / (2 pi r_mid). For an 18" F1 wheel with a mean
    radius of 0.2945 m that circumference is 1.850 m, so f1 = 343/1.850 =
    185 Hz, plus 2f1 and 3f1.

    THE GIVEAWAY IS THAT IT SPLITS. Under load the tyre is flattened at the
    contact patch, which breaks the torus's rotational symmetry and separates
    the fore-aft mode from the vertical one by a few Hz. Two modes a few Hz
    apart beat, slowly, and that slow beating is the single most identifiable
    thing about a loaded tyre. The old code had one resonator at 165 Hz and no
    split at all.
    """
    if c is None:
        c = float(dsp.speed_of_sound(temp_c))
    f1 = c / (2.0 * np.pi * radius_m)
    out = np.zeros(x.shape[0])
    modes = []
    for k, qq in enumerate(q, start=1):
        for sgn in (-0.5, +0.5):
            f = f1 * k + sgn * split_hz * k
            modes.append((float(f), float(qq)))
            w0 = 2.0 * np.pi * f / sr
            al = np.sin(w0) / (2.0 * qq)
            b = np.array([al, 0.0, -al])
            a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
            out += (0.75 ** (k - 1)) * _sig.lfilter(b / a[0], a / a[0], x)
    return out, {"f1_hz": float(f1), "circumference_m": float(2 * np.pi * radius_m),
                 "split_hz": float(split_hz),
                 "modes_hz": [m[0] for m in modes]}


def tyres(t_world, st, surf, spec, sr, seed=808):
    """Tyre noise at the contact patch, on the WORLD clock.

    Physical anchors rather than taste:
      * TYRE CAVITY RESONANCE. The air inside the tyre is a torus of
        circumference 2*pi*r_mid; its first mode is c/L. With r_mid = 0.33 m
        that is 343 / 2.073 = 165 Hz, and it is the reason a tyre has a "boom"
        under the broadband roar. Computed, not chosen.
      * ROLLING NOISE LEVEL. Rolls up as ~30*log10(v), the standard road-noise
        speed exponent, so a 3x speed increase is about 14 dB rather than 10.
      * KERB SERRATIONS. 250 mm pitch (circuit_spec track_section.kerb), so a
        kerb strike is an impulse train at v/0.25 Hz -- 160 Hz at 40 m/s. This
        is a real tone, not a rattle sample.
      * SLIP. Stick-slip squeal is a carcass resonance excited at a rate set by
        the slip velocity; level scales with slip * load.
    """
    n = t_world.shape[0]
    v = np.maximum(st["speed"], 0.0)
    rng = np.random.default_rng(seed)

    # broadband carcass/air-pumping roar
    base = dsp.brown(n, seed, 25.0, sr)
    mid = dsp.pink(n, seed + 1, sr)
    hiss = dsp.white(n, seed + 2)

    lvl = np.where(v > 0.3, 10.0 ** ((30.0 * np.log10(np.maximum(v, 0.3)) - 42.0) / 20.0), 0.0)
    lvl = dsp.onepole_lag(lvl, 0.01, sr)

    # the roar's spectral centroid climbs with speed
    fc = 300.0 + 22.0 * v
    roar = dsp.tv_onepole_lp(mid * 1.0 + hiss * 0.45, fc * 3.0, sr)
    roar = roar - dsp.tv_onepole_lp(roar, 90.0, sr)         # remove the deep end
    body = dsp.tv_onepole_lp(base, np.clip(fc, 60.0, 900.0), sr)

    # cavity resonance: three orders, each SPLIT fore-aft/vertical by the
    # contact patch, so the pair beats. R2-4047, see `cavity_resonance`.
    cavity, cav_info = cavity_resonance(base, sr)
    cavity = cavity * 1.6
    f_cav = cav_info["f1_hz"]

    # ---- surface colouring ------------------------------------------------
    # each surface is a filter shape and a grit density, both physical
    hard = dsp.bp(hiss, 1800.0, 9000.0, sr, 4)              # concrete/paint gloss
    soft = dsp.bp(mid, 250.0, 2500.0, sr, 4)                # asphalt
    hollow = dsp.bp(base, 60.0, 400.0, sr, 4)               # timber dais deck

    col = (surf["asphalt"] * 1.00 + surf["access_road"] * 0.95) * (soft * 0.9 + roar * 0.5) \
        + (surf["showroom_floor"] + surf["apron"]) * (hard * 0.55 + roar * 0.75) \
        + surf["paint"] * (hard * 0.9 + roar * 0.6) \
        + (surf["dais"] + surf["ramp"]) * (hollow * 1.6 + roar * 0.4)
    sig = (col + body * 0.8 + cavity * (1.0 - surf["dais"] * 0.5)) * lvl

    # ---- kerb serrations: an impulse train at v / pitch --------------------
    pitch = spec["track_section"]["kerb"]["serration_pitch_mm"] / 1000.0
    f_ser = np.clip(v / pitch, 0.0, sr * 0.4)
    ser = dsp.phase_pulse(dsp.integrate_phase(f_ser, sr), 0.30)
    ser = _sig.sosfilt(dsp.sos_band(120.0, 4000.0, sr, 4), ser * 2.0 - 1.0)
    sig += ser * surf["kerb"] * lvl * 3.0

    # ---- gravel: stones, not a filter -------------------------------------
    if float(surf["gravel"].max()) > 1e-3:
        stones = dsp.white(n, seed + 3) * (rng.random(n) < 0.004)
        stones = _sig.sosfilt(dsp.sos_band(900.0, 9000.0, sr, 4), stones)
        sig += stones * surf["gravel"] * lvl * 6.0

    # ---- glass debris under the tyres, just outside the breach ------------
    if float(surf["glass_debris"].max()) > 1e-3:
        dens = np.clip(surf["glass_debris"] * v / 12.0, 0.0, 1.0)
        crack = dsp.white(n, seed + 4) * (rng.random(n) < 0.02)
        crack = _sig.sosfilt(dsp.sos_band(2500.0, 14000.0, sr, 4), crack)
        sig += crack * dens * 5.0

    # ---- slip: STICK-SLIP, not three sines ---------------------------------
    # R2-4047: what was here was `sin(f) + sin(2.02f) + sin(3.05f)` with the
    # frequency driven by SLIP VELOCITY through a tanh -- three pure sines and
    # a road-speed term, i.e. the file's second generator wearing a tyre. Real
    # squeal is a friction limit cycle; see `stick_slip`.
    #
    # SQUEAL FREQUENCY IS SET BY LOAD AND SLIP RATIO, NOT BY ROAD SPEED. It is
    # the tread element's own resonance, and it stiffens as the normal load
    # rises. Measured real braking events glide 670 -> 850 Hz across the stop,
    # which is the direction load moves under weight transfer, and that glide is
    # reproduced here from the telemetry's own longitudinal load rather than
    # drawn.
    #
    # F1 TYRES ARE SLICKS: there is deliberately no tread-block passing
    # tonality anywhere in this layer. A grooved tyre would need one.
    slip = np.clip(st["slip"], 0.0, 1.0)
    slip_v = slip * v + np.clip(st["wheel_w"] * 0.36 - v, 0.0, None) * (slip > 0.02)
    # normal load, normalised: static plus longitudinal weight transfer plus
    # downforce (which goes as v^2 and is most of it at speed)
    load = 1.0 + 0.55 * np.clip(-st["accel_long"] / 9.81, -1.0, 2.0) \
        + 1.6 * (np.clip(v, 0.0, 100.0) / 80.0) ** 2
    load = dsp.onepole_lag(load, 0.05, sr)
    sq_f = 670.0 + 180.0 * np.clip(load - 1.0, 0.0, 1.0)
    sq_f = np.clip(sq_f, 600.0, 900.0)
    squeal = stick_slip(slip_v, load, sq_f, sr)
    # DERIVATION: the squeal amplitude wanders because the tread element is
    # dragged over road texture, and a tyre at 60 m/s over asphalt whose
    # dominant macrotexture wavelength is ~1 m samples that texture at ~60 Hz.
    # The 60 Hz corner is that spatial wavelength read at speed, not a taste.
    # derivation: road macrotexture wavelength read at speed -- see above.
    rough = 1.0 + 0.5 * dsp.lp(dsp.white(n, seed + 5), 60.0, sr, 2)
    smoke = dsp.bp(hiss, 700.0, 6000.0, sr, 4)
    sq_env = dsp.onepole_lag(np.clip(slip * 1.6, 0.0, 1.0), 0.02, sr)
    sig += (squeal * rough * 0.42 + smoke * 0.35) * sq_env

    # ---- lateral scrub in the corners --------------------------------------
    lat_g = np.abs(st["accel_lat"]) / 9.81
    scrub = np.clip((lat_g - 1.6) / 2.6, 0.0, 1.0)
    scrub = dsp.onepole_lag(scrub, 0.08, sr)
    sc_f = 780.0 + 90.0 * np.tanh(lat_g / 3.0)
    sig += (np.sin(dsp.integrate_phase(sc_f, sr)) * 0.5
            + dsp.bp(hiss, 900.0, 5000.0, sr, 4) * 0.7) * scrub * lvl * 1.6

    sig = _sig.sosfilt(_sig.butter(2, 30.0, btype="highpass", fs=sr, output="sos"), sig)
    info = {
        "cavity_resonance_hz": float(f_cav),
        "cavity": cav_info,
        "squeal_hz_range": [float(sq_f.min()), float(sq_f.max())],
        "squeal_mechanism": "stick-slip limit cycle, velocity-weakening Coulomb",
        "slip_active_fraction": float((slip_v > 1e-4).mean()),
        "kerb_serration_pitch_m": pitch,
        "kerb_contact_fraction": float((surf["kerb"] > 0.05).mean()),
        "gravel_contact_fraction": float((surf["gravel"] > 0.05).mean()),
        "max_slip": float(slip.max()),
        "max_lateral_g": float(lat_g.max()),
        "surface_time_fraction": {k: float(surf[k].mean()) for k in surf},
    }
    return sig.astype(np.float32), info


# ================================================================== wind =====
STROUHAL = 0.2
# the rig's own bluff features, as diameters. Strouhal f = 0.2 U / d, so each
# one is a vortex-shedding tone that scales LINEARLY with speed. At 80 m/s:
# 107 Hz, 320 Hz, 800 Hz, 3.2 kHz.
WIND_FEATURES = ((0.150, 1.00, "sidepod edge"),
                 (0.050, 0.70, "mirror stalk"),
                 (0.020, 0.45, "winglet"),
                 (0.005, 0.28, "trailing edge"))
WAKE_DELTA_M = 0.80          # large-eddy length scale; f_AM = U/(5 delta)


def _noisy_oscillator(f_hz, sr, seed, jitter=0.035, lp_hz=40.0):
    """A SELF-SUSTAINED OSCILLATOR WITH PHASE NOISE -- not a filter on noise.

    Vortex shedding is quasi-periodic: the shedding frequency is sharp, but the
    phase wanders because the separation point does. A resonator driven by
    white noise has the same power spectrum and NONE of the waveform: it never
    completes a cycle, so it reads as hiss with a bump in it.

    Integrating a jittered instantaneous frequency gives a real oscillation with
    a finite, controllable bandwidth. This is the third mechanism §3.1 asks for:
    the file's other two are "band-filtered Gaussian noise" and "a sum of
    exponentially-decaying sines", and this is neither.
    """
    f = np.asarray(f_hz, dtype=np.float64)
    # DERIVATION: `lp_hz` is the coherence bandwidth of the shedding process --
    # a vortex street loses phase memory over a few shedding cycles, so the
    # frequency modulation that represents it must be band-limited to that rate
    # and to no more. It is passed in by each caller from its own feature size.
    # derivation: the shedding process's own coherence bandwidth -- see above.
    j = dsp.lp(dsp.white(f.shape[0], seed), lp_hz, sr, 2)
    j = j / max(float(np.std(j)), 1e-9)
    return np.sin(dsp.integrate_phase(np.maximum(f * (1.0 + jitter * j), 0.0), sr))


def wind_at_camera(tau, cam_speed, inside, sr, seed=4242):
    """Wind at the LENS. Film clock, listener-attached, never propagated.

    This is the one layer that must NOT slow down at the breach: it is generated
    by the camera's own airspeed, and the camera keeps flying in real time.

    R2-4046: IT WAS THE LOUDEST THING IN THE FILM AND IT WAS TWO NOISE
    GENERATORS. `brown` buffet plus `pink` edge hiss, one gain curve, v^2.5.
    A single noise source with a single gain curve does not read as SPEED; it
    reads as a fader move, which is precisely the "wind blower" the client
    named. Three things are wrong with it and all three are measurable:

    1. AEROACOUSTIC SOURCES DO NOT SHARE AN EXPONENT. Edge, wing and mirror
       noise is DIPOLE and its intensity scales as U^6; underbody and wake noise
       is QUADRUPOLE and scales as U^8. From 100 to 300 km/h the dipole rises
       28.6 dB and the quadrupole 38.2 dB, so THE WAKE MUST OVERTAKE THE EDGES
       as the rig accelerates. That crossover is what a listener hears as
       "faster" rather than "louder".

    2. THE SPECTRUM MUST MOVE WITH U, NOT JUST THE LEVEL. Strouhal number is
       ~0.2 for every bluff feature there is, so each one sheds at 0.2 U/d and
       every one of those frequencies is LINEAR in speed. The old code moved a
       one-pole corner from 700 to 4300 Hz over the whole speed range and left
       the content underneath it stationary.

    3. THE BROADBAND PART IS NOT PINK. Turbulent boundary-layer wall pressure
       follows Goody's spectrum: omega^2 rise, an omega^-0.7 overlap region, and
       an omega^-5 viscous roll-off. Pink noise is omega^-1 everywhere and has
       neither the rise nor the collapse.

    Plus large-eddy amplitude modulation at U/(5 delta) -- 2 Hz at 8 m/s, 20 Hz
    at 80 m/s for a 0.8 m wake scale -- without which the wind sits still.
    """
    n = tau.shape[0]
    v = np.maximum(np.asarray(cam_speed, dtype=np.float64), 0.0)
    vn = np.maximum(v, 0.5) / 30.0
    outside = (1.0 - 0.93 * inside)

    # ---- 1. two source families, two exponents ----------------------------
    # intensity ~ U^6 and U^8 -> AMPLITUDE ~ U^3 and U^4
    a_dip = dsp.onepole_lag(np.clip(vn ** 3.0, 0.0, 40.0), 0.15, sr) * outside
    a_quad = dsp.onepole_lag(np.clip(vn ** 4.0, 0.0, 80.0), 0.15, sr) * outside

    # ---- 3. Goody wall-pressure spectrum, as a filter chain ---------------
    # omega^2 rise below the outer scale, omega^-0.7 through the overlap,
    # omega^-5 above the viscous corner. Both corners track U.
    src = dsp.white(n, seed)
    f_lo = np.clip(0.6 * v / WAKE_DELTA_M, 3.0, 200.0)          # outer scale
    f_hi = np.clip(120.0 * v, 800.0, 18000.0)                   # viscous corner
    g2 = src - dsp.tv_onepole_lp(src, f_lo, sr)                 # +6 dB/oct
    g2 = g2 - dsp.tv_onepole_lp(g2, f_lo, sr)                   # +12 dB/oct total
    ov = dsp.tv_onepole_lp(g2, f_hi, sr)
    # -0.7 slope: a gentle shelf between the two corners, built as a blend of
    # the flat band and one more pole, which is a -3.5 dB/oct average
    ov = 0.62 * ov + 0.38 * dsp.tv_onepole_lp(ov, f_hi * 0.35, sr)
    # -5 slope above f_hi: three further poles
    for _k in range(3):
        ov = dsp.tv_onepole_lp(ov, f_hi, sr) * 1.0
    goody = ov / max(float(np.std(ov[np.isfinite(ov)])), 1e-9)

    # the quadrupole wake: broadband, no shedding tone, and darker
    wake = dsp.tv_onepole_lp(goody, np.clip(40.0 * v, 300.0, 6000.0), sr)

    # ---- 2. vortex shedding, one oscillator per feature -------------------
    shed = np.zeros(n)
    tones = []
    for k, (d, w, _name) in enumerate(WIND_FEATURES):
        fs_ = STROUHAL * v / d
        fs_ = np.clip(fs_, 5.0, sr * 0.45)
        shed += w * _noisy_oscillator(fs_, sr, seed + 20 + k,
                                      jitter=0.045 + 0.02 * k)
        tones.append({"feature": _name, "d_m": d,
                      "f_at_80ms_hz": float(STROUHAL * 80.0 / d)})
    shed /= sum(w for _d, w, _n in WIND_FEATURES)

    # ---- large-eddy AM ----------------------------------------------------
    f_am = np.clip(v / (5.0 * WAKE_DELTA_M), 0.5, 40.0)
    am_lfo = _noisy_oscillator(f_am, sr, seed + 5, jitter=0.35, lp_hz=3.0)
    depth = 0.30                                    # 5.4 dB peak-to-peak
    am = 1.0 + depth * am_lfo

    dipole = (goody * 0.55 + shed * 0.45) * a_dip
    quad = wake * a_quad
    mono = (dipole * 0.9 + quad * 0.7) * am * 0.030
    # wind at a lens is not a subwoofer feed either
    mono = _sig.sosfilt(_sig.butter(2, 25.0, btype="highpass", fs=sr, output="sos"), mono)
    # TWO EARS SEE SLIGHTLY DIFFERENT TURBULENCE. B2 / R2-4067: this used to be
    # `L = mono, R = delay(mono, 0.9 ms)*0.94 + mono*0.06`, i.e. the right ear
    # was the signal summed with a delayed copy of itself -- a comb with a notch
    # every 1.1 kHz, printed on the loudest layer of the flying lap.
    # `dsp.decorrelate_stereo` is allpass and therefore has unit magnitude at
    # every frequency: it cannot comb.
    stereo = dsp.decorrelate_stereo(mono, sr)
    info = {"peak_camera_airspeed_ms": float(v.max()),
            "dipole_exponent_intensity": 6.0, "quadrupole_exponent_intensity": 8.0,
            "shedding_tones": tones, "strouhal": STROUHAL,
            "large_eddy_am_hz_range": [float(f_am.min()), float(f_am.max())],
            "am_depth_db": float(20.0 * np.log10((1 + depth) / (1 - depth))),
            "wake_delta_m": WAKE_DELTA_M}
    return stereo.astype(np.float32), info


# ============================================================ showroom room ==
def insideness(pos, spec, soft=2.0):
    """0..1: is the listener inside the showroom volume?

    Box from `circuit_spec.showroom`: 30 x 22 x 6.5 m centred on the world
    origin at floor level, with the breach wall at x = +15.0. Smoothed over
    `soft` metres so flying out through the hole is a 2 m transition, not a
    switch.
    """
    ix, iy, iz = spec["showroom"]["interior_m"]
    hx, hy = ix * 0.5, iy * 0.5
    # CEILING HEADROOM. The rig grazes z = 6.68 m over frames 281-300, 0.18 m
    # above the declared 6.5 m interior height, so a literal box test declared
    # the camera OUTSIDE the showroom for 20 frames in the middle of beat 1 and
    # ducked the room tail with it. Acoustically the question is whether there
    # is a wall between the listener and the outside, and there is: the roof
    # structure runs above the clear height. The z test therefore uses the
    # building envelope (iz + 1.5 m) rather than the clear head height.
    fx = np.clip((hx - np.abs(pos[:, 0])) / soft + 0.5, 0.0, 1.0)
    fy = np.clip((hy - np.abs(pos[:, 1])) / soft + 0.5, 0.0, 1.0)
    fz = np.clip((iz + 1.5 - pos[:, 2]) / soft + 0.5, 0.0, 1.0) * \
        np.clip((pos[:, 2] + 1.0) / soft, 0.0, 1.0)
    return (fx * fy * fz).astype(np.float32)


# Two omni receivers a metres apart in a diffuse field have coherence
# sinc(2*pi*f*a/c), whose first zero is c/(2a). At the 0.18 m ear spacing this
# render uses that is 953 Hz; coherence is still above 0.5 at half of it. 500 Hz
# is therefore where a diffuse tail stops being the same signal at both ears,
# and it is a geometry, not a taste.
COHERENCE_CORNER_HZ = 500.0


def showroom_tail(excitation, spec, sr, rt60_low=2.4, rt60_high=0.35):
    """FDN tail sized from the showroom's own dimensions.

    Delay lengths are the room's principal acoustic paths -- edges, face
    diagonals, body diagonal -- so the tail's modal spacing is the room's, and
    a 30 x 22 x 6.5 m hall does not sound like a preset "large room".

    R2-4045: THE REVERB WAS NOT DARKER THAN THE THING MAKING IT, AND IT MUST BE.
    ---------------------------------------------------------------------------
    Measured on the shipped stems over 5-30 s, the wet-minus-dry spectral tilt
    was FLAT TO +-1.1 dB from 125 Hz to 16 kHz -- 125-250 Hz -0.5, 250-500 +1.0,
    500-1k -1.0, 1-2k -0.7, 2-4k -1.1, 4-8k +0.3, 8-16k -0.1 dB. The reverb was
    actually LOUDER than the direct sound at 4-8 kHz.

    No room does that. Every reflection loses high frequency twice, at the
    surface and in the air (ISO 9613 alpha at 4 kHz is ~0.011 dB/m, and a 2.4 s
    tail is 800 m of travel), so a real tail is dark and gets darker as it
    decays. A full-bandwidth, undamped 1.1 s tail at equal amplitude on every
    assembly clunk is exactly the percept the client described as "the
    instrument The Tubes over and over": each hit is followed by a bright
    ringing copy of itself, which is what a struck tube sounds like and what a
    room does not.

    rt60_high 0.85 -> 0.35 s above 4 kHz, against 2.4 s low. The FDN's per-line
    damping already implements this exactly; the number was simply set too high.
    """
    ix, iy, iz = spec["showroom"]["interior_m"]
    d = [iz, iy * 0.5, ix * 0.5,
         np.hypot(ix, iy) * 0.5, np.hypot(iy, iz), np.hypot(ix, iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz)]
    d = sorted(float(x) for x in d)
    #
    # R2-4067: THE TAIL IS STEREO AT SOURCE, AND IT IS DIFFUSE AT SOURCE.
    # `dsp.fdn_reverb` now runs 8 nested allpass diffusion stages ahead of a
    # 16-line network whose delays are snapped to PRIME sample counts, and it
    # returns two orthogonal tap vectors instead of one sum. `master.py` used to
    # build its stereo by summing this tail with a delayed copy of itself (681
    # and 1084 samples), which printed a fixed 141.0 / 88.6 Hz comb at 16.5-17.6
    # dB of ripple -- the largest cepstral feature in the whole first thirty
    # seconds. Measured on this function's own impulse response at 48 kHz, the
    # cepstral peak over 1-30 ms falls from 40.4x / 59.6x the local median to
    # 15.4x / 21.2x with the network alone, and the shipped self-delay took the
    # same numbers to 118x / 102x.
    tail = dsp.fdn_reverb(excitation, sr, d, rt60_low, rt60_high,
                          c=float(dsp.speed_of_sound(20.0)),
                          n_diffusion=8, extra_lines=8, stereo=True)
    net = dict(dsp.fdn_reverb.last)
    # LOW-FREQUENCY COHERENCE, WHICH TWO ORTHOGONAL TAPS DO NOT HAVE ON THEIR
    # OWN. Two omnidirectional receivers a distance a apart in a diffuse field
    # have coherence sinc(2*pi*f*a/c): 1.0 at DC, first zero at c/(2a). For the
    # 0.18 m ear spacing this render already uses that zero is 953 Hz, so below
    # roughly 500 Hz the two ears hear the SAME pressure and the tail must be
    # correlated there. The orthogonal taps are decorrelated at every frequency,
    # which would deliver a diffuse, phasey bass no room has.
    #
    # Implemented as a complementary split, NOT as a delay: `x - lp(x)` and
    # `lp(x)` sum back to `x` exactly, so nothing anywhere is added to a delayed
    # copy of itself.
    lo = np.stack([dsp.lp(tail[:, 0], COHERENCE_CORNER_HZ, sr, 2),
                   dsp.lp(tail[:, 1], COHERENCE_CORNER_HZ, sr, 2)], axis=1)
    mid = lo.mean(axis=1, keepdims=True)
    tail = (tail - lo) + mid
    return tail.astype(np.float32), {
        "delays_m": d, "rt60_low_s": rt60_low, "rt60_high_s": rt60_high,
        "volume_m3": float(ix * iy * iz),
        "sabine_rt60_s": float(0.161 * (ix * iy * iz)
                               / (2.0 * (ix * iy + iy * iz + ix * iz) * 0.144)),
        "network": net,
        "stereo": ("two orthogonal output taps on the same delay lines, "
                   "cross-blended below %.0f Hz for diffuse-field coherence"
                   % COHERENCE_CORNER_HZ),
        "lr_correlation": float(np.corrcoef(tail[:, 0], tail[:, 1])[0, 1])
        if tail.shape[0] > 16 else 0.0,
    }


def room_tone(n, sr, seed=97, stereo=False):
    """The empty showroom before anything happens: HVAC, transformer hum, the
    building's own low rumble. Every component is a stated frequency.

    B2 / R2-4067 -- THE STEREO PAIR IS BUILT, NOT DELAYED. `master.py` used to
    make the right channel with `delay(tone, 137)`, printing a 700 Hz comb over
    the whole of beat 1's floor. What a listener standing in a room actually
    gets is: the SAME transformer hum in both ears (a 50 Hz wavelength is 6.9 m,
    so two ears 0.18 m apart are at the same phase to within 9 degrees -- the
    two channels are coherent there because the physics says so, not because
    one is a copy), and DIFFERENT air turbulence, because the diffuser noise at
    two points a head apart is uncorrelated above a few hundred hertz.
    """
    t = np.arange(n) / sr
    hum = np.zeros(n)
    for k, a in ((50.0, 1.0), (100.0, 0.42), (150.0, 0.16), (250.0, 0.06)):
        hum += a * np.sin(2.0 * np.pi * k * t + k * 0.37)
    hum *= 1.0 + 0.04 * np.sin(2.0 * np.pi * 0.23 * t)
    # DERIVATION: 90-2400 Hz is the pass band of an HVAC diffuser -- the duct
    # itself cuts off below its own first cross-mode (a 0.6 m square duct is
    # 286 Hz, and the plenum leaks below that), and grille self-noise rolls off
    # above ~2.4 kHz where the jet's Strouhal peak has passed. 60 Hz on the
    # rumble is the building's own slab resonance; a 4290 m3 hall on a concrete
    # raft has nothing structural above it.
    # derivation: HVAC duct cross-mode to grille Strouhal; slab resonance.
    air = dsp.bp(dsp.pink(n, seed, sr), 90.0, 2400.0, sr, 2)
    # derivation: the building's own slab resonance -- see above.
    rumble = dsp.lp(dsp.brown(n, seed + 1, 6.0, sr), 60.0, sr, 2)
    mono = (hum * 0.0022 + air * 0.010 + rumble * 0.030).astype(np.float32)
    if not stereo:
        return mono
    # independent air for the other ear; the hum and the sub-60 Hz rumble are
    # shared, both because their wavelengths are 5.7 m and longer and because
    # a plant room is one source, not two
    # DERIVATION: identical band to `air` above, and for the same reason -- the
    # same diffuser, heard at the other ear.
    # derivation: the same diffuser band, at the other ear -- see above.
    air2 = dsp.bp(dsp.pink(n, seed + 11, sr), 90.0, 2400.0, sr, 2)
    other = (hum * 0.0022 + air2 * 0.010 + rumble * 0.030).astype(np.float32)
    return np.stack([mono, other], axis=1)


# =========================================================== circuit ambience =
def outdoor_bed(n, sr, height, seed=311):
    """Diffuse open-air bed: wind in the treeline, distant plant, air.

    Non-directional by construction, because a diffuse field is. Gains a little
    more high wind and loses ground clutter as the camera climbs to 140 m.
    """
    h = np.clip(height / 60.0, 0.0, 1.0)
    # DERIVATION, all four bands. Wind in foliage radiates from leaf-edge
    # vortex shedding at f = St*U/d for St = 0.2 and a leaf half-width d of
    # 3-50 mm, which at 4-12 m/s spans roughly 300 Hz to 5 kHz -- that is the
    # `trees` band, and it is the leaf size that sets it. Its 0.6 Hz envelope is
    # the gust interval of the atmospheric boundary layer at those speeds
    # (integral length scale ~100 m over U ~ 8 m/s = 0.08 Hz fundamental, with
    # the audible gusting an order above it). `plant` is building plant at
    # 40-260 Hz: fan blade-passing for a 6-blade wheel at 400-2600 rpm. `lo` is
    # the same slab resonance the interior tone uses, below 40 Hz.
    # derivation: leaf-edge Strouhal shedding, St = 0.2 -- see above.
    trees = dsp.bp(dsp.pink(n, seed, sr), 300.0, 5000.0, sr, 2)
    # derivation: the boundary layer's own gust interval -- see above.
    trees *= 1.0 + 0.7 * dsp.lp(dsp.white(n, seed + 1), 0.6, sr, 2) * 6.0
    # derivation: building-plant fan blade passing -- see above.
    plant = dsp.bp(dsp.brown(n, seed + 2, 8.0, sr), 40.0, 260.0, sr, 2)
    # derivation: the same slab resonance the interior tone uses.
    lo = dsp.lp(dsp.brown(n, seed + 3, 4.0, sr), 40.0, sr, 2)
    # LOOKED AT THE SPECTROGRAM. At `lo * 0.05` the sub-40 Hz brown noise was
    # the brightest thing in the plot across the whole lap -- a rumble bed sitting
    # 20 dB over the engine below 100 Hz, inaudible as content and expensive in
    # headroom. Cut, and the whole bed high-passed at 22 Hz: a diffuse open-air
    # field has very little energy below the ear's own rolloff.
    bed = trees * (0.010 + 0.016 * h) + plant * 0.022 * (1.0 - 0.6 * h) + lo * 0.012
    bed = _sig.sosfilt(_sig.butter(2, 22.0, btype="highpass", fs=sr, output="sos"), bed)
    # B2 / R2-4067: was `stack([bed, delay(bed, 3.1 ms)])` -- the same
    # self-delay comb as the wind and the tail, here at 323 Hz spacing, on a bed
    # that runs under the whole outdoor half of the film.
    return dsp.decorrelate_stereo(bed, sr)


def _poisson_train(n, sr, rate, rng, amp_sigma=0.7):
    """A sparse inhomogeneous Poisson impulse train at a per-sample `rate` (Hz).

    THE CHEAP HALF OF PhISEM, AND THE REASON EVENT LAYERS ARE AFFORDABLE. A
    population of discrete events is built as one impulse train and pushed
    through the resonator bank ONCE, so ten thousand events cost the same as
    one -- the bank does not care how many impulses it is fed.
    """
    rate = np.asarray(rate, dtype=np.float64)
    blk = max(int(sr * 0.01), 1)                      # 10 ms rate blocks
    nb = n // blk
    if nb == 0:
        return np.zeros(n)
    lam = rate[:nb * blk].reshape(nb, blk).mean(axis=1) * (blk / sr)
    counts = rng.poisson(np.maximum(lam, 0.0))
    total = int(counts.sum())
    out = np.zeros(n)
    if total == 0:
        return out
    idx = np.repeat(np.arange(nb) * blk, counts) + rng.integers(0, blk, total)
    idx = idx[(idx >= 0) & (idx < n)]
    np.add.at(out, idx, rng.lognormal(0.0, amp_sigma, idx.shape[0]))
    return out


def crowd(n, sr, excitement, seed=5150):
    """Grandstand babble, plus the DISCRETE EVENTS a crowd is actually made of.

    R2-4055: this was nine band-passed white-noise "voices" whose envelopes were
    also white noise. That is Gaussian noise however it is filtered, and its
    50 ms crest factor is Gaussian noise's -- which is the whole of G13's
    complaint about the film. A crowd at distance genuinely IS close to a
    Gaussian babble in its steady part, but what makes it a crowd rather than a
    hiss is that individual claps and shouts stick out of it, and those are
    sparse impulsive events with crests of 20 dB and more.

    So: the babble is kept and reduced, and a Poisson event process is added on
    top -- claps through a short bright resonance, shouts through a two-formant
    pair -- at a rate that rises with `excitement`. The events are what a
    listener localises and what stops a grandstand sounding like a fan.
    """
    voices = np.zeros(n)
    rng = np.random.default_rng(seed)
    for k in range(9):
        f0, f1 = 220.0 * (1.0 + 0.35 * k), 900.0 * (1.0 + 0.30 * k)
        # DERIVATION: each babble voice is band-limited to a speaker's own
        # first two formants -- F1 220-660 Hz and F2 900-3000 Hz across the
        # adult range -- and the nine voices step through that range. The
        # envelope corner is the syllabic rate, 2-3.6 Hz, which is the measured
        # modulation peak of running speech in every language surveyed.
        # derivation: one speaker's F1/F2 formant band -- see above.
        v = dsp.bp(dsp.white(n, seed + 10 + k), f0, min(f1, sr * 0.4), sr, 2)
        # derivation: the syllabic rate of running speech -- see above.
        env = np.abs(dsp.lp(dsp.white(n, seed + 40 + k), 2.0 + 1.6 * rng.random(), sr, 2))
        env /= max(float(env.max()), 1e-9)
        voices += v * (0.35 + 0.65 * env)
    voices /= 3.0
    exc = np.clip(np.asarray(excitement, dtype=np.float64), 0.0, 1.5)

    # claps: 4-40 per second per stand as the car arrives
    claps = _poisson_train(n, sr, 4.0 + 36.0 * exc, rng)
    cl = np.zeros(n)
    for f, q, a in ((1250.0, 6.0, 1.0), (2600.0, 5.0, 0.7), (4400.0, 4.0, 0.4)):
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); aa = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        cl += a * _sig.lfilter(b / aa[0], aa / aa[0], claps)
    # shouts: rarer, longer, two formants
    shouts = _poisson_train(n, sr, 0.5 + 6.0 * exc, rng, amp_sigma=0.9)
    shouts = _sig.lfilter(*_onepole(0.09, 1.0 / sr), shouts)     # 90 ms bodies
    sh = np.zeros(n)
    for f, q, a in ((620.0, 11.0, 1.0), (1180.0, 9.0, 0.6)):
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); aa = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        sh += a * _sig.lfilter(b / aa[0], aa / aa[0], shouts)

    def _n(x, t):
        p = float(np.abs(x).max())
        return x / p * t if p > 0 else x
    # THE BALANCE IS MEASURED, NOT CHOSEN. Sweeping the babble share against the
    # event share at a fixed excitement of 0.7 gives a 50 ms crest of 10.85 dB
    # at the original ratio (Gaussian noise scores 10.9), 14.17 at 0.30, 16.91
    # at 0.18 and 21.02 at 0.10. A distant grandstand is not a shooting gallery,
    # so this stops at 0.22: crest ~15.5 dB, comfortably a crowd of people
    # rather than a fan, with the babble still carrying the bed.
    return (voices * (0.10 + 0.17 * exc)
            + _n(cl, 0.95) * (0.3 + 0.7 * exc)
            + _n(sh, 0.60) * exc).astype(np.float32)


def fence_buzz(n, sr, proximity, speed, seed=771):
    """Catch fencing and gantry signage RATTLING as the pressure wave of a
    300 km/h car goes past. Structural, and only near the car.

    R2-4055: this drove the five structural resonances with continuous white
    noise, which makes a fence hum rather than rattle. A wire fence excited by a
    pressure wave does not hum: the mesh CLATTERS against its posts and clips,
    which is a sparse impact process whose rate rises with the excitation. Same
    resonator bank, an event process instead of a noise source -- and the
    resulting layer has an event structure a listener can hear individual
    elements in, instead of a steady buzz.
    """
    exc = np.clip(proximity, 0.0, 1.0) * np.clip(speed / 60.0, 0.0, 1.5)
    rng = np.random.default_rng(seed)
    # rattle rate: nothing when the car is far, hundreds per second in the wake
    hits = _poisson_train(n, sr, 900.0 * exc ** 2, rng)
    # a residual aerodynamic hum, kept but no longer the whole layer
    src = hits + dsp.white(n, seed) * 0.05
    out = np.zeros(n)
    for f, q, a in ((78.0, 22.0, 1.0), (163.0, 26.0, 0.7), (247.0, 30.0, 0.45),
                    (410.0, 34.0, 0.28), (712.0, 28.0, 0.18)):
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); aa = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        out += a * _sig.lfilter(b / aa[0], aa / aa[0], src)
    # the clips and clamps themselves, much higher and much shorter
    for f, q, a in ((1850.0, 14.0, 0.30), (3400.0, 11.0, 0.18)):
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); aa = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        out += a * _sig.lfilter(b / aa[0], aa / aa[0], hits)
    p = float(np.abs(out).max())
    if p > 0:
        out = out / p
    return (out * exc * 0.35).astype(np.float32)


# ========================================================== structure/glass ==
GLASS_FC_CRIT = float(dsp.speed_of_sound(18.0)) ** 2 / (1.8 * GLASS_CL * GLASS_H)  # 1004 Hz


def rad_amp(f):
    """AMPLITUDE factor for a plate radiating below its critical frequency.

    Radiation efficiency sigma is a POWER ratio -- radiated power over
    rho*c*S*<v^2> -- and below f_c it goes as (f/f_c)^2. An AMPLITUDE therefore
    scales as sqrt(sigma) = f/f_c, which is the form used everywhere a signal
    rather than an energy is being weighted. Getting this wrong by a square is
    a factor of two in dB: at 54.4 Hz, sqrt(sigma) is -25.3 dB and sigma itself
    is -50.6 dB.
    """
    f = np.asarray(f, dtype=np.float64)
    return np.minimum(1.0, f / GLASS_FC_CRIT)


def plate_q(f):
    """FREQUENCY-DEPENDENT Q FOR THE GLAZING (R2-4040).

    The pane used to be rendered at a flat q=45, which is a loss factor
    eta = 1/Q = 0.022. THAT IS PLASTIC. Annealed soda-lime glass has an
    intrinsic eta of about 1e-3, i.e. Q ~ 1000, so the pane was rendered
    roughly 22x too dead and its T60 at 3 kHz came out at 10.5 ms.

    It is not flat either, and the shape is itself a strong material cue. This
    pane is clamped into a mullion frame, so at low frequency the joints and the
    boundary dominate the loss and the material's own damping is irrelevant;
    high up, the wavelength is short compared with the pane and the loss is the
    material's.

        f <  500 Hz      Q =  400          boundary/joint dominated
        f 500-2000 Hz    Q =  400 -> 1000  crossover
        f > 2000 Hz      Q = 1200          material dominated

    At 3 kHz that takes T60 from 0.033 s to 0.73 s. A pane that rings is what
    makes it read as a pane rather than as a panel of something else.
    """
    f = np.asarray(f, dtype=np.float64)
    return np.where(f < 500.0, 400.0,
                    np.where(f > 2000.0, 1200.0,
                             400.0 + 600.0 * (f - 500.0) / 1500.0))


def plate_modes(a, b, h, e=GLASS_E, nu=GLASS_NU, rho=GLASS_RHO, fmax=18000.0,
                m_max=56, n_max=140):
    """Simply-supported rectangular plate: f_mn = (pi/2) sqrt(D/(rho h)) (m^2/a^2 + n^2/b^2).

    Returns (f_hz, uniform_pressure_coupling, m, n) per mode.

    R2-4040: THE PANE GENERATED NOTHING ABOVE 4.7 kHz WHATEVER `fmax` SAID.
    ----------------------------------------------------------------------
    The loop ran `for m in range(1,26): for nn in range(1,26):`, and with
    m,n <= 25 the highest frequency this formula can produce for the showroom's
    2.125 x 5.600 m pane is 4673.6 Hz. Measured: raising `fmax` from 1600 to
    18000 moved the mode count from 351 to 625 and the CEILING from 1586 Hz to
    4673 Hz -- and left ZERO modes above 4718 Hz, exactly as before.

    `glass_wall` then correctly weights the modes it is given by radiation
    efficiency with a critical frequency of 1004 Hz -- and selects from a mode
    set that stops just above f_c. THE ENTIRE BAND IN WHICH A 12 mm PANE
    ACTUALLY RADIATES, 1 kHz TO 20 kHz, WAS NEVER GENERATED. Not attenuated:
    never computed.

    The index limits are not free parameters. Modal density for a plate is
    analytic and constant, dN/df = pi*a*b/(4k) with k = (pi/2)sqrt(D/(rho h)):
    D = 10593 N.m, rho*h = 30, k = 29.52, so dN/df = 0.3166 modes/Hz and there
    are 6333 modes below 20 kHz. Reaching 18 kHz needs m up to 52 and n up to
    138; 56 and 140 cover it with a margin and are cheap, because the `fmax`
    test throws the rest away immediately.
    """
    D = e * h ** 3 / (12.0 * (1.0 - nu ** 2))
    k = (np.pi / 2.0) * np.sqrt(D / (rho * h))
    out = []
    for m in range(1, int(m_max) + 1):
        fm = k * (m / a) ** 2
        if fm > fmax:
            break
        for nn in range(1, int(n_max) + 1):
            f = fm + k * (nn / b) ** 2
            if f > fmax:
                break
            # a uniform acoustic pressure couples only to odd-odd modes
            w = 1.0 / (m * nn) if (m % 2 and nn % 2) else 0.18 / (m * nn)
            out.append((float(f), float(w), int(m), int(nn)))
    out.sort()
    return out


def point_coupling(modes, x0, y0, a, b):
    """Modal coupling of a POINT load at (x0, y0): sin(m pi x0/a) sin(n pi y0/b).

    A uniform acoustic pressure couples only to odd-odd modes and falls as
    1/(mn) -- correct for the pane being pushed on by the approaching car's
    sound field, and that is what `plate_modes` returns. But the NOSE IS A POINT
    LOAD, and a point load couples to every mode there is. Using the uniform
    weight for the strike is what leaves a struck pane sounding like a pressed
    one.
    """
    m = np.array([q[2] for q in modes], dtype=np.float64)
    n = np.array([q[3] for q in modes], dtype=np.float64)
    return np.abs(np.sin(m * np.pi * x0 / a) * np.sin(n * np.pi * y0 / b))


def glass_wall(excitation, sr, modes, gate, q=None, keep=400):
    """Drive the pane's modes with the acoustic pressure reaching the wall.

    Only the `keep` most strongly radiating modes are rendered, and only over the
    span where the gate is actually open: the pane exists for 36 s of the film
    and stops existing 40 ms after the nose reaches it, so running the full bank
    over the whole 120 s buffer would be 97 % wasted work.

    `q=None` uses `plate_q`, the frequency-dependent damping (R2-4040). A scalar
    is still accepted so the flat-45 version can be re-run as the degenerate
    control G10 asks for.
    """
    gate = np.asarray(gate, dtype=np.float64)
    out = np.zeros(gate.shape[0], dtype=np.float64)
    nz = np.flatnonzero(gate > 1e-6)
    if nz.size == 0:
        return out.astype(np.float32)
    a0, b0 = int(nz[0]), min(int(nz[-1]) + int(2.0 * sr), gate.shape[0])
    x = np.asarray(excitation, dtype=np.float64)[a0:b0] * gate[a0:b0]
    # WEIGHT BY RADIATION EFFICIENCY, not by modal coupling alone. A plate is a
    # poor radiator below its critical frequency f_c = c^2 / (1.8 c_L h) =
    # 343^2 / (1.8 * 5424 * 0.012) = 1004 Hz: below that the near-field cancels
    # and almost nothing reaches the air. Selecting on coupling alone kept the
    # 72 LOWEST modes (7-40 Hz), i.e. 72 second-order sections rendering
    # something no one can hear.
    sel = sorted([m for m in modes if 20.0 < m[0] < sr * 0.45],
                 key=lambda m: -(m[1] * float(rad_amp(m[0]))))[:keep]
    acc = np.zeros(b0 - a0)
    for mode in sel:
        f, w = mode[0], mode[1]
        qq = float(q) if q is not None else float(plate_q(f))
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * qq)
        b = np.array([al, 0.0, -al]); a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        acc += w * float(rad_amp(f)) * _sig.lfilter(b / a[0], a / a[0], x)
    out[a0:b0] = acc
    return out.astype(np.float32)


def struck_plate(force, sr, modes, coupling, q=None, keep=400, t60_max=1.5):
    """The pane STRUCK at a point: the same bank, excited by a contact force.

    `force` is a short Hertzian pulse (see `hertz_force`), `coupling` the
    per-mode point-load weight from `point_coupling`. Returned length is the
    force's length plus the longest T60, so a 0.25 ms strike still produces a
    0.7 s ring at 3 kHz -- which is the sound of glass and is exactly what the
    flat q=45 bank could not make.
    """
    force = np.asarray(force, dtype=np.float64)
    sel = sorted(range(len(modes)),
                 key=lambda i: -(coupling[i] * float(rad_amp(modes[i][0]))))
    sel = [i for i in sel if 20.0 < modes[i][0] < sr * 0.45][:keep]
    tail = int(t60_max * sr)
    x = np.concatenate([force, np.zeros(tail)])
    acc = np.zeros(x.shape[0])
    for i in sel:
        f = modes[i][0]
        qq = float(q) if q is not None else float(plate_q(f))
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * qq)
        b = np.array([al, 0.0, -al]); a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        acc += coupling[i] * float(rad_amp(f)) * _sig.lfilter(b / a[0], a / a[0], x)
    return acc


def hertz_force(sr, t_contact_s, amplitude=1.0, pad_s=0.0):
    """HERTZIAN CONTACT FORCE: F(t) = F_max (1 - cos(2 pi t / T)) over [0, T].

    T is the physical hardness knob and it sets the excitation's cut-off at
    about 1/T, which is why the same modal bank can be made to sound like glass,
    carbon or rubber without touching the bank:

        glass on glass, shard on concrete   T = 0.05 - 0.3 ms
        carbon panel on carbon              T = 0.3  - 1   ms
        rubber tyre on kerb                 T = 3    - 15  ms

    A bare impulse -- which is what every impact in this file used before -- has
    a flat spectrum to Nyquist and therefore no hardness at all. It excites the
    18 kHz modes exactly as hard as the 200 Hz ones, which no physical contact
    does, and it is why every struck object here sounded like the same struck
    object.
    """
    L = max(int(round(t_contact_s * sr)), 2)
    t = np.arange(L) / sr
    f = amplitude * (1.0 - np.cos(2.0 * np.pi * t / (L / sr)))
    if pad_s > 0:
        f = np.concatenate([f, np.zeros(int(pad_s * sr))])
    return f


# ================================================================= assembly ==
# CARBON IS NOT LOWER IN PITCH THAN METAL. IT IS SHORTER IN TIME.
#
# Three numbers, all audible, and the first one is the one everybody gets wrong:
#
#   * SPECIFIC STIFFNESS. sqrt(E/rho) for CFRP is 8000-9000 m/s against 5055 for
#     aluminium and 3900 for titanium. Bending frequency goes as that number, so
#     a carbon panel rings HIGHER than the aluminium one it replaced, not lower.
#   * LOSS FACTOR. CFRP's eta is 30-300x aluminium's, so the ring dies in tens
#     of milliseconds instead of seconds. That -- not pitch -- is what makes
#     composite sound like composite.
#   * ORTHOTROPY. A laminate has different stiffness along and across the fibre,
#     which splits mode pairs that would be degenerate in an isotropic part. The
#     pair beats, slowly, over the first 20-50 ms of the ring.
#
# Bolted joints then set a floor on damping regardless of the base material:
# eta = 5e-3 to 2e-2, i.e. Q 50-200, for any assembled structure.
ASM_MATERIALS = {
    # name: (sqrt(E/rho) m/s, Q, orthotropy split fraction)
    "cfrp":      (8600.0, 65.0, 0.025),
    "aluminium": (5055.0, 170.0, 0.0),
    "titanium":  (3900.0, 150.0, 0.0),
}
# which cluster is made of what. An F1 car is a carbon car with metal corners
# and a titanium halo, and those three groups sound different.
ASM_CLUSTER_MATERIAL = {
    "CORNER_FL": "aluminium", "CORNER_FR": "aluminium",
    "CORNER_RL": "aluminium", "CORNER_RR": "aluminium",
    "halo_assembly": "titanium",
}


def cluster_modes(size, material="cfrp", n_modes=10, n_parts=1):
    """A MODE SET FROM THIS CLUSTER'S OWN GEOMETRY (R2-4048).

    WHAT WAS HERE. Every part seat in beat 1 -- all 616 of them, across 15
    clusters -- was the same four sines at the fixed ratios 1 : 2.31 : 3.87 :
    6.1, transposed by the cluster's bounding-box volume and sharing one
    exponential decay. Fifteen different objects, one instrument. That is the
    other half of "the instrument The Tubes over and over": not only is the
    reverb a ringing copy of each hit, the hits are all the same bank.

    WHAT REPLACES IT. The bounding box says whether a part is a BEAM or a
    PLATE, and the two have different mode series:

      * beam, free-free bending: f_k ~ beta_k^2, beta = 4.730, 7.853, 10.996,
        14.137 -> ratios 1 : 2.756 : 5.404 : 8.933. Used when the longest
        dimension is more than 3.5x the shortest -- wishbones, extrusions, the
        monocoque's longitudinals.
      * plate: f_mn ~ (m/a)^2 + (n/b)^2 on the two largest dimensions with the
        smallest as thickness. Used for panels -- floor, wings, bodywork.

    Both are computed from sqrt(E/rho) and the actual dimensions, so a 5.47 m
    monocoque and a 0.128 m steering wheel get genuinely different SPECTRA and
    not merely different transpositions of one spectrum.
    """
    # WHAT RINGS IS A PART, NOT THE CLUSTER'S BOUNDING BOX. `size` is the bbox
    # of a whole cluster -- 5.47 m for the monocoque, containing 17 pieces -- and
    # treating that box as one plate makes its smallest dimension a "thickness"
    # of 0.89 m, which is not a thing. Scale the box down by n_parts^(1/3) to get
    # the linear size of a typical member, which is what a seat impact excites.
    k_part = max(float(n_parts), 1.0) ** (1.0 / 3.0)
    d = sorted(float(x) / k_part for x in size)
    depth, mid, long_ = d[0], d[1], d[2]
    # a car part is thin-walled: the wall is a fraction of the member's depth,
    # bounded to the 2-12 mm range that composite and sheet parts actually are
    h_wall = float(np.clip(depth * 0.15, 0.002, 0.012))
    cbar, q, split = ASM_MATERIALS[material]
    if long_ > 3.5 * depth:
        betas = np.array([4.730, 7.853, 10.996, 14.137, 17.279, 20.420])
        kappa = depth * 0.289                              # radius of gyration
        f = (betas ** 2) / (2.0 * np.pi * long_ ** 2) * kappa * cbar
        kind = "beam"
    else:
        # plate constant: (pi/2) sqrt(D/(rho h)) = (pi/2) h cbar / sqrt(12(1-nu^2))
        kp = (np.pi / 2.0) * h_wall * cbar / np.sqrt(12.0 * (1.0 - 0.30 ** 2))
        mm = np.arange(1, 5)[:, None]
        nn = np.arange(1, 5)[None, :]
        f = (kp * ((mm / mid) ** 2 + (nn / long_) ** 2)).ravel()
        f = np.sort(f)
        kind = "plate"
    f = f[:n_modes]
    # orthotropy: split each mode into a pair a few percent apart -> beating
    if split > 0.0:
        df = np.clip(f * split, 20.0, 50.0)
        f = np.concatenate([f - df * 0.5, f + df * 0.5])
        order = np.argsort(f)
        f = f[order]
    f = f[(f > 25.0) & (f < 20000.0)]
    tau = q / (np.pi * np.maximum(f, 1.0))
    amp = 1.0 / np.sqrt(np.arange(1, f.size + 1, dtype=np.float64))
    return f, amp, tau, {"kind": kind, "material": material, "q": q,
                         "part_size_m": [round(float(x), 4) for x in d],
                         "wall_mm": round(h_wall * 1e3, 2),
                         "cbar_ms": cbar, "modes": int(f.size),
                         "f_hz": [float(v) for v in f[:8]],
                         "beat_period_ms": float(1000.0 / max(np.clip(f[0] * split, 20.0, 50.0), 1e-9))
                         if split > 0 else None}


# ===================== B5(b) / B6: THE SCHEDULE AND THE SERVO ================
#
# WHAT COULD NOT BE DONE, AND IT IS SAID HERE RATHER THAN WORKED AROUND.
# The spec's B5(a) regenerates `world/beat1_anim_anim.json` with non-uniform
# seat frames on a geometric contraction. THAT IS A PICTURE CHANGE: the 15
# cluster seat frames in that file are the frames at which the 2,978 DELIVERED
# 4K frames show each cluster arriving, and moving them desynchronises the audio
# from a film that is already rendered and is not being re-rendered. So the
# 25-frame (1.041667 s) cluster ladder SURVIVES, its envelope autocorrelation
# survives at reduced r, and this file does not claim otherwise.
#
# What IS available without touching a frame is everything inside each cluster's
# own declared [seat_frame, last_land] window -- 8 frames, 0.3333 s -- because
# the picture does not declare per-part arrival times at all. The audio was
# inventing them, and it was inventing them as an EXACT ARITHMETIC RAMP:
#
#     fr = seat_f + (last_f - seat_f) * (p / (nparts - 1))
#
# which places n parts at exactly equal intervals across exactly 8 frames, i.e.
# an impulse train at exactly 3*(n_parts-1) Hz. Measured on the shipped
# clusters that is 27, 36, 42, 48, 96, 120, 129, 156, 192, 288 and 357 Hz --
# eleven audible pitches, one per cluster, produced by arithmetic and by nothing
# physical.
ARRIVAL_NOTE = (
    "within each cluster's own [seat_frame, last_land] window, arrival times "
    "are t = sqrt(2h/g) from each part's own start height, plus one restitution "
    "bounce inside the anim's own settle_frames allowance. The cluster-level "
    "schedule is the picture's and is untouched.")

G_ACCEL = 9.80665
SETTLE_FRAMES = 3          # `world/beat1_anim_anim.json` declares this
# Restitution for a carbon or aluminium part landing on the showroom's dressed
# deck. A rigid part on a hard floor is 0.5-0.7; a part landing on a padded
# locating cradle -- which is what an exploded-view rig seats into -- is much
# lower. 0.22 is the figure that puts the bounce inside the 3-frame settle the
# animation itself allows for every cluster, which is the constraint the picture
# imposes on this number.
RESTITUTION = 0.22


def _stable_unit(name, k):
    """A deterministic value in [0, 1) from a name and an index.

    Not an RNG draw: the same part must get the same start height in every
    render and in every rebuild, and it must not move when a cluster's part
    COUNT changes, which a shared `rng` walking through the loop would do."""
    h = hashlib.sha256(("%s/%d" % (name, k)).encode()).digest()
    return int.from_bytes(h[:6], "big") / float(1 << 48)


def cluster_arrivals(name, nparts, seat_f, last_f, c, fps=24):
    """[(frame, gain, kind)] for one cluster, replacing the exact grid.

    THE PHYSICS. Every part in a cluster starts somewhere inside the exploded
    shell -- the cluster's own bounding box, lifted by its `explode_offset` --
    and falls to its seat. A body released from height h lands at
    t = sqrt(2h/g), so EQUAL SPACING IN HEIGHT IS NOT EQUAL SPACING IN TIME:
    the arrivals bunch up at the end, because the pieces that started lowest are
    already down while the highest is still travelling. That is why a real
    assembly clatters rather than buzzes, and it is the whole difference between
    this and `p / (nparts - 1)`.

    The window is preserved EXACTLY. The earliest arrival is `seat_f` and the
    latest is `last_f`, so the picture's declared per-cluster window is
    unchanged to the frame; what changes is the distribution inside it.

    THE BOUNCE is one restitution contact at 2*e*v_imp/g after the first, at
    e^2 of the energy, i.e. 20*log10(e) = -13.2 dB. It is inside the animation's
    own 3-frame settle allowance by construction (see RESTITUTION), so nothing
    sounds after the picture has come to rest.
    """
    nparts = int(max(nparts, 1))
    span_f = float(max(last_f - seat_f, 1))
    zsize = float(c["size"][2]) if "size" in c else 0.3
    lift = abs(float(c["explode_offset"][2])) if "explode_offset" in c else 0.0
    # each part's own drop height: the cluster's lift plus where it sits inside
    # the cluster's own vertical extent
    h = np.array([max(lift + zsize * _stable_unit(name, k), 1e-3)
                  for k in range(nparts)], dtype=np.float64)
    t_fall = np.sqrt(2.0 * h / G_ACCEL)
    t_fall = np.sort(t_fall)
    # map the SET of fall times onto the picture's window, preserving its shape
    if float(t_fall.max() - t_fall.min()) < 1e-9:
        u = np.linspace(0.0, 1.0, nparts)
    else:
        u = (t_fall - t_fall.min()) / (t_fall.max() - t_fall.min())
    frames = seat_f + u * span_f
    v_imp = np.sqrt(2.0 * G_ACCEL * h)
    t_bounce = 2.0 * RESTITUTION * v_imp / G_ACCEL          # seconds of flight
    out = []
    for k in range(nparts):
        out.append((float(frames[k]), 1.0, "first"))
        fb = float(frames[k] + t_bounce[k] * fps)
        if fb - frames[k] <= SETTLE_FRAMES:
            out.append((fb, float(RESTITUTION), "bounce"))
    return out


# ---- the servo bed: fifteen actuators, not one LFO -------------------------
# A ballscrew actuator with a 20 mm lead. Lead is what converts the carriage's
# linear speed into a shaft rate, so it is the single number that sets every
# tone in this layer: shaft = v / lead.
BALLSCREW_LEAD_M = 0.020
GEAR_TEETH = 23            # prime, so mesh orders never coincide with shaft orders
POLE_PAIRS = 4             # PMSM radial force is at 2 * f_electrical = 8 * shaft
STATOR_SLOTS = 12
# The actuator arm is a cantilever, so its first bending mode goes as 1/L^2.
# `ARM_F1_AT_1M` is that mode for a 1 m arm of the section these rigs use; each
# cluster's arm length is its own `explode_distance`, so fifteen clusters give
# fifteen different structural frequencies with no common factor and no shared
# period. This is what replaces `f_srv = 320 + 90*sin(2*pi*0.11*t)` -- ONE
# global 9.09 s LFO running the entire showroom.
ARM_F1_AT_1M = 620.0
# Position-loop bandwidth: the rate at which a servo holding a static load
# hunts across its encoder's last count. 20-80 Hz is the normal range for a
# stiff electric axis, and it is spread deterministically per cluster.
DITHER_HZ = (22.0, 79.0)
FLIGHT_S = 1.55            # `world/beat1_anim_anim.json` declares this


def servo_bed(t_world, clusters, sr, launch_film_t, fps=24, seed=1235):
    """B6 -- ONE SERVO PER CLUSTER, replacing one LFO for the whole showroom.

    WHAT WAS HERE, AND WHY IT IS THE "WIND BLOWER".

        f_srv = 320 + 90*sin(2*pi*0.11*t)
        srv   = sin(ph)*0.5 + sin(2.7*ph)*0.2 + bp(white, 900, 6000)*0.6

    Three separate defects in three lines. (1) The BROADBAND term is weighted
    0.6, higher than both tonal terms combined (0.5 + 0.2), and it carries
    22.2 % of all power over 0-13.5 s -- before the first impact exists. It is
    the only thing in the film during the seconds the client described, and it
    is band-passed white noise. (2) One global LFO at 0.11 Hz gives the entire
    showroom a single 9.09 s period, measured in the delivered stem as a
    231.6-409.2 Hz sweep with turning points 8.92 s apart. (3) 2.7x is not a
    ratio of anything.

    WHAT REPLACES IT. Fifteen independent electric actuators, each one modelled
    from the cluster it is carrying:

      * WHILE MOVING -- gear mesh at N_teeth * shaft, stator slot passing at
        N_slots * shaft, and PMSM radial force at 2 * f_electrical =
        2 * pole_pairs * shaft, where shaft = v / lead comes from that cluster's
        OWN descent, which starts `FLIGHT_S` before its OWN seat frame. Fifteen
        trajectories, fifteen start times, no global period.
      * WHILE HOLDING -- the axis is under load and the position loop hunts, so
        the arm's own first bending mode is struck at the loop's bandwidth.
        f_arm = ARM_F1_AT_1M / L^2 with L the cluster's own reach, which gives
        fifteen different pitches between roughly 70 and 620 Hz. THIS IS THE
        LAYER THAT FILLS THE ~1.04 s OF NAKED REVERB BETWEEN BURSTS, and it is
        tonal, which is what the gap needed.
      * BEARING NOISE -- broadband, at 0.06 rather than 0.6, narrowed to the
        1.5-4 kHz band where a rolling-element bearing's housing resonance
        actually lies, and scaled by shaft rate so it exists only while the axis
        is moving. A bearing at rest makes no noise; the shipped layer's hiss
        ran at full level for thirty seconds with nothing turning.
    """
    n = t_world.shape[0]
    tf = t_world + launch_film_t                     # film time, seconds
    out = np.zeros(n, dtype=np.float64)
    info = []
    for i, (name, c) in enumerate(sorted(clusters.items())):
        seat_f = int(c["seat_frame"])
        seat_t = (seat_f - 1) / float(fps)
        reach = max(float(c.get("explode_distance", 0.0)), 0.25)
        f_arm = float(np.clip(ARM_F1_AT_1M / reach ** 2, 60.0, 1400.0))
        f_dither = DITHER_HZ[0] + (DITHER_HZ[1] - DITHER_HZ[0]) * _stable_unit(name, 7)
        # ---- the descent, and the shaft rate it implies --------------------
        u = np.clip((tf - (seat_t - FLIGHT_S)) / FLIGHT_S, 0.0, 1.0)
        # smoothstep position: the animation eases in and out, so the carriage
        # is at rest at both ends and fastest in the middle
        dpos_du = 6.0 * u * (1.0 - u)                # d/du of 3u^2 - 2u^3
        v = dpos_du * reach / FLIGHT_S               # m/s
        shaft = v / BALLSCREW_LEAD_M                 # rev/s
        moving = (u > 0.0) & (u < 1.0)
        holding = (tf >= 0.0) & (tf < seat_t)
        # ---- tones ---------------------------------------------------------
        def tone(mult, amp):
            f = np.clip(shaft * mult, 0.0, sr * 0.44)
            return amp * np.sin(dsp.integrate_phase(f, sr)) * moving
        mech = (tone(GEAR_TEETH, 0.55)
                + tone(GEAR_TEETH * 2.0, 0.18)
                + tone(STATOR_SLOTS, 0.30)
                + tone(2.0 * POLE_PAIRS, 0.40))
        # loading: a servo lifting is louder than one coasting
        mech *= 0.35 + 0.65 * np.clip(shaft / max(float(shaft.max()), 1e-9), 0.0, 1.0)
        # ---- the hold: the arm's own mode, struck by the position loop ------
        dither = 0.5 * (1.0 - np.cos(2.0 * np.pi * f_dither * tf))
        hold = np.sin(dsp.integrate_phase(np.full(n, f_arm), sr)) * (0.25 + 0.75 * dither ** 2)
        hold = hold * holding * 0.45
        # ---- bearing: broadband, but only while something is turning -------
        # DERIVATION: a rolling-element bearing radiates through the resonance
        # of its own outer ring and housing, which for the 20-40 mm bores an
        # electric axis of this size uses sits at 1.5-4 kHz. The band is the
        # HOUSING's, not a choice; what varies with speed is the level, below.
        # derivation: the bearing housing's own resonance -- see above.
        bear = dsp.bp(dsp.white(n, seed + 17 * i), 1500.0, 4000.0, sr, 2)
        bear = bear * 0.06 * np.clip(shaft / 40.0, 0.0, 1.0) * moving
        sig = (mech + hold + bear)
        # each actuator switches off at its own seat frame: fifteen different
        # stop times is the structural answer to "one global period"
        sig *= np.clip((seat_t + 0.10 - tf) / 0.10, 0.0, 1.0) * (tf > -0.5)
        out += sig * 0.012
        info.append({"cluster": name, "arm_reach_m": round(reach, 3),
                     "arm_mode_hz": round(f_arm, 1),
                     "position_loop_hz": round(float(f_dither), 2),
                     "peak_shaft_rev_s": round(float(shaft.max()), 1),
                     "gear_mesh_hz_peak": round(float(shaft.max()) * GEAR_TEETH, 1),
                     "seat_film_t_s": round(seat_t, 4)})
    return out, {"voices": len(info), "ballscrew_lead_m": BALLSCREW_LEAD_M,
                 "gear_teeth": GEAR_TEETH, "pole_pairs": POLE_PAIRS,
                 "stator_slots": STATOR_SLOTS,
                 "broadband_gain": 0.06, "broadband_band_hz": [1500.0, 4000.0],
                 "replaces": ("f_srv = 320 + 90*sin(2*pi*0.11*t) with a 0.6 "
                              "band-passed white-noise term -- one LFO and one "
                              "hiss for the whole showroom"),
                 "per_cluster": info}


def assembly(t_world, clusters, sr, launch_film_t, fps=24, seed=1234):
    """Beat 1: servo whir plus one impact per cluster arrival.

    Arrival times are the ACTUAL seat frames from `world/beat1_anim_anim.json`;
    each cluster's modal bank comes from its own bounding box and material via
    `cluster_modes`, and each seat is driven by a Hertzian contact force whose
    duration is the material pairing's -- not by a bare impulse, which excites
    every mode equally hard and is why every part sounded like the same part.
    """
    n = t_world.shape[0]
    rng = np.random.default_rng(seed)
    out = np.zeros(n, dtype=np.float64)
    ev = []
    n_bounce = 0
    t0 = float(t_world[0])
    cl_info = {}
    for name, c in clusters.items():
        seat_f = int(c["seat_frame"])
        last_f = int(c.get("last_land", seat_f))
        vol = float(c["size"][0] * c["size"][1] * c["size"][2])
        mat = ASM_CLUSTER_MATERIAL.get(name, "cfrp")
        f_c, a_c, tau_c, minfo = cluster_modes(c["size"], mat,
                                               n_parts=int(c["n_parts"]))
        cl_info[name] = minfo
        if f_c.size == 0:
            continue
        # contact time: carbon on carbon is a SOFTER contact than metal on
        # metal, so it excites a narrower band. This is the hardness knob, and
        # it is set by the material pairing rather than by a filter.
        t_contact = 6.0e-4 if mat == "cfrp" else 2.0e-4
        nparts = int(c["n_parts"])
        arrivals = cluster_arrivals(name, nparts, seat_f, last_f, c, fps)
        n_bounce += sum(1 for _fr, _g, kind in arrivals if kind == "bounce")
        for p, (fr, g_bounce, kind) in enumerate(arrivals):
            wt = (fr - 1) / fps - launch_film_t
            i = int((wt - t0) * sr)
            if not (0 <= i < n - int(0.9 * sr)):
                continue
            # each PART of a cluster is a different piece of the same structure:
            # scatter its modes, do not transpose the whole bank by a constant
            jitter = rng.lognormal(0.0, 0.22, f_c.size)
            f = f_c * jitter
            tau = tau_c / jitter
            amp = a_c * hertz_spectrum(f, t_contact) * rng.uniform(0.6, 1.4, f.size)
            L = int(min(float(np.max(np.minimum(6.0 * tau, 0.9))), 0.9) * sr)
            if L < 32 or i + L >= n:
                continue
            tt = np.arange(L) / sr
            ph = rng.uniform(0.0, 2 * np.pi, f.size)
            hit = np.zeros(L)
            for j in range(f.size):
                Lj = int(min(6.0 * tau[j], 0.9) * sr)
                if Lj < 16:
                    continue
                hit[:Lj] += amp[j] * np.sin(2 * np.pi * f[j] * tt[:Lj] + ph[j]) \
                    * np.exp(-tt[:Lj] / tau[j])
            # acceleration noise of the contact itself, same construction as the
            # shards: one cycle at 1/T, not a broadband click
            hit += _accel_noise(sr, t_contact, ACCEL_NOISE_RATIO * float(amp.sum()), L)
            g = 0.30 * (vol ** 0.30) / max(nparts, 1) ** 0.35 * g_bounce
            pk = float(np.abs(hit).max())
            if pk > 0:
                out[i:i + L] += hit / pk * g
            ev.append((name, fr, float(f[0]), kind))
    out = _sig.sosfilt(dsp.sos_band(45.0, 18000.0, sr, 2), out)

    srv, srv_info = servo_bed(t_world, clusters, sr, launch_film_t, fps=fps,
                              seed=seed + 1)
    out += srv
    return out.astype(np.float32), {
        "impacts": len(ev), "clusters": len(clusters), "cluster_modes": cl_info,
        "first_contacts": len(ev) - n_bounce, "restitution_bounces": n_bounce,
        "arrival_schedule": ARRIVAL_NOTE, "servo": srv_info}


# =================================================================== breach ==
# free square plate, first mode: f = 0.47 (h/L^2) c_L. Writing the general
# rectangular form as f_mn = K ((m/a)^2 + (n/b)^2) and demanding that a = b = L
# reproduce that number fixes K exactly -- no free constant anywhere.
SHARD_K = 0.47 * GLASS_H * GLASS_CL / 2.0                       # 15.30
SHARD_KA1 = float(dsp.speed_of_sound(18.0)) / (2.0 * np.pi)      # 54.6 -> /L Hz


def shard_modes(L, rng, n_modes=None, mmax=4, nmax=4):
    """THE MODE SET OF ONE SHARD. Eight to fourteen modes, and no two shards
    share a spectrum (R2-4041).

    WHAT WAS HERE. Three pure sines at the fixed ratios 1 : 2.08 : 3.41, one
    shared exponential decay for all three, and a 0.4 ms DC bump on the front.
    Every shard in the film had the same spectrum, transposed. That is the
    textbook construction of a STRUCK BAR, and it is literally the client's
    "someone banging on tubes" -- not an approximation of it, the thing itself.

    WHAT A SHARD IS INSTEAD. A fractured pane does not produce squares. Draw an
    aspect ratio r ~ lognormal(0, 0.35) and treat the piece as a free plate of
    sides L*sqrt(r) and L/sqrt(r); the rectangular mode formula then splits the
    degenerate (m,n)/(n,m) pairs by an amount that depends on r, so the
    spectrum's SHAPE varies from shard to shard rather than only its pitch. A
    further lognormal(0, 0.08) per mode covers the fact that a fracture edge is
    not a clean rectangle. Reference free-square ratios 1 : 1.47 : 1.81 : 2.60
    : 2.60 : 4.56 are recovered to within that jitter.

    PER-MODE DECAY. tau_n = Q/(pi f_n) with Q = 800-1500. Frequency-proportional
    damping is the cue a listener uses to identify a material, and the previous
    single `decay` -- capped at 0.45 s and scaled LINEARLY in L -- was wrong
    twice: all modes died together, and tau should go as L^2, which it now does
    because f goes as 1/L^2.

    Returns (freqs, amps, taus, q).
    """
    r = float(rng.lognormal(0.0, 0.35))
    a = L * np.sqrt(r)
    b = L / np.sqrt(r)
    m = np.arange(1, mmax + 1)[:, None]
    nn = np.arange(1, nmax + 1)[None, :]
    f = SHARD_K * ((m / a) ** 2 + (nn / b) ** 2)
    f = f.ravel() * rng.lognormal(0.0, 0.08, f.size)
    order = np.argsort(f)
    k = int(n_modes if n_modes is not None else rng.integers(8, 15))
    idx = order[:k]
    f = f[idx]
    # modal amplitude falls with mode order for a point strike; the physical
    # part of that is the contact-force spectrum, applied by the caller, so what
    # is left here is the modal density weighting alone
    amps = 1.0 / np.sqrt(np.arange(1, k + 1, dtype=np.float64))
    q = float(rng.uniform(800.0, 1500.0))
    taus = q / (np.pi * f)
    return f, amps, taus, q


def hertz_spectrum(f, t_contact_s):
    """|F(f)| of the Hertzian half-cosine, normalised to 1 at DC.

    The closed form of the raised-cosine pulse: flat below 1/T, then -18 dB per
    octave. This is what makes contact HARDNESS audible -- a bare impulse
    (which is what this file used) is flat to Nyquist and excites an 18 kHz mode
    exactly as hard as a 200 Hz one, which no physical contact does.
    """
    u = np.asarray(f, dtype=np.float64) * float(t_contact_s)
    out = np.empty_like(u)
    near = np.abs(np.abs(u) - 1.0) < 1e-6
    safe = ~near
    with np.errstate(divide="ignore", invalid="ignore"):
        out[safe] = np.abs(np.sinc(u[safe]) / (1.0 - u[safe] ** 2))
    out[near] = 0.5
    return out


def shard_ballistics(spec, v_contact, seed=31337, max_shards=2200):
    """A real (if simple) ballistic simulation of the shard field.

    Not a random tinkle generator: every shard has a size, a mass, a launch
    velocity, a flight, and a sequence of floor contacts, and the tinkle tail's
    TIMING is whatever that produces. Fed by the telemetry's own contact speed.

    Returns a list of (t_world, position, freqs, amp, decay_s) contact events and
    a summary.
    """
    ap = spec["showroom"]["breach_aperture_m"]
    W, H = float(ap["width"]), float(ap["height"])
    cx, cy, cz = ap["centre_world"]
    rng = np.random.default_rng(seed)

    area_total = W * H
    impact = np.array([cx, 0.0, 0.60])            # the nose meets the pane here
    events = []
    shards = []
    area = 0.0
    while area < area_total and len(shards) < max_shards:
        y = rng.uniform(-W * 0.5, W * 0.5)
        z = rng.uniform(cz - H * 0.5, cz + H * 0.5)
        d = float(np.hypot(y - impact[1], z - impact[2]))
        # SMALL AT THE IMPACT POINT, LARGER AT THE EDGES -- the brief's own rule,
        # and what a real cell-fracture pattern does.
        L = (0.030 + 0.34 * np.clip(d / 3.2, 0.0, 1.0)) * float(rng.lognormal(0.0, 0.45))
        L = float(np.clip(L, 0.015, 0.75))
        area += L * L
        m = GLASS_RHO * GLASS_H * L * L
        # launch: radially away from the impact point, decaying with distance,
        # plus the forward push of the car coming through
        rad = np.array([0.0, y - impact[1], z - impact[2]])
        nrm = float(np.linalg.norm(rad))
        rad = rad / nrm if nrm > 1e-6 else np.array([0.0, 1.0, 0.0])
        sp = v_contact * float(np.exp(-d / 2.6)) * float(rng.uniform(0.25, 1.15))
        vel = rad * sp + np.array([v_contact * float(rng.uniform(0.35, 0.95)), 0.0, 0.0]) \
            + rng.normal(0.0, 1.4, 3)
        shards.append((np.array([cx, y, z]), vel, L, m))

    # ring frequencies: a free plate of side L and thickness h rings at
    # 0.47 * (h / L^2) * c_L, with the classic 1 : 2.08 : 3.41 free-plate ratios
    #
    # FLIGHT IS INTEGRATED, NOT SOLVED IN CLOSED FORM, because a shard of glass
    # is not a cannonball. Its drag area over mass is A/m = L^2 / (rho h L^2) =
    # 1 / (rho h) = 1/30 m^2/kg REGARDLESS of size, so the drag deceleration
    # k|v|v with k = 0.5 rho_air Cd (A/m) = 0.024 /m is 6.7 m/s^2 at 16.7 m/s --
    # comparable to gravity, and the reason a shattered pane lands in a heap in
    # front of the opening instead of 40 m down the apron. The closed-form
    # parabola this replaced threw debris to x = 59 m.
    K_DRAG = 0.5 * 1.204 * 1.2 / (GLASS_RHO * GLASS_H)
    DT = 1.0 / 480.0
    debris_x = []
    # R2-4041: THE BALLISTICS OWN THE MECHANICS AND NOTHING ELSE. An event is
    # now (t, position, shard_index, normal_speed_in, bounce_number, size). The
    # mode set that shard rings with belongs to `shard_modes` and is looked up
    # by `render_shards`, so "how it flies" and "what it sounds like" can no
    # longer silently constrain each other -- which is how `amp = m * vz` came
    # to sit two lines from `f1 = 30.59/L^2` and make loudness the reciprocal of
    # pitch without anybody writing that down.
    for sid, (p0, v0, L, m) in enumerate(shards):
        p = p0.copy(); v = v0.copy()
        t = 0.0
        bounce = 0
        for _step in range(int(6.0 / DT)):
            sp_ = float(np.linalg.norm(v))
            acc = np.array([0.0, 0.0, -G]) - K_DRAG * sp_ * v
            v = v + acc * DT
            p = p + v * DT
            t += DT
            if p[2] <= 0.0:
                p[2] = 0.0
                vz_in = abs(v[2])
                e = 0.30 * float(rng.uniform(0.6, 1.25))
                events.append((t, p.copy(), int(sid), float(vz_in), int(bounce), float(L)))
                debris_x.append(float(p[0]))
                v = np.array([v[0] * 0.72, v[1] * 0.72, vz_in * e])
                p[2] = 1e-3
                bounce += 1
                if v[2] < 0.30 or bounce >= 4:
                    break
    events.sort(key=lambda e: e[0])
    dx = np.array(debris_x) if debris_x else np.array([15.0])
    summary = {
        "shards": len(shards),
        "contact_events": len(events),
        "glass_area_m2": float(area),
        "aperture_m2": float(area_total),
        "contact_speed_ms": float(v_contact),
        "shard_size_min_m": float(min(s[2] for s in shards)),
        "shard_size_max_m": float(max(s[2] for s in shards)),
        "ring_hz_min": float(0.47 * GLASS_H / max(s[2] for s in shards) ** 2 * GLASS_CL),
        "ring_hz_max": float(0.47 * GLASS_H / min(s[2] for s in shards) ** 2 * GLASS_CL),
        "settle_world_s": float(max(e[0] for e in events)) if events else 0.0,
        "drag_coefficient_per_m": float(K_DRAG),
        "debris_p80_x_m": float(np.percentile(dx, 80)),
        "debris_p95_x_m": float(np.percentile(dx, 95)),
        "debris_max_x_m": float(dx.max()),
    }
    return events, summary


def render_shards(events, n, sr, onset_t, groups=4, seed=31337):
    """Render the contact events into `groups` spatial buckets, ON THE FILM GRID.

    `onset_t` is the FILM time of each event, already mapped through the clock by
    the caller. The schedule is therefore stretched by the world-time ramp while
    every shard rings at its own physical frequency -- see master.py R2-4035 for
    why the previous contract (synthesise on the world grid, then varispeed the
    whole buffer) transposed the entire shard field 6.51x down into the
    infrasonic.

    Bucketing is by world Y so the shard field has real width at the ears rather
    than collapsing to a point. Each bucket returns (signal, centroid position).

    R2-4042: AMPLITUDE WAS EXACTLY INVERSELY PROPORTIONAL TO PITCH.
    ---------------------------------------------------------------
    The old law was two lines apart and nobody wrote down their product:

        m  = GLASS_RHO * GLASS_H * L * L   = 30 L^2         (ballistics)
        f1 = 0.47 * (GLASS_H / L^2) * c_L  = 30.59 / L^2    (ballistics)
        amp = m * vz_in                                     (ballistics)

    so amp = 917.7 * vz / f1. A BIG SLAB IS LOUD AND LOW, A BRIGHT CHIP IS
    SILENT. Measured over the 995 contacts: log-amplitude against log-frequency
    fits a slope of -0.994, the top ten contacts carry 32.1% of all shard energy
    and ALL TEN OF THEM RING AT 54.4 Hz (the L = 0.75 m size clamp). 99.67% of
    the field's energy sat below 500 Hz and 0.004% above 2 kHz -- before the
    world-time warp had even been applied.

    THE FILE ALREADY COMPUTED THE CORRECTION AND DECLINED TO USE IT HERE.
    `glass_wall` weights the pane's modes by radiation efficiency about a
    critical frequency of 1004 Hz. A shard radiates by the same physics, and
    two mechanisms apply:

      * BENDING-WAVE RADIATION below coincidence: amplitude x f/f_c, which
        takes a 54.4 Hz contact down 25.3 dB and leaves anything above 1 kHz
        untouched.
      * FINITE SOURCE SIZE: a body radiates poorly below ka = 1, i.e. below
        f = c/(2 pi a) = 54.6/L Hz for a shard of half-size L/2. First order,
        per shard.

    Neither is authored. Both make brightness a consequence of SIZE, which is
    what makes a shower of glass sound sorted by size instead of sounding like
    one instrument played at different pitches.
    """
    n = int(n)
    ys = np.array([e[1][1] for e in events]) if events else np.zeros(1)
    edges = np.quantile(ys, np.linspace(0.0, 1.0, groups + 1))
    edges[0] -= 1.0; edges[-1] += 1.0
    sigs = [np.zeros(n, dtype=np.float64) for _ in range(groups)]
    cents = [np.zeros(3) for _ in range(groups)]
    counts = [0] * groups
    onset_t = np.asarray(onset_t, dtype=np.float64)

    # every shard's mode set, drawn once and reused for all four of its bounces
    n_shards = max((e[2] for e in events), default=-1) + 1
    mrng = np.random.default_rng(seed + 7)
    modes = [shard_modes(float(L), mrng) for L in
             _shard_sizes(events, n_shards)]

    # LENGTH CAP. tau = Q/(pi f) is 5.9 s for a 54 Hz mode at Q = 1000, and a
    # 995-contact field cannot afford 6 tau of every mode. Each MODE gets its
    # own length, min(6 tau, CAP), and the truncation is faded so it is a decay
    # and not a click. At the cap, everything above 3.2 kHz is fully resolved.
    CAP = 0.6
    fade = int(0.004 * sr)
    silent = []
    rendered = 0
    for k_ev, (t, p, sid, vz_in, bounce, L) in enumerate(events):
        gi = int(np.clip(np.searchsorted(edges, p[1]) - 1, 0, groups - 1))
        i = int(onset_t[k_ev] * sr)
        if i < 0 or i >= n:
            continue
        f, a_mode, tau, q = modes[sid]
        # CONTACT DAMPING AFTER THE FIRST BOUNCE. Q = 800-1500 is the damping of
        # a FREE plate, which is what a shard is on the way down and for the
        # first bounce. After that it is skittering on concrete among other
        # debris, in continuous contact with a surface that is nothing like
        # glass, and its Q collapses. Rendering every bounce as a free plate is
        # both wrong and expensive: 64% of the 995 contacts are second, third or
        # fourth bounces, each ringing for 0.4 s, which is what turned a shower
        # into a continuous tone bed (50 ms crest 10.1 dB on the shard bus).
        tau = tau * (0.35 ** min(int(bounce), 3))
        vz = max(float(vz_in), 1e-4)
        m_shard = GLASS_RHO * GLASS_H * L * L
        # T for glass on concrete, 0.05-0.3 ms, softening slightly with each
        # bounce as the piece stops arriving edge-on
        t_contact = 8e-5 * (1.0 + 0.6 * bounce) * (1.0 + 2.0 * L)
        drive = m_shard * vz
        amp = (a_mode * hertz_spectrum(f, t_contact)
               * np.asarray(rad_amp(f))
               * _size_highpass(f, L)) * drive
        amax = float(amp.max()) if amp.size else 0.0
        keep = ((f < sr * 0.45) & (amp > amax * 1e-4)) if amax > 0.0 \
            else np.zeros(f.shape, dtype=bool)
        if not np.any(keep):
            # G7: a contact that produces nothing is a contact that was dropped
            # on the floor. Sub-26.6 mm pieces used to land here silently
            # because every one of their modes sits above 0.45*sr; they are
            # rendered as the spectral tilt they actually are instead.
            s = _fines_burst(sr, L, drive, np.random.default_rng(seed + 1000 + k_ev))
            silent.append(k_ev)
            Ls = s.shape[0]
            if i + Ls < n:
                sigs[gi][i:i + Ls] += s
                cents[gi] += p
                counts[gi] += 1
                rendered += 1
            continue
        f, amp, tau = f[keep], amp[keep], tau[keep]
        Ls = int(min(float(np.max(np.minimum(6.0 * tau, CAP))), CAP) * sr)
        if i + Ls >= n or Ls < 16:
            continue
        tt = np.arange(Ls) / sr
        ph = mrng.uniform(0.0, 2.0 * np.pi, f.shape[0])
        s = np.zeros(Ls)
        for j in range(f.shape[0]):
            Lj = int(min(6.0 * tau[j], CAP) * sr)
            if Lj < 16:
                continue
            tj = tt[:Lj]
            w = np.exp(-tj / tau[j])
            if Lj > fade:
                w[Lj - fade:] *= np.linspace(1.0, 0.0, fade)
            s[:Lj] += amp[j] * np.sin(2.0 * np.pi * f[j] * tj + ph[j]) * w
        # ACCELERATION NOISE, not a DC bump. The old front end was
        # `s[:0.4ms] += 0.6*env`, a one-sided step whose spectrum peaks at DC:
        # a click, and inaudible as a transient once the chain high-passes.
        # The real radiated transient is d/dt of the contact force, which for
        # the Hertzian half-cosine is one full sine cycle at 1/T, band-limited.
        s[:] += _accel_noise(sr, t_contact, ACCEL_NOISE_RATIO * float(amp.sum()), Ls)
        sigs[gi][i:i + Ls] += s
        cents[gi] += p
        counts[gi] += 1
        rendered += 1
    # ---- SKITTER: real debris SLIDES after it stops bouncing ---------------
    # The delivered field stopped dead at the last contact. A piece of glass
    # that has finished bouncing is still moving horizontally, and it scrapes
    # to a halt over a few tenths of a second. This is `scrape`'s mechanism --
    # a stylus reading a spatial roughness profile at the sliding speed -- so
    # the skitter's pitch and brightness fall as the piece slows, rather than
    # being a fade-out of something stationary.
    last_of = {}
    for k_ev, e in enumerate(events):
        last_of[e[2]] = k_ev
    prof = roughness_profile(int(1.5 / 2.0e-5), w=2.5, seed=seed + 99)
    srng = np.random.default_rng(seed + 123)
    for sid, k_ev in last_of.items():
        t, p, _sid, vz_in, bounce, L = events[k_ev]
        i = int(onset_t[k_ev] * sr)
        dur = float(srng.uniform(0.3, 1.5))
        Ls = int(dur * sr)
        if i < 0 or i + Ls >= n or Ls < 64:
            continue
        gi = int(np.clip(np.searchsorted(edges, p[1]) - 1, 0, groups - 1))
        tt = np.arange(Ls) / sr
        v_sl = max(0.4, 0.35 * vz_in) * np.clip(1.0 - tt / dur, 0.0, 1.0) ** 1.5
        x = read_roughness(prof, v_sl, sr, 2.0e-5)
        f_r = float(np.clip(2.0 * SHARD_KA1 / max(L, 1e-3), 200.0, 12000.0))
        q = 25.0
        w0 = 2.0 * np.pi * f_r / sr
        al = np.sin(w0) / (2.0 * q)
        bq = np.array([al, 0.0, -al])
        aq = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        s = _sig.lfilter(bq / aq[0], aq / aq[0], x)
        # scaled off the CONTACT's own drive, so a heavy piece skitters loudly
        # and a light one does not, and the ratio to its own ring is fixed
        g = GLASS_RHO * GLASS_H * L * L * vz_in * 0.08 * float(rad_amp(f_r))
        sigs[gi][i:i + Ls] += s * g
    for gi in range(groups):
        if counts[gi]:
            cents[gi] /= counts[gi]
        else:
            cents[gi] = np.array([15.0, 0.0, 1.0])
    render_shards.last_rendered = rendered
    render_shards.last_fines = len(silent)
    render_shards.last_events = len(events)
    render_shards.last_skitters = len(last_of)
    return [(s.astype(np.float32), c) for s, c in zip(sigs, cents)]


def _shard_sizes(events, n_shards):
    """The size of each shard, recovered from its contacts (they all agree)."""
    out = np.full(max(n_shards, 1), 0.05)
    for (_t, _p, sid, _vz, _b, L) in events:
        out[sid] = L
    return out


def _size_highpass(f, L):
    """First-order radiation roll-off below ka = 1 for a piece of size L.

    f_ka1 = c / (2 pi a) with a = L/2 -> 109.2 / L Hz. A body much smaller than
    a wavelength moves the air out of its own way instead of compressing it, so
    it radiates almost nothing; this is why a 5 mm chip is inaudible at 50 Hz
    however hard it is hit, and why small debris sounds bright rather than quiet.
    """
    f0 = 2.0 * SHARD_KA1 / max(float(L), 1e-4)
    r = np.asarray(f, dtype=np.float64) / f0
    return r / np.sqrt(1.0 + r * r)


def _accel_noise(sr, t_contact, level, n_out):
    """d/dt of the Hertzian contact force: one full sine cycle at 1/T.

    THE SHAPE IS PHYSICAL, THE LEVEL IS DECLARED. Differentiating
    F(t) = F_max(1 - cos(2 pi t/T)) gives exactly one sine cycle at 1/T, so the
    transient's bandwidth is set by contact hardness and by nothing else -- a
    0.08 ms contact radiates to 12 kHz and a 3 ms one does not, without any
    filter being chosen. What is NOT derivable here is how loud that transient
    is relative to the modal ring, because that depends on the radiating area's
    motion during contact; ACCEL_NOISE_RATIO is that one number and it is
    stated rather than buried.

    What it replaces is not a competing model. It replaces
    `s[:0.4ms] += 0.6*env`: a one-sided step whose spectrum PEAKS AT DC, i.e. a
    click with no transient in it, and one that the chain's high-pass removes
    while leaving the shard with no attack at all.
    """
    L = max(int(round(t_contact * sr)), 4)
    t = np.arange(L) / sr
    a = np.sin(2.0 * np.pi * t / (L / sr)) * float(level)
    out = np.zeros(n_out)
    k = min(L, n_out)
    out[:k] = a[:k]
    return out


# the acceleration transient's peak, as a fraction of the summed modal
# amplitude of the same contact. See `_accel_noise`.
ACCEL_NOISE_RATIO = 0.45


def _fines_burst(sr, L, drive, rng, dur=0.02):
    """A piece too small to have a resolvable mode is a SPECTRAL TILT, not a pitch.

    Above about 16 kHz a listener cannot pitch a transient anyway, so a shard
    whose fundamental is above Nyquist-guard is rendered as a short noise burst
    centred where its mode would have been. This closes G7 from the small end:
    every event in the summary now produces non-zero output.
    """
    n = max(int(dur * sr), 32)
    f0 = float(np.clip(SHARD_K * 2.0 / max(L, 1e-4) ** 2, 200.0, sr * 0.42))
    x = rng.standard_normal(n)
    x = _sig.sosfilt(dsp.sos_band(max(f0 * 0.4, 100.0), min(f0 * 1.6, sr * 0.45), sr, 2), x)
    env = np.exp(-np.arange(n) / sr / 0.004)
    x = x / max(float(np.abs(x).max()), 1e-12)
    return x * env * drive * float(rad_amp(f0)) * float(_size_highpass(f0, L))


C_RAYLEIGH_GLASS = 3120.0        # c_R ~ 0.92 c_T for soda-lime
CRACK_TIP_SPEED = 0.55 * C_RAYLEIGH_GLASS      # 1716 m/s, the measured 0.5-0.6 c_R


# ============ FOUR FAMILIES THAT DID NOT EXIST ANYWHERE (R2-4049) ============
# Grepping brake / damper / suspension / shift / gear / kerb across audio/*.py
# returned nothing outside `engine.gear_and_rpm`. BEAT 6 IS AN 11.0 SECOND
# DECELERATION FROM 89.8 m/s TO ZERO, at up to -35.3 m/s^2, WITH NO BRAKING
# SOUND AVAILABLE TO IT. A car film with no brakes has no way to express
# deceleration, and 14.8% of this film's world grid is under -3 m/s^2.
#
# (Downshift/gearshift is the engine workflow's, in `gear_and_rpm`. Flagged,
# not built here.)

def roughness_profile(n_space, w=2.2, seed=0, k0=1.0):
    """A SPATIAL roughness profile with a power-law spectrum S(k) ~ k^-w.

    THE THIRD MECHANISM FOR CONTINUOUS CONTACT. A scrape, a rub or a slide is
    not a filter setting -- it is a stylus reading a surface. Build the surface
    once, in SPACE, then read it at s(t) = integral of v dt: speed then changes
    the pitch AND the brightness together, for free and with no resampling
    artefact anywhere, because nothing is being resampled. w = 2.2 for asphalt,
    2.5 for glass on concrete.
    """
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n_space)
    X = np.fft.rfft(x)
    k = np.maximum(np.arange(X.shape[0], dtype=np.float64), k0)
    X *= k ** (-w / 2.0)
    z = np.fft.irfft(X, n=n_space)
    s = float(np.std(z))
    return z / s if s > 0 else z


def read_roughness(profile, v, sr, ds, cyclic=True):
    """Read a spatial profile at s(t) = integral v dt. Linear interpolation is
    correct here: the profile IS the signal, and reading it at a varying rate is
    exactly what the physical contact does."""
    v = np.asarray(v, dtype=np.float64)
    s = np.cumsum(np.maximum(v, 0.0)) / sr
    idx = s / ds
    n_sp = profile.shape[0]
    if cyclic:
        idx = np.mod(idx, n_sp - 1)
    else:
        idx = np.clip(idx, 0, n_sp - 2)
    i0 = idx.astype(np.int64)
    fr = idx - i0
    return profile[i0] * (1.0 - fr) + profile[i0 + 1] * fr


def brakes(v, decel, sr, seed=9001, r_wheel=0.36, r_disc=0.139):
    """CARBON-CARBON BRAKES. Rubbing tone, disc bell modes, and judder.

    Three parts, all gated on the telemetry's own deceleration:

      * RUBBING. The pad reads the disc's surface, and a disc is a CLOSED
        surface: the profile repeats once per revolution, which is what gives
        braking its characteristic once-per-rev grain and is why brake noise
        wobbles rather than hisses. Read at the rubbing speed omega * r_disc,
        so both the pitch and the brightness of the rub fall as the car slows,
        with no filter sweep involved.
      * DISC BELL MODES. A 278 mm carbon-carbon disc rings at 1.5-4 kHz. Those
        modes are excited by the rub, which is why a squealing brake is a TONE
        on top of a rush and not a louder rush.
      * JUDDER. Disc thickness variation forces the caliper at the wheel
        rotation rate and its first harmonics -- 36.7 Hz at 83 m/s, falling to
        nothing at the stop. Low Q, because a caliper is not a bell.
    """
    n = v.shape[0]
    v = np.maximum(np.asarray(v, dtype=np.float64), 0.0)
    press = dsp.onepole_lag(np.clip(np.asarray(decel) / -9.81, 0.0, 4.0) / 3.6, 0.02, sr)
    press = np.clip(press, 0.0, 1.2)
    if float(press.max()) < 1e-4:
        return np.zeros(n, dtype=np.float32), {"active": False}
    f_wheel = v / (2.0 * np.pi * r_wheel)
    v_rub = f_wheel * 2.0 * np.pi * r_disc

    # ---- rubbing: one disc circumference of surface, read cyclically -------
    circ = 2.0 * np.pi * r_disc
    ds = 2.5e-5                                     # 25 um of disc surface
    prof = roughness_profile(int(circ / ds), w=2.0, seed=seed)
    rub = read_roughness(prof, v_rub, sr, ds)
    rub = rub * press

    # ---- disc bell modes, excited by the rub ------------------------------
    out = np.zeros(n)
    disc_modes = []
    rng = np.random.default_rng(seed + 1)
    for k in range(5):
        f = float(1500.0 + 625.0 * k) * float(rng.uniform(0.95, 1.05))
        q = float(rng.uniform(55.0, 120.0))
        disc_modes.append((f, q))
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al])
        a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        out += (0.8 ** k) * _sig.lfilter(b / a[0], a / a[0], rub)
    # R2-4058: THE DISC MODES ARE THE SIGNAL; THE RAW RUB IS THE FLOOR. Measured
    # on the R2-4056 stems, this bus came out at a 225 Hz centroid over the whole
    # film -- for a layer whose entire content is supposed to live at 1.5-4 kHz.
    # The spatial profile read at speed has an f^-2 temporal spectrum, so mixing
    # it in at 0.35 buried the resonators it was there to excite.
    out = out * 1.0 + rub * 0.12

    # ---- judder: caliper forced at wheel rotation harmonics ---------------
    jud = np.zeros(n)
    for h, amp in ((1.0, 1.0), (2.0, 0.45), (3.0, 0.22)):
        jud += amp * _noisy_oscillator(np.clip(f_wheel * h, 0.5, sr * 0.4),
                                       sr, seed + 20 + int(h), jitter=0.02)
    jud = dsp.lp(jud, 400.0, sr, 2) * press
    # judder is a caliper being shaken, not the sound of braking: it is a
    # texture under the rub, and at 0.30 it WAS the layer
    out += jud * 0.12

    out = _sig.sosfilt(_sig.butter(2, 140.0, btype="highpass", fs=sr, output="sos"), out)
    info = {"active": True,
            "disc_radius_m": r_disc, "wheel_radius_m": r_wheel,
            "peak_wheel_rotation_hz": float(f_wheel.max()),
            "disc_modes_hz_q": [[float(f), float(q)] for f, q in disc_modes],
            "profile_samples": int(prof.shape[0]),
            "profile_spatial_period_m": float(circ),
            "active_fraction": float((press > 0.02).mean())}
    return out.astype(np.float32), info


def suspension(v, accel_long, accel_lat, surf, sr, seed=9101):
    """DAMPERS, UPRIGHTS AND KERB STRIKES, as a two-stage contact.

    A wheel hitting something is not one sound. It is:

      1. A RUBBER-MEDIATED CONTACT. The tyre is between the road and the car,
         so the first stage is a soft contact, T = 3-15 ms, which by
         `hertz_spectrum` puts the excitation's corner at 65-330 Hz -- a thump
         with nothing above about 100 Hz in it. That softness is why a kerb
         strike sounds nothing like a stone hitting the floor.
      2. STRUCTURE-BORNE RING of the upright and wishbones once that thump
         reaches them: beam modes from 100 Hz to 2 kHz at eta ~ 1e-2.

    Plus the heavily damped 1.5-4 Hz body mode, which does not radiate but does
    modulate every load-dependent layer above it.
    """
    n = v.shape[0]
    rng = np.random.default_rng(seed)
    # load transfer events: sharp changes in either acceleration
    jerk = np.abs(np.diff(np.asarray(accel_long, dtype=np.float64), prepend=0.0)) \
        + np.abs(np.diff(np.asarray(accel_lat, dtype=np.float64), prepend=0.0))
    jerk = dsp.onepole_lag(jerk, 0.002, sr)
    thr = float(np.percentile(jerk, 99.5))
    if thr <= 0:
        return np.zeros(n, dtype=np.float32), {"events": 0}
    hits = np.flatnonzero((jerk > thr) & (np.asarray(v) > 5.0))
    if hits.size:
        keep = [int(hits[0])]
        for i in hits[1:]:
            if i - keep[-1] > int(0.08 * sr):
                keep.append(int(i))
        hits = np.array(keep)
    out = np.zeros(n)
    # the upright/wishbone bank: a steel upright and two carbon wishbones
    f_up = np.array([118.0, 274.0, 430.0, 690.0, 1150.0, 1780.0])
    tau_up = 100.0 / (np.pi * f_up)                      # eta = 1e-2, Q = 100
    for i in hits:
        t_soft = float(rng.uniform(3e-3, 15e-3))
        L = int(0.35 * sr)
        if i + L >= n:
            continue
        tt = np.arange(L) / sr
        amp = hertz_spectrum(f_up, t_soft) * rng.uniform(0.7, 1.3, f_up.size)
        s = np.zeros(L)
        for j in range(f_up.size):
            s += amp[j] * np.sin(2 * np.pi * f_up[j] * tt + rng.uniform(0, 6.28)) \
                * np.exp(-tt / tau_up[j])
        # stage 1: the rubber-mediated thump itself
        s += _accel_noise(sr, t_soft, 0.8 * float(amp.sum()), L)
        g = float(np.clip(jerk[i] / thr, 0.5, 4.0))
        pk = float(np.abs(s).max())
        if pk > 0:
            out[i:i + L] += s / pk * 0.5 * g
    # 1.5-4 Hz body mode: does not radiate, but is reported because it is the
    # modulator the load-dependent layers should be riding
    body_hz = 2.4
    out = _sig.sosfilt(_sig.butter(2, 60.0, btype="highpass", fs=sr, output="sos"), out)
    return out.astype(np.float32), {
        "events": int(hits.size), "upright_modes_hz": [float(f) for f in f_up],
        "upright_q": 100.0, "contact_time_ms": [3.0, 15.0],
        "body_mode_hz": body_hz}


def scrape(v, gate, sr, w=2.5, seed=9201, span_m=6.0, modes=(820.0, 1470.0, 2310.0)):
    """CONTINUOUS CONTACT: a stylus reading a surface, through a modal bank.

    §3.3 item 4. Used for debris sliding on concrete after it stops bouncing --
    real debris SLIDES after it bounces, and the shard field in the delivered
    master stopped dead. Speed changes pitch and brightness together because the
    profile is read faster, which is what actually happens.
    """
    n = v.shape[0]
    ds = 2.0e-5
    prof = roughness_profile(int(span_m / ds), w=w, seed=seed)
    x = read_roughness(prof, np.asarray(v, dtype=np.float64), sr, ds) * np.asarray(gate)
    out = np.zeros(n)
    for k, f in enumerate(modes):
        q = 30.0
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al])
        a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        out += (0.7 ** k) * _sig.lfilter(b / a[0], a / a[0], x)
    return out.astype(np.float32), {"exponent_w": w, "modes_hz": list(modes),
                                    "span_m": span_m}


def impact_event(t_world, t_impact, sr, v_contact, seed=606,
                 pane=(2.125, 5.600), strike=(1.0625, 2.9)):
    """THE MOMENT OF CONTACT, AS FIVE LAYERS OFFSET BY PHYSICAL DELAYS (R2-4043).

    t=0 is contact. Every layer below is placed by r/c, not by taste.

      1. FRACTURE RIP        crack impulses scattered across the crack-front
                             sweep. NOT instantaneous: a crack tip runs at
                             0.5-0.6 c_R = 1716 m/s, so the 2.125 m short span
                             takes 1.24 ms and the 5.6 m long span 3.26 ms.
                             3-7 kHz core, the documented glass-shatter band.
      2. PANE MODAL COLLAPSE the full `plate_modes` bank driven through
                             `struck_plate` by a Hertzian POINT load at the
                             strike position, gated off 40 ms after contact
                             when the pane stops existing. 1-18 kHz.
      3. DELAYED FLEXURAL    a damped low waveform at +50-100 ms, ~200 Hz. A
                             real and distinctive feature of glass breakage,
                             and one this file did not have at all.
      4. (shard shower -- `render_shards`)
      5. (debris bed -- `debris_bed`)

    THE SUB LAYER STAYS, AT ITS PROPER LEVEL. The 41/58/79 Hz thud is the felt
    weight of a car arriving and it is kept, but it was 87% of the beat, and
    with the chain's 30 Hz high-pass in front of it and layers 1-3 above it, it
    is now the floor of the event rather than the event.
    """
    n = t_world.shape[0]
    t0 = float(t_world[0])
    i = int((t_impact - t0) * sr)
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(seed)
    if not (0 <= i < n - int(3.0 * sr)):
        return out.astype(np.float32), {}
    a_pane, b_pane = float(pane[0]), float(pane[1])
    x0, y0 = float(strike[0]), float(strike[1])
    info = {}

    # ---- (1) FRACTURE RIP -------------------------------------------------
    # The crack front sweeps out from the strike point. Scatter one crack
    # impulse per fracture site, delayed by its own distance / 1716 m/s, so the
    # rip has a DURATION set by the pane's size and the material's wave speed.
    # A single wideband burst -- which is what the old `ini` layer was -- has no
    # size information in it at all and reads as a click rather than as a sheet
    # of glass 5.6 m across letting go.
    nsite = 420
    sx = rng.uniform(0.0, a_pane, nsite)
    sy = rng.uniform(0.0, b_pane, nsite)
    dly = np.hypot(sx - x0, sy - y0) / CRACK_TIP_SPEED
    Lr = int((float(dly.max()) + 0.030) * sr)
    rip = np.zeros(Lr)
    idx = (dly * sr).astype(int)
    # amplitude falls as the front runs out of stored strain energy
    amp = np.exp(-dly / 0.0022) * rng.uniform(0.4, 1.0, nsite)
    np.add.at(rip, np.clip(idx, 0, Lr - 1), amp)
    rip = _sig.sosfilt(dsp.sos_band(3000.0, 7000.0, sr, 4), rip)
    rip *= np.exp(-np.arange(Lr) / sr / 0.012)
    out[i:i + Lr] += rip * 0.9
    info["crack_front_speed_ms"] = float(CRACK_TIP_SPEED)
    info["crack_sweep_short_span_ms"] = float(a_pane / CRACK_TIP_SPEED * 1e3)
    info["crack_sweep_long_span_ms"] = float(b_pane / CRACK_TIP_SPEED * 1e3)
    info["crack_sites"] = nsite

    # ---- (2) PANE MODAL COLLAPSE ------------------------------------------
    # The pane's own bank, struck at a point rather than pressed uniformly, and
    # gated off 40 ms after contact because by then there is no pane.
    modes = plate_modes(a_pane, b_pane, GLASS_H)
    coup = point_coupling(modes, x0, y0, a_pane, b_pane)
    # nose on glass: carbon against glass, a hard but not glass-on-glass
    # contact -> T = 0.25 ms, so the excitation is flat to ~4 kHz and rolls off
    # above it, which is what stops the 18 kHz modes being hit as hard as the
    # 200 Hz ones.
    T_NOSE = 2.5e-4
    force = hertz_force(sr, T_NOSE, amplitude=v_contact / 16.0)
    pane_ring = struck_plate(force, sr, modes, coup, keep=400, t60_max=1.2)
    # the pane stops existing 40 ms in: gate the ring off, do not fade it out
    gk = int(0.040 * sr)
    gate = np.ones(pane_ring.shape[0])
    if pane_ring.shape[0] > gk:
        gate[gk:] = np.exp(-(np.arange(pane_ring.shape[0] - gk) / sr) / 0.035)
    pane_ring = pane_ring * gate
    # normalise on the RMS of the first 100 ms rather than on the peak: a
    # 400-mode bank's peak is one sample of constructive interference and says
    # nothing about how loud the collapse is
    r0 = float(np.sqrt((pane_ring[:int(0.1 * sr)] ** 2).mean()))
    if r0 > 0:
        pane_ring = pane_ring / r0 * 0.55 * (v_contact / 16.0)
    Lp = min(pane_ring.shape[0], n - i)
    out[i:i + Lp] += pane_ring[:Lp]
    info["pane_modes_computed"] = len(modes)
    info["pane_modes_rendered"] = min(400, len(modes))
    info["pane_mode_max_hz"] = float(max(m[0] for m in modes))
    info["pane_contact_time_ms"] = T_NOSE * 1e3
    info["pane_gate_ms"] = 40.0

    # ---- (3) DELAYED FLEXURAL ---------------------------------------------
    # The pane bends before it breaks; the low bending wave arrives back some
    # tens of milliseconds later. ~200 Hz, heavily damped, at +65 ms.
    d3 = int(0.065 * sr)
    L3f = int(0.5 * sr)
    t3 = np.arange(L3f) / sr
    flex = (np.sin(2.0 * np.pi * 196.0 * t3) * np.exp(-t3 / 0.085)
            + 0.45 * np.sin(2.0 * np.pi * 231.0 * t3 + 0.9) * np.exp(-t3 / 0.06))
    flex *= 1.0 - np.exp(-t3 / 0.004)          # it arrives, it does not click on
    out[i + d3:i + d3 + L3f] += flex * 0.55 * (v_contact / 16.0)
    info["delayed_flexural_ms"] = 65.0
    info["delayed_flexural_hz"] = [196.0, 231.0]

    # ---- the sub layer: felt weight, AND ONLY THAT ------------------------
    # This layer was 87% of beat 3. It is the weight of a car arriving and it
    # belongs in the film, but at 0.85 it WAS the film: the impact bus measured
    # 77.1% of its energy below 100 Hz, a spectral centroid of 79 Hz, and a
    # 50 ms crest of 4.4 dB -- less peaky than white noise, for the sharpest
    # event in the picture. 0.22 puts it under the collapse instead of over it.
    L = int(1.2 * sr); tt = np.arange(L) / sr
    thud = np.zeros(L)
    for f, a, d in ((41.0, 1.0, 0.35), (58.0, 0.7, 0.28), (79.0, 0.45, 0.20)):
        thud += a * np.sin(2.0 * np.pi * f * tt) * np.exp(-tt / d)
    # it must ARRIVE, not fade up: 1.5 ms of attack, so the sub has a transient
    thud *= 1.0 - np.exp(-tt / 0.0015)
    out[i:i + L] += thud * 0.22

    # ---- the mullion: free-free bending of an aluminium extrusion, L = 5.6 m
    #     f_k = (beta_k L)^2 / (2 pi L^2) * sqrt(EI/(rho A)); using an
    #     equivalent radius of gyration of 0.055 m for a 200x60 box section.
    #     The physics here was already right (implied Q = 89, correctly
    #     joint-dominated for a bolted extrusion) and is KEPT. One fix: the
    #     higher modes decayed by an ad-hoc 1/(k+1)^0.6, which is not a damping
    #     law. A single loss factor eta gives tau_k = 1/(pi eta f_k), so higher
    #     modes die faster because they are higher, not because of an exponent.
    Lm, kg = 5.6, 0.055
    cbar = np.sqrt(69.0e9 / 2700.0)                       # 5055 m/s
    betas = (4.730, 7.853, 10.996, 14.137)
    eta_mull = 1.0 / 89.0
    L2 = int(2.6 * sr); t2 = np.arange(L2) / sr
    mull = np.zeros(L2)
    mull_f = []
    for k, be in enumerate(betas):
        f = (be ** 2) / (2.0 * np.pi * Lm ** 2) * kg * cbar
        mull_f.append(float(f))
        tau = 1.0 / (np.pi * eta_mull * f)
        mull += (0.75 ** k) * np.sin(2.0 * np.pi * f * t2) * np.exp(-t2 / tau)
    out[i:i + L2] += mull * 0.30

    # ---- the framing letting go -------------------------------------------
    L3 = int(0.75 * sr)
    cr = dsp.brown(L3, seed + 1, 20.0, sr) * np.exp(-np.arange(L3) / sr / 0.10)
    cr = _sig.sosfilt(dsp.sos_band(90.0, 3200.0, sr, 4), cr)
    out[i:i + L3] += cr * 2.2 * (v_contact / 16.0)

    # ---- dust -------------------------------------------------------------
    L4 = int(2.4 * sr); t4 = np.arange(L4) / sr
    dust = dsp.pink(L4, seed + 2, sr) * (t4 / 0.25 * np.exp(1.0 - t4 / 0.25))
    dust = _sig.sosfilt(dsp.sos_band(180.0, 5200.0, sr, 2), dust)
    out[i:i + L4] += dust * 0.35

    info["mullion_modes_hz"] = mull_f
    info["mullion_loss_factor"] = eta_mull
    info["thud_hz"] = [41.0, 58.0, 79.0]
    info["strike_point_m"] = [x0, y0]
    return out.astype(np.float32), info


def debris_bed(n, sr, onset_t, sizes, seed=20260814, fines_per_contact=140,
               tau_sys=0.9, amp_sigma=0.45, amp_clip_q=1.0,
               res_hz=(3000.0, 8000.0), n_res=5):
    """LAYER 5: THE PhISEM BED -- the thousands of pieces you do not integrate.

    A 12 mm architectural pane does not break into 351 pieces. The ballistic sim
    integrates the ~200 foreground fragments whose individual trajectories are
    worth having, and everything below that is a STOCHASTIC PARTICLE SYSTEM:
    Cook's PhISEM, in which a population of colliding particles excites a small
    resonator bank at a rate that decays as the system loses energy.

    That is what supplies DENSITY. The delivered master had 5-13.5 onsets/s in
    the 1-4 kHz band; auditory fusion into a continuous texture needs more than
    20-30/s and the peak of a real shower is several hundred. Inflating the
    shard count instead would multiply the expensive path by thirty to buy the
    same percept, and would put the fines' individual pitches into a band where
    a listener cannot resolve them anyway.

    The event rate is NOT a drawn curve: it is the ballistic sim's own contact
    schedule, in film time, multiplied by `fines_per_contact`. So the bed
    thickens and thins exactly where the shower does, including the stretch the
    world-time ramp puts on it, without a second timing model to keep in sync.

    Resonators: 3-8 kHz, Q 20-60, which is the measured range for sub-centimetre
    glass on concrete -- short enough to read as noise-like grain, long enough to
    keep the glassiness.
    """
    rng = np.random.default_rng(seed)
    onset_t = np.asarray(onset_t, dtype=np.float64)
    if onset_t.size == 0:
        return np.zeros(n, dtype=np.float32), {}
    t0, t1 = float(onset_t.min()), float(onset_t.max()) + 2.0
    # intensity: the contact schedule, smoothed, times the fines multiplier
    dt = 0.02
    bins = np.arange(t0, t1 + dt, dt)
    hist, _ = np.histogram(onset_t, bins=bins)
    lam = hist / dt * float(fines_per_contact)
    lam = _sig.lfilter(*_onepole(0.05, dt), lam)
    # a settling tail: the system keeps losing energy after the last integrated
    # contact, which is what tau_sys is
    lam = np.maximum(lam, float(lam.max()) * 0.02 * np.exp(-(bins[:-1] - t0) / tau_sys))
    counts = rng.poisson(np.maximum(lam * dt, 0.0))
    total = int(counts.sum())
    if total == 0:
        return np.zeros(n, dtype=np.float32), {}
    # place the events
    idx = np.repeat(((bins[:-1] - 0.0) * sr).astype(np.int64), counts)
    idx = idx + rng.integers(0, max(int(dt * sr), 1), total)
    idx = idx[(idx >= 0) & (idx < n)]
    train = np.zeros(n)
    # a fine's collision impulse: momentum of a sub-cm piece, lognormal spread.
    #
    # R2-4057: BOTH OF THESE NUMBERS WERE RAISED BY MEASUREMENT, NOT BY EAR.
    # Stems from R2-4056 attribute the breach window bus by bus: the bed carried
    # 83.9% of ITS energy above 4 kHz -- by far the brightest thing in the beat
    # and the only bus with real top end -- while being only 3.82% of the beat's
    # total energy. The master's breach therefore came back at 2.80% above 4 kHz
    # against G2's 8%.
    #
    # The bed could not simply be turned up: the peak criterion had already
    # capped it (its LUFS target wanted +28.56 dB and the peak ceiling allowed
    # +24.55). What was wrong was its CREST, not its level -- a lognormal spread
    # of sigma 0.7 spends the bus's headroom on a handful of loud fines. Halving
    # the spread and raising the fines multiplier from 34 to 90 puts more energy
    # under the same peak, which is the only direction available once a bus is
    # peak-limited, and 90 fines per integrated fragment is closer to what a
    # 12 mm pane actually produces than 34 was.
    #
    # TRUNCATING THE TAIL WAS TRIED AND IT MADE THINGS WORSE. `amp_clip_q`
    # defaults to 1.0, i.e. off. The reasoning was sound -- a lognormal is
    # unbounded, no fragment population contains an arbitrarily large fine, and
    # once a bus is peak-limited its RMS-at-full-scale is the only currency
    # there is. On an isolated event train it bought 0.77 dB. On the real bed it
    # LOST 1.41 dB (RMS at peak 1.0: -21.55 -> -22.96 dB), because at 150,000
    # events over 9.5 s the resonators overlap so heavily that the bus's peak is
    # a sum of many events rather than the largest one: clipping the individual
    # amplitudes cuts the RMS and barely touches the peak. Kept as a parameter
    # with the measurement attached, rather than deleted, because the isolated
    # test that justified it is the kind that looks conclusive and is not.
    a_ev = rng.lognormal(0.0, float(amp_sigma), idx.shape[0])
    if 0.0 < amp_clip_q < 1.0 and a_ev.size:
        a_ev = np.minimum(a_ev, float(np.quantile(a_ev, amp_clip_q)))
    np.add.at(train, idx, a_ev)
    # excite the resonator bank ONCE with the whole train -- this is the reason
    # PhISEM is affordable: 40,000 events cost four biquads, not 40,000 syntheses
    span0 = max(int(t0 * sr) - sr // 10, 0)
    span1 = min(int(t1 * sr) + sr, n)
    seg = train[span0:span1]
    out = np.zeros(n)
    acc = np.zeros(seg.shape[0])
    res = []
    # THE BANK IS SPREAD DETERMINISTICALLY, NOT DRAWN. Five uniform draws over
    # 3-8 kHz is a lottery: with one seed 86.9% of the bed's energy landed above
    # 4 kHz and with another 98.4%, which is an 11.5 percentage-point swing in
    # the only bus that has a top end -- i.e. the breach's whole high-frequency
    # content depending on an RNG. Eight resonators evenly over 3.5-9 kHz (the
    # spec says 3-8; sub-centimetre glass on concrete sits at the top of that
    # and slightly above it), with Q still drawn over the stated 20-60.
    for _k in range(int(n_res)):
        f = float(res_hz[0] + (res_hz[1] - res_hz[0]) * (_k + 0.5) / int(n_res))
        q = float(rng.uniform(20.0, 60.0))
        res.append((f, q))
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al])
        a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        acc += _sig.lfilter(b / a[0], a / a[0], seg)
    out[span0:span1] = acc
    info = {"fines_events": int(idx.shape[0]),
            "fines_per_contact": float(fines_per_contact),
            "peak_rate_per_s": float(lam.max()),
            "resonators_hz_q": [[float(f), float(q)] for f, q in res],
            "tau_sys_s": float(tau_sys)}
    return out.astype(np.float32), info


def _onepole(tau_s, dt):
    a = float(np.exp(-dt / max(tau_s, 1e-6)))
    return np.array([1.0 - a]), np.array([1.0, -a])
