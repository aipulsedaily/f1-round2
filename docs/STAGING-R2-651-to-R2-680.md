# STAGING — R2-651 to R2-680

Block: **THE CIRCUIT SURFACE'S APPEARANCE.** The racing surface is on screen for
1,922 of 2,978 frames and no one had looked at it. A pixel gate reported, from
one 720p frame (f2000), that the asphalt has *"no texture and no rubbered-in
racing line"* and that *"tilt-shift DOF makes the circuit read as a tabletop
model"*. The gate said its own finding was under-claimed and rested on one
frame. It was right to say so, and the finding does not survive contact with a
measurement — but something worse does.

**Verdict in one line.** *"No texture"* is **false** — it is an artefact of
judging a 720p frame, and the 4K renders show aggregate, joints, patches and
zone changes. *"Tilt-shift DOF"* is **false** — the circle of confusion on the
asphalt is 0.50 px against a 31.78 px motion streak, so the softness is the
180-degree shutter and belongs to the camera. *"No rubbered-in racing line"* is
**half true for the wrong reason** — the band is there, half a million pixels of
it per frame, delivering 96 % of what AgX at −3.628 can pass. **But it is
painted a median 4.96 m from the line the car actually drives, and the car is on
it for 15 % of the lap.** That is the real defect, it generalises across all
1,524 lap frames, and the module's own documentation predicted it in writing.

Nothing here is written into `docs/DEFECT-LOG-R2.md`; that file has one owner.

---

## R2-651 — the rubber is painted 4.96 m from where the car drives, and the module predicted this failure in writing

**This is the finding.** Everything else in this block is smaller.

`build_surface.md` §2.3 closes with a warning the module wrote about itself:

> `racing_line_offset(s)` is exported. **The car and camera builders must use
> it** — if the car drives a different line from the one the rubber is painted
> on, the whole surface reads as wallpaper.

