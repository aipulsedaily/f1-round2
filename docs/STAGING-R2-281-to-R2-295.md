# Staged for the defect log's owner — R2-281 onwards

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner. My
block is **R2-281 to R2-295**. Paste or renumber as you see fit.

One job: **re-bake the glass-wall breach with corrected frame-member
thresholds**, derived rather than fitted, and find out whether the aperture
reads at 595 m when the frame is allowed to fail at the load its own fastener
fails at.

Artefacts

| | |
|---|---|
| `sim/frame_thresholds.py` | new — the derivation, stdlib-only, **outside Blender** so it can be checked without a 2 h 25 m bake |
| `sim/out/frame_thresholds.json` | its output, every input labelled DECLARED / PUBLISHED / JUDGEMENT |
| `sim/out/rebake_prediction.json` | **written before the bake was launched**, not merely before the render |
| `sim/framemotion.py` | new — asks whether the frame BROKE (joint separation), not whether it moved |
| `sim/shedpx.py` | new — beat 3's payoff in projected pixels, from the table, no render needed |
| `sim/render_r2281.sh` | the after-set at specs copied out of the broker's own job table for the R6 run |
| `sim/tmp/breach_full_r2281.{npz,json}` | the re-bake, 1,657 frames |
| `render/film14_breach_r6b.blend` | the ship candidate — `film14` + the re-baked breach + the east frame |
| `render/r2281/` | the closing run and beat 3, before and after, with the repeats that measure the noise floor |

---

## R2-283 — `build_breach_sim.py` has refused to bake since R2-197 added the outfield, and the first thing anybody re-baking hits is the gate

Before any of the intended work could start:

```
REFUSING TO BAKE: 3 bodies start inside other geometry, worst 0.2990 m
(SIM_Threshold into SIM_Outfield).
```

R2-197 added `SIM_Outfield`, a 2 km catch slab spanning z −0.60 … −0.001, and
its own comment says it *"sits 1 mm below the floor slabs' top so it can never
win a contact against them"*. The floor slabs run z −0.30 … 0.0. **So by
construction the outfield contains 299 mm of `SIM_FloorIn`, `SIM_FloorOut` and
`SIM_Threshold`**, and the penetration gate — which R2-197 had itself widened
from "shards only" to "every body" — raises `SystemExit` before every bake.

It went in **without a bake behind it**: the shipped table `breach_full_m1.npz`
registers **233** box colliders and this build registers **234**, and the extra
one is the outfield.

**And R2-197 was itself a fix.** It was the repair for the 70 bodies that ran
off the end of the static ground and hung motionless 154 m underground for the
last 1,813 frames of the take. So **the repair for one defect silently
disabled the entire pipeline it was repairing**, and nothing noticed, because
the only thing that would have noticed is a bake and nobody ran one. **A fix
that has never once been exercised is not a fix, it is a claim** — and this one
sat in the tree for hours reading as done. The two commits either side of it
touched the same file and neither could have baked either.

Whether the outfield actually *does* catch the 70 is still unmeasured here and
is not this block's to certify: what can be said is that `motion_report` now
reports `caught_by_the_outfield`, it read **0** in the null (nothing should
reach it with no car in the scene), and the production bake is the first run
that will exercise it at all.

The rule the gate is for is *"nothing may be ejected by its own initial
condition"*, and a PASSIVE body cannot be ejected — Bullet never integrates it.
Every defect this gate has ever caught was an ACTIVE body: 582 clamped shards
inside the sill, a mullion foot 88 mm inside it, a head 110 mm inside the head
beam. All of those are still refused. Static-into-static overlap is now
**reported with its worst offenders** and does not stop the bake, because a
catch slab that silently overlaps something else is exactly what R2-197 said it
did not want to be.

---

## R2-281 — the transom threshold, derived from the fastener: 260 → 8.8, and the shipped value was 29.5× the joint

`sim/frame_thresholds.py`. The unit conversion is R2-092's and is the whole
reason this is arithmetic rather than taste: Bullet compares
`breaking_threshold` against the impulse applied in **one substep**, and at
240 Hz × 8 substeps a threshold T is a sustained **T × 1920 N**.

