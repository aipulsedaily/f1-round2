"""Synthesis of the control corpus. Code only -- no recordings, ever.

Every generator here is seeded and deterministic, so a control is a function of
this file and nothing else. Nothing in this module is imported by the render
path (`percept.g_construct` checks that, and fails if it stops being true).

Deliberately self-contained: it does NOT import `audio.layers` or `audio.dsp`.
Those files are being rebuilt, and a control that moves when the thing it is
controlling moves is not a control.
"""

from __future__ import annotations

import math
import os

import numpy as np
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SR = 48000                       # the delivered master's rate
FILM_S = 5956000 / 48000.0       # 124.0833 s, the delivered master's length
BEAT1_S = 33.0                   # the 33 seconds the client actually named

MASTER_WAV = os.path.join(ROOT, "audio", "out", "master.wav")
SWAP_B1_LOOP_WAV = os.path.join(ROOT, "tmp", "gateaudit", "swap_b1_loop.wav")

BEAT1_SHEET = {"beats": [{"name": "1_assembly", "start_s": 0.0}]}
LAP_SHEET = {"beats": [{"name": "5_lap", "start_s": 0.0}]}


def cache_path(name):
    d = os.path.join(ROOT, "tmp", "percept_controls")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def _stereo(a, b=None):
    a = np.asarray(a, dtype=np.float64)
    return np.stack([a, a if b is None else np.asarray(b, dtype=np.float64)], axis=1)


def _norm(x, rms=0.08):
    x = np.asarray(x, dtype=np.float64)
    r = math.sqrt(float(np.mean(x ** 2))) or 1.0
    return x * (rms / r)


# =========================================================== the negatives ==
def octave_matched_noise(x, sr, seed=1401):
    """C1 -- white noise wearing `x`'s own octave balance.

    This is `verify._hairdryer_like`, carried across so the corpus keeps the old
    suite's own strongest adversary. It has the film's tonal balance and no line
    spectrum anywhere, so anything that scores it well is scoring brightness or
    level and not harmonicity. The old harmonic gate's thresholds were tuned
    against THIS and nothing else, which is exactly why the only signal it could
    fail was flat noise.
    """
    x = np.asarray(x, dtype=np.float64)
    x = x.mean(axis=1) if x.ndim > 1 else x
    rng = np.random.default_rng(seed)
    nz = rng.standard_normal(x.shape[0])
    out = np.zeros_like(nz)
    edges = [31.25 * 2.0 ** k for k in range(10)]
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi >= sr * 0.49:
            break
        sos = _sig.butter(4, [lo, min(hi, sr * 0.45)], btype="bandpass",
                          fs=sr, output="sos")
        bx = _sig.sosfilt(sos, x)
        bn = _sig.sosfilt(sos, nz)
        out += bn * (math.sqrt(np.mean(bx ** 2)) / max(math.sqrt(np.mean(bn ** 2)), 1e-12))
    return out


def _impact_block(sr, dur_s, seed, partials=((1.0, 1.0), (2.31, 0.45),
                                             (3.87, 0.22), (6.1, 0.10)),
                  f0=262.0, n_hits=8):
    """One 2 s block of struck-tube hits: the delivered impact voice, exactly --
    four exponentially decaying sines at the inharmonic ratios 1 : 2.31 : 3.87 :
    6.1, which is the timbre of a struck metal bar, not of a carbon part."""
    n = int(dur_s * sr)
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    for h in range(n_hits):
        s = int(h / n_hits * n * 0.5)
        dur = 0.55
        L = min(int(dur * sr), n - s)
        if L <= 16:
            continue
        tt = np.arange(L) / sr
        fp = f0 * float(rng.uniform(0.9, 1.15))
        hit = np.zeros(L)
        for k, amp in partials:
            hit += amp * np.sin(2 * np.pi * fp * k * tt) * np.exp(-tt / (dur * 0.28 / k ** 0.5))
        out[s:s + L] += hit
    return out


def tiled_loop(sr=SR, total_s=BEAT1_S, block_s=2.0, seed=77):
    """C2 -- one 2.000 s block tiled to length. The audit's decisive exhibit:
    beat 1 replaced by this passed all eight old gates, and the old harmonic
    gate rated the loop 35.9 dB BETTER than the film it passed."""
    blk = _impact_block(sr, block_s, seed)
    reps = int(math.ceil(total_s / block_s))
    y = np.tile(blk, reps)[:int(total_s * sr)]
    return _stereo(_norm(y))


def blower_plus_tubes(sr=SR, total_s=BEAT1_S, q=80.0, seed=1917,
                      modes=(187.0, 242.0, 332.0, 452.0, 614.0)):
    """C3 -- the client's exact words built as a signal: white noise through a
    bank of high-Q INHARMONIC pipe modes. Zero line spectrum, zero periodicity.

    At Q=80 this scored +4.04 dB on the shipped harmonic gate -- above that
    gate's 2.0 dB ENGINE bar -- and passed beat 1's limit with more margin than
    the delivered master. It is the single most important negative control in
    the corpus, because it is the one the old instrument rated as CLEAN.
    """
    n = int(total_s * sr)
    rng = np.random.default_rng(seed)
    # the blower: continuous white excitation into the pipes
    exc = rng.standard_normal(n)
    # AND SOMEONE BANGING ON THEM: irregular strikes into the SAME fixed pipes,
    # so the bank has bursts and tails to be measured on. The strikes are
    # irregularly spaced on purpose -- this control must fail on WHAT rings,
    # not on WHEN it is struck, or it would only be a slower C2.
    t = 1.0
    while t < total_s - 1.0:
        s = int(t * sr)
        L = min(int(0.004 * sr), n - s)
        exc[s:s + L] += rng.standard_normal(L) * 60.0
        t += float(rng.uniform(0.8, 2.6))
    out = np.zeros(n)
    for f in modes:
        w0 = 2 * np.pi * f / sr
        al = math.sin(w0) / (2 * q)
        b = np.array([al, 0.0, -al])
        a = np.array([1.0 + al, -2.0 * math.cos(w0), 1.0 - al])
        out += _sig.lfilter(b / a[0], a / a[0], exc)
    nz = rng.standard_normal(n)
    # a broadband bed under it, exactly as a real blower has
    sos = _sig.butter(2, [900.0, 6000.0], btype="bandpass", fs=sr, output="sos")
    out = _norm(out) + _norm(_sig.sosfilt(sos, rng.standard_normal(n)), 0.05)
    return _stereo(_norm(out), _norm(np.roll(out, 137)))


def spectral_tilt(x, sr, db_per_octave=-4.0, pivot_hz=1000.0):
    """C7 -- a broad spectral tilt over an existing signal.

    ANTI-CHEAT. The whole-band SFM of the delivered master reads a reassuring
    0.0142 -- that number is measuring the mix's low-frequency tilt, not its
    tonality, and it is what let this ship. G-FLAT computes flatness INSIDE each
    1/3-octave band, so a tilt cannot move it. This control is what proves that.
    """
    x = np.asarray(x, dtype=np.float64)
    mono2 = x if x.ndim > 1 else x[:, None]
    n = mono2.shape[0]
    f = np.fft.rfftfreq(n, 1.0 / sr)
    g = 10.0 ** (db_per_octave * np.log2(np.maximum(f, 1.0) / pivot_hz) / 20.0)
    g = np.clip(g, 1e-3, 1e3)
    out = np.stack([np.fft.irfft(np.fft.rfft(mono2[:, c]) * g, n)
                    for c in range(mono2.shape[1])], axis=1)
    return out * (float(np.abs(x).max()) / max(float(np.abs(out).max()), 1e-12)) * 0.98


def jittered_identical_gestures(sr=SR, total_s=BEAT1_S, period_s=1.375,
                                jitter=0.15, n=12, seed=606):
    """C6 -- ANTI-CHEAT: the SAME gesture, on a jittered grid.

    Required verdict: FAIL G-GESTURE, PASS G-MOD. This control exists so that
    "just add jitter" cannot buy a pass. Jitter smears the modulation line, so
    G-MOD is satisfied; the gesture is bit-identical every time, so G-GESTURE
    is not. If these two ever agree on this file, one of them is broken.
    """
    rng = np.random.default_rng(seed)
    N = int(total_s * sr)
    out = np.zeros(N)
    g = _impact_block(sr, 0.6, 4321, n_hits=3)
    g *= np.exp(-np.arange(len(g)) / (0.25 * sr))
    t0 = 1.5
    for i in range(n):
        t = t0 + i * period_s * (1.0 + float(rng.uniform(-jitter, jitter)))
        s = int(t * sr)
        L = min(len(g), N - s)
        if L > 16:
            out[s:s + L] += g[:L]
    tail = diffuse_tail(out, sr, rt60_s=1.1, seed=91)
    return _stereo(_norm(out + 0.5 * tail), _norm(out + 0.5 * diffuse_tail(out, sr, 1.1, seed=92)))


