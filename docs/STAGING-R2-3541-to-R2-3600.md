# R2-3541..R2-3600 — assembly15: the landing, the buildability proof, and the

# market measurement that decides the ground cover

Agent `r2-3541-assembly15`. Task: land the eight paths as one commit set, prove
`HEAD` builds, take the gating memory measurement, then build and gate
assembly15 against assembly14.

**Read this first:**

1. The eight-path landing is **still blocked, on two paths, not zero** — the
   brief believed five were freed and in fact **four** were (R2-3541).
2. **The ground cover should ship.** It costs **+17.1 % measured**, not the
   +20.4 % predicted, and that lands inside a **hole in the offer distribution**,
   so it costs **zero** purchasable machines. The scene has **+44.5 %** of
   headroom before it loses one (R2-3544, R2-3545).
3. **assembly15 is WORSE than assembly14 and is NOT a ship candidate** —
   `build_dressing` failed and the world lost **247 objects**. Bisected to a real
   defect: **it takes both the ground cover AND `build_nearband` to cause it.**
   Either alone builds fine, and `TERRAIN_R2970_BEFORE=1` through the identical
   pipeline reaches assembly14's exact object count (R2-3546).

**So the ground cover is affordable but currently defective.** The cost question
is settled in its favour and stays settled; the next task is the defect, not the
decision.

---

## R2-3541 — THE LANDING IS BLOCKED ON TWO PATHS, AND THE BRIEF'S PATH WAS A TYPO

The brief states five paths were freed by retiring the stale seed. **Four were.**
`.git/r2-guard/retire.log` is the record, and it names exactly four:

```
2026-08-08T20:53:19  retired_by=r2-coordinator  owner=inflight-2026-08-07  path=world/build_items.py
2026-08-08T20:53:20  retired_by=r2-coordinator  owner=inflight-2026-08-07  path=world/build_barriers.py
2026-08-08T20:53:20  retired_by=r2-coordinator  owner=inflight-2026-08-07  path=world/items/PLACEMENT.json
2026-08-08T20:53:20  retired_by=r2-coordinator  owner=inflight-2026-08-07  path=world/items/spectator_crowd_world.py
```

**There is no `itemkit` line, and the reason is visible in the brief's own
wording.** The brief lists the fifth path as `world/items/itemkit.py`. The file
is at **`world/itemkit.py`** — it is not in `world/items/`. A retire aimed at a
path that does not exist frees nothing and says so quietly.

**And `tyre_deposit.py` was never free either.** R2-3486 recorded it as `free`;
it is not. Asked of the lease store rather than of the previous report:

| path | lease holding it | claim result |
| --- | --- | --- |
| `world/build_items.py` | — | **CLAIMED** |
| `world/build_barriers.py` | — | **CLAIMED** |
| `world/items/PLACEMENT.json` | — | **CLAIMED** |
| `world/items/spectator_crowd_world.py` | — | **CLAIMED** |
| `world/build_nearband.py` | `inflight-auto` | **CLAIMED** (auto yields, by design) |
| `render/world/assembly/r2/assemble.py` | `inflight-auto` | **CLAIMED** (auto yields, by design) |
| `world/itemkit.py` | **`inflight-2026-08-07`** | **CLASH** |
| `world/items/tyre_deposit.py` | **`inflight-2026-08-07`** | **CLASH** |

Verbatim, one path at a time as instructed:

```
CLASH    world/itemkit.py  held by inflight-2026-08-07 (seed, via world/itemkit.py, 22.8 h old)
CLASH    world/items/tyre_deposit.py  held by inflight-2026-08-07 (seed, via world/items/tyre_deposit.py, 22.8 h old)
>> STAGE RESULT: FAIL (0 claimed, 1 clashes)
```

**Six of eight are mine. I did not retire the other two, and I did not commit
the six.** The instruction is to never retire a lease I do not own, and the
previous agent's reasoning about partial landings is if anything stronger here:
`itemkit.py` is the module carrying `detail_for` and `assert_wired`, i.e. **two
of the six breaks**. Landing six of eight would commit a fingerprinting
assembler and a `build_nearband` into a tree that **still does not build**, and
would make it look repaired at precisely the two call sites a reader would check
last.

