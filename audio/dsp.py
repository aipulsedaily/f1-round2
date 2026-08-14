"""Signal primitives. Everything here is generated; nothing is loaded.

There is deliberately no file-reading code anywhere in this module. The only
inputs are numbers.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _sig

# --------------------------------------------------------------- oscillators --


def integrate_phase(freq, sr, phase0=0.0):
    """Continuous phase from an instantaneous-frequency array.

    Regenerating sin(2*pi*f*t) per block with a changing f restarts the phase at
    every block boundary and clicks. Everything oscillating in this project
    integrates instead. float64 throughout: a float32 cumsum over 11.9 M samples
    loses the low bits of the phase and detunes the top harmonics audibly.
    """
    f = np.asarray(freq, dtype=np.float64)
    ph = np.cumsum(f) * (2.0 * np.pi / sr)
    return ph + (phase0 - (2.0 * np.pi * f[0] / sr))


def osc(freq, sr, phase0=0.0, kind="sin"):
    ph = integrate_phase(freq, sr, phase0)
    if kind == "sin":
        return np.sin(ph, dtype=np.float64).astype(np.float32)
    if kind == "cos":
        return np.cos(ph, dtype=np.float64).astype(np.float32)
    raise ValueError(kind)


def phase_pulse(phase, width):
    """A periodic pulse from a running phase: one narrow bump per 2*pi.

    Used for the exhaust firing events, where the pulse must stay locked to the
    crank angle even while the crank speed is changing.

    NOTE: this is a RAISED COSINE, and it is kept only for the layers that want a
    soft bump. It is the wrong shape for a combustion event and was the first
    cause of R2-1401 -- see `blowdown_pulse` below for why.
    """
    u = np.mod(phase, 2.0 * np.pi) / (2.0 * np.pi)
    w = max(float(width), 1e-6)
    return np.where(u < w, 0.5 * (1.0 - np.cos(2.0 * np.pi * u / w)), 0.0).astype(np.float32)


def blowdown_pulse(phase, width, attack_frac):
    """An exhaust BLOWDOWN event: steep front, exponential decay (R2-1401).

    WHY THE RAISED COSINE HAD TO GO. `phase_pulse` is C1-continuous, so its
    spectrum rolls off at -18 dB/octave above 1/w. At 12,000 rpm the old call --
    width 0.055 of the 720-degree cycle, i.e. 550 us -- put that corner at about
    1.8 kHz, so the combustion excitation itself had NOTHING to give the pipe
    above 2 kHz. Measured on the shipped master: the harmonic-to-noise ratio
    above 2.6 kHz was -0.65 dB, i.e. the top four octaves of an F1 car were
    broadband noise with no harmonic content whatsoever. That is the client's
    "hair blower" in one number, and no amount of re-balancing could have fixed
    it, because there were no harmonics up there to un-bury.

    WHAT A BLOWDOWN ACTUALLY IS. The exhaust valve cracks open against 8-12 bar
    of cylinder pressure. Flow goes choked essentially at once, so the pressure
    at the valve rises in a near-step -- a real blowdown front is a weak shock --
    and then decays roughly exponentially as the cylinder empties, before the
    piston pushes the remainder out. The energy in the FRONT is what makes an
    engine bright; a symmetric bump has no front.

    So: a raised-cosine rise over `attack_frac` of the pulse, then an exponential
    decay, tapered back to zero at the end of the pulse. The rise stays
    C1-continuous, which caps the roll-off at -18 dB/oct ABOVE ITS OWN corner
    -- but that corner is now at 1/(attack_frac*w) instead of 1/w, which at
    attack_frac 0.10 is a decade higher. The pulse still starts and ends at zero
    with zero slope, so it does not alias: at 14,400 rpm (f0 = 720 Hz) the 66th
    harmonic sits at Nyquist and is already 60+ dB down.

    `attack_frac` is the LOAD KNOB. Higher cylinder pressure at valve opening
    means a more violent blowdown and a steeper front, so this is driven from
    throttle in engine.py rather than being a constant. It is the mechanism by
    which the engine gets harder under power and thins off-throttle, which a
    gain envelope alone cannot do -- a fan that changes speed is a hair dryer.

    phase: running phase, one pulse per 2*pi.
    width: pulse duration as a fraction of the period.
    attack_frac: rise time as a fraction of `width`. Scalar or per-sample.
    """
    u = np.mod(np.asarray(phase, dtype=np.float64), 2.0 * np.pi) / (2.0 * np.pi)
    w = max(float(width), 1e-6)
    a = np.clip(np.asarray(attack_frac, dtype=np.float64), 0.02, 0.60) * w
    x = np.clip(u / w, 0.0, 1.0)                     # 0..1 inside the pulse
    rise = 0.5 * (1.0 - np.cos(np.pi * np.minimum(x / np.maximum(a / w, 1e-9), 1.0)))
    # exponential blowdown from the peak, and a C1 taper that lands it on zero
    d = np.clip((x - a / w) / np.maximum(1.0 - a / w, 1e-9), 0.0, 1.0)
    decay = np.exp(-3.4 * d) * (0.5 * (1.0 + np.cos(np.pi * d)))
    y = np.where(x < a / w, rise, decay)
    return np.where(u < w, y, 0.0).astype(np.float32)


def comb_pipe(x, delay_samples, loop_gain, damp_hz, sr, invert=False, blk=None):
    """A PIPE as a bidirectional delay line, not as a bank of tuned resonators.

    THE SECOND CAUSE OF R2-1401. The exhaust used to be synthesised as a sum of
    2-pole bandpasses placed on the pipes' computed mode frequencies -- four
    orders for each primary, five for the collector, three for the tailpipe. That
    is modal synthesis with the series TRUNCATED, and the highest term in it was
    1,936 Hz. Everything the film had above 2 kHz therefore came from noise
    generators, by construction: the harmonic path physically stopped there.

    A pipe does not have four modes. It has as many as fit under Nyquist, at
    exact integer spacing, with a Q that FALLS with frequency because the open
    end radiates high frequencies far more efficiently than low ones. All three
    of those facts come out of a delay line for free:

        y[n] = x[n] +/- g * LP(y[n - D])            D = round(2L/c * sr)

    The round trip is 2L, so the poles land where z^D = +/-g:
      * `invert=True`  (closed at the valve, open at the far end): negative
        feedback, poles at ODD multiples of c/4L -- the quarter-wave series.
      * `invert=False` (open at both ends): positive feedback, poles at ALL
        multiples of c/2L -- the half-wave series.
    Same two formulae the old code evaluated by hand, now generating the whole
    series to Nyquist instead of its first three or four terms.

    `damp_hz` is a one-pole lowpass INSIDE the loop. It is the frequency-
    dependent part of the reflection at the open end (radiation resistance grows
    as (ka)^2, so high modes lose more energy per round trip and come out
    broader). It is what stops the comb ringing like a plucked string.

    EXACT, NOT BLOCKED-APPROXIMATE. Inside a window of D samples every value the
    recursion reads was written before the window began, so the block is a pure
    vector operation and the result is bit-identical to the sample loop. This is
    the same argument `fdn_reverb` uses, and it is the only reason a 6-primary
    waveguide is affordable over 11.5 M samples.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    D = max(int(delay_samples), 2)
    if blk is None:
        blk = D
    blk = min(max(int(blk), 1), D)
    s = -1.0 if invert else 1.0
    c = float(np.exp(-2.0 * np.pi * min(damp_hz, sr * 0.45) / sr))
    g = float(loop_gain)
    y = np.zeros(n + D, dtype=np.float64)
    zi = np.zeros(1)
    bl, al = np.array([1.0 - c]), np.array([1.0, -c])
    for a0 in range(0, n, blk):
        b0 = min(a0 + blk, n)
        fb, zi = _sig.lfilter(bl, al, y[a0:b0], zi=zi)   # y[n-D] is y[a0..b0]
        y[a0 + D:b0 + D] = x[a0:b0] + s * g * fb
    return y[D:D + n]