# ============================================================ room engines ==
def diffuse_tail(x, sr, rt60_s=1.6, seed=5, density=2500.0):
    """Velvet-noise convolution: +-1 pulses, one per grid cell at a jittered
    position, with a band-independent exponential decay.

    Velvet noise HAS NO MODAL STRUCTURE. Its magnitude response is a noise, not
    a comb, so its frequency-domain autocorrelation has no peak -- which is the
    direct structural answer to "the room replies at the same pitches to 0.01 %".
    Used here to build the POSITIVE controls: this is what a room that passes
    G-ROOM sounds like.
    """
    rng = np.random.default_rng(seed)
    n_ir = int(rt60_s * sr)
    grid = max(int(sr / density), 1)
    n_p = n_ir // grid
    idx = (np.arange(n_p) * grid + rng.integers(0, grid, n_p)).astype(int)
    idx = idx[idx < n_ir]
    ir = np.zeros(n_ir)
    ir[idx] = rng.choice([-1.0, 1.0], size=idx.shape[0])
    ir *= np.exp(-6.9078 * np.arange(n_ir) / (rt60_s * sr))
    ir /= math.sqrt(float(np.sum(ir ** 2)) or 1.0)
    return _sig.fftconvolve(np.asarray(x, float), ir)[:len(x)]


def comb_tail(x, sr, delays_m=(6.5, 11.0, 15.0, 18.6, 18.9, 22.9, 26.0, 37.9),
              rt60_s=2.4, seed=11):
    """The DEFECT, for the negative half: an 8-tap FDN with no diffusion stages.

    Its 13 strongest lines are every one a harmonic of a delay length. This is
    what G-ROOM(a) must fail and what `diffuse_tail` must pass, and having both
    means the bar is bracketed rather than guessed.
    """
    c = 343.2158
    D = [max(int(round(d / c * sr)), 8) for d in delays_m]
    N = len(D)
    H = np.array([[1.0]])
    while H.shape[0] < N:              # Sylvester Hadamard, N a power of two
        H = np.block([[H, H], [H, -H]])
    H = H[:N, :N] / math.sqrt(N)       # orthogonal: the loop is stable
    x = np.asarray(x, float)
    n = len(x)
    _ = seed
    # BLOCKED, because a delay line shorter than the block cannot be read and
    # written in the same block: with the shortest line at Dmin samples, every
    # read inside a Dmin-sample block predates every write in it, so the whole
    # block is one vectorised pass instead of Dmin scalar ones.
    blk = max(min(D), 8)
    bufs = [np.zeros(d + blk) for d in D]
    wpos = [0] * N
    g = [10.0 ** (-3.0 * blk / (rt60_s * sr)) for _ in D]
    out = np.zeros(n)
    for b0 in range(0, n, blk):
        b1 = min(b0 + blk, n)
        L = b1 - b0
        rd = np.empty((N, L))
        for j in range(N):
            p = (wpos[j] - D[j]) % len(bufs[j])
            idx = (p + np.arange(L)) % len(bufs[j])
            rd[j] = bufs[j][idx]
        out[b0:b1] = rd.sum(axis=0) / N
        fb = H @ rd
        for j in range(N):
            idx = (wpos[j] + np.arange(L)) % len(bufs[j])
            bufs[j][idx] = (x[b0:b1] + fb[j]) * g[j] ** (D[j] / blk)
            wpos[j] = (wpos[j] + L) % len(bufs[j])
    return out


# ============================================================ the positives =
def _plate_modes(a, b, h, E, nu, rho, fmax=6000.0, n=18):
    """Simply-supported orthotropic-ish plate: f_mn = (pi/2) sqrt(D/(rho h))
    (m^2/a^2 + n^2/b^2). CFRP constants, not glass. The modes come from a
    GEOMETRY, which is the law G-CONSTRUCT enforces on the render path."""
    D = E * h ** 3 / (12.0 * (1.0 - nu ** 2))
    k = (math.pi / 2.0) * math.sqrt(D / (rho * h))
    out = []
    for m in range(1, n):
        for q in range(1, n):
            f = k * ((m / a) ** 2 + (q / b) ** 2)
            if 60.0 < f <= fmax:
                w = 1.0 / (m * q) if (m % 2 and q % 2) else 0.18 / (m * q)
                out.append((f, w))
    out.sort()
    return out[:48]


def _hertzian_pulse(sr, m_kg, r_m, e_star, v_ms):
    """tau = 2.94*(m^2/(R*E*^2*v))^(1/5), rendered as a raised half-sine.

    Band-limited BY CONSTRUCTION with an f^-2 rolloff above 1/tau, which is what
    replaces `rng.standard_normal(L)*exp(-tt/0.004)` -- a white click at gain
    0.5, 616 times, which is a noise generator with a schedule.
    """
    tau = 2.94 * (m_kg ** 2 / (r_m * e_star ** 2 * max(v_ms, 0.1))) ** 0.2
    # the spec's own stated range for this contact: 0.4-2.5 ms. Below 0.4 ms the
    # pulse is a click with energy to 5 kHz, and a click is a noise generator
    # with a schedule -- which is the thing being replaced.
    tau = min(max(tau, 0.4e-3), 2.5e-3)
    n = max(int(tau * sr), 4)
    t = np.arange(n) / sr
    return np.sin(math.pi * t / tau) ** 1.5


def _modal_hit(sr, modes, dur_s, eta, seed, exc):
    n = int(dur_s * sr)
    x = np.zeros(n)
    x[:len(exc)] = exc[:n]
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    for f, w in modes:
        if f >= sr * 0.45:
            continue
        q = 1.0 / max(eta, 1e-4)
        w0 = 2 * np.pi * f / sr
        al = math.sin(w0) / (2 * q)
        b = np.array([al, 0.0, -al])
        a = np.array([1.0 + al, -2.0 * math.cos(w0), 1.0 - al])
        out += w * float(rng.uniform(0.85, 1.15)) * _sig.lfilter(b / a[0], a / a[0], x)
    return out


