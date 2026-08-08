# STAGING R2-2761 .. R2-2820 — beat 1's pacing (#147) and the animation that has to answer to it (#29)

Agent `r2-2761-beat1`. Tasks #147 and #29, taken together because the second is
the first one's consequence.

The client's note, which is the last unaddressed one:

> *"the camera angle overall is just too slow, not fast high attention paced, i
> get sleepy 4 seconds in"*

---

## R2-2761 — THE FIRST THING I DID WAS REBUILD THE RIG, AND IT MOVED THE DEFECT

**`world/camera_rig_path.json` is four days stale and every pacing number taken
through it is a number about a camera that is no longer in the film.**

It is dated Aug 4 15:49; `docs/beat_sheet.json` is dated Aug 8 06:15. Run
`camera_tempo` against it and beat 5 reads `med move` **0.0075** — the *pre*-fix
doppler pass. The beat-5 framing promotion is not in it at all.

So the first measurement was a rig built from the promoted sheet
(`sha256 d8825d84…`), and the check that it is the right rig is that it
reproduces the published beat-5 number to four decimals:

```
5_lap   med move 0.1489      (R2-2178 published 0.1489)
```

**On that rig the census says something different from the brief that sent me
here, and it says it about a different 271 frames.**

| | brief's census (`D` @ 0.87, stale path) | this rig, `camera_tempo` @ 0.10 |
|---|---|---|
| longest flat run | 35.67 s, **f73-928**, spanning three beats | **11.29 s, f484-754**, inside `1_assembly` |
| starts at | 3.0 s | **20.1 s** |

**Both instruments point at beat 1. They do not point at the same frames, and the
frames they disagree about are the ones the complaint names.**

### Frame 96 is not flat. It is one of the busiest frames in the film

Four seconds in is frame 96. `G = 1.0` is this film's own 95th-percentile
gesture. Around frame 96:

```
f88 G=5.17   f96 G=0.65   f101 G=4.84   f103 G=7.55
```

That is the CI → halo_assembly presentation hop, and at **G = 7.5 it is seven
times the film's 95th-percentile gesture**. The complaint's timestamp lands on
the single liveliest moment in beat 1. Beat 1's flat runs, all of them:

| frames | length | |
|---|---|---|
| **f484-754** | **11.29 s** | **the payoff orbit** |
| f759-778 | 0.83 s | the seam bridge (pinned, not mine) |
| f3-15 | 0.54 s | the establishing hold (deliberate) |
| f163-169, f356-362, f213-218 | 0.29, 0.29, 0.25 s | inside the tour |
| six more | ≤ 0.12 s each | |

**I am not going to claim the complaint and the measurement name the same
frames, because on the current camera they do not.** What survives is the
direction: the film's longest flat stretch is in beat 1, it is 11.29 s, and it is
one identifiable shot.

### Why the two censuses disagree, stated so nobody has to re-derive it

The 35.67 s / f73-928 figure is not wrong arithmetic. It is a different
derivative (`D` over 0.5 s) at a threshold sitting at the **97th percentile of the
film's own data**, run against a camera path four days stale — and R2-2171 had
already shown that census is saturated, that "runs" in it are the gaps between
rare spikes rather than stretches of sameness, and that the only intervention
which clears its floor is a 20-degree snap every three seconds. **I am not
re-litigating it. I am reporting that a second, independently-derived instrument
run on the CURRENT camera puts the film's longest flat run at f484-754**, and
that this run is a single shot with a single identifiable cause, which the
35.67 s one never was (it spanned three beats).

### And the instrument warning does not reach me — checked, not assumed

`tools/lap_shotscale.py` keeps its own telemetry reader and clamps 11.03 s early,
which parked beat 6's car up to 230.7 m from where `anim/carpath` puts it and
produced two published findings that had to be retracted. **Nothing in my chain
imports it:**

