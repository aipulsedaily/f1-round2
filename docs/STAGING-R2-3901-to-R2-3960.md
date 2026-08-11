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
