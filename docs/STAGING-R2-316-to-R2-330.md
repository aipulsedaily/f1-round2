# STAGING — R2-316 to R2-330. Beat 1's presentation: focus, framing, and what actually blurs it

Owner of this block: the beat-1 presentation agent. **`docs/DEFECT-LOG-R2.md` is
not edited here.** Highest merged there is R2-278.

Everything below is measured on `render/film14.blend` at `FILM_EXPOSURE = -3.628`
(imported from `world/film_exposure.py`, verified equal in the dump's own
selftest) and on 4K frames rendered on the 5090 through `~/vast-render`.

## THE VERDICT, IN FOUR LINES

1. **The focus track is correct and the suspicion against it is withdrawn.** At
   every one of the fifteen stations `focus_distance` lands on the presented
   cluster's centre to within **0.053 m worst, 0.000-0.028 m typical**. The
   `CAR_ROOT` comparison that suspected it was measuring a body 1.904 m away from
   the one on screen (R2-319).
2. **The framing is not correct, and the gate that was supposed to catch it could
   not.** All fifteen clusters overflow their own presentation frame, 1.06x to
   2.59x, seven of them in both axes. `edge_angle_deg` was zero by construction
   (R2-316, R2-317).
3. **The two are one defect, and framing comes first — as a precondition, not a
   preference.** At the shipped standoff the aperture that would hold a corner
   cluster sharp is **f/37**. At a standoff that makes it fit, it is **f/6.9**.
   `N = D (fill h)^2 / (2 c E^2)`, independent of lens and of distance (R2-320).
4. **Neither is the biggest reason the middle third does not read.** The camera
   smears the picture by a median of **42 px and up to 808 px** at 4K, and the
   pixels confirm the direction to within a few degrees (R2-321, R2-329). Beat
   1's own pan limit, 0.12 frame-widths per frame, *permits* 230 px of smear
   because it is written in a unit that has no pixels in it. **The framing fix is
   the only one of the three levers that pays into all three.**

New instruments, all with selftests that include a negative control:

| tool | what it settles |
|---|---|
| `tools/beat1_dof_dump.py` | the film's ACTUAL per-frame camera DOF and per-cluster world bboxes, out of the 4.53 GB blend |
| `tools/beat1_focus_track.py` | focus against the PRESENTED CLUSTER, per frame, plus each cluster's best moment in all 792 frames |
| `tools/beat1_present_gate.py` | does the cluster FIT, and does its depth fit the depth of field |
| `tools/beat1_smear.py` | the 180-degree shutter's smear in 4K pixels at each station |
| `tools/campath_diff.py` | before/after path diff with the R2-103 floor handled and the self-null printed first |
| `tools/beat1_restand_candidate.py` | the corrected candidate sheet, written to `work/`, never to `docs/` |
| `tools/blur_anisotropy.py` | defocus vs motion blur, from the rendered pixels, no second render needed |

---

## R2-316 — `presentation_framing` reported `edge_angle_deg = 0.000` fifteen times, and could not have reported anything else

`tools/build_beatsheet.py` graded every beat-1 presentation with

```
edge = max(0.0, ang - degrees(asin(rad / nd)))
```

`ang` is the angle from the optical axis to the cluster's **centre**, and
`camera_station()` places the lens on the ray through that centre. **`ang` is
therefore identically zero at every presentation by construction.** Subtracting
the cluster's own angular radius from zero and clamping at zero measures the
angle to the **near** edge of a body the axis passes through — which is inside
the frame always, for every cluster, at every distance, on every lens.

The sign in front of `asin` is the whole defect. The edge that overflows is the
**far** one.

> **This is R2-062's lesson a second time in the same beat.** There, the rig's aim
> gate scored a 9.14 m dash at 7.24 degrees and passed it, because a camera can be
> pointed exactly at its subject and still be moving far too fast to photograph
> it. Here the same gate scores a cluster that is two and a half times too big for
> the frame at 0.00 degrees, because a camera can be pointed exactly at its
> subject and still be far too close to contain it. **Aim was measured twice.
> Photographability has never been measured at all.**

