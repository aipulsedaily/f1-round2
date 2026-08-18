# STAGING R2-1981 to R2-2040

Staged 2026-08-08, audio only. Scope: `audio/`, `watch/audio/`, `tools/`.
Nothing in `world/`, `anim/`, `sim/` or `docs/beat_sheet.json` was touched.

**Trigger.** The client's second note on the audio, harsher than the first:

> "the audio is fucking complete shit sounds like a wind machine with someone
> banging on tubes etc."

The first note was *"sounds like a hair blower."* Between the two, the exhaust was
rebuilt as a digital waveguide (R2-1401) and the harmonic-to-noise ratio above
2.6 kHz went 3.2 → 23.7 dB on the engine bus. **This is a different complaint,
and the difference is the finding: it is no longer "noise", it is "noise plus
resonant thumping."** The rebuild that fixed the hair dryer is what introduced
the tubes.

---

## R2-1981 — The clips the client had were 2.5 hours stale, and they omitted the only beat the previous fix improved

`watch/audio/*.wav` were cut 14:40. `audio/out/master.wav` was written 17:10.
They are not the same mix and the difference is not subtle — comparing each clip
against the same window of the delivered master, over the clip interior with the
5 ms fades excluded:

| clip | window | clip RMS | master RMS | **difference RMS** |
|---|---|---:|---:|---:|
| `02_opening_AFTER_fixed` | 0.0–4.0 s | −31.04 | −29.03 | **−42.68** |
| `04_launch_seam` | 31.5–35.5 s | −12.65 | −13.49 | **−13.10** |
| `05_breach` | 35.0–41.0 s | −10.98 | −11.07 | **−16.28** |
| `06_ending_seam` | 112.0–116.0 s | −17.04 | −16.66 | **−24.89** |
| `09_final_idle` | 121.8–124.1 s | −27.77 | −24.18 | **−31.35** |

A difference only 13 dB below the signal is a different mix, not a rounding
error. **The clips did not represent the delivered master.**

**Worse than stale — unrepresentative.** `tools/audio_watch_clips.py` had been
extended to cut six more clips (10–15: the lap and launch A/B pairs at the
R2-1401 worst moment) and was never re-run, so those six never existed on disk.
The set the client actually had breaks down like this:

| beat covered | seconds in the clip set | share |
|---|---:|---:|
| showroom opening (01–03) | 17.0 | 30 % |
| launch (04) | 4.0 | 7 % |
| **breach (05)** | 6.0 | 10 % |
| **ending (06–09)** | 30.3 | 53 % |
| **flying lap** | **0.0** | **0 %** |

**63 % of the client's listening time was the breach and the ending — the two
beats with the worst harmonic-to-noise ratio in the film, and the two the
harmonic gate does not score.** 0 % was the flying lap, which is the beat the
wind fix was aimed at and the only beat where it demonstrably worked (R2-1982).

Re-cut from the current master before any code was changed, so the tree is never
again in a state where the clips misrepresent the master. 15 clips now on disk.

**A client judging a stale artefact is our failure, not theirs.** This project
has now lost time to that class of mistake twice.

**Defect found while re-cutting, not fixed:** `tools/audio_watch_clips.py` emits
two files numbered `12_` (`12_lap_AB_one_press.wav` and
`12_launch_BEFORE_hairblower.wav`). Cosmetic; flagged rather than changed
because renaming clips mid-review would break any reference the client has.

---

## R2-1982 — The wind remedy landed exactly as predicted, and the prediction was not enough

R2-1402 measured the wind bus at −22.48 dBFS over the flying lap, **4.7 dB above
the engine**, with wind + tyres at 87 % of the broadband floor. The remedy — wind
−18 → −23 LUFS-S plus a −12 dB shelf above 2 kHz — was **predicted to take the
lap from 0.71 → 6.70 dB**. That prediction was never checked against a rendered
master.

**Checked now.** `harmonic_gate` on both rejected masters, same window, like for
like:

| | rejected #1 (hair blower) | rejected #2 (what the client just heard) |
|---|---:|---:|
| lap HNR above 2.6 kHz | **−0.72 dB** | **+6.686 dB** |
| gate verdict | FAIL | PASS |