**Declared by `wall_iface`**, and read out of the file rather than retyped —
the module refuses if the sentence changes:

| | |
|---|---|
| screw port SP1 takes | *"M6 self-tapper, 6.0 mm nominal, cuts its own thread; **40 mm minimum engagement**"* |
| port | 8.5 mm bore with a **5.0 mm open mouth** — a race, not a tapped hole |
| extrusion / fasteners | **6063-T6** / **A2-70 stainless** |
| screws | **2 per transom end**, counted at all 3 × 11 stations, 90 mm apart |

**Three failure modes, smallest governs:**

| mode | | |
|---|---|---|
| **screw shear** | 0.60 × 700 MPa × 20.12 mm² = 8 450 N × 2 | **16 901 N** |
| thread strip | 659.9 mm² (FED-STD-H28), × **80.0 %** because the race is open (5.0 mm mouth on an 8.5 mm bore = 72.1° of circumference missing), × 152 MPa × 2 | 160 463 N |
| bearing | 6.0 × 40.0 mm × 0.80 × 1.5 × 241 MPa × 2 | 138 785 N |

**Screw shear governs at 16.90 kN. T = 16 901 / 1920 = 8.80.**

The shipped **260 is 499 kN — 29.5×** — and more than twice
`THRESH_MULLION_BASE`, i.e. two self-tapping screws priced stronger than the
cast-in anchor studs in the slab.

The previous estimate of this joint was *"~15 kN, call it T ≈ 8"*, stated as
engineering judgement. **It was right to within 13 %.** What is new is that the
number now comes from the declared grade and the declared engagement, and that
the two modes which do **not** govern were computed rather than dismissed — the
open-race reduction in particular is the one that could have made the aluminium
govern instead, and it does not: 160 kN against 17 kN.

### What is judgement, stated so it can be argued with

* **The biggest single uncertainty is a factor of two, and it is in the
  declaration.** `transom_landings` gives one *pair* of screw heights per
  (line, mullion), and at an interior mullion **two** transoms land there. Per
  end, or shared? Taken as **per end**, and the interface argues for it: its own
  note requires a shear block to clear the isolator feet at |y| = 10.0–12.2 and
  32.2–34.4 mm, which describes a block twenty millimetres out to *one* side of
  the centreline, mirrored — a block per side, not one straddling the centre.
  **The other reading is T = 4.4, and that is the low point of the bracket this
  block bakes.** The bracket is not half-and-double for its own sake.
* **Ultimate, not design.** No partial factor. A sim must break a joint at the
  load that breaks it, not at the load a code lets an engineer rely on. With
  EN 1993-1-8's γ_M2 = 1.25 the same arithmetic gives T = 7.04.
* The shear plane passes through the **thread**, not a plain shank (a
  thread-cutting screw is threaded to the head). A plain shank would give
  23.75 kN, T = 12.4.
* No flute reduction: a thread-**cutting** screw's flutes are at the lead, not
  at the joint face. A 15 % allowance would give 14.37 kN, T = 7.5.
* The 160 kN strip mode is **higher than the two screws could deliver in
  tension** (28 kN). That is not a contradiction — it is the declared 40 mm
  minimum engagement doing what a minimum engagement is specified for, making
  the joint fastener-governed. It is quoted as a computed mode, not as a
  capacity anybody could reach.

So the derived value sits in a defensible band of **T = 7.0 … 12.4**, and **8.8
is what the declared numbers give with no allowance either way.**

---

## R2-282 — the head is a movement joint, and the one number I refused to derive

`CON_MUL*_HEAD` shipped as a FIXED constraint at `t_mullion_joint × 0.5` = 20 =
**38.4 kN**, across a joint `wall_iface` records as
`head_expansion_gap_m` — **0.0172 m at mullion 5, and a gap at every one of the
eleven stations, 10.2 … 20.5 mm.** What it holds up once the car has taken the
bottom quarter of mullion 5 is 4.7 m of extrusion plus half of six transom
stubs: **41.0 kg, 402 N. Ninety-six times.**

It is now a `GENERIC` constraint with **x and y locked and z and all three
rotations free** — a slider, which is what an expansion gap is — and it is the
**default**, so the pipeline's own gate now refuses a bake at the *old*
configuration rather than at the new one.

