# STAGING — R2-416 to R2-450 (the first full-length sequence pass)

Owner: the rung-1 sequence block. `docs/DEFECT-LOG-R2.md` is not mine to edit.

**The pass:** `rq anim` sequence `r1full`, 1280x720 / 64 samples, camera `ONER`,
scene `render/film14_breach_r6.blend`, frames 1-2978. `spec_hash 2b46bc3e1868e66d`,
`scene_hash 6eff712098a43044`. Every frame in this document comes from that one
sequence and that one spec unless it says otherwise.

**What this pass is for, and what it is not.** It hunts temporal defects — flicker,
popping, sim jitter, camera kinks, speed-ramp stutter, batch seams and pacing. It is
NOT a judgement on material or geometry quality: several source fixes are queued for
the next world rebuild and surface quality will change. Where a surface reads soft
below, that is noted and not chased.

---

## R2-416 — rung 1's cost is BEAT-INDEPENDENT, and the master's is not

The ladder budgets the 4K master per beat because per-frame cost varies **8.5x**
along the film's own length: showroom 60.2 s/frame, world 510.5 s/frame. That
weighting is what makes beat 5 "67 % of the master on its own".

**At rung 1 that ratio is 1.00, not 8.5.** Measured on this pass's own spec and
its own .blend, one frame each from the showroom, the breach and the lap:

```
f1     beat 1  showroom, exploded field      67.3 s
f2     beat 1  showroom                      62.5 s
f900   beat 3  breach, sim + world visible   65.5 s
f901   beat 3  breach                        68.0 s
f2000  beat 5  the flying lap, full world    65.7 s
```

`f2000` is the frame that matters: **the world scene at 720p/64 costs the same as
the showroom** — 65.7 s against 64.9 s — where at 4K/512 it costs 8.5x more.

**Restated on a larger sample as the pass ran** (22 frames, and this supersedes
the 10-frame figure an earlier draft of this entry quoted):

```
whole pass so far   n=22   mean 62.33 s   min 58.6   max 68.4
  1_assembly        n=18   61.3 s
  3_breach          n= 2   66.8 s
  5_lap             n= 2   67.0 s
```

The spread across the whole film is **58.6-68.4 s, a factor of 1.17**, against a
factor of **8.5** at 4K. Beat 5 runs 9 % above beat 1, not 850 %. The earlier
50-frame rate run `r2b56_720` (beats 5-6, `film6.blend`) measured **63.4 s/frame**
and this pass measures **62.33**, agreeing to 1.7 % across two different .blends.

**Why, and it is the ladder's own point turned up to its limit.** Fixed cost —
scene load, BVH build, per-frame sync — does not shrink with resolution or
samples. At 4K/512 the *traced* work dominates and the world's 13.2 B triangles
show up in the price. At 720p/64 the traced work is so cheap that essentially
nothing but fixed cost remains, so every frame costs the same whatever is in it.

**What this changes:**

- **Rung 1 cannot be budgeted per beat, and does not need to be.** Cost is
  frames x ~62 s, full stop. Beat 5 is 51.2 % of rung 1 — exactly its frame share
  (1,524 / 2,978) — not 67 %.
- **A full-length rung-1 pass is 2,978 x 62.33 s = 51.6 h = $21.7** at $0.4203/hr
  of GPU time, before scene reloads. The ladder's $17.5 / 52.4 h is right on wall
  clock and low on dollars only because the instance rate moved ($0.3339 ->
  $0.4203/hr). **The rate estimate of 63.4 s/frame was good to 1.7 %** — it is the
  per-BEAT weighting, not the rate, that does not apply at this rung.
- **The corollary is a warning about rung 2 and 3, which are still estimates.**
  They are interpolated between a beat-independent measurement and a
  beat-dependent one. The crossover — the resolution at which traced work starts
  to matter again — is unmeasured, so 1080p/128 could sit anywhere between "still
  flat" and "already weighted". Measure the rung.

**Sample size, stated plainly:** n=1 for beat 5 on this blend. The claim that
rung 1 is flat rests on that one frame plus 50 frames of beats 5-6 at the same
resolution and samples on `film6.blend`. It will be re-stated against the full
pass when it lands, and that is the number to trust.

---

## R2-417 — `beat_sheet.md` and `beat_sheet.json` disagree about the film's last image

`docs/beat_sheet.md`, Beat 6:

> Peel-off at t=-3.0s, hold 8.0-11.0s at `[594.19, 16.05, 140.0]` on a **18.75mm** lens.

`docs/beat_sheet.json` `beat6`, and the authored path in `render/film14_path.json`,
both say otherwise:

```
hold_lens_mm            74.0
keys  t= 6.0  lens 18.75 mm      <- the .md quotes THIS key
      t= 8.0  lens 40.00 mm      <- the hold begins here
      t=11.0  lens 74.00 mm      <- the hold ends here
```

The `.md` has taken the lens from the **t=6.0** key — two seconds before the hold
starts — and attached it to the hold. The position it quotes is the hold's;
the lens is not.

**This is a documentation defect, not a film defect, and the distinction matters
because I nearly logged it as the latter.** Measured off the path, the closing
71 frames are static in position and go **40.048 -> 73.997 mm, +84.8 %**, FOV
48.40 -> 27.34 deg. That looked exactly like a defect: a "3-second hold" that is
actually a continuous zoom. It is not — it is authored, deliberate, and
documented as `closing_lens_push` / R2-113:

> "The circuit reads at 40 mm and the wound does not; the wound reads at 74 mm
>  and the circuit is gone. The hold was a freeze, so the push is the only
>  motion in the last 3 s."

The path implements that spec **exactly** (40.0 -> 74.0 over t 8.0-11.0).

**The cost of the `.md` being wrong is real even so:** anyone judging the closing
frame against the prose expects a 18.75 mm wide and will be looking at a 74 mm
lens — a 3.9x difference in focal length on the film's final image. `beat_sheet.md`
is generated, so the fix belongs in `tools/build_beatsheet.py`, not in the file.

**Still open, and only a watch can answer it:** whether an 85 % push over 3.0 s
reads as the intended reveal or as a creep. Edge-of-frame content drifts
**6.25 px/frame median, 8.43 px/frame max at 720p** (18.75 / 25.30 px at 4K),
543 px in total at 720p and 1,628 px at 4K. That is not a subtle move. Judged on
the frames below when they land.

---

## R2-418 — the temporal instrument, and the two known-bad artefacts it first missed

`tools/seq_temporal.py`. Written for this pass because `rq seq stats` gives
per-frame statistics but nothing that reads BETWEEN frames.

**It was wrong twice, and both failures are the ones this project keeps naming.**

**Failure 1 — a metric that reads the same present or absent.** The firefly test
began as "a pixel that jumps and comes straight back", which sounds specific.
Measured on a synthetic clean pan at 3 px/frame it fired on **267 bright pixels of
every single frame** — identical with the defect present and absent — because a
narrow bright feature panning across a pixel in one frame does exactly that. Fixed
by requiring the pixel to be a **spatial** outlier as well: a firefly is alone, a
passing edge is coherent with its 3x3 neighbourhood. The clean control then read 0.

**Failure 2 — measuring the wrong series.** The periodicity check ran on the
frame-to-frame difference series only. A 2-frame brightness flicker puts a
*constant* offset into that series — every adjacent pair differs by the same
amount — so d1 is flat and carries no period-2 line at all. A 1.5 % flicker was
**completely invisible**. Fixed by transforming the `mean` and `sd` series too,
where the same flicker reads **189,029x the spectral median at period 2.01**.

**Calibration, against controls including artefacts already known to be bad:**

| control | what it is | result |
|---|---|---|
| clean | aperiodic pan over a smoothed random field | **0 flagged**; spectral floor 75x |
| firefly | 40 stray bright px on f150-152 only | flags **exactly f150, f151, f152** |
| held | f101 a byte-identical copy of f100 | flags **f101, d1 = 0.0000, "IDENTICAL"** |
| flick2 | 1.5 % brightness flicker every other frame | 0 outliers, **189,029x at period 2.01** |
| period24 | 3 % brighter on every 24th frame | 37 frames flagged + spectral line |

**`flick2` is the row that justifies the second instrument.** The outlier test sees
nothing; only the spectral test sees it. That is the R2-086 class — a defect that
becomes its own baseline — and it is why the flagging thresholds here are derived
from a **global or beat-global** robust scale and never from a rolling window.

**Stated limits.** The spectral floor on the clean control is **75x**, so nothing
below ~100x is evidence. Periodic energy is evidence and not a verdict: real
content can be periodic (fence posts at constant speed), though a period of 2-3
frames at 24 fps almost never can be. `--stride 2` subsamples pixels by 4x, which
is fine for means and percentiles but weakens the single-pixel impulse count;
anything it finds is re-run at `--stride 1`.

---

## R2-419 — beat 1's camera does NOT pulse at the presentation stations. Refuted by its own control

The hypothesis was attractive and it is wrong, which is why it is written down.

Beat 1 presents fifteen clusters at 1.76 s intervals — every 42.2 frames. Its
camera-speed series carries strong periodic energy at **39.2 and 41.3 frames,
655x the spectral median**, which is within a frame or two of the station
spacing. The obvious reading is that the camera decelerates into each
presentation and dashes out — a fifteen-times-repeated pulse, and the single
largest structural fact about the beat's pacing.

**The control kills it.** Mean camera speed in a +/-5-frame window around the
fifteen stations, against 20,000 draws of fifteen randomly placed windows of the
same size:

```
at the 15 stations     1.574 m/s   (n=159)
everywhere else        1.824 m/s   (n=633)
null, random windows   1.776 m/s   sd 0.185
observed sits at the 13.89th percentile of the null   (-1.09 sd)
```

**-1.09 sd is not a finding.** The stations are not systematically slower. The
periodic energy at ~40 frames is real but it is **not phase-locked to the
presentations**, so whatever produces it, it is not the presentation rhythm.

What survives, and it is a plain fact rather than a story:

```
beat 1 camera speed   min 0.046   p10 0.716   median 1.783   p90 2.850   max 3.897 m/s
  frames under 0.5 m/s   50  (6.3 %)
  frames over  3.0 m/s   52  (6.6 %)
```

**An 85x speed range inside one beat**, which is worth knowing before judging its
pacing, and which is consistent with R2-321's separation of the smeared tour
(88 % over 20 px) from the near-static close-out (4 %) without needing a rhythm to
explain it.

---

## R2-420 — where the film's worst camera moments are, predicted from the path before the pixels

From `render/film14_path.json`, all 2,978 frames, independent of any render.
These are the frames to look at first when the pass lands, and two of them are
corroborated by `render/film14_continuity.json`, which was written by a different
tool for a different purpose.

