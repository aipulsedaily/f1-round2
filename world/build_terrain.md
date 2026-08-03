# build_terrain.py — landform, treeline, undergrowth, grass

`/home/zany/f1-round2/world/build_terrain.py` → collection `WORLD_TERRAIN`.
Headless, idempotent:

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio -P world/build_terrain.py
# build, measure against the contract, bake a FEW cameras, save:   (910 s, 1.07 GB)
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio -P world/build_terrain.py -- \
    --selftest --cams doppler,t5_verge,t10_rim \
    --save render/world/terrain/ter.blend
# ... or ONE 300 m window of verge at production density, for pixel work:  (40 s, 34 MB)
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio -P world/build_terrain.py -- \
    --macro doppler --half 150 --cams doppler \
    --save render/world/terrain/macro_doppler.blend
# render on the 5090 (never the 1070 unless the broker is down):
tools/r5090 render/world/terrain/macro_doppler.blend CAM_doppler \
            render/world/terrain/macro_doppler_after.png 512 3840 2160
```

`TERRAIN_FAST=1` (or `TERRAIN_QUALITY=0.3`) thins the scatter for local tests. It changes
counts only — never the design, never a single parameter of the geometry.

This file records the decisions a later reader would otherwise have to reverse-engineer,
and it is honest about what is approximated and where the spec was ambiguous.

---

## 0. WHAT CHANGED, AND WHY

The assembly review found that six modules had each been built and verified **in
isolation**, and that assembled they destroyed each other. This module was the worst
offender in finding #1:

> `TER_Ground` was the topmost surface over 5.3 % of the racing surface, up to **+0.381 m
> proud of the tarmac** at the T10/T11 banked sweeper; 42.3 % of the kerb-and-verge band
> was buried; and the entire runoff programme — 50 555 m² of asphalt, 42 419 m² of gravel
> and 240 000 individually generated stones — was under dirt.

The cause was a single line of design: **the height field was flat laterally.** It took
the centreline elevation `zr` and used `zr − 0.120` across the whole graded platform, so
it could not carry the crown, could not carry banking, and at 4° on T10/T11 the outboard
road edge is 0.66 m below the inboard one. Terrain then covered the runoff in dirt while
*deliberately* leaving that zone bare (`ter_wear` 0.85, no grass inside `PLAT`) because it
had assumed the paving would be on top. Two correct-in-isolation decisions producing "a
grass gray line" — the user's named red line, hit exactly.

`world/world_contract.py` now owns every number two modules share. This module was rebuilt
against it:

| what | before | now |
|---|---|---|
| the ground datum | `zr − 0.120`, flat laterally | **it has none.** `C.ground_z(s, u)` is the datum and terrain does not build ground where it applies |
| the corridor | a 34 m batter blend into a "platform" | **a hole.** `C.road_corridor_mask`, cut cell by cell, welded to `C.corridor_rim` |
| track half-width | `Circuit._half_width`, box-filtered → 15.00 m at s = 3115 | `C.half_width` → **16.00 m**, exactly, where the spec says so |
| runoff widths | `Circuit._platform`, a private table | `C.runoff_widths` / `C.platform_edge` |
| vegetation in the runoff zone | none — the zone was assumed to be paved over | **grass, weeds and stones, placed on `C.ground_z`**, cut out of the asphalt and the gravel beds by `C.runoff_widths` |
| the light materials were tuned to | §2.1's assumed rig (120 W/m², 3.0:1, AgX −2.70) | **`build_sky`, imported and run**; albedos checked against `C.lambert_radiance` |

§9 is the measured evidence that each of those actually landed.

### 0.1 What changed in THIS pass

The assembly verification found five new defects; two of them are this module's, and the
user raised the quality debt directly on a 4K frame. In order:

| # | what | before | now |
|---|---|---|---|
| **assembly #2** | the corridor mouth at the glass plane had no ground | three modules, three margins for one boundary; **1 276 of 7 467 samples (~64 m²) with no usable ground** at the Beat-3 → Beat-4 hinge | `ACCESS_RIBBON_T_MIN` pins the start cap at x = 15.000; keep-out and joint separated. **0 of 14 803 at the mouth, 0 of 47 433 along the whole ribbon corridor.** §2.3b |
| **assembly #4** | 658 m² of the road corridor with no ground | terrain cuts to `platform_edge`, barriers stops at `owned_edge` | measured and quantified (42 076 m² of shoulder owed, 1.6 % missing). **Terrain's rim has not moved and cannot fill it without a coplanar z-fight — this one is `build_barriers`'.** §2.4 |
| **user** | *"the grass is blurry … we need max detail max models detail"* | flat 2-vertex ribbons, 6.0–11.0 mm wide, 211 polys/clump | channelled 3-vertex blades in tillers, 3.4–6.6 mm, **2 914 polys/clump**, with an understorey. **Blade-edge spectral energy ×1.59 at the doppler hover.** §5.5, §9.2b |
| **user** | *"bare ground is a flat sandy plane with no stones or clods"* | measured local σ **6.25/255 at mean 108.4 = 5.8 % relative** over a metre of escarpment; everything under 0.4 m was a bump map | `build_grit`: chips, stones and soil clods as real half-buried meshes, 2.2–15 per m² of bare ground within 95 m of the camera path. §6.3b |
| **user** | *"white speckles read as dirt on the lens"* | **1 745 isolated pixels 28–112/255 above local median** in one 1200 × 500 crop | flowering weeds gated to within 45–110 m of the camera path. §6.3c |
| **user** | *"tree shadows are mushy blobs"* | every L2 canopy shell fully opaque — the leaf material's only cutout is per-*instance* | `mat_canopy`: the shell is perforated at leaf and twig-cluster scale, so the dapple is in the shadow too. §7.1 |
| **user** | *"the whole image is washed out by haze applied to the NEAR ground"* | — | measured, and **it is not terrain's and not near-ground**: at the doppler hover the atmosphere removes one part in 780. §4.1 |
| harness | a blade-level question had a 910 s / 1.07 GB loop | — | `--macro`: one 300 m window of verge at production density, from the same functions, **40 s and 34 MB**. §8.1 |

---

## 1. The one rule this module exists to satisfy

> *"i dont want repeat stuff aka one tree spammed 100 times everything has to be thought
> out no matter what… not a grass gray line done."*

Everything below is organised around that. §5 is the variation system, §6 is what makes
the ground itself worth looking at, and §9 is the evidence.

---

## 2. THE CONTRACT

```python
import world_contract as C
```

Nothing in this file re-derives a shared number. What it asks for:

| call | used for |
|---|---|
| `C.ground_z(s, u)` | the datum. Every plant inside the corridor sits on it |
| `C.platform_edge(s, side)` | the corridor rim — the outboard limit of the road programme |
| `C.corridor_rim_polyline(side)` | what the first ring of terrain vertices welds to |
| `C.verge_edge(s)`, `C.half_width(s)` | the cross-section |
| `C.runoff_widths(s, side)` | which lateral band is asphalt, which is gravel, which is grass |
| `C.barrier_type`, `C.apron_zone` | where the platform is somebody's concrete, not grass |
| `C.centreline_arrays`, `C.project`, `C.su_to_world` | geometry |
| `C.SUN_*`, `C.SKY_*`, `C.REFERENCE_EXPOSURE_EXTERIOR`, `C.lambert_radiance` | the light |

**Deleted:** `Circuit._half_width`, `Circuit._platform`, `Circuit.elev`, `Circuit.query`'s
own projection, `PLATFORM_DROP`, `SHOULDER`, and the corridor blend in `Ground.height`.

### 2.1 The hole, and how it is cut

`build_terrain`'s height field is a **CELL = 2.5 m** grid. A track edge is a 3675 m curve
held to a centimetre. A 2.5 m grid cannot represent it, so "blend the terrain into the
road" was never an available move. It is a hole:

1. **`corridor_field(x, y)`** — a signed field, ≤ 0 where the road programme owns the
   ground, in metres outboard of the rim. Section 2b of the source.
2. **Every mixed cell is split into two triangles and each is clipped** by
   Sutherland-Hodgman against `f ≥ 0`. Splitting first is not a detail: clipping a *quad*
   against an implicit boundary is ambiguous when the two inside corners are diagonally
   opposite, and the ambiguous case resolves to a bow-tie that covers the hole. A triangle
   carrying a linear field has no ambiguous case.
3. **Every cut vertex is put ON the rim by bisection** — 26 halvings, and the answer is
   the *outside* end of the final bracket, so a cut vertex can never end up inside the
   corridor whatever the field does. (False position was tried first and left 1.4 % of the
   cut vertices more than a millimetre out, the worst **33 m** out — a spike straight
   through the runoff. Bisection's bracket shrinks unconditionally; regula falsi's does
   not.)
4. **Each clipped cell's rim edge is then subdivided to ≤ 0.40 m** and the new vertices
   projected onto the rim, because a 2.5 m polyline chasing a 25 m-radius rim has a 31 mm
   sagitta and the rim's *z* curves too. Measured on the 5 m test grid the weld error went
   from a p99 of 8.8 mm to 7.1 mm and the whole distribution tightened; at the production
   2.5 m it is §9's number.
5. **`Ground.height` blends to the rim, not to a platform.** At `Dp = 0` the batter weight
   is exactly 0, so the first ring of vertices lands on `C.ground_z` **by construction, not
   by tolerance**. `TOL_SEAM_M` never has to absorb anything.
6. **The drainage swale moved outside the rim.** It used to be centred 7 m beyond the
   platform edge with σ = 4.6, which left a 34 mm notch *at* the weld — 3.4× TOL_SEAM_M.
   It is now held to zero over the first 1.2–5.0 m and its invert is 9 m out.

### 2.2 The medial axis — a correction to the contract's own mask

`C.project` returns the **nearest** point on the centreline, and `C.road_corridor_mask`
compares `|u|` against *that* branch's `platform_edge`. On a closed loop that is not quite
the corridor: at the medial axis between two branches a point is very nearly equidistant
from both and `project` picks one. If the branch it picks has a 12.1 m platform and the
branch it does not has an 87.9 m one, the mask says "terrain builds here" about ground
`build_barriers` will pave from the other branch.

**Measured on the 2.5 m grid: the nearest-branch field is discontinuous by up to 33.4 m at
the medial axis**, and the cell clipper cannot bisect a discontinuity.

So `corridor_field` is the **exact union**: the minimum, over every 1 m station, of the
signed distance to that station's quad,

```
f_i = max( u − PE_left(s_i + along/(1 − u·κ)),
           −PE_right(s_i + along/(1 − u·κ)) − u,
           |along| − (ds/2)·(1 − u·κ) )
