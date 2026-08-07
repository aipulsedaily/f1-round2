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

    # cavity resonance, 165 Hz, Q 12, excited by the road
    # the gas inside a hot tyre, not the air outside it
    f_cav = float(dsp.speed_of_sound(60.0)) / (2.0 * np.pi * 0.33)
    w0 = 2.0 * np.pi * f_cav / sr
    al = np.sin(w0) / (2.0 * 12.0)
    b = np.array([al, 0.0, -al]); a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
    cavity = _sig.lfilter(b / a[0], a / a[0], base) * 2.2

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

    # ---- slip: stick-slip squeal + smoke -----------------------------------
    slip = np.clip(st["slip"], 0.0, 1.0)
    slip_v = slip * v + np.clip(st["wheel_w"] * 0.36 - v, 0.0, None) * (slip > 0.02)
    sq_f = 900.0 + 260.0 * np.tanh(slip_v / 6.0)
    squeal = (np.sin(dsp.integrate_phase(sq_f, sr)) * 0.6
              + np.sin(dsp.integrate_phase(sq_f * 2.02, sr)) * 0.25
              + np.sin(dsp.integrate_phase(sq_f * 3.05, sr)) * 0.12)
    rough = 1.0 + 0.5 * dsp.lp(dsp.white(n, seed + 5), 60.0, sr, 2)
    smoke = dsp.bp(hiss, 700.0, 6000.0, sr, 4)
    sq_env = dsp.onepole_lag(np.clip(slip * 1.6, 0.0, 1.0), 0.02, sr)
    sig += (squeal * rough * 0.30 + smoke * 0.35) * sq_env

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
        "kerb_serration_pitch_m": pitch,
        "kerb_contact_fraction": float((surf["kerb"] > 0.05).mean()),
        "gravel_contact_fraction": float((surf["gravel"] > 0.05).mean()),
        "max_slip": float(slip.max()),
        "max_lateral_g": float(lat_g.max()),
        "surface_time_fraction": {k: float(surf[k].mean()) for k in surf},
    }
    return sig.astype(np.float32), info


# ================================================================== wind =====
def wind_at_camera(tau, cam_speed, inside, sr, seed=4242):
    """Wind at the LENS. Film clock, listener-attached, never propagated.

    This is the one layer that must NOT slow down at the breach: it is generated
    by the camera's own airspeed, and the camera keeps flying in real time.
    Level follows v^2.5 (turbulent pressure fluctuation on a bluff body scales
    between v^2 and v^3), and the spectrum has two parts: a low buffet whose
    corner rises with speed, and broadband edge hiss.
    """
    n = tau.shape[0]
    v = np.maximum(cam_speed, 0.0)
    amp = (v / 30.0) ** 2.5
    amp = dsp.onepole_lag(np.clip(amp, 0.0, 12.0), 0.15, sr)
    amp *= (1.0 - 0.93 * inside)          # a lens inside a building has no wind

    buffet = dsp.brown(n, seed, 4.0, sr)
    buffet = dsp.tv_onepole_lp(buffet, np.clip(18.0 + 1.6 * v, 15.0, 400.0), sr)
    edge = dsp.pink(n, seed + 1, sr)
    edge = dsp.tv_onepole_lp(edge, np.clip(700.0 + 45.0 * v, 400.0, 12000.0), sr)
    edge = edge - dsp.tv_onepole_lp(edge, 260.0, sr)
    # gusting: real airflow over a moving rig is not stationary
    gust = 1.0 + 0.55 * dsp.lp(dsp.white(n, seed + 2), 1.6, sr, 2) * 4.0
    gust = np.clip(gust, 0.15, 2.2)

    mono = (buffet * 2.2 + edge * 0.8) * amp * gust * 0.055
    # wind at a lens is not a subwoofer feed either
    mono = _sig.sosfilt(_sig.butter(2, 25.0, btype="highpass", fs=sr, output="sos"), mono)
    # two ears see slightly different turbulence: decorrelate, do not just copy
    d = int(0.0009 * sr)
    stereo = np.stack([mono, dsp.delay(mono, d) * 0.94 + mono * 0.06], axis=1)
    return stereo.astype(np.float32), {"peak_camera_airspeed_ms": float(v.max())}


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


