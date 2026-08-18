# build_nearband.md — the band `wood` evacuates

`world/build_nearband.py`. A NEW vegetation tier for round 2. It does not edit
`world/build_terrain.py`; it imports it, reads the same fields, and plants where
`build_terrain`'s own gate has switched every woody tier off.

---

## 1. The defect, in one line of somebody else's code

`build_terrain.habitat()` (currently ~line 3729):

```python
wood  = smoothstep(-0.22, 0.34, fbm(x/165.0, y/165.0, 4, seed=401))
wood *= smoothstep(52.0, 150.0, D)                                   # <-- THE EMPTIER
wood *= (1.0 - 0.88*plateau) * (1.0 - 0.94*built) * (1.0 - 0.80*ez)
```

`D` is distance to the nearest centreline. So woodland probability is **exactly zero
for D <= 52 m** and 0.5 at D = 101 m. `wood` then gates five consumers — woodland
trees (`pw = h["wood"]*0.44*q`), hedgerows, shrubs (`edge`/`inner`), saplings and
ferns. Every woody thing in the world is off within 52 m of the racing line.

Measured against the live camera (`render/film17_path.json`, 2 978 frames), each
ground sample weighted by its exact screen-area-time `sum_frames (s/d)^2`:

| | share of ground screen-area-time |
|---|---|
| woodland probability EXACTLY ZERO (D <= 52 m) | **18.0 %** |
| partially gated (52 < D < 150, mean gate 0.52) | 35.7 % |
| ungated (D >= 150) | 46.3 % |
| more than 10 m from ANY woody instance | **44.9 %** |

and the inversion that makes it visible: ground at 25-50 m depth is a median
**78.9 m** from the nearest tree; ground beyond 250 m is **9.6 m**. The ground the
camera sees closest is the furthest from a tree, by 8.2x.

The client's words: *"anything 5 feet away from the main road and buildings have
blank grass no detail nothing"*, *"i want to fill the WHOLE map with trees and detail
no blank green spots period"*.

## 2. The placement field, and why it cannot make a ring

```
nb_density = (1 - smoothstep(52, 150, D))     # the EXACT complement of the wood gate
           * smoothstep(2.0, 14.0, f)          # f = metres OUTBOARD OF THE CORRIDOR RIM
           * habitat modulation
```

The D term is `1 - wood_gate(D)` and nothing else. A smoothstep plus its own
complement is identically 1, so **whatever shape the handover has, the two tiers sum
to a constant in D by construction.** There is deliberately no second distance term
anywhere in `nb_density()`: every extra D-dependent factor is another chance to put a
ring in the picture, and the whole point of a complement is that it cannot.

Everything else in the field is `f`- or terrain-driven and never `D`-driven:

```python
d *= (1 - 0.55*plateau)                            # the plateau is managed grass
d *= (1 - 0.85*ez)                                 # declared event zones stay clear
d *= (1 - 0.80*built)                              # the paddock gets AMENITY instead
d *= (0.72 + 0.55*smoothstep(0.02, 0.20, slope))   # banks hold scrub
d *= clip(0.62 + 0.52*fbm(cx/44, cy/44, 3), 0.42, 1.25)   # patchiness at 44 m
d *= clip(0.70 + 0.44*fbm(cx/11, cy/11, 2), 0.48, 1.20)   # ... and at 11 m
```

Both patchiness terms are floored at 0.42 and 0.48, so no combination of them can
open a hole the size of the defect this module exists to fix. Scrub with gaps is the
point; scrub with 200 m gaps is the defect again.

**`f`, not `D`, for every standoff rule.** `f` is metres outboard of the corridor
*rim*. The rim is 12.1 m from the centreline at s = 0 (the pit straight) and 87.9 m
at T10. "48 m from the centreline" is inside the pit lane at one and 40 m short of
the barrier at the other; `build_terrain`'s own `habitat()` docstring makes the same
point about the same trap.

## 3. The height ceiling ramps with `f`

This is a race circuit. There is a runoff programme and a debris fence outboard of
every metre of racing surface, and a tree in either is a worse defect than bare
grass. So the placeable unit's height is bounded by a monotone continuous ramp:

| `f` (m outboard of rim) | ceiling | what stands there |
|---|---|---|
| 0 - 2 | 0.00 m | nothing |
| 2 - 8 | 0.30 - 0.62 m | tussock, weed stands, low scrub |
| 8 - 20 | 0.62 - 2.50 m | gorse / bramble / juniper / broom scrub |
| 20 - 52 | 2.50 - 16.5 m | hazel scrub, saplings, short trees only |
| > 52 | 16.5 m (saturates) | the woodland tier's own D gate is ramping up |

