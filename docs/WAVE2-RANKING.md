# WAVE 2 — THE RANKING, AND WHAT NOT TO BUILD

**Written 2026-08-07. This document decides what wave 2 builds and in what order.
It builds nothing.** It supersedes the *sizing* in `docs/WAVE2-SCOPE.md` §3 while
keeping that document's structure and its §6 deletions; where the two disagree on
a number, this one was measured against the live camera and the shipping world
and that one was not.

> ## The headline
>
> **44 items carry 80 % of every pixel-second of item screen presence in the
> film. 90 carry 95 %. And 190 of the 435 never exceed 60 px in any frame of the
> 2,978.**
>
> **Eleven trees carry 50.2 % of it between them.** Not 50 % of vegetation —
> 50 % of *everything*. The single highest-value item in the film is
> `tree_lombardy_poplar` at 5.2 % on its own, and the top eleven ranks are all
> trees before any other class appears.
>
> So the answer to "is wave 2 four hundred modules?" is **no, and it is not 113
> either.** It is **~44 modules for 80 % of the picture, and the first eleven of
> those are trees.**

---

## 1. The number that was asked for

| question | answer |
|---|---:|
| items in the manifest | 435 |
| items with **any** frame above 60 px | **245** |
| items with **zero** frames above 60 px | **190** |
| items carrying 80 % of on-screen area-time | **44** |
| items carrying 95 % of on-screen area-time | **90** |

Tier counts on the live camera (`film17`) and shipping world (`assembly10`):
**HERO 72, MID 58, BULK 305.**

For contrast with the figure this campaign has been quoting: the manifest flags
**343** items as heroes. The camera says **72**. The earlier "343 → 91" collapse
was the same measurement made against an older camera and world; it reproduces in
shape, and the number has moved to 72 rather than away from it. **Every time this
has been measured rather than modelled the answer has got smaller, and it did so
again.**

## 2. Method — reproducible, and its weaknesses stated

**Inputs, stamped.** `work/w2_0/retier_a10/inputs.json`:

| role | file | sha256 |
|---|---|---|
| world | `render/world/assembly/r2/assembly10.blend` | `be56b2a1…` |
| camera | `render/film17_path.json` | `676798074601107f…` (the declared live path) |

Regenerate end to end with `bash tools/retier.sh` — it now resolves the camera
through `tools/live_campath.py` rather than the stale orphan
`world/camera_rig_path.json` (fixed and committed today, `7744d84`; the
control `work/w2_0/ctl_retier_campath.sh` prints `RETIER_CAMPATH_CTL_OK`, 6/6,
and includes a discrimination arm proving the weaker resolver does **not**
refuse). All 2,978 frames, uniform 180° shutter, 1 m voxel point cloud capped at
2,000,000.

**The ranking statistic.** Screen **area** × **duration**, as a strict lower
bound:

```
score = 300² · f300  +  150² · (f150 − f300)  +  60² · (f60 − f150)
```

where `fN` is the number of frames the item is sharp, unoccluded and at least
N px. Each frame is credited only the *lower* edge of the band it falls in, so
the score understates every item and never flatters one. Units are px²·frames.
Ranking written to `work/w2_0/wave2_ranking.json` (all 435 rows, every input
field retained).

**Three weaknesses, stated rather than buried:**

1. **It is a host upper bound for unbuilt items, and that caveat is NOT
   cleared.** `assembly10` was believed to have placed the item modules; it has
   **4 of 38**, and under the current resolution **`0 of 435` items resolve to a
   host list containing their own geometry** — even the 4 that are placed
   (`timing_stand` resolves to `ARCH_PitWall`). So an unbuilt item inherits its
   *host's* best moment. Every tree in the top 11 shares an identical
   `min_depth_m` of 4.577 m, which is the signature of one shared host, not
   eleven measurements. **Treat the tree ranks as "this class dominates" — which
   is robust — and not as "poplar beats pine by 6 %", which is not.**

   **The magnitude is now measured, and it is large.** `lighting_mast` sits at
   rank 16 in §3 on a host-derived 2160 px. Built and measured *as itself* —
   against `film17_path.json`, the 11 stations `build_architecture.py` actually
   authors, their real heights of 11.1–16.4 m, and true frustum tests — it peaks
   at **588 px at 84.18 m on a 32 mm lens**. **The sweep overstates it by
   3.67×**, and the manifest by 3.05×. Three independent causes: it inherits a
   ZONE-tier host (`lighting_mast_head` carries a byte-identical host list, the
   same 1,203 frames and the same 7.602 m — the two rows differ only in
   `height_m`); its `typical_height_m` of 12.0 m is *below* the authored minimum;
   and the 25 m approach is unreachable from any authored station except from
   inside the showroom.

   Since score goes as px², a 3.67× linear overstatement is up to **13× in the
   ranking statistic**. **So ranks are reliable as bands, not as positions**, and
   any item promoted to a build should have its framing re-derived from the
   camera first — which is cheap, and which is exactly what turned rank 16 from
   2160 px into 588 px.
