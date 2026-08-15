# STAGING R2-3421 .. R2-3480

## R2-3421..R2-3432 — task #160: does the world READ as repetitive? The 2.03 % is a number that could not have mattered, and the instrument behind it cannot see a tree

**VERDICT: the world does not read as repetitive, and the ruling that 2.03 %
does not block the master is RIGHT — but not for the reason it was given.**

The ruling reasoned that 2.03 % is safe because 1 instance in 49 is not "one
tree spammed 100 times". That is arithmetic about a denominator, and the worry
attached to it — that relative to its own population the distribution is now
*more* concentrated, 32x even against 6.2x even — is arithmetic about the same
denominator. **Both are answering a question the rule does not ask.** The rule
names a screen event. Measured as a screen event, the commonest source mesh in
the film is nowhere near the failure, and three separate structural faults mean
`top_share` could not have detected the named failure even if it were present.

**One finding is a live defect and is proposed for the log**: the gate that
polices the tree rule **cannot see a tree**. Not a threshold problem — it counts
zero of them. That is R2-3424 below, demonstrated on a six-object scene.

---

### 1. Where the top source actually is on screen

`VEG_grass_fescue_H04_u` is one of **11** hero fescue meshes
(`assembly14_build.json`: `grass_library` 55 over the five kinds in
`build_terrain.GRASS`). `gn_kind` picks with `rng.integers(0, 11, n)`, i.i.d.
and independent of position, so the top source is **1/11 = 9.09 % of fescue-hero
everywhere**, and 2.03 % of VEG only because VEG pools grass with everything
else. Its 2.03 % is not a property of a place; it is 1/11 measured through a
denominator 180x too big.

Reprojected through `world/camera_rig_path.json` with
`tools/screen_presence.py`'s own camera model (`tools/r2_3421_covisible_repeats.py`):

| `VEG_grass_fescue_H` at ... | peak co-visible | of one mesh | peak co-visible **sharp** | of one mesh |
|---|---:|---:|---:|---:|
| ≥ 32 px of the 4K frame | 2,280 (f2251) | 207 | 124 (f2316) | **11.3** |
| ≥ 64 px | 725 (f2329) | 65.9 | 6.2 (f2310) | **0.56** |
| ≥ 128 px | 24.8 (f1716) | 2.25 | 0 | **0.00** |
| ≥ 256 px | 0 | 0 | 0 | **0.00** |

*sharp* = shutter smear ≤ 6 px, `tools/screen_presence.py`'s own
`SMEAR_SHARP_PX`, at the flat 180° shutter that ships.

**At any size where a grass silhouette can be read at all — 128 px of a 4K
frame is a 32 px object in the proxy — the commonest source mesh in the film has
ZERO sharp co-visible copies, in all 2,978 frames.** The named failure is 100.
Its best figure anywhere is 11.3, and that is at 32 px, where a fescue clump is
an 8-pixel smudge in the proxy and there is no silhouette to recognise.

The window in which the top source is even large and sharp at once is **23
frames of 2,978** — f2310–2321 plus a handful at f1560–1568 — i.e. **half a
second of a 124-second film**. Best frame f2319: lens 69.95 mm, eye 3.26 m,
nearest clump 16.7 m, 448 px/m, median smear 8.6 px.

---

### 2. Three structural faults in `top_share`, of which one is a live defect

#### R2-3424 — `instance_variety.py` COUNTS ZERO TREES. **Proposed for DEFECT-LOG-R2.**

`build_terrain.instance_plants()` places every tree, every hedgerow tree and the
paddock avenue — **27,969 objects in `assembly14`** — as *linked duplicate
objects*: real scene objects sharing a mesh. `instance_variety.py` walks
`depsgraph.object_instances` and does `if not inst.is_instance: continue`, which
discards every real object.

Not argued from the source — built and watched, on a six-object scene
(`tools/r2_3421_instance_variety_control.py`, `work/r23421/iv_control.json`):

