# STAGING R2-791 .. R2-820 — beat 1's focus and aperture

Staged here, not in `DEFECT-LOG-R2.md`. Entry numbers are provisional.

Scope handed to me: the client's note on the 53 s proxy — *"assembly 1 too much
blur — that's what, f-stop 1?"* Focus and aperture only. **Camera position and
rotation are not touched by anything in this block**, and R2-798 makes that
structural rather than promised.

A second agent owns this beat's PACING and FRAMING at the same time. Everything
below is written to survive their changes; R2-796 is the reason it can.

---

## R2-791 — THE BRIEFED MEASUREMENT WAS TAKEN FROM THE WRONG BLEND

Stated first because three of the numbers I was given do not describe the film,
and one of them would have sent me to fix a camera that no longer exists.

The table I was briefed with — *"f1 lens 35.000, focus 4.859, f/2.80, subject at
5.37 m"* and seven more rows — is **`render/film14.blend`**, not
`render/film16_breach.blend`. It reproduces byte for byte out of
`work/b1dof/dump.json`, which was written on 2026-08-04 04:07 by
`tools/beat1_dof_dump.py` **against film14**, and whose own header says so.

The camera moved after that. Comparing that dump against `render/film16_path.json`:

| frame | film14 dump position | film16 position | same? |
|---|---|---|:--:|
| f1 | `[0.760, 0.000, 5.661]` 35 mm | `[-0.841, -8.863, 3.757]` 18 mm | **no** |
| f300 | `[-3.345, 1.466, 3.950]` | `[-0.871, 2.470, 3.664]` | **no** |
| f400 | `[-0.654, 0.295, 2.237]` | `[-3.772, 1.144, 1.884]` | **no** |
| f500 | `[-2.412, 0.561, 2.231]` | `[-3.170, -1.368, 1.452]` | **no** |
| f700 | `[6.969, -0.271, 2.314]` | `[6.968, -0.271, 2.314]` | yes |
| f792 | `[5.165, -5.314, 1.285]` | `[5.165, -5.314, 1.285]` | yes |

That is the R2-451/R2-464 re-aim: the presentation tour was re-stationed and the
protected close-out was not. The f1 camera in the shipping film is the
18 mm **establishing** key at f/4.0 focused 9.0 m — a key that does not exist in
the briefed table at all.

**The brief's headline, "focus is short of the subject on every sampled frame by
up to 3.05 m", is therefore a statement about a superseded camera.** The defect
is real and is worse than that, but for a different reason, and the rest of this
block re-derives it from the shipping sheet rather than repairing the old number.

`work/b1dof/dump.json` should be regarded as stale. It is not deleted here
because other blocks cite it, but anything reading it is reading film14.

## R2-792 — WHAT IS ACTUALLY WRONG: THE FOCUS IS KEYED, AND KEYED ONLY, AT 23 STATIONS

`docs/beat_sheet.json` carries 23 beat-1 camera keys. Each sets
`focus_distance_m` to that station's **standoff** — the distance from the lens to
the cluster it presents — and `anim/build_camera_rig.py:1145` keys it *at that
frame and nowhere else*:

```python
if k.get("focus_distance_m"):
    cam_data.dof.focus_distance = float(k["focus_distance_m"])
    cam_data.dof.keyframe_insert("focus_distance", frame=f)
```

Between two stations Blender interpolates the two standoffs. **The interpolated
number is the distance to nothing**: the camera has moved, the parts have moved,
and a Bezier from 1.88 m to 2.08 m knows about neither. The tour spends roughly
570 of its 621 frames between stations.

The keys themselves are RIGHT. R2-795's solver, which computes the distance to
the beat's declared subject from the camera's own forward axis and never reads
the sheet's focus numbers, **agrees with the shipped value at the stations to a
mean of 0.102 m over 18 of them**. That agreement is the finding: the author's
intent was correct and the interpolation lost it.

## R2-793 — THE APERTURE RULE IS NOT MERELY UNCONTROLLED, IT IS BACKWARDS

