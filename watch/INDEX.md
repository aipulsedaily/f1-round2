# What is in this folder, and which of it is a claim about the film as it stands

**Everything in `watch/` is a claim about the current film whether it was meant
as one or not.** This project has now twice had a client judgement formed
against an artefact that was out of date — the audio clips that were 2.5 hours
behind their master, and `PART2_opening_53s.mp4`, which is a camera that had
already been replaced when it was watched. Both were labelled correct *at the
moment they were cut* and neither was labelled at all afterwards.

So this file exists to say, per artefact, **what it shows and whether it is
still true.** It is written by dates that can be checked, not by memory.

---

## CURRENT — safe to judge the film by

| file | cut | shows |
|---|---|---|
| **`PART2_THE_FILM_4K_ProRes422HQ.mov`** | **08-15 00:32** | **THE FILM. The whole of part 2, one unbroken 4K shot.** 3840x2160, 24 fps, **2,978 frames = 124.0833 s, zero cuts**, 512 spp, AgX / look None / exposure -3.628, SDR. ProRes 422 HQ, **11.25 GB**. Rendered from `render/film25_breach.blend` (sha16 **`1d2aa2d86533574e`**) on world `assembly15`, frames 1-2978 on three rented RTX 5090s over 2026-08-09 to 08-13. **AUDIO REBUILT 08-15 — now R2-4152** — carries `PART2_AUDIO_MASTER_R2-4152.wav`, muxed `-c:v copy`. **The picture is unchanged and that is proven, not assumed: the video stream's md5 is `c346a7a322a4a2a403727c1e85f17511` before and after the re-mux.** **This is the delivery master.** |
| **`PART2_THE_FILM_4K_h265.mp4`** | **08-15 00:32** | **The viewing copy of the same film**, same 2,978 frames, same new audio. 3840x2160, 24 fps, 124.0833 s, H.265 `hvc1`, faststart, **880 MB**, AAC 192 kbps. Video stream md5 `235ef36e844a62b0e303e4138907b9fa`, identical before and after the re-mux. Use this to watch; use the ProRes to grade or cut. |
| **`PART2_AUDIO_MASTER_R2-4152.wav`** | **08-15 00:32** | **The audio master the two films carry.** 124.083333 s, 48 kHz, 24-bit stereo, **-23.00 LUFS / -1.10 dBTP** (EBU R 128), limiter gain reduction **-2.65 dB**. The **seventh** master. **What changed is the BREACH and only the breach.** The showroom's glazing is laminated — 5 mm HS / 1.5 mm PVB / 5 mm HS, declared in `sim/out/fracture_wall.json` — and the audio had been ringing every fragment of it at a loss factor BELOW monolithic float glass, 995 contacts a second each ringing 0.6 s, which is a wash and not a shatter. The fragments are now the picture's own 3,216 shards read out of the same fracture the 4K frames were rendered from, median 21 mm against the 351 pieces of median 321 mm the audio was inventing. And the power unit stops outweighing what it is destroying: the shot is 1.6 s of world over 8 s of screen, and a continuous source rendered at true pitch on the film grid was delivering 6.5x the world's energy while the glass delivered the world's. **Beat 1 is a pure gain of +0.043 dB and its cell is untouched.** See the section below. |
| `PART2_AUDIO_MASTER_R2-4147.wav` | 08-14 19:45 | **SUPERSEDED, kept as the arm of the current A/B.** The sixth master. Its beat 1 is the assembly cell the client can hear, and that cell is CARRIED FORWARD UNCHANGED into R2-4152 — this arm exists so the breach can be compared against it. -23.00 LUFS / -1.12 dBTP. |
| `PART2_AUDIO_MASTER_R2-4141.wav` | 08-14 17:50 | **SUPERSEDED, kept as the arm of the current A/B.** The fifth master, rejected on hearing: *"now beat 1 i dont hear anything until the tubes play"*. Measured cause: between the part impacts its beat 1 reached 26.4 dB SPL at domestic playback, **0 of 29 third-octave bands over threshold**. |
| **`listen_2026-08-14/`** | **08-15 00:37** | **The A/B for this rebuild, and the thing to actually play.** Four clips, 1280x720, cut from the delivered H.265 with the two masters muxed against identical picture: `NEW_`/`OLD_beat1_showroom_34s.mp4` (film t 0-34 s) and `NEW_`/`OLD_breach_glass_14s.mp4` (t 34-48 s). **NEW is R2-4152, OLD is R2-4147.** **The breach clip is the pass**; the beat-1 clip is the CONTROL ARM and the two should be indistinguishable there. `CLIPS_OF.json` records both sha16s and the in-points, and each clip's audio was cross-correlated against the master it claims (r >= 0.9978). **No per-clip normalisation**: both masters are -23.0 LUFS integrated, so this is a comparison of content, not of gain. |
| `AFTER_beat5_doppler_4s.mp4` | 08-08 08:20 | **R2-2161, the beat-5 framing fix.** f2340-2439 (t 97.5-101.6 s), 100 frames, 1280x720, 24 fps. The doppler pass. The car is placed **off-centre and travels across the frame**; beat 5's frame-offset is **0.754** against a 0.92 bound. Built from `render/r22161_after.blend`, whose camera path is bit-identical to the gated rig `7fc6d688…`. |
| `BEFORE_beat5_doppler_4s.mp4` | 08-08 08:17 | its matched BEFORE, same 100 frames, same resolution, same 64 samples, same DOF. The shipped camera, which pins the car near **frame centre** the whole way — frame-offset **0.055**. From `render/film22.blend`, camera path `363e4e88…`, the sha `docs/LIVE-CAMERA.md` declares. |
| `AFTER_opening_18s.mp4` | 08-08 01:36 | the opening tempo pass (R2-1606). The most recent camera deliverable. |
| `BEFORE_opening_18s.mp4` | 08-07 17:52 | its matched BEFORE. Correctly named. |
| `audio/` | 08-08 03:14 | re-cut from the master; `audio/INDEX.md` explains the earlier staleness and states it is fixed. |

