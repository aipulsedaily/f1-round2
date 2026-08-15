# STAGING R2-821 to R2-850 — beat 1 pacing and shot scale

Owner: beat-1 pacing (camera position, rotation, lens, timing).
Focus distance and f-stop are NOT touched here — another agent owns them.

Baseline watched: `~/vast-render/out/seq/r2beat1/` (792 frames, 720p),
encoded to `watch/BEFORE_beat1_33s.mp4`.
Camera measured: `world/camera_rig_path.json`
(byte-identical to `render/film16_path.json`, the current ship).

---

## R2-821 — the client's three notes are TWO defects, and framing is not the cause of the pacing one

The coordinator asked whether "way too slow" and "way too zoomed in" are one fact
seen twice. **They are not.** They have different causes, in different files, and
fixing either one alone leaves the other note standing.

**They are distinct, and here is the proof.** The frames in which the whole car
fits the frame are, on the shipping path, exactly three runs:

```
f1-36      36 frames   1.50 s   t  0.0- 1.5 s    the establishing opening
f177-184    8 frames   0.33 s   t  7.3- 7.6 s
f657-792  136 frames   5.67 s   t 27.3-33.0 s    the close-out
```

Between f37 and f656 the car is **exploded across 616 parts**. There is no whole
car to fit, at any focal length, from any distance. Widening every station to
infinity would still show an unfinished car until the corners land. The seat
schedule is computed in `tools/build_beatsheet.py:1064-1073` and baked into
`world/beat1_anim.blend`; it knows nothing about the camera.

Conversely, moving the seat schedule earlier without widening would complete the
car at t≈19 s in front of a camera 1.50 m from a wheel assembly at 2.32× frame
overflow — the audience would not be able to see that it had finished.

**So: framing is the root of "too zoomed in". It is not the root of "too slow".
It is, however, what PAYS FOR the fix to "too slow" — see R2-828.**

---

## R2-822 — the car does not read whole at t = 26.3 s. It reads at t = 29.0 s, and the payoff is 4.0 s, not 5.71 s

R2-430 puts the first whole-car frame at **f631 / t = 26.3 s**. R2-464 puts it at
**f657 / t = 27.4 s**. The two have never been reconciled. **Both are early.**

Contact sheets of f619-f705 and f682-f703 off the delivered 720p ladder:

```
f619   fragment; front wing unpainted, body cut off              does not read
f631   body reads as a car — BUT ALL FOUR WHEELS ARE ABSENT      R2-430's claim
f643   wheels arriving, car cropped at frame right
f657   wheels present but visibly detached and floating          R2-464's claim
f669   near-whole; front-left wheel still separate
f682   wheels clearly apart, suspension links extended
f691   wheels closing, still gapped and smeared
f697   COMPLETE CAR — all four wheels attached, full context
f700   whole, settled
```

R2-430 and R2-464 are both measuring **the moment the car's BODY reads**, with
the corners still in flight. The complete car — which is what the shot is of —
arrives at **f696-697, t ≈ 29.0 s**.

**Corroborated three independent ways:**

1. **Pixels** (above): wheels attach between f691 and f697.
2. **The beat sheet's own arithmetic.** `seat_t[corner] = seat_start + 11·per`
   = `33.0·0.42 + 11·(33.0·0.50/12)` = **28.985 s = f696**, exactly.
3. **Frame-to-frame image change** (below, R2-823): the 1-second rolling mean
   drops below 8.0 for the first time at **f683** and never returns.

**Consequence: the sustained readable stretch is f697-792 = 96 frames = 4.0 s of
a 33.0 s beat — 12 %.** Not 5.71 s. The problem is ~1.7 s worse than briefed,
and the wait is 29.0 s, not 26.3 s.

---

## R2-823 — beat 1's energy curve is INVERTED: 4.14× more on-screen change where nothing reads than where the subject does

This is the mechanism behind "way too slow I feel", and it is not "the camera
moves slowly". Mean absolute frame-to-frame luminance change, all 792 delivered
frames at 160×90:

```
segment                      t              n     mean    median
establishing wide          0.0- 2.5 s      60    13.16     13.34
unreadable tour            2.5-26.3 s     571    20.27     19.83
car resolves              26.3-29.0 s      65    14.59     10.79
readable payoff           29.0-33.0 s      95     4.89      4.60
```

**Ratio, tour to payoff: 4.14×.** Cumulative on-screen change over the 4.0 s
payoff is **465**; over an equivalent 4.0 s window at t=6-10 s it is **1950**.

> **The beat spends its energy where there is nothing to see, and goes still the
> moment there is something to see.**

The viewer gets 26 s of rapid motion through unparseable close-ups, then a
near-static hold on the one image they were waiting for. Both halves read as
slow, for opposite reasons. This is why "too slow" is not answered by moving the
camera faster — the tour is already the fastest part of the beat.

Corroborates R2-321 from the opposite direction: R2-321 measured 1.5 px median
smear in the protected region against 54.7 px over the tour (a factor of 36) and
called it "the region where the camera stops moving". It is the same fact —
R2-321 read it as a virtue of the close-out, and it is also a pacing defect.

---

## R2-824 — the root cause of "too slow" is two constants, and SHORTENING beat 1 makes the payoff SHORTER

`tools/build_beatsheet.py:1064-1065`:

```python
seat_start = dur * 0.42
seat_span  = dur * 0.50
```

`0.42 + 0.50 = 0.92`. **Assembly completes at 92 % of beat 1 by construction, for
any value of `dur`.** The payoff is the remaining 8 % — 2.6 s of nominal budget,
4.0 s as delivered.

**This settles the duration question, and the answer is: do not change the
duration.**

| beat 1 `dur` | assembly completes | payoff |
|---:|---:|---:|
| 24.0 s | 22.08 s | **1.92 s** |
| 33.0 s (ship) | 28.99 s | **4.01 s** |
| 40.0 s | 36.80 s | 3.20 s |

Shortening beat 1 to 24 s — the intuitive response to "too slow" — **more than
halves the payoff**, because everything is expressed as a fraction of `dur`. It
would also cost an audio-master rebuild for a strictly worse result.

Independently predicted by **R2-455**: the feasibility constraint is
`cum_cost(k)/total_cost <= deadline(k)/span`, both sides ratios, so absolute tour
cost cancels — *"a runtime increase cannot buy relief from a constraint expressed
as a fraction of the runtime."* The converse holds too: a runtime **decrease**
buys no relief either.

**Recommendation: beat 1 stays 33.0 s / 792 frames. The film stays 124.0833 s.
The audio master does not need rebuilding.** The fix is entirely inside the two
fractions above and the standoff law, and it is duration-neutral.

---

## R2-825 — the four corners cost 9.2 s (28 % of the beat) to present four near-identical assemblies that all seat at the same instant

From the live gate run (`python3 tools/build_beatsheet.py --check docs/beat_sheet.json`):

```
RW          presented t 15.42 s
CORNER_RL   presented t 19.29 s   1.53 m   58 mm   2.15 x frame height
CORNER_RR   presented t 21.62 s   1.53 m   58 mm   2.12 x
CORNER_FR   presented t 23.08 s   1.50 m   58 mm   2.01 x
CORNER_FL   presented t 24.62 s   1.50 m   58 mm   2.32 x
all four seat simultaneously at t 28.985 s
```

From RW's presentation to CORNER_FL's is **9.20 s — 28 % of beat 1** — spent
presenting four assemblies that `docs/explode_plan.json` itself declares a
`simultaneous_group`, so they impose no order on each other. `CORNER_RL` and
`CORNER_RR` are both 745,562 tris; `CORNER_FR` and `CORNER_FL` are both 690,930.
**The audience is shown the same object four times, each overflowing the frame
by 2.0-2.3×, none of them readable.** This also sits against the project's
no-repeated-assets red line.

This is the single largest recoverable block of time in the beat.

---

## R2-826 — instrument notes, both load-bearing

**(a) `tools/lap_shotscale.py` does not measure beat 1.** Run on the shipping
path it prints:

```
1_assembly    792    --    --    --   (car exploded; not measured)
```

`--selftest` passes all four controls (`SELFTEST_OK`), so the tool is sound — it
simply declares no authority over beat 1, by design, because it projects the
car's *assembled* box. **Any beat-1 shot-scale figure attributed to
`lap_shotscale.py` did not come from it.** For beat 1 the instrument is
`tools/beat1_true_extent.py`.

**(b) `tools/beat1_true_extent.py` is unreliable on 24 % of beat 1**, and this
has not been recorded before. Its `extent()` drops bounding-box corners that fall
behind the camera and computes the hull from whatever remains. On beat 1:

```
frames with a bbox corner behind the camera   190 of 792  (24.0 %)
```

Those readings are spurious in **both** directions — f357 reads 29.9 % (an
apparently wide frame that is actually the camera sitting inside the car's
footprint) and f385 reads 65795 %. Neither is meaningful. Statistics quoted over
all 792 frames inherit this.

**On the 602 frames where the projection is fully in front of the camera:**

```
median car width   213.2 % of frame width
p90                603.6 %
frames that FIT    193
```

`f1 = 35.0 %` — confirming the establishing opening is correct and is the beat's
widest shot. The coordinator's cited 191.7 % / 559.4 % are in the same family and
slightly conservative; the direction of the client's note is confirmed, not
challenged.

> **That 24 % is itself the finding.** For a quarter of beat 1 the camera is close
> enough that part of the assembled car's bounding box falls *behind the camera
> plane*. That is a more vivid statement of "too zoomed in" than any percentile.

---

## R2-827 — ID correction: the cluster-overflow defect is R2-317, not R2-116

R2-116 (`DEFECT-LOG-R2.md:4456`) is `spectator_seated` / `ITEM_UNMEASURABLE` — a
crowd-item gate defect, unrelated to beat 1. The overflow defect is **R2-317**
(`DEFECT-LOG-R2.md:8373`), *"every one of the fifteen presentations overflows its
own frame, 1.06× to 2.59×"*, still open per `STAGING-R2-451-to-R2-470.md:999`.
The range **1.07×-2.40× does not appear in the log** and should not be carried
forward.

