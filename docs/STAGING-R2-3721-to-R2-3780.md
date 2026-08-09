# STAGING R2-3721 .. R2-3780

## R2-3721..R2-3736 — task #162: the variety gate now sees the trees, and the trees are measured for the first time

**VERDICT: the gate is repaired and the trees are measured. The worst single
tree source mesh in the film is `VEG_tree_oak_L2_06` at 45 co-visible sharp
copies at ≥ 64 px, and `VEG_tree_oak_L2_15` at 30 at ≥ 128 px, against the named
failure of 100. The repaired gate nevertheless returns
`INSTANCE_VARIETY_SPAM` on `assembly15` — on five REED GRASS meshes, at
241–300 co-visible sharp copies at ≥ 64 px — and §6 is what those 300 reeds
actually are in the delivered frame. That one needs your ruling; I have not
moved a threshold to make it go away.**

Files: `tools/instance_variety.py` (rewritten),
`tools/r2_3721_variety_gate_control.py` (new, 17 checks),
`tools/r2_3721_sweep_crosscheck.py` (new, 3 claims),
`tools/gate_exit_selftest.py` (contract updated).
Reports: `docs/instance_variety.json` (new schema),
`docs/instance_variety_SUPERSEDED_pre_R2_3721.json` (the stale pre-fix artefact,
moved aside so its 310/1.99 % cannot be requoted),
`work/r23721/`.

---

### 1. The census, both arms, on `assembly15`

```
TOTAL 4,997,117 realized meshes -- 30,204 REAL OBJECTS + 4,966,913 GN instances
                                -- over 3,404 source meshes           (49 s)
```

**The first of those two numbers is the arm the gate could not see.** The old
counting loop was `for inst in deps.object_instances: if not inst.is_instance:
continue`, and `build_terrain.instance_plants()` places every tree, hedgerow
tree, avenue tree, near-band short tree and amenity tree as a LINKED DUPLICATE
OBJECT, which has `is_instance == False`.

The measured GN arm, 4,966,913, is the number the old gate would have reported
in full — it lands on `assembly14`'s 4,955,784 to within 0.2 %, i.e. **the old
figure was the ground cover and nothing else, exactly as the #162 finding
said.** The sweep's candidate set now contains **27,946 discrete plants over 323
source meshes** which no variety instrument in this project had ever counted;
that lands on `assembly15_build.json`'s own woodland 24,646 + hedgerow 3,299 +
avenue 24 = 27,969 to within 23.

Only **two** families in this world are built from repeated meshes at all:
`VEG_*` (1,092 repeated meshes) and the crowd, `SPECX_*` (746). See §5 for what
that does to the exemption table I wrote before measuring.

---

### 2. `top_share` is retired, not recalibrated

The verdict is now **co-visible sharp instances per source mesh**: for every
source mesh used twice or more, and every frame of the delivered camera, the
count of instances of THAT ONE MESH simultaneously in frustum, at least
`RECOG_PX` pixels tall in the 4K delivery, and with shutter smear ≤ 6 px at the
flat 180° shutter. The client's sentence *is* that number: "one tree spammed 100
times" is 100.

It is **measured per mesh, not estimated**. The R2-3421 predecessor divided a
pool's count by an assumed library size because it worked from a voxelised point
dump that had lost which library slot each instance drew. This gate walks the
depsgraph, so it knows the actual source mesh of every instance and needs no
library table, no binomial approximation and no voxel scale factor.

`top_share` is still computed and still written to the report — the historical
records are quoted in it and a reader must be able to line them up — under the
key `top_share_retired_R2_3441`. It decides nothing.

**The control proves the two are different measures, on the same 40 instances of
the same one mesh** (§3, arms C/D): a grove of 40 and the same 40 strung out at
150 m spacing have *identical* `top_share` of 0.4938, and the new measure reads
**40 against 1**.

---

### 3. `tools/r2_3721_variety_gate_control.py` — 17 checks, and the first one is the old code failing

It drives the REAL file — arm B imports `instance_variety.census`, arms C–F run
`tools/instance_variety.py` as a subprocess and judge **both** its exit status
and the worst `STAGE RESULT` in its log. The R2-3421 control reimplemented the
gate's loop inline and could therefore only ever have tested the
reimplementation.