`height_ceiling(f)` is that ramp: piecewise linear through
`F_RAMP = ((0,0), (2,0.30), (8,0.62), (20,2.50), (52,16.5))`, flat beyond, monotone
non-decreasing, and continuous to better than 0.02 m per 22.5 mm of `f`. Nothing is
emitted whose declared height exceeds it — heights are **clipped**, not rejected,
because rejecting would thin the tier exactly at the rim, which is where the defect
lives.

**Hawthorn dominance is not hand-weighted; the ramp produces it.** For the short-tree
sub-tier a target height is drawn in `[2.6, ceiling(f)]` and the species whose habit
brackets it is taken. `SPECIES` gives hawthorn 2.8-6.2 m, rowan 7.0-13.0 m, birch
8.0-16.5 m. The ceiling only reaches 7.0 m at f = 30.3 m and 8.0 m at f = 32.6 m, so
**hawthorn owns the whole f 20-30 m band on its own**, and rowan and birch appear
only where there is genuinely room for them. That is the brief's "weighted toward
hawthorn", arrived at from the geometry rather than typed into a mix vector.

`test_species_fits()` refuses a species whose *shortest* specimen does not fit the
ceiling. Scaling an oak down to 5 m is not a small oak: it is a 5 m tree carrying an
oak's 21 m branching order, and it reads as one.

## 4. The exact tests, applied to final positions

The raster is a 14 m lattice and interpolating `f` across it is worth a metre near a
tight rim, so every surviving candidate is re-tested exactly:

| test | field | what it refuses |
|---|---|---|
| `test_outside_corridor` | `build_terrain.corridor_field` (the union field) | anything inside the road programme's ground |
| `test_off_paving` | `C.platform_field` | anything on the declared z = 0.000 platform |
| `test_transit_clear` | `C.access_route_arrays` | anything inside 8.6 m of the beat-3/4 transit route |
| `test_forecourt_clear` | `C.FORECOURT_WORLD` | anything inside the showroom forecourt box |
| `test_height_ok` | `height_ceiling(f)` | anything taller than the ramp at its own `f` |
| `test_species_fits` | `SPECIES[key]["h"][0]` | a species that cannot be short enough |

`test_transit_clear` is deliberately a *second, independent* test: `corridor_field`
already contains the access ribbon, but the amenity tier plants nearer to it than
anything else in the world does, and a keep-out that exists only as a side effect of
another module's field disappears the day that field is re-scoped.

## 5. The placeable unit is a clump, not a shrub

At D 26-52 m the ground is typically seen at 100-250 m depth, so 1 px = 20-50 mm and
individual leaves are sub-pixel. This is the same argument that made R2-1661's sward
fix a *drift* and not a *clump*, and it matters because the count falls with the
**square** of the pitch: the plantable verge is 0.39 km2, and at a single-shrub pitch
that is nine figures of instance.

So the unit is a **scrub clump**, placed at a pitch of 1.45 m (N1), 2.90 m (N2) or
4.10 m (N3) and *drawn over* `1.45 x pitch` — 2.10 m, 4.21 m and 5.95 m across. That
1.45 factor is the anti-tiling law from `gen_sward`: a patch drawn at exactly the
placement pitch tiles, and a tiling ground cover along a 3 675 m verge is a picket
fence. Drawing wide and placing close makes neighbours overlap ~2.1x in area, so no
seam survives.

**Nothing new is authored.** `gen_nb_clump()` composes the shipping generators —
`gen_shrub`, `gen_weed`, `gen_grass`, `gen_tree("sapling")`, `gen_stone` — into one
mesh with `merge_parts()`, which unions the material slots by name and remaps every
polygon index. The clump's returned height is its **tallest element**, so `gn_kind`'s
normalise-and-rescale makes the target height this module passes *exactly* the height
of the tallest plant in the placed clump. That is what makes the ceiling test exact
rather than approximate.

Three things about that composition were wrong on first build and are worth recording
because the same traps are waiting for anyone extending this:

* **Parts are scaled to a target height relative to the tier's `hnom`, not to their
  own habit height.** A dock is 0.40-1.15 m and a broom 0.50-1.40 m; dropped into a
  tier whose whole ceiling is 0.62 m at their natural size, the clump's tallest
  element is whatever the dice said — and since `gn_kind` normalises by that, the
  *placed* size becomes a function of which weed was drawn.
