# R2-241 to R2-246 — the driver, and the three ways he got into the car wrong

**Block R2-241..R2-255. Used: R2-241 to R2-246. `docs/DEFECT-LOG-R2.md` is not
mine to edit; this is the staging file the entries would come from.**

---

## R2-241 — the cockpit was empty for all 2,978 frames, and nobody had measured
what it was worth

`docs/ITEM-PRESENCE-CENSUS.md` scores `driver_figure` **MID / 220.7 px** and
lists it `ABSENT`. Both halves were understated.

Measured with `render/film14_path.json` (the film's own camera) against
`world/car_anim_car.json` (the car's own per-frame transform), with occlusion by
a BVH of all **9,629,183 car triangles built once in CAR_ROOT-LOCAL space** — so
the camera is transformed into the car each frame rather than the car into the
world, which makes an exact 2,978-frame occlusion sweep cheap:

| probe | peak px | peak SHARP px | frames visible | frames sharp | ≥200 px | closest |
|---|---:|---:|---:|---:|---:|---:|
| helmet (0.26 m) | 1312.4 | **366.0** | 2164 | 1838 | 151 | **1.226 m** |
| cockpit opening (0.40 m) | 1934.3 | 323.8 | 2278 | 1922 | 391 | 1.279 m |
| shoulders / arms | 667.3 | 347.4 | 1905 | 1575 | 224 | 2.093 m |

Per beat, helmet, sharp: beat 1 **209.7**, beat 2 **190.2**, beat 3 119.0,
beat 4 46.2, beat 5 **366.0**, beat 6 7.7. The peak is frame **2632** — 2.42 m
away, 78 % of the helmet unoccluded, car dead straight at 81.5 m/s.

**Both controls held.** POSITIVE: the same instrument on the rear wing reports
1738 visible frames. NEGATIVE: a probe **buried inside the monocoque** reports
**0 visible frames of 2978** while its raw projected size peaks at 25,611 px —
so the occlusion term is live and the metric does not read the same
present-or-absent.

**366 px sharp is 17 % of frame height, held above 200 px for 151 frames, on
screen and unoccluded for 2164 of 2978 frames (73 % of the film).** That is HERO
presence. `driver_figure.py`'s 1,608,502-triangle build is the right tier and is
kept unchanged; its tessellation is set by explicit section counts, not by the
`NEAR_M = 3.0 / LENS_MM = 21.0` header assumption, so nothing was owed there.

## R2-242 — the fit, and the part of it that cannot be fixed

Round 1's cockpit tub offers **0.249 m** of hip-to-headrest rise where a 1.78 m
man needs **0.552 m**, and `/home/zany/opus5-car-render` is READ-ONLY.
`driver_figure.PACKAGE['round1_note']` had already recorded this and recommended
moving the CAR. The car cannot move, so the DRIVER is re-solved onto it:

* `WHEEL_C` overridden from `(0.300, 0, 0.393)` to the measured
  `(0.300, 0, 0.3147)` — **78.3 mm** — and `WHEEL_TILT_DEG` from 25.00 to the
  measured **22.01**. The gloves then land **0.1 mm and 0.0 mm** from the car's
  own `SW_GripL/R` bars.
* helmet crown **0.147 m above the cockpit rim**, **5.5 mm under the halo apex**;
* ankles inside `CI_pedals` in both x and z;
* hip **0.229 m below the seat pan** — i.e. the pelvis and legs are inside the
  monocoque. Invisible, and `tools/driver_containment.py` measures that rather
  than asserting it.

**The fit frame matters.** Frame 1 is mid-explode: the cockpit interior sits
2.443 m above home until about frame 500. `measure_car` refuses any frame where
`CI_seat` is more than 20 mm off home.

## R2-243 — `driver_figure.build(place=)` took the figure apart, limb by limb

`Acc.emit` recentres every mesh on its bounding box and stores the offset in
`ob.location`. `build()` then applied the placement with

    o.matrix_world = Mw @ o.matrix_world

`matrix_world` is a DERIVED value the depsgraph writes; on an object created
moments earlier it can still read IDENTITY. For the objects emitted late in
`build()` the right-hand side was `Mw @ IDENTITY` and the assignment **discarded
the recentre offset**.

MEASURED: `DRV_Helmet` — emitted second — landed on its predicted crown height.
`DRV_Glove_L` — emitted sixth — landed **209 mm from its own grip anchor**, with
`matrix_basis.translation` equal to the placement translation alone and a raw
mesh centroid of `(0.151, 0.0015, 0.1454)` against an anchor at
`(0.2986, 0.1081, 0.3182)`. The module printed `>> driver_figure: 10 objects,
1608502 triangles` and reported success.

Fixed to go through `matrix_basis`, which is composed from stored loc/rot/scale
and is never stale, so the result is order-independent. A four-way unit test
(`WHEEL_C`, tilt and grip-offset overrides, crossed) confirmed the module's own
solve was correct all along: the bug was purely in how the answer was written
back.

## R2-244 — the install empty rode 408 m behind the car

`e.matrix_parent_inverse = root.matrix_world.inverted()` was sampled while the
scene sat on the fit frame, where `CAR_ROOT` is 400 m down the circuit. That
inverse was baked in permanently. `verify_install` caught it at **408.890 m**.
The empty now copies `CI_seat`'s own parent inverse and the `DRV_*` objects hang
off it with an identity inverse.

## R2-245 — keying the driver's appearance rewrote the CAR's seat animation

The empty was given `CI_seat`'s **own** action datablock so it would ride the
assembly. `key_appearance` then inserted `hide_render` keys through it and
forced every keyframe in the action to `CONSTANT` — into the car's action, on
the car's seat, in a blend the car is supposed to pass through untouched. The
explode-offset control went **2.518 m → 104.398 m**.

Two fixes: the empty gets a **copy** of the action, and it is excluded from the
appearance keying. And a **car witness** now brackets the entire run — seven car
objects (`CI_seat`, `CI_seatpad`, `CI_headrest`, `SW_Shell`, `CI_liner`,
`MB_chassis_cockpit`, `halo_assembly_HoopTube`) sampled for translation, rotation
and `hide_render` at ten frames, 70 samples, compared before and after and
refusing to save if any changed. **0 of 70 changed.**

## R2-246 — the left boot came through the chassis skin

`tools/driver_containment.py` renders the driver's coverage as an **alpha
mask**: every car mesh is set `is_holdout`, so it punches a transparent hole
while still occluding, and with `film_transparent` the alpha channel is 1
exactly where an unoccluded driver surface is frontmost. One sample, 0.01 px
filter, opaque `material_override` — binary, no denoiser, nothing to threshold.

(The first cut used the `IndexOB` pass through the compositor and died on
`Scene.node_tree`, which **Blender 5.2 removed**; Blender still exited 0.)

Frame 2632: **132,426 driver pixels, 0 in the driver-absent control**, and
**82 outside the cockpit aperture** in a 10 × 14 px blob 198 px from the hull.
Frame 700: 222 px in a 38 × 13 px blob. Raycasting those exact pixels named
**`DRV_Boot_L` at 3.075 m with `MB_chassis_fwd` 5 mm behind it**.

Same root cause as R2-242, one axis over: the tub is **24 mm too short** as well
as 0.23 m too shallow. The boots are set back by the measured overlap against
`CI_footwell`'s bulkhead — **31.3 mm left, 70.2 mm right** — which leaves the
ankle inside the trouser and inside a footwell nothing can see into.

---

## When the driver appears, and why it is not a pop

The opening shot is the problem: at frames 1–3 a driver riding the seat's
explode path would float **2.44 m above the car, 452 px tall, dead in frame**;
pinned at the home position he would sit in mid-air at 209 px. Neither is
acceptable and neither was noticed until the explode offset was projected.

Measured off-screen runs for a 12-point hull of the whole figure, after the
interior lands: **448–530** and **540–623**. He is keyed hidden until frame
**580** — 40 frames inside the second run — and the gate re-projects the hull
over frames 572–588 and refuses if any is on screen. **0 of 17 were.**

## Pose

`straight`, not the manifest's `hairpin_apex`. At the peak frame the car is dead
straight at 81.5 m/s, and **the car's own `SW_Shell` euler is constant across
every frame sampled — this steering wheel never turns.** A driver holding 62° of
lock on a straight is the first thing an eye catches.

## The placement path — not R2-182's

The driver goes into the CAR, and the car is **appended** into the film from
`world/car_anim.blend` by `tools/build_film_scene.py --car`. So
`tools/place_driver.py` writes `world/car_anim_driver.blend` = `car_anim.blend`
+ `DRV_*`, and the film is built with `--car` pointed at it.
`tools/build_film_scene.py` is untouched (hard constraint 7), and so is the car.
A world-side placement stage would have left the driver at a fixed world point
while the car drove away from him.