**Predicted 0.71 → 6.70. Measured −0.72 → +6.686.** The endpoint matches to
0.014 dB and the starting value to 0.006 dB in magnitude — the prediction quoted
it unsigned, and the true starting point was 0.72 dB *below* zero, so the fix is
worth **7.4 dB** on the lap rather than the 5.99 dB the prediction implied. It
landed, and it is in the delivered master.

**And the client still called it a wind machine.** The reason is in the
distribution the beat median throws away:

| lap HNR above 2.6 kHz | p5 | p25 | **p50** | p75 | p95 |
|---|---:|---:|---:|---:|---:|
| rejected #2 | **−1.89** | 1.15 | **6.69** | 10.37 | 14.76 |

**33.1 % of the flying lap is still below the gate's own 3.0 dB threshold**, with
a fifth of it below zero. The gate scores the *median* per beat, so a beat can
pass with a third of its running time failing. The median moved; the worst third
did not.

**The two ungated beats are worse than the lap, and they are most of what the
client heard** (R2-1981). Per-beat HNR above 2.6 kHz on the delivered master:

| beat | HNR > 2.6 kHz | scored by the gate? |
|---|---:|---|
| 1_assembly | −1.36 | no |
| 2_launch | +5.68 | yes |
| **3_breach** | **+0.09** | **no** |
| 4_transit | +3.67 | yes |
| 5_lap | +6.69 | yes |
| **6_ending** | **+0.16** | **no** |

**11 seconds of ending and 8 seconds of breach read as essentially pure noise,
and 53 % of the client's clip set was the ending.** This is not fixed here — it
is a level/balance question per beat, not a synthesis question, and it wants its
own diagnosis rather than being stacked onto this render. It is the clearest
next target.

---

## R2-2001 — The exhaust pipes were being STRUCK, not driven. 100 % of 99 modes rang past the next firing event

This is the "banging on tubes" half, and it is measurable rather than a matter of
taste.

**The measurement.** Each pipe is `y[n] = x[n] -/+ g*LP(y[n-D])`, whose
denominator is the polynomial `(1 - c z^-1) -/+ g(1-c) z^-D`. **Its roots are the
modes**: root angle gives mode frequency, root magnitude gives decay,
`T60 = 60 / (-20 log10 |z|)` samples. Compare against the interval between firing
events — `20/rpm` seconds for a V6 at three firings per revolution.

Not an impulse-response estimate: a Schroeder decay on a band-filtered impulse
response measures the *analysis filter's* ringing as much as the pipe's. At
125 Hz a third-octave Butterworth has a T60 of **179 ms on its own**, longer than
anything the pipe does. Root-solving has no such floor. Both were run; the
band-filter version is what made the artefact obvious and the root solve is what
made it exact.

**As shipped, primary cylinder 0:**

| mode | T60 | Q | ring-through @ 4,300 rpm | @ 11,000 | @ 14,400 |
|---:|---:|---:|---:|---:|---:|
| 255 Hz | 37.65 ms | 4.36 | 8.1x | **20.7x** | 27.1x |
| 765 Hz | 35.21 ms | 12.24 | 7.6x | 19.4x | 25.3x |
| 2,301 Hz | 23.81 ms | 24.91 | 5.1x | 11.9x | 17.1x |
| 8,529 Hz | 9.53 ms | 36.96 | 2.0x | 4.8x | 6.9x |

**Across all six primaries: 99 modes below 9 kHz, and 100 % of them ring longer
than the interval to the next firing event, at every rpm in the film.** Median
7.5x at 11,000 rpm, worst 20.7x. The collector was worse still: T60 48.6 ms,
Q 6.5 — the longest-ringing element in the exhaust.

A resonator still ringing at 20x the drive interval is not being driven by the
engine. **It is being struck by it.**

**What is NOT the defect.** At 11,000 rpm the firing interval (1.82 ms) is
already shorter than one primary's acoustic round trip (1.91 ms), so a real
engine always has a previous pulse in the pipe and a ratio below 1 is not
physically available. The overlap is real; **its depth was the defect** — twenty
pulses ringing at once instead of three or four.