```
tools/camera_tempo.py       0     tools/build_beatsheet.py        0
tools/beat1_part_framing.py 0     anim/build_camera_rig.py        0
```

`camera_tempo.measure_subject` reads the car through `anim/carpath.Car`, the
correct reader, and `beat1_part_framing.py` reads no telemetry at all — its
subjects are cluster boxes from `docs/explode_plan.json`. **The clamp cannot
reach a beat-1 number**, and now that is a check rather than a *should*.

---

## R2-2762 — WHAT THE PAYOFF ORBIT ACTUALLY IS: a 187-degree turntable in which only the background moves

f484-754 is the payoff orbit key for key — six keys at f465, 513, 562, 610, 658,
706 and the seam at 755, every one of them aiming at `look_at ≈ (0.0, 0, 0.9)`,
the car's centre. Projecting the car into the frame over those 271 frames:

| channel | over f484-754 | |
|---|---|---|
| horizontal offset `u` | **never leaves ±0.026 frame widths** (±0.051 half-frames) | in 11.29 seconds |
| vertical offset `v` | a **constant** −0.10 widths | it does not move either |
| subject travel | **0.0115 frame widths/s**, median | |
| subject size | 0.81 → 0.90 of the half-frame | ~constant |

**The camera swings 187 degrees of azimuth around the car and the car does not
move in the picture, and does not change size in the picture.** Only the
background moves.

That is R2-2161's beat-5 defect exactly — *"a camera doing 60 m/s alongside a car
doing 60 m/s has enormous kinetic numbers and a dead still picture, and that is
exactly the shot a client falls asleep in"* — relocated to beat 1. Beat 5 was
fixed by moving **where the subject sits**, not by moving faster. So the claim
here is stated in the same unit and judged by the same gate.

### And this is why beat 1's flat run survived four previous passes

R2-2171 and R2-2173 swept every beat-1 lever and correctly concluded there was
nothing left: `BEAT1_ORBIT_TEMPO_AMP` is at its ceiling, the tour has 0.05 s of
slack in 17.345 s, the establishing hold moves less than a second, and aim
modulation needs a 20-degree snap every three seconds. **Every one of those is a
lever on the camera's MOTION.** The channel that was never swept is the one the
viewer actually sees, and it had never been measured on this beat.

---

## R2-2763 — THE FRAMING LEVER, AND THE MEASUREMENT THAT SAYS IT IS NEARLY CLOSED

Beat 5 had 0.92 of margin and used 0.754 of it. **The payoff orbit does not have
that.** The car's own projected box, in half-frames (the aim gate's unit, which
fails at 0.92), with the offset at zero:

| key | f465 | f513 | f562 | f610 | f658 | f706 | f755 |
|---|---|---|---|---|---|---|---|
| car `hu` | 0.435 | 0.812 | **0.897** | **0.898** | 0.830 | 0.640 | **0.874** |

**The car already reaches 0.898 before anything is asked of it.** Three of the
seven keys are past a 0.86 safe edge with the shot as shipped. That is R2-842's
finding restated — the radius dip was cut from 1.00 m to 0.35 m precisely because
this shot lives against its fill limit — and it means the horizontal framing
headroom of the payoff orbit is between **−0.04 and +0.05**, not beat 5's 0.75.

**A near-full-frame subject cannot be slid around the frame.** Saying so is more
useful than authoring an offset the clamp then eats, and the clamp does eat it:
at amp 0.34 with no other change, four of five keys resolve to ≤ 0.05.

### So the clamp was built against the car's BOX, not a bounding sphere

`author_beats2_5._frame_offset_world` clamps against `SUBJ_RADIUS_M = 3.06`, half
the car box's diagonal — correct and cheap across beat 5's 1.6 m → 195 m range.
At the orbit's 7.5 m it says the car's angular radius is 0.85 half-frames in
**both** axes and clamps every offset to zero. The car is 5.7 m long and 1.0 m
tall: it fills the frame horizontally and takes about a fifth of it vertically. A
sphere cannot express that. `tools/build_beatsheet.py::_car_screen_half_extent`
projects the eight corners of the real box instead and gives each axis its own
limit — and it reads that box from `world/world_contract.py`, so **the framing
clamp and the clearance floor are looking at the same car.**

