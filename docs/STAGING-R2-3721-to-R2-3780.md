# STAGING R2-3721 .. R2-3780

## R2-3721..R2-3736 — task #162: the variety gate now sees the trees, and the trees are measured for the first time

**VERDICT: the gate is repaired, the trees are measured, and `assembly15` is
CLEAN. With occlusion subtracted (§6b, coordinator ruling) the worst repeat in
the film is `VEG_grass_reed_F00_u` at 52 co-visible sharp copies at ≥ 64 px, and
the worst TREE is `VEG_tree_oak_L2_05` at 35 at ≥ 64 px and
`VEG_tree_oak_L2_15` at 26 at ≥ 128 px — against the named failure of 100.**

**`RECOG_PX` was NOT moved.** The gate first returned `INSTANCE_VARIETY_SPAM` on
five reed-grass meshes at 241–300 copies; those reeds are 182–387 m out behind
the pit wall, and subtracting occlusion removes 82–85 % of them while removing
only 0–31 % of the trees. §6b is that measurement and the six defects the
control found before it could be trusted.

Files: `tools/instance_variety.py` (rewritten),
`tools/r2_3721_variety_gate_control.py` (new, **25 checks**),
`tools/r2_3721_sweep_crosscheck.py` (new, 3 claims),
`tools/gate_exit_selftest.py` (contract updated),
`tools/r2_3421_covisible_repeats.py` (R2-3737 tracker fix, §4a),
`docs/LIVE-CAMERA.md` (film24 declared, R2-3742),
`render/world/assembly/r2/v12{0,1,2}/battery.sh` (`--path`, R2-3743).
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

> **R2-3743 — CLOSED by coordinator instruction.** The three
> `render/world/assembly/r2/v12{0,1,2}/battery.sh` invoked this gate without
> `--path` and would have got VACUOUS(3) rather than a verdict. They now pass
> `--path $R2/render/film24_path.json` for the world scene and a generated
> control camera for the two control blends. A battery that returns VACUOUS is
> a battery nobody will read.

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

**R2-3737 — LANDED.** The file was held by `r2-3421-variety`'s lease and was
left alone until the coordinator released it; **the finding and the file are
that agent's work, the correction is mine.** The one line is now
`if ns > bsharp[thr]["sharp"]:`. Re-running it moves **45 rows**, worst
`VEG_grass_reed_F` at ≥ 32 px from 1,403.7 to 2,742.5 — and `tree:oak_L2` at
≥ 128 px is **347 either way**, so the R2-3421 headline stands.

**And the closure is exact:** with the fix in place the cross-check's two
independently written loops agree on **all 120 comparisons, peak AND sharp**.
CLAIM 3 now demands that the reference be *accounted for* — either pre-fix, in
which case emulating its tracker reproduces it exactly, or post-fix, in which
case the two loops agree outright. Both arms were run and each holds on its own
report. A reference matching neither would be a third behaviour nobody had
accounted for, and that is what the arm refuses.

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

#### 6b. R2-3740..R2-3746 — OCCLUSION SUBTRACTED. **The gate is CLEAN, the trees barely move, and the reeds fall.**

**Coordinator ruling: subtract occlusion, do NOT move `RECOG_PX`.** Co-visible
means visible together; an instance the audience cannot see is not a repeat of
anything, so counting an occluded mesh is a defect in the measure rather than a
strictness setting. `RECOG_PX` is still the inherited **64**.

Subtracting occlusion can only ever LOWER a count, so it will read as a
weakening to anyone looking at the diff. It is not, and here is the proof in one
table — the same run, both ways:

| source mesh | ≥64 px sharp, **no occlusion** | **occlusion subtracted** | removed |
|---|---:|---:|---:|
| `VEG_grass_reed_F03_u` | 300 | **45** | 85 % |
| `VEG_grass_reed_F01_u` | 298 | **48** | 84 % |
| `VEG_grass_reed_F00_u` | 292 | **52** | 82 % |
| `VEG_grass_reed_F02_u` | 266 | **43** | 84 % |
| `VEG_grass_reed_F04_u` | 241 | **40** | 83 % |
| `VEG_tree_oak_L2_06` | 45 | **31** | 31 % |
| `VEG_tree_oak_L2_05` | 36 | **35** | 3 % |
| `VEG_tree_oak_L2_15` (≥128 px) | 30 | **26** | 13 % |
| `VEG_tree_oak_L2_15` (≥256 px) | 13 | **13** | **0 %** |

**The reeds lose 82–85 % and the trees lose 0–31 %.** That is the shape a
correct occlusion pass has to have here: the reeds were behind the pit wall and
the trees were not. A change that had merely lowered everything would have
lowered them together.