`tools/build_beatsheet.py:1040`:

```python
"fstop": 2.2 if g["radius"] < 0.8 else 2.8,
```

A **smaller** cluster gets a **wider** aperture. But a small cluster is presented
from close up, and depth of field collapses with the square of subject distance,
so the rule opens the iris exactly where the depth is already thinnest. Measured
at the shipped keys, at the film's own 2 px / 4K sharpness budget:

| station | lens | f/ | focus | **total depth of field** | cluster depth |
|---|---:|---:|---:|---:|---:|
| SW | 58 mm | 2.20 | 0.750 m | **0.013 m** | 0.345 m |
| NOSE | 58 mm | 2.20 | 1.378 m | **0.045 m** | 0.840 m |
| CI | 58 mm | 2.20 | 1.481 m | **0.052 m** | 0.694 m |
| CORNER_FR | 58 mm | 2.20 | 1.503 m | **0.053 m** | 1.123 m |
| RW | 58 mm | 2.20 | 1.530 m | **0.055 m** | 1.411 m |
| MB | 35 mm | 2.80 | 4.859 m | 2.099 m | 2.364 m |

**Thirteen millimetres of depth of field on an assembly 345 mm deep.** Eight of
the seventeen presentation stations ship with under 60 mm. That is the client's
"f-stop 1": not a shallow look, an unfocusable one. The four widest stations are
fine, which is why f49 (MB) reads acceptably at 4K and f150 and f258 do not.

## R2-794 — `fstop_required` IN THE SHIPPED SHEET IS PARTLY AN ARTEFACT, AND MUST NOT BE THE DESIGN TARGET

`beat_sheet.json`'s `presentation_framing` reports the f-number that would hold
each cluster whole. It reads f/37.95 for CORNER_RL and **f/99.67 for CORNER_RR** —
two stations whose geometry is near-identical (range 1.53 m both, depth 1.386 vs
1.378 m). A 2.6x disagreement between two nearly identical stations is not a
property of the stations.

The cause is the one the pacing agent independently flagged in
`beat1_true_extent.py`: **the projection drops bounding-box corners that fall
behind the camera plane.** `build_beatsheet.py` takes `z_worst = min(zs)` over
all eight corners, and where the camera is close enough that a corner is 0.15 m
off the lens, `n_req = f²|z−s| / (c(s−f)z)` divides by that 0.15 and explodes.
The number is being set by a corner of an axis-aligned box drawn round an
exploded cluster — mostly empty air — that the audience never sees.

So the f/37–f/100 figures are **directionally right and quantitatively unusable**.
They correctly say "these stations cannot be held", which is the framing defect
the other agent is fixing; they must not be used to choose an aperture. R2-797
targets the on-screen, in-front-of-the-lens subject instead.

## R2-795 — THE FIX FOR FOCUS: TRACK THE BEAT'S OWN DECLARED SUBJECT, PER FRAME

`tools/r2791_beat1_focus.py`. Focus is no longer a number in the sheet; it is

    focus_distance(f) = | camera(f) − subject(f) |

where `subject(f)` is **the model `build_camera_rig.Subject.nearest_field()`
already uses for the AIM GATE** — the nearest of the 15 cluster volumes to the
camera's forward axis, each at the position the seat schedule puts it at that
frame, measured to the edge of its bounding sphere.

That model is not my invention and it is already gate-validated on this beat. Its
own docstring records why the obvious alternative was rejected: nominating one
cluster per key and calling the rest a miss "failed beat 1 at 114 deg with the
subject off-screen on 197 of 792 frames", against median 0.00 deg and worst
9.84 deg for the field model, because "beat 1 is a WEAVE through a field of
parts; between two presentations the camera is looking at the parts in between,
which is the film."

**This is the same reason the pacing agent gives for why beat 1 has no whole car
between f37 and f656.** The subject is a cluster, and which cluster it is has to
be asked of the camera, not of a schedule.

