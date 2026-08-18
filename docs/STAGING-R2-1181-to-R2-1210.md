# STAGING R2-1181 .. R2-1210 — verifying a stopped agent's five fixes, and closing the gap it named

The five fixes in R2-1088 were reported by an agent as it was being stopped. None
had been checked by anyone else. This pass re-measures them, sweeps for the class
the `np.roll` defect belongs to, builds the guard the project lacked, and cuts the
listening pass R2-1090 said no agent here could perform.

**Ground rule followed throughout: reproduce the DEFECT number first.** A tool
that cannot reproduce the figure it is replacing has not earned the right to
replace it. Where the defect number could not be reproduced, that is said plainly.

Artefacts available for this, and why the verification is cheap:

    audio/out/ab/master_SHIPPED_aug2.wav   the PRE-FIX master, still on disk
    audio/out/master.wav                   the POST-FIX master
    audio/out/ab/master_A_nolapdown.wav    post-fix, lap-down off
    audio/out/ab/master_B_lapdown.wav      post-fix, lap-down on
    git 19a55b3                            pre-fix audio/ source
    git ac359e4                            the fix commit (audio/ clean in tree)

No render-farm time was used. No GPU was used. Total cost of this pass: CPU only.

---

## R2-1181 — the +31.3 dB frame-1 defect REPRODUCES, exactly, and the fix holds

Measured directly on the two masters, no re-render needed.

| | pre-fix (`master_SHIPPED_aug2.wav`) | post-fix (`master.wav`) |
|---|---|---|
| frame-1 peak | **0.8505** | 0.0510 |
| position of that peak | sample **29** = 0.60 ms | sample 1947 = 40.6 ms |
| RMS of the following 1.0 s | 0.0234 | 0.0222 |
| **peak / programme** | **+31.21 dB** | **+7.21 dB** |
| first sample \|x[0]\| | **0.33204** (−9.6 dBFS) | 0.00464 (−46.7 dBFS) |

R2-1088 claimed `peak 0.8505 against a 0.0233 programme RMS = +31.3 dB`, now
`+7.2 dB`. **Reproduced to four significant figures.** The 0.01 dB difference in
the ratio is the programme-RMS window (0.0234 vs 0.0233), not a disagreement.

Two things the log did not say, both of which matter:

* **The peak is at sample 29, i.e. 0.60 ms in** — inside the first *millisecond*,
  not merely the first frame. Well inside the 11.3 ms the roll wrapped.
* **The first sample itself is 0.332.** The film opened on a step from digital
  silence to −9.6 dBFS. That is a click on its own, independent of the peak that
  follows it, and it is the second statistic the new gate uses.

`dsp.delay` was also checked against the claim that it "is identical to the roll
everywhere except those first n samples":

    n=100000 d=542 : delay[d:] == roll[d:]  True ; delay[:d] all zero  True ;
                     roll[:d] == x[-d:]     True
    (same for d=137, d=681; and delay(x,0) is the identity, delay(x,n>len) is zero)

**The substitution is exact.** VERIFIED.

---

## R2-1182 — WHY it survived every gate: the seam gate cannot reach the film's edges

Not a diligence failure. A structural one, and it is two lines of code.

`audio/verify.py::_boundary_samples` is the whole of it:

```python
for b in sheet["beats"][1:]:        # <-- [1:] : beat 1 is SKIPPED
```

The beat sheet declares six beats starting at 0.000, 33.000, 36.000, 44.000,
49.600 and 113.100 s. `[1:]` drops the first, so the gate visits frames 793, 865,
1057, 1191 and 2715 — the five interior *boundaries*. **Frame 1 is not a boundary
between two beats; it is the outer edge of the first. Frame 2978 is the outer edge
of the last. Neither is in the list, and no other gate looks there either:**

* `level_gate` is global — an 0.8505 sample peak is under 1.0, the true peak still
  made −1.10 dBTP and the integrated loudness still made −14.02 LUFS. One frame in
  2,978 cannot move any of them.
* `level_gate`'s only windowed test asks whether a 1 s window is **too quiet**
  (< −80 dBFS). Nothing asked whether the opening was too **loud** for its
  surroundings.