### CLIENT DECISION 2026-08-15: THE FILMS CARRY THE ORIGINAL AUDIO. Read this first.

**Both films above carry `audio/out/master.wav` (md5 `d5087fd021b5f748f176ecb2b6c1de67`) — the audio
that shipped with the render.** The client heard the rebuilds and ruled: *"orginal audio was better
go back to orgininal audio"*. Done, and **not to be re-litigated by a later pass.**

**Five rebuilt masters exist and none is in the delivery:**

| master | client verdict |
|---|---|
| **`audio/out/master.wav`** | **DELIVERED — the client's choice** |
| R2-4079 — `rejected_audio_R2-4079/` | *"worse, sounds like a shitty musical"* |
| R2-4141 — `PART2_AUDIO_MASTER_R2-4141.wav` | *"beat 1 i dont hear anything until the tubes play"* |
| R2-4147 — `PART2_AUDIO_MASTER_R2-4147.wav` | superseded before judgement |
| R2-4152 — `PART2_AUDIO_MASTER_R2-4152.wav` | heard; the original preferred |

**The video was never touched through any of it.** Every mux and every revert re-verified the video
stream md5 — ProRes `c346a7a322a4a2a403727c1e85f17511`, H.265 `235ef36e844a62b0e303e4138907b9fa` —
and both read those values now. The 2,978 delivered frames are unchanged since the render.

**The rebuilds and their measurements are KEPT, not deleted.** Several findings below are
load-bearing for any future attempt: the varispeed warp transposing the breach 6.51x down, the
K-weighted gain meter deaf to the frequencies the mix was made of, the limiter removing 22 dB while
reporting 0.124, the limiter ducking 161 ms *before* each transient, and the four separate stages
that each independently pushed the film toward smooth.

**But the single most important finding in this file is this: five successive rebuilds each measured
better than the last, and the client rejected every one by ear.** Any future pass should treat that
as the primary evidence — not as a reason to try a sixth with the same instruments.

### THE AUDIO OF 2026-08-15 (R2-4152) — SUPERSEDED BY THE DECISION ABOVE, KEPT FOR THE RECORD