```
ARM A -- the RETIRED walk on 40 trees from ONE mesh
  depsgraph mesh entries: 81 total, 40 with is_instance == True
  source mesh                    gate's walk    unfiltered
  VEG_grass_fescue_H00_u                  20            20
  VEG_grass_fescue_H01_u                  20            20
  VEG_tree_oak_L0_00                       0            40
  ok   RETIRED walk sees 0 of the 40 spammed trees                    [saw 0]
  ok   the trees ARE in the depsgraph -- unfiltered walk sees all 40  [saw 40]
  ok   and the retired walk printed a SPAM verdict about the GRASS while the
       100 %-spammed tree was invisible to it   [top ...H00_u at 50 %]

ARM B -- instance_variety.census(), the REAL function, same scene
  ok   the repaired census sees all 40 trees        [objects=40 gn_instances=0]
  ok   and files them as REAL OBJECTS               [objects=40 gn_instances=0]
  ok   the GN arm is not broken by the fix          [40 over 2 meshes]
  ok   per-instance height is measured, not assumed [3.000 m]

ARM C -- the whole gate on a grove of 40 co-visible trees, ONE mesh
  ok   gate returns PASS(0) -- under the named failure of 100  [rc=0 scan=0]
  ok   and it MEASURED them: 40 co-visible sharp copies
  ok   the trees are the WORST source mesh in the scene

ARM D -- THE SAME 40 INSTANCES OF THE SAME MESH, strung out at 150 m
  ok   C and D have the SAME instance count of the SAME one mesh   [40 vs 40]
  ok   the RETIRED measure cannot separate them   [top_share 0.4938 vs 0.4938]
  ok   the NEW measure separates them             [grove 40 vs strung 1]

ARM E -- 120 co-visible copies of one mesh, over the named failure
  ok   gate returns FAIL(1) and says SPAM   [INSTANCE_VARIETY_SPAM [oak_L0_00]]
  ok   and it names the tree mesh, at 120 co-visible sharp copies

ARM F -- the grove again with NO --path
  ok   gate returns VACUOUS(3), not PASS, when it has no camera

17/17 checks passed          >> STAGE RESULT: IV_GATE_CONTROL_OK
```

**Arm A is the control that had to be watched failing, and it is the exact case
#162 named: 40 trees from one mesh, and the shipped gate saw none of them.**

`gate_exit_selftest.py`'s contract is updated with it. The two shipped control
blends still discriminate under the new measure once given a camera — measured:
`ctl_variety_pos` (500 instances of one mesh in a 250 m row) reads **123**
co-visible sharp copies and FAILs; `ctl_variety_neg` (500 distinct meshes at one
point) reads **2** and passes. A third case was added: the same positive blend
with **no** `--path` must return VACUOUS(3), because co-visibility is a screen
event and a gate with no screen must refuse rather than pass.

> **Carried debt, not fixable by me:** `render/world/assembly/r2/v12{0,1,2}/battery.sh`
> invoke this gate without `--path` and will now get VACUOUS(3) rather than a
> verdict. Those files are under `render/world/assembly/`, which this task was
> told not to touch. **They need `--path render/film24_path.json` adding.**

---

### 4. `tools/r2_3721_sweep_crosscheck.py` — and it caught two silent under-counts in my own sweep

The new sweep has a height-octave spatial index and a per-point cull that the
R2-3421 loop does not have. That is exactly the kind of optimisation that
produces a confident wrong number, so the two loops were made to agree on input
they can share: the 27,969 discrete plants of the `assembly10` dump, which are
exact and unsampled in both, through the same camera. **Ground cover is excluded
from the cross-check on purpose** — the dump voxelises it, so any disagreement
there would be unattributable.

**It failed twice before it passed, both times low, and both are the reason this
file exists rather than a note saying the loop was reviewed:**

1. **The cull tested RANGE against a limit derived from DEPTH.** Recognisable
   means `depth ≤ h·s/px_min`; culling on `range ≤ h·s/px_min` looks equivalent
   because `depth ≤ range`, but the implication runs the wrong way — an
   in-frustum point at 100 m depth is at 152 m RANGE at the edge of an 18 mm
   frame. **102 of 120 comparisons disagreed, every one of them low**;
   `tree:birch_L2` at ≥ 32 px read 572 against 866. The factor is exact and
   lens-dependent: `√(1 + (X/2s)² + (Y/2s)²)`.

2. **The running maxima were updated inside the height-bucket loop.**
   `instance_plants()` randomises every tree's target height, so ONE source mesh
   has instances in two or three height octaves, and per-bucket updates take the
   MAX of the partial counts where the truth is their SUM. **92 of 120
   disagreed**, `tree:plane_L0` reading 17 against 26.

After both fixes:

```
  ok  CLAIM 1  peak_covisible agrees EXACTLY on all 120 comparisons  [0 disagree]
  ok  CLAIM 2  instance_variety's sharp count is NEVER lower         [0 lower]
  ok  CLAIM 3  emulating the reference's tracker reproduces its published
               numbers EXACTLY, so the gap is its tracker            [0 differ]
```

#### 4a. R2-3737 — and CLAIM 3 is a defect in `r2_3421_covisible_repeats.py`. **Proposed for the log.**

