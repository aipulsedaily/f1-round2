# STAGING R2-1881 to R2-1980

Staged by the tree-scoping agent, 2026-08-07. Merge by identity, never by position.
**Nothing here was built. This block measures, and it retires a build decision.**

> **RENUMBERING NOTE.** Two agents appended to this file concurrently and both
> claimed R2-1886/1887/1888. The verification agent's block was shifted **+3**
> (its 1886-1894 are now **1889-1897**) to restore unique identity; its internal
> cross-references were moved with it and its references to R2-1881-1885 were
> left alone. **If you are reading that agent's own report, its "R2-1886…R2-1894"
> means this file's R2-1889…R2-1897.** Nothing was merged by position and no
> entry was dropped. Original at `scratchpad/staging.bak`.
>
> The two blocks measure the same world with different point sets and **they
> reconcile**: the verification agent's woody set is 27,969 (structural only,
> from `world_points.npz`, which carries no shrub or sapling origins) and
> R2-1884's is 72,297 = 27,969 trees + 38,830 shrubs + 5,498 saplings, from
> `sp_points.npz`. Both are printed on every run of its metric.

---

## R2-1881 — `min_depth_m` 4.577 m IS THE GRASS. Every tree in the top 11 was ranked on the vegetation layer's aggregate, and the true nearest tree is 35.13 m

`WAVE2-RANKING.md` §5b asked for this to be settled before any tree is rebuilt.
It is settled, and the error is larger than the 11× it guessed at.

**The mechanism, read from source rather than inferred.** In
`work/w2_0/retier_a10/item_presence.json` all twelve `tree_*` items carry
**`n_hosts: 93`** and a host list that is *the entire `VEG_` layer* —
`VEG_shrub_bramble_L0`, every grass class, every grit class. Their
`min_depth_m` is therefore the minimum over that whole layer, and their
`peak_px_4k` its maximum:

| what the item row says | what it actually is |
|---|---|
| `min_depth_m 4.577` (all 12, identical) | `VEG_grass_*_H` min depth = **4.577 m** — grass under the lens |
| `peak_px_4k 2160.0` (all 12, identical) | grass filling the frame |

**A tree that resolves to 93 hosts including every grass class is not a
measurement of a tree.** `n_hosts` was the tell and it was on the row all along.

**Re-derived, independently.** Not by trusting `mindepth` in the npz but by
re-projecting the points from `render/film17_path.json` through
`live_campath.load()`, 2,978 frames, `s = 3840·lens/36`, `ppm = s/depth`:

| class | instances | min depth | p05 | median | peak px/m |
|---|---:|---:|---:|---:|---:|
| avenue tree | 24 | **35.13 m** | 37.5 | 119.2 | 107.8 |
| woodland tree | 23,487 | **74.54 m** | 316.1 | 883.2 | 52.0 |
| hedgerow tree | 3,130 | **78.95 m** | 268.1 | 838.6 | 49.3 |
| shrub | 38,830 | 57.58 | 222.6 | 618.6 | 69.6 |
| sapling | 5,498 | 123.97 | 238.4 | 631.2 | 44.8 |
| grass | 1,255,084 | **4.58** | 39.6 | 210.5 | 779.0 |

**4.577 m is the grass row, to the centimetre.** The claimed tree depth is
wrong by **7.7×** against the nearest tree and **16.3×** against the woodland
tier that carries 23,487 of the 26,641 instances.

**CANOPY CORRECTION — the point cloud stores TRUNK BASES, one point per
instance** (24,646 `VEG_tree_*` points == the build log's 24,646
`woodland_trees`). A canopy sits up to 27 m above its origin and can be nearer
the lens, so the base figure is not automatically the nearest tree *surface*.
Re-probed with the canopy top and mid-canopy added at each species' authored
max height:

```
nearest tree surface   32.92 m   (VEG_avenue, h 19.6 m)   vs 35.13 m at the base
max px/m incl canopy    107.8    unchanged -> 1 px = 9.3 mm
```

**The correction is 6 % and changes nothing.** 32.92 m is still **7.2×** the
claimed 4.577 m, and no woodland or hedgerow class moves by more than ~2 m.
Stated because the base-only measurement would otherwise have been an
unexamined assumption of exactly the kind this block is about.

**Peak px was overstated per species too** (true peak = peak_ppm × species max
height, from `build_terrain.py:SPECIES`):

```
poplar 1380 px (claimed 2160, 1.57x)   oak      841 (2.57x)
pine   1023            (2.11x)         plane    878 (2.46x)
birch   826            (2.62x)         willow   720 (3.00x)
snag    729            (2.96x)         rowan    560 (3.86x)
cypress 424            (5.09x)         hawthorn 280 (7.72x)
```

Score goes as px², so the ranking statistic is overstated by up to **~60×** for
hawthorn. **The class-level finding survives — trees do dominate — but the rank
order inside it does not**, exactly as §2.1 warned.

**One row is right by accident: the avenue.** `paddock_avenue_tree` (rank 5)
reaches 107.8 px/m at 35.13 m, and at its authored 11.8–19.6 m height that is
**1,272–2,113 px** — genuinely near-frame-filling. 24 trees out of 26,641 do
deserve hero treatment. The other 26,617 do not.

**METHOD NOTE — I got this wrong once and caught it.** My first pass filtered on
`VEG_tree_` and reported 74.54 m. That silently dropped `VEG_hedge_*` and
`VEG_avenue`, and the avenue holds the minimum. **The corrected answer is
35.13 m.** A prefix filter over a naming scheme nobody documented is the same
defect shape as the host list above: a selection that looks total and is not.

---

## R2-1882 — the probe's controls FAILED first time, and the controls were the thing that was broken

All four controls on the first run failed. Reported here rather than quietly
fixed, because the failure mode is instructive: each control planted a **static
world point** and then minimised over **all 2,978 frames**. The camera flies, so
it passes closer to that point later — "5 m ahead at frame 1" is not "5 m away
for the film". **A control that does not hold the frame fixed cannot test a
per-frame projection.**

Redone with the frame held fixed, 8 arms, all PASS:

```
P: point at 4.577 / 5.000 / 12.690 / 84.180 m dead ahead -> exact, 1e-3
P: px-per-metre at 4.577 m on the 18.0 mm lens           -> exact
N: 20 m behind the lens / outside the FOV / at the lens  -> 0 frames each
D: displacing the camera +300 m X moves min_depth 74.54 -> 6.32 m
F: a tree PLANTED at 4.577 m is reported at 2.835 m
```

**The F arm is the one that matters.** The refutation is only worth something if
the instrument could have returned 4.577 m and didn't. It can: plant a tree
there and it reads it. And the D arm proves the probe reads the camera rather
than returning a constant — **trees CAN sit at 6 m; under this camera they do
not.**

---

## R2-1883 — the tree tier was declared unbuildable while a 33.26 M-triangle vegetation library with 26,641 trees was already shipping in the film

`WAVE2-RANKING.md` §5a/§5b concluded the tree tier is unbuildable on an 11 GB
box: 44 L0 sources ≈ 35 M tris, a full-density pine 1.35–1.89 M. Both builds
that reached that wall were building **per-item hero modules in
`world/items/`**. Meanwhile `world/build_terrain.py` already builds and places
the entire layer, and `render/world/assembly/r2/assemble6.log` records what it
produced:

```
woodland_trees 24,646   hedgerow_trees 3,299   avenue 24
shrubs 38,847   saplings 5,500   ferns 7,211   weeds 35,521
grass_clumps 2,984,718 (hero 1,662,591)   grit_pieces 1,617,615
objects 28,004   unique_meshes 1,027
base_library_tris 33,258,111   evaluated_tris 15,072,255,777
build_s 982.0
```