So the defect sat in a blind spot that was the exact shape of the defect. That is
why it survived, and it is the whole argument for R2-1183.

---

## R2-1183 — the edge gate: `audio/verify.py::edge_gate`, wired into the suite

Two statistics, sharing no arithmetic, both applied at **both** edges.

1. **`crest_db`** — the peak inside the edge frame, referenced to the RMS of the
   adjacent 1.0 s, and judged against **the film's own interior frames**. The same
   number is computed for all 2,976 interior frames; the edge must not exceed
   their 99.9th percentile by more than 3 dB. This is `seam_gate`'s own idiom —
   a local reference, because the film's loudest transient is the breach and a
   global threshold would call the breach a defect.

2. **`onset_step_db`** — |x[0]| for the head and |x[−1]| for the tail against the
   same RMS. Outside the file is digital silence, so those two samples *are* the
   step across the film's outer boundary. Threshold 0 dB + 3 dB headroom.

**The thresholds are not tuned.** Measured separations:

    statistic 1   pre-fix frame 1  +31.62 dB   vs interior p99.9  +19.27 dB
                  post-fix frame 1  +8.53 dB   vs interior p99.9  +18.11 dB
    statistic 2   pre-fix          +23.45 dB   post-fix          -12.28 dB

Any headroom from 0 to +12.3 dB gives the same verdict on statistic 1; anything
from −12.3 to +23.4 dB gives the same verdict on statistic 2. The chosen values
sit in the middle of gaps of **22 dB** and **36 dB**. The gate is not measuring a
fine distinction — it is measuring programme against a splice.

### It fires on the pre-fix audio

```
== audio/out/ab/master_SHIPPED_aug2.wav          <-- the defect, as shipped
   FIRST frame 1: peak 0.8505 at 0.60 ms  crest +31.62 dB [FAIL]
                  boundary sample 0.33204        step  +23.45 dB [FAIL]
   LAST  frame 2978: crest +11.41 [ok]           step   +0.40 [ok]
   PASS=False
== audio/out/master.wav               PASS=True   (+8.53 / −12.28)
== audio/out/ab/master_A_nolapdown.wav PASS=True  (+8.50 / −12.30)
== audio/out/ab/master_B_lapdown.wav   PASS=True  (+8.53 / −12.28)
```

### Positive controls, per this project's rule

Three must fail, two must pass. Built from the **clean** master, so each verdict
is attributable to the injected defect alone.

| control | result |
|---|---|
| the film's loudest 11.3 ms arriving on frame 1 through the mix's own 0.35 coefficient | **FAIL** (correct) |
| the same energy arriving on the **last** 11.3 ms | **FAIL** (correct) — proves both edges |
| a single −9.6 dBFS sample at index 0, the step the shipped master really opened with | **FAIL** (correct) |
| a −40 dBFS sample at index 0 — below sensitivity, stated | PASS (correct) |
| **stated negative:** circularly rolling the FINISHED master | PASS (correct) |

**The stated negative is the most informative line here, and it corrected me.**
My first control was the obvious one — roll the finished master by the same
11.3 ms — and *it did not fail the gate*. That is not a hole. **R2-960's roll was
applied to an intermediate buffer, the showroom's 2.4 s reverb tail, whose last
samples are the decay of a car at 323 km/h. The finished film ends on a car that
has stopped**: its last 11.3 ms peak 0.111, so wrapping them onto the head raises
frame 1 only to +15.0 dB, under the +21.1 dB limit. The defect is therefore not
"a wrap" but **loud material arriving at a quiet edge**, and a faithful control
has to inject what actually wrapped. Both controls were rebuilt to do so. The
first version of this gate would have passed its own controls for the wrong
reason.

### Wired in, and the suite still passes

`edge_gate` runs in `audio.verify.main()` alongside the others:

```
>> gates: {"levels": true, "edges": true, "seam": true,
           "external_assets": true, "pitch": true, "doppler": true}
>> STAGE RESULT: AUDIO_VERIFY_OK
```

`audio/out/verify_report.json` now carries an `edges` block and
`CONTROLS_FAIL_AS_EXPECTED: true`. Existing gates are unchanged: seam still
p80.567 PASS, its own four controls still behave.

`tools/audio_edge_gate.py` is the same function behind a cheap entry point —
seconds, not minutes — for use after every render, every cut and every A/B.

