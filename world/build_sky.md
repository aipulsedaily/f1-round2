# build_sky.md — the sky, the sun, and the air between them

`world/build_sky.py` owns **the single physical light of the entire film** and the medium
it travels through. One camera crosses from a darkened showroom interior to a 3675 m
circuit without a cut, so there is exactly one sun, one sky and one atmosphere, and they
have to be right in *absolute* terms, not merely pretty in each beat.

Everything here is generated procedurally in Blender. There is no HDRI, no photograph,
no image file of any kind — the world shader is 198 nodes and travels inside the blend.
(Round 1's `assets/city.exr` is a downloaded photograph; the round-2 brief forbids it and
`DEFECT-LOG-R2.md` R2-013 records the render-farm failure it caused. Nothing here can
repeat that failure, because there is nothing to fail to load.)

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_sky.py
                                                          -- --verify         # the gates
                                                          -- --calibrate      # re-measure the sun
                                                          -- --render all     # test frames
```

`build()` creates the `WORLD_SKY` collection (3 objects, 24 triangles), assigns
`SKY_World`, and returns a summary dict. It is idempotent: the second call purges nine
datablocks and produces the identical scene.

---

## 1. What it makes

| datablock | what it is |
|---|---|
| `SKY_Sun` | the SUN lamp: the direct beam, 115.754 W/m² normal, colour (1.000, 0.716, 0.387), disc 0.545° |
| `SKY_World` | MULTIPLE_SCATTERING sky + three cloud decks + a camera-ray-only solar disc |
| `SKY_AirColumn` | homogeneous Mie + Rayleigh slab, z −220…1500 m, ±40 km |
| `SKY_AirBoundary` | second homogeneous slab, z −220…240 m, adding the near-ground aerosol |
| `SKY_HazeStrata` | textured low haze — **opt-in**, `SKY_STRATA=1`, off by default (§5.2) |

## 2. Hand-off to the other builders

| what | value | why it matters |
|---|---|---|
| `camera.data.clip_end` | **≥ 50 000** | Cycles integrates the volume only to `clip_end`. A 1 km clip truncates the airlight and the horizon goes hard-edged. |
| reference exterior exposure | **−3.048 stops** | an albedo-0.18 horizontal surface in full sun renders at 1.4888 linear; −3.048 puts it on AgX mid-grey. **This module never writes `view_settings`** — the animated camera owns exposure, per the brief. |
| `build_sky.bind_camera(cam)` | call once the rig exists | binds two drivers so the cloud decks parallax against the camera's world XY over the 3.6 km lap. Without it they behave as a skybox — degraded, not broken. |
| `scene.cycles.volume_bounces` | build() raises it to ≥ 2 | at τ > 1 the horizon haze is mostly multiply-scattered light; Blender's default of 0 renders it too dark. |
| `scene.cycles.sample_clamp_indirect` | build() raises 10.0 → 200.0, **only if still at the default** | Cycles' default assumes a scene referenced near 1.0. This one is referenced near 100 — sunlit white renders at 38, a sunlit cloud flank at ~50 — so the default silently crushes the entire indirect budget. A deliberate value set by the render owner is left alone. |
| second SUN lamp | build() warns | the other builders each ship a `TEST_`/`ARCH_TESTSUN`-style lamp for their own previews. Two suns break the one-light law. |
| interior practicals | must stay on for the whole film | not this module's, but `circuit_spec.md` §10.6 depends on it: at 595 m the Beat-6 wound reads only because the room behind it glows. |

---

## 3. The three things that were measured, not assumed

Blender 5.2 changed the Sky Texture (the old `NISHITA` is now `SINGLE_SCATTERING` /
`MULTIPLE_SCATTERING`, the latter being García Liñán's spectral model). Three of its
behaviours are undocumented or easy to get backwards, and all three are invisible in a
clear-sky test frame — so each was measured.

### 3.1 `sun_rotation` convention

The `Vector` input of the Sky Texture node is **disabled** for both scattering models, so
the deck cannot be rotated with a Mapping node and `sun_rotation` is the only handle. An
emissive marker sphere was placed at exactly `SUN_DIR`, an equirect of the sky rendered
with the model's own disc on, and `sun_rotation` swept. The sun's column moved linearly
at 4.0 px/deg and coincided with the marker at 148°. Convention:

```
sun_bearing_world = 90° − sun_rotation          →  SKY_SUN_ROTATION = 147.9697°
```

### 3.2 ray direction in a world shader

`Texture Coordinate → Generated` is the **unit ray direction** in world space.
`Geometry → Incoming` is its **negation**. Measured by rendering the socket as colour
down each world axis. Getting it backwards mirrors the whole sky through the origin,
which a clear-sky test cannot show you.

### 3.3 the sun's irradiance and colour

The lamp is not dialled to taste; it is matched to the sky model's own sun so that the two
cannot disagree. Two independent measurements at the final sky parameters:

| method | E_normal (R, G, B) |
|---|---|
| white Lambert plane, sky disc ON minus OFF, × π ⁄ sin(elevation) | **115.754, 82.917, 44.811** |
| direct solid-angle integration of a 512² / 1.03° render of the disc | 115.764, 82.914, 44.787 |

They agree to four significant figures. `--calibrate` re-runs the first method and fails
loudly if the baked constants drift more than 2 %.

The same render gives the disc's **centre** radiance (2.036e6, 1.458e6, 7.877e5), whose
ratio to the disc mean is 1.25 — i.e. limb darkening u = 0.60, the classic visible-band
value. The world shader draws the disc with exactly that law (§4.3).

---

## 4. The sky

### 4.1 the base

`MULTIPLE_SCATTERING`, `air 1.00 / aerosol 0.45 / ozone 1.30`, altitude 0, elevation
12.4706°, rotation 147.9697°, **`sun_disc = False`**.

* **aerosol is 0.45, not 1.0, on purpose.** The bottom ~1.1 km of aerosol is modelled
  explicitly as geometry (§5) so that distant *objects* haze, which a background shader
  can never do. Leaving the sky at 1.0 would count that air twice.
* **ozone 1.30** — mid-latitude summer. Ozone's Chappuis band eats 550–650 nm and is the
  only reason a clean afternoon sky is blue rather than white; with the sun 12.5° up it is
  what keeps the anti-solar half saturated instead of washing to grey.

### 4.2 three cloud decks

Each deck is a spherical shell intersected by the view ray:

```
t = −R·Dz + sqrt((R·Dz)² + 2RH + H²)          R = 6 371 km
```

The discriminant is positive in every direction, so there is exactly one outward hit and
the maths needs no branch. Using the **sphere** rather than a flat plane is what makes a
deck stop at the true horizon (the 9 km cirrus reaches 338 km and quits) and what
compresses the cells correctly as they recede. The flat-plane version runs to infinity and
reads as a painted dome.

The observer's height is taken as 0 — the camera never exceeds 140 m, which is 1.5 % of
the lowest deck. The observer's **XY is tracked** (`bind_camera`) because the camera
travels 3.6 km, and at 1550 m a deck that does not parallax over that baseline is the
classic skybox tell.

| deck | altitude | cell size | shear | wind | evolves | sun march |
|---|---:|---:|---:|---:|---:|---:|
| cirrus | 9000 m | 9000 m × 5.0 aniso | +18° | 34 m/s | slow | none (optically thin) |
| altocumulus | 4600 m | 2100 m × 1.7 | −12° | 14 m/s | medium | 2 taps |
| cumulus | 1550 m | 1250 m × 1.25 | −34° | 8 m/s | fast | 4 taps |

Design decisions worth knowing:

* **The wind veers with height** (Ekman spiral): surface flow is backed 30–50° from the
  gradient wind, so the three decks run at three different bearings. That single detail is
  most of what makes a sky read as a place rather than a backdrop.
* **Coverage is composed, not uniform.** A large-scale mask thins the sunward sky for the
  two water decks so the low sun has something to read against, and *thickens* it for
  cirrus, because high ice cloud between the lens and a low sun is the whole point of high
  ice cloud. A 26 km noise adds ±0.09 of organic patchiness on top so coverage is never
  flat anywhere.
* **The sun march is nearly the real ray.** At 12.5° a sun ray crosses 4.52 m of deck
  horizontally per metre of depth, so it enters a cumulus almost through its flank.
  Marching in the projected plane toward the sun's bearing is therefore very nearly the
  3-D march, and it produces the correct late-afternoon look: one bright flank, a long
  dark body behind it.
* **Flat bases.** Looking steeply up you see the shaded underside; looking shallow you see
  the sunlit flank. Three nodes, and it is the difference between cumulus and cotton wool.
* **Radiometry is derived, not tinted.** Lit flank = albedo · E_normal · ⟨cos⟩ ⁄ π = 20.7;
  shaded side = albedo · (sky + bounce) ⁄ π = 2.6. Cirrus is handled as optically thin
  single scatter, L = τ · E ⁄ 4π · P(θ) with τ = 0.40, which makes it *darker* than the
  blue sky away from the sun (a grey veil) and brighter than anything but the disc within
  a few degrees of it. That asymmetry is the look of high cloud at a low sun and it falls
  out of the phase function rather than out of a colour choice.

### 4.3 the solar disc

Drawn in the world shader, multiplied by `Light Path → Is Camera Ray`, so it adds
**zero** light. Reasons, in order:

1. the sky node's own `sun_disc` would light the scene a second time on top of the lamp,
   and the lamp is what gives clean shadows and a controllable penumbra;
2. a SUN lamp left visible to camera draws a **flat** disc — no limb darkening, wrong at
   4K in a shot that looks into the sun;
3. so: `lamp.visible_camera = False`, `sky.sun_disc = False`, and the disc is a
   camera-only emission term with the real limb law at the radiance derived from the same
   measured irradiance the lamp uses. One sun, three consumers, no way for them to
   disagree. The limb edge is a smoothstep over ±1.5 % of the radius rather than a step,
   because a hard cut aliases at 4K and 4.5 air masses blur the real limb by about that
   much anyway.

**The disc carries a slab compensation, and gate G5 is why.** The lamp is not attenuated
by `SKY_Atmosphere` (§5.1) because its measured value is already the ground-level beam.
The drawn disc, however, *is* part of the background, so a camera ray to it crosses the
whole slab and is attenuated. Left alone, the visible sun came out **half as bright and
visibly redder** than the light it casts — the bottom kilometre of reddening counted
twice, exactly the error the lamp was spared. G5 measured the disc arriving at
(0.489, 0.437, 0.349) of the lamp; the closed form

```
tau = sigma_aer·(0.62·1500 + 0.38·240)/sin h · AEROSOL_RGB + sigma_ray·1500/sin h · RAYLEIGH_RGB
    = (0.7174, 0.8301, 1.0567)      →   T = (0.4880, 0.4360, 0.3476)
