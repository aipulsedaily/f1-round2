# STAGING R2-1401 to R2-1450

## R2-1401 — "AUDIO IS SHIT SOUNDS LIKE A HAIR BLOWER"

The client's words, verbatim, on the shipped master. It is the harshest note on
any part of this project and it is about the single most important sound in the
film. It is also a **precise** complaint, not a vague one, and it turned out to
name the defect exactly.

### What a hair dryer is, and what the measurement found

A hair dryer is **broadband noise shaped by a resonant cavity, with no harmonic
series**. An engine is a **line spectrum rigidly locked to a firing frequency**.
The difference between them is one number — the ratio of tonal energy to
broadband energy — and **nothing in this project measured it.**

Measured on the shipped master (`master_R2-1400_REJECTED_hairblower.wav`, kept
on disk as the gate's control), median harmonic-to-noise ratio per beat:

| beat | HNR | HNR above 2.6 kHz |
|---|---|---|
| 1_assembly | 3.36 dB | −0.94 dB |
| 2_launch | 15.34 dB | +0.85 dB |
| 3_breach | 1.87 dB | +1.91 dB |
| 4_transit | 4.91 dB | −0.36 dB |
| **5_lap** | **4.18 dB** | **−0.65 dB** |
| 6_ending | 1.44 dB | +0.79 dB |

**Above 2.6 kHz the film was −0.65 dB — the top four octaves of an F1 car
contained more noise than harmonic content.** That is the complaint expressed as
physics, and it is not a balance problem. There were no harmonics up there to
un-bury.

**The diagnosis was not "the harmonics are buried". It was "the harmonics do not
exist above 2 kHz", and it had two independent causes, both structural.**

### Cause 1 — the exhaust's mode series was truncated at its fourth term

`engine.py` synthesised the exhaust as a sum of 2-pole bandpasses placed on the
pipes' computed mode frequencies: four orders per primary, five for the
collector, three for the tailpipe.

```
primaries A   c/4L, L=0.62   276.6  829.9  1383  1936   <- stops here
primaries B   c/4L, L=0.66   259.8  779.5  1299  1819
collector     c/2L, L=1.15   298.3  596.5  894.8 1193  1491
tailpipe      c/2L, L=0.55   623.6  1247   1871
```

**The highest term in the entire harmonic path was 1,936 Hz.** A pipe does not
have four modes; it has as many as fit under Nyquist. Everything the film had
above 2 kHz therefore came from noise generators *by construction* — the
`rasp` band (300–2600 Hz), the turbo `blade` band (2500–11000 Hz) and `surge`.

**Fixed as a digital waveguide** (`dsp.comb_pipe`). A pipe is a bidirectional
delay line, `y[n] = x[n] ± g·LP(y[n−D])` with `D = round(2L/c·sr)`:

* `invert=True` (closed at the valve, open at the collector) → poles at the
  **odd** multiples of c/4L — the quarter-wave series.
* `invert=False` (open at both ends) → poles at **all** multiples of c/2L.

Same two formulae the old code evaluated by hand, now generating the **whole
series to Nyquist**. The in-loop one-pole is the frequency-dependent part of the
open-end reflection (radiation resistance grows as (ka)², so high modes are
broader) — the Q roll-off comes out of the physics instead of being a table of
hand-set Q values. Exact, not approximate: inside a window of D samples every
value the recursion reads was written before the window began, so it vectorises
with a bit-identical result — the same argument `fdn_reverb` already uses.

**Six primaries, not two.** The old model ran one pipe per bank, so a bank's
three cylinders were excited into an *identical* resonator and their partials
stacked exactly — a synthesiser's engine. The three cylinders of a bank sit
~98 mm apart along the block with the collector at one end, so their primaries
**cannot** be equal-length. Modelled at ±6 % about each bank's nominal: six
slightly detuned pipe series at 260–295 Hz, so every firing harmonic meets a
different sum of six responses. That is where an **uneven partial profile** comes
from, and an uneven partial profile is the thing a noise generator cannot fake.

### Cause 2 — the excitation had no high-frequency content to give the pipe

The combustion event was `dsp.phase_pulse`, a raised cosine. A raised cosine is
C1-continuous, so its spectrum falls at **−18 dB/octave** above 1/w. At 12,000
rpm the old call — width 0.055 of the 720° cycle, i.e. 550 µs — put that corner
at about **1.8 kHz**. Even with an untruncated pipe there would have been almost
nothing above 2 kHz to resonate.

**A blowdown is not a bump.** The exhaust valve cracks against 8–12 bar, flow
chokes essentially at once, and the pressure front is close to a weak shock;
the cylinder then empties roughly exponentially. `dsp.blowdown_pulse` is that
shape: a steep raised-cosine rise over `attack_frac` of the pulse, then an
exponential decay tapered back to zero. It still starts and ends at zero with
zero slope, so it does not alias — at 14,400 rpm the 66th harmonic sits at
Nyquist and is already 60+ dB down — but the corner moved a decade up.

**`attack_frac` is the load knob, and this is the part the brief called for by
name.** Load *is* cylinder pressure at valve opening: at full throttle the valve
cracks against three or four times the pressure it sees on a trailing throttle,
so the front is steeper and the blowdown harmonically richer. The old model
multiplied one fixed pulse shape by a gain envelope, so **the only thing throttle
did to the exhaust was change its volume** — which is precisely a fan with a
speed control. Now the engine gets genuinely harder and brighter under power and
thins off-throttle. Measured, this moves the exhaust's spectral centroid by about
an octave across the load range.

### Cause 3 — the turbo was, almost literally, a hair dryer

`whine` sat on shaft orders 6/12/18 plus 2.5–11 kHz white noise at 0.55. At full
boost the shaft turns 2,083 rev/s, so:

```
order 6  -> 12.5 kHz     order 12 -> 25.0 kHz     order 18 -> 37.5 kHz
```

**Two of the three tones are ultrasonic whenever the car is pulling and the third
is at the very top of hearing.** Everything audible from the turbocharger through
the entire flying lap was a band of filtered white noise. A hair dryer *is* a
small compressor wheel making broadband noise in a volute — the client did not
reach for a metaphor, he identified the component.

Rebuilt on what a compressor actually radiates: low shaft orders 1–4 (rotor
imbalance and the pressure field sweeping the volute tongue, 1.7–8 kHz — audible,
and roughly the "order of magnitude above the firing frequency" a turbo is heard
at); blade passing at orders 7 and 14 (7 full blades + 7 splitters), ultrasonic at
peak but sweeping up through the audible band during spool, which *is* the sound
of a turbo spooling; and broadband cut to a sixth, rolled off above 9 kHz, and
modulated at the blade rate rather than left as stationary hiss.

**Turbine torque ripple** added: the turbine is hit by six blowdown pulses per
cycle, so the shaft carries a small speed ripple **at the firing frequency**,
which frequency-modulates every compressor tone and puts sidebands a firing
interval either side of each. It is why a real turbo tone is grainy and locked to
the engine, and why an unmodulated sine at the same frequency reads as a test
tone.

### Cause 4 — overrun was carried by a noise layer

With the injectors cut the engine is still turning at 13,800 rpm and the pistons
are still pushing a full cylinder of air down each primary every cycle. That
motored pumping **rings the pipes at the same 3-per-revolution rate**, which is
why a real overrun is a hard hollow tone and not a hiss. The pipe excitation
floor on a shut throttle was 0.25; it is now 0.38, the broadband `pump` layer is
cut from 0.35 to 0.16, and the overrun pops — a signature of this engine, and
20 dB under the pipe — are lifted from 0.15 to 0.26.

### Measured result, dry engine bench

| operating point | HNR before | HNR after | HNR >2.6 kHz before | after |
|---|---|---|---|---|
| full throttle, 250 km/h | 11.62 dB | **20.3 dB** | 3.22 dB | **23.7 dB** |
| full throttle, 310 km/h | 16.39 dB | **24.4 dB** | 3.87 dB | **23.1 dB** |
| overrun, 250 km/h | 1.02 dB | **8.9 dB** | 7.73 dB | **11.9 dB** |
| idle-ish, 40 km/h | 20.04 dB | 20.3 dB | 1.11 dB | **12.1 dB** |

Harmonic-to-broadband within the engine bus, on throttle: **21.8 dB**. On
overrun: **9.4 dB**, up from 1.3 dB. The strongest spectral line at every
operating point is the firing fundamental, with 2× firing second — verified
directly, and non-firing crank orders sit 10–23 dB below it (present, because
cylinder scatter is real, but subordinate, which is correct for a V6 sharing one
turbine).

### R2-1402 — THE SECOND DEFECT: THE MIX BURIES THE ENGINE ABOVE 2.6 kHz

**The rebuilt engine gained 20 dB of harmonic content above 2.6 kHz. The master
gained 0.9 dB.** Measured on the first full render after the rebuild, the flying
lap went from −0.65 dB to +0.26 dB — against a dry engine bench of +23.7 dB and
an engine-bus internal harmonic-to-broadband of 22.3 dB. Almost the entire fix
was being thrown away in the mix.

Quantified independently, by re-rendering six buses of the real mix through the
project's own code path, one bus per process. The re-render reproduces the shipped
trims to **0.000 dB** on tyres, wind, crowd and fence, which is what makes the
numbers trustworthy. Post-trim, over film 49.6–113.1 s:

| bus | 20 Hz–16 kHz | 2.6–16 kHz | dB rel engine | tonal structure? |
|---|---|---|---|---|
| engine | −27.22 | −37.23 | — | yes |
| **wind** | **−22.48** | −41.58 | **−4.34** | **none at all** |
| tyres | −34.77 | −44.36 | −7.13 | none above 1.2 kHz |
| bed | −37.67 | −50.23 | −12.99 | none |
| crowd | −46.59 | −51.98 | −14.75 | none |
| fence | −43.74 | −70.20 | −32.97 | yes, but all below 1 kHz |
| room | −∞ | −∞ | −∞ | `max(inside)` over the lap is **exactly 0.0** |

**Wind is the loudest bus in the film over the flying lap — 4.7 dB above the
engine by total energy — and it contains no tonal element anywhere.** For a film
whose subject is a car, that is wrong on its face, independent of any masking
argument. `layers.py:155-164` is brown-noise buffet plus a pink-noise edge band;
there is nothing in it to hear but air.

**Two calibration facts that sharpen the whole diagnosis:**

* **The HNR metric reads −1.7 dB on provably pure noise**, not −∞ (crowd, fence's
  skirts and room tone above 2.6 kHz all land at −1.70…−1.75). So the shipped
  master's −0.65 dB was **1.05 dB above a literal noise generator.**
* **The engine's mix trim is set by the wrong window.** Its −10.0 LUFS-S is spent
  on a 3-second window at 38.5–41.5 s — inside the *slow-motion breach* — so
  through the entire flying lap the engine runs **1.45 dB below its own target**
  while wind and tyres run at theirs (their peak windows are at 107.5–111.5 s,
  inside the lap).

Ranked contribution to the non-engine broadband floor above 2.6 kHz: **wind
56.4 %, tyres 32.3 %**, bed 5.7 %, crowd 5.5 %, fence 0.1 %, room 0.0 %.
**Removing crowd, fence and room entirely buys +0.12 dB** — they are not part of
the problem and no change is spent on them. The two reflection buses are shut
through the whole of 60–80 s (`reflect_garage` is open 6.0 % of the lap,
`reflect_showroom` 0.64 %) and mask nothing.

**The remedy is a mix decision and is declared as one.** `TARGET_LUFS_S`'s own
docstring already says the physics does not set this balance — *"'the physics set
the balance' is exactly the kind of principled-sounding decision that produces an
unusable artefact"*. The wind's ~9 dB/octave rolloff (pink noise through a
one-pole) sits inside the physical range for aerodynamic edge noise and is **not**
being called a modelling error. What changes is one constant per bus, plus one
declared shelf, which is what a mix is.