---

## R2-2764 — THE CHANNEL THAT WAS NOT SPENT: scale

Over the orbit the radius runs 7.49 → 7.85 m (+5 %) while the lens runs
35.2 → 40.0 mm (+14 %). **The two very nearly cancel**, which is why the car
holds 0.81-0.90 of the half-frame for the whole 11.29 s. Position constant, size
constant, speed constant: three flat channels at once, which is why no single
lever moved it.

`BEAT1_ORBIT_LENS_DIP_MM` widens the lens through mid-arc and lets it back onto
the seam's 40 mm. It buys three things and **moves no camera**:

* the car **changes size** in frame — the loom channel, which is a thing a viewer
  sees;
* the room opens up around the car at the moment the shot is about the car being
  whole — that is the payoff, not a compromise;
* `hu` falls, which is what finally gives the framing lever something to use.

`sin(pi*e)**2`, not `sin(pi*e)`: the squared window has zero **derivative** at
both ends, so the station's lens and the seam's 40 mm are untouched in value and
in rate. R2-842's *"the lens is C1 there either way"* survives it; a plain sine
would leave the seam C0, and a velocity step in any channel is a cut (R2-838).

The override `B1_ORBIT_LENS_DIP` exists so the null is reproducible and the value
is swept rather than guessed, and it is **bounded by a check that fires**:

```
$ B1_ORBIT_LENS_DIP=25 .venv/bin/python tools/build_beatsheet.py
>> R2-2761: the orbit's lens dip (25.00 mm) takes key 2/6 to 14.89 mm. Beat 1's
   widest declared lens is the 18 mm establishing frame; a payoff orbit wider
   than the establishing shot is not the move this is.
```

### A defect this change would have introduced, caught before it shipped

`focus_distance_m` on the orbit keys is `dist(world, look_at)`. The moment the
aim point is deliberately off the car, **that stops being the distance to the
subject** — at the widest offset it is 0.9 m long, which on a 36 mm lens at f/3
would have pulled focus off the thing the shot exists to show. **A framing change
that silently defocuses the subject is not a framing change.** Focus is now
measured to the *unoffset* aim point, which is the car.

---

## R2-2765 — THE RESULT, MEASURED ON A BUILT RIG

Shipped configuration: `BEAT1_ORBIT_LENS_DIP_MM = 7.0`,
`BEAT1_ORBIT_FRAME_AMP = 0.34`, `BEAT1_ORBIT_FRAME_CYCLES = 1.0`,
`BEAT1_CLOSEOUT_KEYS = 6` (unchanged).

### The census

| | before | after |
|---|---|---|
| **the film's longest flat run** | **11.29 s, f484-754** | **5.50 s, f620-751** |
| second longest | 1.29 s (`3_breach`) | 5.38 s, f482-610 (the other half) |
| `1_assembly` med G | 0.1494 | 0.1473 |

**The 11.29-second run is broken in two by a gesture at f611-618** — the moment
the lens is at its widest and the car is at its smallest. The film's longest flat
stretch is **51 % shorter**.

### The picture, over the payoff orbit (f465-792) — the channel the client feels

| | before | after | |
|---|---|---|---|
| horizontal frame-offset span | 0.082 half-frames | **0.264** | **3.2x** |
| subject travel, median | 0.0120 widths/s | **0.0239** | **2.0x** |
| loom, median | 0.0139 | **0.0244** | 1.8x |
| subject size span | 0.156 | **0.234** | 1.5x |
| on screen | 100 % | 100 % | unchanged |