## R2-796 — WHY THIS SURVIVES THE RE-PACING, WHICH IS THE POINT

The solved curve **contains no frame numbers**. It is a function of the camera's
own evaluated transform and the parts' own seat schedule, both read at build
time. Consequences, stated as commitments the other agent can rely on:

* **Re-time the tour** — the camera reaches each station at a different frame;
  the solver samples the new transform and the focus follows.
* **Pull the corner stations back** (the fix in flight) — the standoff changes,
  the solved distance changes with it, and the aperture bound in R2-797
  *automatically relaxes*, because a station that is further away needs less.
* **Move the seat schedule** so the car completes at t ≈ 20.8 s instead of 29.0 s —
  the field model reads `world/beat1_anim_anim.json`, so the parts are where the
  schedule puts them.

The one thing required is that `anim/build_camera_rig.py` is re-run, which a
re-pacing has to do anyway. **A curve baked to frame numbers would have to be
re-authored by hand after every one of the above; this one is re-derived.**

A per-frame `focus_object` empty and a raycasting driver were both considered and
rejected: `focus_object` is a single pointer on camera data with no per-beat
form, so setting it would silently re-govern beats 2–6, and a driver that
raycasts returns 0.0 — i.e. the entire beat at minimum focus — if script
auto-execution is off on the render box. Neither failure mode is acceptable in a
distributed render.

## R2-797 — THE APERTURE I CHOSE, AND THE TWO MEASUREMENTS THAT BOUND IT

**I picked f/8 as the working stop for the presentation tour, easing to the
shipped f/2.6–3.2 across the close-out — and the iris is deliberately NOT flat.**

It is bounded from both sides, and both bounds are measured:

**From below, by the subject.** The aperture must hold `DEPTH_FRAC_TARGET = 0.80`
of the subject's own depth inside the 2 px budget. Across the tour this demands
more than f/8 nearly everywhere, so this bound is usually slack against the
ceiling — which is the honest way of saying the close stations are unfixable by
aperture and need the standoff the other agent is changing.

**From above, by the background.** Stopping down to hold the subject also drags
the room forward, and a showroom whose far wall is as sharp as the part *is* the
CAD render the brief forbids. So N is capped at the largest value that still
leaves the background at least `SEPARATION_PX = 6.0` px of blur at 4K.

Six pixels is three times what this film calls sharp, and it is not invented: it
is **the background softness the shipped MB station already has** (35 mm, f/2.8,
4.859 m, room at ~15 m → 6.5 px), and MB is not among the frames complained
about. It is adopted as the floor because it is the least separation this film
has been observed to get away with.

This bound is why the iris varies, and the variation is the whole argument:

| station | lens | focus | bg | f/2.8 | f/5.6 | **f/8** | f/16 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SW close | 58 | 0.750 | 12 m | 173.6 px | 86.8 | **60.8** | 30.4 |
| CORNER_RL | 58 | 1.531 | 12 m | 75.9 px | 38.0 | **26.6** | 13.3 |
| SP | 35 | 2.489 | 12 m | 15.1 px | 7.5 | **5.3** | 2.6 |
| MB | 35 | 4.859 | 15 m | 6.5 px | 3.3 | **2.3** | 1.1 |
| close-out CAR | 40 | 8.300 | 30 m | 5.3 px | 2.7 | **1.9** | 0.9 |

At the 58 mm stations even f/16 leaves the wall 13–30 px soft, so the bound never
bites and the ceiling does. **At MB the same f/8 puts the wall at 2.3 px — inside
the film's own definition of sharp** — and the bound drags the iris back open to
about f/3. A single house stop cannot be right at both ends of that, which is why
this beat does not get one.

**Why not f/16**, beyond the brief saying so: it would buy the close stations
0.09–0.41 m of depth against f/8's 0.05–0.20 m — real, but they need 0.35–1.4 m,
so it does not reach either — while pulling the wides to 1–3 px and flattening
them. It trades a defect that aperture cannot fix for one it would create.