| frame(s) | what the path says | corroboration |
|---|---|---|
| **f2634** | the film's **fastest pan**: 0.2207 frame-widths/frame, 141 px of 180-deg smear at 720p, **424 px at 4K** | `worst_rotation_step_deg = 12.957` at **f2634** |
| **f1209** | the largest single-frame camera translation | `worst_position_jump_m = 4.2469` at **f1209** — 102 m/s |
| **f901-f916** | the interior->daylight **exposure ramp**, ~1 stop over 16 frames | `exposure_ramp_frames = [901, 916]` |
| f2906-f2908 | camera arrives at the hold and stops dead | authored; see below |
| f865-f871, f1042-f1056 | the speed ramp's 6-frame ease-in and 15-frame ease-out | `time_map`, solved floor 0.1537 |
| f792/793, f864/865, f1056/1057, f1190/1191, f2714/2715 | beat boundaries | — |

**f2906-f2908 is NOT a defect and the detector was right to flag it.** Per-frame
camera step over the arrival: 1.085 ... 0.0521, 0.0220, 0.0022, 0.0000 m — a
monotone ease-out to a 2 mm final step, then exactly zero for 71 frames. A jerk
detector fires on any authored stop; this one is clean. Recorded here so the flag
is not re-investigated when it appears in the pixel results.

**Two predictions I made and then closed against the source, before spending a
frame on either:**

- *Beat 3 will strobe*, because the camera flies in real time while the shutter
  scales with world time — 14 px of per-frame displacement with ~1 px of blur.
  **Closed: it will not.** `shutter_mode = flat`, `shutter_frames = [0.5, 0.5]`,
  180 deg for the whole take, confirmed in `film14_continuity.json`. The
  double-correction was found and removed already; `build_camera_rig.py`:90-129
  is the record.
- *Beat 3 will show stepped time*, because at a world-time floor of 0.1537 one
  world frame spans 6.5 film frames, and an uninterpolated sim would hold the
  shards for 6 frames and jump. **Closed: it does not.** Measured on f900 -> f901,
  both inside the floor: **57.69 % of pixels changed**, mean |delta| 0.0572,
  with the change spread across the sky band (0.0667), the apron (0.0543) and the
  car (0.0514) alike. Everything moves; nothing is held.

---

## R2-421 — beat 5 is temporally clean over the only contiguous run that existed before this pass

Twenty-four contiguous frames of the flying lap, f1900-f1923, left on disk by the
rate measurement `r2b56_720` (`film6.blend`, an older film build, same 720p/64
spec). Until this pass they were the longest look anyone had had at beat 5.

```
d1 median 0.0305   MAD 0.0012   max 0.0325 @ f1901
outliers at |z| > 6 :  0
periodic energy     :  none above 50x the spectral median in any series
```

**A MAD of 0.0012 against a median of 0.0305 is 4 % variation frame to frame** —
the motion energy is almost constant, which is what a smooth camera over a smooth
world should give and is the opposite of what jitter looks like.

Two limits, stated because this is a positive result and positive results are
where this project has been burned: it is **24 frames of 1,524**, and it is
`film6.blend`, not the shipping `film14_breach_r6.blend`. It is a reason to
expect beat 5 to be clean, not evidence that it is. The full pass decides.

---

*(continues — findings are appended as the pass delivers)*

## R2-422 — the film spends 8.04 s of the lap with the car at 4.2 % of frame width, and the reason is camera physics

> **SUPERSEDED FIGURES.** Every percentage in this entry came from the broken
> subtense formula retired in R2-430. Corrected by projected bounding box: the
> stretch measures **4.22 %** median (not 7.1 %) against a beat-5 median of
> **12.91 %** — the car is at **one third** its usual size, not half. **The
> finding strengthens.** The 8.04 s duration is unaffected: it comes from the
> camera path, not from this instrument. Use R2-430's table for all beat medians.

**Shot scale over all 2,978 frames**, computed from `render/film14_path.json`,
`telemetry/telemetry.csv` and `anim/filmtime.py`'s time map — the car's apparent
length as a fraction of frame width, given the authored lens at each frame. No
render involved, so this is available before the pass finishes and is checkable
against it.

| beat | frames | median camera-to-car | median size | p10 | p90 |
|---|---:|---:|---:|---:|---:|
| 1_assembly | 792 | 5.0 m | **143.7 %** | 78.4 % | 335.6 % |
| 2_launch | 72 | 5.4 m | 101.0 % | 88.5 % | 105.3 % |
| 3_breach | 192 | 6.5 m | 52.7 % | 39.8 % | 66.2 % |
| 4_transit | 134 | 44.1 m | 12.6 % | 11.9 % | 37.6 % |
| 5_lap | 1,524 | 42.9 m | 14.9 % | 7.7 % | 37.4 % |
| 6_ending | 264 | 294.7 m | 1.9 % | 1.0 % | 3.5 % |

**Beat 1's 143.7 % median is R2-317 arrived at from a different direction.** That
entry measured fifteen presentations overflowing their frame by 1.06x to 2.59x
from the cluster bounding boxes; this measures the whole beat from the path and
the car's own length and gets a median of 1.44x with a p90 of 3.36x. Two
independent computations, same conclusion: **for most of the opening 33 seconds
the subject is larger than the frame.**

**The finding this instrument adds that nothing else has: the longest stretches
where the subject is a speck.** Beats 2-6, runs with the car under 10 % of frame
width:

```
f2693-2978   286 frames  11.92 s   spans the end of beat 5 into beat 6
f2035-2227   193 frames   8.04 s   mid-lap
f2307-2344    38 frames   1.58 s
```

The first is beat 6 and is the whole point of the closing wide — authored, and
the car is *meant* to be 1.9 % of the frame. **The second is not.**

**f2035-f2227 in detail** — 8.04 s, 6.5 % of the film's entire runtime, with the
car between 6.8 % and 9.9 % of frame width and never above it:

```
f2020  dist  91.0 m  11.68 %
f2060  dist 142.0 m   7.86 %
f2100  dist 169.5 m   6.96 %
f2160  dist 187.2 m   6.77 %      <- furthest
f2200  dist 175.8 m   7.65 %
f2240  dist 102.4 m  11.54 %
```

against a beat-5 median of 14.9 %. **The car is at half its usual size for eight
seconds in the middle of the flying lap.**

**It is authored, and the beat sheet says why — but the reason is about the
camera, not the audience.** The anchors through this stretch read:

> t=85.31 "T9 seen from **105 m ahead**: the camera is already running for T10"
> t=88.00 "crossing the track line ahead of the car, descending"
> t=90.01 "T10 Panorama 1 at 255 km/h, seen from **195 m down the road**: the
>          camera is already on the doppler line and braking for it"
> t=91.40 "T11 behind us; **170 m of deceleration is what a hover costs**"
> t=92.40 "settling onto the station: 45, 33, 22, 8, 1.5 m/s, five anchors,
>          because arriving at a hover in one is a 6 g stop"

So the eight seconds are the **transit cost of arriving at the doppler station**
in time to be stationary for it. The physics is not in dispute: you cannot stop a
camera from 68 m/s in less than ~200 m, and the doppler beat is the lap's
centrepiece.

**The author already saw it and fought it with the lens.** Focal length climbs
65 -> 70 -> 75 -> 80 -> 85 mm straight through the stretch, which is what holds
the subject at a roughly flat 7 % instead of letting it collapse. At a constant
65 mm, f2160 would read **5.5 %** rather than 6.77 %. The compensation is real and
it is not enough to make the subject large.

**What is NOT decided here, and cannot be by arithmetic:** whether 8 seconds of a
distant car reads as the car pulling away down a long circuit — which is a real
and good thing for a lap to show — or as eight seconds of waiting. That is a
pacing judgement and it needs the watch. It is flagged as the single longest
unintended small-subject stretch in the film so that the watch knows to look.

**Limit of the instrument:** this is the apparent size of the car's length held
perpendicular to the view axis. A car seen end-on is shorter than this says, and
occlusion is not modelled. It is a first measure of subject scale, not a
substitute for looking, and every figure above is confirmable in the delivered
frames.

---

## R2-423 — THE ONE-SHOT LAW HOLDS AT ALL FIVE BEAT BOUNDARIES, and the film's three worst moments are fast, not broken

The film's defining constraint is zero cuts. Until now that was asserted from key
coverage — `film14_continuity.json` shows every beat carries location and rotation
keys — which proves the camera is *animated* everywhere, not that it is
*continuous* anywhere.

**The test.** At each boundary, compare the single-frame step in position,
aim and lens against the median step over the 40 frames around it. A cut is a step
that is large against its own neighbourhood; a fast move is not.

| boundary | \|dp\| m | local median | x | rotation | local median | x | lens step |
|---|---:|---:|---:|---:|---:|---:|---:|
| f792/f793 | 0.1333 | 0.1244 | **1.07** | 0.748 deg | 0.690 | **1.08** | 0.0000 mm |
| f864/f865 | 0.2327 | 0.2478 | **0.94** | 2.459 deg | 1.176 | 2.09 | 0.0250 mm |
| f1056/f1057 | 0.5436 | 0.5327 | **1.02** | 5.555 deg | 2.224 | 2.50 | 0.0000 mm |
| f1190/f1191 | 3.5160 | 3.4549 | **1.02** | 0.165 deg | 0.174 | 0.95 | 0.0000 mm |
| f2714/f2715 | 2.5454 | 2.5540 | **1.00** | 0.062 deg | 0.060 | 1.04 | 0.0047 mm |

**Position is 0.94x to 1.07x the local median at every boundary** — the camera
crosses each beat line at exactly the speed it was already travelling. **Lens is
0.0000 to 0.0250 mm**, which is nothing. The two rotation ratios over 2x are
2.459 deg and 5.555 deg in absolute terms, against a film maximum of 12.957 deg;
they are the aim turning into the next beat, not a jump.

**No seam at any boundary.** This is the path, not the pixels; the dense blocks
queued for this pass cover all five boundaries so the pixels can confirm it.

**And the sharper result — the film has no camera-path kinks at all.** Ranking
every frame by step size, the three worst events each turn out to be a *run* of
near-identical steps rather than an isolated one:

```
POSITION  f1205..f1213   4.2158, 4.2309, 4.2418, 4.2469, 4.2458, 4.2385, 4.2250, 4.2053 m
          -> 101.9 m/s sustained. `worst_position_jump_m = 4.2469 @ f1209` is the
             peak of a smooth run, not a discontinuity. Ratio to its neighbour: 1.000

ROTATION  f2632..f2640  11.502, 12.957, 12.417, 11.999, 11.918, 11.812, 11.512, 11.274 deg
          -> a sustained fast pan. `worst_rotation_step_deg = 12.957 @ f2634` likewise

LENS      f2250..f2256   2.666, 3.031, 3.178, 3.106, 2.815, 2.301 mm  (64.60 -> 47.50)
          -> a sustained fast zoom, 26 % of focal length over 6 frames
```

In all three the worst frame is within 5 % of its own neighbours. **The film's
"worst" camera moments are places where it moves fast, not places where it
breaks.** That is the opposite of what a kink looks like and it is a genuine pass.

---

