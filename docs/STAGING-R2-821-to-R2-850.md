# STAGING R2-821 to R2-850 — beat 1 pacing and shot scale

Owner: beat-1 pacing (camera position, rotation, lens, timing).
Focus distance and f-stop are NOT touched here — another agent owns them.

Baseline watched: `/home/zany/vast-render/out/seq/r2beat1/` (792 frames, 720p),
encoded to `/home/zany/f1-round2/watch/BEFORE_beat1_33s.mp4`.
Camera measured: `/home/zany/f1-round2/world/camera_rig_path.json`
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
  **55-75 GPU-hours, $25-45** against a $73.33 balance. **Not to be spent until a
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