**All eight or none. Two retires are needed, and they are yours:**

```
R2_AGENT=<you> tools/gitguard.py retire --apply world/itemkit.py
R2_AGENT=<you> tools/gitguard.py retire --apply world/items/tyre_deposit.py
```

### The source state is no longer at risk while this waits

assembly14 became unreproducible because its `build_terrain` state existed in no
commit and nowhere on disk. **That failure mode is now closed for assembly15
whether or not the commit lands.** Before touching anything, all 94 world source
files plus the assembler were snapshotted with SHA-256:

```
<scratch>/r2-3541/snapshot/world_src_at_build.tar.gz
<scratch>/r2-3541/snapshot/SHA256SUMS.txt      (100 files)
```

The four hashes the previous agent recorded for assembly14 reproduce exactly —
`build_barriers 2d435466`, `build_items fbf7bc1e`, `build_nearband 3fa0729a`,
`itemkit 41ec66bc` — confirming the worktree is still the state assembly14 read
and that nothing drifted under this task.

**The commit does not change a single byte the build reads.** `git add` of the
worktree changes `HEAD`, not the worktree, and the assembler imports from the
worktree. So assembly15 built now is byte-for-byte the artefact a post-commit
build would produce, and landing the commit later does not invalidate it.
Nothing is wasted by proceeding, and the snapshot is what makes that claim
checkable rather than hopeful.

---

## R2-3542 — THE BUILDABILITY PROOF, BOTH ARMS, RE-OBSERVED

The R2-3482 probe re-run today, same script, same Blender 5.2.0
(`fbe6228777e7`), HEAD extracted fresh via `git archive` at `b51d90a`:

```
>> STAGE RESULT: WORKTREE SOURCE_BUILDABLE   (0 of 5 probes failed: none)
>> STAGE RESULT: HEAD     SOURCE_UNBUILDABLE (5 of 5 probes failed)
```

HEAD's five, unchanged and each observed:

| probe | HEAD |
| --- | --- |
| `nearband_import` | `ModuleNotFoundError: No module named 'build_nearband'` |
| `itemkit.detail_for` | `AttributeError: module 'itemkit' has no attribute 'detail_for'` |
| `itemkit.assert_wired` | `AttributeError: module 'itemkit' has no attribute 'assert_wired'` |
| `build_items.class_feature_owned_at` | `AttributeError: module 'build_items' has no attribute 'class_feature_owned_at'` |
| `build_surface.build()` | `ModuleNotFoundError: No module named 'tyre_deposit'` |

**`HEAD` still does not build, because the landing is still blocked.** The
deliverable "prove `SOURCE_BUILDABLE` before spending 22 minutes" is met in the
form that actually gates the build: **the worktree is the tree the assembler
reads, and it passes 5 of 5 with the positive control observed.** The HEAD arm
is the negative control and it fails, correctly, at all five sites.

---

## R2-3543 — THE FINGERPRINT'S BLIND SPOT IS CLOSED: 11 KEYS → 94

`_source_fingerprint()` enumerated `world/build_*.py`, `world_contract.py` and
`itemkit.py`: **11 keys.** It said nothing about `assemble.py`, nothing about
`world/items/PLACEMENT.json`, and nothing about any `world/items/*.py` — so the
`items` stage, whose entire behaviour those files decide, was invisible to the
mechanism that exists to make artefacts attributable.

That is not a weaker guarantee than a complete one. **It is a false one**, since
the question it answers is "would a rebuild be this file?" and for two worlds
differing by **1,586 objects** it answered *yes*.

Now covered, keys repo-relative:

| set | keys |
| --- | --- |
| `world/build_*.py`, `world_contract.py`, `itemkit.py` | 11 (unchanged) |
| `world/items/*.py` and `world/items/*.json` | +82 |
| `render/world/assembly/r2/assemble.py` (the assembler itself) | +1 |
| **total** | **94** |

