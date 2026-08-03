# WAVE 2 — SCOPE

**Written 2026-08-03. This document decides how big wave 2 is and what it costs.
It builds nothing.** Wave 1 was paused pending re-scope; this is that re-scope.

> **The headline, before anything else.** The wave is **not ~407 items.** It is
> **113 new item modules in 80 build units**, plus **32 rework items**, plus
> **24 interface stubs**, plus a class-level pass over **16 cells**. The other
> **266 items get no module at all**, and that is a measurement, not a budget cut:
> at their largest sharp unoccluded moment in the whole 124-second take they do
> not read. **50 of them are under 12 px and have nothing depending on them; those
> should be deleted from the campaign.**
>
> **And the 407-item wave is not merely expensive, it is impossible:** at the
> measured 1.125 GB per item it needs **453 GB against 135 GB free** (§5.5).
>
> **Three things this scoping found that change how the wave should be run:**
> compute is free and has been mis-costed — wave 1's *entire* gating campaign was
> **0.58 GPU-hours** (§5.1); the number the whole budget rests on, hours per build
> agent, **has never been measured** and the one adjacent figure that has is
> **5.5× worse than assumed** (§5.2); and the gate **false-accepts 2 of its own 5
> known-bad items**, so the peep tier cannot be cut (§5.3).

Every number below is marked **MEASURED** (I ran it, and the command is given),
**ON RECORD** (someone else measured it and the artefact is named), or
**ESTIMATE** (a model, with its assumptions and what would settle it). The
project has had nine instruments turn out to be the broken thing; the marking is
not decoration.

**Provenance of the two inputs everything here rests on:**

| input | what it is | when | measured against |
|---|---|---|---|
| `docs/item_manifest.json` | 435 items, declares what exists | 2026-07-28 | — |
| `docs/screen_presence.json` + `docs/proposed_tiers.json` | the tiering, measured | 2026-08-03T03:58:55 | **`assembly6.blend`**, sha `82cd7065…` |

**Read that second row again. The tiering was measured on `assembly6`. The
shipping world is `assembly8`.** §2.6 measures how much that matters and
concludes: not much, in a bounded and stated way — but it is not nothing and it
is cheap to redo.

---

## 1. WHAT THE ~407 ITEMS REALLY ARE

### 1.1 The count, corrected

**MEASURED** — `world/items/*.py` cross-referenced against the manifest ids:

```
manifest items                                    435
modules on disk under world/items/                 41
  of those, whose filename IS a manifest item id   32   <- the built set
  of those, that are NOT a manifest item id         9   <- human_bench, human_clay,
                                                          human_fabric_probe, human_peep,
                                                          human_png, human_sweep,
                                                          pit_wall_unit_itemkit,
                                                          showroom_facade_panel_v2,
                                                          spectator_crowd
UNBUILT manifest items                            403
```

The brief's "28-module foundation tier / ~407 remaining" is close but stale:
**it is 32 built and 403 unbuilt.** The 9 extra modules are probes, a derived
reference copy, a `_v2`, and one item (`spectator_crowd`) that is real work with
no manifest row — worth reconciling, because `spectator_crowd`'s witness is the
pair R2-121 was written to protect.

### 1.2 The census, by zone, crossed with measured presence

**MEASURED** — `docs/item_manifest.json` × `docs/screen_presence.json`:

| zone | items | HERO | MID | BULK |
|---|---:|---:|---:|---:|
| pit_lane | 58 | **0** | **0** | 58 |
| paddock | 56 | 17 | 13 | 26 |
| vegetation | 35 | 20 | 2 | 13 |
| trackside | 35 | **0** | 11 | 24 |
| crowd | 33 | 6 | 12 | 15 |
| pit_straight | 29 | **0** | 4 | 25 |
| barriers | 26 | 4 | 2 | 20 |
| showroom_breach | 24 | 8 | 1 | 15 |
| grandstand | 23 | 2 | 0 | 21 |
| transit_corridor | 20 | 6 | 4 | 10 |
| pit_building | 18 | **0** | 2 | 16 |
| ephemera | 16 | **0** | 1 | 15 |
| track_surface | 15 | **0** | **0** | 15 |
| people | 15 | 7 | 3 | 5 |
| kerbs_markings | 12 | **0** | **0** | 12 |
| runoff | 11 | **0** | **0** | 11 |
| bridges | 9 | 1 | 1 | 7 |
| **total** | **435** | **71** | **56** | **308** |

**Seven of the seventeen zones contain no HERO item at all**, and they are 195 of
the 435 — pit_lane, trackside, pit_straight, pit_building, ephemera,
track_surface, kerbs_markings, runoff. **pit_lane is the single largest zone in
the manifest at 58 items and every one of them is BULK.**

By owning world module:

| module | items | HERO | MID | BULK |
|---|---:|---:|---:|---:|
| architecture | 214 | 29 | 36 | 149 |
| dressing | 79 | 6 | 9 | 64 |
| terrain | 44 | 22 | 4 | 18 |
| barriers | 39 | 6 | 3 | 30 |
| surface | 30 | 0 | 1 | 29 |
| showroom | 24 | 8 | 1 | 15 |
| car | 5 | 0 | 2 | 3 |

`surface` owns 30 items and has **zero** heroes. Every kerb, every marking, every
asphalt feature.

### 1.3 What the items *are*, structurally

**MEASURED.** 365 of 435 declare ≥ 2 instances; 70 are singletons. Total declared
population **2,439,890**. Six items carry 2.09 M of that (`grass_clump_fescue`
500 k, `tyre_marble` 400 k, `grass_clump_meadow` 350 k, `grass_clump_tussock`
300 k, `gravel_stone` 240 k, `grass_clump_dry` 200 k). **86 % of the declared
population lives in six items.** That matters for §4.

---

## 2. WHICH ARE WORTH BUILDING — MEASURED, NOT ASSUMED

### 2.1 The manifest's `hero` flag is not usable as a selection criterion

**MEASURED**, over all 435 items:

```
manifest hero = true   343 items  ->  measured HERO  38    MID 45   BULK 260
manifest hero = false   92 items  ->  measured HERO  33    MID 11   BULK  48
```

**Only 38 of the manifest's 343 heroes measure HERO. And 33 items the manifest
calls non-hero do.** Nearly half the measured hero set (33 of 71) is invisible to
the flag entirely.

Correlation between the manifest's declared `onscreen_px_4k` and the measured
peak sharp unoccluded size:

```
Pearson  r   = 0.548
Spearman rho = 0.644
items the manifest OVERSTATES by more than 4x   246 of 435
items the manifest UNDERSTATES by more than 4x    0 of 435
```

