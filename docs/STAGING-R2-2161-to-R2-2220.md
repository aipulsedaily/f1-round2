# STAGING R2-2161 .. R2-2220

> **⚠ READ R2-2170 BEFORE THIS SECTION.** The heading below and its "7.1 % flat"
> figure are **RETRACTED**. The instrument bug described here is real, but the
> conclusion I drew from it was wrong in the same way the bug is, and the
> corrected map is in R2-2170. The section is left standing, uncorrected, because
> a retraction that edits away the claim it retracts is not a retraction.

## R2-2161 — THE 85-SECOND FLAT RUN DOES NOT EXIST. It is one argument passed to one function.

I was sent to fix "one unbroken 85 seconds, f938 to f2978, crossing beats 3, 4,
5 and 6", described as **96.7 % of the film flat**. The brief told me to treat
every number in it as a claim and re-derive the map myself. **I did, and the
headline does not survive.**

`tools/campath_pacing.py` computes two derivatives of its image-motion signal
`S`. The fast one, `A`, is `|S[f] - S[f-1]|` — a change over **1/24 of a
second**. The slow one, `D = slow_derivative(S)`, is the change over **0.5 s**.
The file's own TIMESCALE block, lines 386-410, is unambiguous about which is
usable:

> *"Both of them measure how much the rate of image motion changes in 1/24 of a
> second, and NOBODY PERCEIVES A CAMERA THAT WAY. ... it is nearly blind to
> exactly the gesture it is being asked to detect. ... **the slow one is the one
> to read.**"*

It then computes `D` at line 494 — and **line 513 passes `A`**:

```python
runs, jr = flat_stretches(S, A, N)     # campath_pacing.py:513
```

**The flat census is built on the derivative the file spends twenty-five lines
explaining is unusable.** Re-run on the CURRENT camera path (`docs/beat_sheet.json`
as it stands, rig built this session), changing nothing but that one argument:

| derivative fed to `flat_stretches` | % flat | runs | largest run |
|---|---|---|---|
| `A` — 1 frame, **as shipped** | **96.8 %** | 4 | f938-2978 = **85.04 s** |
| `D` — 0.5 s, **the file's own rule** | **7.1 %** | 3 | f2457-2531 = **3.12 s** |

The 85-second run reproduces exactly — **it is a real output of the shipped
code** — and it collapses to 3.12 s the moment the file is read the way it tells
you to read it. Per beat, `D/S` is 38.5 / 42.7 / 65.0 / 29.5 / 30.5 / 40.4 %.
**Every beat is three to six times above the 10 % flat threshold.** There is no
flat beat in this film by this instrument's own corrected methodology.

A second, independent reason to distrust the headline: **a 96.8 % result should
have been its own reductio.** An instrument that reports a film as almost
entirely flat is reporting on itself.

Two further defects in the same census, both real but secondary:

* **The denominator is local.** `jr = mean(A)/mean(S)` over a *moving* 3 s
  window. A denominator that tracks the signal cancels exactly the beat-to-beat
  tempo differences the client is complaining about. Measured on its own saved
  output, beat 5 carries **3.0x the absolute frame-to-frame variation of beat 1**
  (0.00406 vs 0.00136) and is scored **half as jerky** (3.33 % vs 6.67 %), purely
  because its denominator is 6x larger. A uniformly fast film and a uniformly
  slow film both score ~0.
* **The Spearman 0.834 validates a channel the census does not threshold on.**
  It correlates `S` against the beat-1 pixel curve. `A` is never validated
  against anything; neither is `A/S`; neither is the 0.10 threshold. And
  `CALIB_FRAMES = (1, 792)` is **beat 1 only** — the indoor depth branch. The
  outdoor branch that produces the 85-second headline models the car on an
  infinite empty plane under a 5 km sky, with no barriers, fences or kerbs, and
  has never been correlated against a picture at all.

**Nothing in this block "fixes" the 85 seconds, because there is nothing there to
fix.** The instrument is left in place and uncorrected on purpose — it is
another agent's file, the bug is one argument, and silently changing a number
that four documents already quote is how this project got here. **It is written
up here so the next agent does not spend a day on a phantom.**

---

## R2-2162 — What IS wrong, measured by a channel neither instrument had: the subject never moves in the frame

Both existing instruments measure **the camera**. Neither measures **the
picture's composition**. So `tools/camera_tempo.py` (new, this block) adds the
channel that settles it: **where the car actually sits in frame**, per frame,
projected from the rig's own path against the real telemetry.

