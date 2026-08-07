# STAGING R2-1601 .. R2-1660 — the camera's derivative

Client note, about the whole film and not one beat:

> *"the camera angle overall is just too slow, not fast high attention paced,
> i get sleepy 4 seconds in."*

R2-1144 diagnosed this as constant velocity plus a decaying novelty curve, and
that diagnosis is **confirmed and extended**. It is also **narrower than the
problem**: the client's word was "overall", and "overall" turns out to be a
different stretch of film from the one that was sampled.

---

## R2-1601 — THE FILM HAS ONE FLAT STRETCH OF 82.5 SECONDS, AND IT IS NOT THE OPENING

`tools/campath_pacing.py` (new) measures all 2,978 frames from the live camera
path — image motion `S` in frame widths per frame, its derivative, and the
fraction of the frame that is new since one second ago. Measured on the shipped
camera:

| beat | frames | S | A/S (1 frame) | D/S (0.5 s) | N |
|---|---|---|---|---|---|
| 1_assembly | 1-792 | 0.02036 | 6.6 % | 37.9 % | 0.396 |
| 2_launch | 793-864 | 0.04886 | 6.5 % | 42.7 % | 0.411 |
| 3_breach | 865-1056 | 0.01623 | 6.7 % | 65.0 % | 0.342 |
| 4_transit | 1057-1190 | 0.04767 | **2.4 %** | 29.5 % | 0.570 |
| 5_lap | 1191-2714 | 0.12201 | **3.3 %** | 30.5 % | 0.591 |
| 6_ending | 2715-2978 | 0.00783 | 5.6 % | 59.2 % | 0.185 |

The flat-stretch census — sliding jerk ratio under 10 % of local motion for 2 s
or more — returns **96.8 % of the film**, in four runs:

```
   frames            t          dur   beat          A/S       S       N
   938-2978    39.0-124.0 s    85.0s  3->6         3.4%   0.09643  0.524
   373-830     15.5- 34.5 s    19.1s  1_assembly   5.2%   0.01192  0.252
   73-363       3.0- 15.1 s    12.1s  1_assembly   8.2%   0.03442  0.637
   840-931     35.0- 38.8 s     3.8s  2_launch     5.8%   0.03011  0.465
```

**One unbroken run of 85.0 s, frames 938-2978, from t = 39 s to the last frame.**
It crosses the end of beat 3, the whole of beat 4, the whole of beat 5 and the
whole of beat 6 without the camera once changing what it is doing by more than
3.4 % of what it is already doing. That is 68 % of the running time in a single
stretch, and it is **seven times longer than the 12.1 s opening the client
named**. The opening is real and it is the smaller half.

The client said "4 seconds in" because that is when they stopped watching. The
measurement says they would have had no reason to start again.

### What the instrument is, and what makes it admissible

There is **no proxy of this film**. `watch/` holds beat 1 (792 frames) and the
ending (264); beats 2-5 — 1,922 frames, 80.1 s, **64.5 % of the running time** —
have never been rendered as a continuous sequence at all. So the whole-film
curve is computed from the camera path, and it is calibrated against the
pictures that do exist: Spearman **0.834** against `tools/pacing_curve.py`'s
pixel curve over beat 1's 791 frames, gated in `--selftest`.

Two corrections were forced on the instrument while building it, both recorded
in the file:

* **Depth must be ray-cast, not a single number per frame.** A single depth (the
  beat's aim subject) scored 0.795 Spearman / 0.490 Pearson; ray-casting each of
  the 45 sensor samples against the cluster boxes, the car, the ground and the
  room shell scored 0.831 / 0.668. Parallax is the signal, and one depth throws
  it away.
* **The one-frame derivative is nearly blind to the thing it is measuring.**
  R2-1144's `|acceleration| 0.898` and this file's `A` are both `|x[f]-x[f-1]|`,
  and nobody perceives a camera at 1/24 s. When R2-1601's fix gave the payoff
  orbit a **1.96x speed swing**, the one-frame derivative moved 1.47 % -> 1.71 %.
  Over half a second it moved **10.68 % -> 14.94 %**. Both are now reported;
  `D/S` is the one to read.

---

## R2-1602 — WHY BEAT 1 IS A METRONOME: `_allocate` EQUALISES SPEED BY CONSTRUCTION

Not a guess and not an observation about the numbers — an algebraic identity in
`tools/build_beatsheet.py`. For any move whose binding constraint is **transit**,
`move_seconds` is proportional to the chord; `_allocate` then hands it `dt`
proportional to that cost, so

```
speed = chord / dt = chord / (k * chord * EASE / limit) = limit / (k * EASE)
```

and **the chord cancels**. Every transit-bound move flies at exactly the same
speed for any tour, any stations and any span. Measured on the shipped sheet,
the six transit-bound tour hops:

```
MB->CI 2.61   halo->BB 2.66   BB->FD 2.59   EC->SP 2.61   SW->NOSE 2.69   FW->RW 2.62  m/s
```

Six moves from 0.48 m to 8.41 m, six different subjects, **one speed to within
4 %**. That is the "steady drift" the client reports, and it is what a
speed-equalising allocator is *for*. R2-062 introduced it to kill a 7.82 m/s
dash and it did. The cost, unnoticed for the whole of round 2, is that the
camera has no derivative anywhere.

**Same shape as R2-1144's own observation**: the quantity being optimised was one
derivative away from the quantity being perceived. R2-062 optimised the
magnitude of motion. Nobody was minimaxing its variation — and minimax
*guarantees* there is none.

### And the tour cannot be re-tempoed in place

`ratio` is **0.9966**: the tour already sits at 100.3 % of its own minimum
flyable time, with **0.059 s of slack across eleven moves**. Any move made
slower must make another faster, and no move can be made faster without going
through the pan or speed limit R2-062 exists to hold. Re-tempoing the tour
itself requires widening the seat schedule, which moves the assembly and so
requires rebuilding `world/beat1_anim.blend`. **Not done here, deliberately**, and
named below.

---

## R2-1603 — THE FIX: A HELD OPENING AND A BREATHING ORBIT

Both in the generator, `tools/build_beatsheet.py`. `docs/beat_sheet.json` was
regenerated by running it, never hand-edited.

**The establishing frame was never seen.** R2-464 solved a station that holds the
whole exploded field in the darkened showroom — the brief's own first image —
and gave it **zero frames of screen time**: the camera is at that station on
frame 1 and already moving on frame 2. A composition that is leaving before it
has arrived is a start position, not an establishing shot.

`BEAT1_ESTABLISH_HOLD_S = 0.625` holds it for 15 frames and then launches out of
it into the same MB station at the same time. **Free**: the lead-in is allotted
2.0 s and its 3.18 m chord needs 1.21 s at beat 1's own peak-speed limit, so
0.79 s of slack was being spent on being slower. On the built per-frame path:

```
              f1     f13    f22    f31    f40
   BEFORE   0.059  1.217  1.776  2.140  2.432   m/s   a 2.3 s ramp
   AFTER    0.000  0.000  1.715  2.841  3.109   m/s   15 frames still, then a launch
```

**The payoff orbit was 12.07 s of one unvarying gesture** — 36 % of beat 1, on a
single monotone easing curve. `BEAT1_ORBIT_TEMPO_AMP = 0.040` adds a mean-zero
modulation to that curve's parameter `e`, which re-times the whole gesture
coherently because azimuth, radius, height, aim and lens are all functions of
`e`. The camera surges and settles along **exactly the same arc, through exactly
the same pictures**:

```
   BEFORE   2.64  2.86  2.34  2.36  2.47  2.40  2.43  2.33  2.16  1.98  1.76   m/s
   AFTER    2.81  2.92  2.25  1.90  1.83  2.28  3.14  2.83  2.28  1.89  1.60   m/s
```

Three things are preserved **by construction** rather than by tuning, because
`sin(pi*u)^2` and its derivative both vanish at both ends, and all three are
asserted at 400 sample points before any key is emitted:

* `e(0)=0, e(1)=1` — the corner-group station and **the seam** are pinned
* `e'(0)=1.00, e'(1)=0.57` — the velocity match into beat 2 (R2-838) survives
* `e` stays **monotone** — a reversal of the azimuth rate *is* a cut (R2-839)

The amplitude was found by building and reading the flight table, not chosen:
0.055 **failed** the gate at 4.11-4.59 m/s against the 4.00 limit, and the build
said so.

### Gates

```
>> STAGE RESULT: BEATSHEET_OK
>> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED
   1_assembly PASS  worst 7.74 deg @f166 (bound 30.0)  frame-offset 0.480
   2_launch   PASS  worst 16.887 deg @f817 (bound 20.0)      <- unchanged
   3_breach / 4_transit / 5_lap / 6_ending  PASS, all unchanged
   worst position jump 4.247 m @f1209 (limit 12.0)      <- unchanged
   worst rotation step 12.957 deg @f2634 (limit 45.0)   <- unchanged
```

* **Runtime unchanged**: 2,978 frames, 124.0833 s.
* **Zero cuts**: no key removed, no discontinuity introduced; the hold is two
  identical keys, which is a hold, not a cut.
* **Sheet diff**: `beat1` only. `beat2`, `beat3`, `beat4`, `beat5`, `beat6`,
  `beat1_2_seam`, `aim`, `time_map`, `speed_ramps` all **byte-identical**.
* Beat 1 keys 20 -> 21; rig keys 533 -> 534, the difference being exactly the
  hold.
* **Beat 6 untouched** — it is owned by the lap-down/ground workstream.

---

## R2-1604 — TWO ARTEFACT DEFECTS FOUND ON THE WAY, BOTH ABOUT TRUST

**`watch/PART2_opening_53s.mp4` is the PRE-R2-831 camera.** Its first 792 frames
are 0.87 levels from `BEFORE_beat1_33s.mp4` and **50.93 levels** from
`AFTER_beat1_33s.mp4`. The file in the delivery folder called "the opening" is
one shipped fix out of date. If the client formed the "sleepy 4 seconds in"
impression from the clip with "opening" in its name, they were watching the
camera R2-831 already replaced.

**R2-1144's headline numbers are not reproducible from anything on disk, and the
instrument that produced them was never saved.** No novelty or acceleration tool
exists anywhere in the tree or in git history. Re-measuring
`watch/AFTER_beat1_33s.mp4` at its native 1280x720:

| R2-1144 | reproduced | verdict |
|---|---|---|
| accel 0.898, "5.4 % of the mean change" | 0.896, **5.2 %** | **confirmed** |
| first 6 s mean change 16.52 | 17.08 | close, outside tolerance |
| first 4 s 29.35 vs rest 26.34 (1.11x) | 16.54 vs 14.31 (1.16x) | **ratio confirmed, scale 1.8x off** |
| novelty 48.50 / 48.48 / 37.36 / 35.66 / 36.09 | 52.35 / 44.45 / 42.07 / 36.93 / 39.60 | shape differs |

**The load-bearing claim survives**: acceleration is ~5 % of the movement, the
camera is constant-velocity, and the conclusion R2-1601 acts on is the right one.
But the 29.35/26.34 pair cannot be reconciled with the 16.52 at any single
resolution — they are internally inconsistent — and the novelty decay-then-flat
shape does not reproduce. `tools/pacing_curve.py` is now committed with those
five numbers as a selftest, so the next person to measure this measures against
something that exists.

---

## R2-1605 — THE SAME DEFECT LIVES IN THE OTHER GENERATOR, AND IT IS WORSE THERE

Beat 5 was scoped but **not changed**. What the scope found is that R2-1602 is
not a beat-1 defect; it is the project's house style, implemented twice.

**First, a correction to R2-1601's own wording.** Beat 5's image motion is *not*
constant. Its 3-second mean runs from **0.0092** at t=88 s (182 m out on an
80 mm lens) to **0.6956** at t=68 s (the hairpin exit, 16 m out on 34 mm) — a
**75x swing**, and the highest coefficient of variation in the film at 162.9 %.
Plenty happens. What is flat is that **every transition between those levels
takes longer than three seconds**, so the derivative never registers: the sliding
jerk ratio inside beat 5 runs min 0.5 %, median 1.9 %, max 9.8 %, and **1,524 of
1,524 frames** sit under the 10 % threshold. Not one frame escapes.

"The camera never changes what it is doing" was the right conclusion from the
wrong sentence. It changes constantly, and never quickly.

**Six rate-equalising mechanisms are stacked** in `tools/author_beats2_5.py`:

* `_tangents()` L306 — **Bessel secant averaging**: the spline's velocity at each
  anchor is a time-weighted mean of its two neighbours' chord velocities, so it
  cannot lie outside the interval they span. A low-pass filter on velocity,
  applied down a 40-anchor chain. Same signature as `_allocate`.
* `_tangents()` L303-308 — **Fritsch-Carlson clamp to `3.0 * min(|d0|,|d1|)`**,
  i.e. to three times the *slower* neighbour. It bites hardest exactly at the
  transitions where an authored acceleration would live.
* `scalar_at()` L377 and `lerp_aim()` L259 — **smoothstep on lens, fstop and
  aim**, which has zero derivative at *both* ends of every interval. The lens
  cannot step, burst or snap anywhere in beats 2-5. Measured median lens rate
  3.02 mm/s.
* `emit_keys()` L508-523 — a **constant-5-degree-bearing allocator**
  (`BEARING_PER_KEY_DEG = 5.0`). Of beat 5's 315 key intervals, **216 (69 %) sit
  on a rail**: 121 at `MIN_KEY_GAP=2` (clipped) and 95 at `MAX_KEY_GAP=8`, where
  the rig becomes a 3 Hz sampler and AUTO_CLAMPED erases anything shorter than a
  third of a second. The 5-degree criterion is only in control 31 % of the time.
* **`speed_key` is OFF for beat 5** — L899, `speed_key=(name == "2_launch")`. The
  emitter is therefore *structurally blind to speed change*. **Any acceleration
  authored into beat 5's anchors will not survive key emission.** R2-087 declined
  enabling it globally because "beats 3-5 do not do that"; a re-pacing pass makes
  beat 5 do exactly that, which inverts the argument. Known cost: +16 keys, 321
  frames move up to 0.234 m, accel p99.9 4.20x -> 4.25x.
* **The anchor list itself** is an anti-acceleration document, four times over in
  its own notes — "laid out as four decelerating anchors and not as one",
  "five anchors, because arriving at a hover in one is a 6 g stop", "on a smooth
  speed profile rather than at the corners". The helicopter arc runs 50, 51, 54,
  55, 54 m/s across five consecutive anchors: five seconds of constant speed by
  construction.

**The slack is enormous and almost entirely unspent:**

| constraint | bound | beat 5 actual | headroom |
|---|---|---|---|
| aim `bound_deg` | 22.0 deg | worst **1.298** deg | 17x |
| aim `frame_margin` | 0.92 | worst **0.0548** | 16.8x |
| camera speed | 137.8 m/s | 101.9 | 26 % |
| camera accel | 9.78 g | 6.08 | 38 % |
| camera-to-car | 1.40 m floor | **10.57 m** closest over f1191-2559 | 9.2 m |
| lens rate | **ungated** (R2-113) | 76.3 mm/s | unbounded |

A sensitivity probe (lens channel only, position and quaternion bit-identical)
sized the weakest lever: **lens x (1 +- 0.40) at 1 Hz cuts the 82.5 s flat run to
32.8 s** and the film-wide flat fraction from 96.7 % to 80.9 %. That is not a
proposal — a 1 Hz sinusoid is not choreography — but it proves the lever is real
and that it is *not sufficient alone*.

**Levers, ranked**: (1) anchor time spacing and count — the defect is transition
*duration*, and compressing a 3.0 s transition to 0.8 s is seam-free if the
endpoint anchors hold; (2) enable `speed_key`, which is a **precondition** for
(1) and (3), not an optimisation; (3) standoff via `tp()`/`cp()`, since
`S ∝ 1/depth` at Spearman -0.904 and there is 10.57 m of unused approach;
(4) along-track lead — and note `aim_car()`'s `lead_s` and `along_m` are
**implemented, wired through `lerp_aim()` L250, and zero on all 40 anchors**, so
there is a dormant pure-rotation lever costing no position risk at all;
(5) lens, weak and needing the easing changed as well as the values.

**Pinned**: the f1190/1191 seam (the fastest camera move in the film, ~3.5 m per
frame), the f2714/2715 peel, and f2630-2714 which is jointly owned by R2-063's
36-frame Hermite blend, R2-112's nadir roll window and the beat-6 workstream.
Beats 2-5 share **one** cubic Hermite chain, so beat 5's first anchor is an
interior knot of beat 4's spline.

**The tightest real constraint is not the aim gate.** It is the C1 rotation
smear: beat 5 sits at **22.07 %** against **25.47 %, a value already refused
once** in R2-112's cone/rate table. Three points of margin, and R2-089/R2-112
both spent beat 5's smear to buy beat 6's roll.

### THE GATES THAT WILL NOT CATCH A RE-PACING PASS

Recorded here because a fix shipped against these is a fix nobody has checked:

* **aim `bound_deg 22.0` is documented stale three times** (R2-586, R2-592,
  R2-1012): at 158 mm the half-width is 6.50 deg, so a 22 deg bound bounds
  nothing. `frame_margin 0.92` is the only real containment test.
* **`campath_gate` has no roll term at all** (R2-151).
* **`continuity_gate`'s `rot_limit_deg = 45.0`** per frame is 1,080 deg/s — a
  whip would have to be twelve times worse before it fired (R2-851).
* **`continuity_gate`'s acceleration detector is a robust-z against a rolling
  local median** (R2-086), so **a RHYTHMIC re-pacing becomes its own baseline and
  goes unreported.** This is the single most likely way a beat-5 re-pacing ships
  broken, and it is the direct analogue of what R2-1601 hit: an instrument one
  derivative away from the thing being changed.
* **lens rate is computed and never bounded** (R2-113).
* **`subject_sweep.py` exits 0 with no `STAGE RESULT` on a vacuous run**
  (R2-111 L299) — the gate most needed for any lateral-offset change cannot be
  distinguished from a pass.

## WHAT IS NOT DONE, AND WHO SHOULD DO IT

**1. The 85-second flat stretch (f938-2978) is untouched.** R2-1603 changes ~14 s
of beat 1. It does not go near the thing the measurement says is the bigger
problem by a factor of seven. That stretch lives in `tools/author_beats2_5.py`
(beats 2-5) and in the beat-6 workstream, and it needs its own pass.

Note the slack available there: **beat 5's aim gate sits at 1.30 deg against a
22.0 deg bound**. The camera is pointed almost exactly at the car for 63.5
seconds while being allowed to be 22 degrees off it. That is a very large
authored-gesture budget that is currently unspent.

**2. Re-tempoing beat 1's tour needs the seat schedule to move**, which moves the
assembly, which requires rebuilding `world/beat1_anim.blend` and then the film
scene. Sequenced, not skipped.

**3. Beat 1 has no EVENT for its first 9.9 seconds.** `BEAT1_SEAT_START_FRAC =
0.30` means the first part does not seat until t = 9.9 s. Nothing enters frame,
nothing lands, nothing changes in the world; only the camera moves. The client
falls asleep at 4 s. This is the "new information entering frame" lever and it
is entirely unused in the stretch where the complaint was made — but it is the
same blend rebuild as (2), so it belongs in that pass.

**4. `render/film17_path.json` is now stale** with respect to
`docs/beat_sheet.json`. `docs/LIVE-CAMERA.md` still declares it, correctly, as
what was last built. Whoever builds the next film scene must re-declare.

## Artefacts

```
tools/campath_pacing.py            new — whole-film pacing, --selftest, --flat
tools/pacing_curve.py              new — pixel pacing, R2-1144 selftest
tools/build_beatsheet.py           R2-1601..1603
docs/beat_sheet.json               regenerated (beat1 only)
work/r21601/beat_sheet_CANDIDATE.json
work/r21601/rig_{BEFORE,AFTER}.blend + _path.json + _continuity.json
work/r21601/pacing_{BEFORE,AFTER}.json
watch/BEFORE_opening_18s.mp4       f1-432 of the shipped camera, re-encoded free
watch/AFTER_opening_18s.mp4        f1-432 of the re-paced camera  (render pending)
```
