# Staged for the defect log's owner — R2-226 to R2-240

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner.  My
block is R2-226 to R2-240 and I have used six of it.  Paste or renumber as you
see fit.

All of it is one job: **building the stage between `world/items/` and
`assemble.py`**, which `docs/ITEM-PRESENCE-CENSUS.md` found did not exist and
which is why 0 of 41 item modules have ever reached a rendered frame.

Source: `world/build_items.py`, `world/build_items.md`,
`world/items/PLACEMENT.json`, `tools/item_placement_gate.py`,
`tools/item_ab_measure.py`.  Working files: `work/r2226/`.
Artefact: `render/r2226_items.blend`, 5,205,657,600 bytes — `film14` plus 130
placed item objects.

---

## R2-226 — the census read the docs for placement data; the artefacts have it

The census's handover says *"there is no placement step between `world/items/`
and `assemble.py`"* and, separately, that no item module carries placement data.
**The first is true.  The second is true of the documents and false of the
blends**, and the difference decided the whole design of the stage.

Measured out of the built test blends, `work/r2226/inventory_item.py`:

| item | objects | distinct meshes | centroid extent, WORLD metres |
|---|---:|---:|---|
| `armco_post` | 3,236 | 3,236 | x [−716.9, 552.7]  y [−256.8, 926.9] |
| `catch_fence_post` | 676 | 676 | x [−716.9, 625.8]  y [−257.2, 983.9] |
| `crew_figure` | 120 | 120 | x [−58.8, −30.1]  y [−64.3, −37.3] |
| `heras_fence_panel` | 771 | 771 | x [−109.9, 377.8]  y [−105.5, 320.0] |
| `timing_stand` | 10 | 10 | x [161.9, 317.2]  y [47.3, 177.7] |
| `tyre_wall_tyre` | 338 | 338 | x [246.6, 267.3]  y [895.6, 928.1] |

Those are circuit coordinates.  The modules import `world_contract` and resolve
every unit through `C.su_to_world(s, u)` / `C.world_ground_z(x, y)` **at build
time**; projected back onto the centreline by the new stage's own check,
`crew_figure` lands at **s 3232.6 – 3262.0, u +53.8 – +85.9 m**, the paddock
behind the pit building.

**So the missing stage is a transfer, not a placement solver.**  Every item's
position was computed by its author, through the contract every class builder
reads, and dropped on the floor at the door.  A design that had believed the
docs would have written a solver and re-derived 41 authors' work.

`assemble.py`'s `--mods` default now ends in `items`.  **A world rebuild is
owed** before anything changes in the ship.

## R2-227 — 40 of 41 modules cannot be placed today, and the reasons are four

`world/items/PLACEMENT.json`, 41 rows, each blocker naming its measurement.
One row is in state `PLACE`.  The blockers, with multiplicity:

```
SUPERSEDE_WELDED   24    the world already builds this feature, welded inside a
                         class mesh; placing it double-builds
GATE_NOT_ACCEPTED  22    canonical gate.json is not ITEM_ACCEPTED
PARTIAL_BUILD      15    the blend holds fewer units than the item declares
NOT_AN_ITEM         6    probes; their absence is correct
LOCAL_FRAME         5    builds local and publishes place=(R, t); the registry
                         has no transform arm yet
NO_BUILT_BLEND      3
DUPLICATE_MODULE    2    pit_wall_unit_itemkit, showroom_facade_panel_v2
NO_WORLD_FRAME      2    the test blend lays the population on a grid
NO_GATE_REPORT      1    spectator_standing_ga
```

**`crew_figure` is the only clean one, and why it is clean is the census's own
headline.** It supersedes nothing, because §2.5 measured that 0 of `assembly9`'s
30,183 datablock names and 0 of `film14`'s 32,069 match
`figure|person|crowd|spectat|skin|hair|human|crew|driver`, and there is no skin,
flesh or hair material among the 130 / 191.  **The one item that can be placed
without first taking something out is a human being, because there are none.**

Two rows worth naming for whoever picks this up:

* **`tyre_blanket` is the nearest next candidate** — the only row whose ONLY
  blocker is the gate verdict.  56 of 56 declared units, world frame, nothing in
  `assembly9` it would double-build.  Re-gate it ACCEPTED and it is placeable as
  it stands.
