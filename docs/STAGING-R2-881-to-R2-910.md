# STAGING R2-881 to R2-910 — the driver and the seat in the overhead cockpit shot

Block owner: the client's note — *"when we have that one clip right on top of
the F1 car looking down, you see the imperfections in the driver and the seat,
so fix that as well."*

`docs/DEFECT-LOG-R2.md` is NOT edited here.

---

## Driver

### R2-881 — the shot is f2633–f2639, and it is the only one of its kind in the film

The client described a near-overhead look into the open cockpit. That is not a
matter of interpretation: `docs/r2401_cockpit_sweep.json` already projects the
`CI_seal` aperture box through the film camera for all 2,978 frames, and with
the driver present (`--appear 580`) there are **exactly seven frames above 70°
of elevation over the aperture plane**, all consecutive:

| frame | px/m at 4K | elevation | depth | aperture corners in frame |
|---:|---:|---:|---:|---:|
| 2633 | 1403.4 | 70.1° | 2.43 m | 8/8 |
| 2634 | 1441.7 | 75.7° | 2.37 m | 8/8 |
| **2635** | **1458.9** | **80.4°** | **2.34 m** | 8/8 |
| 2636 | 1458.1 | 82.3° | 2.34 m | 8/8 |
| 2637 | 1442.7 | 79.8° | 2.37 m | 8/8 |
| 2638 | 1414.3 | 75.5° | 2.41 m | 8/8 |
| 2639 | 1375.8 | 70.6° | 2.48 m | 8/8 |

There is nothing else in the film remotely like it. **f2635 is the framing**,
and every number in this section is quoted at it: 2.34 m, 32 mm, 1458.9 px/m,
3840 × 2160. The camera is identical in `film14_path.json` and
`film16_path.json`, so the framing has not moved since R2-401 measured it.

`render/r2881/film16_f2635_AS_SHOT.png` is that frame rendered from the
shipping `render/film16_breach.blend` through the real grade — **the picture
the client watched**, not a proxy for it.

### R2-882 — DRV_Helmet shipped with a 30 mm hole in the top of it

This is the defect. It is not a matter of taste and it is not a judgement call.

`build_helmet` lays the shell as a spun `(S, N) = (264, 512)` grid and builds
faces **only between adjacent rows**:

    IDX = i0 + np.arange(S * N).reshape(S, N)
    Q = np.stack([IDX[:-1, :], IDX[:-1, j1], IDX[1:, j1], IDX[1:, :]], -1)
    acc.quads(Q[ok], MAT_PAINT, True)

`HELM_KEYS[0]` is `(z 0.1520, a 0.0180, b 0.0200, …)` — the top key has
**non-zero half-axes**, so row 0 is a real ring of 512 distinct vertices and not
a degenerate point. There is no `acc.cap` and no `acc.fan` anywhere in
`build_helmet`. Row 0 was a raw open mesh boundary.

Measured on the artefact, in the helmet's own local frame, counting edges used
by exactly one face:

| | boundary edges in the top 8 % of the mesh | opening |
|---|---:|---|
| before | 672 | **30.2 mm across = 44 px at the framing** |
| after | 160 | 1.7 mm across = 2 px |