**33.26 M base-library triangles, on this box, in 982 s.** The number the tree
campaign called impossible is the number the shipping world already carries. The
two builds were not blocked by the box; they were sized against a 4.577 m
framing that belongs to grass.

**And the specific asset that broke them is never placed at L0.**
`VEG_tree_cypress0` **does not exist in the assembled world** — cypress appears
only at L1 (25 instances, nearest 153.42 m) and L2 (49, nearest 508.29 m).
`build_terrain.py` selects LOD by `dcam < 95 → L0, < 380 → L1, else L2`, and no
cypress ever lands inside 95 m. **The ~800 k-triangle L0 cypress spray that
stopped two builds has no frame to appear in.**

At the cypress's real nearest station one pixel is **34 mm**; a 55 mm spray is
**1.6 px**. At the pine's (84.03 m, 44.5 px/m) one pixel is **22.5 mm** and a
1.70 mm needle is **0.076 px** — 13× below the line. §5a's 12.69 m needle
crossover is **unreachable**: the nearest tree of any species is 35.13 m and the
nearest pine 84.03 m.

**Consequence for the resume order.** Items 4 and 6 of `WAVE2-RANKING.md` §7 are
answered: the triangle crisis is an artefact, and rebuilding the 11 hero tree
modules is **not** the highest-value use of the next month. The 11 ranks are
real as a *class* statement and the class is already built.

---

## R2-1884 — 44.9 % of the ground the camera looks at is more than 10 m from any woody instance, and the planting is INVERSELY correlated with camera proximity

The client's own finding — *"anything 5 feet away from the main road and
buildings have blank grass no detail nothing"* — measured rather than accepted.

60,000 `TER_Ground` samples, each given its **exact** screen-area-time
`w = Σ_frames (s_f/d_f)²` over the frames it is genuinely inside the frustum
(not a proxy), then its plan distance to the nearest woody instance among the
72,297 placed (trees, hedgerows, avenue, saplings, shrubs).

**Distance from viewed ground to the nearest TREE, weighted by screen-area-time:**

```
0-5 m 13.1 %   5-10 m 20.1 %   10-20 m 19.2 %   20-40 m 18.5 %
40-80 m 15.5 %   80-160 m 11.5 %   >160 m 1.9 %
```

**The finding is the correlation, and it runs the wrong way:**

| ground's min depth to camera | % of ground area-time | median distance to nearest tree | to any woody |
|---|---:|---:|---:|
| 25–50 m | 3.1 % | **78.9 m** | 46.5 m |
| 50–100 m | 15.5 % | 48.3 m | 24.6 m |
| 100–250 m | 35.4 % | 30.7 m | 12.0 m |
| > 250 m | 46.1 % | **9.6 m** | 5.0 m |

**The ground the camera sees closest is the ground furthest from a tree**, by
8.2× against the far band. That is the signature of path-relative placement, and
it is legible in source:

```python
# build_terrain.py, woodland
can = (h["f"] > 12.0) & (h["D"] > 26.0) & (h["built"] < 0.30) & (h["ez"] < 0.42)
idx = idx[outside_corridor(cx_[idx], cy_[idx], 8.0)]
# hedgerows
hedge_ok = (h["fdist"] < 4.2) & (h["f"] > 26.0) & ...
hi = hi[outside_corridor(cx_[hi], cy_[hi], 18.0)]
```

**A 26 m standoff from the track and an 8–18 m corridor exclusion evacuate
exactly the band the lens resolves best.** Inside it the world carries grass,
weeds and grit and nothing woody — which is precisely "blank grass, no detail".

**Headline: 44.9 % of ground screen-area-time is more than 10 m from any woody
instance.** The map is not short of trees (72,297 woody instances, 4.69 M VEG
instances total); it is short of them *where the camera is*.

**Controls:** points planted on known trees return 0.000 m; a point 20 km
outside the map returns unbounded; the real ground returns a spread of 0–∞ m
rather than one value. The nearest-neighbour search expands its ring until the
inner radius exceeds the best distance found, so it cannot return a near miss —
the failure mode a fixed 3×3 lookup has.

---

## R2-1885 — what this block recommends, and what it declines

**Decline:** rebuilding the eleven hero tree modules in `world/items/`. Their
rank rests on a grass-derived 4.577 m and a grass-derived 2160 px; re-measured
they peak at 280–1,380 px at 35–79 m, and the layer is already built to a
33.26 M-triangle library. `tree_italian_cypress` (KNOWN BAD, R2-1341) should be
**dropped, not rebuilt** — no cypress is ever placed at L0.

**Keep:** `paddock_avenue_tree`. 24 instances, 35.13 m, 1,272–2,113 px. It is
the only tree row whose hero framing survives measurement.

**Build instead:** woody and structural vegetation in the **0–50 m band**, by
relaxing the standoff and corridor rules that currently evacuate it. This is a
*placement* change against an existing 1,027-mesh library, not new geometry —
the same shape as the R2-1150 sward fix, which took ground cover 4 % → 72 % for
+0.32 % of the triangle budget.

**Variety is already instrumented and must be held.** `docs/instance_variety.json`:
**4,688,475 VEG instances, 310 sources, top share 1.99 %, gini 0.7216,
15,124 instances per source.** Variety comes from the population, not from more
unique meshes — `build_terrain.py` already varies height, breadth, mirroring,
lean, spin, colour, season and canopy density per instance, and picks species
from six habitat-weighted mixes (`MIX_BASE/EXPOSED/DAMP/STEEP/PARK/HEDGE`).
**Any near-band fill must be re-measured on this instrument and must not move
top share above 2 %.**

**Do not edit `world/build_terrain.py` from this block** — it is live and a
rebuild is in flight. The change above is specified, not applied.

---

## R2-1886 — THE EMPTIER IS ONE LINE WITH FIVE CONSUMERS: `wood *= smoothstep(52, 150, D)`

R2-1884 blamed the standoff rules (`h["D"] > 26.0`, `outside_corridor(..., 8.0)`
and `(..., 18.0)`). **That was the visible rule, not the operative one.** Read
from source, `habitat()` (`build_terrain.py` ~3676) computes:

```python
wood  = smoothstep(-0.22, 0.34, fbm(x/165.0, y/165.0, 4, seed=401))
wood *= smoothstep(52.0, 150.0, D)                               # <-- THE EMPTIER
wood *= (1.0 - 0.88*plateau) * (1.0 - 0.94*built) * (1.0 - 0.80*ez)
```

`smoothstep` returns **exactly 0 below its lower edge**, so woodland probability
is **zero for D <= 52 m** and 0.5 only at D = 101 m. The hard `D > 26.0` gate
never binds: the soft field has already gone to zero 26 m outside it.

**And `wood` is not woodland's alone. It gates five tiers:**

| line | consumer |
|---|---|
| 3962 | woodland `pw = h["wood"] * 0.44 * q` |
| 3990 | hedgerows `(h["wood"] < 0.42)` |
| 4034-4035 | shrubs `edge`/`inner` both derived from `hu["wood"]` |
| 4070 | saplings `(hu["wood"] > 0.30)` |
| 4078 | ferns `(hu["wood"] > 0.55)` |

**One field, five consumers, and every woody tier in the world reads it.** That
is why the near band is not merely short of trees but short of *everything*
woody — which is exactly the client's "blank grass no detail nothing".

**Quantified against what the camera actually looks at** (60,000 `TER_Ground`
samples weighted by exact screen-area-time, D approximated as distance to the
nearest `SURF_Track` sample):

| D (distance to track) | % of ground area-time | mean `wood` gate |
|---|---:|---:|
| 0-26 m | 3.4 % | **0.000** |
| 26-52 m | 14.6 % | **0.000** |
| 52-101 m | 17.7 % | 0.191 |
| 101-150 m | 18.0 % | 0.812 |
| >= 150 m | 46.2 % | 1.000 |

