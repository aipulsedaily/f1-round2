# STAGING R2-2161 .. R2-2220

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
the bearing now changes more. **Every gate that measures the camera's path sees
the same path.**

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
