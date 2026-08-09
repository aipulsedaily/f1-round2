# THE 4K MASTER — what has to be true, and what it costs

Written 2026-08-08 from measurements, not estimates. Every number here has a
run behind it; where a figure was inherited rather than measured it says so.

## The spec, which is a ceiling and not a stepping stone

```
resolution    3840 x 2160        <- CEILING, not a stepping stone
frame rate    24 fps
frames        2,978  (124.0833 s)
cuts          zero
samples       512
grade         AgX / look None / exposure -3.628
dynamic range SDR
```

**256 spp was declined as a look decision, not a budget one.** If money gets
tight the answer is fewer cards and more days, never fewer samples.

## THE GATES — none of these may be waived

The master does not start until every line is green. This list exists because
the bar spent four film generations reporting `PASS` while 13 of its 37
assertions were silent, and the ship candidate flipped to `FAIL` the moment
they were counted.

| # | gate | why it blocks |
|---|---|---|
| 1 | `tools/film_bar.py` on the ship candidate, **all rows, nothing opted out** | it reported `24 checks, 0 failures` when the truth was 40 rows / 4 FAIL / 2 UNMEASURABLE |
| 2 | the **film10 negative control** must FAIL | its own header: *if film10 ever comes back PASS the instrument is broken and every PASS above it is vacuous.* It was piped into `tail` for four generations |
| 3 | `placement_gate` CLEAN on the scene that renders | `assembly14` gave 1,202 violations, 894 crowd prototypes parked in the car's path, while the old gate called it CLEAN by classifying 900 meshes subject and 29,304 context |
| 4 | **the car is in the last 91 frames** | `car_anim.blend` was 3 days behind the camera; beat 6 was wholly off frame for 3.79 s including f2978 |
| 5 | `rig_preflight` OK on the film | it had never once executed — invoked with `python3` when it needs `bpy`, and piped into `tail` |
| 6 | `MIN_CPU_RAM_GB` raised above the scene's **50.6 GiB resident** | the filter's floor was 50.0 and would rent a card the render dies on; the cgroup OOM takes the worker |
| 7 | **START THE MASTER ON BROKERS LAUNCHED AFTER 18:05 TODAY** | see below — the RAM fix exists on disk and is NOT in force in any running broker |

> ### GATE 7: THE RAM FIX IS ON DISK AND NOT IN FORCE
>
> `MIN_CPU_RAM_GB` is read **at import time** and bound as a default argument,
> so every broker started before the edit still holds **50.0**:
>
> ```
> vastctl.py modified   18:05:03 today
> ladderbroker  started Tue Aug 4 20:20:55     fleet03  started 05:31:20
> renderbroker  started Sat Aug 8 04:10:27     fleet08  started 05:31:35
> ```
>
> **All of them predate the edit.** `fleetctl up` on a fresh fleet picks the new
> floor up by construction; **reusing the brokers running since 05:31 does not,
> and it fails SILENTLY with a confident rent line.** That is the whole defect
> family this project has spent a week on, wearing operations clothes: the fix
> is real, the file is correct, and the process in memory is the old one.
>
> **Do not reuse a long-running broker for the master. Stand up a fresh fleet.**
>
> The floor is **72 GiB**, chosen by survey rather than taste: the exclusive
> 5090 market is bimodal and **nothing at all is on sale between 63 and 125
> GiB**, so 64 -> 8 offers, 72 -> 7, 96 -> 6. Any floor above ~64 buys the same
> tier, and 72 is the cheapest way to ask for it. 64 would have kept one 62.7
> GiB box in the set.
>
> **Three unit traps it absorbs, all measured:** vast.ai's `cpu_ram` query term
> is in **GB** while the offer dict answers in **MB**, so a 64 "GB" floor admits
> a **62.7 GiB** box — which was the cheapest offer on the market today. And
> **advertised RAM is not the container's cap**: an offer selling 61.9 GiB
> reported `memory.max` of 59.4 GiB, 96% of what was sold. So the query only
> narrows; a separate check **decides, in GiB, on the returned dict.**