Compatibility was checked rather than assumed: both consumers —
`tools/build_film_scene.py:181` (`_world_source_state`) and
`tools/car_staleness.py:164` — iterate `recorded.items()` and re-resolve each
key against the repo root, so the wider key set works unchanged. All 94 keys
resolve to an existing file under the root. Widening can only turn a false
FRESH into a true STALE.

---

## R2-3544 — THE GATING MEASUREMENT: THE GROUND COVER DOES **NOT** THREATEN PURCHASABILITY

This was the question that could have decided the pass outright, and the answer
is not close. **It is not close in the opposite direction to the one feared.**

### The premise, restated exactly

The film scene measures **50.6 GiB resident** against a card-selection floor
where only seven offers qualify. If the world grows ~20 %, does the scene become
unrentable?

### What the 50.6 GiB actually is — and one correction

Traced to its origin: it is **not** a repo tool's output. It is a hand reading of
`/proc` and cgroup files taken over ssh on vast.ai instance `id-066` on
2026-08-08, recorded at `docs/STAGING-R2-3001-to-R2-3060.md:966-973`, and baked
into `vast-render` at `vastctl/vastctl.py:465` as
`SCENE_WORKING_SET_GIB = 50.6`. The refusal string carries its own provenance.

**The correction: it was measured on `film23_breach.blend`, not `film24_breach`.**
The two differ by 1,440 bytes on disk (10,946,487,113 vs 10,946,488,553), so
50.6 GiB is still right to within noise — but it has never been re-measured on
film24, and the record should say so.

The gate the market applies is not 50.6 but **50.6 × `RAM_HEADROOM` 1.25 =
63.2 GiB/GPU** (`vastctl.py:479`, `_meets_scene_working_set` at `:656-690`).

### The market, surveyed today, not quoted from yesterday

`vastctl offers --hours 8 --disk 30`, exclusive RTX 5090, run now:

| id | RAM GiB | $/hr |
| --- | --- | --- |
| id-033 | 124.9 | 0.441 |
| id-008 | 125.7 | 0.468 |
| **id-014** | **91.4** | 0.454 |
| id-010 | 125.2 | 0.492 |
| id-054 | 125.7 | 0.532 |
| id-021 | 188.3 | 0.535 |
| **id-005** | **93.4** | 0.536 |
| id-052 | 125.5 | 0.601 |

and dropped under the floor: `id-065` 62.7, `id-012` 60.5, `id-001` 60.4.

**The distribution has a hole, and that hole is the whole answer.** Today's rungs
run `60.4, 60.5, 62.7 | 91.4, 93.4, 124.9, 125.2, 125.5, 125.7, 125.7, 188.3` —
**nothing at all is on sale between 62.7 and 91.4 GiB.** The floor the scene
must clear is 63.2 GiB, which sits just above the lower cluster; every machine
that qualifies today is **at least 91.4 GiB**, and six of the eight are ≥ 124.9.

### Driven through the broker's own gate, not through my arithmetic

`VASTRENDER_SCENE_WORKING_SET_GIB` swept against the live market:

| scene resident | required floor (×1.25) | offers that clear |
| --- | --- | --- |
| **50.6 GiB** (today) | 63.2 | **7** |
| 55.0 | 68.8 | 7 |
| **60.9 GiB** (**+20.4 %, the ground cover**) | **76.1** | **7** |
| 65.0 | 81.2 | 7 |
| 70.0 | 87.5 | 7 |
| 73.1 | 91.4 | 6 |
| 75.0 | 93.8 | 6 |
| 80.0 | 100.0 | 6 |
| 90.0 | 112.5 | 5 |
| 100.6 | 125.8 | **1** |

**The count does not move until 73.1 GiB resident, which is +44.5 %.** The
ground cover asks for +20.4 %. It lands squarely inside the 62.7 → 91.4 GiB hole,
and **you pay nothing for growth that stays inside a gap.**

