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

---

## R2-4147 — THE CLIENT: *"now beat 1 i dont hear anything until the tubes play"*

**THE CHEAP EXPLANATION WAS THE WHOLE EXPLANATION, AND IT WAS NEVER MEASURED.**
The cell was not too thin, too smooth or too sparse. **It was 14 dB below the
threshold of hearing.**

`tools/r2_4147_audible.py`, on the delivered `PART2_AUDIO_MASTER_R2-4141.wav`,
at EBU R 128 playback less 12 dB for domestic listening:

| beat 1, between the impacts | measured |
|---|---:|
| broadband SPL | **26.4 dB SPL** |
| loudest third-octave, re: threshold in an NR-25 room | **−13.99 dB** |
| third-octave bands above threshold | **0 of 29** |
| re: threshold in quiet (anechoic, no room) | +5.20 dB |

**Zero bands clear threshold.** A quiet living room's own noise floor is
~15 dB louder than the cell. The client did not mishear it; there was nothing
there to hear. The LUFS-S trace says the same thing in one line: the beat's
cell-only stretches read **−60 LUFS-S against a −23 LUFS programme — 37 LU
down**, and the seat ladder reads −25 to −35.

---

### R2-4147(1) — THE GATE THAT CAUSED IT, AND THE MEASUREMENT THAT PROVES IT

`percept.local_dynamic_range` spans p95 − p5 of the 20 ms level. **Its p95 is an
impact and its p5 is whatever lies between them, so the cheapest way to maximise
it is to put NOTHING between them.** `tools/r2_4147_event_diag.py` — the film's
own 777 part impacts, one filler varied, fillers at matched level:

| beat 1 = impacts + | G-EVENT dB | AMI | AUDIBLE dB |
|---|---:|---:|---:|
| **NOTHING (what R2-4141 shipped)** | **27.17** | 0.8037 | **−140.71** |
| the cell, audible | 12.62 → **FAIL** | 0.8179 | +14.56 |
| a hair dryer | 5.48 | 0.3309 | audible |
| a drone | 0.26 | 0.1807 | audible |

**Silence is G-EVENT's best score, 13.5 dB clear of the bar, and an audible
machine fails it.** R2-4145's CELL_GAIN bracket was walking downhill toward an
empty beat and it arrived. R2-4144's drag-chain rejection — "monotonically
harmful at every level" — is the same artefact.

**No threshold was moved.** G-EVENT is not retired and is not wrong about hair
dryers; it measures TROUGH DEPTH, and trough depth is not eventfulness.

---

### R2-4147(2) — G-PRESENCE: THE INSTRUMENT THE SUITE NEVER HAD

Every quality gate in `percept.py` is RELATIVE — it measures structure *within*
whatever it is handed — so **digital silence scores perfectly on all of them.**
G-PRESENCE is the first absolute measurement in the file. Two limbs, and the
measurement above is why there are two:

* **AUDIBLE** — sensation level of the material *between* the events, in dB over
  the greater of the ISO 226 threshold in quiet and an **NR-25** room (ISO
  R 1996; the *quiet* end of ISO/ANSI's domestic range, chosen so the bar cannot
  flatter itself), at R 128 reference less 12 dB. **Bar 0 dB — the definition of
  audible, not a tuned number.**
* **AMI**, articulation modulation index — the envelope's 4–100 Hz RMS over its
  mean; 100 Hz is the roughness boundary above which a train stops being events
  and becomes timbre. Level-invariant. **Bar 0.50, control-derived and placed
  UNDER the loudest negative rather than at the midpoint, because this corpus
  has exactly one beat-1 positive and a midpoint bar would be drawn through a
  single point.**

**Neither limb alone is sufficient and that is the point:** silence has the
second-best AMI in the table above and is inaudible; the hair dryer is plainly
audible and has the worst AMI but one. A composite score could be traded between
them; two limbs cannot.

| | verdict | sens dB | bands | AMI |
|---|---|---:|---:|---:|
| **R2-4141 shipped master — the complaint** | **FAIL** | −13.99 | 0 | 0.8260 |
| 33 s of digital silence | **FAIL** | — | — | — |
| a silent beat 1 inside a loud programme | **FAIL** | −238.08 | 0 | — |
| C4 `master.wav`, "a hair blower" | **FAIL** | +16.70 | 16 | 0.4225 |
| C1 octave-matched noise | **FAIL** | +25.73 | 19 | 0.2823 |
| C8b the drone | **FAIL** | +38.77 | 9 | 0.0364 |
| **C9 assembly cell (positive)** | **PASS** | +7.20 | 4 | **1.4835** |

**TWO BUGS IN THIS GATE WERE FOUND BY ITS OWN CONTROLS AND ARE WORTH MORE THAN
THE GATE.** The first version returned **INAPPLICABLE** for C1, C8b *and 33 s of
digital silence* — the three signals it exists to fail:

1. **The event mask went blind on stationary material.** With only a "within
   12 dB of p98" test, a signal with no dynamics has every frame inside 12 dB of
   its own top, so the whole passage reads EVENT and there is no gap left to
   measure. Fixed by requiring a frame to be **both** near the p98 **and** 6 dB
   over the passage's median. A hair dryer is now correctly **all gap** — it has
   no events — and is judged on whether that material is articulated.
2. **A silent programme returned INAPPLICABLE from the calibration guard**,
   because `loudness_lufs` returns −inf and −inf was treated as "no calibration
   supplied" rather than as "measured, and there is nothing here".