## COST — measured on 13 real frames at delivery spec

Rendered from `film23_breach.blend` at 3840x2160 / 512 spp / ONER / adaptive
0.01, on one exclusive 5090, first frame per card discarded (BVH build).

| beat | frames | s/frame | GPU-h |
|---|---:|---:|---:|
| 1 assembly | 792 | 230.9 | 50.8 |
| 2 launch | 72 | 211.0 | 4.2 |
| 3 breach | 192 | 371.7 | 19.8 |
| 4 transit | 134 | 304.3 | 11.3 |
| 5 lap | 1,524 | 305.0 | 129.1 |
| 6 ending | 264 | 260.2 | 19.1 |
| **weighted** | **2,978** | **283.3** | **234.4** |

Plus **13.5 s/frame** of non-render overhead — fetch, verify, dispatch,
measured, against ~2 s in the runbook — = 11.1 GPU-h. **Total 245.5 GPU-h.**

Re-priced **at the enforced 72 GiB floor**, which removed the two ~60 GiB boxes
from the pool and therefore costs slightly more per GPU-hour:

| cards | $/GPU-hr | wall clock | total |
|---:|---:|---|---:|
| 1 | 0.4276 | 10.4 days | $107.23 |
| **3** | **0.4501** | **3.5 days** | **$112.88** |
| 5 | 0.4661 | 2.1 days | $117.36 |
| 8 | 0.5251 | 1.3 days | $132.09 |

**Eight cards is the purchasable ceiling** — only seven to eight offers on the
whole market clear the floor. The pre-floor figures were $100.33 / $111.14 /
$118.66; the floor costs **$1.74** at three cards and is not negotiable.

Cold starts priced at the **903.6 s deploy measured today**, not the 10 min
`cost_estimate` assumes, counted as `N x ceil(hours/12)` — 21 at three cards.

**Fastest safe configuration: three cards, ~84 h, ~$111.** Nine is 1.2 days and
$138, but **only seven offers on the whole market clear a safe RAM floor**, so
nine is not purchasable.

**My earlier $81 was wrong** and the reason matters: it was `219.3 s x 2,978`
taken on `film16_breach` at 7.97 GB. The scene is now 10.95 GB, renders at
283.3 s, and carries 16 GPU-h of overhead no previous figure counted.

## CORRECTIONS TO THE COST, MADE BEFORE SPENDING (R2-3666/3667)

**GATE 7 CAUGHT A LIVE ONE, AND IT WOULD HAVE BEEN BILLED TO THIS RENDER.**
The broker `rq anim` actually routes to was **101 hours stale** — started before
`280f49a` introduced the working-set gate — so it carried **no working-set check
at all** and would have rented against a **50 GB floor for a film projected at
~59.3 GiB.** Restarted, `rq drift` clean, 478/478 selftest, nothing rented.
**Fleet brokers 8762-8770 are STILL STALE and must be restarted before any
`fleetctl up`.** This is the gate working, not a theory about it.

**THE GPU-HOUR HAS RISEN 23.1 %.** Cheapest qualifying 5090 today is
**$0.454/hr against $0.3689/hr** at baseline. Re-price before committing.

**AND THE $112.88 WAS NEVER PRICED AT $0.3689.** 245.5 GPU-h x $0.3689 =
$90.58; the published figure used the floor-enforced pool, i.e. **$0.4598/GPU-h**
($112.88 / 245.5). An independent integrator reproduces **$112.90** from the
baseline's own per-beat seconds, so the model is calibrated — but quote the
rate, not just the total.

**THE MARKET GAP IS A KNIFE EDGE, NOT A DESIGN POINT.** Purchasable tiers today
are **73.10, 73.57, then nothing until 99.93 GiB**. The first offer is lost at
**x = 73.0992 GiB** — the "73.1" quoted elsewhere in this file **misses it by
0.0008 GiB.** Do not treat the ground cover's headroom as comfortable; measure
the film's actual resident footprint against 73.0992 and nothing rounder.

