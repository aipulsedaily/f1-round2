# STAGING — R2-621 to R2-650 · the showroom ceiling

Findings staged here for `DEFECT-LOG-R2.md`. Nothing in this file edits the
defect log. Work tree: `~/f1-round2`. Owner: the ceiling agent
(R2-508 handback).

Artefacts:

| what | where |
|---|---|
| the geometry, one definition | `world/items/showroom_ceiling.py` |
| the post-append build tool | `tools/r2621_ceiling_build.py` |
| the cheap iteration scene | `work/ceiling/make_room.py` -> `work/ceiling/room.blend` |
| the frame-coverage instrument | `work/ceiling/probe_campath.py` |
| the set census | `work/ceiling/probe_ceiling.py` |
| build reports | `work/ceiling/build_room.json`, `work/ceiling/build_film17.json` |

---

## R2-621 — R2-504's architecture claim is TRUE, and it is now confirmed from two independent directions rather than quoted

R2-504 and R2-508 both rest on one structural claim: the showroom enters the
film **downstream of the world assembly**, so no assembly rebuild can ever
reach it and the only place a ceiling can land is a post-append operation on a
built film blend. The briefing asked for that to be re-derived rather than
believed. It holds, and here is the derivation, which does not go through
either defect-log entry:

* `render/world/assembly/r2/assemble.py` imports exactly seven world modules —
  `build_surface`, `build_barriers`, `build_terrain`, `build_architecture`,
  `build_dressing`, `build_items`, `build_sky`. None of them authors a
  showroom. There is no eighth import and no showroom collection anywhere in
  the assembly path.
* `tools/build_film_scene.py:316` declares
  `SET_COLLECTIONS = ("SHOWROOM", "PROPS", "LIGHTS")` and appends all three
  from `world/car_anim.blend` at identity, *after* the assembly is open.
* Measured on `world/car_anim.blend`: `Ceiling` is in collection `SHOWROOM`,
  `matrix_world.translation = (0, 0, 0)`, **8 vertices, 6 polygons**, and its
  two largest faces are **686.25 m² each**. Exactly as R2-504 says.

So the fix is a post-append tool, and `tools/r2621_ceiling_build.py` is one, in
the shape `tools/add_dais_ramp.py` established: open the film that exists,
assert the datum it lands against, build into it, save elsewhere.

**One thing in R2-504 has since been fixed and the entry is now stale about
it.** R2-504 was written when `assemble.py` swallowed module exceptions
silently; it now prints `>> ASM MODULES FAILED: ...` and
`>> ASM MODULES RETURNED AN EMPTY SUMMARY: ...`. That hole is closed.

---

## R2-622 — the ceiling is in 57 frames of beat 1, not 792, and the number that matters is not the count

R2-508 is right that the ceiling is in frame 1. The summary that has travelled
with it — *"the beat runs 33 seconds, a quarter of the film's runtime, inside
it"* — invites the reading that the ceiling is in shot for 33 seconds. It is
not. MEASURED on `world/camera_rig.blend` (the rig built 2026-08-04 15:49, the
same one `film16.blend` carries — its `render/film16_path.json` frame 1 is
`p = [-0.8409, -8.8633, 3.7566]`, `lens = 18.0`), by ray-casting a 33 × 19 grid
of image-plane directions against the plane z = 6.200 clipped to the room
footprint, for every frame of beat 1:

```
frames   1 -  19    19 f    ceiling  5.26 % .. 21.05 % of frame   lens 18.0 -> 23.6
frames 296 - 333    38 f    ceiling  1.12 % .. 15.79 % of frame   lens 35.0
---------------------------------------------------------------------------
57 of 792 beat-1 frames.  FRAME 1 IS THE MAXIMUM AT 21.05 %.
```

The other 735 frames of beat 1 have zero ceiling in them: the camera spends
them between -23 ° and -30 ° of elevation on the parts field.

**That count understates the exposure, and the render is what shows it.**
Two of this room's four walls are a specular curtain wall. In the BEFORE frames
at f300 and f320 — rendered here through the film's own grade — the cove rings
appear *reflected* across most of the picture, in frames whose direct ceiling
fraction is 8.8 % and 15.8 %. The ceiling is in more of beat 1 as a reflection
than as a subject, and any future measurement of "is the ceiling in shot"
that only ray-casts the ceiling plane will keep missing that.

**Consequence for anyone budgeting this work:** the correct priority argument
for the ceiling is *"it is 21 % of the film's first frame and it is mirrored
down two walls"*, not *"it is a quarter of the runtime"*. Both justify the
work. Only one of them is true.

---

## R2-623 — "its lamps hang from nothing" is half true, and the half that is false is the ceiling half