**THE BREACH WAS THE FILM'S LARGEST REMAINING AUDIO DEFECT AND TWO PASSES BUILT THE FIX AND
REFUSED TO SHIP IT** — R2-4150 and R2-4151 both improved their gate score and both measured
that the film would have SOUNDED WORSE, because the mix threw the improved glass 8.4 dB away
and the power unit ended up 79 % of the beat. R2-4152 found why, and it was not a mix taste:

* **THE GLAZING IS LAMINATED AND NO LINE OF THE AUDIO HAD READ THAT.** A 5 mm / 1.5 mm PVB /
  5 mm section is a constrained-layer damping sandwich, which is the entire acoustic reason
  laminated glazing is specified. The audio rang it at Q = 800-1500. At the laminate's own
  published loss factor the shard layer's articulation index goes **0.2565 -> 1.1107** against
  a validated physics positive's 0.7857, and its energy above 4 kHz goes **0.15 % -> 6.46 %**.
* **THE FRAGMENTS ARE NOW THE PICTURE'S.** `sim/out/breach_sim.json` is the partition the 4K
  frames were rendered from — 3,216 shards, median 21 mm. The audio was drawing its own: 351
  pieces, median 321 mm, minimum 40 mm. An order of magnitude out in count AND in size, in
  both directions at once.
* **AND THE POWER UNIT WAS DELIVERING 6.5x THE WORLD'S ENERGY.** Beat 3 spends 8 s of screen
  on 1.6 s of world. A shower of impacts re-timed by that map keeps its energy and loses
  power, because the events are the same events. A continuous source rendered at true pitch
  does not — it plays for eight seconds. The same rule moved the two apart by **7.82 dB**, and
  the correction is `sqrt(clock.scale)`, a change of variables with no free parameter, which
  is **exactly 0.000 dB everywhere outside 36-44 s.**

**WHAT IT IS WORTH, ON THE DELIVERED MASTERS.** The breach's articulation index **0.1409 ->
0.3769**; its eventfulness **2.71 -> 7.62 dB**; the engine **44.7 % -> 28.1 %** of the beat.
Four failure lines gone and none added. **The 4-8 kHz band the client has rejected a master
over is 0.27 dB down in absolute terms and 2.37 dB UP relative to the beat**, and 8-16 kHz is
up on both measures. Beats 4 and 5 are 2.98 dB and 1.05 dB LOUDER, because the film's own
programme gain no longer has to cut 3 dB to hold that breach down. The breach itself is
2.47 dB quieter and that is the cost, paid by the bus that was 44.7 % of a beat it reads 0.069
on. **`docs/STAGING-R2-4141-to-R2-4200.md` R2-4152 has every number and every prediction that
was wrong.**

### THE AUDIO OF 2026-08-14 (R2-4147) — THE BEAT-1 REBUILD, CARRIED FORWARD UNCHANGED

**R2-4141 was rejected by ear within hours of shipping: _"now beat 1 i dont hear anything
until the tubes play"_. It was the fourth rejection and the second one caused by a gate.**

**THE CAUSE WAS NOT SUBTLE AND IT HAD NEVER BEEN MEASURED.** Between the part impacts,
R2-4141's beat 1 reached **26.4 dB SPL** at domestic playback and its loudest third-octave
sat **14.0 dB BELOW the threshold of hearing in a quiet (NR-25) room — 0 of 29 bands
audible**. The cell-only stretches read **-60 LUFS-S against a -23 LUFS programme**. There
was nothing there to hear.

**WHY EVERY GATE CALLED IT CLEAN.** Every quality instrument in the suite is *relative* — it
measures structure within whatever it is handed — so **digital silence scores perfectly on
all of them**. G-EVENT in particular spans p95-p5 of the short-term level, so its p5 is
whatever lies between the events and **its best possible score is silence**: measured, the
empty beat scored 27.17 dB against a 13.7 dB bar while an *audible* machine scored 12.62 and
FAILED. The build was steered downhill into an empty beat and it arrived.

**WHAT SHIPPED NOW.**

