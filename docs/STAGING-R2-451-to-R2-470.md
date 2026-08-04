# STAGING — R2-451 to R2-470

Block: the film opens with no identifiable subject. Owner of R2-451..R2-470.
Nothing here is written into `docs/DEFECT-LOG-R2.md`; that file has one owner.

---

## R2-451 — the film looks 84.15 degrees down because `presentation_normals.py` was asked which direction shows the MOST of a part, and for a racing car that is a plan view

Two lines of code, in two files, compose into the opening frame.

`tools/presentation_normals.py` chooses each cluster's presentation direction as

```
argmax_d  projected_area(d) * (1 + 0.45 * distinct_materials(d))
```

`tools/build_beatsheet.py:camera_station()` then places the lens at
`centre + normal * standoff` and aims it at `centre`. **So the camera's
elevation IS the presentation normal's elevation, exactly, by construction.**

A Formula 1 car and every one of its major assemblies is a flat, wide body lying
horizontally. The direction from which you see the most of a flat horizontal body
is from directly overhead. **The scorer was not broken. It answered the question
it was asked, correctly, and the question was wrong.**

Measured, `docs/presentation_normals.json`, all fifteen, sorted by elevation:

```
SP             [+0.102,+0.000,+0.995]   84.15    margin over runner-up 0.0025
NOSE           [+0.102,+0.000,+0.995]   84.15                          0.0086
MB             [+0.102,+0.000,+0.995]   84.15                          0.0015
FD             [+0.102,+0.000,+0.995]   84.15                          0.0085
FW             [+0.163,+0.212,+0.964]   74.48                          0.0036
BB             [-0.094,+0.349,+0.932]   68.79                          0.0042
CI             [+0.193,-0.412,+0.891]   62.95                          0.0044
EC             [-0.028,+0.604,+0.797]   52.83                          0.0174
CORNER_RL      [+0.144,-0.639,+0.755]   49.04                          0.0004
CORNER_RR      [-0.270,+0.646,+0.714]   45.52                          0.0020
RW             [+0.127,+0.739,+0.661]   41.41                          0.0005
CORNER_FL      [-0.745,+0.382,+0.547]   33.15                          0.0148
CORNER_FR      [-0.774,-0.367,+0.516]   31.04                          0.0011
SW             [-0.879,+0.110,+0.464]   27.62                          0.0003
halo_assembly  [+0.127,-0.907,+0.401]   23.64                          0.0065
```

**Every one of the fifteen points upward. The shallowest is 23.64 degrees.**

**Four of them share one vector**, and it is not a coincidence worth shrugging at:
`[0.10193, 0, 0.99479]` is **sample index 0 of the Fibonacci sphere** —
`z = 1 - 1/192`, `theta = 0` — the single most-overhead direction the sampler
owns. MB is the film's first frame.

**The margins are the second half of the finding.** MB wins by 0.15 %, CORNER_RL
by 0.04 %, SW by 0.03 %. These are not decisions, they are ties. Dumping the full
192-direction score surface (`tools/beat1_view_surface.py`, which reproduces the
shipped winner for all fifteen clusters and is asserted to) shows why:

```
MB, top 16 directions, elevation : score as a fraction of the best
  84:1.000  80:0.999  77:0.992  74:0.977  69:0.974  72:0.972  67:0.966  71:0.952
  62:0.945  63:0.943  57:0.937  64:0.932  58:0.923  53:0.920  66:0.917  60:0.912
```

**Sixteen directions spanning 84 degrees to 53 degrees, all inside 8 % of each
other. The objective is nearly flat in elevation, so its argmax is a coin flip —
and the coin landed on the pole.** The objective cannot tell 84 degrees from
53 degrees. The picture can: one is a diagram and the other is a photograph.

**Confirmed against the built film, not only against the source.**
`tools/beat1_nadir_cause.py` compares each cluster's normal elevation with the
camera's actual elevation at that station in `render/film14_path.json`:

```
cluster    normal elev    path elev    sum (must be 0 if the normal IS the aim)
MB              84.15        84.15       -0.00
FD              84.15        83.97        0.18
NOSE            84.15        84.08        0.07
SP              84.15        84.34       -0.19
...  every station within 2.12 deg, the residual being camera_station()'s own
     7 deg weave tilt
```