def distinct_gestures(sr=SR, n=12, seed=31):
    """12 bursts, each from its OWN plate geometry -- a different modal set per
    cluster, which is what "the car is being assembled from its own parts"
    sounds like. The positive control for G-GESTURE."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a = float(rng.uniform(0.25, 1.6))
        b = float(rng.uniform(0.2, 1.3))
        h = float(rng.uniform(0.0018, 0.012))
        modes = _plate_modes(a, b, h, 135e9, 0.30, 1600.0)
        # CFRP loss factor 0.005-0.02 plus a clamped joint 0.05-0.1
        eta = float(rng.uniform(0.02, 0.09))
        exc = _hertzian_pulse(sr, float(rng.uniform(0.4, 9.0)), 0.05, 60e9,
                              float(rng.uniform(1.0, 4.0)))
        out.append(_norm(_modal_hit(sr, modes, 0.45, eta, seed + i, exc)))
    return out


def _servo_voice(sr, n, shaft_rps, teeth, seed, level=1.0):
    """One servo: shaft rate, gear mesh at N_teeth x shaft rate, PMSM radial
    force at 2*f_electrical. All integer multiples of one shaft rate, so it is a
    HARMONIC comb -- tonal content that fills the naked reverb gaps without a
    noise generator anywhere in it."""
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)
    # incommensurate drift: no global period anywhere in the beat
    drift = 1.0 + 0.02 * (np.sin(2 * np.pi * 0.0371 * t + rng.uniform(0, 6))
                          + 0.7 * np.sin(2 * np.pi * 0.0613 * t + rng.uniform(0, 6)))
    f = shaft_rps * drift
    ph = 2 * np.pi * np.cumsum(f) / sr
    y = np.zeros(n)
    for k, amp in ((1, 0.30), (2, 0.22), (3, 0.16), (4, 0.10), (6, 0.08),
                   (teeth, 0.55), (2 * teeth, 0.22), (7, 0.18), (14, 0.09)):
        y += amp * np.sin(k * ph + rng.uniform(0, 6))
    return _norm(y, 1.0) * level


def _servo_bed(sr, n, times, rates, teeth, seed):
    """THE SERVO THAT IS CURRENTLY MOVING, and only that one.

    Fifteen simultaneous fundamentals are NOT periodic, whatever each one is on
    its own: three equal servo voices measure +2.35 dB on a calibrated
    harmonic-to-noise ratio against +45.39 dB for any one of them. So the bed is
    one voice whose shaft rate glides to the cluster that is actually moving.
    Fifteen different rates in sequence still have no global period and no fixed
    pitch, which is the property that matters -- what they must not have is
    fifteen of them at once.
    """
    t = np.arange(n) / sr
    rate = np.interp(t, np.asarray(times, float), np.asarray(rates, float))
    rate = _sig.savgol_filter(rate, min(int(0.25 * sr) | 1, (n // 2) * 2 - 1), 1)
    rng = np.random.default_rng(seed)
    drift = 1.0 + 0.015 * np.sin(2 * np.pi * 0.043 * t + rng.uniform(0, 6))
    ph = 2 * np.pi * np.cumsum(rate * drift) / sr
    nt = int(np.median(teeth))
    y = np.zeros(n)
    for k, amp in ((1, 0.30), (2, 0.22), (3, 0.16), (4, 0.10), (6, 0.08),
                   (7, 0.18), (14, 0.09), (nt, 0.55), (2 * nt, 0.22)):
        y += amp * np.sin(k * ph + rng.uniform(0, 6))
    return y


def physical_showroom_beat(sr=SR, total_s=BEAT1_S, seed=808):
    """C8b -- a beat 1 built the way the spec says to build it.

    Non-uniform arrivals on a geometric contraction (an accelerando has no
    single period), one plate geometry per cluster, Hertzian excitation,
    eta-derived damping giving T60 in tens of milliseconds, a velvet-noise tail
    with two INDEPENDENT L/R sequences, and per-cluster servo voices carrying
    the tonal content between arrivals. Nothing in it is summed with a delayed
    copy of itself.

    This is the control that proves the bars are reachable. A suite that only
    fails things is not evidence of anything.
    """
    rng = np.random.default_rng(seed)
    n = int(total_s * sr)
    dry = np.zeros(n)

    # (a) THE SCHEDULE: geometric contraction, gap ratio 0.86, 2.35 s -> 0.44 s
    gaps, g = [], 2.35
    while sum(gaps) < total_s - 4.0 and len(gaps) < 15:
        gaps.append(g)
        g *= 0.86
    times = np.cumsum([2.0] + gaps)[:15]

    # EVERY PART GETS ITS OWN PLATE GEOMETRY, not one gesture per cluster. An
    # earlier version reused one gesture for all the parts of a cluster and
    # G-ROOM's mobility limb read 0.418 on it -- correctly: the same modal set
    # struck repeatedly IS a fixed reply, whoever is doing the striking.
    n_parts = [int(rng.integers(3, 14)) for _ in times]
    ges = distinct_gestures(sr, n=int(sum(n_parts)), seed=seed + 1)
    gi = 0
    for i, t in enumerate(times):
        s = int(t * sr)
        # (b) parts land on GRAVITY, not on an equal-time grid: t = sqrt(2h/g)
        for _p in range(n_parts[i]):
            g_i = ges[gi]; gi += 1
            # each part detaches at its own moment and from its own height, so
            # t_land = sqrt(2h/g) scatters instead of clustering. Releasing them
            # all at once from similar heights put every part's landing inside
            # one 0.5 s window and printed a 1.7 Hz modulation line -- the same
            # defect as layers.py:367's exact linear placement, one level down.
            h = float(rng.uniform(0.15, 4.0))
            rel = float(rng.uniform(0.0, 0.9))
            dt = rel + math.sqrt(2.0 * h / 9.81) * float(rng.uniform(0.9, 1.1))
            # one restitution bounce
            for k, amp in ((0, 1.0), (1, 0.34)):
                ss = s + int((dt * (1 + 0.62 * k)) * sr)
                L = min(len(g_i), n - ss)
                if L > 16 and ss >= 0:
                    dry[ss:ss + L] += amp * g_i[:L] * float(rng.uniform(0.5, 1.0))

    # (c) THE VOICE BETWEEN ARRIVALS: one servo per cluster, each on its own
    #     shaft rate. ONE IS DOMINANT AT A TIME -- the cluster that is actually
    #     moving -- with its neighbours 14 dB down, because fifteen equal
    #     simultaneous fundamentals are not periodic and would score as noise on
    #     a harmonicity test however tonal each one is on its own.
    # 90-190 rev/s = 5,400-11,400 rpm: a servo motor's actual shaft range.
    rates = [float(rng.uniform(90.0, 190.0)) for _ in times]
    teeth = [int(rng.integers(9, 23)) for _ in times]
    tone = _norm(_servo_bed(sr, n, times, rates, teeth, seed + 100), 1.0)

    # (d) THE ROOM: velvet late field, two INDEPENDENT sequences, RT60 well
    #     inside the Sabine bar for the declared box, and mixed at a level that
    #     leaves the beat TONAL rather than half reverb. The delivered master
    #     ran its room bus level with its direct bus (-36.46 vs -36.34 dBFS,
    #     49.3 % of the power); a reverb tail's magnitude response is noise, so
    #     a beat that is half tail measures as half noise however good the
    #     reverb is.
    src = _norm(dry, 1.0) * 0.13 + tone * 1.0
    L = src + 0.05 * diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 11)
    R = src + 0.05 * diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 12)
    return np.stack([_norm(L, 0.09), _norm(R, 0.09)], axis=1)


def constant_rpm_pu(sr=SR, total_s=33.0, rpm=11000.0, order=1.5, seed=99):
    """C8 -- a physics-true positive: a power unit held at constant rpm.

    Firing lines at order*k*rpm/60 with a mild incommensurate rpm wobble (no
    modulation line in 0.2-3 Hz), 1-2 % per-cylinder gain dispersion so the
    comb is not mathematically perfect, and a compressor band kept at 4-13 kHz
    -- ABOVE the client's complaint band, which is where `rasp` lived.

    R2-4066: THE FIRING GEOMETRY MOVED, SO THE POSITIVE CONTROL MOVES WITH IT.
    B7 adopts the FIA Art. 5.2.10 three-journal crank, which forces uneven
    90/150 firing and halves the fundamental to engine order 1.5. Two firing
    sub-trains a quarter revolution apart multiply the comb by
    |1 + exp(-i*2*pi*m/4)| = 2|cos(pi*m/4)| at order m, so this control now
    carries that weighting -- and therefore carries the order-1.5 line and the
    order-6 null that G-IDENTITY gates.

    IT IS STILL SYNTHESISED HERE FROM THE ALGEBRA and does not import
    `audio.engine`. A positive control that is the render path is not a control;
    if the two ever disagree, C8 fails and the suite refuses to adjudicate,
    which is the outcome that should follow.
    """
    n = int(total_s * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)
    # incommensurate, all well below the 0.2 Hz edge of G-MOD's band
    # A REAL rpm hold still wanders, but only slowly: every drift rate here is
    # an order of magnitude below G-MOD's 0.2 Hz lower edge, and the depth is
    # small enough that intermodulation between them stays there too.
    wob = 1.0 + 0.003 * (np.sin(2 * np.pi * 0.017 * t) + 0.8 * np.sin(2 * np.pi * 0.029 * t)
                         + 0.6 * np.sin(2 * np.pi * 0.041 * t))
    f0 = order * rpm / 60.0 * wob
    ph = 2 * np.pi * np.cumsum(f0) / sr
    y = np.zeros(n)
    for k in range(1, 26):
        f = f0 * k
        if float(f.max()) > sr * 0.45:
            break
        m = order * k                       # engine order of this line
        # the quarter-revolution weighting: exactly 0 at order 6, 1 at order 12
        a_geom = abs(np.cos(np.pi * m / 4.0))
        # 1-2 % per-cylinder dispersion, so the null is deep but not infinite --
        # which is what a real engine's machining tolerance does to it
        a_geom = np.hypot(a_geom, 0.015)
        amp = (1.0 / k ** 1.15) * a_geom * float(rng.uniform(0.98, 1.02))
        y += amp * np.sin(k * ph + rng.uniform(0, 6))
    # turbine/compressor broadband, 4-13 kHz only: above the complaint band
    sos = _sig.butter(4, [4000.0, min(13000.0, sr * 0.45)], btype="bandpass",
                      fs=sr, output="sos")
    y = _norm(y, 1.0) + _norm(_sig.sosfilt(sos, rng.standard_normal(n)), 0.035)
    return _stereo(_norm(y, 0.10), _norm(np.roll(y, 0) * 0.98
                                         + 0.02 * _norm(diffuse_tail(y, sr, 0.4, 21), 1.0), 0.10))


# ========================================= C9: THE POSITIVE THAT WAS MISSING =
# R2-4081. C8b was the corpus's only beat-1 positive and R2-4081 measured what
# it actually is: 98.3 % of its power is a servo comb, its longest held pitch
# is 8.49 s, and the spread of its 20 ms level inside a 2 s window is 0.64 dB
# -- as stationary as white noise. It is a DRONE WITH CLICKS ON IT. Every
# beat-1 tonality bar in `percept.py` was anchored on it, and R2-4081's own
# check of the +8 dB HNR bar declared the bar validated because C8b cleared it
# by 24 dB. So the instrument that was supposed to prove the bars reachable was
# itself the thing the client rejected three times, and the gradient it defined
# pointed at R2-4079.
#
# C9 is the control that half of the corpus never had: PERCUSSIVE, INHARMONIC,
# TRANSIENT-DENSE, UNPITCHED, with structured non-white noise, on the film's
# own PICTURE-LOCKED contact schedule. Nothing in it sustains, and that is not
# a stylistic choice -- it is what "everything here is struck" means.

MATERIALS = (   # E (Pa), nu, rho (kg/m3): steel, aluminium, CFRP, magnesium
    (200e9, 0.30, 7850.0), (69e9, 0.33, 2700.0),
    (135e9, 0.30, 1600.0), (45e9, 0.29, 1780.0),
)


def ring_modes(a, h, E, rho, nu=0.30, fmax=8000.0, n_max=12):
    """Flexural modes of a thin free ring -- a tube's cross-section:

        f_n = n(n^2-1)/sqrt(n^2+1) * (1/2pi) * sqrt(E I / (rho A a^4))

    with I = h^3/12 and A = h per unit width (Love / Rayleigh thin-ring
    theory). The ratios are 1 : 2.83 : 5.42 : 8.73 : 12.4, which are not small
    integers and never will be. THIS IS WHY A STRUCK TUBE IS NOT A NOTE, and
    it is the reason an assembly cell can be dense with metallic resonance and
    still have no pitch: inharmonic partials do not fuse into one.
    """
    c = math.sqrt(E * h ** 2 / (12.0 * rho * (1.0 - nu ** 2))) / (2 * math.pi * a * a)
    out = []
    for n in range(2, n_max):
        f = c * n * (n * n - 1) / math.sqrt(n * n + 1)
        if 55.0 < f <= fmax:
            out.append((f, 1.0 / n))
    return out


def jet_exhaust(sr, dur_s, d_m, u_ms, seed, plenum_hz=None):
    """A pneumatic exhaust: turbulent jet noise, STRUCTURED and non-white.

    Lighthill scaling puts the peak at the Strouhal number St = f D / U ~ 0.2,
    rising as f^2 below it and falling as f^-2 above it. The shape IS the
    structure and it MOVES with the orifice diameter and the supply velocity,
    so no two exhausts in the cell print the same spectrum -- which is what
    keeps a bank of them from being one bed. A plenum Helmholtz resonance
    f_H = (c/2pi) sqrt(A/(V L)) is added at Q ~ 6, the valve opens in 2 ms and
    the line empties exponentially.
    """
    n = max(int(dur_s * sr), 64)
    rng = np.random.default_rng(seed)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    fp = 0.2 * u_ms / d_m
    r = np.where(f > 0, f / max(fp, 1e-6), 1e-6)
    mag = r ** 2 / (1.0 + r ** 4)
    y = np.fft.irfft(mag * np.exp(1j * rng.uniform(0, 2 * np.pi, len(f))), n)
    if plenum_hz:
        w0 = 2 * np.pi * plenum_hz / sr
        al = math.sin(w0) / (2 * 6.0)
        b = np.array([al, 0.0, -al]); a = np.array([1 + al, -2 * math.cos(w0), 1 - al])
        y = y + 0.8 * _sig.lfilter(b / a[0], a / a[0], y)
    t = np.arange(n) / sr
    return _norm(y * (1.0 - np.exp(-t / 0.002)) * np.exp(-t / (0.25 * dur_s)), 1.0)


def servo_move(sr, dur_s, w_max, teeth, seed, poles=4):
    """ONE PICK-AND-PLACE MOVE, under a trapezoidal velocity profile.

    THE THESIS OF THIS CONTROL, IN ONE FUNCTION. The shaft rate is zero at the
    start, zero at the end and constant for at most a third of the move, so
    gear mesh at teeth*w and the PMSM radial force at 2*poles*w are lines whose
    frequency is a multiple of a RATE THAT IS CHANGING. A machine is periodic
    in rhythm and never in pitch. C8b's servo bed holds one rate per cluster
    for seconds at a time, which is where its 8.49 s held note comes from; a
    real move does not hold anything.
    """
    n = max(int(dur_s * sr), 64)
    t = np.arange(n) / sr
    ta = dur_s * 0.35
    w = np.where(t < ta, w_max * t / ta,
                 np.where(t < dur_s - ta, w_max,
                          w_max * np.maximum(dur_s - t, 0.0) / ta))
    ph = 2 * np.pi * np.cumsum(w) / sr
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for k, amp in ((teeth, 0.55), (2 * teeth, 0.20), (2 * poles, 0.30),
                   (4 * poles, 0.12), (1, 0.10), (3, 0.06)):
        y += amp * np.sin(k * ph + rng.uniform(0, 6))
    # bearing and brush broadband, driven by the rate rather than added to it
    sos = _sig.butter(2, [700.0, 9000.0], btype="bandpass", fs=sr, output="sos")
    y = 0.75 * y + 0.25 * _sig.sosfilt(sos, rng.standard_normal(n)) * (w / max(w_max, 1e-9))
    return _norm(y * np.clip(w / max(w_max, 1e-9), 0.0, 1.0) ** 0.6, 1.0)


def nut_runner(sr, dur_s, rate_hz, seed):
    """A socket runner: a train of pawl impacts, 19-44 Hz, speeding up as the
    fastener seats. RHYTHM WITHOUT PITCH, stated as a gesture -- the impact
    rate is an order of magnitude below the lowest pitch this suite tracks and
    the socket's reply is a ring-mode set, which is inharmonic."""
    n = max(int(dur_s * sr), 64)
    rng = np.random.default_rng(seed)
    modes = ring_modes(0.016, 0.004, 200e9, 7850.0)
    x = np.zeros(n)
    t = 0.0
    while t < dur_s:
        i = int(t * sr)
        exc = _hertzian_pulse(sr, 0.05, 0.006, 60e9, float(rng.uniform(0.4, 1.2)))
        L = min(len(exc), n - i)
        if L > 2:
            x[i:i + L] += exc[:L] * float(rng.uniform(0.6, 1.0))
        t += (1.0 / rate_hz) * float(rng.uniform(0.85, 1.15))
        rate_hz *= 1.008
    return _norm(_modal_hit_from(sr, modes, x, 0.02, seed + 1), 1.0)