2. **Banding is coarse.** Only 60/150/300 px thresholds exist in the measurement,
   so an item that spends the film at 299 px scores as 150. This compresses
   differences among mid-rank items and is why §4 declines on *bands*, never on
   rank order.
3. **The 190 zero-scoring items are zero at a 60 px floor**, not invisible. Many
   are visible; none is ever large. That is the distinction §4 turns on.

## 3. The ranking — where the cliff is

| # | item | tier | peak px | f≥300 | score (px²·frames) | cum % |
|---:|---|---|---:|---:|---:|---:|
| 1 | `tree_lombardy_poplar` | HERO | 2160 | 933 | 85,368,600 | 5.2 |
| 2 | `tree_scots_pine` | HERO | 2160 | 864 | 80,442,900 | 10.1 |
| 3 | `tree_oak` | HERO | 2160 | 850 | 79,399,800 | 14.9 |
| 4 | `tree_london_plane` | HERO | 2160 | 833 | 78,157,800 | 19.7 |
| 5 | `paddock_avenue_tree` | HERO | 2160 | 818 | 77,048,100 | 24.3 |
| 6 | `tree_silver_birch` | HERO | 2160 | 807 | 76,200,300 | 29.0 |
| 7 | `tree_crack_willow` | HERO | 2160 | 804 | 75,882,600 | 33.6 |
| 8 | `tree_italian_cypress` | HERO | 2160 | 801 | 75,439,800 | 38.2 |
| 9 | `tree_dead_standing` | HERO | 2160 | 798 | 75,123,900 | 42.7 |
| 10 | `tree_rowan` | HERO | 2160 | 731 | 69,210,900 | 47.0 |
| 11 | `tree_hawthorn` | HERO | 2160 | 513 | 53,204,400 | **50.2** |
| 12 | `escarpment_skyline` | HERO | 1151 | 332 | 34,963,200 | 52.3 |
| 13 | `shrub_hazel` | HERO | 1490 | 241 | 31,134,600 | 54.2 |
| 14 | `tree_sapling` | HERO | 1278 | 224 | 27,760,500 | 55.9 |
| 15 | `hedgerow_section` | HERO | 1278 | 224 | 27,760,500 | 57.6 |
| 16 | `lighting_mast` | HERO | 2160 | 178 | 17,858,700 | 58.7 |
| 17 | `shrub_broom` | HERO | 681 | 155 | 17,343,000 | 59.7 |
| 18 | `catch_fence_post` | HERO | 944 | 120 | 16,992,000 | 60.8 |
| 19 | `breach_dust_column` | HERO | 2160 | 155 | 15,478,200 | 61.7 |
| 20 | `shrub_gorse` | HERO | 596 | 129 | 14,881,500 | 62.6 |

Ranks 21–44 (to the 80 % line), in order: `heras_fence_panel`,
`heras_banner_scrim`, `awning_leg`, `finger_post_sign`, `parasol`,
`forklift_truck`, `paddock_gate`, `forecourt_bollard`, `timing_tower`,
`shrub_bramble`, `log_pile`, `marshal_access_gate`, `gas_bottle_cage`,
`shrub_juniper`, `marshal_overall`, `marshal_figure_standing`,
`paddock_personnel_figure`, `crew_figure`, `photographer_figure`,
`steward_figure`, `grandstand_tower`, `ga_viewing_bank`, `jersey_barrier`,
`mullion_intact`.

**The shape of the distribution is the finding.** Rank 1 scores 85.4 M; rank 44
scores 9.1 M; rank 90 is where 95 % is reached and the remaining **345 items
share 5 %**. There is no defensible reading of this in which building 400 modules
is a better use of a month than building 44 of them properly.

**Build in this order.** It is already sorted by the thing the client is judging
— how much of the picture changes — so rank order *is* the build order.

## 4. What I decline to build, and why