**Fixed.** The block now projects the eight bounding-box corners and reports what
the audience gets: `extent_frac_frame_h` / `extent_frac_frame_w`, the cluster's
depth span, the f-number that would hold that depth inside 2 px at 4K, and the
standoff at which it would fit on the lens it already has. The near-edge test is
**kept unchanged for the bridges and the close-out** — see R2-318.

Gate behaviour, `--check` against the shipped sheet, which writes nothing:

```
before   15 presentations, edge 0.00 deg each        STAGE RESULT: BEATSHEET_OK
after    15 presentations, all 15 FAIL on fit        STAGE RESULT: BEATSHEET_VIOLATION
```

and against the corrected candidate sheet: **0 framing failures, 15/15 fit.** A
gate that has never failed has not been shown to work; this one now fails on the
artefact known to be bad and passes on the artefact built to be good.

---

## R2-317 — every one of the fifteen presentations overflows its own frame, 1.06x to 2.59x

`standoff = max(radius * 1.55 + 0.42, 0.75)`, with `radius` the bbox
half-diagonal, fixes the subtended **solid angle** and knows nothing about the
lens. Measured, on the shipped stations (`tools/beat1_present_gate.py`, and
independently by the corrected gate inside `build_beatsheet.py` — two
implementations, same numbers):

| cluster | f | lens | f-stop | fills H | fills W | depth | blur at near face |
|---|---|---|---|---|---|---|---|
| MB | 1 | 35 | 2.8 | **2.14** | 0.34 | 1.44 m | 1.7 px |
| FW | 62 | 35 | 2.8 | **1.77** | 0.90 | 0.84 m | 5.8 px |
| NOSE | 85 | 58 | 2.2 | **2.59** | 0.63 | 0.44 m | 23.7 px |
| CI | 124 | 58 | 2.2 | **1.91** | **1.61** | 0.78 m | 40.8 px |
| halo_assembly | 155 | 35 | 2.8 | 0.75 | **1.11** | 1.07 m | 10.0 px |
| SP | 191 | 35 | 2.8 | **1.68** | 0.69 | 0.79 m | 3.6 px |
| FD | 236 | 35 | 2.8 | **1.85** | 0.52 | 0.70 m | 1.4 px |
| RW | 276 | 58 | 2.2 | **2.46** | **1.14** | 1.34 m | 86.4 px |
| EC | 305 | 35 | 2.8 | 0.75 | **1.21** | 1.10 m | 5.3 px |
| BB | 339 | 35 | 2.8 | **1.72** | 0.76 | 1.02 m | 10.3 px |
| SW | 386 | 58 | 2.2 | **1.06** | 0.70 | 0.25 m | 46.0 px |
| CORNER_RR | 463 | 58 | 2.2 | **2.54** | **1.44** | 1.34 m | 86.1 px |
| CORNER_RL | 512 | 58 | 2.2 | **2.44** | **1.33** | 1.25 m | 76.3 px |
| CORNER_FR | 551 | 58 | 2.2 | **2.29** | **1.44** | 1.28 m | 83.9 px |
| CORNER_FL | 591 | 58 | 2.2 | **2.32** | **1.45** | 1.30 m | 85.6 px |

**Fifteen of fifteen do not fit. Seven overflow in BOTH axes**, so there is no
crop of the frame that contains them. The audience is shown a fragment.

Confirmed in the picture and not only in the projection — `render/b1focus` at
3840x2160, 512 samples, scene DOF: f120 is one defocused tube across the frame
with no identifiable part in it; f460 is one rear corner larger than the frame
with its suspension links drawn out into streaks.

---

## R2-318 — the corrected gate must not be pointed at the close-out, and why that is not special pleading

Re-graded on the far edge, the two hand-authored close-out keys fail too: the
front wing at t = 25.90 reaches 30.46 deg against an 11.91 deg half-frame.

**That is the shot.** Those keys are composed wides in which a wing running off
the edge of frame is the composition, and a review has already accepted them. The
fit test is a claim about a **presentation** — a station built to make one cluster
large enough to read has failed if the cluster does not fit. Applied to a composed
wide it says nothing.

So the fit test is gated on `presentation_dir_measured`, and the bridges and the
close-out keep the **old near-edge test unchanged**, still reporting RW at t=27.30
as 7.31 deg inside a 14.21 deg half-frame. A corrected metric that fails two
frames a review already accepted is a corrected metric nobody will believe.

