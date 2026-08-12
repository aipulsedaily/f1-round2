# STAGING R2-3901 to R2-3960

## R2-3901 — HANDOVER TAKEN MID-CYCLE-3, AND THE ORPHAN MODEL IS NOW MECHANICAL

Picked the master up at **2026-08-10 16:55Z** from an agent terminated by an API
limit. **The render never stopped.** State read, not inherited:

| | |
| --- | --- |
| frames on disk | **1,376 / 2,978 (46.2%)** |
| credit | $117.45 |
| blend | `film25_breach.blend` sha16 `1d2aa2d86533574e` on assembly15 |
| burn | $1.0444/hr across the live cards, 112.5 h of runway |

`fleetctl status` at 16:55Z showed **two** cards running and fleet05 with none —
which is cycle 3 in progress, not a fault.

### Cycle 3, and it did not follow the cycle-1/2 script

**fleet03 was down 7 minutes 58 seconds, not 35-70.** The whole thing:

| when | what |
| --- | --- |
| 16:40:02 | f542 delivered normally |
| 16:40:15 | tunnel to 47334620 refused; broker logs `UNKNOWN, not dead` and reopens |
| 16:40:16 | tunnel repair fails → `deploying onto existing instance (attempt 1/3)` |
| 16:42:55 | 3 consecutive missed beats → reconcile → **instance does not exist on vast.ai** |
| 16:44:16 | `SshNeverReady` on the dead endpoint → second confirmation it is gone |
| 16:44:17 | offer 38597207 (machine 43130) rented, $0.468/hr, EXCLUSIVE |
| 16:45:29 | reachable in 72 s |
| 16:45:40 | blender bundle pushed, 10.7 s @ 45.15 MB/s |
| 16:47:53 | **scene uploaded in 111.9 s @ 97.9 MB/s** |
| **16:48:13** | **`worker ready`** — deploy finished in 163.6 s |
| 16:55:33 | f543 delivered |

**The 900 s `unknown_grace` was never spent.** Because a deploy was already in
flight when the card vanished, the broker reached its verdict through the
`SshNeverReady` path (240 s) and the heartbeat reconcile (3 beats) instead of
through `await_render`'s silence timer. That is the same mechanism arriving by a
shorter road, and it is why this cycle cost 8 minutes rather than 35.

**The scene push ran at 97.9 MB/s — roughly 3x this render's previous best** and
23x fleet05's cycle-2 worst (4.2 MB/s). R2-3864's diagnosis is confirmed from
the other direction: fleet05 had **no card at all** in this window, so nothing
was competing for the uplink and one stream got the whole pipe. The 7:1 split is
contention, not a property of any host.

**And no frame was orphaned.** f543 was in flight at the drop and was re-rendered
on the new card, costing **436.4 s against a 225 s baseline** — the interrupted
attempt plus the real one. fleet03's gaps are still exactly `[192, 355]`.

### THE ORPHAN RULE, NOW READ OFF THE PLAN LINES RATHER THAN INFERRED

R2-3861 said a lost frame is only recovered if the **job** is requeued. Every
`N frame(s) requested, M already delivered` line each broker has ever written,
for `master4k`:

| broker | plan lines for its master4k job | gaps below its high-water mark |
| --- | --- | --- |
| fleet03 | **one**, `04:06:31` on 08-09: 993 / 0 / 993 | **192, 355** |
| fleet04 | **four** — 08-09 04:07 (993/0/993), 08-09 16:30 and 16:37 (993/139/854), 08-10 05:00 (993/277/716) | **none** |
| fleet05 | 08-09 04:07 (992/0/992), cancelled 04:27 for the R2-3850 beat-6 re-order, `dbc2c783eb28` from 08-09 04:45 (992/5/987) — **and nothing since** | **2127, 2292** |

**fleet04 is the only broker whose job has ever been recomputed from disk, and
fleet04 is the only broker with zero gaps.** The correlation is total and the
mechanism is stated: a requeue re-reads the delivered files and rebuilds the
todo, so it sweeps up its own casualties; a transport-only failure resumes the
same in-memory todo list, which never contained the lost frame.

So the orphan count is not a rate to be estimated — it is a consequence of which
recovery path each card took:

- **fleet03 and fleet05 will each report `COMPLETE` while short.** fleet03 will
  finish 991 of 993, fleet05 correspondingly short of 987.
- **fleet04 will be genuinely complete** unless it orphans one after its last
  requeue.

**Confirmed orphans at 1,376 frames: 192, 355, 2127, 2292.** fleet05's cycle-3
casualty is expected to be **2417**, which was in flight at its 16:41:27 drop; it
will show as a gap once fleet05 passes it.

**This does not change the endgame.** Step 1 of R2-3858 — re-submit `master4k`
and confirm 2,978 of 2,978 — recovers all of them, because a fresh submission
under the same `--name` computes its todo from files on disk. It is ~1.5-2 h of
real rendering, and it is the step that makes the difference between a film and
a film with holes in it.

### fleet05's cycle 3, in progress at the time of writing

| when | what |
| --- | --- |
| 16:40:44 | f2416 delivered normally |
| 16:41:27 | heartbeat 1/3, and the job socket hits `ConnectionDropped` mid-f2417 |
| 16:43:28 | 3 consecutive misses → reconcile → instance 47334687 gone |
| 16:56:44 | **offer 46937219 re-rented — machine 131197, the same machine it was retired off**, $0.455/hr, EXCLUSIVE, 838 Mbps up |
| 16:57:31 | instance 47389166 provisioning; scene cache budget derived on the new card |

The fleet is back to **three cards at $1.5200/hr ($36.48/day)** against $117.38
of credit — **77.2 h of runway** for a tail that needs roughly 43. fleet04 is the
expensive one at $0.5556/hr and is the card due to retire next, so if anything
the blended rate is about to improve.

fleet04 was at 11.92 h of uptime at 16:55Z and is due to retire imminently, so
its push may collide with fleet05's. Under R2-3864 that is the 35-70 min case,
not a deviation, and it is not worth reporting unless it runs past 70.

## R2-3902 — CYCLE 3 CLOSED, AND THE ORPHAN LEDGER IS NOW A TOOL WITH A FALSIFIABLE PREDICTION

### Cycle 3, all three cards, measured to `worker ready` rather than to "running"

| broker | went silent | `worker ready` | **down** | frame orphaned |
| --- | --- | --- | ---: | --- |
| fleet03 | 16:40:15 | **16:48:13** | **7 m 58 s** | none — f543 re-rendered at 436.4 s vs a 225 s baseline |
| fleet05 | 16:41:27 | **17:05:21** | **23 m 54 s** | pending — cursor still 2416 |
| fleet04 | 17:01:18 | *in its grace window* | — | — |

**Both closed cards came back faster than the 35-70 min band**, and neither is a
deviation worth reporting. The reason fleet03 took 8 minutes is mechanical: a
deploy was already in flight when the card vanished, so the verdict arrived
through `SshNeverReady` (240 s) plus the 3-beat reconcile instead of through
`await_render`'s 900 s silence timer. **The grace is an upper bound on how long
the broker will wait for a silent worker, not a fixed cost.**

fleet04 re-rented onto machine 8449 at $0.535/hr in cycle 2 and its retirement
at 17:01 is on schedule. **No host has been condemned this cycle** — the running
total stays at 3 bad hosts in 14 rentals.

### `tools/r23901_orphan_ledger.py` — the ledger, and the test it sets up

R2-3901 established the rule by reading plan lines by hand. It is now a tool, so
that the check is repeatable and so the endgame has a **number to be wrong
about**. It reconstructs each broker's live job from its own delivery stream,
finds the frames that stream skipped, and keeps only those that are also absent
from disk — i.e. dropped in flight and on no todo list anywhere.

