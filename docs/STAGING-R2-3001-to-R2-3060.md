# STAGING R2-3001 to R2-3060 — what the 4K master really costs, and #66 / #67 / #80

Agent `r2-3001-throughput`. 2026-08-08.

Tasks: the master's true cost (raised mid-task, taken first), then **#67**
(re-run the remote-exec A/B on decent hardware), **#66** (local + remote build
queues together), **#80** (`push_scene` is one unresumable stream).

Every number below has a run behind it, made today, on `film23_breach.blend` at
the delivery spec or on this box. Nothing is scaled from the proxy, nothing is
taken from `RENDER-LADDER.md`, and where a documented claim is contradicted the
contradiction is measured rather than argued.

---

## R2-3001 — the probe, and what it cost

One exclusive RTX 5090 (`gpu_frac=1.000`), offer `43255050`, instance
`47189253`, **$0.3689/hr** — the cheapest exclusive card the default filter
returns. The batch cap on the bulk broker was set to `spent + $5.00` **before**
the job was submitted, so the $5 ceiling is a mechanism and not an intention:

```
cap        $23.80          (was $150.00; restored at the end of this task)
spent      $18.7949
remaining  $ 5.0051
```

Fourteen frames of `render/film23_breach.blend` at **3840x2160 / 512 spp /
ONER / adaptive 0.01** — the delivery spec, byte for byte the same `spec` dict
the reference job `fc737127a232` used, on the scene that actually ships.

**Frames were chosen to span the whole-film proxy's own cost range**, not
picked consecutively and not picked by beat alone. The proxy `r22161_proxy`
(2,978 frames, 960x540, 32 spp, `film22.blend`) gives every frame in the film a
measured cost; the 14 probe frames were selected to cover it from its cheapest
(31.8 s) to its dearest warm frame (76.6 s), across all six beats. That makes
the film total an **integration over 2,978 measured proxy frames**, not a
sample mean multiplied by 2,978.

| beat | frames | proxy mean s | proxy median | min | max | proxy GPU-h |
|---|---:|---:|---:|---:|---:|---:|
| 1 assembly | 1–792 | 41.2 | 41.4 | 38.6 | 114.7 | 9.07 |
| 2 launch | 793–864 | 35.2 | 33.5 | 33.2 | 41.5 | 0.70 |
| 3 breach | 865–1056 | 33.8 | 33.7 | 31.8 | 92.0 | 1.80 |
| 4 transit | 1057–1190 | 33.5 | 33.5 | 33.2 | 34.1 | 1.25 |
| 5 lap | 1191–2714 | 58.4 | 61.7 | 33.3 | 234.2 | 24.72 |
| 6 ending | 2715–2978 | 67.1 | 75.3 | 41.6 | 75.9 | 4.92 |
| **all** | 2,978 | **51.34** | 41.57 | 31.8 | 234.2 | **42.47** |

### The first-frame trap, confirmed exactly

The proxy's nine dearest frames are **1, 341, 671, 1001, 1331, 1661, 1991,
2321, 2650** — 109 s to 234 s against a 41.6 s median. Those are precisely the
**first frame of each of the nine cards' blocks**. Nothing about those frames
is expensive; they pay the BVH build.

```
warm (2,969 frames)   mean 51.07 s   median 41.57 s   min 31.8   max 77.0
cold (9 frames)       109.1 .. 234.2 s      excess over warm: 778 s total
```

So the proxy's headline 51.4 s/frame is 51.07 s warm, and the whole cold-start
tax across a nine-card pass was **13 minutes**, not a rate. Any master estimate
that folds those nine frames into a per-frame rate overstates the film by
0.5 %; any estimate that reports the 234.2 s maximum as a beat-5 cost
overstates beat 5 by 4x. The probe therefore renders **f100 first and discards
it**.

---

## R2-3002 — #80, and it is not the resumability

**#80 as posed:** `push_scene` is one unresumable stream; the scene is now
10.19 GiB and the master pushes it to as many as ten cards; re-check.

**The premise is correct.** `broker/remote.py:1489` is `zstd -c <scene> | ssh
'zstd -d -o <path>'` — one process, one TCP connection, no temp file, no
offset, a 3600 s timeout. `stage_scene_tree` is the only caller on the render
path. A resumable 8-stream uploader **already exists twenty lines below it**
(`push_parallel`, `remote.py:1567`) and is used only for the 481 MB Blender
bundle.

**But the resumability is not what costs anything.** Every scene push this
project has ever made, across all eleven broker logs:

```
912 attempts      22 failures (2.4 %)
```

and the failures do not fail late. **Nineteen of the twenty-two died between
0.3 s and 37.1 s** — connection refused, banner-exchange timeout, a torn mux —
i.e. before there was anything to resume:

```
0.3 1.2 1.2 1.4 3.0 3.0 5.9 5.9 7.2 7.2 11.4 17.6 17.6 19.1 20.0 20.1 24.0 30.5 37.1
167.4 181.4 181.4     <- all three on instance 46712525, one host, one hour
```

The only three that died deep were all on **instance `46712525`**, at 167.4 s
and 181.4 s twice — the documented **180 s multiplexed-SSH ceiling**, fixed by
moving the push to `ssh_nomux`. **Since that fix there is not one recorded
mid-stream scene-push failure anywhere in the logs.** Resumability would have
saved, in the entire history of this project, about **eight and a half
minutes** — and the fix that actually removed the failure mode was not
resumability at all.

### What it actually costs is the single stream on a distant host

The push made for this task is the measurement. Instance `47189253`, taken by
the broker's own cheapest-exclusive filter:

```
RTT                 254 ms      (ss: rtt:254.763/0.41, minrtt 252.7)
loss                0.28 %      (4,592,668 retransmitted of 1.63 GB)
cwnd                1533 x 1448 = 2.2 MB in flight
single-stream rate  4.57 MB/s wire  ->  13.4 MB/s of scene per second
10.19 GiB push      817.0 s = 13.6 minutes, no failure, no retry
```

Ten minutes earlier, **to the same instance, over the same link, in the same
deploy**, the Blender bundle went up through `push_parallel`:

```
blender bundle 481 MB, 8 streams   44.6 s   10.79 MB/s   (2.6x the scene push)
```

That is like-for-like: same host, same minute, same local machine, same
uplink. The difference is eight TCP windows instead of one against a 254 ms
round trip.

It also **falsifies a documented, load-bearing claim.** `vast-render/README.md`
line 46:

> *"More SSH streams do **not** help — `push_blender` measured 4.02 MB/s
> parallel against 4.68 MB/s single — so payload size is the only lever the
> broker has on the wire."*

That was measured on a **69 ms** host, where the line really was the limit.
Today, on a 254 ms host, more streams help by **2.36x**, and payload size is
emphatically *not* the only lever. This is the same failure the brief warned me
about in a different guise: a transport number measured on one host and quoted
as a constant.

### And the offer filter is blind to distance

`vastctl.build_query` filters on `inet_up>400 inet_down>400`. The offer dict
**carries `geolocation`** and nothing reads it:

```
47033336  'South Korea, KR'    31499018  'Texas, US'       47165035  'Sweden, SE'
38769886  'Massachusetts, US'  38304383  'Mexico, MX'      45922064  'Japan, JP'
```

`inet_up` says 734 Mbps for the machine we rented. Its RTT is 254 ms. **The
advertised bandwidth does not predict a single-stream transfer at all**, and
the master pushes 10.19 GiB per card.

### At fleet scale, measured on the fleet that ran

`film22.blend` (10,009 MB) went to eleven instances during the whole-film proxy
this morning. Same file, same box, same hour:

```
state    04:52:49    99.6 s   100.5 MB/s raw   <- alone on the uplink
state2   05:24:32   201.5 s    49.7
state3   05:33:22   397.3 s    25.2
state5   05:34:05   280.9 s    35.6
state4   05:34:46  1014.5 s     9.9            <- 10.2x the solo push
state6   05:34:59   337.4 s    29.7
state7   05:37:55   503.6 s    19.9
state9   05:41:06   338.9 s    29.5
state8   05:44:35   340.1 s    29.4
state10  05:52:57   413.7 s    24.2
state11  06:18:03   421.2 s    23.8

n=11  mean 395.3 s  median 340.1 s  72.5 minutes of upload in total
```

