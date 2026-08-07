# STAGING — R2-851 to R2-880 · beat 6, the closing wide

Owner: the beat-6 camera. Merge by identity, never by position.
**Nothing here has been rendered yet** except where a frame is named. A candidate
render of R2-853 is in flight; every claim below that is not marked MEASURED ON
FRAMES is measured on the camera path, not on pixels.

The client's note, in full:

> "Also the ending I don't like. We just zoom out so you see all the patches in
>  the land etc."

---

## R2-851 — the closing wide contains a 91.5 deg/s whip pan, and the film's law forbids one

**MEASURED** on `world/camera_rig_path.json`, the shipped rig.

`sheet["aim"]["6_ending"]` hands the subject off from the car to a fixed point —
the breached facade at `[15, 0, 3.1]` — over `car_until_t 4.0 → point_from_t 6.0`.
At the moment of the hand-off those two subjects are **82 deg apart** in bearing
from the camera, so the aim does not ease between them, it *travels* between them:

| | shipped | this candidate |
|---|---:|---:|
| peak pan, beat 6 | **91.5 deg/s** at f2832 | 11.0 deg/s at f2810 |
| mean pan, beat 6 | 10.94 deg/s | 3.77 deg/s |
| worst rotation smear @4K, 180 deg shutter | **84.8 px** at f2832 | 36.5 px at f2976 |

f2814–f2858 is 44 frames — 1.83 s — of ~95 deg of yaw. At the 18.8–19.5 mm lens
the beat is carrying there, that is 84.8 px of uniform smear across the whole 4K
frame. On the 720p encode the client watched it is visible as a mush: the frame
at f2835 has no readable edge anywhere in it.

**The continuity gate does not see this and cannot.** `rot_limit_deg` is **45.0
degrees per frame** — 1,080 deg/s — so a whip would have to be twelve times
worse before the gate noticed. The gate's own report calls beat 6 the *best*
beat in the film: `aim_per_beat["6_ending"].ang` is **0.054 deg**, because the
camera is pointed at its declared subject to a twentieth of a degree the entire
time. It is aimed perfectly at the wrong thing, and both facts are true at once.

> The brief's law is *"Zero cuts. Zero crossfades. **Zero hidden whip-pan
> cheats.**"* This whip is not hiding a cut, so it does not violate the letter.
> It is still the one gesture the law names by name, and it is in the last beat.

**Recommend a rate bound on the beat sheet**, not just the per-frame step: pan
rate has no gate anywhere in this film, exactly as R2-113 found lens rate had
none (`campath_gate` computes `dlens` and never uses it). A sensible bound is
the smear it produces, since that is the thing that damages the picture:
`rate_deg_s * (shutter/fps) * (3840 / hfov_deg)` under ~40 px at 4K.

---

## R2-852 — the film's subject leaves the film 5.5 s before the film ends

**MEASURED** by projecting `anim/carpath.Car` through the shipped rig, per frame.

| frame | car distance | car width @4K | off-axis | h half-angle | |
|---:|---:|---:|---:|---:|---|
| f2714 | 85 m | 200.0 px | 0.00 deg | 36.9 | centred, the seam |
| f2810 | 381 m | 38.5 px | 0.00 deg | 43.0 | centred, hand-off begins |
| f2833 | 476 m | 31.3 px | **44.6 deg** | 43.2 | **exits frame** |
| f2845 | 521 m | 27.9 px | 72.40 deg | 43.6 | gone |
| f2978 | 1000 m | (45.8 px) | **69.27 deg** | **13.67** | gone |

**The car is out of frame for f2833–2978 — 146 frames, 6.08 s, unbroken.** Not
occluded, not small: at the last frame it is **69.27 deg off the camera axis
inside a 13.67 deg half-angle**. Independently derived by the occlusion sweep
(f2834–2978, 145 frames, 69.26 deg) — the one-frame difference is an
edge-inclusive boundary at f2833, where the car sits within a pixel of the frame
edge, and is not a disagreement.

**An earlier figure of "roughly f2845" in this file was mine and was wrong** —
coarse frame sampling across a 12-frame stride. f2833 is the measured value.

**RETRACTION, carried here so it does not propagate:** an earlier cross-reference
in this staging file said the car was hidden behind `BR_FenceMesh_L03` on
f2976–2978 and that the fence was +7.105 m onto the racing surface (R2-017).
**Neither holds.** The `occ_frac_front = 1.000` rows are real but carry
`in_frame: false`, so they say nothing about a picture; and the fence
re-measures at **−6.756 m, i.e. 6.76 m *outside* the surface**, closed by a
world-contract fix. Nothing in R2-851..R2-856 depends on either claim.