def showroom_tail(excitation, spec, sr, rt60_low=2.4, rt60_high=0.85):
    """FDN tail sized from the showroom's own dimensions.

    Delay lengths are the room's principal acoustic paths -- edges, face
    diagonals, body diagonal -- so the tail's modal spacing is the room's, and
    a 30 x 22 x 6.5 m hall does not sound like a preset "large room".
    """
    ix, iy, iz = spec["showroom"]["interior_m"]
    d = [iz, iy * 0.5, ix * 0.5,
         np.hypot(ix, iy) * 0.5, np.hypot(iy, iz), np.hypot(ix, iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz)]
    d = sorted(float(x) for x in d)
    tail = dsp.fdn_reverb(excitation, sr, d, rt60_low, rt60_high,
                          c=float(dsp.speed_of_sound(20.0)))
    return tail, {"delays_m": d, "rt60_low_s": rt60_low, "rt60_high_s": rt60_high,
                  "volume_m3": float(ix * iy * iz)}


def room_tone(n, sr, seed=97):
    """The empty showroom before anything happens: HVAC, transformer hum, the
    building's own low rumble. Every component is a stated frequency."""
    t = np.arange(n) / sr
    hum = np.zeros(n)
    for k, a in ((50.0, 1.0), (100.0, 0.42), (150.0, 0.16), (250.0, 0.06)):
        hum += a * np.sin(2.0 * np.pi * k * t + k * 0.37)
    hum *= 1.0 + 0.04 * np.sin(2.0 * np.pi * 0.23 * t)
    air = dsp.bp(dsp.pink(n, seed, sr), 90.0, 2400.0, sr, 2)
    rumble = dsp.lp(dsp.brown(n, seed + 1, 6.0, sr), 60.0, sr, 2)
    return (hum * 0.0022 + air * 0.010 + rumble * 0.030).astype(np.float32)


# =========================================================== circuit ambience =
def outdoor_bed(n, sr, height, seed=311):
    """Diffuse open-air bed: wind in the treeline, distant plant, air.

    Non-directional by construction, because a diffuse field is. Gains a little
    more high wind and loses ground clutter as the camera climbs to 140 m.
    """
    h = np.clip(height / 60.0, 0.0, 1.0)
    trees = dsp.bp(dsp.pink(n, seed, sr), 300.0, 5000.0, sr, 2)
    trees *= 1.0 + 0.7 * dsp.lp(dsp.white(n, seed + 1), 0.6, sr, 2) * 6.0
    plant = dsp.bp(dsp.brown(n, seed + 2, 8.0, sr), 40.0, 260.0, sr, 2)
    lo = dsp.lp(dsp.brown(n, seed + 3, 4.0, sr), 40.0, sr, 2)
    # LOOKED AT THE SPECTROGRAM. At `lo * 0.05` the sub-40 Hz brown noise was
    # the brightest thing in the plot across the whole lap -- a rumble bed sitting
    # 20 dB over the engine below 100 Hz, inaudible as content and expensive in
    # headroom. Cut, and the whole bed high-passed at 22 Hz: a diffuse open-air
    # field has very little energy below the ear's own rolloff.
    bed = trees * (0.010 + 0.016 * h) + plant * 0.022 * (1.0 - 0.6 * h) + lo * 0.012
    bed = _sig.sosfilt(_sig.butter(2, 22.0, btype="highpass", fs=sr, output="sos"), bed)
    d = int(0.0031 * sr)
    return np.stack([bed, dsp.delay(bed, d)], axis=1).astype(np.float32)


def crowd(n, sr, excitement, seed=5150):
    """Grandstand babble. Many band-limited random envelopes summed, which is
    what a crowd is; `excitement` swells it as the car arrives."""
    voices = np.zeros(n)
    rng = np.random.default_rng(seed)
    for k in range(9):
        f0, f1 = 220.0 * (1.0 + 0.35 * k), 900.0 * (1.0 + 0.30 * k)
        v = dsp.bp(dsp.white(n, seed + 10 + k), f0, min(f1, sr * 0.4), sr, 2)
        env = np.abs(dsp.lp(dsp.white(n, seed + 40 + k), 2.0 + 1.6 * rng.random(), sr, 2))
        env /= max(float(env.max()), 1e-9)
        voices += v * (0.35 + 0.65 * env)
    voices /= 3.0
    cheer = dsp.bp(dsp.white(n, seed + 90), 700.0, 4500.0, sr, 2)
    return (voices * (0.35 + 0.65 * excitement) + cheer * excitement * 0.55).astype(np.float32)


