# tyre_deposit — the rubber the car actually lays down

**Status: BUILT AND GATED, WIRED INTO NOTHING.** Four node groups and three
replica materials live in `world/items/tyre_deposit.py`. No existing world
module was edited. Nothing ships until a 4K A/B is approved.

    selftest   python3 world/items/tyre_deposit.py --selftest
    relief     python3 world/items/tyre_deposit.py --relief
    build      blender -b --factory-startup -P world/items/tyre_deposit.py -- \
                   --test-scene --substrate concrete --arm deposit \
                   --save world/items/tyre_deposit_test.blend
    gate       blender -b --factory-startup -P world/items/tyre_deposit.py -- --gate

Blender is `/opt/blender-5.2.0-linux-x64/blender`. **It exits 0 on an uncaught
exception.** Judge every run by its printed `>> STAGE RESULT:` line.

---

## 1. What it produces

### The field — `TDP_DepositField`

A shader node group. In: a **world** position, a `Front X` float (the time
gate), a `Traffic Passes` float (the one art knob, default 1). Out: `Density`,
`Coverage`, `Wetting`, `Grain`, `Launch`, `Film`.

| | |
|---|---|
| coordinate | `TexCoord → Object` → `VectorTransform` (POINT, OBJECT → WORLD) |
| valid over | world x −1.80 … **63.5** — see §6 |
| instances | 4: `launch_RL`, `launch_RR`, `film_RL`, `film_RR` |
| ground truth | `work/r2_1211_rubber_tracks.json` + `telemetry/telemetry.csv` |

**(a) The launch patch.** Two patches, one per rear wheel. World
x −1.80000 → −1.55840, |y| = 0.79750, contact patch 251.1 mm, deck z = 0.340.
The along-track profile is the per-frame `deposit_norm` of `wheels.RL/RR`,
decade `1.000 0.954 0.794 0.646 0.507 0.381 0.267 0.168 0.086 0.027`, terminated
at 2.7 % of peak. Both edges — the leading one where the tyre stood, the
trailing one where it hooked up — are authored at 12 mm, the floor of the
resolvable band: as hard as the camera can see and no harder.

