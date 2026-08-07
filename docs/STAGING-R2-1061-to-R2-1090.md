# STAGING R2-1061 … R2-1090 — the tone-curve convergence, diagnosed

Three investigations landed on the tone curve independently. **They are not one
defect and they are not three coincidences. They are one instrument defect, one
correct physical behaviour, and one already-compensated constant.**

Nothing in this block changes a shipped value. No blend was written, no
constant moved, no grade touched. `DEFECT-LOG-R2.md` untouched.

---

## R2-1061 — R2-1042's frame was rendered in a rig whose sun is 139.6° from the film's, and that is 100 % of the finding

`world/surface_test_filmpose.blend` — the rig every number in R2-1036 and
R2-1042 was measured on — was read with `tools/r21061_probe_testrig.py` and
`tools/r21061_probe_mat.py`. It does not render the film's light:

| | the rig | the film / the contract | worth |
|---|---|---|---|
| **sun lamp bearing** | `TEST_Sun` at **(0.00000, 0.97641, 0.21594)** | `C.SUN_DIR` **(0.51785, −0.82777, 0.21594)** | **139.61°** |
| sun elevation, energy, colour | 12.471°, 115.754, (1.0, .7163, .3871) | identical | 0 |
| world | `TEST_Sky`, **one bare `ShaderNodeTexSky`** | `build_sky.build_world()` + aerosol mottle + **three cloud decks** | +0.399 stops on the sky term |
| atmosphere | **absent** — no `SKY_AirColumn`, no `SKY_AirBoundary` | present; 28.30 → 39.01 W/m² | +0.463 stops, **and all aerial perspective** |
| ground | `TEST_Ground`, albedo (0.048, 0.052, 0.028) | `build_terrain` | — |
| **view exposure** | **−3.048** | **−3.628** | **0.580 stops** |

`−3.048` is `C.REFERENCE_EXPOSURE_EXTERIOR`, the value **R2-071 refuted and
`world/film_exposure.py` documents as over-exposing by 0.586 stops.** The rig
that condemned f2225 is graded at the number the project has already rejected.

### The elevation is right and the bearing is not, and that is why f2225 was the odd frame out

At f2225 the camera looks along (−0.2432, 0.9692, −0.0381):

* against the **film's** sun that is **159.47°** — looking almost directly *away*
  from it;
* against the **rig's** sun it is **20.26°** — looking almost directly *into* it,
  with the sun just outside a 24.6° horizontal field.

The rig turned the one away-from-sun frame in the sample into an into-sun frame.
**f2225 was not the hard frame; it was the frame whose camera happened to point
at where the rig had put its sun.**

### Measured on the same 4K crop, same camera, same frame

`b5verdict_4k_002225.png` (film17_breach, −3.628, 512 spp) against
`render/r21031/after_f2225.png` (the rig), crop (2300, 1200)–(3100, 1600), an
open stretch of racing surface in both:

| | display mean | scene-linear |
|---|---:|---:|
| **the film** | **0.3427** | **1.2525** |
| **the rig** | **0.8161** | 11.9001 |

**The rig renders that surface +3.248 stops brighter than the film does.**