**Stated against my own interest: this is a 2-3x change, and beat 5's was
13.7x.** The reason is measured and is in R2-2763 — beat 5 was a 26 m flyby with
0.92 of margin and used 0.754 of it; the payoff orbit is a full-frame shot whose
subject already reaches 0.898. **I did not get beat 5's number and the shot could
not have given it to me.**

### The largest remaining flat run, and where it is

**Both of the two longest runs in the film are still in beat 1**, at 5.50 s
(f620-751) and 5.38 s (f482-610) — the two halves of the orbit either side of the
lens dip. The next is 1.29 s in `3_breach`, and beat 5's longest is 0.92 s.

**It does not land back in beat 5**, so the "the film is uniformly slow" reading
is not what this measurement supports. What it supports is narrower and more
useful: **the payoff orbit is the slowest shot in the film, it is now half as
slow as it was, and it is still the slowest shot in the film.** The remaining
5.5 s is one continuous 90-degree arc of a full-frame car, and the levers that
would halve it again are in `world/` — the orbit's radius, or the seat schedule
that fixes when the orbit can start.

### The beat 1 -> 2 boundary, which I was told to protect

`continuity_gate --campath`, before and after, are the same report:

```
before:  PASS — 0 FAIL, 5 advisory   C2_path_kink f754 z=30.8, f755 z=9.5
after:   PASS — 0 FAIL, 5 advisory   C2_path_kink f754 z=30.8, f755 z=9.5
```

**The seam's z-scores are unchanged to one decimal**, because the seam key is
emitted verbatim, the framing window `sin(pi*u)` is exactly zero there, and the
lens dip's `sin(pi*e)**2` has zero value *and* zero derivative there. The
boundary was sound before and it is the same boundary now.

---

## R2-2766 — CONFINEMENT, MEASURED

**Null control first.** `B1_ORBIT_FRAME=0 B1_ORBIT_LENS_DIP=0` against the
promoted sheet, walked key by key:

```
TOTAL DIFFS (promoted vs NULL rebuild): 52 — every one of them inside /beat1
```

**Zero changes to beats 2, 3, 4, 5 or 6.** Inside beat 1 the only numeric changes
are the 20 `min_clearance_m` figures and `min_clearance_to_car_m`, each moving
2-3 mm — that is the corrected car box (R2-2767) and nothing else. No camera
key's `world`, `look_at`, `lens_mm` or `focus_distance_m` moved at all.

**And on the shipped sheet, walked the same way: 0 diffs outside `/beat1`.**

### On the BUILT path, which is the measurement that counts

The sheet is an input; the rig is what gets rendered. Per-frame, shipped path
against the baseline path:

| | beat 1 (f1-792) | beats 2-6 (f793-2978) |
|---|---|---|
| max position change | **0.000000 m** | **0.000000 m** |
| max lens change | 7.027 mm @f613 | **0.0000 mm** |
| max aim change | 4.526 deg @f686 | 0.192 deg @f1157 |

**The camera flies a bit-identical path through the entire film.** Position is
not "within noise", it is exactly zero at all 2,978 frames — which is what makes
the clearance result below a construction rather than a re-measurement.

### The 0.19 deg in beats 2-6 is the rig build's own noise, and here is the control

Position and lens are *exactly* zero there, so a 0.19 deg rotation difference had
to be explained rather than waved through. Pairwise, over f793-2978:

| pair | max aim difference |
|---|---|
| baseline vs shipped | 0.1917 deg @f1157 |
| baseline vs the 8-key variant | 0.1843 deg @f1203 |
| **shipped vs the 8-key variant** | **0.1803 deg @f966** |

**The last row is the control.** Those two sheets have *byte-identical* beat-2-to-6
blocks and *bit-identical* camera positions, and their rotations still differ by
0.18 deg. **So ~0.19 deg is the floor below which no confinement claim on this
rig can be made** — the same shape as the 2-6 grey level cross-card floor this
project already respects for Cycles, now measured for the rig build. My beats-2-6
delta sits *at* that floor, not above it.