```
scene: 40 linked-duplicate trees on ONE mesh, 40 GN instances on TWO
depsgraph mesh entries: 81 total, 40 with is_instance == True

source mesh                    gate's walk    unfiltered
VEG_grass_fescue_H00_u                  20            20
VEG_grass_fescue_H01_u                  20            20
VEG_tree_oak_L0_00                       0            40

instance_variety.py would report: 40 instances, 2 sources,
                                  top VEG_grass_fescue_H00_u at 50.0 % -> SPAM
>> STAGE RESULT: IV_BLINDSPOT_CONFIRMED_GATE_BROKEN
```

**The gate saw 0 of the 40 trees spammed from one mesh**, and printed a SPAM
verdict about the grass instead. The unfiltered walk saw all 40, so the trees
are in the depsgraph; `is_instance` is what throws them away. The instrument
written for "one tree spammed 100 times" has never counted a tree, and neither
the 311/1.99 % record nor the 1,569/2.03 % one includes a single one.

**And it reconciles on the shipping world, not only on the control scene.**
Summing `assembly14_build.json`'s own `gn_kind` populations:

```
grass 2,975,018 + grit 1,616,541 + sward drifts 266,525 + shrubs 38,847
    + weeds 35,486 + ferns 7,211 + saplings 5,500 + stones 264 + spray 125
                                                       = 4,945,517
instance_variety.py measured VEG                       = 4,955,784   (+0.2 %)

woodland 24,646 + hedgerow 3,299 + avenue 24
    + near-band short 356 + amenity 64                 =    28,389   ABSENT
```

The measured total lands on the geometry-nodes population to within 0.2 % — the
remainder is near-band scrub the summary does not itemise — and the **28,389
discrete plants are simply not in it**. Had they been counted the total would be
~4,984,000. So the 1,569 sources and the 2.03 % are a census of the ground cover
with every tree in the world left out.

#### R2-3425 — the family key makes the ratio a grass ratio, always

`instance_variety.py` keys the family off `key.split("_")[0]`. Every vegetation
emitter is `VEG_*`, so 4.96 M ground-cover instances are **one family**. Any
tree pool is diluted ~180x before it is looked at. Even with R2-3424 fixed, a
tree could not become the top source unless one mesh carried more instances than
all the grass — the metric structurally cannot report the failure it names.

#### R2-3426 — a whole-world ratio cannot express a screen event

"One tree spammed 100 times" is a hundred copies **you can see at once**. A mesh
used a million times, never twice within sight of itself, is not that; a mesh
used twelve times, all twelve filling one frame, is. A ratio over the whole world
cannot distinguish them, which is why both the 2.00 % ceiling and the 32x-even
worry are unanswerable as posed.

---

### 3. What the rule's own metric says about the whole world

`tools/r2_3421_covisible_repeats.py` — for every pool of instances drawing on one
library, the peak number **co-visible in one frame at a readable size**, divided
by the library size. The client's sentence is this number = 100.

Pools merge woodland and hedgerow of the same species and LOD, because
`build_library` hands both the **same** meshes; the avenue is merged into
`plane_L0` for the same reason. Occlusion is ignored, yaw/mirror/scale variation
is ignored, so **every figure is an upper bound** — the safe direction for a red
line, and generous by a lot (several peak frames are in beat 1, where the trees
are behind the showroom wall).

At **≥ 128 px of the 4K frame, sharp** — the smallest size at which a silhouette
is genuinely readable — **every grass pool drops to zero and only trees remain**:

| pool | library | co-visible sharp | per mesh | frame |
|---|---:|---:|---:|---:|
| `tree:oak_L2` | 16 | 331 | **20.7** | 2225 |
| `tree:pine_L2` | 16 | 206 | 12.9 | 2222 |
| `tree:birch_L2` | 16 | 147 | 9.2 | 2218 |
| `tree:oak_L1` | 12 | 107 | 8.9 | 2464 |
| … | | | | |
| every `VEG_grass_*` | 11 | 0 | **0.0** | — |

At **≥ 256 px, sharp**: worst is `tree:oak_L2` at **5.9**, at f2340.

**The worst number in the film is 20.7 against a named failure of 100, it is a
tree and not the grass the ceiling was policing, and it is an upper bound that
ignores occlusion.** `>> STAGE RESULT: COVISIBLE_REPEATS_CLEAN`.

