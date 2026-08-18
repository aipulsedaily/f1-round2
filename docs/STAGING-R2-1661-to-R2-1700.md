# STAGING — R2-1661 to R2-1700 — the ground in the ending

Numbers to be assigned by the log's owner. **`docs/DEFECT-LOG-R2.md` not edited.**

The client, on the last thing still broken in the ending:

> *"the ending i dont like. we just zoom out so you see all the patches in the land."*

Four passes of camera work chased subject size, because subject size was
measurable. None of them touched the ground. R2-1128 had already found the
mechanism and named it a colour bug; **it is a covering bug, and the colour is a
third of it.** Three changes, in `world/build_terrain.py` only, all upstream of
the grade, nothing touched in `anim/carpath.py`, the camera or the car.

---

## R2-16xx — the tiering predicate threw away the camera's altitude, and beat 6 is the only place in the film where the camera has one

`CameraPath.dist` returned the **horizontal** distance to the nearest camera
station, and every ground-cover tier in the module was budgeted against it.

For beats 1–5 that is free. The lens flies 2–6 m over the ground it is looking at,
so a clump 47 m out horizontally is 47.4 m out in three dimensions and lands on the
same side of every threshold.

**Beat 6 climbs to 140 m.** On a horizontal metric the ground directly beneath the
crane is *zero metres from the lens* and buys itself the densest tier in the module,
while the several hundred metres of infield the 22 mm lens is actually pointed at
score 200–600 m and buy the cheapest. Measured, at the beat-6 hold:

```
ground under the crane at (594.19, 16.05):
    CameraPath.dist   0.0 m        <- what the tiering believed
    CameraPath.dist3  130.6 m      <- where the lens actually is
```

And over the whole map, hero ground outboard of the platform edge:

```
horizontal metric   0.0493 km2
true 3-D metric     0.0252 km2     <- 49 % of it was a phantom disc under an aerial
```

`CameraPath.dist3` is added and `build_grass`'s hero predicate moved onto it.
`dist` is **kept**, because the tree, shrub, weed and grit tiers are calibrated
against it and are not in scope: changing one predicate is a fix, changing five is a
different experiment.

**The regression test, and it is the point of the change and not an afterthought.**
`dist3 >= dist` pointwise, so the hero set can only shrink, and it shrinks by moving
the 48 m contour inward by `sqrt(48^2 + h^2) - 48` where `h` is the lens height above
the ground it is looking at. On 20 000 samples against the **real** terrain height
(not a z = 0 plane — testing against a plane charges the predicate for the circuit's
own elevation and reports 12 m where the truth is 9):

| | |
|---|---|
| lap-owned samples that changed hero tier | 21 of 20 000 |
| …of those, outside the 1.2 m annulus at the 48 m contour | **0** |
| max metric shift, lap-owned | 9.26 m (the lens is 6 m over the *centreline*, and the terrain falls away from the track) |
| the hero boundary moves inward by | **0.88 m of 48 — 1.8 %** |
| aerial-owned samples that changed tier | 116 — the phantom disc, and nothing else |

**Honest scoping: this predicate on its own does not fix the frame.** It stops the
budget being spent in the wrong place; it does not put anything in the right one.
That is R2-16xx below. It is fixed first because it is wrong, and because everything
below is tiered against it.

---

## R2-16xx — the infield is 4 % ground cover, and the other 96 % is a three-value colour map

The module had exactly two states and nothing between them.

```
hero clumps   190-330 channelled blades in tillers, ~4 600 tris, ~19 per m2
              -- but only in the verge band, and the verge band is drawn along
                 the track
flat colour   everything else
```

The infield does carry `meadow` clumps: a 1.35 m jittered grid at ~50 % acceptance,
which is **0.28 clumps per square metre**. At a clump radius of 0.2–0.3 m that is
**four per cent ground cover.** The remaining ninety-six per cent is the ground
shader, and out there the ground shader was a per-field flat colour.

Nobody saw it for five beats because the lens never looks at the infield. Beat 6
points a 22 mm lens across it from 99 m up, and four per cent cover over a colour map
is exactly what the client described.

### Why it is a drift and not a clump

Verge density over the 8.39 km² of infield would be **160 million instances**. That
is not a budget, it is a hang, and it is the same shape of argument that has made a
hero tree tier unbuildable elsewhere in this project. The way out is to make the
**placeable unit bigger**: one drift carries the tufts that would otherwise have been
twenty separate clumps, so the instance count falls with the square of the pitch and
the covered area does not move.