### THE CONTROL WAS RUN, AND IT SETTLES IT

`docs/beat_sheet.json` — one sheet, unchanged, no variables — built **twice**,
from a snapshot taken before the regeneration so it could not be invalidated by
it:

| same sheet, two builds | max position | max lens | **max aim** |
|---|---|---|---|
| beat 1 (f1-792) | 0.000000 m | 0.0000 mm | **0.190539 deg** @f736 |
| beats 2-6 (f793-2978) | 0.000000 m | 0.0000 mm | **0.203411 deg** @f2512 |

**Two identical inputs produce rotations differing by 0.20 deg, with position and
lens bit-identical.** `anim/build_camera_rig.py`'s rotation solve is
nondeterministic across builds at about two tenths of a degree, everywhere in the
film, and nothing on this project had measured that.

Against it:

| | beats 2-6 max aim delta |
|---|---|
| **the control — same sheet, twice** | **0.203411 deg** |
| my change | 0.191711 deg |

**My residual is BELOW the control.** The paragraph stands, and it now stands on
a run control rather than on an inference from two sheets that differed in beat 1.

**So ~0.20 deg is the floor below which no confinement claim on this rig can be
made at all** — the same discipline this project already applies to Cycles' 2-6
grey levels across cards, now measured for the rig build. Any future "beats 2-6
are unchanged" claim quoting a rotation delta under 0.20 deg is quoting noise,
including mine: what carries my confinement claim is **position exactly zero at
all 2,978 frames and lens exactly zero outside beat 1**, which are channels this
control shows to be perfectly reproducible.

I would have preferred to disprove myself; the control says otherwise, and the
useful output is the floor rather than the verdict.

---

## R2-2767 — THE NINTH COPY OF THE CAR BOX, AND IT WAS OPTIMISTIC IN TWO AXES

`tools/build_beatsheet.py:1954` hand-typed the car's dimensions. Against
`world/world_contract.py`:

| axis | authored | contract | delta | direction |
|---|---|---|---|---|
| Y half-width | 1.0000 | **1.0025** | −2.5 mm/side | **smaller than the car — unsafe** |
| Z top | 1.330 | **1.332** | −2.0 mm | **smaller than the car — unsafe** |
| X extent | 5.720 | 5.698 | +22.0 mm | longer — conservative |

**A box smaller than the car hands the clearance check optimism nobody
declared**, in the one file that decides how close beat 1's camera may fly. Y and
Z are now imported. **X is deliberately NOT imported**: the contract states the
car's *length* but not where the origin sits along it, so the authored split is
kept and *asserted* to be no shorter than `CAR_BODY_LEN_M`. Importing two axes
and inventing the third would be worse than importing two.

### Clearance on the correct box — the answer the brief asked for

Per-frame, over the rebuilt path, f1-792:

| box | worst clearance | frame | floor | verdict |
|---|---|---|---|---|
| as shipped | 1.0736 m | f273 | 0.30 | PASS |
| **correct dims** | **1.0716 m** | f273 | 0.30 | **PASS — 3.6x the floor** |

**The divergence costs 2.0 mm and the check was never close.** This independently
reproduces R2-2177's figures to four decimals from a separately built rig, which
is worth more than either measurement alone.

**And the re-pace cannot change it, by construction rather than by luck**: the
framing offset moves only `look_at` and the lens dip moves only `lens_mm`. Every
key's `world` is bit-identical, so the camera flies exactly the path it flew
before. **A framing fix cannot fly the camera into the car.**

### The provenance line was hollow and is gone

`measured_on: world/beat1_anim.blend` sat beside the hardcoded literals.
`tools/build_beatsheet.py` has no `bpy` import and never opens a blend: it was a
record of a measurement this code cannot perform or reproduce. It now states
where each axis comes from, which one is authored rather than imported, and
`"not_measured_here": "this file never opens a .blend"`.

---

