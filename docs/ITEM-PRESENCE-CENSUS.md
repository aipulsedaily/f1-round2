# ITEM PRESENCE CENSUS — R2-206

**Written 2026-08-04 in answer to R2-182's open question: *how many items are
gated, tiered and scored for screen presence while being absent from the ship?*
This is an AUDIT. It places nothing, fixes nothing and rebuilds nothing.**

The ship is `render/world/assembly/r2/assembly9.blend`, per
`render/world/assembly/r2/SHIPPING.md`. The film built on it is
`render/film14.blend`, and **the two are not the same population** — §1.4 — so
every verdict below names which artefact it was read from.

> ## THE ANSWER, IN FOUR LINES
>
> 1. **All 41 item modules are absent from the ship. Not one of them — 0/41 —
>    contributes a single datablock to `assembly9.blend` or to `film14.blend`.**
>    `timing_stand` is not a special case; it is the whole set.
>    **32 of the 41 are manifest items, 31 carry a gate report, and all 435
>    manifest items carry a tiering entry and a screen-presence score.** So the
>    literal answer to R2-182's question is **31 gated + tiered + scored items
>    whose module output is absent**, and **32** if `spectator_standing_ga`
>    (module, tier and score; no `gate.json`) is counted.
> 2. **But module-absence is the smaller finding.** Read at the level of the
>    *item* rather than the module: **133 of the 435 items (30.6 %) have no
>    geometry of their class in the world OR the film** — including **17 HERO
>    and 17 MID**. **Every human figure in the film is one of them.** Across
>    `assembly9`'s 30,183 datablock names and `film14`'s 32,069, the only name
>    matching `figur|person|crowd|spectat|skin|hair|human|crew|driver` is
>    `DR_MarshalPosts`, **a post**. There is no skin, flesh or hair material
>    among the 130 / 191. **The film has 18,350 grandstand seats and nobody
>    sitting in them.**
> 3. **This is NOT the manifest's one-directional 4× overstatement mechanism.**
>    Tested, and it does not land: items **present** in the world overstate
>    **47.5 %** > 4× (median 3.95×); items **absent everywhere** overstate
>    **51.9 %** > 4× (median 4.25×). The distributions are the same shape.
>    Absence does not predict overstatement, because `screen_presence.json`
>    measures **hosts** for present and absent items alike — §4. The
>    overstatement mechanism `WAVE2-SCOPE.md` §2.1 already named (a radial
>    `nearest_camera_m` taken abeam, 63° outside the frame) is a *separate*
>    defect. **Two independent faults, not one.**
> 4. **The wave-2 count does not move; its composition does.** The 113 is
>    reproduced exactly here (HERO 71 + MID 56 = 127, minus the 14 built ones
>    that are HERO/MID = **113**). But of those 113: **42 are for things the
>    world already builds** (36 named + 6 counted) — those are reworks wearing a
>    new-module label; **29 are for things that exist nowhere at all**, 15 HERO
>    and 14 MID; **3 exist only as round-1 assets inside `film14`**; and **39
>    cannot be decided from the artefact.** And §6.2's justification for
>    demoting 216 items — *"they already exist as class-level placement
>    geometry"* — **is false for 97 of the 290 unbuilt BULK items and
>    unverifiable for 125 more.**

---

## 0. THE INSTRUMENT, AND ITS CONTROLS, BEFORE ANY VERDICT

R2-182 exists because a check returned a clean zero for the wrong reason, so
nothing below is quoted without the control that makes it a measurement.

### 0.1 Reading the artefact — `bpy.data.libraries.load`, not a scene open

`work/r2206/dump_names.py` lists every datablock name out of a 4 GB blend
without opening the scene. Run under `/opt/blender-5.2.0-linux-x64/blender`,
judged on the printed `STAGE RESULT` line and never on `$?`:

```
assembly9.blend  STAGE RESULT OK objects=28781 collections=72 meshes=1158
                 materials=130 node_groups=34   4.4 s
film14.blend     STAGE RESULT OK objects=29726 collections=77 meshes=2041
                 materials=191 node_groups=34  22.8 s
```

**28,781 reproduces `assembly9_build.json`'s own `total_objects` exactly.** That
is the first control: a reader that silently returned a partial list would not
land on the build report's number.

### 0.2 Exact-name matcher — positive and negative controls, both run every time

`work/r2206/census.py` **asserts** these and refuses to produce a table if any
fails:

| control | expected | got |
|---|---|---|
| `ARCH_PitWall` `SURF_Kerb_T4_in0` `TER_Ground` `DR_Post_01` `BR_Transit_TyreWall` `VEG_gn_grass_fescue_H` `ARCH_ShowroomSurrounds` `W_Surface` `R2_Dressing` `A_Asphalt` | all present | **10/10 present** |
| `ZZZ_NOT_A_THING_9137` `W_Item_NoSuchItemAtAll` `TS_Stand00_BOREAL` `W_Item_TimingStand` `MPD_Deck` `PDS_Deck` `ITEM_HOSPITALITY_DECK` | all absent | **7/7 absent** |
| prefix `ARCH_` `SURF_Kerb_` `DR_Tyres_` `VEG_tree` `BR_Armco_` | all > 0 | 31 / 35 / 24 / 24654 / 29 |
| prefix `TS_` `MPD_` `PWU_` `W_Item_` `ITEM_` `QQZZ_` | all 0 | **0 / 0 / 0 / 0 / 0 / 0** |

The negative-control row deliberately includes the three names R2-182 tested
(`TS_Stand…`, `W_Item_TimingStand`, `MPD_Deck`) **alongside** a string that
cannot exist, so a matcher that matched nothing would fail the positive row in
the same run.

### 0.3 The instrument that WAS wrong, recorded because it was caught

The first run of §3's host check reported **123 items whose hosts are not in
`assembly9`** — which would have contradicted `screen_presence.json`'s own
`host_patterns_matching_nothing: 0`. It was the instrument. The published JSON
**truncates long host lists with a sentinel string** `"...+81 more"`, and the
matcher was testing the sentinel for objecthood. Corrected: **0 items have a
listed host missing from `assembly9`.** Every host that file names still exists
in the current ship, so **no score is orphaned by a host that vanished.**

### 0.4 A name scan cannot see instancing or geometry nodes — so a raw binary sweep too

R2-180's detector was fooled by 41 collections of instancer empties, so the name
scan is backed by `/usr/bin/grep -oaF` over the **whole 4.21 GB** of
`assembly9.blend` and the **4.53 GB** of `film14.blend` (both saved
`compress=False`). This sees library filepaths, custom-property strings and any
literal a datablock scan would miss:

```
pattern                     assembly9   film14
ARCH_PitWall  (+ve control)         3        3     <- obj + mesh + collection
world/items/                        0        0
render/items/                       0        0
W_Item_                             0        0
ITEM_                               0        0
TS_Stand / MPD_Deck / PDS_Deck      0        0
PGD_Girders / GTR_Truss             0        0
MPC_Columns / DRV_Driver            0        0
CFO_Crew / W_HumanBench             0        0
SFP_ShowroomFacadePanel             0        0
ZZZ_NOT_A_THING_9137 (-ve control)  0        0
```

`ARCH_PitWall = 3` is not decoration: **it reproduces the datablock census
exactly** — one object, one mesh, one collection — so the sweep is resolving
real name records and not scanning past them.

**The short 3-character prefixes were also swept, and they are NOISE — measured,
not assumed.** `TS_` returns 8 hits in 4.21 GB. Random controls of the same
length in the same file return `QZ_` 28, `QV_` 14, `XJ_` 13, `KZ_` 12, `VQ_` 10,
`XQ_` 8, `JW_` 6, `ZJ_` 4 — chance for a 3-byte string in 4.21 × 10⁹ bytes is
≈ 252 × 256⁻¹ ≈ 250 for common bytes and single digits for rare ones. Dumping
28 bytes around each of the eight `TS_` hits shows all eight sitting inside
float data with no null-terminated name record. **The verdicts below rest on the
long distinctive patterns, all of which are 0 with a live positive control in
the same pass.**

---

## 1. THE CENSUS

### 1.1 The world is six class-level prefixes and nothing else

`assembly9.blend`'s 28,781 objects carry exactly **six** name prefixes, and its
72 collections, 1,158 meshes, 130 materials and 34 node groups carry the same
six. There is no seventh namespace anywhere in the file:

```
VEG 28314   DR 246   BR 131   SURF 58   ARCH 31   TER 1        = 28,781
```

That is `assembly9_build.json`'s own `object_prefixes` block, and it is
reproduced independently here by reading the blend. **`assemble.py` builds five
modules — `surface, barriers, architecture, terrain, dressing` — and none of the
five imports anything from `world/items/`.** (`build_dressing` imports
`itemkit`, which is a shader-node helper, not an item.) There is no code path by
which an item module's geometry can reach the ship.

### 1.2 All 41 item modules: absent, unanimously

Every module declares a collection name and an object prefix in its own source
header. **Not one of the 41 collections and not one of the 41 prefixes appears
in `assembly9.blend`.** §5's table gives all 41 rows; the summary is:

```
modules on disk under world/items/                       41
  whose filename IS a manifest item id                   32
  probes / derived / _v2 / itemkit (not manifest ids)      9
modules whose declared COLLECTION is in assembly9         0
modules with ANY object of their PREFIX in assembly9      0
modules with any trace in film14.blend                    0
```

The nine non-manifest modules are `human_bench`, `human_clay`,
`human_fabric_probe`, `human_peep`, `human_png`, `human_sweep`,
`pit_wall_unit_itemkit`, `showroom_facade_panel_v2`, `spectator_crowd`. Five of
those (`human_clay`, `human_fabric_probe`, `human_peep`, `human_png`,
`human_sweep`) declare **no collection and no prefix at all** — they are
tooling, and their absence is correct, not a defect. That leaves **36 modules
that emit named geometry and place none of it.**

### 1.3 What is gated, tiered and scored

```
manifest items                                          435
  with a tiering entry (docs/proposed_tiers.json)       435   (BULK 308 / MID 56 / HERO 71)
  with a screen-presence score                          435
  with a module under world/items/                       32
  with a gate report at render/items/<id>/gate.json      31
```

The two off-by-ones are real and worth naming: **`spectator_standing_ga` has a
module, a tier and a score but no `gate.json`**, and **`render/items/spectator_crowd/gate.json`
exists for a directory that is not a manifest id** (`spectator_crowd.py` sets
`ITEM = "spectator_seated"`, the record it serves). So the count of things that
are *gated and tiered and scored while their module output is absent from the
ship* is **31**, or **32** counting the module without a gate.

### 1.4 `film14` is NOT `assembly9` — it is `assembly9` plus 945 round-1 objects

This matters, because a census taken only against the ship would call things
absent that do render. The film scene is a strict superset:

```
film14.blend - assembly9.blend   945 objects   assembly9 - film14   0
new collections   CAR, SHOWROOM, PROPS, LIGHTS, WORLD_SKY
new materials     61  (LiveryPaint, CarbonFibre, GlassPanel, MullionAlu,
                       FloorPolished, TyreRubber, WheelRim, SKY_Air, …)
```