**The error is one-directional. The manifest never undersells an item and
oversells 57 % of them by more than 4×.** That is the signature of a systematic
mechanism, not noise, and the mechanism is named in `docs/PLAN-scope-optimisation.md`
§0 and in `screen_presence.json`'s own `METHOD.frustum`: `nearest_camera_m` is a
**radial** closest approach measured **abeam**, which on a 35 mm lens is 63°
outside the frame. The manifest quotes a screen size at a moment the object is
not on screen.

Worked, on the two items the campaign brief itself uses as its examples:

| item | manifest says | measured min in-frustum depth | manifest px | measured peak **sharp unoccluded** px |
|---|---|---:|---:|---:|
| `kerb_hero_t4` | 0.8 m at 21 mm — *"2800 px/m, a 0.4 mm chip is a visible pixel"* | **8.2 m** | 210 | **11.3** |
| `showroom_floor_slab` | 0.5 m at 35 mm — *"the mirror every part is presented against"* | **9.0 m** | 448 | **10.2** |
| `pit_wall_unit` (the REFERENCE item) | 6.2 m at 35 mm | 13.2 m | 723 | **41.8** |
| `asphalt_wearing_course` | 1.1 m at 21 mm | 2.3 m | 41 | **3.3** |

`kerb_hero_t4` is the item `ITEM-CAMPAIGN-BRIEF.md` §3 uses to teach *"build to
the pixel, not to the vibe"*. **At its best moment in the film it is 11 px.**

### 2.2 The distribution — where the 435 actually sit

**MEASURED**, `peak_unocc_sharp_px_4k` (largest the item ever is while its motion
smear is ≤ 6 px of the 4K frame and it is not occluded):

```
p5   3.5      p25   25.6     p50   75.7     p75  242.5     p90  565.9     max 2160
```

| band | items | reading |
|---|---:|---|
| ≥ 1000 px | **21** | the only items in the film that genuinely receive macro scrutiny |
| 300–1000 | 74 | hero build |
| 150–300 | 53 | silhouette, mass, value, variation |
| 40–150 | 143 | mass and tone |
| 12–40 | 75 | a smudge with a correct value |
| 4–12 | **43** | **does not resolve** |
| < 4 px | **26** | **does not exist on screen** |

The 21 macro items, in full — these are the entire macro-scrutiny surface of the
film: `breach_dust_column`, `escarpment_skyline`, `glass_panel_prefractured`,
`hedgerow_section`, `heras_fence_panel`, `lighting_mast`, `mullion_intact`,
`paddock_avenue_tree`, `showroom_rainwater_goods`, `shrub_hazel`,
`tree_crack_willow`, `tree_dead_standing`, `tree_hawthorn`,
`tree_italian_cypress`, `tree_lombardy_poplar`, `tree_london_plane`, `tree_oak`,
`tree_rowan`, `tree_sapling`, `tree_scots_pine`, `tree_silver_birch`.

**Thirteen of the twenty-one are trees.** The film's macro budget is a tree
budget.

### 2.3 Nothing is invisible, and that is a real result

**MEASURED.** `frames_visible == 0` for **0 of 435** items. The minimum is 437
frames; the median 1,189. `frames_unoccluded_sharp == 0` for **0 of 435**.

So the drop argument is **not** "it never enters frame". Every item enters frame.
The argument is **size**: it enters frame and occupies 3 px.

### 2.4 The one asymmetry that makes the BULK verdicts safe to act on

`screen_presence.json`'s `METHOD.items_are_not_objects` says it plainly, and it is
the most important sentence in the file:

> Each item is mapped to a HOST SET … and **inherits the best moment any host
> surface ever has. That is an UPPER BOUND on the item: it cannot be seen better
> than what it sits on.**

The occlusion term compounds it in the same direction: `METHOD.occlusion` says
the figure is a **lower bound** on occlusion, i.e. an upper bound on visibility.

**Therefore:**

- **A BULK verdict is conservative.** "Its host's best moment is 6 px" means the
  item is *at most* 6 px. Dropping on a BULK verdict cannot be wrong in the
  direction that costs the film.
- **A HERO verdict is optimistic.** "Its host reaches 2160 px" does not mean the
  item does. **The 71-item HERO set is an over-count of unknown size**, and the
  wave should expect to demote some of it once the items exist and can be
  measured as themselves rather than as their hosts.

This asymmetry is the whole basis for §6. It means the aggressive half of the
recommendation is the safe half.

### 2.5 The refuted prediction, and what survives of it

`docs/PLAN-scope-optimisation.md` §M4 wrote its own falsifier down:

> **Prediction, so this document can be wrong in public:** M2 will return
> **between 110 and 170 HERO items**, against the manifest's 343. My model puts
> A+B at 151. **If M2 returns more than 220, §3's geometry is wrong and this plan
> should be rejected wholesale.**

**The measurement returned 71.** The chain, on record:

```
343   manifest hero flag
 91   first screen-presence pass
 75   after the R2-037 flat-180-degree shutter correction   (assembly2, contract 1.0.1)
 71   re-derived on assembly6, contract 1.2.1               (docs/proposed_tiers.json)
```

**The stated prediction band is refuted — 71 is below its 110 floor by 35 %.**
The stated *falsifier* (> 220) never fired, so the plan is not rejected: its
direction was right and its magnitude was under-called by about 40 %. The useful
lesson is the one the frustum correction already taught: **each time this was
measured rather than modelled, the answer got smaller.** A scope document should
expect that to happen once more when items are measured as themselves (§2.4), and
should not plan as though 71 is a floor.

### 2.6 The tiering is one world stale — measured, and bounded

`docs/screen_presence.json` and `docs/proposed_tiers.json` were both generated
2026-08-03T03:58:55 against **`assembly6.blend`**. `SHIPPING.md` declares
**`assembly8.blend`** (built 19:38 the same day) as the shipping world, and
`render/film12.blend` is built on it. **The tiering wave 2 is scoped from is two
promotions behind the world it is scoping.** This is blocker #91 in
`MASTER-PLAN.md` recurring one world later.

**How much it matters — ON RECORD, from the vertex fingerprints in
`render/world/assembly/r2/v122/` and `v123/`:**

```
assembly6 -> assembly7   common objects whose vertex set MOVED:  0 of 28,781
assembly7 -> assembly8   objects MOVED:                          1 of 28,781
                         the one object:  TER_Ground, z only, far field beyond
                         Dc 3,600 m, bbox z max 38.00 -> 364.46 m
```

**MEASURED** — which items host on the one object that moved: **15 of 435**. Of
those, exactly one hosts on `TER_Ground` and nothing else: **`escarpment_skyline`,
already tiered HERO at 1,134 px**. A far horizon that rose 326 m can only make it
*more* visible, so the direction of the error is safe.

**Verdict: the tiering is usable, and re-deriving it on `assembly8` is a
recommended cheap first action, not a blocker.** It is one `screen_presence.py`
sweep over an already-dumped point cloud. Do it before dispatching, so no wave-2
agent reads a number stamped against a world that is not the ship.