### The verdict on the gating question

> "A 20 % geometry increase may push the scene past what is purchasable at any
> price."

**Measured: it does not.** Not marginally — the scene has **+44.5 % of headroom
before it loses one machine**, and would have to roughly **double** (+98.8 %,
100.6 GiB) before the market collapses to a single offer. The ground cover
consumes under half the available headroom and costs **zero** offers.

Three honest caveats, none of which move the verdict:

1. The film's resident growth is being taken as equal to the world's evaluated
   triangle growth. It will in fact be **smaller**, because the film also holds
   the car, the rig and the breach sim, which do not grow at all. 60.9 GiB is
   therefore an **over**-estimate, and the real margin is wider.
2. The market is live: the same query returned 8 offers once and 7 a few minutes
   later. The *shape* — a hole between ~63 and ~91 GiB — is what carries the
   argument, and it is stable across both the archived survey and today's.
3. 50.6 GiB is film23's number, not film24's (above).


---

## R2-3545 — THE TRIANGLE COST, MEASURED: **+17.1 %**, NOT +20.4 %

assembly15 was built under `tools/buildlock.sh` from the worktree, ground cover
**IN** (`TERRAIN_R2970_BEFORE` unset → `R2970_BEFORE=False` → fescue `seed=0.15`,
tussock `seed=0.45`, `PANICLE_N=(18,30)`). Peak RSS of the build **9.19 GiB**
(three independent measures agreeing; the meter was checked against a known
2 GiB allocation first and read 2.01).

### The ground cover is IN, confirmed from the datablocks

The R2-3483 probe re-run against assembly15, with the `verts/polys == 1.75`
discriminator made explicit. **assembly15 is the exact inverse of assembly14 on
both signatures:**

| signature | assembly14 (shipped) | **assembly15** |
| --- | --- | --- |
| grit `sharp_face` — flat / smooth | 0 flat / 24 smooth | **24 flat / 0 smooth** |
| clumps holding `verts/polys == 1.75` exactly | 22 of 22 | **0 of 32** |

`>> STAGE RESULT: GROUNDCOVER PRESENT (pass IN -- 32 of 32 clumps carry panicle geometry)`

### The paired triangle census — same instrument, same day, both worlds

`tools/poly_census.py` run on assembly15 **and** assembly14 today, rather than
quoting assembly14's recorded numbers:

| | assembly14 | assembly15 | delta |
| --- | ---: | ---: | ---: |
| BASE | 123,307,968 (3,445 meshes) | 119,126,112 (3,198 meshes) | −3.4 % ¹ |
| EVALUATED | 1,256,842,384 (30,204 objs) | 1,252,546,092 (29,957 objs) | −0.3 % ¹ |
| **INSTANCES** | **13,842,597,953** | **16,434,456,855** | **+18.72 %** |
| **RENDERED (what Cycles traces)** | **15,099,440,337** | **17,687,002,947** | **+17.14 %** |
| realized instances | 4,966,913 | **4,966,913** | **identical** |
| distinct source meshes | 1,569 | **1,569** | **identical** |

¹ BASE and EVALUATED are *down* only because assembly15 is missing 247 dressing
objects — see R2-3546. Those objects are not instanced, so they do not touch the
two rows that matter.

And the terrain module's own accounting, which is where the previous report's
`15.12 G / 16.31 G` actually came from (`assembly14_build.json`, not a census):

| terrain summary | assembly14 | assembly15 | delta |
| --- | ---: | ---: | ---: |
| `instanced_tris` | 15,115,562,914 | 18,087,554,991 | **+19.66 %** |
| `evaluated_tris` | 16,307,129,669 | 19,279,121,746 | **+18.23 %** |
| `grass_clumps` | 2,975,018 | 2,975,018 | identical |
| `grass_hero_clumps` | 1,821,790 | 1,821,790 | identical |
| `unique_meshes` | 1,432 | 1,432 | identical |

