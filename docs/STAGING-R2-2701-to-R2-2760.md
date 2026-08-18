# STAGING R2-2701 to R2-2760 — the crowd library is not on the road, the gate was

Agent `r2-2701-crowd-placement`. 2026-08-08. Task #150.

`assembly14.blend` reported **`PLACEMENT_FAIL`, 1,202 violations**, every one of
them a `SPECX_Lib*` spectator-library prototype standing at the world origin,
894 of them in the car's swept path at up to 1.6025 m — the full swept
half-width, i.e. dead centre. The question the task set was which of two
opposite things that means, and it forbade guessing.

**It is the gate.** The 894 prototypes are the instance sources of the crowd,
all 894 carry `hide_render = True`, and the whole film has already been rendered
from a scene containing them — with the world origin inside the frustum on 696
of the 2,978 frames, at up to **2,589 px of figure height** — with nothing
there. The gate was measuring geometry that cannot appear in a frame.

---

## R2-2701 — the answer up front

| | |
|---|---|
| What `SPECX_Lib*` is | 894 **instance sources** for the crowd, in `ITEM_spectator_crowd_Library`, all `hide_render = True`, realised as **11,129 instances on the six grandstands** |
| Does it render at the origin | **No.** 696 proxy frames see the origin, closest 2.5 m, and the dais is empty in all of them |
| Does it render at all | **Yes** — f2607 shows the grandstand full of people. Same 894 sources, 300 m away |
| What changed | `tools/placement_gate.py`: non-rendering meshes are measured and reported under `hidden_findings`, not counted as violations — **and every realisation of a hidden source is now measured at its instance matrix** |
| Controls | 42 → **54**, and the four new decisive ones were **watched failing** against two deliberate mutants |
| The world | `assembly14.blend` — **`PLACEMENT_FAIL` 1,202 → `PLACEMENT_CLEAN` 0**, all three clearances positive and naming real geometry. R2-2711 |
| Ship candidate | `render/film23_breach.blend` — **`PLACEMENT_FAIL` 16,685 → 482**, and all 482 are the car, the driver, the showroom set and the wall the car breaches. **Clear to render.** R2-2707, R2-2710 |

---

## R2-2702 — what `SPECX_Lib*` is, established before anything was touched

Read-only probe of `render/world/assembly/r2/assembly14.blend`
(`work/r22701/libprobe_assembly14.json`, log alongside):

```
n_mesh_objects                30,204
n_specx_lib                      894
lib_hide_render_true             894      <- all of them
lib_hide_render_false              0
lib_collections                  ITEM_spectator_crowd_Library  (894)
layer state of that collection   exclude=False hide_viewport=False
                                 collection_hide_render=False
lib_bbox_world                   x[-0.85, 1.02] y[-0.63, 1.00] z[-0.69, 1.96]
depsgraph_instances_of_lib    11,129     at x[32.4, 495.6] y[-138.7, 256.1]
                                            z[2.56, 10.71]
hidden meshes in the whole scene    894   — i.e. these and nothing else
```

Six `SPECX_Crowd_*` field objects, each with a `NODES` modifier whose
`GeometryNodeCollectionInfo` points at `ITEM_spectator_crowd_Library` with
`Separate Children` on, picking a source per point from the `hk_src` attribute:

```
SPECX_Crowd_Ouest       1,843 instances     SPECX_Crowd_Principale  3,345
SPECX_Crowd_T15         2,510               SPECX_Crowd_Est         1,559
SPECX_Crowd_Ouest.001   1,414               SPECX_Crowd_Temporaire    458
                                            ------------------------------
                                            11,129 people
```

11,129 is exactly the population `world/items/spectator_crowd_world.py`
documents. **Deleting the 894 deletes the crowd.**

The source module already knew all of this and says so in prose:
`spectator_crowd.build_library(yard=None)` sets `hide_render` on every source,
and `spectator_crowd_world.build_world` **re-reads the flag off the built
objects and raises** if any came back visible —

> `"%d of %d library sources are NOT hide_render (%s...). The yard=None branch
> is the only one that hides them and it did not run; shipping this puts %d
> unaccounted people in a field."`

— which is the same defect in the opposite direction, already guarded. The
alternative branch (`yard=`) lays the sources out on a visible contact sheet for
`item_gate`, and that branch is documented as being inside the 4K frustum on 545
frames. The world took the hidden branch.

---

## R2-2703 — the frame evidence, which is what actually settles it