Eleven brokers each independently compressed and pushed **the same file** up
**one** uplink. There is no dedup and there cannot be: the instances cannot
copy from each other. So a ten-card master pays, once:

```
measured on the ten-card push above, 05:24:32 -> 06:25:06:
  raw moved            100,090 MB   (10 x 10,009 MB)
  on the wire          ~34,160 MB   after zstd -10 at 2.93x
  union of push time      35.6 min  (span 60.5 min, peak 5 concurrent)
  AGGREGATE            16.0 MB/s on the wire, 46.9 MB/s of scene

so ten cards at today's 10.19 GiB scene: ~37 GB on the wire, ~39 min of
push if it packs as tightly, ~60 min if it packs as loosely as it did today
cards billing while they wait:  ~5 card-hours  =  ~$2.4 at $0.48/hr
```

Two things that aggregate says. **One stream to one host got 4.57 MB/s; ten
streams to ten hosts got 16.0 MB/s**, so the uplink is not saturated by one
push and the per-connection window really is the limit (R2-3002's point,
arrived at from the other direction). And **16 MB/s is still well under the
100.5 MB/s of scene-per-second a single uncontended push achieved at 04:52**,
so the fleet push is neither line-limited nor free.

### The direct A/B, because the bundle comparison was still two different files

Both transports already exist in `broker/remote.py`. Run back to back against
instance `47189253` at 16:46-16:49 on **the same 400 MB file** — deliberately
incompressible (`/dev/urandom`), so zstd's ratio cannot differ between the arms
and this measures the transport and nothing else:

```
A  push_scene    (1 stream, zstd -1)   116.0 s   3.45 MB/s   remote holds 400,000,000 B
B  push_parallel (8 streams, resumes)   43.4 s   9.22 MB/s   remote holds 400,000,000 B
                                                             SPEEDUP 2.67x
```

Both arms delivered the exact byte count, verified on the instance with `stat`.

**Applied to the push this task actually made:** 817.0 s becomes roughly
**306 s**. Across a ten-card master that is about **85 minutes of card time**,
and the resumability #80 asked about comes along for free, because
`push_parallel` already keeps and resumes every surviving part.

There is a real cost to the change and it should be stated: `push_parallel`
splits a *file*, so the scene would have to be compressed to a temp file
(~3.7 GB) instead of streamed. That is ~110 s of local zstd and 3.7 GB of disk
— **and it is compressed once for the whole fleet instead of once per card**,
which removes nine redundant 10.19 GiB compressions from a ten-card deploy.

**#80's verdict: the stated blocker is a NULL; the transport underneath it is a
real, measured 2.67x.** The unresumable stream has cost this project about
eight minutes in 912 pushes and is not a blocker at 10.19 GiB or at ten cards.
Replacing the transport is worth ~85 minutes of card time per master deploy and
makes the resumability question moot.


## R2-3003 — #66, and the hazard is real but it is not the OOM killer

**#66 as posed:** local and remote build queues run together clear the 2.0x bar
at **2.6x** using exec as built; is it safe to turn on for the master build?

First, what the 2.6x is. It is **not a measurement.** It is `A52 + B20` — the
local A/B's 95.3 items/h added to the remote A/B's 160.0 items/h, over the
local's 95.3, = **2.68x**. Two runs that never overlapped, summed. The number
has never been observed; the sum assumes the two queues do not interfere. The
whole question is whether that assumption holds **on this box**, and the answer
came for free, because the scene push for R2-3001 overlapped another agent's
film build and I sampled the box for 63 x 10 s throughout.

### Observed, 15:50-16:03 today, not reconstructed

At 15:50:10 agent `r2-2701-gate-film23breach` took the build lock and opened
`render/film23_breach.blend` (10.19 GiB) under Blender for the placement gate.
One second earlier the broker had started `zstd -10 -T6` on **the same
10.19 GiB file** for the scene push. Both ran for eleven minutes.

```
peak /proc/pressure/memory  full avg10 = 43.0 %    (baseline before: 0.00 %)
minimum MemAvailable        374 MB
swap                        13.0 GB of 45.1 GB used
blender RSS                 up to 8.07 GB
loadavg                     8.9 peak on 6 cores
```

**374 MB available with a 10 GB build in flight is the OOM killer's
neighbourhood**, and `tools/buildlock.sh`'s own refusal threshold is 700 MB.
It did not fire, because it only refuses when available is under 700 MB **and**
swap free is under 4 GB, and swap free was 32 GB.

### The thing buildlock does not cover

The build lock worked exactly as designed — `r2-2701` held it, and any other
*build* would have waited. **The scene push is not a build and does not take
the lock**, and it is a heavy local job: six zstd threads and a 10.19 GiB
sequential read of the very file the gate had open.

So the collision was not a policy failure by either agent. It is that
`buildlock.sh` guards build-vs-build and the master's own critical path
(compress + push, once per card, ten times) is invisible to it.

### And on this box the interference is not symmetric

The push was **not** CPU-starved by the build — `zstd -10 -T6` sat at ~51 % of
one core with nine threads and four idle cores, and `/proc/pressure/cpu` read
`full=0.00`. It was blocked on its output pipe: the transport was the limit
(R2-3002), not the contention. The build, meanwhile, ran to completion.

That is the honest shape of it, and it is milder than the brief feared: **on
this box a local build queue alongside remote work does not kill anything, it
costs memory-stall time.** Nothing was OOM-killed in eleven minutes at 43 %
memory pressure with 374 MB free.


## R2-3004 — the deploy, timed to the second

Every number below is from `state2/broker.log` for instance `47189253`, a cold
rental of the cheapest exclusive 5090 the default filter returns.

```
15:48:30  credit checked, offer 43255050 chosen ($0.369/hr, EXCLUSIVE)
15:48:31  instance created
15:49:02  ssh reachable                                        31.0 s
15:49:07  blender bundle push begins
15:49:51  blender pushed  481 MB in 44.6 s (10.79 MB/s, 8 streams)
15:49:51  provisioning
15:50:09  provision done, cache preflight                      18.0 s
15:50:09  scene push begins (zstd -10, probe 2.93x)
16:03:48  scene uploaded   10,946 MB in 817.0 s (13.4 MB/s raw, 4.57 MB/s wire)
16:04:06  worker ready, scene resident                         18.0 s
16:04:06  DEPLOY FINISHED                                     903.6 s = 15.1 min
16:08:52  frame 100 (first frame on the card) done            274.7 s, 7.9 MB
```

**A cold card costs 15.1 minutes before it renders a pixel, and 90 % of that is
one file going up one TCP stream.** That is the number that matters at ten
cards and at a 12 h retirement cap, and it is the same number #80 is about.


## R2-3004b — #66 continued: the local build queue is already ONE wide, with ten agents in it

Sampled at 16:13:54 while the probe rendered, with no action by me beyond
joining the queue:

```
holder   r22821_remeasure  pid 2715673  since 16:05:10   (8m44s and counting;
                                                          it held for 20m27s)
waiting  r2-1381-PREFIX      9m50s      r2-1381-POSTFIX    6m51s
         r2-2761-d7_a0.34    7m03s      r2970-px-before    4m43s
         r2-3001-execab-local 4m13s     r2-2701-gate-...   3m46s
         r2-2941-apron-light  2m48s     r2-2941-ship-void
         r2-2941-film-floor
depth    10 distinct build requests on one flock

Sampled every 30 s from 16:13 to 17:00 (n=92):
  mean waiters 12.6      max waiters 16      minimum MemAvailable 351 MB
  minimum MemAvailable 351 MB    peak /proc/pressure/memory full avg60 27.4 %
  the queue drained in 2 minutes the moment the 20-minute holder released:
  16:25:43 r2-1381-PREFIX -> 16:26:13 r2970-px-before ->
  16:26:43 r2-3001-execab-local -> 16:27:44 r2-2701-gate-film23breach
```