Output at 17:15Z, 1,380 frames in:

```
broker    live job         cursor done/todo    plans  orphans
fleet03   d3b1b8bde2f4        546  544/993         1  [192, 355]
fleet04   467247848cc6       1397  127/716         4  none
fleet05   dbc2c783eb28       2416  427/987         3  [2127, 2292]

ORPHANED (on no todo list, only a re-submission recovers these): [192, 355, 2127, 2292]
PREDICTED 'to render' ON RE-SUBMISSION = 1598  = 4 orphaned + 1594 not yet rendered
```

It reproduces the four orphans that were found by hand, from a different route,
and **the plan-line count column carries the mechanism in one number**: fleet04
has 4 plan lines and no orphans; the two brokers with a single live plan line
have two orphans each.

**The test, stated before the answer is available.** At re-submission the broker
prints `2978 frame(s) requested, N already delivered, K to render`. **K must
equal the ledger's prediction.**

- **K > predicted** — something other than retirement is dropping frames.
  **Stop. Do not encode. Escalate.**
- **K < predicted** — the gap reader is wrong and the coverage claim is unfounded.
  **Stop.**
- **K = predicted** — the model is confirmed and the re-render is the known
  recovery of known casualties.

This is worth more than a re-submission that simply "renders whatever is
missing", because that version cannot tell a retirement casualty from a defect.

### THE `COMPLETE` LINES ARE GOING TO BE WRONG, BY CONSTRUCTION

Stated plainly so nobody downstream reads one as coverage: **fleet03 will report
`COMPLETE` at 991 of 993 and fleet05 short by however many it orphans.** Those
lines will be accurate about each job's own todo list and false about the film.
**Only the re-submission plus `fleetctl verify --manifest` against the 1-2978
range is coverage.**

## R2-3903 — THE ENCODE COMMANDS WERE DESCRIBED BUT NEVER WRITTEN DOWN, AND ARE NOW RECOVERED BYTE-EXACTLY

**Recorded, NOT run.** The client has asked to review the frame set before the
film is cut, so nothing below has been executed beyond four-frame reconstruction
probes.

R2-3858 says *"both ffmpeg command lines with their measured output sizes"* are
at R2-3854. **They are not.** R2-3854 describes the encodes — profile, bitrate,
the `setparams`, the concat form — but the literal command lines appear nowhere
in the repository. That is a real gap: at 4am it would have been reconstructed
from prose.

So they were recovered from the validated artefacts themselves and **proved by
byte-comparison**, which is a stronger check than re-reading a command:

**ProRes 422 HQ — reproduces `tmp/r23841_encodetest/rate4k_prores422hq.mov` byte for byte:**

```
ffmpeg -r 24 -f concat -safe 0 -i FRAMES.ffconcat \
  -vf "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,\
scale=in_range=full:out_range=tv:out_color_matrix=bt709" \
  -c:v prores_ks -profile:v 3 -vendor apl0 -pix_fmt yuv422p10le \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -i audio/out/master.wav -map 0:v:0 -map 1:a:0 -c:a copy OUT.mov
```

**`-vendor apl0` is the detail that would have been lost.** The first
reconstruction differed from the reference in exactly **16 bytes — four per
frame**, at the same offset in each ProRes frame header: octal `141 160 154 60`
(`apl0`) against `114 141 166 143` (`Lavc`). Decoded pixels were already
bit-identical (PSNR `inf`); only the creator ID differed. With `-vendor apl0`
the file is **byte-identical to the reference**. Some NLEs treat ProRes without
the Apple creator ID as third-party, so this is not cosmetic.

**H.265 — reproduces the reference's every tag and its size to 0.03%:**

```
ffmpeg -r 24 -f concat -safe 0 -i FRAMES.ffconcat -i audio/out/master.wav \
  -map 0:v:0 -map 1:a:0 \
  -vf "setparams=...,scale=in_range=full:out_range=tv:out_color_matrix=bt709" \
  -c:v libx265 -preset slow -pix_fmt yuv420p \
  -b:v 55M -maxrate 60M -bufsize 120M -tag:v hvc1 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 192k -movflags +faststart OUT.mp4
```

Not byte-identical, and **should not be expected to be** — x265 runs
`frame-threads=2` with WPP, so its output depends on thread scheduling. The
deliverable that must be reproducible is the ProRes master, and that one is.

**Two settings recovered that no document records**, both read out of the x265
SEI options string in the reference file rather than guessed:

- **`-preset slow`**, not medium: `ref=4 rc-lookahead=25 rd=4 subme=3 me=3
  merange=57 rdoq-level=2 max-merge=3 limit-refs=3` is the `slow` row exactly.
- **`-tag:v hvc1`** (not `hev1`) and `+faststart` — confirmed by
  `codec_tag_string=hvc1` and `ftyp/moov/free/mdat` atom order.

**The `setparams` defect reproduced on demand.** Encoding the same four frames
**without** it, with `-color_trc bt709` still on the command line, yields
`color_transfer=iec61966-2-1` — the PNG decoder's tag wins. That is R2-3854's
claim, reproduced rather than inherited.

### ENCODE RATES, MEASURED ON REAL 4K FRAMES — a number nobody had

Timed on the four reference 4K frames, on this box, **at load ~4.5-5.2 with two
brokers pushing 11 GB scenes**, so these are pessimistic:

| output | measured | extrapolated to 2,978 frames |
| --- | --- | --- |
| ProRes 422 HQ | 2 s / 4 frames = **0.50 s/frame** | **~25 min** |
| H.265, preset slow | 15 s / 4 frames = **3.75 s/frame** | **~3.1 h** |

**The H.265 pass is a three-hour job, not a footnote**, and it is the one
R2-3854 warns dies under CPU contention. It should be run on an idle box, after
the fleet is down. The ProRes master is cheap by comparison.

### The audio master, re-checked on disk rather than at mux time

```
md5  d5087fd021b5f748f176ecb2b6c1de67   35,736,044 B
     pcm_s24le, 48 kHz, stereo, duration 124.083333 s
```

**Unchanged**, and exactly `2978/24 = 1489/12 = 124.083333 s` of picture. No
`-shortest`, no padding, `-c:a copy`.

## R2-3904 — CYCLE 3 CLOSED ON ALL THREE CARDS, AND f2417 WAS PREDICTED BEFORE IT EXISTED

**Every card has logged `worker ready`.** That is the bar R2-3864 set after
cycle 2 was declared closed while a card was still 68.5 minutes down, and it is
the bar this cycle is measured against — not "the API says running", not "a
frame line appeared".

| broker | went silent | `worker ready` | **down** | replacement | host condemned |
| --- | --- | --- | ---: | --- | --- |
| fleet03 | 16:40:15 | 16:48:13 | **7 m 58 s** | machine 43130, $0.468/hr | none |
| fleet05 | 16:41:27 | 17:05:21 | **23 m 54 s** | machine 131197, $0.455/hr | none |
| fleet04 | 17:01:18 | 17:24:44 | **23 m 26 s** | machine 44842, $0.455/hr | none |

**The whole cycle cost 23 m 26 s of wall clock, not 35-70**, because the three
cards retired 21 minutes apart rather than within 61 seconds of each other, so
**no two scene pushes overlapped.** fleet03 uploaded at 97.9 MB/s and fleet04 at
a comparable rate; nothing saw fleet05's contended 4.2 MB/s from cycle 2. R2-3864
predicted exactly this — the 7:1 split is contention, not a host property — and
the staggering it recommends as a mitigation **has now happened by itself**,
because each re-rent resets that card's 12-hour clock to when it was rented.