**18.0 % of ground screen-area-time carries a woodland probability of exactly
zero. A further 35.7 % is partially gated at a mean of 0.52. Only 46.3 % is
ungated.** Better than half the ground the film looks at is suppressed or
emptied by one multiplication.

**The second half of the defect is `(1.0 - 0.94*built)`** — a 94 % suppression
across the paddock and showroom footprints, which is where beats 1-4 live.
Sized the same way, on the showroom precinct term
`window(x,-172,172,26)*window(y,-172,172,26)` alone:

| `built` | % of ground area-time | mean surviving woody fraction |
|---|---:|---:|
| ~1.0 (the -94 % core) | **13.3 %** | **0.060** |
| 0.5-1.0 | 1.1 % | 0.250 |
| 0.05-0.5 | 0.9 % | 0.758 |
| ~0 (unaffected) | 84.7 % | 1.000 |

**13.3 % of ground screen-area-time sits where woody cover is cut to 6 % of
nominal.** This is a **LOWER BOUND** and is reported as one: `built` is the max
of two windows and the other is in circuit coordinates
(`window(cx,-490,140,26)*window(cy,-70,120,26)`, the paddock), which needs
`world_to_circuit` and therefore Blender. The true figure is larger.

**The client named both halves in one sentence:** *"5 feet away from the main
road **and buildings**"*. One is `smoothstep(52,150,D)`, the other is
`(1 - 0.94*built)`, and they multiply into the same five consumers.

**THE `D` APPROXIMATION IS VALIDATED BY A PREDICTION IT COULD HAVE FAILED.**
The tables above approximate `D` as distance to the nearest `SURF_Track` sample
rather than calling `corridor_fz`, which needs Blender. If that approximation is
sound then, because the gate is exactly zero below 52 m, **essentially no
woodland tree should sit at D < 52 m** — a prediction made against data the
approximation was never fitted to:

| class | min D | frac D < 52 m | has a D gate? |
|---|---:|---:|---|
| woodland trees | **55.4 m** | **0.00 %** | yes |
| hedgerow trees | 54.4 m | 0.00 % | yes |
| shrubs | 33.8 m | 0.35 % | partially — see below |
| grass | **0.0 m** | 52.8 % | **no** |
| grit | 0.0 m | 94.3 % | **no** |

Woodland stops dead at 55.4 m against a gate edge of 52 m. **And the instrument
discriminates**: grass and grit, which read no `D` gate at all, run right up to
D = 0.0 m. A distance measure that reported a floor for everything would have
been measuring itself.

The 0.35 % of shrubs below 52 m is explained rather than excused: shrub density
uses `edge = exp(-((wood - 0.34)/0.22)**2)`, which is **0.092 even at
`wood = 0`** — a Gaussian, not a gate. So a thin shrub population leaks into the
near band at ~9 % of the edge-band rate. That leak is the only woody cover the
band currently has, and it is why the band reads as "blank grass" rather than
bare earth.

---

## R2-1887 — DECIDED: the eleven hero tree modules are declined; `tree_italian_cypress` is dropped, not rebuilt

Acting on R2-1881/1883. **Declined:** per-item hero modules for the eleven trees
occupying the top eleven ranks of `WAVE2-RANKING.md` §3. Their rank rests on a
grass-derived `min_depth_m 4.577` and a grass-derived `peak_px 2160`;
re-measured they peak at 280-1,380 px at 33-79 m, and `build_terrain.py` already
places 26,641 of them from a 33.26 M-triangle library.

**`tree_italian_cypress` is DROPPED rather than rebuilt.** It is KNOWN BAD
(R2-1341, reads as bay laurel at 1:1, flat untapered ribbon branches) and
`world/items/tree_italian_cypress.py` (93,144 bytes) should not be gated. The
reason it can be dropped is stronger than the reason it is broken:
**`VEG_tree_cypress0` does not exist in the assembled world.** No cypress is
ever placed at L0, so the ~800 k-triangle L0 spray that stopped two builds has
no frame to appear in. Its framing derivation, relief budget, pixel-footprint
work, GN instancer and negative-controlled selftests remain reusable and should
be salvaged rather than discarded with the module.

**Kept:** `paddock_avenue_tree`. 24 instances, nearest surface 32.92 m,
107.8 px/m, 1,272-2,113 px at its authored 11.8-19.6 m heights. It is the only
tree row whose hero framing survives measurement.

**Superseded, not deleted:** `WAVE2-RANKING.md` §5a's needle-crossover ladder and
§5b's triangle arithmetic are correct arithmetic on a wrong premise. The 12.69 m
crossover is unreachable — nearest tree of any species is 32.92 m, nearest pine
84.03 m.

---

## R2-1888 — IN FLIGHT: the near-band tier, built as a NEW module so the live file is not touched

`world/build_nearband.py` is being written against this spec. It is a new file;
**`build_terrain.py` is imported, never edited**, because it is live and a
rebuild is in flight carrying the R2-1150 ground fix into the film.

Density is the **exact complement of the emptier**:

```
nb_density = (1 - smoothstep(52, 150, D)) * smoothstep(2.0, 14.0, f) * habitat
```

so near-band + woodland is roughly constant in D **by construction**, and the
no-cliff property is structural rather than tuned. It must still be verified by
a density-vs-D table across 0-300 m showing no step at 52 m or 150 m — the
ground fix's author caught tiers that would have laid visible rings at 200 m and
520 m, and a standoff relaxed to a hard new radius is that defect at a new
distance.

Height ceiling ramps with `f` (metres outboard of the corridor rim) so nothing
lands in the runoff or through the debris fence: < 0.6 m at f 2-8 m; scrub to
2.5 m at f 8-20 m; short species only (hawthorn, rowan, birch) at f 20-52 m;
hand back to woodland beyond. `outside_corridor()` is applied EXACTLY to final
positions, not through the 14 m raster.

The placeable unit is a **scrub clump of 1.5-4 m**, not a single shrub: at D
26-52 m the ground is seen at 100-250 m, so 1 px = 20-50 mm and a leaf is
sub-pixel. Same argument that made the sward unit a drift and dropped the count
with the square of the pitch. **The mechanism is shadow at the 12.47 deg sun**,
where the sward fix turned 35 % plan cover into 72 % screen cover.

Variety is held by the population, not by new meshes: the existing library is
reused via `instance_plants()`/`gn_kind()`, which already vary height, breadth,
mirroring, lean, spin, colour, season and canopy per instance. **Must emit
geometry-nodes instances, not plain objects** — `item_gate.py` ~2986 drops to a
`distinct_topologies >= 2` test on the plain-object path, which is precisely
where "one tree spammed a hundred times" would pass. To be re-measured on
`tools/instance_variety.py` against the shipping 310 sources / 1.99 % top share,
with the instrument first shown to reject a deliberately low-variety population.

---

# STAGED BY THE NEAR-BAND VERIFICATION HARNESS, 2026-08-07 late
# Nothing here builds vegetation. This block builds the means to JUDGE it, and it
# spends its length on the instruments rather than on the renders, because four of
# the seven findings below are broken instruments and none of them is a bad render.
# `docs/DEFECT-LOG-R2.md` NOT edited. No render submitted, $0 spent.

## R2-1889 — THE BEAT-6 A/B CAMERAS ARE NOT THE FILM'S CAMERA, AND ONE OF THEM IS 70.79 DEG OUT

`build_terrain._VIEWS_WORLD` carries `b6_2760/2811/2937/2978`, and its own comment
says where they came from: *"lifted straight out of the R2943 path"*, i.e.
`work/r2941/film17_R2943_path.json`, because those are the frames that rendered the
only 4K stills of the ending. **That file is not the camera `docs/LIVE-CAMERA.md`
declares.** Compared frame by frame against `live_campath.load()`:

```
            position        aim            lens
f2760       0.0000 m        9.51 deg       0.000 mm
f2811       0.0000 m       15.88 deg       2.504 mm
f2937       0.0000 m       70.79 deg      30.922 mm
f2978       0.0000 m       70.79 deg      55.996 mm   (74.00 live vs 129.99)
whole film  max 14.71 m    max 146.72 deg  max 55.996 mm
```

**The position is identical and the aim is not**, which is the worst possible shape:
every check that compares camera POSITIONS passes. At f2760's 81.14 deg horizontal
field, 9.51 deg is **450 px of a 3840 px frame**; at f2978 the two cameras are not
the same shot at all.

This is not a defect in the R2-1661 ground A/B *as an A/B* — both its arms used the
same wrong camera, so its before/after comparison is internally valid. It is a
defect in what that A/B is evidence ABOUT: it judged the ground fix on a frame the
delivered film does not contain. **f2978, the declared CONTROL frame of that A/B —
"if this frame gets worse, the fix is wrong" — is 70.79 deg and 56 mm away from the
film's f2978.**

`tools/r2_1881_bake_cams.py` therefore takes the camera from `live_campath.load()`,
which takes no path argument, instead of from `_VIEWS_WORLD`.

**Caveat, stated because it will bite:** R2-1702 folded `CLOSING_LENS_HOLD_END_MM`
74.0 -> 130.0 into the generators, and the rebuild in flight will regenerate the
camera. When it lands, `docs/LIVE-CAMERA.md` must be re-declared and every number
in this block re-measured; `live_campath` will RAISE until it is, which is the
intended behaviour and not a fault.

## R2-1890 — THE f2760 REFERENCE

`f` from the declared live camera, `render/film17_path.json`, sha256 `67679807…`:

```
position   (420.07278, 88.50896, 60.27535)      altitude 60.28 m
quaternion (0.799404, 0.591929, -0.061191, -0.082639)   |q| off unit 1.2e-7
lens       21.0218 mm on a 36 mm horizontal sensor
field      81.14 deg horizontal, 51.43 deg vertical at 3840 x 2160
elevation  -16.96 deg     bearing 78.20 deg     roll 0.000 (right.z = -0.0000000)
grade      AgX, look None, exposure -3.628  (world/film_exposure.py FILM_EXPOSURE)
```

The camera stands at circuit station **s = 17.2 m, u = -120.57 m** — 120 m outboard
of the pit straight — and the frame centre lands on the ground **207.0 m away at
s = 172.8, u = +1.84**, i.e. dead on the racing line.

**What it frames, measured on 60,000 `TER_Ground` samples through that camera:**

```
ground fills                   31.5 % of the frame        (1,631 of 5,184 tiles)
of that ground, near band      15.3 %   (D <= 52 m, 250 tiles)
of that near band, EVACUATED   100.0 %  (250 of 250)
E  = evacuated near band       4.82 % of the whole frame
E_allband = evacuated ground   24.59 % of the whole frame at any distance
```

**Not one ground tile inside 52 m of the track that this camera sees has a woody
instance within 10 m of it.** Not "mostly" — 250 of 250. The `smoothstep(52.0,
150.0, D)` at `build_terrain.py:3724` is visible in the frame as a total absence,
and the client described it accurately.

## R2-1891 — THE SECONDARY FRAMES, AND THE MEASUREMENT THAT CHOSE THEM

`tools/r2_1881_nearband_ref.py --scan` over all 2,978 frames of the live camera.
The statistic is stated before it is used:

    E(f) = screen area of ground with D <= 52 m AND no woody instance within 10 m,
           over the whole 3840 x 2160 frame

by 40 px screen tile with the nearest ground sample winning each tile — a depth
buffer, so it is bounded by construction. 52.0 is read off the failing line, not
chosen; 10 m is R2-1884's published threshold, reused so the numbers compare.

```
beat          frames   max E   @f     mean E   max E_all   @f     mean E_all
1_opening        792  0.0156   235    0.0016     0.0889     32      0.0223
2                108  0.0120   900    0.0042     0.0812    806      0.0585
3                156  0.0179   944    0.0042     0.0556    939      0.0144
4_transit        134  0.0291  1156    0.0142     0.1113   1161      0.0431
5_lap           1524  0.0442  2089    0.0091     0.1555   2714      0.0532
6_ending         264  0.0633  2832    0.0461     0.4101   2917      0.3098
```

Chosen greedily on E with a 60-frame separation from f2760 and from each other, so
the picks are not three views of one shot:

| frame | E | E_all | lens | ground | centre hits ground at | why this one |
|---|---:|---:|---:|---:|---|---|
| **2760** | 0.0482 | 0.2459 | 21.02 | 31.5 % | s=172.8 u=+1.84, 207 m | **the client's own frame** |
| **2832** | **0.0633** | 0.3466 | 19.18 | 42.4 % | s=62.7 u=+114.9, 366 m | **the maximum E in the entire film** |
| **2933** | 0.0534 | **0.3735** | 50.49 | 48.8 % | s=3314.7 u=+80.2, 609 m | a 50 mm lens and the largest E_allband among the separated picks — catches a fix that only works wide |
| **2089** | 0.0442 | 0.1117 | 73.55 | 12.7 % | s=1973.2 u=-0.36, 170 m | **the beat-5 maximum**, 2 km away round the circuit on a 73.6 mm lens. The generalisation frame: if the fix only helps the ending, this says so |

`void_frac_of_near` is **100.0 %** on every one of them, and on f2811 and f2978 too.

**The sward-fix precedent's frames re-measured on the live camera:** f2811
E = 0.0465, f2978 E = 0.0496. Both are legitimate, both are beat 6, and **neither is
the film's maximum** — f2832 is, by 36 % over f2811.

## R2-1892 — INSTRUMENT PROVED ABLE TO FAIL: `tools/instance_variety.py`, AND THE HOLE IT CANNOT SEE

Six populations manufactured at run time by `tools/r2_1881_variety_control.py`, each
with a KNOWN true answer, then fed to the **shipping guard, unmodified**:

```
arm            what it really is                     STAGE RESULT               exit
spam           4,000 instances, ONE source           INSTANCE_VARIETY_SPAM  100.0 %  1
boundary_hi    4,000 over 50 sources, top 45 %       INSTANCE_VARIETY_SPAM   45.0 %  1
boundary_lo    4,000 over 50 sources, top 35 %       INSTANCE_VARIETY_CLEAN  35.0 %  0
varied         4,000 over 50 sources, top 2 %        INSTANCE_VARIETY_CLEAN   2.0 %  0
empty          nothing realized                      INSTANCE_VARIETY_VACUOUS        3
plainspam      ONE mesh, 2,000 PLAIN OBJECT COPIES   INSTANCE_VARIETY_VACUOUS        3
```

**It can fail.** `spam` is the client's red line built on purpose and the guard says
so, names the mesh, and exits 1. `boundary_hi` and `boundary_lo` differ *only* in
the share of one mesh, ten points either side of the tool's own
`SPAM_TOP_SHARE = 0.40`, and land on opposite verdicts — so SPAM is a live function
of the distribution and not a constant.

**AND IT IS BLIND EXACTLY WHERE IT MATTERS.** `plainspam` is one mesh copied two
thousand times — the named red line, crossed as hard as it can be crossed — and the
guard reports `TOTAL 0 realized instances` and refuses. The cause is one line:
`instance_variety.py` iterates `depsgraph.object_instances` and `continue`s on
`not inst.is_instance`, so **a module that emits plain objects contributes zero to
every number it reports**. The verdict comes back VACUOUS, which reads as *"the
instrument had nothing to measure"* and not as *"the client's red line was
crossed"* — and those two are indistinguishable to anyone reading the token.