**Its breaking threshold is deliberately unchanged at 20.** The lateral
capacity of the head anchor is not declared anywhere in `wall_iface` — unlike
SP1, which declares its fastener, its grade and its engagement — so it cannot
be derived and will not be invented. Keeping it means **nothing that falls in
this bake can have been bought by weakening the head**: the only thing changed
about this joint is its *kind*, and that follows from a declared geometric fact.

`land_breach.sh`'s stage-0 gate pinned `transom == 260.0` as "the configuration
that was decided", so it would have **refused any bake that corrected this**.
It has been moved onto the derived set, and it now also checks the head model,
which is recorded in the report's `thresholds` block for the first time — a
bake whose head model is not recorded is a bake whose frame behaviour cannot be
attributed afterwards.

### The third survivor, found and NOT changed

R2-092's own comment derives the segment-to-segment joint at **T = 16** (a
75 × 160 6063-T6 extrusion failing in bending near 30 kN) and the file ships
**40 = 76.8 kN, 2.5× its own derivation.** That is the same class of error as
R2-281, an order of magnitude smaller. It is left alone on purpose: it is not
what holds the frame across the aperture — that joint *already breaks* in the
shipped bake, twice — and moving it in the same bake would put two independent
variables in one controlled experiment. **Logged, not fixed.**

---

## R2-284 — "did it move" is the wrong question; the right one is "did it come apart"

R2-267 is what happens when the frame's behaviour is read out of a statistic
that is 96 % glass. `sim/framemotion.py` measures **joint separation** —

```
    || (a(t) − b(t)) − (a(0) − b(0)) ||
```

— which is zero for a rigid pair however far the pair travels together, and is
therefore the measurement that does not care whether the wall fell over or was
pushed. Each transom end is matched to the mullion segment
`build_breach_sim._seg_at` actually bolted it to, by the same nearest-centre
rule.

**My first threshold was wrong and the shipped bake caught it.** At 20 mm —
reasoned from the collision margin — it reported **18 of 95 joints broken and
all six of mullion 5's transom ends broken**, in a bake whose transom
constraints are at 499 kN and cannot have broken. A Bullet FIXED constraint is
*soft*: 24 sequential-impulse iterations hold to tens of millimetres, not to
zero. The shipped table brackets it instead, and the bracket is wide open:

| | |
|---|---|
| largest separation on a joint that did **not** break | **0.0725 m** |
| smallest separation on a joint that **did** (`MUL05_S00→S01`) | **1.3605 m** |

a factor of nineteen with nothing in it. **0.25 m**, and every run prints the
whole distribution so the gap cannot close silently.

**Baseline on the shipped table: 2 joints broken of 95**, both inside mullion
5's lower column; **0 of 6 transom ends**; max transom body travel 96.9 mm.

---

## R2-285 — beat 3's payoff, priced before the job could cost it

`sim/shedpx.py` projects every replaced east-frame piece at a film frame from
the film table and `eastframe.plan()` alone — no render, no Blender — so
no-regression can be answered the moment a bake lands rather than after the
farm comes back. It reads the table through `resample.read_film` and poses it
through that module's own `expand()`, so it measures the **same reconstruction
the applier keys**, not a second implementation of it.

Baseline, shipped R6 table, **f0880**: `BF_MUL05_S00` **391.4 × 358.5 px** at
4.65 m, `BF_MUL05_S01` **396.4 × 269.3 px** at 4.70 m. The standing description
of the same two segments is 426 × 428 and 461 × 292; mine is an axis-aligned box
of the eight projected corners and reads about 9 % smaller, so it is a
*comparable* measure rather than the same one — and the comparison it exists for
is before-versus-after through one instrument.

---

## R2-286 — the measuring instrument was checked against the work it has to extend

Before measuring anything new, `sim/wallstats.py` was re-run on the **existing**
R6 pair. It reproduces the previous block's published numbers exactly:

| region | grid_contrast before → after | changed > 8/255 |
|---|---|---|
| WOUND_bridged | **0.03722 → 0.03675** | 1.8114 % |
| NB_left_bay3 | 0.03660 → 0.03697 | 1.5915 % |
| NB_right_bay6 | 0.06775 → 0.06954 | 0.8400 % |
| CTL_UNTOUCHED_bays789 | 0.05324 → 0.05310 | **0.0432 %** |
| CTL_UNTOUCHED_bays012 | 0.04369 → 0.04329 | **0.0000 %** |
| sky | — | 0.0000 % |

and the measured repeat floor at 1/255 runs **2.0 – 13.6 %** across these
regions, which is why the verdict is taken at 8/255. The two untouched
bay-groups are inherited unchanged as the negative control.

---

*(results sections follow once the bake lands)*

## R2-287 — the null holds, and its headline number is a maximum over 378 shards decided by one of them

**P1 of the committed prediction, and the first result in.** 480 frames,
`--wake-all --no-car`: every body awake at frame 1, no car in the scene, the
wall must stand on its own. Run at the derived thresholds and with the head as
a slider, against `sim/tmp/n1.npz` — **the same 480 frames at transom 260 with
the head FIXED**, which is the exact before-half — and against `n2`, the
mullion 15/50 config R2-093 identified as the one that *breaks* the null.

**The frame stands, and that is the claim P1 made:**

| | n1 — transom 260, head FIXED | n2 — mullion 15/50 | **new — transom 8.8, head slider** |
|---|---|---|---|
| max mullion-body sag | 0.175 mm | 0.273 mm | **0.341 mm** |
| max transom-body sag | 0.078 mm | 0.139 mm | **0.148 mm** |
| frame joints broken (of 95) | 0 | 0 | **0** |
| mullion 5 column travel | 0.001 m | 0.001 m | **0.001 m** |

A third of a millimetre, on a wall filmed at 12.96 px/m. The joint got 29.5×
softer and the frame's dead-load response roughly doubled, from 0.175 mm to
0.341 mm. **P1 predicted sub-millimetre and it is sub-millimetre.**

**And the glass did not move either — but the verdict line says it did.**
`NULL VERDICT` reports `worst_px_on_a_pane_that_stays`: **11.52 px** for n1 and
**360.31 px** for this bake, which reads like a large regression. It is one
shard.

| retained bays 2 and 7, 378 shards | n1 | n2 | **new** |
|---|---|---|---|
| median | 15.0 mm | 19.5 mm | 21.3 mm |
| **p95** | **27.7 mm** | **27.6 mm** | **27.6 mm** |
| p99 | 30.2 mm | 37.3 mm | 52.1 mm |
| over 100 mm | 0 | 2 | **1** |
| over 1 m | 0 | 0 | **0** |
| worst shard | 33 mm | **`GS_b07_00010` 510 mm** | **`GS_b07_00010` 918 mm** |

**The p95 is identical to three significant figures across all three
configurations.** The bulk of the retained glass is unchanged. The whole
difference in the headline is `GS_b07_00010` — **the same shard n2 lost at a
completely different threshold**, and the third-worst shard in n1 at 32 mm. It
is one marginal shard in bay 7 that this solver intermittently loses hold of,
it was doing it before the transom threshold was touched, and a **maximum over
378 shards is decided by whichever one of them it is.**

That is R2-274's lesson wearing different clothes — there the *mean* was the
wrong statistic for the wound, here the *max* is the wrong statistic for the
null — and R2-098's, which is the same mistake twice already. The null verdict
should carry a percentile beside its maximum, the way `null_verdict` already
carries `mobility` so that a null passing because nothing can move is visible.
**Logged, not fixed: it is not this block's file to change mid-bake.**

The seven shards R2-199 left open at bond 100 as "a different mechanism,
off camera, logged rather than chased" are almost certainly this population.

## R2-288 — the low bracket point is the alternative reading of the declaration, and it takes the frame apart past the demonstrator

`p_t4`: **T = 4.4**, head slider, 400 frames — impact (sim frame 145) plus
1.06 s. This is not "half, for the sake of it". **4.4 is what the derivation
gives if `transom_landings`' one pair of screws per (line, mullion) is shared
between the two transoms landing there rather than being two per end.** The
bracket's low end is the other reading of the declaration, so this run is the
answer to a question about the source data, not about a knob.