### It crashed on its first robustness test, which is why gates get robustness tests

Fed a two-frame buffer, the first version raised
`IndexError: index -1 is out of bounds for axis 0 with size 0` — `crest[1:-1]` is
empty when there are no interior frames, so the film had nothing to be its own
reference against. **A gate that raises is worse than one that fails**, because a
crash in a suite is easy to read as a tooling problem and route around.

It now returns `APPLICABLE: False` **and `PASS: False`** below 8 frames, with the
reason in the payload. Failing loudly is the only safe direction: a gate that
cannot judge must never report that it did. Tested across mono 1-D input,
non-integer frame counts, exact-minimum lengths, digital silence and a full-scale
square — no exceptions, and the two masters score exactly as before.

---

## R2-1184 — the gate caught something on its first outing: the A/B files click

Run on an extract, statistic 2 reports the **extract's** in-point. That is a
second job worth having.

    audio/out/ab/ending_A_nolapdown.wav   in-point 0.54184   step +9.67 dB
    audio/out/ab/ending_B_lapdown.wav     in-point 0.54559   step +9.68 dB

**These are the two files R2-1090 cut "precisely so a person can decide".** They
were extracted without a fade, so each opens on a hard cut at −5.3 dBFS. A
listener would hear a click on the clip's first frame and could very reasonably
charge it to the film. The copies in `watch/audio/` are faded 5 ms and score
−225 dB.

The older cuts in `audio/out/ab/brake/` do the same thing — in-points 0.25781 and
0.25902, steps **+5.08 dB** and **+5.13 dB**. So this is not a one-off slip in one
pair of files: **every extracted cut this project has made for human review was
made without a fade**, and each one opens on a click. The listening pass has been
handing people an artefact and asking them to judge the film.

A guard that stops the listening pass from manufacturing the very artefact it was
convened to look for is earning its place twice.

---

## R2-1185 — `watch/audio/`: the listening pass, nine clips, about four minutes

R2-1090's gap is a capability gap, and the response is to make the human pass as
cheap and as targeted as possible — not to write another plot.

`tools/audio_watch_clips.py` cuts nine clips with `watch/audio/INDEX.md` as the
index. Every clip carries one line saying what to listen **for**.

| # | clip | frames | what it is for |
|---|---|---|---|
| 01 | `01_opening_BEFORE_defect.wav` | 1–96 | the defect, as shipped |
| 02 | `02_opening_AFTER_fixed.wav` | 1–96 | the same four seconds, fixed |
| 03 | `03_opening_AB_one_press.wav` | ×2 | **the ten-second version — start here** |
| 04 | `04_launch_seam_f792_793.wav` | 756–852 | the f792\|f793 seam at 33.000 s |
| 05 | `05_breach_f865.wav` | 840–984 | the breach — listen for distortion, not a join |
| 06 | `06_ending_seam_f2715.wav` | 2688–2784 | the lift, where the 0.74 dB step was |
| 07 | `07_ending_A_no_lapdown.wav` | 2690–2978 | ending A |
| 08 | `08_ending_B_lapdown.wav` | 2690–2978 | ending B |
| 09 | `09_final_idle_last2s.wav` | 2923–2978 | idle, or a motored engine? |

Three decisions in the cutting, each of which would otherwise have corrupted the
thing being judged:

* **No per-clip normalisation.** One volume setting is right for all nine.
  Normalising per clip would have erased exactly what the 01/02 pair demonstrates.
* **No fade-in on clips 01–03.** They begin at the film's own sample 0. A 5 ms
  fade would have faded out the defect. Clips 04–09 are faded, so the *cut* does
  not make a click that gets mistaken for a defect.
* **WAV, not MP3.** MP3/AAC encoders prepend ~25 ms of silence, which would shift
  the one thing clips 01–03 exist to show. 16 MB total is the price of that.

QC on the cut files, since no agent here can hear them:

    01  first-100 ms peak 0.8505 vs 0.0278 RMS after  =  +29.72 dB   the bang is present
    02  first-100 ms peak 0.0510 vs 0.0282 RMS after  =   +5.15 dB   the bang is absent
    no clipping in any clip (max sample 0.8804, breach)
    clip 09 strongest spectral lines 100–1200 Hz: 215.0, 214.6, 608.3, 309.6 Hz