**Two hypotheses tested and rejected, which is why the fix is where it is:**

1. **"The six fixed pipe pitches are a chromatic cluster."** They are — 246, 261,
   261, 275, 277, 294 Hz is B3–C4–C♯4–D4 within 12 cents of equal temperament,
   which reads on paper as a set of tubular bells. **But it is not what is
   happening.** Synthesised at held rpm, energy at the six quarter-wave
   fundamentals sits **4.7 to 29.5 dB below** the firing series and its harmonics
   at every rpm from 4,300 to 14,400. The waveguide is periodically driven and
   locks to the firing rate; the pipe pitches do not stand out. Rejected on
   measurement.
2. **"Damp the loop harder."** The obvious fix, and a trap. A lowpass inside the
   loop is **dispersive**, so lowering its corner or raising its order shortens
   the effective pipe for the upper modes and the series stops being harmonic.
   Measured maximum deviation from the odd `c/4L` series below 9 kHz:

   | loop filter | max deviation | in cents |
   |---|---:|---:|
   | shipped, 1st order @ 3200 Hz | 1.41 % | 24 |
   | 1st order @ 2400 Hz | 2.28 % | 39 |
   | **3rd order @ 1200 Hz, delay-compensated** | **20.52 %** | **323** |

   That third row shortens T60 at 3 kHz from 18.5 to 2.8 ms — beautifully — and
   it is the **wrong answer**: an inharmonic partial series is the definition of
   a struck bell. It would have bought a quieter ring by making it a *more*
   bell-like one. **`PIPE_DAMP_HZ` therefore does not move.**

**The fix: the loop gains, which are frequency-flat in delay and so shorten the
ring without detuning the instrument.**

| constant | was | now | effect |
|---|---:|---:|---|
| `PIPE_LOOP_GAIN` | 0.70 | **0.34** | T60@f0 37.7 → 12.5 ms, Q 4.36 → 1.45 |
| `COLLECTOR_LOOP_GAIN` | 0.62 | **0.14** | T60@f0 48.6 → 11.9 ms, Q 6.48 → 1.59 |
| `PIPE_DAMP_HZ` | 3200 | **3200** | unchanged, deliberately — see above |

Ring-through at 11,000 rpm, worst element: **20.7x → 7.3x**. Median **7.5x →
4.9x**. All three elements now sit at Q 1.45–2.38 instead of 4.36–6.48.

**What it does to the audible ringing tail — the headline number.** Excite the
full chain at 11,000 rpm for 0.5 s, cut the excitation dead, and measure how long
the 2–6 kHz band takes to fall away. This is literally "how long do the tubes ring
after you stop hitting them":

| | −20 dB | −40 dB | −60 dB |
|---|---:|---:|---:|
| before | 7.67 ms | 17.17 ms | 26.08 ms |
| **after** | **3.33 ms** | **6.08 ms** | **6.46 ms** |

**4.0x shorter to −60 dB.** In firing intervals at 11,000 rpm the tail goes from
**14.3 to 3.5**.

**An honest negative, because it changes what can be claimed.** At *master* level
the 2–6 kHz envelope modulation over the lap did **not** improve — mean +0.17 dB,
only 11 of 29 windows better. Two reasons, and neither is a reason to doubt the
fix:

1. **The metric points the wrong way for this defect.** A long ring *fills* the
   gaps between firings and therefore *smooths* the envelope. Shortening it
   deepens the troughs and pushes p90/p10 **up**. The R2-1401 window-selection
   comment in `tools/audio_watch_clips.py` had this backwards and has been
   corrected in place — it is a measure of how *exposed* each event is, which is
   what makes it a good window to listen at, not a measure of the defect.
2. **6–14 kHz, where the metric is not confounded, moved a lot**: −3.70 dB at
   73.5 s, −5.13 dB at 63.5 s, −1.25 dB at the transit. That is the metallic top
   getting less spiky, which is the part of the band the excitation floor
   (R2-2002) acts on hardest.