`tools/beat1_elevation.py` reproduces every published R2-425 figure exactly —
first frame -84.15, first-60 median -80.86, 187 frames (23.6 %) steeper than 70,
120 (15.2 %) steeper than 80, beat medians -42.39 / -3.28 / -7.53 / -14.11.

---

## R2-452 — the standoff law is NOT the cause of the steep angle, and here is the test rather than the assertion

The brief for this block raised the possibility that `standoff = radius * 1.55 +
0.42` is the root of both defects — "a camera that must sit close enough to fill
the frame with a small cluster ends up steeply above it" — and asked for it to be
tested rather than assumed.

**It is refuted.** The two laws are the RADIUS and the DIRECTION of one polar
placement and neither can produce the other. Measured: at the **shipped**
standoff, the elevation band a lens can occupy while staying inside the room
(`tools/beat1_nadir_cause.py`):

```
cluster      standoff   elev min   elev max   SHIPPED   throw@shipped
MB              4.859      -4.45      61.82     84.15        0.08 m
FD              3.667      -1.25      90.00     84.15        0.05 m
NOSE            1.378      -8.00      90.00     84.15        0.15 m
SP              2.489      -8.00      39.85     84.15        0.36 m
CORNER_FL       1.503      -8.00      90.00     33.15        1.63 m
...
clusters whose reachable band EXCLUDES a shallow (<30 deg) camera:  NONE
```

**Not one of the fifteen was forced upward by its standoff. Every one of them
could have been shot from under 30 degrees without moving one millimetre of
standoff and without leaving the room.**

Two things fell out of the same measurement and both are worse than the thing
being tested.

**(1) `throw` — the distance from the cluster to the floor along the optical axis
extended past it, `centre_z / tan(elev)`. At MB's shipped station it is 0.08 m.**
The lit showroom floor is eight centimetres behind the monocoque. The brief asks
for two presentation devices and that number kills both at once, at any aperture,
under any light rig: *"edge separation from the dark background"* has no dark
background when the background is the floor, and *"DOF as the presenter"* cannot
defocus a background that is at the subject's own distance. R2-425 saw the
consequence in the pixels without naming it — "floor signage cut to
`AN ...EELBASE`". That signage is not beside the subject. It **is** the
background.

**(2) The lens is above the lights.** `tools/beat1_view_surface.py` dumps every
lamp in `world/beat1_anim.blend`: 23 of them, the six showroom spots at
**z = 5.590**, the key at 4.600, nothing higher. The film's first frame is at
**z = 5.6607**. **Every light in the room is below the camera.** SP is worse at
z = 5.991. `tools/build_beatsheet.py:621` asserts "spot rigs from z 5.11" in a
comment with no citation; the measurement says 5.590, and the comment is wrong
by 0.48 m in the direction that hid this.

**Where the two laws DO interact, stated precisely because the general claim is
false.** `fill` at the shipped standoff and shipped lens, varying only the
direction, ranked worst-first out of 109 sampled directions:

```
MB rank 2/109      FW 4/109      NOSE 4/109      BB 4/109      FD 7/109
SP 17/109          CORNER_RR 17  RW 24  CORNER_RL 26  CORNER_FL 37  CORNER_FR 43
CI 38/109          halo 53/109   SW 87/109
```

**For the near-nadir clusters the shipped direction is also among the very worst
for frame overflow — the direction of maximum projected AREA is close to the
direction of maximum projected EXTENT for a flat body, so the two defects
compound. Below about 50 degrees they are uncorrelated.** Only 1 of 15 is in the
top 3 overall, so "the scorer maximises the thing that overflows" is true of the
population that matters and false as a general statement. It is reported both
ways here because the first draft of this entry asserted the general version.

---

## R2-453 — the documented safeguard against exactly this defect does not exist. Nothing has ever read `ranked`

`tools/presentation_normals.py` has carried this paragraph since it was written:

> The best direction is not always USABLE: SP's highest-scoring view is straight
> up, and its exploded centre sits at z 4.2 m, so a 2.54 m standoff put the lens
> at z 6.7 m — through the 6.5 m ceiling. That render came back as a flat grey
> frame of the ceiling slab's underside. The camera placer therefore needs
> somewhere to go next. Emitting the top 16 lets it **walk down the ranking until
> a station fits inside the room**.