**The queue is not made of slow builds. It is made of one slow build.** Four
different agents' work passed through the lock in the two minutes after the
20-minute holder let go, at roughly 30 s each. Twelve agents waited a
cumulative ~2.3 agent-hours for one film-scale build that had no way to say
"this one is big" and no way for a 30-second item build to say "this one is
not".

**`tools/buildlock.sh` is a mutex, so the local build queue on this box has a
concurrency of exactly 1 for anything wrapped in it.** Ten agents were queued
behind one holder. My own 40-second item build (`r2-3001-execab-local`) sat in
that queue for over four minutes without starting.

That reframes #66 completely. **"Run the local and remote build queues
simultaneously" is not a switch that is off — it is a configuration this box
cannot reach.** The 2.6x arithmetic adds a 4-slot local queue to a 12-slot
remote one; the 4-slot local queue does not exist here. Either builds are
wrapped in `buildlock` (concurrency 1, and the 95.3 items/h local half of the
sum is unobtainable), or they are not (concurrency 4, and the OOM hazard the
lock exists to prevent is back).

And a second heavy local job was running unwrapped throughout: another broker's
`zstd -10 -T6 -c render/film22.blend`, a scene push to another card. **The lock
does not see scene pushes**, so the master's own critical path is outside the
only mechanism this box has for scheduling heavy work.


## R2-3005 — `--prio 0` is silently demoted to 100, observed in the act

Reported to me as *"`--prio` on `rq anim` is not necessarily the priority the
job ends up with — two jobs were silently demoted from prio 10 to 100."* I could
not reproduce a 10 -> 100 demotion — my own 14-frame job carries `prio=10` in
the jobs table, as submitted. **But there is a real demotion and it is worse
than the one reported**, because it hits exactly the value a caller reaches for
when a job must go first.

`broker/app.py`, all three submit paths:

```
2055:    prio = int(body.get("prio") or 100)      # POST /jobs      (render)
2123:    prio = int(body.get("prio") or 100)      # POST /sequences (anim)
2487:    prio = int(body.get("prio") or 100)      # POST /exec
```

`0 or 100` is `100`. `--prio 0` — the highest priority `rq` will accept, and the
documented meaning of the flag is *"lower runs sooner"* — becomes the default.

**Observed, not read.** Submitted against the live broker at 16:18, a sequence
that had nothing to render so that the control cost nothing:

```
$ ./rq anim --name r23001_mastercost --frames 100 --prio 0 \
            --agent r2-3001-prio0-control ...
2a19ca4739ea  queued
$ sqlite3 state2/broker.db "select agent,prio from jobs where id='2a19ca4739ea'"
r2-3001-prio0-control|100
```

Submitted 0, stored 100. The job was cancelled immediately afterwards; it never
rendered anything.

**The fix is `body.get("prio", 100)` in three places**, and it is worth making
before a ten-card master, because the one moment anybody will type `--prio 0`
is when a card has stalled and a re-issued block has to jump the queue.

*(The change is not committed here: `vast-render` has another agent's work
already staged in its index — `broker/app.py` among the eight staged files —
and this project's rule is path-scoped commits only. Flagged for whoever owns
that branch.)*


## R2-3006 — a fleet of nine does NOT cost the same per card as one

`vast-render/docs/multi-gpu.md` says **"card count is not a money question —
under $3 across 1 to 8 cards"**, and every master budget on this project has
been built on that. It is true of the *overheads*. It is not true of the
*price*, because the exclusive 5090 market is thin and a fleet has to walk up
it. Live snapshot, 16:21 today, the production filter (`gpu_frac>=0.99`,
`cuda_vers>=12.8`, `reliability>0.98`, `inet>400`), cheapest first:

```
 $/hr        id  geolocation           up Mbps   cpu
0.4414  46937219  South Korea, KR           784   Ryzen 9 7950X 16C
0.4685  47165035  Sweden, SE                631   Xeon E5-2696 v3
0.4694  31499018  Texas, US                 841   Ryzen 9 7945HX
0.4923  38769886  Massachusetts, US         815   Core i9-14900K
0.5347  31275126  Washington, US            565   EPYC 7452 32C
0.5614  38304383  Mexico, MX                479   Ryzen 9 7950X 16C
0.5614  47075581  Sweden, SE               9158   EPYC-Milan
0.6681  25192047  Spain, ES                 782   Ryzen 9 9950X3D 16C
0.7343  46790746  Japan, JP                4190   —
0.8014  45111654  France, FR               6480   Ryzen 9 9950X 16C
```

| fleet width | mean $/GPU-hr | vs one card |
|---:|---:|---:|
| 1 | **0.4414** | — |
| 2 | 0.4550 | +3 % |
| 3 | 0.4598 | +4 % |
| 5 | 0.4813 | +9 % |
| **9** | **0.5479** | **+24 %** |
| 10 | 0.5733 | +30 % |

**Nine cards cost 24 % more per GPU-hour than one**, and that is a fixed
multiplier on the whole master, not a per-card overhead. On a 200 GPU-hour
master it is roughly **$27**. It is the single largest term in the difference
between "the master on one card" and "the master in a day", and no budget on
this project has carried it.

*(The card this probe is on, offer `43255050` at $0.3689/hr, was the cheapest
exclusive on the market when it was taken at 15:48 and is below everything on
the 16:21 list. The market moves; treat the table as a shape, not as prices.)*


## R2-3007 — #67, and the A/B's unit set is recoverable exactly

**#67 as posed:** remote exec measured 1.68x against a 2.0x bar and was
rejected, but on a below-median box (23.04 effective CPUs when offers run
8-384). Re-run it on a proper CPU box and let the number decide.

The re-run is worth doing on this project's own terms because **the original
unit set can be reproduced exactly.** The A/B is described as *"26 real wave-1
item modules, each unit being exactly what an item agent does — import the
module, run `test_scene()`, save the `.blend`"*, and today `world/items/`
contains **exactly 26 modules that define `test_scene`** out of 49 `.py` files:

```
grandstand_riser_unit  kerb_precast_unit   team_truck_trailer   tyre_blanket
crew_fireproof_overall armco_post          marshal_post_column  pit_wall_unit
gantry_truss           timing_stand        heras_fence_panel    tyre_wall_tyre
lighting_mast          catch_fence_post    hospitality_deck     mullion_intact
armco_w_beam           marshal_post_deck   pit_wall_unit_itemkit
showroom_facade_panel_v2 pont_girder       terrain_ground       tree_scots_pine
tree_oak               pont_deck_slab      tree_italian_cypress
```

That matters more than it looks. A throughput ratio measured on a *different*
set of items is not comparable to 1.68x at all, and the brief's own warning —
*"compare like with like, and say explicitly what your sample is"* — is exactly
the trap a re-run invites.

**The single datum that decides the stated hypothesis** is `kerb_precast_unit`,
because the original A/B published it on its own:

```
kerb_precast_unit, one slot, nothing else running
    local i7-7700K       38.9 s
    rented 23-core EPYC  80.0 s      = 1.97x slower per core
```

If the same build on a 16-core Ryzen 9 7950X — the CPU the cheapest exclusive
5090s actually carry — lands near 40 s, the 1.97x was the host and every point
on the B curve moves with it. If it lands near 80 s, the reject stands on
better evidence than it had.


## R2-3008 — three things the broker's own projection does not carry

`Broker.cost_estimate` (`broker/app.py:1619`) is the number `rq anim` prints
before it rents, and it is the number an operator will act on. It is arithmetic
on a measured mean, which is right, but three terms are missing and all three
are measurable today:

| term | in the estimate | measured today |
|---|---|---|
| cold start after the 12 h cap | **10 min** each | **15.1 min** (903.6 s), of which 13.6 min is the scene push |
| per-frame non-render overhead | **0** | **14 s** median (fetch + verify + dispatch) — 11.6 GPU-hours over 2,978 frames |
| price of card *n* of a fleet | one card's `fleet.dph` | +24 % per GPU-hour at nine cards (R2-3006) |

None of these is a criticism of the arithmetic; they are inputs it never had.
The first two are one-line changes against numbers this task measured. The
third is not a constant and should be read off the offer list at plan time,
which is what `fleetctl plan` is for.


## #66 — VERDICT

**CLOSED AS A NULL, and not for the reason the brief expected.**

The brief's worry was the OOM killer. That is not what happens, because
`tools/buildlock.sh` already prevents it: through 63 samples of the busiest
period this box has had today — a 10.19 GiB film build, a 10.19 GiB scene
compression, and ten other agents — **nothing was OOM-killed**, memory pressure
peaked at 43 % `full avg10`, and available memory bottomed at 351 MB without a
kill.

The reason #66 cannot be turned on is arithmetic, not risk:

* the 2.6x is `95.3 + 160.0` over `95.3` — **two runs that never overlapped**,
  added together;
* the 95.3 half is a **4-slot local build queue**, and on this box heavy builds
  are serialised to **one** by the lock that keeps the OOM killer away;
* so the local half of the sum is worth **95.3 / 4 ≈ 24 items/h**, not 95.3,
  the moment the discipline the project actually runs is applied to it;
* which makes the honest combined figure `(160.0 + 24) / 24` if you count from
  the local baseline, or `(160.0 + 24) / 160.0 = 1.15x` if you count from the
  remote one. **Neither is 2.6x and neither clears a 2.0x bar over the better
  of the two halves.**

**What is worth doing instead, and it is cheap:** `buildlock.sh` is a mutex with
no notion of size. A 30-second item build waits behind a 20-minute film build,
and two item builds cannot run together on a box that had 8.5 GB free while they
queued. A lock that admitted work against **measured** `MemAvailable` — one
film-scale build, or N item-scale builds up to a memory budget — would recover
most of the 4-way local queue *without* reintroducing the failure the lock was
written for. That is the change #66 is really asking for.

**And one thing the master must carry regardless:** the scene push is a heavy
local job (`zstd -10 -T6` over 10.19 GiB) that the lock does not see. For a
ten-card master that is ten of them. They should be issued when no film build
holds the lock, or they will collide with the rebuild that produces the very
scene they are pushing — which is exactly what happened at 15:50 today.


## R2-3009 — the 12 h retirement has never happened, on any instance, ever

The runbook says a batch beyond 12 h *"**will** be interrupted — the
in-container watchdog retires the instance at that wall-clock cap"*, and that
the resume is *"handled by design, not yet exercised end to end at that
length."* The broker logs settle how far from exercised it is. Every instance
lifetime this project has ever recorded, longest first:

```
641.8 min   546.5   538.7   530.4   477.5   ...      (10.7 h is the record)
```

and every destroy on record is one of `idle`, `hibernation expired` or
`deploy failed`. **Not one instance has ever reached the cap.** The path that a
2,978-frame master will take dozens of times has never run once.

What it costs if it works exactly as designed is a full cold start each time,
and a cold start on the scene as it stands is **903.6 s**, not the 10 minutes
`cost_estimate` assumes — because a retired instance is *destroyed*, so the
resume is a new rental with an empty disk and the whole 10.19 GiB goes up
again. **And widening the fleet does not avoid it.** At the measured rate the master
is ~236 GPU-hours of work; a card stays under the 12 h cap only if
`236 / N < 12`, i.e. **N > 20 cards** — twice what `fleetctl` can address and
twice what the exclusive market carries. At nine cards each card runs ~26 h and
takes the untested path **twice**; at one card it takes it nineteen times. So
the retirement path is on the critical path of the master at every width that
is actually available, and the only question is how many times.

That makes it the one piece of engineering worth doing before the master
starts: **exercise a watchdog retirement once, deliberately, on a short
sequence**, rather than discovering it 27 times in the middle of a 2,978-frame
delivery.


## R2-3010 — the proxy does not predict the master, and on the breach it inverts

The whole-film proxy was the natural sampling frame for this probe, and using
it to *choose* the 14 frames was right. Using it to *scale* would have been a
disaster, and this is the measurement that says so:

```
frame  beat        proxy (960x540/32)   MASTER (3840x2160/512)   ratio
 200   1_assembly        41.5 s                 260.6 s          6.27
 600   1_assembly        41.4 s                 231.6 s          5.60
 750   1_assembly        39.4 s                 200.7 s          5.09
 830   2_launch          33.3 s                 211.0 s          6.33
 900   3_breach          33.7 s                 418.4 s         12.40
1010   3_breach          32.4 s                 324.9 s         10.03
```