**This is the first cycle with no condemned host.** The running base rate stays
at 3 bad hosts in 14 rentals; it is now 3 in 17. And the fleet came back
**cheaper**: fleet04 replaced a $0.535/hr card with a $0.455/hr one, so the
blended rate fell rather than walking further up the blacklist ladder.

fleet04's re-rent fired at **17:16:27 against a predicted 17:16:18** — the
`unknown_grace` clock from its 17:01:18 drop, correct to **9 seconds**.

### The ledger's first real prediction, made before the fact and confirmed

At 17:15Z, with fleet05's cursor still at 2416, R2-3902 recorded that its
cycle-3 casualty was **expected to be 2417**. fleet05 has now delivered past
that point:

```
fleet05   dbc2c783eb28       2420  430/987         3  [2127, 2292, 2417]
```

**2417 is on no todo list, exactly as predicted, and the count moved 4 -> 5.**
The mechanism is not a story fitted to the data afterwards; it forecast a
specific frame number and the frame number is what appeared.

Revised prediction, which is the number the re-submission must reproduce:

```
ORPHANED: [192, 355, 2127, 2292, 2417]                       count = 5
PREDICTED 'to render' ON RE-SUBMISSION = 1592 = 5 orphaned + 1587 not yet rendered
```

**Expect roughly two more orphans per remaining cycle, not three** — fleet04's
job requeues on every retirement and so recovers its own casualty, while fleet03
and fleet05 do not. With ~3 cycles left that projects **10-11 orphans** at the
end, and ~1.5 h of re-rendering to recover them.

## R2-3905 — THE VERIFICATION PASS, TIMED AND WITH ITS INTERPRETER PINNED

Rehearsed again at 1,397 frames rather than the 13 of R2-3856, to get a real
cost for the endgame and to catch anything that only breaks at scale.

**The interpreter is not `python3` and is not the broker's venv.** Both fail,
differently, and the failure is silent until it isn't:

| interpreter | numpy | PIL | usable |
| --- | --- | --- | --- |
| `python3` | yes | **no** | no |
| `/home/zany/vast-render/.venv/bin/python` | **no** | — | no |
| **`/home/zany/f1-round2/.venv/bin/python`** | **2.5.1** | **12.3.0** | **yes** |

The tool's own docstring says `.venv/bin/python` relative to `f1-round2`, which
is correct; it is only ambiguous if it is read from another directory. **Pinned
here as an absolute path** so the endgame does not spend a turn on a
`ModuleNotFoundError`.

**Timing: 552 frames decoded in 100 s at load 5.76 → 0.181 s/frame → ~9 minutes
for all 2,978.** Cheap enough that there is no reason to sample rather than
decode everything.

**One behaviour worth knowing before it is read as a defect:** `--first/--last`
does **not** restrict which files are decoded — the tool decodes every PNG in
every `--dir` it is given and uses the range only to classify coverage. Running
it on one broker's directory with `--first 1 --last 100` therefore reports
`452 out of range` and `STAGE RESULT: FAIL`, which is correct and is not a
finding. With all three directories and `--first 1 --last 2978`, `outside range`
must be **0**.

**The interim quality signal is good.** All 552 of fleet03's delivered frames
decode at **3840x2160**, none failed to decode, **0 flat, 0 black**, luminance sd
0.132-0.259 and 194-256 distinct levels. That is the whole delivered showroom
block, not a sample, and it is the check `fleetctl verify` structurally cannot
make.

## R2-3906 — THE REBALANCE IS NOW PRICED, AND THE ANSWER IS TO LEAVE IT ALONE

R2-3858 carries the work-conserving rebalance as remaining step 2, deferred
until a card is genuinely idle because R2-3859 showed the split must not be
predicted from measured s/frame. A card is about to be idle, so it is time to
price it rather than inherit the plan.

Rates measured at 18:18Z as each broker's mean over its own last 10 frames:

| broker | s/frame | done / todo | left | hours | finishes |
| --- | ---: | --- | ---: | ---: | --- |
| fleet03 | 280.3 | 558/993 | 435 | **33.9** | **2026-08-12 ~04:15Z** |
| fleet05 | 302.9 | 440/987 | 547 | 46.0 | 2026-08-12 ~16:20Z |
| fleet04 | 343.8 | 136/716 | 580 | **55.4** | **2026-08-13 ~01:45Z** ← the film lands here |

**fleet03 goes idle ~21.5 h before the film finishes.** On the face of it that
is the rebalance's whole case.

### The cost argument for rebalancing does not survive contact with the config

`broker/config.py` runs a three-stage lifecycle on an idle instance:

```
IDLE_GRACE_SEC = 300     running -> stopped   (GPU billing ends immediately)
HIBERNATE_SEC  = 3600    stopped -> destroyed (disk ~$0.014/hr in between)
```

**So fleet03 stops billing for GPU five minutes after its last frame and is
destroyed an hour later, without anyone doing anything.** The 21.5 idle hours
cost approximately **$0.30 of disk**, not the ~$10.50 of GPU an idle rented card
would imply. **There is no money in the rebalance.** What it buys is roughly
**10 hours of wall clock** and nothing else.

### And I cannot perform it anyway, which is the right outcome here

The rebalance requires cancelling and resubmitting fleet04's job so its tail is
disjoint from the chunk handed to fleet03. **I did not create that job**, and the
standing constraint is not to cancel, stop, destroy or reuse a broker, job or
instance I did not create. Racing instead — handing fleet03 a chunk of fleet04's
tail *without* cancelling fleet04's job — is the specific mistake R2-3859 warns
against: both cards would render the same frames, and the only outcomes are
wasted GPU and `duplicated` rows in the manifest.

**Recommendation: do nothing.** The brief states there is no time pressure and
that holding a paid render is preferable to delivering something unverified. Ten
hours of wall clock is not worth an intervention into a recovery path that has
now survived three retirements untouched, on a job I did not start, to save
$0.30.

### Budgets — checked because a paused broker is a reportable event

| broker | cap | spent | remaining | needs | headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
| fleet03 | $42.00 | $19.94 | $22.06 | 33.9 h x $0.4889 = **$16.57** | $5.49 |
| fleet04 | $63.49 | $25.29 | $38.20 | 55.4 h x $0.4550 = **$25.21** | $12.99 |
| fleet05 | $53.00 | $23.31 | $29.69 | 46.0 h x $0.4756 = **$21.88** | $7.81 |

**No broker will hit its own cap**, so none will pause. Caps still sum to
$158.49, the invariant R2-3862 established.

**Fleet projection: $68.55 spent + $63.66 to go = $132.21 against caps**, which
net of the $8.49 of pre-existing banked spend is **$123.7 of the $150 new-spend
ceiling — a 17.5% margin.** That is inside the brief's ~$122 projection and is
**not** threatening $150. Retirement gaps do not bill, so remaining cycles move
the wall clock without moving this number.

## R2-3907 — THE BAD-HOST BLACKLIST IS PER-BROKER, AND THE FLEET PAID FOR THE SAME BROKEN MACHINE TWICE

**Reportable event: a card was condemned.** It cost 4 min 50 s and ~$0.05, and
the interesting part is not the bad host — it is *why the fleet bought it again*.

```
state4  04:54:26 (08-10)  renting offer 46307220 (machine 142281)
state4  05:00:04          machine 142281 refuses our ssh key -> blacklisted for this session
state4  05:00:14          offer 46307220 blacklisted -- "still the cheapest, the next rent
                          would buy it straight back"
state5  05:02:17 (08-11)  renting offer 46307220 (machine 142281)      <-- same offer
state5  05:06:57          machine 142281 refuses our ssh key -> blacklisted for this session
state5  05:07:07          offer 46307220 blacklisted for this session
```