## R2-424 — f2631-f2656: 1.08 s of the flying lap carries over 200 px of 4K motion smear, peaking at 424 px

The same f2634 pan, converted into the unit that decides whether a picture reads.
A 180-degree shutter smears a static point by **half** its per-frame image
displacement, so pan in frame-widths x resolution / 2 is the smear in pixels.

```
f2626  0.0516 w/f    99 px at 4K    33 px at 720p
f2630  0.0970 w/f   186 px          62 px
f2632  0.1435 w/f   275 px          92 px
f2634  0.2207 w/f   424 px         141 px      <- the film's worst
f2638  0.2012 w/f   386 px         129 px
f2644  0.1750 w/f   336 px         112 px
f2648  0.1849 w/f   355 px         118 px
```

The lens is a constant 32.0 mm throughout, so this is pure camera rotation.

**Contiguous runs over 200 px of 4K smear, whole film:**

```
f2631-f2656   26 frames   1.08 s   peak 424 px   [5_lap]
f477-f498     22 frames   0.92 s   peak 315 px   [1_assembly]
f79-f89       11 frames   0.46 s   peak 207 px   [1_assembly]
f2266-f2276   11 frames   0.46 s   peak 310 px   [5_lap]
f1285-f1288    4 frames   0.17 s   peak 206 px   [5_lap]
f1059-f1061    3 frames   0.12 s   peak 206 px   [4_transit]
```

**424 px is 11 % of the frame width at 4K.** For 26 consecutive frames the picture
is smeared by more than a twentieth of its own width. `f477-f498` is the same
event in beat 1 and is the pixel-space form of R2-321's f460/f500 findings,
arrived at independently from the path.

**Against the film's own declared limit.** `weave_spec.pan_limit_widths_per_frame`
is 0.12. Frames over it:

```
1_assembly   18 of 791  (2.3 %)   max 0.1640
5_lap        34 of 1524 (2.2 %)   max 0.2207     <- 1.84x the limit
2,3,4,6                0          max 0.1072
```

**Two honest qualifications.** First, my figure is the **total** inter-frame
rotation (yaw, pitch and roll together) divided by the horizontal field of view;
R2-321 quotes the sheet reporting the tour peaking at 0.0939, which is a smaller
number and is very likely horizontal pan alone. These are different quantities and
mine is the larger by construction — it is the right one for smear, which does not
care which axis moved. Second, `weave_spec` is beat 1's spec; whether its limit was
ever intended to bind beat 5 is not established here. **Beat 1's own 18 violations
are unambiguously in scope.**

**What is NOT decidable at 720p:** whether 424 px of smear at 4K destroys the shot
or reads as speed. At 720p the same event is 141 px, and the two do not look alike.
This one needs a rung-3 or 4 look at f2631-f2656 specifically.

---

## R2-425 — the film opens 84 degrees nose-down, and one second in there is no subject in the frame

**Pixels, from this pass**, frames 1, 7, 13, 19, 25, 31, 37, 43, 49 — the first
1.8 seconds, which nobody had seen in motion.

```
f1-f7    the monocoque cluster: overflowing the frame but READABLE
f13      already unrecognisable in outline; floor signage still legible
f19      a dark smear
f25-f43  NO IDENTIFIABLE SUBJECT. A large translucent blue wedge fills the frame
         vertically, two small out-of-focus part clusters sit at the edges, the
         floor signage is cut to "AN ...EELBASE"
```

f25 is at **t = 1.04 s**.

**The cause is the view angle, and it is measurable.** The camera's elevation:

```
beat 1 median  -42.39 deg      min -84.34 deg      max -5.28 deg
first 60 frames, median  -80.86 deg
frames steeper than 80 deg DOWN   120  (5.00 s, 15.2 % of beat 1)
frames steeper than 70 deg DOWN   187  (7.79 s, 23.6 % of beat 1)
```

**The film's first frame looks 84.15 degrees down** — 5.85 degrees off vertical —
from 5.66 m above a car at floor level. Nearly a quarter of beat 1 is shot
steeper than 70 degrees down. Every other beat is essentially level (beat 2
median -3.3 deg, beat 5 -7.5 deg, beat 6 -14.1 deg); **192 of the film's 195
near-nadir frames are in beat 1.**

**This is not the same defect as R2-321's motion blur, and the distinction
matters for the fix.** R2-321 measured 42.3 px of median camera smear and
concluded the middle third does not read. f25 is not primarily smeared — it is
*framed* so close and so steeply that a single part fills the frame as an abstract
shape. A shutter change would not fix f25; only distance or angle would.

**And the structure it reveals is a rhythm.** The presentations sit at f1 and f43
(1.76 s apart, fifteen of them). f25 is the **travel between two stations**, not a
station. So beat 1 alternates readable presentation with unreadable transit
roughly every 0.9 s for 24.6 s. R2-419 shows the camera does not slow at the
stations, so nothing marks the difference except what is in shot.

**Limits.** Nine frames of 792, at stride 6, at 720p. The dense block f400-f519 is
queued and covers the worst-smeared part of the tour; f745-f864 covers the
close-out that a review called the best material in the film. Both are needed
before this becomes a verdict on the whole beat rather than on its opening second.

---

## R2-426 — a camera ROLL measurement is undefined when the camera looks down, and beat 1's camera looks down

Recorded because it produced a confident, completely false result and the shape is
general.

Measuring roll as "the angle of world-up projected into the image plane" is
standard and correct — **except that the projection's length is cos(elevation)**,
so it collapses to zero as the camera approaches vertical. My first run reported:

```
beat 1  max |roll| 179.40 deg at f9      max step 358.650 deg/frame at f10
beat 5  max step 64.117 deg/frame at f2637
```

**Both are artefacts.** 358.65 deg/frame is an angle wrapping through +/-180, and
the beat-5 figure is refuted outright by an independent instrument: the continuity
gate's `worst_rotation_step_deg` is **12.957** for the whole film, and a total
rotation of 12.957 deg cannot contain 64 deg of roll.

The condition number is `cos(elevation)`, and it should be reported beside every
roll figure:

```
beat 1   min condition 0.0986  (elevation -84.3 deg)   134 frames below 0.2
beat 5   min condition 0.1673  (elevation -80.4 deg)     2 frames below 0.2
beats 2,3,4,6  min condition 0.7631 or better           0 frames below 0.2
```

**134 of beat 1's 792 frames cannot carry a roll measurement at all.** The
elevation figures in R2-425 are used instead: elevation is a direct dot product
against world-up and has no degeneracy anywhere.

**The general form, which this project has met before under other names:** an
angle recovered from a projection is only as good as the projection's length.
Report the length. A derived angle with no stated condition is the trigonometric
version of a count presented as a measurement.

---

## STATUS OF THE PASS — read this before quoting anything above

**19 frames of 2,978 have been delivered as pixels at the time of writing.** The
render is running and resumes; `rq anim --name r1full` re-submits only what is
missing.

**Which findings rest on pixels and which on the authored path:**

| entry | evidence |
|---|---|
| R2-416 rung-1 cost is flat | **pixels** — 5 frames' render times + 50 frames of `r2b56_720` |
| R2-417 `.md` vs `.json` closing lens | source files only; no render needed |
| R2-418 the instrument | **pixels** — 5 synthetic controls, 240 frames each |
| R2-419 no station pulse | authored path + a 20,000-draw null |
| R2-420 hot-spot predictions | authored path, two corroborated by `film14_continuity.json` |
| R2-421 beat 5 clean over 24 frames | **pixels**, but from `film6.blend` |
| R2-422 shot scale / the 8 s speck | path + telemetry + time map |
| R2-423 no seam at any boundary | **authored path only — the pixels have not confirmed it** |
| R2-424 the f2634 smear | authored path; the 720p pixels are not yet rendered |
| R2-425 the opening does not read | **pixels** — f1..f67 at stride 6 |
| R2-426 roll is undefined here | method |

**R2-423 is the one to be most careful with.** "No seam at any beat boundary" is
currently a statement about the camera curve, not about the picture. A seam could
still arrive from something the path does not describe — a light that switches, a
sim that starts, an LOD that swaps. The four dense blocks covering
f792/793, f864/865, f1056/1057, f1190/1191 and f2714/2715 are queued precisely to
close that.

### What is queued, and why these ranges

A full uniform 2,978-frame pass costs **$22.7 of the $25.57 left under the
broker's $45 cap**, with four other agents live on the same budget. It was
retargeted rather than run flat, for two reasons: the budget is shared, and six
source fixes (apron, gantry sign, deck slabs, placed items, crowd, roof) are
queued for the next world rebuild, so a uniform pass buys surface quality that is
about to be replaced. **Temporal defects will not change**, so the frames were
spent where they live.

```
stride-6 across the whole film   497 frames   the complete 124 s at 4 fps, for PACING
f400-f519    beat 1's worst-smeared tour frames (R2-321's f434, f460, f500)
f745-f864    beat 1 close-out + the f792/793 seam + all of beat 2 + f864/865
f865-f984    the breach: ramp ease-in f865-871, exposure ramp f901-916
f1041-f1160  ramp ease-out f1042-1056 + the f1056/1057 seam + transit
f1161-f1280  the f1190/1191 seam + f1209, the largest position step
f1900-f2019  mid-lap; OVERLAPS r2b56_720's f1900-1923 as a cross-build control
f2575-f2694  f2634, the film's fastest pan and largest rotation step
f2695-f2814  the f2714/2715 seam
f2859-f2978  the closing hold, the 85 % push, the last frame
```

1,577 frames, ~29 h, ~$12 — leaving ~$13.5 of the cap for the other four agents.
Every beat boundary, every predicted hot spot, and one deliberate cross-build
control are covered.

### The stride-6 pass is for pacing and CANNOT substitute for the dense blocks

Six frames apart is 0.25 s. It will show shot scale, beat rhythm and whether a
beat outstays its welcome. It **cannot** show flicker, a one-frame pop, judder, a
firefly, or a batch seam — all of which need adjacent frames. `seq_temporal.py`
now refuses to mix the two: `--spacing` must be declared, pairs that are not
exactly that far apart are dropped, and the dropped count is printed, because the
two spacings share one directory and differencing across them would report a
6-frame gap as motion energy.

---

## R2-427 — the temporal instrument's calibration is now reproducible, and the selftest is shown FAILING

R2-418 described a calibration whose controls I then deleted, which would have
left the claim unreproducible. `tools/seq_temporal.py --selftest` rebuilds all
five controls from a fixed seed and asserts them:

```
  PASS  clean     must flag nothing, flagged 0
  PASS  firefly   must flag exactly f150,151,152; flagged 3
  PASS  held      must report the duplicate frame
  PASS  flick2    outliers must miss it (got 0) and a period-2 line must appear
  PASS  period24  must flag something, flagged 37
SELFTEST PASS
```

**A passing selftest proves nothing until it has been seen failing.** Re-injecting
the exact original bug — dropping the spatial-isolation term from the firefly
test, and nothing else:

```
  FAIL  clean     must flag nothing, flagged 238
  FAIL  firefly   must flag exactly f150,151,152; flagged 238
  PASS  held      must report the duplicate frame
  FAIL  flick2    outliers must miss it (got 238) and a period-2 line must appear
  PASS  period24  must flag something, flagged 238
SELFTEST FAIL: clean, firefly, flick2                       exit 1
```

Three of five controls fail and the exit code is non-zero. **The suite discriminates.**

**The `flick2` assertion is the load-bearing one** and it is two-sided on purpose:
the outlier test must MISS it and the spectral test must CATCH it. If outliers
ever start firing on `flick2`, the two instruments have stopped being independent
and the spectral test has lost its reason to exist.

**One weak assertion, stated rather than hidden.** `period24` only asserts
`flagged > 0`, so it passed even with the firefly bug injected — 238 frames
flagged for the wrong reason still satisfies "something was flagged". It is the
least discriminating row in the table and should not be cited as evidence that
the periodic-defect path works; `flick2` is the row that carries that.

**Addendum — the same failure shape, caught a third time, in the progress monitor.**
The background watcher on this pass filtered `rq seq status` with
`grep -E "BLANK|blank|corrupt|ODD"`. The healthy line it is meant to stay silent
on is:

```
VERIFIED  every frame present, complete, consistent, and not blank
```

which contains `blank`. **The alarm fired on the all-clear**, every poll, and
would have been throttled off as noise — leaving a monitor that looks armed and
is deaf. The problem lines are all uppercase keywords anchored at column 0
(`MISSING`, `BLANK`, `CORRUPT`, `ODD`, `UNCHECKED`) against `VERIFIED`, so the
filter is `^(MISSING|BLANK|CORRUPT|ODD|UNCHECKED) `.

Verified in **both** directions before re-arming, because silence is not success:

```
r1full      (healthy)              -> matches nothing        exit 1
r2b56_720   (2 real ODD frames)    -> "ODD  2 frame(s) ..."   exit 0
blankseq    (3 real failures)      -> "MISSING  3 frame(s)"   exit 0
```

A watcher that cannot be shown firing on a known-bad artefact is not a watcher.

**Second addendum — the SAME watcher failed again, oppositely.** With the filter
fixed, it then re-reported the *same* f2000/f2001 flag on every 5-minute poll,
because that flag is a **persistent dispositioned condition** (R2-428: the
sequence is filled out of order, so their neighbours are beat-1 frames). A
watcher that reports STATE rather than CHANGES raises the same alarm forever, is
throttled off as noise, and ends up **deaf while still looking armed** — the
identical end state as the false-positive bug, reached from the opposite
direction.

Fixed by diffing against a state file and emitting only transitions. **CLEARED is
emitted too, and it is a predicted event:** R2-428 says f900/f901 should stop
being flagged once the dense block f865-f984 surrounds them with real beat-3
neighbours, and that if they do NOT clear it becomes a real finding about the
exposure ramp. A watcher that only reports onsets could never deliver that.

Verified in four directions before arming, with a seeded state file rather than
by waiting for reality:

```
1. empty state, flags present   -> "ODD NEW 2 frame(s): 2000,2001"
2. unchanged on the next poll   -> SILENT            <- the bug being fixed
3. state seeded with a stale 901 -> "ODD CLEARED on 1 frame(s): 901"
4. state seeded without 2001    -> "ODD NEW 1 frame(s): 2001"
```

**And the same bug was still present a second time in the same script.** The
`JOBFAIL` query selected every failed job for the sequence on every poll, so one
failure would have repeated indefinitely exactly as the frame flags did. Fixed
with a 310 s window and verified against a real failed job in another sequence
(`blankseq` reports it all-time, and reports nothing inside the window).
**Fixing one instance of a defect is not fixing the defect** — the second copy
was four lines below the first.

**A third trap, unrelated and worth one line:** the watcher initially crashed with
`ModuleNotFoundError: No module named 'bpy'` while importing `json`. A stray
`enum.py` left in the shared scratchpad by another block shadows the standard
library for any script run from that directory. `PYTHONSAFEPATH=1` removes the
script's own directory from `sys.path` and is the fix.

---

## R2-428 — the sequence-relative outlier check assumes a CONTIGUOUS sequence, and a strided fill breaks that assumption

The farm's per-frame outlier check flagged f900 and f901 during this pass:

```
ODD  2 frame(s) do not match their neighbours: 900-901
       900: much brighter than its neighbours: mean 0.4471 vs 0.3282 median over 15 frames (11 MADs)
       901: much brighter than its neighbours: mean 0.4404 vs 0.3259 median over 14 frames (9 MADs)
```

**The detector is not wrong, and reading what it says is what resolves it.** It
claims f900 is much brighter than its neighbours. That is *true*. The delivered
sequence at that moment was:

```
f1, f2, f7, f13 ... f193      stride-6, ALL beat 1 (showroom interior)
f900, f901                    beat 3 (through the glass, full daylight)
f2000, f2001                  beat 5
```

So the "15 neighbours" of f900 in sequence order are **beat-1 showroom frames**,
median luma 0.3282 — which is literally f145's value. f900/f901 are the breach in
daylight at 0.4471/0.4404. A frame that has burst out of a darkened showroom is
supposed to be brighter than one still inside it.

**The general statement, which is a caveat on trusting this check and not a
reason to distrust it:** a rolling median over the 25 *sequence-order* neighbours
is a measure of local continuity, and it is only a measure of anything if the
sequence is locally continuous. This pass deliberately fills **stride-6 across the
whole film first**, so until the dense blocks land, every frame's "neighbours" are
0.25 s apart and any beat boundary in the delivered set will read as an outlier.

**It resolves itself and needs no action:** the dense block f865-f984 is queued
and will surround f900/f901 with genuine beat-3 neighbours, at which point the
flag should clear on its own. **If it does NOT clear once that block lands, it
becomes a real finding** — f901 is the first frame of the authored exposure ramp
(`exposure_ramp_frames = [901, 916]`, ~1 stop over 16 frames), and a ramp that
steps rather than eases would look exactly like this. That is the test.

**Corollary for anyone reading `rq seq status` on a partial pass:** MISSING and
ODD are both expected while a sequence is being filled out of order. Neither is
evidence until the range around the flagged frame is contiguous.

### An observation from the same data, not a defect

Beat 1's frame luma over f1-f193 (stride 6) swings **0.2972 to 0.5184 — a 74 %
range in 8 seconds** — and it does so *smoothly*: 0.361, 0.420, 0.474, 0.518,
0.506, 0.471 on the rise and fall, then 0.478, 0.405, 0.341, 0.312 down. No steps,
no single-frame excursions. This is the camera moving between a dark floor and
brightly-lit parts, which is content rather than flicker, but the amplitude is
worth knowing before judging beat 1's exposure: **the opening third of the film
changes overall brightness by more than half a stop, repeatedly.**

---

## R2-429 — ~~THE FILM HAS NO ESTABLISHING SHOT~~ **WITHDRAWN IN FULL — see R2-430**

> **DO NOT CITE THIS ENTRY.** Its headline is false and its 76.1 % figure was
> wrong by 1.70x — the subtense of the car's LENGTH at its CENTRE distance, where
> the visible extent is its WIDTH on its NEAR face. Beat 1's true minimum is
> **45.1 %**, and the film establishes properly at f631. The pixel observations of
> f1-f283 below are the only part that survives. Kept unedited so the error is
> legible rather than tidied away.

**Pixels first.** 49 stride-6 frames, f1-f283 — the opening 11.8 s of the film,
watched in sequence for the first time. What 12 seconds of beat 1 actually looks
like:

```
f1-f19     the monocoque. READABLE.
f25-f43    a translucent blue wedge fills the frame vertically. Abstract.
f49-f91    stacked pale plates. Abstract slabs; f79-f91 are extreme close smears.
f97-f109   one huge pale blue blade fills the frame, near-identical for 0.5 s.
f115-f139  the monocoque again, obliquely. Partly readable.
f145-f163  the halo and structures over a dark floor. The FIRST coherent view.
f169-f235  closer again, blue-lit internals. Partly readable.
f241-f283  a large grey wing panel with mounting studs. Abstract slabs again.
```

There is never a frame in which you see **what the object is**.

**Measured, and this is the finding.** Apparent car length as a fraction of frame
width, over all 792 frames of beat 1:

```
minimum   76.1 %   @ f754   (camera 8.32 m from the car — its furthest, ever)
p1        76.8 %
p10       78.4 %
median   143.7 %
frames under 100 % of frame width   212 of 792   (8.83 s)
frames under  80 %                   97 of 792   (4.04 s)
frames under  60 %                    0 of 792   (0.00 s)
frames under  50 %                    0 of 792   (0.00 s)
```

**Zero frames under 60 %.** The camera's greatest distance from the car in the
whole beat is **8.32 m**, and that is f754 — the close-out push, the beat's own
widest moment. Every one of the other 791 frames is tighter.

For contrast, every other beat has a genuine wide:

```
2_launch    widest 72.52 %   (max distance    7.4 m)
3_breach    widest 35.87 %   (max distance   14.1 m)
4_transit   widest 11.64 %   (max distance   47.6 m)
5_lap       widest  4.57 %   (max distance  187.2 m)
6_ending    widest  0.96 %   (max distance  338.0 m)
```

**Beat 1 is not short of shot-scale VARIETY — it has 2.10 octaves between p10 and
p90, the second-highest in the film.** That is the trap in the number. All 2.10
octaves sit on the *tight* side of the object: the range is 76 % to 336 %, i.e.
from "just fills the frame" to "three and a half times the frame". A variety
metric alone would have called beat 1 the best-covered beat in the film. **The
scale never crosses to the other side of 100 %.**

**Why this is a sequence finding and not a still finding.** Any single beat-1
frame reads as a deliberate macro shot, and several are beautiful. Seven hundred
and ninety-two of them in a row, with no wide, is a beat in which the audience is
never told what they are looking at. The brief's rule — *"no part seats without
having been seen"* — is satisfied exactly. **The car is not.**

**It compounds with R2-425 and R2-321 rather than duplicating them.** R2-321
found the tour is smeared (88 % over 20 px); R2-425 found it is shot 84 degrees
nose-down with no subject at f25. This adds that even where a frame is sharp,
level and well-composed, **it is still inside the object.** The three have
different fixes: shutter, angle, and distance. Only the third produces an
establishing shot.

**Qualification on the proxy.** This measures the assembled car's 5.698 m length
held perpendicular to the view axis. During beat 1 the car is EXPLODED across a
field wider than the assembled car, so the true subject is larger than modelled
here and every percentage above is, if anything, **understated**. The conclusion
does not depend on the proxy's precision: the binding number is the camera's
maximum distance of 8.32 m from a 5.7 m object, which is a direct path
measurement with no proxy in it at all.