* **One element is the leader**, drawn at 0.90-1.04 x `hnom`. Without it the clump's
  height is the maximum of a handful of independent uniforms, and a clump that drew a
  short weed and a short tussock declared 0.38 m against an `hnom` of 0.62 and was
  then scaled up 1.6x.
* **Scaling uses the MEASURED mesh extent, not the generator's declared height.**
  They differ, and not slightly: `gen_weed` returns the habit height but `_weed_head`
  then puts a flowering head on the stem (a "0.46 m" dock is 0.50 m of geometry);
  `gen_grass` returns the longest *blade length* but the blade leans (a "0.55 m"
  tussock is 0.53 m tall); and **`gen_stone` returns a mesh about 1.5 m across
  whatever size class you asked for** — its `STONES[key]["h"]` is applied downstream
  by `gn_kind`, so multiplying its own return by anything near 1.0 puts a 1.5 m
  boulder in a 0.62 m verge clump. It did. Selftest check 8b reported an N1 clump
  declaring 1.333 m against an `hnom` of 0.62, which is how all three were found.

**`shrub_lod` is the triangle dial and it is the big one.** Measured at LOD 1:
bramble 3 213 tris, hazel 4 824, juniper 12 492, gorse 13 435, broom 14 082 — a 4.4x
spread, because the `brushfine` and `scale` leaf templates are many triangles each.
At LOD 0 gorse is 25 195 and broom 30 966. The first standalone build put LOD-0
shrubs in N2 and produced 40 076-triangle clumps: a hero tree's worth of geometry for
a 2.9 m gorse bush whose leaves are sub-pixel. N1 and N2 are LOD 1 throughout; N3
takes a 25 % minority of LOD 0 because it is the closest *tall* thing to the lens.
The species weights are set with the same table in view — gorse stays as the
signature verge scrub, and the cheap species carry the bulk, which is what a real
verge looks like anyway.

`xy` widens the footprint independently of height (`gn_kind`'s own argument, and its
own argument for existing): a clump scaled down to a 0.35 m ceiling would otherwise
shrink its plan extent to 0.20 of the pitch and leave 96 % bare ground between
clumps, which is the flat wash again.

## 6. Built zones: driven *from* `built`, not suppressed by it

`(1.0 - 0.94*built)` suppresses woody cover by 94 % around the paddock and showroom —
where beats 1-4 live, and exactly what the client meant by *"...and buildings"*.

This tier does not fight that term. The scatter tiers keep `(1 - 0.80*built)` (scrub
in a paddock is wrong), and the ground it vacates is filled by **amenity planting
driven from the declared paving**:

* **clipped hedge runs** along the outlines of `C.APRON_REGIONS_CIRCUIT` (pit lane,
  garages, paddock, apron) and `C.FORECOURT_WORLD`, offset 1.2-4.1 m outboard, with
  real gaps from an fBm along the run;
* **kerbed planters** — a ring of `gen_stone("cobble")` with shrubs standing in it —
  every 17 m;
* **ornamental small trees** (hawthorn / rowan, `lean=0.30`) every 12 m.

Two things make this the right field rather than merely a smaller one. First, the
contract states the paving once, so a hedge run cannot drift away from the pavement
it edges the way `built`'s hand-drawn district drifted away from the architecture
(R2-1821 measured that drift at 47.7 % of the district being open ground). Second,
`build_terrain.cut_field` already cuts the ground mesh against `C.platform_field`, so
a plant that passes `test_off_paving` always has ground under it.

Which side of a paving edge is "outboard" is **measured, not assumed**:
`_edge_offsets()` evaluates `C.platform_field` on both sides and takes the larger.
The circuit rectangles are not all wound the same way and half of them would
otherwise have grown a hedge in the middle of the pit lane.

Hedge segments are emitted **oriented** to the run they edge, which is the only
reason `nb_gn()` exists alongside `gn_kind()`. Every scattered tier uses `gn_kind`
verbatim.

Two consequences of that orientation, both of which were defects first:

* **A hedge segment is returned at unit height and TRUE length.** `nb_gn` normalises
  every library mesh by the height it is handed, so normalising a 2.00 m segment
  *uniformly* by its own 0.85-1.45 m height would divide its **length** by the same
  number — 1.38 to 2.35 m — and a run laid at a 1.85 m pitch would then gap in some
  places and pile up in others according to how tall each segment happened to be
  drawn. The shear normalises **Z only**; length and thickness survive at the metres
  they were drawn at, and the placement scale carries height in metres directly.
