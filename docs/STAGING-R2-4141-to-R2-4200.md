# STAGING R2-4141 to R2-4200

Audio rebuild 4, the showroom. R2-4081..4086 built the instruments; this pass
builds the sound against them, and it is the first pass in this project whose
beat-1 target came from a POSITIVE CONTROL rather than from a bar.

**Four predictions in this pass were confidently made and wrong on
measurement.** Three of them are recorded below in more detail than the fixes,
because they are worth more.

---

## R2-4141 — THE FIRST MEASUREMENT: THE INHERITED BUILD WAS THE REJECTED ONE, AGAIN

`audio/out/r2_4088/master_R2-4088.wav` was rendered by a stopped agent and left
unvalidated. It was measured before anything else, on the instruments R2-4082
and R2-4085 shipped:

| beat 1 | note cover | chord cover | held power | G-EVENT dB | Boersma HNR |
|---|---:|---:|---:|---:|---:|
| bar | ≤0.20 | ≤0.05 | ≤0.15 | ≥13.7 | *(retired here)* |
| **C9 assembly cell (positive)** | **0.000** | **0.000** | **0.0000** | **37.38** | −5.36 |
| M1 `master.wav`, "a hair blower" | 0.158 | 0.000 | 0.0105 | 13.25 | +0.26 |
| M3 R2-4079, "a shitty musical" | 0.375 | 0.286 | 0.0116 | 11.18 | +0.49 |
| **R2-4088, unvalidated** | **0.251** | **0.133** | 0.0583 | 12.03 | **+10.37** |

R2-4088 fails two limbs of G-SUSTAIN. It holds a 2.09 s note and it holds three
at once over an eighth of the beat. **It reads +10.37 dB of Boersma HNR — it
cleared the old +8 dB beat-1 bar, which is exactly what it was built to do, and
that bar was retired at R2-4084 in the same commit its source tree was written
against.** It is a fourth drone, arrived at by a different route: one line
shaft, every station geared from it, one harmonic series in the building.

`master_R2-4081.wav` measures 0.375 / 0.286 / 11.18 — **bit-for-bit the same
verdict as M3**, i.e. it is the musical master re-rendered.

Neither is a starting point. Both are recorded here so that "unvalidated" never
again means "probably fine".

---

## R2-4142 — WHERE BEAT 1's DEFECT ACTUALLY LIVES, MEASURED ONE VOICE AT A TIME

`tools/r2_4141_cell_bench.py --parts` renders the `assembly` layer's two voices
separately and measures each. The answer was not what three passes of tuning
had assumed:

| | note | chord | held power | G-EVENT dB |
|---|---:|---:|---:|---:|
| **the film's 777 part impacts, alone** | **0.060** | **0.000** | **0.0176** | **27.17** |
| R2-4088's line-shaft drive, alone | 0.233 | 0.210 | 0.1749 | 13.93 |
| the two summed | 0.237 | 0.211 | 0.1464 | 13.64 |

**The impacts already pass everything.** They are percussive, inharmonic,
transient-dense and unpitched, they have a geometry and a material per part, and
they measure 27.17 dB of local dynamic range against a 13.7 dB bar. Every
beat-1 defect the client has named for four masters lives in **the bed** — and
the bed drags the layer down by 13.5 dB on its own.

That is the whole diagnosis, and it took twenty minutes of measurement after
three passes of arguing about spectra.

---

## R2-4143 — `cell_events`: THE BED IS DELETED AND REPLACED BY A CELL

`layers.servo_bed` (R2-4070, fifteen oscillators) and `layers.cell_drive`
(R2-4088, one line shaft) are both gone. What replaces them is built the way
`audio/controls/synth.assembly_cell` is built — **from the same theory and not
from its code**, because G-CONSTRUCT forbids the render path importing the
control corpus and checks it.

An assembly cell radiates **events**. Every sound in one is a contact, a valve
or a move that starts and stops, and the two things that separate it from a
hair dryer are both in the envelope: the events are dense, and between them
there is less. There is no continuous voice in a machine shop at all.

* **45 traverses**, on the picture's own move list — fifteen presentation
  windows out of `docs/beat_sheet.json` (0.50 s to 3.21 s, on no grid) and
  fifteen withdrawals. Position is a smoothstep, so the commanded rate is zero
  at both ends and the drive's every line — Maxwell radial force at 2·p·shaft,
  slot passing at N_z·shaft, pinion mesh at z·v/πd — is a multiple of a rate
  that is changing.
* **90 pneumatic exhausts** — Lighthill scaling, peak at Strouhal 0.2, f² up
  and f⁻² down, with the plenum's own Helmholtz resonance. The peak moves with
  the orifice, so no two stations print the same spectrum.
* **90 latch strikes** — Hertzian contact into a clamp collar's thin-ring
  flexural modes, ratios 1 : 2.83 : 5.42 : 8.73. Not small integers, so a
  struck collar is not a note.
* **15 nut runners**, 228 pawl impacts — 19–44 Hz, an order of magnitude below
  the 80 Hz floor G-SUSTAIN tracks.