R2-508 says of the 23 interior practicals: *"Its lamps hang from nothing."*
MEASURED on `world/car_anim.blend`, every LIGHT object with its z and the
round-1 geometry within 0.5 m of it:

```
z 5.590   Spot_0 .. Spot_5      6 lamps   HAVE FIXTURES ALREADY:
                                          SpotRod_i  z 5.800 .. 6.140  36 mm sq
                                          SpotCan_i  z 5.11 .. 5.59  194 v / 240 p
                                          SpotLens_i z 5.11 .. 5.38   98 v / 144 p
z 4.600   Key                   1 lamp    4.60 x 3.40 m area, NO fixture
z 3.200   Rim                   1 lamp    4.80 x 0.62 m area, NO fixture
z 2.800   Fill                  1 lamp    5.00 x 3.40 m area, NO fixture
z 2.56/2.32 WallWash_* x4       4 lamps   wall-mounted, at the light line
z 0.620   Kick                  1 lamp    NO fixture
z 0.450   Bollard_Lamp_0..7     8 lamps   bollard bodies in PROPS
z 0.160   FloorGraze            1 lamp    floor slot
```

So: **the only lamps at ceiling level are the six spots, and all six already
have a rod, a can and a lens** from `s05_lighting_v2.build_spot_rig`. What they
do not have is anything to hang *from* — the rods terminate at z 6.140 in mid
air, 60 mm under a 686 m² quad, which is a different and smaller defect than
the one the briefing describes. It is fixed here with six canopies placed
against each rod's own measured station.

The four genuinely unhoused lamps are `Key`, `Fill`, `Rim` and `Kick` — the
car rig, at z 0.62 to 4.60. **A ceiling cannot fix those, and this work does
not claim to.**

**But the obvious follow-on defect is NOT there, and the negative is worth more
than the suspicion was.** `Fill` (5.00 × 3.40 m) and `Rim` (4.80 × 0.62 m) both
fall inside frame 1's cone — measured against the real frustum at frame 1
(18 mm, half-angles 45.00 ° h / 29.36 ° v, camera at (-0.8409, -8.8633,
3.7566)):

```
Fill    az +19.28   el  +6.21   15.3 m   IN FRAME
Rim     az -28.52   el  +7.01   12.1 m   IN FRAME
Kick    az +40.65   el -25.10    6.9 m   IN FRAME
Key     az +62.55   el +22.31    8.1 m   outside (az beyond 45 deg)
```

In Cycles a camera-visible area lamp renders as a glowing rectangle, and two
5 m panels hanging in mid-air in the film's first frame would be a far worse
defect than a flat ceiling. **They do not render.** MEASURED with
`work/ceiling/lampvis.py`: `visible_camera` is **False on all 23 practicals and
on `SKY_Sun`** — round 1 turned it off on every one. `>> STAGE RESULT:
LAMPVIS_CLEAN`.

Also measured there, and it is why the canopy work matters: `Spot_1`, `Spot_3`
and `Spot_5` are all inside frame 1 at el +16.6 to +17.4 °, near the top of the
picture. `Spot_5`'s rod at (0.0, 7.0) lands inside slot 2, so its canopy is on
the slot head, in shot, at frame 1.

---

## R2-624 — `Cove_Strip_0` and `Cove_Strip_1` are sealed inside `Cove_Coffer_0` and `Cove_Coffer_1`, and deliver no light at all

Found while measuring clearances for the ceiling, on `world/car_anim.blend`:

```
Cove_Strip_0    x -12.50 .. 12.50   y -7.86 .. -7.34   z 6.100 .. 6.120   CoveEmitAmbient
Cove_Coffer_0   x -12.60 .. 12.60   y -7.98 .. -7.22   z 6.090 .. 6.220   CeilingMat
                                                     -> STRICTLY INSIDE, all six faces
```

Same for the +Y pair. `Cove_Coffer_*` is an opaque `CeilingMat` box built by
`s02_showroom`; `Cove_Strip_*` is an emissive box built by
`s05_lighting_v2.build_coves`, which describes them as the ambient wash that
*"keeps the far corners off the floor of the histogram"* and spends a whole
paragraph tuning them from radiance 4.8 to 2.4. **They are inside a closed
opaque box.** Two × 13 m² of emitter delivering nothing.

They are still counted: `showroom_lighting.measure()` reports
`interior_emission_strength_sum = 405.5185` and both strips are in it. So that
figure is not a measure of light in the room.

**THIS IS NOT FIXED HERE AND SHOULD NOT BE.** It is round-1's, the tree is
read-only, and unsealing them would change beat 1's light — the film's
exposure, its black budget and every graded frame already shipped were all
measured with them sealed. The ceiling's panel field is set at **z 6.040,
50 mm below the coffers' 6.090 soffit**, precisely so the coffers are concealed
without being disturbed, and `tools/r2621_ceiling_build.py` refuses to build if
a coffer soffit is at or below the panel datum.