def _modal_hit_from(sr, modes, exc_full, eta, seed):
    """`_modal_hit` driven by an excitation that is already a full signal."""
    out = np.zeros(len(exc_full))
    rng = np.random.default_rng(seed)
    for f, w in modes:
        if f >= sr * 0.45:
            continue
        w0 = 2 * np.pi * f / sr
        al = math.sin(w0) / (2 * (1.0 / max(eta, 1e-4)))
        b = np.array([al, 0.0, -al]); a = np.array([1 + al, -2 * math.cos(w0), 1 - al])
        out += w * float(rng.uniform(0.85, 1.15)) * _sig.lfilter(b / a[0], a / a[0], exc_full)
    return out


def conveyor_bed(sr, n, seed):
    """Rolling contact: surface roughness through the Hertzian contact
    compliance, which is a broad resonance in the low hundreds of Hz, amplitude
    modulated at the roller passage rate. The rate drifts with the load, so the
    modulation is a rhythm and not a period."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / sr
    sos = _sig.butter(2, [45.0, 900.0], btype="bandpass", fs=sr, output="sos")
    y = _sig.sosfilt(sos, rng.standard_normal(n))
    rate = 9.0 + 1.6 * np.sin(2 * np.pi * 0.031 * t) + 0.9 * np.sin(2 * np.pi * 0.017 * t)
    return _norm(y * (1.0 + 0.45 * np.sin(2 * np.pi * np.cumsum(rate) / sr)), 1.0)


GOLDEN = (1.0 + 5.0 ** 0.5) / 2.0


def assembly_cell(sr=SR, total_s=BEAT1_S, seed=4090, n_waves=15, n_parts=470,
                  spread_s=2.2, n_jets=14, n_servos=28, n_runners=7):
    """C9 -- an assembly cell, and the beat-1 positive this corpus never had.

    THE CONTRACT THIS CONTROL EXISTS TO STATE:
      * ~580 contacts over 33 s -- the film's own order of magnitude (616
        first contacts plus 161 restitution bounces) -- so it is a control for
        a DENSE beat and not for a sparse one;
      * fifteen arrival waves on a golden-ratio low-discrepancy schedule, and
        the waves OVERLAP. The film's own uniform 1.0417 s ladder is a known
        G-MOD failure that no audio change can fix (R2-4080), so a control
        that copied it would inherit a failure that is a property of the
        picture. What is copied is the DENSITY, which is what this control is
        about;
      * every part its own geometry -- a plate from (a, b, h, E, nu, rho) or a
        tube from thin-ring theory -- so nothing replies at the same pitches
        twice;
      * Hertzian excitation, joint damping eta 0.02-0.15, so T60 is tens to
        hundreds of milliseconds and NOTHING RINGS INTO THE NEXT EVENT;
      * structured non-white noise from jet exhausts, not from a noise source:
        the spectrum has a Strouhal peak that moves with the orifice;
      * servo moves that GLIDE, never a servo that holds;
      * a velvet-noise late field well inside the declared Sabine RT60.

    MEASURED, over five seeds: G-SUSTAIN note cover 0.000, chord cover 0.000,
    held power share 0.0000 -- without exception, because there is nothing in
    it to hold a note. G-EVENT 35.8-37.4 dB against a 13.7 dB bar. Per-band
    SFM 1.03x white and Boersma HNR -5.3 dB, which is why the two bars that
    used to judge this beat are retired: this signal is what beat 1 should
    sound like and it fails both of them.
    """
    rng = np.random.default_rng(seed)
    n = int(total_s * sr)
    dry = np.zeros(n)
    n_contacts = 0

    # golden-ratio low-discrepancy wave times: no period at any scale, and no
    # two inter-wave gaps alike, so the modulation spectrum has no line to find
    wt = 1.2 + (total_s - 4.0) * np.sort(
        np.array([(i * GOLDEN) % 1.0 for i in range(n_waves)]))

    for pi in range(n_parts):
        w = int(rng.integers(0, n_waves))
        E, nu, rho = MATERIALS[int(rng.integers(0, len(MATERIALS)))]
        if rng.random() < 0.45:
            modes = ring_modes(float(rng.uniform(0.012, 0.075)),
                               float(rng.uniform(0.0012, 0.006)), E, rho, nu)
        else:
            modes = _plate_modes(float(rng.uniform(0.10, 1.5)),
                                 float(rng.uniform(0.08, 1.1)),
                                 float(rng.uniform(0.0012, 0.010)), E, nu, rho)
        if not modes:
            continue
        v = float(rng.uniform(0.6, 4.0))
        exc = _hertzian_pulse(sr, float(rng.uniform(0.15, 12.0)),
                              float(rng.uniform(0.01, 0.12)), 60e9, v)
        hit = _norm(_modal_hit(sr, modes, 0.40, float(rng.uniform(0.02, 0.15)),
                               seed + 31 * pi, exc), 1.0)
        # the part falls: t = sqrt(2h/g) from its own release height, so the
        # arrivals scatter instead of landing on the wave
        h = float(rng.uniform(0.15, 4.0))
        dt = float(rng.uniform(0.0, spread_s)) + \
            math.sqrt(2.0 * h / 9.81) * float(rng.uniform(0.9, 1.1))
        lev = float(rng.uniform(0.4, 1.0)) * min(v / 2.0, 1.4)
        bounces = ((0, 1.0), (1, 0.34)) if rng.random() < 0.26 else ((0, 1.0),)
        for k, amp in bounces:
            i = int((wt[w] + dt * (1 + 0.62 * k)) * sr)
            L = min(len(hit), n - i)
            if L > 16 and i >= 0:
                dry[i:i + L] += amp * lev * hit[:L]
                n_contacts += 1

    for e in range(n_jets):
        j = jet_exhaust(sr, float(rng.uniform(0.12, 0.5)),
                        float(rng.uniform(0.002, 0.008)),
                        float(rng.uniform(120.0, 310.0)), seed + 71 * e + 3,
                        plenum_hz=float(rng.uniform(180.0, 900.0)))
        i = int(float(rng.uniform(0.5, total_s - 1.0)) * sr)
        L = min(len(j), n - i)
        if L > 8:
            dry[i:i + L] += float(rng.uniform(0.05, 0.18)) * j[:L]
    for e in range(n_servos):
        mv = servo_move(sr, float(rng.uniform(0.25, 0.7)),
                        float(rng.uniform(60.0, 210.0)),
                        int(rng.integers(9, 27)), seed + 7 * e)
        i = int(float(rng.uniform(0.2, total_s - 1.0)) * sr)
        L = min(len(mv), n - i)
        if L > 8:
            dry[i:i + L] += float(rng.uniform(0.06, 0.16)) * mv[:L]
    for e in range(n_runners):
        rt = nut_runner(sr, float(rng.uniform(0.3, 0.9)),
                        float(rng.uniform(19.0, 44.0)), seed + 97 * e)
        i = int(float(rng.uniform(0.5, total_s - 1.5)) * sr)
        L = min(len(rt), n - i)
        if L > 8:
            dry[i:i + L] += 0.22 * rt[:L]

    src = _norm(dry, 1.0) + conveyor_bed(sr, n, seed + 5) * 0.03
    L = src + 0.05 * diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 11)
    R = src + 0.05 * diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 12)
    return np.stack([_norm(L, 0.09), _norm(R, 0.09)], axis=1), n_contacts


# ===================================================== the breach positive ==
# R2-4149. G-PRESENCE FAILS AT `3_breach` (AMI 0.1409) AND THE CORPUS COULD NOT
# SAY WHETHER THAT WAS THE AUDIO OR THE INSTRUMENT, because the AMI bar was
# derived from a corpus whose ONLY positive -- C9 -- is a beat-1 assembly cell.
# A bar validated on one beat and applied to another is a bar applied outside
# its own evidence, and R2-4148 said so and declined to chase the number.
#
# This is the missing half: what an 8 s glass breach sounds like when it is
# built from the fracture mechanics rather than from the film, so that the bar
# can be re-derived against a POSITIVE for the beat it is being applied to.
#
# EVERY NUMBER BELOW IS A DERIVATION, and the two that matter most are the two
# that make a glass shower different from every other event train in this file.
GLASS_E, GLASS_NU, GLASS_RHO = 70.0e9, 0.22, 2500.0
GLASS_CL = math.sqrt(GLASS_E / (GLASS_RHO * (1.0 - GLASS_NU ** 2)))   # 5424 m/s
# Toughened glass dices; the fragment side scales with the thickness and with
# the stored surface compression, and for 12 mm architectural toughened glass
# the dice are 10-25 mm. That is the FIRST number that matters, because it
# sets the ring frequency, and it puts it above 7 kHz.
GLASS_H = 0.012
# Crack front in soda-lime glass runs at roughly 0.5 of the Rayleigh speed,
# ~1500 m/s, so a 2.125 m panel dices in 1.4 ms: THE SHATTER IS ONE TRANSIENT,
# not a train. What is a train is what happens afterwards, on the floor.
CRACK_SPEED_MS = 1500.0


def _free_plate_modes(a_m, h_m, fmax=18000.0, n_max=6):
    """A FREE square plate of side `a_m`. f_11 = (lam^2 / 2 pi a^2) sqrt(D/rho h)
    with Leissa's lam^2 = 13.49 for the first mode of a completely free square
    plate, which reduces to 0.6198 * c_L * h / a^2. The higher modes follow the
    free-free ratios 1 : 1.49 : 2.36 : 2.96 : 4.14 -- not small integers, so a
    piece of broken glass has no pitch either.

    THE NUMBER THAT DECIDES WHAT A GLASS SHOWER IS, AND IT IS NOT THE ONE THIS
    CONTROL WAS FIRST WRITTEN WITH. A 15 mm dice of 12 mm toughened glass has
    NO AUDIBLE RESONANCE AT ALL: plate theory does not even apply to it (a/h =
    1.2), and the cube's own lowest elastic mode is a shear mode at c_s/2a =
    113 kHz. Only fragments above about 80 mm -- a/h >= 6.7 -- ring inside the
    audio band. So the tinkle of toughened glass is NOT the dice ringing. It is
    a quarter of a million HERTZIAN CONTACTS, each 30-70 us long and therefore
    broadband to 15-30 kHz, and the ring belongs to the few large pieces that
    come off the restrained edges. Returns nothing when plate theory does not
    apply, rather than returning an ultrasonic mode as if it were audible.
    """
    if a_m < 5.0 * h_m:
        return []
    f11 = 0.6198 * GLASS_CL * h_m / (a_m * a_m)
    out = []
    for r, w in ((1.0, 1.0), (1.49, 0.62), (2.36, 0.38), (2.96, 0.24),
                 (4.14, 0.13))[:n_max]:
        f = f11 * r
        if 55.0 < f <= fmax:
            out.append((f, w))
    return out


def _hertz_tau(m_kg, r_m, e_star, v_ms):
    """Hertzian contact duration, WITHOUT the assembly cell's 0.4 ms floor.

    `_hertzian_pulse` clamps tau to 0.4-2.5 ms and states why: for a part
    landing in a nest, anything shorter is a click and a click is a noise
    generator with a schedule. A GLASS DICE IS NOT THAT CASE. Its mass is
    6.8 grams, so tau comes out at 30-60 us and the clamp would be a factor of
    ten of invented contact time -- and it is exactly that short contact that
    puts the energy up where the fragment's own modes are. The only floor here
    is two samples, which is the rate's floor and not a physical claim.
    """
    v = np.maximum(np.asarray(v_ms, dtype=np.float64), 0.05)
    return 2.94 * (m_kg ** 2 / (r_m * e_star ** 2 * v)) ** 0.2


def _pulse(sr, tau_s):
    n = max(int(round(tau_s * sr)), 2)
    t = np.arange(n) / sr
    return np.sin(math.pi * t / (n / sr)) ** 1.5


def glass_breach(sr=SR, total_s=8.0, seed=6031, ramp=0.21,
                 aperture_wh=(9.6, 5.6), v_car_ms=53.8 / 3.6,
                 n_mullions=5, include=("dice", "slabs", "mullions", "room")):
    """C10 -- A CURTAIN WALL COMING DOWN, and the breach positive this corpus
    never had.

    THE PICTURE THIS IS A CONTROL FOR. `3_breach` is 8 s of SCREEN time in
    which world time ramps to 15-25 %, so roughly 1.7 s of world is stretched
    over the beat. That matters more here than anywhere else in the film,
    because it is the one thing that decides whether a glass shower is a train
    of events or a wash: SLOW MOTION SPREADS THE ARRIVALS AND DOES NOT SPREAD
    THE RINGS. A fragment's ring is 0.1-0.2 s of real time whatever the camera
    is doing; its arrival time is picture. Stretching one and not the other is
    the physics, and it is why the beat CAN be articulated at all.

    WHAT IS IN IT, ALL FROM THE APERTURE'S OWN GEOMETRY (9.6 x 5.6 m of 12 mm
    toughened glass, `docs/circuit_spec.json`):

      * THE SHATTER, WHICH IS **NOT** IN THE DEFAULT AND THAT IS THE POINT.
        One Hertzian contact of the car on the pane, exciting the whole
        panel's modes for the 1.4 ms it takes the crack front to cross it at
        1500 m/s, and then the panel is gone. At its own contact force it is
        40 dB over everything else in the beat, and a control containing it is
        a test of the limiter rather than of the beat: measured, it takes the
        gap sensation level from +12.28 dB to -9.50 dB and G-PRESENCE FAILS
        THE POSITIVE on its audibility limb. **G-PRESENCE judges the material
        BETWEEN the events**, and the car going through the pane is the event,
        not the material. So the default control is the SHOWER -- which is
        also the conservative choice, since including the transient takes AMI
        from 0.77 to 9.17. `include=("shatter", ...)` puts it back, and
        `tools/r2_4149_breach_bench.py` prints both.
      * THE DICE. 9.6 x 5.6 x 0.012 m of glass at 2500 kg/m3 is 1613 kg, and
        at a 15 mm dice that is 239 000 fragments. THEY ARE NOT ALL AUDIBLE AS
        EVENTS and this control does not pretend they are: at that count the
        arrivals are 24 us apart, which is four hundred times over the 100 Hz
        roughness boundary, so the fine dice are a WASH BY THE PHYSICS. They
        are rendered as what they are, and they have NO ring -- see
        `_free_plate_modes`. What they have is a 30-70 us Hertzian contact,
        band-limited only by the rate, high-passed by its own radiation
        (ka = 1 at c/2*pi*a, which is 3.6 kHz for a 15 mm dice).
      * THE ARRIVALS. A fragment released at height h reaches the floor at
        t = sqrt(2h/g), so a uniform release over 0-5.6 m gives an arrival
        density RISING LINEARLY to a hard cutoff at 1.07 s of world time --
        5.1 s of film at this ramp. The shower ends; it does not fade.
      * THE BOUNCES. Glass on concrete has a restitution near 0.65, so each
        arrival is a geometric train 2ve/g, 2ve^2/g, ... that converges in
        2ve/(g(1-e)) seconds. THIS IS THE ARTICULATION: the interval between
        one fragment's bounces sweeps down through the 4-100 Hz band by
        construction, and a chattering sequence is the one event train whose
        rate is set by physics rather than by a schedule.
      * THE SLABS. The pane does not dice uniformly at its edges: the strips
        held by the mullions come away in large pieces, 0.1-0.4 m across, which
        ring an octave or two lower and land SPARSELY. These are the events a
        listener actually resolves, and they are a hundredth of the mass.
      * THE MULLIONS. Steel box sections at 2.20 m centres, torn out of their
        fixings: thin-ring modes, low, inharmonic, long.
      * THE ROOM. `diffuse_tail`, the same velvet-noise late field C9 uses, at
        the showroom's own RT60.
    """
    rng = np.random.default_rng(seed)
    n = int(total_s * sr)
    dry = np.zeros(n)
    w_m, h_m = aperture_wh
    t_impact = 0.55                       # film seconds before the nose lands

    def film_t(world_t):
        """World seconds after the impact -> film seconds. The ramp is a
        constant fraction here; the film's own ramp moves, and a control that
        copied a moving ramp would be copying the artefact."""
        return t_impact + world_t / ramp

    # -- 1. THE SHATTER ----------------------------------------------------
    # The car's effective front mass into a 12 mm pane. The pane rings for the
    # 1.4 ms the crack takes to cross a 2.125 m panel and then it is not a
    # pane any more, so the modal decay is cut there rather than left to ring.
    pane = _plate_modes(2.125, h_m, GLASS_H, GLASS_E, GLASS_NU, GLASS_RHO,
                        fmax=12000.0)
    tau = _hertz_tau(180.0, 0.35, 45e9, v_car_ms)
    shatter = _modal_hit(sr, pane, 0.25, 0.02, seed + 1, _pulse(sr, tau))
    cut = int((2.125 / CRACK_SPEED_MS) / ramp * sr)
    shatter[cut:] *= np.exp(-np.arange(len(shatter) - cut) / (0.02 * sr))
    if "shatter" in include:
        i = int(t_impact * sr)
        L = min(len(shatter), n - i)
        # the pane's contact force sets the scale for the shatter as it does
        # for every fragment below: F = m v (1+e) / tau, e ~ 0 into a pane
        dry[i:i + L] += (180.0 * v_car_ms / tau) * \
            (shatter / max(np.abs(shatter).max(), 1e-12))[:L]

    # -- 2. THE FRAGMENT POPULATION ----------------------------------------
    # ONE SCALE FOR EVERYTHING BELOW. Every contact is scaled by its own peak
    # Hertzian force, m*v*(1+e)/tau, so the balance between the dice wash and
    # the large pieces is the mass distribution's and not a mix decision. That
    # matters here more than anywhere: the balance between a wash and a train
    # IS the quantity G-PRESENCE measures, so choosing it with a fader would be
    # choosing the answer.
    #
    # MASS IS CONSERVED. The pane dices everywhere except within a few dice of
    # a restraint, where the stored compression is lower and the glass comes
    # away in strips: the aperture holds five 2.125 x 5.6 m panels, each with a
    # 15.45 m perimeter, and a 0.15 m edge strip on that perimeter is 2.32 m2
    # of 11.9 m2 -- so 19 % of the AREA leaves in pieces above the dice size,
    # and the classes below carry that.
    mass_total = w_m * h_m * GLASS_H * GLASS_RHO
    classes = ((0.010, 0.22), (0.015, 0.38), (0.022, 0.15), (0.035, 0.06),
               (0.080, 0.07), (0.150, 0.06), (0.300, 0.06))
    n_frag_total = 0
    for L_m, frac in classes:
        big = L_m >= 5.0 * GLASS_H
        if (big and "slabs" not in include) or (not big and "dice" not in include):
            continue
        m_frag = GLASS_RHO * L_m * L_m * GLASS_H
        n_frag = max(int(mass_total * frac / m_frag), 1)
        n_frag_total += n_frag
        # release height uniform over the aperture -> t = sqrt(2h/g), so the
        # arrival density RISES LINEARLY and stops dead at sqrt(2H/g)
        hh = rng.uniform(0.0, h_m, n_frag)
        v0 = np.sqrt(2.0 * 9.81 * hh)
        train = np.zeros(n)
        e = rng.uniform(0.50, 0.75, n_frag)
        tk, vk = v0 / 9.81, v0.copy()
        for _k in range(5):
            idx = (film_t(tk) * sr).astype(np.int64)
            ok = (idx >= 0) & (idx < n) & (vk > 0.05)
            amp = (m_frag * vk * (1.0 + e)) / np.maximum(
                _hertz_tau(m_frag, L_m * 0.5, 45e9, vk), 1e-9)
            np.add.at(train, idx[ok], amp[ok])
            vk = vk * e
            tk = tk + 2.0 * vk / 9.81
        # ONE convolution with the class's contact pulse and ONE modal bank:
        # a linear resonator's response to a sum of impulses IS the sum of its
        # responses, so 239 000 fragments cost two filters, not 239 000.
        tau_c = float(_hertz_tau(m_frag, L_m * 0.5, 45e9,
                                 float(np.median(v0))))
        train = _sig.fftconvolve(train, _pulse(sr, tau_c))[:n]
        # RADIATION. A source smaller than a wavelength does not radiate: the
        # monopole efficiency rises as (ka)^2 and reaches 1 at ka = 1, i.e. at
        # c / (2 pi a). For a 15 mm dice that is 3.6 kHz, which is why a glass
        # shower is all top end and why the dice cannot be a rumble.
        f_rad = min(343.0 / (2.0 * math.pi * (L_m * 0.5)), sr * 0.45)
        train = _sig.sosfilt(_sig.butter(1, f_rad, btype="highpass", fs=sr,
                                         output="sos"), train)
        modes = _free_plate_modes(L_m, GLASS_H)
        if modes:
            # glass eta is 0.001-0.002; a piece landing flat on concrete and
            # staying there is contact-damped an order above that
            train = train + 2.5 * _modal_hit_from(
                sr, modes, train, 0.006, seed + 17 + int(L_m * 1000))
        dry += train

    # -- 3. THE MULLIONS ---------------------------------------------------
    # Steel box sections at 2.20 m centres, torn out of their fixings. Low,
    # inharmonic, long, and scaled on the same force basis as everything else.
    for k in range(n_mullions if "mullions" in include else 0):
        modes = ring_modes(float(rng.uniform(0.05, 0.09)),
                           float(rng.uniform(0.003, 0.006)), 200e9, 7850.0)
        if not modes:
            continue
        v = v_car_ms * 0.5
        tau_m = float(_hertz_tau(40.0, 0.05, 60e9, v))
        hit = _modal_hit(sr, modes, 1.2, 0.004, seed + 401 + k,
                         _pulse(sr, tau_m) * (40.0 * v / tau_m))
        i = int(film_t(float(rng.uniform(0.0, 0.35))) * sr)
        Lp = min(len(hit), n - i)
        if Lp > 16 and i >= 0:
            dry[i:i + Lp] += hit[:Lp]

    src = _norm(dry, 1.0)
    wet = 0.06 if "room" in include else 0.0
    Lc = src + wet * diffuse_tail(src, sr, rt60_s=2.0, seed=seed + 11)
    Rc = src + wet * diffuse_tail(src, sr, rt60_s=2.0, seed=seed + 12)
    return np.stack([_norm(Lc, 0.09), _norm(Rc, 0.09)], axis=1), n_frag_total


BREACH_SHEET = {"beats": [{"name": "3_breach", "start_s": 0.0}]}


# ================================================================ registry ==
def _read_master(path=MASTER_WAV):
    import soundfile as sf                                  # noqa: PLC0415
    x, sr = sf.read(path, always_2d=True)
    return np.asarray(x, dtype=np.float64), int(sr)


def _c1(_):
    x, sr = _read_master()
    n = int(BEAT1_S * sr)
    y = octave_matched_noise(x[:n], sr)
    return _stereo(_norm(y, 0.08), _norm(np.roll(y, 211), 0.08)), sr, BEAT1_SHEET, None


def _c2(_):
    return tiled_loop(), SR, BEAT1_SHEET, None


def _c3(_):
    # presented AS AN ENGINE at a declared constant rpm, so G-ORDER is
    # applicable and can say the thing that matters: these peaks are strong,
    # narrow, and they do not move with the telemetry.
    return blower_plus_tubes(), SR, LAP_SHEET, "constant_rpm"


def _c4(_):
    x, sr = _read_master()
    return x, sr, None, "film"


def _c5(_):
    """The file that passes all eight OLD gates. Regenerated from the master if
    the audit's copy has been swept, so the corpus survives a clean tmp/."""
    if os.path.exists(SWAP_B1_LOOP_WAV):
        import soundfile as sf                              # noqa: PLC0415
        x, sr = sf.read(SWAP_B1_LOOP_WAV, always_2d=True)
        return np.asarray(x, float), int(sr), None, "film"
    x, sr = _read_master()
    y = x.copy()
    loop = tiled_loop(sr, BEAT1_S)
    n = min(int(BEAT1_S * sr), y.shape[0])
    scale = float(np.sqrt(np.mean(y[:n] ** 2)) / max(np.sqrt(np.mean(loop[:n] ** 2)), 1e-12))
    y[:n] = loop[:n] * scale
    xf = int(0.020 * sr)
    r = np.linspace(0, 1, xf)[:, None]
    y[n - xf:n] = y[n - xf:n] * (1 - r) + x[n - xf:n] * r
    return y, sr, None, "film"