def fence_buzz(n, sr, proximity, speed, seed=771):
    """Catch fencing and gantry signage resonating as the pressure wave of a
    300 km/h car goes past. Structural, and only near the car."""
    exc = np.clip(proximity, 0.0, 1.0) * np.clip(speed / 60.0, 0.0, 1.5)
    src = dsp.white(n, seed)
    out = np.zeros(n)
    for f, q, a in ((78.0, 22.0, 1.0), (163.0, 26.0, 0.7), (247.0, 30.0, 0.45),
                    (410.0, 34.0, 0.28), (712.0, 28.0, 0.18)):
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); aa = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        out += a * _sig.lfilter(b / aa[0], aa / aa[0], src)
    return (out * exc * 0.020).astype(np.float32)


# ========================================================== structure/glass ==
def plate_modes(a, b, h, e=GLASS_E, nu=GLASS_NU, rho=GLASS_RHO, fmax=1600.0):
    """Simply-supported rectangular plate: f_mn = (pi/2) sqrt(D/(rho h)) (m^2/a^2 + n^2/b^2).

    For the showroom's 2.125 x 5.600 m, 12 mm glazing this puts the fundamental
    at 7.5 Hz and a dense audible set from ~100 Hz up. Those are the frequencies
    a big pane actually buzzes at, and they are computed here from E, nu, rho and
    thickness rather than picked.
    """
    D = e * h ** 3 / (12.0 * (1.0 - nu ** 2))
    k = (np.pi / 2.0) * np.sqrt(D / (rho * h))
    out = []
    for m in range(1, 26):
        for nn in range(1, 26):
            f = k * ((m / a) ** 2 + (nn / b) ** 2)
            if f <= fmax:
                # a uniform acoustic pressure couples only to odd-odd modes
                w = 1.0 / (m * nn) if (m % 2 and nn % 2) else 0.18 / (m * nn)
                out.append((float(f), float(w)))
    out.sort()
    return out