### The hand-off was authored as a 2 s dissolve and executed as a 1 s cut-away

This is the part that decides what kind of defect this is. `aim["6_ending"]`
declares `car_until_t 4.0 → point_from_t 6.0` — a **two-second blend** of the
aim from the car to the facade, i.e. an author asking for a gradual transfer of
attention. f2810 is t=+4.0 and f2858 is t=+6.0.

**The car left the frame at f2833 — 23 frames, 0.96 s in, 48 % through the
blend, before the hand-off it was part of had finished.** At 19.1 mm the
half-angle is 43.25 deg, so the aim only has to travel 43 deg before the car is
outside the picture, and it has 82 deg to travel.

So the beat sheet declares **where the lens points**. It never declares **what is
in the picture**, and nothing measures it. The unwritten assumption was that a
wide lens easing between two subjects keeps the first one in shot for a while.
At an 82 deg separation it does not — it swings off it. The "letting go" beat
that would have made a departure legible was *intended* and did not happen.

R2-113 established the constraint honestly and it still holds: the car and the
wound are ~1 km apart at f2978 and no single frame can hold both. **What R2-113
did not weigh is that choosing the wound costs the film its subject for the last
quarter of the beat**, and the subject is the thing the audience has been asked
to care about for 113 seconds. That trade was never stated as a trade.

Note also: the shipped hold is **0.0022 m of movement and 0.00 deg of pan over
72 frames** — R2-113's own words, *"it is not a held frame, it is a still"* —
and its remedy was a lens push on a frozen camera. A lens push on a locked-off
frame is what a still photograph being zoomed looks like. **That is precisely
what "we just zoom out" is describing**, and the client is describing the last
gesture of the film accurately.

---

## R2-853 — CANDIDATE: lens and aim only. Every camera position byte-identical.

`docs/R2851_beat_sheet_CANDIDATE.json`, built to
`work/r2851/camrig_R2851.blend` + `_path.json`.

    >> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED

Two edits and nothing else:

| `beat6.keys[].t` | −3.0 | −1.0 | 0.0 | 2.0 | 4.0 | 6.0 | 8.0 | 11.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lens shipped | 32 | 28 | 24 | 21 | 19.5 | 18.75 | 40 | 74 |
| lens candidate | 32 | 28 | 24 | 21 | **22** | **30** | **55** | **130** |

and `aim["6_ending"]` becomes the car for the whole beat (`car_until_t` and
`point_from_t` both 11.0, so `fixed_point` stays declared and the
`undeclared()` validator is still satisfied).

**Every `world[]` and every `speed` is unchanged, so the position path is not a
new curve — it is the same curve.** Verified frame by frame against
`world/camera_rig_path.json`:

* **f1–f2714, worst position delta `0.000e+00` m, quaternion `0.000e+00`, lens
  `0.000e+00` mm.** The candidate is bit-identical to the shipped film up to and
  including the seam frame.
* **The f2714/2715 seam is arithmetically the same object in both:** 2.5454 m
  and 0.1063 deg in the shipped rig, 2.5454 m and 0.1063 deg in the candidate.
  The 1.33 % / ±0.72 MAD pixel measurement of that seam is not at risk, because
  no input to it moved.
* f2715–f2978 worst position delta **2.26e-3 m** — the Hermite resample's own
  float noise, not a change.
* `worst position jump 4.247 m at f1209` and `worst rotation step 12.957 deg at
  f2634` — both identical to the shipped rig, i.e. beat 6 does not become the
  film's worst case in either metric.

What it buys, on the path (**not yet on frames**):

* peak pan **91.5 → 11.0 deg/s**, smear **84.8 → 36.5 px**. The whip is gone —
  not smoothed, *gone*, because the camera is now following something that
  genuinely moves through that arc instead of jumping to a point 82 deg away.
* the car is in frame on **every frame of the beat**, and it never drops below
  **35 px** at 4K.
* the last 3 s stops being a still: **2.89 deg of pan** across f2906–2978 where
  the shipped hold has 0.00, and the car **grows from 45.8 px to 78.5 px** as
  the lens lengthens. The hold now has a reason to be a hold.
* the wide still happens, and earlier, where it is a landscape rather than a
  plan: f2763–f2811 at 21–22 mm and 62–99 m altitude, ~483 m across frame.

