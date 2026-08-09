# STAGING R2-3781 .. R2-3840

## R2-3781..R2-3796 — the last four items: the tiering that promoted them is a host measurement, and the item the brief calls decisive cannot reach a frame

**VERDICT: STOP AND SHIP `film25_breach`. No module was authored, no world was
rebuilt, no film was built, and nothing was rendered or spent.**

The task was to build four modules and rebuild the world as `assembly16` and the
film as `film26_breach`. **Three of the brief's load-bearing premises are false,
and each is false in a way that is measurable on files already on disk.** They
were tested before any geometry was written, which is the only reason this cost
hours instead of days.

| the brief says | measured |
|---|---|
| the apron "shares a host set with the **already-built** `forecourt_paving_bay`" | `forecourt_paving_bay` is **`state: HOLD`** in the registry and contributes **zero datablocks** to `assembly15` / `film25`. Its ownership was ruled **`class`** |
| "**half that surface is dressed and half is not**" | **neither half is dressed by an item.** The whole surface is `build_architecture` class geometry. 4 of 42 registry rows are `PLACE`, and neither of these two is one of them |
| the apron peaks at **495.8 px at f282 — the opening** | f282 is a **showroom interior** (camera at world (1.698, 1.603, 2.401), inside the glass at x = 15.0, 58 mm). The apron is not in that frame. 495.8 px is `ARCH_Paving_Forecourt`'s number, inherited |
| the two "**measure identically**" | they measure identically because the presence tool takes `max()` over a **shared host list**. The two surfaces are **4.7× apart** in the resolution the film gives them |
| the three grandstand/podium items are **ONE decision** | **true, and for a deeper reason than stated** — they are literally *one measurement* (`ARCH_Grandstand_Terrace`, 47.39 px/m) multiplied by three declared heights |

Files: `work/r23781/framing.py` (new, with a 5-arm control),
`work/r23781/footprint.py` (new, with a 5-arm control).
Reports: `work/r23781/{framing,footprint}.json`,
`work/r23781/protected_films_{BEFORE,AFTER}.txt`,
`work/r23781/socket_film10.log`.

---

### 0. The `film10` negative control, reported first as instructed

```
python3 tools/socket_index_audit.py --blend render/film10.blend
rc = 1
FAIL -- 27 finding(s) in the built artefact.
```

**rc = 1.** The instrument is live and every pass measured above it is not
vacuous. Run standalone rather than through `film_bar.py`, because the bar's
`--socket` arm also opens the ~10.9 GB film blend and no film was built here.

---

### 1. Only four item modules are in the ship, and `forecourt_paving_bay` is not one of them

`world/items/PLACEMENT.json` holds **42 rows: 4 `PLACE`, 38 `HOLD`.**

```
catch_fence_post        PLACE   CFP_     676
crew_figure             PLACE   CRF_     120
timing_stand            PLACE   TS_       10
spectator_crowd_world   PLACE   SPECX_   900        = 1,706 objects
```

`render/world/assembly/r2/assembly15_build.json` agrees from the artefact side —
`items_placed: 4`, `objects: 1706`, and `object_prefixes` is
`{ARCH, BR, CFP, CRF, DR, SPECX, SURF, TER, TS, VEG}`. **There is no `FCP_`.**

Corroborated three further ways, none of them the registry:

* **the realized-mesh census of `assembly15`** (`work/r23721/census_a15_meta.json`)
  — 4,997,117 realized meshes over ten families; exactly four are item-owned.
  This is the arm that proves the negative, because it counts GN instances a
  datablock-name scan cannot see.
* **rendered pixels at f2978** (`work/r2500/items_cheap.json`, R2-709) —
  `SPECX_ 68,025 px`, `TS_ 11,821`, `CFP_ 10,263`, `CRF_ 6,232`, negative
  control `0`. Four families, four non-zero readings.
* **`SHIPPING.md`'s promotion ledger** — assembly9 → assembly10 `+1,707`
  objects, attributed to "four registry rows going HOLD → PLACE".

`forecourt_paving_bay`'s row carries two blockers — `PARTIAL_BUILD` (the blend
holds 450 units against a declared 1,400) and `SUPERSEDE_WELDED` — and an
`r2331_ownership.verdict` of **`class`**:

> "`ARCH_Paving_Forecourt` is not paving bays. It also casts the formation slab
> the round-1 pavilion floor sits on … plus the granite sett bands, the bedding,
> the perimeter edge band and slot drain, and the bollard line … The item holds
> 450 of a declared 1,400. **Class.**"

**So the defect the apron was to fix — "half that surface is dressed and half is
not" — does not exist.** The forecourt and the apron are both undressed, both
built by `build_architecture`, and building one more module would have produced
a fifth `HOLD` row, not a changed pixel.

---

### 2. f282 is a showroom interior, and it is where the apron's 495.8 px comes from

Read off `render/film25_path.json` (byte-identical to film24's, the delivered
camera):

```
f275   pos (  0.935   1.126   2.402)   58.00 mm
f282   pos (  1.698   1.603   2.401)   58.00 mm     <- the apron's declared peak
f910   pos ( 15.691  -1.759   2.137)   21.00 mm
f2976  pos (594.190  16.050 140.000)  129.76 mm     <- the closing crane
```

`world_contract.ACCESS_GLASS_X = 15.0`. At f282 the camera is at **x = 1.698 —
thirteen metres inside the glass.** `work/r22161_proxy/r22161_proxy_000282.png`
was looked at: it is the car's rear wing against the glazed wall and the polished
interior floor. **There is no exterior ground anywhere in the frame.**

This is R2-2990's finding arriving a second time by a second route. That entry
established that `ARCH_Paving_Forecourt`'s headline 1049.4475 px/m at f282 is set
by geometry *buried under the showroom floor* — the formation slab at
z −0.36…−0.100 beneath a floor whose top is 0.000 — and that masking to the
item's own geometry moved the answer by 73.75 %. **`exterior_ground_apron`
inherits that object as a host and therefore inherits the whole defect.**

---

### 3. The presence numbers are `declared height × host px/m`. All four.

`work/r23721_item2/a9_film24_item_presence.json` carries
`measured_as_self: false` on all four. Dividing each item's
`peak_unocc_sharp_px_4k` by its manifest `height_m` returns a host's px/m
exactly:

```
item                        h     peak px   =>  implied px/m   the host it is
exterior_ground_apron      1.0      495.8         495.80       ARCH_Paving_Forecourt
forecourt_paving_bay       1.0      495.8         495.80       ARCH_Paving_Forecourt  (identical row)
grandstand_debris_fence    3.6      179.8          49.94       ARCH_Grandstand_05_TEMPORAIRE  (49.96)
podium_backdrop            4.0      189.6          47.40       ARCH_Grandstand_Terrace        (47.39)
podium_structure           3.5      165.9          47.40       ARCH_Grandstand_Terrace        (47.39)
```

**The three grandstand/podium items are not three measurements that happen to
agree. They are one measurement wearing three declared heights.** The brief's
"identical numbers, same host set" is right on the fact and understates it: there
is no independent evidence about any of the three, because none of the three
exists to be measured.

**And the apron and the forecourt bay have byte-identical `measured` blocks** —
every field, not just the peak — because `item_presence` takes `max()` over the
shared host list `[ARCH_Paving_Forecourt, ARCH_Paving_ApronPlatform]`. That is
what "measures identically" means here. It is a property of the host list, not
of the two surfaces.

---

### 4. What the film actually gives these four — `work/r23781/framing.py`