**Exposure is not a consideration.** Cycles' `aperture_fstop` governs lens blur
only; it is not a light-transmission model, so a 1.5-stop iris ramp across the
beat costs nothing in brightness and cannot betray the single take. R2-799's A/B
tests this implicitly — the two arms share a grade and a light rig.

## R2-798 — THE A/B IS STRUCTURALLY INCAPABLE OF MOVING THE CAMERA

`tools/r2791_ab_build.py` builds `render/r2791_dof_ab.blend` (292 MB) from
`world/beat1_anim.blend` — the vehicle `tools/beat1_ab_build.py` established for
this class of question, and for its reasons: same room, same 616 exploded parts,
same part animation, same 23 practicals, at 292 MB against the film's 7.97 GB on
an 11 GB machine.

Both cameras are keyed **from the same per-frame transform, out of the same
`render/film16_path.json`, by the same loop**. `assert_transforms_identical()`
then re-samples both through Blender's own evaluation and requires agreement:

```
>> transforms identical? worst position 0.000e+00 m, quaternion 0.000e+00, lens 0.000e+00 mm over 17 frames
>> focus differs on 13 of 17 sampled frames, worst 1.236 m
>> grade holds -3.628 (AgX / None) at every probed frame
```

Zero, not "small". If this file ever moves a camera the build fails rather than
producing a comparison that attributes a framing difference to focus.

The SHIP arm is keyed from `beat_sheet.json`'s own 23 beat-1 keys at their own
frames and interpolated by Blender — which is not an approximation of the film,
it is the same 23 numbers through the same interpolator that
`build_camera_rig.insert()` uses.

Its limit, stated rather than discovered: through the glass this scene carries
`R2_ProceduralSky`, not the film's sky. Beat 1's subject is inside the room and
both arms share the scene, so no verdict rests on it — **but a frame from here is
not a frame of the film and must not be quoted as one.**

## R2-798a — THE FIELD MODEL WAS NOT GOOD ENOUGH, AND THE MEASUREMENT SAID SO

R2-795's first implementation focused on the field model's cluster centre. It is
recorded here because it looked right, passed its own control, and was worth only
a quarter of the available fix.

Against the measured on-screen subject depth from `tools/r2791_depth_grid.py`
(64x36 rays/frame, 400 frames of the tour), over 292 sampled tour frames:

| | median focus error | p90 | max |
|---|---:|---:|---:|
| shipped | 0.455 m | 1.567 m | 3.841 m |
| field-model solve | 0.336 m | 1.137 m | 2.520 m |
| **measured solve** | **0.227 m** | **0.929 m** | **2.174 m** |

At f401 the field-model solve was **worse than what shipped** — 1.468 m against a
subject at 3.329 m, where the shipped curve had 2.110 m. A bounding sphere drawn
round an exploded cluster is mostly air, and the camera is frequently inside or
beside it, so its centre is not the depth of the visible surface.

So the solver now uses the measured depth where it exists and keeps the field
model only as the fallback for frames where no part is on the axis. Keeping the
fallback matters: the pass must produce a curve on any rig it is handed,
including one built before the parts are in the scene.

## R2-798b — AN ESTIMATOR THAT ALTERNATES IS WORSE THAN EITHER ESTIMATOR

The depth grid samples every 2nd frame. Falling back to the geometric model on
the frames in between does not fill the gap — **it alternates between two
estimators that disagree by metres, every frame.** That alone took the largest
per-frame focus step from 0.265 m to **1.834 m**, which is a snap and would have
failed the continuity constraint outright.

The fix is to densify the measurement onto every frame first and only then solve,
so the estimator is constant along the curve and the remaining variation is the
subject's. Worth stating as a general shape: a curve assembled from two
instruments is not the better of the two, it is the difference between them.

## R2-799 — WHAT THE CURVES DO, IN NUMBERS

Over the tour, f1–f621 (the close-out f622–792 is handed back to the sheet
untouched, ramped over 30 frames so the join is C1).