**What it gives up, stated plainly:** the breached facade. It is no longer in
the last frame at all. See R2-855.

---

## R2-854 — the "patches in the land" are a 155 m Voronoi partition, and the lens crops them but does not fix them

Mechanism established by forensics on `world/build_terrain.py` (findings are
that agent's; recorded here because they decide what the closing wide is allowed
to look at). **Do not merge this as a terrain fix — it belongs to #127's thread
and to whoever owns `build_terrain`.**

`field_pattern()` (`build_terrain.py:1140-1163`) is a Voronoi partition on a
**155 m lattice** warped by only ±46 m, so its cells are convex polygons with
**straight edges**. One `fid` per cell drives *both* colour terms:

* `ter_field` → `pal[floor(fid*3)]`, a **three-entry palette**, mixed in at a
  hard **0.55** constant (`build_terrain.py:2818`) — `pal[2]` = `(0.290, 0.215,
  0.093)` is the tan/khaki region;
* `ter_dry` → `0.15 + 0.85*fid`, swinging the other 45 % between albedo 0.051
  and 0.127 — **1.3 stops**.

Because they share `fid` they **add instead of decorrelating**, and the
transition occupies exactly one 2.5 m vertex cell. Meanwhile the ground shader's
colour spectrum has **nothing at all between 0.385 m and 7.7 m**, and nothing
unconditional between 0.385 m and 19 m. At the shipped closing wide's ~339 mm/px
everything at or below 0.4 m is sub-pixel, so **the only structure that survives
into the frame is 19 m and coarser** — which is to say, the patches, and nothing
else. Grass geometry is culled to zero beyond 700 m of the camera path, so most
of that frame is bare shaded mesh.

**What the candidate's lens does about it, arithmetically:**

| | shipped | candidate |
|---|---:|---:|
| widest lens in the beat | 18.75 mm | 22 mm |
| widest frame span | ~1,143 m | ~483 m |
| 155 m field cells across the widest frame | ~7 | ~3 |
| final-frame span | ~595 m | ~277 m |
| 155 m field cells in the final frame | ~4 | **~1.8** |
| final-frame ground sampling | ~74 mm/px | ~72 mm/px |

So the lens **removes most of the patch boundaries from the frame** — that is a
real and cheap answer to the literal complaint. It does **not** make the ground
good, and it makes one thing worse: at 72 mm/px the missing 0.4–19 m detail band
lands at 5–260 px, so the smoothness is now *more* legible per pixel even though
the blotching is less legible per frame. See R2-856, which measures this instead
of predicting it, and which contradicts the prediction I made first.

---

## R2-856 — how much of each closing frame is bare, grass-less mesh — MEASURED

Method: ray-cast a 96×54 grid through the frustum of the actual built path onto
z=0, then evaluate `build_terrain.py`'s own two scatter conditions at each hit —
`D < 430 m` from the centreline (line 3808) and `smoothstep(700, 260, dcam)`
against the camera path (line 3812). "Bare" means the ground is in frame and
carries **no grass geometry at all**, only the shader.

| | sky | grass | **bare mesh** | ground range |
|---|---:|---:|---:|---|
| **f2860, the widest moment of the pull-back** | | | | |
| shipped, 18.75 mm | 31.5 % | 42.0 % | **58.0 %** | 198 – 5,221 m |
| candidate, 30 mm | 20.4 % | 77.5 % | **22.5 %** | 250 – 4,657 m |
| **f2978, the last frame** | | | | |
| shipped, 74 mm | 0.0 % | 62.3 % | **37.7 %** | 392 – 1,463 m |
| candidate, 130 mm | 0.0 % | 54.4 % | **45.6 %** | 644 – 2,122 m |

**At the moment the client is describing** — the widest point of the pull-back —
**58 % of the shipped frame is ground with no plant geometry on it whatsoever**,
sampled at ~339 mm/px by a shader whose finest surviving colour term is 19 m.
That is the patchwork, and it is now a number. The candidate cuts it to 22.5 %,
because a 30 mm lens aimed at the car is looking at circuit, and the circuit is
inside the scatter radius.

**But the candidate's last frame is worse on this metric, not better** — 45.6 %
bare against 37.7 %. My earlier prediction in R2-854 that T1 would be inside the
grass radius was right about T1 and wrong about the frame: a 130 mm lens at 8.4°
depression reaches from 644 m to **2,122 m**, and the far half of that is past
`dcam < 700`. The long lens buys patch-boundary cropping and pays for it in
bare ground. Recorded rather than smoothed over.