| beat | frames | car's distance from frame centre | car's width in frame | **car's motion across frame** |
|---|---|---|---|---|
| `1_assembly` | 790 | 0.130 | 0.851 | **0.1236 widths/s** |
| `2_launch` | 72 | 0.146 | 1.089 | **0.1907 widths/s** |
| `3_breach` | 192 | 0.053 | 0.628 | 0.0456 widths/s |
| `4_transit` | 135 | **0.017** | 0.134 | **0.0057 widths/s** |
| `5_lap` | **1524** | **0.019** | 0.154 | **0.0077 widths/s** |
| `6_ending` | 263 | **0.003** | 0.023 | **0.0007 widths/s** |

**For the 63.5 seconds of beat 5 the car sits 1.9 % of a frame width from dead
centre and moves 0.0077 of a frame width per second.** That is 16x less
composition change than beat 1 and 25x less than beat 2. Beat 6 is 270x less.

**This is why the kinetic numbers mislead.** Beat 5's camera is doing 60-95 m/s
with a median speed change of 7.3 m/s² — enormous. The *picture* is a car pinned
to the centre of frame at constant size while the background streaks. High
motion, zero event. It is the view from a train window, and it is exactly the
shot a client falls asleep in.

**And the mechanism is in the code, not inferred.** Every one of beat 5's 40
anchors is `aim_car(z_off=...)` — `lat_m` 0, `along_m` 0, `lead_s` 0 on all but
one. The aim is the car's reference point and nothing else, so the car is
*constructed* to land at frame centre. The lens then removes what little looming
is left; the doppler anchor at t=94.63 says so in its own note:

> *"The lens goes 85 -> 40 as the car closes, **so the subject stays large while
> the camera does not move at all**"*

That is a deliberate, documented cancellation of the one cue — the subject
growing as it approaches — that a pass is for. It is the composition analogue of
R2-062's `_allocate`: a fix that solved its own problem by removing a variable.

---

## R2-2163 — The fix: framing offsets in the gate's own unit, with the camera path untouched

`aim_car()` gains `frame_u` / `frame_v`: **where the car sits in the picture, in
half-frames**, resolved at emission against the actual camera position and the
actual lens.

**The unit is the gate's unit, deliberately.** `anim/build_camera_rig.py` scores
framing as `u = (x/-z) / (0.5*sensor_w/lens)` and fails a beat at 0.92. An author
writing 0.45 is writing the number the gate reads back. **The first draft of this
used frame widths and failed the gate at 0.929** — the vertical half-frame is
0.28 widths, so a "0.16 width" rise was really 0.57 of the way to the top edge.
That failure is left in the record because it is the whole argument for the unit.

**The request is clamped by the subject's own angular size.** An offset that is
tasteful at 195 m puts the car half out of frame at 26 m, where it is 24 % of the
frame wide. So the offset is reduced until the car's *edge* sits inside 0.85 of
the half-frame. That is what makes the parameter safe across beat 5's **1.6 m to
195 m** subject range without a per-anchor distance table that goes stale the
moment an anchor moves.

**The camera does not move. Only the lens direction does.** This is the property
that makes the change cheap to trust — the author's own report is identical
before and after on every positional figure:

```
camera speed          max   101.69 m/s at frame 1209      IDENTICAL
camera acceleration   max    53.75 m/s^2 at frame 2560    IDENTICAL
camera-to-car BOX     min    1.808 m at frame 2642        IDENTICAL
seam pin              frame-793 key reproduces exactly    IDENTICAL
```

Only the key count moves, 434 -> 436, because the emitter is bearing-adaptive and
the bearing now changes more.

**CORRECTION TO MY OWN CLAIM ABOVE — "the camera does not move" is true of the
AUTHORED path and not quite true of the BUILT one.** `path_point` is untouched
and every figure the author reports is identical, but the rig fits F-curves
*through the keys*, and 434 -> 436 keys means slightly different Bezier
interpolation between them. Measured on the two built paths, per beat:

| beat | max position change | max lens change |
|---|---|---|
| `1_assembly`, `2_launch`, `3_breach`, `4_transit`, `6_ending` | **exactly 0** | **exactly 0** |
| `5_lap` | **0.264 m** (p99 0.190 m) | 1.41 mm |

**Outside beat 5 the built camera is bit-identical.** Inside it, the path shifts
by up to 0.264 m — and that is the *same effect and the same magnitude* R2-087
measured when it tested enabling `speed_key` globally (0.234 m, lens 1.12 mm),
from the same cause: moving keys moves the curve between them.

**The consequence is the one R2-087 weighed and it must not be buried: this
invalidates any already-rendered frame of beat 5**, which is 1,524 frames and
about two thirds of the master's render cost. R2-087 declined to pay that for a
3.2 % improvement in a passing number. This block is paying it for a 19.3x change
in the channel the client is complaining about, which is a different trade — but
it is a real cost and it is being spent, not waved away.

### The plumbing was proved to be a no-op before any framing was authored

With `frame_u`/`frame_v` wired through `lerp_aim`, `aim_at` and `emit_keys` but
still all zero, the regenerated sheet is **byte-identical to the shipped
`docs/beat_sheet.json`**. The generator reproduces the shipped sheet with **0
diffs** both before the change and after the plumbing, so the framing track is
the only thing this block moves.