**What would settle the remaining question:** whether the beat needs one wide, or
whether the close-out at f648-f792 (the region a review called the best material
in the film) already functions as a delayed establishing shot arriving 27 seconds
late. The dense block f745-f864 is queued and covers exactly that.

---

## R2-430 — **RETRACTION of R2-429.** The film DOES establish; and my retraction's own arithmetic was wrong too

**R2-429 claimed "the film has no establishing shot", on the basis that the car is
never smaller than 76.1 % of frame width. Both the claim and the number are
withdrawn.**

### The number: 76.1 % was wrong by 1.70x, and it is instructive HOW

`tools/` computed apparent size as `(5.698 m x lens / 36 mm) / distance` — the
subtense of the car's **length**, at the distance to the car's **centre**. Two
errors, compounding in **opposite directions**:

```
f697, camera-to-car-centre 7.29 m, lens 36.33 mm

  subtense of LENGTH 5.698 m at the CENTRE distance    0.7890   <- what I published
  subtense of WIDTH  2.005 m at the CENTRE distance    0.2776
  MEASURED off the delivered pixels                    0.4630
  properly projected bounding box                      0.4746
```

* **Wrong dimension.** The car at f697 is head-on; its visible extent is its
  ~2.0 m width, not its 5.698 m length. Inflates by **2.84x**.
* **Wrong depth.** The widest visible feature is the front wing, on the car's
  NEAR face — 4.37 m away, not the centre's 7.29 m. That gap is 2.92 m, which is
  half the car's length (2.85 m). Deflates by **0.60x**.

**Net 1.70x too large — and because the two errors partly cancel, the result
looked plausible.** That is why it survived: a separate agent's tool reproduced
the same figure independently, so the number was carried twice before anyone
projected it through the actual camera.

**The fix is to project the car's oriented bounding box through the camera** and
take the screen-space extent, which makes no assumption about orientation or
which face is nearest. Validated against the pixels before being used:

```
projected bounding box at f697   0.4746
measured off r1full_000697.png   0.4630   (front-wing tips at x=355 and x=947 of 1280)
                                 agree to 2.5 %
```

The pixel measurement was itself read off a ruler drawn on the frame, because two
automated detectors I wrote first returned 0.90 and 1.00 — they latched onto the
turntable and the dark rear wall. **A third instrument failing is why the ruler
went on the picture.**

### What the corrected instrument says

```
beat          corrected median   old (broken)   ratio    corrected MIN
1_assembly          135.0 %         143.7 %      0.94        45.1 %
2_launch            130.4 %         101.0 %      1.29        76.1 %
3_breach             44.5 %          52.7 %      0.84        32.2 %
4_transit             9.4 %          12.6 %      0.75         4.4 %
5_lap                12.9 %          14.9 %      0.87         3.0 %
6_ending              4.1 %           1.9 %      2.20         1.1 %
```

**Beat 1's true minimum is 45.1 %, not 76.1 %.** The beat pulls back to a genuine
full shot. R2-429's conclusion is dead on its own corrected evidence.

### The claim that must NOT be inherited

R2-430's first draft said *"the measurement was right; the threshold was
invented"*, and defended it with *"a subject occupying 76-86 % of frame width is
a full shot"*. **That sentence is false and is withdrawn.** A car at 76 % of frame
width nearly fills the picture; it is not an establishing shot. The real
establishing frames sit at **0.45-0.50**. Anyone leaning on "76 % is a full shot"
later would be reasoning from a figure that never existed.

**So the retraction was right in its conclusion and wrong in its reason.** The
measurement was not right. What was right was **opening the frames** — the eye
beat both tools, and it beat them before either was corrected.

### What survives, and it rests on pixels rather than on any formula

The car first reads whole at **f631, t = 26.3 s**, read directly off the contact
sheet of f601-f703: f601 (25.0 s) and f625 (26.0 s) are partial, f631 is the first
frame showing the complete car with headroom, railings and legible `MERIDIAN`
signage. The sustained readable stretch is the **last 5.71 s of a 33.0 s beat**.

**Independently corroborated:** R2-321 arrives at the same region by an unrelated
route — camera smear, 1.5 px median across f648-f792 against 54.7 px over the
presentation tour, a factor of 36. **Two measurements with nothing in common name
the same ~137 frames**, and neither uses the broken subtense.

**The film runs 26 seconds — 21 % of its runtime — before showing what it is
about.** That is the finding. Whether it is too long is a judgement for the watch.

### Consequences for other entries in this document

* **R2-429 is withdrawn in full.** Its pixel observations of f1-f283 stand; its
  headline, its 76.1 % figure and its cross-beat contrast table do not.
* **R2-422's table is superseded by the corrected one above.** Its mid-lap finding
  **strengthens**: f2035-f2227 measures a corrected median of **4.22 %** (not
  7.1 %), min 2.96 %, against a beat-5 median of 12.91 %. The car is at **one
  third** its usual size for those 8.04 s, not half. The 8.04 s duration is
  unchanged — it comes from the camera path, not from this instrument.
* `tmp/shotscale.npy` is superseded by `tmp/shotscale_v2.npy`.

### R2-428, second instance: f2001, and the control that settles it

```
ODD  2001: far flatter than its neighbours: sd 0.1007 vs 0.2382 median over 12 frames (11 MADs)
```

Same fill-order artefact, and this time confirmed three independent ways rather
than asserted — R2-430 is a fresh reminder of the cost of asserting.

1. **The control.** `r2b56_720` rendered the same frame number at the same
   720p/64 spec from a different blend. Its beat-5 frames run **mean sd 0.1338,
   range 0.0555-0.2253** — and **its own f2000 measures sd 0.0828**, flatter than
   the 0.0992 being flagged here. Flat is normal for this part of the lap.
2. **The picture.** f2000 opened: a high aerial of the car on a wide sweeping
   corner, the majority of the frame smooth low-contrast asphalt. There is
   genuinely very little variance in it. Nothing is wrong with the frame.
3. **The neighbours.** The 12 frames it was compared against are stride-6 beat-1
   showroom frames at sd ~0.24 — busy interiors full of parts.

**Why only f2001 and not f2000, which is statistically identical** (mean
0.3236/0.3228, sd 0.0992/0.1007): f2001 is the last frame in the delivered
sequence, so its whole comparison window lies *behind* it in beat 1, while
f2000's window still contains f2001. The asymmetry is an edge effect of the
window, not a difference between the two frames.

**A build difference worth recording while it is in front of us.** Same frame
number, same spec, two blends:

```
             mean      sd
film6.blend   0.2613   0.0828     (r2b56_720)
film14_breach_r6  0.3236   0.0992  (this pass)
```

**+23.8 % mean, +19.8 % sd.** That is a real change between builds, consistent
with the relighting work recorded between `film9` (3,737 W) and the shipping
46,203 W interior load. It is noted, not chased: the two are different worlds and
this is not a like-for-like comparison. It does mean **`r2b56_720` may be used as
a control for SHAPE and VARIANCE but never for absolute level.**

---

## R2-431 — the transparent-bodywork finding, confirmed independently from this pass's own frames

Reported to me from another block; corroborated here rather than taken on report,
because it decides whether beats 2-6 are worth rendering before `film16`.

**`r1full_000697.png`, the beat-1 close-out, crop (470,230)-(830,530) at 3x** — a
clean head-on three-quarter of the completed car, the best-composed frame in the
beat. All five sub-claims are visible in this single frame:

* **bodywork transparent** — the nose and monocoque read as blue-teal glass with
  an internal lattice plainly visible THROUGH the surface;
* **cockpit empty** — the tub interior is open to view, no driver;
* **no carbon weave** — surfaces are smooth glass and chrome;
* **no decals** — one faint moulded marking on the nose, no livery;
* **tyres** smooth, no sidewall lettering or texture (slicks legitimately have no
  tread, but the sidewalls are blank too).

It is not an artefact of one shot: the same glass reading appears at f1, f25 and
f43 in the opening, and the "translucent blue wedge" that made f25 unreadable in
R2-425 **is this defect**, seen from 84 degrees above at close range.

**Why beats 2-6 were still rendered, and it is a judgement rather than a fact.**
Every defect class this pass hunts — beat seams, breach continuity, the shard
un-break, the 89.79 m proxy travel, geometry pops, temporal flicker, camera kinks,
shot-scale pacing — is **invariant to paint, weave, decals and driver**. Against
that, 2,186 frames of the film had been seen as **four instants** and the one-shot
law had never been checked in pixels at a single seam.

**Two caveats that must travel with any beat 2-6 verdict from this pass:**

1. **Readability verdicts are pessimistic and provisional.** A glass car against a
   busy world reads worse than a painted one will. Any "the subject does not read"
   finding in beats 2-6 must be re-judged after the material fix. Structural
   pacing — shot scale, beat length, seam continuity — is unaffected.
2. **Beat 3 is asymmetric evidence.** Glass shards against a glass car is a poor
   read, so a verdict of *"breach continuity is clean"* would be **weak** evidence
   from this pass, while *"breach continuity is broken"* would be **strong**. The
   known un-break (483 mm -> 17 mm, pane bulging as a sheet and springing back)
   should be visible regardless; if it is NOT visible here, that is not evidence
   it is absent.

---

## R2-432 — A MONITOR MUST REPORT CHANGES, NOT STATE. Stated as a law, because it has now arrived through two different doors

> **A watcher that reports STATE rather than CHANGES raises the same alarm
> forever, is throttled off as noise, and ends up DEAF WHILE STILL LOOKING
> ARMED.**

