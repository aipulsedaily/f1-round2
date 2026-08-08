# STAGING R2-2941 .. R2-3000

Opened 2026-08-08. Task #52 (the item campaign, waves 2+) and task #90 (three
unlogged geometry defects at the pit exit and the glass mouth).

**`docs/DEFECT-LOG-R2.md` is NOT edited by anything in this file.** Proposed
entries are written here as proposed text; the log's owner merges them.

Other agents append their own blocks to the end of this file. Nothing above a
block belongs to its author.

---

## R2-2941..R2-2949 — the trees were never within 74 metres, and the ranking that put them first was measuring their host

### The claim under test

`docs/WAVE2-RANKING.md` §3 ranks eleven trees as ranks 1–11, carrying **50.2 %
of all item screen presence in the film**, every one of them at a peak of
**2160 px**, and every one of them reporting the **identical** `min_depth_m` of
**4.577 m**.

Eleven independent measurements do not agree to four decimal places. That
number is one shared host's best moment, inherited by eleven items which — by
the ranking's own §2 weakness 1 — have no geometry of their own in the
host-resolution table: *"0 of 435 items resolve to a host list containing their
own geometry."* §5b flags it as a hypothesis and says settling it "gates the top
50 % of the ranking". §7 step 4 says do it **before building any tree**.

### The instrument

`tools/r2941_veg_framing.py`. It measures the one class of thing in this world
whose own authored positions are on disk rather than inherited:
`work/w2_0/retier_a10/world_points.npz` carries `veg_origin` (27,969 × 3),
`veg_bbox` (27,969 × 6) and `veg_name`, dumped from the assembled world. **No
host table is consulted and none is needed.**

The camera is resolved through `tools/live_campath.py`, never named. It comes
back `render/film19_path.json`. **The ranking was measured against
`film17_path.json`, which `docs/LIVE-CAMERA.md` superseded on 2026-08-07 under
R2-1701** — so the ranking is also a measurement of a camera the film no longer
has. Projection maths is imported from `tools/screen_presence.py`
(`camera_track`, `RES_X`, `RES_Y`); this file defines no sensor constant of its
own. `R1_SHELL` is lifted out of `world/build_architecture.py`'s own AST rather
than retyped, because that module imports `bpy` at module scope and cannot be
imported from bare python.

### The controls, and the failures watched

`--selftest` is **12/12**, and six of the twelve are negative arms. That is not
the evidence. `tools/r2941_veg_framing_control.py` damages the instrument three
ways and **watches the arms fire**:

```
baseline (undamaged): rc=0 failed=none
ok   damage A_no_frustum_rejection       rc=1 fired=[negative_behind_camera,
                                                     negative_outside_frustum,
                                                     overfill_clamped_to_frame]
ok   damage B_radial_not_pinhole_depth   rc=1 fired=[closed_form_depth,
                                                     closed_form_height, ...]
ok   damage C_no_clamp_to_frame          rc=1 fired=[overfill_clamped_to_frame]
>> STAGE RESULT: CONTROL_PASS (3/3 damage modes rejected)
```

Damage B is the manifest's own error — radial distance where pinhole depth
belongs. Arm `overfill_arm_is_not_vacuous` exists because an overfill clamp test
on a small box passes for the wrong reason; it asserts the unclamped value
really would be 186,667 px.

### Three readings, and two of them were thrown away for cause

**Reading 1 — world AABB, all frames.** Every one of 22 vegetation classes
returns **2160 px**, i.e. everything overfills. Rejected as uninformative: a
median oak instance's world AABB is **29.7 × 29.6 × 23.2 m**, so its nearest
corner is ~15 m closer than its trunk. The AABB model is a bound so loose it
reproduces the ranking's own non-answer.

**Reading 2 — trunk segment, all frames.** `avenue` peaks at **2600 px at
36.94 m, frame 147**. **Falsified by the frame.**
`work/r22161_proxy/r22161_proxy_000147.png` is a wheel macro **inside the
showroom** with no vegetation anywhere in it. The tool's stated no-occlusion
caveat fired exactly where it said it would. 929 of 2,978 frames have the camera
inside the round-1 pavilion plan (contiguous, f1–f929); vegetation is all
outdoors and the shell is between them.

**Reading 3 — trunk segment, camera outside the pavilion. This is the result.**
`work/r2941/veg_framing_outdoor.json`, 2,049 frames.

| species | inst | peak px | depth at peak | **nearest ever** | h (m) |
|---|---:|---:|---:|---:|---:|
| `tree_poplar` | 1895 | 1219.9 | 281.0 m | **97.9 m** | 25.5 |
| `hedge_oak` | 498 | 904.3 | 143.8 m | **111.3 m** | 17.5 |
| `tree_plane` | 500 | 867.1 | 284.9 m | **115.4 m** | 20.3 |
| `tree_willow` | 2977 | 837.1 | 244.3 m | **117.1 m** | 17.0 |
| `tree_pine` | 2694 | 831.9 | 291.4 m | **84.2 m** | 24.1 |
| `tree_oak` | 4609 | 829.2 | 104.8 m | **104.8 m** | 23.2 |
| `tree_birch` | 5317 | 671.6 | 107.6 m | **74.7 m** | 15.8 |
| `avenue` | 22 | 663.1 | 106.2 m | **106.2 m** | 16.9 |
| `tree_hawthorn` | 3164 | 409.8 | 273.2 m | 107.7 m | 8.2 |
| `tree_cypress` | 74 | 347.6 | 171.3 m | 151.8 m | 12.9 |

**No tree in this film is ever closer to the camera than 74.69 m.** The
ranking's 4.577 m is wrong by **16× to 39×**, in the same direction and for the
same reason `lighting_mast` was wrong by 11× (R2-1362). The peak-px column is
wrong by **1.8× to 6.2×** — and since the ranking statistic goes as px², **by up
to 39× in score.**

Frames 2365, 2516 and 1750 of the free proxy set were checked and agree: the
treeline is a hazed, low-contrast, motion-blurred band across the top of frame.

### What this dissolves

`docs/WAVE2-RANKING.md` §5a computed the needle crossover at **12.69 m** — below
that a Scots pine needle is over half a pixel, above it the honest construction
scales the blade and divides shoot count. §5b then reported that **two
independent tree builds hit the same wall**: a correct spray needs ~800 k
tris/tree, 44 L0 sources is ~35 M triangles, that will not fit 11 GB, and
dropping below 37 sources breaks the variety floor. Its conclusion: *"as
specified, the tree tier is unbuildable on this machine, and it is 11 of the top
11 ranks."*

**The nearest tree in the film is 74.69 m — 5.9× beyond the needle crossover.
The L0 tier is never on screen at all.** §5b's own words: *"If trees are seen at
tens of metres rather than 4.577 m, the crisis largely dissolves."* It is, and
it does. **The tree tier's triangle crisis was an artifact of a shared host.**

---

## R2-2945 — the ranking optimised the wrong quantity, and it ranked the least-resolvable class first

The re-derivation above corrects the trees' distance. It does not go far enough,
because **distance is not the quantity that decides whether detail survives.**

`work/w2_0/retier_a10/sp_objects.json` already carries, per object, with
occlusion and with the flat 180° shutter, a field the campaign has never ranked
on: **`peak_unocc_sharp_px_per_m`** — the resolution at which the object is seen
*while it is sharp*. For `SURF_Track` that is **165 px/m against a peak of
1432 px/m**: motion blur removes **8.7×** of the resolution the geometry is built
to.

Ranked on it, wave 2 inverts:

| class | **sharp px/m** | **1 px =** | nearest | sharp frames |
|---|---:|---:|---:|---:|
| `ARCH_Paving_Forecourt` | **1049.4** | 0.95 mm | 3.79 m | 410 |
| spectator library figures | 791–844 | 1.2 mm | 1.57 m | ~533 |
| **`VEG_grass_*`, `VEG_grit_*`** | **425.8** | **2.35 mm** | **4.58 m** | **845–1011** |
| `VEG_weed_thistle` | 347.9 | 2.87 mm | 6.01 m | 813 |
| `VEG_weed_nettle` / `ragwort` / `dock` | 230–260 | 3.8–4.3 mm | 5.0–7.2 m | 765–819 |
| `TER_Ground` | 121.2 | 8.3 mm | 23.68 m | 751 |
| `VEG_avenue` — the best tree in the film | 80.9 | 12.4 mm | 35.13 m | 187 |
| **`VEG_tree_oak0` — rank 1 in the old ranking** | **22.7** | **44 mm** | **104.4 m** | 371 |

**Trees resolve at 22.7 px/m. Grass and grit resolve at 425.8 px/m — 18.8×
finer — with up to 1,011 sharp frames against the oak's 371.**

At 22.7 px/m a bark fissure (10–30 mm) is **0.23–0.68 px**; an oak leaf (80 mm)
is **1.8 px**; a Scots pine needle (1.7 mm) is **0.039 px — 26× below the
one-pixel line.** The campaign was about to commit ~35 M triangles at the head
of its build order to a class that cannot resolve a leaf.

**Why the ranking missed it:** its statistic is area × duration
(`300²·f300 + 150²·(f150−f300) + 60²·(f60−f150)`). Trees win that by being huge
and far away. It never asks at what resolution the thing is seen, so **it ranks
the least-resolvable class first.** This is the pixel-footprint law — the one
this project has already violated at least six times, at 0.87 px and 2.17 px —
applied in the direction nobody applied it: not to a feature within an item, but
to the choice of which item to build.

**And the frame says the same thing.** `work/r22161_proxy/r22161_proxy_002316.png`
is the peak sharp frame for grass and grit: the foreground sward fills the bottom
~35 % of frame at full sharpness with thistles in flower, and the treeline is a
hazed band of thin stems along the top. **The user's most-quoted rejection of
this project — "half assed… the grass is blurry" — lands exactly on the top
buildable class, which has no module.**

### Consequence for the build order

