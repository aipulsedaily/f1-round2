# SCALE.md — how big this film actually is, measured

*Written 2026-08-18. Supersedes every triangle count published about this project
before that date. Seven of them were wrong; §12 lists all seven and what each one
actually was.*

**The one-line answer.** The film evaluates **17,707,774,735 triangles for every
one of its 2,978 frames** — 17.7 billion, one 4K frame, every instance realised.
Across the whole film that is **52,733,753,160,830** triangle-evaluations, 52.7
trillion. The geometry resident in the file is **138,073,595** unique triangles.
The website that shows the film draws **55,242,834** per frame — a different
scene, 320× smaller, and **not** this project's polygon count.

Every figure below carries three things and is not publishable without them:

* **what it counts** — one of the four definitions in §1;
* **how it was got** — `MEASURED` (an instrument was run and its output
  recorded), `DERIVED` (arithmetic over figures that are themselves measured),
  or `COMPUTED` (a generator's own self-accounting estimate, which is *not* a
  measurement of realised geometry);
* **where it came from** — a file and, where the file is long, a line.

That rule exists because this document is a correction. The retired figures had
none of the three, and it took a client asking *"so only 20m polys? i thought it
was 20 billion polys?"* to find out.

---

## 1. Four different numbers, and why conflating them broke everything

There is no such thing as "the polygon count". There are four quantities, they
differ by more than two orders of magnitude, and **every geometry error this
document corrects was one of them being quoted as another.**

| | definition | this film |
|---|---|---:|
| **(a) UNIQUE / LIBRARY** | geometry resident once in memory. Each mesh datablock counted a single time. No modifiers applied, no instances expanded. | **138,073,595** |
| **(b) EVALUATED PER FRAME** | every instance expanded and every modifier applied — what Cycles builds its BVH over for **one** frame. Whole scene; **not** view-frustum culled. | **17,707,774,735** |
| **(c) TOTAL ACROSS THE FILM** | (b) × 2,978 frames. A cumulative *work* figure, **not** a scene size. | **52,733,753,160,830** |
| **(d) WHAT THE BROWSER DRAWS** | the web build — a separate, purpose-built scene that is not a decimation of the film. Listed here only so nobody quotes it as (b). | **55,242,834** |

Say them out loud with their units attached and they stop being confusable:

* (a) *"138 million unique triangles of library geometry."*
* (b) *"17.7 billion triangles evaluated per frame."*
* (c) *"52.7 trillion triangle-evaluations to produce the film."*
* (d) *"55.2 million triangles drawn per frame in the browser."*

(b) ÷ (a) = **128×**. That ratio is the entire argument of the build: 138 M
triangles resident once become 17.7 G on screen because 4,966,913 instances draw
from only 1,569 distinct source meshes. It is also why the render fits in **5.5 GB
of VRAM**.

(b) ÷ (d) = **320.5×**. That is the factor by which the retired headline figure
under-stated the film.

---

## 2. The headline figures

| figure | value | def | class | source |
|---|---:|---|---|---|
| evaluated triangles per frame | **17,707,774,735** | (b) | DERIVED from two MEASURED parts | world census 17,691,299,239 + film-only additions 16,475,496 — §3, §4 |
| evaluated triangles, whole film | **52,733,753,160,830** | (c) | DERIVED | 17,707,774,735 × 2,978, exact integer arithmetic |
| unique library triangles | **138,073,595** | (a) | DERIVED from MEASURED parts | §5 |
| realized instances per frame | **4,966,913** | (b) | MEASURED | `docs/DEFECT-LOG-R2.md:56798`; `tools/poly_census.py`, `tools/instance_variety.py` |
| distinct source meshes behind them | **1,569** | — | MEASURED | `docs/DEFECT-LOG-R2.md:56799` |
| the car, evaluated | **10,875,060** | (b) | MEASURED | §6 |
| scene objects in the delivered blend | **46,267** | — | MEASURED | `work/r23661/measured_film25_breach.json`, `n_objects` |
| image texture files in the delivered film | **0** | — | MEASURED | `work/r23661/build_film25.log:84` |

**What the delivered artefact is**, because the retired figures described a world
that never shipped:

| | |
|---|---|
| film blend | `render/film25_breach.blend`, 10,956,580,171 bytes (gitignored) |
| its world | **`assembly15.blend`**, not `assembly14`. `work/r23661/build_film25.log:3` records the deliberate override in full. `render/world/assembly/r2/SHIPPING.md` still names `assembly14` and was knowingly left unrewritten — it was under another agent's lease at the time. |
| frames | 2,978 at 24 fps, 3840×2160 |
| the car | `world/R2_3361_car_anim_driver_CS.blend`, **appended** — not linked (`build_film25.log:5`) |

---

## 3. The world, fully measured — the four layers