```
recog px    worst source mesh              SHARP    frame      (no occlusion)
>= 32       VEG_grass_reed_F03_u             140     2341      832
>= 64       VEG_grass_reed_F00_u              52     2337      300
>= 128      VEG_tree_oak_L2_15                26     2340       30
>= 256      VEG_tree_oak_L2_15                13     2343       13
>> STAGE RESULT: INSTANCE_VARIETY_CLEAN
```

**The worst repeat in the film is now 52, against the named failure of 100, and
the worst TREE is 35 at ≥64 px and 26 at ≥128 px.** The client's number is
comfortable and it always was.

##### What the occluder set is, and which way every error in it points

The shell is **7,943,063 surface points at 1.5 m from 2,191 objects** —
terrain, track, kerbs, barriers, walls, grandstands, buildings, bridges: every
real object whose mesh has one user. Deliberately conservative in four separate
places, so the subtracted count is still an **upper bound**, just a tighter one:

* **Repeated instances do not occlude each other.** A tree behind a tree still
  counts. That is the case the red line is actually about.
* **`OCC_TOL_M` = 0.75 m**, so a plant is not occluded by the ground it stands on.
* **Subjects beyond the shell's reach are counted visible without a test** —
  65,807 of 13,736,766 subject tests, **0.479 %**, reported by the run itself.
* **The shell is clipped to the camera corridor ±1,500 m.** That is not an
  approximation: an occluder must be *nearer* than what it occludes, and
  `assembly15`'s terrain is a 22 km × 22 km landscape of which **93 % is beyond
  any possible occluder distance** (64.5 M points → 7.9 M).

The one bias in the other direction, stated rather than hoped away: the mip
reconstruction dilates an occluding surface by up to two sample spacings **at
its silhouette edge**, so a subject within ~3 m of the *end* of a wall may be
called occluded when a sliver of it shows. Everywhere that is not an edge —
which is all of a pit wall except its ends — the reconstruction is exact.

##### R2-3741..R2-3746 — the control failed FIVE times, and every failure was a real defect

Arms G and H of `tools/r2_3721_variety_gate_control.py`: G is the grove of 40
with occlusion on and **nothing in the way** — it must still see 40. H is the
same grove, same camera, with a **two-triangle wall** between the lens and the
trees — it must fall, and its *unsubtracted* count on the same run must still
read 40, so that it is shown to have fallen because of the wall and not because
the measurement stopped working.

| # | what the control saw | the defect behind it |
|---|---|---|
| 1 | shell = 55,979 points for a 2.5 km world | `HOST_DIAG_M` applied to *every* object threw out `SURF_Track` (1,688 m), the terrain and all 131 `BR_*` armco runs — **it threw out the pit wall.** The host test is size **and** being vegetation. |
| 2 | 38 GB of swap, run stopped by task id | the sampler materialised one object's entire sample set before deduping. A few thousand 50 m terrain triangles are ~1,100 samples each. Now batched at 400 k. |
| 3 | **40 of 40 trees through a solid wall** | a splatted point is not a surface: 1.5 m at 30 m is 67 quarter-res pixels, so 203 wall samples filled 55 of the ~387,000 they cover — a buffer 99.98 % holes. |
| 4 | **35 of 40** through the wall | the query footprint was taken from the **subject's** depth; an occluder is nearer and has a *larger* footprint. Replaced with a mip pyramid, each sample splatted at its own footprint. |
| 5 | **40 → 33 in an empty field** | the probe was the instance **origin**, and `instance_plants()`/`gn_kind()` put a plant's origin **on the ground** — so every plant was occluded by the earth it stands on. Now probed at mid-height. |
| 6 | **5 of 40** through the wall | random samples do not cover a grid: drawing `area/cell²` uniform points leaves **1/e = 37 %** of cells empty. Now ×6 oversampled before dedupe (99.75 % coverage). |

```
ARM G -- occlusion ON, nothing in the way
  ok   with occlusion ON the gate STILL sees all 40 trees
  ok   and the unsubtracted count is the same 40, i.e. nothing was hidden
  ok   gate still returns PASS(0)
ARM H -- the SAME grove, a two-triangle wall between lens and trees
  ok   the walled shell has more points than the open one
  ok   behind the wall the gate sees 0 of the 40 trees
  ok   and that is at least a 10x reduction, i.e. the wall did the work
  ok   and it fell BECAUSE OF THE WALL: the unsubtracted count is still 40
25/25 checks passed          >> STAGE RESULT: IV_GATE_CONTROL_OK
```

**A seventh defect, in the control itself:** `run_gate()` did not delete the
report before running, so a *crashing* arm was graded on the previous arm's
json and passed. It deletes it now. A stale report is a pass nobody earned.

