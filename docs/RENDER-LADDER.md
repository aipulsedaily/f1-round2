# The render ladder — never go straight to 4K

The user's instruction, and it is correct:

> "once were done mastering the models etc. we cant go straight to a 4k video we
>  need hundres of 1080p 720p video stripped into frames pixel peeped and make
>  sure EVERYTHING is flawless"

## Why this is not just caution — it is the only way to find half the defects

**Stills and sequences catch DIFFERENT defect classes, and neither substitutes for
the other.**

A 4K still can show you carbon weave, a bevel, a decal edge, a material that
reads as plastic. It can never show you:

| defect | only visible across frames |
|---|---|
| flicker / fireflies resolving differently per frame | yes |
| popping shadows, LOD swaps | yes |
| sim jitter, a shard that pops or interpenetrates for 3 frames | yes |
| camera-path kinks, an easing discontinuity | yes |
| speed-ramp stutter, stepped time | yes |
| motion blur reading wrong during a ramp | yes |
| batch seams where two machines rendered adjacent ranges | yes |
| pacing — a beat that is 2 s too long | yes |

And the reason 4K cannot be the iteration medium is arithmetic. **The arithmetic
below replaces an earlier figure of "49.8 GPU-hours and $15.44, 60.2 s/frame",
which was wrong by roughly 8x — corrected 2026-08-02.**

### Why the old number was wrong, because the mistake is instructive

Two figures were in circulation, and BOTH were real measurements on this 5090 at
3840x2160 / 512 samples. They disagreed by 8.5x because **they are different scenes**:

| scene | s/frame | n | what it is |
|---|---|---|---|
| `beat1_anim.blend` | **60.2** | 1 | the showroom interior — where the old ladder figure came from |
| `render3.blend` | **510.5** | 2 | the full world assembly, 13.2 B traced triangles |

Neither is the film. **The film is one continuous take that begins inside the
showroom and ends out in the world**, so its per-frame cost varies by 8.5x across
its own length. Extrapolating either scene flat across 2,978 frames is the same
error in two directions — the same unrepresentative-sample failure that produced
the remote-exec A/B reject on a below-median CPU box.

Also in the broker's history, for context: `assembly_render.blend` 195.0 s (n=10),
`render2.blend` 227.0 s (n=6), `ter.blend` 122.9 s (n=15). The world-scene family
runs 195–510 s; `render3.blend` is the newest and heaviest.

### The real 4K master budget, weighted per beat

| beat | frames | basis | s/frame | render h |
|---|---|---|---|---|
| 1_assembly | 792 | showroom | 60.2 | 13.2 |
| 2_launch | 72 | showroom | 60.2 | 1.2 |
| 3_breach | 192 | showroom + sim | 60.2 | 3.2 |
| 4_transit | 134 | world | 510.5 | 19.0 |
| 5_lap | **1,524** | world | 510.5 | **216.1** |
| 6_ending | 264 | world | 510.5 | 37.4 |
| | **2,978** | | | **290.2** |

Plus 25.6 h of non-render overhead (31 s/frame) and ~6.2 h of cold starts:

> **322 h = 13.4 days on one 5090, $131 at $0.4083/hr.**

For comparison: assuming the world rate flat gives 18.9 d / $185; assuming the
showroom rate flat gives 3.4 d / $33. The truth is neither.

**Treat 13.4 days / $131 as a FLOOR, not an estimate.** Five things push it up and
none push it down:
- n=1 and n=2. These are tiny samples.
- **Beat 3's destruction sim is unmeasured.** Rigid-body destruction rebuilds the
  BVH every frame, so `persistent_data` buys nothing. It is priced here at the
  showroom rate, which is certainly too low.
- **Beat 6 is the closing WIDE** — it sees more of the world than any other shot,
  and is priced at the same rate as the lap.
- **Wave 2 adds ~407 more item types.** `render3.blend` is today's world, not the
  shipping one.
- The 512-sample basis is not a settled delivery spec. 640 samples was measured at
  roughly +25 %.

### THE DISK BLOCKER WAS NEVER REAL — the 34.3 MB/frame figure is wrong

**MEASURED 2026-08-03, on actual 4K frames on disk:**

```
render/breach_f9/f9_3840_f0866.png    7.22 MB
render/breach_f9/f9_3840_f1030.png    7.81 MB
render/breach_f9/f9_1920_f0866.png    1.96 MB
```

**~7.5 MB/frame at 4K, not 34.3.** The 34.3 figure appears nowhere in this repo as a
frame size; the only `34.3` in the docs is `5.0 x 34.3 mm` from an unrelated defect
measurement. It looks transcribed from something else, and **every disk conclusion
drawn from it was wrong by 4.6x** — including an earlier rewrite of this very section,
which re-published it without measuring.

