# STAGING R2-4081 to R2-4140

Audio rebuild 3, the instrument pass. The client has rejected **three** masters
and named a **different** defect each time:

| file | what the client said | the defect |
|---|---|---|
| `audio/out/master.wav` | "a wind blower", "hair blower" | TOO NOISY |
| `audio/out/ab/master_R2-2001_REJECTED_tubes.wav` | "banging on tubes", "The Tubes over and over" | WRONG STRUCTURE |
| `watch/rejected_audio_R2-4079/PART2_AUDIO_MASTER_R2-4079.wav` | "ngl audio is worse, sounds like a shitty musical" | TOO MUCH STRUCTURE |

R2-4082 to R2-4086 build the instrument that would have caught the third one,
and then go back and ask what the two instruments that produced it were
actually measuring. The answer was not what anyone had written down.

---

## R2-4081 — WHAT THE BENCHES IN THIS PASS HAD ALREADY ESTABLISHED

Recorded here from their own outputs in `audio/out/r2_4081/`, because R2-4082
onwards builds directly on two of them.

* **`hnr_control.json`** asked whether G-HNR's +8 dB beat-1 bar — flagged at
  R2-4062 as *never validated against a signal that should pass* — is
  reachable. It found `C8b_physical_showroom_beat` reads **+32.21 dB**, i.e.
  clears the bar by 24 dB, and concluded the bar stands. **R2-4084 overturns
  that conclusion, using that bench's own sweep.** The sweep is the reason: at
  `dry_gain` 0.13, C8b is **98.3 % sustained tone by power**. The signal that
  proved the bar reachable is a drone.
* **`mobility_null.json`** measured, correctly and first, that G-ROOM(b)'s
  recurrence statistic has a **chance level of 0.40–0.47** at the burst counts
  in play, against a 0.35 bar, and that limb (a) already gates an excess over
  chance while limb (b) gates a raw fraction. R2-4085 acts on that measurement
  in a different way and says so.

---

## R2-4082 — G-SUSTAIN: THE GATE THAT WOULD HAVE CAUGHT R2-4079

### The thing that was unmeasurable

R2-4079's suite verdict on the file the client called a musical was that beat 1
was **NOT TONAL ENOUGH**: G-HNR read **+0.49 dB** against its +8 dB bar and
G-FLAT read 0.773× white against 0.45×. Both statements are true at once,
because a median over 80 ms windows is an opinion about the whole mix and what
an audience hears is **the loudest thing that holds a note inside it**. Nothing
in the suite computed that quantity.

`audio/percept.py` now tracks sinusoidal partials frame to frame and defines a
**note** operationally: a partial that stays inside **25 cents** for **0.6 s**
while standing **8 dB** over the median of its own ±1/3-octave neighbourhood.
Every number in that definition is derived, not chosen:

* **0.6 s** is above the T60 of every struck resonator in the film —
  `2.2/(η·π·f)` at η 0.02–0.15 is 30–350 ms at 200 Hz — and below any note a
  listener calls held.
* **25 cents** is under the smallest pitch movement a machine makes by 5.6×: a
  servo under a trapezoidal move sweeps its mesh line over an octave, and the
  film's own declared Doppler station moves 141 cents.
* **8 dB over the LOCAL floor** is what lets the instrument work on a **mix**.
  A pad inside a broadband bed is 20 dB over its neighbourhood while the beat's
  median periodicity reads 0 dB. That is exactly the R2-4079 case.

### Three limbs, and what each one is for

| limb | C9 (positive) | C8b (negative) | what it says |
|---|---:|---:|---|
| `note_cover` ≤ 0.20 | **0.000** | 0.597 | something is holding a pitch |
| `chord_cover` ≤ 0.05 | **0.000** | 0.576 | THREE pitches at once — a chord |
| `held_power_share` ≤ 0.15 | **0.0000** | 0.5193 | and they carry the beat |

`chord_cover` is the limb that separates **musical** from merely **tonal**, and
it is the cleanest number in the corpus: the physics-true assembly cell reads
0.000 across every seed tried, because *three independent constant-rate sources
is not a thing an assembly cell has*.

**It runs on percussive beats only** — `PERCUSSIVE_BEATS`, derived from
`PROTAGONIST` rather than listed by hand. A power unit holds a pitch by physics
and gating it for that would be the same error being corrected, one gate over.