* **`spectator_crowd`'s `GATE_NOT_ACCEPTED` is reading the wrong file.**
  `spectator_crowd.py` sets `ITEM = "spectator_seated"`, so the row's verdict
  came from `render/items/spectator_seated/gate.json` (REJECTED) and not from
  `render/items/spectator_crowd/gate.json` (ACCEPTED), which exists for a
  directory that is not a manifest id — census §1.3's off-by-one.  The row is
  HOLD either way on `NO_WORLD_FRAME`, which is decisive and independent of the
  gate, and the row now says so rather than being taken as true.

## R2-228 — `tools/placement_gate.py` has R2-180's fall-through, in the gate the campaign relies on

Run on a scene holding **two** item collections it prints

    collection 'W_Item_CrewFigure' (item-campaign convention); 2 item
    collections present, took the largest -- pass --subject to be explicit

and measures crew_figure's 120 meshes as the subject while filing the ten
`TS_Stand*` objects under `context_findings`.  That is exactly R2-180 —
*"`cands = pick or cands` fell through to 'any item collection, take the
biggest'"* — in a different file, and **a placement stage makes multi-item
scenes the normal case**, so it will now fire routinely rather than never.

Worked round by running the gate once per item with `--subject`.  Both clean,
and the second run produces numbers the fall-through never reached:

```
crew_figure   PLACEMENT_CLEAN  0 violations; no subject mesh came within
                               bounding-box reach of ANY of the three volumes
timing_stand  PLACEMENT_CLEAN  0 violations
              road_corridor  3.487 m clear  TS_Stand05_GRISAILLE
              car_path       5.370 m clear  TS_Stand00_BOREAL
              camera_path   10.509 m clear  TS_Stand03_ESTIVAL
```

**And R2-110's controls were run with them, because a gate run only against the
thing you hope is clean is not a measurement:**

```
ctl_place_pos           PLACEMENT_FAIL     (must fail)
ctl_place_neg           PLACEMENT_CLEAN    (must pass)
ctl_place_nearmiss_neg  PLACEMENT_CLEAN    (must pass — over-rejection)
```

The gate is not mine to change; it is named here.

## R2-229 — the supersede debt is physical, and a counter could not have shown it

`build_items` derives its `REBUILD_OWED` lines from `assembly9_build.json`'s own
counters — `pit_wall_stands = 5`, `armco_posts = 3561`, `fence_posts = 676`.
**A counter says what was built, not where it is**, and "the old version has to
come out" is a claim about space.

`work/r2226/supersede_overlap.py` links `ARCH_PitWall` **alone** out of the
4.21 GB ship — one object through `bpy.data.libraries.load`, not a scene open —
and counts wall vertices inside each placed unit's world bounding box:

```
10 of 10 TS_Stand* units contain host geometry
4,300 of ARCH_PitWall's 24,664 vertices
worst TS_Stand09_KESTREL 2,184, best TS_Stand06_HALCYON 18
```

**A bounding box is generous.**  A stand's box runs from the ground to its
canopy and the wall passes beneath it, so this is an upper bound on
interpenetration rather than proof of it.  What it does establish is that the
hero stands and the welded ones occupy the same volume of the pit straight,
which is what makes them one feature built twice — and it is why
`timing_stand`'s state is HOLD despite being `ITEM_ACCEPTED`, complete at 10 of
10, in world frame and keep-out clean.

`catch_fence_post` is the starkest case and needs no measurement: the item
builds **676** posts and `build_barriers` reports `fence_posts = 676`.

## R2-230 — `build_items.purge()` leaked mesh datablocks, and the idempotence test is what caught it

`build()` twice in one session, on an identical 120-object scene:

```
run 1   123 objects   122 meshes   3,137,756 verts
run 2   123 objects   243 meshes   6,275,504 verts      <- before the fix
run 2   123 objects   121 meshes   3,105,356 verts      <- after
```

`purge()` removed the objects and left their meshes, and **Blender reused the
object names**, so the scene looked right — first and last object names
identical across both runs.  A second leak was in the rig-drop path: a standin
ground plane's mesh outlives its object the same way.

Blender drops zero-user datablocks on save, so this could never have reached a
shipped blend.  It matters anyway, because **the mesh counts are how the
no-repeats rule is enforced in this file** — `distinct meshes == objects`,
`users == 1`, `top_share` — and an in-session mesh count that doubles is a count
nobody can use.

Removal is scoped to what this stage placed.  It never sweeps `bpy.data` for
orphans: an orphan somebody else made is not this stage's to delete, and
*"`purge(prefix)` has no default prefix"* is a rule this project already paid
for.