def _c6(_):
    return jittered_identical_gestures(), SR, BEAT1_SHEET, None


def _c7(_):
    """R2-4081: PRESENTED AT THE LAP, NOT AT BEAT 1.

    C7 exists to prove that a broad spectral tilt cannot hide flatness from
    G-FLAT's per-band construction -- the whole-band SFM reads a reassuring
    0.0142 on the delivered master and that is what let it ship. G-FLAT is an
    engine-beat instrument from R2-4081 on, so a control aimed at G-FLAT has to
    be presented at a beat G-FLAT judges, or it proves nothing about the gate
    and only proves that the gate declined to look. The 33 s taken is the film's
    own lap (t = 49.6 s, beat 5), which is the beat the client called a hair
    blower, and the tilt is added to it exactly as before."""
    x, sr = _read_master()
    a = int(49.6 * sr)
    n = int(BEAT1_S * sr)
    return spectral_tilt(x[a:a + n], sr), sr, LAP_SHEET, None


def _c8(_):
    return constant_rpm_pu(), SR, LAP_SHEET, "constant_rpm"


def _c8b(_):
    return physical_showroom_beat(), SR, BEAT1_SHEET, None


def _c9(_):
    return assembly_cell()[0], SR, BEAT1_SHEET, None


# name -> (builder, required verdict, gates it MUST trip, one-line what-it-is)
CONTROLS = {
    # R2-4081 MOVED THIS CONTRACT AND DID NOT WEAKEN IT. C1 is presented at
    # beat 1, where G-FLAT and G-HNR no longer have an opinion -- so requiring
    # it to trip them would require the suite to answer a question it has been
    # shown it cannot answer for percussive material. What must catch a hair
    # dryer at beat 1 is G-EVENT, and C1 is now the control that says so: 4.70
    # dB of local dynamic range against a 13.7 dB bar. The spectral instruments
    # keep their own hair dryer at an engine beat -- C3, which declares
    # constant-rpm telemetry and must still trip both.
    "C1_octave_matched_noise": (
        _c1, "FAIL", ("G-EVENT",),
        "octave-matched filtered noise -- the literal hair dryer"),
    "C2_tiled_loop": (
        _c2, "FAIL", ("G-NOVEL", "G-MOD", "G-GESTURE"),
        "one 2.000 s block tiled to length"),
    "C3_blower_plus_tubes": (
        _c3, "FAIL", ("G-ORDER", "G-ROOM"),
        "noise through high-Q inharmonic pipes -- the client's exact words"),
    "C4_delivered_master": (
        _c4, "FAIL", ("G-NOVEL", "G-MOD", "G-GESTURE", "G-ROOM", "G-FLAT"),
        "THE DELIVERED, REJECTED MASTER, retained permanently"),
    "C5_swap_b1_loop": (
        _c5, "FAIL", ("G-NOVEL",),
        "the file that passes all eight OLD gates, ALL_PASS=True, exit 0"),
    "C6_jittered_identical_gestures": (
        _c6, "FAIL", ("G-GESTURE",),
        "ANTI-CHEAT: same gesture, jittered grid -- must PASS G-MOD"),
    "C7_master_plus_tilt": (
        _c7, "FAIL", ("G-FLAT",),
        "ANTI-CHEAT: delivered master + a broad spectral tilt"),
    "C8_constant_rpm_pu": (
        _c8, "PASS", (),
        "physics-true positive: a power unit at constant rpm"),
    # C8b WAS A POSITIVE UNTIL R2-4081 MEASURED IT. The signal is unchanged and
    # deliberately so -- what changed is the claim made about it, and it changed
    # because of numbers, not taste: 98.3 % of its power is a servo comb
    # (R2-4081's own dry-gain sweep), its longest held pitch is 8.49 s, three or
    # more pitches are held at once for 58 % of the beat, and the spread of its
    # 20 ms level inside a 2 s window is 0.64 dB, which is white noise's 0.65.
    # It is the CHEAPEST SIGNAL THAT SATISFIES THE OLD BEAT-1 BARS -- +32.21 dB
    # Boersma against a +8 dB bar, 0.389x white against a 0.45x bar -- and the
    # client rejected the master that was built toward those bars. So it takes
    # C7's role at a different gate: the control that proves the suite cannot be
    # bought by holding a note.
    "C8b_tonal_showroom_drone": (
        _c8b, "FAIL", ("G-SUSTAIN", "G-EVENT"),
        "ANTI-CHEAT: the cheapest signal that clears the OLD beat-1 tonality "
        "bars -- 98.3 % sustained tone by power, formerly this corpus's only "
        "beat-1 positive"),
    "C9_assembly_cell": (
        _c9, "PASS", (),
        "physics-true positive: an assembly cell on the film's own "
        "picture-locked contact schedule -- percussive, inharmonic, "
        "transient-dense, unpitched"),
}