This is the same hole one level up in `tools/item_gate.py` ~2986: with no realized
instances, `gn_instanced` is False, `realized_instances()` is never consulted, and
the variation test degrades to `cv_size >= 0.03 and distinct_topologies >= 2` —
**two distinct shapes**. Against the shipping instrumented world's 310 sources and
1.99 % top share, that is not a guard.

**CONSEQUENCE FOR `world/build_nearband.py`, and it is a hard requirement, not
advice: the near-band tier MUST emit geometry-nodes instances.** If it emits plain
objects, both guards go quiet, the variety number does not move off 4,688,475 /
310 / 1.99 % because the new population is not in it at all, and R2-1885's
"must not move top share above 2 %" becomes vacuously true. The arms and the
commands are in `tools/r2_1881_variety_control.py`; run them before believing any
variety reading on a new tier.

## R2-1893 — INSTRUMENT PROVED ABLE TO FAIL: the near-band metric, including the version of it I got wrong

`tools/r2_1881_nearband_ref.py --selftest`, 15 controls, `>> STAGE RESULT:
R2_1881_NEARBAND_REF_OK`. The ones that carry weight:

```
PLANTED  ground planted AT a woody origin reads 0.000000000 m, 0.00 % blank
BARE     a manufactured ring at D = 10 m -- inside the evacuation by construction --
         reads 100.00 % blank
E2E      the SAME frame with the woody population EMPTIED: void/near 100 %
E2E      the SAME frame with a tree ON every sample: E exactly 0.0000, same 1,631 tiles
E2E      all three arms share one framing, so anything E does is the planting
V        cKDTree agrees with brute force to 0.000e+00 over 1,500 x 6,000
P        a point on the forward axis lands on (1920.000000, 1080.000000)
N        20 m behind the lens, and beside-and-behind, contribute zero
```

**Two of my own instruments were broken and the controls found both.**

1. **The BARE control indexed a row where it meant a column** (`P[0]` for `P[:,0]`),
   so the "ring at D = 10 m" was actually at a mean D of **102.48 m** — outside the
   evacuation, where the answer is not known. It reported 83.33 % blank, which is a
   plausible-looking number and would have been believed. The control that caught it
   is the one that asks whether the control is what it says it is.
2. **The first E summed `ppm^2 * a_sample` over samples and returned E = 46.22** for
   a quantity bounded by 1. The dump is a vertex sample of the terrain mesh and the
   mesh is denser near the corridor — *exactly the band being measured* — so an
   area-weighted sum multiplies the defect by the tessellation. **The bound is what
   caught it**; a statistic with no bound would have shipped.

**The honest limits, stated rather than implied.** No occlusion — ground behind a
grandstand still counts, so E is an upper bound on exposed void, the same
declaration `lap_shotscale.py` makes. And the point cloud's woody set is **27,969
trees, hedgerow trees and avenue**, not R2-1884's 72,297: `work/w2_0/retier_a10/
world_points.npz` carries no origins for shrubs or saplings, so E is measured
against structural woody only and overstates the void relative to R2-1884's
definition. Both numbers are printed on every run.

## R2-1894 — INSTRUMENT PROVED ABLE TO FAIL: `tools/r2_1821_ground_detail.py`, and it is only valid PAIRED

Its own manufactured controls pass on a real 4K frame
(`render/r2_1661/before_b6_2811.png`): synthetic sward at 55 % cover reads **9.04**
against the 4.09 pit-building reference, the same ground with the tufts removed
reads **0.63**. It can see cover.

Then fed a patch KNOWN BARE and a patch KNOWN PLANTED, derived from the geometry
rather than by eye, on that same already-paid frame, measured on `CAM_b6_2811`'s own
reconstructed pose (not the live one — see R2-1889):

```
KNOWN BARE    D <= 52 m, no woody within 10 m   n=  313  median sd 3.65
KNOWN PLANTED woody within 5 m                  n=  342  median sd 5.44
far bare      D >  52 m, no woody within 10 m   n= 1872  median sd 2.03
                                                    planted / bare = 1.49x
```

**1.49x, with interquartile ranges that overlap** (bare p75 4.92 vs planted p25
3.49). On its face the instrument barely discriminates. It does not, and the reason
is a confound worth more than the number:

```
median depth   bare 263.9 m   planted 682.1 m   far-bare 436.9 m
```

**The metric is not depth-normalised.** The same tuft subtends more pixels near the
lens, which is why *bare* ground in the near band (3.65) reads higher than *bare*
ground beyond it (2.03) on identical planting. The planted tiles are 2.6x further
away than the bare ones, so the raw comparison is fighting the depth gradient.
Matched by depth band:

```
 150-300 m   bare med 3.68   planted med 6.32   1.72x
 300-600 m   bare med 3.90   planted med 7.56   1.94x
 600-1200 m  bare med 2.24   planted med 5.64   2.52x
             depth-matched planted/bare = 2.07x   (unmatched 1.49x)
```

**Verdict: fit for a PAIRED comparison — the same tiles, before arm against after
arm, where depth is held fixed by construction — and NOT fit for comparing one
region of a frame against another region at a different depth.** Its own
`DEFAULT_REGIONS` table does the latter, comparing "grass beside the pit building"
against "pit buildings (reference)" at unequal depth, and therefore understates.
The harness in R2-1895 is paired.

**And my first version of this control was itself the broken instrument.** I cut
1024 x 640 rectangles over the densest bare and densest planted ground and compared
region sd: 4.01 vs 4.11, ratio 1.02x. The densest bare rectangle available anywhere
in the frame is **21 % bare** and the densest planted one **22 % planted** — the
other ~79 % of each is track, buildings, sky and ground of the other class. **A
rectangle is not a patch**, and a control whose subject is a fifth of its own area
cannot discriminate anything. Redone per tile at the metric's own 32 px grid, where
purity is 100 % by construction.

## R2-1895 — THE HARNESS, AND THE REFUSAL THAT COSTS NOTHING

`tools/r2_1881_ab.sh BEFORE_MODULE.py AFTER_MODULE.py BEFORE.blend AFTER.blend`

```
1  bake CAM_f2760 / f2832 / f2933 / f2089 into BOTH arms from live_campath.load()
2  compare the two arms' camera manifests -- identical or STOP, before any GPU
3  render 4 frames x 2 arms, 3840x2160 @512, on the 5090 broker
4a verify each job's BROKER `effective` line: exposure=-3.628, camera=CAM_fNNNN,
   resolution_percentage=100