| beat 1 | R2-4141 (rejected) | **R2-4147** |
|---|---:|---:|
| gap level vs threshold, NR-25 room | **-13.99 dB** | **+9.24 dB** |
| third-octave bands audible | **0** | **7** |
| gap SPL at domestic playback | 26.4 dB | 32.9 dB |
| G-PRESENCE (new gate) | **FAIL** | **PASS** |
| G-SUSTAIN note cover | **0.2075 FAIL** | **0.0453 PASS** |
| G-EVENT | 14.69 PASS | **14.93 PASS** |
| G-NOVEL r at the 1.04 s ladder | 0.549 | **0.413** |
| the seat ladder's own level | -30.99 dBFS | **-31.01 dBFS** (unchanged) |

**The picture-locked impacts were not touched** — the ladder is within 0.02 dB. What changed
is that the machine around them now exists for the whole beat instead of only while a cluster
is moving, and that it is **denser rather than merely louder**: the traverse's voice was a
stationary drive tone measuring an articulation index of **0.2831 against the literal hair
dryer's 0.2823**, and it is now a drag chain — a train of contacts — at **1.3711**, beside a
staging train whose rate is arithmetic off the picture (616 parts / 33.0 s = **18.7
operations per second**). A cell nine times louder passes G-EVENT *more* comfortably than the
silent one did, because short distinct events do not fill troughs.

**WHAT THIS COST, STATED PLAINLY.** G-RING's beat-1 measurement is **gone**: it had 4 usable
decay regions and now has 2, so it reports INAPPLICABLE where it previously reported FAIL
(ratio 1.529 against a 1.5 bar). You cannot measure a room's reverberation time in an
operating factory, and that is not a metaphor — ISO 3382 needs the level to fall 12 dB into a
gap. **The reverb itself was not touched in this pass** (no line of `showroom_tail` or
`fdn_reverb` changed), so the room is the same room; what was lost is the ability to read it
off the master's beat 1. G-RING still measures and still fails at `5_lap`.

**R2-4149 CLOSED THAT, AND THE ANSWER IS THAT THE MEASUREMENT WAS NOT THERE TO LOSE.** The gate
was given the control it had never had: impacts convolved with an exponential decay whose T60 is
**declared** and which is frequency-independent by construction, so the truthful answer is known
(`tools/r2_4149_ring_control.py`). It returns **0.994 of the truth** when the gaps are ≥ 1.5 s and
quiet — the estimator is excellent where it applies — and **0.41 of the truth** at beat 1's own
0.42 s gaps. Beat 1's longest continuous fall is **0.650 s** and a 2.4 s room needs 1.00 s just to
traverse ISO 3382's T20 window. **INAPPLICABLE is the correct verdict at beat 1, and it is now
correct by measurement rather than by accident.** The same control found something the gate did not
know about itself: its 1.5× narrowband bar reads **1.88 on a room that is uniform by construction**
when the gaps are short, and its estimator over-reads by up to 2.06× through an inter-event floor.
**No bar was moved** — it is declared open in `percept.py` with the numbers, as G-ROOM's already
are. The 5_lap FAIL survives its own null (1.03–1.25 there against the film's 1.515) and stands.

**THE LARGEST UN-ACTIONED AUDIO DEFECT IN THE FILM IS NOT BEAT 1 — IT IS THE BREACH.** G-PRESENCE
fails `3_breach` at an articulation index of **0.141**, and R2-4148 refused to chase it because
every positive in the corpus was a beat-1 control. R2-4149 built the missing one: 8 s of curtain
wall coming down, from the aperture's own geometry and the fracture mechanics
(`tools/r2_4149_breach_bench.py`). **A physics-true breach reads 0.697–0.775 over five seeds — it
clears the 0.50 bar comfortably, so the bar is right for this beat and was NOT moved, and the
film's 0.141 is the audio.** The ablation names what is missing: the fine dice alone — 229 000
fragments too dense for an ear to resolve — read **0.153**, which is essentially the film's number,
while the large edge pieces and the mullions read **1.314** on their own. The envelope says the
same thing in one line: **in eight seconds of a car going through a glass wall at 53.8 km/h, the
loudest instant is 6.4 dB over the median.** Beat 1 is 35.7 dB. This is a real, named, un-fixed
defect and it is listed open.

---

### THE AUDIO REBUILD OF 2026-08-14 (R2-4141) — SUPERSEDED, KEPT FOR THE RECORD

**The films above carry `PART2_AUDIO_MASTER_R2-4141.wav`.** The R2-4079 rebuild described further
down was muxed in on 08-14, played to the client, judged *"ngl audio is worse, sounds like a shitty
musical"*, and reverted; it is parked at `rejected_audio_R2-4079/`. This is the fifth master and it
replaces `audio/out/master.wav`, which the films carried in the meantime. **The video has never been
touched through any of it — md5 verified identical through every mux and the revert.**

**The client's three rejections trace an arc, and the target is the middle of it:**

```
"a wind blower"              no structure at all        TOO NOISY
"banging on tubes"           inharmonic ringing         WRONG STRUCTURE
"a shitty musical"           sustained pitch            TOO MUCH STRUCTURE
```

**A machine is percussive, inharmonic, transient-dense and UNPITCHED — periodic in rhythm, never in
pitch.** Beat 1's bed used to be a sustained voice: fifteen actuator oscillators (which summed to
noise, the hair blower) and then, in an unshipped build, one geared line shaft (which summed to a
drone, and measured note cover 0.233 / chord cover 0.210 on its own). Both are gone. The showroom is
now **45 traverses that glide and stop, 90 pneumatic exhausts, 90 latch strikes, 15 nut runners and
228 pawl impacts**, all on the picture's own move list out of `docs/beat_sheet.json`, plus one
rolling bed at 3 % of the event level. Nothing in it runs longer than a move.

