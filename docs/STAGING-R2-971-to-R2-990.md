# STAGING — R2-971 to R2-990 · the ending, adjudicated

> ## ⚠ ENTRY-NUMBER COLLISION — READ BEFORE MERGING ANYTHING FROM THIS FILE
>
> **`docs/STAGING-R2-971-to-R2-999.md` already occupies R2-971 … R2-982** with a
> completely different subject — render economics, instance pricing and the 4K
> master's disk fit. It was last written 2026-08-07 10:34, while this file was
> being written.
>
> **So R2-971 through R2-982 each name two different things right now.** My
> R2-974 is the internal-contrast instrument; theirs is "INSTANCE 47049525 IS
> BURNING STORAGE FOR NOTHING". The defect log's merge rule is *merge by
> identity, never by position*, and that rule cannot survive two entries with the
> same identity.
>
> I was told this file was new and that nothing else writes here. That was true
> of the **filename** and false of the **numbers**, and I did not discover it
> until after the entries were written and cross-referenced to each other.
>
> **I have deliberately not renumbered.** Renumbering now would silently break
> every internal cross-reference in this file and, worse, would be a guess at
> which of two live agents owns the range. **Whoever merges these must
> renumber one of the two files as a deliberate act.** My entries are
> self-consistent and can be moved as a block; the natural fix is to shift this
> file to a free range (R2-991+ or beyond) since the other file claims the wider
> span.

**Owner: the independent adjudicator.** I did not build the camera candidate,
the lap-down, the audio or the world. Nothing in this file may be merged into
`docs/DEFECT-LOG-R2.md` by me, and I have edited no file in this tree other
than this one.

The question I was given is one question and I answer only it:

> Does the film now end on a subject? Not "is the car bigger" — that is
> established arithmetic. Is the last frame an image of *a car arriving*, or a
> tighter crop of the same aerial with a bigger dot in it?

The standard is the one the previous adjudicator wrote down after getting it
wrong: **visible and "a subject" are different things.** Three consecutive
passes of camera work reported success; the fourth pass watched all 264 frames
and the 4K stills at 1:1 and found the ending still did not work. I have
assumed throughout that I am the fifth pass and that the prior is failure.

---

## R2-971 — PRE-REGISTERED. Twelve falsifiers, written before a single frame of this arm existed.

Written and saved before the re-key had finished loading the film scene, i.e.
before `watch/r2943_4k/` or `watch/r2943b6_frames/` contained anything at all.
I have read R2-950's five pre-registered failure modes; they are the builder's
list. These are mine. Where they overlap I say so, and where I think the
builder's own number is wrong I give mine.

Two of these (**F1**, **F8**) are already measured, on geometry rather than
pixels, and are stated here as findings rather than as questions.

### F1 — the closing car is 215 px, not 231, and "a subject" is 236

**MEASURED** on `work/r2941/camrig_R2943_path.json` and `anim/carpath.Car`,
before looking at a frame.

R2-945 and R2-949 report the closing car at **230.7 / 230.4 px**. That figure is
`CAR_LEN * px_per_metre` — the car's full 5.698 m held broadside and square to
the lens. The car is not square to the lens. At f2978:

| | |
|---|---:|
| car heading | 40.00 deg |
| bearing camera → car | 106.95 deg |
| **yaw between car axis and view azimuth** | **66.95 deg** |
| depression of the view | **24.10 deg** |
| foreshortening factor `sin∠(car_fwd, view_dir)` | **0.9337** |
| **projected long axis** | **215.2 px** |
| projected across-car axis | **44.0 px** |

Against R2-862's own ladder — 176.7 px "a car", **236 px "a subject"**, 265 px
"a car with a visible wing and airbox" — the honest number is **215 px, which is
8.8 % short of the quoted figure and 8.8 % below the "a subject" line**, not 2 %
below it. The car is between "a car" and "a subject" on the builder's own scale.

This does not decide anything on its own. It does mean the arithmetic no longer
reaches the threshold the whole change was aimed at, and that the decision must
be made on the picture with no margin in hand.

**Falsifier:** if the silhouette measured on the rendered 4K frame is materially
shorter than 215 px, the size claim has been overstated twice and the ending is
being defended by a number that was never true.

### F2 — a subject has internal structure

The discriminator between "a car" and "a bigger dot" is not extent, it is
whether the object resolves into *parts*. At three-quarter-rear-high — which is
what 66.95 deg of yaw and 24.10 deg of depression give — the parts that must
show are the **rear wing as a distinct horizontal bar**, the engine cover /
airbox ridge, the front wing beyond the nose, the four wheels separated from the
body, and the waist between sidepod and floor.

**Falsifier:** at 1:1 in a 400×300 crop, if the car is a single elongated blob
with no internal edge — in particular **if the rear wing cannot be seen as
separate from the body** — it is a bigger dot and the ending fails.

### F3 — figure/ground at the car's edge, and the new risk nobody costed

R2-862's failure was that the car separated from its background by a **0.14
blue-minus-red break and a specular hit**, not by luminance — it measured
*brighter* than its surround (0.516 vs 0.476). At 1 km it sat on gravel run-off.
**It now stands on tarmac.** A dark blue-grey car on grey asphalt is a different
and worse figure/ground problem, and I cannot find it costed anywhere in
R2-941..R2-950.

**Falsifier:** if the car's median luminance is within ±8 % of the pit-straight
tarmac immediately around it *and* the colour break is again the only separator,
then R2-862's failure has been reproduced at 2.7× the size and the extra pixels
bought nothing.

### F4 — "we just zoom out" is the client's actual sentence, and the gesture is byte-identical

R2-944 states it plainly and it is the most important sentence in the staging
file: the beat sheet is **R2-853's, unmodified**, and every camera `world[]` and
every `speed` is unchanged from the shipped film. So:

* the camera still climbs from **27.5 m to 140.0 m** across the beat,
* it still travels **+279 m in x and −73 m in y** away from the car,
* the lens still opens to its widest at f2763,
* and the frame's world width still runs **131 m → 422 m** by f2823.

**The gesture the client complained about is still in the film, in full, and
R2-943 does not touch a byte of it.** The only thing that changed is what is at
the end of it.

**Falsifier:** watching f2715-2860 at speed, if the dominant read is still
*retreat* — the world opening up and the eye losing its anchor — then the change
has appended a payoff to the complaint rather than answered it. What would clear
it: the widening reading as a reveal *of the car's deceleration*, the eye staying
on the car because the car is visibly slowing against a streaming background.

### F5 — the widest frame is where the patches live, and it is still there

Frame world width peaks at **422 m at f2823**, and is **420 m at f2811** at
22 mm from 99 m of altitude. R2-854's "patches" are a **155 m Voronoi
partition**, so a 420 m frame holds about **seven cells across** — the worst
possible sampling, wide enough to show the tiling and tight enough for the
straight cell edges to read as edges.

**Falsifier:** if the 4K stills at f2760 and f2811 show straight-edged tonal
polygons, the client's literal complaint survives at the exact moment the beat
is widest, whatever the last frame does.

### F6 — the last 4.1 s is a pure lens push on a locked frame — not 1.75 s

R2-949 item 1 and R2-950 item 2 register this as **42 frames / 1.75 s**, from
the car stopping at f2936 to f2978. I make it far worse, and the difference is
the whole argument.

The camera *tracks the car dead centre* for all 264 frames (`|ndc| = 0.000`), so
the car does not move on screen at all. All perceived car motion is carried by
the **background streaming past it**. R2-943's own table gives that rate:

| frame | background streaming past the car, px/frame @4K |
|---:|---:|
| f2715 | 109.70 |
| f2760 | 32.75 |
| f2820 | 5.98 |
| f2880 | **1.83** |
| f2906 | **1.13** |
| f2936 | 0.00 |

The camera's position stops at **f2906**. Below roughly 2 px/frame at 4K there
is nothing an audience can see, so from about **f2880** the only thing moving in
the frame is the lens. That is **98 frames = 4.1 s**, not 42 frames = 1.75 s.

**Falsifier:** if, watching, I cannot say within ~10 frames when the car stopped,
then nothing *arrives* — the motion dissolves rather than resolves — and
R2-852's *"a lens push on a locked-off frame is what a still photograph being
zoomed looks like"* applies to the new ending exactly as it applied to the old.

### F7 — the arrival happens in the middle of the beat, not at the end

Of 264 frames, essentially all of the perceptible deceleration happens in the
first **105** (f2715-2820, 109.70 → 5.98 px/frame, an 18× collapse). The
remaining **159 frames / 6.6 s** are a lens move on a car that has, to the eye,
already arrived.

**Falsifier:** if the event lands at ~f2820 and the last 6.6 s is a zoom, then
the film's final gesture is still a zoom and the arrival is not the ending — it
is six and a half seconds before the ending.

### F8 — the light is frontal and flat, and the shadow is behind the car

**MEASURED** on `world/build_sky.py`, before looking at a frame. I can find no
entry in R2-941..R2-950 that costs the lighting of the closing frame at all.

`SUN_ELEV = 12.4706 deg`, `SUN_BEARING = −57.9697 deg`. At f2978 the camera lies
at bearing **286.95 deg** from the car and the sun at **302.03 deg** — they are
**15.1 deg apart**. The sun is therefore almost directly behind the camera:

* the car is **front-lit and flat-lit**, with no shape-defining shadow on its own
  body — which is the light that most suppresses the internal structure F2
  requires;
* its cast shadow is **4.49 m** long (0.992 m of car at 12.47 deg of sun) and
  points at bearing **122.03 deg**, i.e. **within 15 deg of directly away from
  the camera**, so it projects to ~**86 px** but falls largely *behind* the car's
  own body where the camera cannot see it.

**Prediction, registered so it can be wrong in my favour:** a 4.49 m cast shadow
from a 12.5 deg sun is a large feature, and a shadow anchoring an object to a
plane is the single strongest cue that a thing is an object rather than a
texture patch. **I expect the shadow, not the car's own 215 px, to decide F2.**
If it is visible the ending has a chance; if the geometry has hidden it behind
the car, the car floats.

### F9 — arrival needs a destination, and R2-943b proves there is none in frame

R2-943b establishes, and I accept, that the closing frame contains **no
start/finish line, no pit building, no grandstand and no architecture of any
kind** — a 95 m stretch of pit straight and grass, and that this is determined
rather than chosen. *"The film ends where the lap began"* is therefore true in
the world and, by the builder's own measurement, **invisible**.

This is the sharper form of R2-950's item 1. The question is not whether the car
reads as broken down; it is that **arriving requires somewhere to have arrived**,
and there is nothing in the frame that says *finish* rather than *stop*.

**Falsifier:** if the closing frame contains no cue that this is an end of a lap
— no line, no structure, no marshal, no flag, nothing — then the image is "a car
stopped in a field", and the entire difference between arriving and breaking
down is being carried by four seconds of braking that have already ended, and
not by the frame the film actually ends on.

### F10 — no horizon and no sky anywhere in the closing 5 s

Taken over unchanged from R2-949 item 3, because it is correctly registered and
I have nothing to add except that it is now load-bearing in a way it was not:
the closing frame is 95 m of ground with no sky, no horizon and (F9) no
architecture. A frame with none of those three is a **plan**, not a view.

### F11 — runtime, the seam, and the aim gate

Re-measured, not assumed:

* runtime must remain **2,978 frames / 124.0833 s**;
* the **f2714/2715 seam** must re-measure at ~1.33 % from interpolation **on
  rendered frames**, not on the path;
* the **aim gate** claim of 0.029 deg worst at f2758 against a 26.0 bound.

### F12 — the grade

Delivery is **3840×2160 / 24 fps / AgX / look None / exposure −3.628 / SDR**.
The car's legibility at distance across the whole film depends on a **0.14
blue-minus-red** break and a specular glint, not on luminance. **Falsifier:**
any crushed saturation or lifted black floor measured against the already-
rendered B-candidate 4K stills at the same frames.

---

## R2-972 — where my list and the builder's differ

| | R2-950's five | mine |
|---|---|---|
| dead final phase | 42 frames / 1.75 s | **98 frames / 4.1 s** (F6) — the car is imperceptible from f2880, not f2936 |
| the car's size | 230.7 px, "2 % below a subject" | **215.2 px, 8.8 % below** (F1) — the quoted figure ignores 66.95 deg of yaw |
| reads as broken down | defended by the preceding braking | **F9** — the frame has no destination in it, which is a property of the last frame and not of the braking |
| the client's sentence | not addressed | **F4** — the "zoom out" gesture is byte-identical to the shipped film's |
| lighting | not addressed anywhere | **F8** — 12.47 deg frontal sun; flat light and a hidden shadow |
| grade, seam, runtime, occlusion | registered | kept (F11, F12) |


---

## R2-973 — the four re-measurements. Three hold exactly. The fourth is measured on rendered frames and holds.

Taken before the R2-943 frames existed, on the built path, the beat sheet and
the frames already on disk.

### Runtime — HOLDS

`docs/beat_sheet.json` and `docs/R2851_beat_sheet_CANDIDATE.json` both declare
`fps 24`, `total_s 124.1`, `total_frames 2978`, and
`work/r2941/camrig_R2943_continuity.json` reports `frames 2978`,
`resolution [3840, 2160]`, `shutter flat [180.0, 180.0]`. The film clock is
built by `filmtime.build_time_map(sheet, 2978)` from the **beat sheet**, which
the lap-down does not touch; the only `time_map` entry is beat 3's ramp
(`declared_world_s 1.6`, `achieved 1.6000000000000003`), unchanged.

**2,978 frames / 124.0833 s. The deceleration did not move it, and could not
have — it is a car change and the clock is a camera-and-sheet object.**

### The aim gate — HOLDS EXACTLY

`camrig_R2943_continuity.json`, `aim_per_beat["6_ending"]`:

```
ang 0.02902241204399352   ang_f 2758   bound_deg 26.0   n 264
off 6.336844117202535e-05 off_f 2719   dist_m 342.53708740806445
```

**0.029 deg worst at f2758 against a 26.0 bound**, exactly as claimed, over all
264 frames, at a max subject range of 342.5 m. `worst_position_jump_m 4.2469 at
f1209` and `worst_rotation_step_deg 12.957 at f2634` are also as claimed — beat
6 is not the film's worst case in either.

### The f2714/2715 seam — MEASURED ON RENDERED FRAMES, and my instrument was validated first

The seam claim is the one I was told to re-measure on pixels rather than on the
path, so I did not accept R2-944's *"nothing that feeds it moved"*.

**Instrument validation.** I rebuilt R2-711's method — the frame-difference
series through the boundary against linear interpolation from its immediate
neighbours, plus the ratio to the local median and the MAD distance — and ran it
on `out2/seq/r2full/` (the shipped film, 720p, frames 793-2978):

