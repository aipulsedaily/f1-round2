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