**f900 and f1010 are the proxy's two cheapest sampled frames and the master's
two dearest.** f1010 is the single cheapest frame in the entire 2,978-frame
proxy (32.4 s) and costs **324.9 s** at delivery spec — 1.6x a beat-1 frame the
proxy priced 28 % higher. The regression of master on proxy over the sample has
**R^2 = 0.26 and a NEGATIVE slope** on the first six frames, collapsing to
**R^2 = 0.01** once beat 5 is added. That is not a weak predictor, it is an
anti-predictor, and the reason is exactly the fixed/scalable split
`RENDER-LADDER.md` derived and then stopped applying: at 960x540x32 a frame is
almost entirely per-frame overhead, which is highest where the *scene* is heavy
(beat 5's vegetation instancing); at 3840x2160x512 a frame is almost entirely
sampling, which is highest where the *image* is noisy — the breach, where
everything is seen through fractured glass and adaptive sampling never
converges early.

**Consequence for this estimate, and for anyone tempted to shortcut the next
one:** the film total is built by weighting each beat's own measured master
mean by that beat's frame count. Any figure derived by multiplying the proxy's
42.5 GPU-hours by a ratio is wrong, and wrong by different signs in different
beats.


## R2-3011 — caveats on the master number, stated before the number

Four things bound what the figure in R2-3012 can honestly claim.

**1. It is a figure for `film23_breach.blend`, and that is not certainly the
master scene.** `docs/NEXT-REBUILD.md` still lists work that no film blend
carries, and `film23_breach.blend` was written at 07:09 today, before the
beat-5 re-pace promotion at 06:15 had a rebuild behind it. Agent `r2-2701` was
running the placement gate against this very file while the probe rendered. If
a further rebuild lands more of the item campaign — 49 of 435 item modules
exist — the per-frame cost goes **up**, not down.

**2. One card, one host, one hour.** Every per-frame number is from instance
`47189253`, an exclusive RTX 5090 on a Ryzen 9 7950X. The published spread on
*exclusive single* 5090s is **1.21x** (the project's own corrected figure, after
an earlier ±45 % claim had to be withdrawn for folding an 8-GPU box's per-GPU
rate into it). So read the totals with a ±10 % host band, not as a point.

**3. Thirteen frames, not 2,978.** Beat means rest on 1-4 probe frames each.
The largest exposure is beat 5 at 1,524 frames — 51 % of the film — and it
carries the widest sampling error of any term in the estimate.

**4. The 12 h cold-start term is a projection onto a path that has never
run** (R2-3009). It is priced at the 903.6 s deploy measured today, which is
itself dominated by a single-stream push that R2-3002 argues should be replaced.


### #67 has an argument that does not depend on the ratio at all

While the probe rendered, this box's build lock went from **10 waiters to 16**,
and a 30-second item build of mine sat in that queue for over sixteen minutes
behind one film-scale gate. That is the ordinary state of this machine with
seven agents live, not an unlucky moment.

**Remote exec's value is not only its throughput ratio. It is that an exec job
does not queue behind a 10 GB film build**, because it runs on a box that has
no film build on it. A 1.68x ratio measured against a *saturated* local queue
understates the wall-clock benefit of moving work off a machine whose heavy-job
concurrency is one.

That does not overturn the reject — the bar was items/hour and it should stay
items/hour — but it is the reason the re-measure is worth its few cents even if
the number comes back the same.


## R2-3012 — the shape of the answer, before the last frames land

Three terms decide the fleet width, and only one of them is what everybody
assumes:

**Price rises with width, monotonically.** The exclusive 5090 market is ten
offers deep and the tenth is 1.8x the price of the first (R2-3006). Every extra
card is bought at the top of the remaining list.

**Wall clock falls as 1/N, exactly.** Nothing in the master is serial across
cards: `fleetctl` partitions the frame range into disjoint contiguous blocks
and each broker owns one instance. The only shared resource is the local
uplink at deploy time, and at 16 MB/s aggregate (R2-3002) ten scene pushes are
~40 minutes of one-time cost against tens of hours of render.

**The 12 h retirement is unavoidable at every reachable width** (R2-3009), so
it is a constant, not a lever: 20 deploys at one card, 27 at nine.

So the choice is a straight money-for-time trade with no safety term in it
above 2 cards, and one real safety term below: **at one card the master is ten
days long, and ten days is ten days of anything going wrong** — a host
disappearing, the local box rebooting, the queue being starved by another
agent's work — against a $30 saving.


## R2-3013 — the local half of #67's ratio, re-measured today

`kerb_precast_unit`, the one item the original A/B published on its own, built
on this box at 16:48-16:50 under `tools/buildlock.sh` (so: exactly one heavy
build on the machine, which is the *favourable* case for the local side):

```
>> STAGE RESULT: BUILD_UNIT kerb_precast_unit OK build=68.02s wall=78.69s
                            bytes=232,074,685  objects=2,307
```

`build_sec` is measured around `test_scene()` alone; `wall_sec` adds Blender
start-up, the save and the JSON write.

**The A/B's published local figure for this module is 38.9 s.** Today the same
module, on the same machine, with the build lock held and nothing else heavy
running, takes **68.0 s** — **1.75x slower**. The module has not been touched
since 3 August. What changed is the machine: seven agents, 16 jobs queued on the
build lock, and 45 GB of swap in play.

That matters for #67 in a direction nobody has counted, and it is the opposite
of the one the brief expected. **#67 asks whether the REMOTE half was measured
on a bad box. The local half is the half that has moved.** The A/B's `A52`
denominator — 95.3 items/h — was taken on a quieter machine than the one the
item campaign actually runs on. Scaling it by the 1.75x measured here gives
**~54 items/h** as this box's current local rate, and `160.0 / 54 = 2.96x`.

**The bar is 2.0x. On today's local baseline, remote exec clears it.**

State the sample explicitly, because that is what this project keeps getting
wrong: this is **one module, one run, each side**, and the 1.75x is a
*local-box-load* factor, not a property of the code. It is enough to say the
1.68x reject is not a stable fact — it is a ratio between two things, one of
which varies by 1.75x with how many agents are awake — and not enough on its own
to overturn the decision. The remote arm of the re-run (26 units, 12 slots, the
same host class the master runs on) is what settles it, and it is running.


## R2-3014 — THE NUMBER

Thirteen measured frames of `render/film23_breach.blend` at **3840x2160, 512
spp, ONER, adaptive 0.01, AgX, DOF from the scene** — the delivery spec — on one
exclusive RTX 5090. The fourteenth (f100) is discarded as the card's first
frame.

```
 frame  beat         proxy s   MASTER s   x proxy
   100  1_assembly      41.0      274.7     6.70   DISCARDED (BVH build)
   200  1_assembly      41.5      260.6     6.27
   600  1_assembly      41.4      231.6     5.60
   750  1_assembly      39.4      200.7     5.09
   830  2_launch        33.3      211.0     6.33
   900  3_breach        33.7      418.4    12.40   <- dearest
  1010  3_breach        32.4      324.9    10.03
  1120  4_transit       33.6      304.3     9.07
  1400  5_lap           75.8      331.8     4.38
  1750  5_lap           61.9      306.6     4.96
  2100  5_lap           33.7      284.1     8.44
  2500  5_lap           75.6      297.6     3.94
  2800  6_ending        61.7      255.9     4.15
  2950  6_ending        75.5      264.4     3.50   <- cheapest
```

**Per-frame non-render overhead: 13.5 s median (n=13, range 13-20 s)** — the
fetch of an ~8 MB PNG, its verification and the next dispatch, all of which the
GPU sits through. On this 254 ms host. The runbook's figure is ~2 s.

### Seconds per frame at true master spec, per beat regime

| beat | frames | probe frames | mean s/frame | GPU-hours |
|---|---:|---:|---:|---:|
| 1 assembly (showroom interior) | 792 | 3 | **230.9** | 50.8 |
| 2 launch | 72 | 1 | **211.0** | 4.2 |
| 3 breach (through fractured glass) | 192 | 2 | **371.7** | 19.8 |
| 4 transit | 134 | 1 | **304.3** | 11.3 |
| 5 lap (open circuit, vegetation, crowds) | 1,524 | 4 | **305.0** | 129.1 |
| 6 ending | 264 | 2 | **260.2** | 19.1 |
| **whole film, beat-weighted** | **2,978** | **13** | **283.3** | **234.4** |

**The beat-to-beat spread is 1.76x** (211.0 at beat 2 to 371.7 at beat 3) — not
the 8.5x `RENDER-LADDER.md` was built on, and not the 1.5x its first correction
claimed either. **The expensive beat is the breach, and it is expensive because
of noise, not geometry.**

### Total, and what it costs

```
render                      234.4 GPU-hours   (2,978 x 283.3 s)
per-frame overhead           11.1 GPU-hours   (2,978 x 13.5 s)
                            --------------
work                        245.5 GPU-hours
```

| cards | $/GPU-hr | deploys (12 h cap) | deploy GPU-h | wall clock | **TOTAL** |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.4414 | 21 | 5.3 | 251 h = **10.5 d** | **$110.69** |
| 2 | 0.4550 | 22 | 5.5 | 125 h = 5.2 d | $114.22 |
| **3** | 0.4598 | 21 | 5.3 | **84 h = 3.5 d** | **$115.31** |
| 5 | 0.4813 | 25 | 6.3 | 50 h = 2.1 d | $121.18 |
| 9 | 0.5479 | 27 | 6.8 | 28 h = 1.2 d | $138.22 |
| 10 | 0.5733 | 30 | 7.5 | 25 h = 1.1 d | $145.06 |

Deploys are priced at the **903.6 s measured today**, not the 10 minutes
`cost_estimate` assumes, and the count is `N x ceil(hours_per_card / 12)`
because a watchdog retirement destroys the instance and the next one starts
from an empty disk.

### Does $74.82 cover it? No.

```
credit at 17:00                          $74.34
cheapest configuration (1 card, 10.5 d)  $110.69
SHORTFALL                                 $36.35    at the slowest option
SHORTFALL                                 $40.97    at 3 cards / 3.5 days
SHORTFALL                                 $63.88    at 9 cards / 1.2 days
```

**The $81 estimate was low by 37 % at the same card count, and the gap is not
the rate — it is the terms that were never in it.** $81 was `219.3 s/frame x
2,978` on `film16_breach.blend` (7.97 GB). Today's scene is `film23_breach`
(10.95 GB), it renders at **283.3 s/frame beat-weighted**, and on top of that
sit 11.1 GPU-hours of per-frame fetch overhead and 5.3 GPU-hours of cold starts
that no previous figure carried.

**An honest ask is $120 for the 3-card configuration**, which leaves ~$5 of
headroom on a number with a ±10 % host band around it. Asking for exactly the
shortfall would fund a master with no margin for one slow host.


### The proxy control, finished

With all thirteen frames in, the regression of master seconds on proxy seconds
is:

```
master = 277 + 0.14 * proxy        R^2 = 0.00
```

**Zero.** Across a 2.3x range of proxy cost the master's per-frame time carries
no information from it at all. The whole-film proxy that cost $31.12 and 42.5
GPU-hours is an excellent *sampling frame* — it is how the 14 frames were chosen
to span the film — and it is worth **nothing** as a predictor of the master's
rate. Any future estimate that multiplies it by a ratio is guessing.


## R2-3015 — `adaptive_threshold 0.02` is not the lever it has been sold as

`RENDER-LADDER.md` carries it as *"visually free"* at **~11 %**, corrected once
to **7.3 %**, and it has been the standing answer to "the master is short".
Measured on `film23_breach.blend` at full delivery spec, the same three frames
at 0.01 and 0.02, back to back on the same card:

| frame | beat | 0.01 | 0.02 | saving |
|---|---|---:|---:|---:|
| 200 | 1_assembly | 260.6 s | 243.3 s | **6.6 %** |
| 900 | 3_breach | 418.4 s | 411.8 s | **1.6 %** |
| 1750 | 5_lap | 306.6 s | 296.2 s | **3.4 %** |

**The saving evaporates exactly where the money is.** Beat 5 is 51 % of the
film and gives 3.4 %; beat 3 is the dearest beat and gives 1.6 %. Weighted by
beat length the whole-film saving is **about 3.7 %** — roughly **$4** on a $115
master, not the $10-13 an 11 % figure implies.

The reason is the same one that makes the breach dear in the first place:
adaptive sampling can only stop early where a pixel has converged, and through
fractured glass with motion blur almost nothing converges. Raising the
threshold gives back nothing on the frames that cost the most.

**Do not budget on it.** It is inside the noise of the host lottery.


## R2-3016 — THE FASTEST SAFE CONFIGURATION, and what it costs

**Recommendation: three cards, `fleetctl` brokers 3-5, ~84 hours (3.5 days),
~$111** — priced in R2-3019 against a corrected 64 GB RAM floor, which the
master needs and the current filter does not ask for.

```
fleetctl plan   -n 3 --frames 1-2978 --sec-per-frame 283 --push-sec 817
fleetctl up     -n 3 --scene /home/zany/f1-round2/render/<master>.blend
fleetctl submit -n 3 --name master4k --frames 1-2978 \
                --cam ONER --res 3840 2160 --samples 512
fleetctl verify --manifest state/fleet/master4k.json
fleetctl down
```

**Why three and not one.** One card is $110.69 and **ten and a half days**. The
$4.62 saved is not worth ten days of exposure to a host vanishing, this box
rebooting, or another agent's work starving the queue — and it is inside the
±10 % band the measurement itself carries.

**Why three and not nine.** Nine cards is 1.2 days but **$138.22** — the thin
exclusive market charges 24 % more per GPU-hour by the ninth card (R2-3006).
$23 for 2.3 days is a real trade and the client can take it; it is not the
default, because the money is the binding constraint here and the wall clock is
not.

**Why `fleetctl` and not one broker with a wide range.** `rq anim`'s own
warning is right: one sequence job holds a worker for its whole range and
nothing preempts it. Three brokers on three single-GPU rentals is the shape
that is already proven, needs no new broker code, and partitions by
construction.

### Do these first. The first one is a correctness blocker, not an optimisation

0. **Raise `vastctl.MIN_CPU_RAM_GB` from 50 to at least 64** (R2-3018). The
   scene is **50.6 GiB resident**; the current floor will rent a card that
   OOM-kills the render worker, and a cgroup OOM picks the largest RSS, which
   *is* the render worker. This is the one item I would not start the master
   without.
1. **`--prio 0` -> 100** (R2-3005). Three one-word changes in `broker/app.py`.
   The one time anyone types `--prio 0` is when a stalled card's block has to
   jump the queue mid-master.
2. **Exercise a 12 h watchdog retirement once** (R2-3009). It has never
   happened on any instance in this project's history, and the master takes
   that path 21 times. Costs one short sequence and an hour of wall clock.
3. **Read `geolocation` when choosing offers** (R2-3002). It is in the offer
   dict and nothing looks at it. The card this probe ran on has a **254 ms**
   RTT, which cost 13.6 minutes of scene push and 13.5 s per frame of fetch —
   about **$6** across the master, on top of a slower deploy.
4. **Switch the scene push to `push_parallel`** (R2-3002). Measured **2.67x**
   on this host, already written, already resumable. ~85 minutes of card time
   per fleet deploy, and it makes the fleet compress once instead of N times.

### Do NOT reach for these

* **`adaptive_threshold 0.02`** — 3.7 % weighted, not 11 % (R2-3015).
* **256 spp** — the client declined it as a look decision; nothing here changes
  that.
* **A wider fleet as a cost measure** — it is strictly more expensive.


## R2-3017 — what this cost

```
budget ceiling set BEFORE submitting anything, on the broker that would rent:
    ladderbroker cap  $150.00 -> $23.80   ( = spent $18.79 + $5.00 )
    renderbroker cap  $150.00 -> $36.40   ( = spent $31.40 + $5.00 )

one exclusive RTX 5090, offer 43255050, instance 47189253, $0.3689/hr GPU
                                                           $0.3897/hr with disk

  deploy + 14 master-spec frames + 3 adaptive A/B frames
  + a 400 MB transport A/B + 26 remote build units
```

Credit read from the vast.ai API, not from a local counter:

```
$74.82  at 15:48, before anything was rented
$74.01  at 17:32
------
$ 0.81  spent
```

**Under a $5 ceiling by a factor of six**, and the ceiling was a mechanism
(`rq budget --set`) rather than an intention. Both caps are restored at the end
of this task.


## R2-3018 — #67's remote arm, and the thing it found instead

The 26 units were submitted to the card the master probe was on — `rq exec`,
12 slots, the shipping path, the same 26 modules the original A/B used.
**Not one of them built.** All 26 came back:

```
ResourceWait: waited 603s for 20.0G of free memory and only 5.5G was ever
available — the container cap is /sys/fs/cgroup/memory.max, not the host's
`free`. The build was never started
```

Measured on instance `47189253` while it was serving the scene:

```
/sys/fs/cgroup/memory.max       63,803,752,448   =  59.4 GiB
/sys/fs/cgroup/memory.current   58,342,010,880   =  54.3 GiB   (91 % used)
/sys/fs/cgroup/cpu.max          3071999/100000   =  30.7 CPUs   (nproc says 32)
render worker RSS               53,035,096 kB    =  50.6 GiB
```

### Finding 1 — the film scene costs 50.6 GiB of host RAM, and the offer floor is 50 GB

**`film23_breach.blend` is 10.19 GiB on disk and 50.6 GiB resident.** The
project's only previous measurement of this was *"41.4-41.6 GB per process for
a 7.97 GB scene"* — this is the same ratio, on a scene 37 % larger, and it puts
the master's working set at **50.6 GiB on every card**.

`vastctl.MIN_CPU_RAM_GB` is **50.0**. **The offer filter will rent a box the
master cannot load.** The card this probe took has 59.4 GiB and sat at **91 %**
throughout — 8.8 GiB of headroom. A card at the floor has none, and a cgroup
OOM picks the largest RSS, which is the render worker.

**That is the one thing in this document I would fix before renting three
cards**, and it is a one-line change: raise `MIN_CPU_RAM_GB` to at least 64.

### Finding 2 — exec cannot share a card with a resident film scene

`EXEC_MIN_FREE_MEM_GB` defaults to **20.0** — a constant sized in
`exec_server.py`'s own header for *"twelve concurrent item builds ... 90 GiB
across twelve is 7.5 GiB each"*. A single item build measured **1.27 GiB RSS**
here. So the gate is roughly **15x** what one unit needs, and with a film scene
resident it can never open: 5.5 GiB free will never reach 20 GiB while the
worker holds 50.6 GiB.

The gate is right to exist — an over-committed exec batch would OOM-kill
somebody's 4K render, and the header says so. It is wrong to be a **constant**:
it refuses **one** 1.3 GiB build on a box with 5.5 GiB free.

### #67 — verdict

**NOT SETTLED, and the reason is a measurement, not a failure to try.** What
was established:

* the original unit set is exactly recoverable — 26 modules define
  `test_scene()` (R2-3007);
* the **local** half of the 1.68x has moved by **1.75x** since it was taken
  (R2-3013), which alone would put the ratio at ~2.96x and over the bar;
* the **remote** half cannot be re-taken on a card that is also holding the
  film scene — not because the box is too small, but because a 20 GB constant
  gate cannot see that one build needs 1.3 GB.

**To finish #67 costs about $0.30**: one dedicated CPU box with no scene
loaded, 26 units, 12 slots, and the wall clock compared against B12's 805.5 s.
It should not be run on a card that is rendering, and after this it cannot be.

**My recommendation is to run it — but AFTER the master is funded**, because it
buys build throughput for the item campaign and nothing for the master, and the
master is short.


## R2-3019 — the master cost, corrected for the RAM floor

R2-3018 says every card must hold **50.6 GiB** of resident scene. Re-pricing
the same 245.5 GPU-hours of work against the live market at **17:46** with
`VASTRENDER_MIN_RAM_GB=64` instead of 50:

```
 $/hr        id  geolocation          RAM GiB  cpu
0.4001  47185127  Thailand, TH            62.7  EPYC 9554 64-Core
0.4414  46937219  South Korea, KR        124.9  Ryzen 9 7950X 16-Core
0.4881  46307220  Estonia, EE            247.3  EPYC 7402 24-Core
0.4923  38769886  Massachusetts, US      125.2  Core i9-14900K
0.5347  31275126  Washington, US         125.7  EPYC 7452 32-Core
0.6014  47107854  Taiwan, TW             125.5  EPYC 9124 16-Core
0.7343  46790746  Japan, JP              251.4  —
```

| cards | $/GPU-hr | deploys | wall clock | **TOTAL** |
|---:|---:|---:|---:|---:|
| 1 | 0.4001 | 21 | 251 h = 10.4 d | **$100.33** |
| 2 | 0.4207 | 22 | 126 h = 5.2 d | $105.60 |
| **3** | 0.4432 | 21 | **84 h = 3.5 d** | **$111.14** |
| 5 | 0.4713 | 25 | 50 h = 2.1 d | $118.66 |

**Requiring more memory made it cheaper, not dearer** — the RAM-rich boxes
happen to be the cheap ones this hour. What it *did* cost is **depth**: only
**seven** offers on the whole market meet a 64 GB floor, so **a nine-card fleet
is not purchasable today at a memory the scene can actually load.** Three is.

*(A units warning inherited from `vastctl`'s own comment: the vast.ai query
takes `cpu_ram` in **GB** while the offer dict returns **MB**, so
`cpu_ram>=64` admits the 62.7 GiB Thailand box. Against a 50.6 GiB working set
that is 12 GiB of headroom, which is enough; if you want 64 **GiB** ask for
`>=69`.)*

**Final answer to "does $74.82 cover it":** no. **$111 at three cards, $100 at
one.** The shortfall is **$26 to $37** against the $74.01 now on the account,
and I would ask for **$120** so the master is not one slow host away from
stopping.


## R2-3020 — controls observed, and the state left behind

Four instruments were used here that could have passed vacuously. Each was
watched doing its job:

| control | observed |
|---|---|
| `rq budget --set` as a spend ceiling | set to `spent + $5.00` **before** the job was submitted, and printed `remaining $4.9984`; restored to $150 on both brokers at 17:47 |
| `tools/buildlock.sh` | took the lock, **queued my build behind eleven others for 22 minutes**, ran it, released it, printed `BUILDLOCK RELEASED ... rc=0` |
| the exec idle-timer clause | `16:46:39 idle 301s by the render queue, but 12 exec job(s) are in flight — NOT stopping the instance` |
| the broker's idle-down | `17:56:49 idle 300s — stopping instance (disk kept)` / `17:56:50 instance 47189253 stopped after 128.3 min running (~$0.789 gpu)` |

And one that **failed loudly and cost nothing**, which is the point: the first
26 `rq exec` submissions died on `argument --arg: expected one argument`
because `--arg --item` is read as a flag. Twenty-six refusals, zero jobs
created, zero dollars. Fixed with `--arg=--item` and resubmitted.

### State left behind

```
instance 47189253   STOPPED at 17:56:50 (GPU meter off), disk billing $0.037/hr
                    broker destroys it automatically at 21:56 unless used
                    -> film23_breach.blend stays staged, so a master started
                       on this card in the next 4 h skips a 13.6 min push
brokers             untouched: none started, none stopped, none restarted
caps                renderbroker $150.00, ladderbroker $150.00 — as found
jobs                every job created here is mine; the 26 exec jobs were
                    cancelled by me after all 26 returned ResourceWait
lease               docs/STAGING-R2-3001-to-R2-3060.md, held by r2-3001-throughput
```

**Nothing in `vast-render` was committed.** Its index already holds another
agent's staged work (`broker/app.py`, `broker/execservice.py`,
`worker/exec_server.py` and five more, 3,635 insertions). The four changes this
task recommends — `MIN_CPU_RAM_GB`, `prio`, `geolocation`, `push_parallel` —
are described precisely enough to apply, and are left for whoever owns that
branch.