```
TARGET_LUFS_S["wind"]   -18.0 -> -23.0
BUS_HF_SHELF            wind, tyres, bed:  -12 dB above 2 kHz, applied post-trim
```

Sized against a real mix experiment, not a guess: the rebuilt engine bus was
re-rendered and summed against the *unchanged* delivered bed buses, and the trim
and shelf swept. Over the flying lap:

| mix | HNR | above 2.6 kHz |
|---|---|---|
| engine bus alone (the ceiling) | 16.78 | **14.35** |
| beds as shipped | 3.09 | **0.71** |
| HF −6 dB | 3.28 | 2.99 |
| HF −12 dB | 3.36 | 5.42 |
| **wind −4 flat + HF −12 dB @ 2 kHz** | **3.89** | **6.70** |
| wind −4 flat + HF −15 dB @ 2 kHz | 3.91 | 7.48 |

Chosen deliberately short of the maximum: the beds stay audible and keep doing
their job, and **the film gets brighter where it matters rather than darker.**
Octave balance over the lap, relative to peak: 500 Hz–1 kHz **+3.6 dB**, 1–2 kHz
**+3.5 dB**, 2–4 kHz **+2.6 dB**, and only **−1.9 dB** in the top octave — because
the engine's own harmonics now occupy the space the noise was in.