### Watched firing

* `M-SUST` (three held notes over C9) — **FIRED**, all three limbs, 0.656 /
  0.615 / 0.563. The mutation deliberately uses **three arbitrary frequencies
  in a ratio that is not consonant** (1 : 1.331 : 1.587), because the property
  gated is HOLDING, not harmony. A gate that only fired on consonant intervals
  would be a taste instrument.
* `C8b_tonal_showroom_drone` — **FAIL**, as now required.
* `C6_jittered_identical_gestures` — FAIL, 0.408 / 0.315, and that is a **true
  reading, not a false one**: C6's identical gesture rings for 2.2 s at one
  pitch, which is a note. C6's own contract (must trip G-GESTURE, must pass
  G-MOD) is unaffected.
* **`M3` — FAIL, 0.375 / 0.286, and it is the ONLY master that fails it.**

---

## R2-4083 — C9: THE POSITIVE CONTROL THIS CORPUS NEVER HAD

`audio/controls/synth.assembly_cell`. Percussive, inharmonic, transient-dense,
**unpitched**, with structured non-white noise. Everything from first
principles, nothing recorded, nothing imported from the render path:

* **thin-ring flexural modes** `f_n = n(n²−1)/√(n²+1) · (1/2π)√(EI/ρAa⁴)` for
  every tube — ratios 1 : 2.83 : 5.42 : 8.73, which are not small integers and
  never will be. *That is why a struck tube is not a note*, and it is why a
  dense metallic beat can have no pitch at all.
* **plate modes** from (a, b, h, E, ν, ρ) per part, four materials;
* **Hertzian contact** `τ = 2.94(m²/(RE*²v))^0.2` as the excitation;
* **joint damping** η 0.02–0.15, so nothing rings into the next event;
* **jet-noise exhausts** — Lighthill scaling, peak at Strouhal 0.2, f² up and
  f⁻² down, plus a plenum Helmholtz resonance. Structured, non-white, and its
  peak MOVES with the orifice, so two exhausts never print the same spectrum;
* **servo moves under a trapezoidal velocity profile** — the shaft rate is zero
  at both ends and constant for at most a third of the move, so every line in
  it is a multiple of a rate that is changing. *A machine is periodic in rhythm
  and never in pitch*, made literal in one function;
* **nut runners** at 19–44 Hz — rhythm an order of magnitude below any pitch
  the suite tracks;
* ~**580 contacts over 33 s**, the film's own order of magnitude (616 first
  contacts plus 161 restitution bounces).

**On the film's own arrival grid, and why not exactly:** the picture's uniform
1.0417 s ladder is a G-MOD failure that no audio change can fix (R2-4080), so a
control that copied it would inherit a failure that belongs to the picture.
What C9 copies is the **density**, which is what it is a control for. The wave
schedule is a golden-ratio low-discrepancy sequence: no period at any scale.

Measured over five seeds: note cover **0.000**, chord cover **0.000**, held
power share **0.0000**, every time. G-EVENT 21.4–37.4 dB. It passes the corpus.

---

## R2-4084 — THE RE-DERIVATION: BOTH BEAT-1 BARS ARE RETIRED, AND NEITHER WAS MOVED TO MAKE A MASTER PASS

### The measurement that settles it

A 33 s passage of **660 Hertzian impulses driving plate modes** — no noise
generator anywhere in its signal path, every part its own geometry — measured
on the shipped estimators, against every negative in the corpus:

| beat-1 passage | per-band SFM (×white) | Boersma HNR |
|---|---:|---:|
| **660 struck plates, no noise source at all** | **1.263** | **−3.78 dB** |
| **C9 assembly cell (positive control)** | **1.032** | **−5.36 dB** |
| C1 octave-matched noise (the literal hair dryer) | 0.700 | — |
| C3 blower into tubes | 0.639 | −0.63 dB |
| C2 tiled loop | 0.669 | +8.35 dB |
| M1 delivered master, "a hair blower" | 0.922 | +0.26 dB |
| M2 tubes master | 0.921 | +0.04 dB |
| M3, "a shitty musical" | 0.773 | +0.49 dB |
| **C8b servo drone bed alone** | **0.338** | **+30.54 dB** |
| white noise | 0.994 | −11.23 dB |
| pure harmonic comb | 0.126 | — |