# C6 must PASS these even though its overall verdict is FAIL. This is the
# anti-cheat contract, written down and machine-checked.
MUST_PASS_GATES = {
    "C6_jittered_identical_gestures": ("G-MOD",),
}

# ===================================== DECLARED OPEN, WITH THE MEASUREMENT ==
# R2-4081. A gate listed here does not count toward a control's verdict, and
# every run PRINTS the entry and writes it into the report. This exists for one
# situation and it is not "the control does not pass yet": it is
#
#   A BAR THAT THE INSTRUMENT'S OWN NULL ALREADY EXCEEDS.
#
# A bar below the chance level of its own statistic cannot be met by anything,
# so a control failing it is not evidence about the control. The alternative --
# moving the bar -- is a change to a gate this pass was not sent to re-derive,
# on evidence gathered while doing something else, and R2-4081 declines to make
# it quietly. The entry is the work item, with the numbers to start from.
#
# THE RULE, so this cannot become a dumping ground: an entry is only admissible
# with a MEASURED null for the limb in question, quoted in the reason. No
# entry may be added because a control "nearly" passes.
OPEN = {
    "C9_assembly_cell": {
        "G-ROOM": (
            "LIMB (c) ONLY, and both of its bars sit under their own floors. "
            "(1) The cepstral bar is 1.5x peak-over-median. Measured through "
            "the shipped tail-spectrum path on material that contains NO DELAY "
            "OF ANY KIND -- thirteen struck plates, each its own geometry, no "
            "room, no reverb, nothing summed with a copy of itself -- the "
            "reading is 10.44x, and thirteen filtered noise bursts with no "
            "modes at all read 25.28x. A real 1.333 ms delayed copy of the "
            "same material reads 78-206x, so the statistic does separate an "
            "echo from no echo by an order of magnitude; it is the BAR that "
            "is an order of magnitude below the no-echo case. C9 reads 5.91x, "
            "which is BELOW the no-delay null and above the bar. (2) The "
            "ripple bar is 8.0 dB p95-p5 over 1/12-octave bands, and R2-4067 "
            "already recorded in this repo that a diffuse field's transfer "
            "function is Rayleigh-distributed with a p95-p5 of 17.7 dB BY "
            "CONSTRUCTION. C9's tails read 10.45 dB. A bar of 8 dB asks a "
            "diffuse late field to be less rippled than diffuseness permits. "
            "R2-4081 measured both and moved NEITHER: re-deriving G-ROOM was "
            "not this pass's remit and it needs its own, with C9 and a "
            "delayed-copy pair as the two-sided anchor. Limbs (a) and (b) are "
            "unaffected, are still gated on this control, and it passes both."
        ),
    },
}

