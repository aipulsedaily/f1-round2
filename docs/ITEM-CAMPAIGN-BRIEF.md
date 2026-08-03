# The per-item hero asset campaign — the contract

> "1 agent per ITEM in every scene to build each item a trash can a water bottl
>  the tire of the truck the haul etc. to extreme realesim and perfeciton etc."

435 items. One agent each. None of them can see the others' work, and every one
of them will finish by reporting success. This document is what makes that
survivable: the standard they all build to, and the gate that decides whether
they actually met it.

`docs/item_manifest.json` is the single source of truth for **what exists**. This
file is the single source of truth for **what "done" means**.

---

## 1. The seven laws (from the manifest — non-negotiable)

1. **Everything is built by hand, procedurally, in Blender.** No downloaded
   models, no photo textures, no HDRIs, no AI-generated anything. The project is
   currently clean — verified zero image-texture nodes. Keep it that way.
2. **No real sponsor names or team liveries.** 31 invented brands already exist
   in `build_dressing`'s brand book; 12 are shared with `build_architecture`.
   Reuse them — inventing a 32nd fragments the world's identity.
3. **Scale against the measured car:** 5.698 m long, 2.005 m wide, 0.340 m ride
   height. Not against intuition.
4. **z = 0.000 is simultaneously** the showroom floor, the paddock apron, the
   access road and the pit-straight racing surface. One plane, no lip, no step.
5. **Anything standing on ground embeds ≥ 0.020 m** (`BASE_EMBED_M`) and is
   placed with `world_contract.world_ground_z`, never on an assumed z.
6. **Recentre every object on emit; every material reads `TexCoord → Object`,
   never `Geometry → Position`.** At |P| ≈ 1000 m a position-driven procedural
   loses all precision — this is why the first pass had blotching.
7. **Chunk along s** so no object spans more than ~80–260 m of circuit.

---

## 2. The quality bar

The user rejected the first world pass as *"okay kinda cute"* and then rejected a
4K frame as *"half assed… the grass is blurry."* Both times he was right. Treat
"okay" as a failing grade.

> "push this as far as phiscally possible we have all the time in the world.
>  idc if it takes a month"

**Render time and wall-clock are not constraints.** Never trade quality for
speed. The three specific standards that came out of those rejections:

- **Material depth.** A flat colour is a placeholder. Every surface needs layered
  history — base variation, roughness variation, edge wear, dirt, repair.
- **Detail is a GEOMETRY problem, not a material problem.** A grass shader on a
  flat plane cannot look like grass 2.4 m from the lens. If a feature would be
  visible at the item's filmed distance, it must exist as mesh.
- **Instanced things need genuine per-instance variation**, not one mesh rotated
  randomly. His named failure is *"one tree spammed 100 times."*

---

## 3. Your item tells you how much detail it needs

Every manifest record carries the numbers that decide this. Do not guess:

| field | what it obliges you to do |
|---|---|
| `nearest_camera_m` | the closest the camera ever gets. Build for this. |
| `lens_at_closest_mm` | with this lens — a 21 mm at 0.8 m is not a 58 mm at 2.6 m |
| `onscreen_px_4k` | how big the thing reads on the 4K master |
| `instances` | how many exist, hence how much variation is required |
| `variation_axes` | *what* must differ between instances — already decided for you |
| `depends_on` | build these first; do not redefine them |
| `notes` | the item's specific brief, often naming the exact shot it appears in |

Screen resolution at your item's own distance:

```
px_per_m = (3840 × lens_mm / 36) / nearest_camera_m
```

`kerb_hero_t4` is filmed at 0.8 m on a 21 mm lens — 2800 px/m, so a 0.4 mm chip
in the paint is a visible pixel. `armco_w_beam` at 2.6 m on 35 mm is 1436 px/m,
so a bolt chamfer at 4 mm is 6 px. **Build to the pixel, not to the vibe.**

---

## 4. Acceptance — eight measurements, not a claim

*Rewritten 2026-08-02. The previous version of this section described four
checks; the gate has had eight since #59 and it now renders its own witness
frame. If you were told "four checks", you were told wrong.*

```bash
/opt/blender-5.2.0-linux-x64/blender -b <your_module.blend> --factory-startup \
    -P tools/item_gate.py -- --item <id> --collection <YOUR_ITEM_COLLECTION> \
                             --out render/items/<id>/gate.json
```

Four checks are free and run first, off the mesh. If any of them fails the gate
does not queue a GPU job at all, and the remaining four report **NOT MEASURED**
— which is a rejection, not a pass.