**Beat 1, against the master the films carried this morning:**

| gate at beat 1 | `master.wav` (was) | R2-4141 (now) | |
|---|---|---|---|
| **G-EVENT** — is it events or a bed | **FAIL** 13.25 dB | **PASS** 14.69 dB | the anti-hair-dryer instrument |
| **G-GESTURE** — do the bursts differ | **FAIL** worst pair 0.808 | **PASS** | |
| **G-BALANCE** protagonist margin | **FAIL** -0.57 dB | **PASS** +11.28 dB | the cell now leads the mix |
| **G-RING** vs the room's Sabine RT60 | **FAIL** 3.35 s at 713 Hz | **PASS** | |
| G-MOD | FAIL 16.71 dB | FAIL 12.14 dB | picture-locked, better by 4.6 dB |
| G-ROOM(c) cepstral | FAIL 48.55x | FAIL 14.55x | instrument, better by 3.3x |
| **G-SUSTAIN** — is anything holding a note | **pass** 0.158 | **FAIL 0.208** | see below |
| G-NOVEL | FAIL r=0.343 | FAIL r=0.549 | picture-locked, and worse |

**Ten gates fail on this master where eleven failed on the last one.**

**THE TWO THINGS THAT GOT WORSE, STATED PLAINLY.**

**G-SUSTAIN now fails, by one note.** It has three limbs and this master fails only the weakest:
note cover 0.208 against 0.20, while **chord cover reads 0.000 against 0.05 and held power 0.00035
against 0.15** — the two limbs that separate *musical* from merely *tonal*, both essentially zero
(the master the client called a musical read 0.375 / 0.286). The ten partials responsible are at
2.5-3.8 kHz, hold 0.68-0.90 s each, and carry 0.0002-0.005 of the beat's power; the assembly stem
that produced them reads note cover **0.000** on its own. **They are the room, not the cell** — and
the room's own tail is measurably longer than it is declared to be (below). One note fewer and this
limb passes, which is exactly why nothing was tuned to remove one.

**G-NOVEL got worse, and it is measuring the picture.** Beat 1's twelve seat times are a perfect
1.045 s ladder in the delivered 4K frames. The part impacts alone score r = 0.000 — but that is not
proof the ladder is inaudible, it is proof the GAPS ARE EMPTY. Put anything at all in them and the
ladder becomes legible: this cell 0.578, band-limited noise 0.610, white noise 0.652, **a sustained
tone 0.756**. The cell is the lowest fill measured and a drone is the worst. There is no fill that
beats leaving beat 1 empty, and leaving beat 1 empty is the master the client rejected as *"The
Tubes over and over"*.