def glass_wall(excitation, sr, modes, gate, q=45.0, keep=72):
    """Drive the pane's modes with the acoustic pressure reaching the wall.

    Only the `keep` most strongly coupled modes are rendered, and only over the
    span where the gate is actually open: the pane exists for 36 s of the film
    and stops existing 40 ms after the nose reaches it, so running 351 second-
    order sections over the whole 120 s buffer would be 97 % wasted work.
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
    fc_crit = float(dsp.speed_of_sound(18.0)) ** 2 / (1.8 * GLASS_CL * GLASS_H)
    def _rad(f):
        return min(1.0, (f / fc_crit) ** 2)
    sel = sorted([m for m in modes if 20.0 < m[0] < sr * 0.45],
                 key=lambda m: -(m[1] * _rad(m[0])))[:keep]
    acc = np.zeros(b0 - a0)
    for f, w in sel:
        w0 = 2.0 * np.pi * f / sr
        al = np.sin(w0) / (2.0 * q)
        b = np.array([al, 0.0, -al]); a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
        acc += w * _sig.lfilter(b / a[0], a / a[0], x)
    out[a0:b0] = acc
    return out.astype(np.float32)


# ================================================================= assembly ==
def assembly(t_world, clusters, sr, launch_film_t, fps=24, seed=1234):
    """Beat 1: servo whir plus one impact per cluster arrival.

    Arrival times are the ACTUAL seat frames from `world/beat1_anim_anim.json`;
    each impact's pitch comes from the cluster's own bounding-box volume from
    `docs/explode_plan.json`, used as a mass proxy, so a 5.47 m monocoque lands
    an octave and a half below a steering wheel.
    """
    n = t_world.shape[0]
    rng = np.random.default_rng(seed)
    out = np.zeros(n, dtype=np.float64)
    ev = []
    t0 = float(t_world[0])
    for name, c in clusters.items():
        seat_f = int(c["seat_frame"])
        last_f = int(c.get("last_land", seat_f))
        vol = float(c["size"][0] * c["size"][1] * c["size"][2])
        # a plate/shell's ring frequency falls as its linear size grows
        f0 = 210.0 / max(vol, 0.02) ** (1.0 / 3.0)
        f0 = float(np.clip(f0, 55.0, 900.0))
        nparts = int(c["n_parts"])
        for p in range(nparts):
            fr = seat_f + (last_f - seat_f) * (p / max(nparts - 1, 1))
            wt = (fr - 1) / fps - launch_film_t
            i = int((wt - t0) * sr)
            if not (0 <= i < n - int(0.9 * sr)):
                continue
            fp = f0 * float(rng.uniform(0.82, 1.9))
            dur = float(np.clip(0.55 * (f0 / max(fp, 1.0)), 0.05, 0.9))
            L = int(dur * sr)
            tt = np.arange(L) / sr
            env = np.exp(-tt / (dur * 0.28))
            hit = np.zeros(L)
            for k, amp in ((1.0, 1.0), (2.31, 0.45), (3.87, 0.22), (6.1, 0.10)):
                hit += amp * np.sin(2.0 * np.pi * fp * k * tt) * np.exp(-tt / (dur * 0.28 / k ** 0.5))
            click = rng.standard_normal(L) * np.exp(-tt / 0.004)
            g = 0.30 * (vol ** 0.30) / max(nparts, 1) ** 0.35
            out[i:i + L] += (hit * env + click * 0.5) * g
            ev.append((name, fr, float(fp)))
    out = _sig.sosfilt(dsp.sos_band(45.0, 9000.0, sr, 2), out)

    # servo whir while parts are in flight (frames 1..792)
    fly = ((t_world + launch_film_t) * fps >= 1) & ((t_world + launch_film_t) * fps <= 800)
    f_srv = 320.0 + 90.0 * np.sin(2.0 * np.pi * 0.11 * t_world)
    srv = (np.sin(dsp.integrate_phase(f_srv, sr)) * 0.5
           + np.sin(dsp.integrate_phase(f_srv * 2.7, sr)) * 0.2
           + dsp.bp(dsp.white(n, seed + 1), 900.0, 6000.0, sr, 2) * 0.6)
    out += srv * fly * 0.012
    return out.astype(np.float32), {"impacts": len(ev), "clusters": len(clusters)}


# =================================================================== breach ==
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
    for p0, v0, L, m in shards:
        f1 = 0.47 * (GLASS_H / (L * L)) * GLASS_CL
        freqs = np.array([f1, f1 * 2.08, f1 * 3.41])
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
                amp = m * vz_in
                decay = float(np.clip(0.05 + 0.55 * L, 0.03, 0.45)) * (0.6 ** bounce)
                events.append((t, p.copy(), freqs, amp, decay))
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


def render_shards(events, t_world, t_impact, sr, groups=4):
    """Render the contact events into `groups` spatial buckets on the WORLD grid.

    Bucketing is by world Y so the shard field has real width at the ears rather
    than collapsing to a point. Each bucket returns (signal, centroid position).
    """
    n = t_world.shape[0]
    t0 = float(t_world[0])
    ys = np.array([e[1][1] for e in events]) if events else np.zeros(1)
    edges = np.quantile(ys, np.linspace(0.0, 1.0, groups + 1))
    edges[0] -= 1.0; edges[-1] += 1.0
    sigs = [np.zeros(n, dtype=np.float64) for _ in range(groups)]
    cents = [np.zeros(3) for _ in range(groups)]
    counts = [0] * groups
    for (t, p, freqs, amp, decay) in events:
        gi = int(np.clip(np.searchsorted(edges, p[1]) - 1, 0, groups - 1))
        i = int((t_impact + t - t0) * sr)
        L = int(min(decay * 6.0, 1.5) * sr)
        if i < 0 or i + L >= n or L < 8:
            continue
        tt = np.arange(L) / sr
        env = np.exp(-tt / max(decay, 1e-3))
        s = np.zeros(L)
        for k, f in enumerate(freqs):
            if f >= sr * 0.45:
                continue
            s += (0.8 ** k) * np.sin(2.0 * np.pi * f * tt + k * 1.1) * env
        s[:max(int(0.0004 * sr), 2)] += 0.6 * env[:max(int(0.0004 * sr), 2)]
        sigs[gi][i:i + L] += s * amp * 6.0
        cents[gi] += p
        counts[gi] += 1
    for gi in range(groups):
        if counts[gi]:
            cents[gi] /= counts[gi]
        else:
            cents[gi] = np.array([15.0, 0.0, 1.0])
    return [(s.astype(np.float32), c) for s, c in zip(sigs, cents)]


def impact_event(t_world, t_impact, sr, v_contact, seed=606):
    """The moment of contact: laminated pane, aluminium mullion, structure, dust.

    (a) low thud     -- the pane's own low modes slammed, 40-80 Hz, fast decay
    (b) mullion      -- a 5.6 m aluminium extrusion's bending modes, struck
    (c) crunch       -- filtered brown-noise burst, the framing letting go
    (d) dust         -- a slow filtered whoosh, the concrete dust cloud
    """
    n = t_world.shape[0]
    t0 = float(t_world[0])
    i = int((t_impact - t0) * sr)
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(seed)
    if not (0 <= i < n - int(3.0 * sr)):
        return out.astype(np.float32), {}

    # (a) thud
    L = int(1.2 * sr); tt = np.arange(L) / sr
    thud = np.zeros(L)
    for f, a, d in ((41.0, 1.0, 0.35), (58.0, 0.7, 0.28), (79.0, 0.45, 0.20)):
        thud += a * np.sin(2.0 * np.pi * f * tt) * np.exp(-tt / d)
    out[i:i + L] += thud * 0.85

    # (b) mullion: free-free bending of an aluminium extrusion, L = 5.6 m
    #     f_k = (beta_k L)^2 / (2 pi L^2) * sqrt(EI/(rho A)); using an
    #     equivalent radius of gyration of 0.055 m for a 200x60 box section.
    Lm, kg = 5.6, 0.055
    cbar = np.sqrt(69.0e9 / 2700.0)                       # 5055 m/s
    betas = (4.730, 7.853, 10.996, 14.137)
    L2 = int(2.6 * sr); t2 = np.arange(L2) / sr
    mull = np.zeros(L2)
    for k, be in enumerate(betas):
        f = (be ** 2) / (2.0 * np.pi * Lm ** 2) * kg * cbar
        mull += (0.75 ** k) * np.sin(2.0 * np.pi * f * t2) * np.exp(-t2 / (0.9 / (k + 1) ** 0.6))
    out[i:i + L2] += mull * 0.30

    # (c) crunch
    L3 = int(0.75 * sr)
    cr = dsp.brown(L3, seed + 1, 20.0, sr) * np.exp(-np.arange(L3) / sr / 0.10)
    cr = _sig.sosfilt(dsp.sos_band(90.0, 3200.0, sr, 4), cr)
    out[i:i + L3] += cr * 2.2 * (v_contact / 16.0)

    # (d) dust
    L4 = int(2.4 * sr); t4 = np.arange(L4) / sr
    dust = dsp.pink(L4, seed + 2, sr) * (t4 / 0.25 * np.exp(1.0 - t4 / 0.25))
    dust = _sig.sosfilt(dsp.sos_band(180.0, 5200.0, sr, 2), dust)
    out[i:i + L4] += dust * 0.35

    # the fracture initiation itself: a very short, very wide crack
    L5 = int(0.03 * sr)
    ini = rng.standard_normal(L5) * np.exp(-np.arange(L5) / sr / 0.0035)
    ini = _sig.sosfilt(dsp.sos_band(600.0, 16000.0, sr, 4), ini)
    out[i:i + L5] += ini * 1.4

    return out.astype(np.float32), {
        "mullion_modes_hz": [float((b ** 2) / (2.0 * np.pi * Lm ** 2) * kg * cbar) for b in betas],
        "thud_hz": [41.0, 58.0, 79.0],
    }