---

## R2-319 — THE FOCUS TRACK IS NOT BROKEN. The confounded `CAR_ROOT` comparison is withdrawn

The suspicion was that beat 1's `focus_distance` does not track its subject,
based on samples against the distance to `CAR_ROOT`. **In beat 1 the car is
exploded across 616 parts and `CAR_ROOT` is the assembled body's origin.** The
mean gap between "distance to CAR_ROOT" and "distance to the cluster actually
being presented" is **1.904 m** — that is the confound, measured, and it is now a
standing negative control inside `tools/beat1_focus_track.py --selftest`.

Against the right reference, from the blend, at the fifteen stations:

```
worst |focus_distance - range to the presented cluster's CENTRE|   0.053 m
typical                                                            0.000-0.028 m
```

**The focus lands on the presented cluster's centre to within a few centimetres
at every station.** `camera_station()` returns the standoff and
`build_beatsheet.py` writes that same number into `focus_distance_m`, so it is
correct by construction and the construction holds. Beat 1's focus track is
correct in the sense it was accused of being wrong.

**What is wrong is that the cluster is far deeper than the depth of field.** At
58 mm, f/2.2, focused at 1.503 m, the range that stays inside 2 px at 4K is
**53 mm**. The corner cluster it is presenting is **1300 mm deep**. The centre is
sharp to 0.2 px and the near face is blurred by **86 px**:

```
CORNER_FL f591   focus 1.503 m   depth 0.87 -> 2.17 m   DOF 1.477 -> 1.530 m
                 blur: centre 0.2 px   far face 36 px   NEAR FACE 89 px
```

13 of the 15 presentations are not fully in focus; only MB and FD are, and only
because they are the two furthest stations.

---

## R2-320 — framing is a PRECONDITION of focus, not a parallel defect, and the law says so in closed form

The exact thin-lens blur, `C = (f/N) f |s - s_f| / ((s_f - f) s)`, inverted for
the f-number that holds a body of depth `D` and widest extent `E` sharp to a
circle `c` while it fills a fraction `fill` of a frame of sensor height `h`:

```
    N_required  =  D * (fill * h)^2 / (2 c E^2)
```

**Independent of focal length and of standoff.** Both cancel, because the
standoff that achieves a given fill is itself proportional to the focal length.
Two consequences decide the order of the fixes:

1. **At the shipped standoff there is no aperture that works.** The corner
   clusters fill 2.3-2.5x the frame, and holding their depth inside 2 px there
   needs **f/35 to f/37**. That is not a photographable aperture, it destroys the
   background separation the brief asks for, and it is deep into diffraction.
2. **At a standoff that makes them FIT, f/5.2 to f/9.0 suffices** — a normal
   aperture, and the rest of the film already runs at f/5.6.

> **Fix the framing first. Not as a preference — as a precondition.** The focus
> cannot be fixed at today's standoff by any means. Once the fill target is
> chosen the required aperture follows in closed form and is invariant to *how*
> the fill was achieved, so the aperture is a one-line consequence of the framing
> decision and never needs its own iteration.

---

## R2-321 — the largest reason beat 1's middle third does not read is neither of them. It is the 180-degree shutter

`use_motion_blur = True`, `motion_blur_position = CENTER`, shutter 0.5 frames
(`anim/build_camera_rig.py`:772). A 180-degree shutter smears a static point by
half its per-frame image displacement. Measured at the fifteen stations, in 4K
pixels, holding the cluster box fixed between f and f+1 so this isolates the
**camera's** contribution:

```
median smear at the presented cluster's CENTRE      42.3 px
worst at a station                                 189.4 px   NOSE, f85
worst measured anywhere in the tour                808.0 px   f532
best frames of the close-out                    1.6-28 px    f648-792
```

**The beat sheet's own pan limit permits this and nobody converted it into
pixels.** `weave_spec.pan_limit_widths_per_frame = 0.12`; the sheet reports the
tour peaking at 0.0939. **0.0939 of 3840 px is 361 px per frame, and half of that
is 180 px of smear.** The limit is expressed in a unit that is resolution-free,
and the picture is not.