**Every negative outscores every positive, on both instruments at once.** This
is not a threshold that needs moving. It is a statistic that is not monotone in
the property being gated, and no value of either bar passes what should pass
and fails what should fail.

**Why per-band SFM inverts:** an impulse's magnitude spectrum is smooth and
deterministic, so its bin-to-bin variance is *lower* than white noise's
chi-square fluctuation and its spectral flatness comes out *higher*. A shower of
struck plates is literally flatter than white noise on this estimator.
`calibrate_flat` never caught it because every signal it was ever shown was a
sustained comb with noise added: it verifies monotonicity **along that one
axis**, and says nothing about impulsive material.

**Why Boersma HNR inverts:** it measures whether the signal holds a note. A
struck resonator does not. The question is close to the opposite of the right
question for an assembly cell — which is what the brief for this pass suspected
and what the table above establishes.

### What happened instead

* `G_HNR.beat1_median_min_db` (+8.0 dB) — **RETIRED**.
* `G_FLAT.beat1_median_max_ratio_of_white` (0.45×W) — **RETIRED**.
* G-FLAT and G-HNR are now **engine-beat instruments**, scoped by
  `ENGINE_BEATS`, which is derived from `PROTAGONIST`. At an engine beat,
  "does it hold the note it should" is the right question and both gates keep
  every bar they had. `G_FLAT.slice_max_ratio_of_white` stays at 0.55 and its
  positive anchor changes from C8b's 0.496 to **C8's 0.127**, because a
  tonality bar anchored on a drone is not anchored.
* Both retirements are recorded in `percept.RETIRED` with the measurement, so
  re-adding either has to argue with a number rather than with a gap.

### The process failure this closes

The +8 dB bar's only validation was C8b, which is 98.3 % sustained tone by
power. **The instrument that proved the bar reachable was itself the thing the
client rejected three times**, and the gradient it defined pointed at R2-4079.
C8b keeps its builder, unchanged, and changes role: it is now the **anti-cheat
control** — the cheapest signal that clears the old beat-1 bars — and it is
required to FAIL. What changed is the claim made about it, and it changed on
numbers.

---

## R2-4085 — G-EVENT, AND THE TWO ESTIMATOR CORRECTIONS THE POSITIVE CONTROL FORCED

### G-EVENT

Retiring the beat-1 spectral bars leaves the hair dryer ungated at beat 1, and
after R2-4084 it is clear no stationary spectral statistic can do that job. The
difference between a hair dryer and an assembly cell is **not in the spectrum.
It is in the envelope.**

`local_dynamic_range` = p95−p5 of the 20 ms level inside 2 s windows, **median**
over windows.

| signal | dB | |
|---|---:|---|
| white noise | 0.65 | |
| C8b drone | 0.64 | as stationary as white noise |
| **C9's own octave-band spectrum, re-synthesised stationary** | **2.06** | the `M-EVENT` mutation |
| C1 octave-matched noise | 4.70 | |
| C3 blower into tubes | 8.79 | loudest negative |
| **C9 assembly cell** | **21.36** | positive, 21.4–26.4 over five seeds |

Bar **13.7 dB**: the maximum-margin placement in log units between the positive
and the loudest negative — equal ratio to each, 1.56× either way. **No master
was consulted.**

`M-EVENT` is the sharpest mutation in the suite: it replaces the control with
**its own octave-band spectrum as stationary noise**, so every spectral
statistic survives and every event is gone. It reads 2.06 dB. FIRED.

**The median, not the quartile, and that is a measurement:** beat 1's arrivals
are clustered, so the quietest quarter of its 2 s windows lands in the gaps,
where stationarity is correct. On C9 the p25 reads 8.72 dB against
blower-into-tubes' 8.07 — no separation at all — while the median reads 21.36
against 8.79. The quartile measures the silence.

### G-ROOM(b): the recurrence statistic is a birthday problem

`mobility_null.json` measured the chance level first. This is the same
measurement taken further — on **independent log-uniform peaks**, which share
nothing by construction:

| bursts | 8 | 12 | 20 | 40 | 60 |
|---|---:|---:|---:|---:|---:|
| recurrence | 0.031 | 0.162 | 0.277 | **0.638** | **0.835** |

against a 0.35 bar. **At forty bursts pure independence fails the gate.** C9 was
reading 0.666 and the film's own beat 1 reads 0.600 for the same reason.

Two corrections, and **the bar was not touched**:

1. `G_ROOM.max_bursts` = 16, where chance is ~0.22. The delivered master still
   reads 0.570 and the fixed-resonator mutation 0.375.
2. `recurrence_null()` — a line only counts as recurring if it appears in more
   bursts than the most-recurring line of an independent draw does 19 times out
   of 20. That is a family-wise error rate of 5 % over all ~341 resolvable
   1 % bins, not a per-bin test.

All three G-ROOM mutations still fire. C9 passes limbs (a) and (b).

### G-ROOM(c): DECLARED OPEN, MEASURED, AND NOT MOVED

C9 fails limb (c), and the limb's own null is why:

| material | cepstral peak / median |
|---|---:|
| 13 struck plates, own geometry, **no room, no delay of any kind** | **10.44×** |
| 13 filtered noise bursts, no modes at all | **25.28×** |
| C9 assembly cell | 5.91× |
| the same material summed with a 1.333 ms delayed copy | 78–206× |
| the bar | **1.5×** |

The statistic **does** separate an echo from no echo, by an order of magnitude.
It is the bar that is an order of magnitude below the no-echo case. The ripple
sub-limb is the same shape: 8.0 dB against a diffuse field's Rayleigh p95−p5 of
**17.7 dB by construction**, which R2-4067 had already recorded in this repo.

**R2-4085 measured both and moved neither.** Re-deriving G-ROOM was not this
pass's remit, and moving three bars on evidence gathered while doing something
else is how bars get loose. Instead `audio/controls/synth.OPEN` declares the
gate open **for C9 only**, with the measurement in the entry, and
`tools/percept_matrix.py` prints it on every run and writes it into the report.
The rule attached to that mechanism, so it cannot become a dumping ground: **an
entry is admissible only with a measured null for the limb it names**, never
because a control "nearly" passes.

---

## R2-4086 — THE ACCEPTANCE TEST: THREE MASTERS, THREE REASONS

`tools/r2_4081_acceptance.py`, output in
`audio/out/r2_4081/acceptance_R2-4081.json`.

At **gate** level all three masters fail nearly everything, which is the right
answer to "is this shippable" and a useless answer to "why was it rejected".
The reason lives one level down. **Beat 1, computed from the per-beat rows:**

| master | note cover | chord cover | G-SUSTAIN | G-EVENT | G-NOVEL r | G-MOD |
|---|---:|---:|:--|---:|---:|---:|
| M1 hair blower | 0.158 | 0.000 | **pass** | 13.25 dB FAIL | 0.343 **FAIL** | 16.71 dB FAIL |
| M2 tubes | 0.142 | 0.000 | **pass** | 13.46 dB FAIL | 0.307 **FAIL** | 18.98 dB FAIL |
| M3 musical | **0.375** | **0.286** | **FAIL** | 11.18 dB FAIL | −0.240 **pass** | 11.96 dB FAIL |

**The one master the client called a musical is the only one that fails
G-SUSTAIN, and the only one that passes the repetition gate.** The signatures
are opposite, which is what "each for its own reason" has to mean.

Unique (gate, beat) rows, computed from outcomes and not from parsed strings:

* **M1** — `G-BALANCE@1_assembly` (near-white stems carry the beat)
* **M2** — `G-RING@5_lap` (a 1/6-octave band ringing 3.6× the broadband decay:
  an under-damped isolated mode, which is what "tubes" is)
* **M3** — `G-SUSTAIN@1_assembly`, `G-FLAT@2_launch`, `G-BALANCE@2_launch`

Control matrix: **PERCEPT_MATRIX_OK**. 10 controls all correct, **14 mutations
all FIRED, no blind gates**, 38 thresholds, 0 provenance violations, no
`source=artefact` anywhere.

---

## R2-4087 — WHAT DID NOT DISCRIMINATE, AND IS THEREFORE NOT IN THE SUITE

Four of the five quantities the brief proposed were built and measured. **Three
were dropped on the measurement**, and that is the more useful half of this
pass.