The frames a person can look at:

* **f2340** — the largest, sharpest treeline in the delivery, and the ≥256 px
  peak. Bare snags and canopies through heavy haze; every crown a different
  height, branch structure and lean. No repeat is apparent.
* **f2218** — the ≥128 px `birch_L2` peak. Most of the counted trees are behind
  the grandstand and the bridge, which is the occlusion this instrument
  deliberately does not subtract.
* **f1545** — the L2 peak in the earlier stride-2 pass; treeline hazed and
  smeared, crowns 40–80 px at 4K, nothing readable as a repeat.
* **f2319** — the near-field verge at its sharpest and largest. The verge closes
  into a continuous sward; individual clump silhouettes are not separable, which
  is why the ≥128 px grass row is zero.

---

### 4. The delivered pixels, and a threshold the controls destroyed

`tools/r2_3421_frame_repetition.py` runs two arms on the near-field band of the
delivered frames (proxy y 362–538, which is where hero grass ≥150 px/m lands):
full-offset normalised cross-correlation for **duplicated silhouettes**, and
autocorrelation for **placement period**. Neither arm can see the other's
failure, so both are present.

**Two of this instrument's own faults were found by watching its controls, and
both would have produced a confident wrong answer.**

1. **The first NCC search was vacuous.** It compared patches on a stride-4 grid
   against each other, so two copies of one patch pasted at positions differing
   by a non-multiple of 4 were never compared at their aligned offset. Measured:
   the shipping band scored **3.43 %** and a band repainted **entirely out of one
   patch** scored **3.84 %** — no separation at all, between two pictures that
   are not remotely alike to look at. Replaced with an exhaustive FFT search over
   every integer offset, plus the left-right flip (`gn_kind` mirrors half of
   every scatter in x).

2. **`NCC_HIT = 0.90` was chosen by taste and the ladder falsified it.** Near-field
   grass under a 180° shutter is so self-similar that any two 24 px windows of it
   correlate at ~0.75, so at 0.90 the shipping band and the spammed band overlap.
   The threshold is now **0.96**, which is where the two populations part.

Calibration on **f2319's** band — the verge at its sharpest — with every control
built out of the **same pixels**, so grade, blur, grain and contrast are held and
the only new thing is repetition:

| band | NCC ≥ 0.90 | ≥ 0.96 | ≥ 0.98 | period peak |
|---|---:|---:|---:|---:|
| `phase` — THE NULL: same power spectrum, no structure | 0.26 % | **0.000 %** | 0.000 % | 0.131 |
| **the delivery** | 6.51 % | **0.011 %** | **0.000 %** | 0.119 |
| `tile100` — the band repainted from one patch | 11.68 % | **2.38 %** | 0.67 % | 0.077 |
| `tile20` — one patch over 20 % of the band | 36.83 % | **13.75 %** | 5.58 % | 0.088 |
| `lattice` — one patch on a regular grid | 98.92 % | **94.68 %** | 79.67 % | **0.790** |
| `shuffle` — RETIRED, see below | 19.59 % | 3.50 % | 0.62 % | 0.111 |

At 0.96 the ladder is monotone in how much literal repetition was added, **the
null does not fire at all**, and the delivery sits 216x below the weakest
positive control and 1,250x below the 20 % rung — the rung that corresponds to
the "force the top source to 20 %" the brief asked for. The periodicity arm
separates on its own: 0.119 delivered against 0.790 for a lattice, with
`PERIOD_FAIL` at 0.30 between them, and the null at 0.131 — i.e. **the delivery
is no more periodic than structureless noise with its own power spectrum.**

The delivery's 6.51 % at NCC 0.90 is 25x the null's 0.26 %, and that is real and
expected: grass genuinely does repeat motifs, because it is grass. It is also
the reason 0.90 was useless as a line.