Measured with `framemotion`, against the shipped table **truncated to the same
400 frames**:

| | shipped, 260 / fixed | **p_t4, 4.4 / slider** |
|---|---|---|
| frame joints broken (of 95) | 2 | **23** |
| mullion 5's transom ends broken (of 6) | 0 | **6** |
| max transom-body travel | **0.097 m** | **12.222 m** |
| mullion 5 column (S02…S07) max travel | 0.16 m | **13.603 m** |
| lattice line z0 / z1 / z2 max travel | 0.097 / 0.073 / 0.043 m | **12.22 / 6.77 / 5.62 m** |

**Every one of mullion 5's eight segments leaves, all three transom lines leave
across both bays, and this goes past the demonstrator** — which only removed
mullion 5 above 1.55 m and six stubs.

**And it does not stop at the wound.** `TRN_z0_b02→MUL02_S00`,
`TRN_z0_b02→MUL03_S02` and `TRN_z0_b06→MUL07_S02` break too: transoms coming
off **bay 2 and bay 6**, and bay 2 is a *retained* bay whose glass stays put
(max shard travel 0.283 m, 0 of 195 over 1 m). At 4.4 the film would render an
undamaged bay of glass with its transom hanging off it.

**The glass tells the same story from the other side, and the retained bays
hold in both:**

| bay | role | shipped med / max @400f | p_t4 med / max @400f |
|---|---|---|---|
| 2 | **retained** | 0.005 / 0.048 m | 0.005 / **0.283** m — 0 of 195 over 1 m |
| 3 | destroyed | 0.012 / 0.028 m | 0.007 / 0.046 m |
| **4** | destroyed | 3.663 / **113.601** m | **14.717 / 18.534** m |
| **5** | destroyed | 1.876 / 19.093 m | **15.109 / 19.213** m |
| 6 | destroyed | 0.027 / 6.969 m | 0.013 / 3.849 m |
| 7 | **retained** | 0.025 / 0.196 m | 0.010 / **0.528** m — 0 of 183 over 1 m |

The cascade is confined to the two bays the car goes through. Note what else
changed: bay 4's **113.6 m outlier is gone** — p_t4's whole field maxes at
18.5 m and its distribution *tightens* (p95 15.16 against a median of 14.72).
A frame that lets go releases its glass as a coherent field instead of holding
some of it while the solver squeezes a few shards out at 110 m/s. That is the
opposite of what a "weaker means wilder" intuition predicts and it is
consistent with R2-199's finding that the blow-up is an over-determined
network shedding residual as velocity.

**So the bracket's low end is not obviously wrong physically — it is wrong
compositionally**, and that is a judgement about a picture, which is where the
brief says such calls belong.

## R2-289 — the frame comes apart across the WHOLE bracket, and it took a 29.5× error to stop it

`p_t17`: **T = 17.6, twice the derived value**, head slider, same 400 frames.
The point of a high bracket is to find where the result stops holding. **It
does not stop.**

| 400 frames, same seed, same everything else | shipped **260** | **4.4** (other reading) | **17.6** (2× derived) |
|---|---|---|---|
| frame joints broken (of 95) | **2** | 23 | **19** |
| mullion 5's transom ends broken (of 6) | **0** | 6 | **6** |
| max transom-body travel | **0.097 m** | 12.222 m | **15.639 m** |
| mullion 5 column max travel | 0.157 m | 13.603 m | **6.642 m** |
| lattice z0 / z1 / z2 max travel | 0.10 / 0.07 / 0.04 m | 12.2 / 6.8 / 5.6 m | **15.6 / 5.5 / 5.4 m** |
| damage outside bays 4–5 | — | **transoms off bays 2 and 6** | **none** |

**All six of mullion 5's transom ends break at 4.4 and at 17.6 alike.** The
derived 8.8 sits between two points that both take the frame apart, so the
answer does not depend on resolving the factor-of-two in the declaration, and
it does not depend on the derivation being right to better than a factor of two
in either direction.

**What was actually holding the frame together was the 29.5×.** The band this
job could defend on the arithmetic is T = 4.4 … 17.6 — a factor of four, from
the shared-screw reading at one end to double the derived value at the other —
and the whole of it breaks the frame. 260 is 15× above the top of that band.