---

## R2-3021 — the RAM floor is IN (`vast-render` `280f49a`)

Landed in `vastctl/vastctl.py`, committed **path-scoped** — `git commit -F ... --
vastctl/vastctl.py` — because that repo's index holds another agent's 3,635
staged insertions across eight files. Verified byte-identical before and after:
`8 files changed, 3635 insertions(+), 45 deletions(-)` both times.

```
MIN_CPU_RAM_GB          50.0 -> 72.0
SCENE_WORKING_SET_GIB   50.6      the measurement, as a constant, not as prose
RAM_HEADROOM            1.25
```

**Why 72 and not 56 or 64.** The exclusive 5090 market is bimodal and has a hole
in it. Surveyed today at five floors:

```
floor  50 GB -> 11 offers    RAM 62.7, 60.5, 124.9, 247.3, 251.5, 125.2 GiB
floor  64 GB ->  8 offers    RAM 62.7, 124.9, 247.3, 251.5, 125.2, 125.7
floor  72 GB ->  7 offers    RAM 124.9, 247.3, 251.5, 125.2, 125.7, 251.4
floor  80 GB ->  7 offers    (identical set)
floor  96 GB ->  6 offers    (identical set)
```

**Nothing is on sale between 63 GiB and 125 GiB.** Any floor above ~64 buys the
same tier, so 72 is simply the cheapest way to ask for it. 64 would keep one
62.7 GiB box in the set — 12 GiB of headroom on a scene that is still growing,
with 49 of 435 item modules built.