**The 215.0 Hz line independently corroborates R2-954**: the closing really does
carry an idle fundamental where a motored engine would have none. That is a
by-product of cutting the clip, from a different measurement than the one the
fix's author used.

Self-consistency check: the edge gate **fails clip 01 and passes clip 02**. The
guard and the listening pass agree about which of the two contains the defect.

**What the sweep newly implicated, and therefore what is NOT in this set.** The
brief asked for a clip at anything the sweep newly implicates. The sweep found
**no leak and nothing newly audible**: the seven bounded sites are either
design-intent (the look-ahead limiter), unmeasurable at 24 bits (`dsp.py:380`, at
1e-13 dB), confined to a single analysis frame (`audio_ending_ab.py:95`), or
already inside a clip — `dsp.py:367`'s one-second program-gain settling happens
in the film's first second, which clips 01–03 cover end to end. **Adding clips
for the rest would have spent the client's attention on things measurement has
already bounded.** The one thing the sweep did implicate for ears was the
in-point click on the A/B files (R2-1184), and that is fixed in the cut rather
than described in a note.

---

## R2-1186 — the class sweep: 91 sites, **0 leaks**, 7 bounded, and one dependency nobody had named

`np.roll` used as a delay is a pattern, not an incident. The whole audio tree was
swept for anything that can move energy or dependency from one end of the film to
the other, or read a value from outside the window it is applied to.

**No second instance of R2-960 exists.** The most likely hiding place turned out
not to exist at all: **there is no frequency-domain convolution anywhere in this
project.** The reverb is a time-domain FDN, the reflections are geometric image
sources, the band-split is IIR, propagation is a Catmull-Rom resample. There is
nothing to zero-pad wrongly. `scipy.signal.resample` — the FFT resampler, which
*is* circular — is not used; the three resamplers are all `resample_poly`.

| category | sites | LEAK | BOUNDED | BENIGN | ACCEPTED-GLOBAL |
|---|---:|---:|---:|---:|---:|
| 1. `np.roll` | 2 | 0 | 0 | 2 | 0 |
| 2. FFT / frequency domain | 12 | 0 | 1 | 11 | 0 |
| 3. ring buffers / modulo / wrap modes | 10 | 0 | 0 | 10 | 0 |
| 4. whole-array reductions | 12 | 0 | 0 | 9 | 3 |
| 5. block-loop look-ahead | 8 | 0 | 4 | 3 | 1 |
| 6. `filtfilt` / IIR state | 38 | 0 | 2 | 36 | 0 |
| 7. resamplers, splines, seeds, phase | 9 | 0 | 0 | 9 | 0 |
| **total** | **91** | **0** | **7** | **80** | **4** |

**The two surviving `np.roll` calls** are both in `verify.py::control_seam`
(lines 435, 450) — the positive-control self-test that fabricates a splice and a
crossfade to prove the seam gate fires. Each arm takes `x.copy()`, so the master
array is never mutated; the rolled arrays are consumed only by `seam_gate()`,
which returns percentiles, and are never written to a wav or summed into a mix.
**BENIGN**, checked rather than assumed.

**The seven bounded sites, with their measured reach:**

| site | what it is | reach |
|---|---|---|
| `dsp.py:217` | `sosfiltfilt` in `split_bands` — every propagated bus | 73 ms at 1e-12, **exactly zero beyond**; length-independent |
| `dsp.py:342` | limiter gain `filtfilt` — a look-ahead limiter, non-causal by design | 333 ms at 1e-6; \|dy\| at sample 0 = 0 |
| `dsp.py:369` | program-gain block mean, blk 8192 | 85.3 ms — same shape as the fixed R2-957 sites |
| `dsp.py:367` | program-gain initial condition `e[:sr].mean()` | **1 s**, up to 12 dB unclamped — largest-magnitude look-ahead in the tree |
| **`dsp.py:380`** | program-gain 0.5 Hz `sosfiltfilt` | **the only thing that reaches sample 0** |
| `scene.py:107` | Savitzky-Golay derivative, centred 7-point | ±125 ms of world time |
| `tools/audio_ending_ab.py:95` | circular brick-wall `irfft`, no zero-pad | one 41.67 ms frame; **analysis tool, not the render path** |