`work/r22161_proxy/` is 2,978 frames at 960×540 covering the whole film. All
2,978 were rendered from `render/film22.blend` (broker job records across
`state2…state11`, `seq = r22161_proxy`, `scene =
render/film22.blend`), and `work/r22041/build_film22.log`
line 1 reads

```
Read blend: ".../render/world/assembly/r2/assembly14.blend"
>> film scene: assembly14.blend -> render/film22.blend  (+977 objects, 32045 total)
```

**So these frames are of the very world that failed the gate.**

Projecting the world origin through `render/film23_path.json` (byte-identical to
`film22_path.json`) at 3840×2160 / 36 mm:

```
frames with the world origin inside the frustum        696 of 2,978
closest approach of the camera to the origin           2.52 m
apparent height there of a 1.75 m figure             2,589 px   (frame height 2,160)
apparent height at frame 1 (9.2 m, wide)               364 px
```

The origin is where the showroom dais is — telemetry station 0, where the car
starts. Frames inspected:

| frame | camera → origin | what is there |
|---|---|---|
| 1 | 9.2 m, origin at (2095, 814) of 4K | the car on the dais, the dais empty |
| 372 | 2.8 m | the car's bodywork filling the frame, no figure |
| 812 | dais in full view | the dais empty but for the car |

**894 human figures stacked inside a 1.9 m cube at that point would be
unmissable at 91 px in the proxy and 364 px at 4K. They are not there.**

The positive half of the same control, and it matters more than the negative
half: **frame 2607 shows the grandstand packed with people.** Same 894 sources,
realised 11,129 times, 300 m from the origin. So the flag is not hiding the
crowd — it is hiding the *sources*, exactly as designed, and the instancing that
depends on them is working.

That is the whole finding: **the world is right, and the instrument was
measuring something that is not in the film.**

---

## R2-2704 — so the fix is in the gate, and it is not an allow-list

`tools/placement_gate.py` walked `scene.objects` and measured every mesh
regardless of whether it can render. Its three volumes are all statements about
the film — *"a car would hit it"*, *"the shot is dead and there is no cutting
around it"* — and there is no physics in this project; the car is animated off
telemetry. A mesh that never renders cannot be hit and cannot be clipped.

Three things were added, and the second is the one that makes the first
defensible.

**1. `render_hidden_map(scene)`** — `{object: why}` for every mesh that cannot
reach a frame where it stands: `object.hide_render`, any collection *above* it
with `collection.hide_render`, or a `layer_collection.exclude` **in every view
layer with `use` set** (the union would have been a silencer; a collection
switched off in one view layer and on in another still reaches the frame).
`hide_viewport` is deliberately **not** in the list — it hides an object from
the 3D view and renders it anyway.

**2. Every realisation of a hidden source is measured, at its instance matrix.**
This is the hole that (1) opens, and it is not hypothetical — *"hidden source,
instanced somewhere visible"* is precisely what the crowd library **is**.
`measure()` now walks `depsgraph.object_instances`; an instance whose source is
render-hidden is measured per-vertex and reported as a first-class violation
named `instancer[source]`, carrying `instance_of`, `instanced_by` and
`source_hidden_because`. **Hiding a fence and instancing it onto the racing line
now fires louder than leaving it visible, not quieter.**

**3. Nothing is silenced.** Findings from hidden meshes go to `hidden_findings`
with the reason in every row, exactly as `context_findings` already worked; the
count is in the printed verdict tag and the JSON; and their own closest approach
is kept separately in `hidden_closest_approach_m` so removing them from
`closest_approach_m` does not lose the number. That removal was itself a repair:
on `assembly14` the crowd library **owned both headline clearances** —
`car_path −1.6025 m` and `camera_path −0.6919 m` — so the two figures a reader
acts on were about geometry that is not in the film.

### What is still not measured, named with its size

Instances whose source is **visible** are not measured at their instance
matrices — only the source object is, where it stands. On `assembly14` that is
**4,955,784 realisations**, nearly all `VEG_*` scatter. That blind spot predates
this change and is not widened by it, and the report now counts it in
`instances.of_visible_sources_NOT_MEASURED` so **the gate declares its own
coverage instead of implying total coverage**. Closing it means adjudicating ~5 M
grass and grit realisations against the corridor and is its own task.

---

## R2-2705 — the controls, watched failing