* **The three amenity kinds share one line and must not share a station.** A tree and
  a planter drawn at the same `run` as a hedge segment stand *inside* it — three sets
  of geometry interpenetrating at the exact spot the beat-1-to-4 lens is pointed. The
  stations are partitioned: a tree takes its station, a planter takes its station,
  and the hedge takes what is left. A specimen tree standing in a gap in a hedge run
  is what a real forecourt looks like anyway.

Hedge heights are clipped by the same `height_ceiling(f)` as everything else. The
pit-lane paving abuts the road corridor, so a hedge run there genuinely can sit at a
small `f`, and there is no reason for the amenity tier to be exempt from the rule
that governs the open band.

## 7. The mechanism is shadow, not geometry

The sun sits at `C.SUN_ELEV_DEG = 12.47 deg`, so `cot(elev) = 4.52`: a 1.0 m scrub
lays 4.52 m of shadow across the ground. In R2-1661 35 % plan cover read as 72 %
screen cover for exactly this reason.

`shadow_cover()` measures it geometrically rather than hoping: over a 180 x 180 m
patch of real near band at 0.25 m cells, every instance is stamped as its plan
footprint and then as that footprint swept along the sun's ground bearing by
`h/tan(elev)`; the union is the cover.

## 8. Instance diversity — the strong path, on purpose

`tools/item_gate.py` (~line 2986) only demands `distinct_topologies >= 2` on the
**plain-object** path, and that weak path is exactly how "one tree spammed a hundred
times" would pass. Everything this module emits is a geometry-nodes instance the
depsgraph can walk, so it lands on the strong path:

```python
need_sources = max(8, min(40, int(math.sqrt(real["realized"]))))
var_ok = (distinct_sources >= need_sources and distinct_shapes >= need_sources
          and top_source_share <= 0.25 and top_shape_share <= 0.25)
```

`library_diversity()` applies that same rule to every emission and reports it.
`build_terrain` ships 8 / 12 / 16 unique meshes per species at L0 / L1 / L2 — the
first clears the `>= 8` floor with no headroom at all and the other two fall short
once the near band's own instances are added to the count — so
`_short_tree_library()` tops each `(species, LOD)` group up to `NB_TREE_LIB_TARGET`
(22) with meshes generated here from the same `gen_tree`, seeded independently.

**`library_diversity()` is my own bookkeeping, and bookkeeping is not evidence.** It
is cross-checked against `tools/instance_variety.py` run on the saved `.blend`, which
walks `depsgraph.object_instances` and skips anything where `not is_instance`. That
tool's own docstring records the reason this matters: fed 2 000 plain-object copies
of one mesh it reports `TOTAL 0 realized instances` and a verdict of `VACUOUS`. A
plain-object tier is invisible to it *entirely* — so a plain-object near band would
have produced a clean report from an instrument that never saw the geometry, which is
indistinguishable from a pass. A zero realized count is a FAILED build here, not a
quiet one.

One caveat on reading that tool's output: it families by `key.split("_")[0]` on the
emitter's name, and everything this module emits is `VEG_nb_*` — it has to be,
because `build_terrain.purge()` only reaps the `TER_` and `VEG_` prefixes and a
distinct token would break idempotency. So the near band appears *inside* the `VEG`
family rather than as its own row. The per-emission table from `library_diversity()`
is the finer-grained view; the tool's realized total is the proof the depsgraph sees
it at all.

## 9. The one shader this module authors

A sheared hedge face is not a shrub's silhouette: it is a plane of cut twig ends, and
at a 12.47 deg sun that plane is the brightest thing in the paddock unless it carries
relief. `mat_nb_clipped()` is the only material added, and **both of its numbers come
from `itemkit` rather than from a keyboard**:

```python
detail = K.detail_for(0.045, distance_m=26.0, lens_mm=35.0)
amp_mm = K.relief_amplitude_for(0.26, wavelength_m=0.045)
```

The `Normal` socket is fed **by name** — Blender 5.2 moved
`Principled BSDF.Normal` from socket index 5 to 6.

The selftest carries a negative control on this too: the house default `detail=8` at
the same wavelength emits octaves below the resolvable floor and is shown to be
refused by `K.finest_octave_for`.

