# Scope optimisation — cutting the agent count without cutting the frame

> Brief: minimise agent count **without lowering what the viewer actually sees**.
> Every claim below is either a measurement I ran (marked **MEASURED**), a stated
> model with its assumptions on the table (marked **MODELLED**), or a measurement
> I am recommending someone else run (marked **RECOMMENDED**). Nothing here is
> asserted from having read code — R2-017 and R2-018 are what happens when it is.

---

## 0. The headline, in one paragraph

The `hero` flag was assigned on `nearest_camera_m` alone, and `nearest_camera_m`
is the *minimum distance from the camera corridor to the object*. It contains no
information about whether the camera is **pointed** at the object at that moment,
how long it stays there, or how fast the object is sweeping across the frame. For
the 251 items the camera passes side-on, the moment of closest approach is the
moment the object is **abeam** — i.e. at 90° to the direction of travel, which for
a 35 mm lens is 63° outside the frame. The manifest is therefore quoting a screen
size at a moment the object is not on screen. Correcting for that alone, with no
other assumption, cuts the median abeam on-screen size from 373 px to 164 px and
leaves only 59 of 251 above 300 px. Add the 180° shutter the rig already sets and
the median resolvable size falls to 47 px. **343 heroes is not a measurement; it
is a distance field with a threshold on it.**

And underneath that: **the camera does not exist for 65.8 % of the film.** I
measured this on `world/camera_rig.blend` itself. There is no basis on which to
decide any item's fidelity until it does.

---

## 1. MEASURED — the camera rig has 24 keyframes for 2,978 frames

Run against the artefact, not the source
(`/opt/blender-5.2.0-linux-x64/blender -b world/camera_rig.blend -P …`):

```
scene frames                1 – 2978        camera "ONER"
distinct keyframes          24
  location   x/y/z          24 keys each
  rotation_quaternion       16 keys each   <- all of them in beat 1
  lens / fstop              24 keys
  focus_distance            16 keys
key frames                  1, 42, 84, 127, 169, 211, 253, 296, 338, 380, 422,
                            465, 507, 549, 591, 754,   2714, 2762, 2786, 2834,
                            2882, 2930, 2978, 3050
largest key gap             1960 frames  (754 -> 2714)  = 65.8 % of the film
  chord over that gap       123.23 m
  max deviation from chord  0.819 m      -> it is a straight line
  camera speed in the gap   min 0.486 / mean 1.509 / max 4.524 m/s
  orientation in the gap    FROZEN — no rotation key exists after frame 754
```

