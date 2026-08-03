# Throughput optimisation — how to build 435 items in days instead of weeks

**Scope of this document: EXECUTION EFFICIENCY ONLY.** The work list is taken as
given. A separate pass is deciding what work can be cut against the camera; this
one asks how the work that must happen gets done in fewer agents and fewer hours.

**Quality is not a variable here.** The user has rejected two passes as *"okay
kinda cute"* and *"half assed… the grass is blurry"*, and the standard is
*"surpasses what real life would look like"*. Every lever below either leaves the
standard untouched or raises it. The largest single lever — a gate that predicts
the peep — raises it, because it makes the bar machine-enforced instead of
sampled.

Everything numeric in this document is either measured (with the command or file
that produced it) or a stated assumption with the A/B that settles it. That
discipline is not decoration: `DEFECT-LOG-R2.md` records **six** occasions on
which the verification, not the work, was the broken thing.

---

## 0. The measured starting position

| quantity | value | source |
|---|---|---|
| wave-1 items built | 28 | `world/items/*.py` |
| wave-1 gate results | **28 / 28 ITEM_ACCEPTED, zero rejected** | `render/items/*/gate.json` |
| wave-1 peep results | **15 / 15 REWORK, zero SHIP** | `workflows/wf_e4d7f755-73d.json`, `result.items[]` |
| wall-clock, first gate to last | **16.6 h** (04:49 → 21:26, 2026-07-29) | mtimes of `render/items/*/gate.json` |
| workflow concurrency | **4** | `zWy(n)=min(16,max(2,n-2))`, `nproc`=6 |
| local box | i7-7700K, **6 cores, 11.6 GB RAM**, 12.7 GB already in swap | `nproc`, `/proc/meminfo` |
| remote box | EPYC 7742, **32 effective cores, 515 GB RAM** | vast instance record |
| item test blends on disk | **28 GB** for 28 items (max 2.13 GB, `pont_deck_slab_test.blend`) | `du -sh world/items/` |
| broker jobs against item scenes | 553 jobs, **7,687 s rendering, 40,737 s in-job wall** | `state/broker.db` |
| ⇒ fraction of item-render job time **not** rendering | **81 %** | same |
| median item macro render | **9.2 s**; median per-job overhead **37.4 s** | same |
| lines of Python written in wave 1 | 102,069 across 28 modules | `wc -l world/items/*.py` |
| of which re-implemented scaffold | **27,992 lines = 27.4 %** | function-level diff across the 28 |

Calibration used throughout: fitting 28 builds + 15 peeps into 16.6 h at 4-way
concurrency gives **build agent ≈ 2.4 h, peep agent ≈ 0.3 h**
(28 × 2.4 + 15 × 0.3 = 71.7 agent-h ÷ 4 = 17.9 h ≈ the 18 h observed). The naive
435-item projection reproduces the brief's figure exactly: 870 builds × 2.4 +
870 peeps × 0.3 = 2,349 agent-h ÷ 4 = **587 h = 24.5 days, 1,740 agents**. The
model is anchored, not invented.

---

## 1. THE TABLE — current vs proposed, per lever

Levers are cumulative; each row includes everything above it.

| # | lever | agents | agent-hours | concurrency | wall-clock | why |
|---|---|---:|---:|---:|---:|---|
| — | **baseline, no change** | **1,740** | 2,349 | 4 | **587 h ≈ 24.5 d** | 435 × 2 agents × 2 rounds, at measured wave-1 rates |
| 1 | **gate predicts the peep** — round-2 rate 100 % → 20 % | 1,044 | 1,488 | 4 | 372 h ≈ 15.5 d | the multiplier is rounds, not items; kill the round and you kill ~700 agents. Includes a +0.15 h/build surcharge for the extra passes the new gate renders |
| 2 | **+ batching** — 435 items → ~240 build units, 435 peeps → ~70 cluster peeps | 372 | 1,069 | 4 | 267 h ≈ 11.1 d | 262 of 435 items share zone **and** exact filmed distance; only 73 distinct distances exist across 435 items |
| 3 | **+ remote exec** — bpy build/gate moves to the EPYC | 372 | 928 | 4 | 232 h ≈ 9.7 d | removes the 81 % transfer overhead measured inside item render jobs, and the local swap thrash. **Does not by itself raise concurrency.** |
| 4 | **+ Agent-tool orchestration** — 4 → 16 concurrent | 372 | 928 | **16** | 58 h ≈ 2.4 d | the `min(16, cpu−2)` cap is the *workflow runtime*; the Agent tool's cap is a flat 20, env-overridable. Only safe once (3) has moved the load off this box |
| 5 | **+ `world/itemkit.py` + one worked example** | 372 | 751 | 16 | **47 h ≈ 2.0 d** | 27.4 % of wave-1 output was re-typed scaffold; importing it instead is a straight subtraction from every agent |

**Net: 1,740 agents → 372 (−79 %); 24.5 days → ~2 days (−92 %).**

Two honest caveats on that table:

- Rows 1 and 2 rest on stated assumptions (round-2 rate 20 %; batch cost model
  `2.4 × (0.45 + 0.55n)` hours). Both are checkable on the first tranche; §7 says
  how, and what to do when the check fails.
- Row 4 is the recommendation with real downside risk. §6 states exactly what it
  costs if I am wrong.

At 16-way agent concurrency the plan becomes **agent-bound, not compute-bound**:
240 build units through 12 remote exec slots is roughly 10 h of remote compute
against 47 h of agent time. That is the right place for the bottleneck to sit,
because agent time is the thing that improves with better scaffolding.

---

## 2. KILL THE SECOND ROUND — what the gate must measure

### 2.1 Why the current gate has no discriminating power, in one number

`material_depth` requires ≥ 6 procedural texture nodes for a hero. Across the 28
wave-1 items the measured value ranges **19 to 82, median 45**. The tightest
margin to the threshold in the entire set is **3.2×**. A check whose closest
observed call is 3.2× clear is not a gate; it is a formality.

The same holds for the other two live checks: `geometry_resolves_at_distance`
requires p10 ≤ 6.0 px and measures 0.18–5.12 (median 1.19, only
`gravel_bed_surface` anywhere near); `no_external_assets` is trivially satisfied
by a project that has never had an image texture.