Those 945 are **round-1 assets** — the F1 car (`CAR_ROOT`, `FW_` 120,
`RW_` 97, `SW_` 65, `wheel_` 56, `halo_` 53, `brake_` 88, `MB_`, `EC_`, `FD_`,
`BB_`, `SP_`, `CI_`, `NOSE_`), the showroom (`Floor`, `Wall_BackX/SideY`,
`Ceiling`, `GW_Front_Glass_00..13`, `Cove_*`, `Spot_*`, `Vitrine_*`,
`Turntable_*`, `Platform_Dais`, `Forecourt_*`, `Bollard_*`, `Barrier_*`,
`Plaque_*`, `WallSign_*`), and the props (`ToolChest_*`, `WingTrolley_*`,
`FlightCase*`, `TyreStackA_*`, `TyreBlanket_1..3`, `PitBoard_*`, `GunRack_*`,
`HoseReel_*`).

**Three consequences.**

* **The showroom is not in the shipping world.** `build_architecture` builds
  `ARCH_ShowroomSurrounds` — the *neighbours*: a service yard, a precast wall,
  four plant boxes — and its own summary declares
  `r1_floor_interface.requires: "the assembly must composite round-1 Floor;
  without it the mouth reads as a 100 mm formation step — ground, not a hole"`.
  `assembly9` does not composite it. `film14` does. **Anything measured against
  `assembly6`/`assembly9` for a `showroom_breach` item was measured against a
  service yard.**
* **16 items exist only in the film**, as round-1 geometry — verdict `F_ONLY`
  below. Three of them are in the wave-2 113.
* **The car is not in either the world or the tiering.** `screen_presence.json`
  says so itself: *"The car is not in this scene, so it neither occludes nor is
  measured."*

### 1.5 The verdicts, and what each one rests on

| verdict | means | evidence class | n |
|---|---|---|---:|
| `W_NAMED` | a datablock in `assembly9` **is** the item | artefact: name | **94** |
| `W_COUNTED` | no name, but `assembly9_build.json` — written by the ship's own build at save time — carries a non-zero counter for it | artefact: the ship's own report | **24** |
| `F_ONLY` | absent from `assembly9`; present in `film14` as a round-1 asset | artefact: name | **16** |
| `UNDET` | the host object exists and may weld the item inside it, but `assembly9` carries **no name and no counter** | **undecidable from the artefact** | **168** |
| `ABSENT` | the item's whole **class** is absent from **both** artefacts | artefact: class-level absence | **133** |

`UNDET` is not a hedge, it is the finding: **the ship carries no per-item
provenance.** `ARCH_PitWall` is one welded mesh; nothing in the file records
which of its triangles are a coping, a padding, an advert or a timing stand. For
168 of 435 items the artefact cannot be made to answer, and no amount of care
with the matcher changes that. Anyone who wants those 168 resolved needs a
provenance attribute written at build time, not a better grep.

| verdict | HERO | MID | BULK | total |
|---|---:|---:|---:|---:|
| `W_NAMED` | 27 | 14 | 53 | 94 |
| `W_COUNTED` | 5 | 2 | 17 | 24 |
| `F_ONLY` | 2 | 3 | 11 | 16 |
| `UNDET` | 20 | 20 | 128 | 168 |
| **`ABSENT`** | **17** | **17** | **99** | **133** |

---

## 2. THE CLASSIFICATION OF THE ABSENCES

### 2.1 Never placed at all — 36 modules, 0 objects

The dominant class. Every module that emits geometry emits it into a collection
of its own naming (`W_Item_*`, `ITEM_*`, `TS_`, `MPD_`, `PDS_`, `PGD_`, `GTR_`,
`MPC_`, `SFP_`, `CFO_`, `DRV_`, …) and **nothing ever reads that collection.**
There is no placement step between `world/items/` and `assemble.py`. This is not
36 separate oversights; it is a missing pipeline stage.

### 2.2 Placed under a different name — 0

Checked, and it does not happen. If an item module's output had been placed
under a class-level name, the module's *prefix* would still have to appear
somewhere, or a mesh datablock would carry it. Both are 0. The reverse
possibility — that class-level code independently builds the same feature — is
common and is exactly what `W_NAMED` / `W_COUNTED` record: `timing_stand`'s
feature **is** in the world as `pit_wall_stands = 5` welded inside `ARCH_PitWall`
(5 built against 10 declared), built by `build_architecture`, not by
`timing_stand.py`. **That is why R2-182's before/after render would have been
identical and yet the world does contain a timing stand.** Both halves of that
sentence are true and neither on its own is the whole story.

### 2.3 Placed as an instance or via geometry nodes — checked explicitly, and no

This is the R2-180 failure mode, so it was tested three ways and not assumed:

* **All 34 node groups in `assembly9` are `VEG_gn_*`** — grass, grit, shrubs,
  weeds, stones, fern, sapling. There is no geometry-node group belonging to
  `ARCH`, `BR`, `DR` or `SURF`, so no class-level object can be generating item
  geometry procedurally at evaluation time.
* **All 72 collections are class-level** (`WORLD_TERRAIN/*`, `W_Surface`,
  `R2_Dressing`, `R2_Barriers`, `ARCH_*`, `BR_*`, `DR_*`, `VEG_*_lib`). An
  instancer empty must point at a collection; there is no collection an item
  could be hiding in.
* **Zero library references.** `world/items/` and `render/items/` return **0**
  from the raw binary sweep of both blends. Nothing is linked in from an item
  test blend.

### 2.4 Deliberately not in the world — 5 of the 41

`human_clay`, `human_fabric_probe`, `human_peep`, `human_png`, `human_sweep`
declare no collection and no prefix. They are probes and reference tooling.
Their absence is correct. `showroom_facade_panel_v2` and `pit_wall_unit_itemkit`
are second implementations of items that already have one; `human_bench` and
`spectator_crowd` are real work with no manifest row. **Nine modules total are
not manifest items; five of them should never have been expected in the world.**

### 2.5 The class that is absent from everything — 133 items

Not "unplaced" — **there is no geometry of this kind anywhere in the project's
shipping artefacts.** Four groups, each established by a class-level probe over
the union of both blends' names and materials:

| group | n | the probe |
|---|---:|---|
| **human figures** | 60 | 0 of 30,183 (a9) / 32,069 (f14) names match `figur\|person\|crowd\|spectat\|skin\|hair\|human\|crew\|driver`; the sole hit is `DR_MarshalPosts`, a post. No skin/flesh/hair material among 130 / 191. |
| **road vehicles** | 25 | 0 names match `car\|truck\|van\|ambul\|tender\|crane\|tractor\|forklift\|vehicle\|wheel\|chassis` in `assembly9`. The only counter is `transporters = 20`. `film14`'s `wheel_*` / `CAR_*` are the round-1 F1 car. |
| **surface ephemera** | 29 | 0 names match `stain\|litter\|scuff\|puddle\|oil\|chalk\|spill\|drift`; the only near-hits are the *materials* `A_RustSteel` and `A_Soil`, which are shaders, not features. No counter. |
| **showroom-owned, module never runs** | 15 | `assemble.py MODS = surface,barriers,architecture,terrain,dressing`. `showroom` is not one of them and `car` is not one of them. No shard / spall / dust / gasket / rainwater / stud name in either blend. |
| **traffic cones** | 4 | 0 names match `cone\|bollard\|jersey` outside round-1's showroom `Bollard_*`. No counter. |

**The 60 figures are the headline.** `HUMAN-FIGURE-BRIEF.md` exists,
`crew_figure.py`, `driver_figure.py`, `paddock_personnel_figure.py`,
`spectator_seated.py`, `spectator_standing_ga.py`, `spectator_crowd.py` and
`crew_fireproof_overall.py` exist and are gated — and **the world the film
renders contains not one human being.** `marshal_figure_standing` is scored
**HERO at 551.8 px**; its host is `DR_MarshalPosts`, and what is at that spot is
a post with no marshal on it.

### 2.6 World features nobody declared

The census also runs the other way. `assembly9` builds things **no manifest item
claims**, so they have no module, no gate, no tier and no score:
`VEG_grit_chip` / `VEG_grit_clod` / `VEG_grit_stone` (`grit_pieces = 1,617,615`),
`VEG_stone_pebble`, `VEG_tree_snag` (1,498 dead trees — `tree_dead_standing`
claims the species but not the count), `BR_Subbase_L/R`, `SURF_ApronJoint`
(`apron_joint_quads = 2,432`), `ARCH_Ground_Compound`. Searching the 435 ids for
`grit`, `clod`, `pebble`, `subbase`, `apron_joint`, `compound`, `snag` returns
**zero manifest items for any of them.** The 1.6 M grit pieces are the largest
single population in the world and the campaign has never had a row for them.

---

## 3. THE EFFECT ON THE WAVE-2 SCOPE

### 3.1 The 113 is reproduced exactly, and it does not move

Recomputed here from `docs/screen_presence.json` and the module list, without
reading `WAVE2-SCOPE.md`'s arithmetic:

```
HERO 71 + MID 56                                          127
  minus HERO/MID items that already have a module        - 14
  ------------------------------------------------------------
  NEW ITEM MODULES                                        113
```

The 14 are `access_road_slab`, `armco_post`, `catch_fence_post`, `crew_figure`,
`driver_figure`, `heras_fence_panel`, `marshal_post_column`, `mullion_intact`,
`paddock_personnel_figure`, `pont_girder`, `showroom_facade_panel`,
`spectator_seated`, `spectator_standing_ga`, `tyre_wall_tyre`. **The number is
right. Nothing in this census moves it.**

### 3.2 What the 113 is actually made of

| the 113, by what is in the ship | HERO | MID | total |
|---|---:|---:|---:|
| `W_NAMED` — the world already builds this thing, by name | 26 | 10 | **36** |
| `W_COUNTED` — the world builds it, counted not named | 5 | 1 | **6** |
| `UNDET` — host exists, artefact cannot say | 19 | 20 | **39** |
| `F_ONLY` — exists only as a round-1 asset in `film14` | 1 | 2 | **3** |
| **`ABSENT`** — **exists nowhere** | **15** | **14** | **29** |

**42 of the 113 are reworks wearing a new-module label.** `catch_fence_post`
would be a "new module" for a thing the world already ships as
`BR_FenceStruct_*`, 27 objects, `fence_posts = 676`. That is not an argument
against building it — the point of the campaign is to replace class-level
approximations with hero geometry — but it is a *different job* from the 29,
with a different risk: **a module for an item the world already builds must be
integrated against existing geometry, and the moment it is placed the old
version has to come out.** `WAVE2-SCOPE.md`'s ledger has one line for "already
built (rework, not new build) − 32"; the honest figure for *rework against
existing world geometry* is **32 + 42 = 74**.

**The 29 that exist nowhere, in full, biggest first:**