Cross-checked against `telemetry/telemetry.csv` with the beat sheet's own
world-time↔film-time map (which is internally consistent to 0.1 %: the four
transit legs sum to 8.91 s against the beats' 8.98 s, and the lap's 3,671.6 m
over 63.5 s against the spec's 3,675 m / 63.545 s):

```
frames of the gap in which the car is moving      1740
camera-to-car distance   min 3.8 m   median 612.5 m   max 962.4 m
frames with the car within 50 m                    131  ( 7.5 %)
frames with the car beyond 500 m                  1204  (69.2 %)
```

**Beats 2, 3, 4 and 5 — the launch, the wall breach, the transit and the entire
flying lap — have no camera.** The rig drifts 123 m in a straight line at walking
pace with a frozen orientation while the car covers 4,053 m at up to 92 m/s.

`camera_rig_continuity.json` reports `worst_position_jump_m: 4.0012`,
`worst_rotation_step_deg: 5.723`, and `STAGE RESULT: CAMERA_RIG_CONTINUOUS`. That
verdict is **true and correct** — a slow straight drift is perfectly continuous.
The gate measured continuity, which is what it claims to measure. What no gate
measures is *coverage*: whether the camera is anywhere near the film. This is not
a broken gate (R2-017/018's shape); it is an **absent** one, and it has the same
consequence — a green line in a log that a reader banks as "the camera is done".

### Why this is the first item in a scope document

`nearest_camera_m` for all 435 items was derived from a *reconstructed* 4,507-sample
corridor — assembled in a prior session from the beat-1 keys, the transit legs, the
Beat-5 vantage table in `circuit_spec.md` and the Beat-6 keys. That reconstruction
is a reasonable design intent. **It is not the camera.** It exists only as prose in
`docs/item_manifest.md` §1; there is no script, no sample file, and nothing in the
rig that agrees with it. Every fidelity decision for 435 items currently rests on a
number derived from an object that was never built and cannot be re-derived.

---

## 2. MEASURED — where the film's frames actually go, and which items compete for them

| beat | seconds | frames | % of film | items tagged | items **only** in this beat | items/frame |
|---|---:|---:|---:|---:|---:|---:|
| 1 assembly | 33.0 | 792 | 26.6 % | **12** | 0 | 0.015 |
| 2 launch | 3.0 | 72 | 2.4 % | 6 | 0 | 0.083 |
| 3 breach | 8.0 | 192 | 6.4 % | 44 | 2 | 0.229 |
| 4 transit | 5.6 | **134** | 4.5 % | **220** | **60** | **1.642** |
| 5 lap | 63.5 | 1524 | 51.2 % | 314 | 155 | 0.206 |
| 6 ending | 11.0 | 264 | 8.9 % | 69 | 10 | 0.261 |

Three facts fall straight out:

1. **Beat 1 is 26.6 % of the film and contains 12 of the 435 items.** The
   showroom assembly is the round-1 car, already built. The whole 435-item
   campaign exists to serve beats 3–6, which is 88.1 s.
2. **220 items are dressed for a 5.6-second transit, and 60 of them appear
   nowhere else.** At 58.5 m/s that beat covers 328 m of corridor. Sixty items
   exist to be glimpsed once, in 134 frames, from a car doing 210 km/h.
3. **155 items exist only for the lap**, where the camera covers 3,675 m in
   1,524 frames at a mean 57.8 m/s.

### MEASURED — camera speed per beat, from the project's own data

| beat | source | camera screen speed |
|---|---|---:|
| 1 | 16 beat-1 keys, 60.19 m of path over 31.4 s | **1.92 m/s** |
| 2 | launch leg, 10.0 m over 3.0 s of screen | 3.35 m/s |
| 3 | 36.0 m of world motion over 8.0 s of screen (time ramp to 20 %) | **4.50 m/s** |
| 4 | 327.7 m over 5.6 s | **58.51 m/s** |
| 5 | 3,671.6 m over 63.5 s | **57.82 m/s** |
| 6 | 8 beat-6 keys, 524.4 m over 14.0 s, decelerating to **0** for a 3 s hold | 37.45 m/s |

Beat 5's own vantage table decomposes further, and one line of it matters more
than the rest of the manifest put together:

```
chase T1–T3            s    0– 760  10.7 s   71.0 m/s
kerb-height hairpin    s  760–1160  10.6 s   STATIC CAMERA on the T4 inside kerb
rise + helicopter arc  s 1160–1910  14.6 s   51.4 m/s
dive to the sweeper    s 1910–2403   7.0 s   70.4 m/s
bridge + doppler hover s 2403–2700   4.4 s   67.5 m/s, then a 7.46 s HOVER
whip and catch         s 2700–3115   7.0 s   59.3 m/s
onboard follow         s 3115–3675   7.1 s   78.9 m/s
```

**The film has exactly four places where the camera is slow or still**: beat 1
(792 frames at 1.9 m/s, tracking), beat 3's slow-motion breach (192 frames at
4.5 m/s of screen motion), the T4 hairpin station (254 static frames at 21 mm),
the doppler hover (179 frames), and beat 6's crane-out ending in a 72-frame dead
hold. Everything else in the film is a pass at 130–280 km/h.

**Hero fidelity is earned in those five pockets and nowhere else.** That is the
whole scope argument, and it is a statement about the camera, not about taste.

---

## 3. MODELLED — real screen presence: what `onscreen_px_4k` is actually worth

`onscreen_px_4k = height_m × lens_mm × 3840 / (36 × nearest_camera_m)` is
arithmetically correct and physically misleading, for two independent reasons.

### 3a. The frustum correction (independent of any render setting)

For an item the camera **passes** rather than **approaches**, closest approach
happens abeam — bearing 90° from the direction of travel. The horizontal half-FOV
is `atan(18/lens)`: 27.2° at 35 mm, 40.6° at 21 mm, 17.2° at 58 mm. The item is
in frame only while its bearing is under that, i.e. only at distances of at least
`D / sin(θ_h)` — **2.19 × `nearest_camera_m` at 35 mm.**

```
peak IN-FRAME size = onscreen_px_4k × sin(θ_h)
```

MEASURED consequence over the 251 abeam items:

| | manifest | frustum-corrected |
|---|---:|---:|
| median peak px | 373 | **164** |
| items under 150 px | 56 | **116** |
| items at or above 300 px | 149 | **59** |

This correction assumes nothing about shutters, denoisers or renderers. It is
geometry. It applies to every item the camera goes past instead of towards.

### 3b. The motion correction (assumes the rig's own 180° shutter)

`anim/build_camera_rig.py` sets `shutter = 0.5` (180°) and scales it with world
time. For an item at bearing β and perpendicular standoff D, past a camera
translating at v, the image sweeps at `v·sin²β / D` rad/s. In 4K pixels, over one
1/48 s exposure:

```
smear_px = (3840 · lens/36) · v · sin²β / (48 · D)
```

Worked example, checked two ways: an item 15 m abeam, 35 mm, 57.8 m/s. Angular
rate 3.85 rad/s = 221 °/s; in 1/48 s that is 4.6° of arc; the 35 mm frame is 54.4°
across 3840 px = 70.6 px/deg, so 325 px of smear. The closed form gives 300 px at
the same numbers. **The object smears by roughly its own height in a single
exposure.**

Solving for the bearing at which smear equals **6 px — `tools/item_gate.py`'s own
hero resolve threshold, not a number I invented** — gives each item's *sharp
size*: how big it is at the last moment it is still resolvable.

MEASURED over the 251 abeam items (using the *slowest* beat each item appears in,
i.e. deliberately generous):

```
manifest px is overstated by:  median 8.3x   (p10 5.5x, p90 14.6x)
sharp size    p25  20 px   p50  47 px   p75  75 px   p90 156 px
under  60 px  153/251   of which 116 are currently flagged hero
under 150 px  224/251   of which 166 are currently flagged hero
```

For the 33 ground-plane items (track surface, kerb faces, runoff), the geometry
is different — the camera flies *over* them, so smear is `f·h·v/(48·x²)` and the
road is sharp only where it is far, and far means foreshortened to nothing:

```
sharp size    p25 0.2 px   p50 0.5 px   p75 2.0 px   p90 5.0 px    (33/33 under 60 px)
```

`asphalt_crack_seal`, `asphalt_paver_mat_joint`, `timing_loop_sawcut`,
`kerb_bedding_joint`, `tyre_marble`, `rubber_line_deposit` — **none of these has a
resolvable moment anywhere in the lap.** They are real and they must exist as
tone; they do not merit a dedicated agent plus an adversarial review.

### 3c. MEASURED — the conclusion survives switching motion blur off

Sensitivity of the 251 abeam items to both assumptions:

| shutter | gate px | sharp < 60 px | sharp < 150 px | sharp ≥ 300 px | median sharp |
|---|---:|---:|---:|---:|---:|
| **180° (the rig's setting)** | 6 | 153 | 224 | 10 | 47 px |
| 180° | 12 | 119 | 215 | 14 | 67 px |
| 90° | 6 | 119 | 215 | 14 | 67 px |
| 45° | 12 | 67 | 136 | 36 | 134 px |
| **no motion blur at all** | — | — | **116** | **59** | **164 px** |

Even with the shutter closed to a quarter of the rig's setting *and* the
resolve threshold doubled, 136 of 251 abeam items stay under 150 px. Even with
motion blur removed entirely, the frustum correction alone leaves 116 under
150 px and only 59 at or above 300 px. **There is no setting of the render that
makes 343 heroes correct.**

### Where this model is weak, stated plainly

* It assumes the camera looks roughly along its direction of travel during the
  fast phases. True for the chase, the transit and the onboard follow; false for
  the helicopter arc (looking down and inward) and during the whip. Items under
  the arc will be *further* than modelled and are being treated generously here.
* Pocket membership (which items are in beat 1 / beat 3 / T4 / hover / beat 6) is
  a **keyword proxy** over `notes` and the `beats` array. It over-includes
  (anything mentioning "T4" is tagged static) and under-includes (`armco_post`
  lands outside the hover pocket while `armco_w_beam` — the same barrier — lands
  inside it). It is a triage heuristic, not a measurement.
* It uses `nearest_camera_m`, which as §1 establishes was derived from a corridor
  that no longer corresponds to anything in the repository.

**All three weaknesses are removed by the same single measurement, in §9.**

---

## 4. What the camera never sees — what I can and cannot say

I **cannot** answer this from the manifest. `docs/item_manifest.json` carries no
world positions: 435 records × 19 fields, none of them a coordinate. There is no
mapping from a manifest `id` to the objects in `render/world/assembly/assembly.blend`
(28,686 objects across five owners). Answering "never in frustum" requires
projecting real geometry against a real camera, and neither exists in usable form
today. Anyone who tells you a number here without doing that is guessing.

What the geometry does already say, from `docs/item_manifest.md` §1 and the vantage
table, and what the measurement should be expected to confirm:

* **T12, T13 and T14 are never approached.** The whip-and-catch cuts a 485 m
  straight chord *inside* the loop the car drives around, so those corners are
  only seen at 60–115 m from a camera doing 40–70 m/s. Everything dressed on the
  inside of that loop is behind the camera for the whole take.
* **The stands are seen from above.** Beat 6 clears the grandstand roof by 13.8 m.
  Seat undersides, seat backs below shoulder height, row-end brackets, the
  concourse and the vomitories are permanently occluded by the 82 %-occupancy
  crowd sitting on them. The manifest already downgraded `grandstand_seat` for
  exactly this reason; the same logic has not been applied to
  `grandstand_seat_bracket`, `grandstand_row_letter`, `grandstand_nosing`,
  `grandstand_gutter` or `grandstand_concourse`.
* **1,712,075 instances** are carried by the 186 items whose modelled sharp size
  never exceeds 60 px. Whatever fraction of those is also never in frustum is
  pure recovered budget.

**RECOMMENDED, §9:** an object-index pass over the finished take answers this
exactly and without argument — any object with zero ID-pass pixels across all
2,978 frames is *provably* never seen, and that is a fact, not a model.

---

## 5. Waves 4–6 — the premise is inverted

The brief asks for a bulk treatment of waves 5–6. MEASURED from the manifest:

| wave | items | hero | distance | on-screen px |
|---|---:|---:|---|---|
| 1 | **139** | 139 | ≤ 4 m or ≥4 dependants | — |
| 2 | **124** | 124 | ≤ 10 m or ≥2 dependants | — |
| 3 | 74 | 74 | ≤ 15 m | — |
| 4 | 81 | 13 | 15.4 – 25.0 m | 20 – 2160 |
| 5 | **14** | 0 | 26.0 – 45.0 m | 132 – 2160 |
| 6 | **3** | 1 | 55.0 – 60.0 m | 355 – 475 |

**Waves 5 and 6 are 17 items in total.** They are not a bulk problem; they are a
rounding error, and the manifest's "silhouette and mass only" rule already
disposes of them. One agent covers all 17. Wave 4's 81 items are already 84 %
non-hero. **The bulk is waves 1–2: 263 items, all 263 flagged hero.**

Waves 5–6 also demonstrate why distance is the wrong axis. `tree_scots_pine` at
30 m is 2160 px — it overfills the frame vertically — and it is *not* a hero.
`pit_building_balustrade` at 31 m is 132 px and also not a hero. The wave number
groups two objects that differ by 16× in screen presence, while separating the
Scots pine from `tree_london_plane` (14 m, wave 3, hero) which is the same species
class of object. **Waves are a build-order device. They are not a fidelity
classifier and should not be used as one.**

---

## 6. Dependency collapse — MEASURED

`depends_on` is a real graph and it is already shaped for collapse.

```
435 items, 280 with at least one dependency, 155 roots
connected components of depends_on:  136   (72 singletons, 64 of size >= 2)
largest components:  38 (crew_*)  23 (grass/ga/terrain)  22 (marshal_*)
                     19 (grandstand/crowd/spectator)  14 (armco_*)
                     14 (catch_fence_*)  14 (truck_*)  13 (asphalt_*)
grouping by (module, first name token):  177 groups, 107 of them singletons
```

The top 20 parents by dependant count are **exactly the wave-1 modules already
built**: `crew_fireproof_overall` (18 children), `terrain_ground` (14),
`asphalt_wearing_course` (8), `spectator_seated` (8), `armco_w_beam` (7),
`marshal_post_column`/`_deck` (6 each), `kerb_precast_unit`, `paddock_paving_bay`,
`heras_fence_panel`, `pit_wall_unit`, `team_truck_trailer`, `timing_stand`,
`tyre_blanket` (5 each). **The parents whose agents already exist own 135 of the
435 items as direct children.**

The children are, overwhelmingly, *the same object at a different scale*:
`armco_splice_bolt`, `armco_reflector`, `armco_spacer_block`, `armco_terminal`
are four agent-tasks for parts that live on the beam `armco_w_beam` already emits,
sharing its material, its coating history and its instancing. Emitting them from
the parent's module is not a compromise — it is the only way they can share a
weathering history at all. Four separate agents that cannot see each other's work
will produce four unrelated rust treatments bolted to one barrier.

**Proposed collapse unit: `(module, name-family)`.** It respects module ownership
(the code has to live somewhere), it respects the dependency graph (children of a
parent share its family), and it is mechanical rather than judgemental.

```
bucket A  126 items ->  55 groups     bucket C   27 items ->  11 groups
bucket B   25 items ->  14 groups     bucket D  257 items -> 127 groups
```

---

## 7. What is already good enough — the 28 built modules

Two separate findings, both of which say **stop reworking and start re-judging**.

### 7a. MEASURED — nine of the 28 were peeped at a distance the camera never occupies

The peeps were run at `nearest_camera_m` on the item's own lens. For the abeam
items that is a view the camera never has. Comparing the peep distance with the
closest **in-frame** distance and the closest **sharp** distance:

| item | peeped at | closest in-frame | closest sharp | peep px | sharp px |
|---|---:|---:|---:|---:|---:|
| `crew_fireproof_overall` | 10.0 m | 21.9 m | **86.6 m** | 653 | **75** |
| `timing_stand` | 10.0 m | 21.9 m | 86.6 m | 1195 | 138 |
| `marshal_post_column` | 6.0 m | 13.1 m | 67.1 m | 1742 | 156 |
| `marshal_post_deck` | 6.0 m | 13.1 m | 67.1 m | 560 | 50 |
| `pit_wall_unit` | 6.2 m | 13.6 m | 68.2 m | 723 | 66 |
| `armco_post` | 2.6 m | 5.7 m | 44.1 m | 2154 | 127 |
| `tyre_blanket` | 13.0 m | 28.4 m | 98.7 m | 195 | 26 |
| `hospitality_deck` | 22.0 m | 48.1 m | 129.2 m | 102 | 17 |

`crew_fireproof_overall` is the clean case. It was condemned for having, across
110 instances, "zero knee dirt, shin abrasion, rubber transfer, grease
handprints, sweat darkening or repairs", and for a trouser silhouette that fits a
quadratic taper to 0.61 px RMS (1.6 mm) where real Nomex should perturb it
5–10 mm. Every one of those observations is correct and every one of them is
**sub-pixel at 75 px**, which is the largest the garment is ever both in frame and
resolvable. A 1.6 mm silhouette error at 75 px total figure height is 0.02 px.

The reviewer was not wrong about the render. **The render was of a view that does
not occur in the film.**

### 7b. All 15 REWORK verdicts were issued under two unclosed systemic defects

`docs/WAVE1-PEEP-SYNTHESIS.md` states this itself, and I am only quantifying the
consequence:

* **SYSTEMIC 1 — no sun in the item test scenes.** R−B negative in every
  luminance band and increasingly negative toward the highlights, on two
  unrelated scenes. "Every material judged in a wave-1 test scene was judged
  under the wrong light… Nothing about material tuning should be actioned until
  this is closed."
* **SYSTEMIC 2 — the whole frame is uniformly soft.** The sky carried 87 % of the
  detail energy of in-focus steel; near/mid/far identical within 4 %, so it is not
  depth of field. `tools/sharpness_probe.py` was written at 21:25 today to
  diagnose it. **It is not yet closed.**

**Zero of the 15 REWORK verdicts is currently actionable.** Acting on them now
costs 15 rebuilds plus 15 re-peeps and may be wasted in full. Re-judging them
after the render path is fixed costs 15 re-peeps and nothing else.

### 7c. Recommendation

* Freeze all rework on the 28 built modules.
* Fix the sun and the softness (2 agents, §9).
* Re-judge the 15 in a **frame** peep at the real camera, not an item peep at
  `nearest_camera_m`.
* **Predicted outcome, stated so it can be checked:** of the 9 bucket-D items
  above, at least 6 will be accepted with no geometry change once judged at their
  true screen presence under correct light. If fewer than 4 are accepted, this
  section is wrong and item-level peeps should be reinstated.

---

## 8. THE TABLE — current agent count vs proposed

Buckets, from §3. A = seen from a slow or static camera pocket; B = approached
head-on (bridges, portals, the transit corridor, the showroom); C = passed at
speed but still resolves ≥150 px; D = never resolves surface detail.

| # | Category | Items | Current agents/round | Proposed agents/round | Reasoning |
|---|---|---:|---:|---:|---|
| 0a | **Camera, beats 2–5** | — | 0 (deferred) | **1** | MEASURED §1: 1,960 frames have no camera. Nothing downstream can be decided without it. Not a saving — a prerequisite that was missing from the ledger. |
| 0b | **Render-path fix** (sun; uniform softness) | — | 0 | **2** | §7b. Until closed, every appearance verdict is void, so every peep agent is spend with no product. |
| 0c | **Screen-presence measurement** | — | 0 | **1** | §9. Replaces the model in §3 with a measurement and re-derives `hero` for all 435 items at once. |
| 1 | **Hero build** — buckets A+B | 151 | 151 | **69** | 55 + 14 `(module, family)` groups (§6). One agent per family, emitting the family. The parent already owns the children's material history. |
| 2 | **Reads-at-speed** — bucket C | 27 | 27 | **11** | ≥150 px sharp: silhouette, mass, correct value, genuine per-instance variation. No macro history. |
| 3 | **Texture-and-mass** — bucket D | 257 | 257 | **16** | 13 `(module, zone)` cells of ≥6 items plus 13 small cells rolled into their owner. These items **exist already** — the class-level placement systems built them. What they need is a silhouette/value/variation pass, not 257 new modules. |
| 4 | **Adversarial review** | — | 435 | **60** | 40 frame-peeps + 20 macro-peeps. See below. |
| | **per round** | 435 | **870** | **160** | |
| | **× 2 rounds** (brief's assumption) | | **1,740** | **~316** | round 2 rebuilds 96 + re-reviews 60; the Tier-0 four do not repeat |

**1,740 → ~316 agents. A 5.5× cut.** At the brief's own 4-concurrent / 1.3 h
figures that is ~103 agent-hours of wall clock against ~566, plus roughly a day of
serial Tier-0 work that must precede everything. Concurrency and batching are the
other agent's lane; I have only changed *how many* agents there are.

### Row 4 in detail — why review collapses 435 → 60

The current design reviews **one item, alone, at `nearest_camera_m`, in a test
scene**. Three things are wrong with that as a unit of review, and all three are
scope questions rather than efficiency ones:

1. **The distance is wrong** (§7a) — measured, on 8 of the 9 items I could check.
2. **The context is wrong.** The user's rejections were of *frames*: "okay kinda
   cute", "half assed… the grass is blurry", "the people in stands honestly
   fucking shit". Not one was of an item in isolation. A defect that only appears
   when 40 items sit next to each other under one sun — which is what "okay kinda
   cute" describes — is invisible to 435 solo reviews and obvious in one frame.
3. **The lighting is wrong** (§7b), and the item test scene is precisely where it
   is wrong.

**Proposed unit of review: the frame, at the real camera.** The film has ~12
distinct vantage regimes (beat 1 presentation; beat 2; beat 3 slow-mo breach;
beat 4 transit; beat 5's seven phases; beat 6 crane and hold). Three frames each
= 36; call it **40 frame-peeps**. Each covers dozens of items at the exact
distance, lens, shutter, motion blur and light they will ship with.

Retain **20 per-item macro peeps** — and only for items that genuinely receive
macro scrutiny in the film: `kerb_hero_t4` (a static 21 mm lens sitting *on* it for
254 frames), `driver_figure` / `driver_helmet` / `driver_race_suit` /
`driver_gloves`, the showroom glass and mullion family through the slow-motion
breach, `grass_clump_fescue` under the doppler hover, and the beat-6 hold
subjects. These are the items where the manifest's own distance figure is real.

---

## 9. RECOMMENDED — the measurements to run, with method and cost

### M1. Author the beats 2–5 camera. *(prerequisite, 1 agent)*

Extend `docs/beat_sheet.json` with camera keys for beats 2–5 and `build_camera_rig.py`
to consume them, including `look_at` targets so orientation is keyed past frame 754.
The sources already exist and agree with each other: the transit legs in
`circuit_spec.json`, the Beat-5 vantage table, the doppler station at
`(-578.82, -47.47, 4.802)`, and `telemetry.csv` for the car to track.

**Add a coverage gate to the rig build**, in the shape R2-018 settled: refuse to
report success if any span longer than N frames carries no key, or if the tracked
subject leaves the frustum for longer than a stated tolerance. Print the numbers.
The existing continuity check is correct and should stay; it simply does not
answer this question, and no gate currently does.

*Cost: 1 agent. Serial — everything else waits on it.*

### M2. The screen-presence pass. *(1 agent; the core recommendation)*

Once M1 exists, render the whole take against `render/world/assembly/assembly.blend`
with **only geometric passes**:

```
engine        CYCLES,  samples = 1,  denoise OFF,  film filter width 0.01
passes        IndexOB (use_pass_object_index)  +  Vector (use_pass_vector)
resolution    960 x 540   (1/16 the pixels of 4K; multiply areas by 16)
frames        1 – 2978, step 1   (step 2 acceptable; do NOT step 4 — the whip
              and the bridge threshold move a full frame-width in ~6 frames)
setup         assign object.pass_index = 1..N over all 28,686 objects, dumped
              to a JSON sidecar mapping index -> object name -> owning module
```

Then per frame, `np.bincount` the IndexOB buffer → **pixels per object per frame,
with occlusion and frustum both handled exactly by the renderer** — no model, no
assumption. The Vector pass gives **per-pixel screen-space motion in pixels**, so
for each object and frame you get its *actual* smear, replacing every assumption
in §3b. `pass_index` is written as float32, which represents integers up to 2²⁴
exactly, so 28,686 indices are safe.

Derived per object, and this is the field that should replace `hero`:

```
frames_visible          count of frames with pixel_count > 0
peak_px_4k              16 x max pixel count over the take
peak_SHARP_px_4k        16 x max pixel count restricted to frames whose median
                        |Vector| over that object's pixels is <= 6 px
first/last frame seen, and the frame of peak sharp presence
```

**Why this is the right measurement and not another gate that can lie:** it
reports a physical quantity (pixels) measured on the artefact (the render), it
cannot pass vacuously (an object with no pixels reports zero, which is an answer,
not a pass), and it is falsifiable by eye against the frame it names.

**Cost.** Both passes are geometric — no light sampling, no shading. The dominant
costs are scene load and BVH build on a 4.2 GB / ~50 M-triangle scene, paid once.
Estimate 15–45 min of setup and 0.3–2 s/frame → **1–4 GPU-hours** for the full
take. **This must run on the rented 5090, not locally: this box has 11 GB of RAM
(MEASURED, `free -g`) and cannot load the assembly without thrashing 44 GB of
swap.** Budget one agent and one working session.

**Risk, stated:** if the scene will not fit in 32 GB of VRAM, fall back to CPU
(slower but the passes are cheap), or split the render by collection and union the
per-object results — the ID pass is per-object, so splitting is lossless for
frustum and area but **loses cross-collection occlusion**, which must then be
recovered with a combined depth-only pass. Do not silently accept the split
result as if it included occlusion.

### M3. Cheap fallback if M2 will not fit *(same agent, ~1 hour)*

One Blender load to dump every object's world-space bounding box to JSON, then
project all 8 corners against the per-frame camera matrix for all 2,978 frames in
pure NumPy — 28,686 × 2,978 × 8 = 683 M point transforms, seconds of compute.
Yields frustum membership, nearest distance and projected screen area exactly;
**misses occlusion only**. Because ignoring occlusion can only *overestimate*
visibility, any demotion made on M3's output is conservative and safe. M3 alone
decides "never seen" and "never larger than 40 px"; M2 is needed only to demote
further.

### M4. Re-derive the manifest *(no agent — a script)*

Rewrite `hero` from M2/M3 output. Proposed rule, with the thresholds named so
they can be argued with:

```
HERO      peak_SHARP_px_4k >= 300  AND  frames_visible >= 24   (1.0 s)
MID       peak_SHARP_px_4k >= 150
BULK      everything else — existence, silhouette, value, variation
NEVER     frames_visible == 0 -> delete from the campaign entirely
```

**Prediction, so this document can be wrong in public:** M2 will return **between
110 and 170 HERO items**, against the manifest's 343. My model puts A+B at 151.
If M2 returns more than 220, §3's geometry is wrong and this plan should be
rejected wholesale.

---

## 10. The single highest-leverage recommendation, and what it costs if I am wrong

> **Author the beats 2–5 camera (M1), then re-derive `hero` from the measured
> screen-presence pass (M2). Dispatch no further item agent until both exist.**

Four agents, roughly two days of mostly serial work, standing in front of a
campaign currently scoped at 1,740 agents and 24 days.

**Why it is the highest leverage.** Every one of the other cuts in this document
— the family collapse, the frame-peep, the bucket-D bulk pass, the freeze on
rework — is *contingent on which items are heroes*. M2 settles that question for
all 435 items simultaneously, with a measurement rather than an argument. And M1
is not optional under any plan: the deliverable is a single continuous 4K take,
and 65.8 % of it currently has no camera. It is on the critical path whether or
not anyone agrees with a word of §3.

**What it costs if I am wrong.**

* *If the authored camera lingers far more than the vantage table implies* —
  slower passes, more static stations — more items are heroes than I predict.
  The demotions in Tiers 2 and 3 have to be reversed. Worst case, every one of the
  257 bucket-D items is re-promoted to a dedicated agent and we land back at the
  original 1,740 **plus the four Tier-0 agents: an overrun of 0.2 %.** The
  asymmetry is the entire argument. The downside is four agents; the upside is
  ~1,400.
* *And it is caught before it is paid for.* M2 runs before any Tier-1 agent is
  dispatched. Being wrong shows up as a number in the measurement, not as a
  rejected film two weeks later.
* *If the 180° shutter reasoning is wrong* — the user shortens the shutter, or
  wants blur removed — §3c has the sensitivity MEASURED: at a 45° shutter with a
  doubled threshold, 136 of 251 abeam items are still under 150 px, and **with
  motion blur off entirely the frustum correction alone still leaves 116 under
  150 px and only 59 at or above 300 px.** The recommendation does not depend on
  the shutter.
* *The genuine risk this plan carries* is the family collapse in Tier 1, not the
  demotions. If one agent owning `(architecture, grandstand)` — 20 items — does a
  thinner job than 20 agents would have, that is a real quality loss in the one
  place the film ends. Mitigation: the frame-peep for beat 6's hold is one of the
  20 retained macro peeps, and the grandstand is under it. If that peep fails
  twice, split that family and only that family.

---

## 11. What I could not verify

Stated plainly, because an unverified claim reported as unverified is useful and
one reported as done is a defect with a delay fuse.

1. **No item has a world position anywhere in the repository.** The manifest has
   435 records × 19 fields and not one coordinate. Every question of the form
   "is this item ever in frame" is therefore unanswerable from the manifest, by
   me or by anyone. §4 is a method, not an answer.
2. **`nearest_camera_m` is unreproducible.** The 4,507-sample corridor it derives
   from exists only as prose in `docs/item_manifest.md` §1 — no script, no sample
   file, nothing in the rig that matches. I could not check a single one of the
   435 values. Every fidelity decision on this project currently rests on it.
3. **I did not load `assembly.blend`.** 4.2 GB and 28,686 objects against 11 GB of
   RAM (MEASURED). Anything I could have reported from a swap-thrashed partial
   load would have been worse than reporting nothing. M2/M3 must run on the 5090.
4. **Pocket membership is a keyword proxy**, not a measurement — §3's caveats.
   The A/B/C/D buckets are triage, and 19 of 71 name-families straddle a bucket
   boundary. The bucket counts in §8 are good to perhaps ±20 items, and M2
   replaces them outright.
5. **I did not verify the 1.3 h/agent or 4-concurrent figures** — taken from the
   brief as given, and they are the other agent's lane.
6. **Only 8 of the 15 peeped items could be checked** against their true screen
   presence; the other 7 fall in pockets where my model does not produce a sharp
   distance. §7a's conclusion is measured on 8, extrapolated to 15.
7. **Possible double-correction in the beat-3 motion blur, unverified and out of
   scope.** `build_camera_rig.py` sets `motion_blur_shutter = 0.5 × world_time_scale`.
   If Blender's time remap already slows object motion per frame, scaling the
   shutter again would make the slow-motion breach ~5× sharper than a 180° shutter,
   not equal to one. I did not test this and it changes nothing in this plan — it
   would only make beat 3 an even stronger hero pocket. It belongs in the defect
   log, not here.
8. **The one thing I am most confident about is the one thing to re-check first.**
   §1 is measured on the rig as it stands at the time of writing. If someone has
   authored beats 2–5 since, re-run the probe before acting on anything in this
   document — every number downstream of §1 assumes that gap is real.