**A gate that goes blind on its own negative controls is the exact failure this
file already documents twice** (G-HNR at beat 1, G-RING's `nan` broadband). It
was caught only because the controls were run before the gate was believed.

---

### R2-4147(3) — THE FIX IS STRUCTURAL. LOUDER WAS MEASURED AND IT WAS NOT ENOUGH.

Raising `CELL_GAIN` alone reproduces failure mode #1. On the R2-4141 cell:

| CELL_GAIN | 0.008 | 0.030 | 0.050 | 0.075 | 0.120 |
|---|---:|---:|---:|---:|---:|
| AUDIBLE dB | −5.63 | +5.82 | +10.21 | +13.62 | +16.79 |
| **AMI** | 0.7710 | 0.6895 | 0.6273 | **0.5650** | **0.4868** |

**At the level that makes it audible the old cell becomes a wash** — AMI 0.487
is between blower-into-tubes and the hair dryer. **The bracket for that
architecture was genuinely EMPTY**, and saying so is the result.

**WHY, IN ONE NUMBER.** Six real moves, concatenated:

| | AMI |
|---|---:|
| **`servo_traverse` as it shipped — the drive's order set** | **0.2831** |
| **C1, the literal hair dryer** | **0.2823** |
| the drag chain alone | 1.3711 |
| C9, the positive control | 1.4835 |

**The cell's dominant voice was a hair dryer to three decimal places.** R2-4144
added the chain at 0.1–0.85 of it and measured no benefit — correct, and for a
reason it did not name: it was adding a machine as a *garnish* to a stationary
voice five times louder. **The balance is inverted here, not nudged**, and the
physics agrees: a servo's radial force acts on a heavy stiff stator whose
displacement is microns (the mass law, already coded, already the thing that
fixed G-RING), while a cable chain is links undergoing real momentum changes
against stops every 50 mm of travel.

**AND THE CELL ONLY EXISTED WHILE A CLUSTER WAS MOVING.** Every voice was bound
to one of fifteen clusters, so outside the picture's 9.9–21.3 s presentation
window the layer had nothing scheduled at all — 67.5 % of the beat was gap
against the positive control's 10.4 %. `staging_train` is the rest of the
machine, and **its rate is arithmetic off the picture**: 616 parts / 33.0 s =
**18.7 staging operations per second**, two Hertzian contacts each, running the
whole beat because a stager runs ahead of a presenter.

**THE DAMPING IS THE DIFFERENCE BETWEEN A RATTLE AND A WASH, AND THIS FILE
ALREADY HELD THE RIGHT NUMBER.** `_ring_from`'s own docstring: eta reaches 0.15
for a *mass-loaded, gasketed clamp* — and a locating nest with a part sitting on
it is exactly that. The mean gap between contacts is 27 ms:

| nest eta | 0.012 | 0.050 | 0.100 | 0.150 |
|---|---:|---:|---:|---:|
| T60 at 2 kHz | 29 ms | 7 ms | 3.5 ms | 2.3 ms |
| staging AMI | **0.5998** | 1.2418 | **1.5836** | 1.8060 |

At eta 0.012 the rings are **longer than the gap between them** and the train
fills in — **the drag-chain failure, reached a third time by a different route.**
At 0.10 it is above the positive control.

---

### R2-4147(4) — WHAT SHIPS, AND THE PREDICTION THAT WAS WRONG

`CELL_GAIN` 0.008 → **0.075**, `STAGING_RATIO` **2.5**, `STAGING_ETA_NEST`
**0.10**, `DRIVE_TO_CHAIN` **0.30**, the drag chain restored as the traverse's
primary voice.

**THE WARNING FROM THE AGENT THAT BUILT `cell_events` WAS THAT 9.4× LOUDER MUST
BREAK G-EVENT AND G-RING. MEASURED, IT DID NOT, AND THE REASON IS THAT THE FIX
WAS STRUCTURAL:**

| beat-1 layer | R2-4141 | **R2-4147** |
|---|---:|---:|
| G-EVENT LDR | 23.40 dB PASS | **20.26 dB PASS** |
| G-SUSTAIN note / chord / held | 0.021 / 0.000 / 0.0002 | **0.000 / 0.000 / 0.0000** |
| G-ROOM | FAIL | **PASS** |
| G-NOVEL r at 1.04 s | 0.578 | **0.382** |
| gap sensation level | −13.99 dB | **+14.56 dB** |

**A cell nine times louder passes G-EVENT by 6.6 dB, because short distinct
events do not fill troughs — only long ones do.**

**THE `nan` CLIFF THAT SET `CELL_GAIN = 0.008` WAS MEASURED ON A SIGNAL WITH NO
ROOM IN IT.** `tools/r2_4141_gain_sweep.py` reads G-RING off `render_parts()`,
which is the **dry** `assembly` layer; the showroom tail is a different bus
(`reflect_showroom`). A dry layer has no room decay to measure, so its broadband
T60 is noise in the region detector — which is why it is `nan` at 0.030 and a
number at 0.050 and 0.075, **non-monotonic in the quantity it was read as a
cliff in.** On the delivered master, where the tail is present, beat 1 gives 30
bands and 4 decay regions at the shipped level. G-RING's Sabine limb also still
runs when the broadband is `nan`; only the isolated-mode ratio is skipped.

---

### R2-4147(5) — SECONDARY: `wet_hf_hz`. **DO NOT IMPLEMENT IT TO HIT 0.35 s.**

`wet_hf_hz=4000.0` is in `dsp.fdn_reverb`'s signature and in no line of its
body. The per-line damping is a one-pole whose coefficient is chosen to make the
**Nyquist** gain right, so its corner lands wherever that puts it. Measured on
the 6.5 m line at the shipped settings:

| | 250 Hz | 1 kHz | **4 kHz** | 8 kHz | 16 kHz | Nyquist |
|---|---:|---:|---:|---:|---:|---:|
| delivered RT60 | 2.39 s | 2.22 s | **1.10 s** | 0.50 s | 0.25 s | 0.21 s |

Declared: 2.4 s low, **0.35 s above 4 kHz**. The crossover is an octave and a
half too high and it **overshoots** past 12 kHz.

**BUT THE DECLARED TARGET IS THE THING THAT IS WRONG.** Sabine with ISO 9613 air
absorption, on the showroom's own 4290 m³ / 1996 m²:

| RT60 at 4 kHz | surface alpha it demands |
|---|---:|
| **0.35 s (declared)** | **0.967 — anechoic-grade, impossible** |
| 0.805 s (measured, R2-4141) | 0.408 — an ordinary treated showroom |
| 2.4 s (declared low) | 0.122 — consistent with the code's own 0.144 |

**The network is already delivering a physically correct high-frequency decay
and the declaration is the error.** That also explains the previous prediction
failure: a shelf built to chase 0.35 s lengthened the tail because it was
chasing a number that should not be chased.

**NOTHING IN THE REVERB WAS CHANGED IN THIS PASS**, deliberately: the correct
fix is to change a *declaration*, which changes the room under every beat, and
it must not be confounded with a beat-1 A/B the client is being asked to judge.
It needs its own pass and its own listen.

---

## R2-4148 — THE RENDER, AND WHAT IT COST

`audio/out/r2_4147/master_R2-4147.wav`, -23.00 LUFS / -1.12 dBTP, limiter GR
-0.85 dB, `AUDIO_MASTER_OK`. `tools/percept_matrix.py` returns
**`PERCEPT_MATRIX_OK`** — 40 thresholds, **0 provenance violations**, every
control got its required verdict, every mutation fired. **G-CONSTRUCT is
unchanged at 17 pre-existing violations and none of them are in the new code.**

| beat 1, at MASTER level | R2-4141 | **R2-4147** |
|---|---:|---:|
| **G-PRESENCE** | **FAIL** −13.99 dB, 0 bands | **PASS** +9.24 dB, 7 bands |
| **G-SUSTAIN** note cover | **FAIL 0.2075** | **PASS 0.0453** |
| G-EVENT | PASS 14.69 dB | **PASS 14.93 dB** |
| G-NOVEL r at 1.04 s | FAIL 0.549 | FAIL **0.413** |
| G-MOD | FAIL 12.14 dB | FAIL 12.16 dB |
| G-RING | **FAIL, ratio 1.529** | **INAPPLICABLE** |
| the seat ladder's own RMS | −30.99 dBFS | **−31.01 dBFS** |

**G-SUSTAIN AT BEAT 1 WAS FAILING ON THE SHIPPED MASTER AND THE LAYER BENCH SAID
IT PASSED.** R2-4146 read G-SUSTAIN off the dry `assembly` layer, which measures
0.000; the MASTER measures 0.2075 against a 0.20 bar, from partials in the room
tail that the layer bench cannot see. The gate this entire rebuild exists to
satisfy was red on the delivered file and the bench was pointed away from it.

---

### THE COST, AND IT IS THE ONE THE PREVIOUS AGENT PREDICTED

**G-RING's beat-1 measurement is gone.** 4 usable decay regions → 2 →
INAPPLICABLE. **That warning was correct and it is recorded as correct.** Three
things bound it:

1. It was **already FAILING** at beat 1 (1.529 against 1.5). A failing
   measurement became an absent one; a passing one was not broken.
2. **The reverb was not touched** — no line of `showroom_tail` or `fdn_reverb`
   changed, so the room is the same room. What was lost is the ability to read
   it off the master's beat 1, not the room's correctness.
3. G-RING still measures and still fails at `5_lap` (14 regions), so the gate is
   not blind.

**It is still a real loss of coverage and it is not written off.** You cannot
measure ISO 3382 T20 in an operating factory: the standard needs a 12 dB fall
into a gap, and an audible machine is what is in the gap. The remedy is to
measure the room from a source with no machine in it, and the obvious candidate
— the `reflect_showroom` stem — **does not work either**: it is wet-only and
continuous, so `decay_regions` finds ZERO regions in it, on R2-4141's stems as
well as R2-4147's. **The room needs a dedicated impulse-response measurement
rather than a stolen gap.** OPEN.

---

### THE OTHER NEW FAILURE, AND WHY IT IS NOT ACTED ON

**G-PRESENCE FAILS AT `3_breach`** — AMI 0.1409, on the density limb. It is
reported and it is deliberately not chased, for a reason that is about the
instrument and not about the beat: **the AMI bar is control-derived from a corpus
whose only positive is C9, and C9 is a BEAT-1 control.** The breach's
between-event material is a decaying tail plus a debris bed, and a decaying tail
has a smooth envelope by definition. Whether 0.1409 is a defect or the
instrument reaching past its validation needs a breach-beat positive control,
which this corpus does not have. **Adjusting the gate's scope to make the
failure disappear would be the exact behaviour this file forbids**, so it stands
as a red flag with a stated caveat. OPEN.

---

### DELIVERY

Both films re-muxed `-c:v copy`, **video stream md5 verified byte-identical**:
ProRes `c346a7a322a4a2a403727c1e85f17511`, H.265
`235ef36e844a62b0e303e4138907b9fa`. 124.083333 s in both, unchanged.
`watch/INDEX.md` updated; `watch/listen_2026-08-14/` re-cut with **NEW =
R2-4147, OLD = R2-4141** so the A/B is pointed at the complaint itself rather
than at a two-rejections-old negative; `CLIPS_OF.json` accurate.
`audio/out/master.wav` and `watch/rejected_audio_R2-4079/` are untouched and
both still fail.

**PREDICTIONS MADE IN THIS PASS THAT WERE WRONG:**

1. **That the staging train would raise the layer's density on its own.** It
   lowered it — cell AMI 0.4101 → 0.3558 — because at eta 0.012 the nest rings
   were longer than the gaps between contacts. Diagnosed only because the voice
   was measured alone before being believed.
2. **That `STAGING_RATIO` was a distance.** It is a work-rate ratio and the
   answer is above 1, not below it; 0.55 was not enough and the curve says so.
3. **That the drag chain needed to be re-added at R2-4144's levels.** At
   0.1-0.85 of the drive it changes nothing, because the drive was the louder
   voice AND the wrong one. It had to become the primary voice.
4. **That a new gate would be right because its controls were chosen carefully.**
   The first version of G-PRESENCE returned INAPPLICABLE for the hair dryer, the
   drone AND 33 s of digital silence. It was caught by running the controls
   before believing the gate, which is the only reason this entry is not another
   rejection.

---

## R2-4149 — THE THREE ITEMS R2-4148 LEFT OPEN, CLOSED BY MEASUREMENT

Beat 1 is not re-opened. What is closed here is the three things the pass that
fixed it wrote down as OPEN: the reverb declaration, G-RING's lost beat-1
measurement, and G-PRESENCE's failure at the breach.

**THE HEADLINE IS THAT TWO OF THE THREE END IN NO CHANGE TO THE AUDIO AND THE
THIRD ENDS IN NO CHANGE TO A BAR**, and every one of those non-changes is a
measurement rather than a shrug. Four predictions in this pass were wrong and
they are all here.

---

### R2-4149(1) — THE REVERB: THE DECLARATION WAS THE DEFECT AND THE NETWORK WAS ALREADY A ROOM

`tools/r2_4149_room_hf.py` derives the room's own high-frequency decay in the
shape this design already declares it in — ONE surface absorption, from the
Sabine reference that is already in `percept.SHOWROOM_*` and in
`layers.showroom_tail`'s own Sabine line — **with air accounted for separately,
because air is not a surface**:

    RT60(f) = 0.161 V / (S*alpha + 4 m(f) V),   m from ISO 9613-1

V = 4290 m3, S = 1996 m2, and the declared 2.4 s low-frequency RT60 backs out
**alpha = 0.1416** once the 250 Hz air term is credited.

| f | 125 | 250 | 1 k | 2 k | **4 k** | 8 k | 16 k | 24 k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ISO 9613 air, dB/m | 0.0004 | 0.0013 | 0.0047 | 0.0099 | **0.0297** | 0.1053 | 0.3645 | 0.6901 |
| 4mV, against S*alpha = 283 | 1.7 | 5.2 | 18.4 | 39.1 | **117** | 416 | 1440 | 2727 |
| **target RT60, s** | 2.43 | 2.40 | 2.29 | 2.15 | **1.73** | 0.99 | 0.40 | 0.23 |

**THE DOCSTRING'S OWN AIR FIGURE WAS WRONG TOO.** `showroom_tail` said "ISO
9613 alpha at 4 kHz is ~0.011 dB/m". The closed form at 20 C / 50 % RH /
101.325 kPa gives **0.0297 dB/m**; 0.011 is roughly the 2 kHz value. Above
6 kHz **the air IS the room** — 416 absorption units against the surfaces' 283.

**AND THEN THE MEASUREMENT SAID THE NETWORK WAS ALREADY RIGHT.** On
`dsp.fdn_reverb`'s own impulse response, at the render's own 96 kHz:

| f | 250 | 1 k | 2 k | **4 k** | 8 k | 11.3 k | 16 k | 20 k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| delivered T60, s | 2.48 | 2.28 | 1.81 | **1.27** | 0.92 | 0.81 | 0.79 | 0.84 |
| target, s | 2.40 | 2.29 | 2.15 | **1.73** | 0.99 | 0.65 | 0.40 | 0.29 |
| **surface alpha it implies** | 0.135 | 0.157 | 0.171 | **0.213** | 0.169 | 0.034 | **−0.285** | **−0.640** |

Log-RMS error against the physical room over 250 Hz – 16 kHz: **0.184**, i.e.
20 % in T60, against a 25 % tolerance G-RING already writes down for this same
estimator. **The implied surface absorption rises 0.14 → 0.21 from 125 Hz to
9 kHz, which is what ordinary porous treatment does.** From 125 Hz to 9 kHz
this network is a physically realisable room and the sentence next to it was
the only thing that was not.

**WRONG PREDICTION #1, AND IT NEARLY BECAME A CONCLUSION.** The first run of
this bench was at 48 kHz, because that is the delivered file's rate. **The FDN
runs at `sr_internal` = 96 kHz.** At 48 kHz the same code reads 0.90 s at 4 kHz
and a log-RMS of 0.379; at 96 kHz it reads 1.27 s and 0.184. `rt60_high` is a
NYQUIST target, so halving Nyquist moves the whole curve — and a conclusion was
one command away from being drawn about a sample rate this film is not
rendered at.

**`wet_hf_hz` IS DELETED FROM `dsp.fdn_reverb`'s SIGNATURE, NOT IMPLEMENTED.**
The reason is physics and not tidiness: **a room has no crossover frequency.**
Sabine-with-air is smooth and has no corner anywhere, so a parameter naming a
corner asserts a shelf that must not exist — which is exactly why the one time
this project built that shelf it LENGTHENED the tail. The declaration in
`showroom_tail` is replaced by the curve above.

**`rt60_high` IS NOT CHANGED, AND THAT DECISION WAS RENDERED RATHER THAN
ARGUED** — see R2-4149(5).

---

### R2-4149(2) — WHERE THIS NETWORK STOPS BEING A ROOM, AND IT IS NOT THE DAMPER

Above about 11 kHz the delivered tail implies a **NEGATIVE surface
absorption** — it rings longer than a hall with perfectly reflective walls
could, once air is credited. That is not a declaration problem and no
`rt60_high` can fix it.

**WRONG PREDICTION #2: that this was the one-pole damper overshooting.** It is
the DIFFUSER. The eight-stage allpass chain in front of the network has its own
energy decay, it is frequency-FLAT because an allpass is, and it is measured:

| the diffuser's own IR | broadband | 1 kHz | 4 kHz | 16 kHz |
|---|---:|---:|---:|---:|
| T60, s | **0.777** | 0.659 | 0.765 | 0.861 |

Its longest stage alone — 35.93 ms at g = 0.70 — is 0.696 s. **A tail cannot
decay faster than the burst that excites it.** With `n_diffusion=0` the same
network runs monotonically to 0.24 s at 20 kHz; with the diffuser in, no
`rt60_high` from 0.10 to 0.45 s moves the 16 kHz band off 0.79 ± 0.02 s.

It is **declared and bounded, and deliberately not fixed**: the only levers are
a shorter span or a lower g, and R2-4079 measured that lowering g makes the
cepstral ripple **monotonically worse** — which is the metallic-diffuser defect
a master was rejected for. Trading a rejected defect for an inaudible one above
11 kHz is not a trade. **OPEN, with the number.**

---

### R2-4149(3) — G-RING AT BEAT 1: THE MEASUREMENT WAS NOT THERE TO LOSE

`tools/r2_4149_ring_cover.py`, on the delivered master's beat 1:

| beat 1, broadband envelope | R2-4147 | R2-4141 | `master.wav` (negative) |
|---|---:|---:|---:|
| prominent peaks in 33 s | 54 | 21 | 23 |
| median gap between them, s | **0.420** | 0.990 | 1.205 |
| peaks with the 12 dB ISO 3382 needs | 15 of 54 | 13 of 21 | 11 of 23 |
| **the envelope keeps FALLING for, median s** | **0.040** | 0.150 | 0.085 |
| longest continuous fall, s | **0.650** | 0.650 | 1.165 |
| usable decay regions (needs 3) | **2** | 4 | 4 |

**WRONG PREDICTION #3: that per-band region detection would restore coverage.**
`decay_regions` finds gaps in the BROADBAND envelope and every 1/6-octave band
is then read inside those same gaps, which is not what ISO 3382 does — a band
should be measured in its own gap. Implemented with the identical rules (6 dB
prominence, 0.30 s minimum, 3 dB stop), it made things **worse**: 5 bands with
a measurable T60 against the 18 the broadband gaps already yield, because a
1/6-octave envelope's own Rayleigh fluctuation trips the 3 dB stop rule almost
immediately. Recorded, not shipped.

**AND THEN THE CONTROL THIS GATE NEVER HAD SAID SOMETHING WORSE.**
`tools/r2_4149_ring_control.py` — impacts convolved with an exponential IR
whose T60 is **declared** and which is frequency-INDEPENDENT by construction,
so the truthful `worst/broadband` is 1.0 and the truthful T60 is the exponent:

| a KNOWN 2.4 s room, no floor | gap 4.0 s | 2.0 s | 1.5 s | 1.0 s | 0.60 s | **0.42 s** |
|---|---:|---:|---:|---:|---:|---:|
| median T60 returned, s | 2.389 | 2.388 | 2.387 | 2.169 | 1.457 | **0.985** |
| as a fraction of the truth | 0.995 | 0.995 | **0.994** | 0.904 | 0.607 | **0.410** |
| worst / broadband | 1.119 | 1.119 | 1.121 | 1.152 | 1.308 | **1.882** |

| a KNOWN 2.4 s room, 1.5 s gaps | no floor | −60 dB | −50 dB | −40 dB | −35 dB |
|---|---:|---:|---:|---:|---:|
| median T60 returned, s | 2.387 | 2.455 | 3.085 | **4.550** | — |
| as a fraction of the truth | 0.994 | 1.023 | 1.285 | **1.896** | — |

**THREE FACTS, AND NONE OF THEM WAS KNOWN BEFORE THIS PASS:**

1. **THE ESTIMATOR IS EXCELLENT WHERE IT IS APPLICABLE** — 0.994 of a known
   truth with gaps ≥ 1.5 s and a quiet floor. Nothing in this project had ever
   fed it a decay whose T60 was known.
2. **BEAT 1 IS NOT IN THAT REGIME AND CANNOT BE.** Its longest continuous fall
   is 0.650 s; a 2.4 s room needs 1.00 s just to traverse T20's −5 to −25 dB
   window and ≥ 1.5 s for the estimator to return the truth. At beat 1's own
   0.42 s gaps the estimator returns **0.41 of a known truth.** **BEAT 1
   GENUINELY HAS NO MEASURABLE DECAY, INAPPLICABLE IS THE CORRECT VERDICT, AND
   IT IS NOW CORRECT BY MEASUREMENT RATHER THAN BY ACCIDENT.** What was lost at
   R2-4147 was not a measurement of the room.
3. **G-RING's 1.5× BAR SITS BELOW ITS OWN NULL IN THE SHORT-GAP REGIME** —
   1.882 on a room that is uniform by construction. It is the same shape as
   G-ROOM's two open bars. **THE BAR IS NOT MOVED**; it is declared open at the
   point of use in `percept.py` with the numbers, and nothing was tuned to it.

**AND THE ONE BEAT G-RING STILL MEASURES IS INSIDE THE FLOOR BIAS.** 5_lap has
2.42 s gaps — comfortable — but its broadband envelope p95−p5 is **13.4 dB**,
because an engine is running through all of it. Matched to that geometry, a
**uniform 2.4 s room** reads:

| floor | −inf | −50 dB | −40 dB | −35 dB (env 14.5 dB ≈ the film's 13.4) |
|---|---:|---:|---:|---:|
| median T60 returned, s | 2.389 | 3.045 | 4.619 | **4.904** |
| worst band, s (Sabine bar 3.00 s) | 2.65 | 3.67 | 4.98 | **5.32** |
| worst / broadband (bar 1.50) | 1.119 | 1.250 | 1.048 | **1.029** |

The master's 5_lap reads worst 4.450 s, broadband 2.938 s, **ratio 1.515**.
**The ratio limb SURVIVES its null there** — a uniform room reads 1.03–1.25 at
that geometry and the film reads 1.515, so that FAIL is real and is not
explained away. **The Sabine limb does not**: its null at 5_lap's geometry is
5.32 s against a 3.00 s bar. That limb only runs on interior beats, all of
which are currently INAPPLICABLE, so it is firing nowhere — but a re-derivation
of G-RING now has a two-sided anchor to do it with, which it did not before.

---

### R2-4149(4) — G-PRESENCE AT THE BREACH: THE BAR IS RIGHT AND THE AUDIO IS WRONG

`synth.glass_breach` is the breach-beat positive the corpus did not have: 8 s
of curtain wall coming down, built from the aperture's own geometry (9.6 × 5.6 m
of 12 mm toughened glass) and the fracture mechanics, in the corpus module and
from the theory rather than from the render path's code.

**THE PHYSICS CORRECTION THIS CONTROL FORCED, FOUND BY CHECKING ITS OWN
NUMBERS — WRONG PREDICTION #4.** The first version rang every fragment as a
free plate at `0.0459 c_L h / a²`. That constant is **13.5× too small** —
Leissa's free square plate is `lam² = 13.49`, i.e. `0.6198 c_L h / a²` — and
with it corrected the real result appears: **a 15 mm dice of 12 mm toughened
glass has NO AUDIBLE RESONANCE AT ALL.** Plate theory does not even apply
(a/h = 1.2) and the cube's own lowest elastic mode is a shear mode at
c_s/2a = **113 kHz**. Only fragments above ~80 mm ring inside the audio band.
**The tinkle of toughened glass is not the dice ringing — it is a quarter of a
million Hertzian contacts of 30–70 µs each, high-passed by their own radiation
(ka = 1 at 3.6 kHz for a 15 mm dice), plus the ring of the few large pieces off
the restrained edges.**

`tools/r2_4149_breach_bench.py`, all on the shipped estimator:

| | AMI |
|---|---:|
| **bar** | **0.50** |
| **C10 the shower — the conservative positive, five seeds** | **0.697 – 0.775** |
| the same, with the car-through-the-pane transient | 9.05 – 9.28 |
| the large pieces and mullions alone | 1.314 |
| **the fine dice alone — a wash by the physics** | **0.153** |
| **the film's own `3_breach`** | **0.141** |
| C10 replaced by its own spectrum, stationary (anti-cheat) | 0.371 |

**A GOOD BREACH CLEARS THE BAR BY 55 %, SO THE BAR IS NOT WRONG FOR THIS BEAT
AND IT IS NOT MOVED.** The film's 0.1409 is the audio, and the ablation names
the defect precisely: **the film's breach measures like an unaccompanied dice
wash.** What it is missing is the layer a listener can count — the large edge
pieces and the mullions, which read 1.314 on their own.

The envelope statistic says the same thing in one line. Over the whole film:

| beat | 1_assembly | 3_breach | 4_transit | 5_lap | 6_ending |
|---|---:|---:|---:|---:|---:|
| AMI | 0.778 | **0.141** | 0.189 | 0.199 | 0.270 |
| envelope p95−p5, dB | 31.7 | **9.9** | 8.9 | 13.8 | 8.7 |
| peak − median, dB | 35.7 | **6.4** | 9.8 | 18.5 | 21.4 |

**In eight seconds of a car going through a glass wall at 53.8 km/h, the
loudest instant is 6.4 dB over the median.** Beat 1 is 35.7.

**AMI's OWN HOLE, FOUND BY RUNNING THE NULLS BEFORE BELIEVING THE CONTROL.** A
**single impulse in 8 s of digital silence reads 37.13** — 74× the bar and 25×
the C9 positive — because AMI is normalised by a mean that silence drives to
zero. It falls to 1.18 with a floor 80 dB down and to 0.055 at 40 dB. **This is
the same shape as the hole G-EVENT already has** and it is why the car impact
is deliberately NOT in the default control: with it, C10 reads 9.17 and
G-PRESENCE **FAILS its own positive** on the audibility limb (+12.28 → −9.50 dB
gap sensation), because one unlimited transient swamps the beat. G-PRESENCE
judges the material BETWEEN the events; the car through the pane is the event.

**C10 IS A BENCH CONTROL AND IS NOT REGISTERED IN `CONTROLS`, AND THE REASON IS
MEASURED.** Over five seeds it returns a clean overall PASS on three: on two of
them G-GESTURE's worst-pair limb reads 0.812/0.814 against a 0.80 bar — which
is a TRUE property of a glass shower, two similar slabs landing similarly, not
a defect to engineer out — and on one the shower's hard arrival cutoff leaves
the beat's last 2.5 s under threshold. **A control whose required verdict is
PASS cannot be one that passes three runs in five**, and forcing it would be
tuning a control to a corpus. It stands with its numbers printed. **OPEN.**

---

### R2-4149(5) — `rt60_high` 0.35 → 0.45 WAS RENDERED IN FULL AND IS NOT SHIPPED

The declaration is corrected in R2-4149(1) at zero cost, because it is a
sentence. Whether the NUMBER should also move is a different question, it
changes the room under every beat, and it was answered the only way this chain
accepts: `tools/r2_4149_tail_ab.py` patches `layers.showroom_tail` rather than
editing it — so the render path in git is the shipped one at all times — and
the whole film was rendered at 0.45 s and put through `tools/percept_matrix.py`.

**THE PREDICTION, WRITTEN INTO THE TOOL'S DOCSTRING BEFORE THE RENDER STARTED:**
0.45 s makes the 4 kHz tail 22 % longer, and R2-4148 measured that beat 1's
G-SUSTAIN note cover comes from partials IN THE ROOM TAIL rather than from the
assembly layer — so the physics-correct direction should make the gate this
whole rebuild exists to satisfy WORSE, and nothing should improve.

**IT WAS RIGHT, AND IT IS THE FIRST PREDICTION IN THIS PASS THAT WAS.**

| | R2-4147, `rt60_high` 0.35 | the A/B, 0.45 |
|---|---:|---:|
| **G-SUSTAIN beat-1 note cover** (bar 0.20) | **0.0453** | **0.0666** |
| G-SUSTAIN beat-1 longest held note, s | 0.768 | 0.768 |
| G-PRESENCE beat 1: sensation dB / AMI | 9.243 / 0.7776 | 9.207 / 0.7839 |
| G-PRESENCE `3_breach` AMI | 0.1409 | 0.1406 |
| G-RING 5_lap worst / broadband | 1.5148 | 1.5139 |
| G-MOD beat 1, dB | 12.158 | 12.203 |
| G-NOVEL beat 1, lag s | 1.040 | 1.040 |
| every gate's film-level verdict | — | **IDENTICAL, all thirteen** |

`PERCEPT_MATRIX_OK`, 40 thresholds, 0 provenance violations, corpus and
mutations correct on both. **NOT ONE GATE MOVES, AND THE ONE NUMBER THAT MOVES
MATERIALLY MOVES 47 % THE WRONG WAY.** A physics fit improved by five points
inside a 25 % tolerance is not worth a 47 % regression on the beat-1 limb that
four rejections were about. **`rt60_high` STAYS AT 0.35 s.** The render and its
adjudication are kept at `audio/out/r2_4149/` so the next agent does not have
to repeat them.

---

### R2-4149(6) — WHAT SHIPS, AND THE PROOF THAT THE AUDIO DID NOT MOVE

**NO AUDIO CHANGED IN THIS PASS. `PART2_AUDIO_MASTER_R2-4147.wav` IS THE
DELIVERY, UNTOUCHED, AND NEITHER FILM WAS RE-MUXED** — there is nothing to
re-mux, so the ProRes and H.265 video md5s are not merely unchanged, they were
never rewritten. `audio/out/master.wav` and `watch/rejected_audio_R2-4079/`
are untouched and still fail.

What changed is three files, and every change is a declaration, a comment or a
control:

* **`audio/dsp.py`** — `wet_hf_hz` deleted from `fdn_reverb`'s signature (it
  was in no line of its body), with the derivation of why a room has no
  crossover and what `rt60_high` actually controls.