**Grade A — 190 items, decline outright.** Never above 60 px in any of 2,978
frames. Their combined contribution to the ranking statistic is **zero**, and it
is zero by measurement rather than by a threshold I chose. This subsumes and
extends `WAVE2-SCOPE.md` §6.1's 50 deletions.

**Grade B — ranks 91–245, decline as per-item modules.** 155 items sharing the
last 5 % of area-time. They are visible and they matter *collectively* — they are
the texture of the world — but a per-item hero module returns almost nothing.
Handle them class-level in their owning world module, as `WAVE2-SCOPE.md` §3.4
already proposes at 16 `(module, zone)` cells.

**Grade C — five wave-1 rejections, decline the rework.** `asphalt_wearing_course`
(3.3 px), `pont_deck_slab` (3.7), `gravel_bed_surface` (10.4),
`kerb_precast_unit` (11.7), `grandstand_riser_unit` (13.8) — none with a single
frame above 150 px. Reworking relief on a 3.3 px surface is indefensible.
`terrain_ground` (5.3 px) is equally uninformative but currently reads ACCEPTED;
its acceptance was measured at 467 px, **88× larger than the camera ever shows
it**, and means nothing either way.

**What I explicitly do NOT decline**, against appearances:
- `crew_fireproof_overall` measures 60.9 px while the figure wearing it measures
  551.8. A garment cannot be nine times smaller than its wearer — that is a host
  mis-assignment, not a small item. Re-measure before judging.
- The `SUPERSEDE_WELDED` items. 14 held rows are held partly because *the world
  already builds that feature*, welded into a class object. Declining them costs
  the frame nothing, because the feature is present either way.

## 5. The trap sitting directly under this ranking

The ranking says build trees. The project's single most expensive lesson says
**how**, and the two interact badly if taken separately.

At **4,500 instances**, `tree_oak` faces the gate's variety floor of **40 distinct
sources, 40 distinct shapes, ≤ 25 % commonest** — but only if it emits geometry-
nodes instances the depsgraph can walk. **If it emits plain objects, the same
check demands `distinct_topologies >= 2`** (`tools/item_gate.py` ~2986). Nineteen
of the 32 wave-1 items took that weak path, four of them declaring 900–3,641
instances. It has not yet produced a false accept — those four measure 88–803
topologies — but nothing prevents one, and **the guard whose entire purpose is
"one tree spammed a hundred times" would grade 4,500 identical trees as a pass on
two variants.** This is staged as R2-1381 and is **unfixed**.

So: the highest-value items in the film are also the ones the red-line guard is
weakest against. Fix the guard before, or with, the trees.

## 5a. Three results the stopped tree builds produced that outlive them

These cost most of a session to obtain and are cheap to lose. None depends on the
modules being kept.

**Relief stages superpose by TANGENT, not by `m`.** `tree_oak`'s own check 7c
caught its built bark field at a 99.9th-percentile wall of 44.82° = **m 6.375**,
outside `hard_feature`'s 1.50–6.00 ceiling — from two fissure networks each
*individually* in band (m 5.24 and m 4.46). **The relief law as written in
`ITEM-CAMPAIGN-BRIEF.md` §4a gives a per-stage budget and says nothing about how
stages compose.** Anything that declares several relief stages in one band can be
compliant stage-by-stage and out of band once built. `relief_budget()` audits
stages as declared; only a measurement of the *built* field catches this. This
belongs in the brief.

**The needle crossover is 12.69 m, and it decides the tree LOD ladder.** At
4K/35 mm, `px_per_m = 3733.33/d`. A Scots pine needle is 1.70 × 58 mm, so it is
1.00 px at 6.35 m, **0.50 px at 12.69 m**, and 0.20 px at 31.11 m — where an 18 m
tree exactly fills the 2160 px frame. **At the item's own peak presence a needle
is five times below the one-pixel line.** So needle mesh is justified at natural
size only to ~12.7 m; beyond it the honest construction scales the blade by *k*
and divides shoot count by *k²*, conserving projected needle area (measured 1.000
/ 0.999 / 0.992 across L0/L1/L2). Also declined with arithmetic, and worth
reusing: needle twist/keel 0.3 mm (0.24 px), bark wax grain 0.4 mm (0.33 px),
stomatal banding 0.25 mm (0.20 px).

**A full-density conifer cannot be the library primitive on this box.** One L0
Scots pine measures **1.35–1.89 M triangles** (534k–794k needles). Forty-four
sources is ~66 M tris; the declared 4,200 instances at L0 would be
**~4.4 × 10⁹**. L1 sources measure 249–311 k. Any tree plan that does not lead
with an LOD ladder is not costed. Note also that `item_gate.edge_stats_m` is a
pure-Python loop over every edge — on these meshes **it, not RAM, is the
ceiling**.

