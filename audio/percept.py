"""Percept gates -- the instruments that replace the eight that passed three
rejected masters.

WHY THIS FILE EXISTS, IN ONE PARAGRAPH
======================================
The client rejected three audio masters. All eight gates in `verify.py` passed
every single time. The audit (docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md)
proved the gates could not have done otherwise:

  * A literal wind blower pointed into a rack of tubes PASSES the old beat-1
    harmonic gate with MORE margin than the delivered master (+4.04 dB at Q=80,
    above the gate's own 2.0 dB ENGINE bar).
  * Beat 1 replaced by one 2.000 s block tiled 16.5x passes all eight gates,
    ALL_PASS=True, exit 0 -- and the harmonic gate rates that loop 35.9 dB
    BETTER than the film it passed.
  * `hnr_profile` had no f0 estimate and no harmonicity test. Its own docstring
    said so. It subtracted a 269.5 Hz running median and called everything above
    it "tonal". Noise through any resonator has narrow peaks.
  * Every threshold was "the midpoint between what THIS master reads and what
    the adversary reads" (verify.py:816). A gate calibrated on the defect cannot
    fail the defect.

THE THREE RULES THIS FILE ENFORCES IN CODE, NOT IN PROSE
========================================================
1. THREE SEPARATE INSTRUMENTS WHERE THERE WAS ONE NUMBER. `harmonic` collapsed
   flatness, harmonicity and order structure into a single median. G-FLAT,
   G-HNR and G-ORDER measure them separately and are gated separately. That
   collapse was the original mistake and it is not repeated.

2. EVERY THRESHOLD CARRIES A MACHINE-CHECKED `source`. `audit_thresholds()`
   REJECTS any threshold whose source is not in {physics, published,
   control-derived}. `artefact` is banned in writing: the self-referential rule
   at verify.py:816 is the defect, and a threshold derived from the master under
   test cannot be shipped from this module.

3. INAPPLICABLE IS NOT PASS. A gate that cannot measure a beat says so, and an
   INAPPLICABLE row never contributes to a verdict. The old harmonic gate on
   pure noise reported `failures: []` -- "I cannot measure this", never "this is
   noise" -- and that read as green.

WHAT IS DELIBERATELY NOT HERE
=============================
No threshold in this file was read off `audio/out/master.wav`. Where a bar needs
an empirical anchor it is measured, at run time, against SYNTHESISED controls in
`audio.controls` -- one that must pass and one that must fail -- and the anchor
values are written into the report so the placement is auditable. Two
instruments (G-HNR, G-FLAT) re-calibrate themselves against synthetic mixtures
of KNOWN noise fraction on every invocation, so the instrument re-validates
itself each time rather than being trusted from a note written once.
"""

from __future__ import annotations

import ast
import json
import math
import os
from dataclasses import dataclass

import numpy as np
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.dirname(os.path.abspath(__file__))

PASS = "PASS"
FAIL = "FAIL"
INAPPLICABLE = "INAPPLICABLE"

QUALITY = "quality"
PROVENANCE = "provenance"

# The only sources a threshold may claim. `artefact` is not in this set and
# never will be -- see rule 2 above. CI calls `audit_thresholds()` and a
# violation is a hard error, not a warning.
SOURCES_ALLOWED = ("physics", "published", "control-derived")

# THE FIRING ORDER THE SUITE PREDICTS LINES FROM.
#
# B7 (R2-4066) adopts the FIA Art. 5.2.10 three-journal geometry, which forces
# uneven 90/150 firing and HALVES the firing fundamental from engine order 3 to
# order 1.5. Every gate that predicts a line from telemetry rpm has to move with
# it or it looks for a comb that is not there.
#
# This constant is DELIBERATELY NOT IMPORTED FROM `audio.engine`. A judge that
# reads its ground truth out of the thing it is judging cannot fail it -- that is
# the same defect as `verify.py:816`'s "the limit is the midpoint between what
# THIS master reads and what the adversary reads", pointed at a different
# quantity. The two are derived independently from the same regulations and are
# expected to agree; if they ever disagree, G-ORDER and G-IDENTITY both fail and
# say so, which is the correct outcome.
ENGINE_FIRING_ORDER = 1.5


@dataclass(frozen=True)
class Threshold:
    key: str
    value: float
    units: str
    source: str
    note: str

    def as_dict(self):
        return {"key": self.key, "value": self.value, "units": self.units,
                "source": self.source, "note": self.note}


def _T(key, value, units, source, note):
    t = Threshold(key, float(value), units, source, note)
    THRESHOLDS[key] = t
    return t


THRESHOLDS: dict[str, Threshold] = {}

# ---------------------------------------------------------------- G-FLAT ----
# Tilt-free per-band spectral flatness against white through the identical
# pipeline. The whole-band SFM reads a reassuring 0.0142 on the delivered
# master -- that number is measuring the mix's LOW-FREQUENCY TILT, not its
# tonality, and it is what let this ship. SFM is therefore computed INSIDE each
# 1/3-octave band and then averaged, so tilt cannot contaminate it (C7 is the
# control that proves this).
_T("G_FLAT.slice_max_ratio_of_white", 0.55, "SFM / SFM(white)", "control-derived",
   "TWO-SIDED, from synthesised controls only, all measured per 3 s slice on "
   "the shipped estimator: the constant-rpm power unit C8 worst slice 0.127; "
   "octave-matched noise 0.721; blower-into-tubes 0.661; tiled loop 0.700; the "
   "delivered master 0.973. 0.55 clears the positive by 4.3x and sits 17 % "
   "under the nearest negative. R2-4081 REPLACED THE POSITIVE ANCHOR: it was "
   "C8b's 0.496 worst slice, and C8b is 98.3 % sustained tone by power, so it "
   "anchored a tonality bar with a drone. The bar is unchanged at 0.55 and its "
   "DOMAIN is now engine beats only -- see g_flat's docstring for the "
   "measurement that forced that, and G-EVENT for what judges the rest.")

# ---------------------------------------------------------------- G-HNR -----
# Boersma (1993) autocorrelation harmonic-to-noise ratio: the textbook HNR,
# implemented in-repo so no GPL dependency enters the shipped package. The
# instrument is re-calibrated against synthetic mixtures on EVERY invocation.
_T("G_HNR.calibration_max_error_db", 0.5, "dB", "published",
   "Boersma 1993 (IFA Proc. 17:97-110). The published method is exact on a "
   "harmonic-plus-noise mixture; 0.5 dB is the tolerance this implementation "
   "must hold against truths computed from the mixture coefficients. The "
   "diagnosis measured <=0.22 dB, so this is a loose guard on the INSTRUMENT, "
   "not on any film.")
_T("G_HNR.fraction_below_zero_max", 0.10, "fraction of windows", "physics",
   "0 dB is equal harmonic and aperiodic power -- the definition, not a "
   "calibration. A window below it carries more noise than signal. Applied to "
   "ENGINE BEATS ONLY since R2-4081: a power unit that spends a tenth of a "
   "beat with more noise than firing in it is a defect, and a struck plate "
   "below the same line is a struck plate.")

# --------------------------------------------------------------- G-ORDER ----
_T("G_ORDER.min_energy_on_predicted_lines", 0.60, "fraction of 300-4000 Hz energy",
   "control-derived",
   "The predicted comb is f = order*k*rpm/60 with rpm from TELEMETRY, which is "
   "independent ground truth, Doppler-shifted by the same retarded-time solve "
   "the mix was rendered with. Anchored between a synthesised constant-rpm "
   "power unit (which must clear it) and noise through fixed inharmonic pipes "
   "(which must not, because its peaks do not move with rpm).")
_T("G_ORDER.line_tolerance_pct", 1.5, "percent of line frequency", "physics",
   "+-1.5 % is 26 cents, under a quarter of a semitone, and comfortably wider "
   "than the 0.5 % rpm resolution of the telemetry solve across one analysis "
   "window. Set by the measurement's own resolution, not by any film's score.")

# ------------------------------------------------------------ G-IDENTITY ----
# SPECIFIED IN THE SPEC AND ABSENT FROM THE SUITE UNTIL NOW, and R2-4053 said
# so rather than shipping it as a row that could only fail: it gates the
# order-1.5 line and the order-6 notch, and both exist only once B7's
# `half_order_weight` does. B7 landed at R2-4066, so it lands here.
#
# THE DERIVATION, IN FULL, BECAUSE THE BARS ARE DERIVED AND NOT MEASURED.
# FIA 2025 Art. 5.2.10 permits three con-rod journals; Art. 5.2.7 fixes a
# 90-degree vee. Two cylinders per journal in a 90-degree vee are forced 90
# degrees apart in crank angle, and the three journals sit 120 degrees apart, so
# the six firings land at 0/90, 240/330, 480/570 -- a pattern of period 240
# degrees, i.e. two thirds of a revolution, so the firing fundamental is engine
# ORDER 1.5. The pattern is two pulses a quarter revolution apart, so the
# even-fired comb is multiplied by |1 + exp(-i*2*pi*m/4)| = 2|cos(pi*m/4)| at
# order m:
#
#   order   1.5    3.0    4.5    6.0    7.5    9.0   12.0
#   A(m)   0.383  0.707  0.924  0.000  0.924  0.707  1.000
#
#   20*log10(A(1.5)/A(3.0)) = -5.34 dB      order 6 is an EXACT null
#
# NO MEASURED F1 SPECTRUM WAS OBTAINABLE to corroborate any of this -- every
# publisher returned 403 -- so both bars are deliberately loose and both are
# marked DERIVED-NOT-MEASURED. What they test is that the geometry is PRESENT
# and has the right sign, not that its depth is exactly the algebra's.
_T("G_IDENTITY.half_order_min_db_rel_order3", -12.0, "dB re order 3", "physics",
   "The half order must be PRESENT. Derived value is -5.34 dB from "
   "20*log10(cos(0.375*pi)/cos(0.75*pi)); the bar sits 6.7 dB below it because "
   "a shared turbine collector genuinely attenuates the half order (engine.py's "
   "own `_collector_tail` argues this) and the pipe response at order 1.5 is not "
   "the pipe response at order 3. An evenly-fired engine reads MINUS INFINITY "
   "here -- its order-1.5 amplitude is identically 0.0000, verified to 1e-12 -- "
   "so this bar separates the two geometries and nothing else. "
   "DERIVED-NOT-MEASURED.")
_T("G_IDENTITY.half_order_max_db_rel_order3", 6.0, "dB re order 3", "physics",
   "The other side, and it is the one that matters for a false pass: a half "
   "order LOUDER than the main order is not a 90/150 V6, it is a V6 firing "
   "three times per two revolutions, i.e. a broken engine or an octave error in "
   "whatever produced it. Derived value -5.34 dB, so this is 11.3 dB of "
   "headroom above the algebra. DERIVED-NOT-MEASURED.")
_T("G_IDENTITY.min_order6_notch_db", 6.0, "dB below the mean of orders 4.5/7.5",
   "physics",
   "The order-6 null is EXACT in the algebra -- A(6) = |cos(1.5*pi)| = 0 -- and "
   "it is the one feature no static EQ can fake, because the notch frequency is "
   "6*rpm/60 and slides with the crank. It cannot be infinitely deep in a real "
   "render: 1-2 % per-cylinder timing and charge dispersion fills it in, the "
   "analysis window has finite resolution, and the neighbouring orders leak. "
   "6 dB is the depth that survives all three and is still unambiguous against "
   "a comb that has no notch at all, where the ratio is 0 dB by construction. "
   "DERIVED-NOT-MEASURED.")
_T("G_IDENTITY.line_present_db_over_floor", 6.0, "dB over the local floor",
   "control-derived",
   "A reference order that is not itself a line cannot anchor a ratio. 6 dB of "
   "excess over the median of a +-25 % neighbourhood is the point at which the "
   "band carries four times its own floor's power, which the synthesised "
   "constant-rpm control clears by more than 50 dB and filtered noise cannot "
   "reach at all. Applied to orders 3 / 4.5 / 7.5 only: order 6 is REQUIRED to "
   "be absent and gating on its presence would invert the test.")
_T("G_IDENTITY.min_windows", 8.0, "windows", "control-derived",
   "Fewer than eight 0.5 s windows on throttle with a telemetry rpm is not a "
   "measurement, and asserting an identity defect from a measurement that did "
   "not happen is the same error as calling an unmeasurable beat a pass. Below "
   "this the beat is INAPPLICABLE, which is not PASS.")

# ---------------------------------------------------------------- G-RING ----
_T("G_RING.t60_vs_sabine_max_ratio", 1.25, "ratio", "physics",
   "Sabine RT60 = 0.161*V/(S*alpha) for the DECLARED showroom (30 x 22 x 6.5 m, "
   "V = 4290 m3, S = 1996 m2) at the absorption the design declares. No band "
   "may ring longer than the room it claims to be. 1.25 is measurement "
   "tolerance on a backward-integrated decay slope. The delivered master rang "
   "at T60 3.0-4.6 s against a declared 2.4 s -- ratio 1.25-1.92.")
_T("G_RING.narrowband_vs_broadband_max_ratio", 1.5, "ratio", "physics",
   "A diffuse field decays uniformly across frequency. A 1/6-octave band that "
   "decays slower than the broadband envelope is by definition an "
   "under-damped isolated mode -- a pipe, not a room. 1.5 is measurement "
   "tolerance; the physics bar is 1.0.")

# --------------------------------------------------------------- G-NOVEL ----
_T("G_NOVEL.max_envelope_autocorrelation", 0.15, "Pearson r", "control-derived",
   "40-band log-spectrum envelope at 100 Hz, per-band normalised, lags "
   "0.3-16 s. Anchored on two SYNTHESISED endpoints measured every run: "
   "filtered noise (no repetition) and a 2 s block tiled to length (pure "
   "repetition). The bar sits near the noise anchor, not at the midpoint -- "
   "midpoint placement is the banned rule.")
_T("G_NOVEL.lag_min_s", 0.30, "s", "physics",
   "Below 0.3 s an envelope correlation is measuring a single event's own "
   "shape, not a repeat of it.")
_T("G_NOVEL.lag_max_s", 16.0, "s", "physics",
   "Half the shortest gated beat, so every reported lag has at least two "
   "cycles inside the beat.")
_T("G_NOVEL.min_peak_prominence", 0.05, "Pearson r", "physics",
   "A correlation maximum that is not a LOCAL maximum is a trend, not a "
   "period. Slow drift makes r decay monotonically from lag 0, and reading "
   "max(r) over the range then returns r(lag_min) -- 0.726 on a constant-rpm "
   "power unit with nothing repeating in it. Only prominent local maxima are "
   "candidates; a signal with none scores zero by definition, not by threshold.")

# ----------------------------------------------------------------- G-MOD ----
_T("G_MOD.max_peak_over_local_median_db", 6.0, "dB", "control-derived",
   "Modulation-spectrum peak-to-local-median over 0.2-3 Hz. The bar must sit "
   "ABOVE the jittered-gesture anti-cheat control (C6, which must PASS G-MOD "
   "and fail only G-GESTURE) and BELOW the exact tiled loop (C2). Both anchors "
   "are synthesised and both are re-measured every run; if they ever cross, "
   "the gate reports a calibration failure instead of a verdict. The spec's "
   "provisional 4 dB was raised to 6 dB by that measurement -- documented, "
   "not quietly retuned, and moved by a CONTROL, never by a master.")

# ------------------------------------------------------------- G-GESTURE ----
_T("G_GESTURE.max_mean_pairwise_similarity", 0.55, "Pearson r", "control-derived",
   "Burst-to-burst timbral distinctness. Anchored between a synthesised "
   "identical-gesture control (r -> 1) and a synthesised distinct-gesture "
   "control (independent modal sets per burst).")
_T("G_GESTURE.max_worst_pairwise_similarity", 0.80, "Pearson r", "control-derived",
   "No two bursts in the film may be near-copies of each other even if the "
   "mean is respectable.")

# ---------------------------------------------------------------- G-ROOM ----
_T("G_ROOM.max_fixed_line_comb_regularity", 0.40, "fraction over chance",
   "control-derived",
   "Modal density, measured the only way a rendered mix permits. Weyl's law "
   "gives 4*pi*V*f^2/c^3 = 1336 modes/Hz at 1 kHz for V = 4290 m3, which no "
   "audio analysis can COUNT -- at 1 Hz FFT resolution the ceiling is ~0.5 "
   "resolvable peaks/Hz. The executable equivalent: a delay-line bank's fixed "
   "lines are HARMONICS OF A DELAY LENGTH (the delivered master's thirteen "
   "strongest matched to 0.01-0.93 %), and a diffuse field has no such "
   "structure. Two-sided anchor: an 8-tap FDN scores near 1 and five "
   "inharmonic pipes -- also fixed, also narrow -- score at chance. DEVIATION "
   "FROM SPEC, DECLARED: the spec's '20 dB of Weyl' bar is not measurable on a "
   "mix; the Weyl number is reported for reference and this is what is gated.")
_T("G_ROOM.max_bursts", 16.0, "bursts", "control-derived",
   "R2-4081. THE RECURRENCE STATISTIC IS A BIRTHDAY PROBLEM and its chance "
   "level was never measured. On INDEPENDENT log-uniform peaks -- peaks that "
   "by construction share nothing -- it reads 0.031 at 8 bursts, 0.162 at 12, "
   "0.277 at 20, 0.638 at 40 and 0.835 at 60, against a 0.35 bar. Any beat "
   "dense enough to produce forty bursts therefore fails limb (b) whatever it "
   "sounds like, which is what the physics-true assembly cell C9 was doing at "
   "0.666 and what the film's own beat 1 was doing at 0.600. Sixteen holds the "
   "chance level near 0.22 while leaving the delivered master at 0.570 and the "
   "fixed-resonator mutation at 0.375, so nothing that should fire stops "
   "firing. The bar itself is UNCHANGED and was not touched.")
_T("G_ROOM.max_peak_recurrence", 0.35, "fraction of peak observations", "control-derived",
   "Mobility. Whatever you strike, the room must not reply at the same pitches. "
   "Per-burst top-8 peaks, recurrence at 1 % tolerance across >=3 bursts. "
   "Anchored between a synthesised position-varying room (scatters) and a "
   "synthesised fixed high-Q resonator bank (does not).")
_T("G_ROOM.max_cepstral_peak_over_median", 1.5, "ratio", "control-derived",
   "Ripple, quefrency 1-30 ms. Summing a signal with a delayed copy of itself "
   "prints a cepstral peak AT the delay; absent one the cepstrum is flat and "
   "the ratio is ~1. Anchored on a synthesised pair, comb and no-comb.")
_T("G_ROOM.min_band_occupancy", 0.75, "fraction of 1/12-oct bands",
   "control-derived",
   "APPLICABILITY, measured from the audio rather than declared. A ripple "
   "statistic is a statement about a broadband field; on a sparse line spectrum "
   "most 1/12-octave bands are empty and the 'ripple' measures the gaps between "
   "partials (a physics-true tonal bed read 113 dB). Below this occupancy the "
   "ripple limb reports INAPPLICABLE -- which is not a pass, and limbs (a) and "
   "(b) and G-RING are unaffected.")
_T("G_ROOM.max_ripple_p95_minus_p5_db", 8.0, "dB", "control-derived",
   "1/12-octave log-spectrum ripple over 0.4-6 kHz. The delivered master read "
   "17.60 dB L / 16.51 dB R. Anchored on the same synthesised comb/no-comb "
   "pair as the cepstral limb.")

# ------------------------------------------------------------- G-BALANCE ----
_T("G_BALANCE.near_white_ratio_of_white", 0.60, "SFM / SFM(white)", "control-derived",
   "A stem at >=0.6 of white per-band flatness is a noise generator by "
   "measurement. Same synthetic mixture calibration as G-FLAT.")
_T("G_BALANCE.max_near_white_power_share", 0.25, "fraction of beat power", "control-derived",
   "Beat 1 of the delivered master ran 92.6 %. Summing two decorrelated "
   "near-white stems is what takes a mix from ~82 % to 98.6 % of white -- the "
   "MIX is the final flattening step, which is why this is measured on stems "
   "and not on the master.")
_T("G_BALANCE.min_protagonist_margin_db", 8.0, "dB", "control-derived",
   "Measured, every run, as the stem-level margin at which a synthesised "
   "protagonist-plus-noise mixture still meets the G-FLAT bar. Not a taste "
   "judgement and not read from any master. Delivered: -12.01 / +0.11 / "
   "+0.03 dB on beats 1 / 4 / 5.")

# ------------------------------------------------------------- G-SUSTAIN ----
# R2-4081. THE GATE THAT WOULD HAVE CAUGHT R2-4079, and the reason it is a
# separate instrument rather than another bar on G-HNR: G-HNR's beat-1 median
# read R2-4079 as NOT TONAL ENOUGH (+0.49 dB against +8 dB) on the same file
# the client rejected as "a shitty musical". A median over 80 ms windows is an
# opinion about the whole mix; what an audience hears is the loudest thing that
# HOLDS A NOTE inside it. That is what these three numbers measure.
_T("G_SUSTAIN.min_note_s", 0.60, "s", "physics",
   "A pitch shorter than this is a RING, not a note: a struck steel plate at "
   "eta 0.02-0.15 has T60 = 2.2/(eta*pi*f) = 30-350 ms at 200 Hz, so 0.6 s is "
   "above every decay a struck resonator in this film can produce and below "
   "any note a listener would call held. Derived from the damping, not chosen.")