* **`audio/layers.py`** — `showroom_tail`'s declaration replaced by the curve,
  and its wrong 4 kHz air-absorption figure corrected.
* **`audio/percept.py`** — TEXT ONLY, in two `_T` reason strings. **NO
  THRESHOLD VALUE, LIMB, SCOPE OR APPLICABILITY RULE WAS CHANGED ANYWHERE.**
  G-RING's ratio bar carries its measured null; G-PRESENCE's AMI bar carries
  the breach positive that confirms it.
* **`audio/controls/synth.py`** — `glass_breach` added. Not registered in
  `CONTROLS`, so no control's required verdict changes; the seven synthesised
  controls rebuild bit-identically.

**PROVED, NOT ASSERTED.** The signature edit is inert by inspection, which is
not the standard here, so it was measured: `showroom_tail` run on a fixed
excitation at 96 kHz under `git show HEAD:audio/dsp.py` and under the edit
returns **md5 `654a292f5373649baf7df3777915cf36` both ways** — bit-identical.
The shipped master was then re-adjudicated end to end with the edited files.

**FOUR PREDICTIONS IN THIS PASS WERE WRONG:**

1. **That the reverb bench should run at 48 kHz** because that is the delivered
   file's rate. The FDN runs at 96 kHz and `rt60_high` is a Nyquist target, so
   the entire delivered curve moves with it — 4 kHz reads 0.90 s at 48 kHz and
   1.27 s at 96 kHz. A conclusion about the wrong sample rate was one command
   from being written down.