## R2-2768 — #29: WHAT BEAT 1'S ASSEMBLY ANIMATION NEEDED

### The instrument, because none of the existing ones answer this question

`tools/beat1_part_framing.py`. Every existing tool answers a neighbouring
question: `beat1_present_gate.py` sees only the 15 presentation keys and only at
each cluster's *exploded* position; `beat1_true_extent.py` tracks the assembled
car and says itself it is only authoritative after the corners seat;
`screen_presence.py` needs a Blender point cloud and **assumes static geometry**,
which is the one thing 616 flying parts are not; `r2401_part_mask.py` is true
per-part pixels but it renders.

This one takes the moving cluster boxes and the per-frame camera and reports
where each cluster sits in the frame, every frame it is alive, in half-frames.

**It states what it is a model of.** The flight is Blender F-curve keys and this
file does not open the blend, so the curve *between* them is a model of an
AUTO_CLAMPED bezier, not the bezier. Two models are run — `smooth` and `linear`,
which bracket the real curve — and **any verdict that differs between them is
reported UNRESOLVED rather than settled.** The ±4.5° flight spin can push a
corner outside a translated box, which is a bias toward calling something
on-screen, so the box is inflated by the arc a point at its own radius sweeps.

`--selftest` has a negative control (a path against itself → 0 changes) and two
positive ones (a camera turned 180° → everything `off`; a 16 m box at 10 m →
never `inside`). All three fire.

### What it found — a real, small, bounded cost, and it is a decision not a footnote

Baseline against the offset camera, both flight models:

```
RW           1 frame   f479-482    off  -> edge     (better: it was off-frame)
CORNER_RL    2 frames  f516-518    edge -> inside   (better)
CORNER_RR    4-9 frames f491-499   inside -> edge   (WORSE)
>> STAGE RESULT: PART_FRAMING_REGRESSION  {'smooth': 4, 'linear': 9}
```

**Nothing goes `off`. One cluster, CORNER_RR, is edge-clipped for 4-9 frames of
its 49-frame flight** — the two flight models bracket it at 4 and 9, so the real
figure is between them and I am not going to pick one.

That is the honest price: **a 41-part wheel corner is clipped by the frame edge
for roughly a fifth of a second while it flies in, in exchange for breaking the
film's longest flat run.** It is not free and it should not be reported as free.
It is also recoverable without touching the camera — CORNER_RR's own
`explode_offset` or its 8-frame stagger would move it — and that is a change to
`world/`, which is the rebuild #29 already needs for a different reason.

### The desync is real, it is not the explode plan, and the rebuild already exists

**The explode plan itself has not changed.** Re-deriving `tools/explode_plan.py`
against `docs/inventory_iter.json` reproduces `docs/explode_plan.json` exactly —
all 15 `explode_offset` vectors, the same seat order, the same 28-pass solve.

What beat 1's animation actually predates is **R2-831's seat re-pace**,
`BEAT1_SEAT_START_FRAC/SPAN_FRAC` 0.42/0.50 → 0.30/0.38:

| | `world/beat1_anim_anim.json` (shipped) | `docs/beat_sheet.json` (current) |
|---|---|---|
| MB | f333 | f238 |
| CORNER_* | **f696** | **f513** |

**All 15 clusters are 60-180 frames adrift**, and `tools/build_beatsheet.py`
already prints `!! PART/CAMERA DESYNC … 15 of 15 clusters … REBUILD REQUIRED`.

**The rebuild exists and nobody promoted it.** `world/R2829_beat1_anim.blend` and
`world/R2829_beat1_anim_anim.json` (2026-08-07 03:50) seat MB f238 and the
corners f513 / last land f521 — **exactly the current sheet, on all 15
clusters.** So #29's "the animation predates the camera fix" is true of the
*promoted* artefact and already false of one sitting beside it. `beat1_part_framing`
therefore defaults `--anim` to the R2829 sidecar and says why, rather than
silently judging the new camera against the old pacing.