That is the same terminal condition as a watcher whose filter matches the
all-clear (R2-427's first addendum, where `grep "blank"` matched *"...and not
blank"*). **The two bugs are opposites** — one fires when nothing is wrong, the
other keeps firing when something is wrong and already understood — and they
converge on an identical outcome. Two independent routes to one failure state is
much stronger evidence that the shape is real than either instance alone, which
is why this is written as a law rather than as a second incident.

**The corollary that makes it actionable: CLEARED is a first-class event.**
R2-428 *predicts* that f900/f901 will stop being flagged once the dense block
f865-f984 surrounds them with real beat-3 neighbours — and that **if they do not
clear, it becomes a finding about the authored exposure ramp** at
`exposure_ramp_frames = [901, 916]`. A watcher that only reports onsets can never
deliver a predicted all-clear, so it cannot close the very hypothesis that
justified logging the flag.

**Tested by seeding a state file rather than by waiting for reality** — the same
method as R2-427's selftest, and for the same reason: a transition you wait for
is a transition you cannot force.

```
1. empty state, flags present     -> "ODD NEW 2 frame(s): 2000,2001"
2. unchanged on the next poll     -> SILENT                <- the bug
3. state seeded with a stale 901  -> "ODD CLEARED on 1 frame(s): 901"
4. state seeded without 2001      -> "ODD NEW 1 frame(s): 2001"
```

---

## R2-433 — FIXING ONE INSTANCE OF A DEFECT IS NOT FIXING THE DEFECT

Having written the delta logic above and verified it four ways, the same script
still contained the identical bug **four lines below the fix**:

```sql
-- frame flags: fixed, diffed against a state file
-- job failures, immediately underneath, NOT fixed:
SELECT ... FROM jobs WHERE seq='r1full' AND state='failed'
```

That query returns every failed job on **every** poll. One failure would have
repeated indefinitely, exactly as the frame flags did, and throttled the watcher
into the same deafness the delta logic was written to prevent.

Fixed with a 310 s window on `finished`, and verified against a **real** failed
job in another sequence rather than a hypothetical one:

```
blankseq, all-time window   -> 39d266775dd8 failed finished=1785279097
blankseq, 310 s window      -> (empty)
```

**The general form:** when a defect is found, the next question is not "is it
fixed" but **"where else does this shape appear"** — starting with the same file,
the same function, the adjacent lines. This project's own history has the pattern
(`FILM_EXPOSURE` hardcoded in three places; `SHIPPING.md`'s ship name copied into
`input_stamp.py`); this is the same failure at a ten-line scale.

---

## R2-434 — ~~THE LADDER CANNOT BE STARVED~~ **REOPENED — I TESTED ONE OF TWO STAGES**

> **The headline is withdrawn. The measurement below is correct and is kept,
> but it establishes a property of the RANKING ONLY, and ranking is not
> sufficient for service.** A second gate, `Broker.cheaper_to_finish`, sits
> DOWNSTREAM of the ranking and vetoes the starvation switch on a different
> question entirely. See R2-435. Empirically: `r2451` was starved **6,250 s**
> (104 min) with its scene never uploaded at all, which the 27-minute bound
> below does not permit.

A concern was raised that the sequence pass would lose every race against a
continuous stream of short, high-priority verification renders from four other
agents, and finish days late without there ever being an hour of visible stall.
**Tested, and it does not happen.**

### The existing guarantee, driven under continuous arrival

`broker/db.py`'s `oldest_waiting_scene` orders scenes by **effective age**:

```
effective_age = (now - created) + clamp((100 - prio) * 20 s, +/- 1800 s)
```

`test_priority_cannot_starve_a_scene` already asserts a bound — but it is
**static**, two jobs in a fixed queue, and says nothing about arrival. So the
scenario was rebuilt against the real query in a temporary database: twelve
ladder jobs at prio 90-130, against **three fresh prio -1000 jobs regenerated at
every step, forever**.

```
  t (s)  t (min)   winner   ladder eff  rival eff
      0      0.0    rival          200       1830
    800     13.3    rival         1000       1830
   1600     26.7    rival         1800       1830
   1700     28.3   LADDER         1900       1830
   4000     66.7   LADDER         4200       1830
```

**The rival line is PINNED at 1830 s and cannot rise.** A newly arrived job has
real age ~0, so its effective age is its clamp and nothing more — arriving *more*
of them, or at *lower* priority, changes nothing. Only the ladder accumulates real
age, and real age is unclamped. Crossover is `CLAMP + rival_age - my_boost` =
1800 + 30 - 200 = **1630 s**, observed in (1600, 1700].

**Bound: the ladder waits at most ~27 minutes, whatever arrives.** This is
`SCENE_PRIO_BOOST_MAX_SEC` doing exactly what its comment claims. **No new
mechanism is needed and none was added** — adding priority aging on top of
priority aging would have been the "starvation cap that bounded nothing" a second
time.

### What IS at risk, and it was mine

**Preemption happens only BETWEEN jobs.** Nothing interrupts a running chunk. So
the worst-case wait for a critical-path verification render stuck behind the
ladder is:

```
threshold (they must first accumulate this much wait) + my chunk duration
```

with the threshold set by `starve_threshold()` = `max(300, reload_cost x 2.0)` —
**2850 s for this 4.99 GB scene** (1126 s at the load speed this instance is
currently showing).

```
chunk    duration    worst wait (T=2850s)   (T=1126s)
 120f       2.08 h          2.87 h            2.39 h     <- as queued
  60f       1.04 h          1.83 h            1.35 h     <- re-cut to this
  20f       0.35 h          1.14 h            0.66 h
```

**Re-cut from 120-frame to <=62-frame chunks: 22 jobs, the same 1,247 frames and
the identical coverage, longest chunk 1.07 h.** Their worst-case wait behind me
drops from 2.87 h to 1.83 h.

**Why not go smaller.** The floor is the threshold itself, and the threshold
exists to stop switch thrashing — below ~60 frames the wait is dominated by the
2850 s term, so further cuts buy little while costing duty cycle: I yield at the
first boundary *after* the threshold is crossed, so shorter chunks mean less
rendering per turn against a fixed ~27 min re-win and a ~1425 s reload. 60 frames
is where the two curves cross.

**A side benefit worth naming:** 22 chunk boundaries instead of 12 doubles the
number of places a batch seam could appear — which is a *feature* for this pass,
because batch seams are on its hunting list and every boundary frame is now known
in advance. `spec_hash` is identical across all 22, so a settings drift would be a
409 rather than an invisible seam.

---

## R2-435 — CHECKING ONE STAGE OF A DECISION IS NOT CHECKING THE DECISION

R2-434 seeded a queue, drove the **real** `oldest_waiting_scene` query under
continuous arrival, and measured a 28.3-minute bound. The method was right and
the result is reproducible. **It was still the wrong answer, because the switch
is RANKING AND VETO and I measured only the stage I pointed the test at.**

```
next_job()
  |
  +-- oldest_waiting_scene()   <- RANKING. R2-434 tested this. Bound holds.
  |
  +-- cheaper_to_finish()      <- VETO.    Not tested. Unbounded. The real gate.
```

`broker/app.py:385`. If the loaded scene's queued work can be drained for less
than a round trip, the starvation switch is cancelled — **at any priority**,
because this gate never consults `prio` or effective age at all. The proof that
it is a veto rather than a ranking effect: another agent submitted at
`--prio -1000` and its jobs did not move until the payback term was relaxed.

**This is the sibling of the lesson I had written one entry earlier.** R2-433
says *"fixing one instance of a defect is not fixing the defect."* The same
shape, one level up: **checking one stage of a decision is not checking the
decision.** A seeded-queue test against the real code is exactly the right
method and it still only measures what it is aimed at. Before claiming a
property of a decision, enumerate its stages — and test that the list is
complete, not just each item on it.

---

## R2-436 — the work estimator was wrong by 67x on the only job class the ladder has

`cheaper_to_finish` priced the loaded scene as:

```python
queued = self.db.depth_by_scene().get(current, 0)   # a COUNT OF JOBS
per    = self.db.mean_render_sec()                  # seconds per STILL
drain  = queued * per
```

`mean_render_sec` counts stills only, and its docstring says so deliberately —
`seq IS NULL` is load-bearing there, because averaging a sequence job's
hours-long `render_sec` into a per-still mean wrecks the queue ETA. **The bug is
not in that function. It is that `cheaper_to_finish` asked it a question it
never claimed to answer.**

Measured on my own queue, 22 jobs / 1,247 frames:

```
OLD pricing   22 jobs x 52.7 s  =    1,159 s   (0.32 h)
NEW pricing   1,247 frames x 62.3 s = 77,688 s  (21.58 h)      67x
round trip    2.0 x 1,550 s reload  =  3,100 s
```

1,159 <= 3,100, so the veto fired and held. **A scene holding 21.6 GPU-hours was
judged finishable inside a 52-minute round trip.**

Fixed by `db.pending_work_sec(scene)`, which prices each queued job as what it
actually is — a sequence job at `frames remaining x mean_frame_sec`, a still at
`mean_render_sec`. `mean_frame_sec` already existed and already prefers the
sequence's own frames as its estimator.

### The bound, and the FIXED bound that was wrong first

My first attempt capped the veto by the *waiting scene's wait*
(`SCENE_VETO_MAX_SEC = 1800`). **The suite caught it: 375/377 against a 377/377
baseline**, and the two failures were exactly the test that protects this
behaviour. That test seeds a rival which has waited **2,400 s** against a loaded
scene holding 42 s of work behind a 180 s round trip — draining is genuinely
correct there, and it records the measured 2026-08-03 incident where two 292 MB
scenes traded the worker every job at 89 % overhead.

**A fixed cap on the rival's wait re-creates the exact thrashing the veto exists
to prevent.** The distinction I had missed:

> in the legitimate case the work **runs out**; in the starvation case the scene
> is continuously **replenished**.

So the bound belongs on the veto's **own promise**. It claims the scene drains in
`drain` seconds; if it is still vetoing well past that, the claim was false. The
promise recorded is the **first** one, so topping the scene up cannot extend the
grace. `SCENE_VETO_GRACE = 3.0`, floored at `SCENE_STARVE_SEC` so a tiny drain
still gets a fair chance to finish.

### Controls, run against the real `Broker.cheaper_to_finish`

```
PASS  POSITIVE  ladder loaded, 1247 sequence frames priced 20.54 h -> no veto
PASS  NEGATIVE  7 stills, 42 s of work, rival waited 2400 s        -> VETO, 42 s
PASS  BOUND     same scene, veto running 6250 s past a 42 s promise -> no veto
```

**The NEGATIVE control is the one that matters** and it is the rubber-stamp
guard the fix was required to have: the 2026-08-03 case must still be vetoed, or
the fix has simply broken the veto in the other direction and reintroduced
89 % switch overhead.

**Offline suite: 377/377, identical to the unpatched baseline** — which was
established by running the same suite on an untouched copy first, because
attributing a regression before measuring the baseline is a failure this log
already records.

### One thing the fix does NOT do, stated because it would be easy to assume

**Correct pricing alone does not end the ladder's starvation.** The negative
control proves it: when another agent's small scene is loaded with two genuinely
cheap stills, the veto is still correct and the ladder is still not served. What
the pricing fixes is the **reverse** direction — it stops the ladder's own scene
from vetoing everyone else once it is loaded. Only the promise bound ends the
starvation. They are two defects that happened to live in one expression.

---

## R2-437 — A CLEARED FLAG DOES NOT CARRY ITS OWN CAUSE, and my watcher asserted one it never checked

R2-432 made CLEARED a first-class event, and the justification was that R2-428
*predicts* f900/f901 stop being flagged once the dense block f865-f984 surrounds
them with real beat-3 neighbours — with the standing test that **if they do not
clear, it becomes a finding about the authored exposure ramp**.

On 2026-08-04 16:5x the watcher fired:

```
ODD CLEARED on 2 frame(s): 900,901  <- expected once their range became contiguous
```

**The clear is real. The stated cause is fabricated, and the standing test was
NOT satisfied.** Checked rather than believed:

```
frames delivered between f890 and f930:   900, 901      <- the block never landed
beat-2 frames that HAD landed, luma:      0.4180 .. 0.4662
f900 / f901 luma:                         0.4471 / 0.4404
```

f900/f901 stopped being outliers because **unrelated frames 100 frames away**
brightened the neighbourhood median until it bracketed them. Their own range is
still empty. **f901 still has no beat-3 neighbour, so the exposure-ramp
hypothesis is still open** — and a canned message had just declared it closed.

**The defect is in the watcher, and it is a familiar shape.** The string
`"<- expected once their range became contiguous"` was printed on *every* clear,
unconditionally. It reads as a diagnosis and is a constant: it says the same
thing whether the cause is present or absent, which is the same failure as a
metric that reads identically with the defect present and absent (R2-418) and a
filter that matches the all-clear (R2-427).

Fixed to report the transition and explicitly refuse to explain it:

```
ODD CLEARED on 2 frame(s): 900,901  -- CAUSE NOT DETERMINED: a flag can clear
because the frame's own range filled in, OR because unrelated frames elsewhere
shifted the neighbourhood statistics. Check which.
```

**The general form, and it is the sharpest version of this pass's recurring
lesson:** an event and its explanation are two different claims. Emitting them
together as one line makes the unverified half inherit the credibility of the
verified half. **A monitor may report what happened. It may not report why.**

**Consequence for the pass:** R2-428's exposure-ramp test is still pending and
still worth running. It requires f865-f984 — queued, not yet rendered. When that
block lands, f901 acquires genuine beat-3 neighbours and the question can be
asked properly for the first time.

### R2-437, second instance — and the operational rule that follows

Twenty minutes later the watcher fired again, now with the corrected wording:

```
ODD CLEARED on 2 frame(s): 2000,2001  -- CAUSE NOT DETERMINED ... Check which.
```

Checked. **Same cause, and the canned message would have been wrong a second
time.** f2000/f2001's own range is still empty — the only frames delivered
between f1900 and f2019 are f2000 and f2001 themselves. What changed is 1,200
frames away: beat-2 frames f800-f807 landed with `sd` falling 0.2490 -> 0.2152
as the camera moves, and f900/f901 sit at 0.18, which dragged the neighbourhood
median down until f2000/f2001's 0.0992/0.1007 stopped reading as an outlier.

**Two flags raised and two cleared in this pass, and in all four cases the cause
was frames elsewhere rather than the frame's own neighbourhood.** So the rule,
stated plainly for anyone reading `rq seq status` on a partially-filled
sequence:

> **While a sequence is being filled out of order, ODD is a statement about the
> DELIVERED SET, not about the frame.** Flags will appear and disappear as
> unrelated ranges land. Neither an onset nor a clear is evidence about the
> frame it names until the frames around it exist.
>
> **This does NOT weaken the detector, and reading four "the cause was
> elsewhere" corrections as though it did would be the wrong conclusion.** The
> check is behaving correctly and its message says exactly what it measured —
> *"does not match its neighbours"* — which was true every time. What the rule
> establishes is **when the check becomes USABLE: only once the range around a
> flagged frame is contiguous.** That is a schedule, not a defect. Every dense
> block in this pass was queued precisely to make it true at the frames that
> matter, so the rule is a statement about this pass's fill order, not about
> the instrument.

---

## R2-438 — THERE IS NO EXPOSURE RAMP. `INTERIOR_STOPS = 0.0`, and two of my own entries said otherwise

R2-420 and R2-428 both describe `exposure_ramp_frames = [901, 916]` as
**"~1 stop over 16 frames"**. That is wrong and both are corrected here.

`anim/build_camera_rig.py`:175 reads

```python
INTERIOR_STOPS = FX.INTERIOR_STOPS if FX else 0.85
```

and I took the **fallback**, 0.85, for the value. The real one, in
`world/film_exposure.py`:238, is:

```python
INTERIOR_STOPS = 0.0
```

so `interior = daylight - 0.0 = daylight`, and the two keyframes at f901 and
f916 hold **identical values**. The ramp is a no-op. `film_exposure.py` states
the measured consequence directly:

> "at 0.0 the interior sits at mean 0.32-0.48 with **0.0000 % pure black on
>  every frame and the exposure never moves across all 2,978 cut-free frames**"

**And it is 0.0 for the one-shot law, which makes it the opposite of an
oversight.** From the same docstring:

> "This is ONE UNBROKEN TAKE WITH ZERO CUTS. An exposure ramp across the breach
>  is a camera visibly adjusting, with no cut to hide it behind — precisely what
>  the brief forbids."

0.85 also pointed the wrong way: it darkened the interior, which was the end
already crushing to pure black over 1.30 % of the frame. The real fix was
levelling the showroom practicals by `-FILM_EXPOSURE`.

**Reading a constant's fallback for its value is a small mistake with a large
blast radius**, because the fallback is chosen to be *plausible*. Grep the
constant, not the expression that consumes it.

---

## R2-439 — PRE-REGISTERED: the f901 test, written before f865-f984 exists

R2-428 left a standing test: if f901 still flags once its neighbourhood is
contiguous, that is a real finding. Four flag transitions in this pass have now
been explained by delivery order, and **an explanation that has worked four times
is exactly the one that gets applied a fifth time without checking.** So the
decision rules are committed here, before the frames exist, in the same form as
R2-383's nine predictions.

**What is known now:** f865-f984 is queued and unrendered; only f900 and f901
exist between f890 and f930. Exposure is authored CONSTANT across the whole film
(R2-438). The camera crosses the glass plane at f904; `f0 = cross_f - 3 = 901`.

**P1 — the exposure is flat.** Across f890-f930 the view-transform exposure does
not move, so any brightness change is CONTENT: the camera emerging through
glass into daylight. **I predict no whole-frame multiplicative step.**

**P2 — the control that makes P1 falsifiable.** If the delivered frames DO show a
coherent whole-frame brightening of order one stop across f901-f916, then
`INTERIOR_STOPS = 0.0` did not reach this blend, and **that is itself the
defect** — an iris move on screen at the breach, in a cut-free take. This is the
outcome that would make the pass worthwhile even if everything else is clean, and
it is the reason the range is worth rendering densely.

**P3 — what a persistent flag would and would not mean.** If f901 still reads as
an outlier against a full contiguous beat-3 neighbourhood, it is a real finding —
but it **cannot** be "the exposure ramp stepped", because there is no ramp. It
would be a content, geometry or lighting discontinuity at the breach, and the
diagnosis would start over.

**P4 — the smoothness test, stated as a number in advance.** On the contiguous
f890-f930 series, the second difference of `lum_mean` must carry no sample beyond
**6 MADs** of its own median. A step masquerading as a ramp is a spike there. I
predict no such sample.

**P5 — the discriminator between exposure and content, if P1 fails.** An exposure
change is uniform and multiplicative: every pixel scales by the same factor, so
the ratio between a dark region and a bright region is unchanged. A content
change is not. Comparing the ratio `p10/p90` frame to frame separates them
without needing to know what is in shot.

**P6 — REVISED 2026-08-04, AND THE FIRST VERSION WAS WRONG IN SUBSTANCE.**

The first version pinned P1-P5 to `film16.blend`. That pin is withdrawn, because
**`film16.blend` cannot answer the question at all: it has no breach in it.**
Established by another block with a complementary signature — every object
`apply_breach` CREATES is absent, and every object it DELETES is present:

```
                          film14_breach_r6   film16
BREACH_Shards (collection)        1            0
GP_b04        (pane)              2            0
GS_b04_00000  (shard)             3            0
BF_MUL05_S02  (baked piece)       3            0
GW_Right_Mull_04  round-1 mullion,
                  DELETED by apply_breach      0            2
GW_Right_Transom_0  same                       0            2
ONER          (camera, CONTROL)   6            6
```

The non-zero control is what makes the negative trustworthy: a zero from a
compressed blend is otherwise indistinguishable from a zero scene.

**And the file that CAN answer it will have a different name.**
`sim/land_breach.sh` writes `render/<film>_breach.blend`, so the target is
`film16_breach.blend`, not `film16.blend`. A pin by filename would have been
wrong even if `film16` had contained a breach.

**So admissibility is pinned to a VERIFIABLE PROPERTY, not to a name.** A build
may answer P1-P5 only if, checked on the file itself before any frame is
measured:

```
BREACH_Shards        present      (apply_breach ran)
GP_b04               present
GW_Right_Mull_04     ABSENT       (the round-1 mullion it deletes)
ONER                 present      (control - a zero here voids the check)
```

plus: **every frame in f890-f930 carries ONE `scene_hash`.** The broker records
the scene per job, so this is checkable after the fact and not merely intended.

**Why a property and not a name, stated as the general point:** a filename is a
label someone chose; the pre-registration needs a fact about the artefact. Pinning
to `film16.blend` would have been satisfiable by a file that renders an unbroken
glass wall — the test would have run, produced clean numbers, and answered
nothing. **The admission criterion has to be something the artefact either has or
does not have.**

**What is still inadmissible:** the f900/f901 frames from `film14_breach_r6`
(control data), and any frame from `film16.blend` as it stands, including the
five-frame probe. The probe is diagnostic, not evidence for this test.

**THE PROCEDURE, and it is the point of writing this down:** when f865-f984
lands **from `film16`**, run these five checks and report the result **before**
consulting the fill-order explanation. That explanation is now five for five,
which makes it the one most likely to be applied to f901 without looking. The
prior explanation is not evidence about a frame it has never been tested
against.

### R2-437, third instance — the MAD shrank, which is not how it cleared

f2000/f2001 **re-flagged** after clearing, and the cause is again elsewhere —
their own range between f1900 and f2019 is still just the two of them. But the
mechanism is not the one that cleared them, which is why it was worth checking
rather than pattern-matching:

```
CLEARED earlier : the neighbourhood MEDIAN moved toward them
                  (beat-2 frames at luma 0.418-0.466 bracketed f900/f901)
RE-FLAGGED now  : the neighbourhood MAD SHRANK away from them
                  f806-f811 landed in a tight cluster, sd 0.2054-0.2159
                  -> median sd 0.2126, spread collapsed
                  -> f2000's unchanged sd 0.0992 went from inside the scatter
                     to 11 MADs outside it
```

**Neither frame changed. Their statistics are byte-identical to when they
cleared** (mean 0.3236/0.3228, sd 0.0992/0.1007 throughout). A robust z-score has
two moving parts, and a homogeneous delivered set makes the scale small, which
makes everything else an outlier.

Fifth transition in this pass, fifth time the cause was frames elsewhere — and
the first time the *mechanism* differed.

**AND THAT IS AN ARGUMENT ABOUT HOW TO WRITE FINDINGS, not just about this
detector.** The rule was stated at the level of **what can be concluded**:

> neither an onset nor a clear is evidence about the frame it names until the
> frames around it exist

The tempting alternative was to state it at the level of **mechanism** — *"flags
drift as the neighbourhood median moves"* — which is what the first four
transitions actually showed, is more specific, and sounds more expert. **It would
have been falsified by the very next case**, where the median barely moved and
the MAD collapsed instead.

A robust z-score has two moving parts and this pass has now been bitten by both.
A finding written about the mechanism is only as durable as the mechanism you
happened to see first; a finding written about what may be concluded survives
mechanisms it never anticipated. **Prefer the conclusion-level statement, and put
the mechanism underneath it as evidence rather than as the claim.**

---

## R2-440 — the control set, and an honest account of what the probe-first design did and did not catch

### The `film14_breach_r6` frames are promoted from "sunk cost" to reference data

157 frames at `out/seq/r1full`, 144 MB, camera `ONER`, spec `2b46bc3e1868e66d`,
scene `6eff712098a43044`. **Do not delete them.** They are the only rendered
record of a film that *has* its breach, and beats 2-6 share their camera with
every candidate that follows, so:

* when `film16_breach.blend` exists, `r1full` is the direct A/B for whether
  re-applying the breach reproduces what r6 had — **same camera, different
  world, so every difference is the rebuild**;
* f900/f901 are the only breach frames anyone has rendered from a scene that
  contains a breach;
* beat 2 is contiguous f793-f816+, which is a usable continuity baseline.

Their value went **up** when `film16` turned out to be breach-less. A control is
worth what the thing it controls for is worth.

### What the probe-first sequencing actually did here, said plainly

The pass was held one step short of queueing 22 chunks against `film16`. It would
have rendered **~21 hours and most of the remaining budget** of a car driving
through an **unbroken glass wall**, with round 1's undeformed aluminium grid
standing across it and an intact showroom behind it for beats 4-6 — the film's
pivot, plus every continuity frame downstream.

**But the probe did not catch it. Another block did, from the object graph,
while the 7.5 GB push was still queued.** The five probe frames have not
rendered. Claiming this as a save for the probe would be claiming credit for a
result that arrived by another route.

**What is defensible is the sequencing, not the instrument.** The rule "probe
before you commit a multi-hour pass to an unrendered build" is what created the
interval in which somebody else's finding could land and be acted on. A pass
queued the moment `film16` appeared would have been running before the object
graph was ever inspected, and the discovery would have arrived as a cancellation
rather than as a hold.

**That is the honest version and it is still an argument for keeping the rule:**
the value of a gate is not only what it detects itself, it is the delay it
imposes before an irreversible commitment. Both this and R2-431's
"render beats 2-6 anyway" judgement were decisions about **what a frame can still
be worth when the build under it is known to be changing** — and they went
opposite ways, correctly: geometry pops and beat seams survive a car repaint,
but nothing survives the absence of the event the beat exists to show.

---

## R2-441 — the attribution test has lost its conditions, and that is the honest result

R2-436 fixed a work estimator that priced a sequence job as one still — 67x low —
so `cheaper_to_finish` vetoed the starvation switch and the ladder's scene held
the GPU. The fix was verified by controls and by the 377/377 offline suite. The
outstanding item was a **live** demonstration: the ladder's scene loaded, holding
many hours of sequence work, another scene waiting — does it yield?

**That configuration occurred, and it does not discriminate.**

```
19:00 switching FROM film16_breach.blend TO r2521/r2521_after6.blend
      after 1 job(s) — another scene has waited 2978s, over the 300s this switch has to beat

  queue at that instant, captured rather than reconstructed:
    r1ladder     r2full        21 jobs, 1211 frames queued   = 14.7 h of work
    r2521-paint  r2521after6    1 job,     4 frames running
```

The scene yielded. But the arithmetic that decides *why* is:

```
  round_trip           <=   300 s     (the message printed a 300 s threshold, and
                                       threshold = max(300, reload_cost x 2.0),
                                       so reload_cost <= 150 s)
  OLD pricing drain     =   927 s     (21 jobs x 44.15 s/still)
  NEW pricing drain     = 48464 s     (1211 frames x 40.02 s/frame, 13.5 h)

  a veto fires when drain <= round_trip
    OLD:   927 <= 300  ->  NO VETO
    NEW: 48464 <= 300  ->  NO VETO
```

**Both pricings give the same answer, so the yield is not evidence for the fix.**

**Why the conditions dissolved, and it is worth knowing.** The veto can only fire
when the loaded scene is *cheap to drain relative to reloading it*. On broker 2
`film16_breach` is cached locally and its switch is **11.7 s measured** (`scene
switch complete in 11.7s (no redeploy)`), which collapses `round_trip` to under
300 s — below even the OLD drain estimate. The 67x scenario needed an
**expensive** reload, which is what broker 1 had: a 4.99 GB scene at ~1,550 s,
giving `round_trip` 3,100 s against an OLD drain of 1,159 s.

**So the defect was real and the fix is real, but the environment that exposed it
has been engineered away** — by the bulk/verification broker split and by broker 2
having 85.9 GB of cache where broker 1 had 32.2 GB and thrashed. A scene that
never gets evicted is never expensive to reload.

**Stated as a rule, because the temptation was to keep waiting for a cleaner
firing:** a test whose conditions no longer exist is not a failed test and is not
a pending one. It is closed, with the reason recorded. Continuing to wait would
have meant eventually reporting some *other* switch as the attribution — and
every switch on this broker will now show a yield, because `cheaper_to_finish`
essentially never vetoes when reloads are cheap.

**Where the fix still matters, unchanged:** any broker whose cache cannot hold
the working set. Broker 1 was measured re-pushing scenes it already had on 8 of
19 switches. There, reloads cost minutes, `round_trip` is thousands of seconds,
and a 21-job sequence priced at 927 s would still be vetoed indefinitely. The
fix is dormant here, not unnecessary.

---

## R2-442 — THE f792/f793 SEAM IS CLEAN, measured in pixels for the first time

The film's defining constraint is zero cuts. R2-423 tested all five beat
boundaries **on the authored camera path** and found no discontinuity — but that
is a statement about the curve, not the picture, and it explicitly left open
"a light that switches, a sim that starts, an LOD that swaps".

Four of the five boundaries sit inside beats 2-6 and are covered by `r2full`.
**f792/f793 was the exception**: it needs a frame from each side of the beat-1
boundary, the beat-1 side was deliberately cancelled when the camera was
superseded, and it could only be closed once `film16_breach` existed. It is now
closed.

```
        pair   mean |d|    p99.9    >0.25
   788-> 789    0.03401   0.6124   3.036%
   789-> 790    0.03620   0.6161   3.321%
   790-> 791    0.03842   0.6165   3.631%
   791-> 792    0.04077   0.6171   4.028%
   792-> 793    0.04324   0.6275   4.433%   <-- THE SEAM
   793-> 794    0.04750   0.6337   5.105%
   794-> 795    0.05149   0.6373   5.712%
```

**The d1 series is strictly monotone across the boundary**, and the seam value
lands where interpolation puts it:

```
  linear interpolation from its two neighbours   0.04414
  measured at the seam                           0.04324
  error                                          2.05 %
```

`p99.9` (0.6171 -> 0.6275 -> 0.6337) and the hot-pixel fraction (4.028 -> 4.433
-> 5.105 %) are equally smooth. The camera is accelerating into beat 2 and the
boundary frame is simply the next sample of that acceleration. **1.092x the local
median, +0.55 MADs — indistinguishable from its neighbours.**

**And the test is stronger than it looks, because the two frames were rendered on
DIFFERENT MACHINES.** f792 came from broker 1 (instance id-031) and f793 from
broker 2 (instance id-029), hours apart, with `film16_breach` pushed separately
to each host. Identical `scene_hash 1e8d5440c349fe51` and `spec_hash
1dd9cdaf86a87876`, verified before the comparison was trusted.

So this simultaneously clears two defect classes the ladder exists to hunt:

* **the beat seam** — no discontinuity at the one boundary nothing had checked;
* **the batch seam** — "adjacent ranges rendered by two machines" is precisely
  the configuration here, and it produces no measurable signature at all.

**What it does not clear:** this is 720p and one boundary. The other four are
covered by `r2full` and will be measured the same way as their ranges complete.

---

## R2-443 — R2-439 ANSWERED. No exposure ramp defect; the flags were fill-order; P4 failed and my bound was wrong

Run against `film16_breach`, f890-f930, **41 of 41 frames contiguous**, f901's
neighbourhood **21 of 21**, one `spec_hash`, one scene — P6 satisfied. Results
recorded before consulting the fill-order explanation, as the procedure required.

| | prediction | result |
|---|---|---|
| **P1** exposure flat, any change is content | no ~1 stop rise | **PASS** — f901->f916 is **-0.038 stops** |
| **P2** control: a ~1 stop rise would BE the defect | must not fire | **did not fire** — `INTERIOR_STOPS = 0.0` did reach this blend |
| **P3** f901 flags with a full neighbourhood? | — | **does NOT flag.** The earlier ODD flags were fill-order artefacts |
| **P4** 2nd difference of `lum_mean`, no sample > 6 MADs | predicted pass | **FAIL** — 6 samples, \|z\| max 58.19, at f897, 899-903 |
| **P5** p99/p01 separates exposure from content | — | ratio moves **+70.8 %** -> **content, not exposure** |

**The exposure-ramp hypothesis is CLOSED, and closed properly.** R2-428 raised it,
R2-437 showed the four clears that "explained" it were all caused by frames
elsewhere, and R2-438 found there is no ramp to step. Now the direct test on a
full neighbourhood says f901 is not an outlier at all. **There is no iris move at
the breach** — which matters, because an exposure ramp across a cut-free breach is
the thing `film_exposure.py` set `INTERIOR_STOPS = 0.0` specifically to prevent.

### P4 failed, and the bound was mine, not the film's

```
f898 0.4473  f899 0.4414  f900 0.4469  f901 0.4400  f902 0.4553  f903 0.4489
f904 0.4466 -> f920 0.4198   monotone, no outliers
d1   f894-903  ~0.050-0.058      f904 onward  ~0.021-0.025
```

`d1` **halves in a single frame at f903->f904**, and f904 is exactly where the
camera crosses the glass plane (`cross_f`, since `f0 = cross_f - 3 = 901`). The
f901->f902 change localises to the lower-left (0.072 against 0.031 on the right;
0.077 bottom against 0.042 top) — the breach region.

The frames settle it: f899-901 are dominated by large translucent shards sweeping
across frame, f902 fewer, f903 nearly clear, f904 clean. **The camera passes
through the breach and the near-field glass exits.** The mean-luma oscillation is
each frame catching a different amount of bright specular glass; the `d1` step is
that field leaving. P5 independently said content, not exposure, before the frames
were opened.

**So P4's bound was too strict for the beat it was applied to.** A 6-MAD bound on
the second difference of mean luma is right for smooth camera work over static
content; **beat 3 contains a violent transient by design.** I set that bound in
advance, which was the correct discipline, and it was the wrong number — a
pre-registered prediction that fails and is then explained is weaker evidence than
one that passes, and it should be recorded as such rather than smoothed over.

**What was NOT observed:** the known slab un-break (483 mm -> 17 mm, the pane
bulging as a sheet and springing back). Nothing in f899-904 shows a pane deforming
and returning — what is there is shards transiting. That event, if it is visible at
all, is earlier, near impact around f865-880, and this window does not cover it.
**Absence here is not evidence of absence there.**