So the defensible claims are the exact ones: **mode T60 is 3.0x shorter by root
solve, the audible tail is 4.0x shorter by direct measurement, and the master's
6–14 kHz articulation drops up to 5.1 dB.** The 2–6 kHz master envelope is not
evidence either way.

**The physical reading of the smaller numbers.** The shipped values counted
radiation from the open end and nothing else, and radiation alone really is that
lossless — an unflanged 42 mm pipe reflects ~0.98 at 1 kHz, which is why the
model rang. What was missing is everything else a *turbocharged* exhaust does to
a pressure wave: gas leaving at 100+ m/s convects energy out of the primary, and
the turbine past the collector is a near-total acoustic sink rather than a
reflector — extracting that energy is what it is *for*. Both are broadband, and
both belong in the round-trip magnitude. The collector's old comment already
claimed "the turbine is a large, lossy obstruction"; 0.62 did not model one.

---

## R2-2002 — The blowdown rise time had no floor, so the model hit the pipes hardest exactly where it fired most often

The second half of the same mechanism. R2-2001 shortens the ring; this stops
striking it so hard.

`attack` is a **fraction of a crank-angle-fixed window**, so the rise time in
seconds falls as 1/rpm with nothing stopping it:

| rpm | rise time, full load | excitation energy above 2 kHz |
|---:|---:|---:|
| 4,300 | 237 µs | −16.66 dB |
| 8,000 | 128 µs | −10.36 dB |
| 14,400 | **71 µs** | **−6.34 dB** |

A 71 µs raised-cosine edge is spectrally flat past 10 kHz. **The excitation's
energy above 2 kHz rose 10.3 dB from idle to the limiter** — so the model struck
the high modes hardest at exactly the rpm where it also fired 3.3x more often,
into modes with T60 of 9–20 ms. That is a hammer.

**A real blowdown cannot rise that fast at any rpm.** Port pressure is set by
choked discharge through the opening valve curtain, whose time constant is
`V/(A_eff·c)` — a *time*, independent of crank speed. Higher cylinder pressure
chokes harder and discharges faster, so the floor is **shorter under load**,
which is the same direction R2-1401's load-shaping already runs.

```
rise_floor_s = 180e-6 + (420e-6 - 180e-6) * (1 - load*fuel)
attack = clip(max(attack, rise_floor_s / (0.085*cycle_s)), 0.02, 0.60)
```

**R2-1401 is not undone.** The floor only ever *lengthens* a rise, so below
~6,000 rpm it does nothing at all and R2-1401's behaviour there is untouched bit
for bit. Where it does bite it keeps the load span: at 14,400 rpm full load
180 µs against overrun 420 µs is still **2.3x**, where the unfloored model had
71 vs 212 µs. Measured on the dry exhaust, energy above 2 kHz falls 1.9–2.7 dB at
the top of the range and stops climbing with rpm.

---

## R2-2003 — The tube fix was quietly making the wind complaint worse, until it was compensated

Caught before the delivered render, not after, and worth recording because it is
the kind of interaction that turns one fixed complaint into two live ones.

**Shortening a ring removes energy.** Measured on the dry exhaust bus with the
R2-2001/2002 constants against the shipped ones:

| rpm | throttle | old RMS | new RMS | change |
|---:|---:|---:|---:|---:|
| 4,300 | idle | −23.46 | −26.53 | −3.07 |
| 8,000 | full | −15.75 | −20.12 | −4.37 |
| 11,000 | full | −17.37 | −20.69 | −3.32 |
| 13,000 | full | −16.77 | −18.23 | −1.46 |
| 14,400 | full | −17.10 | −18.71 | −1.61 |
| 12,000 | overrun | −24.15 | −30.58 | **−6.43** |

Mean on throttle: **−2.69 dB**.

**Everything else in the engine bus is fixed-level** — `rasp`, `turbo`, `mguh`,
`mguk`, `pump` — and the bus is then trimmed **as a whole** to −10 LUFS-S. So an
uncompensated exhaust drop does not make the engine quieter; it hands 2.7 dB of
the engine over to its own noise layers. In the shipped report the exhaust sits
at 0.0806 RMS against 0.0163 for the sum of the others, a 13.9 dB lead; losing
2.7 dB of that takes it to 11.2 dB.