| # | check | what it measures | what it catches |
|---|---|---|---|
| 1 | `no_external_assets` | image-texture nodes and external image files, anywhere in the file | a downloaded texture or HDRI, i.e. Law 1 |
| 2 | `material_depth` | count of procedural texture nodes reachable from the surface output; ≥ 6 hero, ≥ 3 otherwise | a flat colour with no graph behind it at all |
| 3 | `geometry_resolves_at_distance` | **10th-percentile** edge length in screen px at the item's filmed distance; ≤ 6 px hero, ≤ 16 px otherwise | an object with no mesh detail finer than a pixel — "a smooth tube" |
| 4 | `per_instance_variation` | realized-instance walk: `distinct_sources`, `distinct_shapes`, and the commonest source's share | "one tree spammed 100 times", and its sequel, 420 datablocks holding 6 poses |
| 5 | `witness_frame_valid` | the delivered frame's dimensions, subject and control pixel counts, clipping and crush, and whether the control sphere is lit by a warm sun from the side | a frame that is black, blown out, lit from underneath, or not the resolution it was staged for — R2-020 and R2-021 |
| 6 | `surface_microstructure` | band-passed contrast at r1–r2 (1–2 px) as a ratio to the strictest **brightness-matched smooth control in the same frame** | a surface flatter than the placeholder blob beside it. `crew_fireproof_overall` has 28 texture nodes, `spectator_seated` 51, and both measured flatter than a featureless ovoid |
| 7 | `relief_reads_as_lip_and_shade` | luminance asymmetry along the sun direction: does the surface have a sunward lip and a shadowed side, or is it a single-value mark? | **texture painted on instead of built.** This is the check 21 of 28 wave-1 items fail |
| 8 | `silhouette_departs_from_analytic` | RMS departure of the outline from a fitted analytic curve, in mm, against the control | cloth that is a machined cone. `crew_fireproof_overall`'s trouser fitted a quadratic taper to 0.61 px RMS where real Nomex perturbs 5–10 mm |

**`material_depth` is kept only as a free pre-render floor, and its own
docstring says plainly that it does not measure appearance.** Counting nodes was
the wrong instrument: the two items that most obviously failed the eye passed it
comfortably. Checks 6 and 7 are what actually discriminate. Do not read a
`material_depth` pass as evidence of anything but "a graph exists".

### The witness frame — the gate renders its own

The gate no longer judges your macro. It stages its own scene on the 5090:
**your subject beside a plain sphere, a plain plane and a six-step grey wedge**
(albedos 0.02 → 0.95), all under the contract sun, and measures checks 5–8
against those controls. Three consequences you have to build for:

- **The subject is chosen for you.** With a population it is the **median by
  triangle count** — the typical instance, not the best one. Building one hero
  bay and pointing the camera at it moves nothing. With a single instance it is
  the largest object by bounding-box diagonal, because "median sub-part" once
  picked a 10 mm sealant strip and reported on a road slab.
- **Every number is a RATIO inside one frame.** Nothing moves if the manifest's
  filmed distance turns out to be wrong, which matters because most of them are:
  `nearest_camera_m` was measured abeam. `--filmed-distance-m` and
  `--onscreen-px-4k` supply a corrected figure without editing the manifest, and
  whichever was used is recorded in every report.
- **Look at the witness PNG.** It is written next to your report. A measurement
  cannot tell you its input was black, and on this project that exact mistake
  produced a confident published conclusion about a working instrument (R2-021).

### The four things that make a check FAIL rather than skip

- **Unproven is a FAIL.** An item that declares 7,800 instances, shows 262
  objects and yields no realized instances has not been measured (R2-018,
  R2-019). Build the test scene so it **realizes a representative sample** —
  leave the instancer in the depsgraph rather than pre-flattening it.
- **Transform randomisation is not variation.** `distinct_sources` counts source
  geometry: one mesh instanced 7,800 times scores **1** however wildly the
  transforms are randomised. The requirement scales with population,
  `max(8, min(40, sqrt(n)))`, and the commonest source may hold at most 25 %.
- **The 10th percentile, not the median.** Most of a guardrail is smooth beam
  whose edges are legitimately long. The question is not "is everything fine"
  but "does fine detail exist anywhere". If even the finest decile is coarser
  than a screen pixel, nothing on the object resolves.
- **A failed render is a failure, never a skip.** If the witness frame does not
  arrive, three checks were not measured.

### Deliver the macro at 3840 × 2160