These four numbers are a **single `tools/poly_census.py` run on the shipped
world**, with no arithmetic on top. They are the most solid geometry figures in
this repository.

| layer | triangles | across | source |
|---|---:|---|---|
| **BASE** | **123,422,404** | 3,445 mesh datablocks | `docs/DEFECT-LOG-R2.md:56797` |
| **EVALUATED** | **1,256,842,384** | 30,204 mesh objects | `docs/DEFECT-LOG-R2.md:56796` |
| **INSTANCES** | **16,434,456,855** | 4,966,913 realized instances from 1,569 distinct sources | `docs/DEFECT-LOG-R2.md:56795`, `:56798-56799` |
| **RENDERED** | **17,691,299,239** | = EVALUATED + INSTANCES | `docs/DEFECT-LOG-R2.md:56794` |

All four also appear at `docs/STAGING-R2-3601-to-R2-3660.md:371-377`, in the
`assembly14` / `assembly15` comparison table they were produced for.

**The identity closes to the unit.** 1,256,842,384 + 16,434,456,855 =
17,691,299,239, exactly. It closes on the `assembly14` column of the same table
too: 1,256,842,384 + 13,842,597,953 = 15,099,440,337. That is a real check on the
instrument, not a restatement.

### Which `assembly15`

There are **two** `assembly15` censuses in this repository's records and only one
is the shipped world.

| | RENDERED | BASE | EVALUATED | meshes |
|---|---:|---:|---:|---:|
| first build — **DEFECTIVE** | 17,687,002,947 | 119,126,112 | 1,252,546,092 | 3,198 |
| rebuild — **SHIPPED** | **17,691,299,239** | **123,422,404** | **1,256,842,384** | **3,445** |
| delta | 4,296,292 | 4,296,292 | 4,296,292 | 247 |

The first build was missing all 247 `build_dressing` objects (`R2-3546`;
`docs/STAGING-R2-3541-to-R2-3600.md:289-296` carries its own footnote saying so).
The delta is **exactly** `build_dressing`'s independently measured triangle count
— `assembly15_build.json mods.dressing.summary.triangles` = 4,296,292 over 247
objects — on three census layers at once, with zero error. `R2-3605`
(`docs/DEFECT-LOG-R2.md:56720`) is the rebuild. **Quote 17,691,299,239. If you
see 17,687,002,947 anywhere, it is the defective build.**

---

## 4. What the film adds to the world

`film25_breach.blend` is `assembly15` plus these. All MEASURED; all definition (b).

| collection | triangles | objects | source |
|---|---:|---:|---|
| `CAR` (car + driver) | **10,875,060** | 626 | census on `world/R2_3361_car_anim_driver_CS.blend` — §6 |
| `BREACH` | **4,958,736** | 15,091 | `work/r23661/breach25.log:21` |
| `PROPS` | 466,264 | 189 | same census run, `by_collection.PROPS` |
| `R2_SHOWROOM_CEILING` | 147,992 | 21 | census; corroborated by `build_film25.log:11` recording 73,996 quads |
| `SHOWROOM` | 22,492 | 76 | census, `by_collection.SHOWROOM` |
| `LIGHTS` | 4,928 | 38 | census, `by_collection.LIGHTS` (mesh emitters) |
| `WORLD_SKY` | 24 | 3 | `work/r23661/build_film25.log:80` |
| **total** | **16,475,496** | | |

The breach is the shattered east glass wall: **3,796 shards, 11,246 fines puffs
at 4,679,872 triangles, and 39 frame pieces** (`breach25.log:19-21`). It was
missing from every previously published film total, as was the car, as was the
sky.

`build_film25.log:85` records the film scene as `assembly15.blend` **+978
objects** → 32,046 total; the breach then adds 15,091, giving the 46,267 in the
delivered blend.

---

## 5. Unique / library geometry — definition (a)

| | triangles | meshes | source |
|---|---:|---:|---|
| `assembly15` world | 123,422,404 | 3,445 | poly_census BASE, `DEFECT-LOG-R2.md:56797` |
| car blend | 9,544,439 | 885 | census on `world/R2_3361_car_anim_driver_CS.blend` |
| showroom ceiling library | 147,992 | 21 | ceiling census |
| breach | 4,958,736 | | `work/r23661/breach25.log:21` |
| sky | 24 | | `work/r23661/build_film25.log:80` |
| **sum** | **138,073,595** | | **DERIVED** |

**This is an upper bound, and deliberately so.** Appending merges datablocks, so
the delivered blend's own BASE is at or just below this. It cannot be measured
exactly without opening a 10.96 GB file — see §11.

---

## 6. The car

**10,875,060 evaluated triangles across 626 objects.** MEASURED, by a
per-collection census of `world/R2_3361_car_anim_driver_CS.blend` — the exact
blend the film appends, named at `work/r23661/build_film25.log:5`.

