# STAGING R2-1241 to R2-1270

Fleet orchestration for the master render: N brokers, N single-GPU rentals, as
one operation. Built and proven 2026-08-07 against `film17_R2943.blend` at
delivery spec.

Code lives in `~/vast-render`: `farm/brokers.py`, `fleetctl`, `farm/procure.py`,
`farm/test_claim_crossproc.py`, `farm/test_gpu_guard.py`, `scripts/brokerN.sh`,
and one guard in `worker/server.py`. Nothing in `~/opus5-car-render` was touched.

---

## R2-1241 — `db.claim` IS cross-process atomic, and the obvious control does not prove it

`db.claim`'s docstring says `BEGIN IMMEDIATE` stops two dispatchers selecting
the same row. That was reasoned about for two THREADS inside one broker. Eight
brokers are eight OS processes, and SQLite's cross-process locking is a
different mechanism — POSIX file locks, WAL, `busy_timeout`, a real
`SQLITE_BUSY` that a threaded test never provokes.

Measured (`farm/test_claim_crossproc.py`), 8 real processes, one 300-job queue,
4 s each, three runs differing ONLY in transaction bracketing:

| mode | claims | SQLITE_BUSY | double-claimed across processes | rate |
|---|---|---|---|---|
| `BEGIN IMMEDIATE` (shipping) | 300 | 0 | **0** | 71/s |
| `BEGIN DEFERRED` | 300 | **680** | 0 | 71/s |
| no transaction (autocommit) | 641 | 0 | **206** | 152/s |

**The first control chosen was wrong, and that is the finding.** `BEGIN
DEFERRED` — the obvious "naive version" — does not double-claim. SQLite refuses
to upgrade a read transaction to a write one behind another writer's back, so
it aborts with `SQLITE_BUSY` instead: **safe, and 69 % of attempts thrown
away.** A test that had stopped there would have printed a green tick for a
mechanism it never stressed. The real control is no transaction at all, which
handed one job to **three** different processes.

The harness reports INCONCLUSIVE rather than PASS if its own control fails to
fail. Sensitivity is a result.

**71 claims/s against 4.5–11 s of serial broker work per frame** — the claim
path is four orders of magnitude from being the fleet's bottleneck.

**What this does NOT license:** a shared queue. `meta` is a flat key/value
table; `instance_id`, `bad_hosts`, the spend ledger and the resident
`scene_hash` all live in it under fixed keys. Two brokers on one DB would
overwrite each other's instance id and then destroy a card neither recognised.
The fleet partitions by contiguous frame block instead, and `fleetctl verify`
proves exactly-once on the delivered PNGs, which is the property that matters.

---

## R2-1242 — the multi-GPU default cost trap is now unreachable, and the guard is proved without renting a wide box

`worker/server.py:enable_gpu()` ended with `d.use = d.type == chosen` — every
OptiX device on the instance. Point a broker at an 8-GPU box and it silently
rents eight cards and delivers **1.27x**: $512.05 and 7.8 days for the master,
against $74.21 and 0.8 days on eight separate single cards. Correct frames,
eight times the rent, nothing in the log or on the bill to distinguish it.

`enable_gpu` now **refuses** an instance with more than one OptiX device unless
told what to do with it:

* `VASTRENDER_GPU_SLOT=<i>` pins one card and logs which, and that the others
  are billing and idle.
* `VASTRENDER_GPU_ALL=1` takes them all, deliberately, logging the measured
  1.27x.
* Neither → `TooManyGPUs`, whose message carries the count, the measured cost
  of both wrong answers, and the two ways to proceed.

**Refusing rather than silently pinning is the point.** Pinning would render
correctly while seven cards billed at $0.34/hr with nothing on them — the same
money lost, with a good render on top to hide it.

The guard is a **pure function** `select_devices(devices, kind, slot,
take_all)`, so `farm/test_gpu_guard.py` compiles it out of the shipping file
(not a copy — `ast`-extracted from `worker/server.py`) and drives it with fake
devices. 13 assertions, all green, no rented hardware:

```
single-GPU instance: unchanged            8-GPU, no instruction: REFUSED
slot=3 pins exactly one                   slot=8 / -1 / 99 refused, not clamped
GPU_ALL=1 takes all eight                 CPU entries never counted as cards
2-GPU instance also refuses               refusal names count, cost, remedy
```

A guard for a failure that only appears on a rented 8-GPU box, testable only on
a rented 8-GPU box, is not a guard.

`farm/procure.py` closes the same trap one layer earlier by refusing to BUY a
multi-GPU offer at all.

---

## R2-1243 — addressing a broker by URL is unsafe, and the fix is a loader with no wrong call

R2-979 reported one broker's status as two. The output was not wrong; it was
**unattributed**. `rq` takes `VASTRENDER_URL` or defaults to 8760, and
`BROKER_STATE` is read nowhere in the tree (verified: zero occurrences).

Worse, and previously unremarked: **`rq` silently re-routes.** `anim` and `seq`
go to `VASTRENDER_BULK_URL` (8761) unless `VASTRENDER_URL` is set. The obvious
way to write a fleet submission — eight `rq anim` calls in a loop with eight
`--frames` — sends **all eight blocks to broker 2**, the client's live beat-1
card, and says so only on stderr, on the seventh iteration.

`farm/brokers.py` follows `tools/live_campath.py`: it does not offer a URL to
check, it offers a BROKER. The URL, the state directory, the label, both tunnel
ports and the output directory come off one frozen object; `broker(n)` is the
only constructor. `rq_env()` pins `VASTRENDER_URL` and drops
`VASTRENDER_BULK_URL`. Every fleet command prints the identity triple it used:
`#3 http://127.0.0.1:8762 state3 fleet03`.

**And it verifies against the kernel, not against the broker.** `Broker.verify()`
finds the pid holding the listening socket via `/proc/net/tcp` + `/proc/*/fd`
and asserts its `/proc/<pid>/environ` carries the declared `VASTRENDER_DB`,
`VASTRENDER_PORT` and `VASTRENDER_LABEL`. That is how the process was started,
not a claim it makes about itself. `fleetctl up` and `fleetctl submit` refuse to
send work to a broker that fails it.

### The label scheme is a correctness property

`vastctl.our_instances` selects with `label.startswith(LABEL_PREFIX)` and
`Fleet.adopt_or_reap` **destroys every instance it returns bar the one it
adopts.** `broker2.sh` documents this for one pair. The generalisation bites:
**`fleet1` is a prefix of `fleet10`**, so the obvious naming would have broker 1
of the fleet reap broker 10's card, mid-frame, at its next restart.

Fleet labels are therefore fixed width (`fleet03`, `fleet10`), which makes
prefix-disjointness follow from distinctness, and `_assert_disjoint()` checks
all 12x12 pairs at import — including against the two live literals. The
selftest demonstrates the naive scheme aliasing rather than merely asserting
that the real one does not.

### The port formula reproduces the live brokers rather than renumbering them

Broker n: port `8760+(n-1)`, tunnel `8800-2n`, exec `8799-2n`, state
`state{n}`, out `out{n}`. Broker 1 falls out as 8760/8798/8797/`state`/`out` and
broker 2 as 8761/8796/8795/`state2`/`out2` — exactly what `brokerd.sh` and
`broker2.sh` already use, asserted in the selftest. A formula that did not
reproduce them would have required renumbering a running card.

`scripts/brokerN.sh <n> start|stop|status` reads the same module, so the shell
path and the Python path cannot disagree. It **refuses brokers 1 and 2**.

---

## R2-1244 — the N-pushes objection is worth half a dollar and ten minutes

**The strongest argument against eight separate cards, measured and closed.**