The 160 that remain are the inner liner's own uncapped ring (`Sl, Nl = 96,
160`), which sits 21.5 mm inboard behind a now-opaque shell and cannot be seen
from any camera. **Not fixed here, and it should be** — it is the same one-line
omission and it is listed under "what I have not fixed" below.

**Why it was never caught.** It is invisible from every angle except directly
above, and the film looks down into the cockpit exactly once, for the seven
frames in R2-881. In `render/r2881/film16_f2635_AS_SHOT.png` it is a hard,
perfectly circular black disc in the middle of the helmet — and the helmet is
**91.6 % of every driver pixel in that frame** (`docs/r2401_part_mask_base.json`:
helmet + balaclava 157,999 px of 172,468). It is also the *sharpest* thing in
the frame, because f2634 carries the worst camera rotation step in the entire
film (12.957°/frame) and everything else is smeared by the shutter while a hard
high-contrast edge survives it.

The fix caps it as a real crown, not a lid: an ellipsoid-of-revolution dome
whose base slope is set equal to the shell's own (−2.833 lateral, −3.083
fore-aft) so it meets tangentially and trades no crease for the hole, with
`da/dz → −∞` at the apex, which is what a sphere does at its pole. Rings step
down geometrically to 0.30 mm before the fan closes them, so the fan spans
0.9 px at the framing and cannot itself read as a pole.

**How much of the film was exposed to it.** The hole faces straight up, so its
visibility is a function of camera elevation over the aperture. From the same
sweep, driver present and ≥ 6 of 8 aperture corners in frame:

| elevation | frames | seconds | px/m range |
|---|---:|---:|---|
| ≥ 30° | 337 | 14.04 | 82 – 1459 |
| ≥ 45° | 84 | 3.50 | 138 – 1459 |
| ≥ 60° | 30 | 1.25 | 221 – 1459 |
| **≥ 70°** | **7** | **0.29** | **1376 – 1459** |

Everywhere except those seven frames the scale collapses — at 221 px/m a 30 mm
hole is 6.6 px, and at 82 px/m it is 2.5 px. **The one place in 2,978 frames
where this defect is large enough to be unmistakable is the shot the client
named.** They found the worst case by eye.

### R2-883 — the profile was piecewise-linear, and printed a crease ring at every key

`_helm_profile` was `np.interp` through 11 keys. Interpolated linearly and then
smooth-shaded, that has a tangent break at every key. Near the crown they are
savage: the segment (0.1520, 0.0180) → (0.1400, 0.0520) runs at dR/dZ = **2.83**
and the next at **1.60**, a **12.6° normal jump across one mesh row**. On a
shell 826 px wide that prints as a hard conical crease ring, one row wide and
therefore aliased. Three of them, at z = 0.140, 0.120 and 0.090.

Replaced with Fritsch–Carlson monotone cubic Hermite — *not* the `catmull`
already in the file, because the half-widths are **not monotone in z** (`a`
peaks at z = −0.04) and an unlimited cubic overshoots at the turn, which would
put a bulge in the shell that the reference has none of. Fritsch–Carlson limits
the end slopes to the secants and cannot overshoot.

Measured, dihedral angle across every interior edge in the top 35 % of the
mesh — the part the overhead camera sees — same instrument both sides:

| | edges | median | p99 | > 6° | > 10° |
|---|---:|---:|---:|---:|---:|
| before | 131,432 | 0.671° | 18.94° | 6,396 | 3,609 |
| after | 144,558 | 0.798° | 18.12° | **3,319** | **2,214** |

**Creases over 6° are down 48 %, over 10° down 39 %.** What remains is real
design geometry — the duct slots, the spoiler step, the louvres — which are
*supposed* to be creases. The median rises slightly because the cap adds 13
rings of genuinely curved surface.

### R2-884 — the crown was also carrying 512 sliver quads at 10.6 : 1

`helm_surface` distributed rows by a raised cosine, `g = 0.5 − 0.5·cos(πSS)`,
which has **zero slope at both ends**. That crowded 39 of the 264 rows into the
top 20 mm: row 0 → row 1 was 0.0209 mm against an azimuthal step of 0.2209 mm.
Degenerate slivers are where implicit vertex normals go noisy, and this ring
was dead centre of the driver in the shot.

Blending 12 % of a linear ramp in takes the crown step to ~0.145 mm and moves
**nothing** elsewhere — both curves pass through (0,0), (0.5,0.5) and (1,1), so
the rim end and the mid-shell are sampled exactly where they were.

### R2-885 — the relief encoding threw the sign away and then saturated

This one is worth stating carefully, because it is the mechanism behind a gate
verdict that has been on this module's record since 3 August.

`build_helmet` packs its surface relief into the `seam` vertex channel:

    aux = np.stack([np.clip(np.abs(d) * 120.0, 0, 1), …

Both halves are wrong.

* **`abs` throws the sign away.** The +5.2 mm duct fairing and the −11.0 mm
  slot at its leading edge encode identically, so the shader puts the same
  bright edge on both. A raised thing and a sunk thing render the same.
* **`* 120` saturates at |d| > 8.33 mm.** The +14 mm rear spoiler and the
  −11 mm slot both become **flat 1.0 plateaus**. A constant has no gradient and
  a Bump node reads gradients, so across the interior of the two largest relief
  features on the helmet the shader contributed exactly nothing.

The item gate's verdict on `driver_figure` reads:

> the features on this surface are single-value marks: they have no sunward lip
> and no lee shadow, which is how a printed decal behaves and not how a
> physical object does

That is a precise description of `clip(abs(d) * 120, 0, 1)`. **The gate named
the disease correctly.** See R2-886 for why it nevertheless was not looking at
the patient.

Now encoded signed about 0.5 at 25 units/metre — the convention this file
*already* documents and uses for its four `liv` channels, where one channel unit
is 40 mm. `d` spans −11…+14 mm and lands in 0.225…0.850 with headroom at both
ends and nothing clipped. `mat_paint` decodes it; `wall()`'s own vertices move
from 0.0 to 0.5 so the aperture walls no longer carry a phantom half-unit
(20 mm) step across them; `mat_foam` on the liner sees a constant either way and
is unaffected.

### R2-886 — the gate's verdict on this module was measured on the wrong object, at the wrong scale

**Do not read this as the gate being repaired or overturned.** Its relief
statistic is disputed and under active repair by another agent, and nothing here
depends on which way that lands. The point is narrower and it is checkable
without adjudicating the statistic at all: **whatever the gate measured, it was
not measuring the surface the client is looking at.**

`render/items/driver_figure/gate_run.log`:

> witness frame: subject **`DRV_Suit`** — largest of 10 objects by bbox diagonal
> (1.58 m)

and

> item driver_figure hero=True **filmed at 3.0 m on a 21 mm lens** … 747 px/m

Three independent mismatches, each measurable:

1. **Wrong subject.** The image checks (relief, microstructure, silhouette) run
   on `DRV_Suit` alone. At f2635 the suit's group contributes **3,312 px of
   172,468 — 1.9 %** (`docs/r2401_part_mask_base.json`). Helmet + balaclava is
   **91.6 %**. The subject was chosen automatically as the largest bounding-box
   diagonal, which on a seated figure is the torso — the one part of him the
   car hides. The module's own manifest entry says so in as many words:
   *"Only the helmet, shoulders, upper arms and hands are ever visible above the
   cockpit rim."*
2. **Wrong scale.** `docs/item_manifest.json` declares `nearest_camera_m: 3.0`
   and `lens_at_closest_mm: 21`, giving the gate's 746.7 px/m. The real closest
   framing with the driver present is 2.34 m on a **32 mm** lens = **1458.9
   px/m**. The film shows this item at **1.95× the linear detail the gate judged
   it at** — nearly 4× the area. Every scale-dependent threshold the gate
   applied (`detail_limit_px` 6.0, band radii r1 = 1.339 mm) is computed at the
   wrong scale; at the real framing r1 = 0.686 mm.
3. **Wrong artefact.** The gated blend predates the on-disk one. This turned out
   not to matter — see R2-887 — but it is a third reason the verdict and the
   picture are not the same measurement.

**The honest summary is not "the gate was wrong".** It is: the gate described a
real defect mechanism (R2-885) in language that turned out to fit the helmet
exactly, while pointing at a surface that is 1.9 % of the picture, at half the
resolution the film uses. The client found the actual defect — a hole — by
looking at the frame. That is the finding.

### R2-887 — the staleness does not explain anything, and here is the check

The verdict rests on a 29 July artefact; the on-disk blend is 3 August and a
fresh remote build (4 August 19:17,
`~/vast-render/out/exec/da704fff70a8/driver_figure_test.blend`,
196,695,551 bytes) was sitting unclaimed. It is byte-identical to
`render/driver_figure_FRESH.blend` already in the tree (md5
`ad2a929dc6c40a214983d99a08ee1f2c` for both), so it needed no landing.

**Everything above was measured against the FRESH build**, not the gated one.
`docs/r2881_probe_fresh.json` is that probe. It says the staleness was never the
story:

* **All 14 materials feed `Principled BSDF.Normal`, resolved by name, with a
  live Bump behind it.** The "14 dead bump stacks" failure mode is *not*
  present here — this module hand-rolls its own socket-guarded `NG._feed`, which
  addresses inputs by string. The index-5/6 hypothesis is refuted.
* The defect in R2-882 is present in the fresh build. So is R2-883, R2-884 and
  R2-885.

So: **two independent defects on one module, as suspected — but the second one
is not "the relief reading". It is that nobody had rendered this object from
above.**

### R2-888 — the livery is sprayed paint with no thickness

Every livery band is composited into Base Color and into **nothing else**. The
four `liv` SDF channels never reach the bump chain and never reach Roughness, so
each colour break is a step in albedo across a surface that stays perfectly,
continuously smooth. On a shell 826 px wide that reads as a decal, which is what
it is.

Fixed by feeding a 0.30 mm transition ramp on each channel's `|sdf − 0.5|` into
both the coat and the base normal at **0.09 mm** of step — two colour coats plus
clear. That is a **physical** number and deliberately *not* taken from
`itemkit.relief_amplitude_for`: that law sizes a sinusoid to a target radiance
modulation, and this is a step whose height is set by how much paint is on the
helmet. (The law was consulted for the bands where it does apply — at the film's
12.47° sun a 0.28 modulation on the 4.65 mm orange-peel band wants 0.046 mm, and
the existing peel stack is already at ≈0.19 modulation, so it was left alone.)

The base lobe was also seeing `peel × 0.4` and nothing else — a mirror under a
clear coat of only 0.36 weight, so most of the response came off a perfect
surface. It now gets the paint edge and the decoded shell relief too, because
both are *below* the clear coat in a real paint stack.

### R2-889 — the fix does not move the driver, and it still passes containment

The crown gained a 2.68 mm dome, so the first thing to check is whether the
figure moved in the car. It did not. `tools/place_driver.py` re-run unmodified,
its report diffed field by field against the shipping
`docs/driver_placement.json` — **27 numeric fields, 2 changed**:

| field | shipping | R2-881 |
|---|---:|---:|
| `crown_correction_mm` | −16.405 | −18.384 |
| `stats.seconds` | 33.8 | 166.8 |

`place_driver`'s own crown correction absorbed the dome exactly — it lowers the
figure by however much the crown rose — so the H-point, the ankle in the pedal
box, the wheel override, the tilt and `hip_below_seat_pan_m` are **bit-identical**.
The fit was accepted on all four checks.

`tools/driver_containment.py`, unmodified, on the fixed blend at the film's own
camera (`render/film16_path.json`) — this is the gate that R2-406's +54 mm
experiment failed:

| frame | driver px | driver px with him hidden | **outside the aperture** |
|---:|---:|---:|---:|
| 2635 | 171,972 | 0 | **0** |
| 2632 | 131,536 | 0 | **0** |

Shipping build for comparison: 172,468 / 0 at f2635 and 132,155 / 0 at f2632.
The 0.3 % drop in driver pixels is the capped crown plus the 2 mm correction.
`negative_control_ok: true` on both — the instrument reads 0 with the driver
hidden and six figures with him present, so it is measuring something.
`docs/r2881_containment_after.json`.

**The `stats.seconds` regression is real and is mine.** `_pchip` recomputes its
Fritsch–Carlson slopes on every call, and `build_helmet`'s aperture-edge
bisection calls `helm_surface` 26,624 times, so the build went 33.8 s → 166.8 s.
It is a pure memoisation away (the keys are constant) and it changes no output.
Not done here because the artefacts in this block were built from the source as
it stands and I would rather ship them in sync than shave two minutes off a
build.

### What I have not fixed, and why

* **The inner liner's 160-vertex crown ring** (R2-882) and the balaclava's own
  uncapped crown and foam shell. All three are the same one-line omission. All
  three are behind an opaque shell that is now closed, so none can be seen; they
  are mesh-integrity debt, not picture defects.
* **`NRM` displaces relief along a radial vector from a fixed centre**
  `(0.004, 0, 0.010)` rather than the true surface normal. On a superellipse of
  exponent 2.2–3.0 those differ, so all shell relief is pushed along a sheared
  direction. Real, measurable, and it changes the shape of every relief feature
  — but it is a change to the whole shell's geometry and I would not make it in
  the same pass as a defect fix without its own before/after.
* **No chin strap, no D-rings, no visor gasket, no cheek pads** (the comment at
  the interior block claims cheek pads; there are none). At this framing the
  chin and cheeks face away from the camera. Worth doing, not worth doing here.
* **The item gate's framing declaration** (`nearest_camera_m: 3.0`,
  `lens_at_closest_mm: 21`) is wrong by 1.95× for this item and should be
  corrected to 2.34 m / 32 mm. I have not touched `docs/item_manifest.json`
  because it is shared and re-gating is another agent's block.

### R2-890 — the before/after, at the shot's own framing, through the real grade

Both sides are the same scene built by `tools/build_driver_look.py` at the film
camera `CAM_DRV_F2635` out of `render/film16_path.json`, differing **only** in
which `driver_figure.py` built the driver. AgX / look None / exposure −3.628,
read back and asserted by the build. 4K, 256 samples, `--border` cropped to the
cockpit on the 5090; the crown tiles re-rendered locally on CPU at 96 samples
with **motion blur off**, because the instrument here is the surface and not the
shutter (see the caveat below).

    render/r2881/AB_cockpit_f2635.png    the whole cockpit, 1500 x 1229 each
    render/r2881/AB_helmet_f2635.png     the helmet at 2x, nearest-neighbour
    render/r2881/AB_crown_f2635.png      the crown at 4x

Measured on the crown tile (200 x 200 px of the 4K frame, identical border):

| | px below 3 % luminance | darkest pixel |
|---|---:|---:|
| before | **1,910** | 0.0070 |
| after | **0** | 0.0398 |

1,910 px is the hole. It is not a dark region of a surface — it is the absence
of a surface, and nothing in the after frame is that dark because there is now a
shell there. The geometric measurement in R2-882 (44 px → 2 px of boundary loop)
and the photometric one agree.

In the helmet tile the rest of the block shows too: the conical crease ring
round the crown has become continuous curvature (R2-883), the livery boundaries
now carry a paint step instead of ending as an albedo edge on a glass surface
(R2-888), and the two top duct fairings read with a lip on the sun side and a
shadow on the lee side instead of the symmetric bright rims that
`clip(abs(d)·120, 0, 1)` was giving them (R2-885).

**The caveat, stated rather than buried.** In the film these seven frames carry
very heavy motion blur — f2634 is the worst camera rotation step in the whole
take at 12.957°/frame — and `render/r2881/film16_f2635_AS_SHOT.png` shows most
of the frame smeared into streaks. So of everything in this block:

* **the hole survives the shutter and dominates** — it is a hard, round,
  high-contrast shape and it is the sharpest thing in the delivered frame;
* the crease ring and the livery step survive partially;
* the orange-peel and paint microstructure largely do not, at this frame. They
  earn their keep on the other 2,201 frames where the cockpit is on screen and
  the camera is not whipping.

Ranking them by what the client can actually see was the point of measuring at
the framing instead of at the gate's.

### Artefacts — driver

    world/items/driver_figure.py     the five edits: _pchip + _helm_profile,
                                     the row distribution in helm_surface, the
                                     crown cap in build_helmet, the signed
                                     relief encoding + wall(), and mat_paint

    work/r2881/probe_driver.py       per-object geometry and, per material,
                                     what reaches Principled BSDF.Normal
                                     RESOLVED BY NAME
    work/r2881/check_crown.py        boundary-edge / hole / crease instrument
    work/r2881/crown_only.py         the crown loop alone, in LOCAL coords

    docs/r2881_probe_fresh.json      the FRESH (4 Aug) build, before
    docs/r2881_probe_after.json      after
    docs/r2881_crown_before.json     docs/r2881_crown_after.json
    docs/r2881_driver_placement.json place_driver re-run, 2 of 27 fields moved
    docs/r2881_containment_after.json  0 outside at f2635 and f2632

    render/r2881/film16_f2635_AS_SHOT.png   THE FRAME THE CLIENT WATCHED,
                                            from the shipping film16_breach
    render/r2881/look2635_BEFORE.blend      like-for-like A/B scenes at the
    render/r2881/look2635_AFTER.blend       film's own camera, real grade
    render/r2881/AB_cockpit_f2635.png       the crops
    render/r2881/AB_helmet_f2635.png
    render/r2881/AB_crown_f2635.png

    work/r2881/car_anim_driver_R2881.blend  the placed car. NOT promoted over
                                            world/car_anim_driver.blend.

**Nothing shipping was overwritten by this block.** `world/items/driver_figure.py`
is edited at source; every blend it produced is under `work/r2881/` or
`render/r2881/`.

### R2-898 — the two halves compose, and this is the blend that has both

The driver half and the seat half were built in parallel off the same shipping
car, so neither blend contains the other's fix: `world/car_anim_driver_R2881_seat.blend`
has the seat and the OLD helmet, and `work/r2881/car_anim_driver_R2881.blend`
has the new helmet and the OLD seat. Neither is the picture.

`tools/cockpit_surface.py` run on the driver-fixed blend composes them without
complaint — it is a material-and-shading-attribute pass and the driver fix is
geometry in a different object, so there is nothing for them to fight over. It
did not trip its own `FAIL_ALREADY_APPLIED` guard, and its static guarantee
(every `CI_*` vertex and evaluated `matrix_world` hashed at ten frames) held on
the driver-fixed car exactly as it did on the shipping one:

    work/r2881/car_anim_driver_R2881_BOTH.blend    both fixes
    render/r2881/look2635_BOTH.blend               at the film camera
    render/r2881/look2635_both.png                 rendered, 4K, real grade
    render/r2881/AB_FINAL_f2635.png    <-- THE ONE TO LOOK AT: shipping car on
                                           the left, both fixes on the right,
                                           same camera, same frame, same grade
    docs/r2881_both.json                           the compose run's report

**Whoever promotes should build from this one**, or re-run `cockpit_surface.py`
on whatever driver-fixed car is current — not promote either half alone.

**One discrepancy left standing rather than reconciled.** The seat half quotes
1416.4 px/m at f2635 and the driver half quotes 1458.9 (from
`docs/r2401_cockpit_sweep.json`, which projects the `CI_seal` aperture box). The
two differ by 3 %, which is the difference between measuring at the aperture
plane and at whatever depth the seat instrument sampled. It changes no verdict
in either half — every threshold in both is a ratio to an in-frame control — but
it is two numbers for one framing and one of them is wrong.

---

## Seat

Same frame, same camera, same grade as the driver half above: **f2635,
`CAM_DRV_F2635`, 2.34 m, 32 mm, 3840 × 2160, AgX / look None / exposure
−3.628.** The driver half measures 1458.9 px/m at the aperture plane; the seat
sits slightly further back and this half is quoted at the **measured 1416.4
px/m at the centre of `CI_seat`** (f = 32/36 × 3840 = 3413.3 px, d = 2.410 m).
Where the two halves differ by 3 %, that is why.

Scope: **material and shading attributes only.** Not one vertex moves, no
topology changes, no keyframe is touched — proved rather than asserted, see
R2-895.

### R2-891 — the carbon weave was authored at 2.34 px and therefore did not exist

`CarbonMatte` inherits round 1's `carbon_fibre()` / `_weave(nt, scale=190.0)`
from `opus5-car-render/build/s03_materials.py`. The triplanar twill is three
`Mapping` nodes at Scale 190 with a `Wave BANDS` at Scale 1.0 behind each, and
**Blender's Wave node multiplies its coordinate by 20 internally**, so the
emitted period is

    (2π/20) / 190 = 1.6535 mm  =  604.8 periods/m  =  2.34 px at this framing

which is Nyquist. Averaged over a pixel that is a constant, and a constant is
what the client saw.

This is the same bug, on the same car, that `world/car_paint.py` already fixed
on the exterior — its `WEAVE_PITCH_M = 0.0050` carries the note *"the weave was
authored at 760 repeats/m, a 1.3 mm twill, which is below a pixel … and left
every carbon panel a dead-flat mirror"*. `car_paint.py` only ever targets the
material named `LiveryPaint` (`TARGET_MATERIAL`, line 124). **That is precisely
why `CarbonMatte` never received it.**

Re-pitched to the same shipped 5.0 mm. The twill *design* is untouched — same
triplanar projection, same two perpendicular SIN bands overlaid, same
object-space coordinate, same albedo and roughness ramps. Only the pitch, and
the two numbers that depend on the pitch:

| | before | after |
|---|---:|---:|
| Mapping Scale (×3) | 190.0 | **62.832** = (2π/20)/0.0050 |
| emitted pitch | 1.6535 mm | **5.0000 mm** |
| at 1416.4 px/m | **2.34 px** | **7.08 px** |

**The relief had to be re-derived, and this is the trap in re-pitching a
weave.** Slope goes as amplitude/wavelength, so tripling the pitch at a fixed
amplitude divides the modulation by three. Round 1's Bump was 0.0005 m ×
0.095 = 47.5 µm, which is m = 0.813 pp at 1.6535 mm — far above
`itemkit.RELIEF_BANDS["isotropic_micro"] = (0.12, 0.45)`, but sub-pixel, so it
only ever delivered noise. Re-stated as a modulation through
`itemkit.relief_amplitude_for`:

    relief weave BEFORE (old pitch)  λ 1.65 mm  amp 0.048 mm  slope 5.16°  m 0.813 pp  HIGH
    relief weave AFTER               λ 5.00 mm  amp 0.056 mm  slope 2.03°  m 0.320 pp  ok

0.32 and not the band centre because the law is calibrated on the contract sun's
12.47° directional key and this is a shaded cockpit interior lit mostly by sky
and bounce, which under-delivers modulation for the same slope.

**The grazing fade also had to move, and forgetting it would have thrown the
whole fix away on a bowl.** Round 1 fades the weave toward its mean over
|N·I| ∈ 0.10…0.42 as a stand-in for the mip filtering a procedural never gets —
a band chosen *for a 1.6535 mm weave*. Aliasing begins where the projected
period crosses a pixel and that period scales with the pitch, so a 5.0 mm weave
survives 3.023× further into grazing: 0.10/3.02 = 0.033, 0.42/3.02 = 0.139.
Set to **0.045…0.200** (rounded outward for margin). A seat is a bowl seen from
80° above; its bolsters and back are exactly the parts sitting at |N·I| ≈ 0.2–0.4
that the old band was erasing.

**Blast radius, stated because it is larger than the seat.** `CarbonMatte` is on
**92 objects**, only 7 of which are `CI_*`. The weave was sub-pixel on all 92, so
this fixes the car's whole structural-carbon read, not just the seat — and the
monocoque is the strongest single measurement in R2-896.

### R2-892 — `SuedeGrip` had no colour and no roughness texture at all

Round 1's entire material was `TexCoord → TexNoise(Scale 1400) → Bump →
Normal`, with Base Color and Roughness as **constants**. The one texture is a
1.143 mm feature = **1.62 px**, fully sub-pixel, and it feeds nothing but the
bump. `imperfections.py` then modulates those constants — but a soiling layer on
a flat value is a flat value with dirt on it.

Its relief was not sized either: 0.0003 m × 0.28 = 84 µm at 1.143 mm is
**m = 2.035 pp**, 4.5× the top of the isotropic band, and it did not read as
relief because the wavelength was sub-pixel. It read as grain noise, which the
renderer averaged into a slightly darker flat.

Rebuilt. **The resolvable band here is 2–6 px = 1.4–4.2 mm**, and everything is
inside it by construction; the report checks that rather than trusting it.

Suede is not isotropic — it has a **nap**, and the whole reason a real pad does
not read as felt is that you can see which way the pile lies. So:

| field | size | px | what it is |
|---|---|---:|---|
| `nap` | 2.20 mm across × 11.0 mm along | 3.12 × 15.6 | anisotropic pile, 5 : 1 streak |
| `mottle` | 3.80 mm isotropic | 5.38 | so the streaks vary in density |
| `sweep` | 24.0 mm isotropic | 34.0 | above the band on purpose — pile *domains*, which is what the eye reads first from 2.4 m |
| *(round 1)* | *1.143 mm* | *1.62* | *the only field there was, bump only* |

The stretch is done on the **coordinate**, not on the Scale socket —
`object × (across/along, 1, 1)` in front of a noise asked for
`wavelength_m = across` — so both numbers stay legible in metres.

Plus the term that actually makes suede look like suede: **the view direction
projected into the surface, dotted with the pile direction, faded in with
grazing angle.** That is a broad lightness that swings as the shell curves away,
and no amount of isotropic noise fakes it. It is faded out head-on because a
sheen lobe that acts at normal incidence is not a sheen lobe.

Albedo, roughness, sheen and relief are all read off those same fields, so the
surface cannot disagree with itself. Roughness is **anti**-correlated with
albedo — the bright streaks are pile lying flat, the smoother state — because a
roughness field that agrees with the colour field just prints the colour twice.

| socket | before | after |
|---|---|---|
| Base Color | constant (0.017, 0.017, 0.019) | 0.55× … 1.45× that, **mean preserved** |
| Roughness | constant 0.86 | 0.780 … 0.925 |
| Sheen Weight | constant 0.06 | 0.035 … 0.100, **directional**, mean ≈ 0.065 |
| Normal | m 2.035 pp at 1.14 mm | **m 0.350 pp at 2.20 mm** (0.0271 mm) |

**State the realised spread, not the ramp ends.** The ends are 1.40 stops apart
and quoting that would overstate this sevenfold: the height is a weighted sum of
three independent normalised noises, so it concentrates on its mean — σ ≈ 0.136
in height, which the ramp turns into **≈ 0.20 stops of albedo at 1σ and ≈ 0.6 at
3σ**. The ends are reached only where all three fields agree, which is where a
real pile has a whorl.

Sheen is held on a short leash on purpose. D027 is the governing lesson — at
0.32 it turned a 1.7 %-albedo grip into a light grey pillow, exactly as it
turned the tyres grey. The mean does not move; only the direction-dependence is
new.

`SuedeGrip` is on **6 objects**: the four seat shells plus `SW_GripL`/`SW_GripR`.

### R2-893 — 42 % of the carbon's response was a gloss layer on an unbumped normal

`CarbonMatte` ships `Coat Weight = 0.42`, `Coat Roughness = 0.34`, and
**`Coat Normal` unconnected**. So nearly half the response came off a perfectly
smooth shading normal and washed out whatever weave survived R2-891.

`imperfections.py` does wire `Coat Normal` — under `coat=True`, and
`AMOUNTS["CarbonMatte"]` sets `coat=False` (`AMOUNTS["CarbonFibre"]` sets it
true, which is why the *lacquered* carbon has it and the matte does not). Now
wired, **after** `imperfections.inject` runs, so the coat sees the whole stack —
round 1's weave bump *and* round 2's micro bump — rather than only the part that
existed when this pass ran. Wiring it before inject would have left a different
surface under the clearcoat than on top of it. `verify()` refuses to save unless
`Coat Normal` and `Normal` resolve to the **same (node, socket)**.

### R2-894 — the facets are real, and they are `shade_auto_smooth(36°)` with nothing behind it

Round 1's `_emit` calls `shade_auto_smooth(ob, 36°)`, which writes hard
`sharp_edge` booleans and **nothing else** — no bevel, no custom normals, and
(checked) no Smooth-by-Angle modifier that would re-derive them at render time.
On a 0.53 m shell at 15,778 polys the median edge is 4.91 mm = 7.2 px, so a 36°
dihedral is not a design feature: it is the loft's own curvature sampled at that
density. The rolled edge of the seat pan and the crest of every bolster are
continuous, and printing a crease along them is what the client is looking at.

Threshold raised to **60°**. An edge above it keeps its flag, an edge below it
loses it, boundary and non-manifold edges are left alone (a hole's rim has no
dihedral to judge). Applied to all 15 `CI_*` shells.

`sharp_edge` is a per-edge **attribute**. Changing it changes shading and cannot
change geometry — which is exactly why this scope was chosen, given that 32 of
these objects carry beat 1's explode path.

Up-facing = an adjacent face whose world normal has n·ẑ > 0.342 (cos 70°) at
frame 2635; the camera is 80.4° above the aperture plane, so world +Z is within
10° of the view axis and "up-facing" is "what the client can see".

| object | sharp | → | in the 36–60° false band | up-facing | → |
|---|---:|---|---:|---:|---|
| `CI_seat` | 3,423 | **2,371** | 1,052 | 2,013 | **1,377** |
| `CI_seatpad` | 1,132 | **596** | 536 | 670 | **240** |
| `CI_headrest` | 6,278 | **3,615** | 2,663 | 2,644 | **1,562** |
| `CI_sidehead` | 918 | **210** | 708 (77 %) | 422 | **64** |
| `CI_liner` | 1,377 | **728** | 649 | 488 | **98** |
| `CI_harness_web` | 6,811 | **2,670** | 4,141 | 3,724 | **1,675** |
| **all 15 `CI_*`** | **57,362** | **28,261** | **29,101 → 0** | **29,868** | **14,370** |

**Hard sharp edges on up-facing `CI_*` geometry: 29,868 → 14,370, a 51.9 %
reduction**, and every one of the 29,101 false-band flags is gone. What remains
is designed: the pan-to-back junction, the harness slots, the shell's cut edges.

### R2-895 — the change is proved static, not asserted static

`static_fingerprint()` hashes every `CI_*` vertex coordinate, and hashes the
**evaluated** `matrix_world` of every `CI_*` at ten frames spanning the film
(1, 200, 400, 700, 1000, 1400, 1800, 2200, 2635, 2900) — sampled rather than
read off the fcurves, because Blender 5.x actions are slotted (`Action.fcurves`
no longer exists) and because a curve hash would still miss a constraint, a
driver, a parent or a delta transform. Sampling the matrix catches all of them
and is what "the car flies the same path" actually means.

Both blends: **verts `706b166fff7e09…`, anim `f1af305a3dab17…`, identical before
and after.** The tool refuses to save otherwise.

The `imperfections.py` layer is preserved by the documented round trip, not by
guessing: `IMP.strip(mat)` → rewrite → `IMP.inject(mat, IMP.AMOUNTS[name], 1.0)`
at the strength `world/car_anim_driver_imp.json` records. Editing underneath a
live injection would mean guessing which `R2IMP_*` input used to be the base
value. Sockets re-taken: `CarbonMatte` Base Color / Normal / Roughness;
`SuedeGrip` Base Color / Normal / Roughness / Sheen Weight / Specular IOR Level.

Every socket this pass writes goes through `feed()`, which resolves **by name**
and raises if the name is absent — Blender 5.2 moved `Principled BSDF.Normal`
from index 5 to 6 and inserted `Filter Width` at index 2 of `ShaderNodeBump`,
and index feeding shipped 14 dead bump stacks on this project. `out_by_name()`
additionally refuses any link that lands on a **disabled** output, which is the
`ShaderNodeMix`-has-three-`Result`s fault `car_paint.py` shipped once (R2-534).

*(A note for whoever reaches for `itemkit.NT` next: `NT.pin` cannot set a
constant 3-vector. It appends a 1.0 for the alpha channel, which is right for a
Colour socket and a `ValueError: sequences of dimension 0 should contain 3
items, not 4` on a Vector one. The `_vector_gain` docstring's
`vmath('MULTIPLY', obj, (110.0,)*3)` example does not run. `cockpit_surface.set_vec`
is the two-line workaround. Verified against 5.2, not assumed.)*

### R2-896 — the A/B, at the framing, with its null and its negative control

Both arms are `tools/build_driver_look.py` at `CAM_DRV_F2635` out of
`render/film16_path.json`, differing **only** in which car blend built them.
AgX / look None / −3.628, read back and asserted by the build. Motion blur off
and DOF off on both (the instrument here is the surface, not the shutter — see
the caveat). 4K, 256 samples, `--border 0.24 0.58 0.32 0.79`, 1306 × 1015 px.
Three renders, ≈ 9 s of GPU each, ≈ **$0.004 total**.

**The windows are computed from the geometry, once, and reused by both arms**
(`tools/r2881_seat_window.py`): the camera is raycast through the crop on a 4 px
lattice and each cell records which object *and which material* it landed on.
A rectangle is the wrong shape here and the run proves it — the seat is crossed
by four harness straps and the driver's arms, so the largest 100 %-pure
`CI_seat` rectangle in this crop is 36 × 68 px. The mask keeps every pixel and
the measure script **erodes it by 24 px** — 3σ of the widest DoG kernel — so no
band value reported has seen a pixel of another material. Nothing is measured
across a silhouette.

The metric is the project's own (`tools/r2366_ab_measure.octaves`): band-passed
peak-to-peak of **log** luminance per octave, 1st–99th percentile.  Log and not
linear because R2-060 measured paint-on-curvature leaking 40.9× more into a
linear band-pass, and this is a curved bowl in a dark cockpit — exactly that
case. **The fine band (σ 1→2 px) is the headline**: it is where a 5.0 mm weave
(7.1 px) and a 2.2 mm nap (3.1 px) live, and a flat material has power in the
coarse octaves — that is *form*, the shape of the seat — and nothing there.

**Fine-band p-p of the seat surface, before → after:**

| region | material | px measured | fine band (σ1→2) | | | mid (σ2→4) | |
|---|---|---:|---:|---:|---:|---:|---:|
| | | | before | after | ratio | before | after |
| `CI_liner` | CarbonMatte | 12,672 | 0.987 | **2.630** | **2.66×** | 1.496 | 1.807 |
| `MB_chassis_cockpit` | CarbonMatte | 4,784 | 0.174 | **1.734** | **9.99×** | 0.192 | 0.533 |
| `CI_seatpad` | SuedeGrip | 46,336 | 0.097 | **0.255** | **2.62×** | 0.156 | 0.227 |
| `CI_harness_web` | SuedeGrip | 33,904 | 0.101 | **0.267** | **2.65×** | 0.098 | 0.216 |
| `CI_sidehead` | SuedeGrip | 30,432 | 0.987 | 1.022 | 1.03× | 1.050 | 1.079 |
| **`LiveryPaint`** | *control* | 304,496 | 0.4517 | 0.4519 | **1.00×** | 0.5142 | 0.5146 |

`CI_seat` and `CI_headrest` are reported by the tool but **skipped**: 3,376 and
1,792 px survive erosion, too few to carry the statistic. They are the same two
materials as the rows above and nothing turns on them.

**The null**, which is what makes any of this evidence: the AFTER scene rendered
a second time from the byte-identical blend. Cycles is stochastic and
OpenImageDenoise is not idempotent, so two renders of one scene do not match,
and a difference only counts if it clears that floor.

| region | fine-band \|A−B\| | null floor | signal / floor |
|---|---:|---:|---:|
| `CI_liner` | 1.6433 | 0.0017 | **980×** |
| `MB_chassis_cockpit` | 1.5600 | 0.0043 | **362×** |
| `CI_seatpad` | 0.1575 | 0.0001 | **1,185×** |
| `CI_harness_web` | 0.1659 | 0.0006 | **280×** |
| `LiveryPaint` *(control)* | **0.0002** | 0.0001 | **3.3×** |

The control is `LiveryPaint`, 33.7 % of this crop, which R2-881 does not touch.
It moves by 0.0002 against a floor of 0.0001 — i.e. it does not move. **Mean
luminance is unchanged to five decimals in every region** (`CI_seatpad` 0.00169
→ 0.00165, control 0.05019 → 0.05019), which is the point of preserving the
suede's albedo mean: the seat gained structure without gaining or losing value
against the rest of the cockpit.

**`CI_sidehead` is the one region that barely moved, and it is worth saying why
rather than dropping it.** Its before fine band is already 0.987 — ten times the
seat pad's — on a surface ten times brighter (mean 0.0204 vs 0.00169). It is the
side head protection, the one seat shell that catches the sky, and 77 % of its
918 sharp flags were in the false band. Removing those creases *took* fine-band
power out at the same time as the nap *put* fine-band power in, and the two
roughly cancel: 0.987 → 1.022. That is a real result, not a null one — the
composition of the band changed even though its magnitude did not — but the
number on its own does not show it, so it is stated rather than averaged away.

### R2-897 — what survives the shutter, and what does not

f2634 is the worst camera rotation step in the film (12.957°/frame) and
`render/r2881/film16_f2635_AS_SHOT.png` shows most of the delivered frame
smeared into streaks. Ranking this block by what the client can actually see in
the *delivered* shot, not in the A/B:

* **R2-894, the false creases, survives the blur and is the highest-value change
  here.** They are hard, high-contrast edges on continuous curvature, and motion
  blur smears a hard edge into a visible streak rather than removing it. 14,370
  fewer of them on up-facing geometry is the item most likely to have caused the
  client's note.
* **R2-893, the coat normal, survives**, because it acts on the specular of a
  large smooth panel and that is a low-frequency change.
* **R2-892's `sweep` field (24 mm / 34 px) and the directional nap survive** —
  they are broad value structure, which blur preserves.
* **R2-891's 7.1 px weave and R2-892's 3.1 px nap partially survive**, smeared
  along the motion vector. They are still worth having at this frame — they are
  what makes the surface read as a *material* rather than a tone — and they earn
  their keep on the other 2,201 frames where the cockpit is on screen and the
  camera is not whipping.

That ranking is the reason the A/B was rendered with motion blur off: the
instrument had to be the surface. It is not a claim that the delivered frame
looks like the A/B.

### What I have not fixed, and why

* **No bevel and no custom normals on the `CI_*` shells.** Raising the threshold
  removes the false creases; a 0.5 mm bevel on the *true* ones would additionally
  give them a highlight instead of a mathematically zero-width arris. That is a
  topology change, and topology is the one thing this scope excludes.
* **`CI_seat` at 15,778 polys over 0.53 m is genuinely coarse** — median edge
  7.2 px. A subdivision would remove the remaining faceting outright. Same
  reason: geometry.
* **The twill is two overlaid SIN bands, not a real 2/2 twill float.**
  `car_paint.py` builds the proper thing (`_twill_plane`, tow-over-tow with a
  `MAXIMUM` combine). Round 1's plaid now reads correctly at 5.0 mm and the brief
  for this pass was explicitly *scale, not design*, so it was left. Upgrading
  `CarbonMatte` to `car_paint`'s twill would make the bare carbon and the painted
  carbon the same laminate, which they should be, and is worth its own A/B.
* **`SuedeGrip` covers the harness webbing.** Webbing is not suede — it is a
  woven polyester tape with a ~2 mm rib. The nap field at 2.2 mm happens to read
  plausibly on it (2.65× fine band, and it looks like weave in the crop), but it
  is the right answer by accident. It wants its own material.
* **The two steering-wheel grips also carry `SuedeGrip`** and therefore also got
  the nap. Correct — they are the same alcantara — but they were not re-judged at
  their own framing here.

### Artefacts — seat

    tools/cockpit_surface.py         the pass: weave re-pitch + relief re-derive
                                     + grazing-fade re-band, SuedeGrip rebuilt,
                                     Coat Normal wired, sharp threshold raised,
                                     with strip/inject round-trip, by-name socket
                                     feeding, wiring verify and the static proof
    tools/r2881_seat_window.py       raycast material-purity masks, computed once
                                     from geometry and reused by both arms
    tools/r2881_seat_measure.py      the octave band-pass A/B with null + control

    world/car_anim_driver_R2881_seat.blend   the fixed blends. NEITHER shipping
    world/car_anim_R2881_seat.blend          blend was overwritten.

    work/r2881_seat/seat_driver.json full report: pitches, px, relief budget,
    work/r2881_seat/seat_car.json    per-object sharp census before and after,
                                     static fingerprints

The pass refuses to run twice: both materials carry an `r2cs` key and a second
invocation exits `FAIL_ALREADY_APPLIED` before touching anything, because
Blender exits 0 on an uncaught exception and a half-applied rewrite would have
been silent to `$?`.
    work/r2881_seat/windows.json     crop composition + the mask
    work/r2881_seat/windows_mask.npz
    work/r2881_seat/seat_ab.json     every octave of every region, all three arms

    render/r2881_seat/look2635_AFTER.blend        the A/B scenes (BEFORE is the
                                                  driver half's
                                                  render/r2881/look2635_BEFORE.blend)
    render/r2881_seat/seat_f2635_BEFORE.png       1306 x 1015, the crop
    render/r2881_seat/seat_f2635_AFTER.png
    render/r2881_seat/seat_f2635_NULL.png         the noise floor
    render/r2881_seat/peep_carbon_1to1_BEFORE.png  640 x 480 1:1, AS DELIVERED,
    render/r2881_seat/peep_carbon_1to1_AFTER.png   no levels applied
    render/r2881_seat/peep_seatpad_1to1_BEFORE.png
    render/r2881_seat/peep_seatpad_1to1_AFTER.png

**Nothing shipping was overwritten by this half either.** `docs/DEFECT-LOG-R2.md`
is not edited.