**The previous author found this defect, in a rendered frame, and wrote down the
fix. The fix was never implemented.** `grep -rn ranked --include=*.py` over the
whole repository returns `catch_fence_cranked_head`, `spectator_crowd`, and three
unrelated locals. **No code has ever read the `ranked` field.**

The consequence is measurable and shipped: SP's station sits at z 5.991 — inside
the ceiling at 6.20 but **0.40 m above the spot rigs it is supposed to be lit
by**. The walk-down that would have caught it was a containment check that never
ran, and even as described it would not have caught MB: MB's lens at z 5.6607 is
"inside the room" by 0.54 m and is still a plan view from above the lighting rig.

> **A safeguard described in a docstring is not a safeguard. This one was
> load-bearing in the log, in the reasoning of the file that emits the data, and
> in nobody's execution path.** It also names its own falsifier — the ceiling
> render — so it read as a fix that had already been validated once.

---

## R2-454 — the depression cap is the FILM'S OWN number, and the more elegant law is recorded being rejected

A cap on how steeply a presentation may look down needs a source that is not
taste. Measured off `render/film14_path.json`, `tools/beat1_elevation.py`:

```
PROTECTED f648-792, which a review called the best material in the film
                                   median -10.88    range -16.77 .. -5.28
beats 2-6, 2,186 frames, every one of them accepted material
                                   median -10.56
the four HAND-AUTHORED close-out keys inside beat 1 itself
                                   -11.08, -13.50, -14.41, -24.91
the two hand-authored BRIDGE keys (transitions, not presentations)
                                   -23.86, -35.66
the presentation tour f1-590, the region under repair
                                   median -54.42    min -84.34
```

**The film has already converged on about -11 degrees everywhere it works and on
-54 degrees in the one place it does not.** The deepest depression any authored,
review-accepted *presentation* key uses is **-24.91**. So the law is: **a
presentation station may not look down more steeply than 25 degrees** — the
film's own practice applied to the region that departed from it.

**The more elegant law is rejected here and the rejection is the point.** I
derived: *the horizon must be inside the frame*, `elev <= atan(sensor_h/2 /
lens)`. It is exact, lens-aware, has no free parameter, and states precisely when
the entire frame becomes floor — 16.13 degrees on a 35 mm lens, 9.90 on a 58 mm.
**It fails the close-out's own first key**, which sits at -24.91 degrees inside an
11.91-degree half-frame and which a review has already accepted.

> **A frame can be almost entirely floor and still be the best shot in the film.**
> R2-318 states the rule this is an instance of: a corrected metric that fails
> frames a review already passed is a corrected metric nobody will believe. I had
> the better-looking law and the film had the better number.

Two further bounds, both measured, neither derived:

* **the lens stays under the light rig** — `cam_z <= 5.29`, from the measured
  spot plane at 5.590 with 0.30 m of clearance;
* **the lens clears the rope barrier** — `cam_z >= 1.20`. `world/beat1_anim.blend`
  puts `Barrier_Post_*` at radius 6.84–7.06 topping out at **z 0.915** and
  `Barrier_Rail_*` at 0.785, so the close-out's stated "more than 1.2 m above it"
  rule is 0.285 m of real margin and not a guess. It is kept unchanged rather than
  loosened, even though loosening it would have unblocked FW (see R2-456).

**And the tie-break spends the plateau instead of throwing it away.** Because the
objective is flat in elevation (R2-451), the choice is: *the shallowest direction
within 3 % of the best score that satisfies the bounds*. The 3 % is declared, its
per-cluster cost is printed, and without it seven of fifteen clusters pile onto
the cap at exactly 23.64 degrees, which is a beat with no weave left in it.

---

## R2-455 — the nadir framing was BUYING THE SCHEDULE, and this is why lengthening beat 1 cannot pay for the fix

Re-aiming all fifteen directions makes beat 1's tour unschedulable. Two mechanisms,
both geometric:

* **Stations swing outward.** A station is `centre + d * standoff`. With `d`
  near-vertical every station sits nearly directly ABOVE its cluster and the
  camera hovers over a field 6 m across. With `d` shallow the station moves out to
  a horizontal radius of `standoff * cos(elev)` and the camera must fly AROUND the
  field. MB is the worst case and it is also the film's first frame: standoff
  4.859 m, so its station goes from 0.49 m horizontally off the monocoque to
  4.69 m.
