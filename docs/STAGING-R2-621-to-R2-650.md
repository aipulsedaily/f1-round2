# STAGING — R2-621 to R2-650 · the showroom ceiling

Findings staged here for `DEFECT-LOG-R2.md`. Nothing in this file edits the
defect log. Work tree: `/home/zany/f1-round2`. Owner: the ceiling agent
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
not claim to.** Whether three area lamps of 4.6 × 3.4 m, 5.0 × 3.4 m and
4.8 × 0.62 m floating at 2.8 – 4.6 m are camera-visible in beat 1 is a live
question this work did not settle: `Fill` at (4.2, 5.6, 2.8) and `Rim` at
(-6.6, 1.8, 3.2) both fall inside frame 1's 90 ° horizontal and −39/+19 °
vertical span. **Recommended as its own finding for whoever picks it up.**

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

**(c) Every `itemkit.NT` builder already returns a socket tuple.**
`t.noise(...)`, `t.vor(...)`, `t.ramp(...)`, `t.math(...)`, `t.maprange(...)`
all return `(node, index)`. Wrapping one again as `(noise_result, 0)` makes
`pin()` read it as a colour and raise `NodeSocketFloat.default_value expected a
float type, not tuple`. 19 of them in the first draft of the materials. Loud,
at least — but the failure was *inside* a Blender `-P` script, which **exits 0**,
so it only became a verdict because `gate_exit.guard` was wired in from the
first line.

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

### the invariant this design turns on

Nothing here is new light and nothing is under a light. The two cove annuli are
housed in open, splayed, white-lined slots; the panel field is 50 mm below the
`Cove_Coffer_*` soffit so the sealed strips of R2-624 stay sealed; every new
surface is at or below z 6.185; the six round-1 spot rods keep their rods, cans
and lenses and gain only a canopy at the surface they pass through.