**The metric that matters is not focus error, it is how much of the subject the
audience actually gets sharp.** For every sampled tour frame, the rays that land
on an assembly part inside the central 50 % of frame are scored against the
film's own 2 px / 4K budget with the actual lens, focus and f-stop of that arm:

| fraction of the on-screen subject inside the 2 px budget | shipped | solved |
|---|---:|---:|
| median frame | **0.9 %** | **45.0 %** |
| mean | 21.0 % | 45.5 % |
| **frames with essentially nothing sharp (< 5 %)** | **174 / 292** | **86 / 292** |

**On 174 of 292 sampled tour frames the shipping film has under 5 % of its own
subject in focus.** That is the client's note, quantified. It is halved.

It is not taken to zero, and it cannot be: the residual 86 frames are the close
58 mm stations where the depth of field is 13–55 mm and no photographable
aperture reaches (R2-793, R2-803). Those need the standoff, which is the other
agent's fix.

Supporting figures, same 292 frames:

| | shipped | solved |
|---|---:|---:|
| depth of field, median frame | 0.158 m | 0.586 m (×3.71) |
| focus error vs measured subject depth, median | 0.455 m | **0.227 m** |
| f-stop, median | f/2.39 | f/6.65 (range f/2.58–8.00) |

**Continuity.** The raw track steps whenever the subject the axis is on changes.
It is Hann-smoothed over ±11 frames — symmetric, so it introduces no lag, because
a lagging focus is a focus that trails its subject, which is the defect being
fixed. Measured on the curve as Blender EVALUATES it, not on the keys:

* largest per-frame change **under 0.33 m**, spread across consecutive frames —
  racks, not snaps;
* second difference p99 0.032 m, max 0.036 m — no spikes, so C1 holds in practice
  and not merely C0.

The smoothing width is a measured trade-off and R2-801's module records the
sweep: rack 9 gives 54.8 % median sharpness at 0.440 m/frame, rack 21 gives
33.1 % at 0.150 m/frame. All are C1, so the continuity constraint does not choose
between them; 11 was chosen because the note being answered is about blur.

## R2-800 — THE CONTROL, AND IT IS TWO-SIDED ON PURPOSE

`tools/r2791_beat1_focus.py --selftest`. The project's own warning is that an
instrument validated on a sample is not validated over a range, and that a
sharpness metric measuring edge energy reads *detail*, not *focus*. This metric
is geometric — a circle of confusion computed from measured depth — so it cannot
be fooled by content, but it can be fooled by a wrong subject model, and that is
what the control is for.

A one-sided *"the solver disagrees with what shipped"* would be passed by any
curve at all, including a wrong one; it proves only that the solver is not the
identity. So both directions are required:

* **at a station** the shipped number is the standoff, which *is* the distance to
  the presented cluster, so the solver must **agree** — it does, mean 0.102 m
  over 18 stations. Were this to fail, the subject model is wrong and everything
  downstream of it is wrong.
* **between stations** the shipped curve is a Bezier between two standoffs and the
  solver is tracking the subject, so they must **diverge** — and the divergence
  is the defect.

Only both together support the claim actually being made, which is not "the
shipped curve is wrong" but "the author's intent was right and the interpolation
lost it".

Also checked: `quat_fwd` unit and correct on identity; the film's own DOF numbers
reproduced at two stations (SW 0.013 m, MB 2.099 m); `n_for` inverts `coc_px`;
`hann_smooth` preserves a constant exactly and is symmetric about a step
(0.450/0.550) so it cannot introduce lag.

## R2-801 — INSTRUMENTS ADDED

| file | what it is |
|---|---|
| `tools/r2791_beat1_focus.py` | the solver; importable by the rig builder, standalone for analysis, `--selftest` |
| `tools/r2791_focus_dump.py` | per-frame DOF **and the raw f-curves** off a shipping blend — the per-frame sample cannot tell a KEY from an INTERPOLATION and that difference is the whole question |
| `tools/r2791_depth_grid.py` | 64×36 raycast depth grid per frame: what the lens actually sees, immune to R2-794's behind-camera artefact because a ray only travels forwards |
| `tools/r2791_ab_build.py` | the two-camera A/B, with the transform-identity assertion |