* **Pans become real.** `move_seconds` charges for the bearing change between
  consecutive view directions. **Fifteen near-nadir view directions are all nearly
  parallel to one another, so the shipped tour costs almost nothing in pans.** A
  photographic tour points the lens in fifteen genuinely different directions and
  pays for every one.

Measured on the shipped visiting order, `tools/beat1_tourcost.py`: the tour cost
goes from **40.414 s to 54.121 s, a factor of 1.34**, from the direction change
alone with every standoff untouched.

**And the obvious escape route does not exist.** The brief permits beat 1 to grow
("total runtime may grow toward ~2 minutes and that is fine") and R2-323/R2-330
costed +7.4 s and +3.1 s for the standoff fix on exactly that basis. **It does not
help here.** The binding constraint is the part-flight deadlines (R2-062): a
station solved against a cluster's *exploded* position is aimed at empty air once
that cluster starts flying. Feasibility is

```
cum_cost(k) / total_cost  <=  deadline(k) / span
```

and **both sides are ratios — the absolute tour cost cancels.** Lengthening the
beat scales `span` up and makes every deadline *harder*, not easier. The deadlines
come from `world/beat1_anim_anim.json` and are absolute film times.

> **A runtime increase cannot buy relief from a constraint expressed as a fraction
> of the runtime.** This is also why nothing in this block wants to move the
> beat-1/beat-2 seam: there was never a version of the fix that had a use for it.

---

## R2-456 — twelve of fifteen re-aimed, and the three that could not be, with the reason for each

The first search consulted only the deadline solve and found 13 of 15 re-aimable.
**Built into an actual sheet that candidate fails three gates the shipped sheet
passes:**

```
the camera passes 0.085 m from the assembled car body, f517-561   (floor 0.30)
two moves peak at 4.41-4.95 m/s                                   (limit 4.00)
the close-out entry sweeps 15.9-17.8 % of frame width per frame   (limit 12)
```

**A station that is schedulable can still be a station the camera has to fly
through the car to reach.** Pulling a corner station down to 5–23 degrees puts it
at wheel height on the far side of the assembled car, and the straight run between
two such stations goes through the car — the same defect `BEAT1_CLOSEOUT` was
hand-authored to fix (R2-029), which is why the close-out is hand-authored and not
solved. The search was rerun (`tools/beat1_reaim_gated.py`) against the **whole**
of `build_beatsheet.py`, accepting a candidate only if its hard-failure set is a
subset of the shipped sheet's, and iterated to a fixed point because a single
greedy pass is order-dependent — FD fails on pass 1 and succeeds on pass 3, once
MB and SP have moved and the tour is a different shape.

```
cluster          was      now   camera z was   now      score kept
SP             84.15    23.64      5.991     4.513         69.0 %
MB             84.15    22.35      5.661     2.674         48.2 %
FD             84.15    21.06      4.177     1.848         55.1 %
BB             68.79    24.30      3.315     2.373         66.7 %
CI             62.95    23.64      4.632     3.907         88.3 %
EC             52.83    21.06      4.072     2.975         87.6 %
CORNER_RL      49.04    16.02      2.219     1.485         98.5 %
CORNER_RR      45.52    12.33      2.155     1.389         98.3 %
RW             41.41    22.35      2.175     1.745         39.3 %
CORNER_FR      31.04    22.35      1.838     1.635         93.0 %
SW             27.62    22.35      2.377     2.314         99.3 %
halo_assembly  23.64    23.64      4.662     4.662        100.0 %
--- not re-aimed ---
NOSE           84.15    84.15      2.819     2.819      no legal direction schedules
FW             74.48    74.48      2.442     2.442      only 6 legal directions exist
CORNER_FL      33.15    33.15      1.885     1.885      no legal direction clears the gates
```

**FW is the interesting failure and it is the room, not the schedule.** Its
exploded centre is at z 0.440 — the front wing hangs near the floor — and its
standoff is 2.078 m, so the 1.20 m rope-clearance floor forces
`sin(elev) >= 0.3657`, i.e. **elevation >= 21.45 degrees before any other
consideration.** Its entire legal band is 21.45–25 degrees, six sampled
directions, and none of the six schedules. A part hanging half a metre off the
floor cannot be shot from a shallow angle by a camera that must stay above a
0.915 m barrier.

**CORNER_FL not moving is a benefit, not a cost**: its station at f591 is the one
that reaches into the protected close-out (R2-326), and it is now provably
untouched.