**The clump counts are identical to the unit.** The pass changes what is inside
a clump, not how many there are — which is exactly what makes this a clean
measurement of the ground cover and nothing else.

**The prediction was +20.4 %; the measurement is +17.1 % (whole world, rendered)
and +18.2 % (terrain evaluated).** R2-3483's extrapolation was high by ~2 points
— i.e. wrong in the safe direction, and close enough that its method was sound.

### Against the market, using the measured number

| growth basis | film resident | floor (×1.25) | offers |
| --- | ---: | ---: | ---: |
| today | 50.6 GiB | 63.2 | **7** |
| **+17.14 %** (world rendered) | **59.3 GiB** | **74.1** | **7** |
| +18.72 % (world instances) | 60.1 GiB | 75.1 | **7** |
| +19.66 % (terrain instanced) | 60.5 GiB | 75.7 | **7** |
| — first offer lost at — | 73.1 GiB | 91.4 | 6 |

**Every basis lands in the hole, and none of them costs an offer.** The margin to
the first loss is +44.5 % against a measured demand of +17.1 %, so the conclusion
does not depend on which of the three growth figures you prefer.

---

## R2-3546 — **ASSEMBLY15 IS WORSE THAN ASSEMBLY14 ON ONE STAGE. FLAGGING IT.**

The first assembly15 build printed:

```
>> ASM MODULES FAILED: dressing
>> STAGE RESULT: ASSEMBLE_FAIL
```

`build_dressing` raised at `build_dressing.py:747`:

```
File "world/build_dressing.py", line 4191, in build_marshal_post
    wx, wy, z, lat = anchor("post%02d" % post["n"], s, lat, side, ...)
File "world/build_dressing.py", line 747, in anchor
    wx, wy, wz = float(wx), float(wy), float(wz)
TypeError: only 0-dimensional arrays can be converted to Python scalars
```

**It failed 1.1 s in, on effectively the first marshal post, and the world lost
all 247 dressing objects** — the ad boards, the tyre stacks, the flagpoles, the
TV cameras, the marshal posts. 30,821 objects against assembly14's 31,068.

`build_dressing.py` is **byte-identical** to the file assembly14 built from
(`f5d4cc5d` at a14, HEAD and worktree), as are `world_contract.py` and
`build_barriers.py`. So an **input** changed, not the code.

### Two isolation runs, and the second one refuses to reproduce it

| run | modules | dressing |
| --- | --- | --- |
| assembly15, full | surface, barriers, architecture, terrain, nearband, dressing, items | **FAIL at 1.1 s** |
| isolation A | surface, barriers, architecture, **dressing** | **OK**, 247 objects, 41.8 s |
| isolation B | surface, barriers, architecture, terrain (under `capture_terrain`), nearband, dressing | **OK**, 247 objects, 104.4 s |

Isolation B reproduces `assemble.py`'s exact module sequence, its
`capture_terrain` wrapping, and its `NB.build(ctx=…)` call, with the scene at
**29,115 objects** at dressing time — the same count the failing run had — and
dressing completed normally, landing on **29,362 objects, precisely
assembly14's post-dressing count**.

**So the failure did not reproduce under an identical sequence.** That makes it
either non-deterministic or dependent on something `assemble.py` does that the
isolation does not. It is *not* explained by the ground cover on the evidence so
far, and I am not going to claim it is.

`float()` on a size-1 array still works in this numpy, verified — so the offending
value had **more than one element**, i.e. `post["s"]` reached `station_world` as a
multi-element array. Nothing in the static read of `marshal_post_plan` /
`_finalise_posts` produces that from scalars, which is consistent with the
non-reproduction.

**A straight rebuild is running now** — the cheapest decisive test, and it yields
a complete world if it passes. Its result is the thing to read before anything
else in this block is acted on.

### What this means for the verdict

**Report it as a regression against assembly14, because that is what the
artefact shows.** assembly15 as first built is **not a ship candidate**: it is
missing 247 objects that assembly14 has. The gate numbers above survive it
(instances and sources are untouched by dressing), but `placement_gate` on a
world with no ad boards, tyre stacks or marshal posts would return a CLEAN it has
not earned, and is therefore **deliberately not reported as a pass** below.