##### The threshold was NOT moved, and that is the point

`RECOG_PX` is 64, exactly as inherited. Had it been moved to 128 the FAIL would
also have gone away — and the number would have meant less while reading the
same. The reeds fall because the pit wall is between them and the lens, which
is a fact about the world, not about where a line was drawn.

---

#### 6c. Superseded: what §6b replaces

**The rest of this section records the state BEFORE occlusion was subtracted**
and is kept because the ruling turned on it. The 300-copy reed FAIL below is
real as an unoccluded count — it is the `no-occ` column of the table in §6b —
and the frames referenced are still the right frames to look at.

#### 6d. What I had NOT done, and why it was your call

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

### R2-3747 — the five skipped items: what shipping without them costs

Asked for cheaply from what item 2 already measured
(`work/r23721_item2/a9_film24_item_presence.json`, delivered camera, 2,978
frames at 24 fps). "Sharp+unoccluded" is the only column worth ranking on — it
is the frames on which the thing is both resolvable and actually in view.

| item | visible f | **sharp+unocc f** | = seconds | peak px (was) | where it peaks |
|---|---:|---:|---:|---|---|
| `exterior_ground_apron` | 1,464 | **354** | 14.8 s | **495.8** (151.6) | beat 1, f282 |
| `farm_gate` | 2,257 | **719** | 30.0 s | 157.5 (157.4) | beat 5, f122 |
| `grandstand_debris_fence` | 1,112 | **248** | 10.3 s | 179.8 (118.2) | **f2978 — the last frame** |
| `podium_backdrop` | 1,112 | **248** | 10.3 s | 189.6 (131.4) | **f2976** |
| `podium_structure` | 1,112 | **248** | 10.3 s | 165.9 (114.9) | **f2976** |

**The apron is the one that counts, and for a reason beyond its 3.3× jump.**
`exterior_ground_apron` and the **already-built** `forecourt_paving_bay` share a
host set and measure *identically* — 1,464 / 354 / 495.8 px, peaking in beat 1 at
f282 where their host reaches 1,061 px. So it is not merely a BULK item that
crossed a line: **it is the unbuilt twin of a module that was already judged
worth building, on the same surface, in the opening shot.** Shipping without it
means half of that surface is dressed and half is not.

**`farm_gate` has the most screen time and the least reason to worry** — 30
seconds sharp and unoccluded, but it peaks at 157.5 px against 157.4 before, i.e.
**it crossed the tier line on frame count, not on size.** It is a background
silhouette for the whole of beat 5. Cheapest of the five to skip.

**The three grandstand/podium items are one decision, not three.** Identical
1,112 / 248 / f2976–2978, same host set. 10 seconds each — but those seconds are
the **closing frames of the film**, at the longest lens, and in a single
unbroken take the last image is the one that is remembered. They are also the
only three of the five whose peak lands in beat 6.

**If only one is built: `exterior_ground_apron`.** If two: add the podium group
as a single pass. `farm_gate` last.