**MB keeps only 48.2 % of its unconstrained score and RW 39.3 %.** That is the
honest price and it is a price in the scorer's units, not in the picture's — the
scorer's units are "projected area x material count", and the whole finding of
R2-451 is that maximising them produced a diagram.

---

## R2-456b — the fix across the WHOLE beat, and where the remaining 64 steep frames live

The brief for this block warned that flattening one key can move the problem
rather than fix it. Measured over all 792 frames, `tools/beat1_elevation.py`:

```
                                before        after
beat 1 first frame              -84.15        -22.35     lens z 5.6607 -> 2.6743
beat 1 f25  (t = 1.04 s)        -82.09        -24.55     lens z 4.5600 -> 1.7992
beat 1 first-60 median          -80.86        -24.31
beat 1 median                   -42.39        -22.47
beat 1 min                      -84.34        -83.97
frames steeper than 70 down    187 (23.6 %)  64 (8.1 %)
frames steeper than 80 down    120 (15.2 %)  18 (2.3 %)
film-wide near-nadir frames        192           69
```

**The camera is now under the light rig at every station.** The shipped f1 sat at
z 5.6607 with the highest lamp in the room at 5.590; it now sits at 2.6743.

**The 64 frames that are still steeper than 70 degrees are not scattered — every
one of them belongs to the two clusters the search could not move**, attributed
to the nearest presentation station:

```
FW      38 frames
NOSE    26 frames
------------------
        64          and nothing else in the beat is over 70 deg
```

The fifteen stations, after:

```
f   1  MB      -22.35     f 211  FW      -74.99  <-- unfixable
f  25  RW      -24.55     f 233  NOSE    -83.97  <-- unfixable
f  83  FD      -20.48     f 284  CI      -22.24
f 111  EC      -18.92     f 306  halo    -25.00  <-- the clamp, after the tilt
f 140  BB      -25.00     f 329  SP      -24.53
f 388  SW      -20.14     f 463  CORNER_RL -15.67
f 519  CORNER_RR -14.69   f 554  CORNER_FR -22.10
f 591  CORNER_FL -31.12  <-- deliberately untouched, protects f648-792
```

**BB and halo_assembly land on exactly -25.00**, which is `_legalise_station_dir`
doing the job it was added for: both were selected at 24.30 and 23.64 and the
weave tilt pushed them past the cap, and the backstop pulled them back without
touching their azimuth.

---

## R2-457 — the seam is bit-identical, and the protected region moves 8.2 px against the rejected candidate's 104

**Nulls first, both of them, before any verdict.**

```
build_beatsheet.py rebuilt from the SHIPPED sheet, clamp disabled
    beat 1's 22 camera keys, worst delta over world/look_at/t/lens/fstop/focus
                                                                     0
    beat-1 key-to-key path 54.96 m   (R2-323 publishes 54.958 m)
    beats 2-5, `aim`, `time_map`, `beat1_2_seam` all present after carry-forward

build_camera_rig.py rebuilt from that sheet vs render/film14_path.json
    worst |dp| over all 2,978 frames                                 0 m
    worst |dlens|                                                    0 mm

tools/campath_diff.py self-null, the before path against itself
    raw stored q      dq 0.203165 deg     <- the R2-103/R2-325 rounding floor
    re-normalised q   dq 0.000003 deg
```

**The before arm is the film's own path, bit for bit.**

`tools/seam_gate.py`, same invocation, both arms:

| | before | after |
|---|---|---|
| `chord_m` | 2.0893 | **2.0893** |
| `speed_ms` | 1.2727 | **1.2727** |
| `look_angle_deg` | 13.2504 | **13.2504** |
| `lens_delta_mm` | -0.051 | **-0.051** |
| built path vs declared keys | f754 0.0000 mm, f793 0.0000 mm | identical |
| peak speed | 8.9124 m/s @f804 | identical |
| worst BULGE | 1.407x f815-817 | identical |
| worst LOCAL accel | 3.59x @f796 | identical |
| worst rotation | 4.91 %width/frame @f806 | identical |
| verdict | SEAM_OK | **SEAM_OK** |

`tools/campath_diff.py`, before -> after:

```
beat 1        f1-792        worst dp 10.5588 m @f61    dq 179.884 deg @f216
  f1-590                    worst dp 10.5588 m @f61
  f591-647                  worst dp  0.0825 m @f603   dq   0.648 deg
  PROTECTED f648-792        worst dp  0.0099 m @f648   dq   0.066 deg   dlens 0
beats 2-6     f793-2978     worst dp  0.0000 m         dq   0.000 deg   dlens 0
```