```

with the rim linearly interpolated off a 5 cm station grid. A minimum of finitely many
continuous functions is continuous, which is the entire point. Three corrections in there
are load-bearing and each was measured:

* **arc, not tangent.** A point at lateral `u` whose perpendicular foot is `d` metres of
  station away sits at `along = d(1 − uκ)`. Treating `along` as station puts the rim
  lookup **0.55 m** out at 57 m of offset in an 82 m-radius corner.
* **the rim at the foot, not at the station.** The runoff ramps are steep — 45 m of
  asphalt eased over 55 m is 0.8 m of rim per metre travelled — so using the quad's own
  station dilates the union laterally by **1.4 m** and opens a slot between terrain and
  the platform.
* **`(1 − uκ)` on the along window** closes the fan gap between consecutive quads on the
  outside of a curve, which at 88 m of runoff and κ = 0.04 is **3.5 m**.

The result is deliberately **conservative**: terrain's hole is a *superset* of
`road_corridor_mask`, never a subset, so terrain can never build ground the road programme
also builds. §9 reports how much extra that is, and where.

**This is a note for the contract's author, not a complaint:** `road_corridor_mask` under-
claims at the medial axis, by up to 0.7 m of rim on the left of the lap. If two modules
ever disagree there, that is why.

### 2.3 Vegetation inside the hole — the actual "not a grass gray line" fix

Terrain builds no *ground* inside the corridor. It still **plants** there, and that is the
contract's explicit instruction (WORLD_CONTRACT §5) as well as the user's:

* the ground-cover band is generated in `(s, u)` from **`C.verge_edge`** — inside the
  corridor — out to `C.platform_edge + 42 m`, so it crosses the runoff programme instead
  of starting outside it;
* it is cut out of the runoff asphalt and every gravel bed by `C.runoff_widths`, and out of
  the pit-wall footing and the declared pit-exit apron by `C.barrier_type` /
  `C.apron_zone`, because those are `build_architecture`'s concrete;
* everything inside the corridor is placed on **`C.ground_z`**, never on this module's own
  height field, which inside the corridor is a smooth fiction.

Three geometry bugs had to be fixed before that was true, and all three were only visible
because the placement was *measured* rather than eyeballed:

| bug | consequence, measured |
|---|---|
| the jitter was applied in world x/y *after* the band test | clumps walked back into the gravel |
| the along-track step ignored the `(1 − uκ)` arc factor | 0.8 m of lateral error at 40 m of offset in a 50 m corner |
| **the (s, u) → world map folds** where \|u\| exceeds the radius of curvature on the inside of a bend | T4 is an R25 hairpin; a band running 42 m past the rim on its inside crossed the centre of curvature and came back down the other side. **26 % of samples landed up to 112 m from the offset they were drawn at, and 5 782 ended up on the racing surface.** Capped at 0.75 R |

And then, because drawing in `(s, u)` on one side says nothing about which branch of the
loop a world point is nearest to — in the infield a clump drawn 50 m off the esses can be
20 m off the doppler straight, and land in *its* gravel trap — **every sample is
re-projected with `C.project` and the cross-section test is redone against the branch that
is really there.** That is the same call `C.world_ground_z` makes. Before that pass,
15 753 of 60 000 in-corridor samples were on runoff asphalt or in a gravel bed. After it,
`selftest` reports **0**.

### 2.3b The corridor mouth at the glass plane — assembly finding #2, closed

**Three modules used three different margins for the same boundary, and 64 m² of the
Beat-3 → Beat-4 hinge had no ground at all.** The contract's `in_access_ribbon` tested
`tt >= -margin`, which walks the ribbon's **start cap backwards through the glass wall**
by whatever margin the caller passes:

| caller | margin | where its cut landed |
|---|---:|---|
| `road_corridor_mask` (this module) | `ACCESS_CORRIDOR_MARGIN_M` 3.00 | terrain cut to **x = 12.00** |
| `build_architecture` | `RIBBON_SAW_M` 0.30 | paving cut to **x = 14.70** |
| `build_surface` | — | the ribbon mesh **starts at x = 15.000** |

Nobody built x 12.0 → 15.0. Measured on a 0.10 × 0.5 m grid over x 4–17, y ±14:
**1 276 of 7 467 samples had no usable ground (~64 m²)** — a continuous 3.0 m deep band
across the whole 12 m driving width, with x 14.70–14.975 fully open, at the exact metre
the car and the camera pass through as the car breaches the glass.

**The fix is in the contract, because the disagreement was in the contract.** Two edits,
both in `world_contract.py` (bumped to **1.0.1**):

1. `ACCESS_RIBBON_T_MIN = 0.0` pins the ribbon's **start cap at the breach plane** for
   every consumer and every margin. The ribbon *begins* at `ACCESS_GLASS_X` = 15.000 by
   construction — spec §10.3(b) is about the first 50 m *outside* the glass, and behind
   the glass is the showroom floor. There is nothing to gain from a longitudinal margin
   there: both surfaces sit on a declared plane at `APRON_Z`, so a butt joint is exact.
2. **The keep-out and the joint are separated.** `ACCESS_CORRIDOR_MARGIN_M` (3.0 m) is
   *terrain's* keep-out, sized by the Beat-4 corridor walls, which stand at +8.0 / −7.0
   against a 6.0 m ribbon half-width. `ACCESS_RIBBON_SAW_M` (0.30 m) is *paving's* joint.
   Subtracting the keep-out from the declared apron — which is what `apron_platform_mask`
   did — left a further 3 m strip either side of the ribbon that terrain had cut and
   architecture had not paved, while `world_ground_z` correctly said architecture owned
   it. `road_corridor_mask` now takes a `ribbon_margin`, and `apron_platform_mask` passes
   the saw.

**Measured after, with `world_ground_z`'s own ownership as the referee** — a void is a
point terrain owns *and* the corridor mask cuts:

| scan | before | after |
|---|---:|---:|
| glass mouth, x 4–17, y ±14, 0.10 × 0.25 m | 1 276 samples, ~64 m² | **0 of 14 803** |
| the whole 244 m ribbon corridor, ±12 m, 0.5 × 0.25 m | — | **0 of 47 433** |

Both are `world_contract --selftest` checks now (74 checks, 0 failed), so they cannot
regress silently.

**And nothing else moved.** `world_ground_z` — the one call every other module uses to sit
an object on the ground — was already invoking `in_access_ribbon` with `margin = 0`, where
`tt >= -0` and `tt >= 0` are the same test. Verified by monkey-patching the pre-1.0.1
function back in and diffing over **400 000 random world points**: **0 differences in z,
0 differences in owner.** Only `road_corridor_mask` and the exclusive `apron_platform_mask`
changed, which are exactly the two that were wrong. The corridor cut confirms it in
geometry: **311 888 m² removed against 311 975 m² before**, an 87 m² reduction, which is
the 3 m × ~28 m of forecourt this defect was. This module's `corridor_fz` uses `C.ACCESS_RIBBON_T_MIN` for its own
ribbon term, so terrain's cut and the contract's mask agree at the mouth by construction.

**What is still open on this defect, and it is not terrain's:** `build_architecture` has
its own `-RIBBON_SAW_M - t` term at `build_architecture.py:1453`. The contract cannot
reach into it. Until that reads `-t`, architecture saws its own paving back to x = 14.70
and a 0.30 m × 12.75 m slot stays open on its side — now floored by terrain's forecourt
pad at −0.20 m rather than bottomless, but still a defect.

### 2.4 What terrain still owes its neighbours

* `build_barriers` must extend its runoff platform mesh out to `C.platform_edge(s, side)`.
  Terrain welds to that line and builds nothing inboard of it; if the platform stops at
  the barrier there will be a strip of nothing between them. **This is now measured, in
  the assembled world: 658 m² over 104 stations, worst at T3 s 702–746 (38 m² per 2 m
  station, gaps up to ~40 m wide), plus s 794–810, 1026–1112, 1734–1854, 3006–3018 and
  3372–3426.** The size of the obligation is `platform_edge − max(barrier_offset,
  runoff_edge)`, integrated over the lap: **42 076 m²** (left 20 020, mean 5.45 m wide;
  right 22 056, a constant 6.00 m). So barriers builds 98.4 % of it and misses patches.
  Terrain cannot fill them: the surface there is `C.ground_z`, which is the *same*
  function barriers builds to, so a terrain skirt inboard of the rim would be a coplanar
  z-fight wherever barriers *did* build — `TOL_COPLANAR_M`'s rule is cut, do not offset.
  The rim is the contract's `platform_edge` and it has not moved.
* The runoff programme's **grass bands** — 18–25 m of the cross-section over most of the
  lap, and everything between `verge_edge` and the barrier on the pit straight — are
  surfaced by `build_barriers`, and terrain plants on top of them. Its material there
  should be turf/soil, not asphalt: grass clumps hide a lot but not a grey base colour
  seen at a graze under a 12.5° sun.

---

## 3. THE LANDFORM

Structure, outermost first:

1. **Shepard base.** Inverse-4th-power interpolation of the circuit's own `z(s)` over the
   whole plane (control points every 10 m, softening radius 42 m). The ground everywhere
   is anchored to the elevation the circuit actually has, so the infield between two track
   sections at different heights becomes a natural ramp rather than a guess.
2. **The five named landforms of `circuit_spec §5`,** each anchored to the *track feature
   it is named after* (see §10 for why not to its published rectangle):
   * **NE escarpment** — falls at −8 % from 44 m beyond T4's apex to −10.5 m inside an
     angular fan around the hairpin's outward normal, then levels into a valley floor.
     This is what gives the kerb-height hairpin camera its falling background.
   * **The ridge** — two smooth domes, +3.55 m behind the esses and +2.75 m on the infield
     flank, so the summit shelf reads at +11.2 m against 8.0 m of road.
   * **The west hillside** — a ramp hinged on the line through the sweeper and the doppler
     straight, falling to −12 m outboard.
   * **The return hollow** — a −1.15 m dome deepening the bowl T12/T13 already sit in.
   * **The plateau** — flat 0.000 over circuit x −620…+300, y −120…+140, feathered 110/85 m.
3. **The three named empty zones** (`§10.7`) damp both the landforms and the relief noise.
4. **Relief** — fBm at 195 m / 620 m / 2100 m, amplitude ramping in with **distance from
   the nearest centreline**, plus 26 m and 7.4 m micro-relief bands that now start at the
   **rim** rather than 2 m from the centreline, so the ground immediately behind the
   barrier is not glassy.
5. **The batter** — 34 m from the rim into natural ground, weight exactly 0 at the rim.

**Long-range fields are keyed on distance-to-centreline, short-range ones on
distance-outboard-of-the-rim, and that split is deliberate.** `Dp` (outboard of the rim) is
exact only inside a 130 m band — outside it the cheap nearest-branch value is used, and
both exceed the 34 m batter so the height field cannot notice the switch. But the relief's
amplitude ramps run to 2.6 km, the woodland mask to 150 m and the hedgerows to 340 m, and
any of those keyed on `Dp` would step at the band edge. They are keyed on `Dc`, which is
continuous everywhere.

**An earlier version printed 15 m cliffs across the outfield.** It masked the landforms
with the nearest-station arc length `s` and the signed lateral offset `d`; both flip
discontinuously across the medial axis of a closed loop. Everything in (2) is now a smooth
world-space primitive. **No landform may depend on (s, d).**

### Mesh
One rectilinear grid, 2.5 m uniform across the core (world x −980…+900, y −560…+1290) then
26 geometrically growing rings (×1.30), 805 × 793 = 638 365 candidate vertices spanning
**21.7 × 21.7 km**, minus the corridor. Non-uniform spacing in a single grid means there is
no LOD boundary to crack. The extent matters for Beat 6: from 140 m up the true horizon is
42 km away.

---

## 4. THE LIGHT

**`build_sky` is the physical light of this film and the test harness imports it and runs
it.** `test_scene` calls `build_sky.build(scene, camera)` and `build_sky.bind_camera(cam)`,
so a terrain frame is lit by the film's actual sun, sky, cloud decks and atmosphere. If
the import fails it falls back to `world_contract`'s published constants — which are
`build_sky`'s own measured values — and says so in the log.

**§2.1 of the previous version of this note was wrong and is deleted.** It published an
assumed rig and told task #27 to "ADOPT S2.1 VERBATIM". Task #27 measured its sun against
its own sky instead, and was right to:

| | §2.1 assumed | `build_sky` shipped | consequence |
|---|---|---|---|
| sun | 120 W/m² at (1.000, 0.735, 0.470) | **115.754** at (1.000, **0.71632**, **0.38712**) | the real sun is markedly redder and much less blue |
| aerosol / ozone | 1.45 / 1.80 | **0.45 / 1.30** | sky tint (0.3115, 0.5582, 1.0000) |
| direct : diffuse | 3.00 : 1 | **2.072 : 1** | shadows are 45 % brighter relative to key, and bluer |
| exposure | −2.70 AgX, Medium Contrast look | **−3.048 AgX, Look = None** | 0.348 stops and a tone curve |
| aerial perspective | σ = 2.2e−5 /m, described as "26 km visibility" | σ = **1.7009e−4** /m, 23 km | Koschmieder says 3.912/2.2e−5 = **178 km**. The old haze was 7.7× too thin and the 3.7 km lap had almost no depth cue |

Every ground and plant albedo is therefore a real visible-band reflectance now, checked
arithmetically rather than by eye:

```
C.lambert_radiance(a) = a/π · (E_DIRECT_HORIZONTAL + SKY_IRRADIANCE)
                      = a/π · (29.224, 25.482, 23.249)