- **Do not build hero tree modules.** `tree_oak.py`, `tree_scots_pine.py` and
  `tree_italian_cypress.py` (ungated, and the cypress KNOWN BAD, R2-1341) should
  not be gated into the world on the strength of the old ranking. At 22.7 px/m
  the tree tier is a **silhouette, species-mix and treeline-variety** problem,
  which costs no triangles. The manifest already names the defect, in
  `tree_oak.notes`: birch is 20 % of the base mix plus 7.5 % dead timber, so *"a
  quarter of every treeline is a pale stem and it reads as 'a birch wood'"* —
  visible in proxy frames 2316 and 2516, and fixable at zero triangle cost.
- **Build the ground-cover tier**, at 2.35 mm/px. Dispatched (see the
  R2-2970..R2-2989 block below, when its author appends it).

### What is NOT settled, stated rather than buried

1. `sp_objects.json` was measured against **`film17_path.json`**, superseded by
   film19. The divergence is documented as confined to beat 1, but that has not
   been re-verified for this field. The vegetation re-derivation above IS on
   film19.
2. `r2941_veg_framing.py` does **not** test occlusion. It is an upper bound, and
   the pavilion exclusion is a coarse proxy that was adopted only after the frame
   falsified reading 2. A tree occluded by a grandstand still counts.
3. The world is `assembly10`, not the shipping `assembly14`. Vegetation
   placement is seeded and camera-independent, so this does not move *where* the
   trees are, but it has not been re-taken on the ship.

---

## R2-2946 — the variety red line has no current measurement, and its two records disagree

The floor this campaign must not breach is **311 distinct sources, commonest
share ≤ 2.0 %**. Both halves of that are quoted from records that disagree, and
neither was taken against the shipping world:

| record | sources | instances | top source | top share | dated |
|---|---:|---:|---|---:|---|
| `docs/instance_variety.json` | **310** | 4,688,475 | `VEG_grass_fescue_H03_u` | **0.0199** | mtime 2026-07-29 05:01, **untracked in git** |
| `docs/WAVE2-SCOPE.md:430` | **311** | 4,689,798 | — | — | — |

**They differ by one source and 1,323 instances, and the JSON predates
`assembly14` by ten days.** So the project's hard red line — the one guarding
the user's named failure, "one tree spammed 100 times" — is being policed
against a number from a superseded world, by a file no commit owns. That is the
same shape as R2-1007 (43 tools reading a stale camera) and as
`docs/screen_presence.json` still holding the 08-04 measurement.

**The margin is also effectively zero, and it is in the class wave 2 is about to
touch:** the commonest source in the entire world is a **grass** source at
**1.99 % against a 2.00 % limit — 0.0001 of headroom.** Any change that adds
instances to an existing grass source, or that removes a source, breaches the
red line by itself. The safe direction for any ground-cover work is therefore
**more distinct sources, not more instances per source** — which is also what
the user's named failure is actually about.

**Recommended, not done here:** re-run `tools/instance_variety.py` against the
world `tools/shipping_world.py` resolves, and let that supersede both records.
It needs a ~10 GB Blender load and three agents were live on an 11 GB box; it is
handed to the ground-cover author with the measurement to take before and after.

---

## Files

| path | what |
|---|---|
| `tools/r2941_veg_framing.py` | the re-derivation; `--selftest` 12/12, six negative arms |
| `tools/r2941_veg_framing_control.py` | damages the tool three ways and watches the arms fire |
| `work/r2941/veg_framing.json` | reading 1, world AABB, all frames — **superseded, uninformative** |
| `work/r2941/veg_framing_segment.json` | reading 2, trunk segment, all frames — **falsified by proxy frame 147** |
| `work/r2941/veg_framing_outdoor.json` | reading 3, trunk segment, camera outside the pavilion — **the result** |

Reproduce:

```bash
python3 tools/r2941_veg_framing.py --selftest
python3 tools/r2941_veg_framing_control.py
python3 tools/r2941_veg_framing.py --model segment --exclude-pavilion \
        --out work/r2941/veg_framing_outdoor.json
```

---

## R2-2947 — the film17 → film19 camera drift is NOT confined to beat 1, and 23 % of the world's screen-presence measurements sit inside it

R2-2945 above listed as unsettled that `work/w2_0/retier_a10/sp_objects.json`
was measured against `film17_path.json`, superseded by film19 on 2026-08-07
(R2-1701), and that the divergence was *"documented as confined to beat 1"*.
**It is not, and closing that caveat produced a worse finding than the caveat.**

`render/film17_path.json` vs `render/film19_path.json`, all 2,978 frames:

| quantity | worst | where |
|---|---:|---|
| frames differing at all | **846 of 2,978 (28.4 %)** | spans from f2 to f2978 |
| position | **21.399 m** | f2177 |
| focal length | **55.996 mm** | f2978 |
| orientation | **78.753 deg** | f2857 |

The divergent spans are not one block. The three largest are **f2716–f2978 (263
frames — the entire ending), f2134–f2253 (120 frames), and f465–f753**.

`docs/LIVE-CAMERA.md` records of the *earlier* film16→film17 drift: *"From f781
onward the two files are bit-identical… so nothing outside beat 1 can be
affected by this class of drift."* That sentence is true of the pair it
describes. **It is false of the pair that is live now**, and the class of drift
has plainly been generalised from it — the caveat in `WAVE2-RANKING.md` §2 and
the one I wrote in R2-2945 both inherited the belief without testing it.

**Consequence: 521 of 2,261 objects (23.0 %) have their peak sharp frame inside
a divergent frame.** Every quantity derived from `sp_objects.json` — including
`work/w2_0/wave2_ranking.json`, all 435 rows, and the tier counts HERO 72 / MID
58 / BULK 305 — is therefore measured on a camera the film does not have, for
close to a quarter of the world.

### What this does NOT touch, checked rather than assumed

Every object R2-2945's build decision rests on has its peak sharp frame in a
**non-divergent** frame, verified individually:

| object | sharp frame | pos Δ | lens Δ | angle Δ |
|---|---:|---:|---:|---:|
| `VEG_grass_fescue_H` | 2316 | 0.000 m | 0.000 mm | 0.00° |
| `VEG_grit_chip` | 2316 | 0.000 m | 0.000 mm | 0.00° |
| `VEG_weed_thistle` | 2318 | 0.000 m | 0.000 mm | 0.00° |
| `VEG_tree_oak0` | 1727 | 0.000 m | 0.000 mm | 0.09° |
| `VEG_avenue` | 821 | 0.000 m | 0.000 mm | 0.00° |
| `ARCH_Paving_Forecourt` | 282 | 0.000 m | 0.000 mm | 0.17° |
| `TER_Ground` | 122 | 0.000 m | 0.000 mm | 0.00° |
| `SURF_Track` | 2620 | 0.000 m | 0.000 mm | 0.00° |

**So the sharp-resolution inversion in R2-2945 stands on frames where the two
cameras are bit-identical**, and the ground-cover build order does not depend on
the re-measurement below. The caveat is closed for the decision it was attached
to, and left open for the ranking as a whole.

### Proposed defect-log entry (NOT written to `DEFECT-LOG-R2.md` — for the owner to merge)

> **R2-XXXX — "confined to beat 1" was inherited from a different pair of
> cameras, and the live pair diverges over the whole film.** `film17` → `film19`
> differ in 846 of 2,978 frames, worst 21.399 m of position (f2177), 55.996 mm
> of focal length (f2978) and 78.753° of orientation (f2857), with the largest
> single divergent span being the last 263 frames. 23.0 % of world objects
> (521/2,261) have their peak sharp frame inside that divergence, so
> `sp_objects.json`, `docs/screen_presence.json` and `work/w2_0/wave2_ranking.json`
> are stale for close to a quarter of the world. **Not fixed** — the re-measure
> needs a ~10 GB Blender load. Named here so the next reader does not quote the
> ranking as current. The specific rows R2-2945 relies on were individually
> checked and are on bit-identical frames.

Reproduce: `render/film17_path.json` and `render/film19_path.json` are both in
the tree; the comparison is a dozen lines of numpy over `p`, `q` and `lens`.

---

## R2-2948 — the size of the inversion, and one precision note on the instrument

**How much of the planned wave 2 the sharp-resolution ranking removes.**
`work/w2_0/wave2_ranking.json`, ranked by its own score:

| | terrain-owned vegetation |
|---|---:|
| of the top **20** modules | **17** |
| of the top **44** — the "80 % of the picture" line | **21** |

So the inversion in R2-2945 is not a re-ordering of one item. **Nearly half the
44 modules the campaign proposed to build for 80 % of the picture belong to the
class that resolves at 22.7–80.9 px/m**, and 17 of the first 20 do.

For scale on the campaign's other headline: the manifest flags **343 of 435
items as heroes**; the tiering against the live camera and shipping world says
**HERO 72, MID 58, BULK 305**. The task brief's "343 → 91" is the older form of
the same collapse; the current number is 72, and **every time this has been
measured rather than modelled it has got smaller.** The sharp-resolution
measurement is the same effect applied one level deeper.

**Precision note, stated rather than buried.** `sp_objects.json` reports
`peak_unocc_sharp_px_per_m` (occlusion-aware) but `sharp_frame` is taken from
`sharp_ppm`, the occlusion-*unaware* series
(`tools/screen_presence.py:416-420`). For the objects tabulated in R2-2945 the
two coincide, but the frame numbers quoted — and used in R2-2947's divergence
check — are strictly the peak *sharp* frame, not the peak *unoccluded-sharp*
frame. Also, "sharp" means **smear ≤ 6 px** (`SMEAR_SHARP_PX`, the gate's own
hero resolve threshold), not zero smear. Both of these make the reported
resolution an **upper bound**, which is the safe direction for the conclusion
drawn from it: trees are, if anything, worse than 22.7 px/m.


---

## R2-2950..R2-2959 — the variety guard's weak path, closed (R2-1381)