So: **28/28 accepted, 15/15 reworked.** The gate is not slightly permissive. It
is orthogonal to the bar.

`crew_fireproof_overall` has 28 procedural texture nodes and rendered as vinyl.
`spectator_seated` has 51 and rendered as mannequins. Node count asks *"did you
write shader nodes?"* — a question about the code. R2-017's rule is **"measure
the artefact, not the process"**, and `material_depth` is the last check in the
gate still measuring the process.

### 2.2 G1 — assert the delivered frame *(cheapest check in this plan)*

The gate must open `macro.png` itself and assert `width == 3840 and height ==
2160`, and that the camera it was rendered from carries the manifest's exact
`lens_at_closest_mm` at exactly `nearest_camera_m` from the item's bounds. Fail
otherwise.

**Caught defect, measured by me from the PNG headers just now:**

> **11 of 28 wave-1 items (39 %) delivered their hero macro at 1920×1080** while
> `gate.json` reported 4K px/m figures and passed all four checks —
> `armco_post`, `asphalt_wearing_course`, `catch_fence_post`,
> `grandstand_riser_unit`, `heras_fence_panel`, `kerb_precast_unit`,
> `mullion_intact`, `pont_girder`, `team_truck_trailer`, `timing_stand`,
> `tyre_wall_tyre`.

Root cause is in the harness, not the agents:
`workflows/scripts/item-campaign-wave1-foundations-wf_0ee7b7fb-854.js:107-108`
instructs `./rq render --cam <CAM> --res 1920 1080`. The gate never opened the
image at all, so a 2× resolution error was invisible to it — and 39 % of wave
1's peep evidence was gathered at half the resolution the peep was supposed to
judge. `heras_fence_panel`'s reviewer noticed independently: *"delivered at
1920×1080 = 622 px/m, against a detail budget built to 1244 px/m."*

Cost to implement: minutes. Cost of not having had it: 39 % of a wave.

### 2.3 G2 — band-passed contrast, against a reference the gate **identifies**

The synthesis proposes *"band-passed contrast against a known-smooth reference in
the same frame"*. That is right, and the naive implementation of it is a trap.

I ran the naive version over all 28 delivered macros — take the top 12.5 % of the
frame as "sky" and use it as the smooth control. It fails: `gravel_bed_surface`
returns a background band-pass of **23.86 %** and `spectator_seated` **12.15 %**,
because in those frames the top of the image is ground and crowd. A positional
assumption about where the reference lives is precisely the *"reported success
while measuring nothing"* failure this project has hit six times.

**The reference must be identified, not assumed.** Render a **Z pass** and an
**Object Index pass** beside the beauty. `Z == inf` is the true background mask —
guaranteed smooth because it is the sky shader with no geometry behind it.
`object_index == <item>` is the true subject mask. Neither is a guess.

Then, over the subject mask only, with `bp(r) = RMS(boxblur_r − boxblur_2r) /
mean` at r ∈ {1, 2, 4, 8, 16} px:

| requirement | threshold |
|---|---|
| absolute fine-scale structure | `bp(1) ≥ 3.0 %` (hero) |
| beats its own background | `bp(1) ≥ 1.5 × bp_background(1)` |
| energy is not all coarse | `bp(1) / bp(4) ≥ 0.25` |
| beats any `STANDIN_`/`CTX_` object in the same frame | at r = 1, 2 and 4 |

**Caught defects.** My measurement over the lower band of each delivered macro,
`bp` at r1/r2/r4:

| item | bp r1/r2/r4 | r1/r4 | what the peep said |
|---|---|---:|---|
| `tyre_blanket` | **0.81 / 0.84 / 0.74** | 1.09 | flattest in the set, and *falling* with radius; subject is 0.6 % of pixels |
| `access_road_slab` | **0.40 / 0.98 / 2.22** | 0.18 | *"about a third of total image area carries no resolvable detail"* |
| `forecourt_paving_bay` | **0.59 / 1.40 / 3.08** | 0.19 | *"no feature finer than ~8–12 native px"* |
| `armco_w_beam` | **0.89 / 2.30 / 5.76** | 0.15 | *"zero zinc spangle, zero crystal boundaries, zero dendrite"* |
| `kerb_precast_unit` | **1.11 / 2.97 / 6.51** | 0.17 | *"max \|dLum/dx\| = 0.0897 over 2,072,520 px; zero pixels above 0.10"* |
| `pit_wall_unit` | 1.17 / 2.03 / 3.15 | 0.37 | — |
| `mullion_intact` | 1.79 / 2.77 / 4.15 | 0.43 | — |
| `gantry_truss` | 1.80 / 2.79 / 4.04 | 0.45 | — |
| `showroom_facade_panel` | 1.84 / 3.77 / 6.09 | 0.30 | — |

Nine of 28 fail `bp(1) ≥ 3.0` outright and six of those also fail the
coarse-energy ratio. And the two cases the synthesis built its argument on are
the cleanest of all, because in both the reference is *inside the frame*:

- `crew_fireproof_overall`: fabric **0.89 / 0.34 / 0.49 / 0.96 / 1.33** against
  the `STANDIN` smooth featureless ovoid head at **1.52 / 0.86 / 1.06 / 1.34 /
  1.66**. The Nomex is flatter than the placeholder blob at every single radius.
- `marshal_post_column`: hero steel **0.69 / 0.73 / 0.78** at r4/8/16 against
  concrete **1.52 / 2.25 / 2.72** and dirt **1.88 / 2.58 / 2.65** in the same
  render, with sky at **0.03 / 0.02 / 0.02**. The hero is the flattest real
  surface in its own frame.

Node count caught **none** of these. Both `crew_fireproof_overall` (28 nodes) and
`spectator_seated` (51) were ≥ 3× the hero threshold.

### 2.4 G3 — the sun-difference pass: value PAIRS, measured not inferred

The synthesis asks for *"value PAIRS not colour marks at a 12.5° raking sun."*
Make it exact rather than aesthetic: render the frame **twice** — once complete,
once with the sun lamp muted (sky only) — and take `L_direct = L_full − L_sky`
per pixel. That is an exact decomposition of the illumination, with no inference
about what a shadow "should" look like.