**Lens sweep at f2978, same viewpoint** (the camera is static from f2906, so
only the lens differs):

| lens | car px @4K | sky | bare | horizon in frame |
|---:|---:|---:|---:|:--:|
| 70 mm | 43.5 | 6.3 % | 42.2 % | **yes** |
| 85 mm | 52.4 | 0.0 % | 47.5 % | no |
| 100 mm | 61.4 | 0.0 % | 47.1 % | no |
| **130 mm (candidate)** | **79.5** | 0.0 % | 45.6 % | no |
| 160 mm | 97.7 | 0.0 % | 44.4 % | no |

Two things fall out. **`bare` is flat at 44–48 % across 85–160 mm** — going
longer does not buy back ground quality, so 130 mm is not costing anything a
shorter lens would save. And **the horizon leaves frame between 70 and 85 mm.**
The shipped final frame is also 0 % sky; a closing frame with no horizon in it
is part of why both read as a plan rather than a view, and it is worth deciding
deliberately rather than inheriting.

The refinement this points at, **not** in the candidate and untested: ~85 mm
with the car framed in the **lower third** rather than centred, which puts the
horizon back across the top with the car still at ~52 px. `sheet["aim"]` has a
`z_off` but it is a constant over the whole beat and the car is 85 m away at
f2715 and 1,000 m away at f2978, so a fixed offset cannot do it — it would need
a declared framing offset that scales with subject range. f2937 in the candidate
is the same viewpoint at ~84 mm and is being rendered at 4K, so this can be
judged on pixels before anyone writes that parameter.

**Minimum terrain work this shot still needs, in priority order** (all
procedural, all inside existing files, none of it mine to land):

1. **Decorrelate `ter_dry` from `fid` and feather the cell boundary using
   `fdist`** — which is already computed and already used for hedges. ~6 lines.
   Kills the straight-edged patches outright.
2. **Fill the 0.4–60 m hole in `mat_ground`'s colour ladder** and the matching
   normal gap between `bump1` (0.385 m) and `bump2` (7.69 m). `ter_dist` is
   already created as an Attribute node at `build_terrain.py:2785` **and linked
   to nothing** — the crossfade hook exists.
3. **`SKY_STRATA=1`.** Structured low haze is written, tested and documented in
   `build_sky.py:944-966` and is off by default. It is the one-line fix for the
   featureless brown horizon band, which occupies ~15 % of the shipped closing
   frames.
4. Treeline: the beat-6 treeline is **16 unique L2 meshes repeated 150–256×
   each** (birch L2 is 4,089 instances from 16 meshes). That is 1.5–2.5× past
   this project's own "one tree spammed 100 times" red line, and it is only
   visible from altitude — i.e. only in this beat.

**Verdict on the ordering question:** the terrain work does *not* block the
camera change, and the camera change should go first. The reason is not cost, it
is that a beautifully textured version of the shipped ending is still an ending
with no subject in it. Fixing the ground makes the shipped wide *not ugly*; it
cannot make it *about* anything. Conversely the candidate reduces the ground's
share of the frame, which buys the terrain thread time without buying it an
excuse.

---

## R2-855 — what the ending is for, and the alternative that was rejected

The shipped ending's declared content is *"the circuit with the breached
showroom in it"*, and its last gesture is a push from 40 mm to 74 mm that brings
the wound from 37 px to 65 px. R2-113 did honest work to make that read and its
measurements are sound. **It still does not land, and the reason is not
resolution.**

At 65 px in a 3840 px frame the wound is 1.7 % of frame width, sitting in a
field of transporters, containers, light masts and paving of equal contrast,
and the audience last saw that building **80 seconds earlier, from inside, at a
completely different scale**. It asks a viewer to recognise a grey shed and then
read a hole in it, with no isolation, no contrast cue and no lead-in. The client
watched exactly this and reported seeing patches of land — which is what you see
when the intended subject does not resolve as a subject.

**The candidate's answer to "what is being revealed that is worth the last four
seconds":** the car, alone, still running, getting further away and *sharper* as
the lens lengthens on it. The film ends on the thing it is about, leaving under
its own power. The pull-back still happens and still reveals the circuit — it
just stops climbing into a plan view and stops turning its back on the car.