2. **That the top-octave overshoot was the one-pole damper.** It is the
   diffuser's own 0.777 s frequency-flat decay, and no `rt60_high` can reach
   below it.
3. **That per-band decay regions would restore G-RING's beat-1 coverage.**
   They made it worse — 5 measurable bands against 18 — because a 1/6-octave
   envelope's own Rayleigh fluctuation trips the 3 dB stop rule.
4. **That a 15 mm glass dice rings.** Its lowest elastic mode is a shear mode
   at 113 kHz, and the free-plate constant the control was first written with
   was 13.5× too small. Caught by checking the control's own numbers against a
   published case (a 1 m x 6 mm steel plate) before believing it.

**AND THE ONE THAT WAS RIGHT** is the only one that led to a decision: that
making the room physically correct at 4 kHz would cost G-SUSTAIN at beat 1 and
buy nothing. It did, so nothing shipped.

---

## OPEN, AFTER THIS PASS

1. **G-RING's 1.5× ratio bar sits below its own null (1.88×) in the short-gap
   regime**, and its Schroeder estimator OVER-reads by up to 2.06× through an
   inter-event floor and UNDER-reads to 0.41 with gaps under ~0.6× the T60.
   `tools/r2_4149_ring_control.py` is the two-sided anchor a re-derivation
   needs. Nothing was tuned to this bar and nothing should be.
