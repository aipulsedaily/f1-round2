# STAGING R2-3301 .. R2-3360 — the film's ending has no car in it, and the rebuild that puts one there

Agent: `r2-3301-caranim`. **No rendering was done and none was needed.** Every
pixel figure below is projected onto `render/film23_path.json`, the camera the
already-paid-for proxy at `work/r22161_proxy/` was rendered with.

---

## R2-3301 — the camera tracks a car that is not in the scene

```
world/car_anim.blend         built 2026-08-04 19:51
R2-943 lap-down              anim/carpath.py   2026-08-07 08:40
render/film22.blend          built 2026-08-08 04:51
render/film23_breach.blend   built 2026-08-08 07:09   <- the ship candidate
```

`tools/build_film_scene.py` **appends** the `CAR` collection and does not re-key
it, so both films carry a car authored three days before the lap-down while
their camera paths carry the lap-down.

**`render/film22_path.json` and `render/film23_path.json` are byte-identical**
(`363e4e88b30207ad`), so a figure measured on one is a figure about the ship
candidate. Confirmed before anything else was done, because the delivered
proxy's provenance is the only thing that makes any of this "on the pixels".

---

## R2-3302 — A REBUILD OF THIS BLEND IS NOT ONE COMMAND, and that is a second defect on the same path

`docs/NEXT-REBUILD.md` says of R2-943: *"Nothing to fold in; the rebuild picks it
up by running the source."* That is true of the **motion** and false of the
**artefact**, and the difference would have shipped a worse regression than the
one it fixed.

`world/car_anim.blend` is **not** the output of `anim/build_car_anim.py`. It is
that output with **two in-place material passes applied to the artefact
afterwards**, on 2026-08-04 19:51, recorded in no build script anywhere:

```
world/car_paint.py      --save   R2-521 paint v5      (+94 nodes on LiveryPaint)
tools/imperfections.py  --out    R2-014/015 wear      (R2_Imperfection, 13 mats)
```

Probed on the bytes, before trusting any of it:

| blend | `R2_Imperfection` | `LiveryPaint` |
| --- | --- | --- |
| `world/beat1_anim.blend` — **the input** | **0** | 1 |
| `world/car_anim.blend` — the shipped car | **1** | 1 |

**So running the one documented command and calling it a rebuild silently
reverts the hero subject's paint to round 1's chromed shell** — the panel that
measures 0.0121 albedo and reads as a window onto structure (R2-521). The chain
is therefore build → `car_paint --save` → `imperfections --out`, in that order
(`docs/NEXT-REBUILD.md` order rule 2), and the promotion **refuses** on a bytes
probe if either tag is missing from the rebuilt file.

*Generalises to the same lesson one file over:* **the recipe that produces an
artefact is not the same thing as the tool named after it**, and the passes that
are applied *to* an artefact rather than *by* its builder are exactly the ones no
rebuild picks up.

---

## R2-3303 — `tools/car_staleness.py`: the cheap check that would have caught this four days ago

`build_film_scene`'s validation of the appended car is thorough and **entirely
structural** — CAR_ROOT present, exactly 8 `CARRIG_*` hubs, no parent outside the
collection, `CAR_ROOT` carries an action. Every one of those passed on the stale
car. **None of them is about age.**

`world/` already has this check for its own modules
(`report_world_staleness` / `_world_source_state`, hash arm with an mtime
fallback). This is the same idea one collection over, deliberately the same
shape, over the nine sources that decide where the car is and what it looks like
— including `world/car_paint.py` and `tools/imperfections.py`, because of R2-3302.

Run against the real file as it stood this afternoon:

```
>> CAR STALENESS: car_anim.blend predates 5 of the source(s) that define it
   [mtime check -- this car carries no source fingerprint]:
   anim/carpath.py +60.8h, anim/carrig.py +60.4h, docs/beat_sheet.json +93.7h,
   docs/circuit_spec.json +74.3h, world/car_paint.py +0.2h
>> STAGE RESULT: CAR_STALE
```