`item_gate.py` computes every pixel figure from `RES_X_4K = 3840`, and the
`px_per_m` formula in section 3 has 3840 in its numerator. The wave-1 harness
asked the renderer for 1920 × 1080 and **11 of 28 heroes shipped at half
resolution and were scored as 4K** — every pixel judgement on them out by
exactly 2× (R2-020). A 1080p macro is not a smaller version of the deliverable,
it is a different measurement. Use `itemkit.macro_rig()`, which will not produce
another resolution unless asked by name, and **read the dimensions back off the
file you wrote** — what you asked `rq` for is not evidence of what landed on
disk. `tools/campaign_preflight.py --policy wave2` enforces this.

### Prefer `--collection` to `--prefix`

`--prefix` exists so an item can name itself when no collection matches. It is
taken **as given**: no standin filter, no collection consulted. It was
introduced so `marshal_post_deck` could exclude the 50 `CTX_Column` stand-ins in
its test scene, and the gate now does that itself — measured on that blend, 75
meshes of which 50 are `CTX_` carrying 16.8 % of the faces, and auto-detection
selects the right 25 with no flag at all. All 28 wave-1 items re-gate correctly
without it.

Since 2026-08-02 the gate also checks that a `--prefix` has not been used to
carve a piece out of the item: if it drops objects that are not named like
stand-ins, the gate **refuses** and names them. `--collection` is filtered,
reported, and skips standin/context sub-collections on its own. Use that.

**One number is reported but deliberately not gated:** triangles per declared
instance. The rejected grandstand crowd measured **390 triangles per person**,
which cannot carry a finger, a face, or a fold of cloth. Every other threshold is
distance-relative, and at 14.7 m the 6 px limit permits 29.5 mm features — so a
body of 30 mm facets passes every automated check while reading as a mannequin.
No threshold is set because a trash can and a human need different budgets and
one invented number for 435 item classes would be a guess wearing a
measurement's clothes. **Look at it, and ask whether it is enough for your item.**

### 4a. THE RELIEF-AMPLITUDE LAW — state the LIGHT, not the millimetres

*Added 2026-08-02. This is the single most expensive thing on this project that
was not written down. Read it before you choose any bump depth, any noise
amplitude, or any fold-field displacement.*

**What the eye judges is not the height of a bump. It is the radiance modulation
the bump produces.** A Lambertian surface lit at elevation `e` has radiance
∝ `sin(e)`; tilt its normal by `θ` and that becomes `sin(e ± θ)`, so the relative
peak-to-peak modulation is

```
m = 2 · θ / tan(e)            (exactly: m = 2 · sin θ / tan e)
```

**This film's sun sits at 12.47°, where `tan(e) = 0.2213` — a 4.52× amplifier**
against a midday reference. The same crumple that is a soft grain at noon is a
saturated crust here.

**Do not compute this by hand and do not write 4.5 down anywhere.** `itemkit`
derives it from `world_contract.SUN_ELEV_DEG`, so if the sun moves the amplifier
moves with it:

```python
amp_mm = K.relief_amplitude_for(0.28, wavelength_m=0.008)   # -> 0.079 mm
nt.bump(h, 1.0, modulation_pp=0.28, wavelength_m=0.008)     # same, wired
K.relief_budget(stages, band="isotropic_micro")             # audit what exists
```

`relief_amplitude_for` is the same fix shape as `noise(wavelength_m=…)` replacing
a raw `scale=`: **state the physical quantity you actually mean.**

**A wavelength is not optional.** The same 0.5 mm is `m = 1.74` on an 8 mm
crumple and `m = 0.14` on a 100 mm flute — a factor of twelve. An amplitude
without a wavelength is not a relief specification.

#### What the record supports, and it was judged by eye

Three amplitude sets were rendered and **rejected** on the human figures, and
every one of them had been reasoned about in **millimetres of cloth**:

| set | slope | m | how it rendered |
|---|---:|---:|---|
| shipped | 5.0° | 0.79 | a machined cone |
| first fix | 22.6° | 3.76 | coarse stucco |
| second fix | 10.4° | 1.66 | thick felt / towelling |
| **accepted** | **1.8°** | **0.28** | cloth; creases carry the rest |

**Bound it both ways.** 0.79 was rejected for being too little exactly as 3.76
was rejected for being too much. `itemkit.RELIEF_BANDS` carries the bands the
record supports — `isotropic_micro` 0.12–0.45, `isotropic_macro` 0.35–0.95,
`sparse_crease` 0.80–1.60, `geometry_fold` 0.60–1.40, `hard_feature` 1.5–6.0 —
and `relief_budget(..., band=…)` marks a stage `LOW` as readily as `HIGH`.