**That is the wind-machine complaint, made worse by the fix for the tube
complaint.** The two notes would have traded against each other and the client
would have been right a third time.

`"exhaust": exhaust * 0.55` → `* 0.75` (+2.69 dB, ×1.364), which puts the exhaust
back exactly where R2-1401 balanced it against the noise layers. **This is level
compensation, not a louder engine** — the bus LUFS target is unchanged, so the
film's loudness is unchanged.

It restores RMS, so the transients come back very slightly prouder than before
against a ring that is now 3x shorter. That is the intended direction: a clean
pulse at the firing rate is what an engine *is*. What was wrong was the twenty
pulses still ringing behind it.

---

## R2-2004 — A gate for the question none of ours were asking

**Every gate we own passed a master the client called complete shit, and the
harmonic gate passed it most emphatically of all** — HNR above 2.6 kHz went
3.2 → 23.7 dB in the rebuild that *caused* the banging.

That is not a bug in the harmonic gate. HNR asks *"is this tonal rather than
noisy"*, and **a struck tube is extremely tonal — it scores well.** Nothing we
owned asked the other question: does the tone *stop* between firing events, or
ring on into the next one.

`waveguide_gate()` in `audio/verify.py`. It measures **decay, not spectrum**, and
it reads the synthesiser's own constants rather than the rendered wav — the mode
structure is fully determined by `PRIMARY_L_CYL`, the loop gains and the damping
corners, so solving it directly is exact, instant, and cannot be masked by the
wind bed sitting on top of it in the mix.

Thresholds, chosen against the rejected masters and not against the fix:

| | limit | rejected #2 | now |
|---|---:|---:|---:|
| median mode ring-through @ 11,000 rpm | ≤ 5.0 | 8.34 | **4.85** |
| worst mode below 9 kHz | ≤ 9.0 | 20.71 | **7.29** |
| max deviation from the harmonic series | ≤ 4.0 % | 1.41 | **1.74** |

**Positive controls** — the first three must FAIL, the fourth must PASS:

| control | med | worst | harmonic | PASS |
|---|---:|---:|---:|---|
| R2-1401 shipped, 0.70/3200 (the rejected master) | 8.34x | 20.71x | 1.41 % | **False** |
| near-lossless pipe, gain 0.85 | 10.70x | 44.97x | 1.40 % | **False** |
| 3rd-order in-loop lowpass @ 1200 Hz — short ring, **inharmonic** | 1.27x | 8.20x | **20.52 %** | **False** |
| STATED NEGATIVE: the values now shipped | 4.58x | 6.89x | 1.45 % | **True** |

The third control is the one that matters for the future. It is the tempting
wrong fix from R2-2001, it passes both decay limbs comfortably, and **it is
caught only by the harmonicity limb.** If that limb is ever deleted as
redundant, this control starts passing and the gate stops protecting anything.

`ALL_PASS` now aggregates eight gates: `levels`, `edges`, `seam`,
`external_assets`, `pitch`, `doppler`, `harmonic`, `waveguide`.

---

## R2-2006 — The harmonic gate has never once run inside the suite, and the report on disk is from a master two rebuilds ago

Found by running the suite, which had apparently not been done end to end since
14:45 yesterday.

```
File "audio/verify.py", line 1316, in main
    V["harmonic"] = harmonic_gate(x, sr, sheet, ...)
File "audio/verify.py", line 952, in hnr_profile
    P = np.abs(np.fft.rfft(x[a0:a0 + n] * w)) ** 2
ValueError: operands could not be broadcast together with shapes (4096,2) (4096,)
```

`hnr_profile` windows with a 1-D Hann. `main()` passes the master, **which is
stereo**. So the harmonic gate threw every single time the suite ran it.

**Three things follow, and they matter more than the one-line fix.**