## 10. Deviations from the brief, and the reasons

**The near-band tier is gated in `D` only and shaped in `f` only.** The brief's
tier table ends with "`f` > 52 m: hand back to the existing woodland tier". Taken as
a *cut* in `f` that would reintroduce exactly the artefact the module exists to
remove, because **the woodland gate is on `D`, not on `f`**, and the two are not the
same variable: `f = D - rim`, and the rim runs 12.1 m to 87.9 m round the lap. A cut
at f = 52 m therefore lands at D = 64 m on the inside of T4 and at D = 140 m at T10 —
the first of those is a hole cut in the middle of the band this tier is here to fill,
laid as a line parallel to the track down the whole lap.

So the handover is done the way it is safe to do it: the **D-complement** closes the
tier down as the woodland gate opens up (they sum to a constant), and `f` only ever
sets the *ceiling* and the *species*, which saturate at f = 52 m. The result is that
outboard of f = 52 m the near band is emitting the same short-tree/hazel mix the
woodland edge emits, at a density that is falling exactly as fast as woodland's is
rising. That is the no-cliff property, and section 11 measures it.

**Everything else follows the brief as written.**

## 11. The no-cliff evidence — MEASURED, not asserted

`density_vs_D()` does not model either tier. It walks **every woody instance actually
in the built scene** — plain objects by `object.location`, geometry-nodes tiers by
their point clouds — projects each to `D = |u|` with `C.project`, and bins it in 10 m
bins across 0-300 m against Monte-Carlo annulus areas of *plantable* ground (outside
the corridor, off the declared paving).

**Instance counts alone cannot carry this verdict**, and the first build proved it:
they treat a three-stem gorse clump and a 21 m oak as one unit each, which is not
remotely the same amount of "not a blank green spot". So the table prints counts
(what was actually placed — those cannot be argued with) *and* woody plan cover, and
the verdict is taken on cover.

Cover uses the random-disc law, `1 - exp(-lambda a)`, not naive area/area: summed
footprint over ground area exceeds 1 as soon as crowns overlap, and a woodland at 150
trees/ha of 4.5 m crown sums to 0.95 while a closed wood is nearer 0.80 of real
cover. The footprint radii are DECLARED (`FOOT_R`), not measured off 5.3 M realized
instances — a clump's is its `pitch * 0.42`, a woodland tree's is 0.32 x the mean
habit height of `MIX_BASE`. So cover here is a model with stated inputs;
`shadow_cover()` is the direct raster measurement that backs it.

### The measured table

`--full` build, open country (`built < 0.30`), measured against
`build_terrain.py` md5 **`01c5c684d65b3c47610562747f5897fa`** (recorded in
`work/nearband/terrain_fingerprint.txt`; an earlier build of this tier measured a
terrain that had changed 14 minutes later, which is exactly the staleness
`assemble.py`'s content-fingerprinting exists to catch, so the fingerprint is part of
the evidence now).

| D (m) | area ha | woodland/ha | nearband/ha | total/ha | cover BEFORE | cover AFTER |
|---|---|---|---|---|---|---|
| 20-30 | 0.29 | 0.00 | 10.3 | 10.3 | 0.000 | 0.001 |
| 30-40 | 2.90 | 0.69 | 12.1 | 12.8 | 0.000 | 0.004 |
| 40-50 | 4.38 | 10.3 | 319.4 | 329.7 | 0.001 | 0.084 |
| 50-60 | 4.71 | 15.3 | 569.7 | 585.0 | 0.002 | 0.232 |
| 60-70 | 4.87 | 22.6 | 289.9 | 312.4 | 0.024 | 0.201 |
| 70-80 | 5.06 | 35.2 | 215.9 | 251.1 | 0.042 | 0.194 |
| 80-90 | 5.55 | 53.0 | 169.0 | 221.9 | 0.072 | 0.194 |
| 90-100 | 6.01 | 68.0 | 137.4 | 205.4 | 0.070 | 0.165 |
| 100-110 | 6.12 | 89.6 | 101.2 | 190.8 | 0.119 | 0.190 |
| 110-120 | 5.99 | 117.1 | 58.5 | 175.6 | 0.132 | 0.178 |
| 120-130 | 6.04 | 129.9 | 35.8 | 165.6 | 0.162 | 0.189 |
| 130-140 | 6.06 | 137.1 | 13.9 | 151.0 | 0.175 | 0.186 |
| 140-150 | 6.40 | 140.9 | 1.7 | 142.6 | 0.172 | 0.173 |
| 150-160 | 6.33 | 145.9 | 0.00 | 145.9 | 0.175 | 0.175 |
| 160-300 | ~6.2 ea | 140-246 | 0.00 | 140-246 | 0.169-0.246 | 0.169-0.246 |