---

## R2-2769 — THE LEASE I DID NOT TAKE, AND WHY REFUSING IT COST NOTHING

When I reached for the sheet it was held:

```
$ R2_AGENT=r2-2761-beat1 tools/gitguard.py claim docs/beat_sheet.json
CLASH    docs/beat_sheet.json  held by r2-2161-pacing (agent, via docs/beat_sheet.json, 9.4 h old)
>> STAGE RESULT: FAIL (0 claimed, 1 clashes)
```

9.4 h against a 24 h TTL, so LIVE, and `gitguard` is explicit that **no named
owner is ever retirable, at any age, by any flag**. The owner's work
(R2-2161..R2-2178) was committed and it *looked* finished — but **"it looks
finished" is not a release**, and a peer cannot grant permission any more than my
own reading of their git log can. So I stopped, kept the sheet as a candidate,
and surfaced it.

**The coordinator had already released that lease** as part of retiring nine
belonging to finished agents; my information was simply out of date. Re-checked
and claimed cleanly:

```
CLAIMED  docs/beat_sheet.json
>> STAGE RESULT: OK (1 claimed, 0 clashes)
```

**Refusing to take it cost nothing**, and that is the point worth recording:
every number in this document was measured on a candidate sheet that the
generator reproduces byte-for-byte on demand, so waiting for the real answer was
free. The regenerated in-place sheet is **byte-identical to the candidate every
measurement here was taken on** — checked, not assumed:

```
docs/beat_sheet.json  vs  the measured arm:  IDENTICAL
sha256  d8825d84...  ->  1abee787a8044f35abd2cf453a8c6526d0a6be54ca287a10804c7457ff9f79bd
```

And the hazard I was warned about, re-checked on both sides of the regeneration:

| | before regenerating | after regenerating |
|---|---|---|
| `frame_u` worktree / HEAD | 47 / 47 | **47 / 47** |
| `frame_v` worktree / HEAD | 47 / 47 | **47 / 47** |
| `_frame_offset_world` worktree / HEAD | 2 / 2 | **2 / 2** |

**Beat 5 was not reverted**, and the zero-diff `author_beats2_5` re-run in
R2-2766 is the positive evidence for that rather than the absence of evidence
against it.

### THE GUARD'S THREAT MODEL IS FILE-GRANULAR AND THE HAZARD IS HUNK-GRANULAR

`tools/build_beatsheet.py` **was already dirty when I claimed it**, and the guard
did not and could not tell me. Splitting the diff by hunk:

```
hunks that are mine        12   beat 1's re-pace
hunks that are NOT mine     2   R2-1701's beat-6 closing-lens work
                                (CLOSING_LENS_HOLD_START/END_MM at @@ -286,
                                 and the "why" string in closing_lens_push())
```

`claim` reported `OK (1 claimed, 0 clashes)` and handed me the path. **That is
the guard working exactly as designed, and it is not enough**, because a lease
protects a PATH and this is two agents' work inside one path. `git add` on a
clean-of-clashes file can still sweep somebody else's uncommitted work — which is
R2-226 and R2-234 arriving through the one door the mechanism does not cover.

**This is the same shape as the other guard hole found tonight**: committing a
derived artefact sweeps its generator's uncommitted state in through the output,
where the index guard cannot look. Stated generally, because both instances are
the same sentence:

> **The guard's threat model is FILE-GRANULAR. The hazard is HUNK-GRANULAR, and
> it is also GRAPH-GRANULAR — a path can be free of clashes and still be carrying
> another agent's work, either inside the file or upstream of it.**

`>> STAGE RESULT: OK (0 violations)` is a statement about *paths staged*, not
about *work authored*. It cannot be read as the latter, and this pass read it as
the latter once before catching itself.

### AND CARRYING THEM REPAIRS A LIVE REPRODUCIBILITY DEFECT — hazard 1's exact shape, in the other generator