---

## R2-625 — THE FIRST OCCLUSION PROBE WAS THE WRONG INSTRUMENT, and it convicted a light slot of having walls

Worth staging as a method finding, because it is the third instrument on this
project to fail this way and the failure mode is the same each time.

The ceiling houses the two cove emitters in recessed light slots. To prove it
had not stolen their light, the build tool fired nine fixed ray directions from
sample points on each emitter into the downward hemisphere and **failed the
build on any hit**:

```
>> OCCLUSION: 6912 rays from 2 emitter(s) over 127920 new tris -> 2110 hit(s)
     Cove_Ring blocked at [3.949, -0.054, 5.809] (0.307 m)
     Cove_Ring blocked at [4.946,  0.180, 5.845] (0.629 m)
>> STAGE RESULT: CEILING_OCCLUDES_EMITTER
```

Every hit was on the reveal, at 35 ° and 70 ° from nadir. A recess has walls by
definition, so the probe was asking a question whose only clean answer is "do
not build a recess". And the verdict carried **no information about how much
light was actually lost** — 2,110 of 6,912 is not 30 %, because the nine
directions were not distributed by anything.

Replaced with the integral that actually predicts the picture: the
**cosine-weighted** fraction of the downward hemisphere that reaches the room,
which is proportional to the flux a Lambertian emitter delivers. Directions are
drawn by Malley's method (uniform on the disc, projected down), so the
estimator is unbiased and needs no per-ray weight. Two verdicts come out of it
and only one is a refusal:

* `nadir_blocked` — anything directly under an emitter. A refusal at any
  transmittance, because that is building under a light.
* `transmittance` — reported against a floor of 0.70.

**And then the corrected instrument changed the design.** The first cut of the
slots — parallel walls, the project's dark beam paint — measured

```
Cove_Ring       0.66      (analytic, 2-D slot model)
```

a third of two coves given away to their own reveal. That is a real defect the
hit-counter could not have shown and could not have sized. The fix is what a
real building does: **splay the reveal and line it matt white**, because a
light cove's reveal is a reflector, not a shade. Measured on the built mesh,
24,576 rays:

```
Cove_Ring        0.9008 cosine-weighted downward, nadir blocked 0 / 96 points
Cove_RingOuter   0.8554 cosine-weighted downward, nadir blocked 0 / 96 points
```

and both numbers UNDERSTATE what the room keeps, because the intercepted
fraction lands on an 0.82-albedo matt white reveal and mostly comes back.

---

## R2-626 — three build-time traps, each caught by a control that already existed or was written for it

Staged because all three are cheap for the next agent to re-hit.

**(a) The slot head, built downward, was inside the round-1 slab.** The plenum
deck was emitted as `ring(r0, r1, Z_DECK, Z_DECK + 0.030)` with `Z_DECK =
6.185`, i.e. up to z 6.215 — **inside** `Ceiling`'s 6.200 ..  6.500 cuboid,
where it would have rendered as a 686 m² quad slicing across the new work.
Caught on the first run by `showroom_ceiling.selftest()` check [8], which
compares every declared new surface against `Z_SLAB`, and again on the built
mesh by the tool's `z_probe()`. Now 13 mm thick, built upward into the 15 mm
gap: highest new surface z 6.1980.

**(b) `itemkit.hash01` takes INTEGERS, and neither failure is loud.**
`hash01("tray")` raises `ValueError: invalid literal for int()`. Worse,
`hash01(6.04)` silently returns `hash01(6)` — `int()` truncates — so every
tray in a 1.07 m column would have come back with the *same* per-instance
value while the source looked varied. That is the project's named headline
failure (one asset spammed) arriving through a helper that looks like it
prevents it. `showroom_ceiling._h()` maps strings through FNV-1a and quantises
floats to millimetres before calling it.

**(d) A per-instance attribute that was silently constant — the project's own
headline failure wearing the clothes of the fix for it.** The ceiling's
variation is driven by a per-island float attribute the materials read as
`pnl`. The emitter baked it under the name **`isl`**, and it baked the raw
island **index**. Two independent faults, either alone fatal:

* the name did not match, so `ShaderNodeAttribute("pnl")` evaluated to a
  constant 0.0 and 72 apron segments came out one flat white across 17 m — in
  the part of the ceiling that IS frame 1 (R2-627);
* even with the name fixed, an index running 1, 2, 3 … 72 into a mix factor
  that clamps at 1 makes every segment past the first identical anyway.