* **one rolling bed** at 3 % of the event RMS, the only continuous term.

**THE ONE NUMBER THAT MAKES A GLIDE SAFE, AND IT IS ARITHMETIC.** A smoothstep
rate is inside ±25 cents of its own peak over 0.120 of the move, so a move holds
a pitch for G-SUSTAIN's 0.6 s only if it lasts **5.0 s**. Every move is capped
at 3.4 s and the margin is reported per render, not asserted.

**AND THE PHYSICS THAT MAKES IT SAFER.** What a servo axis radiates is its
torque ripple, and torque is J·α + friction: largest while accelerating,
smallest while coasting. A smoothstep's acceleration is exactly zero at
mid-move — which is exactly where its rate is stationary. **The one instant this
voice holds a pitch is the one instant it is quietest, by physics rather than by
an envelope drawn to beat a gate.**

Measured, cell alone: **note 0.000, chord 0.000, held power 0.0000** — C9's own
numbers, on every version tried.

---

## R2-4144 — FOUR PREDICTIONS, THREE WRONG, AND WHAT EACH ONE TAUGHT

### WRONG — the drag chain. `tools/r2_4141_chain_sweep.py`

Every gantry carries its cables in an articulated energy chain; each link rolls
through the bend radius and drops on its stop, so a 50 mm pitch at 1–5 m/s
articulates at 20–100 Hz. It was added because *a moving machine is a train of
contacts, not a tone with an envelope on it*, and it should therefore have moved
the cell's local dynamic range toward the control's.

| chain : drive | 0 | 0.1 | 0.2 | 0.35 | 0.6 | 0.85 |
|---|---:|---:|---:|---:|---:|---:|
| cell G-EVENT (dB) | **11.95** | 11.75 | 11.35 | 10.65 | 9.27 | 8.35 |

**Monotonically harmful, at every level.** The reason is the rate: G-EVENT's
short-term level is a 20 ms window, and at 20–100 Hz every such window already
contains between half an articulation and two. A train that dense does not make
the level fluctuate — **it fills the troughs**, which is what a hair dryer does,
reached from the opposite direction. **Density in events and density in the
envelope are not the same quantity.** The voice was removed and now lives in the
bench that rejected it.

### WRONG — the descent move. It was the metronome.

The first build gave each cluster a 1.55 s descent traverse `FLIGHT_S` before
its own seat. Beat 1's twelve seat times are a perfect 1.045 s ladder, so that
is **fifteen identically-shaped swells starting 1.045 s apart — which is
literally control C6**, a jittered metronome of identical gestures. Measured on
the sum: G-NOVEL r = **0.615 at lag 1.040 s** against a 0.15 bar, and G-MOD
23.95 dB against the impacts' own 11.18.

The repair is also the physics: **`cluster_arrivals`, which every impact in this
beat is built from, drops each part under gravity at t = √(2h/g).** A gantry
lowering each cluster at a commanded feed contradicts the layer standing next to
it. The arm releases; gravity does the rest. The descent traverse is gone and
what remains at that instant is the gripper — one blow-off, one detent.

### WRONG — that the release events were then the metronome.

They were not, and dropping them entirely changed **nothing**:

| at CELL_GAIN 0.012 | G-NOVEL r | at lag |
|---|---:|---:|
| release as scheduled | 0.558 | 1.040 |
| release dropped entirely | 0.558 | 1.040 |
| release scattered 0.45 s | 0.557 | 1.040 |
| release scattered 0.90 s | 0.557 | 1.040 |

### THE MEASUREMENT THAT EXPLAINED ALL THREE — G-NOVEL AT BEAT 1 IS THE PICTURE

The part impacts alone score r = **0.000**, "no prominent local maximum: no
period, only trend", and that looks like proof the ladder is inaudible. **It is
proof that the gaps are empty.** With nothing between the seats, the per-band
normalised log-spectrum envelope in the gaps is numerical floor rather than
signal, and there is nothing for the seats to correlate against. Put **anything**
in the gaps at one level and the ladder becomes legible:

| added to the film's own impacts, all at the same RMS | G-NOVEL r | at lag |
|---|---:|---:|
| nothing | **0.000** | — |
| **this cell** | **0.578** | 1.040 |
| band-limited noise | 0.610 | 1.040 |
| white noise | 0.652 | 1.040 |
| **a sustained tone** | **0.756** | 1.050 |

**The cell is the lowest of the four, and a drone is the worst.** There is no
fill that scores better than leaving beat 1 empty, and leaving beat 1 empty is
the master the client rejected as *"The Tubes over and over"*. **G-NOVEL at beat
1 is a PICTURE failure in the same sense G-MOD is** — R2-4080's ruling, the
client's decision — and this pass does not chase it, because chasing it means
either silence or a drone and both have been delivered and rejected.

**No threshold was moved.** The gate is correct; what it is reading is the
1.0417 s seat ladder, and the ladder is in the delivered 4K frames.

### RIGHT, AND ONLY BECAUSE IT WAS ATTRIBUTED FIRST — the missing mass law