**Note also:** `docs/screen_presence.json` carries an
`exposure_unmeasured_2026_08_03` block withdrawing its `4_by_eye` validation arm
— eight frames rendered 3.628 stops over (R2-109). **The numeric tiering is
unaffected** (it was never read from those frames) but the tiering now stands on
three validation arms, not four. Restoring the fourth costs eight frames.

---

## 3. THE PROPOSED WAVE-2 SET AND BUILD ORDER

### 3.0 The starting position nobody should skip

**MEASURED**, `python3 tools/campaign_preflight.py --all --policy wave2`:

```
SKIP 0   BUILD 435
```

**Not one item of the 435 — including all 32 that already have a module — meets
the wave-2 contract.** Per-rule, over the 32 built items:

| rule | fails |
|---|---:|
| `macro_png_complete` | **31 / 32** |
| `macro_at_gate_resolution` | 31 / 32 |
| `gate_accepted` | 21 / 32 |
| `module_parses` | 1 / 32 (`spectator_standing_ga` defines no top-level `build()`) |
| `test_blend_readable` / `gate_report_decodes` / `gate_report_is_current` | 1 / 32 each |

**31 of the 32 built items have no `macro.png` on disk at all.** They were moved
into `_superseded_2026-08-0{2,3}_R2-061/` and never re-rendered. Deliverable 3 of
the campaign brief's four (`render/items/<id>/macro.png` at 3840 × 2160) is
currently absent for 97 % of the built corpus. `spectator_seated` is the only
item that has one.

**Wave 2 therefore starts with a rework tier, not a build tier.** Any plan that
dispatches 113 new agents before closing this is building a second floor on an
unfinished first.

### 3.1 The tiers

| tier | what | items | build units | rationale |
|---|---|---:|---:|---|
| **W2-0** | re-derive the tiering on `assembly8`; re-render the 8 exposure frames | — | 1 | §2.6. Nothing downstream should read an `assembly6` number once `assembly8` is the ship. Cheap, serial, first. |
| **W2-R** | **rework the 32 built items** | 32 | ~8 | §3.0. Re-render 31 macros at 4K; re-gate all 32 on a fresh witness (§7.4); re-read 20 verdicts off the printed line (§7.2). No new geometry unless the re-read says so. |
| **W2-A** | **unbuilt measured HERO** | **66** | **45** | ≥ 300 px sharp on ≥ 24 frames. Full hero build: material history, geometry that resolves, per-instance variation, macro. |
| **W2-B** | **unbuilt measured MID** | **47** | **35** | ≥ 150 px on ≥ 12 frames. Silhouette, mass, correct value, genuine variation. **No macro history** — nothing on these is ever inspected above 300 px. |
| **W2-C** | **BULK items with ≥ 2 dependants** | **24** | 0 modules | §3.3. **Interface stubs, not modules.** |
| **W2-D** | remaining BULK | 266 | 16 cells | §3.4. Class-level pass in the owning world module. No per-item module. |
| | **new item modules** | **113** | **80** | |

Build units are the `(module, name-family)` collapse already computed in
`docs/proposed_tiers.json` — one agent owns a family and emits its children,
because the parent already owns the children's material history. Restricted to
the unbuilt set: **HERO 66 items → 45 groups; MID 47 items → 35 groups.** Group
sizes are mostly 1 (36 of 45 HERO groups, 29 of 35 MID); the collapse's value is
concentrated in a handful of big families (one HERO group of 11, one of 5).

### 3.2 Build order, and why

1. **W2-0** — serial, one agent, before anything is dispatched.
2. **W2-R** — the 32 built items, because everything else inherits their
   interfaces and because §3.0 says the foundation is not actually laid.
   `spectator_seated` alone has **8 dependants** and is currently
   `ITEM_UNMEASURABLE` (§7.2).
3. **W2-A vegetation first — 20 of the 66.** Thirteen of the film's 21
   macro-scrutiny items are trees and every one of them is unbuilt HERO. They are
   also the largest single variety risk (§4) and the largest instance
   populations. If any part of this wave deserves the *"a month is acceptable"*
   budget, it is here.
4. **W2-A remainder — 46**, ordered by measured px descending.
5. **W2-B — 47**, after W2-A, because MID items are frequently children of HERO
   families and get most of their material history from the parent.
6. **W2-C** stubs can run in parallel with anything; they are contract files.
7. **W2-D** last, and only after a frame-peep says the class-level pass is what
   those 266 items actually need.

**The sequencing rule from `MASTER-PLAN.md` applies at every step:** a change to
`itemkit.py` or `world_contract.py` invalidates every blend built before it
(§7.3 measures this at **31 of 32**). Freeze both for the duration of a tranche,
or pay for the rebuild twice.

### 3.3 W2-C — why 24 BULK items still need *something*

**MEASURED.** 24 unbuilt BULK items are depended on by ≥ 2 other items. They are
BULK — they do not read — but a dependant needs their dimensions, their brand,
their material family. Examples: `pit_lane_surface` (6 px, 2 dependants),
`garage_interior_floor` (5 px, 2), `safety_car_light_bar` (6 px, 2),
`runoff_asphalt_mat` (4 px, 2), `tecpro_block_blue` (142 px, 3),
`la_passerelle_truss` (144 px, 3).

**They should ship an `<id>_interface.json` and nothing else.** A hero module for
a 5 px floor that exists only so another item can read its z is exactly the work
this document exists to remove. This converts 24 modules into 24 contract files.

### 3.4 W2-D — the 266, and what they already are

`screen_presence.json`'s own limitation note: *"People, crowd and 407 of the 435
items are NOT BUILT. Their host is the ground or structure they will stand on."*
For the BULK tier that is the point — **these items already exist as class-level
placement geometry** in `build_architecture`, `build_dressing`, `build_terrain`,
`build_surface` and `build_barriers`. What they need is a silhouette/value/
variation pass on that geometry, not 266 new modules. `docs/proposed_tiers.json`
collapses them to **36 `(module, zone)` cells, 16 of which are ≥ 6 items and get
an agent; 20 small cells roll into their module owner.** Largest cells:
architecture×pit_lane 53, architecture×paddock 26, dressing×trackside 24,
barriers×barriers 18, architecture×grandstand 18.

---

## 4. HOW THE VARIETY RED LINE KEEPS HOLDING

> *"i dont want repeat stuff aka one tree spammed 100 times everything has to be
> thought out no matter what"*

### 4.1 Where the world stands, and what the number does *not* cover

**ON RECORD**, `render/world/assembly/r2/v122/variety_distribution_v122.json`
(assembly7, sha `97d0a530…`):

```
realized instances 4,689,798      distinct source meshes 311
n_eff (Simpson)          89.09    n_eff (Shannon) 113.04
top source share          1.99 %  top-10 share 43.63 %   gini 0.7222
```