`tools/r2_3421_covisible_repeats.py` tracks the busiest sharp frame with

```python
bsharp = {p: dict(n=0.0, f=0, sharp=0.0) ...}
...
if ns > bsharp[thr]["n"]:                        # ns is a SHARP count
    bsharp[thr] = dict(n=n, f=f + 1, sharp=ns)   # n is the TOTAL
```

— it compares this frame's **sharp** count against the stored frame's **total**.
Since total ≥ sharp always, a later frame can only displace an earlier one by
beating its TOTAL, so **the tracker reports a lower bound on the peak sharp
count, not the peak.** Not asserted: the same loop was run a second time with
`sharp_tracker="r2_3421"` and **reproduced that tool's published numbers exactly
on all 120 comparisons**, which is what makes the mechanism the explanation
rather than a story about it.

It under-reports on **26 of 120** comparisons. The largest movements:

| pool | rung | published | corrected |
|---|---|---:|---:|
| `tree:willow_L1` | ≥128 px | 12 | **49** |
| `tree:poplar_L1` | ≥256 px | 3 | **24** |
| `tree:poplar_L2` | ≥128 px | 65 | **95** |
| `tree:oak_L2` | ≥256 px | 74 | **94** |
| `tree:oak_L1` | ≥32 px | 332 | **388** |

**The R2-3421 headline is NOT affected.** `tree:oak_L2` at ≥ 128 px is 347 both
ways, i.e. cvrr **21.7** on the delivered camera against the 20.7 published on
the orphan `camera_rig_path.json` — a camera difference, not a tracker one. The
conclusion "the worst number in the film is ~20 against a named failure of 100"
survives the correction.

**`tools/r2_3421_covisible_repeats.py` IS NOT EDITED.** It is held by
`r2-3421-variety`'s lease, and a lease I do not own is not mine to release. The
defect is reported and the file is left alone. **It needs one line changed by
its owner:** `if ns > bsharp[thr]["sharp"]:`.

---

### 5. The exemption table matched nothing, and that is a finding too

Removing the `is_instance` filter could reveal hardware that is identical by
manufacture and by regulation — armco panels, splice bolts, tyre walls — and a
gate that fails on 4,675 identical bolts has mistaken engineering for laziness.
So the gate carries an explicit, printed, reasoned exemption table rather than
the predecessor's `VEG_*` scope restriction disguised as a family key.

**Measured: it matched 0 of the 1,838 repeated source meshes.** The barrier
hardware in this world is MERGED GEOMETRY — all **131** `BR_*` source meshes
have exactly **one** user each — so it never enters the repeat metric at all.
The table is kept, because the failure it guards is real for a world that does
place hardware as duplicates, and the gate now **prints how many meshes it
matched** so a table that has quietly stopped applying cannot go on looking like
it is doing something.

**The crowd is also measured for the first time**, and it is clean: 746 repeated
`SPECX_*` meshes, 12,029 instances, worst **3** co-visible sharp copies.

#### 5a. And the one silent drop the gate could have had, named and counted

`HOST_DIAG_M` (200 m) keeps 2.5 km scatter hosts out of the height buckets. A
host has one user, so `MIN_USERS` already excludes it — but a genuinely
*repeated* mesh that large would leave the metric without a word, which is this
project's most-repeated defect shape. The gate now computes and prints it:

```
host-diagonal filter: 102 source mesh(es) exceed 200 m and NONE of them is
repeated, so nothing was dropped by it.
```

Measured, not assumed. Had any been repeated the report would carry them under
`repeated_but_larger_than_host_diag` and the run would say **"this is a hole,
not a pass."**

---

### 6. THE TREES, MEASURED. And the reed grass, which is why the gate says SPAM.

`docs/instance_variety.json`, `assembly15` against `render/film24_path.json`
(sha16 as recorded in the report), 2,977 frames, stride 1, 47 s:

| ≥ px of the 4K frame | worst source mesh | co-visible **sharp** | frame |
|---|---|---:|---:|
| ≥ 32 | `VEG_grass_reed_F03_u` | 832 | 2341 |
| ≥ 64 **(verdict row)** | `VEG_grass_reed_F03_u` | **300** | 2340 |
| ≥ 128 | `VEG_tree_oak_L2_15` | **30** | 2218 |
| ≥ 256 | `VEG_tree_oak_L2_15` | **13** | 2343 |

**The trees, which have never been measured by this instrument in the history of
the project:**