This turned out to be much more than salvage. **HEAD cannot reproduce its own
beat sheet**, and R2-1701's two uncommitted hunks are the reason. Measured by
stashing my work, regenerating from HEAD alone, and reading beat 6 back:

```
HEAD's sheet carries      closing lens 55.0 -> 130.0 mm
HEAD's generator produces closing lens 40.0 ->  74.0 mm
->  HEAD CANNOT REPRODUCE ITS OWN SHEET
```

**The promoted sheet was generated by a dirty working tree**, and the beat-6
closing lens push in it exists *only* in an uncommitted file. That is the
identical hazard I was briefed on for beat 5 — *"regenerating anywhere that
resolves it from HEAD silently reverts it, and every gate still passes green"* —
sitting unnoticed in `tools/build_beatsheet.py` for beat 6 the entire time. A
fresh clone, a worktree, or one `git checkout tools/` would have quietly walked
beat 6's ending lens from 130 mm back to 74 mm, and **no gate would have said a
word, because both are legal lenses.**

**So committing R2-1701's hunks is not a favour to a departed agent. It closes
the second instance of the defect this whole block was warned about**, and it is
the reason the manifest's *"landed in source, in no film blend"* line was true:
the work was in source, and source was never committed.

Checked after the fact, on the committed pair: the generator regenerates
`docs/beat_sheet.json` **byte-identically**, and `author_beats2_5.py` re-run over
it produces **zero diffs**. HEAD reproduces HEAD now.

### What I did about it: carried, with attribution, rather than swept or dropped

The coordinator's ruling is that R2-1701's two hunks are **a wanted manifest
item** — `docs/NEXT-REBUILD.md` lists *"Beat-6 ending re-key — lens f2978
73.997 -> 129.993 mm"* under **landed in source, in no film blend**, and
`closing_lens_push(beat6)` is exactly that. Its author is finished and the work is
uncommitted, **so the real choice was never "sweep it or leave it" — it was
"commit it or lose it" to the next stray `git checkout`.**

So it is committed, and **both changes are named in the commit message**: mine as
beat 1's re-pace, those two hunks as R2-1701's beat-6 closing lens push, inherited
from a finished agent and carried deliberately. **Attribution in the message is
what makes this landing rather than stealing**, and it is the only part of this
that a file-granular guard can never supply.

### What the next agent should pick up

1. **Promote the sheet.** Regenerate with `.venv/bin/python tools/build_beatsheet.py`
   once the lease clears, and commit it *with* `tools/build_beatsheet.py` in one
   commit — **after** separating R2-1701's two beat-6 hunks, which belong to
   whoever wrote them and not to this ticket. Verify `frame_u`/`frame_v`/`_frame_offset_world` read 47/47/2 in the
   worktree **and at HEAD** before and after — they do today, and `3ec8b6a` is
   why.
2. **The same-sheet rebuild control** (R2-2766). It was queued and the build lock
   was held by other agents for the rest of my window. If it returns a
   beats-2-6 aim delta below 0.18 deg, my "0.19 deg is the rig's noise floor"
   paragraph is wrong and the leak is mine.
3. **`world/R2829_beat1_anim.blend` is the artefact #29 actually needs**, and it
   already exists and already agrees with the sheet on all 15 clusters. Promoting
   it is a `world/` decision, not a camera one.
4. **CORNER_RR's 4-9 clipped frames** (R2-2768) are recoverable in the explode
   plan without touching the camera, and that is the same rebuild as (3).
5. **No render was spent.** Every number here is geometric, off built rig paths.
   The $24.82 is untouched and no broker was rented. The photographic
   confirmation beat 5 got in `watch/BEFORE_/AFTER_beat5_doppler_4s.mp4` has no
   equivalent here yet, and **until it does, "the car now travels across the
   frame" is a geometric claim and not a photographic one** — which is exactly
   the caveat R2-2175 attached to the beat-5 finding before its A/B was rendered.