### The query term is not the check, and the units are why

`build_query` asks `cpu_ram>=72` and **vast.ai reads that as GB while the offer
dict answers in MB** — 7.4 % apart. A 64 "GB" floor admits a **62.7 GiB** box;
that was the cheapest offer on the market today. So the query narrows and a new
`_meets_scene_working_set` **decides, in GiB, on the returned dict**. Same
belt-and-braces as the existing `_within_bandwidth_ceiling`, for a better
reason: that one guards a term the API might ignore, this one guards a term the
API honours *in units we did not mean*.

A third gap the check absorbs: **the advertised figure is not the container's
cap.** Offer `43255050` sells 61.9 GiB; the container it produced reported
`memory.max` = **59.4 GiB**, 96 % of what was sold.

### The refusal, observed firing

A shortage now **raises** instead of falling through to the bandwidth error or
the co-tenancy warning — neither of which is about memory, and both of which are
confident. It names the floor, the measurement, the rejected offers with their
real RAM, and the market depth.

**Both controls were run, and control 2 is the load-bearing one — the query
floor was left LOW at 50 GB on purpose, so the GiB re-check is provably what
refused:**

```
CONTROL 1  shipped floor          -> 8 offers, 0 below 63.2 GiB   PASS
CONTROL 2  working set 400 GiB,
           query floor 50 GB      -> REFUSED                      PASS
   | REFUSING TO RENT: no exclusive RTX 5090 offer carries enough RAM ...
   |   need    400.0 GiB resident x 1.25 headroom = 500.0 GiB per GPU
   |   measured on instance 47189253 ... 50.6 GiB resident, on a 59.4 GiB
   |   cgroup cap running at 91 %
   |   rejected 30 offer(s): 43255050 (61.9 GiB, $0.3592/hr), ...
   |   NOTE: the exclusive market is bimodal ... nine is not purchasable
```