That is **0.06 % of a frame.** Which is the honest answer to *"how big is the car
against the world"*, and is not a reason to leave it out — it was left out of
every previous film total, and that was one of the five faults in the retired
per-frame figure.

| | |
|---|---|
| decomposition | round-1 car **9,629,183** over 616 meshes (`tools/inventory.py`, `docs/inventory_iter.json`; quoted at `docs/DEFECT-LOG-R2.md:5843`) + driver **1,245,877** by subtraction |
| driver cross-check | the driver's own build record: built at 1,621,350 triangles, trimmed by 189,780 of 817,272 faces, predicting ~1,244,850 — agreeing to **0.08 %** |
| largest single module | **`MB_` monocoque, 1,844,927 triangles over 17 parts** — 1.8× the next largest (`docs/beat_sheet.md:34`, `docs/explode_plan.json:780`) |
| one front corner | **673,832** — wheel 257,640 + brake 182,336 + suspension 233,856 |

---

## 7. Per-module breakdown of the world

Read the `class` column before quoting any row. **Two of these are COMPUTED** —
the generator's own estimate rather than a census — and they are the two largest.
§8 is about exactly that.

| module | triangles/frame | objects | class | source |
|---|---:|---:|---|---|
| `build_terrain` | 19,279,121,746 | 28,019 | **COMPUTED** | `assembly15_build.json mods.terrain.summary.evaluated_tris`; of which `instanced_tris` 18,087,554,991; library 33,623,237 over 1,432 unique meshes |
| `build_items` | 42,467,316 | 1,706 | MEASURED | `mods.items.summary.triangles` |
| `build_nearband` | 237,226,561 | 10,267 instances | **COMPUTED** | `mods.nearband.summary.nb_instanced_tris`; library 20,021,074 over 312 meshes |
| `build_barriers` | 11,562,480 | 131 | MEASURED | `mods.barriers.summary.tris` |
| `build_dressing` | 4,296,292 | 247 | MEASURED | `mods.dressing.summary.triangles` |
| `build_surface` | 2,721,433 | 58 | MEASURED | `mods.surface.summary.triangles`; 35 serrated kerbs are 1,609,580 of it |
| `build_architecture` | 2,502,344 | 31 | MEASURED | `mods.architecture.summary.base_tris` |
| `build_sky` | 24 | 3 | MEASURED | `work/r23661/build_film25.log:80` |

All `assembly15_build.json` paths are relative to `render/world/assembly/r2/`.

Three notes that are the whole reason this table exists:

* **`build_items` was missing from every published total.** At 42,467,316 it is
  the second-largest non-vegetation module in the world: 900 spectators
  31,142,407 + 120 crew 5,958,729 + 10 timing stands 3,073,024 + 676 catch-fence
  posts 2,293,156. It uses **no instancing at all** — `instancers: 0`,
  `shared_meshes: 0`, 1,706 objects over 1,706 distinct meshes.
* **`build_barriers` replaces a sourceless number.** 11,760,000 was published; it
  is a round number with no source anywhere in this repository. The shipped value
  is 11,562,480. This module also states it uses object instancing zero times —
  no master panel, post, block, tyre or pebble.
* **`build_dressing` is the module that adjudicated §8.** It is the one generator
  that does a real per-object triangle walk instead of estimating, and it agrees
  with the census to the unit.

`assembly15_build.json total_objects` = 31,068. The module rows above sum to
**30,195**, leaving **873 objects unattributed to any module summary** — the
nearband's 14 emitters account for a few of them and the rest are not run down
here. Flagged rather than tidied: it does not move any triangle figure (the
census counts objects, not module rows) but it is an open minor item.

### Vegetation populations

MEASURED by the generators' own placement counters,
`assembly15_build.json mods.terrain.summary`:

| | count | | count |
|---|---:|---|---:|
| grass clumps | 2,975,018 | shrubs | 38,847 |
| — of them at hero LOD *(a subset, do not add)* | 1,821,790 | weeds | 35,486 |
| grit pieces | 1,616,541 | woodland trees | 24,646 |
| sward drifts | 266,525 | ferns | 7,211 |
| — sward A / B / C | 116,924 / 93,538 / 56,063 | saplings | 5,500 |
| gravel spray, cobble, boulder | 125 / 219 / 45 | hedgerow trees | 3,299 |
| | | avenue trees | 24 |

The census counts **4,966,913 realized instances**. The generators' placement
counters sum to approximately the same — the reconciliation pass records
4,955,784, agreeing to 0.224 %. **Not fully reproduced here:** summing the fields
above (excluding hero clumps as a subset) gives 4,973,097, which is 17,313 above
the recorded 4,955,784. The three instruments agree to within a quarter of a
percent, which is the claim worth making; the exact field set behind 4,955,784 is
an open minor item and is left visible rather than tidied.

---

## 8. The census and the generators disagree by 10.7 %, and it is not closed

