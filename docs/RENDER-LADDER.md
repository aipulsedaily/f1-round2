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

### THE DISK BLOCKER — the master does not currently fit

At the measured **34.3 MB/frame**, 2,978 frames is **102.1 GB**. This box has
**78 GB free**. A full 4K master stops at about **frame 2,274** — roughly ten days
and $100 of GPU in — after which every remaining frame fails on write.

The *instance* disk was never the problem and is fine: `collect` deletes each frame
the moment its fetch verifies. Nothing was measuring the local side; `rq anim` now
warns at submit. **This must be solved before the master is started, not during.**
Note that `render/world/assembly/` holds seven ~4.2 GB assemblies (~29 GB), all of
them stale against contract 1.2.0 — but they are also the only existing worlds if a
rebuild fails, so that is a decision for the user, not a cleanup.

## The ladder

Rungs 0–3 are scaled from the measured 4K figures by pixel count and sample count.
**That scaling is optimistic**: BVH build and scene load are fixed costs that do not
shrink with resolution, so low-res passes cost relatively more than linear predicts.
Measure rung 1 for real on its first run and correct this table.

| rung | resolution | samples | full-length pass | purpose |
|---|---|---|---|---|
| 0 | 640x360 | 32 | ~$0.3 | camera path sanity — does the move work at all |
| 1 | 720p | 64 | ~$1.8 | timing, pacing, continuity, gross defects |
| 2 | 1080p | 128 | ~$8 | flicker, popping, sim behaviour, ramp smoothness |
| 3 | 1080p | 256 | ~$16 | near-final look; grade and exposure decisions |
| 4 | **4K** | **512** | **$131, 13.4 days** | THE MASTER — rendered once, when nothing is open |

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