---

## R2-2164 — Beat 6 is the deadest stretch in the film and this block does not touch it

Beat 6 is contested territory (lap-down, ground fix) and the brief says
coordinate rather than overwrite. **So this is a referral, with the measurement
attached, not an edit.**

Beat 6 is the deadest beat in the film on every channel measured here:

* mean image motion `S` = **0.00466** — **26x lower than beat 5** (0.12211) and
  4x lower than beat 1.
* novelty = **0.081**, against 0.590 in beat 5 — almost nothing new enters frame.
* the car sits **0.003 of a frame width** from centre, **2.3 % of the frame
  wide**, moving **0.0007 widths/s**, for 11 seconds.

The lap-down (R2-943) already moved the car from 79 px to 230.7 px, which is the
right direction. **The remaining problem is not the car's size, it is that
nothing in the frame changes for eleven seconds.** `frame_u`/`frame_v` from
R2-2163 is available to beat 6's owner and needs no camera move to use.

---

### The abstraction was checked against the built path, and my first reading of it was wrong

An authoring unit is worth nothing if the frame does not end up where the anchor
asked. So all 38 anchors were compared against **where the car actually lands in
the rig's own built path**:

* **Horizontal: worst deviation 0.084 half-frames, typically 0.01.** The car goes
  where it is put.
* **Vertical: a systematic −0.06 to −0.15 offset**, which on first look I
  annotated as the subject-size clamp firing. **That was wrong.** It is the
  pre-existing `z_off` — every anchor aims 0.55–0.80 m *above* the car's
  reference point, so the reference point sits that far low in frame. Predicting
  the term as `−(z_off/D)·lens/(0.5·sensor_h)` and subtracting it leaves
  residuals **under 0.02 half-frames** on 33 of 38 anchors.

The remaining outliers are real and understood: at t=109.60 the camera is
directly over the car at close range, where `z_off` subtends −0.76 half-frames
and the small-angle prediction above stops being valid; at t=76.00 and t=55.70
the subject-size clamp genuinely fires. **Those are the clamp doing its job, not
the resolver missing.**

Worth stating because it nearly went in the other direction: the first version of
this check printed "clamped by subject size" against 20 anchors on a threshold I
had picked, and that annotation was an artefact of the threshold rather than a
property of the run. The z_off decomposition is what distinguishes them.

### What it measures, after

| beat | car's motion across frame, BEFORE | AFTER | change |
|---|---|---|---|
| `1_assembly` | 0.1236 | 0.1236 | — |
| `2_launch` | 0.1907 | 0.1907 | — |
| `3_breach` | 0.0456 | 0.0456 | — |
| `4_transit` | 0.0057 | 0.0057 | — |
| **`5_lap`** | **0.0077** | **0.1489 widths/s** | **19.3x** |
| `6_ending` | 0.0007 | 0.0007 | — |

Beat 5 goes from **16x less** composition change than beat 1 to **1.2x more**.
Over the worst 20 s window — f1959-2439, the helicopter arc through T10 and the
doppler pass — it is **0.0042 -> 0.1917 widths/s, 45.6x**. The aim gate reads
beat 5 at **12.02 deg against a 22.0 bound** and framing **0.754 against the 0.92
margin**: the fix uses about half the headroom available to it.

### AND HERE IS WHAT THIS FIX DOES NOT DO — measured, not hedged

**It does not change how much the picture moves. It changes what the picture is
of.** Run through `campath_pacing`'s validated image-motion channel `S` over
beat 5:

| | mean `S` | `D/S` (0.5 s) | novelty |
|---|---|---|---|
| BEFORE | 0.12211 | 30.5 % | 0.590 |
| AFTER | 0.11804 | 29.3 % | 0.592 |

**Whole-frame optical flow is flat to within 3 %, and slightly DOWN.** That is
the honest consequence of not moving the camera: the background streaks exactly
as it did. The claim this block makes is narrow and it is the only one the
measurement supports — **the subject now travels across the frame instead of
being pinned to its centre.** Whether that is what converts "I get sleepy" into
attention is a question for a viewing, not for this instrument, and the A/B is
cut so it can be lost.

Three further limits, stated so nobody has to rediscover them:

* **Beats 3 and 4 are untouched.** Beat 4's aim gate has only 3.75 deg of
  headroom (10.25 against a 14.0 bound), which is not enough for a framing move
  worth making. Beat 3 has 16 deg spare and is the obvious next candidate.
* **No acceleration or direction change was added to the camera itself.** The
  brief asked for all three levers; this delivers composition change only. The
  positional envelope is byte-identical on purpose, because that is what made the
  change cheap enough to trust in one pass.