Eight rentals need eight copies of the scene; one wide box needs one, because
its cards share a filesystem. `multi-gpu.md` calls this *"the single strongest
argument for one 8-GPU box over eight 1-GPU instances, which would pay 8× every
push."* Prior evidence was contradictory: 4–5 MB/s uplink (R2-1047), 617 s for
one push (card probe), and a 4.5× fetch spread between two live hosts.

Four brokers pushed `film17_R2943.blend` (**7,980 MB**) to four fresh instances
**concurrently**, 2026-08-07 15:05–15:14 UTC:

| broker | blender 481 MB | scene 7,980 MB | scene MB/s | rent → ready |
|---|---|---|---|---|
| 5 | 8.9 s (54.4 MB/s) | **191.5 s** | 41.7 | 258 s |
| 6 | 15.7 s (30.7 MB/s) | **242.6 s** | 32.9 | 356 s |
| 3 | 44.3 s (10.9 MB/s) | **389.8 s** | 20.5 | 613 s |
| 4 | 63.8 s (7.5 MB/s) | **439.9 s** | 18.1 | 625 s |

All four overlapped for 106 s, three for a further 119 s. **31,920 MB of source
moved in 527 s = 60.6 MB/s aggregate.** The blend compresses **5.43× at zstd
-10** — measured directly on a 400 MB sample, which also showed compression
running at 102 MB/s, so the CPU is not the constraint either — so this was
**~11 MB/s on the wire against a ~27 MB/s uplink.**

**They did not serialise, and the local box was not the limit.** The proof is
the rank order: each host's scene rate tracks the rate that same host accepted
the *Blender bundle* at, before any scene contention existed, in exactly the
same order. The spread is **host ingest** — the ±45 % host lottery applying to
the push — not local contention. The two slow hosts went *faster* on the 8 GB
payload than on the 481 MB one, which is fixed per-transfer overhead amortising,
exactly as `incidents.md` warns.

### The number

Paid, non-rendering rental from `renting offer` to `deploy finished`:
**258 / 356 / 613 / 625 s, mean 463 s per card.** At the mean live rate of
$0.4556/hr that is **$0.059 per card, $0.47 for eight** — **0.6 % of an ~$82
master.** And because the pushes are concurrent the fleet's cold start is
bounded by its slowest card: **625 s = 10.4 min against a 20.4 h render,
0.85 % of the wall clock.**

> The single strongest argument for a wide box costs about half a dollar and
> ten minutes. It does not move the ranking.

**Extrapolation, labelled as one:** at N=8 the same scene needs ~22 MB/s on the
wire against a ~27 MB/s known ceiling. It should fit. That is arithmetic, not a
measurement — the first eight-wide run must watch the aggregate, which is why
`fleetctl status` now prints live per-broker push throughput.

**The old 2.29× compression figure is wrong for this scene.** Every push
estimate built on it overstates wire bytes by 2.4×.

---

## R2-1245 — the fleet renders the film at delivery spec, exactly once

**Not a design document. A render.** 2026-08-07 15:03:39–16:09:33 UTC.

```
scene    film17_R2943.blend   hash ec95e539bb6a04d4   (identical on all four)
spec     3840x2160, 512 spp, camera ONER, spec_hash c49ed585b3812fe5
frames   2715-2762, contiguous, beat 6 opening — 48 frames
fleet    brokers 3-6, four SEPARATE exclusive 5090s, gpu_frac 1.000 x4
```

### Every frame present exactly once, by hash

```
present 48    missing 0    duplicated 0    outside range 0
broker 3  2715-2726  12/12      broker 5  2739-2750  12/12
broker 4  2727-2738  12/12      broker 6  2751-2762  12/12
distinct sha256                          48 of 48
sha256 == the hash the BROKER recorded   48/48
resolutions delivered                    3840x2160 (one)
blank gate                               48 OK, 0 not-OK, 0 unmeasured
```

The hash check is against each broker's own `frames` table — a record made by a
different process at a different time, when it verified the fetch. Hashing a
file and comparing it to itself proves nothing.

### Speedup, from measured values only