**THE OPEN REVERB NUMBER IS CLOSED, AND THE ANSWER WAS THAT THE DECLARATION WAS WRONG AND THE
NETWORK WAS ALREADY A ROOM (R2-4149).** `layers.showroom_tail` declared **0.35 s above 4 kHz**
against 2.4 s low. Both halves of that were wrong. A 0.35 s tail at 4 kHz in this hall demands a
surface absorption of **0.967** — anechoic-grade in a glass building — and **there is no crossover
frequency at all**: a room's high-frequency decay is Sabine with the ISO 9613 air term,
`RT60(f) = 0.161 V / (S·α + 4 m(f) V)`, which is a smooth curve with no corner anywhere in it. The
room's own 4290 m³ / 1996 m² and its declared 2.4 s back out α = 0.1416, and that gives a target of
**1.73 s at 4 kHz**, 0.99 s at 8 kHz, 0.40 s at 16 kHz. Measured against that curve on the reverb's
own impulse response **at the render's real 96 kHz** (`tools/r2_4149_room_hf.py`), the network reads
1.27 s at 4 kHz and sits within **20 % log-RMS** across 250 Hz – 16 kHz, with an implied surface
absorption that rises 0.14 → 0.21 — which is what ordinary porous treatment does. So
`dsp.fdn_reverb`'s dead `wet_hf_hz` parameter was **deleted rather than implemented** (a parameter
naming a corner asserts a shelf that must not exist, which is why the earlier shelf attempt
lengthened the tail), the declaration was replaced by the curve, and **the number itself was left
alone** — the alternative was rendered in full and adjudicated: at 0.45 s not one of the thirteen
gates changes verdict and beat-1 G-SUSTAIN note cover gets **47 % worse**. **No audio changed.**

The one place this reverb is not a room is **above ~11 kHz**, where its implied surface absorption
goes negative. That is the eight-stage allpass diffuser's own frequency-flat 0.777 s energy decay,
not the damper, and no `rt60_high` can reach below it — a tail cannot decay faster than the burst
that excites it. It is left alone because the only levers reopen R2-4079's metallic-diffuser defect.

---

### THE AUDIO REBUILD OF 2026-08-14 (R2-4079) — REJECTED, AND WHY. Kept for the record.

**The rebuild overshot because the GATES POINTED THE WRONG WAY.** `G-HNR` demanded +8 dB of Boersma
autocorrelation periodicity on beat 1 and `G-FLAT` demanded a non-flat spectrum. Push both hard and
the cheapest way to satisfy them is **sustained pitched material** — which is music. That +8 dB bar
was flagged in R2-4062 as never validated against a signal that *should* pass it, and a positive
control for it was never built. It was chased anyway. **Both beat-1 bars were retired at R2-4084**,
on the measurement that every negative control in the corpus outscores every positive on both at
once; they remain live and unchanged at the engine beats, where holding a note is the physics.

**A machine is periodic in RHYTHM and never in PITCH.** It is percussive, inharmonic, and
transient-dense. Boersma HNR measures "does this hold a note", which is close to the opposite of what
a robot assembly cell should score well on.

**What this gives us that we did not have before: three rejected masters, each rejected for a
DIFFERENT reason.** `master.wav` (noise), the R2-1400/R2-2001 pair (tube ringing), and R2-4079
(musical). **Any instrument worth keeping must fail all three, and fail each for its own reason.**
That is a far stronger control set than any single adversary, and it did not exist until the client
rejected the third one.

### THE AUDIO REBUILD OF 2026-08-14 — what it changed (superseded, kept for the record)

The client rejected three successive audio masters — *"a wind blower"*, *"the first 30 seconds sound
like the instrument The Tubes over and over"*, *"the sound even glass breaking is awful"* — while
**all eight audio gates passed every time.** The gates were the first defect and have been replaced.

**Measured, delivered master → this one:**

| | delivered | now |
|---|---:|---:|
| breach spectral centroid | 51.5 Hz | **1372.1 Hz** |
| breach energy below 100 Hz | 85.57 % | **1.88 %** |
| limiter maximum gain reduction | −22.76 dB | **−0.83 dB** |
| fraction of film pulled >1 dB | 20.65 % | **0.00 %** |
| integrated loudness | −14 LUFS | **−23.00 LUFS** |