## R2-231 — the placement check that did not exist, shown failing before it was trusted passing

`tools/item_placement_gate.py`.  R2-182 paid a full render cycle for the
question *is the item in the blend you are about to render?*, and the answer for
all 41 items was no.

**`--selftest`, seven families built live in-process.**  The four must-fail cases
are the point:

| case | verdict | arm |
|---|---|---|
| 40 objects / 40 meshes / stamped | `PLACED` | — |
| no collection at all | `ABSENT` | — |
| 39 of a declared 40 | `PLACED_BUT_WRONG` | `COUNT` |
| **40 objects wearing ONE mesh** | `PLACED_BUT_WRONG` | `NO_REPEATS` ×3 |
| 40 objects, 8 meshes (top 12.5 %) | `PLACED_BUT_WRONG` | `NO_REPEATS` ×3 |
| 40 objects, no provenance stamp | `PLACED_BUT_WRONG` | `PROVENANCE` |
| 4 objects, 1 mesh | `PLACED_BUT_WRONG` | `NO_REPEATS` (share not gated below 10 units; the datablock arm still fires) |

**And the strongest control cost nothing, because it was already on disk.**  The
same gate, same registry, run against the two artefacts the census measured:

```
render/film14.blend        --expect absent   crew_figure ABSENT, 1 of 1
                           >> PLACEMENT_ITEMS_ABSENT_AS_EXPECTED_OK
render/r2226_items.blend                     crew_figure  PLACED 120 objects,
                                                          120 meshes, 0 unstamped
                                             timing_stand PLACED  10 objects,
                                                           10 meshes, 0 unstamped
                           >> PLACEMENT_ITEMS_OK
```

A gate that cannot tell the shipping world from a placed one is not measuring
placement.  `tools/item_ab_measure.py` **refuses to interpret an A/B at all**
unless it is handed this gate's verdict for the AFTER blend.

---

## What is owed

1. **A world rebuild** to put `crew_figure` in the ship.  `assemble.py`'s
   default `--mods` now ends in `items`; nothing moves until an assembly runs.
2. **`build_architecture` and `build_barriers`** own every `REBUILD_OWED` line.
   Until a class module stops welding a feature, the hero module for that
   feature cannot be placed.  This is the honest, physical form of the census's
   *32 + 42 = 74 reworks*.
3. **A `frame: "local"` arm in the registry** for the five modules that build
   local and publish `place=(R, t)` / a `*_to_world()`: `pont_girder`,
   `pont_deck_slab`, `gantry_truss`, `driver_figure`, `crew_fireproof_overall`.
   Named and stopped.
4. **Per-face provenance in the class builders** — see the note below.  It is
   what would close the census's 168 `UNDET`, and the mechanism is already in
   those files.

### The provenance note, because the census asked whether it is worth it

**Object-level stamping is done and it is cheap**: every object this stage
places, and its mesh, carries `r2_item`, `r2_manifest_item`,
`r2_item_collection`, `r2_src_blend`, `r2_src_sha8`, `r2_gate`, `r2_stage`,
`r2_placed_utc`, and the gate fails an unstamped object inside a placed
collection so the stamp cannot rot into decoration.

**It does not close the 168, and it cannot.**  Those items are welded inside
`ARCH_PitWall`, `ARCH_Gantry`, `ARCH_PaddockBuildings` — *one mesh*, so no
object-level property can distinguish a coping from an advert from a timing
stand inside it.  The census asks for "a provenance attribute written at build
time"; for welded geometry that has to be a **face-domain attribute**, not a
custom property.

**It is worth building, and the reason is that the mechanism already exists in
those files.**  `build_architecture`'s `MB` accumulator already carries per-face
parallel arrays — `self.fm` material index, `self.fs` smooth flag, `self.fc`
colour — and `MB.build()` already writes them with `me.polygons.foreach_set(...)`
and `me.color_attributes.new(...)`.  `build_barriers` and `build_dressing` use
the identical `foreach_set` idiom.  A face-domain `INT` attribute keyed to an
item-id table is **`fc`'s twin**: one array beside the three that exist, one
`me.attributes.new(name="r2_item", type='INT', domain='FACE')` beside the colour
layer, and a current-item context set per *section* of the builder rather than
at each of the ~230 append sites.

That would make all 435 items decidable from the artefact for ever, and it
should be done at the next class-module change, because it needs a rebuild
anyway and one is already owed.