R2-3861 praised the double blacklist — machine *and* offer — as "the detail that
makes the recovery terminate", and it does. **But it terminates only for the
broker that learned it.** The blacklist is session-scoped state inside one
broker process, so fleet05 had no knowledge of fleet04's verdict from 24 hours
earlier and bought the same box. **Every broker must rediscover every bad host
independently**, and with three brokers the fleet can pay for the same broken
machine up to three times.

**The host has not been repaired in 24 hours**, which strengthens R2-3863 rather
than contradicting it. fleet04's verdict on 08-10 and fleet05's on 08-11 are the
same machine, the same offer, the same failure — `sshd` completes the handshake
and denies publickey, so `authorized_keys` was never written. It is a durable
property of machine 142281, not a transient.

**The discriminating signal again arrived long before the timeout.**
`Permission denied` was in the log at **05:03:44, 55 s after renting**; the
verdict was not reached until **05:06:57**, on the 240 s `SshNeverReady` budget.
R2-3863 already recorded that a ~30 s cut-off would reach the same verdict and
save ~3.5 min per bad host. This is the fourth instance of that, and the
argument is now worth ~14 min across the render. **Still not worth changing
middleware under a live render** — recorded for whoever tunes this next.

**Base rate: 4 bad hosts in 19 rentals, ~21%**, unchanged from R2-3863's 3 in 14.

**Exposure that remains:** fleet03 has never drawn machine 142281 and its
blacklist does not contain it. If it draws that offer on a future retirement it
will pay the same ~5 min. There are 2-3 cycles left, so this is a small,
bounded, known cost — not something to intervene over.

### Cycle 4 in progress, all three cards, and the fleet has re-synchronised

| broker | dropped | re-rented | note |
| --- | --- | --- | --- |
| fleet03 | 04:45:52 | 05:01:10 (predicted 05:00:52, **+18 s**) | took machine 131197, which fleet05 released 91 s earlier |
| fleet05 | ~04:56 | 05:02:17 -> condemned -> re-renting | machine 142281 |
| fleet04 | due ~05:16 | — | at 11.75 h |

**Cycle 3's helpful stagger is gone**: all three cards now retire inside ~30
minutes, so their 11 GB scene pushes will compete for the uplink again. Under
R2-3864 that is the 35-70 min case. Report thresholds set at fleet03 05:55Z,
fleet05 06:06Z, fleet04 06:26Z.

## R2-3908 — THE BAD HOST REPAIRED THE ORPHANS, AND MY LEDGER HAD BOTH A BUG AND A BLIND SPOT

The condemnation at R2-3907 had a consequence I did not anticipate and which
runs the opposite way to the cost:

```
05:07:13 ERROR broker  job dbc2c783eb28 requeued: sequence master4k stopped at
                       frame 2127 ... FleetUnavailable: deploy failed on freshly
                       rented instance
05:07:13 INFO  broker  sequence master4k job dbc2c783eb28: 992 frame(s) requested,
                       563 already delivered, 429 to render
```

**It stopped at frame 2127 — which is one of fleet05's own orphans.** A deploy
failure requeues the job; a requeue recomputes the todo **from the files on
disk**; and the lowest frame absent from fleet05's block is 2127. So all three of
its casualties — **2127, 2292 and 2417** — are back on a todo list and will be
rendered by the running fleet.

**The broken host paid for itself.** It cost 4 min 50 s and ~$0.05, and in
exchange it converted three permanent orphans into scheduled work, saving ~15
minutes of re-render at the end. That is luck, not design, and it is only worth
recording because it confirms the mechanism in the **recovering** direction:
R2-3861 said a requeue sweeps up its own casualties, and this is the first time
one has been observed doing so for frames orphaned in *earlier* cycles.

### Two defects in my own instrument, found by running it

**1. It crashed on a requeued-but-not-yet-delivering job.** The empty-stream
branch built a dict without `done_in_pass`/`todo`/`plan_lines` and the report
line raised `KeyError`. Fixed: that state now prints `cursor = requeued` and
**orphans = none**, which is the correct reading — a job whose todo was just
recomputed from disk can orphan nothing, because every absent frame in its block
is back on the list.

**2. I was not running it often enough, and it cost me twelve hours of
accuracy.** `fleet04` orphaned **f1398** at its cycle-3 retirement (~17:25 on
08-10). At 17:24 the ledger correctly said `none`, because fleet04's cursor was
still 1397 and it had not yet passed the gap. **I did not run it again until
05:10 today**, so an orphan sat undetected for ~12 h. It was never *lost* — the
re-submission recovers it regardless — but a ledger that is only consulted
occasionally is not a ledger.

**Fixed structurally rather than by intending to remember:** the 30-minute pulse
now runs the ledger every cycle and emits a line **only when the orphan set
changes**. Silence means unchanged; a change announces itself.

### The ledger now, and the revised prediction

```
broker    live job         cursor done/todo    plans  orphans
fleet03   d3b1b8bde2f4        696  694/993         1  [192, 355]
fleet04   467247848cc6       1515  244/716         4  [1398]
fleet05   dbc2c783eb28   requeued    0/429         5  none

ORPHANED: [192, 355, 1398]                                    count = 3
PREDICTED 'to render' ON RE-SUBMISSION = 1200 = 3 orphaned + 1197 not yet rendered
```

**The count went 5 -> 3, not 5 -> 7.** fleet03 remains the only broker whose job
has never been requeued, and it is the only one accumulating casualties
monotonically; its cycle-4 frame (f697) will surface as a fourth once its cursor
passes it.

## R2-3909 — CYCLE 4 CLOSED, AND `FAILED` IS THE ORPHAN MECHANISM WEARING ITS OWN NAME

**Every card has logged `worker ready`.**

| broker | dropped | `worker ready` | **down** | notes |
| --- | --- | --- | ---: | --- |
| fleet03 | 04:45:52 | 05:15:45 | **29 m 53 s** | deploy 831 s — uplink shared again |
| fleet05 | 04:57:50 | 05:18:06 | **20 m 16 s** | *including* a condemned host and two rentals |
| fleet04 | 05:17:04 | 05:41:29 | **24 m 25 s** | same machine 44842, $0.455/hr |

**Worst card 29 m 53 s, against a 35-70 min band.** Four cycles have now run and
none has reached 35 minutes since cycle 2's 68.5. The stagger closed to ~30 min
this cycle and the pushes did overlap — fleet03's deploy went from 164 s to
831 s — and it still came in under the band, because a shared uplink slows a
push without stalling it.

### The `FAILED` lines are the orphan mechanism, correctly labelled

`sequence master4k frame N FAILED (~1100-1260s, 1 consecutive)` has now appeared
**once per cycle on fleet04** and is not a defect. The broker's own text is
exact: *"the instance has not answered a single progress probe for 15.0 min while
reattaching. This is a TRANSPORT failure, not a statement about the render."*
It is `await_render` spending its grace on a card that no longer exists.

| frame | cycle | outcome |
| --- | --- | --- |
| f1133 | 1 | recovered — a later deploy failure requeued the job |
| f1271 | 2 | **on disk** — recovered by fleet04's 05:00:20 requeue |
| f1398 | 3 | **orphan** — job continued in place |
| f1517 | 4 | **will orphan** — no requeue line follows and it is absent from disk |

**A correction to R2-3901, which was too strong.** I wrote that fleet04 "is the
only broker whose job has ever been recomputed from disk" and framed that as a
property of the broker. It is not. **fleet04 requeues only on a *deploy*
failure; on a transport-only failure it continues in place exactly like the
others.** That is why f1133 and f1271 came back while f1398 and f1517 do not.
The rule is about **which failure path the cycle took**, not about which broker
took it — and R2-3908's fleet05 requeue, triggered by a condemned host, is the
same rule seen from the other side.

The corrected statement of the mechanism:

> **A retirement orphans its in-flight frame unless something later forces that
> broker's job to requeue.** A deploy failure forces it; a transport failure does
> not. Nothing about the identity of the broker predicts which one happens.

Orphan set will reach `[192, 355, 697, 1398, 1517]` when fleet04 passes 1517.
The pulse announces changes, so this needs no further watching.

## R2-3910 — AN UNBUYABLE OFFER IS WALKING THE PRICE UP, AND fleet05 WILL HIT ITS CAP

### Offer 46851284 is not a race. It is persistently unbuyable, and it is not blacklisted.

I reported it at 17:17 as a lost race and said the listing was "evidently still
live and the earlier 400 was a transient". **That was wrong, and the next
re-rent disproved it twelve minutes later.**

```
state3  17:17:35  renting offer 46851284 (machine 53711) — $0.455/hr
state3  17:17:35  offer 46851284 could not be created (HTTPError: 400) — trying the next
state3  17:17:35  renting offer 36318699 (machine 46633) — $0.529/hr      <- +16%
state5  17:29:06  renting offer 46851284 (machine 53711) — $0.455/hr
state5  17:29:07  offer 46851284 could not be created (HTTPError: 400) — trying the next
state5  17:29:07  renting offer 46285754 (machine 34481) — $0.668/hr      <- +47%
```

**Two brokers, twelve minutes apart, same offer, same 400.** If it were a race
lost to another buyer the listing would have gone; instead it is still the
cheapest qualifying offer and it 400s every time it is asked for.

**And nothing blacklists it.** The broker blacklists an offer it *destroyed as
unusable* — R2-3861's "the detail that makes the recovery terminate" — but a
create that returns 400 never produces an instance to destroy, so that path is
never reached. **The offer therefore stays at the top of the cheapest-first list
and will be selected again on every future re-rent**, costing one rung up the
price ladder each time. It has now cost two.

This is the same shape of defect as R2-3907's per-broker blacklist: the recovery
is correct, terminates, and does not learn.

### The consequence: fleet05 will hit its own cap and pause

| broker | cap | spent | remaining | work left | needs | verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| fleet03 | $42.00 | $31.29 | $10.71 | 121 fr, 12.7 h @ $0.5502 | $6.97 | ok |
| fleet04 | $63.49 | $36.60 | $26.89 | 348 fr, 31.4 h @ $0.4756 | $14.93 | ok |
| fleet05 | $53.00 | $35.53 | **$17.47** | 306 fr, 31.3 h @ **$0.6680** | **$20.88** | **PAUSES** |

**fleet05's budget lasts 26.2 h of the 31.3 h it needs — short by $3.40, about
50 frames.** On current rates it would stop around **2026-08-12 ~19:40Z**.

**This is a distribution problem, not an overrun, and it is exactly the case
R2-3862 already solved once.** Its rule: *"The trigger to escalate is the FLEET
total projecting past $150, not one broker hitting its own cap — the latter is a
pause I can fix in one command without spending an extra cent. Do not silently
raise the total."*

The fleet total does **not** breach:

```
caps sum          $158.49   (unchanged, the R2-3862 invariant)
fleet spent       $103.41
still needs        $42.78
PROJECTED TOTAL   $146.18  =  $137.69 of the $150 new-spend ceiling
```

**But the margin has narrowed from 17.5% to 8.2%** since R2-3906, and the entire
difference is the price walk: fleet05 at $0.668/hr against the $0.455 it aimed
at, and fleet03 at $0.5502. **Both premiums were bought by the same unbuyable
offer.**

**The fix is `rq budget --set`, moving cap from fleet03 to fleet05 with the total
unchanged** — fleet03 finishes in ~12.7 h with **$3.74** of its $10.71 unspent,
which is almost exactly fleet05's shortfall. **I have not done it.** Changing a
broker's budget is an intervention on a broker I did not create, and the standing
instruction is to verify rather than drive. It is also not urgent: the pause is
~26 h away, it costs nothing to leave until fleet03 actually finishes, and doing
it *after* fleet03 finishes is strictly better because the spare cap is then a
measured number rather than a projection.

**If it is never done, the failure mode is benign and recoverable**: fleet05
pauses with ~50 frames unrendered, nothing is lost, and those frames are picked
up by the pre-encode re-submission along with the orphans.

### Orphans, cycle 5

`f876` (fleet03) and `f2669` (fleet05) both FAILED on the transport path with
their jobs continuing in place, so both orphan. Expected set once the cursors
pass them: **[192, 355, 697, 876, 1398, 1517, 2669]**.

## R2-3911 — THE BLACKLIST CANNOT BE FIXED, AND WOULD NOT HAVE HELPED. #169, SECOND INSTANCE.

### There is no supported way to blacklist an offer, and I have not invented one

`rq` offers `render exec anim seq budget get status cancel teardown resume drift`.
`fleetctl` offers `plan up submit status down record verify`. **Neither has a
blacklist command.** The list lives in the broker's SQLite `meta` table under
`bad_hosts` (`broker/app.py:1535`), written only by `save_blacklist()` after a
condemnation. The only routes in are writing to a running broker's database or
restarting it to reload — both excluded. **So: not fixed, by instruction and by
absence of a mechanism.**

### And here is why fixing it would have changed nothing

```python
# broker/app.py:1519
BLACKLIST_TTL_SEC = 6 * 3600
```

**The blacklist expires after 6 hours. The retirement period is 12.** So *every
condemnation is forgotten before the cycle that could use it.* No entry has ever
survived to influence a later re-rent, and none can, in any broker, for any host.

**This is the actual root cause of R2-3907, and my account there was incomplete.**
I attributed fleet05 buying machine 142281 to the blacklist being per-broker
session state. That is true but insufficient: fleet04's entry was **24 h old**,
so it had lapsed four times over, and fleet04 itself would have re-bought that
machine just as readily. **Per-broker scope and a 6 h TTL are two independent
reasons cross-cycle learning cannot happen**, and the TTL is the binding one.

The TTL is deliberate and its comment argues for it — *"short enough that a
machine having a bad hour is not written off for the week"* — a defensible
trade for a farm doing many short jobs. **It is simply mis-tuned for a render
whose hardware rotates every 12 hours.** Nothing is broken; the constant was
chosen against a different workload.

**Logged against #169 as a second instance of the same root cause:** a blacklist
that records only what it *destroyed* never learns from a failure that produced
no instance (the 400), and a TTL shorter than the failure's recurrence interval
means even what it does record is forgotten first.

**Cost, bounded and accepted:** one rung up the price ladder per re-rent that
draws offer 46851284. Two so far (+16% on fleet03, +47% on fleet05). With ~1-2
cycles left this is a few dollars, against the risk of poking a live broker
mid-render. **Not worth it.**

## R2-3912 — THE CAP REBALANCE IS WRITTEN, GATED AND NOT YET RUN

Authorised: move cap fleet03 -> fleet05, **after fleet03 finishes**, on measured
spare, total unchanged, `rq budget --set` only, fleet04 untouched.

`scratchpad/r23911_cap_rebalance.sh` is written and dry-run. It refuses unless
**fleet03 holds no instance on the vast.ai API**, its **live spend has settled
to zero**, and the **sum of the three caps is identical to the cent** before and
after. It re-reads all three caps afterwards and exits non-zero if the total
moved.

### The dry run caught a gate that FAILED OPEN, which is the whole reason to rehearse

First version of gate 1:

```bash
INST=$("$VR/.venv/bin/python" -m vastctl.vastctl status 2>/dev/null | grep -c "fleet03 pid")
```

It reported **0 instances while fleet03 was visibly running one**. `python -m
vastctl.vastctl` resolves only with `cwd == ~/vast-render`; run from anywhere
else it dies, stderr is swallowed by `2>/dev/null`, stdout is empty, and
`grep -c` returns 0 — **which the gate read as "the card is gone, proceed."**
The single most important safety check in the script was a no-op, and it looked
like a pass.