**Eight controls, every one observed to fail before the checker was trusted**
(`--selftest`, `SELFTEST PASS`). The first is the real defect — a car four days
older than `anim/carpath.py` with no fingerprint — because a checker hardwired to
"fresh" passes any test made only of fresh inputs. `stale/lapdown` mutates
`anim/carpath.py` exactly as R2-943 did and requires the stamped car to go stale
**and name the file**. `fresh/touched_identical` is the mtime arm's false alarm
made non-hypothetical: `world/car_paint.py`'s mtime is **ten minutes newer** than
the real `world/car_anim.blend`, so an mtime-only check calls the shipped car
stale for a file whose bytes may never have moved.

`stale/blend_moved` deserves its own line: a fingerprint stamped on a file that
has since been re-saved must be **refused**, because that is exactly the
`car_anim_measured.json` failure — a perfectly convincing answer about a file
that is not the one on disk.

---

## R2-3304 — the rebuild, and what it is made of

`work/r2-3301/rebuild_car_anim.sh`, one hold of the big lane. Every stage judged
on its own printed `>> STAGE RESULT:` line and never on `$?`, with a `need()`
that **also refuses on a `_FAIL`/`_REFUSED`/`REFUSING TO SAVE` anywhere in that
stage's log** — a FAIL followed by a later PASS must not read as a pass.

```
0/6  re-sample the promoted beat 1   ->  world/beat1_anim_measured.json
1/6  sample the car blend ON DISK    ->  work/r2-3301/car_anim_measured_BEFORE.json
2/6  anim/build_car_anim.py          ->  world/car_anim_R2_3301.blend   CAR_ANIM_BUILT
3/6  world/car_paint.py --save                                          R2521_CARPAINT_APPLY_OK
4/6  tools/imperfections.py --out                                       IMPERFECTIONS_OK
5/6  sample the new blend            ->  work/r2-3301/car_anim_measured_AFTER.json
```

From the build log, unquoted:

```
>> reparent invariance: worst matrix element moved 5.960e-08 (Vitrine_A_brake_assembly_FL_Bell), over 947 objects at frame 792
>> keyed 2978 frames on CAR_ROOT and 8 hub empties in 17.9 s
>> 125076 keys on 42 curves; worst mid-frame departure from linear:
   as inserted 9.212e-02  ->  after setting LINEAR 4.806e-08
```

**The material chain reproduced the shipped layer exactly.** `car_paint` ends at
214 nodes on `LiveryPaint` with `Base Color <- R2CP_084_livery as pigment`,
`Metallic <- R2CP_085_metallic`, `Roughness <- R2CP_090_roughness`,
`Normal <- R2CP_092_flake facets` — the R2-521 v5 wiring. And the imperfection
report diffs against the shipped one at **nothing**:

```
K identical  True     GRP identical  True     strength 1.0 / 1.0
13 materials, same names, per-material diffs: NONE
```

**The rebuilt blend is 301,667,220 bytes — the same byte count as the shipped
car.** That is corroboration and not proof, but it is the corroboration you want
from a chain whose whole risk was silently dropping a material pass.

---

## R2-3305 — BEATS 1-5 DID NOT MOVE, measured on the artefact. And the record's boundary is off by one frame.

Measured `matrix_world`-to-`matrix_world` between the two blends —
`work/r2-3301/confinement.py`, equality and **not** a tolerance, because a
tolerance here would hide the one thing the file exists to detect.

```
span                          frames     d loc (m)   d rot (deg)  d contact (m)  d spin (rad)  d steer (deg)
1_assembly                       792  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
2_launch                          72  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
3_breach                         192  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
4_transit                        134  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
5_lap                           1524  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
6_ending                         264  6.780306e+02  2.160537e+02   6.800166e+02  2.108988e+03   7.326407e+00
```

**Every channel is exactly zero on 2,714 of the 2,715 confined frames.** Not
"below tolerance" — bitwise equal, on location, XYZ Euler, all four contact
patches, all four spin F-curves and all four steer F-curves.

### The one frame that is not zero, and it is f2715

**`docs/NEXT-REBUILD.md` records the lap-down as "beats 1-5 bit-identical at
0.000e+00 m and 0.00000 deg through f2715". Measured on the artefact built
today, that is true through f2714 and FALSE at f2715.**