C.lambert_radiance(0.18) = (1.674, 1.460, 1.332), mean 1.4888 = AgX mid grey
```

`probe_albedo()` renders four known patches (0.18 grey, turf, dry grass, scree) to a linear
EXR under the real light and prints measured/`lambert_radiance` per channel. §9.2 has the
numbers, and they turned up a **second** light finding that is not this module's to fix:

> **`C.lambert_radiance` under-predicts the shipped rig by 0.53–0.58 stops**, uniformly
> across a 4.3× range of albedo, because `C.SKY_IRRADIANCE = (4.228, 7.577, 13.573)` was
> measured from the sky *texture* and does not include `SKY_Atmosphere`'s in-scattering.
> The harness therefore renders at **−3.628 = −3.048 − 0.580** and logs both numbers.

The exposure the film ships is the camera rig's (task #34) and the irradiance constant is
`build_sky`'s; this note is a measurement handed to both, not a regrade. What it does *not*
mean is that any albedo should move: the constancy of the ratio is precisely the proof
that the materials are right.

### 4.1 "The whole image is washed out by haze applied to the near ground"

**The terrain/sky mismatch this was suspected to be is already closed, and the log line
proves it on every frame this module renders:**

```
[terrain 41.0s] lit by build_sky: sun 115.754 W/m2 (1.0, 0.71632, 0.38712), AgX -3.628
```

That is `C.SUN_ENERGY`, `C.SUN_COLOR`, `C.SKY_AEROSOL` 0.45 and `C.SKY_OZONE` 1.30 —
`build_sky`'s own shipped, measured values, imported and run, not §2.1's assumed
120 W/m² / (1, .735, .470) / 1.45 / 1.80 / 3.0 : 1 / −2.70. §2.1 is deleted and every
albedo in §6.4 was re-checked against `C.lambert_radiance` (§9.2). So the wash-out is not
that.

**Nor is it near-ground aerial perspective, and the number says so.** `build_sky`'s
extinction is `SIGMA_EXT_550` = 1.7009e−4 /m (Koschmieder, 23 km visual range). Veiling at
the distances in question:

| distance | 2.4 m | 7.5 m | 100 m | 400 m | 2 km |
|---|---:|---:|---:|---:|---:|
| `1 − exp(−σd)` | 0.04 % | **0.13 %** | 1.7 % | 6.6 % | 28.8 % |

At the doppler hover the nearest ground in frame is 7.5 m, where the atmosphere removes
**one part in 780**. That is not a wash-out; it is not measurable. The rendered evidence
agrees: `macro_doppler_after.png` at that camera has near-field grass at mean 44.9/255
against a sky band at 171.6/255 — 1.9 stops of separation, with p1 = 12.3 in the shadowed
thatch. There is nothing veiled about it.

**What the user was looking at is `CAM_T10_HELI.png`, and its geometry is 200 m – 2 km.**
At 2 km the same physically-correct model removes 28.8 % of the contrast, and the frame's
own subject — the escarpment — is the thing that has no detail to lose (§6.3b: local
σ 3.1/255). So the frame reads as haze-washed for two reasons that are *both* addressed
here and neither of which is the atmosphere: **bare ground with no geometry in it, and
sub-pixel bright flowers on top of it.** Whether 23 km visual range is the right creative
choice for a 3.7 km lap is `build_sky`'s call and the camera rig's, not this module's; the
extinction coefficient is not something terrain may quietly halve.

---

## 5. THE VARIATION SYSTEM

Two hard facts set the budget. Trees are never closer than ~15 m to the camera path (they
stand back beyond the rim), and the lap crosses 3.7 km of country. So the answer is neither
"one asset" nor "every tree unique" — it is **many unique base meshes plus per-instance
variation that changes what the eye actually reads: silhouette, size, colour and season.**

### 5.0 Budget, in one paragraph

Instances are the expensive axis and base geometry is the cheap one, because Cycles keeps
one copy of a mesh however many objects reference it. Everything below follows: **8 unique
hero trees per species** (so no L0 mesh is used more than ~17 times in the world), **54–98
blades per grass clump** (a fat clump costs the renderer nothing extra), and then as many
placements as the design needs.

### 5.1 Genuinely different base structures

Not one generator with a scale slider. Branching topology, gravitropism sign, taper law,
crown envelope and leaf morphology all differ:

| species | habit | what makes it structurally different |
|---|---|---|
| pedunculate oak | spreading, heavy limbs | 6 orders, spiral phyllotaxis, primaries as long as the bole, lobed leaves |
| lombardy poplar | narrow column | 10 primaries off one leader, gravitropism +0.88 |
| scots pine | whorled, bare bole | whorl branching, 46 % clear bole |
| silver birch | slender, weeping twigs | gravitropism goes **negative** with depth (+0.28 → −0.80) |
| london plane | avenue tree, high fork | opposite phyllotaxis, 12-sided bole, largest leaves |
| italian cypress | tight column | 15 near-vertical primaries, crown ratio 0.22 |
| crack willow | spreading + weeping shoots | 6 orders with gravitropism to −1.05 |
| hawthorn | multi-stem scrub | 2–4 stems from the base, highest curl, crown ratio 1.45 |
| rowan | upright, pinnate | compound leaves on a rachis, opposite branching |
| dead standing timber | bare, broken | no foliage, 0.50 taper, bleached bark |

plus saplings, five shrubs (bramble, gorse, hazel, broom, juniper), ferns, five grasses,
and — new in this pass — **six weeds and three stone classes** (§6).

### 5.2 Every base mesh is itself unique
The library generates *n* independent trees per species per LOD from independent RNG
streams — **8 / 12 / 16 per species at L0 / L1 / L2**. Nothing is copied. Two oaks in the
library differ in bole length, branch counts at every order, every branch angle, every
wobble and every leaf position.

### 5.2b The virtual shoot
The branch recursion stops at 4–6 orders, so leaves were originally pinned within
millimetres of ~1500 terminal twigs: a correct leaf-area index arranged as *ropes*, and the
trees rendered as bare skeletons with green string on them. A real tree has one more order
— the season's unlignified shoots — which carries leaves out into the crown volume.
Modelling those as geometry costs another 5× of branches for detail 40 m from the lens, so
each terminal segment sprouts a few **virtual shoots** instead: leaves ride out along them
in tufts, at zero extra branch geometry. Leaf counts then went up on top — **×1.55 at L0,
×2.35 at L1** (LAI ≈ 4–5.5). L1 gets the bigger multiplier because it covers 95–380 m from
the path, which at 4K is a tree 100–400 px tall, and it had been budgeted as background.

### 5.3 What differs per instance, on top of that
| axis | range | effect |
|---|---|---|
| height | the species' range, narrowed 22–26 % on exposed ground | every instance a different size |
| breadth | ±8.5 % independent of height | changes crown proportion, not just scale |
| mirror | 50 % get `scale.x < 0` | a silhouette rotation cannot produce |
| spin | 0–360° | |
| lean | ±1.7°, biased downwind, ×2.6 on exposed ground | wind-flagged ridge trees vs sheltered hollow trees |
| **canopy density** | the shader drops 0–26 % of that instance's leaves | **the silhouette itself changes per instance** |
| season | 0–62 % autumn on the top 18 % of instances, with per-leaf bleed | most green, a minority turning, none identical |
| hue / value | ±4 % hue, 0.62–1.42 value on bark; ±3 % hue on leaves | no two trees the same colour |

### 5.4 Placement is habitat-driven, not a scatter

Species probability blends six mixes selected continuously by altitude, slope, wetness and
how built-up the ground is: exposed ridge → pine 40 %, hawthorn 22 %, dead timber 9 %, and
shorter and leaning harder; damp low ground → willow 28 %, birch 24 %, poplar 16 %; steep
hillside → pine 30 %, oak 20 %; plateau and paddock → plane 26 %, poplar 22 %, cypress 14 %
(planted species, because a human planted them); hedgerows → hawthorn 45 % and shorter.

**Every standoff rule is now written against the corridor rim, not against
distance-from-the-centreline.** "48 m from the centreline" is inside the pit lane at s = 0
(rim 12.1 m) and 40 m short of the barrier at T10 (rim 87.9 m), and the old rules used the
same number at both. Trees stand off 12 m outboard of the rim, shrubs 3 m, ferns 5 m; and
because the raster the coarse decision reads is a 14 m lattice, **every survivor gets an
exact `corridor_field` test on its final position** before it is placed.

**Hedgerows come from the same Voronoi partition as the ground shader's field colours,** so
a hedge always sits exactly on the boundary it is shading. **The paddock avenue is
planted**: 27 evenly spaced plane trees, ±0.9 m of jitter, three gaps where trees were lost
and two young replacements, at L0 with an 11.8–19.6 m height range — a real avenue is
uniform in *spacing and species*, not in size.

### 5.5 Grass — **vegetation is a geometry problem, not a material problem**

> *"think it half asses on this the grass is blurry etc. we need max detail max models
> detail on everything for fnal video"*

That note was made on a 4K frame, at 1:1, and it is a statement about **what a blade of
grass IS at the distance the lens is actually at**. `beat_sheet.json`'s doppler hover puts
the camera at station 2555, 26.0 m off the centreline, **2.4 m above grade**, on a 35 mm
lens. So the arithmetic that decides this section:

| | |
|---|---|
| angular resolution, 35 mm on 36 mm sensor at 3840 px | 2.474e−4 rad/px |
| frame pitch / vertical half-angle | −1.68° / 16.13° |
| **nearest ground actually inside the frame** | **7.47 m** horizontal, 7.85 m slant |
| **one pixel there** | **1.94 mm** |
| one pixel at the 2.4 m directly below | 0.59 mm |

**Three things make a blade read, and the old generator had one of them.**

1. **Width near 2–4 px.** The old blades were **6.0–11.0 mm across** — `w` is a
   *half*-width and the ribbon is ±`w` — which is 2–3× life size (fescue is 1–3 mm, rye
   3–6). Oversized blades **overlap**, and overlap is precisely what turns blades into a
   mat. Now **3.4–6.6 mm** for fescue: 1.8–3.4 px at 7.5 m, 6–12 px at 2.4 m.
2. **A fold.** A flat two-vertex ribbon has ONE normal across its width, so under a
   12.47° sun a whole blade is one flat tone and neighbouring blades differ only by their
   lean. A real blade is **channelled about its midrib**. Every hero blade now carries
   **three vertices per station — edge, keel, edge** — so the two halves shade differently
   and the keel throws a specular line down the blade. *That* is where the brief's "edges
   and tips" come from: it is a light/dark **pair** even when the blade is 2 px wide,
   which no shader on a flat strip can produce.
3. **Dark gaps.** Most of the read of turf is the shadowed thatch *between* the blades.
   The old clump was a uniform disc of full-length blades, so it closed into a canopy with
   nothing under it. Blades now come in **tillers** (a real sward is tillers, not a
   scatter) — each tiller a fan from one crown — and **26–38 % of every clump is a short
   understorey** at 0.30–0.62 of full height that fills the floor without closing the top.

Plus **6 segments instead of 3** (a 0.25 m blade is 125 px tall at 2.4 m, and a
three-segment polyline reads as a kinked stick), a real point at the tip (0.05 `w` instead
of 0.15) and a progressive **twist** about the blade axis.

**The cost is almost nothing, and that is why this is the right axis to spend on.** Cycles
keeps ONE copy of a mesh however many objects instance it. A hero clump went from ~460
triangles to **5 828** (2 914 quads, measured) and the whole hero library is 45 meshes.
What *does* scale is per-instance BVH traversal, so the hero blade is spent only where it
can be seen: **`GRASS_HERO_D` = 48 m of the camera path**, beyond which a 4 mm blade is
under a third of a pixel and what matters is the clump silhouette, which the far mesh
(the old flat 3-segment ribbon, 54–98 blades) still has.

**The far tier keeps the WIDE blade, deliberately.** Narrowing to life size is what makes
the hero blade resolve at 7.5 m; past 48 m a blade is under a third of a pixel and its
width is not a shape any more, it is a **coverage fraction**. A 3.4 mm blade out there is
simply half the sward of a 6.6 mm one for identical instance cost, so `gen_grass` restores
the previous pass's widths for `lod != 0` and the far field cannot thin out behind the
hero band. It is the one place in the module where the LOD tiers differ in a *physical*
quantity rather than in polygon count, and it is on purpose.

Generated **along the track** in `(s, u)`, from `C.verge_edge` outward to
`C.platform_edge + 42 m`, with the 62/38 mixture bias of §5.5b below. **900 clumps per
station-metre per side** and **190–330 blades per hero clump**, which is ~19 clumps/m² at
the verge and ~11 at the doppler station's 26 m offset — **2 300–4 000 blades/m² where
the camera flies**, against 400–700 in the previous pass and ~35 in the pass before that.

* **consistent wind lean** — every blade leans toward bearing 65° at 15° × a per-clump
  0.55–1.55 factor, and bends progressively along its length like the cantilever it is;
* **patchy and worn where it would be** — an 11 m patch field, a 7 m clump-scale field, and
  the **run-wide scuff** below;
* **kind by habitat** — mown fescue on the verge, tussock in the rough, seeding meadow
  grass in the fields, dry burnt grass on the ridge, the escarpment **and wherever cars run
  wide**, reeds in the wet hollow.

Instanced through Geometry Nodes (`Instance on Points`, `Pick Instance` from a library
collection deliberately **not linked to the scene**), with per-point index, rotation and
scale attributes computed in numpy.

---

## 6. MAKING THE GROUND WORTH LOOKING AT

### 6.1 Where cars run wide

`scuff(s, side)` is a station field, per side, of how hard a piece of ground gets used when
a car misses the apex. It is built from the centreline's own curvature — hard from R286 m
down to R62 m — smoothed with a kernel whose peak is **45 m past the geometric apex**,
because that is where a car that has run out of road actually arrives, and gated to the
**outside** of the turn. It drives three things:

* the ground shader's rubber-and-dragged-soil staining (`ter_scuff`, albedo 0.046/0.041/0.038);
* grass density (−62 %) and grass *kind* (the dry mix gets +1.10 of weight);
* where gravel dragged out of a trap ends up.

### 6.2 A verge is not grass

Six weeds, each a different habit rather than a re-tint: **dock** (broad basal rosette, rust
seed spike), **thistle** (spiny rosette, one brush head), **ragwort** (branched, flat yellow
corymb), **plantain** (flat rosette, bare rods — weighted toward the trodden strip),
**yarrow** (feathery, white umbel), **nettle** (opposite-leaved, square stem, no flower).
Leaves are built as real arching tapered ribbons, not flat quads on a frame, because a dock
leaf 1.2 m from the lens has to actually curve. Heads are four different constructions
(spike, rod, brush, corymb/umbel).

### 6.3 Stone

Three classes — pebble, cobble, boulder — each an icosphere pushed around by fBm plus a
ridged facet field, flattened along a random bedding plane. Placed three ways:

* **scree and field stone** on steep ground and in the ploughed-up patches, outside the rim;
* **gravel spray** — pebbles dragged out of a trap and thrown across the grass behind it,
  only where there *is* a trap, only in the 9 m downstream of it, and only where `scuff`
  says cars actually go off;
* in the shader, a **voronoi stone field** so a scree slope is made of individual stones
  rather than of brown noise.

### 6.3b Grit — what makes bare ground bare ground

> *"bare ground is a flat sandy plane with no stones or clods"*

It was, and no shader could have fixed it. **Measured on `CAM_T10_HELI.png`, over an
840 × 460 crop of the escarpment: local (9 × 9) σ of luminance 6.25/255 at a mean of
108.4 — 5.8 % relative contrast**, and 5.1 % on the pale runoff beside it. The surface is
flat to within a few pixel values over a metre of ground. For scale, the same statistic on
the doppler frame's near ground after this pass is **13.49/255 at mean 44.5 = 30.3 %**.

The cause is structural. Everything the ground shader carries below ~0.4 m is a **bump**,
and a bump has no silhouette, casts no shadow on its neighbour, and disappears entirely at
a 12.47° grazing sun, where the only thing that reads is the shadow one clod throws across
the next. §6.3's field stone *was* geometry, but it is the 0.10–1.70 m fraction and it is
gated to slopes > 7° and the ploughed patches: **244 cobbles and 30 boulders in the whole
world.** What bare ground is actually made of is the **10–95 mm fraction** — grit, flint
chips, and dried clods of the soil itself.

`build_grit` scatters that fraction as real meshes:

* **three classes** — chip 12–38 mm (46 %), stone 35–95 mm (24 %), **soil clod** 20–70 mm
  (30 %). The clod is the same generator as the stone with `mat_clod`, whose albedo is
  deliberately the ground shader's own `GA_DUST` (0.098) / `GA_SOIL` (0.044) pair: a clod
  that reads as a *different material* from the ground it broke off is worse than no clod.
  What makes it visible is that it has a silhouette, not that it has a colour.
* **half buried.** Each piece is sunk 30–60 % of its own height into the datum. A stone
  lying *on* a plane is a stone lying on a plane; a stone *bedded into* it is a stone in
  the ground, and at a grazing sun the difference is the shape of the shadow.
* **density is driven by bareness**, which is the **inverse of the very same 11 m patch
  field that thins the grass**, plus `scuff`, slope and dryness. Grit therefore appears
  exactly where the sward does not, and the two never fight for the same square metre.
  15 pieces/m² on fully bare ground at the lens, 2.2 at `GRIT_D`.
* **`GRIT_D` = 95 m of the camera path**, and the number is derived, not chosen: a 40 mm
  clod is 20 px at 7.5 m and 1.6 px at 95 m, so that is where it stops being geometry and
  starts being noise.
* the draw is **area-normalised**: `verge_band` is sampled *without* the verge bias and
  each sample is accepted with probability `target × band_width / per_m`, where the band
  width is recovered exactly as `(lat − f) + 22`, i.e. `platform_edge − verge_edge + 22`,
  whatever the runoff programme is doing at that station. Constant pieces per m², not
  constant pieces per station-metre.

### 6.3c The white speckles

> *"white speckles read as dirt on the lens"*

**Measured, on the same frame:** in a 1200 × 500 crop, **1 745 isolated pixels sit 28–112
(mean 41) above their own 9 × 9 local median**, the brightest at (220, 208, 193).

They are **yarrow umbels and ragwort corymbs** — physically correct flowers (a white
umbel really is that bright against 0.05 turf) that are **sub-pixel at 200–400 m**. A
sub-pixel object three stops above its background does not average down; it aliases into a
dot, and 1 745 of them read as a dirty lens.

The fix is not to darken a correct albedo, it is to stop drawing flowers at distances
where they cannot be flowers: the two flowering habits are now weighted by
`smoothstep(110, 45, dcam)` — full inside 45 m of the camera path, gone by 110 m — with
dock, thistle, plantain and nettle taking up the weight so the far verge does not thin
out. Every flower that survives has enough pixels to read *as* a flower.

### 6.4 The ground shader

Thirteen baked vertex attributes, not eight: `ter_wet`, `ter_wear`, `ter_cover`, `ter_mown`,
`ter_hedge`, `ter_dry`, `ter_field` (crop colour, RGB), `ter_dist`, `ter_plateau`, and new
in this pass **`ter_rock`**, **`ter_moss`**, **`ter_scuff`** and **`ter_slope`**.

`ter_slope` is worth calling out: the old `ground_attributes` shipped an all-zero `slope`
array and every rule that read it was therefore dead code. It is now the gradient of the
built height field itself, sampled bilinearly at the cut vertices.

Five noise scales — 6 cm, 40 cm, a metre, ten metres, a hundred — where there were three.
The two finest exist because the camera passes within 2 m of this surface on the verge, and
at 4K a scale-2.6 noise is a 40 cm blob. Four stacked bump nodes: grain, stones (masked by
the voronoi so the stones stand proud of the grit between them), clod, and landform.

Layers, in order: pasture (two greens × crop tint × dry) → blade-scale straw mottle → soil
and dust under `ter_wear` → thin-cover soil showing through the sward → **stone** →
subsoil on steep faces → **run-wide rubber** → **moss** → hedge root-strip → damp. There is
no single flat green anywhere in it, and the swale invert is explicitly wet and glossier.

Albedos, all real visible-band reflectances (§4):

| | linear RGB | mean | stops under AgX mid grey |
|---|---|---|---|
| dense green pasture | (0.042, 0.082, 0.028) | 0.051 | −1.83 |
| lighter sward | (0.062, 0.098, 0.036) | 0.065 | −1.47 |
| hay / standing dead | (0.170, 0.150, 0.062) | 0.127 | −0.50 |
| dry dust and clay | (0.148, 0.122, 0.086) | 0.119 | −0.60 |
| damp turned soil | (0.058, 0.043, 0.030) | 0.044 | −2.03 |
| limestone / flint scree | (0.228, 0.222, 0.202) | 0.217 | +0.27 |
| ground a car has run over | (0.046, 0.041, 0.038) | 0.042 | −2.10 |

---

## 7. LOD, budgeted by distance to the camera path

| tier | distance to path | tree content |
|---|---|---|
| L0 hero | < 95 m | 6 branch orders, 30–57 k individual leaves on virtual shoots |
| L1 mid | 95–380 m | one fewer segment/side per order, ~1/3 the leaves × 2.35 |
| L2 far | > 380 m | trunk + limbs + 5–11 twice-displaced canopy shells, each shell unique |

**L2 is not a throwaway tier.** At the Beat-6 hold the camera is 140 m up on an 18.75 mm
lens; a 15 m tree a kilometre out still covers ~37 px at 4K, which is enough silhouette to
betray a sphere. The shells carry a smooth lobe for the crown's masses times a per-vertex
hash spike for the ragged twiggy edge, overlap and skirt downward, and are shaded *darker*
than the hero LOD (a canopy at a kilometre is mostly self-shadowed).

### 7.1 The L2 shell is a PERFORATED mass — "tree shadows are mushy blobs"

The shells were shaded with the species' **leaf** material, whose only transparency is the
per-*instance* defoliation test (`pid < thr`, `thr` ∈ 0.74–1.01) — and the shells are
authored with `pid` ∈ 0.02–0.46, so **every L2 shell was fully opaque.** Seen from the
helicopter the far woodland therefore cast flat slabs: a real canopy is 55–75 % gaps by
projected area, and those gaps are the whole of what makes a tree shadow a pool of dapple
instead of a hole.

Cutting real leaves at L2 is not the answer — an L2 tree is 37 px at a kilometre and there
are 24 646 of them. What *is* the answer is that **the shadow does not care how the gaps
are made.** `mat_canopy(key)` is a new material on its own slot (index 2, so the leaf
material is untouched) which cuts the shell with two object-space noise fields — leaf scale
(17 /unit) × twig-cluster scale (3.1 /unit) — thresholded to about 0.55 coverage. Cycles
evaluates the same shader on shadow rays, so the dapple is in the shadow as well as in the
silhouette, at zero extra geometry. Its colour is the species' summer leaf held darker
(value 0.58–1.08 against the hero LOD's 0.72–1.30) and its roughness +0.22, because a
canopy at that distance is mostly self-shadowed and should not sparkle.

---

## 8. THE TEST HARNESS

`build()` creates no light, no world and no camera. `test_scene` does, in a throwaway
`TER_TEST` collection, and it builds two things:

1. **the light** — `build_sky`, imported and run (§4);
2. **`TER_PROXY_Road`** — the road programme as the contract describes it: the racing
   surface out to `verge_edge` and the runoff out to `platform_edge`, meshed straight off
   `C.ground_z` and `C.runoff_widths`, band-coloured (track / kerb / verge / runoff asphalt
   / gravel / platform).

The proxy exists because terrain deliberately builds nothing inside the corridor, so a
terrain-only frame of the verge would show grass floating over a hole. **It is test
geometry, `build()` never creates it, and the real thing is `build_surface`'s and
`build_barriers`'.** Its value is that it is generated from the contract alone: anywhere
terrain and the proxy disagree, terrain is wrong.

Camera views are specified as `(station, signed lateral, height)` and resolved through
`C.su_to_world`, so they land on the datum whatever the widths do. Each was chosen against
the contract's cross-section at that station, not by eye — e.g. `t5_verge` at s = 1250,
u = +12.5 is inside a grass band that runs from `verge_edge` 9.50 to `platform_edge` 39.09
with no asphalt and no gravel in it.

`--cams` bakes a **few** named cameras into the saved blend for `tools/r5090`. Few is
literal: the worker prewarms every camera at load and 19 of them blew the readiness probe.

### 8.1 `--macro` — the two-minute loop

A full build is **910 s and a 1.07 GB blend**. That is the wrong iteration loop for a
question that is settled in a 360 × 180 pixel crop, and the cost of a wrong loop is that
you stop iterating.

```
blender -b --factory-startup -noaudio -P world/build_terrain.py -- \
        --macro doppler --half 150 --cams doppler \
        --save render/world/terrain/macro_doppler.blend
