# build_items — the stage between `world/items/` and `assemble.py`

**Written for R2-226.  It is the answer to `docs/ITEM-PRESENCE-CENSUS.md`:
0 of 41 item modules contribute a single datablock to `assembly9.blend` or
`film14.blend`, and the cause is that there was no stage.  Nothing failed
because there was nothing to fail.**

    assemble.py --mods surface,barriers,architecture,terrain,dressing,items
                                                                    ^^^^^

---

## 1. The finding that decided the design

The census concludes that no item module carries placement data.  That is true
of the **documents**.  It is not true of the **artefacts**, and the difference
is the whole design.

Measured directly out of the built test blends (`work/r2226/inventory_item.py`,
which refuses if the declared collection is absent and prints its own
`STAGE RESULT`):

| item | objects | distinct meshes | centroid extent, WORLD metres |
|---|---:|---:|---|
| `armco_post` | 3,236 | 3,236 | x [−716.9, 552.7]  y [−256.8, 926.9] |
| `catch_fence_post` | 676 | 676 | x [−716.9, 625.8]  y [−257.2, 983.9] |
| `crew_figure` | 120 | 120 | x [−58.8, −30.1]  y [−64.3, −37.3] |
| `heras_fence_panel` | 771 | 771 | x [−109.9, 377.8]  y [−105.5, 320.0] |
| `timing_stand` | 10 | 10 | x [161.9, 317.2]  y [47.3, 177.7] |
| `tyre_wall_tyre` | 338 | 338 | x [246.6, 267.3]  y [895.6, 928.1] |

Those are circuit coordinates, not a bench layout.  The modules import
`world_contract` and resolve every unit through `C.su_to_world(s, u)` and
`C.world_ground_z(x, y)` **at build time**.  Projected back onto the centreline
by the stage's own check, `crew_figure` sits at **s 3232.6 – 3262.0, u +53.8 –
+85.9 m** — the paddock behind the pit building, which is where a crew belongs.

**So the missing stage is a TRANSFER, not a placement solver.**  Every item's
position was already computed, by its author, through the same contract every
class-level builder reads — and then dropped on the floor at the door.  This
module is that door.

## 2. How it fits the other builders

`build_dressing` states its rule as *"`anchor()` is the only way anything in
this file touches the ground"*.  The analogue here is stricter: **`build_items`
computes no position at all.**  It owns no datum, no width, no ground height and
no transform.  The only spatial thing it does is *check* — it projects every
placed object back onto the centreline and refuses a population that does not
land on the circuit.

Everything else is the shape of the other five modules: `assemble.py` calls
`build()`, `build()` returns a flat summary dict, every datablock it owns lives
under one root collection (`R2_Items`) and is purged before a rebuild, so two
consecutive calls give an identical scene.

**It runs last, and that is not alphabetical.**  An item may supersede
class-level geometry, and it can only take out what has already been built.

## 3. The registry, and why there is no auto-detection

`world/items/PLACEMENT.json`, 41 rows, one per module.  An item with no row is a
**refusal**, not a guess.

R2-180 is what a guess looks like: a detector fell through to *"any item
collection, biggest wins"* and silently measured another item's floor.  The
corpus has four collection naming schemes — `W_Item_TimingStand`,
`ITEM_MARSHAL_POST_DECK`, `PDS_Deck` + `PGD_Girders`, `CFO_Crew` — and
`armco_post_test.blend` contains a **foreign** `W_Item_ArmcoWBeam` collection
holding 33 objects of another item.  A fall-through would have eaten it.

Each row's facts are read from an artefact, never typed:

| field | established by |
|---|---|
| `collection` / `prefix` | the module's own top-level constants, by AST. Agrees with the census §8 table on **all 41 rows** — two independent readings |
| `expect_objects` | the inventory probe where one was run, else the canonical `render/items/<id>/gate.json` `measured.objects` |
| `source_sha256` | sha256 of the **whole** blend. Never a prefix of one: `tools/provenance.py` — *"a hash of the first N bytes is a hash that LIES"* |
| `supersedes` | `assembly9_build.json`'s own counters and `assembly9.blend`'s object-name list, read back from the 4.21 GB artefact |
| `state` / `blockers` | judgement, each blocker naming the measurement behind it |