The projection, the constants and the quaternion convention are **imported from
`tools/screen_presence.py`**, not retyped, so this arm and the published table
are the same instrument pointed at a different subject (R2-2990's rule). The
authoritative column is `peak_unocc_sharp_px_per_m` out of
`work/r23721_item2/a9_film24_sp_objects.json`; this task's own arm is printed
beside it and differs where noted.

```
                                     published        this task's arm
exterior_ground_apron
  ARCH_Paving_ApronPlatform  (self)    133.60 @f1020     155.63 @f2581
  ARCH_Paving_Forecourt   (ranked)    1049.45 @f282      870.80 @f382
                                       -- 7.86x --        -- 5.60x --
grandstand_debris_fence  (self==ranked) 49.96 @f2978     256.35 @f2703
podium_backdrop / _structure             47.39 @f2976     115.79 @f2695
```

**Only the apron is over-ranked.** The three grandstand/podium items are ranked
through their own would-be location, so their numbers — poor as they are — are
honest.

**Where the two arms disagree, the published one wins, and the reason is a
defect in mine, stated rather than buried:** my smear mask is built from the
camera's *angular* rate alone. For a near object on a fast-translating camera
(f2703, the grandstand at 10.76 m in beat 5) translation dominates and my mask
calls sharp a frame the published table does not. The published
`peak_unocc_sharp_px_per_m` for `ARCH_Grandstand_03_PRINCIPALE` is **22.98**,
mine reads 256.35 at the same object. **Use 49.96 / 47.39, not my numbers.**

#### The control, and what each arm was watched to do

`python3 work/r23781/framing.py --control`

```
  (none)       NULL, must NOT move    0/ 8 moved   ok
  no_frustum   must move              8/ 8 moved   ok
  no_depth     must move              8/ 8 moved   ok
  no_smear     must move              2/ 8 moved   ok
  frozen_lens  must move              8/ 8 moved   ok
>> STAGE RESULT: R2_3781_FRAMING_CONTROL_OK
```

`no_smear` moving only 2 of 8 is reported rather than tuned away: for the
grandstand objects the peak frame is already sharp, so removing the sharpness
test cannot move them. An arm that moves 2 of 8 is still an arm that can fail;
an arm that moved 0 would have been declared vacuous.

**One defect in this instrument was caught by its own output and fixed before
any number above was used.** The first draft printed the *median* depth beside a
*minimum*-depth px/m — "155.63 px/m at 178.02 m on a 40 mm lens", which is
arithmetically impossible. Fixed to report the depth of the point that set the
figure. The impossible pair is what made it visible; a plausible one would not
have been.

---

### 5. Every feature's pixel size, stated before anything was built — `work/r23781/footprint.py`

R2-2970's law, unchanged: **isolated features are declined at 1 px, periodic
features at 2 px on their PITCH** — "a wave sampled under twice per period does
not come out small, it comes out aliased". Two amplifiers, both derived from the
contract rather than typed: the sun at **12.47061°** gives relief features a
shadow of **×4.5217**, and in-plane rows on the apron are foreshortened by
**|n·v| = 0.2071** (R2-2990's measured grazing angle for this surface — carried
here as a *stated* assumption, flagged in the tool's own output).

#### 5a. `exterior_ground_apron` — 133.60 px/m, **1 px = 7.485 mm**, Nyquist 14.97 mm

| feature | kind | mm | px | line | verdict |
|---|---|---:|---:|---:|---|
| bay saw-cut joint PITCH | per | 3000.0 | 400.81 | 2.0 | ABOVE — **already built** (`paving_bays 5491`, `paving_sawn 2178`) |
| surface undulation, λ 1.5 m | per | 1500.0 | 200.40 | 2.0 | ABOVE — already built |
| edge upstand / drop to bedding | relief | 100.0 | 60.41 | 1.0 | ABOVE — already built (`apron_edge_max_drop_mm 5.0`) |
| tyre-rubber deposit band WIDTH | inplane | 600.0 | 16.60 | 1.0 | ABOVE — already built by `build_surface` |
| drainage channel slot PITCH | per | 25.0 | 3.34 | 2.0 | ABOVE |
| bay joint SHADOW (5 mm sinking) | relief | 5.0 | **3.02** | 1.0 | ABOVE — already built (`apron_joint_quads 2432`) |
| arris chamfer at bay edge | relief | 3.0 | **1.81** | 1.0 | ABOVE |
| exposed aggregate diameter | iso | 8.0 | 1.07 | 1.0 | **MARGINAL** |
| **joint sealant bead WIDTH** | inplane | 10.0 | **0.28** | 1.0 | **BELOW** |
| **bay joint WIDTH** | inplane | 4.0 | **0.11** | 1.0 | **BELOW** |
| **broom / tine finish PITCH** | per | 2.5 | **0.33** | 2.0 | **BELOW** |
| **float-texture stipple** | iso | 1.2 | **0.16** | 1.0 | **BELOW** |
| **hairline shrinkage crack WIDTH** | inplane | 0.8 | **0.02** | 1.0 | **BELOW** |

**7 ABOVE, 1 MARGINAL, 5 BELOW — and every one of the seven ABOVE is already
built by `build_architecture` or `build_surface`.** The genuinely new candidates
— the broom finish, the float skin, the aggregate, the sealant bead, the
hairlines, the visible cut of the joint itself — are all BELOW the line or
marginal. **At the resolution the film gives this surface, an item module has
nothing to add that reads.** The one exception, the 3 mm arris at 1.81 px, is a
single chamfer on an edge the class module already draws.

The declined rows are on the record deliberately: R2-2970's rule is that "the
arithmetic that declines a feature has to be on the record or somebody will
build it again."

#### 5b. `grandstand_debris_fence` — 49.96 px/m, **1 px = 20.018 mm**, Nyquist 40.04 mm

| feature | kind | mm | px | line | verdict |
|---|---|---:|---:|---:|---|
| fence overall height | iso | 3600.0 | 179.84 | 1.0 | ABOVE |
| post PITCH | per | 2500.0 | 124.89 | 2.0 | ABOVE |
| post section depth | iso | 150.0 | 7.49 | 1.0 | ABOVE |
| bracket / cleat plate | iso | 100.0 | 5.00 | 1.0 | ABOVE |
| top rail diameter | iso | 48.0 | 2.40 | 1.0 | ABOVE |
| **debris MESH aperture PITCH** | per | 50.0 | **2.50** | **2.0** | **MARGINAL** |
| **mesh wire diameter** | iso | 3.15 | **0.16** | 1.0 | **BELOW — must be shading** |
| **tensioning cable diameter** | iso | 8.0 | **0.40** | 1.0 | **BELOW** |
| **galvanising spangle** | iso | 15.0 | **0.75** | 1.0 | **BELOW** |

**The defining feature of a debris fence — the mesh itself — lands at 2.50 px of
pitch against a 2.0 px Nyquist line, and its wire is 0.16 px.** A debris fence
at the closing frames is a 180 px tall translucent band with a hatch one sample
either side of aliasing. It is buildable; it is not obviously worth building,
and the mesh must be **shading, not wire geometry**, or it will alias rather than
soften.

#### 5c. `podium_structure` — 47.39 px/m, **1 px = 21.100 mm**

**7 ABOVE, 1 MARGINAL, 1 BELOW.** Overall height 165.88 px, dais riser 8.53,
step nosing **6.43 px through its shadow** (1.42 px as geometry — the ×4.5217 is
what makes a step read as a step), deck plank pitch 7.11, balustrade infill
pitch 4.74, panel joint reveal 2.14, handrail tube 1.99. Declined: **fixing bolt
head 19 mm = 0.90 px**. Marginal: deck plank gap 5 mm = 1.07 px in shadow.

#### 5d. `podium_backdrop` — 47.39 px/m, **1 px = 21.100 mm**

**5 ABOVE, 1 MARGINAL, 2 BELOW.** Overall height 189.57 px, brand tile pitch
56.87, **sponsor lettering cap height 300 mm = 14.22 px** (the only thing a
backdrop is for, and it reads), fabric sag 8.57 px in shadow, frame tube 2.37.
Declined: **fabric weave pitch 1.2 mm = 0.06 px** and **panel seam 12 mm =
0.57 px**. Marginal: eyelet 25 mm = 1.19 px.

#### The control

`python3 work/r23781/footprint.py --control`

```
  (none)           NULL, must NOT move    0/39   ok
  no_shadow        must move              4/39   ok
  no_foreshorten   must move              1/39   ok
  no_nyquist       must move              1/39   ok
  ranked_px_per_m  must move              4/39   ok
>> STAGE RESULT: R2_3781_FOOTPRINT_CONTROL_OK
```

`no_shadow` moving 4 rows is the ×4.5217 doing real work: without it the step
nosing, the plank gap, the bay-joint shadow and the arris all fall below the
line. `ranked_px_per_m` moving 4 rows is **the defect itself, dosed** — swapping
the apron's honest 133.60 px/m for the ranking's 1049.45 promotes four features
that do not read.

---

### 6. The two surfaces are 4.7× apart, and the apron cannot reach a frame anyway

The manifest's own note for `exterior_ground_apron` describes **world X 10..90,
Y −40..+40** — the showroom breach ground — while `tools/item_hosts.py` maps it
to `ARCH_Paving_ApronPlatform`, the **316 m pit-exit apron** at x −83.5…166.5,
y −146.5…47.5. Measured against the built point cloud, the declared rectangle
holds **26.7 %** of the apron platform's points and **31.7 %** of the forecourt's,
so the two readings of the item overlap but are not the same object.

Restricting each surface to that declared rectangle and re-measuring:

```
  ApronPlatform, whole 316 m strip           155.63 px/m  @f2581  27.50 m   1 px = 6.425 mm
  ApronPlatform INSIDE X 10..90 Y -40..40    143.09 px/m  @f996   20.60 m   1 px = 6.989 mm
  Forecourt,     whole object                870.80 px/m  @f382    6.75 m   1 px = 1.148 mm
  Forecourt     INSIDE X 10..90 Y -40..40    671.72 px/m  @f868    4.39 m   1 px = 1.489 mm
```

**f868 is beat 3, the breach.** The forecourt paving genuinely is 4.39 m from
the lens there — that number is not an artefact, and it is why
`forecourt_paving_bay` was written. **The apron is 4.7× coarser than the
forecourt on the same "shared" surface.** They were never one surface at one
resolution; the host list made them look like one.

**And the apron cannot reach a frame without a class-level change.**
`ARCH_Paving_ApronPlatform` is a single object `build_items` could delete — but
that one mesh carries five welded layers (finished bays, gully cylinders,
bedding, sealant, a closed formation slab), and two other modules have already
cut themselves back to its boundary: `build_surface`'s `SURF_ApronJoint` laps
onto it on the identical `apron_zone(s,+1) > 0.5` predicate, and
`build_terrain` cuts a real hole in `TER_Ground` there. Removing it opens
~6,400 m² of sky. Doing it properly needs a `class_switch` inside
`build_apron_platform` that skips the finished-bay pass while keeping bedding,
sealant and formation — a source change to `build_architecture.py` plus a full
re-assembly. **Its twin on the same host set was ruled `class` for exactly this
reason.**

---

### 7. Two corrections to the acceptance criteria

**7a. "`assembly16` must fingerprint 0 of 94 drifted" cannot survive adding
modules, and the invariant that can is `0 drifted`.** The 94 is a *count of
source files*, not a constant:

```
   world/items              82        (49 *.py + 33 *.json)
   world/build_*.py         10
   world/itemkit.py          1
   world/world_contract.py   1
   assemble.py               1        = 94
```

Adding N item modules with their interface json makes it **94 + 2N**. A build
that added four modules and still reported "94" would mean the fingerprint had
*not* picked them up — the opposite of what the criterion is for.

**7b. `assembly15` still fingerprints 0 of 94 against the worktree right now**,
re-run under this task:

```
assembly15 fingerprint: 94 file(s), 0 differ from the worktree now
```

So no world source has drifted under any agent since film25 was built, and
`film25_breach` remains buildable from its own recorded state.

---

### 8. The three protected films are untouched

Taken before any work and re-taken after. **`film25_breach` had no recorded
sha anywhere in `docs/`, `work/` or `render/` — this is the first one.**

```
BEFORE 2026-08-09T04:12:13Z          AFTER (see protected_films_AFTER.txt)
film23_breach  642371aea6df60c1515066a2497d093ac1c0886bbc13c5ffc4c591e90c4f908e   10,946,487,113 B
film24_breach  19b59635d1c394b3dcef77baebbb0d9dc6852a84175ecc3d08ca19c97406592c   10,946,488,553 B
film25_breach  1d2aa2d86533574ef6b57d2b947ce32598b714d0eb3477fa0cbe6659f59c1418   10,956,580,171 B
```

The first sixteen hex of film23 and film24 reproduce the values
`run_rebuild25.sh` recorded (`642371aea6df60c1`, `19b59635d1c394b3`).
**`film25_breach` = `1d2aa2d86533574e` should go into the next rebuild script's
tripwire; there was nothing to compare its first reading against.**

---

### 9. What was deliberately NOT done

**No module was authored. No `assembly16`. No `film26_breach`. No render, no
GPU job, $0 spent.** Credit is untouched at $73.33.

Proceeding would have meant: authoring four modules against a detail budget
overstated 7.86× for the decisive one; gating four items on the 5090 (money, and
the gate needs **12,000 subject pixels** in its witness frame — the same floor
that returned `ITEM_UNMEASURABLE` for `forecourt_paving_bay` at its corrected
framing, for $0.0264); adding registry rows that `build_items` would refuse
unless the live `gate.json` reads `ITEM_ACCEPTED`; and then a ~22 min world
rebuild and a multi-hour film rebuild, to put a fifth `HOLD` row next to the
four that already exist.

**`film26_breach` therefore has no camera-path sha and no bar verdict to
report.** Manufacturing either would be worse than reporting neither.

---

### 10. If the increment is still wanted, this is the only defensible one

**The podium group — `podium_structure` then `podium_backdrop` — and nothing
else.** They are the only two of the four that are *both* reachable and have
content above the line.

* **Reachable.** `build_architecture` builds **no podium on the grandstands at
  all** — the sole podium geometry in the world is a timber deck, nine 35 mm
  balusters and a handrail welded into `ARCH_RaceControl` on the pit building,
  which is not in either item's host set. The census records both as `UNDET`:
  *"host `ARCH_Grandstand_*` exists; assembly9 carries NO name and NO counter for
  this feature."* So `"supersedes": []`, **no `class_switch`, no
  `rebuild_owed`, no class-builder edit** — exactly the position
  `spectator_crowd_world` was in.
* **Content.** 7 of 9 and 5 of 8 features above the line, including 14.22 px of
  sponsor lettering and a step nosing that reads at 6.43 px through its shadow.
* **Anchoring.** Anchor to the terrace deck at **`APRON_Z = 0.000`**, *not* to
  `C.world_ground_z` — the grandstand band is beyond `platform_edge(-1) = 25.0`
  and `world_ground_z` returns **NaN** there. Respect `grandstand_max_z = 13.25`,
  which is asserted twice because the beat-6 camera passes 13.8 m above the
  roofline.
* **Order.** `podium_structure` (build order 424) before `podium_backdrop` (425);
  the backdrop consumes the structure's interface json. Note
  `podium_structure` declares `depends_on: ["pit_building_roof_deck"]`, which
  has no module — that dependency needs resolving or explicitly waiving first.

**`grandstand_debris_fence` I would decline** on its own arithmetic: its
defining feature is 2.50 px against a 2.0 px Nyquist line and its wire is
0.16 px. **`exterior_ground_apron` I would decline** on §5a and §6: nothing it
could add reads, and it cannot reach a frame without a class-level change.

**The honest expected gain from the podium group is two objects, 166 and 190 px
tall, at ~292 m on a 130 mm lens, in the last 10.3 seconds, beside a grandstand
that is already cropped at frame edge.** That is a real increment and a small
one, and it costs a world rebuild, a film rebuild and a full bar re-run against
a `film26` that must still land the camera path at `9d055d63da724993`.

---

### 11. How to reproduce every number above

```bash
cd /home/zany/f1-round2

# the negative control, first
python3 tools/socket_index_audit.py --blend render/film10.blend ; echo "rc=$?"

# what the film gives the four items, and the 5-arm control
python3 work/r23781/framing.py --out work/r23781/framing.json
python3 work/r23781/framing.py --control

# every feature's pixel size, stated before building, and the 5-arm control
python3 work/r23781/footprint.py --out work/r23781/footprint.json
python3 work/r23781/footprint.py --control

# the presence numbers are height x host px/m
python3 -c "
import json
d=json.load(open('work/r23721_item2/a9_film24_item_presence.json'))
for r in d['items']:
    if r['id'] in ('exterior_ground_apron','forecourt_paving_bay',
                   'grandstand_debris_fence','podium_backdrop','podium_structure'):
        m=r['measured']
        print('%-26s h=%4.1f peak=%7.1f => px/m %8.2f  self=%s'%(
            r['id'],r['height_m'],m['peak_unocc_sharp_px_4k'],
            m['peak_unocc_sharp_px_4k']/r['height_m'],r['measured_as_self']))"

# the fingerprint, and what the 94 is made of
python3 -c "
import json,hashlib,os
R2='/home/zany/f1-round2'
fp=json.load(open(R2+'/render/world/assembly/r2/assembly15_build.json'))['source_sha256']
d=[r for r,s in sorted(fp.items()) if hashlib.sha256(open(os.path.join(R2,r),'rb').read()).hexdigest()!=s]
print('fingerprint: %d file(s), %d differ'%(len(fp),len(d)))"

# f282 is a showroom interior -- look at it
#   work/r22161_proxy/r22161_proxy_000282.png   (camera x=1.698, inside glass at x=15.0)
#   work/r22161_proxy/r22161_proxy_002976.png   (the closing crane, 140 m up, 130 mm)
```

`work/` is gitignored, so the two scripts are tracked and their json are not;
every number regenerates from the commands above. **Nothing was rendered and
nothing was spent.**