`--selftest` goes **42 → 54 controls**, `>> STAGE RESULT:
PLACEMENT_SELFTEST_OK` (`work/r22701/selftest_2.log`). The new section builds
four objects in one place — the racing line at the high point — and requires
four different verdicts for four different reasons:

```
>> SELFTEST: non-rendering geometry, and the hole that opens
   PASS  hide_render is read as 'cannot reach a frame'
   PASS  CONTROL: a VISIBLE mesh is not classed non-rendering
   PASS  A  visible cube on the racing line is a VIOLATION
   PASS  B  the SAME cube hidden is NOT a violation
   PASS  B  ...and is REPORTED under hidden_findings, with its reason
   PASS  C  a hidden source INSTANCED onto the road IS a violation
   PASS  D  the same hidden source instanced CLEAR of the road is silent
   PASS  D  ...and the hidden source at its own location is not a violation
   PASS  CONTROL: the instance pass actually ran
   PASS  closest_approach on road_corridor is NOT owned by the hidden cube
   PASS  COUNTERFACTUAL: hidden cube alone on the road -> 0 violations
   PASS  COUNTERFACTUAL: ...and it is still in hidden_findings
```

D is the crowd library reproduced in miniature — one hidden source in a library
collection, instanced by a GeometryNodes `CollectionInfo` field onto a point
3 km off the circuit — and it has to be **silent**, or A and C prove nothing
about the actual case.

### The controls were observed failing, against two deliberate mutants

A control that has only ever passed has not been tested. Two copies of the fixed
gate were broken in the two ways that matter and run against the same blend and
the same frozen inputs:

| mutant | change | result |
|---|---|---|
| **M1** `work/r22701/mutant_no_instance_pass.py` | the instance pass is skipped | `FAIL  C  a hidden source INSTANCED onto the road IS a violation  fires=False expected=True` and `FAIL  CONTROL: the instance pass actually ran` → `>> STAGE RESULT: PLACEMENT_SELFTEST_FAIL`, rc=1 |
| **M2** `work/r22701/mutant_silent_hidden.py` | hidden findings dropped instead of reported | `FAIL  B ...and is REPORTED under hidden_findings` and `FAIL  COUNTERFACTUAL: ...and it is still in hidden_findings` → `>> STAGE RESULT: PLACEMENT_SELFTEST_FAIL`, rc=1 |

Note what M1 also demonstrates: with the instance pass removed,
`closest_approach on road_corridor` is owned by `SELFTEST_VIS_onroad`; with it
present, it is owned by `SELFTEST_FIELD_onroad[SELFTEST_HID_source]` — the
instance, which is deeper in. The instance pass is not decoration.

**And the first run of both mutants exited `rc=0` on an uncaught
`ModuleNotFoundError`** (the copies were outside `tools/`, so the gate's own
`sys.path` insert did not find `provenance`). Blender 5.2 exiting 0 on a
traceback, observed live, in the middle of judging controls. Only the
`>> STAGE RESULT:` line was trusted.

### The existing battery is unchanged

```
ctl_place_pos   rc=1  >> STAGE RESULT: PLACEMENT_FAIL
                      closest car_path CTL_Obstacle -1.171 m, road_corridor -7.822 m
ctl_place_neg   rc=0  >> STAGE RESULT: PLACEMENT_CLEAN
```

Same verdicts, same objects, same clearances as before the change.

---

## R2-2706 — a second defect found on the way: the gate's default camera path
   is not the film's camera

`placement_gate.py --campath` defaults to `world/camera_rig_path.json`, and
`work/r2-2341/frozen/camera_rig_path.json` is a byte copy of it
(`d9c8f5c54ccd…`). **That is not the live camera.** `docs/LIVE-CAMERA.md`
declares sha `363e4e88b302…`, which is `render/film23_path.json` (and
`film22_path.json`, and `film19_path.json` — all identical).

So the `camera_path` volume in the assembly14 baseline — the volume that
produced 308 of the 1,202 violations — was swept along a camera the film does
not use. `docs/LIVE-CAMERA.md` measures the divergence between that orphan and
the live path at up to **9.866 m of position and 103.3 deg of orientation, all
of it inside beat 1** — which is precisely the span that contains the origin.

Every run in this task passes `--campath render/film23_path.json` explicitly.
The default is left as found and is flagged here: **it should be changed to read
`tools/live_campath.py`'s declaration rather than a filename**, which is the
whole point of that file, and it belongs in the defect log rather than in this
change.