| source mesh | instances | ≥64 px sharp | frame | ≥128 px | ≥256 px |
|---|---:|---:|---:|---:|---:|
| `VEG_tree_oak_L2_06` | 266 | **45** | 1222 | 19 | 4 |
| `VEG_tree_oak_L2_12` | 267 | 39 | 200 | 26 | 6 |
| `VEG_tree_oak_L2_04` | 263 | 39 | 1222 | 24 | 4 |
| `VEG_tree_oak_L2_15` | 285 | 37 | 200 | **30** | **13** |
| `VEG_tree_pine_L2_12` | 156 | 31 | 1246 | — | — |
| `VEG_tree_poplar_L2_09` | 116 | 30 | 820 | — | — |

**The worst tree in the film is 45 against a named failure of 100, and it is an
upper bound that subtracts no occlusion.** It reconciles with R2-3421's
pool-level estimate to a degree worth stating: that pass measured the `oak_L2`
POOL at 507 co-visible sharp at ≥64 px over a library of 16, i.e. an expected
**31.7** per mesh with a binomial 99th percentile of ≈ **47.5**. The measured
per-mesh maximum is **45**. The estimator was sound; it just could not name the
mesh.

#### 6a. The gate FAILS `assembly15`, on reed grass, and here is exactly what that is

```
>> 5 SOURCE MESH/MESHES REACH THE NAMED FAILURE: 100 co-visible SHARP copies
     VEG_grass_reed_F03_u  300 copies at f2340  (13,716 instances in the world)
     VEG_grass_reed_F01_u  298 copies at f2341
     VEG_grass_reed_F00_u  292 copies at f2340
     VEG_grass_reed_F02_u  266 copies at f2340
     VEG_grass_reed_F04_u  241 copies at f2340
>> STAGE RESULT: INSTANCE_VARIETY_SPAM
```

**The number is right.** Independently recomputed by brute force over all 13,716
instances of `VEG_grass_reed_F03_u` at f2340 with no grid, no buckets and no
cull: 354 in frame at ≥ 64 px, **300** of them sharp. And the heights are
measured, not assumed — `build_terrain.GRASS_PROF["reed"]["h"] = (0.9, 1.9)`,
and the census reads reed_F instances at min 0.80 / median **1.74** / max 2.88 m.

**This is a correction to R2-3421's grass rows.** That pass used class
representative heights — 0.95 m for reed, the midpoint of the emitter's range —
because the point dump carries no per-clump bbox, and it explicitly flagged the
sensitivity: *"doubling the assumed height moves the answer from the ≥128 px row
to the ≥64 px row."* For `reed_F` the real median is **1.8× the assumed
midpoint**, and that is exactly what happened.

**And what those 300 reeds are in the delivered frame is the other half of the
answer.** At f2340 the lens is 89.2 mm and the counted reeds are **182–387 m
away**, subtending 64–106 px of the 4K frame (16–26 px of the proxy) — **not one
of them reaches 128 px, anywhere in the film.** Looked at, not assumed
(`work/r23721/f2340_reedband_2x.png`, `f2340_reedzoom_4x.png`, cropped from the
free proxy — no credit spent): **the band the reeds occupy is behind the pit
wall and dissolved in heavy haze.** There is no repeated silhouette in it
because there is no silhouette in it. This instrument subtracts neither
occlusion nor atmospheric extinction, by design, and this is that bound doing
its job in the direction it was built to err.

#### 6b. What I have NOT done, and why it is your call

The verdict row is `RECOG_PX = 64`, **inherited unchanged** from
`r2_3421_covisible_repeats.py`. Moving it to 128 — where R2-3421 argued a
silhouette first becomes genuinely readable, and where every grass pool is zero
and the worst thing in the film is a tree at 30 — would turn this FAIL into a
CLEAN.

**I have not moved it.** You told me not to recalibrate `top_share` but to
replace it, and quietly picking a comfortable threshold for the replacement is
the same mistake wearing the new measure's clothes; it is also precisely the
`NCC_HIT = 0.90` error this project already made once and had falsified by its
own ladder. So the gate ships firing, the ladder is printed in full, and the
ruling is yours:

* **the honest case for 128 px** — a 0.99 m reed at 200 m through 89 mm of lens
  is 64 px of a 4K frame and, in the delivered pixels, behind a wall and inside
  haze. "One tree spammed 100 times" is about copies you can *recognise*.
* **the honest case for keeping 64 px** — the threshold was not chosen with this
  result in view, and changing it now, because of this result, is choosing it
  with this result in view.

A third option, and the one I would take if it were mine: **leave the row at 64
and subtract occlusion**, which is the assumption that is actually doing the
damage here rather than the threshold. `screen_presence.py` already rasterises a
depth buffer from the point cloud for exactly this. That is real work, not a
threshold move, and it is not in this task's scope.

---

<!-- ITEM 2 (#159) -- the beat-1 re-sweep against render/film24_path.json --
     lands here. -->