1. **`ALL_PASS` was never reached.** The aggregation and the report write are
   *after* the harmonic gate, so the run died before either. `verify_report.json`
   on disk is dated **7 Aug 14:45** — older than `verify.py` (16:21), older than
   the R2-1401 rebuild (15:19), older than the master the client was given
   (17:10). It describes a master from two rebuilds ago and carries **six** gate
   keys.
2. **So "every gate we own passed the mix the client rejected" is not true.**
   The gates never finished running on it. The six that print before the crash
   printed; nothing aggregated them; nothing wrote them down. The failure looked
   exactly like a healthy run, because stdout is buffered and stderr is not, so
   the traceback surfaces at the *top* of the log above six gates' worth of
   healthy-looking output.
3. **It was only ever exercised on mono.** `control_harmonic` reduces its own
   control files with `y.mean(axis=1)`, so the mono requirement was known — it
   was simply never applied to the master itself. Every standalone invocation
   (including the R2-1401 3.2 → 23.7 dB figure) passed mono and worked.

Fixed at the two entry points rather than at the call sites, so no future caller
can reintroduce it: `harmonic_gate` reduces to mono on entry, and
`control_harmonic` does the same before it *builds* controls 2 and 3 out of `x`
(a stereo band-split was being added to mono noise).

With it running, on the new master: worst engine-driven beat **HNR 4.94 dB**
(threshold 2.0), **HNR above 2.6 kHz 3.91 dB** (threshold 3.0). PASS, and all
three controls fail as required.

---

## R2-2007 — The film ended on a hard truncation. Same defect as the frame-1 bang, other end of the film, and it was in the master the client was given

Exposed by R2-2006: once the suite could reach its own aggregation, `edges`
failed — **on the last frame, not the first.**

`audio/master.py` cuts the master to length with `out = out[:want]` and nothing
puts it down. The film ends on a running idle, so the final sample lands wherever
in the firing cycle the cut happens to fall:

| master | last sample | step above trailing RMS | verdict |
|---|---:|---:|---|
| `master_SHIPPED_aug2` (2 Aug) | 0.0298 | +0.40 dB | ok, by luck |
| `master_R2-1400_REJECTED_hairblower` | 0.0414 | +2.40 dB | ok, by luck |
| **`master_B_lapdown` — what the client heard** | **0.1217** | **+8.02 dB** | **FAIL** |
| this render, before the fix | 0.1089 | +7.98 dB | FAIL |

**It is luck, not design** — the three differ only in where the cut fell in the
idle cycle. **This is the exact mirror of R2-960's +31 dB bang on frame 1**: same
class of defect, other end of the film, and `edge_gate` has been failing it all
along with nobody able to read the verdict.

Frame 1 is unaffected and stays green — crest +8.33 dB, step **−12.47 dB**, well
inside the +3.00 limit. The `np.roll` fix is intact.

**Fix:** 12 ms of raised cosine at the tail, applied *after* the loudness
iteration so nothing downstream can scale the endpoint back off zero. At 24 fps
that is 0.29 of one frame; against a 215 Hz idle (4.65 ms period) it is 2.6
cycles — a clean stop rather than an audible fade. **Duration unchanged: 2,978
frames, 124.0833 s.**

---

## R2-2009 — MY MISTAKE: I destroyed the exact master the client was played

Recording this plainly because it is the same class of failure as R2-1981, made
by me, four hours after writing R2-1981 up.

Regenerating the ending A/B needs `master_B_lapdown.wav` to be the current
master, so I copied the new render over it — **and `master_B_lapdown.wav` WAS the
artefact the client had just rejected.** `*.wav` is gitignored (`.gitignore:19`),
so there was no second copy and no VCS history. The exact bytes the client
listened to are gone.

**What survived, and how close it is.** `master_A_nolapdown.wav` from the same
17:59 render of the same code was still on disk and was copied to
`master_R2-2001_REJECTED_tubes.wav` before the A re-render could take it too. A
and B are the same film until 113.1 s, but **not bit-identical even before then**
— `master.py`'s whole-film gain staging is a function of the ending, which is
exactly what `tools/audio_ending_ab.py` was built to report. Measured over the
6 s A/B window at 73.5 s, against `16_lap_BEFORE_tubes.wav`, which had already
been cut from the true B:

| | |
|---|---:|
| best-fit broadband gain B/A | 0.99926553 (**−0.0064 dB**) |
| residual after removing it, RMS | −86.45 dBFS |
| …relative to the window | **68.9 dB below signal** |

Inaudible, and none of the ringing this A/B demonstrates lives in it. So the
A/B stands. But it is a **substitute**, and `tools/audio_watch_clips.py` now says
so at the point of use so that nobody later describes it to the client as the
exact file they played.

**The actual lesson is the gitignore.** Every rejected master is evidence — it is
the only thing that can prove a fix landed — and the one directory holding them
is excluded from version control with no archival rule of its own. The three
survivors (`master_SHIPPED_aug2`, `master_R2-1400_REJECTED_hairblower`, and now
`master_R2-2001_REJECTED_tubes`) survive only because someone gave them names
that no pipeline step writes to. `master_B_lapdown.wav` had a name the pipeline
writes to, so it died. **Rejected artefacts should be renamed out of the
pipeline's namespace the moment they are rejected**, not left under the filename
that produced them.

---

## R2-2010 — Clips 07 and 08 were cut from orphaned files no tool has written for weeks

Re-cutting the clips (R2-1981) was not on its own enough to make the page honest,
because two of them do not come from the master at all.

`tools/audio_watch_clips.py` read:

```
END_A = .../ab/ending_A_nolapdown.wav
END_B = .../ab/ending_B_lapdown.wav
```

`tools/audio_ending_ab.py` writes `ending_A.wav` and `ending_B.wav`. **Nothing in
the pipeline has written the `_nolapdown` / `_lapdown` names in a long time**, so
those two files sat at 7 Aug 17:59 while the master they were meant to represent
was rebuilt twice. Clips 07 and 08 — **the two clips that carry the one creative
decision only the client can make**, and 24 of the 57 seconds they were played —
were cut from them.

This is the R2-1981 defect one directory deeper: not a stale *cut*, a stale
*source*. Re-running the cutter would never have fixed it.

Repointed to the names the ending tool actually emits, and the two orphans
deleted so they cannot be picked up again.

**Verified after the fix** — every "after" clip re-derived from the delivered
master and compared sample-for-sample against it:

| clip | max abs delta vs `master.wav` |
|---|---:|
| `02_opening_AFTER_fixed` | 0.000e+00 |
| `04_launch_seam` | 0.000e+00 |
| `05_breach` | 0.000e+00 |
| `06_ending_seam` | 0.000e+00 |
| `09_final_idle` | 0.000e+00 |
| `11_lap_AFTER_rebuilt` | 0.000e+00 |
| `13_launch_AFTER_rebuilt` | 0.000e+00 |
| `17_lap_AFTER_damped` | 0.000e+00 |

**And the standing extract defect is not reintroduced.** Every extract this
project has ever cut opened on a hard cut at +9.67 dB. Across the 16 clips that
are not the deliberate frame-1 defect demonstration, the worst opening step is
**+0.00 dB** — every one of them starts from a boundary sample of exactly zero.
Clips 01 and 03 still open at +19.58 dB, which is the artefact they exist to
show.

---

## R2-2008 — Not done, and why

- **Mode coupling between the primaries** — the third candidate cause. The six
  pipes are summed into the collector and nothing returns up them, so they are
  six independent resonators rather than one manifold. Physically real, and
  deliberately not attempted: it means a global feedback path across six delay
  lines evaluated over 11.9 M samples, with genuine instability risk, and the
  two changes above are what the measurements actually pointed at. Worth doing
  as its own piece of work with its own stability proof, not stacked onto a fix
  the client is waiting on.
- **The breach and the ending** (R2-1982) — 0.09 and 0.16 dB HNR above 2.6 kHz,
  ungated, and 63 % of what the client heard. The clearest next target.
- **The harmonic gate's per-beat median** (R2-1982) — it passed a lap with 33 %
  of its running time below the threshold. A percentile floor would not have.