**A control that failed, reported rather than quietly dropped:** `shuffle` was
meant to be the null — the same patches, rearranged, no new duplicates — and it
scored **above `tile100`**, because shuffling manufactures hard tile seams and the
seams correlate with each other. A control that introduces its own artefact
measures the artefact. It is retired as a null and replaced by `phase`, which
randomises the band's Fourier phase and keeps its power spectrum exactly: same
texture statistics, same blur, same contrast, no repeated structure anywhere.

#### The arm fires on five delivered frames, and neither firing is repetition

Swept over eight frames of beat 5 with the same fixed band, the delivery does
**not** read as uniformly clean, and that has to be said before the verdict is:

| frame | textured patches | NCC ≥ 0.96 | period | what is actually in the band |
|---|---:|---:|---:|---|
| f2316 | 9,021 / 9,165 | **0.000 %** | 0.102 | verge, sharp |
| f2318 | 9,073 | **0.000 %** | 0.113 | verge, sharp |
| f2319 | 9,038 | **0.011 %** | 0.119 | verge, sharp |
| f2320 | 9,066 | **0.000 %** | 0.122 | verge, sharp |
| f2330 | 6,862 | 1.46 % | 0.242 | verge **and concrete run-off** |
| f2292 | 8,160 | 5.21 % | 0.097 | verge, 213–245 px of drag |
| f2251 | **2,217** | 13.2 % | 0.168 | **asphalt and gravel run-off** |
| f2400 | 4,111 | 14.9 % | 0.264 | **a painted kerb** |
| f2365 | **2,848** | **26.4 %** | **0.318** | **gravel run-off, near-featureless** |

Looked at, not assumed. **f2365's band is not vegetation at all** — it is the
smooth gravel-and-asphalt run-off, which is why only 2,848 of
9,165 patches clear the variance floor: the ones that do are faint smooth
gradients and shutter streaks, and near-flat gradients correlate with each other
trivially. **f2400's band contains the red-and-white kerb**, which is periodic
*by design and by regulation* — that is the period arm correctly finding a
repeating pattern that is supposed to repeat.

So the honest statement of the image-domain result is narrower than the sweep:

> **On every frame where the band is the near-field verge and the grass is
> sharp — f2316, f2318, f2319, f2320, the entire window in which the top source
> is both large and resolvable — the duplicate arm reads 0.000–0.011 %, against
> 13.75 % for the same band with the top source forced to 20 %.**

**The band is a fixed rectangle and that is this instrument's real limitation.**
It should be selected per frame from the co-visibility pass (which knows where
the grass is) rather than assumed to be the bottom third. Not fixed here, and
named so the next reader does not quote the f2365 number as a finding about
vegetation. **A high reading on a flat gravel apron is a fact about gravel.**

**And the controls answer the question by eye before any number does.**

* `work/r23421/control_bands.png` — the delivered band and the three positive
  controls stacked at 2x. `tile20`, `tile100` and `lattice` are instantly,
  unmistakably repetitive **at proxy resolution**; the delivered band is a
  continuous varied sward. That is the perceptual test the brief asked for, and
  it is not close.
* `work/r23421/pairs_ship_vs_tile20_vs_lattice.png` — the six strongest matched
  pairs found in each band, side by side. **In the delivery the strongest
  "duplicate" the search can find is plainly not a duplicate**; in `tile20` and
  `lattice` the pairs are visibly the same picture. This is the duplicate arm
  showing its working rather than asserting a percentage.

---

### 5. What this does NOT establish

* **The proxy is a 4x linear downscale.** Everything above is measured on the
  delivery as delivered, and the co-visibility result does not depend on
  resolution — it is computed in 4K pixels from the camera path. But the
  image-domain arm resolves a quarter of what the master will. It is not needed
  for the verdict (the ≥128 px grass row is zero on geometry alone, and the
  worst tree pool is 5x under the named failure), so **no 4K frame is requested
  and no credit is spent.**
* **Occlusion is not subtracted** anywhere in §3. Several peak frames are beat-1
  frames where the trees are inside the showroom's sightline and invisible.