**A method error worth recording, because it nearly produced the wrong
conclusion.** The first shelf sweep used `x - highpass(x)*(1-g)` with a *causal*
high-pass. A causal high-pass is not the complement of anything, so subtracting it
comb-filters instead of shelving: sweeping its depth from −6 to −18 dB moved the
lap's HNR by **0.04 dB**, which reads exactly like "the beds are not the problem
after all". The corrected form uses a zero-phase lowpass so `lo + hi == x` to
machine precision — the construction `dsp.split_bands` already uses, for the same
reason — and the same sweep then moved it by **5.9 dB**.

**The analysis window was also wrong, and fixing it cut both ways.** The metric
started at 93 ms. The source is a car whose pitch moves under both rpm and Doppler
— at the doppler station the ratio spans 1.29 to 0.81 over 7 s — so inside 93 ms an
8 kHz partial sweeps ~48 Hz, four analysis bins, and smears into the very floor it
is being compared against. On the rebuilt engine bus alone, above 2.6 kHz: 21 ms →
4.52 dB, **43 ms → 14.35 dB**, 93 ms → 10.38 dB, 186 ms → 5.84 dB. 43 ms resolves a
600 Hz firing series at 23 Hz bins and is short enough that the lines stay put.
**The rejected master was re-measured at the same window before any threshold was
chosen** (lap above 2.6 kHz: −0.73 dB at 43 ms against −0.65 dB at 93 ms), so the
window was not picked to flatter the fix.