This is why f460's suspension links are ribbons and why the 100 % crop of f200
has no edge in it anywhere: at those frames the depth-of-field blur is 2-8 px and
the motion blur is 40-120 px. **A DOF fix alone would not have made the middle
third read.**

**It also explains the protected region without one word about taste.** Across all
791 measurable frames of beat 1 (`tools/beat1_smear_profile.py`, the smear of
whichever cluster is nearest the optical axis at each frame):

```
                          n    median      p90       max   frames over 20 px
beat 1, all             791    42.1 px  149.4 px  628.1 px   580  (73 %)
  the presentation tour 590    54.7 px  184.5 px  628.1 px   519  (88 %)
  CORNER_FL + close-out  57    30.1 px   49.8 px   62.8 px    55  (96 %)
  PROTECTED f648-792    144     1.5 px    6.7 px   28.3 px     6  ( 4 %)
```

**The region a review called the best material in the film is the region where the
camera stops moving: 1.5 px of median smear against 54.7 px over the tour, a
factor of 36.** 88 % of the tour is over 20 px and 4 % of the protected region is.
No aesthetic judgement is needed to separate them.

The three defects share one lever. Pulling a station back to make its cluster fit
also cuts the parallax smear and lowers the angular rate needed to hold the
subject, so the framing fix is the only one of the three that pays into all
three.

---

## R2-322 — a presentation WINDOW is not "on screen", and 127 frames prove it

`beat1.schedule` runs each cluster's window from **its own station's arrival to
the NEXT station's arrival**, so the last frames of a window are spent flying
away from the thing the window names. At f500, the cluster its window nominates
(`CORNER_RR`) is **95.68 deg off axis** — beside the camera, not in the picture.
`continuity_gate` already prints the same fact from the other side: 127 beat-1
frames have the nominated cluster more than 25 deg off axis, worst 76.94 deg.

Any focus verdict taken at "the frames where the sheet says X is presented" is
therefore grading the camera on frames where X is not in shot — **the same class
of confound as measuring against `CAR_ROOT`, one level up.** Both are now
negative controls, and `tools/beat1_focus_track.py --best` asks the question the
brief actually asks instead: does every cluster get **some** frame where it is on
screen, whole, and sharp?

Its answer needs reading with care and is logged here so it is not misquoted:
15 of 15 clusters do have such a frame, **but for eleven of them that frame is in
the close-out (f625-792), where the car is assembled and the part is 20-30 % of
frame height as one detail of a whole car.** That is not a presentation. At the
station built to present it, every one of the fifteen is too big for the frame.

---

## R2-323 — the candidate fix clears all fifteen, and breaks the speed solve in five places

`tools/beat1_restand_candidate.py` pulls each station back along its own **measured**
presentation direction until the cluster fills 0.85 of the limiting frame
dimension, sets `focus_distance_m` to the new standoff and `fstop` to the
f-number the law above requires. Direction, `look_at` and lens are untouched, so
`presentation_normals` still chooses which face the audience sees.

```
framing         15/15 FAIL  ->  0/15 FAIL          all fit at 0.85 or under
apertures       f/2.2-2.8   ->  f/1.4-8.9 (SW f/23.7, see R2-324)
mean standoff   2.033 m     ->  4.436 m   (2.18x)
key-to-key path 54.958 m    ->  67.228 m  (1.22x)
```

**And it fails the R2-062 speed gate in five places**, worst 5.28-5.90 m/s
between f551 and f591 against a 4.00 m/s limit, because the tour was timed for
the closer stations and the moves are now longer inside the same 33 s.