---

## R2-2707 — the ship candidate, under the gate of record: **PLACEMENT_FAIL,
   16,685 violations** — and 1,202 was the small half of it

Said loudly and early, as the task asked. `render/film23_breach.blend`, gate at
`HEAD` (`ab078e1`), live camera path, frozen spec/telemetry/sheet
(`work/r22701/gate_film23_breach_HEAD.{log,json}`):

```
>> subject: 46231 meshes via every mesh in the scene (nothing looks like context)
>> tested 46156 objects; 28869 rejected on bounding box; 17287 measured per-vertex
>> closest approach, camera_path    Plaque_Surround   -1.070 m   at (-0.393, -5.389, 0.666)
>> closest approach, car_path       GS_b05_00921      -1.602 m   at (0.0, 0.0, 0.008)
>> closest approach, road_corridor  ARCH_Gantry       +1.149 m   at (336.512, 163.194, 0.305)
>> determinism: 2 pass(es), IDENTICAL
>> 16685 PLACEMENT VIOLATIONS
>> STAGE RESULT: PLACEMENT_FAIL
```

**16,685, not 1,202** — because the film scene is `assembly14` plus 16,027 more
meshes, and almost all of the new ones are at the origin too:

```
DB          11,246   at the origin      breach debris flakes (sim/apply_breach.py)
GS           3,796   at the origin      breach glass shards  (sim/build_breach_sim.py)
SPECX        1,159   at the origin      the crowd library
FW SW NOSE     ~450  at the origin      THE CAR ITSELF, and the driver in it
halo brake                              (front wing, side wing, nose, halo,
wheel DRV                                brakes, wheels, suspension, DRV_*)
suspension
Vitrine Plaque  ~24  x[-1, 14] y[-6, 0] the SHOWROOM SET around station 0
Barrier Bollard
BF GP           15   x ~ 14.9           the showroom floor / plinth
------------------------------------------------------------------------
16,685      of which 16,646 are within 3 m of the world origin
```

Read that list again. The three largest groups are prototype/rest-position
libraries at the origin — the same shape of finding as `SPECX_Lib*` — and the
next group is **the car**, which is inside `car_path` by construction because
`car_path` IS the car's swept volume, and at frame 1 the car is at station 0.

**`placement_gate` is a WORLD gate, and `film23_breach.blend` is not a world.**
`render/world/assembly/r2/SHIPPING.md` declares an *assembly* as the ship for
exactly this reason. A film scene additionally contains: the subject of the
car-path volume, the driver inside it, the showroom the car starts in and drives
out of, and two animated debris libraries. Reporting those as placement
violations is the instrument being pointed at something it was not built for.

The one number in that run that IS a world statement is
**`road_corridor: ARCH_Gantry +1.149 m`** — the same object and the same figure
the last trustworthy report (`v122`, on `assembly7`) recorded. **The racing
surface itself is clear, on the ship candidate, measured.**

### The same blend under the fixed gate

`work/r22701/gate_film23_breach_FIXED.json` (see R2-2709 for why this first run
was REFUSED and had to be repeated — the refusal was correct and it was my bug):

```
>> non-rendering: 15938 mesh(es) cannot appear in a frame where they stand
                  -- object.hide_render(evaluated)=15938
>> instances: 4966913 realised in 51.5 s; 11129 of them from a NON-RENDERING
   source and therefore measured at their instance matrix (868 per-vertex,
   10261 rejected on bounding box); 4955784 from visible sources are NOT
   measured -- declared
>> 16203 finding(s) belong to meshes that CANNOT REACH A FRAME where they stand

violations                  482        (was 16,685)
hidden_findings          16,203
violations from instances     0        of 11,129 crowd realisations measured
```

**Every remaining violation is the car, the driver in it, or the showroom set
around station 0** — `FW_ SW_ NOSE_ halo brake wheel suspension MB_ BB_ FD_ EC_
SP_ DRV_` (451 in `car_path`) and `Vitrine_ Plaque_ Barrier_ Bollard_ CI_ BF_
GP_ DeckType_` (31 in `camera_path`). **Zero `SPECX_`, zero `DB_`, zero `GS_`.**

And the 15,938 hidden meshes are not only the crowd library: at frame 1 the
11,246 `DB_*` debris flakes and the `GS_*` glass shards are hidden too, because
`sim/apply_breach.py` keys `hide_render` 1 → 0 at each flake's birth frame —
*"a flake does not exist before the crack that freed it opens"*. That is why the
predicate reads the EVALUATED object and not the stored boolean, and it is
controlled in both directions (R2-2705, section 9d).

