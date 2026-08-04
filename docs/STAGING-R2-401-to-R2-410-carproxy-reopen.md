# STAGING — the car-proxy reopen (numbers to be assigned by the log's owner)

The coordinator has reopened this. The framing I was given — that the cause was
the kinematic car's inability to lose momentum to 2,240.9 kg of glass — is
refuted by my own measurement (0.203 % of the car's momentum), and they have
said plainly that the framing was theirs. What is left standing is the thing
the data actually points at:

> `MUL05_S02` travels **55.35 m**. **25.6 m of that was riding the car's deck**
> and the rest is the slide that ride paid for. Two independent questions:
> **why is it on the car at all**, and **why does it slide so far once it
> leaves**. And the acceptance criterion is not a distance — it is whether it
> reads wrong on screen.

---

## R2-4xx — six predictions, committed before the reopened search

Written before any of the three measurements below is run. Everything used is
data already on disk: `sim/out/breach_film_R2387.npz`, `sim/tmp/r2386/A0.npz`,
and the ONER camera track.

### On the RIDE — is it a solver failure or a modelled outcome?

Three candidate mechanisms were named: a collision-shape gap, a substep/CCD
failure at speed, or the fracture releasing pieces inside the car's swept
volume. **I predict none of them.**

* **P20 — no tunnelling.** `MUL05_S02` is **never inside a car-proxy part** at
  any frame, on the 128-direction over-approximating hull test that already
  over-counts. If it had tunnelled through the bodywork it would have to appear
  inside it for at least one sampled frame.
* **P21 — not released inside the swept volume.** At its first movement the
  segment's car-local x is **greater than +2.0 m**, i.e. ahead of the nose
  (`NOSE_DX` = 3.020), and its world z is **above `CAR_TOP_Z` = 0.992**. It is
  not born inside the car.
* **P22 — it falls onto the car, and that is what the scene says should
  happen.** `MUL05_S02` spans z 1.55–2.33 m, centre 1.94. The car strikes the
  mullion at 0–1 m, this segment is pushed forward at **about 10 m/s against
  the car's 16.4**, so the car overtakes it while it is still falling, and it
  lands on a deck whose top is at 0.992 m. I predict the trace shows world z
  decreasing monotonically through the crossing with **no discontinuity**, and
  car-local x decreasing smoothly from +2.7 through zero. If so, the ride is
  not a bug to fix; it is a consequence to accept or to design out of the
  *proxy's geometry*, and saying otherwise would be inventing a defect.

### On the SLIDE — 64 m of architectural aluminium

* **P23 — the slide is honest sliding friction at a defensible coefficient, and
  the artefact is that the piece never tumbles.** Bullet combines friction
  multiplicatively, so aluminium 0.45 × concrete 0.62 = **0.279**, which is a
  real µ for aluminium on concrete. I predict the measured deceleration during
  the free slide is within 25 % of µg = 2.74 m/s², **and** that the segment's
  angular speed during that slide is **under 2 rad/s** — i.e. it lies flat on
  one face of a box and skates. A real 160 × 75 mm extrusion tumbles end over
  end and digs in. **If the angular speed is low, the fix is a shape and a
  rotational drag, not a friction number**, and lowering µ would be fitting.

### On the CRITERION — pixels, not metres

* **P24 — the 55 m is not what is on screen; the ride is.** I predict
  `MUL05_S02` at rest projects to **under 40 px of length in the closing
  frames**, and that its largest on-screen presence by an order of magnitude is
  during the ride in beat 3, at 6–13 m from the lens. **The frames that decide
  this are f0890–f1050, not f2940/f2978.**
* **P25 — the one I expect to be wrong.** P24 assumes the resting place is far
  and small. If any of the three lower mullion segments comes to rest inside
  the *beat 4* camera's view of the apron — the take is continuous and the car
  drives past its own debris — then the metre count matters after all and P24
  is the wrong question. I have not looked, and I would rather be caught by
  this than not have written it down.


---

## R2-4xx — the ride is not a solver failure, and the 55.35 m decomposes exactly

Three controls on `MUL05_S02`, run before anything was changed.

### P20, P21, P22 — all three confirmed. Nothing is broken.

| control | result |
|---|---|
| frames INSIDE any car-proxy part (128-direction hull test, which OVER-counts) | **0 of 400** |
| car-local x at first movement | **+2.912 m** — ahead of the nose (`NOSE_DX` 3.020), not born inside |
| world z at first movement | **1.949 m** — twice `CAR_TOP_Z` (0.992) |
| largest single-frame Δz over the whole descent | **0.0237 m**; frames with Δz > 0.25 m: **0** |
| largest single-frame step, any axis | **0.0767 m** — 9.6 mm per substep at 1,920 Hz, against a 75 mm section |

**No tunnelling, no CCD failure, no piece released inside the car.** The segment
descends smoothly from z 1.949 to the deck over 117 sim frames while the car
drives under it. It crosses the nose plane at z 1.954 — a metre clear of the
roof — and reaches deck height 119 frames later at car-local x −0.378.

**So the mechanism is exactly what the scene says should happen.**
`MUL05_S02` spans z 1.55–2.33 m. The car strikes the mullion at 0–1 m, this
segment is pushed forward at about 10 m/s against the car's 16.4, the car
overtakes it while it is still falling, and it lands on a deck whose top is at
0.992 m. **There is no bug here to fix.** Had I gone looking for a collision
gap or a substep failure I would have found nothing, and three predictions said
so before the test.

### The 55.35 m, decomposed on the production bake

| phase | `MUL05_S02` | `MUL05_S00` | `TRN_z0_b05` |
|---|---|---|---|
| **aboard the car** | sim f142–476, film **f859.6–f1038.7**, **1.396 s world** | f861.6–f973.7, 0.896 s | f859.5–f993.2, 1.108 s |
| distance carried | **22.93 m** | 12.46 m | 15.25 m |
| **speed at separation** | **23.08 m/s** | 19.49 m/s | 21.73 m/s |
| free slide | 21.63 m from 15.62 m/s | 25.61 m from 18.31 m/s | 24.08 m from 17.34 m/s |
| measured deceleration | **4.47 m/s² (µ_eff 0.456)** | 4.98 (0.508) | 5.34 (0.544) |
| **angular speed while sliding** | median **0.99 rad/s**, p90 2.85 | 1.10, 4.85 | 0.75, 2.46 |
| total | **55.35 m** | 54.00 m | 55.14 m |

**P23 scores half.** I predicted the deceleration would be within 25 % of
µg = 2.74 m/s² and it is **4.47–5.34** — 63 to 95 % higher, because the air I
added is doing about half the work. That clause is **WRONG**, and wrong in the
direction that flatters the fix, which is the direction to be most suspicious
of. The other clause is **RIGHT**: the median angular speed while sliding is
**0.75–1.10 rad/s**, about a sixth of a revolution per second. **These pieces
do not tumble. They lie on one face of a box and skate**, which a bent 160 × 75
extrusion on tarmac does not do.

### And the criterion: P24 confirmed, and it changes what has to be fixed

Projecting each far traveller through the ONER track for all 2,134 frames of
the take:

| body | biggest on screen | at | range | **at rest, f2978** |
|---|---|---|---|---|
| `TRN_z0_b05` | **1,879 px long** | f971 | 2.9 m | **30.6 px** |
| `TRN_z0_b04` | **1,507 px** | f970 | 3.6 m | 30.4 px |
| `MUL05_S00` | 864 px | f977 | 2.4 m | 11.3 px |
| `MUL05_S01` | 704 px | f976 | 2.9 m | 11.3 px |
| `MUL05_S02` | 614 px | f972 | 3.3 m | **11.3 px** |

**The 55 m is 11 pixels. The ride is nineteen hundred.** At rest these members
are 8–31 px in the closing frames — at the limit of what R2-278 says can be
measured at all. Their entire on-screen life is **f0967–f0978**, where five
structural members ride the car past a lens 2.4 to 3.6 m away, in slow motion,
filling up to half the frame width.

**So the metre count was the wrong target and the coordinator is right that the
criterion is pixels — but the answer that follows is not "55 m is acceptable".
It is that the ride, not the distance, is the thing on screen, and the ride is
enormous.** I am not claiming these pieces are out of shot. They are the shot.


---

## R2-4xx — the ride ends in the REAR WING, and my own transport census could not see it

### The mechanism, frame by frame

`MUL05_S02` in the car's own frame, through the production bake. The proxy's
solid vertical faces are at car-local x = +1.500 (`tub` front), +1.150 (`halo`
front), +0.100 (`airbox` front), −0.700 (cover/airbox rear) and **−2.200
(`wing_r` front)**:

| sim f | film | car-local x | car-local z | d(x)/dt rel. | world v |
|---|---|---|---|---|---|
| 150 | f860.4 | +2.719 | 1.907 | −8.22 | 8.75 |
| 206 | f866.4 | +0.793 | 1.985 | −10.33 | 6.99 |
| 248 | f890.4 | −0.526 | 1.112 | −7.41 | 10.28 |
| 290 | f917.7 | **−1.716** | 0.956 | −4.76 | 14.76 |
| 304 | f926.8 | −1.843 | 0.952 | **+1.56** | 21.85 |
| 318 | f936.0 | −1.679 | 1.073 | **+3.68** | 25.41 |
| 360 | f963.3 | −2.005 | 1.519 | +1.08 | 23.68 |
| 430 | f1008.8 | −2.522 | 1.502 | +1.24 | 27.13 |
| 472 | f1036.1 | −2.900 | 1.687 | −4.36 | 23.31 |

From **film f917 to f1044 — 127 film frames — the segment sits within half a
metre of car-local x = −2.200**, and its velocity relative to the car
**oscillates between −6 and +3.7 m/s**. It is not sliding. It is being caught,
released and caught again by a wall, while the car's authored animation takes
its world speed from 14.8 to 27.1 m/s.

**That wall is the rear wing.** `wing_r` is
`box(TAIL_DX, −2.200, −0.535, 0.535, 0.700, 0.980)` — a solid slab **0.478 m of
chord, 1.07 m of span and 0.280 m thick** — flanked by `rep_l` / `rep_r`, two
endplates rising from z 0.320 to 0.980. Together they are a **tray**: a
full-width leading face to stop anything sliding aft, two side walls to stop it
leaving sideways, and a floor. Anything that reaches it is kept.

**A real rear wing is an aerofoil.** Its mainplane is a 30–50 mm element, not a
280 mm block, and the space between it, the beam wing and the crash structure
is open air. A member sliding off the engine cover falls **through** that gap
onto the track. In the proxy the gap is filled and it lands in a box.

**This is the same class of finding as the floor's 8 mm ground clearance
against 11.5 mm glass (R2-384): a convex decomposition turning an open,
skeletal structure into a solid one, and the debris behaving accordingly.** It
is also why friction was never going to fix the ride — of the 9.3 m/s² the
segment gains, only 2.43 m/s² is available from friction (µ_combined 0.2475 × g).
**The rest is normal contact against a face, and a normal force does not care
what µ is.**

### P26 — committed while the three cells bake

**The ride survives at every friction.** `MUL05_S02` will be held on the deck
in all three 700-frame cells — µ 0.20, 0.35 and 0.55 — and B1's "0 frames held"
at 400 frames will not survive the longer window. If the ride is a rear-wing
trap, µ is not the lever and no value of it is.

### And a correction to my own instrument, which is why I nearly missed this

`carproxy_census.py` measures "transport" as distance covered inside the
proxy's own point-cloud envelope inflated by 120 mm. That envelope's **upper
bound is car-local z = 1.112 m**. `MUL05_S02` rides at **car-local z 0.95 to
1.69**. **For most of the ride it is above the box I was measuring transport
inside**, so every `transport_m` figure I have published under-counts the
high-riding members — including the headline **40,587 m → 8,445 m**.

It is the same error in both tables, so the −79 % ratio is probably close to
right, but "probably" is not a measurement and the corrected figures are being
computed now. **B1's `MUL05_S02 transported 0.0 m, 0 frames held` — which I
came within an inch of treating as evidence that friction 0.20 kills the ride —
means only that the segment was not inside a box that stops 118 mm above the
car's roof.** It says nothing about whether it was riding.

The measurement that *did* see it — "on the deck" as car-local z > 0.55 within
the car's plan — is the one in the phase decomposition above, and it reports
**335 frames aboard**, not zero.


---

# HANDOFF — the car proxy, closed here

Stood down mid-search: the host was thrashing at 29 GB of 43 GB swap with six
Blender processes, and three of them were mine. **I killed all three 700-frame
cells** (`sim/tmp/r2402c/C0,C1,C2`, µ 0.20 / 0.35 / 0.55 with air) and released
about 2 GB of swap. They were confirmatory, not decisive — see P26 below, which
is left **UNRESOLVED** rather than quietly dropped.

## 1. Where it stands

| | shipped R6 | R2281 re-bake | **R2387 (live candidate)** |
|---|---|---|---|
| `MUL05_S02` travel | 0.14 m | **89.79 m** | **55.35 m** |
| bodies over 1 m/s at the last key | 70 | 2,646 | **27** |
| `GS_b05_00434` (2.5 g, underfloor) | — | 205.01 m | **1.12 m** |
| connected aperture | 2.15 × 6.00 | 2.15 × 6.00 | **2.15 × 6.00**, bay 5 100 % |
| car's seams | — | identical | **bit-identical** |

**What got it from 89.79 to 55.35 m: one change, `--air-drag derived`.** The
sim had no air in it. Every active body now carries a `linear_damping` computed
from its own collision mesh (Cauchy S/4), Cd 1.17, ρ 1.225, linearised about
the car's own 16.584 m/s at the glass plane. Nothing chosen, no contact model
touched, no cost to the car's trajectory.

**What remains, decomposed exactly:**

| phase | distance | how it ends |
|---|---|---|
| **aboard the car** | **22.93 m** over 1.396 s of world time (film f859.6–f1038.7) | leaves at **23.08 m/s** |
| ballistic / bouncing | ~11 m | lands |
| free slide | **21.63 m** at 4.47 m/s² (µ_eff 0.456), **median 0.99 rad/s** — it skates, it does not tumble | stops |

**The ride is the whole defect.** It carries 22.93 m directly and hands the
piece over at 23.08 m/s instead of the ~10–12 m/s it had before boarding, which
buys most of the remaining 32 m.

## 2. The screen-space verdict — settle this and do not re-litigate the metres

Every far traveller, projected through the ONER track over all 2,134 frames of
the take:

| body | biggest on screen | frame | range | **at rest, f2978** |
|---|---|---|---|---|
| `TRN_z0_b05` | **1,879 px long** | f971 | 2.9 m | **30.6 px** |
| `TRN_z0_b04` | 1,507 px | f970 | 3.6 m | 30.4 px |
| `MUL05_S00` | 864 px | f977 | 2.4 m | 11.3 px |
| `MUL05_S01` | 704 px | f976 | 2.9 m | 11.3 px |
| `MUL05_S02` | 614 px | f972 | 3.3 m | **11.3 px** |

**The 55 m subtends 11 pixels. The ride subtends 1,879.** Three orders of
magnitude. A slide of 8–31 px at 542 m range is at or below the scale R2-278
established `grid_contrast` cannot even measure. **The transport distance is
the invisible half of this defect and always was.** Anyone reopening this on
the metre count should read this table first.

The whole on-screen life of these members is **f0967–f0978**, where five
structural members ride a car past a lens 2.4–3.6 m away, in slow motion,
filling up to half the frame width.

## 3. The rear-wing tray — the mechanism, and what a fix has to change

`MUL05_S02` in the car's own frame: from **film f917 to f1044 — 127 film
frames — it sits within half a metre of car-local x = −2.200**, its velocity
relative to the car oscillating between **−6 and +3.7 m/s** while its world
speed climbs from 14.8 to 27.1 m/s. It is not sliding. It is being caught,
released and caught again by a wall.

That wall is `wing_r`:
`box(TAIL_DX, −2.200, −0.535, 0.535, 0.700, 0.980)` — **0.478 m of chord,
1.070 m of span, 0.280 m thick: a thickness-to-chord ratio of 58.6 %.** No
aerofoil is 59 % thick; a rear wing mainplane runs 10–15 %. **The
inconsistency is internal and needs no outside data** — `rep_l` / `rep_r`
beside it are modelled correctly as 35 mm fins 660 mm tall. The proxy has two
right endplates enclosing a block where the car has open air. Together they are
a **tray**: a full-width leading face, two side walls, a floor.

**Why friction was never the lever.** Of the 9.3 m/s² the segment gains,
friction can supply at most µ_combined × g = 0.2475 × 9.81 = **2.43 m/s²**. The
rest is normal contact against a face, and a normal force does not care what µ
is. That is why cutting µ to 0.20 (R2-389) bought nothing here and cost five
mullion segments left standing in the wound box.

**What a fix would change, already implemented and NOT yet baked:**
`--rear-wing aerofoil` (committed, `sim/breachlib.py`) thins the mainplane to
12 % of its own chord at the top of the band it already occupies. Span, chord,
overall height and both endplates are unchanged; **no part is added and no
dimension comes from outside the file.** It opens **0.478 × 0.660 m of air
between the endplates** — the route a member sliding off the engine cover takes
in the real car. `verify_proxy("aerofoil")` passes every existing check
including `top == CAR_TOP_Z`. **It has never been run.** One 700-frame cell
against `--rear-wing solid` would settle it.

## 4. The predictions, scored

Committed before the search, in this file, at `62fdfee`.

| | prediction | outcome |
|---|---|---|
| **P20** | no tunnelling — never inside a proxy part | **RIGHT** — 0 of 400 frames, on a test that over-counts |
| **P21** | not released inside the swept volume: car-local x > +2.0, z above `CAR_TOP_Z` | **RIGHT** — +2.912 m and z 1.949 against a roof at 0.992 |
| **P22** | it falls onto a car that drives under it; smooth, no discontinuity | **RIGHT** — largest single-frame Δz **0.0237 m**, zero frames over 0.25 m, largest step 0.0767 m = 9.6 mm per substep against a 75 mm section. **No collision-shape gap, no CCD failure, no fracture releasing pieces inside the car.** All three candidate mechanisms I was handed are excluded |
| **P23a** | slide deceleration within 25 % of µg = 2.74 m/s² | **WRONG** — 4.47–5.34 m/s², 63–95 % higher. The air I added does about half the work, and I failed to credit my own change. Wrong in the direction that flatters the fix, which is the direction to distrust |
| **P23b** | angular speed under 2 rad/s — it skates rather than tumbles | **RIGHT** — median 0.75–1.10 rad/s, about a sixth of a revolution per second |
| **P24** | the 55 m is not what is on screen; the ride is; the deciding frames are f0890–f1050 not f2940/f2978 | **RIGHT, and it is the finding** — 11 px against 1,879 px, peak at f0967–f0978 |
| **P25** | the one I expected to be wrong: that a member rests where beat 4 sees it, making the metres matter after all | **RIGHT to have written it, and it did not fire** — the members rest at x 68.9–70.2, 542 m from the closing camera, 8–31 px |
| **P26** | the ride survives at every friction; B1's "0 frames held" was an artefact of the 400-frame window | **UNRESOLVED** — the three cells that would have settled it were killed to free the host. The mechanism above predicts it strongly but it is not measured |

**Two right for the wrong reason is worth naming.** P20–P22 were right, and
being right meant there was **nothing to fix** where I was told to look. The
value of that block of work is entirely negative: it closed off three
mechanisms so the fourth could be found.

## 5. Unmeasured, and what would reopen this

* **Is the ride in frame during beat 3? YES, and it is measured, not assumed.**
  The projection above puts five members at 614–1,879 px at 2.4–3.6 m across
  f0967–f0978. I have also rendered and looked at **f0950 and f1000 from both
  builds** (`render/r2387/COMPARE_ride_f0950_*.png`,
  `COMPARE_ride_f1000_*.png`): a mullion lies across the car in both, and at
  f1000 the re-bake is **towing a pane attached to its tail** while R2387 has
  separated from it. **This does not reopen the question — it is the question.**
  The peak frames f0967/f0972/f0977 were in flight on the farm when I stood
  down; if they landed they are in `render/r2387/`.
* **P26 is unresolved** — friction bracket over 700 frames, killed.
* **`--rear-wing aerofoil` has never been baked.** It is the only candidate
  fix left standing and it is untested.
* **My transport census under-counts, in every figure I published.**
  `carproxy_census.py`'s envelope tops out at car-local z = **1.112 m** and the
  ride happens at z 0.95–**1.69**. The corrected totals were still computing
  when I stopped. **The −79 % transport ratio (40,587 → 8,445 m) is the same
  error in both tables and is probably close to right, but "probably" is not a
  measurement.**

### The instrument lesson, stated properly

The census did **not** report a wrong value. It reported a **correct value
about the wrong volume** — and nothing in its output distinguishes "the debris
was not being carried" from "I did not look where it was being carried."
`MUL05_S02` showed `transported 0.0 m, 0 frames held` in cell B1, and I came
within an inch of treating that as evidence that friction 0.20 kills the ride.
It meant only that the segment was not inside a box that stops 118 mm above the
car's roof.

**A bounded search reports confidently about its bound.** Every other finding
in this pass has the same shape: `grid_contrast` measuring rows that cannot
contain a member (R2-400), the R2-296 controls whose rectangle the blast radius
had outgrown, `cheaper_to_finish` pricing sequence jobs at the stills rate. In
each case the number was right and the volume it described was not the one
anybody was asking about.