tools/r5090 render/world/terrain/macro_doppler.blend CAM_doppler out.png 512 3840 2160
```

**40 s, 34 MB.** It builds ONE 300 m window of verge around whichever view you name, at
full production density — 285 822 clumps, 166 962 of them hero, 121 726 grit pieces — plus
the road proxy, `build_sky` and the camera. `--nogrit` and `TERRAIN_LEGACY_GRASS=1` turn
individual layers off for A/B.

Two things make it evidence rather than a demo:

* **it calls the same functions the build calls.** `verge_band` takes a `swin` station
  window, `build_grass` / `build_weeds_and_stones` / `build_grit` take the same window and
  a `meadow` / `field` flag. Nothing is reimplemented. A probe that reimplements the
  placement is evidence about the probe.
* **it does NOT call `Ground.height` directly.** `Ground.height` includes the corridor
  batter, so it calls `corridor_fz`, which is the O(points × 3675 stations) exact union
  field — fine for the 638 k vertices of one build, ruinous for ~540 k band samples × 3
  (the slope finite difference) × 3 passes. The first version did, and did not finish the
  first band in four minutes. `_probe_gz` samples a 5 m grid once (12 s) and bilinearly
  interpolates, which is exactly what `build()` does with `GridZ` off the built mesh.

---

## 9. EVIDENCE

Everything here is a number this module measured, or a frame it rendered and looked at.

### 9.1 `--selftest`, measured against the contract

```
ground_verts                  607 530      ground_polys                 607 843
verts_inside_corridor_1mm           0      min_corridor_field_mm      -0.753
verts_in_contract_mask          1 438      contract_version            1.0.1
rim_samples                     1 660      rim_no_terrain                   0
rim_owned_by_other_branch         129
weld_max_mm                   290.797      weld_p99_mm                  4.250
weld_rms_mm                     7.477      weld_within_TOL_SEAM         false
road_rays                       4 000      terrain_above_road_pct       0.0000
terrain_above_road_worst_m     0.0000      terrain_above_road_worst_at   None
half_width_3115                 8.000      half_width_250               8.000
plants_total                4 716 443      plants_in_corridor       2 365 970
plants_on_runoff_or_gravel          1
```

**Every number the integration round bought is still there.** `verts_inside_corridor_1mm`
0, `terrain_above_road_pct` 0.0000 against the review's 5.3 %, `terrain_above_road_worst_m`
0.0000 against +0.381 m, `rim_no_terrain` 0, `half_width` 8.000 at both s = 3115 and
s = 250, and the weld distribution is bit-for-bit what it was (max 290.797 mm at the
4.5 m isthmus, p99 4.25, rms 7.477). The corridor cut, the weld and the datum were not
touched by this pass and the selftest proves it rather than asserting it.

`plants_on_runoff_or_gravel` is **1**, not 0, and it is worth being exact about: one piece
of grit out of 1 614 928 (4 716 443 plants in total) sits on a runoff/gravel boundary
cell. It is a single sample landing within the numerical width of the band test, not a
class of failure — the same test that returned 0 for 3.1 M plants last pass returns 1 for
4.7 M this pass.

**The corridor cut, from the build log:**

```
corridor cut: 3 898 cells clipped, 6 102 rim vertices (+12 965 infill),
              49 902 grid verts dropped, 311 888 m2 removed   (152.2 s)