The registry is keyed on the **module**, not the manifest id.  `pit_wall_unit`
and `pit_wall_unit_itemkit` declare the same id *and the same collection*; so do
`showroom_facade_panel` and `showroom_facade_panel_v2`; and `spectator_crowd.py`
sets `ITEM = "spectator_seated"`.  A registry keyed on the id would have
silently dropped one of each pair.

## 4. What it refuses, and which defect each refusal is

| refusal | the defect it is |
|---|---|
| item has no registry row / declared collection absent from the blend | R2-180 — "biggest wins" measured another item's floor |
| `expect_objects` ≠ what the blend holds | a `--limit` gating sample shipped as the population.  `tyre_wall_tyre` holds 338 of a declared 2,255 |
| gate verdict ≠ `ITEM_ACCEPTED` | a placement stage that ships un-accepted geometry makes the gate optional |
| any mesh datablock with more than one user, any instancer, `distinct meshes ≠ objects` | the no-repeats red line |
| family `top_share` > 10 % at ≥ 10 units | `WAVE2-SCOPE` §4.3's per-family bound |
| a multi-unit population collapsed within 25 m of the world origin | a LOCAL-frame blend placed at identity.  Five modules build local and publish `place=(R, t)`; the registry does not yet carry their transforms |
| appending would produce a `.001`-suffixed collection | the item is already in this world; placing it twice is the defect the stage exists to prevent |

Staleness is **reported and never gated**, on its own greppable
`>> ITEMS STALE CLOSURE:` line.  R2-119 measured 30 of 32 item blends stale
against their whole import closure and 0 of 32 against their own module.  That
is the campaign's standing condition, not a regression; a verdict that failed on
it would fail every assembly and be ignored inside a week.

## 5. Supersede — "the old version has to come out"

Census §3.2: *"a module for an item the world already builds must be integrated
against existing geometry, and the moment it is placed the old version has to
come out."*

Every row declares `supersedes` as **exact object names, never patterns** — a
pattern that swept one object too many would delete a neighbour's work, and this
stage runs after every class-level builder.  Two kinds:

* `{"object": "BR_TyreWall_T4"}` — a whole object.  The stage removes it and
  reports the removal with its triangle count.
* `{"welded_in": "ARCH_PitWall", "counter": "pit_wall_stands", "n": 5}` — welded
  inside a shared class mesh.  The stage **cannot** take it out: that is a
  change to `build_architecture` and a full assembly.  It prints
  `>> ITEMS REBUILD OWED:` and the debt is carried, not hidden.

This is why only one row is in state `PLACE`.  Of the 41: **24 would
double-build geometry the world already welds**, 22 are not `ITEM_ACCEPTED`,
15 hold a partial population, 6 are probes, 5 build in a local frame, 3 have no
blend, 2 are duplicate modules of another row and 2 lay their population out on
a grid for the macro camera rather than in the world.

## 6. The no-repeats line, and where it is won

`WAVE2-SCOPE.md` §4.2: the world-level spam check **cannot fire**.  One mesh at
500,000 copies scores **7.01 % against a 40 % threshold**, because the
denominator is 4.7 M grass instances.  *"The named failure the user drew a red
line around is invisible to the instrument that carries its name."*

Placement is the only stage at which a "one mesh, many transforms" shortcut can
enter, so it is where the line is won.  Three ways, weakest first:

1. **Structurally.**  The stage copies object datablocks one for one.  There is
   no code path here that creates an instance, a linked duplicate, a particle
   system or a geometry-node emitter.  It cannot take the shortcut because the
   shortcut is not written.