```
    f2713   d loc 0.000000e+00 m   d rot 0.000000e+00 deg
    f2714   d loc 0.000000e+00 m   d rot 0.000000e+00 deg
    f2715   d loc 1.525879e-05 m   d rot 3.652131e-02 deg   <-- THE BOUNDARY
    f2716   d loc 1.840442e-03 m   d rot 2.511602e-01 deg
```

Decomposed, because "1.5e-05 m" and "0.037 deg" are two different kinds of thing:

| f2715 | dx | dy | dz | d roll | **d pitch** | d yaw |
| --- | --- | --- | --- | --- | --- | --- |
| | 0.000e+00 | **-1.526e-05** | -1.304e-08 | 2.5e-09 | **3.652e-02 deg** | 3.4e-06 |

* **The position is not a difference.** `-1.526e-05 m` is **exactly one float32
  ULP** at `y = 171.1836` (computed, not asserted: `nextafter` gives
  1.5259e-05). `dx` is exactly zero and `dz` is 1.3e-08. The car is in the same
  place to the last bit the blend can store.
* **The pitch is a real difference**, and it has a named mechanism.
  `carrig.body_pitch` returns the telemetry column while `t <= t_end` and the
  lap-down's closed form after it; `carpath._extrap` runs **flat out to the
  start/finish line and only then brakes**, so the onset is at `t_brake`, not at
  `t_end`. Evaluated on the live source:

```
  f2713  t 72.569867  decel 0.000000 m/s2  body_pitch -0.080534 deg
  f2714  t 72.611533  decel 0.000000 m/s2  body_pitch  0.000000 deg
  f2715  t 72.653200  decel 0.684767 m/s2  body_pitch  0.036521 deg
  f2716  t 72.694867  decel 4.708380 m/s2  body_pitch  0.251114 deg
```

  **0.036521 deg is the confinement table's 3.652131e-02 to five significant
  figures**, so the mechanism is confirmed against the artefact and not merely
  plausible. `t_brake` falls between f2714 and f2715: **f2715 is the first frame
  the lap-down touches at all.**

* f2714 reads exactly zero for a reason worth stating, because it looks like
  luck: it is already past `t_end` but before `t_brake`, so the new build's
  `body_pitch` takes the lap-down branch and gets **0.0** out of it, while the
  old build's took its flat-0.0 past-telemetry branch. **Two different
  mechanisms returning the same number.** It is not evidence that the lap-down
  stops at f2714; it is evidence that the lap-down has not started yet.

**Priced, so nobody has to guess whether 0.037 deg matters:** at f2715 the
camera is 87.3 m from the car on a 24.00 mm lens, and 6.374e-04 rad about the
box's 3.017 m worst arm is **1.923 mm of on-car displacement = 0.0564 px at 4K**.
Invisible, and still not zero — which is why it is reported as a difference
rather than rounded into the claim it contradicts.

> **This is NOT the `build_camera_rig.py` 0.203411 deg noise floor** and must not
> be waved through as it. That floor belongs to the camera rig's rotation solve.
> `CAR_ROOT`'s keys come out of deterministic arithmetic on the telemetry — no
> solver, no floor — and 0.036521 deg is reproducible to five figures from
> source. A number being smaller than somebody else's noise does not make it
> noise.

### What moved on purpose

`world/beat1_anim.blend` was promoted in the same pass (R2-3301b), so the 616
assembly parts in frames 1-792 move by design: **worst witness part 2.902 m at
f399 (`halo_assembly_FinBase`)**. `CAR_ROOT` itself holds its rest pose across
the whole of beat 1 in **both** blends, which is what the `1_assembly` row above
measures, so the two facts do not collide.

---

## R2-3306 — BEAT 6, ON THE DELIVERED PIXELS. 31.0 px and a third of the beat empty, to 81.0 px and none.

`work/r2-3301/beat6_subject.py`, projected onto `render/film23_path.json` — the
ship candidate's camera, and byte-identical to the camera the paid-for proxy was
rendered with. Box, camera basis, sensor and projection all **imported** from
`tools/lap_shotscale.py`; nothing retyped.