Decomposed, the rig's two *level* errors nearly cancel — exposure **−0.580**
stops against light level **−0.609** stops (25.579 W/m² of sun-plus-bare-sky
against the film's 39.011) — for a net **−0.029 stops**. So:

> **+3.277 stops of the rig's error is not level at all.**

And the film's own into-sun glare excursion, measured on delivered frames — clean
road at f2225 (0.3427 → 1.2525) against glared road at f2360 (0.7692 → 12.2077)
— is **+3.285 stops**. The two agree to **0.008 stops**.

**The rig's f2225 error IS the film's sun glare, delivered at the wrong frame.**
It is one quantity measured two ways, and it identifies the cause without
appealing to anything else.

### What survives of R2-1036 and what does not

* **The A/B survives.** Both arms were rendered in the same rig, so the
  before/after octave ratios are a fair comparison of the material with itself.
  Three frames moved; that stands.
* **Every absolute level in it is void** — 0.8617 display, "27× mid grey", the
  "55 % of the slope" table, and the conclusion that f2225 has no headroom.
* **"27× mid grey" was also an arithmetic slip.** Mid grey under this grade is
  scene-linear **2.2254**, not 1.0. Display 0.8617 is scene-linear 27.35, i.e.
  **12.3× mid grey, +3.62 stops** — and in the *delivered* grade that same
  radiance is +3.04 stops, not +4.75.
* **The lighting geometry of all four A/B frames is not the film's**, so which
  frame is grazing, which surface features catch light, and where the sheen
  falls are all rig properties. The contrast *ratios* are unaffected; the
  *choice of which frames are representative* is.

**R2-1042 is withdrawn as an exposure defect.** The agent's handling was
correct — it stated the result against itself rather than texturing around it —
and the rig it inherited is what was wrong.

---

## R2-1062 — the film's own AgX transfer, stated correctly, because R2-1036's version has been quoted twice

Read from `render/r2651/agx.json`, which is Blender's own colour management
measured on a known ramp at AgX / look None / **exposure −3.628**. `lin` is
**scene-linear before exposure**; the exposure is baked into `disp`.

| | |
|---|---|
| mid grey, scene-linear | **2.2254** ( = 0.18 / 2^−3.628 ) |
| mid grey, display | **0.4613** |
| **peak slope** | **0.1536 display/stop, at display 0.4712** — i.e. essentially *at* mid grey |
| slope 75 % of peak | display **0.6817** = +1.61 stops over mid grey |
| slope 60 % of peak | display **0.7739** = +2.50 stops |
| slope 50 % of peak | display **0.8125** = +2.95 stops |
| display saturates | **0.9330** |

The three shoulder thresholds above are what `tools/r21061_knee_sweep.py`
measures. **Level is not the complaint and must not be used as one** — a sky is
meant to be bright. The complaint is *slope*, and slope is what is measured.

`--selftest` is 4/4 with one arm that must fail: a frame **one** stop over mid
grey is required **not** to be called shoulder, because a threshold that fires on
everything bright explains nothing.

---

## R2-1063 — the sweep. 12.04 s of 124.1 s sits on the shoulder, and it is four arcs, not a diffuse condition

**Cost: $0.00.** 1 745 delivered frames at the film's own grade were already on
disk and nobody had measured them: `out2/seq/r2full` (film16_breach, f793–2978,
1 247 frames, 1280×720/64, `exposure: null` → the scene's −3.628),
`out2/seq/r2beat1_v2` (film17_breach, beat 1), `out2/seq/r2851b6` (beat 6).
Beats 2–6 of `film16_path` are **bit-identical** to `film17_path` (they differ
only over f2–753), so the sweep describes the shipping film.

Shoulder area **below the horizon**, per beat:

| beat | n | sh75 p50 / p90 / max | sh60 p50 / p90 / max | max clip |
|---|---:|---|---|---:|
| 1_assembly | 234 | 12.12 / 30.66 / 46.87 | 7.21 / 16.11 / 29.59 | 6.04 % |
| 2_launch | 72 | 21.00 / 42.23 / 45.25 | 8.91 / 36.81 / 40.39 | 1.75 % |
| 3_breach | 192 | 1.38 / 11.71 / 12.65 | 0.09 / 0.75 / 2.19 | 0.89 % |
| 4_transit | 134 | 0.43 / 1.61 / 4.34 | 0.02 / 0.58 / 1.47 | 0.15 % |
| **5_lap** | **585** | **0.40 / 12.93 / 69.11** | **0.02 / 1.47 / 40.25** | **20.87 %** |
| 6_ending | 264 | 3.86 / 5.53 / 5.84 | 0.06 / 0.13 / 0.83 | 0.003 % |

**The median lap frame has 0.40 % of its ground on the shoulder.** The condition
is a tail, and the tail is four contiguous arcs:

| arc | screen time | peak sh75 | peak clip | closest view-to-sun |
|---|---:|---:|---:|---:|
| f1376–f1436 | 2.54 s | 43.0 % | 10.6 % | **21.4°** |
| f1671–f1746 | 3.17 s | 38.4 % | 20.9 % | **12.1°** |
| f2185–f2235 | 2.12 s | 28.0 % | 0.00 % | 144.8° |
| f2285–f2385 | 4.21 s | **69.1 %** | 18.3 % | **15.8°** |
| **total** | **12.04 s of 124.1 s** | | | |

Restricted to the **bottom 40 % of the frame** — road, never sky — the arcs are
sharper and the clipping almost vanishes, which locates it:

| frame | sh75 | sh50 | clip | mean |
|---|---:|---:|---:|---:|
| f2340 | **94.99 %** | 4.59 % | 0.05 % | 0.7477 |
| f2360 | 87.19 % | **43.25 %** | **2.04 %** | 0.7692 |
| f1426 | 43.83 % | 8.01 % | 0.00 % | 0.6533 |
| f1686 | 43.12 % | 16.09 % | 0.02 % | 0.6119 |
| **f2225** | **0.00 %** | **0.00 %** | **0.00 %** | **0.3791** |
| f2000 / f2035 / f2160 / f2500 / f2700 | 0.00 % | 0.00 % | 0.00 % | 0.32 / 0.28 / 0.35 / 0.40 / 0.17 |

**The 10–21 % clip figures are the sun's own glow in the sky, not the road.**
Ground clip never exceeds 2.04 % anywhere in the film. A sun in shot clips; that
is not a defect and there is no exposure at which it does not.

**f2225 — the frame the whole question was opened on — is one of the cleanest
frames in the film.** Zero percent of its road is even past the 75 %-slope
point.

---

## R2-1064 — the bright road is the sun's specular sheen, and it is where geometry says it must be

`tools/r21061_glitter.py`, **no render**. For a flat road it computes the
**specular point** — the ground point whose mirror reflection of the view ray
reaches the sun — from `C.SUN_DIR` and the delivered camera path, projects it
into the frame, and compares it with the measured bright region's centroid.

| frame | view-to-sun | predicted specular point | measured bright centroid | miss |
|---|---:|---|---|---:|
| f1426 | 21.4° | (694.8, 446.1) | (739.4, 447.5) | **0.03 frame-widths** |
| f1391 | 27.1° | (662.6, 306.1) | (560.2, 362.9) | 0.09 |
| f1686 | 23.0° | (246.1, 615.1) | (286.4, 507.8) | 0.09 |
| f1421 | 26.9° | (1030.9, 450.5) | (900.5, 427.9) | 0.10 |
| f1691 | 21.0° | (291.1, 623.1) | (291.4, 478.0) | 0.11 |

**Negative control, and it fires.** f2225, f2000, f2035, f2160, f2185, f2190,
f2600, f2700 — every away-from-sun frame — put the specular point **behind the
camera**, and f2160 and f2700 have no bright region at all. The predictor does
not put a hot spot in every frame.

**The same test run on the rig's own misplaced sun explains the rig's frame.**
At f2225 with `TEST_Sun`'s bearing the specular point lands at pixel
(4119.7, 2743.2) — just off the bottom-right corner of the 3840×2160 frame — and
the rig's bright band is an elongated glitter path pointing exactly at it,
going to hard clip as it approaches. Two rigs, two suns, two predictions, both
hit.

**Across all 585 delivered lap frames**, `tools/r21061_sun_correlation.py`:

| view-axis to sun | n | sh75 below-horizon, p50 |
|---|---:|---:|
| 0–30° | 41 | **31.17 %** |
| 30–60° | 41 | 2.91 % |
| 60–90° | 48 | 0.84 % |
| 90–120° | 185 | **0.29 %** |
| 120–150° | 148 | 0.64 % |
| 150–180° | 122 | 0.03 % |

A **100×** swing in shoulder area, ordered by where the sun is.
Spearman ρ = **−0.447**.

> **Stated against myself: the negative control is not comfortable.** Camera
> height gives ρ = **−0.346** on the same data — nearly as strong. That is
> expected (a low camera is both closer to the sun's azimuth in these arcs and
> more grazing) but it means the *rank correlation alone* would not settle this.
> What settles it is the binned table above, the five direct specular-point hits
> at 0.03–0.11 frame-widths, and the away-from-sun control. The scalar is the
> weakest of the four pieces of evidence and is reported as such.

### Is it correct, or is it a defect?

**Correct, and deliberately so.** `world/build_surface.md` shows the specular
response at this sun was tuned twice, on measurements, before any of this:

* §"binder flushing" — *"nearly invisible in plan and **blazes at a 12.47° sun**,
  which is the condition every frame in this film is shot under"*;
* defect 7 — rubber dropping roughness by 0.30 made the racing line *brighter*
  than the asphalt at grazing angles; reduced to 0.12 so *"the sheen survives,
  the line reads"*;
* defect 13 — `Specular IOR Level` dropped 0.38 → 0.24 because a roughness-0.8
  surface *"puts enough sky in the lobe to turn a warm-grey binder cold at every
  grazing angle the film uses, and grazing angles are most of them."*

Base roughness is **0.72–0.86**, which is dry asphalt. A +3.3-stop sheen on
tarmac with the sun 12–21° off the lens axis is what tarmac does.

**And the frame agrees.** At f1426 the sheen is a glitter path running up to the
sun with the car sitting on it as a black silhouette — it is the most legible
the car is anywhere in the lap. Nothing here reads as a mistake.

---

## R2-1065 — R2-084 is adjacent, not causal, and the brief's statement of it conflates two different numbers

`C.SKY_IRRADIANCE` is **0.403 stops** low against the sky the film builds
(11.1818 measured against 8.4593 published). It **costs the film 0.123 stops**,
because the film's light is sun-dominated and the sky term is diluted 3.07×.
Those are two different quantities and `world/film_exposure.py` says so
explicitly (*"0.123 stops is what the shortfall COSTS THE FILM, not how far
`C.SKY_IRRADIANCE` is out"*). The brief pairs the 0.123 with the 11.18-vs-8.46
ratio, which is the 0.403.

**It is already compensated.** `FILM_EXPOSURE = −3.048 − 0.463 − 0.117 = −3.628`
carries `SKY_SHORTFALL_STOPS = −0.117` for exactly this. The uncompensated
residual is **+0.0061 stops**.

What that is worth in a delivered 8-bit frame:

| at display | slope | **0.123 stops** | **0.0061 stops (the actual residual)** |
|---|---:|---:|---:|
| f2000 road 0.5656 | 0.1451 | 4.6 code values | **0.23** |
| shoulder knee 0.6817 | 0.1123 | 3.5 | **0.17** |
| glared road 0.7692 | 0.0980 | 3.1 | **0.15** |

Against a glare excursion of **109 code values**. Even taken entirely
uncompensated, 0.123 stops is **2.8 %** of the effect it was suspected of
causing.

**And the mechanism excludes it outright.** The shortfall is in the *sky* term.
The shoulder excursion is the *sun's specular lobe*. Sky irradiance does not
enter the specular term except as weak ambient, so a sky-term error cannot
produce it in any amount.

> **Two true facts sitting next to each other with no relationship** — the shape
> this project has hit before. R2-084 remains open on its own merits (it is a
> real error in a published constant, and `film_exposure.py` documents why fixing
> it naively makes the film's number *worse* — a re-bake is a fixed-point
> iteration). It has nothing to do with the tone curve.

---

## R2-1066 — where a fix would belong, and why four of the five candidates are wrong

| candidate | verdict |
|---|---|
| **scene radiance** | No. Measured on the 5090 against a lambertian card and a 32-rung emissive ladder, two view transforms agreeing to 0.014 stops. |
| **the sun** | No. `SUN_ENERGY`, `SUN_COLOR`, elevation and bearing were measured against the sky model, and the exposure is calibrated *to* them. Moving the sun moves every frame, including beat 1. |
| **the material's albedo** | No, and it is the trap. The road is correctly dark when it is not in the glare (0.3791 at f2225, −0.83 stops under mid grey). Albedo drives the diffuse term; the excursion is specular. Lowering albedo would darken the 112 s that are already right to fix the 12 s that are not. |
| **the view transform / the look** | Forbidden — a client decision — **and not the cause.** AgX at −3.628 is doing precisely what a 3.3-stop specular excursion demands of it. |
| **the grade** | Forbidden twice over: one grade for the whole unbroken take, and the standing no-crush/no-lift constraint. |
| **the camera path** | **The only place left, and the only one with a real lever.** Four arcs, 12.04 s, defined entirely by the camera's heading relative to a fixed 12.47° sun. This is R2-652's ruling applied again: *if the read is real it belongs to the camera department, and it must not be textured around.* |

**And nothing needs to be done.** The sheen is authored, physically correct, and
the frame that carries the most of it is the frame in which the car reads best.
The honest answer to the question as asked is:

> **AgX is behaving correctly and there is no defect here.**

The one thing that *is* a defect is the instrument — `surface_test_filmpose.blend`
(R2-1061), which will keep producing wrong verdicts until its sun is put where
the contract says and its grade is set to `film_exposure.FILM_EXPOSURE`.

### Adjacent, found by the sweep, not mine

* **Beat 1's 6.04 % clip at f198–f205 is the daylight through the showroom
  glass** — the exterior sky and apron behind the window, blowing exactly as an
  interior-with-window shot does. It is unrelated to R2-082, which levelled the
  interior *practicals* to reach 0.0000 % pure **black**. Not a defect.
* **`world/surface_test_filmpose.blend` has no saved builder.** `CAM_filmpose_*`
  appears in exactly two files, both consumers. An ad-hoc rig with no build
  script cannot be regenerated, cannot be gated, and is how its sun got 139.6°
  out with nothing to notice.

---

## R2-1067 — two controls on the sweep itself, because a 1 745-frame number nobody has checked is not evidence either

**RESOLUTION CONTROL.** The brief allows 720p where the answer does not depend on
resolution. It does not — measured, not assumed. Six frames exist at both
1280×720/64 (denoised) and 3840×2160/512:

| frame | sh75 below-horizon, 720p | 4K | delta |
|---|---:|---:|---:|
| f2035 | 0.06 % | 0.06 % | 0.00 |
| f2100 | 0.11 % | 0.22 % | +0.11 |
| f2160 | 0.27 % | 0.35 % | +0.08 |
| f2185 | 27.99 % | 27.97 % | −0.03 |
| f2190 | 25.95 % | 25.96 % | +0.01 |
| **f2225** | **16.07 %** | **16.05 %** | **−0.01** |

Agreement to **0.11 percentage points** across a 0.06 %–28 % range. The shoulder
metric is resolution- and sample-independent, so the whole sweep is honest at
720p and the 4K frames were used only where the answer needed them.

**COVERAGE CONTROL.** `r2full` is not uniform: f793–1281 step 1, f1286–1896
step 5, f1900–2020 step 1, f2025–2575 step 5, f2576–2978 step 1. A step-5 sample
cannot miss an arc longer than 5 frames (0.21 s) and the shortest arc found is
51 frames, so **no arc can be hidden**; the arc *boundaries* are ±5 frames and
are quoted as such. Beat 5 is sampled 585 / 1 524 = 38 %.

**GRADE CONTROL.** The whole sweep rests on `exposure: null` meaning −3.628.
Checked end to end rather than read off a config: `film17_breach` at 4K/512
downscaled to 720p against `film16_breach` at 720p/64, **same frame f2225, two
different film builds, two resolutions, two sample counts** —

| | 4K/512, film17 | 720p/64, film16 |
|---|---:|---:|
| mean luma | 0.5052 | 0.5064 |
| p50 | 0.4125 | 0.4131 |

**0.0036 stops apart.** Both sequences are at the film's grade and are
comparable to each other.

**Also checked:** the R2-971 `PONT_B5_REBASED` candidate path moves **f2185 by
20 m and nothing else in the arcs** — f1376, f1426, f1436, f1671, f1691, f1746,
f2285, f2340, f2360, f2385 all move **0.000 m**. If that candidate lands, this
finding does not need re-running.

---

## R2-1068 — the counterfactual: what a master exposure move actually costs, measured on 189 delivered frames

The four wrong candidates in R2-1066 "each look like they worked on the frame you
tested". The exposure one can be tested on the whole film for **$0.00**, because
the delivered PNGs plus the film's own measured transfer are enough to re-grade
them: invert display → scene-linear through `agx.json`, apply Δ stops, push back.
`tools/r21061_exposure_counterfactual.py`. (It re-grades each channel through the
neutral ramp; AgX is not channel-separable, so this is exact for neutrals and good
for luma statistics, which is all it is used for. `--validate` checks it against a
real rendered pair — see R2-1069.)

**The smallest move that does anything useful is −0.846 stops** — just enough to
bring f2360's road *mean* to the 75 %-slope knee. It still leaves half that road
past the knee. Its cost, every 8th frame of the film:

| beat | sh75 below-horizon, now → after | lum p50, now → after |
|---|---|---|
| 1_assembly | 12.91 → 8.39 | 0.306 → 0.216 |
| **2_launch** | 27.11 → 16.56 | 0.336 → 0.239 |
| 3_breach | 2.51 → 0.19 | 0.332 → 0.236 |
| 4_transit | 0.51 → 0.01 | 0.240 → 0.166 |
| **5_lap** | **0.27 → 0.03** | 0.283 → 0.199 |
| 6_ending | 3.92 → 0.07 | 0.389 → 0.281 |

**And R2-082's own gate, on R2-082's own definition** — a pixel with all three
channels exactly 0 — over all **336** delivered beat-1 and beat-2 frames:

| | frames with any pure black | p90 | worst frame |
|---|---:|---:|---:|
| **now** | **68 / 336** | 0.0007 % | 0.0660 % (f860) |
| **at −0.846 stops** | **107 / 336** | **0.0129 %** | **0.2031 %** |

Read the columns against each other:

* **It fixes a problem the median frame does not have.** Beat 5's median goes
  0.27 % → 0.03 %. The median lap frame was never on the shoulder.
* **It walks back exactly what R2-082 bought.** The number of beat-1/2 frames
  carrying pure black goes up **1.6×**, p90 up **18×**, the worst frame up
  **3.1×**. R2-082 reached that state by levelling the practicals by
  `−FILM_EXPOSURE`; the practicals cannot be re-levelled to compensate without a
  per-beat exposure, which the one-shot law forbids.
* **Stated against myself:** R2-082 records **0.0000 % on every beat 1–2 frame**
  and these delivered 8-bit 720p frames show 68 with a trace, worst 0.066 %,
  concentrated at f852–f862. That is far more likely to be 8-bit quantisation of
  a float render than a regression, it is **not** a claim I am making, and it is
  flagged for R2-082's owner rather than acted on. The *direction and size of the
  change* under the counterfactual do not depend on it.
* **It darkens the entire film** — every beat's median luminance drops ~30 %.
* **And it contradicts R2-071 directly.** −3.628 sits **0.006 stops** from a
  measurement made on the 5090 against an 18 % card and a 32-rung radiance
  ladder, cross-checked by two view transforms agreeing to 0.014 stops and a
  closed-form sRGB inverse. −4.474 is **0.85 stops** from that measurement —
  140× the residual R2-071 defended, and in the direction R2-109 already caught
  once.

**To bring the glared road to mid grey costs −2.456 stops.** That is not a
proposal, it is a demonstration of the size of the thing: the excursion is
physical, it is 3.3 stops, and exposure cannot address it without taking the
other 112 seconds with it.

**Raising** exposure is not on the table either, for the same reason in reverse:
R2-071 rejected −3.048 at 0.586 stops precisely because it blows highlights, and
these are the frames it would blow first.

---

## R2-1069 — the actual scene-referred radiance of f2225's road, against what it should be

The brief asks for the number, not the adjective. Measured on
`b5verdict_4k_002225.png` (the film, 4K/512, −3.628), rect (2350, 1240)–(2950, 1480),
verified by eye at 1:1 to be clean asphalt with no line, kerb or car in it:

| | |
|---|---:|
| display mean | **0.3220** (sd 0.0249) |
| **scene-referred radiance** | **1.1218** |
| mid grey, same units | 2.2254 |
| **position on the curve** | **−0.99 stops UNDER mid grey** |
| local AgX slope there | 0.1305 display/stop = **85 % of peak** |

**What it should be.** `C.lambert_radiance(a) = a/π · E`. The asphalt's off-line
reflectance is **0.063–0.081 by zone**, measured on the shipped material at five
stations (`build_surface.md` §2.5, defect 9). Under the film's **measured**
light, 39.0106 W/m²:

| albedo | predicted lambertian | measured / predicted |
|---|---:|---:|
| 0.063 | 0.7823 | 1.43× (**+0.52 stops**) |
| 0.072 | 0.8941 | 1.25× (**+0.33 stops**) |
| 0.081 | 1.0058 | 1.12× (**+0.16 stops**) |

**+0.16 to +0.52 stops above a pure lambertian** — which is what a real surface
with a specular lobe, sky ambient and 50–200 m of aerial perspective in front of
it should sit at. The contract's own law is *"if a material's rendered patch is
not within a few percent of `lambert_radiance` for its intended albedo, the
material is wrong, not the light."* It is within half a stop, on the high side,
for the right reasons.

> **f2225's road is not blown and it is not "correctly bright". It is correctly
> DARK** — a full stop under mid grey, on 85 % of AgX's peak slope, with more
> tonal headroom above it than almost anything else in the frame.

(The patch is smooth because of the 180° shutter on a 280 km/h pan — **R2-652**,
already settled, and not the material.)

---

## R2-1070 — the ending, checked, because a fix that helps a road and kills the closing shot is a net loss

**My conclusion is a null change, so the ending is bit-identical by construction.**
That is the answer, but it is not a test, so the ending was measured anyway.

**Current state, 4K, delivered grade** (`r2851_4k_A_shipped`, −3.628):

| frame | sh75 below-horizon | sh60 | clip | lum mean |
|---|---:|---:|---:|---:|
| f2811 | 1.99 % | 0.02 % | 0.000 % | 0.4536 |
| f2937 | 4.12 % | 0.12 % | 0.002 % | 0.3946 |
| **f2978** | **5.97 %** | **0.20 %** | **0.004 %** | 0.3911 |

Over all 264 delivered beat-6 frames at 720p the shoulder is p50 3.86 % / max
5.84 % with **max clip 0.003 %**. **The ending has no shoulder problem at all**,
and the specular glint the closing constraint depends on is intact (f2978 peak
luma 1.0000, a handful of pixels).

**What the rejected candidates would do to it.** Under the −0.846-stop
counterfactual, beat 6's median luminance falls **0.389 → 0.281**, a ~28 %
darkening of the closing wide — applied to a shot whose whole problem is that a
small distant object has to separate from its background. And the constraint's
mechanism, as **R2-974** re-derived it, is the car's *internal contrast ratio*
against a low-variance ground (7.50× at f2035 where it works, 0.90× where it
fails); a global darkening compresses the car's own p95−p5 toward the toe, which
is the one thing that measurement says actually carries the shot.

**So the ending agrees with the road.** The move that would flatten 12 s of glare
darkens the 11 s that must not be darkened. Both tests point the same way, which
is the only reason this is a recommendation and not a trade-off.

> **Not mine, flagged:** beat 6 is being re-rendered right now by the R2-943
> agent (`film17_R2943.blend`, the closing car at 343 m instead of 1 km). Every
> beat-6 number above is from the **shipped** arm and will need re-reading
> against the candidate if it lands. Nothing in this diagnosis depends on which
> arm ships.

---

## R2-1071 — the tone curve accounts for ALL of the texture loss in the glare and none of it is extra, and a control proves the predictor is not a universal fitter

R2-1042's claim, stated properly, is falsifiable: *the surface texture is being
graded away*. If AgX is merely doing what AgX does, then the fine-octave contrast
of a glared road should be predictable **from its display level alone**, using
nothing but the measured curve.

For a fixed *relative scene* contrast — which is what a surface texture is —
relative *display* contrast goes as **slope / mean**. Taking f2225's clean road
as the one reference and predicting the others (RMS contrast in the 4 px band,
`tools/r21031_octave_contrast.py`, delivered 1280×720 frames):

| patch | display mean | AgX slope | slope/mean | predicted | **observed** | obs/pred |
|---|---:|---:|---:|---:|---:|---:|
| f2225 clean road | 0.3864 | 0.1451 | 0.3755 | *reference* | 0.0084 | 1.00× |
| **f2340 glare road** | 0.7507 | 0.0972 | 0.1295 | 0.0029 | **0.0023** | **0.79×** |
| **f2360 glare road** | 0.8796 | 0.0608 | 0.0691 | 0.0015 | **0.0017** | **1.10×** |
| f2000 clean road — **CONTROL** | 0.3308 | 0.1313 | 0.3969 | 0.0089 | 0.0271 | **3.05×** |

**The glared roads are predicted to within −21 % / +10 % by the view transform
alone.** Nothing else is being lost. The surface's scene-referred contrast in the
glare is the same as its scene-referred contrast out of it; what changed is where
the sun put it on the curve.

**And the control fires.** f2000 — a *clean* road at a different distance, lens
and shutter streak — misses by **3.05×**, because it differs in mm/px and motion
blur, not in tone. A predictor built only from the tone curve is therefore not
explaining everything put in front of it, which is the only thing that makes the
two glare rows mean anything.

> **This is the whole finding in one line.** *"AgX compresses highlights"* is a
> description of AgX working, and here it is quantified: in the 12 s of into-sun
> arcs the curve removes exactly the contrast a 3.3-stop lift is entitled to
> remove, and not one part more. **The texture is not being graded away. It is
> being displayed at the level the sun put it.**

Two footnotes that matter and point opposite ways:

* **The glared road carries MORE absolute display range, not less** — p95−p5 is
  **0.1115** at f2360 against **0.0465** at f2225. The sheen adds a large smooth
  gradient across the patch while the curve takes the fine octaves. A single
  scalar would call f2360 the higher-contrast patch; the octave table says which
  contrast it is. (Fourth time on this project that an aggregate has disagreed
  with a redistribution — R2-1031's 0.96× is the most recent.)
* **The frames, which are the arbiter.** At 1:1 the f2360 road is a near-white
  cream sheet carrying only smeared streaks; at f1426 the same sheen is a glitter
  path running to the sun with the car a black silhouette on it and the most
  legible it is anywhere in the lap. **Same phenomenon, opposite verdicts** — and
  that difference is composition and lens, i.e. the camera department, not the
  grade. That is the only actionable thing in this whole block, and it is a
  creative call, not a defect.

---

## R2-1072 — the answer, and what is left open

**The three pointers are not one defect.**

| pointer | verdict |
|---|---|
| **R2-1042** — f2225's road at 0.8617, 55 % slope | **Withdrawn. An instrument defect.** The rig's sun lamp is **139.61°** from the contract's bearing, its world is a bare Sky Texture with no clouds and no atmosphere, and it grades at **−3.048** — the value R2-071 refuted. In the delivered film that same road sits at **0.3220 display, 0.99 stops UNDER mid grey, on 85 % of AgX's peak slope, 0.00 % of it past the knee.** |
| **R2-084** — `C.SKY_IRRADIANCE` 0.123 stops low | **Adjacent, not causal.** Already compensated inside `FILM_EXPOSURE`; residual **+0.0061 stops = 0.15 of one 8-bit code value**. It is a *sky* term; the excursion is the *sun's* specular lobe. Real, open, unrelated. |
| **the grade constraint** | **Untouched, and it agrees.** The move that would flatten the glare darkens the closing wide by 28 % and multiplies beat-1/2 crush; both tests point the same way. |

**And the real behaviour underneath all three:** the film spends **12.04 s of
124.1 s** with significant road area on AgX's shoulder, in **four arcs defined
entirely by the camera pointing within ~30° of a fixed 12.47° sun**. It is a
specular sheen, it lands where geometry says the sun's mirror image must be, the
material was deliberately tuned to do it, and the view transform removes from it
exactly the contrast a 3.3-stop lift is entitled to remove — **−21 % / +10 %
against prediction, with a control that misses by 3.05×.**

> **AgX is behaving correctly and there is no defect in the tone curve.**

### Changed: nothing

No blend written, no constant moved, no grade touched, `DEFECT-LOG-R2.md` not
edited. New read-only instruments only:

| tool | what it does | selftest |
|---|---|---|
| `tools/r21061_knee_sweep.py` | shoulder area of a delivered frame, from the film's own measured transfer | **4/4**, one arm required to fail |
| `tools/r21061_glitter.py` | predicts the specular point from sun + pose, no render | negative control fires on 8 away-from-sun frames |
| `tools/r21061_sun_correlation.py` | shoulder area vs view-to-sun over 585 lap frames | negative control on camera height, reported even though it is close |
| `tools/r21061_exposure_counterfactual.py` | re-grades delivered frames to test an exposure move for $0 | `--validate` against a real rendered pair |
| `tools/r21061_probe_testrig.py`, `..._probe_mat.py` | read-only probes of a blend's light and BSDF | — |

**Spend: $0.031** — six 1280×720/64 frames on the already-cached
`film17_R2943.blend` (no upload), queued at priority 60 behind R2-943's batch, to
validate `r21061_exposure_counterfactual.py` against ground truth and to show the
−2.07-stop move on a real f2360, f2978 and f400. **Everything else in this block
cost $0.00** and came from 1 745 delivered frames that were already on disk.

### Open, and not mine

1. **`world/surface_test_filmpose.blend` is broken and has no builder.** Its sun
   must be `C.SUN_DIR` and its grade `film_exposure.FILM_EXPOSURE`, and it needs
   a saved build script and a preflight that asserts both. Until then it will
   keep producing confident wrong verdicts — it has produced two.
   **Owner: whoever owns R2-1031/R2-1036.**
2. **Every absolute level in R2-1036 needs re-reading** once that rig is fixed.
   The A/B ratios stand; the levels do not.
3. **The four into-sun arcs are a composition question, not a defect.**
   f1376–1436, f1671–1746, f2185–2235, f2285–2385 (±5 frames). At f1426 the sheen
   is the best the car looks all lap; at f2340–2360 the frame goes to cream.
   **Owner: the camera department**, per R2-652's ruling.
4. **R2-084 stays open on its own merits** — and `film_exposure.py` already
   documents why a naive re-bake makes `FILM_EXPOSURE` *worse* (a fixed-point
   iteration, not an assignment). Nothing here changes that.
5. **A trace of pure black at f852–f862** (max 0.066 %) against R2-082's recorded
   0.0000 %. Almost certainly 8-bit quantisation. **Owner: R2-082.** Not a claim.
