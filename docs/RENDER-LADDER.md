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

### THE DISK BLOCKER — no longer blocking, but it is close, and it is now the FILMS

At the measured **34.3 MB/frame**, 2,978 frames is **102.1 GB**.

**Re-measured 2026-08-03: 143 GB free.** The master fits, with ~41 GB of margin. The
earlier figure of 78 GB — and the prediction that a 4K master would die at about frame
2,274, ten days and $100 of GPU in — **no longer holds.** Nothing was deleted to achieve
this; the box simply has more room than the note assumed.

**What now dominates local disk is not the assemblies, it is the film scenes.**

```
render/world/assembly/     49 GB    the worlds, incl. assembly8 (the ship)
render/film*.blend         48 GB    15 scenes at ~4.5 GB each
```

**Each film scene is ~4.53 GB and a new one is built whenever the camera or the world
moves** — which today happened four times (film9 → film10 → film11 → film12, with
film13 building). At 4.5 GB apiece that is an 18 GB day. **This is the growth curve to
watch, not the assemblies**, which change far less often.

**Do NOT bulk-delete either directory.** Four of those films are load-bearing:

| keep | why |
|---|---|
| the newest | the ship |
| `film10.blend` | the deliberate **assembly6 control** — `socket_index_audit --blend` FAILs it with 27 findings, which is what makes the newest film's PASS non-vacuous |
| `film9.blend` | the un-relit historical reference, 3,737 W against 46,203 |
| every assembly | the only existing worlds if a rebuild fails |

Superseded *intermediate* films (film11, film12 once film13 verifies) are the safe
reclaim, at ~4.5 GB each. **Ask before deleting** — the user has offered another 128 GB
on request, and asking costs less than losing a control.

The *instance* disk was never the problem: `collect` deletes each frame the moment its
fetch verifies, and the scene cache is now derived from measured room (23.0 GB on a
32.2 GB box) rather than a constant sized for a 16 GB disk that never arrived.

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