Read the two right-hand columns down and the whole argument is there.

**BEFORE**, woody cover ramps 0.000 → 0.175 over 150 metres, and the first eleven
bins are effectively zero. That is the defect, drawn.

**AFTER**, from 50 m outward the total is 0.232, 0.201, 0.194, 0.194, 0.165, 0.190,
0.178, 0.189, 0.186, 0.173, 0.175 — **flat, against a far field of 0.170**. The
handover from near band to woodland happens across 100 m of D with no step in the
total: as `nearband/ha` falls 570 → 0, `woodland/ha` rises 15 → 146, and the sum does
not move. That is the complement doing exactly what it was chosen to do.

### The headline numbers

| | before | after |
|---|---|---|
| mean woody cover, D 0-52 m | **0.0008** | **0.1065** (133x) |
| bins under D 160 m with zero cover | **3** | **0** |
| cover step at the 150 m gate edge | 0.0157 | **0.0080** |
| cover step at the 52 m gate edge | 0.392 | 0.932 (see below) |
| max cover step, D 20-200 m | 1.769 (at 60 m) | 1.839 (at 40 m) |

### The two honest failures

**The residual step at 40-52 m is real, my own gate reports `ok=0` for it, and I
tried to fix it and failed.** Cover goes 0.084 at 40-50 m to 0.232 at 50-60 m. I have
not hidden it and I have not relaxed the threshold to make it go away. What is known:

* It is **not** a step in `D` that this tier introduced. `max_step_20_200m` was
  **1.769 before** (at 60 m) and **1.839 after** (at 40 m) — the same magnitude,
  moved one bin. The pre-existing step is the woodland gate's own foot.
* It is the **outboard ramp `smoothstep(2, 14, f)` turning on**, which the brief
  specifies and which is the debris-fence standoff. Open ground at D < 50 m only
  exists where the corridor rim is narrow (12.1 m on the pit straight against 87.9 m
  at T10), so on that ground `f = D - rim` is 8-38 m and the ramp is still climbing.
* **It is therefore not a circle in the picture.** It tracks `f`, and `f` is a fence
  line that varies 12-88 m from the centreline round the lap. A D-histogram is the
  right instrument for the woodland gate (which is genuinely in `D`) and the wrong
  one for this term.
* **THE ATTEMPTED FIX, AND ITS MEASURED RESULT.** Cover arithmetic says the only
  levers are `dens` (already ~1.0) and *which tier owns the ground*: for a clump
  drawn at 1.45 x its own pitch, cover is `0.554 * dens` **independent of pitch**, and
  N1's plan radius is 0.61 m against N2's 1.22 m. So the second build moved the N1/N2
  crossfade inboard from 6-11 m to 5-9 m and raised `dens` to 1.00 / 0.98, to put the
  bigger footprint on the inner ground. **It did not work.** The 40-50 m bin went
  0.073 → 0.084 and the 50-60 m bin went 0.198 → 0.232, so the *relative* step barely
  moved (0.921 → 0.932): shifting the crossfade fed both bins, because the inner bin's
  ground is a minority of the `f` distribution in both. Mean cover 0-52 m did improve,
  0.0912 → 0.1065. The conclusion I draw is that **this step cannot be moved without
  either weakening the outboard ramp the brief specifies, or putting scrub in the
  runoff** — and I am not doing either on my own authority.

**Nobody has looked at it at 4K.** No frame has been rendered of this tier: no
witness, no f2760 A/B, nothing. The metric argues; on this project the rendered frame
decides. Until that A/B exists, "the residual step reads as the runoff edge" is an
argument and not a finding, and this section should be read as an unclosed item.

### The built district, reported separately and NOT resolved here

| | woodland/ha | nearband/ha | area |
|---|---|---|---|
| built district (`built >= 0.30`) | 1.8 | 44.9 | 13.3 ha |

That is a **25x ratio**, and it is a deliberate disagreement with a live decision in
another module rather than an ordering accident — see §15.

## 12. What it costs

Standalone `--full` build on this box (11 GB, GTX 1070, three other Blenders
competing for RAM):