# -------------------------------------------------------------------- noise ---
def white(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def delay(x, n):
    """Shift `x` later by `n` samples, filling the head with silence.

    A DELAY, NOT `np.roll` (R2-960). `np.roll` is CIRCULAR: it wraps the end of
    the signal onto its beginning. Used for the showroom's stereo decorrelation
    in `master.py` it put the last 11.3 ms of the 2.4 s reverb tail -- the tail
    of a car at 323 km/h -- onto the FIRST 11.3 ms of a film that opens on a
    silent showroom. Measured on the shipped master: a 0.8505 peak (-1.4 dBFS)
    inside frame 1, against a programme RMS of 0.0217 (-33 dBFS) over the
    following second. A 32 dB transient on the first frame of the film.

    `np.roll(x, n)[i] == x[i-n]` for every i >= n, so this differs from the roll
    ONLY in the first `n` samples, which is exactly the wrapped-in material.
    """
    if n <= 0:
        return np.asarray(x)
    y = np.zeros_like(np.asarray(x))
    y[n:] = np.asarray(x)[:-n]
    return y


def brown(n, seed, corner=20.0, sr=96000):
    """-6 dB/oct noise, DC-blocked. Integrating white noise directly random-walks
    away from zero over 12 M samples; a one-pole integrator with a leak at
    `corner` cannot."""
    w = white(n, seed)
    b, a = _sig.butter(1, corner, btype="highpass", fs=sr)
    out = _sig.lfilter([1.0], [1.0, -0.999], w)
    out = _sig.lfilter(b, a, out)
    return (out / max(float(np.abs(out).max()), 1e-9)).astype(np.float32)


def pink(n, seed, sr=96000):
    """-3 dB/oct, by the standard 3-pole Voss/Gardner IIR approximation
    (Robert Bristow-Johnson's coefficients). Flat to within 0.3 dB, 10 Hz-20 kHz."""
    w = white(n, seed)
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
    out = _sig.lfilter(b, a, w)
    return (out / max(float(np.abs(out).max()), 1e-9)).astype(np.float32)


# ------------------------------------------------------------------ filters ---
def sos_band(lo, hi, sr, order=4):
    return _sig.butter(order, [lo, hi], btype="bandpass", fs=sr, output="sos")


def bp(x, lo, hi, sr, order=4):
    return _sig.sosfilt(sos_band(lo, hi, sr, order), x).astype(np.float32)


def lp(x, f, sr, order=4):
    return _sig.sosfilt(_sig.butter(order, f, btype="lowpass", fs=sr, output="sos"),
                        x).astype(np.float32)


def hp(x, f, sr, order=4):
    return _sig.sosfilt(_sig.butter(order, f, btype="highpass", fs=sr, output="sos"),
                        x).astype(np.float32)


def onepole_lag(x, tau_s, sr, init=None):
    """First-order lag. Written as an lfilter so it is not a Python loop."""
    a = float(np.exp(-1.0 / (max(tau_s, 1e-6) * sr)))
    zi = np.array([(init if init is not None else float(x[0])) * a])
    y, _ = _sig.lfilter([1.0 - a], [1.0, -a], x, zi=zi)
    return y


def tv_onepole_lp(x, fc, sr):
    """TIME-VARYING one-pole lowpass, cutoff `fc` per sample.

    A static filter cannot follow a source whose distance changes by two orders
    of magnitude in a second. Implemented as the exact one-pole recursion with a
    per-sample coefficient, in a numba-free numpy-friendly form: the recursion is
    genuinely sequential, so it runs through scipy's lfilter in blocks of
    constant coefficient (256 samples = 2.7 ms at 96 kHz, far shorter than any
    audible change in the coefficient, and continuous because the filter state
    is carried across blocks).
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    fc = np.clip(np.broadcast_to(np.asarray(fc, dtype=np.float64), (n,)),
                 20.0, sr * 0.45)
    #
    # THE COEFFICIENT IS TAKEN AT THE BLOCK'S FIRST SAMPLE, NOT AVERAGED OVER THE
    # BLOCK (R2-957). `fc[a0:b0].mean()` reads 512 samples AHEAD of where it is
    # applied, so the filter's output before an event depended on the event: a
    # change confined to the last 11 s of the film moved samples up to 5.3 ms
    # (at 96 kHz) BEFORE it. The magnitude was 1.2e-06 on the tyre bus, i.e.
    # nothing, and it is still a value read from the future. `fc[a0]` is the
    # cutoff at the instant the block starts being filtered; the docstring's own
    # justification -- the block is far shorter than any audible change in the
    # coefficient -- applies unchanged, and it is causal.
    blk = 512
    out = np.empty(n, dtype=np.float64)
    zi = np.zeros(1)
    for a0 in range(0, n, blk):
        b0 = min(a0 + blk, n)
        c = float(np.exp(-2.0 * np.pi * fc[a0] / sr))
        y, zi = _sig.lfilter([1.0 - c], [1.0, -c], x[a0:b0], zi=zi)
        out[a0:b0] = y
    return out.astype(np.float32)


# ---------------------------------------------------- complementary bandsplit --
def band_edges(sr):
    """Crossover frequencies for the air-absorption filterbank."""
    e = [88.4, 176.8, 353.6, 707.1, 1414.2, 2828.4, 5656.9, 11313.7]
    return [f for f in e if f < sr * 0.45]


def band_ranges(sr):
    e = band_edges(sr)
    lo = [10.0] + e
    hi = e + [min(sr * 0.49, 20000.0)]
    return list(zip(lo, hi))


def band_centres(sr):
    return [float(np.sqrt(a * b)) for a, b in band_ranges(sr)]


def band_absorption_table(sr, temp_c=18.0, rh_pct=55.0, r_max=2000.0,
                          n_r=240, n_f=32):
    """Effective air-absorption gain per band as a function of distance.

    NOT alpha(band centre) * r. The bands are an octave wide and alpha roughly
    QUADRUPLES across an octave up top, so evaluating it at the geometric centre
    over-attenuates the whole lower half of every band. Measured consequence on
    the first master: 8.5 dB below a pink reference at 4 kHz and 13.6 dB below at
    6.3 kHz, i.e. a film that sounded like it was under a blanket, produced by a
    modelling shortcut rather than by the air.

    Instead each band's transmission is POWER-AVERAGED over 32 log-spaced
    frequencies inside it, at every distance, and the result is a per-band curve
    G(r) that is interpolated per sample. Same physics, evaluated properly.

    Returns (r_grid, dB table of shape (n_bands, n_r)).
    """
    rs = np.concatenate([[0.0], np.logspace(np.log10(0.25), np.log10(r_max), n_r - 1)])
    out = []
    for lo, hi in band_ranges(sr):
        fs = np.exp(np.linspace(np.log(max(lo, 10.0)), np.log(hi), n_f))
        a = iso9613_alpha(fs, temp_c, rh_pct)                   # dB/m
        g = np.sqrt(np.mean(10.0 ** (-np.outer(rs, a) / 10.0), axis=1))
        out.append(20.0 * np.log10(np.maximum(g, 1e-12)))
    return rs, np.array(out)


def split_bands(x, sr, order=4):
    """Yield complementary bands whose sum is EXACTLY x.

    Built as successive zero-phase lowpasses: band_k = lp_k(x) - lp_{k-1}(x),
    with lp_0 = 0 and lp_B = x, so the sum telescopes to x to machine precision
    with no crossover ripple at all. Zero-phase (filtfilt) costs a small
    non-causal pre-echo on transients -- at 96 kHz with a 4-pole Butterworth the
    pre-ring of the lowest crossover is about 8 ms, and it is the price of a
    filterbank that provably does not colour the signal when every band gain is
    1.0. Checked by `verify.py::test_bandsplit_reconstruction`.
    """
    prev = np.zeros_like(x, dtype=np.float64)
    for f in band_edges(sr):
        sos = _sig.butter(order, f, btype="lowpass", fs=sr, output="sos")
        cur = _sig.sosfiltfilt(sos, x)
        yield (cur - prev).astype(np.float32)
        prev = cur
    yield (np.asarray(x, dtype=np.float64) - prev).astype(np.float32)


# ---------------------------------------------------------- air, ISO 9613-1 ---
def iso9613_alpha(f, temp_c=18.0, rh_pct=55.0, p_kpa=101.325):
    """Atmospheric absorption in dB per metre. ISO 9613-1:1993, closed form.

    Not a fitted curve and not a constant: the whole point of the lap is that a
    car 500 m away has lost its top two octaves and one 26 m away has not.
    """
    f = np.asarray(f, dtype=np.float64)
    T = temp_c + 273.15
    T0 = 293.15
    pr = p_kpa / 101.325
    # saturation vapour pressure ratio (ISO 9613-1 Annex, Eq. from psat)
    Csat = -6.8346 * (273.16 / T) ** 1.261 + 4.6151
    psat_ratio = 10.0 ** Csat
    h = rh_pct * psat_ratio / pr                      # molar concentration of water vapour, %
    frO = pr * (24.0 + 4.04e4 * h * (0.02 + h) / (0.391 + h))
    frN = pr * (T / T0) ** -0.5 * (9.0 + 280.0 * h * np.exp(-4.170 * ((T / T0) ** (-1.0 / 3.0) - 1.0)))
    a = 8.686 * f * f * (
        1.84e-11 * (1.0 / pr) * np.sqrt(T / T0)
        + (T / T0) ** -2.5 * (
            0.01275 * np.exp(-2239.1 / T) / (frO + f * f / frO)
            + 0.1068 * np.exp(-3352.0 / T) / (frN + f * f / frN)))
    return a                                          # dB/m


def speed_of_sound(temp_c=18.0):
    return 331.3 * np.sqrt(1.0 + temp_c / 273.15)


# -------------------------------------------------------------------- reverb --
def fdn_reverb(x, sr, delays_m, rt60_low, rt60_high, c=None, seed=11, wet_hf_hz=4000.0):
    """Feedback delay network sized from a REAL room's dimensions.

    `delays_m` are acoustic path lengths in metres -- for the showroom they come
    straight from `circuit_spec.showroom.interior_m`, so the modal spacing of the
    tail is the modal spacing of the actual room rather than of a preset. The
    feedback matrix is a Householder reflection (lossless, so the decay is set
    only by the per-line damping, which is what makes RT60 controllable).
    """
    x = np.asarray(x, dtype=np.float64)
    if c is None:
        c = float(speed_of_sound(20.0))
    n = x.shape[0]
    N = len(delays_m)
    D = [max(int(round(d / c * sr)), 8) for d in delays_m]
    # per-line gain for the target RT60 at low frequency
    g = np.array([10.0 ** (-3.0 * d / (c * rt60_low)) for d in delays_m])
    # per-line one-pole damping so HF decays at rt60_high instead
    gh = np.array([10.0 ** (-3.0 * d / (c * rt60_high)) for d in delays_m])
    damp = np.clip(1.0 - gh / np.maximum(g, 1e-9), 0.0, 0.98)

    rng = np.random.default_rng(seed)
    inj = rng.choice([-1.0, 1.0], N) / np.sqrt(N)
    u = np.ones(N) / np.sqrt(N)                       # Householder vector

    # BLOCK SIZE = the SHORTEST delay. Inside a block of that length every read
    # from every line was written before the block began, so the whole block can
    # be read, mixed and written as vectors. This is exact, not an approximation:
    # it is the same recursion, evaluated in an order the data dependencies allow.
    blk = min(D)
    lines = [np.zeros(n + d + blk) for d in D]        # write positions are absolute
    out = np.zeros(n)
    zi = [np.zeros(1) for _ in range(N)]
    for a0 in range(0, n, blk):
        b0 = min(a0 + blk, n)
        m = b0 - a0
        s = np.empty((N, m))
        for k in range(N):
            s[k] = lines[k][a0:b0]                    # what was written D_k ago
        for k in range(N):
            c = 1.0 - damp[k]
            y, zi[k] = _sig.lfilter([c], [1.0, -(1.0 - c)], s[k], zi=zi[k])
            s[k] = y
        v = s * g[:, None]
        v = v - 2.0 * u[:, None] * (u @ v)[None, :]
        v = v + inj[:, None] * x[a0:b0][None, :]
        for k in range(N):
            lines[k][a0 + D[k]:b0 + D[k]] = v[k]
        out[a0:b0] = s.sum(axis=0) / np.sqrt(N)
    return out.astype(np.float32)


# ------------------------------------------------------------------ dynamics --
def soft_limit(x, ceiling=0.891, lookahead_ms=1.0, release_ms=40.0, sr=96000,
               true_peak=True, oversample=4):
    """Lookahead limiter that limits the TRUE peak, not the sample peak.

    `ceiling` is linear (0.891 = -1.0 dBFS). Returns (y, max_gain_reduction_db).

    WHY TRUE PEAK. The first version limited |x| to -1.25 dBFS and the finished
    master measured -0.73 dBTP: the inter-sample peaks sat 0.52 dB above every
    sample, which is exactly what a -1 dBTP delivery spec exists to catch. The
    envelope is therefore taken from a 4x oversampled copy and folded back to
    the base rate by a max over each group of `oversample` samples, so the gain
    that gets applied is the gain the reconstructed waveform needs.

    R2-4032: THE GAIN PATH WAS ZERO-PHASE AND HELD FOR A QUARTER OF A SECOND.
    ------------------------------------------------------------------------
    The previous version built the gain as

        g = minimum_filter1d(need, size=2*rel+1)       rel = 120 ms
        g = sosfiltfilt(butter(2, 1000/release_ms), g)

    Both of those steps are SYMMETRIC IN TIME. `minimum_filter1d` centred on a
    +-120 ms window pins the gain to the minimum over a quarter of a second on
    BOTH sides of a transient, and `sosfiltfilt` is zero-phase, so the smoothing
    also runs backwards. Measured on a single-sample impulse at 96 kHz: the gain
    began falling 161.4 ms BEFORE the peak and recovered 161.4 ms after it, a
    322.9 ms hole with the transient in the middle, reaching -14.10 dB.

    That is not a limiter artefact, it is a limiter running in reverse. Every
    attack in the film ducked the two hundred milliseconds of programme leading
    up to it -- which is exactly the material whose absence a listener hears as
    "no attack", because the ear judges an onset against what preceded it. The
    breach's 10-90% onset rise measured 6.9 ms in the delivered master against a
    2 ms target, and this stage is where the other 5 ms went.

    THE REPLACEMENT IS CAUSAL AND SHORT. Attack comes from the lookahead alone
    (1 ms, the spec's ceiling), release is a one-pole with a 40 ms time
    constant, and NOTHING in the gain path runs backwards. The recursion

        g[i] = need[i]                        if need[i] <= g[i-1]   (attack)
        g[i] = a*g[i-1] + (1-a)*need[i]       otherwise              (release)

    is genuinely nonlinear, so it is evaluated at a 2 kHz CONTROL RATE over the
    block minimum of `need` -- which can never miss a peak, because the block
    minimum bounds every sample in the block -- and interpolated back up. At
    2 kHz the control grid is 0.5 ms, an eighth of the release constant and half
    the lookahead, so nothing audible is quantised by it. The final
    `min(g, need)` guarantees the ceiling exactly, as before.
    """
    from scipy.ndimage import maximum_filter1d
    x = np.asarray(x, dtype=np.float64)
    squeeze = x.ndim == 1
    if squeeze:
        x = x[:, None]
    n = x.shape[0]
    if true_peak:
        env = np.zeros(n)
        for ch in range(x.shape[1]):
            up = np.abs(_sig.resample_poly(x[:, ch], oversample, 1,
                                           window=("kaiser", 8.0)))
            m = up.shape[0] // oversample * oversample
            env = np.maximum(env, up[:m].reshape(-1, oversample).max(axis=1)[:n]
                             if m // oversample >= n else
                             np.pad(up[:m].reshape(-1, oversample).max(axis=1),
                                    (0, n - m // oversample), mode="edge"))
    else:
        env = np.abs(x).max(axis=1)
    la = max(int(sr * lookahead_ms / 1000.0), 1)
    # the lookahead is the ONLY non-causality left, and it is one millisecond:
    # the gain is allowed to see `la` samples ahead so the attack is a ramp
    # rather than a step, and no further.
    peak = maximum_filter1d(env, size=2 * la + 1, mode="nearest")
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))

    blk = max(int(sr / 2000.0), 1)                       # 0.5 ms control grid
    nb = (n + blk - 1) // blk
    pad = nb * blk - n
    bm = np.min(np.pad(need, (0, pad), mode="edge").reshape(nb, blk), axis=1)
    a = float(np.exp(-blk / (release_ms * 1e-3 * sr)))
    gc = np.empty(nb)
    prev = 1.0
    for i in range(nb):
        v = bm[i]
        prev = v if v <= prev else a * prev + (1.0 - a) * v
        gc[i] = prev
    # linear interpolation between control-block CENTRES, so the release is a
    # smooth ramp rather than a 0.5 ms staircase. Deliberately not an IIR
    # smoother: an lfilter would start from zero initial conditions and open the
    # film with a gain ramp out of silence, which is how the first version of
    # this rewrite put a 0.5 ms fade-in on sample 0.
    xc = np.arange(nb) * blk + (blk - 1) * 0.5
    g = np.interp(np.arange(n), xc, gc)
    g = np.minimum(g, need)
    gr_db = float(20.0 * np.log10(max(float(g.min()), 1e-9)))
    # HOW MUCH OF THE FILM, NOT JUST HOW DEEP. A maximum is one instant and can
    # be one sample; what a listener hears is the DISTRIBUTION. The diagnosis
    # measured the delivered master at "20.65% pulled >1 dB, 15.48% >3 dB,
    # 12.15% >6 dB, mean -1.75 dB", and those are the numbers a limiter should
    # be judged on. Stashed on the function rather than added to the return, so
    # every existing caller keeps working.
    gdb = 20.0 * np.log10(np.maximum(g, 1e-9))
    soft_limit.last_stats = {
        "max_gr_db": gr_db,
        "mean_gr_db": float(gdb.mean()),
        "frac_over_1db": float((gdb < -1.0).mean()),
        "frac_over_3db": float((gdb < -3.0).mean()),
        "frac_over_6db": float((gdb < -6.0).mean()),
        "p50_gr_db": float(np.percentile(gdb, 50)),
        "p01_gr_db": float(np.percentile(gdb, 1)),
    }
    y = (x * g[:, None]).astype(np.float32)
    return (y[:, 0] if squeeze else y), gr_db


def program_gain(x, sr, target_rms=0.10, attack_s=4.0, release_s=8.0,
                 max_boost_db=12.0, max_cut_db=6.0):
    """A slow mastering gain, not a compressor.

    The film runs from a dark empty showroom to 313 km/h at 26 m. A purely
    physical 1/r mix puts beat 1 at about -55 LUFS short-term and beat 5 at -8,
    which is a 47 dB program range: correct, and unwatchable. This applies one
    slow, bounded gain with 4 s / 8 s time constants -- ten times slower than any
    musical compressor, so it does not pump and does not audibly duck one layer
    under another. It is a MIX decision and is reported as one: the short-term
    LUFS range before and after is measured in the report.
    """
    x = np.asarray(x, dtype=np.float64)
    e = _sig.sosfilt(_sig.butter(2, 20.0, btype="highpass", fs=sr, output="sos"), x) ** 2
    aa = float(np.exp(-1.0 / (attack_s * sr)))
    rr = float(np.exp(-1.0 / (release_s * sr)))
    env = np.empty_like(e)
    acc = float(e[:sr].mean()) if e.shape[0] > sr else float(e.mean())
    blk = 8192
    for a0 in range(0, e.shape[0], blk):
        b0 = min(a0 + blk, e.shape[0])
        m = float(e[a0:b0].mean())
        c = aa if m > acc else rr
        # exact block-wise one-pole on the block mean, then held
        acc = m + (acc - m) * (c ** (b0 - a0))
        env[a0:b0] = acc
    rms = np.sqrt(np.maximum(env, 1e-14))
    g_db = 20.0 * np.log10(target_rms / np.maximum(rms, 1e-7))
    g_db = np.clip(g_db, -max_cut_db, max_boost_db)
    # smooth the (already slow) gain once more so there is no block edge at all
    #
    # THIS `filtfilt` IS THE ONE PLACE THE FILM'S END REACHES ITS FIRST SAMPLE,
    # AND IT IS NAMED HERE SO THE CLAIM CAN BE EXACT (R2-1186). `sosfiltfilt`
    # runs the filter forwards and then backwards, so g_db[0] is a function of
    # g_db[-1]. Measured on film-length buffers by bursting the last 0.2 s:
    #
    #     |dg| at sample 0     5.3e-13 dB on one bench, 2.6e-09 dB on another
    #     |dg| > 0.1 dB        from ~0.7 s before the burst
    #     |dg| > 1e-6 dB       from ~6 s before the burst
    #
    # The near-field numbers are the INTENDED behaviour of a 4 s/8 s mastering
    # gain and are described above. The far-field number is the honest one: at
    # sample 0 the dependence is under 1e-8 dB, roughly ten orders of magnitude
    # below a 24-bit LSB and more than 200 dB below the +31.2 dB frame-1 defect
    # that motivated the sweep. It is not zero, so "the film does not depend on
    # its ending" is false as stated; it is bounded, so "the film's dependence on
    # its ending is unmeasurable at 24 bits" is true. The second sentence is the
    # one this project can defend, and R2-1089's prefix-identity claim should be
    # read against it.
    #
    # Two look-aheads above are the same SHAPE as the R2-957 sites that were
    # fixed, and are LEFT AS THEY ARE deliberately: `acc = e[:sr].mean()` seeds
    # the envelope from the first second, and `m = e[a0:b0].mean()` reads the
    # 85 ms block (blk 8192 at 96 kHz) it is about to write. Both are local, both
    # sit inside a gain that is explicitly a MIX decision rather than a source,
    # and changing either would move the master. Causalising them is a one-line
    # change (`e[0]`, `e[a0]`) if the class is ever to be closed rather than
    # bounded -- but that is a deliberate re-mix needing a re-render and a fresh
    # listening pass, not a quiet edit made while the client is being asked to
    # approve the current one.
    g_db = _sig.sosfiltfilt(_sig.butter(2, 0.5, btype="lowpass", fs=sr, output="sos"), g_db)
    return (x * 10.0 ** (g_db / 20.0)).astype(np.float32), g_db


# ------------------------------------------------------------- BS.1770-4 -----
def _k_weighting(sr):
    """ITU-R BS.1770-4 pre-filter + RLB, bilinear-transformed to `sr`.

    Coefficients are DERIVED from the standard's analogue prototype rather than
    copied at 48 kHz, so the same code measures the 96 kHz internal bus and the
    48 kHz master and gets the same answer.
    """
    # stage 1: high-frequency shelf, +4 dB above ~1.5 kHz
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = np.tan(np.pi * f0 / sr)
    Vh = 10.0 ** (G / 20.0)
    Vb = Vh ** 0.4996667741545416
    a0 = 1.0 + K / Q + K * K
    b = np.array([(Vh + Vb * K / Q + K * K), 2.0 * (K * K - Vh), (Vh - Vb * K / Q + K * K)]) / a0
    a = np.array([1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0])
    # stage 2: RLB high-pass at 38 Hz
    f0b, Qb = 38.13547087602444, 0.5003270373238773
    Kb = np.tan(np.pi * f0b / sr)
    a0b = 1.0 + Kb / Qb + Kb * Kb
    b2 = np.array([1.0, -2.0, 1.0])
    a2 = np.array([1.0, 2.0 * (Kb * Kb - 1.0) / a0b, (1.0 - Kb / Qb + Kb * Kb) / a0b])
    return (b, a), (b2, a2)


def loudness_lufs(stereo, sr, gate=True):
    """Integrated loudness, ITU-R BS.1770-4 with the -10 LU relative gate.

    stereo: (n, 2). Channel weights 1.0/1.0 for L/R as the standard specifies.
    Returns (integrated_lufs, short_term_lufs_array, block_times).
    """
    x = np.asarray(stereo, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    (b1, a1), (b2, a2) = _k_weighting(sr)
    y = np.empty_like(x)
    for ch in range(x.shape[1]):
        y[:, ch] = _sig.lfilter(b2, a2, _sig.lfilter(b1, a1, x[:, ch]))
    # 400 ms blocks, 75 % overlap
    bs = int(round(0.4 * sr))
    hop = bs // 4
    nb = max((x.shape[0] - bs) // hop + 1, 1)
    p = np.empty(nb)
    for i in range(nb):
        seg = y[i * hop:i * hop + bs]
        p[i] = float((seg ** 2).mean(axis=0).sum())
    with np.errstate(divide="ignore"):
        lk = -0.691 + 10.0 * np.log10(np.maximum(p, 1e-20))
    if not gate:
        return float(-0.691 + 10.0 * np.log10(p.mean())), lk, np.arange(nb) * hop / sr
    keep = lk > -70.0
    if not keep.any():
        return float("-inf"), lk, np.arange(nb) * hop / sr
    rel = -0.691 + 10.0 * np.log10(p[keep].mean()) - 10.0
    keep2 = keep & (lk > rel)
    if not keep2.any():
        keep2 = keep
    integ = -0.691 + 10.0 * np.log10(p[keep2].mean())
    # 3 s short-term
    sb = int(round(3.0 * sr))
    nst = max((x.shape[0] - sb) // hop + 1, 1)
    st = np.empty(nst)
    for i in range(nst):
        seg = y[i * hop:i * hop + sb]
        st[i] = -0.691 + 10.0 * np.log10(max(float((seg ** 2).mean(axis=0).sum()), 1e-20))
    return float(integ), st, np.arange(nst) * hop / sr


def true_peak_dbtp(stereo, sr, oversample=4):
    """True peak by 4x polyphase upsampling, as BS.1770-4 Annex 2 specifies."""
    x = np.asarray(stereo, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    pk = 0.0
    for ch in range(x.shape[1]):
        up = _sig.resample_poly(x[:, ch], oversample, 1, window=("kaiser", 8.0))
        pk = max(pk, float(np.abs(up).max()))
    return 20.0 * np.log10(max(pk, 1e-12))


def max_short_term_lufs(x, sr, win_s=3.0, hop_s=0.5):
    """Peak 3-second short-term loudness, O(n) via a cumulative sum.

    Used for gain staging: "how loud is this layer when it is playing" is the
    question a bus trim answers, and integrated loudness answers a different one
    (a layer that plays for four seconds of a two-minute film has a very low
    integrated value and a perfectly normal short-term one).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    (b1, a1), (b2, a2) = _k_weighting(sr)
    p = np.zeros(x.shape[0])
    for ch in range(x.shape[1]):
        y = _sig.lfilter(b2, a2, _sig.lfilter(b1, a1, x[:, ch]))
        p += y * y
    c = np.concatenate([[0.0], np.cumsum(p)])
    w = int(win_s * sr)
    h = max(int(hop_s * sr), 1)
    if c.shape[0] <= w:
        m = float(p.mean())
    else:
        starts = np.arange(0, c.shape[0] - 1 - w, h)
        m = float(((c[starts + w] - c[starts]) / w).max())
    return float(-0.691 + 10.0 * np.log10(max(m, 1e-20)))