Live re-measurement today (the gate's own FRAMING block) gives per-cluster
overflow of **1.11× to 2.32×** on the current camera, 15 of 15 failing.

---

## R2-828 — the proposed fix, and why the framing change is what pays for the timing change

Three changes, coupled. None of them touches duration.

**1. Make the standoff law lens-aware** (`tools/build_beatsheet.py:612`):

```python
standoff = max(radius * 1.55 + 0.42, 0.75)     # fixes SOLID ANGLE, lens-blind
```

The gate already prints the required distance for every cluster ("it would fit
at X m"). Worst cases: `RW` 1.53 → 4.10 m, `CORNER_FL` 1.50 → 4.10 m,
`FD` 3.25 → 6.37 m, `MB` 4.86 → 7.52 m.

**2. Present the four corners as ONE group** from a single pulled-back vantage
(R2-825). They seat simultaneously and impose no order on each other.

**3. Move the seat schedule earlier** (`:1064-1065`), e.g.
`seat_start = dur*0.30`, `seat_span = dur*0.36` → corners seat at **t ≈ 20.8 s
(f499)**, giving a **12.2 s** legible payoff instead of 4.0 s.

**Why (1) and (2) pay for (3).** Pulling stations back reduces `move_seconds()`
in both its terms — the pan term `_pan_s()` is directly proportional to the
bearing swept, and from farther out the bearing between adjacent clusters
shrinks. Consolidating the corners recovers ~6.7 s of the 9.2 s in R2-825.
Together they cut the tour's time cost enough to let the whole tour finish by
t ≈ 18.7 s, which is what the earlier seat schedule requires (deadline =
seat − 2.05 s, `:1245-1247`).

**And it pays into the other two open notes at the same time**, exactly as R2-321
predicted (*"the framing fix is the only one of the three that pays into all
three"*): pulling back cuts parallax smear, and it collapses the f-stop the
corners need from **f/37-f/100 to something reachable** — which is the other
agent's defect, not mine, but it means our two candidates must be judged
together and not separately.

### What this changes that is currently pinned

| pin | where | status |
|---|---|---|
| `CORNER_FL` must land on frame 591 | `:1021` assert | **must be relaxed** — derived from the dead 1.76 s uniform slot |
| f591-792 "PROTECTED" | `tools/campath_diff.py` windows | encodes the CURRENT structure; it is the material being moved |
| `BEAT1_CLOSEOUT` t=25.90/27.30/28.60/29.90 | `:728-745` | move earlier with the schedule |
| establishing opening, 18 mm, −10.00°, 2.0 s lead | `:910-916` + asserts | **DO NOT TOUCH** |
| beat 1→2 seam key at t=31.40 s | `:1088` | **DO NOT TOUCH** |
| `world/beat1_anim.blend` | 291 MB | **must be regenerated** — `:1059-1063` warns a seat change silently desyncs parts from camera |

### Cost

Nothing queued. Stated in advance:

- **720p proxy re-render of beat 1, 792 frames** — the ladder measured
  **43.3 s/frame mean, 9.5 GPU-hours** total on the 5090. At vast 5090 rates that
  is roughly **$4-7**. This is the right verification spend and it is what I
  recommend.
- **4K master of beat 1, 792 frames** — approximately **6-8× the proxy**, call it
  **55-75 GPU-hours, $25-45** against a $[redacted] balance. **Not to be spent until a
  proxy has been watched and the framing/focus candidates have been seen
  together.**

### Blocked on a decision

Change (2) alters the tour order, which the coordination brief requires be
reported rather than landed unilaterally. Changes (1) and (3) are mechanical once
(2) is agreed. Nothing has been written to `docs/beat_sheet.json`,
`world/`, or `render/`.

---

# IMPLEMENTATION — R2-829 to R2-838

Landed by the agent that inherited R2-821..R2-828. Everything below is measured
on this tree, not carried over. Candidate artefacts, so that nothing under
`docs/`, `world/` or `render/` that another agent is reading has moved:

```
docs/R2829_beat_sheet_CANDIDATE.json     the sheet
world/R2829_beat1_anim.blend             the 616-part assembly, REBUILT
world/R2829_beat1_anim_anim.json         its sidecar (new seat frames)
world/R2829_camera_rig.blend             the rig
world/R2829_camera_rig_path.json         the per-frame path
```

`docs/beat_sheet.json`, `world/beat1_anim.blend`, `world/camera_rig*.blend` and
everything in `render/` are **untouched**.

---

## R2-829 — the standoff law is lens-aware, and all fifteen presentations now fit

`tools/build_beatsheet.py`. The law was `standoff = max(radius*1.55 + 0.42, 0.75)`
— a function of the subject alone, which fixes the subtended angle at ~80 deg and
then takes the picture through whatever lens `lens_for()` returns. An 80 deg
subject through a 58 mm lens is two and a half times wider than the frame, so the
overflow was the arithmetic working exactly as written.

The replacement states what is actually wanted and solves for it:

```
max(extent_h / SENSOR_H, extent_w / SENSOR_W) == FILL_TARGET   (0.85)
```

on the eight bounding-box corners projected through the real lens from the real
direction — the FRAMING gate's own measurement, so the placer is now scored by
the instrument that judges it. It is a fixed point (`s <- s * fill / FILL_TARGET`),
iterated on the true projection, and **solved jointly with the direction** because
the R2-451 elevation clamp depends on the standoff and the standoff depends on the
direction. Non-convergence raises rather than shipping an unsolved station.

**Result: R2-317 is closed. 15 of 15 fitting, every one at exactly 0.850.**

```
cluster          lens   old standoff   new standoff        was      now
MB                35        4.86 m         7.04 m       1.31 x    0.85 x
BB                35        1.81           2.25         1.19      0.85
CI                58        1.48           2.60         1.64      0.85
halo_assembly     35        1.88           2.32         1.11      0.85
FW                35        2.08           2.58         1.14      0.85
NOSE              58        1.38           2.31         1.51      0.85
SW                58        0.75           1.08         1.24      0.85
SP                35        2.49           3.18         1.19      0.85
EC                35        2.51           3.21         1.13      0.85
FD                35        3.25           4.80         1.67      0.85
RW                58        1.53           3.80         2.28      0.85
the four corners  58     1.50-1.53      ONE station     2.01-2.32  0.85
```

**And it collapses the aperture the corners need, which is the other agent's
defect.** `fstop_required` at the group's station is **f/2.24**, against f/37-f/100
for the four individual corner presentations. RW goes f/38.5 -> f/10.9. The worst
remaining is SW at f/24.0, which is a 0.13 x 0.28 x 0.23 m object at 1.08 m.

### A correction to R2-828's own instrument

R2-828 quoted the gate's `standoff_for_fill_m` — "it would fit at 4.10 m" — as the
required distances. Those are **4-8 % high**. `s_fit = nd * extent / FILL_TARGET`
extrapolates linearly from the current distance, and extent does not fall exactly
as 1/d: the perspective term does not scale, so a box measured from close in
predicts a farther standoff than it actually needs. The fixed point on the true
projection gives RW 3.80 m where the linear estimate said 4.10, and MB 7.04 where
it said 7.52. The gate's figure is a good seed and not an answer.

---

## R2-830 — the four corners are one station, and it is also a whole-car frame

The union of the four exploded boxes is a real 5.26 x 4.42 x 0.72 m subject, 170
parts, 2,872,984 tris. It goes through the same R2-829 solve as everything else
and the FRAMING gate measures it identically — a new subject is declared and then
checked, not exempted. Its direction is the normalised mean of the four measured
presentation normals, so it is still measured rather than generated.

It is built **in memory only** and deliberately not written to
`docs/explode_plan.json`: `anim/build_beat1_anim.py` iterates `clusters` and
dereferences `parts`, so a synthetic cluster there would animate a 166-part
duplicate of four clusters that are already animated.

**Station: [-6.904, 0.366, 4.266], 7.578 m, 35 mm, 25 deg depression.**

**The unplanned result, and it is the best thing in this change.** The four
corners' seated positions are the four corners of the car, so a frame containing
the exploded group contains the assembled car. Measured from that exact station:

```
exploded corner group   0.850 of frame
ASSEMBLED CAR           0.831 of frame width
```

(0.831 is measured from the SOLVED station. On the built per-frame path the same
frame reads **0.834**, the difference being the bezier that passes through the
key rather than stopping on it. The rendered number is 0.834; both are quoted
because a claim measured off the solver and a claim measured off the path are
different claims, and this block has already been bitten once by treating a
key-derived figure as if it covered a span — see R2-842.)

The beat's climax and its establishing payoff are now **the same shot**. The
camera arrives at a wide that holds the whole car, and the car assembles inside
it. R2-822's complaint — that the first whole-car frame arrives at t = 29.0 s —
is answered at **t = 19.33 s**, which is before the last part has even landed.

The 9.20 s of four near-identical presentations is gone, and with it the
no-repeated-assets breach.

---

## R2-831 — the seat schedule, and why 0.30 / 0.36 is not flyable

`seat_start = dur*0.42`, `seat_span = dur*0.50`, summing to 0.92, so assembly
completed at 92 % of the beat by construction. Now `0.30 / 0.38`.

**The approved plan said 0.30 / 0.36 -> corners at t = 20.79 s. That schedule does
not exist.** The plan's cost model expected the pulled-back stations to make the
tour cheaper, because from farther out the bearing between adjacent clusters
shrinks and the pan term falls. That half is right. The half that was not modelled
is that `move_seconds = max(dwell, transit, pan)` and pulling the stations back
moves them APART, so transit rises and becomes the binding term.

**Measured, as minimum flyable tour time — this is the solved number the brief
asked for, replacing the predecessor's estimate of ~6.7 s recovery and t ~ 18.7 s:**

```
shipped 15-node tour, lens-blind stations     18.91 s
the SAME tour with lens-aware stations        21.19 s     framing costs 2.28 s
the 12-node grouped tour, lens-aware          17.29 s     grouping saves 3.90 s
                                                          net 1.62 s FASTER
```

The recovery is **3.90 s, not 6.7 s**. And the target was never reachable: a
17.29 s tour starting at 2.00 s cannot present the corners before 19.29 s, and
they may not seat until 2.05 s after that (1.55 s flight + 0.5 s margin). **The
floor is 21.34 s.** Even the shipped lens-blind geometry could not have seated
them before 22.96 s. 20.79 s was not taken away by the framing fix; it was never
on the table.

A 21 x 20 grid over (start, span), each cell a full Held-Karp solve against that
cell's own deadlines:

```
0.30 / 0.36    NO visiting order exists, at any speed the beat allows
0.28 / 0.40    corners t 21.340 s    the earliest feasible point on the grid
0.30 / 0.38    corners t 21.395 s    <- SHIPPED
0.42 / 0.50    corners t 28.985 s    what shipped before
```

The frontier is flat — every feasible pair has `start + 11*span/12` ~ 0.647 — so
**0.30 is kept exactly as briefed and the span alone absorbs the deviation.** One
number changed instead of two.

**Payoff: 4.01 s -> 11.29 s. 2.81x, against the 3.05x the plan hoped for.**
Corners seat f513, last part settled f521, beat ends f792.

---

## R2-832 — the solver compared a tour-relative cost against a beat-relative deadline

`solve_visit_order` filtered on `cum_cost * scale <= deadline`. `cum_cost` is
measured from the start of the tour; the deadline is measured from the start of
the beat; and the establishing lead-in is 2.0 s of difference between those two
origins. **This is why the shipped sheet presents FD at 14.54 s against a 13.20 s
deadline while the solver believed it was inside it** — visible as
`<-- PRESENTED AFTER IT HAS FLOWN` on every run of the shipped tree.

Two changes. `t0` is now passed and added. And the feasibility test is the
**minimum-time schedule** rather than a guessed scale factor: a move cannot be
flown faster than `move_seconds`, so if the cumulative `move_seconds` to a cluster
already exceeds its deadline, no allocation of any span can rescue it. The old
loop guessed a scale, filtered against it, then re-derived the scale from the
filtered answer — it converged on self-consistency, not on feasibility.

The span is then **chosen rather than assumed**: `t_k = lead + span * cum_k/total`
inverts to one upper bound on the span per cluster, and the largest span every
cluster tolerates is taken, so the beat is as unhurried as its deadlines allow.
Solved: **17.345 s, bound by CORNER_GROUP, ratio 0.997.**

Every cluster is now presented before its deadline, with no arrow on any row.

---

## R2-833 — the close-out is derived, and it is now the payoff rather than a transition

The four hand-placed close-out keys were anchored to landing frames 630 / 663 /
696, all of which R2-831 moves by ~8 s. Keeping them would have pointed the camera
at four events that no longer happen there — R2-029 reintroduced by arithmetic
instead of by omission. The close-out is now derived from the corner group's
solved station and the pinned seam key and moves whenever they do.

**And the job changed.** Making the payoff 2.8x longer without moving the camera
would have made the client's note worse, not better: R2-823 measured the payoff at
4.89 mean frame-to-frame change against 20.27 across the tour, and the complaint
was never that the camera was slow. It was that the camera went STILL exactly when
there was finally something to look at. So the payoff is **shot**: one continuous
orbit, azimuth 177 deg -> 327 deg the short way, behind the car and down its right
flank to the front-right three-quarter, radius 6.9 -> 8.1 m, descending 4.27 ->
1.90 m, lens 35 -> 40 mm so the car holds a constant size while the vantage
changes completely.

Interpolated in **cylindrical** coordinates, not Cartesian: a straight line
between two stations on opposite sides of a car goes through the car (R2-029); an
arc in azimuth cannot. Clearance never falls below 4.84 m against a 0.30 m floor.

The final orbit key **is** the seam key object itself rather than a copy of its
numbers, so there is only one place the seam is written down.

---

## R2-834 — focus is not owned here and the keys say so

The orbit keys carry `focus_distance_m` = the geometric range to the aim point and
`fstop` ramped onto the seam key's own 3.2. **These are not focus decisions; they
are the absence of one**, present only so the key is well-formed and the rig can
build it. The focus agent owns them. R2-829 has already moved the ground under
that work in their favour — see the f/37-f/100 -> f/2.24 collapse in R2-829.

---

## R2-835 — the `CORNER_FL lands on frame 591` assertion is removed, and must not come back

```python
assert int(round(times[corners[-1]] * 24)) == int(round(corner_last_t * 24))
```

`corner_last_t = dur*0.80 - dur*0.80/15` — the 15th of fifteen equal 1.76 s slots.
**That slot scheme no longer exists.** R2-062 replaced the uniform slot with a
cost-proportional allocation and the constant survived only because it happened to
remain reproducible; R2-830 removes CORNER_FL's individual presentation entirely,
so there is nothing left for the assertion to be about.

**Recorded here so it is not restored as a safety check.** It reads like one —
"the best material in the film must come out unchanged" — but it is not a property
of the picture, it is the arithmetic of a dead uniform slot. Any legitimate change
to the seat schedule, the tour or the standoff law moves that frame, and an
assertion forbidding it would forbid the fix rather than protect the shot. What
protects the shot is the FRAMING gate and the campath gate, which measure pictures.

---

## R2-836 — the part/camera desync is now a printed check, not a comment

The seat schedule was computed inside `build_beat1` while the presentation
DEADLINES derived from it were read out of `world/beat1_anim_anim.json` — the
sidecar of the last build of a 291 MB blend. Two sources for one fact, and the
sheet trusted the stale one. `seat_schedule()` is now the single source, and
`main()` compares it against the blend's sidecar and says so, loudly:

```
>> !! PART/CAMERA DESYNC: world/beat1_anim.blend was built from a DIFFERENT
   seat schedule than this sheet declares — 15 of 15 clusters disagree
   CORNER_FL  blend f696 (29.00 s)  sheet f513 (21.39 s)  -7.61 s
   REBUILD REQUIRED
```

After rebuilding: `>> part/camera sync: world/R2829_beat1_anim.blend agrees with
this sheet's seat schedule on all 15 clusters`.

**Also R2-836: the sky/camera bind is now gated in `tools/build_film_scene.py`.**
`build_camera_rig` deletes every camera and builds a fresh ONER;
`build_sky.bind_camera()` points two SCRIPTED cloud-parallax drivers at a camera
BY ID. If the sky ever predates the rig those targets go to None and build_sky's
own docstring says the decks then "sit at world XY (0,0) and behave as a skybox" —
no error, no crash, just a different sky, and a different sky is different LIGHT
even for an interior beat, because the showroom has a glass curtain wall and two
specular walls.

**Verified empirically rather than assumed, and the ordering on this path is
already correct:** `assembly10.blend` carries **0 worlds and 0 cameras**, so
`world_before is None` always fires and `build_sky` runs AFTER the rig, binding to
the new ONER. Both `world/camera_rig.blend` and `world/R2829_camera_rig.blend`
were probed directly: **no node-tree drivers at all at the rig stage**, so there
was nothing to dangle. The check is added anyway, because "it has always fired
that way" is not a guarantee and this failure is invisible downstream.

---

## R2-837 — the one aim excursion in the beat was a LENS defect, not an aim defect

The first built rig came back `CAMERA_RIG_FAIL`: `1_assembly: subject reaches
1.155 of the half-frame at frame 431`. Measured every frame of beat 1 against the
nearest cluster's bounding-sphere edge — the aim gate's own `ang / half_v`:

```
f420-433    14 frames over the 0.92 margin, peaking 1.155 @f431
everywhere else in the 792 frames    inside the margin
```

**One excursion in the beat, and the row identifies the cause:**

```
f431   lens 46.8 mm   half-frame 12.22 deg   nearest edge 14.12 deg
```

The camera is not pointed at nothing. RW's edge is 14.12 deg off axis and the
frame is 12.22 deg tall, so the subject is 1.9 deg outside a picture **a 37 mm
lens would have contained**. The hop leaves RW (58 mm) for the group (35 mm) and
the rig ramps the lens linearly across 65 frames, so the turn finishes long before
the widening does.

So the answer is not the old bridge — a key that points the camera at something
else — it is a key that finishes the widening **before** the turn needs it, which
is also what the shot wants: you widen as you pull back, so the car grows into the
frame instead of snapping wide at the end. One derived key at 28 % of the hop,
36.5 mm.

**Result: worst frame-offset 1.155 -> 0.598, and all six beats PASS.**

### The retired bridges

`BEAT1_BRIDGES` is no longer emitted, and is kept in source with its reasoning.
It covered a 110 deg pan between two stations 1.53 m from their subjects, halfway
through which the lens pointed at bare floor. Both of its premises are gone:
R2-829 pulls those stations to 3.80 m and 7.58 m, from where every station looks
inward at the same car, and R2-830 deletes CORNER_RL's individual presentation, so
the pan it covered does not occur. **It was not removed on that argument alone —
the rebuilt path was measured frame by frame and has exactly one excursion, which
is R2-837's and is elsewhere.**

---

## R2-838 — the orbit eased out onto a seam that beat 2 leaves at 1.29 m/s

The payoff orbit used a smoothstep, `u*u*(3-2u)`, whose derivative is zero at both
ends. That is the right curve for a move that stops, and this move does not stop —
it hands over to beat 2. The per-frame campath gate caught it precisely:

```
[WARN] C2_path_kink: frame 754: camera speed changes 0.0439 m/frame in one
frame, z=56.4 against a local median of 0.00086 (0.2 -> 1.2 m/s). An eased
curve does not do this; a keyframe with a linear handle does.
```

Frame 754 is the beat 1/2 seam. **A C0-continuous seam is not enough for this
film: a velocity step is a cut that does not look like one in a still.** The
easing is now a cubic with the boundary conditions the shot actually has — e(0)=0,
e'(0)=0 (the camera has been nearly still at the group station while the car
assembled), e(1)=1, e'(1)=0.80 (matching beat 2's departure instead of fighting
it). Final segment 0.78 m/s -> 1.74 m/s.

---

## Gates, and what the rest of the film did

**`campath_diff.py`, self-null printed first as required:**

```
SELF-NULL  camera_rig_path.json vs itself
   raw stored q  (the R2-103 trap)   dq 0.204607 deg      <- the floor
   re-normalised q                   dq 0.000003 deg
```

**Beats 2-6 are byte-identical AND frame-identical:**

```
beats 2-6   f793-2978   frames 2186   dp 0.0000 m   dq 0.000 deg   dlens 0 mm
```

and every non-`beat1` block of the sheet (`aim`, `beat1_2_seam`, `beat2`..`beat6`,
`beats`, `doppler`, `speed_ramps`, `time_map`, `total_s`, ...) compares IDENTICAL.
**Both pinned keys survived exactly**: the establishing opening (t=0.0,
[-0.8409, -8.8633, 3.7566], 18 mm, -10.00 deg) and the beat 1/2 seam key (t=31.40,
[6.8, -4.4, 1.9], 40 mm) are byte-for-byte unchanged.

`campath_diff`'s `PROTECTED f648-792` window reports large deltas. That window
encodes the OLD structure and is the material being moved; it is not a failure.

**Beat 1 as built:**

```
tour       MB -> CI -> halo -> BB -> FD -> EC -> SP -> SW -> NOSE -> FW -> RW -> CORNER_GROUP
span       17.345 s solved, ratio 0.997, bound by CORNER_GROUP
framing    12 of 12 fit; 15 of 15 clusters at 0.850         (was 15 of 15 FAILING)
clearance  worst 1.093 m to the car box                     (was 0.352 m)
pan        worst 8.39 % of frame width per frame, limit 12  (was 9.4 %)
speed      max 3.8 m/s per-frame, peak limit 4.0            (2 pre-flight
                                                             UNRESOLVEDs both
                                                             resolved by the
                                                             per-frame gate)
aim        worst 9.20 deg, offset 0.598, margin 0.92        (was FAIL at 1.155)
```

---

## R2-839 — the orbit was turning the way the film does not go, and that is a reversal, not a kink

R2-838 softened the seam but did not fix it: the gate still read frame 754 at
`0.3 -> 1.2 m/s`. The cause was not the easing. It was the **direction**.

The orbit took the short way round — azimuth 177 deg -> 327 deg, +150 deg —
arriving at the seam travelling **+x +y**. The film's very next key
(`beat1_2_seam`, f755, [6.757, -4.424, 1.884]) leaves it travelling **-x -y**.
That is not a kink, it is a **reversal**: the camera stops dead at f754 and goes
back the way it came. Blender's AUTO_CLAMPED handles then flatten the key, because
a local extremum is precisely what a reversal is.

**Measured — per-frame chord either side of the seam, candidate against shipped:**

```
f744   cand 0.045   ship 0.064
f750   cand 0.023   ship 0.056
f754   cand 0.010   ship 0.051      <- the seam
f756   cand 0.049   ship 0.049      <- the seam bridge takes over, identical
```

The shipped path never had this problem because its close-out arrived **already
travelling -x -y**, monotone through the key, so nothing flattened. That is a
constraint on the orbit's direction and it comes from the one-shot law.

**So the sign is now chosen by where the film goes next**, not by which way is
shorter: `seam_onward_point()` reads the first camera position after t=31.4 out of
`beat1_2_seam` / `beat2` — blocks this file does not author — and the orbit turns
whichever way leaves its azimuth rate matching. If that point cannot be found the
short way is kept and the log says the seam's velocity continuity is NOT
established, because a missing input must not become a silent claim.

The long way is 210 deg instead of 150, and at a 7.5 m mean radius that is 27.5 m
of arc in 12.08 s — which the pre-flight duly rejected at **4.04-4.52 m/s against
beat 1's 4.00 m/s peak limit** (`BEATSHEET_VIOLATION`). Two changes paid for it:

* **the rate profile is flat, not eased.** Start rate 1.00 — the camera reaches
  the group station already moving at ~1.96 m/s and easing to a standstill and out
  again is a deceleration the energy curve cannot afford. End rate 0.57, which is
  ~1.2 m/s, matching the carried-forward seam-bridge keys instead of fighting them.
* **the orbit cuts the corner.** The radius dips 1.0 m below the straight
  interpolation at mid-arc and returns to it at both ends, removing ~2.4 m of arc
  without moving either endpoint. **Bounded by the picture, not by the gate**: at
  mid-arc the radius is 6.5 m and the lens ~37.5 mm, so the 5.72 m car spans 0.92
  of frame width — still whole, which is the whole point of the payoff.

Result — the six orbit segments become near-uniform and then ease into the seam:

```
4.33  4.44  4.43  4.37  4.09  3.38 m       2.15 -> 1.68 m/s
peak estimates 2.29-3.35 m/s, all inside the 4.00 limit
```

### The path is cleaner than the film that shipped

Per-frame campath gate, both paths, same tool:

```
SHIPPED    PASS — 0 FAIL, 6 advisory
           kinks at f369, f370, f434 (the retired bridge keys' handles), f755
           rotation smears f2266-2274, f2631-2655   (beat 5, pre-existing)

CANDIDATE  PASS — 0 FAIL, 3 advisory
           kink at f754 only
           the same two beat-5 smears, unchanged
```

**Three of the shipped film's four path kinks were inside beat 1 and are gone.**
The two beat-5 rotation smears are untouched and are not mine.

**And the remaining f754 advisory is now the same character as the shipped film's
own seam advisory, not a speed step:**

```
before R2-839   f754   0.3 -> 1.2 m/s   z = 32.9      a reversal
after  R2-839   f754   1.2 -> 1.2 m/s   z = 10.2      residual curvature
shipped film    f755   1.2 -> 1.2 m/s   z =  8.8      the same thing
```

Rig verdict: **`CAMERA_RIG_CONTINUOUS_AND_AIMED`, all six beats PASS**, beat 1
worst aim 9.21 deg / frame-offset 0.598 against a 0.92 margin.

---

## R2-840 — the re-pacing moves the driver's entrance into the centre of the payoff shot

**Found downstream, caused here.** `tools/place_driver.py` makes the driver figure
appear at frame 580, and gates that choice with `figure_offscreen(...,
render/film14_path.json, ...)` — a camera **two generations old**, so its PASS was
never evidence about the shipping film and is certainly not evidence about this
one.

Under the shipped sheet f580 sat inside a 58 mm close-up of a single cluster, with
the lens 0.29 m from the cockpit; the figure appeared far outside the frame and
nobody saw it arrive. **R2-830/831/833 changes that completely**: the car is whole
at f521 and f464-754 is one continuous orbit of the assembled car.

**Measured by projecting the cockpit through both paths directly (path JSON only,
no Blender):**

```
                f575        f580        f585
SHIPPED    u  17.418      13.896      10.565     range 0.10-0.56 m   outside
R2-829     u  -0.134      -0.131      -0.128     range 6.7-6.8 m     DEAD CENTRE
```

At f580 the steering wheel is at u -0.131, v -0.068 — the middle of a clean 6.7 m
wide — with the halo (u -0.016, v 0.094) and cockpit internals (u -0.117, v
-0.043) centred beside it. **A driver materialising there is a pop in the centre
of the payoff.**

### There is exactly one window left, and it is early

Scanning from f396 (halo seats f388-396, so the cockpit is complete) to f792 for
frames where the cockpit is **out** of frame:

```
f396-427    32 frames, 1.33 s     <- the only one in the whole beat
```

From f428 to the end the cockpit is in frame continuously, because the payoff is
one unbroken orbit of the car. **The re-pacing does not merely move the hiding
place; it very nearly abolishes it.** That is a general consequence worth stating:
a beat whose payoff is a long continuous wide has almost no frames in which
anything may quietly change.

Re-measured with a DRIVER-SIZED box (the CI cluster grown 0.15 m in x, 0.30 m in
y and 0.55 m upward for helmet clearance), worst |u,v| over all eight corners,
1.00 = frame edge:

```
f400   101.96      f414   4.40      f428   1.38
f406    21.00      f420   2.41      f430   1.22   marginal
f410     8.45      f424   1.80      f434   1.05   marginal
```

**Recommendation: `--appear 400`.** The whole driver box is 102x outside the frame
there — the camera is on RW's presentation key (f399), tight on the rear wing at
58 mm. It is also motivated rather than merely hidden: the cockpit finishes
assembling at f396 and the driver arrives four frames later. Anything in f396-412
is safe; 400 is the maximum-margin choice.

**Not landed here.** `place_driver.py` is not this block's to author and the change
is one argument in the rebuild chain. Handed to the agent running that chain, with
the instruction to re-gate against `film17_path.json` rather than `film14`, and to
trust the tool over these numbers if the two disagree.

---

# R2-840 — THE REBUILD CHAIN (appended by the agent running it, not by the blocks above)

Everything under this heading is written by the chain runner. It authors no
camera, no timing and no lens; where it records a number, that number was
measured, and where it declines to act, it says so rather than acting quietly.

## R2-840 — `--appear 400` IS CORRECT AND `place_driver.py` WILL REFUSE IT

The block above recommends `--appear 400`. **It is right, and it cannot currently
be run**, because `tools/place_driver.py` refuses it eighty lines before
`figure_offscreen()` is ever consulted:

```python
EXPLODE_LANDED = 500      # measured: cockpit interior is home by here   (:62)

if a.appear <= EXPLODE_LANDED:                                          # (:719)
    print("STAGE RESULT: FAIL -- appear frame %d is before the cockpit "
          "interior lands (%d)" % (a.appear, EXPLODE_LANDED))
    return 1
```

400 <= 500. The run fails on a constant, not on a picture.

**The constant is stale, and stale in the shape R2-835 already named.** It is a
measurement of a seat schedule that R2-831 moved by roughly eight seconds. From
`world/R2829_beat1_anim_anim.json`, the clusters the driver actually occupies:

| cluster | seat | last land |
|---|---:|---:|
| CI (the cockpit interior itself) | 338 | **346** |
| SW | 363 | 371 |
| halo_assembly (closes over him) | 388 | **396** |

Everything the driver sits in is home by f346 and the halo closes at f396, so
f400 is legal *in the picture* with four frames to spare. `EXPLODE_LANDED = 500`
survived only because its input never moved — which is exactly the argument
R2-835 makes for deleting the `CORNER_FL lands on frame 591` assertion. **A gate
that forbids the fix is not protecting the shot.**

## R2-840a — MEASURED HERE, WITH THE TOOL'S OWN PROJECTION, AND IT AGREES

`figure_offscreen()` touches no `bpy` — only numpy, json and math — so
`work/r2840/appear_probe.py` lifts its body **verbatim** from
`place_driver.py:239-285` and re-points it at a camera path of choice. Copied
rather than imported because `place_driver` imports `bpy` at module scope.

**The shipped gate is not evidence about this film.** The default `--appear 580`,
over the tool's own +-8 window, H-point `[0.198, 0.000, 0.180]`:

```
film14  (what the gate actually checks)   on screen at  0 of 17 frames
film16  (the shipped film)                on screen at  0 of 17 frames
R2829   (the camera actually built)       on screen at 17 of 17 frames
```

**Seventeen of seventeen.** The driver would materialise in frame, in the middle
of the payoff orbit. Under both earlier cameras the same H-point is off screen on
every frame of the window — which is why this has never fired, and why the gate's
PASS would have been reported as a pass.

Scanning f300-784 for frames whose whole +-8 window is clear:

```
f300-332   33 frames, 1.38 s
f382-416   35 frames, 1.46 s
frames that are ALSO > EXPLODE_LANDED = 500:   NONE
```

The block above found f396-427 with a driver-sized box; this finds f382-416 with
the tool's 12-point hull. **Both contain f400**, from two different subject models,
which is the agreement worth having. And the last line is the finding: **the two
constraints do not intersect.** No `--appear` satisfies both, so this cannot be
resolved by choosing a different frame. One of them has to change.

## R2-840b — NOT CHANGED HERE, AND WHY THAT IS THE POINT

`EXPLODE_LANDED` is a beat-1 measurement inside a shared tool. Relaxing another
agent's safety gate so that one's own pipeline proceeds is the move that should
never be silent, and a chain runner is the worst-placed party to make it. It is
recorded, not landed.

**If it is landed, derive it rather than retype it** — the same correction R2-836
made for the desync check. `max(last_land)` over the clusters the driver occupies
(CI, SW, halo_assembly) reads **f396** off the sheet's own seat schedule, which
makes f400 legal today and makes the gate follow any future re-pacing instead of
forbidding it. Retyping `396` works this week and re-rots the moment the schedule
moves again.

**The 720p proxy is NOT submitted while this is open.** Rendering it would spend
real money to produce an AFTER clip carrying a centre-frame driver pop that the
BEFORE clip does not have, contaminating the exact A/B the render exists to make.

## R2-840c — THE DRIVER BLEND IS FOUR STEPS, NOT ONE

Recorded because the chain reads as one line and is not, and skipping the tail of
it renders an unpainted car.

```
world/beat1_anim.blend        0 R2CP_/R2IMP_ node markers
world/car_anim.blend        376
```

So `world/car_paint.py --save` and `tools/imperfections.py` land **after**
`anim/build_car_anim.py`, per R2-521/R2-531, and the shipped `car_anim_driver.blend`
is `build_car_anim -> place_driver -> car_paint -> imperfections`. Also note
`place_driver.py`'s docstring USE line is wrong: it shows `blender -b
--factory-startup -P tools/place_driver.py`, but the script operates on the
**currently open** blend and never opens one, so the car must be named on the
command line.

## R2-840d — THE FOCUS POST-PASS TARGETS THE FILM BLEND, NOT THE RIG

`tools/build_film_scene.py` calls `build_camera_rig.main()` internally, so focus
written to `world/R2829_camera_rig.blend` is overwritten by the film build.
R2-791's pass therefore runs on `render/film17.blend` after it. The depth grid is
still measured on the 291 MB rig blend, per R2-805 — legitimate only because both
cameras come from the same builder and the same sheet, which
`work/r2840/campath_identity.py` checks rather than assumes.

`SOLVE.load_field()` hardcodes `world/beat1_anim_anim.json` — the **stale**
schedule (corners f696, not f513). It does not reach a focus value: `_interp_keys`
clamps at both ends, so one measured frame in the grid densifies subject depth
across all 792 and the geometric field stays a fallback that is never taken. Worth
knowing before someone reads the path and assumes the worst.

### R2-840a — landed: `EXPLODE_LANDED` is derived, and the appearance is gated against the film being built

Two typed values in `tools/place_driver.py` had gone stale, and together they made
the tool unsatisfiable: **the driver may not appear before frame 500, and under the
re-paced camera there is no frame after 500 where he is off screen.** The chain
agent found this, measured it, and correctly refused to relax another block's
safety gate to get its own pipeline moving. It is landed here instead, because
both values are beat-1 measurements and it is this block that invalidated them.

**1. `EXPLODE_LANDED = 500` is now derived** from the part animation's own sidecar
— the file `anim/build_beat1_anim.py` writes beside the blend — over the three
clusters the figure is actually IN: the cockpit internals he sits in, the wheel he
holds, and the halo that arcs over his head. `last_land`, not `seat_frame`,
because a cluster's parts are staggered and the last one is the one that would be
seen arriving around him.

```
world/beat1_anim_anim.json          CI 473  SW 506  halo 539   -> f539
world/R2829_beat1_anim_anim.json    CI 346  SW 371  halo 396   -> f396
```

Missing sidecar now RAISES rather than falling back on a remembered number, which
is the R2-836 correction applied to a second place.

**Note this broadens the gate**, and deliberately. The old constant's own comment
said "cockpit interior is home by here", and 500 was right for CI alone (473) —
but the wheel lands at 506 and the halo at 539, so a driver appearing at 501 would
have had the steering wheel fly into his hands. **The shipped film was never
exposed to that** because it used `--appear 580`, and 580 > 539, so the stricter
derived gate does not retro-break it:

```
shipped --appear 580  vs derived old-schedule f539   PASS
new     --appear 400  vs derived new-schedule f396   PASS
```

**2. The appearance is gated against `--campath`**, not a hardcoded
`render/film14_path.json`. Over this tool's own +-8 window at the default appear
frame, the chain agent measured the figure on screen **0 of 17 frames under film14
and film16, and 17 of 17 under the camera actually built** — the gate was passing
on a film nobody was making. The stale default is retained so existing callers
keep working, and it now prints a warning naming itself as superseded.

Landed on top of another agent's uncommitted R2-401 work in the same file
(`--hip-raise` / `--fit-warn-only`), in disjoint regions, and left uncommitted
work untouched.

## R2-840e — `--campath render/film17_path.json` IS NOT REACHABLE, AND WHAT IS USED INSTEAD

R2-840's new `--campath` is right and the instruction attached to it — *"pass
`--campath render/film17_path.json`"* — cannot be followed, for a structural
reason rather than a preference.

`render/film17_path.json` is **written by** `tools/build_film_scene.py`: it runs
`build_camera_rig.main()` internally with its own `--out`, and the rig builder
dumps `<out>_path.json`. `build_film_scene.py` consumes the driver blend as
`--car`. So `place_driver.py` must run BEFORE the file it is being asked to gate
against exists. The dependency is circular.

**Used instead: `world/R2829_camera_rig_path.json`** — the standalone rig, built
by the same `anim/build_camera_rig.py` from the same
`docs/R2829_beat_sheet_CANDIDATE.json`, therefore the same camera.

**That is verified, not assumed.** `work/r2840/campath_identity.py` runs
immediately after the film build and compares the two paths frame by frame over
every beat-1 frame the two share, on position, quaternion and lens, requiring
exactly 0.0 on all three. Anything else means the appearance gate was measured on
a camera the film does not have, and the correct response is to redo
`place_driver`, not to accept the result.

The same substitution is what lets `tools/r2791_depth_grid.py` be measured on the
291 MB rig blend instead of the 7.5 GB film — R2-805's own instruction — so one
check licenses both. Worth stating plainly: **two stages of this chain depend on
that identity, and neither would announce itself if it were false.**

---

## R2-841 — the instrument for the client's actual note, validated against R2-823 before use

`tools/beat1_energy.py`. R2-823's inversion measurement — 20.27 across the tour
against 4.89 across the payoff — is the mechanism behind "way too slow I feel" and
is the thing R2-830/831/833 were built to fix. **It was published with no tool
beside it.** That matters here more than usual: two other beat-1 figures in this
project turned out to have come from instruments that do not measure beat 1
(`lap_shotscale.py` prints `car exploded; not measured`) or that are unreliable
over a quarter of it (`beat1_true_extent.py`, R2-826).

So this tool reproduces R2-823 on R2-823's own frames FIRST and refuses to report
any comparison until it does — an instrument that cannot recover a known result is
not evidence about a new one.

```
REPRODUCING R2-823 on ~/vast-render/out/seq/r2beat1
  segment                   n  pub n     mean      pub   median      pub
  establishing wide        60     60    13.16    13.16    13.34    13.34  ok
  unreadable tour         571    571    20.27    20.27    19.83    19.83  ok
  car resolves             65     65    14.59    14.59    10.79    10.79  ok
  readable payoff          95     95     4.89     4.89     4.60     4.60  ok
>> STAGE RESULT: ENERGY_SELFTEST_OK
```

Exact on all four segments, means and medians both, so the AFTER numbers will be
directly comparable rather than merely similar.

**The AFTER sequence is reported against its OWN landmarks, not the old ones.**
The R2-823 segment edges (2.5 / 26.3 / 29.0 s) are properties of the cut being
replaced; using them on the new cut would score the fix against the geometry of
the thing it fixed. The new edges are the new landmarks: establishing 0-2.0 s,
tour 2.0-19.33 s (to the corner-group presentation), car resolves 19.33-21.71 s
(to the last part settling at f521), payoff 21.71-33.0 s.

**Prediction, registered before the frames exist**, so it can be wrong: the tour
figure should fall (the stations are 2-3x further out, so the same camera motion
subtends less image change) and the payoff figure should rise substantially (the
payoff is now a 210 deg orbit rather than a near-static hold). The ratio should
come down from 4.14x toward ~1. If the payoff figure does NOT rise, the orbit is
not doing its job and the client's note is not answered, whatever the framing
numbers say.

## R2-840f — PARKED: THE SHEET CHANGED UNDER A RUNNING CHAIN

`docs/R2829_beat_sheet_CANDIDATE.json` was re-authored (orbit radius dip
1.00 -> 0.35, lens ramp ease-late) while `tools/build_film_scene.py` was 11
minutes into reading it. Recorded because the response is the interesting part.

**`render/film17.blend` was killed rather than kept.** It had not reached its
save, so nothing is on disk — but the reason it would have been discarded even if
it had is worth writing down: `build_film_scene.py` runs `build_camera_rig.main()`
internally against `--sheet`, and a build that read an input while it was being
rewritten cannot say *which version it got*. The artefact might well have been
correct. **"Probably built from the right camera" is not a property anything
downstream can check**, and every gate below it — the focus solve, the campath
identity check, the appearance gate — would have reported PASS against whichever
camera it happened to contain. A build whose provenance is unknown is worse than
no build, because it looks exactly like a good one.

**The depth grid is superseded and was renamed, not merely noted.**
`R2791_GRID_OK` measured 912,384 rays against `world/R2829_camera_rig.blend` as
it stood at dip 1.00. Focus fitted to that grid would be focus fitted to a camera
that no longer exists — the R2-791 defect exactly, arrived at from the other
direction. It is now
`work/r2840/depthgrid_R2829_SUPERSEDED_dip100.json`, and because
`work/r2840/chain2.sh` refuses to start without a grid at the live path, the
staleness is structural: the chain cannot silently re-use it. A comment saying
"this is stale" would have depended on the next reader reading it.

**What survives, and why it is safe to keep.** `CAR_ANIM_BUILT`,
`R2521_CARPAINT_APPLY_OK`, `IMPERFECTIONS_OK` and `place_driver`'s
`STAGE RESULT: OK` are all independent of the camera. The one that needs an
argument rather than an assertion is `place_driver`: its appearance gate is a
statement about frames 392-408, the orbit re-author moves f464 onward, and the
two do not overlap — so the 0-of-17 result holds. If a future change touches
anything before f408, that gate has to be re-run, and this paragraph is the
record of why it did not need to be this time.

**Nothing was spent.** The 720p proxy was not submitted.

---

## R2-842 — the payoff cropped the car for 1.33 s, and I made R2-429's mistake to put it there

**The FRAMING gate checks presentation KEYS. The payoff is 329 frames of
continuous orbit BETWEEN keys, and every claim I made about it was a claim about
a span checked only at its endpoints.** Projecting the assembled car's box through
every frame of the built path:

```
dip 1.00 m    f464-792   min 0.588   max 1.046 @f580   mean 0.818
              frames where the car does NOT fit: 32   (f565-596, 1.33 s)
```

1.33 s of a payoff whose entire purpose is that the car is finally whole,
answering a note that was literally "too zoomed in".

**The cause was my own arithmetic, and it is the error this file already
documents.** R2-839 justified the 1.0 m radius dip like this: *"at mid-arc the
radius is 6.5 m and the lens is ~37.5 mm, so the 5.72 m car spans 0.92 of the
frame width."* 5.72 m is the car's **length**, which is its apparent width only
when the camera is broadside. Mid-orbit the camera is neither broadside nor level,
so the projected extent is larger than the length subtense. **R2-429's headline
made precisely this mistake** — "the car is never smaller than 76.1 % of frame
width" — and the correction sits three screens above the line I wrote. I
reproduced it inside the block that corrects it.

**Fixed two ways, both bounded by the measurement rather than by an estimate:**

* `BEAT1_ORBIT_RADIUS_DIP_M` 1.00 -> **0.35**.
* the orbit's lens ramp is **ease-late** (`e*e`), so it holds near 35 mm through
  mid-arc — where the car is most oblique and therefore widest in frame — and
  tightens only as the orbit settles. It still lands exactly on the seam's 40 mm.

```
dip 0.35 m    f464-792   min 0.559   max 0.921   mean 0.756
              frames where the car does NOT fit: 0
```

### `tools/beat1_perframe_audit.py` — the other span claims, now checked

Written because this defect was a class, not an incident:

```
CLAIM 1  the payoff orbit holds the whole car, every frame
         max 0.921, 0 frames fail                              PASS
CLAIM 2  the orbit never nears the car box (floor 0.30 m)
         worst 4.514 m @f662                                   PASS
CLAIM 3  beat 1 never flies through the car
         worst 1.074 m @f273                                   PASS
CLAIM 4  the establishing frame is untouched and still widest
         f1 = 0.350 of frame width, exactly R2-826's 35.0%     PASS
```

Gates after the fix: `BEATSHEET_OK`, `CAMERA_RIG_CONTINUOUS_AND_AIMED` (six of six
PASS, beat 1 aim 9.23 deg / offset 0.600), campath `PASS — 0 FAIL, 3 advisory`.
**The seam advisory improved again to z = 8.1, now better than the shipped film's
own f755 at z = 8.8.**

### Cost, and what it says about the order of operations

This invalidated a running rebuild: `render/film17.blend` was mid-build against
the superseded sheet and the depth grid had been measured on the superseded rig.
Both were discarded and re-run. **Editing a live input under a running chain is
the mistake; the lesson is that the per-frame audit belongs before the chain
starts, not after it.** No render spend was lost, because the chain was stopped
before the 792-frame submission.

## R2-840g — RE-RUNNING THE DEPTH GRID WAS NECESSARY, AND HERE IS THE NUMBER

The grid was re-measured against the R2-842 rig on the argument that fitting
focus to a superseded camera is R2-791's own defect from the other side. That
argument is now a measurement. Comparing the two grids frame by frame, over the
386 sampled frames both carry subject depth on:

```
whole beat, median |delta|                      0.000 m
the re-authored payoff, f464 onward   median    0.185 m
                                      max       0.625 m
```

**Two things fall out, and the first is the useful one.** Before f464 the two
grids agree *exactly* — median and max both 0.000 m — which independently
confirms R2-842 touched only the payoff and left the presentation tour alone. It
is a check on the re-author that the re-author did not have to be trusted for.

And after f464 the subject moved by up to **0.625 m**. Had the old grid been
reused, that is how far the focal plane would have sat from the subject through
the payoff — on the very shot the client called too blurry, in a beat whose close
stations have 13-55 mm of depth of field. **The staleness was worth 0.625 m, not
nothing**, which is the difference between a precaution and a fix.

Recorded because "re-run it, it might be stale" is a weak argument that happens
to be right, and "re-run it, here is what it was worth" is a strong one. The
superseded file is kept as `depthgrid_R2829_SUPERSEDED_dip100.json` precisely so
this comparison remained possible.

## R2-840h — THE BREACH REFUSED, AND THE REFUSAL COUNT WENT 9 -> 10 BECAUSE THE SHOWROOM GREW A CEILING

`sim/apply_breach.py` refused film17 on `glazing_pocket_clear`. Two separate
things were going on and only one of them was mine.

**First, the refusal itself is expected and `--force` is the canonical
invocation.** `sim/land_breach.sh` says so in as many words — *"`--force` is
still right; read `R5_intruders_over_the_wound_after` in the apply report, not
the preflight's headline count."* R2-271 records the history: the check refuses
on geometry the applier does not own, it has refused on every apply since film9,
and the acceptance criterion is measured after the build, not before it. **The
chain omitting `--force` was an authoring error in the chain, not a defect in the
scene.**

**Second, and the part worth measuring: the count was 9 for film16 and 10 for
film17.** Forcing past an unexplained extra intruder is exactly what that note
warns against, so the tenth was identified before anything was written.
`--preflight-only` (which writes no scene) gives the full population:

```
GW_Front_Mull_14, GW_Front_Transom_0/1/2   the SOUTH wall's frame
GW_Right_Transom_0/1/2                     round 1's east frame, what eastframe.py cuts
WallLine_SideFin_0/1                       the two light fins
R2C_PerimeterReveal                        <- not in film16's nine
```

`R2C_PerimeterReveal` is the showroom ceiling's perimeter shadow-gap backing
(`world/items/showroom_ceiling.py`, R2-517). It is a box from z 6.030 to
`Z_DECK + DECK_T` = **6.198**, and the glazing pocket tops out at **6.1120** — so
it clips the top **82 mm** of the pocket where the ceiling meets the wall head,
around the whole room perimeter, which is why it registers on the east wall at
x ~ 14.95. That is **six metres above the wound**.

**And it is new because the ceiling is new, not because anything broke:**

```
world/showroom_ceiling.blend   built 08-04 18:33
render/film16.blend            built 08-04 16:26   <- two hours EARLIER
```

film16's build log contains no ceiling line at all; film17's reads
`>> appended R2_SHOWROOM_CEILING (21 objects, 73996 polys)`. **film17 is the
first film in this project with a ceiling in the showroom.** The tenth intruder
is a feature arriving, in the same class as the south wall's frame and the light
fins: real, correctly detected, and not this module's to move.

*Generalises to:* **a count that changes is a question, not a verdict.** 9 -> 10
looked like a regression and was a new asset; the only way to tell was to name
the object. `--preflight-only` exists precisely so that can be asked without
writing anything.

## R2-840i — THE A/B IS CONFOUNDED: `BEFORE` HAS NO CEILING AND `AFTER` DOES

Stated on its own because it is the one finding in this block that changes how
the deliverable should be READ, and a reviewer who does not know it will
misattribute.

`watch/BEFORE_beat1_33s.mp4` comes from `film16_breach`, built 08-04 16:26.
`world/showroom_ceiling.blend` was built 08-04 18:33. **The BEFORE clip was
rendered in a showroom with no ceiling**, and film17 is the first film in this
project that has one — 21 objects, 73,996 polys, appended by
`tools/build_film_scene.py`, which now refuses to build without it.

**Beat 1 is the interior beat, so this is not a neutral addition.** It is a large
bounce surface directly above the subject, in a shot graded at a fixed exposure
of -3.628. Ambient level, fill on the upper surfaces of the 616 exploded parts,
and the character of the room's indirect light are all now inside the difference
between the two clips, and **none of them are R2-829 or R2-842.**

**Nothing is being done about it, deliberately.** The ceiling is correct and the
film should have it; rendering film17 without one to obtain a cleaner comparison
would mean shipping a worse scene to protect a measurement, which is the wrong
way round. What is required is that the confound is declared, so that:

* differences in FRAMING, PACING and FOCUS may be attributed to the re-author;
* differences in BRIGHTNESS, FILL and AMBIENT may not.

*Generalises to:* **an A/B built from two dates is an A/B over every change
between those dates.** The clips are eleven days and an unknown number of
landings apart. The honest form of the claim is not "this is the re-framing" but
"this is the re-framing plus everything else that landed", and the only way to
narrow it is to name what else landed. The ceiling was found by accident, while
diagnosing a breach refusal — which means the right question for the next
comparison is what ELSE differs that nobody tripped over.

## R2-840j — AND THE CEILING REALLY IS IN THE WOUND. THE POST-BUILD GATE CAUGHT WHAT MY REASONING MISSED

R2-840h argued `R2C_PerimeterReveal` was benign because it sits six metres above
where the car goes through. **That argument was wrong, and the gate said so:**

```
R5 intruders OVER THE WOUND, after   FAIL   [['R2C_PerimeterReveal', 0, 15, 8, 3]]
```

The error was in reading "the wound" as the car's path. It is not. `apply_breach`
defines it as **bays 4 and 5's whole clear opening**, y -2.1625..2.1625, full
height — the aperture, not the trajectory — and `_tris_hit_box` finds **3
triangles** of the reveal crossing it. Height was never the question; the reveal
enters the opening at the head and that is inside the box.

**This is why the check is a triangle test and not an AABB or a vertex test**
(R2-125): the reveal's vertices are metres away around the perimeter, and only
its faces cross. The identical failure mode the check was built for.

**Everything else about the apply is correct**, and identical to film16:

```
built 3845 objects, 278864 tris, 5806793 keys      film16: 3845 / 278864 / 5806793
east frame census   PASS   39 of 39 pieces
east wall census    PASS   all 10 bays have a GP_b* pane, none hidden at frame 1
R5 elsewhere        9      byte-identical to film16's accepted nine
```

So the entire delta between this apply and the shipped one is **one object, three
triangles**.

**What it is not.** It is not a bar across the aperture. The thing this check was
protecting against was `GW_Right_Transom_0/1/2` — three unbroken 21.9 m transoms
that would have survived the car flying through them. The reveal is ceiling trim
at the head of the opening, in the top ~1.3 % of its height. **But "smaller than
the defect the check was built for" is not the same as "not a defect", and that
judgement is not the chain runner's to make.**

**What it means for the beat-1 proxy, stated so the decision is easy.** Beat 1 is
frames 1-792; the breach is 865-1056. Through the whole proxy the east wall's
glass is intact and unbroken, which is exactly what the east wall census PASSes
on. The failing criterion is a property of the aperture in beat 3 and the proxy
does not reach it.

**The proxy was NOT submitted.** A gate failed, and the instruction for this
chain is to stop and report rather than route around it — twice now that has been
right. `render/film17_breach.blend` is complete on disk (7,979,667,219 bytes) and
is renderable the moment someone owning the ceiling or the breach says the three
triangles are acceptable, or trims them.

## R2-840k — THE FIX: THE PERIMETER REVEAL WAS INSIDE THE GLAZING POCKET ON BOTH GLAZED WALLS

**A change to `world/items/showroom_ceiling.py`, which is somebody else's committed
and verified module.** Written up in full so its author can see exactly what moved
and disagree with it.

### What was wrong

The perimeter reveal backs the shadow gap at the wall head. It was one box per
wall, all four with the same underside:

```python
a.box(x0, x1, y0, y1, 6.030, Z_DECK + DECK_T)
```

On the two SOLID walls that is right and nothing is behind it. On the two GLAZED
walls the curtain wall's **glazing pocket** is behind it — the 24 mm channel the
panes sit in, x 14.9455..14.9695, topping out at z **6.1120**. A backing plate
reaching 6.030 sits **82 mm inside that channel**: ceiling trim occupying the slot
the glass lives in. An overlap, not a design.

### Why nobody saw it

The reveal's own vertices are metres away around the perimeter and only its
**faces** cross the pocket, so a vertex test or a bounding-box test reads clear.
It took `apply_breach`'s triangle test — R2-125, built for precisely this after
round 1's east mullions passed a vertex-only sweep of 29,387 meshes — to find 3
faces inside the breach aperture's clear opening.

### The change

```python
Z_REVEAL_BOT        = 6.030    # solid walls, unchanged
Z_REVEAL_BOT_GLAZED = 6.115    # 3.0 mm clear of the pocket head, 6.1120
```

and the four strips now carry their own underside, N and W unchanged, S and E
lifted. **Both glazed walls, not just the east one.** The south wall carries the
identical overlap and escaped notice only because the breach does not open there;
fixing one and leaving the other would be fixing the symptom.

### Measured after, on the 7 MB library rather than the 7.5 GB film

```
faces in the POCKET : 3      faces in the WOUND (bays 4-5) : 0
STAGE RESULT: REVEAL_CLEAR_OF_WOUND
```

The 3 remaining pocket faces are the NORTH strip's `x = +15` corners at y ~ +11 —
a solid wall, 10.9 m from the aperture, in the same accepted "elsewhere" bucket as
the south wall's frame and the light fins. **The wound is clear, which is the
criterion.**

`CEILING_SELFTEST_CLEAN` after the edit; the library rebuilds to the same
**21 objects / 73,996 polys**, so the topology is untouched and only two strips'
undersides moved.

### One methodological note, because the first measurement of this was wrong

The first version of `work/r2840/verify_reveal.py` ignored the pocket's **y**
bound and reported `REVEAL_STILL_IN_POCKET`, because it was catching the north
strip's `x = +15` corners — unchanged, and nowhere near the aperture. **A box test
that drops an axis is not a box test.** The corrected script tests all three and
reports the pocket and the wound separately, which is also the distinction the
applier itself draws.

## R2-840l — THE PROXY IS SUBMITTED, AND IT WAS RESUBMITTED IN CHUNKS RATHER THAN AS ONE JOB

Submitted `r2beat1_v2` off `render/film17_breach.blend`, 1280x720 / 64 samples /
CYCLES / OPENIMAGEDENOISE / `--dof scene` / adaptive 0.01, frames 1-792.

**The first submission was cancelled without ever running, and the reason is worth
keeping.** `rq anim` accepted the whole 792-frame range as ONE job and then said:

```
!! ONE JOB, 792 FRAMES — this holds a worker for ~9.4h and nothing preempts it:
!! run_sequence does not yield, and the dispatcher only re-evaluates fairness
!! BETWEEN jobs. Two such submissions once held the farm for 10,200 s while
!! seven agents' 60 s renders could not run.
```

The broker was not speaking hypothetically: at that moment it had **6 other jobs
queued and 1 running**, and the running one was another agent's `r2851ab`, itself
submitted as `20/62 frames` — **they were already following the convention.** A
792-frame job at `--prio 90` would have taken the only worker for nine and a half
hours and starved every one of them.

Cancelled `4fc754a6e63d` and resubmitted as **13 chunks of <= 62 frames** under
the same `--name`, which is the resume key, so chunking costs nothing and the
7.98 GB scene stays resident across them.

```
1-62   5dcd5edad9b1     435-496  fe23eeb4be35
63-124 339d8471225f     497-558  8cc80d2d6cb1
125-186 9093af29781d    559-620  0f12f7f62a0c
187-248 2a4533c42d99    621-682  fe349e095287
249-310 c4a393e49f04    683-744  d4d7e236b1cf
311-372 527eca7ecba2    745-792  2744aa4b659e
373-434 0067b8bcadaa
```

Projected **$4.21** total (12 x $0.33 + $0.25), against a $150 cap with $9.24
spent. The broker flags its own estimate as a BASIS MISMATCH — 43 s/frame measured
on other sequences, not this spec — so the actual will be reported when it lands.

*Generalises to:* **the tool's warnings are load-bearing and this one names its own
incident.** A submission that is accepted is not a submission that is neighbourly,
and on a shared farm the difference is nine hours of somebody else's work.

## R2-840m — THE DRIVER APPEARANCE IS CLEAN ON PIXELS, NOT JUST ON THE GATE

`place_driver`'s gate said the figure is off screen on all 17 frames of its
window. That is a projection of a 12-point hull, so it is a claim about a model.
Checked against the rendered frames instead — adjacent-frame RMSE across the
appearance, where `DRV_*` become visible AT f400:

```
baseline adjacent-frame RMSE, f300-361      0.070 .. 0.167

f396->f397  0.1040
f397->f398  0.1015
f398->f399  0.1005
f399->f400  0.0840   <-- the driver becomes visible on this step
f400->f401  0.0887
f401->f402  0.0996
```

**The appearance frame is the SMALLEST step in its own window** and sits well
inside the baseline. A figure materialising in shot would spike; this dips,
because the step is dominated by camera motion and the driver contributes
nothing. R2-840's defect is closed on the picture.

Worth stating why this check is not redundant with the gate: the gate and the
render share no code. The gate projects a 12-point hull through a camera path
JSON; this measures what Cycles actually drew. **An agreeing independent
instrument is the only thing that upgrades a model's claim into a fact** — and
the original defect existed precisely because a gate agreed with itself against
the wrong camera for two generations.

Method is the ladder's own (`docs/RENDER-LADDER.md`): *"diff adjacent frames to
surface temporal defects a human eye smooths over."*

## R2-840n — R2-842's CROP FIX, CONFIRMED ON THE DELIVERED FRAME

f580 is the frame R2-842 measured at **fill 1.046** — the worst of the 32
(f565-596) where the payoff orbit cropped the car. In the delivered 720p frame
the whole car sits inside the frame with clear margin on all four sides.

The prediction was made from a per-frame projection and the render is an
independent instrument; they agree. Also visible in the same frame: the driver's
helmet in the cockpit, correctly seated. He becomes visible at f400 OFF SCREEN
(R2-840m) and is legitimately in shot by f580 — the fix was to stop him
MATERIALISING in view, never to hide him, and both halves of that now have a
picture behind them.

## R2-840o — THE FOCUS RESULT IS NOT VOID, AND THE STALE PATH IS IN THE CONTROL, NOT THE PASS

A correction, because getting this wrong in either direction misreports the client's
own feedback loop.

**The claim:** `tools/r2791_beat1_focus.py` reads `render/film16_path.json` — the
superseded camera — and hardcodes it at line 574 for frames 1-792, so the focus
fix was computed against a camera the film does not have, and the client's blur
note is unanswered.

**The path is real. It is in two places, and the applied pass calls neither:**

```
line 574  ->  inside  def selftest():   (line 518)   R2-800's two-sided control
line 621  ->  inside  def main():                    the standalone CLI's --path default
```

`tools/r2791_apply_focus.py` — the thing that actually wrote the keys — touches
only `CLOSEOUT_F`, `HANDOFF_FRAMES`, `depth_from_grid()`, `solve()` and
`load_field()`. None reads a camera. The `cams` handed to `solve()` are built
inside `apply_focus` from the OPENED BLEND, frame by frame through Blender's own
evaluation, and its log says which blend:

```
>> read 792 frames of camera ONER from render/film17.blend
>> subject/background depth MEASURED from work/r2840/depthgrid_R2842.json (386/396)
>> GUARD: position 0.000e+00 m, rotation 0.000e+00, lens 0.000e+00 mm over 42 frames
```

and the grid it used was measured on the rebuilt R2842 rig, which
`campath_identity.py` proved bit-identical to film17's ONER — `dp 0.000e+00 m,
dq 0.000e+00, dlens 0.000e+00 mm over 792 beat-1 frames`. **The focus curve was
solved against the camera the film actually has.** That is the property R2-796
was designed to guarantee: *"the solved curve contains no frame numbers... re-run
it and the focus is re-derived from the camera that actually exists."*

**What IS stale is the CONTROL, and that matters differently.** R2-800's
two-sided selftest — solver must AGREE at stations, DIVERGE between them — reads
`film16_path.json` and the shipped `docs/beat_sheet.json`. Against the R2-829/842
sheet those are different generations, so it reports **SKIP, not PASS**, exactly
as R2-806a already recorded. So:

* the focus **was applied** correctly, per-frame, from measured depth, with the
  camera provably untouched;
* the solver's **validating control has not been re-run on this generation**.

"Applied against the right camera but with an unre-run control" and "computed
against the wrong camera" are not the same statement, and only the first is true.

*Generalises to:* **a grep for a stale filename finds every use of it, including
the uses that do not matter.** Which function encloses the line decides whether it
is a defect or a footnote, and that is one `awk` away.

## R2-840p — WATCHING IT: PACING IS ANSWERED ON PIXELS, AND THE BLUR NOTE HAS MOVED HOUSE

Adjacent-frame RMSE off the delivered 720p frames, as a proxy for on-screen
motion. It is the same instrument used for the driver appearance (R2-840m) and it
needs no access to the scene.

```
TOUR    f80-450     median 0.138    range 0.056 .. 0.182
PAYOFF  f470-600    median 0.081    range 0.057 .. 0.102
```

**PACING — answered.** R2-823 measured the shipped payoff at 4.89 mean
frame-to-frame change against 20.27 across the tour: a ratio of **0.24**, which is
the "camera goes still exactly when there is finally something to look at" that
the client actually objected to. The delivered payoff runs at **0.59** of the
tour. It is no longer the dead spot, and it is still visibly calmer than the tour,
which is the distinction R2-833 was aiming at — *shot*, not *still*, and not
frantic either.

**FRAMING — answered.** R2-840n: f580, measured at fill 1.046 before, holds the
whole car with margin. f464 holds the assembled body plus the presenting corners.

**BLUR — the fix landed and the complaint may survive it, for a different
reason.** At f258, the frame R2-804 described in the shipped arm as *"one sharp
object in a cream field... the tyre behind it is a formless dark blob with no
tread, no rim and no brake gear"*, the delivered frame resolves the tyre's tread,
rim, brake gear and red sidewall band, and the glass wall reads as mullions rather
than a wash. **The focus change is visible and it works.**

But the dominant softness in that frame is now **MOTION BLUR**, not defocus, and
nobody has asked about this:

* the tour runs at 0.11-0.18 adjacent-frame RMSE — fast camera motion, and at a
  1/2-ish shutter that is a lot of smear at the close stations;
* **R2-831 made the tour 1.62 s FASTER than shipped.** Whatever the re-pacing did
  for the payoff, it can only have increased motion blur across the presentation
  stations;
* R2-804 already flagged motion blur as "a separate and untouched defect... that
  is shutter and camera speed" and assigned it elsewhere. It is still untouched.

**So if the client watches this and still says "too blurry", the cause will be
shutter, not aperture, and the correct response will NOT be to stop down further.**
Recording it now, before the verdict comes back, so the diagnosis is not
re-litigated from scratch against a fix that already landed.

## R2-840q — f150 IS THE FRAME THAT SETTLES WHETHER THE FOCUS FIX REACHED THE PICTURE

R2-840o argued from the code that the focus was solved against film17's own
camera. f150 settles it from the other end, on a delivered frame, and it is the
right frame to settle it on because R2-804 nominated it in advance:

> *"f150, a transit frame — the largest measured focus error in the beat, 3.71 m,
> and the one that ISOLATES FOCUS FROM APERTURE. The shipping curve is at
> 2.041 m; the lens is actually pointed at material 5.754 m away. Nothing whatever
> in the shipping frame is sharp — not the wheel, not the stanchion, not the floor
> line, not the wall."*

and it predicted what a working fix would look like:

> *"the plane lands on the wheel and suspension at ~5.7 m. The tyre's red sidewall
> band, the rim and the brake structure resolve; the suspension links read as metal
> with defined edges; the rope stanchion gains a hard edge and a defined base disc."*

**The delivered frame shows every one of those.** Rim, brake disc and hub are
legible, the red sidewall band reads, the suspension links read as metal with
defined edges, and the stanchion has a hard edge and a defined base disc.

**This is the arm of the evidence that aperture cannot fake.** At f258 an
improvement could be attributed to stopping down. Here the shipped frame had NO
sharp content anywhere, so a readable wheel can only have come from moving the
plane — which is precisely why R2-804 nominated this frame. A prediction
registered in advance, on a frame chosen in advance, met on the delivered pixels.

**The blur that remains in it is motion blur** and it is directional: the tyre's
trailing edge and the floor's light streaks smear left-to-right while the
suspension links stay crisp. Focus and shutter are separable in this frame and
only one of them was fixed (R2-840p).

## R2-840r — DELIVERED

```
watch/AFTER_beat1_33s.mp4     18,218,991 bytes
                              h264 / 1280x720 / yuv420p / 24 fps / 792 frames / 33.000 s

sequence r2beat1_v2           792 frames, 0.80 GB, mean 31.7 s/frame
                              rq seq verify DEEP: every file re-hashed and re-measured, 792 OK
                              independent missing-frame-number check: 792/792, missing none
cost                          792 x 31.7 s = 6.97 GPU-h x $0.4403/hr = $3.07
                              (projected $4.21; the brief budgeted $5.50-6.00)
```

**Spec-identical to the BEFORE clip** — same codec, resolution, pixel format,
frame rate, frame count and duration to the millisecond — so nothing in the
comparison is a container artefact.

### The three client notes, and only two of them are answered

| note | verdict | the evidence, on delivered pixels |
|---|---|---|
| "way too slow" | **ANSWERED** | payoff motion 0.24 -> **0.59** of the tour (R2-840p) |
| "way too zoomed in" | **ANSWERED** | f580 fill 1.046 -> holds with margin; f464 holds body + corners (R2-840n) |
| "too much blur" | **FIX LANDED, NOTE NOT CLOSED** | f150 and f258 resolve exactly as R2-804 predicted (R2-840q) — but motion blur is now the dominant softness and the tour got **1.62 s faster** (R2-840p) |

The third line is the one to hold carefully. The focus fix is real, was applied
against the film's own camera (R2-840o), and is demonstrated on a frame nominated
in advance. **It is still not a claim that the client's blur note is closed**,
because shutter was never touched and R2-800's validating control reports SKIP on
this generation. If the note comes back, the answer is shutter, not aperture.

### And the comparison carries an uncontrolled variable

**film17 is the first film in this project with a showroom ceiling** (R2-840i).
Seeing f1 rendered, this is larger than first described: the ceiling is a coffered
drum with a radial ribbed dish directly over the turntable and it occupies roughly
the top third of the establishing frame. **The opening shot of the AFTER clip is
dominated by geometry that does not exist in the BEFORE clip.**

Attributable to R2-829/842: framing, fill, pacing, focus, depth of field.
NOT attributable: brightness, ambient, fill on the parts' upper surfaces, and
anything read off the establishing frame's upper half.