**"Beats 2-6 are bit-identical" is what I wrote first and it is NOT TRUE, and the
way it is untrue is the exact trap this project keeps logging.** A byte comparison
of the stored records says **1,129 of the 2,186 frames differ.** Separated:

```
                    frames with ANY   worst      worst re-normalised   worst raw
                    position change    |dp|          rotation          |q| delta
beats 2-6                 0          0.000000 m     0.000198 deg        1.0e-06
PROTECTED f648-792       67          0.009850 m     0.066318 deg        4.0e-04
f591-647                 55          0.082470 m     0.648434 deg        4.1e-03
self-null (R2-325)        -          0          raw 0.203165 / renorm 0.000003
```

**Every one of those 1,129 differences is in the SIXTH DECIMAL of a quaternion**
— `0.687109` against `0.68711` — with position and lens identical to the byte.
The re-normalised rotation is **0.000198 deg**, which across a 4K frame is
**0.02 px**. The raw self-null floor on this very comparator is 0.203 deg, a
thousand times larger. So: **beats 2-6 do not move. They re-serialise.** Had this
been reported off the byte comparison it would have read as 1,129 frames of
damage to five finished beats.

In screen pixels at the range the film's own
focus is holding, against R2-326's costed-and-not-shipped candidate:

```
frame    this fix              R2-326's rejected candidate
f591     0.000 mm ->   0.0 px  (CORNER_FL not re-aimed)   1886.8 mm
f603    84.162 mm -> 333.0 px
f620     9.570 mm ->  15.8 px
f648    10.037 mm ->   8.2 px  <---------------------     118 mm -> 104 px
f655     0.000 mm ->   0.0 px                             0 mm -> 0 px
f665     5.802 mm ->   4.4 px                             68 mm -> 47 px
f700     1.250 mm ->   0.7 px                             15 mm -> 8 px
f720     0.000 mm ->   0.0 px                             0.3 mm -> 0 px
f754     0.000 mm ->   0.0 px                             0 mm -> 0 px
f792     0.000 mm ->   0.0 px
```

**f648 moves by 8.2 px against the rejected candidate's 104 — 12.7x less — and
f591, f655, f720, f754 and f792 move by exactly zero.** The elevation at f591,
f648, f700 and f754 is unchanged to 0.00 degrees.

**Reported and not buried: f603 moves by 333 px.** That is inside f591–647, the
CORNER_FL approach, which is **not** the protected f648–792 band but is adjacent
to it. It is not a key move — CORNER_FL's own key is pinned at 0.000 mm — it is
the spline bulging because the key *before* it changed, so the Bezier tangent at
f591 changed. R2-326's candidate moved f591 itself by 1.887 m; this one moves it
by nothing and bulges 84 mm mid-span. **It has not been looked at in pixels.**

---

## R2-457b — what the re-aim costs and what it closes, on the gates neither arm was built to satisfy

Both arms, `tools/continuity_gate.py --campath`, **PASS with 0 FAIL**:

```
                                   before            after
beat 1 worst rotation      16.41 %w/fr @f487   11.01 %w/fr @f229
beat 1 median rotation           2.79              2.50
beat 1 max speed                  3.9 m/s           4.2 m/s
beat-1 key-to-key path          54.96 m           60.18 m
mean camera speed               1.665 m/s         1.824 m/s   (design 1.994)
min clearance to the car        0.505 m           0.352 m     (floor 0.30)
max estimated pan              0.0939            0.0939
clusters seating unseen             0                 0
advisories                          5                 5
```

**R2-062 left one defect explicitly open and this closes it.** Its own words:
*"Still open, and deliberately not fixed here: f487 remains a 16.4 % WARN —
crossing behind the rear axle, the bisector of the two corner view directions is
within 5 deg of straight down, so roll must spin through the vertical
singularity... The real fix is a third bridge key at a wider lens."* The
`C1_rotation_smear: frames 478-495: 16% of frame width per frame` advisory is
**gone from the after arm**, and no third bridge key was authored. It was never a
bridge problem. **The bisector was within 5 degrees of straight down because both
corner view directions were pointing down**; take them out of the nadir and the
singularity is not there to spin through. The largest path kink also shrinks,
f462 at 0.0319 m/frame becoming f327 at 0.0161.