**Both arms are measured twice: once as the author's MODEL, and once as the
ARTEFACT** — `CAR_ROOT`'s `matrix_world` off the saved blend. `--car source` is
the right thing to judge a rebuild by only until the rebuild exists; after that
the question is what the file holds.

| beat 6, f2715-f2978 | **BEFORE** — the shipped car | **AFTER** — the rebuild |
| --- | --- | --- |
| car width p50 @4K | **31.0 px** | **81.0 px** |
| car width min / max | 15.9 / 153.5 | **53.5** / 244.1 |
| box height p50 @4K | 19.2 px | 37.0 px |
| **frames under 60 px — WIDTH** | **211/264 = 79.9 %** | **54/264 = 20.5 %** |
| frames under 60 px — height | 253/264 = 95.8 % | 207/264 = 78.4 % |
| **frames WHOLLY OFF FRAME** | **91/264 = 34.5 %, 3.79 s** | **0/264 = 0.0 %** |
| first wholly-off frame | **f2888**, and it never returns | — none — |
| **is the film's last frame in shot?** | **NO** | **YES** |

**Every figure in that table is measured off the blends, not off the models.**
The four-way cross-check that says so:

```
BEFORE artefact  vs MODEL --car built    worst 3.243e-05 m over 264 frames
BEFORE artefact  vs MODEL --car source   worst 6.780e+02 m
AFTER  artefact  vs MODEL --car built    worst 6.780e+02 m
AFTER  artefact  vs MODEL --car source   worst 2.108e-05 m
```

Each blend agrees with exactly one arm to ~2e-05 m and disagrees with the other
by 678 m. **The rebuild keyed the source. The shipped car did not.**

### A correction to R2-3181's own log, which I reproduced before contradicting

R2-3181 reports beat 6 as *"frames under 60 px 95.8 %"* alongside *"car size
31.0 px @4K p50"*. Reproducing its figures exactly first — p50 31.0, min 15.9,
max 153.5, 91/264 wholly off, first off f2888, in-shot p50 30.1 — then
recomputing the 60 px count every way it could have been taken:

```
width < 60 px    211/264 = 79.9 %          <- the metric "31.0 px" comes from
height < 60 px   253/264 = 95.8 %          <- the published figure
min(w,h) < 60    253/264 = 95.8 %
```

**95.8 % is the count on the box's HEIGHT; the width count is 79.9 %.** Both are
true and both describe the same defect, but they are two metrics and the report
reads as one, next to a width figure. Given and labelled here, and the client
was quoted the 95.8 % beside the 31.0 px — the coordinator is correcting it.

*One classification note, so the small discrepancy is not a mystery:* this tool
counts one f2888-adjacent frame as `partly-off` where R2-3181's counted it
`mostly on` (91 off / 1 partly / 172 on, against 91 / 0 / 173). Nothing else
differs and no headline moves.

### The gate said so too, from a completely different direction, and nobody had connected it

`tools/car_anim_gate.py` on the shipped car — this is the **plain** gate, not
the shot-scale tool, and it reads the road out of `world/build_surface.py`'s own
`world_contract.ground_z`:

```
E  tyre contact patches vs the ground the road is built from:
   worst -3.2062 m at f2977 FR, rms 0.3051 m over 3972 samples
   FAIL E: a contact patch is -3.2062 m off the road at frame 2977 corner FR (tolerance 0.030)
FAIL A: the steer angle departs from atan(wheelbase * curvature) by up to 7.3264 deg
>> STAGE RESULT: CAR_ANIM_FAIL
```

**The shipped car's tyres are 3.2 metres below the road surface at f2977** — it
does not merely leave frame, it leaves the circuit. That is a second instrument,
measuring a different property against a different reference, reporting the same
defect, and it was already failing before anyone looked. `world/car_anim_gate.log`
of 2026-08-03 records this same measurement as `E worst +0.0036 m at f850, PASS`.

**And `--selftest` was BROKEN, not merely failing.** Both `[expect PASS]` control
arms failed, so the gate's own controls could not vouch for its verdicts:

```
FAIL IDENTITY: world/car_anim.blend is 301667220 bytes now, 300235801 when it was sampled
FAIL IDENTITY: ... the dump describes a different file from the one on disk
    SELFTEST BROKEN — the gate did not do what it claims
>> STAGE RESULT: CAR_GATE_SELFTEST_BROKEN
```