Nothing failed. The build passed, the material-depth floor passed (the
attribute node is present and wired), and the render was plausible. It was
found by *looking at* the first frame and asking why 72 segments were one
tone. `_emit()` now hashes the island id through `_h` and bakes it as `pnl`,
and `showroom_ceiling._variety()` is the control: 560 of 560 trays get a
distinct value, against a negative-control arm feeding `hash01` the raw floats
which collapses to **190 of 560** — so the control can fail, and does.

**(c) Every `itemkit.NT` builder already returns a socket tuple.**
`t.noise(...)`, `t.vor(...)`, `t.ramp(...)`, `t.math(...)`, `t.maprange(...)`
all return `(node, index)`. Wrapping one again as `(noise_result, 0)` makes
`pin()` read it as a colour and raise `NodeSocketFloat.default_value expected a
float type, not tuple`. 19 of them in the first draft of the materials. Loud,
at least — but the failure was *inside* a Blender `-P` script, which **exits 0**,
so it only became a verdict because `gate_exit.guard` was wired in from the
first line.

---

## R2-629 — A GUARD WHOSE CONDITION CAN NEVER BE MET IS INDISTINGUISHABLE FROM A GUARD THAT IS WORKING, RIGHT UP UNTIL YOU NEED IT

Stated as a law, because this pass turned up three members of the same family
and this is the cleanest statement of it.

`film16.blend` is 7.5 GB and this box is 11 GB with six agents on it. After the
first landing attempt drove the machine to 36 of 43 GB of swap, I put the retry
behind a memory gate:

```
if [ "$AVAIL" -ge 9 ] || { [ "$AVAIL" -ge 4 ] && [ "$SWAPFREE" -ge 25 ]; }
```

**Free RAM on that box never reaches 9 GB.** The gate would have waited for
ever, logged nothing, and looked like caution. It had the shape of a
safety mechanism and the behaviour of a decision not to do the work — and
nothing would have reported the difference, because a gate that is waiting and
a gate that can never open produce the same output: silence.

It is the same shape as the rest of this pass:

* R2-625's occlusion probe — a check whose only clean answer was "do not build
  a recess", so passing it meant not doing the work;
* R2-626(d)'s per-instance attribute — present, wired, node-count-clean, and
  constant;
* and this.

The correction is not a bigger number, it is **the right term**. What actually
went wrong was swap EXHAUSTION (7 GB left, with another agent independently
loading the same 7.5 GB film), so swap headroom is the term that matters and
free RAM is the term that does not. The gate now needs 5 GB of RAM **or** 2 GB
plus 18 GB of swap headroom, and it opened within seconds of being re-armed.

**The paired instinct is worth keeping too:** the gate yields rather than
gambles. If swap free drops under 3 GB it kills MY attempt, because when swap
runs out the kernel picks the victim and it may not be me. Giving up my own
15 minutes is cheap; OOM-ing another agent's four-hour bake is not.

---

## R2-630 — I reported a broker stall that was a scene push, and the status line said so in plain text

Recorded against myself, because it is the instrument-reading failure this
project keeps finding and I made it while writing up the last one.

I reported broker 8760 as **stalled**: `running ... no progress reported yet`,
`0/5 frames (0%)`, `done` frozen at 1,910, idle climbing past 600 s. Every one
of those readings was true and the conclusion was wrong. The broker was
**sending a 7,507 MB scene at 13.71 MB/s** — nine minutes of push — and the
probe showing 0/5 frames was queued behind it, exactly as it should be.
`rq status` prints `sending <scene> <size> <elapsed> <rate>` in plain text and
I did not read that line before drawing a conclusion from the ones underneath
it.

Two things follow:

* **"No progress" is not a symptom until you have checked what the thing is
  doing.** A transfer in flight and a hung worker look identical from the
  frame counter alone, and only one of them is a defect.
* **There is a second broker.** `VASTRENDER_URL=http://127.0.0.1:8761` — an
  exclusive card (`gpu_frac 1.0`), measured **1.64× faster** on adjacent frames
  of the same scene (36.6 s vs 59.9 s), with 79.4 GB free against 8760's 9.0 GB.
  The standing routing policy is bulk to 8761 and stills to 8760 on cache
  economics, but that assumes 8760 is *available*; committed to a 7.5 GB push
  and then a 21-hour pass, it is not. The six 4K A/B jobs were cancelled on
  8760 and requeued on 8761, which woke it from `stopped` inside one poll.

---

## R2-631 — the 7.9 GB round trip should not exist, and the fix is the shape the showroom already uses

Asked to move the film landing onto broker 2 via `rq exec`, because the local
box was 4 GB from swap exhaustion and the landing was its largest consumer.
The landing was stopped immediately — it was minutes from being killed by its
own swap guard having achieved nothing, and stopping it took the box from
39 GB of swap back to 24 GB.