**`per_instance_variation` exists for one sentence of the user's — "i dont want
repeat stuff aka one tree spammed 100 times" — and until this commit an item
that emitted PLAIN OBJECTS could satisfy it with two meshes.**
`docs/WAVE2-RANKING.md` §5 named the hole and left it open, directly under a
ranking whose top eleven items are all trees at up to 4,500 instances. It is
closed here, in the order this project insists on: **the false accept was built
and watched to PASS the guard as shipped before a line of the fix was written.**

Files: `tools/item_gate.py` (the fix), `tools/r2_1381_variety_control.py` (the
four controls and the residual probe, in Blender, no render),
`tools/r2_1381_rescore.py` (the re-score of the shipped verdicts, pure python).
Evidence logs: `tmp/r2_1381_prefix.log`, `tmp/r2_1381_postfix.log`,
`tmp/r2_1381_rescore.log`. No `gate.json` was edited and no GPU was used.

### R2-2950 — the false accept, watched passing the guard as shipped

The control harness loads the gate under test from a git revision
(`--gate git:cea0e57`), so "the guard as shipped" is not a story about a file
that no longer exists — the run is repeatable today and in a year. Built:

> **4,500 plain objects, drawn round-robin from TWO source meshes, each with a
> random uniform scale U(0.85, 1.15) in the object matrix.** Two trees, 4,500
> times, at slightly different sizes. Nothing else.

```
>> gate under test: git cea0e57 (186066 bytes)
>> variation_verdict present: False
>>   declared 4500, objects measured 4500, gn_instanced=False
>>   cv_size 0.11691  distinct_topologies 2
>>   OLD rule -> True
>> STAGE RESULT: R2-1381 PRE-FIX RUN ... C1 (false accept passes the shipped rule) = True
```

`cv_size 0.11691 >= 0.03` and `distinct_topologies 2 >= 2`. **The guard whose
entire purpose is that failure returned `per_instance_variation: true` on it.**
The margin was not narrow: the size CV cleared its floor by 3.9×, and the
topology floor is clearable by ANY two meshes at ANY population.

### R2-2951 — the rule that replaced it

The plain-object path is now held to the realized-instance path's own law, on
the same numbers, using the same fingerprint:

| | as shipped | now |
|---|---|---|
| shape identity | `len(set(triangle_count))` | `_shape_signature` — the SAME function the realized path uses |
| count required | **2**, at any population | `need_distinct_shapes(n) = min(n, max(8, min(40, √n)))` |
| commonest shape | *not measured* | `<= top_share_limit(n) = max(0.25, 1/n)` |
| size CV | `>= 0.03` | `>= 0.03` (kept) |
| topologies | `>= 2` | `>= 2` (kept) |

Three things about this that are deliberate:

1. **No second shape hasher.** `_shape_signature` was already there for
   geometry-nodes sources; `instance_variation` now runs it over each object's
   evaluated mesh, which costs nothing because that mesh is already in hand for
   the bounding box. `need_distinct_shapes` and `top_share_limit` are now the
   ONE definition both paths call — the realized path stopped carrying its own
   copy of `max(8, min(40, sqrt(n)))` and its own literal `0.25`.
2. **The signature is taken in LOCAL space**, exactly as it is for a
   geometry-nodes source. A per-object scale in the matrix is a transform, not
   a shape. If world scale counted, the false accept above would produce 4,500
   "shapes" and pass again.
3. **`min(n, ...)` and `max(0.25, 1/n)` are not relaxations.** A population of
   seven objects asked for eight distinct shapes is being asked for something
   no population of seven can contain, and a population of three asked for a
   25 % ceiling likewise. Those are arithmetically impossible requirements, not
   strict ones, and they would fail `pont_girder` (7 objects, 7 different
   bodies, ACCEPTED) for being small. Checked, not assumed: every
   realized-instance population on disk is 10 or larger, where both are exact
   no-ops — `tools/r2_1381_rescore.py` puts all seven shipped `real` blocks back
   through the shared functions and reports **0 strong-path verdicts moved**.

The decision also moved out of `main()` into `variation_verdict()`, so the rule
can be exercised without a 40-minute gate run. That is why the controls below
exist at all.

### R2-2952 — the same false accept, refused

Identical geometry, identical seed, new guard:

```
>>   cv_size 0.11691  distinct_topologies 2
>>   distinct_shapes 2  top_shape_share 0.5  (required 40, limit 0.25)
>>   distinct_source_meshes 2  distinct_shapes_scale_invariant 2
>>   OLD rule -> True      NEW rule -> False
```

**2 shapes against 40 required, and the commonest shape is 50 % of the
population against a 25 % ceiling.** It fails on both halves, not on a
tie-break.

### R2-2953 — the positive controls: this is not a guard that rejects everything

The mirror failure costs a rebuild of every item in the film, so it is watched
too, in both size regimes:

| control | item | measured | verdict |
|---|---|---|---:|
| **C3** | 4,500 objects from **40 genuinely different bodies** | cv 0.23438, 40 topologies, **40 shapes**, commonest **2.51 %** (need 40, limit 25 %) | **PASS** |
| **C4** | **7 objects, 7 different bodies** (the `pont_girder` shape), declared 4 | cv 0.18526, 7 topologies, **7 shapes**, commonest **14.29 %** (need 7, limit 25 %) | **PASS** |

C3 is exactly what the strong path demands at 4,500 instances — forty sources —
and it passes with the count met exactly and the share 10× inside the limit. So
the honest build of the tree tier that the ranking calls for is buildable
through this guard; the two-variant version is not.

```
>> STAGE RESULT: R2-1381 CONTROLS ALL PASS (C1_false_accept_passes_OLD=True,
   C2_false_accept_fails_NEW=True, C3_varied_passes_NEW=True,
   C4_small_varied_passes_NEW=True)
```

### R2-2954 — the residual, measured rather than asserted

One route through the new rule remains, and it is named with a number rather
than a caveat. **D1 (a probe, not a control): 450 objects, TWO bodies, with the
per-copy scale baked into the VERTEX DATA instead of the object matrix.**

```
>>   distinct_shapes 298  top_shape_share 0.0111  (required 21, limit 0.25)
>>   distinct_source_meshes 450  distinct_shapes_scale_invariant 3
>>   NEW rule -> True
```

Those really are 298 different meshes, so the rule passes it by the letter, and
it is two trees at 450 sizes by the eye. `_shape_signature` quantises the
bounding box in centimetres, so a scaled copy is a new shape to it.
`instance_variation` now also reports `distinct_shapes_scale_invariant` — the
same signatures with each one's longest side divided out — and **298 shapes
collapse to 3 families**. The gate prints a `** RECORDED, NOT FAILED **` line
whenever that count falls below half the shape count.

It is recorded rather than gated on purpose: it cannot distinguish this failure
from a legitimate library whose bodies share a topology and an aspect ratio
(jittered copies of one generator differ by millimetres, under the
quantisation), so gating on it would manufacture the mirror failure R2-2953
exists to prevent. **A reviewer reading `distinct_shapes 4500,
distinct_shapes_scale_invariant 2` in a tree item's report now has the number
that says "look again".**

### R2-2955 — re-scoring the 33 shipped verdicts, without re-rendering

`tools/r2_1381_rescore.py` reads every `render/items/*/gate.json` and re-decides
`per_instance_variation` from what those reports already contain. It writes
nothing. **Nineteen items took the plain-object path with more than one declared
instance** — the count `WAVE2-RANKING.md` §5 gives, confirmed.

What the record can and cannot settle:

* `distinct_shapes >= distinct_topologies` whenever a differing triangle count
  brings a differing vertex or polygon count with it, which is the ordinary
  case. So a recorded `distinct_topologies` that already clears the new
  requirement settles the COUNT half.
* **The commonest-shape share was never recorded on this path** — the old rule
  had no use for it — and it cannot be bounded from a distinct count. 90
  topologies over 3,236 objects is equally consistent with an even spread and
  with 2,500 objects sharing one. So the SHARE half is **unproven**, and
  unproven is not a pass (R2-019).

```
>> STAGE RESULT: R2-1381 RESCORE 19 weak-path items, 0 FAIL, 13 UNPROVEN,
   6 PASS; 5 ACCEPTED verdicts affected
>> strong-path verdicts moved by the shared thresholds: 0
```

**No shipped item is shown to be a false accept.** Five ACCEPTED items lose
their proof and need a re-gate — which is a CPU gate run, not a render:

| item | declared | objects | topologies | shapes needed | status now |
|---|---:|---:|---:|---:|---|
| `armco_post` | 3,641 | 3,236 | 90 | 40 | UNPROVEN — count clears, share never measured |
| `catch_fence_post` | 690 | 676 | 142 | 26 | UNPROVEN — count clears, share never measured |
| `crew_figure` | 120 | 120 | 60 | 10 | UNPROVEN — count clears, share never measured |
| `heras_fence_panel` | 900 | 771 | 258 | 27 | UNPROVEN — count clears, share never measured |
| `pit_wall_unit` | 125 | 119 | 22 | 10 | UNPROVEN — count clears, share never measured |

Two ACCEPTED weak-path items survive with a proof rather than a presumption,
because every one of their objects has its own triangle count, which fixes the
share at 1/n: **`pont_girder`** (7 objects, 7 topologies, need 7, share 0.143)
and **`timing_stand`** (10 objects, 10 topologies, need 8, share 0.100).
`pont_girder` is the case that made `min(n, ...)` necessary: without it the item
would have flipped to a rejection for having only seven objects.

The other eight weak-path items in the same UNPROVEN state are already
ITEM_REJECTED for other reasons (`armco_w_beam`, `grandstand_riser_unit`,
`gravel_bed_surface`, `kerb_precast_unit`, `marshal_post_column`,
`paddock_personnel_figure`, `showroom_facade_panel`, `tyre_blanket`), and four
more are provably fine (`crew_fireproof_overall`, `hospitality_deck`,
`marshal_post_deck`, `team_truck_trailer`).

### R2-2956 — a second, narrower exemption, found and NOT taken

`variation_verdict` still returns `True` unconditionally when
`instances_declared <= 1`, **however many objects the item actually emits**. On
disk that exempts seven items whose declaration disagrees with their own object
count, including one by a factor of 459:

| item | declared | objects found | result |
|---|---:|---:|---|
| `access_road_slab` | 1 | **459** | ITEM_REJECTED |
| `pont_deck_slab` | 1 | 13 | ITEM_REJECTED |
| `driver_figure` | 1 | 10 | ITEM_REJECTED |
| `terrain_ground` | 1 | 10 | **ITEM_ACCEPTED** |
| `dais_delivery_ramp` | 1 | 6 | ITEM_REJECTED |
| `asphalt_wearing_course` | 1 | 5 | ITEM_REJECTED |
| `gantry_truss` | 1 | 3 | **ITEM_ACCEPTED** |

A population is being exempted by a MANIFEST DECLARATION rather than by a
measurement, which is the same species of defect as the one above. It is left
alone deliberately: 459 slabs of road surface are not "459 copies of a tree",
the correct threshold depends on what a declaration of 1 is supposed to mean
for a surface built in tiles, and closing it blind would flip items whose
manifests are merely mislabelled. **Named here so it is not rediscovered as a
surprise.**

Also found, unrelated to R2-1381: **`render/items/spectator_crowd/gate.json`
carries `"item": "spectator_seated"`.** Any tool keying on that field merges the
two crowd items into one row — which is the likeliest reason this campaign keeps
saying "32 item gate reports" when there are **33** on disk (and four item
directories — `human_bench`, `tyre_deposit`, `_relief`, `_winding` — with no
`gate.json` at all).

### R2-2957 — the fix is machine-detectable, because prose in a staging document is not

`tools/mark_gate_version_stale.py` is this project's existing answer to "a pass
awarded by a weaker instrument", and it finds stale reports by COUNTING checks.
**It cannot see a check that was strengthened rather than added**: all 33 reports
on disk say `8 checks`, and nineteen of them hold a `per_instance_variation`
decided on two triangle counts. So the gate now writes its variation law into
the report's own `thresholds` block:

```json
"variation_shape_law": "R2-1381: distinct SHAPES via _shape_signature on BOTH
   the realized-instance and the plain-object path; min(n, max(8, min(40,
   sqrt(n)))) required, commonest <= max(0.25, 1/n)",
"variation_cv_size_floor": 0.03
```

**A report without that key was written by the pre-R2-1381 gate, whatever its
check count says.** The five items in R2-2955 are then findable by a tool rather
than by remembering this document. (The provenance stamp already records
`item_gate.py`'s sha256, which is the same fact expressed in a form nobody can
read; both are now present.)

### R2-2958 — the same hole is still open ONE LEVEL UP, in the film-wide instrument

`tools/r2_1881_variety_control.py` — which predates this work — manufactures six
populations whose true answer is known and requires `tools/instance_variety.py`
to say so. Its sixth arm, `plainspam`, is **2,000 plain-object copies of one
mesh**, and its docstring says what happens: `instance_variety.py` iterates
`depsgraph.object_instances` and `continue`s on `not inst.is_instance`
(`tools/instance_variety.py:68`), so a module emitting plain objects contributes
**zero** to every number it reports. That tool produced `docs/instance_variety.json`
— 4,688,475 instances, 310 sources, top share 1.99 % — **the film-wide answer to
the user's red line.**

R2-1381 closes the per-item gate. It does not touch that. **A tier built out of
plain objects is still invisible to the film-wide variety number, where it reads
as `INSTANCE_VARIETY_VACUOUS` — an instrument complaint — rather than as the red
line being crossed.** `r2_1881_variety_control.py`'s docstring still points at
`tools/item_gate.py:~2986` as the twin of that hole; that half is now historical,
and the half in its own subject is not. Not fixed here, and not a line of code
away from being fixed: the honest version walks the plain objects too and has to
decide what "a source" means when there is no instancer to group by.

### Reproduce

```
bash tools/buildlock.sh r2-1381-PREFIX  /opt/blender-5.2.0-linux-x64/blender \
  -b -noaudio --factory-startup --python tools/r2_1381_variety_control.py -- \
  --n 4500 --sources 40 --gate git:cea0e57        # C1 must print True
bash tools/buildlock.sh r2-1381-POSTFIX /opt/blender-5.2.0-linux-x64/blender \
  -b -noaudio --factory-startup --python tools/r2_1381_variety_control.py -- \
  --n 4500 --sources 40                           # CONTROLS ALL PASS
python3 tools/r2_1381_rescore.py                  # no Blender, no render
```

The post-fix run was repeated against the final committed code (`tmp/r2_1381_final.log`, all four controls pass) because the report-key
addition in R2-2957 landed after the first one — a control that ran against an earlier state of the file is evidence about that file, not
about this one.

### Proposed defect-log entry (NOT written to `DEFECT-LOG-R2.md` — for the owner to merge)

> **R2-1381 — CLOSED. The variety guard's plain-object path graded 4,500 copies
> of two meshes as a pass.** `item_gate.per_instance_variation` held
> geometry-nodes instances to 8–40 distinct sources, the same number of distinct
> shapes and a 25 % commonest-share ceiling, but asked an item emitting plain
> objects only for `cv_size >= 0.03` and `distinct_topologies >= 2`. Watched
> failing before it was fixed: 4,500 plain objects from 2 source meshes at
> random uniform scale measured `cv_size 0.11691`, `distinct_topologies 2`, and
> the guard as shipped (`cea0e57`) returned **true**. The plain-object path now
> fingerprints each object's evaluated mesh with `_shape_signature` — the same
> function the realized path uses — and applies the same
> `need_distinct_shapes(n)` and `top_share_limit(n)`, both now shared rather
> than duplicated; the false accept measures **2 shapes against 40 required and
> a 50 % commonest share against 25 %** and is refused. Positive controls pass
> (4,500 objects from 40 bodies; 7 objects from 7 bodies). Re-scoring the 33
> shipped reports: **no false accept shipped**, 0 strong-path verdicts move, and
> **5 ACCEPTED items (`armco_post`, `catch_fence_post`, `crew_figure`,
> `heras_fence_panel`, `pit_wall_unit`) become UNPROVEN** because the
> commonest-shape share was never recorded on that path — they need a re-gate,
> not a re-render. Residual, recorded not gated: variation baked into vertex
> data rather than the object matrix still reads as distinct shapes; the report
> now carries `distinct_shapes_scale_invariant` (298 shapes → 3 families in the
> probe) so a reviewer can see it. Related and NOT fixed: `declared <= 1` still
> exempts a population entirely, which covers 7 items on disk, one of them 459
> objects. **Still open one level up:** `tools/instance_variety.py` skips
> non-instances entirely (`:68`), so plain-object populations contribute zero
> to `docs/instance_variety.json`, the film-wide variety number — the arm
> `tools/r2_1881_variety_control.py --arm plainspam` exists to show exactly
> that and it is unaffected by this fix.

---

## R2-2990..R2-2999 — forecourt paving: the 0.95 mm/px headline is one voxel of a slab buried under the showroom floor, and the item is filmed at 4.49 mm/px

### The two numbers that disagreed, and neither survived

R2-2945 ranks `ARCH_Paving_Forecourt` **first in the film** on
`peak_unocc_sharp_px_per_m`: **1049.4475 px/m — 0.95 mm/px — 410 sharp frames**,
quoted against `min_depth_m = 3.79 m`. Its module reads **ITEM_ACCEPTED** in
`render/items/forecourt_paving_bay/gate.json` at `filmed_at_m = 1.7`,
`lens_mm = 35`, `onscreen_px_4k = 2160` — **2196.1 px/m, 0.4554 mm/px** — with
`framing_source: "item_manifest.json"`.

The module was BUILT to the second. Its docstring opens with a twelve-row pixel
table headed *"px_per_m = (3840 * 35 / 36) / 1.7 = 2196.1 px/m -> 1 px =
0.4554 mm"*, and `PX_PER_M` / `MM_PER_PX` / `lod_pitch()` are all derived from
`NEAREST_CAMERA_M = 1.7`.

**Measured against the live camera, the item is filmed at 222.78 px/m —
4.4887 mm/px — at f910, 10.055 m on a 21.000 mm lens.** The gate over-framed it
by **9.86x linear and 97.2x in area**, which sits almost exactly on
`WAVE2-RANKING.md` §7 step 1's measured median of 8.83x.

And "3.79 m at 1049.4 px/m" was never one measurement: 3.79 m is `min_depth_m`
over all visible frames and 1049.4475 px/m is at f282, where the depth is
**5.8952 m on a 58.000 mm lens**. Two frames, quoted as one framing — the same
composition error the manifest makes.

### The instrument and its calibration