2. **By assertion, every run.**  `distinct meshes == objects`, every mesh with
   exactly one user, no object with `instance_type != 'NONE'`.  Measured on the
   six candidates: **3236/3236, 676/676, 120/120, 771/771, 10/10, 338/338**,
   zero shared meshes and zero instancers in all six.  A violation is a
   refusal.
3. **By measurement, per family, at the per-family bound.**  `top_share` over
   the item's own family, gated at **10 %** — §4.3's bound — never at the global
   40 % that provably cannot fire.  The six score 0.031 %, 0.148 %, 0.833 %,
   0.130 %, 10.000 % and 0.296 %.  `timing_stand` at exactly 1/10 is the floor
   of a ten-unit population; it is admitted by `MIN_UNITS_FOR_SHARE`, not by
   loosening the bound, because a share bound is meaningless below 1/bound
   units.

`tools/item_placement_gate.py --selftest` builds a family of 40 objects wearing
**one** mesh and requires (2) and (3) to fail on it, and a family of 40 wearing
8 meshes (top 12.5 %) and requires (3) to fail on that.  A check that has never
been shown to fail is not a check.

## 7. Provenance

Census §1.5: *"the ship carries no per-item provenance … anyone who wants those
168 resolved needs a provenance attribute written at build time, not a better
grep."*

Every placed object and its mesh carry `r2_item`, `r2_manifest_item`,
`r2_item_collection`, `r2_src_blend`, `r2_src_sha8`, `r2_gate`, `r2_stage`,
`r2_placed_utc`.  The gate treats an unstamped object in a placed collection as
a **failure**, so the stamp cannot rot into decoration.

**What this does and does not close.**  It makes every object this stage places
decidable for ever — the next census reads a custom property instead of
guessing from a name.  It does **not** retro-resolve the 168 `UNDET` rows: those
are welded inside `ARCH_PitWall`, `ARCH_Gantry`, `ARCH_PaddockBuildings` and
friends, built by the class modules, and only those modules can stamp them.  See
§9.

## 8. Running it

```bash
# the assembly path — places every row whose state is PLACE
blender -b --factory-startup -P render/world/assembly/r2/assemble.py -- \
        --out A.blend --mods surface,barriers,architecture,terrain,dressing,items

# a test build against an existing scene; --place overrides the state field
blender -b render/film14.blend --factory-startup -P world/build_items.py -- \
        --place crew_figure,timing_stand --out work/x.blend --report work/x.json

# is it actually in the blend you are about to render?  BOTH directions:
blender -b work/x.blend --factory-startup -P tools/item_placement_gate.py -- \
        --out work/x_gate.json                       # must be PLACEMENT_ITEMS_OK
blender -b render/film14.blend --factory-startup -P tools/item_placement_gate.py -- \
        --expect absent                              # must be ..._ABSENT_AS_EXPECTED_OK
blender -b --factory-startup -P tools/item_placement_gate.py -- --selftest
```

Judge on the printed `STAGE RESULT` line.  Blender 5.2 exits 0 on an uncaught
script exception and did so on this project again today.

## 9. What is owed, and to whom

* **A world rebuild** to put `crew_figure` in the ship.  `assemble.py`'s default
  `--mods` now ends in `items`; nothing moves until an assembly runs, and those
  are scheduled, not taken.
* **`build_architecture` / `build_barriers`** own every `REBUILD_OWED` line.
  Until a class module stops welding a feature, the hero module for that
  feature cannot be placed.  This is the honest form of the census's
  *"32 + 42 = 74 reworks"*.
* **The five local-frame modules** (`pont_girder`, `pont_deck_slab`,
  `gantry_truss`, `driver_figure`, `crew_fireproof_overall`) each publish
  `place=(R, t)` or a `*_to_world()`.  The registry needs a `frame: "local"`
  arm carrying that transform.  It is named here and stopped here.
* **The class-level builders** could stamp `r2_item` the same way, which is what
  it would take to resolve the census's 168 `UNDET`.  It is one line per
  emitted object and it is not this stage's to add.
