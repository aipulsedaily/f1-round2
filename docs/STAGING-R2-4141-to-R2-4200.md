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

---

## R2-4151 — THE MIX. THE 8.38 dB IS NOT IN THE CEILING; 2.96 dB OF IT IS IN THE ATTACK, AND THE REST IS HEADROOM THE FILM DOES NOT HAVE.

R2-4150 built the breach fix, measured it, and correctly refused to ship it:
the glass layer got 4.3× more articulate and the delivered beat got worse,
because `master.add()` trimmed the improved bus 8.38 dB down. It left two
candidate directions with their arithmetic attached. **This pass adjudicated
both. The one with the bigger number attached is wrong, and the mechanism that
is right was not on the list.**

---

### R2-4151(1) — THE CANDIDATE WITH THE ARITHMETIC, CHECKED FIRST, AND REFUTED. `tools/r2_4151_contact_time.py`

The standing rule is that a guard which fires on a signal that is genuinely too
peaky is RIGHT and the signal is wrong, so R2-4150(8)'s contact-time candidate
was adjudicated before a line of the mix was touched:

> `t_contact = 8e-5 (1 + 0.6 b)(1 + 2 L)` spans 1.99× where Hertz gives
> `L^0.6` = 6.7×, so the largest fragments are ~10.6 dB too peaky.

**THE PREMISE IS RIGHT AND THE CONCLUSION IS WRONG.**

* **The coefficient is checked, not quoted** (R2-4149's hazard rule, after a
  free-plate constant was once wrong by 13.5×). `t_c = 2.9432 δ_max/v` is
  verified by integrating the Hertz ODE `m δ'' = −k δ^{3/2}` directly:
  **2.9433 against 2.9432.**
* **The exponent really is wrong.** Over the picture's 21.3 → 495 mm the
  shipped law's effective exponent is **0.21 against Hertz's 0.60**, and a
  433 mm fragment's contact is **5.25× too short** at α = 0.05. The absolute
  level is robust: α over its whole plausible range, 0.01 → 0.50, moves `t_c`
  by 2.19× and the exponent not at all.
* **AND CORRECTING IT MAKES THE BUS PEAKIER.** Measured over all 8401 contacts:
  the peak proxy falls **2.29 dB** and the energy proxy **3.60 dB**, i.e.
  **crest +1.31 dB**, and the sign holds across α = 0.02–0.20 (+0.94 to
  +1.53 dB). **The peak criterion would take MORE away, not less.**

**WHY THE ARITHMETIC MISLED.** It assumed peak ∝ 1/T. `hertz_spectrum` is FLAT
below 1/T, and a 433 mm fragment's entire mode set sits at 174–2049 Hz while
1/T is 6.7 kHz on the shipped law and 1.7 kHz on the Hertz law. Lengthening the
contact does not touch the peak; it attenuates the UPPER modes, which carry
energy and not peak. **NOT IMPLEMENTED**, on R2-4150(8)'s own reasoning: it is
a real ~3.4× error in contact hardness and it belongs to whoever next opens the
shard synthesiser with nothing riding on the answer.

---

### R2-4151(2) — `BUS_PEAK_CEILING`'s STATED REASON DOES NOT EXIST ANYWHERE IN THIS FILM. `tools/r2_4151_peak_scope.py`

R2-4034's derivation is that the BS.1770 meter is deaf to the breach's buses
because they are almost entirely sub-bass. The direct measure of that is the
**same 3 s short-term meter taken K-weighted and taken UNWEIGHTED** — identical
window, hop and offset, differing only by the filter, so the gap is the meter's
deafness to that bus and nothing else. Every bus, both shipped stem sets:

| the three buses the peak criterion wins on | K-weighted | unweighted | **deafness** |
|---|---:|---:|---:|
| `engine` | −29.46 | −31.08 | **−1.62 dB** |
| `impact` | −27.63 | −27.56 | **+0.07 dB** |
| `shards` (R2-4150) | +1.05 | +0.01 | **−1.04 dB** |
| the deafest bus in the whole film, `assembly` | −34.16 | −31.89 | **+2.27 dB** |

**R2-4034 MEASURED 14.09 dB ON THE `impact` BUS. IT READS +0.07 dB TODAY** —
because **R2-4035, in the same rebuild, moved the transient world-attached
sources onto the film grid** and took `impact` from **92.99 % of its energy
below 30 Hz to 3.09 %**. The ceiling's premise was eliminated by its own
commit's neighbour and nobody re-measured it.

**WHAT THE CRITERION ACTUALLY IS.** `g_peak < g_lufs` reduces exactly to
`PLR > −target`: a bus is trimmed below its declared loudness precisely when
its peak-to-loudness ratio exceeds a **mix constant**. `shards` declares −9.0,
so anything over **9.0 dB of PLR** is taxed — less PLR than any transient
signal on earth has. **This is the same mechanism as the other three: it
punishes eventfulness, and it does so by construction.**

**THE POSITIVE CONTROL SAYS THE SAME, ON THE CRITERION'S OWN MEASURE.**
`synth.glass_breach` is the validated physics positive for this exact event.
Its peak-to-loudness ratio, measured the way `add()` measures it:

| | PLR | crest | AMI |
|---|---:|---:|---:|
| corpus positive, dice + slabs + mullions | **27.14 dB** | 33.44 | 0.7782 |
| corpus, slabs alone | 27.85 dB | 34.12 | 1.4070 |
| **R2-4150's rebuilt `shards` bus** | **20.71 dB** | 27.81 | 1.1107 |
| R2-4147's shipped `shards` bus | **12.88 dB** | 17.60 | 0.2565 |
| the criterion's tax threshold at `shards`' -9.0 target | **9.00 dB** | — | — |

**THE REFERENCE ANSWER WOULD BE TAXED 18.14 dB — 6.4 dB HARDER THAN THE THING
BEING FIXED.** And the master that shipped sits at less than half the
reference's PLR, which is the same statement as "it was a wash", in the units
the mix actually uses. **A guard that punishes the correct answer more than the
defect is not measuring the defect.**

**AND IT IS NOT DISABLED.** It is still load-bearing for a reason R2-4034 does
not state: `impact` is ONE event in a 124 s film, its 3 s meter reads
−27.63 LUFS, and its −6.5 target therefore asks for **+21.13 dB**. Without the
ceiling that bus enters the sum at a linear peak of **19.5**. The 3-second
short-term meter is the wrong instrument for a single-event bus and the peak
ceiling is what has been covering for it. **`BUS_PEAK_CEILING` IS UNCHANGED AT
1.0.**

---

### R2-4151(3) — AND IT IS NOT THE 8.38 dB BLOCKER EITHER. TWO DECLARED THRESHOLDS BIND FIRST.

The R2-4150 stems summed and put through `master.py`'s real post-premix chain —
30 Hz high-pass, program gain, DC block, the solved-for single limiter pass:

| `shards` | premix peak | G14 (≤ +6 dBFS) | limiter GR | G1 (≤ 3 dB) |
|---|---:|---|---:|---|
| +0.00 dB (as delivered) | +2.99 dBFS | PASS | −0.59 dB | PASS |
| +4.00 dB | +5.91 dBFS | PASS | −1.02 dB | PASS |
| +6.00 dB | +7.55 dBFS | **FAIL** | −1.24 dB | PASS |
| **+8.38 dB (the OPEN item's ask)** | **+9.58 dBFS** | **FAIL** | **−3.07 dB** | **FAIL** |

**G14 BINDS AT ABOUT +4.05 dB AND G1 AT ABOUT +8.2 dB.** Both are declared
thresholds and neither may be moved to make a master pass. **So the 8.38 dB was
never available from the mix at any setting of the ceiling, and the OPEN item
that named the ceiling as "THE BLOCKER" was wrong by construction.** What is
available from the mix is at most 4 dB, and this pass does not take it: it
takes 2.96 dB out of the SOURCE instead, at unchanged premix peak.

---

### R2-4151(4) — WHERE THE PEAK ACTUALLY COMES FROM. THE ATTACK WAS 1.7× ITS OWN DECLARATION AND VARIED BY 3× ON A RANDOM INTEGER.

`ACCEL_NOISE_RATIO = 0.45` is declared as *"the acceleration transient's PEAK,
as a fraction of the modal ring of the same contact"* — the one number in the
shard synthesiser the file says is stated rather than derived. `render_shards`
passed it **`amp.sum()`**: the value the ring would reach only if all 8–14 of
its modes were in phase, which they never are, because `ph` is drawn uniformly.

Measured over 2848 contacts of the rebuilt breach:

| `amp.sum()` / ring peak | p10 | median | p90 |
|---|---:|---:|---:|
| | 1.07 | **1.69** | 3.19 |

**THE DELIVERED RATIO WAS A MEDIAN 0.76 AGAINST A DECLARED 0.45, AND IT VARIED
BY 3× BETWEEN CONTACTS ACCORDING TO HOW MANY MODES `shard_modes` HAPPENED TO
DRAW.** A shard's attack got louder because of a random integer.

`latch_strike`, in the same file, already references `np.abs(y).max()`.
`part_impacts` uses `amp.sum()` and gets away with it because it
peak-normalises the whole contact afterwards. **`render_shards` is the one call
site where the reference reaches the mix unnormalised, and it is the one that
was wrong.** `part_impacts` is beat 1 and was deliberately NOT touched.

**WHAT IT IS WORTH.** Same population, same damping, that line the only
difference:

| dry glass field, 36–44 s | `amp.sum()` | **ring peak** |
|---|---:|---:|
| peak | 241.97 | **160.89** (−3.56 dB) |
| max short-term | 22.74 | **22.14 LUFS** (−0.60 dB) |
| crest | 27.81 dB | **24.58 dB** |
| **articulation index** | **0.8161** | **0.8140** |

**A peak that can be removed without moving the loudness or the articulation
was not carrying any of the sound.** Under a fixed peak ceiling it is worth
**2.96 dB of delivered level**, and the premix peak does not move, so G14 and
G1 are untouched. **This is the one place the 8.38 dB was actually hiding, and
it is in the source, exactly where R2-4150(8) said to look — just at a
different parameter.**

---

### R2-4151(5) — THE DECLARED MIX WAS INVERTED BY A TRIM, AND NOTHING SAID SO.

`TARGET_LUFS_S` is a table of absolute numbers, and two of its entries are a
RELATIONSHIP. R2-4060's own comment: *"Sitting it 1.5 dB under the foreground
shards is a mix statement: the fragments lead, the fines sit just beneath
them."*

An absolute pair expresses that relationship only for as long as both buses
reach their numbers. **`shards` does not.**

| 36–44 s | declared | R2-4147 delivered | R2-4150 delivered |
|---|---:|---:|---:|
| `shards` LUFS-S | −9.0 | −12.89 | **−20.71** |
| `debris` LUFS-S | −10.5 | −14.12 | **−10.50** |
| **`debris` relative to `shards`** | **−1.5 dB** | −1.23 dB | **+10.21 dB** |

**THE MIX STATEMENT WAS INVERTED BY 11.7 dB BY A TRIM, SILENTLY, AND EVERY GATE
THAT READS THE BREACH READ THE INVERSION.** The reason the two renders differ
is itself the fourth mechanism: R2-4147's `debris` was peak-limited and fell
3.62 dB short of its target; R2-4150's, spread over 8401 contacts instead of
1055, is smoother, is no longer peak-limited, and collects its declared level
in full. **The wash was rewarded for being a wash.**

`RELATIVE_TARGET_LUFS_S` is added to `master.py`: a bus may declare its level as
an offset from another bus's **DELIVERED** short-term loudness, and `build()`
resolves it after the reference has been summed and refuses if it has not.

**AND THE OFFSET GOES BACK TO −4.0 dB.** R2-4060 raised `debris` from −13.0 to
−10.5 on one stated reason — *"the bed carries 97.6 % of its own energy above
4 kHz and is the only bus in the breach with any top end (every other bus is
below 0.2 %)"*. **R2-4150(5) refuted that by measurement**: the rebuilt `shards`
bus carries **6.46 %** of its energy above 4 kHz against 0.15 % as delivered,
i.e. **43×**. A raise whose premise is false is reverted, not re-argued, so the
offset is R2-4044's own words — *"it sits UNDER the foreground shards rather
than beside them"* — which is the −13.0 that was in the table before R2-4060,
i.e. **4.0 dB under `shards`**. R2-4150(5) left this OPEN with the number
specifically so it would not be confounded with the A/B the client was asked to
judge. That A/B has happened.

---

### R2-4151(6) — WHAT WAS BUILT, AND THE ONE THING THAT WAS NOT

> **THIS SECTION WAS WRITTEN BEFORE THE RENDER AND IT SAID "WHAT SHIPS".
> R2-4151(9) REVERSES IT: NOTHING SHIPS.** It is left standing because a plan
> that was overturned by its own measurement is the most useful thing in the
> file. The five changes below were written into `audio/layers.py` and
> `audio/master.py`, rendered end to end and adjudicated; they are now
> `tools/r2_4151_landing.patch`, applied with
> `git apply tools/r2_4151_landing.patch`, and the render path in git is the
> shipped one again.

Built, rendered and measured:

1. **`layers.shard_modes`** — `GLASS_LAMINATE_ETA = 0.030` replaces Q = 800–1500.
   R2-4150(3)'s derivation, unchanged, swept across the whole published band in
   `tools/r2_4150_breach_bench.py`. **This is the whole glass fix.**
2. **`layers.picture_fragments` / `layers.shard_ballistics`** — the population is
   read from `sim/out/breach_sim.json`, the partition the 4K frames were
   rendered from. Worth 0.017 of AMI and 43× the energy above 4 kHz.
3. **`layers.debris_bed`** — density is a declared TOTAL, defaulted to the
   delivered 139,950, so correcting the population cannot silently take the bed
   to 1,177,213.
4. **`layers.render_shards`** — the acceleration transient references the ring's
   own peak, so `ACCEL_NOISE_RATIO` delivers the 0.45 it declares. R2-4151(4).
5. **`master.RELATIVE_TARGET_LUFS_S`** — `debris` is declared 4.0 dB under
   `shards`'s DELIVERED level. R2-4151(5).

**NOT CHANGED, AND EACH FOR A STATED REASON:** `BUS_PEAK_CEILING` (its premise
is dead but it is still the only thing standing between a single-event bus and
a linear peak of 19.5); G14 and G1 (declared thresholds, and they are what
bounds this); the contact-time law (R2-4151(1)); `part_impacts`' identical
`amp.sum()` reference (beat 1 is picture-locked); `audio/verify.py` and
`tools/percept_matrix.py`; the engine (R2-4150(2)'s bound says no glass layer
clears 0.50 through it, and it is the next defect and a separate pass).

---

### R2-4151(7) — THE PREDICTIONS, WRITTEN DOWN BEFORE THE RENDER WAS ADJUDICATED

Every one has a number, and they are recorded before `tools/percept_matrix.py`
was run on the new master.

1. **`shards` delivered LUFS-S −20.71 → −17.8 ± 0.7**, still peak-criterion-won,
   still short of its −9.0 target by about 8.8 dB. **`debris` −10.50 → −21.8 ±
   0.7**, and the peak criterion will NOT win on it.
2. **The premix peak does not move: +2.9 to +3.2 dBFS, G14 PASS, limiter GR
   within 0.2 dB of −0.59, G1 PASS.** The whole point of taking the level out of
   the attack rather than out of the ceiling is that the mix's headroom is
   unchanged.
3. **G-PRESENCE `3_breach` AMI 0.1409 (R2-4147) / 0.1472 (R2-4150) → 0.20–0.25,
   AND STILL FAIL.** R2-4150(2)'s measured bound says an ORACLE glass layer
   reaches 0.3031 through this engine against a 0.50 bar, so a PASS here would
   mean the bound is wrong, not that the build is good.
4. **G-BALANCE `3_breach` protagonist margin +4.13 (R2-4147) / −7.44 (R2-4150) →
   +0.8 to +2.2 dB. THIS IS THE ONE NUMBER THAT DOES NOT RECOVER, IT IS
   PREDICTED TO REGRESS AGAINST THE SHIPPED MASTER, AND THE REASON IS STATED
   RATHER THAN DISCOVERED:** R2-4147's +4.13 dB was bought by a `shards` bus
   that was 33.74 % of the beat *because it was a wash* — 17.6 dB crest, eta
   0.00087, 63 rings alight at once. An articulate bus cannot be that loud
   under any peak ceiling this film's headroom allows. **If this pass is judged
   on that limb alone it ships nothing.**
5. **G-BALANCE `3_breach` near-white share 0.474 (R2-4147) / 0.398 (R2-4150) →
   0.24–0.33.** It may cross the 0.25 bar. If it does, that limb PASSES for the
   first time in the project.
6. **G-EVENT `3_breach` 2.71 dB (R2-4147) / 4.30 (R2-4150) → 4.0–5.5 dB, still
   far under the 13.7 bar.**
7. **G-SUSTAIN `3_breach`: R2-4150's new worse limb — a pitch held 0.269 of the
   beat, which is the ENGINE showing through with the glass 8.4 dB down —
   improves, and the chord limb stays clear. I do not predict it clears the
   0.20 bar.**
8. **BEAT 1 IS UNCHANGED, ALL GATES, ALL NUMBERS.** Nothing in this pass touches
   the assembly layer, the cell, the reverb or beat 1's mix, and
   `part_impacts`' identical `amp.sum()` reference was deliberately left alone.
9. **BEATS 4–6 MOVE VIA `debris_p80_x_m` 30.15 → 23.14 m**, exactly as R2-4150(6)
   predicted and R2-4150(10) scored RIGHT: G-BALANCE `4_transit` +1.34 dB,
   G-FLAT `4_transit` 0.700 → 0.661, G-HNR `4_transit` 0.675 → 0.631.
10. **NO GATE'S FILM-LEVEL VERDICT FLIPS.** I predict this pass improves five of
    the breach's numbers and regresses one.

---

### R2-4151(8) — THE RENDER

`audio/out/r2_4151/master_R2-4151.wav`, **−23.00 LUFS / −1.11 dBTP, limiter GR
−1.10 dB, premix peak +3.21 dBFS, `AUDIO_MASTER_OK`** — G1 and G14 both PASS,
which is the point: **the level was taken out of the attack and not out of the
headroom.** `tools/percept_matrix.py` returns `PERCEPT_MATRIX_OK`, 40
thresholds, 0 provenance violations, G-CONSTRUCT unchanged at 17 pre-existing
violations with none in the new code.

**AND THE SOURCE FIX WAS WORTH A THIRD OF WHAT THE BENCH SAID.**

| `shards` bus | R2-4150 | **R2-4151** |
|---|---:|---:|
| raw linear peak | 12.23 | **10.73** (−1.15 dB) |
| max short-term | 1.05 | 0.84 |
| trim from the peak ceiling | −21.76 | −20.61 |
| **delivered LUFS-S** | **−20.71** | **−19.77 (+0.94 dB)** |
| short of its −9.0 target by | 11.71 dB | **10.77 dB** |

**The dry field's peak fell 3.85 dB and the propagated bus's fell 1.15 dB**,
because the acceleration transient is the highest-frequency thing in a contact
and `prop.render`'s air absorption had already removed most of it before the
peak ceiling ever saw it. **A bench measured on the dry layer cannot see what
propagation does to a transient.** That is the same class of error as
R2-4150(10)'s first scored prediction — a bench that held the mix constant and
could not see a trim — **in two consecutive passes.**

`debris` followed its reference down to **−23.77 LUFS-S**, i.e. 13.27 dB below
where R2-4150 delivered it, because that is what "4.0 dB under `shards`" means
when `shards` is 10.77 dB short of its own declaration.

---

### R2-4151(9) — THE ADJUDICATION IMPROVES, THE ARTEFACT DOES NOT, AND NOTHING SHIPS

`tools/r2_4150_matrix_diff.py`, R2-4147 against R2-4151. **NO GATE'S FILM-LEVEL
VERDICT MOVED. THREE FAILURE LINES DISAPPEARED AND NONE APPEARED:**

| | R2-4147 | R2-4151 | |
|---|---|---|---|
| G-PRESENCE `3_breach` AMI | 0.1409 | **0.1710** | better, bar 0.50 |
| G-EVENT `3_breach` | 2.71 dB | **3.27 dB** | better, bar 13.7 |
| **G-BALANCE `3_breach` near-white share** | **0.474 FAIL** | **— GONE** | **the limb PASSES, for the first time** |
| **G-BALANCE `3_breach` margin** | **+4.13 dB** | **−0.14 dB** | **4.27 dB WORSE** |
| G-ROOM `3_breach` (c) cepstral 23.26× | FAIL | **— GONE** | the rings are gone |
| G-ROOM `3_breach` (c) ripple 12.40 dB | FAIL | **— GONE** | the rings are gone |
| G-ROOM `3_breach` (c) | FAIL | INAPPLICABLE | **0 usable decay tails** |
| G-SUSTAIN `3_breach` | no line | no line | R2-4150's new bad limb did not arrive |
| G-BALANCE `4_transit` | −2.30 dB | −0.93 dB | better |
| G-FLAT `4_transit` | 0.700 | 0.662 | better |
| G-HNR `4_transit` | 0.675 | 0.624 | better |
| every beat-1 line | — | — | **IDENTICAL** |

Beat 1's waveform differs from R2-4147 by **a pure gain of +0.285 dB with the
residual 92.4 dB below it** — the film's own program gain, and nothing else.

**AND THE PASS STILL DOES NOT SHIP. THE REASON IS THE ABLATION, NOT THE TABLE.**

On the delivered stems, putting `debris` back where R2-4150 had it and changing
nothing else:

| `debris` | beat AMI | G-BALANCE margin | near-white share | breach 4–8 kHz |
|---|---:|---:|---:|---:|
| **as rendered (−4.0 dB under `shards`)** | **0.1810** | **−0.14 dB** | **0.200** | **81.9 dB** |
| +6.00 dB | 0.1712 | −1.88 dB | 0.239 | 85.7 dB |
| +13.27 dB (R2-4150's level) | **0.1516** | −6.51 dB | 0.407 | 92.1 dB |

**THE GLASS REBUILD IS WORTH 0.1421 → 0.1516 AND TAKING THE WASH AWAY IS WORTH
0.1516 → 0.1810. THREE QUARTERS OF THE ADJUDICATION'S IMPROVEMENT IS
SUBTRACTION** — and this file has already documented one gate whose best
possible score is silence. Three more measurements, on the delivered masters:

* **The breach is 3.6 dB darker at 4–8 kHz than the master it would replace.**
  That band at the breach was the debris bed, which is 97.6 % above 4 kHz, and
  the client's word for a film with no top end is on record.
* **The glass is 6.9 dB quieter** (`shards` delivered −12.89 → −19.77 LUFS-S)
  **and the engine goes from 52 % to 79 % of the beat.** R2-4150(1) named the
  engine as the breach's next defect at 44.7 %. **This pass would deliver it
  worse.**
* **The glass LAYER's spectrum is right, and that is not the same thing.**
  Against the corpus positive `synth.glass_breach`, band by band, the layer
  moves toward the reference in **all five bands** (1–4 kHz −8.3 → −5.5 against
  −2.5; 8–16 kHz −20.2 → −17.4 against −11.7; 0–200 Hz −12.4 → −14.8 against
  −23.2). **The shape is better and the level is 6.9 dB down, and it is the
  level the client hears.**

**THE MIX CANNOT DELIVER THIS FIX, AND THAT IS NOW MEASURED RATHER THAN
SUSPECTED.** The peak criterion costs the articulate bus 10.77 dB; G14 binds
any mix-side recovery at +4.05 dB and G1 at +8.2 dB, and neither may be moved;
the source-side recovery available without touching a declared number is
0.94 dB; and restoring the declared balance by lowering the wash instead costs
the breach the top end the wash was carrying. **A breach in which the glass is
6.9 dB quieter and the engine is 79 % of the beat is not shippable on the
strength of three gate lines.**

**`PART2_AUDIO_MASTER_R2-4147.wav` REMAINS THE DELIVERY, UNTOUCHED.** Neither
film was re-muxed; both video streams were re-verified read-only this pass and
still read `c346a7a322a4a2a403727c1e85f17511` (ProRes) and
`235ef36e844a62b0e303e4138907b9fa` (H.265). `watch/INDEX.md` and
`watch/listen_2026-08-14/` are unchanged because nothing was cut.
`audio/out/master.wav` and `watch/rejected_audio_R2-4079/` are untouched and
still fail. **`audio/layers.py` AND `audio/master.py` ARE REVERTED TO THE
SHIPPED STATE**, and the whole landing is `tools/r2_4151_landing.patch`
(`git apply tools/r2_4151_landing.patch`), on R2-4149(5)'s standing rule that
the render path in git must reproduce the delivered master at all times.

---

### R2-4151(10) — THE PREDICTIONS FROM R2-4151(7), SCORED

**Four wrong, one partly, five right — and the headline was one of the wrong
ones, again.**

1. **`shards` −17.8 ± 0.7, `debris` −21.8 ± 0.7. BOTH WRONG** — −19.77 and
   −23.77. The accel fix was worth **+0.94 dB in the mix against +2.96 dB on
   the dry field**, and R2-4151(8) has the mechanism: propagation had already
   taken the transient out before the ceiling saw it. **A layer bench mis-sized
   a mix effect in two consecutive passes, in opposite directions.**
2. **Premix +2.9 to +3.2 dBFS, GR within 0.2 dB of −0.59, both PASS. PARTLY
   RIGHT** — +3.21 dBFS (just outside) and −1.10 dB (0.51 dB outside). Both
   PASS, and the headroom claim — that the source fix costs no headroom — held.
3. **AMI 0.20–0.25 and still FAIL. WRONG ON THE RANGE, RIGHT ON THE VERDICT** —
   0.1710.
4. **G-BALANCE margin +0.8 to +2.2 dB, predicted to regress. WRONG ON THE
   RANGE, RIGHT ON THE DIRECTION AND ON WHAT IT WOULD MEAN** — −0.14 dB. The
   prediction said in terms: *"if this pass is judged on that limb alone it
   ships nothing."* It was not judged on that limb alone; it was judged on the
   artefact, and it still ships nothing.
5. **Near-white share may cross the 0.25 bar. RIGHT** — the line is gone.
6. **G-EVENT 4.0–5.5 dB. WRONG** — 3.27 dB, between R2-4147's 2.71 and
   R2-4150's 4.30.
7. **G-SUSTAIN `3_breach` improves and does not clear its bar. RIGHT, AND
   BETTER THAN PREDICTED** — there is no G-SUSTAIN failure line at the breach
   in either master; R2-4150's *"a pitch held 0.269 of the beat"* did not
   arrive, because the engine no longer stands alone in the gap.
8. **Beat 1 unchanged, all gates, all numbers. RIGHT** — every line identical,
   and the waveform is a pure +0.285 dB with the residual 92.4 dB down.
9. **Beats 4–6 move via `debris_p80_x_m`. RIGHT** — G-BALANCE `4_transit`
   −2.30 → −0.93, G-FLAT 0.700 → 0.662, G-HNR 0.675 → 0.624.
10. **No verdict flips; five numbers better, one worse. RIGHT ON THE VERDICTS**
    — and three failure LINES disappeared, which the prediction did not
    anticipate.

---

## OPEN, AFTER R2-4151

1. **THE BREACH FIX IS BUILT, RENDERED AND ADJUDICATED, AND IT IS ONE PATCH
   AWAY.** `tools/r2_4151_landing.patch` carries the laminate damping, the
   picture's fragment population, the declared-total fines bed, the
   acceleration transient's ring reference and `RELATIVE_TARGET_LUFS_S`.
   `git apply` it and the render reproduces `audio/out/r2_4151/`. **It is
   withheld for ONE reason and it is not a gate: the delivered glass is 6.9 dB
   quieter than the master it would replace and the engine becomes 79 % of the
   beat.**
2. **THE BLOCKER IS A HEADROOM BUDGET, NOT A CEILING, AND THE 8.38 dB WAS NEVER
   IN THE MIX.** `BUS_PEAK_CEILING`'s stated derivation is dead — measured
   deafness ≤ 2.27 dB on every bus in the film, +0.07 dB on R2-4034's own case,
   because R2-4035 moved the sub-bass out from under it. What the criterion
   actually does is bound peak-to-loudness ratio at −target, i.e. tax
   eventfulness; the validated positive control for this event would be taxed
   **18.14 dB, 6.4 dB harder than the bus it trimmed 11.71 dB.** It stays
   anyway, because it is the only thing between a single-event bus and a linear
   peak of 19.5 — **the real defect is that a 3-second short-term meter is the
   wrong instrument for a bus whose event is 0.16 ms, and there is no second
   instrument.** Whoever takes this needs a headroom BUDGET across buses,
   measured against G14's +6 dBFS and G1's 3 dB, both of which are declared and
   were measured this pass at +4.05 dB and +8.2 dB of `shards`.
3. **THE ENGINE IS NOW THE WHOLE PROBLEM AND IT HAS BEEN SINCE R2-4150(1).**
   44.7 % of the breach as shipped, 79 % with the glass fixed, AMI 0.069,
   −17.79 dBFS RMS against −30.19 on the flying lap. The measured bound says an
   ORACLE glass layer reaches **0.3031** against a 0.50 bar through it. **No
   pass at the breach can succeed until the engine's eight-held-seconds is
   dealt with, and this pass is the proof: the glass layer now reads 1.11
   against a corpus positive's 0.79 and the beat still reads 0.17.**
4. **THE CONTACT-TIME LAW IS WRONG BY 3.4× ON THE LARGEST FRAGMENTS AND IT IS
   NOT WORTH ANY LEVEL.** `L^0.21` against Hertz's `L^0.6`, verified against a
   directly-integrated ODE. Correcting it makes the bus 1.3 dB PEAKIER. It
   belongs to whoever next opens the shard synthesiser with nothing riding on
   the answer. `tools/r2_4151_contact_time.py`.
5. **`ACCEL_NOISE_RATIO` IS NOW THE SHARD BUS'S TOP END, AND IT IS THE ONE
   UNDERIVED NUMBER IN THE SYNTHESISER.** With the reference corrected, the
   bus's energy above 4 kHz falls from 2.22 % to 0.68 % of itself — the attack
   *was* the top end. 0.45 is stated rather than derived, and it now controls a
   band the client has rejected a master over.
6. **`reflect_showroom` + `aperture` ARE 61 % OF THE NEAR-WHITE BACKGROUND AT
   THE BREACH** once the wash is gone (3.31 % and 3.07 % of the beat against a
   protagonist at 10.1 %), and G-BALANCE's margin limb cannot be reached
   without them. R2-4054 already wrote the rule for these two — *"if they still
   measure more than 15 dB under the mix after this, they should be deleted
   rather than raised again"* — and they now sit 14.8 and 15.1 dB under the
   beat. Nobody has applied that rule.
7. **THE AUDIO STILL THROWS ITS DEBRIS SIX TIMES TOO FAR** (p80 23.14 m rebuilt
   against a picture that rests at 16.6 m), carried unchanged from R2-4150(6).
8. Carried unchanged: G-RING's ratio bar under its own null; G-RING's Sabine
   limb un-anchored; AMI's and G-EVENT's shared hole; G-ROOM(c)'s two bars
   under their nulls; **G-MOD and G-NOVEL at beat 1 remain PICTURE.**

---

## R2-4152 — THE ENGINE. THE FILM WAS DELIVERING 6.5× THE WORLD'S ENGINE ENERGY AND THE WORLD'S GLASS, AND THAT IS ARITHMETIC ON R2-4064'S OWN RULE.

R2-4151 ended with a complete, measured breach fix withheld for one reason —
*"the delivered glass is 6.9 dB quieter than the master it would replace and the
engine becomes 79 % of the beat"* — and two OPEN items it could not close: a
headroom budget in place of a ceiling, and the engine.

**Both were the same item.** The film's premix peak sits at film t = 40.377 s
and it is **51.1 % `shards` and 44.4 % `engine`**. The bus that had to get
louder and the bus that had to get quieter were competing for one sample.

---

### R2-4152(1) — THE ENGINE'S DEFECT IS A MISSING CLAUSE IN A RULE THIS FILE ALREADY RELIES ON. `tools/r2_4152_engine_ramp.py`

R2-4064's rule is *"slow motion stretches the SCHEDULE and leaves the PITCH
alone"*, and `master.py` applies it to two classes of world-attached source in
the same eight seconds without ever saying what it does to their **LEVEL**:

* **IMPULSIVE** (R2-4035: `impact`, `shards`, `debris`). Each contact is placed
  at `to_film(t_world)` and rendered at its true duration. The events are **the
  same events**, so their energy in the window is whatever the world contains
  and their mean POWER falls by the clock scale. Nobody chose that; it is what
  "re-time the events" means.
* **CONTINUOUS** (R2-4064: `engine`, `tyres`). The operating point is mapped
  through `to_film` and the carrier is rendered at true frequency, so the engine
  emits at its true instantaneous power for **eight seconds of screen where the
  world contains 1.60** — and its energy in the window is multiplied by
  **1/scale = 6.5054**.

**THE SAME RULE MOVES THE TWO CLASSES' RELATIVE MEAN POWER BY 1/scale.** On the
delivered stems, over 36–44 s:

| | R2-4147 stems | R2-4151 stems |
|---|---:|---:|
| continuous / impulsive, as delivered | **−0.35 dB** | **+7.21 dB** |
| the same with the level clause applied | −8.17 dB | −0.61 dB |
| the excess, energy-weighted under the engine's own power | **7.82 dB** | 7.82 dB |
| the excess at the ramp floor | 8.13 dB | 8.13 dB |
| **the excess anywhere else in the film** | **0.00 dB** | **0.00 dB** |

**WHICH CLASS IS RIGHT, AND WHY IT IS NOT A PREFERENCE.** The impulsive class is
right *by construction*: an event is indivisible, so re-timing can neither
create nor destroy any of one. The continuous class has no events, so nothing
forced its energy to be conserved and **nothing in the file ever said what
should.** The invariant that makes the two consistent is the one the picture
already claims — *the window contains the world's own event, more slowly.* Slow
motion shows you the same 1.6 seconds; it does not show you five extra cars.

Under that invariant a continuous source rendered at true pitch on the film grid
carries `sqrt(scale)` in amplitude, because

    ∫_film p(τ)·scale(τ) dτ  ==  ∫_world p(w) dw        (dw = scale·dτ)

is a **CHANGE OF VARIABLES**, exact rather than approximate, **with no free
parameter in it.** At scale 1 it is 0.000 dB, and `clock.scale` is exactly 1.0
outside film t 35.983–43.968 s, so **it is bit-exact silent across the whole of
beat 1.**

**THE PREMISE THE CHANGE OF VARIABLES NEEDS, CHECKED AGAINST R2-4064'S OWN
WITNESS** rather than assumed: that the film-grid engine's power at film τ *is*
the world engine's at w(τ). `audio/out/witness_engine_grid.json` measures the
rpm schedule agreeing to **0.0039 rpm** and the two grids' RMS agreeing to
**0.02 dB in all four of its windows** (breach, ramp core, after the ramp, lap).

---

### R2-4152(2) — WHAT IT IS WORTH, AND THE COINCIDENCE IS STATED RATHER THAN ENJOYED

R2-4150(1)'s attribution and R2-4150(2)'s ORACLE bound, recomputed on the
delivered stems with the clause applied and nothing else changed:

| on the R2-4147 stems | as delivered | clause, SHIPPING FORM |
|---|---:|---:|
| **beat AMI** | **0.1421** | **0.1801** |
| engine share of the beat | 44.73 % | **11.91 %** |
| shards share | 36.27 % | 58.53 % |

| on the R2-4151 stems (the withheld patch) | as delivered | clause, SHIPPING FORM |
|---|---:|---:|
| **beat AMI** | **0.1810** | **0.3270** |
| engine share of the beat | **75.37 %** | 34.37 % |
| shards share | 11.29 % | 31.19 % |

*"Shipping form" means the clause on `engine` and `tyres` alone — see
R2-4152(2a). With the derived buses corrected too it reads 0.1839 and 0.3642,
and that version is not shippable.*

**AND THE FEASIBILITY BOUND MOVES WITH IT.** R2-4150(2) substituted the corpus
positive's own shower for the film's glass at the same delivered energy — an
ORACLE layer — and got **0.3031 against a 0.50 bar**, which is the measurement
that has said for three passes that *no glass layer clears the bar through this
engine.* With the clause on all of engine, tyres and the derived buses it reads
**0.4999**.

**THAT COINCIDENCE IS STATED RATHER THAN ENJOYED.** There is no free parameter
in `10·log10(clock.scale)` to have landed it on the bar; **the direction of
R2-4150(2)'s conclusion is unchanged** — a perfect glass layer still does not
clear 0.50 — and the number would be identical if the bar were 0.20.

**THE CORRECTED ORACLE BOUND LANDS AT 0.4999 AGAINST A 0.50 BAR AND THAT IS
SAID OUT LOUD RATHER THAN ENJOYED.** There is no free parameter in
`10·log10(clock.scale)` to have landed it there; **the direction of R2-4150(2)'s
conclusion is unchanged** — a perfect glass layer still does not clear the bar
through this mix — and the number would be identical if the bar were 0.20.

**AND THE COST, WHICH IS THE HALF THAT DECIDES.** On the R2-4151 stems the beat
RMS falls **5.69 dB** and the 4–8 kHz band **2.47 dB**. The engine was 44.7 % of
a beat it reads AMI 0.069 on, so the loss is not paid by the glass — but it is
paid, and **on its own it would have made R2-4151's artefact problem worse, not
better.** That is what R2-4152(3) is for.

---

### R2-4152(3) — THE SECOND INSTRUMENT. `BUS_PEAK_CEILING` WAS NEVER COMPARED TO G14, AND THE FILM WAS THROWING AWAY 2.89 dB OF ITS OWN DECLARED BUDGET. `tools/r2_4152_headroom.py`

R2-4151 left this: *"whoever takes this needs a headroom BUDGET across buses,
measured against G14's +6 dBFS and G1's 3 dB"*, and *"the real defect is that a
3-second short-term meter is the wrong instrument for a bus whose event is
0.16 ms, and there is no second instrument."*

**`BUS_PEAK_CEILING` IS NOT A BUDGET AND NEVER WAS.** It is a per-bus constant,
**it has never once been compared to G14 anywhere in this file**, and nothing in
the report has ever been able to answer *how much peak headroom does this film
have left*. The ledger answers it. Every bus's true peak as it enters the sum,
against G14's declared +6.0 dBFS premix bound:

| | R2-4147 | R2-4151 |
|---|---:|---:|
| arithmetic sum of the bus true peaks (every bus peaking on one sample) | +17.25 | +17.25 dBFS |
| **delivered premix true peak** | **+3.21** | **+3.21 dBTP** |
| coincidence κ = delivered / worst case | 0.1986 | (−14.04 dB) |
| **G14's budget left UNSPENT** | **+2.79 dB** | **+2.79 dB** |
| buses ON the ceiling | `engine`, `impact`, `shards` | same three |
| **the common ceiling G14 actually supports, SOLVED by bisection** | — | **1.3940 = +2.89 dBFS** |

**THE MIX REALISES A FIFTH OF ITS OWN WORST CASE**, so the budget is *not*
divisible by a bus count — that would be as arbitrary as the 1.0 it replaces,
in the other direction — and it has to be **solved**, which is what the limiter's
own makeup already does in this file.

**AND EXACTLY THREE BUSES SIT ON THE CEILING: `engine`, `impact`, `shards`.**
None of them makes a sound in beat 1 — the engine's ignition is at world
t = −2.30 s, i.e. film 31.7 s — so **raising the ceiling cannot move beat 1**,
and the render proves it rather than the argument.

**THE CRITERION IS ALSO MOVED INTO THE TRUE-PEAK DOMAIN**, which is the domain
of the thing it protects: G14, the delivery ceiling and the limiter are all true
peak, and a sample-domain ceiling on a 0.16 ms Hertzian contact under-reads the
inter-sample peak and over-reads nothing. Both numbers are logged per bus.

**THE VALIDATION OPEN #2 ASKS FOR — and R2-4034's own derivation names the
number.** Its text reads: *"That bus entered the sum at a linear peak of 7.50,
i.e. **+17.5 dBFS**"*. At the solved ceiling:

| case, at the level its own target asks for | PLR | TP dBTP | over budget | |
|---|---:|---:|---:|---|
| **a bus entering the sum at +17.5 dBFS** | 32.31 | +17.53 | **+14.61 dB** | **FAIL — the protection is intact** |
| `impact` where its own 3 s target puts it (linear 19.5) | 32.31 | +25.83 | +22.95 dB | **FAIL — still stopped** |
| `synth.glass_breach`, the validated positive, at the budget | 27.14 | +2.89 | 0.00 | **PASS** |

**AND THE CORPUS POSITIVE IS NO LONGER TAXED FOR BEING THE RIGHT ANSWER.**
R2-4151(2)'s indictment was that the old criterion would tax `synth.glass_breach`
**18.14 dB against 11.71 dB for the film's own bus — 6.4 dB harder on the
reference answer.** At a COMMON peak budget that asymmetry is not a penalty on
either: both land on the **same delivered true peak**, and the 4.4 dB between
them is just their raw peaks at matched loudness. **The peak criterion is not
what stops the reference answer from working. What stops it is the SIZE of the
budget, and the budget is G14, and G14 is declared and is not moved.**

**WHAT A PEAK CRITERION STILL CANNOT DO, STATED RATHER THAN GLOSSED.** A peak
carries no information about how long a bus was making a sound, so no threshold
in this domain can tell a shower of 8401 contacts from one event in 124 s of
silence — **which is the defect OPEN #2 actually named.** The instrument for
*that* is BS.1770-4's own second window:

    U  =  (max 400 ms MOMENTARY)  −  (max 3 s SHORT-TERM)

parameter-free, because both windows are the standard's and neither is this
file's, and **independent of crest**: two buses with the same PLR and different
temporal concentration get different U, which is the separation the peak
criterion cannot make at any threshold. Measured on the R2-4151 stems:

| bus | U | |
|---|---:|---|
| **`impact`** | **8.46 dB** | **the largest in the film, and R2-4034's own case** |
| `structure` | 7.68 dB | the pane, one 40 ms world event |
| `room` | 5.69 dB | |
| `assembly` | **4.53 dB** | **beat 1's own bus** |
| `shards` | 4.14 dB | a shower of 8401 contacts |
| `engine` | 1.59 dB | continuous, as it should be |
| `bed` | 0.19 dB | |

**`impact` AND `shards` HAVE THE SAME PLR TO 0.5 dB AND THE INSTRUMENT SEPARATES
THEM BY 4.32 dB.** That is the separation `BUS_PEAK_CEILING` cannot make at any
threshold — and it is a *partial* instrument, said plainly: 400 ms is itself long
against a 0.16 ms contact, so U under-reads `impact` by construction and 8.46 dB
is a floor on its mis-metering, not the size of it.

**IT IS MEASURED HERE AND DELIBERATELY NOT APPLIED**, for a reason the table
itself gives: **`assembly` reads 4.53 dB**, so subtracting U from every bus's
target would move **beat 1**, and beat 1 is picture-locked. It is the next pass's
tool and it now has its numbers.

---

### R2-4152(2a) — WHERE THE CLAUSE GOES IN THE CHAIN, AND THE TRAP THAT DECIDED IT

Physically the clause is emission-side and belongs on `eng_f` before
propagation. **It is applied AFTER the bus trim instead, and the reason is a
measurement.**

`add()` re-normalises every bus to its declared `TARGET_LUFS_S` measured on that
bus's **own loudest 3 s window**. For every bus whose loudest window is inside
the ramp, that renormalisation **hands the clause straight back and pays for it
OUTSIDE the ramp.** Measured on the R2-4151 stems, what the trim would have
compensated:

| bus | max short-term, delivered | with the clause | the trim would give back |
|---|---:|---:|---:|
| `aperture` | −24.00 @ 37.5 s | −32.13 | **+8.13 dB** |
| `reflect_showroom` | −23.00 @ 38.0 s | −31.13 | **+8.13 dB** |
| **`room`** | **−31.00 @ 35.0 s** | **−36.57** | **+5.57 dB** |
| `structure` | −30.00 @ 34.5 s | −31.27 | +1.27 dB |
| `reflect_garage` | −27.00 @ 47.5 s | −27.00 | 0.00 dB |

**`room` IS BEAT 1's OWN REVERB.** Applying the clause to the excitation would
have left the breach almost unchanged and made **beat 1's showroom tail 5.57 dB
louder** — a picture-locked beat moved by a beat-3 fix, silently, by exactly the
mechanism R2-4151(5) caught at `debris`.

So the clause is applied post-trim to **the two buses that are continuous
world-attached sources, `engine` and `tyres`**, and the buses DERIVED from them
are left alone with the reason recorded: **their absolute entries in
`TARGET_LUFS_S` are relationships declared as absolutes** — a room tail is a
fraction of what excites it — which is R2-4151(5)'s defect in a second place.
Declaring them with `RELATIVE_TARGET_LUFS_S` against their exciters is the next
pass's item; guessing at it inside an engine fix is not. **This costs the beat:
the full clause reads 0.3642 and the shipping form 0.3270.**

The delivered PEAK is unaffected either way — `engine` peaks at film t = 109.15 s
and `tyres` at 109.34 s, both outside the ramp — so the headroom ledger is exact.

---

### R2-4152(4) — WHAT WAS BUILT

Five changes, and the first four are `tools/r2_4151_landing.patch` applied
unmodified — the withheld build, landing behind the engine work exactly as
R2-4151 said it should.

1. **`layers.shard_modes`** — `GLASS_LAMINATE_ETA = 0.030` replaces Q = 800–1500.
   R2-4150(3)'s derivation, swept across the whole published band.
2. **`layers.picture_fragments` / `shard_ballistics`** — the population is read
   from `sim/out/breach_sim.json`, the partition the 4K frames came from.
3. **`layers.debris_bed`** — density is a declared TOTAL.
4. **`layers.render_shards`** — the acceleration transient references the ring's
   own peak. **`master.RELATIVE_TARGET_LUFS_S`** — `debris` 4.0 dB under
   `shards`'s DELIVERED level.
5. **`master.BUS_RAMP_LEVEL_CLAUSE`** — `sqrt(clock.scale)`, post-trim, on
   `engine` and `tyres`. R2-4152(1). **No free parameter.**
6. **`master.BUS_PEAK_CEILING` 1.0 → 1.60**, SOLVED against G14 and G1 with a
   declared 1.03 dB margin, and moved into the **true-peak** domain. The
   report now carries a `headroom_ledger` block: what each bus claims of G14's
   budget, the coincidence, and how much is left.

**NOT CHANGED, EACH FOR A STATED REASON:** G14 (+6.0 dBFS) and G1 (3 dB) — both
declared, both the things the budget is solved against, neither moved; the
meter-validity limb U — measured, not applied, because `assembly` reads 4.53 dB
and beat 1 is picture-locked; the contact-time law (R2-4151(1)); `part_impacts`'
`amp.sum()` reference (beat 1); `audio/verify.py` and `tools/percept_matrix.py`;
`TARGET_LUFS_S`'s entries; `reflect_showroom`/`aperture`'s levels (R2-4151 OPEN
#6, still nobody's).

---

### R2-4152(5) — THE PREDICTIONS, WRITTEN DOWN BEFORE THE RENDER WAS ADJUDICATED

Recorded before `tools/percept_matrix.py` was run on the new master. Every one
has a number. **The last two passes reported four wrong and one partly, with the
headline wrong both times.**

1. **`shards` delivered LUFS-S −12.89 (R2-4147) / −19.77 (R2-4151) → −15.9
   ± 0.5**, still peak-criterion-won, still about 6.9 dB short of its −9.0
   target. **`debris` → −19.9 ± 0.5** (R2-4147: −14.12).
2. **`engine` becomes LUFS-LIMITED FOR THE FIRST TIME and reaches its declared
   −10.0 LUFS-S**, because the clause is post-trim so its meter still reads the
   breach. Trim +17.91 → **+19.46 dB**; delivered engine **−6.3 ± 0.5 dB in the
   breach** and **+1.55 dB on the flying lap** against R2-4147.
3. **Premix true peak +4.8 to +5.3 dBFS, G14 PASS with at least 0.7 dB of
   margin; limiter GR −0.6 to −1.0 dB, G1 PASS.** The offline chain said +4.97
   and −0.75, and the true-peak criterion is slightly tighter than the sample
   one, so the render should land at or under that.
4. **G-PRESENCE `3_breach` AMI 0.1409 (R2-4147) / 0.1710 (R2-4151) → 0.28–0.38,
   AND STILL FAIL.** The stem bench in shipping form reads 0.3270 and the
   ceiling is common-mode across `engine`, `shards`, `debris` and `impact`, so
   the delivered number should sit near it. **A PASS here would mean the bench
   is wrong, not that the build is good.**
5. **G-BALANCE `3_breach` protagonist margin +4.13 (R2-4147) / −0.14 (R2-4151)
   → +6 to +10 dB, AND IT MAY PASS THE +8.0 BAR FOR THE FIRST TIME.** `3_breach`'s
   protagonists are declared as `shards`, `structure`, `impact` — **not the
   engine** — so this pass raises the protagonist 4.08 dB and drops the largest
   thing that was not one by 6.3 dB. This is the limb R2-4151 predicted would
   not recover and was judged on.
6. **G-BALANCE `3_breach` near-white share: the line stays GONE.**
   `reflect_showroom` and `aperture` are the near-white background, they are
   NOT corrected and NOT raised, and the protagonist is +4.08 dB.
7. **G-EVENT `3_breach` 2.71 (R2-4147) / 3.27 (R2-4151) → 4.5–7.0 dB, still far
   under the 13.7 bar.** The engine was filling the troughs.
8. **THE BREACH'S 4–8 kHz BAND: R2-4151 was 3.60 dB DARKER than R2-4147 and
   that is why it was withheld. → −0.5 to +1.5 dB.** `debris` follows `shards`
   up 4.08 dB and the bed is unchanged.
9. **BEAT 1 IS IDENTICAL — a pure gain, residual at least 80 dB down.** No bus
   that sounds in beat 1 is peak-limited, so the ceiling cannot reach it, and
   `clock.scale` is exactly 1.0 across the whole of it, so the clause is
   bit-exact 0.000 dB. **If this one is wrong the pass is over.**
10. **BEATS 4–6: the engine is +1.55 dB and `debris_p80_x_m` moves 30.15 →
    23.14 m.** `4_transit` and `5_lap` declare the ENGINE as protagonist, so
    their G-BALANCE margins should IMPROVE. **I predict `4_transit` stays better
    than R2-4147 on all three of G-BALANCE, G-FLAT and G-HNR.**
11. **NO GATE'S FILM-LEVEL VERDICT FLIPS**, and no failure line appears that was
    not there in R2-4147.

---

### R2-4152(6) — THE RENDER

`audio/out/r2_4152/master_R2-4152.wav`, **−23.00 LUFS / −1.10 dBTP, limiter GR
−2.65 dB, premix true peak +4.49 dBTP, `AUDIO_MASTER_OK`.** G14 PASS with
**1.51 dB of its budget left**; G1 PASS with 0.35 dB of margin.
`tools/percept_matrix.py` returns `PERCEPT_MATRIX_OK`, 40 thresholds, 0
provenance violations, G-CONSTRUCT unchanged at its 17 pre-existing violations
with none in the new code.

**EVERY BUS IN THE FILM IS BIT-IDENTICAL TO R2-4147 EXCEPT FOUR.**

| bus | R2-4147 | R2-4151 | **R2-4152** | |
|---|---:|---:|---:|---|
| `engine` | −11.54 | −11.54 | **−10.00** | **LUFS-limited for the first time — it reaches its declared target** |
| `shards` | −12.88 | −19.77 | **−15.69** | peak-limited, now by 6.69 dB instead of 10.77 |
| `debris` | −14.12 | −23.77 | **−19.69** | follows `shards` at −4.0 |
| `impact` | −32.31 | −32.31 | **−28.25** | +4.06, the ceiling |
| every other bus | — | — | **identical trim, to 0.01 dB** | |

**THE ENGINE CAME OFF THE CEILING**, which is the mechanism R2-4152(5)#2
predicted: with the clause applied post-trim its meter still reads the breach,
so it asks for +19.46 dB, and at a ceiling of 1.60 the peak criterion no longer
undercuts that. `buses_on_the_ceiling` is now **`impact`, `shards`** — the two
event buses, and nothing else.

**AND `audio/verify.py` RETURNS `AUDIO_VERIFY_FAIL`, WHICH IT ALSO DOES ON THE
SHIPPED MASTER.** The failing limb is the Doppler station at film t = 106.76 s
(1 PASS / 1 FAIL / 1 INAPPLICABLE). **Re-run on `master_R2-4147.wav` this pass,
read-only, it returns the identical 1/1/1 and the identical `doppler: false`.**
It is pre-existing, it is not caused by this pass, and it is not fixed by it.

---

### R2-4152(7) — THE ADJUDICATION. `tools/r2_4150_matrix_diff.py`, R2-4147 AGAINST R2-4152

**NO GATE'S FILM-LEVEL VERDICT MOVED. FOUR FAILURE LINES AND TWO
INAPPLICABLE-FOR-NO-COVERAGE LINES DISAPPEARED; ONE INAPPLICABLE APPEARED.**

| | R2-4147 | R2-4151 | **R2-4152** | |
|---|---:|---:|---:|---|
| **G-PRESENCE `3_breach` AMI** | **0.1409** | 0.1710 | **0.3769** | **2.67×**, bar 0.50 |
| **G-EVENT `3_breach`** | **2.71 dB** | 3.27 | **7.62 dB** | **2.81×**, bar 13.7 |
| G-ROOM `3_breach`(c) cepstral 23.26× | FAIL | GONE | **GONE** | the rings are gone |
| G-ROOM `3_breach`(c) ripple 12.40 dB | FAIL | GONE | **GONE** | |
| G-ROOM `3_breach`(b) 0 usable bursts | INAPPL | — | **GONE** | **coverage GAINED** |
| G-GESTURE `3_breach` 0 bursts | INAPPL | — | **GONE** | **coverage GAINED** |
| G-RING `5_lap` 1796 Hz rings 1.51× | FAIL | — | **GONE** | |
| **G-BALANCE `3_breach` margin** | **+4.13** | −0.14 | **+3.06 dB** | **1.07 dB WORSE** |
| **G-BALANCE `3_breach` near-white share** | **0.474** | GONE | **0.660** | **WORSE, and the line is back** |
| G-BALANCE `4_transit` | −2.30 | −0.93 | **+0.43 dB** | +2.73 |
| G-BALANCE `5_lap` | −3.10 | — | **−1.55 dB** | +1.55 |
| G-BALANCE `6_ending` | −22.04 | — | **−20.49 dB** | +1.55 |
| G-FLAT `4_transit` | 0.700 | 0.662 | **0.627** | |
| G-HNR `4_transit` | 0.675 | 0.624 | **0.497** | |
| G-HNR `5_lap` | 0.697 | — | **0.651** | |
| G-ORDER `4_transit` / `5_lap` | 0.194 / 0.187 | — | **0.208 / 0.194** | |
| G-ROOM `5_lap`(c) cepstral | 6.09× | — | **5.71×** | |
| G-NOVEL `1_assembly` | r 0.413 | — | **r 0.408** | the only beat-1 line, and see (8) |

**THE ONE NEW LINE** is `G-ROOM 3_breach(c ripple): 0 usable decay tails` — the
same INAPPLICABLE R2-4151 produced, and for the same reason: **it replaces two
FAILURES with a loss of coverage, because a fragment at the laminate's own loss
factor does not ring for 0.6 s any more and there is no decay tail left to
measure.** G-ROOM(c)'s two bars sit below their own nulls and are OPEN
(R2-4149); this pass does not tune to them and does not claim the change as a
win.

**THE TWO REGRESSIONS ARE REAL AND THEY ARE THE SAME REGRESSION.** With the
engine 6.59 dB down in the beat, what is LEFT is more near-white than it was —
the share limb is mechanical and it says so, 0.474 → 0.660. And the margin limb
falls 1.07 dB because `shards`, its dominant protagonist, is still 2.80 dB below
where R2-4147 had it. **R2-4151 OPEN #6 named the cause and nobody has acted on
it**: `reflect_showroom` and `aperture` are 61 % of that background, R2-4054
wrote the rule for them — *"if they still measure more than 15 dB under the mix
after this, they should be deleted rather than raised again"* — and they are
untouched by this pass, deliberately, because a level change to two background
buses inside an engine fix is exactly the confound this file keeps catching.

---

### R2-4152(8) — THE ARTEFACT TEST, WHICH IS WHAT DECIDES. `tools/r2_4152_artefact.py`

R2-4151 improved its adjudication and was withheld anyway, on three measured
statements about the film rather than about the gate. **THE SAME THREE, IN THE
SAME UNITS, ON THE DELIVERED MASTERS:**

| R2-4151's indictment | R2-4151 | **R2-4152** |
|---|---:|---:|
| **the breach, 4–8 kHz, against the master it replaces** | **−3.64 dB** | **−0.27 dB** |
| the breach, 8–16 kHz | −1.77 dB | **+0.57 dB** |
| **the glass** (`shards` delivered LUFS-S) | **−6.88 dB** | **−2.80 dB** |
| **the engine's share of the beat** (44.73 % as shipped) | **79 %** | **28.06 %** |

**THE BAND THE CLIENT HAS REJECTED A MASTER OVER IS NOT DOWN.** And the
breach's SPECTRAL BALANCE — each band against that beat's own broadband, which
is the measure of "darker" that survives a level change:

| relative to the beat's own broadband | R2-4147 | R2-4151 | **R2-4152** |
|---|---:|---:|---:|
| 1–4 kHz | −4.13 | −3.26 | −4.45 dB |
| **4–8 kHz** | **−12.56** | −15.36 | **−10.19 dB** — **2.37 dB brighter than shipped** |
| **8–16 kHz** | **−21.77** | −22.71 | **−18.57 dB** — **3.20 dB brighter** |

**WHAT IS DOWN IS THE MIDDLE, AND THAT IS THE POWER UNIT LEAVING.** 200 Hz–4 kHz
falls about 3 dB in absolute terms, which is where a firing comb at 690 Hz and
its orders live. 0–200 Hz is +0.70 dB.

**THE BEAT LEVELS, WHOLE FILM, DELIVERED** (dBFS RMS):

| beat | R2-4147 | R2-4151 | **R2-4152** |
|---|---:|---:|---:|
| `1_assembly` | −35.17 | −34.88 | **−35.08** |
| `2_launch` | −21.79 | −21.51 | −20.99 |
| **`3_breach`** | **−22.05** | −22.84 | **−24.52** |
| `4_transit` | −35.30 | −34.90 | **−32.32** |
| `5_lap` | −29.63 | −28.97 | **−28.58** |
| `6_ending` | −36.53 | −36.23 | −37.23 |

**THE BREACH IS 2.47 dB QUIETER AND THAT IS THE COST, STATED PLAINLY.** It is
paid by a bus that was 44.7 % of a beat it reads AMI 0.069 on, and it buys the
2.67× on articulation and the 2.81× on eventfulness. Beats 4 and 5 are
**2.98 dB and 1.05 dB LOUDER**, because the film's own programme gain no longer
has to cut 3.04 dB to hold a breach that was delivering 6.5× the world's engine
energy — `program_gain.min_db` moves −3.04 → **−1.54 dB**.

**AND BEAT 1, WHICH IS PICTURE-LOCKED.** Block by block, NEW against OLD:

    film t  0 - 31 s      +0.043 dB, CONSTANT TO THREE DECIMALS IN EVERY BLOCK
    film t 31 - 33 s      +0.43 to +1.54 dB
    film t 33 - 36 s      +1.58 to +0.08 dB   (beat 2, the launch)

**BEAT 1'S ASSEMBLY CELL IS A PURE GAIN OF +0.043 dB FOR 31.7 OF ITS 33
SECONDS**, and every beat-1 bus's trim is identical to R2-4147's to 0.01 dB. The
last 1.3 s is not: **the engine's ignition is at world t = −2.30 s, i.e. film
t = 31.70 s**, and the engine is +1.55 dB because it reached its declared target.
That is a real change inside beat 1's declared span and it is **the engine
starting, not the cell.** One beat-1 gate number moves with it — G-NOVEL
`1_assembly` r 0.413 → 0.408, in the improving direction — and no beat-1 verdict
changes. **`world/beat1_anim_anim.json` was not opened and no video was
re-rendered.**

**THE VERDICT: THIS SHIPS.** Not because three gate lines went — R2-4151 had
that and was withheld — but because the three things the film was withheld ON
are answered: **the top end is level-to-brighter, the glass is 2.80 dB down
instead of 6.88 and it is a completely different bus (its own AMI 0.2565 →
1.1107, its energy above 4 kHz 0.15 % → 6.46 %), and the engine is 28 % of the
breach against 44.7 % in the master it replaces.**

---

### R2-4152(9) — THE PREDICTIONS FROM R2-4152(5), SCORED

**Six right, three wrong, two partly — and one of the wrong ones is the limb the
previous pass was judged on, for the third consecutive pass.**

1. **`shards` → −15.9 ± 0.5, `debris` → −19.9 ± 0.5. RIGHT** — −15.69 and
   −19.69, both inside the band.
2. **`engine` becomes LUFS-limited, reaches −10.0, trim +17.91 → +19.46, and is
   −6.3 dB in the breach / +1.55 dB on the lap. RIGHT, exactly** — trim +19.46,
   delivered −10.00, engine LUFS-S in the breach −11.54 → −18.13 (−6.59 dB).
3. **Premix +4.8 to +5.3 dBFS, GR −0.6 to −1.0 dB, both PASS. PARTLY RIGHT AND
   THE GR IS BADLY WRONG** — premix **+4.49 dBTP** (0.31 dB outside, in the safe
   direction) and GR **−2.65 dB** against a predicted −0.75. **THE OFFLINE
   CHAIN REPRODUCES THE PREMIX PEAK TO 0.5 dB AND THE LIMITER'S GAIN REDUCTION
   TO ONLY 1.9 dB.** Both thresholds PASS and G1 had 0.35 dB left, but **a
   0.35 dB margin on a declared threshold was not what the sweep promised**, and
   the sweep is what the ceiling was chosen from. That is a third instrument in
   this chain that mis-sized an effect it was built to size.
4. **G-PRESENCE `3_breach` AMI 0.28–0.38, AND STILL FAIL. RIGHT** — 0.3769,
   inside the band, and it still fails the 0.50 bar.
5. **G-BALANCE `3_breach` margin +6 to +10 dB and it may PASS. WRONG, AND
   WRONG IN DIRECTION** — **+3.06 dB**, i.e. 1.07 dB WORSE than R2-4147 rather
   than 2 to 6 dB better. The reasoning named the right mechanism (the engine is
   not a protagonist of this beat) and missed that the engine is not in the
   BACKGROUND set either, so removing it does nothing for the ratio — while
   `shards`, the protagonist that matters, is still 2.80 dB below R2-4147.
6. **Near-white share: the line stays GONE. WRONG, AND IT IS THE WORST NUMBER IN
   THE PASS** — 0.474 → **0.660**. Same error as #5, in the denominator: taking
   6.59 dB out of the one large bus that is NOT near-white raises the near-white
   share of what is left, mechanically. **I predicted a limb would stay clear on
   a mechanism I had not checked the definition of.**
7. **G-EVENT `3_breach` 4.5–7.0 dB. WRONG, AND BETTER THAN PREDICTED** —
   **7.62 dB** against R2-4147's 2.71.
8. **The breach's 4–8 kHz −0.5 to +1.5 dB. RIGHT ON THE DELIVERED MASTER**
   (−0.27 dB) **AND WRONG ON THE STEM SUM** (−3.96 dB). The two disagree by
   3.7 dB because the stem sum is pre-limiter and pre-programme-gain. **The
   delivered master is what the client hears and it is the one that decides**,
   and this pass is only entitled to say that because it measured both and said
   which. R2-4151's −3.60 dB was a delivered-master number, so the comparison in
   R2-4152(8) is like for like.
9. **BEAT 1 IS IDENTICAL — a pure gain, residual ≥ 80 dB down. PARTLY RIGHT, AND
   THE PART THAT IS WRONG IS STATED RATHER THAN ROUNDED AWAY.** A single
   best-fit gain over 0–33 s leaves a residual only **30.1 dB** down, which by
   the test I wrote would have ended the pass. Block by block it is **+0.043 dB,
   constant to three decimals, for 0–31 s** — and then +0.43 to +1.54 dB over
   31–33 s, because **the engine's ignition is at film t = 31.70 s** and the
   engine is +1.55 dB. The assembly cell is untouched, every beat-1 bus trim is
   identical to 0.01 dB, and the one beat-1 gate number moves 0.413 → 0.408. **A
   whole-beat residual test could not tell "beat 1 moved" from "beat 2 starts
   1.3 s inside beat 1", and it took a block-wise measurement to say which.**
10. **BEATS 4–6 improve on G-BALANCE, G-FLAT and G-HNR at `4_transit`. RIGHT** —
    −2.30 → +0.43 dB, 0.700 → 0.627, 0.675 → 0.497, and `5_lap` and `6_ending`
    improve too. Beats 4 and 5 are also 2.98 dB and 1.05 dB LOUDER.
11. **No verdict flips, no new failure line. RIGHT ON THE VERDICTS AND WRONG ON
    THE LINES** — G-BALANCE `3_breach`'s near-white line, which R2-4151 had
    cleared, is back.

---

### DELIVERY

**`PART2_AUDIO_MASTER_R2-4152.wav` IS THE DELIVERY.** Both films re-muxed
`-c:v copy`, **video stream md5s taken before and after and verified
byte-identical by the landing script, which refuses if either moves**: ProRes
`c346a7a322a4a2a403727c1e85f17511`, H.265 `235ef36e844a62b0e303e4138907b9fa`.
Both 124.083333 s. `watch/INDEX.md` updated. `watch/listen_2026-08-14/` re-cut
with **NEW = R2-4152, OLD = R2-4147** — the breach clip is the pass and the
beat-1 clip is the control arm — and every clip's audio was cross-correlated
against the master it claims (r ≥ 0.9978). `CLIPS_OF.json` is accurate.

**`audio/out/master.wav` and `watch/rejected_audio_R2-4079/` are untouched and
both still fail.** `audio/verify.py` and `tools/percept_matrix.py` are untouched.
`world/beat1_anim_anim.json` was not opened and no video was re-rendered.

**ONE FILE IS WRITTEN AND NOT STAGED:** `watch/listen_2026-08-14/CLIPS_OF.json`
is held by a live `gitguard` lease belonging to `r2-4147-audio-presence`. The
file on disk is correct and the clips are correct; the commit does not contain
it, because taking another agent's leased path is the thing the guard exists to
stop and there is no `--force`. Whoever holds that lease should stage it.

---

## OPEN, AFTER R2-4152

1. **G-BALANCE `3_breach` IS NOW THE BREACH'S WORST LIMB AND ITS CAUSE HAS BEEN
   NAMED FOR TWO PASSES.** Near-white share 0.660 against a 0.25 bar, margin
   +3.06 against +8.0. `reflect_showroom` and `aperture` are 61 % of that
   background and sit 14.8 and 15.1 dB under the beat; **R2-4054 wrote the rule
   — *"if they still measure more than 15 dB under the mix after this, they
   should be deleted rather than raised again"* — and nobody has applied it.**
   Applying it is a mix change and belongs in its own pass, with the A/B.
2. **THE OFFLINE CHAIN MIS-SIZED THE LIMITER BY 1.9 dB.**
   `tools/r2_4152_headroom.chain` reproduces `master.py`'s post-premix chain and
   predicted GR −0.75 where the render delivered −2.65. G1 passed with 0.35 dB
   to spare and the ceiling was chosen off that sweep. **Anyone raising
   `BUS_PEAK_CEILING` further must fix the reproduction first**, because the
   next dB is inside the error bar. G14 the sweep got right to 0.5 dB.
3. **THE METER-VALIDITY LIMB IS BUILT, MEASURED AND NOT APPLIED.**
   `U = maxMomentary(400 ms) − maxShortTerm(3 s)`, parameter-free, crest-
   independent, and it separates `impact` (8.46 dB, one event in a 124 s film)
   from `shards` (4.14 dB, a shower of 8401 contacts) which no peak threshold
   can. **It is not applied because `assembly` reads 4.53 dB and beat 1 is
   picture-locked.** It is also a PARTIAL instrument: 400 ms is long against a
   0.16 ms contact, so 8.46 dB is a floor on `impact`'s mis-metering.
4. **`TARGET_LUFS_S` HAS MORE RELATIONSHIPS DECLARED AS ABSOLUTES.** R2-4151(5)
   found `debris` and fixed it with `RELATIVE_TARGET_LUFS_S`. R2-4152(2a) found
   four more by measurement: `aperture`, `reflect_showroom`, `room` and
   `structure` are the room's and the facades' response to sources, and their
   absolute targets renormalise any change to those sources straight back —
   **+8.13, +8.13, +5.57 and +1.27 dB.** That is why the ramp clause could not
   be applied to them, and it is worth 0.3270 against 0.3642 on the beat.
5. **`mix_trim_db` AND THEREFORE G15's LIST MOVED BY 4.08 dB AND IT IS AN
   ARTEFACT OF THE CEILING.** `mix_trim_db = g_db − g_peak` is defined against a
   version of the bus normalised to `BUS_PEAK_CEILING`, so raising the ceiling
   shifted every bus's number by the same 4.08 dB and put four more buses on
   G15's list. **G15 is `asserted: False`, report-only, and cannot fail a
   build**, so nothing is hidden by this — but the metric should be defined
   against 0 dBFS, which is what its own comment says it means. One line.
6. **THE ENGINE'S REPORTED `delivered_lufs_s` DOES NOT INCLUDE THE RAMP CLAUSE.**
   `add()` records `meas + trim`, and the clause is applied after. The STEMS do
   include it, so every measurement in this entry is of the real thing, but the
   report's number for `engine` reads −10.00 where the breach delivers −18.13.
7. **`audio/verify.py`'s DOPPLER GATE FAILS ON THE SHIPPED MASTER AND ON THIS
   ONE**, identically: 1 PASS / 1 FAIL / 1 INAPPLICABLE, the failing station at
   film t = 106.76 s where the predicted Doppler span is only 1.41 semitones.
   Measured read-only on `master_R2-4147.wav` this pass. Pre-existing, untouched,
   and nobody's.
8. **THE CONTACT-TIME LAW IS STILL WRONG BY 3.4× AND STILL WORTH NO LEVEL**
   (R2-4151(4)); **the audio still throws its debris six times too far**
   (R2-4150(6)); **`ACCEL_NOISE_RATIO` is still the one underived number in the
   shard synthesiser** (R2-4151(5)).
9. Carried unchanged: G-RING's ratio bar under its own null; G-RING's Sabine
   limb un-anchored; AMI's and G-EVENT's shared hole; G-ROOM(c)'s two bars under
   their nulls — **and G-ROOM(c) at `3_breach` is now INAPPLICABLE for want of a
   decay tail, which is a loss of coverage and is not claimed as a win**;
   **G-MOD and G-NOVEL at beat 1 remain PICTURE.**