### R2-1403 — THE GATE THAT SHOULD HAVE EXISTED FIRST

**Every gate in `verify.py` passed the master the client rejected.** They were
all correct: levels legal, seams clean, pitch tracking the telemetry to 1.3 cents,
Doppler solving to 5.2 cents. Not one of them asked whether the sound was an
*engine* rather than a *fan*, because that question is about a ratio and nothing
measured it. **Nobody on this project can hear, so anything not measured is not
checked** — and this defect is the proof.

`verify.py::harmonic_gate` measures the tonal-to-broadband ratio per beat via a
median-filtered spectral floor (a median is insensitive to the sparse narrow peaks
a harmonic series makes, so it tracks the noise underneath them). No f0 estimate
is involved, deliberately: by the time the signal reaches the master it has been
through a moving Doppler shift, two facade reflections and a 2.4 s room tail, so
the lines are neither stationary nor exactly harmonic. Scored over the beats the
engine drives (2_launch, 4_transit, 5_lap) — beat 1 is an empty showroom, beat 3
is a breaking window, beat 6 fades to a distant idle, and none of them is supposed
to be harmonic.

Three positive controls, one of which was not constructed to fail:

1. **The R2-1400 master itself**, kept on disk. The artefact the client actually
   rejected, scored by the gate written to catch it.
2. **White noise wearing the master's own octave balance** — a literal hair
   dryer with the film's exact tonal balance and no line spectrum at all. If the
   gate were secretly measuring brightness or level rather than harmonicity, this
   would pass.
3. **STATED NEGATIVE**: the master with its top four octaves replaced by noise of
   equal band energy — the R2-1401 defect reconstructed on top of a *fixed*
   master. It must fail the HF threshold while still passing the broadband one,
   which is what makes those two thresholds separate numbers.

### R2-1404 — REVIEW EXTRACTS OPENED ON A HARD CUT

`tools/audio_ending_ab.py` wrote `x[a:]` with no fade — a hard cut into the middle
of a 313 km/h flying lap, so every A/B extract this project made for human review
opened on a step transient that is an artefact of the extraction and not of the
film. Measured on the previous pair: a +0.89 dB opening step with a 0.089
sample-to-sample jump inside the first 2 ms. On this project a click at the top of
a review clip has already been mistaken for a defect in the master once. A 5 ms
in-point fade is now applied; the out-point is the film's own last sample and is
left alone. `tools/audio_watch_clips.py` already faded its own in-points and is
unchanged in that respect.

### R2-1405 — FOUND, NOT FIXED: 48 % OF THE FLYING LAP IS CLASSIFIED AS "DAIS"

Found while measuring the tyre bus and recorded here because it is real, it is in
`audio/`, and it is **not** being fixed in this pass.

`scene.py:456` guards asphalt with `x > 64.6`; `scene.py:445` gives dais
`band(-1e6, 3.70)` with **no such guard**. The car's world x is below 3.70 m for
**47.9 %** of the flying lap (it ranges −635 … +557 m), so both classifications
fire and the render agrees: `surface_time_fraction_while_moving` reports
`dais 0.387 / asphalt 0.489`. **For roughly 40 % of the flying lap the tyres are
rendered as a hollow timber showroom deck** (`hollow*1.6 + roar*0.4`,
`layers.py:83`) instead of as asphalt — a genuine desync between the tyre voice
and the picture.

**Deliberately left alone in this pass, for two reasons.** It is a different
defect from the one the client raised; and the dais voice is *darker* than the
asphalt voice, so correcting it would add broadband energy in exactly the band
R2-1402 just cleared and would make the hair-blower complaint marginally worse.
It needs its own listening pass with the mix re-checked afterwards. **This is the
next audio item.**

### What was NOT changed

The driveline, the gearbox solution, the clutch/launch model, the shift events,
the shift/launch RNG streams, the propagation, the program gain and the limiter
are untouched. The render reports the same 31 upshifts, 31 downshifts and
14,351 rpm maximum as before, which is the check that the rebuild is confined to
the exhaust and turbo voice. No bus trim moved except wind's, and the only EQ
added is the declared three-bus shelf.

Crowd, fence, room and both reflection buses were measured, found irrelevant to
the defect (+0.12 dB between them), and **left alone**.

Audio is CPU-only. **Cost on the farm: $0.**