**The causes were shared, not per-sound.** Three stages in series: the world-time warp was a
**varispeed resampler**, transposing every world-attached source **6.51× down** at the breach — which
is why the glass had no glass in it; gain-staging used a **K-weighted meter that is deaf below
~50 Hz**, so it over-drove the impact bus by 23.6 dB; and the limiter then removed up to **22 dB while
reporting 0.124 dB**, because it ran eight passes in a loop and only the last, gentlest one reached
the report. A separate defect made the limiter **duck 161 ms *before* each transient** — its gain path
used a zero-phase filter, which is symmetric in time.

**Why −23 LUFS and not −14.** The mix's own peak-to-loudness ratio is 22.1 dB; −14 LUFS at −1 dBTP
permits only 12.85 dB. −14 is a **streaming-music normalisation target**, wrong for a film containing
an exploding glass wall. EBU R 128 asks −23.0 ±0.5 at −1 dBTP and the material lands at −23.13 — they
agree to 0.13 LU, so the film now delivers with essentially no limiting at all.

**ONE COMPLAINT IS ONLY HALF FIXED, BY THE CLIENT'S OWN DECISION.** *"The Tubes"* — a free-free
metal-bar mode series at ratios 1 : 2.31 : 3.87 : 6.1, struck 616 times in 16 s — is **gone**.
*"Over and over"* is **not**. Beat 1's cluster onsets sit on an exact 1.0417 s grid, and **those are
the frames the 2,978 delivered 4K frames actually show**; moving them desyncs audio from picture.
Fixing it needs ~800 frames re-rendered (~$29, ~1 day). **The client was offered that with costs on
2026-08-14 and chose to ship.** So `G-MOD` fails at 11.96 dB @ exactly 1.000 Hz and is marked
**picture-locked**. Successive clusters are now timbrally distinct — `G-NOVEL` and `G-GESTURE` pass —
so the film is **measurably less repetitive in timbre and exactly as periodic in time.** Do not read
that gate's failure as an oversight.

**The gate suite now fails the film it is judging: 6 of 10, against 9 of 9 for the delivered master.**
Most remaining failures are **instrument limits, not audio defects** — after the firing-order change
the engine's harmonic comb is wider than a 1/3-octave band below ~1.5 kHz, so per-band flatness
scores the loudest thing in the film as noise. `source=artefact` thresholds are now rejected by the
suite **by name**: the old bars had been set at "the midpoint between what this master reads and what
the adversary reads", and a gate calibrated to the defect cannot fail the defect.

`superseded_audio_2026-08-13/PART2_THE_FILM_4K_h265.mp4` is the **rejected audio**, kept as the
watchable before. Its ProRes twin was deleted: its video is bit-identical to the current master and
its audio is `audio/out/master.wav`, retained separately as the permanent negative control — so it
carried no unique information. **As of R2-4141 that file is one of TWO rejected arms held on disk**:
`rejected_audio_R2-4079/` holds the musical one, and `audio/out/master.wav` the hair blower. Both
are permanent negative controls in `audio/controls/` and both must keep failing the suite; neither
is ever to be edited.

**What the beat-5 pair does and does not claim.** It claims the **subject now moves across the frame**. It does **not** claim the picture moves faster — the camera's path is nearly unchanged (max positional delta 0.264 m over the whole film, exactly zero outside beat 5), so whole-frame optical flow is essentially the same. Read it for *where the car sits and how it travels*, not for speed. The camera also moves and re-lenses very slightly as well as re-aiming (position ≤0.264 m at f2584, lens ≤1.41 mm at f2244, aim ≤12.045 deg at f2273, all inside f1195-f2677) — that is part of the change, not a regression.

**These two arms were checked for contamination rather than assumed clean.** `world/showroom_lighting.py` changed at 05:33 on 08-08, after `film22.blend` was built, and it adds a lamp (23 -> 24). Control frames were rendered on both arms at frames where the two cameras are **bit-identical**, and measured against a noise floor taken from the same frame rendered twice on different physical 5090s (max 2-6 levels, 0.0000% of pixels over 8 levels):