**MEASURED, and this is the part that changes the plan:** the file's
`by_first_token` table has **exactly one family — `VEG`.** All 311 sources are
vegetation. `distinct_emitters` is 34, every one a vegetation scatter host.

**So the celebrated 311 / 89.1 / 1.99 % says nothing whatever about the item
campaign.** It is a statement about grass. Not one manifest item has ever been
measured by the world-level variety instrument, because no manifest item is
currently instanced into the assembled world.

### 4.2 The world-level spam check cannot fire, and here is the arithmetic

`tools/instance_variety.py` declares `SPAM_TOP_SHARE = 0.40` — a family is spam
when its commonest mesh is ≥ 40 % of it. **MEASURED**, against the post-wave
population (4,689,798 world + 2,439,890 declared = 7,129,688):

| item | declared | if built entirely on ONE mesh | verdict of the global check |
|---|---:|---:|---|
| `grass_clump_fescue` | 500,000 | **7.01 %** of the world | **PASS** |
| `tyre_marble` | 400,000 | 5.61 % | PASS |
| `grass_clump_meadow` | 350,000 | 4.91 % | PASS |

**The single largest item in the manifest, built as literally one mesh spammed
half a million times, does not trip the world's spam check.** The check is
measured against a denominator dominated by 4.7 M grass instances, and no
individual item can reach 40 % of that. The named failure the user drew a red
line around is invisible to the instrument that carries its name.

At the *gate's own floor* it is worse, because the gate permits 25 % on the
commonest source: `grass_clump_fescue` shipping 40 sources with 125,000
instances on the commonest is **1.75 %** of the world — indistinguishable, on the
global number, from today's healthiest source.

### 4.3 What actually holds the line, and the four rules wave 2 runs under

The line is held by exactly two things, and neither is the global figure:

- **`item_gate` check 4, per item.** `distinct_sources` counts *source geometry*,
  so one mesh instanced 7,800 times scores **1** however wildly the transforms are
  randomised. Requirement `max(8, min(40, sqrt(n)))` sources, commonest ≤ 25 %.
- **`variety_distribution.py`'s per-family arm** — `by_first_token` /
  `by_two_tokens`. It exists, it is correct, and **it has never had a non-VEG
  family to report on.**

**MEASURED**, the per-item requirement over the 365 multi-instance items:
225 items need only the floor of 8 sources; **55 items need the ceiling of 40**.
If every multi-instance item ships exactly the minimum, the world gains **5,654
source meshes** against today's 311 — an 18× expansion of the world's geometry
vocabulary. For the proposed wave-2 HERO+MID set alone: 99 multi-instance items,
472,059 declared instances, **+1,585 sources minimum**.

**The four rules:**

1. **Per-family, never global.** Every wave-2 acceptance runs
   `variety_distribution.py` and reads the **family** row for the item's prefix,
   not `global`. A family's top_share is bounded at **10 %**, not 40 % — chosen
   because the world's healthiest family today runs at 1.99 % and the gate's
   per-item ceiling of 25 % is 12.6× looser than that. State the number in the
   tool so it can be argued with; do not leave the wave protected by a threshold
   that provably cannot fire.
2. **The 25 % per-item ceiling is a floor on effort, not the target.** An item
   that lands at 24 % passed the gate and failed the brief. Report the achieved
   top_share in every item's hand-back and treat anything above 10 % as a
   finding.
3. **The six big-population items are their own tier.** 86 % of the declared
   population lives in `grass_clump_fescue`, `tyre_marble`, `grass_clump_meadow`,
   `grass_clump_tussock`, `gravel_stone`, `grass_clump_dry`. Every one is
   BULK-or-MID by measured presence, so none of them earns a hero build — but
   each is individually capable of moving the world's variety statistics more
   than the other 429 combined. They get the ceiling requirement (40 sources)
   and an explicit per-family audit whatever their tier.
4. **`distinct_shapes` has a case to answer and it has been tested.** R2-116
   settled it on `spectator_seated`: 7,420 realized instances, 420 sources, 420
   distinct shapes, commonest 0.4 %, **14 distinct base postures**, and the
   positive control (`force_posture` fixed) returns 1 and FAILS. The instrument
   discriminates. Wave 2 should carry the same positive control per family — a
   deliberately-spammed variant that the check is *shown* to reject — because a
   variety check that has never failed anything is not evidence.

### 4.4 The no-external-assets law at 113 items

**ON RECORD:** the project is verified clean — zero image-texture nodes — and
`item_gate` check 1 (`no_external_assets`) walks every image datablock and every
`TEX_IMAGE` node in the file, before any GPU job. `itemkit.assert_no_external_assets()`
runs it again inside the module.

That is structurally sufficient and needs no change. What needs saying is **where
the pressure comes from at 113 items**, because §2.2 answers it: the wave's macro
surface is **13 tree species and 8 other items**. Bark, leaf and canopy at 1,000+
px is precisely the work that tempts a downloaded texture, and it is 62 % of the
film's macro budget. **The mitigation is scheduling, not policing** — put the
trees first (§3.2 step 3), give them the "a month is acceptable" budget, and do
not let them be the last thing built by a tired wave.

Two corollaries the record already supports:

- **The mesh carries the read, the shader garnishes it.** Five of the seven
  wave-1 modules that PASS check 7 have wholly dead shader stacks and pass on
  geometry alone (every one carries `m ≥ 2` in the mesh's own dihedrals). At a
  12.47° sun, geometry is the cheaper and more reliable route to a surface that
  reads — and it is also the route that cannot be faked with a photograph.
- **State the light, not the millimetres.** `K.relief_amplitude_for(m, wavelength_m=…)`,
  and `RELIEF_BANDS` bounds it **both ways** — 0.79 was rejected for too little
  exactly as 3.76 was rejected for too much. Three amplitude sets were rendered
  and rejected before anyone reasoned in radiance.

---

## 5. BUILD + GATE TIME PER ITEM

### 5.1 Compute is not the cost, and the record has been quoting the wrong number

**MEASURED.** Build wall-clock, from the `date +%H:%M:%S` stamps
`work/r2038/run_module3.sh` prints either side of the `blender -b -P` call
(`work/r2038/queue*.log`, `pipe_<item>.log`), n = 13:

```
build:  min 20 s   median 55 s   p90 96 s   max 561 s (pont_deck_slab)
```

A weaker second source — sequential stage-log mtimes in `work/r2116/logs/`,
n = 15, carrying ~30 s of sha256 overhead — gives median 106 s, max 434 s.
Union over the 21 of 28 items with any build measurement: **median 89 s.**

**MEASURED.** Gate cost, three layers, each from a different artefact:

| layer | source | median | p90 | max |
|---|---|---:|---:|---:|
| whole gate wall | `render/gate_witness/_work/sweep2.log`, n = 26 | **155 s** | 256 s | 361 s |
| broker round-trip (submit → PNG) | `render/gate_witness/_results/*/gate.json`, n = 28, all 512 samples | **43.2 s** | 154.3 s | 186.5 s |
| **actual GPU render** | `/home/zany/vast-render/state/broker.db`, 196 witness jobs, read-only | **7.21 s** | 16.24 s | 80.19 s |

```
sum of render_sec over EVERY witness frame wave 1 ever produced:  2,089 s = 0.58 GPU-h
```

**Wave 1's entire gating campaign cost 35 minutes of 5090 time.** The gate's
wall clock is dominated by its *free* part — blend load, edge and node
statistics, image analysis — at a median ~110 s of CPU, and the broker round-trip
is scene upload and teardown, the 81 % overhead already on record. Queue wait is
the only large tail (median 94 s, p90 4,065 s) and it is contention, not work.

**Correction to the planning record, and to an earlier draft of this section:** the
single `242.4 s` figure in `render/items/pit_wall_unit/gate.json` is a broker
round-trip outlier, not a render cost, and it is not n = 1 — 28 real renders are
recorded under `render/gate_witness/_results/`. **GPU is not a constraint on this
wave at any plausible size.** 113 items × 5 gate runs × 2 frames × 7.2 s is
**under 2.3 GPU-hours.**

### 5.2 The cost is agent authoring time, and it is the least-measured number

**This is the finding that should change how the wave is budgeted.**

`docs/PLAN-throughput-optimisation.md` §0 anchors the entire 435-item projection
on **build agent ≈ 2.4 h, peep agent ≈ 0.3 h**. That pair is a **back-fit**: it
solves 28 b + 15 p = 71.7 agent-h against a 16.6 h window at concurrency 4. It is
not a measurement of either quantity, and the doc says so.

**What actually survives — MEASURED, from the workflow store:**

- The successful wave-1 build dispatch's record **does not exist**. In
  `wf_e4d7f755-73d.json`, 26 of 28 `build:<item>` agents are `state: done` with
  `queuedAt: null` — resumed from a prior run whose record was not retained. None
  of the 143 retained subagent transcripts is a wave-1 item build.
- **Exactly two per-item build-agent wall times survive**, and both are outliers:
  `build:pont_deck_slab` **118.7 min**, and `build:showroom_facade_panel (retry 1)`
  **255.5 min and never finished**.
- **Peep agents are measurable and the assumption is wrong by 5.5×.** 27
  `peep:<item>` agents, deconvolved at concurrency 4: **median 27.1 min**, p90
  32.1, max 33.6 — **11.4 agent-hours**, against the 0.3 h/peep the plan assumes.
  (Completion timestamps MEASURED; the per-agent split is an ESTIMATE from the
  deconvolution.)
- **No build tool on this project records its own duration.** No
  `secs`/`seconds`/`elapsed`/`duration` field exists in any item-module build
  output; `tools/item_build_cmd.py` records none. Every build number above comes
  from shell `date` stamps or file mtimes.

**So the number that drives the whole campaign budget — hours per build agent —
has never been measured, and the one adjacent number that has is 5.5× worse than
assumed.** That is the single largest unquantified risk in any wave-2 estimate,
and closing it costs one instrumented tranche.

### 5.3 Rework rate, and the gate's measured false-accept rate

**MEASURED**, `render/gate_witness/_work/TABLE.txt` — the A/B of the wave-1
four-check gate against the current eight-check gate over exactly the 28 wave-1
items:

```
ACCEPTED under the wave-1 gate      26 of 28
ACCEPTED under the current gate      7 of 28      REJECTED 21 of 28 (75 %)
dominant failure: relief_reads_as_lip_and_shade   FAIL x15 + NOT MEASURED x6
```

**Effective first-pass yield against the standard actually being enforced:
7 / 28 = 25 %.** Budget two rounds minimum.

**And the number that says the gate cannot be the only judge.** `TABLE.txt`
designates five items as **MUST-REJECT** — known-bad artefacts the gate is
required to catch. It caught three (`armco_w_beam`, `marshal_post_deck`,
`spectator_seated`) and **passed two**: `crew_fireproof_overall` and
`terrain_ground`, both marked `*** PASSED ***` in the table's own margin.

**A measured 2-of-5 false-accept rate on the gate's own known-bad set.** At 113
items that is an expected ~40 % of the bad ones surviving. *The gate is
necessary, not sufficient* is not a caveat on this project; it is a measured
40 %. **The macro peep tier is not optional and must not be cut to save agents.**

**MEASURED**, re-gates per item, two independent counts: surviving `gate*.json`
versions give **81 files across 32 items** (2–4 each, a floor — in-place
overwrites left no version); broker witness-job clustering gives **median 5 gate
runs per item, p90 9, max 11**. **Take 3–5 gate runs per item as the planning
figure**, not one.

### 5.4 Module size, and the cost of the proposed wave

**MEASURED:**

```
41 modules, 117,938 lines total    over the 28 wave-1 items: median 3,712, p90 4,708, max 5,612
32 test blends                     17.2 GB total, median 346 MB, max 2.38 GB
world/items/ on disk               36 GB for 32 items = 1.125 GB/item incl. .blend1
render/gate_witness/               3.9 GB      witness.png median 4.6 MB
```

**ESTIMATE** of the wave, rebuilt on the corrected inputs above. Build and gate
compute are folded into the agent hour because they are minutes inside it:

| tier | units | h/unit | agent-h | basis |
|---|---:|---:|---:|---|
| W2-0 re-tier | 1 | 3 | 3 | one sweep over an existing point cloud |
| W2-R rework | 8 | 3 | 24 | re-render 31 macros + re-gate 32; no new geometry |
| W2-A hero | 45 | **2.0** | 90 | the 2.4 h back-fit, less the 27.4 % scaffold `itemkit` now supplies. **UNMEASURED — see §5.2** |
| W2-B mid | 35 | 1.4 | 49 | no macro history, no macro peep |
| W2-C stubs | 24 | 0.3 | 7 | a contract file |
| W2-D cells | 16 | 4.0 | 64 | a class-level pass over an existing system |
| peeps | ~40 | **0.45** | 18 | **measured 27.1 min**, not the plan's 0.3 h |
| | | | **≈ 255 agent-h** | **first pass only** |

**× 2 rounds at the measured 25 % first-pass yield ≈ 450–500 agent-hours.** At the
wave-1 concurrency of 4 that is ~5 days; at 16-way, ~30 h — but §5.5 says 16-way
is not reachable.

GPU: **≈ 2.3 GPU-hours** for the whole wave. It is free.

**Against the same model the naive 407-item wave is ~1,600 agent-hours across two
rounds** — and §5.5 says it cannot run at all.

**The honest confidence statement:** the tier *counts* in this document are
measured and I stand behind them. The *hours* rest on a back-fit that has never
been measured, and the one adjacent measurement available says the back-fit is
optimistic by 5.5×. **Treat ≈ 500 agent-hours as a lower bound and instrument the
first tranche.**

### 5.5 The constraint nobody has costed: disk

**MEASURED.**

```
world/items/   36 GB for 32 items  =  1.125 GB per item (test blend + .blend1)
free on /      135 GB
```

```
403 unbuilt items x 1.125 GB  =  453 GB          free: 135 GB
113 proposed    x 1.125 GB    =  127 GB          free: 135 GB
```

**The 407-item wave does not fit on the disk. It is short by 318 GB.** This is
not a scheduling problem or a money problem; it is arithmetic, and it is the
hardest single argument in this document against the naive scope.

**Even the reduced 113-item wave consumes 94 % of the free space** and leaves
nothing for witness blends (4.9 MB × 2 per item), witness PNGs (4.6 MB × 2),
`render/film*.blend`, or the assembly rebuilds that are running right now.

**Wave 2 needs a disk policy before it needs an agent:** delete `.blend1`
backups (roughly halves it), and purge each item's `_test.blend` once its gate
report and macro are on disk and verified. Neither is optional at 113 items and
neither exists today.

---

## 6. WHAT I PROPOSE DROPPING, AND WHY

> *I would rather have 60 items built, gated and rendered than 400 declared and
> 100 done.*

**The honest number is 113 new modules, not 407.** Here is the deletion, in three
grades of confidence.

### 6.1 DELETE FROM THE CAMPAIGN — 50 items

**MEASURED.** Unbuilt **and** BULK **and** under 12 px at their best sharp
unoccluded moment **and** zero dependants. Per §2.4, every one of those numbers
is an **upper bound**, so each of these is *at most* what is shown.

By zone: track_surface 8, kerbs_markings 7, pit_lane 6, grandstand 5, barriers 4,
runoff 4, showroom_breach 4, trackside 3, paddock 2, ephemera 2, pit_straight 2,
transit_corridor 2, pit_building 1.

The sharp end of it — these are the items a module would be *built* for:

| item | peak sharp px | declared instances |
|---|---:|---:|
| `asphalt_transverse_joint` | **0.6** | 40 |
| `timing_loop_sawcut` | **0.6** | 3 |
| `catch_fence_woven_wire` | **0.8** | 2,080 |
| `asphalt_paver_mat_joint` | **0.9** | 80 |
| `pit_lane_speed_line` | **1.0** | 1 |
| `wheel_gun_hose` | **1.0** | 12 |
| `asphalt_crack_seal` | **1.1** | 300 |
| `tv_camera_cable` | 1.6 | 15 |
| `grandstand_nosing` | 1.6 | 3,400 |
| `pit_exit_gore` | 2.0 | 1 |
| `grandstand_row_letter` | 2.0 | **18,350** |
| `concrete_lifting_eye` | 2.1 | 250 |
| `kerb_bedding_joint` | 3.1 | 3,400 |
| `grid_numeral` | 3.3 | 20 |
| `glazing_gasket_set` | 3.4 | 220 |
| `pit_wall_coping` | 3.5 | 125 |
| `access_road_saw_joint` | 3.8 | 240 |

…and 33 more between 4 and 12 px, including `kerb_hero_t4` (11.3),
`start_finish_line` (11.4), `showroom_floor_slab` (10.2), `gravel_stone` (6.3),
`marble_drift_bank` (11.4), `cigarette_end` (11.2), `crew_helmet_visor` (9.7).

**`grandstand_row_letter` is 18,350 declared instances at 2.0 px.** A hero module
for it would be a month of work producing two pixels. **`catch_fence_woven_wire`
is 2,080 instances at 0.8 px** — below one pixel, on a 4K master.

Three of these deserve a sentence each because they are named in the project's own
teaching material and dropping them looks wrong until you read the number:

- **`kerb_hero_t4`** is `ITEM-CAMPAIGN-BRIEF.md` §3's worked example of building
  to the pixel — *"filmed at 0.8 m on a 21 mm lens — 2800 px/m, so a 0.4 mm chip
  in the paint is a visible pixel."* Measured minimum in-frustum depth: **8.2 m.**
  The 0.8 m is an abeam radial distance at which the kerb is 63° outside the
  frame. Peak sharp unoccluded size: **11.3 px.**
- **`showroom_floor_slab`** is the manifest's own *"in Beat 1 it is the mirror
  every part is presented against."* **10.2 px.** It should still exist as a
  surface — it is the floor — but it does not warrant a per-item hero module, and
  its reflection is a property of the showroom build, not of a slab module.
- **`start_finish_line`** peaks at **587 px** unsharp and **66 px** sharp, and
  **11.4 px** sharp-and-unoccluded. The gap between those three numbers is the
  whole argument: it is big when it is smeared, and small when it is legible.

### 6.2 NO MODULE, HANDLED CLASS-LEVEL — 216 further items

The remaining unbuilt BULK items (290 total, minus the 50 deleted and the 24
stubbed) do not get a per-item module. They already exist as class-level
placement geometry and are addressed in **16 `(module, zone)` cells** (§3.4).
This is a demotion, not a deletion: they stay in the frame, they get a
silhouette/value/variation pass, and they are re-examined by frame-peep at the
real camera.

### 6.3 STUB ONLY — 24 items

§3.3. Interface JSON, no module.

### 6.4 The ledger

```
manifest                                          435
  already built (rework, not new build)          - 32
  DELETE from the campaign entirely              - 50
  no module, class-level cell                    -216
  interface stub only                            - 24
  ------------------------------------------------
  NEW ITEM MODULES IN WAVE 2                      113   ( 66 HERO + 47 MID )
  as build units after the family collapse         80
```

**113, not 407. A 72 % cut, every unit of it justified by a measured screen size
that is a proven upper bound.**

And per §2.5 and §2.4, **expect 113 to fall further**, not rise: every time this
has been measured rather than modelled the answer has got smaller, and the HERO
set is an over-count of unknown size because an item inherits its host's best
moment. The right posture is to build W2-A, measure the items as themselves, and
re-derive before committing to W2-B.

---

## 7. HOW WAVE 2 AVOIDS THE FIVE HARNESS DEFECTS

A 113-item wave — let alone a 407-item one — run on this harness as it stands
will manufacture convincing nulls at scale. Each defect below is stated with what
I measured today and the rule wave 2 runs under.

### 7.1 R2-108 / R2-120 — the build flags are not uniform

**MEASURED**, `python3 tools/item_build_cmd.py --census --no-runtime`, over all
41 modules:

```
parser        argparse 35   hand-rolled 5   none 1
build verb    --test 22   --test-scene 5   --test-blend 4   (none) 10
save flag     --out 21    --save 18       (none) 2
DISTINCT (verb, save) COMBINATIONS:  8
  --test --save 15 | (none) --out 9 | --test --out 7 | --test-blend --out 3
  --test-scene --save 3 | --test-scene --out 2 | (none) (none) 1 | --test-blend (none) 1
```

**Eight distinct CLI conventions across 41 modules, and 23 of 41 do not take
`--save`.** On a hand-rolled parser the wrong flag is silent: the module builds
the scene, prints its full report, throws the result away and **exits 0**. That
manufactured a flawless 0.00 % null where the truth was 57.50 %.

**Rule:** no wave-2 harness ever types a build command. It calls
`tools/item_build_cmd.py --build --item <id> --out <path>`, which derives the
command from the module's own parser **and requires the target blend's sha256 to
change**. A module whose blend does not move did not build, whatever its exit
code said.

**Two defects in that tool, found while running it (§8).**

### 7.2 R2-116 / R2-117 — the verdict on disk is not the verdict of the run

**MEASURED**, reconciling the JSON `result` field against the printed
`STAGE RESULT` line in `render/items/*/gate_run.log` (31 manifest items, every one
of which has printed-line evidence):

| source | ACCEPTED | REJECTED | UNMEASURABLE |
|---|---:|---:|---:|
| JSON `result` field | 11 | **20** | — (no cell exists) |
| printed `STAGE RESULT` / `REPORT_STATUS` | 11 | **17** | **3** |

**3 of 31 reports on disk (9.7 %) say `ITEM_REJECTED` where the run said
`ITEM_UNMEASURABLE`:** `marshal_post_column`, `spectator_seated`, `tyre_blanket`.
Only one of the three carries the `REPORT_STATUS` annotation; the other two are
recoverable only from the log.

*A gate that could not look and a gate that looked and rejected are opposite
findings — one is "fix the item", the other is "fix the gate".* At the measured
9.7 % rate, a 400-item wave misroutes **~39 items** into rework they do not need,
and each of those is a full build agent.

**Rule:** wave-2 status is read from the printed line, never the field. Every
gate invocation tees its stdout to `render/items/<id>/gate_run.log`, and the
orchestrator's admission test greps `STAGE RESULT:`. **`campaign_preflight.py
--policy wave2` currently branches on `gate_result`, i.e. on the field R2-117
says cannot carry the answer** — see §8.

### 7.3 R2-119 — staleness, and it is worse than 30 of 32

**MEASURED today**, `python3 tools/item_dep_staleness.py --census --no-runtime`:

```
32 rows      STALE_CLOSURE 31      CLEAN 1
own_module_newer (what --stale-census sees):  0 of 32
```

**Every item blend but one is stale against its import closure, and the
own-module rule scores all 32 clean.** What makes them stale:

| dependency newer than the blend | items |
|---|---:|
| `world/world_contract.py` | **30** |
| `world/itemkit.py` | 9 |
| `world/build_surface.py` | 3 |
| `world/items/marshal_post_column.py` | 3 |
| `world/humankit.py`, `world/film_exposure.py`, `world/items/armco_w_beam.py` | 1 each |

worst lag: median 4.5 h, p90 131.2 h, max 137.9 h (`asphalt_wearing_course`).

**This is the single most important operational fact for wave 2: one edit to
`world_contract.py` invalidates every item blend in the wave simultaneously.**
At 32 items that is a 32-item rebuild. At 113 it is 113. At 407 it is 453 GB of
rebuild that will not fit on the disk (§5.5).

**Rule:** `world_contract.py` and `itemkit.py` are **frozen for the duration of
each tranche**, with the freeze enforced by stamping their sha256 into every
item's report (`tools/input_stamp.py` already does this) and refusing to gate an
item whose blend predates either. A staleness rule that looks only at the
module's own source is blind to exactly the dependency that made the last twenty
defects.

### 7.4 R2-121 — the witness path, and a second problem in the same place

**MEASURED**, `tools/item_gate.py:2931-2937`:

```python
wbdir  = os.path.join(WITNESS_BLEND_ROOT, a.item)          # item-derived, NOT movable
wdir   = os.path.abspath(a.witness_dir) if a.witness_dir else wbdir
wblend = os.path.join(wbdir, "witness.blend")              # follows wbdir
wpng   = os.path.join(wdir,  "witness.png")                # follows --witness-dir
```

The blend is pinned to the item id (deliberately — the broker requires the scene
inside one of its roots, so a client-supplied path is a traversal vector) while
the PNG and spec follow `--witness-dir`. **A flag that redirects some of a tool's
outputs and not others is worse than one that redirects none:** it reads as
isolation while writing outside the sandbox, and it tears the blend/PNG pair
apart. That is how re-gating `spectator_seated` overwrote `spectator_crowd`'s
witness — the pair R2-061 was written to protect.

**Rule:** **wave 2 never passes `--witness-dir`.** Default paths only, one gate
per item id at a time, and the orchestrator holds a per-item lock. If a witness
must be preserved, copy the whole directory aside first — as
`render/gate_witness/spectator_seated_wave1/` and
`_r2116_spectator_crowd_witness_backup/` already do.

**And the second problem, which I measured and which is not R2-121:**

```
published reports under render/items/*/gate.json whose witness came from
  --from-png (re-analysis of an existing PNG, no render):        31 of 32
witness PNGs OLDER than the item test blend they describe:       19 of 31
   armco_w_beam 7.3 h · gravel_bed_surface 7.2 h · marshal_post_deck 7.1 h
   crew_figure 7.1 h · pit_wall_unit 7.1 h · armco_post 7.0 h · ...
```

The renders themselves are real and are recorded separately — 28 of them under
`render/gate_witness/_results/*/gate.json`, all at 512 samples. The problem is
the **join**: the published verdicts were re-analysed off PNGs rendered in that
earlier sweep, and **19 of the 31 test blends have since moved underneath them.**

**A majority of wave 1's current verdicts were computed by re-analysing a PNG
that predates the blend it is supposed to describe.** This is R2-118's shape one
layer out — *"re-auditing an old witness republishes a number about an artefact
that no longer exists"* — and `--from-png` has no guard for it: it requires the
spec sidecar, so it knows *which pixels are the control*, but nothing tells it
the subject still looks like that. Reported as **SUSPECT, not as a defect**: per
R2-120's determinism arm, 10 of 16 rebuilt modules came back bit-identical, so an
mtime says the source moved, not that the geometry did. Settling it costs one
`--build` per item and a sha compare.

**Rule:** wave 2 gates render their own witness. `--from-png` is permitted only
when the PNG is **newer** than the blend, and the gate should refuse otherwise.

### 7.5 The defect that is not in the numbered list — the macro

§3.0. **31 of 32 built items have no `macro.png`.** The gate's own eight checks
are explicitly *"necessary, not sufficient"*; the campaign brief says *"an item is
done when the gate passes **and** the render survives that look."* For 97 % of
the built corpus the second half has no artefact. Wave 2 must treat
`macro_png_complete` + `macro_at_gate_resolution` as admission criteria — which
`campaign_preflight --policy wave2` already does correctly — and the wave must not
be allowed to declare an item done without them.

---

## 8. DEFECTS FOUND WHILE SCOPING

Listed here rather than in `DEFECT-LOG-R2.md`, which I do not own. Each is
reproducible from a command in this document.

1. **`tools/item_build_cmd.py --census --no-runtime` mislabels 35 of 41 rows.**
   With the runtime arm skipped, every row's RUNTIME column reads
   `-- static only (hand-rolled parser)` — *including the 35 rows whose own PARSER
   column the same table prints as `argparse`.* A reader concludes 41 of 41
   modules are hand-rolled when the measured truth is 5. The skip reason is
   correct for 5 rows and fabricated for 35. Repro:
   `python3 tools/item_build_cmd.py --census --no-runtime`.

2. **The same census's summary line undercounts its own finding.** It prints
   *"the WRONG SAVE FLAG on 21 of 41 modules"*, but `--save` is also wrong for the
   2 modules that take no save flag at all. The correct figure is **23 of 41**,
   which is what R2-108 records. The tool disagrees with the defect log about the
   defect log's own number.

3. **`tools/campaign_preflight.py --policy wave2` inherits R2-117.** Its
   `gate_accepted` rule branches on the JSON `result` field — the field R2-117
   establishes is two-valued for three outcomes. Measured consequence: the wave-2
   admission checkpoint marks `marshal_post_column`, `spectator_seated` and
   `tyre_blanket` as rejections when their runs printed `ITEM_UNMEASURABLE`. The
   checkpoint that exists to route the wave routes 9.7 % of it wrongly, in the
   expensive direction.

4. **`item_gate --from-png` will re-score a witness older than the blend.**
   §7.4. 19 of 31 on disk are in that state today. SUSPECT, not proven defective;
   R2-118's shape one layer out.

5. **The published tiering names `assembly6`; the ship is `assembly8`.** §2.6.
   Bounded and safe in direction, but `docs/proposed_tiers.json` is the file wave
   2 is scoped from and it should be re-stamped against the shipping world before
   a single agent reads it.

6. **`world/items/spectator_standing_ga.py` parses but defines no top-level
   `build()`** (1,029 lines, 27 defs). Preflight catches it. It is either
   truncated or was never finished, and it is a manifest item.

7. **`render/items/spectator_crowd/gate.json` is a report about a different
   item.** Its `"item"` field reads **`spectator_seated`** and its `witness.png`
   path points at `render/gate_witness/spectator_seated/witness.png`. The
   directory name says one item, the contents say another. This is R2-121's
   mechanism leaving a permanent artefact: a report filed under the wrong id is
   worse than a missing one, because every consumer that keys on the directory —
   `campaign_preflight` included — reads it as `spectator_crowd`'s verdict.
   `spectator_crowd` is also a built module with **no manifest row** at all.

8. **`render/gate_witness/_work/TABLE.txt` contradicts its own table.** Its
   summary line reads *"28 items: 7 ACCEPTED, 21 REJECTED (before: all 28
   ACCEPTED)"* while its own BEFORE column shows `pont_deck_slab` and
   `showroom_facade_panel` as REJECTED. `docs/PLAN-throughput-optimisation.md:26`
   repeats the "28/28 ACCEPTED, zero rejected" claim. **Two of the three sources
   say 26 of 28.** Treat first-gate acceptance as **≈ 93 %**, not 100 %. The
   "28/28 accepted, 15/15 reworked" framing that motivates the whole gate rewrite
   is directionally right and numerically wrong.

9. **The wave-1 build campaign's workflow record does not exist**, so per-item
   build-agent time is unrecoverable (§5.2). No build tool on this project records
   its own duration. Wave 2 should stamp a duration into every item's hand-back;
   it costs one field.

---

## 9. THE ESTIMATES, NAMED

| claim | status | what would settle it |
|---|---|---|
| **113 new modules** (66 HERO + 47 MID) | **MEASURED** selection over an **ON RECORD** tiering | — |
| 71/56/308 tiering | **ON RECORD**, validated 3 ways (aim gate 0.004°, positive-control camera, ID-pass render 94.2 % / 0 misses in the direction that matters) | its 4th arm (by-eye) is withdrawn on exposure grounds; 8 frames re-rendered at −3.628 restores it |
| tiering valid on `assembly8` | **ESTIMATE**, bounded by a measured 1-object diff | one `screen_presence.py` sweep — recommended as W2-0 |
| HERO 71 is an over-count | **ESTIMATE**, from the stated upper-bound property of host inheritance | measure the items as themselves after W2-A |
| 50 items droppable outright | **MEASURED**, and the measurement is a proven upper bound | — |
| build 89 s · gate wall 155 s · GPU 7.2 s/frame · **0.58 GPU-h for all of wave 1** | **MEASURED** — `work/r2038/queue*.log`, `_work/sweep2.log`, `_results/*/gate.json`, `broker.db` | — |
| 3–5 gate runs per item | **MEASURED**, two independent counts | — |
| 25 % first-pass yield; gate false-accepts **2 of 5** known-bads | **MEASURED**, `render/gate_witness/_work/TABLE.txt` | — |
| peep agent 27.1 min (5.5× the planning assumption) | **MEASURED** completions, **ESTIMATED** per-agent split (concurrency-4 deconvolution) | instrument one tranche |
| **2.0 h per hero build unit** | **UNMEASURED.** The 2.4 h it derives from is a back-fit; the wave-1 build workflow record does not exist | one instrumented tranche — the single highest-value measurement left |
| ≈ 500 agent-hours over two rounds | **ESTIMATE, LOWER BOUND**, compounding the row above | same |
| 16-way concurrency | **NOT REACHABLE TODAY** — disk-bound before agent-bound (§5.5) | a disk policy; then it is a real number |
| 1.125 GB/item · 135 GB free · 407 items = 453 GB | **MEASURED** | — |
| ≈ 2.3 GPU-hours for the whole wave | **ESTIMATE** from measured per-frame render × measured gate-run counts | — |

**The three numbers to take away:**

1. **113 new item modules, not 407.** Every unit of the 72 % cut is justified by a
   measured screen size that is a *proven upper bound*, and 50 items should be
   deleted from the campaign outright.
2. **Compute is free; agent time is everything.** Wave 1's entire gating campaign
   cost 35 minutes of GPU. The number that actually sets the budget — hours per
   build agent — has never been measured on this project, and the one adjacent
   figure that has is 5.5× worse than assumed.
3. **The gate false-accepts 2 of its own 5 known-bads.** Do not cut the peep tier
   to save agents; it is the only instrument that has ever caught the real yield.

If the wave must be smaller still, **cut W2-B before W2-A** — those 47 items never
exceed 300 px and nothing in the film ever inspects them closely.