The cause is the stale dump of R2-3307 below, not the gate. `world/car_anim_gate_selftest.log`
of 2026-08-03 ends `CAR_GATE_SELFTEST_OK`, so this is a regression the stale file
caused in an instrument, on top of the one it caused in the film.

---

## R2-3307 — `world/car_anim_measured.json`, its stale consumers, and which ones actually change

The file was sampled **2026-08-03 04:04** off a blend that changed **2026-08-04
19:51** — 300,235,801 bytes recorded against 301,667,220 on disk. It has now been
regenerated **on the promoted file, at its promoted name**, by re-running
`tools/sample_car_blend.py` on it. It was **not** produced by renaming the
build-time dump and editing its `blend`/`blend_bytes`/`blend_mtime` fields: a
dump that claims to describe a file it was not measured on is precisely the
failure being closed here.

### Who read the stale one

Twelve call sites in nine files. What matters is **which frames each of them
reads**, because the stale file was wrong in two different ways at once and only
one of them survives the rebuild.

| consumer | what it takes from the file | frames | verdict |
| --- | --- | --- | --- |
| `tools/r2651_occlusion_sweep.py` | the car it raycasts against | f1057-f2978 | **RE-RUN. 264 of its 1,922 rows are beat 6 and every one is about a car that moved up to 678 m.** |
| `tools/car_anim_gate.py` | the whole verdict | 1-2978 | **RE-RUN** (done below) |
| `tools/lap_shotscale.py` | controls C6/C7, `occlusion/*` | 793-2978 | **controls flip by design — see R2-3308** |
| `sim/breachlib.py` (`CAR_JSON`) | the car proxy the breach sim keys | **beat 3, f865-1056** | **NO RE-BAKE.** Confined span, measured `0.000000e+00 m` on every channel. |
| `sim/fracture.py`, `sim/seams.py`, `sim/carproxy_probe.py`, `sim/r2701_bake.py`, `sim/remote_bake.py` | via `breachlib` | beat 3 | **NO RE-BAKE**, same reason |
| `tools/beat2_probe.py` | beat-2 launch pose | f793-864 | unchanged, `0.000000e+00 m` |
| `tools/r2651_pont_sightline.py`, `tools/r2731_pit_sightline.py`, `tools/r2731_pont_camera_apply.py`, `tools/r2_1706_pont_source_verify.py` | car pose for sightlines | beat 4/5 bridge and pit | unchanged, `0.000000e+00 m` |
| `tools/r2_2881_pixelpeep.py` | box validation | beat 5 | unchanged |

**The one that has to be re-run is the occlusion sweep**, and the confinement
table is what licenses leaving everything else alone: those consumers all read
frames inside f1-f2714, where the two blends are bitwise equal. **The 10.9 GB
breach bake does not need redoing** — that is worth saying explicitly, because
the instinct on "the car changed" is to redo the sim, and the measurement says
beat 3 did not move by a single float.

### The ledger is now stale, and its own check will say so

`lap_shotscale.ledger_is_stale(source=BUILT_CAR)` compares the occlusion
ledger's mtime against `world/car_anim_measured.json`'s. Regenerating the dump
makes the dump newer, so `occlusion/not_stale_car` — **the control R2-3186 added
for exactly this** — now fails. That is the control working: an occlusion result
is a claim about a world **and** about a car, and the car underneath it has
changed.