> **The framing fix is not a standoff edit. It is a re-solve.** Held-Karp has to
> re-run over the new station positions and the time allocation with it. At the
> same speed limit the candidate needs **+7.4 s (33.0 -> 40.4 s)** — which the
> brief explicitly permits ("total runtime may grow toward ~2 minutes and that is
> fine"), but which moves every beat boundary after it and is a bigger unit of
> work than this block.

The alternative that costs no time is a **wider lens at the same station** — the
extent is linear in focal length, so 58 mm -> 19-27 mm and 35 mm -> 14-18 mm makes
every cluster fit without moving one camera, and divides the smear of R2-321 by
the same ratio. It is rejected here as a recommendation because a 14 mm lens
1.4 m from a monocoque is a different film, but it is the lever if the runtime
cannot move.

---

## R2-324 — the steering wheel cannot be fixed by standoff, and needs its own call

`SW` is 0.128 x 0.280 x 0.230 m. Its standoff is clamped by `max(..., 0.75)` and
it fits the frame at **0.935 m**, so the candidate barely moves it. But at 0.935 m
on a 58 mm lens its 0.245 m of depth needs **f/23.7** to stay inside 2 px — an
aperture where diffraction on a 9.375 um pixel is itself the limit.

SW is the one cluster where the closed-form law has no comfortable answer, because
its depth-to-width ratio is the worst in the field. The choices are a shorter lens
at the same distance, a much longer lens much further back, or accepting that the
rim is sharp and the column stub is not. **Open. Not decided here.**

---

## R2-325 — R2-103's quaternion floor, reproduced on this block's own comparator, before any verdict was read off it

The stored path quaternions are rounded to six decimals, so `|q|` is off unit by
about 8e-7 and `2*acos(|dot|)` amplifies that by a square root. Run as the
self-null, a path file against a **bit-identical copy of itself**:

```
raw stored q      2978 frames   dp 0 m   dq 0.203165 deg   dlens 0 mm
re-normalised q   2978 frames   dp 0 m   dq 0.000003 deg   dlens 0 mm
```

**0.203 deg is the floor, on a file compared against itself.** Every rotation
figure in R2-326 is taken on re-normalised, sign-normalised quaternions, and the
self-null is printed above every comparison `tools/campath_diff.py` makes.

Separately, rebuilding the rig from the **shipped** sheet reproduces
`render/film14_path.json` exactly — 0 m of position, 0 mm of lens, and every
quaternion component byte-identical across all 2978 frames. That is the null the
candidate is measured against.

---

## R2-326 — what the candidate does to the protected f648-792 region: 104 px at its first frame, nothing after f720

The question that blocked this work was whether moving `CORNER_FL` at f591 reaches
into f648-792, which a review called the best material in the film. Measured on
the built path, candidate against shipped:

```
                             worst |dp|        worst rotation
beat 1        f1-792           6.6156 m @f1        26.119 deg @f236
  f1-590 (the presentations)   6.6156 m @f1        26.119 deg @f236
  f591-647 (CORNER_FL + close) 1.8868 m @f591       0.003 deg @f593
  PROTECTED f648-792           0.1151 m @f648       0.000 deg @f650
beats 2-6     f793-2978        0.0000 m             0.000 deg
```

In screen pixels, using the range the film's own focus is holding at each frame:

```
f648  118 mm -> 104 px      f665   68 mm ->  47 px      f700  15 mm ->  8 px
f655    0 mm ->   0 px      f720  0.3 mm ->   0 px      f754   0 mm ->  0 px
```

**Beats 2 to 6 are bit-identical. The seam does not move at all** (R2-327). The
protected region is perturbed only at its first ~70 frames, by at most 104 px,
with zero rotation change, and is exactly unchanged from f720 on.

**That is not zero, and it is not being reported as zero.** 104 px at 4K is
visible. The existing machinery to remove it is already in `build_beatsheet.py` —
CORNER_FL's slot is pinned and there is a handle pin at f754 for exactly this
class of bleed — and a re-solve that keeps CORNER_FL's *time* fixed while moving
its *position* should be able to hold the close-out. **Not attempted here**, because
`render/film*.blend` is off limits to this block and a station change that cannot
be rendered cannot be judged in the only currency this project accepts.

---

## R2-327 — the four seam invariants, before and after, from the same script

`tools/seam_gate.py`, same invocation, `render/film14_path.json` and
`docs/beat_sheet.json`:

| | before | after (shipped, unchanged) | candidate (`work/b1rig/after_path.json`) |
|---|---|---|---|
| `chord_m` | 2.0893 | 2.0893 | 2.0893 |
| `speed_ms` | 1.2727 | 1.2727 | 1.2727 |
| `look_angle_deg` | 13.2504 | 13.2504 | 13.2504 |
| `lens_delta_mm` | -0.051 | -0.051 | -0.051 |
| built path vs declared keys | f754 0.0000 mm, f793 0.0000 mm | identical | identical |
| peak speed | 8.9124 m/s @f804 | identical | identical |
| worst BULGE | 1.407x f815-817 | identical | identical |
| worst LOCAL accel | 3.59x @f796 | identical | identical |
| verdict | SEAM_OK | SEAM_OK | SEAM_OK |

The shipped column cannot have moved: **this block changed no camera data at
all.** The one edit to `tools/build_beatsheet.py` is inside the report block, and
`--check` mode writes nothing. The candidate column is identical because the seam
lives at t = 31.4 and t = 33.041667, both outside beat 1's presentations, and the
candidate's perturbation is exactly zero from f720.

---

## R2-328 — what was NOT confirmed

* **The motion-blur decomposition is measured but not yet isolated in a
  rendered A/B.** The smear figures in R2-321 are geometry from the built path,
  and the DOF-off control frames (f200, f400, f591 at `--dof off`) were queued and
  are reported separately. Until one of them is looked at, "motion blur dominates
  DOF at f200" rests on the arithmetic and on the visible direction of the streaks,
  not on a controlled pair.
* **No frame of the candidate has been rendered**, because `render/film*.blend`
  is off limits to this block. Every candidate number above is geometry.
* **The re-solve is not attempted**, so "+7.4 s" is the cost at the same speed
  limit on the same tour order, not the cost of the tour Held-Karp would choose
  for the new stations. It could be less.
* **SW is open** (R2-324).
* **Whether f/5.2-9.0 is the right LOOK** is a judgement nobody has made from a
  frame. The arithmetic says it is the aperture that makes the presented part
  read; it also flattens the separation the brief asks for. The background at
  10 m still blurs by 8-12 px at f/6.5 focused at 4 m, which is separation, but
  it is not the f/2.2 look.

---

## R2-329 — the motion-blur finding, confirmed in the PIXELS and not only in the geometry

R2-321's smear figures are geometry off the built path. `tools/blur_anisotropy.py`
settles them from the rendered frames alone, with no second render, because
**defocus and motion blur do not have the same shape**: the circle of confusion is
a circle and suppresses gradients equally in every direction, while a 180-degree
shutter is a line integral along one direction and leaves the gradients ACROSS it
almost intact.

The structure tensor of the frame gives the axis gradients survive in. The camera
path independently predicts the smear direction. **They are computed from
disjoint inputs and must agree.**

| frame | predicted surviving axis, from the path | measured, from the pixels | delta | predicted smear | anisotropy |
|---|---|---|---|---|---|
| f120 | 17.8 deg | 11.4 deg | 6.4 | 107 px | 0.585 |
| f200 | 162.4 deg | 160.2 deg | **2.2** | 40 px | 0.845 |
| f300 | 88.6 deg | 92.9 deg | **4.3** | 85 px | 0.896 |
| f460 | 52.4 deg | 51.5 deg | **0.9** | 117 px | 0.832 |
| f400 | 169.1 deg | 90.2 deg | **79** | **11 px** | **0.401** |

Four of the five agree to within 6.4 degrees on a quantity nothing in the image
pipeline was told about. **The middle third is smeared by the camera, and the
direction proves it.**

**And the fifth is the point, not the exception.** f400 is the one frame of the
five where the predicted smear is small — 11 px against 40-117 — and it is also
the only one whose anisotropy collapses, to 0.40 against 0.83-0.90. With no
smear to align to, the surviving axis reverts to the scene's own structure (the
turntable rim that fills its lower half). **So the instrument separates the two
causes rather than merely confirming one:** f120, f200, f300 and f460 are
motion-blurred frames; f400 — the frame the earlier agent flagged as "a bright
smear, no subject in focus" — is a genuine depth-of-field frame, and its subject
is 0.328 m behind the focus plane with 29.5 px of defocus and its centre outside
the vertical frame.

Limit, stated with the finding: a sharp picture of parallel edges is anisotropic
before anything blurs it, and the selftest carries that case explicitly (sharp
horizontal stripes read 1.0000). The verdict above rests on the AGREEMENT of two
independent estimates of a direction, never on the magnitude alone.