| | corrected |
|---|---|
| 4K master, 2,978 frames | **~22 GB** (was claimed 102.1 GB) |
| 1080p full pass | ~5.8 GB |
| 720p full pass | under 3 GB |
| ProRes 422 HQ, 124.08 s | ~11 GB |
| H.265 delivery | **under 1 GB** |
| **whole delivery** | **~34 GB** |

**There is no disk blocker and there never was.** The prediction that a 4K master would
die at about frame 2,274 was an artefact of the bad constant. With 136 GB free the master
fits five times over, rehearsal passes cost single-digit GB, and **nothing needs deleting.**

**What does occupy real space is the working set, and that is fine:** 49 GB of assemblies
and 55 GB of film scenes, growing ~8 GB per world+film iteration and ~4.65 GB per breach
apply. That is a burn rate to watch, not a blocker — and it is *build* artefacts, not
deliverables.

**The lesson is the one this project keeps re-learning:** a per-frame size is one `ls`
away, and it was quoted for weeks instead. **Measure the artefact.**

The *instance* disk was never the problem: `collect` deletes each frame the moment its
fetch verifies, and the scene cache is now derived from measured room (23.0 GB on a
32.2 GB box) rather than a constant sized for a 16 GB disk that never arrived.

## THE DELIVERY SPEC IS SETTLED: 4K MAXIMUM

**The user's instruction, 2026-08-03: "video i want in max 4k ... for final".**

    resolution   3840 x 2160          <- the CEILING, not a stepping stone
    frame rate   24 fps
    frames       2,978  (1 .. 2978)
    duration     124.0833 s
    cuts         zero
    grade        AgX / look None / exposure -3.628   (world/film_exposure.py)
    dynamic range SDR  <- CONFIRMED by the user 2026-08-04, not an assumption

**SDR is confirmed, and that is what makes AgX the right transform.** AgX maps the
scene's real radiance -- sun plus sky at ~39 W/m2 -- onto a standard-range display,
rolling highlights off toward white the way film does instead of hard-clipping them
the way `Standard` would. `look: None` means no extra contrast curve on top.

**If HDR is ever wanted instead, it is not a render setting.** It is a different view
transform, a different grade, and a re-derivation of `FILM_EXPOSURE` -- which was
MEASURED against an 18 % card on the 5090, with two independent transforms agreeing to
0.014 stops. That decision belongs before the master, never after.

**Do not render above 4K for any reason.** There is no 6K or 8K rung above rung 4, and
nothing downstream expects one. An 8K attempt (7680x4320 @ 8192 samples) was made earlier
in this project and **failed with `RuntimeError: worker closed connection without replying`
after ~4 minutes** — suspected instance RAM or disk, never diagnosed, and now moot. If
anyone proposes an 8K pass "for safety" or "to downsample from", the answer is no: it is
undiagnosed, unbudgeted, roughly 4x the master's cost, and the delivery is 4K.

**What this settles about storage** (see the corrected figures above): the 4K frame
sequence is ~22 GB, a ProRes 422 HQ master ~11 GB, an H.265 delivery under 1 GB. The
whole delivery is ~34 GB against 136 GB free.

**Rung 4 IS the master.** The ladder's purpose is to arrive there once, clean.

## The ladder

**RUNG 1 IS NOW MEASURED, and the scaled estimates below it were wrong by ~10×.**
This table previously said *"measure rung 1 for real on its first run and correct
this table"* — 2026-08-03 is that measurement, taken on 50 real beat-5/6 frames.

> **720p / 64 samples = 63.4 s/frame → 52.4 h → $17.5 for a full-length pass.**
> The scaled estimate said **$1.8**. Off by **9.7×**.

**Why the scaling was wrong, and the number worth remembering:**

```
nominal 720p/64 -> 4K/512   =  9x pixels  x  8x samples  =  72x
ACTUAL measured ratio       =  510.5 / 63.4              =   8.1x
```

**Fixed cost dominates, not pixels.** Scene load, BVH build and per-frame overhead
do not shrink with resolution — so a low-res pass costs *far* more than its pixel
count suggests, and a 4K pass costs *far less* than 72× a 720p one. Any estimate
derived by scaling resolution and samples on this project will be wrong in both
directions. **Measure the rung.**

#### Splitting the frame into fixed and scalable — and the intuition it inverts

The two measurements above are two points on one line, so they can be solved.
With `63.4 = F + P` at 720p/64 and `510.5 = F + 72P` at 4K/512:

```
P = (510.5 - 63.4) / 71  =   6.30 s      the part that scales with pixels x samples
F =  63.4 - 6.30         =  57.1 s      the part that does not
```

