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
| **`PART2_THE_FILM_4K_ProRes422HQ.mov`** | **08-14 14:39** | **THE FILM. The whole of part 2, one unbroken 4K shot.** 3840x2160, 24 fps, **2,978 frames = 124.0833 s, zero cuts**, 512 spp, AgX / look None / exposure -3.628, SDR. ProRes 422 HQ, **11.25 GB**. Rendered from `render/film25_breach.blend` (sha16 **`1d2aa2d86533574e`**) on world `assembly15`, frames 1-2978 on three rented RTX 5090s over 2026-08-09 to 08-13. **AUDIO REBUILT 08-14** — carries `PART2_AUDIO_MASTER_R2-4079.wav`, muxed `-c:a copy`. **The picture is unchanged and that is proven, not assumed: the video stream's md5 is `c346a7a322a4a2a403727c1e85f17511` before and after the re-mux.** **This is the delivery master.** |
| **`PART2_THE_FILM_4K_h265.mp4`** | **08-14 14:39** | **The viewing copy of the same film**, same 2,978 frames, same new audio. 3840x2160, 24 fps, 124.0833 s, H.265 `hvc1`, faststart, **880 MB**, AAC 192 kbps. Video stream md5 `235ef36e844a62b0e303e4138907b9fa`, identical before and after the re-mux. Use this to watch; use the ProRes to grade or cut. |
| **`PART2_AUDIO_MASTER_R2-4079.wav`** | **08-14 13:30** | **The audio master the two films carry.** 124.083333 s, 48 kHz, 24-bit stereo, **-23.00 LUFS / -1.12 dBTP** (EBU R 128 — see below for why this is not -14). Built from commit `773008e`. The three earlier masters were rejected by the client; this is the fourth. |
| `AFTER_beat5_doppler_4s.mp4` | 08-08 08:20 | **R2-2161, the beat-5 framing fix.** f2340-2439 (t 97.5-101.6 s), 100 frames, 1280x720, 24 fps. The doppler pass. The car is placed **off-centre and travels across the frame**; beat 5's frame-offset is **0.754** against a 0.92 bound. Built from `render/r22161_after.blend`, whose camera path is bit-identical to the gated rig `7fc6d688…`. |
| `BEFORE_beat5_doppler_4s.mp4` | 08-08 08:17 | its matched BEFORE, same 100 frames, same resolution, same 64 samples, same DOF. The shipped camera, which pins the car near **frame centre** the whole way — frame-offset **0.055**. From `render/film22.blend`, camera path `363e4e88…`, the sha `docs/LIVE-CAMERA.md` declares. |
| `AFTER_opening_18s.mp4` | 08-08 01:36 | the opening tempo pass (R2-1606). The most recent camera deliverable. |
| `BEFORE_opening_18s.mp4` | 08-07 17:52 | its matched BEFORE. Correctly named. |
| `audio/` | 08-08 03:14 | re-cut from the master; `audio/INDEX.md` explains the earlier staleness and states it is fixed. |

### THE AUDIO REBUILD OF 2026-08-14 — REJECTED AND REVERTED. Read this before reading the rest.

**The films above carry `audio/out/master.wav` again.** The R2-4079 rebuild described below was
muxed in, played to the client, and **judged WORSE than what it replaced**: *"ngl audio is worse,
sounds like a shitty musical"*. It is parked at `rejected_audio_R2-4079/`. The video was never
touched — md5 verified identical through both the mux and the revert.

**The client's three rejections now trace an arc, and the middle of it is the target:**

```
"a wind blower"              no structure at all        TOO NOISY
"banging on tubes"           inharmonic ringing         WRONG STRUCTURE
"a shitty musical"           sustained pitch            TOO MUCH STRUCTURE
```

**The rebuild overshot because the GATES POINT THE WRONG WAY.** `G-HNR` demands +8 dB of Boersma
autocorrelation periodicity on beat 1 and `G-FLAT` demands a non-flat spectrum. Push both hard and
the cheapest way to satisfy them is **sustained pitched material** — which is music. That +8 dB bar
was flagged in R2-4062 as never validated against a signal that *should* pass it, and a positive
control for it was never built. It was chased anyway.

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
carried no unique information.

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