**The write-back was never the problem.** Broker 2's own measured fetch rate is
**8.3 MB/s**, so 7,969 MB comes home in about 16 minutes. Fine.

**The INPUT is the problem, and `rq exec` cannot solve it:**

* An exec job's whole input is a BUNDLE from a local root. There is no
  supported way to hand it a scene that already sits in the render worker's
  cache — `execservice.ensure_ready` deliberately reuses whatever scene the
  render worker holds, and says in its own comment that *"an exec job must
  never restart the render worker."* So the film would have to travel as an
  `--include`.
* `execremote.push_bundle` compresses with a **hardcoded `zstd -19 -T4`** and
  has no level selection. The SCENE path has one, and it exists because `-19`
  was measured feeding a 4-5 MB/s wire at **1.3 MB/s** on a 4.22 GB push while
  the receiving ssh sat at 0.0 % CPU. Bundles never needed that fix because a
  bundle is meant to be ~7.9 MB of code.
* `docs/agents.md` states the intent in one line: **"Ship code, not blends"**,
  and *"the `.blend` is born where the render happens."*

So the farm route means compressing 7.9 GB at `-19` on a box already at load
20+, to send the farm a file it already has, to get back a file we already know
how to make. **The round trip is worse than waiting** — which was the answer
the request explicitly invited, and it is the correct one.

### the third option, which removes the round trip permanently

The showroom is already solved this way. `tools/build_film_scene.py` appends
`SHOWROOM`, `PROPS` and `LIGHTS` from `world/car_anim.blend` at identity —
while the film blend is open and about to be saved anyway. A ceiling that ships
as a library collection joins that list and costs the pipeline **nothing**,
because the open and the save are already paid for by the film build.

`tools/r2621_ceiling_library.py` emits it:

```
LIBRARY R2_SHOWROOM_CEILING: 21 objects, 73,996 polys, 9 material(s)
lights 0, FILE images 0, emissive materials 0
highest surface R2C_CoveLiner at z 6.1980 (slab soffit 6.200)
saved world/showroom_ceiling.blend  6.99 MB  in 12.1 s
```

**6.99 MB against 7,969 MB — 1,140x smaller than the artefact the round trip
was for.** It REFUSES to write a library carrying a light datablock, a FILE
image, an emissive material, a material below the depth floor, or anything
above the slab soffit, so the consumer does not have to re-verify it.

Round-tripped rather than assumed — `work/ceiling/append_test.py` appends it
into the showroom scene in exactly the shape `build_film_scene.py` uses:

```
appended R2_SHOWROOM_CEILING: 21 objects, 73996 polys
LIGHTING BEFORE / AFTER   46,203.313 W  23 lamps  mark 3.628   IDENTICAL
assert_levelled PASS
appended ceiling spans z 5.5705 .. 6.1980 (slab soffit 6.200)
>> STAGE RESULT: APPEND_OK
```

The three lines that land it, next to the existing `SET_COLLECTIONS` append:

```python
with bpy.data.libraries.load("world/showroom_ceiling.blend", link=False) as (src, dst):
    dst.collections = ["R2_SHOWROOM_CEILING"]
scene.collection.children.link(dst.collections[0])
```

`tools/r2621_ceiling_build.py` is kept for landing on a film that already
exists, which is still the right tool when somebody wants that and has the
memory for it.

---

## R2-632 — the build summary's `z_extent` was QUOTED FROM THE CONSTANTS, and it was wrong by 190 mm

Found by the library's own append test, which is the point of having one.

`showroom_ceiling.build()` reported `"z_extent": [Z_PRI_BOT, Z_DECK + DECK_T]`
— the primary beam's bottom flange and the deck's top, straight from the
module's constants. The append test asserted the appended mesh's lower bound
against that number and **failed on the geometry**:

```
appended ceiling spans z 5.5705 .. 6.1980
appended ceiling bottom z 5.5705 is not the built 5.760
```

The mesh is right and the summary was wrong. The lowest thing on this ceiling
is **a track head barrel**, not a beam: the heads hang off the secondary
soffit at 5.874, drop a stem, and their barrels tilt down to 5.5705. The
declared extent was 190 mm shallow and had been in every report since the
first build.

Nothing would have caught it. It is a number the module states about itself,
computed from the same constants a reader would check it against, so it agrees
with the source and disagrees with the artefact — the same shape as R2-626(d)'s
constant attribute and R2-629's unmeetable guard. `_measured_z_extent()` now
reads it off the emitted meshes.

---

## R2-627 — what is actually in frame 1, measured, and why the ceiling was designed around it rather than around the plan