**THE RAM GATE FILTERS ON ADVERTISED RAM; THE SCENE LIVES IN THE CAP.**
Measured on the rented knife-edge box (offer 42272271): advertised **91.374
GiB**, container `memory.max` = 94,187,290,624 B = **87.72 GiB**. That is
**96.0% of what was sold**, and it reproduces an earlier independent
observation (61.9 sold → 59.4 capped, also 96%).

So `_meets_scene_working_set` filtering on the advertised figure **overstates
the margin by 4%**: a 73.09 GiB working set that just clears the gate on this
box actually sits at 87.72 / 73.09 = **1.20x headroom, not the 1.25x
`RAM_HEADROOM` names.** Still headroom, but not the headroom the constant
claims. **Either filter on `advertised x 0.96`, or raise `RAM_HEADROOM` to
1.30 so the effective margin is the stated one.** The code comment already
anticipated the gap; this puts a measured number on it.

**THE BVH PREMISE IS MEASURABLY WRONG.** The baseline's first frame rendered in
**274.66 s, BELOW the 283.3 s mean** — `render_sec` never contained the BVH
build, which sits in the ~948 s of setup. **Discarding each card's first frame
is still right** (push, load and first-fetch variance) **but it is not removing
a BVH cost**, and any argument that leans on that is wrong.

## THINGS THAT LOOK LIKE LEVERS AND ARE NOT

- **The proxy predicts nothing. R^2 = 0.00.** Its two *cheapest* frames are the
  master's two *dearest*. Never scale a cost from it.
- **`adaptive_threshold 0.02` is 3.7% weighted, not 11%** — and only **1.6%**
  on the breach. It evaporates exactly where the money is.
- **`--prio 0` is stored as 100** on all three submit paths
  (`int(body.get("prio") or 100)` — zero is falsy). Use 1.
- **The 12 h retirement has never fired on any instance** (longest life 10.7 h).
  The master takes that path 21 times. **Exercise it once first.**

## DISK — measured, and not a blocker

```
2,978 x 8.083 MB (mean)  = 23.5 GiB       p95 8.797 -> 25.6 GiB
+ ProRes 11 GB + H.265 <1 GB + one film scene 10 GB = ~47 GB of 148 GB free
```

Delivery frames are **8-bit RGB at 8.08 MB mean**, not the 15 MB assumed. The
16-bit 15.87 MB population is pixel-peep frames, not deliverables. Even at the
pathological 11.01 MB/frame it is 31 GB. **Render straight to disk.**

`.blend1` backups regenerate at full size on every save and the sweep is
repeatable — **re-run it just before the master starts.**

## THE GRADE — the one thing that cannot be fixed afterwards

**The grade must not crush saturation or lift blacks.** The closing car's
legibility rests on a **0.14 blue-minus-red colour break and a specular
glint**, not on luminance. A grade that reads well on a waveform and kills
that break has destroyed the ending.

## AUDIO — done, and one named lever if it comes back

Master byte-identical at `d5087fd021b5f748f176ecb2b6c1de67`, 124.0833 s,
-14.00 LUFS, -1.10 dBTP, all 8 gates green, 21/21 watch clips bit-exact.

If the client rejects the ending again the first number to look at is
`TARGET_LUFS_S["crowd"] = -27.0`, which owns **86%** of the band — **not** the
engine and **not** the wind. A mix decision with a name, not a defect hunt.

## AFTER THE RENDER

- **Cycles + OIDN are not deterministic across cards** — measured cross-card
  difference 2-6 levels of 255. **Byte-identity can never be an acceptance
  test on this fleet**, and any gather step must resolve duplicates
  deliberately rather than silently.
- Verify coverage, re-hash every frame against the broker's independently
  recorded sha256, and decode-check for blank frames. All three found nothing
  on the proxy; all three are still required.
- **Tear down and verify against the vast.ai API, not a local state file.**
  `reap`'s kill list was empty for a whole fleet once because it filtered on a
  label no live card carried.