| control | where | max channel delta | pixels >8 levels | mean luminance delta |
|---|---|---|---|---|
| f526 | showroom, beats 1-3 | 116 | 2.857% | +0.744 |
| f2950 | circuit, beat 6 | 40 | 0.164% | +0.0064 |

f526 is the **positive** control and it fires loudly — the extra lamp is real and the method has power to see it. f2950 is the **negative** control: the residual on the circuit is **117x smaller in mean luminance** than in the showroom and amounts to 0.007% of the mean level. So the lighting change is confined to the showroom and the beat-5 A/B is a camera comparison, as intended. Frames inside f1195-f2677 cannot serve as controls because the camera differs there by construction; f2950 is the nearest frame where it does not.

## SUPERSEDED — do not judge the current film by these

| file | cut | why it is not current |
|---|---|---|
| **`PART2_opening_53s.mp4`** | **08-07 03:10** | **Pre-R2-831 camera.** The beat-1 re-frame/re-pace landed at 08-07 04:11, an hour *after* this was cut. The camera in this file no longer exists. This is the file the client may have formed their pacing judgement from. |
| **`PART2_closing_17s.mp4`** | **08-07 03:11** | Same batch, and additionally pre-dates the R2-943 lap-down (08-07 14:12) which put a moving car in the closing frames. The ending in this file is the *smudge* ending. |
| `seq1/`, `seq2/` | 08-07 03:10 | frame sequences from the same superseded batch. |
| `AFTER_beat1_33s.mp4` | 08-07 16:02 | a valid AFTER for the beat-1 **re-frame**, but it predates the opening tempo pass. Superseded by `AFTER_opening_18s.mp4` for any question about pacing. |
| `BEFORE_beat1_33s.mp4` | 08-07 03:15 | its matched BEFORE, same batch as the superseded PART2 pair. |

## A/B PAIRS — each is a claim only about its own question

| file | cut | question it answers |
|---|---|---|
| `R2851_ending_CANDIDATE.mp4` / `R2851_ending_SHIPPED_A.mp4` | 08-07 07:25 | an ending A/B. Both arms predate the lap-down. |
| `R2943_ending_LAPDOWN.mp4` | 08-07 14:12 | the lap-down ending. Beat 6 is under active work; check with its owner before treating this as final. **See the warning directly below — do not judge the ending on this file.** |

> ### THE ENDING HAS NOW BEEN SEEN. THIS BANNER IS RETIRED (2026-08-14)
>
> **`PART2_THE_FILM_4K_ProRes422HQ.mov` and `PART2_THE_FILM_4K_h265.mp4`
> supersede every clip above, including the ending.**
>
> The banner that stood here from 2026-08-08 said that no file in this folder
> could be used to judge the ending, because every clip showing beat 6 had been
> rendered from a film whose car was three days older than its camera — the car
> absent from frame for the last 3.79 seconds, including the final frame
> (R2-3181).
>
> **That is fixed and the fix is in delivered pixels, not in a plan.** `f2978`
> was rendered, fetched, hash-checked, decoded and looked at: the car is on the
> main straight with kerbs, catch fencing, a populated grandstand and the
> ground cover around it. All **2,978** frames were verified three independent
> ways — coverage against the range 1-2978 (0 missing, 0 duplicated), every
> frame's sha256 re-checked against the hash its broker recorded at fetch
> (2978/2978), and every frame decoded from scratch (2,978 decoded, one
> resolution 3840x2160, 0 failed, 0 flat, 0 black).
>
> **The clips above are still superseded and still must not be judged by** — but
> the reason has changed. They are old cuts of a film that now exists in full.
> Judge it by the two files at the top of this file.

## LINKS

`r2943_4k`, `r2943b6_frames` are symlinks into `~/vast-render/out/seq/`. They
follow whatever is at the other end and are **not** snapshots.

---

### The rule this folder now runs on

If you cut something in here, put a row in this table in the same action. An
artefact whose provenance lives only in a chat transcript is an artefact that
will be mistaken for current the next time somebody opens the folder — which is
exactly what happened twice.