It also had a second, opposite bug: a bare `fleet03 pid` match hits the trailing
`"broker(s) running with no rented card: ... fleet03 pid ..."` line — i.e. it
matches **exactly when fleet03 is idle**, so once the first bug was fixed the
gate would have blocked forever.

Both fixed. The gate now **proves the query worked** before trusting its answer:

```bash
if ! printf '%s' "$STATUS" | grep -qE '^[0-9]+ instance\(s\)|no instances'; then
  echo ">>>> ABORT: could not read instance state from the vast.ai API."
  echo "     An unanswered question is not a 'no'. Refusing to act on silence."
```

and counts only real instance rows (`^<id> running|loading ... fleet03 pid`).

**Both arms verified against the live system:**

| arm | expected | got |
| --- | --- | --- |
| fleet03 holding a card | ABORT | **exit 91** — "still holds an instance (1)" |
| API unreadable (empty status) | ABORT | **exit 90** — "refusing to act on silence" |

This is the same defect family as R2-3860's failed reconcile, which defaulted to
*"assuming it still exists"* rather than treating an unanswerable question as a
dead card. **A check that cannot distinguish "no" from "I could not ask" is not
a check.** It would have moved cap out of a broker that was still spending.

**Trigger:** fleet03 has ~121 frames left, ~12.7 h, finishing ~**08-12 06:00Z**.
Its `COMPLETE` line is already matched by the lifecycle monitor. fleet05 does not
pause until ~**08-12 19:40Z**, so there are ~13 h of slack between the two.

## R2-3913 — CYCLE 5 BROKE THE 70-MINUTE BAR: fleet05 WAS DOWN 78 MINUTES

**Reportable deviation.** Four cycles ran at 8-30 minutes; this one did not.

```
17:09:35  f2668 delivered, the last frame on the old card
17:13:50  ConnectionDropped mid-f2669 — the retirement
18:31:56  worker ready
          ------------------------------------------------
          78 min 06 s
```