2. **G-RING's Sabine limb is un-anchored where it would fire.** At 5_lap's
   geometry a uniform 2.4 s room reads 5.32 s against a 3.00 s bar. The limb
   only runs on interior beats, which are all INAPPLICABLE, so it fires
   nowhere today — which is exactly why it needs deriving before it does.
3. **`3_breach` is the film's flattest beat and G-PRESENCE is right about it.**
   AMI 0.141 against a control-derived 0.50 that a physics-true breach clears
   at 0.775. Peak−median 6.4 dB in eight seconds of a car going through a
   glass wall. **The missing layer is named: the large edge pieces and the
   mullions, which read 1.314 on their own.** This is the largest un-actioned
   audio defect in the film and it is not a beat-1 problem.
4. **AMI has a hole and so does G-EVENT, and it is the same hole.** A single
   impulse in silence reads 37.13. Both statistics are normalised by something
   silence drives to zero. Neither is exploited by anything in the corpus or
   the film, and both should be bounded when either is next re-derived.
5. **C10 is a bench control, not a corpus control.** Three PASSes in five
   seeds; G-GESTURE's worst-pair limb reads 0.812 on two of them because two
   similar glass slabs landing similarly ARE near-copies. Registering it needs
   either more seeds' worth of evidence or an honest look at whether a
   worst-pair bar means anything for a shower of identical fragments.