4b crops chosen by the measurement, then the two metrics and 1:1 A/B strips
```

**Phase 2 is R2-1151 made mechanical.** That entry cost a report to the client of
"the fix does not work" from an arm that had rendered with a socket unlinked. Prose
does not stop that; a byte comparison of the two arms' cameras, resolution, sensor,
samples, view transform, look, exposure and DOF state does. Proved both ways:

```
arm A vs arm B (same builder, twice)            >> STAGE RESULT: R2_1881_ARMS_MATCHED
arm A vs arm C (C graded at the OLD -2.70)      >> STAGE RESULT: R2_1881_ARMS_DIFFER [exposure]
```

Arm C reproduces the historical defect on purpose: the pre-contract harness graded
at -2.70 with a Medium Contrast look, 0.348 stops and a tone curve from the film.

**Phase 4a exists because the blend and the broker are two different claims.** The
blend declares a grade; the broker declares what it *actually rendered with*, on its
own line, and only the second is evidence. The r2_1661 jobs are the worked example:
`job ada0865a2ec0 effective — camera=CAM_b6_2811 exposure=-3.628 lens=22.0`.

**The baked cameras are verified against Blender's own projection, not asserted.**
`work/r2_1881/verify_bake.py`: position 1.7e-6..5.6e-6 m, aim 1.8e-6..7.2e-6 deg,
lens 3.1e-8..3.5e-6 mm, and **max |my projection - Blender's world_to_camera_view|
= 0.0671 px** over 400 scattered points per camera. My projection instrument and the
renderer agree to a fifteenth of a pixel, so the crops are cut from the pixels the
measurement chose.

Two side-findings from writing that verifier:

* **Blender does NOT normalise a quaternion it is handed.** The path file rounds to
  six decimals so |q| is off unit by ~4e-7, and the residual lands in the object
  matrix as scale. Fixed in the baker; `tools/beat1_elevation.py` already knew and
  said so at its line 19.
* **`acos` cannot resolve a small angle.** My first aim check used
  `acos(dot(a,b))` and reported `9.90e-03 deg` for f2089 and exactly `0.00e+00` for
  the other three — because near dot = 1 float64 acos has a resolution of about
  1e-2 deg. Re-measured with `asin(|a x b|)` the true errors are 1.8e-6..7.2e-6 deg.
  Anything in this tree that compares camera aims with `acos` is quantised at 1e-2
  deg and cannot see a smaller drift than that.

**Crops are chosen by the measurement, not by eye** — `--crops` returns the densest
windows of evacuated near-band tiles with non-maximum suppression, in a regions JSON
that both `r2_1821_ground_detail.py --regions` and `peep.py ab --box` consume:

```
f2760_nearband_0  [1360, 640 1280x800]  21 % of the box
f2832_nearband_0  [2360, 840 1280x800]  21 %      f2933_nearband_0  [  40, 480]  22 %
f2089_nearband_0  [1400,   0 1280x800]  17 %
```

Boxes 0 and 1 per frame are worth cutting; box 2 falls to 2-5 % and should not be
used as evidence. **DOF is forced OFF in both arms** — the r2_1661 arms rendered
`dof=True`, the near band is the FOREGROUND of these frames, and a defocused
foreground is the one thing that would make a scrub tier and an empty field look
alike.

## R2-1896 — THE TWO ALREADY-PAID PNGs ARE NOT NEAR-BAND EVIDENCE. DO NOT SCORE THEM.

`~/vast-render/out/064b88b666c9.png` and `650d03fabe40.png` are 3840x2160 and paid
for, and the instruction to score rather than re-buy them is right in general. Their
own broker `effective` lines say what they are:

```
camera=GATE_CAM   lens=35.0   exposure=0.0   color_mode=RGBA
064b88b666c9   alpha 0.686   mean 0.1209   crushed 31.3 %
650d03fabe40   alpha 0.091   mean 0.0363   crushed 90.8 %
```

**`GATE_CAM` is `item_gate.py`'s witness camera.** These are single-item witness
renders on a transparent film at exposure 0.0 — 650d03fabe40 is 90.8 % black. They
are not the film's camera, not the film's lens, not the film's grade and not on an
opaque background. A/Bing a near-band terrain frame against one of them would differ
in **camera, lens, exposure and film transparency at once**, which is R2-1151 four
times over. Scored, and the score is: unusable here. **$0 saved is the wrong way to
put it — a meaningless number avoided is the right one.**

## R2-1897 — COST, AND WHAT IS IN FLIGHT

**Estimated cost of the full harness run, stated before the spend as required.**
From `render/r2_1661/ab.log`, 3840x2160 @512 on a terrain-only world of this weight
ran **129.2-165.6 s** per frame on the 5090.

```
8 renders (4 frames x 2 arms) @ ~150 s        ~20 min GPU
scene load, 2 arms @ ~620 s (broker: load 622s / 7 %)   ~21 min
provisioning, observed up to 903 s once                 ~0-15 min
                                        1.0-1.3 h at $0.4387/hr
ESTIMATE  $0.44 - $0.57 ;  budget $1.20 for one re-run
```
Adding the r2_1661 1080p regression pair (t5_verge, esses) is about **+$0.10**.
The two terrain-only arm builds are LOCAL and free (`build_s 1925.7` each, ~64 min
wall for the pair) but need the 11 GB box, which is currently at **0 GB available**.

**IN FLIGHT AT THE TIME OF WRITING — none of it touched, nothing torn down.**

```
assembly11 rebuild   PID 1835390, 5.5 GB RSS, render/world/assembly/r2/assemble.py
                     -> assembly11.blend. Owns world/, the box's memory, and the
                     answer to whether R2-1701's four stale generators reach a frame
broker 8761          instance id-051, $0.4387/hr, up 2.9 h, spend $1.37,
                     film18_breach.blend loaded, running r21601_open frame 203,
                     depth 4. ANOTHER AGENT'S. Not touched
broker 8760          GPU down, depth 0, idle 69 min. Not touched, not torn down
winding_audit        PID 1864229, hospitality_deck sheet-facing repro
r2_1821_paved_check  PID 1858853 -- the `paved` predicate landed in build_terrain
                     at 18:35 and is being checked. Same file build_nearband must
                     not collide with