**The alternative, recorded so nobody re-derives it:** keep the wound and fix
its legibility instead — isolate it with light, or push further than 130 mm on
it, or move the hold position. Rejected for the beat because (a) the whip
survives it, since the 82 deg hand-off is what buys the wound at all; (b) it
still costs the last 5.5 s of the film its subject; and (c) the frame around the
wound is a truck park, and no lens fixes that.

**A third option that was NOT rejected and is not mine:** the car does not have
to still be at 300 km/h at f2978. `anim/carpath.Car` extrapolates past the end
of telemetry *"along the circuit's own centreline at its final speed"*
(`carpath.py:28-33`), which is a deliberate choice and a defensible one. A car
that decelerates on its lap-down would let the camera stay much closer to it and
would make a far tighter ending possible. That is a change to the car, not the
camera, and it should be decided by whoever owns the car — but the closing wide
is the only beat it would affect.

---

## R2-857 — should the film end on its subject at all? The decision, weighed.

Asked directly, because "put the car back in frame" is not automatically right
and a deliberate final drift off the subject is a legitimate ending.

### It WAS a decision. What was not decided is the thing that broke.

The record is explicit: `aim["6_ending"].subject` reads *"car until t=+4.0, then
the breached facade"*, `wound_enters_frame_t` is 6.0, `facade_px` is [109, 119],
and R2-113 measured three lenses against it and chose 40→74 mm on the evidence.
Somebody decided to leave the car, wrote it down, and defended it with numbers.
**This is not an undecided ending and should not be fixed as if it were a bug.**

What nobody decided — because nothing in the film measures it — is that the car
would be **gone 1 s into a 2 s hand-off**, swung off at 91.5 deg/s rather than
released. The beat sheet has a vocabulary for where the lens points and **no
vocabulary at all for what is in the picture**. That gap is the defect, and it
is the same family as R2-851's missing pan-rate bound and R2-113's dead `dlens`
variable: a quantity the film depends on that nothing computes.

### The drift ending, executed properly — costed, and rejected for now

A legible release is mechanically reachable and I costed it rather than
dismissing it. Slow the hand-off from `4.0 → 6.0` to roughly `4.0 → 9.0`: the
aim then travels 82 deg at ~16 deg/s instead of 91.5, and the car stays in frame
until about **f2875** instead of f2833 — a 42-frame improvement — and crucially
it **exits at the frame edge under its own motion**, which is what a deliberate
departure looks like. The whip dies at the same time.

**Rejected for this pass, on the destination and not on the gesture.** What the
camera lands on afterwards is unchanged: a 65 px wound in a truck park, and a
frame that R2-856 measures at **58 % bare grass-less mesh** at its widest.
Fixing the departure and keeping the arrival gives a well-executed move onto
something not worth arriving at. The client's note is about what the wide
*shows*, and this option changes only how we get there.

> The two options are therefore **not rivals on taste — they are gated on the
> world being finished.** When the terrain in R2-854 is done, the slow release
> is the better ending and it should be revisited. Today it is not available.

### Recommendation, and what it costs

**End on the car.** Not because ending on a subject is a rule, but because the
alternative's subject is a landscape that is 58 % untextured mesh under a
155 m Voronoi patchwork with a featureless horizon, and the car is a finished
hero asset. This is partly a verdict on the world's readiness and I would rather
say so than dress it as a story judgement.

**The cost, stated plainly: the film loses its callback to beat 3.** The wound
is the only narrative idea in the ending — the arc is *built → broke out → ran*,
and landing on the hole is what closes it. Ending on the car is a weaker idea
cleanly executed instead of a stronger idea that does not read. I do not think
that trade is close today, but it is a real loss and it should not be logged as
a pure win.

The callback cannot be rescued at these positions: the camera is 594 m from the
showroom because it flew there on a decelerating cubic, and flying back is both
outside the declared trajectory and would have to disturb the peel-off, which
sits inside the beat-5 hand-off blend and therefore on the f2714/2715 seam.
**That seam is measured clean at 1.33 % and this candidate does not touch it.**

### The one change that would let a future version have both

`anim/carpath.py:28-33` extrapolates the car past the end of telemetry *"along
the circuit's own centreline at its final speed"*. That is a declared choice,
not a measurement — and it is why the car is 1,000 m away and 69 deg off-axis at
the last frame. A car that decelerates on its lap-down, which is what one
actually does after a flying lap, would end the film far closer to the camera
and could share a frame with the circuit meaningfully.