_T("G_SUSTAIN.stability_cents", 25.0, "cents", "physics",
   "A quarter of a semitone. The physical claim being tested is that machine "
   "pitch MOVES: a servo under a trapezoidal move profile sweeps its gear-mesh "
   "line over an octave, an engine on throttle sweeps with rpm, and a Doppler "
   "pass at the film's own 1.41-semitone station sweeps 141 cents. 25 cents is "
   "under the smallest of those by 5.6x and above the +-11 cent worst-case "
   "parabolic bin-interpolation error of a 4096-point window at 80 Hz.")
_T("G_SUSTAIN.peak_prominence_db", 8.0, "dB over the local floor", "physics",
   "A partial has to stand 8 dB over the median of its own +-1/3-octave "
   "neighbourhood, i.e. carry 6.3x its own floor's power density, before it is "
   "a partial at all. Below that a peak is the Rayleigh fluctuation of a "
   "broadband field: the p95-p5 of a diffuse transfer function is 17.7 dB by "
   "construction (R2-4067), so an isolated 8 dB excess is common in noise and "
   "an 8 dB excess HELD FOR 0.6 s at one frequency is not.")
_T("G_SUSTAIN.max_note_cover", 0.20, "fraction of the beat", "control-derived",
   "How much of the beat has something holding a pitch. Two-sided, from "
   "synthesised controls only: the physics-true assembly cell C9 reads 0.000 "
   "-- over five seeds, without exception -- and the drone-plus-clicks C8b "
   "reads 0.597. A ratio placement is undefined against a zero anchor, so the "
   "bar is one third of the NEGATIVE: the most of a beat that may hold a "
   "pitch while two thirds of it does not. It is deliberately not 0, because "
   "a real showroom has an HVAC line and a lighting ballast and over-"
   "correction is a named failure mode in the spec.")
_T("G_SUSTAIN.max_chord_cover", 0.05, "fraction of the beat", "control-derived",
   "THREE PITCHES HELD AT ONCE IS A CHORD. This is the limb that separates "
   "MUSICAL from merely TONAL and it is the cleanest one in the corpus: the "
   "assembly cell C9 reads 0.000 across every seed, because three independent "
   "constant-rate sources is not a thing an assembly cell has, and C8b reads "
   "0.576. 0.05 of a 33 s beat is 1.65 s -- the allowance for a coincidence, "
   "not for a chord.")
_T("G_SUSTAIN.max_held_power_share", 0.15, "fraction of beat power",
   "control-derived",
   "The power limb, so that a short LOUD pad cannot pass on coverage alone. "
   "Each held note is credited its own three-bin share of its own frames' "
   "power, time-weighted over the beat. C9 reads 0.0000 and C8b reads 0.5193, "
   "which is its own R2-4081 dry-gain sweep (98.3 % of its power in a servo "
   "comb) recovered from the audio by a different instrument. The bar is 0.15 "
   "because a bed that is one part in seven sustained tone is a bed and one "
   "part in three is a pad. HONEST LIMITATION, DECLARED: this limb does NOT "
   "fire on the master the client called a musical -- R2-4079 reads 0.0116 -- "
   "because its pad sits inside a broadband bed. The cover and chord limbs are "
   "what catch that file. This limb catches the drone.")

# ---------------------------------------------------------------- G-EVENT ----
# R2-4081. THE INSTRUMENT THAT MAKES RESCOPING G-FLAT AND G-HNR SAFE. Once
# those two stop being applied to percussive beats, something still has to be
# able to fail a hair dryer at beat 1 -- and it cannot be a stationary spectral
# statistic, because the measurement below is what R2-4081 found:
#
#   passage                                   per-band SFM      Boersma HNR
#   660 struck plates over 33 s, no noise           1.263 x W       -3.78 dB
#   source anywhere in the signal path
#   the delivered "hair blower" master               0.922 x W       +0.26 dB
#   octave-matched filtered noise (C1)               0.700 x W        --
#   the C8b servo drone bed alone                    0.338 x W      +30.54 dB
#
# A signal built ENTIRELY of Hertzian impulses driving plate modes reads
# FLATTER THAN WHITE NOISE and LESS PERIODIC than the hair dryer, on both
# instruments at once. That is not a threshold that needs moving; it is a
# statistic that is not monotone in the property being gated. An impulse has a
# smooth deterministic magnitude spectrum, so its per-bin variance is LOWER
# than white noise's chi-square fluctuation and its SFM is HIGHER. The
# difference between a hair dryer and an assembly cell is not in the spectrum
# at all. It is in the envelope.
_T("G_EVENT.window_s", 2.0, "s", "physics",
   "The spread is taken inside 2 s windows and the median over windows is "
   "gated, so a macro fade cannot buy the number and one busy passage cannot "
   "carry a stationary beat. 2 s holds at least two of the film's own "
   "arrivals at its slowest cluster spacing.")
_T("G_EVENT.short_term_ms", 20.0, "ms", "physics",
   "20 ms is under the 30-350 ms T60 of every struck resonator in the film, so "
   "an individual event's decay is resolved rather than averaged away, and it "
   "is over the 12.5 ms period of the lowest gated band so the measurement is "
   "a level and not a waveform.")
_T("G_EVENT.min_local_dynamic_range_db", 13.7, "dB", "control-derived",
   "p95-p5 of the 20 ms level inside 2 s windows, MEDIAN over windows. "
   "Two-sided and synthesised at BOTH ends, every number measured with the "
   "shipped estimator: white noise 0.65 dB; the C8b drone 0.64 dB; the "
   "assembly cell's OWN octave-band spectrum re-synthesised as stationary "
   "noise 2.06 dB (the M-EVENT mutation, and the sharpest negative there is "
   "-- every spectral statistic in the suite survives it and every event in "
   "the beat is gone); octave-matched noise C1 4.70 dB; blower-into-tubes C3 "
   "8.79 dB. The positive, C9, reads 21.36 dB and holds 21.4-26.4 dB over "
   "five seeds. 13.7 is the MAXIMUM-MARGIN placement in log units between the "
   "positive and the loudest negative -- equal ratio to each, 1.56x either "
   "way -- which is the only defensible position given one anchor on each "
   "side and no distribution. NO MASTER WAS CONSULTED. That two of the "
   "rejected masters land 0.2-0.5 dB under it is an outcome, not a "
   "derivation, and R2-4081 says in the staging log that a 0.45 dB margin is "
   "not a margin it would defend.")

# ----------------------------------------------------------- G-CONSTRUCT ----
_T("G_CONSTRUCT.max_unscheduled_noise_sources", 0.0, "count", "physics",
   "THE LAW: no white()/pink()/brown() output may reach a bus without passing "
   "an event scheduler or a physically-parameterised filter carrying a "
   "derivation comment. Every source is an excitation driving a resonator "
   "whose modes come from a geometry. Zero is the only defensible count and it "
   "is not a calibration.")

# The showroom, from docs/circuit_spec.json. Used by G-RING's Sabine bar and by
# G-ROOM's Schroeder frequency. Declared here so the physics is auditable.
SHOWROOM_INTERIOR_M = (30.0, 22.0, 6.5)
SHOWROOM_DECLARED_RT60_S = 2.4          # what layers.showroom_tail declares
INTERIOR_BEATS = ("1_assembly", "2_launch", "3_breach")

# Which stem is the protagonist of each beat. THIS IS A DECLARATION ABOUT THE
# FILM, NOT A THRESHOLD -- it says what the audience is meant to be listening
# to, and it is stated once, here, rather than inferred from whichever stem
# happens to be loudest (which is how a noise bed becomes the protagonist).
PROTAGONIST = {
    "1_assembly": ("assembly",),
    "2_launch":   ("engine",),
    "3_breach":   ("shards", "structure", "impact"),
    "4_transit":  ("engine",),
    "5_lap":      ("engine",),
    "6_ending":   ("engine", "assembly"),
}
# Beats where no stem is the protagonist by design are INAPPLICABLE to
# G-BALANCE rather than passed by it.

# WHICH BEATS MAY HOLD A PITCH, DECLARED ONCE (R2-4081).
#
# A power unit is periodic in PITCH by physics: its firing comb is order*rpm/60
# and holding a note is what it does. An assembly cell is periodic in RHYTHM
# and never in pitch: everything in it is struck, and struck resonators decay.
# The suite had one set of tonality instruments pointed at both, and the bar it
# carried to beat 1 (+8 dB Boersma median, <=0.45x white flatness) is
# satisfiable ONLY by sustained pitched material -- which is what R2-4079 built
# and what the client rejected on hearing.
#
# So the beats split, and the split is derived from PROTAGONIST rather than
# listed by hand: a beat whose protagonist is the engine is judged on whether
# it holds the note it should (G-ORDER, G-IDENTITY, G-HNR, G-FLAT); a beat
# whose protagonist is not is judged on whether it is EVENTFUL (G-EVENT) and on
# whether it is NOT holding a note (G-SUSTAIN).
ENGINE_BEATS = tuple(k for k, v in PROTAGONIST.items() if "engine" in v)
PERCUSSIVE_BEATS = tuple(k for k, v in PROTAGONIST.items() if "engine" not in v)


# ============================================== RETIRED, AND WHY (R2-4081) ==
# A bar that is deleted leaves no evidence that it was ever wrong, and the next
# rebuild re-derives it. These two are kept here, unenforced, with the
# measurement that retired them, so that re-adding either one has to argue with
# a number. NEITHER WAS MOVED TO MAKE A MASTER PASS -- both were removed
# because a SYNTHESISED POSITIVE CONTROL cannot reach them and every synthesised
# NEGATIVE outscores it, which is a statement about the statistic and not about
# any film.
RETIRED = {
    "G_HNR.beat1_median_min_db": {
        "value": 8.0, "units": "dB", "retired_at": "R2-4081",
        "was": ("10*log10(0.85/0.15) = 7.53 dB rounded up: the point where the "
                "aperiodic fraction of a calibrated mixture falls below 15 %."),
        "why": ("Boersma HNR at a percussive beat is INVERTED, not "
                "mis-thresholded. Measured on beat 1, medians: physics-true "
                "assembly cell C9 -4.34 dB; 660 struck plates with no noise "
                "source at all -3.78 dB; blower-into-tubes C3 -0.63 dB; the "
                "delivered hair-blower master +0.26 dB; the tubes master "
                "+0.04 dB; the master rejected as a musical +0.49 dB. Every "
                "negative outscores every positive, so no bar exists that "
                "passes what should pass and fails what should fail. The only "
                "corpus signal that ever cleared +8 dB at beat 1 is C8b, which "
                "is 98.3 % sustained tone by power -- the bar's sole "
                "validation came from a drone, and R2-4079 chasing the bar "
                "produced a drone the client rejected on hearing."),
        "replaced_by": ("G-SUSTAIN for pitch and G-EVENT for noisiness; G-HNR "
                        "itself is unchanged and still gated on engine beats, "
                        "where holding a note is the physics."),
    },
    "G_FLAT.beat1_median_max_ratio_of_white": {
        "value": 0.45, "units": "SFM / SFM(white)", "retired_at": "R2-4081",
        "was": ("the showroom held tighter than the film average, anchored on "
                "C8b's 0.389 per-beat median."),
        "why": ("Per-band SFM is not monotone in noisiness for impulsive "
                "material. A 33 s passage of Hertzian impulses driving plate "
                "modes measures 1.263x white -- FLATTER THAN WHITE NOISE -- "
                "because an impulse's magnitude spectrum is smooth and "
                "deterministic while white noise's per-bin power is "
                "chi-square. Against 0.922x for the delivered hair-blower "
                "master and 0.700x for octave-matched noise, the ordering is "
                "inverted. The 0.389 anchor that set the bar is C8b's, and "
                "C8b is a drone."),
        "replaced_by": "G-EVENT, which measures the same property in the "
                       "envelope, where hiss and machinery actually differ.",
    },
}


def audit_thresholds(extra: dict | None = None):
    """THE CI CHECK. Any threshold whose source is not in SOURCES_ALLOWED is a
    violation, and `artefact` is called out by name because it is the specific
    rule that shipped three rejected masters.

    Returns a dict; `PASS` is False if anything is wrong. `tools/percept_matrix.py`
    exits non-zero on a False and refuses to adjudicate anything.
    """
    reg = dict(THRESHOLDS)
    if extra:
        reg.update(extra)
    violations = []
    for k, t in sorted(reg.items()):
        if t.source == "artefact":
            violations.append({
                "key": k, "source": t.source,
                "why": ("BANNED: a threshold derived from the artefact under "
                        "test. This is verify.py:816's rule and it is the "
                        "reason three rebuilds shipped without anyone knowing "
                        "they were bad.")})
        elif t.source not in SOURCES_ALLOWED:
            violations.append({"key": k, "source": t.source,
                               "why": f"source must be one of {SOURCES_ALLOWED}"})
        if not t.note or len(t.note) < 40:
            violations.append({"key": k, "source": t.source,
                               "why": "no derivation note; a bare number is not a threshold"})
    return {
        "n_thresholds": len(reg),
        "sources_allowed": list(SOURCES_ALLOWED),
        "by_source": {s: sorted(k for k, t in reg.items() if t.source == s)
                      for s in SOURCES_ALLOWED},
        "violations": violations,
        "PASS": len(violations) == 0,
    }


def thresholds_report():
    return {k: t.as_dict() for k, t in sorted(THRESHOLDS.items())}


def V(key):
    return THRESHOLDS[key].value


# ======================================================= signal plumbing ====
def to_mono(x):
    x = np.asarray(x, dtype=np.float64)
    return x if x.ndim == 1 else x.mean(axis=1)


@dataclass
class Beat:
    name: str
    t0: float
    t1: float


def beats_from_sheet(sheet, duration_s):
    bs = sheet["beats"]
    out = []
    for i, b in enumerate(bs):
        t0 = float(b["start_s"])
        t1 = float(bs[i + 1]["start_s"]) if i + 1 < len(bs) else float(duration_s)
        out.append(Beat(b["name"], t0, min(t1, duration_s)))
    return [b for b in out if b.t1 - b.t0 > 0.5]


def _slice(mono, sr, b: Beat):
    return mono[int(b.t0 * sr):int(b.t1 * sr)]