**The cost, stated plainly: the camera now passes 0.352 m from the car instead of
0.505 m**, against a 0.30 m floor. That is 70 % of the margin gone, and the next
agent to move a beat-1 station has much less room than I did.

---

## R2-458 — R2-429 folded in: ONE CHANGE DOES NOT FIX BOTH, and the measurement that settles it

R2-429 landed mid-block: beat 1 never goes wider than 76.1 % of frame width, the
lens is never further than 8.32 m from the car in 33 seconds, and the film has no
establishing shot. The question put to this block was whether one change fixes
both that and the 84-degree angle.

**It does not, and the two directions of the test both come back negative.**

* **Standoff does not force the angle** (R2-452): at the shipped standoff every
  one of the fifteen clusters can reach a sub-30-degree camera without leaving the
  room. Not one was pushed up there by its distance.
* **Angle does not create width.** `tools/beat1_shotscale.py`, before -> after:

```
beat 1 max camera distance        8.04 m  ->   8.04 m      (unchanged)
beat 1 median distance            4.32 m  ->   4.25 m
car at its smallest                0.791  ->    0.791      of frame width
frames under 100 % of frame width    141  ->      170
frames under  60 %                     0  ->        0      (unchanged)
p10..p90                     0.826-4.407  -> 0.826-3.652
```

**The re-aim moves the maximum camera distance by 0.00 m and the widest frame not
at all.** It takes 29 frames below 100 % and pulls the tight end in by 0.75
octaves, which is the right direction and is nowhere near an establishing shot.

The instrument reproduces R2-429's shape and names the same worst frame (f754),
and reproduces **zero frames under 60 % exactly**; it reads 8.04 m / 79.1 %
against the published 8.32 m / 76.1 %, a 3.5 % gap that is the car-reference
convention (this uses `beat_sheet.beat1.car_box`'s centre and its 5.72 m X span;
R2-429 used 5.7 m and a reference 0.28 m away). **The gap is stated rather than
tuned away.**

> **They are the two coordinates of one polar placement and they have two
> different fixes.** `standoff = radius * 1.55 + 0.42` fixes the subtended angle,
> so the subject always fills the frame and is therefore never seen whole — that
> is R2-429, and it is a RADIUS. `argmax projected_area` returns a plan view —
> that is R2-425, and it is a DIRECTION. A radius cannot choose a direction.
> Fixing the angle gives a well-composed frame of something the audience still
> cannot identify; **R2-429's fix is still owed and this block does not deliver
> it.**

**This block adds no width anywhere**, so it does not pre-empt the open question
of whether f648–792 already functions as a delayed establishing shot. That
question is safe to answer after this lands: the protected region moves 8.2 px at
its first frame and zero from f655 on.

---

## R2-459 — what I could NOT confirm

* **The 3 % score tolerance and the 25-degree cap have not been swept against
  rendered frames.** Both are defended by measurement — the plateau is real, the
  cap is the film's own — but nobody has looked at a 20-degree station beside a
  30-degree one and preferred it.
* **f603's 333 px has not been looked at.** It is outside the protected band and
  the key either side of it is pinned, but 333 px at 4K is a shift a review would
  see and the argument that it does not matter is geometric, not photographic.
* **NOSE and FW are still shot from 84.15 and 74.48 degrees**, and 64 frames of
  beat 1 (8.1 %) remain steeper than 70. The opening is fixed; the beat is not.
* **The A/B renders come from `render/r2451_b1ab.blend`, not from the film.** It
  is `world/beat1_anim.blend` — same showroom, same 616 exploded parts, same 23
  practicals, same part animation, lifted by `showroom_lighting` and graded at
  `FILM_EXPOSURE` — but through the glass wall it shows `R2_ProceduralSky` and not
  `world/build_sky.py`'s sky. **A frame from it is not a frame of the film** and
  the comparison is only valid arm-to-arm.
* **The re-solved visiting order has not been reviewed as a sequence.** It is
  re-derived by the shipped Held-Karp against the moved stations, which is what
  R2-062's machinery does by construction and is the opposite of pinning an order
  that was optimal for stations that no longer exist — but the order changed and
  nobody has watched it.
* **`fill` is untouched by design.** All fifteen still fail R2-317's framing gate.