## 5b. THE ONE THING TO CHECK BEFORE REBUILDING ANY TREE

**Two independent tree builds hit the same wall.** A correct cypress spray needs
~800 k tris/tree, so 44 L0 sources is ~35 M triangles and will not fit 11 GB —
but dropping below 37 sources breaks the variety floor at 1,400 instances. The
pine's numbers say the same thing an order of magnitude louder. **As specified,
the tree tier is unbuildable on this machine**, and it is 11 of the top 11 ranks.

**Before reopening that trade, check the distance it rests on.** Every tree
reports a `min_depth_m` of **4.577 m** — and reports the *identical* value, which
is one shared host rather than eleven measurements (§2.1). The one item where
this was actually re-derived moved from a host-derived 7.602 m to a measured
**84.18 m — an 11× error** (R2-1362).

And the cypress render shows both answers in one frame: **the near trees read as
broadleaf, the background trees read acceptably as cypress** (R2-1342). Same
asset, same light, same frame; the only variable is angular size.

**If trees are seen at tens of metres rather than 4.577 m, the crisis largely
dissolves** — at 80 m a 55–130 mm spray is sub-pixel, the LOD ladder does the
work, and the 800 k-triangle L0 source may never be on screen at all. If 4.577 m
is real, the trade is genuine and must be made deliberately. **This is a
hypothesis with a precedent, not a finding.** What settles it is the method that
settled `lighting_mast`: resolve the live camera path, take the stations the
world actually authors, test the frustum. It is cheap, and it gates the top
50 % of the ranking.

## 6. State on disk — read this before building anything

**Four item modules exist that have NEVER BEEN GATED.** Written 2026-08-07
15:25–15:33 by build agents that were stopped mid-flight when the client cut
concurrency:

| file | bytes | gate report |
|---|---:|---|
| `world/items/tree_oak.py` | 104,007 | **none** |
| `world/items/tree_scots_pine.py` | 99,450 | **none** |
| `world/items/tree_italian_cypress.py` | 93,144 | **none** |
| `world/items/lighting_mast.py` | 98,133 | partial only (`relief.json`, `placement.json`; **no `gate.json`**) |