**This section exists so that the disagreement cannot be quietly averaged away by
whoever reads next.**

Two instruments measured the same world.

| | instanced triangles/frame | full frame incl. film additions |
|---|---:|---:|
| `tools/poly_census.py` — walks the depsgraph, per realized instance | **16,434,456,855** | **17,707,774,735** |
| the generators' own build summaries | 18,324,781,552 | 19,596,373,668 |
| gap | +1,890,324,697 (**+11.50 %**) | +1,888,598,933 (**+10.67 %** of the census) |

The generator frame figure is terrain 19,279,121,746 + nearband 237,226,561 +
items 42,467,316 + barriers 11,562,480 + dressing 4,296,292 + surface 2,721,433 +
architecture 2,502,344 = 19,579,898,172, plus the 16,475,496 of film-only
additions from §4.

**Where they agree, they agree very closely**, and this is what localises the
fault:

| | census | generators | agreement |
|---|---:|---:|---|
| the non-instanced, object-level layer | 1,256,842,384 | 1,255,116,620 | **−0.137 %** |
| instance **counts** | 4,966,913 | 4,955,784 | **−0.224 %** |
| triangles **per instance** | 3,308.8 | 3,697.7 | **+11.75 %** |

So the entire gap is triangles-per-instance. Nothing else moves.

*(The per-instance gap is +11.75 %, not the +11.50 % of the total: instance
counts differ by −0.224 % as well, and the two compose. The reconciliation record
quotes +11.50 % on this row; recomputed here, 3,697.7 / 3,308.8 = 1.1175. It
changes nothing about the argument and is corrected rather than carried.)*

### The suspect that was named, and what happened to it

**Named suspect:** `tools/poly_census.py:64`. In the instance loop the tool does
`ob = inst.object` and then `ob.to_mesh()` — apparently on an *unevaluated*
object, which would drop modifiers on instance sources and make the census a
**floor**, i.e. the truth would be higher than 16,434,456,855, not lower.

**Status: REFUTED by direct experiment, 2026-08-18.** A probe built a scene whose
instance source carries a SUBSURF modifier and is instanced by Geometry Nodes,
then ran that exact loop over it. The loop reported **192 triangles per instance**
— a cube is 12 base triangles, and subsurf level 2 is 96 quads = 192 triangles.
It reported the **modified** count. `bpy`'s `DepsgraphObjectInstance.object` is
already the evaluated object, so `ob.to_mesh()` on it returns post-modifier
geometry. The census does not drop modifiers, and it is **not** a floor.