| | |
|---|---|
| fleet wall clock | **3,954 s = 1.098 h** (first `renting offer` → last PNG on local disk) |
| single card, measured counterfactual | **13,069 s = 3.630 h** |
| | = 1 × median deploy (469 s) + every frame's own `render_sec` + every frame's own serial collect |
| **wall-clock speedup** | **3.31× on 4 cards** — 83 % of theoretical, *including* all four deploys and pushes |
| **steady state** | **3.60×** — 90 % of theoretical, render+collect only; the asymptote a 2,978-frame master sees |

### Cost, off the API, sampled before teardown destroyed the evidence

| broker | instance | machine | API $/hr | hours | $ |
|---|---|---|---|---|---|
| 3 | 47088518 | 144732 | 0.4237 | 1.112 | 0.4713 |
| 4 | 47088546 | 127280 | 0.4356 | 1.103 | 0.4802 |
| 5 | 47088573 | 137580 | 0.4741 | 1.095 | 0.5190 |
| 6 | 47088605 | 43130 | 0.4889 | 1.087 | 0.5313 |
| | | | | | **$2.0019** |

`show_instances` stops returning an instance the moment it is destroyed, and
`dph_total × duration` is the only account-side record of what a card cost.
Read it *after* teardown and the answer is silently $0.00. `fleetctl down`
samples it first, for that reason.

Planned beforehand at $1.12–$2.50 by `fleetctl plan`; actual **$2.00**, inside
the range and at the slow end, because the hosts drawn were slower than the
235 s/frame basis the plan was given.

### Teardown, verified

```
0 fleet instances alive — verified against the vast.ai API
2 NON-FLEET instance(s) still billing, LEFT ALONE:
   47039886  ladderbroker-...  broker 2 (protected)
   47090933  renderbroker-...  broker 1 (protected)
```

Independently re-checked afterwards: two instances on the account, both the
protected live brokers; two `broker.app` processes, both the live ones. Credit
$62.57 → $59.79.

### The serial broker work, and why the dispatch-thread worry does not apply

Measured as the wall gap between consecutive frames landing minus the second
frame's own render time — activity probe, ping, fetch, sha256, `imgstat` and
`rm -f` over SSH: **median 10.30 s/frame (5.39–21.22, n=44)**, per broker
6.04 / 9.85 / 10.62 / 12.38 s.

Against a 253.6 s frame that is **4.1 % busy**. And it is 4.1 % of *each
broker's own dispatch thread, in its own process* — **it does not sum.** The
"42 % busy at eight workers" concern belongs to the one-broker-N-workers
design, which is not what was built. In an N-broker fleet the dispatch thread
cannot saturate, at any N.

### The multi-GPU guard, live on a rented card

`enable_gpu()`'s new line, read off instance 47088573 by SSH mid-run:

```
[worker] device=OPTIX [NVIDIA GeForce RTX 5090]  (1 of 1 OPTIX device(s) on this instance)
```

So the guard is deployed, ran, and is transparent on a single-GPU box — the
half of R2-1242 that unit tests cannot establish.

---

## R2-1246 — teardown is not finished when the broker says it is

`rq teardown` returns success from the broker that ran it, and that broker
cannot see any other label — the isolation that stops two brokers reaping each
other. So "success" has never meant "nothing is billing". An idle rented 5090 is
$0.45/hr, **$10.80/day**, doing nothing.

`fleetctl down` therefore does not trust the reply. After every broker has
answered it re-queries the vast.ai API, retries up to four times with 15 s
settle, and:

* exits **non-zero** naming every fleet instance still alive, with `$/hr`,
  `$/day` and the exact `vastctl destroy` command;
* names every **non-fleet** instance still billing and which protected broker
  owns it, so `fleet down` cannot be read as `farm down`;
* flags any instance whose label no declared broker owns — nothing can tear
  those down, because no broker recognises them.

---

## R2-1247 — procurement must rank on $/frame, and today it cannot

`farm/procure.py`. Two hard rejects, neither of them a penalty:

* **`gpu_frac < 0.99`.** `vastctl.search_offers` treats exclusivity as a
  preference and falls back to shared supply, loudly — correct for one
  interactive broker that must keep serving, wrong for a fleet provisioned
  deliberately in one go. A shared card is R2-382: a co-tenant took 17,737 MiB
  and Cycles answered VRAM exhaustion with a structurally perfect all-black PNG,
  at 1.64x slower per frame for 12 % less money.
* **`num_gpus > 1`.** Of 42 two-GPU listings surveyed, 4 were exclusive and 28
  were quarter shares; the text reads "2x RTX 5090" either way.

Run against the live market 2026-08-07 15:12 UTC:

```
22 offers matched the production filter
 7 survived procurement       15 rejected as SHARED       0 multi-GPU
 0 of 7 had a MEASURED rate at this spec
```

**Zero.** So at that moment the ranking was on price alone — which is the thing
this module exists to say does not work. `fleetctl record` writes measured
s/frame per MACHINE per SPEC into `farm/hostrates.json`, and must be run
**before** teardown, because after `down` the machine id is gone and the rate
can never be
attributed to the silicon that earned it.

Keyed on machine, not instance: an instance is a rental, the machine is the
silicon. Keyed within that on `spec_hash`, because a rate measured at 720p/64
says nothing about 4K/512 — the two-point fit that assumed otherwise produced
four wrong master estimates in both directions.

### It is no longer zero — four machines, measured on identical work

Written by `fleetctl record` from the proving run. Same scene hash, same
`spec_hash`, four exclusive 5090s rented within two minutes of each other, 12
frames each:

| machine | API $/hr | measured s/frame | **$/frame** |
|---|---|---|---|
| 144732 | 0.4237 | 248.3 | **0.02922** ← cheapest per frame |
| 127280 | 0.4356 | 249.7 | 0.03021 |
| 137580 | **0.4741** | **233.4** ← fastest | 0.03074 |
| 43130 | 0.4889 | 282.9 | 0.03843 |

**The fastest card is not the cheapest per frame.** Machine 137580 renders 6 %
faster than 144732 and costs 12 % more, so it is **5 % dearer per frame** — the
exact shape this module was built for, now observed on cards we actually held
rather than inferred across separate sessions.

Price spread **1.15×**, speed spread **1.21×**, and they **compounded** rather
than cancelling: **$/frame spread 1.32×**. The earlier two-host observation
that an 11 % price difference and a 10 % speed difference cancel to 1.6 % was a
coincidence of that pair, not a rule.

### The ±45 % host lottery is too big a number for exclusive 1× 5090s

Four cards, same work, same hour: **233.4–282.9 s/frame = 1.21×**, or roughly
±10 % about the mean. The two 1× hosts in the original survey were 1.10×
apart. The **±45 %** figure came from including the 8-GPU box's *per-GPU* rate
(225.4 s) alongside two 1× hosts — a different machine class.

So: **exclusive single-GPU 5090s cluster within about 1.2× on sustained rate.**
Width, not the host lottery, is what moves that number. Procurement should still
rank on $/frame — the table above shows why — but the spread it is arbitrating
is ~1.3×, not ~2×.

Note also the min/max of *individual frames* was 227–432 s = 1.9×, and that is
misleading: the 432 s frames are each broker's **first**, paying the BVH build.
Sustained means are what a 2,978-frame master sees.

---

## R2-1248 — is eight the right number?

**Yes, eight works — but eight is not what binds, and the thing that does bind
was not on the list of worries.**

Every candidate ceiling, measured rather than argued:

| candidate ceiling | measured at N=4 | verdict at N=8 |
|---|---|---|
| dispatch thread saturating | 10.30 s/frame serial work = **4.1 % busy**, and it is **per process** | **cannot saturate at any N** |
| local CPU / uplink for N pushes | 60.6 MB/s aggregate, ~11 MB/s wire vs ~27 MB/s uplink | ~22 MB/s — fits, but that is arithmetic |
| local RAM for N brokers | ~50–70 MB RSS each | trivial |
| port space | 8760–8798 holds 12 brokers | fine |
| **market supply of exclusive 1× 5090s** | **7 offers + 4 held = 11 machines** | **binding** |
| block sizing | cost **17 %** of theoretical speedup | costs more |