**Cost of that change:** it moves the car for the whole of beat 6, so the
spatialised audio — engine, doppler, the camera-as-listener — needs a rebuild
over the last 11 s. It is not the camera's to make. Flagged for whoever owns the
car, as the single highest-leverage change available to this ending.

---

## R2-858 — the aim gate and the in-frame test made to meet, on the same numbers

An aim-error bound and an in-frame test are **not the same claim**, and this
project has twice been caught by two instruments that agreed in spirit and
measured different things. So they are reconciled here explicitly, on the
occlusion sweep's own reprojection, in its own units.

**screen-x in FRAME-WIDTH units** — 0.0 is the left edge, 0.5 the centre, 1.0 the
right edge — for the SHIPPED camera at f2978:

| source | screen-x |
|---|---:|
| occlusion sweep | 5.919 |
| its hand-reprojection | 5.917 |
| this file, rectilinear | **5.9194** |

**Agreement to 0.0004 frame-widths = 1.6 px at 4K.**

### My own instrument was wrong, and the way it was wrong is the lesson

An earlier revision of this file printed **6.064** for the same quantity. That
used an **angular (equidistant) mapping**, `x = f_px * atan2(loc_x, fw)`, and a
perspective camera is **rectilinear**: `ndc_x = (loc_x / fw) / tan(hfov/2)`. At
69 deg off-axis the two diverge badly. **Withdrawn.**

What makes it instructive is *which* number survived the error. The off-axis
angle came out at 69.27 deg against the sweep's 69.26 and looked like
independent confirmation — **but an angle is projection-independent, so it could
not have disagreed.** The agreeing number carried no information about the thing
that was broken, and the screen coordinate that did carry it was 2.5 % out. Two
instruments agreeing on a quantity neither of them projects is the failure mode
this section exists to prevent, reproduced by the author of the section.

### Both tests, both arms, over the whole beat

| frame | shipped screen-x | | candidate screen-x | |
|---:|---:|---|---:|---|
| f2810 | 0.5000 | in frame | 0.5000 | in frame |
| f2833 | **1.0097** | **OUT** | 0.5001 | in frame |
| f2900 | 3.5887 | OUT | 0.5000 | in frame |
| f2969 | 6.2287 | OUT | 0.4969 | in frame |
| f2977 | 5.9775 | OUT | **0.5071** | in frame |
| f2978 | 5.9194 | OUT | 0.5000 | in frame |

* **shipped: 146 of 264 frames out of frame**, one unbroken run f2833–2978,
  worst `|ndc|` 11.457 at f2969.
* **candidate: 0 of 264 frames out of frame**, worst `|ndc|` **0.014** at f2977 —
  the car is within **0.7 % of frame centre for all 264 frames**.

**The two instruments' worst cases land on the same frame, f2977**: the aim gate
reads 0.1109 deg against a 26.0 bound, the in-frame test reads screen-x 0.5071.
They are measuring different things and they now agree about which frame is
hardest, which is the cross-check that was missing.

> The film's ending contains its subject. **This is a claim about geometry, not
> about the picture** — whether the car is *legible* at 1,000 m through 130 mm of
> haze is a separate question and only the 4K stills can answer it.

---

## R2-859 — beat 6 keys its rotation every 8 frames on any smoothly-tracked aim, and the aim gate cannot see the result

**The rule** (`anim/build_camera_rig.py`): step 2–8 frames, break when the bearing
has moved more than **5.0 deg**. It was written for a beat 6 whose aim swings
**82 deg** from the car to a fixed facade, where 5 deg trips constantly and the
stride stays short.

**It is wrong for any beat 6 that tracks a subject.** R2-853's candidate moves
its aim ~2.9 deg *in total*, so the 5 deg test **never fires**, the stride pins
at its maximum 8, and rotation is keyed every 8 frames straight through the one
place it must not be — the last half second, where the car rounds T1 and the pan
the camera owes it accelerates **7x, from 0.030 to 0.213 deg/frame**.

Measured on the 8-frame build, car offset from frame centre, px @4K:

    f2968  -5.5   f2971 -22.3   f2974 -14.5   f2977 +27.1
    f2969 -11.8   f2972 -24.2   f2975  -0.0   f2978  -0.0
    f2970 -17.8   f2973 -22.1   f2976 +19.7

A **51 px swing in 5 frames** — the subject visibly drifts off centre, overshoots
the other way and snaps back, in the last half second of the film.