```

311 888 m² against 311 975 m² last pass: **87 m² less**, which is the 3 m × ~28 m of
forecourt that the ribbon start-cap fix (§2.3b) handed back to `build_architecture`.

311 975 m² against the contract's own figure of 309 180 m² — the 2 795 m² difference is
the medial-axis correction of §2.2, i.e. terrain cutting *more* than
`road_corridor_mask` asks for, never less.

**The three headline numbers, before and after:**

| | assembly review | now |
|---|---|---|
| terrain above the racing surface | **5.3 % of samples, worst +0.381 m** | **0.0000 %, worst 0.0000 m** |
| kerb + painted verge buried | 42.3 % (54.0 % left / 43.6 % right) | terrain does not reach it: the band is 12.1–87.9 m inside the hole |
| runoff programme under dirt | 50 555 m² asphalt + 42 419 m² gravel + 240 000 stones | **0 m² covered** — and 1 391 952 grass clumps, 20 991 weeds and 116 dragged pebbles now stand on it |

**Two numbers that are NOT clean, stated plainly:**

* `weld_within_TOL_SEAM` is **false**. 5 of 1 660 rim samples exceed `TOL_SEAM_M`
  (0.30 %), p99 is 4.25 mm and p50 1.79 mm. The 290.8 mm outlier is at s = 728 on the
  left, world (281.6, 674.2) — where the terrain strip between two branches of the loop
  is **4.5 m wide**, measured, so the ground there is a crown battered from both rims
  rather than a flat shoulder. It is a real feature of a narrow isthmus, not a gap. The
  next two (31.5 mm at s = 132, 17.6 mm at s = 1744) are ordinary chord/z-curvature
  residual on the widest runoff ramps.
* `verts_in_contract_mask` = 1 438 of 607 526 (0.24 %) are terrain vertices that
  `C.road_corridor_mask` calls corridor. They sit within ~1 cm of the boundary and are
  the second-order residual of the union field's 1 m station sampling.

Read it as:

| check | what it means |
|---|---|
| `verts_inside_corridor_1mm` | terrain vertices inside the road corridor. **This is finding #1 as one number.** |
| `terrain_above_road_pct` / `_worst_m` | ray-cast over the racing surface *and* the runoff: how often, and by how much, terrain is above the road. Was 5.3 % / +0.381 m. |
| `weld_max_mm` / `p99` / `rms` | the built mesh against `C.corridor_rim_polyline`, sampled 0.10 m outboard, ray-cast. `TOL_SEAM_M` is 10 mm. |
| `rim_owned_by_other_branch` | rim samples that legitimately fall inside *another* branch's corridor (§2.2). Terrain leaving a hole there is correct. |
| `plants_on_runoff_or_gravel` | plants standing on runoff asphalt or in a gravel bed. Was 15 753 of 60 000 in-corridor samples. |
| `verts_in_contract_mask` | terrain vertices inside `C.road_corridor_mask` — the residual of the union-vs-nearest difference at the ~1 cm level. |

### 9.2 The albedo probe

```
patch          albedo   measured (linear R,G,B)      measured / lambert_radiance
0.18 grey      0.180    2.6273  2.1609  1.6735       1.569  1.480  1.256
turf           0.051    0.6327  1.0096  0.2780       1.619  1.518  1.342
dry grass      0.127    2.5734  1.8840  0.6167       1.627  1.548  1.344
scree          0.217    3.3680  2.7157  1.9237       1.588  1.508  1.287
```

**The ratio is constant to ±1.9 % across a 4.3× range of albedo.** That is the whole
result: the materials are right relative to each other and to their own albedo, and the
*constant* is not — `C.SKY_IRRADIANCE` was measured from the sky texture alone and does
not include `SKY_Atmosphere`'s in-scattering, which adds roughly 38 W/m² of warm airlight
to a horizontal surface. An 0.18 surface therefore renders 0.53–0.58 stops above where
`REFERENCE_EXPOSURE_EXTERIOR` intends it.

**This harness therefore exposes at −3.628 = −3.048 − 0.580 and prints both numbers on
every render.** It is a finding for `build_sky` (whose `SKY_IRRADIANCE` should include the
atmosphere) and for the camera rig (task #34, which owns the film's exposure) — not a
unilateral regrade, and not a reason to darken any albedo, because the albedos are the
one thing the probe proves correct.

### 9.2b THE BLADE GATE — the doppler hover at 4K, 1:1

**The question, and the frame it is answered in.** `macro_probe` builds one 300 m window
of verge (s 2405–2705) at full production density — 285 822 clumps, 166 962 of them hero,
121 726 grit pieces — and bakes `CAM_doppler`, which is the beat sheet's own camera:
world (−578.82, −47.47, 4.802), 2.4 m above grade, 35 mm. Rendered at **3840 × 2160, 512
samples, on the 5090**, lit by `build_sky`, AgX at −3.628.

It is an **A/B**: `TERRAIN_LEGACY_GRASS=1` reverts the grass layer to the previous pass and
nothing else — same seed, same 285 822 clump positions, same kinds, same scales, same grit,
same light, same camera. One variable.

| | before | after |
|---|---:|---:|
| polygons per hero clump (mean, measured at build) | **211** | **2 914** |
| blades per clump | 54–98, scattered | **190–330, in tillers of 3–8** |
| blade width, fescue | 6.0–11.0 mm | **3.4–6.6 mm** |
| segments | 3 | **6** |
| cross-section | flat, 2 verts/station | **channelled, 3 verts/station** |
| understorey | none | **26–38 % of the clump at 0.30–0.62 h** |

**Measured on the rendered pixels**, `render/world/terrain/crops/*_ab.png`, same crop
boxes in both frames:

| | near crop (7.5–12 m) | mid crop (14–25 m) |
|---|---:|---:|
| light/dark alternations per 1000 px of scanline | 239.3 → **290.1** (**×1.21**) | 249.1 → **283.0** (**×1.14**) |
| spectral energy at the **blade-edge** scale, > 1/4 cycles/px (2–4 px features) | 10.3 % → **16.3 %** (**×1.59**) | 8.7 % → **11.4 %** (**×1.31**) |
| spectral energy at the **strap** scale, 1/32–1/8 cycles/px (8–32 px) | 38.3 % → **26.6 %** (**×0.69**) | 35.1 % → **33.3 %** (**×0.95**) |

That last pair is the result, stated as a number: **the image's energy moved out of the
strap scale and into the blade-edge scale.** A "fuzzy continuous mat" is precisely an
image whose variance lives at 8–32 px; individual blades live at 2–4 px.

`crops/blade_zoom_ab.png` is a 360 × 180 crop at 3× nearest-neighbour, which is where the
mechanism is visible rather than merely measurable: **before**, broad flat straps, each one
a single tone across its width; **after**, blades 3–5 px wide, each carrying a bright keel
line down its middle with darker flanks either side, tapering to a real point, arching, and
with shadowed thatch between them. The keel is doing exactly what §5.5(2) says it does — it
makes a 3 px blade a **light/dark pair**, and that is why it survives at 4K where a flat
ribbon does not.

**The grit is in the same frame.** First pass, the 35–95 mm pieces came back at
(196, 190, 176) against grass at (74, 78, 46) — 2.1 stops up, and they read as golf balls
in the sward. `mat_stone` is right for a scree slope and wrong in a verge; `mat_grit_stone`
(§6.3b) is the dark lithology with soil washed into the crevices, 1.0–1.3 stops above the
ground instead of 2.1. What makes grit read is the shadow it throws, not its value.

### 9.3 Rendered frames

`render/world/terrain/`, 4K, on the 5090, lit by `build_sky`.

| frame | what it is |
|---|---|
| `macro_doppler_after.png` | **the blade gate**, §9.2b. The beat sheet's doppler camera, 2.4 m above grade |
| `macro_doppler_before.png` | the same frame with `TERRAIN_LEGACY_GRASS=1` |
| `crops/blade_zoom_ab.png`, `crops/blade_near_ab.png`, `crops/blade_mid_ab.png` | the 1:1 (and 3×) A/B strips the numbers above were measured on |
| `t10_rim.png` | **the grit gate.** s = 2150, u = −92.0, i.e. 4.3 m OUTSIDE `platform_edge` 87.70. Its foreground is exactly the case §6.3b is about: dry, scuffed, thinly grassed ground at 3–15 m from the lens. The chips, stones and clods are visible as individually bedded pieces each throwing its own shadow at 12.47°, against the assembly frame's featureless pale plane |
| `before/t10_rim_narrowfar.png` | the same frame built before the far-tier blade width was restored (§5.5) |
| `crops/farlod_ab.png` | the A/B for that decision. At 92 m from the camera PATH this foreground is the far tier even though it is 3 m from the lens. Measured on the same 900 × 600 crop: local (9 × 9) σ **8.67/255 at mean 94.2 = 9.2 % relative** with life-size blades, **11.27/255 at mean 86.6 = 13.0 %** with the wide ones — **+41 % of local structure for zero extra instances** |

**One honest caveat on `t10_rim.png`.** `GRASS_HERO_D` is measured from the CAMERA PATH,
not from the camera, and this is a *test* camera parked 92 m off the centreline — 44 m
outside the hero band — so its foreground is deliberately the far tier. No film camera is:
the beat sheet's lap cameras stay within ~30 m of the centreline, the doppler hover is at
26 m, and Beat 6's crane keys are themselves in `CameraPath`. The frame is still worth
having, because it is the harshest possible test of the far tier and it is what drove the
wide-blade decision.

| frame | where it is, against the contract | what it is for |
|---|---|---|
| `t5_verge.png` | s = 1250, u = **+12.5**, 1.35 m, 34 mm. `verge_edge` 9.50, `platform_edge` 39.09, **no asphalt and no gravel** in the cross-section — 29.6 m of grass | the verge the camera actually flies down. Turf to the painted edge, wildflowers, the contract's kerb band, the treeline standing back at 51 m |
| `pit_verge.png` | s = 3300, u = **−13.5**, 1.30 m, 40 mm. The pit straight's south verge: 8.5 m of grass between `verge_edge` 10.50 and the barrier pinned at circuit y = −19 | the strip that was **0.63 m of unbuilt ground** before the width fix, and that had **no vegetation at all** until the built-pad rule was made corridor-aware |
| `t10_rim.png` | s = 2150, u = **−92.0**, i.e. **4.3 m OUTSIDE** `platform_edge` 87.70, 2.30 m, 28 mm | the T10/T11 sweeper, where TER_Ground stood +0.381 m proud of the tarmac. Terrain's own ground in the foreground, the weld, and 55 m of runoff asphalt + 15 m of gravel that are now on top instead of underneath |
| `t8_gravel.png` | s = 1792, u = **−57.5**, 1.25 m, 50 mm — 3.5 m outboard of the gravel bed that ends at 54.00, grass to 62.29 | the gravel edge, the pebbles dragged out of it by `scuff`, the grass, the rim and the swale |

`before/` holds the same four frames from the intermediate passes, so every regression
below can be checked rather than taken on trust:

| before/ | the defect it shows |
|---|---|
| `t5_verge_k062.png` | **the verge bias with the wrong sign.** `u = e + t**0.62 * W` has areal density ∝ `a**0.61`, which *increases* outward: bare ground with weeds standing in it, exactly where the camera flies. `t**1.8` inverts it |
| `*_thin.png` | clumps scaled uniformly from a unit-height mesh: short mown turf came out short **and narrow**, 15 tufts/m² × 0.12 m = 11 % ground cover |
| `*_straw.png` | 80 % of every clump mixed to a 0.17–0.25 dry tone from mid-blade up, under a sun at (1.000, 0.716, 0.387) — the whole verge read as straw |
| `pit_verge_nograss.png` | the built pad (circuit x −490…+140, **y −70…+120**) contains the whole pit straight, so testing it removed every clump from the south verge |
| `t10_rim_thinshoulder.png` | a pure power-law band starves its far half: 2.6 clumps/m² at the rim. Fixed with a 62/38 mixture of verge-biased and uniform draws |

**The road in all four frames is `TER_PROXY_Road`, not `build_surface` and not
`build_barriers`.** It is generated from `C.ground_z` and `C.runoff_widths` alone (§8), so
it is exactly what the contract says is there — which makes these frames a test of the
contract as much as of the terrain — but its gravel is a flat pale plane where the real
one has 240 000 individually generated stones, and its asphalt has no aggregate. Read the
proxy as a *datum*, not as a look.

### 9.4 Build numbers

```
woodland trees            24 646      hedgerow trees             3 298
paddock avenue                24      shrubs                    38 841
saplings                   5 501      ferns                      7 211
grass clumps           2 986 019      of them, INSIDE the road corridor   1 392 522
   of them, HERO LOD    1 660 414      (< 48 m of the camera path)
weeds                     35 574      of them, INSIDE the road corridor      20 966
GRIT pieces            1 614 928      gravel spray 127, field stone 244 / 30
unique base meshes         1 027      base library triangles       33.3 M (resident once)
objects in WORLD_TERRAIN  28 003      evaluated triangles          12.58 G
build                    910.6 s      + selftest 197 s
```

The clump COUNT is unchanged to 0.002 % (2 986 019 against 2 986 069) — the placement was
not touched, only what stands at each point. Evaluated triangles went 4.69 G → 12.58 G and
the resident base library only 32.7 M → 33.3 M, which is the whole argument for spending
on blades: **the geometry is instanced, so 13.8× the polygons in a hero clump costs 0.6 M
triangles of memory, not 8 G.**

---

## 10. HONEST NOTES, APPROXIMATIONS AND OPEN ITEMS

1. **`circuit_spec.json`'s `terrain.landforms` block says `"frame": "circuit"`, but its
   rectangles are not consistent with that.** The plateau rectangle is correct in the
   circuit frame; the return hollow matches T12/T13 only in **world** coordinates; the NE
   escarpment rectangle contains neither T4's circuit position nor its world position.
   Rather than pick one reading and be wrong half the time, each landform is anchored to
   the track feature it is named after, which satisfies the stated *purpose* of every one
   of them. **If the spec owner meant the rectangles literally, this is the line to
   revisit.**
2. **The corridor field is a superset of `C.road_corridor_mask`** (§2.2), by up to 0.7 m of
   rim on ~13 % of the left-hand rim. That is the medial-axis correction and it is
   deliberate, but it is a *deviation from the contract as written* and the contract's
   author should decide whether `road_corridor_mask` or this is the definition.
3. **The union field costs real time.** `corridor_field` is O(points × 3675 stations); the
   ground pass is the slowest part of the build. It is exact, continuous and conservative,
   and the alternative (nearest-branch) is none of those. Wall-clock is not a constraint on
   this project, so the exact version wins; if it ever needs to be faster, bucket the query
   points spatially and select stations by bounding box.
4. **Cut vertices are on the rim to ~1e−7 m, but the mesh *between* them is a chord.**
   Rim-edge subdivision to 0.40 m takes the sagitta to ~1 mm at R25; the residual weld
   error in §9.1 is dominated by the *z* curvature of the rim, not by its plan curvature.
5. **Terrain still lowers the paddock / pit / apron pad and the round-1 ground plate to
   −0.20 m**, feathered over 26 m, so `build_architecture`'s slab never z-fights. That is
   unchanged and it is a tolerance, not a weld — the contract does not cover it.
6. **Grass does not extend past ~430 m from the track**; beyond that the ground shader's
   field colours carry it. Invisible at the Beat-6 hold; a camera dropped into the far
   outfield would find shader-only ground.
7. **No wind animation.** The lean is static. The clump meshes already carry a `pgrad`
   attribute (0 at the base, 1 at the tip) that a displacement or a sine in geometry nodes
   can drive without regenerating anything.
8. **The `--save` blend must not go on `/tmp`.** `/tmp` here is a 5.9 GB tmpfs, i.e. RAM,
   on a box with 11 GB total and six builders running. Use `/var/tmp` or, for anything
   `tools/r5090` has to read, a permitted root under `f1-round2/`.
9. **Cloud parallax is bound to one camera.** `build_sky.bind_camera` drives the cloud
   decks' observer off a specific camera object, and `--cams` binds the first of the four.
   The light is unaffected — only the decks' XY parallax — but a frame from
   `CAM_pit_verge` has `CAM_t5_verge`'s cloud registration. Harmless at these framings and
   over these distances; it would not be in a shot that pans on the sky.
10. **What is still open, honestly:**
   * the shrub layer's five species are all built by the same `gen_shrub` generator with
     different parameters — genuinely different silhouettes, but not the ten independent
     *structures* the tree layer has. If the camera gets within ~15 m of the undergrowth,
     that is the layer to rebuild next;
   * **birch is 20 % of `MIX_BASE`** and dead timber 7.5 %, so a quarter of every treeline
     is a pale stem. Not asset reuse, but it reads as "a birch wood" everywhere;
   * the weeds are placed on a single band pass, so they thin out beyond the rim + 26 m.
     A meadow-wide weed pass would help the far verges;
   * the road proxy is a *test* object. Once `build_barriers` has migrated, the honest
     evidence render is terrain + the real barriers module, and these frames should be
     re-shot against it.

11. **Open on OTHER modules, with the measurement attached, because these are the ones
    that will still be defects in the assembled world after this pass:**
   * **`build_architecture`** — `build_architecture.py:1453` still carries its own
     `-RIBBON_SAW_M - t` term, which saws its paving back to world x = 14.70 while
     `build_surface`'s ribbon starts at x = 15.000. The contract cannot reach into a
     module's private arithmetic. It should read `-t` (or, better, call
     `C.in_access_ribbon(..., margin=C.ACCESS_RIBBON_SAW_M)`). Until then a 0.30 m ×
     12.75 m slot stays open at the threshold — now floored by terrain's forecourt pad at
     −0.20 m instead of bottomless, but a 200 mm groove across the driving line at the
     frame the car breaches the glass. **Architecture must also now PAVE x 12.0 → 15.0**,
     which `apron_platform_mask` hands it as of contract 1.0.1 and which it was previously
     told to cut.
   * **`build_barriers`** — the 658 m² (§2.4). The obligation is
     `platform_edge − max(barrier_offset, runoff_edge)` and it is **42 076 m²** over the
     lap; 658 m² of it is unbuilt. Terrain welds to `platform_edge` and cannot fill the
     gap without a coplanar z-fight against the parts barriers *did* build.
   * **`build_sky`** — two measurements handed over, neither of them a request to regrade:
     `C.SKY_IRRADIANCE` excludes `SKY_Atmosphere`'s in-scattering and so under-predicts
     the shipped rig by 0.53–0.58 stops (§4, §9.2); and 23 km visual range costs 28.8 % of
     the contrast at 2 km, which is what `CAM_T10_HELI.png` is actually showing (§4.1).