| | terrain | + near band |
|---|---|---|
| build time | 929.7 s | **+198.3 s** |
| base library triangles | 33 493 647 | **+19 971 231 (+60 %)** |
| evaluated triangles | 16 158 549 193 | **+233 842 416 (+1.45 %)** |
| objects | 28 019 | +14 emitters |
| unique meshes | 1 432 | +~230 |
| instances | | **10 267 (36 583 woody stems)** |

**234 M instanced triangles is 1.45 % of the terrain budget** — for the 18.0 % of
ground screen-area-time that had no woody cover available to it at any density. That
is the number that matters and it is cheap.

**The base library is the expensive half, at +60 %.** It is resident memory, once,
shared by every instance — but it is real, and the dial is
`NB_TREE_LIB_TARGET` (22): topping the short-tree library up to 22 unique meshes per
`(species, LOD)` is roughly half of that 20 M, because a hero birch is 269 098
polygons. Dropping it to 16 would save ~4 M and still clear the item gate for the
instance counts this tier actually places (354 short trees split across 9
species/LOD groups, so `max(8, sqrt(n))` is 8-12 per group, not 40).

Where the instanced triangles go (first build's per-tier split; the second differs
only in the N1/N2 balance):

| tier | instances | tris each | share |
|---|---|---|---|
| N1 verge tussock | ~2 100 clumps | 5 552 | 5 % |
| N2 scrub | ~3 450 clumps | 15 286 | 24 % |
| N3 hazel thicket | ~3 800 clumps | 18 434 | 33 % |
| short trees (hawthorn/rowan/birch) | 354 | ~169 000 | 28 % |
| amenity (hedge / planter / ornamental) | ~445 | 27 177 / 40 747 | 10 % |

### Shadow — the measured amplification

`shadow_cover()` over a 180 x 180 m patch of real near band at 0.25 m cells, sun at
`C.SUN_ELEV_DEG` = 12.47 deg (`cot` = 4.522), 859 instances:

| | |
|---|---|
| plan cover | **0.0889** |
| plan + shadow cover | **0.3318** |
| amplification | **3.733x** |

8.9 % of ground covered by geometry does 33.2 % of the work, for no extra triangles.
That is the whole argument for spending the budget on low scrub at a grazing sun
rather than on taller geometry: R2-1661 measured 35 % plan reading as 72 % screen for
the same reason, and this is the same lever at a smaller scale.

### Instance diversity — verified with the external guard, not with my own bookkeeping

`tools/instance_variety.py` on the saved `world/nearband.blend`:

```
TOTAL 4,902,372 realized instances

family       instances  sources  inst/src  top share    gini   verdict
VEG          4,902,372      823     5,957       2.0%   0.867   concentrated

>> no family leans on one source mesh past 40 %
>> STAGE RESULT: INSTANCE_VARIETY_CLEAN
```

**A non-zero realized count is the point.** That tool iterates
`depsgraph.object_instances` and skips anything where `not is_instance`, so a
plain-object tier reports `TOTAL 0` and `VACUOUS` — a clean report from an instrument
that never saw the geometry. This tier is visible to it. Its own per-emission check
(`library_diversity()`, 12 emissions, all passing `distinct_sources >= max(8,
min(40, sqrt(realized)))` and `top_source_share <= 0.25`) is the finer-grained view.

## 13. Running it

```
B=/opt/blender-5.2.0-linux-x64/blender

# instrument check only -- 4 s, no ground, no library
$B -b --factory-startup -noaudio -P build_nearband.py -- --selftest

# terrain + near band, standalone, with the full evidence
$B -b --factory-startup -noaudio -P build_nearband.py -- --full --selftest \
   --save world/nearband.blend --stats work/nearband/stats.json

# fast iteration: ground + library + this tier, no grass, no sward, no grit
TERRAIN_FAST=1 $B -b --factory-startup -noaudio -P build_nearband.py -- \
   --terrain-only --quality 0.25
```

`--full` runs `build_terrain.build()` first and captures its `Ground`, `GridZ`,
`CameraPath`, `Raster` and library through `capture_terrain` — a context manager that
wraps five module attributes for the duration of the call and puts them back. This
module does not edit `build_terrain.py` and does not need to: Python resolves module
globals at call time. It matters that these are **the same objects**: a second
`GridZ` sampled off `Ground.height` on a coarser grid is a different height field,
and plants placed against it would sit at a different z from the woodland they are
meant to blend into.