### The dispatch-thread worry does not exist in this architecture

It was a real concern for *one broker with eight workers*, where one thread
does the fetch/verify for all eight. This fleet is eight **processes**, each
with its own dispatch thread, each measured at 4.1 % busy. It does not sum.

### Supply is the ceiling, and eleven is not a comfortable eleven

Sampled twice on 2026-08-07: **22 and 23** offers passed the full production
filter; **7 exclusive single-GPU** each time, the rest shared. Plus the four
already held, **11 exclusive machines existed on the market at once.**

`bad_offers` and `bad_machines` persist for **24 h**. A bad day that condemns
three leaves exactly eight, with zero slack — and the market churns fast enough
that the cheapest offer changed identity between two samples five minutes
apart. Eight is reachable today and would not have been reachable on a thinner
day.

It degrades gracefully, which is the saving grace: each broker rents
independently, so a fleet that can only get six cards is a fleet of six that
takes longer, not a failed run.

One real N-scale effect, observed: **broker 6 tried to rent the offer broker 4
had just taken** and got a 400. `_rent` fell through to the next candidate in
one second and nothing was lost. N brokers shopping one market converge on the
same cheapest listing, and the frequency rises with N.

### The number that should change is not the width — it is the block sizing

At N=4 the fleet delivered **3.31× of a theoretical 4×**. The gap is almost
entirely the slowest card: mean 253.6 s/frame against the slowest host's
282.9, and `mean / slowest = 89.6 %` predicts the measured steady-state 90 %
almost exactly. Equal blocks mean the fleet waits for its worst draw while its
best card idles down.

**At N=8 this gets worse, because the chance of drawing one slow card rises
with N.** The fix is not fewer cards, it is sizing blocks by *measured*
throughput: `fleetctl plan/submit --weights` now takes a weight per broker, and
`fleetctl record` produces the numbers to fill it from one frame per host at
about **$0.02 a host**.

### So: eight, with two conditions

1. **Rent eight, measure one frame on each (~$0.16 total), then re-split the
   remaining frames by `--weights`.** Two-pass, and it buys back most of the
   10 % that equal blocks throw away.
2. **Check supply first** with `farm/procure.py`. If fewer than ~10 exclusive
   1× offers are on the board, run six and accept 1.5 days instead of 1.1 —
   do not fall back to shared cards to reach eight. A shared card is R2-382,
   and a block rendered black costs more than the day it saved.

**Do not buy a wide box to avoid the pushes.** That was the strongest argument
for one, and R2-1244 measures it at **$0.47 and ten minutes.**

### Re-priced for the master, on today's cards, honestly bounded

Mean measured 253.6 s/frame + 10.3 s serial = 263.9 s/frame at the mean live
rate of $0.4556/hr:

```
2,978 frames x 263.9 s            = 218.3 GPU-hours
at 8 cards                        = 27.3 h wall = 1.14 days
rental                            = $99.5   (+ ~$0.5 of deploy/push)
```

**Bounded, not estimated.** These are beat-6 frames of `film17_R2943.blend` on
four hosts drawn on one afternoon, and the film's beats span 1.5× on the old
survey. It is an upper anchor for *these hosts on this beat*, not a
beat-weighted film figure — combining it with the 211.8 s/frame beat-weighted
basis from a different `.blend` on a different host is exactly the
neighbouring-configuration error that produced four wrong master estimates.

What is solid regardless of beat: **the market rate has moved up 7–14 %** (mean
$0.4556/hr against the $0.3999–$0.4488 the original tables were built on), so
every dollar figure in `multi-gpu.md` is low by roughly that much.