**"Fixed cost dominates" is true at 720p and FALSE at 4K, and that inverts the
usual reading:**

| rung | fixed `F` | scalable | fixed share |
|---|---|---|---|
| 720p / 64 | 57.1 s | 6.3 s | **90 %** |
| 4K / 512 | 57.1 s | 453.4 s | **11 %** |

A 720p frame is almost entirely overhead. A 4K frame is almost entirely pixels.
This is *why* the ratio is 8.1× and not 72×, and it is the number to reach for
before proposing any change that claims to speed up rendering.

**What it settles immediately:** throwing more GPUs at a *single frame* only
divides the scalable part. Eight GPUs on one frame gives `57.1 + 453.4/8` =
**4.49×** at 4K and `57.1 + 6.3/8` = **1.10×** at 720p — i.e. nothing at all at
the rung where the ladder actually spends its 52 hours. Parallelism on this
project has to come from **rendering different frames at once**, never from
splitting one. See `vast-render/docs/multi-gpu.md`.

> **CAVEAT, and it is a real one: this is a two-point fit.** `n=50` at 720p
> (`r2b56_720`, beats 5–6) against `n=2` at 4K (`render3.blend`) — **different
> .blends**, and with adaptive sampling on, so the effective sample ratio may
> not be a clean 8×. `F` and `P` are the best available decomposition of two
> honest measurements, not a third measurement. Treat 57.1 s as an order of
> magnitude, and re-solve it the moment a third rung is measured.

| rung | resolution | samples | full-length pass | basis |
|---|---|---|---|---|
| 0 | 640x360 | 32 | ~$12 (est.) | scaled from rung 1 — **unmeasured, expect it to be high** |
| 1 | 720p | 64 | **$17.5, 52.4 h** | **MEASURED**, 50 frames, beats 5–6 |
| 2 | 1080p | 128 | ~$35 (est.) | interpolated between two measurements |
| 3 | 1080p | 256 | ~$50 (est.) | interpolated |
| 4 | **4K** | **512** | **$108, 13.4 days** | **MEASURED** basis, weighted per beat |

**The gap between rungs is much smaller than anyone assumed.** A full 720p pass is
**16 %** of the master's cost, not 1.4 %. That changes the discipline in one
direction only: rehearsal passes are *not* nearly free, so run them **deliberately
and few**, on ranges chosen to answer a specific question — not as a habit.

Cost at **$0.3339/hr** (the current instance; earlier figures used $0.4083). The
master's dollar figure moved on the *rate*, not on the work — 322 h either way.

The gap between rung 3 and rung 4 is the whole argument for the ladder: the master
costs more than every rehearsal combined, takes nearly two weeks of wall clock, and
**you get one attempt per fortnight**. Hunting temporal defects needs tens of passes.

Per-BEAT passes are the working unit and cost a fraction of the above — but note the
fraction is NOT proportional to duration. Beat 3 is 8 seconds and cheap; Beat 5 is
63.5 seconds at the world rate and is **67 % of the entire master on its own**.

## The rule

**A rung is only climbed when the rung below has zero open defects.** Not "no
known blockers" — zero open. The whole discipline of this project is that a claim
is not evidence, and "it will probably be fine at 4K" is a claim.

## Method at each rung

1. Render the sequence with `rq anim` (frame-range jobs, resume, per-frame
   sha256 + IEND + dimension + BLANK verification).
2. Assemble with ffmpeg and **watch it**.
3. **Strip back to frames and pixel-peep** — the user's word, and the right one.
   A defect that survives a moving watch is often obvious on a held frame.
4. Diff adjacent frames to surface temporal defects a human eye smooths over.
5. Log every defect in `DEFECT-LOG-R2.md`, fix, re-render THE SAME RANGE, confirm.

## What the farm already gives us

- `rq anim --frames A-B` with resume: a re-run renders only what is missing.
- Per-frame **blank/black detection** with a sequence-relative outlier check
  (rolling median/MAD over 25 neighbours) — on a synthetic 2,978-frame test with
  frame 1,600 dropped it flags exactly [1600], and a deliberate fade flags nothing.
- `spec_hash` per frame, so a mid-sequence settings change is a 409 rather than an
  invisible seam.
- `rq seq stats --csv` for a per-frame statistics dump across the whole sequence —
  which is how a human actually finds one bad frame in three thousand.

## The one thing the ladder cannot do

Low resolution HIDES material and geometry defects. A 720p pass will happily pass
grass that is a fuzzy mat, an asphalt that is a grey gradient, a decal that is
soft. So the ladder runs ALONGSIDE the per-item 4K macro audits, never instead of
them:

    sequences at low res   ->  temporal, motion, continuity, pacing
    stills at 4K, 1:1      ->  material, geometry, texture, detail

