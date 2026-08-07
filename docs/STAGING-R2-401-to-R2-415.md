# STAGING R2-401 to R2-415 — the cockpit is too small for the driver: what it costs on screen, and what to do

Block owner: the driver-fit question left open by R2-241..R2-250.
`docs/DEFECT-LOG-R2.md` is NOT edited here.

**Verdict up front: ACCEPT IT.** The defect as stated does not exist on the
measured datum, the cheap fix makes the picture worse and fails the shipped
containment gate, and the expensive fix is a redesign of 24 % of the car. The
frames that prove it are `render/r2401/overlay_ab_f2635.png` and
`render/r2401/ab_f2632_full.png`.


## R2-401 — the driver is 92 % helmet, and that is the whole of the finding

`tools/r2401_part_mask.py` runs `driver_containment`'s instrument once per
GROUP: every car mesh `is_holdout`, `film_transparent`, one sample, 0.01 px
filter, opaque `material_override`, so alpha is 1 exactly where an unoccluded
DRIVER surface is frontmost. R2-241 measured how BIG the driver is. It did not
measure WHAT is on screen, and the whole question turns on that.

At **frame 2635**, the largest cockpit in the film with the driver present
(2.34 m, 80.4° above the aperture plane, 1,459 px/m):

| group | own pass | contribution to the rendered mask |
|---|---:|---:|
| all `DRV_*` that render | 172,468 px | — |
| helmet + balaclava | 157,999 | **157,999  (91.6 %)** |
| gloves | 11,157 | **11,157  (6.5 %)** |
| suit + HANS + harness + extras | 40,392 | **3,312  (1.9 %)** |

The torso's own pass is 40,392 px and only 3,312 of them survive into the
combined mask, because the helmet is in front of the rest of him. At frame
2632 it is **1,539 px of 132,155 — 1.2 %**.

Controls held. NEGATIVE: an all-hidden group returns **0 px** at both frames.
POSITIVE: the groups sum to MORE than the whole (209,548 vs 172,468 at f2635),
and the excess is exactly the mutual occlusion, so the groups do cover the
driver rather than silently missing part of him. The `all` figure at f2632 is
**132,155 px**, identical to R2-246's independently-run number.

**So the observation that started this is real.** The volume between the wheel
and the helmet is not a driver reading dark; it is the car's own seat, liner
and harness, with 1.9 % of a driver in front of it. `render/r2401/hollow_ab.png`
is the driver-present and driver-absent crops of that volume side by side and
the two are nearly identical.


## R2-402 — but "0.20 m below the cockpit rim" measures a joint centre against a rim 0.63 m in front of it

The number that opened this investigation is **0.207 m**, and it is
`docs/driver_placement.json`'s `anchors_local['shoulder_l']` z against
`CI_seal`'s **global maximum** z. Both halves are the wrong thing.

* `anchors_local` is `driver_figure`'s SKELETON, and it is also the module's
  PREDICTION — written to the report before `place_driver`'s −16.405 mm crown
  correction translated every emitted object. The glenohumeral joint centre is
  inside the body.
* `CI_seal`'s max z (0.7298) occurs at **x = +0.626**, at the scuttle. The rim
  directly outboard of the shoulder is lower and falls away forward — measured
  by `tools/r2401_cockpit_fit.py` in 50 mm slices: 0.6689 at x −0.15, 0.6645 at
  −0.10, **0.6310 at −0.05**, 0.6052 at +0.50.

Measured on the EMITTED MESH instead — the highest `DRV_Suit` vertex over each
deltoid, |y| 0.13..0.26, x −0.15..0.10:

| | z | vs CI_seal max 0.7298 | vs the rail beside it, 0.6310 |
|---|---:|---:|---:|
| suit shoulder, as built | **0.6003** | **0.1294 below** | 0.0307 below |
| the joint anchor it was read from | 0.5225 | 0.2073 below | 0.1085 below |

The gap between the two rows is **0.078 m**, which is the flesh over the joint —
a deltoid radius, and anatomically what it should be.

**On the surface datum the shoulder is 0.129 m below the rim, i.e. inside the
0.10–0.15 the reference is quoted as showing.** The defect is a datum mismatch
of 78 mm between a skeleton anchor and a surface reference.

This does not make R2-401 go away — 1.9 % is 1.9 % — but it does mean the
shoulder line is not the thing that is wrong, and moving it is moving something
that is already where it should be.


## R2-403 — there is no halo over the driver's head, and no engine cover either

`solve_hpoint`'s fourth fit check is `crown > halo_top + 0.01` → "the head is
outside the survival cell", against `halo_assembly_HoopTube`'s global max z of
0.8825. `tools/r2401_headroom.py` slices that tube along x:

| x | z range | nearest \|y\| | verts on the centreline |
|---:|---|---:|---:|
| −0.05 (the crown's x) | 0.6411 .. 0.7698 | **0.2892** | **0** |
| +0.00 | 0.7188 .. 0.7882 | 0.3252 | 0 |
| +0.85 | 0.8329 .. 0.8816 | 0.0026 | 1117 |
| +0.90 | 0.8366 .. 0.8825 | 0.0028 | 1097 |

The halo apex is the **front pillar junction at x +0.90**, 0.95 m ahead of the
crown. Over the head the halo is 0.29 m outboard and BELOW the crown. So the
check compares the helmet's height against a bar that is nowhere near it.

And `tools/r2401_cockpit_fit.py` fires 4,000 rays straight up off the helmet's
upper cap into a BVH of 176 car objects, 4,078,475 triangles: **0 of 4,000 hit
anything within 3 m.** There is nothing above the helmet at all. The stated
"0.054 m of headroom to the engine cover" is not a clearance; it is the gap up
to the bodywork's own silhouette line behind the head — `EC_shell` 0.9335,
`MB_chassis_cockpit` 0.9262 — and the true ceiling is the roll hoop
**`EC_hoop`, top 0.9529, i.e. 0.076 m** above the crown, not 0.054.

Not fixed here, because it changes a shipping gate's semantics: the fourth fit
check should read against `EC_hoop`, which is the object that is actually over
the driver.


## R2-404 — the window in which any of this can be seen is 25 frames

`tools/r2401_cockpit_sweep.py` projects the eight corners of the `CI_seal`
aperture box plus the driver landmarks through `render/film14_path.json` at
`world/car_anim_car.json`'s own per-frame car transform, for all 2,978 frames.
Frames counted only if ≥ 6 of 8 aperture corners land on the 3840 × 2160 frame
AND f ≥ 580, `place_driver --appear`, before which he is keyed hidden.

**2,201 frames (91.7 s) qualify.** Of those:

| helmet size | frames | seconds |
|---|---:|---:|
| ≥ 100 px | 356 | 14.8 |
| ≥ 200 px | 46 | 1.9 |
| ≥ 300 px | 15 | 0.6 |

and what a candidate correction is worth in pixels, over those 2,201 frames:

| move | median | p90 | max |
|---|---:|---:|---:|
| +54 mm | **6.9 px** | 28.9 | **78.8** |
| +77 mm (the datum gap of R2-402) | 9.9 | 41.2 | 112.3 |
| +135 mm (chest to the aperture's lower edge) | 17.3 | 72.2 | 197.0 |
| +229 mm (hip onto round 1's seat pan) | 29.3 | 122.5 | 334.1 |

The maxima all fall in one run, **f2628–f2652 — 25 frames, 1.04 second** — which
carries 6.5 % of the driver's total projected-size-time. Everywhere else the
whole argument is worth single-digit pixels.


## R2-405 — the first cut of that sweep nominated four frames where the cockpit is off screen

It asked whether the CROWN projected inside the frame plus a 200 px margin, and
returned f530–533 as the four largest cockpits in the film at **4,940 px/m**.
They are not. At f530 the camera is 1.27 m off the car and the aperture's eight
corners project to x 2,548..7,304: **one of eight** lands on a 3,840 px frame
and the crown is at x 3,591, off the right edge.

It was caught because `place_driver.figure_offscreen` had already measured
frames 448–530 as an OFF-SCREEN run, and the two disagreed. A single landmark
plus a generous margin is not an in-frame test; the aperture box is. Fixed, and
the fix is why R2-404's table is the real one.


## R2-406 — the +54 mm raise, built and rendered: it buys 6× the torso and fails containment

`tools/place_driver.py` gains `--hip-raise` (default 0.0, no behaviour change).
It lifts the H-point only; `wheel_rel = wheel_centre − H` is computed AFTER, so
the module **re-solves the arms down to the car's own grips** rather than the
gloves floating off them, which a rigid translation of the built figure would
do. Measured on the artefact: gloves **0.1 mm and 0.0 mm** from `SW_GripL/R`,
car witness **0 of 70** samples changed, install tracking 0.00000 m with the
2.518 m explode offset still seen.

`world/car_anim_driver_R2401_EXPERIMENT_raise54.blend`, against the shipping
build, at 4K/256 samples on the 5090:

| | base | +54 mm | |
|---|---:|---:|---|
| f2635 all driver px | 172,468 | 202,500 | +17.4 % |
| f2635 **torso visible** | 3,312 | 21,171 | **× 6.39** |
| f2632 torso visible | 1,539 | 9,417 | × 6.12 |
| suit shoulder z | 0.6003 | 0.6567 | |
| … below `CI_seal` max | **0.1294** | **0.0731** | **out of the 0.10–0.15 band** |
| helmet crown z | 0.8770 | 0.9310 | 0.022 under `EC_hoop` |

So it more than answers "how much of the gap does it close": on the joint datum
it takes 0.207 → 0.153, right onto the band's edge; on the SURFACE datum, which
R2-402 shows is the right one, it takes 0.129 → 0.073 and **overshoots the band
in the other direction.**

And then it fails the gate. `tools/driver_containment.py`, unmodified, on the
raised blend:

| frame | base: px / outside | +54 mm: px / outside | |
|---|---:|---:|---|
| 2635 | 172,468 / **0** | 202,500 / **208** | FAIL |
| 2632 | 132,155 / **0** | 155,204 / **13** | FAIL |
| 2625 | 23,441 / 0 | 32,068 / 0 | OK |
| 828 | 17,004 / 0 | 24,871 / 0 | OK |
| 700 | 15,978 / 0 | 22,297 / **6** | FAIL |

Both columns are the same unmodified instrument, run in the same session shape,
with the driver-absent control reading 0 px on all ten passes. The shipping
build reads **0 outside on all five frames including f2635**, which R2-249 had
never tested. The 208 px are
visible without the mask: in `render/r2401/raise54_f2635_crop.png` the shoulder
and HANS come through the monocoque skin as **gold wedges lying on the bodywork
outboard of the rim**, one above the cockpit on the engine-cover shoulder and
one below it on the tub flank. `render/r2401/overlay_ab_f2635.png` outlines
them.

That is the trade in one line: **+17,859 px of torso inside the cockpit, bought
with 208 px of driver on the outside of the car.**


## R2-407 — and it does not fix the thing it was supposed to fix

The complaint is the volume between the wheel and the helmet. The chest is at
z 0.450. The cockpit aperture's LOWER edge — `CI_seal` min z — is **0.5849**.
The chest is 0.135 m below the hole it would have to be seen through, so at
+54 mm it is at 0.504 and still 0.081 m below it. Compare
`render/r2401/base_f2635_crop.png` with `raise54_f2635_crop.png`: that volume is
the same dark tub in both. What the raise moved was the helmet and the shoulder
tips, not the chest.

To put the chest in the aperture takes **+135 mm**, at which the crown reaches
1.012 — **0.059 m above the roll hoop `EC_hoop`**, i.e. the driver's head
standing proud of the car. There is no height at which this figure's torso is
visible through this car's cockpit opening and his head is still inside the car.

A smaller raise was not built. It is not motivated: on the surface datum every
millimetre of raise moves the shoulder further out of the reference band, and
the leak is caused by the shoulders reaching the tub sides, which begins as soon
as they rise.


## R2-408 — what supplying corrected cockpit geometry at apply time would actually cost

`sim/apply_breach.py`'s R3 is the precedent and it is worth reading precisely:
it deletes **ten `GW_Right_Glass_*` objects of four vertices each** — zero
thickness planes on x = 15.000, which cannot be glass at any distance — and
supplies ten laminated panes. Un-animated, one material, no fasteners, no
seams, and the module that supplies them owns the breach anyway.

The cockpit is not that. Measured on `world/car_anim.blend`:

* the `CI_*`/`MB_*` cluster is **32 objects, 1,120,084 polygons, 24.4 % of the
  car's 4,598,601**, across 8 procedural materials;
* **all 32 are animated** — every one carries beat 1's explode path, and
  `place_driver` exists in its current form because a single action datablock
  shared with `CI_seat` rewrote the car's own assembly flight (R2-245);
* `MB_chassis_cockpit` alone is 182,225 polygons and is the surface the halo
  mounts, the seal, the fasteners and the imperfection pass all land on.

And there is no room underneath. To put the hip on the seat pan the pan and the
cell floor drop **0.229 m**. `MB_cell_floor`'s underside is at 0.3860 and
`MB_chassis_cockpit`'s lowest surface at 0.3704; the plank is at 0.0400, the
skids at 0.0389, `MB_underpan` spans **0.042 .. 0.160**. The corrected floor
would land at 0.157 — inside the underpan — so the underpan, plank, skids and
plank bolts move too, and the tub sides and the sidepods that meet them follow.
Raising the opening 0.13 m instead redraws the car's silhouette and the halo
mounts with it.

All of that lands on the object beat 1 is a 33-second close pass over.
Measured from the camera path: **189 frames (7.9 s) with the camera inside 2.0 m
of the cockpit, 323 frames (13.5 s) inside 3.0 m**, and a peak scale of
**70 px per millimetre** at f556, 0.09 m off the skin. New geometry would have
to match round 1's weave, rivet pitch and seam lines at that scale, hand-built,
with no repeated assets — for a defect worth 6.9 px at the median frame.


## R2-409 — RECOMMENDATION: accept it

**Accept.** Ship `world/car_anim_driver.blend` as it stands.

Why the others lose:

* **Raise into the headroom — loses on the pictures and on the gate.** It does
  not fill the hollow (R2-407): the chest cannot reach the aperture. It moves
  the shoulder OUT of the reference band on the datum that measures a surface
  against the rim above it (R2-402/R2-406). It puts 208 px of driver through the
  monocoque at the film's largest cockpit frame and fails
  `tools/driver_containment.py` at 3 of 5 frames. And 208 px of gold on the
  bodywork is a defect a viewer can point at, where 1.9 % vs 10.5 % of torso
  inside a dark cockpit is not.
* **Supply corrected geometry at apply time — loses on cost and on risk.** It is
  1.12 M polygons and 32 animated objects across 24.4 % of the car, it has to
  displace the underpan and the plank to find the 0.229 m, and it lands on the
  hero object of a 33-second close pass that peaks at 70 px/mm. `apply_breach`'s
  precedent replaced forty vertices that could not be right at any distance;
  this would replace a quarter of the car to move something by 6.9 px at the
  median frame. In a one-take film with zero cuts, every seam of it has to hold
  for 2,978 frames.
* **Accept — costs nothing and is defensible from the frames.**
  `render/r2401/base_f2635_crop.png` is the worst case: 2.34 m, 80° above the
  aperture, the largest the cockpit ever gets with a driver in it. The helmet is
  seated, the hands are on the wheel (`overlay_base_f2635.png` outlines both
  gloves in blue at the rim), the shoulder line sits 0.129 m under the rim
  which is where reference puts it, and the cockpit reads as a cockpit. The
  volume forward of the helmet is dark because it is the seat and the liner of
  a car whose cockpit sides are above its driver's shoulders — which is what a
  modern F1 cockpit looks like from above.

What IS worth doing, and is cheap: **R2-403's fit check**. `solve_hpoint`'s
halo test is comparing the crown against a bar 0.95 m forward with no geometry
over the head. It happens to pass on the shipping build, so it is not urgent,
but it is a gate that is not measuring what it says it measures, and the next
person to move the driver will be stopped or waved through by the wrong number.
Point it at `EC_hoop`.


## R2-410 — what I could not confirm

* **The reference band itself.** "Reference shows 0.10–0.15" was given to me,
  not measured here, and no external reference may be fetched. Everything above
  is conditional on it. If the band is meant against the rim rail directly
  outboard of the shoulder rather than the cockpit's highest line, the shipping
  build reads 0.031 and is too HIGH, and the raise makes that worse, not better
  — the recommendation is unchanged either way, which is why I have not chased
  it further.
* **A raise smaller than 54 mm was not built** (R2-407 gives the reason).
* **`--fit-warn-only`** is new and refuses unless `--out` contains
  `EXPERIMENT`. It has been exercised once, on the one blend it was written for.
* **The look scene is not the film.** `tools/build_driver_look.py` ships the
  car, the driver, the contract sun and sky — no track, no grandstands, no
  showroom — so the visor mirrors a cleaner sky than the film will. That is the
  same scene the R2-241..250 evidence was shot in, so the A/B is like-for-like,
  but neither is the shipping frame.
* **f2635 was never in `driver_containment`'s frame list** before this block.
  R2-249's 0-outside result was measured at 2632/2625/828/700/1200/2100. The
  base build has now been run at 2635 and reads 0 outside there too —
  `docs/r2401_containment_base.json`. Nothing else in the shipping build was
  re-verified; this block changed no shipping artefact.


## Artefacts

    tools/r2401_cockpit_fit.py       geometry off the emitted mesh + the ceiling BVH
    tools/r2401_headroom.py          what is above and behind the head; the halo profile
    tools/r2401_cockpit_sweep.py     px/m and camera elevation, all 2,978 frames
    tools/r2401_part_mask.py         the helmet / arms / torso pixel split
    tools/place_driver.py            + --hip-raise, + --fit-warn-only  (defaults unchanged)

    docs/r2401_cockpit_fit.json      docs/r2401_cockpit_fit_raise54.json
    docs/r2401_headroom.json         docs/r2401_cockpit_sweep.json
    docs/r2401_part_mask_base.json   docs/r2401_part_mask_raise54.json
    docs/r2401_placement_raise54.json
    docs/r2401_containment_base.json docs/r2401_containment_raise54.json

    render/r2401/base_f2635_crop.png     render/r2401/raise54_f2635_crop.png
    render/r2401/ab_f2635_full.png       render/r2401/ab_f2632_full.png
    render/r2401/overlay_ab_f2635.png    render/r2401/overlay_ab_f2632.png
    render/r2401/silhouette_ab_f2635.png render/r2401/hollow_ab.png

    world/car_anim_driver_R2401_EXPERIMENT_raise54.blend   NOT FOR SHIPPING
