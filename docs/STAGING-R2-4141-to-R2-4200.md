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