The obvious way to build this ceiling is a waffle grid over the whole plan.
That was built — 428 trays on the curtain wall's own mullion bays, 9 primary
Vierendeel girders with 246 web posts, 13 secondary downstands, 152 sprinklers,
64 unlit track heads, 8 diffusers — and then the first render showed that in
**frame 1 none of it is visible.**

The geometry is unforgiving and it is worth writing down, because it applies to
anything anyone builds up there. The camera is at z 3.7566 looking 10.00 ° down
with an 18 mm lens. As a ceiling point gets FURTHER from the camera its
elevation angle DECREASES, so the far half of the room compresses into a thin
band just above the wall line and the ceiling directly overhead sits at the top
of the frame. At frame 1 the ceiling enters at 6.95 m horizontal — y ≈ −1.9 —
so the frame's ceiling band runs from y ≈ −1.9 (top of frame) to y = 11.25
(the wall). Everything past about r = 9 m is foreshortened into a few dozen
pixels.

**So the only ceiling that shows in the film's first frame is the part within
about 8 m of the turntable's axis** — which is exactly the part the two round-1
cove rings already occupy. That is why this ceiling is a concentric feature 17 m
across (drum, light slot, ring beam, apron, ring beam, light slot, ring beam,
apron) with the waffle field outside it, and why the aprons are **panelled into
48 and 72 segments on a constant 0.70 m arc** and populated with 54 fittings
rather than left as smooth annuli: in the shot that matters, they ARE the
ceiling, and two smooth white rings read as a light fitting rather than a
building.

The waffle field is not wasted — it is what shows at f296–333, where the camera
is 9 to 12 m from the far ceiling and the primary girders and their web posts
read clearly. But it is not what carries frame 1.

---

## R2-628 — the build, and what it is verified against

`tools/r2621_ceiling_build.py`, run on a film blend. Adds only; creates no
light and no emissive material.

```
21 objects, 73,996 polygons, 88,500 vertices, built in 2.7 s
9 materials, all procedural, 0 image texture nodes
```

Verifications, all on the built mesh, all in the same run:

```
LIGHTING BEFORE  scene_mark 3.628  46,203.313 W  23 lamps  7 emissive mats  405.5185
LIGHTING AFTER   scene_mark 3.628  46,203.313 W  23 lamps  7 emissive mats  405.5185
                 -> IDENTICAL. read with showroom_lighting.measure(), never a
                    hand-rolled probe.
assert_levelled  PASS, called UNCONDITIONALLY before the save, not in a branch
GRADE            AgX, look 'None', exposure -3.628, re-asserted via film_exposure
COVE TRANSMITTANCE  Cove_Ring 0.9008, Cove_RingOuter 0.8554, nadir blocked 0/96
Z CEILING        highest new surface z 6.1980 against the slab soffit 6.200
MATERIALS        every one >= 3 texture nodes, >= 2 bump nodes, 0 image nodes,
                 and Principled's Normal socket LINKED -- checked by NAME,
                 because Blender 5.2 moved it from index 5 to 6 and index
                 feeding shipped 14 dead bump stacks on this project
```

`gate_exit` tokens: `CEILING_BUILT` / `CEILING_MEASURED_OK` pass;
`CEILING_VACUOUS` refuses; `CEILING_LIGHT_DRIFT_FAIL`,
`CEILING_UNDER_EMITTER_FAIL`, `CEILING_REVEAL_FAIL`,
`CEILING_INSIDE_SLAB_FAIL`, `CEILING_MATERIAL_FLAT_FAIL`,
`CEILING_NOT_SAVED_FAIL` fail. Every one was checked against
`gate_exit.code_for` rather than assumed — the first four tokens drafted mapped
to CRASH because they contained none of the project's markers, which
`gate_exit` says out loud rather than guessing them into a pass.

### how it composes with the rebuild agent's film, WITHOUT racing them

`tools/build_film_scene.py` is in flight — `film16.blend` was built from
`assembly10.blend` at 16:26 on 2026-08-04 while this work was going on — so
nothing here edits it. The ceiling is a separate post-append stage, exactly as
`tools/add_dais_ramp.py` is, and it chains onto any film blend:

```
blender -b render/film16.blend --factory-startup \
    -P tools/r2621_ceiling_build.py -- --out render/film16_ceiling.blend
```

It is idempotent (`itemkit.purge(PFX, COLL)` first), so re-running it on a
blend that already has a ceiling replaces it rather than doubling it, and it
re-asserts every datum on the way in, so a newer film with a moved set stops it
rather than getting a ceiling in the wrong place.

