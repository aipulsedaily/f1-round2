# `build_surface.py` — the driving surface

Builds the 3 675.00 m racing surface, its kerbs, its markings and the unrubbered
concrete access road that carries the car from the breached glass wall onto the pit
straight. One module, one collection (`W_Surface`), idempotent, headless:

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py -- --verify
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py -- --render
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_surface.py -- --blend=contract
```

Everything is generated. There is not one image texture, HDRI or downloaded asset in
this module; every pattern is either explicit per-vertex geometry or a procedural node
network evaluated in 3-D world space.

---

## 0. THE CONTRACT — what changed, and the numbers

The assembly review found that six modules built in isolation destroy each other when
assembled. Three of its five findings landed on this file. `world/world_contract.py` is
now authoritative over it and **every shared number was deleted from here and imported
from there.**

| gone from `build_surface` | now | why it had to move |
|---|---|---|
| `_build_width` / `_S["half_w"]` | `C.half_width` | it was **0.978 m** out over **14.14 %** of the lap |
| `_build_cross` / `_cross_z` | inside `C.ground_z` | `build_barriers` needed banking and could not express it |
| `_undulation` (bulk) | inside `C.ground_z` | ditto |
| `_neg_kerb_z` | inside `C.ground_z` | the trough is ground, not decoration |
| the 12 mm verge drain (one line in `_build_road`) | inside `C.ground_z` | it was a number only this module knew |
| `_elements` position integration, `centreline`, `_centreline_arrays` | `C.centreline*` | duplicate implementation, contract RULE 1 |
| `_build_elevation`, `elevation_c` | `C.elevation_c` | duplicate implementation |
| `_S["neg_kerbs"]` derivation | `C.NEG_KERBS` | the serrated runs must split where the road actually dips |
| `_access_path`, the ribbon's own `z` and edges | `C.access_route_*` / `C.ground_z` | Beat 4 was a coplanar z-fight for 116 m |
| the test rig's invented sun and grade | `C.SUN_*` / `C.SKY_*` / `C.REFERENCE_EXPOSURE_EXTERIOR` | finding #5, committed inside a test harness |

**What is still this module's own**, and the only thing it adds on top of the datum, is
a racing-line micro layer: a −9 mm compaction dip along the driven line and a +4.5 mm
braking washboard. Contract §2 permits exactly that under two conditions, and both are
enforced by construction rather than promised — `np.clip` to `C.MICRO_LAYER_MAX_M`, then
multiplied by `C.micro_window(s, u)`, which is identically zero at and beyond
`half_width`:

```
surface_z(s, u)  ==  C.ground_z(s, u)  +  clip(micro, ±0.018) · micro_window(s, u)
```

### 0.1 Conformance, measured on every build

`build()` runs `verify()` and returns it under `summary["contract"]`; `-- --verify` also
writes `render/world/surface/contract_conformance.json`. Every line below is from that
file, against contract **v1.0.1**.

| what | measured |
|---|---|
| `half_width` vs the contract, whole lap | **0.000 m** (was max **0.978 m**, rms 0.156, **14.14 %** of the lap over 10 mm) |
| `half_width(3115.0)` / `(250.0)` / `(3085.0)` | **8.000 / 8.000 / 7.500** — transition starts at the element boundary, and is linear |
| road mesh vs `surface_z` at the exact `(s, u)` it was built from | **4.8e-7 m** (float32 vertex storage) |
| outer edge of `SURF_Track` vs `C.verge_edge`, both sides, every row | **0.000 m** |
| micro layer, 200 000 random points inside the racing surface | max **14.1 mm**, p99 **11.0 mm**, p50 **0.48 mm**, bound 18 mm |
| micro layer at and beyond `half_width` | **0.000 m** — a multiplication, not a promise |
| ribbon mesh vs `C.ground_z` | **2.6e-7 m** |
| ribbon over the 49.60 m apron run, max \|z\| | **0.000000 m** — spec §10.3(b) exactly, not to a tolerance |
| ribbon ↔ `SURF_Track` shared edge, **149.0 m** of it | **0.000 m** (with `C.access_z` it would be **80.2 mm**) |
| ribbon saw strip vs `C.access_ribbon_polygon(0.30)` | **1.7e-16 m** |
| Beat-4 scan, world y = 0, x −5…+111, at 0.25 m | **3** ownership changes, **0** unowned points |
| the same line as a **BVH raycast over the built meshes**, 465 points | max **1** surface at any point; **0** points with two; **0** coplanar pairs |
| negative kerb depth, T8 / T12, against the local cross-section | **−54.7 / −54.3 mm** (spec §9: −60 mm) |
| **corridor mouth: where each consumer's cut lands on x** (§5.7) | terrain **15.000**, paving **15.000**, bare polygon **15.000**, this mesh **15.000** — **max disagreement 0.000 m**, was **3.000 m** |
| the mouth on the review's own grid, x 4…17 × y ±14, 7 467 samples | **0** owned by terrain; `build_surface` owns x **15.10 … 17.00** and nothing behind the glass |
| **ribbon lying inboard of `C.verge_edge`** (§5.8) | **6.8 µm**, **0** vertices over 1 mm — was **49.99 mm** over **126** vertices |
| **apron joint** (§9): across-joint extent vs `C.verge_edge` | **−5.4 µm … +50.00 mm** — the inner edge *is* `SURF_Track`'s outer edge |
| apron joint inner edge vs `surface_z` at the same rows | **0.000 m** |
| the joint at the review's own s = 3247 / 3305 / 3361 | ray lands **−5 mm** below the datum, not **−300 mm** |
| **kerb foot embed below `C.ground_z`** (§3) | **−20.0 … −20.5 mm** vs `C.BASE_EMBED_M` = 20 mm — was **+21 mm with an open shell edge** |
| **BVH self-census, 58 objects, every pair** | **39** intersecting: **35** kerb-on-track (the contract's embed), **3** kerb-on-kerb (adjacent runs), **1** ribbon↔track (a shared edge, 6.8 µm lateral, 0.000 m in z) |
| **18 % calibration card in `albedo_probe.png`** (§10) | renders at **0.1850** against `C.lambert_radiance(0.18)`'s **0.1800** — **+2.8 %** |
| procedural texture nodes / image textures | **47** / **0** |

Two numbers in that file are **not** clean, and both are reported every build rather
than absorbed into a tolerance:

* **`contract_datum_sf_line_step_m` = 6.75 mm.** `C._undulation` evaluates value noise
  on raw `S`, which is not cyclic, so **the datum steps across the start/finish line**.
  The bug is originally this module's — the contract inherited the function verbatim —
  but it now lives in `world_contract` and only `world_contract` can close it (make the
  noise period a whole number of cells per lap, or ease the last 30 m into the first).
  It is inside `C.TOL_SEAM_M` = 10 mm and it falls under the 400 mm painted S/F line,
  but it is a step in **the** datum, on the pit straight, where the onboard follow
  crosses at 330 km/h. The road mesh itself is C0 across it: the wrap quad is 0.38 m
  long, so the step is a 1.8 % ramp over one row rather than an edge.
* **`contract_project_ds_max_m` = 44.0 mm** (`du` 1.25 mm). `C.project`'s nearest-sample
  search plus first-order correction is that far out in *station* at the 28 m hairpin
  radius at 10 m of lateral offset. It costs **0.6 mm of z**, and it is the entire
  difference between "is the mesh the datum" (4.8e-7 m) and "what does a neighbour
  asking `C.world_ground_z` get back" (0.6 mm, away from the S/F line). Recorded so
  nobody rediscovers it as a mystery.

---

## 1. What is in the collection

| object | what | tris |
|---|---|---:|
| `SURF_Track` | the whole lap as ONE welded cyclic mesh — asphalt, verges, negative kerbs, all markings. 7 598 rows × 69 columns, outermost column on `C.verge_edge(s)` | 1 033 328 |
| `SURF_Kerb_*` (35) | individually generated two-tone serrated kerbs, footed on `C.ground_z` | 1 448 622 |
| `SURF_AccessRoad` | the Beat-4 ribbon: breach → 49.6 m flat apron run → R150/40° merge arc → the closing gore, unrubbered concrete, built on `C.ground_z`, starting **exactly on the breach plane** `C.ACCESS_RIBBON_T_MIN` (§5.7) | 71 808 |
| `SURF_ApronJoint` | **new** — the declared lap at the track ↔ apron-platform boundary, `C.verge_edge` → +50 mm, 207.9 m of the pit-exit apron edge (§9) | 4 376 |
| `SURF_GridNum_01..20` | painted grid-slot numerals on the pit straight | ~1.8 k |

58 objects, **2 720 945 triangles**, build 53 s including the conformance gate.
Materials: `M_Surf_Asphalt`, `M_Surf_Kerb`, `M_Surf_Concrete`, **`M_Surf_Joint`**,
`M_Surf_GridPaint` — **47 procedural texture nodes, 0 image textures.**

The triangle count moved from 2 549 003 because every kerb gained a real track-side
riser (§3), the ribbon gained its end cap and a 45-column layout, and the apron joint
is new.

Idempotency is verified, not asserted: consecutive `build()` calls in one session return
an identical census and leave nothing in the scene root.

---

## 2. The decisions a later reader would otherwise have to reverse-engineer

The short version, if you read nothing else: **the road is built on the un-spiralled
element list so it stays locked to telemetry (§2.1); the racing line is solved from the
corner table and the spec's own lateral-acceleration model, not drawn (§2.3); and every
mid-scale pattern in the asphalt is cellular rather than fractal, because fractal noise
at the road's own width reads as camouflage (§2.5).**

### 2.1 The surface centreline is the EXACT element list, with no clothoids

Spec §6.1 says to insert Euler spirals at every straight↔arc junction. **This module
deliberately does not put them in the road**, and that is the single most consequential
choice in the file.

`telemetry.csv` — the project's declared single source of truth for all motion — was
integrated from the raw arc/straight element list with no transitions. A proper
clothoid shifts the arc laterally by `L_c²/24R`, which is **1.26 m at T1 and 2.67 m
through the T10b release**. Had the road been built on a spiralled centreline, the car
driven from telemetry would sit up to 2.7 m off where the road says it should be — a
fifth of the track width, and visible in every chase frame. Keeping the road on the
element list keeps car and road locked together.

What the clothoids actually buy is a smooth *steering and roll* channel, and that
belongs to the driven line and to the vehicle, not to the tarmac. So the transitions
that would have been in the geometry are applied instead to the things that are
genuinely surface attributes and genuinely would read as steps at 4K:

* **banking** eases in and out over ~45 m rather than switching on at the arc (a hard
  cross-slope step is very visible under the helicopter arc; a curvature step on a
  14 m-wide matte road is not),
* ~~**width transitions** use a raised cosine of the spec's 60 m support instead of the
  spec's "linear", so they are C1~~ — **WRONG, AND IT WAS THE BUG.** See §0. The
  raised-cosine was applied *centred on the element boundary* instead of starting there,
  which is what made `half_width(3115)` come out 7.022 instead of 8.000; and even
  correctly centred, a C1 rounding is only safe if all five consumers adopt it, which is
  precisely the assumption that produced the strip of unbuilt ground down both edges
  of the pit straight. The spec says linear, `C.half_width` is linear, and the
  0.95° deflection a 1 m width change over 60 m puts in the road edge is a construction
  joint a real circuit has,
* **the racing line** is smooth to second order everywhere.

### 2.2 The element list — positions now come from the contract

`circuit_spec.json` publishes each element's `start_world` rounded to 1 cm. Rebuilding
the centreline from those values puts a **5.8 mm position step at each of the 31
element joints**. Geometrically that is nothing. But sampled at 0.25 m stations it
reads as 0.08 of spurious curvature — four times the hairpin's real curvature — and it
made the first version of the racing-line drivability solver chase rounding noise. The
answer is to re-integrate the element list forward from the datum (329.396, 169.820) on
bearing 40.000°.

**That reasoning is unchanged; the implementation moved.** `C.centreline` /
`C.centreline_arrays` do the integration now, and this module's `_elements()` keeps only
the *table* — tag, type, radius, turn, length, start station — because the kerb plan and
the racing-line solve are indexed by corner and the contract does not publish that
mapping. `prepare()` checks the provenance rather than trusting it: every element start
`C.centreline` returns is compared against the spec's own published `start_world`, and
the build raises if any is more than a centimetre out (**measured 5.8 mm**, which is the
published rounding itself).

### 2.3 The racing line is solved, not drawn

Requirement: a rubbered line that *tightens through apexes*, following the real racing
line. There is no racing-line polyline in the spec, so it is derived from the corner
table and then constrained by the spec's own vehicle model.

**How it is painted on** is as consequential as where it runs, and the first version got
it wrong in a way that only a plan-view render exposes. The band was a core out to
`spread` plus a halo out to `spread*3.3 + 1.6 m` — **14.5 m on the pit straight, wider
than the road**. Rendered from the helicopter arc that is not a racing line, it is one
side of the tarmac being darker than the other, and it reads as a lighting error. A
rubbered band is a legible object, so it is now built as one:

| part | width | what it is |
|---|---|---|
| heart | `0.55 × spread` | flat, fully rubbered, the width the cars actually use |
| shoulder | to `1.05 × spread` | the fall-off, about a metre |
| feather | to `min(1.9 × spread + 0.9, 0.78 × half-width)` | the smear, never to the edge |
| tyre tracks | ±0.82 m either side of the line, 0.20 m wide | measured off the 2.005 m car |

The half-width cap is what keeps clean tarmac against the white line however much the
cars fan out. `spread` itself comes from telemetry lateral load — 1.05 m at the hairpin,
3.9 m on a straight — so the band **tightens through the apexes on its own**, which is
the requirement, rather than being drawn tight.

**Construction.** For every corner: a turn-in key at the far edge, an apex key at the
inside edge, a track-out key at the far edge.

* the apex station is moved **late** in proportion to slowness — 20 % of the arc below
  120 km/h, 11 % to 190, 4 % above (a driver sacrifices entry for exit exactly in
  proportion to how much exit there is to be had);
* the apex offset puts the car's inside wheel over the white line and onto the kerb
  (`Wh − 0.55` for the car centre, against a measured 2.005 m car), except on the two
  fast kinks where the full kerb is not used (`Wh − 0.85`);
* **lead and trail come from the approach speed, not the apex speed** — read out of
  `telemetry.csv` 70 m before and 50 m after the arc. The car is already on the far
  edge while it is still braking from 296 km/h into an 80 km/h hairpin, so an
  apex-speed rule hands T4 a 20 m turn-in ramp, which is wrong by a factor of three;
* corners with a large turn angle get an **apex dwell** rather than a point apex. The
  classic `R_line = R + w/(sec(θ/2) − 1)` is worth **+0.5 m at 176°** — the width buys
  a hairpin nothing, and the car simply rides the inside through the middle of the
  arc. Dwell scales with turn angle and is zero below 40°.

**Collision resolution.** Keys closer than 26 m are merged. Two adjacent edge keys
collapse to their mean, which is precisely what turns the T6–T9 esses from a zig-zag
into one flowing diagonal — the "straightening the esses" the spec asks for falls out
rather than being drawn.

**Room-to-move clamp.** Between two corners 40–55 m apart (the esse links, and S12
between T12 and T13) the purely geometric answer swings the car from edge to edge: the
first version produced a **14 m radius at 115 km/h, about 25 g**. A raised-cosine
excursion of `Δu` over `L` needs `2Δu·π²/L²` of path curvature, so each edge key is
clamped to the excursion its neighbouring apexes actually afford, at 55 % of the §7
lateral budget.

**Drivability solve.** Finally the line is relaxed until its curvature satisfies

```
kappa(s) <= max( 1.06 * |k_centre| / (1 - u*k_centre) ,  1.03 * a_lat(v) / v^2 )
```

with `a_lat(v) = min(15.0 + 0.0050 v², 48.0)` and `v(s)` from telemetry — the spec's own
§7 model. The first term matters: the spec solved every apex speed so the *centreline*
sits exactly on the lateral limit, so the vehicle term alone leaves the line no
headroom inside a corner. The honest statement is "never tighter than riding the inside
edge of the corner you are in", and inside a 176° hairpin that concentric value *is*
the racing line.

Two traps were hit and are worth recording:

* a **curvature-masked blend diverges** — blending a smoothed line in under a spatially
  varying mask injects fresh curvature at the mask edges, which grows the mask, which
  … The solver now smooths the mask on the scale of the smoothing, keeps the
  best-so-far by residual, and widens the relief scale instead of iterating harder;
* the measured curvature is **low-passed over 2 m** before the residual is taken,
  because the un-transitioned centreline steps its curvature at every element joint and
  a difference stencil turns each step into a spike.

**Verified result.** Peak lateral load implied by the drawn line is **4.33 g** against
the circuit's design maximum of 4.89 g at T3. Minimum radius **21.0 m**, which is
`28 − 6.95` — the hairpin's inside line, exactly as it should be. Every apex sits on
the inside edge; every corner except the hairpin has a line radius larger than the
track radius.

`racing_line_offset(s)` is exported. **The car and camera builders must use it** — if
the car drives a different line from the one the rubber is painted on, the whole
surface reads as wallpaper.

### 2.4 The road is crowned and banked — and that is now `C.ground_z`, not a local secret

`C.ground_z(s, u)` is **the** datum. It carries everything below, and it is why the
review's finding #1 cannot recur through this module:

* elevation from the spec's PVI stations with symmetric parabolic vertical curves —
  reproduces the spec's realised extremes exactly (**z_min −3.666 m, z_max +7.964 m**);
* banking per §4 with the sign convention *outside high*, T8's 1° adverse and T4's
  −1.5 %-easing-to-flat entry camber from `camber_overrides`;
* a **parabolic drainage crown**, 1.45 % mean cross-fall at the edge, suppressed
  wherever the road is deliberately banked, and reduced by 45 % on the pit straight and
  the transit route because §2 declares those one plane with the paddock;
* low-frequency undulation, wavelengths ≥ 3 m only: 30 mm at 46 m, 14 mm at 15 m,
  5.5 mm at 5 m. Everything shorter than ~2 m is carried by the shader, which resolves
  it far better than 0.7 m rows could;
* the **negative-kerb troughs** and the **12 mm verge drain**;
* and, outboard of `verge_edge`, the **−1.6 % runoff fall taken from the banked road
  edge**, which is the thing the old `build_barriers.ground_z` could not express.

**The lateral is signed, and that is not cosmetic.** `build_barriers` and
`build_dressing` spoke `(lat, side)` with `lat ≥ 0`. Banking is antisymmetric in `u`, so
a datum in `|lat|` cannot carry it — which is exactly why the barriers datum was ±0.69 m
out at the verge edge on T10/T11. Every lateral this module passes is signed.

`surface_z(s, u)` is still exported, but it is now `C.ground_z` **plus** the bounded
racing-line micro layer (§0). Other modules should call `C.ground_z`; call `surface_z`
only if you specifically want the driven-line compaction dip — the car's contact patch
does, a barrier post does not.

Consequence to be aware of: at the T10/T11 sweeper the racing line sits **0.48 m below
the centreline**, because 4° of banking across 7 m is 0.49 m. Telemetry's `z` is the
centreline value. Anything placed at the racing line must add `C.ground_z`.

### 2.5 Nothing is instanced, and the anti-tiling is structural

The user's red line is "no one tree spammed 100 times". For a surface the equivalent
failure is a repeating texture, and it is avoided by construction rather than by
disguise:

* **there is no tile.** Every asphalt pattern is a 3-D procedural evaluated at object
  coordinates, which for this object equal world coordinates. A noise or Voronoi
  evaluated over a 1 900 m domain has no period. Float32 at 950 m resolves 0.06 mm, so
  even the 0.6 mm micro layer is clean;
* **eleven detail scales**, chosen against what a pixel is worth at the two closest
  camera stations rather than by eye: the doppler hover is 26 m out on a 50 mm lens
  (4.9 mm/px at 4K) and the T4 kerb-height camera is ~5 m out on a 21 mm (2.2 mm/px).
  A 14 mm chip is 3 px at the first and 6 px at the second, so the aggregate has to
  *be* 14 mm. The first pass used 80 mm cells and read as smooth tarmac in a macro
  crop — the whole point of rendering the macro test;

  | layer | size | carries |
  |---|---:|---|
  | macro 2 | 140 m | pour-to-pour tint drift |
  | macro 1 | 33 m | age/bleaching drift |
  | **paver mats** | **9.5 m** | **mixer-load tone, by CELL ID — see below** |
  | saw-cut grid | 34 × 4.4 m | rectangular patch repairs in road space |
  | segregation | 0.65 m | chip-rich / binder-rich mottling |
  | coarse stone | 30 mm | the few big faces that make it read as stone |
  | aggregate | 18 mm | the bulk of the chips |
  | intermediate | 9 mm | fills between the 18 mm faces |
  | fines | 4 mm | mortar stone, paint chipping mask |
  | grain | 2.3 mm | surface grain, weak bump |
  | micro | 0.6 mm | weak bump only |

  The **aggregate is applied as a multiplicative contrast field, not as a mix toward a
  chip colour.** That is the single most important line in this file and it was found
  by measuring, not by looking: a plan-view albedo render of the first version returned
  a dry-tarmac reflectance of **≥ 0.083** — light concrete — because three separate
  layers each mixed toward a bright chip colour and each one lifted the mean. With the
  tarmac that bright the rubbered line had nothing to be darker than, and the circuit
  read from the air as one grey ribbon. Multiplying leaves the mean on the zone colour,
  so the delivered reflectance is now, **measured the same way on the shipped material**
  (plan views under a uniform dome, 3rd/50th/92nd percentile of road pixels between
  0.012 and 0.115 albedo, so paint, kerbs and verge are excluded):

  | station | rubbered line | median | clean tarmac | ratio |
  |---|---:|---:|---:|---:|
  | T1 | 0.0281 | 0.0604 | 0.0757 | **2.69** |
  | the esses | 0.0281 | 0.0520 | 0.0684 | **2.43** |
  | T12 | 0.0281 | 0.0604 | 0.0808 | **2.87** |
  | T4 hairpin | 0.0288 | 0.0550 | 0.0684 | **2.37** |
  | pit straight | 0.0281 | 0.0452 | 0.0626 | **2.23** |

  A real heavily-used circuit runs 2.2–2.6 : 1 off-line to line, and dry dense-graded
  asphalt sits at 0.04–0.09. Both are now inside the band, at every station, and the
  spread between stations is the resurfacing zones doing their job.

* **nine resurfacing zones** around the lap, each with its own age, base colour,
  paving-lane width and lane phase, separated by transverse construction joints placed
  where a resurfacing contract would actually stop (a corner exit or a straight end,
  never mid-apex). The pit straight is the freshest — it takes the start every year;
* **paver mats from a Voronoi CELL ID at 9.5 m, ±13.5 %.** This is deliberately the
  strongest mid-scale layer, and it is safe to be strong *because it is cellular*: each
  mixer load went down at its own temperature and compacted to its own tone, and the
  boundary between two loads is a line. The equivalent smooth-noise version at the same
  scale is what made the first helicopter frame read as camouflage — fractal noise at
  the road's own width is a cloud, a Voronoi cell is a paving mat;
* longitudinal paving-lane joints whose spacing and phase differ per zone, each with a
  350 mm screed-edge shoulder 16 % lighter than the middle of the mat (a 30 mm joint
  cannot be seen from 100 m up; the shoulder can); crack-sealant tar snakes that only
  appear in the old zones; timing-loop saw cuts at the line and both sector splits;
* **repairs in the two shapes a circuit actually carries** — irregular *milled* areas
  from a Voronoi id, and *saw-cut* patches that are rectangles in road space with a
  25 mm bitumen-sealed kerf round the perimeter, because a saw cuts straight lines. The
  rectangles come from a 34 m × 4.4 m cell grid in (s, u) with a per-cell hash choosing
  which cells carry one and how big it is and where inside the cell it sits: ~25 per
  lap, no two the same size. The first version had only the Voronoi family, at a
  0.02-wide id window on 16 m cells — **four patches on the entire 3 675 m lap**, which
  is why the first plan view came back as an unbroken ribbon;
* **every kerb is a separate mesh with its own parameters** — see §3.

---

## 3. Kerbs

Geometry is the spec's **corrected** §9 figures, not D's self-contradictory ones:
1.50 m wide, **25 mm proud at the track-side lip, 50 mm at the outer lip, 25 mm
serration amplitude on a 250 mm pitch → 75 mm peak**, red/white at 1.00 m alternation.
Against 340 mm of measured ride height that leaves 265 mm of plank clearance, so the
car can use every kerb on the circuit.

35 runs are generated from a per-corner plan (`KERB_PLAN`) in which **every entry
carries the reason it exists** — apex kerbs everywhere, turn-in kerbs only where the
car arrives at the edge still braking (T1, T4, T10, T12), exit kerbs sized to the
runoff behind them. T6's exit kerb doubles as T7's turn-in kerb because that is how
esses are kerbed.

Sampling is 31.25 mm, i.e. **8 samples per serration**, so the sawtooth is real
geometry, not a bump map.

### 3.1 The track-side riser, which was missing

spec §9 puts the kerb **25 mm proud at its track-side lip**, and the profile duly began
at **+21 mm above the road with nothing between the two**. The kerb was an open shell
whose leading edge floated over the asphalt along **all 35 runs**: a 21 mm slot at a
sun with a **4.52 shadow ratio**, i.e. a dark line down the inside of every kerb on the
circuit, and a place a ray can get under the geometry entirely.

Two columns now sit at `t = 0.000` so the step is a real vertical face, and its bottom
sits **`C.BASE_EMBED_M` (20 mm) INTO the datum** — the contract's own published embed
for anything standing on the ground, and what stops a 10 mm mesh tolerance opening a lit
gap under it. The normal comes out right by construction: the column direction at the
riser is `+z`, so `T × (0,0,1)` faces the track, exactly as the outer face's `T ×
(0,0,−1)` faces the verge.

**Measured on the built meshes:** kerb foot embed **−20.0 … −20.5 mm** (`C.BASE_EMBED_M`
= 20 mm, so the check is `≤ −0.020` and it passes on every run), riser height up to
**58.3 mm** including the serration. Cost: **160 958 triangles**, 1 609 580 total.

The 35 kerb↔`SURF_Track` pairs the BVH self-census reports are this embed, and they are
the contract's, not a defect — §4 of `WORLD_CONTRACT.md` requires it. The census also
reports **3 kerb↔kerb** pairs (adjacent runs whose end ramps overlap by design) and
**one** ribbon↔track pair, which is a shared edge and is measured as such in §5.8.

### Per-kerb variation — what actually differs

No two kerbs share a mesh, a length, or a parameter set. Each run is seeded from its
index and gets its own:

* **precast section length** (1.85–2.25 m), and per-section **height step**
  (σ = 2.2 mm) and **roll** (σ = 3.5 mrad) — real kerbs are cast in units and never lie
  perfectly flush, and this alone makes every kerb unique at close range;
* **paint block length** (0.955–1.055 m) and **phase**, so the red/white blocks land
  differently against the serrations on every kerb;
* **serration phase**, so the sawtooth does not start in the same place twice;
* a **wear field** peaked where the cars actually strike — 42 % along an inside kerb,
  72 % along an exit kerb — which flattens the serrations by up to 55 %, takes the paint
  off the peaks first, and drives the rubber smear;
* **impact damage**: 2–6 individually knocked-down serration groups per kerb at random
  stations and widths;
* **end ramps** of different lengths (1.1–2.8 m) at each end;
* **pigment identity**: two random parameters per kerb take the red from deep oxide to
  sun-bleached orange-pink and the white from clean to grey.

The paint blocks are crisp because a per-vertex `blk` attribute counts blocks as a
continuous index — `floor(blk)` even is red, odd is white — which survives jittered
block lengths without needing split geometry.

**Negative kerbs** are the spec's true negative kerbs, not "negative sausage kerbs":
−60 mm deep, 0.80 m wide, at the T8 apex and the T12 exit only. They are cut into the
road mesh's kerb band with rounded lips and 1.6 m end ramps, and the serrated run is
split around them.

---

## 4. Markings

* **track-edge white line**, 100 mm, outer edge on the track limit;
* **green painted verge**, 1.0 m outboard of every kerb, with a 100 mm white line on its
  inboard lip — and plain asphalt shoulder where there is no kerb;
* **start/finish line**, 400 mm across the full width at s = 0, with timing-loop saw
  cuts before it and at both sector splits (s = 1200, s = 2450);
* **20 grid boxes**, staggered, 2.6 × 6.0 m with a 100 mm outline, pole on the left,
  which is the inside for T1. Numerals are real glyph geometry projected onto the
  surface (so they follow the crown) at 3.5 mm of paint thickness;
* **pit-exit lane lines and gore chevrons** on `SURF_AccessRoad` — see §5.5; they are
  this module's because architecture cuts `ARCH_Markings` to the ribbon polygon;
* **pit-exit blend line** on the track, solid white, from the merge at s = 3459.4 converging over
  90 m — the spec's own description of what a pit exit is;
* **launch rubber** — twenty pairs of black stripes off the twenty grid slots, each
  decaying over 13–18 m as that car hooks up, each with its own length and intensity.
  It is the most recognisable marking on any pit straight and the beat-5 onboard follow
  runs straight over it;
* **paint wear**, driven by the rubber field and by distance from the driven line, so
  the paint on the pit straight is scuffed exactly where the cars cross it and intact
  where they do not. Worn paint reveals the aggregate underneath through the 4 mm chip
  mask, and where it is scrubbed it **greys off rather than vanishing**: these lines are
  repainted for the meeting, so what takes them off is tyres crossing them, not age.
  The first version added 0.45 of 33 m macro noise to the wear, which deleted the
  track-edge line for 40 m at a time — a *dashed* white line, which at a race circuit
  means something entirely different;
* **rubber**, **marbles** and **lock-up streaks** are all read out of `telemetry.csv`:
  deposit density from traction and braking and lateral load, the dark core's width
  narrowing where lateral load is high (all cars on one line) and widening on the
  straights, four wandering skid streaks whose intensity follows `−a_long`.

## 5. The access ribbon — the µ change, and the Beat-4 fix

Spec §7 declares µ 1.00 on the circuit and **0.90 on the unrubbered access road**, and
§10.5 declares the apron run as concrete. `SURF_AccessRoad` is therefore a genuinely
different surface, not a tint: broom finish, 4.5 m saw-cut contraction joints across and
4.0 m construction joints along, **per-slab tone from a hash of the bay index (±14.5 %,
plus a laitance term)** because every bay was poured and floated on its own day and
jointed concrete always reads as a chequer of greys, no rubbered-in line at all, and a
single pair of launch streaks fading out over the first 34 m because **the car has been
down here exactly once**. The per-slab tone is what says "concrete" at 40 m, where the
broom finish and the 20 mm joints are both sub-pixel.

### 5.1 What was wrong

Scanning the review's own line — world y = 0, x −5 → +111 — the winning surface flipped
**six times over 116 m** between `SURF_AccessRoad`, `ARCH_Paving_Paddock`,
`ARCH_Paving_Apron` and `ARCH_Markings`, at separations of **1.4–9.0 mm**. At 4K with a
flying camera that is stroboscopic depth fighting straight through the beat the brief
calls the world-design linchpin. The previous version of this note said "the paddock
builder should cut around the ribbon rather than overlap it", which is the right fix
addressed to nobody.

### 5.2 Who owns each square metre

`C.TOL_COPLANAR_M`'s rule is **cut, do not offset**, and the contract names the owners:

| | |
|---|---|
| driving surface of the transit route | **`build_surface`** — it is a road, it is continuous with the racing surface it merges into, and it must share that surface's datum exactly or the merge is a seam at 219.5 km/h |
| its markings | **`build_surface`** (§5.5) — architecture cuts `ARCH_Markings` to the same polygon it cuts its paving to, so if they were not painted here the pit exit would have none |
| the walled corridor | **`build_barriers`**; `ARCH_ApronCorridor` is deleted by name |
| everything outside the polygon | `build_architecture`, cut to `C.access_ribbon_polygon(margin=0.30)` |

`_build_access` builds **exactly that polygon's interior**, so architecture's cut line
and this mesh's boundary are the same line. Verified: the mesh's outboard offset from
`C.access_edges` matches `ACCESS_SAW_M` to **1.7e-16 m** wherever the edge is free.

### 5.3 The sawn edge strip — TWO edges, TWO gates

The contract describes its polygon's 0.30 m margin as "the sawn edge strip
`build_surface` lays along the ribbon". It is laid — but only where there is a slab to
butt.

**The inboard edge fades.** Past route station **t = 95.33 m** the ribbon's inboard edge
has converged onto `SURF_Track`'s painted verge; there is no slab to butt to, and a
0.30 m overhang there would be a 0.30 m *coplanar overlap* on the runoff platform — the
exact defect being fixed. `free_in = v_in − (verge_edge − u)` gates it.

**The outboard edge must not.** The first version gated *both* strips on `free_in`,
which is a property of the inboard edge alone. So the outboard strip vanished over the
last 150 m of the ribbon while `build_architecture` went on cutting its apron slabs
0.30 m clear of the declared edge — an unbuilt strip along the outboard edge over every
station the two share. The outboard gate is now a direct question to the contract:
**who owns the ground 150 mm beyond this edge?** `C.world_ground_z` answers; where the
answer is `build_architecture:paving` the strip is laid at full width, and where it is
`build_barriers:runoff platform` it is not, because that platform butts `verge_edge`
with no inset and is not cut to the ribbon.

The gate is **dilated before it is smoothed**. A plain mean filter rounds the shoulders,
and the strip came out **0.273 m** where architecture was still cutting at 0.300 — a
27 mm gap, the same class of defect one row further out. Dilating by 2.0 m and then
smoothing over 1.5 m makes the strip provably full width wherever the neighbour is
architecture. **Measured: `ribbon_saw_out_shortfall_max_m` = 0.000 over the 122.9 m of
route where `world_ground_z` names architecture.**

### 5.7 THE CORRIDOR MOUTH AT THE GLASS PLANE — assembly defect #2

Three modules used three different margins for the same boundary, and **nobody built
x 12.0 → 15.0**. On the review's grid — 0.10 × 0.5 m over x 4…17, y ±14 — **1 276 of
7 467 samples had no usable ground (~64 m²)**: a continuous 3.0 m deep band across the
whole 12 m driving width, **0.300 m of it fully open**, at the exact metre the car and
the camera pass through as the glass breaches (`CAM_GLASS_GAP.png`).

The cause is one line. `in_access_ribbon` tested `tt >= -margin`, so each consumer
walked the ribbon's **start cap** back through the glass wall by its own margin:

| module | margin | cut landed at |
|---|---:|---:|
| `road_corridor_mask` | `ACCESS_CORRIDOR_MARGIN_M` 3.00 | x **12.00** |
| `build_architecture` | `RIBBON_SAW_M` 0.30 | x **14.70** |
| `build_surface` | none on the cap | x **15.000** |

**This module did not choose a fourth margin.** Behind the glass is the showroom floor —
round 1's `Floor`, 30.0 × 22.0, top z = 0.000, world x −15…+15 (spec §10.1), and the
re-levelled `ExteriorGround` (spec §10.3(b), exactly z = 0.000 over world x 10…90).
Paving 3 m of it from here would have been a **3 m × 12.6 m coplanar overlap with
`Floor`** in the hero frame: a hole traded for a z-fight, which is precisely the shape of
mistake the integration round was called to stop making.

Contract **1.0.1** settled it instead — `ACCESS_RIBBON_T_MIN = 0.0`, the breach plane,
pinned for every consumer and every margin, with the lateral keep-out
(`ACCESS_CORRIDOR_MARGIN_M`, terrain's) and the lateral joint (`ACCESS_RIBBON_SAW_M`,
paving's) separated so they can never be conflated again. This module **reads the pin**:

```python
RIBBON_T_MIN     = float(getattr(C, "ACCESS_RIBBON_T_MIN", 0.0))   # 0.0
RIBBON_CAP_END_M = ACCESS_SAW_M                                    # 0.30, the far cap
```

so the number stays settled in the contract and the mesh follows it. `verify()` asks all
four consumers where their cut lands and publishes the spread:

| consumer | cut lands on x |
|---|---:|
| terrain keep-out, margin 3.00 | **15.000** |
| paving joint, margin 0.30 | **15.000** |
| bare polygon, margin 0.00 | **15.000** |
| **this mesh** | **15.000** |
| | **max disagreement 0.000 m** (was 3.000) |

and re-runs the review's own 7 467-sample grid through `C.world_ground_z`: **0 samples
owned by terrain**, `build_surface` owning x **15.10 … 17.00** and nothing behind the
glass. `glass_cap_plan.png` is that metre in true-scale plan with all three historical
cut lines drawn on it.

### 5.8 The clip has to be made in WORLD terms, not in route terms

Found by the BVH self-census, not by reading the code.

`C.access_edges` clips the ribbon's inboard edge with `E − U` evaluated at the **route
centreline**, and this mesh then offsets from that centreline along the **route normal**.
Over the R150 merge arc the route heading and the track heading differ by up to
**11.2°**, so an edge that is exactly `verge_edge` in route coordinates lands
`v·(1 − cos Δθ)` *inside* it in world coordinates.

**Measured on the built mesh: 126 vertices up to 49.99 mm inboard of `C.verge_edge`,
around s = 3430 / t = 125** — the ribbon lying **on the racing surface**, at exactly the
same `ground_z`, i.e. a **zero-separation coplanar pair of ~1.9 m²** in the middle of the
Beat-4 merge. It is small and it is the worst kind there is, and it had been there since
the ribbon was first clipped.

Three fixed-point passes against `C.project` push the edge back out; the correction is
second order so it converges to microns. **Now 6.8 µm, 0 vertices over 1 mm.**

### 5.4 The ribbon is `C.ground_z`, and `C.access_z` is not

This is the one place this module deliberately departs from a contract v1.0.0 function,
and it is departed from with a measurement rather than an opinion.

`C.access_z(t, v)` eases from the flat apron onto `ground_z` with a weight that is a
function of `t` **alone**, completing at the merge point t = 154.32. But the ribbon
starts **sharing an edge** with `SURF_Track` at t = 95.33. Along the 149.0 m of shared
edge, `access_z` therefore sits up to **80.2 mm** above `ground_z` (max **89.5 mm**
anywhere on the ribbon) — **8× `C.TOL_SEAM_M`**, on a boundary two modules share, in the
beat the camera flies at rooftop height.

Measured instead: **`C.ground_z` is already exactly 0.000000 over the whole 49.60 m
apron run**, at every lateral across the ribbon and 0.30 m beyond both edges. The
contract's own apron tie (§7 of `WORLD_CONTRACT.md`) does it, because `apron_zone` is
1.000 along the whole approach. So the ribbon is built on `ground_z` and nothing else:

* spec §10.3(b)'s "first 50 m outside the glass exactly 0 % and exactly level with the
  interior floor" holds **exactly**, not to a tolerance — max \|z\| **0.000000 m**;
* the join to `SURF_Track` is **0.000 mm** for the whole 149.0 m the two meshes share
  an edge;
* there is **one** datum function under the whole beat, which is the entire point of
  the contract.

`C.access_z` is therefore redundant and should be retired, or redefined as `ground_z`,
in the next contract revision. `verify()` measures **both** numbers on every build so
the claim never becomes a memory.

The old crown is gone with it. `−0.0125·|u|^1.7` put the ribbon edge 75 mm below the
apron, violating §10.3(b) and §10.5; so did the 10 mm of surface noise that used to be
added on top. A poured slab is flat — its texture is the broom finish and the joints,
which are the shader's.

### 5.5 The markings this module now owns

Everything is keyed off a second UV, `uv_edge` = (distance from the inboard edge,
distance from the outboard edge), because **both edges are converging curves** and a
line painted at a fixed lateral would walk off the slab.

* **100 mm continuous white either side** — the pit-exit lane (spec §10.5). The inboard
  one is dropped where the ribbon has merged onto `SURF_Track`'s verge and the track's
  own blend line takes over: `M_Surf_Asphalt` paints that from s = 3459.4 over 90 m,
  which is exactly where this one stops;
* **45° chevron hatch** in the closing wedge, 0.30 m of paint on a 1.20 m pitch, which
  is what a real pit exit paints on the gore;
* both weather by abrasion and sun rather than by tyres, because there are no tyres
  here — they chalk against the macro tint, pick up the grit relief underneath, and are
  cut by the saw joints.

### 5.6 What the neighbours must cut — measured, so nobody has to guess

| | |
|---|---:|
| total ribbon area | **1 426 m²** |
| of which outboard of `verge_edge`, i.e. on top of the runoff programme | **282 m²** |
| over lap stations | **s 3401.9 … 3549.4** |

`C.world_ground_z` gives the ribbon priority over the platform, so **`build_barriers`
must cut its runoff platform to `C.access_ribbon_polygon(margin=0.0)` over that
stretch** or 282 m² of platform and ribbon are exactly coplanar — both are `ground_z`,
so the separation would be 0.000 m, which is the worst kind of z-fight there is.
`build_architecture` cuts to `margin=0.30`; the two cut lines differ, deliberately, and
both coincide with this mesh's boundary where they apply.

---

## 6. Interfaces for the other builders

**Prefer `world_contract`.** Everything geometric that another module needs is there,
and importing it does not drag `bpy` or this module's 240-iteration racing-line solve
along:

```python
import world_contract as C
C.ground_z(s, u)                # THE datum.  signed u, + = left of travel
C.world_ground_z(x, y)          # -> (z, owner) for any world point
C.half_width(s) / C.verge_edge(s) / C.platform_edge(s, side)
C.access_ribbon_polygon(0.30)   # architecture cuts to this
C.access_ribbon_polygon(0.00)   # barriers cut to this  (see §5.6)
```

What is genuinely this module's, and is not in the contract:

```python
import build_surface as S
S.prepare()                     # cheap; no scene changes