* **The point dump is `assembly10`, the variety number is `assembly14`.** For the
  trees this is exact — `woodland_trees` 24,646 and `hedgerow_trees` 3,299 are
  identical in both build records. For grass it is 9.6 % low
  (`grass_hero_clumps` 1,662,591 → 1,821,790), which moves no row that matters.
  **The near-band tier is new in `assembly14` and is NOT measured here**: 356
  short trees and 64 amenity trees drawn from **312 base meshes**, i.e. 1.35
  instances per mesh. It is the most varied population in the world and it is the
  one closest to the lens, so its absence makes §3 conservative, not optimistic.
* **`shrub`, `fern`, `weed` and `stone` pools are measured and clean** but their
  heights are class representatives, not per-instance bboxes; only the tree pools
  carry exact per-instance bboxes from the dump.
* **The grass rows depend on an assumed clump height** (0.22 m for fescue, the
  midpoint of `GRASS_PROF["fescue"]["h"]`), because the point dump voxelises the
  emitter's base mesh and carries no per-clump bbox. **The conclusion survives a
  4x error in it**, which is the whole point of quoting the ladder rather than
  one row: doubling the assumed height moves the top source's answer from the
  ≥128 px row to the ≥64 px row, i.e. from **0.00** to **0.56**; quadrupling it
  reaches the ≥32 px row at **11.3**. All three are far under the named 100, and
  0.42 m is the largest a fescue clump gets in this build.

---

### 4b. THE RENDER LADDER — top share 9 % → 20 % → 100 % changes nothing an eye can see, and the control that proves the eye can see