**One operational note, not a defect in anything.** The box is 11 GB and
`film16.blend` is 7.5 GB. The first attempt to land the ceiling on it read
6.9 GB, drove the machine to 36 of 43 GB of swap and had not reached its first
print in 13 minutes, while six agents' jobs competed for the same page cache —
including a second, independent load of the same `film16.blend`. It was killed
rather than allowed to OOM somebody else's bake.
`work/ceiling/land_on_film.sh` re-runs it behind a memory gate and picks up
whatever the newest `film1[6-9].blend` is when the window opens.

### the frames, and what is still owed

Rendered from the film's OWN camera (`ONER`, the rig `film16.blend` carries),
in a scene carrying the real `SHOWROOM` / `PROPS` / `LIGHTS` collections at
identity, through the real grade (AgX, look `None`, exposure −3.628) with
`showroom_lighting.apply()` on and `assert_levelled` PASS:

```
work/ceiling/ab/before_f0001.png   f1    round-1 flat ceiling   |  MATCHED PAIRS,
work/ceiling/ab/after_f0001.png    f1    ceiling, FINAL         |  same instrument,
work/ceiling/ab/before_f0300.png   f300  round-1 flat ceiling   |  same settings,
work/ceiling/ab/after_f0300.png    f300  ceiling, FINAL         |  960 px / 48 spp
work/ceiling/ab/before_f0320.png   f320  round-1 flat ceiling
work/ceiling/peep/after_f0001.png  f1    ceiling, FIRST CUT (kept: it is the
work/ceiling/peep/after_f0300.png  f300  control R2-625's design change is
                                         measured against)
```

What the pairs show, and they show different things on purpose:

* **f1** — before is one flat quad with two glowing annuli painted on it and no
  thickness anywhere. After is the concentric feature: ribbed stepped drum over
  the turntable, two splayed white light slots with the coves recessed in them,
  three ring beams, two segmented aprons with their fittings, and a perimeter
  shadow gap at the wall head.
* **f300** — before is a flat khaki band above the wall with a single corner
  line in it. After is the WAFFLE FIELD: the primary Vierendeel girders read
  clearly with their web posts, the secondaries cross them, and the outer ring
  beam curves through. This is the pair that justifies building the field at
  all, because R2-627 shows none of it reaches frame 1.

f1, f300 and f320 are the three beat-1 stations that look up: f1 is the
establishing frame (21.05 % ceiling), f300 and f320 are inside the second run
(8.8 % and 15.8 % direct, and both dominated by the ceiling's reflection in the
curtain wall).

**Still owed, both blocked on shared infrastructure rather than on the work:**

* **The 4K A/B.** Six jobs — f1, f310, f320, before and after, 3840 × 2160 at
  220 samples — queued on the broker at 17:23 as
  `r2621_room_before.blend` / `r2621_room_after.blend`. Estimated ~10 min of
  GPU at $0.4203/hr, about **$0.07**. They have sat unserved for ~25 min while
  the broker stayed on scenes other agents kept re-feeding, and the GPU worker
  restarted once mid-wait (`gpu starting-worker`) and then held a
  `breach-continuity` job at "no progress reported yet" with the served count
  stuck at 1,910. My scenes are now FIRST in the waiting list. Reported, not
  worked around — this looks like the known `cheaper_to_finish()` scene-switch
  condition plus a worker stall.
* **The landing on `film16.blend`.** Running, and it is I/O bound rather than
  wedged: `showroom_lighting.classify()` touches every object's `bound_box`,
  which pages in the whole 7.5 GB file. MEASURED on the second attempt — 9.94 GB
  read, then **471 KB in 30 s** once three other agents' jobs (including an
  independent `film16_breach.blend` at 3.1 GB) took swap back down to 9 of
  43 GB free. It will finish when the box gives it a window and not before.
  Handed off self-healing rather than babysat:
  `work/ceiling/land_on_film2.sh` retries on the newest `film1[6-9].blend`,
  and `work/ceiling/swap_guard.sh` kills MY attempt if swap free drops under
  3 GB — giving up my work rather than gambling with somebody else's bake.

  **The first gate was itself a defect worth recording.** It required 9 GB of
  free RAM on an 11 GB box shared by six agents, which never happens, so it
  would have waited forever while looking careful. What actually went wrong on
  attempt one was swap EXHAUSTION (36 of 43 GB used, 7 GB left), so swap
  headroom is the term that matters and free RAM is the term that does not.

### the invariant this design turns on

Nothing here is new light and nothing is under a light. The two cove annuli are
housed in open, splayed, white-lined slots; the panel field is 50 mm below the
`Cove_Coffer_*` soffit so the sealed strips of R2-624 stay sealed; every new
surface is at or below z 6.185; the six round-1 spot rods keep their rods, cans
and lenses and gain only a canopy at the surface they pass through.