### The camera really does pass 130 mm from a plaque, and the frame is clean

`camera_path Plaque_Surround −1.070 m` is the deepest surviving finding, and it
is not a rounding artefact: projecting the live camera path against the reported
point gives **0.130 m at frame 830**, 0.496 m from `Barrier_Post_7` at f798,
0.801 m from `Vitrine_Posts` at f883. Frame 830 of the proxy shows the camera
skimming the dais past the car with nothing clipped or intersected. So the 1.2 m
`CAM_CLEAR_R` sphere is doing what it should — flagging that the shot flies
through a set at hand's breadth — and the rendered evidence says the shot
survives it. **Reported, looked at, not a blocker.**

---

## R2-2709 — the determinism guard fired on MY change, and it was right

The first run of the fixed gate on `film23_breach.blend` did not produce a
verdict:

```
>> determinism: 2 pass(es), DIFFERED; scene walk 289de956b08f5b68
>> REFUSING TO REPORT: the same unchanged scene measured differently on repeat,
   in one process, with nothing touched between passes. Every number above is
   unciteable.
>> STAGE RESULT: PLACEMENT_NONDETERMINISTIC_REFUSED     (rc=3)
```

Cause, and it is entirely mine: I put `instances.walk_secs` — the **wall-clock
time to walk 4,966,913 instances** — inside the reproducibility fingerprint.
51.5 s is not 51.4 s, so the two passes could never agree, and every report of
every large world would have been unciteable for a reason with nothing to do
with the world. R2-2341's guard caught it on its first contact with real
geometry.

Two things changed:

* `walk_secs` is excluded from the fingerprint. It stays in the report body,
  where it is useful and harmless.
* `_fingerprint` was a **closure inside `main()`**, which no control could
  reach. It is now module-level `report_fingerprint(p)`, and `--selftest`
  asserts on the same function the verdict rests on: two passes of an unchanged
  scene must fingerprint identically, `walk_secs` must be in the report, and
  `walk_secs` must **not** be in the fingerprint.

Controls: **57 → 60**, `>> STAGE RESULT: PLACEMENT_SELFTEST_OK`
(`work/r22701/selftest_5.log`).

---

## R2-2710 — is the ship candidate clear to render?

**Yes for the world. The 482 findings that survive on the film scene are the
car, the driver in it, the set the camera skims, and the wall the car is
supposed to go through — and every one of them was checked by name.**

The citable run (`work/r22701/gate_film23_breach_FIXED2.{log,json}`,
`determinism: 2 pass(es), IDENTICAL`, both fingerprints `cf74c50385a1a9ac`):

```
>> non-rendering: 15938 mesh(es) cannot appear in a frame where they stand
>> instances: 4966913 realised in 56.9 s; 11129 from a NON-RENDERING source and
   therefore measured at their instance matrix (868 per-vertex, 10261 rejected
   on bbox); 4955784 from visible sources are NOT measured -- declared
>> closest approach, camera_path    Plaque_Surround   -1.070 m
>> closest approach, car_path       CI_seatpad        -1.602 m
>> closest approach, road_corridor  ARCH_Gantry       +1.149 m
>> determinism: 2 pass(es), IDENTICAL
>> 482 PLACEMENT VIOLATIONS
>> STAGE RESULT: PLACEMENT_FAIL  [+16203 hidden findings on 15938 non-rendering mesh(es)]
```

**16,685 → 482, and 0 of the 11,129 crowd realisations violates anything.**

Every one of the 482, adjudicated by name and by x-coordinate rather than
waved through:

| group | n | x span | what it is |
|---|---|---|---|
| `FW_ SW_ NOSE_ halo brake wheel suspension MB_ BB_ FD_ EC_ SP_ CI_ DeckType_` | 425 | −1.5 … 3.0 | **the car**, at station 0, inside its own swept volume by construction |
| `DRV_` | 8 | 0.0 … 0.3 | **the driver**, inside the car |
| `Plaque_ Vitrine_ Barrier_ Bollard_` | 24 | −0.6 … 13.5 | **the showroom set**, in `camera_path` — the shot flies through it |
| `BF_ GP_` | 15 | 14.92 … 15.08 | **the east glass wall and its aluminium frame** — `sim/eastframe.py`: *"there is no piece of them that can leave when the car goes through"*. This is the breach. The car is meant to be in it |