Against R2-3864's 35-70 min budget and cycle 2's previous worst of 68.5 min.
**Nothing was lost** — f2669 was recovered by the requeue (R2-3908's mechanism),
and no frame is at risk.

### It was not the rentals. It was the uplink, and it was worse than cycle 2.

fleet05 needed three attempts (a 400 on offer 46851284, a condemnation of
machine 34481), but those cost only **~6 minutes total**; it had a good card at
**17:35:04**. The remaining **57 minutes were the deploy**:

| stage | this cycle | normal | ratio |
| --- | --- | --- | ---: |
| blender bundle, 481 MB | **1262.0 s @ 0.38 MB/s** | ~11-50 s @ 14-45 MB/s | **~118x slower** |
| scene, 10.96 GB | **2054.5 s @ 5.3 MB/s** | 112-665 s @ 16-98 MB/s | ~10x slower |
| **deploy total** | **3359.7 s** | 164-830 s | |

**0.38 MB/s on the bundle is not contention as previously characterised — it is
near-collapse.** Cycle 2's bad case was 0.92 MB/s on the same transfer; this is
2.4x worse again.

### The cause is a new one: a condemnation storm overlapping a deploy

R2-3864 explained the 7:1 split as **two** scene pushes competing. This cycle had
something the earlier analysis never saw: **fleet04 made four rental attempts
between 17:48 and 18:07**, each of which opens SSH and starts pushing a 481 MB
bundle before the host's refusal is established, *while fleet05 was pushing.*
fleet04 then began its own 10.96 GB scene push at **18:28:46**, still concurrent.

So the uplink was serving fleet05's bundle, fleet05's scene, and a stream of
fleet04 bundle attempts — **and every fleet04 attempt that ends in a
condemnation still consumed uplink first.** The cost of a bad host is therefore
not just its own ~5 minutes; **it is also the bandwidth it steals from whichever
card is legitimately deploying at the time.** That is a coupling between the two
failure modes that neither R2-3863 nor R2-3864 anticipated.

### Why this is still not worth intervening in

- **No frames lost, no cost.** Nothing bills while no instance exists, and the
  frames were recovered by the requeue. The whole event is wall clock.
- **The mitigation R2-3864 names — stagger the re-rents — is not available to
  me.** It would mean interfering with a live recovery path, on brokers I did
  not create, to save wall clock on a render with budget headroom.
- **The fleet re-staggers itself.** Each re-rent resets that card's 12 h clock,
  so the cards drift apart again on their own; cycle 3 cost 23 minutes precisely
  because they had drifted 21 minutes apart.

**Recorded, not acted on.** Budget the next cycles at **35-80 min**, and expect
the upper end whenever a condemnation storm overlaps a deploy.

### Cycle 5, the most eventful of the render

| broker | down | attempts | notes |
| --- | ---: | ---: | --- |
| fleet03 | 21 m 00 s | 2 | offer 46851284 400'd; landed $0.5502 |
| fleet05 | **78 m 06 s** | 3 | 400 + machine 34481 condemned; deploy 3359.7 s |
| fleet04 | in progress | 4 | 400 + machines 34481 and 31233 condemned; landed $0.455 |

**Three separate hosts condemned in one cycle** (34481 twice, 31233 once),
against three in the whole render before it. **Base rate 6 bad in ~24 rentals,
~25%** — consistent with the 21% at R2-3863, so the market has not degraded; this
cycle simply drew more rentals because each condemnation forces another.

## R2-3914 — RETRACTION: THE "CONDEMNATION STORM STOLE THE UPLINK" CLAIM IN R2-3913 IS FALSE

**R2-3913's causal explanation is withdrawn. Its measurements stand; its
mechanism does not.** The 78-minute downtime is real. The reason I gave for it
is not, and it was relayed onward before I checked it.

### What I claimed, and why it was wrong

I wrote that fleet04's four rental attempts *"each of which opens SSH and starts
pushing a 481 MB bundle before the host's refusal is established"* stole uplink
from fleet05's deploy. **R2-3863 already recorded the opposite** — its table has
a `first bundle push` column reading `never` for every condemned host — and I
did not check my claim against it.

The log is unambiguous:

```
17:48:50  deploying onto instance 47484025 (machine 34481)
17:53:05  instance 47484025 refuses our ssh key            <- nothing between
18:03:19  deploying onto instance 47484341 (machine 31233)
18:07:32  instance 47484341 refuses our ssh key            <- nothing between
```

A grep for any push line against either instance id returns **nothing**. The
publickey denial happens during the SSH handshake, before a byte of payload.
**A condemned host transfers nothing and therefore steals no bandwidth.** The
cost of a failed rental is its ~5 minutes and nothing else.

### What the measurements actually show

Bounded by **log line offsets**, not timestamps — several lines I first read as
concurrent were from 08-10, which is exactly the trap R2-3860 documented and
which I walked into anyway:

| transfer | window | rate | competing traffic |
| --- | --- | ---: | --- |
| fleet05 bundle | 17:36:01-17:57:03 | **0.38 MB/s** | **none — alone on the uplink** |
| fleet05 scene | 17:57:24-18:31:41 | 5.3 MB/s | partial: fleet04's bundle 18:13:29-18:28:24 |
| **fleet05, cycle 4, same broker** | 05:13:34-05:17:55 | **30.27 / 69.3 MB/s** | — |

fleet03 finished pushing at **17:23:06** and fleet04 pushed nothing until
**18:13:29**, so **fleet05's bundle had the link to itself and still managed
0.38 MB/s.** Contention cannot explain a transfer that had no competition.

**The difference is the path.** Cycle 5 pushed to `host-A` — the South
Korea host R2-3864 identified as the high-RTT loser of its 7:1 split. Cycle 4's
fast push went to `host-C`. R2-3864's **underlying** mechanism, that
OpenSSH's fixed internal buffer caps single-stream throughput regardless of link
speed and penalises high-RTT paths, explains this cleanly. Its **framing** as
"two pushes competing" does not, and I extended that framing past its evidence.

### The consequence for #169

**The coupling argument does not survive, and it was the strongest case for
fixing the blacklist.** What remains is the direct cost only: one rung up the
price ladder per re-rent that draws a bad host or the unbuyable offer — and even
that is **transient**, because the selector returns to ~$0.455/hr once the
session blacklist has absorbed them. Observed three times this cycle. That is a
materially weaker case than the one I made.

### The pattern in my own errors, which is the thing worth fixing

Three times now I have asserted a mechanism ahead of the measurement: the 400
called "a transient" (R2-3910 corrected it), "fleet04 is the broker whose job
requeues" (R2-3909 corrected it to a property of the failure path), and this.
**Each was a correlation generalised without an attempt to break it**, and in
each case the disconfirming evidence was already in the repository.

The standard for the rest of this task: **mark inference as inference, and
search for the record that contradicts it before reporting, not after.** The
frame checks are built on exactly this principle — `fleetctl verify` is not
trusted about decoding because it re-reads its own record — and my prose should
meet the bar my tools do.

## R2-3915 — CYCLE 5 CLOSED

| broker | down | attempts | notes |
| --- | ---: | ---: | --- |
| fleet03 | **21 m 00 s** | 2 | offer 46851284 400'd; landed $0.5502/hr |
| fleet04 | **62 m 49 s** | 4 | 400 + machines 34481, 31233 condemned; landed $0.455/hr |
| fleet05 | **78 m 06 s** | 3 | 400 + machine 34481 condemned; deploy 3359.7 s on a high-RTT path |

Band widened to **35-80 min** with escalation above 80. Three condemnations in
one cycle; base rate **6 bad hosts in ~24 rentals, ~25%**, consistent with the
21% at R2-3863.

**All three jobs requeued except fleet03's**, so the orphan set stands at
**[192, 355, 697, 876]** — all four fleet03's, the only broker whose job has
never been recomputed from disk.

## R2-3916 — fleet03 FINISHED ITS BLOCK AND SWEPT ITS OWN ORPHANS. THE ORPHAN COUNT IS ZERO.

**This corrects the central claim of R2-3901 through R2-3915, in the direction of
the system being better than I described it.**

```
04:45:18  sequence master4k frame 993 done (989/993)
04:45:18  job d3b1b8bde2f4 requeued WITHOUT spending an attempt — this pass
          delivered 989 frame(s) before it stopped, so it made progress
04:45:19  sequence master4k job d3b1b8bde2f4: 993 requested, 989 already
          delivered, 4 to render
04:49:40  frame 192 done (1/4)
04:53:33  frame 355 done (2/4)
04:56:55  frame 697 done (3/4)
05:03:18  frame 876 done (4/4)
05:03:18  job d3b1b8bde2f4 COMPLETE — 4 frame(s) in 18.0 min, all verified
```

**Those four frames are exactly fleet03's four orphans**, and all four are now on
disk. The ledger reads:

```
ORPHANED: none          count = 0
PREDICTED 'to render' ON RE-SUBMISSION = 417   = 0 orphaned + 417 not yet rendered
```

### What I had wrong

I reported, repeatedly and to the coordinator, that

> *"A retirement orphans its in-flight frame unless something later forces that
> broker's job to requeue. A deploy failure forces it; a transport failure does
> not."*

The first sentence is right. **The second is incomplete: reaching the end of the
pass also forces it.** When `run_sequence` exhausts its todo having delivered
fewer frames than were requested, it requeues *without spending an attempt* and
recomputes the plan from disk — which finds precisely the frames that were
skipped. **The orphans were never permanent. They were deferred to the end of the
block.**

R2-3861's *"the master will finish with 2 frames missing unless something
re-renders them"* was therefore pessimistic, and every ledger reading since has
been measuring **work deferred**, not **work lost**. The distinction matters
because it is the difference between a defect and a schedule.

**Why I did not see it sooner, stated plainly:** no broker had ever finished a
block before. The behaviour is only observable at the end of a pass, and until
05:03Z today no pass had ended. The ledger was right about every frame it
listed; my interpretation of what the listing *meant* outran the evidence — the
same error as R2-3910 and R2-3914, for the third and I hope last time.

### The falsifiable form, stated before the evidence exists

**fleet04 and fleet05 will each do the same when their blocks end**, and the
pre-encode re-submission will find **0 frames to render, not 4-10.**

- **Re-submission reports 0 to render** — the model above is confirmed and
  coverage is proven by `fleetctl verify --manifest` alone.
- **Re-submission reports N > 0** — the sweep is not universal, those N frames
  are the real orphans, and they get rendered. Nothing is lost either way.

**The re-submission stays mandatory regardless.** Its value was never that it
rescues frames; it is that it is the only check that compares the film against
the range 1-2978 rather than against a job's own todo list. A `COMPLETE` line
that reads *"4 frame(s), all verified"* is true and tells you nothing about
coverage — which is exactly the trap this whole exercise was built to avoid.

### fleet03 is done: 993 of 993

Its block is complete, its four casualties recovered, and it holds the only
finished third of the film.

## R2-3917 — THE REBALANCE GATE FIRED CORRECTLY, AND THERE IS LIKELY NOTHING TO MOVE

Run at 05:04Z, 46 seconds after fleet03's `COMPLETE`:

```
>>>> ABORT: fleet03 still holds an instance on vast.ai (1). Spare is
     a projection until its card is gone. Waiting is free; this is not.
exit=91
```

**Correct.** `IDLE_GRACE_SEC` is 300 s, so the card is still rented and still
billing for up to five minutes after the last frame. Acting now would have
computed spare against a number still moving — and fleet03's `live` spend was
**$6.67** at that moment, unsettled.

**And the spare is much smaller than I projected.** fleet03 has spent **$37.85
of its $42.00 cap — $4.15 remaining**, against the ~$10.49 I estimated at 17:53Z
yesterday. The difference is the $0.5502/hr card it drew in cycle 5 after losing
the 400-race, run for a full 12 hours.

Whether anything needs moving:

| broker | cap remaining | work left | needs @ current rate |
| --- | ---: | --- | ---: |
| fleet04 | ~$26.8 banked-basis | 233 fr, ~19.4 h | ~$9.2 |
| fleet05 | **$11.76** | 184 fr, ~14.8 h | **~$7.0** |

**Neither is short.** On these numbers the rebalance script will reach
`nothing to move` and exit 0 without touching a cap, which is the right outcome
and the one it was written to be able to reach. It will be re-run once fleet03's
card is gone and its spend has settled, so the decision rests on measured
numbers rather than these.

Credit **$64.59 = 43.0 h of runway** against ~19.4 h of remaining work.

## R2-3918 — HOST DEFECTS OUTLIVE THE BLACKLIST BY AN ORDER OF MAGNITUDE. #169, PROPERLY ARGUED THIS TIME.

Cycle 6 condemned **machine 8512** on fleet05. The same machine, with the same
failure, was condemned by fleet04 in **cycle 1**:

```
state4:3255  16:37:06 (08-09)  instance 47286610 (machine 8512) refuses our ssh key
state5:3649  05:56:27 (08-12)  instance 47523049 (machine 8512) refuses our ssh key
```

**61 hours 19 minutes apart, still broken.** With machine 142281 (24 h) that is
two independent measurements of the same thing: **`authorized_keys` failures are
a durable property of a host, not a bad hour.**

```python
BLACKLIST_TTL_SEC = 6 * 3600     # broker/app.py:1519
```

**The TTL is ~10x shorter than the shortest observed defect lifetime and ~60x
shorter than the longest.** Its comment justifies itself as *"short enough that a
machine having a bad hour is not written off for the week"* — a reasonable
instinct that the measurements do not support. **Nothing in this render has ever
looked like a bad hour.** Every condemned host was condemned again on every
subsequent encounter, without exception.

### The unshared blacklist, demonstrated cleanly

Every machine each broker has condemned:

| broker | condemned |
| --- | --- |
| fleet04 | 52271, 8512, 142281, 34481, 31233 |
| fleet05 | 142281, 34481, 8512 |

**Every single one of fleet05's condemnations is a host fleet04 had already
condemned.** fleet05 has never independently discovered a bad host — it has only
ever rediscovered fleet04's, at ~5 minutes each. And fleet05 has just rented
**machine 31233**, which fleet04 condemned yesterday at 18:07:32.

**This is the argument for #169, and it does not depend on the bandwidth claim I
retracted at R2-3914.** It rests on two measured facts: the defects are durable
over days, and the blacklist is both per-process and expires in 6 hours. A
fleet-wide blacklist with a TTL matched to the observed defect lifetime would
have prevented **every repeat condemnation in this render** — 3 of the 7, at
~5 minutes and one price-ladder rung each.

## R2-3919 — fleet05'S BUDGET IS NOW GENUINELY TIGHT, AND THE REBALANCE IS BLOCKED FOR ~8 MINUTES

| | |
| --- | --- |
| cap | $53.00 |
| spent | $41.59 |
| **remaining** | **$11.41** |
| work left | **176 frames**, ~14.2 h |
| current card | **$0.734/hr** (machine 31233, deploying) |
| **needs** | **~$10.4** |
| **headroom** | **~$1.0** |

The price walk this cycle: $0.537 (create failed) -> $0.668 (machine 8512,
condemned) -> **$0.734**. If machine 31233 is also condemned — and fleet04
condemned it yesterday — the next rung likely breaches the cap.

**fleet03 has $4.08 of cap sitting idle**, which is more than the shortfall.
This is precisely the case the rebalance was authorised for.

**It is blocked, correctly.** fleet03's card went `cold` at ~05:05 and
`HIBERNATE_SEC = 3600` destroys it at ~06:05; until then the gate refuses
because an instance still exists and **$6.74 of live spend has not settled**.
Moving cap now would be arithmetic on a number still in motion.

**There is no urgency in the 8-minute wait:** fleet05 holds 15.5 h of budget at
its current rate against 14.2 h of work, so it cannot pause before the gate
opens. The rebalance will be re-run after ~06:05 on settled figures.

## R2-3920 — CORRECTION: THE IDLE CARD IS DESTROYED AT 09:08Z, NOT 06:05Z

I said fleet03's stopped card would be destroyed "at ~06:05" and that the
rebalance gate would open then. **Wrong, and the correct figure was in a log line
I had already fetched.**

```
05:08:18  idle 300s — stopping instance (disk kept)
05:08:19  instance 47482165 stopped after 710.7 min running (~$6.271 gpu).
          disk keeps billing ~$0.037/hr; destroying in 240 min
```

**240 minutes, so 09:08Z.** I read `HIBERNATE_SEC = _env("HIBERNATE", 3600)` out
of `config.py` and quoted the *default* without checking whether it was
overridden. It is:

```
/proc/2998103/environ:  VASTRENDER_HIBERNATE=14400
```

**Fourth instance of stating a mechanism ahead of the measurement**, and the
cheapest one to have avoided: the broker prints the actual number, in plain
English, in the same line that announced the stop.

**What was right:** `IDLE_GRACE_SEC = 300` predicted the stop exactly — COMPLETE
at 05:03:18, stopped at 05:08:18, five minutes to the second. **GPU billing
ended there**, which is the part that matters for cost. The card now costs
**$0.037/hr of disk**, so the whole 4-hour hibernation is **~$0.15**.

### Consequence for the rebalance

The gate stays shut until **09:08Z**, because fleet03's **$6.77 of `live` spend
does not bank until the instance is destroyed**. Acting before then would move
cap computed against an unsettled figure — exactly what the gate exists to
prevent, and it is refusing correctly for the second reason in a row.

**No urgency, verified rather than assumed:**

| broker | cap remaining | work left | needs | headroom |
| --- | ---: | --- | ---: | ---: |
| fleet04 | $20.53 | 221 fr, 20.2 h @ $0.4756 | **$9.6** | $10.9 |
| fleet05 | $11.00 | 170 fr, 13.2 h @ $0.5289 | **$7.0** | $4.0 |

**Neither broker can exhaust its cap before 09:08Z**, or indeed at all on
current rates. fleet03's spare is $4.06 and will still be spare at 09:08.

Finish projections: **fleet05 ~08-12 19:50Z**, **fleet04 ~08-13 02:50Z**.

## R2-3921 — THE REBALANCE RAN, MEASURED THE NEED, AND CORRECTLY DECLINED TO ACT

fleet03's card was destroyed at ~09:08Z as its own log said it would be. Its
spend settled — **`live $0.0000`, banked $38.03** — and both gates opened for the
first time.

**And the first thing the dry run produced was a proposal I refused to apply.**

```
fleet03 spare = $2.97
fleet05 shortfall at worst case = $14.36
MOVE = $2.97
```

That `$14.36` came from a **hardcoded constant** — `(spent + 24.00) - cap` —
which I wrote when fleet05 had **306 frames** left. It had 138. The number was
stale within hours and the script was about to move real cap on the strength of
it. **A gate that checks the world but computes on a constant is only half a
gate**, which is the same lesson as the fail-open cwd bug at R2-3912, arriving
from the other direction.

Replaced with a measurement: frames still on fleet05's todo, at the mean of its
last 10 delivered frames, priced at **the dearest card this render has ever
actually rented ($0.734/hr)**, times a 1.20 margin. It also aborts (exit 97)
rather than guessing if it cannot read those numbers.

```
fleet03 spare (cap - spent - $1.00 reserve) = $2.97   [dead money: its block is done]
fleet05 work left = 138 frames x 278.2s @ $0.734/hr worst-case x1.20 = $9.39
fleet05 cap available now                        = $9.63
fleet05 shortfall                                = $0.00
MOVE                                             = $0.00
>>>> nothing to move. Doing nothing is the correct outcome.
```

**No cap was moved. The three caps still read $42.00 / $63.49 / $53.00, summing
to $158.49**, the R2-3862 invariant, untouched since it was set.

### Why doing nothing is right, and where the residual risk sits

fleet05 covers its remaining work **even at the worst rate this render has ever
paid, with a fifth on top** — $9.63 available against $9.39. At its actual
current rate ($0.5289/hr) the need is ~$6.8 and the headroom ~$2.8.

The one thing to keep in view: **fleet05 retires once more at ~18:06Z**, with
roughly 2 hours of work left afterwards. Even a bad price walk at that point
costs ~$1.5 against several dollars of remaining cap. **The exposure is small
and shrinking**, and the script stays ready if it changes.

**fleet03's $2.97 is dead money and stays dead** — its block is complete, its
card destroyed, and it will never rent again. Leaving it in place keeps the
achievable fleet spend *lower*, which is the safer direction and costs nothing.

### Fleet position

| | |
| --- | --- |
| frames | **2,641 / 2,978 (88.7%)** |
| cards | 2, $1.0044/hr |
| credit | $60.45 = 60.2 h runway against ~20 h of work |
| orphans | **[1766]** — fleet04's cycle-6 frame, deferred not lost |
| projected total | ~$119 of the $150 ceiling |