*(The probe is `build/truenumbers/census_instancing_probe.py` in the companion
website repository, where the reconciliation pass was run; its full adjudication
is `build/truenumbers/RECONCILIATION.json`, entries D1, D2 and E1-E5. It is
recorded here because the finding is about this repository's instrument.)*

### Where the evidence points

* **The generators do not count instanced geometry — they estimate it.** They
  multiply a placement count by the triangle count of **one representative
  library mesh**. `world/build_terrain.py:4472` does
  `inst_tris += len(PF) * _mesh_tris(lib[("fern", 0)][0][0])` — variant `[0][0]`
  standing in for the whole fern library; `world/build_terrain.py:2988` takes the
  mean of **one** kind and applies it to all kinds. That is class COMPUTED by
  construction, and it is biased **upward** whenever the representative variant
  is heavier than the mean of what was actually placed.
* **Where a generator really counts, the two agree exactly.** `build_dressing`
  does a per-object walk. Its 4,296,292 matches the census delta of §3 on BASE,
  EVALUATED and RENDERED simultaneously, with zero error, three times over. The
  instruments do not disagree about *counting*; they disagree about *estimating*.
* **The error signature fits an estimator, not a dropped modifier.** A dropped
  modifier would have shown up in the object-level layer too. It does not — that
  layer agrees to 0.137 %.
* **A prior instance of the same bias is on record.** On `assembly14` the terrain
  module claimed 15,115,562,914 instanced / 16,307,129,669 evaluated while
  `poly_census.py` on the saved blend measured 13,842,597,953 / 15,099,440,337 —
  the module over-reporting by ~9 %. `docs/STAGING-R2-3541-to-R2-3600.md:303`
  flags it explicitly, months before this document.

### What is still open

**No instrument has accounted for the residual 1,888,598,933 triangles
object-by-object.** The evidence above says the generator over-estimates and the
census is the authority, and that is how this repository publishes it. It is not
the same thing as having closed the gap to the unit, and nobody should write that
it is.

**So: quote 17,707,774,735.** If the generators' 19,596,373,668 is mentioned at
all, label it *"the generators' own build-time estimate, ~11 % high"*. **Do not
average the two. Do not present the census as a lower bound. Do not drop the gap
from the record.**

The one *real* limitation of `poly_census.py` — that it walks the **viewport**
depsgraph — is separate and is documented in §10.

---

## 9. The superseded-terrain chain: 12.58 G → 15.07 → 16.16 → 16.31 → 19.28 G

This is the cleanest example in the project of the defect class this repository's
logs exist to catalogue: **a generator's self-reported number going stale four
times while remaining perfectly quotable the whole way.**

`build_terrain`'s evaluated-triangle figure, in order:

| value | where it lives | what it was |
|---:|---|---|
| **12,575,897,022** — published as **12.58 G** | `world/build_terrain.md:1026`; also `assembly2_build.json` | A **standalone local terrain build** — 1,027 unique meshes, 28,003 objects — predating every shipped assembly. |
| **15,072,255,777** | `assembly5` … `assembly10_build.json` | Six consecutive assemblies. Still 1,027 unique meshes. |
| **15,116,140,745** | `assembly11_build.json` | The library jumps to **1,432** unique meshes. |
| **16,158,549,193** — the **16.16 G** | `work/nearband/stats.json:28`, `work/nearband/full.log:41`; tabulated at `world/build_nearband.md:454` | The nearband study's own terrain baseline. |
| **16,688,041,589** | `assembly12_build.json` | |
| **16,307,129,669** | `assembly13`, `assembly14_build.json` | The last pre-ship value. |
| **19,279,121,746** | **`assembly15_build.json`** | **The world that shipped.** |

**The library figure travelled with it.** `build_terrain`'s
`base_library_tris` went 33,279,197 → 33,258,111 (six consecutive assemblies) →
33,499,359 → 33,491,131 → 33,494,051 → **33,623,237** over 1,432 unique meshes in
the shipped world, while the *published* value stayed **33.26 M over 1,027
meshes** — correction 4 in §13. The `README.md` line quoting "33.26 M … 26,641
trees" was corrected on 2026-08-18; `docs/README.md:173` still quotes the old
pair while describing a historical document and is deliberately left as written.

The published per-frame film total, 12,835,016,237, took the **first** row. By
then it had been superseded four times over and was **6.7 billion triangles
short on that one term alone.**

**It was internally inconsistent before it was ever stale.** The published sum
paired terrain's 12.58 G with a nearband figure of 233,842,416 lifted from
`world/build_nearband.md:454` — and that table's *own terrain line, two rows
above the number that was taken, reads 16,158,549,193.* Both numbers came off the
same table; only one of them was read.

The transferable lesson, and the reason this gets its own section:

> A generator prints a summary. The summary is written into a document. The
> document remains readable, quotable and confident for months while the
> generator's output moves by 53 %. Nothing in the pipeline marks the document
> stale, because nothing in the pipeline knows the document exists.

The defence this repository landed is not a process — it is the rule at the top
of this file: **a figure without its definition, its class and its source line is
not publishable**, because those three are what let a reader notice that
`build_terrain.md:1026` describes a standalone build with 1,027 meshes while the
shipped world has 1,432.

Related: `docs/DOC-ACCURACY-AUDIT.md` hunts this exact class across the whole
repository — *a claim that was true when written and is false now.*

---

## 10. The instrument: `tools/poly_census.py`

**Everything in §3 came out of this one script, and it is 100 lines.** A reader
who wants to check these numbers can.

```bash
blender -b -noaudio render/world/assembly/r2/assembly15.blend -P tools/poly_census.py
```

It takes roughly **19 minutes** on a world of this size and needs enough RAM to
open the blend (`assembly15.blend` is 9.59 GB; the delivered film blend is 10.96 GB
and wants ~52 GiB — see §11). It prints four totals and then the fifteen heaviest
single objects.

### What each layer means

Quoting the tool's own docstring, which defines them in exactly the terms this
document uses:

* **`BASE`** — sum over `bpy.data.meshes` of polygons, triangulated as
  `max(len(p.vertices) - 2, 1)`. What is *stored in the file*. Ignores every
  modifier and every instance. This is definition (a).
* **`EVALUATED`** — each scene object's mesh **after modifiers** (subsurf,
  solidify, mirror, geometry nodes that output geometry), one copy per object.
  What one copy really costs.
* **`INSTANCES`** — every instance the depsgraph emits, counted separately. For a
  world with millions of grass clumps this is the only honest figure.
* **`RENDERED`** = `EVALUATED + INSTANCES`. **What Cycles traces.** This is
  definition (b).

`BASE` is *not* a component of `RENDERED` — the same geometry appears in
`EVALUATED` after modifiers. Adding `BASE` to `RENDERED` is a category error.

### How it stays affordable

The instance loop caches converted meshes by `ob.data.name`, so a clump instanced
half a million times is converted **once**, not half a million times. Without that
cache a census of this world would not finish.

### Known limitations — state these whenever you quote it