**The aim gate reports this as 0.1109 deg and PASSES it against a 26 deg bound.**
A bound sized for *"is the subject in shot"* cannot see a wobble three orders of
magnitude below it — the same shape as R2-851's missing pan-rate bound.

**A degree threshold could not have caught it either.** The failure is that the
aim's *second* derivative is large while its first derivative is small, and a
first-order test is blind to that by construction. So the **stride cap** is the
parameter that matters, and it is now the one exposed.

**Fix:** the stride and the bearing bound are read from
`sheet["beat6"]["aim_keying"]`, defaulting to `8` and `5.0`.

* **The default is proven a no-op.** Built the *same* shipped sheet with the
  original code and with the edit and diffed all 2,978 frames:
  **position `0.000e+00` m, quaternion `0.000e+00`, lens `0.000e+00` mm.**
* Candidate sets `max_stride_frames: 2` — 156 intermediate samples, up from 63.

| | stride 8 | stride 2 |
|---|---:|---:|
| worst car excursion, whole beat | 27.1 px | **16.4 px** |
| aim gate, `6_ending` | 0.1109 deg | **0.0717 deg** |
| f2968–f2976 excursion | up to 24 px | **under 1.2 px** |

Worst rotation smear is 36.5 → 33.7 px and that is **correct, not residual** —
it is the pan the moving car actually requires, i.e. physics, not error.

---

## R2-860 — what can and cannot move the post off the car. My own hypothesis was wrong.

The 2 px post at x=1941–1942 grazing the car's trailing edge at f2978.

**I predicted the R2-859 wobble caused it. It does not.** f2978 is a *declared
key* where the aim was already exact (car offset `+0.031 px` before and after),
so densifying the keys leaves the post exactly where it was. Recorded because
the prediction was wrong and the measurement is what settled it.

Three levers tested against the geometry:

1. **Camera rotation — CANNOT work, and this is exact, not approximate.** A pure
   rotation moves the car and the background by the *same* angle. Measured at
   f2978: separation is **20.87 px at 0.00 deg of extra yaw, 20.87 px at 0.07
   deg, and 20.87 px at 0.30 deg.** Nudging the aim is not available.
2. **Lens — CANNOT work.** The post is 21 px off-axis, and a focal change scales
   the car and its offset together. The tangency is **scale-invariant**.
3. **Camera translation — would work** (~1 m of lateral parallax), and is the
   one thing that breaks R2-853's byte-identical position guarantee.

So the tangency is **rotation-invariant and scale-invariant**. Only parallax or
moving the post itself changes it.

**And the post is not a free parameter.** `FENCE_SPAN = 8.00` is declared —
`build_barriers.md`: *"debris (catch) fence, 3.6 m mesh on 6 m posts at **8 m
centres** | spec §9"*. Posts sit at exact multiples of it along the barrier
polyline (`u = pi * FENCE_SPAN`). Moving one post would (a) break a declared
pitch locally, (b) have to propagate into the fence weave, which is built
between consecutive posts, and the marshal-gate frames built from the same
`posts` list, and (c) desynchronise `world/items/catch_fence_post.py`, which
builds the same population independently and whose count agreement with this
loop is an existing check (R2-331/R2-229). The *phase* is undeclared, but
shifting it moves all 690 posts in every frame of the film.

> **Verdict: this is not the cheap placement change it looked like.** It is a
> camera-parallax question or an accepted tangency, and it should be decided
> deliberately. Awaiting an object-ID ray-cast to confirm the post is in fact a
> `BR_Fence*` member and whether it is nearer than the car (occluding) or
> further (merely adjacent) — that distinction has not been established and I
> have not assumed it.

---

## R2-861 — the shipped beat sheet fails its own camera-rig gate, and it moved mid-task

`docs/beat_sheet.json` was rewritten at **03:48 today** — beat 1 went from 23
camera keys to **19** (the re-paced beat 1). Two consequences.

**1. The current sheet does not build a passing rig, and it is not mine.**

    >> per-beat verdict:
         1_assembly  FAIL  subject reaches 1.155 of the half-frame at frame 431 (margin 0.92)
    >> STAGE RESULT: CAMERA_RIG_FAIL

Proven pre-existing rather than asserted: the **original, unmodified**
`build_camera_rig.py` produces the identical FAIL on the identical sheet. Beat 6
passes in both. **Flagged for whoever owns the re-pacing — a film cannot be
rebuilt from this sheet until f431 is resolved.**