The image-domain controls above are made of pixels. This one goes through the
**real pipeline**: `tools/r2_3421_variety_control.py` builds a `macro_probe`
window of verge from `build_terrain`'s own `build_grass`/`gn_kind`, with `nlib`
forced to the shipping **11** (read out of `assembly14_build.json`, not the
probe's own 9), at **f2319's camera** — lens 69.95 mm, eye 3.26 m, axis 2.99°
down, optical axis meeting the ground at 62.4 m — and renders a **960×540 crop
of a 3840×2160 frame**, so the px/m is the master's, not the proxy's.

`tools/instance_variety.py` on the probe: **183,158 instances, 134 sources, top
share 3.0 %** — already over the 2.00 % ceiling before anything is done to it.

Then `inst_idx` is rewritten in place. **Positions, heights, lean, lighting,
camera and seed are identical across every rung**; the only thing that changes is
how many distinct meshes the picks land on.

| rung | fescue-hero top share | what it is |
|---|---:|---|
| `ship` | **9.09 %** | as built, 11 hero meshes |
| `top20` | **20.19 %** | the top source forced to a fifth |
| `top100` | **100 %** | **one mesh**, the literal named failure |
| `allgrass100` | **100 %**, all 5 kinds × 2 tiers | the whole ground cover on 10 meshes |
| `stamp` | 100 % **and no randomisation** | yaw, mirror and anisotropic scale removed |

`work/r23421/ladder_all.png` stacks all five.

**`ship`, `top20`, `top100` and `allgrass100` are indistinguishable.** Collapsing
the near-field verge from eleven meshes to one — from 9 % to 100 % top share, at
4K scale, with *no motion blur at all*, which is far harsher than the delivery —
produces no repetition an eye can find. The clumps interpenetrate so completely
at the shipping density that what the frame shows is **blades, not clumps**, and
clump identity is not a visible quantity.

**`stamp` is instantly, obviously wrong.** With the per-instance yaw and mirror
gone, the whole sward combs into one direction and reads as a brushed mat rather
than a meadow. **That is the control on the control, and it fired**: the eye
*can* see uniformity in this crop, so "`ship` looks like `top100`" is a real
observation and not a failure to look.

Which settles what `top_share` is actually measuring here:

> **What defeats repetition in this world's ground cover is `gn_kind`'s
> per-instance randomisation — a continuous uniform yaw, a 50 % x-mirror and
> independent x/y/z scale jitter — not the size of the library. `top_share`
> cannot see randomisation at all. It is not a mis-set threshold; it is the
> wrong quantity.**

`tools/r2_3421_frame_repetition.py` on the five rungs agrees, and in doing so
exposes its own limit:

| rung | NCC max | NCC ≥ 0.96 | period |
|---|---:|---:|---:|
| `ship` | 0.886 | **0.000 %** | 0.042 |
| `top20` | 0.888 | **0.000 %** | 0.040 |
| `top100` | 0.880 | **0.000 %** | 0.039 |
| `allgrass100` | 0.854 | **0.000 %** | 0.051 |
| `stamp` | 0.894 | **0.000 %** | **0.114** |

**Even at a 100 % top share the duplicate arm finds nothing** — no two 24 px
windows of a sward built from one mesh are the same picture, because the
per-instance transform means they are not the same picture. That is the ladder's
result stated in the instrument's own units.

**Both arms would have MISSED the one rung that is actually wrong.** `stamp`
moves the period arm only 2.2–2.9x — 0.114 against a `PERIOD_FAIL` of 0.30 — and
the duplicate arm not at all. A combed sward is not a lattice and contains no
duplicated window; the failure is *directional uniformity*, and neither arm has
a statistic for it. **The eye caught `stamp` and the numbers did not.**

So a third arm was built rather than left as a note — `orientation_R`, the
magnitude-weighted axial concentration of the gradient orientations, 0 isotropic
and 1 all-one-way — and it is the separation the other two lacked:

| rung | `orient_R` | whole-frame NCC vs `ship` |
|---|---:|---:|
| `ship` | 0.3100 | 1.000 |
| `top20` | 0.3104 | **0.988** |
| `top100` | **0.3107** | **0.986** |
| `allgrass100` | 0.2891 | 0.278 |
| `stamp` | **0.6226** | 0.171 |

**Flat to 0.2 % across a top share of 9 %, 20 % and 100 %; 2.01x on the rung
that is wrong.** And the second column is the hard version of "indistinguishable":
**collapsing the near-field fescue library from eleven meshes to one changes the
rendered picture by 1.4 %**, because the per-instance transform, not the mesh,
is what makes one clump differ from the next.

The delivered f2319 measures `orient_R` **0.0963** — a third of the still
render's, as motion and the wider view make it more isotropic still — and now
returns `>> STAGE RESULT: FRAME_REPETITION_CLEAN`.

Cost: five CPU renders of ~4.5 minutes each, **$0**, on the box, not the 5090.
48 samples with denoising — adequate for a *relative* comparison between five
frames that differ in one attribute, and not offered as a quality frame.

---

### 5b. There are THREE variety rules in this project and they disagree

Found while checking what the near-band tier does. `tools/item_gate.py` already
carries a variety rule of the right *shape* — per population, not per world —
and it already has a false-accept control that has been observed to fail
(`tools/r2_1381_variety_control.py`: 4,500 objects from two meshes REFUSED,
4,500 from forty bodies ACCEPTED):

```
distinct_sources >= max(8, min(40, sqrt(n)))    and    top_source_share <= 0.25
```

Applied to the shipping vegetation pools it gives a **third** answer, different
from both the 40 % in `instance_variety.py` and the 2.00 % the campaign polices:

| pool | n | sources | `item_gate` needs | top share | vs 25 % arm | vs source arm |
|---|---:|---:|---:|---:|:--|:--|
| `VEG_grass_fescue_H` | 1,021,524 | 11 | 40 | 9.1 % | pass | **fail** |
| `VEG_grass_tussock_H` | 317,018 | 11 | 40 | 9.1 % | pass | **fail** |
| `tree:oak_L2` | 3,924 | 16 | 40 | 6.2 % | pass | **fail** |
| `VEG_fern` | 7,211 | 9 | 40 | 11.1 % | pass | **fail** |
| near-band short tree, per (species, LOD) | ~40 | 22 | 8 | 4.5 % | pass | pass |

**Every pool passes the share arm comfortably and most fail the source-count
arm** — and the source-count arm is the campaign's own named calibration error
in another costume. `sqrt(1,021,524)` is 1,010; the `min(40, ...)` cap is doing
all of the work, and 40 was chosen for *items* in the tens-to-thousands, whose
individual identity is resolved on screen. Fed a million grass clumps whose
individual identity is never resolved — measured: **zero** sharp co-visible
copies of any one of them at ≥128 px — it demands 40 hero meshes per grass kind
and buys nothing an audience can see.

So: three rules, three answers, and none of them is the rule. The near-band tier
is the one place the project already reasoned this way on purpose — it tops each
(species, L0) library from 8 up to 22 *because* those trees are the ones nearest
the lens — and it is the only pool that passes everything.

---

### 6. Was the ruling right?

**Right conclusion, wrong reason — and the worry that prompted the doubt was
also the wrong question.**

* **Right**: 2.03 % does not block the master. Nothing in the world reaches the
  named failure, and the top source specifically is at **zero** co-visible sharp
  copies at any readable size.
* **Wrong reason**: "1 in 49 is not one tree spammed 100 times" reasons about
  the ratio, and so does "32x even is more concentrated than 6.2x even". Both
  are statements about a denominator that pools 4.9 M grass clumps with 27,969
  trees. **The 32x-even worry is not a rationalisation — it is a correct
  observation about a statistic that was never measuring the rule.** Answering
  it either way would have been answering the wrong question.
* **And the ladder shows the quantity has no perceptual content at all here**
  (§4b): the same verge at 9 %, 20 %, 100 % and "the whole ground cover on ten
  meshes" is the same picture, while removing the per-instance yaw — which
  `top_share` cannot see — is instantly wrong. A ceiling on `top_share` was
  never going to catch the thing it is afraid of, at any value.
* **The ceiling should not be "recalibrated" — it should be replaced.** A
  2.00 % (or 2.10 %, or 0.064 %) line on `top_share` cannot detect the named
  failure at any setting, because of R2-3424 and R2-3425. Recalibrating it
  would ratify an instrument that counts zero trees.

**Recommended, and not landed by this block:**

1. **R2-3424 is a shipping-quality defect in the gate, not in the film.** Fix
   `instance_variety.py` to count linked duplicates, and key the family on the
   emitter, not on `VEG`. Until then its verdicts are about ground cover only
   and should be labelled as such.
2. **Police `cvrr_sharp` at ≥128 px, not `top_share`.** It is the rule's own
   sentence in numbers, it is cheap (no Blender, ~3 minutes on the point dump),
   and it has a control that has been observed to fail.
3. If a line is wanted now: `cvrr_sharp ≥ 128 px` is **20.7** on the ship
   against a named failure of **100**. Any line between them is defensible;
   none of them blocks this master.
4. **Do not adopt `item_gate`'s `sqrt(n)` source floor for ground cover** (§5b).
   It would demand 40 hero meshes per grass kind against the shipping 11, on a
   cap chosen for populations four orders of magnitude smaller, to fix a
   repetition that is measurably invisible. That is the same calibration error
   the campaign is trying to stop making, pointed the other way. **The 25 %
   share arm, per pool, is the part worth keeping** — every pool in the world
   passes it, and it is measured against a denominator that means something.

---

### Paths

| path | what |
|---|---|
| `tools/r2_3421_covisible_repeats.py` | the rule's own metric; `work/r23421/covisible.json` |
| `tools/r2_3421_instance_variety_control.py` | the six-object proof that the gate counts zero trees |
| `tools/r2_3421_frame_repetition.py` | duplicate + period arms on the delivered frames, with the ladder |
| `tools/r2_3421_variety_control.py` | the render ladder: ship / top20 / top100 / allgrass100 / stamp at held placement |
| `work/r23421/ladder_all.png` | **the five rungs stacked — the picture the verdict rests on** |
| `work/r23421/control_bands.png` | the delivered band and three positive image-domain controls |
| `work/r23421/pairs_ship_vs_tile20_vs_lattice.png` | the strongest matched pairs found in each band |
| `work/r23421/frames_treepeaks.png` | f2340 and f2225, the largest/sharpest treelines |
| `work/r23421/probe.blend` | the 30 MB verge probe the ladder is rendered from |
| `work/r23421/` | every measurement, log and control band |

**$0 spent.** No render was commissioned; credit is untouched at $[redacted].