Nothing uses it. `grep -rn racing_line_offset --include=*.py` over the whole
tree returns `build_surface.py` itself, `world/items/asphalt_wearing_course.py`
(which is build_surface's own item), and nothing else. Not `anim/carpath.py`,
not `anim/build_car_anim.py`, not `anim/build_camera_rig.py`, not
`tools/build_telemetry.py`.

### Measured, not inferred

`tools/build_telemetry.py:build_geometry()` integrates the lap from
`spec["elements"]`' `start_world` and `heading_world_deg` — that is **the
centreline**. So the single source of truth for all motion drives the car down
the geometric middle of the road for the whole lap. Projecting every telemetry
sample through `world_contract.project()` and comparing against the dumped
`racing_line_offset` (`tools/r2651_line_dump.py`, `render/r2651/line.json`):

| quantity | p50 | p90 | max |
|---|---:|---:|---:|
| car's signed lateral offset from the centreline, \|u\| | **0.003 m** | — | — |
| painted rubber's centre, \|u\| | **4.811 m** | — | 7.143 m |
| **\|car_u − rubber_u\|** | **4.955 m** | **6.665 m** | **12.468 m** |

On a road whose `half_width` is 7.0–8.0 m, the rubbered band is centred a median
of **five metres** — two thirds of the way to the edge — from the tyres that are
supposed to have laid it. The car runs on clean tarmac for the entire lap while
a dark band sweeps side to side beside it.

### It generalises across the whole lap, not just at f2000

`tools/r2651_band_sweep.py` evaluates it at every telemetry sample of beat 5
(1,524 of them, the full 3,675 m):

| where the car is | share of the lap |
|---|---:|
| on the rubbered **heart** — the width §2.3 says the cars actually use | **14.96 %** |
| inside the shoulder | 32.48 % |
| inside the feather at all | 60.50 % |
| **on tarmac carrying no rubber whatsoever** | **39.50 %** |

The car spends **six sevenths of the lap off the band that its own tyres are
supposed to have laid**, and two fifths of it on tarmac the material treats as
never having been driven on. This is not an f2000 artefact and it is not a
near-miss at a few corners.

### It is not a near-miss and it is not noise: the module contradicts itself in its own source

`build_surface._car_box()` — the scale reference the test harness drops into
every shot — places the car at `racing_line_offset(station)`. The shipped car is
at `u ≈ 0`. Two objects in this project both claiming to be "the car", 5 m apart,
and the surface material is keyed to the one that is not rendered.

### This is a route/telemetry disagreement of the class R2-042 was

R2-042 found the route and the telemetry disagreeing by 9.04 m at the pit wall
and the decision was recorded rather than averaged. This is the same shape and
it is larger in effect, because 9.04 m was 60 m of beat 4 and this is 1,524
frames of beat 5.

**It is deliberately NOT fixed here, and that is a decision, not an omission.**
There are exactly two repairs and they belong to different owners:

* **(a) move the car onto the racing line.** Correct in principle —
  `racing_line_offset` is already drivability-solved to 4.33 g against a 4.89 g
  design maximum, minimum radius 21.0 m at the hairpin, which is the hairpin's
  inside line. But `telemetry.csv` is the declared single source of truth for
  *all* motion: its `s` drives wheel rotation, steering, pitch, roll, the camera
  choreography's timing and every layer of the audio mix. Re-solving it moves
  picture against sound in a film with no cuts. **Not this agent's to make.**
* **(b) move the rubber onto `u ≈ 0`.** Cheap, mine, and **wrong**: it paints a
  straight band down the middle of every corner, which no circuit has, and it
  destroys the one property §2.3 was built to deliver — a band that tightens
  through the apexes because `spread` comes from telemetry lateral load.

**(a) is geometrically ready today — the obstacle is blast radius, not the
line.** Checked against the dumped field (`render/r2651/line.json`):

| | measured | bound |
|---|---:|---:|
| minimum radius | **21.05 m** | 28 m track radius − 6.95 = the hairpin's inside line |
| peak lateral load | **4.33 g** | 4.89 g circuit design maximum |
| line stays inside `verge_edge` | **everywhere** | required |
| worst \|u\| as a share of `half_width` | **0.933** | < 1 |

Nothing has to be re-solved for the car to drive it. The cost is entirely
downstream: `s` drives wheel rotation, steering, pitch, roll, camera timing and
the whole audio mix, and a driven line 5 m off the centreline is a different
lap length and therefore a different lap time.

Recommendation: **(a)**, owned by whoever owns telemetry, with the surface
following for free because the material already reads `racing_line_offset`. If
(a) is refused, the honest fallback is to re-solve the racing line *constrained
to pass through the driven line*, which is a different and much weaker object,
and it should be logged as a compromise rather than as a fix.

---

## R2-652 — "tilt-shift DOF" is false by a factor of 64; the blur is the shutter

The gate attributed the tabletop read to depth of field. `tools/r2651_dof_dump.py`
pulls the rig's own keyed `aperture_fstop` and `focus_distance` for all 2,978
frames (the published `camera_rig_path.json` carries `p`, `q` and `lens` and
nothing else, so until now no one could check). `tools/r2651_track_scale.py`
then computes, per frame, the circle of confusion at the racing surface and the
camera-motion streak over the rig's 180-degree shutter.

Over the 1,645 frames of beats 4 and 5 in which the surface exceeds 2 % of the
delivered frame:

| | p50 | p90 | p99 |
|---|---:|---:|---:|
| DOF circle of confusion on the asphalt | **0.50 px** | 1.32 px | 2.59 px |
| camera-motion streak, 180-degree shutter | **31.78 px** | 162.33 px | 1038.52 px |

**Motion blur exceeds depth of field on 1,640 of 1,645 frames.** At the gate's
own frame f2000 the numbers are CoC **0.00 px** against a **69.7 px** streak: the
camera is focused at 78.1 m on a subject at 79.5 m, i.e. exactly on the tarmac
the gate called defocused.

### One depth is not enough to kill it, so it was killed at three

A median CoC could in principle hide the very thing being claimed — a *gradient*
of focus across the frame is exactly what tilt-shift is. So the CoC was
re-evaluated at the **nearest** visible asphalt (d10), the median, and the
**farthest** (d90) of the same frame:

| | p50 | p90 | p99 | max |
|---|---:|---:|---:|---:|
| CoC at nearest visible surface | 0.25 px | 1.28 | 2.00 | 2.8 |
| CoC at median | 0.50 px | 1.32 | 2.58 | 3.7 |
| CoC at farthest visible surface | 0.58 px | 1.34 | 2.93 | 4.8 |
| **near-to-far CoC span within one frame** | **0.27 px** | 0.91 | 1.45 | 2.5 |

**That span exceeds 4 px in 0 of 1,645 frames, and exceeds the motion streak in
0 of 1,645 frames.** In the eight frames with the largest span the streak runs
213–1,651 px against a CoC span of at most 2.5 px. The aperture is f/5.6
throughout the lap and focus tracks the car.

There is no depth-of-field gradient across the racing surface anywhere in beats
4 and 5. The soft-above-and-below, sharp-across-the-middle band that reads as
tilt-shift is a **panning shot**: the camera's rotation rate cancels the
ground's parallax at the car's depth and nowhere else. That is what a real
long-lens tracking shot of a car at 280 km/h does, and it is physically correct.

If the tabletop read is real it belongs to `motion_blur_shutter` (0.5, flat,
`anim/build_camera_rig.py:1278`) and to the camera department. **It does not
belong to the asphalt and it must not be textured around.** Reported per the
brief's explicit request.

---

## R2-653 — the gate measured resolution, not material, and the project's own ladder doc said it would

`docs/RENDER-LADDER.md`, last section, written before any of this:

> Low resolution HIDES material and geometry defects. A 720p pass will happily
> pass grass that is a fuzzy mat, **an asphalt that is a grey gradient**, a decal
> that is soft.

The gate judged a 720p frame — one ninth of the delivered pixel count.
`tools/r2651_track_scale.py` reports millimetres of surface per delivered pixel
for every pose. Over the same 1,645 beat-4/5 frames, cycles per pixel for each
of the material's own eleven layers:

| layer | λ | 4K px/cycle, p50 | frames ≥ 2 px at 4K | 720p px/cycle, p50 | frames ≥ 2 px at 720p |
|---|---:|---:|---:|---:|---:|
| paver mats | 9.50 m | 355.8 | 100 % | 118.6 | 100 % |
| segregation | 0.65 m | 24.3 | **99.7 %** | 8.1 | 74.7 % |
| coarse stone | 30 mm | 1.12 | 30.6 % | 0.37 | 5.2 % |
| **aggregate** | **18 mm** | **0.67** | **11.0 %** | **0.22** | **2.1 %** |
| intermediate | 9 mm | 0.34 | 3.7 % | 0.11 | 1.2 % |
| fines | 4 mm | 0.15 | 1.8 % | 0.05 | 0.0 % |
| grain | 2.3 mm | 0.09 | 0.5 % | 0.03 | 0.0 % |

**At 720p the aggregate is 0.22 px per cycle. It cannot appear, whatever the
material contains.** "The asphalt has no texture" was arithmetically guaranteed
by the frame the gate chose, and would have been returned by an identical gate
run against a photograph of real tarmac.

**That does not make the surface innocent.** The same table says the material's
five finest layers — everything below 65 cm — are doing nothing for 69–99.5 % of
the lap *at 4K*. The detail budget is spent where the film's own camera cannot
spend it. Whether that leaves a visible gap is a question about pixels, not
about arithmetic, and it is answered by rendering rather than by this table: see
R2-655.

---

## R2-654 — the rubbered line IS there, and it is delivering 96 % of what this grade can pass

`build_surface.md` §2.5 measures the band at **2.2–2.9 : 1** against clean
tarmac. That number was taken from **plan views under a uniform dome, in linear
albedo**. The film is a 12.47-degree sun at grazing incidence through **AgX, look
None, exposure −3.628**. Those are different measurements and the second had
never been taken.

`tools/r2651_line_probe.py` takes it: it projects the cross-section
`u = −verge_edge … +verge_edge` at stations the camera can actually see, reads
the **delivered** pixels along it, and marks where `build_surface` says the
heart, shoulder and feather are. At f2000, s = 1785–1805:

* luminance falls monotonically from **0.268** at u = −4.95 to **0.200** at
  u ≈ +4.0, and the minimum of the section sits at u = +3.4 against a predicted
  band centre of +4.8. The band is in the frame and roughly where predicted.
* against the **local linear trend** its depth is **1.084 / 0.951 / 0.974** —
  i.e. there is no legible edge. It is a ramp across the road, not a band.

f2001, the only other delivered lap frame, agrees: trend-relative depth
**0.922 / 0.941**, and the section minimum again lands near the prediction
(u = +4.16 and +4.39 against predicted centres +5.26 and +5.84). Across all five
sections the darkest point of the road sits a consistent ~1.2 m inboard of the
predicted band centre — which is what a broad ramp clipped by the road edge
looks like, not what a misplaced band looks like.

**The trend subtraction is the whole instrument and it was forced by a negative
control.** The first version compared the mean inside the band with the mean
outside it and returned **0.72 on a synthetic pure gradient containing no band
at all** — it would have found rubber on every section it looked at, because a
crowned road under a low oblique sun *is* a gradient in `u`. `--selftest` now
carries five controls including two the metric must fail.

### Then the grade was measured instead of assumed

`tools/r2651_agx_curve.py` pushes a 4,096-step log ramp through Blender's own
colour management at this film's exact grade and reads back what it wrote — no
formula, no approximation of AgX:

* linear 0.18 → display **0.0989**; linear 1.00 → display **0.3016**
* the measured section, **0.268 : 0.200 display**, is a **1.62 : 1 scene ratio**
* a **perfect 2.4 : 1** albedo band delivers **1.68 : 1** on screen here
* a **2.9 : 1** band delivers **1.86 : 1**; a **3.3 : 1** band delivers **1.99 : 1**

**The shipped surface is delivering 1.62 against a documented-perfect 1.68.**
The rubber layer is not dead, not disconnected and not washed out by the
specular lobe — the specular-cancellation trap was already found and mitigated
in `build_surface.py` (roughness drop cut 0.30 → 0.12, and the comment records
why).

So the gate's "no rubbered-in racing line" is **half right for the wrong
reason**. There is no legible *line* — but the ceiling on legibility at this
exposure is ~1.9 : 1 of display contrast, and no amount of albedo will buy a
hard-edged stripe out of AgX's toe. Any future request for "a stronger racing
line" is a request about the grade or the exposure, not about the material, and
should be routed accordingly.

*Caveat stated rather than buried:* the inverse-AgX step is applied to the Rec.709
luma of a near-neutral surface. AgX is per-channel with a chroma mix, so this is
exact for neutrals and approximate off them. Asphalt is as neutral as this film
gets, which is why the measurement was taken there.

### And the band is not merely present, it is enormous

The other way "no rubbered-in racing line" could have been true is if the band
were off-frame or sub-pixel for most of the take. It is not.
`tools/r2651_band_sweep.py` projects the heart through every pose:

| beat | racing surface, share of frame | **rubbered heart, share of frame** | heart as share of visible road | heart, delivered 4K px |
|---|---:|---:|---:|---:|
| 4_transit (122 fr) | 40.3 % | **4.96 %** | 0.144 | 411,094 |
| 5_lap (1,524 fr) | 44.5 % | **6.96 %** | 0.183 | **577,434** |
| 6_ending (264 fr) | 4.0 % | 0.73 % | 0.174 | 60,862 |

*(occlusion-blind upper bounds, and the tool says so)*

**Better than half a million delivered pixels of rubbered band, in the median
frame of the lap.** The line is on screen, at size, in essentially every frame
of beats 4 and 5. It is not missing; it is soft-edged because AgX's toe is what
it is, and it is in the wrong place because of R2-651.

---

## R2-655 — the film's own camera now has test frames, which it did not before

Nineteen shots existed in `build_surface._shot_defs()` and **not one of them was
a frame the audience will ever see.** All were stations the module chose for
itself — 26 m on an 85 mm lens, 5 m on a 21 mm. Beat 5 is a 40 mm lens 22 m up
moving at 280 km/h, and the surface reached a render ladder without ever having
been photographed from there.

`FILM_POSE_FRAMES` / `_film_pose_defs()` / `_make_film_pose_cameras()` and the
`filmpose` blend group build cameras from the shipped rig's own pose,
quaternion, lens, `aperture_fstop` and `focus_distance`. **The frames are chosen
from the measurement table, not by eye:**

| frame | mm/px at 4K | surface share | CoC | streak | what it decides |
|---|---:|---:|---:|---:|---|
| **f1547** | 11.8 | 46 % | 0.83 px | 7.0 px | the sharpest close look at the surface in the whole film |
| f2225 | 21.0 | 18 % | 0.26 px | 10.3 px | mid range, still sharp |
| f2000 | 11.5 | 50 % | 0.00 px | 69.7 px | **the gate's own frame, at 4K instead of a ninth of it** |
| f1226 | 51.5 | 41 % | 0.46 px | 5.4 px | the wide, where only the metre-and-up layers survive |

The rotation is copied from the rig's quaternion rather than reconstructed by
`_look_at`, because `_look_at` forces a roll of zero and beat 5 rolls.

Rendered at 3840×2160 / 512 samples through the real grade — `render/r2651/`.
Cost as quoted before queueing: 26–61 s/frame, **$0.05 for the set**.

### And they answer the texture question, in pixels

**f1547, 21 m, 11.8 mm/px, 1:1** (`render/r2651/before_f1547.png`) — the asphalt
carries dense, legible aggregate stipple: individual chips resolve, there is real
tonal variation between paving lanes, the track-edge line has a worn and chipped
edge rather than a vector one, and diagonal segregation banding runs through it.
**This is not "a flat grey value" and it is not close to one.**

**f2000, 79 m, 11.5 mm/px, 1:1** (`render/r2651/before_f2000.png`) — the gate's
own frame, at nine times its pixel count. Aggregate is present but reduced to a
faint stipple; what carries the surface here is the longitudinal paving-lane
joints, the pale milled repair patches and the resurfacing-zone tone changes.
Legible, but visibly flatter than f1547.

**So the gate's first claim is refused: at the delivered resolution the asphalt
has texture.** But the difference between those two crops is the whole of
R2-653's argument made visible — the fine octaves earn their keep close in and
thin out at the distances beat 5 actually lives at. That is an argument for
strengthening the **0.1–0.5 m and 1–4 m** octaves, which survive at lap
distances, and specifically *not* for adding more fine aggregate, which would
land entirely below the resolution of the shot that needs help.

*Caveat on the vehicle:* these come from the surface-only harness, so the pale
ground around the ribbon is `TEST_Ground`, there is no sky model, no barriers and
no motion blur. That isolates the material, which is what they are for; it does
**not** reproduce the delivered frame's lighting in full.

### They also settle R2-659 the right way

f1547 was the frame where the two coverage methods disagreed 7×. The render
shows asphalt filling most of the frame — **the area-credit figure of 0.464 is
right and the per-pixel cross-check's 0.065 is wrong**, exactly as the flat-plane
control predicted. The picture, not either projection, was the arbiter.

---

## What I am NOT building, and why

The brief lists what a real circuit surface has and asks for an argument rather
than a shopping list. Read against the material, most of the list is already
there — and the measurement table says which parts of it the film's camera can
ever see. Both matter, so both are given:

| the brief asked for | state in `build_surface.py` | can the film see it? |
|---|---|---|
| aggregate at close range | 30 / 18 / 9 / 4 / 2.3 / 0.6 mm layers, applied as a **multiplicative contrast field** (§2.5 — mixing toward a chip colour lifted dry reflectance to 0.083 and the fix is recorded) | 18 mm resolves in **11 %** of lap frames at 4K; the three finest layers essentially never |
| rubbered line, correct width | heart / shoulder / feather / tyre tracks, `spread` from telemetry lateral load so it tightens through apexes | **6.96 % of the frame**, ~577 k px, every lap frame |
| rubbered line, correct **path** | **WRONG — R2-651**, 4.96 m from the driven line | — |
| marbles off-line | `marb_ring`, outboard of `1.7–2.4 × spread`, gated on `rubber` | ring width is metres; resolvable throughout |
| braking-zone darkening | `brake` field from telemetry `a_long`, driving `skid` lock-up streaks and the rubber `dep` term | resolvable |
| kerb paint worn where cars run | `wear` term keyed to `rubber` × approach distance; kerbs are 35 separately generated meshes | resolvable at the kerb-height stations |
| surface repairs, seams, joins | saw-cut rectangular patches in road space with a 25 mm bitumen kerf, Voronoi milled areas, ~25 per lap; longitudinal paving-lane joints with 350 mm screed shoulders; crack-sealant snakes in the old zones; timing-loop cuts | 4.4 m and up — resolvable in ~100 % of frames |
| drainage camber picked out by specular | parabolic crown in `C.ground_z` (1.45 % edge cross-fall) plus **drainage runnels running ACROSS the road**, deliberately the one direction nothing else runs | resolvable |
| a circuit that is not uniform | nine resurfacing zones with their own age, base colour, lane width and phase; paver mats from a **Voronoi CELL ID** at 9.5 m; no tile anywhere — every pattern is 3-D procedural over a 1,900 m domain | resolvable at every distance |

**So the "no repeated assets" red line is not the live risk here.** There is no
tile to spam: §2.5's anti-tiling is structural, the mid-scale layer is cellular
rather than fractal for a recorded reason (fractal noise at the road's own width
reads as camouflage), and the variation is already driven by the telemetry, the
corner table and the resurfacing plan rather than by noise alone.

**Adding octaves is therefore the wrong move and I decline it.** The honest
reading of R2-653's table is not "the surface needs more texture" but "the
surface's fine texture is spent below the resolution of the shot that shows it".
The two candidate responses are:

* **rebalance toward 0.1–0.5 m and 1–4 m**, the two real gaps in the octave
  ladder (0.03 m → 0.65 m is a 22× jump, 0.65 m → 4.4 m is 6.8×). This is the
  R2-366 repair shape and it is cheap.
* **leave it alone**, because the close stations — the T4 kerb-height camera at
  2.2 mm/px and the doppler hover at 4.9 mm/px — are exactly where the fine
  layers earn their keep, and stripping them to serve the lap would fail the
  frames the fine layers exist for.

**Neither is chosen on arithmetic.** They are chosen by looking at f1547 at 1:1,
which is what R2-655 queued and what the ladder doc demands. Building first and
looking after is how a surface acquires four more layers nobody can see.

---

## Instruments added, and the controls they must fail

Roughly a third of this project's findings have been broken instruments. Every
tool in this block carries a `--selftest` with negative controls:

| tool | what it measures | a control it must FAIL |
|---|---|---|
| `tools/r2651_dof_dump.py` | keyed fstop / focus / shutter per frame | — (a dump, not a metric) |
| `tools/r2651_track_scale.py` | surface share, mm/px, CoC, motion streak | in-focus plane must give CoC exactly 0; a plane mis-focused to 5 m must give the hand-computed 14.49 px, not "large" |
| `tools/r2651_line_probe.py` | delivered band depth vs predicted position | a pure gradient with no band must give exactly 1.000; a band predicted 5 m off must not return the band's real depth |
| `tools/r2651_agx_curve.py` | the film's linear↔display transfer | linear 0.18 must land on AgX's published 0.0989 |
| `tools/r2651_line_dump.py` | `racing_line_offset` and the usage fields as data | heart must equal 0.55 × spread by construction |

**A broken instrument was found and fixed by this discipline** — see R2-654's
gradient control, which condemned the first version of the band metric before it
was ever pointed at a frame.

---

## R2-656 — the feather's cap is on its own width, not on the road edge, so on 57.8 % of the lap the rubber ends AT the paint

`build_surface.md` §2.3, on the feather's `0.78 × half_width` cap:

> The half-width cap is what keeps clean tarmac against the white line however
> much the cars fan out.

It does not. The cap bounds the feather's **half-width**; it is then centred on
`racing_line_offset`, which reaches ±7.144 m. Measured every 2 m round the lap:

| | share of lap | max overrun |
|---|---:|---:|
| feather reaches beyond `verge_edge` | **57.8 %** | **2.88 m** |
| heart reaches beyond `verge_edge` | 0.0 % | −1.32 m (always inside) |

The heart is safe — the important half of the claim holds. But the feather runs
off the racing surface on more than half the lap, where the shader's `on_track`
multiply clips it dead. **A feather that is clipped is not a feather:** it ends
in a hard edge exactly at the track-edge line instead of fading out before it,
which is the opposite of what the cap was written to achieve.

Small, cheap, and unambiguously this module's. The fix is to cap
`|centre| + feather` against `verge_edge` rather than capping `feather` against
`half_width` — but it should land **after** R2-651 is resolved, because moving
the band's centre moves every one of these overruns.

---

## R2-657 — the telemetry-to-film frame join is +973, not +792, and a control caught it

Worth recording because anything else joining these two tables will reach for
the same wrong number. `telemetry.csv` numbers frames from the car's first
movement, so the natural join is "beat 2 starts at 33.0 s, so film = telemetry +
33.0 × 24 = **+792**".

**That is wrong by 181 frames**, because beat 3 runs world time at 15–25 % of
screen time — 8 seconds of film buys about 1.5 seconds of car. Film time is not
telemetry time plus a constant anywhere before beat 5.

Solved instead from the data: `telemetry.s_m` is global arc length including the
transit, so `max(s_m) − C.LAP` = 377.730 m is the transit, and the telemetry
frame at that station is the one crossing the start/finish line. The beat sheet
puts that at f1191, giving **+973** — which checks exactly at the far end:
telemetry's last frame maps to f2715 against a declared beat-5 end of f2714, and
the lap needs 1,524 frames against 1,525 supplied.

The wrong offset was not caught by inspection. It was caught by a control that
demanded the lap span the whole 3,675 m; at +792 it spanned 514–3,671 m, and the
tool failed its own selftest rather than reporting a plausible wrong number.
**From beat 5 onward a constant offset is valid; before it, none is**, and
nothing in this block uses one there. R2-651's 4.96 m never depended on the join
at all — it compares the car against the band at the car's own station, row by
row.

---

## R2-658 — a third beat table is in circulation and one of them is wrong by 910 frames

`tools/r2366_surface_visibility.py` declares `beat4 1057-2100`, `beat5
2101-2714`, and its docstring says the table comes "from docs/beat_sheet.json's
own frames". `world/camera_rig_continuity.json` — written by the rig that was
actually keyed — says `4_transit 1057-1190`, `5_lap 1191-2714`. The rig is
authoritative and `r2366_surface_visibility.py` is **910 frames out on the
beat-4/5 boundary**, which is 38 seconds of a 124-second film.

Nothing in this block used that table; `tools/r2651_track_scale.py` carries the
rig's boundaries and says in a comment why. Flagged because anything else that
copied it inherited the error.

---

## R2-659 — the coverage number was cross-checked by a second method, and the SECOND method was the broken one

The headline "the racing surface is 44.5 % of the delivered frame" comes from an
area-crediting projection: each `(s, u)` sample carries its own cell area and is
credited `area · cos(incidence) · (f_px / d)²`. That is exactly the shape of
metric that has failed on this project before — a coverage number believed
without a control.

So it was cross-checked against a completely independent per-pixel method: cast
one ray per pixel, intersect the ground, ask `world_contract` whether the point
is inside `verge_edge`. No area crediting anywhere.

| frame | per-pixel road | area-credit road | ratio |
|---|---:|---:|---:|
| f2000 | 0.461 | 0.503 | 0.92 |
| f2225 | 0.170 | 0.178 | 0.96 |
| f1226 | 0.462 | 0.412 | 1.12 |
| **f1547** | **0.065** | **0.464** | **0.14** |

**One frame in four disagreed by 7×, and it was the frame chosen as the hero
close-up.** That is not a result to write around, and the contamination is not
small: the camera at f1547 sits **2.85 m** above the road, and **41.3 % of beat
5 has the camera under 5 m**. If the area-credit method over-read by 7× on those
frames the beat-5 median would fall from 0.445 to 0.238 and most of this block's
framing would be wrong.

**Resolved by building a case with an answer known in advance.** A camera at
2.85 m on a 39.93 mm lens over an *infinite flat plane*, viewing a 20 m strip:
the strip's image can be integrated exactly in image space, because a ground
point `(u, y, 0)` lands at `py = f_px·h/y + H/2`.

| | coverage |
|---|---:|
| area-credit method | 0.3227 |
| **exact image-space integral** | **0.3733** |
| ratio | **0.864 — it UNDER-reads** |

The area-credit formula is sound and conservative; the residual is the 2 m
station sampling truncating the far field. **The per-pixel cross-check is the
instrument that fails**: its 3-step fixed-point solve for the ray/ground
intersection does not converge for near-horizontal rays from a low camera, which
is precisely the f1547 geometry and precisely why it agreed on the three
high-camera frames and not on the low one.

The numbers in R2-653/R2-654 stand, and are if anything slightly low. **f1547 is
still flagged**: it is the one queued frame whose geometry the analysis handles
worst, and the render — not either projection — is what will settle what it
actually looks like.

---

---

## R2-660 — the car is hidden behind Le Pont de la Plongee for 12 frames, and the window is half a second, not the 49-frame pass

Handed over as "at f2190 the car is not in the frame at all — the centre of the
delivered frame is a concrete parapet", with a suspicion it was the grandstand
from f2180. **It is neither a grandstand nor the whole pass.**

### Measured analytically, because the bridge is eleven numbers in source

`tools/r2651_pont_sightline.py`. `build_architecture.py` builds
`ARCH_PontPlongee` in a local frame on the centreline at `PONT_S = 2410.0`, so
it can be reconstructed exactly as an oriented box and the camera-to-car segment
intersected against it — no 7.5 GB scene, no rented box, one second, on a
machine that is swapping. It is a **cheap prediction the full raycast must
agree with**, not a replacement for it.

| band | z above the road | |
|---|---|---|
| girders | 6.80 – 8.15 | solid |
| deck slab | 8.15 – 8.42 | solid |
| parapet | 8.42 – 9.52 | **solid concrete — the "parapet" in the report** |
| mesh screen | 9.52 – 10.50 | see-through in reality, opaque to a raycast |

**Result: 12 frames, f2181–f2192, 0.50 s.** *(Superseded in detail by the
exact ray-cast, R2-664: the true window is **f2180–f2193** with **f2180–f2191**
wholly hidden. This analytic model was one frame out at each end because it
omits the bridge's own dressing. The mechanism below is unaffected.)* Fully blocked at all three sampled
car heights on 11 of them. The car is 182–186 m away throughout. f2180 crosses
the **mesh screen only** — see-through in life, so it should not be counted as
concrete. **f2195 and f2200 are completely clear**: f2200 is near-field crowding,
not occlusion, and the two were different problems all along.

### Why it happens, which is the whole of the fix

The sightline sweeps **down and inward** across the bridge plane as the shot
progresses — it enters over the top and leaves under the soffit:

| frame | crosses at lateral u | height over the road |
|---|---:|---:|
| f2178 | −20.70 m | +10.51 m — outside the span, above everything |
| f2180 | −16.57 m | +9.84 m — just outside, in the mesh only |
| f2182 | −12.95 m | +9.21 m — **inside the parapet** |
| f2190 | −4.02 m | +7.11 m — **inside the girders** |
| f2192 | −3.08 m | +6.67 m — below the soffit, clearing |
| f2194 | −2.55 m | +6.26 m — under the bridge, clear |

The line descends through **10.51 → 6.26 m** while the solid band occupies
**6.80 → 9.52 m**. The band sits squarely inside the sweep, so it is crossed.

**This is why raising the bridge is the wrong lever.** To clear vertically the
band must be wholly above 10.51 m (soffit ≥ 10.0 m — a **+3.2 m** raise, and a
pedestrian overpass at 10 m of clearance is a different structure) or wholly
below 6.26 m (soffit ≤ 3.54 m — impossible over a racetrack). Measured:

| soffit over the road | blocked frames |
|---:|---:|
| 6.80 (shipped) | 12 |
| 8.00 | 8 |
| 9.20 | 3 |
| 10.00 | **0** |

### The fix: move it 50 m along the track, and it is robust

| station | blocked frames |
|---:|---:|
| 2410 (shipped) | 12 |
| 2430 | 11 |
| 2450 | 5 |
| **2460 … 2610** | **0 at every 10 m step tested** |

**A 50 m move to `PONT_S = 2460.0` clears it, with a 150 m plateau beyond — not
a knife-edge.** And it is the right *kind* of fix under the caution in the
brief:

* the bridge keeps its lateral position, its height and its span. It still
  crosses directly over the racing surface and still whips past the lens. **No
  architecture is stood politely back from the track**; the speed cue is intact.
* it is **lens-independent**. A sightline does not care about focal length, so
  the focal retune neither causes nor cures this, and this fix cannot be undone
  by a later lens change. Only a change to the camera *path* could move it.
* it spends the pass at a moment the sightline is not descending through the
  deck, which is spacing along the lap — the same lever R2-581's sweep already
  recommended for the near-field crowding.

### Not applied yet, and the reason is not caution for its own sake

1. **The authoritative full-world raycast is in flight.** If there are other
   occluders on the lap — armco, catch fence, the grandstand — the placement
   plan should be made **once, for all of them**. Two separate placement edits
   to the same passage is exactly how a one-shot film acquires a seam.
2. **`ARCH_PontPlongee` is a host, not just a shape.** Eight item families sit
   on it (`pont_girder`, `pont_parapet`, `pont_abutment`, …) and
   `build_dressing` hangs its fascia banners on this bridge's faces — R2-256
   records a real collision on that face that took a gate to find. Moving it has
   cross-module effects that should be verified rather than assumed, and the
   local box cannot currently rebuild the world to check.
3. `build_dressing` treats **s = 2440–2680** as the doppler straight and lifts
   trackside dressing density there to 0.86 on the −1 side. Station 2460 lands
   inside that run. That is not a collision — the bridge spans overhead — but it
   is a crowding interaction to check before committing, not after.

---

## R2-661 — the lens demand curve is contaminated, but by 4.9 % and with the opposite sign to the obvious guess

`lap_shotscale.py` declares in its own LIMITS that it does not model occlusion,
so frames where the car is hidden still contribute their apparent size to the
demand curve that set the focal ramp. True, and it must be re-run. But the size
of the correction is measurable rather than rhetorical:

| | |
|---|---:|
| occluded frames | **12** |
| the lens demand stretch, f2012–2256 | 245 frames |
| occluded share of that stretch | **4.9 %** |
| occluded share of beat 5 | **0.79 %** |
| median `subj_frac_w` across the stretch | 0.0441 |
| median `subj_frac_w` on the occluded frames | **0.0475** |

**The occluded frames were reporting a subject slightly LARGER than the stretch
median.** So they were mildly *suppressing* the demand for focal length, not
inflating it: dropping them makes the passage look marginally worse and would,
if anything, argue for a little more zoom rather than less. The curve should
still be re-fitted once the placement is settled — **flagged for whoever owns
the focal ramp, as requested** — but it should be re-fitted expecting a small
move in the direction of more zoom, not a retreat from the 142.5 mm peak.

---

## R2-662 — the asphalt question, answered from 72 delivered lap frames instead of one

The gate's finding rested on f2000. Two ladder sequences covering beats 4-6
already existed and had been overlooked — **`out/seq/r2b56_720` (50 frames,
f1100-2978) and `out/seq/b456wit_f11` (25 frames, f1250-2978)** — so the
generalisation question was answerable from delivered pixels at zero cost the
whole time.

**Provenance, because it decides whether the answer is worth anything.**
Rendered 08-03 at 1280x720 from the pre-`film16` world, so no placed items and
no driver. That does not matter for this question: **`world/build_surface.py`
was last modified 08-02 11:41, before these frames were rendered**, so the
asphalt material in them IS the shipped one. `film16`'s +1,707 items do not
touch the asphalt shader. The two passes writing now (`r2full`, `r2beat1`) are
on `film16_breach` and are still in beats 1-2; they will supersede this set for
anything item-dependent, and nothing here is.

`tools/r2651_line_probe.py`'s trend-relative band depth, run over **72 lap
frames / 213 cross-sections**:

| | trend-relative band depth |
|---|---:|
| p5 | 0.082 |
| p25 | 0.847 |
| **p50** | **0.973** |
| p75 | 1.054 |
| p95 | 2.268 |

| | |
|---|---:|
| sections with a band you could actually see (>= 1.20) | **25 of 213 = 11.7 %** |
| sections >= 1.10 | 44 of 213 = 20.7 % |

**The median is 0.973 — no legible band — and the finding generalises.** The
scatter either side of 1.0 is other content crossing the section (kerbs,
shadows, repair patches, the car), not a band; a real band would push the
distribution one way only.

### And it is a distance effect, sharply

| distance to the surface | n | median depth | fraction >= 1.20 |
|---|---:|---:|---:|
| **0-25 m** | 13 | **1.110** | **46.2 %** |
| 25-60 m | 15 | 0.892 | 0.0 % |
| 60-120 m | 98 | 0.964 | 15.3 % |
| 120-300 m | 22 | 0.948 | 9.1 % |
| 300-1200 m | 65 | 0.988 | 3.1 % |

**Inside about 20 m the band reads** — f2666 and f2680 score 2.55 and 2.59 at 13
and 19 m. Beyond that it does not. That is exactly what R2-654's grade ceiling
predicts: the band's *edges* are what make it legible, and they need pixels
across them; the flat interior contrast is capped at ~1.7:1 display by AgX
whatever the albedo. So the gate saw a true thing at f2000, for a reason that is
neither "no texture" nor "the rubber layer is broken".

**This does not weaken R2-651, it sharpens it.** The one condition in which the
rubbered band IS legible — the camera inside 20 m of the surface, which is the
onboard and chase material — is precisely the condition in which the audience
can also see where the car's tyres are. Those are the frames in which a band
painted 4.96 m from the driven line is most obviously wrong.

---

## R2-663 — R2-547's blank billboard is not a billboard, and the grandstand has 18,350 seats

Both halves of that defect note are refused, by raycasting f900's own verified
pose (position and lens matched to `camera_rig_path.json` at 0.0000 m /
0.0000 deg) through `render/film14_breach_r6.blend` — confirmed via the broker
DB as the scene that actually rendered `seq/r1full`.

**The white rectangle is a breach glass shard, `GS_b04_00524`, material
`BREACH_Glass`** — an 11 mm slab 0.30 m from the lens, built by
`sim/apply_breach.py`. Behind it is empty sky: of 3,842 rays through the crop
against the whole 4,711-object scene, 47 (1.2 %) hit anything, and those hit a
grandstand roof at 260 m *outside* the white bar.

* **Not a placeholder and not a dead texture stack.** `BREACH_Glass` has exactly
  two nodes. **Emission Strength = 0.0** — so "self-lit" was an inference from
  brightness, not a fact. There are no texture nodes at all, so nothing can be
  disconnected, and `apply_breach.py` sets every socket **by name**, so the
  Blender-5.2 Normal-socket-index trap is not involved.
* **Not dressing** (`build_dressing` standalone: 0 hits in the box; the nearest
  ad board `DR_Ad_043` projects below the bar and does carry artwork), **not
  architecture**, **not a light** (all 25 are behind the camera with
  `visible_camera = False`), **not the sky** (sky-only render of the same pose:
  169-180 grey, zero pixels above 215).
* Best-supported remaining hypothesis, **stated as unproven**: a motion-blurred
  blown specular highlight on the shard. The bar's ends are 2 px hard, its
  interior is dead flat at 233-234, and its mean falls 231 -> 216 between f900
  and f901 while its outline barely moves. Confirming it needs a Cycles A/B with
  `BREACH` hidden, **and that A/B was never run** — so the hypothesis stays
  unproven rather than quietly hardening into the answer. A sub-frame shutter
  sweep (does a shard cross the bar during the shutter?) was started and was
  **killed by memory pressure before producing output** — abandoned, not
  pending.
* **The one caveat, kept rather than buried, and now closed as abandoned:**
  `VEG_*` — 24,654 trees, 3,299 hedges, 26 instance libraries — was **never
  raycast**. Three load attempts were killed by memory pressure. A canopy
  reading as a hard-edged, uniform, cool-white 233 rectangle at 4 deg elevation
  is implausible, but that is an argument, not a measurement, and it is the one
  geometry set in the scene this conclusion does not rest on evidence for.

**The grandstands have seats, and the count is 18,350** (15,039 seatable, 3,311
folded), from two independent methods that agree: the replayed
`grandstand_seats.json` ledger and the geometry — `A_Seat` is **422,616 quads /
845,232 triangles** plus 557,352 `A_Alu` triangles of standards. Cross-check:
VIRAGE OUEST at 2 boxes/seat gives 25,716 / 6 / 2 = **2,143**, exactly the
ledger figure. In f900 itself `A_Seat` is the largest material by ray count on
the visible stand — 946 of 1,711 rays.

And the thing R2-547 called *"a dark grid with yellow dashes and no seat
geometry"* **is the seats**: `ARCH_Grandstand_02_OUEST` / `A_Seat` at 237 m,
base `#3c4348` with a `#c9a227` gold chequer laid by `_seat_colour()`
(`build_architecture.py:4692-4723`). The yellow dashes are gold seats.

---

## R2-664 — CORRECTED BY THE RAY-CAST: one occlusion event on the lap, not two, and my second cluster was a false positive

**This section originally reported two clusters. The exact ray-cast has killed
the second one and I am correcting it in place rather than leaving the wrong
number standing.**

`tools/r2651_occlusion_sweep.py` casts one ray per each of 58 sample points on
the car's real `world_contract.CAR_BODY_*` box, per frame, against a world
rebuilt on the rented box from its own modules — **`surface + barriers +
architecture + terrain`, contract 1.2.1**. It never opened `film16.blend`.
22 controls, all passing.

### What my projection proxy got wrong, and why

| | frames flagged f2253-2327 | verdict |
|---|---:|---|
| `r2651_occ_proxy.py` (1 m voxels, cone test) | **50** | **WRONG** |
| `r2651_occlusion_sweep.py` (rays, depth test) | 2, max `occ_frac` **0.0968**, and the owner is `SURF_Track` | correct |

`BR_Trap_outer_R_2579`, `BR_Verge_R` and `BR_Subbase_R` **never occlude the car
anywhere**. The proxy's 1 m occupancy cells over-read at grazing incidence: at a
shallow angle a 1 m cell straddles a sightline that the real surface misses by
centimetres. I flagged that cluster as proxy-only and explicitly declined to
claim severity, which was right — but the frame count itself was noise, and
"contiguity across 8 runs argues they are real" was **wrong reasoning**: a
systematic geometric over-read is contiguous too.

### The actual occlusion ledger, beats 4-6

| frames | dur | wholly hidden | object | channel | occluder distance |
|---|---:|---:|---|---|---:|
| **f1113-1118** (beat 4) | 0.25 s | **f1114-1116** | `ARCH_PitBuilding_Shell` | solid | 10-11 m |
| **f2180-2193** (beat 5) | 0.58 s | **f2180-2191, 12 frames** | `ARCH_PontPlongee` | f2180 fence, rest solid | 26-57 m |
| f2306-2309 | 0.17 s | none (0.097) | `SURF_Track` | surface | 107 m |
| f2717-2719 (beat 6) | 0.12 s | none (0.194 max) | `ARCH_Gantry` | solid | 75 m |
| **f2974-2978** (beat 6) | 0.21 s | **f2976-2978** | `BR_FenceMesh_L03` | **fence** | — |

**Beat 5 has exactly one occlusion event.** The Pont de la Plongee pass is the
only thing that hides the car on the entire flying lap.

### Three corrections to the anchor as it was handed to me

1. **f2190 is frame 11 of a 12-frame blackout, not the event.** The blackout
   starts at **f2180** and had been running for ten frames before anyone looked.
2. **It is not a parapet at f2190.** At f2190 the thing over the car is a
   **steel plate girder at 51.9 m**. The parapet frames are f2181-2184. The
   bridge is one object carrying concrete, steel and mesh, so the channel has to
   be decided by the **hit face's material**, not the object's name — classifying
   by name would have called f2180 concrete when it is the see-through screen.
3. **The camera has already flown past the bridge and is looking back**, at a car
   130-160 m short of it. The occluder is 26-57 m from the lens while the
   subject is at 183 m. My analytic slab model happened to be direction-agnostic
   so it survived this, but the mental picture I had was backwards.

### The fix is unchanged, and now better supported

`PONT_S = 2410 -> 2460` was already tested against the whole of beat 5 rather
than the known window. With the ray-cast confirming the bridge is the **only**
lap occluder, that move now closes the entire beat-5 occlusion problem rather
than one of two clusters.

**One thing the ray-cast cannot see and my proxy could:** `dressing` and `items`
were not in the rebuilt world, so **`DR_BridgeBanners` is absent from it**. The
proxy put the banners in the corridor out to f2196. They hang on this bridge's
faces — the same faces R2-256 records a collision on — and **they will not
follow `PONT_S` on their own.**

---

## R2-665 — the farm blocked this measurement twice, for two different reasons, and the second one was mine

Recorded because both are reusable lessons rather than incidents.

1. **`WorkerBusy` burned retry attempts instead of requeueing.** The guard
   itself is right — deploying over a worker mid-frame would SIGKILL minutes of
   GPU time — but a refusal spent an attempt, and three attempts expired inside
   a single 39-second frame while both cards held 14-hour sequence passes. Four
   jobs died at `3/3` having never run. **Fixed by the farm agent**: it now
   requeues without spending an attempt, after a 90 s backoff, verified by an
   exec job completing between two frames of a running pass.
2. **`StaleBundle`, and that one was self-inflicted.** The bundle was 96 files /
   38.3 MB drawn from `world/*.py`, `world/items/*` and `telemetry/*.csv` —
   directories that eight agents are actively editing. The digest is taken at
   submit and re-checked at dispatch, and the 90 s backoff *widens* that window.
   **`--include` must name the files a script actually reads, not the
   directories they live in.**

The lesson worth keeping: **a farm job's bundle is a shared-state dependency,
and the busier the tree the narrower it has to be.** Meanwhile the entire
occlusion question turned out to be answerable without the farm at all — once
from source constants (R2-660) and once from an existing point dump (R2-664).

---

## R2-666 — two occlusions nobody was looking for, and one of them is on the film's last frame

Both fall out of the same sweep and neither was in anyone's brief.

**Beat 4: the car is wholly hidden behind `ARCH_PitBuilding_Shell` for three
frames (f1114-1116), six affected.** The occluder is **10-11 m from the lens** —
this is the transit, threading past the pit building at close range. It is a
harder blackout than the bridge in one respect: at 10 m there is no possibility
of reading the car through anything.

**Beat 6: `BR_FenceMesh_L03` covers the car completely on f2976, f2977 and
f2978 — the last three frames of the film.** It is the **fence** channel, so in
reality the car is seen *through* a catch fence rather than hidden by it, and
this is a composition question rather than a blackout. But:

> `BR_FenceMesh_L03` is **already a logged defect**. R2's placement audit
> measured it at **+7.105 m of lateral intrusion against a 7.39 m half-width at
> s = 926** — "spans the racing surface", crossing from one edge nearly to the
> other.

So the object standing between the lens and the car on the closing frame of the
film is the same object already measured as standing on the racing line. That is
not a coincidence to be filed twice: **fixing the L03 intrusion should be
checked against the closing frame**, and whoever closes that defect should be
told the closing frame is a witness for it.