**2. R2-853's candidate has been re-based onto the current sheet** and now
carries beat 1 identical to shipped (19 keys). Re-verified against a build of
the *current* shipped sheet:

* **f1–f2656 bit-identical** — 2,656 frames, position and quaternion both
  `0.000e+00`.
* Only **50 frames differ, f2657–f2714**, inside the beat-5→beat-6 hand-off
  blend, worst **1.39 mm** and **0.0217 deg**. At f2680 the camera is travelling
  ~3.3 m per frame, so 1.39 mm is 0.04 % of one frame's travel.
* **The seam frames are untouched in position:** f2714 and f2715 both
  `0.000e+00` m, quaternion `1e-6` (~0.0001 deg, about 0.006 px at 4K).
  **The 1.33 % seam measurement is not at risk.**

**The render in flight predates the re-base.** It carries the stride-8 keying
and the old beat 1. Beat 1 does not affect f2715–2978, and f2978 is unchanged,
so it remains valid for judging the *gesture* and the 4K stills; it does not
carry the R2-859 wobble fix. Not worth re-queueing on its own.

---

## R2-862 — WATCHED. The candidate fixes the geometry and does NOT fix the ending.

264 frames at 720p (`watch/R2851_ending_CANDIDATE.mp4`) against the shipped arm,
plus the 4K stills at 1:1. **MEASURED ON FRAMES**, not on the path.

**What it fixes, and these hold up on screen:** the whip is gone, the pull-back
reads as one continuous gesture, the hold breathes instead of freezing, and the
frame at f2860 is circuit and treeline rather than 58 % bare mown-looking field.
Against the shipped arm it is better in every respect the client complained about.

**What it does not fix.** At 1:1 on the 4K final frame the car is dead centre and
is **a grey-blue smudge on the run-off, of a piece with the tyre-wall shadow and
the gravel behind it.** The frame is a handsome, layered, correctly-hazed aerial
of a circuit corner **with no subject in it.**

This is not the wash-out I was worried about — the car is *visible*. It is that
**visible and "a subject" are different things, and I conflated them.** The 4K
measurement said so in numbers before I looked: peak luminance contrast **7 %
below** background, the car actually *brighter* than its surround (0.516 vs
0.476), carried by a specular hit on the airbox and a 0.14 blue-minus-red break.
That is a detail you can find when told where to look. A closing image cannot be
built on it.

### The camera cannot fix this. The distance can.

At 130 mm and 4K:

| car distance | width @4K | reads as |
|---:|---:|---|
| **1,000 m — today** | **79.5 px** | a smudge on the run-off |
| 700 m | 113.6 px | findable, still not a subject |
| 450 m | 176.7 px | a car |
| 300 m | 265.0 px | a car with a visible wing and airbox |

There is no lens and no aim that turns a 5.698 m object at 1 km into a closing
subject — R2-860 already showed the framing is rotation- and scale-invariant.
**The only free variable left is how far away the car is**, and that is
`carpath.py`'s extrapolation at a constant 83.1 m/s, which carries it 913 m in
the closing 11 s.

A lap-down deceleration is not enough on its own:

| 83.1 m/s decays to | travelled | approx camera distance | width |
|---:|---:|---:|---:|
| 60 m/s (216 kph) | 787 m | ~862 m | 92 px |
| 40 m/s (144 kph) | 677 m | ~742 m | 107 px |
| 15 m/s (54 kph) | 540 m | ~591 m | 134 px |

**But the car coming to rest near the start/finish line does it.** From the hold
at `[594.19, 16.05, 140.0]` to `start_finish_world [329.396, 169.82, 0]` is
**336.7 m — 236 px.** That is a subject, and a car easing to a stop after a
flying lap is what actually happens. It is also a better *idea* than the current
one: the film would end where the lap began.

### Recommendation

**Ship R2-853 anyway, and do not call the ending solved.** It is strictly better
than the shipped arm on every axis, and — the reason it matters — **it is the
necessary first half.** Its aim tracks the car, so a car that ends up closer is
framed automatically and correctly. The shipped camera would still be pointed at
the facade and would miss a nearer car entirely.

**The second half is not mine.** It is `anim/carpath.py:28-33` and it costs an
11-second rebuild of the spatialised audio. R2-857 flagged it as the
highest-leverage change available; **R2-862 upgrades it from an option to the
finding.** The ending is a car-motion problem wearing a camera problem's clothes,
and three passes of camera work were needed to establish that it is not a camera
problem.