* **`speed_key` is still off for beat 5**, and R2-087's measured refusal to
  enable it globally still stands *for this camera* — it found "nothing on the
  other side of it" because the camera's speed does not vary. That reasoning is
  conditional on a camera that does not change speed. **Any future pass that adds
  speed variation to beat 5 must re-open R2-087, because the emitter is
  bearing-driven and would be structurally blind to the change.** This pass adds
  no speed variation, so it does not need it: the emitter picked up the extra
  aim movement on its own and went 434 -> 436 keys.

---

## R2-2168 — RETRACTED IN FULL. The rig is bit-exact deterministic; the "0.2 degree noise floor" was my own arithmetic

**I published, one commit ago, that `anim/build_camera_rig.py` is
nondeterministic at ~0.2 degrees, on 48.1 % of frames. That is false and the
retraction is the finding.**

Confirming "only my beats moved" appeared to show rotation differing on 2,157
frames, 377 of them in beat 1, which my change cannot reach. I ran the rig twice
on the identical sheet, measured ~0.19 deg between the two runs, and concluded
the rig was the culprit. **I did not look at the numbers themselves.** When I
finally did:

```
f2598  q_run1 = [0.687841, 0.585976, -0.277797, -0.326089]
       q_run2 = [0.687841, 0.585976, -0.277797, -0.326089]
```

**Identical. Every component, every frame.** Two runs of the rig on the same
sheet are bit-identical on **2,978 of 2,978 frames** in position, rotation and
lens. The rig is deterministic and there is no defect in it.

**The bug was in my comparison.** I measured the angle between two rotations as
`2·acos(|q₁·q₂|)`. The path file stores quaternions **rounded to six decimals**,
so a stored quaternion is not exactly unit-norm — `|q|²` lands a few times 10⁻⁷
away from 1. `acos` has an **unbounded derivative at 1**, so 5×10⁻⁷ of norm error
becomes ~0.0017 rad, and doubling it gives the ~0.19 deg I reported as a noise
floor. **It was the same number for every beat because it is a property of the
rounding, not of the film** — which should have been the tell, and I read it as
corroboration instead.

Recomputed with a stable formula — normalise both quaternions, then
`2·atan2(‖q₁−q₂‖, ‖q₁+q₂‖)`:

| beat | frames bit-identical | max rotation change |
|---|---|---|
| `1_assembly` | **792 / 792** | 0.00000 deg |
| `2_launch` | **72 / 72** | 0.00000 deg |
| `3_breach` | **192 / 192** | 0.00000 deg |
| `4_transit` | 109 / 135 | **0.00512 deg** |
| **`5_lap`** | 0 / 1524 | **6.02244 deg** |
| `6_ending` | 0 / 263 | **0.00015 deg** |

And position, which was measured with a formula that was never unstable:

| beat | frames whose position moved | max |
|---|---|---|
| all beats except `5_lap` | **0** | **exactly 0** |
| `5_lap` | 1,374 | 0.264 m (lens 1.407 mm) |

**The corrected result is stronger than the one it replaces.** Beats 1, 2 and 3
are *bit-identical* — not "within noise", identical. Beat 4 has 26 frames
differing by at most **0.00512 deg**, which is the shared beats-2-to-5 spline
adjusting its tangents near the boundary, and is 2,000x smaller than the 10.25
deg aim error already sitting in that beat. **Beat 6 differs by 0.00015 deg** —
one unit in the last stored decimal, i.e. the contested territory is untouched to
the precision the file can express.

**Two corrections to numbers published earlier in this document**, both caused by
the same formula: beat 5's max rotation change is **6.02244 deg, not 12.0447**,
and there is no "57x the noise floor" because there is no noise floor.

I flagged another agent's instrument for misusing a derivative, and then shipped a
numerical-stability error of my own into a commit. **The check that caught it was
looking at the raw values instead of the summary statistic** — which is the same
check that would have caught the 85-second run three days ago.

---

## R2-2170 — RETRACTING MY OWN "7.1 % FLAT". I made the same class of error I accused the file of, and the corrected map moves the defect to beat 1

**The film is about 95 % flat by this instrument. The brief's headline percentage
was approximately right and my correction of it was wrong.**

R2-2161 said: the file computes a 0.5 s derivative `D`, its docstring says to use
it, line 513 passes the 1-frame `A`, and feeding `D` instead takes the census
from 96.8 % flat to 7.1 %. **The first three clauses are true. The fourth is my
own error.**

`FLAT_JERK_RATIO = 0.10` is not a free parameter. Lines 444-455 calibrate it
**against `A`**: *"On the delivered beat 1 the pixel instrument reads 5.2 % over
the first six seconds, and the client falls asleep in it. 10 % is the working
floor: it is twice the number attached to a complaint."* `D` is a change measured
over twelve times the interval, and it is **8.72x larger than `A` across this
film** (5.05x in the very window the threshold was calibrated on). **I fed a
quantity to a threshold calibrated for a different quantity** — which is exactly
the crime I charged line 513 with, committed in the opposite direction.