### The rebuild reproduced it exactly

A straight rebuild through the same path failed identically — `dressing ok=False`
at **1.1 s**, 30,821 objects, 8,780.0 MB, peak RSS 9.68 GiB, 1,197 s.

```
>> ASM MODULES FAILED: dressing
>> STAGE RESULT: ASSEMBLE_FAIL
```

So the failure is **deterministic inside `assemble.py`** and **absent outside
it**, under what is otherwise the same module sequence and the same 29,115-object
scene. That pins the trigger to something `assemble.py` does that the isolation
does not — not to the ground cover, and not to `build_dressing` itself. The
isolation and the assembler differ in only a few places (`gc.collect()` between
stages, the `report`/fingerprint bookkeeping, `items` in `MODS`), and none of
them has an obvious route to a multi-element `post["s"]`.

### THE BISECT IS DONE, AND THE GROUND COVER IS THE CAUSE

Four arms, all through `assemble.py`, all with the same binary:

| arm | terrain | ground cover | nearband | dressing |
| --- | :-: | :-: | :-: | --- |
| assembly15 (and its rebuild) | ✓ | **IN** | ✓ | **FAIL at 1.1 s** |
| `--mods surface,barriers,architecture,terrain,dressing` | ✓ | **IN** | — | **OK**, 247 objs, 105.3 s |
| `TERRAIN_R2970_BEFORE=1`, full sequence | ✓ | **OUT** | ✓ | **OK**, 247 objs, 108.4 s → 29,362 |
| assembly14 (pre-ground-cover terrain) | ✓ | OUT | ✓ | OK, 247 objs |

**It takes BOTH the ground cover AND nearband to break dressing.** Either alone
is fine. With `TERRAIN_R2970_BEFORE=1` the identical pipeline — same assembler,
same nearband, same `build_dressing` — reaches **29,362 objects, exactly
assembly14's post-dressing count.**