G-RING **passed on the impacts alone and passed on the cell alone**, and the sum
failed it: a 1/6-octave band at 5702 Hz decaying 1.75 s against a 1.02 s
broadband. `tools/r2_4141_ring_attrib.py` takes the voices out one at a time —
not the valves, not the latches, not the runners, not the bed. The traverse.

A radial force does not become sound in the air gap; it becomes sound by driving
the structure it is bolted to, and **above that structure's first resonance the
response of a mass-controlled body to a force falls as 1/f²**. That is the mass
law and it was simply missing: the 14th force order at peak feed sat in the mid
kilohertz at full amplitude/14 and was held there for the length of every move.
G-RING is right to call that an under-damped isolated mode — a band that never
decays because it is still being driven. With the law applied, **G-RING passes
on the sum.**

---

## R2-4145 — `CELL_GAIN`, BRACKETED ON BOTH SIDES. `tools/r2_4141_gain_sweep.py`

The cell's level is not a taste knob and it is not a bar being chased. Too quiet
and beat 1's first 9.9 s and last 11.6 s go back to being empty. Too loud and
**two things fail at once and they are the same physical fact**: G-EVENT's local
dynamic range falls because a filled gap is a raised p5, and G-RING's broadband
decay stops being *measurable at all*, because ISO 3382's T20 needs the level to
fall 12 dB inside the gap and it cannot fall 12 dB into a floor that is 10 dB
down.

| CELL_GAIN | 0.008 | 0.012 | 0.016 | 0.022 | 0.030 |
|---|---:|---:|---:|---:|---:|
| G-EVENT (dB) | **23.40** | 13.51 | 13.48 | 13.27 | 12.98 |
| G-RING broadband T60 (s) | **0.8967** | nan | nan | nan | nan |
| G-RING ratio | **1.292** | — | — | — | — |

**A limb that goes from a number to `nan` is not a pass — it is a limb that has
gone blind**, and this pass walked into exactly that once: the mass-law fix
moved G-RING from 1.71× FAIL to a "PASS" whose broadband T60 was `nan`. The
sweep exists because of that mistake. **0.008 is the loud side of the cliff.**

---

## R2-4146 — THE LAYER, AGAINST THE CORPUS

`tools/r2_4141_cell_bench.py --parts --gates --control`:

| | note | chord | held power | G-EVENT dB |
|---|---:|---:|---:|---:|
| bar | ≤0.20 | ≤0.05 | ≤0.15 | ≥13.7 |
| **C9 assembly cell (positive)** | 0.000 | 0.000 | 0.0000 | 37.38 |
| the part impacts alone | 0.060 | 0.000 | 0.0176 | 27.17 |
| the cell alone | **0.000** | **0.000** | **0.0000** | 10.62 |
| **the shipped layer** | **0.021** | **0.000** | **0.0002** | **23.40** |

Every master-level gate that applies at beat 1, run on the layer (which is
0.9345 of beat 1's stem power):

| gate | verdict | what it is |
|---|---|---|
| **G-SUSTAIN** | **PASS** | the gate this rebuild exists to satisfy |
| **G-EVENT** | **PASS** | 23.40 dB, inside C9's own 21.4–37.4 range |
| **G-GESTURE** | **PASS** | |
| **G-RING** | **PASS** | was FAIL until the mass law landed |
| G-MOD | FAIL | **picture**: the 1.0417 s ladder, R2-4080, client ruled |
| G-NOVEL | FAIL | **picture**: the same ladder — see R2-4144 |
| G-ROOM (c) | FAIL | **instrument**: the two bars sit below their own nulls |

**The cell alone reads 10.62 dB on G-EVENT and that is stated rather than
hidden.** It is 1.8 dB over the loudest negative in the corpus and 5.9 dB over
the hair dryer, and it is below the bar. G-EVENT is a **beat** gate on the
master; a bed is not a beat, and judging one by the other is the category error
R2-4084 spent a whole pass correcting. What is judged — beat 1, which is the
impacts and the cell together — reads 23.40 dB.

---

## OPEN, INHERITED AND NOT PAPERED OVER

1. **G-ROOM(c)'s two bars still sit below their own nulls** — 1.5× against a
   10.44× no-delay null, 8.0 dB against a 17.7 dB Rayleigh floor (R2-4085). The
   layer reads 14.36× and 16.45 dB. **16.45 dB is BELOW the 17.7 dB floor**, so
   the ripple limb is failing material that is quieter than a diffuse field.
   Nothing here was tuned to it and nothing here should be: R2-4085 measured
   both bars and moved neither, and this pass has no new anchor to offer.
2. **G-MOD and G-NOVEL at beat 1 are one fact, not two.** Whoever re-derives
   either should read R2-4144's table first: every fill scores worse than
   silence, and a drone scores worst of all.
3. **`reflect_garage` −22 → −27 LUFS-S** is carried in from the stopped agent's
   tree with its own derivation and its own prediction that it flips no gate.
   The prediction is checked against this render's stems rather than repeated.