Scale-matched, so that `D` is judged against `0.10 × 8.72 = 0.87`:

| census | % flat | runs | largest run |
|---|---|---|---|
| `A` @ 0.10 — as shipped | 96.8 % | 4 | **85.04 s**, f938-2978 |
| `D` @ 0.10 — **my retracted claim** | 7.1 % | 3 | 3.12 s |
| **`D` @ 0.87 — scale-matched** | **95.1 %** | **5** | **35.67 s, f73-928** |

**What survives, what does not.** The film really is overwhelmingly flat by this
instrument — 96.8 % and 95.1 % agree, and that number is robust to which
derivative you use. **What does not survive is the shape and the location.** The
single unbroken 85 s crossing beats 3-6 is an artefact of the 1-frame derivative;
measured correctly the film's flat time is **five separate runs**:

| run | length | frames | beats |
|---|---|---|---|
| 1 | **35.67 s** | f73-928 | **`1_assembly` + `2_launch` + `3_breach`** |
| 2 | 32.42 s | f946-1723 | `3_breach` + `4_transit` + `5_lap` |
| 3 | 25.25 s | f1737-2342 | `5_lap` |
| 4 | 15.21 s | f2363-2727 | `5_lap` + `6_ending` |
| 5 | 9.46 s | f2752-2978 | `6_ending` |

**The largest flat run in this film is 35.7 seconds and it starts at frame 73 —
three seconds in.** The client said they get sleepy four seconds in. Two other
instruments, derived independently, land in the same place: `camera_tempo`'s
longest flat run is f487-737 and its longest composition lock is f462-793, both
inside beat 1.

**Consequence for this block's fix, stated against my own interest.** Beat 5 is
not the worst stretch; beat 1 is. Beat 5 does carry **57.7 s of flat time across
runs 2 and 3**, so the framing work in R2-2163 lands on genuinely flat territory
and the composition measurement behind it (0.0077 widths/s, which no threshold
choice affects) is untouched by any of this. **But this block did not fix the
film's worst stretch, and the brief's instinct that beat 1 was already handled is
not supported** — R2-1606 addressed roughly the first second of a 35.7 s run.

**Why I got it wrong.** I checked whether the derivative was the one the file
mandated. I did not check whether the threshold was calibrated for it. A ratio
test needs both halves audited, and I audited one.

---

## R2-2171 — THE FOURTH RELOCATION, AND IT IS THE LAST ONE: the flat-run census is saturated, and beat 5 was the right target all along

I was told to fix beat 1's 35.67 s run at f73-928. **I did not, and this section
is why.** Before writing generator code I tested whether the lever would work,
and testing it exposed the census itself.

### The threshold sits at the 99th percentile of the film's own data

The jerk-ratio curve across all 2,978 frames:

| derivative | median | p90 | p99 | **max** | threshold | where the threshold sits |
|---|---|---|---|---|---|---|
| `A` (1 frame) | 0.024 | 0.078 | 0.098 | **0.112** | 0.10 | **99th percentile** |
| `D` (0.5 s), scale-matched | 0.236 | 0.582 | 1.241 | 1.694 | 0.87 | **97th percentile** |

**`FLAT_JERK_RATIO = 0.10` is above 99 % of the values it is applied to, and only
12 % below the maximum the film ever reaches.** A threshold placed there does not
measure flatness — it declares the film flat and then reports where the few
excursions happen to fall. That is why 96.8 % and 95.1 % agree: **both are
saturated**, and the "runs" are the gaps between rare spikes rather than
stretches of genuine sameness.

### It is not reachable by any camera worth shipping

Synthetic aim modulation over f73-928, camera path untouched, measured not
assumed:

| intervention | `A/S` over the run | verdict |
|---|---|---|
| shipped | 6.93 % | flat |
| smooth 6 deg sine, 4 s period | 6.72 % | **worse** |
| 6 deg burst every 3 s | 7.95 % | flat |
| 12 deg burst every 3 s | 9.51 % | flat |
| **20 deg burst every 3 s** | **11.71 %** | **clears 10 %** |

**The only thing that clears the floor is a camera that snaps 20 degrees every
three seconds for thirty-five seconds.** That is not a pacing fix, it is a fault.
And the film-wide census barely moves for it: 95.1 % -> 94.7 % flat.

### Ranked by the metric's continuous value, beat 5 is the flattest beat in the film

Drop the saturated threshold and read the jerk ratio itself. **Both derivatives
agree on the ranking**, which the run census does not:

| beat | median jerk ratio (`D`) | rank |
|---|---|---|
| **`5_lap`** | **0.1946** | **flattest** |
| `1_assembly` | 0.2713 | 2nd |
| `3_breach` | 0.2910 | 3rd |
| `6_ending` | 0.4123 | 4th |
| `4_transit` | 0.4487 | 5th |
| `2_launch` | 0.5309 | liveliest |

**Beat 5 — the beat this block already fixed — is the flattest beat in the film
on the only version of this metric that discriminates.** Beat 1's "largest flat
run" was the fourth artefact in a row, and it was produced the same way as the
first three: by reading a threshold instead of a distribution.

### And the fix moved it, in the only place it touched

| beat | before | after | change |
|---|---|---|---|
| `1_assembly`, `2_launch`, `3_breach`, `4_transit`, `6_ending` | — | — | **+0.0 %** |
| `5_lap` | 0.1946 | 0.2136 | **+9.8 %** |

Five beats bit-identical, one improved — the same confinement R2-2169 measured
in the rotation channel, now visible in the pacing channel.

### The answer to the question I was asked

*"If the answer is that it moves to beat 5 and beat 5 is now the worst, say so —
that would mean the film is uniformly slow rather than locally slow."*

**It is that answer.** The beats span 0.195 to 0.531 — a **2.7x spread with no
outlier**. There is no 35-second villain. The film is uniformly slow, beat 5 is
the slowest part of it, and beat 5 remains the flattest even after a 9.8 %
improvement. **The next work on pacing belongs in beat 5, not beat 1**, and it
should be judged on the composition channel and a viewing rather than on a run
census that cannot fail.

### What beat 1 would actually need, and why it is not mine to do

Beat 1's tour is speed-equalised by construction (R2-062's `_allocate`), and the
span is already **100.3 % of its own minimum flyable time with 0.059 s of slack
across eleven moves**. There is nothing to redistribute. Re-tempoing it means
widening the seat schedule, which moves the assembly and requires rebuilding
`world/beat1_anim.blend` — and **`world/` is explicitly outside this block's
scope**. The two levers that are in scope, `BEAT1_ESTABLISH_HOLD_S` and
`BEAT1_ORBIT_TEMPO_AMP`, act on the lead-in and the payoff orbit, not on the
25 seconds of tour in the middle of the run I was pointed at.

**`tools/build_beatsheet.py` and `docs/beat_sheet.json` were never touched by
this block.** No fork, no unpromoted edit, no lease taken from the agent
currently promoting the sheet.

---

## R2-2173 — EVERY in-scope beat-1 lever, measured to exhaustion. There is no beat-1 fix that does not go through `world/`

R2-2171 asserted that beat 1's levers were closed. **An assertion is not a
measurement, so here is the measurement.** All four levers, tested against the
promoted sheet.

### 1. The orbit tempo is already at its ceiling

`BEAT1_ORBIT_TEMPO_AMP` is env-overridable precisely so it can be swept. Swept:

| amplitude | verdict | worst peak speed (limit 4.00 m/s) |
|---|---|---|
| **0.040 — shipped** | **`BEATSHEET_OK`** | 4.31 (tolerated: inside the instrument's own resolution) |
| 0.055 | `BEATSHEET_VIOLATION` | 4.59 |
| 0.070 | `BEATSHEET_VIOLATION` | 4.86 |
| 0.090 | `BEATSHEET_VIOLATION` | 5.22 |
| 0.120 | `BEATSHEET_VIOLATION` | 5.74 |

The comment claiming 0.040 is "the largest that `beat1_flight_check` still
passes" was written two passes ago and **it is still true**. The next step up
fails. This lever is spent.

### 2. The tour has 0.052 s of slack across twelve presentations

Not from a comment — from the run itself:

```
>> beat 1 SPAN SOLVED: 17.345 s for 12 presentations, bound by CORNER_GROUP
   (ratio 0.997; 1.000 = every move sits exactly on its own limit)
```

**17.345 s at 99.7 % of the point where every move is exactly on its limit.**
Slack across the whole tour is ~0.05 s. There is no time to redistribute, so
there is no rhythm to build out of redistribution. This is R2-062's minimax
doing exactly what it was built to do.

### 3. The establishing hold moves less than a second of a 33-second beat

| hold | verdict |
|---|---|
| 0.300 s | `BEATSHEET_OK` |
| **0.625 s — shipped** | `BEATSHEET_OK` |
| 0.900 s | `BEATSHEET_OK` |
| 1.400 s | `BEATSHEET_VIOLATION` |

There is room here — and **it is the wrong direction**. Lengthening the hold
makes the opening *more* static, which is the complaint. Shortening it removes a
beat rather than adding a rhythm. Either way it touches under a second of the
35.67 s stretch I was pointed at.

### 4. Aim modulation needs a 20-degree snap every three seconds

Measured in R2-2171 and not repeated here: 6 deg bursts reach 7.95 %, 12 deg
reach 9.51 %, and only 20 deg bursts clear the 10 % floor. That is a fault, not a
camera.

### The conclusion, stated as a scope boundary rather than an opinion

**Beat 1's tempo lives in the seat schedule.** The tour's span is solved from when
each cluster stops being where its station says it is, which comes from
`world/beat1_anim_anim.json` and the assembly it was built from. Widening it
moves the assembly and requires rebuilding `world/beat1_anim.blend`.
**`world/` is explicitly outside this block's scope, and the runtime is
load-bearing so the span cannot simply be lengthened either.**

So the honest position is: **beat 1 cannot be re-tempoed by me, and the reason is
structural rather than a lack of effort.** It needs either a world rebuild or a
decision to spend runtime — both of which are the coordinator's call, not mine.
`tools/build_beatsheet.py` and `docs/beat_sheet.json` remain untouched by this
block.

---

## R2-2174 — The sheet is correct on exactly one machine, and now there is a mechanism that says so

**The hazard is real and it is verified, not accepted on description:**

```
tools/author_beats2_5.py    frame_u  worktree = 47   HEAD = 0
```

`docs/beat_sheet.json` is 100 % derived output. Beat 5's framing feature exists
**only in an uncommitted working-tree file**, because the git guard refused the
commit (the path is leased by `inflight-2026-08-07`) and I did not steal the
lease. So a fresh clone, a git worktree, or any `git checkout tools/` regenerates
a different beat 5 — **and every gate still passes, because the gates cannot tell
two legal cameras apart.** The old camera passed them too.

**`docs/SESSION-HOLD.md` line 23 already says a warning is not a mechanism**, and
this had only a warning. So `tools/sheet_reproduces.py` is new in this block. It
regenerates the sheet from the working tree, diffs it against the shipped file,
and separates the two failures that need different answers:

| verdict | meaning |
|---|---|
| `SHEET_DIVERGED` | the sheet does **not** come back out of this tree — hand-edited, or an input moved under it |
| `SHEET_UNCOMMITTED_GENERATOR` | it reproduces **here and only here** — correct on one machine, silently different for everyone else |
| `SHEET_REPRODUCES` | anyone who checks this commit out gets this camera |

Run against the promoted sheet, it says both halves of the truth:

```
sha256  d8825d84d88ae6f92ceb6dab7da80ee4476bfa1e3caf0b6b0de27dea3ab33364
REPRODUCTION FROM THE WORKING TREE: IDENTICAL
     DIRTY  tools/build_beatsheet.py
     DIRTY  tools/author_beats2_5.py
     DIRTY  docs/circuit_spec.json
>> STAGE RESULT: SHEET_UNCOMMITTED_GENERATOR
```

**The promotion is sound** — the sheet is exactly what this tree produces. It is
also unreproducible by anybody else until three files are committed.

### The remedy I was given would have committed another agent's work

I was told `tools/build_beatsheet.py` is dirty with **"+26 lines — YOUR file"**
and to commit the generator and the sheet together. **`tools/build_beatsheet.py`
is not my file and I never edited it.** It carries zero occurrences of `frame_u`.
Its diff is R2-1701 folding R2-85x:

```
+CLOSING_LENS_HOLD_START_MM = 55.0
+CLOSING_LENS_HOLD_END_MM = 130.0
+# ... the car grows 45.8 px -> 78.5 px over the last 3 s ...
```

That is **beat 6's closing lens** — contested territory this block was told to
coordinate on and not overwrite, and somebody else's in-flight work. Committing
it under my name is precisely what the guard exists to prevent.

**The divergence is also wider than described.** It is not one file, it is three,
and they belong to at least two other agents — `docs/circuit_spec.json` is dirty
as well and is an input to every beat. **No single agent can close this hazard
without committing work that is not theirs.** That makes it a coordination
decision, and the mechanism above is the part of it I can deliver alone: from
here on the condition is detected and named rather than discovered days later.

**I did not regenerate the sheet.** R2-2173 established there is no beat-1 change
to make, so there was nothing to regenerate for, and the safest action on a sheet
whose provenance is already fragile was to leave it byte-identical at
`d8825d84…`.

---

## R2-2175 — The instrument behind the surviving claim, validated against an independent implementation

Everything this block still asserts rests on one number: **the car moves 0.0077
frame widths per second in beat 5.** That comes from `tools/camera_tempo.py`,
which projects the car into the frame with hand-rolled quaternion maths — written
by me, checked by nobody, and used to overturn two other instruments. **After two
retractions in one session, that is not a thing to leave unvalidated.**

`anim/build_camera_rig.py` computes the same projection independently: inside
Blender, using `Quaternion.inverted() @ d` and the scene's own render aspect,
against `0.5 * sensor_w / lens`. Two implementations, no shared code, no shared
process.

**First attempt: two of five matched.** The failures were not in the maths — they
were **different subjects**. The rig aims at the car's reference point *plus a
per-beat `z_off`* declared in the sheet (0.55 / 0.65 / 0.80 / 0.80), and beat 6
hands over to a fixed point. I was projecting the raw car origin. Aligning the
subject definitions:

| beat | rig | `camera_tempo` | delta |
|---|---|---|---|
| `2_launch` | 0.588 | **0.588** | +0.000 |
| `4_transit` | 0.321 | **0.321** | −0.000 |
| **`5_lap`** | **0.754** | **0.754** | **−0.000** |
| `3_breach` | 0.223 | 0.251 | +0.028 |

**Three of four agree to three decimal places, including beat 5.** The projection
that produced the composition finding is the same projection the aim gate uses to
pass or fail the film.

**Beat 3's 0.028 is unexplained and I am not going to invent a reason for it.**
It is the beat whose world time collapses to 15.4 % over six frames — the
steepest ramp in the film, where the rig and I index the time map at slightly
different places — but I have not proven that and it is stated as a loose end
rather than a footnote. It does not touch beat 5.

**What this validates and what it does not.** It validates the geometry: the car
lands where the instrument says it lands. **It does not validate against pixels** —
no frame of the current camera covering beat 5 has been rendered yet.
`watch/seq1` and `seq2` cannot substitute; they are the superseded pre-R2-831
camera, which is exactly the trap `watch/INDEX.md` was written to close. The
whole-film proxy now rendering will supply the first real pixel check, and until
it does, **"the subject is pinned to the centre of frame" is a geometric claim,
not a photographic one.**

---

## R2-2172 — A threshold and the quantity it judges are ONE instrument

Generalised, because this is the eighth broken-instrument finding on this project
and the first where the break was in the **calibration** rather than the
measurement:

> **A threshold and the quantity it judges are a single instrument. Changing
> either one alone silently rescales the verdict, and neither half announces it.**

The three failures in this document are all one shape:

1. **The file changed the quantity and kept the threshold.** `campath_pacing`
   computes `D` over 0.5 s, documents that `A` over 1 frame is unusable, and
   passes `A` to a threshold calibrated for `A`. Self-consistent by accident.
2. **I changed the quantity and kept the threshold.** I passed `D` to that same
   threshold and reported 7.1 % flat. `D` runs 8.72x larger, so I had rescaled
   the verdict by 8.72x and called it a correction.
3. **The threshold was never calibrated against a distribution at all.** It was
   set at "twice the number attached to a complaint" — a defensible anchor — and
   nobody then checked where that lands in the data. It lands at the 99th
   percentile, which makes the census unfalsifiable.

**The check that would have caught all three is the same one: print the
distribution of the quantity next to the threshold before believing any verdict
built on it.** A threshold at the 99th percentile and a threshold at the median
are different instruments wearing the same number.

Two things stood between this block and a shipped sheet, both of them other
people's work, and neither was forced.

1. **A film build was live.** `render/film23.blend` began building at 05:38 via
   `tools/build_film_scene.py`, which runs the camera rig against
   `docs/beat_sheet.json`. Writing the sheet during that build would have put a
   half-applied camera into a 10 GB artefact. **`docs/beat_sheet.json` is
   byte-identical to its state at the start of this session** — verified by
   md5 (`17fd6e3d64d3e1ace3fca27b379cad1a`), not by intention.
2. **`tools/author_beats2_5.py` is leased by `inflight-2026-08-07`**, 7.7 h old,
   and the git guard refused the commit. It was refused correctly and **the lease
   was not stolen.** That file already carried another agent's uncommitted work
   when this block started; the framing change is additive on top of it, and the
   0-diff reproduction was run WITH their changes in place, so their work is
   intact and reflected in the shipped sheet.

The generator change therefore sits in the working tree, committed nowhere,
while `tools/camera_tempo.py`, `watch/INDEX.md` and this note are in `b3f811a`.
**That is the desync this project has been bitten by before and it is named here
rather than left to be discovered.** It closes with one lease release and one
regeneration; a follow-up agent is holding the sequence and will not overwrite
the sheet if anything other than the `beat5` block has moved underneath it.

---

## R2-2165 — `watch/` now says which of it is true

`watch/INDEX.md` is new. Two artefacts in that folder have already been judged as
current when they were not. **`PART2_opening_53s.mp4` is verified stale by date,
not by inheritance**: it was cut 08-07 03:10 and the beat-1 re-frame that
replaced its camera landed 08-07 04:11. `PART2_closing_17s.mp4` (08-07 03:11)
additionally predates the R2-943 lap-down and shows the smudge ending.

The index labels every file as CURRENT / SUPERSEDED / A-B PAIR with the date and
the reason, and states the rule: an artefact whose provenance lives only in a
chat transcript will be mistaken for current the next time somebody opens the
folder.