S.racing_line_offset(s)         # lateral offset of the driven line, +ve = left
S.surface_z(s, u)               # C.ground_z + the racing-line micro layer (<= 18 mm,
                                # zero at and beyond half_width).  The car's contact
                                # patch wants this; a barrier post does not.
S.verify()                      # the conformance dict in section 0.1
```

`S.centreline`, `S.elevation_c`, `S.track_half_width` and `S.su_to_world` are kept as
aliases of the contract's functions so old call sites do not break, but new code should
name the contract. `S.outer_edge(s, side)` is `C.verge_edge(s)` on `C.ground_z` — the
outermost point of this module's geometry, verified to **0.000 m** on every row of the
built mesh, and it is **not** at z = 0: it carries the crown, the banking and the
undulation, so query it rather than assuming a plane.

---

## 7. Test renders — what was looked at, and what it changed

Under `render/world/surface/`, **rendered on the rented RTX 5090** — 3840 × 2160 at
512–768 samples for the assembly round — via `tools/r5090`. Eight blends
(`world/surface_test_{contract,surface,macro,ribbon,rake,probe,defects,joint,jointoff}
.blend`, ~57 MB each) carry 1–5 named cameras apiece — deliberately small, because
the worker prewarms every camera in a blend at load and a 19-camera blend once blew a
readiness probe and destroyed an instance. `-- --blend=<group>` writes one.

| frame | what it is for |
|---|---|
| **`pit_edge_16m.png`** | **s = 3115.0, where the 16 m pit straight opens.** The stand-in platform starts at `C.verge_edge` *exactly*, so if this module's road edge fell short of it — as it did by 0.978 m — the frame shows daylight through the gap |
| **`merge_seam.png`** | **route t = 104 → 150**, raking along the 149 m edge the ribbon shares with `SURF_Track`, so a millimetre of step would catch the 12.47° sun as a lit line. With `C.access_z` the step here is 48 mm (80 mm at t = 95) |
| **`apron_flat.png`** | the 49.60 m apron run at Beat-4 camera height: dead flat at z = 0.000 per spec §10.3(b), and the pit-exit lane markings this module now owns |
| `access_road.png` | the µ 0.90 concrete — broom finish, saw-cut bays, per-slab tone |
| `doppler_pass.png` | the spec's exact hover station, (−578.82, −47.47, 4.802), aimed **down**-road |
| `hairpin_kerb.png` | kerb height, z = 0.80, **outside** T4 looking across — the hero corner |
| `straight_low.png` | onboard height down the pit straight: grid, S/F line, faded paint |
| `grid_launch.png` | the grid itself: launch rubber, boxes, numerals, S/F line |
| `sweeper_air.png` | T10/T11 from helicopter altitude: does the line read from above |
| `wide_repeat_check.png` | wide over the esses, explicitly hunting recognisable repeats |
| `macro_asphalt.png` | ~1.3 m of frame: aggregate, segregation, joints, tar snake — **with an 18 % lambertian card in shot** |
| `kerb_macro.png` | ~1 m of kerb: serrations, precast joints, paint blocks, wear — same card |
| `negative_kerb.png` | the T8 apex negative kerb, **across** the trough from the track side |

### 7.0 The frames added for the assembly round, and what each one settles

All on the 5090, 3840 × 2160 at 512–768 samples except the A/B pair, which is
2560 × 1440 because it is a 1.24 m macro and the joint is 55 px wide either way. Blends:
`surface_test_{defects,joint,jointoff,probe,rake}.blend`. Every other frame in the table
below was re-rendered against the new material at 3840 × 2160.

| frame | what it settles |
|---|---|
| **`glass_cap_plan.png`** | **assembly defect #2.** 24 m of the corridor mouth in true-scale plan with all three historical cut lines drawn: **magenta x = 12.000** (terrain's old keep-out), **amber x = 14.700** (paving's old saw), **cyan x = 15.000** (`C.ACCESS_GLASS_X`, contract 1.0.1's pin). The ribbon's cap edge lands **on the cyan line**; the magenta and amber lie on bare ground that belongs to the showroom floor. There is no 0.300 m slot because there is no longer a fourth answer |
| **`apron_joint_BEFORE.png` / `apron_joint_AFTER.png`** | **assembly defect #3, as an A/B on one variable.** 50 mm at 1.24 m looking **across** the joint at 37°, against `TEST_ApronNb` — a stand-in built to `build_apron_platform`'s *measured* numbers and nothing else: bay inset **12 mm**, sub-base **0.300 m** down. BEFORE has `SURF_ApronJoint` deleted; AFTER has it. **Measured off the two frames, 144 scan columns:** the joint line reads **64.3 % darker** than the surface beside it before, **37.6 %** after — a **1.71×** reduction, and the absolute floor goes **0.047 → 0.099** linear. The black line is now a lit groove |
| **`apron_joint_rake.png`** | the same joint at 0.35 m off the deck, **92 m** down the pit-exit apron edge, raked by the 12.47° sun — the condition that turned a 12 mm gap into a black line down 220 m of pit straight |
| **`albedo_probe.png`** | **photometric, not pictorial** (§10.1). `view_transform = 'Standard'` at `C.REFERENCE_EXPOSURE_EXTERIOR`, so the pixel **is** linear reflectance. 12.0 m of pit straight in true-scale plan at 3.125 mm/px with an 18 % card **laid on the datum corner by corner**. The card renders at **0.1850** against `lambert_radiance(0.18)`'s **0.1800** |
| **`rake_low.png`** | 0.60 m off the deck along the sun's own azimuth: at 12.47° a surface either has relief or is revealed as a painted plane |

Plan-view orthographic maps are in `render/world/surface/plan/` — `lap`, `t1`,
`hairpin`, `esses`, `sweeper`, `t12`, `straight`, `grid`, rendered under a uniform white
dome with the Standard view transform so they are close to albedo. **They are the tool
that found most of the defects below**: a lit perspective frame hides a missing racing
line, a 1 100 px plan view of 90 m of road does not. They are also what the reflectance
figures in §2.5 were measured from. They predate the contract migration and are still
valid for the material, which did not change; regenerate them if it is ever retuned.

### 7.1 The harness itself was two of the review's findings

* **The light was invented.** `_mk_sun` used to build its own sun — energy 5.0, colour
  (1.000, 0.705, 0.435), aerosol 1.6, ozone 2.0 — and grade at −0.85 stops with an
  `AgX - Medium High Contrast` look. Every material in this module was tuned under it.
  That is finding #5 committed inside a test harness: a surface calibrated against a
  light that does not exist looks wrong the moment `build_sky` is switched on. It is now
  `C.SUN_*` / `C.SKY_*` verbatim, and the grade is `C.VIEW_TRANSFORM` / `C.VIEW_LOOK` /
  `C.REFERENCE_EXPOSURE_EXTERIOR` = AgX, Look **None**, **−3.048 stops** — the film's one
  lens and one grade. **Every frame in the table above is 2.2 stops and a tone curve
  away from the frames the previous version of this note describes; read them as a fresh
  set, not as a comparison.**
* **The ground was invented too.** The stand-in terrain was a hand-tuned drop table hung
  off this module's own cross-slope — which is how a test harness ends up validating a
  road against ground no other module builds. It is now `C.ground_z` out to
  `C.platform_edge` (the same surface `build_barriers` paves) and only batters away
  beyond the corridor rim. It is built **once for the whole 3 675 m lap** in the 5090
  blends, so every camera in a group sees the same world; the old per-shot rebuild meant
  two frames could disagree about the ground and neither would show it.
* **An 18 % lambertian card** sits 0.55 m to one side of the aim point in the two macro
  frames — beside the tarmac, not on top of it; the first version was 1.20 m and filled
  the frame it existed to calibrate.
* **The rig was checked against `C.lambert_radiance`, in linear EXR, not by eye.** Two
  large lambertian planes at albedo 0.18 and 0.07, 512 samples, `max_bounces = 0`,
  Standard transform at exposure 0:

  | albedo | rendered (linear R, G, B) | `C.lambert_radiance` | ratio |
  |---:|---|---|---:|
  | 0.18 | (1.7804, 1.5640, 1.4416) | (1.6744, 1.4600, 1.3321) | **1.0715** |
  | 0.07 | (0.7929, 0.6968, 0.6423) | (0.6512, 0.5678, 0.5180) | 1.2274 |

  Fitting the red channel: **rendered = 8.977·a + 0.165** against the contract's
  **9.302·a**. The slope is **3.5 % below** `lambert_radiance` and the 0.165 pedestal is
  Principled's residual specular against the sky dome, which `lambert_radiance`
  deliberately does not model. At a = 0.18 the total is **+0.100 stops**. The rig *is*
  the contract's light, to a tenth of a stop, and now it is a measurement rather than an
  assertion.
* **And the tarmac was then measured against the card, in the same frame.**
  `macro_asphalt.png`, 2560 px, 512 samples: card **0.4508** display, tarmac beside it
  **0.3998**, tarmac further up **0.3498**, the painted line **0.6319**. Run back through
  the linear calibration above, 0.3498 display is the AgX image of an **0.07 albedo**
  surface under this light, which is exactly the middle of the 0.045–0.081 band §2.5
  measured on the shipped material. **The asphalt is correctly calibrated under the
  contract's light; it was not calibrated to a different one and rescued by exposure.**
* **What the film's grade does to this material, honestly.** AgX with Look = None at
  −3.048 stops is a much flatter transform than the `AgX - Medium High Contrast` at
  −0.85 the previous frames used, and the macro crop reads *softer* because of it: the
  aggregate is all there at 0.41 mm/px but its contrast is compressed. That is the grade
  the film ships with, so it is the right frame to judge from — but if a later pass wants
  more bite in the tarmac at close range, the lever is the aggregate's multiplicative
  contrast, **not** exposure and **not** the base colour, both of which would move the
  measured albedo out of band. Re-check §2.5's table against `C.lambert_radiance` if it
  is ever touched.

`--render` (local 1070, 1280 × 720) takes `--only=name[,name…]` for fast iteration; the
published frames come from the 5090 path.

### 7.2 What the stand-in still cannot show, so do not read it as evidence

* Beyond `C.platform_edge` the stand-in batters away at 6 m rows down to −22 m. In
  `sweeper_air.png` that reads as coarse polygonal facets and in `access_road.png` it
  throws a large shadow across the frame. **Neither is this module's geometry**; the real
  ground there is `build_terrain`'s, welded to `C.corridor_rim_polyline`.
* The pit-exit apron that `build_architecture` will pave at z = 0.000 is not in these
  frames either, so `access_road.png` shows the ribbon crossing the batter instead of a
  paved apron. The ribbon's own z is `C.ground_z` and is verified against it to
  **2.6e-7 m**; what is missing is the neighbour, not the datum.
* The dark band along the horizon in several frames is the sky **below** the horizon
  line — nothing yet fills the far field. Task #25's.

The dark band along the horizon in several frames is the **sky below the horizon line**,
not a hole: the stand-in ribbon ends 320 m out and nothing yet fills the distance. The
treeline and terrain are task #25's.

**Fifteen defects were found by looking at the frames, not at the code**, and the last
seven of them were only found because the frames were *measured* as well as looked at.
Items 9–15 are a second pass over a version that already had a note claiming it was
finished — the first eight below were real, but the frames that "proved" them were
rendered from a mid-edit copy of this file, and the surface that actually shipped was a
uniform grey ribbon with no racing line on it. Everything in this section is now backed
by a frame rendered from the file as it stands.

1. **The test sun was below the horizon.** A Blender SUN emits along its local −Z, so
   the local Z axis must be the direction-*to*-sun; the first version negated it. The
   whole first batch came back flat, shadowless and sky-blue, and it read as a material
   problem until the light was checked.
2. **The aggregate was five times too coarse.** 80 mm Voronoi cells read as smooth
   tarmac in a 3 m macro crop. Rescaled against millimetres-per-pixel at the two closest
   camera stations (§2.5), and graded across three chip sizes on warped coordinates
   because one scale reads as a quilt.
3. **The helicopter frame read as camouflage.** Two causes. The 33 m macro noise was
   swinging the asphalt age by ±0.21 — exactly the road's own width, so the surface
   looked cloudy from above; reduced to ±0.08. And the rubber's streak modulation used
   `P × (0.1, 0.1, 1)`, which is **isotropic in plan** and produces blobs, not streaks.
   Rebuilt on the metric UV as 0.31 m across × 18 m along, plus a finer tyre-width
   layer, with the contrast pulled from 0.62–1.18 down to 0.84–1.08.
4. **The stand-in ground plane hid the subject.** At the doppler station the road falls
   at −2.82 %, so a plane pinned to the local z rises through the track 100 m out.
   Replaced with a ribbon that follows the centreline — and its innermost column had to
   be moved to `Wh + 2.50`, the module's true outer edge, or the road overhangs it and
   you see daylight underneath.
5. **The kerb paint looked like watercolour.** A 0.30 blotch mix at 0.38 m made every
   kerb mottled. Real kerb paint is flat; the variation belongs in the wear field. Blotch
   to 0.13, white pulled down from 0.66 to 0.50 so it stops blowing out.
6. **Every grid numeral was mirrored.** A driver walking up the grid reads the numbers
   with +s away and their own right hand at −u, so glyph +x maps to −u. They were also
   1.6 m behind the tail of the box; they now sit beside it, outboard, where a real grid
   paints them.
7. **The racing line disappeared from the low pit-straight frame.** Rubber was dropping
   roughness by 0.30, and at a grazing angle the specular gain from a smoother surface
   exactly cancelled the albedo loss — the band was *brighter* than the asphalt around
   it. Reduced to 0.12: the sheen survives, the line reads.
8. **The kerb paint wore away in fog.** The wear mask was driven by the vertex's
   absolute height above the road, which across a kerb is just a ramp, so the shader
   turned it into a smooth cloud over the whole kerb. What it needs is the *serration
   phase*, which is now baked as its own attribute — the concrete shows through in
   crisp bands on the ridge tops, which is what a struck kerb actually looks like.

### Second pass — found by measuring the frames, not by looking at them

9. **The tarmac was light concrete, and it was what hid the racing line.** An emission
   plan view of the shader's Base Color, sampled across the road, returned **≥ 0.083**
   reflectance off the line. The rubber was working the whole time; there was simply
   nothing for it to be darker *than*, and every layer that was supposed to add
   character had been tuned against a base two shades too pale. Fixed by making the
   aggregate multiplicative (§2.5). Off-line reflectance is now 0.063–0.081 by zone,
   the rubbered heart 0.028, a 2.2–2.9 : 1 ratio — measured the same way, on the
   shipped material, at five stations (table in §2.5).
10. **The racing line had no edge.** Its halo ran to `spread*3.3 + 1.6 m` = 14.5 m on a
    16 m road, so from the air the road was simply darker on one side — a gradient, not
    a line. Rebuilt as heart / shoulder / feather with the feather capped at 78 % of the
    half width (§2.3). The esses plan view now shows the flowing diagonal the corner
    table implies, and it was the frame that proved it.
11. **Four patch repairs on 3 675 m of road.** The Voronoi id window was 0.02 wide on
    16 m cells. Added the saw-cut rectangle family and widened the milled window: ~25
    repairs per lap, none the same size (§2.5).
12. **The track-edge white line was dashed.** 0.45 of 33 m macro noise in the paint wear
    was deleting it for 40 m at a time. Wear is now dominated by distance from the
    driven line, floored at 0.42, and worn paint greys instead of disappearing.
13. **The tarmac rendered blue.** `Specular IOR Level 0.38` on a roughness-0.8 surface
    puts enough sky in the lobe to turn a warm-grey binder cold at every grazing angle
    the film uses, and grazing angles are most of them. Dropped to 0.24 and the binder
    warmed; the sheen on the rubbered line survives, the sky comes off the rest.
14. **The stand-in runoff was a hillside, and it ate the doppler frame.** The TEST
    ribbon fell 0.55 m in the first 7 m and 3.2 m by 48 m; from the spec's hover
    station — 26 m out, 2.4 m over the road — that put the lens level with the tarmac
    plane and made the road a 2°-thick line under 70 % of stand-in ground. Spec §9
    gives this station 55 m of *asphalt* runoff and asphalt runoff drains at 2–3 %, so
    the profile is now 2–3 %. The frame is also aimed down-road rather than across it:
    at 26 m and 2.4 m the surface is genuinely at a 5° grazing angle, and the useful
    test is 50 m of continuous tarmac, not the vanishing point.

15. **The stand-in ground ate the inside of the track.** Fixing 14 by flattening the
    runoff exposed a bug the steep profile had been hiding: the ribbon's innermost
    column was *flush* with the verge, but the real road edge carries up to 30 mm of
    undulation and a 12 mm verge drain that the ribbon does not reproduce, so it poked
    through along a wandering line. With a 2–3 % cross-fall it stayed high for metres
    and the sweeper frame came back with a **jagged sawtooth of stand-in terrain eating
    the inside edge of the track** — which looks exactly like a shader defect and is
    not one. The ribbon now starts 70 mm below the verge.

**One process defect, recorded because it cost more than any of the above.** The eight
test frames that the first version of this note cited as evidence were written by a
render that was still running while the module was being edited underneath it. The
frames on disk and the code on disk did not describe the same surface, and two of the
defects "fixed" above (the camouflage, item 3) were only fixed in the code — nobody had
re-rendered to confirm, and the confirming frame still showed the bug. **Never cite a
frame whose mtime is older than the module's.**

Two `_SHOT_NOTES` strings (console labels only) were edited during the final render, so
the frames on disk are technically 90 s older than `build_surface.py`. Rather than
assert that the edit was cosmetic, it was **checked**: `sweeper_air` was re-rendered
from the final file and compared to the copy taken during the run — 9 958 differing
pixels of 921 600 at RMSE 2.5 × 10⁻⁵, which is the OIDN denoiser's own non-determinism
and not a change in the surface. That is the standard of proof this note now holds
itself to.

~~**Exposure was calibrated, not guessed**… sun 5.0 W/m² warm (1.0, 0.705, 0.435)
against sky 0.40… **None of this is the film's grade**.~~ **SUPERSEDED — that was the
problem.** A material tuned under a light nobody else uses is finding #5. The rig is now
`world_contract` §8 verbatim and the frames *are* shot at the film's grade; see §7.1.

### Third pass — the contract migration, and what the frames caught this time

16. **The width transition was centred on the element boundary, not started at it.**
    `_build_width` set the 16 m span to `[3115 + 30, 250 − 30]` and then smoothed it
    with a ±30 m raised cosine, so `half_width(3115)` came out **7.022 instead of
    8.000** — max **0.978 m**, rms 0.156 m, over **14.14 %** of the lap. Because
    `build_barriers` pins the runoff, the painted verge, the advertising boards and the
    barrier line to `verge_edge = half_width + 2.50`, that left a **strip of unbuilt
    ground down both edges of the pit straight: 0.978 m at its worst, more than 10 mm
    wide over 520 m of the lap, mean 0.170 m inside that band.** The assembly review
    reported it as "a 0.63 m strip"; that figure reproduces as neither the peak nor the
    mean, so the measured ones above are what this module publishes. Deleted;
    `C.half_width`.
    `pit_width_plan.png` renders the defect as a magenta band floated over the ground it
    used to leave bare: **pixel-measured against the frame's own scale (15.61 px/m) the
    band is 0.936 m wide at s = 3122 against 0.938 m predicted, and 0.641 m at s = 3094
    against 0.647 m** — and it now lies entirely on tarmac.
17. **The test harness's stand-in ground spanned a quad across the road.** Found by
    rendering `pit_width_plan` and seeing 30 m-long olive teardrops *on the tarmac*: the
    first version of the rewritten `_test_props` emitted one continuous quad strip, so
    the chord from −`verge_edge` to +`verge_edge` cut straight across the road at the
    two edge heights. The road only crowns up 0.10 m between them, so anywhere the
    undulation or the banking lifted the chord it punched through. Two disjoint quad
    blocks now, one per side. **This is the same class of bug as the review's finding
    #1, committed in a test harness, and only a plan view would ever have shown it.**
18. **The ribbon fought the paddock for 116 m at 1.4–9.0 mm.** See §5. Fixed by cutting,
    not offsetting. Verified two ways: `C.world_ground_z` along the review's own scan
    line gives **3 clean ownership changes and 0 unowned points**, and a **BVH raycast
    straight down over the built meshes at 465 points along that line finds a maximum of
    ONE surface at every point, 0 points with two surfaces and 0 coplanar pairs**.
19. **`C.access_z` would have left an 80 mm ledge along the ribbon/track joint.** §5.4.
    `merge_seam.png` is the frame: a 35 mm lens raking down the joint at 1.2 m, where a
    millimetre of step catches a 12.47° sun as a lit line. Built on `C.ground_z` there
    is nothing there — concrete meets asphalt and the only line in the crop is the
    painted one.

### Fourth pass — the assembly round, found by measuring the assembled world

The five defects the assembly verification raised against the world were found in the
**assembled** scene, not in any module's own tests. Two landed here. Four more were
found on the way to fixing them, all four by a measurement rather than by reading:

20. **A 0.300 m × 12.75 m fully-open slot at the glass plane** (§5.7). Three modules
    walked the ribbon's start cap back through the showroom wall by three different
    margins. Closed in contract 1.0.1 by pinning the cap; this module reads the pin
    instead of choosing a fourth answer. **Max disagreement across all four consumers:
    3.000 m → 0.000 m.** `glass_cap_plan.png`.
21. **A 12 mm × 300 mm open joint down 220 m of the pit-exit apron edge** (§9). Two
    surfaces both stopping on `verge_edge` while one of them insets its bays 12 mm.
    Closed with a declared lap. **Joint line 64.3 % → 37.6 % darker than the surface
    beside it**, measured off `apron_joint_BEFORE/AFTER.png` on 144 scan columns.
22. **The ribbon lay 50 mm ON the racing surface over the merge** (§5.8) — 126 vertices,
    ~1.9 m², zero separation, both on `ground_z`. Found by the **BVH self-census**, which
    is a check this module did not have before and which `tools/collision_gate.py`
    cannot answer on a blend with no car in it. **49.99 mm → 6.8 µm.**
23. **Every kerb on the circuit floated 21 mm over the road with an open shell edge**
    (§3.1). Found by asking why the same census reported 35 kerb-on-track pairs and then
    measuring what the kerb's inner column actually did. **+21 mm and open → −20.0 mm and
    a real riser**, `C.BASE_EMBED_M`.
24. **The outboard sawn strip vanished for the last 150 m of the ribbon** (§5.3),
    because both strips were gated on a number that describes the inboard edge. Fixed
    by asking `C.world_ground_z` who owns the ground beyond the edge. **Shortfall
    0.000 m over the 122.9 m where architecture owns it.**
25. **The asphalt had been tone-mapped out, not under-authored** (§10). Every layer the
    review said was missing existed. The base sat **2.49 stops** into AgX's toe, the
    rubber collapsed to **0.012** albedo, and the 18 mm aggregate was being warped by
    **±15 mm** — as much as the cell. Found with a photometric probe whose 18 % card
    lands on **0.1850 against 0.1800**, i.e. a frame in which the pixel is the albedo.
    A test that cannot be argued with is worth more than a test that looks nice.

---

## 8. Known limits / handover notes

* **Displacement is bump-only.** The material is authored so that switching
  `displacement_method` to `'BOTH'` and adding adaptive subdivision on selected
  stations would give true micro-displacement; it is off because dicing 3 675 m of road
  at 4K is not a sensible default. Asphalt relief is 1–3 mm and bump holds it at the
  closest station in the film (~4 m at T4) — verified in `macro_asphalt.png`.
* **The two finest bump layers are deliberately weak (0.42 and 0.58, not 0.60 and
  0.75).** A 0.6 mm and a 2.3 mm normal perturbation is far below the ray footprint
  past about 8 m, so beyond that they are pure noise: Cycles samples them at random
  within the pixel and OIDN smears the result into swirls. That is what the original
  "camouflage" helicopter frame actually was — not the albedo layers it was blamed on.
  **If a later pass raises them, re-check `sweeper_air.png` and check it for temporal
  flicker in motion, not just in a still**: undersampled bump is a per-frame random
  field and will crawl.
* **Anything that adds mid-scale variation must be cellular, not fractal.** Smooth
  noise at 5–40 m — the road's own width — is a cloud, and a cloud on tarmac reads as
  camouflage or as a lighting error. Voronoi cells at the same scale read as paving
  mats, saw cuts and patches. Every strong mid-scale layer in this material is cellular
  for that reason; the fractal layers are all held under ±10 %.
* **The verge is where this module stops.** Runoff asphalt, gravel, grass and barriers
  are task #24's; the boundary is `C.verge_edge(s)` and it is met to **0.000 m**.
* **The out lap is not the flying lap.** The rubber band is a season of cars, not this
  one run: at s = 0 the drawn line is at u ≈ −4.8 while the transit blend puts the car
  on the centreline. That is correct, not a mismatch.
* ~~**The access-road ribbon and the paddock apron are coplanar at z = 0** where they
  meet. The paddock builder should cut around the ribbon rather than overlap it.~~
  **Fixed — see §5.** The ribbon is now exactly `C.access_ribbon_polygon(0.30)`'s
  interior and the review's scan line shows 3 clean ownership changes and 0 unowned
  points. Three things this module cannot do itself, and they are the handover:
  1. **`build_architecture` must cut `ARCH_Paving_*` and `ARCH_Markings` to
     `C.access_ribbon_polygon(margin=0.30)`.** That polygon's boundary *is* this mesh's
     boundary; nothing overlaps and nothing is left bare. **Its own `-RIBBON_SAW_M - t`
     and `t - (ACCESS_TOTAL + RIBBON_SAW_M)` cap terms must go** — contract 1.0.1 pins
     the start cap at `ACCESS_RIBBON_T_MIN` = 0.0 and a module that keeps its own
     longitudinal margin reopens the 0.300 m slot on its own side, where the contract
     cannot reach it (§5.7).
  2. **`build_barriers` must cut its runoff platform to
     `C.access_ribbon_polygon(margin=0.0)` over s 3401.9 … 3549.4.** The ribbon rides
     282 m² of the platform there and both are `C.ground_z`, so uncut they are coplanar
     at exactly 0.000 m separation.
  3. **`build_architecture`'s forecourt bay grid skips any bay overlapping the pavilion
     footprint** (`bx0 < 15.05`), so it lays nothing over world x **15.0 … 16.5** — and
     the ribbon only covers `|v| ≤ 6.30` there. Measured on the review's own grid, that
     leaves x 15.0 … 16.5 at 6.30 < |y| ≤ 9.0 with no ground. `C.world_ground_z` says
     architecture owns it. It is 1.5 m of the Beat-4 mouth just outside the ribbon's
     sawn strip and it is **not** this module's — the ribbon's edge is exactly where
     architecture cuts to (§5.3, shortfall 0.000 m over 122.9 m of route). A bay that
     straddles the building line should be **clipped, not skipped**.
* **Two contract defects are recorded, not worked around** (§0.1): the datum steps
  **6.75 mm** across the start/finish line because `C._undulation` is not cyclic, and
  `C.access_z` disagrees with `C.ground_z` by up to **89.5 mm** on the ribbon. Both
  survive into **v1.0.1**. The first needs a `world_contract` edit — this module cannot
  fix it without disagreeing with the datum. The second is already routed around here,
  with the number published every build; `access_z` should be retired or redefined as
  `ground_z`.
* **A third is now closed and is worth recording as closed:** `in_access_ribbon`'s start
  cap. v1.0.0's `tt >= -margin` gave three consumers three different answers for the
  same boundary and cost **64 m²** of the Beat-3 → Beat-4 hinge; v1.0.1 pins it at
  `ACCESS_RIBBON_T_MIN` = 0.0 and separates terrain's 3.0 m **keep-out** from paving's
  0.30 m **joint**. This module reads the pin rather than choosing a margin, so the
  number stays settled in one place (§5.7).
* **`C.access_edges` clips in ROUTE coordinates and the ribbon is offset along the
  ROUTE normal** (§5.8). Over the merge arc those differ by up to 11.2°, so the clip
  lands up to 50 mm inside `verge_edge` in world terms. This module now corrects it with
  three fixed-point passes against `C.project` — **6.8 µm residual** — but any other
  module that offsets from the access route and expects to land on `verge_edge` will hit
  the same thing. It belongs in `access_edges`.
* **The apron joint is a DECLARED LAP, not a seam** (§9). `SURF_ApronJoint` occupies
  `verge_edge … verge_edge + 50 mm` over 207.9 m and sits 1.6–5 mm below the datum. A
  coplanar gate that does not know about it will report 50 mm × 207.9 m of
  `build_surface`-vs-`build_architecture` overlap under `C.TOL_COPLANAR_M`; that is the
  lap doing its job, and it is why the constant is published as
  `build_surface.APRON_JOINT_LAP_M` and read from the contract if the contract ever
  defines it. **The right end state is `build_apron_platform` starting its bay grid at
  `verge_edge + APRON_JOINT_LAP_M` with no perimeter inset**, at which point the overlap
  is zero and the groove is the joint.
* **The kerb riser is 20 mm of deliberately buried geometry** (§3.1). The BVH self-census
  reports 35 kerb-on-track pairs and they are `C.BASE_EMBED_M`, not defects. Do not
  "fix" them by lifting the kerbs.
* Grid numerals use Blender's bundled vector font (application-supplied glyph outlines,
  the same category as its Voronoi texture — not a downloaded asset). If the font is
  unavailable the numerals are skipped and the boxes still build.
* **Debug handles are left in.** Key intermediate sockets in the asphalt graph are
  labelled `DBG:<name>` by `_G.tag()` (`rub`, `core`, `on_track`, `paint_a`, `chip_hi`,
  `patch`, `dust`, `base_dry`). To see any layer on its own, find the node by label,
  feed it to an Emission and render a plan view — that is how defects 9–12 were located
  in a graph of ~450 anonymous nodes. Do not remove the labels.
* **What still has room in it, honestly.** At 100 m+ the tarmac reads as a ribbon with
  a band on it and little else: the paver mats and repairs are at the limit of what a
  pixel can carry there, which is also true of the real thing, but if the beat-6 closing
  wide wants more history in the surface the place to add it is more repairs and more
  zone contrast, not more noise. The racing line's contrast is in the right band
  (2.2–2.9 : 1, table in §2.5); if it is ever pushed further, push the *clean* asphalt
  up rather than the band down, and re-check the white lines and the kerb against it.

---

## 9. THE TRACK ↔ APRON JOINT — assembly defect #3, and the lap that closes it

**The finding.** `SURF_Track`'s outer edge ends at `u = 10.500 = C.verge_edge(s)`.
`ARCH_Paving_ApronPlatform`'s first bay starts at `u = 10.512`, because
`build_apron_platform` lays a regular 2.4 × 3.0 m grid whose first column is
`verge_edge.min()` and then insets **every** bay by 12 mm — and its own inboard
clearance test, `d_in = u − verge_edge`, is `+0.012` there, so it never fires. Between
the two the ray falls **0.300 m** to the sub-base. Verified at s = 3247 / 3305 / 3361,
over the whole **220 m** of the pit-exit apron. At a **12.47°** sun with a 4.52 shadow
ratio that is a black line down the pit straight — literally the grey line at the track
edge the user named.

**Why it is not fixable by moving either edge.** `verge_edge` is where this module's
road *ends*; the same coordinate cannot also be where the neighbour's slab *begins*
unless one of them **laps** the other, and a lap has to be somebody's declared geometry
with a number attached. Two surfaces both stopping on a shared coordinate and hoping is
what produced the defect, and it would produce it again at whatever new coordinate the
two agreed on, because the 12 mm is an *inset*, not a position.

**build_surface laps**, because it owns the datum the joint is cut in, and because an
asphalt-to-concrete joint is physically a feature of the **asphalt** side: a formed
groove, sealed with bitumen, and never a void.

`SURF_ApronJoint` runs from `u = verge_edge` — exactly `SURF_Track`'s outer edge, the
**same row stations**, the same `C.ground_z`, so the butt is **0.000 mm by construction
rather than by tolerance** — out to `verge_edge + APRON_JOINT_LAP_M`, with a 5 mm
sealant invert and a 1.6 mm lap that tucks under whatever the neighbour lays:

| across the joint | z |
|---|---|
| `+0.000 m` | `ground_z` — the track edge, exactly |
| `+0.008 m` | `ground_z − 5 mm` — sealant invert |
| `+0.022 m` | `ground_z − 5 mm` |
| `+0.032 m` | `ground_z − 1.6 mm` |
| `+0.050 m` | `ground_z − 1.6 mm` — the lap |

**Three outcomes, all of them correct**, which is the point of lapping rather than
butting:

| what the neighbour does | what is seen |
|---|---|
| starts at 10.512 (today) | a 12 mm wide, **5 mm** deep sealed joint groove — not a 12 mm wide, **300 mm** deep slot. Photographed as an A/B against a stand-in built to those exact two numbers: the line goes from **64.3 %** darker than the surface to **37.6 %**, floor **0.047 → 0.099** linear (§7.0) |
| adopts the lap and starts at 10.550 | the whole 50 mm groove is the joint, lit, and it reads as a construction joint because it is one |
| butts exactly at 10.500 | the strip is entirely under the slab, 1.6 mm below it, and there is nothing to see |

**Where it is applied, and where it is deliberately not.** Only where
`C.apron_zone(s, +1) > 0.5` — the identical predicate `build_apron_platform` uses to
decide the apron exists (`keep = WC.apron_zone(S, +1) > 0.5`). Everywhere else the
outboard neighbour is `build_barriers`' runoff platform, which butts `verge_edge` with
no inset and needs no lap; lapping it would be **3 675 m × 2 sides of new coplanar
overlap**, i.e. a much larger defect than the one being closed.

And **not where the Beat-4 ribbon is the neighbour.** The apron platform and the ribbon
both reach `verge_edge` on the left of the pit straight and overlap over **s 3402…3429**;
there the track's neighbour is `SURF_AccessRoad`, which butts `verge_edge` exactly on the
same `C.ground_z` and needs no joint at all. Laying one put this module's own two meshes
1.6 mm apart over **1.35 m²** — caught by the BVH self-census, not by reading the code,
and cut with `C.in_access_ribbon(margin=ACCESS_SAW_M)`. Built length **207.9 m** over
s **3195.8 … 3403.7**.

**The material is not black.** The defect reads as a black line because a 0.300 m void
is unlit. A real sealed joint is weathered bitumen at roughly the reflectance of the
tarmac beside it — `M_Surf_Joint`'s palette is bounded at **0.024 … 0.093** and its
variation is in the trodden-in grit and the sheen, not in the tone. Anything darker
would reinstate the line this geometry exists to remove.

`APRON_JOINT_LAP_M` and `APRON_JOINT_DEPTH_M` are read from the contract if it ever
publishes them, so the number can be settled there without touching this file.

---

## 10. THE ASPHALT — why it read as "a flat grey gradient", measured

The assembly review's verdict on the largest continuous surface in the film was that it
rendered as a flat grey gradient with no aggregate, tar seams, patches or rubber pickup.
All four of those layers **existed in the material**. The reason they were not on screen
turned out to be arithmetic, not authorship, and it took a photometric probe to see it.

### 10.1 The probe: make the pixel a number

`albedo_probe` is a true-scale plan view of **12.0 m across the pit straight at
s = 3500**, 3840 px wide (**3.125 mm/px**), with a **1.00 m 18 % lambertian card** laid
**on the datum corner by corner** — a flat card at the aim point's z floats 50 mm over a
crowned road, and at a 12.47° sun that throws a 226 mm shadow and makes the calibration
reference the brightest error in frame.

It is rendered with `view_transform = 'Standard'` at `C.REFERENCE_EXPOSURE_EXTERIOR`,
**not AgX**. That is the whole trick: under this light and this exposure a lambertian
albedo-`a` horizontal surface lands on linear `a` exactly —
`a/π · (E_direct_h + E_sky) · 2^−3.048 = a · 0.99994` — so **the pixel is the albedo**
and "is the aggregate reading" becomes arithmetic.

**The card renders at 0.1850 against a target of 0.1800: +2.8 %.** That single number
validates `C.SUN_*`, `C.SKY_*`, `C.REFERENCE_EXPOSURE_EXTERIOR` and `lambert_radiance()`
end to end, in a render, on the 5090.

### 10.2 What the probe found

| | before | after |
|---|---:|---:|
| whole-frame delivered albedo (mean) | **0.0423** | **0.0528** |
| clean tarmac, u +1.4…+3.4 | **0.0424** | **0.0522** |
| rms contrast at the 6 mm scale, clean tarmac | 0.353 | **0.336** |
| rms contrast at the 19 mm scale (the chip scale) | 0.293 | **0.183** … see below |
| rms contrast at 19 mm **inside the rubbered band** | **0.141** | **0.160** |

Three separate mistakes, each measured:

**(a) The base was two and a half stops into AgX's toe.** The previous pass drove the
zone colours to 0.032 (fresh) / 0.076 (old) because a plan-view render measured 0.083
and read as light concrete *next to a rubbered line that was not dark enough*. The fix
went to the wrong end of the ladder. Mid grey is albedo 0.18; a 0.032 surface sits
**2.49 stops** below it, in the part of AgX where the curve's slope is lowest, so the
±0.5 multiplicative chip contrast the material generates arrived on screen compressed to
a fraction of a stop. **The aggregate was built and then tone-mapped out.** The ladder is
now 0.060 fresh / 0.136 old — real values for dense-graded asphalt (fresh 0.045–0.055,
bleached 0.10–0.13) — which puts the delivered surface at **1.15 stops** below mid grey,
on the straight part of the curve.

**(b) The rubber collapsed to 0.012.** The band multiplied to 0.24 and then mixed 0.70
of the way to 0.0128 — landing a fully-rubbered heart *below fresh asphalt, below the
sealant, below anything else on the circuit*. What makes a racing line read is the
**ratio**, not the absolute: a rubbered-in line measures 0.028–0.035 and is a third of
the bleached tarmac beside it. Now `×0.60` then `mix 0.20`, so 82 % of the chip contrast
survives through it — and the meso relief suppression under the band went 0.55 → **0.28**,
because rubber *fills the mortar*, it does not plane the stones off. Before the change
the hero surface of the onboard follow was the smoothest thing in frame.

**(c) The 18 mm aggregate had been warped out of existence.** The coordinate feeding the
18 mm Voronoi carried a **±15 mm** warp — as large as the cell it was warping. Every
stone was smeared into its neighbours and the layer degenerated into high-frequency
noise: at 3.1 mm/px the probe came back as **sandpaper**, grain everywhere and not one
stone the eye could resolve as a stone. The warp is now **6.5 mm**, which distorts the
cell outlines the way crushing does and leaves them cells.

Two more followed from looking at the 1:1 crop rather than the histogram:

* **there was no mortar.** The chip window `0.05…0.46` called almost the whole cell a
  chip top, so the field was a dense even stipple — embossed rubber, not graded
  aggregate. Narrowed to `0.03…0.33`, with the binder term widened to `0.30…0.62`, each
  stone gets a saturated flat face and there is binder-rich mortar between them.
* **the height field was a field of domes.** `mr(agg_d, 0.0, 0.45)` is a smooth dome per
  cell, which is exactly what pebbled rubber looks like. The bump is now driven by the
  chip field itself: flat faces with a sharp shoulder, which is what a crushed stone
  bedded in binder is.

### 10.3 Three lithologies, not a hue ramp

A quarry delivers one rock; a circuit resurfaced nine times has several, and a single
load is itself a mix. The previous version ran a **continuous hue ramp** across the
cells — and a continuous ramp averages to grey at any distance where a cell falls under
a pixel, which is exactly the doppler station. Three **discrete** stone colours selected
by a per-cell hash keep their identity when they average, because the average of three
separated colours is not one of them: pale quartzite (1.26), mid granodiorite (1.02),
dark basalt (0.70), plus an uncorrelated draw on the 9 mm layer.

The hash had to change too. A `SMOOTH_F1` Color output is a **blend** of the neighbouring
cells' colours, so using it as a per-stone identity gives every stone a tone that fades
into the next one — which is precisely how three discrete lithologies average back to one
grey. A hard `F1` twin at the same scale on the same warped coordinate supplies the ids;
its cells *are* the smooth layer's cells and its colour is constant across each of them.

### 10.4 What was added, and why each one is a real thing

| layer | what it is | why it earns its nodes |
|---|---|---|
| **pluck-outs** | 20–60 mm sockets where a stone has come out: dark rough floor, 1.45 of negative height | the most recognisable "this is a used road surface" cue at the macro station, and the one thing a Voronoi field can never produce — a Voronoi has no holes |
| **binder flushing** | bitumen risen through the mat: 0.66× albedo, **−0.30 roughness**, meso relief suppressed | nearly invisible in plan and blazes at a 12.47° sun, which is the condition every frame in this film is shot under; it is also the cheapest thing that stops 3 675 m of tarmac reading as one material |
| **drainage runnels** | pale mineral wash running **across** the road at the cross-fall | the one direction nothing else in this material runs, so it breaks the longitudinal grain of the streaks, the lane joints and the racing line at once |
| **anisotropy** | specular lobe stretched along `uv_su`'s station axis, 0.06 → **0.55** through the band | tyres polish stone *along* the direction of travel; at a grazing sun that is the difference between a dark stripe and a surface that has been driven on. The tangent is the road's own, corner by corner, for free |
| **glass beads** | 0.2–0.8 mm retro-reflective ballotini in the line paint: +34 % albedo, −0.34 roughness | it is what circuit line paint is dressed with, and sub-pixel specular that averages to a slightly brighter, sharper line is exactly what a beaded line does on camera |
| **kerb biofilm** | olive-black algae in the serration valleys, outboard half, scrubbed off where the tyres strike | a kerb is a damp shaded horizontal concrete surface with water-holding valleys; this is the detail that separates one that has stood through a winter from one just extruded |
| **concrete map crazing** | `DISTANCE_TO_EDGE` Voronoi at 40–120 mm, two scales | a real crack network, not a noise level-set thresholded into a fractal web — which is what made the asphalt's first tar-snake pass look like frost |
| **efflorescence** | lime bloom out of the slab joints, the only thing brighter than the slab | stops the Beat-4 apron reading as one flat value across 116 m |

**Census, counted on every build:** `M_Surf_Asphalt` **26**, `M_Surf_Concrete` **9**,
`M_Surf_Kerb` **6**, `M_Surf_Joint` **4**, `M_Surf_GridPaint` **2** — **47 procedural
texture nodes, 1 368 shader nodes, 0 image textures.** The review's stated reason the
world reads as placeholder is 22 procedural texture nodes across six modules; this one
module now carries more than twice that, and still ships no external asset.

---