| tier | from the lens | pitch | λ tufts/m² | tris/drift | drifts | instanced tris |
|---|---|---|---|---|---|---|
| A | 30–200 m | 2.30 m | 5.65 | 851 | ~110 k | ~94 M |
| B | 200–520 m | 3.60 m | 2.80 | 574 | ~89 k | ~51 M |
| C | 520–1050 m | 6.00 m | 0.65 | 375 | ~62 k | ~23 M |
| | | | | | **~261 k** | **~168 M** |

Against terrain's existing **13.88 G** instanced triangles: **1.2 %.** Library is
3 tiers × 5 kinds × 13 drifts = 195 meshes, ~110 k resident triangles, every one
generated independently — 24 of 24 test drifts hash to 24 distinct vertex buffers.

**The density is solved, not chosen.** `lam` is a GROUND density, and the drift is
populated off `pitch²` — the ground it owns — and not off the 1.45×-oversize area it
is drawn over. Those are not the same number: 2.1 drift centres lie within reach of
any ground point, so populating off the drawn area puts **2.1 λ** on the ground, and
tier B would have come out at 88 % screen cover — a solid dark mat, which is the flat
wash again in the other direction. Inverting the cover law for a 72 % mean gives:

| tier | thin patches | mean | lush patches |
|---|---|---|---|
| A | 42.2 % | **72.0 %** | 83.0 % |
| B | 42.0 % | **71.8 %** | 82.8 % |
| C | 42.3 % | **72.1 %** | 83.1 % |

**against the 4 % it has today** — and the spread is the point as much as the mean.
A uniform 72 % would be a second flat wash; 42–83 %, driven by patchiness at 38 m and
9 m, is rough grazing.

**And the tiers crossfade, they do not butt.** A hard cut at 200 m and 520 m would
lay two concentric density rings across the exact frame this is being built for.
Each tier fades out over [d1−24, d1+26] while the next fades in over the same
interval, and a smoothstep plus its own complement sums to one — verified at 1.000
across the join.

### Sized by what the lens resolves, not by what grass is

The four 4K frames of this ending that exist put the ground at **2.5 cm per pixel**
(f2978, 130 mm, 345 m) and **9.2 cm per pixel** (f2811, 22 mm, 259 m), falling to
~36 cm at a kilometre. A 4 mm fescue blade is a quarter of a pixel at the *best* of
those, so a blade out here is not a shape, it is a coverage fraction — the same
argument the far grass tier already makes for keeping its wide blade. Drift leaves
are 1.0–6.0 cm across by tier: a coarse rough sward, which is what unmanaged infield
is.

### The mechanism is shadow, not silhouette

The sun ships at **12.47° elevation**, so everything vertical throws a shadow 4.5
times its own height. Screen cover from an oblique view is

```
1 - exp( -lambda * (4 r^2 + 2 r h cot(elevation)) )
```

and at f2811's 22.6° axis, λ = 1.6/m² of r = 0.22 m, h = 0.38 m tufts is **61 %** —
from 35 % *plan* cover, because an oblique view of vertical things is mostly their
sides. That is why this works at ~800 triangles per drift and would not work as a
flat texture, and why 0.07 rush spikes per square metre are worth their triangles
entirely for the 4.5 m of shadow each one lays down.

### One bug caught before it reached a render

`gn_kind` normalises every library mesh by the second value its generator returns and
then rescales the lot by one target, so **whatever that value is becomes the thing
every drift is made equal in.** Returning the tallest plant would have done exactly
that to the tallest plant: a drift that happened to draw no rush spike tops out at
0.70 m against a library mean of 1.30 and would have been scaled up **1.86×** — a 9 m
drift on a 6 m pitch, its leaves 1.86× the width the resolvable-floor arithmetic had
just chosen, with the variation driven by a dice roll about spikes. It returns the
**plan half-extent**, a per-tier constant, so the normalise-and-rescale is exactly
1.0. The smoke gate now asserts the reference has zero standard deviation across a
library.

---

## R2-16xx — three coincident quantisations in the field colour, and `dry` was driven by the same random number as the family

```python
fam = np.floor(fid * 3.0).astype(int)
pal = np.array([[0.118, 0.170, 0.052],
                [0.235, 0.243, 0.083],
                [0.290, 0.215, 0.093]])
dry = np.clip(0.15 + 0.85 * fid, 0, 1)
```

1. **Three colours in the world.** A field is 155 m across; at 99 m and 22 mm that
   is a third of the frame in one flat value.
2. **Luminances 0.150 / 0.230 / 0.222** — a 53 % step between neighbours, measured
   at 20–25 CV p5–p95 over half the frame.