*(Caveat carried from item 2 §"The one thing this measurement is NOT": these are
`assembly9` presence numbers with the world held fixed, which is what makes the
diff a camera diff. They are not the shipping world's absolute numbers.)*

## R2-3721 item 2 (defect #159) — THE TIERING DOES MOVE, AND MOSTLY NOT IN BEAT 1


### The premise needed one correction before it could be tested

The brief says `docs/screen_presence*.json` was swept against
`world/camera_rig_path.json`. That is true of the **filename** and false of the
**bytes**, and the difference is the whole of R2-1007 wearing a new coat.

`work/w2_0/retier_a9/inputs.json` stamps `camera_path` sha256 `f1c65c46…`.
That hash is `render/film13_path.json` = `render/film14_path.json` = **git
HEAD's copy of `world/camera_rig_path.json`**. The working-tree copy carries
`d9c8f5c5…` (film16's bytes) and acquired them at 2026-08-04 15:49 — **fourteen
hours after the 01:49 sweep**. The sweep's own `campos` array settles it
independently of any stamp: it reproduces `render/film14_path.json` to
**5 micrometres** and today's `world/camera_rig_path.json` only to **8.86 m**.

So the orphan that actually produced the delivered tiering is **film14's
bytes**, and a re-sweep pointed at `world/camera_rig_path.json` today would have
compared the wrong pair. Every arm below uses `render/film14_path.json` as the
baseline camera and says so.

### The diff, reproduced and then corrected

The R2-3243 C4 metric — `|Δp| > 1e-6 m`, `|Δlens| > 1e-6 mm`, and
`max |Δq_i| > 1e-6` on the **raw stored** quaternion components — reproduces
exactly against `film22`:

```
world/camera_rig_path.json vs render/film22_path.json
  position    1142/2978   max 21.3991 m  @f2177
  lens        1065/2978   max 55.9962 mm @f2978
  orientation 2516/2978   (raw components)
```

**1,142 / 1,065 / 2,516 confirmed.** Two riders on it:

* The **orientation** count is on raw six-decimal components with no
  re-normalisation and **no sign fix**, so it counts rounding noise and
  double-cover sign flips as differences. The R2-103-safe geodesic angle gives
  **1,023** frames above 0.2°, not 2,516. The *maxima* are unaffected.
* The **maxima are not beat 1's.** 21.40 m is at **f2177** and 56.00 mm at
  **f2978** — beat 5 and beat 6. Beat 1's own worst is 9.85 m / 23.00 mm.

Against the camera this task is actually about, and from the baseline the docs
were actually swept from:

```
render/film14_path.json vs render/film24_path.json      (C4 metric)
  position    2347/2978   max 21.4339 m  @f2176
  lens        2129/2978   max 55.9962 mm @f2978
  orientation 2708/2978   raw   |   2456/2978 above 0.2 deg geodesic, max 179.52 deg @f87
  divergent (1 mm / 1 um / 0.2 deg): 2498 frames
      inside beat 1 (f1-792)   753 of 792   worst  9.79 m / 28.64 mm / 179.52 deg
      outside beat 1          1745          worst 21.43 m / 56.00 mm /  78.75 deg
```

**Beat 1 is 753 of 792 frames divergent — the brief's "essentially the whole of
beat 1" is right. What the brief omits is that 1,745 further frames outside
beat 1 also diverge, and they carry the larger numbers.** That omission turns
out to be the finding.

### The answer: 17 items change tier, and only 5 of them peak in beat 1

Camera-only re-derive: same point cloud (`work/w2_0/retier_a9/world_points.npz`,
assembly9 — the world the delivered docs were swept from), same
`screen_presence.py --uniform-shutter`, same `tools/item_presence.py`, same
`work/w2_0/tier_delta.py` R2-1275 used. The baseline re-derived through today's
`item_hosts.py` reproduces `docs/screen_presence.json` **item for item, 435 of
435, zero tier differences** — so the chain being diffed is the chain that made
the delivered file.

```
                   HERO   MID   BULK
  orphan (film14)    69    58    308      <- docs/screen_presence.json
  DELIVERED film24   71    57    307
  delta              +2    -1     -1

  wave-2 build set (unbuilt HERO+MID)   109 -> 111
  agents per round (agents_per_round.py) 149 -> 151
  FRAME-peeps (frame_peeps.py)            29 ->  28
```

**The one confound in reusing the 08-04 baseline npz was checked, not assumed.**
The baseline arm reuses `work/w2_0/retier_a9/sp_points.npz` as it was written on
2026-08-04, so if the sweep code had changed since, "camera-only" would be false.
`git show 2675a06:tools/screen_presence.py` and `git show 68f94cc~1:…` hash
identically (`a166a669…`) — the measurement half of the tool did not change
between the baseline sweep and today's arms. `item_presence.py` and
`item_hosts.py` **have** changed since, which is why both arms were re-derived
through today's copies rather than one arm being read off `docs/`; that
re-derivation reproduces `docs/screen_presence.json` 435 of 435.

The aggregate barely moves. **The rows move: 17 of 435 items change tier**, and
`tier_delta.py`'s own partition arm fires — `PARTITION_REFUTED` — because
**12 of the 17 peak outside beat 1**.

```
  PEAK INSIDE beat 1 — 5
    exterior_ground_apron     BULK -> MID    f153   151.6 px   showroom_breach
    farm_gate                 BULK -> MID    f154   157.4 px   vegetation
    forecourt_paving_bay      BULK -> MID    f153   151.6 px   showroom_breach   BUILT
    media_centre_building     MID  -> HERO   f154   801.0 px   paddock
    medical_centre_building   MID  -> HERO   f154   629.3 px   paddock

  PEAK OUTSIDE beat 1 — 12
    apron_wall_panel          MID  -> HERO   f910   514.5 px   transit_corridor
    big_screen_tower          MID  -> HERO   f2572  328.4 px   crowd
    grandstand_debris_fence   BULK -> MID    f2572  118.2 px   grandstand
    podium_backdrop           BULK -> MID    f2572  131.4 px   crowd
    podium_structure          BULK -> MID    f2572  114.9 px   crowd
    grass_clump_reed          HERO -> MID    f2316  383.2 px   vegetation
    pont_abutment             HERO -> MID    f2191  718.5 px   bridges
    hoarding_leg              MID  -> BULK   f1559  269.0 px   trackside
    marshal_broom             MID  -> BULK   f2321  247.6 px   trackside
    marshal_figure_flagging   MID  -> BULK   f2321  309.5 px   trackside
    marshal_post_column       MID  -> BULK   f2175  162.1 px   trackside         BUILT
    pont_girder               MID  -> BULK   f2191  242.5 px   bridges           BUILT
```

**So the framing in the brief — "beat 1's item priorities" — is the smaller half
of the defect.**

That is not an inference from the peak-frame column; it is measured directly, by
a third arm. `ctl_k100_path.json` is film24 everywhere **except** beat 1, where
it is the orphan — so diffing it against each end splits the swap in two, and
the two halves are byte-identical outside the span each is meant to test:

```
                                          HERO  MID  BULK   items changing tier
  orphan everywhere (docs baseline)         69   58   308
  orphan in beat 1, film24 outside          68   57   310   11  (all outside beat 1)
  film24 everywhere                         71   57   307    6  (5 inside beat 1)
                                                            ---
                                          total                17
```

**11 of the 17 tier moves are caused by the part of the camera change that is
not in beat 1**, and 6 by beat 1. The two contributions are exactly additive at
the tier level — 11 + 6 = 17, no interaction — so neither is masking the other.
The 11 come from the beat-5 re-pace and the beat-6 closing lens that film24
carries, which were never part of the R2-1007 story. The one item in the beat-1
half whose *peak* is elsewhere, `apron_wall_panel` (peak f910), crosses the
HERO line on beat-1 frames it does not peak on — which is why the peak-frame
partition is a heuristic and `tier_delta.py` is right to report it as refuted.

### And the swap is two changes, not one — which matters for the proxy

`film22` (== the bytes `docs/LIVE-CAMERA.md` still declares, and the camera
`work/r22161_proxy/`'s 2,978 frames were actually rendered from) sits between
the orphan and film24, so the swap splits into the R2-3243 defect and the newer
re-pace:

```
                                             HERO  MID  BULK   moved  build set
  orphan (film14)  — docs/screen_presence.json  69   58   308            109
  film22           — the R2-3243 defect, and    73   60   302     12     115
                     the camera the proxy has
  film24           — delivered                  71   57   307      7     111
  orphan -> film24 net                                            17     111
```

Two things fall out. **12 + 7 = 19 against a net of 17**, so two items move and
move back — a tier that agrees at the ends is not evidence that nothing happened
in between. And the **film22 tiering (73/60/302, build set 115) is the one that
matches the only rendered pixels in existence**; anything joining presence
numbers to proxy frames should use that arm, not film24's and not the docs'.
All 7 of the film22 → film24 moves peak outside beat 1.

### Built that shouldn't have been, skipped that should have been

Read against the **delivered** camera, with BUILT defined as `world/items/*.py`
whose stem is a manifest id (36 modules), exactly as `WAVE2-SCOPE.md` §1.1 does:

**Built on a tier the delivered camera does not support — 2.**

* `marshal_post_column` — MID under the orphan, **BULK** under film24
* `pont_girder` — MID under the orphan, **BULK** under film24

Both have a dedicated module; under the delivered camera both belong in the
class-level W2-D pass. (Seventeen further built items are BULK under *both*
cameras — that is a scoping question, not this defect's.)

**Skipped that should have been built — 5**, all BULK under the orphan and
therefore never in the wave-2 build set at all:

* `exterior_ground_apron` — 151.6 → **495.8 px** (+227 %)
* `farm_gate` — 157.4 → 157.5 px (it crossed on frame count, not size)
* `grandstand_debris_fence` — 118.2 → 179.8 px
* `podium_backdrop` — 131.4 → 189.6 px
* `podium_structure` — 114.9 → 165.9 px

**Would have been wasted — 3**, unbuilt items in the build set under the orphan
that the delivered camera puts in BULK: `hoarding_leg`, `marshal_broom`,
`marshal_figure_flagging`.

**Budgeted at the wrong depth — 6.** MID → HERO (needs macro history nobody
budgeted): `apron_wall_panel`, `big_screen_tower`, `media_centre_building`,
`medical_centre_building`. HERO → MID (budgeted macro history it does not
need): `grass_clump_reed`, `pont_abutment`.

### The number that moved far more than the tier — px/m

`WAVE2-SCOPE.md` §2.6's R2-634 note already wrote the correct warning for a
*smaller* camera swap than this one:

> TIER ASSIGNMENT IS ROBUST TO THE CAMERA. `px_per_m` IS NOT, AND `px_per_m` IS
> WHAT AGENTS ACTUALLY BUILD AGAINST. — 1 of 560 objects changed tier, 14 of 560
> moved `px_per_m` by more than 10 %.

On this swap, on the same field (`peak_unocc_sharp_px_per_m`, 560 objects):

```
  moved > 10 %                          322 of 559
  moved by 2x or more                    76 of 559
  lost a sharp unoccluded peak entirely  49
  gained one                              1
  |log2 ratio|   p50 0.170   p90 1.283   max 4.184
```

**322 of 559, against R2-634's 14.** Extremes: `DR_Apex_022` 7.5 → 135.7 px/m,
`DR_TVCam_11` 7.5 → 134.6, `BR_Runoff_R` 76.7 → 405.0, `SURF_Kerb_T11_out1`
76.2 → 347.6. Of the 36 items that already have modules, **11 have a detail
budget that moved by more than 25 % and 4 by more than 2×** — `forecourt_paving_bay`
151.6 → 495.8 px (+227 %), `pont_deck_slab` 3.7 → 11.5, `kerb_precast_unit`
11.7 → 26.1, `asphalt_wearing_course` 3.3 → 7.0. The 49 that lose every sharp
unoccluded moment are the dressing and grid-number families —
`DR_Marker_021` 176.8 → 0, `BR_TecPro_R11` 157.3 → 0, `DR_Apex_023` 93.0 → 0,
and eleven `SURF_GridNum_*`.

**And the same split says this is not beat 1's doing either:**

```
                            objects >10 %   >2x   lost sharp peak entirely
  BEAT 1 ALONE                     2         1              0
  BEATS 2-6 ALONE                320        75             49
  both together                  322        76             49
```

**Beat 1's camera change is the larger one in metres and degrees — 9.8 m and
179° against 21.4 m and 79° — and it barely touches the detail budget at all**,
because it re-frames the same forecourt at similar scale. `ARCH_Paving_Forecourt`
476.7 → 1049.4 px/m is essentially beat 1's whole contribution. The beat-5
re-pace and beat-6 closing lens are what redistribute the film's resolution.

**The tier count is the reassuring number and it is the wrong one to read; and
"beat 1" is the wrong span to read it over.**

### The controls, and what each of them was watched to do

A comparison that cannot report a difference is not evidence of no difference —
and equally, one that reports differences for any input is not evidence of one.
Both failure modes were tested.

**C1 — the null.** `tier_delta.py` fed the baseline against **itself**:
`moved=0 inside_beat1=0 outside_beat1=0`, `PARTITION_HOLDS`. The tool does not
manufacture moves.

**C2 — dose-response, on a control camera that is a measured FRACTION of the
real defect.** `ctl_kNNN_path.json` is film24 with beat 1 pulled a fraction *k*
of the way back to the orphan — position lerped, lens lerped, orientation
slerped — and byte-identical to film24 everywhere else (verified: max
0.000000 m / 0.000003° outside beat 1). Injecting that error into the delivered
camera and re-running the whole chain:

```
  k = 0.00   beat-1 error 0.00 m / 0.00 deg      0 items change tier
  k = 0.10                0.98 m / 17.95 deg     3
  k = 0.25                2.45 m / 44.88 deg     5
  k = 1.00                9.79 m / 179.52 deg    6      <- the real defect
```

**Monotone, and it resolves a tenth of the defect.** So when the beat-1 half of
the swap is reported as 6 tier moves, that is a measured 6 and not a floor the
instrument could not see below.

**C3 — the code was not the variable.** The measurement half of
`screen_presence.py` hashes identically at the 08-03 baseline commit and at
today's parent commit, so reusing the 08-04 baseline npz does not smuggle a code
change into a camera diff (above).

**C4 — the guard added to `screen_presence.py`**, 9 arms, 4 of which must fail
(below).

**C5 — the answer is not an artefact of assembly9.** The whole pair was re-run
on the assembly10 dump (`work/w2_0/retier_a10/world_points.npz`, 2,261 objects
against assembly9's 560, and 4 items resolving as SELF rather than via a class
host):

```
                        assembly9   assembly10
  items changing tier        17          16
    peak inside beat 1        5           5
    peak outside beat 1      12          11
  wave-2 build set    109 -> 111   109 -> 112
  objects px/m > 10 %  322 / 559  1163 / 2261
  objects px/m > 2x     76 / 559   276 / 2261
```

**Fifteen of the sixteen assembly10 moves are the same items, in the same
direction.** The one that does not move on assembly10 is `hoarding_leg`
(MID → BULK on assembly9 only). Every named finding below survives the world
change.

**And one control failed usefully during the run.** `item_presence.py` was fired
at one arm's npz a second before that arm's `sp_objects.json` had been written,
and it printed `>> STAGE RESULT: item_presence_CRASH` instead of quietly
producing a record with no `MEASURED_AGAINST`. That is the R2-097 shape being
caught by the instrument built for it.

### What to do about it, in the order it matters

1. **Do not re-tier through `tools/retier.sh` until `docs/LIVE-CAMERA.md`
   declares film24.** The script resolves its camera through
   `live_campath.load()` and takes no camera argument on purpose, so today it
   would re-tier against film19. One deliberate edit to the declaration, by
   whoever owns the film24 promotion, unblocks it.
2. **Re-stamp the detail budgets before any more item work is authored.** 322 of
   559 objects moved more than 10 % in px/m and 76 moved by 2×; an item built
   for 477 px/m and filmed at 1049 px/m is built to a quarter of the resolution
   it needs. This is R2-634's warning, one camera generation later and 23× worse.
3. **Nine items need a decision on their tier**: 5 that should have been in the
   build set and were not, 3 that were and should not have been, and the 2 built
   modules the delivered camera puts in BULK.
4. **Beat 1 is not where the correction lands.** If the opening shot is what the
   dressing decision is about, beat 1's re-frame moves 6 tiers and 2 objects'
   detail budgets. The rest of the film moves 11 tiers and 320 detail budgets.

### Four things found on the way that are not this defect

**1. `docs/LIVE-CAMERA.md` is stale again, and this is its third recurrence.**
It declares `render/film19_path.json`. Those bytes (`363e4e88…`) are also
film21, film22 and film23 — so the declaration was accurate until film24 was
built at 2026-08-08 19:21 and did not re-declare. `tools/retier.sh` resolves its
camera through `live_campath.load()` and takes no camera argument by design, so
**`bash tools/retier.sh` run today re-tiers against film19, not film24.** The
gap is real if smaller than the orphan's: film22 → film24 differs on 1,374
frames in position (max 0.264 m), 1,522 in lens (max 7.03 mm) and 1,724 above
0.2° (max 12.05°). R2-1701 logged this same failure for film18; it is now
film24's turn. The file needs one deliberate edit by whoever owns the film24
promotion — it is a decision, not a repair, so this task did not make it.

**2. The `FILM_POSE_FRAMES` non-contamination note no longer holds in
orientation.** R2-3243 scoped its finding by observing that f1547, f2000, f1226,
f1350, f1787, f2622 and f2632 were byte-identical between the authoring camera
and film22, so R2-651 and R2-1036's surface work was safe. Against **film24**
those same frames have moved:

```
  f1547   dp 0.013 m   dlens 0.05 mm   dq  9.658 deg
  f2000   dp 0.004 m   dlens 0.00 mm   dq  6.826 deg
  f1226   dp 0.001 m   dlens 0.00 mm   dq  8.285 deg
  f2225   dp 0.055 m   dlens 0.15 mm   dq  0.721 deg
```

All four `FILM_POSE_FRAMES` are in beat 5 (f1191–f2714) and beat 5 is what
film24 re-paced. Position and lens are still right to centimetres; **the aim is
up to 9.7° different**, which for a grazing-angle surface bed is not nothing.
This is a flag for whoever owns R2-651/R2-1036, not a verdict — and note that
`world/build_surface._film_pose_defs()` reads `world/camera_rig_path.json`
directly, i.e. the orphan, so the bed is not built from film24 either way.

**3. The only rendered pixels that exist for the whole take are film22's.**
`work/r22161_proxy/` was rendered from `render/film22_path.json`
(`tools/r2_2881_pixelpeep.py:76`). film24 has no proxy. Anything that joins
presence numbers to proxy pixels must use film22 for the pixels and say so.

**4. `tools/screen_presence.py` still defaulted `--path` to the orphan.**
Fixed under this task — see below.

### The instrument, and the control that was watched to fail

`tools/screen_presence.py --path` defaulted to `world/camera_rig_path.json`,
which is the file `live_campath.KNOWN_STALE` names by content. **The tool whose
output the item campaign is tiered from shipped with the R2-1007 orphan as its
default camera.** Changed:

* `--path` has **no default**. Omitted, it resolves the live camera through
  `docs/LIVE-CAMERA.md`; there is no route to a camera nobody named.
* A camera in `live_campath.KNOWN_STALE` is **refused** unless `--why-stale
  '<reason>'` is given, mirroring `load_explicit`'s contract.
* The output json now records **`camera_path_sha256`**, plus
  `camera_is_known_stale` / `why_stale`. This is the field that would have
  caught #159 on the day: `camera_path` is a *filename*, and the filename behind
  `docs/screen_presence*.json` stayed `world/camera_rig_path.json` while its
  bytes were replaced fourteen hours after the sweep. A reader comparing by name
  would have concluded they matched.

`ctl_stale_camera.sh` runs nine arms and **four of them must fail**. Re-run by
the lead against the final committed state of the tools:

```
  MUST FAIL: the real R2-1007 orphan, no reason given          ok  rc=1, KNOWN-STALE
    ...and it refused BEFORE reading points or measuring       ok  no npz, no json
  MUST FAIL: a whitespace-only --why-stale is not a reason     ok  rc=1, KNOWN-STALE
  MUST FAIL: the film13/film14 bytes the docs were swept from  ok  rc=1, says defect #159
  MUST FAIL: the same bytes under an innocent filename         ok  rc=1, KNOWN-STALE
  POSITIVE: a stated reason lets the stale sweep run           ok  rc=0
    ...and the OUTPUT records that it was stale                ok  sha=d9c8f5c54ccd1ad8 stale=True
  POSITIVE: no --path resolves docs/LIVE-CAMERA.md             ok  rc=0
    ...and it swept exactly that file                          ok  film19_path.json
  >> STAGE RESULT: SP_CAMERA_GUARD_OK  9 passed, 0 failed
```

The fourth arm is the one that arrived last and matters most: `KNOWN_STALE`
originally named only the *film16* generation of the orphan, and **the bytes
that actually contaminated `docs/screen_presence*.json` are film13/film14's**
(commit `ab0239d`). A guard that named the wrong generation of the same defect
would have passed every other arm here.

The third arm is the one that earns its place: R2-1007's file was already
sitting under the most innocent name in the tree, so a guard that keys on the
filename would have passed every other arm and still missed the defect.

### How to reproduce every number above

```bash
cd ~/f1-round2
# 1. the camera diff, R2-3243's metric and the R2-103-safe one side by side
python3 work/r23721_item2/camdiff.py

# 2. the control cameras: fractions k of the REAL beat-1 change
python3 work/r23721_item2/make_ctl.py 1.00 0.25 0.10

# 3. the arms. World held fixed, camera varied, one at a time under buildlock
bash work/r23721_item2/run_sweeps.sh

# 4. the baseline, re-derived through TODAY's hosts so both sides match
python3 tools/item_presence.py --npz work/w2_0/retier_a9/sp_points.npz \
  --sheet docs/beat_sheet.json --objects work/w2_0/retier_a9/sp_objects.json \
  --out work/r23721_item2/a9_orphan14_item_presence.json \
  --tiers work/r23721_item2/a9_orphan14_tiers_raw.json

# 5. every delta, through the tool R2-1275 used
bash work/r23721_item2/analyse_all.sh a9_film24 a9_film22 a9_k100 a9_k025 \
                                      a9_k010 a10_film14 a10_film24
python3 work/r23721_item2/builtcheck.py \
  work/r23721_item2/a9_orphan14_item_presence.json \
  work/r23721_item2/a9_film24_item_presence.json
python3 work/r23721_item2/objdelta.py work/w2_0/retier_a9/sp_objects.json \
  work/r23721_item2/a9_film24_sp_objects.json --label "orphan -> film24"

# 6. the guard control. Four of its nine arms MUST fail.
bash work/r23721_item2/ctl_stale_camera.sh
```

Artefacts (`work/` is gitignored, so the scripts are tracked and the npz are
not — every number regenerates from the commands above):
`work/r23721_item2/{camdiff,make_ctl,moved,objdelta,builtcheck}.py`,
`work/r23721_item2/{run_sweeps,analyse_all,ctl_stale_camera}.sh`, and per arm
`<arm>_{sweep.log,sp_objects.json,sp_points.npz,item_presence.json,tiers_raw.json}`
plus `delta_<arm>.json`.

**Nothing was rendered and nothing was spent.** Every arm is numpy over an
already-dumped point cloud.

### The one thing this measurement is NOT

Both point clouds available on disk are stale worlds — `assembly9` and
`assembly10`, against `SHIPPING.md`'s `assembly14`. That is deliberate and it is
the right call for this question: holding the world fixed is what makes the diff
a *camera* diff, and `tools/retier.sh`'s own header names "a camera-only
re-derive, where the world is deliberately held fixed and ONLY the projection is
redone" as a supported mode. It does mean **these tier numbers are not the
shipping world's tier numbers.** Dumping `assembly14` opens a 7 GB+ blend on a
box with 2 GB free and is a separate job. The assembly10 arms are here so the
camera answer can be shown not to be an artefact of assembly9.

