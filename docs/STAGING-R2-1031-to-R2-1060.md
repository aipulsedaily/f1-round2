# STAGING R2-1031 … R2-1060 — the circuit surface (task #127)

Owner: the asphalt/wearing-course pass. **`DEFECT-LOG-R2.md` is not edited by this
file's author** — everything here is staged for whoever owns that log.

Scope: `world/build_surface.py` `_mat_asphalt()` and two gates the module did not
have. No mesh, no contract, no telemetry, no camera.

---

## R2-1031 — the surface is not untextured; its detail is authored in octaves the film's camera cannot resolve, and the relief law says so in numbers

The complaint ("reads as untextured, no asphalt detail, no rubbered-in racing
line") is **true at the delivered frame and false about the material**. The
material has 20 procedural layers and 617 lines of shader. What it does not have
is anything in the octave band this film photographs the road at.

Four independent lines, none of which is "I looked at the graph".

### (a) what distance does the camera actually see the road at — measured

`render/r2651/track_scale.json`, 1 888 frames in which the road covers ≥ 2 % of
the delivered frame, **weighted by how much of the frame it covers**:

| | p5 | p25 | p50 | p75 | p95 |
|---|---:|---:|---:|---:|---:|
| distance to surface | 16.2 m | 59.1 m | **125.9 m** | 486.9 m | 1017.7 m |
| mm of surface per 4K pixel | 3.82 | 10.82 | **20.75** | 108.10 | 282.96 |

92.6 % of the film's road pixels are beat 5. A feature reads between roughly
2 px and 30 px, so **the film's own readable band on this surface is 40 mm to
2 m** — and at p25 it is 22 mm to 320 mm.

### (b) the layer census against that band — arithmetic, from the source

Wavelengths quoted as `itemkit.bump_relief_report` reads them
(`NOISE_WAVELENGTH_FACTOR` 1.60 / scale, `VORONOI_WAVELENGTH_FACTOR` 2.17 /
scale). *Reading `1.0/scale` instead — the obvious thing — makes every Voronoi
layer 2.17× too fine, and an earlier census in this module's own comments did
exactly that.*

| where | layers |
|---|---|
| ≥ 2.9 m | macro2 222 m, cover 76 m, macro 53 m, snake 29 m, patch 29 m, pour 21 m, dust 7.3 m, flush 4.7 m |
| **40 mm – 2 m** | **`mott` 1.03 m — carrying a 0.22 tint. That is the whole list.** |
| ≤ 103 mm | pluck 103, warp 67, agg0 66, agg 39, aggb 19, agg2 9.2, grain 3.7, micro 1.0, bead 0.9 |

Eight layers above the readable band, nine below it, **one inside it**. The gap
runs 103 mm → 1.03 m, which at p50 is **5 px to 50 px** — the centre of
legibility.

### (c) the delivered frames, at 4K, at 1:1 — and the atmosphere ruled out

R2-655 rendered four film-pose frames at 3840×2160 / 512 and wrote *"these are
the before, and no change should be made until they have been looked at at
1:1."* They had not been. They now have.

* **`before_f2225.png`** (21.0 mm/px) — the road is a **dead smooth cream
  ribbon**. The kerb reads, the paint reads, the asphalt has nothing.
* **`before_f1547.png`** (11.8 mm/px, the sharpest look at the surface in the
  whole film) — a **uniform sandpaper stipple**: every chip the same size, the
  same brightness, evenly spaced over the entire frame, with no structure at any
  larger scale. This is the "one tiling noise over 5 km" failure, at chip scale.

**The R2-652 escape hatch is closed by its own control.** That finding correctly
sent the last asphalt complaint to the camera department, so the same
possibility had to be excluded before touching the material.
`tools/r21031_octave_contrast.py` (new; five controls, two of which it must
fail) on **f2225, one frame, same depth, same haze**:

| patch | 4 px | 8 px | 16 px | 32 px |
|---|---:|---:|---:|---:|
| kerb stripes — **atmosphere control** | 0.0175 | 0.0206 | 0.0336 | **0.0545** |
| asphalt (see the correction below) | 0.0109 | 0.0118 | 0.0163 | **0.0191** |
| flat test-harness ground | 0.0023 | 0.0005 | 0.0003 | 0.0001 |
| sky — **null control** | 0.0018 | 0.0004 | 0.0002 | 0.0001 |

Contrast **survives** the haze at that range: the kerb carries **2.9×** the
road's at both the 335 mm and 670 mm bands. The road is smooth because the
material is smooth.

### two corrections to the above, found by checking what the pixels actually were

Both are mine, both were in the first draft of this note, and both are the same
mistake — **naming a patch by what it looks like instead of by what it is.**

1. I recorded the fourth row as *"the runoff terrain measures as flat as the
   sky — a worse defect, belongs to `build_terrain`."* **It is not terrain.** A
   raycast of the camera says that patch is **100 % `TEST_Ground` /
   `TEST_GroundMat`**, the test harness's own flat grey card. `build_terrain` is
   not in this blend at all. There is no terrain finding here and the sentence
   is withdrawn.
2. The asphalt row above is **62 % asphalt, 26 % test ground, 11 % kerb**. The
   number is contaminated and is superseded by the pure-asphalt measurement in
   R2-1036.

Every patch quoted from here on is verified by raycast against the built scene,
and the rects are chosen by `tools/r21031_asphalt_mask.py`'s largest-all-asphalt-rectangle
rather than by eye. f1547, f1226 and f2000's original patches came back
93–100 % asphalt, so the diagnosis itself stands; f2225's did not.

### (d) the relief law — and this is the part that names the mechanism

`itemkit.relief_budget` on the **shipped** bump stack, at the film's own
12.471° sun, conservative `height_pp = 1.0`:

| stage | λ | amp | slope | m | vs `isotropic_macro` 0.35–0.95 |
|---|---:|---:|---:|---:|---|
| micro | 0.62 mm | 0.147 mm | 36.5° | **5.374** | **HIGH** |
| grain | 2.33 mm | 0.754 mm | 45.5° | **6.453** | **HIGH** |
| h_meso | 17.86 mm | 5.500 mm | 44.1° | **6.289** | **HIGH** |
| mott | 645 mm | 1.400 mm | 0.4° | **0.062** | **LOW** |

**The three layers the film cannot resolve run 4×–18× OVER the accepted
modulation. The one layer in the octave it can resolve runs 6×–26× UNDER it.**

This is the 122-stage dead bump stack again in a form no node-count check could
ever see: **nothing is disconnected — every stage is wired, every socket fed by
name — and the relief is still doing nothing, because all of it is spent where
the camera is not.** A 44° mean slope at 18 mm is not aggregate, it is
sandpaper, and sandpaper is exactly what f1547 shows. The source comment above
those stages says they are *"deliberately weak … keep them quiet"*; they were at
m = 5.4.

**Recorded as the general result:** a bump stack can fail exactly as completely
by misallocation as by disconnection, and only a *physical* audit distinguishes
the two. A wiring check passes both.

---

## R2-1032 — what was built, and the rule that decides where relief is allowed to be the answer

### the missing octaves, as five different structures

Five draws of one noise at five scales is "one tree spammed a hundred times"
moved into texture space, so these are five different *kinds* of thing, chosen
because a dense-graded wearing course really carries them there:

| layer | λ | px @ p50 | what it is |
|---|---:|---:|---|
| `nest` | 0.150 m | 7.2 | aggregate clustering — stone-on-stone contact zones, mortar-rich ground between. Turns an even stipple into grouped stones. |
| `seg2` | 0.300 m | 14.5 | the paver's auger starving and flooding the mat: chip-rich pale patches, mortar-rich warm ones |
| `pick` | 0.400 m | 19.3 | rubber pick-up mottle — rubber does not lay evenly |
| `screed` | 0.444 m | 21.4 | the screed's transverse corrugation. **The only thing in the material that runs across the road**, so it breaks the longitudinal grain of the streaks, the lane joints and the band at once |
| `craze` | 0.658 m | 31.7 | fatigue cracking as a **cell network** — distinct from `snake`, which is the 29 m sealant line laid over it later |
| `ravel` | 0.986 m | 47.5 | fretting: mortar stripped, coarse stone standing proud, paler and rougher |

`ravel` and `screed` are gated on `offline` (distance from the driven corridor in
units of the corridor's own width) because that is physically where they survive
— inside the corridor the tyres knead the mortar back and polish the ripple flat.
`craze` is gated on `rubber`, which is the telemetry's own load field.

### the mechanism, which is not relief

**These layers survive distance by modulating the amplitude of the aggregate, not
by having relief of their own.** At 21 mm/px an 18 mm chip is sub-pixel, so the
pixel receives the chip field's local *mean*; if the chip field's amplitude
varies at 0.3 m, the delivered pixel varies at 0.3 m. That is `amp_field`, and it
is a texture-of-texture — which is also **why it survives AgX where a flat albedo
step does not.** R2-654's measured 1.9 : 1 display ceiling is a ceiling on
*levels*.

### the rule the law forced

`relief_amplitude_for` says reaching `isotropic_macro` at 1.03 m needs **13.7 mm**
peak-to-peak, and at 0.45 m needs 17.6 mm. **A road that waved 14 mm every metre
would be unraceable.** So the budget carries two kinds of stage:

* **`"m"`** — aimed at a radiance modulation, gated inside its band **both ways**;
* **`"mm"`** — bounded by the object, gated against a physical amplitude, with the
  modulation it delivers *reported* rather than targeted.

The two kinds **agree wherever both apply**, and that is worth more than either.
Every band-aimed stage came out at an amplitude a real wearing course has —
0.05 mm of grain, 1.16 mm of chip proud of the mortar, 2.9 mm of stone nest,
4.2 mm of segregation, 9.1 mm of sawn joint — **without any of those numbers
being chosen**. Law and object diverge only above 0.6 m, which is exactly where
the `"mm"` stages begin.

### the budget, read back off the built graph

Not off the plan. `_RELIEF_PLAN` and `relief_amplitude_for` are the same function
evaluated twice and comparing them is an algebraic identity — itemkit's own
`emitted_wavelength_m` docstring says precisely that about the check that let
R2-058 live for as long as it did.

```
=== asphalt relief budget, read back off the built graph ===
  Bump       fine         lam     3.72 mm  amp  0.0524 mm  m  0.4000  isotropic_micro        ok
  Bump.001   aggregate    lam    38.75 mm  amp  1.1645 mm  m  0.8500  isotropic_macro        ok
  Bump.002   hard         lam   103.33 mm  amp  9.0538 mm  m  2.4000  hard_feature           ok
  Bump.003   nest         lam   149.66 mm  amp  2.9025 mm  m  0.5500  isotropic_macro        ok
  Bump.004   seg2         lam   300.19 mm  amp  4.2306 mm  m  0.4000  isotropic_macro        ok
  Bump.005   craze        lam   657.58 mm  amp -3.0000 mm  m -0.1296  physical 1.0-15.0 mm   ok
  Bump.006   waviness     lam  1032.26 mm  amp  4.0000 mm  m  0.1101  physical 0.5-8.0 mm    ok
>> STAGE RESULT: asphalt_relief_budget PASS  (7 stages, 0 out of band)
```

Seven stages spanning 3.7 mm to 1.03 m instead of four clustered at ≤ 18 mm and
one orphan at 645 mm.

### two structural changes the budget forced

* **The 0.6 mm stage is gone, and not because it was too strong.** Below the ray
  footprint a normal perturbation is not geometry, it is a BRDF: Cycles samples
  it at random inside the pixel and the denoiser turns the variance into swirls.
  Sub-footprint texture's physically correct home is **roughness**, and that is
  where it went. 0.6 mm is under the footprint at every station in this film bar
  the closest, where it was generating m = 5.4.
* **Hard features got their own stage.** A sawn joint, a saw kerf, a planer lip
  and a pluck socket are *edges* — `hard_feature`, 1.50–6.00 — and riding them on
  the aggregate's amplitude meant either the stone was sandpaper or the joints
  were invisible. They are now budgeted at **the width of the cut**, not the
  spacing of the cuts.

---

## R2-1033 — `relief_gate()`: the audit reads the graph, and it fired three times before it passed

New, runs on every `build()`. It fails on a stage whose Height is unlinked (the
dead stack), on a stage whose Height is driven by another Bump (height and normal
chain crossed — the R2-038 shape), and on a stage outside its band **on either
side**.

It also fails **UNPLANNED**: any stage whose read-back wavelength matches no plan
entry. That clause is the load-bearing one and it caught all three real defects:

1. **The aggregate stage was being audited at 18.8 m.** `bump_relief_report`
   walks back from Height depth-first, *last input first*, and stops at the first
   texture it meets. Every modulation on `h_meso` (rubber, flush, runnel, ravel,
   crazing) has a texture behind it, so the walk reached `craze_cover`'s 18.8 m
   coverage noise and reported the 38.8 mm aggregate stage at **m = 0.0018 — a
   470× error, in the direction that makes a HIGH stage look dead.**
2. The same on the crazing stage.
3. The screed stage reads **1.6 m** rather than its true 0.44 m, because its
   coordinate is built in a `CombineXYZ` from two Math nodes and `_vector_gain`
   cannot see the 3.60 — itemkit's own documented trap, from the other side. It
   is audited at `seg2`'s 0.30 m, which is the branch the walk enters, and that
   is **stated in the source rather than left to be discovered.**

The fix is that every audited Height puts its own texture in argument 1. That is
a coupling to another module's traversal order and is **not defensible on its
own**; what makes it safe is that the UNPLANNED clause turns a change in that
traversal into a loud failure instead of a silent audit of the wrong octave.

---

## R2-1034 — the "patches in the land" mechanism was live in the asphalt too

The milled repairs ramped the Voronoi cell distance `0.42 → 0.30` on a 13.3 m
cell — a **1.6 m wide feather all the way round**. What that renders as is a soft
pale cloud, which is the client's rejected "patches in the land" arriving here by
the same mechanism, in a different module. The pale blobs on `before_f2000.png`
are these.

A planer leaves a cut you can put a straightedge against. Two changes: the
boundary is warped at 1.4 m so it is not a smooth Voronoi arc (a planer works in
passes and leaves a stepped outline), and the feather is **0.13 m** with a sealed
40 mm lip round it — the same treatment the sawn patches already had and the
milled ones did not.

**A repair has an edge, and that is the whole difference between a repair and a
stain.**

---

## R2-1035 — the racing line still disagrees with the telemetry by 4.885 m, and now something will say so

R2-651 measured this, routed it to the telemetry owner, and there it stopped —
with nothing anywhere that would notice a regression *or a fix*. Re-measured
today by an independent path (`world_contract.project` over `telemetry.csv`,
1 524 lap samples):

| | |
|---|---:|
| car's `\|u\|` from the centreline, p50 | **0.0026 m** |
| painted band's `\|u\|`, p50 | 4.883 m |
| **disagreement, p50** | **4.885 m** |
| disagreement, p90 | 6.446 m |
| disagreement, max | 7.144 m |
| bar (0.55 × min spread = the narrowest heart) | 0.830 m |

`telemetry.csv` is unchanged since 2026-08-02, so R2-651's finding stands
verbatim: the car drives the geometric centreline for the entire lap while the
rubber sweeps side to side five metres away.

**Deliberately not fixed here, and that is the same decision R2-651 recorded.**
Moving the rubber onto `u ≈ 0` paints a straight band down the middle of every
corner, which no circuit has; re-solving the telemetry moves picture against
sound in a film with no cuts. Both repairs belong to other owners. What this
module can honestly do is **refuse to be silent about it**, which is
`racing_line_telemetry_gate()` — it prints a `>> STAGE RESULT:` line on every
build and currently FAILs.

Worth restating from R2-662, because it is what makes this urgent rather than
academic: the **one** condition in which the band is legible at all is the camera
inside 20 m of the surface, which is the onboard and chase material — precisely
the frames in which the audience can also see where the tyres are.

`_load_telemetry` now carries `x`/`y`. The usage fields only ever read the
accelerations, which is exactly how the band could be five metres from the tyres
that laid it with nothing noticing.

---

## Instruments added

| tool | measures | a control it MUST fail |
|---|---|---|
| `tools/r21031_octave_contrast.py` | band-limited rms contrast per octave of a delivered frame, in delivered pixels | a linear ramp must return < 1e-4 — a crowned road under a low sun *is* a gradient in `u`, and this is R2-654's false positive in a different instrument; heavy blur must kill the fine octaves |
| `world/build_surface.relief_gate()` | every `ShaderNodeBump` in the built graph, through itemkit's law | a stage whose wavelength matches no plan entry; a dead Height; a crossed Height/Normal |
| `world/build_surface.racing_line_telemetry_gate()` | painted band vs driven line | — (a measurement with a stated bar) |

**The octave instrument failed its own controls first** and was fixed before it
was pointed at anything: band labelling was one octave out (a 16 px sinusoid
reported in the 8 px band) and a linear ramp returned 1.6e-3 of pure boundary
artefact from `mode="edge"` padding folding the ramp back on itself.

---

---

## R2-1036 — the A/B, at 4K, at 1:1, at matched camera and matched exposure

Four film poses re-rendered from `world/surface_test_filmpose.blend` at
3840×2160 / 512 through the same grade. **$0.0488 of GPU** (broker spend
$26.4084 → $26.4572; 175 s of 5090 across four frames).

**The pair is verifiably comparable.** The sky is untouched by this change, so
it is the control: before vs after sky mean agrees to **1e-6** on all four
frames. Same camera, same lens, same aperture, same exposure.

Measured on **raycast-verified 100 % asphalt rects**, rms contrast per octave:

| frame | mm/px | grazing (along/across) | 46-90 mm band | 180-370 mm | 700 mm-1.6 m |
|---|---:|---:|---:|---:|---:|
| **f2000** | 11.5 | 1.7 : 1 | **2.70× / 2.11×** | 1.45× | 1.26× |
| **f1226** (the wide) | 51.5 | 40 : 1 | 1.22× / **1.65×** | **1.90×** | **1.58×** |
| **f1547** (closest look) | 11.8 | 17 : 1 | 0.96× / 1.05× | 1.10× | 1.03× |
| **f2225** | 21.0 | 32 : 1 | 1.90× / 1.52× | 1.13× | 0.97× |

**And the frames, which are the arbiter** (`docs/peep/r21031/AB_*.png`, before
left, after right, 1:1):

* **f2000 — transformative.** Before: a flat cream plane carrying two hairlines
  and four soft pale amorphous blobs. After: a surface with aggregate and mortar
  structure, chip-rich and binder-rich patches, joints that read as sealed cuts
  with a dark line and a lighter shoulder — and **the amorphous blobs are gone**,
  because they were R2-1034's 1.6 m feather.
* **f1226 — clear.** Before: flat grey with one hairline. After: legible surface
  grain, mottling, and a joint with a real profile.
* **f1547 — better, and the metric understates it.** The contrast did not rise;
  it **moved**. The 46 mm band fell 0.96× and the 90-370 mm bands rose — which is
  exactly the trade that was bought: the sandpaper stipple broken down, the meso
  structure put in. Side by side, the uniform even speckle is replaced by patchy
  chip-rich and mortar-rich ground with a crack line running through it. **A
  single scalar would have called this "no change"; the crop pair does not.**
* **f2225 — genuinely little change, and the reason is not the material.**

### f2225, stated against myself

That road patch sits at **0.8617 display mean — 27× the linear level of mid
grey.** Measured off `render/r2651/agx.json`, this film's own transfer:

| road patch at | display / stop |
|---|---:|
| f1547 0.3188 | 0.1251 |
| f1226 0.3771 | 0.1393 |
| f2000 0.5656 | 0.1399 |
| **f2225 0.8617** | **0.0682 — 55 % of the others** |

The material's gain *is* there (1.90×, 1.52× in the fine bands) but it arrives on
a surface with **half the tonal headroom left**, at a 32 : 1 grazing
foreshortening. Whether that surface should be that bright is an exposure and
lighting question. **That is R2-652's finding, and this time it is correctly
applied — to one frame out of four, after the other three were shown to move.**
It is not a defence of the material, because the material did move here too; it
is the reason the movement does not show.

---

## R2-1037 — the mesh is bit-identical, checked rather than argued

The brief asks whether this breaks the module's bit-identical rebuild under
contract 1.2.0. **It does not**, and that is measured by building the module
twice in `--factory-startup` Blender — once from `git show HEAD:` and once from
the working tree — and hashing every mesh's vertex coordinates and loop indices:

```
HEAD          MESH_SHA256 27a25aaafe4d…fb570  objects=59  tris=2721445
working tree  MESH_SHA256 27a25aaafe4d…fb570  objects=59  tris=2721445
```

Identical. (2 721 445 − 12 for `--factory-startup`'s default Cube =
**2 721 433**, the contract's own figure, which is a free cross-check that the
hash is looking at the right geometry.)

This was checked rather than reasoned about, even though the reasoning is easy —
only `_mat_asphalt`, `_load_telemetry`'s return dict and two new gates were
touched, and none is on the geometry path. Reasoning is what R2-605 calls
"agreement with a document", and it is not verification.

---

## Still open, not mine

* **The racing line / telemetry disagreement** — R2-1035. Owner is task #19.
  `racing_line_telemetry_gate()` now FAILs loudly on every build.
* **f2225's road at 0.86 display** — R2-1036. Owner is lighting/exposure, not the
  surface. Flagged, not textured around.