def _stft_power(mono, sr, win=8192, hop=None):
    hop = hop or win // 2
    n = (len(mono) - win) // hop + 1
    if n < 1:
        return np.zeros((0, win // 2 + 1)), np.zeros(win // 2 + 1)
    w = np.hanning(win)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = mono[idx] * w
    P = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    f = np.fft.rfftfreq(win, 1.0 / sr)
    return P, f


def third_octave_edges(f_lo, f_hi):
    """1/3-octave centres over [f_lo, f_hi], ISO-style, from 1 kHz."""
    k0 = int(math.floor(3 * math.log2(f_lo / 1000.0)))
    k1 = int(math.ceil(3 * math.log2(f_hi / 1000.0)))
    out = []
    for k in range(k0, k1 + 1):
        fc = 1000.0 * 2.0 ** (k / 3.0)
        lo, hi = fc / 2.0 ** (1 / 6.0), fc * 2.0 ** (1 / 6.0)
        if hi <= f_lo or lo >= f_hi:
            continue
        out.append((max(lo, f_lo), min(hi, f_hi), fc))
    return out


SFM_WIN = 2048
# 43 ms. CHOSEN BY MEASUREMENT, not by habit: the separation between the
# synthesised degenerates and the synthesised physical construction, measured
# over 2048/4096/8192/16384, is 2.89 / 2.35 / 1.94 / 1.72. A long window smears
# a 40 ms modal decay into something that looks like a steady band, which is
# exactly the content this gate must be able to tell from noise. This is
# estimator design against controls; no master was consulted.


def per_band_sfm(mono, sr, f_lo=500.0, f_hi=3000.0, win=SFM_WIN, min_bins=5):
    """Spectral flatness computed INSIDE each 1/3-octave band, then averaged.

    This is the tilt-free construction. A broad spectral tilt changes the level
    of each band but not the flatness WITHIN it, so C7 (the delivered master
    plus a tilt) cannot move this number -- which is the whole point, because
    the whole-band SFM read 0.0142 on the delivered master and that reassuring
    number is what let it ship.
    """
    P, f = _stft_power(mono, sr, win=win)
    if P.shape[0] < 1:
        return float("nan")
    vals = []
    for lo, hi, _fc in third_octave_edges(f_lo, f_hi):
        m = (f >= lo) & (f < hi)
        if m.sum() < min_bins:
            continue
        Pb = np.maximum(P[:, m], 1e-30)
        # SILENCE IS NOT FLATNESS. Every bin of an empty frame lands on the same
        # numerical floor, so its spectral flatness is exactly 1.0 -- and
        # averaging that in made a five-mode decaying ring measure 1.65*W, i.e.
        # FLATTER THAN WHITE NOISE, and a pure harmonic comb measure 0.345*W in
        # the bands its harmonics happen to miss. Both were the estimator
        # measuring its own floor. Frames more than 50 dB under the band's own
        # p95 are not measurements and are dropped.
        e = Pb.mean(axis=1)
        live = e > max(float(np.percentile(e, 95)) * 10 ** (-50.0 / 10.0), 1e-28)
        if live.sum() < 4:
            continue
        Pb = Pb[live]
        sfm = np.exp(np.log(Pb).mean(axis=1)) / Pb.mean(axis=1)
        vals.append(float(np.mean(sfm)))
    return float(np.mean(vals)) if vals else float("nan")


def white_sfm_reference(n, sr, seed=90210, f_lo=500.0, f_hi=3000.0, win=SFM_WIN):
    """W: literal white noise through the IDENTICAL pipeline, same length."""
    rng = np.random.default_rng(seed)
    return per_band_sfm(rng.standard_normal(n), sr, f_lo, f_hi, win)


# ============================================== Boersma HNR (in-repo) ======
def boersma_hnr(mono, sr, win_s=0.080, hop_s=0.010, f0_lo=70.0, f0_hi=600.0,
                silence_rel_db=-40.0):
    """Boersma (1993) autocorrelation harmonic-to-noise ratio.

    The autocorrelation of the WINDOWED signal is divided by the
    autocorrelation of the window itself before the peak is taken -- that
    division is the whole method, and it is what the old `hnr_profile` did not
    have. r is the normalised height of the highest non-zero-lag peak;
    HNR = 10*log10(r/(1-r)).

    NO median filter, NO "anything above the floor is tonal". The peak is a
    PERIODICITY measurement: noise through a high-Q resonator has narrow
    spectral peaks and no periodicity, and it scores near 0 dB here, which is
    exactly the discrimination the shipped gate did not have.
    """
    n = int(round(win_s * sr))
    hop = int(round(hop_s * sr))
    if len(mono) < n + hop:
        return np.zeros(0), np.zeros(0)
    w = np.hanning(n)
    rw = np.correlate(w, w, "full")[n - 1:]
    rw = rw / max(rw[0], 1e-30)
    lo_lag = max(int(sr / f0_hi), 2)
    hi_lag = min(int(sr / f0_lo), n - 2)
    if hi_lag <= lo_lag:
        return np.zeros(0), np.zeros(0)

    nf = (len(mono) - n) // hop + 1
    idx = np.arange(n)[None, :] + hop * np.arange(nf)[:, None]
    seg = mono[idx]
    seg = seg - seg.mean(axis=1, keepdims=True)
    lev = np.sqrt((seg ** 2).mean(axis=1))
    segw = seg * w

    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    S = np.fft.rfft(segw, nfft, axis=1)
    ac = np.fft.irfft(np.abs(S) ** 2, nfft, axis=1)[:, :n]
    ac = ac / np.maximum(ac[:, :1], 1e-30)
    ac = ac / np.maximum(rw[None, :n], 1e-6)

    band = ac[:, lo_lag:hi_lag + 1]
    j = np.argmax(band, axis=1)
    r = band[np.arange(nf), j]
    # parabolic refinement of the peak height
    jj = j + lo_lag
    ok = (jj > 0) & (jj < n - 1)
    y0 = ac[np.arange(nf), np.maximum(jj - 1, 0)]
    y2 = ac[np.arange(nf), np.minimum(jj + 1, n - 1)]
    den = (y0 - 2 * r + y2)
    d = np.where(np.abs(den) > 1e-12, 0.5 * (y0 - y2) / np.where(np.abs(den) > 1e-12, den, 1.0), 0.0)
    d = np.clip(d, -0.5, 0.5)
    rp = r - 0.25 * (y0 - y2) * d
    r = np.where(ok, rp, r)

    r = np.clip(r, 1e-9, 1.0 - 1e-9)
    hnr = 10.0 * np.log10(r / (1.0 - r))
    # silence gate: a window 40 dB under the segment's own p95 level is not a
    # measurement of anything. Reported as a count, never as a pass.
    ref = np.percentile(lev, 95) if nf else 0.0
    live = lev > ref * 10 ** (silence_rel_db / 20.0)
    return hnr, live


def harmonic_noise_mixture(sr, dur_s, noise_fraction, f0=145.0, seed=4242,
                           n_harm=24, bp=(80.0, 8000.0)):
    """A mixture of a harmonic comb and bandpassed noise at a KNOWN aperiodic
    power fraction. This is the ground truth both G-HNR and G-FLAT calibrate
    against, every run. It is synthesised from its own coefficients, so its
    truth is arithmetic, not a measurement of anything."""
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)
    comb = np.zeros(n)
    for k in range(1, n_harm + 1):
        if f0 * k > sr * 0.45:
            break
        comb += (1.0 / k) * np.sin(2 * np.pi * f0 * k * t + rng.uniform(0, 2 * np.pi))
    comb /= np.sqrt(np.mean(comb ** 2))
    sos = _sig.butter(4, [bp[0], min(bp[1], sr * 0.45)], btype="bandpass",
                      fs=sr, output="sos")
    nz = _sig.sosfilt(sos, rng.standard_normal(n))
    nz /= np.sqrt(np.mean(nz ** 2))
    f = float(np.clip(noise_fraction, 0.0, 1.0))
    return comb * math.sqrt(1.0 - f) + nz * math.sqrt(f)


def calibrate_hnr(sr=48000, dur_s=3.0):
    """RE-VALIDATE THE INSTRUMENT ON EVERY INVOCATION.

    The diagnosis validated this construction once, against mixtures at known
    noise fractions, returning 16.98/12.86/9.62/4.88/0.22 dB against truths of
    16.90/12.79/9.54/4.77/0.00 dB. Re-running it here means the instrument
    re-validates itself each time rather than inheriting a note somebody wrote.
    """
    rows = []
    for f in (0.02, 0.05, 0.10, 0.25, 0.50, 0.75):
        x = harmonic_noise_mixture(sr, dur_s, f)
        h, live = boersma_hnr(x, sr)
        meas = float(np.median(h[live])) if live.any() else float("nan")
        truth = 10.0 * math.log10((1.0 - f) / f)
        rows.append({"noise_fraction": f, "truth_db": truth,
                     "measured_db": meas, "error_db": meas - truth,
                     # 0.75 is BELOW both of this gate's bars (0 dB and +8 dB),
                     # so it is reported and not gated -- see the note below.
                     "gated": f <= 0.50})
    g = [r for r in rows if r["gated"] and np.isfinite(r["error_db"])]
    err = max(abs(r["error_db"]) for r in g)
    return {"rows": rows, "max_abs_error_db": float(err),
            "limit_db": V("G_HNR.calibration_max_error_db"),
            "bias_direction_note": (
                "The residual error is POSITIVE at every point and grows with "
                "noise fraction (peak-of-N-lags bias). It is +0.12 dB at the "
                "+8 dB bar and +0.40 dB at the 0 dB bar, and it makes the "
                "instrument read HIGH -- i.e. LENIENT -- never strict. A "
                "lenient bias cannot manufacture a failure, so no signal is "
                "failed by this gate because of it. The 0.75 row (+0.95 dB) is "
                "far below both bars and is reported, not gated."),
            "PASS": bool(err <= V("G_HNR.calibration_max_error_db"))}


def calibrate_flat(sr=48000, dur_s=3.0):
    """Where the slice bar comes from: the per-band SFM of mixtures whose
    aperiodic fraction is known by construction. Reported every run so the
    placement is auditable from the report alone.

    R2-4081: the beat-1 limb of this calibration is gone with the beat-1 bar
    (see RETIRED). What remains is the mapping from the surviving slice bar to
    an aperiodic fraction, and one number that should have been read years ago:
    THIS CALIBRATION ONLY EVER RAN ON HARMONIC-PLUS-NOISE MIXTURES. Every
    signal it was ever shown was a sustained comb with noise added, so the
    monotonicity it verifies is monotonicity ALONG THAT ONE AXIS. It says
    nothing about impulsive material, and impulsive material is where the
    estimator inverts.
    """
    n = int(dur_s * sr)
    W = white_sfm_reference(n, sr)
    rows = []
    for f in (0.0, 0.15, 0.25, 0.35, 0.50, 0.75, 1.0):
        x = harmonic_noise_mixture(sr, dur_s, f)
        s = per_band_sfm(x, sr)
        rows.append({"noise_fraction": f, "sfm": s, "ratio_of_white": s / W})
    fr = [r["noise_fraction"] for r in rows]
    ra = [r["ratio_of_white"] for r in rows]
    implied_45 = float(np.interp(V("G_FLAT.slice_max_ratio_of_white"), ra, fr))
    monotone = bool(np.all(np.diff(ra) > 0))
    return {"white_reference_sfm": W, "rows": rows,
            "noise_fraction_implied_by_slice_bar": implied_45,
            "monotone": monotone,
            "note": ("Per-band SFM saturates FAST: a pure harmonic comb reads "
                     "0.126*W and 15 % added noise already reads 0.554*W. So "
                     "0.55*W is not 'half noise' -- it is about 15 % aperiodic "
                     "energy in 500-3000 Hz. The mapping is recomputed here "
                     "every run so the bar's meaning is read off the report "
                     "and not off a comment."),
            "domain": ("HARMONIC-PLUS-NOISE MIXTURES ONLY. Monotone along the "
                       "noise-fraction axis of a SUSTAINED comb; not monotone "
                       "in noisiness for impulsive material, where 660 struck "
                       "plates read 1.263x white. That is why G-FLAT is an "
                       "engine-beat instrument from R2-4081 on."),
            "PASS": bool(monotone and 0.03 <= implied_45 <= 0.45)}


# ===================================================== envelope machinery ===
def band_envelopes(mono, sr, n_bands=40, f_lo=50.0, f_hi=12000.0, env_hz=100.0):
    """40 log-spaced band envelopes at 100 Hz, per-band z-scored.

    Per-band normalisation is what makes the self-similarity a TIMBRE
    comparison rather than a level comparison: two bursts of different
    loudness but identical spectrum still correlate at 1.
    """
    hop = max(int(round(sr / env_hz)), 1)
    win = hop * 4
    P, f = _stft_power(mono, sr, win=win, hop=hop)
    if P.shape[0] < 4:
        return np.zeros((0, n_bands)), env_hz
    edges = np.geomspace(f_lo, min(f_hi, sr * 0.45), n_bands + 1)
    E = np.zeros((P.shape[0], n_bands))
    for i in range(n_bands):
        m = (f >= edges[i]) & (f < edges[i + 1])
        if m.sum() == 0:
            m = np.argmin(np.abs(f - 0.5 * (edges[i] + edges[i + 1])))
            E[:, i] = P[:, m]
        else:
            E[:, i] = P[:, m].mean(axis=1)
    E = 10.0 * np.log10(np.maximum(E, 1e-20))
    E -= E.mean(axis=0, keepdims=True)
    sd = E.std(axis=0, keepdims=True)
    E /= np.maximum(sd, 1e-9)
    return E, sr / hop


def envelope_autocorrelation(mono, sr, lag_min_s=0.3, lag_max_s=16.0):
    E, fs = band_envelopes(mono, sr)
    if E.shape[0] < 16:
        return {"r_max": float("nan"), "lag_s": float("nan"), "n_frames": int(E.shape[0])}
    nf = E.shape[0]
    l0, l1 = int(lag_min_s * fs), min(int(lag_max_s * fs), nf - 8)
    if l1 <= l0:
        return {"r_max": float("nan"), "lag_s": float("nan"), "n_frames": nf}
    # unbiased per-band autocorrelation via FFT, averaged across bands
    nfft = 1 << int(np.ceil(np.log2(2 * nf)))
    S = np.fft.rfft(E, nfft, axis=0)
    ac = np.fft.irfft(np.abs(S) ** 2, nfft, axis=0)[:nf]
    norm = np.maximum(nf - np.arange(nf), 1)[:, None]
    ac = ac / norm
    ac = ac / np.maximum(ac[:1], 1e-30)
    r = ac[:, :].mean(axis=1)
    # A PERIOD IS A LOCAL MAXIMUM, NOT A TREND. Slow drift -- an rpm wobble, a
    # fade, a camera move -- makes r decay monotonically from lag 0, and simply
    # taking max(r) over the lag range then reads whatever r is at lag_min. That
    # read 0.726 on a constant-rpm power unit with nothing repeating in it. A
    # repeat is a peak that stands above its own neighbourhood, so only local
    # maxima with prominence are candidates, and a signal with none scores zero.
    pk, props = _sig.find_peaks(r[l0:l1 + 1], prominence=V("G_NOVEL.min_peak_prominence"))
    if pk.size == 0:
        return {"r_max": 0.0, "lag_s": float("nan"), "n_frames": int(nf),
                "prominence": 0.0, "n_candidate_peaks": 0,
                "note": "no prominent local maximum: no period, only trend"}
    j = int(pk[int(np.argmax(r[l0:l1 + 1][pk]))]) + l0
    prom = float(props["prominences"][int(np.argmax(r[l0:l1 + 1][pk]))])
    return {"r_max": float(r[j]), "lag_s": float(j / fs), "n_frames": int(nf),
            "prominence": prom, "n_candidate_peaks": int(pk.size),
            "ladder": [{"lag_s": float(k * j / fs), "r": float(r[k * j])}
                       for k in (1, 2, 3, 4) if k * j <= l1]}


def broadband_envelope(mono, sr, f_lo=150.0, f_hi=8000.0, env_hz=50.0):
    sos = _sig.butter(4, [f_lo, min(f_hi, sr * 0.45)], btype="bandpass",
                      fs=sr, output="sos")
    y = _sig.sosfilt(sos, mono)
    e = np.abs(_sig.hilbert(y)) if len(y) < 4_000_000 else np.abs(y)
    # ANTI-ALIAS BEFORE DECIMATING. Block-averaging is a sinc with big
    # sidelobes: on a harmonic-rich source the envelope still ripples at f0, and
    # decimating without a proper filter folded that ripple down into the
    # modulation band -- a constant-rpm power unit read an 8.1 dB "modulation
    # peak" at 2.909 Hz that moved when its rpm moved, i.e. an alias of the
    # firing rate and not a modulation of anything.
    q = max(int(round(sr / env_hz)), 1)
    ne = len(e) // q
    if ne < 8:
        return np.zeros(0), env_hz
    lp = _sig.butter(6, 0.4 * env_hz, btype="low", fs=sr, output="sos")
    e = _sig.sosfiltfilt(lp, e)
    e = e[:ne * q].reshape(ne, q).mean(axis=1)
    return e, sr / q


def modulation_spectrum(mono, sr, f_mod_lo=0.2, f_mod_hi=3.0):
    """Peak-to-local-median of the envelope's own spectrum over 0.2-3 Hz.

    A metronome puts one narrow line here. Jitter smears it. That difference
    is exactly what separates control C2 (which must fail) from control C6
    (which must pass this gate and fail G-GESTURE instead), and it is why the
    bar is anchored on those two controls every run.
    """
    e, fs = broadband_envelope(mono, sr)
    dur = len(e) / fs
    if dur < 12.0:
        return {"peak_over_local_median_db": float("nan"), "peak_hz": float("nan"),
                "why": "shorter than 12 s: a 0.2 Hz modulation is not resolvable"}
    # DETREND. A slow drift -- an rpm wobble, a fade -- puts a large skirt at the
    # bottom of the band and an undetrended estimator reported 10.6 dB at the
    # 0.2 Hz edge for a constant-rpm power unit. 0.125 Hz is one over the
    # sub-window length, so the trend removed is by construction outside the
    # measured band.
    q = max(int(8.0 * fs) | 1, 3)
    e = e - _sig.savgol_filter(e, min(q, (len(e) // 2) * 2 - 1), 1)

    # WELCH, NOT ONE PERIODOGRAM. A single periodogram's own null is ~8 dB: the
    # max of ~90 exponentially-distributed bins over its own median is 8 dB with
    # nothing periodic present at all, so NO bar on a raw periodogram can mean
    # anything. Averaging K sub-windows brings the null down to a few dB, and
    # the null is measured and reported below rather than assumed.
    nsub = int(min(12.0, dur / 3.0) * fs)
    hop = max(nsub // 3, 1)
    K = max((len(e) - nsub) // hop + 1, 1)
    w = np.hanning(nsub)
    acc = None
    for i in range(K):
        s = e[i * hop:i * hop + nsub]
        if len(s) < nsub:
            break
        P = np.abs(np.fft.rfft(s * w)) ** 2
        acc = P if acc is None else acc + P
    if acc is None:
        return {"peak_over_local_median_db": float("nan"), "peak_hz": float("nan")}
    M = acc / K
    f = np.fft.rfftfreq(nsub, 1.0 / fs)
    band = (f >= f_mod_lo) & (f <= f_mod_hi)
    if band.sum() < 4:
        return {"peak_over_local_median_db": float("nan"), "peak_hz": float("nan")}
    df = f[1] - f[0]
    # A SHOULDER IS NOT A LINE. A linear-width local median read 13.74 dB on a
    # physics-true showroom beat whose modulation spectrum was a smooth 1/f
    # shoulder -- 22.6, 22.0, 17.2, 12.3, 12.0, 10.4, 3.3 dB, monotone, with no
    # peak anywhere in it. An accelerando and a rising bed BOTH put energy at
    # the bottom of this band, and neither is a repeat. So the baseline is a
    # smooth cubic in log-frequency fitted with outlier rejection: a shoulder is
    # absorbed by the fit, a metronome's line is an outlier from it.
    fit_band = (f >= 0.10) & (f <= min(5.0, fs / 2.5))
    xf = np.log10(np.maximum(f[fit_band], 1e-6))
    yf = 10.0 * np.log10(np.maximum(M[fit_band], 1e-30))
    keep = np.ones(xf.shape[0], bool)
    coef = np.polyfit(xf, yf, 3)
    for _ in range(3):
        res = yf - np.polyval(coef, xf)
        keep = res <= 3.0
        if keep.sum() < 8:
            break
        coef = np.polyfit(xf[keep], yf[keep], 3)
    base = np.polyval(coef, np.log10(np.maximum(f, 1e-6)))
    exc = 10.0 * np.log10(np.maximum(M, 1e-30)) - base
    idx = np.nonzero(band)[0]
    j = idx[int(np.argmax(exc[idx]))]
    # the null: the same statistic over the bins the fit KEPT, i.e. how far the
    # estimator's own scatter reaches with nothing periodic present.
    null = float(np.percentile(exc[fit_band][keep], 95)) if keep.sum() > 8 else float("nan")
    return {"peak_over_local_median_db": float(exc[j]), "peak_hz": float(f[j]),
            "welch_segments": int(K), "resolution_hz": float(df),
            "baseline_scatter_p95_db": null,
            "modulation_period_s": float(1.0 / f[j]) if f[j] > 0 else None}


# ================================================= burst / gesture analysis =
ONSET_RISE_DB = 6.0
# A BURST IS AN EVENT, NOT A SAMPLE OF A CONTINUOUS SIGNAL. An earlier version
# took the top N of the flux distribution regardless of magnitude, and on a
# steady tone that produced 40 "bursts" that were of course all identical --
# G-GESTURE read 0.999 and G-ROOM's mobility limb read 1.000 on a physics-true
# constant-rpm power unit. A gate that fires on a signal with no gestures in it
# is not measuring gestures. The rise threshold is what makes "no bursts" say
# INAPPLICABLE instead of FAIL.


def find_bursts(mono, sr, max_bursts=40, min_gap_s=0.25, dur_s=0.35,
                rise_db=ONSET_RISE_DB):
    """Onsets: a rise of at least `rise_db` in the broadband envelope over
    ~15 ms, kept only if they stand clear of the local floor."""
    e, fs = broadband_envelope(mono, sr, env_hz=200.0)
    if len(e) < 32:
        return []
    le = 20.0 * np.log10(np.maximum(e, 1e-12))
    k = max(int(0.015 * fs), 1)
    d = le[k:] - le[:-k]
    d = np.concatenate([np.zeros(k), d])
    floor = float(np.percentile(le, 60))
    ok = (d >= rise_db) & (le >= floor)
    cand = np.nonzero(ok)[0]
    if cand.size == 0:
        return []
    order = cand[np.argsort(-d[cand])]
    picked = []
    for i in order:
        if all(abs(i - j) > min_gap_s * fs for j in picked):
            picked.append(int(i))
        if len(picked) >= max_bursts:
            break
    out = []
    for i in sorted(picked):
        s = int(i / fs * sr)
        n = int(dur_s * sr)
        if s + n <= len(mono):
            out.append((s, n))
    return out


def _band_log_spectrum(seg, sr, n_bands, f_lo=80.0, f_hi=12000.0):
    P, f = _stft_power(seg, sr, win=min(1 << int(np.log2(max(len(seg), 64))), 4096))
    if P.shape[0] == 0:
        return np.zeros(n_bands)
    edges = np.geomspace(f_lo, min(f_hi, sr * 0.45), n_bands + 1)
    pm = P.mean(axis=0)
    out = np.empty(n_bands)
    for i in range(n_bands):
        m = (f >= edges[i]) & (f < edges[i + 1])
        out[i] = 10.0 * math.log10(max(float(pm[m].mean()) if m.any() else 1e-20, 1e-20))
    return out


# A GESTURE IS WHAT THE ONSET ADDS, NOT WHAT WAS ALREADY THERE. Measuring the
# burst window raw made every burst carry the sustained bed underneath it, and
# on a beat with a strong tonal bed that alone read 0.956 mean similarity and
# 0.938 peak recurrence -- the gate scoring the BED, twelve times, and calling
# it twelve identical gestures. Every burst feature below is therefore
# referenced to the 200 ms immediately before its own onset.
PRE_ONSET_S = 0.20
PRE_GUARD_S = 0.02


def _pre_onset(mono, sr, s):
    a = max(int(s - (PRE_ONSET_S + PRE_GUARD_S) * sr), 0)
    b = max(int(s - PRE_GUARD_S * sr), a + 1)
    return mono[a:b]


def gesture_features(mono, sr, bursts, n_bands=24, n_sub=6):
    """Per-burst timbre-over-time: 24 log bands x 6 time sub-frames, referenced
    to the 200 ms before the onset, with the burst's own mean removed so LEVEL
    cannot make two different gestures look alike or two identical ones look
    different."""
    feats = []
    for s, n in bursts:
        seg = mono[s:s + n]
        pre = _band_log_spectrum(_pre_onset(mono, sr, s), sr, n_bands)
        sub = n // n_sub
        row = []
        for k in range(n_sub):
            row.extend(_band_log_spectrum(seg[k * sub:(k + 1) * sub], sr, n_bands) - pre)
        v = np.array(row)
        v = v - v.mean()
        nrm = np.linalg.norm(v)
        feats.append(v / nrm if nrm > 1e-9 else v)
    return np.array(feats) if feats else np.zeros((0, n_bands * n_sub))


def pairwise_similarity(F):
    if F.shape[0] < 3:
        return {"n": int(F.shape[0]), "mean": float("nan"), "max": float("nan")}
    S = F @ F.T
    iu = np.triu_indices(F.shape[0], 1)
    v = S[iu]
    return {"n": int(F.shape[0]), "mean": float(np.mean(v)), "max": float(np.max(v)),
            "p90": float(np.percentile(v, 90))}


# ============================================================ room analysis =
def decay_regions(mono, sr, min_s=0.30, max_s=1.5, max_regions=14,
                  prominence_db=6.0):
    """THE INTER-EVENT GAPS: what happens after each burst stops.

    Defined as the stretch from just after an envelope peak to wherever the
    envelope stops falling. An earlier version demanded a MONOTONE fall for
    0.35 s and found ZERO regions in the delivered master's beat 1 -- a beat
    with twelve bursts and about a second of naked reverb after each one.
    Real decays are not monotone at 200 Hz frame rate; they are noisy, and a
    detector that requires monotonicity finds nothing and then reports
    INAPPLICABLE, which is how a gate goes quietly blind.
    """
    e, fs = broadband_envelope(mono, sr, env_hz=200.0)
    if len(e) < 64:
        return []
    le = 20.0 * np.log10(np.maximum(e, 1e-12))
    k = min(int(0.05 * fs) | 1, (len(le) // 2) * 2 - 1)
    if k >= 5:
        le = _sig.savgol_filter(le, k, 2)
    pk, _p = _sig.find_peaks(le, prominence=prominence_db,
                             distance=max(int(0.30 * fs), 1))
    regions = []
    for i, p in enumerate(pk):
        a = p + int(0.05 * fs)
        stop = pk[i + 1] if i + 1 < len(pk) else len(le)
        b = min(a + int(max_s * fs), stop, len(le))
        if b - a < int(min_s * fs):
            continue
        # end the region where the envelope stops falling: the first point that
        # is 3 dB above the running minimum since `a`.
        seg = le[a:b]
        rmin = np.minimum.accumulate(seg)
        rise = np.nonzero(seg > rmin + 3.0)[0]
        if rise.size:
            b = a + int(rise[0])
        if (b - a) / fs >= min_s:
            regions.append((int(a / fs * sr), int(b / fs * sr)))
    regions.sort(key=lambda r: r[0] - r[1])
    return regions[:max_regions]


def band_decay_t60(mono, sr, regions, f_lo=200.0, f_hi=6000.0, n_bands=None):
    """Per-1/6-octave T60 from the decay slope in each region, plus the
    broadband T60 over the same regions."""
    if not regions:
        return {"bands": [], "broadband_t60_s": float("nan")}
    k = 0
    centres = []
    while True:
        fc = f_lo * 2.0 ** (k / 6.0)
        if fc > f_hi:
            break
        centres.append(fc)
        k += 1
    if n_bands:
        centres = centres[:n_bands]

    def _t60(sig):
        """ISO 3382 T20, by SCHROEDER BACKWARD INTEGRATION.

        A straight fit to the raw band envelope is hopeless here: on the
        delivered master's own tails it returns R^2 = 0.23-0.37, so any honest
        goodness-of-fit guard rejects every band and the gate reports
        INAPPLICABLE while a 4.8 s ring sits in front of it. The backward
        integral E(t) = int_t^T p^2 is monotone by construction and fits at
        R^2 > 0.95. T20 x 3 is the standard extrapolation for a decay that does
        not reach -60 dB inside the gap available.
        """
        sl = []
        for a, b in regions:
            seg = np.asarray(sig[a:b], dtype=np.float64)
            if len(seg) < int(0.20 * sr):
                continue
            q = max(int(sr / 400.0), 1)
            ne = len(seg) // q
            if ne < 12:
                continue
            p2 = (seg[:ne * q] ** 2).reshape(ne, q).mean(axis=1)
            E = np.cumsum(p2[::-1])[::-1]
            le = 10.0 * np.log10(np.maximum(E / max(E[0], 1e-30), 1e-12))
            t = np.arange(ne) / (sr / q)
            m = (le <= -5.0) & (le >= -25.0)
            if m.sum() < 8:
                continue
            A = np.polyfit(t[m], le[m], 1)
            span = float(t[m].max() - t[m].min())
            drop = -A[0] * span
            resid = le[m] - np.polyval(A, t[m])
            var = float(np.var(le[m]))
            r2 = 1.0 - float(np.var(resid)) / var if var > 1e-12 else 0.0
            # A BAND THAT IS NOT DECAYING HAS NO T60: a sustained tone inside a
            # broadband gap fits a near-zero slope, and an earlier guard turned
            # that into "T60 = 115 s at 400 Hz" on a physics-true bed.
            if A[0] < -3.0 and drop >= 12.0 and r2 >= 0.90:
                sl.append(-60.0 / A[0])
        return float(np.median(sl)) if sl else float("nan")

    rows = []
    for fc in centres:
        lo, hi = fc / 2 ** (1 / 12.0), fc * 2 ** (1 / 12.0)
        if hi >= sr * 0.45:
            break
        sos = _sig.butter(4, [lo, hi], btype="bandpass", fs=sr, output="sos")
        rows.append({"f_hz": fc, "t60_s": _t60(_sig.sosfilt(sos, mono))})
    sos = _sig.butter(4, [f_lo, min(f_hi, sr * 0.45)], btype="bandpass",
                      fs=sr, output="sos")
    return {"bands": rows, "broadband_t60_s": _t60(_sig.sosfilt(sos, mono))}


def sabine_rt60(interior_m, rt60_declared_s):
    ix, iy, iz = interior_m
    v = ix * iy * iz
    s = 2.0 * (ix * iy + ix * iz + iy * iz)
    alpha = 0.161 * v / (s * rt60_declared_s)
    return {"volume_m3": v, "surface_m2": s, "implied_alpha": alpha,
            "rt60_s": 0.161 * v / (s * alpha)}


def schroeder_frequency(volume_m3, t60_s):
    return 2000.0 * math.sqrt(t60_s / volume_m3)


def comb_regularity(freqs, d_lo=20.0, d_hi=260.0, d_step=0.05, tol_pct=1.5):
    """Are the room's FIXED lines harmonics of a delay length?

    This is G-ROOM's density limb, and it is deliberately NOT a comb detector on
    the raw spectrum. A sustained harmonic SOURCE is also a comb, so a raw comb
    detector fires on any healthy engine -- it read 0.640 on a physics-true
    showroom beat whose only "comb" was its own servo harmonics. The
    discriminator is that a room's reply is FIXED while a source's moves, so
    this runs on the lines that limb (b) has already shown to recur across
    bursts, and asks only whether those fixed lines are evenly spaced.

    The delivered master's thirteen strongest fixed lines were every one a
    harmonic of an FDN delay line, matched to 0.01-0.93 %. Noise through five
    inharmonic pipes also has fixed lines -- and they are NOT a comb, which is
    what gives this limb a two-sided anchor instead of a one-sided guess.
    """
    f = np.asarray(sorted(float(v) for v in freqs))
    if f.size < 6:
        return {"score": float("nan"), "spacing_hz": float("nan"),
                "n_lines": int(f.size), "why": "fewer than 6 fixed lines"}
    ds = np.arange(d_lo, d_hi, d_step)
    best = (-1.0, float("nan"), 0.0)
    for d in ds:
        tol = np.minimum(tol_pct / 100.0 * f, 0.25 * d)
        res = np.abs(f - d * np.round(f / d))
        hit = float((res <= tol).mean())
        chance = float(np.mean(np.minimum(2.0 * tol / d, 1.0)))
        if hit - chance > best[0] - best[2]:
            best = (hit, float(d), chance)
    return {"score": best[0], "spacing_hz": best[1], "chance_level": best[2],
            "excess_over_chance": best[0] - best[2], "n_lines": int(f.size)}


def tail_spectrum(mono, sr, regions, win=16384):
    """The averaged magnitude spectrum of the film's OWN decay tails.

    G-ROOM's density and ripple limbs run here and nowhere else, and that is a
    correctness requirement, not an optimisation: a healthy engine's firing
    comb is itself a comb, so measuring "is there a comb" on a sustained source
    would fail a physics-true power unit. The room's structure is what is left
    when the source has stopped, so the tails are where it must be measured. If
    a beat has no tails, G-ROOM's (a) and (c) limbs are INAPPLICABLE -- which is
    not a pass.
    """
    acc, f, n = None, None, 0
    for a, b in regions:
        seg = mono[a:b]
        if len(seg) < win:
            continue
        P, f = _stft_power(seg, sr, win=win, hop=win // 2)
        if P.shape[0] == 0:
            continue
        acc = P.mean(axis=0) if acc is None else acc + P.mean(axis=0)
        n += 1
    if acc is None:
        return None, None, 0
    return acc / n, f, n


def cepstral_ripple_of(S, sr, q_lo_ms=1.0, q_hi_ms=30.0):
    """The signature of summing a signal with a delayed copy of itself. The
    delivered master's largest cepstral feature in its first 30 s was exactly
    master.py's own 681 and 1084 sample delays."""
    if S is None or len(S) < 2048:
        return {"peak_over_median": float("nan"), "quefrency_ms": float("nan")}
    L = 0.5 * np.log(np.maximum(S, 1e-20))
    c = np.abs(np.fft.irfft(L))
    q0, q1 = int(q_lo_ms * 1e-3 * sr), int(q_hi_ms * 1e-3 * sr)
    q1 = min(q1, len(c) - 1)
    if q1 <= q0:
        return {"peak_over_median": float("nan"), "quefrency_ms": float("nan")}
    band = c[q0:q1]
    med = float(np.median(band))
    j = int(np.argmax(band))
    return {"peak_over_median": float(band[j] / max(med, 1e-20)),
            "quefrency_ms": float((q0 + j) / sr * 1e3)}


def fractional_octave_ripple_of(S, f, f_lo=400.0, f_hi=6000.0, frac=12):
    """1/12-octave ripple, plus the OCCUPANCY that says whether a ripple
    statistic means anything here.

    A ripple statistic is a statement about a broadband field. On a sparse line
    spectrum most 1/12-octave bands contain no line at all, and the "ripple"
    then measures the gaps between harmonics: a physics-true tonal showroom bed
    read 113.25 dB, which is not a comb, it is silence between partials. So
    occupancy -- the fraction of bands within 40 dB of the loudest -- is
    measured from the audio and reported, and the limb declares itself
    INAPPLICABLE below 0.75 rather than failing a signal for being tonal.
    """
    nan = {"ripple_db": float("nan"), "occupancy": float("nan")}
    if S is None:
        return nan
    m = (f >= f_lo) & (f <= f_hi)
    if m.sum() < 64:
        return nan
    fb, Sb = f[m], S[m]
    out = []
    fc = f_lo
    while fc <= f_hi:
        lo, hi = fc / 2 ** (1 / (2 * frac)), fc * 2 ** (1 / (2 * frac))
        sel = (fb >= lo) & (fb < hi)
        if sel.sum() >= 2:
            out.append(10.0 * math.log10(max(float(Sb[sel].mean()), 1e-20)))
        fc *= 2 ** (1.0 / frac)
    if len(out) < 12:
        return nan
    out = np.array(out)
    occ = float((out >= np.percentile(out, 90) - 40.0).mean())
    det = out - _sig.savgol_filter(out, min(len(out) // 2 * 2 - 1, 21), 2)
    return {"ripple_db": float(np.percentile(det, 95) - np.percentile(det, 5)),
            "occupancy": occ, "n_bands": len(out)}


def recurrence_null(n_bursts, top_k=8, tol_pct=1.0, f_lo=200.0, f_hi=6000.0,
                    n_rep=200, seed=20260814):
    """THE CHANCE LEVEL OF `peak_recurrence`, MEASURED RATHER THAN ASSUMED.

    R2-4081. This statistic was never null-tested and it is a birthday problem:
    n_bursts x top_k observations land in ln(f_hi/f_lo)/ln(1+tol) resolvable
    bins -- 341 of them at 1 % over 200-6000 Hz -- so coincidences accumulate
    with the number of bursts. Measured on INDEPENDENT log-uniform draws, i.e.
    on peaks that by construction have nothing to do with each other:

        bursts      8     12     20     40     60
        recurrence  0.031  0.162  0.277  0.638  0.835     (bar 0.35)

    At 40 bursts pure independence scores 0.638 and the gate fails everything,
    including a beat in which every part has its own geometry. Two things
    follow, and R2-4081 does both: the burst count is capped where the null is
    still small (G_ROOM.max_bursts), and a line only counts as recurring if it
    appears in MORE bursts than the most-recurring line of an independent draw
    does 19 times out of 20 -- which is a family-wise error rate of 5 % over
    all the bins at once, not a per-bin test.
    """
    rng = np.random.default_rng(seed)
    lo, hi = math.log(f_lo), math.log(f_hi)
    maxes, fracs = [], []
    for _ in range(n_rep):
        obs = [list(np.exp(rng.uniform(lo, hi, top_k))) for _ in range(n_bursts)]
        flat = sorted(v for row in obs for v in row)
        clusters = []
        for v in flat:
            if clusters and abs(v - clusters[-1][-1]) / v * 100.0 <= tol_pct:
                clusters[-1].append(v)
            else:
                clusters.append([v])
        best, rec = 0, 0
        for c in clusters:
            mu = float(np.mean(c))
            nb = sum(1 for row in obs
                     if any(abs(v - mu) / mu * 100 <= tol_pct for v in row))
            best = max(best, nb)
            if nb >= 3:
                rec += len(c)
        maxes.append(best)
        fracs.append(rec / max(len(flat), 1))
    return {"n_bursts": int(n_bursts), "n_rep": int(n_rep),
            "max_bursts_per_line_p95": float(np.percentile(maxes, 95)),
            "recurrence_mean": float(np.mean(fracs)),
            "min_bursts_to_count": int(max(3, math.ceil(np.percentile(maxes, 95)) + 1))}


def peak_recurrence(mono, sr, bursts, top_k=8, tol_pct=1.0, f_lo=200.0, f_hi=6000.0):
    """Mobility: does the answer move when the question moves?

    Whatever is struck, a room with position-dependent early reflections and a
    diffuse tail replies differently. A bank of fixed high-Q resonators replies
    at the same frequencies every time -- 430.2 Hz recurred in 7 of 12 bursts of
    the delivered master inside a 0.27 Hz spread.

    R2-4081: a line now has to beat the CHANCE LEVEL for this many bursts (see
    `recurrence_null`) before it is called a line at all. The bar is unchanged
    and the anchors it was placed between are unchanged; what changed is that
    the numerator no longer counts coincidences, which is what it was doing on
    any beat dense enough to produce more than about twenty bursts."""
    if len(bursts) < 4:
        return {"n_bursts": len(bursts), "recurrence": float("nan"),
                "n_observations": 0}
    obs = []
    for s, n in bursts:
        seg = mono[s:s + n]
        if len(seg) < 2048:
            continue
        win = min(8192, 1 << int(np.log2(len(seg))))
        P, f = _stft_power(seg, sr, win=win)
        if P.shape[0] == 0:
            continue
        S = P.mean(axis=0)
        # referenced to the pre-onset bed, for the same reason as the gesture
        # features: what recurs must be what the ROOM adds, not what was
        # already sounding.
        pre = _pre_onset(mono, sr, s)
        if len(pre) >= win:
            Pp, _fp = _stft_power(pre, sr, win=win)
            if Pp.shape[0]:
                S = np.maximum(S - Pp.mean(axis=0), S * 1e-6)
        m = (f >= f_lo) & (f <= f_hi)
        Sb, fb = S[m], f[m]
        k = max(int(len(Sb) / 60) | 1, 5)
        rel = 10 * np.log10(np.maximum(Sb, 1e-20)) - _sig.savgol_filter(
            10 * np.log10(np.maximum(Sb, 1e-20)), k, 2)
        pk, _ = _sig.find_peaks(rel, distance=max(int(len(Sb) / 200), 2))
        if len(pk) == 0:
            continue
        pk = pk[np.argsort(-rel[pk])][:top_k]
        obs.append([float(fb[p]) for p in pk])
    if len(obs) < 4:
        return {"n_bursts": len(bursts), "recurrence": float("nan"),
                "n_observations": 0}
    flat = sorted(x for row in obs for x in row)
    clusters = []
    for v in flat:
        if clusters and abs(v - clusters[-1][-1]) / v * 100.0 <= tol_pct:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    n_obs = len(flat)
    null = recurrence_null(len(obs), top_k=top_k, tol_pct=tol_pct,
                           f_lo=f_lo, f_hi=f_hi)
    n_min = null["min_bursts_to_count"]
    recurring = 0
    top = []
    for c in clusters:
        # how many DISTINCT bursts contributed to this cluster
        nb = sum(1 for row in obs if any(abs(v - np.mean(c)) / np.mean(c) * 100 <= tol_pct
                                         for v in row))
        if nb >= n_min:
            recurring += len(c)
            top.append({"f_hz": float(np.mean(c)), "bursts": int(nb),
                        "spread_hz": float(max(c) - min(c))})
    top.sort(key=lambda r: -r["bursts"])
    return {"n_bursts": len(obs), "n_observations": n_obs,
            "recurrence": recurring / n_obs,
            "distinct_frequencies": len(clusters),
            "null": null, "min_bursts_to_count": n_min,
            "top_recurring": top[:24]}


# ==================================================================== GATES ==
def _verdict(rows, failures, inapplicable_reasons):
    if failures:
        return FAIL
    if not rows:
        return INAPPLICABLE
    return PASS


def g_flat(mono, sr, beats, slice_s=3.0, engine_beats=None):
    """G-FLAT -- tilt-free per-band spectral flatness against white.

    Replaces one third of `harmonic`. Answers ONE question: is this band noise
    or is it not. It has no opinion about harmonicity (G-HNR) or about order
    structure (G-ORDER), because collapsing the three was the original mistake.

    R2-4081: APPLIED TO ENGINE BEATS ONLY, and the beat-1 median bar is
    RETIRED. The rescoping is not a relaxation, it is a correction of the
    instrument's domain, and it was forced by a measurement rather than argued:
    a 33 s passage of 660 Hertzian impulses driving plate modes -- no noise
    generator anywhere in its signal path -- measures 1.263x white on this
    estimator, against 0.922x for the delivered master the client called a hair
    blower and 0.700x for literal octave-matched noise. An impulse's magnitude
    spectrum is smooth and deterministic, so its per-bin variance is LOWER than
    white noise's chi-square fluctuation and its spectral flatness is HIGHER.
    There is therefore NO value of this bar that passes a percussive positive
    control and fails the negatives: the ordering is inverted, not
    mis-thresholded. G-EVENT is the instrument that fails a hair dryer at a
    percussive beat, and it does it in the envelope, where the difference is.
    """
    engine_beats = ENGINE_BEATS if engine_beats is None else engine_beats
    W = white_sfm_reference(min(len(mono), int(8 * sr)), sr)
    per_beat, failures, inapp = {}, [], []
    for b in beats:
        if b.name not in engine_beats:
            inapp.append(f"{b.name}: not an engine beat -- per-band SFM is not "
                         f"monotone in noisiness for percussive material "
                         f"(struck plates read 1.263x white), so this "
                         f"instrument has no opinion here. G-EVENT and "
                         f"G-SUSTAIN judge this beat.")
            continue
        seg = _slice(mono, sr, b)
        if len(seg) < int(2.0 * sr):
            inapp.append(f"{b.name}: shorter than 2 s")
            continue
        slices = []
        n = int(slice_s * sr)
        for i in range(0, len(seg) - n + 1, n):
            s = per_band_sfm(seg[i:i + n], sr)
            slices.append(s / W)
        if not slices:
            inapp.append(f"{b.name}: no full {slice_s} s slice")
            continue
        med = float(np.median(slices))
        worst = float(np.max(slices))
        lim = V("G_FLAT.slice_max_ratio_of_white")
        row = {"median_ratio_of_white": med, "worst_slice_ratio_of_white": worst,
               "n_slices": len(slices), "limit": lim, "outcome": PASS}
        if worst > lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: worst 3 s slice {worst:.3f}*W > {lim:.2f}*W")
        per_beat[b.name] = row
    return {"gate": "G-FLAT", "kind": QUALITY,
            "measures": ("spectral flatness computed inside each 1/3-octave band "
                         "then averaged, 500-3000 Hz, per 3 s slice, as a ratio "
                         "of white noise through the identical pipeline"),
            "white_reference_sfm": W, "calibration": calibrate_flat(sr=sr),
            "per_beat": per_beat, "failures": failures,
            "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_hnr(mono, sr, beats, engine_beats=None):
    """G-HNR -- calibrated Boersma harmonic-to-noise ratio.

    Replaces one third of `harmonic`. The instrument is re-validated against
    synthetic mixtures of known noise fraction on every invocation, and the
    gate REFUSES to return a verdict if that calibration fails.

    R2-4081: APPLIED TO ENGINE BEATS ONLY. Boersma HNR asks "does this hold a
    note", which is the right question of a power unit and close to the
    opposite of the right question of an assembly cell. The +8 dB beat-1 bar
    was flagged at R2-4062 as never validated against a signal that should
    pass; R2-4081 built that signal and the answer is that NO BAR WORKS on this
    statistic at a percussive beat, because the ordering is inverted:
    physics-true assembly cell -4.34 dB, 660 struck plates -3.78 dB, the
    blower-into-tubes negative -0.63 dB, the delivered hair-blower master
    +0.26 dB, the master the client called a musical +0.49 dB. Every negative
    outscores every positive. The one signal in the corpus that cleared +8 dB
    at beat 1 is C8b, which R2-4081's own sweep shows is 98.3 % sustained tone
    by power -- so the bar's only validation came from a drone, and chasing the
    bar produced a drone. The `fraction_below_0db` limb is rescoped with it,
    for the same reason and by the same measurement (C9 reads 0.986).
    """
    engine_beats = ENGINE_BEATS if engine_beats is None else engine_beats
    cal = calibrate_hnr(sr=sr)
    per_beat, failures, inapp = {}, [], []
    if not cal["PASS"]:
        return {"gate": "G-HNR", "kind": QUALITY, "calibration": cal,
                "per_beat": {}, "failures": [],
                "inapplicable": ["instrument failed its own calibration"],
                "verdict": INAPPLICABLE,
                "measures": "Boersma 1993 autocorrelation HNR"}
    for b in beats:
        if b.name not in engine_beats:
            inapp.append(f"{b.name}: not an engine beat -- Boersma HNR measures "
                         f"whether the signal holds a note, and a struck "
                         f"resonator does not. G-SUSTAIN judges the pitch of "
                         f"this beat and G-EVENT judges its noisiness.")
            continue
        seg = _slice(mono, sr, b)
        h, live = boersma_hnr(seg, sr)
        if live.sum() < 40:
            inapp.append(f"{b.name}: {int(live.sum())} live windows")
            continue
        hv = h[live]
        med = float(np.median(hv))
        below = float((hv < 0.0).mean())
        row = {"median_db": med, "fraction_below_0db": below,
               "windows": int(live.sum()), "outcome": PASS,
               "p25_db": float(np.percentile(hv, 25))}
        lim_below = V("G_HNR.fraction_below_zero_max")
        if below > lim_below:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: {below:.3f} of windows below 0 dB "
                            f"> {lim_below:.2f}")
        per_beat[b.name] = row
    return {"gate": "G-HNR", "kind": QUALITY,
            "measures": ("Boersma (1993) autocorrelation HNR: the normalised "
                         "autocorrelation of the windowed signal divided by the "
                         "autocorrelation of the window, peak over f0 60-800 Hz. "
                         "A PERIODICITY test, so noise through a high-Q resonator "
                         "scores near 0 dB however narrow its peaks are."),
            "calibration": cal, "per_beat": per_beat, "failures": failures,
            "inapplicable": inapp, "verdict": _verdict(per_beat, failures, inapp)}


def g_novel(mono, sr, beats):
    """G-NOVEL -- self-similarity. Nothing in the old suite computed any such
    quantity, which is why "over and over" was structurally unmeasurable and
    why a 2 s block tiled 16.5x passed all eight gates."""
    per_beat, failures, inapp = {}, [], []
    lim = V("G_NOVEL.max_envelope_autocorrelation")
    for b in beats:
        seg = _slice(mono, sr, b)
        if len(seg) < int(4.0 * sr):
            inapp.append(f"{b.name}: shorter than 4 s")
            continue
        r = envelope_autocorrelation(seg, sr, V("G_NOVEL.lag_min_s"),
                                     min(V("G_NOVEL.lag_max_s"), (b.t1 - b.t0) / 2.0))
        row = dict(r); row["limit"] = lim; row["outcome"] = PASS
        if not np.isfinite(r["r_max"]):
            inapp.append(f"{b.name}: envelope too short for the lag range")
            continue
        if r["r_max"] > lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: r={r['r_max']:.3f} at lag {r['lag_s']:.3f} s "
                            f"> {lim:.2f}")
        per_beat[b.name] = row
    return {"gate": "G-NOVEL", "kind": QUALITY,
            "measures": ("max envelope autocorrelation of the 40-band, per-band "
                         "normalised log-spectrum envelope over lags 0.3-16 s"),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_mod(mono, sr, beats):
    """G-MOD -- modulation spectrum. A metronome puts one narrow line in the
    0.2-3 Hz band. This is the limb C6 must PASS: jitter is not a fix, and the
    gate that catches jittered repetition is G-GESTURE, not this one."""
    per_beat, failures, inapp = {}, [], []
    lim = V("G_MOD.max_peak_over_local_median_db")
    for b in beats:
        seg = _slice(mono, sr, b)
        if len(seg) < int(8.0 * sr):
            inapp.append(f"{b.name}: shorter than 8 s, 0.2 Hz is unresolvable")
            continue
        m = modulation_spectrum(seg, sr)
        row = dict(m); row["limit_db"] = lim; row["outcome"] = PASS
        if not np.isfinite(m["peak_over_local_median_db"]):
            inapp.append(f"{b.name}: modulation spectrum unmeasurable")
            continue
        if m["peak_over_local_median_db"] > lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: {m['peak_over_local_median_db']:.2f} dB peak "
                            f"at {m['peak_hz']:.3f} Hz > {lim:.1f} dB")
        per_beat[b.name] = row
    return {"gate": "G-MOD", "kind": QUALITY,
            "measures": ("peak-to-local-median of the 150-8000 Hz envelope's own "
                         "spectrum over 0.2-3 Hz"),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_gesture(mono, sr, beats):
    """G-GESTURE -- burst-to-burst timbral distinctness. THE ANTI-CHEAT GATE:
    C6 is a jittered metronome of identical gestures, which passes G-MOD and
    must fail here, so that "just add jitter" cannot buy a pass."""
    per_beat, failures, inapp = {}, [], []
    lm, lx = (V("G_GESTURE.max_mean_pairwise_similarity"),
              V("G_GESTURE.max_worst_pairwise_similarity"))
    for b in beats:
        seg = _slice(mono, sr, b)
        bursts = find_bursts(seg, sr)
        if len(bursts) < 5:
            inapp.append(f"{b.name}: {len(bursts)} bursts, fewer than 5")
            continue
        F = gesture_features(seg, sr, bursts)
        s = pairwise_similarity(F)
        row = dict(s); row["limit_mean"] = lm; row["limit_max"] = lx
        row["outcome"] = PASS
        if s["mean"] > lm:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: mean pairwise similarity {s['mean']:.3f} > {lm:.2f}")
        if s["max"] > lx:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: worst pair {s['max']:.3f} > {lx:.2f}")
        per_beat[b.name] = row
    return {"gate": "G-GESTURE", "kind": QUALITY,
            "measures": ("pairwise correlation of per-burst 24-band x 6-subframe "
                         "log-spectra with each burst's own mean removed"),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_room(mono, sr, beats, interior_beats=INTERIOR_BEATS):
    """G-ROOM -- three limbs: density (a), mobility (b), ripple (c).

    (a) is Schroeder's diffuseness test, not a literal mode count: Weyl's law
        gives 1336 modes/Hz at 1 kHz for a 4290 m3 room and NO audio analysis
        can count that many. The Weyl number is reported; the diffuseness is
        gated. Stated as a deviation from the spec rather than quietly dropped.
    """
    sab = sabine_rt60(SHOWROOM_INTERIOR_M, SHOWROOM_DECLARED_RT60_S)
    f_s = schroeder_frequency(sab["volume_m3"], SHOWROOM_DECLARED_RT60_S)
    weyl = 4.0 * math.pi * sab["volume_m3"] * 1000.0 ** 2 / 343.0 ** 3
    per_beat, failures, inapp = {}, [], []
    for b in beats:
        seg = _slice(mono, sr, b)
        if len(seg) < int(6.0 * sr):
            inapp.append(f"{b.name}: shorter than 6 s")
            continue
        row = {"outcome": PASS, "limbs": {}}
        regions = decay_regions(seg, sr)
        S, f, n_reg = tail_spectrum(seg, sr, regions)

        # THE BURST COUNT IS CAPPED (R2-4081) because the recurrence statistic
        # is a birthday problem and its chance level rises with the number of
        # observations: 0.162 at 12 bursts, 0.638 at 40, against a 0.35 bar. The
        # cap keeps the measurement on the side of that curve where it means
        # something, and `recurrence_null` reports the chance level for the
        # count actually used so the report carries its own scepticism.
        bursts = find_bursts(seg, sr, max_bursts=int(V("G_ROOM.max_bursts")))
        pr = peak_recurrence(seg, sr, bursts)

        # (a) DENSITY: are the room's FIXED lines a comb? Runs on the lines
        #     limb (b) found to recur, because a moving source is not a room.
        fixed = [t["f_hz"] for t in pr.get("top_recurring", [])
                 if t["bursts"] >= 3]
        cr = comb_regularity(fixed)
        lim = V("G_ROOM.max_fixed_line_comb_regularity")
        la = dict(cr); la["limit"] = lim; la["n_tail_regions"] = n_reg
        if not np.isfinite(cr["score"]):
            la["outcome"] = INAPPLICABLE
            inapp.append(f"{b.name}(a density): {cr['n_lines']} fixed lines, "
                         f"fewer than 6 -- with no fixed reply there is no room "
                         f"comb to measure")
        elif cr["excess_over_chance"] > lim:
            la["outcome"] = FAIL
            row["outcome"] = FAIL
            failures.append(f"{b.name}(a density): {cr['score']:.2f} of the "
                            f"{cr['n_lines']} fixed lines are harmonics of "
                            f"{cr['spacing_hz']:.2f} Hz ({cr['excess_over_chance']:.2f} "
                            f"over chance) > {lim:.2f} -- the tail is a delay-line "
                            f"bank, not a field")
        else:
            la["outcome"] = PASS
        row["limbs"]["a_density"] = la

        limb = V("G_ROOM.max_peak_recurrence")
        lb = dict(pr); lb["limit"] = limb
        if not np.isfinite(pr["recurrence"]):
            lb["outcome"] = INAPPLICABLE
            inapp.append(f"{b.name}(b mobility): {pr['n_bursts']} usable bursts")
        elif pr["recurrence"] > limb:
            lb["outcome"] = FAIL
            row["outcome"] = FAIL
            failures.append(f"{b.name}(b mobility): {pr['recurrence']:.3f} of peak "
                            f"observations recur in >=3 bursts > {limb:.2f}")
        else:
            lb["outcome"] = PASS
        row["limbs"]["b_mobility"] = lb

        cep = cepstral_ripple_of(S, sr)
        rp = fractional_octave_ripple_of(S, f)
        rip, occ = rp["ripple_db"], rp["occupancy"]
        lc = {"cepstral_peak_over_median": cep["peak_over_median"],
              "cepstral_quefrency_ms": cep["quefrency_ms"],
              "ripple_p95_minus_p5_db": rip, "band_occupancy": occ,
              "limit_cepstral": V("G_ROOM.max_cepstral_peak_over_median"),
              "limit_ripple_db": V("G_ROOM.max_ripple_p95_minus_p5_db"),
              "min_occupancy": V("G_ROOM.min_band_occupancy"),
              "n_tail_regions": n_reg,
              "outcome": PASS}
        if not np.isfinite(occ):
            lc["outcome"] = INAPPLICABLE
            inapp.append(f"{b.name}(c ripple): {n_reg} usable decay tails")
        elif occ < V("G_ROOM.min_band_occupancy"):
            lc["outcome"] = INAPPLICABLE
            inapp.append(f"{b.name}(c ripple): band occupancy {occ:.2f} < "
                         f"{V('G_ROOM.min_band_occupancy'):.2f} -- the tail is a "
                         f"line spectrum, not a reverberant field, so a ripple "
                         f"statistic would be measuring the gaps between "
                         f"partials. Limbs (a) and (b) and G-RING still apply.")
        else:
            if np.isfinite(cep["peak_over_median"]) and \
                    cep["peak_over_median"] > V("G_ROOM.max_cepstral_peak_over_median"):
                lc["outcome"] = FAIL
                row["outcome"] = FAIL
                failures.append(f"{b.name}(c ripple): cepstral peak "
                                f"{cep['peak_over_median']:.2f}x median at "
                                f"{cep['quefrency_ms']:.3f} ms > "
                                f"{V('G_ROOM.max_cepstral_peak_over_median'):.1f}x")
            if np.isfinite(rip) and rip > V("G_ROOM.max_ripple_p95_minus_p5_db"):
                lc["outcome"] = FAIL
                row["outcome"] = FAIL
                failures.append(f"{b.name}(c ripple): 1/12-oct ripple {rip:.2f} dB > "
                                f"{V('G_ROOM.max_ripple_p95_minus_p5_db'):.1f} dB")
        row["limbs"]["c_ripple"] = lc
        per_beat[b.name] = row
    return {"gate": "G-ROOM", "kind": QUALITY,
            "measures": ("(a) diffuseness of the tail as frequency-domain "
                         "autocorrelation, (b) recurrence of spectral peaks "
                         "across bursts, (c) cepstral and 1/12-octave ripple"),
            "reference": {
                "sabine": sab, "schroeder_frequency_hz": f_s,
                "weyl_modes_per_hz_at_1khz": weyl,
                "weyl_note": ("reported, not gated: 1336 modes/Hz cannot be "
                              "COUNTED at any audio analysis resolution. Limb "
                              "(a) gates the equivalent Schroeder diffuseness "
                              "condition instead. DEVIATION FROM SPEC, DECLARED.")},
            "interior_beats": list(interior_beats),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_ring(mono, sr, beats, interior_beats=INTERIOR_BEATS):
    """G-RING -- ring-through and modal decay on the RENDERED STEREO WAV, over
    ALL layers and the whole film. The gate it replaces (`waveguide`) solved
    engine.py's pipe constants algebraically at a hand-picked 11,000 rpm, never
    opened the wav, and could not see layers.assembly or the showroom tail at
    all -- which is where the tube ringing actually was."""
    sab = sabine_rt60(SHOWROOM_INTERIOR_M, SHOWROOM_DECLARED_RT60_S)
    per_beat, failures, inapp = {}, [], []
    for b in beats:
        seg = _slice(mono, sr, b)
        regs = decay_regions(seg, sr)
        if len(regs) < 3:
            inapp.append(f"{b.name}: {len(regs)} usable decay regions")
            continue
        d = band_decay_t60(seg, sr, regs)
        t60s = [r["t60_s"] for r in d["bands"] if np.isfinite(r["t60_s"])]
        if len(t60s) < 6:
            inapp.append(f"{b.name}: {len(t60s)} bands with a measurable decay")
            continue
        bb = d["broadband_t60_s"]
        worst = float(np.max(t60s))
        med = float(np.median(t60s))
        row = {"broadband_t60_s": bb, "median_band_t60_s": med,
               "worst_band_t60_s": worst, "n_bands": len(t60s),
               "n_decay_regions": len(regs), "outcome": PASS,
               "worst_band_hz": float([r["f_hz"] for r in d["bands"]
                                       if r["t60_s"] == worst][0])}
        if np.isfinite(bb) and bb > 0.05:
            ratio = worst / bb
            row["narrowband_over_broadband"] = ratio
            lim = V("G_RING.narrowband_vs_broadband_max_ratio")
            row["limit_narrowband_ratio"] = lim
            if ratio > lim:
                row["outcome"] = FAIL
                failures.append(f"{b.name}: a 1/6-oct band at "
                                f"{row['worst_band_hz']:.0f} Hz rings "
                                f"{ratio:.2f}x the broadband decay > {lim:.2f}x "
                                f"-- an under-damped isolated mode, not a room")
        if b.name in interior_beats:
            lim = V("G_RING.t60_vs_sabine_max_ratio") * sab["rt60_s"]
            row["sabine_rt60_s"] = sab["rt60_s"]
            row["t60_limit_s"] = lim
            if worst > lim:
                row["outcome"] = FAIL
                failures.append(f"{b.name}: worst band T60 {worst:.2f} s at "
                                f"{row['worst_band_hz']:.0f} Hz > {lim:.2f} s "
                                f"(Sabine {sab['rt60_s']:.2f} s x "
                                f"{V('G_RING.t60_vs_sabine_max_ratio'):.2f})")
        per_beat[b.name] = row
    return {"gate": "G-RING", "kind": QUALITY,
            "measures": ("per-1/6-octave T60 from backward decay slopes in the "
                         "film's own inter-event gaps, against the Sabine RT60 "
                         "of the declared showroom and against the broadband "
                         "decay over the same gaps"),
            "reference": {"sabine": sab},
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


# ======================================================= G-SUSTAIN / G-EVENT =
# The two instruments R2-4081 adds, and the reason they exist:
#
# THE CLIENT REJECTED THREE MASTERS FOR THREE DIFFERENT REASONS and the suite
# could name only one of them. R2-4079 was rejected as "a shitty musical" while
# the suite's beat-1 opinion of it was that it was NOT TONAL ENOUGH (G-HNR
# +0.49 dB against a +8 dB bar). Both statements are true at once, because the
# film's beat 1 is a broadband mix with a sustained pitched pad inside it: the
# median says noise, the audience hears the pad.
#
# So the quantity that was missing is not "how tonal is this beat on average".
# It is "is anything in here HOLDING A NOTE" -- a statement about the loudest
# stable thing present, not about the median of everything present. G-SUSTAIN
# tracks individual partials and asks how long they hold a pitch. G-EVENT asks
# the complementary question in the time domain, because once the spectral
# bars stop being applied to percussive beats (R2-4081, below) something still
# has to be able to fail a hair dryer.


def stft_partials(mono, sr, win=4096, hop=1024, f_lo=80.0, f_hi=4000.0,
                  prom_db=None, max_peaks=24):
    """Per-frame prominent spectral peaks, parabolically refined.

    Prominence is measured against a running median of the log spectrum over a
    +-1/3-octave neighbourhood, so a partial has to stand out of ITS OWN local
    floor. That is what makes this instrument work on a MIX: a sustained pad
    sitting inside a broadband bed is 20 dB over its neighbourhood even when
    the beat's median periodicity reads 0 dB, which is precisely the case the
    Boersma median could not see.
    """
    prom_db = V("G_SUSTAIN.peak_prominence_db") if prom_db is None else prom_db
    n = (len(mono) - win) // hop + 1
    if n < 1:
        return [], np.zeros(0)
    w = np.hanning(win)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    S = np.abs(np.fft.rfft(mono[idx] * w, axis=1)) ** 2
    f = np.fft.rfftfreq(win, 1.0 / sr)
    df = f[1]
    lo, hi = max(int(f_lo / df), 2), min(int(f_hi / df), S.shape[1] - 2)
    if hi <= lo + 4:
        return [], np.zeros(0)
    L = 10.0 * np.log10(np.maximum(S, 1e-30))

    # the local floor, on a log-spaced grid of centres and interpolated between
    kk = np.arange(L.shape[1])
    hw = np.maximum((kk * (2 ** (1 / 6.0) - 1)).astype(int), 6)
    grid = np.unique(np.clip(np.round(np.geomspace(max(lo, 1), hi, 48)).astype(int),
                             1, L.shape[1] - 1))
    med = np.empty((L.shape[0], len(grid)))
    for gi, k in enumerate(grid):
        a, b = max(k - hw[k], 0), min(k + hw[k] + 1, L.shape[1])
        med[:, gi] = np.median(L[:, a:b], axis=1)

    total = S.sum(axis=1)
    frames = []
    for t in range(L.shape[0]):
        row = L[t]
        exc = row - np.interp(kk, grid, med[t])
        k = np.arange(lo + 1, hi - 1)
        m = (row[k] > row[k - 1]) & (row[k] >= row[k + 1]) & (exc[k] > prom_db)
        kk2 = k[m]
        if len(kk2) == 0:
            frames.append(np.zeros((0, 4)))
            continue
        y0, y1, y2 = row[kk2 - 1], row[kk2], row[kk2 + 1]
        den = y0 - 2 * y1 + y2
        d = np.where(np.abs(den) > 1e-9,
                     0.5 * (y0 - y2) / np.where(np.abs(den) > 1e-9, den, 1.0), 0.0)
        d = np.clip(d, -0.5, 0.5)
        fk = (kk2 + d) * df
        amp = y1 - 0.25 * (y0 - y2) * d
        # the partial's share of the frame's own power: three bins, because a
        # Hann mainlobe is four bins wide and the peak bin alone understates it
        share = (S[t, kk2 - 1] + S[t, kk2] + S[t, kk2 + 1]) / max(total[t], 1e-30)
        order = np.argsort(-exc[kk2])[:max_peaks]
        frames.append(np.stack([fk[order], amp[order], exc[kk2][order],
                                share[order]], axis=1))
    return frames, np.arange(len(frames)) * hop / sr


def partial_tracks(frames, times, tol_cents=40.0, max_gap=2):
    """Greedy frame-to-frame association of peaks into partial tracks."""
    active, done = [], []
    for ti, pk in enumerate(frames):
        used = set()
        for tr in active:
            if len(pk):
                d = 1200.0 * np.abs(np.log2(pk[:, 0] / tr["f"][-1]))
                j = int(np.argmin(d))
                if d[j] <= tol_cents and j not in used:
                    used.add(j)
                    tr["f"].append(float(pk[j, 0]))
                    tr["e"].append(float(pk[j, 2]))
                    tr["p"].append(float(pk[j, 3]))
                    tr["t"].append(float(times[ti]))
                    tr["miss"] = 0
                    continue
            tr["miss"] += 1
        for tr in list(active):
            if tr["miss"] > max_gap:
                done.append(tr)
                active.remove(tr)
        for j in range(len(pk)):
            if j not in used:
                active.append({"f": [float(pk[j, 0])], "e": [float(pk[j, 2])],
                               "p": [float(pk[j, 3])], "t": [float(times[ti])],
                               "miss": 0})
    done.extend(active)
    return [t for t in done if len(t["f"]) >= 2]


def held_notes(tracks, hop_s, min_dur_s=None, tol_cents=None):
    """MAXIMAL RUNS INSIDE A TRACK WHOSE PITCH STAYS IN A BAND.

    A NOTE, operationally: a partial that HOLDS a pitch. This is the one
    definition in the file that separates a machine from music, and it is
    written as physics rather than as taste -- a servo under a trapezoidal move
    profile, an engine on a throttle ramp and a Doppler pass all sweep through
    the band and none of them is counted; a held note does not sweep, which is
    what "held" means.
    """
    min_dur_s = V("G_SUSTAIN.min_note_s") if min_dur_s is None else min_dur_s
    tol_cents = V("G_SUSTAIN.stability_cents") if tol_cents is None else tol_cents
    out = []
    for tr in tracks:
        f = np.asarray(tr["f"])
        t = np.asarray(tr["t"])
        c = 1200.0 * np.log2(f / f[0])
        i = 0
        while i < len(c):
            j, lo, hi = i, c[i], c[i]
            while j + 1 < len(c):
                nl, nh = min(lo, c[j + 1]), max(hi, c[j + 1])
                if nh - nl > tol_cents:
                    break
                lo, hi, j = nl, nh, j + 1
            dur = t[j] - t[i] + hop_s
            if dur >= min_dur_s:
                out.append({
                    "t0": float(t[i]), "t1": float(t[j] + hop_s), "dur": float(dur),
                    "f_hz": float(np.median(f[i:j + 1])),
                    "excess_db": float(np.median(np.asarray(tr["e"])[i:j + 1])),
                    "power_share": float(np.mean(np.asarray(tr["p"])[i:j + 1])),
                })
            i = j + 1 if j > i else i + 1
    return out


def _cover(spans, total_s, min_overlap=1):
    """Fraction of `total_s` covered by at least `min_overlap` spans."""
    if not spans or total_s <= 0:
        return 0.0
    ev = []
    for a, b in spans:
        ev.append((a, 1))
        ev.append((b, -1))
    ev.sort()
    depth, last, tot = 0, None, 0.0
    for t, d in ev:
        if depth >= min_overlap and last is not None:
            tot += t - last
        depth += d
        last = t
    return float(min(tot / total_s, 1.0))


def note_statistics(mono, sr, total_s):
    """The three numbers G-SUSTAIN gates, from one pass of the tracker."""
    frames, times = stft_partials(mono, sr)
    hop_s = float(times[1] - times[0]) if len(times) > 1 else 1024.0 / sr
    notes = held_notes(partial_tracks(frames, times), hop_s)
    spans = [(n["t0"], n["t1"]) for n in notes]
    # power share of held notes: time-weighted mean of each note's share of its
    # own frames' power, summed. Bounded by construction at 1.0.
    share = 0.0
    for n in notes:
        share += n["power_share"] * n["dur"] / max(total_s, 1e-9)
    return {
        "n_notes": len(notes),
        "note_cover": _cover(spans, total_s, 1),
        "chord_cover": _cover(spans, total_s, 3),
        "longest_note_s": max([n["dur"] for n in notes], default=0.0),
        "held_power_share": float(min(share, 1.0)),
        "loudest_notes": sorted(notes, key=lambda n: -n["dur"] * n["excess_db"])[:6],
    }


def local_dynamic_range(mono, sr, win_s=None, st_ms=None, floor_db=60.0):
    """MEDIAN, OVER SHORT WINDOWS, OF THE SPREAD OF THE SHORT-TERM LEVEL.

    Hiss is stationary and machinery is not, and that difference lives in the
    ENVELOPE, not in the spectrum -- which is the whole lesson of R2-4081. The
    p95-p5 spread of the 20 ms level inside a 2 s window is ~0.6 dB for white
    noise and ~0.6 dB for a drone, and tens of dB for anything struck. Taken as
    a median over windows so a macro fade cannot buy the number, and floored
    60 dB under the window's own peak so digital silence cannot inflate it.
    """
    win_s = V("G_EVENT.window_s") if win_s is None else win_s
    st_ms = V("G_EVENT.short_term_ms") if st_ms is None else st_ms
    w = max(int(st_ms * 1e-3 * sr), 8)
    hop = max(w // 2, 1)
    n = (len(mono) - w) // hop + 1
    if n < 8:
        return {"median_db": float("nan"), "p25_db": float("nan"), "n_windows": 0}
    idx = np.arange(w)[None, :] + hop * np.arange(n)[:, None]
    rms = np.sqrt((mono[idx] ** 2).mean(axis=1))
    L = 20.0 * np.log10(np.maximum(rms, 1e-12))
    per = max(int(win_s * sr / hop), 8)
    peak = L.max()
    vals = []
    for i in range(0, len(L) - per + 1, per):
        seg = L[i:i + per]
        if seg.max() < peak - 40.0:      # a silent window is not a measurement
            continue
        seg = np.maximum(seg, seg.max() - floor_db)
        vals.append(float(np.percentile(seg, 95) - np.percentile(seg, 5)))
    if not vals:
        return {"median_db": float("nan"), "p25_db": float("nan"), "n_windows": 0}
    return {"median_db": float(np.median(vals)),
            "p25_db": float(np.percentile(vals, 25)),
            "n_windows": len(vals)}


def g_sustain(mono, sr, beats, percussive_beats=None):
    """G-SUSTAIN -- IS ANYTHING HOLDING A NOTE.

    The gate that would have caught R2-4079. It runs only on beats whose
    protagonist is not the engine, because an engine at constant rpm HOLDS a
    pitch by physics and gating it for that would be an error of the same
    family as the one being corrected.
    """
    pb = PERCUSSIVE_BEATS if percussive_beats is None else percussive_beats
    per_beat, failures, inapp = {}, [], []
    for b in beats:
        if b.name not in pb:
            inapp.append(f"{b.name}: an engine beat -- a power unit holds a "
                         f"pitch by physics and G-ORDER/G-IDENTITY are the "
                         f"instruments that judge it")
            continue
        seg = _slice(mono, sr, b)
        if len(seg) < int(4.0 * sr):
            inapp.append(f"{b.name}: shorter than 4 s")
            continue
        st = note_statistics(seg, sr, (b.t1 - b.t0))
        row = dict(st); row["outcome"] = PASS
        row["limits"] = {
            "note_cover": V("G_SUSTAIN.max_note_cover"),
            "chord_cover": V("G_SUSTAIN.max_chord_cover"),
            "held_power_share": V("G_SUSTAIN.max_held_power_share"),
        }
        if st["note_cover"] > V("G_SUSTAIN.max_note_cover"):
            row["outcome"] = FAIL
            failures.append(f"{b.name}: something holds a pitch for "
                            f"{st['note_cover']:.3f} of the beat > "
                            f"{V('G_SUSTAIN.max_note_cover'):.2f}")
        if st["chord_cover"] > V("G_SUSTAIN.max_chord_cover"):
            row["outcome"] = FAIL
            failures.append(f"{b.name}: three or more pitches are held at once "
                            f"for {st['chord_cover']:.3f} of the beat > "
                            f"{V('G_SUSTAIN.max_chord_cover'):.2f} -- that is a "
                            f"chord, not a machine")
        if st["held_power_share"] > V("G_SUSTAIN.max_held_power_share"):
            row["outcome"] = FAIL
            failures.append(f"{b.name}: held notes carry "
                            f"{st['held_power_share']:.3f} of the beat's power > "
                            f"{V('G_SUSTAIN.max_held_power_share'):.2f}")
        per_beat[b.name] = row
    return {"gate": "G-SUSTAIN", "kind": QUALITY,
            "measures": ("sinusoidal partials tracked frame to frame; a NOTE is "
                         "a partial that stays inside "
                         f"{V('G_SUSTAIN.stability_cents'):.0f} cents for "
                         f"{V('G_SUSTAIN.min_note_s'):.2f} s while standing "
                         f"{V('G_SUSTAIN.peak_prominence_db'):.0f} dB over its "
                         "own +-1/3-octave floor. Gated on how much of the beat "
                         "holds a note, how much of it holds three at once, and "
                         "what share of the power they carry."),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


# ---------------------------------------- the absolute-audibility estimators -
# R2-4147. These are the only ABSOLUTE measurements in this file: everything
# else is a statement about a signal's own internal structure, and these are
# statements about whether a listener's ear is reached at all.

# THE CALIBRATION, DECLARED AND DERIVED. EBU R 128 / Tech 3343 monitoring
# practice puts a -23 LUFS programme at 73 dB SPL at the reference position.
# The film is delivered at -23.0 LUFS (`master.TARGET_LUFS_I`). A domestic
# viewer does not run reference level; 12 dB under it is the median domestic
# figure and it is the one gated on, because the client watched this on a
# laptop and a passage that is inaudible at home is inaudible.
REF_SPL_AT_TARGET_LUFS = 73.0
DOMESTIC_OFFSET_DB = 12.0
# NR-25 (ISO R 1996): octave-band L = a + b*N. ISO/ANSI recommend NR 25-30 for
# a living room; 25 is the QUIET end and therefore the conservative choice for
# a bar -- material inaudible in the quietest domestic room is inaudible.
NR_BANDS = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0,
                     8000.0])
NR_A = np.array([55.4, 35.5, 22.0, 12.0, 4.8, 0.0, -3.5, -6.1, -8.0])
NR_B = np.array([0.681, 0.790, 0.870, 0.930, 0.974, 1.000, 1.015, 1.025, 1.030])
ROOM_NR = 25.0
ART_LO, ART_HI = 4.0, 100.0
ART_ENV_HZ = 400.0


def threshold_in_quiet_db(f_hz):
    """ISO 226 / Terhardt's closed form for the absolute threshold of hearing,
    dB SPL against frequency. A PUBLISHED curve, not a fit to this film."""
    f = np.maximum(np.asarray(f_hz, dtype=np.float64), 20.0) / 1000.0
    return (3.64 * f ** -0.8
            - 6.5 * np.exp(-0.6 * (f - 3.3) ** 2)
            + 1e-3 * f ** 4)


def room_noise_third_octave_db(f_hz, nr=ROOM_NR):
    """NR-`nr` octave levels interpolated in log f, spread to third-octaves.
    An octave holds three thirds, so each third is 10*log10(3) = 4.77 dB down."""
    oct_l = NR_A + NR_B * nr
    lf = np.log2(np.maximum(np.asarray(f_hz, dtype=np.float64), 20.0))
    return np.interp(lf, np.log2(NR_BANDS), oct_l) - 10.0 * np.log10(3.0)


def masked_threshold_db(f_hz, nr=ROOM_NR):
    """What a band must exceed to be heard at all, in a real domestic room."""
    return np.maximum(threshold_in_quiet_db(f_hz),
                      room_noise_third_octave_db(f_hz, nr))


def third_octave_centres(f_lo=25.0, f_hi=16000.0):
    """IEC 61260 preferred centres. Audibility is decided inside a critical
    band and a third-octave is within ~1.4x of the ERB where it matters."""
    n0 = int(np.round(3.0 * np.log2(f_lo / 1000.0)))
    n1 = int(np.round(3.0 * np.log2(f_hi / 1000.0)))
    return 1000.0 * 2.0 ** (np.arange(n0, n1 + 1) / 3.0)


def band_spl(seg, sr, full_scale_spl_db, centres=None):
    """Per-third-octave SPL of one segment at the declared calibration."""
    if centres is None:
        centres = third_octave_centres()
    seg = np.asarray(seg, dtype=np.float64)
    n = len(seg)
    if n < 256:
        return centres, np.full(len(centres), -np.inf)
    nfft = int(2 ** np.ceil(np.log2(min(max(n, 4096), 65536))))
    f, pxx = _sig.welch(seg, fs=sr, nperseg=min(nfft, n), window="hann",
                        scaling="spectrum")
    out = np.empty(len(centres))
    for i, fc in enumerate(centres):
        m = (f >= fc / 2 ** (1 / 6)) & (f < fc * 2 ** (1 / 6))
        p = float(pxx[m].sum()) if m.any() else 0.0
        out[i] = 10.0 * np.log10(max(p, 1e-30)) + full_scale_spl_db
    return centres, out


def event_mask(mono, sr, guard_s=0.35, hop_s=0.010):
    """WHICH SAMPLES ARE 'BETWEEN THE EVENTS', measured off the signal itself.

    A frame is EVENT if its 20 ms level is BOTH within 12 dB of the passage's
    p98 AND more than 6 dB over the passage's own median. The mask is dilated
    FORWARD by `guard_s` so an impact's own decay -- which is the thing a
    listener does hear -- is never counted as the gap it decays into.
    Everything else is GAP.

    THE SECOND CONDITION IS NOT A REFINEMENT, IT IS WHAT MAKES THE GATE WORK ON
    THE CASES IT EXISTS FOR. With only the p98 test, a STATIONARY signal has
    p98 ~ p50, so every frame lands within 12 dB of the top and the whole
    passage is marked EVENT -- leaving no gap to measure and returning
    INAPPLICABLE. Measured, before this was fixed: the hair dryer C1, the drone
    C8b and THIRTY-THREE SECONDS OF DIGITAL SILENCE all came back INAPPLICABLE
    from the one gate built to fail them. A gate that goes blind on its own
    negative controls is the failure this file has already documented twice
    (G-HNR at beat 1, G-RING's `nan` broadband).

    With both conditions, a stationary passage is ALL GAP -- which is correct
    and is the whole point: a hair dryer has no events, so it is nothing but
    the material between them, and it is then judged on whether that material
    is articulated. Silence is likewise all gap, and gap containing nothing.
    """
    w = max(int(0.020 * sr), 8)
    hop = max(int(hop_s * sr), 1)
    n = (len(mono) - w) // hop + 1
    if n < 8:
        return np.zeros(len(mono), dtype=bool)
    idx = np.arange(w)[None, :] + hop * np.arange(n)[:, None]
    L = 20.0 * np.log10(np.maximum(np.sqrt((mono[idx] ** 2).mean(axis=1)), 1e-12))
    hot = (L > (np.percentile(L, 98) - 12.0)) & (L > np.median(L) + 6.0)
    k = int(guard_s / hop_s)
    if k > 0:
        hot = np.convolve(hot.astype(float), np.ones(k + 1), mode="full")[:n] > 0
    out = np.zeros(len(mono), dtype=bool)
    for i in np.flatnonzero(hot):
        out[i * hop:i * hop + w] = True
    return out


def gap_audibility(mono, sr, lufs_i, seg_s=1.0, spl_offset_db=DOMESTIC_OFFSET_DB):
    """SENSATION LEVEL OF THE GAPS, in dB over the masked threshold.

    A listener sets the volume by the PROGRAMME, so a film delivered at
    `lufs_i` and played at (REF - offset) dB SPL puts 0 dBFS at
    (REF - offset) - lufs_i dB SPL, and every band is measured against that.

    Reported as the MEDIAN over 1 s gap segments, so one busy second cannot
    carry a beat -- `local_dynamic_range`'s own reasoning, pointed at the
    opposite quantity.
    """
    mono = np.asarray(mono, dtype=np.float64)
    fs_spl = (REF_SPL_AT_TARGET_LUFS - spl_offset_db) - lufs_i
    gap = ~event_mask(mono, sr)
    centres = third_octave_centres()
    thr = masked_threshold_db(centres)
    ns = int(seg_s * sr)
    rows = []
    for i in range(0, len(mono) - ns + 1, ns):
        g = gap[i:i + ns]
        if g.mean() < 0.60:
            continue
        s = mono[i:i + ns][g]
        if len(s) < int(0.20 * sr):
            continue
        _, spl = band_spl(s, sr, fs_spl, centres)
        sl = spl - thr
        rows.append((float(np.max(sl)), int((sl > 0).sum()),
                     float(10.0 * np.log10(np.sum(10.0 ** (spl / 10.0))))))
    if not rows:
        return {"median_sensation_db": float("nan"),
                "median_bands_audible": float("nan"),
                "median_gap_spl_db": float("nan"),
                "gap_fraction": float(gap.mean()),
                "why": "no segment of this passage is mostly gap"}
    # A GAP THAT CONTAINS NOTHING IS A MEASUREMENT, NOT A MISSING ONE. Digital
    # silence gives -inf here, and -inf must reach the gate as a FAIL rather
    # than as a nan that reads INAPPLICABLE -- which is precisely how the first
    # version of this gate scored 33 s of silence as "not applicable".
    a = np.nan_to_num(np.array(rows), neginf=-400.0, posinf=400.0)
    return {"median_sensation_db": float(np.median(a[:, 0])),
            "median_bands_audible": float(np.median(a[:, 1])),
            "median_gap_spl_db": float(np.median(a[:, 2])),
            "p10_sensation_db": float(np.percentile(a[:, 0], 10)),
            "n_gap_segments": len(rows),
            "full_scale_spl_db": fs_spl,
            "gap_fraction": float(gap.mean())}


def articulation_modulation_index(mono, sr, f_lo=ART_LO, f_hi=ART_HI):
    """RMS OF THE ENVELOPE'S ARTICULATION BAND OVER THE ENVELOPE'S MEAN.

    THE ONE THING IT MUST NOT BE IS TROUGH DEPTH. A dense machine and an empty
    gap both make `local_dynamic_range` large -- the machine because its
    contacts are loud, the gap because its floor is low -- and that degeneracy
    is what steered R2-4141 into silence. A MODULATION INDEX cannot be bought
    with level: it is normalised by the envelope's own mean, so a passage with a
    SMOOTH envelope scores low however loud it is, and a passage with no signal
    has no envelope and returns nan rather than a perfect score.

    4-100 Hz is not chosen. 4 Hz is below the slowest rate an actuator or a
    hand produces, and 100 Hz is the roughness boundary above which the ear
    stops resolving separate events and starts hearing timbre -- above it a
    train IS a tone, which is the failure this project has shipped four times.

    Stationary noise is not zero here and must not be: a band-limited noise
    envelope fluctuates by its own Rayleigh statistics. White noise measures
    0.0849 and that is the floor of the scale, not an error.
    """
    mono = np.asarray(mono, dtype=np.float64)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    dec = max(int(sr // (4 * ART_ENV_HZ)), 1)
    e = _sig.sosfiltfilt(_sig.butter(4, ART_ENV_HZ, btype="lowpass", fs=sr,
                                     output="sos"), np.abs(mono))[::dec]
    fs = sr / dec
    mu = float(np.mean(e))
    if mu <= 1e-12 or len(e) < int(4 * fs):
        return {"ami": float("nan"), "why": "no envelope: nothing is here"}
    # detrend at f_lo/2 so a macro fade cannot enter the band
    e = _sig.sosfiltfilt(_sig.butter(2, f_lo * 0.5, btype="highpass", fs=fs,
                                     output="sos"), e)
    band = _sig.sosfiltfilt(_sig.butter(4, [f_lo, f_hi], btype="bandpass",
                                        fs=fs, output="sos"), e)
    return {"ami": float(np.sqrt(np.mean(band ** 2)) / mu), "env_fs": fs}


# ------------------------------------------------------------- G-PRESENCE ---
# R2-4147. THE SUITE HAD NO CHECK FOR "IS ANYTHING AUDIBLE HERE", AND SILENCE
# PASSED EVERY GATE IN IT.
#
# Every quality instrument above is RELATIVE: it measures structure WITHIN
# whatever it is handed. G-EVENT reads the spread of the short-term level,
# G-SUSTAIN the cover of held partials, G-MOD the depth of a modulation,
# G-FLAT the shape of a spectrum. Feed any of them digital silence and it scores
# perfectly -- infinite local dynamic range, zero note cover, no modulation --
# so a beat that contains NOTHING is, to this suite, a clean beat.
#
# That is not a hypothetical. R2-4141's CELL_GAIN bracket had a measured upper
# bound and an ARGUED lower bound, silence sat inside it, and the suite could
# not see the difference. `tools/r2_4147_audible.py` measured the delivered
# master: between the part impacts, beat 1 reaches 26.4 dB SPL broadband at
# domestic playback and its most audible third-octave sits 14.0 dB BELOW the
# masked threshold in an NR-25 room. ZERO bands clear threshold. The client
# said "now beat 1 i dont hear anything until the tubes play" and the client
# was reading an instrument the suite did not have.
#
# TWO LIMBS, AND NEITHER IS SUFFICIENT ALONE. THAT IS THE POINT.
#
#   AUDIBLE -- the sensation level of the material BETWEEN the events, in dB
#     over the masked threshold of a quiet domestic room. It is ABSOLUTE: it
#     depends on the delivered loudness and a declared playback calibration,
#     not on the passage's own internal contrast. Silence scores -inf.
#
#   AMI -- the articulation modulation index, the envelope's 4-100 Hz RMS over
#     its mean. It says whether what is there is a train of distinct events or
#     a smooth bed. It is level-invariant by construction.
#
# MEASURED, AND THE MEASUREMENT IS WHY BOTH ARE HERE (`r2_4147_event_diag.py`,
# the film's own impacts plus one filler, all fillers at matched level):
#
#     filler            AMI      AUDIBLE dB
#     nothing         0.8037       -140.71     <- best AMI in the table
#     the cell        0.8179        +14.56
#     a hair dryer    0.3309         (aud.)
#     a drone         0.1807         (aud.)
#
# SILENCE HAS THE SECOND-BEST AMI IN THAT TABLE AND IS INAUDIBLE; the hair
# dryer is audible and has the worst AMI but one. Either limb alone can be
# satisfied by the defect the other one catches, which is exactly the trap
# G-EVENT fell into, and it is why this gate has two limbs rather than a
# composite score that could be traded off between them.
_T("G_PRESENCE.min_gap_sensation_db", 0.0, "dB over masked threshold",
   "physics",
   "ZERO, and a bar at zero cannot be accused of being tuned: it is the "
   "definition of audible. A third-octave band is heard when its level exceeds "
   "the greater of the ISO 226 / Terhardt threshold in quiet and the ambient "
   "of the room it is played in. The room is NR-25 (ISO R 1996 noise rating, "
   "L = a + b*N per octave, minus 10*log10(3) for a third), which is the QUIET "
   "END of ISO/ANSI's 25-30 domestic recommendation -- chosen deliberately, "
   "because material that is inaudible even in the quietest living room is "
   "inaudible. Playback is the R 128 / Tech 3343 reference of 73 dB SPL for a "
   "-23 LUFS programme, less 12 dB for domestic listening. The delivered "
   "R2-4141 master reads -13.99 dB here.")
_T("G_PRESENCE.min_articulation_index", 0.50, "dimensionless",
   "control-derived",
   "THE CORPUS SETS IT AND THE CORPUS IS PRINTED (`tools/r2_4147_sep.py`, all "
   "at beat 1 on the shipped estimator): POSITIVE C9 assembly cell 1.4835. "
   "NEGATIVES: C3 blower-into-tubes 0.5589, C1 the hair dryer 0.2823, white "
   "noise 0.0849, C8b the drone 0.0364. The film's own part impacts read "
   "0.8037. 0.50 sits under the loudest negative rather than at the geometric "
   "midpoint, and that is DELIBERATE AND CONSERVATIVE: this corpus has exactly "
   "ONE positive at beat 1, so there is no spread to estimate and a bar placed "
   "at the midpoint (0.91) would be a bar drawn through a single point. It is "
   "placed to fail every negative the corpus contains and no higher. IT IS NOT "
   "A TARGET -- C9 is the target, and anything reading near 0.50 is passing by "
   "a hair and should be read as such.")


def g_presence(mono, sr, beats, lufs_i=None, percussive_beats=None):
    """G-PRESENCE -- IS ANYTHING AUDIBLE BETWEEN THE EVENTS, AND IS IT A MACHINE.

    `lufs_i` is the delivered programme loudness and it is what makes this gate
    ABSOLUTE. Without it there is no calibration and the gate reports
    INAPPLICABLE rather than guessing, because a guessed calibration is how an
    absolute measurement quietly becomes a relative one.
    """
    pb = PERCUSSIVE_BEATS if percussive_beats is None else percussive_beats
    per_beat, failures, inapp = {}, [], []
    lim_a = V("G_PRESENCE.min_gap_sensation_db")
    lim_m = V("G_PRESENCE.min_articulation_index")
    # -inf IS A MEASUREMENT AND IT IS THE WORST ONE. `loudness_lufs` returns
    # -inf for a programme with no signal in it, and an earlier version of this
    # guard treated that the same as "no calibration supplied" -- so THIRTY-
    # THREE SECONDS OF DIGITAL SILENCE came back INAPPLICABLE from the gate
    # whose entire reason for existing is that silence passes everything else.
    # A silent programme fails here, by name.
    if lufs_i is not None and np.isneginf(lufs_i):
        return {"gate": "G-PRESENCE", "kind": QUALITY,
                "per_beat": {b.name: {"outcome": FAIL} for b in beats
                             if b.name in pb},
                "failures": ["the programme has no measurable loudness at all: "
                             "there is no signal here"],
                "inapplicable": [], "verdict": FAIL}
    if lufs_i is None or not np.isfinite(lufs_i):
        return {"gate": "G-PRESENCE", "kind": QUALITY, "per_beat": {},
                "failures": [], "inapplicable": ["no programme loudness: this "
                                                 "gate is absolute and will "
                                                 "not guess a calibration"],
                "verdict": INAPPLICABLE}
    for b in beats:
        if b.name not in pb:
            inapp.append(f"{b.name}: an engine beat -- a power unit running is "
                         f"audible by physics and G-ORDER judges it")
            continue
        seg = _slice(mono, sr, b)
        if len(seg) < int(4.0 * sr):
            inapp.append(f"{b.name}: shorter than 4 s")
            continue
        a = gap_audibility(seg, sr, lufs_i)
        m = articulation_modulation_index(seg, sr)
        row = {"gap_sensation_db": a.get("median_sensation_db", float("nan")),
               "gap_bands_audible": a.get("median_bands_audible", float("nan")),
               "gap_spl_db": a.get("median_gap_spl_db", float("nan")),
               "gap_fraction": a.get("gap_fraction", float("nan")),
               "articulation_index": m.get("ami", float("nan")),
               "limits": {"gap_sensation_db": lim_a,
                          "articulation_index": lim_m},
               "outcome": PASS}
        if not np.isfinite(row["gap_sensation_db"]):
            inapp.append(f"{b.name}: {a.get('why', 'no gap segments')}")
            continue
        if row["gap_sensation_db"] < lim_a:
            row["outcome"] = FAIL
            failures.append(
                f"{b.name}: between the events the loudest third-octave sits "
                f"{row['gap_sensation_db']:.2f} dB relative to the masked "
                f"threshold of a quiet room, i.e. {-row['gap_sensation_db']:.1f} "
                f"dB UNDER it, with {row['gap_bands_audible']:.0f} bands "
                f"audible -- there is nothing here to hear")
        # A nan ARTICULATION INDEX MEANS "no envelope: nothing is here", which
        # is a FAIL and not an absent measurement. The only quantity that
        # returns it is silence, and silence is what this gate exists to catch.
        if not np.isfinite(row["articulation_index"]):
            row["outcome"] = FAIL
            failures.append(
                f"{b.name}: no envelope at all -- there is no signal here to "
                f"be articulated")
        elif row["articulation_index"] < lim_m:
            row["outcome"] = FAIL
            failures.append(
                f"{b.name}: articulation index {row['articulation_index']:.4f} "
                f"< {lim_m:.2f} -- what is between the events is a smooth bed, "
                f"not a train of distinct events")
        per_beat[b.name] = row
    return {"gate": "G-PRESENCE", "kind": QUALITY,
            "measures": ("the sensation level of the material BETWEEN the "
                         "events, in dB over the greater of the threshold in "
                         "quiet and an NR-25 room, at R 128 playback less 12 dB "
                         "for domestic listening; and the articulation "
                         "modulation index, the envelope's 4-100 Hz RMS over "
                         "its mean. ABSOLUTE, so silence fails it, which is the "
                         "one thing every other quality gate here scores as "
                         "perfect."),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


def g_event(mono, sr, beats, percussive_beats=None):
    """G-EVENT -- IS IT EVENTFUL, measured in the time domain.

    THE INSTRUMENT THAT REPLACES G-FLAT AND G-HNR ON PERCUSSIVE BEATS. Both of
    those read a dense shower of struck plates as WORSE than the hair dryer the
    client rejected (R2-4081 measured 1.263x white and -3.78 dB on a passage
    containing no noise generator at all), so neither can be the instrument
    that fails a hair dryer at beat 1. This one can: a hair dryer is stationary
    and an assembly cell is not.
    """
    pb = PERCUSSIVE_BEATS if percussive_beats is None else percussive_beats
    per_beat, failures, inapp = {}, [], []
    lim = V("G_EVENT.min_local_dynamic_range_db")
    for b in beats:
        if b.name not in pb:
            inapp.append(f"{b.name}: an engine beat -- a power unit is "
                         f"legitimately stationary and G-ORDER judges it")
            continue
        seg = _slice(mono, sr, b)
        if len(seg) < int(4.0 * sr):
            inapp.append(f"{b.name}: shorter than 4 s")
            continue
        d = local_dynamic_range(seg, sr)
        row = dict(d); row["limit_db"] = lim; row["outcome"] = PASS
        if not np.isfinite(d["median_db"]):
            inapp.append(f"{b.name}: no live window")
            continue
        # THE MEDIAN, NOT THE QUARTILE, and the choice is a measurement:
        # beat 1's arrivals are CLUSTERED, so the quietest quarter of its 2 s
        # windows lands in the gaps between clusters, where the only content is
        # room tone and tail and where stationarity is correct. On the
        # percussive positive the p25 reads 8.72 dB against blower-into-tubes'
        # 8.07 -- no separation at all -- while the median reads 21.36 against
        # 8.79. The quartile measures the silence; the median measures the beat.
        if d["median_db"] < lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: the median 2 s window spans only "
                            f"{d['median_db']:.2f} dB of 20 ms level < "
                            f"{lim:.1f} dB -- stationary, i.e. a bed and not "
                            f"a sequence of events")
        per_beat[b.name] = row
    return {"gate": "G-EVENT", "kind": QUALITY,
            "measures": ("p95-p5 of the 20 ms short-term level inside each 2 s "
                         "window, taken as the 25th percentile over windows so "
                         "neither a macro fade nor one busy passage can carry "
                         "the beat"),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


# --------------------------------------------------------------- G-ORDER ----
def predicted_order_lines(f_lo, f_hi, f_fund):
    k = np.arange(1, int(f_hi / max(f_fund, 1e-6)) + 2)
    f = f_fund * k
    return f[(f >= f_lo) & (f <= f_hi)]


def order_energy_fraction(seg, sr, f_fund, f_lo=300.0, f_hi=4000.0,
                          tol_pct=1.5, win=None):
    win = win or (1 << int(np.log2(min(len(seg), int(0.5 * sr)))))
    if win < 4096 or len(seg) < win:
        return float("nan")
    P, f = _stft_power(seg, sr, win=win, hop=win // 2)
    if P.shape[0] < 1:
        return float("nan")
    S = P.mean(axis=0)
    m = (f >= f_lo) & (f <= f_hi)
    tot = float(S[m].sum())
    if tot <= 0:
        return float("nan")
    on = np.zeros_like(f, bool)
    for fl in predicted_order_lines(f_lo, f_hi, f_fund):
        on |= (np.abs(f - fl) / fl * 100.0 <= tol_pct)
    return float(S[m & on].sum() / tot)


def g_order(mono, sr, beats, rpm_at, order=ENGINE_FIRING_ORDER, doppler_at=None,
            throttle_at=None, engine_beats=("2_launch", "4_transit", "5_lap")):
    """G-ORDER -- is the line spectrum a COMB THAT MOVES WITH THE TELEMETRY?

    Replaces one third of `harmonic`, and it is the limb that C3 (noise through
    fixed inharmonic pipes) cannot fake: its peaks are narrow and strong and
    they do not move, and rpm here comes from TELEMETRY, which is independent
    ground truth and not estimated from the audio.
    """
    per_beat, failures, inapp = {}, [], []
    lim = V("G_ORDER.min_energy_on_predicted_lines")
    tol = V("G_ORDER.line_tolerance_pct")
    for b in beats:
        if b.name not in engine_beats:
            inapp.append(f"{b.name}: not an engine beat by declaration "
                         f"(engine beats: {list(engine_beats)})")
            continue
        seg = _slice(mono, sr, b)
        step = 0.5
        fr, ctrl = [], []
        t = b.t0 + 0.25
        while t + step <= b.t1:
            i0, i1 = int((t - b.t0) * sr), int((t - b.t0 + step) * sr)
            rpm = float(rpm_at(t))
            if throttle_at is not None and float(throttle_at(t)) <= 0.10:
                t += step
                continue
            if not np.isfinite(rpm) or rpm < 3000.0:
                t += step
                continue
            ratio = float(doppler_at(t)) if doppler_at is not None else 1.0
            f_fund = order * rpm / 60.0 * ratio
            v = order_energy_fraction(seg[i0:i1], sr, f_fund, tol_pct=tol)
            if np.isfinite(v):
                fr.append(v)
                # SHUFFLE CONTROL: the same window against a deliberately wrong
                # fundamental. If the film scores no better than this, the comb
                # is not locked to the telemetry and the number means nothing.
                ctrl.append(order_energy_fraction(seg[i0:i1], sr,
                                                  f_fund * 1.37, tol_pct=tol))
            t += step
        if len(fr) < 6:
            inapp.append(f"{b.name}: {len(fr)} windows on throttle with a "
                         f"telemetry rpm")
            continue
        med = float(np.median(fr))
        cm = float(np.median(ctrl))
        row = {"median_energy_on_lines": med, "windows": len(fr),
               "CONTROL_wrong_fundamental_median": cm,
               "limit": lim, "line_tolerance_pct": tol, "outcome": PASS}
        if med < lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: {med:.3f} of 300-4000 Hz energy on lines "
                            f"predicted from telemetry rpm < {lim:.2f} "
                            f"(wrong-fundamental control {cm:.3f})")
        per_beat[b.name] = row
    return {"gate": "G-ORDER", "kind": QUALITY,
            "measures": (f"fraction of 300-4000 Hz energy within +-{tol}% of "
                         f"f = {order}*k*rpm/60, rpm from TELEMETRY, "
                         f"Doppler-shifted by the render's own retarded-time solve"),
            "engine_order": order,
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


# ------------------------------------------------------------ G-IDENTITY ----
def _order_line_db(seg, sr, f_fund, orders, tol_pct=1.5, win=None):
    """Level of the line at f = m*f_rev, for each engine order m.

    Returns {m: (level_db, over_floor_db)}.

    TWO NUMBERS, AND THE REASON IS A BUG THIS ESTIMATOR HAD FIRST. The obvious
    construction -- peak bin over the median of a local neighbourhood -- reads
    the LEAKAGE ENVIRONMENT as much as the line. On the synthesised constant-rpm
    control, whose true line powers are +51.18 / +49.34 dB at orders 1.5 and 3
    (a ratio of +1.84 dB, exactly what the construction puts there), that
    estimator returned +85.1 / +97.6 dB and a ratio of -12.4 dB, because the
    Hanning skirt of the very strong low orders raises the floor around 275 Hz
    far more than around 550 Hz. It would have failed a control that is correct
    by construction, and the number it failed it on was an artefact of the
    instrument.
    #
    So:
      * `level_db` is the SUMMED power inside the line's own tolerance band
        with the local floor's contribution subtracted (floor median x the
        band's bin count). Summing rather than peak-picking is necessary
        because a line at 1375 Hz with a 0.3 % rpm wander smears over several
        bins while a line at 275 Hz does not -- peak-picking under-reads high
        orders by 15 dB for that reason alone. This is the number order ratios
        are taken from.
      * `over_floor_db` is that excess against the same local floor, and it is
        used ONLY as a presence test: a line that does not stand clear of its
        own neighbourhood is not a line.
    """
    win = win or (1 << int(np.log2(max(min(len(seg), int(0.5 * sr)), 4096))))
    if win < 4096 or len(seg) < win:
        return {m: (float("nan"), float("nan")) for m in orders}
    P, f = _stft_power(seg, sr, win=win, hop=win // 2)
    if P.shape[0] < 1:
        return {m: (float("nan"), float("nan")) for m in orders}
    S = P.mean(axis=0)
    out = {}
    for m in orders:
        fl = f_fund * m
        if fl < 30.0 or fl > sr * 0.45:
            out[m] = (float("nan"), float("nan"))
            continue
        onm = np.abs(f - fl) / fl * 100.0 <= tol_pct
        near = (np.abs(f - fl) / fl <= 0.25) & ~onm
        if onm.sum() < 1 or near.sum() < 8:
            out[m] = (float("nan"), float("nan"))
            continue
        floor = float(np.median(S[near])) * float(onm.sum())
        band = float(S[onm].sum())
        excess = max(band - floor, 1e-30)
        out[m] = (float(10.0 * np.log10(excess)),
                  float(10.0 * np.log10(excess / max(floor, 1e-30))))
    return out


def g_identity(mono, sr, beats, rpm_at, order=1.5, doppler_at=None,
               throttle_at=None, engine_beats=("2_launch", "4_transit", "5_lap")):
    """G-IDENTITY -- is this the FIA Art. 5.2.10 firing geometry, or an evenly
    fired V6 with a half order that is identically zero?

    G-ORDER asks whether the comb tracks the telemetry. This asks a different
    question that G-ORDER cannot: WHICH comb. An evenly fired V6 puts nothing at
    all at order 1.5 and has no notch at order 6; the three-journal geometry puts
    order 1.5 at a derived -5.34 dB under order 3 and nulls order 6 exactly. Both
    are lines that MOVE WITH RPM, so neither can be faked by a fixed filter --
    the order-6 notch in particular slides 400 Hz to 1200 Hz across this film.

    Bars are DERIVED, not measured: no F1 spectrum was obtainable. See the
    threshold notes.
    """
    per_beat, failures, inapp = {}, [], []
    lo_lim = V("G_IDENTITY.half_order_min_db_rel_order3")
    hi_lim = V("G_IDENTITY.half_order_max_db_rel_order3")
    notch_lim = V("G_IDENTITY.min_order6_notch_db")
    min_win = int(V("G_IDENTITY.min_windows"))
    pres = V("G_IDENTITY.line_present_db_over_floor")
    tol = V("G_ORDER.line_tolerance_pct")
    ORDERS = (1.5, 3.0, 4.5, 6.0, 7.5)
    if order != 1.5:
        return {"gate": "G-IDENTITY", "kind": QUALITY, "per_beat": {},
                "failures": [], "verdict": INAPPLICABLE,
                "inapplicable": [f"the render declares firing order {order}, not "
                                 f"1.5 -- there is no half order to measure and "
                                 f"no order-6 notch to find. This is the "
                                 f"`half_order_weight = 0.0` engine and the gate "
                                 f"says so rather than failing it for being "
                                 f"what it declares itself to be."],
                "measures": "order-1.5 presence and the order-6 notch"}
    for b in beats:
        if b.name not in engine_beats:
            inapp.append(f"{b.name}: not an engine beat by declaration")
            continue
        seg = _slice(mono, sr, b)
        step = 0.5
        rows = []
        t = b.t0 + 0.25
        while t + step <= b.t1:
            i0, i1 = int((t - b.t0) * sr), int((t - b.t0 + step) * sr)
            rpm = float(rpm_at(t))
            if throttle_at is not None and float(throttle_at(t)) <= 0.10:
                t += step
                continue
            if not np.isfinite(rpm) or rpm < 3000.0:
                t += step
                continue
            ratio = float(doppler_at(t)) if doppler_at is not None else 1.0
            f_rev = rpm / 60.0 * ratio
            d = _order_line_db(seg[i0:i1], sr, f_rev, ORDERS, tol_pct=tol)
            # the REFERENCE orders must be present for the ratio to mean
            # anything; order 6 is allowed -- required, in fact -- to be absent
            if (all(np.isfinite(d[m][0]) for m in ORDERS)
                    and all(d[m][1] > pres for m in (3.0, 4.5, 7.5))):
                rows.append(d)
            t += step
        if len(rows) < min_win:
            inapp.append(f"{b.name}: {len(rows)} windows with orders 3/4.5/7.5 "
                         f"standing more than {pres:.0f} dB clear of their own "
                         f"local floor, out of a required {min_win}")
            continue
        med = {m: float(np.median([r[m][0] for r in rows])) for m in ORDERS}
        med_over = {m: float(np.median([r[m][1] for r in rows])) for m in ORDERS}
        half_rel = med[1.5] - med[3.0]
        notch = 0.5 * (med[4.5] + med[7.5]) - med[6.0]
        row = {"windows": len(rows),
               "order_line_level_db": med,
               "order_line_db_over_local_floor": med_over,
               "order1p5_minus_order3_db": half_rel,
               "order6_notch_db_below_mean_of_4p5_and_7p5": notch,
               "derived_order1p5_minus_order3_db": -5.34,
               "limits": {"half_rel_db": [lo_lim, hi_lim],
                          "notch_db": notch_lim},
               "outcome": PASS}
        if half_rel < lo_lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: order 1.5 is {half_rel:.2f} dB relative to "
                            f"order 3, below {lo_lim:.1f} dB -- the half order the "
                            f"three-journal geometry requires is not there")
        elif half_rel > hi_lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: order 1.5 is {half_rel:+.2f} dB relative to "
                            f"order 3, above {hi_lim:.1f} dB -- louder than the "
                            f"order it is supposed to sit under")
        if notch < notch_lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: the order-6 notch is {notch:.2f} dB below "
                            f"orders 4.5/7.5, less than {notch_lim:.1f} dB -- the "
                            f"quarter-revolution null is absent")
        per_beat[b.name] = row
    return {"gate": "G-IDENTITY", "kind": QUALITY,
            "measures": ("order-1.5 level relative to order 3, and the depth of "
                         "the order-6 null, both on lines predicted from "
                         "TELEMETRY rpm and therefore both sliding with the "
                         "crank -- no static EQ can produce either"),
            "engine_order": order,
            "derivation": ("A(m) = |cos(pi*m/4)| from two firing sub-trains a "
                           "quarter revolution apart. DERIVED-NOT-MEASURED: no "
                           "F1 spectrum was obtainable to corroborate it."),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(per_beat, failures, inapp)}


# ------------------------------------------------------------- G-BALANCE ----
def comb_spacing_of(seg, sr, f_lo=500.0, f_hi=3000.0, d_lo=40.0, d_hi=600.0,
                    win=16384):
    """THE LINE SPACING A STEM'S OWN SPECTRUM DECLARES, AND WHETHER THE PER-BAND
    ESTIMATOR CAN SEE IT. R2-4079(4).

    THE PROBLEM THIS MEASURES, WHICH IS AN INSTRUMENT LIMIT AND NOT A SIGNAL
    DEFECT. `per_band_sfm` computes flatness INSIDE each 1/3-octave band, which
    is what makes it immune to tilt (that is G-FLAT's whole design, and C7 is
    the control that proves it). The cost of that design is a resolution floor:
    a 1/3-octave band at f is

        w(f) = f * (2^(1/6) - 2^(-1/6)) = 0.2316 * f          Hz wide,

    so a comb of spacing df has TWO lines inside a band only above

        f = df / 0.2316 = 4.318 * df.

    Below that frequency each band holds at most one line, and one line in a
    band is indistinguishable from a bump of noise: the band reads FLAT however
    tonal the source is. There is no free parameter in that crossover -- it is
    the ratio of a 1/3-octave bandwidth to a comb spacing and nothing else.

    IT IS NOT HYPOTHETICAL AND B7 MADE IT WORSE. Adopting the FIA Art. 5.2.10
    three-journal geometry HALVED the firing fundamental from engine order 3 to
    order 1.5, i.e. from rpm/20 to rpm/40, which across this film is 275-360 Hz.
    4.318 x 275 = 1187 Hz and 4.318 x 360 = 1554 Hz, so over the lower 60 % of
    G-BALANCE's own 500-3000 Hz analysis window the engine's comb CANNOT be
    scored as tonal by this estimator. Measured consequence: the engine reads
    0.60-0.71 x white and is counted as one of the near-white stems it is
    supposed to lead.

    This function reports that, per stem, as a MEASUREMENT rather than as an
    argument: the spacing is found in the stem's own log spectrum (a comb prints
    a peak in the spectrum's autocorrelation at its spacing), and the returned
    `unresolved_band_fraction` is the fraction of the analysis window lying
    below 4.318 x that spacing. NOTHING GATES ON IT. It is reported so that a
    near-white verdict the instrument cannot support is visible as such.

    `win` is 16384 and not `SFM_WIN`: at the stems' 96 kHz a 2048-point window
    puts only 53 bins between 500 and 3000 Hz, which cannot resolve a 275 Hz
    comb at all. A measurement OF a resolution limit must not itself be coarser
    than the structure it is looking for.
    """
    S, f = _stft_power(seg, sr, win=win)
    if S is None or S.shape[0] == 0:
        return {"spacing_hz": float("nan"), "peak_r": float("nan"),
                "resolvable_above_hz": float("nan"),
                "unresolved_band_fraction": float("nan")}
    Sm = S.mean(axis=0)
    m = (f >= f_lo) & (f <= f_hi)
    if m.sum() < 64:
        return {"spacing_hz": float("nan"), "peak_r": float("nan"),
                "resolvable_above_hz": float("nan"),
                "unresolved_band_fraction": float("nan")}
    L = np.log(np.maximum(Sm[m], 1e-20))
    # remove the coarse spectral SHAPE, so what is left is line structure only.
    # A Savitzky-Golay over ~200 Hz is wide enough to pass a 275 Hz comb and
    # narrow enough to take the tilt out.
    df = float(f[1] - f[0])
    wlen = int(max(int(200.0 / df) // 2 * 2 + 1, 5))
    if wlen >= L.size:
        wlen = int(max((L.size // 2) * 2 - 1, 5))
    L = L - _sig.savgol_filter(L, wlen, 2)
    L = L - L.mean()
    ac = np.correlate(L, L, mode="full")[L.size - 1:]
    ac = ac / max(ac[0], 1e-30)
    k0, k1 = int(d_lo / df), min(int(d_hi / df), ac.size - 1)
    if k1 <= k0 + 2:
        return {"spacing_hz": float("nan"), "peak_r": float("nan"),
                "resolvable_above_hz": float("nan"),
                "unresolved_band_fraction": float("nan")}
    j = int(np.argmax(ac[k0:k1])) + k0
    spacing = float(j * df)
    cross = 4.318 * spacing
    # the fraction of the analysis window that is NARROWER than the spacing
    frac = float(np.clip((min(cross, f_hi) - f_lo) / (f_hi - f_lo), 0.0, 1.0))
    return {"spacing_hz": spacing, "peak_r": float(ac[j]),
            "resolvable_above_hz": cross, "unresolved_band_fraction": frac}


def g_balance(stems: dict, sr, beats, protagonist=PROTAGONIST):
    """G-BALANCE -- the protagonist margin, measured on STEMS.

    Measured on stems because the MIX is the final flattening step: two
    decorrelated 82-85 %-flat sources sum to 98.6 % of white, so a master can
    read worse than either of its parts and no master-level metric can name
    which part did it. `stems` maps name -> (float array, sr).

    R2-4079(4) -- THE MARGIN CONTAINED ITSELF, AND THAT IS ARITHMETIC, NOT A BAR.
    ---------------------------------------------------------------------------
    The near-white set did not exclude the protagonist, so on any beat where the
    protagonist is BOTH the loudest stem and reads over the near-white line, the
    margin was the protagonist measured against itself and COULD NOT EXCEED
    0 dB whatever the mix did. Measured on R2-4069: beat 2 is 95.97 % engine and
    reported -0.04 dB; beats 4, 5 and 6 are the same shape; at the breach BOTH
    `shards` and `impact` are protagonists and both were inside their own
    denominator. Five of six beats.

    The fix is to the DENOMINATOR ONLY, and it is deliberately not applied to
    the share limb:

      * THE MARGIN asks "does the protagonist lead the near-white BACKGROUND",
        so the background is the near-white stems that are not the protagonist.
        A statistic whose denominator contains its own numerator is not a
        margin.
      * THE SHARE asks "how much of this beat is near-white", and the answer
        must keep counting the protagonist, because a protagonist that is itself
        near-white is the client's actual complaint. Excluding it there would
        let a beat that is 99 % white noise pass both limbs, which is the exact
        defect this gate exists to catch.

    So a hair-dryer protagonist still fails, on the share limb, and the margin
    stops being an identity. NO THRESHOLD MOVED.
    """
    per_beat, failures, inapp = {}, [], []
    if not stems:
        return {"gate": "G-BALANCE", "kind": QUALITY, "per_beat": {},
                "failures": [], "verdict": INAPPLICABLE,
                "inapplicable": ["no stems available -- G-BALANCE cannot be "
                                 "measured on a master alone, and INAPPLICABLE "
                                 "is not PASS"],
                "measures": "stem-level near-white power share and protagonist margin"}
    nw_lim = V("G_BALANCE.near_white_ratio_of_white")
    sh_lim = V("G_BALANCE.max_near_white_power_share")
    mg_lim = V("G_BALANCE.min_protagonist_margin_db")
    for b in beats:
        rows, tot = {}, 0.0
        for name, (sx, ssr) in stems.items():
            i0, i1 = int(b.t0 * ssr), int(b.t1 * ssr)
            seg = to_mono(sx[i0:i1])
            if len(seg) < int(1.0 * ssr):
                continue
            p = float(np.mean(seg ** 2))
            tot += p
            W = white_sfm_reference(min(len(seg), int(8 * ssr)), ssr)
            s = per_band_sfm(seg, ssr) / W if p > 1e-18 else float("nan")
            cs = (comb_spacing_of(seg, ssr) if p > 1e-18
                  else {"spacing_hz": float("nan"), "peak_r": float("nan"),
                        "resolvable_above_hz": float("nan"),
                        "unresolved_band_fraction": float("nan")})
            rows[name] = {"power": p, "sfm_ratio_of_white": s,
                          "comb_spacing_hz": cs["spacing_hz"],
                          "comb_autocorr_r": cs["peak_r"],
                          "sfm_resolvable_above_hz": cs["resolvable_above_hz"],
                          "sfm_unresolved_band_fraction":
                              cs["unresolved_band_fraction"]}
        if tot <= 1e-18 or not rows:
            inapp.append(f"{b.name}: every stem is digital silence")
            continue
        prot = [n for n in protagonist.get(b.name, ()) if n in rows]
        for name, r in rows.items():
            r["power_share"] = r["power"] / tot
            r["is_protagonist"] = bool(name in prot)
            r["near_white"] = bool(np.isfinite(r["sfm_ratio_of_white"])
                                   and r["sfm_ratio_of_white"] >= nw_lim
                                   and r["power_share"] > 1e-4)
        # THE SHARE keeps the protagonist in: a near-white protagonist is the
        # complaint, not an exemption. THE MARGIN takes it out: see the
        # docstring. Two different questions, two different sets, one gate.
        nw_share = sum(r["power_share"] for r in rows.values() if r["near_white"])
        bg = {k: r for k, r in rows.items()
              if r["near_white"] and not r["is_protagonist"]}
        nw_power = sum(r["power"] for r in bg.values())
        pp = sum(rows[n]["power"] for n in prot)
        margin = (10.0 * math.log10(max(pp, 1e-20) / max(nw_power, 1e-20))
                  if nw_power > 1e-18 else float("inf"))
        row = {"near_white_power_share": nw_share, "protagonist": prot,
               "protagonist_margin_db": margin, "limit_share": sh_lim,
               "limit_margin_db": mg_lim, "outcome": PASS,
               "near_white_background_stems": sorted(bg),
               "near_white_stems_including_protagonist":
                   sorted(k for k, r in rows.items() if r["near_white"]),
               "protagonist_counted_near_white":
                   sorted(n for n in prot if rows[n]["near_white"]),
               "margin_note": ("the denominator is the near-white stems that "
                               "are NOT the protagonist; the share limb above "
                               "still counts every near-white stem including "
                               "the protagonist"),
               "instrument_limit": (
                   "per-band SFM cannot score a comb whose spacing exceeds a "
                   "1/3-octave bandwidth: w(f) = 0.2316*f, so a comb of "
                   "spacing df is resolvable only above 4.318*df. Each stem's "
                   "own measured spacing and the resulting unresolved fraction "
                   "of the 500-3000 Hz window are reported per stem. NOTHING "
                   "GATES ON THEM -- they say which near-white verdicts this "
                   "instrument is entitled to."),
               "stems": {k: {kk: vv for kk, vv in v.items() if kk != "power"}
                         for k, v in sorted(rows.items())}}
        if not prot:
            row["outcome"] = INAPPLICABLE
            inapp.append(f"{b.name}: no protagonist stem present")
            per_beat[b.name] = row
            continue
        if nw_share > sh_lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: near-white stems carry {nw_share:.3f} of "
                            f"beat power > {sh_lim:.2f}")
        if margin < mg_lim:
            row["outcome"] = FAIL
            failures.append(f"{b.name}: protagonist {'+'.join(prot)} leads the "
                            f"near-white background "
                            f"({'+'.join(sorted(bg)) or 'none'}) by "
                            f"{margin:+.2f} dB < {mg_lim:+.1f} dB")
        per_beat[b.name] = row
    scored = {k: v for k, v in per_beat.items() if v["outcome"] != INAPPLICABLE}
    return {"gate": "G-BALANCE", "kind": QUALITY,
            "measures": ("per-beat stem power share of stems measuring >=0.6 of "
                         "white per-band flatness, and the protagonist's margin "
                         "over their sum"),
            "per_beat": per_beat, "failures": failures, "inapplicable": inapp,
            "verdict": _verdict(scored, failures, inapp)}


# ----------------------------------------------------------- G-CONSTRUCT ----
NOISE_GENERATORS = ("white", "pink", "brown", "standard_normal", "randn")
# NOT `uniform` and NOT `normal`: both are overwhelmingly used to draw SCALARS
# (a duration, a detune, a per-cylinder gain), and flagging
# `L = int(r.uniform(0.004, 0.020) * sr)` as a noise source that reaches a bus
# is a false positive that trains people to ignore the report. `standard_normal`
# and `randn` are kept because that is how the white click at layers.py's
# impact voice is actually written.
# A noise output is legal only where it is CONSUMED by one of these -- an event
# scheduler or a physically-parameterised filter -- and only where a derivation
# comment says where the parameters came from.
LEGAL_CONSUMERS = ("bp", "lp", "hp", "sos_band", "sosfilt", "sosfiltfilt",
                   "lfilter", "comb_pipe", "fdn_reverb", "tv_onepole_lp",
                   "onepole_lag", "split_bands", "biquad", "resonator",
                   "modal_bank", "plate_modes", "velvet", "schedule",
                   "convolve", "fftconvolve", "image_source")
DERIVATION_MARKERS = ("derivation:", "physics:", "derived from", "from the "
                      "geometry", "hz because", "measured from", "iso ",
                      "sabine", "weyl", "hertzian", "critical frequency")
# Not on the render path: the control corpus is allowed to synthesise noise,
# because synthesising a hair dryer is its JOB. The exclusion is checked, not
# assumed -- `g_construct` fails if any render-path module imports it.
CONSTRUCT_EXCLUDE = ("verify.py", "percept.py")
CONSTRUCT_EXCLUDE_DIRS = ("controls",)


def g_construct(pkg=PKG):
    """G-CONSTRUCT -- THE LAW, machine-checked exactly as `external_assets` is.

    No white()/pink()/brown() output may reach a bus without passing an event
    scheduler or a physically-parameterised filter carrying a derivation
    comment. The single largest generator of the client's "wind blower" was
    `dsp.bp(dsp.white(n, seed+1), 900.0, 6000.0, sr, 2) * 0.6` -- band-limited,
    yes, but with no derivation for 900, 6000 or 0.6, and weighted higher than
    both of the servo's tonal terms combined.
    """
    files = []
    for root, dirs, fs in os.walk(pkg):
        dirs[:] = [d for d in dirs if d not in CONSTRUCT_EXCLUDE_DIRS
                   and not d.startswith("__")]
        files += [os.path.join(root, f) for f in fs if f.endswith(".py")]
    hits, scanned = [], []
    for fp in sorted(files):
        base = os.path.basename(fp)
        if base in CONSTRUCT_EXCLUDE:
            continue
        scanned.append(base)
        src = open(fp, encoding="utf-8", errors="ignore").read()
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            hits.append({"file": base, "line": 0, "what": f"unparseable: {e}"})
            continue
        parent = {}
        for nd in ast.walk(tree):
            for ch in ast.iter_child_nodes(nd):
                parent[id(ch)] = nd
        for nd in ast.walk(tree):
            if not isinstance(nd, ast.Call):
                continue
            name = _dotted_name(nd.func).split(".")[-1]
            if name not in NOISE_GENERATORS:
                continue
            # walk outwards: is this value consumed by a legal consumer?
            cur, consumer, depth = nd, None, 0
            while id(cur) in parent and depth < 8:
                cur = parent[id(cur)]
                depth += 1
                if isinstance(cur, ast.Call):
                    cn = _dotted_name(cur.func).split(".")[-1]
                    if cn in LEGAL_CONSUMERS:
                        consumer = cn
                        break
                if isinstance(cur, (ast.FunctionDef, ast.Module)):
                    break
            ctx = " ".join(lines[max(nd.lineno - 6, 0):nd.lineno + 2]).lower()
            has_note = any(m in ctx for m in DERIVATION_MARKERS)
            if consumer is None:
                hits.append({"file": base, "line": nd.lineno,
                             "what": f"{name}() reaches a bus with no scheduler "
                                     f"and no physically-parameterised filter",
                             "src": lines[nd.lineno - 1].strip()[:110]})
            elif not has_note:
                hits.append({"file": base, "line": nd.lineno,
                             "what": f"{name}() -> {consumer}() with no derivation "
                                     f"comment: where do its parameters come from?",
                             "src": lines[nd.lineno - 1].strip()[:110]})
    # THE DECLARED EXCLUSION MUST STILL BE TRUE -- no render-path module may
    # import the control corpus, or "not on the render path" is a fiction.
    leak = []
    for fp in sorted(files):
        base = os.path.basename(fp)
        if base in CONSTRUCT_EXCLUDE:
            continue
        src = open(fp, encoding="utf-8", errors="ignore").read()
        if "controls" in src and ("import controls" in src or "from .controls" in src):
            leak.append(base)
    if leak:
        hits.append({"file": ",".join(leak), "line": 0,
                     "what": "render-path module imports audio.controls, which "
                             "is excluded from this scan -- the exclusion is no "
                             "longer true"})
    return {"gate": "G-CONSTRUCT", "kind": PROVENANCE,
            "measures": ("AST: every white()/pink()/brown() must be consumed by "
                         "an event scheduler or a physically-parameterised "
                         "filter and must carry a derivation comment"),
            "scanned": scanned, "excluded_files": list(CONSTRUCT_EXCLUDE),
            "excluded_dirs": list(CONSTRUCT_EXCLUDE_DIRS),
            "hits": hits, "n_hits": len(hits),
            "limit": V("G_CONSTRUCT.max_unscheduled_noise_sources"),
            "failures": [f"{h['file']}:{h['line']} {h['what']}" for h in hits],
            "inapplicable": [],
            "verdict": PASS if len(hits) == 0 else FAIL}


def _dotted_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


# ================================================== telemetry ground truth ==
def film_telemetry(spec, sheet_path, srf=4800):
    """rpm / throttle / Doppler ratio as functions of FILM time.

    Every number here comes from `telemetry/telemetry.csv` through this
    project's own gearbox solve, film clock and retarded-time solve -- the same
    machinery the mix was rendered with. It is INDEPENDENT GROUND TRUTH: nothing
    in it is estimated from the audio, which is the entire point of G-ORDER and
    the reason the old `pitch` gate (which re-synthesised the engine and
    measured THAT) is now provenance and not quality.

    The rpm is evaluated at the EMISSION time, not the arrival time: the wave
    arriving at the ears at film t was emitted r/c seconds earlier, up to
    614 ms at the far end of a pass, and ignoring that put an earlier version of
    the doppler gate a whole gear out.
    """
    from .clock import Clock                                  # noqa: PLC0415
    from .scene import Telemetry, CameraPath                  # noqa: PLC0415
    from . import engine as eng_mod                           # noqa: PLC0415
    from . import spatial as sp                               # noqa: PLC0415

    clock = Clock(sheet_path, sr=48000)
    tel = Telemetry(spec=spec)
    w = np.arange(float(tel.t[0]), float(tel.t[-1]), 1.0 / srf)
    v = np.interp(w, tel.t, tel.v_world)
    a = np.interp(w, tel.t, tel.col["accel_long_ms2"])
    rpm_f, _g, _l = eng_mod.gear_and_rpm(v, np.zeros_like(v), np.zeros_like(v),
                                         srf, w, -2.30, -0.05)
    thr_f, _br = eng_mod.throttle_from_spec(v, a, spec)

    t_ctrl = np.arange(0.0, clock.duration_s, 1.0 / sp.CTRL_HZ)
    w_ctrl = clock.world_at_film(t_ctrl)
    car = tel.sample(w_ctrl, "v_world")
    try:
        cam = CameraPath()
        _eL, _eR, centre, _R = cam.ears(t_ctrl)
        hdg = car["heading"]
        fwd = np.stack([np.cos(hdg), np.sin(hdg), np.zeros_like(hdg)], axis=1)
        src = car["pos"] - fwd * 1.60 + np.array([0.0, 0.0, 0.42])
        t_a, _rr, _e, _u = sp.retarded(t_ctrl, src, centre, sp.C_AIR)
        ratio = 1.0 / np.gradient(t_a, t_ctrl)
        have_geometry = True
    except Exception:                                          # noqa: BLE001
        t_a, ratio, have_geometry = t_ctrl, np.ones_like(t_ctrl), False

    def _emit_world(t):
        te = np.interp(np.atleast_1d(t), t_a, t_ctrl)
        return clock.world_at_film(np.clip(te, 0.0, clock.duration_s))

    def rpm_at(t):
        return np.interp(_emit_world(t), w, rpm_f)[0] if np.isscalar(t) else \
            np.interp(_emit_world(t), w, rpm_f)

    def throttle_at(t):
        return np.interp(_emit_world(t), w, thr_f)[0] if np.isscalar(t) else \
            np.interp(_emit_world(t), w, thr_f)

    def doppler_at(t):
        r = np.interp(np.atleast_1d(t), t_a, ratio)
        return float(r[0]) if np.isscalar(t) else r

    return {"rpm_at": rpm_at, "throttle_at": throttle_at, "doppler_at": doppler_at,
            "have_geometry": have_geometry, "clock": clock, "telemetry": tel}


def constant_rpm_telemetry(rpm=11000.0):
    """Ground truth for the constant-rpm positive control: the value it was
    synthesised at, which is known by construction and not measured."""
    return {"rpm_at": lambda t: rpm, "throttle_at": lambda t: 1.0,
            "doppler_at": lambda t: 1.0, "have_geometry": False,
            "engine_beats": ("5_lap",)}


# ============================================================ the suite =====
QUALITY_GATES = ("G-FLAT", "G-HNR", "G-SUSTAIN", "G-EVENT", "G-PRESENCE",
                 "G-ORDER", "G-IDENTITY", "G-RING", "G-NOVEL", "G-MOD",
                 "G-GESTURE", "G-ROOM", "G-BALANCE")
PROVENANCE_GATES = ("G-CONSTRUCT",)


def run_suite(x, sr, sheet, stems=None, telemetry=None, gates=None,
              engine_order=ENGINE_FIRING_ORDER):
    """Run every gate that applies to `x` and return one report.

    `telemetry` is a dict with callables rpm_at / doppler_at / throttle_at, or
    None -- in which case G-ORDER is INAPPLICABLE, which is NOT a pass.
    """
    mono = to_mono(x)
    beats = beats_from_sheet(sheet, len(mono) / sr)
    want = set(gates) if gates else set(QUALITY_GATES) | set(PROVENANCE_GATES)
    out = {}
    if "G-FLAT" in want:
        out["G-FLAT"] = g_flat(mono, sr, beats)
    if "G-HNR" in want:
        out["G-HNR"] = g_hnr(mono, sr, beats)
    if "G-SUSTAIN" in want:
        out["G-SUSTAIN"] = g_sustain(mono, sr, beats)
    if "G-EVENT" in want:
        out["G-EVENT"] = g_event(mono, sr, beats)
    if "G-PRESENCE" in want:
        # THE PROGRAMME'S OWN DELIVERED LOUDNESS IS THE CALIBRATION. It is
        # measured here rather than passed in, so the gate cannot be handed a
        # flattering number, and it is measured on the FULL signal because that
        # is what a listener sets the volume by.
        from audio import dsp as _dsp
        try:
            _li, _, _ = _dsp.loudness_lufs(
                x if np.ndim(x) > 1 else np.stack([mono, mono], axis=1), sr)
        except Exception:
            _li = None
        out["G-PRESENCE"] = g_presence(mono, sr, beats, lufs_i=_li)
    if "G-NOVEL" in want:
        out["G-NOVEL"] = g_novel(mono, sr, beats)
    if "G-MOD" in want:
        out["G-MOD"] = g_mod(mono, sr, beats)
    if "G-GESTURE" in want:
        out["G-GESTURE"] = g_gesture(mono, sr, beats)
    if "G-ROOM" in want:
        out["G-ROOM"] = g_room(mono, sr, beats)
    if "G-RING" in want:
        out["G-RING"] = g_ring(mono, sr, beats)
    if "G-ORDER" in want:
        if telemetry:
            out["G-ORDER"] = g_order(mono, sr, beats, telemetry["rpm_at"],
                                     order=engine_order,
                                     doppler_at=telemetry.get("doppler_at"),
                                     throttle_at=telemetry.get("throttle_at"),
                                     engine_beats=telemetry.get(
                                         "engine_beats",
                                         ("2_launch", "4_transit", "5_lap")))
        else:
            out["G-ORDER"] = {"gate": "G-ORDER", "kind": QUALITY, "per_beat": {},
                              "failures": [], "verdict": INAPPLICABLE,
                              "inapplicable": ["no telemetry supplied -- rpm must "
                                               "be independent ground truth and "
                                               "is never estimated from the audio"],
                              "measures": "comb tracking against telemetry rpm"}
    if "G-IDENTITY" in want:
        if telemetry:
            out["G-IDENTITY"] = g_identity(mono, sr, beats, telemetry["rpm_at"],
                                           order=engine_order,
                                           doppler_at=telemetry.get("doppler_at"),
                                           throttle_at=telemetry.get("throttle_at"),
                                           engine_beats=telemetry.get(
                                               "engine_beats",
                                               ("2_launch", "4_transit", "5_lap")))
        else:
            out["G-IDENTITY"] = {"gate": "G-IDENTITY", "kind": QUALITY,
                                 "per_beat": {}, "failures": [],
                                 "verdict": INAPPLICABLE,
                                 "inapplicable": ["no telemetry supplied -- the "
                                                  "order lines are predicted from "
                                                  "rpm and are never estimated "
                                                  "from the audio"],
                                 "measures": "order-1.5 presence and the order-6 notch"}
    if "G-BALANCE" in want:
        out["G-BALANCE"] = g_balance(stems or {}, sr, beats)
    if "G-CONSTRUCT" in want:
        out["G-CONSTRUCT"] = g_construct()

    quality = {k: v["verdict"] for k, v in out.items() if v["kind"] == QUALITY}
    prov = {k: v["verdict"] for k, v in out.items() if v["kind"] == PROVENANCE}
    inapp = sorted(k for k, v in quality.items() if v == INAPPLICABLE)
    return {
        "gates": out,
        "quality_verdicts": quality,
        "provenance_verdicts": prov,
        "any_fail": any(v == FAIL for v in quality.values()),
        # NO FAIL is not the same as PASS. `quality_pass` requires every quality
        # gate to have actually measured something and passed: an INAPPLICABLE
        # row is the suite saying "I could not judge this", which is exactly
        # what `harmonic` said on pure noise while reporting green.
        "no_fail": not any(v == FAIL for v in quality.values())
        and any(v == PASS for v in quality.values()),
        "quality_pass": bool(quality) and all(v == PASS for v in quality.values()),
        "inapplicable_gates": inapp,
        "rule": ("INAPPLICABLE is not PASS and never counts toward a verdict. "
                 "Provenance gates are excluded from the quality verdict "
                 "because they do not take the rendered master as an input."),
    }


def failing_gates(report):
    return sorted(k for k, v in report["quality_verdicts"].items() if v == FAIL) + \
        sorted(k for k, v in report["provenance_verdicts"].items() if v == FAIL)


if __name__ == "__main__":
    print(json.dumps(audit_thresholds(), indent=1))
