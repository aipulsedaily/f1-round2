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
    x, sr = _read_master()
    n = int(BEAT1_S * sr)
    return spectral_tilt(x[:n], sr), sr, BEAT1_SHEET, None


def _c8(_):
    return constant_rpm_pu(), SR, LAP_SHEET, "constant_rpm"


def _c8b(_):
    return physical_showroom_beat(), SR, BEAT1_SHEET, None


# name -> (builder, required verdict, gates it MUST trip, one-line what-it-is)
CONTROLS = {
    "C1_octave_matched_noise": (
        _c1, "FAIL", ("G-FLAT", "G-HNR"),
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
    "C8b_physical_showroom_beat": (
        _c8b, "PASS", (),
        "physics-true positive: a beat 1 built the way the spec says to"),
}

# C6 must PASS these even though its overall verdict is FAIL. This is the
# anti-cheat contract, written down and machine-checked.
MUST_PASS_GATES = {
    "C6_jittered_identical_gestures": ("G-MOD",),
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
            "must_pass": MUST_PASS_GATES.get(name, ())}


def build_all():
    return [build(k) for k in CONTROLS]