leases               inflight-2026-08-07 (312 paths), r2-1761-debt (gitguard +
                     report_repro), inflight-auto (which swept this block's own new
                     tools within seconds of their being written -- the guard from
                     R2-17xx #115 working, on me)
```

**Handover to whoever lands `world/build_nearband.py`:**

1. It **must** emit geometry-nodes instances, not plain objects (R2-1892).
2. Build both arms terrain-only and LOCAL, after the rebuild frees the box.
3. `tools/r2_1881_ab.sh BEFORE_MOD AFTER_MOD BEFORE.blend AFTER.blend`. It refuses
   at phase 2 for $0 if the arms differ.
4. The bar to clear at f2760 is `void_frac_of_near` **100.0 % -> materially below
   it**, re-measured with `--frame 2760`, and `E` down from 0.0482.
5. Re-run `tools/instance_variety.py` on the assembled world and hold top share
   below 2 % (R2-1885) — but read R2-1892 first: that number cannot see a
   plain-object tier at all.

---

## R2-1898 — READINESS RULING on `world/build_nearband.py`: three of four blockers closed, and the fourth is now ONE question a frame can answer

Ruled on artifacts, never on the source file. Reading 112 kB of plausible Python
and concluding it works is R2-725's mistake, and `WAVE2-RANKING.md` §6 already
records four tree modules that looked substantial and carried no verdict.

**CLOSED — the external variety guard, which was the hard requirement.**
`tools/instance_variety.py` on the built blend:
**`TOTAL 4,902,372 realized instances`, 823 sources, top share 2.0 %,
`INSTANCE_VARIETY_CLEAN`.** Non-zero is the whole point: R2-1892 proved that
tool returns `TOTAL 0 realized instances` / `VACUOUS` on a plain-object tier, so
a zero here would have meant *both* guards were blind. The tier is genuinely
GN-instanced. Note the module's own `nearband_instance_diversity ok=1` did
**not** close this and could not have — a module's internal diversity check is
not the guard that has the hole.

**CLOSED — the stale-terrain defect.** The first measurement was taken against a
`build_terrain.py` that changed 14 minutes later (23:29 read, 23:43 write) —
the exact failure `assemble.py`'s content-fingerprinting exists to catch,
recurring within the hour. Re-measured against md5 `01c5c684…` with the
fingerprint recorded.

**CLOSED — reuse and cost.** 233.8 M instanced tris = **1.45 %** of terrain's
16.16 G. Base library +19.97 M (+60 %), dial `NB_TREE_LIB_TARGET`. Worth noting
against R2-1883: terrain 33.5 M + near-band 20.0 M = **53.5 M base-library
triangles now build on this 11 GB box**, against the 35 M that two builds called
impossible.

**OPEN — the 40-52 m cover step, and it is now a single well-posed question.**
The module's own gate reports **`ok=0`**: cover 0.084 -> 0.232 across 40-52 m.
Everything else about the no-cliff case is strong, and the complementarity works
exactly as designed — **from 50 m outward the total is flat**:

```
0.232 0.201 0.194 0.194 0.165 0.190 0.178 0.189 0.186 0.173 0.175   (far field 0.170)
```

As near-band density falls 570 -> 0 per ha, woodland rises 15 -> 146, **and the
sum does not move.** Mean cover in D 0-52 m went **0.0008 -> 0.1065 (133x)**,
bins under 160 m with zero cover **3 -> 0**, and the step at the 150 m gate edge
*improved* 0.0157 -> 0.0080.

**Why the remaining step may not be a defect at all.** `max_step` was **1.769
before** the module and 1.839 after — it pre-existed. It is the outboard ramp
`smoothstep(2, 14, f)` turning on, and `f` is metres outboard of the corridor
rim, so **it tracks the fence line, not a radius.** The rim varies 12-88 m
around the circuit. **A ring is a circle at constant radius; an edge that
follows a rim varying by 76 m is the runoff boundary**, which a real circuit
genuinely has and which SHOULD be visible. R2-1149's rings at 200 m and 520 m
were circles. This is not that shape.

**But that is an argument, and arguments do not decide here.** The author tried
to remove the step, failed, and reported the failure rather than moving the
threshold — moving the N1/N2 crossfade inboard raised both bins and made the
relative step slightly worse. **Bought the frame instead** (authorised, <= $1.20,
f2760 first then f2832): the question put to it is *does the 40-52 m transition
read as a ring, or as the runoff edge?* If it reads as a ring, the module does
not ship. The metric cannot answer this and that is precisely what 4K is for.

**Shadow transfers to the woody layer**, confirming R2-1150's mechanism is not
specific to sward: plan cover 0.0889 -> **0.3318** with shadow at the 12.47 deg
sun, **3.733x amplification**.

**Selftest 62/62 with 16 negative controls fired**, including
`tall_species_refused_in_the_band` (an oak at f = 25 m), `inside_rim_candidates_refused`,
`one_mesh_spammed_refused` and `house_default_detail_8_would_be_refused`.

**ORDERING — `build_nearband` goes AFTER `terrain` in `MODS`, unconditionally.**
Not a judgement call: it captures `CameraPath`, `GridZ`, `Ground`, `Raster` and
`build_library` from terrain via a context manager that restores them, and its
density is defined as the exact complement of terrain's `wood` gate. It cannot
precede what it reads.

**UNRESOLVED BY DESIGN — the `built` district, referred to its owner.** This
tier places **45.2 instances/ha inside the `built` district against woodland's
1.8/ha (25x)**, which disagrees with R2-1821's deliberate retention of `built`
as a tree keep-out (`build_terrain.py:3749` — *"a tree keep-out around a paddock
genuinely IS a district"*). The tier's case is that this is **amenity planting**
— hedges, planters and ornamentals off the declared paving edge — and not
woodland. **That author is mid-pass in that file and rules on it, not us.**
Written into `world/build_nearband_HANDOVER.md` as a 4-patch spec, **not
applied**. All no-cliff evidence above is computed over `built < 0.30`, so this
dispute cannot contaminate it.

**Three defects the module's own checks caught during development**, documented
rather than buried: `gen_stone` returns ~1.5 m meshes regardless of size class
(a 1.5 m boulder in a 0.62 m verge clump); clump parts scaled by declared rather
than measured extents; hedge segments normalised uniformly, which would have
divided their length by their height.

---

# R2-1898 to R2-1902 — THE NEAR-BAND A/B, RENDERED AND JUDGED
# 4 frames x 4K on the 5090, $0.129 spent of $1.20 authorised.

## R2-1898 — CORRECTION TO MY OWN R2-1889: THE `_VIEWS_WORLD` CAMERAS ARE NOT WRONG ANY MORE, AND THE REASON MATTERS MORE THAN THE ERROR

R2-1889 said `build_terrain._VIEWS_WORLD`'s `b6_*` entries were 9.51 deg (f2760) to
70.79 deg (f2978) off the film's camera, and that the R2-1661 ground A/B was
therefore judged on frames the film does not contain. **That was true at 22:40 and
false by 23:21**, and I am striking it rather than leaving it to be cited.

`docs/LIVE-CAMERA.md` was re-declared at 23:21 under R2-1701:
`render/film17_path.json` -> **`render/film19_path.json`**, sha256 `363e4e88…`.
Measured against the R2943 path that `_VIEWS_WORLD` was lifted from:

```
NEW live (film19) vs R2943, beat 6 (f2715-2978):
   worst aim difference anywhere in the beat   0.0002 deg at f2718
   f2760 / f2811 / f2937 / f2978               0.0000 m, 0.0000 deg, 0.0000 mm
```

**Beat 6 of the declared camera is now bit-identical to the R2943 path.** R2-1702's
fold of the beat-6 aim and lens into the generators landed in the rebuild, so the
camera moved onto the entries, not the other way round. `_VIEWS_WORLD` was right and
`film17_path.json` was the outlier. The r2_1661 ground A/B stands.

**What survives, and it is the whole point:** `_VIEWS_WORLD` holds a hardcoded COPY
of the camera. It agreed today by 0.0002 deg and disagreed yesterday by 70.79 deg,
and nothing in the tree would have told you which day you were on. This harness
reads `live_campath.load()` and so tracks the declaration whichever way it moves —
the arms rendered below are on `film19_path.json` because that is what was declared
when they were baked. **A copy that happens to be right is not a source of truth.**

For the record, film17 -> film19 at this harness's frames:
```
f2760  dpos 0.0000 m  daim  9.5124 deg  dlens 0.0001 mm
f2832  dpos 0.0001 m  daim 30.0821 deg  dlens 6.2209 mm   (lens now 25.402)
f2933  dpos 0.0000 m  daim 70.7859 deg  dlens 27.6533 mm
f2089  dpos 0.0000 m  daim  0.0001 deg  dlens 0.0000 mm
whole film: max position move 21.399 m at f2177
```

## R2-1899 — BOTH ARMS CAME OUT OF ONE FILE, BECAUSE A REBUILT `BEFORE` WOULD NOT HAVE BEEN AN ARM

The obvious BEFORE arm is a fresh `build_terrain` run without the tier. It is the
wrong arm and the reason is on disk:

```
world/build_terrain.py when nearband.blend was built   01c5c684d65b3c47610562747f5897fa
world/build_terrain.py now                             bdeac55c3b7384abd87bd7002343620a
```

**The terrain module moved between the two builds.** A BEFORE built from today's copy
would differ from the AFTER in the terrain module as well as in the tier — R2-1151
again, and invisible, because both arms would log a clean `build_terrain` run.

So `tools/r2_1898_split_arms.py` takes both arms out of `world/nearband.blend`: the
AFTER as built, the BEFORE the same file with the tier's 294 `VEG_nb_*` objects out
of the render. One terrain build, one rng stream, one grass field, one library, one
camera. **The arms differ in the tier and in nothing else, by construction.**

```
>> arms_loaded    28,898 objects, 294 VEG_nb_*, 1 light, NearBand collection: ABSENT
>> cameras_baked  CAM_f2089/2760/2832/2933 from film19_path.json  363e4e88b30207ad
>> grade          AgX, look None, exposure -3.628, 3840x2160, dof off
>> after_saved    realized_instances 4,902,372
>> before_saved   realized_instances 4,892,105
>> arms_differ    drop 10,267
```

**10,267 is exactly `nb_instances` from the module's own `work/nearband/stats.json`.**
The tier is removed completely and nothing else is. That control is the mirror of the
parity check and both are needed: parity proves the arms are the SAME where they must
be, and it would pass just as happily on a file compared with itself.

**My gate on that control was wrong and reported FAIL on a correct split.** I had
written `drop > 100000`, assuming the tier would be millions of instances; it is
10,267 emitters carrying 233.8 M triangles, 22.8 k tris each. A magic number where a
cross-check was available. The right control is `drop == nb_instances`, and it holds
exactly.

Parity, on the arms actually rendered:
```
campath / sha256 / resolution / sensor / samples / view_transform / look /
exposure / use_dof / cameras          ALL IDENTICAL
>> STAGE RESULT: R2_1881_ARMS_MATCHED
```
And the grade as the BROKER ran it, per job, not as the blend claims it:
```
a0ffaa0f85f3 after  camera=CAM_f2760 lens=21.0217 exposure=-3.628 dof=False res%=100
1706e93cec7e before camera=CAM_f2760 lens=21.0217 exposure=-3.628 dof=False res%=100
5bff2948d404 after  camera=CAM_f2832 lens=25.402  exposure=-3.628 dof=False res%=100
217ff437a5d5 before camera=CAM_f2832 lens=25.402  exposure=-3.628 dof=False res%=100
>> STAGE RESULT: R2_1900_GRADE_OK
```

## R2-1900 — THE 40-52 m TRANSITION IS THE RUNOFF EDGE. IT IS NOT A RING.

**The question was made falsifiable before the frame was looked at.** The author's
account is that the step is the outboard ramp `smoothstep(2, 14, f)`, `f` = metres
outboard of the corridor rim. That predicts the boundary lies on an **iso-`f`** curve,
which WANDERS with the fence line because `platform_edge` runs **12.25 to 70.67 m**
round the lap. The defect hypothesis predicts an **iso-`D`** curve — a fixed-width
band answering to nothing, which is what R2-1661 caught as density rings at 200 m and
520 m. These are different curves, so the picture can choose.

`work/r2_1881/ring_or_edge.py` projects both into each frame and reports whether they
separate enough for the frame to decide:

```
f2760   9,639 in-frame stations, screen separation p50 8 px, p90 170 px, max 371 px
        >> R2_1899_RINGTEST_ADJUDICABLE
f2832   9,856 in-frame stations, p50 9 px, p90 117 px, max 360 px
        >> R2_1899_RINGTEST_CANNOT_ADJUDICATE at p90 -- but its corner box separates
           by 360 px and is usable; the frame-wide verdict is withheld, the corner's is not
```

**THE VERDICT, from the two corner crops at 1:1** —
`render/r2_1881/OVL_f2760_ringtest_0.png` and `OVL_f2832_ringtest_0.png`:

At both corners the iso-`f` curve swings wide around the paved runoff apron and the
iso-`D` curve cuts straight across it. **The vegetation boundary follows the apron.**
The dense scrub band traces the runoff's outer edge around the bend, including the
tight curvature at the apex, and stops where the runoff programme stops. The iso-`D`
line crosses the same scrub band diagonally with **no change in the vegetation on
either side of it** — at f2832 it is drawn straight through uniformly dense scrub.

**A constant-`D` ring cannot bend around a runoff apron, and this boundary does.**

Supported by measurement as well as by the crop. `work/r2_1881/twoway.py` bins the
SAME pixels two ways, at fixed depth (90-320 m, so R2-1893's depth confound cannot
act) and clear of the barrier line (`f` from 4 m):

```
sweep f, holding D fixed    texture moves 5.92x   (rows 14.29x / 2.00x / 1.47x)
sweep D, holding f fixed    texture moves 1.72x   (rows  1.21x / 1.81x / 2.14x)
>> STAGE RESULT: R2_1900_TWOWAY_RUNOFF_EDGE_iso_f
```

**Reported with its weakness: the 5.92x is a mean dominated by one sparse bin.** On
medians the two are 2.00x against 1.81x, which is not decisive on its own. The
measurement points the same way as the crops and does not carry the verdict by
itself; the corner geometry does, and it is unambiguous.

**And the one-way version of this test was wrong, three ways.** Binning the marginal
`D` gave a 2.31x sharper step than `f` and would have returned RING. All three
confounds are real and worth carrying: (a) `D`'s low bins are fed only by the
NARROW-rim stations, so a step there is a change of subpopulation, not of place;
(b) the barrier line stands at the platform edge and reads as very high fine detail
at small `f`; (c) fine-detail sd is not depth-normalised (R2-1893) and the samples
spanned a 22x depth range. **The confounded test gave the opposite answer to the
correct one**, which is the whole argument for two-way binning.

## R2-1901 — WHAT THE FRAME SAYS ABOUT THE CLIENT'S COMPLAINT

f2760, before against after, at the boxes located by the DIFFERENCE MAP rather than
by eye (`work/r2_1881/regions_change_f2760.json`):

```
9.93 % of the frame's pixels changed by more than 1/255;  5.12 % by more than 5/255

region                    before sd   after sd    delta    anisotropy
f2760_change_0 [1000,360]      4.67       6.12   +31.0%    1.08 -> 1.01
f2760_change_1 [2560,560]      5.27       5.91   +12.1%    1.32 -> 1.23
f2760_change_2 [2080,1360]     4.03       4.19    +3.9%    1.09 -> 1.09
```

Anisotropy near 1.0 in both arms, so the gain is geometry and not a change in smear —
the distinction R2-1821 built that second number for.

`render/r2_1881/AB_f2760_change_0.png` is the frame to show the client. BEFORE: the
mid-ground field between the treeline and the road is smooth empty olive with
nothing standing on it — *"blank grass no detail nothing"*, verbatim. AFTER: the same
field carries scattered scrub, low woody stems and a denser fringe along the platform
edge.

**Two honest caveats, neither of which is a reason to hold the module.**

1. **The far field is still bare, and it is in the same frame.** Beyond the near band
   the ground reads pale and empty with sparse twiggy bushes. That is `f` > ~40 m,
   outside this tier's remit and inside the woodland gate's ramp
   (`smoothstep(52, 150, D)`), where cover is genuinely low by design. The near-band
   fix works where it applies and the original complaint is still legible just
   outboard of it. Whoever owns the next pass should read R2-1884's 44.9 % against
   this frame, not against the near band alone.
2. **The new scrub reads as pale twiggy bushes** in this light, matching the existing
   woodland tier's look. Whether that reads to the client as "detail" or as "dead
   sticks" is a real question and it is not one the metrics answer. It is emphatically
   no longer blank.

## R2-1902 — COST AND STATE

```
broker 8760, instance id-053, $0.4601/hr
  spend when I started 00:34   $0.1218
  spend when I finished 00:47  $0.2504
  MY SHARE                     $0.129   of $1.20 authorised
4 frames, 3840x2160 @512, 124-127 s each; 2 scene uploads of 2194 MB at 40.6 MB/s
```
Nothing torn down. Broker 8761 (another agent's `film18_breach` render) not touched.
The instance was already up and carrying `r2_1829/ground_B_rim.blend` for another
workstream; that scene is still cached and its jobs were not cancelled. The only job
ids I cancelled are none — all four of mine completed.

**Frames and crops:** `render/r2_1881/{before,after}_f{2760,2832}.png` (4K),
`OVERLAY_after_f{2760,2832}.png`, `OVL_f2760_ringtest_{0,1,2}.png`,
`OVL_f2832_ringtest_0.png`, `AB_f2760_change_{0,1,2}.png`,
`AB_f2832_ringtest_0.png`, `WIDE_after_f2760_1600.png`, `DIFF_f2760_1600.png`.