**17.6 is also the better-behaved end**, which is not what a bracket usually
does: its damage is confined to bays 4 and 5, where 4.4 sheds transoms off two
bays that keep their glass. So the two ends of the bracket fail in *opposite*
directions — 4.4 by spreading, 17.6 not at all — and the derived value sits
between them.

**One thing this cannot yet attribute.** Both bracket points carry the head
slider as well as the corrected transom threshold, so "the ends broke" and "the
column fell" are not yet separable. The hypothesis the numbers suggest is that
they are two different mechanisms doing two different jobs — the transom
threshold decides whether the six ends let go (0 of 6 at 260, 6 of 6 at both
4.4 and 17.6), and the head model decides whether the column then has anywhere
to hang. `p_hfix` (8.8, head **fixed**) and `p_hsld` (260, head **slider**) are
baked to settle it; they are the two off-diagonal cells of the 2×2 and they are
queued behind the production bake.

## R2-290 — the corrected frame unmasks a kinematic bulldozer: 2,647 shards freeze mid-slide, 88 m downrange, across two-thirds of the closing frame

**The production re-bake at the derived thresholds landed clean and its
headline numbers are right.** 1,657 frames, `EXIT=0`, `land_breach` stage 0
and stage 4 both PASS:

| | shipped | **re-bake** |
|---|---|---|
| connected aperture | 2.15 × 6.00 m | **2.15 × 6.00 m** |
| bay 4 / bay 5 vacated | 96.7 / 95.4 % | **96.7 / 95.4 %** |
| shards gone | 2,962 | **2,923** |
| glass mass gone | 772.4 kg | **765.9 kg** |
| mullion 5 max displacement | 4.43 m, **2** of 8 segments gone | **89.79 m, ALL 8 gone** |
| transom max displacement | **0.089 m** | **69.83 m** |
| mullions 0–4, 6–10 displacement | 0.0000 m | **0.0000 m** — controls hold |

**P8 confirmed, P2 confirmed, and P3 — which I wrote as 50/50 and declined to
predict — resolves in favour of the column falling.** I was too conservative
and the reason is instructive: I reasoned statically, and the six transom ends
that would have held the column up are broken by the same transient that
breaks everything else.

**And the bake is not shippable, for a reason that is not the thresholds.**

The car proxy is `kinematic=True` — it is driven by the film's own authored
animation and *must* be, so it cannot be slowed by anything it hits. In the
shipped bake that never showed, because the frame was 29.5× too strong and
held the glass back from it. With the frame correctly weak, the car ploughs
the unrestrained field down the forecourt at its own speed:

| median destroyed-bay shard | shipped | re-bake |
|---|---|---|
| speed at sim f200 / f400 / f1000 / f1650 | 5.56 / 1.78 / 0.25 / **0.05** m/s | 12.95 / **18.88** / 14.15 / **7.33** m/s |
| final position | x = 16.5, **at rest by t = 2.9 s** | **x = 103.0, still sliding** |
| median travel | **3.77 m** | **88.17 m** |

It *accelerates* between f200 and f400 while lying on the ground at z = 0.02,
up to 18.88 m/s — and the car proxy's own parts never exceed 19.90 m/s
(R2-096). It is being pushed, and an infinitely massive bulldozer does not
stop pushing.

**The consequence is R2-197's defect at thirty-eight times the scale.** At the
table's last key **2,647 of 3,796 shards are still moving faster than 1 m/s
(median 6.995 m/s)**, and `apply_breach` extrapolates CONSTANT, so they hang
motionless for the remaining ~1,300 film frames of a take with zero cuts. The
camera is east of the wall, so 88 m of eastward travel moves the debris
*toward* it: the frozen field projects across **u 884…3465, v 1041…2067** of
the 4K closing frame — 2,581 × 1,026 px, two-thirds of the frame width — where
the shipped field occupies 476 × 1,040 px at the base of the wall and is at
rest (median 0.033 m/s, 77 shards over 1 m/s).