| requirement | threshold | what it is |
|---|---|---|
| (a) a dominant direct key exists | `mean(L_direct) / mean(L_full) ≥ 0.45` over the subject | there IS a sun, and it is doing the lighting |
| (b) the frame contains a **pair** | ≥ 2 % of subject px with ratio > 0.6 **and** ≥ 2 % with < 0.1 | lit and shadowed samples of the same material both present |
| (c) the shadow is the right length | cast run within ±25 % of `h · cot(12.47°) = 4.51 h` | `L_direct` **is** the shadow map |

**Caught defects, all with the peeps' own numbers:**

- `team_truck_trailer` — landing-leg shadows measured ~1:1 with leg height,
  implying a ~45° source. At 12.5° a 1.2 m leg needs **5.4 m** and the 4.0 m body
  needs **18 m**; observed body shadow **3–4 m**. Fails (c) by ~4.5×.
- `tyre_blanket` — a 0.720 m wheel must cast **3.26 m**; observed a compact lobe
  **one wheel-diameter** long. Wall shadows only ~12 % darker in sRGB (~1.3:1
  linear) ⇒ direct sun ≈ **one fifth** of that wall's illumination. Fails (a) and (c).
- `marshal_post_column` — ten shadow edges measured a **14–30 % luminance drop**,
  i.e. direct sun contributing only ~20–25 % of ground illumination. Fails (a) at
  0.20–0.25 against 0.45.
- `armco_w_beam` — bolt-head shadows ~1 head-length imply a 30–40° sun. Fails (c).
- `driver_figure` and `pont_deck_slab` — **neither module calls `lights.new` at
  all.** Both rely on `tools/fix_audit_blend.py:59-105 procedural_world()`, which
  builds a Sky Texture → Background → Output and **no light object of any kind**
  (`sun_intensity = 0.85` there is a Sky-Texture property, not a lamp). Neither
  item was ever peeped. G3(a) fails them at `mean(L_direct)/mean(L_full) = 0`,
  which is the only clean way this gets found.