`render/r2731/occ_final_items.json` carries **264 rows at or after f2715**. All
264 describe the wrong car. The 12 hidden frames the ledger asserts (f2180-2191,
beat 5's bridge) are inside the confined span and are unaffected.

---

## R2-3308 — **THE SHIP CANDIDATE DOES NOT APPEND `world/car_anim.blend`.** Rebuilding it was necessary and is not sufficient.

This is the finding that changes the answer to "does the ship candidate need
rebuilding", and I found it while writing the film-rebuild step rather than
before it.

`render/world/assembly/r2/v127/run_rebuild23.sh` line 28:

```
CAR=world/R22041_car_anim_driver_CS.blend
...
$B -b "$ASM" ... -P tools/build_film_scene.py -- --out render/film23.blend --car "$CAR"
```

`build_film_scene.py`'s `--car` **defaults** to `world/car_anim.blend`, and every
film on the ship path **overrides it**. `film23_breach.blend`'s own build log
says so in one line:

```
>> appended CAR (636 objects) from world/R22041_car_anim_driver_CS.blend in 27.4 s
```

**That file is the fifth link of a chain of in-place edits on top of the same
Aug-04 keys, and not one link re-keys `CAR_ROOT`:**

```
world/car_anim_driver.blend                Aug 4 19:51   <- THE KEYS, pre-lap-down
 -> work/r2881/car_anim_driver_R2881_BOTH   Aug 7 04:23   driver + seat  (R2-2881)
 -> world/R2829_car_anim_driver.blend       Aug 7 04:36
 -> world/R21701_car_anim_driver_CS.blend   Aug 7 23:01
 -> world/R22041_car_anim_driver_CS.blend   Aug 8 04:02   cockpit surface (R2-2041)
```

**It is already proved on the delivered pixels that this file carries the
pre-lap-down keys, and the proof costs nothing new:** `render/film22.blend`
appended exactly this car, and R2-3182 measured the constant-speed arm landing
on the car in `work/r22161_proxy/` to **0.000 m on every frame of beats 5 AND
6**, with the lap-down arm on empty asphalt. The delivered proxy IS the evidence.

### Why my date check would not have caught it, stated rather than buried

```
>> CAR STALENESS: R22041_car_anim_driver_CS.blend predates 1 of the source(s)
   that define it [mtime check]: docs/beat_sheet.json +13.5h
```

**It fires — and it never names `anim/carpath.py`, because the blend is 19.4 h
NEWER than the file whose motion it does not contain.** A reader who re-saved
the blend to clear that warning would have cleared it *while the real defect
stayed*. **That is worse than a clean miss**, and it is the general failure of
date-based staleness against a chain of derivative re-saves: every edit that
does not fix the defect still refreshes the timestamp that would report it.

`--selftest` control `known/date_arm_is_BLIND_to_the_real_defect` pins this on
the real file, so nobody can later mistake the date arm for sufficient.

### The check that cannot be fooled: read the keys, not the dates

`car_staleness.check_appended_car_keys(root, scene)` evaluates the appended
`CAR_ROOT`'s `matrix_world` at six probe frames and compares against
`anim/carrig` — the same pose function that authored them. Re-saving a blend
cannot change that answer; only re-keying it can. Three probes are inside the
confined span (f1200, f2000, f2714) and three are past `t_brake` (f2760, f2850,
f2978), **deliberately**: a check that only looks where the lap-down bites
cannot tell "this car is stale" from "this is not the film's car at all", and
the confined half is what makes a PASS mean something.

It is Blender-side and costs one `frame_set` loop over six frames inside a pass
`build_film_scene` is already making — no second film-sized open anywhere.
`pose_series` is called over all 2,978 frames and then indexed, never over a
window, because it accumulates wheel rotation from its first sample (R2-947).

Wiring it in is three lines at `tools/build_film_scene.py:352`, immediately
after the existing `CAR_ROOT ... animated` check:

```python
import car_staleness as CS
stale += CS.check_appended_car_keys(root, scene)
```

**I have not made that edit.** `tools/build_film_scene.py` is held by
`inflight-auto` and carries **95 uncommitted insertions** from another agent; a
lease is file-granular while the hazard is hunk-granular, and clobbering that is
a worse outcome than a checker that has to be called explicitly. The function,
its controls and its call site are ready for whoever holds that lease.

---

## R2-3309 — the gates, before and after, on the promoted artefact

`world/car_anim.blend` is now the rebuild. `world/car_anim_PRE_R2943.blend` is
the file it replaced, kept.

### `tools/car_anim_gate.py` — FAIL to PASS, on measurements nobody had connected to the ending

| | BEFORE (shipped car) | AFTER (rebuild) |
| --- | --- | --- |
| **E** worst contact patch vs the road | **-3.2062 m at f2977 FR**, rms 0.3051 m | **+0.0036 m at f850 RL**, rms 0.0001 m |
| **A** steer vs Ackermann | **departs by 7.3264 deg** | **3.15e-07 deg** |
| **F** witness part vs `beat1_anim.blend` | 2.783 m at f399 | **0.00e+00 m** over 25 parts x 16 frames |
| IDENTITY | **FAIL** — dump describes a different file | clean |
| verdict | **`CAR_ANIM_FAIL`** | **`CAR_ANIM_OK`** |
| `--selftest` | **`CAR_GATE_SELFTEST_BROKEN`** — both `[expect PASS]` arms failed | **`CAR_GATE_SELFTEST_OK`**, 5/5 arms |

Two figures worth reading as physics rather than as gate output. `B` moves from
**ground 5046.05 m** to **4286.82 m**, and the wheels from 14,026 rad to 11,917
rad: the car now brakes instead of streaking on at 89.767 m/s, and the wheels
follow it, `1896.6443 rev turned = 1895.1897 rolling + 1.4546 slip` — the
sanctioned launch wheelspin survives untouched at 1.4546 rev against 1.4547
before. Rolling contact and the slip window are both preserved through a change
that moved the car 678 m.

### `tools/lap_shotscale.py --selftest` — four controls flipped, every one by design

```
occlusion/car_identity      WARN -> PASS   the dump describes the blend on disk
film/built_arm_is_the_film  PASS -> FAIL   constant-speed arm now off by 6.55e+02 m
film/lapdown_is_NOT_in_the_film
                            PASS -> FAIL   "matches the built car to 3.47e-05 m
                                            through f2714 and then diverges to 0.0 m"
occlusion/not_stale_car     PASS -> FAIL   the ledger is older than the car again
```

R2-3181 wrote C6/C7 so that **"the day someone rebuilds `car_anim.blend` the
controls fail and say why"**. They did, and the message they print is the proof:
*diverges to 0.0 m*. **`--car source` is now the film.**

**These four need somebody's hand, and it is not mine** —
`tools/lap_shotscale.py` is leased by `r2-3181-instruments`:

1. **C6/C7 have inverted semantics.** `--car built` no longer describes any file
   on disk; it is now purely a historical arm for measuring the *delivered*
   proxy. C6 should assert the SOURCE arm reproduces the dump and C7 should
   assert the constant-speed arm does not.
2. **`occlusion/not_stale_car` is correct and must stay red until
   `tools/r2651_occlusion_sweep.py` is re-run.** 264 of the ledger's 1,922 rows
   are at or after f2715 and every one describes a car that has moved up to
   678 m. The 12 hidden frames it asserts (f2180-2191) are inside the confined
   span and are unaffected.
3. The module docstring's `--car` help text and the `>> WARNING, beat 6 only:`
   banner both now say the opposite of the truth and will mislead the next
   reader within the hour.

### `tools/car_staleness.py --check world/car_anim.blend`

```
>> CAR STALENESS: none - car_anim.blend matches its recorded source fingerprint
   over 9 module(s) [content check]
>> STAGE RESULT: CAR_FRESH
```

Stamped at `docs/beat_sheet.json` **`1abee787a8044f35`** — the live sheet,
carrying beat 5's re-pace, beat 1's re-pace and beat 6's 129.99 mm closing lens.
That sha is the film's provenance for this car.

---

## R2-3310 — the key check, observed to fail, on the real ship-path file

`work/r2-3301/keycheck.sh`. One hold of the big lane, two Blender opens, no
render.

```
--- POSITIVE  world/R22041_car_anim_driver_CS.blend  [expect CAR_KEYS_STALE]
>> CAR KEYS: the appended CAR_ROOT is NOT where anim/carrig puts it: worst 678.0 m
   at f2978 (tolerance 0.05). Per-frame:
   f1200 0.000 m, f2000 0.000 m, f2714 0.000 m, f2760 43.490 m, f2850 247.075 m, f2978 678.031 m
>> STAGE RESULT: CAR_KEYS_STALE          CONTROL ok

--- NEGATIVE  world/car_anim.blend  [expect CAR_KEYS_MATCH_SOURCE]
>> CAR KEYS: none - the appended CAR_ROOT matches anim/carrig to 0.0000 m over 6
   probe frames spanning the confined span AND the lap-down
   (f1200 0.000, f2000 0.000, f2714 0.000, f2760 0.000, f2850 0.000, f2978 0.000)
>> STAGE RESULT: CAR_KEYS_MATCH_SOURCE   CONTROL ok
```

**The positive arm is the file the ship candidate actually contains**, and the
per-frame column is the whole story in one line: identical through f2714,
43.5 m adrift by f2760, 678 m by the film's last frame. The negative arm is the
same function on the same day answering **0.000 m on all six**, so the check is
not stuck on either answer.

`f2760 43.490 m` is worth pausing on — it is the **43.5 m** R2-3182 measured
between the two arms at that frame, arrived at here from `matrix_world` on a
blend rather than from a model. Two instruments, two methods, same number.

### One source was missing from the fingerprint, and adding it is not cosmetic

`anim/carrig.py:150` imports `world_contract`, and the four-wheel contact solve
stands on `world_contract.ground_z` — the function `world/build_surface.py`
builds the road mesh from. **The car's Z and all four contact patches are a
function of that file**, so it is now in `CAR_SOURCES` and the car is re-stamped
over **10** modules. Without it the road could move under a car the checker
still called fresh.

`world/build_surface.py` is deliberately **not** in the list: `carrig` reads the
*contract*, not the *builder*. That is also why the reverted R2-3061 asphalt
work is genuinely not a variable in this build — confirmed, `build_surface.py`
is at `9b5d6fb26e337732`, and nothing in the car's source closure touches it.

---

## R2-3311 — DOES THE SHIP CANDIDATE NEED REBUILDING? Yes, and on more axes than one

**`render/film23_breach.blend` is superseded on four axes.** It has not been
touched — two other agents are mid-measurement on it and it is left exactly as
they found it. `render/film24_breach.blend` is the agreed name for its
replacement.

| axis | state in `film23_breach` | what it needs |
| --- | --- | --- |
| **the car's motion** | pre-R2-943, 91 frames of the ending with no subject | **BLOCKED — see below** |
| **beat 5's camera** | `363e4e88`, predates the re-pace | rebuild the rig from the live sheet |
| **beat 1's camera** | `363e4e88`, predates the re-pace and R2-1701's beat-6 lens | same rebuild |
| **beat 1's assembly** | the pre-R2829 seat schedule, 15/15 clusters 95-183 frames late | now fixed in `world/beat1_anim.blend` (R2-3301b) |

### THE BLOCKER, and it is new: the ship path's car is a different file and it is still stale

Rebuilding `world/car_anim.blend` fixes the file `build_film_scene` *defaults*
to. **Every film on the ship path overrides `--car`** and appends
`world/R22041_car_anim_driver_CS.blend`, which R2-3308 shows is a five-link
derivative chain off the same Aug-04 keys and which R2-3310 measures at **678.0 m
adrift at f2978**.

**So `film24_breach` cannot be built from today's work alone.** The prerequisite
is a rebuild of the *driver* car through the same chain this staging block
established for the plain one:

```
1. anim/build_car_anim.py   on the driver-bearing beat 1        -> keys from source
2. world/car_paint.py --save                                    -> R2-521 v5
3. tools/imperfections.py --out                                 -> R2-014/015
4. the R2-2881 driver+seat, R2-1701 and R2-2041 cockpit-surface passes RE-APPLIED
   -- they are edits to an artefact, not steps of a builder, exactly as R2-3302
   found for the paint. Each is currently expressed only as a probe blend.
5. tools/car_staleness.py --stamp, then --keys: it must read 0.000 m at f2978
```

**Step 4 is the real work and I have not done it**, because it is four passes
whose only expression is a chain of throwaway blends — the thing
`docs/NEXT-REBUILD.md` calls *"a derivative blend is evidence, not an
artefact"*. Whoever picks it up should treat `world/car_anim.blend` as the
worked example: the chain is knowable, it is just not written down anywhere yet.

**Estimated position: the ending is fixed in the car, and the film that would
show it does not exist yet.** No rendering is required to get there — the whole
of this block cost zero frames, and so does the film build.