**This is not a threshold defect and correcting the thresholds did not create
it.** Both bakes are wrong about the debris; the shipped one is wrong in a way
that happens to look plausible, because an over-strong frame was doing the job
the car proxy's mass should have been doing. Fixing one exposed the other, and
that is the second time in this block (R2-283 is the first).

**It also sits between the camera and the wound**, so the closing frame from
this bake cannot be used to measure whether the aperture reads. That is what
R2-291 is for.

> **A diagnosis I got wrong, corrected here rather than quietly dropped.** The
> first 4K render of this scene died with `Out of memory in CUDA queue enqueue
> (integrator_shade_volume)` and I attributed it to the enlarged debris field
> blowing up the volume integrator's bounds. **That is refuted.** The
> atmosphere is built by `world/build_sky.py` as two fixed boxes at
> `SLAB_HALF = 40000.0` — ±40 km — independent of anything the sim does, so
> debris going from 20 m to 250 m is nothing against it; `sim/` creates no
> volume object at all; the identical OOM hit a different agent's unrelated
> scene in the same 21-minute window; and the same scene rendered fine at 256
> samples minutes later. The instance was failing, not the scene (R2-292). The
> geometry barely moved either: 3,845 → 3,856 objects, 278,864 → 278,910 tris.
> I state it because the wrong diagnosis was plausible, self-serving — it made
> my own defect look bigger — and would have been believed.

### What is NOT wrong with it

* the `--wake-all --no-car` null holds (R2-287);
* the two untouched bay-groups are untouched — mullions 0–4 and 6–10 at
  **0.0000 m**;
* `swap-scene`, the R2-098 check asked of the scene that actually renders,
  **PASSES** with 0 problems;
* the table-level `--swap` check FAILs at 375 uncovered shards — **and it fails
  on the shipped table too, at 301**, same 2,118-frame worst gap. Pre-existing,
  24 % larger, not introduced here.

## R2-291 — beat 3 does not regress, it gets substantially stronger, and my own numeric check said the opposite

The one thing this job was told not to trade away. **f0866, 1920 × 1080, 256
samples, all three builds at identical settings**, so the comparison needs no
caveat:

| | changed > 1/255 | **> 8/255** | > 32/255 | mean &#124;Δ&#124; | max |
|---|---|---|---|---|---|
| pre-R6 → R6 (the previous block's result) | 17.929 % | **2.548 %** | 0.535 % | 1.208/255 | 150/255 |
| **R6 → R2-281 re-bake** | 65.834 % | **27.950 %** | **9.186 %** | **10.398/255** | 201/255 |

The 2.548 % reproduces the previous block's published 2.54 % exactly — the
third time this session an inherited number has been reproduced before being
extended. **The re-bake moves eleven times as many pixels at 8/255 as R6 did**,
and seventeen times as many at 32/255.

`render/r2281/COMPARE_f0866_preR6_R6_REBAKE.png`, three panels:

* **pre-R6**: the car is through and the mullion runs straight and unbroken
  behind it. Round 1's static grid.
* **R6**: mullion 5's foot is torn out. Real, and subtle.
* **re-bake**: **a full-height aluminium member is torn out and tumbling
  diagonally across the upper frame**, the structure above the car is broken
  and displaced, and the wall is visibly *open* over the car rather than
  cracked. It is a different and much stronger image, and every member is still
  present — nothing was deleted to get it.

**And my own numeric no-regression check called this a regression.**
`sim/shedpx.py` reported `BF_MUL05_S00` shrinking 140,310 → 7,800 px and
`BF_MUL05_S01` 106,754 → 10,394 px at f0880, an 18× and 10× loss on precisely
the two segments R2-276 celebrated. That reading is *correct and irrelevant*:
those two segments are the ones the car sweeps downrange (R2-290), so they get
smaller because they leave, while `BF_MUL05_S07` grows 375,069 → 582,492 px and
twelve pieces exist that did not exist before, because the upper column the
shipped bake left hanging now comes down.

**A per-piece metric cannot see that the event got bigger when the pieces are
not the same pieces.** It flagged `regression=CHECK`, which is what it should
do, and then the picture had to decide — exactly the order the brief sets out.
**P7 holds**, but not for the reason I wrote: I predicted the same two segments
would be at least as large, and they are not.