## R2-802 — RENDER SPEND

Instance 47040457 at $0.4627/hr. 4K/64-sample frames measured at **~59 s each**,
so single frames are ~$0.008 and the proxy-versus-master question does not arise
at this scale. Recorded because the earlier estimate in this block was 390 s per
4K frame — 6.6× too pessimistic — and it drove a plan to render the A/B at 720p
that was not necessary.

## R2-803 — OPEN, AND NOT MINE

* **The close 58 mm stations cannot be held by any aperture** — they need
  f/24–f/100 and the reachable ceiling is f/8. This is the framing defect
  (R2-317: all fifteen framing-fit checks already fail, up to 2.32× frame
  height) and the other agent is fixing it by pulling the stations back. My
  aperture bound relaxes automatically when they do; **no change to this block
  is required after their fix, only a re-run.**
* `work/b1dof/dump.json` is stale (R2-791) and other blocks cite it.
* `beat_sheet.json`'s `fstop_required` is partly artefact (R2-794) and is quoted
  in at least one other document.

## R2-804 — VERIFICATION, ON FRAMES

3840×2160, 64 samples, AgX / look None / exposure −3.628, both arms from
`render/r2791_dof_ab.blend`, in `work/r2791/ab2/`.

**On resolution.** I was told 720p might not be enough to judge sharpness. It is
enough for *this* note and not for the general question, and the distinction is
worth keeping: circle of confusion scales with resolution, so blur as a FRACTION
OF FRAME WIDTH is resolution-independent and the gross defocus the client
objected to reads identically at 720p — which is exactly why they could object to
it from a 720p clip. What 720p cannot adjudicate is whether the subject is
*critically* sharp at the 2 px / 4K budget, because 2 px at 4K is 0.67 px at
720p. Since 4K frames measured at ~59 s each on this card (R2-802), the question
was moot and everything below is 4K.

**f258, the SW station — the frame that most deserves the client's note.**

* SHIP: the steering-wheel face is on the plane and reads. **Nothing else in the
  frame does.** The tyre behind it is a formless dark blob with no tread, no rim
  and no brake gear; the glass wall is an undifferentiated blue wash; the dais is
  featureless white. One object floating in cream.
* FIX: the tyre resolves — tread blocks, rim spokes, brake duct, the red sidewall
  band. The glass wall resolves into mullions and panels. The dais takes surface
  texture and the floor markings appear. The wheel face is marginally softer than
  SHIP's and remains entirely legible.

That single pair is the note answered: the frame goes from one sharp object in a
cream field to a car part standing in a showroom.

**f49, the MB station — the control that the fix must NOT flatten.** This is the
widest, best-behaved station, already acceptable in the shipping film, and the
one where over-stopping would show as a CAD render. FIX resolves the two
background wheels (spokes, brake components, sidewall bands) and the far wall's
panel grid, while **the "MERIDIAN 3600 mm WHEELBASE" floor lettering and the far
background stay soft.** Depth still falls off. This is the R2-797 background bound
doing what it was put there to do — at MB it holds the iris near f/3 rather than
letting it go to f/8.

**Motion blur is a separate and untouched defect.** In both arms of f258 the
steering wheel carries heavy directional streaking, and f150 carries it across
the whole frame. That is shutter and camera speed, it belongs to the pacing
agent, and no part of this block changes it. **A reviewer looking at these frames
should not read the remaining smear as focus.**

**f150, a transit frame — the largest measured focus error in the beat, 3.71 m,
and the one that isolates FOCUS from aperture.** The shipping curve is at 2.041 m
here; the lens is actually pointed at material 5.754 m away. Nothing whatever in
the shipping frame is sharp — not the wheel, not the stanchion, not the floor
line, not the wall.