### The one dependency that was not named anywhere — now named

`dsp.py:380` runs the gain forwards and then backwards, so `g_db[0]` is a
function of `g_db[-1]`. I re-measured this myself rather than take it on report,
by bursting the last 0.2 s of a film-length buffer:

    |dg| at sample 0     5.3e-13 dB (my bench) / 2.6e-09 dB (the sweep's bench)
    |dg| > 0.1 dB        from ~0.7 s before the burst
    |dg| > 1e-6 dB       from ~6 s before the burst

The two benches disagree by four orders of magnitude, which is what differing
test signals do at this level; **both agree the value is non-zero and both agree
it is unmeasurable.** Under 1e-8 dB at sample 0 is roughly ten orders of
magnitude below a 24-bit LSB and **more than 200 dB below the +31.2 dB defect
that started the sweep**.

It matters because of how it is *stated*. "The film does not depend on its
ending" is **false**. "The film's dependence on its ending is unmeasurable at
24 bits" is **true**. R2-1089's prefix-identity claim should be read against the
second sentence. `dsp.py:380` now carries that paragraph and both figures in a
comment; the change is **comment-only — 30 added lines, 0 added non-comment
lines, verified by diff** — so no master moves.

### What was deliberately NOT changed

`dsp.py:367` and `dsp.py:369` are the same R2-957 shape as the two sites that
were fixed, and both are trivially causalisable (`e[0]`, `e[a0]`). **They are
left alone on purpose.** Both sit inside `program_gain`, which is explicitly a
*mix decision* rather than a source; changing either moves the master, which
would invalidate every clip in `watch/` and require a fresh 22-minute render and
a new listening pass. Closing that class is a deliberate re-mix, not a quiet
edit made while the client is being asked to approve the current one. The
reasoning is recorded at the site.

Two near-misses worth recording, because they are the same class and were
avoided by luck or judgement rather than by a rule: `clock.py:89` and
`scene.py:336` use `PchipInterpolator`, which has **local support** — a
`CubicSpline` there would have made every film sample a function of every
keyframe including the last. And `dsp.py:339,341` use `mode="nearest"` on the
limiter's `maximum_filter1d`/`minimum_filter1d`; `mode="wrap"` there would have
been R2-960 all over again, in the limiter.

### On R2-1089's two named scalars

The mechanism is broader than the entry says. `master.py:280` applies the same
short-term-LUFS trim construct to **all fourteen buses**, not just the crowd —
crowd was simply the only one that moved. This is not an unnamed global
(`master.py:51-67` declares the table as a mix decision), but "two named
scalars" understates it as "fourteen, of which two moved". **No other
content-dependent global scalar is applied to the master.**

---

## R2-1187 — the three `scene.py` fixes: all VERIFIED, three stated numbers wrong

Every defect number was reconstructed and reproduced before the fix was checked.

**A method note that matters:** the pre-fix tree at `19a55b3` is *not* the defect
state — it is the pre-lap-down baseline. R2-943's defective audio edit was never
committed on its own; `ac359e4` contains both the lap-down and its fixes. The
defect state and the author's own rejected first fix were therefore reconstructed
from the description before anything could be measured.

### R2-952 — VERIFIED

| | claimed | measured |
|---|---|---|
| defect: audio vs picture car position | 2.349 mm | **2.349164e-03 m** (argmax f2936) |
| post-fix agreement | 8.0e-14 m | **8.038873e-14 m** (median 0.0) |

**Not 8e-14 for a trivial reason.** `Telemetry.v_extrap` is bit-identical to
`carpath.Car.v[-1]` (same CSV column), `t_brake` matches to 0.0e+00, and the two
`LapDown` tables differ by **0.000e+00** across all 48,001 rows — yet the two
implementations are independent (vectorised vs scalar `bisect`), positions span
460.8 m, and 98 of 329 frames differ at the 1e-14 level. It is genuine float64
round-off between two real, different computations of the same seeded quantity.

**Latent fragility found, not previously recorded:** audio builds its own
`LapDown` and walks `centreline_table(spec, 1.0)` while `carpath.Car` walks step
**2.0**. The 8.039e-14 m residual *is* that table round-off on the pit straight.
On a curve the same two tables disagree by **1.5–1.8 cm**. The lap-down stops
226.5 m past the line and T1 begins at 250 m, so there is **~24 m of margin**
between "8e-14 m" and "1.7 cm". The docstring's "the SAME table" is a separate
instance, not a shared object. It is correct today and it is one ending-length
change away from not being.

### R2-953 — VERIFIED, but "46 ms before the seam" is wrong

Defect, the author's rejected first fix, and the shipped fix all reproduce digit
for digit: `accel_long` 1.507307 → −0.000000, gate 1.000000 → 0.918018, a
**0.7430 dB** step (claimed 0.74). The rejected fix reproduces too, including its
+0.796 m/s² at f2715 and 349 samples of positive `accel_long` while speed falls.
Shipped fix: residual step **0.0000 dB**, **zero** samples with `accel_long > 0`
while speed falls, and past `t_brake` it matches `carpath.Car.decel(t)` to
**7.105e-15 m/s²**.

**The mislabel:** 46.23 ms is `t_brake − t_end` — the flat-out segment, which the
defect-log *body* names correctly. The step sits **28.20 ms** before the
f2714\|f2715 seam, not 46. Commit-message wording only; the fix is right. This
figure had already propagated into the client-facing clip note and has been
corrected there.

### R2-954 — VERIFIED, on the real production grid, with two decorative details wrong

Run at the real `Clock(sheet, sr=96000)` → 11,520,001 samples, not a bench.

| | claimed | measured |
|---|---|---|
| stopped-car throttle, pre-fix | 2.1e-05 | **2.090805e-05** |
| fuel | 3.5e-04 | **3.484674e-04** |
| combustion gate | 12.8 % | **0.1283** (post-fix 0.5515) |
| v_clutch, recomputed from the spec | 8.55 m/s | **8.55240 m/s** |

**The bit-exact no-op claim holds, and holds hard** — this was the claim most
likely to be wrong and it is not. First sample where the floor changes `thr`:
index 10,853,850 = world **t 78.060937 s** (claimed 78.061), at v = 8.552351 m/s,
exactly the derived threshold. Samples touched at or before `t_end`: **0**.
Everywhere the floor loses, `thr` is bitwise identical across all 10.85 M samples.

Two decorative details do **not** reproduce, neither affecting the fix: there is
no 7.80 m/s hairpin (the whole `lock < 1` region on the lap is the *launch*, world
t 0–1.41 s; lap minimum past t=2 s is 16.21 m/s), and the tail is **1.79 s**
(43 frames, f2936–f2978), not 1.75 s.

### The closing idle at the ear — PARTIALLY VERIFIED, and the film is right

| line | claimed | measured |
|---|---|---|
| idle f0 | **216.0 Hz**, +9.06 dB | **214.92 Hz**, +17.95 dB |
| 2f0 / 3f0 / 4f0 | 430 / 645 / 860 Hz | 429.93 / 644.99 / 860.64 Hz |

**The audio is correct and the commit message is the misquote.** 4300 rpm ÷ 60 ×
3 firings/rev = **215.0 Hz**, so 214.92 is the physically right answer and 216.0
was never it. The prominence figure of 9.06 dB could not be reproduced under any
bed definition tried — every method gives **more** (+12.8 dB Welch, +17.9 dB
padded FFT, +20.4 dB broadband). The claim errs conservative, not inflated.

The discrimination control is what makes this an idle rather than a resonance:
during the injector cut at film 116.0–117.75 s the same peak is unlocked
(216.98 Hz) at only +4.36 dB, and the 550 Hz firing tone collapses from +25.7 dB
at film 112.0 to +7.5 dB at 113.5 — consistent with the claimed termination at
113.6.

**This was independently corroborated a third time, by accident:** the spectral QC
run on `watch/audio/09_final_idle_last2s.wav` — cut for the listening pass, from a
different measurement path — returns strongest lines at **215.0, 214.6, 608.3,
309.6 Hz**. The client-facing note has been corrected from 216 Hz to 215 Hz.

---

## R2-1188 — the three `engine.py` whole-film leaks: all three VERIFIED, to the sample

Every figure reproduced exactly against the literal pre-fix commit `19a55b3`.

**First, why they looked unreproducible.** R2-1088 says "sample 42 of **960,000**",
which reads as the first half's length. It is the length of the **whole** bench,
and the bench's sample rate — **48 kHz** — is never stated. At 96 kHz the same
construction gives 78 / 0.0334 / 0.0478 and nothing matches. Once the bench was
rebuilt at 48 kHz with the change at sample 480,000, every number landed.

### R2-956 — VERIFIED (exact)

| | claimed | measured |
|---|---|---|
| rpm (and gear) over the first half | bit-identical | **bit-identical** |
| first differing engine sample | 42 | **42** |
| delta RMS | 0.0287 | **0.028720** |
| signal RMS | 0.0489 | **0.048908** |
| ratio | −4.6 dB | **−4.63 dB** |
| post-fix | bit-identical | **0 non-zero samples of difference** |

Mechanism confirmed independently of the bench: on an unrelated 20 s ramp at
96 kHz the pre-fix first half still differs while rpm/gear stay bit-identical, and
delta RMS scales **linearly with Δ`f_crank.mean()`** — the signature of a
whole-array reduction applied per sample.

### R2-957 — VERIFIED (exact, both sites)

| turbo, blk 2048 | claimed | measured |
|---|---|---|
| first differing sample | 479,235 | **479,235** |
| distance before the change at 480,000 | 765 | **765** |
| magnitude | 0.0087 | **8.7077e-03** |

479,232 = 234 × 2048 is the block start, so the first difference is **3 samples
into the straddling block** — the block-boundary attribution is unambiguous.
Arithmetic: 2048/96000 = **21.333 ms**; 512/96000 = **5.333 ms**; t_end at film
113.055 s minus 21.33 ms = 113.034 s, inside frame 2713's [113.0, 113.0417)
window. **All three check.**

`tv_onepole_lp` measured on the **real tyre bed**, lap-down off vs on: worst
\|d\| before t_end **1.1921e-06** against the claimed 1.2e-06; post-fix
**0.000e+00**. First difference 1 sample into the 512-block straddling the change.

One correction: **0.0087 is a peak, not an RMS.** RMS over the 764-sample leak
window is 1.66e-03 and over the whole first half 6.62e-05. "Magnitude" is fair;
the number is `max|d|`.

### R2-958 — VERIFIED (exact), and order-independence demonstrated rather than asserted

Run at the source on the **real telemetry**, not a bench:

| | claimed | measured |
|---|---|---|
| first differing index | 2,198,824 | **2,198,824** |
| world t | 10.809 s | **10.8088 s** |
| earlier than end of telemetry | 61.8 s | **61.774 s** |
| worst delta (shared rng) | 1.102e-01 | **1.102e-01** |
| post-fix | bit-identical | **True, 0.000e+00** |

speed/rpm/gear were bit-identical before t_end in **both** arms, so the leak is
purely the shared stream. The order-independence claim was tested, not taken:
post-fix draws are identical when events are **appended, prepended, or iterated
in reverse**. The pre-fix shared `rng` survives *append only* — and fails on
prepend and on reorder. **The claim holds exactly as stated**, which is worth
saying because it was the easiest of the five to assert without checking.

I confirmed the same structure independently before the track reported: post-fix
`default_rng([seed, kind, i])` gives 600 distinct non-colliding streams invariant
to order and count, while a pre-fix shared walk shifts the first overrun pop by
1.31 when seven downshifts are inserted ahead of it.

---

## R2-1189 — two things the sweep found that the log gets WRONG, both still open

Neither affects the shipped master. Both affect what this project is entitled to
*claim*, which is the subject of this whole pass.

### The jitter normalisation is content-safe but LENGTH-fragile

`engine.py:322`, `jit = jit / max(|jit|.max(), 1e-9)` — a whole-array reduction
that survived R2-956. It does **not** leak content: `jit` derives from
`dsp.white(n, seed+1)` through a causal `sosfilt`, with no `v`, no `rpm`, no
`f_crank`, and `white(n,seed)` is a verified strict prefix of `white(2n,seed)`.
**R2-956's fix genuinely closes the content path.**

But the constant is length-dependent — measured to move **+19.5 %** between
n = 800,000 and n = 1,000,000. It is safe *for this film* only by accident:
`argmax|jit|` sits at sample 1,962,186 (world t 40.9 s at 48 kHz) and 1,962,552
(t 20.4 s at 96 kHz), both far inside the film, and the world grid's `n` comes
from the beat sheet and `sr`, not the telemetry — so R2-943 could not have moved
it. **That is why the prefix-identity tool passes, not evidence the pattern is
safe.** Sensitivity, so the risk is a number rather than a worry: forcing a **1 %**
change in that constant moves the engine from **sample 106** at **−19.7 dB**
whole-signal delta — the same class and order as R2-956 itself. `dsp.brown()`
and `dsp.pink()` carry the identical pattern with the identical property.

### The turbo whine branch: the log's dismissal is right at 96 kHz and wrong at 48 kHz

`engine.py:411`, `if float(np.nanmax(f)) < sr * 0.45`. The log says this "is
decided by the SAMPLE RATE and not by the film at either rate this project uses".
Recomputed from the code's own constants:

    sr = 96000, 0.45*sr = 43200   order 6/12/18 ceilings 12500 / 25068 / 37429 Hz
                                  -> all three ALWAYS take the `if`.  Log correct.
    sr = 48000, 0.45*sr = 21600   film's peak shaft 2023.3 rps gives
                                  order 12 = 24345.5 Hz, order 18 = 36350.7 Hz
                                  -> BOTH take the `else`, and WHICH branch they
                                     take is a function of the film's peak shaft.

The two branches produce materially different whine — the `else` clamps to
0.44·sr and applies a mask — so a flip changes the whine layer everywhere.

**The master is rendered at 96 kHz and is unaffected.** But
`tools/audio_prefix_identity.py` defaults to **`--sr 48000`**, so **the tool used
to prove the film does not depend on its ending runs at the one rate where an
extra film-dependent branch exists that the render does not have.** It does not
leak for the lap-down A/B — the peak shaft is on the flying lap, which the
lap-down does not touch, and the post-fix run is bit-identical — but the log's
sentence should be narrowed to 96 kHz, and the tool arguably should run at the
rate it is certifying.

Both are recorded here rather than changed: altering either moves the master or
the certification, and neither should happen quietly while the client is being
asked to approve the current mix.

---

## Verdicts — all five reported fixes

| defect | claim | verdict |
|---|---|---|
| **R2-960** `np.roll` on frame 1 | 0.8505 / 0.0233 / +31.3 dB → +7.2 dB | **VERIFIED exactly** (+31.21 → +7.21; `dsp.delay` proven identical to the roll for all i ≥ n) |
| **R2-956** `mean()` moved sample 42 | 42 / 0.0287 / 0.0489 | **VERIFIED exactly** |
| **R2-957** 21 ms lookahead into f2713 | 765 / 0.0087; 1.2e-06 | **VERIFIED exactly** (both sites; "0.0087" is a peak, not an RMS) |
| **R2-958** RNG re-seed 61.8 s early | t 10.809 / 2,198,824 | **VERIFIED exactly**, incl. order-independence |
| **R2-954** closing throttle 2.1e-05 | motored engine for the last 1.75 s | **VERIFIED** (2.090805e-05; bit-exact no-op holds; tail is **1.79 s**, not 1.75) |
| R2-952 audio/picture seed | 2.349 mm → 8.0e-14 m | **VERIFIED** (both halves) |
| R2-953 0.74 dB step | "46 ms before the seam" | **VERIFIED**, but it is **28.20 ms**; 46.23 ms is `t_brake − t_end` |
| R2-1089 accepted 5.8e-03 master delta | correct to accept | **AGREED** — and the trim construct applies to **14 buses**, not 2 |

**No reported fix failed to verify.** Five stated numbers are wrong — the
"46 ms", the "1.75 s", the "216.0 Hz", the "9.06 dB", and the 7.80 m/s hairpin —
and in every case **the code is right and the prose is wrong**, which is the
benign direction but is exactly how a project ends up unable to reproduce its own
figures. The bench rate for "sample 42" is unstated, which is what made three
correct fixes look unreproducible until the rate was inferred.