### DROPPED — pitch-class concentration on a 12-TET lattice

The obvious "is it music" test: fold every stable pitch onto a semitone grid and
measure circular concentration R (Rayleigh, so the p-value is free). Measured
on beat 1:

| | M3 musical | M1 | M2 | C8b drone | C8 power unit | C2 loop |
|---|---:|---:|---:|---:|---:|---:|
| R | **0.19** | 0.22 | 0.32 | 0.38 | 0.49 | 0.60 |

**The master the client called a musical is the LEAST scale-concentrated signal
in the table**, and a constant-rpm power unit is one of the most. The reason is
plain in hindsight: harmonics of one fundamental land near 12-TET by
arithmetic — 3:2 is 2 cents from a tempered fifth — so this measures *harmonic
comb*, not *scale*. It is anti-correlated with what it was meant to detect.
Dropped.

### DROPPED — consonant intervals between simultaneous sources

Not implementable without source separation, and the reason it is not merely
hard is the one above: partials of a single machine are already in small-integer
ratios, so an interval histogram over simultaneous partials cannot tell one
harmonic source from two consonant ones without first grouping partials into
sources — which is the separation problem. What survives of the idea is
`chord_cover`, which counts **simultaneity** and ignores **interval**, and the
`M-SUST` mutation is deliberately built on a dissonant triad so the gate cannot
be passed by detuning.

### DROPPED — sustained stable f0 as a standalone quantity

`note_cover` alone does **not** separate music from machinery: C8b reads 0.597
and a constant-rpm power unit reads 0.997, both higher than M3's 0.375. Sustain
only becomes discriminating once it is (a) scoped to non-engine beats and (b)
paired with `chord_cover`. Shipped as one limb of three, never alone.

### DROPPED — transient density and spectral flux crest

Onsets/s: M3 3.55, M1 1.82, M2 1.82, C9 5.88, C8b 7.82. Flux crest: M1 2.07,
M3 4.47, C9 3.18–4.1, C8b 11.56. **C8b — a drone — outscores the physics-true
assembly cell on both.** The counts are dominated by how the events are
clustered, not by how many there are. The property is real and the estimator was
wrong; `local_dynamic_range` measures the same intent and separates C9 from
every negative by 2.4×.

### KEPT — harmonicity of ringing, but as construction rather than as a gate

Thin-ring theory gives inharmonic partials by algebra, so "is the ringing
inharmonic" is enforced in C9 by construction and by G-CONSTRUCT's law on the
render path (every source an excitation driving a resonator from a geometry).
A separate gate measuring partial-ratio inharmonicity would need the same
source grouping that sank the interval limb.

---

## OPEN, IN ORDER

1. **G-ROOM needs its own pass.** Limb (c)'s two bars sit below their own
   floors — 1.5× against a 10.4× no-delay null, 8 dB against a 17.7 dB Rayleigh
   floor — and limb (b) gates a raw fraction where limb (a) gates an excess over
   chance. `mobility_null.json` and R2-4085 have the anchors; C9 and a
   delayed-copy pair are the two-sided control.
2. **G-EVENT's margin against M1 and M2 is 0.2–0.5 dB.** The bar was placed
   between two synthesised anchors and no master was consulted, so the near-miss
   is an outcome and not a derivation — but **a 0.45 dB margin is not a margin
   worth defending**, and the honest reading is that G-EVENT catches C1 (4.70),
   C8b (0.64) and `M-EVENT` (2.06) decisively and catches M1 and M2 by luck.
   What actually fails M1 for noisiness is G-FLAT at its engine beats, where the
   instrument is valid.
3. **`held_power_share` does not fire on M3** (0.0116), because its pad sits
   inside a broadband bed. It fires on the drone. Stated in the threshold note
   rather than left for someone to discover.
4. **G-MOD at beat 1 still needs the picture** (R2-4080, unchanged). Every
   master reads 11.96–18.98 dB against a 6 dB bar and no audio change moves it.
5. **G-SUSTAIN has not been tried against a build that is aiming at it.** Every
   gate in this suite has been gamed by the next build at least once; the
   anti-cheat that exists is `M-SUST`, and the one that does not yet exist is a
   passage that holds notes for 0.59 s at a time.