**Blender exits 0 on an uncaught exception.** Judge only on the printed
`>> STAGE RESULT:` lines; every one of them carries `ok=1` or `ok=0`.

## 14. Selftest and its negative controls

A check that has never been shown to fail is not a check. The commonest defect across
840 log entries on this project is a broken instrument, not a bad render. So every
gate is exercised twice — once on input it must accept, once on input it must refuse
— and the refusals are reported by name in the `fired` list of the stage line.

`--selftest`: **62 checks, 62 passed, 16 negative controls fired.** Runs in ~4 s (no
ground mesh, no library). The controls, and what each one refuses:

| control | refuses |
|---|---|
| `gate_detector_rejects_a_wrong_gate_edge` | the "wood is exactly zero inside the gate" instrument, asserted at D <= 80 m instead of 52 m — if it passed for both it would be measuring nothing |
| `scrub_above_ceiling_refused` | a 2.40 m scrub at `f` = 5.0 m (ceiling 0.410 m) |
| `scrub_above_ceiling_refused_at_tier2_floor` | a 2.50 m gorse at `f` = 8.0 m (ceiling 0.620 m) |
| `tall_species_refused_in_the_band` | oak (h_min 12.0 m) at `f` = 25 m, ceiling 4.99 m |
| `poplar_refused_at_f40` | poplar (h_min 16.0 m) at `f` = 40 m |
| `hawthorn_refused_at_f21` | hawthorn (h_min 2.8 m) at `f` = 20.5 m — even the shortest tree species is refused where the ramp has not opened |
| `centreline_candidates_refused` | 400 candidates placed ON the racing line |
| `inside_rim_candidates_refused` | 40 candidates 1.0 m inside the left corridor rim |
| `candidate_on_the_forecourt_refused` | the middle of the declared showroom forecourt |
| `candidate_on_the_transit_route_refused` | a point ON the beat-3/4 route centreline |
| `candidate_inside_the_transit_clearance_refused` | 6.6 m off that route, inside the 8.6 m clearance |
| `candidate_inside_the_forecourt_box_refused` | inside `FORECOURT_WORLD` + clearance |
| `nearband_refuses_the_far_field` | density at D = 300 m must be **exactly** 0 |
| `nearband_refuses_the_rim` | density at `f` = 1.0 m must be **exactly** 0 |
| `one_mesh_spammed_refused` | a 5 000-instance emission from 1 source mesh |
| `house_default_detail_8_would_be_refused` | `detail=8` at lam 45 mm — below the resolvable floor, 2 wasted octaves |

The negative control on the corridor test caught a defect **in the control itself**:
the rim was first taken from `corridor_fz`'s `lim`, but at `u = 0` the sign of `u` is
a coin flip, so `lim` returned the RIGHT rim (up to 87.9 m at T10) for a point being
offset to the LEFT — landing 76 m outside the corridor and passing for the wrong
reason. It now takes `C.platform_edge(s, +1)` directly.

Check 8b (the clump declares the height it says it does) failed on its first run and
on its second, and found three separate real defects — see §5. That is the check
earning its place: none of the others could have seen any of them, because the
ceiling was never violated.

## 15. THE OPEN QUESTION — not mine to rule on

R2-1821 replaced the hand-drawn `built` district with the contract's `paved` field for
the three ground-cover tiers, but **deliberately kept `built` as the tree keep-out**
(`build_terrain.py`, in `habitat()`): *"Trees, shrubs, ferns, weeds, grit and the
park species mix still read `built`, because a tree keep-out around a paddock
genuinely IS a district."*

This module plants **44.9 instances/ha inside that district against woodland's 1.8/ha
— a 25x ratio** over 13.3 ha. It is amenity planting, not woodland: clipped hedge
runs, kerbed planters and ornamental standards, all `< 1.45 m` except the ornamentals,
all driven from the declared paving edge, all outside the corridor, the transit route
and the forecourt box. The design intent is that this is the *right* thing to put in a
paddock and is not what the keep-out was written to exclude.

**But that is a direct disagreement with a live decision in a file I must not edit,
and the author of that decision is mid-pass in it.** It is stated here with the
numbers attached, and it is theirs to rule on. If the ruling is that the keep-out
covers amenity planting too, the change is one line — drop `build_amenity()` from
`build()` — and the open-country evidence in §11 is unaffected, because it is
computed over `built < 0.30` precisely so that this question cannot contaminate it.
