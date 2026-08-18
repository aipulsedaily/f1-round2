# STAGING R2-971 to R2-999

## R2-971 — THE 4K MASTER DOES NOT FIT, AND THE STATED GAP WAS TOO SMALL

Re-derived from the brokers' own job history, not from any doc.

### The anchor: 219.3 s/frame, not 196.5

Job `fc737127a232` (broker 2, agent `masterprobe`, 2026-08-07 03:15–03:48):

```
scene       film16_breach.blend      <- the shipping film
resolution  3840 x 2160
samples     512
adaptive    0.01
frames      9, spanning 30 .. 2850   <- all six beats, not one window
render_sec  1974                     -> 219.3 s/frame
```

**It ran with ZERO overlapping jobs on an exclusive card** (checked against every
other row's `started`/`finished` in `state2/broker.db`), so it carries no CPU
contention. This is the best-designed measurement of the master's per-frame cost
that exists in either database, and nothing else comes close: every other 4K/512
row is `n<=3`, a single frame, or a different `.blend`.

The `196.5 s/frame` figure in circulation is **11 % low**. It is not in either
broker DB as a measured film16_breach rate at the delivery spec.

### `adaptive_threshold 0.02` saves 7.3 %, not the ~11 % assumed

The only clean A/B in the record — same frame, same card, four minutes apart:

| job | frame | samples | adaptive | render |
|---|---|---|---|---|
| `f4fd3a867e6d` | 880 | 512 | 0.01 | 280.1 s |
| `3e6b376b325f` | 880 | 512 | **0.02** | **259.7 s** |

**7.3 %.** A second pair at 256 spp (frame 2300, `b05efdd54765` 127.4 s vs
`8ab2b20e8815` 122.2 s) gives 4.1 %. Both jobs in the 880 pair overlapped the
same exec build, so the *ratio* is fair even though the absolute numbers are
contention-inflated relative to the clean 219.3.

`RENDER-LADDER.md` derives its `160.7 h / $71.40` from an implied **11 %**
saving. No measurement in this project supports that.

### The master, re-derived

```
2,978 frames x 219.3 s x 0.927 (adaptive 0.02)  = 168.2 h render
per-frame overhead (load 341s / render 17730s = 1.9 %)   3.2 h
cold starts                                              0.8 h
                                                  ------------
                                                       172.2 h   ~7.2 days
```

At the current card's $0.4444/hr: **$76.5**. At 512 / 0.01 with no threshold
change: 186 h, **$82.7**.

**Credit, read directly from the vast.ai account (not from `rq`): $[redacted].**

In flight and not yet landed: 625 frames of 720p/64 on broker 2 (measured
49.8 s/frame median, n=36) = 8.65 h = **~$3.8**, plus two exec builds. Broker 1's
queue is empty. So realistic credit at the master's start is **~$[redacted]**.

> **The gap on the current card is ~$11, not $1.81.**

## R2-972 — THERE IS NO CHEAPER EXCLUSIVE 5090 *UNDER THE PRODUCTION FILTER*

Live market, 2026-08-07, `scripts/probe_offers.py` (which uses the real
`vastctl.build_query`, so it lists only what the broker would actually rent):

```
cheapest exclusive offer   id-006   $0.4547/hr
what we already hold       id-037   $0.4444/hr   <- cheaper than the market
```

**Migrating under the current filter is strictly negative.** All nine exclusive
offers cost more per hour than the card broker 2 is already running. The
$0.189/hr card is long gone and nothing within 2x of it exists.

The cheap entries in the shared list — $0.336 and $0.348 — are `gpu_frac` 0.25
and 0.125. That is the R2-382 trap, and this project has already paid for it:
a co-tenant held 17,737 MiB while our Blender swung to 13,432 MiB against a
32,607 MiB card, and **Cycles under VRAM exhaustion returns a zero-filled buffer
that becomes a structurally perfect PNG** — right dimensions, right sha256, no
picture. Shared cards also measured **1.64x slower per frame** (instance
id-027). At 1.64x, $0.348/hr is $0.571/hr of work: the master would cost ~$99
and take 12 days. **Not a candidate at any price.**

## R2-973 — THE CPU FLOOR IS A BUILD CONSTANT AND IT IS PRICING THE MASTER OUT

`vastctl.MIN_CPU_CORES_EFFECTIVE = 32.0` is why the cheap exclusive stock is
invisible. Every word of its justification is about **build** throughput —
items/h, concurrent Blender processes, exec slots. Drop it and the same
exclusive query returns whole machines at **$0.3356/hr**:

| id | $/hr | gpu_frac | cpu | rel | disk | $/TB up,dn |
|---|---|---|---|---|---|---|
| `id-017` | **0.3356** | **1.0** | 16 | 0.995 | 533 GB | 2.60 / 2.60 |
| `id-018` | 0.3356 | 1.0 | 16 | 0.991 | 388 GB | 2.60 / 2.60 |
| `id-019` | 0.3747 | 1.0 | 28 | **0.998** | 1325 GB | 3.91 / 2.60 |
| `id-041` | 0.4281 | 1.0 | 12 | 0.997 | 605 GB | 1.30 / 1.30 |

These are **`gpu_frac = 1.0`** — whole machines, verified, direct ports, inside
the $4/TB bandwidth ceiling. They are not the shared trap. The only thing they
have less of is CPU.

**A 4K master does not use CPU.** One Blender process, Cycles on the GPU,
`denoise_gpu: true`, and under `persistent_data` the scene loads *once* across
all 2,978 frames. Measured on id-037: `load 341s` against `render 17730s` —
**1.9 %**. Tripling the load phase on an 8-core host adds ~0.6 % to the master.

**Bandwidth is a non-issue for this job specifically.** The master pulls
2,978 x 7.5 MB = 22 GB down and pushes the scene once (~5 GB). At $2.60/TB that
is **under $0.10 total**. The $4/TB ceiling exists for the *item campaign*
(~384 GB), not for this.

### The master costed against each candidate (172.2 h, 45 GB disk, incl. transfer)

| card | $/hr | GPU | disk | net | **total** | vs $[redacted] credit |
|---|---|---|---|---|---|---|
| `id-037` **current** | 0.4444 | 76.5 | incl. | 0.10 | **$76.6** | **short $10.9** |
| `id-006` cheapest under filter | 0.4547 | 78.3 | 2.12 | 0.10 | **$80.5** | short $14.8 |
| `id-019` rel 0.998, cpu 28 | 0.3747 | 64.5 | 2.12 | 0.10 | **$66.7** | short $1.0 |
| `id-017` rel 0.995, cpu 16 | 0.3356 | 57.8 | 3.54 | 0.10 | **$61.4** | **fits, $4.3** |

## R2-974 — INSTANCE id-040 IS BURNING STORAGE FOR NOTHING

Read straight from the vast.ai API:

```
id-040  renderbroker-1786081905  actual_status = exited
          80 GB @ $0.20/GB/mo  =  $0.0219/hr  =  $0.53/day
```

`vastctl`'s own module docstring: *"Destroy, never stop. Storage bills for as
long as an instance exists."* This one is **exited**, has served **zero** renders
(`rq status`: `load 37s (100%) render 0s`), and broker 1's queue is empty
(`depth=0`, idle >30 min). Over the master's 7.2 days it will quietly spend
**~$3.9** — which is most of the headroom in the table above.

It is broker 1's card and other agents submit stills to broker 1, so this is
**reported, not actioned**. But it is the cheapest recoverable dollar on the
board.

## R2-975 — THE TWO-BROKER STATUS READ, AND WHY IT LOOKED LIKE ONE CARD

`rq --state state2` and `BROKER_STATE=state2` are both wrong; neither is an
interface. `rq` addresses a broker **by URL**:

```
VASTRENDER_URL=http://127.0.0.1:8760 ./rq status    # broker 1, state/
VASTRENDER_URL=http://127.0.0.1:8761 ./rq status    # broker 2, state2/
```

`BROKER_STATE` is not read anywhere in `rq`, so setting it returns broker 1
silently — **a prior read of "both brokers" was broker 1 twice.** The two cards
are not alike:

| | broker 1 (8760) | broker 2 (8761) |
|---|---|---|
| instance | id-040 | id-037 |
| rate | $0.4844 (API) | **$0.4444** |
| state | **exited**, 0 renders | running, 17,930 s up |
| queue | empty | depth 13, 625 frames |
| storage | $0.20/GB/mo | **$0.04/GB/mo** |

The `load 37s (100%) render 0s` card and "the current instance at $0.4627" are
**the same machine** — broker 1's, the idle one. The card doing the work is the
*cheaper* of the two.

Note also that `rq` reports $0.4627/hr for id-040 while the API says $0.4844,
and $0.4403 for id-037 against the API's $0.4444. **Cost the master off the
API, not off `rq status`.**

## R2-976 — CHANGE MADE, NOT DEPLOYED

`vastctl/vastctl.py` (the file was git-clean; none of the ~10 uncommitted files
from other agents were touched):

```python
MIN_CPU_CORES_EFFECTIVE = float(os.environ.get("VASTRENDER_MIN_CPU") or 32.0)
```

**Default is unchanged at 32**, so nothing that runs `rq exec` changes
behaviour and the build broker keeps its cores. A render-only broker sets
`VASTRENDER_MIN_CPU=8` in its launcher next to `VASTRENDER_DISK_GB`, exactly the
mechanism `scripts/broker2.sh` already uses. Verified end to end: the env var
changes the emitted query and `search_offers` then returns the $0.3356
exclusive stock.

**A broker that rents on a lowered floor must not be sent `rq exec` build
work** — which is why this is a per-process knob and not a new default.

Not deployed. Picking it up needs a broker restart, and restarting broker 2 now
would cut 625 frames mid-pass.

## R2-977 — WHAT IS NOT RECOMMENDED

- **Do not migrate mid-pass.** Broker 2 has ~8.7 h of queued 720p work. The job
  boundary is when that queue drains.
- **Do not drop to 256 spp.** It fits (~$40) and it is a look decision the
  client already declined. It is not on the table as a budget lever.
- **Do not auto-migrate on price.** An automatic re-rent that chases $/hr is
  what walks into `gpu_frac 0.125` at 3 a.m. Any migration must re-assert
  `gpu_frac >= 0.99` and be taken deliberately, at a boundary.

## R2-978 — THE CHEAP CARD IS 9 % SLOWER, AND THE SAVING IS $2, NOT $15

R2-973 costed the master on the assumption that a cheaper exclusive 5090 renders
at the same rate. **It does not.** Measured, not inferred:

```
job fc737127a232  m4k_probe   instance id-037  $0.4444/hr  32c  61.6 GB  Florida
job 71fc8fd87ccf  m4k_cheap2  instance id-043  $0.3888/hr  32c  63.4 GB  South Africa
```

Same nine frames, same `.blend`, same `spec_hash` **`1983dced5cacabb6`** — which
folds in the scene's content digest `1e8d5440c349fe51`, so this is not "the same
settings", it is provably the same render of the same file. Same
`worker/server.py` (unchanged since 2026-08-04 06:50), so `render_sec` means the
same thing on both sides: pure `bpy.ops.render.render()`, no transfer, no load.

| frame | anchor s | probe s | ratio |
|---|---|---|---|
| 30 | 151.0 | 166.8 | 1.105 |
| 400 | 182.6 | 199.6 | 1.093 |
| 760 | 151.7 | 167.4 | 1.103 |
| 830 | 158.1 | 173.7 | 1.098 |
| 950 | 216.0 | 234.4 | 1.085 |
| 1120 | 230.5 | 250.5 | 1.087 |
| 1500 | 270.9 | 292.7 | 1.080 |
| 2300 | 210.5 | 228.6 | 1.086 |
| 2850 | 197.1 | 214.2 | 1.087 |
| **mean** | **196.48** | **214.19** | **1.0902** |

**The spread is 1.080 to 1.105.** Nine paired frames spanning all six beats and
a 1.8x range of per-frame cost, and the ratio moves by 2.5 %. This is the
tightest measurement in the project's record, and it says the same thing every
time: **the cheaper card is 9.0 % slower.**

### The saving, after the slowdown eats it

Cost per frame is rate x time, so a 12.4 % cheaper card that is 9.0 % slower is
**2.2 % cheaper per frame**, not 12.4 %.

```
                     all-in $/hr   s/frame   master h   master $
anchor id-037         0.4488      186.7      155.0      $70.06
probe  id-043         0.3999      203.1      168.6      $67.95
                                                          ------
                                                saving     $2.11
```

`$/hr` is `dph_total` from the **API**, which already includes the disk. Master
figures are at `adaptive_threshold 0.02` and include per-frame overhead, cold
starts at the 12 h `MAX_INSTANCE_HOURS` wall, and scene re-pushes — see R2-980
for the derivation.

**Credit at teardown: $[redacted].** So the master is **$1.96 short on the current
card and $0.15 clear on the cheap one** — and broker 2 still has 12 queued
`film17_breach` jobs to pay for out of the same balance. R2-973's "$4.3
headroom" does not exist at any price on this board.

### The pixels are the same; the bytes are not

Every frame passed the blank gate, and `lum_mean`, `lum_sd`, `lum_min`,
`lum_max` and `lum_levels` agree between the two hosts **to full printed
precision** on 7 of 9 frames and to 1e-6 on the other two. The PNGs are
nonetheless not bit-identical (frame 30: 7,765,101 B vs 7,767,322 B, different
sha256) — different driver (580.173.02 vs 590.48.01) and a different OIDN build
denoise the same samples marginally differently.

**That is a batch-seam risk, and `spec_hash` cannot see it.** `spec_hash` folds
in the scene and the settings, not the host, so a resume that changes machines
mid-sequence is invisible to every gate the farm has. At this magnitude it is
far below what a delivery codec carries — the same footing the
`adaptive_threshold 0.02` decision stands on — but the master will span 13-14
rentals whichever card it runs on, and **"same picture" here is a measurement,
not a guarantee that holds for an arbitrary pair of hosts.**

## R2-979 — THE $0.3356 TIER IS A 32 GB DESKTOP AND IT CANNOT OPEN THE SCENE

**The first probe failed, and the failure is worth more than the $0.10 it cost.**

`vastctl.MIN_CPU_CORES_EFFECTIVE = 32` was never only a CPU term. Checked
against the live market 2026-08-07, adding `cpu_ram>=50` to the 32-core
exclusive query **drops zero offers**: every >=32-core 5090 on sale carries
60-126 GB. Drop the floor to 8 and the hardware class changes underneath you.
Every single $0.3356/hr offer in that tier is one SKU:

```
Ryzen 7 7800X3D, 8C/16T, 30.5 GB RAM, South Korea    (5 offers, all identical)
```

**30.5 GB cannot open this film.** `config.EXEC_SCENE_MEM_FACTOR` already
carries the measurement — 22 GB resident for a 4.17 GB blend, **5.3x** — and
`film16_breach.blend` is 7.97 GB, so it needs about **42 GB**. The exec path has
refused this box on those grounds twice already (`ExecMemoryShort`); the render
worker has no such gate.

Measured on instance id-042 (offer id-013, $0.3356/hr, 30.5 GB): the worker
loaded the scene and reported ready in 308 s, the render started, and then

```
ping    205 ms, 0 % loss          TCP to :41032   connects instantly
ssh     "Connection timed out during banner exchange"  x4
frame   9 minutes, no progress, on a frame the 61.6 GB anchor renders in 151 s
```

**The box did not fail. It went catatonic.** And every probe the broker has —
heartbeat, progress, disk measurement — rides the same ssh that is being
starved, so a thrashing host is indistinguishable from a network fault. The log
for those nine minutes reads as a transport incident. It was a memory incident.

> This is the failure the CPU floor was accidentally preventing, and R2-973
> removed the guard without noticing it was one. **Every word of R2-973 about
> CPU is still true. It was answering the wrong question.**

### The fix, committed

`vastctl/vastctl.py` (path-scoped; the ~10 uncommitted files from other agents
were not touched), commit `a191737`:

```python
MIN_CPU_RAM_GB = float(os.environ.get("VASTRENDER_MIN_RAM_GB") or 50.0)
...
f"cpu_ram>={min_ram_gb:g} "
```

**Default 50, not 0.** It is behaviour-preserving where the old floor already
applied — nothing at >=32 cores is excluded by it — and it is what makes
lowering `MIN_CPU` safe rather than a trap. A guard that only exists when
someone remembers to set it is the guard that was not there.

**Units, because this one is silent:** the vast.ai query language takes
`cpu_ram` in **GB**; the offer dict returns it in **MB**. `cpu_ram>=50000`
matches nothing at all and reads as "no capacity" rather than as a malformed
query.

**Not deployed.** Both live brokers keep their in-memory copy until they are
restarted, and neither should be restarted mid-queue.

### What the market actually offers once RAM is asked for

```
cpu_ram>=50, exclusive, all other production terms unchanged
  id-015   $0.3888   32c   61.9 GB   rel 0.994   <- rented and measured
  id-009   $0.4014   12c   62.6 GB   rel 0.998
  id-011   $0.4547   24c   62.2 GB   rel 0.988
```

Cheapest viable is **$0.3888**, not $0.3356. The 26 % discount in R2-973 is
really **12.4 %**, and 9.0 % of that is spent on being slower.

## R2-980 — 219.3 s/frame IS A COLD START DIVIDED BY NINE

R2-971 corrected 196.5 to 219.3 and called the difference an under-count. **Both
numbers are real measurements of the same job and neither is the master's
rate.** From the broker's own log, job `fc737127a232`:

```
03:15:31  job admitted, offer rented
03:16:34  instance reachable                    62 s
03:18:16  worker serving the scene             102 s   -> 165 s ONE-TIME
03:18:16 .. 03:48:25   nine frames            1809 s
03:48:25  job finishes;  render_sec = 1973.9 s
```

`Broker.run_sequence` sets a sequence job's `render_sec` to `time.time() -
started` — **wall clock for the whole pass, rental and deploy included.** So:

| | s/frame | what it is |
|---|---|---|
| 196.5 | sum of the nine `frames.render_sec` / 9 | Cycles only |
| **201.0** | 1809 / 9 | **per-frame steady state — what 2,978 frames pay** |
| 219.3 | 1973.9 / 9 | the same, plus a one-time 165 s cold start **/ 9** |

The recurring per-frame overhead is **4.52 s** — confirmed frame by frame from
the log timestamps, which give +2.0, +4.4, +4.3, +4.9, +5.0, +4.5, +5.1, +4.5,
+5.9 s against the reported render times.

**R2-971 then added that overhead again.** Its `172.2 h` is
`2978 x 219.3 x 0.927` plus 3.2 h of per-frame overhead plus 0.8 h of cold
starts — but 219.3 already contains both, and it amortises the cold start over
**9** frames instead of 2,978. It also applies the `0.927` adaptive factor to
the overhead and cold-start portions, which do not scale with sample count.

```
                                        R2-971      re-derived
master h @ adaptive 0.02                 172.2         155.0
master $ on the current card             $76.5        $70.06
```

**11 % high.** Derivation, all from measured parts:

```
2978 x (196.48 x 0.927 + 4.52) = 555,814 s = 154.4 h
13 rentals x 165 s cold start  =    2,145 s =   0.6 h
                                             -------
                                               155.0 h  = 6.5 days
```

13 rentals because `vastctl.MAX_INSTANCE_HOURS = 12.0` retires every box at 12 h
regardless of what it is doing. Each rental re-pushes the 7.97 GB scene: ~104 GB
up and ~22 GB down across the master, **$0.49** at $3.91/TB — not the $0.10 in
R2-973, which counted one push.

## R2-981 — INSTANCE id-040 IS NOT DEAD STORAGE, AND THE $3.9 IS NOT THERE

R2-974 recommended reclaiming broker 1's exited instance for ~$3.9 over the
master's duration. **Verified before acting, and the premise does not hold.
Not reclaimed.** Three independent reasons, in ascending order of finality:

**1. It destroys itself after 60 minutes, and always has.** `HIBERNATE_SEC`
defaults to 3600 and broker 1 does not override it. It says so on every stop:

```
08:45:32  instance id-040 stopped after 9.0 min running (~$0.535 gpu).
          disk keeps billing ~$0.037/hr; destroying in 60 min
```

and the mechanism demonstrably fires — `id-031` stopped 06:06:31 and was
destroyed at 07:06:38, "hibernation expired, confirmed gone". A stopped
instance on this broker has a **one-hour** lifetime, not a 7.2-day one. The
maximum exposure is one window: **$0.022.**

**2. It is not idle.** It was woken by other agents' exec jobs at **07:31:29,
08:35:47 and 09:35:12** — three times in three hours, each time inside its own
60-minute window, which is *why* it survived to be observed as "exited". At the
time of writing it has been **running for 40 minutes**, staging
`film17_breach.blend` for job `9707a546f554`. Destroying it would have cut an
8 GB transfer out from under another agent.

**3. The storage rate in the log is wrong anyway, in the safe direction.**
`fleet.py` prints `config.DISK_GB * 0.0004667`, a hard-coded constant equal to
$0.3407/GB/month. The API reports this host at `storage_cost = 0.20` and
`storage_total_cost = 0.02222/hr`. **The broker over-states stopped-disk cost by
1.7x**, and it uses a constant where the offer carries the real per-host figure
(which ranges $0.133-$0.333/GB/month across today's market). Not fixed here —
`fleet.py` is one of the ~10 files other agents are mid-flight on.

**What was checked before deciding, and what could not be:** the queue was
empty (`depth=0`) and had served zero renders; `rq status` reported `cache
0.00G in 1 scene(s)`, so there is no warm cache to lose; the only exec outputs
on record (`c066603f71e3`) were already fetched to
`out/exec/c066603f71e3/occ_pilot.json`; the two failed/canceled exec jobs
produced none. The one thing that **cannot** be checked is the disk of a
*stopped* container — there is no ssh into it — so "nothing on its disk is
needed" rests on those records rather than on an inspection. Given that the
instance destroys itself hourly, that gap never had to be closed.

## R2-982 — WHAT THIS PROBE DOES NOT SETTLE, SAID PLAINLY

`RENDER-LADDER.md` has been wrong about the master three times, in both
directions, always because a rate measured on one scene was extrapolated across
2,978 frames. **This entry is the fourth candidate and it should be read as
one.**

What is strong here: the comparison is **paired, n=9, same `spec_hash`, same
worker build, spanning frames 30-2850**, and the ratio holds to within 2.5 %
across a 1.8x range of per-frame cost. As a statement about *these two hosts*,
1.0902 is about as solid as this project gets.

What it does **not** establish:

- **It is 9 frames out of 2,978 — 0.3 %.** The anchor's own beat coverage is
  the same nine frames. Two measurements drawn from the same nine-frame sample
  are not independent evidence about the other 2,969.
- **It is one host per price point.** The 1.0902 is a property of id-037
  against id-043. **Host-to-host variance across the 13-14 rentals a master
  needs is completely unmeasured**, and it is now the dominant risk — larger
  than the $2.11 the card choice is worth.
- **Both measurements are of a scene that no longer ships.** The anchor and this
  probe both render `film16_breach.blend`. Broker 2 has been serving
  **`film17_breach.blend`** (7.98 GB, rebuilt today 06:09) since this morning.
  A rate measured on the previous revision of the film is exactly the error this
  document keeps logging, one revision closer in.
- **The `0.927` adaptive factor is n=1**, one frame pair on a contended card.
- **The 165 s cold start is n=2**, and the second probe's deploy took 456 s
  because local `zstd -10` was competing with broker 2's twelve exec builds.
  Cold-start cost is a function of what else the workstation is doing.

**What would actually settle it:** one contiguous beat — 200-300 frames — at
full delivery spec, from the `.blend` that will ship, on the card the master
will run on, read off `frames.render_sec` rather than off a job total. That is
11-17 h and **$5-7**, roughly 10 % of the master. Against a single-attempt
7-day render with under $1 of headroom either way, that is not an expensive
rehearsal; it is the only measurement that has ever been asked for here and
never taken.

**And the headroom is the real finding.** At $[redacted] credit the master costs
$70.06 on the card we are on and $67.95 on the cheapest viable alternative.
**There is no card on this market that makes a 512-spp 4K master comfortable.**
The gap does not close on the card. It closes on credit, or it does not close.

## R2-983 — MY OWN R2-980 WAS 7.8 % LOW, FOR THE REASON THIS FILE KEEPS LOGGING

Caught before it shipped, and it is the fourth-time-wrong error in a new dress.

R2-980 derived the master from **196.48 s/frame**, the flat mean of the anchor's
nine sample frames. Those nine frames are not the film in the proportions the
film has:

| beat | frames | s/frame | share of render time | sampled by |
|---|---|---|---|---|
| 1_assembly | 792 | 161.8 | 20.3 % | 3 of 9 |
| 2_launch | 72 | 158.1 | 1.8 % | 1 |
| 3_breach | 192 | 216.0 | 6.6 % | 1 |
| 4_transit | 134 | 230.5 | 4.9 % | 1 |
| **5_lap** | **1,524** | **240.7** | **58.2 %** | **2** |
| 6_ending | 264 | 197.1 | 8.2 % | 1 |

**Beat 5 is 58 % of the master's render time and 51 % of its frames, and it is
sampled by two frames whose times differ by 29 %** (f1500 270.9 s, f2300
210.5 s). A flat mean weights it 2/9 instead of 1,524/2,978.

```
flat mean of nine frames   196.48 s/frame   ->  155.0 h  $69.57
beat-weighted              211.80 s/frame   ->  166.8 h  $74.84    +7.8 %
```

Use **211.80**. And note what it implies: **no card decision in this document
matters next to beat 5's rate, which is n=2 with a 29 % internal spread.** The
whole 1x-versus-8x market spread is 8.8 %.

## R2-984 — THE OFFER QUERY HAS ONLY EVER SEEN ONE EIGHTH OF THE MARKET

`vastctl.build_query` contained the literal `num_gpus=1`. Not a default, not a
parameter — a literal. **The broker has never been able to see a multi-GPU
machine**, which is why `docs/multi-gpu.md` had to source its offers by hand.

Third one in the same file, identical shape: `MIN_CPU_CORES_EFFECTIVE` hid the
cheap exclusive stock (R2-973), the missing RAM floor hid that the cheap stock
is a 32 GB desktop (R2-979), `num_gpus=1` hid multi-GPU entirely. Fixed in
`9533751`; **at `num_gpus=1` the emitted query is byte-identical to before.**

### What scales with width and what does not

Getting this backwards would make the filter exclude the box it exists to find.

* **RAM scales.** Measured on nine concurrent runs: **41.4–41.6 GB resident per
  Blender** holding the 7.97 GB scene. `VASTRENDER_MIN_RAM_GB` is now multiplied
  by GPU count.
* **Cores do not scale from the build floor.** `MIN_CPU_CORES_EFFECTIVE = 32` is
  a *build* constant (12 concurrent `rq exec` processes on one box). Expressed
  per GPU it would demand 256 cores and exclude the 192-core 8x boxes — the
  cheapest GPU-hours on the market. The query takes `max(per-box, per-GPU x N)`
  with a new `MIN_CPU_CORES_PER_GPU = 8`.
* **Disk does not scale**, because the scene cache is content-addressed on a
  shared filesystem: one 7.97 GB push serves every worker on the box.

### The exclusive market, by width

```
        offers   viable (>=42 GB RAM/GPU)   cheapest viable $/GPU-hr
  1x      20              14                      0.3803
  2x       5               5                      0.3883
  4x       2               1                      0.4670
  8x      11              11                      0.3470
  3x, 6x   none
```

**Only 1x and 8x are deep markets.** 2x is five offers and no cheaper than 1x;
4x barely exists.

### The client's own offer is the `gpu_frac` trap

Offer `id-030` was described as *2x 5090, 48 cores of 192*. **48/192 = 0.25**,
and a whole machine has `cpu_cores_effective == cpu_cores`. It had churned
before it could be read directly, but the market says what it was: of **42**
two-GPU 5090 listings, only **4** are `gpu_frac 1.0` — **28 are `gpu_frac
0.25`**. That is the R2-382 co-tenancy class, measured 1.64x slower with a
zero-filled-buffer failure mode, and it is not a candidate at any price.

## R2-985 — BOTH MULTI-GPU MODELS MEASURED: ONE RIGHT, ONE WRONG BY 3.5x

Rented an 8x RTX 5090 box (`id-045`, offer `id-035`, California, EPYC
192c/503 GB, `gpu_frac 1.0`, $2.71/hr all-in = **$0.339/GPU-hr**) and rendered
**frame 30 of `film16_breach.blend`, `spec_hash 1983dced5cacabb6`** — the same
frame, same spec, as the R2-978 comparison. Luminance identical to six decimal
places on every host, so only hardware differs.

```
                                        modelled       MEASURED    verdict
N independent workers, 1 GPU each         8.00x          7.80x     RIGHT
N GPUs on ONE frame                       4.49x          1.27x     WRONG by 3.5x
```

**Eight concurrent workers, one GPU pinned each via `CUDA_VISIBLE_DEVICES`, all
on frame 30:**

```
render_s  229.3 217.7 224.7 228.0 221.9 227.4 227.4 227.1   mean 225.42
solo on the same box, one GPU                               219.65
concurrency penalty                                          2.6 %  -> 7.80x
peak host RAM   322 GB of 503        per-process RSS  41.4-41.6 GB
```

Twenty-four effective cores per worker — below `MIN_CPU_CORES_EFFECTIVE = 32`,
which `multi-gpu.md` flagged as an unquantified risk — cost **2.6 %**, including
eight simultaneous 7.97 GB scene loads.

**All eight GPUs on one frame: 172.8 s against 219.65 s solo — 1.27x, not
4.49x.** The doc honestly labelled this *a model, not a measurement*; it was
wrong in the expensive direction. **And it is what happens by default:**
`enable_gpu()` sets `d.use` on every OptiX device, so pointing today's broker at
an 8-GPU box silently rents eight cards and uses 1.27 of them. A master run that
way is **$512 and 7.8 days.**

## R2-986 — $/GPU-HR IS A TRAP. $/FRAME IS THE NUMBER.

The client asked for "cheapest possible pricing, full stop". This is the honest
answer and it is not the one the market's sticker prices suggest.

```
Florida    1x   $0.4488/GPU-hr x 151.0 s  = $0.01882/frame
S. Africa  1x   $0.3999/GPU-hr x 166.8 s  = $0.01853/frame
California 8x   $0.3387/GPU-hr x 225.4 s  = $0.02121/frame   <- DEAREST
```

> **The cheapest $/GPU-hr box on the market is the dearest per frame**, because
> its individual GPUs are **45 % slower** than a good single card.

Market-wide the per-GPU price spread from 1x to 8x is **8.8 %**. The host
lottery — how fast the silicon you actually drew renders — is **±45 %** across
three measured hosts. **Width is inside the noise of which host you get.**

And the sharpest illustration: the two 1x hosts differ by **11 % in price** and
**10 % in speed**, and those cancel to **1.6 % in $/frame**. Shopping on sticker
price is close to worthless. **The cheapest thing available is a good host, not
a wide box** — and the only way to know a good host is to render one frame on it
and compare against 151.0 s.

## R2-987 — THE RECOMMENDATION: EIGHT BROKERS, EIGHT CARDS, NO CODE

Beat-weighted 211.80 s/frame x 0.927 (`adaptive 0.02`), 2,978 frames, serial
broker work at the worst measured 4K host, cold starts at the 12 h
`MAX_INSTANCE_HOURS` wall.

| architecture | wall | days | total $ | code |
|---|---|---|---|---|
| 1 broker, 1 card (today) | 163.1 h | 6.8 | **$74.11** | — |
| **8 brokers, 8 cards** | **20.4 h** | **0.8** | **$74.21** | **none** |
| 1 broker, 8 workers, 8x box | 30.4 h | 1.3 | $83.60 | ~1,300 lines |
| 1 broker, 1 worker, 8x box | 186.6 h | 7.8 | $512.05 | none — the default |

**Eight broker processes on eight single cards: 8x the speed for +0.1 % money
and no new code.** It is the "two brokers, one card each" pattern already built
and proven, run eight times. The ~1,300-line N-worker build is **$9 dearer and
50 % slower** than the free option, because the wide boxes on this market have
slow GPUs.

### How to do it without breaking the farm

* **Contiguous blocks, never stripes.** `parse_range` supports `1-2978x8`, which
  balances load perfectly and is exactly wrong: PNGs from different hosts are
  **not bit-identical** (different driver, different OIDN build — measured,
  luminance agrees to 6 dp, bytes do not). Striping puts a machine boundary
  between every adjacent frame pair; contiguous blocks put seven in the whole
  film. Size blocks by the per-beat table in R2-983, not by frame count.
* **Eight disjoint labels**, pairwise — `startswith`, so "renderbroker2" is
  reaped by "renderbroker".
* **Eight disjoint tunnel and exec ports.** Startup reaping SIGKILLs any `ssh -L`
  on its port that is not its own child; a collision kills a sibling's tunnel
  mid-frame and reads as bad hardware.
* **The local workstation is the bottleneck, not the market.** 6 cores, 11 GB
  RAM. Eight concurrent `zstd -10` compressions of a 7.97 GB scene will
  serialise on it: one push took 405 s today against the exec builds, and the 8x
  box's took **617 s**. Stagger the starts.
* **Probe each host with one frame before committing it to a block.** At ±45 %
  host variance and ~$0.02/frame, one frame is the cheapest insurance on the
  board.

## R2-988 — WHAT I DID NOT BUILD, AND WHY

**The N-worker path is not built, and on these numbers it should not be.** It
costs ~1,300 lines to be $9 dearer and 50 % slower than eight broker processes.

Independently of the economics, it was also **not mine to write**. Of the five
files `multi-gpu.md` sizes the work across, **four are among the uncommitted
files other agents hold right now** — `broker/config.py` (`WORKER_PORT`),
`broker/fleet.py` (`ep`/`tunnel`/`scene_hash`, ~400–600 lines), `broker/remote.py`
(`WORKER_PIDS`, `progress.json`, ~150), `broker/app.py` (`dispatch_once`, ~300).
Only `worker/server.py` is clean. The brief forbids deploying those, and the
build cannot be done without editing them.

The three couplings that would break, from that doc's own table, are all still
real and all still unaddressed: `progress.json` is one file and every
do-not-kill-a-running-frame guard reads it; `WORKER_PIDS` kills by pattern, so
one restart kills all eight; and `activity()` cannot answer both "is slot N
rendering" and "is any slot rendering". **What has changed is only that they are
no longer worth solving.**

**What would reopen it:** an 8-GPU box whose per-GPU speed is within ~10 % of a
good single card. n=1 here, and only 11 exclusive 8x offers exist. The test is
one frame and ~$1 — rent, render frame 30, compare against 151.0 s. **Do not buy
a wide box without doing that first.**

### Spend and standing state

The 8x probe cost **$1.90** — $0.26 on a first host that failed to deploy (its
own `apt-get` still held the dpkg lock) and $1.64 on 36.4 min of the box that
worked. Over the ~$0.40 budgeted; the failed host and a 617 s scene push on a
6-core uplink are where it went. Both instances destroyed and confirmed gone.
Credit **$[redacted]**. Broker 2 was not touched at any point and carried the
client's beat-1 proxy throughout.