#### CHECK BOTH LAYERS. This is where it repeated.

Once the fabric **shader** was corrected to 0.28 pp, the same misconception
turned out to exist one layer down in the **fold-field GEOMETRY**: 8.2 mm of
radial displacement at a 100 mm flute is a 14.4° surface, `m = 2.32`, and it
became the dominant defect. Corrected 2.09–4.16 → 0.93–1.29 pp.

Nothing that reads materials could ever have seen it. Run both:

```bash
blender -b <your.blend> --factory-startup -P tools/relief_audit.py -- --item <id>
```

which reports every `ShaderNodeBump` as a slope and an `m` (walking back to the
texture driving its Height for the wavelength) **and** the mesh's own dihedral
angles banded by edge length, as an RMS slope and an `m`. Correcting one and not
the other is exactly what happened, twice.

#### What the 21 rejections look like under the law — measured, 2026-08-02

`tools/relief_audit.py` was run over all 28 wave-1 witness blends. The check-7
rejections are **not** a single story, and the law is what makes that visible:

- **Five have essentially no relief in either layer.** `asphalt_wearing_course`
  m 0.002 shader / 0.107 geometry, `gravel_bed_surface` 0.051 / —,
  `paddock_paving_bay` 0.008, `access_road_slab` 0.178 with one stage,
  `driver_figure` 0.005 / 0.24–0.73. These are exactly "rejected for an
  amplitude they had no way to know to target". The fix is
  `relief_amplitude_for` and a re-run.
- **One fails from the other end.** `tyre_blanket` runs at m **6.0** median in
  the shader and 4.0–6.9 in the geometry — twenty times the accepted cloth
  target of 0.28 and well past the 3.76 that was rejected as *coarse stucco*.
  The old framing had no way even to say this; a bound with only a floor cannot.
- **Fourteen of the 28 ship a DEAD BUMP STACK,** and this was not previously on
  record. Their built blends carry the R2-038 wiring — the chain pinned into
  `Height`, the height texture into `Filter Width`, and the first bump of every
  chain sitting on a **constant**, which has zero gradient and therefore
  contributes no relief at all. 122 stages across 14 modules. For those, the
  amplitude was never the variable. `itemkit.NT.bump` wires by name and was
  fixed on 2026-08-02; those modules need a **rebuild**, not a re-tune.
- **It is in the passers too**, which is why it survived: five of the seven
  modules that PASS check 7 also have wholly dead shader stacks
  (`armco_post`, `crew_fireproof_overall`, `pit_wall_unit`, `pont_girder`,
  `tyre_wall_tyre`). **They pass on their geometry** — every one of them carries
  m ≥ 2 in the mesh's own dihedrals. That is the strongest single lesson in this
  table: **on this film's sun, the mesh carries the read and the shader
  garnishes it.**

The gate itself is not in question. Check 7 was validated against a physical
ladder — monotonic across 0/0.5/2/8 mm ribs, painted stripes scoring inside a
flat plate's margin — and **its verdicts stand**.

### 4b. WHICH SIDE OF THE SURFACE DOES THE RENDERER GET?

*Added 2026-08-02.*

An orientation audit of a finished human figure found **54 of 318 emitted pieces
facing inward** — head shell, both ears, the hair mass, both shoe uppers, both
soles, all 22 tread bars. It passed every check in the project, because every
check measured the **model** and none measured the **side**. The audit sweep
then found inward pieces in **20 of 30 built item blends**, so this is not
confined to the figures.

**Read the next paragraph before you spend a day on it.** The mechanism that was
*attributed* to it — "Cycles flips a back-facing normal, so it rendered with
every bump inverted, a brow ridge lit as a groove" — **is not what Cycles
does**, and that has now been measured. `tools/winding_probe.py` renders one
sphere, in one place, under the contract sun with a 12 mm ridge at m = 2.2,
correct and reversed:

| | result |
|---|---|
| `Geometry > Backfacing` | correct **black**, reversed **white** — Cycles knows |
| lit render, Principled + Bump | mean \|difference\| **0.00011**, high-pass correlation **+0.9997** |
| the same with true **displacement** | mean \|difference\| 0.0117, correlation +0.9553 |

For an **opaque Principled surface with a bump** — which is what every item in
this campaign is — an inside-out shell renders **the same picture**. So do not
budget a repair-and-re-gate campaign for it.