6. **The diffuser floors the tail at 0.777 s above ~11 kHz**, where the implied
   surface absorption is negative. Bounded, declared, not traded against
   R2-4079's ripple fix.
7. **G-ROOM(c)'s two bars still sit below their own nulls** (R2-4085,
   R2-4146). Unchanged, and still nothing should be tuned to them.
8. **G-MOD and G-NOVEL at beat 1 remain PICTURE** (R2-4080, R2-4144).


---

## R2-4150 — THE BREACH. THE MODEL THIS PASS INHERITED WAS WRONG, AND SO WAS THE ONE IT REPLACED IT WITH.

R2-4149 left `3_breach` as the film's largest un-actioned audio defect with a
model of it attached:

> **The film is almost entirely fine dice.** It is a uniform wash of tiny
> fragments with nothing large in it. **The breach needs its big pieces.**

That model came from a NUMBER MATCH — the corpus positive's dice-only ablation
reads 0.153 and the film reads 0.141 — and **a number match is not an
attribution.** This pass measured the film instead. Two things are true and
neither is the model:

1. **THE FILM'S BREACH HAS NOTHING BUT BIG PIECES.** `shard_ballistics` was
   producing **351 fragments of median 321 mm with a MINIMUM of 40 mm**. There
   is no fine end in it at all. The inherited diagnosis was exactly inverted.
2. **AND CORRECTING THAT IS WORTH NOTHING TO THE GATE.** Rebuilt on the
   delivered frames' own 3216-fragment fracture, the glass layer moves from
   0.2533 to **0.2223** — the wrong way, inside the noise — and the beat from
   0.1695 to **0.1479**. **THE POPULATION WAS NEVER THE DEFECT.**

**THE DEFECT IS THE ONE THIS FILE HAS NOW DOCUMENTED FOUR TIMES: THE RINGS ARE
LONGER THAN THE GAPS BETWEEN THEM.** The drag chain (R2-4144), the nest at
eta 0.012 (R2-4147), the staging train (R2-4148), and now every fragment of
glass in the breach.

---

### R2-4150(1) — THE ATTRIBUTION. `tools/r2_4150_breach_attrib.py`

Every bus alone over 36–44 s of the shipped stems, its share of the window, and
the sum without it:

| bus | AMI alone | share % | sum without it |
|---|---:|---:|---:|
| **engine** | **0.0686** | **44.73** | **0.1964** |
| shards | 0.2565 | 36.27 | 0.1012 |
| debris | 0.2747 | 12.37 | 0.1553 |
| aperture | 0.3530 | 2.09 | 0.1412 |
| reflect_showroom | 0.2735 | 2.09 | 0.1415 |
| tyres | 0.2108 | 0.83 | 0.1436 |
| impact | 1.2919 | 0.35 | 0.1431 |
| structure | 1.4008 | 0.34 | 0.1491 |
| **the sum** | **0.1421** | 100 | — |

**THE ENGINE IS 44.7 % OF THE BREACH AND READS 0.069.** Eight seconds of film
across the ramp is 1.6 s of world at a clock scale of 0.1537, so what beat 3
contains is a full-throttle power unit **held for eight seconds** — and its bus
reads **−17.79 dBFS RMS there against −30.19 on the flying lap.** The engine is
at its loudest in the whole film during the breach, by 12.4 dB.

---

### R2-4150(2) — THE FEASIBILITY BOUND, MEASURED BEFORE ANYTHING WAS BUILT

The corpus positive's own shower substituted for `shards`+`debris` at the same
delivered energy — an ORACLE glass layer, one that reads 0.7857 alone:

| glass layer \ engine | +0 dB | −6 dB | −12 dB | muted |
|---|---:|---:|---:|---:|
| the film's own shards+debris | 0.1421 | 0.1718 | 0.1876 | 0.1964 |
| **the ORACLE at the same energy** | **0.3031** | 0.4257 | 0.5057 | 0.5549 |
| the ORACLE, +6 dB | 0.4687 | 0.5862 | 0.6460 | 0.6765 |
| the ORACLE, +12 dB | 0.6206 | 0.6970 | 0.7280 | 0.7418 |

**A PERFECT GLASS LAYER CANNOT CLEAR THE 0.50 BAR THROUGH THIS MIX.** It
reaches 0.3031. Leave-one-out with the oracle in place: removing the engine is
worth +0.25 and **every other bus in the beat is worth 0.006 or less.**

That number was obtained before a line of the breach was touched, and it is
what makes this pass's verdict honest rather than disappointed: **the glass was
rebuilt on its own merits, and the residual was known in advance to be the
engine.**

---

### R2-4150(3) — THE GLAZING IS LAMINATED, AND NO LINE OF THE AUDIO HAD READ THAT

`sim/out/fracture_wall.json` — tracked, and the file the delivered frames' crack
pattern came out of — declares the section:

    "glass_makeup": "5 mm HS / 1.5 mm PVB / 5 mm HS laminated",  11.5 mm

**That is a constrained-layer damping sandwich**, which is the entire reason
laminated glazing is specified acoustically. `audio/layers.shard_modes` rang
every fragment of it at **Q = 800–1500, i.e. eta = 0.00067–0.00125 — BELOW the
published internal loss factor of MONOLITHIC float glass.**

`tools/r2_4150_glass_material.py` establishes the correct figure twice, by two
routes that share no assumption, and checks its own arithmetic first:

* **THE ARITHMETIC, AGAINST A PUBLISHED CASE, BEFORE ANY GLASS NUMBER IS
  QUOTED** (R2-4149's hazard note): Leissa's completely-free square plate,
  lambda² = 13.49, on a 1.000 m × 6 mm steel plate returns **19.68 Hz against a
  published 19.7 Hz — 0.1 % error.**
* **DERIVED.** Ross-Kerwin-Ungar's ceiling for a symmetric three-layer plate
  depends on the geometry alone: Y = 3(h_skin+h_core)²/h_skin² = **5.07**, so
  eta_c ≤ **0.423 × eta_PVB**. Glassy PVB at tan δ = 0.15 permits **0.063**.
* **PUBLISHED.** monolithic glass **0.0006–0.002**; PVB laminate, standard
  interlayer **0.02–0.06**; acoustic interlayer **0.1–0.3**.

`GLASS_LAMINATE_ETA = 0.030` is the middle of the published standard-interlayer
band and inside the RKU ceiling. **THE BAND IS CARRIED IN THE CODE AND SWEPT IN
THE BENCH**, because a conclusion that only survives at one end of a published
range is not a conclusion.

**AND THE FREQUENCIES BARELY MOVE.** EN 16612's effective thickness at the
glassy gamma → 1 is **11.49 mm against the 12.0 mm already in use — 4 %.** One
mechanism changes the damping by a factor of thirty and the pitch by four per
cent, which is why this is one fix and not two.

---

### R2-4150(4) — THE 2×2. `tools/r2_4150_breach_bench.py`

Population × damping, on the glass layer alone and in the delivered mix:

| | glass AMI | contacts | in the mix |
|---|---:|---:|---:|
| **legacy population, Q 800–1500 — WHAT SHIPPED** | **0.2533** | 1055 | **0.1695** |
| legacy population, laminate eta 0.030 | **0.8149** | 1055 | **0.3844** |
| picture population, Q 800–1500 | 0.2223 | 8401 | 0.1479 |
| **picture population, laminate eta 0.030** | **0.8315** | 8401 | **0.3841** |

**THE DAMPING IS THE ENTIRE FIX AND THE POPULATION IS WORTH 0.017 ON THE LAYER
AND −0.0003 IN THE MIX.** Both are shipped, and the reason the population ships
is NOT this table — see R2-4150(5).

**eta ACROSS THE WHOLE PUBLISHED BAND**, picture population:

| eta | 0.00087 | 0.002 | 0.010 | 0.020 | **0.030** | 0.045 | 0.060 | 0.100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| glass AMI | 0.2223 | 0.2561 | 0.5055 | 0.7074 | **0.8315** | 0.9757 | 1.0695 | 1.3070 |
| beat AMI | 0.1479 | 0.1604 | 0.2664 | 0.3436 | **0.3841** | 0.4215 | 0.4407 | 0.4848 |

**NO VALUE IN THE PUBLISHED BAND CLEARS THE BAR, INCLUDING THE ACOUSTIC-PVB END
AT 0.10.** That is the protection this pass has against its own knob: the
result cannot be bought by raising eta, so eta was left in the middle of the
band it belongs in.

**AMI's HOLE, CHECKED AGAINST THE BUILD** (R2-4149: a single impulse in 8 s of
silence reads 37.13). Fraction of the layer's energy in its loudest 20 ms:
shipped **0.0219**, rebuilt **0.0265**. **The score is not one bang over a quiet
bed.**