```

agrees to three decimals, so the disc is pre-divided by it exactly rather than fitted. The
drawn peak is 4.172e6 at tint (1.000, 0.802, 0.544); after the slab it is the 2.036e6 at
(1.000, 0.716, 0.387) that the lamp casts.

**There is no hand-painted aureole.** The circumsolar glow was measured on the bare sky
(18→3 from 0.5° to 25°) and the rest comes from Mie in-scattering in the haze slab, which
is where it belongs physically. Painting one on top would have double-counted it.

### 4.4 banding

Round 1 logged sky banding as a defect class. Four things are done about it and none of
them is a post-process:

1. **Nothing is quantised in the shader.** No colour ramps, no lookup textures, no image
   of any kind — the gradient is analytic and has infinite angular resolution, so it
   cannot band at 4K, 8K or any other resolution.
2. **A 1 % aerosol mottle** at a few degrees' scale multiplies the sky. Real skies have
   it, and it decorrelates quantisation *structurally* — unlike a per-pixel dither, which
   averages away to nothing under 1000+ samples.
3. The cloud decks put real structure across most of the sky anyway.
4. `dither_intensity = 1.0` at the 8-bit encode (a render setting, not this module's; it
   is set in the test harness so the gate measures the shipping path).

The G4 gate renders 3840×2160 through the shipping view transform to 8-bit and measures
the longest run of identical codes and the residual σ in LSB **on a single-pixel column**.
Its first version averaged 240 columns and failed the sky — because averaging cancels the
dither, which is the very thing hiding the staircase. What a viewer sees is the displayed
pixels, so that is what gets measured; the averaged figure survives as a diagnostic
because it reports the underlying gradient slope. See §7.

---

## 5. The air

### 5.1 what it is

```
sigma_ext(550) = 3.912 / V,   V = 23 km   →   1.7009e-4 /m
   Rayleigh 1.16e-5  (λ⁻⁴ split 0.649 / 1.000 / 1.949 across Rec.709 primaries)
   aerosol  1.585e-4 (Ångström 1.1 split 0.887 / 1.000 / 1.200)