**Where it does decide the picture:** true displacement (measured above),
refraction and transmission (a reversed glass shell refracts as if the camera
were inside the glass — `showroom_facade_panel` and `mullion_intact` are glass),
subsurface scattering, any shader reading `Geometry > Backfacing`, and every
consumer that is not Cycles. It is also **free** — `new_mesh` orients on emit —
so get it right on the way in rather than arguing about it later.

**A mirrored piece has reversed winding BY CONSTRUCTION.** So does a ring loft
walked the other way, a swept profile with a flipped parameter, and a capped
boundary loop. These are the idioms every item module is built from.

`itemkit.new_mesh()` now runs `orient_outward` by default, so this cannot reach
the renderer from a new module. Pass `orient=False` **only** for a surface that
is deliberately one-sided, and say why in a comment.

To check something already built:

```bash
blender -b <your.blend> --factory-startup -P tools/winding_audit.py -- \
        --item <id> --rays 600
```

Three things it reports, and you need all three:

- **`inward`** — pieces whose exact signed volume says they face the wrong way.
  Decided per connected component, closing open pieces by capping their boundary
  loops first. No heuristic and no deadband.
- **`undecidable`** — pieces that enclose too little to have an inside: a road
  slab, a paving bay, a lone plate. **These are left alone**, deliberately.
  Flipping a correct road surface across the whole film is a worse defect than
  the one being fixed.
- **`ray.fraction`** — rays cast from the hemisphere a camera can occupy, first
  hit taken, back faces counted. **This is the one that says whether it
  matters.** An inward piece buried inside solid geometry costs nothing; a
  reversed head shell is why this section exists. A count alone will not tell
  you which you have.

**If you repair winding on a built module, re-gate it and look at the before and
after.** The measurement above says the pixels will not move for an opaque
bump-shaded surface — so if your before/after *does* move, something else moved
with it and you need to know what.

### The gate is necessary, not sufficient

It cannot judge whether the thing looks good. It exists so that human attention
is spent on taste instead of on catching placeholders. **Every item also ships a
macro render at its own `nearest_camera_m` and `lens_at_closest_mm`**, which is
pixel-peeped by eye. An item is done when the gate passes *and* the render
survives that look.

---

## 5. Placement

Anything you put into the world is subject to `tools/placement_gate.py`:

> "you need to make sure theres no building no fences etc ont he road every thing
>  to be perfectionasistly placed onto the map"

It reports **intrusion depth in metres** into the road corridor, the car's driven
path and the camera's flight path, ranked worst-first. A finding reads "move this
1.4 m outboard", so there is nothing to interpret. Edge-defining families (kerbs,
sub-base, pit wall) are held to the true half-width rather than the courtesy
margin — they may sit at the boundary, never inside it.

Do not silence the gate by adding your item to an allow-list. If your item is
genuinely an edge-definer, say so and it gets the tighter threshold instead.

---

## 6. Waves

From the manifest, closest-and-most-depended-upon first, so that anything with
dependants exists before its dependants are built:

| wave | scope |
|---|---|
| 1 | ≤ 4 m from the lens, or depended on by ≥ 4 other items |
| 2 | ≤ 10 m, or depended on by ≥ 2 other items |
| 3 | ≤ 15 m — the hero threshold |
| 4 | ≤ 25 m |
| 5 | ≤ 45 m |
| 6 | > 45 m — silhouette and mass only |

343 of the 435 items are heroes. The tail is not filler: wave 6 sets the horizon
the whole frame is read against.

---

## 7. What to hand back

1. The module under `world/items/<id>.py`, defining a top-level `build()` and
   emitting into a named collection. **Import `world/itemkit.py`** for the
   scaffold — sun, camera, collections, node DSL, hash and noise, brand book,
   interface JSON — and read `world/items/REFERENCE.md` first. A census of the
   28 wave-1 modules found 29.9 % of 102,554 lines in functions whose name
   recurs across three or more of them. Spend your budget on the object.
2. `render/items/<id>/gate.json` — the gate report, passing.
3. `render/items/<id>/macro.png` — the macro render at the manifest's own
   distance and lens, **3840 × 2160** (see section 4).
4. A short note naming what you built, what you measured, and **anything you
   could not verify**. An unverified claim reported as unverified is useful; an
   unverified claim reported as done is a defect with a delay fuse.

Do not report success on the strength of the code having run. On this project the
verification has been the broken thing four separate times — see R2-017. Measure
the artefact, not the process.