---

## R2-633 — the relief statistic: the contaminated-band finding is real, the fix I proposed for it is NOT, and the known-truth ladder is what said so

Three separate things, and they have to be kept apart because two of them
survive and one does not.

### (a) the contaminated band — STANDS

`relief_reads_as_lip_and_shade` gates on a dip measured over a band that MIXES
the half that moved when the sun crossed sides with the half that did not —
relief diluted by paint. The gate computes the undiluted number, prints it in
brackets, and does not gate on it:

```
kerb_precast_unit      mixed +0.0301   light-driven +0.2963
asphalt_wearing_course mixed -0.0027   light-driven +0.3463
showroom_facade_panel  mixed -0.0679   light-driven +0.3151
```

Six of the fifteen relief FAILs invert on the undiluted number.

### (b) `ok_bal` CANNOT FIRE ON ITS OWN WORST CASE — STANDS, AND IS INDEPENDENT

`tools/item_gate.py:3071`:

```python
ok_bal = (foc is None or focc is None or foc >= focc)
```

The spectral-balance clause **silently PASSES when it cannot be measured**, and
`foc` is `None` exactly when `fine_subject` or `coarse_subject` is zero — a
surface with no energy in a band, which is the wave-1 signature the clause was
written to catch ("all the energy sat at r8-r16 and none at r1-r4"). It fires on
everything except the thing it exists for. `crew_fireproof_overall` and
`driver_figure` both report `spectral balance None` and both are let through it.

**Fix it with VACUOUS, the verdict this project already has for an arm that
cannot pass on an empty set.** Silently passing is the one option that is
definitely wrong. This is worth doing whatever happens to (a).

### (c) the proposed swap — FAILS ITS CONTROLS, AND IS WITHDRAWN

Two independent controls, in order.

**The known-bad set.** `crew_fireproof_overall` is MUST-REJECT and the dip
clause is the ONLY check currently failing it. Its light-driven dip is +0.1612 —
a PASS. Swapping statistics moves the gate from 1 false-accept to 2. **(a) was
incidentally covering for (b)**, which is why the swap looked free and was not,
and why anyone who fixed the dip in isolation would have concluded their fix was
bad and reverted it.

**The 15-specimen known-truth ladder** (`render/relief_2light/truth_table_*.json`,
already rendered — no new GPU work). Both rules scored AS THE GATE ACTUALLY RUNS
THEM, i.e. the dip clause AND `light_amplitude` together:

```
A vs B  (the gate's own runner-up sun -- the OPERATIONAL case)
    CURRENT  14 / 15        PROPOSED  14 / 15     tied; both miss e_bolts_3mm
A vs C  (180 deg reversal)
    CURRENT  13 / 15        PROPOSED  12 / 15     proposed loses e_bolts and l_cyl_rib
```

**On the ladder the proposed rule is a wash at the operational geometry and
worse at the reversal. It is not an improvement and it is not landing.**

### the puzzle this leaves, which is the actual next question

Isolating the dip clause alone, PROPOSED beats CURRENT 12/15 to 9/15 on A vs B —
CURRENT passes six painted decoys that the light-driven dip rejects. Combined
with `light_amplitude` the difference vanishes, because **`light_amplitude` is
already doing all the paint rejection** (paint decoys measure x0.02-1.40 against
its x2.00 bar).

So on the ladder the dip clause contributes almost nothing. On the ITEMS it
rejects 15 of 21 while `light_amplitude` passes every one of them at x29-x427.
**Those two facts cannot both describe a healthy statistic**, and the ladder
cannot say which is wrong because it contains no specimen resembling a real item
— every panel is a single-material plate, cylinder or sphere, and the items are
multi-material bodies at 170-2333 px/m.

**The missing control is a ladder specimen that looks like an item.** That is
the next measurement, it needs renders, and it should be built before anyone
touches the dip clause again.

---

## R2-634 — `driver_figure` reads as INVERTED relief, and the corrected statistic convicts it harder

Flagged rather than fixed, because the gate is unsettled and fixing an item
against a statistic under review is how rework gets done twice.

```
driver_figure    mixed dip        -0.0137
                 light-driven     -0.2289      <- worse, not better
                 spectral balance  None        <- and unmeasurable, per R2-633(b)
```

Both of the gate's relief routes convict it, and the sharper one convicts it
harder. This is not one of the six that invert. The driver was specifically
asked for, is in the cockpit, and is on screen in the hero shot — so of the
three items reading as inverted relief (`grandstand_riser_unit` -1.2396,
`dais_delivery_ramp` -0.2460, `driver_figure` -0.2289) this is the one that
reaches the picture. Whoever reworks the figure should have the corrected
number, not the mixed one.