```

V = 23 km is a clean-but-not-arctic summer afternoon, and it was chosen for what it does
to the shot rather than for a mood: 600 m (the Beat-6 showroom) transmits 91 %, 3 km
transmits 60 %, 10 km transmits 18 %. That is a readable depth ramp instead of either a
crisp matte painting or grey mush.

Two nested **homogeneous** slabs approximate the real exponential profile
σ(z) = σ₀·exp(−z/1120 m) in two steps: a full-column slab at 0.62 σ₀ carrying all of the
Rayleigh, and a boundary-layer slab at 0.38 σ₀ that overlaps it (rather than abutting —
coincident volume faces are a precision hazard and a gap would punch a hole in the
column). Ground level therefore sees 1.00 σ₀ and anything above 240 m sees 0.62.

`visible_shadow = False` on both, deliberately. The measured `SUN_IRRADIANCE` is already
the value **at the ground** — all 4.5 air masses of reddening are inside `SUN_COLOR`. If
the slabs also attenuated shadow rays they would apply the bottom kilometre of that path a
second time (τ = 0.70 over the 4.1 km slant path, i.e. half the key light), and every
shadow ray in the film would become a volume ray. The price is that the global haze casts
no god rays; a clear sky has no occluders, so there is nothing to lose, and the breach
dust column is a separate local volume that may cast whatever it likes.

### 5.2 why the air is homogeneous — the measurement that decided it

The obvious "quality" move is a texture-driven haze layer with patchy density. It was
built, rendered and rejected on cost. Same frame, 512×256 / 64 spp, GTX 1070:

| configuration | time |
|---|---:|
| no volume | 2.5 s |
| homogeneous slab | 2.7 s |
| homogeneous slab + a second homogeneous slab nested inside it | 8.1 s vs 8.8 s alone — **free** |
| slab + **textured** low layer | 22–48 s |
| the same, with `volume_biased` forced on | 11.1 s |

Cycles integrates a homogeneous volume analytically and ray-marches a textured one; in
Blender 5.2 `volume_biased` is off by default, so `volume_step_rate` does nothing and the
cost is ratio-tracking. Across 2978 frames the difference is between free and a multi-day
tax on the whole film, for a subtlety. So the global air is analytic, and the textured
layer survives as `SKY_STRATA=1` for hero frames.

What being homogeneous does **not** cost, because these are properties of the phase
function and the scene rather than of a density texture:

* the air glows toward the sun and goes quietly blue-grey away from it — same medium,
  opposite behaviour, no per-shot cheat;
* haze darkens inside the shadow of a grandstand or the pit building, because shadow rays
  *out of* the volume are still occluded by real geometry;
* the distance ramp, which is the entire point.

### 5.3 the phase function — chosen by measurement

The first version used a single Henyey-Greenstein lobe at g = 0.78, the textbook value for
continental haze. It rendered a **40° featureless white blob** wherever the camera looked
near the sun, because a single HG lobe is far too flat: P(0)/P(20°) is only 5.1.

The mean airlight was then rendered in annuli around the sun (48 spp, 90° lens) for six
candidates:

| phase | 0.6–1.5° | 6–12° | 12–20° | 1°→20° fall |
|---|---:|---:|---:|---:|
| HG g = 0.60 | 47 | 42 | 22 | 2× — no aureole at all |
| HG g = 0.85 | 280 | 105 | 30 | 9× — still too broad |
| two-lobe HG 0.93 + 0.45 | 386 | 50 | 18.5 | 21× — good |
| **Mie d = 2.0 µm** | **498** | **77** | **24** | **21× — same shape, one closure** |
| Mie d = 0.6 µm | 170 | 93 | 32 | 5× — too flat |
| Mie d = 8.0 µm | 2578 | 55 | 23 | 112× — fog, not haze |

Mie at 2 µm reproduces the two-lobe fit in a single node, and 2 µm is also the right
number physically for continental haze and thin mist droplets.

### 5.4 the closure budget — a hard Cycles limit worth writing down

Cycles charges **`MAX_VOLUME_STACK_SIZE` = 32 closures per volume closure** against a
kernel limit of 64. A material may therefore hold at most **two** volume closure nodes.
The first version had four (two HG lobes + absorption + Rayleigh) and Cycles logged

```
WARNING Maximum number of closures exceeded: 128 > 64
```

then silently clamped — a correctness bug hiding in a log line nobody greps for. The
budget is now spent as: one Mie aerosol + one Rayleigh in the column slab, one Mie in the
boundary slab, and an assertion in `_atmosphere_material` so a future edit cannot quietly
blow it again.

The casualty was aerosol **absorption**, and its cost is bounded and known. Single-
scattering albedo is taken as 1.0 (real tropospheric aerosol is 0.90–0.98). The
**extinction is unchanged** — the coefficient is set to the target either way, so the
distance ramp and the visual range are exact — and only the airlight is up to 8 % brighter
than a ssa = 0.92 haze, i.e. the far distance sits a twelfth of a stop lighter.

---

## 6. Decisions a later reader would otherwise reverse-engineer

**6.1 The sun is absolute, not convenient.** The scene renders at ~115 W/m², so a sunlit
white surface sits near 10 linear and the film needs about −3 stops of camera exposure.
That is deliberate: the showroom interior and the circuit exterior are in one continuous
take, and the only way the Beat-4 "exposure animates from interior spill to full daylight"
ramp can be honest is if the two are separated by the real number of stops. Normalising
the sun to something comfortable would have made that ramp a lie.

**6.2 The clouds light the scene; the disc does not.** Cloud decks are visible to every
ray type, so they appear in the car's paint reflections and contribute to ambient. A gloss
-black F1 car reflecting a featureless gradient is the classic CG giveaway; this is the
cheapest fix for it available. Only the disc is camera-only, and only because the lamp
already does that job.

**6.3 There are no cloud shadows on the ground, and that is a decision.** Blender sun
lamps take no gobo, so cloud shadows would need real geometry high above the circuit —
which would then also have to be lit, shaded and matched to the world-shader decks. Worse,
a moving cloud shadow crossing the track changes the key light during a single unbroken
take, and five other builders are lighting to a constant sun. A mostly-clear late
afternoon motivates their absence. If they are ever wanted, the honest implementation is a
transmissive plane at 1550 m sharing the cumulus deck's noise parameters, not a hack in
this module.

**6.4 The camera-XY drivers use simple expressions on purpose.** `frame / fps` and a bare
`v` on a `TRANSFORMS` variable are handled by Blender's simple-expression evaluator, so
the blend does not need script auto-execution to animate correctly. That matters because
these blends go to a rented render node, and enabling auto-run there is not something to
do casually.

**6.5 The test harness clears the stage, and had to learn to.** `blender -b
--factory-startup` opens with a 2 m Cube at the origin and a 1000 W point light 6 m above
it. Both were silently present in the first round of test frames: the Cube swallowed the
1 m shadow gnomon (which is why an early frame appeared to show a cube with a black top
face), the Cube's own shadow was measured as the gnomon's and came out 30 % long, and the
point light polluted every ambient reading. `_clear_test()` now owns the stage and asserts
no stray lights. **`build()` deliberately does not do this** — it is meant to be called
into the assembled world and touches nothing but its own datablocks.

---

## 7. The gates

`-- --verify` renders five measurements, all five currently passing. Numbers below are
from the run recorded in `render/world/sky/verify.json`.

### G1 — face radiance against the Lambert prediction

A 2 m albedo-0.8 cube, each face shot on axis. Predicted direct radiance is
`albedo/π · E_normal · max(0, n·s)`; everything above it is ambient.

| face | n·s | measured | direct prediction | ambient |
|---|---:|---|---|---|
| top | 0.2159 | 12.06, 10.02, 7.87 | 6.37, 4.56, 2.46 | 5.70, 5.46, 5.41 |
| east | 0.5179 | 24.89, 19.19, 12.22 | 15.26, 10.93, 5.91 | 9.62, 8.25, 6.31 |
| south | 0.8278 | 37.93, 28.85, 17.73 | 24.40, 17.48, 9.45 | 13.53, 11.37, 8.28 |
| north | 0.0000 | 3.19, 3.27, 3.33 | 0, 0, 0 | 3.19, 3.27, 3.33 |

Every lit face lands on its prediction plus a plausible ambient, and the ambient *rises*
with how much sunward sky the face sees (5.4 → 8.5 → 11.5) — the circumsolar haze glow
doing exactly what it should.

Derived, and the number that would expose double counting between the sky model's own
aerosol column and `SKY_Atmosphere`'s:

```
diffuse irradiance with haze  22.4, 21.5, 21.2
direct horizontal             25.0, 17.9,  9.7
diffuse / direct-horizontal = 1.24        real sky at 12.5°: 0.8-1.2      PASS
```

1.24 sits just above the quoted band and that is the honest reading: this air is on the
hazy side of "clear", which is the design (§5.1). It is also the number that would blow up
if the sky model's aerosol column and `SKY_Atmosphere`'s were both counted in full —
`SKY_AEROSOL = 0.45` instead of 1.0 is what keeps it at 1.24 instead of near 1.5.

### G2 — shadow length and bearing

A 1.000 m post, orthographic from straight above, profiled along the expected shadow ray.

```
length  4.568 m vs 4.522 m  (+1.02%)      bearing  121.90° vs 122.03°  (−0.13°)   PASS
```

The +1.02 % is the post's own 50 mm half-width plus the 40 mm confirmation run, i.e. the
instrument, not the light. Two earlier readings of this gate were wrong for reasons worth
recording: a global dark-pixel threshold returned a frame corner (a thin post's shadow is
0.1 % of the frame, so any percentile lands inside render noise), and taking the *last*
sub-threshold sample rather than the first crossing doubled the answer.

### G3 — aerial perspective

Identical albedo-0.8 cards, each scaled to subtend the same angle, at five ranges along
the anti-solar axis. The implied airlight is `measured − L(0)·T(d)`.

| range | measured | T(d) | implied airlight |
|---:|---|---:|---|
| 50 m | 24.81, 19.13, 12.18 | 0.9915 | 0.21, 0.16, 0.10 |
| 500 m | 23.99, 18.45, 11.73 | 0.9185 | 1.20, 0.88, 0.54 |
| 2 km | 21.55, 16.46, 10.41 | 0.7116 | 3.89, 2.85, 1.74 |
| 8 km | 15.34, 11.73, 7.71 | 0.2565 | 8.98, 6.82, 4.58 |
| 25 km | 11.30, 9.15, 6.81 | 0.0142 | 10.95, 8.87, 6.64 |

The airlight rises monotonically to a plateau and the card converges onto it — the card at
25 km *is* the air. That is the curve aerial perspective is supposed to have, and
`sky_away.png` and `sky_beat6.png` show the same ladder as a picture.

### G4 — banding at 4K

3840×2160 through the shipping view transform to 8-bit with `dither_intensity = 1.0`,
**denoised** (the worst case: the denoiser removes exactly the render noise that would
otherwise hide banding, so an un-denoised gate passes for the wrong reason).

```
gradient spans 34 codes over 2160 px (63.5 px/code)
single-pixel column : longest flat run 17 px, residual sigma 0.534 LSB       PASS
240-column average  : longest flat run 94 px, residual sigma 0.234 LSB       diagnostic
```

63.5 px per code is a *very* slow gradient — precisely the condition round 1 banded in —
and at the pixel level it carries 0.53 LSB of structure with no run longer than 17 px, so
there is nothing for the eye to lock onto. `sky_banding_crop26x.png` is the same patch at
26× contrast: no contours, only fine dither and the sky's own mottle.

### G5 — the drawn disc must *be* the lamp

A 2000 mm lens (1.03° of frame) pointed straight up the sun vector; the drawn disc is
integrated over solid angle and must return `SUN_IRRADIANCE`.

```
drawn disc, integrated   116.008, 83.116, 44.936
lamp irradiance          115.754, 82.917, 44.811
worst channel            0.28%                                              PASS
```

This is the gate that found the slab double-reddening described in §4.3 — before the fix
it read 65 % low with a per-channel signature. Nothing else in the pipeline would have
caught a sun that is the wrong brightness for its own shadows.

---

## 8. Test renders

In `render/world/sky/`, all rendered locally on the GTX 1070 and looked at:

| frame | what it is for |
|---|---|
| `sky_dome.png` | full 360° equirect — every deck, the disc, the horizon, in one image |
| `sky_into_sun.png` | straight into the 12.5° sun: disc, aureole, cirrus silver lining |
| `sky_beat6.png` | the Beat-6 hold station and lens, (594.19, 16.05, 140.0) at 18.75 mm |
| `sky_away.png` | anti-solar, with the depth ladder |
| `sky_shadow.png` | a 1 m cube: the sunward face brightest, then the east face, then the top, and a 4.5 m shadow |
| `sky_banding.png` | the 4K gradient the G4 gate measures |
| `sky_banding_crop26x.png` | the same patch at 26× contrast: no contours, only dither and mottle |
| `verify.json` | every number in §7, machine-readable |

The ground in these frames is harness scaffolding — a flat albedo-0.115 plane and a few
concrete slabs. The real terrain, surface, barriers and dressing belong to the other five
modules; nothing here depends on them and nothing there should re-declare a sun.
