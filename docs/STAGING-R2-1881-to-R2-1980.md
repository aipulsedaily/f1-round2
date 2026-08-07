# STAGING R2-1881 to R2-1980

Staged by the tree-scoping agent, 2026-08-07. Merge by identity, never by position.
**Nothing here was built. This block measures, and it retires a build decision.**

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