**Do not assume these work.** They are substantial and define `build()`, but not
one has a verdict, no macro was confirmed at 3840×2160, and **21 of 28 wave-1
items failed the gate at some point.** A fresh session that reads
`world/items/tree_oak.py` and concludes tree_oak is built will repeat R2-725
("I dispatched a build that was already built, because I read a finding and not
the tree") in its mirror image. Gate them first; treat the verdict, not the file,
as the state.

Per-module state as handed back, in the authors' own terms:

- **`tree_oak`** — pure-python selftest **31 of 32**, including 6 negative
  controls shown to reject known-bad input. `Tree.grow()`, `mesh()`, the GN group
  and `test_scene()` **have never executed inside Blender**. The one failure is
  real and general (§5a). No interface JSON on disk.
- **`tree_scots_pine`** — selftest **22/22**; geometry builds in Blender and was
  measured across 3 sources × 3 LODs. No test blend, no gate, nothing looked at.
  Three of its own guards fired during the build and caught real errors,
  including a forward-fill bug that would have baked "current-year needle" onto
  the entire trunk. **Three unfinished edits inside the module would mislead a
  reader** — its docstring §0c still argues for gating at 4.577 m while the code
  gates at 12.693 m, and `test_scene` lacks the `Near` sub-collection the near
  arm needs.
- **`tree_italian_cypress`** — **KNOWN BAD. Do not gate it; rebuild the foliage
  first** (R2-1341). It is the only one of the four that was rendered and looked
  at, and **it is not a cypress** — at 1:1 it reads as a bay laurel: spray length
  ~4× oversize, spray width ~8×, order-1 branch diameter ~7×, and a hollow crown
  with sky visible through it. **All 25 of its selftests passed, negative controls
  included, and none could see it.** The frame itself is sound (0.0000 clipped,
  5.7 % crushed), so this is a verdict on the subject, not the exposure. A second
  defect the sizing account does not cover: **the branches are flat untapered
  ribbons**, hard-edged with visible polygon silhouettes — fixing spray size alone
  would leave correct foliage on flat slabs. Everything else in the module — the
  framing derivation, derived relief budget, pixel footprint, the instancer on the
  strong variety path, and the selftests with their negative controls — stands and
  is reusable. **This is the most useful of the four results**, because it is the
  only one where the frame was allowed to decide.
- **`lighting_mast`** — selftest 11/11, interface JSON written, relief audit and
  placement gate both run and clean (all 11 stations, tightest camera clearance
  1.99 m). **Only `gate.json` is missing**; the job died at exit 144 on a 5090
  that was still resuming, and never rendered. Its macro is staged at 3840×2160
  but **was never rendered, so the dimensions were never read back off disk** —
  R2-020 remains unverified for it.

Also note `world/items/tyre_deposit.py` (103,814 bytes, 15:33) appeared from
activity outside this task's four agents — **`world/items/` is being written
concurrently by others**, so any count of "built modules" is a moving target and
should be re-taken, not quoted from here.

**Not published, deliberately:** `docs/screen_presence.json` still holds the
08-04 assembly9/film14 measurement. The refreshed one is at
`work/w2_0/retier_a10/item_presence.json`. It was **not** promoted because doing
so would retire the `presence_unverified_2026_08_04` caveat's `to_clear` line
while its condition is unmet (§2.1). Promote it once items resolve to their own
geometry — not before.

> ### NOTHING OF MINE IS RUNNING — stopped deliberately, and why
>
> `work/w2r1286/regate.sh` ran detached until 15:47 and **was killed because it
> was producing false negatives, not verdicts.** Its results at the point of
> stopping:
>
> ```
> access_road_slab   rc=3  2136s  STAGE RESULT: ITEM_UNMEASURABLE
> armco_post         rc=3   320s  STAGE RESULT: ITEM_UNMEASURABLE
> ```
>
> **2 of 2 UNMEASURABLE, both for transport reasons rather than anything about
> the item.** `access_road_slab`'s is directly my fault — I cancelled its
> in-flight render (R2-1390). `armco_post`'s is not, which points at something
> systemic in the fresh-instance path. Allowed to run to completion this would
> have written **32 `ITEM_UNMEASURABLE` reports that look like data**, and a
> NOT-MEASURED is a rejection, not a skip. That is the defect class this project
> hunts, so producing 32 of them unattended is worse than producing none.
>
> **Killing the parent was not enough, and this is worth knowing.** `kill 1679205`
> left an orphaned `item_gate.py` (PID 1718786) reparented to init, which promptly
> **submitted a fresh farm job**. Same incomplete-scope mistake as R2-1390 in a
> different costume: I scoped the kill to the shell and not its descendants.
> Caught, killed by explicit PID — **not `pkill -f`**, which is the same sweep
> antipattern — and its job cancelled by id. Broker 8760's queue is **EMPTY** and
> no process of mine remains.
>
> **Two paid renders survived on disk and should be used rather than re-bought:**
> - `~/vast-render/out/064b88b666c9.png` — 3840×2160, 33,893,524 B
>   (`access_road_slab` witness)
> - `~/vast-render/out/650d03fabe40.png` — 2,036,855 B
>   (`armco_w_beam` witness)
>
> `item_gate.py --from-png` scores a delivered PNG without re-rendering.
>
> **To resume:** start **`work/w2r1286/run_all.sh`**, not `regate.sh` — the orchestrator sequences the BASE and MEASURED arms whose comparison is the point (R2-1288). It is resumable; a killed item is simply redone. But
> **diagnose the UNMEASURABLE transport failure first** — otherwise it will
> reproduce 32 times. Outputs land in `work/w2r1286/gate_M/<item>/gate.json`,
> witnesses in `work/w2r1286/wit_M/<item>/`, progress in `work/w2r1286/armM.log`.
> Verdicts are the printed `>> STAGE RESULT:` lines, **never** the exit code —
> Blender exits 0 on an uncaught exception.
>
> **Do not** touch brokers on `state2`–`state6`; they carry other agents' film
> renders, including the client's beat-1 proxy. A separate `tyre_deposit.py --gate`
> Blender process belongs to another workstream and is **not** mine.

**As of this writing the re-gate had produced ZERO verdicts.** It is staged (R2-1286..1294,
`work/w2r1286/`, `regate.sh` is resumable) but every arm is 0 of 32: the rented
5090 died mid-campaign, a job was submitted to an instance that no longer
existed, and the replacement was still booting when work stopped.

**I then cancelled four jobs on broker 8760, and two belonged to other sessions.**
See **R2-1390** — my defect, and the most important operational item on this page.
I queried the broker DB for every `queued`/`running` row and cancelled all of
them, inferring ownership from the **scene path** while the `jobs` table's
**`agent` column** stated it outright. One I should not have touched was
`brokerfix` **re-running the very `access_road_slab` witness I had diagnosed as
wedged** — I cancelled the repair and the thing being repaired, and reported it
as tidying up after myself.

**The paid render survived and does not need re-buying:**
`~/vast-render/out/064b88b666c9.png` — valid PNG, **3840 × 2160**,
33,893,524 bytes. That is the gate's required master resolution (R2-020), and
`item_gate.py --from-png` scores a delivered PNG without re-rendering, so
`access_road_slab`'s witness can be scored from this file directly.

**Rules for anyone touching a shared broker: cancel only by a job id you
submitted; never sweep a queue; never cancel what you did not submit, however
stale it looks — a stale-looking job is evidence about someone else's work, not
yours.** `rq cancel` records no caller, so the log cannot attribute a
cancellation after the fact; discipline at the call site is the only control, and
it is the one that failed here.

Broker 8760's queue is otherwise empty; its idle timer owns the GPU decision and
is more careful than a manual teardown (`broker/config.py:667` — "an idle queue
is not an idle GPU"). Brokers on `state2`–`state6` carry other agents' film work
and were not touched.

**Two uncommitted tool changes exist**, from the plumbing work: `tools/item_hosts.py`
(adds `placement_prefixes()`, `self_hosts()`, a `SELF` host tier) and
`tools/item_presence.py` (adds `--no-self-hosts`, `measured_as_self`, a census).
**`audit()`'s signature changed from a 2-tuple to a 3-tuple** — its only caller is
updated, but a fresh session must not assume the old shape. Its control fires:
`--no-self-hosts` → `SELF_HOST_MISSED=4`, non-zero; with the fix → 0. One loose
end: the refusal exits **2 (CRASH) rather than 1 (FAIL)**, so the verdict token
probably does not match `gate_exit`'s `_FAIL_MARKERS`. Re-hosting moves exactly
**one** item (MID 58→57, BULK 305→306); which item was not identified.

**Also outstanding, staged in `docs/STAGING-R2-1271-to-R2-1400.md`:**
`tools/input_stamp.py` still hardcodes the stale camera literal (R2-1271);
`item_gate.py` can override the framing **distance but not the lens** (R2-1367),
so a witness staged for a 32 mm item is rendered at the manifest's 35 mm and
comes out ~9 % oversized; `placement_gate.py` sees only the carrier on a
GN-instanced item, and its `--campath` still defaults to the R2-1007 orphan.

**R2-1384 is WITHDRAWN** — my claim that a rejected item sits in the shipping
world was wrong three ways (I read a `gate.json` the ledger does not cite; that
file's own `REPORT_STATUS` disowns its verdict as `ITEM_UNMEASURABLE`; and
`build_items.py:505` already re-reads the live gate). **The real defect found
while refuting it is better: 3 of 4 placed items ship bytes that were never
gated**, invisible because the sha check and the verdict check both pass and
nothing composes them. Build a gate-provenance-binding guard, not a
verdict-regression guard.

## 7. If you pick this up cold, do these in order

1. **Re-gate the 32 built items at measured framing** (`--filmed-distance-m`,
   `--onscreen-px-4k` from the ranking JSON, not the manifest). The manifest
   over-frames by a median **8.83×**, worst **336×**. This is the head of the
   chain: every rejection that flips releases an item into the world, which is
   the only thing that lets the tiering measure items as themselves.
2. **Fix the variety guard's weak path** (§5), with a control that fires.
3. **Gate the four ungated modules** in §6 and find out what they actually are.
4. **Re-derive the TREES' true filmed distance first** (§5b). It is cheap, it
   gates the top 50 % of the ranking, and it decides whether the tree tier's
   triangle crisis is real or an artifact of a shared-host 4.577 m. Do this
   before rebuilding `tree_italian_cypress` or building any other tree.
5. **Before building any item, re-derive its framing from the camera** — the
   authored-stations method that turned `lighting_mast` from 2160 px into
   588 px (§2.1). It is cheap, it is the difference between building for the
   right band and the wrong one, and on the one item where it has been done it
   moved the answer by 3.67×.
6. **Then build down the ranking from rank 1**, one module at a time.

Nothing above requires a wide fan-out. The ranking is the deliverable; the
building is the easy part once it is not being done four hundred times.