# THE STEM RUN EACH CONTROL OWNS, IF IT OWNS ONE (R2-4079).
# `tools.percept_matrix._stems` used to hand a hard-coded `audio/out/stems` to
# EVERY signal that declared film telemetry, so C5 -- whose whole first beat is
# a tiled loop -- was scored on the delivered master's stems, and so was every
# new master ever adjudicated. A stem run belongs to exactly ONE rendered wav.
# C4 IS the delivered master, so `audio/out/stems` is genuinely its own. C5
# replaced beat 1 of that master with a synthesised loop, so no stem run
# corresponds to it and G-BALANCE on it is INAPPLICABLE, which is not a PASS
# and is not a regression: C5 exists to trip G-NOVEL.
CONTROL_STEMS = {
    "C4_delivered_master": os.path.join(ROOT, "audio", "out", "stems"),
}


def build(name):
    fn, required, trips, what = CONTROLS[name]
    x, sr, sheet, tel = fn(None)
    return {"name": name, "x": x, "sr": sr, "sheet": sheet, "telemetry_kind": tel,
            "required_verdict": required, "must_trip": trips, "what": what,
            "stems_dir": CONTROL_STEMS.get(name),
            "must_pass": MUST_PASS_GATES.get(name, ()),
            "open": OPEN.get(name, {})}


def build_all():
    return [build(k) for k in CONTROLS]