**Correction to the synthesis, with a count.** SYSTEMIC-1 ("the item test scenes
have no sun") is too broad. **26 of 28 wave-1 modules do build a real SUN lamp**
at `C.SUN_ENERGY = 115.754` with `C.SUN_COLOR` and the correct
`SUN_DIR.to_track_quat("Z","Y")` orientation — including `spectator_seated`, the
item the synthesis cited (`spectator_seated.py:2504-2547`), and
`asphalt_wearing_course`, whose own peep independently confirmed a warm
directional key (R−B rising to **+0.0991** in the top band, R/B 2.39). The real
residual defect is narrower and worse: **two modules have no sun at all, and the
shared helper silently supplies none to anyone who trusts it.** G3 turns that
from an argument into a measurement, and `itemkit.contract_light()` (§5) makes it
unrepeatable.

### 2.5 G4 — the amplitude ledger *(this is the one that replaces node counting)*

Fifteen reviewers independently performed the same arithmetic: *the module claims
feature X at size S; at this item's px/m that is P pixels; is P present in the
image?* Fifteen times, same operation, by hand. It is fully mechanisable, and it
is the direct expression of the synthesis's core finding —

> *"the mechanism is in the code and its amplitude is 3–5× too small to survive
> to pixels… invisible to any check that inspects the code rather than the image."*

Each module emits `render/items/<id>/amplitudes.json`:

```json
{"features": [
  {"name": "zinc spangle",     "size_m": 0.020,   "signal": "albedo"},
  {"name": "push-back kink",   "size_m": 0.181,   "signal": "silhouette"},
  {"name": "proud nail head",  "size_m": 0.025,   "signal": "silhouette"},
  {"name": "joint lip shadow", "size_m": 0.00286, "signal": "shadow"},
  {"name": "wet bitumen",      "size_m": 0.004,   "signal": "specular"}
]}
```

The gate computes `expect_px = size_m × px_per_m` **itself**, from the manifest —
never trusting the module's arithmetic — then, per signal type:

| `signal` | measurement | passes when |
|---|---|---|
| `albedo` | `bp(r)` at `r = expect_px / 2`, subject mask vs background mask | subject ≥ 1.5 × background |
| `silhouette` | degree-2 polynomial fit to the Z-pass silhouette over each 100 px run | RMS residual ≥ `0.25 × expect_px` somewhere |
| `shadow` | connected dark region in `L_direct` | extent ≥ `0.5 × expect_px` |
| `specular` | pixels above `3 × median(L)` | count > 0 |

**Three-way verdict, and the third way is the important one:**

- `expect_px < 2` → **REFUSE, naming the feature.** The claim cannot reach film at
  this distance. Build it larger or delete the claim. This is not a pass and it is
  not a failure of the object — it is a failure of the *declaration*, and it makes
  the builder confront its own arithmetic before it renders.
- `expect_px ≥ 2` and no signal → **FAIL.** This is the wave-1 bug, exactly.
- signal found → pass.

**Caught defects:**

| item | claim | `expect_px` | measured | verdict |
|---|---|---:|---|---|
| `marshal_post_deck` | ~90 screws/ply floor, 25 mm nail head @ 622 px/m | **15** | *"not one fixing is visible anywhere on the deck"* | FAIL |
| `terrain_ground` | 46 mm rut, 85 mm chevron tread | **180** | *"brown stripes with no depth"*; rut floor **8 % BRIGHTER** than adjacent turf (0.281 vs 0.259); 77 mm lip should throw ~85 px of black, measured **3–6 px** | FAIL |
| `crew_fireproof_overall` | `LAMBDA_FLEX` 68 mm fold language | **25.4** | trouser silhouette fits a quadratic taper to **0.61 px RMS (1.6 mm)**; required 0.25 × 25.4 = **6.4 px** | FAIL by 10× |
| `armco_w_beam` | zinc spangle, two-scale 5–40 mm | **7–57** | fine octave **entirely absent**; cells measure 42–84 mm | FAIL |
| `forecourt_paving_bay` | p90 joint lip 2.86 mm | **28.4** | every joint a constant-width constant-value line | FAIL |
| `pont_girder` | 372 fillet weld runs, 595 bolt heads, 3,383 lines of oil-canning | — | *"produce zero pixels"*; *"not one of 595 bolt heads has a rust stain"* | FAIL |
| `armco_post` | 17×40 mm stadium slot at three rail heights | **24 × 57** | *"no slot, no bolt, no nut, no washer"*; 8 of 10 headline features under 25 px | FAIL |
| `asphalt_wearing_course` | bitumen meniscus 0.4 mm @ 2036.4 px/m | **0.81** | sub-pixel **by construction** | **REFUSE** — effort spent on a feature that mathematically cannot appear |

**Why this is the right replacement for the node count.** The gate's own author
declined to gate triangles-per-instance on the grounds that *"one invented number
for 435 item classes would be a guess wearing a measurement's clothes."* That
objection is correct and it is exactly why the amplitude ledger works: **the
threshold is not invented, it comes from the item's own declaration.** A trash can
and a human are each held to what they said they built. No per-class constant is
required anywhere in G4.

### 2.6 G5 — subject coverage, and the vacuous-frame refusal

From the index pass, compute the fraction of the macro occupied by the item, by
stand-ins, and by background. **Refuse below 25 % subject for a hero.**

Caught: `tyre_blanket` subject = **0.6 % of pixels** (~230×230 of 3840×2160);
`kerb_precast_unit` **~50 % stand-ins**; `heras_fence_panel` **~60 % proxy ground
and empty sky**; `armco_w_beam` **~35 % sky + ~30 % featureless ground** with only
the leftmost ~600 px at the manifest's 2.6 m; `pont_girder`'s `CTX_Deck` a
featureless beige box at **~25 % of frame**; `marshal_post_deck`, where ~⅓ of
frame mass is the builder's own `CTX_` column stub — **excluded from the gate by
the `--prefix` argument.**

This is R2-018 in image form: a frame that mostly does not contain the subject
cannot evaluate the subject, and unproven is not a pass. It also closes the
`--prefix` escape hatch — whatever the prefix excludes still occupies pixels, and
G5 counts pixels.

### 2.7 G6 — uniform softness, with a real background mask

`tools/sharpness_probe.py` already encodes the right idea and already carries the
`armco_w_beam` numbers in its docstring (sky 1.543 / steel 1.775 = **0.87**, where
its own thresholds put "sharp" at ≤ 0.30). Its weakness is the same positional
assumption as §2.3: it slices fixed horizontal bands.

Rebuild it on the Z-pass background mask —
`ratio = meanLaplacian(background) / meanLaplacian(subject)`, require **≤ 0.30**.
My positional reproduction returns > 1.0 for 12 of 28 macros, which is itself the
evidence that fixed bands are unusable: those numbers are comparing ground
against ground. **The ratio is only meaningful with an identified background,
which is why the Z pass is not optional.**

And run the pair with the denoiser ON and OFF, per the tool's own DISAMBIGUATION
section: ratio drops with it off ⇒ OPENIMAGEDENOISE is eating detail; ratio stays
near 1 in both ⇒ it is an amplitude problem in the asset. Wave 1 could not
separate these from a single frame, and **every wave-1 macro was rendered with
the denoiser on.** Settle it once, globally, before wave 2 — it costs two renders.

### 2.8 G7 — the gate's own regression suite *(no new gate ships without this)*

`DEFECT-LOG-R2.md` states the lesson outright:

> *"the only thing that has reliably worked is running the check against an
> artefact already known to be bad and confirming it fails."*

So: **before the new gate is used on anything, run it against the 15 peeped
wave-1 macros. It must REJECT all 15.** If it accepts even one, it is not ready.
Wave 1's failure is not a sunk cost — it is a labelled test set, the only one this
project has, and it is worth more than the assets it produced.

Add the mirror test: hand-rework **one** item to genuine SHIP (§5 nominates
`asphalt_wearing_course`) and confirm the gate ACCEPTS it. A gate that rejects
everything is as useless as one that accepts everything; you need one of each to
know it discriminates.

Cost: one afternoon. This is what stops defect number seven.

---

## 3. BATCHING — one agent, N items, without "one tree spammed 100 times"

### 3.1 The rule

**Batch CONTEXT. Never batch GEOMETRY.**

| shared across a batch | never shared |
|---|---|
| the test scene, ground plane, sun rig | mesh datablocks |
| the macro camera and the gate invocation | per-item `variation_axes` satisfaction |
| material *authoring functions* (parameterised) | the amplitude ledger — one per item id |
| the module scaffold | the `per_instance_variation` measurement |

### 3.2 Admission test — all four must hold

1. **Same `zone`, same `nearest_camera_m`, same `lens_at_closest_mm`.** One camera
   at the correct optics judges all members. This is not restrictive: **262 of 435
   items** sit in a cluster of ≥ 3 sharing zone and exact distance, and only **73
   distinct distances exist across all 435**, ten of which carry 200 items.
2. **Members are parts of one physical assembly, or one material family.**
   Parts-of-one-assembly is the strongest case and it *improves* quality:
   `pont_girder`'s reviewer concluded *"a well-built object photographed badly"*
   precisely because it was shot in isolation, and `team_truck_trailer`'s tyre came
   back *"pale tan, ~0.35 albedo, lighter than the apron"* because nobody was
   looking at the vehicle as a vehicle.
3. **No joint evaluation of variation.** Each item id is still gated separately for
   `per_instance_variation`.
4. **Batch size ≤ 8.** Above that, per-item attention falls below the wave-1
   baseline and the batch degrades into a checklist.

### 3.3 The red line, made mechanical

After every batch, run the two tools that already exist:

- `tools/mesh_reuse.py` — **zero mesh datablocks may have users spanning more than
  one item id.** The world-wide census these tools already produced is the
  precedent: 467 non-vegetation objects, 467 distinct meshes, **gini exactly
  0.000** across dressing, barriers, surface and architecture. Nothing is reused
  even twice. A batch that breaks that is rejected and its items are rebuilt
  singly.
- `tools/instance_variety.py` — per item id, `top_source_share` no worse than the
  same item would be required to hit alone.

That turns *"i dont want repeat stuff aka one tree spammed 100 times"* into a
number applied to the batching decision itself, rather than a hope.

### 3.4 Where batching is NOT safe

- **Same class, different distance.** `tree` spans 14.0–30.0 m across 11 items.
  Those are LOD tiers. Merging them is the fastest available route to the named
  failure. **If a candidate batch's `nearest_camera_m` values are not identical, it
  is not a batch.**
- **The crowd cluster** — 14 items at exactly 14.7 m in `zone: crowd`. On paper the
  best batch in the manifest; in practice the worst. `spectator_seated` alone
  declares 7,800 instances and measured **rot_sd yaw 3.99°**, four pose
  silhouettes tiling the entire stand, and *"two identical maroon X-pose figures
  adjacent at (2860–3200, 620–800)"* despite 400 distinct topologies. Population
  variety **is** the job there, and batching invites one body reused across
  `spectator_child`, `spectator_standing_in_row` and `spectator_seated_leaning`.
  **Crowd items stay singleton.**
- Anything whose `variation_axes` differ materially from its neighbours'.

### 3.5 The batches worth taking first

| batch | n | zone / distance | why it is one object |
|---|---:|---|---|
| marshal post | 17 | trackside @ **6.0 m** (19 of 20 marshal items are at exactly 6.0) | column, deck, handrail, roof, screen, sign, stair, telephone, water cooler, chair, broom, flag, flag rack, light panel, absorbent bin — **one post assembly, not seventeen items** |
| team transporter | 10–14 | paddock @ **8.0 m**, all wave 2 | tractor, trailer, light cluster, livery decal, mirror arm, mud flap, side skirt, tyre, wheel_steer, wheel_trailer — one vehicle |
| pit crew | 15 | pit_lane @ **10.0 m** | one crew; shared fireproof material, per-figure geometry |
| armco system | 6 | barriers @ **2.6 m**, all wave 1 | w_beam, post, splice_bolt, reflector, spacer_block, catch_fence_post — one barrier run |
| tv camera rig | 5 | trackside @ **12.0 m** | housing, mast, body, cable, platform — one rig |
| driver | 4–5 | people @ **3.0 m**, all wave 1 | figure, gloves, helmet, race suit — one person |
| heras fencing | 4 | transit_corridor @ **exactly 3.0 m** | panel, coupler, foot, banner scrim — one fence |
| asphalt surface | 5 | track_surface @ **1.1–1.5 m** | wearing course, crack seal, patch repair, transverse joint, tyre marble — one road |

Projected: ~55 batches covering 262 items (mean 4.76) + ~173 singletons =
**~228 build units**, rounded to **240** after the crowd and tree exclusions.

---

## 4. REMOTE EXECUTION — the minimum viable EXEC job type

### 4.1 The measurement that makes the case

The vast-5090 skill states, at `SKILL.md:183-190`:

> *"The rented EPYC is ~1.5× slower per core than the local i7-7700K, so remote
> assembly is worse on both axes. Assemble here, push the assembled `.blend`."*

That is a claim about the **latency of one build**. The question is the
**throughput of a wave**, and three measurements say it does not follow:

1. **The local box cannot hold the work.** 28 items produced **28 GB** of test
   blends (max 2.13 GB) on a box with **11.6 GB of RAM and 12.7 GB already in
   swap**. The remote box has **515 GB** — a 44× advantage. Per-core speed is
   irrelevant when the binding constraint is memory.
2. **The gate itself is a memory hog.** `item_gate.edge_stats_m` appends every
   edge length to a Python list: for `paddock_paving_bay` that is **33,078,173
   floats ≈ 1.06 GB**, which it then sorts — on top of the evaluated meshes.
   Across the 28 items, 356.9 M edges.
3. **Pushing assembled blends is where wave 1's time actually went.** For the 553
   broker jobs against item scenes: **7,687 s rendering, 40,737 s in-job wall
   clock — 81 % of it not rendering.** Median per-job overhead **37.4 s** against a
   median render of **9.2 s**; excluding the 20 worst jobs it is still **7.34 h
   over 513 jobs**. Uplink measures 4–5 MB/s, and `SCENE_CACHE_GB = 8.0` against
   28 GB of blends guarantees LRU thrash and re-uploads. Scaled to 435 items that
   is **~143 h of pure uplink**.

Building remotely deletes item 3 entirely: **the blend is born where the render
happens.** Only `gate.json` (~1 KB) and `macro.png` (~7.6 MB) come back, on the
*download* side, which is the fast half of an asymmetric line.

### 4.2 The A/B that settles it

Every module already has an argparse `main()` (measured: 28/28), so this needs no
new code:

| run | configuration | what it answers |
|---|---|---|
| **A1** | local, 1 at a time | per-item latency, local |
| **A4** | local, 4 at a time | items/hour, local — the current regime |
| **B1** | remote, 1 at a time | per-item latency, remote — *the skill's claim, on its own terms* |
| **B12** | remote, 12 at a time | items/hour, remote |

Sample: 8 wave-1 modules spanning the output range (`timing_stand` 49 MB →
`pont_deck_slab` 2.13 GB). Measure wall-clock for the whole batch, plus peak RSS.

**Decision rule, fixed in advance:** adopt remote exec iff
**`B12 items/h ≥ 2 × A4 items/h`.** Record A1 and B1 regardless, so the skill's
claim is confirmed or refuted on its own terms instead of argued about.

Predicted: `B1/A1 ≈ 1.5` (the skill is right about per-core) and
`B12/A4 ≈ 3–5` (its conclusion does not follow). If B12 fails the rule, remote
exec is dropped and the table's row 3 and 4 are forfeit — §6.

### 4.3 The design, minimal

**Do not put EXEC inside the render worker.** `server.py:17-21` states *"Never
thread… One render at a time is also correct on the GPU"* — that law is right for
GPU work, and routing builds through it would serialize every build behind every
render and hand a build process the ability to corrupt the warm scene.

Instead: **a second process on the same box.** `worker/exec_server.py`, port
8800, the same newline-JSON-over-TCP protocol and the same `ssh -L` tunnel.
It is launched exactly as the render worker is
(`broker/remote.py:1636-1660 worker_launch_cmd()`), i.e. as
`blender -b --factory-startup -P exec_server.py` — **because there is no
`python3` on the box** (the CUDA `base` image plus a 14-package apt list, none of
them Python). Running the supervisor under Blender's bundled CPython 3.13 needs
zero provisioning changes and it may `subprocess.Popen` freely. It spawns
`blender -b --factory-startup -P <entry>` children, up to `EXEC_SLOTS`.

The two workers do not contend: Cycles on the 5090 is GPU-bound and uses 1–2 host
threads; the exec children are CPU-bound.

**Schema — a new frozenset, not a widening of the existing one:**

```python
EXEC_REQUIRED = frozenset({
    "job_id",        # broker-minted; worker re-validates [A-Za-z0-9_-]{1,64}
    "bundle",        # digest16 of a pushed input bundle; must already exist
    "entry",         # path RELATIVE to bundle root
    "argv",          # list[str], passed after `--`; never a shell string
    "outputs",       # list[str] of relative paths to fetch; explicit, never glob-all
    "timeout_s",     # int; hard kill
    "blender_args",  # list[str], e.g. ["-b", "--factory-startup"]
    "cpu_slots",     # int; slots this job occupies
})
```

Enforced as the first three lines of `handle_exec()`, mirroring
`server.py:689-692` verbatim in shape:

```python
missing = EXEC_REQUIRED - spec.keys()
if missing:
    raise ValueError(f"incomplete exec spec, missing: {sorted(missing)}")
```

**No defaults anywhere.** The warm-worker model's rule — *"this server holds no
render policy"* — applies unchanged: an omitted field is rejected, never filled
in.

**Invariants, each preserved explicitly:**

| invariant | how EXEC honours it |
|---|---|
| broker mints job IDs (`db.py:223-236`) | unchanged; `spec["job_id"]` is overwritten broker-side and re-validated against `[A-Za-z0-9_-]{1,64}` worker-side |
| path traversal (`scenes.py:28-74`) | `entry` and every `outputs` element are `realpath`'d and required to resolve **inside** `/workspace/exec/<job_id>/bundle` and `/…/out` respectively — resolve first, then contain, exactly as scene paths do |
| 30-min heartbeat (`vastctl.py:88-96`, `HEARTBEAT_STALE_SEC=1800`) | untouched. `Broker.heartbeat_loop` (`app.py:1281-1316`) is its own daemon thread on a 60 s tick and never enters the dispatch path — that separation is already an incident fix. A 40-minute exec job cannot starve it |
| `MAX_INSTANCE_HOURS = 12.0` | `timeout_s ≤ 3600`, and an exec job killed by instance rotation is **requeued without spending an attempt**, reusing the rule already implemented for sequences at `app.py:723-746` |
| `~/opus5-car-render` and `~/f1-round2` read-only (`README.md:235-240`) | those paths **do not exist** on the remote box. The bundle is *copied* (not symlinked) into a per-job directory so a build writing beside its module cannot corrupt the shared cache. The broker fetches only declared outputs; **the local agent** writes them into the project |
| render worker stays strictly serial | different process, different port, untouched code |

**Bundle staging.** Add `remote.push_bundle(paths) -> digest16`, reusing the
content-addressed scene-cache pattern (`remote.py:640-672`): tar + `zstd -19`,
scp to `/workspace/bundles/<digest16>/`, write `.complete` **last**. The input set
for an item build is Python only — `world/*.py`, `world/items/*.py`, `tools/*.py`,
`docs/item_manifest.json` — measured at ~5 MB, under two seconds of uplink, and
cached across every job in a wave. **No `.blend` ever goes up.**

**Dispatch.** `Broker.next_job` already discriminates on `job["scene"]` and
branches on `job["seq"]`. EXEC adds `job["kind"] == "exec"` and — the one real
difference — **dispatches up to `EXEC_SLOTS` concurrently** while render jobs stay
one at a time. That needs a second dispatch thread, not a change to the existing
one; both respect `Fleet.ensure_ready`'s lock.

**Results.** `Broker.collect` (`app.py:543-603`) hard-wires PNG verification, so
EXEC needs a parallel `collect_exec` that checks **size + sha256 of each declared
output** and nothing else — no PNG structure, no `blank_gate`. `spec_hash` is
computed from `IMAGE_FIELDS` only (`seq.py:62-66`) and `app.py:1629-1634` already
tolerates a `None` hash, so exec jobs store `spec_hash = None` with no change.

**Sizing.** Start `EXEC_SLOTS = 12` (32 effective cores, leaving headroom for
Cycles host threads and scp), giving ~43 GB per slot against the 2.9 GB the local
box currently has *in total*. Raise it against measured throughput, not intuition.

Run the exec worker on the **same rented instance** as the renderer. Money is not
a constraint and the GPU is needed for the macros anyway; a second box is
provisioning work for no wall-clock gain.

---

## 5. PROMPT AND HARNESS EFFICIENCY

### 5.1 `world/itemkit.py` — stop re-typing 27 % of the output

Wave 1 wrote **102,069 lines** across 28 modules. **27,992 of them (27.4 %) are
scaffold that every agent re-implemented from scratch**, and only 21 functions
came out byte-identical across ≥ 5 modules. `contract_light` averages 51.7 lines
and is byte-identical in **3 of 19** modules that have it.

| category | lines re-typed | goes into `itemkit` |
|---|---:|---|
| scene scaffold (`build`, `purge`, `_coll`, `contract_light`, `add_camera`, `macro_rig`, `test_scene`, `interface_json`, `selftest`, `main`) | 13,640 | yes |
| mesh toolkit (`Acc`, `extrude`, `sweep`, `tube`, `box`, `bolt`, `icosphere`, `shade_by_angle`) | 4,133 | yes |
| shader-node helpers (`NT`, `_nd`, `_ramp`, `_noise`, `_vor`, `_mixc`, `_math`) | 2,346 | yes |
| noise/hash/math (`hash01`, `fbm1`, `vnoise*`, `clamp01`, `sstep`, `Rng`) | 1,442 | yes |
| **total** | **21,561** | |

Two of those functions do more than save typing:

- **`itemkit.contract_light()`** — one implementation, verified once against G3's
  sun-difference measurement, used by all 435. That is what makes
  `driver_figure`/`pont_deck_slab`'s missing sun structurally impossible rather
  than merely fixed.
- **`itemkit.macro_rig()`** — sets `resolution_x = 3840` with nothing for an agent
  to get wrong. 11 of 28 wave-1 macros were 1080p and **the harness itself asked
  for it** at line 107 of the workflow script.

### 5.2 One worked example beats any amount of prose

Wave 1 gave every agent 45 lines of `LAW` and **no example of a finished item**.
Rework **one** item by hand to genuine SHIP under the new gate, and ship it as the
reference build every agent reads first.

Nominate **`asphalt_wearing_course`**: it is the one item whose lighting was
independently confirmed correct by its own peep (R−B rising to **+0.0991** in the
top band, R/B 2.39; near-field sun/sky separation `p95/p20 = 10.37`, inside the
healthy 5–12× band). Its remaining defects are pure material/geometry amplitude —
exactly the class every other item shares — so fixing it teaches the right lesson
and nothing else.

### 5.3 Is build + peep the right unit? No.

**Two structural changes:**

1. **Decouple the peep from the build.** Wave 1 ran `pipeline(ITEMS, build, peep)`,
   so a build failure yields nothing at all — and **13 of 15 owed peeps died on
   transient API 500s** in exactly that shape. Make the peep a separate pass over
   whatever artefacts exist on disk.
2. **Peep per cluster, not per item.** In round 1 the peep's job was to find what
   the gate should have measured. Once G1–G6 measure it, the peep's job changes to
   **taste**, and taste is comparative: an agent shown six items from the same zone
   at the same distance can rank them and identify the one that does not belong,
   which a solo peep structurally cannot. **435 peeps → ~70 cluster peeps.**

This is not a reduction in scrutiny. Every item still gets a 4K macro at its own
distance and lens, still gets G1–G6 run against that image, and still gets human
eyes — now with siblings beside it for comparison.

---

## 6. THE CONCURRENCY CEILING — and my single highest-leverage recommendation

### 6.1 What the cap actually is *(verified in the binary)*

The brief's `min(16, cpu_cores − 2)` is real and I found it:

```js
function zWy(e){ return Math.min(16, Math.max(2, e - 2)) }
…
KWy = zWy(jSd.cpus().length)          // module-level constant, no env override
```

It sits inside the **workflow runtime**, immediately beside
`tengu_workflow_agent_cap_exceeded` and the workflow agent cap `WSd = 1000`. With
`nproc` = 6 it evaluates to **4**, and there is **no environment variable that
overrides it**.

But the **Agent tool** is a different code path:

```js
function gPu(){ return Z.CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS ?? gty }   // gty = 20
```

with the user-facing message *"Concurrent subagent limit reached… ask them to
increase `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`."*

**A main-thread orchestrator using the Agent tool gets 20 concurrent subagents.
The workflow runtime gets 4.** Wave 1 ran under the workflow runtime, which is
why it ran at 4.

Related limits found in the same place, both of which bite at 435 items:
`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` defaults to **200** (so the campaign must
be tranched or the variable raised), and a single workflow may make at most
**1,000** `agent()` calls (so the 1,740-agent baseline could not have run as one
workflow anyway).

### 6.2 The recommendation

> **Move the bpy build and gate work to the EPYC (§4), and only then orchestrate
> the campaign through the Agent tool at 16-way concurrency instead of the
> workflow runtime's 4.**

**These are one lever, not two.** Remote exec alone leaves you pinned at 4 by the
workflow cap. Agent-tool orchestration alone puts 16 concurrent bpy builds on a
6-core, 11.6 GB box that is *already* 12.7 GB into swap — the `cpu_cores − 2`
formula exists precisely because local agents are assumed CPU-bound, and it is
only safe to step around once they genuinely are not. Together they are the
4 → 16 step, which is **9.7 days → 2.4 days**, the largest single row in the
table.

### 6.3 What it costs if I am wrong

**Failure mode 1 — the agents are not as I/O-bound as I think.** If each agent
still does meaningful local work (reading blends back, running peep image
analysis), 16 of them will exhaust 11.6 GB and the box enters a swap death
spiral.
*Cost:* one lost session plus a hard reboot; the wave restarts from the artefact
checkpoint (§7), which is cheap **by design**.
*Mitigation:* ramp **4 → 8 → 12 → 16**, one tranche per step, aborting the ramp if
`MemAvailable` drops below 2 GB. This is a dial, not a switch, and it is the
reason to build the checkpoint before turning it.

**Failure mode 2 — losing the workflow runtime loses `pipeline()` caching**, which
is the thing that rescued two lost sessions (a usage cap and a batch of API 500s;
agents whose prompt+opts were unchanged replayed instantly). If the
artefact-checkpoint pre-flight has a hole, a cap event costs a full re-run of
everything in flight instead of a replay.
*Cost:* up to one tranche ≈ 16 items × 2.4 h = **38 agent-hours**.
*Mitigation:* the pre-flight is a filesystem test, not a cache — write it and
**test it against wave 1's existing 28 artefacts before relying on it. It must
skip all 28.**

**Failure mode 3 — quality.** No lever here touches the standard, but batching is
where quality could leak. The red line is mechanical and already tooled: zero mesh
datablocks shared across item ids within a batch (§3.3).
*Cost if breached:* rebuild the batch's items singly — the same work the plan was
avoiding, i.e. the downside is losing the saving, not shipping worse work.

**If the B12 A/B fails** (§4.2), rows 3 and 4 of the table are forfeit and the
plan lands at **~372 agents, 267 h ≈ 11 days**. That is still a 79 % cut in agents
and a 55 % cut in wall-clock, from rows 1, 2 and 5 alone — none of which depend on
any remote-execution work.

### 6.4 The second-highest-leverage item, for completeness

**G7: run the new gate against the 15 peeped wave-1 macros and require it to
reject all 15, before using it on anything.** It costs an afternoon and it is the
only thing standing between this plan and defect number seven. Every other number
in this document is downstream of the gate being real.

---

## 7. FAILURE ECONOMICS — making the harness cheap to resume

Two sessions were lost (a usage cap, a batch of API 500s). Both resumed from
cache. Four changes make that reliable rather than lucky:

1. **Cache-key stability is the entire resume story.** An agent replays instantly
   only if its prompt **and** opts are byte-identical. So a per-agent prompt must
   be a pure function of `(item id, wave, brief version)`. Anything variable goes
   in a **file the agent reads**, never in the prompt text.
   **Wave 1 violated this**: the peep prompt interpolates `${b.what_i_built}` and
   `${JSON.stringify(b.could_not_verify)}` — free text from the upstream agent. If
   a build agent re-runs and phrases anything differently, every downstream peep
   cache-misses.
   *Fix:* the build agent writes `render/items/<id>/claim.json`; the peep prompt
   names the **path**.

2. **Checkpoint the artefact, not the agent.** An item is done iff four files
   exist and the gate passes:
   `world/items/<id>.py`, `render/items/<id>/gate.json`,
   `render/items/<id>/macro.png`, `render/items/<id>/amplitudes.json`.
   A pre-flight reads the filesystem and spawns agents **only** for items whose
   artefacts are missing or stale against the module mtime. A resumed wave then
   costs only the missing items, regardless of cache state — and this is what
   makes §6.2's failure mode 1 cheap.

3. **Checkpoint inside the build.** A 2.1 GB blend that takes 40 minutes and dies
   at minute 39 currently loses everything. Every module already has an argparse
   `main()`; add `--stage {geo,mat,scene,gate}` so a failed run resumes from the
   last saved stage. This matters far more remotely, where
   `MAX_INSTANCE_HOURS = 12.0` rotates the box out from under a running job.

4. **Bound the blast radius.** Run waves in fixed tranches sized to finish inside
   a usage-cap window (≈ 16 items at 16-way concurrency ≈ 2.5 h), rather than
   launching 139 wave-2 agents at once. A cap then costs at most one tranche, and
   it composes with the 200-subagents-per-session limit found in §6.1.

---

## 8. ORDER OF WORK

| # | step | blocks | cost |
|---|---|---|---|
| 1 | **G7 harness first** — stand up the new gate's regression suite against the 15 peeped wave-1 macros | everything | ½ day |
| 2 | Settle the denoiser question globally: one item, denoiser ON vs OFF, G6 ratio on both | all material judgements | 2 renders |
| 3 | Implement G1 (frame assertion) and G5 (subject coverage) — both trivial, both catch measured wave-1 defects | — | ½ day |
| 4 | Implement G2/G3/G6 on Z + index + sun-difference passes; confirm all 15 reject | wave 2 | 1 day |
| 5 | Implement G4 amplitude ledger; confirm all 15 reject | wave 2 | 1 day |
| 6 | Hand-rework `asphalt_wearing_course` to SHIP; confirm the gate **accepts** it | the worked example | 1 day |
| 7 | Extract `world/itemkit.py` from the 28 existing modules | agent efficiency | 1 day |
| 8 | Run the §4.2 A/B; decide remote exec on the stated rule | rows 3–4 of the table | ½ day |
| 9 | If adopted: `exec_server.py` + `push_bundle` + exec dispatch thread | 16-way concurrency | 2 days |
| 10 | Artefact pre-flight; **verify it skips all 28 wave-1 items** | safe resume | ½ day |
| 11 | Ramp concurrency 4 → 8 → 12 → 16, one tranche per step, watching `MemAvailable` | — | inline |

Steps 1–7 are worth doing whether or not remote exec is adopted, and they are
what rows 1, 2 and 5 of the table rest on.

---

## 9. WHAT I COULD NOT VERIFY

Stated plainly, because an unverified claim reported as unverified is useful and
one reported as done is a defect with a delay fuse.

1. **Peak RSS of a full build + gate for a large item.** I measured only the
   smallest test blend: `timing_stand_test.blend` (49.5 MB) → **632.5 MB peak
   RSS** against a **283.4 MB** Blender baseline. I did not run a large one
   because the box had 1.77 GB available and a Blender was already holding 45 % of
   RAM. **"Four concurrent large builds exceed 11.6 GB" is an extrapolation, not a
   measurement.** Settle it with:
   `python3 -c "import subprocess,resource;subprocess.run([BLENDER,'-b',BLEND,'--factory-startup','-P','tools/item_gate.py','--','--item',ID,'--out','/dev/null']);print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024)"`
   on `pont_deck_slab` (2.13 GB).
2. **Actual `blender -b -P <module>.py` build time**, separated from agent
   thinking/writing time. No log records it. The §4.2 A/B produces it as a
   by-product; until then the 2.4 h/agent figure is a *total*, and the split
   between "agent writing Python" and "Blender executing it" is unknown. If most
   of the 2.4 h is the agent writing, remote exec's benefit is smaller than row 3
   claims and §5's `itemkit` benefit is larger.
3. **Whether the EPYC's per-core deficit is 1.5× for *this* workload.** The skill
   asserts it without citing a bpy benchmark; every number it does cite is a
   transfer number. B1/A1 settles it.
4. **The batch cost model** `2.4 × (0.45 + 0.55n)` is a stated assumption with no
   data behind it. One measured batch of 5 against 5 singletons from the same
   cluster settles it, and row 2 of the table moves accordingly.
5. **The 20 % round-2 rate** is an assumption. Check it on the first tranche: if
   the round-1 SHIP rate is below 60 %, the gate is not yet predicting the peep
   and **scaling is premature** — return to §2 rather than proceeding.
6. **The 13 wave-1 items never peeped** (`paddock_paving_bay`, `pit_wall_unit`,
   `timing_stand`, `catch_fence_post`, `mullion_intact`, `gravel_bed_surface`,
   `tyre_wall_tyre`, `driver_figure`, `grandstand_riser_unit`, `gantry_truss`,
   `hospitality_deck`, `showroom_facade_panel`, `pont_deck_slab`). Their defect
   profile is *assumed* to resemble the 15 that were. If it differs, G1–G6 may
   under-cover. Cheap partial check: G1 already flags 5 of these 13 as 1080p
   deliveries.
7. **Whether 16 concurrent Agent-tool subagents actually behave as modelled** on
   this box. Untested. §6.2's ramp is the test, and §6.3 is the cost of being
   wrong.
8. **The `sky/subject` and `bp` figures in §2.3 and §2.7** were computed by me with
   *positional* bands over the delivered macros, because no Z pass exists for
   wave 1. They are sufficient to show that positional bands are unusable and to
   rank the flattest items, but they are **not** the numbers the proposed gate
   would report. Those require the Z pass and a re-render.
