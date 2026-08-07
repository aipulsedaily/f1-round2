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

**Credit, read directly from the vast.ai account (not from `rq`): $69.52.**

In flight and not yet landed: 625 frames of 720p/64 on broker 2 (measured
49.8 s/frame median, n=36) = 8.65 h = **~$3.8**, plus two exec builds. Broker 1's
queue is empty. So realistic credit at the master's start is **~$65.7**.

> **The gap on the current card is ~$11, not $1.81.**

## R2-972 — THERE IS NO CHEAPER EXCLUSIVE 5090 *UNDER THE PRODUCTION FILTER*

Live market, 2026-08-07, `scripts/probe_offers.py` (which uses the real
`vastctl.build_query`, so it lists only what the broker would actually rent):

```
cheapest exclusive offer   37400096   $0.4547/hr
what we already hold       47039886   $0.4444/hr   <- cheaper than the market
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
46780377). At 1.64x, $0.348/hr is $0.571/hr of work: the master would cost ~$99
and take 12 days. **Not a candidate at any price.**

## R2-973 — THE CPU FLOOR IS A BUILD CONSTANT AND IT IS PRICING THE MASTER OUT

`vastctl.MIN_CPU_CORES_EFFECTIVE = 32.0` is why the cheap exclusive stock is
invisible. Every word of its justification is about **build** throughput —
items/h, concurrent Blender processes, exec slots. Drop it and the same
exclusive query returns whole machines at **$0.3356/hr**:

| id | $/hr | gpu_frac | cpu | rel | disk | $/TB up,dn |
|---|---|---|---|---|---|---|
| `44173748` | **0.3356** | **1.0** | 16 | 0.995 | 533 GB | 2.60 / 2.60 |
| `44173814` | 0.3356 | 1.0 | 16 | 0.991 | 388 GB | 2.60 / 2.60 |
| `44499405` | 0.3747 | 1.0 | 28 | **0.998** | 1325 GB | 3.91 / 2.60 |
| `47062871` | 0.4281 | 1.0 | 12 | 0.997 | 605 GB | 1.30 / 1.30 |

These are **`gpu_frac = 1.0`** — whole machines, verified, direct ports, inside
the $4/TB bandwidth ceiling. They are not the shared trap. The only thing they
have less of is CPU.

**A 4K master does not use CPU.** One Blender process, Cycles on the GPU,
`denoise_gpu: true`, and under `persistent_data` the scene loads *once* across
all 2,978 frames. Measured on 47039886: `load 341s` against `render 17730s` —
**1.9 %**. Tripling the load phase on an 8-core host adds ~0.6 % to the master.

**Bandwidth is a non-issue for this job specifically.** The master pulls
2,978 x 7.5 MB = 22 GB down and pushes the scene once (~5 GB). At $2.60/TB that
is **under $0.10 total**. The $4/TB ceiling exists for the *item campaign*
(~384 GB), not for this.

### The master costed against each candidate (172.2 h, 45 GB disk, incl. transfer)

| card | $/hr | GPU | disk | net | **total** | vs $65.7 credit |
|---|---|---|---|---|---|---|
| `47039886` **current** | 0.4444 | 76.5 | incl. | 0.10 | **$76.6** | **short $10.9** |
| `37400096` cheapest under filter | 0.4547 | 78.3 | 2.12 | 0.10 | **$80.5** | short $14.8 |
| `44499405` rel 0.998, cpu 28 | 0.3747 | 64.5 | 2.12 | 0.10 | **$66.7** | short $1.0 |
| `44173748` rel 0.995, cpu 16 | 0.3356 | 57.8 | 3.54 | 0.10 | **$61.4** | **fits, $4.3** |

## R2-974 — INSTANCE 47049525 IS BURNING STORAGE FOR NOTHING

Read straight from the vast.ai API:

```
47049525  renderbroker-1786081905  actual_status = exited
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
| instance | 47049525 | 47039886 |
| rate | $0.4844 (API) | **$0.4444** |
| state | **exited**, 0 renders | running, 17,930 s up |
| queue | empty | depth 13, 625 frames |
| storage | $0.20/GB/mo | **$0.04/GB/mo** |

The `load 37s (100%) render 0s` card and "the current instance at $0.4627" are
**the same machine** — broker 1's, the idle one. The card doing the work is the
*cheaper* of the two.

Note also that `rq` reports $0.4627/hr for 47049525 while the API says $0.4844,
and $0.4403 for 47039886 against the API's $0.4444. **Cost the master off the
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