It also refuses on the record that it **deliberately contradicts
`search_offers`' own principle** — *"availability wins over preference"* — which
is right about exclusivity (a shared card renders, just riskily) and wrong about
RAM (a box that cannot hold the scene is not a degraded render, it is no
render).

### `vastctl offers` now shows RAM and geolocation

```
id         $/hr   rel    net Mbps   RAM GiB  disk$/GB  est 8h   geo                CPU
46979969   0.428  0.997  7082/14067 137.5    0.1333    $3.46    California, US     EPYC 9655 96-Core
46937219   0.441  0.981  784/649    124.9    0.2000    $3.89    South Korea, KR    Ryzen 9 7950X
46307220   0.488  0.995  926/968    247.3    0.2000    $4.00    Estonia, EE        EPYC 7402 24-Core
...
RAM floor 63.2 GiB/GPU (50.6 GiB measured resident x 1.25); 8 offer(s) cleared it.
```

`geolocation` has been in the offer dict all along and nothing read it — the box
this probe ran on advertised **734 Mbps** and had **254 ms RTT**. The column
makes the good choice visible: today's cheapest is also Californian.

### The master, re-priced at the enforced floor

| cards | $/GPU-hr | deploys | wall clock | **total** |
|---:|---:|---:|---|---:|
| 1 | 0.4276 | 21 | 251 h = 10.4 d | $107.23 |
| **3** | **0.4501** | 21 | **84 h = 3.5 d** | **$112.88** |
| 5 | 0.4661 | 25 | 50 h = 2.1 d | $117.36 |
| 8 | 0.5251 | 24 | 31 h = 1.3 d | $132.09 |

**$112.88 at three cards** — $1.74 more than the $111.14 quoted, because the
floor removed the two ~60 GiB boxes. **The $120 already quoted to the client
covers it**, and eight is now the purchasable ceiling: nine cards do not exist
at a memory this scene can load.

## R2-3022 — DEFECT for the log: the exec memory gate is a constant

`EXEC_MIN_FREE_MEM_GB` (`broker/execremote.py:65`) defaults to **20.0 GB** and
is a flat constant. It was sized in `exec_server.py`'s own header for *"twelve
concurrent item builds ... 90 GiB across twelve is 7.5 GiB each"*.

**One item build measures 1.27 GiB RSS** (`kerb_precast_unit`, this box, today).
So the gate is ~15x what a unit needs, and it cannot see that. With a film scene
resident there is 5.5 GiB free, and the gate **refuses one 1.3 GiB build on a
box that could run four**. All 26 units of #67's remote arm died on it:

```
ResourceWait: waited 603s for 20.0G of free memory and only 5.5G was ever
available — the container cap is /sys/fs/cgroup/memory.max, not the host's
`free`. The build was never started
```

The gate is right to exist — its header says an over-committed exec batch would
OOM-kill somebody's 4K render, and it would. It is wrong to be a **constant**
when the per-unit cost is measurable and the available memory is readable. It
should gate on `slots x measured-unit-RSS`, not on a number chosen for a
different box and a different scene.

**Not fixed here**: it lives in `broker/execremote.py` and `worker/exec_server.py`,
and `worker/exec_server.py` is one of the eight files another agent has staged
(807 insertions). Same reason `--prio 0` is not fixed here — `broker/app.py`
carries 139 of their staged insertions, so a path-scoped commit of it would
commit **their** work under my message. Both are one-line changes, both are
described precisely, and both belong to whoever owns that branch.


## R2-3023 — THE FIX IS ON DISK AND NOT IN FORCE. Restart the brokers.

`MIN_CPU_RAM_GB` is a module-level constant read at **import** time, and it is
also bound as a default argument in `search_offers` — bound when the function is
defined, i.e. when the module is imported. **Every broker process now running
imported the old file and holds 50.0 in memory.**

```
vastctl.py modified                 18:05:03 today
renderbroker  pid 1960091  started  Sat Aug 8 04:10:27
ladderbroker  pid  677451  started  Tue Aug 4 20:20:55
fleet03       pid 1974220  started  Sat Aug 8 05:31:20
fleet08       pid 1974442  started  Sat Aug 8 05:31:35
fleet11       pid 1985431  started  Sat Aug 8 05:53:18
```

Every one predates the edit by hours or days. What they imported, from git:

```
280f49a^  MIN_CPU_RAM_GB = float(... or 50.0)     <- what all live brokers hold
HEAD      MIN_CPU_RAM_GB = float(... or 72.0)     <- what a NEW process gets
          fresh import -> MIN_CPU_RAM_GB=72.0, floor=63.2 GiB/GPU
```

**So the master must be launched on brokers started after 18:05, or the floor
does not apply and the whole of R2-3021 is decorative.** This is the failure
shape this project has hit a dozen times — an instrument that exists and is not
in the path — and it would be silent: a broker with the old constant rents a
60 GiB box and logs a perfectly confident rent line.

`fleetctl up` starts brokers 3..n+2 via `scripts/brokerd.sh`, so a fleet brought
up fresh for the master picks the new floor up by construction. **A fleet reusing
the nine brokers already running since 05:31 does not.** Check before renting:

```bash
# each fleet broker must have started AFTER vastctl.py was modified
ps -o pid,lstart= -p <broker pid>
```

**I have not restarted anything.** Brokers 3-11 and the two protected ones are
other agents' processes with other agents' work on them; `fleetctl down`/`up` on
the fleet is the owner's call, and `rq status` showed fleet08 renting a card at
17:58 while I was writing this.


## R2-3024 — NEAR MISS: the process tree and the scratchpad are SHARED between agents

Cleaning up my own stale poll loops, I listed the children of the `claude`
process (pid 2690886) intending to kill them by PID. **Two of them were not
mine.**

```
PID 2830931  alive 49:34   bash .../scratchpad/r2941/chain2.sh
                           -> r2970-control, r2970-px-after2, r2970-macro-before,
                              r2970-var-before, r2970-macro-after, ...
                              a SEVEN-STAGE buildlock chain, 46 minutes in
PID 2879170  alive 02:55   until [ -f $SP/ship_step.json ] ...
PID 2879465  alive 02:24   grep -E "grass library:|TOTAL|^VEG |CHAIN2 DONE|..."
```

**Every agent in this session is a child of the same process and writes to the
same scratchpad directory** — `/tmp/claude-0/…/262f2abe-…/scratchpad/` is
session-scoped, not agent-scoped. So:

* **"it is a child of my claude PID" is NOT an ownership test.** A PID sweep of
  my own children would have killed another agent's 46-minute seven-stage build
  chain mid-flight — the exact incident class already in the brief ("a blanket
  cancel once took four jobs from three owners").
* **The scratchpad is a shared namespace.** `scratchpad/inspect.py`, written by
  another agent, shadowed the standard library's `inspect` and crashed my
  transport A/B on import (`ModuleNotFoundError: No module named 'bpy'` from
  inside `dataclasses`). Fixed by running from a private subdirectory —
  `scratchpad/r23001/` — which is what any agent writing an importable `.py`
  there should do.

**The only safe stop mechanism is the task ID**, because that is the one handle
scoped to the agent that created it. Six stale waiters of mine were stopped that
way (`b79artu6z`, `bl4k889g3`, `bkvt7l1wf`, `bh7fhgo89`, and two the harness
reaped itself). **Nothing belonging to another agent was touched, and the check
that established that is in this section rather than in my head.**