1. **It walks the VIEWPORT depsgraph.** `bpy.context.evaluated_depsgraph_get()`
   in background mode gives the viewport evaluation, so any modifier with
   different viewport and render settings would be counted at its *viewport*
   level. The probe in §8 demonstrated this directly: a subsurf at viewport
   level 2 / render level 3 was counted at level 2.
   **Why it is inert here:** grepping `render_levels`, `show_render`,
   `show_viewport` and `use_render` across `world/build_terrain.py` and
   `world/build_nearband.py` returns **zero** matches. No generator in this
   project sets a viewport/render divergence, so the depsgraph the census walked
   is the one Cycles would have built.
2. **The instance cache is keyed on the mesh datablock name.** Two instance
   sources sharing one mesh datablock but carrying *different* modifier stacks
   would both be counted at whichever was seen first. Nothing in this world is
   known to do that, and nothing has checked.
3. **`EVALUATED` iterates `scene.objects`, so hidden objects are included.**
   The census measures the scene, not the visible frame. That is intentional —
   definition (b) is explicitly not frustum-culled — but it means the census is
   an upper bound on what any *one* camera position costs.
4. **It has never been run on `film25_breach.blend` itself.** See §11.
5. **It is not a floor.** The modifier-dropping hypothesis was tested and
   refuted; see §8.

`tools/instance_variety.py` is the companion instrument for the instance layer.
It reports the 4,966,913 / 1,569 split by family: **823 VEG / 746 SPECX**, top
family share **2.0 %**, gini **0.867**, verdict `INSTANCE_VARIETY_CLEAN`
(`docs/DEFECT-LOG-R2.md:56798-56801`, `docs/instance_variety.json`). No family
exceeds 40 % — which is what stops 4.97 M instances from reading as one repeated
asset.

---

## 11. What is not established, and why

Stated plainly rather than discovered later.