* FIX: the plane lands on the wheel and suspension at ~5.7 m. The tyre's red
  sidewall band, the rim and the brake structure resolve; the suspension links
  read as metal with defined edges; the rope stanchion gains a hard edge and a
  defined base disc; the floor line and its reflection tighten.
* The near dais surface across the bottom stays soft, correctly — it is close and
  outside the plane.

This is the half of the fix that aperture cannot produce. At f258 the improvement
could be attributed to stopping down; here the shipped frame has no sharp
content anywhere, so a readable wheel can only have come from moving the plane.

**Honest limit on this frame:** f150 remains a soft *image* overall, because it
carries heavy motion blur across the stanchion, the wall markings and the
suspension. Focus is fixed; the smear is not, and is not mine.

All six FIX frames (f49, f150, f258, f371, f464, f592) rendered and held in
`work/r2791/ab2/`.

## R2-806 — THE RE-FRAMING LANDED MID-BLOCK AND IT FLIPS THE SIGN OF THE APERTURE FIX

`docs/beat_sheet.json` was re-authored at 03:48 while this block was in progress:
**23 beat-1 camera keys became 19**, the four corner stations collapsed into one
`CORNER_GROUP` at t = 19.33 s, and the close-out became six `CAR` keys as the seat
schedule moved earlier. This is the framing fix the other agent described.

**It works, on my measurement.** Stations with under 0.20 m of depth of field at
their own shipped aperture:

| | old sheet | new sheet |
|---|---:|---:|
| stations under 0.20 m of DOF | **8 of 17** | **3 of 19** |
| the four corners | 0.053–0.055 m each | one station, **5.472 m** |

The corner stations are no longer unfixable. R2-803's open item is closed by
their work, not mine.

**And it creates the mirror defect, which is mine.** Pulling back moves the
subject toward the background, so at the *same* shipped f/2.8 the room comes
forward. Background circle of confusion at 12 m, new sheet, shipped apertures:

| station | old | **new** |
|---|---:|---:|
| MB | 6.5 px | **2.8 px** |
| CORNER_GROUP (was CORNER_RL) | 75.9 px | **2.3 px** |
| the six CAR keys | — | **2.0–2.2 px** |

**This film calls 2 px sharp.** Eight of nineteen stations now put the showroom
inside that, which is the CAD-render look the brief forbids arriving by the other
door. So under the new framing **the aperture correction changes sign across the
beat**: still stopping down at the three remaining 58 mm close stations, now
opening *up* at the wides to keep the room off the subject's plane.

`N_MIN` was therefore lowered from f/2.8 to f/2.0. The original floor encoded
"nothing in a beat complained about as too blurry should ever open wider than it
shipped", which was true of the framing this work started against and is false of
the one that landed. The background bound now acts in both directions.

**Nothing else in this block needs changing** — that is the property R2-796 was
built for. The solver reads the camera and the parts, not the sheet's numbers.

## R2-806a — PROVENANCE OF EVERY "SHIPPED" NUMBER IN THIS BLOCK, AND ONE GAP

Stated precisely, because it would be easy to read these as having been measured
off the shipping blend and they were not.

**Every "shipped" focus and f-stop figure above is the 23-key RECONSTRUCTION, not
a reading of `render/film16_breach.blend`.** `tools/r2791_depth_grid.py` was run
against `render/r2791_dof_ab.blend` with `--cam ONER_SHIP`, and that camera is
keyed from `docs/beat_sheet.json`'s own beat-1 keys at their own frames and
interpolated by Blender. It is the same 23 numbers through the same interpolator
that `build_camera_rig.insert()` uses, so it is a faithful reconstruction — and
the A/B is internally consistent either way, because the SHIP arm that RENDERED
is the same camera that was MEASURED.