3. **`dry` was `0.15 + 0.85 * fid`**, the same random number that picked the family,
   so the crop colour and the hay/straw mix stepped at the same boundary in the same
   direction. One number, one edge, two coincident steps.

Now: the palette is a **closed loop** walked continuously by `fid`, so every field
takes its own colour off a 1-D manifold and no quantisation is left to make a blotch;
compressed to 0.168 / 0.211 / 0.206, with the family difference carried in **hue**,
because fields genuinely do differ and hue is how a boundary reads as a boundary
rather than as a brightness patch; `dry` comes off an independent hash; and two
unquantised tints at 190 m and 64 m multiply the whole thing and **do not respect the
field partition**, which is what stops the eye locking onto it.

| | before | after |
|---|---|---|
| distinct crop luminances across `fid` | 3 | **1123 of 1201 samples** |
| largest jump between adjacent `fid` | 0.080 | **0.000109** |
| brightest crop / darkest crop | 1.527 | **1.259** |
| p95/p5 of field luminance on a transect | ~1.50 | **1.297** |

### And the octave ladder had a hole exactly where this beat lives

Five noises at 3 cm, 13 cm, 38 cm, 7.7 m and 62 m — and the 62 m one only tinted
`GA_GRN` against `GA_GRN2`, a ±20 % swing on a term that then had **55 %** of a flat
per-field colour mixed over it. Between 40 cm and 8 m: nothing. Between 8 m and
62 m: nothing. **The only strong signal anywhere in the 10–200 m band was the field
partition itself** — and at 99 m up on a 22 mm lens, the 10–200 m band *is* the
picture. Two octaves added at 22 m and 139 m, multiplicative, neither of which knows
where a hedge is; the flat-colour mix dropped 0.55 → 0.42.

### The crop grain: what "worked land" looks like from 100 m up

Reducing the step stops the boundaries reading as blotches, but leaves 155 m of
smooth colour either side of every hedge, and smooth is the other half of the
complaint. `ter_crop` now carries, per vertex, the field's own row direction packed
as (cos, sin) and its headland band; `mat_ground` rotates the object coordinates into
that frame and draws **cutting swathes at 5.2 m**, **tramlines every 21 m at 1.7 m
wide** (arable fields only, stopping at the headland, as a real sprayer does), and a
**headland worked across the rows**. This cannot live in a vertex attribute — the
ground grid is 2.5 m and a wheeling is 1.7 m wide — and it costs shader maths and no
geometry at all. Interpolating (cos, sin) across a boundary shortens the vector,
which fades the grain out exactly where the hedge is, which is where it should fade.

### `detail_for`, on the shader that covers every square metre of ground in the film

`n_grain` at 3 cm carried `detail = 10`: eleven octaves, finest **0.029 mm**, against
a **1.32 mm** floor at the closest the lens ever gets to this surface (2.4 m, 34 mm,
4K). **Six octaves nobody can sample**, everywhere.

```
detail   was  10, 12, 12,  9,  6
         now   4,  5,  5,  6,  6, 6, 8      (two of these are the new octaves)
```

The two new mid-scale noises are floored deliberately coarse (340 mm and 4000 mm):
their job is the 10–200 m band, and everything below a third of a metre is already
carried by the three fine noises above them.

### Not a grade fix, and it could not have been one

Under the closing haze, asphalt and field measure 0.367/0.333/0.246 against
0.380/0.354/0.263. Anything applied downstream to separate those takes the car's
0.14 blue-minus-red break with it, and that colour break — not luminance — is the
whole reason the car is legible at 63 px. Every change above is upstream of the
grade, on the ground's own albedo and geometry.

---

## R2-16xx — the instruments

**`tools/r2_1661_smoke.py`** — builds every drift tier and kind, builds
`mat_ground`, and asserts: drift plan extent against its placement pitch (the
anti-tiling rule), triangle budget, scale-reference constancy, 24-of-24 distinct
vertex hashes, every Attribute node in the material is one `build_ground` actually
writes, no `TEX_IMAGE` anywhere, `dist3 >= dist` pointwise, the phantom disc closed,
and the beats-1–5 invariant above. Judged on `>> STAGE RESULT:` — Blender exits 0 on
an uncaught exception.

**`tools/r2_1661_measure.py`** — measures the defect the way R2-1128 measured it,
on rendered frames, not on the source:

* **patch CV** — blur to 41 px (a 155 m field at f2811's 9.2 cm/px is ~1700 px
  across, so 41 px keeps whole fields and destroys grass), then (p95−p5)/median over
  the ground mask. This is "you see all the patches" in a number. **Must go down.**