`tools/r2990_forecourt_framing.py`. Camera through `tools/live_campath.py`
(no path is named for a live read; `--selftest` asserts the only `film*_path.json`
literal in the file is the calibration control's). Projection constants
`RES_X`, `RES_Y`, `SENSOR_MM`, `SMEAR_SHARP_PX`, `OCC_RES`, `OCC_TOL_M` and the
quaternion convention are IMPORTED from `tools/screen_presence.py`; bay geometry
(`CELL_W`, `CELL_H`, `SETOUT_X`, `RIBBON_KEEPOUT`) is imported from the item
module; `R1_SHELL` is parsed out of `world/build_architecture.py`'s AST because
that module is contended and imports `bpy`. Nothing is retyped.

**Calibration, run first and deliberately uncorrected:** configured exactly as
`screen_presence.py` was — whole object, voxel z as stored, no sample floor — on
the camera `sp_objects.json` was measured against, it returns
**1049.4475 px/m at f282, 1.64e-8 relative error, and 410 sharp frames against
the published `frames_sharp: 410`.** Every correction below is therefore a
change of subject or of camera, not a change of instrument.

### R2-2947's f282 claim is confirmed — and its 0.17 deg was a comparator artifact

At f282 `film17` and `film19` are **byte-identical in `p`, `q` and `lens`**,
checked on the raw JSON with no instrument in between. So B (swap to the live
camera) moves nothing: 1049.4475 px/m at f282 either way.

R2-2947 reports **0.17 deg** of orientation difference at that frame.
`screen_presence.camera_track` builds R straight from a quaternion the path files
round to six decimals, so |q|^2 = 0.999999 and R is off orthonormal by ~1e-6;
`acos((tr-1)/2)` is ill-conditioned at tr=3 and turns that into an apparent
0.17 deg. Orthonormalising and using `2 asin(||Ra-Rb||_F / 2sqrt2)` returns
**exactly 0.0**. The identity arm — a path compared against ITSELF, which must
report zero frames differing — is what caught it. With the fixed comparator the
whole-film figures reproduce R2-2947 exactly where they should: worst
**21.399 m at f2177**, **55.996 mm at f2978**, **78.753 deg at f2857**; 845
frames differ in position or lens and **2,477 of 2,978 differ in any of p/q/lens**
(R2-2947's 846 is the position-or-lens count).

### The ablation: what each correction is worth

| step | px/m | mm/px | frame | depth | lens | samples |
|---|---:|---:|---:|---:|---:|---:|
| A. `sp_objects` reproduced (calibration) | **1049.447** | 0.953 | 282 | 5.895 m | 58.000 | **1** |
| B. + the live camera | 1049.447 | 0.953 | 282 | 5.895 m | 58.000 | 1 |
| C. + only the item's OWN geometry | 275.457 | 3.630 | 104 | 13.553 m | 35.000 | 242 |
| D. + voxel centre -> the bay plane | 389.249 | 2.569 | 74 | 14.999 m | 54.734 | 3 |
| E. + >= 25 sharp unoccluded samples | 271.551 | 3.683 | 104 | 13.748 m | 35.000 | 243 |
| **F. + camera OUTSIDE the pavilion, >= 10** | **222.783** | **4.489** | **910** | **10.055 m** | **21.000** | 10 |
| F. + camera outside, >= 25 | 158.065 | 6.327 | 1011 | 19.378 m | 28.716 | 31 |
| F. + camera outside, >= 50 | 155.257 | 6.441 | 1013 | 19.975 m | 29.074 | 56 |

**C is the finding.** `ARCH_Paving_Forecourt` is not only the paving bays. The
item module's own docstring, section *"WHAT THE ASSEMBLY MUST DELETE"*, says it
replaces THE BAY FACES AND ONLY THE BAY FACES and that the assembly must KEEP
the object's sub-base prism and *"its formation slab under the pavilion
(R1_FORMATION_Z), which this module does not build."* Same Blender object, same
row in `sp_objects.json`.

**The single cloud point that sets the published 1049.4475 px/m is at
(3.5, -3.5, -0.5)** — inside `R1_SHELL = (-15.250, 15.000, -11.250, 11.250)` and
on the voxel layer that holds `build_architecture`'s closed formation slab at
-0.36..-0.100, under a showroom floor whose top is 0.000. It is 1 of 2,448
points; 3 of 2,448 are in frustum at f282 and 1 is sharp. Masking to the item's
own geometry — bay layer, outside the shell, outside the access ribbon: 1,712 of
2,448 points kept, 736 dropped off the bay layer, 152 inside the pavilion, 12 in
the ribbon — moves the answer by **73.75 %.** This is R2-1362 / R2-2941's
"measuring their host", one level in: not a shared host, but a shared OBJECT.

**F is the frame refusing to agree with the arithmetic.** The winners at every
step up to E have the camera INSIDE the pavilion (f1–f903, 903 of 2,978 frames).
`work/r22161_proxy/r22161_proxy_000282.png` is a showroom interior;
`*_000104.png` is a dark showroom floor with suspension parts hanging over it
and a concrete wall behind. Neither contains any forecourt paving. The occlusion
model is a quarter-res depth buffer rasterised from a 1 m point cloud and
`screen_presence.py` says in terms that `ever_unoccluded = True` is not proof — a
cloud at 1 m cannot express a wall. This is `r2941_veg_framing.py`'s reading 2
exactly (a peak at f147 that was a wheel macro indoors), and the same coarse
proxy is adopted here, after the image refuted the alternative and not before.
`work/r22161_proxy/r22161_proxy_000910.png` **does** show large paved bays with
a legible joint grid.

### The pixel footprint, stated BEFORE anything was changed — and nothing was changed

`tools/r2990_forecourt_pixels.py`, every dimension imported from the module.
Sun elevation 12.47061 deg read out of the relief audit's own record; shadow
amplifier 4.5217. Grazing factor at f910 is **|n.v| = 0.2071 (11.95 deg above
the pavement)**, so in-plane sizes along the view lose 79 % — the shadow column
is given as a range from face-on to fully grazing.

| feature | mm | px @ GATE (0.4554 mm/px) | **px @ FILM (4.4887 mm/px)** | shadow px, face-on .. grazing | verdict at the film framing |
|---|---:|---:|---:|---|---|
| joint slot, nominal width | 12.00 | 26.35 | **2.67** | — | resolves |
| joint slot, narrowest | 7.00 | 15.37 | **1.56** | — | 1-2 px, marginal |
| joint slot, widest | 24.00 | 52.71 | **5.35** | — | resolves |
| joint depth, deepest (washed out) | 30.00 | 65.88 | **6.68** | 30.22 .. 6.26 | resolves |
| joint depth, shallowest (fresh sand) | 5.00 | 10.98 | **1.11** | 5.04 .. 1.04 | 1-2 px, marginal |
| cast arris chamfer (formed edge) | 5.00 | 10.98 | **1.11** | 5.04 .. 1.04 | 1-2 px, marginal |
| sawn arris break (cut edge) | 0.60 | 1.32 | **0.13** | 0.60 .. 0.13 | SUB-PIXEL |
| mould line down the flag face | 22.00 | 48.31 | **4.90** | 22.16 .. 4.59 | resolves |
| arris chip | 2.00 | 4.39 | **0.45** | 2.01 .. 0.42 | SUB-PIXEL |
| chipping zone in from the edge | 16.00 | 35.14 | **3.56** | — | resolves |
| saw-blade score on a sawn face (BUMP) | 0.25 | 0.55 | **0.06** | — | SUB-PIXEL |
| sawn gap where a flag was cut in | 3.00 | 6.59 | **0.67** | — | SUB-PIXEL |
| blast finish: aggregate cell, max | 4.60 | 10.10 | **1.02** | — | 1-2 px, marginal |
| blast finish: aggregate proud, max | 1.00 | 2.20 | **0.22** | 1.01 .. 0.21 | SUB-PIXEL |
| agg finish: aggregate cell, max | 7.60 | 16.69 | **1.69** | — | 1-2 px, marginal |
| agg finish: aggregate proud, max | 2.05 | 4.50 | **0.46** | 2.06 .. 0.43 | SUB-PIXEL |
| coarse stone, the 14 mm one the docstring names | 14.00 | 30.75 | **3.12** | — | resolves |
| sub-mm matrix pitting (BUMP) | 0.15 | 0.33 | **0.03** | 0.15 .. 0.03 | SUB-PIXEL |
| matrix erosion | 0.80 | 1.76 | **0.18** | 0.81 .. 0.17 | SUB-PIXEL |
| flag-to-flag lip, target | 3.00 | 6.59 | **0.67** | 3.02 .. 0.63 | SUB-PIXEL |
| flag warp across the diagonal | 2.40 | 5.27 | **0.54** | 2.42 .. 0.50 | SUB-PIXEL |
| flag rock on a short bed | 2.10 | 4.61 | **0.47** | 2.12 .. 0.44 | SUB-PIXEL |
| bed level scatter (1 sd) | 1.60 | 3.51 | **0.36** | 1.61 .. 0.33 | SUB-PIXEL |
| settlement basin depth | 5.50 | 12.08 | **1.23** | 5.54 .. 1.15 | 1-2 px, marginal |
| jointing grit relief, max | 3.10 | 6.81 | **0.69** | 3.12 .. 0.65 | SUB-PIXEL |
| jointing grit grain, max | 2.20 | 4.83 | **0.49** | — | SUB-PIXEL |
| bitumen overband width | 55.00 | 120.78 | **12.25** | — | resolves |
| bitumen overband proud | 3.00 | 6.59 | **0.67** | 3.02 .. 0.63 | SUB-PIXEL |
| grout collar width | 55.00 | 120.78 | **12.25** | — | resolves |
| MESH PITCH near band (d <= 2.6 m) | 0.85 | 1.87 | **0.19** | — | MESH FLOOR |
| MESH PITCH band 3 (d <= 7.0 m) | 3.40 | 7.47 | **0.76** | — | MESH FLOOR |
| MESH PITCH far band (d > 7.0 m) | 6.80 | 14.93 | **1.51** | — | MESH FLOOR |
| MESH PITCH library flags | 9.00 | 19.77 | **2.00** | — | MESH FLOOR |


**24 of 43 non-mesh features are sub-pixel at the framing the film uses. At the
framing the gate accepted, 2 were** — and those two are the two the module
deliberately left to a bump map. The item's whole lippage/warp/rock/chip/
aggregate vocabulary — the thing that makes it precast flags rather than a scored
plane — lands between 0.13 and 0.78 px. The mesh is cut at a 0.85 mm near-band
pitch, **0.19 px**, and carries **22,945,780 triangles** whose median edge is
**0.23 px** at the measured framing (2.29 px at the gate's).

Not everything dies: the 12 mm joint slot is 2.67 px, its 30 mm washed-out depth
6.68 px, the 22 mm mould line 4.90 px, the 55 mm bitumen overband 12.25 px, the
14 mm coarse stone 3.12 px, and the 16 mm chipping zone 3.56 px. **The bay
module and the joint pattern survive; the surface finish does not.** The
manifest's own note for this item — *"Bay module and joint pattern must survive a
1.7 m lens - a single unbroken slab reads as lino"* — turns out to name the half
that is still true at 10 m.

### The relief stack IS alive, and it is alive below the resolvable floor

`render/items/_relief/forecourt_paving_bay.json`, written 2026-08-03 20:36
against the 12:26 witness blend, so it is not one of the 28 stale ones:
**4 materials with bump, 5 stages, 0 height-unlinked, 0 undeterminable,
0 height-driven-by-a-bump, m_min 0.037, m_median 3.014, m_max 3.7355.** Nothing
in it is dead.

**The number that proves it is rendered, not declared.** `gate.json`'s two-light
block: the band that MOVED when the sun crossed to its other candidate side is
**4.2417 % contrast against the strictest brightness-matched smooth control's
0.0224 % — x189.28**, with the fine band at x151.48. That is a measurement of
the BUILT field in an image, and it is unambiguous.

**The `WAVE2-RANKING.md` §5a tangent trap does NOT bite here, measured rather
than assumed.** Only `FCP_Flag_blast` carries two stages, and they are chained
Normal-to-Normal. Superposing by tangent: 24.397 deg + 0.235 deg of slope give
24.592 deg, **m 3.7634 against a largest declared stage of 3.7355** — 0.03 of
overshoot, not `tree_oak`'s 6.375 from two in-band networks.

**What does bite is scale.** At 4.4887 mm/px:

| stage | driver | lam | m | lam in px | |
|---|---|---:|---:|---:|---|
| `FCP_Flag_blast` / Bump | Noise | 1.067 mm | 3.735 | **0.24** | below 2 px Nyquist |
| `FCP_Flag_blast` / Bump.001 | Wave | 89.760 mm | 0.037 | 20.00 | |
| `FCP_JointFill` / Bump | Noise | 1.778 mm | 3.014 | **0.40** | below 2 px Nyquist |
| `FCP_Overband` / Bump | Noise | 4.706 mm | 3.067 | **1.05** | below 2 px Nyquist |
| `FCP_Reinstatement` / Bump | Noise | 1.455 mm | 2.269 | **0.32** | below 2 px Nyquist |

**Four of the five audited stages carry m 2.27–3.74 at a wavelength under two
pixels.** `itemkit.OCTAVE_FLOOR_PX = 2.0` and `OCTAVE_FLOOR_MM = 2.38`; three of
the four are under 2.38 mm outright. At the gate's 0.4554 mm/px they were 2.34,
3.90, 10.34 and 3.19 px — all legal. **The framing is the only thing that made
them legal.**

Three further gaps, each a measurement rather than a reading of the report:

1. **The module never invokes the relief law at all.** `grep -n itemkit
   world/items/forecourt_paving_bay.py` returns nothing across 3,836 lines. No
   `relief_budget`, no `relief_amplitude_for`, no `detail_for`. Bump `Strength`
   and `Distance` are typed literals, and the module's private `_MB.noise(co,
   scale, detail=6.0, ...)` takes a raw `Scale` — the exact API `itemkit.noise()`
   exists to replace *("makes the caller state a wavelength instead of a
   Scale")* — with the house `detail=6.0` default the octave law names as the
   thing nobody chooses. The 1.067 mm pit noise runs `detail=5.0`, so it also
   emits octaves down to **0.033 mm**.
2. **Half the item's bump stages have never been audited.** The module builds 10:
   `_flag_material` x 3 families x 2, plus joint, overband, reinstatement and
   `FCP_Colonist`. The audit found 5, because it runs on `witness.blend`, which
   contains ONE object. `FCP_Flag_agg`'s two stages are numerically identical to
   blast's (m 3.7355 / 0.0370); `FCP_Flag_hone`'s bump1 is at Strength 0.12
   instead of 0.55, i.e. amp 0.0336 mm, slope 5.652 deg, **m 0.8906** — a third
   band again, never reported anywhere.
3. **The geometry half of the audit covered 6,390 of 22,945,780 triangles —
   0.0278 % of the item**, one object, `FCP_Joint_01231`, banded 4–12 mm at
   rms dihedral 2.383 deg, m 0.376. The layer that caught the human figures'
   fold field at m 2.32 after the shader was corrected has effectively not been
   run on this item.

### The re-gate

**Command** (`--out` and `--witness-dir` deliberately under `work/`, so the
published `render/items/forecourt_paving_bay/gate.json` and its witness PNGs are
not overwritten):

```bash
bash tools/buildlock.sh r2990-regate-forecourt \
  /opt/blender-5.2.0-linux-x64/blender -b -noaudio \
  world/items/forecourt_paving_bay_test.blend --factory-startup \
  -P tools/item_gate.py -- --item forecourt_paving_bay \
  --out work/r2990/gate/gate_measured_framing.json \
  --witness-dir work/r2990/gate_witness \
  --samples 512 --always-render \
  --filmed-distance-m 16.7577 --onscreen-px-4k 595.3
```

**Verdict: `ITEM_UNMEASURABLE`, exit 3 (VACUOUS in `tools/gate_exit.py`'s
scheme). Not ACCEPTED, and not REJECTED.**

```
>> item forecourt_paving_bay  hero=True  filmed at 16.7577 m on a 35 mm lens
>> 450 objects, 22945780 triangles, 7 materials
>> edges  p10    0.85 mm =     0.19 px   (limit 6.0 px -- this is the check)
>>        med    1.04 mm =     0.23 px   (advisory)
>> relief wiring: 54 node tree(s) read from the BLEND, 0 miswired, 0 relief
   output(s) feeding a computation
>> 223 px/m at the filmed distance = 4.489 mm per pixel.
   Band radii: r1=4.5mm, r2=9.0mm, r4=18.0mm, r8=35.9mm, r16=71.8mm
>> triangles: 22945780 total, 38545 per onscreen pixel
>>   subject 544 px, sphere 115817 px, plane 43691 px
>> REFUSING TO REPORT A VERDICT: the witness frame is unusable, so every
   render-based check was forfeited and nothing was measured about this module
>> STAGE RESULT: ITEM_UNMEASURABLE
```

`unmeasurable: ["only 544 subject pixels (need 12000) -- the subject does not
fill enough of the witness frame to measure"]`. The witness subject is the
typical instance, `FCP_Joint_01231`; at 16.76 m it is 544 px of an 8.3 M-pixel
frame, so **`surface_microstructure`, `relief_reads_as_lip_and_shade` and
`silhouette_departs_from_analytic` are all `null` — forfeited, not passed.**

**So the ACCEPTED verdict is a verdict about 0.4554 mm/px and nothing else.**
At the framing the film uses, the gate's three render-based checks — including
the relief check, the one 21 of 28 wave-1 items failed — cannot be taken at all.
The item is not shown to be bad; it is shown to be **unmeasured at its own
framing**, which under this project's own rule (R2-018/R2-019, "an unproven pass
is not a pass") is the one thing that must not read as an acceptance.

The checks that do not need the render all still pass at the new framing:
`no_external_assets`, `material_depth`, `relief_wiring_reaches_the_shader`
(new since the 2026-08-03 run: 54 node trees read from the blend, 0 miswired),
`geometry_resolves_at_distance` — 0.19 px against a 6.0 px LIMIT, which the check
reads as comfortably fine because it is a ceiling on coarseness with no floor —
and `per_instance_variation` (4,009 realized from 385 sources / 169 shapes,
commonest 2.9 %). The gate also repeats its own 2026-08-03 warning that
*"the source meshes are largely COPIES of each other: 385 datablocks carrying
only 169 shapes."*

**Cost: $0.0264** on the 5090 broker — two 4K/512-sample frames, 2.946 s and
2.944 s of GPU each, the rest instance spin-up. Well under the $5 I was told to
ask before exceeding.

**One side effect, owned and undone.** `--witness-dir` redirects the PNGs and
the spec but NOT the staged blend: `item_gate.stage_witness` writes
`render/gate_witness/<item>/witness.blend` from the manifest, so the re-gate
overwrote the published 2026-08-03 witness blends (the ones
`render/items/_relief/forecourt_paving_bay.json` names). Blender's own `.blend1`
backups held the originals; both are **restored byte-for-byte**
(sha256 `9ef1e31a…` / `64971343…`, 4,628,503 / 4,628,505 bytes, mtime 2026-08-03
12:26) and my 16.7577 m staging is kept at
`work/r2990/gate_witness/blends_16.7577m/`. The published PNGs and
`witness_spec.json` were never touched. **This is a real trap for anyone
following `WAVE2-RANKING.md` §7 step 1 and re-gating 32 items at measured
framing: `--out` and `--witness-dir` do not make the run read-only.**


**The R2-1367 lens trap applies, and hard.** `item_gate.py` honours
`--filmed-distance-m` (line 3081) and reads `lens = rec["lens_at_closest_mm"]`
(line 3088) with no override; there is still no `--lens-mm`. The film's lens at
f910 is **21.000 mm**, the manifest's is 35. Handing the gate the true depth
10.0546 m would stage the witness at **371.3 px/m against the film's 222.78 —
66.7 % too large**, far worse than R2-1367's original 9.4 %. So the gate is
handed **16.7577 m, which is a 35 mm-EQUIVALENT and not a position**, derived as
`(3840 * 35 / 36) / 222.783`. `--onscreen-px-4k 595.3` is the measured screen
diagonal of one 1.5 x 1.0 m flag at f910, projected corner by corner; the naive
unforeshortened figure the manifest's formula would give is 273.4 px.

At the SAME frame the trap would have been invisible in step E: at f104 the
film's lens is 35.000 mm exactly, so distance and 35 mm-equivalent coincide at
13.7482 m. The trap only became visible because the subject mask moved the
answer to a frame with a different lens.

### Every control, and the failure each one was watched to produce

No arm below is quoted from a pass. Each one was damaged and watched to
produce the failure named beside it.

**1. `--selftest`, 16 arms on `r2990_forecourt_framing.py`, 12 on
`r2990_forecourt_pixels.py`.** The negative arms and what they caught:

| arm | the failure watched |
|---|---|
| a point behind the camera | rejected at depth -10.000 |
| 3.7 m off axis on a 50 mm lens at 10 m | rejected at px 3893.3 of 3840 — **and 3.5 m accepted at px 3786.7**, so the arm is not "reject everything" |
| pinhole vs radial | 4.000 vs 5.000 on the same point: 25 % |
| a grazing flag | 382.4 px against the closed form's 385.8 and face-on's 673.0 — **the first threshold I wrote (0.55x) FAILED at 0.568 and was replaced by the closed form rather than loosened** |
| **IDENTITY: a path against itself** | **FAILED on first run — 1,087 frames "differ", worst 2.958e-06 deg.** That is what exposed the `acos((tr-1)/2)` conditioning, and therefore that R2-2947's 0.17 deg is an artifact |
| the subject mask MUST REJECT (3.5,-3.5,-0.5) | rejected — inside `R1_SHELL`, formation-slab layer |
| the subject mask MUST KEEP the east forecourt | kept, so it is not "reject everything" |
| plane snap MUST MOVE the points | by 0.500 m |
| the pixel table MUST FIRE on 0.25 mm and 0.15 mm | both flagged SUB-PIXEL |
| the pixel table MUST NOT FIRE on the 12 mm joint | not flagged |
| vacuity BOTH ways | at 1e-6 mm/px nothing is sub-pixel; at 1e6 mm/px all 43 are |
| **the table is WIRED to the module** | `FCP.CHAMFER_W_M` damaged to 0.011 in memory -> the table reports 11.000 mm; damage removed -> 5.000 mm. Without this the whole file could be a transcription and read identically |
| the only `film*_path.json` literal is the control's | asserted by regex over the tool's own source |

**2. A runtime assertion, not a selftest.** Occlusion can only remove points, so
a frame's occluded-sharp peak is bounded by its sharp peak with occlusion
ignored. The tool REFUSES if the winner does not exceed the weakest shortlisted
frame's occlusion-free peak, rather than returning the best of an arbitrary 240.

**3. `tools/r2990_forecourt_framing_control.py` — six damage modes, two
configurations, and it FAILED TWICE AND FOUND A REAL BUG IN MY OWN TOOL.**

Run 1: **four of six arms read `moved 0.00 %` — radial, no_frustum, no_smear,
no_occ.** Cause: pass 2 (the occlusion pass) re-derived the winning frame's
px/m with its own undamaged arithmetic, so the damage switches altered only the
shortlist ORDER and the same frame won anyway. Four checks that changed nothing —
this project's most-logged defect shape, committed by the file written to catch
it. Fixed by extracting one `frame_metrics()` used by both passes.

Run 2: radial, no_smear, no_subject_mask and no_plane_snap fire on the headline;
no_frustum and no_occ still read 0.00 %.

Run 3, widened to every published quantity and to the configuration the ANSWER
uses:

```
== sp (as published) ==
  baseline        1049.4475 px/m at f282   1 pts, 410 sharp frames  REPRODUCES
  radial          ok  ppm 1049.4475->1007.5394
  no_frustum      ok  frames_sharp 410->569, peak_any_ppm 1060.95->170471.94
  no_smear        ok  ppm 1049.4475->1060.9536, f282->f275, frames_sharp 410->1391
  no_occ          FAIL  VACUOUS -- not one published quantity moves
  no_subject_mask ok  ppm 1049.4475->275.4566, f282->f104, pts 1->242
  no_plane_snap   ok  ppm 1049.4475->1085.8599
== answer (masked, snapped, outdoors) ==
  baseline         222.7832 px/m at f910   10 pts
  radial          ok  ppm 222.7832->193.6777
  no_frustum      ok  frames_sharp 191->244, peak_any_ppm 441.30->172580.86
  no_smear        ok  ppm 222.7832->307.7222, f910->f930
  no_occ          FAIL  VACUOUS -- not one published quantity moves
>> STAGE RESULT: R2990_CONTROL_FAIL  vacuous arm(s): sp / no_occ, answer / no_occ
```

`no_frustum`'s `peak_any_ppm 1060.95 -> 170,471.94` is R2-1362's trap made
visible: without a frustum test the object scores off a point essentially at the
lens, 160x its real best.

**`no_occ` is STILL VACUOUS, and I am not silencing it, because the vacuity IS
the finding.** The occlusion buffer removes not one point of this object in
either configuration. `sp_objects.json` says the same thing about itself:
`points_ever_unoccluded == points` (2,448 of 2,448) and `peak_sharp_px_per_m ==
peak_unocc_sharp_px_per_m` **bit for bit**. And it generalises:

| across all 2,261 objects in `sp_objects.json` | count | share |
|---|---:|---:|
| `points_ever_unoccluded == points` | 2,093 | **92.6 %** |
| `peak_sharp_px_per_m == peak_unocc_sharp_px_per_m` bitwise | **1,992** | **88.1 %** |
| `peak_px_per_m == peak_unocc_px_per_m` bitwise | 2,159 | 95.5 % |

**For 88.1 % of the world the `unocc` in `peak_unocc_sharp_px_per_m` — the field
R2-2945 re-ranked wave 2 on — contributes nothing.** It is
`peak_sharp_px_per_m` wearing a prefix. That is precisely why the buffer said
"unoccluded" while proxy frames 282 and 104 show the paving behind a wall, and
it is why the pavilion exclusion had to be added by hand.

**4. The FRAME as a control, which is the one that overruled the arithmetic.**
Readings B through E were falsified by looking at the free proxy renders — 282 is
a showroom interior, 104 is a showroom floor — and F was corroborated the same
way at 910. No paid render was involved in any of it.


### Files

| path | what |
|---|---|
| `tools/r2990_forecourt_framing.py` | the derivation; `--selftest` 24 arms, 9 negative |
| `tools/r2990_forecourt_framing_control.py` | damages it six ways in two configurations and watches the arms fire |
| `tools/r2990_forecourt_pixels.py` | the pixel-footprint table; `--selftest` 13 arms |
| `work/r2990/framing.json` | the ablation, the calibration and the camera A/B |
| `work/r2990/pixels.json` | the per-feature table at both framings |
| `work/r2990/control.json` | every damage arm and what it moved |

Reproduce:

```bash
python3 tools/r2990_forecourt_framing.py --selftest
python3 tools/r2990_forecourt_framing.py --calibrate --out work/r2990/framing.json
python3 tools/r2990_forecourt_framing_control.py
python3 tools/r2990_forecourt_pixels.py --graze 0.2071 --out work/r2990/pixels.json
```

### Proposed defect-log entries (NOT written to `DEFECT-LOG-R2.md` — for the owner to merge)

> **R2-XXXX — the film's highest-resolution surface was a buried slab.**
> `sp_objects.json`'s rank-1 `peak_unocc_sharp_px_per_m` for
> `ARCH_Paving_Forecourt`, 1049.4475 px/m at f282, is set by ONE of 2,448 cloud
> points, at (3.5, -3.5, -0.5) — inside `R1_SHELL`, on the layer of
> `build_architecture`'s closed formation slab at -0.36..-0.100, under an opaque
> showroom floor, in a frame where the camera is inside the pavilion. Restricted
> to geometry `forecourt_paving_bay` actually builds and to frames where the lens
> is outdoors, the item is filmed at **222.783 px/m, 4.4887 mm/px, f910,
> 10.055 m on a 21 mm lens** — the manifest's accepted framing over-frames by
> **9.86x linear / 97.2x in area**. Any `sp_objects.json` row whose object is
> shared between an item and geometry the item does not own has this defect;
> nothing in the pipeline tests for it.

> **R2-XXXX — R2-2947's "0.17 deg at f282" is a comparator artifact, not a
> drift.** `film17` and `film19` are byte-identical in `p`, `q` and `lens` at
> f282. `screen_presence.camera_track` does not normalise the quaternion, the
> path files round it to six decimals, and `acos((tr-1)/2)` at tr=3 turns a 1e-6
> scale error into 0.17 deg. Use `2 asin(||Ra-Rb||_F / 2sqrt2)` after
> orthonormalising; it returns exactly 0.0 and a self-comparison then reports
> zero frames differing. The whole-film worst cases (21.399 m at f2177,
> 55.996 mm at f2978, 78.753 deg at f2857) are unaffected and reproduce exactly.

> **R2-XXXX — `forecourt_paving_bay` never invokes the relief law, and half its
> relief stages have never been audited.** Zero references to `itemkit` in 3,836
> lines; bump `Strength`/`Distance` are typed literals and the module's private
> `_MB.noise()` takes a raw `Scale` with the house `detail=6.0`. The module
> builds 10 bump stages; `relief_audit` reports 5, because it runs on a witness
> blend containing one object — which is also why the geometry half of the audit
> covered **0.0278 % of the item's triangles**. Four of the five audited stages
> carry m 2.27–3.74 at wavelengths of 0.24–1.05 px at the measured framing, all
> below `itemkit.OCTAVE_FLOOR_PX = 2.0`; they were legal only at the manifest's
> 0.4554 mm/px. The `WAVE2-RANKING.md` §5a tangent superposition was checked and
> does NOT bite here (3.7634 built vs 3.7355 largest declared).

> **R2-XXXX — `peak_unocc_sharp_px_per_m` is not occlusion-aware for 88 % of the
> world.** In `work/w2_0/retier_a10/sp_objects.json`, `peak_sharp_px_per_m` and
> `peak_unocc_sharp_px_per_m` are **bit-identical for 1,992 of 2,261 objects
> (88.1 %)**, and `points_ever_unoccluded == points` for 2,093 (92.6 %). The
> occlusion model is a quarter-res depth buffer rasterised from a 1 m point
> cloud, which cannot express a wall; `screen_presence.py` says so and calls
> `ever_unoccluded = True` unproven. Consequence: R2-2945's re-ranking of wave 2
> is, for most of the world, a ranking on `peak_sharp_px_per_m` with a prefix.
> On `ARCH_Paving_Forecourt` it passes paving that is behind the pavilion shell,
> in frames where the camera is inside it. Found because a damage arm that
> removed the occlusion buffer entirely moved not one published quantity, in
> either configuration — the control is left FAILING rather than silenced.

> **R2-XXXX — re-gating at measured framing overwrites the published witness
> blend even with `--out` and `--witness-dir` redirected.**
> `item_gate.stage_witness` writes `render/gate_witness/<item>/witness.blend`
> and `_flip.blend` from the manifest path regardless of `--witness-dir`, which
> only redirects the PNGs and the spec. A re-gate of `forecourt_paving_bay` at
> `--filmed-distance-m 16.7577` replaced the 2026-08-03 blends that
> `render/items/_relief/forecourt_paving_bay.json` describes. Recovered here
> from Blender's `.blend1` backups and verified byte-identical, but
> `WAVE2-RANKING.md` §7 step 1 asks for this to be done to 32 items, and the
> `.blend1` backup only survives ONE overwrite. Either honour `--witness-dir`
> for the blend too, or add `--stage-only`-style isolation.

---

## R2-2949 — correcting R2-2945: three of my rows do not survive, the headline does, and the field I ranked on is not occlusion-aware

R2-2990..R2-2999 refuted my top row. I re-tested the rest of my own table the
same way — camera outside the pavilion, and a **minimum sharp-sample floor**,
which is the control I did not apply and should have. Re-run with the point
cloud and the live camera:

| object | ≥1 sample | ≥10 | ≥25 | verdict on my row |
|---|---:|---:|---:|---|
| `VEG_grass_fescue_H` | 425.82 | **425.82** | **396.91** | **survives** |
| `VEG_grit_chip` | 425.82 | **425.82** | **396.91** | **survives** |
| `VEG_weed_thistle` | 347.88 | **141.41** | **85.73** | **single-sample artifact** |
| `ARCH_Paving_Forecourt` | 165.48 | 163.46 | 161.64 | **withdrawn** (see below) |

**Four things I got wrong.**

1. **`ARCH_Paving_Forecourt` at 1049.4 px/m is withdrawn.** The single point of
   2,448 that sets it is at (3.5, −3.5, −0.5) — inside `R1_SHELL`, on the voxel
   layer holding the closed formation slab at −0.36..−0.100, **under an opaque
   showroom floor, in a frame where the camera is inside the pavilion.** The
   item module's own docstring says it does not build that geometry. Masking to
   the item's own geometry moves the answer **73.75 %**. My independent re-test
   above gives **165.5 px/m**, agreeing with the 158–163 the owning agent
   measured at a ≥25 floor. It was never the highest-resolution surface in the
   film, and it is not in the top group at all.

2. **`VEG_weed_thistle` at 347.9 px/m is withdrawn** — it collapses to 141.4 at
   a 10-sample floor and 85.7 at 25. Same defect as the forecourt row, caught by
   the same control.

3. **The depth column in R2-2945 was composed from two different frames.** I
   paired each `peak_unocc_sharp_px_per_m` with `min_depth_m`, which is the
   minimum over *all* visible frames, not the depth at the peak. Grass is not
   425.8 px/m "at 4.58 m" — it is 425.8 px/m at **f2316, depth 17.40 m**.
   **That is exactly the composition error I criticised the manifest for**, made
   in my own table two sections earlier.

4. **`peak_unocc_sharp_px_per_m` is not occlusion-aware for most of the world.**
   It is bit-identical to the non-occluded `peak_sharp_px_per_m` for **1,992 of
   2,261 objects (88.1 %)**, and `points_ever_unoccluded == points` for 92.6 %.
   `screen_presence.py` says in terms that `ever_unoccluded = True` is not proof
   — a 1 m point cloud at quarter resolution cannot express a wall. I read the
   field's name as a guarantee. It is not one.

### What survives, and why I am not withdrawing the finding

**Grass and grit hold at 425.82 px/m to a 10-sample floor and 396.91 to 25**, and
that row is corroborated by an image rather than by arithmetic:
`work/r22161_proxy/r22161_proxy_002316.png` shows sharp foreground sward filling
the bottom third of frame. The forecourt row was refuted by the same test —
proxy 282 is a showroom interior — so the instrument that killed three rows is
the one that confirms this one.

**Trees hold, by two independent methods that were never wired together:**
`sp_objects.json` gives `VEG_tree_oak0` **22.66 px/m**; my own segment model
(`r2941_veg_framing.py`, different inputs, different code path) gives 829.2 px
on a 23.2 m tree at 104.77 m = **35.7 px/m**. They disagree by 1.6× and agree on
the order of magnitude.

So the corrected ratio is **grass ~397–426 px/m against trees ~23–36 px/m —
11× to 19×, not the 18.8× I quoted.** The build-order conclusion is unchanged:
grass and grit are the top buildable class by measured sharp resolution, trees
are the bottom, and a pine needle at 22.7–35.7 px/m is 0.04–0.06 px.

**What this costs the rest of the ranking:** the R2-2945 table's non-vegetation
rows were taken from the same field with no sample floor and no working
occlusion, so `spectator library figures 791–844 px/m` and `TER_Ground 121.2`
should be treated as **unverified** until re-run with a floor. The two
vegetation rows and the tree rows are the ones tested here.

### And a correction to R2-2947's own arithmetic

R2-2947 reported **0.17 deg** of orientation difference at f282. That is an
artifact of my comparator, not a property of the cameras: the path files round
quaternions to six decimals, so |q|² = 0.999999, and `acos((tr−1)/2)` is
ill-conditioned at tr = 3. With the rotation orthonormalised and
`2·asin(‖Ra−Rb‖_F / 2√2)` the answer at f282 is **exactly 0.0** — the two
cameras are byte-identical there in `p`, `q` and `lens`. **This does not weaken
R2-2947's conclusion, it strengthens it**: the frames my build decision rests on
are not merely close, they are identical. The whole-film worst cases reproduce
unchanged (21.399 m at f2177, 55.996 mm at f2978, 78.753 deg at f2857), and the
one number to restate is the count: my **846** is the *position-or-lens* count;
**2,477 of 2,978** frames differ in any of `p`/`q`/`lens`.

The arm that caught it was an identity control — a path compared against itself,
which must report zero — and it was watched failing at 1,087 frames before it was
believed. I did not build that arm; I should have.

---

## R2-2949a — the subject-mask objection: conceded for the forecourt, refuted for grass, with the measurement that settles it

The forecourt author objected that R2-2949's re-test applied the **sample floor
alone** — the smallest of the three corrections — and would therefore land near
the right number while still measuring the buried slab and the indoor frames:
*agreement, not corroboration*. Checked, and the objection is **half right, and
right about the half that was mine.**

**What my re-test actually applied:** the pavilion exclusion **and** the sample
floor, but **not** the subject mask. So it was two of three, not one of three —
and the missing one is exactly the 73.75 % correction.

### Conceded: my 165.48 px/m is not independent corroboration

At its winning frame (f1008, outdoors) the 25 points that set my figure lie at
**z −0.500..0.500**. The bay faces are the z ≈ 0.5 layer; **z = −0.5 is the
sub-base prism, which the item module's own docstring says it does not build.**
So my number is still measuring geometry outside the subject, just not the same
geometry: the pavilion exclusion removed the indoor peak, and the sub-base
survived it.

**`ARCH_Paving_Forecourt` carries 152 of 2,448 points (6.209 %) inside
`R1_SHELL`.** The authoritative figure is the masked one: **222.783 px/m at ≥10**,
158.065 at ≥25. My 165.48 is withdrawn as corroboration and should not be quoted
beside it.

### Refuted: the grass and grit rows are not shared-object contaminated

The same check, same code, on the rows that survived:

| object | points | inside `R1_SHELL` | top-25 setters in shell | setter z | setter spread |
|---|---:|---:|---:|---|---|
| `VEG_grass_fescue_H` | 164,884 | **1 (0.001 %)** | **0** | 0.500..1.500 | 5.0 × 12.0 m |
| `VEG_grit_chip` | 247,106 | **0 (0.000 %)** | **0** | 0.500..1.500 | 5.0 × 12.0 m |
| `ARCH_Paving_Forecourt` | 2,448 | 152 (6.209 %) | 0 | −0.500..0.500 | 1.0 × 3.0 m |

The 425.82 px/m is set by **25 points spread over 5.0 × 12.0 m**, not one voxel;
all of them **outdoors**; all at **z 0.5–1.5 m**, which is grass standing above
terrain rather than a slab buried under a floor; and centred at
**(−570.5, −64.5)** — 570 m from the pavilion, out on the circuit. The frame is
f2316, which `work/r22161_proxy/r22161_proxy_002316.png` shows as sharp
foreground sward.

**There is no buried layer inside these objects to contaminate them**, which is
the structural reason the forecourt failed and grass did not: `ARCH_Paving_Forecourt`
is one Blender object holding three different things (bay faces, sub-base prism,
formation slab), and `VEG_grass_fescue_H` is one object holding grass.

### Conceded: the f282 point was inverted

R2-2949 said the byte-identical cameras at f282 *"strengthens the conclusion
drawn from it."* That is wrong. **f282 belongs to the withdrawn forecourt row,
so it now supports nothing of mine**, and two identical cameras agreeing on a
measurement of a buried slab is agreement on the wrong object. The frames my
build decision actually rests on are **f2316** (grass, verified outdoors in the
proxy) and **f1727/f1750** (trees). f282 should be struck from the argument.

### Conceded: the 88.1 % was overstated

The correct statement is that `peak_unocc_sharp_px_per_m` is **bit-identical to
the non-occluded series for 1,992 of 2,261 objects**, i.e. the occlusion model
returned "unoccluded" for them. `screen_presence.py` states the asymmetry
itself: **`False` is proof, `True` is not.** It does **not** follow that the
model is wrong everywhere, and my wording implied that. Any re-run needs the
sample floor **and** an occlusion model a 1 m cloud can support, or it
reproduces the same vacuous pass in a new costume.

**Net effect on the build order: none.** Grass and grit hold at 425.82 px/m to a
≥10 floor with zero shell contamination and 25 spatially-spread setters; trees
hold at 22.7–35.7 px/m by two independent methods. The corrected ratio is
11×–19×.
