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
| 16:57:31 | re-rented; scene cache budget derived on the new card |

fleet04 was at 11.92 h of uptime at 16:55Z and is due to retire imminently, so
its push may collide with fleet05's. Under R2-3864 that is the 35-70 min case,
not a deviation, and it is not worth reporting unless it runs past 70.