---

### R2-4150(5) — THE POPULATION SHIPS ANYWAY, AND THE REASON IS THE PICTURE

`sim/fracture.py` partitions every pane — radials first, then hoops arrested on
them, then a mosaic coarsening outward, with the 16 mm clamped under the
pressure plate holding slabs — and publishes one record per shard in
`sim/out/breach_sim.json`, which is **tracked**. The 4K frames were rendered
from that partition. The audio never read it:

| equivalent side √area | the picture | the audio, as delivered |
|---|---:|---:|
| under 20 mm | 1412 | **0** |
| 20–50 mm | 1108 | 2 |
| 50–100 mm | 146 | 17 |
| 100–200 mm | 194 | 45 |
| 200–400 mm | 328 | 155 |
| over 400 mm | 28 | 132 |
| **median piece** | **21 mm** | **321 mm** |
| **count / mass** | **3216 / 1119 kg** | **351 / 1624 kg** |

**AN ORDER OF MAGNITUDE OUT IN COUNT AND IN SIZE, IN BOTH DIRECTIONS AT ONCE.**
It is shipped because it is a picture desync, and it buys a real spectral change
even though it buys no AMI: the shard bus carries **0.15 % of its energy above
4 kHz as delivered and 6.46 % rebuilt — 43×.** That matters on its own terms,
and it retires R2-4060's stated reason for the `debris` bus's level ("the only
bus in the breach with any top end, every other bus below 0.2 %"), which is now
false by measurement. **The `debris` level was NOT changed in this pass** — that
is a mix change and it must not be confounded with the A/B the client is being
asked to judge, exactly as R2-4147(5) reasoned about the reverb. OPEN, with the
number.

**A BUG THE REBUILD EXPOSED AND THE REBUILD FIXES.** `debris_bed`'s density was
`fines_per_contact` × however many contacts the ballistics happened to produce,
so the number of sub-centimetre pieces in the showroom was a function of the
shard count. Correcting the population silently took the bed from 139,950 fines
to **1,177,213** — 8.4× denser, at 113,000 arrivals per second against a 100 Hz
roughness boundary. The parameter is now a declared TOTAL, defaulted to the
delivered figure exactly, so **the bed is unchanged and the field above it is a
single-variable change.**

---

### R2-4150(6) — THE PREDICTIONS, WRITTEN DOWN BEFORE THE RENDER WAS ADJUDICATED

Every pass in this chain has reported predictions that failed. These were
recorded before `tools/percept_matrix.py` was run on the new master, from the
stem-substituted bench, and each has a number:

1. **G-PRESENCE `3_breach` AMI 0.1409 → 0.35–0.42, AND STILL FAIL.** The bench
   says 0.3841 and the bar is 0.50. **The bound in R2-4150(2) says no glass
   layer clears it through this engine**, so a PASS here would mean the bench
   is wrong, not that the build is good.
2. **G-EVENT `3_breach` 2.71 dB → about 3.5–4.5 dB, AND STILL FAIL.** Measured
   on the substituted mix: median 2 s window 3.61 → **4.57 dB** against a
   13.7 dB bar. Trough depth is what the engine is filling, and the glass
   cannot un-fill it.
3. **G-SUSTAIN `3_breach` "three or more pitches held at once for 0.099 of the
   beat" → under the 0.05 bar, PASS.** A fragment at eta 0.030 holds nothing;
   at eta 0.00087 a 321 mm piece rang for 0.600 s inside an 8 s beat.
4. **G-BALANCE `3_breach` — DIRECTION UNKNOWN, AND THAT IS STATED RATHER THAN
   GUESSED.** The protagonist leads the near-white background by +4.13 dB
   against an +8.0 dB bar. The rebuilt field is peakier (26.9 dB crest), and
   the `shards` bus is already PEAK-CRITERION limited — it misses its declared
   −9.0 LUFS-S target by 3.88 dB because one linear peak pins it at 1.0. A
   peakier field may be trimmed FURTHER down. **The two shortfalls, 3.87 dB of
   G-BALANCE margin and 3.88 dB of missed LUFS target, agree to 0.01 dB, and
   that coincidence is worth someone's attention.**
5. **BEAT 1 IS UNCHANGED, all gates, all numbers.** Nothing in this pass touches
   the assembly layer, the cell, the reverb or the mix.
6. **`debris_p80_x_m` 30.15 → 23.14 m**, which feeds `classify()` and therefore
   the tyres' debris surface in beats 4–6. It is a consequence, it is declared,
   and it moves TOWARD the picture: the delivered bake's fallen pieces rest at
   **p50 16.40 m, p80 16.64 m, p95 17.10 m** — i.e. 1.4–2.1 m past a wall at
   x = 15.0. **The audio still throws its debris six times too far, and that is
   a separate desync recorded here rather than fixed in this pass.**

---

### R2-4150(7) — THE RENDER. THE GLASS GOT 4.3× MORE ARTICULATE AND THE BEAT GOT WORSE.

`audio/out/r2_4150/master_R2-4150.wav`, −23.00 LUFS / −1.16 dBTP, limiter GR
−0.59 dB, `AUDIO_MASTER_OK`; `tools/percept_matrix.py` returns
`PERCEPT_MATRIX_OK`, 40 thresholds, 0 provenance violations, **G-CONSTRUCT
unchanged at 17 pre-existing violations and none of them in the new code.**

**THE GENERATOR FIX WORKED EXACTLY AS DESIGNED.** On the delivered stems, over
36–44 s:

| the `shards` bus | R2-4147 | **R2-4150** |
|---|---:|---:|
| **its own AMI** | 0.2565 | **1.1107** |
| against the corpus positive's whole shower | — | 0.7857 |
| against its "large pieces and mullions alone" | — | 1.3108 |
| energy above 4 kHz | 0.15 % | **6.46 %** |
| crest | 17.6 dB | 27.7 dB |
| its loudest ten 20 ms windows | 14.5 % of the bus | **49.1 %** |

**AND THE MIX THREW IT AWAY.**

| bus, 36–44 s | R2-4147 | R2-4150 |
|---|---:|---:|
| `shards` share of the beat | **36.27 %** | **6.36 %** |
| `shards` delivered energy | — | **−8.38 dB** |
| `debris` share of the beat | 12.37 % | **31.55 %** |
| `debris` delivered energy | — | **+3.25 dB** |
| engine share of the beat | 44.73 % | **54.01 %** |
| **beat AMI** | **0.1421** | **0.1379** |

**THE ARTICULATE LAYER WAS TRIMMED 8.4 dB DOWN AND AN UNCHANGED WASH TOOK ITS
PLACE.** Restore only the level and nothing else — same rebuilt signal, same
everything, the `shards` bus put back to the energy the old one delivered:

| | beat AMI |
|---|---:|
| delivered R2-4147 | 0.1421 |
| **R2-4150 as rendered** | **0.1379** |
| R2-4150, `shards` restored to the old bus energy (+8.38 dB) | **0.3219** |
| R2-4150, both glass buses restored to the old energies | **0.3484** |

**THE FIX IS WORTH 2.45× ON THIS BEAT AND THE MIX COSTS ALL OF IT.**

---

### R2-4150(8) — WHY, AND IT IS NOT A BUG. THE PEAK CRITERION PENALISES ARTICULATION.

`master.add()` trims every bus to the LESSER of its declared LUFS-S target and
whatever keeps its linear peak at `BUS_PEAK_CEILING` = 1.0. Both renders'
`shards` bus enters at peak 1.0. What changed is what is under the peak:

| `shards` | R2-4147 | R2-4150 |
|---|---:|---:|
| raw max short-term LUFS | 17.91 | **1.05** |
| trim from the −9.0 LUFS-S target | −26.91 | −10.05 |
| trim from the peak ceiling | **−30.80** | **−21.76** |
| **delivered LUFS-S** | **−12.89** | **−20.71** |
| **short of its declared target by** | **3.88 dB** | **11.71 dB** |

**A MORE EVENTFUL BUS HAS A HIGHER CREST, SO AT A FIXED PEAK CEILING IT
DELIVERS LESS LOUDNESS.** That is the criterion doing exactly what R2-4034
specified, on a bus for which R2-4034's *reason* does not apply: the ceiling
exists because the K-weighting discounts sub-bass the meter cannot hear, and
the rebuilt shard bus's peaks are 0.16 ms Hertzian contacts with 6.5 % of the
bus's energy above 4 kHz. **The meter can hear these peaks perfectly well.**

**AND THE CREST MAY ITSELF BE PART-ARTEFACT, WITH ARITHMETIC ATTACHED.**
`render_shards` sets a fragment's contact time as
`t_contact = 8e-5 (1 + 0.6 b)(1 + 2 L)`, which over the picture's 21 mm → 495 mm
size range is a factor of **1.99**. Hertzian impact of geometrically similar
bodies gives `t_c ∝ (m²/(R E*² v))^(1/5)`, and for a plate (m ∝ L², R ∝ L) that
is `t_c ∝ L^0.6`, i.e. a factor of **6.7** over the same range. **The largest
fragments' contacts are about 3.4× too short and therefore about 10.6 dB too
peaky** — which is the same order as the 8.38 dB the mix took away. It is
recorded with its arithmetic and **it was NOT implemented**, because deriving a
contact-time law while needing 8.4 dB is exactly the situation this file warns
about four times over.

---

### R2-4150(9) — WHAT THE ADJUDICATION SAYS, AND WHAT SHIPS

`tools/r2_4150_matrix_diff.py`, R2-4147 against R2-4150. **NO GATE'S FILM-LEVEL
VERDICT MOVED.** Line by line:

| | R2-4147 | R2-4150 | |
|---|---:|---:|---|
| G-PRESENCE `3_breach` AMI | 0.1409 | **0.1472** | flat |
| G-EVENT `3_breach` | 2.71 dB | **4.30 dB** | better, bar 13.7 |
| **G-BALANCE `3_breach` protagonist lead** | **+4.13 dB** | **−7.44 dB** | **11.6 dB WORSE** |
| G-BALANCE `3_breach` near-white share | 0.474 | 0.398 | better, bar 0.25 |
| **G-SUSTAIN `3_breach`** | chord held 0.099 | **a pitch held 0.269** | **worse limb** |
| G-ROOM `3_breach` (c) | FAIL 23.26× / 12.40 dB | **INAPPLICABLE** | **coverage lost** |
| G-BALANCE `4_transit` | −2.30 dB | −0.96 dB | better |
| G-FLAT `4_transit` | 0.700 | 0.661 | better |
| G-HNR `4_transit` | 0.675 | 0.631 | better |
| every beat-1 line | — | — | **IDENTICAL** |

**THE ADJUDICATION DOES NOT IMPROVE. NOTHING SHIPS.**
`PART2_AUDIO_MASTER_R2-4147.wav` remains the delivery, untouched; neither film
was re-muxed, so the ProRes and H.265 video md5s were never rewritten — both
were re-verified read-only this pass and still read `c346a7a322a4a2a403727c1e85f17511`
and `235ef36e844a62b0e303e4138907b9fa`. `watch/INDEX.md` and
`watch/listen_2026-08-14/` are unchanged because nothing was cut.
`audio/out/master.wav` and `watch/rejected_audio_R2-4079/` are untouched and
still fail.

**AND `audio/layers.py` IS REVERTED TO THE SHIPPED STATE.** The rebuild is
landed as `tools/r2_4150_breach_rebuild.py`, a patch, on R2-4149(5)'s own
reasoning: **the render path in git must reproduce the delivered master at all
times**, and a rebuild that was measured and rejected must not be the thing
`git HEAD` renders. `tools/r2_4150_breach_bench.py` runs the whole 2×2 through
it and reproduces every number above with the render path untouched.

---

### R2-4150(10) — THE PREDICTIONS FROM R2-4150(6), SCORED

1. **AMI 0.35–0.42 and still FAIL. WRONG.** It read **0.1472**. The bench was
   right about the LAYER and wrong about the FILM, because the bench held the
   mix constant and the mix is what moved. **A bench that substitutes at
   constant energy cannot see a trim, and this one did not say so.**
2. **G-EVENT 3.5–4.5 dB and still FAIL. RIGHT** — 4.30 dB.
3. **G-SUSTAIN's chord limb clears. PARTLY RIGHT AND NET WORSE.** The chord
   limb went; a worse one arrived — *something holds a pitch for 0.269 of the
   beat* against a 0.20 bar — because with the glass 8.4 dB down, the engine's
   held pitch through the ramp is what is left.
4. **G-BALANCE direction unknown. THE UNCERTAINTY RESOLVED THE BAD WAY, BY THE
   NAMED MECHANISM.** +4.13 → −7.44 dB.
5. **Beat 1 unchanged. RIGHT** — not one beat-1 line moved.
6. **`debris_p80_x_m` moves beats 4–6. RIGHT**, and every one of those moves is
   an improvement: G-BALANCE `4_transit` +1.34 dB, G-FLAT `4_transit`
   0.700 → 0.661, G-HNR `4_transit` 0.675 → 0.631.

---

## OPEN, AFTER R2-4150

1. **THE BREACH'S DEFECT IS NAMED AND THE FIX IS BUILT AND MEASURED.** Fragments
   of PVB-laminated glass rang at eta 0.00087 — below monolithic float glass —
   and 995 contacts a second rang for 0.600 s each. At the laminate's published
   0.030 the glass layer reads **1.1107 against a corpus positive's 0.7857**,
   and the beat would read **0.3484** at the delivered mix levels. Everything
   needed is in `tools/r2_4150_breach_rebuild.py`.
2. **THE BLOCKER IS `BUS_PEAK_CEILING` AGAINST AN EVENT BUS, AND IT IS 8.38 dB.**
   R2-4034's derivation is about sub-bass the K-weighting cannot hear; it fires
   here on 0.16 ms contacts with 6.5 % of their energy above 4 kHz. **This needs
   its own pass and it must not be done inside a glass rebuild.** The two
   candidate directions, with their arithmetic: the peak criterion's
   applicability rule, and the contact-time law's `L^0.6` (R2-4150(8)).
3. **THE ENGINE IS 44.7 % OF THE BREACH AND READS AMI 0.069**, and the measured
   bound says **no glass layer clears the 0.50 bar through it** — an ORACLE
   layer reaches 0.3031. 1.6 s of world stretched over 8 s of film is a
   full-throttle power unit held for eight seconds, at −17.79 dBFS against
   −30.19 on the flying lap. **Slow motion spreads a shower's arrivals and does
   not spread a continuous source's energy**, which is why beat 3 is the one
   beat where the car outweighs what it is destroying. Nothing was tuned to
   this and nothing should be until it is derived.
4. **THE AUDIO THROWS ITS DEBRIS SIX TIMES TOO FAR.** The delivered bake's
   fallen pieces rest at p50 **16.40 m**, p95 **17.10 m** — 1.4–2.1 m past a
   wall at x = 15.0. The audio's launch law puts p80 at 30.15 m as shipped and
   23.14 m rebuilt. It feeds `classify()` and therefore the tyres' debris
   surface in beats 4–6.
5. **`debris_bed`'s density is a multiple of the shard count.** Corrected in the
   patch, not in the tree, since the tree is reverted. Anyone touching the
   population must fix this in the same edit or the bed silently multiplies.
6. Carried unchanged from R2-4149: G-RING's ratio bar under its own null;
   G-RING's Sabine limb un-anchored; AMI's and G-EVENT's shared hole; C10 a
   bench control; the diffuser's 0.777 s floor above 11 kHz; G-ROOM(c)'s two
   bars under their nulls; **G-MOD and G-NOVEL at beat 1 remain PICTURE.**