```
d[2712->2713] = 0.056714
d[2713->2714] = 0.054425
d[2714->2715] = 0.052134   <- the seam
d[2715->2716] = 0.051252
d[2716->2717] = 0.050557

SHIPPED f2714/2715   obs=0.052134  lin_pred=0.052838  dev=-1.33%  ratio_to_median=0.947
```

**−1.33 %, reproducing R2-711's published figure to two decimal places on an
instrument built independently.** That is the agreement that licenses everything
below it.

**The splice, and its validation.** No arm of beat 6 has a rendered f2714 —
every beat-6 render on disk starts at f2715 — so the seam can only be measured by
splicing the shipped f≤2714 to the candidate f≥2715. That is exactly the
identity R2-944 claims, so using it would be assuming the answer. I therefore
validated the splice on the arm where it can be checked, the R2-853 camera-only
candidate (`out2/seq/r2851b6/`), whose beat-6 aim is the car in both arms before
t=4.0 and which was rendered under a **different `spec_hash`**
(`6061ca627b6c03d0` against r2full's `1dd9cdaf86a87876`):

```
B-CANDIDATE spliced  obs=0.052133  lin_pred=0.052838  dev=-1.33%
```

**The cross-spec splice changes the measured difference by 1e-6 on a value of
0.052** — the two renders are noise-free relative to each other, so splicing
adds ~0.002 % to a 1.33 % signal. The method is sound and I will apply it to the
R2-943 frames when they land.

### The grade — baselines established on the arms already on disk

Delivery asserted by the re-key: 3840×2160 / AgX / look None / exposure −3.628.
`exposure_calibration` in the continuity report reads `film_exposure −3.628`.
Measured on the 4K PNGs:

| | lum p0.1 | p50 | p95 | p99.9 | mean sat |
|---|---:|---:|---:|---:|---:|
| shipped f2811 | 0.1513 | 0.3943 | 0.7230 | 0.7438 | 0.2481 |
| B candidate f2811 | 0.1487 | 0.3830 | 0.7209 | 0.7435 | 0.2544 |
| shipped f2978 | 0.1752 | 0.3651 | 0.7049 | 0.7806 | 0.2046 |
| **B candidate f2978** | **0.2913** | 0.4391 | **0.5648** | 0.7483 | 0.2369 |

The B candidate's closing frame has a **black floor lifted to 0.291 and a p95
crushed to 0.565** — half the shipped frame's dynamic range. **That is not a
grade, it is 1 km of atmospheric haze**, and it is a large part of why R2-862
found the car unreadable there: the arm that was judged had lost half its
contrast to distance before the car was even considered. A closing frame at
343 m should recover most of it, and if it does not, that is a finding.

Car versus surround in the B candidate's f2978, reproducing R2-862's
measurement: car box **lum 0.5445**, surround **lum 0.5149** — **the car is 5.7 %
brighter than its background**, confirming R2-862's "brighter than its surround"
independently.


---

## R2-974 — NEW INSTRUMENT. What actually makes the car read is internal contrast, not luminance and not the colour break — and R2-862's ladder is calibrated at the wrong distance.

**MEASURED ON RENDERED 4K FRAMES ALREADY ON DISK**, before any R2-943 frame
existed. Nobody on this project has run this comparison, and it changes what the
closing frame has to achieve.

### The calibration nobody did: bracket 215 px with real frames

R2-862's ladder — 176.7 px "a car", 236 px "a subject", 265 px "wing and airbox"
— was derived **at 1,000 m through the haze of the shipped closing frame**. It
has been used ever since as if it were a property of pixel counts. It is not.
There are 4K frames of this same car, at nearly the same depression angle, on
disk:

| frame | car distance | projected px | depression | source |
|---|---:|---:|---:|---|
| f1120 | 43.6 m | 285.2 | 22.1 deg | `out2/seq/m4k_probe/` |
| **f2035** | **110.7 m** | **144.3** | **21.9 deg** | `out2/seq/b5verdict_4k/` |
| f2978 (B) | 1,000.1 m | 79.0 | 24.1 deg | `out2/seq/r2851_4k_B_candidate/` |
| **f2978 (A, pending)** | **342.9 m** | **215.2** | **24.10 deg** | — |

**I opened f2035 at 1:1. At 144 px the car is unmistakably a car** — the rear
wing reads as a distinct multi-element bar, the airbox and engine cover are
separate, the driver's yellow helmet is visible in the cockpit, the front wing's
elements are individually resolved, and all four wheels are clearly detached from
the body. It is sitting **on tarmac**.

**So 144 px at 110 m is comfortably "a subject" while 79 px at 1 km is a smudge,
and the ladder that says the boundary is 236 px cannot be right as stated.**
Legibility is a function of angular size *and* haze *and* what the car is sitting
on. R2-862 measured one point on that surface and reported it as a threshold.

### F3 is answered, and answered favourably, before the frame arrives

I registered dark-car-on-grey-asphalt as an uncosted new risk. **f2035 refutes
it**: this car's livery is blue and cyan and the tarmac is neutral grey, so the
car separates from the road strongly. Tarmac is a *better* ground for it than the
gravel run-off the B arm parked it on.

### The mechanism is internal contrast, and R2-862 diagnosed it as the wrong thing

Measuring the car region against the surface immediately beside it:

| frame | car lum | bg lum | **lum break** | b−r break | car p95−p5 | bg p95−p5 | **ratio** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **f2035 — reads as a subject** | 0.2089 | 0.2163 | **−3.4 %** | +0.0246 | **0.3359** | 0.0448 | **7.50×** |
| **f2978 B — judged a smudge** | 0.5479 | 0.5302 | +3.3 % | — | 0.1903 | 0.2112 | **0.90×** |
| f1120 (285 px, 43.6 m) | 0.1495 | 0.2139 | −30 % | — | 0.3139 | 0.2258 | 1.39× |

**Look at the frame that unambiguously works.** Its luminance break against the
road is **−3.4 %** — essentially nothing — and its blue-minus-red break is
**+0.0246**, six times *smaller* than the 0.14 that R2-862 said was carrying the
distant car. Neither of the two quantities the project has been protecting is
doing the work.

What separates them is that **the car carries 7.50× the internal contrast of the
surface it sits on**. It is a high-variance, structured object on a smooth,
low-variance ground. And the failure case says the same thing from the other
side: in the B arm the car's internal contrast is **0.90× its background's** — it
is a *smoother* patch than the gravel, rake marks, tyre wall and fence around it,
which is precisely why the eye will not stop on it.

> A car reads as a subject when it is the most structured thing in its
> neighbourhood. R2-862 found a colour break and a specular glint because at
> 79 px those are the only things that survive — they are the *residue* of
> legibility, not its cause. Protecting them is protecting the symptom.

### What this means for the grade constraint

The standing constraint — no crushed saturation, no lifted blacks — is **still
right, and for a better reason than the one recorded.** What must be protected is
not the 0.14 colour break; it is the car's *internal* contrast, and lifting
blacks or crushing saturation destroys that far more directly. The constraint
survives; its justification should be rewritten.

### And it gives the closing frame a pass/fail test with a number on it

When the R2-943 f2978 lands I will measure the same ratio. On smooth pit-straight
tarmac the background should be low-variance like f2035's, so:

* **ratio ≳ 3× and car p95−p5 ≳ 0.25 → the car reads as an object.**
* **ratio ≲ 1.5× → it has reproduced the B arm's failure at a larger size.**

Registered before the measurement.

---

## R2-975 — the haze at 343 m is roughly half the haze at 1 km, measured

The B arm was judged at 1,000 m, and a large part of what beat it was never the
car — it was that the frame had lost half its dynamic range to atmosphere before
the car was considered. Measured across four 4K frames, same AgX, same −3.628:

| frame | subject distance | lum p0.1 | p95 | **range** |
|---|---:|---:|---:|---:|
| f1120 | 43.6 m | 0.0549 | 0.2921 | 0.237 |
| f2035 | 110.7 m | 0.1022 | 0.5180 | 0.416 |
| **f2850** | **308.1 m** | **0.1826** | **0.7170** | **0.534** |
| f2978 B | 1,000.1 m | 0.2913 | 0.5648 | **0.274** |
| f2978 shipped | (mixed, near) | 0.1752 | 0.7049 | 0.530 |

**At ~308 m the frame keeps a 0.534 range — the same as the shipped closing
frame's 0.530 — while at 1 km it collapses to 0.274.** The lap-down's closing
frame sits at 343 m, i.e. essentially at the f2850 point on this curve.

**This is the single largest unclaimed advantage of the change, and R2-941..R2-950
never mentions it.** Bringing the car from 1 km to 343 m does not only make it
2.7× bigger in linear terms; it roughly doubles the contrast available to render
it with. The staging file argues the whole case on pixel count and never notices
that it also bought back the frame's dynamic range.


---

## R2-976 — I WAS WRONG IN F4, and the correction is favourable to the candidate

I pre-registered that *"the gesture the client complained about is still in the
film, in full, and R2-943 does not touch a byte of it"*, on the strength of
R2-944's statement that every camera `world[]` and `speed` is unchanged. I then
measured it instead of quoting it, and **half of that sentence is false.**

### What is true: the camera's POSITION path through the beat is identical

Measured frame by frame, `work/r2941/camrig_R2943_path.json` against
`render/film17_path.json` (the shipped film's own path):

| | |
|---|---:|
| beat 6, worst camera position delta A vs shipped | **7.150e-03 m** at f2733 |
| beat 6, worst camera position delta A vs B | **0.000e+00 m**, all 264 frames |
| beat 6, worst lens delta A vs B | **0.000e+00 mm**, all 264 frames |
| beat 6, worst aim delta A vs B | 18.3806 deg at f2795 |

So the camera still climbs 27.5 → 140.0 m and still travels 279 m away from the
line. **A and B differ in aim and in nothing else**, exactly as R2-944 claims,
and I confirm it independently.

**Incidental finding, not this task's:** beats 1-5 are **not** identical to the
shipped film — worst camera position delta **14.710 m at f604**, with rotation
differences up to 179 deg around f602. That is the R2-731..760 beat-1/2 camera
move that R2-951 already identified as uncommitted in the tree, and it is why
R2-853 verified against `world/camera_rig_path.json` rather than against the
shipped film's path. It is not caused by the lap-down. It does mean **the film
that would be rendered from this tree is not the shipped film outside beat 6**,
which anyone comparing arms needs to know.

### What is false: the lens gesture is materially different, and in the right direction

"We just zoom out" is a statement about focal length, and focal length is exactly
what R2-853 changed. Horizontal field of view across the closing beat:

| | widest | reached at | spent widening | spent tightening | closes to |
|---|---:|---:|---:|---:|---:|
| **shipped** | **87.7 deg** | **f2858** | **143 frames = 6.0 s** | 120 frames = 5.0 s | 27.3 deg |
| **candidate (A and B)** | **81.2 deg** | **f2763** | **48 frames = 2.0 s** | **215 frames = 9.0 s** | **15.8 deg** |

**The shipped ending is predominantly a widening: it opens continuously for six
seconds and reaches 87.7 deg.** The candidate opens for two seconds to 81.2 deg
and then tightens for nine. The gesture is not merely reduced, it is **inverted** —
the shipped closing beat is a pull-out, the candidate's is a push-in with a short
reveal at the front of it.

**That is a direct, literal answer to the client's sentence**, and neither R2-853
nor R2-943 states it in this form anywhere. R2-853 has the lens table but never
converts it to field of view or to time-spent-widening, which is the thing the
client actually described.

**Credit where it belongs:** this improvement is entirely R2-853's, the camera
candidate. A and B have identical lens curves. The lap-down does not contribute
to it. But it does mean my F4 falsifier is **not met**, and the "we just zoom
out" complaint is addressed at the level of the gesture, before any question
about what the gesture lands on.

### What survives of F4

The camera still *rises* 112 m and still *retreats* 279 m. A push-in on a
receding camera can still read as retreat if the net effect on the world is
expansion. Frame world width at the car peaks at 422 m at f2823 in the candidate.
**So F4 is not dismissed, it is narrowed:** the lens is no longer the problem, and
the question is whether the camera's physical climb still reads as pulling away.
Only the 264 frames answer that.


---

## R2-977 — F6 refined: the closing frames are not static, and the push eases out

I pre-registered that from about f2880 *"the only thing moving in the frame is
the lens"*. That is true. What I had not measured is **how much motion that is**,
and "only the lens" turns out to be a misleading way to say it.

Apparent radial displacement produced by the focal-length change alone, at 4K:

| frame | lens (mm) | scale change/frame | px/frame at r=1000 | **px/frame at the corner** |
|---:|---:|---:|---:|---:|
| f2870 | 33.67 | 1.749 % | 17.5 | **38.5** |
| f2886 | 45.29 | 1.674 % | 16.7 | 36.9 |
| f2902 | 54.41 | 0.428 % | 4.3 | 9.4 |
| f2918 | 60.21 | 1.451 % | 14.5 | 32.0 |
| f2934 | 79.61 | 1.868 % | 18.7 | **41.2** |
| f2950 | 104.20 | 1.424 % | 14.2 | 31.4 |
| f2966 | 124.09 | 0.695 % | 6.9 | 15.3 |
| **f2974** | **129.19** | **0.245 %** | **2.5** | **5.4** |

So through the "dead" phase the frame is changing by **15-41 px per frame at its
edges** — an order of magnitude more than the 1.83 px/frame of car-versus-ground
motion that I used to call the phase motionless. The image is being magnified
2.36× between f2906 and f2978, and 1.57× after the car has stopped.

**And the push decelerates into the last frame:** 1.42 %/frame at f2950,
0.695 % at f2966, **0.245 % at f2974**. The zoom eases out to nearly nothing
exactly as the film ends.

**That changes the shape of the ending as designed.** The car comes to rest at
f2936 and the lens comes to rest at f2978: *both* the subject and the camera
settle, the subject first and the camera second. That is a deliberate and
recognisable ending gesture, not an oversight, and R2-949 does not claim it —
it apologises for the phase instead.

**F6 is therefore narrowed, not withdrawn.** The phase is not dead. The open
question is a different and harder one: **does magnification-only motion read as
the film still being alive, or as a zoom into a photograph?** R2-852's charge was
specifically that a lens push on a locked-off camera reads as the latter. The
difference now claimed is that there is a subject at the centre of it and that
the subject stopped on purpose. That is exactly the thing a metric cannot settle,
and my 98-frame figure was measuring the wrong quantity to settle it with.

For scale, the shipped ending's push is **stronger** through the same window —
44-54 px/frame at the corners at f2870-2886 against the candidate's 37-43 — so
"a lens push on a static camera" does not distinguish the two arms at all. Both
have one. Only what is at the centre of it differs.


---

## R2-978 — the occlusion question, answered analytically without the raycast

R2-950 item 5 left this open — *"no ray-cast was run on the new resting position
… nothing is expected, but nothing was proved."* The raycast that was to prove it
(`r2851ab`, job `e30af0d64dfd`) has been wedged on broker 8761 in an
`ExecMemoryShort` retry loop for over 110 minutes and may not land at all. It
does not need to.

**MEASURED** from `world/build_barriers.py`'s own declared constants and the
built camera path:

```
camera            [594.19, 16.05, 140.00]      car at rest  [502.90, 315.40, 0.34]
camera offset     288.0 m to the side of the pit straight, 122.5 m along it
catch fence line  8.00 m (half of the 16.0 m pit straight) + 6.76 m outside
                  the surface  =  14.76 m from the centreline
fence post top    FENCE_POST_H 6.00 - FENCE_EMBED 1.20  =  4.80 m
```

The sightline from the camera to the stopped car crosses the fence line at
**0.9488 of the way to the car**, at a height of **7.50 m**, at track s ≈ 220 m.

| | |
|---|---:|
| sightline height at the fence line | **7.50 m** |
| fence post height | **4.80 m** |
| **clearance** | **2.70 m** |

**The sightline clears the catch fence posts by 2.70 m.** And the fence *weave*
is a fade-out card — `FENCE_FADE_NEAR 45.0`, `FENCE_FADE_FAR 190.0` — while the
fence line is **325 m** from the camera, so the mesh is fully faded and only the
posts are solid geometry at all.

The crossing is at track s ≈ 220 m, and `build_architecture`'s pit building spans
s −245 to +75, so there is no building at the crossing either.

**Nothing occludes the car at rest.** This is R2-950's fifth pre-registered
failure mode discharged, on the geometry, without spending the render. The 264
frames confirm it directly when they land, but the answer does not depend on them.


---

## R2-979 — the car is nailed to the exact centre of the frame for all 264 frames, and nobody has called that a composition

**MEASURED** by projecting the car through the built path with the actual
quaternions, all 264 frames:

| | |
|---|---:|
| car screen **x** | **1919.9 to 1920.1** of 3840 — a range of **0.2 px** |
| car screen **y** | 1086.6 to 1109.5 of 2160 — a range of **22.9 px** |

R2-945 reports this as a success — *"`|ndc| = 0.000` is not a rounding of
something small: the car is on the frame's centre line to better than a pixel for
the entire beat"* — and as a *geometric* claim it is impeccable. As a statement
about a picture it is a warning.

**The subject sits at the dead geometric centre of the frame, to a fifth of a
pixel, for eleven continuous seconds, while a symmetric radial zoom magnifies
everything about that same point.** There is no lead room, no drift, no
thirds, no offset of any kind. Every line of the composition converges on the
exact centre and stays there.

That is the framing of a tracking reticle. It is what makes the car trivially
*findable* — which is the problem R2-862 was solving — and it is also what makes
the frame compositionally inert, because nothing in it is ever allowed to sit
anywhere interesting.

**And it contradicts a constraint the staging file records as binding.** R2-949
item 3 dismisses R2-856's proposal of *"~85 mm with the car in the lower third"*
on the grounds that it *"is not available at this camera position"*. That is true
of the **lens** half of the proposal — the horizon genuinely cannot be recovered
at a 24.10 deg depression. It is **not** true of the framing half. Putting the
car in the lower third is a property of where the aim points, not of where the
camera is, and an aim offset costs nothing geometrically: the aim gate's beat-6
bound is 26.0 deg and the beat is currently using **0.029 deg** of it. There are
**26 degrees of unused aim budget** and the car is being held at the centre to a
fifth of a pixel.

**I am not proposing the change** — I am the adjudicator, not the builder, and
whether it improves the ending is exactly the kind of question that has to be
looked at rather than argued. I am recording that the option was declared
unavailable when it is available, and that the reason nobody has tried it is that
the aim gate rewards centring and no gate anywhere in this film measures
composition.


---

## R2-980 — every mechanical cue that the car is braking is below the resolution of the picture

R2-943 and R2-947 build the lap-down's physical detail carefully and verify it
hard: brake dive using `build_telemetry.py`'s own closed form, clipping at the
declared 1.6 deg ceiling; rolling contact exact to **1.350e-12 m** over all 2,977
intervals; zero backwards wheel steps; `body_roll` and `ground_distance` rewritten
so the tyres do not spin under a stopped car. R2-947's own summary calls the
brake dive *"the telemetry's own declared ceiling, i.e. the term clips."*

**MEASURED** — what any of it is worth in pixels, on a 3.600 m wheelbase against
the built path:

| frame | decel m/s² | dive deg | car px | **nose drop px** | wheel dia px |
|---:|---:|---:|---:|---:|---:|
| f2715 | 0.68 | 0.037 | 115.7 | **0.1** | 21.1 |
| **f2730** | **28.56** | **1.523** | 82.6 | **2.0** | 14.9 |
| f2760 | 16.37 | 0.873 | 57.0 | 0.7 | 9.3 |
| f2820 | 9.25 | 0.493 | 45.7 | 0.3 | 6.5 |
| f2880 | 2.14 | 0.114 | 69.0 | 0.1 | 9.3 |
| f2925 | 1.23 | 0.065 | 111.7 | 0.1 | 15.1 |
| f2940 | 0.00 | 0.000 | 146.9 | **0.0** | 19.9 |
| f2978 | 0.00 | 0.000 | 215.2 | **0.0** | 29.1 |

**The brake dive reaches a maximum of 2.0 pixels of nose movement, at f2730, on a
car 82.6 px long.** Everywhere else it is at or below 1.1 px. And the two
quantities are anti-correlated by construction: **the dive is largest when the
car is smallest, and is exactly zero for the whole of the period in which the car
is large enough to see it.** The car is at 147-215 px only after it has stopped,
by which time there is nothing to show.

The wheels are the same story. Wheel diameter runs **6.5 to 29 px** across the
beat. At f2936, where the spin-down was carefully made to reach exactly zero in
finite time, the wheels are **20 px across** with motion-blurred tyres — a 20 px
disc's rotation is not resolvable, so "the wheels stop" is an event that cannot
be seen either.

> The engineering is correct, thorough, and invisible. Not *subtle* — **invisible**:
> 2 px at peak, on a frame that is 3,840 px wide.

**Why this matters to the verdict and not just to the record.** R2-950's first
pre-registered failure mode is *"the car reads as broken down, not as a
lap-down"*, and its stated defence is that *"the audience watches it brake
continuously for four seconds first, which a failure does not do."* That defence
depends on the braking being **visible**. This measurement says the braking has
exactly one visible signature — **the rate at which the background streams past
the car** — and R2-943's own table shows that rate collapsing 18× (109.70 → 5.98
px/frame) inside the first 105 frames.

So the entire read of "a driver bringing a car in" versus "a car that has stopped"
rests on a single cue, in the first 4.4 s of an 11 s beat, after which nothing
about the car itself tells the audience anything. **That is a much narrower base
than R2-950 assumes it is standing on**, and it is why the 264 frames, and not
the last still, have to decide item 1.


---

## R2-981 — WHAT I HAVE NOT BEEN ABLE TO LOOK AT, stated plainly

At the time of writing, **the R2-943 frames do not exist.** `watch/r2943_4k/` and
`watch/r2943b6_frames/` are empty. Everything above this line is measured either
on the built path, on the beat sheet, or on the frames of *other* arms that were
already rendered. **None of it is a verdict, and I will not turn it into one.**

The render did not fail to finish; it failed to start, twice, for two unrelated
middleware reasons:

1. **On broker 8761** the re-key exec (`65507c9a0431`) never executed a line. It
   sat in an unbounded `ExecMemoryShort` refund-and-retry loop — the exec
   precheck demands `scene_bytes × 5.5 = 43.9 GB` free, the render worker holds
   the 8 GB `film17_breach` resident, and two copies do not fit on the box. 29
   requeues. It also carries `timeout_s: 5400` against a worker limit of 3600, so
   it was going to fail on submission even if the memory had cleared.
2. **On broker 8760**, where I resubmitted it with the timeout corrected and
   where it was admitted immediately, it failed terminally after 3 attempts:
   the exec stager pushes the 7.98 GB scene successfully in ~128 s and the exec
   precheck then refuses it with *"scene 493845696f4899f6 is not completely
   staged on this instance (no .complete marker)"*. Three full re-pushes, no
   execution.

**Also recorded because it is not mine and will not fix itself:** the object-ID
raycast `e30af0d64dfd` (`r2851ab`), which R2-950 item 5 is waiting on, is wedged
in the *same* `ExecMemoryShort` loop on 8761 and has been for over 110 minutes.
It is not going to land on its own. R2-978 above answers its question
analytically, so the ending does not depend on it, but whoever owns it should
know.

### The validity check that must be applied to the first still that lands

Adopted from the builder, and correct: the animation jobs must render the
**re-keyed** scene, and the un-re-keyed `render/film17_breach.blend` is the path
of least resistance on a box that already has it loaded. A wrong-scene render
would come back non-blank, correct resolution and worthless. At f2978 the two are
trivially distinguishable:

* **re-keyed (valid):** 130 mm, a stretch of pit straight, one car at the exact
  centre, no buildings, no horizon, no sky.
* **original (invalid):** 74 mm, pit building, grandstand, paddock, shipping
  containers, the breached showroom mid-frame, **no car anywhere** — pixel-wise
  the same content as `out2/seq/r2851_4k_A_shipped/..._002978.png`, which can be
  diffed against directly.

**If the frame that arrives is the second one, it is not evidence and I will say
so rather than judge it.**


---

## R2-982 — PROVENANCE AND THE BUILD CONFOUND, both checked before judging anything

### The frames are from the re-keyed scene — verified three ways, one of them mine

`out/exec/bd0345da6cb3/rekey_R2943.log` ends `>> STAGE RESULT:
FILM_SCENE_REKEYED_R2943`, and I read it rather than take a summary of it:

```
BEFORE: world SKY_World, slab [SKY_AirBoundary, SKY_AirColumn], 3840x2160,
        AgX, look None, exposure -3.628, camera ONER, objects 35304
AFTER : identical on every field
6_ending  worst 0.03 deg at frame 2758 (bound 26.0)  max subject range 342.5 m
```

The **`max subject range 342.5 m`** is the tell: the un-re-keyed film reports
1000.0 m and aims at the facade. The world was swapped by the rig build and
explicitly restored, so the frames are lit by the film's own sky and not by
`R2_ProceduralSky`. The log also contains **two** `Saved as "film17_R2943.blend"`
lines, so the existence of an 8 GB output proves nothing — only the final STAGE
RESULT does. The render jobs record scene digest `ec95e539bb6a04d4` (the re-keyed
blend) rather than `493845696f4899f6` (the original), and the delivered f2978 is
a 130 mm frame, not the original's 74 mm.

There is also a `>> STAGE RESULT: CAMERA_RIG_FAIL` earlier in the log — beat
`1_assembly` at f431, the pre-existing R2-861 defect. Beats 2-6 PASS. It is not
in my 264 frames and it is not caused by this change.

### THE f2715 CONTROL — the build confound is real in principle and REFUTED in fact

The comparison arms (`r2851b6`, `r2851_4k_B_candidate`) render from
`film16_R2851` (35,283 objects, built 2026-08-04); the lap-down renders from
`film17` (35,304 objects, built 2026-08-07). The 21-object difference is the
showroom-ceiling library, which proves `film17` carries at least one item from the
62-hour gap. `docs/NEXT-REBUILD.md` lists in that same gap a **car paint v5**
change worth **albedo 0.0121 → 0.0372 and three-quarter diffuse 7.32 → 19.96 %** —
a 2.7× change, at exactly the viewing angle of the closing frame. If only one
build carried it, a car that reads better at 343 m might be reading better
because it is a brighter object.

**f2715 is the exact control**, and it is free: the driver lifts *between* f2714
and f2715, so at f2715 the car has lost 35 microns and the camera position,
rotation and lens are all `0.000e+00` different between the arms. Any pixel
difference there is the film build.

| | |
|---|---:|
| whole frame, mean \|RGB diff\| | **0.002194** |
| whole frame, px changed > 8/255 | **0.083 %** |
| whole frame, mean luminance | **+0.01 %** |
| **car region** (60×34 px at 720p), luminance | **+1.20 %** |
| background tarmac control patch | **−0.27 %** |
| **car-specific difference** | **≈ +1.5 percentage points** |
| car internal contrast | A 0.2122 vs B 0.2165 |

**A 2.7× paint change would be +170 %. The measured car-specific difference is
+1.5 %.** Side by side at 5× the two cars are indistinguishable — same blue, same
brightness, same shading, same tyres.

**So the car paint v5 change is either in both builds or in neither, and the A/B
is clean.** The confound was correctly raised and is now closed by measurement
rather than by assumption. Every comparison below stands as a comparison about
the ending.

---

## R2-983 — WATCHED AT 4K, 1:1. The car is a subject. F1, F2, F3 and F12 all clear.

### The closing frame, f2978

At true 1:1, in a 400×300 crop, the car resolves into **parts**: the rear wing
as a distinct element, the front wing, **all four wheels separated from the body**
with orange rims, the cockpit, the halo, the driver's helmet, the engine cover,
the sidepod waist and the floor edge. At 3× the livery graphics are legible.

**F2's falsifier — "a single elongated blob with no internal edge, in particular
if the rear wing cannot be seen as separate from the body" — is not met, and is
not close to being met.**

Measured on the rendered frame with my R2-974 instrument, background boxes
hand-placed on clean pit-straight tarmac:

| | car | road |
|---|---:|---:|
| lum mean | 0.3062 | 0.2908 |
| p5 / p95 | 0.2145 / 0.5089 | 0.2574 / 0.3145 |
| **internal contrast** | **0.2944** | **0.0571** |
| **RATIO** | **5.16×** | — |
| luminance break | **+5.3 %** | |
| b−r break | **+0.0127** | |

**Pre-registered in R2-974: ratio ≥3× reads, ≤1.5× fails. Measured 5.16×.**
Against the same instrument, the frame R2-862 called a smudge measures **0.90×**
and the frame that unambiguously works measures 7.50×. The closing frame sits
firmly in the reading regime.

**And it confirms R2-974's mechanism rather than R2-862's.** The luminance break
is +5.3 % and the colour break +0.0127 — both small, both roughly what they were
in the failing arm. What changed is **internal contrast: 0.2944 against a road at
0.0571.** The car's minimum luminance is **0.1465** against the road's 0.2327, so
**the car supplies the local black point of its own neighbourhood** — the tyres
and the shadow are the darkest things in the frame's centre.

**F8's prediction was right and it is the shadow that does much of the work.** The
low 12.47 deg sun throws a large, hard-edged cast shadow up-screen and to the
left, with the wing shapes readable in it. It roughly doubles the car's visual
footprint and welds it to the road surface. I registered before looking that I
expected the shadow rather than the car's 215 px to decide F2; that is what
happened. The flat frontal light I worried about does not flatten the car,
because the shadow supplies the modelling the lighting does not.

**F1's falsifier is not met either.** I predicted a 215.2 px projected long axis
against R2-945's quoted 230.7. The measured silhouette bounding box is
**237 × 74 px** — slightly *larger* than my figure, because the wings span wider
than the body axis I projected. My correction to the arithmetic stands (R2-945's
number ignores 66.95 deg of yaw) but it was a correction in the wrong direction
for the picture, and the picture is what matters.

### F3 — the tarmac risk I registered is refuted

I flagged dark-car-on-grey-asphalt as an uncosted new risk. It is not a risk:
this car is blue on neutral grey, and tarmac is a **better** ground for it than
the gravel run-off the B arm parked it on, because tarmac is smooth and
low-variance and lets the car win the internal-contrast comparison 5.16×.

### The car reads far earlier and far smaller than any ladder predicted

| frame | projected px | at 1:1 it reads as |
|---:|---:|---|
| **f2811** | **45.7** | **a racing car** — blue body, wheels, front wing, cast shadow |
| f2760 | 57.0 | a racing car, clearly, with motion blur |
| f2937 | 146.9 | fully resolved: wings, wheels, helmet, shadow |
| f2978 | 215.2 (237 measured) | fully resolved, livery legible at 3× |

**At f2811 the car is at its smallest in the entire beat — 45.7 px — and it still
reads as a racing car.** That is a quarter of R2-862's 176.7 px "a car" rung.
**R2-862's ladder is wrong by roughly 4× at the bottom end**, because it was
calibrated on a car at 1 km through haze that had cost the frame half its
dynamic range, and it has been quoted ever since as though it were a property of
pixel counts. It is not. It is a property of pixel counts **and** haze **and**
what the car is standing on.

**F7 is therefore substantially weakened.** I registered that the beat's middle
would be a dot. It is small, but it is never a dot — there is a legible car in
every frame I have looked at, including the trough.

### F12 — the grade is intact, and better than intact

| f2978 | lum p0.1 | p50 | p95 | mean sat |
|---|---:|---:|---:|---:|
| **A lap-down** | **0.1750** | 0.3083 | 0.5441 | **0.3325** |
| B candidate | 0.2913 | 0.4391 | 0.5648 | 0.2369 |
| shipped | 0.1752 | 0.3651 | 0.7049 | 0.2046 |

**The black floor is 0.1750 against the shipped film's 0.1752** — the lap-down
recovers the shipped closing frame's black point exactly, while the arm it
replaces sits at 0.2913 because 1 km of haze has lifted it. **Saturation is
0.3325 against the shipped 0.2046 — 62 % higher.** Nothing is crushed and nothing
is lifted; the delivery contract is asserted identical before and after the
re-key. R2-975's prediction that closing at 343 m buys back the frame's dynamic
range is confirmed on the delivered frames.


---

## R2-984 — R2-943b's central prediction about its own closing frame is FALSE. There is a grandstand full of people in it.

R2-943b states, as a determined result rather than a choice:

> "the closing frame is *determined*: a 95 m-wide stretch of the pit straight past
>  the pit exit, with the car at its centre, and **no architecture and no
>  start/finish line in it**. That is not a choice I made and it is not one
>  available to be made differently."

and its table records *"Only s=100 puts any architecture in the closing frame,
and s=100 is not reachable."*

**I opened the frame. The bottom-left corner of f2978 contains a grandstand with
an individuated crowd in it** — dozens of separate seated spectators with hats
and jackets, some standing, a banner, handrails, the stand's concrete flank and
its access deck. The rest of the frame carries barrier walls with advertising
hoardings on both sides of the straight, catch fencing with posts, red-and-white
kerbing along the whole outside of the corner, a gravel run-off, marshal posts,
and the T1 entry with its kerbs upper-right.

**The closing frame is not bare and it is not architecture-free. It is a
well-dressed piece of racing circuit with a crowd watching.**

### Why the prediction failed, which matters more than that it did

R2-943b projected exactly one thing: `build_architecture.py`'s declared
**pit-building box** `PB_X0/PB_X1/PB_Y0/PB_Y1`. Having found that box outside the
frustum it concluded "no architecture". But the pit building is not the only
built thing on a circuit, and the frame is full of the others — grandstand,
barriers, hoardings, fences, kerbs, run-off, crowd — none of which is in that
box.

> This is the same error as R2-946, in the same file, made twice within one
> entry-pair: **gating on one declared feature and reporting the result as a
> property of the whole frame.** R2-946 evaluated two of the meadow scatter's
> five terms and reported "0.0 % bare mesh"; R2-943b projected one of the world's
> many built objects and reported "no architecture". Both were then corrected by
> the cheapest possible act, which is opening the picture.

### What it does to my F9, and to R2-950's first failure mode

I pre-registered F9 — *"arrival needs a destination and R2-943b proves there is
none in frame … the image is a car stopped in a field"*. **F9 is refuted.** The
frame contains the strongest possible destination signal: **a crowd, watching.**
A car at rest on a racing surface in front of a populated grandstand, inside kerbs
and barriers and catch fencing, does not read as a breakdown in a field. It reads
as a car that has finished.

That also removes the load R2-950's item 1 was carrying. Its defence of "lap-down
rather than retirement" rested entirely on the audience having watched four
seconds of braking — a defence I showed in R2-980 is much weaker than it looks,
because every mechanical cue of braking is below 2 px. It does not need that
defence. **The context is in the frame.**

I record with some irony that this entry is the strongest single piece of
evidence *for* the ending in this file, and it is the correction of a claim the
builder made against itself.


---

## R2-985 — the f2714/2715 seam, RE-MEASURED ON THE RENDERED LAP-DOWN FRAMES

R2-944 argued the seam was safe without measuring pixels — *"nothing that feeds
it moved"*. That is a good argument and I did not accept it, because the seam is
the one place in this film where an argument is not the standard.

Method and instrument as validated in R2-973 (reproduces R2-711's published
−1.33 % on the shipped film to two decimal places; cross-spec splice error
1e-6).

```
d[2712->2713] = 0.056714
d[2713->2714] = 0.054425
d[2714->2715] = 0.052128   <- the seam
d[2715->2716] = 0.051289
d[2716->2717] = 0.050450
```

| arm | deviation from interpolation | ratio to local median |
|---|---:|---:|
| shipped | **−1.33 %** | 0.947 |
| B candidate (camera only) | **−1.33 %** | 0.948 |
| **A lap-down** | **−1.38 %** | **0.959** |

**−1.38 % against −1.33 %, a difference of five hundredths of a percentage
point, on a criterion of 4 %.** The one-shot law holds at this seam in pixels,
on the arm that actually changes the car, and not merely by inheritance.

The series diverges from the shipped one first at `d[2718->2719]` (0.053287
against 0.053605) — which is the deceleration beginning to bite three frames
after the lift, exactly where R2-943's model says it should, and nowhere near
the boundary.

**All four re-measurements I was asked for are now complete:**

| | claimed | measured | verdict |
|---|---|---|---|
| runtime | 2,978 frames / 124.0833 s | 2,978 / 124.0833 | **holds** |
| f2714/2715 seam | 1.33 % from interpolation | **1.38 %**, on frames | **holds** |
| aim gate, beat 6 | 0.029 deg at f2758 vs 26.0 | 0.02902 deg at f2758 | **holds exactly** |
| the grade | AgX / None / −3.628, no crush, no lift | blacks 0.1750 vs shipped 0.1752; sat +62 % | **holds, and improves** |


---

## R2-986 — WATCHED. All 264 frames at 720p and four stills at 4K, 1:1.

### THE VERDICT

**The film now ends on a subject. It does not end on an arrival.**

The last frame is an image of a car — not a tighter crop of the same aerial with
a bigger dot in it. That question, the one I was sent to answer, is answered
**yes**, and not marginally. R2-862's finding has been fixed.

What has *not* been delivered is the thing R2-943 was built to deliver and named
itself after. **The car's arrival at rest is invisible.** The film's last gesture
is still a zoom, and the event at the centre of it cannot be seen to happen.

Both halves of that are load-bearing and I will not collapse them into a single
grade.

### Why the first half is a yes

At 1:1 the closing car resolves into parts — rear wing, front wing, four
separated wheels, cockpit, halo, helmet, engine cover, floor edge — and carries
**5.16×** the internal contrast of the tarmac it stands on, against **0.90×** for
the arm R2-862 called a smudge and **7.50×** for a frame that is unarguably a
subject. It supplies the local black point of its own neighbourhood. A large,
hard cast shadow from the 12.47 deg sun welds it to the road. The frame around it
is a dressed racing circuit — kerbs, barriers, hoardings, catch fencing, run-off
— **with a grandstand full of individuated spectators in it** (R2-984).

A car at rest on the racing surface, in front of a crowd, inside the furniture of
a circuit, does not read as a breakdown. It reads as a car that has finished. The
worry that framed this whole review — that the picture would be a car stopped in
an empty field — is simply not what is on screen.

**And the car reads far earlier and far smaller than anyone predicted.** At f2811,
its smallest point in the entire beat at **45.7 px**, it is still legibly a
racing car. R2-862's ladder — 176.7 px for "a car" — is wrong by roughly 4× at
the bottom, because it was calibrated at 1 km through haze that had already cost
the frame half its dynamic range. The car is legible in every one of the 264
frames. It is never a dot.

### Why the second half is a no, and this is the finding

The whole architecture of R2-943 is that the film ends **where the lap began,
with the car arriving.** I measured whether the arrival happens on screen.

Per-frame difference in a 90×60 box locked to the car, where the radial zoom
contributes nothing:

| phase | | car-box d |
|---|---|---:|
| f2715-2760 | hard braking, 89.8 → 46 m/s | 0.01614 |
| f2761-2820 | braking, 46 → 17 m/s | 0.01359 |
| f2821-2880 | crawl, 17 → 3.4 m/s | 0.00875 |
| f2881-2935 | creep, 3.4 → 0 | 0.00722 |
| **f2936-2978** | **at rest** | **0.00583** |

A smooth monotone decay with **no event anywhere in it.** Around the stop:

```
f2926..f2946:  .0072 .0069 .0068 .0070 .0067 .0065 .0065 .0063 .0062 .0069
               .0064 .0063 .0065 .0063 .0058 .0062 .0060 .0058 .0063 .0062 .0059
                               ^ f2936, the car reaches rest
window sd = 0.00038      |d(2936) - median| = 0.00002
```

**The frame at which the film's subject comes to rest differs from its neighbours
by five per cent of one standard deviation.** My F6 falsifier was *"if I cannot
say within ~10 frames when the car stopped"*. I cannot say within a hundred. I
checked it visually as well, stepping f2916-2976: the car does one thing across
those 61 frames — **it gets bigger.** Nothing marks the stop.

The car does not arrive. It asymptotes. And the reason is structural rather than
a tuning error:

* **Every mechanical cue of braking is below 2 px** (R2-980). Brake dive peaks at
  **2.0 px of nose movement** at f2730 and is *exactly zero* for the whole period
  in which the car is finally big enough to see. The wheels are 6.5-29 px, so
  their spin-down is unresolvable. R2-947's rolling contact is exact to 1.35e-12 m
  and invisible.
* **The only visible cue is the background streaming past**, and R2-943's own
  profile collapses that 18× inside the first 105 frames.
* **So the deceleration is over, as a visible event, by about f2820** — 6.6 s
  before the film ends. My F7 stands in that form: the arrival happens in the
  middle of the beat, and the last 2.6 s is magnification.

The lens push is not *dead* — it moves the frame edges 15-41 px/frame and eases
out to 0.245 %/frame at f2974 (R2-977), and the whole-frame difference actually
**rises** through f2915-2945 as the push accelerates. That is the awkward shape:
**the camera's gesture peaks exactly as the subject's gesture ends.** R2-852's
charge — *"a lens push on a locked-off frame is what a still photograph being
zoomed looks like"* — is not fully answered. It is answered only to the extent
that there is now something worth zooming into.

### The client's sentence

*"We just zoom out so you see all the patches in the land."* Watched end to end,
the beat reads as **rise → reveal → converge**, not as retreat. My F4 was wrong
and R2-976 records why: the shipped ending widens for **6.0 s to 87.7 deg**; this
one widens for **2.0 s to 81.2 deg** and then tightens for **9.0 s to 15.8 deg**.
The gesture is inverted. That is a real answer to what the client said, and the
credit belongs to R2-853, not to the lap-down.

**The patches, however, are still there.** Through f2763-2901 the flat olive and
khaki fields with their straight tonal seams are visible, most obviously in the
lower-right foreground and mid-left. They are no longer the *subject* of the
frame — the circuit is — but F5 is only partly cleared, and R2-854's Voronoi
partition is untouched and still owns that defect.

### What is worse than the arm it replaces

**No horizon and no sky for the last 6.3 seconds.** The horizon leaves frame at
**f2826** in this arm, against **f2894** in the camera-only candidate and
**f2920** in the shipped film — nearly three times as long a stretch of pure
ground as the film the client rejected. The closing optical axis is **24.0 deg
below horizontal**, the steepest of the three. R2-949 item 3 registered this
honestly but did not state the comparison: **on this axis the lap-down is the
worst of the three arms**, and it is the reason the closing frames read as a plan
of a place rather than a view of one.

### The composition nobody has looked at

The car is pinned to **x = 1919.9-1920.1 px of 3840** — a range of 0.2 px — for
all 264 frames, with 22.9 px of vertical drift (R2-979). Every line converges on
the exact centre and stays there while a symmetric zoom magnifies about that same
point. The aim gate's beat-6 bound is 26.0 deg and the beat uses **0.029** of it.
R2-949 dismissed *"the car in the lower third"* as unavailable at this camera
position; the lens half of that is true, the framing half is not. **There are 26
degrees of unused aim budget and no gate in this film measures composition.**

### Verdict, stated so it can be acted on

1. **The ending is fixed in the respect it was broken.** R2-862's defect —
   a closing frame with no subject in it — is gone. This is strictly and
   substantially better than both arms on disk, and the improvement is real
   rather than an artefact of a different film build (R2-982).
2. **It is not fixed in the respect R2-943 claimed.** The film ends *on* the car;
   it does not end *on the car arriving*. The arrival is real in the world,
   correct in the physics, and invisible in the picture.
3. **If one more change is made to this beat, it should be the one that makes the
   stop visible**, not another lens or another braking profile. R2-950's own
   fallback — end at ~208 px still rolling — would trade a subject that has
   stopped invisibly for a subject that is still moving, and on this evidence
   that is the better trade, because motion is the only cue that survives at this
   scale. Second best is the unused aim budget: 26 degrees of it, and a car
   currently nailed to the centre pixel.
4. **The horizon is now the strongest remaining argument against the hold's
   140 m altitude**, and it belongs to whoever owns that key.

**Nothing here is a reason not to ship this over what is on disk.** It is a
reason not to call the ending finished.