```
HERO  breach_dust_column        2160.0    HERO  jersey_barrier            480.4
HERO  showroom_rainwater_goods  1017.1    MID   ambulance                 459.8
HERO  mullion_bent_stub          847.6    MID   puddle                    444.7
HERO  forklift_truck             693.7    MID   recovery_tractor          424.4
MID   recovery_crane_truck       565.9    HERO  marshal_figure_seated     409.9
HERO  marshal_overall            551.8    HERO  traffic_cone              400.3
HERO  marshal_figure_standing    551.8    HERO  pallet_truck              378.4
HERO  photographer_figure        551.8    MID   marshal_figure_flagging   309.5
HERO  steward_figure             551.8    MID   spectator_standing_in_row 278.7
MID   fire_tender                530.5    MID   spectator_standing_at_rail 278.7
HERO  log_pile                   511.0    MID   spectator_with_phone      231.0
HERO  breach_dust_ground_burst   508.6    MID   hi_vis_tabard             220.7
HERO  wall_stud_framing          508.6    MID   crowd_density_field       199.1
                                          MID   crowd_idle_motion         199.1
                                          MID   spectator_seated_leaning  183.2
                                          MID   driver_race_suit          173.4
```

**13 of the 29 are people.** Seven more are road vehicles. Five are
showroom-breach items whose owning module never runs. **Their screen-presence
scores are measurements of the ground and the grandstands they would stand on**
— see §4 — so the pixel figures above are the least trustworthy in the whole
selection, and they are the ones that put those items in the wave.

### 3.3 The number that DOES move: §6.2

`WAVE2-SCOPE.md` §6.2 demotes 216 items to a class-level pass on the grounds
that *"they already exist as class-level placement geometry and are addressed in
16 (module, zone) cells."* Over the 290 unbuilt BULK items that claim covers:

```
W_NAMED    43     the claim is TRUE and checkable
W_COUNTED  15     TRUE, on the ship's own counter
F_ONLY     10     exists only in film14, as a round-1 asset
UNDET     125     the claim is UNVERIFIABLE from the artefact
ABSENT     97     THE CLAIM IS FALSE — there is no class-level geometry
```

**97 items are demoted to a class-level pass over geometry that does not
exist.** A `(dressing, ephemera)` cell agent told to give `oil_stain`,
`cigarette_end` and `gaffer_tape_strip` a value-and-variation pass will find
nothing to pass over. A `(architecture, crowd)` cell told to handle
`spectator_child`, `spectator_umbrella` and `ga_picnic_group` will find 18,350
empty seats. **This is the number in `WAVE2-SCOPE.md` that this census
falsifies**, and it is larger than the 29.

---

## 4. WHAT THIS MEANS FOR `screen_presence.json`

### 4.1 The route, established — and it is the same route for present and absent items

`tools/item_presence.py` maps every one of the 435 items onto a **host set** of
world objects via the explicit table in `tools/item_hosts.py`, and gives the item
**the best moment any host surface ever has**. Both files say so in their own
prose, without being asked:

> `screen_presence.json` › `METHOD.items_are_not_objects`: *"The assembled world
> has 468 evaluated objects and 28,313 vegetation instances and **NONE of them is
> a manifest item** — 407 of the 435 items have no module yet, and the rest are
> features distributed over class-level placement geometry. Each item is mapped
> to a HOST SET … and inherits the best moment any host surface ever has. That is
> an UPPER BOUND on the item."*

> `tools/item_hosts.py`: *"'where is `truck_mud_flap`' has no exact answer and
> will not have one until the item campaign builds it. What DOES have an exact
> answer is 'where is the geometry a mud flap hangs off'."*

**So the answer to "were the scores for present items produced by the same
route?" is yes, identically. Every one of the 435 is a host measurement.** No
item in the file was ever measured as itself. `pit_wall_unit`'s 41.8 px is
`ARCH_PitWall`'s 41.8 px; `timing_stand`'s 631 px in beat 4 is `ARCH_PitWall`'s
631 px in beat 4 — and in that case the pit wall really does carry five timing
stands, so the number is a loose upper bound on a real thing.

### 4.2 Where the upper bound stops being an upper bound on anything

The host rule is defensible *when the host is what the item sits on*. It breaks
in two ways this census can name:

* **133 items whose class does not exist.** `marshal_figure_standing`'s host is
  `DR_MarshalPosts`. A figure standing on that post would indeed be no bigger
  than the post — so 551.8 px is a valid upper bound on a hypothetical marshal.
  It is **not a measurement of anything in the film**, and a reader who takes it
  as "this reads at 551 px" is reading the post.
* **The 24 `showroom_breach` items, whose hosts are the wrong objects
  entirely.** Their hosts are `ARCH_ShowroomSurrounds`, `ARCH_Paving_Forecourt`
  and `ARCH_Paving_ApronPlatform` — the service yard and the paving *outside*.
  The showroom itself is not in the world the tiering was measured against
  (`assembly6`), and is not in `assembly9` either. **`mullion_intact` at 1051 px
  and `glass_panel_prefractured` at 1013.7 px are measurements of forecourt
  paving.** Those two items *do* render — they are in `film14` as round-1
  `GW_Front_Glass_*` and `MullionAlu` — so the right numbers are obtainable, and
  the numbers on record are not them.

### 4.3 What is NOT wrong with the file, said plainly

* **No host is orphaned.** All 435 items resolve to hosts that still exist in
  `assembly9` (§0.3). `host_patterns_matching_nothing: 0` is true.
* **The a6 → a9 drift is nil for this purpose.** `SHIPPING.md` records
  `name-set symmetric difference 0` across a6 → a7 → a8 → a9, so no host has
  appeared or vanished under the tiering since it was taken.
* **The file is not lying; it is being read wrong.** It states its own
  limitation in three places. R2-182 happened because the *consumers* —
  `WAVE2-SCOPE.md`'s selection, and whoever planned a before/after render from
  the film — treated a host upper bound as an item measurement.

### 4.4 The concrete recommendation, and it is not a fix

`screen_presence.json` should carry a per-item **`in_ship`** field with this
census's verdict, so that a HERO score on an item with `ABSENT` cannot be quoted
without the qualifier travelling with it. **That is a change to a measurement
artefact and therefore a decision, not an audit finding. It is named here and
stopped here.**

---

## 5. IS THIS THE MANIFEST'S ONE-DIRECTIONAL ERROR MECHANISM? — NO

`WAVE2-SCOPE.md` §2.1 found the manifest overstates **246 of 435** items by more
than 4× and understates **exactly 0**, and called that the signature of a
mechanism. The brief for this census asked whether item-absence is that
mechanism. **Tested, and it is not.** If absence were driving the overstatement,
absent items would overstate and present ones would not:

| presence verdict | n | median `manifest_px / measured` | share > 4× |
|---|---:|---:|---:|
| `W_NAMED` — in the world, by name | 94 | **3.83×** | 46.8 % |
| `W_COUNTED` — in the world, counted | 24 | 5.05× | 50.0 % |
| `F_ONLY` — round-1 asset in the film | 16 | 7.40× | 75.0 % |
| `UNDET` | 168 | 5.52× | 64.9 % |
| **`ABSENT` — nowhere at all** | **133** | **4.25×** | **51.9 %** |
| all 435 | 435 | 5.42× | 56.6 % (246) |

Collapsed to the one comparison that decides it:

```
PRESENT in the world (W_NAMED + W_COUNTED)   n=118   median 3.95x   47.5 % > 4x
ABSENT everywhere                            n=133   median 4.25x   51.9 % > 4x
understating items, either group                                     0
```

**The two distributions are the same shape.** A 4.4-point difference in the
> 4× share across 251 items is not a mechanism; it is the same error applied to
both. And that is exactly what §4.1 predicts: the manifest and the measurement
are compared **through the host** in both cases, so whether the item itself
exists never enters the arithmetic.

**The mechanism `WAVE2-SCOPE.md` already named is the mechanism** — a radial
`nearest_camera_m` taken at closest approach, which for anything the camera
passes is abeam and 63° outside a 35 mm frame. **This census finds a second,
independent defect that happens to share the same consumers.** Fixing one will
not move the other, and a repair that claims to fix both should be disbelieved.

---

## 6. WHAT I COULD NOT CONFIRM

1. **168 items are `UNDET` and no instrument available can resolve them.** The
   world is welded: `ARCH_PitWall`, `ARCH_Gantry`, `ARCH_PaddockBuildings` are
   single meshes with no per-feature attribute. For these the artefact is silent
   and I have refused to guess. Resolving them needs a provenance attribute
   written at build time.
2. **`W_COUNTED` trusts a counter, not geometry.** `transporters = 20` is the
   ship's own report that 20 transporters were built; I have not verified 20
   trucks are in the mesh. `SHIPPING.md` itself warns twice that *"a summary that
   does not change is not evidence that geometry did not move"* — the same
   caution applies to a summary that says something was built.