**It is time-gated, and so is the film.** `Front X` is keyframed from the
wheel's own per-frame world x — **248 keys, frames 817 → 1064, x −1.79280 →
62.039** — LINEAR between keys, CONSTANT extrapolation:

    f ≤ 817   −1.812  (12 mm behind the mark's start: strictly nothing)
    f 818     −1.792803        f 823   −1.662575
    f 819     −1.766776        f 824   −1.636503
    f 820     −1.740703        f 825   −1.610503
    f 821     −1.714676        f 826   −1.584475
    f 822     −1.688603        f 827   −1.558403   … then on to x = 62.039

`bind_time(value_node)` installs it; `FULLY_LAID_X` is the static value for an
A/B. **A static deck mark is a beat-1 defect, not a beat-2 fix**: the same
ground is seen at 27.6° and 42.7° at frames 374 and 424, under a parked car.

**The first pass of this module got the film wrong in exactly the same way**,
and the field probe caught it: at frame 816 the deck beyond the mark was already
carrying the tractive film at density 4.99e-04. A film lying on ground the car
has not reached is rubber from a drive-out that has not happened, and the
showroom floor at x = 6.3 … 15 is on screen while the car is still parked. One
curve now gates both terms.

**(b) The tractive-slip film.** Derived from `accel_long_ms2` and
`normal_load_norm`:

    mu_used(t) = accel_long_ms2(t) / (2 · normal_load_norm(t) · g)
    kappa(t)   = mu_used(t) / (C_kappa/Fz)

`mu_used` over x = 15 … 49 is **1.6968 … 1.7023, p50 1.7004** — flat, because
`accel_long_ms2` is 10.659 … 10.699 across the whole span. One scale constant,
set by the brief's 1 m target and then checked:

| | |
|---|---|
| ∫ mu_used ds over x = 15…49 | 57.4657 m |
| scale | 0.0174017 |
| **kappa over x = 15…49** | **0.02953 … 0.02962** — inside the 2–8 % band |
| slid over x = 15…49 | **1.00000 m** (the calibration target) |
| slid over the whole straight drive-out | 1.84825 m |
| implied C_kappa/Fz vs the car's **weight** | 57.5 |
| …with the ~2× aero load at 16–31 m/s | **28.7 — the top of the 15–30 slick range** |

### The three applications

| group | substrate | what the deposit does |
|---|---|---|
| `TDP_Apply_Concrete` | `M_Surf_Concrete` | Base Color ×dim + mix; **Roughness 0.80 → 0.52**; **Specular IOR Level 0.32 → 0.5322**; both substrate bump stages REDUCED; three own relief stages |
| `TDP_Apply_BrushedMetal` | `TurntableTop` | **Metallic 0.86 → 0.052**; Roughness → 0.68; Base Color barely touched |
| `TDP_Apply_PolishedFloor` | `FloorPolished` | **no pigment mix exists in the graph**; Roughness → 0.42; Coat Weight 0.45 → 0.171 (capped); Coat Roughness 0.045 → 0.30 |

The delivery ramp is **not built**: `dais_delivery_ramp` is HOLD in
`world/items/PLACEMENT.json`, `tools/build_film_scene.py` composites only
`Floor`, `GW_*`, `Turntable_Deck`, `Platform_Dais`, and the derived deposit
there is 0.0 anyway.

`0.5322` is not a taste number. Principled's Specular IOR Level is F0/0.08, and
rubber at n = 1.52 has F0 = ((n−1)/(n+1))² = 0.04258.

---

## 2. The idea the whole module turns on

Under **any** single monotone opacity law, a film at 1/460 of a mark's areal
density either leaves the mark invisible or leaves the film invisible. That is
the real tension in this block, and it is why the apron paint has never worked.

Rubber does two different things at two different scales, and they saturate
1000× apart. One transferred film thickness, two laws:

    thickness(D) = D · LAUNCH_PEAK_AREAL · TRANSFER_M_PER_M
    TRANSFER_M_PER_M = 9.0e-8 m of film per metre of tyre surface slid per m²
                       (Archard on rubber/concrete at ~3 bar)

    the launch patch, D = 1        →  11.0 µm of rubber
    the tractive film, D = 9.6e-4  →  10.6 nm of rubber

**Three scales, not two — and the third one the gate had to teach me.**

| law | drives | length | launch (11.0 µm) | film (10.6 nm) |
|---|---|---:|---:|---:|
| **wetting** | Roughness, Coat Roughness | `TAU_WET_M` **7.6 nm** — surface energy, ~25 molecular layers | 1.0000 | 0.7523 |
| **interface** | Metallic, Specular IOR Level, Coat Weight | `TAU_IFACE_M` **110 nm** — a quarter of a visible wavelength | 1.0000 | **0.0918** |
| **coverage** | Base Colour | `TAU_OPTICAL_M` **3.1 µm** — optical depth ≈ 1 in carbon-black rubber | 0.9716 | 0.0034 |

`Metallic`, `Specular IOR Level` and `Coat Weight` were first driven by
*wetting*, which saturates at a monolayer. The tractive film is 10.6 nm, so it
came out 75 % "wetted" and was **turning brushed metal into a dielectric**: the
deck's film band measured **+52.2 %** against a launch mark of **+23.2 %**. A
tractive film cannot out-read a burnout, and a 10 nm transfer film does not stop
a metal being a metal. Those three channels are properties of the Fresnel
interface, and a film only owns the interface once it is thick against a quarter
wave. See R2-1221.

So the launch patch is a black mark **and** the tractive film is a 75 %-wetted,
zero-pigment gloss change, from one derived density field with no art fudge.
And that is what a fresh rubbered-in acceleration zone looks like in life: not a
stain — a satin band that goes dark at grazing. It is also exactly the channel
R2-1213 found missing: `M_Surf_Concrete`'s Specular IOR Level is flat 0.32 and
the existing mark never touches it.

### `Traffic Passes` — the one art knob, and it has a unit

The physics is unambiguous and unwelcome: **3 % tractive slip over 34 m leaves
~10 nm of rubber, which changes no surface's albedo measurably.** The derived
single-pass film's entire read is therefore in gloss.

`Traffic Passes` is the honest place to put the decision that follows. It is the
number of equivalent tractive-slip passes the surface carries, it multiplies the
film's areal density linearly, and **N = 1 is exactly this car, once**. The gate
renders N = 1 and N = 60 side by side so the cost of the decision is a measured
number instead of an argument.

---

## 3. The octave law, in both directions

Every structure this module authors lives in **12 mm … 300 mm**, inside the
resolvable band on every relevant surface at both 4K and 720p.

**Amplitudes.** All seven authored relief stages get their millimetres from
`K.relief_amplitude_for(m, wavelength_m)`. `selftest [4]` PARSES this file with
`ast` and fails if any `.bump(...)` call carries a typed `distance=` or is
missing `modulation_pp=`. A grep cannot do that job here, because the docstring
quotes `build_surface`'s own `distance=0.0030`.

**Fractals — and this is the part no module in this repo currently gets right.**
`ShaderNodeTexNoise` with `Detail = d` emits d+1 octaves at λ, λ/2 … λ/2^d. A
120 mm noise at the house default `detail=6` is *also* emitting a 1.9 mm octave
and a 0.94 mm octave — six times below the 12 mm floor and below the 2.4 mm
"material only, never pattern" line on every surface in the staging doc's band
table. Those octaves cannot reach the image at any resolution this film is
graded at, and they are not free: with the house defaults, **one 4K frame of the
concrete arm did not finish in ten minutes** on this box's CPU.

So `detail_for(λ)` derives the octave count and holds the finest octave at or
above the band floor. Measured finest octave over all 12 textures in the file:
**12.00 mm against a 12 mm floor.**

**And the sign.** On the concrete the deposit *reduces* relief, because rubber
fills texture. Both `M_Surf_Concrete` stages are modulated down — measured off
`build_surface.py:2887-2888`'s own `strength`/`distance` pairs, which reproduce
the staging doc's reported m = 3.15 and 3.29 to three digits:

| substrate stage | λ | amp | m | reduced by up to |
|---|---:|---:|---:|---:|
| micro | 2.29 mm | 0.270 mm | 3.141 | 55 % |
| aggregate | 24.11 mm | 3.000 mm | 3.292 | 90 % |

The 2.29 mm stage is below the band on every surface *and* carries m = 3.15.
Suppressing it is a move toward the law, not away from it.

---

## 4. No repeated assets

Four instances, eight independent hashed draws each — density gain, lateral
centre offset, patch width, rib weight, rib phase, graining phase, a full 3-D
noise origin, and edge hardness. `K.hash01`'s murmur3 finaliser is what stops
seven properties of one instance collapsing onto one value.

    gain         1.0274  0.9057  1.0953  0.9707
    dy (m)       0.0022  0.0008 -0.0022  0.0045
    width (m)    0.2514  0.2529  0.2443  0.2504
    rib_w        0.2684  0.3122  0.3276  0.2705
    edge (m)     0.0154  0.0121  0.0106  0.0113
    closest pair of noise origins: 9.85 m apart

The gate MEASURES the spread between the two launch patches off a rendered
ortho field probe. It does not claim it.

---

## 5. Wired by name

Not one shader socket in this file is addressed by index. Blender 5.2 has
Principled `[4] Alpha [5] Thin Wall [6] Normal` — R2-057 wired nine bump chains
into Thin Wall — and Bump has `[2] Filter Width` in front of `[3] Height`.
Everything goes through `NT.pin_named` / `NT.bump` / `_set_named` / `_o(node,
name)`; `ShaderNodeMix` A/B go through `NT.cmix`/`NT.fmix`, which pin 6/7 and
2/3.

---

## 6. The R2-651 guard

The field is world-locked, so it can only be right where the driven line is
straight. Measured on the tracks JSON: **inside x ≤ 63.5 the rear wheel's y is
EXACTLY ±0.79750 — max deviation 0.0000 mm over 272 samples. The first sample
outside, at x = 63.536, is already 6.55 mm off.** `FILM_X_END = 63.5` and
`_dep_relief` raises rather than extrapolate.

itemkit forbids world-space texturing because at |P| ~ 1000 m a float has
~0.06 mm left. Over |x| ≤ 63.5 m a float has 3.8 µm, which is why world space is
safe *here* and only here. The gate renders the field through a **12°-yawed**
object — the turntable deck's real yaw — and measures that the mark still lands
at world x = −1.80000.

---

## 7. Corrections to the staging diagnosis

Recorded here rather than in `docs/DEFECT-LOG-R2.md`, which has one owner. All
four are `[FINDING]` lines in `--selftest`.

1. **The areal ratio is 1/460, not 1/140.** Launch: 3.290344 m over
   0.2416 × 0.2511 m = 54.237 m/m² mean, 122.534 m/m² peak. Film: 1.0 m over
   33.7894 × 0.2511 m = 0.11786 m/m². Ratio 1/460.2 against the mean, 1/1039.6
   against the peak. The brief's 1/140 is 34/0.2416 — the *length* dilution,
   with its own "about 30 % of the launch's 3.29 m" factor dropped. Its two
   sentences disagree by 3.3×.
2. **`launch_mark_profile` contradicts `launch_mark.decay_note` in the same
   JSON.** The 256-point resample's last sample is 0.00000; `decay_note` says
   the mark "terminates at 2.7 % of peak … a hard trailing edge, not a fade" and
   `terminal_deposit_norm` is 0.02671. The resampler fades the last 12.3 mm to
   zero. **This module uses the per-frame arrays**, and anyone else consuming
   that JSON's resample will silently lose the feature the brief calls the
   distinguishing one.
3. **The derived tractive film is FLAT.** kappa varies by **0.304 %** across
   x = 15…49 — the exact span over which `build_surface.py:2836` ramps its paint
   linearly from 1.0 to 0.0. The existing falloff is not weak; it is the wrong
   *shape*, and there is no falloff to author.
4. **The octave law was being broken by the fractals, not only by the
   amplitudes** (§3). This is not specific to this block; it applies to every
   `detail=6`/`detail=8` noise in the repo.

---

## 8. What is NOT claimed

- The deck patch is **not** the biggest lever. It is exposed for five frames at
  ~3.5° grazing. It is built because it is the only physically derived mark in
  the film and because a static one would be a beat-1 defect. The gate's 30°
  camera on it is a **diagnostic** angle and is labelled as such.
- The floor application is **not** presented as physically derived. The derived
  deposit over x = 6.3 … 15 is the tractive film and nothing else; no launch
  mark lands there. `Floor_Datum_Ring`, a steel inlay standing 3 mm proud at
  x = 7.300, crosses the wheel line and will appear in any crop of that surface.
- The substrate materials in this file are **reduced replicas** for the gate
  only. They carry the real Principled parameters and the concrete's measured
  ±14.5 % per-bay tone hash — that is the number the deposit has to beat — but
  they are not a re-authoring of anything and nothing outside this file sees
  them.

---

## 9. The gate

`--gate` renders and measures; it asserts nothing.

- **[A]** the `relief_budget` table for every authored stage, with band verdict
  and the 12–300 mm window check;
- **[B]** an ORTHO top-down field probe over an exact world window, through a
  12°-yawed object: where the mark really is, its length, its width, its
  per-patch spread, and the time gate at three `Front X` values;
- **[C]** per substrate, at the **4K pixel law** and matched camera and matched
  exposure: control
  vs deposit vs traffic (vs the existing paint, on concrete), as a per-pixel
  ratio inside the deposit's own measured footprint; the substrate's own
  variation on the same pixels; the roughness / metallic / specular / coat
  fields themselves rendered as emission and differenced; and pure-black
  percentage on the delivered 8-bit AgX frame at an exposure solved so the
  CONTROL arm sits at the film's measured operating point;
- **[D]** `ShaderNodeTexImage` count and `K.assert_no_external_assets`.

**On "4K pixel law" rather than "4K frame".** `resolution_x` stays 3840 and the
measured scale stays **2.705 mm/px** on the apron — against the staging doc's own
apron-near p50 of 2.73 mm/px — so every pixel figure here is a real 4K pixel
figure. What `RENDER_BORDER` does is stop Cycles path-tracing the 66 % of the
frame that carries neither deposit nor measurement. The reason is the machine,
and it belongs in the record rather than hidden: this box has **six cores**,
`nvidia-smi` could not open its GPU ("Unable to determine the device handle for
GPU0"), and three other agents' item gates were rendering on it throughout — a
full 4K frame of the concrete arm was taking of the order of half an hour.
R2-020's rule is that the RESOLUTION must not be quietly halved; cropping the
traced region touches neither the resolution nor the pixel law, and halving
`resolution_x` would touch both.

Measured numbers are appended to
`docs/STAGING-R2-1211-to-R2-1240.md` and written to
`render/items/tyre_deposit/gate.json`.

---

## 10. Measured (gate run 2026-08-07, 4K pixel law, 20 spp)

> **RE-MEASURED AND REINSTATED (concrete).** The tables below were first taken
> with the default Cube in the scene; every concrete figure moved by less than
> 0.13 pp when it was removed and no conclusion changed. The deck tables were
> a photograph of the Cube and are still being re-measured. `--factory-startup` is not an empty
> scene: it holds a 2 m Cube at the world origin, `itemkit.purge(prefix)`
> correctly refuses to delete datablocks it does not own, and the deck's
> measurement scene is centred on (0, 0, 0.340) — on top of the Cube. A probe
> emitting a constant 0.86 read back a mean of **5.390** over 99.7 % of the
> deck frame; after `_empty_the_scene()` it reads **0.86000** over 100 %. The
> concrete scene at x = 32 had the Cube 40 m away but still inside the tyre
> band's y range, so its numbers are retracted too. See R2-1220 in
> `docs/STAGING-R2-1211-to-R2-1240.md`.

### The field, through a 12°-yawed object

| | measured | declared |
|---|---|---|
| mark, world x | −1.80706 … −1.55134 | −1.80000 … −1.55840 + the 11–15 mm hard edges |
| RL patch centre, world y | **+0.79987** | +0.79750 + its own 2.2 mm jitter = +0.79970 |
| RR patch centre, world y | **−0.79674** | −0.79750 + its own 0.8 mm jitter = −0.79670 |
| patch width | 265.7 / 264.1 mm | 251.1 mm + edge |

Both within 0.4 mm — half a probe pixel. Per-instance spread between the two
launch patches: peak **6.40 %**, mean **10.74 %**, width **1.56 mm**, lateral
centres +2.37 / +0.76 mm; closest pair of noise origins **9.85 m**.
Time gate before frame 818: max density **0.0**, lit pixels **0**.

### Rough concrete — the apron

340 485 px of footprint, 2.71 mm/px, 30° grazing, identical camera/sun/seed so
the ratio cancels the lighting exactly.

| arm | mean | p50 | band-vs-shoulder | p99.5 lateral gradient |
|---|---:|---:|---:|---:|
| derived film, N = 1 | +0.71 % | −0.91 % | +1.70 % | **1.067 %/mm** |
| derived film, N = 60 | −4.21 % | −7.35 % | −4.13 % | **1.605 %/mm** |
| `build_surface`'s existing paint | −18.79 % | −18.73 % | −17.49 % | **0.243 %/mm** |

| channel | control | deposit | delta | existing |
|---|---:|---:|---:|---:|
| Roughness | 0.8002 | 0.6664 | −16.7 % | −0.0773 |
| Specular IOR Level | 0.3200 | 0.3315 | **+3.6 %** | **+0.0000** |
| Height Coarse sd | 0.18572 | 0.15757 | −15.2 % | **0.0 %** |

Pure black, delivered 8-bit AgX at the solved exposure: **0.0000 % on every
arm.** `ShaderNodeTexImage` count **0**.

**WITHDRAWN — see R2-1233.** This section originally concluded "the conclusion
is not the mean, it is the edge", on a 4.4×/6.6× lateral-gradient advantage.
R2-1225 rendered the same comparison **in the film** and measured **0.324 %/mm
(existing) against 0.319 %/mm (deposit) — no advantage at all**. A gradient is
amplitude over distance; the transition IS shorter, but this replica gave the
deposit ~20× more amplitude than the real `M_Surf_Concrete` does (−4.35 % here
vs −0.20 % in the film), because it carries that material's Principled
parameters and bay-tone hash and none of its crazing, efflorescence, joints or
grit. What survives is geometric: **containment, 119 mm at half depth against
the paint's 379 mm**, and the mark being where the wheel actually was. In the
film at 1:1 the deposit could not be found. The existing mark is a 640 mm
feathered wash with a 0.24 %/mm edge on a surface whose own bay hash swings
±14.5 % — it reads as mottle at any amplitude. And the physically derived single
pass is **+0.71 %** (p50 −0.91 %, i.e. straddling zero): 3 % slip over 34 m transfers ~10.6 nm of rubber, which
changes no albedo at all. **No pigment on that apron is derivable from this
car's single pass.** `Traffic Passes` is where that decision belongs.

### Cost

One arm of the bare concrete substrate: **2 min 00 s**. The same substrate
carrying the deposit field: **12 min 05 s** — **6.0×**. Four instances × four
fractals is inherent to "no repeated assets" and a shader cannot branch past an
instance whose lateral band is zero.

### Polished floor — measured, and the sign is BRIGHTER

3.32 mm/px (doc p50 3.31), 25° grazing, 282,199 px, three-scale model.

| arm | mean | p05 | p50 | p95 | gradient |
|---|---:|---:|---:|---:|---:|
| derived film N=1 | **+3.06 %** | −0.57 % | +2.98 % | +7.04 % | 0.371 %/mm |
| derived film N=60 | −1.41 % | −12.77 % | +0.24 % | +3.92 % | 0.417 %/mm |

| channel | control | deposit | delta | driven by |
|---|---:|---:|---:|---|
| Roughness | 0.0975 | 0.2373 | +143.4 % | wetting |
| Coat Roughness | 0.0450 | 0.1555 | +245.5 % | wetting |
| **Coat Weight** | 0.4500 | 0.4366 | **−3.0 %** | **interface** |

**Pure black 0.0000 % on every arm**, and the deposit **raises** the darkest
in-footprint pixel (0.06138 → 0.06166). Exposure solved so the control arm sits
at the film's measured 0.10 operating point (−5.546 EV → 0.1005).

Under the superseded wetting-driven model coat weight fell 0.45 → 0.2401 (47 %
suppression); under the corrected model it is 3.0 %. The deposit stopped being
"the coat removed" and became "the coat broadened", and those have **opposite
signs** at an off-specular view. **This does not license relaxing the coat cap**
— the cap is inert here only because nothing on this floor is optically thick,
and it is the only guard once a real mark lands on a coated dielectric.

**Every derived deposit in this film is a brightening** (deck +23.2 %, floor
+3.06 %, apron +1.56 %). The only darkening in the block is the hand-painted
apron streak, which is also the only thing not derived from the telemetry.


### Concrete, re-measured under the three-scale model (supersedes the table above)

| arm | mean | p05 | p50 | p95 | (superseded) |
|---|---:|---:|---:|---:|---:|
| derived film N=1 | **+0.71 %** | −7.87 % | **−0.91 %** | +13.29 % | +1.56 % |
| derived film N=60 | −4.35 % | −20.88 % | −7.62 % | +18.69 % | −4.33 % |
| existing paint | −18.82 % | −25.69 % | −18.75 % | −11.93 % | −18.82 % |

Specular IOR Level 0.3200 → **0.3315 (+3.6 %)**, down from +31.4 %; Roughness
(−16.7 %) and Height Coarse are bit-identical across the model change, as
wetting-driven channels must be. The existing paint is unchanged to four digits
— a useful null, since no field touches it.

**The apron result gets weaker, and that is the honest direction.** +0.71 % mean
with a p50 of −0.91 % straddles zero. A 10.6 nm film owns 9.2 % of the Fresnel
interface and none of the albedo; what remains is a roughness change alone.

**Correction against this module's own interest:** an earlier note said the
deposit raises concrete's darkest in-footprint pixel. Under the corrected model
it does not — 0.22335 → **0.21804**, lowered, because the spurious specular lift
is gone. Pure black stays **0.0000 %** on all four arms and 0.218 is nowhere
near zero, but the claim was an artefact of the bug and is withdrawn. The
floor's lift (0.06138 → 0.06166) was measured under the corrected model and
stands.

### Brushed metal (deck) — confirmed under the three-scale model

1.31 mm/px, 30° diagnostic grazing, 540,784 px footprint of which the two launch
patches are 13,112 px (0.46 %).

| region | superseded | corrected |
|---|---:|---:|
| **the launch patches** | +23.2 % | **+23.18 %** — unchanged, as predicted |
| whole footprint, N=1 | +52.2 % | **+10.90 %** — the artefact collapses |
| whole footprint, N=60 | — | **+84.19 %** |

Independent check: `Traffic Passes` scales only the film, so the two arms' mark
regions must agree — measured **+23.18 %** vs **+23.19 %**.

| channel | control | deposit | delta |
|---|---:|---:|---:|
| Roughness | 0.3935 | 0.4975 | +26.4 % (wetting) |
| **Metallic** | 0.8600 | **0.8156** | **−5.2 %** (interface; was driving to 0.25) |

Pure black **0.0000 %** on every arm; the deposit **raises** the darkest
in-footprint pixel, 0.15861 → 0.18188.

### `Traffic Passes` is a PER-SURFACE quantity — do not make it global

At N=60 the film is 636 nm, thick against a quarter wave, so `Interface`
saturates and the film legitimately kills the deck's metallic character —
an **+84 % bright band across the turntable**. The physics is right; applying it
there is not. A showroom display turntable has not been driven over sixty times;
an access road plausibly has.

- **deck: N = 1, by construction.** The car drives off it once.
- **floor: N = 1**, same reason.
- **apron: N is the open question** — the only surface that is a public road.

`FILM_TRAFFIC_SWEEP = 60` exists only as a gate arm. If it ships it ships as a
per-material argument on the apron alone. A single global knob would have put an
84 % stripe on the turntable while fixing the apron, and only the deck arm makes
that visible.

### A judgement call to make deliberately

The deck's derived N=1 film band reads **+10.90 %**, against the floor's +3.06 %
and the apron's +0.71 % — the same 10.6 nm film, shown 3.6× more strongly than
the floor and 15× more than the apron, because a roughness change on a dark
conductor moves more radiance than the same change on a coated dielectric or
matte concrete. The brief asks the film to "read as a faint continuous tint,
never as a mark". **+10.9 % is at the upper edge of faint**, on a surface that is
23.9 % of the frame at p50. It is derived, not painted — but it should be looked
at in the 4K A/B rather than assumed acceptable because the physics produced it.

---

## 11. Limits of this gate — read before quoting any number above

`--gate` measures what the shader **does**: a channel delta, a world-space
position, a saturation law, a time gate, a relief amplitude. Those are sound.

It cannot measure what the material **reads like**. Reading is contrast against
the rest of the surface, and the rest of the surface is exactly what a reduced
replica leaves out. `_concrete_substrate` carries `M_Surf_Concrete`'s Principled
parameters and its ±14.5 % bay hash and **none** of its crazing, efflorescence,
joints, grit or per-slab segregation — so it gave the deposit roughly **20×** the
amplitude the real material does (−4.35 % here against −0.20 % measured in the
film, R2-1225).

Consequently:

- **Signs are defensible.** They rest on shading physics the substrate does not
  change: a conductor has no diffuse lobe wherever you measure it, and a coat
  that is not suppressed cannot darken by being suppressed.
- **Magnitudes are upper bounds** until measured in the film, on every substrate.
- **Contrast statistics from this gate should not be quoted at all.** The
  withdrawn 4.4×/6.6× edge claim was a ratio whose denominator was the thing the
  replica omitted.

The one measurement still worth renting a GPU for is the **deck's launch patch**:
the only optically thick mark in the block, the only place the derived physics
has real amplitude, and never yet in frame in the film (at f981 the patches are
31 m behind the car).