Both must be clean before the master renders.

---

# CORRECTION 2026-08-07 — BOTH RATE ANCHORS IN THIS DOCUMENT ARE THE WRONG SCENE

**Every schedule and cost figure above this line is drawn on files that are not
the film.** Three agents measured this independently, from different data, and
converged:

```
                    THIS DOC        MEASURED ON film16_breach      source
4K  s/frame          510.5           196.5 / 194 / 212 (weighted)  3 agents
720p s/frame          63.4            42.3                         completed pass
```

- The **510.5 s** 4K anchor is `render3.blend`, n=2.
- The **63.4 s** 720p anchor is `film6.blend`.
- Neither is `film16_breach.blend`, which is what ships.

**The 4K figure is ~2.6x too high**, so the "$108 / 13.4 days" master budget is
not a figure for this film. Re-measured properly, sampling **all six beats**:
**175.2 h render + 4.0 h overhead + 0.8 h cold starts = 180.0 h, $79.99** on one
exclusive card at $0.4444/hr.

**The beat-to-beat variance this doc is built on does not exist in the real
scene.** It assumes 8.5x. Measured: **1.5x across the whole film**, and beat 6 -
the closing wide it feared most - is *cheaper* than beat 5. At 720p the
completed pass puts the breach window f860-930 at 43.71 s/frame, **1.03x the
film average**. Per-frame overhead is **4.8 s, not 31**.

## The budget as it actually stands

```
master @ 512 spp                    180.0 h    $79.99
master @ adaptive_threshold 0.02    160.7 h    ~$71.40   <- visually free
credit                                          $72.39
```

`adaptive_threshold 0.02` was measured against a frame: mean delta **0.06**,
p99.9 of **1 level**, **0.00 %** of samples beyond 2 levels - below what any
delivery codec carries. **256 samples fits comfortably (~$47) and is NOT taken**:
17.5 % of samples move beyond 2 levels, so it is a look decision, not a budget
one.

**Headroom at the threshold setting is $1.93, not a percentage.** Fifteen
rentals is fifteen chances to draw a slower host than the one measured.

**Card count is not a money question** - under $3 across 1 to 8 cards, because
cold starts are 102 s on this class of host. It is purely wall clock: **7.5 days
on one card, 3.8 on two, 2.5 on three.**

**Both cards bill at $0.9239/hr combined** = ~78 h of runway against $72.39. The
per-broker $150 caps are **blind to each other** - $300 nominal against $72 real
- so **credit is the binding constraint and the caps protect nothing.**

---

# CORRECTION 2026-08-07 (second) — 196.5 s/frame IS ALSO NOT THE FILM'S RATE

The correction above replaced 510.5 s/frame with 196.5. **196.5 is 11 % low.**
Full derivation in `STAGING-R2-971-to-R2-999.md`; the short version:

The only whole-film measurement at the delivery spec is job `fc737127a232` —
`film16_breach.blend`, 3840x2160, 512 spp, **9 frames spanning 30..2850**,
1974 s, on an exclusive card with **zero overlapping jobs**:

```
                    THIS DOC      MEASURED (fc737127a232)
4K/512 s/frame       196.5              219.3
adaptive 0.02 saving  ~11 %              7.3 %   (frame 880, same card, 4 min apart)
```

Re-derived: **172.2 h, ~7.2 days, $76.5** at the current card's $0.4444/hr —
**not $71.40.** Against $69.52 credit (read from the vast.ai account) less ~$3.8
in flight, **the master is ~$11 short on the card we are on.**

**This document has now been wrong about the master three times, in both
directions, and every time for the same reason: a rate measured on one scene,
or one frame, extrapolated across 2,978.** The rule that keeps being written
here and not followed — *measure the artefact* — applies to per-frame time as
much as to per-frame bytes. Before the master is scheduled, re-read
`fc737127a232` from `state2/broker.db` rather than any number on this page.

**The gap closes on the card, not on the look.** Exclusive `gpu_frac=1.0` 5090s
exist at **$0.3356/hr** — 26 % under what we pay — and are invisible only
because `vastctl.MIN_CPU_CORES_EFFECTIVE = 32.0`, a floor written for `rq exec`
**build** throughput. A 4K master is one Blender process with Cycles and
denoise on the GPU and the scene loaded once; CPU is 1.9 % of its wall clock.
On such a card the master is **~$61** and fits. See R2-973.

**Do not reach for 256 spp.** It fits at ~$40 and the client declined it as a
look decision. It is not a budget lever.