Nothing unaccounted for; no fence, no building corner, no tyre stack.

**And `road_corridor` is `ARCH_Gantry +1.149 m` — clear, on the ship candidate,
by its own measurement.** That is the same object and the same figure as the
last trustworthy world report (`v122`, `assembly7`), so the racing surface has
been clean throughout and the "nothing came near it" of the older reports was
purely the instrument.

### The honest qualification

`placement_gate` is a **world** gate and `film23_breach.blend` is not a world —
`render/world/assembly/r2/SHIPPING.md` declares an *assembly* as the ship for
exactly this reason. On a film scene it necessarily reports the subject of the
`car_path` volume as being inside `car_path`. **The verdict that means what it
says is the one on the assembly**, which is R2-2711.

Two further honest limits, both stated in the report rather than implied away:

* **It is a single-frame instrument** measured against whole-film volumes. At
  frame 1 the 11,246 `DB_*` flakes and 3,796 `GS_*` shards are hidden and at
  rest; where they are on the other 2,977 frames is a question nothing here
  asks.
* **4,955,784 realisations of visible sources are not measured** at their
  instance matrices. Counted and declared, not fixed.

Neither is a reason to hold the render. Both belong in the defect log.

---

## R2-2711 — the verdict that means what it says: `assembly14` is
   **`PLACEMENT_CLEAN`**

Same blend as the finding, same frozen inputs, live camera path, fixed gate
(`work/r22701/gate_assembly14_FIXED.{log,json}`):

```
>> subject: 30204 meshes via every mesh in the scene (nothing looks like context)
>> non-rendering: 894 mesh(es) cannot appear in a frame where they stand
>> instances: 4966913 realised; 11129 from a NON-RENDERING source, measured at
   their instance matrix (868 per-vertex); 0 of them violates anything
>> 1159 finding(s) belong to meshes that CANNOT REACH A FRAME where they stand
>> closest approach, camera_path    BR_Verge_R        +0.648 m   (ARCH_Gantry 0.031 m behind)
>> closest approach, car_path       BR_Concrete_L12   +4.608 m   (ARCH_PitWall 0.120 m behind)
>> closest approach, road_corridor  ARCH_Gantry       +1.149 m   (BR_Verge_R 0.705 m behind)
>> determinism: 2 pass(es), IDENTICAL
>> NOTHING is on the road, in the car's path, or in the camera's path
>> STAGE RESULT: PLACEMENT_CLEAN  [+1159 hidden findings on 894 non-rendering mesh(es)]
```

| | gate of record (`ab078e1`) | fixed gate |
|---|---|---|
| verdict | **`PLACEMENT_FAIL`, 1,202** | **`PLACEMENT_CLEAN`, 0** |
| where the 1,202 went | — | 1,159 `hidden_findings`, listed in full with reasons |
| `car_path` closest | `SPECX_Lib0853_turned_b0` **−1.6025 m** | `BR_Concrete_L12` **+4.608 m** |
| `camera_path` closest | `SPECX_Lib0664_stand_b7` **−0.6919 m** | `BR_Verge_R` **+0.648 m** |
| `road_corridor` closest | `ARCH_Gantry` +1.1491 m | `ARCH_Gantry` +1.1491 m |

**All three clearances are now positive and all three name real world
geometry.** Two of the three used to be a hidden prototype standing at the
origin, so the two numbers a reader was supposed to act on were about something
that is not in the film.

1,159 and not 1,202 because these runs use the **live** camera path rather than
the orphan the gate defaults to (R2-2706): `car_path` is 894 either way, and
`camera_path` goes 308 → 265. That is the size of the camera error, on this
world, and it is the second reason nothing about the old number was safe to
quote.

**Nothing needs to be deleted, moved, or hidden. The world is clean and was
clean.**

---

## R2-2708 — leases and files

Claimed under `R2_AGENT=r2-2701-crowd-placement`, one path at a time:

```
docs/STAGING-R2-2701-to-R2-2760.md   CLAIMED
tools/placement_gate.py              CLASH (r2-2641-land-debt) -> waited -> CLAIMED
```

`tools/placement_gate.py` was clashing when this task began. It was **not**
forced. `r2-2641-land-debt` landed it at `ab078e1` and released; the claim was
retried and granted, and the edit is on top of their committed version, not on a
stale copy.