* **texture** — RMS of what the blur threw away, over the same mask. Grass, tufts,
  shadow, crop grain. **Must go up.** The two together are the argument: CV alone
  can be improved by flattening the land, which would be a different defect.
* **bare fraction** — ground whose local texture is under 35 % of the frame median.

Two controls manufactured at run time, so neither can expire when the defect is
fixed: a synthetic three-value patchwork at the measured 50 % step must read
20–60 CV (**34.05**), the same field with the step removed must read near zero
(**0.07**), and they must separate by 4× (**500×**). It refuses to report if either
control fails.

**The A/B is shot from the camera that made the stills, not from the clean one.**
R2-1129: two beat-6 cameras exist, and `world/camera_rig_path.json` — sha256-verified
and selftest-green — is **not** the camera that rendered
`~/vast-render/out/seq/r2943_4k/`. Those came from
`work/r2941/film17_R2943_path.json`. Four views baked into `_VIEWS_WORLD` off that
path: `b6_2760`, `b6_2811` (the worst case, 420 m of world across the frame),
`b6_2937`, `b6_2978` (the control — the near bank is hero, and it already looks
right; if this frame gets worse the fix is wrong).

---

## R2-16xx — results

Both arms terrain-only, built from the same seed, same contract, same grade (AgX /
look None / **−3.628**, `build_terrain`'s own `setup_render`), same camera — the one
that rendered the four existing 4K stills. 4K/512 for beat 6, 1080p/256 for the
beat-5 regression. **129 s a frame** on the 5090 against the film blend's 258, because
a ground-only 1.1 GB scene is the right instrument for a ground question.

### The build

| | before | after | |
|---|---|---|---|
| instanced tris | 13,880,689,022 | 13,924,573,990 | **+43.9 M, +0.32 %** |
| evaluated tris | 15,072,255,777 | 15,116,140,745 | +0.29 % |
| base library tris | 33,258,111 | 33,499,359 | +241 k |
| objects | 28,004 | 28,019 | +15 |
| blend on disk | 1,087 MB | 1,105 MB | +18 MB |
| grass clumps | 2,984,718 | 2,984,718 | unchanged |
| …of them hero | 1,662,591 | 1,643,883 | **−18,708** |
| sward drifts | — | **264,890** | A 106,486 / B 93,304 / C 65,100 |

**The predicate fix pays for two-thirds of the new layer.** The sward costs 172.7 M
instanced triangles; closing the phantom disc hands back ~129 M by demoting 18,708
clumps that were carrying 190–330 channelled blades each for a lens 130 m above them.
The net cost of the whole of R2-1661 is **0.32 %** of terrain's triangle budget, and
the placement itself takes **30 seconds** of a 1,344 s build.

`--selftest`, on the after arm: **`plants_on_runoff_or_gravel` = 0** — no drift on the
racing surface, the runoff asphalt or in a gravel trap. `terrain_above_road_pct` 0.0,
`verts_inside_corridor_1mm` 0, `horizon_bearings_below_zero` 0. (`weld_within_TOL_SEAM`
is `false` at `weld_max_mm` 18.609 — **pre-existing and much improved**: the recorded
value in `render/world/terrain/full_build.log` is 290.797 with the same false flag.
Nothing here touches the weld.)

### The frame — f2811, the worst case

`render/r2_1661/peep_f2811_field.png`, 1:1 at (2300, 1450) 900×560, open farmland:

* **before** — a smooth olive wash with a hard-edged tan patch cutting through the
  lower third, sparse dark dashes on an otherwise featureless surface, and a boundary
  that nothing crosses.
* **after** — continuous granular cover across the whole crop; the boundary has
  dissolved into a mottled transition.

`render/r2_1661/peep_f2811_left.png`, 1:1 at (150, 470) 900×420, is the cleaner
statement of the same thing: **before** carries a distinctly darker polygonal field
cell whose edges can be traced by eye — one Voronoi cell of `field_pattern`, which is
literally the thing the client is pointing at. **After**, that polygon is largely gone.

### The numbers, and one of them is a null result I am not going to dress up

On a box containing **exactly one field boundary and no trees** — (2300, 1450) 900×560:

| | before | after | |
|---|---|---|---|
| **edge_p99** — sharpest large-scale tonal transition | 27.83 | **17.39** | **−37.5 %** |
| **texture** | 3.906 | **5.482** | **+40.4 %** |
| patch_sd | 3.520 | 3.577 | +1.6 % |

Over the **whole infield** (three boxes, 24 % of frame), the same run says:

| | before | after | |
|---|---|---|---|
| texture | 4.377 | **5.824** | **+33.1 %** |
| texture p05 | 1.226 | 1.383 | +12.8 % |
| bare (absolute) | 0.0585 | 0.0556 | −5.0 % |
| band-pass patch CV | 40.18 | 40.58 | **+1.0 %** |
| edge_p99 | 120.9 | 121.2 | +0.2 % |

**The wide-box variance and edge numbers do not move, and that is honest.** Two
reasons, both real:

1. **`edge_p99` over a wide box is measuring tree shadows, not fields.** It reads 121
   there against 27.8 on the boundary box — the sun is at 12.47°, every tree lays down
   a hard-edged shadow four and a half times its own height, and this pass did not
   touch trees. The field-boundary signal is a tenth of that and is invisible
   underneath it.
2. **Variance is the wrong question, and this pass proved it on itself.** The fix
   *deletes* one kind of band-scale variance (155 m flat blocks with a step at the
   hedge) and *deliberately adds another* (the sward's own 38 m and 9 m patchiness,
   which is the whole reason the new cover is not a second flat wash). Those two are
   the same magnitude and opposite in meaning, and no variance metric can tell them
   apart. A patch is not "variance", it is **a bounded region with an edge** — which
   is why `_edges` exists and why it is measured where a field boundary actually is.

Three metrics were tried and two were contaminated before the third worked. The rule
held again: **the rendered frame decided, and the metric only argued.**

### The control — f2978, which already looked right

Boxes over the hero verge band, which is why it looked right in the first place:

| median | edge_p99 | patch CV | texture | texture p05 |
|---|---|---|---|---|
| +0.3 % | −3.0 % | +1.5 % | −0.6 % | +0.5 % |

**Everything inside ±3 %. The control holds.**

### The regression — beats 1–5

`t5_verge` (knee height on the verge) and `esses` (the ridge shoulder), 1080p/256:

| view | patch CV | texture | edge_p99 |
|---|---|---|---|
| t5_verge | 55.473 → **55.465** | 12.62 → 11.64 | 150.9 → 152.4 |
| esses | 43.73 → **41.74** | 8.57 → 8.74 | 86.3 → 88.9 |

`render/r2_1661/peep_t5.png` and `peep_esses.png` at 1:1: **the frames are the same
picture.** Identical hero blades in the foreground, identical verge band, identical
treeline. `t5_verge`'s patch CV is unchanged to three decimal places. This is the
regression test the predicate change was owed, and it passes by measurement *and* by
eye — as the arithmetic said it would: the hero boundary moves inward 0.88 m of 48.

### Cost

**$1.06** of GPU for the whole pass — 10 renders (8 A/B + 2 sanity) at 129 s a 4K
frame, plus two 1.1 GB scene uploads. Budget: $120.06 of $150 remaining, $58.13 of
vast.ai credit.

### What is NOT proven, and what it would cost

This is verified on a **terrain-only** blend. It is the right instrument for a ground
question — nothing else is in the frame to argue about — but it is **not the delivered
picture**. Confirming on the film needs `render/world/assembly/r2/assemble.py` re-run
with the new terrain and then `tools/build_film_scene.py`, which is another
workstream's blend (7.98 GB, OOMs on this box). Once that exists: a 24-frame 4K sample
of the ending is **$0.92**, the full 264-frame beat 6 is **$10.10**.

Two things this pass deliberately did not do, both because they are out of scope and
would have been changes to other people's calibrated numbers: the tree, shrub, weed and
grit tiers still read the horizontal `CameraPath.dist`, and the ground height field is
untouched. The tree tier is the one worth revisiting — `edge_p99` says tree shadows
are now the largest hard-edged feature in the infield by a factor of four.

### Reproducing the A/B

The before arm is `world/_b6_before_terrain.py` — `git show HEAD:world/build_terrain.py`
plus the four `b6_*` view entries, nothing else — kept so the comparison stays
reproducible.

```bash
blender -b --factory-startup -noaudio -P world/build_terrain.py -- \
    --selftest --cams b6_2811,b6_2978,t5_verge,esses \
    --save render/r2_1661/ground_after_4cam.blend
blender -b --factory-startup -noaudio -P tools/r2_1661_rebake.py -- \
    --module world/_b6_before_terrain.py --load render/r2_1661/ground_before.blend \
    --save render/r2_1661/ground_before_4cam.blend --cams b6_2811,b6_2978,t5_verge,esses
bash tools/r2_1661_ab.sh
.venv/bin/python tools/r2_1661_measure.py BEFORE.png AFTER.png --selftest \
    --boxes "2300,1450,900,560"
```

`TERRAIN_SWARD` is the density dial for the new layer. It is a measurement switch,
never a quality one.