1. **The delivered film blend was never censused directly.**
   `render/film25_breach.blend` is 10.96 GB and needs roughly **52 GiB of RAM** to
   open (the render workers' own measured `VmHWM` is 52.42 GiB); the authoring box
   has 11 GB. So the per-frame total is the **recorded `assembly15` census plus
   additions measured from their own source blends**, not one census of the
   delivered file.
   **The residual risk is small and one-directional:** appending merges
   datablocks and the breach deletes six round-1 solids, so a direct census would
   land **at or slightly below** 17,707,774,735.
2. **The `assembly15` census was not re-run for this document.** It is a recorded
   measurement on a 9.59 GB blend that also cannot be opened on the authoring box.
   It is corroborated three ways: the EVALUATED + INSTANCES identity closes to the
   unit on **both** worlds; the same tool on `assembly14` and `assembly15` the
   same day returned identical realized-instance and distinct-source counts; and
   `docs/STAGING-R2-3601-to-R2-3660.md` records the re-measurement of every other
   gate on both worlds.
3. **The 10.7 % census-versus-generator gap is explained but not closed.** §8.
4. **The generators' placement-counter total, 4,955,784, was not reproduced
   field-by-field from `assembly15_build.json`.** §7.
5. **What would close 1 and 2:** a rented instance with ≥64 GB RAM — this
   project's own fleet, at roughly $0.46/hr — could open `film25_breach.blend` and
   run one authoritative census, for about **$0.50-$1.00** including the ~11 GB
   scene push. That buys provenance, not a correction: no figure here is expected
   to move by more than a fraction of a percent. **Nothing was rented for this
   document.**

---

## 12. Render settings and what the film cost

### Delivered spec

| | | source |
|---|---|---|
| engine | **Cycles** / OptiX | the blend's *saved* engine is `BLENDER_EEVEE`; the harness defaults `--engine` to `CYCLES`, and `docs/STAGING-R2-3841-to-R2-3900.md:194` records this being **checked, not assumed**, before launch |
| resolution | 3840 × 2160 at 100 % | `docs/MASTER-RUNBOOK.md:63-71` |
| frames | 1-2978 at 24 fps — 124.083 s, **0 cuts, one camera** | |
| samples | **512**, adaptive threshold **0.01** | `STAGING-R2-3841-to-R2-3900.md:184-199` |
| denoiser | **OpenImageDenoise** | as above, a checked default |
| grade | **AgX**, look None, exposure **−3.628** stops, SDR | authored in the blend; no `--exposure` was passed |
| camera | `ONER`, clip 0.05 - 200,000 m, scene DOF | overriding animated DOF is how round 1 lost a render |
| VRAM | **5.5 GB** on an RTX 5090 | because 4.97 M instances resolve to only ~1,569 distinct source meshes |
| CPU RAM per worker | `VmHWM` **52.42 GiB**, cgroup peak 64.52 GiB | |
| output | **23.5 GiB** of frames, 2,978 distinct sha256, all decoding at 3840×2160, 0 flat/black | `docs/STAGING-R2-3901-to-R2-3960.md:1596-1602` |
| image texture files | **0** | `work/r23661/build_film25.log:84` — *"world 'SKY_World' kept; 0 FILE images before, 0 after"*; every per-module `image_texture_nodes` in `assembly15_build.json` is 0 |

### Per-frame render time, over all 2,978 delivered frames

MEASURED, `docs/STAGING-R2-3901-to-R2-3960.md:1602`:

| min | median | mean | max |
|---:|---:|---:|---:|
| **194.7 s** | **283.8 s** | **280.0 s** | **445.1 s** |

### Cost

| | | |
|---|---|---|
| delivered master | **231.6 GPU-hours** | DERIVED: 280.0 s × 2,978 = 833,840 s |
| hardware | 3 exclusive whole-machine RTX 5090s on vast.ai, $0.428 / $0.454 / $0.455 per hour | frames split 993 / 993 / 992, coverage exact |
| wall clock | **97.3-97.7 h** (midpoint 97.5, approximate), launched 2026-08-09 ~04:06-04:30Z, complete 2026-08-13 05:45:19Z | the range is the launch-time uncertainty, not measurement noise. GPU utilisation ~79 % over ~292 machine-hours |
| cost of the master | **$132.57** | against a $150 ceiling. `docs/READING-LIST.md:140`, `docs/QUICKSTART.md:291`. **Treat as an upper bound** — `docs/DOC-ACCURACY-AUDIT.md:554-564` (§UNRESOLVED, U1) lists the master's isolated cost as UNRESOLVED, because the brokers' cumulative $141.06 covers their whole life including non-master work, and says explicitly **do not publish $141.06**. $132.57 is $141.06 less $8.49 of pre-existing banked spend. Cross-check: $132.57 / ~292 machine-hours = $0.454/machine-hour against quoted rates of $0.428-$0.455, agreeing to ~2 %. |
| everything else — every test, probe, calibration and retry | **161.9 GPU-hours** | MEASURED: `SUM(COALESCE(render_sec, exec_sec, 0))` over the jobs table of all twelve **local** `vast-render` broker databases; 2,764 jobs, 10,954 frame records |
| **project total** | **393.5 GPU-hours** | DERIVED: 161.9 + 231.6, two **disjoint** sets |
| **effective rate** | **$0.58 / GPU-hour** | $229.76 of vast.ai spend over the period ÷ 393.5 GPU-hours. An **upper bound**: vast.ai also bills boot, image pull, scene upload, idle and teardown, so rental hours exceed GPU-work hours and the true rate is lower. |

**The 161.9 h figure was published as the project's *total* GPU time, and that was
wrong.** 161.9 h is the sum over the twelve *local* broker databases, and the
delivered film render is in none of them — it ran on remote brokers 3, 4 and 5
whose databases lived on the rented machines. The film alone, at 231.6 h, is more
than the total it was supposedly inside. The rate published alongside it,
$1.42/GPU-hour, was inflated **2.4×** purely because its denominator omitted the
film.

---

## 13. The seven corrections

Every figure this document replaces, and what each one actually was.

| # | published | correct | the fault |
|---|---:|---:|---|
| 1 | 55,175,846 as *"the project's polygon count"* | **55,242,834** browser triangles **drawn** per frame, definition (d) | **Two faults.** *Scope:* it is the **web build's** figure; quoting it as the project's scale under-stated the film by **321×**. *Value:* also wrong twice over — `architecture.glb`'s 66 `EXT_mesh_gpu_instancing` master meshes (6,928 tris) were counted at their own node transform **and** once per instance row, which the glTF spec forbids; and the car was entered at its **unique** 875,411 inside a per-frame **drawn** total when the shipped hero draws 949,327 over 584 mesh nodes / 547 meshes. The errors partly cancelled: −6,928 + 73,916 = **+66,988**. |
| 2 | 12,835,016,237 film triangles/frame | **17,707,774,735** (**+38 %**) | **Wrong in five independent ways at once.** §9 for the stale terrain term; it was also internally inconsistent before it went stale; the term was **COMPUTED**, not measured; it omitted `build_items` (42,467,316), `build_sky`, the breach, the ceiling and the props; and **it omitted the car**. |
| 3 | 38,222,478,354,586 whole-film | **52,733,753,160,830** | A **third, separate** defect: the published value was not even the product of its own premise. 12,835,016,237 × 2,978 = 38,222,678,353,786, so it was **199,999,200 short** of the number it claimed to be. Found by re-running every arithmetic chain rather than trusting any of them. |
| 4 | 33,300,000 unique over 1,027 meshes | **138,073,595** for the film; **123,422,404 over 3,445 meshes** for the world alone | It was `build_terrain`'s **own library only** — not the world's, let alone the film's — **and** a stale generation of it. Shipped terrain records 33,623,237 over 1,432 meshes. |
| 5 | 11,760,000 for `build_barriers` | **11,562,480** | A rounded number with no source anywhere in this repository. |
| 6 | 161.9 GPU-hours; $1.42/GPU-hour | **393.5 GPU-hours; $0.58/GPU-hour** | §12. The delivered film render was in none of the twelve local broker databases that the 161.9 was summed from. |
| 7 | *"0 image textures in the entire world"* | **0 in the film, 0 in the 8 map GLBs, 4 in the shipped browser car** | True as written of the film and of the map, **false of the shipment**. The web build bakes the car's procedural livery down to 4 WebP textures so a browser can afford it; the film has none at all. **Always scope it.** The true and more interesting claim is *"0 image textures in the map — every surface is procedural."* |

**Before any of that, the instancing count was got wrong three times in a row** —
62,917, then 63,270, then 63,334 — each time by **deriving** a number when a
measurement already existed to be read. The receipt carried the field. Reading it
gives 76,845. That is the origin of this document's standing rule:

> **Read the measurement. Do not derive around it.**

---

## 14. Which of these sources a clone will actually have

A citation you cannot open is not a source. **Checked against the tracked tree on
2026-08-18**, and stated here rather than discovered later:

**In the repository — you can follow these:**

| | |
|---|---|
| `docs/DEFECT-LOG-R2.md` | the four census layers of §3, at `:56794-56801` |
| `docs/STAGING-R2-3601-to-R2-3660.md` | the same table at `:371-377` |
| `docs/STAGING-R2-3841-to-R2-3900.md`, `docs/STAGING-R2-3901-to-R2-3960.md` | the render spec and the per-frame timing of §12 |
| `world/build_terrain.md` | the 12.58 G row of §9, at `:1026` |
| `tools/poly_census.py`, `tools/instance_variety.py` | the instruments |
| `docs/beat_sheet.md`, `docs/explode_plan.json` | the car's `MB_` monocoque figure |
| `docs/DOC-ACCURACY-AUDIT.md`, `docs/QUICKSTART.md`, `docs/READING-LIST.md` | the cost caveats |

**Gitignored — present on the authoring machine, absent from a clone:**

| | what it carried here |
|---|---|
| `render/world/assembly/r2/assembly15_build.json` | **the whole of §7**, the generator figures of §8, and the shipped end of §9's chain |
| `render/world/assembly/r2/assembly2..14_build.json` | the rest of §9's chain |
| `work/r23661/build_film25.log`, `breach25.log`, `measured_film25_breach.json` | the film-only additions of §4, the sky, the texture count |
| `work/nearband/stats.json`, `work/nearband/full.log`, `world/build_nearband.md` | the 16.16 G row of §9 |
| `docs/STAGING-R2-3541-to-R2-3600.md` | the defective `assembly15` of §3 and the ~9 % gap flagged on `assembly14` |
| `docs/inventory_iter.json`, `docs/instance_variety.json` | the car decomposition; the instance-variety split |
| every `.blend` | so no figure here can be re-measured from a clone alone |

**So: §3's headline census is followable in a clone; §7 and most of §9 are not.**
Everything in the ignored column is a build record or a log, not source — this
repository tracks source and reasoning and does not track artefacts (see the
`.gitignore` header for why). The figures were transcribed here **because** the
records they came from will not travel, and every one of them was read from the
file named beside it on 2026-08-18. Promoting the `*_build.json` records into the
tracked tree would close the gap and is a deliberate decision for the owner, not
one this document took.

**Line numbers versus entry IDs.** `docs/DEFECT-LOG-R2.md` is append-only and
**line numbers move**; entry IDs do not. The stable citations for §3 are
**`R2-3605`** (the rebuild) and **`R2-3606`** (the gates re-measured on both
worlds). The `:56794` style line numbers throughout this document are as of
2026-08-18 — use them to find the entry, then trust the ID.

---

## See also

* `docs/DEFECT-LOG-R2.md:56720-56805` — `R2-3605` / `R2-3606`, the rebuild of
  `assembly15` and the census table §3 quotes.
* `docs/STAGING-R2-3601-to-R2-3660.md:371-377` — the same table in its staging file.
* `docs/STAGING-R2-3541-to-R2-3600.md:303` — the ~9 % generator-versus-census gap,
  flagged on `assembly14` long before §8.
* `docs/DOC-ACCURACY-AUDIT.md` — the audit for claims that were true when written
  and are false now. §9 is a worked example of what it hunts.
* `docs/BROKEN-INSTRUMENTS.md` — the general form: a check that returns the same
  answer whether the defect is present or absent.
* `docs/MASTER-RUNBOOK.md` — the 4K master run, its gates and its costings.
* `tools/poly_census.py`, `tools/instance_variety.py` — the instruments.
* `render/world/assembly/r2/assembly15_build.json` — the generators' own build
  record for the shipped world.