What is not closed: whether that reconstruction differs from the shipping blend's
literal f-curves, which could only differ through Bezier handle behaviour at the
keys. `tools/r2791_focus_dump.py` exists to answer exactly that and **its output
was never obtained.** Both attempts died to farm defects — first an exec-dispatch
race against a still-uploading Blender, then a memory gate (the job needs ~20 GB
to open a 7.97 GB blend and the warm render process left 3.7 GB). Both are now
fixed in `~/vast-render`.

**CORROBORATED ON FRAMES INSTEAD, which is this project's own standard.** The
reconstruction was checked the way the rest of this block was judged — by
rendering the same frame both ways at 4K and looking at it. `work/r2791/before/`
holds f49, f150 and f258 rendered from `render/film16_breach.blend` through
camera `ONER`; `work/r2791/ab/` holds the same three from the reconstructed
`ONER_SHIP`.

At **f150** the two are the same picture as far as focus is concerned: the same
soft red sidewall band on the wheel, the same soft rim, the same soft-edged
stanchion and base disc, the same mush across the floor line and wall, and
nothing critically sharp in either. At **f258** both show the same signature —
wheel face on the plane, tyre a formless blob, glass wall an undifferentiated
wash. The differences between them are the documented scene differences
(`R2_ProceduralSky` through the glass, wall brightness), not depth of field.

So the reconstruction reproduces the film's defocus at the frames the claims are
made from. What remains strictly unproven is *exact f-curve equality*, which
could only differ through Bezier handle behaviour near beat 1's last key — and
that is f718-754, inside the close-out this block hands back untouched and
outside the f1-621 window every headline number comes from.

**The dump is therefore deliberately not re-run.** Waking a hibernated instance
to re-upload a 7.97 GB blend (~$0.40) to characterise handle behaviour in a
region this block does not touch, on a camera the re-framing has already
superseded, buys nothing the frames have not already shown. The tool is written
and the farm now works if anyone wants it closed exactly.

R2-800's second control still reports **SKIP rather than a pass**, because
corroboration on three frames is not the numeric proof that control was written
to make, and labelling it otherwise would be the exact move this block criticises
elsewhere.

## R2-807 — WHAT IS AND IS NOT VERIFIED, GIVEN THE TIMING

Stated plainly so nobody over-reads R2-804.

* The **A/B frames in `work/r2791/ab2/` are against the camera that SHIPPED**
  (`render/film16_path.json`, the film16 tour). They are a valid, controlled test
  of the focus and aperture change on that camera, and R2-798's zero-difference
  transform guarantee holds for them.
* They are **not** a test of the new sheet. No rig has been built from the 19-key
  sheet yet, so no per-frame camera path for it exists.
* The correct next step is mechanical and is the workflow this was designed for:
  build the rig from the new sheet, run `tools/r2791_depth_grid.py` on it, then
  `tools/r2791_apply_focus.py --grid …`. **No re-authoring.**
* The numbers in R2-799 (0.9 % → 45.0 % of the subject sharp; 174 → 86 dead
  frames) are measurements of the OLD framing. Under the new framing the shipped
  arm will start from a better place and the headroom will be smaller. Quoting
  them against the new sheet would overstate this block's contribution.

## R2-805 — FOR THE AGENT RE-PACING THIS BEAT

* Run `tools/r2791_apply_focus.py` **after** your rig build. It reads the camera
  you authored and writes only `dof.focus_distance` and `dof.aperture_fstop`; it
  snapshots location, rotation and lens before the pass and fails the run if any
  of them moved. Verified clean: `position 0.000e+00 m, rotation 0.000e+00, lens
  0.000e+00 mm` over 42 frames.
* Give it `--grid` from `tools/r2791_depth_grid.py` run on your rig. Without a
  grid it falls back to the geometric field model, which R2-798a shows is worth
  only a quarter of the fix.
* **Pulling the corner stations back helps me automatically.** The aperture bound
  relaxes as standoff grows; nothing in this block needs re-authoring after your
  change, only re-running.
* `CLOSEOUT_F = 622` is where I hand back to the sheet. If your re-pacing moves
  the close-out, pass `--closeout` rather than letting it drift.
