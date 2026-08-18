# THE 4K MASTER — what has to be true, and what it costs

> ## LIVE: THE MASTER IS RENDERING. Launched 2026-08-09 ~04:30Z.
>
> ```
> blend    render/film25_breach.blend   sha16 1d2aa2d86533574e
> world    assembly15                   0 of 94 source files drifted
> fleet    3 fresh cards on 8762/8763/8764, RAM floor verified from /proc
> ETA      ~82 h, around 2026-08-12
> spend    ~$0.99 of a ~$102-113 projection, cap $150, credit $[redacted]
> ```
>
> **The brokers are DETACHED — each is its own session leader with its own
> supervisor — so the render survives the session that started it.** Verified
> from `/proc/<pid>/stat`: ppid == sid for every one.
>
> **THE REMAINING STEPS ARE WRITTEN OUT IN ORDER, WITH EXACT COMMANDS, AT
> `docs/STAGING-R2-3841-to-R2-3900.md` (R2-3858)** — including the disjoint
> rebalance if fleet03 finishes early, and both ffmpeg command lines with their
> measured output sizes. **Read that before touching anything.**
>
> ### Three things for whoever picks this up
>
> **1. WATCH THE FIRST 12-HOUR RETIREMENT — do not assume the resume worked.**
> Due **16:06:32 / 16:07:02 / 16:07:33Z**. It has **never fired on this
> project** (longest instance life ever: 10.7 h) and the master takes that path
> roughly 21 times. Broker 5's job already demonstrated the resume logic
> correctly skipping five delivered frames, which is encouraging and **is not
> the same test**.
>
> **2. GATE 3's RESIDUAL IS REAL AND IS NOT A PASS.** `PLACEMENT_CLEAN` does
> **not** cover the ground cover's 4.96 M instances — by the tool's own
> declaration. It proves nothing *placed* is on the road; it does not prove the
> grass is off the tarmac. That rests on pixels, which were looked at.
>
> **3. DO NOT RUN THE 4K ENCODE WHILE THE BOX IS LOADED.** A 720p libx265 test
> already died on CPU contention at load ~19. Encode after the render, not
> beside it.
>
> ### And the correction that matters most about this launch
>
> **`placement_gate` had NEVER been run on the world that renders.** The
> `PLACEMENT_CLEAN` recorded for the assembly15 era had **no log, no JSON and no
> work directory**; its hidden count (1,203) did not reconcile with the only
> real run (1,159); and its selftest quote was verbatim from a log written the
> minute the tool was last edited. assembly14's verdict does not transfer — the
> 50 meshes it skipped as *empty* are exactly the `VEG_*` ground cover that
> carries geometry in assembly15, and the camera moved on **1,374 of 2,978
> frames** against a 0.648 m margin.
>
> It was run properly before the render: selftest first (**all 60 controls
> behaved**), then the gate — **`PLACEMENT_CLEAN`, zero violations, two
> identical passes, camera clearance `BR_Verge_R +0.648 m`.** The margin
> survived the camera move. **It is clean. It simply was not proven when this
> file first said it was.**


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

## FINAL MEASURED NUMBERS — film25_breach on assembly15 (R2-3669)

**Measured on the knife-edge card, six frames at true delivery spec, $0.312
spent, instance destroyed and confirmed by BOTH authorities (vast.ai API and
the broker).**

| frame | beat | film25 | film23 baseline | delta |
|---:|---|---:|---:|---:|
| 100 | assembly — **LEADER, DISCARD** | 243.575 | 274.660 | -11.32 % |
| 600 | assembly | 226.241 | 231.569 | -2.30 % |
| 900 | breach | 385.173 | 418.389 | -7.94 % |
| 1400 | lap | 308.266 | 331.773 | -7.09 % |
| 2100 | lap | 251.938 | 284.075 | -11.31 % |
| 2800 | ending | 230.521 | 255.917 | -9.92 % |

Five measured frames: mean **280.428 s** against the baseline's mean **over
those same five frames** of **304.345 s** — **-7.86 %**.

**DO NOT COMPARE 280.428 AGAINST 283.3.** That figure is the baseline's mean
over all 14 of its frames including its own leader. The like-for-like number
is 304.345.

**AND DO NOT BANK THE SPEEDUP.** Every frame got faster despite +17.16 %
traced triangles, but this is **a different host and n=1 per frame**. The card
is the likelier explanation than the world. **Treat the sign as unverified
until both worlds have run on one box**, and price the master at the baseline
seconds — the speedup is upside, not budget.

**THE RATE IS ESSENTIALLY UNCHANGED, WHICH IS THE POINT.** Today's cheapest
qualifying card is **$0.454/hr** against the **$0.4598/GPU-h that actually
produced $112.88.** The "+23.1 %" figure was measured against $0.3689, a rate
that never produced that total. **So the master is still ~$113, and today's
rate is marginally cheaper than the one behind the published figure.**

Setup overhead also came in **better**: **527.19 s** of rent+push+load+BVH
against the baseline's ~948 s, then 9.41-17.97 s per frame thereafter.

### FOOTPRINT — the projection was wrong and the direction is safe

| | GiB |
|---|---:|
| **Worker `VmHWM` — the successor to the 50.6 constant** | **52.4173** |
| cgroup `memory.peak` | 64.5228 |
| cgroup `memory.max` (the cap) | 87.7238 |

**Implied floor at x1.25: 65.52 GiB/GPU**, against a projection of 74.13 that
**overshot by 11.6 %.** Versus the old baseline it is **+3.6 %** — so
**+17.16 % of traced triangles bought ~3.6 % of resident memory**, because the
ground cover is instanced: it multiplies what the BVH traces, not what the
worker holds. The blend grew ~10 MB on disk, which says the same thing.

**All 9 of today's offers clear 65.52 GiB. Margin to the 73.0992 cliff is
20.68 GiB — the footprint would have to grow another 39.4 % to lose the
cheapest card.** `memory.events` read `oom 0 oom_kill 0 high 0 max 0` for the
whole run; peak sat at 74.6 % of cap.

**One qualifier to carry:** `VmHWM` is the like-for-like successor to 50.6, but
**the cgroup is what the OOM killer acts on**, and that peaked at 64.52 GiB —
~12 GiB higher, because it also counts page cache from streaming an 11 GB file.
Setting the constant from the cgroup instead gives a floor of 80.65 GiB, which
still clears all 9 offers but leaves only **8.58 GiB** of margin on the
cheapest.

## CORRECTIONS TO THE COST, MADE BEFORE SPENDING (R2-3666/3667)

**GATE 7 CAUGHT A LIVE ONE, AND IT WOULD HAVE BEEN BILLED TO THIS RENDER.**
The broker `rq anim` actually routes to was **101 hours stale** — started before
`9fc984c` introduced the working-set gate — so it carried **no working-set check
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
Measured on the rented knife-edge box (offer id-014): advertised **91.374
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