3. **The `F_ONLY` mapping is judgement, not measurement.** `GW_Front_Glass_*`
   is the showroom glass wall; whether it is *prefractured* as
   `glass_panel_prefractured` requires cannot be read from a name. Four loose
   candidates were rejected during this audit for exactly that reason —
   `truck_tyre → wheel_tyre_*_Tyre` (that is the F1 car's tyre),
   `media_pen_structure → Vitrine_*`, `garage_tyre_allocation → TyreStackA_*`,
   `pit_lane_bollard → Bollard_*` (round-1's forecourt bollards). `wing_rack →
   WingTrolley_*` is kept but flagged as arguable.
4. **I did not re-run the tiering against `assembly9`.** The scores quoted
   throughout are the on-record ones measured against `assembly6`. §4.3 argues
   the drift is immaterial *for host existence*; it says nothing about whether
   peak pixel sizes moved.
5. **Not tested: whether any item module's geometry reaches a render by a route
   other than a `.blend` datablock** — an at-render-time import, a driver, a
   handler. Both blends were swept for `world/items/` and `render/items/` as
   literal strings and both return 0, which covers a linked library and a stored
   filepath, but not a script that imports at runtime. `tools/build_film_scene.py`
   is out of scope for this audit under the brief's hard constraint 7.

---

## 7. WHAT NEEDS PLACING — NAMED, AND STOPPED

Under the brief's hard constraint 3, this audit places nothing. The decisions it
hands over, in the order the numbers rank them:

1. **There is no pipeline stage between `world/items/` and `assemble.py`.**
   36 modules emit named geometry into collections nothing reads. Until that
   stage exists, every future item module joins the same set.
2. **60 human figures are absent from a film with 18,350 grandstand seats, a
   pit lane and a paddock.** Seven figure modules are built and gated.
3. **The 97 `ABSENT` items inside §6.2's 216** cannot receive a class-level
   pass, because there is nothing to pass over.
4. **The showroom is in `film14` and not in `assembly9`.** Every
   `showroom_breach` measurement on record was taken against the world without
   it.
5. **`screen_presence.json` should carry the `in_ship` verdict per item**, so a
   score for something that does not exist cannot be quoted bare.

---

## 8. PER-MODULE TABLE — all 41

| module | declares collection | prefix | manifest item | gate report | collection in `assembly9` | objects with prefix in `assembly9` |
|---|---|---|---|:-:|:-:|---:|
| `access_road_slab.py` | `W_Item_AccessRoadSlab` | `ARS_` | `access_road_slab` | Y | **NO** | **0** |
| `armco_post.py` | `W_Item_ArmcoPost` | `AP_` | `armco_post` | Y | **NO** | **0** |
| `armco_w_beam.py` | `W_Item_ArmcoWBeam` | `AWB_` | `armco_w_beam` | Y | **NO** | **0** |
| `asphalt_wearing_course.py` | `W_Item_AsphaltWearingCourse` | `AWC_` | `asphalt_wearing_course` | Y | **NO** | **0** |
| `catch_fence_post.py` | `W_Item_CatchFencePost` | `CFP_` | `catch_fence_post` | Y | **NO** | **0** |
| `crew_figure.py` | `W_Item_CrewFigure` | `CRF_` | `crew_figure` | Y | **NO** | **0** |
| `crew_fireproof_overall.py` | `CFO_Crew` | `CFO_` | `crew_fireproof_overall` | Y | **NO** | **0** |
| `dais_delivery_ramp.py` | `W_Item_DaisDeliveryRamp` | `DDR_` | `dais_delivery_ramp` | Y | **NO** | **0** |
| `driver_figure.py` | `DRV_Driver` | `DRV_` | `driver_figure` | Y | **NO** | **0** |
| `forecourt_paving_bay.py` | `W_Item_ForecourtPavingBay` | `FCP_` | `forecourt_paving_bay` | Y | **NO** | **0** |
| `gantry_truss.py` | `GTR_Truss` | `GTR_` | `gantry_truss` | Y | **NO** | **0** |
| `grandstand_riser_unit.py` | `W_Item_GrandstandRiserUnit` | `GRU_` | `grandstand_riser_unit` | Y | **NO** | **0** |
| `gravel_bed_surface.py` | `W_Item_GravelBedSurface` | `GBS_` | `gravel_bed_surface` | Y | **NO** | **0** |
| `heras_fence_panel.py` | `W_Item_HerasFencePanel` | `HFP_` | `heras_fence_panel` | Y | **NO** | **0** |
| `hospitality_deck.py` | `ITEM_HOSPITALITY_DECK` | `HD_` | `hospitality_deck` | Y | **NO** | **0** |
| `human_bench.py` | `W_HumanBench` | `HB_` | — *(not a manifest id)* | — | **NO** | **0** |
| `human_clay.py` | `-` | `-` | — *(not a manifest id)* | — | **n/a** | **n/a** |
| `human_fabric_probe.py` | `-` | `-` | — *(not a manifest id)* | — | **n/a** | **n/a** |
| `human_peep.py` | `-` | `-` | — *(not a manifest id)* | — | **n/a** | **n/a** |
| `human_png.py` | `-` | `-` | — *(not a manifest id)* | — | **n/a** | **n/a** |
| `human_sweep.py` | `-` | `-` | — *(not a manifest id)* | — | **n/a** | **n/a** |
| `kerb_precast_unit.py` | `W_Item_KerbPrecastUnit` | `KPU_` | `kerb_precast_unit` | Y | **NO** | **0** |
| `marshal_post_column.py` | `MPC_Columns` | `MPC_` | `marshal_post_column` | Y | **NO** | **0** |
| `marshal_post_deck.py` | `ITEM_MARSHAL_POST_DECK` | `MPD_` | `marshal_post_deck` | Y | **NO** | **0** |
| `mullion_intact.py` | `W_Item_MullionIntact` | `MUL_` | `mullion_intact` | Y | **NO** | **0** |
| `paddock_paving_bay.py` | `W_Item_PaddockPavingBay` | `PPB_` | `paddock_paving_bay` | Y | **NO** | **0** |
| `paddock_personnel_figure.py` | `W_Item_PaddockPersonnelFigure` | `PPF_` | `paddock_personnel_figure` | Y | **NO** | **0** |
| `pit_wall_unit.py` | `W_Item_PitWallUnit` | `PWU_` | `pit_wall_unit` | Y | **NO** | **0** |
| `pit_wall_unit_itemkit.py` | `W_Item_PitWallUnit` | `PWU_` | `pit_wall_unit` | — | **NO** | **0** |
| `pont_deck_slab.py` | `PDS_Deck` | `PDS_` | `pont_deck_slab` | Y | **NO** | **0** |
| `pont_girder.py` | `PGD_Girders` | `PGD_` | `pont_girder` | Y | **NO** | **0** |
| `showroom_facade_panel.py` | `SFP_ShowroomFacadePanel` | `SFP_Panel_` | `showroom_facade_panel` | Y | **NO** | **0** |
| `showroom_facade_panel_v2.py` | `ITEM_SHOWROOM_FACADE_PANEL` | `SFP_` | `showroom_facade_panel` | — | **NO** | **0** |
| `spectator_crowd.py` | `ITEM_spectator_crowd` | `SPECX_` | `spectator_seated` | Y | **NO** | **0** |
| `spectator_seated.py` | `ITEM_spectator_seated` | `SPECSEAT_` | `spectator_seated` | Y | **NO** | **0** |
| `spectator_standing_ga.py` | `ITEM_spectator_standing_ga` | `GAX_` | `spectator_standing_ga` | — | **NO** | **0** |
| `team_truck_trailer.py` | `W_Item_TeamTruckTrailer` | `TTT_` | `team_truck_trailer` | Y | **NO** | **0** |
| `terrain_ground.py` | `ITEM_TERRAIN_GROUND` | `TG_` | `terrain_ground` | Y | **NO** | **0** |
| `timing_stand.py` | `W_Item_TimingStand` | `TS_` | `timing_stand` | Y | **NO** | **0** |
| `tyre_blanket.py` | `W_Item_TyreBlanket` | `TBK_` | `tyre_blanket` | Y | **NO** | **0** |
| `tyre_wall_tyre.py` | `W_Item_TyreWallTyre` | `TWT_` | `tyre_wall_tyre` | Y | **NO** | **0** |
*(`n/a` = the module declares no collection or no prefix; the five `human_*`
probes declare neither and are tooling, not items.)*

---

## 9. PER-ITEM TABLE — all 435

`module?` = a file `world/items/<id>.py` exists. `gate?` = `render/items/<id>/gate.json` exists.
Every row has a tiering entry and a screen-presence score, so those columns are omitted.
`in assembly9?` is the §1.5 verdict.

| item | zone | owning module | tier | peak sharp px | module? | gate? | in `assembly9`? | evidence |
|---|---|---|---|---:|:-:|:-:|---|---|
| `armco_post` | barriers | barriers | MID | 244.0 | Y | Y | **W_COUNTED** | armco_posts=3561 |
| `armco_reflector` | barriers | barriers | BULK | 9.8 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `armco_spacer_block` | barriers | barriers | BULK | 32.5 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `armco_splice_bolt` | barriers | barriers | BULK | 8.1 |  |  | **W_COUNTED** | bolts=4675 |
| `armco_terminal` | barriers | barriers | BULK | 162.7 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `armco_w_beam` | barriers | barriers | BULK | 50.4 | Y | Y | **W_NAMED** | BR_Armco_L00..R16  29 obj; counter armco_panels=1781 |
| `barrier_cable_conduit` | barriers | dressing | BULK | 25.2 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `barrier_foot_kerb` | barriers | barriers | BULK | 47.3 |  |  | **W_NAMED** | DR_Kerb_* 28 obj + collection DR_KerbDetail |
| `barrier_junction_box` | barriers | dressing | BULK | 94.6 |  |  | **W_COUNTED** | junction_boxes=65 |
| `catch_fence_base_collar` | barriers | barriers | BULK | 32.3 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `catch_fence_cranked_head` | barriers | barriers | BULK | 145.5 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `catch_fence_mesh_panel` | barriers | barriers | HERO | 582.1 |  |  | **W_NAMED** | BR_FenceMesh_* 27 obj; counter fence_spans=655.0 |
| `catch_fence_post` | barriers | barriers | HERO | 970.2 | Y | Y | **W_NAMED** | BR_FenceStruct_* 27 obj; counter fence_posts=676 |
| `catch_fence_woven_wire` | barriers | barriers | BULK | 0.8 |  |  | **W_NAMED** | BR_FenceWire_R; counter hero_wires=2080 |
| `concrete_barrier_block` | barriers | barriers | BULK | 34.3 |  |  | **W_NAMED** | BR_Concrete_L00/L12/L13; counter concrete_blocks=113 |
| `concrete_lifting_eye` | barriers | barriers | BULK | 2.1 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `gate_latch_hardware` | barriers | barriers | BULK | 47.3 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_access_gate` | barriers | barriers | HERO | 599.1 |  |  | **W_COUNTED** | gates=28 |
| `tecpro_anchor` | barriers | barriers | BULK | 23.6 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tecpro_block_blue` | barriers | barriers | BULK | 141.6 |  |  | **W_NAMED** | BR_TecPro_* 8 obj; counter tecpro_blocks=5540 |
| `tecpro_block_red` | barriers | barriers | BULK | 78.6 |  |  | **W_NAMED** | BR_TecPro_* 8 obj; counter tecpro_blocks=5540 |
| `tecpro_strap` | barriers | barriers | BULK | 12.6 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_wall_belt_facing` | barriers | barriers | HERO | 378.4 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_wall_bolt_plate` | barriers | barriers | BULK | 37.8 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_wall_through_rod` | barriers | barriers | BULK | 6.3 |  |  | **UNDET** | host BR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_wall_tyre` | barriers | barriers | MID | 208.1 | Y | Y | **W_NAMED** | BR_TyreWall_T4 + BR_Transit_TyreWall; counter tyres=2255 |
| `pont_abutment` | bridges | architecture | HERO | 718.5 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_banner` | bridges | dressing | BULK | 215.5 |  |  | **W_NAMED** | DR_BridgeBanners; counter bridge_banners=4 |
| `pont_bearing_pad` | bridges | architecture | BULK | 44.9 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_deck_slab` | bridges | architecture | BULK | 3.7 | Y | Y | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_girder` | bridges | architecture | MID | 242.5 | Y | Y | **W_NAMED** | ARCH_PontPlongee; counter bridges=2 |
| `pont_parapet` | bridges | architecture | BULK | 197.6 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_scupper` | bridges | architecture | BULK | 53.9 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_service_duct` | bridges | architecture | BULK | 26.9 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `pont_soffit_panel` | bridges | architecture | BULK | 62.9 |  |  | **UNDET** | host ARCH_PontPlongee exists; assembly9 carries NO name and NO counter for this feature |
| `big_screen` | crowd | architecture | MID | 229.9 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `big_screen_tower` | crowd | architecture | MID | 328.4 |  |  | **W_NAMED** | ARCH_Grandstand_Towers |
| `crowd_banner_draped` | crowd | dressing | MID | 175.2 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `crowd_density_field` | crowd | architecture | MID | 199.1 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crowd_flag_handheld` | crowd | dressing | BULK | 95.6 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crowd_idle_motion` | crowd | architecture | MID | 199.1 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crowd_litter_drift` | crowd | dressing | BULK | 15.9 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `food_concession_unit` | crowd | architecture | HERO | 477.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `ga_picnic_group` | crowd | architecture | BULK | 95.6 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `ga_terrace_step` | crowd | terrain | BULK | 39.8 |  |  | **W_COUNTED** | terrace_bays=918, terrace_depth_m=1.85 |
| `ga_viewing_bank` | crowd | terrain | HERO | 955.7 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `merchandise_stall` | crowd | architecture | HERO | 477.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `passerelle_crowd_at_parapet` | crowd | architecture | BULK | 82.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `pedestrian_crowd_barrier` | crowd | architecture | MID | 175.2 |  |  | **F_ONLY** | film14 SHOWROOM Barrier_Post_0..7 + Barrier_Rail_* |
| `podium_backdrop` | crowd | dressing | BULK | 131.4 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `podium_structure` | crowd | architecture | BULK | 114.9 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `portable_toilet_block` | crowd | architecture | HERO | 366.3 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `spectator_backpack_coolbox` | crowd | architecture | BULK | 71.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_bag_and_coat` | crowd | architecture | BULK | 63.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_child` | crowd | architecture | BULK | 151.3 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_clothing` | crowd | architecture | BULK | 111.5 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_ear_defenders` | crowd | architecture | BULK | 31.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_entrance_gate` | crowd | architecture | HERO | 382.3 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `spectator_folding_stool` | crowd | architecture | BULK | 135.4 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_headwear` | crowd | architecture | BULK | 25.5 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_seated` | crowd | architecture | MID | 199.1 | Y | Y | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_seated_leaning` | crowd | architecture | MID | 183.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_standing_at_rail` | crowd | architecture | MID | 278.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_standing_ga` | crowd | architecture | MID | 278.7 | Y |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_standing_in_row` | crowd | architecture | MID | 278.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_umbrella` | crowd | architecture | BULK | 143.3 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `spectator_with_phone` | crowd | architecture | MID | 231.0 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `timing_tower` | crowd | architecture | HERO | 656.8 |  |  | **W_NAMED** | ARCH_Grandstand_Towers |
| `absorbent_granule_residue` | ephemera | dressing | BULK | 148.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `cable_tie_offcut` | ephemera | dressing | BULK | 16.8 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `chalk_mark` | ephemera | dressing | BULK | 29.6 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `cigarette_end` | ephemera | dressing | BULK | 11.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `crushed_can` | ephemera | dressing | BULK | 56.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `discarded_bottle` | ephemera | dressing | BULK | 134.3 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `dust_drift` | ephemera | surface | BULK | 5.6 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `footprint_in_gravel` | ephemera | barriers | BULK | 111.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `fuel_spill_stain` | ephemera | dressing | BULK | 185.3 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `gaffer_tape_strip` | ephemera | dressing | BULK | 18.5 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `grass_clipping_drift` | ephemera | terrain | BULK | 66.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `litter_paper_scrap` | ephemera | dressing | BULK | 67.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `oil_stain` | ephemera | dressing | BULK | 222.4 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `puddle` | ephemera | terrain | MID | 444.7 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `rust_streak` | ephemera | barriers | BULK | 84.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `scuff_mark_barrier` | ephemera | barriers | BULK | 28.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `grandstand_banner` | grandstand | dressing | BULK | 65.7 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_block_letter` | grandstand | dressing | BULK | 39.4 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_bracing` | grandstand | architecture | BULK | 6.6 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_camera_platform` | grandstand | architecture | BULK | 32.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_cladding` | grandstand | architecture | BULK | 32.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_column` | grandstand | architecture | HERO | 426.9 |  |  | **W_NAMED** | ARCH_Grandstand_00..05 + Terrace + Towers  8 obj |
| `grandstand_concourse` | grandstand | architecture | BULK | 11.0 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_debris_fence` | grandstand | barriers | BULK | 118.2 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_front_rail` | grandstand | architecture | BULK | 36.1 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_gutter` | grandstand | architecture | BULK | 9.9 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_handrail` | grandstand | architecture | BULK | 32.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_litter_bin` | grandstand | architecture | BULK | 32.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_nosing` | grandstand | architecture | BULK | 1.6 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_riser_unit` | grandstand | architecture | BULK | 13.8 | Y | Y | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_roof_sheet` | grandstand | architecture | BULK | 1.6 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_roof_truss` | grandstand | architecture | BULK | 52.5 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_row_letter` | grandstand | architecture | BULK | 2.0 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_seat` | grandstand | architecture | BULK | 14.8 |  |  | **W_COUNTED** | grandstand_seats=18350 |
| `grandstand_seat_bracket` | grandstand | architecture | BULK | 3.9 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_skirt` | grandstand | architecture | BULK | 60.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_stair` | grandstand | architecture | BULK | 29.6 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grandstand_tower` | grandstand | architecture | HERO | 525.5 |  |  | **W_NAMED** | ARCH_Grandstand_Towers |
| `grandstand_vomitory` | grandstand | architecture | BULK | 78.8 |  |  | **UNDET** | host ARCH_Grandstand_* exists; assembly9 carries NO name and NO counter for this feature |
| `grid_box_marking` | kerbs_markings | surface | BULK | 17.2 |  |  | **W_NAMED** | ARCH_Markings + ARCH_RoadMarkings; counter marking_faces=3081 |
| `grid_numeral` | kerbs_markings | surface | BULK | 3.3 |  |  | **W_NAMED** | SURF_GridNum_01..20; counter grid_numerals=20 == 20 declared |
| `kerb_bedding_joint` | kerbs_markings | surface | BULK | 3.1 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `kerb_end_ramp` | kerbs_markings | surface | BULK | 11.7 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `kerb_hero_t4` | kerbs_markings | surface | BULK | 11.3 |  |  | **W_NAMED** | SURF_Kerb_T4_in0/out1/out2 |
| `kerb_negative_trough` | kerbs_markings | surface | BULK | 9.4 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `kerb_precast_unit` | kerbs_markings | surface | BULK | 11.7 | Y | Y | **W_NAMED** | SURF_Kerb_* 35 runs; counter kerb_runs=35 |
| `pit_exit_blend_line` | kerbs_markings | surface | BULK | 0.7 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `pit_exit_gore` | kerbs_markings | surface | BULK | 2.0 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `start_finish_line` | kerbs_markings | surface | BULK | 11.4 |  |  | **W_NAMED** | ARCH_Markings + ARCH_RoadMarkings; counter marking_faces=3081 |
| `verge_green_paint` | kerbs_markings | surface | BULK | 70.2 |  |  | **UNDET** | host SURF_Kerb_* / ARCH_Markings exists; assembly9 carries NO name and NO counter for this feature |
| `white_line_edge` | kerbs_markings | surface | BULK | 0.7 |  |  | **W_NAMED** | ARCH_Markings + ARCH_RoadMarkings; counter marking_faces=3081 |
| `awning_leg` | paddock | architecture | HERO | 945.9 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `bin_liner` | paddock | architecture | BULK | 94.6 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `cable_reel_drum` | paddock | architecture | MID | 315.3 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `catering_counter` | paddock | architecture | MID | 346.8 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `finger_post_sign` | paddock | architecture | HERO | 819.8 |  |  | **W_COUNTED** | ground_finger_posts=8 |
| `fire_point_station` | paddock | architecture | HERO | 473.0 |  |  | **W_COUNTED** | ground_fire_points=4 |
| `flight_case` | paddock | architecture | MID | 283.8 |  |  | **F_ONLY** | film14 PROPS FlightCase0/1_*  17 obj |
| `folding_chair` | paddock | architecture | MID | 268.0 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `folding_table` | paddock | architecture | MID | 236.5 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `forklift_truck` | paddock | architecture | HERO | 693.7 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `fuel_drum` | paddock | architecture | MID | 277.5 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `gas_bottle` | paddock | architecture | HERO | 441.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `gas_bottle_cage` | paddock | architecture | HERO | 599.1 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `generator_unit` | paddock | architecture | HERO | 504.5 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `hospitality_awning` | paddock | architecture | BULK | 127.8 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `hospitality_building` | paddock | architecture | BULK | 276.8 |  |  | **W_NAMED** | ARCH_PaddockBuildings |
| `hospitality_deck` | paddock | architecture | BULK | 25.6 | Y | Y | **W_NAMED** | ARCH_Ground_Decks; counter ground_decks=5, ground_deck_seats=38 |
| `jerry_can` | paddock | architecture | BULK | 148.2 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `lighting_mast` | paddock | architecture | HERO | 2160.0 |  |  | **W_COUNTED** | ground_light_masts=11 |
| `lighting_mast_head` | paddock | architecture | MID | 189.2 |  |  | **W_COUNTED** | ground_light_masts=11 |
| `media_centre_building` | paddock | architecture | HERO | 798.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `medical_centre_building` | paddock | architecture | HERO | 627.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `motorhome_unit` | paddock | architecture | BULK | 178.9 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `paddock_avenue_tree` | paddock | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_avenue_*  24 obj |
| `paddock_duct_cover` | paddock | architecture | BULK | 126.1 |  |  | **W_NAMED** | ARCH_Ground_Furniture; counter ground_furniture_groups=182 |
| `paddock_gate` | paddock | architecture | HERO | 693.7 |  |  | **W_NAMED** | ARCH_Ground_Compound |
| `paddock_manhole_cover` | paddock | architecture | MID | 189.2 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `paddock_paving_bay` | paddock | architecture | BULK | 107.8 | Y | Y | **W_NAMED** | ARCH_Paving_Paddock; counter paving_bays=5491 |
| `paddock_planter` | paddock | architecture | MID | 283.8 |  |  | **W_NAMED** | ARCH_Ground_Planting; counters ground_planters=48, forecourt_planters=10 |
| `paddock_slot_drain` | paddock | architecture | BULK | 157.7 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `pallet_stack` | paddock | architecture | HERO | 441.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `pallet_truck` | paddock | architecture | HERO | 378.4 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `parasol` | paddock | architecture | HERO | 819.8 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `planter_shrub` | paddock | terrain | MID | 340.7 |  |  | **W_NAMED** | ARCH_Ground_Planting; counters ground_planters=48, forecourt_planters=10 |
| `power_distribution_board` | paddock | architecture | MID | 346.8 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `race_control_building` | paddock | architecture | BULK | 85.3 |  |  | **W_NAMED** | ARCH_RaceControl |
| `skip_container` | paddock | architecture | HERO | 409.9 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `team_truck_tractor` | paddock | architecture | BULK | 166.1 |  |  | **W_COUNTED** | transporters=20 |
| `team_truck_trailer` | paddock | architecture | BULK | 170.3 | Y | Y | **W_COUNTED** | transporters=20 |
| `trash_can` | paddock | architecture | MID | 299.5 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `truck_air_line_coil` | paddock | architecture | BULK | 21.3 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_landing_leg` | paddock | architecture | BULK | 46.8 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_light_cluster` | paddock | architecture | BULK | 8.5 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_livery_decal` | paddock | architecture | BULK | 85.2 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_loading_ramp` | paddock | architecture | BULK | 4.3 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_mirror_arm` | paddock | architecture | BULK | 21.3 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_mud_flap` | paddock | architecture | BULK | 23.4 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_rear_door` | paddock | architecture | BULK | 153.3 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_side_skirt` | paddock | architecture | BULK | 38.3 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_tyre` | paddock | architecture | BULK | 44.7 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_wheel_steer` | paddock | architecture | BULK | 44.7 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `truck_wheel_trailer` | paddock | architecture | BULK | 44.7 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `water_bottle` | paddock | architecture | BULK | 75.7 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `water_bottle_crate` | paddock | architecture | BULK | 110.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `water_tank_ibc` | paddock | architecture | HERO | 378.4 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `wheelie_bin` | paddock | architecture | MID | 346.8 |  |  | **UNDET** | host ARCH_Paving_Paddock exists; assembly9 carries NO name and NO counter for this feature |
| `crew_figure` | people | architecture | HERO | 551.8 | Y | Y | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_headset` | people | architecture | BULK | 69.4 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `driver_boots_and_feet` | people | car | BULK | 63.1 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `driver_figure` | people | car | MID | 220.7 | Y | Y | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `driver_gloves` | people | car | BULK | 75.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `driver_helmet` | people | car | BULK | 88.3 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `driver_race_suit` | people | car | MID | 173.4 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `hi_vis_tabard` | people | dressing | MID | 220.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `marshal_figure_seated` | people | dressing | HERO | 409.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `marshal_figure_standing` | people | dressing | HERO | 551.8 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `marshal_overall` | people | dressing | HERO | 551.8 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `paddock_personnel_figure` | people | architecture | HERO | 551.8 | Y | Y | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `photographer_figure` | people | dressing | HERO | 551.8 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `photographer_rig` | people | dressing | BULK | 110.4 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `steward_figure` | people | architecture | HERO | 551.8 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `garage_awning` | pit_building | architecture | BULK | 6.2 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_bay_number` | pit_building | dressing | BULK | 12.3 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_door_concertina` | pit_building | architecture | BULK | 138.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_door_guide_rail` | pit_building | architecture | BULK | 147.9 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_door_overhead` | pit_building | architecture | BULK | 138.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_door_roller` | pit_building | architecture | BULK | 138.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_door_sectional` | pit_building | architecture | BULK | 138.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_facade_panel` | pit_building | architecture | BULK | 61.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_interior_floor` | pit_building | architecture | BULK | 4.9 |  |  | **W_NAMED** | ARCH_Paving_Garages; counter garages=14 |
| `garage_light_batten` | pit_building | architecture | BULK | 3.7 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_pier` | pit_building | architecture | BULK | 147.9 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `garage_rear_door` | pit_building | architecture | BULK | 67.8 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `pit_building_balustrade` | pit_building | architecture | BULK | 33.9 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `pit_building_roof_deck` | pit_building | architecture | BULK | 9.2 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `pit_building_soffit` | pit_building | architecture | BULK | 18.5 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `pit_building_stair_core` | pit_building | architecture | MID | 369.6 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `pit_building_west_gable` | pit_building | architecture | MID | 369.6 |  |  | **W_NAMED** | ARCH_PitBuilding_Shell + ARCH_PitBuilding_Detail |
| `pit_building_window_band` | pit_building | architecture | BULK | 55.4 |  |  | **UNDET** | host ARCH_PitBuilding_* exists; assembly9 carries NO name and NO counter for this feature |
| `air_hose_reel` | pit_lane | architecture | BULK | 20.9 |  |  | **F_ONLY** | film14 PROPS HoseReel_Drum/Hose/Stand |
| `air_line_drop` | pit_lane | architecture | BULK | 104.4 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `bodywork_trolley` | pit_lane | architecture | BULK | 45.2 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `crew_engineer_at_monitor` | pit_lane | architecture | BULK | 59.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_fireproof_overall` | pit_lane | architecture | BULK | 60.9 | Y | Y | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_front_wing_adjuster` | pit_lane | architecture | BULK | 41.8 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_garage_technician` | pit_lane | architecture | BULK | 60.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_gloves_and_boots` | pit_lane | architecture | BULK | 10.4 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_headset_full` | pit_lane | architecture | BULK | 7.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_helmet_visor` | pit_lane | architecture | BULK | 9.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_jack_operator_front` | pit_lane | architecture | BULK | 55.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_jack_operator_rear` | pit_lane | architecture | BULK | 55.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_kneeling_pad` | pit_lane | architecture | BULK | 2.1 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_mechanic_kneeling` | pit_lane | architecture | BULK | 40.0 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_mechanic_standing` | pit_lane | architecture | BULK | 60.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_pitlane_fire_marshal` | pit_lane | architecture | BULK | 60.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_radio_beltpack` | pit_lane | architecture | BULK | 4.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_release_operator` | pit_lane | architecture | BULK | 62.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_stabiliser` | pit_lane | architecture | BULK | 52.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_starter_operator` | pit_lane | architecture | BULK | 45.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_tyre_carrier_off` | pit_lane | architecture | BULK | 52.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_tyre_carrier_on` | pit_lane | architecture | BULK | 52.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_visor_cleaner` | pit_lane | architecture | BULK | 62.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `crew_wheel_gunner` | pit_lane | architecture | BULK | 48.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `engine_starter_trolley` | pit_lane | architecture | BULK | 27.8 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `engineer_on_timing_stand` | pit_lane | architecture | BULK | 52.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `fire_extinguisher_handheld` | pit_lane | dressing | BULK | 20.9 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `fire_extinguisher_wheeled` | pit_lane | architecture | BULK | 41.8 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_ceiling_gantry` | pit_lane | architecture | BULK | 12.3 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_curtain_divider` | pit_lane | architecture | BULK | 123.2 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_engineering_desk` | pit_lane | architecture | BULK | 23.1 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_spare_car_covered` | pit_lane | architecture | BULK | 33.9 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_team_signage` | pit_lane | dressing | BULK | 24.6 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_toolboard` | pit_lane | architecture | BULK | 61.6 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `garage_tyre_allocation` | pit_lane | architecture | BULK | 49.3 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `media_camera_operator` | pit_lane | architecture | BULK | 60.9 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `media_pen_structure` | pit_lane | architecture | BULK | 83.5 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `medical_car` | pit_lane | architecture | BULK | 52.2 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `monitor_bank_trolley` | pit_lane | architecture | BULK | 55.7 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `pit_box_marking` | pit_lane | architecture | BULK | 19.8 |  |  | **W_NAMED** | ARCH_Markings + ARCH_RoadMarkings; counter marking_faces=3081 |
| `pit_jack_front` | pit_lane | architecture | BULK | 12.2 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `pit_jack_rear` | pit_lane | architecture | BULK | 13.9 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `pit_lane_bollard` | pit_lane | architecture | BULK | 31.3 |  |  | **ABSENT** | NO CONE GEOMETRY: 0 of 30,183 a9 and 0 of 32,069 f14 names match cone|bollard|jersey outside the round-1 showroom Bollard_*; no counter. |
| `pit_lane_light_panel` | pit_lane | dressing | BULK | 17.4 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `pit_lane_speed_line` | pit_lane | architecture | BULK | 1.0 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `pit_lane_surface` | pit_lane | architecture | BULK | 6.1 |  |  | **W_NAMED** | ARCH_Paving_PitLane |
| `press_photographer_pitwall` | pit_lane | dressing | BULK | 55.7 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `safety_car` | pit_lane | architecture | BULK | 50.5 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `safety_car_light_bar` | pit_lane | architecture | BULK | 5.6 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `stop_go_board` | pit_lane | dressing | BULK | 17.4 |  |  | **UNDET** | host ARCH_Paving_PitLane / ARCH_Paving_Garages exists; assembly9 carries NO name and NO counter for this feature |
| `team_principal_figure` | pit_lane | architecture | BULK | 59.2 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `tool_chest` | pit_lane | architecture | BULK | 36.5 |  |  | **F_ONLY** | film14 PROPS ToolChest_*  13 obj |
| `tyre_blanket` | pit_lane | architecture | BULK | 23.7 | Y | Y | **F_ONLY** | film14 PROPS TyreBlanket_1..3 + TyreStrap + TyreBuckle |
| `tyre_blanket_controller` | pit_lane | architecture | BULK | 5.2 |  |  | **F_ONLY** | film14 PROPS TyreCtrl_Body/Face/Lead |
| `tyre_trolley` | pit_lane | architecture | BULK | 45.2 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `wheel_gun` | pit_lane | architecture | BULK | 19.1 |  |  | **F_ONLY** | film14 PROPS GunRack_Gun0..3 + Line0..3 |
| `wheel_gun_hose` | pit_lane | architecture | BULK | 1.0 |  |  | **F_ONLY** | film14 PROPS GunRack_Gun0..3 + Line0..3 |
| `wing_rack` | pit_lane | architecture | BULK | 55.7 |  |  | **F_ONLY** | film14 PROPS WingTrolley_*  11 obj (trolley; same item as a wing RACK is arguable) |
| `flagpole` | pit_straight | dressing | BULK | 110.4 |  |  | **W_NAMED** | DR_Flagpoles; counter flagpoles=12 |
| `gantry_fascia` | pit_straight | dressing | BULK | 98.0 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `gantry_ladder` | pit_straight | architecture | MID | 653.3 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `gantry_leg` | pit_straight | architecture | MID | 735.0 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `gantry_soffit_panel` | pit_straight | architecture | BULK | 20.4 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `gantry_truss` | pit_straight | architecture | BULK | 98.0 | Y | Y | **W_NAMED** | ARCH_Gantry (one welded object); counter gantry_soffit_z=9.0 |
| `gantry_tv_pod` | pit_straight | dressing | BULK | 40.8 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `gantry_walkway` | pit_straight | architecture | BULK | 89.8 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `la_passerelle_banner` | pit_straight | dressing | BULK | 66.2 |  |  | **W_NAMED** | DR_BridgeBanners; counter bridge_banners=4 |
| `la_passerelle_deck` | pit_straight | architecture | BULK | 21.3 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `la_passerelle_mesh` | pit_straight | architecture | BULK | 113.5 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `la_passerelle_stair` | pit_straight | architecture | MID | 354.6 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `la_passerelle_tower` | pit_straight | architecture | MID | 425.5 |  |  | **W_NAMED** | ARCH_Grandstand_Towers |
| `la_passerelle_truss` | pit_straight | architecture | BULK | 144.2 |  |  | **W_NAMED** | ARCH_LaPasserelle |
| `pa_horn_speaker` | pit_straight | dressing | BULK | 28.0 |  |  | **W_NAMED** | DR_Speaker_* 14 obj; counter pa_speakers=14 == 14 declared |
| `pit_board` | pit_straight | dressing | BULK | 41.8 |  |  | **F_ONLY** | film14 PROPS PitBoard_Face/Num/Pole/... |
| `pit_wall_advert` | pit_straight | dressing | BULK | 21.6 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `pit_wall_coping` | pit_straight | architecture | BULK | 3.5 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `pit_wall_padding` | pit_straight | architecture | BULK | 27.8 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `pit_wall_terminal` | pit_straight | architecture | BULK | 41.8 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `pit_wall_unit` | pit_straight | architecture | BULK | 41.8 | Y | Y | **W_NAMED** | ARCH_PitWall (collection+obj+mesh) |
| `sponsor_flag` | pit_straight | dressing | BULK | 18.4 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `start_light_backing` | pit_straight | dressing | BULK | 106.2 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `start_light_panel` | pit_straight | dressing | BULK | 89.8 |  |  | **UNDET** | host ARCH_PitWall / ARCH_Gantry / ARCH_LaPasserelle exists; assembly9 carries NO name and NO counter for this feature |
| `timing_stand` | pit_straight | architecture | BULK | 111.4 | Y | Y | **W_COUNTED** | pit_wall_stands=5 inside ARCH_PitWall (5 built, 10 declared) |
| `timing_stand_canopy` | pit_straight | architecture | BULK | 7.0 |  |  | **W_COUNTED** | pit_wall_stands=5 inside ARCH_PitWall (5 built, 10 declared) |
| `timing_stand_monitor` | pit_straight | architecture | BULK | 12.2 |  |  | **W_COUNTED** | pit_wall_stands=5 inside ARCH_PitWall (5 built, 10 declared) |
| `timing_stand_seat` | pit_straight | architecture | BULK | 31.3 |  |  | **W_COUNTED** | pit_wall_stands=5 inside ARCH_PitWall (5 built, 10 declared) |
| `windsock` | pit_straight | dressing | BULK | 29.4 |  |  | **W_COUNTED** | windsocks=3 == 3 declared |
| `bare_soil_scar` | runoff | terrain | BULK | 10.3 |  |  | **W_COUNTED** | grit_pieces=1617615 -> VEG_grit_chip/clod/stone |
| `grass_runoff_turf` | runoff | terrain | BULK | 12.2 |  |  | **W_COUNTED** | grass_in_corridor=1386383, grass_hero_clumps=1662591 |
| `gravel_bed_surface` | runoff | barriers | BULK | 10.4 | Y | Y | **W_NAMED** | BR_Trap_* 19 obj + BR_Gravel; counter trap_area_m2=36888 |
| `gravel_rake_furrow` | runoff | barriers | BULK | 5.1 |  |  | **W_NAMED** | material A_Gravel + BR_Gravel collection |
| `gravel_retaining_kerb` | runoff | barriers | BULK | 31.3 |  |  | **UNDET** | host BR_Runoff_* / BR_Trap_* exists; assembly9 carries NO name and NO counter for this feature |
| `gravel_stone` | runoff | barriers | BULK | 6.3 |  |  | **W_NAMED** | BR_Stones_apex_L/outer_R 5 obj; counter stones=240000 |
| `runoff_asphalt_mat` | runoff | barriers | BULK | 4.2 |  |  | **W_NAMED** | BR_Runoff_L/R + BR_RunoffAsphalt; counter runoff_area_m2=41117 |
| `runoff_edge_lip` | runoff | barriers | BULK | 9.4 |  |  | **W_NAMED** | ARCH_RetainEdge; counter retain_edge_m=351.8 |
| `runoff_sponsor_paint` | runoff | dressing | BULK | 38.7 |  |  | **W_NAMED** | DR_Paint_* 5 obj; counter painted_logos=5 |
| `verge_gully_grate` | runoff | dressing | BULK | 203.7 |  |  | **W_COUNTED** | gullies=46 |
| `verge_swale` | runoff | terrain | BULK | 138.5 |  |  | **W_NAMED** | BR_Verge_L/R + material BR_Verge |
| `breach_dust_column` | showroom_breach | showroom | HERO | 2160.0 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `breach_dust_ground_burst` | showroom_breach | showroom | HERO | 508.6 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `concrete_spall_debris` | showroom_breach | showroom | BULK | 13.6 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `curtain_wall_head_extrusion` | showroom_breach | showroom | BULK | 37.3 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `curtain_wall_sill_extrusion` | showroom_breach | showroom | BULK | 42.4 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `curtain_wall_transom` | showroom_breach | showroom | BULK | 27.1 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `dais_deck` | showroom_breach | showroom | BULK | 57.6 |  |  | **F_ONLY** | film14 Platform_Dais + Turntable_Deck (SHOWROOM) |
| `dais_delivery_ramp` | showroom_breach | showroom | BULK | 57.6 | Y | Y | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `exterior_ground_apron` | showroom_breach | showroom | BULK | 370.6 |  |  | **W_NAMED** | ARCH_Paving_ApronPlatform; counter apron_platform_m2=6421.2 |
| `floor_shard_scatter` | showroom_breach | showroom | BULK | 6.8 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `forecourt_bollard` | showroom_breach | showroom | HERO | 503.7 |  |  | **W_COUNTED** | forecourt_bollards=6 |
| `forecourt_paving_bay` | showroom_breach | showroom | BULK | 370.6 | Y | Y | **W_NAMED** | ARCH_Paving_Forecourt; counter forecourt_formation_m2=681.5 |
| `glass_panel_prefractured` | showroom_breach | showroom | HERO | 1013.7 |  |  | **F_ONLY** | film14 GW_Front_Glass_00..13 (14 panels), material GlassPanel |
| `glass_shard` | showroom_breach | showroom | BULK | 42.4 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `glass_shard_fan_settled` | showroom_breach | showroom | BULK | 10.6 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `glazing_gasket_set` | showroom_breach | showroom | BULK | 3.4 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `mullion_bent_stub` | showroom_breach | showroom | HERO | 847.6 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `mullion_intact` | showroom_breach | showroom | HERO | 1051.0 | Y | Y | **F_ONLY** | film14 material MullionAlu welded into the GW_ glass wall |
| `showroom_facade_panel` | showroom_breach | showroom | MID | 203.4 | Y | Y | **F_ONLY** | film14 Wall_BackX/SideY + FluteHi/FluteLo, materials WallBackX/WallSideY |
| `showroom_floor_slab` | showroom_breach | showroom | BULK | 10.2 |  |  | **F_ONLY** | film14 Floor, Floor_BayNumber, Floor_PitBox, material FloorPolished |
| `showroom_parapet_coping` | showroom_breach | showroom | BULK | 33.9 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `showroom_rainwater_goods` | showroom_breach | showroom | HERO | 1017.1 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `showroom_signage_lettering` | showroom_breach | showroom | BULK | 101.7 |  |  | **F_ONLY** | film14 WallSign_Rule/Strap/Word + Plaque_* |
| `wall_stud_framing` | showroom_breach | showroom | HERO | 508.6 |  |  | **ABSENT** | owning module `showroom` NEVER RUNS: assemble.py MODS = surface,barriers,architecture,terrain,dressing. No shard/spall/dust/gasket/rainwater/stud name in a9 or f14. build_architecture's own summary declares `r1_floor_interface.requires: the assembly must composite round-1 Floor`; assembly9 does not, film14 does -- but only Floor/Wall/GW_, not these. |
| `asphalt_crack_seal` | track_surface | surface | BULK | 1.1 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `asphalt_patch_repair` | track_surface | surface | BULK | 42.8 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `asphalt_paver_mat_joint` | track_surface | surface | BULK | 0.9 |  |  | **W_NAMED** | SURF_ApronJoint + M_Surf_Joint; counter apron_joint_quads=2432 |
| `asphalt_transverse_joint` | track_surface | surface | BULK | 0.6 |  |  | **UNDET** | host SURF_Track exists; assembly9 carries NO name and NO counter for this feature |
| `asphalt_wearing_course` | track_surface | surface | BULK | 3.3 | Y | Y | **W_NAMED** | SURF_Track + M_Surf_Asphalt; counter road_quads=516664 |
| `bridge_expansion_joint` | track_surface | surface | BULK | 10.8 |  |  | **UNDET** | host SURF_Track exists; assembly9 carries NO name and NO counter for this feature |
| `launch_rubber_stripe` | track_surface | surface | BULK | 5.7 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `lockup_skid_mark` | track_surface | surface | BULK | 8.6 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `marble_drift_bank` | track_surface | surface | BULK | 11.4 |  |  | **W_COUNTED** | gravel_spray=122 -> VEG_stone_spray |
| `rubber_line_deposit` | track_surface | surface | BULK | 57.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `timing_loop_sawcut` | track_surface | surface | BULK | 0.6 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `track_drain_slot` | track_surface | surface | BULK | 66.1 |  |  | **UNDET** | host SURF_Track exists; assembly9 carries NO name and NO counter for this feature |
| `track_gully_lid` | track_surface | surface | BULK | 82.6 |  |  | **UNDET** | host SURF_Track exists; assembly9 carries NO name and NO counter for this feature |
| `track_manhole_cover` | track_surface | surface | BULK | 99.1 |  |  | **UNDET** | host SURF_Track exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_marble` | track_surface | surface | BULK | 2.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `advertising_board` | trackside | dressing | BULK | 107.6 |  |  | **W_NAMED** | DR_Ad_000..045  46 obj; counter ad_boards_barrier=515 |
| `ambulance` | trackside | architecture | MID | 459.8 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `apex_sponsor_board` | trackside | dressing | BULK | 94.2 |  |  | **W_NAMED** | DR_Apex_* 11 obj; counter apex_boards=16 |
| `catch_fence_banner` | trackside | dressing | MID | 226.4 |  |  | **W_NAMED** | DR_Ban_* 34 obj; counter ad_banners_fence=128 |
| `corner_name_plate` | trackside | dressing | BULK | 70.7 |  |  | **W_COUNTED** | corner_signs=15 |
| `corner_number_plate` | trackside | dressing | BULK | 141.5 |  |  | **W_COUNTED** | corner_signs=15 |
| `distance_marker_board` | trackside | dressing | BULK | 212.2 |  |  | **W_NAMED** | DR_Marker_* 14 obj; counter distance_boards=24 |
| `fire_tender` | trackside | architecture | MID | 530.5 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `free_standing_hoarding` | trackside | dressing | MID | 430.4 |  |  | **W_NAMED** | DR_Billboard_00..08  9 obj; counter billboards=9 |
| `hoarding_leg` | trackside | dressing | MID | 269.0 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `info_gate_sign` | trackside | dressing | BULK | 176.8 |  |  | **W_NAMED** | DR_Sign_* 22 obj; counter info_signs=16 |
| `marshal_absorbent_bin` | trackside | dressing | BULK | 123.8 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_broom` | trackside | dressing | MID | 247.6 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_chair` | trackside | dressing | BULK | 150.3 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_figure_flagging` | trackside | dressing | MID | 309.5 |  |  | **ABSENT** | NO FIGURE GEOMETRY IN EITHER BLEND: 0 of 30,183 (a9) / 32,069 (f14) names match figur|person|crowd|spectat|skin|hair|human|crew|driver; only DR_MarshalPosts, a post. No skin/flesh/hair material among 130 / 191. |
| `marshal_flag` | trackside | dressing | BULK | 132.6 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_flag_rack` | trackside | dressing | BULK | 176.8 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_light_panel` | trackside | dressing | BULK | 88.4 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_column` | trackside | dressing | MID | 162.1 | Y | Y | **W_NAMED** | DR_Post_01..24 + collection DR_MarshalPosts; counter marshal_posts=24 |
| `marshal_post_deck` | trackside | dressing | BULK | 52.1 | Y | Y | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_handrail` | trackside | dressing | BULK | 57.9 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_roof` | trackside | dressing | BULK | 5.8 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_screen` | trackside | dressing | BULK | 104.2 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_sign` | trackside | dressing | BULK | 20.3 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_post_stair` | trackside | dressing | BULK | 92.6 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_telephone` | trackside | dressing | BULK | 70.7 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `marshal_water_cooler` | trackside | dressing | BULK | 194.5 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `recovery_crane_truck` | trackside | architecture | MID | 565.9 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `recovery_tractor` | trackside | architecture | MID | 424.4 |  |  | **ABSENT** | NO ROAD-VEHICLE GEOMETRY: 0 of 30,183 a9 names match car|truck|van|ambul|tender|crane|tractor|forklift|vehicle|wheel|chassis; the only counter is transporters=20 (claimed by team_truck_trailer/tractor). film14's wheel_*/CAR_* are the round-1 F1 car. |
| `tv_camera_body` | trackside | dressing | BULK | 11.7 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tv_camera_cable` | trackside | dressing | BULK | 1.6 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tv_camera_housing` | trackside | dressing | BULK | 17.6 |  |  | **W_NAMED** | DR_TVCam_* 13 obj; counter tv_cameras=13 |
| `tv_camera_mast` | trackside | dressing | MID | 171.8 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tv_camera_platform` | trackside | dressing | BULK | 39.0 |  |  | **UNDET** | host DR_* exists; assembly9 carries NO name and NO counter for this feature |
| `tyre_stack_trackside` | trackside | dressing | BULK | 106.2 |  |  | **W_NAMED** | DR_Tyres_* 24 obj; counter tyre_stacks=119 |
| `access_road_gully` | transit_corridor | architecture | MID | 320.3 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `access_road_kerb` | transit_corridor | architecture | BULK | 80.1 |  |  | **W_NAMED** | ARCH_Ground_ServiceRoad; counter ground_road_segments=234 |
| `access_road_saw_joint` | transit_corridor | surface | BULK | 3.8 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `access_road_slab` | transit_corridor | surface | MID | 190.9 | Y | Y | **W_NAMED** | SURF_AccessRoad; counter access_quads=35904 |
| `apron_wall_coping` | transit_corridor | barriers | BULK | 34.3 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `apron_wall_panel` | transit_corridor | barriers | MID | 514.5 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `apron_wall_weep_pipe` | transit_corridor | barriers | BULK | 12.9 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `cable_ramp` | transit_corridor | architecture | BULK | 48.0 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `cone_connector_bar` | transit_corridor | dressing | BULK | 26.7 |  |  | **ABSENT** | NO CONE GEOMETRY: 0 of 30,183 a9 and 0 of 32,069 f14 names match cone|bollard|jersey outside the round-1 showroom Bollard_*; no counter. |
| `heras_banner_scrim` | transit_corridor | dressing | HERO | 960.8 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `heras_fence_coupler` | transit_corridor | architecture | BULK | 48.0 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `heras_fence_foot` | transit_corridor | architecture | BULK | 80.1 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `heras_fence_panel` | transit_corridor | architecture | HERO | 1067.6 | Y | Y | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `jersey_barrier` | transit_corridor | architecture | HERO | 480.4 |  |  | **ABSENT** | NO CONE GEOMETRY: 0 of 30,183 a9 and 0 of 32,069 f14 names match cone|bollard|jersey outside the round-1 showroom Bollard_*; no counter. |
| `pit_exit_portal_frame` | transit_corridor | architecture | MID | 315.8 |  |  | **W_NAMED** | BR_Transit_Portal |
| `pit_exit_portal_sign` | transit_corridor | dressing | BULK | 25.3 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `portal_boom_gate` | transit_corridor | architecture | BULK | 7.6 |  |  | **UNDET** | host BR_Transit_* exists; assembly9 carries NO name and NO counter for this feature |
| `traffic_cone` | transit_corridor | dressing | HERO | 400.3 |  |  | **ABSENT** | NO CONE GEOMETRY: 0 of 30,183 a9 and 0 of 32,069 f14 names match cone|bollard|jersey outside the round-1 showroom Bollard_*; no counter. |
| `transit_debris_fence` | transit_corridor | barriers | HERO | 600.0 |  |  | **W_NAMED** | BR_Transit_Fence + BR_Transit_FenceMesh |
| `transit_tyre_wall_stack` | transit_corridor | barriers | HERO | 630.6 |  |  | **W_NAMED** | BR_Transit_TyreWall |
| `drainage_ditch` | vegetation | terrain | BULK | 95.5 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `escarpment_skyline` | vegetation | terrain | HERO | 1134.2 |  |  | **UNDET** | host VEG_* / TER_Ground exists; assembly9 carries NO name and NO counter for this feature |
| `fallen_branch` | vegetation | terrain | BULK | 85.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `farm_gate` | vegetation | terrain | BULK | 155.2 |  |  | **UNDET** | host VEG_* / TER_Ground exists; assembly9 carries NO name and NO counter for this feature |
| `fern_clump` | vegetation | terrain | MID | 298.1 |  |  | **W_NAMED** | VEG_fern + VEG_fern_*_u + gn VEG_gn_fern |
| `field_boundary_fence` | vegetation | terrain | BULK | 143.3 |  |  | **W_NAMED** | ARCH_Ground_Fences |
| `grass_clump_dry` | vegetation | terrain | BULK | 106.5 |  |  | **W_NAMED** | VEG_grass_dry_F/H + gn + material |
| `grass_clump_fescue` | vegetation | terrain | BULK | 119.2 |  |  | **W_NAMED** | VEG_grass_fescue_F/H + gn + material |
| `grass_clump_meadow` | vegetation | terrain | BULK | 149.0 |  |  | **W_NAMED** | VEG_grass_meadow_F/H + gn + material |
| `grass_clump_reed` | vegetation | terrain | HERO | 383.2 |  |  | **W_NAMED** | VEG_grass_reed_F/H + gn + material |
| `grass_clump_tussock` | vegetation | terrain | MID | 191.6 |  |  | **W_NAMED** | VEG_grass_tussock_F/H + gn + material |
| `hedgerow_section` | vegetation | terrain | HERO | 1277.5 |  |  | **W_NAMED** | VEG_hedge_*  3299 obj over 9 species |
| `leaf_litter` | vegetation | terrain | BULK | 66.2 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `log_pile` | vegetation | terrain | HERO | 511.0 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `moss_patch` | vegetation | terrain | BULK | 33.1 |  |  | **ABSENT** | NO SURFACE-EPHEMERA GEOMETRY OR COUNTER: 0 of 30,183 a9 names match stain|litter|scuff|puddle|oil|chalk|spill|drift (only materials A_RustSteel, A_Soil, which are shaders not features); no counter in assembly9_build.json. |
| `rock_boulder` | vegetation | terrain | BULK | 143.3 |  |  | **W_NAMED** | VEG_stone_boulder + VEG_gn_stone_boulder; counter stones_boulder=47 |
| `rock_scree_stone` | vegetation | terrain | BULK | 17.9 |  |  | **W_NAMED** | VEG_stone_cobble / VEG_stone_pebble; counter stones_cobble=217 |
| `shrub_bramble` | vegetation | terrain | HERO | 511.0 |  |  | **W_NAMED** | VEG_shrub_bramble_L0/L1 + gn + leaf material |
| `shrub_broom` | vegetation | terrain | HERO | 681.3 |  |  | **W_NAMED** | VEG_shrub_broom_L0/L1 + gn + leaf material |
| `shrub_gorse` | vegetation | terrain | HERO | 596.2 |  |  | **W_NAMED** | VEG_shrub_gorse_L0/L1 + gn + leaf material |
| `shrub_hazel` | vegetation | terrain | HERO | 1490.4 |  |  | **W_NAMED** | VEG_shrub_hazel_L0/L1 + gn + leaf material |
| `shrub_juniper` | vegetation | terrain | HERO | 468.4 |  |  | **W_NAMED** | VEG_shrub_juniper_L0/L1 + gn + leaf material |
| `terrain_ground` | vegetation | terrain | BULK | 5.1 | Y | Y | **W_NAMED** | TER_Ground obj + mesh + material |
| `tree_crack_willow` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_willow*  2977 obj |
| `tree_dead_standing` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_snag*  1498 obj + material VEG_bark_snag |
| `tree_hawthorn` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_hawthorn*  3164 obj |
| `tree_italian_cypress` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_cypress*  74 obj |
| `tree_lombardy_poplar` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_poplar*  1895 obj |
| `tree_london_plane` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_plane*  500 obj |
| `tree_oak` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_oak*  4609 obj |
| `tree_rowan` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_rowan*  1918 obj |
| `tree_sapling` | vegetation | terrain | HERO | 1277.5 |  |  | **W_NAMED** | VEG_sapling + VEG_tree_sapling_L*  9 obj, gn VEG_gn_sapling |
| `tree_scots_pine` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_pine*  2694 obj |
| `tree_silver_birch` | vegetation | terrain | HERO | 2160.0 |  |  | **W_NAMED** | VEG_tree_birch*  5317 obj |
| `weed_joint_colonist` | vegetation | terrain | BULK | 63.9 |  |  | **W_NAMED** | VEG_weed_{dock,nettle,plantain,ragwort,thistle,yarrow} + 6 gn |
---

## 10. WHAT TO RUN

```
work/r2206/dump_names.py      lists every datablock name out of a 4 GB blend via
                              bpy.data.libraries.load, without opening the scene.
                              Prints STAGE RESULT; judge on that, not on $?.
work/r2206/census.py          the exact-name + prefix matcher, with the positive
                              and negative controls ASSERTED every run (§0.2).
                              Writes work/r2206/census.json.
work/r2206/verdict.py         the curated per-item verdict mapping (§1.5), with
                              its evidence string per item.  Writes verdicts.json.
work/r2206/patterns.txt       the raw binary sweep pattern list, with its
work/r2206/noise.txt          random 3-character noise controls (§0.4).
work/r2206/names_assembly9.json   the 28,781 + 72 + 1,158 + 130 + 34 names.
work/r2206/names_film14.json      the 29,726 + 77 + 2,041 + 191 + 34 names.
```

Nothing in `work/r2206/` writes to `world/`, `render/`, `sim/` or any artefact
this project ships.

**`work/` is blanket-ignored by `.gitignore:27`**, so those seven files are on
disk and not in the repository — the same arrangement as `v120/`, `v123/` and
`work/r2100/`, which `SHIPPING.md` cites the same way. A search tool that
respects `.gitignore` will not find them; `/usr/bin/grep` and `ls` will.