So this is not flakiness, and it is not `assemble.py` bookkeeping. **It is a real
defect introduced by the ground-cover pass**, surfacing through `build_nearband`
into `build_dressing`'s `anchor()`, where `post["s"]` arrives as a multi-element
array. (The earlier non-reproduction outside `assemble.py` is now the odd result,
not the failure; the most likely explanation is that the hand-reconstructed
`NEARBAND_CTX` in that probe was not identical to the assembler's.)

**`build_nearband.py` is the untracked module — the one with no committed source
at all.** The defect sits in the interaction between the newest terrain work and
the module that has never been committed, which is exactly the pair with the
least review behind it.

---

## R2-3547 — GATE VERDICTS AGAINST assembly14

Measured today with the same instrument on both worlds wherever a number is
given. **Where a gate was not run, it says so — no assembly14 number is carried
forward under a new name.**

| gate | assembly14 (baseline) | assembly15 | verdict |
| --- | --- | --- | --- |
| triangle budget — RENDERED | 15,099,440,337 | **17,687,002,947** | **+17.14 %**, measured both sides |
| triangle budget — INSTANCES | 13,842,597,953 | **16,434,456,855** | +18.72 % |
| terrain `evaluated_tris` | 16,307,129,669 | 19,279,121,746 | +18.23 % |
| variety — realized instances | 4,966,913 | **4,966,913** | **IDENTICAL** |
| variety — distinct sources | 1,569 | **1,569** | **IDENTICAL** |
| variety — top share (VEG) | 2.03 % | **2.0 %** (gini 0.867) | **unchanged** |
| variety — VEG / SPECX split | 823 / 746 | **823 / 746** | **IDENTICAL** |
| `instance_variety` verdict | clean | **`INSTANCE_VARIETY_CLEAN`** | **PASS**, no family leans on one source past 40 % |
| ground cover present | **absent** (22/22 clumps at 1.75) | **present** (0/32 at 1.75) | as intended |
| `placement_gate` | `PLACEMENT_CLEAN, 0` (`SHIPPING.md:512`) | **NOT RUN — deliberately** | see below |
| z-fight (`probeG`) | passed | **NOT RUN** | see below |
| winding | passed | **NOT RUN** | per-item sweep; item sources byte-identical to a14's |
| socket (`--blend` arm) | passed | **NOT RUN** | see below |
| `socket_index_audit` (source arm) | — | 72 LETHAL / 19 MOVED / 1219 STABLE | **standing project-wide state, not a regression**; the source arm is world-independent |

**Why three gates are deliberately not run rather than run and reported.**
assembly15 is missing its 247 dressing objects — the ad boards, tyre stacks,
flagpoles, marshal posts and TV cameras. Those are precisely the class of object
`placement_gate` exists to catch on the road, and a `PLACEMENT_CLEAN` returned by
a world that does not contain them is **a pass it has not earned**. Running the
gate would produce a number that looks like a verdict and is not one. The same
argument applies to the z-fight and socket blend arms. They are worth running the
moment R2-3546 is closed, and not before.

**The gate that was run and observed to behave:** `placement_gate --selftest`,
**all 60 controls behaved**, including the positive ones that must fire (`a PLAIN
object 0.20 m into the car path is a violation  fires=True expected=True`).
`>> STAGE RESULT: PLACEMENT_SELFTEST_OK`. So the instrument is trusted and only
its subject is withheld.

**Nothing regressed on any gate that ran.** The one regression is a build stage,
not a gate, and it is R2-3546.

---

## R2-3548 — RECOMMENDATION ON THE GROUND COVER

**Ship it.** With the numbers behind it:

* It costs **+17.1 %** of what Cycles traces (15.10 G → 17.69 G), measured on
  both worlds with one instrument on one day — **not** the +13.9 % on the ticket
  and **not** the +20.4 % predicted. The prediction erred high by ~2 points.
* That growth takes the film from 50.6 GiB resident to a projected **59.3 GiB**,
  requiring a **74.1 GiB** card. **Seven offers clear that — the same seven that
  clear today.** Nothing is lost, because the market has no machines between
  62.7 and 91.4 GiB and the new floor lands in that empty band.
* The first offer is lost at **73.1 GiB resident, i.e. +44.5 %**. The pass asks
  for +17.1 %. It consumes **38 % of the available headroom** and leaves the rest.
* The clump counts are unchanged to the unit (2,975,018 clumps, 1,821,790 hero,
  1,432 unique meshes, 4,966,913 instances, 1,569 sources), so the cost is
  entirely *inside* the existing vocabulary. **The variety census does not move
  at all** — this buys detail without buying repetition.

The preference in the brief was to include it because the panicle branch reads at
18-19 px at a visible band. **The measurement does not contradict that
preference; it removes the objection to it.** The scene a nobody-can-rent
argument was aimed at does not exist at this size.

### But it cannot ship yet, and that IS about the ground cover

The bisect in R2-3546 closed after this recommendation was first written, and it
changes the shape of the answer:

**The ground cover is affordable but currently defective.** It costs dressing —
247 objects — through `build_nearband`. `TERRAIN_R2970_BEFORE=1` builds the same
world with the same nearband and loses nothing.

So the recommendation stands as a recommendation about the *pass*, not about
*today's artefact*:

* **The market objection is dead.** +17.1 % is affordable with 27 points of
  headroom to spare, and that finding does not expire when the defect is fixed.
  **This is no longer a question about cost.**
* **The pass is not shippable until the nearband × ground-cover defect is
  fixed.** One defect, one interaction, and a clean A/B that isolates it to
  within one flag.
* **Do not ship assembly15 as built,** and do not ship it with
  `TERRAIN_R2970_BEFORE=1` either — that is assembly14's world with extra steps,
  and it would spend a rebuild to gain nothing.

The next task is the defect, not the decision. The decision is made: **the ground
cover is worth its triangles.**
